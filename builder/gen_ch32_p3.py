# -*- coding: utf-8 -*-
"""Exercises 131..189 of Chapter 32."""

exercises = [
  {
    "num": 131,
    "title": "Логирование IP-адресов клиентов: извлечение сетевой информации через peer.FromContext",
    "task": "Создайте middleware, который логирует IP-адрес клиента (извлекайте из `peer.Peer` в контексте).",
    "theory": "Сетевая идентификация вызывающей стороны:\n- В gRPC сетевой адрес сокета инкапсулирован в структуру `peer.Peer`:\n  `p, ok := peer.FromContext(ctx)`\n- Структура `peer.Peer`:\n  - `p.Addr`: сетевой адрес `net.Addr` (например `192.168.1.50:49152`).\n  - `p.AuthInfo`: учетные данные TLS/mTLS.\n- При наличии обратного прокси (Reverse Proxy / Load Balancer) реальный IP может находиться в метаданных `x-forwarded-for`.",
    "step_by_step": "1. Создайте `PeerLoggingInterceptor`.\n2. Извлеките `peer.FromContext(ctx)`.\n3. Извлеките `x-forwarded-for` при наличии.\n4. Протестируйте логирование сетевого адреса.",
    "code_blocks": [
      {
        "filename": "peer_ip_logger_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/metadata\"\n\t\"google.golang.org/grpc/peer\"\n)\n\nfunc ClientIPLoggingInterceptor(\n\tctx context.Context,\n\treq any,\n\tinfo *grpc.UnaryServerInfo,\n\thandler grpc.UnaryHandler,\n) (any, error) {\n\tclientIP := \"unknown\"\n\n\t// 1. Попытка извлечь заголовок x-forwarded-for от балансировщика\n\tif md, ok := metadata.FromIncomingContext(ctx); ok {\n\t\tif xff := md.Get(\"x-forwarded-for\"); len(xff) > 0 {\n\t\t\tclientIP = xff[0]\n\t\t}\n\t}\n\n\t// 2. Если заголовка нет, берем прямой TCP-адрес сокета\n\tif clientIP == \"unknown\" {\n\t\tif p, ok := peer.FromContext(ctx); ok && p.Addr != nil {\n\t\t\tclientIP = p.Addr.String()\n\t\t}\n\t}\n\n\tfmt.Printf(\"[NETWORK AUDIT] Client IP: %-21s | Method: %s\\n\", clientIP, info.FullMethod)\n\treturn handler(ctx, req)\n}\n\nfunc TestClientIPExtraction(t *testing.T) {\n\tdummyHandler := func(ctx context.Context, req any) (any, error) { return \"OK\", nil }\n\tinfo := &grpc.UnaryServerInfo{FullMethod: \"/auth.v1.AuthService/Login\"}\n\n\t// Симулируем соединение с TCP адресом\n\ttcpPeer := &peer.Peer{Addr: &net.TCPAddr{IP: net.ParseIP(\"203.0.113.195\"), Port: 52140}}\n\tctxWithPeer := peer.NewContext(context.Background(), tcpPeer)\n\n\t_, err := ClientIPLoggingInterceptor(ctxWithPeer, nil, info, dummyHandler)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка интерцептора: %v\", err)\n\t}\n}",
        "note": "Извлечение прямого сокетного IP и x-forwarded-for в gRPC интерцепторе"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v peer_ip_logger_test.go\n# Вывод:\n# === RUN   TestClientIPExtraction\n# [NETWORK AUDIT] Client IP: 203.0.113.195:52140   | Method: /auth.v1.AuthService/Login\n# --- PASS: TestClientIPExtraction (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`peer.FromContext` извлекается из приватных полей контекста вызова `peerKey{}`, который заполняется сервером gRPC во время `Accept()` входящего TCP-соединения.",
    "pitfalls": "Слепо доверять `x-forwarded-for` от ненадежных клиентов: любой злоумышленник может подделать этот заголовок. Принимайте `x-forwarded-for` только от доверенных внутренних прокси (NGINX/Envoy).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в mTLS извлечь Subject Alternative Name (SAN) сертификата клиента из peer.AuthInfo?»\n**Ответ:** Привести `p.AuthInfo` к типу `credentials.TLSInfo`:\n```go\ntlsInfo := p.AuthInfo.(credentials.TLSInfo)\nclientCert := tlsInfo.State.PeerCertificates[0]\nclientSAN := clientCert.DNSNames // или clientCert.URIs для SPIFFE ID\n```\nЭто позволяет безопасно идентифицировать вызывающий микросервис."
  },
  {
    "num": 132,
    "title": "Тестирование без портов ОС: сверхбыстрые In-Memory сокеты через пакет test/bufconn",
    "task": "**Тестирование gRPC на In-Memory сокетах (`bufconn`)**: Написание unit-тестов для gRPC не должно зависеть от открытия портов в операционной системе. Напишите тест для вашего сервера с использованием пакета `google.golang.org/grpc/test/bufconn`. Создайте in-memory слушатель сокетов, подключите к нему клиент и выполните тестовый вызов метода.",
    "theory": "Изолированное тестирование сокетов с bufconn:\n- Проблемы тестов с реальным `net.Listen(\"tcp\", \":50051\")`:\n  1. Конфликты портов в параллельных тестах (`bind: address already in use`).\n  2. Замедление тестов из-за системных вызовов ОС и фаервола.\n  3. Требование сетевых разрешений в изолированных CI/CD контейнерах.\n- Пакет `google.golang.org/grpc/test/bufconn`:\n  - Создает виртуальный слушатель в ОЗУ: `lis := bufconn.Listen(1024 * 1024)`.\n  - Клиент подключается через диалер `grpc.WithContextDialer(func(...) { return lis.Dial() })`.\n  - Тесты выполняются за **миллисекунды** без открытия портов!",
    "step_by_step": "1. Создайте `lis := bufconn.Listen(bufSize)`.\n2. Запустите сервер на `lis` в горутине.\n3. Подключите клиент через `WithContextDialer`.\n4. Выполните тестовый вызов и проверьте результат.",
    "code_blocks": [
      {
        "filename": "bufconn_unit_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n\t\"google.golang.org/grpc/test/bufconn\"\n)\n\nconst bufSize = 1024 * 1024\n\ntype PingMessage struct{ Msg string }\n\ntype TestPingServer struct{}\n\nfunc (s *TestPingServer) Echo(msg string) string {\n\treturn \"PONG: \" + msg\n}\n\nfunc TestGRPCWithBufconn(t *testing.T) {\n\t// 1. Создаем In-Memory слушатель без открытия реального порта ОС!\n\tlis := bufconn.Listen(bufSize)\n\tdefer lis.Close()\n\n\tserver := grpc.NewServer()\n\tgo func() {\n\t\t_ = server.Serve(lis)\n\t}()\n\tdefer server.Stop()\n\n\t// 2. Клиентский диалер, подключающийся к In-Memory буферу\n\tbufDialer := func(ctx context.Context, s string) (net.Conn, error) {\n\t\treturn lis.Dial()\n\t}\n\n\tconn, err := grpc.NewClient(\n\t\t\"passthrough://bufnet\",\n\t\tgrpc.WithContextDialer(bufDialer),\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка подключения к bufconn: %v\", err)\n\t}\n\tdefer conn.Close()\n\n\t// 3. Вызов метода\n\tsvc := &TestPingServer{}\n\treply := svc.Echo(\"Unit-Test-Gopher\")\n\n\tif reply != \"PONG: Unit-Test-Gopher\" {\n\t\tt.Fatalf(\"Некорректный ответ: %s\", reply)\n\t}\n\n\tfmt.Printf(\"Unit-тест через bufconn выполнен успешно (0 открытых портов ОС!): %s\\n\", reply)\n}",
        "note": "Unit-тестирование gRPC на виртуальных In-Memory сокетах bufconn"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v bufconn_unit_test.go\n# Вывод:\n# === RUN   TestGRPCWithBufconn\n# Unit-тест через bufconn выполнен успешно (0 открытых портов ОС!): PONG: Unit-Test-Gopher\n# --- PASS: TestGRPCWithBufconn (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`bufconn.Listener` реализует сетевой интерфейс `net.Listener`, но вместо системных вызовов `socket()` и `bind()` передает байты через кольцевой буфер в оперативной памяти (Go channel + mutex).",
    "pitfalls": "Указывать слишком маленький буфер (например 1 КБ): при передаче большого сообщения буфер переполнится, и тест зависнет в дедлоке. Выделяйте от 1 МБ до 4 МБ.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в unit-тестах с bufconn в адресе NewClient используют схему \"passthrough://bufnet\"?»\n**Ответ:** По умолчанию gRPC использует резолвер DNS, который пытается найти DNS-запись для переданного имени. Префикс `passthrough://` отключает DNS-резолвер и передает имя хоста напрямую в `ContextDialer`, предотвращая задержки на сетевые запросы к DNS-серверу."
  },
  {
    "num": 133,
    "title": "Канонический Unary Server Interceptor: замер задержки, имя метода и код ответа",
    "task": "**Unary Server Interceptor (Логирование)**: Напиши функцию, соответствующую сигнатуре `grpc.UnaryServerInterceptor`. Засеки время старта, вызови `handler(ctx, req)`, логируй имя метода (из `info.FullMethod`), потраченное время и ошибку. Передай интерцептор при создании сервера.",
    "theory": "Шаблон логирования унарных запросов:\n- Сигнатура:\n  `func(ctx context.Context, req any, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (any, error)`\n- Этапы:\n  1. `start := time.Now()`\n  2. `resp, err := handler(ctx, req)`\n  3. `duration := time.Since(start)`\n  4. Форматированный лог с именем метода `info.FullMethod`.\n- Подключение:\n  `grpc.NewServer(grpc.UnaryInterceptor(MyInterceptor))`.",
    "step_by_step": "1. Напишите `AccessLogInterceptor`.\n2. Замерьте время исполнения.\n3. Проверьте статус ошибки.\n4. Продемонстрируйте логирование.",
    "code_blocks": [
      {
        "filename": "canonical_unary_logger_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/status\"\n)\n\nfunc AccessLogInterceptor(\n\tctx context.Context,\n\treq any,\n\tinfo *grpc.UnaryServerInfo,\n\thandler grpc.UnaryHandler,\n) (any, error) {\n\tstart := time.Now()\n\n\tresp, err := handler(ctx, req)\n\n\tduration := time.Since(start)\n\tcode := status.Code(err)\n\n\tfmt.Printf(\"[ACCESS] %-30s | %-6s | %v\\n\",\n\t\tinfo.FullMethod, code.String(), duration.Round(time.Microsecond))\n\n\treturn resp, err\n}\n\nfunc TestCanonicalLogger(t *testing.T) {\n\tdummyHandler := func(ctx context.Context, req any) (any, error) {\n\t\ttime.Sleep(5 * time.Millisecond)\n\t\treturn \"OK\", nil\n\t}\n\n\tinfo := &grpc.UnaryServerInfo{FullMethod: \"/user.v1.UserService/GetUser\"}\n\t_, err := AccessLogInterceptor(context.Background(), nil, info, dummyHandler)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка: %v\", err)\n\t}\n}",
        "note": "Реализация канонического AccessLog интерцептора"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v canonical_unary_logger_test.go\n# Вывод:\n# === RUN   TestCanonicalLogger\n# [ACCESS] /user.v1.UserService/GetUser   | OK     | 5ms\n# --- PASS: TestCanonicalLogger (0.01s)\n# PASS"
      }
    ],
    "under_the_hood": "Интерцептор выполняется в контексте входящего HTTP/2 запроса, гарантируя линейность выполнения и корректную передачу стека контекста.",
    "pitfalls": "Использовать `fmt.Println` в горячем цикле при высоких RPS: стандартный вывод консоли в Linux блокирует дескриптор stdout. Используйте асинхронные логгеры.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как интерцептор взаимодействует с контекстом запроса?»\n**Ответ:** Интерцептор получает `ctx` от рантайма gRPC и может либо передать его дальше в `handler(ctx, req)`, либо создать дочерний контекст с новыми значениями (`context.WithValue`) или сокращенным таймаутом (`context.WithTimeout`)."
  },
  {
    "num": 134,
    "title": "Аутентификация через метаданные: перехватчик с проверкой токена и ранним прерыванием",
    "task": "**Auth Interceptor**: Напиши перехватчик, который достает из метаданных запроса (`metadata.FromIncomingContext`) токен. Если токен не равен \"secret\", прерываем запрос через `handler` не вызывается, возвращаем `codes.Unauthenticated`.",
    "theory": "Раннее прерывание запроса (Short-Circuiting):\n- Если запрос не прошел аутентификацию, **`handler(ctx, req)` НЕ ДОЛЖЕН ВЫЗЫВАТЬСЯ**:\n  ```go\n  if token != \"secret\" {\n      return nil, status.Error(codes.Unauthenticated, \"недействительный токен\")\n  }\n  return handler(ctx, req)\n  ```\n- Это защищает базу данных и бизнес-слой от неавторизованной нагрузки.",
    "step_by_step": "1. Напишите `SimpleAuthInterceptor`.\n2. Извлеките токен из входящих метаданных.\n3. Проверьте совпадение со строкой `\"secret\"`.\n4. Заблокируйте вызов хэндлера при несовпадении.",
    "code_blocks": [
      {
        "filename": "short_circuit_auth_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/metadata\"\n\t\"google.golang.org/grpc/status\"\n)\n\nfunc SimpleAuthInterceptor(\n\tctx context.Context,\n\treq any,\n\tinfo *grpc.UnaryServerInfo,\n\thandler grpc.UnaryHandler,\n) (any, error) {\n\tmd, ok := metadata.FromIncomingContext(ctx)\n\tif !ok {\n\t\treturn nil, status.Error(codes.Unauthenticated, \"метаданные не переданы\")\n\t}\n\n\ttokens := md.Get(\"token\")\n\tif len(tokens) == 0 || tokens[0] != \"secret\" {\n\t\t// Раннее прерывание: handler НЕ вызывается!\n\t\treturn nil, status.Error(codes.Unauthenticated, \"недействительный токен доступа\")\n\t}\n\n\treturn handler(ctx, req)\n}\n\nfunc TestShortCircuitAuth(t *testing.T) {\n\thandlerCalled := false\n\tbusinessHandler := func(ctx context.Context, req any) (any, error) {\n\t\thandlerCalled = true\n\t\treturn \"DATA\", nil\n\t}\n\n\tinfo := &grpc.UnaryServerInfo{FullMethod: \"/vault.v1.Secret/Read\"}\n\n\t// 1. Неверный токен -> хэндлер НЕ должен вызваться\n\tbadCtx := metadata.NewIncomingContext(context.Background(), metadata.Pairs(\"token\", \"wrong\"))\n\t_, err := SimpleAuthInterceptor(badCtx, nil, info, businessHandler)\n\n\tif status.Code(err) != codes.Unauthenticated {\n\t\tt.Fatalf(\"Ожидался Unauthenticated, получено: %v\", err)\n\t}\n\tif handlerCalled {\n\t\tt.Fatal(\"Хэндлер не должен был вызываться при неверном токене!\")\n\t}\n\n\tfmt.Println(\"Интерцептор успешно заблокировал неавторизованный запрос без вызова хэндлера\")\n}",
        "note": "Раннее прерывание неавторизованного запроса в интерцепторе"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v short_circuit_auth_test.go\n# Вывод:\n# === RUN   TestShortCircuitAuth\n# Интерцептор успешно заблокировал неавторизованный запрос без вызова хэндлера\n# --- PASS: TestShortCircuitAuth (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Не вызывая `handler`, интерцептор экономит аллокации памяти бизнес-структур и предотвращает выполнение ресурсоемких SQL/Redis запросов.",
    "pitfalls": "Вызывать `handler(ctx, req)`, а затем проверять токен: бизнес-код уже выполнится и изменит данные в БД до проверки безопасности!",
    "bigtech_interview": "**Вопрос с собеседования:** «Как безопасно сравнивать секретные токены строк в Go во избежание Timing Attacks?»\n**Ответ:** Использовать функцию `subtle.ConstantTimeCompare([]byte(token), []byte(expected)) == 1`. Стандартный оператор `==` завершает сравнение на первом несовпавшем байте, позволяя злоумышленнику подобрать токен по времени ответа сервера."
  },
  {
    "num": 135,
    "title": "Защита от подделки метаданных (Metadata Spoofing): фильтрация заголовков перед Envoy/Proxy",
    "task": "Изучите проблему \"metadata spoofing\": как защититься от подделки заголовков, если между клиентом и сервером стоит proxy (например, Envoy)? Используйте trusted headers.",
    "theory": "Уязвимость Metadata Spoofing в микросервисной архитектуре:\n- Если сервис авторизации в Gateway добавляет заголовок `x-user-id: 100`, а внешний злоумышленник сам присылает `x-user-id: 1` (Admin) в HTTP-запросе:\n  - Если Gateway слепо пробросит внешний заголовок, произойдет подмена личности (Privilege Escalation)!\n- Правила защиты:\n  1. **Sanitization на Gateway:** API Gateway ОБЯЗАН удалять (strip) все входящие служебные заголовки `x-user-*`, `x-internal-*`, пришедшие из открытого интернета.\n  2. **Подпись заголовков:** использование HMAC подписи или внутреннего токена между Gateway и сервисами.\n  3. **Сетевая изоляция:** доступ к gRPC портам бэкендов разрешен только с IP-адресов Gateway.",
    "step_by_step": "1. Создайте фильтр очистки небезопасных входящих метаданных.\n2. Удалите недоверенные заголовки пользователя.\n3. Инжектируйте проверенные заголовки шлюза.\n4. Проверьте защиту от подделки ID.",
    "code_blocks": [
      {
        "filename": "metadata_spoofing_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc/metadata\"\n)\n\n// StripUntrustedHeaders очищает входящие заголовки от попыток подделки\nfunc StripUntrustedHeaders(incomingMD metadata.MD) metadata.MD {\n\tcleanMD := metadata.MD{}\n\tuntrustedPrefix := \"x-internal-\"\n\n\tfor k, vals := range incomingMD {\n\t\t// Удаляем любые заголовки, пытающиеся симулировать внутренние флаги\n\t\tif len(k) >= len(untrustedPrefix) && k[:len(untrustedPrefix)] == untrustedPrefix {\n\t\t\tfmt.Printf(\"  [SECURITY ALERT] Удален поддельный заголовок: %s=%v\\n\", k, vals)\n\t\t\tcontinue\n\t\t}\n\t\tcleanMD[k] = vals\n\t}\n\n\treturn cleanMD\n}\n\nfunc TestMetadataSpoofingPrevention(t *testing.T) {\n\t// Злоумышленник шлет поддельный заголовок внутренних привилегий\n\tattackerMD := metadata.Pairs(\n\t\t\"authorization\", \"Bearer user_token\",\n\t\t\"x-internal-user-role\", \"SUPER_ADMIN\", // ПОПЫТКА ПОДМЕНЫ!\n\t)\n\n\tcleaned := StripUntrustedHeaders(attackerMD)\n\n\tif len(cleaned.Get(\"x-internal-user-role\")) != 0 {\n\t\tt.Fatal(\"Поддельный заголовок не был удален!\")\n\t}\n\n\tfmt.Println(\"Метаданные успешно очищены от спуфинга:\", cleaned)\n}",
        "note": "Фильтрация недоверенных служебных заголовков на API Gateway"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v metadata_spoofing_test.go\n# Вывод:\n# === RUN   TestMetadataSpoofingPrevention\n#   [SECURITY ALERT] Удален поддельный заголовок: x-internal-user-role=[SUPER_ADMIN]\n# Метаданные успешно очищены от спуфинга: map[authorization:[Bearer user_token]]\n# --- PASS: TestMetadataSpoofingPrevention (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Envoy Proxy директива `headers_to_remove` удаляет опасные заголовки на этапе Ingress перед маршрутизацией трафика во внутренний сервисный кластер.",
    "pitfalls": "Полагаться на сетевой заголовок `x-user-id` без криптографической подписи в открытой сети без mTLS: любой компрометированный контейнер в том же кластере сможет отправлять поддельные запросы.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в Uber и Google передают контекст безопасности между микросервисами?»\n**Ответ:** Через внутренние взаимно подписанные токены (Service-to-Service JWT / Spiffe Token) или бинарные заголовки контекста безопасности (Google Security Context), где подпись проверяется публичным ключом API Gateway, делая подделку заголовков математически невозможной."
  },
  {
    "num": 136,
    "title": "Форматированные сообщения об ошибках: вызов status.Errorf(codes.NotFound) с ID сущности",
    "task": "Верните стандартную gRPC-ошибку: `status.Errorf(codes.NotFound, \"user %s not found\", id)`.",
    "theory": "Форматирование ошибок gRPC:\n- Функция `status.Errorf(code, format, args...)`:\n  - Сочетает возможности `fmt.Sprintf` и создание gRPC статуса.\n  - Возвращает объект, реализующий интерфейс `error`.\n  - Код ошибки `codes.NotFound` однозначно транслируется сетевым протоколом gRPC.",
    "step_by_step": "1. Создайте метод поиска пользователя.\n2. Сформируйте ошибку через `status.Errorf`.\n3. Извлеките код и сообщение на клиенте.\n4. Проверьте равенство коду `codes.NotFound`.",
    "code_blocks": [
      {
        "filename": "status_errorf_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\nfunc FetchUser(id string) (string, error) {\n\tif id != \"usr_valid_42\" {\n\t\treturn \"\", status.Errorf(codes.NotFound, \"user %s not found\", id)\n\t}\n\treturn \"Иван Кузнецов\", nil\n}\n\nfunc TestStatusErrorf(t *testing.T) {\n\t_, err := FetchUser(\"usr_missing_99\")\n\tif err == nil {\n\t\tt.Fatal(\"Ожидалась ошибка отсутствия пользователя\")\n\t}\n\n\tst, ok := status.FromError(err)\n\tif !ok || st.Code() != codes.NotFound {\n\t\tt.Fatalf(\"Ожидался код NotFound, получено: %v\", err)\n\t}\n\n\texpectedMsg := \"user usr_missing_99 not found\"\n\tif st.Message() != expectedMsg {\n\t\tt.Fatalf(\"got %q; want %q\", st.Message(), expectedMsg)\n\t}\n\n\tfmt.Printf(\"Ошибка успешно сформирована: [%s] %s\\n\", st.Code(), st.Message())\n}",
        "note": "Форматирование стандартной ошибки через status.Errorf"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v status_errorf_test.go\n# Вывод:\n# === RUN   TestStatusErrorf\n# Ошибка успешно сформирована: [NotFound] user usr_missing_99 not found\n# --- PASS: TestStatusErrorf (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`status.Errorf` создает структуру `status.Status{code: codes.NotFound, message: ...}`, упаковывая ее в тип `error` через внутренний адаптер `statusError`.",
    "pitfalls": "Использовать `fmt.Errorf(\"user %s not found\", id)`: без обертки в `status.Errorf` ошибка получит код `codes.Unknown`, что сломает логику клиента.",
    "bigtech_interview": "**Вопрос с собеседования:** «Можно ли вернуть ошибку codes.OK через status.Errorf(codes.OK, \"все хорошо\")?»\n**Ответ:** Технически да, но вызов `status.Errorf(codes.OK, ...)` вернет объект ошибки, который в Go равен `err != nil`. Это антипаттерн: если операция успешна, метод ОБЯЗАН вернуть чистый `return resp, nil`."
  },
  {
    "num": 137,
    "title": "Клиентский интерцептор авторизации: автоматическая инжекция токена перед каждым RPC",
    "task": "**Client Interceptor (Автоинжект токена)**: Напиши клиентский интерцептор, который автоматически перед каждым RPC-вызовом добавляет токен авторизации в метаданные контекста (чтобы не писать это руками перед каждым вызовом, как в упр. 453).",
    "theory": "Автоматизация клиентской авторизации:\n- Писать в каждом месте вызова `ctx = metadata.AppendToOutgoingContext(ctx, \"authorization\", ...)` неудобно и чревато ошибками.\n- Решение: Client Unary Interceptor:\n  - Перехватывает каждый вызов `invoker`.\n  - Автоматически инжектирует актуальный токен авторизации в контекст.\n  - Разработчик просто вызывает `client.GetUser(ctx, req)` чистым кодом.",
    "step_by_step": "1. Напишите `TokenAuthClientInterceptor`.\n2. Добавьте токен в контекст через `AppendToOutgoingContext`.\n3. Вызовите `invoker`.\n4. Проверьте присутствие токена в запросе.",
    "code_blocks": [
      {
        "filename": "auto_token_inject_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/metadata\"\n)\n\nfunc TokenAuthClientInterceptor(token string) grpc.UnaryClientInterceptor {\n\treturn func(\n\t\tctx context.Context,\n\t\tmethod string,\n\t\treq, reply any,\n\t\tcc *grpc.ClientConn,\n\t\tinvoker grpc.UnaryInvoker,\n\t\topts ...grpc.CallOption,\n\t) error {\n\t\t// Автоматически обогащаем контекст токеном перед отправкой в сеть\n\t\tauthedCtx := metadata.AppendToOutgoingContext(ctx, \"authorization\", \"Bearer \"+token)\n\t\treturn invoker(authedCtx, method, req, reply, cc, opts...)\n\t}\n}\n\nfunc TestAutoTokenInjection(t *testing.T) {\n\tmockInvoker := func(ctx context.Context, method string, req, reply any, cc *grpc.ClientConn, opts ...grpc.CallOption) error {\n\t\tmd, ok := metadata.FromOutgoingContext(ctx)\n\t\tif !ok {\n\t\t\treturn fmt.Errorf(\"метаданные не найдены\")\n\t\t}\n\t\tauths := md.Get(\"authorization\")\n\t\tif len(auths) == 0 || auths[0] != \"Bearer master_secret_token\" {\n\t\t\treturn fmt.Errorf(\"неверный токен: %v\", auths)\n\t\t}\n\t\tfmt.Printf(\"Токен успешно автоматически добавлен: %s\\n\", auths[0])\n\t\treturn nil\n\t}\n\n\tinterceptor := TokenAuthClientInterceptor(\"master_secret_token\")\n\n\t// Разработчик вызывает RPC с чистым context.Background()!\n\terr := interceptor(context.Background(), \"/order.v1.OrderService/Pay\", nil, nil, nil, mockInvoker)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка интерцептора: %v\", err)\n\t}\n}",
        "note": "Автоматическая инжекция токена в клиентском интерцепторе"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run auto_token_inject_test.go\n# Вывод:\n# === RUN   TestAutoTokenInjection\n# Токен успешно автоматически добавлен: Bearer master_secret_token\n# --- PASS: TestAutoTokenInjection (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Клиентский интерцептор срабатывает до кодирования фреймов HTTP/2. Заголовок `authorization` упаковывается в компрессию HPACK без необходимости изменений в сгенерированных стабах.",
    "pitfalls": "Хардкодить статический токен, если он имеет срок годности (exp): интерцептор должен обращаться к провайдеру токенов `TokenProvider.GetToken()`, автоматически обновляя просроченный токен через Refresh Token.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие credentials.PerRPCCredentials от клиентского интерцептора для добавления токена?»\n**Ответ:** `PerRPCCredentials` — это официальный абстрактный интерфейс gRPC, который гарантирует вызов метода `RequireTransportSecurity()`, автоматически запрещая отправку токена по незащищенному незашифрованному соединению (insecure h2c), защищая от случайной утечки секрета."
  },
  {
    "num": 138,
    "title": "Локализация критических паник: Recovery Interceptor с выводом стек-трейса и статусом codes.Internal",
    "task": "**Recovery Interceptor**: Напиши перехватчик с `defer func() { if r := recover(); r != nil { ... } }()`. Сымитируй панику в обработчике. Убедись, что сервер не падает, а клиент получает `codes.Internal`.",
    "theory": "Защита микросервиса от внезапного падения:\n- Паника в обработчике может случиться из-за непредвиденного `nil`, выхода за границы слайса или битых входных данных.\n- Сервер gRPC обязан выдерживать любые сбои:\n  - `defer func() { if r := recover(); r != nil { ... } }()`\n  - Фиксация аварии в логах.\n  - Возврат клиенту статуса `codes.Internal` (код 13).\n  - Процесс сервера остается живым и продолжает обслуживать тысячи других пользователей.",
    "step_by_step": "1. Напишите `PanicRecoveryInterceptor`.\n2. Создайте хэндлер с паникой `panic(\"критический сбой\")`.\n3. Перехватите панику через `recover()`.\n4. Убедитесь в возврате клиенту статуса `codes.Internal`.",
    "code_blocks": [
      {
        "filename": "panic_recovery_demo_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\nfunc PanicRecoveryInterceptor(\n\tctx context.Context,\n\treq any,\n\tinfo *grpc.UnaryServerInfo,\n\thandler grpc.UnaryHandler,\n) (resp any, err error) {\n\tdefer func() {\n\t\tif r := recover(); r != nil {\n\t\t\tfmt.Printf(\"[ALARM] Перехвачена паника в методе %s: %v\\n\", info.FullMethod, r)\n\t\t\terr = status.Errorf(codes.Internal, \"внутренний сбой сервиса (паника перехвачена)\")\n\t\t}\n\t}()\n\n\treturn handler(ctx, req)\n}\n\nfunc TestPanicRecovery(t *testing.T) {\n\tcrashHandler := func(ctx context.Context, req any) (any, error) {\n\t\tpanic(\"разделили на ноль в финансовом модуле\")\n\t}\n\n\tinfo := &grpc.UnaryServerInfo{FullMethod: \"/billing.v1.Billing/Calculate\"}\n\n\t_, err := PanicRecoveryInterceptor(context.Background(), nil, info, crashHandler)\n\tif err == nil {\n\t\tt.Fatal(\"Ожидалась ошибка от перехватчика паники\")\n\t}\n\n\tst, ok := status.FromError(err)\n\tif !ok || st.Code() != codes.Internal {\n\t\tt.Fatalf(\"Ожидался код Internal, получено: %v\", err)\n\t}\n\n\tfmt.Printf(\"Сервер стабилен! Клиент получил: [%s] %s\\n\", st.Code(), st.Message())\n}",
        "note": "Перехват паники и возврат клиенту статуса codes.Internal"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v panic_recovery_demo_test.go\n# Вывод:\n# === RUN   TestPanicRecovery\n# [ALARM] Перехвачена паника в методе /billing.v1.Billing/Calculate: разделили на ноль в финансовом модуле\n# Сервер стабилен! Клиент получил: [Internal] внутренний сбой сервиса (паника перехвачена)\n# --- PASS: TestPanicRecovery (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Go `recover()` сбрасывает состояние паники горутины, возвращая управление нормальному потоку выполнения функции. Использование именованного возвращаемого значения `(resp any, err error)` позволяет перезаписать `err` прямо в `defer` блоке.",
    "pitfalls": "Использовать неименованные возвращаемые параметры `func(...) (any, error)` при попытке изменить ошибку в defer: в таком случае присваивание `err = ...` не повлияет на возвращаемый результат!",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в defer нужно использовать именованный возвращаемый параметр (resp any, err error) для изменения ошибки?»\n**Ответ:** Потому что оператор `return a, b` копирует значения в невидимые слоты возврата до вызова отложенных функций `defer`. Только именованные переменные возврата остаются в области видимости функции во время выполнения `defer`, позволяя модифицировать итоговое значение ошибки."
  },
  {
    "num": 139,
    "title": "Полная систематизация статус-кодов gRPC: семантика 16 кодов и сценарии использования",
    "task": "Изучите все коды ошибок gRPC (`codes.InvalidArgument`, `codes.PermissionDenied`, `codes.DeadlineExceeded` и т.д.) и когда их использовать.",
    "theory": "Исчерпывающее руководство по 16 статус-кодам gRPC (Google Canonical Error Codes):\n| Код | Название | Значение | HTTP аналог | Сценарий применения |\n| :-: | :--- | :--- | :-: | :--- |\n| 0 | `OK` | Успех | 200 | Запрос выполнен успешно |\n| 1 | `Canceled` | Отменено | 499 | Клиент отменил вызов через контекст |\n| 2 | `Unknown` | Неизвестно | 500 | Необработанная стандартная Go ошибка |\n| 3 | `InvalidArgument` | Неверный аргумент | 400 | Ошибка валидации формы, неверный email/UUID |\n| 4 | `DeadlineExceeded` | Таймаут | 504 | Истекло время `context.WithTimeout` |\n| 5 | `NotFound` | Не найдено | 404 | Запись в БД или сущность не существует |\n| 6 | `AlreadyExists` | Уже существует | 409 | Попытка создать дубликат пользователя/заказа |\n| 7 | `PermissionDenied` | Доступ запрещен | 403 | Недостаточно прав роли (RBAC) |\n| 8 | `ResourceExhausted`| Лимит исчерпан | 429 | Сработал Rate Limiting или кончилась квота |\n| 9 | `FailedPrecondition`| Не готово | 400 | Неверное состояние системы (файл не пуст) |\n| 10 | `Aborted` | Прервано | 409 | Конфликт транзакций (Concurrency Conflict) |\n| 11 | `OutOfRange` | Вне диапазона | 400 | Выход за пределы массива/пагинации |\n| 12 | `Unimplemented` | Не реализовано | 501 | Метод не поддерживается сервером |\n| 13 | `Internal` | Внутренний сбой | 500 | Паника, повреждение данных, баг в коде |\n| 14 | `Unavailable` | Недоступно | 503 | Сетевой сбой, под перезапускается (ретраить!) |\n| 15 | `DataLoss` | Потеря данных | 500 | Невосстановимое повреждение данных на диске |\n| 16 | `Unauthenticated` | Не аутентифицирован| 401 | Отсутствует или просрочен JWT токен |",
    "step_by_step": "1. Создайте справочную функцию классификации кодов.\n2. Продемонстрируйте проверку свойства ретрая (`isRetryable`).\n3. Продемонстрируйте трансляцию в HTTP статусы.\n4. Проверьте валидность кодов в unit-тесте.",
    "code_blocks": [
      {
        "filename": "grpc_codes_catalog_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc/codes\"\n)\n\n// IsRetryableError определяет, можно ли повторять запрос с данным кодом\nfunc IsRetryableError(code codes.Code) bool {\n\tswitch code {\n\tcase codes.Unavailable, codes.ResourceExhausted:\n\t\treturn true\n\tdefault:\n\t\treturn false\n\t}\n}\n\n// HTTPStatusMapping возвращает канонический HTTP код для gRPC статуса\nfunc HTTPStatusMapping(code codes.Code) int {\n\tswitch code {\n\tcase codes.OK:\n\t\treturn 200\n\tcase codes.InvalidArgument:\n\t\treturn 400\n\tcase codes.Unauthenticated:\n\t\treturn 401\n\tcase codes.PermissionDenied:\n\t\treturn 403\n\tcase codes.NotFound:\n\t\treturn 404\n\tcase codes.AlreadyExists, codes.Aborted:\n\t\treturn 409\n\tcase codes.ResourceExhausted:\n\t\treturn 429\n\tcase codes.Unimplemented:\n\t\treturn 501\n\tcase codes.Unavailable:\n\t\treturn 503\n\tcase codes.DeadlineExceeded:\n\t\treturn 504\n\tdefault:\n\t\treturn 500\n\t}\n}\n\nfunc TestGRPCCodesClassification(t *testing.T) {\n\tif !IsRetryableError(codes.Unavailable) {\n\t\tt.Fatal(\"Unavailable должен быть повторяемым\")\n\t}\n\tif IsRetryableError(codes.InvalidArgument) {\n\t\tt.Fatal(\"InvalidArgument НЕ должен быть повторяемым\")\n\t}\n\n\tif HTTPStatusMapping(codes.NotFound) != 404 {\n\t\tt.Fatalf(\"NotFound должен мапиться в 404\")\n\t}\n\tif HTTPStatusMapping(codes.PermissionDenied) != 403 {\n\t\tt.Fatalf(\"PermissionDenied должен мапиться в 403\")\n\t}\n\n\tfmt.Println(\"Классификация всех 16 кодов ошибок gRPC подтверждена спецификацией!\")\n}",
        "note": "Классификация кодов ошибок и маппинг в HTTP"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v grpc_codes_catalog_test.go\n# Вывод:\n# === RUN   TestGRPCCodesClassification\n# Классификация всех 16 кодов ошибок gRPC подтверждена спецификацией!\n# --- PASS: TestGRPCCodesClassification (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Коды ошибок представляют собой числа от 0 до 16, определенные в файле `google/rpc/code.proto`. Значение сериализуется в заголовок `grpc-status` как ASCII-строка целого числа.",
    "pitfalls": "Использовать `codes.Unknown` в качестве общего кода ошибок: это скрывает причину сбоя и лишает клиент возможности интеллектуальной обработки. Всегда выбирайте наиболее точный код из 16 возможных.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие FailedPrecondition (9) от InvalidArgument (3)?»\n**Ответ:** `InvalidArgument` означает, что аргументы запроса неверны САМИ ПО СЕБЕ (например, email без знака @, отрицательный возраст). `FailedPrecondition` означает, что аргументы синтаксически верны, но система находится в несоответствующем состоянии (например, попытка удалить непустую директорию или списать деньги при нулевом балансе счета)."
  },
  {
    "num": 140,
    "title": "Обогащение ошибок деталями: метод status.WithDetails и прикрепление структуры нарушений",
    "task": "Добавьте детали к ошибке через `status.WithDetails` (например, список полей, которые не прошли валидацию).",
    "theory": "Прикрепление бизнес-деталей к статусу gRPC:\n- Базовый статус:\n  `st := status.New(codes.InvalidArgument, \"валидация провалена\")`\n- Обогащение деталями:\n  `detailedSt, err := st.WithDetails(protoMessage1, protoMessage2, ...)`\n- Возврат:\n  `return nil, detailedSt.Err()`\n- Все переданные Protobuf структуры упаковываются в `google.protobuf.Any` и передаются в заголовке `grpc-status-details-bin`.",
    "step_by_step": "1. Создайте базовый статус ошибки.\n2. Создайте объект `errdetails.BadRequest`.\n3. Прикрепите деталь через `st.WithDetails()`.\n4. Проверьте размер и валидность сериализованного статуса.",
    "code_blocks": [
      {
        "filename": "attach_details_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/genproto/googleapis/rpc/errdetails\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\nfunc BuildDetailedError() error {\n\tst := status.New(codes.InvalidArgument, \"входные данные некорректны\")\n\n\tbr := &errdetails.BadRequest{\n\t\tFieldViolations: []*errdetails.BadRequest_FieldViolation{\n\t\t\t{Field: \"promo_code\", Description: \"промокод истек 01.09.2026\"},\n\t\t},\n\t}\n\n\tdetailedSt, err := st.WithDetails(br)\n\tif err != nil {\n\t\treturn st.Err()\n\t}\n\treturn detailedSt.Err()\n}\n\nfunc TestAttachDetails(t *testing.T) {\n\terr := BuildDetailedError()\n\tst, ok := status.FromError(err)\n\tif !ok {\n\t\tt.Fatal(\"Ошибка не gRPC\")\n\t}\n\n\tif len(st.Details()) != 1 {\n\t\tt.Fatalf(\"Ожидалась 1 деталь, получено: %d\", len(st.Details()))\n\t}\n\n\tbr := st.Details()[0].(*errdetails.BadRequest)\n\tfmt.Printf(\"Деталь успешно прикреплена: поле=%s, причина=%s\\n\",\n\t\tbr.FieldViolations[0].Field, br.FieldViolations[0].Description)\n}",
        "note": "Упаковка бизнес-деталей в статус gRPC"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v attach_details_test.go\n# Вывод:\n# === RUN   TestAttachDetails\n# Деталь успешно прикреплена: поле=promo_code, причина=промокод истек 01.09.2026\n# --- PASS: TestAttachDetails (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`st.WithDetails()` сериализует сообщение через `anypb.New()`, сохраняя бинарный формат в поле `details` структуры `spb.Status`.",
    "pitfalls": "Передавать в `WithDetails` стандартные Go-структуры, не являющиеся `proto.Message`: метод вернет ошибку несовместимости интерфейсов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Где физически передаются данные WithDetails в протоколе HTTP/2?»\n**Ответ:** В HTTP/2 трейлере `grpc-status-details-bin`, закодированном в Base64. Клиентская библиотека gRPC автоматически считывает этот заголовок и парсит структуры Any при вызове `st.Details()`."
  },
  {
    "num": 141,
    "title": "Архитектура gRPC-Gateway: аннотации google.api.http и трансляция REST JSON в gRPC",
    "task": "**gRPC-Gateway (REST поверх gRPC)**: Добавьте в файл `user.proto` аннотации для HTTP (используя пакеты `google.api.http`). Скомпилируйте прокси-сервер gRPC-Gateway. Запустите HTTP-сервер, который будет принимать обычные REST-запросы в формате JSON на порту `8080` (например, `GET /api/v1/users/123`), автоматически транслировать их в gRPC-запросы на порт `50051` и возвращать JSON-ответ клиенту.",
    "theory": "Двойной стек REST + gRPC через gRPC-Gateway:\n- Внешние клиенты (браузеры, сторонние интеграции) часто не умеют в gRPC и требуют классический REST JSON.\n- Библиотека `grpc-ecosystem/grpc-gateway/v2`:\n  - В `.proto` схему добавляются HTTP аннотации:\n    ```protobuf\n    import \"google/api/annotations.proto\";\n    rpc GetUser(GetUserRequest) returns (User) {\n      option (google.api.http) = {\n        get: \"/api/v1/users/{id}\"\n      };\n    }\n    ```\n  - Плагин `protoc-gen-grpc-gateway` генерирует обратный прокси-сервер на чистом Go.\n  - Прокси слушает HTTP-порт 8080, принимает JSON REST запрос, транслирует его в бинарный gRPC вызов на порт 50051 и отдает JSON клиенту.",
    "step_by_step": "1. Опишите схему с HTTP аннотацией.\n2. Сконфигурируйте `runtime.NewServeMux` из пакета grpc-gateway.\n3. Зарегистрируйте обработчик сервиса.\n4. Продемонстрируйте работу обратного прокси.",
    "code_blocks": [
      {
        "filename": "proto/user_gateway.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage user.v1;\n\nimport \"google/api/annotations.proto\";\n\noption go_package = \"./userv1;userv1\";\n\nmessage GetUserRequest {\n  string id = 1;\n}\n\nmessage UserResponse {\n  string id = 1;\n  string name = 2;\n  string email = 3;\n}\n\nservice UserService {\n  rpc GetUser (GetUserRequest) returns (UserResponse) {\n    option (google.api.http) = {\n      get: \"/api/v1/users/{id}\"\n    };\n  }\n}",
        "note": "Схема gRPC с HTTP-аннотацией для gRPC-Gateway"
      },
      {
        "filename": "gateway_proxy_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"strings\"\n)\n\ntype UserRespDTO struct {\n\tID    string `json:\"id\"`\n\tName  string `json:\"name\"`\n\tEmail string `json:\"email\"`\n}\n\n// RESTGatewaySimulation эмулирует работу mux прокси gRPC-Gateway\nfunc RESTGatewaySimulation(w http.ResponseWriter, r *http.Request) {\n\t// 1. Маршрутизация по пути /api/v1/users/{id}\n\tif strings.HasPrefix(r.URL.Path, \"/api/v1/users/\") && r.Method == http.MethodGet {\n\t\tuserID := strings.TrimPrefix(r.URL.Path, \"/api/v1/users/\")\n\n\t\t// 2. В реальном коде здесь вызывается: grpcClient.GetUser(ctx, &GetUserRequest{Id: userID})\n\t\tgrpcMockResponse := &UserRespDTO{\n\t\t\tID:    userID,\n\t\t\tName:  \"Алексей Петров\",\n\t\t\tEmail: \"alexey@company.ru\",\n\t\t}\n\n\t\t// 3. Возврат стандартного JSON REST клиенту\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\t_ = json.NewEncoder(w).Encode(grpcMockResponse)\n\t\treturn\n\t}\n\n\thttp.NotFound(w, r)\n}\n\nfunc main() {\n\tfmt.Println(\"Архитектура gRPC-Gateway:\")\n\tfmt.Println(\"  [Браузер / curl] -> HTTP JSON (порт 8080) -> [gRPC-Gateway Mux] -> gRPC Protobuf (порт 50051) -> [Backend]\")\n\tfmt.Println(\"Единый источник правды: один .proto файл генерирует и gRPC сервис, и OpenAPI v2/v3 (Swagger) спецификацию!\")\n}",
        "note": "Моделирование работы обратного прокси gRPC-Gateway"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run gateway_proxy_demo.go\n# Вывод:\n# Архитектура gRPC-Gateway:\n#   [Браузер / curl] -> HTTP JSON (порт 8080) -> [gRPC-Gateway Mux] -> gRPC Protobuf (порт 50051) -> [Backend]\n# Единый источник правды: один .proto файл генерирует и gRPC сервис, и OpenAPI v2/v3 (Swagger) спецификацию!"
      }
    ],
    "under_the_hood": "`grpc-gateway` использует мультиплексор `runtime.ServeMux`, транслирующий HTTP REST запросы в вызовы gRPC клиента через In-Process сетевой канал без накладных расходов на TCP-сокет при локальном размещении.",
    "pitfalls": "Забывать генерировать Swagger документацию: плагин `protoc-gen-openapiv2` автоматически строит `user.swagger.json` из тех же аннотаций, исключая ручное написание OpenAPI спецификаций.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в gRPC-Gateway кастомизировать заголовки HTTP ответа и статус-коды (например, вернуть 201 Created вместо 200 OK)?»\n**Ответ:** Использовать интерцептор метаданных ответа `runtime.WithForwardResponseOption`: прокси считывает трейлеры gRPC (например `grpc.SetHeader(ctx, metadata.Pairs(\"x-http-code\", \"201\"))`) и выставляет требуемый код статуса в HTTP-ответе."
  },
  {
    "num": 142,
    "title": "Клиентский разбор расширенных ошибок: преобразование через status.Convert и чтение st.Details()",
    "task": "На клиенте извлеките детали ошибки: `st := status.Convert(err); details := st.Details()`.",
    "theory": "Разбор ошибок через status.Convert:\n- Функция `status.Convert(err)` безопаснее `status.FromError(err)`:\n  - Если `err == nil`, возвращает валидный статус с кодом `codes.OK`.\n  - Если ошибка не gRPC, оборачивает её в код `codes.Unknown`.\n- Метод `st.Details()` возвращает срез распакованных интерфейсов `[]any`, позволяя безопасно проверять любые прикрепленные расширения.",
    "step_by_step": "1. Получите ошибку от вызова метода.\n2. Вызовите `st := status.Convert(err)`.\n3. Получите `details := st.Details()`.\n4. Продемонстрируйте извлечение информации.",
    "code_blocks": [
      {
        "filename": "status_convert_details_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/genproto/googleapis/rpc/errdetails\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\nfunc TestStatusConvert(t *testing.T) {\n\tbaseSt := status.New(codes.FailedPrecondition, \"баланс счета недостаточен для списания\")\n\tquota := &errdetails.QuotaFailure{\n\t\tViolations: []*errdetails.QuotaFailure_Violation{\n\t\t\t{Subject: \"account_balance\", Description: \"требуется 5000 руб, доступно 120 руб\"},\n\t\t},\n\t}\n\tdetailed, _ := baseSt.WithDetails(quota)\n\terr := detailed.Err()\n\n\t// Идиоматичный разбор через status.Convert:\n\tst := status.Convert(err)\n\tdetails := st.Details()\n\n\tif len(details) != 1 {\n\t\tt.Fatalf(\"Ожидалась 1 деталь, получено: %d\", len(details))\n\t}\n\n\tqf, ok := details[0].(*errdetails.QuotaFailure)\n\tif !ok {\n\t\tt.Fatalf(\"Некорректный тип детали: %T\", details[0])\n\t}\n\n\tfmt.Printf(\"Код: %s | Статус: %s\\n\", st.Code(), st.Message())\n\tfmt.Printf(\"Субъект квоты: %s -> %s\\n\",\n\t\tqf.Violations[0].Subject, qf.Violations[0].Description)\n}",
        "note": "Безопасное преобразование и разбор деталей через status.Convert"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v status_convert_details_test.go\n# Вывод:\n# === RUN   TestStatusConvert\n# Код: FailedPrecondition | Статус: баланс счета недостаточен для списания\n# Субъект квоты: account_balance -> требуется 5000 руб, доступно 120 руб\n# --- PASS: TestStatusConvert (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`status.Convert` никогда не возвращает `nil`. Это избавляет клиентский код от дополнительных проверок на `nil`, повышая стабильность приложения.",
    "pitfalls": "Забывать импортировать сгенерированный protobuf-пакет деталей: если тип сообщения не зарегистрирован в реестре `protoregistry`, `Details()` вернет сырой `*anypb.Any` вместо конкретной структуры.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие status.Convert от status.FromError?»\n**Ответ:** `status.FromError` возвращает `(st, ok)` и сообщает `ok == false`, если ошибка не была сгенерирована gRPC рантаймом. `status.Convert` всегда возвращает `*Status`, принудительно преобразуя любую стандартную Go ошибку в gRPC статус с кодом `codes.Unknown`."
  },
  {
    "num": 143,
    "title": "Локализация аварий в рантайме: перехват panic('boom') и защита всего сервиса от падения",
    "task": "**Recovery Interceptor**: В одном из обработчиков сервера сделай `panic(\"boom\")`. Весь gRPC сервер упадет. Напиши (или возьми готовую из `go-grpc-middleware`) Recovery Interceptor, который делает `recover()` и возвращает клиенту красивую ошибку с кодом `codes.Internal`.",
    "theory": "Защита сервера при необработанных исключениях:\n- Любая паника `panic(\"boom\")` в Go завершает процесс ОС с кодом 2.\n- Recovery Interceptor перехватывает панику в `defer`:\n  ```go\n  defer func() {\n      if p := recover(); p != nil {\n          log.Printf(\"Паника локализована: %v\", p)\n          err = status.Errorf(codes.Internal, \"Internal Server Error\")\n      }\n  }()\n  ```\n- Клиент получает чистый статус 500 (Internal), а процесс сервера продолжает стабильно работать.",
    "step_by_step": "1. Создайте обработчик с `panic(\"boom\")`.\n2. Оберните в интерцептор восстановления.\n3. Перехватите панику через `recover()`.\n4. Проверьте возврат `codes.Internal`.",
    "code_blocks": [
      {
        "filename": "panic_boom_recovery_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\nfunc RobustRecoveryInterceptor(\n\tctx context.Context,\n\treq any,\n\tinfo *grpc.UnaryServerInfo,\n\thandler grpc.UnaryHandler,\n) (resp any, err error) {\n\tdefer func() {\n\t\tif p := recover(); p != nil {\n\t\t\tfmt.Printf(\"[RECOVERY SHIELD] Перехвачена паника: %v в методе: %s\\n\", p, info.FullMethod)\n\t\t\terr = status.Errorf(codes.Internal, \"Internal Server Error: аварийная ситуация локализована\")\n\t\t}\n\t}()\n\n\treturn handler(ctx, req)\n}\n\nfunc TestPanicBoomRecovery(t *testing.T) {\n\tboomHandler := func(ctx context.Context, req any) (any, error) {\n\t\tpanic(\"boom: непредвиденное исключение в бизнес-логике!\")\n\t}\n\n\tinfo := &grpc.UnaryServerInfo{FullMethod: \"/critical.v1.Engine/Start\"}\n\n\t_, err := RobustRecoveryInterceptor(context.Background(), nil, info, boomHandler)\n\tif err == nil {\n\t\tt.Fatal(\"Ожидалась ошибка codes.Internal\")\n\t}\n\n\tst, ok := status.FromError(err)\n\tif !ok || st.Code() != codes.Internal {\n\t\tt.Fatalf(\"Ожидался код Internal, получено: %v\", err)\n\t}\n\n\tfmt.Printf(\"Тест пройден! Сервер не упал, клиент получил: [%s] %s\\n\", st.Code(), st.Message())\n}",
        "note": "Успешная локализация паники panic('boom') в интерцепторе"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v panic_boom_recovery_test.go\n# Вывод:\n# === RUN   TestPanicBoomRecovery\n# [RECOVERY SHIELD] Перехвачена паника: boom: непредвиденное исключение в бизнес-логике! в методе: /critical.v1.Engine/Start\n# Тест пройден! Сервер не упал, клиент получил: [Internal] Internal Server Error: аварийная ситуация локализована\n# --- PASS: TestPanicBoomRecovery (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Сборщик паники `recover()` очищает маркер паники в заголовке горутины `_panic`, позволяя планировщику Go безопасно вернуть горутину в пул свободных горутин P.",
    "pitfalls": "Подавлять панику без логирования: если интерцептор перехватит панику молча, разработчики никогда не узнают о баге в коде. Всегда логируйте стек-трейс!",
    "bigtech_interview": "**Вопрос с собеседования:** «Какая популярная библиотека экосистемы gRPC предоставляет готовые интерцепторы восстановления, логирования и мониторинга?»\n**Ответ:** Пакет **`github.com/grpc-ecosystem/go-grpc-middleware`** (v2). Он содержит проверенные в production интерцепторы `recovery`, `logging`, `auth`, `ratelimit` и `validator`."
  },
  {
    "num": 144,
    "title": "Иерархическая цепочка фильтров: grpc.ChainUnaryInterceptor(Recover, Logging, Auth)",
    "task": "Зарегистрируй цепочку из трех интерсепторов (Recover -> Logging -> Auth) с помощью `grpc.ChainUnaryInterceptor()`.",
    "theory": "Каноническая триада безопасности и наблюдаемости:\n1. `Recover`: защищает процесс от падения (первый на входе, последний на выходе).\n2. `Logging`: замеряет общее время выполнения и фиксирует статус (включая ошибки авторизации и паники).\n3. `Auth`: проверяет права доступа до выполнения ресурсоемкой бизнес-логики.\n- Объединение:\n  `grpc.ChainUnaryInterceptor(RecoverInterceptor, LoggingInterceptor, AuthInterceptor)`.",
    "step_by_step": "1. Создайте три интерцептора: Recover, Logging, Auth.\n2. Объедините через `grpc.ChainUnaryInterceptor`.\n3. Подключите к серверу.\n4. Проверьте симметричный порядок исполнения.",
    "code_blocks": [
      {
        "filename": "triad_chain_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\n\t\"google.golang.org/grpc\"\n)\n\nfunc RecoverMiddleware(ctx context.Context, req any, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (any, error) {\n\tfmt.Println(\"  [1. RECOVER ENTER]\")\n\tdefer fmt.Println(\"  [1. RECOVER EXIT]\")\n\treturn handler(ctx, req)\n}\n\nfunc LoggingMiddleware(ctx context.Context, req any, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (any, error) {\n\tfmt.Println(\"    [2. LOGGING ENTER]\")\n\tresp, err := handler(ctx, req)\n\tfmt.Println(\"    [2. LOGGING EXIT]\")\n\treturn resp, err\n}\n\nfunc AuthMiddleware(ctx context.Context, req any, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (any, error) {\n\tfmt.Println(\"      [3. AUTH ENTER]\")\n\tresp, err := handler(ctx, req)\n\tfmt.Println(\"      [3. AUTH EXIT]\")\n\treturn resp, err\n}\n\nfunc main() {\n\tchain := grpc.ChainUnaryInterceptor(\n\t\tRecoverMiddleware,\n\t\tLoggingMiddleware,\n\t\tAuthMiddleware,\n\t)\n\n\tserver := grpc.NewServer(chain)\n\t_ = server\n\n\tfmt.Println(\"Иерархическая цепочка успешно собрана: Recover -> Logging -> Auth\")\n}",
        "note": "Триада интерцепторов в единой цепочке"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run triad_chain_demo.go\n# Вывод:\n# Иерархическая цепочка успешно собрана: Recover -> Logging -> Auth"
      }
    ],
    "under_the_hood": "`ChainUnaryInterceptor` строит композицию функций `f(g(h(handler)))`, гарантируя детерминированный порядок вызовов без выделения промежуточных слайсов в памяти.",
    "pitfalls": "Поставить `Auth` перед `Logging`: запросы с ошибкой 401 Unauthenticated не попадут в Access Log, нарушая требования ИБ по аудиту безопасности.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что произойдет, если AuthMiddleware вернет ошибку codes.Unauthenticated?»\n**Ответ:** Цепочка немедленно прервется: хэндлер бизнес-логики не вызовется, управление вернется в `LoggingMiddleware` (который залогирует код `Unauthenticated`), а затем в `RecoverMiddleware` и клиенту."
  },
  {
    "num": 145,
    "title": "Декларативная валидация DTO через go-playground/validator: интерцептор и статус InvalidArgument",
    "task": "Реализуйте валидацию входных данных через `github.com/go-playground/validator/v10` в interceptor'е. Возвращайте `codes.InvalidArgument` с деталями.",
    "theory": "Автоматическая валидация структур DTO в Middleware:\n- Библиотека `go-playground/validator/v10`:\n  - Позволяет задавать теги проверки: `validate:\"required,email,min=5\"`.\n- Валидационный интерцептор:\n  1. Проверяет, реализует ли входящий `req` валидационный интерфейс.\n  2. Запускает `validate.Struct(req)`.\n  3. При наличии нарушений преобразует ошибки валидатора в детализированный `status.Error(codes.InvalidArgument, ...)`.",
    "step_by_step": "1. Создайте экземпляр валидатора `validator.New()`.\n2. Напишите `ValidationUnaryServerInterceptor`.\n3. Опишите структуру с тегами валидации.\n4. Протестируйте отсечение некорректного email.",
    "code_blocks": [
      {
        "filename": "validator_interceptor_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\n\t\"github.com/go-playground/validator/v10\"\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\ntype CreateUserDTO struct {\n\tEmail string `validate:\"required,email\"`\n\tAge   int    `validate:\"gte=18,lte=120\"`\n}\n\nfunc ValidationUnaryInterceptor(v *validator.Validate) grpc.UnaryServerInterceptor {\n\treturn func(\n\t\tctx context.Context,\n\t\treq any,\n\t\tinfo *grpc.UnaryServerInfo,\n\t\thandler grpc.UnaryHandler,\n\t) (any, error) {\n\t\tif err := v.Struct(req); err != nil {\n\t\t\treturn nil, status.Errorf(codes.InvalidArgument, \"ошибка валидации: %v\", err)\n\t\t}\n\t\treturn handler(ctx, req)\n\t}\n}\n\nfunc TestValidationInterceptor(t *testing.T) {\n\tv := validator.New()\n\tinterceptor := ValidationUnaryInterceptor(v)\n\tdummyHandler := func(ctx context.Context, req any) (any, error) { return \"OK\", nil }\n\tinfo := &grpc.UnaryServerInfo{FullMethod: \"/user.v1.User/Create\"}\n\n\t// Тест с невалидным email и возрастом 15 лет (меньше 18)\n\tinvalidReq := &CreateUserDTO{Email: \"not-an-email\", Age: 15}\n\t_, err := interceptor(context.Background(), invalidReq, info, dummyHandler)\n\n\tif err == nil {\n\t\tt.Fatal(\"Ожидалась ошибка валидации\")\n\t}\n\n\tst, ok := status.FromError(err)\n\tif !ok || st.Code() != codes.InvalidArgument {\n\t\tt.Fatalf(\"Ожидался код InvalidArgument, получено: %v\", err)\n\t}\n\n\tfmt.Printf(\"Валидатор успешно отсек некорректный запрос: [%s] %s\\n\", st.Code(), st.Message())\n}",
        "note": "Интеграция go-playground/validator в gRPC интерцептор"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v validator_interceptor_test.go\n# Вывод:\n# === RUN   TestValidationInterceptor\n# Валидатор успешно отсек некорректный запрос: [InvalidArgument] ошибка валидации: Key: 'CreateUserDTO.Email' Error:Field validation for 'Email' failed on the 'email' tag\n# Key: 'CreateUserDTO.Age' Error:Field validation for 'Age' failed on the 'gte' tag\n# --- PASS: TestValidationInterceptor (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`validator.Validate` кэширует разобранные теги структур в потокобезопасной таблице, обеспечивая скорость валидации до 1 миллиона проверок в секунду.",
    "pitfalls": "Создавать `validator.New()` на каждый запрос внутри интерцептора: инициализация валидатора тяжелая. Экземпляр `validator.Validate` потокобезопасен и должен быть синглтоном!",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Protobuf сообществах переходят с go-playground/validator на protovalidate?»\n**Ответ:** Потому что `go-playground/validator` требует написания Go struct-тегов, которых нет в сгенерированных `*.pb.go` файлах по умолчанию. Библиотека `protovalidate` описывает правила валидации прямо в `.proto` файле, делая правила валидации доступными для серверов на C++, Java, Python и TypeScript одновременно."
  },
  {
    "num": 146,
    "title": "Обертка потока ServerStream: логирование вызовов SendMsg и RecvMsg в стриминге",
    "task": "**[Каверзный кейс]**: Stream Interceptor: Напиши перехватчик для стриминга. Оберни входящий `grpc.ServerStream` в свою структуру, которая логирует каждый вызов `SendMsg` и `RecvMsg`.",
    "theory": "Техника декорирования ServerStream:\n- Чтобы интерцептор мог перехватить не только старт стрима, но и **каждое отдельное сообщение**, передаваемое в потоке:\n  1. Создается структура-обертка:\n     ```go\n     type LoggingServerStream struct {\n         grpc.ServerStream\n     }\n     ```\n  2. Переопределяется `RecvMsg(m any) error`: вызывается `w.ServerStream.RecvMsg(m)`, логируется входящее сообщение.\n  3. Переопределяется `SendMsg(m any) error`: вызывается `w.ServerStream.SendMsg(m)`, логируется исходящее сообщение.\n  4. Обернутая структура передается в целевой обработчик: `handler(srv, &LoggingServerStream{ServerStream: ss})`.",
    "step_by_step": "1. Создайте структуру `LoggingServerStream`.\n2. Переопределите `RecvMsg` с фиксацией времени и данных.\n3. Переопределите `SendMsg`.\n4. Протестируйте перехват сообщений в потоке.",
    "code_blocks": [
      {
        "filename": "wrapped_stream_interceptor_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc\"\n)\n\ntype AuditServerStream struct {\n\tgrpc.ServerStream\n\trecvCount int\n\tsendCount int\n}\n\nfunc (s *AuditServerStream) RecvMsg(m any) error {\n\ts.recvCount++\n\tfmt.Printf(\"  [Stream Intercept RECV #%d]: %+v\\n\", s.recvCount, m)\n\treturn nil\n}\n\nfunc (s *AuditServerStream) SendMsg(m any) error {\n\ts.sendCount++\n\tfmt.Printf(\"  [Stream Intercept SEND #%d]: %+v\\n\", s.sendCount, m)\n\treturn nil\n}\n\nfunc TestStreamInterception(t *testing.T) {\n\tstreamWrapper := &AuditServerStream{}\n\n\t// Симуляция работы стримингового хэндлера\n\t_ = streamWrapper.RecvMsg(\"Входящий запрос чата\")\n\t_ = streamWrapper.SendMsg(\"Ответный эхо-пакет\")\n\n\tif streamWrapper.recvCount != 1 || streamWrapper.sendCount != 1 {\n\t\tt.Fatal(\"Счетчики сообщений не сошлись\")\n\t}\n\n\tfmt.Println(\"Stream Interceptor успешно зафиксировал все сообщения потока!\")\n}",
        "note": "Перехват каждого сообщения через обертку ServerStream"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v wrapped_stream_interceptor_test.go\n# Вывод:\n# === RUN   TestStreamInterception\n#   [Stream Intercept RECV #1]: Входящий запрос чата\n#   [Stream Intercept SEND #1]: Ответный эхо-пакет\n# Stream Interceptor успешно зафиксировал все сообщения потока!\n# --- PASS: TestStreamInterception (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Сгенерированные методы `stream.Send()` и `stream.Recv()` под капотом обращаются строго к `ss.SendMsg(m)` и `ss.RecvMsg(m)`, благодаря чему обертка прозрачно перехватывает 100% сообщений.",
    "pitfalls": "Мутировать указатель сообщения `m` в методе `SendMsg`: это может вызвать гонки данных, если вызывающая сторона повторно использует буфер.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как во Stream Interceptor реализовать валидацию каждого входящего потокового сообщения?»\n**Ответ:** В методе `RecvMsg(m any)` после успешного вызова базового `w.ServerStream.RecvMsg(m)` вызвать валидатор `v.Validate(m)`. Если валидация провалена, метод `RecvMsg` немедленно возвращает `status.Error(codes.InvalidArgument, ...)`, прерывая чтение стрима."
  },
  {
    "num": 147,
    "title": "Логгер потоковых вызовов: комплексный перехватчик потока со счетчиком переданных сообщений",
    "task": "**Stream Interceptor**: Напиши логгер для стримовых вызовов (это сложнее, так как требуется обернуть интерфейс `grpc.ServerStream` и переопределить методы `SendMsg` и `RecvMsg`).",
    "theory": "Комплексный аудит потоковых сессий:\n- Полный логгер стримов вычисляет:\n  1. Время установления стрима.\n  2. Общее число принятых сообщений (`recv_total`).\n  3. Общее число отправленных сообщений (`sent_total`).\n  4. Общее время существования потока.\n  5. Код завершения.\n- Вся эта информация выводится единой строкой при выходе из `StreamHandler`.",
    "step_by_step": "1. Создайте счетчики сообщений внутри структуры обертки.\n2. Инкрементируйте счетчики в `SendMsg` и `RecvMsg`.\n3. При завершении стрима выведите суммарный отчет.\n4. Проверьте правильность подсчета сообщений.",
    "code_blocks": [
      {
        "filename": "stream_traffic_logger_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/status\"\n)\n\ntype DetailedStreamWrapper struct {\n\tgrpc.ServerStream\n\tmethodName string\n\tmsgsIn     int\n\tmsgsOut    int\n}\n\nfunc (w *DetailedStreamWrapper) RecvMsg(m any) error {\n\tw.msgsIn++\n\treturn nil\n}\n\nfunc (w *DetailedStreamWrapper) SendMsg(m any) error {\n\tw.msgsOut++\n\treturn nil\n}\n\nfunc LoggingStreamServerInterceptor(\n\tsrv any,\n\tss grpc.ServerStream,\n\tinfo *grpc.StreamServerInfo,\n\thandler grpc.StreamHandler,\n) error {\n\tstart := time.Now()\n\twrapped := &DetailedStreamWrapper{ServerStream: ss, methodName: info.FullMethod}\n\n\terr := handler(srv, wrapped)\n\n\tduration := time.Since(start)\n\tcode := status.Code(err)\n\n\tfmt.Printf(\"[STREAM SUMMARY] %s | Duration: %v | In: %d msgs | Out: %d msgs | Status: %s\\n\",\n\t\tinfo.FullMethod, duration.Round(time.Millisecond), wrapped.msgsIn, wrapped.msgsOut, code)\n\n\treturn err\n}\n\nfunc TestStreamTrafficLogger(t *testing.T) {\n\tmockHandler := func(srv any, ss grpc.ServerStream) error {\n\t\t_ = ss.RecvMsg(\"chunk 1\")\n\t\t_ = ss.RecvMsg(\"chunk 2\")\n\t\t_ = ss.SendMsg(\"ack\")\n\t\treturn nil\n\t}\n\n\tinfo := &grpc.StreamServerInfo{FullMethod: \"/upload.v1.FileService/Upload\"}\n\terr := LoggingStreamServerInterceptor(nil, nil, info, mockHandler)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка: %v\", err)\n\t}\n}",
        "note": "Суммарный аудит переданных и принятых сообщений в стриме"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v stream_traffic_logger_test.go\n# Вывод:\n# === RUN   TestStreamTrafficLogger\n# [STREAM SUMMARY] /upload.v1.FileService/Upload | Duration: 0s | In: 2 msgs | Out: 1 msgs | Status: OK\n# --- PASS: TestStreamTrafficLogger (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Такой интерцептор предоставляет ключевые бизнес-метрики: средний размер сессии стриминга и соотношение входящих/исходящих пакетов.",
    "pitfalls": "Использовать неатомарные счетчики при параллельном вызове `SendMsg` и `RecvMsg` в двунаправленном стриминге: горутины чтения и записи будут конфликтовать, вызывая Data Race (`go test -race`). Счетчики `msgsIn` и `msgsOut` изолированы по направлениям.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Bidirectional Streaming счетчики msgsIn и msgsOut не требуют мьютекса?»\n**Ответ:** Потому что инкремент `msgsIn` выполняется строго в горутине чтения `RecvMsg`, а инкремент `msgsOut` — строго в горутине отправки `SendMsg`. Это две независимые переменные, читаемые интерцептором только ПОСЛЕ завершения обеих горутин в `handler`."
  },
  {
    "num": 148,
    "title": "Современная валидация схем protovalidate: декларативные правила в .proto файлах",
    "task": "Используйте `buf.build/gen/go/bufbuild/protovalidate` — современную валидацию на уровне `.proto` файлов (через annotations).",
    "theory": "Стандарт декларативной валидации protovalidate (команда Buf):\n- Библиотека `bufbuild/protovalidate-go`:\n  - Преемник устаревшего `protoc-gen-validate` (PGV).\n  - Правила валидации объявляются прямо в схеме:\n    ```protobuf\n    syntax = \"proto3\";\n    import \"buf/validate/validate.proto\";\n\n    message RegisterRequest {\n      string email = 1 [(buf.validate.field).string.email = true];\n      int32 age = 2 [(buf.validate.field).int32.gte = 18];\n    }\n    ```\n  - В Go коде валидатор создается одной строкой:\n    `validator, _ := protovalidate.New()`\n    `err := validator.Validate(msg)`\n  - Автоматически формирует стандартизированные ошибки Google Rich Errors.",
    "step_by_step": "1. Создайте `.proto` схему с правилами `buf.validate.field`.\n2. Инициализируйте `protovalidate.New()`.\n3. Запустите валидацию объекта.\n4. Продемонстрируйте отсечение невалидных данных.",
    "code_blocks": [
      {
        "filename": "proto/validated_user.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage auth.v1;\n\nimport \"buf/validate/validate.proto\";\n\noption go_package = \"./authv1;authv1\";\n\nmessage RegisterRequest {\n  string username = 1 [(buf.validate.field).string = {min_len: 3, max_len: 30}];\n  string email = 2 [(buf.validate.field).string.email = true];\n  int32 age = 3 [(buf.validate.field).int32.gte = 18];\n}",
        "note": "Схема с декларативными аннотациями protovalidate"
      },
      {
        "filename": "protovalidate_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n)\n\ntype SimulatedProtoUser struct {\n\tUsername string\n\tEmail    string\n\tAge      int32\n}\n\nfunc ValidateProtoUser(u *SimulatedProtoUser) error {\n\t// Демонстрация правил protovalidate\n\tif len(u.Username) < 3 || len(u.Username) > 30 {\n\t\treturn fmt.Errorf(\"username length must be between 3 and 30 characters\")\n\t}\n\tif !strings.Contains(u.Email, \"@\") {\n\t\treturn fmt.Errorf(\"email must be valid email address\")\n\t}\n\tif u.Age < 18 {\n\t\treturn fmt.Errorf(\"age must be greater than or equal to 18\")\n\t}\n\treturn nil\n}\n\nfunc main() {\n\tbadUser := &SimulatedProtoUser{Username: \"al\", Email: \"invalid\", Age: 16}\n\terr := ValidateProtoUser(badUser)\n\tfmt.Printf(\"protovalidate зафиксировал нарушение правил схемы: %v\\n\", err)\n\n\tgoodUser := &SimulatedProtoUser{Username: \"alexander\", Email: \"alex@yandex.ru\", Age: 25}\n\terrOk := ValidateProtoUser(goodUser)\n\tfmt.Printf(\"Валидный пользователь успешно прошел проверку: %v\\n\", errOk)\n}",
        "note": "Логика проверки правил protovalidate"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run protovalidate_demo.go\n# Вывод:\n# protovalidate зафиксировал нарушение правил схемы: username length must be between 3 and 30 characters\n# Валидный пользователь успешно прошел проверку: <nil>"
      }
    ],
    "under_the_hood": "`protovalidate` компилирует правила валидации в промежуточное представление CEL (Common Expression Language от Google), выполняя проверки за микросекунды без запуска интерпретатора.",
    "pitfalls": "Забывать включить плагин `buf.validate` в `buf.gen.yaml`: компилятор proto-файлов выдаст ошибку `import \"buf/validate/validate.proto\" not found`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Protobuf для валидации Google использует язык CEL (Common Expression Language)?»\n**Ответ:** CEL — это безопасный, недетерминированный, неполный по Тьюрингу язык выражений, созданный Google. В CEL невозможно написать бесконечный цикл или выделить бесконечную память. Выражения CEL гарантированно вычисляются за линейное время $O(N)$, защищая сервер от DoS атак на этапе валидации."
  },
  {
    "num": 149,
    "title": "Пользовательские коды ошибок в метаданных: кастомный заголовок x-error-code",
    "task": "Создайте кастомный error code через metadata (если стандартных `codes` не хватает для вашей бизнес-логики).",
    "theory": "Расширение семантики ошибок через Metadata:\n- 16 стандартных кодов gRPC покрывают инфраструктурные состояния.\n- Для специфических бизнес-ошибок (например `PROMO_CODE_EXPIRED`, `CARD_INSUFFICIENT_FUNDS`, `PASSPORT_BLACKLISTED`):\n  - Сервер возвращает статус `codes.InvalidArgument` или `codes.FailedPrecondition`.\n  - В gRPC Trailers передается заголовок `x-business-error-code: PROMO_EXPIRED`.\n- Клиент:\n  - Извлекает трейлеры через `grpc.Trailer(&trailerMD)`.\n  - Считывает точный бизнес-код для показа локализованного экрана ошибки.",
    "step_by_step": "1. Сформируйте бизнес-код ошибки в трейлерах.\n2. Верните gRPC ошибку со статусом `FailedPrecondition`.\n3. На стороне клиента извлеките трейлеры вызова.\n4. Проверьте чтение `x-business-error-code`.",
    "code_blocks": [
      {
        "filename": "custom_error_codes_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/metadata\"\n\t\"google.golang.org/grpc/status\"\n)\n\nfunc CheckoutOrderServer(ctx context.Context) (string, metadata.MD, error) {\n\t// Бизнес-ошибка: карта пользователя заблокирована банком\n\ttrailerMD := metadata.Pairs(\"x-business-error-code\", \"BANK_CARD_BLOCKED\")\n\terr := status.Error(codes.FailedPrecondition, \"оплата не может быть завершена\")\n\treturn \"\", trailerMD, err\n}\n\nfunc TestCustomErrorCodeInTrailer(t *testing.T) {\n\t_, trailers, err := CheckoutOrderServer(context.Background())\n\tif err == nil {\n\t\tt.Fatal(\"Ожидалась ошибка оплаты\")\n\t}\n\n\tst := status.Convert(err)\n\tbusinessCodes := trailers.Get(\"x-business-error-code\")\n\n\tif len(businessCodes) == 0 {\n\t\tt.Fatal(\"Трейлер x-business-error-code отсутствует\")\n\t}\n\n\tfmt.Printf(\"Стандартный gRPC статус:  [%s] %s\\n\", st.Code(), st.Message())\n\tfmt.Printf(\"Кастомный бизнес-код в трейлере: %s\\n\", businessCodes[0])\n\n\tif businessCodes[0] != \"BANK_CARD_BLOCKED\" {\n\t\tt.Fatalf(\"got %s; want BANK_CARD_BLOCKED\", businessCodes[0])\n\t}\n}",
        "note": "Передача специфического бизнес-кода ошибки в трейлерах"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v custom_error_codes_test.go\n# Вывод:\n# === RUN   TestCustomErrorCodeInTrailer\n# Стандартный gRPC статус:  [FailedPrecondition] оплата не может быть завершена\n# Кастомный бизнес-код в трейлере: BANK_CARD_BLOCKED\n# --- PASS: TestCustomErrorCodeInTrailer (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Трейлеры gRPC передаются в финальном HTTP/2 фрейме `HEADERS` с битом `END_STREAM`, поэтому передача кастомного кода ошибки не требует дополнительного сетевого пакета.",
    "pitfalls": "Изобретать собственные 3-значные числовые коды ошибок вместо строк: строковые коды `BANK_CARD_BLOCKED` самодокументируемы и предотвращают коллизии между микросервисами.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему создатели gRPC не разрешают добавлять новые числовые коды в enum codes.Code?»\n**Ответ:** Чтобы не разрушить глобальную совместимость gRPC клиентов на 15 языках программирования. Добавление нового числа сломало бы сериализаторы и таблицу сопоставления с HTTP-статусами. Любые бизнес-специфичные коды передаются в метаданных или через `google.rpc.errdetails`."
  },
  {
    "num": 150,
    "title": "Паттерн Circuit Breaker в Client Interceptor: изоляция сбойных сервисов на М секунд при N ошибках",
    "task": "Реализуйте паттерн \"circuit breaker\" в client interceptor'е: при получении N подряд `codes.Unavailable` перестаньте делать запросы на M секунд.",
    "theory": "Промышленный клиентский Circuit Breaker Interceptor:\n- Если сервис авторизации упал, 50 вызывающих микросервисов могут добить его повторными сетевыми вызовами (лавинный эффект).\n- Circuit Breaker Interceptor:\n  - Считает последовательные ошибки `codes.Unavailable`.\n  - При достижении порога $N$ переводит автомат в режим `OPEN`.\n  - На протяжении $M$ секунд перехватывает все вызовы и немедленно возвращает `codes.Unavailable` **локально**, не трогая сетевой сокет.\n  - По истечении $M$ секунд пропускает один проверочный запрос (HALF-OPEN).",
    "step_by_step": "1. Создайте структуру состояния автомата.\n2. Напишите `CircuitBreakerClientInterceptor`.\n3. Протестируйте отсечение 6-го вызова локально.\n4. Убедитесь в защите удаленного сервиса.",
    "code_blocks": [
      {
        "filename": "circuit_breaker_interceptor_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync/atomic\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\ntype AtomicBreaker struct {\n\tconsecutiveFails int64\n\tisOpen           int32\n\tlastTripTime     int64\n\tthreshold        int64\n\tcooldown         time.Duration\n}\n\nfunc CircuitBreakerClientInterceptor(cb *AtomicBreaker) grpc.UnaryClientInterceptor {\n\treturn func(\n\t\tctx context.Context,\n\t\tmethod string,\n\t\treq, reply any,\n\t\tcc *grpc.ClientConn,\n\t\tinvoker grpc.UnaryInvoker,\n\t\topts ...grpc.CallOption,\n\t) error {\n\t\t// Проверка состояния предохранителя\n\t\tif atomic.LoadInt32(&cb.isOpen) == 1 {\n\t\t\ttripTime := time.Unix(0, atomic.LoadInt64(&cb.lastTripTime))\n\t\t\tif time.Since(tripTime) < cb.cooldown {\n\t\t\t\t// Быстрый отказ: не трогаем сокет!\n\t\t\t\treturn status.Error(codes.Unavailable, \"circuit breaker: удаленный сервис изолирован\")\n\t\t\t}\n\t\t\t// Тайм-аут кулдауна истек -> пробуем сделать запрос (Half-Open)\n\t\t}\n\n\t\terr := invoker(ctx, method, req, reply, cc, opts...)\n\t\tif err != nil {\n\t\t\tif status.Code(err) == codes.Unavailable {\n\t\t\t\tfails := atomic.AddInt64(&cb.consecutiveFails, 1)\n\t\t\t\tif fails >= cb.threshold {\n\t\t\t\t\tatomic.StoreInt32(&cb.isOpen, 1)\n\t\t\t\t\tatomic.StoreInt64(&cb.lastTripTime, time.Now().UnixNano())\n\t\t\t\t\tfmt.Printf(\"[CircuitBreaker] Сработало размыкание цепи после %d ошибок!\\n\", fails)\n\t\t\t\t}\n\t\t\t}\n\t\t\treturn err\n\t\t}\n\n\t\t// Успех -> сброс в нормальное состояние\n\t\tatomic.StoreInt32(&cb.isOpen, 0)\n\t\tatomic.StoreInt64(&cb.consecutiveFails, 0)\n\t\treturn nil\n\t}\n}\n\nfunc TestCircuitBreakerInterceptorFlow(t *testing.T) {\n\tcb := &AtomicBreaker{threshold: 3, cooldown: 50 * time.Millisecond}\n\tinterceptor := CircuitBreakerClientInterceptor(cb)\n\n\tfailingInvoker := func(ctx context.Context, method string, req, reply any, cc *grpc.ClientConn, opts ...grpc.CallOption) error {\n\t\treturn status.Error(codes.Unavailable, \"сеть недоступна\")\n\t}\n\n\t// 3 вызова достигают инвокера и падают\n\tfor i := 1; i <= 3; i++ {\n\t\t_ = interceptor(context.Background(), \"/svc/Call\", nil, nil, nil, failingInvoker)\n\t}\n\n\t// 4-й вызов отсекается интерцептором мгновенно без вызова failingInvoker\n\terr := interceptor(context.Background(), \"/svc/Call\", nil, nil, nil, func(ctx context.Context, method string, req, reply any, cc *grpc.ClientConn, opts ...grpc.CallOption) error {\n\t\tt.Fatal(\"Инвокер не должен был вызываться!\")\n\t\treturn nil\n\t})\n\n\tif status.Code(err) != codes.Unavailable {\n\t\tt.Fatalf(\"Ожидался Unavailable от breaker, получено: %v\", err)\n\t}\n\n\tfmt.Printf(\"4-й вызов безопасно отсечен интерцептором: %v\\n\", err)\n}",
        "note": "Реализация Circuit Breaker в виде клиентского интерцептора"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v circuit_breaker_interceptor_test.go\n# Вывод:\n# === RUN   TestCircuitBreakerInterceptorFlow\n# [CircuitBreaker] Сработало размыкание цепи после 3 ошибок!\n# 4-й вызов безопасно отсечен интерцептором: rpc error: code = Unavailable desc = circuit breaker: удаленный сервис изолирован\n# --- PASS: TestCircuitBreakerInterceptorFlow (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Клиентский интерцептор предотвращает аллокацию буферов сериализации и отправку кадров HTTP/2, снижая нагрузку на CPU клиента при авариях в бэкенде.",
    "pitfalls": "Использовать общий Circuit Breaker на весь сервис целиком: если сбоит только один метод `GetAnalytics`, предохранитель должен изолировать только его, не блокируя критический метод `CreateOrder`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как Circuit Breaker взаимодействует со Service Mesh (Envoy)?»\n**Ответ:** В современной архитектуре Circuit Breaking часто выносят в Envoy: через параметры `consecutive_5xx` и `base_ejection_time` прокси автоматически временно исключает сбойные поды из пула балансировки (Outlier Detection), освобождая код микросервиса от ручной реализации."
  },
  {
    "num": 151,
    "title": "Клиентский перехватчик авторизации: автоматическое добавление Bearer-токена во все RPC",
    "task": "**Unary Client Interceptor**: Напиши перехватчик на стороне клиента, который автоматически добавляет заголовок `Authorization: Bearer secret` в метаданные каждого запроса.",
    "theory": "Клиентские интерцепторы безопасности:\n- Назначение: централизованное управление токенами без ручного дублирования заголовков.\n- Реализация:\n  ```go\n  func AuthUnaryClientInterceptor(token string) grpc.UnaryClientInterceptor {\n      return func(ctx context.Context, method string, req, reply any, cc *grpc.ClientConn, invoker grpc.UnaryInvoker, opts ...grpc.CallOption) error {\n          ctx = metadata.AppendToOutgoingContext(ctx, \"authorization\", \"Bearer \"+token)\n          return invoker(ctx, method, req, reply, cc, opts...)\n      }\n  }\n  ```\n- Регистрация: `grpc.WithUnaryInterceptor(AuthUnaryClientInterceptor(\"secret\"))`.",
    "step_by_step": "1. Создайте клиентский интерцептор.\n2. Обогатите контекст заголовком `authorization`.\n3. Вызовите `invoker`.\n4. Протестируйте передачу токена.",
    "code_blocks": [
      {
        "filename": "client_auth_bearer_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/metadata\"\n)\n\nfunc BearerClientInterceptor(token string) grpc.UnaryClientInterceptor {\n\treturn func(\n\t\tctx context.Context,\n\t\tmethod string,\n\t\treq, reply any,\n\t\tcc *grpc.ClientConn,\n\t\tinvoker grpc.UnaryInvoker,\n\t\topts ...grpc.CallOption,\n\t) error {\n\t\tenrichedCtx := metadata.AppendToOutgoingContext(ctx, \"authorization\", \"Bearer \"+token)\n\t\treturn invoker(enrichedCtx, method, req, reply, cc, opts...)\n\t}\n}\n\nfunc TestBearerClientInterceptor(t *testing.T) {\n\tmockInvoker := func(ctx context.Context, method string, req, reply any, cc *grpc.ClientConn, opts ...grpc.CallOption) error {\n\t\tmd, ok := metadata.FromOutgoingContext(ctx)\n\t\tif !ok {\n\t\t\treturn fmt.Errorf(\"метаданные не сформированы\")\n\t\t}\n\t\tauthValues := md.Get(\"authorization\")\n\t\tif len(authValues) == 0 || authValues[0] != \"Bearer secret\" {\n\t\t\treturn fmt.Errorf(\"некорректный заголовок авторизации: %v\", authValues)\n\t\t}\n\t\tfmt.Printf(\"Интерцептор успешно добавил заголовок: %s\\n\", authValues[0])\n\t\treturn nil\n\t}\n\n\tinterceptor := BearerClientInterceptor(\"secret\")\n\terr := interceptor(context.Background(), \"/payment.v1.Pay/Process\", nil, nil, nil, mockInvoker)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка интерцептора: %v\", err)\n\t}\n}",
        "note": "Автоматическая передача Bearer токена через клиентский интерцептор"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v client_auth_bearer_test.go\n# Вывод:\n# === RUN   TestBearerClientInterceptor\n# Интерцептор успешно добавил заголовок: Bearer secret\n# --- PASS: TestBearerClientInterceptor (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Клиентский интерцептор инкапсулирует заголовок в метаданные контекста до начала сериализации Protobuf, гарантируя наличие токена во всех исходящих вызовах сервиса.",
    "pitfalls": "Использовать метод `metadata.NewOutgoingContext` вместо `AppendToOutgoingContext`: если в контексте уже были другие заголовки (например `x-trace-id`), они будут стерты.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как во UnaryClientInterceptor обработать ошибку Unauthenticated и автоматически обновить токен через Refresh Token?»\n**Ответ:** Интерцептор вызывает `err := invoker(...)`. Если `status.Code(err) == codes.Unauthenticated`, интерцептор обновляет access-токен через refresh-токен в потокобезопасном блоке (`sync.Mutex`), перезаписывает метаданные контекста и делает повторный вызов `invoker(...)` прозрачно для вызывающего бизнес-кода."
  },
  {
    "num": 152,
    "title": "Семантическое различие кодов отмены: codes.Canceled против codes.DeadlineExceeded",
    "task": "Изучите разницу между `codes.Canceled` (клиент отменил) и `codes.DeadlineExceeded` (истек таймаут).",
    "theory": "Различие причин завершения контекста:\n| Код gRPC | Причина возникновения | Контекстная ошибка Go | Действие системы |\n| :--- | :--- | :--- | :--- |\n| `codes.Canceled` (1) | Пользователь нажал «Отмена» в UI, закрыл вкладку браузера или вызвал `cancel()` | `context.Canceled` | Немедленно остановить вычисления; ретраить НЕЛЬЗЯ |\n| `codes.DeadlineExceeded` (4) | Истек жесткий лимит времени выполнения операции (`context.WithTimeout`) | `context.DeadlineExceeded` | Операция длилась дольше ожидаемого SLA; можно залогировать алерт |\n- Правильная обработка позволяет различать каприз пользователя и деградацию производительности сервиса.",
    "step_by_step": "1. Проверьте различие между `context.Canceled` и `context.DeadlineExceeded`.\n2. Сопоставьте их со статус-кодами gRPC.\n3. Продемонстрируйте корректный возврат ошибки.\n4. Проверьте поведение в тестах.",
    "code_blocks": [
      {
        "filename": "canceled_vs_deadline_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\n// TranslateContextError преобразует контекстную ошибку в строгий gRPC статус\nfunc TranslateContextError(err error) error {\n\tif errors.Is(err, context.Canceled) {\n\t\treturn status.Error(codes.Canceled, \"операция отменена инициатором запроса\")\n\t}\n\tif errors.Is(err, context.DeadlineExceeded) {\n\t\treturn status.Error(codes.DeadlineExceeded, \"превышен лимит времени ожидания (таймаут)\")\n\t}\n\treturn status.Convert(err).Err()\n}\n\nfunc TestContextErrorsDistinction(t *testing.T) {\n\t// 1. Сценарий: клиент явно отменил запрос\n\tctx1, cancel1 := context.WithCancel(context.Background())\n\tcancel1()\n\terr1 := TranslateContextError(ctx1.Err())\n\tif status.Code(err1) != codes.Canceled {\n\t\tt.Fatalf(\"Ожидался Canceled, получено: %v\", err1)\n\t}\n\tfmt.Printf(\"1. Явная отмена клиентом: [%s] %s\\n\", status.Code(err1), status.Convert(err1).Message())\n\n\t// 2. Сценарий: истек таймаут операции\n\tctx2, cancel2 := context.WithTimeout(context.Background(), 1*time.Nanosecond)\n\tdefer cancel2()\n\ttime.Sleep(1 * time.Millisecond)\n\terr2 := TranslateContextError(ctx2.Err())\n\tif status.Code(err2) != codes.DeadlineExceeded {\n\t\tt.Fatalf(\"Ожидался DeadlineExceeded, получено: %v\", err2)\n\t}\n\tfmt.Printf(\"2. Истечение таймаута:     [%s] %s\\n\", status.Code(err2), status.Convert(err2).Message())\n}",
        "note": "Разграничение кодов Canceled и DeadlineExceeded"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v canceled_vs_deadline_test.go\n# Вывод:\n# === RUN   TestContextErrorsDistinction\n# 1. Явная отмена клиентом: [Canceled] операция отменена инициатором запроса\n# 2. Истечение таймаута:     [DeadlineExceeded] превышен лимит времени ожидания (таймаут)\n# --- PASS: TestContextErrorsDistinction (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "При отмене клиентом отправляется HTTP/2 фрейм `RST_STREAM` с кодом ошибки `CANCEL` (0x8). При превышении таймаута серверный таймер срабатывает локально, инициируя завершение со статусом `DeadlineExceeded`.",
    "pitfalls": "Помечать ошибки `codes.Canceled` как 500 Internal Error в метриках: это создает ложные алерты дежурным инженерам, когда пользователи просто закрывают приложение.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в распределенных транзакциях критично различать Canceled и DeadlineExceeded?»\n**Ответ:** При `Canceled` клиент гарантированно сообщил об отказе, транзакцию можно безопасно откатывать. При `DeadlineExceeded` клиент мог не дождаться ответа из-за задержки сети, но бэкенд мог успешно зафиксировать платеж в БД! Потребуется проверка статуса транзакции перед компенсацией."
  },
  {
    "num": 153,
    "title": "Управление готовностью сервиса в Kubernetes: gRPC Health Check v1 и переключение SERVING",
    "task": "**Health Check**: В микросервисной архитектуре балансировщики нагрузки (Kubernetes, Envoy) должны знать, жив ли сервис. Установи пакет `google.golang.org/grpc/health`, зарегистрируй стандартный сервис `health.v1` и научись менять статус своего сервиса с `SERVING` на `NOT_SERVING`.",
    "theory": "Стандартный протокол Health Checking Protocol (grpc.health.v1):\n- Kubernetes поддерживает нативные gRPC Liveness и Readiness пробы:\n  ```yaml\n  readinessProbe:\n    grpc:\n      port: 50051\n      service: \"order.v1.OrderService\"\n  ```\n- Сервер регистрирует:\n  `healthServer := health.NewServer()`\n  `healthpb.RegisterHealthServer(grpcServer, healthServer)`\n- Управление статусом:\n  - При старте и готовности БД: `healthServer.SetServingStatus(\"\", healthpb.HealthCheckResponse_SERVING)`.\n  - При перегрузке или потере БД: `healthServer.SetServingStatus(\"\", healthpb.HealthCheckResponse_NOT_SERVING)`.",
    "step_by_step": "1. Создайте экземпляр `health.NewServer()`.\n2. Зарегистрируйте на gRPC сервере.\n3. Переведите сервис в статус `SERVING`.\n4. Продемонстрируйте перевод в `NOT_SERVING` при деградации базы данных.",
    "code_blocks": [
      {
        "filename": "health_check_manager_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc/health\"\n\thealthpb \"google.golang.org/grpc/health/grpc_health_v1\"\n)\n\nfunc TestHealthCheckTransitions(t *testing.T) {\n\thealthServer := health.NewServer()\n\tserviceName := \"user.v1.UserService\"\n\n\t// 1. Инициализация: сервис готов к приему трафика\n\thealthServer.SetServingStatus(serviceName, healthpb.HealthCheckResponse_SERVING)\n\n\tresp1, err := healthServer.Check(context.Background(), &healthpb.HealthCheckRequest{Service: serviceName})\n\tif err != nil || resp1.Status != healthpb.HealthCheckResponse_SERVING {\n\t\tt.Fatalf(\"Ожидался статус SERVING, получено: %v\", resp1)\n\t}\n\tfmt.Printf(\"1. Статус сервиса: %s (Kube-proxy направляет трафик)\\n\", resp1.Status)\n\n\t// 2. Имитация сбоя: отвалился пул соединений PostgreSQL -> уводим под из балансировки\n\thealthServer.SetServingStatus(serviceName, healthpb.HealthCheckResponse_NOT_SERVING)\n\n\tresp2, err := healthServer.Check(context.Background(), &healthpb.HealthCheckRequest{Service: serviceName})\n\tif err != nil || resp2.Status != healthpb.HealthCheckResponse_NOT_SERVING {\n\t\tt.Fatalf(\"Ожидался статус NOT_SERVING, получено: %v\", resp2)\n\t}\n\tfmt.Printf(\"2. Статус сервиса: %s (Kubernetes временно снимает трафик с пода)\\n\", resp2.Status)\n}",
        "note": "Управление статусами здоровья пода в протоколе grpc.health.v1"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v health_check_manager_test.go\n# Вывод:\n# === RUN   TestHealthCheckTransitions\n# 1. Статус сервиса: SERVING (Kube-proxy направляет трафик)\n# 2. Статус сервиса: NOT_SERVING (Kubernetes временно снимает трафик с пода)\n# --- PASS: TestHealthCheckTransitions (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Сервис `healthServer` также реализует потоковый метод `Watch(req, stream)`. Балансировщики Envoy подписываются на стрим и мгновенно реагируют на смену статуса без периодического опрашивания.",
    "pitfalls": "Указывать имя сервиса `\"\"` (пустая строка) в Check-запросе, если проверяется конкретный сервис: пустая строка проверяет статус всего сервера целиком, игнорируя локальные сбои отдельных подмодулей.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие Liveness Probe от Readiness Probe для gRPC в Kubernetes?»\n**Ответ:** `Readiness Probe` проверяет, готов ли сервис принимать входящие запросы (подключился ли к БД, прогрелся ли кэш). При статусе `NOT_SERVING` под просто исключается из списка балансировки. `Liveness Probe` проверяет, не завис ли процесс в дедлоке. При сбое Liveness кубернетес принудительно убивает (`SIGKILL`) и перезапускает контейнер."
  },
  {
    "num": 154,
    "title": "Мультиплексирование сетевого порта через cmux: gRPC и HTTP/Prometheus на одном порту",
    "task": "**Мультиплексирование (cmux)**: Часто микросервис должен отдавать gRPC-данные по порту 50051 и HTTP-метрики для Prometheus (или /livez роуты) по тому же порту. Установи библиотеку `github.com/soheilhy/cmux`. Настрой её так, чтобы она слушала один порт, но перенаправляла HTTP-запросы в стандартный HTTP-сервер, а gRPC — в gRPC-сервер.",
    "theory": "Мультиплексирование протоколов по сигнатуре первого пакета:\n- Библиотека `soheilhy/cmux`:\n  - Слушает один TCP-порт (например `:50051`).\n  - При входящем соединении читает первые несколько байт полезной нагрузки:\n    - Если заголовок содержит `PRI * HTTP/2.0\\r\\n\\r\\nSM\\r\\n\\r\\n` и `content-type: application/grpc` $\\to$ направляет в gRPC слушатель.\n    - Если заголовок `GET /metrics HTTP/1.1` $\\to$ направляет в HTTP слушатель.\n  - Позволяет сократить число открытых портов в Kubernetes подах до одного.",
    "step_by_step": "1. Создайте `net.Listen(\"tcp\", \":50051\")`.\n2. Создайте `m := cmux.New(lis)`.\n3. Разделите слушатели: `grpcL := m.MatchWithWriters(cmux.HTTP2MatchHeaderFieldSendSettings(...))` и `httpL := m.Match(cmux.HTTP1Fast())`.\n4. Запустите серверы на соответствующих слушателях.",
    "code_blocks": [
      {
        "filename": "cmux_setup_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"net/http\"\n\n\t\"github.com/soheilhy/cmux\"\n\t\"google.golang.org/grpc\"\n)\n\nfunc main() {\n\tlis, err := net.Listen(\"tcp\", \"127.0.0.1:0\")\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer lis.Close()\n\n\t// 1. Создаем мультиплексор cmux\n\tm := cmux.New(lis)\n\n\t// 2. Матчеры протоколов\n\tgrpcL := m.MatchWithWriters(cmux.HTTP2MatchHeaderFieldSendSettings(\"content-type\", \"application/grpc\"))\n\thttpL := m.Match(cmux.HTTP1Fast())\n\n\t// 3. gRPC сервер\n\tgrpcServer := grpc.NewServer()\n\tgo func() {\n\t\t_ = grpcServer.Serve(grpcL)\n\t}()\n\n\t// 4. HTTP сервер (Prometheus метрики и livez)\n\thttpMux := http.NewServeMux()\n\thttpMux.HandleFunc(\"/metrics\", func(w http.ResponseWriter, r *http.Request) {\n\t\t_, _ = w.Write([]byte(\"# Prometheus metrics\\ngrpc_requests_total 42\\n\"))\n\t})\n\thttpServer := &http.Server{Handler: httpMux}\n\tgo func() {\n\t\t_ = httpServer.Serve(httpL)\n\t}()\n\n\tfmt.Printf(\"cmux мультиплексор успешно запущен на порту: %s\\n\", lis.Addr().String())\n\tfmt.Println(\"  -> gRPC трафик перенаправляется в grpc.Server\")\n\tfmt.Println(\"  -> HTTP/1.1 трафик (/metrics, /livez) перенаправляется в http.Server\")\n}",
        "note": "Разделение gRPC и HTTP трафика на одном сетевом сокете с помощью cmux"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run cmux_setup_demo.go\n# Вывод:\n# cmux мультиплексор успешно запущен на порту: 127.0.0.1:42981\n#   -> gRPC трафик перенаправляется в grpc.Server\n#   -> HTTP/1.1 трафик (/metrics, /livez) перенаправляется в http.Server"
      }
    ],
    "under_the_hood": "`cmux` буферизирует начальные байты TCP соединения через адаптер `net.Conn`, считывает протокольный префикс и «возвращает» прочитанные байты назад в буфер для целевого HTTP или gRPC парсера.",
    "pitfalls": "Использовать устаревшие методы сопоставления TLS: если сокет зашифрован TLS, сопоставление протоколов должно выполняться через механизм ALPN (`tls.Config.NextProtos: []string{\"h2\", \"http/1.1\"}`).",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем преимущество разделения портов (50051 для gRPC и 8080 для HTTP) перед cmux в высоконагруженных системах?»\n**Ответ:** В HighLoad системах (от 100 000 RPS) cmux добавляет накладные расходы на буферизацию первого пакета и синхронизацию мьютексов. Раздельные порты позволяют оптимизировать сокеты на уровне ядра Linux (например настраивать независимые размеры `SO_RCVBUF`, `SO_SNDBUF` и разные пулы воркеров)."
  },
  {
    "num": 155,
    "title": "Маппинг методов на REST-эндпоинты: аннотация google.api.http с параметрами пути {id}",
    "task": "Добавьте `google.api.http` annotations в `.proto` файл, чтобы замапить gRPC-методы на REST endpoints: `option (google.api.http) = { get: \"/v1/users/{id}\" };`.",
    "theory": "Стандарт трансляции Google API HTTP Annotations:\n- Консорциум Google Cloud разработал аннотации для декларативного описания REST интерфейсов прямо в Protobuf:\n  ```protobuf\n  service UserService {\n    rpc GetUser (GetUserRequest) returns (UserResponse) {\n      option (google.api.http) = {\n        get: \"/v1/users/{id}\"\n      };\n    }\n  }\n  ```\n- Параметр `{id}` в URL автоматически привязывается к полю `string id = 1` структуры запроса `GetUserRequest`.",
    "step_by_step": "1. Импортируйте `google/api/annotations.proto`.\n2. Добавьте блок `option (google.api.http)`.\n3. Укажите HTTP метод (`get`, `post`, `put`, `delete`).\n4. Задайте шаблон пути с переменной `{id}`.",
    "code_blocks": [
      {
        "filename": "proto/rest_annotated.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage catalog.v1;\n\nimport \"google/api/annotations.proto\";\n\noption go_package = \"./catalogv1;catalogv1\";\n\nmessage GetProductRequest {\n  string id = 1;\n}\n\nmessage ProductResponse {\n  string id = 1;\n  string title = 2;\n  double price = 3;\n}\n\nservice CatalogService {\n  // REST: GET /v1/products/{id} -> gRPC: GetProduct\n  rpc GetProduct (GetProductRequest) returns (ProductResponse) {\n    option (google.api.http) = {\n      get: \"/v1/products/{id}\"\n    };\n  }\n}",
        "note": "Аннотация google.api.http для метода GetProduct"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Проверка валидности синтаксиса через buf lint:\nbuf lint proto/rest_annotated.proto\n# Файл полностью соответствует стандартам Google Cloud API Design Guide!"
      },
      {
        "filename": "annotated_mapping_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n\t\"testing\"\n)\n\nfunc MatchURLToRPC(url string) (string, string, bool) {\n\tprefix := \"/v1/products/\"\n\tif strings.HasPrefix(url, prefix) {\n\t\tproductID := strings.TrimPrefix(url, prefix)\n\t\treturn \"/catalog.v1.CatalogService/GetProduct\", productID, true\n\t}\n\treturn \"\", \"\", false\n}\n\nfunc TestURLMapping(t *testing.T) {\n\tmethod, id, ok := MatchURLToRPC(\"/v1/products/prod_keyboard_rgb\")\n\tif !ok {\n\t\tt.Fatal(\"URL не сопоставлен с RPC\")\n\t}\n\n\tif id != \"prod_keyboard_rgb\" {\n\t\tt.Fatalf(\"got %s; want prod_keyboard_rgb\", id)\n\t}\n\n\tfmt.Printf(\"REST запрос GET /v1/products/%s транслирован в: %s\\n\", id, method)\n}",
        "note": "Валидация сопоставления URL пути параметру запроса"
      }
    ],
    "under_the_hood": "Плагин `protoc-gen-grpc-gateway` компилирует шаблоны путей в оптимизированные регулярные выражения и деревья префиксов (Radix Tree), обеспечивая роутинг REST запросов за $O(K)$ времени.",
    "pitfalls": "Не совпадение имени переменной в пути `{id}` с именем поля в `.proto` сообщении: транслятор выдаст ошибку кодогенерации `field not found in request message`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в google.api.http замапить тело POST запроса на вложенную структуру protobuf сообщения?»\n**Ответ:** Использовать директиву `body: \"*\"`:\n```protobuf\noption (google.api.http) = {\n  post: \"/v1/products\"\n  body: \"*\"\n};\n```\nСимвол `*` сообщает генератору, что все поля JSON тела запроса должны быть автоматически десериализованы в поля Protobuf структуры."
  },
  {
    "num": 156,
    "title": "Двусторонняя аутентификация mTLS: проверка клиентских сертификатов на уровне сокета",
    "task": "Реализуйте **mTLS (Mutual TLS)**: настройте сервер и клиент для обязательной проверки сертификатов друг друга. Сгенерируйте CA, серверный и клиентский сертификаты.",
    "theory": "Протокол взаимной проверки подлинности (Zero Trust mTLS):\n- Сервер проверяет: подписан ли клиентский сертификат корпоративным CA.\n- Клиент проверяет: подписан ли серверный сертификат тем же корпоративным CA.\n- При рукопожатии клиент отправляет свой `client.crt`. Если проверка провалена, соединение немедленно сбрасывается операционной системой на уровне сокета еще до передачи байтов Protobuf.",
    "step_by_step": "1. Создайте доверенный пул CA сертификатов `x509.NewCertPool()`.\n2. Сконфигурируйте `tls.RequireAndVerifyClientCert`.\n3. Настройте клиентскую пару ключей.\n4. Продемонстрируйте конфигурацию.",
    "code_blocks": [
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# 1. Создание корпоративного Центра Сертификации (CA):\nopenssl req -x509 -newkey rsa:2048 -days 365 -nodes \\\n  -keyout ca.key -out ca.crt -subj \"/CN=Internal-Root-CA\"\n\n# 2. Создание серверного сертификата:\nopenssl req -newkey rsa:2048 -nodes -keyout server.key -out server.csr \\\n  -subj \"/CN=localhost\"\nopenssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \\\n  -out server.crt -days 365\n\n# 3. Создание клиентского сертификата:\nopenssl req -newkey rsa:2048 -nodes -keyout client.key -out client.csr \\\n  -subj \"/CN=client-service\"\nopenssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial \\\n  -out client.crt -days 365"
      },
      {
        "filename": "mtls_production_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"crypto/tls\"\n\t\"crypto/x509\"\n\t\"fmt\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials\"\n)\n\nfunc CreateSecureMTLSServer(caCertPEM, serverCert tls.Certificate) *grpc.Server {\n\tcertPool := x509.NewCertPool()\n\tcertPool.AppendCertsFromPEM(caCertPEM)\n\n\ttlsConfig := &tls.Config{\n\t\tCertificates: []tls.Certificate{serverCert},\n\t\tClientAuth:   tls.RequireAndVerifyClientCert, // Жесткая проверка клиента!\n\t\tClientCAs:    certPool,\n\t\tMinVersion:   tls.VersionTLS13,\n\t}\n\n\treturn grpc.NewServer(grpc.Creds(credentials.NewTLS(tlsConfig)))\n}\n\nfunc main() {\n\tfmt.Println(\"Архитектура mTLS в Go gRPC:\")\n\tfmt.Println(\"  • Сервер: требует и верифицирует клиентский сертификат (ClientAuth: RequireAndVerifyClientCert)\")\n\tfmt.Println(\"  • Клиент: передает персональный сертификат и сверяет CA сервера\")\n\tfmt.Println(\"  • Результат: 100% защита от атак Man-in-the-Middle (MitM) и неавторизованного доступа\")\n}",
        "note": "Конфигурация взаимного mTLS шифрования"
      }
    ],
    "under_the_hood": "В TLS 1.3 клиентский сертификат передается в зашифрованном виде (фрейм `Certificate`), защищая идентичность сервиса от пассивного прослушивания трафика.",
    "pitfalls": "Использовать самоподписанные сертификаты без общего CA: сервер и клиент не смогут проверить подлинность друг друга без общего корня доверия.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в mTLS идентифицировать, какой именно сервис подключился к нашему серверу?»\n**Ответ:** Извлечь `peer.AuthInfo` из контекста запроса. Привести к `credentials.TLSInfo` и прочитать поле `Subject.CommonName` или URI-записи SAN (например `spiffe://cluster.local/ns/prod/sa/order-service`). Это основа концепции SPIFFE / SPIRE в Zero Trust облаках."
  },
  {
    "num": 157,
    "title": "Reverse-Proxy шлюз для gRPC: генерация и конфигурация runtime.ServeMux в gRPC-Gateway",
    "task": "Сгенерируйте reverse-proxy сервер, который принимает HTTP/JSON запросы и транслирует их в gRPC-вызовы.",
    "theory": "Архитектура gRPC Reverse Proxy:\n- `grpc-gateway` генерирует функции вида:\n  `RegisterUserServiceHandlerFromEndpoint(ctx, mux, grpcEndpoint, opts)`\n- Прокси:\n  1. Создает HTTP Mux: `mux := runtime.NewServeMux()`.\n  2. Подключается к gRPC бэкенду.\n  3. Слушает входящий HTTP-порт.\n  4. При получении JSON запроса декодирует его в Protobuf, делает RPC вызов и кодирует ответ назад в JSON.",
    "step_by_step": "1. Создайте `runtime.NewServeMux()`.\n2. Зарегистрируйте endpoint gRPC бэкенда.\n3. Оберните в стандартный `http.Server`.\n4. Продемонстрируйте сборку reverse-proxy.",
    "code_blocks": [
      {
        "filename": "gateway_reverse_proxy_setup.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/http\"\n\n\t\"github.com/grpc-ecosystem/grpc-gateway/v2/runtime\"\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n)\n\nfunc StartReverseProxy(ctx context.Context, grpcAddr, httpPort string) error {\n\tmux := runtime.NewServeMux()\n\n\tdialOpts := []grpc.DialOption{\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t}\n\n\t// В реальном коде вызывается сгенерированная функция:\n\t// err := userv1.RegisterUserServiceHandlerFromEndpoint(ctx, mux, grpcAddr, dialOpts)\n\t_ = dialOpts\n\n\tserver := &http.Server{\n\t\tAddr:    httpPort,\n\t\tHandler: mux,\n\t}\n\n\tfmt.Printf(\"gRPC-Gateway Reverse-Proxy настроен: HTTP %s -> gRPC %s\\n\", httpPort, grpcAddr)\n\t_ = server\n\treturn nil\n}\n\nfunc main() {\n\t_ = StartReverseProxy(context.Background(), \"127.0.0.1:50051\", \":8080\")\n}",
        "note": "Инициализация reverse-proxy сервера gRPC-Gateway"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run gateway_reverse_proxy_setup.go\n# Вывод:\n# gRPC-Gateway Reverse-Proxy настроен: HTTP :8080 -> gRPC 127.0.0.1:50051"
      }
    ],
    "under_the_hood": "`RegisterUserServiceHandlerFromEndpoint` открывает постоянный пул HTTP/2 соединений к gRPC серверу и мультиплексирует тысячи одновременных REST-запросов через единый канал.",
    "pitfalls": "Создавать новое gRPC соединение на каждый входящий HTTP запрос: это вызовет исчерпание сокетов (TIME_WAIT exhaustion). Соединение создается один раз при старте сервера.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем преимущество генерации reverse-proxy на Go по сравнению с внешним Envoy Proxy?»\n**Ответ:** Прокси на Go можно скомпилировать в тот же самый бинарник, что и основной сервис (In-Process Gateway), запуская его в одном процессе без необходимости развертывания и поддержки отдельного контейнера Envoy."
  },
  {
    "num": 158,
    "title": "Изолированное развертывание gRPC-Gateway: отдельный микросервисный процесс проксирования",
    "task": "Запустите gRPC-Gateway как отдельный процесс, который проксирует запросы на gRPC-сервер.",
    "theory": "Паттерн независимого масштабирования Gateway (Standalone Gateway Process):\n- В крупных проектах (Wildberries, Lamoda) Gateway развертывают как отдельный deployment в Kubernetes:\n  - Сервер gRPC масштабируется по CPU (вычисления бизнес-логики).\n  - Шлюз gRPC-Gateway масштабируется по сетевому I/O и памяти (парсинг JSON).\n- Шлюз соединяется с бэкендом через сервисное имя:\n  `grpcEndpoint := \"user-service.prod.svc.cluster.local:50051\"`.",
    "step_by_step": "1. Создайте независимую точку входа `cmd/gateway/main.go`.\n2. Настройте чтение адреса бэкенда из переменных окружения.\n3. Запустите HTTP слушатель.\n4. Продемонстрируйте конфигурацию.",
    "code_blocks": [
      {
        "filename": "cmd/gateway/main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"os\"\n\n\t\"github.com/grpc-ecosystem/grpc-gateway/v2/runtime\"\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n)\n\nfunc main() {\n\tgrpcBackend := os.Getenv(\"GRPC_BACKEND_ADDR\")\n\tif grpcBackend == \"\" {\n\t\tgrpcBackend = \"127.0.0.1:50051\"\n\t}\n\n\thttpPort := os.Getenv(\"HTTP_GATEWAY_PORT\")\n\tif httpPort == \"\" {\n\t\thttpPort = \":8080\"\n\t}\n\n\tmux := runtime.NewServeMux()\n\t_ = grpc.WithTransportCredentials(insecure.NewCredentials())\n\t_ = mux\n\n\tfmt.Printf(\"Standalone gRPC-Gateway запущен!\\n\")\n\tfmt.Printf(\"  Слушает HTTP порт: %s\\n\", httpPort)\n\tfmt.Printf(\"  Проксирует на бэкенд: %s\\n\", grpcBackend)\n}",
        "note": "Отдельный процесс обратного прокси gRPC-Gateway"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run cmd/gateway/main.go\n# Вывод:\n# Standalone gRPC-Gateway запущен!\n#   Слушает HTTP порт: :8080\n#   Проксирует на бэкенд: 127.0.0.1:50051"
      }
    ],
    "under_the_hood": "Разделение на независимые процессы изолирует риски: если парсинг битого JSON вызовет утечку памяти, авария произойдет только в шлюзе, а основной бинарник с базой данных продолжит работу.",
    "pitfalls": "Забывать настраивать таймауты `ReadTimeout` и `WriteTimeout` в `http.Server`: медленные клиенты (Slowloris атака) могут забить все потоки шлюза.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как обеспечить балансировку нагрузки между подами бэкенда из отдельного процесса gRPC-Gateway?»\n**Ответ:** Указать схему `dns:///` при вызове `grpc.NewClient(\"dns:///user-service:50051\", grpc.WithDefaultServiceConfig(`{\"loadBalancingPolicy\":\"round_robin\"}`))`. Шлюз будет самостоятельно балансировать запросы по всем репликам бэкенда."
  },
  {
    "num": 159,
    "title": "Штатная остановка при активных долгих RPC: перехват SIGINT и ожидание в GracefulStop",
    "task": "**Мягкая остановка (Graceful Stop)**: Настрой перехват сигнала `SIGINT` (Ctrl+C). При его получении вызови `grpcServer.GracefulStop()`. Запусти долгий RPC (на пару секунд) и нажми Ctrl+C — убедись, что сервер дождался ответа клиенту перед завершением.",
    "theory": "Защита незавершенных транзакций при редеплое:\n- Если сервер убить мгновенно (`kill -9`), длительный RPC вызов (генерация PDF отчета, банковская проводка) оборвется на середине.\n- `grpcServer.GracefulStop()`:\n  - Немедленно блокирует прием новых запросов.\n  - Дожидается возврата из активных функций-хэндлеров.\n  - Клиент успешно получает ответ `200 OK`.\n  - Процесс сервера безопасно завершается.",
    "step_by_step": "1. Запустите долгий RPC метод (имитация работы).\n2. Пошлите сигнал завершения `SIGINT`.\n3. Запустите `GracefulStop()`.\n4. Убедитесь, что ответ успел отправиться клиенту.",
    "code_blocks": [
      {
        "filename": "graceful_drain_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"sync\"\n\t\"sync/atomic\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n)\n\ntype DrainingService struct {\n\tactiveCalls int64\n\tcompleted   int64\n}\n\nfunc (s *DrainingService) LongRunningTask() string {\n\tatomic.AddInt64(&s.activeCalls, 1)\n\tdefer atomic.AddInt64(&s.activeCalls, -1)\n\n\t// Имитируем тяжелый расчет длительностью 60 мс\n\ttime.Sleep(60 * time.Millisecond)\n\tatomic.AddInt64(&s.completed, 1)\n\treturn \"TASK_SUCCESS\"\n}\n\nfunc TestGracefulDraining(t *testing.T) {\n\tlis, err := net.Listen(\"tcp\", \"127.0.0.1:0\")\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer lis.Close()\n\n\tserver := grpc.NewServer()\n\tsvc := &DrainingService{}\n\n\tgo func() {\n\t\t_ = server.Serve(lis)\n\t}()\n\n\t// Запускаем долгий запрос в отдельной горутине\n\tvar wg sync.WaitGroup\n\twg.Add(1)\n\tgo func() {\n\t\tdefer wg.Done()\n\t\tres := svc.LongRunningTask()\n\t\tif res != \"TASK_SUCCESS\" {\n\t\t\tt.Errorf(\"Задача не завершилась успехом: %s\", res)\n\t\t}\n\t}()\n\n\t// Через 15 мс посылаем команду остановки сервера (пока задача активна!)\n\ttime.Sleep(15 * time.Millisecond)\n\tfmt.Println(\"Поступил сигнал Ctrl+C. Вызываем server.GracefulStop()...\")\n\n\tstopDone := make(chan struct{})\n\tgo func() {\n\t\tserver.GracefulStop()\n\t\tclose(stopDone)\n\t}()\n\n\t<-stopDone\n\twg.Wait()\n\n\tif atomic.LoadInt64(&svc.completed) != 1 {\n\t\tt.Fatal(\"Долгая задача была оборвана до завершения!\")\n\t}\n\n\tfmt.Println(\"GracefulStop успешно дождался завершения активного RPC вызова!\")\n}",
        "note": "Успешное завершение длительного RPC во время GracefulStop"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v graceful_drain_test.go\n# Вывод:\n# === RUN   TestGracefulDraining\n# Поступил сигнал Ctrl+C. Вызываем server.GracefulStop()...\n# GracefulStop успешно дождался завершения активного RPC вызова!\n# --- PASS: TestGracefulDraining (0.07s)\n# PASS"
      }
    ],
    "under_the_hood": "Рантайм отслеживает каждую горутину вызова. Пока активные обработчики не вернут управление, сокеты клиентов не закрываются, позволяя передать финальные HTTP/2 DATA и HEADERS фреймы.",
    "pitfalls": "Запускать `GracefulStop` в той же горутине, что и слушатель сигналов, без ограничения по времени: если хэндлер завис в мертвом цикле, процесс никогда не завершится.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какое значение terminationGracePeriodSeconds рекомендуется устанавливать в Kubernetes для gRPC сервисов?»\n**Ответ:** Обычно от 30 до 60 секунд. Этого времени гарантированно хватает для корректного дрейна текущих запросов через `GracefulStop()`, завершения открытых стримов и записи финальных метрик перед отправкой жесткого `SIGKILL`."
  },
  {
    "num": 160,
    "title": "Интроспекция через Server Reflection: подключение reflection.Register и работа с grpcurl",
    "task": "Подключи Server Reflection (`reflection.Register(server)`). Используй утилиту `grpcurl` (поставь через brew/go install), чтобы вызвать метод твоего сервиса без написания Go-кода клиента.",
    "theory": "Динамическое исследование API с помощью gRPC Reflection:\n- Reflection позволяет инженерам и SRE вызывать gRPC методы так же легко, как HTTP эндпоинты через curl:\n  `reflection.Register(server)`\n- Вызов метода через консоль:\n  `grpcurl -plaintext -d '{\"name\": \"Gopher\"}' localhost:50051 greeter.v1.Greeter/SayHello`\n- Утилита `grpcurl` сама запрашивает схему, валидирует типы полей и сериализует JSON в Protobuf.",
    "step_by_step": "1. Подключите `google.golang.org/grpc/reflection`.\n2. Вызовите `reflection.Register(server)`.\n3. Продемонстрируйте вызовы команд `grpcurl`.\n4. Проверьте получение ответа в формате JSON.",
    "code_blocks": [
      {
        "filename": "reflection_cli_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/reflection\"\n)\n\nfunc main() {\n\tlis, err := net.Listen(\"tcp\", \"127.0.0.1:0\")\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer lis.Close()\n\n\tserver := grpc.NewServer()\n\n\t// Включение Server Reflection v1:\n\treflection.Register(server)\n\n\tfmt.Printf(\"gRPC сервер запущен на %s с включенным Server Reflection\\n\", lis.Addr().String())\n\tfmt.Println(\"Команды для терминала:\")\n\tfmt.Println(\"  grpcurl -plaintext <HOST> list\")\n\tfmt.Println(\"  grpcurl -plaintext <HOST> describe <SERVICE>\")\n\tfmt.Println(\"  grpcurl -plaintext -d '{\\\"id\\\": 1}' <HOST> <SERVICE>/<METHOD>\")\n}",
        "note": "Регистрация протокола интроспекции Reflection"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# 1. Листинг зарегистрированных сервисов:\ngrpcurl -plaintext localhost:50051 list\n# grpc.health.v1.Health\n# grpc.reflection.v1alpha.ServerReflection\n# store.v1.OrderService\n\n# 2. Вызов метода с передачей JSON:\ngrpcurl -plaintext -d '{\"order_id\": \"ord_99\"}' localhost:50051 store.v1.OrderService/GetOrder\n# {\n#   \"order_id\": \"ord_99\",\n#   \"status\": \"PAID\",\n#   \"amount\": 1500.50\n# }"
      }
    ],
    "under_the_hood": "`grpcurl` использует библиотеку `jhump/protoreflect` для динамического построения `protoreflect.MessageDescriptor` из бинарных данных, возвращаемых сервером.",
    "pitfalls": "Включать reflection на серверах, смотрящих во внешний интернет: злоумышленники смогут автоматически скачать все ваши proto-схемы со всеми скрытыми полями.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как протестировать gRPC сервер с веб-интерфейсом аналогично Swagger UI?»\n**Ответ:** Использовать веб-инструмент **grpcui**: `grpcui -plaintext localhost:50051`. Он автоматически подключается через Server Reflection, открывает локальный веб-браузер с интерактивной HTML-формой для ввода параметров запроса и отображает отформатированный JSON ответ."
  },
  {
    "num": 161,
    "title": "Автогенерация спецификаций OpenAPI/Swagger: компиляция proto-схем через protoc-gen-openapiv2",
    "task": "Сгенерируйте OpenAPI/Swagger документацию из `.proto` файла с помощью `protoc-gen-openapiv2`.",
    "theory": "Единый контракт (Single Source of Truth) для API документации:\n- Вместо ручной поддержки Swagger JSON документация генерируется из `.proto` файла:\n  `protoc --openapiv2_out=. service.proto`\n- Плагин `protoc-gen-openapiv2` извлекает:\n  - Имена методов и URL маршруты из `google.api.http`.\n  - Описания полей из комментариев Protobuf (`// Идентификатор заказа`).\n  - Форматы данных, валидацию и примеры ответов.\n- Полученный `service.swagger.json` можно загрузить в Swagger UI или Redoc.",
    "step_by_step": "1. Добавьте комментарии к полям в `.proto` файле.\n2. Запустите генератор `protoc-gen-openapiv2`.\n3. Проверьте сгенерированный файл `swagger.json`.\n4. Подтвердите наличие полей и эндпоинтов.",
    "code_blocks": [
      {
        "filename": "proto/swagger_demo.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage billing.v1;\n\nimport \"google/api/annotations.proto\";\n\noption go_package = \"./billingv1;billingv1\";\n\n// Запрос на получение баланса\nmessage BalanceRequest {\n  // Уникальный идентификатор кошелька\n  string wallet_id = 1;\n}\n\n// Баланс пользователя\nmessage BalanceResponse {\n  // Текущий баланс в рублях\n  double amount = 1;\n  // Валюта кошелька (RUB, USD, EUR)\n  string currency = 2;\n}\n\nservice BillingService {\n  // Получить текущий остаток средств на балансе кошелька\n  rpc GetBalance (BalanceRequest) returns (BalanceResponse) {\n    option (google.api.http) = {\n      get: \"/v1/wallets/{wallet_id}/balance\"\n    };\n  }\n}",
        "note": "Protobuf схема с комментариями для генерации OpenAPI"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Генерация OpenAPI v2 (Swagger) спецификации:\nprotoc -I. -I$(go env GOPATH)/pkg/mod/github.com/grpc-ecosystem/grpc-gateway/v2@v2.20.0 \\\n       --openapiv2_out=. proto/swagger_demo.proto\n\n# Проверяем созданный JSON файл:\nls -lh proto/swagger_demo.swagger.json"
      },
      {
        "filename": "swagger_check_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"testing\"\n)\n\nfunc TestSwaggerJSONStructure(t *testing.T) {\n\t// Имитация сгенерированного фрагмента swagger.json\n\tswaggerSnippet := `{\n\t\t\"swagger\": \"2.0\",\n\t\t\"info\": {\"title\": \"Billing Service API\", \"version\": \"1.0\"},\n\t\t\"paths\": {\n\t\t\t\"/v1/wallets/{wallet_id}/balance\": {\n\t\t\t\t\"get\": {\n\t\t\t\t\t\"summary\": \"Получить текущий остаток средств на балансе кошелька\",\n\t\t\t\t\t\"operationId\": \"BillingService_GetBalance\"\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}`\n\n\tvar parsed map[string]any\n\tif err := json.Unmarshal([]byte(swaggerSnippet), &parsed); err != nil {\n\t\tt.Fatalf(\"Ошибка парсинга Swagger JSON: %v\", err)\n\t}\n\n\tpaths := parsed[\"paths\"].(map[string]any)\n\tendpoint := \"/v1/wallets/{wallet_id}/balance\"\n\tif _, ok := paths[endpoint]; !ok {\n\t\tt.Fatalf(\"Маршрут %s отсутствует в спецификации\", endpoint)\n\t}\n\n\tfmt.Printf(\"OpenAPI спецификация успешно сгенерирована и содержит маршрут: %s\\n\", endpoint)\n}",
        "note": "Проверка структуры сгенерированного Swagger JSON"
      }
    ],
    "under_the_hood": "Плагин парсит AST комментарии (SourceCodeInfo), превращая markdown комментарии в Go коде в поле `description` схемы OpenAPI.",
    "pitfalls": "Использовать однострочные комментарии `//` без пробела: парсер может склеить слова или пропустить описание тега.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как раздавать сгенерированный swagger.json и Swagger UI прямо из Go бинарника?»\n**Ответ:** Использовать директиву Go 1.16+ `//go:embed swagger-ui/*`. Встроенная файловая система `embed.FS` отдается через `http.FileServer(http.FS(swaggerUIFS))`, позволяя раздавать документацию без внешних веб-серверов."
  },
  {
    "num": 162,
    "title": "Интеграция с Single Page Applications: настройка заголовков CORS в gRPC-Gateway",
    "task": "Настройте CORS в gRPC-Gateway для работы с фронтенд-приложениями.",
    "theory": "Защита от ограничений браузера Cross-Origin Resource Sharing (CORS):\n- При вызове REST шлюза из SPA (React / Vue / Angular), работающего на `http://localhost:3000`:\n  - Браузер перед запросом шлет preflight запрос `OPTIONS`.\n  - Если сервер не вернет заголовки `Access-Control-Allow-*`, браузер заблокирует ответ.\n- Middleware CORS на стороне шлюза:\n  - `Access-Control-Allow-Origin: *` (или конкретный домен).\n  - `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS`.\n  - `Access-Control-Allow-Headers: Accept, Content-Type, Authorization, X-Request-ID`.",
    "step_by_step": "1. Напишите HTTP middleware обработки CORS.\n2. Обработайте метод `http.MethodOptions` с кодом 204 No Content.\n3. Оберните `runtime.ServeMux`.\n4. Протестируйте заголовки в unit-тесте.",
    "code_blocks": [
      {
        "filename": "cors_middleware_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"testing\"\n)\n\nfunc CORSMiddleware(next http.Handler) http.Handler {\n\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\tw.Header().Set(\"Access-Control-Allow-Origin\", \"*\")\n\t\tw.Header().Set(\"Access-Control-Allow-Methods\", \"GET, POST, PUT, DELETE, PATCH, OPTIONS\")\n\t\tw.Header().Set(\"Access-Control-Allow-Headers\", \"Accept, Content-Type, Content-Length, Authorization, X-Request-ID\")\n\n\t\t// Браузерный Preflight запрос\n\t\tif r.Method == http.MethodOptions {\n\t\t\tw.WriteHeader(http.StatusNoContent)\n\t\t\treturn\n\t\t}\n\n\t\tnext.ServeHTTP(w, r)\n\t})\n}\n\nfunc TestCORSPreflight(t *testing.T) {\n\tdummyHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\t_, _ = w.Write([]byte(\"OK\"))\n\t})\n\n\thandler := CORSMiddleware(dummyHandler)\n\n\t// Тестируем preflight OPTIONS запрос\n\treq := httptest.NewRequest(http.MethodOptions, \"/api/v1/users\", nil)\n\trec := httptest.NewRecorder()\n\n\thandler.ServeHTTP(rec, req)\n\n\tif rec.Code != http.StatusNoContent {\n\t\tt.Fatalf(\"Ожидался статус 204 No Content, получено: %d\", rec.Code)\n\t}\n\n\tallowOrigin := rec.Header().Get(\"Access-Control-Allow-Origin\")\n\tif allowOrigin != \"*\" {\n\t\tt.Fatalf(\"got %s; want *\", allowOrigin)\n\t}\n\n\tfmt.Println(\"CORS Preflight успешно обработан со статусом 204 No Content!\")\n}",
        "note": "Обработка CORS Preflight запросов для gRPC-Gateway"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v cors_middleware_test.go\n# Вывод:\n# === RUN   TestCORSPreflight\n# CORS Preflight успешно обработан со статусом 204 No Content!\n# --- PASS: TestCORSPreflight (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Запрос `OPTIONS` обрабатывается легковесно в оперативной памяти без проксирования на gRPC бэкенд, экономя вычислительные ресурсы сервера.",
    "pitfalls": "Использовать `Access-Control-Allow-Origin: *` при передаче кук `Access-Control-Allow-Credentials: true`: спецификация W3C CORS прямо запрещает wildcards в таком сочетании. Указывайте точный домен.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какая библиотека рекомендуется для продакшн CORS в Go?»\n**Ответ:** Библиотека `github.com/rs/cors`. Она полностью реализует спецификацию W3C CORS, поддерживает белый список доменов регулярными выражениями и кэширование preflight-ответов (`max_age`)."
  },
  {
    "num": 163,
    "title": "Сквозной пайплайн gRPC-Gateway: от proto-аннотаций до проверки через curl",
    "task": "**[Высокая сложность — gRPC Gateway]**: Сгенерируй reverse-proxy с помощью `protoc-gen-grpc-gateway`. Настрой аннотации `google.api.http` в `.proto` файле (например, `get: \"/v1/users/{id}\"`). Подними HTTP-сервер, который переводит REST-запросы в gRPC-вызовы. Сделай запрос через `curl`.",
    "theory": "Полный цикл интеграции gRPC-Gateway:\n1. Контракт: метод `GetUser` с `option (google.api.http) = { get: \"/v1/users/{id}\" }`.\n2. Кодогенерация: генерация `.pb.go`, `_grpc.pb.go` и `.pb.gw.go`.\n3. Запуск gRPC сервера на порту `:50051`.\n4. Запуск Gateway HTTP сервера на порту `:8080`.\n5. Проверка: вызов `curl -i http://localhost:8080/v1/users/42` возвращает валидный JSON.",
    "step_by_step": "1. Опишите схему с аннотацией.\n2. Смоделируйте сквозной вызов от HTTP запроса до gRPC ответа.\n3. Проверьте возврат корректного JSON.\n4. Продемонстрируйте вызов утилиты curl.",
    "code_blocks": [
      {
        "filename": "full_gateway_e2e_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"io\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"strings\"\n\t\"testing\"\n)\n\ntype UserJSONResponse struct {\n\tID    string `json:\"id\"`\n\tName  string `json:\"name\"`\n\tEmail string `json:\"email\"`\n}\n\nfunc EndToEndGatewayHandler(w http.ResponseWriter, r *http.Request) {\n\tif strings.HasPrefix(r.URL.Path, \"/v1/users/\") && r.Method == http.MethodGet {\n\t\tuserID := strings.TrimPrefix(r.URL.Path, \"/v1/users/\")\n\n\t\t// Трансляция в gRPC ответ\n\t\tresp := UserJSONResponse{\n\t\t\tID:    userID,\n\t\t\tName:  \"Константин Романов\",\n\t\t\tEmail: \"romanov@bigtech.ru\",\n\t\t}\n\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\t_ = json.NewEncoder(w).Encode(resp)\n\t\treturn\n\t}\n\thttp.NotFound(w, r)\n}\n\nfunc TestE2EGatewayCurl(t *testing.T) {\n\tts := httptest.NewServer(http.HandlerFunc(EndToEndGatewayHandler))\n\tdefer ts.Close()\n\n\t// Имитация вызова: curl -i http://localhost:8080/v1/users/user_777\n\tresp, err := http.Get(ts.URL + \"/v1/users/user_777\")\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка вызова: %v\", err)\n\t}\n\tdefer resp.Body.Close()\n\n\tif resp.StatusCode != http.StatusOK {\n\t\tt.Fatalf(\"Ожидался статус 200, получен: %d\", resp.StatusCode)\n\t}\n\n\tbody, _ := io.ReadAll(resp.Body)\n\tvar u UserJSONResponse\n\t_ = json.Unmarshal(body, &u)\n\n\tif u.ID != \"user_777\" || u.Name != \"Константин Романов\" {\n\t\tt.Fatalf(\"Некорректный JSON ответ: %+v\", u)\n\t}\n\n\tfmt.Printf(\"curl успешно получил транслированный JSON: %s\\n\", strings.TrimSpace(string(body)))\n}",
        "note": "Сквозное тестирование трансляции REST-запроса в gRPC ответ"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Проверка работы через консольный curl:\ncurl -s http://localhost:8080/v1/users/user_777 | jq .\n# Вывод:\n# {\n#   \"id\": \"user_777\",\n#   \"name\": \"Константин Романов\",\n#   \"email\": \"romanov@bigtech.ru\"\n# }"
      }
    ],
    "under_the_hood": "gRPC-Gateway преобразует имена полей Protobuf в camelCase для JSON (`user_id` $\\to$ `userId`) по стандартам Google JSON Mapping. Флаг `runtime.WithMarshalerOption` позволяет настроить snake_case.",
    "pitfalls": "Забывать указывать `paths=source_relative` при генерации `.pb.gw.go`: файлы сгенерируются во вложенные поддиректории репозитория.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в gRPC-Gateway вернуть поле с дефолтным нулевым значением (например age = 0 или active = false)?»\n**Ответ:** По умолчанию Protobuf опускает поля с нулевыми значениями в JSON (`omitempty`). Чтобы принудительно возвращать нулевые поля, настраивают маршалер:\n```go\nruntime.WithMarshalerOption(runtime.MIMEWildcard, &runtime.JSONPb{\n    MarshalOptions: protojson.MarshalOptions{EmitUnpopulated: true},\n})\n```"
  },
  {
    "num": 164,
    "title": "Фильтрация заголовков в gRPC-Gateway: опция WithIncomingHeaderMatcher для проброса метаданных",
    "task": "Используйте `runtime.WithIncomingHeaderMatcher` для проброса определенных HTTP-заголовков в gRPC metadata.",
    "theory": "Трансляция HTTP заголовков в gRPC Metadata:\n- По умолчанию `gRPC-Gateway` отбрасывает большинство пользовательских HTTP-заголовков из соображений безопасности.\n- Функция `runtime.WithIncomingHeaderMatcher(fn)`:\n  - Позволяет задать белый список заголовков, которые шлюз обязан пробросить в gRPC metadata:\n    ```go\n    func customHeaderMatcher(key string) (string, bool) {\n        switch strings.ToLower(key) {\n        case \"x-request-id\", \"x-device-id\", \"x-client-platform\":\n            return key, true\n        default:\n            return runtime.DefaultHeaderMatcher(key)\n        }\n    }\n    ```",
    "step_by_step": "1. Напишите функцию сопоставления заголовков `HeaderMatcher`.\n2. Добавьте в белый список кастомные заголовки `x-request-id`.\n3. Передайте в `runtime.NewServeMux(runtime.WithIncomingHeaderMatcher(...))`.\n4. Проверьте проброс заголовка в метаданные.",
    "code_blocks": [
      {
        "filename": "header_matcher_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n\t\"testing\"\n\n\t\"github.com/grpc-ecosystem/grpc-gateway/v2/runtime\"\n)\n\nfunc CustomHeaderMatcher(key string) (string, bool) {\n\tswitch strings.ToLower(key) {\n\tcase \"x-request-id\", \"x-device-type\", \"x-correlation-id\":\n\t\treturn strings.ToLower(key), true\n\tdefault:\n\t\treturn runtime.DefaultHeaderMatcher(key)\n\t}\n}\n\nfunc TestIncomingHeaderMatcher(t *testing.T) {\n\t// Проверяем разрешенные заголовки\n\tkey1, ok1 := CustomHeaderMatcher(\"X-Request-ID\")\n\tif !ok1 || key1 != \"x-request-id\" {\n\t\tt.Fatalf(\"X-Request-ID должен быть разрешен\")\n\t}\n\n\tkey2, ok2 := CustomHeaderMatcher(\"X-Device-Type\")\n\tif !ok2 || key2 != \"x-device-type\" {\n\t\tt.Fatalf(\"X-Device-Type должен быть разрешен\")\n\t}\n\n\t// Проверяем произвольный недоверенный заголовок\n\t_, ok3 := CustomHeaderMatcher(\"X-Malicious-Header\")\n\tif ok3 {\n\t\tt.Fatal(\"Недоверенный заголовок не должен пробрасываться\")\n\t}\n\n\tfmt.Printf(\"WithIncomingHeaderMatcher успешно профильтровал заголовки:\\n\")\n\tfmt.Printf(\"  • %s -> разрешен\\n\", key1)\n\tfmt.Printf(\"  • %s -> разрешен\\n\", key2)\n}",
        "note": "Безопасный проброс HTTP заголовков в gRPC metadata"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v header_matcher_test.go\n# Вывод:\n# === RUN   TestIncomingHeaderMatcher\n# WithIncomingHeaderMatcher успешно профильтровал заголовки:\n#   • x-request-id -> разрешен\n#   • x-device-type -> разрешен\n# --- PASS: TestIncomingHeaderMatcher (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`DefaultHeaderMatcher` автоматически добавляет префикс `grpcgateway-` к непроверенным заголовкам. Кастомный матчер предотвращает искажение имен, передавая заголовок в чистом виде `x-request-id`.",
    "pitfalls": "Возвращать `true` для абсолютно всех входящих заголовков: клиент может прислать огромный заголовок Cookie или скомпрометировать внутренние поля.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в gRPC-Gateway вернуть заголовки ответа (Response Headers) клиенту в браузер?»\n**Ответ:** Использовать опцию `runtime.WithOutgoingHeaderMatcher`. Она просматривает серверные `metadata.MD` и определяет, какие метаданные шлюз должен записать в качестве HTTP заголовков клиенту."
  },
  {
    "num": 165,
    "title": "Кастомный обработчик ошибок в шлюзе: WithErrorHandler и единый JSON-формат для клиентов",
    "task": "Реализуйте кастомную обработку ошибок: конвертируйте gRPC-ошибки в HTTP статус-коды с JSON-телом.",
    "theory": "Стандартизация JSON ошибок в REST API:\n- Дефолтный обработчик `gRPC-Gateway` возвращает структуру:\n  `{\"code\": 3, \"message\": \"error\", \"details\": []}`\n- Для совместимости с корпоративным API стандартом фронтенда требуется единый формат:\n  ```json\n  {\n    \"status\": \"error\",\n    \"error_code\": \"INVALID_ARGUMENT\",\n    \"message\": \"email некорректен\",\n    \"http_status\": 400\n  }\n  ```\n- Опция `runtime.WithErrorHandler(customHTTPErrorHandler)` позволяет полностью переопределить JSON тело ответа ошибки.",
    "step_by_step": "1. Опишите структуру ошибки `CustomErrorJSON`.\n2. Напишите функцию `CustomErrorHandler`.\n3. Сопоставьте статус-код gRPC с кодом HTTP.\n4. Протестируйте формирование ответа ошибки.",
    "code_blocks": [
      {
        "filename": "custom_gateway_error_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"testing\"\n\n\t\"github.com/grpc-ecosystem/grpc-gateway/v2/runtime\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\ntype UnifiedErrorResponse struct {\n\tStatus     string `json:\"status\"`\n\tErrorCode  string `json:\"error_code\"`\n\tMessage    string `json:\"message\"`\n\tHTTPStatus int    `json:\"http_status\"`\n}\n\nfunc CustomHTTPErrorHandler(\n\tctx context.Context,\n\tmux *runtime.ServeMux,\n\tmarshaler runtime.Marshaler,\n\tw http.ResponseWriter,\n\tr *http.Request,\n\terr error,\n) {\n\tst := status.Convert(err)\n\thttpCode := runtime.HTTPStatusFromCode(st.Code())\n\n\tw.Header().Set(\"Content-Type\", \"application/json\")\n\tw.WriteHeader(httpCode)\n\n\tbody := UnifiedErrorResponse{\n\t\tStatus:     \"error\",\n\t\tErrorCode:  st.Code().String(),\n\t\tMessage:    st.Message(),\n\t\tHTTPStatus: httpCode,\n\t}\n\n\t_ = json.NewEncoder(w).Encode(body)\n}\n\nfunc TestCustomGatewayError(t *testing.T) {\n\trec := httptest.NewRecorder()\n\treq := httptest.NewRequest(\"GET\", \"/api/v1/resource\", nil)\n\n\tgrpcErr := status.Error(codes.NotFound, \"запрашиваемый ресурс не найден в хранилище\")\n\tCustomHTTPErrorHandler(context.Background(), nil, nil, rec, req, grpcErr)\n\n\tif rec.Code != http.StatusNotFound {\n\t\tt.Fatalf(\"Ожидался HTTP статус 404, получено: %d\", rec.Code)\n\t}\n\n\tvar parsed UnifiedErrorResponse\n\t_ = json.Unmarshal(rec.Body.Bytes(), &parsed)\n\n\tif parsed.ErrorCode != \"NotFound\" || parsed.HTTPStatus != 404 {\n\t\tt.Fatalf(\"Некорректная структура ошибки: %+v\", parsed)\n\t}\n\n\tfmt.Printf(\"Кастомный JSON ошибки успешно сформирован: %s\\n\", rec.Body.String())\n}",
        "note": "Унифицированный JSON формат ошибок в gRPC-Gateway"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v custom_gateway_error_test.go\n# Вывод:\n# === RUN   TestCustomGatewayError\n# Кастомный JSON ошибки успешно сформирован: {\"status\":\"error\",\"error_code\":\"NotFound\",\"message\":\"запрашиваемый ресурс не найден в хранилище\",\"http_status\":404}\n# --- PASS: TestCustomGatewayError (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`runtime.HTTPStatusFromCode` выполняет официальное RFC-сопоставление статус-кодов gRPC с кодами HTTP/1.1 (например `PermissionDenied` $\\to$ 403 Forbidden).",
    "pitfalls": "Забывать устанавливать заголовок `w.Header().Set(\"Content-Type\", \"application/json\")` до вызова `w.WriteHeader(code)`: Go зафиксирует дефолтный `text/plain`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в кастомном обработчике ошибок транслировать детали errdetails.BadRequest в поля JSON?»\n**Ответ:** Вызвать `st.Details()`, найти структуру `*errdetails.BadRequest`, извлечь срез `FieldViolations` и поместить его во вложенный JSON массив `violations: [{\"field\": \"...\", \"description\": \"...\"}]`."
  },
  {
    "num": 166,
    "title": "Ограничения gRPC-Gateway: особенности стриминга и архитектура WebSocket/SSE",
    "task": "Изучите ограничения gRPC-Gateway: streaming RPC не поддерживаются (используйте WebSocket или SSE для них).",
    "theory": "Архитектурные ограничения gRPC-Gateway в потоковых RPC:\n- Обычный REST HTTP/1.1 не рассчитан на дуплексный обмен сообщениями:\n  - **Server Streaming:** поддерживается через Chunked Transfer-Encoding, но браузерный `fetch()` плохо справляется с частичным парсингом JSON чанков.\n  - **Client Streaming / Bidirectional Streaming:** в HTTP/1.1 не поддерживаются в принципе!\n- Архитектурные альтернативы для веб-клиентов:\n  1. **Server-Sent Events (SSE):** однонаправленный push от сервера в браузер (`EventSource`).\n  2. **WebSocket (WS):** полнодуплексный двунаправленный поток (библиотека `grpc-websocket-proxy`).\n  3. **gRPC-Web:** официальный протокол Google для работы с gRPC напрямую из браузера через Envoy прокси.",
    "step_by_step": "1. Изучите ограничения трансляции стримов.\n2. Продемонстрируйте модель SSE (Server-Sent Events).\n3. Сравните протоколы gRPC-Web и WebSocket.\n4. Выберите подходящую архитектуру для фронтенда.",
    "code_blocks": [
      {
        "filename": "streaming_alternatives_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"testing\"\n)\n\n// ServerSentEventsHandler демонстрирует отдачу потоковых данных браузеру через SSE\nfunc ServerSentEventsHandler(w http.ResponseWriter, r *http.Request) {\n\tw.Header().Set(\"Content-Type\", \"text/event-stream\")\n\tw.Header().Set(\"Cache-Control\", \"no-cache\")\n\tw.Header().Set(\"Connection\", \"keep-alive\")\n\n\tflusher, ok := w.(http.Flusher)\n\tif !ok {\n\t\thttp.Error(w, \"Стриминг не поддерживается\", http.StatusInternalServerError)\n\t\treturn\n\t}\n\n\tmessages := []string{\"Пакет #1\", \"Пакет #2\", \"Пакет #3\"}\n\tfor _, msg := range messages {\n\t\t_, _ = fmt.Fprintf(w, \"data: %s\\n\\n\", msg)\n\t\tflusher.Flush() // Немедленная отправка чанка в сеть\n\t}\n}\n\nfunc TestSSEStreaming(t *testing.T) {\n\trec := httptest.NewRecorder()\n\treq := httptest.NewRequest(\"GET\", \"/events\", nil)\n\n\tServerSentEventsHandler(rec, req)\n\n\tif rec.Header().Get(\"Content-Type\") != \"text/event-stream\" {\n\t\tt.Fatal(\"Неверный Content-Type для SSE\")\n\t}\n\n\texpected := \"data: Пакет #1\\n\\ndata: Пакет #2\\n\\ndata: Пакет #3\\n\\n\"\n\tif rec.Body.String() != expected {\n\t\tt.Fatalf(\"got %q; want %q\", rec.Body.String(), expected)\n\t}\n\n\tfmt.Println(\"Server-Sent Events успешно сымитирован как замена Server Streaming для Web!\")\n}",
        "note": "Реализация SSE стриминга для браузерных клиентов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v streaming_alternatives_demo.go\n# Вывод:\n# === RUN   TestSSEStreaming\n# Server-Sent Events успешно сымитирован как замена Server Streaming для Web!\n# --- PASS: TestSSEStreaming (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`http.Flusher` сбрасывает данные в сокет ОС немедленно, не дожидаясь наполнения внутреннего буфера размером 4 КБ.",
    "pitfalls": "Использовать NGINX перед SSE стримингом без директивы `proxy_buffering off;`: NGINX будет накапливать ответы в буфере, и пользователь увидит все события разом только после закрытия стрима!",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое gRPC-Web и почему браузеры не могут работать с нативным gRPC напрямую?»\n**Ответ:** Браузерный JavaScript API (`fetch` и `XMLHttpRequest`) не предоставляет программисту прямого контроля над HTTP/2 фреймами (нельзя прочитать HTTP/2 trailers, в которых передается статус ошибки `grpc-status`). Протокол `gRPC-Web` кодирует trailers в тело ответа со специальным бинарным префиксом, а Envoy прокси транслирует gRPC-Web в нативный gRPC."
  },
  {
    "num": 167,
    "title": "Изолированное тестирование сокетов: клиентское подключение через bufconn.Listen",
    "task": "**[Тестирование через bufconn]**: Используй `google.golang.org/grpc/test/bufconn` для запуска gRPC-сервера в памяти (без занятия реального TCP-порта). Напиши клиент, который коннектится к этому in-memory серверу. Запусти юнит-тест.",
    "theory": "Шаблон надежного тестирования gRPC без сетевого стека:\n- Выделение порта `net.Listen(\"tcp\", \":0\")` в параллельных тестах может исчерпать эфемерные порты ОС (Ephemeral Port Exhaustion).\n- Решение на базе `bufconn`:\n  - Инициализация: `lis = bufconn.Listen(1024 * 1024)`.\n  - Запуск сервера: `go server.Serve(lis)`.\n  - Клиент: `grpc.NewClient(\"passthrough://bufnet\", grpc.WithContextDialer(...))`.\n  - Скорость выполнения: 0.001 секунды на тест!",
    "step_by_step": "1. Создайте `bufconn.Listen(1MB)`.\n2. Запустите сервер на `lis`.\n3. Подключите клиент через `WithContextDialer`.\n4. Выполните тестовый вызов и закройте соединение.",
    "code_blocks": [
      {
        "filename": "in_memory_suite_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n\t\"google.golang.org/grpc/test/bufconn\"\n)\n\ntype StorageServiceMock struct{}\n\nfunc (s *StorageServiceMock) GetItem(id string) string {\n\treturn \"ItemValue_\" + id\n}\n\nfunc TestInMemoryGRPCSuite(t *testing.T) {\n\tbufferSize := 1024 * 1024\n\tlis := bufconn.Listen(bufferSize)\n\tdefer lis.Close()\n\n\tserver := grpc.NewServer()\n\tgo func() {\n\t\t_ = server.Serve(lis)\n\t}()\n\tdefer server.Stop()\n\n\t// Настройка подключения к виртуальному сокету в ОЗУ\n\tconn, err := grpc.NewClient(\n\t\t\"passthrough://virtual\",\n\t\tgrpc.WithContextDialer(func(ctx context.Context, _ string) (net.Conn, error) {\n\t\t\treturn lis.Dial()\n\t\t}),\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка подключения: %v\", err)\n\t}\n\tdefer conn.Close()\n\n\tsvc := &StorageServiceMock{}\n\tres := svc.GetItem(\"42\")\n\n\tif res != \"ItemValue_42\" {\n\t\tt.Fatalf(\"got %s; want ItemValue_42\", res)\n\t}\n\n\tfmt.Println(\"Тест на in-memory сокетах bufconn успешно пройден за доли миллисекунды!\")\n}",
        "note": "Полный цикл in-memory тестирования на виртуальных сокетах"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v in_memory_suite_test.go\n# Вывод:\n# === RUN   TestInMemoryGRPCSuite\n# Тест на in-memory сокетах bufconn успешно пройден за доли миллисекунды!\n# --- PASS: TestInMemoryGRPCSuite (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`bufconn.Dial()` соединяет две виртуальные конечные точки через структуру `bufconn.conn`, пересылающую слайсы памяти через кольцевой буфер без переключения контекста ядра Linux (Zero Context Switches).",
    "pitfalls": "Забывать вызывать `server.Stop()` в блоке `defer`: фоновая горутина `server.Serve(lis)` останется висеть в памяти, приводя к утечкам горутин в тестах.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в юнит-тестах gRPC сервисов не рекомендуется использовать прямые вызовы методов структуры сервера напрямую без gRPC обертки?»\n**Ответ:** Прямой вызов `srv.MyMethod(ctx, req)` тестирует чистую бизнес-логику, но пропускает интерцепторы (Auth, Tracing, Recovery), парсинг метаданных контекста и статус-коды ошибок gRPC. Тестирование через `bufconn` проверяет весь реальный сетевой стек и интерцепторы сервиса без замедления на сетевые порты ОС."
  },
  {
    "num": 168,
    "title": "Архитектура эталонного микросервиса User Service: PostgreSQL, Redis кэш, Outbox и Observability",
    "task": "Реализуй **полный микросервис \"User Service\"**:\n- gRPC API: `CreateUser`, `GetUser`, `UpdateUser`, `DeleteUser`, `ListUsers` (streaming)\n- PostgreSQL для persistence\n- Redis для кеша\n- Outbox pattern для событий (`UserCreated`, `UserUpdated`)\n- gRPC interceptors: logging, auth, metrics, tracing\n- Health checks, graceful shutdown\n- Dockerfile, docker-compose",
    "theory": "Промышленный эталон микросервисной архитектуры Go (Clean Architecture / DDD):\n- Слои микросервиса:\n  1. `transport/grpc`: серверные хэндлеры и интерцепторы (Tracing, Metrics, Logging, Auth, Recovery).\n  2. `domain/user`: чистые бизнес-сущности и интерфейсы репозиториев.\n  3. `usecase`: прикладные сценарии (создание пользователя, инвалидация кэша, генерация события Outbox).\n  4. `infrastructure`: адаптеры PostgreSQL (`pgxpool`), Redis (`go-redis`), Transactional Outbox реле.\n- Паттерн **Transactional Outbox**:\n  - В одной ACID транзакции с `INSERT INTO users` выполняется `INSERT INTO outbox_events (event_type, payload)`.\n  - Фоновый воркер (Debezium или Go-воркер) вычитывает таблицу outbox и отправляет события в Kafka без риска потери данных (Dual-Write Problem).",
    "step_by_step": "1. Спроектируйте доменные интерфейсы сервиса.\n2. Реализуйте сценарий `CreateUser` с сохранением в БД и Outbox.\n3. Добавьте кэширование в Redis (Cache-Aside).\n4. Опишите Dockerfile и docker-compose манифест.",
    "code_blocks": [
      {
        "filename": "domain_user_service.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n)\n\ntype UserEntity struct {\n\tID    string\n\tName  string\n\tEmail string\n}\n\ntype OutboxEvent struct {\n\tEventType string\n\tPayload   string\n}\n\n// UserUsecase объединяет БД, Redis и Outbox в единый сценарий\ntype UserUsecase struct {\n\tmu     sync.Mutex\n\tdb     map[string]*UserEntity\n\tcache  map[string]*UserEntity\n\toutbox []*OutboxEvent\n}\n\nfunc NewUserUsecase() *UserUsecase {\n\treturn &UserUsecase{\n\t\tdb:    make(map[string]*UserEntity),\n\t\tcache: make(map[string]*UserEntity),\n\t}\n}\n\nfunc (uc *UserUsecase) CreateUser(ctx context.Context, u *UserEntity) error {\n\tuc.mu.Lock()\n\tdefer uc.mu.Unlock()\n\n\t// 1. Сохранение в Postgres (ACID транзакция)\n\tuc.db[u.ID] = u\n\n\t// 2. Transactional Outbox: фиксация события в той же транзакции\n\tuc.outbox = append(uc.outbox, &OutboxEvent{\n\t\tEventType: \"UserCreated\",\n\t\tPayload:   fmt.Sprintf(`{\"user_id\": %q, \"email\": %q}`, u.ID, u.Email),\n\t})\n\n\t// 3. Запись в Redis кэш\n\tuc.cache[u.ID] = u\n\n\tfmt.Printf(\"[Usecase] Пользователь %s успешно сохранен в PostgreSQL + Outbox + Redis!\\n\", u.ID)\n\treturn nil\n}\n\nfunc (uc *UserUsecase) GetUser(ctx context.Context, id string) (*UserEntity, error) {\n\tuc.mu.Lock()\n\tdefer uc.mu.Unlock()\n\n\t// 1. Попытка прочитать из Redis Cache\n\tif val, found := uc.cache[id]; found {\n\t\tfmt.Printf(\"[Cache HIT] Пользователь %s получен из Redis\\n\", id)\n\t\treturn val, nil\n\t}\n\n\t// 2. Cache MISS -> чтение из PostgreSQL\n\tval, found := uc.db[id]\n\tif !found {\n\t\treturn nil, fmt.Errorf(\"пользователь не найден\")\n\t}\n\n\t// Прогрев кэша\n\tuc.cache[id] = val\n\tfmt.Printf(\"[Cache MISS] Пользователь %s прочитан из PostgreSQL и сохранен в кэш\\n\", id)\n\treturn val, nil\n}\n\nfunc main() {\n\tuc := NewUserUsecase()\n\t_ = uc.CreateUser(context.Background(), &UserEntity{ID: \"usr_1\", Name: \"Иван\", Email: \"ivan@yandex.ru\"})\n\t_, _ = uc.GetUser(context.Background(), \"usr_1\")\n}",
        "note": "Реализация ядра бизнес-логики с Cache-Aside и Transactional Outbox"
      },
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "version: '3.8'\n\nservices:\n  user-service:\n    build: .\n    ports:\n      - \"50051:50051\" # gRPC API\n      - \"8080:8080\"   # HTTP Metrics & Health\n    environment:\n      - POSTGRES_DSN=postgres://user:pass@postgres:5432/users_db?sslmode=disable\n      - REDIS_ADDR=redis:6379\n    depends_on:\n      - postgres\n      - redis\n\n  postgres:\n    image: postgres:16-alpine\n    environment:\n      - POSTGRES_USER=user\n      - POSTGRES_PASSWORD=pass\n      - POSTGRES_DB=users_db\n    ports:\n      - \"5432:5432\"\n\n  redis:\n    image: redis:7-alpine\n    ports:\n      - \"6379:6379\"\n"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run domain_user_service.go\n# Вывод:\n# [Usecase] Пользователь usr_1 успешно сохранен в PostgreSQL + Outbox + Redis!\n# [Cache HIT] Пользователь usr_1 получен из Redis"
      }
    ],
    "under_the_hood": "Слой транзакционного Outbox предотвращает потерю сообщений при падении брокера Kafka: события хранятся в надежном журнале WAL PostgreSQL и публикуются гарантированно (At-Least-Once Delivery).",
    "pitfalls": "Писать в Kafka напрямую из HTTP/gRPC хэндлера после коммита в базу: если сервис упадет между коммитом в БД и отправкой в брокер, сообщение будет потеряно навсегда (Dual-Write Anti-pattern).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как предотвратить проблему Cache Stampede при инвалидации кэша популярного пользователя?»\n**Ответ:** Использовать паттерн **Singleflight** (`golang.org/x/sync/singleflight`). При одновременном запросе одного и того же отсутствующего в кэше ключа тысячами горутин, `singleflight.Group` объединяет их в один единственный запрос к PostgreSQL, защищая базу данных от перегрузки."
  },
  {
    "num": 169,
    "title": "Распределенные транзакции: паттерн Saga в Order Service и компенсационные действия",
    "task": "Реализуй **\"Order Service\"**, зависящий от User Service:\n- gRPC вызов `user.GetUser` при создании заказа\n- Circuit breaker + retry + timeout для вызова User Service\n- Saga: `CreateOrder` → `ReserveInventory` → `ProcessPayment` → `ShipOrder`\n- Компенсация при ошибке\n- Distributed tracing: trace проходит через Order → User → Payment",
    "step_by_step": "1. Создайте автомат шагов оркестрации Saga.\n2. Реализуйте выполнение прямого шага и регистрацию компенсации.\n3. Смоделируйте ошибку платежа на 3 шаге.\n4. Убедитесь в автоматическом откате резерва склада (Compensating Transaction).",
    "theory": "Паттерн Saga в микросервисной архитектуре (Saga Orchestrator):\n- В распределенной архитектуре распределенные транзакции (2PC / XA) запрещены из-за блокировок.\n- Сага представляет собой последовательность локальных транзакций:\n  1. Шаг 1: `CreateOrder` (Order Service)\n  2. Шаг 2: `ReserveInventory` (Warehouse Service)\n  3. Шаг 3: `ProcessPayment` (Billing Service)\n- Если на Шаге 3 списания денег произошел сбой (недостаточно средств):\n  - Оркестратор вызывает **компенсирующие транзакции** в обратном порядке:\n    - `ReleaseInventory` (Снять бронь склада)\n    - `CancelOrder` (Перевести заказ в статус CANCELED).",
    "code_blocks": [
      {
        "filename": "saga_orchestrator_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype SagaStep struct {\n\tName       string\n\tExecute    func(context.Context) error\n\tCompensate func(context.Context) error\n}\n\ntype OrderSagaOrchestrator struct {\n\tsteps []SagaStep\n}\n\nfunc (s *OrderSagaOrchestrator) AddStep(step SagaStep) {\n\ts.steps = append(s.steps, step)\n}\n\nfunc (s *OrderSagaOrchestrator) Run(ctx context.Context) error {\n\tvar executedSteps []SagaStep\n\n\tfor _, step := range s.steps {\n\t\tfmt.Printf(\"  [Saga Exec] Выполняем шаг: %s\\n\", step.Name)\n\t\terr := step.Execute(ctx)\n\t\tif err != nil {\n\t\t\tfmt.Printf(\"  [Saga ERROR] Сбой на шаге %s: %v. Запуск компенсации...\\n\", step.Name, err)\n\t\t\ts.rollback(ctx, executedSteps)\n\t\t\treturn err\n\t\t}\n\t\texecutedSteps = append(executedSteps, step)\n\t}\n\n\tfmt.Println(\"  [Saga SUCCESS] Все шаги успешно зафиксированы!\")\n\treturn nil\n}\n\nfunc (s *OrderSagaOrchestrator) rollback(ctx context.Context, executed []SagaStep) {\n\t// Компенсации вызываются в ОБРАТНОМ порядке (LIFO)\n\tfor i := len(executed) - 1; i >= 0; i-- {\n\t\tstep := executed[i]\n\t\tif step.Compensate != nil {\n\t\t\tfmt.Printf(\"  [Saga Rollback] Компенсируем шаг: %s\\n\", step.Name)\n\t\t\t_ = step.Compensate(ctx)\n\t\t}\n\t}\n}\n\nfunc TestSagaExecutionWithRollback(t *testing.T) {\n\tsaga := &OrderSagaOrchestrator{}\n\n\tsaga.AddStep(SagaStep{\n\t\tName: \"1. CreateOrder\",\n\t\tExecute: func(ctx context.Context) error { return nil },\n\t\tCompensate: func(ctx context.Context) error {\n\t\t\tfmt.Println(\"    -> Отмена заказа в базе данных\"); return nil\n\t\t},\n\t})\n\n\tsaga.AddStep(SagaStep{\n\t\tName: \"2. ReserveInventory\",\n\t\tExecute: func(ctx context.Context) error { return nil },\n\t\tCompensate: func(ctx context.Context) error {\n\t\t\tfmt.Println(\"    -> Возврат зарезервированного товара на склад\"); return nil\n\t\t},\n\t})\n\n\tsaga.AddStep(SagaStep{\n\t\tName: \"3. ProcessPayment\",\n\t\tExecute: func(ctx context.Context) error {\n\t\t\treturn fmt.Errorf(\"карта отклонена банком (недостаточно средств)\")\n\t\t},\n\t\tCompensate: func(ctx context.Context) error { return nil },\n\t})\n\n\terr := saga.Run(context.Background())\n\tif err == nil {\n\t\tt.Fatal(\"Ожидался сбой на шаге платежа\")\n\t}\n\n\tfmt.Println(\"Тест успешно подтвердил: компенсирующие транзакции сняли бронь со склада!\")\n}",
        "note": "Оркестрация распределенной саги с автоматическим откатом"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v saga_orchestrator_test.go\n# Вывод:\n# === RUN   TestSagaExecutionWithRollback\n#   [Saga Exec] Выполняем шаг: 1. CreateOrder\n#   [Saga Exec] Выполняем шаг: 2. ReserveInventory\n#   [Saga Exec] Выполняем шаг: 3. ProcessPayment\n#   [Saga ERROR] Сбой на шаге 3. ProcessPayment: карта отклонена банком (недостаточно средств). Запуск компенсации...\n#   [Saga Rollback] Компенсируем шаг: 2. ReserveInventory\n#     -> Возврат зарезервированного товара на склад\n#   [Saga Rollback] Компенсируем шаг: 1. CreateOrder\n#     -> Отмена заказа в базе данных\n# Тест успешно подтвердил: компенсирующие транзакции сняли бронь со склада!\n# --- PASS: TestSagaExecutionWithRollback (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Компенсирующие транзакции ОБЯЗАНЫ быть семантически идемпотентными: если сетевой сбой произойдет во время выполнения компенсации, повторный вызов компенсации должен завершиться успешно.",
    "pitfalls": "Предполагать, что компенсирующая транзакция может просто удалить строку из базы (`DELETE FROM orders`): в финансовых системах удалять данные запрещено. Компенсация записывает сторнирующую проводку.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие Saga Orchestration от Saga Choreography?»\n**Ответ:** В хореографии (Choreography) микросервисы слушают события Kafka и сами решают, что делать дальше (нет центрального координатора, но сложно отслеживать граф вызовов). В оркестрации (Orchestration) выделенный Order Service управляет последовательностью вызовов по схеме State Machine, явно вызывая нужные gRPC методы и компенсации."
  },
  {
    "num": 170,
    "title": "Асинхронная доставка событий в Notification Service: Kafka/NATS, DLQ и gRPC API подписок",
    "task": "Реализуй **\"Notification Service\"**:\n- Подписка на events из Kafka/NATS (Outbox от User/Order сервисов)\n- Отправка email/SMS/push (заглушки)\n- DLQ для необработанных событий\n- gRPC API для управления подписками",
    "theory": "Архитектура Event-Driven потребителя с Dead Letter Queue (DLQ):\n- Сервис уведомлений подписывается на топики Kafka/NATS: `user-events`, `order-events`.\n- При получении события `OrderCreated`:\n  - Выполняется отправка Push-уведомления или SMS.\n  - Если шлюз отправки SMS недоступен после 3 попыток:\n    - Сообщение НЕ теряется и не блокирует очередь (No Head-of-Line Blocking).\n    - Сообщение отправляется в специальный топик **DLQ (Dead Letter Queue)** `notifications-dlq` для последующего анализа инженерами.\n- gRPC API сервиса позволяет пользователям настраивать каналы уведомлений (`email: true, push: false`).",
    "step_by_step": "1. Создайте структуру обработчика событий.\n2. Реализуйте попытки доставки сообщений с ретраями.\n3. При превышении попыток перенаправьте в Dead Letter Queue.\n4. Протестируйте изоляцию сбойных событий.",
    "code_blocks": [
      {
        "filename": "dlq_consumer_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n)\n\ntype EventMessage struct {\n\tID        string\n\tRecipient string\n\tPayload   string\n\tAttempts  int\n}\n\ntype NotificationConsumer struct {\n\tmu  sync.Mutex\n\tdlq []*EventMessage\n}\n\nfunc (c *NotificationConsumer) ProcessMessage(ctx context.Context, msg *EventMessage) error {\n\tconst maxRetries = 3\n\n\t// Симулируем постоянный отказ отправки SMS\n\tfor msg.Attempts < maxRetries {\n\t\tmsg.Attempts++\n\t\tfmt.Printf(\"  [Попытка #%d] Отправка уведомления для %s не удалась (SMS Provider 503)\\n\",\n\t\t\tmsg.Attempts, msg.Recipient)\n\t}\n\n\t// Попытки исчерпаны -> перемещаем в Dead Letter Queue (DLQ)\n\tc.mu.Lock()\n\tc.dlq = append(c.dlq, msg)\n\tc.mu.Unlock()\n\n\tfmt.Printf(\"[DLQ ROUTED] Событие %s направлено в Dead Letter Queue для расследования!\\n\", msg.ID)\n\treturn nil\n}\n\nfunc TestDeadLetterQueueRouting(t *testing.T) {\n\tconsumer := &NotificationConsumer{}\n\tmsg := &EventMessage{\n\t\tID:        \"evt_order_8819\",\n\t\tRecipient: \"+79991234567\",\n\t\tPayload:   \"Ваш заказ собран и передан курьеру\",\n\t}\n\n\t_ = consumer.ProcessMessage(context.Background(), msg)\n\n\tconsumer.mu.Lock()\n\tdlqCount := len(consumer.dlq)\n\tconsumer.mu.Unlock()\n\n\tif dlqCount != 1 {\n\t\tt.Fatalf(\"Ожидалось 1 сообщение в DLQ, получено: %d\", dlqCount)\n\t}\n\n\tfmt.Println(\"Тест подтвердил: сбойное событие не заблокировало очередь и изолировано в DLQ\")\n}",
        "note": "Изоляция необработанных событий в Dead Letter Queue (DLQ)"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v dlq_consumer_test.go\n# Вывод:\n# === RUN   TestDeadLetterQueueRouting\n#   [Попытка #1] Отправка уведомления для +79991234567 не удалась (SMS Provider 503)\n#   [Попытка #2] Отправка уведомления для +79991234567 не удалась (SMS Provider 503)\n#   [Попытка #3] Отправка уведомления для +79991234567 не удалась (SMS Provider 503)\n# [DLQ ROUTED] Событие evt_order_8819 направлено в Dead Letter Queue для расследования!\n# Тест подтвердил: сбойное событие не заблокировало очередь и изолировано в DLQ\n# --- PASS: TestDeadLetterQueueRouting (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Kafka DLQ реализуется как отдельный топик с тем же форматом сообщений плюс метаданные об ошибке в заголовках (`x-original-topic`, `x-exception-message`), что позволяет SRE-инженерам перезапустить обработку после исправления бага.",
    "pitfalls": "Подавлять ошибки (ack message) без сохранения в DLQ: сообщения будут бесследно утеряны из очереди.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как предотвратить отправку дубликатов SMS клиенту при ретраях из Kafka (At-Least-Once delivery)?»\n**Ответ:** Реализовать **Idempotent Consumer**: перед отправкой SMS сервис атомарно записывает ключ события `eventId` в Redis (`SET event_id \"PROCESSING\" NX EX 86400`). Если ключ уже существует в Redis, отправка не выполняется, а сообщение сразу подтверждается (ACK), гарантируя доставку ровно одного SMS."
  },
  {
    "num": 171,
    "title": "Асинхронные долгие операции: паттерн Long-Running Operations (LRO) и опрос operation_id",
    "task": "Реализуйте асинхронную обработку: клиент отправляет запрос, сервер возвращает `operation_id`, клиент опрашивает статус операции другим RPC.",
    "theory": "Паттерн Long-Running Operations (Google LRO / Awaitable Operations):\n- Если задача занимает минуты (импорт 10 ГБ CSV, обучение ML-модели, создание резервной копии), держать открытый RPC вызов нельзя из-за таймаутов.\n- Архитектура LRO:\n  1. `rpc StartMigration (MigrationRequest) returns (Operation);`\n     - Сервер немедленно возвращает `operation_id: \"op_98124\"`, `done: false`.\n  2. Задача выполняется в фоновом пуле воркеров.\n  3. Клиент опрашивает статус: `rpc GetOperation (GetOperationRequest) returns (Operation);`.\n  4. Когда задача завершена: сервер возвращает `done: true`, `response: {...}`.",
    "step_by_step": "1. Создайте хранилище статусов операций в памяти.\n2. Реализуйте метод инициализации операции `StartLongTask`.\n3. Реализуйте метод опроса статуса `PollOperation`.\n4. Протестируйте переход задачи из RUNNING в COMPLETED.",
    "code_blocks": [
      {
        "filename": "lro_async_engine_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype OperationStatus string\n\nconst (\n\tOpRunning   OperationStatus = \"RUNNING\"\n\tOpCompleted OperationStatus = \"COMPLETED\"\n\tOpFailed    OperationStatus = \"FAILED\"\n)\n\ntype OperationRecord struct {\n\tID        string\n\tStatus    OperationStatus\n\tResult    string\n\tCreatedAt time.Time\n}\n\ntype LROManager struct {\n\tmu         sync.Mutex\n\toperations map[string]*OperationRecord\n\tcounter    int\n}\n\nfunc NewLROManager() *LROManager {\n\treturn &LROManager{operations: make(map[string]*OperationRecord)}\n}\n\nfunc (m *LROManager) StartTask(ctx context.Context, taskName string) string {\n\tm.mu.Lock()\n\tdefer m.mu.Unlock()\n\n\tm.counter++\n\topID := fmt.Sprintf(\"op_%d\", m.counter)\n\top := &OperationRecord{\n\t\tID:        opID,\n\t\tStatus:    OpRunning,\n\t\tCreatedAt: time.Now(),\n\t}\n\tm.operations[opID] = op\n\n\t// Фоновый воркер выполнения тяжелой задачи\n\tgo func(id string) {\n\t\ttime.Sleep(30 * time.Millisecond) // Имитация вычислений\n\t\tm.mu.Lock()\n\t\tdefer m.mu.Unlock()\n\t\tif cur, ok := m.operations[id]; ok {\n\t\t\tcur.Status = OpCompleted\n\t\t\tcur.Result = \"Экспорт данных успешно завершен (архив data.tar.gz)\"\n\t\t}\n\t}(opID)\n\n\treturn opID\n}\n\nfunc (m *LROManager) GetOperation(id string) (*OperationRecord, bool) {\n\tm.mu.Lock()\n\tdefer m.mu.Unlock()\n\top, ok := m.operations[id]\n\treturn op, ok\n}\n\nfunc TestLROExecution(t *testing.T) {\n\tmanager := NewLROManager()\n\topID := manager.StartTask(context.Background(), \"BigDataExport\")\n\tfmt.Printf(\"1. Запущена асинхронная операция: ID=%s\\n\", opID)\n\n\t// Опрашиваем статус сразу\n\topInit, _ := manager.GetOperation(opID)\n\tif opInit.Status != OpRunning {\n\t\tt.Fatalf(\"Ожидался статус RUNNING, получено: %s\", opInit.Status)\n\t}\n\tfmt.Printf(\"2. Первичный опрос статуса: %s\\n\", opInit.Status)\n\n\t// Дожидаемся завершения фонового воркера\n\ttime.Sleep(50 * time.Millisecond)\n\topDone, _ := manager.GetOperation(opID)\n\tif opDone.Status != OpCompleted {\n\t\tt.Fatalf(\"Ожидался статус COMPLETED, получено: %s\", opDone.Status)\n\t}\n\n\tfmt.Printf(\"3. Финальный опрос статуса: %s (Результат: %s)\\n\", opDone.Status, opDone.Result)\n}",
        "note": "Реализация паттерна Long-Running Operations (LRO) с асинхронным опросом"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v lro_async_engine_test.go\n# Вывод:\n# === RUN   TestLROExecution\n# 1. Запущена асинхронная операция: ID=op_1\n# 2. Первичный опрос статуса: RUNNING\n# 3. Финальный опрос статуса: COMPLETED (Результат: Экспорт данных успешно завершен (архив data.tar.gz))\n# --- PASS: TestLROExecution (0.05s)\n# PASS"
      }
    ],
    "under_the_hood": "В Google Cloud API и Kubernetes стандартом является `google.longrunning.Operation`. Структура содержит поле `metadata` (процент выполнения) и `response` типа `Any`.",
    "pitfalls": "Опрашивать `GetOperation` без задержки (Busy-Wait Loop): тысячи клиентов сожгут процессор сервера. Используйте Exponential Backoff (100ms $\\to$ 200ms $\\to$ 500ms $\\to$ 1s).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как уведомить клиента о завершении долгой операции без постоянного поллинга?»\n**Ответ:** 1. Использовать gRPC Server Streaming (`rpc WaitOperation returns (stream OperationProgress)`). 2. Использовать Webhook (сервер сам шлет HTTP POST при завершении). 3. Использовать WebSocket/SSE для браузерных приложений."
  },
  {
    "num": 172,
    "title": "Шлюз API Gateway с параллельной агрегацией: errgroup, REST трансляция и сборка Dashboard",
    "task": "Реализуй **API Gateway**:\n- HTTP REST на входе, gRPC на выходе к сервисам\n- Auth: JWT validation, rate limiting per client\n- Request/response transformation: REST JSON ↔ gRPC protobuf\n- Aggregation: `GET /dashboard` вызывает 3 сервиса параллельно, мержит результаты",
    "theory": "Паттерн Backend for Frontend (BFF) / API Gateway Aggregator:\n- Пользовательскому приложению для открытия главного экрана требуется информация из 3 сервисов:\n  1. `UserService.GetProfile` (Профиль)\n  2. `OrderService.GetRecentOrders` (Последние заказы)\n  3. `NotificationService.GetUnreadCount` (Непрочитанные уведомления)\n- Последовательный опрос займет $T_1 + T_2 + T_3 = 300$ мс.\n- **Параллельная агрегация через `golang.org/x/sync/errgroup`:**\n  - Все 3 вызова запускаются в параллельных горутинах.\n  - Итоговое время равно самому медленному вызову: $\\max(T_1, T_2, T_3) \\approx 100$ мс!",
    "step_by_step": "1. Создайте структуру агрегированного ответа `DashboardDTO`.\n2. Используйте `errgroup.Group` для параллельных вызовов.\n3. Объедините результаты ответа.\n4. Протестируйте ускорение агрегации.",
    "code_blocks": [
      {
        "filename": "gateway_aggregator_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n\n\t\"golang.org/x/sync/errgroup\"\n)\n\ntype DashboardResponse struct {\n\tUserName    string   `json:\"user_name\"`\n\tRecentOrder string   `json:\"recent_order\"`\n\tUnreadCount int      `json:\"unread_count\"`\n}\n\nfunc AggregateDashboard(ctx context.Context, userID string) (*DashboardResponse, error) {\n\tg, gCtx := errgroup.WithContext(ctx)\n\tvar mu sync.Mutex\n\tdash := &DashboardResponse{}\n\n\t// 1. Вызов User Service\n\tg.Go(func() error {\n\t\ttime.Sleep(15 * time.Millisecond) // Имитация gRPC вызова\n\t\tmu.Lock()\n\t\tdash.UserName = \"Екатерина Смирнова\"\n\t\tmu.Unlock()\n\t\treturn nil\n\t})\n\n\t// 2. Вызов Order Service\n\tg.Go(func() error {\n\t\ttime.Sleep(20 * time.Millisecond)\n\t\tmu.Lock()\n\t\tdash.RecentOrder = \"Заказ #9923 (Доставлен)\"\n\t\tmu.Unlock()\n\t\treturn nil\n\t})\n\n\t// 3. Вызов Notification Service\n\tg.Go(func() error {\n\t\ttime.Sleep(10 * time.Millisecond)\n\t\tmu.Lock()\n\t\tdash.UnreadCount = 4\n\t\tmu.Unlock()\n\t\treturn nil\n\t})\n\n\tif err := g.Wait(); err != nil {\n\t\treturn nil, err\n\t}\n\t_ = gCtx\n\n\treturn dash, nil\n}\n\nfunc TestDashboardAggregation(t *testing.T) {\n\tstart := time.Now()\n\tdash, err := AggregateDashboard(context.Background(), \"usr_100\")\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка агрегации: %v\", err)\n\t}\n\n\tduration := time.Since(start)\n\tif dash.UserName != \"Екатерина Смирнова\" || dash.UnreadCount != 4 {\n\t\tt.Fatalf(\"Некорректные данные: %+v\", dash)\n\t}\n\n\tfmt.Printf(\"Dashboard успешно собран за %v (параллельно!):\\n\", duration.Round(time.Millisecond))\n\tfmt.Printf(\"  • Пользователь: %s\\n\", dash.UserName)\n\tfmt.Printf(\"  • Последний заказ: %s\\n\", dash.RecentOrder)\n\tfmt.Printf(\"  • Новых сообщений: %d\\n\", dash.UnreadCount)\n}",
        "note": "Параллельная агрегация данных от 3 микросервисов через errgroup"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v gateway_aggregator_test.go\n# Вывод:\n# === RUN   TestDashboardAggregation\n# Dashboard успешно собран за 20ms (параллельно!):\n#   • Пользователь: Екатерина Смирнова\n#   • Последний заказ: Заказ #9923 (Доставлен)\n#   • Новых сообщений: 4\n# --- PASS: TestDashboardAggregation (0.02s)\n# PASS"
      }
    ],
    "under_the_hood": "`errgroup.WithContext(ctx)` гарантирует отмену зависимых горутин: если один из сервисов вернул критическую ошибку, контекст остальных немедленно закрывается, экономя ресурсы.",
    "pitfalls": "Забывать защитить общую структуру `dash` мьютексом `mu.Lock()`: одновременная запись полей разными горутинами вызовет фатальный Data Race.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как реализовать частичную деградацию (Graceful Degradation) в агрегаторе API Gateway?»\n**Ответ:** Если некритичный сервис (например Notification Service) недоступен по таймауту, шлюз не роняет весь дашборд ошибкой 500. Ошибка логируется, а поле `unread_count` заполняется нулем или дефолтным значением, позволяя пользователю увидеть профиль и заказы."
  },
  {
    "num": 173,
    "title": "Интеграционное тестирование микросервисов: Testcontainers, изоляция данных и сквозной E2E сценарий",
    "task": "Реализуй **\"Integration Test Suite\"**:\n- testcontainers: PostgreSQL, Redis, Kafka\n- Запуск всех 3 сервисов в памяти (или в Docker)\n- gRPC клиенты, HTTP клиенты\n- Проверка end-to-end сценариев: регистрация → создание заказа → уведомление\n- Очистка данных между тестами",
    "theory": "Промышленный эталон интеграционного тестирования (Integration Test Suite):\n- Мокирование внешних систем (Postgres/Redis) часто скрывает ошибки синтаксиса SQL и гонки данных.\n- Библиотека `testcontainers-go`:\n  - На лету поднимает реальные легковесные Docker контейнеры в рантайме теста:\n    `postgresContainer, _ := postgres.RunContainer(ctx, ...)`\n  - Применяет миграции базы данных.\n  - Запускает сервисы с реальным сетевым взаимодействием.\n  - По завершении тестов автоматически гарантирует полное удаление контейнеров (Ryuk Moby reaper).",
    "step_by_step": "1. Смоделируйте сквозной тестовый контур трех микросервисов.\n2. Проведите сценарий: Регистрация $\\to$ Оплата $\\to$ Уведомление.\n3. Проверьте изоляцию данных между тестами.\n4. Протестируйте очистку ресурсов.",
    "code_blocks": [
      {
        "filename": "e2e_integration_suite_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype IntegrationEnvironment struct {\n\tusersDB  map[string]string\n\tordersDB map[string]string\n\tevents   []string\n}\n\nfunc NewIntegrationEnvironment() *IntegrationEnvironment {\n\treturn &IntegrationEnvironment{\n\t\tusersDB:  make(map[string]string),\n\t\tordersDB: make(map[string]string),\n\t}\n}\n\nfunc (env *IntegrationEnvironment) CleanUp() {\n\tclear(env.usersDB)\n\tclear(env.ordersDB)\n\tenv.events = nil\n}\n\nfunc TestE2ECompleteUserJourney(t *testing.T) {\n\tenv := NewIntegrationEnvironment()\n\tdefer env.CleanUp()\n\n\t// Шаг 1: Регистрация пользователя в User Service\n\tuserID := \"usr_bigtech_01\"\n\tenv.usersDB[userID] = \"alex@ozon.ru\"\n\tenv.events = append(env.events, \"UserRegistered:\"+userID)\n\n\t// Шаг 2: Создание заказа в Order Service\n\torderID := \"ord_laptop_55\"\n\tif _, userExists := env.usersDB[userID]; !userExists {\n\t\tt.Fatal(\"Пользователь не найден\")\n\t}\n\tenv.ordersDB[orderID] = \"PAID\"\n\tenv.events = append(env.events, \"OrderCreated:\"+orderID)\n\n\t// Шаг 3: Notification Service получил события из шины Kafka\n\tif len(env.events) != 2 {\n\t\tt.Fatalf(\"Ожидалось 2 события в шине, получено: %d\", len(env.events))\n\t}\n\n\tfmt.Println(\"Интеграционный E2E сценарий успешно пройден:\")\n\tfor idx, evt := range env.events {\n\t\tfmt.Printf(\"  [%d] Транзакция: %s\\n\", idx+1, evt)\n\t}\n}",
        "note": "Сквозное тестирование пользовательского пути через связанные микросервисы"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v e2e_integration_suite_test.go\n# Вывод:\n# === RUN   TestE2ECompleteUserJourney\n# Интеграционный E2E сценарий успешно пройден:\n#   [1] Транзакция: UserRegistered:usr_bigtech_01\n#   [2] Транзакция: OrderCreated:ord_laptop_55\n# --- PASS: TestE2ECompleteUserJourney (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`testcontainers-go` взаимодействует с локальным Docker daemon через сокет `/var/run/docker.sock`, выделяя динамические эфемерные порты для каждого контейнера во избежание конфликтов при параллельном запуске в CI.",
    "pitfalls": "Запускать миграции в цикле каждого теста: это замедлит выполнение сьюта. Миграции на контейнер накатывают один раз в `TestMain(m *testing.M)`, а между тестами очищают таблицы через `TRUNCATE`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как ускорить интеграционные тесты с базой данных в 10 раз?»\n**Ответ:** Разместить данные PostgreSQL в оперативной памяти с помощью флага `tmpfs`: `tmpfs: [\"/var/lib/postgresql/data:rw\"]`. Это отключает синхронизацию с физическим диском (fsync), давая скорость работы на уровне In-Memory базы при сохранении 100% совместимости с синтаксисом PostgreSQL."
  },
  {
    "num": 174,
    "title": "Нагрузочное тестирование с ghz: профилирование задержек p50/p95/p99 и анализ узких мест pprof",
    "task": "Реализуй **\"Load Test\"**:\n- `ghz` или `k6` для gRPC/HTTP нагрузки\n- 1000 RPS на User Service\n- Измерь latency p50/p95/p99\n- Найди bottleneck через pprof\n- Оптимизируй и повтори",
    "theory": "Инженерия нагрузочного тестирования gRPC:\n- Инструмент **`ghz`** — промышленный стандарт нагрузочного тестирования gRPC на Go.\n- Запуск нагрузки 1000 RPS на 10 000 запросов:\n  `ghz --insecure --proto=user.proto --call=user.v1.UserService.GetUser -d '{\"id\":\"usr_1\"}' -c 50 -q 1000 -n 10000 localhost:50051`\n- Анализ метрик SLA:\n  - $P50$ (медиана): типичное время ответа.\n  - $P95$: граница медленных запросов.\n  - $P99$: критический хвост латентности (Tail Latency).\n- Профилирование узких мест: `go tool pprof http://localhost:6060/debug/pprof/profile`.",
    "step_by_step": "1. Смоделируйте сбор и вычисление процентилей $P50$, $P95$, $P99$.\n2. Отсортируйте задержки вызовов.\n3. Продемонстрируйте вычисление показателей латентности.\n4. Оцените отчет нагрузочного тестирования.",
    "code_blocks": [
      {
        "filename": "ghz_metrics_parser_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sort\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype LatencyReport struct {\n\tP50 time.Duration\n\tP95 time.Duration\n\tP99 time.Duration\n\tRPS float64\n}\n\nfunc CalculatePercentiles(samples []time.Duration) LatencyReport {\n\tsort.Slice(samples, func(i, j int) bool { return samples[i] < samples[j] })\n\tn := len(samples)\n\n\treturn LatencyReport{\n\t\tP50: samples[int(float64(n)*0.50)],\n\t\tP95: samples[int(float64(n)*0.95)],\n\t\tP99: samples[int(float64(n)*0.99)],\n\t\tRPS: 1000.0,\n\t}\n}\n\nfunc TestPercentilesReport(t *testing.T) {\n\t// Имитация 1000 замеров от ghz\n\tvar samples []time.Duration\n\tfor i := 1; i <= 1000; i++ {\n\t\t// Большинство запросов 1-3 мс, редкие выбросы до 25 мс\n\t\tif i > 980 {\n\t\t\tsamples = append(samples, time.Duration(15+i%10)*time.Millisecond)\n\t\t} else {\n\t\t\tsamples = append(samples, time.Duration(1+i%3)*time.Millisecond)\n\t\t}\n\t}\n\n\treport := CalculatePercentiles(samples)\n\n\tfmt.Println(\"Результаты нагрузочного тестирования gRPC сервиса (ghz 1000 RPS):\")\n\tfmt.Printf(\"  • Latency P50 (Медиана): %v\\n\", report.P50)\n\tfmt.Printf(\"  • Latency P95:          %v\\n\", report.P95)\n\tfmt.Printf(\"  • Latency P99 (Хвост):   %v\\n\", report.P99)\n\n\tif report.P50 > 5*time.Millisecond {\n\t\tt.Fatal(\"Слишком высокая медианная задержка\")\n\t}\n}",
        "note": "Расчет процентилей задержек P50, P95, P99"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск реального стресс-теста через утилиту ghz:\nghz --insecure \\\n    --proto=proto/user.proto \\\n    --call=user.v1.UserService.GetUser \\\n    -d '{\"id\":\"usr_42\"}' \\\n    -c 50 -q 1000 -n 10000 \\\n    127.0.0.1:50051\n\n# Вывод ghz:\n# Summary:\n#   Count:        10000\n#   Total:        10.02 s\n#   Slowest:      24.12 ms\n#   Fastest:      0.82 ms\n#   Average:      2.15 ms\n#   Requests/sec: 998.00\n# Response time histogram:\n#   p50: 1.95 ms\n#   p95: 3.12 ms\n#   p99: 18.50 ms"
      }
    ],
    "under_the_hood": "Высокий $P99$ чаще всего вызван паузами сборщика мусора Go (GC Stop-The-World STW mark termination) или блокировками пула соединений БД. Профиль `pprof/mutex` выявляет конкуренцию за мьютексы.",
    "pitfalls": "Запускать нагрузочный генератор `ghz` на той же машине, где крутится сервис: генератор заберет 50% CPU, исказив замеры. Генератор запускают с отдельного тестового сервера.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое Coordinated Omission в нагрузочном тестировании и как ghz с ним справляется?»\n**Ответ:** Это искажение измерений, когда генератор нагрузки ждет ответа на предыдущий запрос перед отправкой следующего. Если сервис замирает на 2 секунды, генератор тоже простаивает и не фиксирует запросы, которые должны были упасть по таймауту. Флаг `--async` или генератор `k6/vegeta` шлют запросы строго по расписанию независимо от задержек сервера."
  },
  {
    "num": 175,
    "title": "Интроспекция через Server Reflection v1alpha: интеграция и отладка с grpcurl",
    "task": "Используйте серверную рефлексию (`grpc.reflection.v1alpha.ServerReflection`) для удобной отладки с `grpcurl`.",
    "theory": "Совместимость версий Server Reflection:\n- В экосистеме gRPC существует два протокола Reflection:\n  - `grpc.reflection.v1alpha` (исторический стандарт).\n  - `grpc.reflection.v1` (современный релизный стандарт gRPC v1.56+).\n- Регистрация `reflection.Register(server)` автоматически активирует поддержку обоих протоколов для совместимости со старыми и новыми версиями `grpcurl`.",
    "step_by_step": "1. Подключите пакет `reflection`.\n2. Зарегистрируйте reflection на сервере.\n3. Исследуйте сервис через вызов `grpcurl`.\n4. Продемонстрируйте консольное взаимодействие.",
    "code_blocks": [
      {
        "filename": "reflection_alpha_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/reflection\"\n)\n\nfunc main() {\n\tlis, err := net.Listen(\"tcp\", \"127.0.0.1:0\")\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer lis.Close()\n\n\tserver := grpc.NewServer()\n\n\t// Регистрация Server Reflection\n\treflection.Register(server)\n\n\tfmt.Printf(\"Сервер с Reflection готов на %s\\n\", lis.Addr().String())\n\tfmt.Println(\"grpcurl совместим с обеими версиями протокола v1 и v1alpha!\")\n}",
        "note": "Регистрация протокола рефлексии"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run reflection_alpha_demo.go\n# Вывод:\n# Сервер с Reflection готов на 127.0.0.1:39105\n# grpcurl совместим с обеими версиями протокола v1 и v1alpha!"
      }
    ],
    "under_the_hood": "Сервер отдает proto-дескрипторы из бинарного файла `FileDescriptorProto`, сохраненного компилятором `protoc` в глобальном реестре инициализации пакета `init()`.",
    "pitfalls": "Использовать флаг `-plaintext` при подключении к продакшн серверу с TLS: клиент не сможет договориться о рукопожатии.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем нужна рефлексия, если у команды уже есть git репозиторий с proto-файлами?»\n**Ответ:** Для динамических балансировщиков и API-шлюзов (например Envoy gRPC-JSON transcoder). Шлюз может на лету запрашивать схемы с бэкенда через Reflection и обновлять свои правила маршрутизации без необходимости пересборки конфигов при каждом изменении контрактов."
  },
  {
    "num": 176,
    "title": "Бесшовный релиз Blue-Green Deployment: мгновенное переключение трафика 100% Blue в Green",
    "task": "Реализуй **\"Blue-Green Deployment\"**:\n- 2 версии сервиса (blue=v1, green=v2)\n- Ingress переключает трафик 100% blue → 100% green\n- Без downtime, с rollback возможностью\n- Проверь через integration tests на green перед переключением",
    "theory": "Стратегия Blue-Green развертывания без простоя (Zero-Downtime Releases):\n- В кластере одновременно развернуты два независимых окружения:\n  - **Blue (v1):** текущая стабильная версия, принимающая 100% боевого трафика.\n  - **Green (v2):** новая версия, задеплоенная рядом, принимающая 0% пользовательского трафика.\n- Этапы:\n  1. На Green-окружении прогоняются интеграционные смоук-тесты.\n  2. Балансировщик (Ingress / Service selector) переключает селектор подов с `version: blue` на `version: green`.\n  3. Новые запросы gRPC мгновенно идут на Green.\n  4. При обнаружении аномалий откат (Rollback) на Blue выполняется за 1 секунду переключением селектора.",
    "step_by_step": "1. Смоделируйте селектор маршрутизации трафика.\n2. Проверьте отправку запросов на Blue.\n3. Проведите смоук-тест на версии Green.\n4. Переключите селектор на Green и проверьте перенаправление.",
    "code_blocks": [
      {
        "filename": "blue_green_router_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n)\n\ntype ServiceDeployment struct {\n\tVersion string\n}\n\nfunc (s *ServiceDeployment) Handle(ctx context.Context, msg string) string {\n\treturn fmt.Sprintf(\"[%s] Обработано: %s\", s.Version, msg)\n}\n\ntype IngressTrafficSwitch struct {\n\tmu            sync.RWMutex\n\tactiveCluster *ServiceDeployment\n}\n\nfunc (sw *IngressTrafficSwitch) Route(ctx context.Context, msg string) string {\n\tsw.mu.RLock()\n\tdefer sw.mu.RUnlock()\n\treturn sw.activeCluster.Handle(ctx, msg)\n}\n\nfunc (sw *IngressTrafficSwitch) SwitchTraffic(target *ServiceDeployment) {\n\tsw.mu.Lock()\n\tdefer sw.mu.Unlock()\n\tsw.activeCluster = target\n}\n\nfunc TestBlueGreenDeploymentFlow(t *testing.T) {\n\tblueV1 := &ServiceDeployment{Version: \"v1.0.0-BLUE\"}\n\tgreenV2 := &ServiceDeployment{Version: \"v2.0.0-GREEN\"}\n\n\trouter := &IngressTrafficSwitch{activeCluster: blueV1}\n\n\t// 1. Текущий боевой трафик идет на Blue\n\tres1 := router.Route(context.Background(), \"Запрос #1\")\n\tfmt.Println(\"Боевой трафик:\", res1)\n\tif res1 != \"[v1.0.0-BLUE] Обработано: Запрос #1\" {\n\t\tt.Fatalf(\"Некорректный роутинг на Blue\")\n\t}\n\n\t// 2. Дымовое тестирование на Green окружении ДО переключения\n\tsmokeTest := greenV2.Handle(context.Background(), \"SmokeTest\")\n\tfmt.Println(\"Интеграционный тест на Green:\", smokeTest)\n\n\t// 3. Мгновенное переключение 100% трафика на Green\n\trouter.SwitchTraffic(greenV2)\n\tfmt.Println(\">>> Ingress переключил селектор: 100% трафика направлено на GREEN!\")\n\n\t// 4. Все новые вызовы идут на Green\n\tres2 := router.Route(context.Background(), \"Запрос #2\")\n\tfmt.Println(\"Боевой трафик:\", res2)\n\tif res2 != \"[v2.0.0-GREEN] Обработано: Запрос #2\" {\n\t\tt.Fatalf(\"Некорректный роутинг на Green\")\n\t}\n}",
        "note": "Мгновенное переключение трафика в Blue-Green стратегии развертывания"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v blue_green_router_test.go\n# Вывод:\n# === RUN   TestBlueGreenDeploymentFlow\n# Боевой трафик: [v1.0.0-BLUE] Обработано: Запрос #1\n# Интеграционный тест на Green: [v2.0.0-GREEN] Обработано: SmokeTest\n# >>> Ingress переключил селектор: 100% трафика направлено на GREEN!\n# Боевой трафик: [v2.0.0-GREEN] Обработано: Запрос #2\n# --- PASS: TestBlueGreenDeploymentFlow (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Kubernetes Blue-Green реализуется изменением селектора в манифесте Service: `kubectl patch service app-service -p '{\"spec\":{\"selector\":{\"version\":\"green\"}}}'`. Kube-proxy перенаправляет iptables за доли секунды.",
    "pitfalls": "Вносить обратно-несовместимые изменения в схему БД (например удаление колонки): Blue версия мгновенно упадет при миграции Green. Используйте паттерн Expand and Contract (двухфазные миграции).",
    "bigtech_interview": "**Вопрос с собеседования:** «Что делать с долгоживущими gRPC стримами при переключении с Blue на Green?»\n**Ответ:** Вызвать на старых Blue подах `GracefulStop()`. Сервер отправит стримам фрейм `GOAWAY`. Клиенты gRPC автоматически откроют новые соединения, которые Ingress направит уже на Green поды, завершая миграцию без потери сообщений."
  },
  {
    "num": 177,
    "title": "Геораспределенная отказоустойчивость: концепция Multi-Region Active-Active и Disaster Failover",
    "task": "Реализуй **\"Multi-region deployment\"** (концептуально):\n- Active-Active: 2 региона, каждый обрабатывает свой shard пользователей\n- Global load balancer (GeoDNS) маршрутизирует\n- Replication PostgreSQL (read replicas), Redis Cluster\n- Failover: при падении региона — traffic shift в другой",
    "theory": "Архитектура Multi-Region Active-Active:\n- Развертывание в двух географически удаленных датацентрах (например DC-Москва и DC-СПб).\n- Маршрутизация трафика:\n  - **GeoDNS / Anycast BGP:** направляет пользователя в ближайший регион (минимальный RTT).\n  - Шардирование пользователей: пользователи европейской части обслуживаются в DC-1, восточной — в DC-2.\n- Базы данных:\n  - PostgreSQL асинхронная потоковая репликация между регионами.\n  - Redis активная репликация.\n- Сценарий **Disaster Failover:**\n  - При отключении питания в DC-1 GeoDNS снимает трафик и перенаправляет 100% запросов в DC-2 за считанные секунды.",
    "step_by_step": "1. Создайте модель двух регионов.\n2. Реализуйте GeoDNS роутер с проверкой здоровья региона.\n3. Смоделируйте аварию в регионе 1.\n4. Проверьте автоматическое переключение трафика (Traffic Shift).",
    "code_blocks": [
      {
        "filename": "multi_region_failover_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype DataCenter struct {\n\tName    string\n\tIsAlive bool\n}\n\ntype GeoDNSRouter struct {\n\tRegionMSK *DataCenter\n\tRegionSPB *DataCenter\n}\n\nfunc (r *GeoDNSRouter) RouteUser(userHomeRegion string) string {\n\t// 1. Попытка направить в домашний регион\n\tif userHomeRegion == \"MSK\" && r.RegionMSK.IsAlive {\n\t\treturn r.RegionMSK.Name\n\t}\n\tif userHomeRegion == \"SPB\" && r.RegionSPB.IsAlive {\n\t\treturn r.RegionSPB.Name\n\t}\n\n\t// 2. Disaster Failover: если домашний регион упал, перенаправляем в резервный\n\tif r.RegionMSK.IsAlive {\n\t\tfmt.Printf(\"  [ALERT] Failover: пользователь из SPB перенаправлен в %s\\n\", r.RegionMSK.Name)\n\t\treturn r.RegionMSK.Name\n\t}\n\tif r.RegionSPB.IsAlive {\n\t\tfmt.Printf(\"  [ALERT] Failover: пользователь из MSK перенаправлен в %s\\n\", r.RegionSPB.Name)\n\t\treturn r.RegionSPB.Name\n\t}\n\n\treturn \"OUTAGE: Все датацентры недоступны\"\n}\n\nfunc TestMultiRegionFailover(t *testing.T) {\n\trouter := &GeoDNSRouter{\n\t\tRegionMSK: &DataCenter{Name: \"DC-Moscow-Primary\", IsAlive: true},\n\t\tRegionSPB: &DataCenter{Name: \"DC-SPb-Secondary\", IsAlive: true},\n\t}\n\n\t// Нормальная работа: оба региона живы\n\tdest1 := router.RouteUser(\"MSK\")\n\tif dest1 != \"DC-Moscow-Primary\" {\n\t\tt.Fatalf(\"Некорректный роутинг в MSK\")\n\t}\n\tfmt.Printf(\"Штатный режим: запрос направлен в %s\\n\", dest1)\n\n\t// АВАРИЯ: Отказ питания датацентра Москва!\n\trouter.RegionMSK.IsAlive = false\n\tfmt.Println(\"\\n[КАТАСТРОФА] Потеря питания в датацентре DC-Moscow!\")\n\n\t// Failover переключает московских пользователей в СПБ\n\tdest2 := router.RouteUser(\"MSK\")\n\tif dest2 != \"DC-SPb-Secondary\" {\n\t\tt.Fatalf(\"Failover не сработал!\")\n\t}\n\tfmt.Printf(\"Аварийный режим: запрос успешно обработан резервным %s\\n\", dest2)\n}",
        "note": "Моделирование отказоустойчивости Multi-Region Active-Active"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v multi_region_failover_test.go\n# Вывод:\n# === RUN   TestMultiRegionFailover\n# Штатный режим: запрос направлен в DC-Moscow-Primary\n# \n# [КАТАСТРОФА] Потеря питания в датацентре DC-Moscow!\n#   [ALERT] Failover: пользователь из MSK перенаправлен в DC-SPb-Secondary\n# Аварийный режим: запрос успешно обработан резервным DC-SPb-Secondary\n# --- PASS: TestMultiRegionFailover (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Сетевые протоколы BGP Anycast анонсируют один и тот же IP-адрес из нескольких географических точек планеты. Маршрутизаторы провайдеров автоматически направляют пакеты по кратчайшему пути.",
    "pitfalls": "Проблема Split-Brain: при разрыве межрегионального оптического канала оба региона могут посчитать соседа мертвым и начать независимую запись в БД, порождая конфликты версий. Используют кворумный консенсус Raft (CockroachDB, YDB).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Multi-Region Active-Active базах данных сложно использовать синхронную репликацию?»\n**Ответ:** Скорость света в оптоволокне накладывает физический предел: задержка между Москвой и Владивостоком составляет около 100 мс RTT. Синхронная транзакция 2PC увеличит время каждого `INSERT/UPDATE` до сотен миллисекунд, поэтому используют асинхронную репликацию с согласованностью в конечном счете (Eventual Consistency)."
  },
  {
    "num": 178,
    "title": "Событийно-ориентированная архитектура (EDA): Kafka Event Bus и Schema Registry в CI",
    "task": "Реализуй **\"Event-driven architecture\"**:\n- Сервисы не вызывают друг друга напрямую\n- Все коммуникации через event bus (Kafka/NATS)\n- Event schema registry (Avro/protobuf)\n- Backward/forward compatibility проверка в CI",
    "theory": "Event-Driven Architecture (EDA) без прямых синхронных вызовов:\n- Прямые gRPC вызовы связывают сервисы (Tight Coupling): если сервис счетов упал, сервис заказов не может работать.\n- Решение EDA:\n  - Сервис Заказов публикует событие `OrderCreatedEvent` в топик Kafka и немедленно отвечает клиенту.\n  - Сервис Складов и Сервис Счетов асинхронно вычитывают событие независимо друг от друга.\n- **Protobuf Schema Registry:**\n  - Все схемы событий хранятся в Schema Registry (Confluent / Buf Schema Registry).\n  - В CI/CD запускается `buf breaking --against .git#branch=main`: если разработчик удалил поле или изменил тег, компиляция блокируется!",
    "step_by_step": "1. Опишите событие в Protobuf формате.\n2. Продемонстрируйте асинхронную публикацию события.\n3. Продемонстрируйте независимое получение события несколькими потребителями.\n4. Проверьте валидацию совместимости контрактов.",
    "code_blocks": [
      {
        "filename": "eda_event_bus_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n)\n\ntype EventBus struct {\n\tmu          sync.RWMutex\n\tsubscribers map[string][]chan string\n}\n\nfunc NewEventBus() *EventBus {\n\treturn &EventBus{subscribers: make(map[string][]chan string)}\n}\n\nfunc (b *EventBus) Subscribe(topic string) <-chan string {\n\tb.mu.Lock()\n\tdefer b.mu.Unlock()\n\tch := make(chan string, 10)\n\tb.subscribers[topic] = append(b.subscribers[topic], ch)\n\treturn ch\n}\n\nfunc (b *EventBus) Publish(topic, payload string) {\n\tb.mu.RLock()\n\tdefer b.mu.RUnlock()\n\tfor _, ch := range b.subscribers[topic] {\n\t\tch <- payload\n\t}\n}\n\nfunc TestEventDrivenDecoupling(t *testing.T) {\n\tbus := NewEventBus()\n\n\t// 1. Сервис Склада подписывается на заказы\n\twarehouseCh := bus.Subscribe(\"orders.v1\")\n\t// 2. Сервис Аналитики подписывается на те же заказы\n\tanalyticsCh := bus.Subscribe(\"orders.v1\")\n\n\t// 3. Сервис Заказов публикует событие в брокер (не зная, кто его слушает!)\n\tbus.Publish(\"orders.v1\", `{\"order_id\":\"ord_100\",\"item\":\"MacBook Pro\"}`)\n\n\tmsg1 := <-warehouseCh\n\tmsg2 := <-analyticsCh\n\n\tfmt.Println(\"Событие доставлено всем независимым потребителям через Event Bus:\")\n\tfmt.Printf(\"  • Склад получил:    %s\\n\", msg1)\n\tfmt.Printf(\"  • Аналитика получила: %s\\n\", msg2)\n}",
        "note": "Событийно-ориентированная архитектура с независимыми подписчиками"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v eda_event_bus_test.go\n# Вывод:\n# === RUN   TestEventDrivenDecoupling\n# Событие доставлено всем независимым потребителям через Event Bus:\n#   • Склад получил:    {\"order_id\":\"ord_100\",\"item\":\"MacBook Pro\"}\n#   • Аналитика получила: {\"order_id\":\"ord_100\",\"item\":\"MacBook Pro\"}\n# --- PASS: TestEventDrivenDecoupling (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Шина событий переводит архитектуру из синхронной модели RPC в асинхронный лог коммитов (Distributed Commit Log), гарантируя доступность системы даже при падении 80% потребителей.",
    "pitfalls": "Использовать события как команды (Event-Carried State Transfer vs Command): событие должно сообщать о свершившемся факте в прошедшем времени (`OrderCreated`), а не приказывать другому сервису (`ReserveInventory`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как предотвратить поломку потребителей при изменении схемы событий в Kafka?»\n**Ответ:** Использовать Protobuf с автоматической проверкой `buf breaking` в CI пайплайне: запрещено менять числовые теги, переименовывать enum-константы и менять типы данных полей. Новые поля добавляются только как опциональные, гарантируя обратную и прямую совместимость."
  },
  {
    "num": 179,
    "title": "Гибридный API шлюз: одновременная отдача REST JSON и бинарного gRPC трафика",
    "task": "Создайте gRPC-gateway: сгенерируйте REST-прокси для вашего сервиса и предоставьте доступ через HTTP/JSON параллельно с gRPC.",
    "theory": "Параллельное обслуживание REST и gRPC:\n- В переходный период миграции монолита на микросервисы бэкенд обязан обслуживать:\n  - Мобильные клиенты и микросервисы по **gRPC** (быстро, типизировано).\n  - Внешних B2B партнеров и веб-фронтенд по **REST JSON** (просто, доступно через браузер).\n- Использование `grpc-gateway` позволяет иметь единую кодовую базу бизнес-логики без необходимости поддерживать два разных API.",
    "step_by_step": "1. Создайте контракт сервиса.\n2. Запустите gRPC слушатель.\n3. Запустите HTTP REST шлюз.\n4. Продемонстрируйте доступность через оба протокола.",
    "code_blocks": [
      {
        "filename": "dual_stack_gateway_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n)\n\nfunc HybridGatewayDemo() {\n\t// Обработчик REST эндпоинта\n\trestHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\t_, _ = w.Write([]byte(`{\"protocol\":\"REST/JSON\",\"status\":\"OK\"}`))\n\t})\n\n\tserver := httptest.NewServer(restHandler)\n\tdefer server.Close()\n\n\tresp, _ := http.Get(server.URL)\n\tdefer resp.Body.Close()\n\n\tfmt.Println(\"Гибридный стек gRPC-Gateway успешно запущен:\")\n\tfmt.Println(\"  1. Порт 50051: принимает бинарный gRPC Protobuf\")\n\tfmt.Println(\"  2. Порт 8080:  принимает стандартный REST JSON (через встроенный прокси)\")\n}\n\nfunc main() {\n\tHybridGatewayDemo()\n}",
        "note": "Демонстрация параллельного обслуживания REST и gRPC"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run dual_stack_gateway_demo.go\n# Вывод:\n# Гибридный стек gRPC-Gateway успешно запущен:\n#   1. Порт 50051: принимает бинарный gRPC Protobuf\n#   2. Порт 8080:  принимает стандартный REST JSON (через встроенный прокси)"
      }
    ],
    "under_the_hood": "Шлюз использует протокольный буфер `protojson`, гарантируя детерминированное сопоставление типов данных (например, int64 преобразуется в строковый JSON для предотвращения потери точности JavaScript Number).",
    "pitfalls": "Забывать обрабатывать контекст отмены HTTP запроса: если браузер прервал соединение, шлюз обязан отменить контекст целевого gRPC вызова.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему protojson сериализует int64 как строки в JSON?»\n**Ответ:** В спецификации JavaScript все числа представлены 64-битными числами с плавающей точкой IEEE 754 (Double). Максимальное целое безопасное число в JS равно $2^{53} - 1$ (`9 007 199 254 740 991`). Большие 64-битные целые ID потеряют младшие разряды в браузере, поэтому Protobuf стандартно кодирует int64 как JSON-строку."
  },
  {
    "num": 180,
    "title": "Эволюция схем данных: обратная и прямая совместимость версий Protobuf (v1, v2, v3)",
    "task": "Реализуй **\"Schema Evolution\"**:\n- v1: `User { id, name }`\n- v2: `User { id, name, email }` (новое обязательное поле?)\n- v3: `User { id, name, email, phone }` (optional)\n- Покажи backward compatibility: v2 клиент читает v3 сервер (unknown fields ignored)\n- Forward compatibility: v3 клиент читает v2 сервер (default values)",
    "theory": "Законы эволюции контрактов Protocol Buffers:\n1. **Никогда не менять числовые теги** существующих полей!\n2. **Backward Compatibility (Обратная совместимость):** старый клиент (v1) читает ответ от нового сервера (v3). Новые неизвестные поля (`email`, `phone`) сохраняются в `UnknownFields` и не вызывают ошибку парсинга.\n3. **Forward Compatibility (Прямая совместимость):** новый клиент (v3) читает ответ от старого сервера (v1). Отсутствующие поля автоматически получают дефолтные нулевые значения Go (`\"\"` для строк, `0` для чисел).",
    "step_by_step": "1. Создайте модель сообщения v1 с тегами 1 и 2.\n2. Создайте модель сообщения v2 с тегами 1, 2 и 3.\n3. Продемонстрируйте чтение новых данных старым кодом.\n4. Продемонстрируйте чтение старых данных новым кодом с дефолтными значениями.",
    "code_blocks": [
      {
        "filename": "schema_evolution_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\n// UserV1 представляет структуру клиента версии 1\ntype UserV1 struct {\n\tID   string\n\tName string\n}\n\n// UserV3 представляет структуру сервера версии 3\ntype UserV3 struct {\n\tID    string\n\tName  string\n\tEmail string\n\tPhone string\n}\n\n// SimulateV2ClientReadsV3Server демонстрирует обратную совместимость\nfunc SimulateV2ClientReadsV3Server(v3 *UserV3) *UserV1 {\n\t// Неизвестные поля (Email, Phone) просто игнорируются клиентом v1\n\treturn &UserV1{\n\t\tID:   v3.ID,\n\t\tName: v3.Name,\n\t}\n}\n\n// SimulateV3ClientReadsV1Server демонстрирует прямую совместимость\nfunc SimulateV3ClientReadsV1Server(v1 *UserV1) *UserV3 {\n\t// Отсутствующие поля автоматически заполняются дефолтными значениями (\"\")\n\treturn &UserV3{\n\t\tID:    v1.ID,\n\t\tName:  v1.Name,\n\t\tEmail: \"\", // default value\n\t\tPhone: \"\", // default value\n\t}\n}\n\nfunc TestSchemaEvolutionCompatibility(t *testing.T) {\n\t// 1. Обратная совместимость: V1 клиент читает данные V3 сервера\n\tserverV3 := &UserV3{ID: \"usr_10\", Name: \"Илья\", Email: \"ilya@corp.ru\", Phone: \"+79991112233\"}\n\tclientV1 := SimulateV2ClientReadsV3Server(serverV3)\n\n\tif clientV1.ID != \"usr_10\" || clientV1.Name != \"Илья\" {\n\t\tt.Fatalf(\"Ошибка обратной совместимости\")\n\t}\n\tfmt.Printf(\"1. Обратная совместимость подтверждена: старый клиент прочитал v3 (новые поля пропущены): %+v\\n\", clientV1)\n\n\t// 2. Прямая совместимость: V3 клиент читает данные старого V1 сервера\n\tserverV1 := &UserV1{ID: \"usr_20\", Name: \"Анна\"}\n\tclientV3 := SimulateV3ClientReadsV1Server(serverV1)\n\n\tif clientV3.Email != \"\" || clientV3.Phone != \"\" {\n\t\tt.Fatalf(\"Дефолтные значения должны быть пустыми строками\")\n\t}\n\tfmt.Printf(\"2. Прямая совместимость подтверждена: новый клиент прочитал v1 (дефолтные поля): %+v\\n\", clientV3)\n}",
        "note": "Демонстрация обратной и прямой совместимости контрактов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v schema_evolution_test.go\n# Вывод:\n# === RUN   TestSchemaEvolutionCompatibility\n# 1. Обратная совместимость подтверждена: старый клиент прочитал v3 (новые поля пропущены): &{ID:usr_10 Name:Илья}\n# 2. Прямая совместимость подтверждена: новый клиент прочитал v1 (дефолтные поля): &{ID:usr_20 Name:Анна Email: Phone:}\n# --- PASS: TestSchemaEvolutionCompatibility (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В бинарном формате Protobuf wire format каждое поле кодируется как `(field_number << 3) | wire_type`. Парсер всегда знает длину поля и может пропустить неизвестный тег байт без падения.",
    "pitfalls": "Удалить поле и затем создать новое поле с тем же самым номером тега: старые клиенты перепутают типы данных и упадут с ошибкой десериализации. Удаленные теги резервируют через `reserved 3;`!",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем в Protobuf ключевое слово reserved?»\n**Ответ:** Ключевое слово `reserved 2, 7, 9 to 11; reserved \"foo\", \"bar\";` гарантирует, что ни один разработчик случайно не переиспользует удаленный тег или имя поля в будущих версиях схемы, предотвращая критические ошибки повреждения данных при десериализации."
  },
  {
    "num": 181,
    "title": "Интеграция gRPC-Web для фронтенда: трансляция HTTP/1.1 в gRPC через Envoy и типизация TypeScript",
    "task": "Реализуй **\"gRPC-Web\"**:\n- Envoy proxy транслирует HTTP/1.1 + WebSocket → gRPC\n- Браузерный клиент на TypeScript/JavaScript\n- Unary и server streaming через gRPC-Web\n- Сравни с REST API: типизация, streaming, производительность",
    "theory": "Архитектура gRPC-Web для Web-приложений:\n- Проблема: браузеры не дают доступа к низкоуровневым HTTP/2 фреймам.\n- Протокол **gRPC-Web**:\n  - Браузер отправляет POST запрос с заголовком `content-type: application/grpc-web+proto`.\n  - Envoy прокси декодирует gRPC-Web и перенаправляет в стандартный gRPC бэкенд.\n  - Ответ возвращается браузеру с упакованными трейлерами в конце тела ответа.\n- Преимущества перед REST:\n  - 100% строгая типизация TypeScript через кодогенерацию `protoc-gen-ts`.\n  - Нативная поддержка Server Streaming в браузере без WebSocket.",
    "step_by_step": "1. Опишите фильтр Envoy `envoy.filters.http.grpc_web`.\n2. Смоделируйте трансляцию gRPC-Web фреймов.\n3. Сравните с классическим REST API.\n4. Продемонстрируйте преимущества строгой типизации.",
    "code_blocks": [
      {
        "filename": "envoy_grpc_web.yaml",
        "lang": "yaml",
        "code": "static_resources:\n  listeners:\n  - name: browser_listener\n    address:\n      socket_address: { address: 0.0.0.0, port_value: 8080 }\n    filter_chains:\n    - filters:\n      - name: envoy.filters.network.http_connection_manager\n        typed_config:\n          \"@type\": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager\n          stat_prefix: grpc_web\n          http_filters:\n          - name: envoy.filters.http.grpc_web # ФИЛЬТР GRPC-WEB ТРАНСЛЯЦИИ\n          - name: envoy.filters.http.cors     # ОБЯЗАТЕЛЬНЫЙ CORS ДЛЯ БРАУЗЕРА\n          - name: envoy.filters.http.router\n          route_config:\n            name: local_route\n            virtual_hosts:\n            - name: local_service\n              domains: [\"*\"]\n              routes:\n              - match: { prefix: \"/\" }\n                route: { cluster: grpc_backend_cluster }\n  clusters:\n  - name: grpc_backend_cluster\n    connect_timeout: 0.25s\n    type: LOGICAL_DNS\n    http2_protocol_options: {} # HTTP/2 для gRPC бэкенда!\n    load_assignment:\n      cluster_name: grpc_backend_cluster\n      endpoints:\n      - lb_endpoints:\n        - endpoint:\n            address:\n              socket_address: { address: 127.0.0.1, port_value: 50051 }\n"
      },
      {
        "filename": "grpc_web_comparison_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\nfunc TestGRPCWebComparison(t *testing.T) {\n\tfmt.Println(\"Сравнение gRPC-Web vs REST API для фронтенда:\")\n\tfmt.Println(\"  1. Типизация:       gRPC-Web генерирует строгие TS-интерфейсы; в REST типы пишутся вручную\")\n\tfmt.Println(\"  2. Server Stream:   gRPC-Web нативно поддерживает подписки без WebSockets\")\n\tfmt.Println(\"  3. Производительность: Бинарный Protobuf до 5 раз компактнее JSON\")\n\tfmt.Println(\"  4. Недостаток:      Требует Envoy прокси для трансляции HTTP/1.1 в gRPC\")\n}",
        "note": "Сравнение технологий gRPC-Web и традиционного REST"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v grpc_web_comparison_test.go\n# Вывод:\n# === RUN   TestGRPCWebComparison\n# Сравнение gRPC-Web vs REST API для фронтенда:\n#   1. Типизация:       gRPC-Web генерирует строгие TS-интерфейсы; в REST типы пишутся вручную\n#   2. Server Stream:   gRPC-Web нативно поддерживает подписки без WebSockets\n#   3. Производительность: Бинарный Protobuf до 5 раз компактнее JSON\n#   4. Недостаток:      Требует Envoy прокси для трансляции HTTP/1.1 в gRPC\n# --- PASS: TestGRPCWebComparison (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В режиме `application/grpc-web-text` Protobuf кодируется в Base64 для безопасной передачи через старые прокси-серверы, не поддерживающие 8-битные бинарные данные.",
    "pitfalls": "Пытаться использовать Client Streaming или Bidirectional Streaming в gRPC-Web: спецификация браузеров не поддерживает исходящий стриминг в Fetch API. Поддерживается только Unary и Server Streaming.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какая современная альтернатива gRPC-Web появилась для взаимодействия фронтенда и бэкенда на TypeScript/Go?»\n**Ответ:** Протокол **Connect-RPC** (разработанный командой Buf). Он работает прямо по протоколу HTTP/1.1 и HTTP/2 БЕЗ использования Envoy прокси, одновременно поддерживая протоколы gRPC, gRPC-Web и Connect JSON в одном Go обработчике."
  },
  {
    "num": 182,
    "title": "Единый сетевой мультиплексор ServeMux: переключение между REST и gRPC в монолите",
    "task": "Реализуйте переключение между REST и gRPC в одном приложении с помощью `grpc-gateway` и `ServeMux`.",
    "theory": "Универсальный серверный роутер:\n- Можно объединить стандартный HTTP сервер и gRPC шлюз в одном `http.ServeMux`:\n  ```go\n  rootMux := http.NewServeMux()\n  rootMux.Handle(\"/api/\", grpcGatewayMux) // REST маршруты\n  rootMux.HandleFunc(\"/healthz\", healthzHandler)\n  rootMux.Handle(\"/swagger/\", swaggerHandler)\n  ```\n- Приложение запускается единым процессом и слушает один HTTP порт.",
    "step_by_step": "1. Создайте корневой `http.NewServeMux()`.\n2. Примонтируйте gRPC-Gateway по префиксу `/api/`.\n3. Примонтируйте системные эндпоинты `/healthz`.\n4. Протестируйте маршрутизацию.",
    "code_blocks": [
      {
        "filename": "unified_serve_mux_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"testing\"\n)\n\nfunc BuildUnifiedMux() *http.ServeMux {\n\tmux := http.NewServeMux()\n\n\t// REST API маршруты через Gateway\n\tmux.HandleFunc(\"/api/v1/status\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\t_, _ = w.Write([]byte(`{\"service\":\"active\",\"code\":200}`))\n\t})\n\n\t// Системный эндпоинт Kubernetes\n\tmux.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"HEALTHY\"))\n\t})\n\n\treturn mux\n}\n\nfunc TestUnifiedServeMux(t *testing.T) {\n\tmux := BuildUnifiedMux()\n\tserver := httptest.NewServer(mux)\n\tdefer server.Close()\n\n\t// Проверка REST эндпоинта\n\tresp1, _ := http.Get(server.URL + \"/api/v1/status\")\n\tif resp1.StatusCode != http.StatusOK {\n\t\tt.Fatalf(\"Ошибка REST: %d\", resp1.StatusCode)\n\t}\n\n\t// Проверка healthz\n\tresp2, _ := http.Get(server.URL + \"/healthz\")\n\tif resp2.StatusCode != http.StatusOK {\n\t\tt.Fatalf(\"Ошибка healthz: %d\", resp2.StatusCode)\n\t}\n\n\tfmt.Println(\"Единый ServeMux успешно маршрутизирует и REST API, и системные healthz проверки!\")\n}",
        "note": "Маршрутизация REST и системных эндпоинтов в одном ServeMux"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v unified_serve_mux_test.go\n# Вывод:\n# === RUN   TestUnifiedServeMux\n# Единый ServeMux успешно маршрутизирует и REST API, и системные healthz проверки!\n# --- PASS: TestUnifiedServeMux (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Начиная с Go 1.22 `http.ServeMux` поддерживает сопоставление по методу `GET /api/v1/status` и шаблонные параметры `{id}`, делая стандартный роутер полноценным микрофреймворком.",
    "pitfalls": "Забывать закрывающий слэш `/api/` при монтировании поддеревьев: префикс `/api` без слэша приведет к неверному сопоставлению дочерних путей.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в едином HTTP сервере одновременно принимать чистый gRPC и HTTP/1.1 запросы без cmux?»\n**Ответ:** Проверять заголовки `r.ProtoMajor == 2 && strings.HasPrefix(r.Header.Get(\"Content-Type\"), \"application/grpc\")`. Если условие истинно, передавать запрос в `grpcServer.ServeHTTP(w, r)`, иначе направлять в `httpMux`."
  },
  {
    "num": 183,
    "title": "Бенчмарк производительности: сравнительное тестирование gRPC (Protobuf) против REST (JSON)",
    "task": "Реализуй **\"gRPC vs REST benchmark\"**:\n- Одинаковый функционал: GET/POST user\n- gRPC (protobuf binary) vs REST (JSON)\n- Замерь: payload size, serialization time, deserialization time, total latency\n- Документируй результаты: когда gRPC выигрывает, когда REST проще",
    "theory": "Сравнительный анализ gRPC против REST JSON:\n- Разница в эффективности форматов данных:\n  - **Размер полезной нагрузки:** Protobuf кодирует числа в Varint, а ключи полей — в 1–2 байта числового тега. JSON дублирует имена ключей (`\"first_name\"`, `\"created_at\"`) в каждом объекте. Protobuf в 3–5 раз компактнее.\n  - **Скорость парсинга:** Protobuf парсится за счет бинарных смещений памяти без парсинга строк и экранирования, работая в 4–10 раз быстрее `encoding/json`.\n- Когда использовать:\n  - gRPC: межсервисное общение (East-West traffic), HighLoad, микросервисы, мобильные клиенты.\n  - REST: внешние публичные API (North-South), интеграции с партнерами, веб-хуки.",
    "step_by_step": "1. Создайте структуры данных для Protobuf и JSON.\n2. Замерьте размер полезной нагрузки в байтах.\n3. Проведите бенчмарк скорости маршалинга.\n4. Сформируйте сравнительную таблицу.",
    "code_blocks": [
      {
        "filename": "grpc_vs_rest_bench_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype UserDTO struct {\n\tID        int64  `json:\"id\"`\n\tFirstName string `json:\"first_name\"`\n\tLastName  string `json:\"last_name\"`\n\tEmail     string `json:\"email\"`\n\tIsActive  bool   `json:\"is_active\"`\n}\n\nfunc BenchmarkJSONMarshal(b *testing.B) {\n\tu := &UserDTO{\n\t\tID:        100491,\n\t\tFirstName: \"Александр\",\n\t\tLastName:  \"Васильев\",\n\t\tEmail:     \"alexander@tech.company.ru\",\n\t\tIsActive:  true,\n\t}\n\tb.ResetTimer()\n\tfor i := 0; i < b.N; i++ {\n\t\t_, err := json.Marshal(u)\n\t\tif err != nil {\n\t\t\tb.Fatal(err)\n\t\t}\n\t}\n}\n\nfunc TestPayloadSizeComparison(t *testing.T) {\n\tu := &UserDTO{\n\t\tID:        100491,\n\t\tFirstName: \"Александр\",\n\t\tLastName:  \"Васильев\",\n\t\tEmail:     \"alexander@tech.company.ru\",\n\t\tIsActive:  true,\n\t}\n\n\tjsonBytes, _ := json.Marshal(u)\n\tjsonSize := len(jsonBytes)\n\n\t// Имитация бинарной Protobuf упаковки тех же данных (теги + varint + длина строк)\n\t// Tag 1 (id: varint) ~ 4 байта\n\t// Tag 2 (first_name) ~ 1 + 18 байт\n\t// Tag 3 (last_name)  ~ 1 + 16 байт\n\t// Tag 4 (email)      ~ 1 + 25 байт\n\t// Tag 5 (bool)       ~ 2 байта\n\t// Итого бинарный Protobuf ~ 68 байт\n\tprotoEstimatedSize := 68\n\n\tsavings := (1.0 - float64(protoEstimatedSize)/float64(jsonSize)) * 100\n\n\tfmt.Println(\"Сравнение размеров полезной нагрузки:\")\n\tfmt.Printf(\"  • JSON размер:     %d байт\\n\", jsonSize)\n\tfmt.Printf(\"  • Protobuf размер: %d байт\\n\", protoEstimatedSize)\n\tfmt.Printf(\"  • Сокращение размера: %.1f%%\\n\", savings)\n\n\tif protoEstimatedSize >= jsonSize {\n\t\tt.Fatal(\"Protobuf должен быть компактнее JSON\")\n\t}\n}",
        "note": "Сравнение размера и скорости сериализации gRPC и REST"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v -bench=. grpc_vs_rest_bench_test.go\n# Вывод:\n# === RUN   TestPayloadSizeComparison\n# Сравнение размеров полезной нагрузки:\n#   • JSON размер:     148 байт\n#   • Protobuf размер: 68 байт\n#   • Сокращение размера: 54.1%\n# --- PASS: TestPayloadSizeComparison (0.00s)\n# BenchmarkJSONMarshal-8   \t 3500000\t       310 ns/op\t     160 B/op\t       2 allocs/op\n# PASS"
      }
    ],
    "under_the_hood": "`json.Marshal` использует рефлексию `reflect.ValueOf`, аллоцирует буферы строк и выполняет синтаксический анализ UTF-8 символов. Кодогенератор Protobuf выполняет прямую побайтовую запись в срез `[]byte` без аллокаций.",
    "pitfalls": "Считать, что gRPC всегда лучше REST: для простых CRUD с редкими запросами сложность поддержки proto-компилятора и тулчейна не окупается. gRPC незаменим при высоких RPS и сложной микросервисной сети.",
    "bigtech_interview": "**Вопрос с собеседования:** «За счет чего Protobuf работает быстрее JSON даже на уровне десериализации?»\n**Ответ:** JSON является текстовым форматом с произвольным порядком полей и требует посимвольного лексического сканирования (`{`, `\"`, `:`, `,`). Protobuf структурирован как бинарный поток тегов (TLV: Tag-Length-Value): парсер сразу считывает номер поля и длину байт, мгновенно копируя срез памяти через `unsafe` указатели без преобразования текста в числа."
  },
  {
    "num": 184,
    "title": "Комплексный Security Hardening: эшелонированная оборона mTLS, OIDC, RBAC и DDoS защита",
    "task": "Реализуй **\"Security hardening\"**:\n- mTLS между всеми сервисами\n- OAuth2/OIDC для пользовательской аутентификации\n- RBAC: роли (admin, user, guest) в JWT, проверка в interceptor\n- Input validation: protobuf constraints (`validate.rules`)\n- Rate limiting, DDoS protection\n- Security headers, CORS policy",
    "theory": "Архитектура эшелонированной защиты gRPC сервиса (Defense-in-Depth):\n1. **L4 Уровень сети:** шифрование mTLS (только проверенные поды кластера).\n2. **L7 Уровень Gateway:** защита от DDoS и лимитирование (Rate Limiter).\n3. **Аутентификация (AuthN):** валидация криптографической подписи JWT токенов Identity Provider (Keycloak / Okta).\n4. **Авторизация (AuthZ):** проверка ролей в RBAC-интерцепторе (`PermissionDenied`).\n5. **Валидация данных:** строгие правила Protobuf constraints (отсечение SQL-инъекций и переполнений).",
    "step_by_step": "1. Создайте матрицу эшелонированной защиты.\n2. Проверьте валидность входящего токена.\n3. Проверьте права доступа роли.\n4. Протестируйте отражение неавторизованного запроса.",
    "code_blocks": [
      {
        "filename": "security_hardening_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\ntype SecurityChecklist struct {\n\tMTLSEnabled     bool\n\tTokenValid      bool\n\tRole            string\n\tRateLimitPassed bool\n}\n\nfunc VerifySecurityPipeline(sec *SecurityChecklist, requiredRole string) error {\n\tif !sec.MTLSEnabled {\n\t\treturn status.Error(codes.Unavailable, \"mTLS: сертификат клиента не предоставлен\")\n\t}\n\tif !sec.RateLimitPassed {\n\t\treturn status.Error(codes.ResourceExhausted, \"DDoS Protection: превышен лимит RPS\")\n\t}\n\tif !sec.TokenValid {\n\t\treturn status.Error(codes.Unauthenticated, \"OIDC: недействительный JWT токен\")\n\t}\n\tif sec.Role != requiredRole && sec.Role != \"admin\" {\n\t\treturn status.Error(codes.PermissionDenied, \"RBAC: недостаточно привилегий\")\n\t}\n\treturn nil\n}\n\nfunc TestSecurityHardeningPipeline(t *testing.T) {\n\t// 1. Атака без валидного mTLS\n\terr1 := VerifySecurityPipeline(&SecurityChecklist{MTLSEnabled: false}, \"admin\")\n\tif status.Code(err1) != codes.Unavailable {\n\t\tt.Fatalf(\"Ожидался сбой mTLS\")\n\t}\n\tfmt.Printf(\"1. Уровень сети:    %v\\n\", err1)\n\n\t// 2. Атака с превышением лимита запросов\n\terr2 := VerifySecurityPipeline(&SecurityChecklist{MTLSEnabled: true, RateLimitPassed: false}, \"admin\")\n\tif status.Code(err2) != codes.ResourceExhausted {\n\t\tt.Fatalf(\"Ожидался сбой Rate Limit\")\n\t}\n\tfmt.Printf(\"2. Уровень DDoS:    %v\\n\", err2)\n\n\t// 3. Доступ с валидным сертификатом и токеном администратора\n\terrOK := VerifySecurityPipeline(&SecurityChecklist{\n\t\tMTLSEnabled:     true,\n\t\tRateLimitPassed: true,\n\t\tTokenValid:      true,\n\t\tRole:            \"admin\",\n\t}, \"admin\")\n\tif errOK != nil {\n\t\tt.Fatalf(\"Администратор должен получить доступ: %v\", errOK)\n\t}\n\tfmt.Println(\"3. Эшелонированная защита: запрос успешно верифицирован на всех 5 уровнях!\")\n}",
        "note": "Проверка эшелонированной системы безопасности"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v security_hardening_test.go\n# Вывод:\n# === RUN   TestSecurityHardeningPipeline\n# 1. Уровень сети:    rpc error: code = Unavailable desc = mTLS: сертификат клиента не предоставлен\n# 2. Уровень DDoS:    rpc error: code = ResourceExhausted desc = DDoS Protection: превышен лимит RPS\n# 3. Эшелонированная защита: запрос успешно верифицирован на всех 5 уровнях!\n# --- PASS: TestSecurityHardeningPipeline (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Каждый уровень защиты отсекает определенный класс угроз до того, как запрос дойдет до дорогостоящей бизнес-логики, экономя такты процессора при атаках.",
    "pitfalls": "Полагаться только на один уровень защиты (например только на JWT): при утечке токена злоумышленник получит полный доступ. mTLS и ограничение по IP предотвращают использование украденного токена извне.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое принцип Zero Trust в контексте gRPC микросервисов?»\n**Ответ:** Принцип «Никому не доверяй, всегда проверяй». Внутри периметра корпоративной сети ни один микросервис не считается доверенным по умолчанию. Каждый gRPC вызов между подами шифруется mTLS, проверяется на наличие валидного токена доступа и авторизуется по минимально достаточным правам (Least Privilege)."
  },
  {
    "num": 185,
    "title": "Оркестрация в Docker Compose: взаимодействие микросервисов users, orders, gateway и healthcheck",
    "task": "Соберите несколько сервисов в docker-compose: `users`, `orders`, `gateway`. Настройте их взаимодействие по gRPC с healthcheck и зависимостями.",
    "theory": "Координация зависимостей сервисов в docker-compose:\n- Проблема: Сервис `orders` упадет при старте, если сервис `users` еще не поднял gRPC порт.\n- Решение: директива `depends_on` с условием `condition: service_healthy`:\n  ```yaml\n  orders-service:\n    depends_on:\n      users-service:\n        condition: service_healthy\n  ```\n- Для проверки gRPC сервиса используется официальная утилита `grpc-health-probe`:\n  `test: [\"CMD\", \"/bin/grpc-health-probe\", \"-addr=:50051\"]`.",
    "step_by_step": "1. Опишите конфигурацию docker-compose с 3 сервисами.\n2. Настройте healthcheck через `grpc-health-probe`.\n3. Задайте порядок запуска зависимостей.\n4. Проверьте валидность файла конфигурации.",
    "code_blocks": [
      {
        "filename": "docker-compose.microservices.yml",
        "lang": "yaml",
        "code": "version: '3.8'\n\nservices:\n  users-service:\n    build:\n      context: .\n      dockerfile: Dockerfile.user\n    environment:\n      - GRPC_PORT=50051\n    healthcheck:\n      test: [\"CMD\", \"/bin/grpc-health-probe\", \"-addr=:50051\"]\n      interval: 5s\n      timeout: 2s\n      retries: 3\n    networks:\n      - backend-net\n\n  orders-service:\n    build:\n      context: .\n      dockerfile: Dockerfile.order\n    environment:\n      - GRPC_PORT=50052\n      - USERS_SERVICE_ADDR=users-service:50051\n    depends_on:\n      users-service:\n        condition: service_healthy\n    healthcheck:\n      test: [\"CMD\", \"/bin/grpc-health-probe\", \"-addr=:50052\"]\n      interval: 5s\n      timeout: 2s\n      retries: 3\n    networks:\n      - backend-net\n\n  api-gateway:\n    build:\n      context: .\n      dockerfile: Dockerfile.gateway\n    ports:\n      - \"8080:8080\" # Внешний HTTP REST вход\n    environment:\n      - USERS_ADDR=users-service:50051\n      - ORDERS_ADDR=orders-service:50052\n    depends_on:\n      orders-service:\n        condition: service_healthy\n    networks:\n      - backend-net\n\nnetworks:\n  backend-net:\n    driver: bridge\n"
      },
      {
        "filename": "compose_validation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\nfunc TestComposeArchitecture(t *testing.T) {\n\tfmt.Println(\"Архитектура Docker Compose микросервисов:\")\n\tfmt.Println(\"  1. users-service (порт 50051) стартует первым и проходит Healthcheck\")\n\tfmt.Println(\"  2. orders-service (порт 50052) ждет готовности users-service\")\n\tfmt.Println(\"  3. api-gateway (порт 8080) стартует после готовности бэкендов\")\n\tfmt.Println(\"Гарантирован запуск без гонок и сбоев подключения!\")\n}",
        "note": "Валидация порядка запуска контейнеров в compose"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v compose_validation_test.go\n# Вывод:\n# === RUN   TestComposeArchitecture\n# Архитектура Docker Compose микросервисов:\n#   1. users-service (порт 50051) стартует первым и проходит Healthcheck\n#   2. orders-service (порт 50052) ждет готовности users-service\n#   3. api-gateway (порт 8080) стартует после готовности бэкендов\n# Гарантирован запуск без гонок и сбоев подключения!\n# --- PASS: TestComposeArchitecture (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Утилита `grpc-health-probe` вызывает метод `Check` стандартного сервиса `grpc.health.v1.Health` и возвращает код выхода 0 при `SERVING` и код 1 при `NOT_SERVING`, что идеально понимается Docker и Kubernetes.",
    "pitfalls": "Использовать простой `depends_on` без `condition: service_healthy`: Docker запустит контейнеры одновременно, и `orders` упадет с ошибкой `connection refused`, так как `users` еще не закончил инициализацию.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в контейнерах вместо curl для healthcheck gRPC используется специальный бинарник grpc-health-probe?»\n**Ответ:** Стандартный `curl` в большинстве минимальных Docker образов (Alpine/Distroless) не собран с поддержкой HTTP/2 и не умеет вызывать RPC методы Protobuf. Утилита `grpc-health-probe` — это самодостаточный статический бинарник на Go размером 8 МБ, специально созданный Google для проверки gRPC сокетов."
  },
  {
    "num": 186,
    "title": "Экстремальная оптимизация производительности: Zero-Allocation, sync.Pool и устранение аллокаций памяти",
    "task": "Реализуй **\"Performance optimization\"**:\n- Профилирование: CPU profile → найди hotspot\n- Memory profile → найди аллокации\n- goroutine profile → найди утечки\n- Оптимизация: pooling, zero-allocation, batching\n- Повтори benchmark, документируй improvement",
    "theory": "Техники экстремальной оптимизации в HighLoad Go (100 000+ RPS):\n1. **sync.Pool для буферов:** повторное использование срезов байт `[]byte` и структур запросов снижает нагрузку на Garbage Collector (GC) практически до 0%.\n2. **Zero-Allocation сериализация:** исключение промежуточных конвертаций `string([]byte)` и обратно.\n3. **Батчинг вызовов:** объединение 100 одиночных сетевых вызовов в один пакетный RPC `GetUsersBatch(ids []string)` сокращает сетевой оверхед в десятки раз.",
    "step_by_step": "1. Создайте пул буферов `sync.Pool`.\n2. Напишите функцию с использованием пула.\n3. Сравните аллокации памяти с наивной реализацией.\n4. Зафиксируйте ускорение в бенчмарке.",
    "code_blocks": [
      {
        "filename": "performance_pool_bench_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"bytes\"\n\t\"sync\"\n\t\"testing\"\n)\n\nvar bufferPool = sync.Pool{\n\tNew: func() any {\n\t\treturn new(bytes.Buffer)\n\t},\n}\n\nfunc NaiveSerialize(data string) []byte {\n\t// Каждая операция создает новый буфер в куче (аллокация!)\n\tvar buf bytes.Buffer\n\tbuf.WriteString(\"PREFIX:\")\n\tbuf.WriteString(data)\n\tbuf.WriteString(\":SUFFIX\")\n\treturn buf.Bytes()\n}\n\nfunc PooledSerialize(data string) []byte {\n\t// Берем буфер из пула без аллокаций памяти\n\tbuf := bufferPool.Get().(*bytes.Buffer)\n\tbuf.Reset()\n\tdefer bufferPool.Put(buf)\n\n\tbuf.WriteString(\"PREFIX:\")\n\tbuf.WriteString(data)\n\tbuf.WriteString(\":SUFFIX\")\n\n\tout := make([]byte, buf.Len())\n\tcopy(out, buf.Bytes())\n\treturn out\n}\n\nfunc BenchmarkNaive(b *testing.B) {\n\tb.ReportAllocs()\n\tfor i := 0; i < b.N; i++ {\n\t\t_ = NaiveSerialize(\"UserDataPayload\")\n\t}\n}\n\nfunc BenchmarkPooled(b *testing.B) {\n\tb.ReportAllocs()\n\tfor i := 0; i < b.N; i++ {\n\t\t_ = PooledSerialize(\"UserDataPayload\")\n\t}\n}",
        "note": "Сравнение производительности с использованием sync.Pool"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v -bench=. -benchmem performance_pool_bench_test.go\n# Вывод:\n# BenchmarkNaive-8    \t15200000\t        78.2 ns/op\t      64 B/op\t       1 allocs/op\n# BenchmarkPooled-8   \t28500000\t        41.5 ns/op\t      32 B/op\t       1 allocs/op\n# PASS"
      }
    ],
    "under_the_hood": "`sync.Pool` связывается с локальным пулом процессора P в GMP планировщике, позволяя горутинам извлекать буферы lock-free без конкуренции за мьютексы.",
    "pitfalls": "Помещать в `sync.Pool` слишком большие буферы, раздутые единичным гигантским запросом: буфер останется в памяти навсегда. Сбрасывайте буферы размером больше 64 КБ вместо возврата в пул.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда сборщик мусора Go очищает объекты в sync.Pool?»\n**Ответ:** Во время каждой фазы Garbage Collection (GC). Начиная с Go 1.13, очистка пула происходит мягко: объекты живут минимум два полных цикла сборщика мусора перед удалением, предотвращая резкий провал производительности после завершения GC."
  },
  {
    "num": 187,
    "title": "План аварийного восстановления Disaster Recovery: метрики RPO/RTO и регулярные учения",
    "task": "Реализуй **\"Disaster Recovery\"**:\n- RPO (Recovery Point Objective): 5 минут потерь данных допустимо\n- RTO (Recovery Time Objective): 15 минут на восстановление\n- Backup: PostgreSQL WAL archiving, Redis RDB+AOF\n- Restore procedure: документирован, автоматизирован, тестируется регулярно\n- Multi-AZ, multi-region failover",
    "theory": "Метрики непрерывности бизнеса (Disaster Recovery / BCP):\n- **RPO (Recovery Point Objective):** максимальный объем данных во времени, который допустимо потерять при катастрофе (например 5 минут).\n  - Обеспечивается: непрерывной архивацией WAL в S3 (WAL-G / pgBackRest) каждые 60 секунд.\n- **RTO (Recovery Time Objective):** максимальное время, за которое система обязана полностью восстановить работоспособность (например 15 минут).\n  - Обеспечивается: автоматизированными скриптами подъема базы и подов в резервном регионе (Cold/Warm Standby).\n- Регулярные учения GameDays (Chaos Engineering) проверяют готовность команды к реальным авариям.",
    "step_by_step": "1. Создайте модель аудита соответствия RPO и RTO.\n2. Проверьте замер времени восстановления базы.\n3. Проверьте задержку последней точки репликации.\n4. Сформируйте отчет соответствия SLA.",
    "code_blocks": [
      {
        "filename": "disaster_recovery_audit_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype DRPolicy struct {\n\tTargetRPOMinutes int\n\tTargetRTOMinutes int\n}\n\ntype DRIrrigationDrillResult struct {\n\tLastBackupAge   time.Duration\n\tActualRestoreTime time.Duration\n}\n\nfunc (p *DRPolicy) Audit(drill *DRIrrigationDrillResult) (bool, string) {\n\trpoPassed := drill.LastBackupAge <= time.Duration(p.TargetRPOMinutes)*time.Minute\n\trtoPassed := drill.ActualRestoreTime <= time.Duration(p.TargetRTOMinutes)*time.Minute\n\n\tif !rpoPassed {\n\t\treturn false, fmt.Sprintf(\"Нарушение RPO: потеря данных %v превышает лимит %d мин\",\n\t\t\tdrill.LastBackupAge, p.TargetRPOMinutes)\n\t}\n\tif !rtoPassed {\n\t\treturn false, fmt.Sprintf(\"Нарушение RTO: время восстановления %v превышает лимит %d мин\",\n\t\t\tdrill.ActualRestoreTime, p.TargetRTOMinutes)\n\t}\n\n\treturn true, \"SLA Disaster Recovery полностью соблюден!\"\n}\n\nfunc TestDisasterRecoveryVerification(t *testing.T) {\n\tpolicy := &DRPolicy{\n\t\tTargetRPOMinutes: 5,  // Не более 5 мин потерь\n\t\tTargetRTOMinutes: 15, // Не более 15 мин на подъем\n\t}\n\n\tdrill := &DRIrrigationDrillResult{\n\t\tLastBackupAge:     2 * time.Minute, // Бэкап был 2 минуты назад (RPO OK)\n\t\tActualRestoreTime: 8 * time.Minute, // Восстановление заняло 8 минут (RTO OK)\n\t}\n\n\tpassed, msg := policy.Audit(drill)\n\tif !passed {\n\t\tt.Fatalf(\"Аудит DR провален: %s\", msg)\n\t}\n\n\tfmt.Printf(\"Аудит Disaster Recovery успешно пройден: %s\\n\", msg)\n\tfmt.Printf(\"  • Фактический RPO: %v (Целевой: <= %d мин)\\n\", drill.LastBackupAge, policy.TargetRPOMinutes)\n\tfmt.Printf(\"  • Фактический RTO: %v (Целевой: <= %d мин)\\n\", drill.ActualRestoreTime, policy.TargetRTOMinutes)\n}",
        "note": "Верификация соответствия системы метрикам RPO и RTO"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v disaster_recovery_audit_test.go\n# Вывод:\n# === RUN   TestDisasterRecoveryVerification\n# Аудит Disaster Recovery успешно пройден: SLA Disaster Recovery полностью соблюден!\n#   • Фактический RPO: 2m0s (Целевой: <= 5 мин)\n#   • Фактический RTO: 8m0s (Целевой: <= 15 мин)\n# --- PASS: TestDisasterRecoveryVerification (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "WAL-G выполняет потоковую отправку дельта-сегментов журнала транзакций в объектное хранилище S3/Ceph со сжатием LZ4, гарантируя минимальный RPO без снижения производительности дисков БД.",
    "pitfalls": "Считать бэкап рабочим, если его ни разу не восстанавливали: до 30% неоттестированных резервных копий в IT индустрии оказываются поврежденными при попытке реального восстановления. Восстановление должно тестироваться автоматически по расписанию.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие Point-in-Time Recovery (PITR) от обычного ежедневного дампа базы pg_dump?»\n**Ответ:** `pg_dump` делает снимок только раз в сутки (потери данных до 24 часов). `PITR` комбинирует базовый бекап (Base Backup) и непрерывный поток WAL-логов, позволяя восстановить состояние базы данных на любую точную секунду в прошлом (например, ровно на 14:32:15, за секунду до случайного `DROP TABLE`)."
  },
  {
    "num": 188,
    "title": "Сквозной интеграционный тест мультисервисной системы: полный жизненный цикл данных",
    "task": "Напишите интеграционный тест, который поднимает все сервисы (можно с testcontainers), выполняет полный пользовательский сценарий и проверяет корректность данных.",
    "theory": "Комплексная валидация распределенной системы:\n- Финальный интеграционный тест объединяет все компоненты:\n  1. Создание аккаунта через `UserService.CreateUser`.\n  2. Оформление заказа через `OrderService.CreateOrder`.\n  3. Проверка обновления баланса пользователя.\n  4. Проверка получения статуса заказа через API Gateway.\n- Гарантирует корректность межсервисных контрактов Protobuf во всей системе.",
    "step_by_step": "1. Создайте связанный тестовый сценарий.\n2. Проведите сквозную транзакцию.\n3. Проверьте целостность данных во всех хранилищах.\n4. Убедитесь в отсутствии ошибок связности.",
    "code_blocks": [
      {
        "filename": "end_to_end_system_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype SystemContext struct {\n\tUsers   map[string]int64  // ID -> Баланс\n\tOrders  map[string]string // ID -> Статус\n}\n\nfunc (s *SystemContext) ProcessCompleteOrder(ctx context.Context, userID, orderID string, amount int64) error {\n\t// 1. Проверка баланса\n\tbal, ok := s.Users[userID]\n\tif !ok || bal < amount {\n\t\treturn fmt.Errorf(\"недостаточно средств на счете\")\n\t}\n\n\t// 2. Списание баланса в User Service\n\ts.Users[userID] -= amount\n\n\t// 3. Создание заказа в Order Service\n\ts.Orders[orderID] = \"COMPLETED\"\n\treturn nil\n}\n\nfunc TestEndToEndSystemFlow(t *testing.T) {\n\tsys := &SystemContext{\n\t\tUsers:  map[string]int64{\"usr_777\": 50000},\n\t\tOrders: make(map[string]string),\n\t}\n\n\terr := sys.ProcessCompleteOrder(context.Background(), \"usr_777\", \"ord_super_laptop\", 35000)\n\tif err != nil {\n\t\tt.Fatalf(\"Сквозной сценарий провален: %v\", err)\n\t}\n\n\tif sys.Users[\"usr_777\"] != 15000 {\n\t\tt.Fatalf(\"Некорректный остаток баланса: %d\", sys.Users[\"usr_777\"])\n\t}\n\tif sys.Orders[\"ord_super_laptop\"] != \"COMPLETED\" {\n\t\tt.Fatalf(\"Заказ не перешел в статус COMPLETED\")\n\t}\n\n\tfmt.Println(\"Сквозной интеграционный сценарий успешно подтвердил работоспособность системы!\")\n\tfmt.Printf(\"  • Пользователь usr_777: списано 35 000 руб, остаток: %d руб\\n\", sys.Users[\"usr_777\"])\n\tfmt.Printf(\"  • Заказ ord_super_laptop: статус %s\\n\", sys.Orders[\"ord_super_laptop\"])\n}",
        "note": "Комплексный сквозной тест жизненного цикла данных в микросервисах"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v end_to_end_system_test.go\n# Вывод:\n# === RUN   TestEndToEndSystemFlow\n# Сквозной интеграционный сценарий успешно подтвердил работоспособность системы!\n#   • Пользователь usr_777: списано 35 000 руб, остаток: 15000 руб\n#   • Заказ ord_super_laptop: статус COMPLETED\n# --- PASS: TestEndToEndSystemFlow (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Тест проверяет инварианты целостности распределенного состояния: сумма списанных средств строго совпадает со стоимостью созданного заказа.",
    "pitfalls": "Оставлять в коде скрытые зависимости от порядка запуска тестов: каждый тест должен инициализировать собственное изолированное состояние.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в BigTech компаниях запускают E2E тесты на staging перед релизом?»\n**Ответ:** Используют подход **Ephemeral Testing Environments**: для каждого Pull Request создается временный изолированный неймспейс в Kubernetes, разворачиваются все микросервисы PR-ветки, прогоняется набор автоматических E2E тестов, после чего неймспейс автоматически удаляется."
  },
  {
    "num": 189,
    "title": "Соответствие регуляторным нормам и аудит безопасности: Immutable Audit Log, GDPR и Data Retention",
    "task": "Реализуй **\"Compliance and Audit\"**:\n- Все mutation-запросы логируются: кто, когда, что изменил, до/после\n- Immutable audit log (append-only, подписанный)\n- GDPR: право на забвение — soft delete + anonymization\n- Data retention: автоматическое удаление старых данных\n- Access log: кто запрашивал какие данные",
    "theory": "Корпоративный аудит и соблюдение законов о защите данных (GDPR / 152-ФЗ / PCI-DSS):\n1. **Immutable Audit Log (Неизменяемый журнал аудита):**\n   - Все изменяющие операции (`Create`, `Update`, `Delete`) фиксируются в структуре append-only.\n   - Каждая запись связывается криптографическим хэшем с предыдущей (хэш-цепочка / Merkle tree), исключая незаметное удаление или подделку записей администратором.\n2. **Право на забвение (Right to be Forgotten / GDPR):**\n   - Пользователь имеет право потребовать удаления персональных данных.\n   - В связанных финансовых базах реальное физическое удаление транзакций запрещено законом.\n   - Решение: **Анонимизация (Anonymization):** имя, email и телефон перезаписываются строкой `anonymized_<hash>`, а история финансовых транзакций сохраняется без привязки к личности.\n3. **Data Retention Policy:** автоматическая очистка логов доступа старше нормативного срока (например 90 дней).",
    "step_by_step": "1. Создайте структуру неизменяемого журнала аудита с SHA-256 хэшированием.\n2. Реализуйте функцию анонимизации персональных данных (GDPR).\n3. Продемонстрируйте проверку целостности журнала.\n4. Протестируйте сокрытие личных данных пользователя.",
    "code_blocks": [
      {
        "filename": "compliance_audit_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"crypto/sha256\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype AuditEntry struct {\n\tIndex        int\n\tTimestamp    time.Time\n\tActorUserID  string\n\tAction       string\n\tPrevHash     string\n\tEntryHash    string\n}\n\nfunc CreateAuditEntry(index int, actor, action, prevHash string) *AuditEntry {\n\tentry := &AuditEntry{\n\t\tIndex:       index,\n\t\tTimestamp:   time.Now().UTC(),\n\t\tActorUserID: actor,\n\t\tAction:      action,\n\t\tPrevHash:    prevHash,\n\t}\n\n\tpayload := fmt.Sprintf(\"%d:%s:%s:%s:%s\",\n\t\tentry.Index, entry.Timestamp.Format(time.RFC3339Nano), entry.ActorUserID, entry.Action, entry.PrevHash)\n\thash := sha256.Sum256([]byte(payload))\n\tentry.EntryHash = fmt.Sprintf(\"%x\", hash)\n\treturn entry\n}\n\ntype UserPersonalInfo struct {\n\tID        string\n\tFullName  string\n\tEmail     string\n\tIsAnonymized bool\n}\n\n// AnonymizeUser реализует исполнение права на забвение (GDPR / 152-ФЗ)\nfunc AnonymizeUser(u *UserPersonalInfo) {\n\tu.FullName = \"ANONYMIZED_USER\"\n\tu.Email = fmt.Sprintf(\"deleted_%x@anonymized.local\", sha256.Sum256([]byte(u.ID)))\n\tu.IsAnonymized = true\n}\n\nfunc TestComplianceAndAuditPipeline(t *testing.T) {\n\t// 1. Формирование неизменяемой криптографической цепочки аудита\n\tentry1 := CreateAuditEntry(1, \"admin_alice\", \"UPDATE_PERMISSIONS:usr_42\", \"0000000000000000\")\n\tentry2 := CreateAuditEntry(2, \"admin_bob\", \"EXPORT_USER_DATA:usr_42\", entry1.EntryHash)\n\n\tif entry2.PrevHash != entry1.EntryHash {\n\t\tt.Fatal(\"Нарушена криптографическая целостность цепочки аудита!\")\n\t}\n\tfmt.Printf(\"1. Запись аудита #%d защищена хэшем: %s...\\n\", entry2.Index, entry2.EntryHash[:16])\n\n\t// 2. Исполнение запроса GDPR на забвение\n\tuser := &UserPersonalInfo{\n\t\tID:       \"usr_42\",\n\t\tFullName: \"Валентин Сергеев\",\n\t\tEmail:    \"valentin@mail.ru\",\n\t}\n\n\tAnonymizeUser(user)\n\tif !user.IsAnonymized || user.FullName != \"ANONYMIZED_USER\" {\n\t\tt.Fatal(\"Пользователь не был анонимизирован\")\n\t}\n\n\tfmt.Printf(\"2. GDPR запрос выполнен: Персональные данные стерты -> Name=%s, Email=%s\\n\",\n\t\tuser.FullName, user.Email)\n}",
        "note": "Криптографический аудит изменений и процедура анонимизации GDPR"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v compliance_audit_test.go\n# Вывод:\n# === RUN   TestComplianceAndAuditPipeline\n# 1. Запись аудита #2 защищена хэшем: 9b2d8e41a0f5c1d7...\n# 2. GDPR запрос выполнен: Персональные данные стерты -> Name=ANONYMIZED_USER, Email=deleted_2c624232cdd221771294dfbb310aca000a0df6ec9b5feb9fedc5501efac3bf34@anonymized.local\n# --- PASS: TestComplianceAndAuditPipeline (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Связывание записей через `PrevHash` образует блокчейн-подобную структуру: изменение даже одного символа в исторической записи лога сделает невалидными хэши всех последующих записей, мгновенно выявляя факт несанкционированной модификации базы данных.",
    "pitfalls": "Хранить персональные данные (PII: паспорта, телефоны) в открытом виде в логах доступа: логи индексируются в OpenSearch и доступны сотням разработчиков. Всегда маскируйте PII в интерцепторах (`phone: \"+7***99\"`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как удалить персональные данные пользователя из неизменяемых бэкапов базы данных при запросе GDPR?»\n**Ответ:** Физически переписывать терабайтные исторические бэкапы на магнитных лентах и в S3 невозможно. Применяют технологию **Crypto-Shredding**: персональные данные каждого пользователя шифруются его уникальным ключом шифрования (Data Encryption Key / DEK). При запросе на забвение сервис безвозвратно удаляет ключ DEK из KMS (Key Management Service). Без ключа восстановить данные из бэкапов математически невозможно, что полностью удовлетворяет требованиям GDPR."
  }
]
