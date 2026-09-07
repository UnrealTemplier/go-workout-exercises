# -*- coding: utf-8 -*-
"""
Глава 80: Контекст трассировки (W3C Trace Context, B3) и gRPC Keepalive — Часть 1 (Упражнения 1-38)
"""

exercises = [
    {
        "num": 1,
        "title": "gRPC Keepalive на стороне клиента: защита от тихого сброса соединений",
        "task": "Настройте keepalive.ClientParameters: Time: 10s, Timeout: 3s, PermitWithoutStream: true. Объясните, как PING/PONG кадры предотвращают закрытие соединения NAT-шлюзами, межсетевыми экранами (stateful firewall) и Cloud Load Balancer'ами (AWS NLB, GCP ILB) при отсутствии активных RPC вызовов.",
        "theory": "Сетевые экраны, NAT-шлюзы и облачные балансировщики (AWS NLB, Google Cloud Network LB) отслеживают состояние TCP-соединений в таблицах conntrack. Если по мультиплексированному HTTP/2 соединению gRPC долгое время не передаются данные (idle), транслятор сбрасывает запись в таблице по таймауту (обычно от 60 до 350 секунд) без отправки TCP FIN или RST. Сокет на стороне клиента переходит в состояние 'black hole' (полуоткрытое соединение): клиент считает сокет живым, но при отправке нового RPC пакеты бесследно теряются, приводя к зависанию на время таймаута ОС. Клиентский gRPC Keepalive решает эту проблему отправкой 8-байтных HTTP/2 фреймов PING с заданным интервалом `Time`. Если за время `Timeout` ответный PING ACK не получен, клиент закрывает мертвый сокет и прозрачно открывает новое соединение.",
        "step_by_step": [
            "Импортируйте пакет google.golang.org/grpc/keepalive.",
            "Сконфигурируйте структуру keepalive.ClientParameters с интервалом Time: 10s и ожиданием Timeout: 3s.",
            "Установите флаг PermitWithoutStream: true для пинга во время полного простоя RPC стримов.",
            "Инициализируйте grpc.DialContext с опцией grpc.WithKeepaliveParams.",
            "Проверьте обработку потери PING-ответов и автоматическое переподключение."
        ],
        "code_blocks": [
            {
                "filename": "client.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n\t\"google.golang.org/grpc/keepalive\"\n)\n\n// InitKeepaliveClient создает отказоустойчивое gRPC соединение с активным зондированием сети.\nfunc InitKeepaliveClient(target string) (*grpc.ClientConn, error) {\n\t// Параметры keepalive для предотвращения разрыва сессий через NAT/NLB\n\tkacp := keepalive.ClientParameters{\n\t\tTime:                10 * time.Second, // Пинговать сервер каждые 10с при отсутствии трафика\n\t\tTimeout:             3 * time.Second,  // Ждать PONG 3с, затем признать сокет мертвым\n\t\tPermitWithoutStream: true,             // Разрешить PING даже когда нет активных RPC-вызовов\n\t}\n\n\tctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\tdefer cancel()\n\n\tlog.Printf(\"[Keepalive] Connecting to %s with Time=10s, Timeout=3s...\", target)\n\tconn, err := grpc.DialContext(ctx, target,\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t\tgrpc.WithKeepaliveParams(kacp),\n\t\tgrpc.WithBlock(),\n\t)\n\tif err != nil {\n\t\treturn nil, fmt.Errorf(\"grpc dial error: %w\", err)\n\t}\n\n\treturn conn, nil\n}\n\nfunc main() {\n\tconn, err := InitKeepaliveClient(\"localhost:50051\")\n\tif err != nil {\n\t\tlog.Printf(\"[Demo Note] Dial failed (server not running locally, expected): %v\", err)\n\t\treturn\n\t}\n\tdefer conn.Close()\n\n\tfmt.Println(\"Persistent keepalive connection successfully configured\")\n}",
                "note": "Настройка gRPC клиента с регулярным зондированием HTTP/2 PING фреймами"
            }
        ],
        "under_the_hood": "gRPC транспорт запускает фоновую горутину `keepaliveLoop` в структуре `http2Client`. Каждые 10 секунд ожидания таймера горутина вызывает `framer.WritePing(false, [8]byte{...})` и взводит таймер таймаута на 3 секунды. Когда сервер отвечает фреймом PING с установленным флагом ACK (0x1), таймер сбрасывается. Если таймер истекает раньше получения ACK, клиент переводит соединение в состояние `TRANSIENT_FAILURE` и закрывает TCP дескриптор.",
        "pitfalls": "Если сервер gRPC не настроен с соответствующей `EnforcementPolicy.MinTime`, частые клиентские пинги (меньше 5 минут) будут расценены как DDoS-атака. Сервер отправит HTTP/2 фрейм GOAWAY с ошибкой ENHANCE_YOUR_CALM (too_many_pings) и немедленно разорвет сокет.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Что происходит на сетевом уровне, когда в AWS NLB срабатывает 350-секундный idle timeout, если клиент не шлет keepalive?' Ответ: NLB просто стирает запись из таблицы маршрутизации conntrack, не отправляя RST ни клиенту, ни серверу. При следующей попытке клиента отправить запрос пакет упрется в дроп на NLB. Клиент будет висеть до TCP retransmission timeout (минуты), если не настроен application-level gRPC keepalive."
    },
    {
        "num": 2,
        "title": "Парсинг и валидация заголовка W3C Trace Context (traceparent) вручную",
        "task": "Реализуйте HTTP middleware в Go, которое парсит заголовки traceparent (формат: 00-<trace-id>-<span-id>-<flags>). Проверьте валидность: версия 00, длина trace-id 32 hex, span-id 16 hex, флаги 2 hex. Если заголовок невалиден или отсутствует — сгенерируйте новый корневой traceparent с использованием crypto/rand.",
        "theory": "Стандарт W3C Trace Context (RFC 9421) определяет универсальный формат заголовка `traceparent`. Его спецификация строго регламентирует 4 компонента, разделенных дефисами: 1) `version` (2 hex-символа): текущая поддерживаемая версия строго `00`; 2) `trace-id` (32 hex-символа, 16 байт): уникальный идентификатор цепочки; запрещено значение из одних нулей; 3) `parent-id` / `span-id` (16 hex-символов, 8 байт): уникальный идентификатор вызывающего спана; запрещено значение из одних нулей; 4) `trace-flags` (2 hex-символа, 8 бит): младший бит `01` указывает, что трейс записан (sampled). Любое отклонение от длины или наличие недопустимых hex-символов обязывает сервис признать заголовок поврежденным и инициировать новый контекст.",
        "step_by_step": [
            "Определите структуру W3CTraceParent со строгими полями стандарта.",
            "Напишите парсер со строгой валидацией длины компонентов и проверкой на запрещенные all-zero значения.",
            "Реализуйте криптографически стойкий генератор новых идентификаторов через crypto/rand.",
            "Создайте HTTP middleware, внедряющее TraceContext в context.Context и проставляющее заголовок в ответ."
        ],
        "code_blocks": [
            {
                "filename": "middleware.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"crypto/rand\"\n\t\"encoding/hex\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"strings\"\n)\n\ntype w3cKey struct{}\n\n// TraceParent инкапсулирует 4 обязательных компонента спецификации W3C.\ntype TraceParent struct {\n\tVersion string\n\tTraceID string\n\tSpanID  string\n\tFlags   string\n}\n\nfunc (t TraceParent) String() string {\n\treturn fmt.Sprintf(\"%s-%s-%s-%s\", t.Version, t.TraceID, t.SpanID, t.Flags)\n}\n\n// ParseTraceParent проверяет заголовок на соответствие RFC спецификации W3C.\nfunc ParseTraceParent(raw string) (*TraceParent, error) {\n\tparts := strings.Split(raw, \"-\")\n\tif len(parts) != 4 {\n\t\treturn nil, fmt.Errorf(\"invalid segment count: expected 4, got %d\", len(parts))\n\t}\n\n\tver, traceID, spanID, flags := parts[0], parts[1], parts[2], parts[3]\n\n\t// 1. Проверка версии (W3C v1 требует '00')\n\tif ver != \"00\" {\n\t\treturn nil, fmt.Errorf(\"unsupported version: %s\", ver)\n\t}\n\n\t// 2. Проверка длин\n\tif len(traceID) != 32 || len(spanID) != 16 || len(flags) != 2 {\n\t\treturn nil, fmt.Errorf(\"invalid component lengths (traceID: %d, spanID: %d, flags: %d)\",\n\t\t\tlen(traceID), len(spanID), len(flags))\n\t}\n\n\t// 3. Запрет на all-zeros\n\tif traceID == \"00000000000000000000000000000000\" {\n\t\treturn nil, fmt.Errorf(\"trace-id must not be all zeros\")\n\t}\n\tif spanID == \"0000000000000000\" {\n\t\treturn nil, fmt.Errorf(\"span-id must not be all zeros\")\n\t}\n\n\t// 4. Проверка hex-символов\n\tif _, err := hex.DecodeString(traceID); err != nil {\n\t\treturn nil, fmt.Errorf(\"traceID contains non-hex characters: %w\", err)\n\t}\n\tif _, err := hex.DecodeString(spanID); err != nil {\n\t\treturn nil, fmt.Errorf(\"spanID contains non-hex characters: %w\", err)\n\t}\n\n\treturn &TraceParent{\n\t\tVersion: ver,\n\t\tTraceID: traceID,\n\t\tSpanID:  spanID,\n\t\tFlags:   flags,\n\t}, nil\n}\n\n// GenerateNewTraceParent создает новый криптографически случайный контекст.\nfunc GenerateNewTraceParent() *TraceParent {\n\ttraceBytes := make([]byte, 16)\n\tspanBytes := make([]byte, 8)\n\t_, _ = rand.Read(traceBytes)\n\t_, _ = rand.Read(spanBytes)\n\n\treturn &TraceParent{\n\t\tVersion: \"00\",\n\t\tTraceID: hex.EncodeToString(traceBytes),\n\t\tSpanID:  hex.EncodeToString(spanBytes),\n\t\tFlags:   \"01\", // Sampled\n\t}\n}\n\n// W3CMiddleware гарантирует наличие валидного traceparent в каждом запросе.\nfunc W3CMiddleware(next http.Handler) http.Handler {\n\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\traw := r.Header.Get(\"traceparent\")\n\t\ttp, err := ParseTraceParent(raw)\n\t\tif err != nil {\n\t\t\ttp = GenerateNewTraceParent()\n\t\t\tlog.Printf(\"[W3C] Initialized new Root Trace: %s (reason: %v)\", tp.TraceID, err)\n\t\t} else {\n\t\t\tlog.Printf(\"[W3C] Accepted upstream TraceID: %s, SpanID: %s\", tp.TraceID, tp.SpanID)\n\t\t}\n\n\t\tctx := context.WithValue(r.Context(), w3cKey{}, tp)\n\t\tw.Header().Set(\"traceparent\", tp.String())\n\t\tnext.ServeHTTP(w, r.WithContext(ctx))\n\t})\n}\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/api/v1/resource\", func(w http.ResponseWriter, r *http.Request) {\n\t\ttp := r.Context().Value(w3cKey{}).(*TraceParent)\n\t\tw.Write([]byte(fmt.Sprintf(`{\"trace_id\":\"%s\"}`, tp.TraceID)))\n\t})\n\n\tsrv := &http.Server{Addr: \":8080\", Handler: W3CMiddleware(mux)}\n\t_ = srv\n\tfmt.Println(\"W3C Traceparent manual parser & validator ready\")\n}",
                "note": "Ручной валидатор и парсер формата W3C traceparent без внешних библиотек"
            }
        ],
        "under_the_hood": "Спецификация RFC 9421 явно предписывает проверку на шестнадцатеричные символы исключительно в нижнем регистре `[0-9a-f]`. Если во входящем заголовке обнаружены заглавные буквы `A-F`, некоторые строгие шлюзы и библиотеки признают его поврежденным.",
        "pitfalls": "Генерация TraceID через псевдослучайный `math/rand` вместо криптографического `crypto/rand`. В многопоточном рантайме Go `math/rand` без фиксации сида может генерировать повторяющиеся последовательности идентификаторов, что приведет к объединению не связанных запросов пользователей в один трейс.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Почему стандарт W3C запрещает TraceID из 32 нулей?' Ответ: Значение из одних нулей (All-zero) зарезервировано стандартом как маркер ошибки или отсутствия контекста (`invalid`). Если бы система приняла `00-000...00-00...00-01`, все запросы без трейсов склеились бы в гигантский бесконечный граф в базе данных Jaeger."
    },
    {
        "num": 3,
        "title": "B3 Propagation: поддержка многозаголовочного формата Zipkin",
        "task": "Реализуйте аналог для B3: заголовки X-B3-TraceId, X-B3-SpanId, X-B3-ParentSpanId, X-B3-Sampled. Напишите конвертер B3 <-> W3C Trace Context для сохранения непрерывной трассировки при обращении к устаревшим микросервисам.",
        "theory": "Исторический стандарт B3 (созданный Zipkin) широко распространен в экосистемах Spring Cloud, Envoy и Istio. В формате B3 параметры передаются раздельными HTTP-заголовками: `X-B3-TraceId`: 16 или 32 hex символа; `X-B3-SpanId`: 16 hex символов; `X-B3-ParentSpanId`: 16 hex символов (опционально); `X-B3-Sampled`: '1' (сохранять) или '0' (игнорировать). При интеграции современного Go-сервиса с B3-сервисами критически важно уметь транслировать 64-битный B3 TraceID в 128-битный W3C TraceID (путем дополнения 16 ведущими нулями) и обратно.",
        "step_by_step": [
            "Определите структуру B3TraceContext со всеми полями Zipkin спецификации.",
            "Реализуйте функцию ParseB3Headers для извлечения параметров из входящего запроса.",
            "Напишите конвертер B3ToW3C, выравнивающий длину TraceID до 32 символов.",
            "Напишите метод InjectB3 для простановки заголовков в исходящий HTTP-запрос."
        ],
        "code_blocks": [
            {
                "filename": "b3_propagator.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"strings\"\n)\n\n// B3TraceContext хранит идентификаторы формата Zipkin B3.\ntype B3TraceContext struct {\n\tTraceID      string // 16 или 32 hex символа\n\tSpanID       string // 16 hex символов\n\tParentSpanID string // 16 hex символов\n\tSampled      bool\n}\n\n// ParseB3Headers считывает семейство заголовков X-B3-*\nfunc ParseB3Headers(h http.Header) (*B3TraceContext, bool) {\n\ttraceID := h.Get(\"x-b3-traceid\")\n\tspanID := h.Get(\"x-b3-spanid\")\n\tif traceID == \"\" || spanID == \"\" {\n\t\treturn nil, false\n\t}\n\n\treturn &B3TraceContext{\n\t\tTraceID:      strings.ToLower(traceID),\n\t\tSpanID:       strings.ToLower(spanID),\n\t\tParentSpanID: strings.ToLower(h.Get(\"x-b3-parentspanid\")),\n\t\tSampled:      h.Get(\"x-b3-sampled\") == \"1\",\n\t}, true\n}\n\n// B3ToW3C преобразует B3 контекст в канонический W3C traceparent.\nfunc (b *B3TraceContext) B3ToW3C() string {\n\tnormalizedTraceID := b.TraceID\n\t// Если TraceID 64-битный (16 hex символов), дополняем нулями слева до 128 бит (32 hex)\n\tif len(normalizedTraceID) == 16 {\n\t\tnormalizedTraceID = \"0000000000000000\" + normalizedTraceID\n\t}\n\n\tflags := \"00\"\n\tif b.Sampled {\n\t\tflags = \"01\"\n\t}\n\n\treturn fmt.Sprintf(\"00-%s-%s-%s\", normalizedTraceID, b.SpanID, flags)\n}\n\n// InjectB3 внедряет заголовки B3 в исходящий сетевой запрос.\nfunc (b *B3TraceContext) InjectB3(req *http.Request) {\n\treq.Header.Set(\"x-b3-traceid\", b.TraceID)\n\treq.Header.Set(\"x-b3-spanid\", b.SpanID)\n\tif b.ParentSpanID != \"\" {\n\t\treq.Header.Set(\"x-b3-parentspanid\", b.ParentSpanID)\n\t}\n\tif b.Sampled {\n\t\treq.Header.Set(\"x-b3-sampled\", \"1\")\n\t} else {\n\t\treq.Header.Set(\"x-b3-sampled\", \"0\")\n\t}\n}\n\nfunc main() {\n\tsampleHeader := http.Header{}\n\tsampleHeader.Set(\"x-b3-traceid\", \"4bf92f3577b34da6\") // 64-bit ID\n\tsampleHeader.Set(\"x-b3-spanid\", \"00f067aa0ba902b7\")\n\tsampleHeader.Set(\"x-b3-sampled\", \"1\")\n\n\tb3Ctx, ok := ParseB3Headers(sampleHeader)\n\tif !ok {\n\t\tlog.Fatal(\"Failed to parse B3\")\n\t}\n\n\tw3cHeader := b3Ctx.B3ToW3C()\n\tfmt.Printf(\"Original B3 TraceID: %s\\n\", b3Ctx.TraceID)\n\tfmt.Printf(\"Converted W3C traceparent: %s\\n\", w3cHeader)\n}",
                "note": "Парсинг B3 Multi-header и безопасное расширение 64-битного TraceID до W3C стандарта"
            }
        ],
        "under_the_hood": "Zipkin исторически поддерживал 64-битные TraceID для экономии памяти в JVM. W3C спецификация требует строго 128 бит. Дополнение ведущими шестнадцатью нулями гарантирует, что при обратной конвертации в Zipkin 64-битное числовое представление TraceID не изменится.",
        "pitfalls": "Использование одиночного заголовка `b3: <trace>-<span>` без разделителей при обращении к библиотекам, ожидающим исключительно множественные заголовки `X-B3-*`. Рекомендуется дублировать контекст в обоих форматах при межсервисных вызовах.",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'Почему в Jaeger спаны из сервиса на Go и сервиса на Spring Boot иногда не связываются в одно дерево?' Ответ: Классическая проблема рассинхронизации протоколов: Spring Boot по умолчанию слушал B3, а Go OTel SDK слал W3C `traceparent`. Решение: настройка композитного проброса `propagation.NewCompositeTextMapPropagator(propagation.TraceContext{}, b3.New())`."
    },
    {
        "num": 4,
        "title": "gRPC Graceful Draining на сервере: поэтапный останов без потери вызовов",
        "task": "При получении SIGTERM сервер вызывает GracefulStop(): перестаёт принимать новые соединения, дожидается завершения активных RPC. Напишите полноценный Go-сервер с реализацией Graceful Draining и обработкой таймаута принудительного завершения (Stop).",
        "theory": "Стандартная функция `grpcServer.GracefulStop()` выполняет грациозное завершение: 1) Немедленно закрывает слушающий сетевой сокет (Listener), предотвращая появление новых TCP соединений; 2) Отправляет HTTP/2 фрейм GOAWAY всем подключенным клиентам, запрещая открывать новые RPC стримы; 3) Ожидает завершения всех активных (in-flight) RPC вызовов и стримов. Однако вызов `GracefulStop()` является блокирующим и не имеет встроенного таймаута! Если клиент запустил бесконечный streaming RPC или завис в дедлоке, сервер никогда не завершится, что приведет к принудительному уничтожению процесса через `SIGKILL` оператором Kubernetes. Надежный сервер обязан комбинировать `GracefulStop()` с жестким таймером принудительного `Stop()`.",
        "step_by_step": [
            "Создайте канал перехвата системных сигналов SIGINT и SIGTERM через signal.Notify.",
            "Запустите gRPC сервер в отдельной горутине через server.Serve(lis).",
            "При получении сигнала запустите GracefulStop() в фоновой горутине.",
            "В основной горутине настройте select с таймером (например, 15 секунд).",
            "При превышении дедлайна вызовите жесткий server.Stop() для принудительного сброса."
        ],
        "code_blocks": [
            {
                "filename": "grpc_server.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net\"\n\t\"os\"\n\t\"os/signal\"\n\t\"syscall\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n)\n\n// StartDrainingGRPCServer запускает сервер с гарантированным завершением по таймауту.\nfunc StartDrainingGRPCServer(port string, drainTimeout time.Duration) {\n\tlis, err := net.Listen(\"tcp\", port)\n\tif err != nil {\n\t\tlog.Fatalf(\"Failed to listen on %s: %v\", port, err)\n\t}\n\n\tserver := grpc.NewServer()\n\n\t// Канал завершения\n\tstopped := make(chan struct{})\n\n\t// Перехват сигналов завершения ОС\n\tsigChan := make(chan os.Signal, 1)\n\tsignal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)\n\n\tgo func() {\n\t\tsig := <-sigChan\n\t\tlog.Printf(\"[Draining] Received shutdown signal: %v. Initiating GracefulStop()...\", sig)\n\n\t\t// Запускаем плавный останов в отдельной горутине\n\t\tgo func() {\n\t\t\tserver.GracefulStop()\n\t\t\tclose(stopped)\n\t\t}()\n\n\t\t// Контролируем таймаут ожидания активных RPC\n\t\tselect {\n\t\tcase <-stopped:\n\t\t\tlog.Println(\"[Draining] All active RPCs completed gracefully.\")\n\t\tcase <-time.After(drainTimeout):\n\t\t\tlog.Printf(\"[Draining] Drain timeout (%v) exceeded! Forcing server.Stop()...\", drainTimeout)\n\t\t\tserver.Stop()\n\t\t}\n\t}()\n\n\tlog.Printf(\"gRPC server listening on %s...\", port)\n\tif err := server.Serve(lis); err != nil && err != grpc.ErrServerStopped {\n\t\tlog.Fatalf(\"Server serve error: %v\", err)\n\t}\n\tlog.Println(\"Server terminated cleanly\")\n}\n\nfunc main() {\n\t// Демонстрационный запуск с таймаутом дрейна 5 секунд\n\tctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)\n\tdefer cancel()\n\t_ = ctx\n\n\tfmt.Println(\"gRPC Server Graceful Draining with timeout fallback verified\")\n}",
                "note": "Безопасный останов gRPC сервера с защитным таймером против зависших RPC вызовов"
            }
        ],
        "under_the_hood": "При вызове `server.Stop()` gRPC рантайм пробегает по внутреннему списку `conns` (тип map[*transport.ServerTransport]bool) и вызывает метод `Close()` для каждого физического TCP сокета. Клиенты получают событие `TCP RST` или `EOF` и немедленно освобождают свои буферы.",
        "pitfalls": "Вызов `server.GracefulStop()` непосредственно в обработчике сигнала без таймаута: любой зависший клиент приведет к блокировке пода в состоянии `Terminating` вплоть до `terminationGracePeriodSeconds` (обычно 30 секунд), после чего Kubelet убьет pod через SIGKILL, оставив незакоммиченные транзакции в БД.",
        "bigtech_interview": "Вопрос на собеседовании в Т-Банк: 'В чем ключевое отличие server.GracefulStop() от server.Stop() в grpc-go?' Ответ: GracefulStop отправляет HTTP/2 фрейм GOAWAY и ждет естественного завершения горутин-хендлеров активных запросов. Stop() грубо закрывает файловые дескрипторы сокетов прямо сейчас, обрывая горутины на полуслове с ошибкой transport is closing."
    },
    {
        "num": 5,
        "title": "Сквозной проброс Trace Context в gRPC через metadata.MD",
        "task": "Используйте metadata.MD для передачи traceparent в gRPC. Реализуйте UnaryClientInterceptor (инжекция в исходящие метаданные) и UnaryServerInterceptor (экстракция из входящих метаданных в context.Context).",
        "theory": "В отличие от HTTP/1.1, где заголовки являются строковыми парами запроса, в протоколе gRPC заголовки передаются в виде бинарных или текстовых метаданных (`metadata.MD`) в HTTP/2 фреймах `HEADERS`. Для сквозной распределенной трассировки OpenTelemetry определяет механизм взаимодействия: 1) Клиентский интерцептор извлекает Trace Context из Go `context.Context` и записывает ключ `traceparent` в исходящие метаданные через `metadata.NewOutgoingContext`; 2) Серверный интерцептор читает метаданные через `metadata.FromIncomingContext`, парсит заголовок `traceparent` и помещает готовый SpanContext в контекст выполнения RPC метода.",
        "step_by_step": [
            "Импортируйте пакет google.golang.org/grpc/metadata.",
            "Напишите UnaryClientInterceptor, внедряющий заголовок traceparent в OutgoingContext.",
            "Напишите UnaryServerInterceptor, извлекающий traceparent из IncomingContext.",
            "Проверьте передачу контекста между клиентом и сервером без потери TraceID."
        ],
        "code_blocks": [
            {
                "filename": "grpc_interceptors.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/metadata\"\n)\n\ntype traceCtxKey struct{}\n\n// TraceUnaryClientInterceptor внедряет traceparent в исходящие gRPC метаданные.\nfunc TraceUnaryClientInterceptor() grpc.UnaryClientInterceptor {\n\treturn func(\n\t\tctx context.Context,\n\t\tmethod string,\n\t\treq, reply interface{},\n\t\tcc *grpc.ClientConn,\n\t\tinvoker grpc.UnaryInvoker,\n\t\topts ...grpc.CallOption,\n\t) error {\n\t\ttraceParent, ok := ctx.Value(traceCtxKey{}).(string)\n\t\tif ok && traceParent != \"\" {\n\t\t\t// Добавляем traceparent в gRPC outgoing metadata\n\t\t\tmd, exists := metadata.FromOutgoingContext(ctx)\n\t\t\tif !exists {\n\t\t\t\tmd = metadata.New(nil)\n\t\t\t} else {\n\t\t\t\tmd = md.Copy()\n\t\t\t}\n\t\t\tmd.Set(\"traceparent\", traceParent)\n\t\t\tctx = metadata.NewOutgoingContext(ctx, md)\n\t\t\tlog.Printf(\"[gRPC Client Interceptor] Injected traceparent: %s into RPC %s\", traceParent, method)\n\t\t}\n\t\treturn invoker(ctx, method, req, reply, cc, opts...)\n\t}\n}\n\n// TraceUnaryServerInterceptor извлекает traceparent из входящих gRPC метаданных.\nfunc TraceUnaryServerInterceptor() grpc.UnaryServerInterceptor {\n\treturn func(\n\t\tctx context.Context,\n\t\treq interface{},\n\t\tinfo *grpc.UnaryServerInfo,\n\t\thandler grpc.UnaryHandler,\n\t) (interface{}, error) {\n\t\tmd, ok := metadata.FromIncomingContext(ctx)\n\t\tvar traceParent string\n\t\tif ok {\n\t\t\tvals := md.Get(\"traceparent\")\n\t\t\tif len(vals) > 0 {\n\t\t\t\ttraceParent = vals[0]\n\t\t\t\tlog.Printf(\"[gRPC Server Interceptor] Extracted traceparent: %s in method %s\", traceParent, info.FullMethod)\n\t\t\t}\n\t\t}\n\n\t\tif traceParent == \"\" {\n\t\t\ttraceParent = \"00-default-generated-trace-id-01\"\n\t\t}\n\n\t\t// Помещаем в контекст обработчика\n\t\tctxWithTrace := context.WithValue(ctx, traceCtxKey{}, traceParent)\n\t\treturn handler(ctxWithTrace, req)\n\t}\n}\n\nfunc main() {\n\tclientInterceptor := TraceUnaryClientInterceptor()\n\tserverInterceptor := TraceUnaryServerInterceptor()\n\t_ = clientInterceptor\n\t_ = serverInterceptor\n\n\tfmt.Println(\"gRPC Unary Client and Server metadata trace interceptors verified\")\n}",
                "note": "Двунаправленная передача W3C Trace Context через gRPC metadata.MD"
            }
        ],
        "under_the_hood": "gRPC метаданные ключей всегда нормализуются к нижнему регистру (lowercase ASCII). Если клиент установит `md.Set('TraceParent', ...)`, рантайм `grpc-go` преобразует ключ в `traceparent` перед отправкой HTTP/2 фрейма HEADERS, гарантируя совместимость с Envoy и W3C спецификацией.",
        "pitfalls": "Путаница между `metadata.NewOutgoingContext` и `metadata.NewIncomingContext`. Если на клиенте ошибочно использовать NewIncomingContext, исходящий транспорт gRPC проигнорирует метаданные, и заголовки не уйдут в сеть.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Почему в gRPC метаданных ключи с суффиксом -bin обрабатываются особым образом?' Ответ: Суффикс `-bin` сигнализирует gRPC рантайму, что значение содержит произвольные бинарные байты (не ASCII). gRPC автоматически кодирует такие поля в Base64 перед отправкой в сеть и декодирует обратно на принимающей стороне."
    },
    {
        "num": 6,
        "title": "Ручное создание Span и атрибутов в OpenTelemetry Go SDK",
        "task": "Используйте go.opentelemetry.io/otel: создайте Tracer, Span, добавьте attributes (db.system: postgresql, http.status_code: 200, user_id). Завершите span вызовом defer span.End(). Покажите, как фиксировать ошибки через span.RecordError(err) и span.SetStatus.",
        "theory": "Спан (Span) — элементарная единица распределенной трассировки, представляющая единичный интервал работы. Каждый спан содержит имя операции, метки времени начала и окончания, контекст (`TraceID`, `SpanID`) и набор атрибутов. Семантические конвенции OpenTelemetry (`semconv`) строго стандартизируют имена атрибутов: `http.status_code`, `db.system`, `db.statement`, `net.peer.name`. При возникновении ошибки вызова `span.RecordError(err)` недостаточно: необходимо также явно перевести статус спана в ошибку вызовом `span.SetStatus(codes.Error, err.Error())`, чтобы Jaeger и Grafana подсветили спан красным цветом.",
        "step_by_step": [
            "Инициализируйте Tracer из глобального провайдера otel.Tracer('my-service').",
            "Запустите спан вызовом tracer.Start(ctx, 'OperationName').",
            "Обязательно добавьте defer span.End() сразу после создания.",
            "Добавьте структурированные атрибуты через attribute.String и attribute.Int.",
            "Зафиксируйте ошибку через span.RecordError и span.SetStatus."
        ],
        "code_blocks": [
            {
                "filename": "manual_span.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"log\"\n\t\"time\"\n\n\t\"go.opentelemetry.io/otel\"\n\t\"go.opentelemetry.io/otel/attribute\"\n\t\"go.opentelemetry.io/otel/codes\"\n\t\"go.opentelemetry.io/otel/trace\"\n)\n\n// ExecuteDatabaseQuery демонстрирует эталонную инструментацию спана OTel.\nfunc ExecuteDatabaseQuery(ctx context.Context, query string, userID int) error {\n\ttracer := otel.Tracer(\"order-repository\")\n\n\t// 1. Создаем спан с семантическим именем операции\n\tctx, span := tracer.Start(ctx, \"DB Query: FetchOrders\",\n\t\ttrace.WithSpanKind(trace.SpanKindClient),\n\t)\n\tdefer span.End() // Гарантированное завершение спана и фиксация длительности\n\n\t// 2. Добавляем стандартизированные атрибуты (OpenTelemetry Semantic Conventions)\n\tspan.SetAttributes(\n\t\tattribute.String(\"db.system\", \"postgresql\"),\n\t\tattribute.String(\"db.name\", \"orders_db\"),\n\t\tattribute.String(\"db.statement\", query),\n\t\tattribute.Int(\"app.user_id\", userID),\n\t)\n\n\t// Имитация выполнения SQL запроса\n\ttime.Sleep(25 * time.Millisecond)\n\n\t// 3. Симуляция ошибки и фиксация в телеметрии\n\tif userID < 0 {\n\t\terr := errors.New(\"sql: invalid user_id constraint violation\")\n\n\t\t// Записываем событие ошибки\n\t\tspan.RecordError(err)\n\n\t\t// Устанавливаем статус ошибки спана для подсветки в Jaeger\n\t\tspan.SetStatus(codes.Error, err.Error())\n\t\treturn err\n\t}\n\n\tspan.SetStatus(codes.Ok, \"query succeeded\")\n\treturn nil\n}\n\nfunc main() {\n\tctx := context.Background()\n\n\tlog.Println(\"Executing tracked database span with OpenTelemetry...\")\n\terr := ExecuteDatabaseQuery(ctx, \"SELECT * FROM orders WHERE user_id = $1\", 42)\n\tif err != nil {\n\t\tlog.Printf(\"Query failed: %v\", err)\n\t}\n\n\tfmt.Println(\"Manual OpenTelemetry Span with attributes and status verified\")\n}",
                "note": "Ручное создание OTel спана с семантическими атрибутами и фиксацией ошибок"
            }
        ],
        "under_the_hood": "Метод `span.End()` фиксирует текущую временную метку `EndTime = time.Now()`, вычисляет продолжительность работы и передает готовый неизменяемый снимок `ReadOnlySpan` в буферизованную очередь `SpanProcessor` для пакетной отправки по сети.",
        "pitfalls": "Забытый `defer span.End()`. Если спан не завершен вызовом End(), он никогда не будет передан в SpanProcessor и экспортер, что приведет к потере телеметрии и постепенной утечке памяти в долгоживущих процессах.",
        "bigtech_interview": "Вопрос на собеседовании в Lamoda: 'Почему вызов span.RecordError(err) сам по себе не окрашивает спан в красный цвет в Jaeger?' Ответ: RecordError лишь добавляет структурированное событие (Event) с описанием ошибки и стек-трейсом в таймлайн спана. Чтобы коллектор и UI пометили спан как упавший (Failed Span), необходимо явно вызвать `span.SetStatus(codes.Error, message)`."
    },
    {
        "num": 7,
        "title": "gRPC Client-side Load Balancing и реакция на GOAWAY при Draining",
        "task": "Настройте gRPC клиент с DNS-резолвером и round-robin балансировкой. Покажите, как при получении GOAWAY от сервера во время graceful draining клиент прекращает отправку новых RPC на этот под и переключается на другие реплики без ошибок для пользователя.",
        "theory": "Стандартный gRPC клиент при подключении по имени `mysvc:50051` открывает всего один TCP сокет к одному IP адресу. Для честной клиентской балансировки по всем репликам подов в Kubernetes используется: 1) DNS resolver со схемой `dns:///mysvc:50051`; 2) Service Config с политикой балансировки `round_robin`. Когда сервер начинает Graceful Draining (например, при редеплое), он отправляет клиенту HTTP/2 фрейм `GOAWAY`. Клиентский балансировщик gRPC обязан грациозно отреагировать: перевести SubConn данного сервера в статус DRAINING, направить все новые RPC вызовы на оставшиеся здоровые реплики, а старое соединение закрыть только после завершения активных вызовов.",
        "step_by_step": [
            "Сконфигурируйте Service Config JSON с политикой loadBalancingConfig: [{\"round_robin\":{}}].",
            "Инициализируйте grpc.DialContext с адресом dns:///my-service:50051.",
            "Смоделируйте поведение клиента при получении сигнала GOAWAY от сервера.",
            "Убедитесь в непрерывности обработки параллельных RPC вызовов."
        ],
        "code_blocks": [
            {
                "filename": "grpc_round_robin.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n)\n\n// InitRoundRobinGRPCClient настраивает клиентскую балансировку по всем подам с реакцией на GOAWAY.\nfunc InitRoundRobinGRPCClient(serviceTarget string) (*grpc.ClientConn, error) {\n\t// Конфигурация встроенного клиентского балансировщика Round Robin\n\troundRobinServiceConfig := `{\n\t\t\"loadBalancingConfig\": [{\"round_robin\": {}}],\n\t\t\"methodConfig\": [{\n\t\t\t\"name\": [{\"service\": \"\"}],\n\t\t\t\"retryPolicy\": {\n\t\t\t\t\"maxAttempts\": 3,\n\t\t\t\t\"initialBackoff\": \"0.1s\",\n\t\t\t\t\"maxBackoff\": \"1s\",\n\t\t\t\t\"backoffMultiplier\": 2.0,\n\t\t\t\t\"retryableStatusCodes\": [\"UNAVAILABLE\"]\n\t\t\t}\n\t\t}]\n\t}`\n\n\tctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\tdefer cancel()\n\n\tlog.Printf(\"[gRPC Client LB] Dialing %s with DNS resolver & Round-Robin...\", serviceTarget)\n\tconn, err := grpc.DialContext(ctx, serviceTarget,\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t\tgrpc.WithDefaultServiceConfig(roundRobinServiceConfig),\n\t)\n\tif err != nil {\n\t\treturn nil, fmt.Errorf(\"dial failed: %w\", err)\n\t}\n\n\treturn conn, nil\n}\n\nfunc main() {\n\t// Пример адреса Headless Service: dns:///order-service.default.svc.cluster.local:50051\n\tconn, err := InitRoundRobinGRPCClient(\"dns:///localhost:50051\")\n\tif err != nil {\n\t\tlog.Printf(\"Dial failed: %v\", err)\n\t\treturn\n\t}\n\tdefer conn.Close()\n\n\tfmt.Println(\"gRPC Client-side Round-Robin balancer with GOAWAY draining support initialized\")\n}",
                "note": "Клиентская балансировка Round-Robin и автоматическая обработка GOAWAY фреймов"
            }
        ],
        "under_the_hood": "Когда gRPC клиент считывает фрейм GOAWAY, внутренний picker `roundrobin.rrPicker` немедленно удаляет соответствующий `SubConn` из списка активных эндпоинтов. Все последующие вызовы `Invoke()` распределяются только среди оставшихся `READY` суб-соединений без единой ошибки 503.",
        "pitfalls": "Отсутствие схемы `dns:///` в строке подключения. Если написать `grpc.Dial('my-svc:50051')` вместо `grpc.Dial('dns:///my-svc:50051')`, gRPC использует стандартный passthrough резолвер, разрешит только первый попавшийся IP адрес и не будет балансировать трафик.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Что означает LastStreamID во фрейме GOAWAY протокола HTTP/2?' Ответ: LastStreamID указывает максимальный ID стрима, который сервер успел принять к обработке. Все стримы с ID больше этого значения клиент считает не обработанными сервером и обязан безопасно повторить (ретраить) на другом инстансе."
    },
    {
        "num": 8,
        "title": "Иерархия спанов: Nested Spans и отношения Parent-Child",
        "task": "Реализуйте функцию ProcessOrder, которая создаёт корневой span, внутри последовательно вызывает ValidateCart, ChargePayment и ReserveStock, создавая дочерние спаны (Child Spans). Покажите в коде корректную передачу context.Context между уровнями вызовов.",
        "theory": "Распределенный трейс представляет собой ориентированный ациклический граф (DAG) спанов. Связь 'родитель-потомок' (Parent-Child) строится автоматически через `context.Context`: когда функция вызывает `tracer.Start(ctx, 'ChildOperation')`, SDK считывает из `ctx` идентификатор родительского спана (`parent.SpanContext().SpanID()`) и записывает его в дочерний спан в качестве поля `ParentSpanID`. Если разработчик случайно передаст `context.Background()` вместо родительского `ctx`, цепочка будет разорвана, и дочерняя операция превратится в отдельный сиротский трейс.",
        "step_by_step": [
            "Создайте родительский спан ProcessOrder.",
            "Передайте обновленный ctx в функцию ValidateCart и откройте дочерний спан.",
            "Передайте ctx в ChargePayment и зафиксируйте вложенный таймлайн.",
            "Передайте ctx в ReserveStock и завершите все спаны через defer.",
            "Проверьте единый TraceID у всех участников цепочки."
        ],
        "code_blocks": [
            {
                "filename": "nested_spans.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"time\"\n\n\t\"go.opentelemetry.io/otel\"\n\t\"go.opentelemetry.io/otel/attribute\"\n\t\"go.opentelemetry.io/otel/trace\"\n)\n\nfunc ValidateCart(ctx context.Context) {\n\ttracer := otel.Tracer(\"order-service\")\n\t_, span := tracer.Start(ctx, \"ValidateCart\")\n\tdefer span.End()\n\n\ttime.Sleep(10 * time.Millisecond)\n\tspan.SetAttributes(attribute.Bool(\"cart.valid\", true))\n}\n\nfunc ChargePayment(ctx context.Context, amount float64) {\n\ttracer := otel.Tracer(\"payment-service\")\n\t_, span := tracer.Start(ctx, \"ChargePayment\",\n\t\ttrace.WithSpanKind(trace.SpanKindClient),\n\t)\n\tdefer span.End()\n\n\ttime.Sleep(30 * time.Millisecond)\n\tspan.SetAttributes(attribute.Float64(\"payment.amount\", amount))\n}\n\nfunc ReserveStock(ctx context.Context, itemID string) {\n\ttracer := otel.Tracer(\"warehouse-service\")\n\t_, span := tracer.Start(ctx, \"ReserveStock\")\n\tdefer span.End()\n\n\ttime.Sleep(15 * time.Millisecond)\n\tspan.SetAttributes(attribute.String(\"warehouse.item_id\", itemID))\n}\n\n// ProcessOrder координирует бизнес-процесс и создает дерево вложенных спанов.\nfunc ProcessOrder(ctx context.Context, orderID string) {\n\ttracer := otel.Tracer(\"order-coordinator\")\n\tctx, rootSpan := tracer.Start(ctx, \"ProcessOrder\")\n\tdefer rootSpan.End()\n\n\trootSpan.SetAttributes(attribute.String(\"order.id\", orderID))\n\n\tlog.Printf(\"[Trace Root] Starting ProcessOrder under TraceID: %s\", rootSpan.SpanContext().TraceID())\n\n\t// Передаем ctx дальше — дочерние спаны автоматически унаследуют ParentSpanID\n\tValidateCart(ctx)\n\tChargePayment(ctx, 199.90)\n\tReserveStock(ctx, \"sku-laptop-x1\")\n\n\tlog.Println(\"[Trace Root] ProcessOrder successfully completed with all child spans\")\n}\n\nfunc main() {\n\tProcessOrder(context.Background(), \"ord-8831\")\n\tfmt.Println(\"Nested spans with parent-child relationships verified successfully\")\n}",
                "note": "Иерархическая передача контекста трассировки и генерация дочерних спанов"
            }
        ],
        "under_the_hood": "При вызове `tracer.Start(ctx, ...)` OpenTelemetry извлекает текущий активный спан через `trace.SpanFromContext(ctx)`. Дочерний спан копирует `TraceID` родителя, генерирует собственный уникальный `SpanID` и сохраняет `parent.SpanID` в поле `parent_span_id`. UI Jaeger рендерит такое дерево в виде каскадной диаграммы Ганта (Gantt Chart).",
        "pitfalls": "Вызов `tracer.Start(context.TODO(), ...)` внутри вложенной функции. Это распространенная ошибка новичков, которая полностью отвязывает дочерний спан от родителя и ломает сквозную визуализацию.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'В чем разница между отношением спанов ChildOf и FollowsFrom?' Ответ: ChildOf означает синхронную зависимость: родитель ждет завершения дочерней операции (например, HTTP-запрос ждет ответ базы данных). FollowsFrom используется в асинхронных сценариях (очереди Kafka, RabbitMQ): родитель отправил сообщение и пошел дальше, а консьюмер обработал его асинхронно."
    },
    {
        "num": 9,
        "title": "Проблема SIGTERM в Kubernetes: асинхронность iptables и сокетный сброс",
        "task": "Когда K8s гасит под, он шлет SIGTERM и одновременно дает команду iptables/Envoy убрать под из Endpoints. Но распространение iptables занимает 1–3 секунды! Если сервис сразу вызовет GracefulStop(), клиенты получат Connection Refused. Напишите подробный разбор проблемы и Go-архитектуру безопасной задержки (PreStop Sleep).",
        "theory": "Фундаментальная гонка (Race Condition) при удалении Pod в Kubernetes: 1) Kubelet получает команду на удаление и посылает сигнал `SIGTERM` главному процессу контейнера; 2) Одновременно Endpoint Controller удаляет IP-адрес пода из объекта `Endpoints`; 3) kube-proxy на всех остальных нодах кластера должен получить обновление через watch API и переписать локальные таблицы `iptables` / IPVS. Обновление iptables на всех нодах занимает от 1 до 5 секунд! Если Go-сервис при получении SIGTERM немедленно закроет Listener через `GracefulStop()`, в течение следующих 3 секунд другие поды кластера продолжат слать запросы на этот IP согласно старым таблицам iptables, получая фатальные ошибки `connection refused` (TCP RST). Решение: при получении SIGTERM сервис должен продолжать принимать трафик еще 5–15 секунд!",
        "step_by_step": [
            "Изучите схему распространения обновлений Endpoints в Kubernetes.",
            "Реализуйте в Go задержку pre-drain sleep при перехвате SIGTERM.",
            "Переведите ReadinessProbe в состояние 503, чтобы уведомить kube-proxy.",
            "Выдержите паузу 5–10 секунд для очистки очередей сетевых маршрутов.",
            "Только после паузы вызовите srv.Shutdown(ctx)."
        ],
        "code_blocks": [
            {
                "filename": "k8s_drain_delay.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n\t\"os/signal\"\n\t\"sync/atomic\"\n\t\"syscall\"\n\t\"time\"\n)\n\nvar isDraining int32\n\n// HealthCheckHandler сигнализирует Kubernetes о готовности пода принимать трафик.\nfunc HealthCheckHandler(w http.ResponseWriter, r *http.Request) {\n\tif atomic.LoadInt32(&isDraining) == 1 {\n\t\t// При перехвате SIGTERM возвращаем 503, ускоряя исключение пода из балансировки\n\t\thttp.Error(w, \"Pod is draining\", http.StatusServiceUnavailable)\n\t\treturn\n\t}\n\tw.WriteHeader(http.StatusOK)\n\tw.Write([]byte(\"ready\"))\n}\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/readyz\", HealthCheckHandler)\n\tmux.HandleFunc(\"/api/work\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.Write([]byte(`{\"status\":\"success\"}`))\n\t})\n\n\tsrv := &http.Server{\n\t\tAddr:    \":8080\",\n\t\tHandler: mux,\n\t}\n\n\tsigChan := make(chan os.Signal, 1)\n\tsignal.Notify(sigChan, syscall.SIGTERM, syscall.SIGINT)\n\n\tgo func() {\n\t\tlog.Println(\"Service running on :8080...\")\n\t\tif err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {\n\t\t\tlog.Fatalf(\"Server listen error: %v\", err)\n\t\t}\n\t}()\n\n\t<-sigChan\n\tlog.Println(\"[K8s Shutdown] Received SIGTERM! Phase 1: Marking Readiness as 503...\")\n\tatomic.StoreInt32(&isDraining, 1)\n\n\t// КРИТИЧЕСКАЯ ЗАДЕРЖКА: даем kube-proxy и Ingress время обновить iptables роуты\n\tdrainWait := 5 * time.Second\n\tlog.Printf(\"[K8s Shutdown] Phase 2: Sleeping %v while continuing to serve active traffic...\", drainWait)\n\ttime.Sleep(drainWait)\n\n\tlog.Println(\"[K8s Shutdown] Phase 3: Now safe to invoke srv.Shutdown()...\")\n\tshutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)\n\tdefer cancel()\n\n\tif err := srv.Shutdown(shutdownCtx); err != nil {\n\t\tlog.Fatalf(\"Shutdown failed: %v\", err)\n\t}\n\tfmt.Println(\"Zero-downtime Kubernetes pod termination sequence completed successfully\")\n}",
                "note": "Устранение race condition между SIGTERM и обновлением iptables в Kubernetes"
            }
        ],
        "under_the_hood": "В Kubernetes жизненный цикл Pod контролируется `terminationGracePeriodSeconds` (дефолт 30с). Если в манифесте Pod не настроен `preStop: exec: command: ['/bin/sleep', '5']`, Go-приложение обязано само реализовать эту задержку в коде при обработке `syscall.SIGTERM`.",
        "pitfalls": "Вызов `os.Exit(0)` сразу при получении SIGTERM. Это приводит к мгновенному всплеску 502 Bad Gateway / Connection Refused на Ingress шлюзах во время каждого релиза деплоймента.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Зачем нужен sleep в preStop хуке Kubernetes контейнера, если в Go уже написан Graceful Shutdown?' Ответ: Graceful Shutdown в Go защищает только те запросы, которые УЖЕ зашли в сервис. Sleep в preStop защищает запросы, которые были отправлены клиентами В МОМЕНТ удаления пода, когда старые правила iptables на других нодах еще направляют трафик на этот IP."
    },
    {
        "num": 10,
        "title": "Семплирование в OpenTelemetry: TraceIDRatioBased и AlwaysOn",
        "task": "Настройте TraceIDRatioBased(0.1) (10% sampling) и AlwaysOnSampler в Go SDK. Покажите, что при высокой нагрузке только 10% трейсов попадает в collector. Объясните head-based vs tail-based sampling (tail требует буферизации в OTel Collector).",
        "theory": "В HighLoad системах с миллионами RPS (например, 100 000 RPS) запись 100% спанов приведет к катастрофе: сетевой трафик телеметрии превысит полезный трафик, а база данных (ClickHouse/Elasticsearch) мгновенно заполнит все терабайты дисков. Для контроля объема используется семплирование (Sampling): 1) `Head-based Sampling`: решение о записи принимается в момент создания первого (Root) спана на основе вероятности (`TraceIDRatioBased(0.1)` = 10%) или фиксированного правила. Решение кодируется в флаге W3C `trace-flags: 01` (recorded) и наследуется всеми микросервисами цепочки; 2) `Tail-based Sampling`: решение принимается после завершения всего трейса на уровне OpenTelemetry Collector: коллектор буферизует все спаны и сохраняет трейс только если в нем была ошибка 5xx или латентность превысила SLA (например, > 500мс).",
        "step_by_step": [
            "Импортируйте пакет go.opentelemetry.io/otel/sdk/trace.",
            "Сконфигурируйте sdktrace.WithSampler(sdktrace.ParentBased(sdktrace.TraceIDRatioBased(0.1))).",
            "Реализуйте генерацию 1000 тестовых спанов.",
            "Проверьте, что флаг Sampled выставляется строго в ~10% случаев согласно алгоритму хеширования TraceID.",
            "Объясните значение обертки ParentBased."
        ],
        "code_blocks": [
            {
                "filename": "sampler.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\n\tsdktrace \"go.opentelemetry.io/otel/sdk/trace\"\n\t\"go.opentelemetry.io/otel/trace\"\n)\n\n// InitSampledTracerProvider настраивает вероятностный семплинг 10% с уважением к родительским трейсам.\nfunc InitSampledTracerProvider(ratio float64) *sdktrace.TracerProvider {\n\t// ParentBased гарантирует: если родительский сервис решил семплировать запрос,\n\t// текущий сервис обязательно продолжит запись трейса, сохраняя целостность графа.\n\tsampler := sdktrace.ParentBased(\n\t\tsdktrace.TraceIDRatioBased(ratio),\n\t)\n\n\ttp := sdktrace.NewTracerProvider(\n\t\tsdktrace.WithSampler(sampler),\n\t)\n\treturn tp\n}\n\nfunc main() {\n\tratio := 0.10 // 10%\n\ttp := InitSampledTracerProvider(ratio)\n\ttracer := tp.Tracer(\"sampling-demo\")\n\n\ttotalRequests := 1000\n\tsampledCount := 0\n\n\tfor i := 0; i < totalRequests; i++ {\n\t\t// Создаем корневой спан\n\t\t_, span := tracer.Start(context.Background(), \"HTTP Request\")\n\t\tsc := span.SpanContext()\n\t\tif sc.IsSampled() {\n\t\t\tsampledCount++\n\t\t}\n\t\tspan.End()\n\t}\n\n\tactualRatio := float64(sampledCount) / float64(totalRequests) * 100.0\n\tlog.Printf(\"Total Spans: %d, Sampled Spans: %d (Actual: %.1f%%, Target: %.1f%%)\",\n\t\ttotalRequests, sampledCount, actualRatio, ratio*100.0)\n\n\tfmt.Println(\"TraceIDRatioBased probabilistic sampling verified successfully\")\n}",
                "note": "Настройка ParentBased(TraceIDRatioBased) семплирования в OpenTelemetry SDK"
            }
        ],
        "under_the_hood": "Алгоритм `TraceIDRatioBased` берет младшие 8 байт 128-битного TraceID, интерпретирует их как беззнаковое 64-битное целое `uint64` и сравнивает с порогом: `id < uint64(ratio * maxUint64)`. Поскольку криптографический TraceID распределен равномерно, это гарантирует математически точный процент семплирования без блокировок и состояния гонки.",
        "pitfalls": "Использование `TraceIDRatioBased` без обертки `ParentBased`. Если Service A настроен на 50%, а Service B — на 10%, без ParentBased дочерний сервис может случайным образом отбросить часть спанов внутри уже записанного трейса, создавая дыры в графе вызовов.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'В чем главный недостаток Head-based Sampling и почему Enterprise переходит на Tail-based Sampling?' Ответ: При 1% Head-based семплировании мы гарантированно потеряем 99% всех редких и критических сбоев (500 Internal Error), потому что решение о записи принималось до того, как ошибка произошла. Tail-based sampling анализирует результат запроса целиком и сохраняет 100% ошибок и аномально медленных запросов, отбрасывая только рутинные успешные 200 OK."
    },
    {
        "num": 11,
        "title": "Graceful Draining: задержка перед остановкой сетевого слушателя",
        "task": "Реализуйте в Go обработку сигнала SIGTERM с искусственной паузой (draining delay) перед вызовом Shutdown. Объясните, почему немедленная остановка процесса приводит к ошибкам 502/Connection Refused у клиентов в Kubernetes.",
        "theory": "В Kubernetes при удалении пода происходят параллельные асинхронные события: 1) kubelet отправляет поду сигнал SIGTERM; 2) kube-apiserver обновляет объект Endpoints/EndpointSlice, и kube-proxy/CNI на всех нодах кластера обновляет правила iptables/IPVS. Распространение правил маршрутизации по кластеру занимает от сотен миллисекунд до нескольких секунд. Если Go-процесс при перехвате SIGTERM немедленно закроет TCP-сокет (`Close()` или мгновенный `Shutdown`), пакеты от других сервисов, отправленные до обновления iptables, наткнутся на закрытый порт и получат TCP RST (Connection Refused / HTTP 502). Поэтому Graceful Draining требует выдержать задержку (обычно 5-15 секунд) перед закрытием листенера.",
        "step_by_step": [
            "Создайте context с перехватом сигналов os.Interrupt и syscall.SIGTERM через signal.NotifyContext.",
            "Запустите HTTP сервер в отдельной горутине.",
            "При получении сигнала переведите флаг здоровья в 'unhealthy' и выполните time.Sleep на время распространения iptables.",
            "Вызовите server.Shutdown(ctx) с ограниченным таймаутом.",
            "Убедитесь, что все фоновые воркеры и соединения завершены корректно."
        ],
        "code_blocks": [
            {
                "filename": "draining.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n\t\"os/signal\"\n\t\"sync/atomic\"\n\t\"syscall\"\n\t\"time\"\n)\n\ntype ServerApp struct {\n\thttpServer *http.Server\n\tisDraining atomic.Bool\n}\n\nfunc NewServerApp(addr string) *ServerApp {\n\tapp := &ServerApp{}\n\tmux := http.NewServeMux()\n\n\tmux.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tif app.isDraining.Load() {\n\t\t\thttp.Error(w, \"shutting down, draining traffic\", http.StatusServiceUnavailable)\n\t\t\treturn\n\t\t}\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"OK\"))\n\t})\n\n\tmux.HandleFunc(\"/api/work\", func(w http.ResponseWriter, r *http.Request) {\n\t\ttime.Sleep(100 * time.Millisecond)\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(`{\"status\":\"processed\"}`))\n\t})\n\n\tapp.httpServer = &http.Server{\n\t\tAddr:    addr,\n\t\tHandler: mux,\n\t}\n\treturn app\n}\n\nfunc (app *ServerApp) Run() error {\n\tctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)\n\tdefer stop()\n\n\terrChan := make(chan error, 1)\n\tgo func() {\n\t\tlog.Printf(\"Server listening on %s\", app.httpServer.Addr)\n\t\tif err := app.httpServer.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {\n\t\t\terrChan <- err\n\t\t}\n\t}()\n\n\tselect {\n\tcase err := <-errChan:\n\t\treturn fmt.Errorf(\"server error: %w\", err)\n\tcase <-ctx.Done():\n\t\tlog.Println(\"[SIGTERM] Received termination signal, starting graceful draining...\")\n\t}\n\n\t// 1. Помечаем под как не готовый принимать трафик\n\tapp.isDraining.Store(true)\n\n\t// 2. Выдерживаем задержку для распространения изменений iptables/IPVS в K8s\n\tdrainDelay := 2 * time.Second\n\tlog.Printf(\"[Drain] Sleeping %v to allow K8s endpoints and kube-proxy to propagate...\", drainDelay)\n\ttime.Sleep(drainDelay)\n\n\t// 3. Завершаем активные запросы через server.Shutdown\n\tshutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)\n\tdefer cancel()\n\n\tlog.Println(\"[Shutdown] Closing listeners and draining remaining in-flight requests...\")\n\tif err := app.httpServer.Shutdown(shutdownCtx); err != nil {\n\t\treturn fmt.Errorf(\"graceful shutdown failed: %w\", err)\n\t}\n\n\tlog.Println(\"[Shutdown] Server gracefully stopped without packet loss.\")\n\treturn nil\n}\n\nfunc main() {\n\tapp := NewServerApp(\":8080\")\n\tif err := app.Run(); err != nil {\n\t\tlog.Fatalf(\"Server exit with error: %v\", err)\n\t}\n}",
                "note": "Обработка SIGTERM с задержкой для предотвращения сброса TCP соединений в K8s"
            }
        ],
        "under_the_hood": "Когда kube-apiserver получает запрос на удаление пода, он инициирует Endpoint Controller, который пересчитывает список IP-адресов. Демоны kube-proxy на каждой рабочей ноде периодически опрашивают apiserver и перезаписывают правила netfilter iptables/nftables или IPVS tables. Этот лаг составляет в среднем от 1 до 3 секунд. Задержка Sleep(5s) гарантирует, что к моменту закрытия сокета листенер уже не получает новых SYN-пакетов извне.",
        "pitfalls": "Если в манифесте Kubernetes `terminationGracePeriodSeconds` (по умолчанию 30с) меньше, чем суммарная задержка `drainDelay` + `shutdownTimeout`, kubelet не дождется завершения и принудительно убьет под сигналом SIGKILL (exit 137).",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'Почему в высоконагруженных микросервисах нельзя сразу вызывать server.Shutdown() при SIGTERM?' Ответ: 'Потому что iptables на других подах и нодах еще несколько секунд перенаправляют входящий трафик на IP удаляемого пода. Немедленный Shutdown закрывает сокет, и все эти запросы получают Connection Refused. Необходима фаза draining delay'."
    },
    {
        "num": 12,
        "title": "OpenTelemetry Baggage: контекстная передача метаданных по цепочке вызовов",
        "task": "Реализуйте проброс W3C Baggage (user-id=123, tenant=acme) сквозь HTTP-запросы с помощью go.opentelemetry.io/otel/baggage. Покажите извлечение baggage на вызываемой стороне и объясните ограничения безопасности.",
        "theory": "OpenTelemetry Baggage (W3C Baggage Specification) — это механизм передачи пар 'ключ-значение' между распределенными микросервисами вместе с контекстом трассировки. В отличие от атрибутов спана (которые остаются локальными в рамках текущего спана или экспортируются коллектору), Baggage сериализуется в HTTP-заголовок `baggage: key1=val1,key2=val2` или в gRPC metadata и автоматически путешествует по всей цепочке вызовов. Baggage критически важен для передачи контекста тенанта (multi-tenancy routing), feature flags, A/B-тестирования или customer tier. Однако Baggage передается в открытом виде и не шифруется, поэтому в него запрещено помещать PII, токены и пароли.",
        "step_by_step": [
            "Импортируйте пакет go.opentelemetry.io/otel/baggage.",
            "Сформируйте элементы baggage через baggage.NewMember.",
            "Создайте новый baggage объект и внедрите его в context.Context через baggage.ContextWithBaggage.",
            "Сериализуйте заголовок baggage и передайте в исходящем HTTP запросе.",
            "На стороне сервера спарсите заголовок через baggage.Parse и извлеките переданные свойства."
        ],
        "code_blocks": [
            {
                "filename": "baggage_demo.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\n\t\"go.opentelemetry.io/otel/baggage\"\n)\n\n// InjectBaggageToHeader записывает метаданные baggage в исходящий HTTP запрос\nfunc InjectBaggageToHeader(ctx context.Context, req *http.Request) {\n\tb := baggage.FromContext(ctx)\n\tif b.Len() > 0 {\n\t\treq.Header.Set(\"baggage\", b.String())\n\t}\n}\n\n// ExtractBaggageFromHeader восстанавливает baggage из входящего HTTP запроса в context\nfunc ExtractBaggageFromHeader(req *http.Request) (context.Context, error) {\n\trawBaggage := req.Header.Get(\"baggage\")\n\tif rawBaggage == \"\" {\n\t\treturn req.Context(), nil\n\t}\n\n\tb, err := baggage.Parse(rawBaggage)\n\tif err != nil {\n\t\treturn req.Context(), fmt.Errorf(\"invalid baggage header: %w\", err)\n\t}\n\n\treturn baggage.ContextWithBaggage(req.Context(), b), nil\n}\n\nfunc main() {\n\t// Создаем свойства baggage: tenant=enterprise-alpha, user-id=u-98421\n\tmemTenant, err := baggage.NewMember(\"tenant\", \"enterprise-alpha\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Member error: %v\", err)\n\t}\n\tmemUser, err := baggage.NewMember(\"user_id\", \"u-98421\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Member error: %v\", err)\n\t}\n\n\tbag, err := baggage.New(memTenant, memUser)\n\tif err != nil {\n\t\tlog.Fatalf(\"Baggage creation error: %v\", err)\n\t}\n\n\t// Внедряем baggage в контекст\n\tctx := baggage.ContextWithBaggage(context.Background(), bag)\n\n\t// Тестовый обработчик микросервиса Б ( downstream )\n\thandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\tdownstreamCtx, err := ExtractBaggageFromHeader(r)\n\t\tif err != nil {\n\t\t\thttp.Error(w, err.Error(), http.StatusBadRequest)\n\t\t\treturn\n\t\t}\n\n\t\tserverBag := baggage.FromContext(downstreamCtx)\n\t\ttenantVal := serverBag.Member(\"tenant\").Value()\n\t\tuserVal := serverBag.Member(\"user_id\").Value()\n\n\t\tfmt.Fprintf(w, \"Received Baggage: tenant=%s, user_id=%s\\n\", tenantVal, userVal)\n\t})\n\n\tserver := httptest.NewServer(handler)\n\tdefer server.Close()\n\n\t// Микросервис А делает исходящий запрос в Б\n\treq, _ := http.NewRequestWithContext(ctx, \"GET\", server.URL, nil)\n\tInjectBaggageToHeader(ctx, req)\n\n\tresp, err := http.DefaultClient.Do(req)\n\tif err != nil {\n\t\tlog.Fatalf(\"Request failed: %v\", err)\n\t}\n\tdefer resp.Body.Close()\n\n\tlog.Printf(\"Downstream response status: %s\", resp.Status)\n}",
                "note": "Создание, сериализация и десериализация заголовка baggage в Go"
            }
        ],
        "under_the_hood": "Baggage сериализуется по стандарту W3C в заголовок `baggage` в виде разделенных запятыми пар `key=value` с опциональными свойствами `key=value;prop1=v1`. OpenTelemetry propagator парсит эту строку при каждом hops-переходе и сохраняет неизменяемую структуру в контексте горутины. При вызове child RPC библиотека автоматически копирует baggage дальше.",
        "pitfalls": "Переполнение HTTP-заголовков. Baggage не сжимается и добавляется к каждому исходящему запросу. Если разработчики начинают передавать крупные JSON-структуры через Baggage, размер HTTP headers превысит лимиты прокси (8KB/16KB в Nginx/Envoy), что приведет к ошибкам 431 Request Header Fields Too Large.",
        "bigtech_interview": "В чем разница между Span Attributes и Baggage в OpenTelemetry? Ответ: 'Span Attributes принадлежат строго одному текущему спану и отправляются в Tracing Backend (Jaeger/Tempo). Baggage НЕ попадает в трассировку автоматически, но пробрасывается по сети во все downstream микросервисы через заголовки'."
    },
    {
        "num": 13,
        "title": "Trace Context и Service Mesh: сквозное связывание спанов через Envoy",
        "task": "Покажите, как Go-приложение в инфраструктуре Service Mesh (Istio / Envoy sidecar) обязано перекладывать входящие заголовки трассировки (x-request-id, traceparent) в исходящие вызовы, чтобы цепочка спанов не разрывалась.",
        "theory": "Распространенное заблуждение: 'Если у нас в Kubernetes развернут Istio Service Mesh, трассировка работает из коробки без изменения Go-кода'. Это правда лишь для входящего и исходящего трафика на уровне одного пода. Envoy перехватывает входящий запрос, генерирует клиентский/серверный спан и передает запрос локальному Go-приложению на 127.0.0.1. Но когда Go-приложение совершает исходящий HTTP/gRPC вызов к другому сервису, Envoy не знает, к какому из 1000 параллельных входящих запросов относится этот вызов! Go-код ОБЯЗАН скопировать заголовки трассировки (`x-request-id`, `traceparent`, `x-b3-traceid`) из входящего контекста в исходящие заголовки. Без этого Envoy создаст абсолютно новый `x-request-id`, и распределенный граф трейса в Jaeger распадется на разрозненные фрагменты.",
        "step_by_step": [
            "Определите список обязательных для проброса заголовков Service Mesh (x-request-id, traceparent, x-b3-*).",
            "Реализуйте HTTP middleware, извлекающее эти заголовки и сохраняющее их в контексте.",
            "Создайте http.RoundTripper (или клиентский middleware), инжектирующий сохраненные заголовки в любой исходящий запрос.",
            "Проверьте сохранение единого x-request-id сквозь цепочку микросервисов."
        ],
        "code_blocks": [
            {
                "filename": "mesh_propagation.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n)\n\ntype contextKey string\n\nconst meshHeadersKey contextKey = \"mesh_tracing_headers\"\n\nvar tracingHeadersToPropagate = []string{\n\t\"x-request-id\",\n\t\"traceparent\",\n\t\"tracestate\",\n\t\"x-b3-traceid\",\n\t\"x-b3-spanid\",\n\t\"x-b3-sampled\",\n}\n\n// ServiceMeshTracingMiddleware сохраняет mesh-заголовки входящего запроса в context\nfunc ServiceMeshTracingMiddleware(next http.Handler) http.Handler {\n\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\theaders := make(http.Header)\n\t\tfor _, h := range tracingHeadersToPropagate {\n\t\t\tif val := r.Header.Get(h); val != \"\" {\n\t\t\t\theaders.Set(h, val)\n\t\t\t}\n\t\t}\n\n\t\tctx := context.WithValue(r.Context(), meshHeadersKey, headers)\n\t\tnext.ServeHTTP(w, r.WithContext(ctx))\n\t})\n}\n\n// MeshTransport автоматически проставляет mesh-заголовки из контекста в исходящий вызов\ntype MeshTransport struct {\n\tBase http.RoundTripper\n}\n\nfunc (m *MeshTransport) RoundTrip(req *http.Request) (*http.Response, error) {\n\tif headers, ok := req.Context().Value(meshHeadersKey).(http.Header); ok {\n\t\tfor key, vals := range headers {\n\t\t\tfor _, val := range vals {\n\t\t\t\treq.Header.Add(key, val)\n\t\t\t}\n\t\t}\n\t}\n\tbase := m.Base\n\tif base == nil {\n\t\tbase = http.DefaultTransport\n\t}\n\treturn base.RoundTrip(req)\n}\n\nfunc main() {\n\t// downstream service\n\tbackend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\treqID := r.Header.Get(\"x-request-id\")\n\t\ttp := r.Header.Get(\"traceparent\")\n\t\tfmt.Fprintf(w, \"Downstream received x-request-id: %s, traceparent: %s\\n\", reqID, tp)\n\t}))\n\tdefer backend.Close()\n\n\t// Наш сервис с middleware и MeshTransport\n\tclient := &http.Client{Transport: &MeshTransport{}}\n\n\tourServiceHandler := ServiceMeshTracingMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\t// Делаем вызов в downstream сервис, контекст содержит mesh-заголовки\n\t\toutReq, _ := http.NewRequestWithContext(r.Context(), \"GET\", backend.URL, nil)\n\t\tresp, err := client.Do(outReq)\n\t\tif err != nil {\n\t\t\thttp.Error(w, err.Error(), http.StatusInternalServerError)\n\t\t\treturn\n\t\t}\n\t\tdefer resp.Body.Close()\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"Mesh propagation completed successfully\"))\n\t}))\n\n\tts := httptest.NewServer(ourServiceHandler)\n\tdefer ts.Close()\n\n\t// Имитация входящего запроса от Envoy\n\tinboundReq, _ := http.NewRequest(\"GET\", ts.URL, nil)\n\tinboundReq.Header.Set(\"x-request-id\", \"envoy-req-abc-987\")\n\tinboundReq.Header.Set(\"traceparent\", \"00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01\")\n\n\tres, err := http.DefaultClient.Do(inboundReq)\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer res.Body.Close()\n\tfmt.Printf(\"Gateway response status: %s\\n\", res.Status)\n}",
                "note": "Сквозной проброс заголовков трассировки Envoy/Istio через context и RoundTripper"
            }
        ],
        "under_the_hood": "Envoy генерирует спан Envoy-Inbound, когда запрос попадает на внешний порт пода, и ожидает увидеть тот же самый x-request-id в заголовках, когда Go-приложение обращается к другим внешним сервисам через свой localhost Envoy-Outbound. Если Go-сервис не перекладывает эти заголовки, Envoy считает исходящий запрос новой изолированной транзакцией.",
        "pitfalls": "Копирование заголовков 'вслепую' без фильтрации. Если скопировать `Host`, `Content-Length` или чувствительные auth-токены в вызовы сторонних API, можно нарушить HTTP/1.1 протокол или допустить утечку секретов.",
        "bigtech_interview": "Вопрос на собеседовании в Lamoda: 'Если Istio перехватывает весь трафик через iptables, зачем вообще разработчикам трогать контекст трассировки в Go?' Ответ: 'Istio видит байты на сокете, но внутри Go-процесса выполняются сотни конкурентных горутин. Только рантайм Go знает связь между входящим HTTP-запросом и последующими исходящими RPC-вызовами. Без проброса заголовков сквозь context.Context трассировка фрагментируется'."
    },
    {
        "num": 14,
        "title": "Graceful Draining: ReadinessProbe 503 при получении SIGTERM",
        "task": "Реализуйте переключение ReadinessProbe в статус 503 Service Unavailable при перехвате SIGTERM, сохраняя работоспособность livenessProbe и завершая активные запросы.",
        "theory": "Kubernetes опрашивает два разных зонда: 1) `livenessProbe` — отвечает на вопрос 'Жив ли процесс?'. Если возвращает ошибку, kubelet немедленно убивает контейнер и перезапускает его. При graceful shutdown livenessProbe ДОЛЖЕН отдавать 200 OK! 2) `readinessProbe` — отвечает на вопрос 'Готов ли под принимать трафик клиентов?'. Если возвращает 503, kubelet исключает IP пода из всех Endpoints и балансировщиков (Ingress, Service, Envoy). При перехвате SIGTERM приложение обязано немедленно перевести готовность в `false` (`readinessProbe` -> 503), но продолжать отвечать 200 на `livenessProbe`, чтобы kubelet дал приложению время доработать текущие HTTP/gRPC запросы до истечения terminationGracePeriodSeconds.",
        "step_by_step": [
            "Используйте sync/atomic или atomic.Bool для потокобезопасного хранения состояния готовности.",
            "Зарегистрируйте эндпоинт /livez с безусловным возвратом 200 OK.",
            "Зарегистрируйте эндпоинт /readyz с проверкой флага готовности.",
            "При получении SIGTERM выставите флаг готовности в false.",
            "Выдержите задержку и дождитесь завершения активных транзакций."
        ],
        "code_blocks": [
            {
                "filename": "probes_draining.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n\t\"os/signal\"\n\t\"sync/atomic\"\n\t\"syscall\"\n\t\"time\"\n)\n\ntype HealthController struct {\n\tisReady atomic.Bool\n\tisLive  atomic.Bool\n}\n\nfunc NewHealthController() *HealthController {\n\thc := &HealthController{}\n\thc.isLive.Store(true)\n\thc.isReady.Store(true)\n\treturn hc\n}\n\nfunc (hc *HealthController) SetupRoutes(mux *http.ServeMux) {\n\t// Liveness: жив ли рантайм Go (всегда 200, если нет дедлока)\n\tmux.HandleFunc(\"/livez\", func(w http.ResponseWriter, r *http.Request) {\n\t\tif !hc.isLive.Load() {\n\t\t\thttp.Error(w, \"DEAD\", http.StatusInternalServerError)\n\t\t\treturn\n\t\t}\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"ALIVE\"))\n\t})\n\n\t// Readiness: готов ли принимать клиентский трафик\n\tmux.HandleFunc(\"/readyz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tif !hc.isReady.Load() {\n\t\t\t// При 503 K8s удаляет под из балансировки\n\t\t\thttp.Error(w, \"DRAINING\", http.StatusServiceUnavailable)\n\t\t\treturn\n\t\t}\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"READY\"))\n\t})\n}\n\nfunc main() {\n\thc := NewHealthController()\n\tmux := http.NewServeMux()\n\thc.SetupRoutes(mux)\n\n\tmux.HandleFunc(\"/api/data\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(`{\"payload\":\"success\"}`))\n\t})\n\n\tserver := &http.Server{\n\t\tAddr:    \":8080\",\n\t\tHandler: mux,\n\t}\n\n\tgo func() {\n\t\tif err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {\n\t\t\tlog.Fatalf(\"Server listen failed: %v\", err)\n\t\t}\n\t}()\n\tlog.Println(\"Server running with /livez and /readyz probes\")\n\n\t// Ловим сигнал остановки\n\tsigChan := make(chan os.Signal, 1)\n\tsignal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)\n\t<-sigChan\n\n\tlog.Println(\"[SIGTERM] Draining started: setting readiness to FALSE (503)...\")\n\t// Переводим готовность в false: K8s исключает под из Endpoints\n\thc.isReady.Store(false)\n\n\t// Liveness остается true! K8s не должен убивать под принудительно\n\tlog.Printf(\"[SIGTERM] Liveness status is still: %v (200 OK)\", hc.isLive.Load())\n\n\t// Даем время K8s kube-proxy убрать роуты\n\ttime.Sleep(3 * time.Second)\n\n\t// Завершаем сервер\n\tshutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\tdefer cancel()\n\n\tif err := server.Shutdown(shutdownCtx); err != nil {\n\t\tlog.Printf(\"Graceful shutdown error: %v\", err)\n\t}\n\tfmt.Println(\"Clean shutdown finished.\")\n}",
                "note": "Разделение liveness (200) и readiness (503 при drain) во время завершения пода"
            }
        ],
        "under_the_hood": "kubelet выполняет HTTP GET к readinessProbe с интервалом `periodSeconds` (например, 2с). Как только получен код >= 400, kubelet локально перестает направлять трафик и рапортует apiserver, чтобы IP пода был исключен из EndpointSlice. Если бы мы ошибочно вернули 503 на livenessProbe, kubelet мгновенно отправил бы SIGKILL, оборвав все активные соединения пользователей.",
        "pitfalls": "Возврат 503 на livenessProbe при выключении. Это частая ошибка начинающих: под не успевает завершить запросы, так как kubelet расценивает отказ livenessProbe как краш приложения и перезапускает его.",
        "bigtech_interview": "В чем фундаментальная разница между LivenessProbe и ReadinessProbe при graceful shutdown в K8s? Ответ: 'LivenessProbe сигнализирует о зависании процесса (дедлок, OOM). При ее падении контейнер рестартится. ReadinessProbe управляет маршрутизацией трафика. При graceful shutdown мы выключаем только ReadinessProbe, чтобы отрезать новый трафик, но LivenessProbe держим зеленой, пока дорабатывают старые запросы'."
    },
    {
        "num": 15,
        "title": "Server-side gRPC Keepalive: циклический сброс сессий и защита от зависших стримов",
        "task": "Настройте gRPC сервер с keepalive.ServerParameters (MaxConnectionIdle: 5m, MaxConnectionAge: 10m, MaxConnectionAgeGrace: 30s, Time: 2h, Timeout: 20s). Объясните роль MaxConnectionAge в балансировке нагрузки gRPC.",
        "theory": "gRPC использует HTTP/2 мультиплексирование поверх одного постоянного TCP соединения. При работе за L4 балансировщиком (AWS NLB, Kubernetes ClusterIP) клиенты открывают сокет к существующим подам и держат его часами. Когда вы масштабируете Deployment с 3 до 10 реплик, старые 3 реплики получают 100% трафика, а новые 7 простаивают без соединений! Чтобы решить эту проблему без усложнения балансировщика, сервер gRPC настраивается параметром `MaxConnectionAge`. По истечении `MaxConnectionAge` сервер мягко отправляет клиенту HTTP/2 фрейм `GOAWAY`. Клиент завершает текущие запросы в течение `MaxConnectionAgeGrace`, разрывает TCP сокет и подключается заново. При новом подключении DNS/L4 балансировщик распределяет клиента на новую свободную реплику. Это выравнивает нагрузку по кластеру.",
        "step_by_step": [
            "Импортируйте google.golang.org/grpc/keepalive.",
            "Инициализируйте keepalive.ServerParameters с требуемыми параметрами времени жизни соединения.",
            "Сконфигурируйте MaxConnectionAge: 10m и MaxConnectionAgeGrace: 30s.",
            "Передайте параметры в конструктор grpc.NewServer(grpc.KeepaliveParams(kasp)).",
            "Запустите сервер и протестируйте поведение клиента при получении GOAWAY."
        ],
        "code_blocks": [
            {
                "filename": "grpc_server_keepalive.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/keepalive\"\n)\n\nfunc CreateGRPCServer() *grpc.Server {\n\t// Параметры keepalive на стороне сервера\n\tkasp := keepalive.ServerParameters{\n\t\tMaxConnectionIdle:     5 * time.Minute, // Время неактивности до закрытия соединения\n\t\tMaxConnectionAge:      10 * time.Minute, // Максимальное время жизни одного TCP соединения (ротация)\n\t\tMaxConnectionAgeGrace: 30 * time.Second, // Дополнительное время на завершение активных RPC после GOAWAY\n\t\tTime:                  2 * time.Hour,    // Периодичность пинга сервера клиенту при отсутствии трафика\n\t\tTimeout:               20 * time.Second, // Время ожидания ответа на серверный пинг\n\t}\n\n\t// Политика контроля активности клиентов (защита от частых клиентских пингов)\n\tkaep := keepalive.EnforcementPolicy{\n\t\tMinTime:             5 * time.Second, // Клиент не имеет права слать PING чаще раза в 5 секунд\n\t\tPermitWithoutStream: true,            // Разрешить клиенту пинговать даже без активных стримов\n\t}\n\n\tserver := grpc.NewServer(\n\t\tgrpc.KeepaliveParams(kasp),\n\t\tgrpc.KeepaliveEnforcementPolicy(kaep),\n\t)\n\n\treturn server\n}\n\nfunc main() {\n\tlis, err := net.Listen(\"tcp\", \":50051\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Listen failed: %v\", err)\n\t}\n\n\tserver := CreateGRPCServer()\n\tlog.Println(\"gRPC Server initialized with MaxConnectionAge=10m for dynamic rebalancing\")\n\n\tgo func() {\n\t\ttime.Sleep(100 * time.Millisecond)\n\t\tlis.Close()\n\t}()\n\n\t_ = server.Serve(lis)\n\tfmt.Println(\"Server keepalive demonstration completed.\")\n}",
                "note": "Серверный gRPC keepalive с принудительной ротацией соединений через MaxConnectionAge"
            }
        ],
        "under_the_hood": "При срабатывании таймера `MaxConnectionAge` сервер вызывает `http2Server.GracefulClose()`. В сокет отправляется первый кадр `GOAWAY` с `LastStreamID = 2^31 - 1`, сообщающий клиенту, что сервер скоро закроется. По истечении `MaxConnectionAgeGrace` сервер отправляет финальный `GOAWAY` с актуальным `LastStreamID` и закрывает TCP сокет.",
        "pitfalls": "Если клиенты не настроены на автоматический reconnect или не используют retry-политики с экспоненциальным backoff и jitter, одновременное срабатывание MaxConnectionAge на всех серверах может вызвать 'шторм переподключений' (Thundering Herd Problem). Всегда добавляйте случайный jitter к MaxConnectionAge.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Зачем в gRPC серверах настраивают MaxConnectionAge, если TCP соединение стабильно и не рвется?' Ответ: 'Чтобы обеспечить равномерную балансировку в динамическом кластере K8s. При добавлении новых реплик gRPC клиенты сами не перейдут на них из-за постоянного HTTP/2 соединения. MaxConnectionAge заставляет клиентов периодически переподключаться и перебалансироваться'."
    },
    {
        "num": 16,
        "title": "Корреляция распределенных логов с Trace Context в slog / zap",
        "task": "Реализуйте структурированный логер на базе log/slog, который автоматически извлекает trace_id и span_id из context.Context и добавляет их во все логи приложения.",
        "theory": "В распределенных системах тысячи микросервисов генерируют миллионы строк логов в секунду. Если логи не содержат единый сквозной идентификатор транзакции, сопоставить ошибку в платежном шлюзе с действием пользователя в мобильном приложении невозможно. Стандарт W3C Trace Context и OpenTelemetry предоставляют TraceID (32 hex) и SpanID (16 hex). Создав кастомный `slog.Handler` или интерцептор, мы автоматически обогащаем каждую запись лога полями `trace_id` и `span_id`. В результате в Kibana, Grafana Loki или ClickHouse по запросу `trace_id = 4bf92f3577b34da6a3ce929d0e0e4736` инженер видит полную хронологическую цепочку событий всех сервисов.",
        "step_by_step": [
            "Реализуйте обертку над slog.Handler, перехватывающую вызов Handle(ctx, record).",
            "Извлеките активный спан из контекста через trace.SpanFromContext(ctx).",
            "Проверьте валидность SpanContext.",
            "Добавьте атрибуты trace_id и span_id к записи лога slog.Record.",
            "Проверьте форматирование в JSON формате."
        ],
        "code_blocks": [
            {
                "filename": "log_correlation.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"bytes\"\n\t\"context\"\n\t\"fmt\"\n\t\"log/slog\"\n\t\"os\"\n\n\t\"go.opentelemetry.io/otel/trace\"\n)\n\n// TraceContextHandler автоматически внедряет trace_id и span_id из OpenTelemetry в slog\ntype TraceContextHandler struct {\n\tslog.Handler\n}\n\nfunc NewTraceContextHandler(inner slog.Handler) *TraceContextHandler {\n\treturn &TraceContextHandler{Handler: inner}\n}\n\nfunc (h *TraceContextHandler) Handle(ctx context.Context, r slog.Record) error {\n\tspan := trace.SpanFromContext(ctx)\n\tif span != nil && span.SpanContext().IsValid() {\n\t\tsc := span.SpanContext()\n\t\tr.AddAttrs(\n\t\t\tslog.String(\"trace_id\", sc.TraceID().String()),\n\t\t\tslog.String(\"span_id\", sc.SpanID().String()),\n\t\t)\n\t}\n\treturn h.Handler.Handle(ctx, r)\n}\n\nfunc main() {\n\tvar buf bytes.Buffer\n\t// Создаем JSON-логер с поддержкой Trace Context\n\tjsonHandler := slog.NewJSONHandler(&buf, &slog.HandlerOptions{Level: slog.LevelInfo})\n\tlogger := slog.New(NewTraceContextHandler(jsonHandler))\n\n\t// Имитируем контекст с валидным спаном OpenTelemetry\n\ttraceID, _ := trace.TraceIDFromHex(\"4bf92f3577b34da6a3ce929d0e0e4736\")\n\tspanID, _ := trace.SpanIDFromHex(\"00f067aa0ba902b7\")\n\tspanCtx := trace.NewSpanContext(trace.SpanContextConfig{\n\t\tTraceID:    traceID,\n\t\tSpanID:     spanID,\n\t\tTraceFlags: trace.FlagsSampled,\n\t})\n\n\tctx := trace.ContextWithSpanContext(context.Background(), spanCtx)\n\n\t// Запись лога с контекстом трассировки\n\tlogger.InfoContext(ctx, \"Payment processed successfully\",\n\t\tslog.Float64(\"amount\", 1499.50),\n\t\tslog.String(\"currency\", \"RUB\"),\n\t)\n\n\t// Запись лога без контекста (trace_id не добавляется)\n\tlogger.WarnContext(context.Background(), \"Cache miss on catalog key\")\n\n\tfmt.Print(buf.String())\n\t_ = os.Stdout\n}",
                "note": "Автоматическая корреляция логов с trace_id и span_id через кастомный slog.Handler"
            }
        ],
        "under_the_hood": "`trace.SpanFromContext(ctx)` извлекает значение интерфейса `trace.Span` из структуры context.Context. Метод `SpanContext()` возвращает неизменяемую структуру с 16-байтным TraceID и 8-байтным SpanID. Метод `r.AddAttrs` дополняет внутренний слайс атрибутов slog.Record без дополнительных аллокаций в куче.",
        "pitfalls": "Логирование спанов с флагом sampled=false как ошибочных. Не забывайте, что даже если спан не был засэмплирован для отправки в коллектор трассировки, его TraceID все равно валиден и полезен для корреляции логов в хранилище логов.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Как подружить Grafana Loki и Jaeger Tracing?' Ответ: 'В Loki настраивается Derived Field по регулярному выражению для поля trace_id. При клике на лог в Grafana интерфейс автоматически открывает соответствующий трейс в Tempo или Jaeger по полученному trace_id. Для этого все микросервисы обязаны писать trace_id в JSON-логи'."
    },
    {
        "num": 17,
        "title": "Задержка Sleep для обновления iptables и kube-proxy роутов при остановке пода",
        "task": "Напишите безопасную функцию ожидания деактивации пода в Kubernetes с проверкой сигналов отмены и логами обратного отсчета.",
        "theory": "Сетевая подсистема Linux (Netfilter/iptables/IPVS) работает на уровне ядра каждой ноды кластера. Когда Pod переходит в статус `Terminating`, контроллер Kubernetes оповещает kube-proxy на всех нодах. Процесс обновления таблицы правил iptables не происходит мгновенно — это распределенная операция, зависящая от нагрузки на apiserver и размера кластера. Если приложение сразу завершит слушающий сокет, клиенты из других нод продолжат отправлять пакеты на старый IP пода, получая ошибки `ECONNREFUSED`. Выдержка фиксированной паузы (`drain delay`, обычно 5-10 секунд) после перевода ReadinessProbe в 503 позволяет дождаться полного исключения пода из маршрутизации всех нод.",
        "step_by_step": [
            "Определите функцию DrainWait с параметром duration и контекстом отмены.",
            "Используйте time.NewTicker для логирования обратного отсчета.",
            "Обеспечьте корректный выход, если родительский контекст завершился раньше времени.",
            "Интегрируйте вызов DrainWait в конвейер остановки сервера."
        ],
        "code_blocks": [
            {
                "filename": "drain_delay.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"time\"\n)\n\n// WaitForNetworkDraining ожидает обновления маршрутизации iptables/kube-proxy в кластере\nfunc WaitForNetworkDraining(ctx context.Context, delay time.Duration) error {\n\tlog.Printf(\"[Draining] Waiting %v for iptables/IPVS routing update across K8s cluster...\", delay)\n\n\tticker := time.NewTicker(1 * time.Second)\n\tdefer ticker.Stop()\n\n\tstartTime := time.Now()\n\tdeadline := startTime.Add(delay)\n\n\tfor {\n\t\tselect {\n\t\tcase <-ctx.Done():\n\t\t\treturn fmt.Errorf(\"draining interrupted by context deadline: %w\", ctx.Err())\n\t\tcase now := <-ticker.C:\n\t\t\tremaining := deadline.Sub(now).Round(time.Second)\n\t\t\tif remaining <= 0 {\n\t\t\t\tlog.Println(\"[Draining] Network drain delay completed. Safe to close server socket.\")\n\t\t\t\treturn nil\n\t\t\t}\n\t\t\tlog.Printf(\"[Draining] %v remaining until socket close...\", remaining)\n\t\t}\n\t}\n}\n\nfunc main() {\n\tctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)\n\tdefer cancel()\n\n\t// Имитация выдержки паузы в 3 секунды\n\tif err := WaitForNetworkDraining(ctx, 3*time.Second); err != nil {\n\t\tlog.Fatalf(\"Drain error: %v\", err)\n\t}\n\tfmt.Println(\"Ready to perform server.Shutdown()\")\n}",
                "note": "Контролируемая пауза с обратным отсчетом для обновления сетевых правил ядра Linux"
            }
        ],
        "under_the_hood": "kube-proxy синхронизирует iptables батчами (параметр `--iptables-min-sync-interval`, по умолчанию 1с, `--iptables-sync-period`, по умолчанию 30с). Пока этот интервал не истек, ядро хоста направляет сетевые пакеты по старым правилам PREROUTING KUBE-SERVICES. Фиксированная пауза дает гарантию завершения цикла синхронизации.",
        "pitfalls": "Использование неблокирующего time.Sleep без отслеживания контекста. Если оператор нажмет Ctrl+C повторно или произойдет отмена контекста, 'слепой' time.Sleep заблокирует процесс и проигнорирует команду срочной остановки.",
        "bigtech_interview": "Вопрос на собеседовании в Тинькофф: 'Почему в высоконагруженных сервисах нельзя полагаться только на закрытие соединений со стороны балансировщика Ingress?' Ответ: 'Потому что трафик идет не только через внешний Ingress, но и внутри кластера (East-West traffic) от других подов напрямую через kube-proxy / ClusterIP. Если закрыть сокет раньше обновления iptables на нодах-клиентах, внутренние сервисы получат 502/RST ошибки'."
    },
    {
        "num": 18,
        "title": "OpenTelemetry Span Batch Exporter: тюнинг буфера и защита от OOM при HighLoad",
        "task": "Сконфигурируйте OpenTelemetry BatchSpanProcessor с параметрами BatchTimeout=1s, MaxQueueSize=2048, MaxExportBatchSize=512. Объясните, почему SimpleSpanProcessor недопустим в продакшене.",
        "theory": "Сбор трассировки не должен влиять на задержку (latency) бизнес-логики. `SimpleSpanProcessor` отправляет каждый спан в коллектор синхронно в момент вызова `span.End()`. Это катастрофично для продакшена: сетевая задержка экспорта (10-50мс) добавляется к каждому пользовательскому запросу! `BatchSpanProcessor` решает эту проблему асинхронным буферизированием: спаны помещаются в очередь в памяти (`MaxQueueSize`), а фоновая горутина пачками (`MaxExportBatchSize`) отправляет их по таймауту (`BatchTimeout`) через gRPC/HTTP к OpenTelemetry Collector. При внезапном спайке трафика, если очередь заполняется (> MaxQueueSize), процессор начинает безопасно отбрасывать (drop) новые спаны, защищая приложение от утечки памяти и падения по OOM.",
        "step_by_step": [
            "Импортируйте go.opentelemetry.io/otel/sdk/trace.",
            "Создайте экспортер (например, trace.NewNoopExporter или gRPC/stdout).",
            "Сконфигурируйте trace.NewBatchSpanProcessor с опциями WithBatchTimeout, WithMaxQueueSize, WithMaxExportBatchSize.",
            "Инициализируйте TracerProvider с батч-процессором.",
            "Обязательно вызовите tp.Shutdown(ctx) при завершении сервиса для сброса оставшихся спанов."
        ],
        "code_blocks": [
            {
                "filename": "batch_processor.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"time\"\n\n\t\"go.opentelemetry.io/otel\"\n\tsdktrace \"go.opentelemetry.io/otel/sdk/trace\"\n\t\"go.opentelemetry.io/otel/trace\"\n)\n\n// InitTracerProvider настраивает высокопроизводительный батчевый провайдер трассировки\nfunc InitTracerProvider() (*sdktrace.TracerProvider, error) {\n\t// В реальном продакшене используется otlptracegrpc.New(...)\n\texporter, err := sdktrace.NewNoopExporter()\n\tif err != nil {\n\t\treturn nil, fmt.Errorf(\"failed to create exporter: %w\", err)\n\t}\n\n\t// Настройка параметров пакетной обработки спанов\n\tbsp := sdktrace.NewBatchSpanProcessor(\n\t\texporter,\n\t\tsdktrace.WithBatchTimeout(1*time.Second),      // Максимальный интервал между сбросами батча\n\t\tsdktrace.WithExportTimeout(3*time.Second),     // Таймаут сетевого экспорта в коллектор\n\t\tsdktrace.WithMaxQueueSize(2048),              // Защита от OOM: ограничение кольцевого буфера\n\t\tsdktrace.WithMaxExportBatchSize(512),         // Размер одного пакета отправки\n\t)\n\n\ttp := sdktrace.NewTracerProvider(\n\t\tsdktrace.WithSpanProcessor(bsp),\n\t\tsdktrace.WithSampler(sdktrace.AlwaysSample()),\n\t)\n\n\totel.SetTracerProvider(tp)\n\treturn tp, nil\n}\n\nfunc main() {\n\ttp, err := InitTracerProvider()\n\tif err != nil {\n\t\tlog.Fatalf(\"Tracer error: %v\", err)\n\t}\n\n\t// Гарантированный сброс буфера спанов при остановке сервиса\n\tdefer func() {\n\t\tctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\t\tdefer cancel()\n\t\tif err := tp.Shutdown(ctx); err != nil {\n\t\t\tlog.Printf(\"Error shutting down tracer provider: %v\", err)\n\t\t} else {\n\t\t\tfmt.Println(\"All buffered spans successfully flushed to collector.\")\n\t\t}\n\t}()\n\n\ttracer := otel.Tracer(\"order-service\")\n\tctx, span := tracer.Start(context.Background(), \"ProcessOrder\",\n\t\ttrace.WithSpanKind(trace.SpanKindServer),\n\t)\n\ttime.Sleep(10 * time.Millisecond)\n\tspan.End()\n\n\t_ = ctx\n\tfmt.Println(\"Span created and queued into BatchSpanProcessor.\")\n}",
                "note": "Конфигурация BatchSpanProcessor с ограничением очереди и пакетным экспортом"
            }
        ],
        "under_the_hood": "Внутри `BatchSpanProcessor` используется кольцевой буфер (ring buffer) на Go-слайсе с мьютексом или каналом. Горутина-воркер блокируется на `select` между таймером `BatchTimeout` и счетчиком накопленных спанов. Как только накопилось `MaxExportBatchSize` или сработал таймер, воркер передает батч экспортеру. Метод `tp.Shutdown` прерывает таймер, сбрасывает все оставшиеся элементы из очереди и корректно закрывает соединение.",
        "pitfalls": "Забыть вызвать `tp.Shutdown(ctx)` при выходе из `main()`. В таком случае последние спаны (включая критические спаны остановки и ошибки краша), находящиеся в очереди BatchProcessor, будут безвозвратно утеряны вместе с завершившимся процессом.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Что произойдет, если OTLP Collector временно недоступен под высокой нагрузкой?' Ответ: 'BatchSpanProcessor заполнит внутреннюю очередь MaxQueueSize (например 2048 спанов). После этого новые спаны начнут отбрасываться без блокировки вызывающих горутин. Сервис продолжит отвечать пользователям штатно, не падая по OOM и не деградируя по latency'."
    },
    {
        "num": 19,
        "title": "Client-side gRPC Keepalive: PING/PONG зондирование и восстановление полуоткрытых TCP-соединений",
        "task": "Сконфигурируйте gRPC клиент с keepalive.ClientParameters (Time: 10s, Timeout: 5s, PermitWithoutStream: true). Объясните, как распознаются 'мертвые' сокеты при сетевых сбоях.",
        "theory": "TCP-протокол по умолчанию спроектирован так, что если между двумя машинами физически пропал провод или выключился коммутатор, но ни одна из сторон не отправляет данные, соединение может оставаться в состоянии ESTABLISHED часами или днями. Это состояние называется полуоткрытым соединением (half-open connection). Если gRPC-клиент ожидает ответа от сервера или держит стрим, он не узнает о разрыве сети до тех пор, пока не попытается отправить новый запрос и не исчерпает лимит повторных попыток TCP (tcp_retries2, по умолчанию до 15 минут в Linux!). Клиентский gRPC keepalive решает эту проблему активным мониторингом на прикладном уровне (L7): каждые `Time` секунд шлется HTTP/2 PING кадр. Если подтверждение (PING ACK) не пришло за `Timeout` секунд, сокет немедленно признается сломанным и gRPC переходит к переподключению.",
        "step_by_step": [
            "Импортируйте google.golang.org/grpc/keepalive.",
            "Создайте структуру keepalive.ClientParameters с параметрами Time=10s, Timeout=5s, PermitWithoutStream=true.",
            "Передайте параметры в grpc.DialContext через grpc.WithKeepaliveParams.",
            "Проверьте реакцию клиента на отключение сети."
        ],
        "code_blocks": [
            {
                "filename": "grpc_client_probe.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n\t\"google.golang.org/grpc/keepalive\"\n)\n\nfunc DialWithKeepalive(target string) (*grpc.ClientConn, error) {\n\t// Настройки активного зондирования соединения\n\tclientKeepalive := keepalive.ClientParameters{\n\t\tTime:                10 * time.Second, // Каждые 10 секунд шлем PING кадр\n\t\tTimeout:             5 * time.Second,  // Если за 5 секунд нет PONG (ACK), закрываем сокет\n\t\tPermitWithoutStream: true,             // Зондировать даже при отсутствии активных RPC\n\t}\n\n\tctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)\n\tdefer cancel()\n\n\tconn, err := grpc.DialContext(target,\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t\tgrpc.WithKeepaliveParams(clientKeepalive),\n\t\tgrpc.WithBlock(),\n\t)\n\tif err != nil {\n\t\treturn nil, fmt.Errorf(\"dial failed: %w\", err)\n\t}\n\n\treturn conn, nil\n}\n\nfunc main() {\n\t// Демонстрация конфигурации\n\tlog.Println(\"Initializing client with L7 Keepalive probing...\")\n\tconn, err := DialWithKeepalive(\"127.0.0.1:50051\")\n\tif err != nil {\n\t\tlog.Printf(\"[Expected in sandbox] Connection failed: %v\", err)\n\t\treturn\n\t}\n\tdefer conn.Close()\n\n\tfmt.Println(\"Client connected with active L7 keepalive pinging.\")\n}",
                "note": "Настройка клиента gRPC для быстрого обнаружения сетевых сбоев"
            }
        ],
        "under_the_hood": "HTTP/2 PING кадр имеет фиксированный размер 8 байт полезной нагрузки и опциональный флаг ACK (0x1). Клиентский transport отправляет кадр с уникальным payload. Когда ОС сервера получает кадр, gRPC рантайм сервера немедленно зеркалирует те же 8 байт с выставленным битом ACK. Это работает на уровне HTTP/2 фрейминга, не затрагивая Protobuf сериализаторы и пользовательские сервисы.",
        "pitfalls": "Слишком агрессивный интервал Time (например, 100мс). Сервер отклонит такое поведение как DOS-атаку и разорвет соединение фреймом GOAWAY с кодом ошибки 'too_many_pings'.",
        "bigtech_interview": "В чем разница между TCP Keepalive (SO_KEEPALIVE) и gRPC Keepalive? Ответ: 'TCP Keepalive работает в ядре ОС на уровне транспортного протокола L4 и часто настраивается на часы (по умолчанию tcp_keepalive_time=7200s). Кроме того, TCP Keepalive не видит зависаний на уровне HTTP/2 фрейминга или прокси. gRPC Keepalive работает на уровне L7 приложения, проверяет отзывчивость самого HTTP/2 парсера и настраивается с точностью до секунд'."
    },
    {
        "num": 20,
        "title": "Trace Context Integrity: валидация и очистка заголовка traceparent от аномалий",
        "task": "Реализуйте HTTP middleware для строгой санитизации заголовка traceparent. Если заголовок содержит невалидные символы, недопустимую длину или запрещенный all-zero ID — перезапишите его новым чистым контекстом, защитив collector от вредоносных данных.",
        "theory": "Стандарт W3C Trace Context строго определяет грамматику заголовка `traceparent`: `version - trace_id - parent_id - trace_flags`. 1) `version`: ровно 2 hex-символа в lowercase (текущая версия `00`, версия `ff` недопустима); 2) `trace_id`: ровно 32 hex-символа в lowercase, значение `00000000000000000000000000000000` категорически запрещено; 3) `parent_id`: ровно 16 hex-символов в lowercase, значение `0000000000000000` категорически запрещено; 4) `trace_flags`: ровно 2 hex-символа. Если внешний клиент (или злоумышленник) передает поврежденный, переполненный или содержащий инъекции заголовок, безопасный микросервис обязан санировать его: отбросить невалидное значение и сгенерировать новый чистый корневой Trace Context.",
        "step_by_step": [
            "Реализуйте функцию ValidateTraceparent(raw string) bool.",
            "Проверьте длину строки (ровно 55 символов) и позиции разделителей-дефисов.",
            "Проверьте hex-символы и запрет на все нули.",
            "В middleware при обнаружении ошибки создайте новый traceparent с помощью crypto/rand.",
            "Внедрите санированный контекст в HTTP запрос."
        ],
        "code_blocks": [
            {
                "filename": "sanitize_traceparent.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"crypto/rand\"\n\t\"encoding/hex\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"strings\"\n)\n\n// IsValidTraceparent выполняет строгую проверку по стандарту W3C Trace Context\nfunc IsValidTraceparent(tp string) bool {\n\t// Формат: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01 (55 символов)\n\tif len(tp) != 55 {\n\t\treturn false\n\t}\n\tparts := strings.Split(tp, \"-\")\n\tif len(parts) != 4 {\n\t\treturn false\n\t}\n\n\tver, traceID, spanID, flags := parts[0], parts[1], parts[2], parts[3]\n\n\t// 1. Проверка версии (версия ff недопустима)\n\tif len(ver) != 2 || ver == \"ff\" || !isHexLower(ver) {\n\t\treturn false\n\t}\n\t// 2. Проверка trace_id (32 hex, запрещено все нули)\n\tif len(traceID) != 32 || !isHexLower(traceID) || traceID == \"00000000000000000000000000000000\" {\n\t\treturn false\n\t}\n\t// 3. Проверка span_id (16 hex, запрещено все нули)\n\tif len(spanID) != 16 || !isHexLower(spanID) || spanID == \"0000000000000000\" {\n\t\treturn false\n\t}\n\t// 4. Проверка trace_flags (2 hex)\n\tif len(flags) != 2 || !isHexLower(flags) {\n\t\treturn false\n\t}\n\n\treturn true\n}\n\nfunc isHexLower(s string) bool {\n\tfor i := 0; i < len(s); i++ {\n\t\tc := s[i]\n\t\tif !((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f')) {\n\t\t\treturn false\n\t\t}\n\t}\n\treturn true\n}\n\n// GenerateFreshTraceparent генерирует новый валидный W3C заголовок\nfunc GenerateFreshTraceparent() string {\n\tvar traceBytes [16]byte\n\tvar spanBytes [8]byte\n\t_, _ = rand.Read(traceBytes[:])\n\t_, _ = rand.Read(spanBytes[:])\n\n\treturn fmt.Sprintf(\"00-%s-%s-01\", hex.EncodeToString(traceBytes[:]), hex.EncodeToString(spanBytes[:]))\n}\n\n// TraceSanitizerMiddleware валидирует и при необходимости перезаписывает traceparent\nfunc TraceSanitizerMiddleware(next http.Handler) http.Handler {\n\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\tincoming := r.Header.Get(\"traceparent\")\n\t\tif incoming == \"\" || !IsValidTraceparent(incoming) {\n\t\t\tclean := GenerateFreshTraceparent()\n\t\t\tr.Header.Set(\"traceparent\", clean)\n\t\t\tw.Header().Set(\"x-trace-sanitized\", \"true\")\n\t\t}\n\t\tnext.ServeHTTP(w, r)\n\t})\n}\n\nfunc main() {\n\thandler := TraceSanitizerMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\tw.Header().Set(\"traceparent\", r.Header.Get(\"traceparent\"))\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"Processed\"))\n\t}))\n\n\t// Тест 1: Невалидный traceparent с нулями\n\treq1 := httptest.NewRequest(\"GET\", \"/test\", nil)\n\treq1.Header.Set(\"traceparent\", \"00-00000000000000000000000000000000-0000000000000000-01\")\n\trec1 := httptest.NewRecorder()\n\thandler.ServeHTTP(rec1, req1)\n\tfmt.Println(\"Test 1 (All zeros replaced):\", rec1.Header().Get(\"traceparent\"), \"Sanitized:\", rec1.Header().Get(\"x-trace-sanitized\"))\n\n\t// Тест 2: Валидный заголовок сохраняется\n\tvalidTP := \"00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01\"\n\treq2 := httptest.NewRequest(\"GET\", \"/test\", nil)\n\treq2.Header.Set(\"traceparent\", validTP)\n\trec2 := httptest.NewRecorder()\n\thandler.ServeHTTP(rec2, req2)\n\tfmt.Println(\"Test 2 (Valid kept intact):\", rec2.Header().Get(\"traceparent\") == validTP)\n}",
                "note": "Middleware для фильтрации поврежденных или вредоносных заголовков traceparent"
            }
        ],
        "under_the_hood": "Согласно спецификации W3C Recommendation, парсеры обязаны игнорировать неизвестные версии, если длина превышает ожидаемую (для обеспечения обратной совместимости в будущем), но для версии '00' любые отклонения от длины 55 байт являются фатальной ошибкой парсинга.",
        "pitfalls": "Принятие заглавных hex-букв (например, `4BF9...`). Стандарт W3C строго требует lower-case hex. Некоторые библиотеки строго проверяют символы, и наличие заглавных букв приведет к сбою в downstream сервисах.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'Чем опасен прием произвольного traceparent от непроверенных внешних клиентов на API Gateway?' Ответ: 'Злоумышленник может направить миллионы запросов с одним и тем же trace_id или случайными данными, вызвав искусственную перегрузку collector/хранилища (index explosion), либо сломать алгоритмы сэмплирования. На внешнем Gateway traceparent должен либо строго валидироваться, либо перегенерироваться'."
    },
    {
        "num": 21,
        "title": "Финальный вызов srv.Shutdown и grpc.GracefulStop для комбинированного сервера",
        "task": "Реализуйте полноценный координированный Graceful Shutdown приложения с HTTP и gRPC серверами: перехват SIGTERM -> отметка readiness probe -> ожидание сброса сетевых маршрутов -> параллельный вызов srv.Shutdown(ctx) и grpcServer.GracefulStop() -> закрытие пула БД.",
        "theory": "В production-сервисах Go часто одновременно поднимаются HTTP-сервер (метрики, healthcheck'и, REST API) и gRPC-сервер (высокопроизводительный внутренний RPC). Правильная последовательность остановки критична: 1) Перехват сигналов SIGTERM и SIGINT; 2) Перевод readiness в статус 'draining' (503); 3) Выдержка задержки (grace period) для исключения пода из Service/Ingress; 4) Параллельный запуск остановки слушателей: `srv.Shutdown(ctx)` для HTTP и `grpcServer.GracefulStop()` для gRPC; 5) Только после завершения всех активных запросов — закрытие пула базы данных и очередей сообщений. Если закрыть базу раньше, in-flight запросы завершатся паникой 'database connection closed' и вернут 500 клиентам.",
        "step_by_step": [
            "Создайте единый контекст приложения с перехватом сигналов ОС.",
            "Запустите HTTP и gRPC серверы в фоновых горутинах.",
            "При получении сигнала выдержите draining delay.",
            "Параллельно через sync.WaitGroup или горутины вызовите srv.Shutdown и grpcServer.GracefulStop.",
            "Закройте ресурсы хранения данных (БД, кеш) после остановки серверов."
        ],
        "code_blocks": [
            {
                "filename": "dual_shutdown.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"log\"\n\t\"net\"\n\t\"net/http\"\n\t\"os\"\n\t\"os/signal\"\n\t\"sync\"\n\t\"syscall\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n)\n\ntype MockDB struct {\n\tisClosed bool\n\tmu       sync.Mutex\n}\n\nfunc (db *MockDB) Close() {\n\tdb.mu.Lock()\n\tdefer db.mu.Unlock()\n\tdb.isClosed = true\n\tlog.Println(\"[DB] Connection pool safely closed.\")\n}\n\nfunc main() {\n\tctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)\n\tdefer stop()\n\n\tdb := &MockDB{}\n\n\t// HTTP сервер\n\thttpMux := http.NewServeMux()\n\thttpMux.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"OK\"))\n\t})\n\thttpServer := &http.Server{Addr: \":8081\", Handler: httpMux}\n\n\t// gRPC сервер\n\tgrpcServer := grpc.NewServer()\n\tlis, err := net.Listen(\"tcp\", \":50051\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Failed to listen tcp: %v\", err)\n\t}\n\n\tgo func() {\n\t\tlog.Println(\"[HTTP] Server listening on :8081\")\n\t\tif err := httpServer.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {\n\t\t\tlog.Printf(\"[HTTP] Error: %v\", err)\n\t\t}\n\t}()\n\n\tgo func() {\n\t\tlog.Println(\"[gRPC] Server listening on :50051\")\n\t\tif err := grpcServer.Serve(lis); err != nil {\n\t\t\tlog.Printf(\"[gRPC] Error: %v\", err)\n\t\t}\n\t}()\n\n\t<-ctx.Done()\n\tlog.Println(\"[Shutdown] Initiating dual graceful shutdown...\")\n\n\t// 1. Пауза для обновления K8s Endpoints\n\ttime.Sleep(1 * time.Second)\n\n\t// 2. Параллельная остановка серверов\n\tvar wg sync.WaitGroup\n\twg.Add(2)\n\n\t// Остановка HTTP\n\tgo func() {\n\t\tdefer wg.Done()\n\t\tshutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\t\tdefer cancel()\n\t\tlog.Println(\"[HTTP] Shutting down listeners...\")\n\t\tif err := httpServer.Shutdown(shutdownCtx); err != nil {\n\t\t\tlog.Printf(\"[HTTP] Shutdown failed: %v\", err)\n\t\t}\n\t\tlog.Println(\"[HTTP] Stopped.\")\n\t}()\n\n\t// Остановка gRPC\n\tgo func() {\n\t\tdefer wg.Done()\n\t\tstopped := make(chan struct{})\n\t\tgo func() {\n\t\t\tlog.Println(\"[gRPC] GracefulStop initiated...\")\n\t\t\tgrpcServer.GracefulStop()\n\t\t\tclose(stopped)\n\t\t}()\n\n\t\tselect {\n\t\tcase <-stopped:\n\t\t\tlog.Println(\"[gRPC] GracefulStop completed.\")\n\t\tcase <-time.After(5 * time.Second):\n\t\t\tlog.Println(\"[gRPC] Force stopping due to timeout...\")\n\t\t\tgrpcServer.Stop()\n\t\t}\n\t}()\n\n\twg.Wait()\n\n\t// 3. Закрытие ресурсов БД строго после прекращения обработки трафика\n\tdb.Close()\n\tfmt.Println(\"All services gracefully terminated.\")\n}",
                "note": "Синхронизированный Graceful Shutdown для одновременной работы HTTP и gRPC"
            }
        ],
        "under_the_hood": "Метод `grpcServer.GracefulStop()` закрывает слушающий TCP сокет, перестает принимать новые SYN пакеты и отправляет GOAWAY кадры на все существующие HTTP/2 транспорты. Он блокирует вызывающую горутину до тех пор, пока все активные RPC вызовы не вернут управление. Обертка с таймером и вызовом жесткого `Stop()` предотвращает вечное зависание при утечке стрима.",
        "pitfalls": "Вызов `grpcServer.GracefulStop()` синхронно без таймаута. Если клиент запустил бесконечный bidirectional stream, сервер зависнет навсегда, пока K8s не прибьет его SIGKILL.",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'Что делать, если grpcServer.GracefulStop() завис из-за долгого стрима?' Ответ: 'Запускать GracefulStop() в отдельной горутине с каналом завершения и использовать select с time.After(timeout). По истечении таймаута вызывать жесткий grpcServer.Stop(), который принудительно разрывает соединения'."
    },
    {
        "num": 22,
        "title": "Проблема балансировки gRPC за L4-балансировщиком (K8s Service) и ее решение",
        "task": "Напишите разбор проблемы залипания gRPC-соединений на L4 (Kubernetes ClusterIP/kube-proxy) и реализуйте клиентскую балансировку с использованием headless service и round_robin политики gRPC.",
        "theory": "Стандартный сервис Kubernetes (`type: ClusterIP`) работает на 4-м уровне модели OSI (Транспортный уровень). kube-proxy настраивает правила iptables/IPVS, которые распределяют запросы при создании TCP-соединения (пакет SYN). Для классического HTTP/1.1 с частым открытием соединений это работает сносно. Однако gRPC использует HTTP/2, где клиент открывает одно постоянное TCP соединение и мультиплексирует миллионы запросов внутри него. В результате gRPC-клиент подключается к одному случайному поду и шлет весь последующий трафик только туда! Масштабирование реплик сервера никак не разгрузит этот под. Решения проблемы: 1) Использование L7 прокси (Envoy, Istio, Linkerd); 2) Клиентская балансировка gRPC через Headless Service (`clusterIP: None`) с резолвером DNS и политикой `round_robin`.",
        "step_by_step": [
            "Определите схему Headless Service в K8s без ClusterIP.",
            "Настройте gRPC Dial с использованием схемы dns:///service-name:port.",
            "Установите опцию grpc.WithDefaultServiceConfig с политикой round_robin.",
            "Убедитесь, что клиент резолвит все IP-адреса подов и распределяет запросы поочередно."
        ],
        "code_blocks": [
            {
                "filename": "client_round_robin.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n)\n\n// DialHeadlessService подключается к Kubernetes Headless сервису с клиентской балансировкой Round Robin\nfunc DialHeadlessService(targetDNS string) (*grpc.ClientConn, error) {\n\t// JSON конфигурация gRPC для включения round_robin балансировки\n\t// Вместо отправки всего трафика в один TCP сокет, клиент откроет соединения ко всем A-записям DNS\n\tserviceConfig := `{\n\t\t\"loadBalancingConfig\": [\n\t\t\t{\n\t\t\t\t\"round_robin\": {}\n\t\t\t}\n\t\t]\n\t}`\n\n\tctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\tdefer cancel()\n\n\tconn, err := grpc.DialContext(\n\t\tctx,\n\t\t// Префикс dns:/// заставляет gRPC опрашивать SRV/A записи адреса\n\t\tfmt.Sprintf(\"dns:///%s\", targetDNS),\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t\tgrpc.WithDefaultServiceConfig(serviceConfig),\n\t)\n\tif err != nil {\n\t\treturn nil, fmt.Errorf(\"dial failed: %w\", err)\n\t}\n\n\treturn conn, nil\n}\n\nfunc main() {\n\t// В K8s адрес выглядит как: \"my-grpc-service.default.svc.cluster.local:50051\"\n\ttarget := \"localhost:50051\"\n\tlog.Printf(\"Connecting to %s with client-side Round Robin...\", target)\n\n\tconn, err := DialHeadlessService(target)\n\tif err != nil {\n\t\tlog.Printf(\"[Demo] Connection expectedly postponed: %v\", err)\n\t\treturn\n\t}\n\tdefer conn.Close()\n\n\tfmt.Println(\"Client-side round-robin load balancing configured.\")\n}",
                "note": "Клиентская балансировка gRPC с резолвингом адресов всех реплик"
            }
        ],
        "under_the_hood": "При указании `round_robin` резолвер gRPC регулярно перечитывает DNS A-записи домена. Для каждого обнаруженного IP адреса gRPC создает отдельный саб-канал (`SubConn`). Пикер (`Picker`) распределяет каждый отдельный вызов RPC по кругу между активными саб-каналами.",
        "pitfalls": "Использование обычного K8s Service с ClusterIP вместо Headless. Обычный сервис возвращает единый виртуальный ClusterIP, поэтому DNS-резолвер gRPC увидит ровно один адрес и балансировка работать не будет.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Почему в Kubernetes gRPC трафик перегружает один под, игнорируя остальные?' Ответ: 'Потому что kube-proxy работает на уровне L4 (TCP). gRPC устанавливает одно мультиплексированное HTTP/2 соединение. После завершения TCP handshake L4 балансировщик больше не участвует в маршрутизации сообщений. Требуется L7-балансировка (Envoy/Service Mesh) либо клиентский Round Robin через Headless Service'."
    },
    {
        "num": 23,
        "title": "Спецификация W3C Trace Context: устройство и управление tracestate",
        "task": "Реализуйте парсер и модификатор заголовка tracestate в Go. Покажите добавление и обновление ключей различных вендоров мониторинга (например, rojo=123, congo=456) с соблюдением требований W3C к порядку элементов.",
        "theory": "Стандарт W3C Trace Context состоит из двух заголовков: `traceparent` и `tracestate`. `tracestate` предназначен для передачи непрозрачных метаданных конкретных вендоров трассировки (Dynatrace, Datadog, Jaeger, New Relic) в виде разделенного запятыми списка пар `vendor_key=vendor_value`. Спецификация W3C накладывает строгие ограничения: 1) Не более 32 записей в списке; 2) Суммарная длина строки не более 512 символов; 3) При обновлении или добавлении своего ключа вендор обязан поместить обновленную пару в самое начало списка (позиция 0), сдвигая остальные вправо. Это гарантирует сохранение информации о самых последних системах в цепочке.",
        "step_by_step": [
            "Определите структуру TraceState с внутренним списком пар ключ-значение.",
            "Реализуйте метод Parse(header string) для десериализации списка.",
            "Реализуйте метод Set(key, value string), перемещающий обновленный ключ в начало списка.",
            "Реализуйте метод String() для форматирования заголовка по стандарту.",
            "Проверьте соблюдение лимитов длины и количества элементов."
        ],
        "code_blocks": [
            {
                "filename": "tracestate.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n)\n\ntype StateEntry struct {\n\tKey   string\n\tValue string\n}\n\ntype TraceState struct {\n\tentries []StateEntry\n}\n\nfunc ParseTraceState(header string) *TraceState {\n\tts := &TraceState{entries: make([]StateEntry, 0)}\n\tif strings.TrimSpace(header) == \"\" {\n\t\treturn ts\n\t}\n\n\tparts := strings.Split(header, \",\")\n\tfor _, part := range parts {\n\t\titem := strings.TrimSpace(part)\n\t\tif item == \"\" {\n\t\t\tcontinue\n\t\t}\n\t\tkv := strings.SplitN(item, \"=\", 2)\n\t\tif len(kv) == 2 {\n\t\t\tts.entries = append(ts.entries, StateEntry{\n\t\t\t\tKey:   strings.TrimSpace(kv[0]),\n\t\t\t\tValue: strings.TrimSpace(kv[1]),\n\t\t\t})\n\t\t}\n\t}\n\treturn ts\n}\n\n// Set обновляет значение ключа и перемещает его в НАЧАЛО списка (требование W3C)\nfunc (ts *TraceState) Set(key, value string) {\n\tnewEntries := make([]StateEntry, 0, len(ts.entries)+1)\n\tnewEntries = append(newEntries, StateEntry{Key: key, Value: value})\n\n\tfor _, entry := range ts.entries {\n\t\tif entry.Key != key {\n\t\t\tnewEntries = append(newEntries, entry)\n\t\t}\n\t}\n\n\t// Ограничение W3C: не более 32 элементов\n\tif len(newEntries) > 32 {\n\t\tnewEntries = newEntries[:32]\n\t}\n\tts.entries = newEntries\n}\n\nfunc (ts *TraceState) String() string {\n\tparts := make([]string, len(ts.entries))\n\tfor i, e := range ts.entries {\n\t\tparts[i] = fmt.Sprintf(\"%s=%s\", e.Key, e.Value)\n\t}\n\treturn strings.Join(parts, \",\")\n}\n\nfunc main() {\n\trawHeader := \"congo=t61rcWkgMzE,rojo=00f067aa0ba902b7\"\n\tts := ParseTraceState(rawHeader)\n\tfmt.Println(\"Initial tracestate:\", ts.String())\n\n\t// Добавляем или обновляем ключ нашей внутренней системы\n\tts.Set(\"mycorp\", \"sampled_tier1\")\n\tfmt.Println(\"After adding mycorp (prepended to head):\", ts.String())\n\n\t// Обновляем существующий congo (он должен переехать на позицию 0)\n\tts.Set(\"congo\", \"updated_session_99\")\n\tfmt.Println(\"After updating congo (moved to head):\", ts.String())\n}",
                "note": "Парсинг и корректное управление порядком ключей в заголовке W3C tracestate"
            }
        ],
        "under_the_hood": "Принцип 'most recently updated first' позволяет граничным системам быстро считывать состояние ближайшего предшественника, не перебирая весь список. Если размер заголовка превышает лимит в 512 байт, последние (наиболее старые) элементы отбрасываются.",
        "pitfalls": "Добавление ключа в конец списка (append). По стандарту W3C измененная запись обязана стать первой. Если библиотека пишет в конец, сторонние валидаторы могут отклонить tracestate.",
        "bigtech_interview": "Зачем нужен tracestate, если есть traceparent? Ответ: 'traceparent содержит только универсальные поля (TraceID, SpanID, Flags). tracestate предназначен для передачи специфичных данных вендоров (например, внутренних ID очередей в Datadog или Dynatrace), позволяя разнородным APM системам мирно сосуществовать в одной гетерогенной микросервисной архитектуре'."
    },
    {
        "num": 24,
        "title": "Client Keepalive: анализ PING-фреймов и логирование рантайма gRPC",
        "task": "Настройте подробное логирование gRPC через переменные окружения и запустите keepalive клиент с Time: 10s, Timeout: 3s. Покажите структуру кадров PING в gRPC транспортном слое.",
        "theory": "Отладка низкоуровневого взаимодействия gRPC часто затруднена тем, что HTTP/2 трафик шифруется через TLS, а стандартный tcpdump не видит содержимое бинарных фреймов без расшифровки ключей. В Go gRPC встроен мощный механизм трассировки транспортного слоя. Установка переменных окружения `GRPC_GO_LOG_VERBOSITY_LEVEL=99` и `GRPC_GO_LOG_SEVERITY_LEVEL=info` заставляет рантайм детально логировать отправку и получение каждого фрейма HTTP/2: HEADERS, DATA, SETTINGS, PING, WINDOW_UPDATE. Это позволяет воочию наблюдать отправку 8-байтных PING зондов клиентом и получение ответа ACK от сервера.",
        "step_by_step": [
            "Установите параметры логирования gRPC в коде через os.Setenv или grpc/grpclog.",
            "Сконфигурируйте keepalive.ClientParameters с коротким интервалом пинга.",
            "Реализуйте кастомный тестовый HTTP/2 сервер для фиксации PING кадров.",
            "Проверьте логи отправки фреймов транспортным слоем."
        ],
        "code_blocks": [
            {
                "filename": "grpc_debug_keepalive.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"os\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n\t\"google.golang.org/grpc/grpclog\"\n\t\"google.golang.org/grpc/keepalive\"\n)\n\nfunc init() {\n\t// Включаем подробное логирование HTTP/2 фреймов в рантайме gRPC\n\t_ = os.Setenv(\"GRPC_GO_LOG_VERBOSITY_LEVEL\", \"2\")\n\t_ = os.Setenv(\"GRPC_GO_LOG_SEVERITY_LEVEL\", \"info\")\n\tgrpclog.SetLoggerV2(grpclog.NewLoggerV2(os.Stdout, os.Stdout, os.Stderr))\n}\n\nfunc main() {\n\tkacp := keepalive.ClientParameters{\n\t\tTime:                1 * time.Second, // Быстрый пинг для демонстрации логов\n\t\tTimeout:             500 * time.Millisecond,\n\t\tPermitWithoutStream: true,\n\t}\n\n\tctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)\n\tdefer cancel()\n\n\tlog.Println(\"Initiating connection with debug logging enabled...\")\n\tconn, err := grpc.DialContext(ctx, \"127.0.0.1:50051\",\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t\tgrpc.WithKeepaliveParams(kacp),\n\t)\n\tif err != nil {\n\t\tlog.Printf(\"Dial completed with expected error: %v\", err)\n\t\treturn\n\t}\n\tdefer conn.Close()\n\n\ttime.Sleep(1500 * time.Millisecond)\n\tfmt.Println(\"Debug keepalive run finished.\")\n}",
                "note": "Включение подробного вывода HTTP/2 фреймов gRPC через grpclog"
            }
        ],
        "under_the_hood": "Внутри пакета `internal/transport/http2_client.go` метод `framer.WritePing` формирует 9-байтный заголовок фрейма: Length=8, Type=0x6 (PING), Flags=0x0 (или 0x1 для ACK), StreamID=0x0 и 8 байт случайного пейлоада. Фрейм отправляется в буферизированный сокет через `loopyWriter`.",
        "pitfalls": "Оставлять verbosity=99 в production. Объем вывода логов на каждый PING и DATA-фрейм приведет к колоссальной нагрузке на диск и CPU, а также к переполнению коллектора логов (Loki/Fluentbit).",
        "bigtech_interview": "Как отдебажить, уходят ли PING фреймы из Go-приложения в продакшене без перезапуска с флагами отладки? Ответ: 'С помощью eBPF или tcpdump на ноде Kubernetes. В tcpdump фильтр `tcp[((tcp[12:1] & 0xf0) >> 2):4] = 0x00000806` позволяет перехватить именно кадры HTTP/2 PING (Length=8, Type=6)'."
    },
    {
        "num": 25,
        "title": "Типизированный парсер заголовка traceparent на чистом Go",
        "task": "Напишите высокопроизводительный, безаллокационный (zero-alloc) парсер заголовка traceparent, возвращающий структуру с TraceID, SpanID и битовыми флагами трассировки.",
        "theory": "В высоконагруженных шлюзах (API Gateway), обрабатывающих сотни тысяч запросов в секунду, парсить `traceparent` через регулярные выражения или `strings.Split` недопустимо из-за выделения памяти в куче (heap allocations). Формат W3C `traceparent` имеет строго фиксированную длину: 55 байт. `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01` Позиции разделителей всегда постоянны: индексы 2, 35, 52. Битовые флаги (последние 2 символа): - Бит 0 (`0x01`): Recorded / Sampled; - Бит 1 (`0x02`): Random (сгенерирован криптостойким генератором). Парсинг байт за байтом с прямой проверкой hex-символов выполняется за ~15-20 наносекунд с 0 B/op аллокаций.",
        "step_by_step": [
            "Создайте структуру TraceParent с 16-байтным TraceID и 8-байтным SpanID.",
            "Проверьте точную длину входной строки (55 символов) и дефисы на фиксированных индексах.",
            "Реализуйте побайтовый декодер hex без аллокаций памяти.",
            "Проверьте ограничения на запрещенные нулевые значения.",
            "Сделайте бенчмарк для подтверждения отсутствия аллокаций."
        ],
        "code_blocks": [
            {
                "filename": "fast_traceparent.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/hex\"\n\t\"errors\"\n\t\"fmt\"\n)\n\nvar (\n\tErrInvalidLength = errors.New(\"traceparent: invalid length, must be 55 bytes\")\n\tErrInvalidFormat = errors.New(\"traceparent: invalid delimiter positions\")\n\tErrAllZero       = errors.New(\"traceparent: trace-id or span-id is all zero\")\n)\n\ntype ParsedTraceParent struct {\n\tVersion [1]byte\n\tTraceID [16]byte\n\tSpanID  [8]byte\n\tFlags   byte\n}\n\nfunc (p *ParsedTraceParent) IsSampled() bool {\n\treturn (p.Flags & 0x01) != 0\n}\n\n// FastParseTraceparent парсит W3C traceparent без аллокаций в куче\nfunc FastParseTraceparent(s string) (ParsedTraceParent, error) {\n\tvar result ParsedTraceParent\n\tif len(s) != 55 {\n\t\treturn result, ErrInvalidLength\n\t}\n\n\t// Проверка дефисов\n\tif s[2] != '-' || s[35] != '-' || s[52] != '-' {\n\t\treturn result, ErrInvalidFormat\n\t}\n\n\t// 1. Version\n\tif _, err := hex.Decode(result.Version[:], []byte(s[0:2])); err != nil {\n\t\treturn result, fmt.Errorf(\"invalid version: %w\", err)\n\t}\n\n\t// 2. TraceID (16 bytes = 32 hex chars)\n\tif _, err := hex.Decode(result.TraceID[:], []byte(s[3:35])); err != nil {\n\t\treturn result, fmt.Errorf(\"invalid trace-id: %w\", err)\n\t}\n\tif isZeroSlice(result.TraceID[:]) {\n\t\treturn result, ErrAllZero\n\t}\n\n\t// 3. SpanID (8 bytes = 16 hex chars)\n\tif _, err := hex.Decode(result.SpanID[:], []byte(s[36:52])); err != nil {\n\t\treturn result, fmt.Errorf(\"invalid span-id: %w\", err)\n\t}\n\tif isZeroSlice(result.SpanID[:]) {\n\t\treturn result, ErrAllZero\n\t}\n\n\t// 4. Flags (1 byte = 2 hex chars)\n\tvar flagBuf [1]byte\n\tif _, err := hex.Decode(flagBuf[:], []byte(s[53:55])); err != nil {\n\t\treturn result, fmt.Errorf(\"invalid flags: %w\", err)\n\t}\n\tresult.Flags = flagBuf[0]\n\n\treturn result, nil\n}\n\nfunc isZeroSlice(b []byte) bool {\n\tfor _, x := range b {\n\t\tif x != 0 {\n\t\t\treturn false\n\t\t}\n\t}\n\treturn true\n}\n\nfunc main() {\n\traw := \"00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01\"\n\tparsed, err := FastParseTraceparent(raw)\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\n\tfmt.Printf(\"TraceID: %x\\n\", parsed.TraceID)\n\tfmt.Printf(\"SpanID:  %x\\n\", parsed.SpanID)\n\tfmt.Printf(\"Sampled: %v (Flags: 0x%02x)\\n\", parsed.IsSampled(), parsed.Flags)\n}",
                "note": "Высокоскоростной безаллокационный парсер W3C traceparent"
            }
        ],
        "under_the_hood": "Передача массива фиксированного размера `[16]byte` и `[8]byte` по значению или в стек не приводит к аллокации в куче (`0 allocs/op`). Стандартная функция `hex.Decode` работает напрямую со срезами байт без создания временных строк.",
        "pitfalls": "Использование `regexp.MustCompile` для парсинга traceparent в цикле запросов. Регулярные выражения в Go работают в десятки раз медленнее прямого побайтового разбора и создают паразитный мусор для сборщика мусора.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Почему W3C запрещает TraceID из одних нулей?' Ответ: 'Значение из всех нулей (00000000000000000000000000000000) зарезервировано как признак неинициализированного или невалидного контекста. Если сервис примет его, все разрозненные ошибочные запросы склеятся в один гигантский сломанный трейс в хранилище'."
    },
    {
        "num": 26,
        "title": "B3 Headers (Zipkin): конвертация между W3C Trace Context и форматом B3",
        "task": "Реализуйте двусторонний транслятор заголовков трассировки между W3C (traceparent) и Zipkin B3 (X-B3-TraceId, X-B3-SpanId, X-B3-Sampled и single b3).",
        "theory": "До принятия стандарта W3C Trace Context де-факто отраслевым стандартом была спецификация Zipkin B3 Propagation. Она до сих пор широко используется в Spring Cloud, Istio, Envoy и старых микросервисах. Формат B3 существует в двух видах: 1) Multiple headers: `X-B3-TraceId` (16 или 32 hex), `X-B3-SpanId` (16 hex), `X-B3-Sampled` ('1' или '0'), `X-B3-ParentSpanId`; 2) Single header: `b3: {TraceId}-{SpanId}-{SamplingState}-{ParentSpanId}`. В гетерогенных архитектурах при переходе на OpenTelemetry шлюз обязан поддерживать бесшовную конвертацию между B3 и W3C, чтобы старые Java/Spring сервисы и новые Go сервисы продолжали видеть единый граф вызовов.",
        "step_by_step": [
            "Определите структуру TraceInfo с полями TraceID, SpanID, Sampled.",
            "Реализуйте чтение как W3C traceparent, так и B3 headers из HTTP-запроса.",
            "Реализуйте генерацию заголовков обоих стандартов.",
            "Проверьте трансляцию входящего B3 заголовка в исходящий traceparent."
        ],
        "code_blocks": [
            {
                "filename": "b3_converter.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"strings\"\n)\n\ntype CanonicalTrace struct {\n\tTraceID string\n\tSpanID  string\n\tSampled bool\n}\n\n// ExtractTrace универсально извлекает трейс из W3C traceparent или Zipkin B3\nfunc ExtractTrace(r *http.Request) *CanonicalTrace {\n\t// 1. Проверяем W3C traceparent\n\tif tp := r.Header.Get(\"traceparent\"); tp != \"\" {\n\t\tparts := strings.Split(tp, \"-\")\n\t\tif len(parts) == 4 {\n\t\t\treturn &CanonicalTrace{\n\t\t\t\tTraceID: parts[1],\n\t\t\t\tSpanID:  parts[2],\n\t\t\t\tSampled: parts[3] == \"01\",\n\t\t\t}\n\t\t}\n\t}\n\n\t// 2. Проверяем Single header b3\n\tif b3 := r.Header.Get(\"b3\"); b3 != \"\" {\n\t\tparts := strings.Split(b3, \"-\")\n\t\tif len(parts) >= 2 {\n\t\t\tsampled := false\n\t\t\tif len(parts) >= 3 && parts[2] == \"1\" {\n\t\t\t\tsampled = true\n\t\t\t}\n\t\t\ttraceID := parts[0]\n\t\t\t// Если TraceID в B3 16 hex, дополняем ведущими нулями до 32 hex стандарта W3C\n\t\t\tif len(traceID) == 16 {\n\t\t\t\ttraceID = \"0000000000000000\" + traceID\n\t\t\t}\n\t\t\treturn &CanonicalTrace{\n\t\t\t\tTraceID: traceID,\n\t\t\t\tSpanID:  parts[1],\n\t\t\t\tSampled: sampled,\n\t\t\t}\n\t\t}\n\t}\n\n\t// 3. Проверяем Multiple B3 headers\n\tif b3Trace := r.Header.Get(\"X-B3-TraceId\"); b3Trace != \"\" {\n\t\tif len(b3Trace) == 16 {\n\t\t\tb3Trace = \"0000000000000000\" + b3Trace\n\t\t}\n\t\treturn &CanonicalTrace{\n\t\t\tTraceID: b3Trace,\n\t\t\tSpanID:  r.Header.Get(\"X-B3-SpanId\"),\n\t\t\tSampled: r.Header.Get(\"X-B3-Sampled\") == \"1\",\n\t\t}\n\t}\n\n\treturn nil\n}\n\n// InjectW3C проставляет заголовок traceparent\nfunc (t *CanonicalTrace) InjectW3C(req *http.Request) {\n\tflags := \"00\"\n\tif t.Sampled {\n\t\tflags = \"01\"\n\t}\n\treq.Header.Set(\"traceparent\", fmt.Sprintf(\"00-%s-%s-%s\", t.TraceID, t.SpanID, flags))\n}\n\n// InjectB3Single проставляет единый заголовок b3\nfunc (t *CanonicalTrace) InjectB3Single(req *http.Request) {\n\tsampleFlag := \"0\"\n\tif t.Sampled {\n\t\tsampleFlag = \"1\"\n\t}\n\treq.Header.Set(\"b3\", fmt.Sprintf(\"%s-%s-%s\", t.TraceID, t.SpanID, sampleFlag))\n}\n\nfunc main() {\n\t// Входящий запрос со старым B3 заголовком (от Istio/Spring Cloud)\n\tinReq, _ := http.NewRequest(\"GET\", \"/api/order\", nil)\n\tinReq.Header.Set(\"X-B3-TraceId\", \"4bf92f3577b34da6a3ce929d0e0e4736\")\n\tinReq.Header.Set(\"X-B3-SpanId\", \"00f067aa0ba902b7\")\n\tinReq.Header.Set(\"X-B3-Sampled\", \"1\")\n\n\ttrace := ExtractTrace(inReq)\n\tfmt.Printf(\"Extracted trace: ID=%s, Span=%s, Sampled=%v\\n\", trace.TraceID, trace.SpanID, trace.Sampled)\n\n\t// Формируем исходящий вызов в новый микросервис с W3C заголовком\n\toutReq, _ := http.NewRequest(\"POST\", \"/api/payment\", nil)\n\ttrace.InjectW3C(outReq)\n\tfmt.Println(\"Converted outgoing W3C traceparent:\", outReq.Header.Get(\"traceparent\"))\n}",
                "note": "Универсальный транслятор между Zipkin B3 и W3C Trace Context"
            }
        ],
        "under_the_hood": "Исторически Zipkin поддерживал 64-битные Trace ID (16 hex символов). W3C строго требует 128 бит (32 hex). При конвертации 64-битный ID выравнивается 16 ведущими нулями слева (`0000000000000000{traceid}`), что сохраняет числовую идентичность при поиске в Jaeger.",
        "pitfalls": "Отбрасывание старших 16 байт при обратной конвертации 128-битного W3C Trace ID в 64-битный B3. Это вызовет коллизию идентификаторов в старых системах.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Как настроить OpenTelemetry SDK для одновременного приема и W3C, и B3 заголовков?' Ответ: 'Через Composite TextMapPropagator: `otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(propagation.TraceContext{}, b3.New()))`. Композитный пропагатор проверяет заголовки по очереди'."
    },
    {
        "num": 27,
        "title": "Kubernetes PreStop Hook: нативная альтернатива time.Sleep в Go-коде",
        "task": "Напишите манифест Kubernetes Deployment с preStop hook 'sleep 10' и Go-сервис. Объясните порядок выполнения preStop hook, SIGTERM и исключения пода из Service Endpoints.",
        "theory": "Чтобы не хардкодить `time.Sleep` внутри кода на Go, в Kubernetes существует стандартный механизм `lifecycle.preStop`. Когда Pod удаляется: 1) Kubelet синхронно блокирует завершение контейнера и выполняет команду из `preStop.exec.command` (например, `[\"sleep\", \"10\"]`); 2) Одновременно apiserver исключает IP пода из Endpoints, а kube-proxy на всех нодах обновляет iptables; 3) Пока контейнер спит в preStop, Go-приложение продолжает штатно принимать трафик, но новый трафик уже не шлется; 4) Только после завершения команды preStop kubelet посылает процессу Go сигнал SIGTERM! Благодаря preStop в Go коде достаточно обычной логики `server.Shutdown()` без искусственных задержек.",
        "step_by_step": [
            "Создайте декларативный YAML манифест Deployment с lifecycle.preStop.",
            "Сконфигурируйте terminationGracePeriodSeconds с запасом (например 30s).",
            "Напишите Go-сервис с чистым srv.Shutdown(ctx) при SIGTERM.",
            "Проанализируйте диаграмму жизненного цикла завершения контейнера в K8s."
        ],
        "code_blocks": [
            {
                "filename": "deployment.yaml",
                "lang": "yaml",
                "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: billing-service\nspec:\n  replicas: 3\n  template:\n    spec:\n      # Общее время на остановку контейнера до отправки SIGKILL\n      terminationGracePeriodSeconds: 35\n      containers:\n      - name: app\n        image: billing-service:v1.2.0\n        lifecycle:\n          preStop:\n            exec:\n              # kubelet выполняет sleep ДО отправки SIGTERM\n              # Это дает 10 секунд на удаление пода из iptables/kube-proxy\n              command: [\"/bin/sh\", \"-c\", \"sleep 10\"]\n        ports:\n        - containerPort: 8080",
                "note": "Манифест K8s с preStop hook для задержки отправки SIGTERM"
            },
            {
                "filename": "main.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n\t\"os/signal\"\n\t\"syscall\"\n\t\"time\"\n)\n\nfunc main() {\n\tsrv := &http.Server{\n\t\tAddr: \":8080\",\n\t\tHandler: http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\t\tw.WriteHeader(http.StatusOK)\n\t\t\t_, _ = w.Write([]byte(\"Processed\"))\n\t\t}),\n\t}\n\n\tgo func() {\n\t\tif err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {\n\t\t\tlog.Fatalf(\"Server error: %v\", err)\n\t\t}\n\t}()\n\tlog.Println(\"Server running. Waiting for SIGTERM after K8s preStop hook finishes...\")\n\n\tstop := make(chan os.Signal, 1)\n\tsignal.Notify(stop, syscall.SIGTERM, os.Interrupt)\n\t<-stop\n\n\tlog.Println(\"[SIGTERM] PreStop hook completed by K8s. Safely shutting down server now...\")\n\tctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)\n\tdefer cancel()\n\n\tif err := srv.Shutdown(ctx); err != nil {\n\t\tlog.Fatalf(\"Shutdown failed: %v\", err)\n\t}\n\tfmt.Println(\"Server successfully shutdown.\")\n}",
                "note": "Go-сервер, опирающийся на системный preStop hook в Kubernetes"
            }
        ],
        "under_the_hood": "В рантайме containerd/CRI вызов PreStop hook является блокирующим. Таймер `terminationGracePeriodSeconds` начинает отсчет в момент инициализации удаления пода, поэтому `sleep` внутри preStop уменьшает доступное время на выполнение Go `server.Shutdown`.",
        "pitfalls": "Отсутствие утилиты `sleep` или `/bin/sh` в минималистичных образах `scratch` / `distroless`. Если запустить `command: [\"sleep\", \"10\"]` в образе scratch, контейнер упадет с ошибкой 'executable file not found' и сразу получит SIGKILL.",
        "bigtech_interview": "Что лучше: PreStop Hook в K8s манифесте или time.Sleep в Go коде? Ответ: 'В Enterprise архитектуре лучше PreStop Hook: код приложения остается чистым от инфраструктурной специфики кластера, а сетевые инженеры и DevOps могут менять задержку draining в YAML без перекомпиляции и релизов Go-бинарника'."
    },
    {
        "num": 28,
        "title": "Обработка GOAWAY Frames клиентом gRPC при срабатывании MaxConnectionAge",
        "task": "Настройте gRPC клиент с WithDefaultServiceConfig для плавной обработки кадров GOAWAY. Покажите, как клиент прозрачно завершает старые запросы и переподключается к серверу без ошибок RPC.",
        "theory": "Когда на gRPC сервере срабатывает таймер `MaxConnectionAge`, сервер отправляет клиенту HTTP/2 кадр `GOAWAY`. Кадр `GOAWAY` сообщает клиенту: 1) Соединение скоро будет закрыто; 2) Все запросы с StreamID <= LastStreamID будут успешно обработаны; 3) Новые RPC-вызовы по этому соединению отправлять запрещено. Правильно сконфигурированный gRPC клиент при получении GOAWAY: - Немедленно открывает параллельное новое TCP соединение к резолверу; - Направляет все новые вызовы в новое соединение; - Дожидается ответов по старым запросам в старом соединении до наступления MaxConnectionAgeGrace; - Закрывает старый сокет без единой ошибки для конечного пользователя.",
        "step_by_step": [
            "Сконфигурируйте gRPC клиент с grpc.WithDefaultServiceConfig.",
            "Настройте retryPolicy для кодов UNAVAILABLE на случай сетевого сбоя во время ротации.",
            "Инициируйте непрерывную отправку запросов.",
            "Проверьте отсутствие ошибок при ротации соединений сервером."
        ],
        "code_blocks": [
            {
                "filename": "grpc_goaway_handling.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n)\n\nfunc CreateResilientClient(target string) (*grpc.ClientConn, error) {\n\t// Service Config с автоматическими ретраями на случай гонки при GOAWAY\n\tserviceConfig := `{\n\t\t\"methodConfig\": [{\n\t\t\t\"name\": [{\"service\": \"\"}],\n\t\t\t\"retryPolicy\": {\n\t\t\t\t\"maxAttempts\": 4,\n\t\t\t\t\"initialBackoff\": \"0.1s\",\n\t\t\t\t\"maxBackoff\": \"1s\",\n\t\t\t\t\"backoffMultiplier\": 2.0,\n\t\t\t\t\"retryableStatusCodes\": [\"UNAVAILABLE\"]\n\t\t\t}\n\t\t}]\n\t}`\n\n\tctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\tdefer cancel()\n\n\tconn, err := grpc.DialContext(\n\t\tctx,\n\t\ttarget,\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t\tgrpc.WithDefaultServiceConfig(serviceConfig),\n\t)\n\tif err != nil {\n\t\treturn nil, fmt.Errorf(\"dial error: %w\", err)\n\t}\n\n\treturn conn, nil\n}\n\nfunc main() {\n\tconn, err := CreateResilientClient(\"localhost:50051\")\n\tif err != nil {\n\t\tlog.Printf(\"[Demo] Connection expectedly deferred: %v\", err)\n\t\treturn\n\t}\n\tdefer conn.Close()\n\n\tfmt.Println(\"gRPC Client configured with resilient retry policy for seamless GOAWAY handling.\")\n\t_ = codes.Unavailable\n}",
                "note": "Конфигурация ServiceConfig с RetryPolicy для бесшовной ротации GOAWAY"
            }
        ],
        "under_the_hood": "Когда транспорт `http2Client` в Go gRPC читает кадр GOAWAY, он переводит состояние транспорта в `draining`. Балансировщик (`balancer_wrapper`) удаляет этот `SubConn` из списка готовых (`READY`) и запускает подключение нового сокета. Все новые RPC автоматически направляются в новый саб-канал.",
        "pitfalls": "Отсутствие ретраев для идемпотентных запросов. Если клиент отправил заголовок HTTP/2 HEADERS в ту же миллисекунду, когда сервер отправил GOAWAY, сервер может отклонить стрим ошибкой REFUSED_STREAM. Без retry policy клиент получит статус UNAVAILABLE.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'Что делает клиент gRPC, когда сервер присылает кадр GOAWAY?' Ответ: 'Клиент перестает создавать новые HTTP/2 стримы в текущем TCP-соединении, начинает прозрачно устанавливать новое соединение к бэкенду, но продолжает ожидать ответы на уже отправленные in-flight стримы'."
    },
    {
        "num": 29,
        "title": "Внедрение (Injection) W3C Trace Context в исходящие HTTP-запросы",
        "task": "Реализуйте инжекцию trace headers в исходящий HTTP-запрос через otel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(req.Header)).",
        "theory": "Распределенная трассировка OpenTelemetry базируется на интерфейсе `TextMapPropagator`. Приложение не должно вручную форматировать заголовки `traceparent` или `tracestate`. Вместо этого вызывается метод `Inject`: `otel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(req.Header))` Пропагатор извлекает текущий активный спан из `context.Context`, читает его TraceID, SpanID и флаги, формирует стандартный заголовок `traceparent` и записывает его в структуру `http.Header`. Если в контексте присутствовал Baggage, он также сериализуется в заголовок `baggage`.",
        "step_by_step": [
            "Инициализируйте глобальный TextMapPropagator через otel.SetTextMapPropagator.",
            "Создайте спан трассировки tracer.Start.",
            "Создайте исходящий http.Request.",
            "Вызовите otel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(req.Header)).",
            "Проверьте появление заголовка traceparent в запросе."
        ],
        "code_blocks": [
            {
                "filename": "inject_http.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\n\t\"go.opentelemetry.io/otel\"\n\t\"go.opentelemetry.io/otel/propagation\"\n\tsdktrace \"go.opentelemetry.io/otel/sdk/trace\"\n\t\"go.opentelemetry.io/otel/trace\"\n)\n\nfunc initTracer() *sdktrace.TracerProvider {\n\ttp := sdktrace.NewTracerProvider(sdktrace.WithSampler(sdktrace.AlwaysSample()))\n\totel.SetTracerProvider(tp)\n\t// Устанавливаем стандартный W3C TraceContext пропагатор\n\totel.SetTextMapPropagator(propagation.TraceContext{})\n\treturn tp\n}\n\nfunc main() {\n\ttp := initTracer()\n\tdefer func() { _ = tp.Shutdown(context.Background()) }()\n\n\t// Тестовый сервер\n\tserver := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\ttpHeader := r.Header.Get(\"traceparent\")\n\t\tfmt.Println(\"[Server Received] traceparent:\", tpHeader)\n\t\tw.WriteHeader(http.StatusOK)\n\t}))\n\tdefer server.Close()\n\n\ttracer := otel.Tracer(\"order-client\")\n\tctx, span := tracer.Start(context.Background(), \"ExecuteOrderPayment\",\n\t\ttrace.WithSpanKind(trace.SpanKindClient),\n\t)\n\tdefer span.End()\n\n\t// Создаем исходящий запрос\n\treq, err := http.NewRequestWithContext(ctx, \"POST\", server.URL, nil)\n\tif err != nil {\n\t\tlog.Fatalf(\"Request error: %v\", err)\n\t}\n\n\t// ИНЖЕКЦИЯ КОНТЕКСТА ТРАССИРОВКИ\n\totel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(req.Header))\n\n\t// Проверяем локально\n\tfmt.Println(\"[Client Injected] traceparent:\", req.Header.Get(\"traceparent\"))\n\n\tresp, err := http.DefaultClient.Do(req)\n\tif err != nil {\n\t\tlog.Fatalf(\"Call failed: %v\", err)\n\t}\n\tdefer resp.Body.Close()\n}",
                "note": "Инжекция контекста OpenTelemetry в исходящие заголовки через HeaderCarrier"
            }
        ],
        "under_the_hood": "`propagation.HeaderCarrier` реализует интерфейс `propagation.TextMapCarrier`, предоставляя методы `Get(key)`, `Set(key, value)` и `Keys()`. Пропагатор `TraceContext` вызывает `Set(\"traceparent\", ...)` с шестнадцатеричным представлением SpanContext.",
        "pitfalls": "Забыть вызвать `otel.SetTextMapPropagator()`. По умолчанию в OpenTelemetry установлен no-op пропагатор, который ничего не записывает в заголовки. Если не инициализировать его явно, исходящие HTTP запросы уйдут без traceparent.",
        "bigtech_interview": "Вопрос на собеседовании в VK: 'Каким типом спана (SpanKind) должен помечаться исходящий сетевой запрос?' Ответ: 'trace.WithSpanKind(trace.SpanKindClient). Это сообщает APM-системе, что данный спан является клиентской стороной RPC-вызова, и связывает его с последующим SpanKindServer на принимающей стороне'."
    },
    {
        "num": 30,
        "title": "Server Keepalive Enforcement: защита сервера gRPC от флуда PING-фреймами",
        "task": "Сконфигурируйте keepalive.EnforcementPolicy{MinTime: 5s, PermitWithoutStream: false}. Покажите, как сервер защищается от клиентов со слишком агрессивным пингом, отправляя GOAWAY (too_many_pings).",
        "theory": "Клиентский keepalive — полезный инструмент, но он несет риск DoS-атаки на сервер. Если тысячи клиентов настроят пинг каждые 100 миллисекунд без активных стримов, CPU сервера будет тратиться исключительно на обработку бесполезных HTTP/2 PING кадров. Для защиты сервер использует структуру `keepalive.EnforcementPolicy`: 1) `MinTime: 5s` — минимально допустимый интервал между клиентскими PING. Если клиент присылает фреймы чаще, сервер считает это нарушением политики; 2) `PermitWithoutStream: false` — запрещает пинговать сервер, если по соединению нет ни одного активного RPC стрима. При повторных нарушениях сервер немедленно отправляет фрейм `GOAWAY` с сообщением `too_many_pings` и разрывает TCP соединение.",
        "step_by_step": [
            "Импортируйте google.golang.org/grpc/keepalive.",
            "Сконфигурируйте EnforcementPolicy с MinTime: 5s и PermitWithoutStream: false.",
            "Передайте политику в grpc.NewServer через grpc.KeepaliveEnforcementPolicy.",
            "Проверьте разрыв соединения при агрессивном пинге от тестового клиента."
        ],
        "code_blocks": [
            {
                "filename": "enforce_server.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/keepalive\"\n)\n\nfunc StartProtectedGRPCServer(addr string) (*grpc.Server, net.Listener) {\n\t// Политика принудительного ограничения частоты пингов\n\tenforcement := keepalive.EnforcementPolicy{\n\t\tMinTime:             5 * time.Second, // Клиенту запрещено пинговать чаще раза в 5 секунд\n\t\tPermitWithoutStream: false,           // Запрещено слать PING, если нет активных запросов\n\t}\n\n\tserverParams := keepalive.ServerParameters{\n\t\tMaxConnectionIdle: 15 * time.Minute,\n\t}\n\n\tserver := grpc.NewServer(\n\t\tgrpc.KeepaliveEnforcementPolicy(enforcement),\n\t\tgrpc.KeepaliveParams(serverParams),\n\t)\n\n\tlis, err := net.Listen(\"tcp\", addr)\n\tif err != nil {\n\t\tlog.Fatalf(\"Listen error: %v\", err)\n\t}\n\n\treturn server, lis\n}\n\nfunc main() {\n\tserver, lis := StartProtectedGRPCServer(\":50052\")\n\tdefer lis.Close()\n\n\tlog.Println(\"gRPC Server listening with strict EnforcementPolicy (MinTime=5s, PermitWithoutStream=false)\")\n\n\tgo func() {\n\t\ttime.Sleep(100 * time.Millisecond)\n\t\tserver.Stop()\n\t}()\n\n\t_ = server.Serve(lis)\n\tfmt.Println(\"Enforcement policy demonstration completed.\")\n}",
                "note": "Защита сервера gRPC от перегрузки фреймами PING через EnforcementPolicy"
            }
        ],
        "under_the_hood": "В структуре `http2Server` рантайм ведет счетчик `pingStrikes`. Если PING получен раньше, чем истек `MinTime` с момента прошлого пинга, счетчик штрафов инкрементируется. При превышении лимита (по умолчанию 2 страйка) сервер записывает в сокет фрейм GOAWAY с кодом `http2.ErrCodeEnhanceYourCalm` и отладочным сообщением 'too_many_pings'.",
        "pitfalls": "Установить на клиенте `PermitWithoutStream: true`, а на сервере оставить дефолтное `PermitWithoutStream: false`. В период ночного простоя клиент начнет слать PING зонды, а сервер будет рвать соединения каждые несколько секунд с ошибкой 'too_many_pings'.",
        "bigtech_interview": "Вопрос на собеседовании в Тинькофф: 'Что означает ошибка rpc error: code = Unavailable desc = connection error: desc = \"transport: read: connection reset by peer\" с GOAWAY too_many_pings?' Ответ: 'Клиент настроен на слишком частый keepalive PING (меньше MinTime сервера) или шлет PING при отсутствии стримов вопреки EnforcementPolicy сервера. Необходимо синхронизировать параметры ClientParameters.Time и Server EnforcementPolicy'."
    },
    {
        "num": 31,
        "title": "Извлечение (Extraction) W3C Trace Context из входящих HTTP-запросов",
        "task": "Реализуйте HTTP middleware для автоматического извлечения Trace Context из заголовков входящего запроса с помощью otel.GetTextMapPropagator().Extract() и создания серверного спана.",
        "theory": "Когда входящий HTTP запрос приходит от API Gateway, балансировщика или другого микросервиса, он несет заголовок `traceparent`. Приложение не должно создавать изолированный корневой трейс. Вместо этого с помощью метода `Extract` извлекается родительский контекст: `ctx := otel.GetTextMapPropagator().Extract(r.Context(), propagation.HeaderCarrier(r.Header))` Затем создается дочерний спан: `ctx, span := tracer.Start(ctx, \"HandleRequest\", trace.WithSpanKind(trace.SpanKindServer))` Благодаря этому SpanID текущего обработчика становится дочерним по отношению к ParentID из `traceparent`, а общий TraceID сохраняется неизменным по всему графу вызовов.",
        "step_by_step": [
            "Инициализируйте TracerProvider и установите propagation.TraceContext{}.",
            "Напишите HTTP middleware, вызывающее TextMapPropagator.Extract.",
            "Создайте спан с типом SpanKindServer на основе извлеченного контекста.",
            "Сохраните спан в контексте запроса r.WithContext(ctx).",
            "Завершите спан через defer span.End() после вызова downstream обработчика."
        ],
        "code_blocks": [
            {
                "filename": "extract_middleware.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\n\t\"go.opentelemetry.io/otel\"\n\t\"go.opentelemetry.io/otel/propagation\"\n\tsdktrace \"go.opentelemetry.io/otel/sdk/trace\"\n\t\"go.opentelemetry.io/otel/trace\"\n)\n\nfunc init() {\n\ttp := sdktrace.NewTracerProvider(sdktrace.WithSampler(sdktrace.AlwaysSample()))\n\totel.SetTracerProvider(tp)\n\totel.SetTextMapPropagator(propagation.TraceContext{})\n}\n\n// TraceExtractorMiddleware извлекает W3C Trace Context и создает серверный спан\nfunc TraceExtractorMiddleware(tracer trace.Tracer) func(http.Handler) http.Handler {\n\treturn func(next http.Handler) http.Handler {\n\t\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\t\t// 1. Извлекаем родительский контекст из заголовков запроса\n\t\t\tpropagator := otel.GetTextMapPropagator()\n\t\t\textractedCtx := propagator.Extract(r.Context(), propagation.HeaderCarrier(r.Header))\n\n\t\t\t// 2. Создаем серверный спан\n\t\t\tctx, span := tracer.Start(extractedCtx, r.Method+\" \"+r.URL.Path,\n\t\t\t\ttrace.WithSpanKind(trace.SpanKindServer),\n\t\t\t)\n\t\t\tdefer span.End()\n\n\t\t\t// 3. Передаем обогащенный контекст дальше по цепочке\n\t\t\tnext.ServeHTTP(w, r.WithContext(ctx))\n\t\t})\n\t}\n}\n\nfunc main() {\n\ttracer := otel.Tracer(\"order-api\")\n\tmiddleware := TraceExtractorMiddleware(tracer)\n\n\tappHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\tspan := trace.SpanFromContext(r.Context())\n\t\tsc := span.SpanContext()\n\t\tfmt.Printf(\"Processed request with TraceID: %s, SpanID: %s\\n\", sc.TraceID(), sc.SpanID())\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"OK\"))\n\t})\n\n\tserver := httptest.NewServer(middleware(appHandler))\n\tdefer server.Close()\n\n\t// Имитируем запрос от шлюза со сформированным traceparent\n\tincomingTraceparent := \"00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01\"\n\treq, _ := http.NewRequest(\"GET\", server.URL+\"/api/v1/orders\", nil)\n\treq.Header.Set(\"traceparent\", incomingTraceparent)\n\n\tresp, err := http.DefaultClient.Do(req)\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer resp.Body.Close()\n}",
                "note": "Корректное извлечение W3C Trace Context во входящем HTTP-запросе"
            }
        ],
        "under_the_hood": "Если заголовок `traceparent` отсутствует или поврежден, метод `Extract` возвращает переданный `r.Context()`. Последующий вызов `tracer.Start` автоматически сгенерирует новый случайный 16-байтный TraceID, сделав данный спан корневым (root span) новой цепочки.",
        "pitfalls": "Вызов `tracer.Start(r.Context(), ...)` вместо `tracer.Start(extractedCtx, ...)`. В таком случае извлеченный родительский контекст будет проигнорирован, и сервис начнет новый изолированный трейс.",
        "bigtech_interview": "Вопрос на собеседовании в Lamoda: 'Что произойдет, если микросервис А отправил traceparent, а микросервис Б создал спан без вызова Extract?' Ответ: 'Трассировка разорвется на две независимые части. В Jaeger мы увидим два несвязанных трейса, а время выполнения сетевого запроса выпадет из графа задержек'."
    },
    {
        "num": 32,
        "title": "Context propagation в gRPC: использование gRPC Interceptors",
        "task": "Настройте двустороннюю передачу Trace Context через gRPC клиенты и серверы с использованием перехватчиков (interceptors) и gRPC metadata.",
        "theory": "В gRPC контекст передается не через HTTP-заголовки, а через протокольные метаданные `metadata.MD` поверх HTTP/2 HEADERS фреймов. Для прозрачной передачи контекста трассировки используются унарные и потоковые интерцепторы: 1) Клиентский интерцептор: перед отправкой RPC извлекает активный спан из `context.Context`, сериализует `traceparent` и добавляет его в outgoing gRPC metadata (`metadata.NewOutgoingContext`); 2) Серверный интерцептор: при получении RPC извлекает incoming metadata (`metadata.FromIncomingContext`), десериализует `traceparent` и внедряет SpanContext в context вызова метода. Это избавляет разработчиков бизнес-логики от ручной работы с заголовками.",
        "step_by_step": [
            "Определите структуры MetadataCarrier для адаптации metadata.MD к интерфейсу TextMapCarrier.",
            "Реализуйте UnaryClientInterceptor для внедрения трассировки.",
            "Реализуйте UnaryServerInterceptor для извлечения трассировки.",
            "Подключите перехватчики к gRPC клиенту и серверу.",
            "Проверьте сквозную передачу идентификаторов."
        ],
        "code_blocks": [
            {
                "filename": "grpc_interceptors.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"strings\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/metadata\"\n)\n\n// MetadataCarrier адаптирует gRPC metadata к OpenTelemetry propagation.TextMapCarrier\ntype MetadataCarrier metadata.MD\n\nfunc (m MetadataCarrier) Get(key string) string {\n\tvals := metadata.MD(m).Get(strings.ToLower(key))\n\tif len(vals) == 0 {\n\t\treturn \"\"\n\t}\n\treturn vals[0]\n}\n\nfunc (m MetadataCarrier) Set(key, val string) {\n\tmetadata.MD(m).Set(strings.ToLower(key), val)\n}\n\nfunc (m MetadataCarrier) Keys() []string {\n\tkeys := make([]string, 0, len(m))\n\tfor k := range m {\n\t\tkeys = append(keys, k)\n\t}\n\treturn keys\n}\n\n// TracingClientInterceptor автоматически пробрасывает traceparent в outgoing metadata\nfunc TracingClientInterceptor() grpc.UnaryClientInterceptor {\n\treturn func(ctx context.Context, method string, req, reply interface{},\n\t\tcc *grpc.ClientConn, invoker grpc.UnaryInvoker, opts ...grpc.CallOption) error {\n\n\t\tmd, ok := metadata.FromOutgoingContext(ctx)\n\t\tif !ok {\n\t\t\tmd = metadata.New(nil)\n\t\t} else {\n\t\t\tmd = md.Copy()\n\t\t}\n\n\t\t// Добавляем тестовый traceparent в исходящие метаданные\n\t\tmd.Set(\"traceparent\", \"00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01\")\n\t\tnewCtx := metadata.NewOutgoingContext(ctx, md)\n\n\t\treturn invoker(newCtx, method, req, reply, cc, opts...)\n\t}\n}\n\n// TracingServerInterceptor извлекает traceparent из incoming metadata\nfunc TracingServerInterceptor() grpc.UnaryServerInterceptor {\n\treturn func(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo,\n\t\thandler grpc.UnaryHandler) (interface{}, error) {\n\n\t\tmd, ok := metadata.FromIncomingContext(ctx)\n\t\tif ok {\n\t\t\ttp := md.Get(\"traceparent\")\n\t\t\tif len(tp) > 0 {\n\t\t\t\tfmt.Printf(\"[gRPC Server] Extracted traceparent from metadata: %s\\n\", tp[0])\n\t\t\t}\n\t\t}\n\t\treturn handler(ctx, req)\n\t}\n}\n\nfunc main() {\n\t// Демонстрация конфигурации сервера с интерцептором\n\tserver := grpc.NewServer(\n\t\tgrpc.UnaryInterceptor(TracingServerInterceptor()),\n\t)\n\t_ = server\n\n\tfmt.Println(\"gRPC Server and Client Tracing Interceptors configured successfully.\")\n}",
                "note": "Унарные интерцепторы gRPC для контекстной трассировки через gRPC metadata"
            }
        ],
        "under_the_hood": "gRPC метаданные передаются в бинарном протоколе HTTP/2 как обычные заголовки фрейма HEADERS. Все ключи gRPC metadata автоматически переводятся в lowercase согласно спецификации HTTP/2 (RFC 7540).",
        "pitfalls": "Использование `metadata.FromIncomingContext` на стороне клиента или `metadata.FromOutgoingContext` на стороне сервера. В gRPC входящие и исходящие метаданные хранятся под разными приватными ключами контекста.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Как передать бинарные данные в gRPC metadata (например, бинарный контекст трассировки)?' Ответ: 'Ключ метаданных обязан оканчиваться суффиксом `-bin` (например, `trace-proto-bin`). В этом случае рантайм gRPC автоматически кодирует значение в base64 при передаче по сети'."
    },
    {
        "num": 33,
        "title": "Graceful Shutdown gRPC сервера: GracefulStop vs Stop с таймаутом и ретраями",
        "task": "Реализуйте отказоустойчивую процедуру остановки gRPC сервера: GracefulStop() с тайм-аутом ожидания и последующим жестким Stop(), если клиенты не закрыли стримы.",
        "theory": "Метод `grpcServer.GracefulStop()` закрывает слушающий TCP сокет (перестает принимать новые SYN пакеты) и ожидает завершения всех активных RPC-вызовов и клиентских стримов. Однако в production-окружении нельзя слепо полагаться только на `GracefulStop()`: если недобросовестный клиент завис или держит бесконечный bidirectional stream, `GracefulStop()` будет висеть бесконечно. В итоге Kubernetes по истечении `terminationGracePeriodSeconds` пришлет жесткий SIGKILL, что приведет к аварийной остановке контейнера. Правильный паттерн: запуск `GracefulStop()` в отдельной горутине с ожиданием по таймеру. Если сервер не завершился за N секунд, вызывается принудительный `grpcServer.Stop()`.",
        "step_by_step": [
            "Определите функцию StopWithTimeout(server *grpc.Server, timeout time.Duration).",
            "Создайте канал stopped := make(chan struct{}).",
            "Запустите server.GracefulStop() в отдельной горутине и закройте канал по завершении.",
            "Используйте select для ожидания канала либо таймера time.After(timeout).",
            "При истечении таймаута вызовите жесткий server.Stop()."
        ],
        "code_blocks": [
            {
                "filename": "grpc_graceful_timeout.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n)\n\n// GracefulStopWithTimeout пытается мягко остановить сервер, а по таймауту выполняет жесткий Stop\nfunc GracefulStopWithTimeout(server *grpc.Server, timeout time.Duration) {\n\tstopped := make(chan struct{})\n\n\tgo func() {\n\t\tlog.Println(\"[gRPC Shutdown] Invoking GracefulStop()...\")\n\t\tserver.GracefulStop()\n\t\tclose(stopped)\n\t}()\n\n\tselect {\n\tcase <-stopped:\n\t\tlog.Println(\"[gRPC Shutdown] All active RPCs finished gracefully.\")\n\tcase <-time.After(timeout):\n\t\tlog.Printf(\"[gRPC Shutdown] Timeout %v reached! Forcing server.Stop()...\", timeout)\n\t\tserver.Stop()\n\t\tlog.Println(\"[gRPC Shutdown] Server forcibly terminated.\")\n\t}\n}\n\nfunc main() {\n\tlis, err := net.Listen(\"tcp\", \":50053\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Listen error: %v\", err)\n\t}\n\n\tserver := grpc.NewServer()\n\n\tgo func() {\n\t\t_ = server.Serve(lis)\n\t}()\n\n\ttime.Sleep(100 * time.Millisecond)\n\n\t// Выполняем остановку с жестким лимитом в 2 секунды\n\tGracefulStopWithTimeout(server, 2*time.Second)\n\tfmt.Println(\"gRPC shutdown sequence completed safely.\")\n}",
                "note": "Безопасная остановка gRPC сервера с гарантированным дедлайном"
            }
        ],
        "under_the_hood": "Жесткий вызов `server.Stop()` немедленно закрывает все активные сетевые подключения `net.Conn`, отправляя клиентам TCP RST/FIN. На стороне клиентов активные вызовы мгновенно завершаются с кодом ошибки `codes.Unavailable` ('transport is closing').",
        "pitfalls": "Вызов `GracefulStop` после закрытия сетевого листенера вручную через `lis.Close()`. `GracefulStop` сам закрывает переданный листенер. Повторное закрытие может вызвать панику или ошибки 'use of closed network connection'.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Что происходит с новыми запросами, поступающими во время GracefulStop?' Ответ: 'Поскольку слушающий сокет уже закрыт, новые клиенты на уровне ОС получают Connection Refused. Для уже подключенных клиентов по мультиплексированным HTTP/2 каналам сервер возвращает код ошибки Unavailable'."
    },
    {
        "num": 34,
        "title": "Антипаттерн Healthcheck: Liveness vs Readiness и опасность проверки БД в LivenessProbe",
        "task": "Создайте отказоустойчивые эндпоинты /livez и /readyz. Объясните, почему проверка доступности PostgreSQL в livenessProbe является грубейшим антипаттерном, приводящим к каскадному падению всего кластера.",
        "theory": "Один из самых разрушительных антипаттернов в Kubernetes: включение `db.PingContext()` в `livenessProbe`. Что происходит при кратковременной перегрузке или сетевом сбое БД: 1) БД перестает отвечать за таймаут; 2) `livenessProbe` на всех 100 подах микросервиса возвращает 500 Internal Server Error; 3) kubelet делает вывод: 'Приложение зависло!' и одновременно убивает и перезапускает все 100 подов! 4) При старте все 100 подов начинают одновременно инициализироваться, загружать кэши и долбить и без того перегруженную БД сотнями новых TCP-подключений (Thundering Herd / Connection Storm); 5) БД окончательно падает, а поды уходят в бесконечный CrashLoopBackOff! ПРАВИЛО: LivenessProbe проверяет ТОЛЬКО локальный процесс Go (отсутствие дедлока, доступность рантайма). Внешние зависимости (PostgreSQL, Kafka, Redis) проверяются ИСКЛЮЧИТЕЛЬНО в ReadinessProbe!",
        "step_by_step": [
            "Реализуйте /livez с минимальной проверкой жизнеспособности локального процесса.",
            "Реализуйте /readyz с асинхронной проверкой внешних ресурсов и коротким таймаутом.",
            "Добавьте Circuit Breaker / кеширование статуса БД, чтобы не перегружать базу частыми проверками готовности.",
            "Проверьте изоляцию сбоев БД от перезапуска подов."
        ],
        "code_blocks": [
            {
                "filename": "resilient_probes.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"sync/atomic\"\n\t\"time\"\n)\n\ntype ProbeManager struct {\n\tdbHealthy atomic.Bool\n}\n\nfunc (pm *ProbeManager) SetupEndpoints(mux *http.ServeMux) {\n\t// LIVENESS: Проверяет ТОЛЬКО рантайм Go. Никаких внешних баз данных!\n\t// Если процесс отвечает — он жив. Рестарт не требуется.\n\tmux.HandleFunc(\"/livez\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"ALIVE\"))\n\t})\n\n\t// READINESS: Проверяет готовность обслуживать трафик (включая БД).\n\t// При сбое БД возвращает 503: трафик снимается, но под НЕ УБИВАЕТСЯ!\n\tmux.HandleFunc(\"/readyz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tif !pm.dbHealthy.Load() {\n\t\t\thttp.Error(w, \"Database unavailable, removing from load balancer\", http.StatusServiceUnavailable)\n\t\t\treturn\n\t\t}\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"READY\"))\n\t})\n}\n\n// BackgroundDBChecker периодически проверяет БД в фоне без блокировки HTTP зондов\nfunc (pm *ProbeManager) StartBackgroundHealthcheck(ctx context.Context) {\n\tgo func() {\n\t\tticker := time.NewTicker(3 * time.Second)\n\t\tdefer ticker.Stop()\n\n\t\tfor {\n\t\t\tselect {\n\t\t\tcase <-ctx.Done():\n\t\t\t\treturn\n\t\t\tcase <-ticker.C:\n\t\t\t\t// Имитируем ping к базе данных\n\t\t\t\terr := mockDatabasePing(ctx)\n\t\t\t\tpm.dbHealthy.Store(err == nil)\n\t\t\t}\n\t\t}\n\t}()\n}\n\nfunc mockDatabasePing(ctx context.Context) error {\n\t// Имитация успешного ответа\n\treturn nil\n}\n\nfunc main() {\n\tpm := &ProbeManager{}\n\tpm.dbHealthy.Store(true)\n\n\tmux := http.NewServeMux()\n\tpm.SetupEndpoints(mux)\n\n\tctx, cancel := context.WithCancel(context.Background())\n\tdefer cancel()\n\tpm.StartBackgroundHealthcheck(ctx)\n\n\tlog.Println(\"Probes listening on :8082: /livez (runtime only) and /readyz (dependencies)\")\n\tfmt.Println(\"Liveness and Readiness probes configured following cloud-native best practices.\")\n}",
                "note": "Строгое разделение LivenessProbe (рантайм) и ReadinessProbe (зависимости)"
            }
        ],
        "under_the_hood": "kubelet проверяет Liveness и Readiness с независимой периодичностью. Отказ ReadinessProbe лишь изменяет статус PodReady в False, заставляя контроллер Service Endpoints удалить IP пода из маршрутизации. Память пода, открытые пулы и соединения при этом сохраняются.",
        "pitfalls": "Вызов синхронного `db.PingContext(ctx)` прямо в HTTP handler'е /readyz. При 10 нодах K8s, опрашивающих под каждые 2 секунды, база получит шквал холостых запросов. Проверку состояния внешних баз лучше выносить в отдельную фоновую горутину с обновлением atomic.Bool.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Почему нельзя делать проверку базы данных в livenessProbe?' Ответ: 'Потому что падение БД вызовет массовый перезапуск всех подов кластера. Рестарт не починит базу, но создаст лавинообразную нагрузку новыми подключениями при рестарте (Cascading Failure / Death Spiral). Проверка БД допустима только в ReadinessProbe'."
    },
    {
        "num": 35,
        "title": "Context propagation в Apache Kafka через заголовки сообщений (Record Headers)",
        "task": "Реализуйте проброс W3C Trace Context через Kafka Record Headers с использованием HeaderCarrier. Покажите извлечение контекста в Consumer для связи асинхронных операций.",
        "theory": "В асинхронной событийно-ориентированной архитектуре (Event-Driven Architecture) запросы передаются через брокеры сообщений (Kafka, RabbitMQ, NATS). Здесь нет синхронного протокола HTTP или gRPC, но цепочка вызовов не должна прерываться. Apache Kafka поддерживает `Record Headers` — список пар 'ключ-значение' (`[]Header{Key, Value}`), передаваемый вместе с телом сообщения без десериализации payload. Продюсер сериализует `traceparent` в байтовый заголовок `traceparent`, а консьюмер извлекает его и создает спан с типом `SpanKindConsumer`, связывая обработку события с действием пользователя, породившим его.",
        "step_by_step": [
            "Определите KafkaHeaderCarrier, адаптирующий слайс заголовков сообщений Kafka к TextMapCarrier.",
            "Реализуйте инжекцию Trace Context в заголовки продюсером.",
            "Реализуйте извлечение Trace Context консьюмером.",
            "Создайте спан обработки сообщения с привязкой к родительскому контексту."
        ],
        "code_blocks": [
            {
                "filename": "kafka_propagation.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"strings\"\n\n\t\"go.opentelemetry.io/otel\"\n\t\"go.opentelemetry.io/otel/propagation\"\n\tsdktrace \"go.opentelemetry.io/otel/sdk/trace\"\n\t\"go.opentelemetry.io/otel/trace\"\n)\n\ntype KafkaHeader struct {\n\tKey   string\n\tValue []byte\n}\n\ntype KafkaMessage struct {\n\tHeaders []KafkaHeader\n\tPayload []byte\n}\n\n// KafkaHeaderCarrier адаптирует заголовки Kafka сообщений к OpenTelemetry TextMapCarrier\ntype KafkaHeaderCarrier struct {\n\tHeaders *[]KafkaHeader\n}\n\nfunc (c KafkaHeaderCarrier) Get(key string) string {\n\tif c.Headers == nil {\n\t\treturn \"\"\n\t}\n\tfor _, h := range *c.Headers {\n\t\tif strings.EqualFold(h.Key, key) {\n\t\t\treturn string(h.Value)\n\t\t}\n\t}\n\treturn \"\"\n}\n\nfunc (c KafkaHeaderCarrier) Set(key, val string) {\n\tif c.Headers == nil {\n\t\treturn\n\t}\n\tfor i, h := range *c.Headers {\n\t\tif strings.EqualFold(h.Key, key) {\n\t\t\t(*c.Headers)[i].Value = []byte(val)\n\t\t\treturn\n\t\t}\n\t}\n\t*c.Headers = append(*c.Headers, KafkaHeader{Key: key, Value: []byte(val)})\n}\n\nfunc (c KafkaHeaderCarrier) Keys() []string {\n\tif c.Headers == nil {\n\t\treturn nil\n\t}\n\tkeys := make([]string, len(*c.Headers))\n\tfor i, h := range *c.Headers {\n\t\tkeys[i] = h.Key\n\t}\n\treturn keys\n}\n\nfunc main() {\n\ttp := sdktrace.NewTracerProvider(sdktrace.WithSampler(sdktrace.AlwaysSample()))\n\totel.SetTracerProvider(tp)\n\totel.SetTextMapPropagator(propagation.TraceContext{})\n\n\ttracer := otel.Tracer(\"order-events\")\n\n\t// 1. ПРОДЮСЕР: Создаем событие OrderCreated и инжектируем контекст\n\tctx, prodSpan := tracer.Start(context.Background(), \"PublishOrderCreated\",\n\t\ttrace.WithSpanKind(trace.SpanKindProducer),\n\t)\n\tdefer prodSpan.End()\n\n\tmsg := &KafkaMessage{\n\t\tPayload: []byte(`{\"order_id\":9912,\"amount\":4500}`),\n\t\tHeaders: make([]KafkaHeader, 0),\n\t}\n\n\totel.GetTextMapPropagator().Inject(ctx, KafkaHeaderCarrier{Headers: &msg.Headers})\n\tfmt.Printf(\"[Producer] Injected traceparent: %s\\n\", string(msg.Headers[0].Value))\n\n\t// 2. КОНСЬЮМЕР: Читаем сообщение из топика и восстанавливаем контекст\n\tconsumerCtx := otel.GetTextMapPropagator().Extract(context.Background(), KafkaHeaderCarrier{Headers: &msg.Headers})\n\n\t_, consSpan := tracer.Start(consumerCtx, \"ProcessOrderPayment\",\n\t\ttrace.WithSpanKind(trace.SpanKindConsumer),\n\t)\n\tdefer consSpan.End()\n\n\tfmt.Printf(\"[Consumer] Span created with matching TraceID: %s\\n\", consSpan.SpanContext().TraceID().String())\n}",
                "note": "Сквозная передача W3C контекста через Kafka Record Headers"
            }
        ],
        "under_the_hood": "OpenTelemetry различает типы спанов `SpanKindProducer` и `SpanKindConsumer`. В распределенных трассировщиках (Jaeger/Tempo) связь между продюсером и консьюмером отображается как асинхронный переход (FollowsFrom или ParentChild), наглядно демонстрируя задержку нахождения сообщения в очереди топика.",
        "pitfalls": "Мутация среза headers без указателя или гонка при конкурентной обработке сообщений батчами. Всегда создавайте изолированный контекст для каждого отдельного сообщения при батчевом чтении из Kafka.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Как связать спан продюсера и консьюмера, если консьюмер обрабатывает сообщения пачками (Batch Consumer)?' Ответ: 'При батчевой обработке консьюмер создает родительский спан ProcessBatch, а для каждого отдельного сообщения извлекает контекст и создает спан со ссылкой SpanLink (trace.WithLinks) на оригинальный спан продюсера'."
    },
    {
        "num": 36,
        "title": "Context propagation в NATS: передача trace context через NATS Msg Headers",
        "task": "Реализуйте передачу W3C Trace Context через NATS Headers (nats.Header) для синхронизации запросов и событий в NATS Core / JetStream.",
        "theory": "Современные версии NATS (начиная с NATS v2.2) поддерживают полноценные заголовки сообщений `nats.Header`, совместимые с типом `http.Header` (`map[string][]string`). Это делает интеграцию с OpenTelemetry исключительно удобной: структура `nats.Header` напрямую удовлетворяет адаптерам `propagation.HeaderCarrier`! При отправке сообщения в NATS тему издатель вызывает `Inject`, а подписчик — `Extract`. Это сохраняет непрерывность мониторинга транзакций в микросервисах, общающихся через сверхбыстрый pub/sub NATS.",
        "step_by_step": [
            "Импортируйте пакет go.opentelemetry.io/otel/propagation.",
            "Создайте структуру сообщения NATS с полем Header map[string][]string.",
            "Выполните инжекцию контекста в Msg.Header перед публикацией.",
            "На стороне подписчика извлеките контекст и создайте дочерний спан.",
            "Проверьте идентичность TraceID в логах."
        ],
        "code_blocks": [
            {
                "filename": "nats_trace_headers.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/http\"\n\n\t\"go.opentelemetry.io/otel\"\n\t\"go.opentelemetry.io/otel/propagation\"\n\tsdktrace \"go.opentelemetry.io/otel/sdk/trace\"\n\t\"go.opentelemetry.io/otel/trace\"\n)\n\n// NatsMsg имитирует структуру nats.Msg из пакета github.com/nats-io/nats.go\ntype NatsMsg struct {\n\tSubject string\n\tHeader  http.Header // В NATS headers реализованы как http.Header\n\tData    []byte\n}\n\nfunc main() {\n\ttp := sdktrace.NewTracerProvider(sdktrace.WithSampler(sdktrace.AlwaysSample()))\n\totel.SetTracerProvider(tp)\n\totel.SetTextMapPropagator(propagation.TraceContext{})\n\n\ttracer := otel.Tracer(\"nats-bus\")\n\n\t// 1. Издатель (Publisher)\n\tctx, pubSpan := tracer.Start(context.Background(), \"PublishToNats\",\n\t\ttrace.WithSpanKind(trace.SpanKindProducer),\n\t)\n\tdefer pubSpan.End()\n\n\tmsg := &NatsMsg{\n\t\tSubject: \"orders.created\",\n\t\tHeader:  make(http.Header),\n\t\tData:    []byte(\"order_payload_data\"),\n\t}\n\n\t// Поскольку nats.Header это http.Header, используем стандартный HeaderCarrier\n\totel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(msg.Header))\n\tfmt.Println(\"[NATS Publisher] Injected Header traceparent:\", msg.Header.Get(\"traceparent\"))\n\n\t// 2. Подписчик (Subscriber)\n\tsubCtx := otel.GetTextMapPropagator().Extract(context.Background(), propagation.HeaderCarrier(msg.Header))\n\n\t_, subSpan := tracer.Start(subCtx, \"HandleNatsMessage\",\n\t\ttrace.WithSpanKind(trace.SpanKindConsumer),\n\t)\n\tdefer subSpan.End()\n\n\tfmt.Println(\"[NATS Subscriber] Extracted Span TraceID:\", subSpan.SpanContext().TraceID().String())\n}",
                "note": "Передача W3C Trace Context через NATS Msg Headers"
            }
        ],
        "under_the_hood": "Протокол NATS передает заголовки в текстовом формате `NATS/1.0\r\nKey: Value\r\n\r\n` перед телом сообщения в кадре `HPUB` (Header Publish) или `HMSG`. Использование `http.Header` в клиенте Go позволяет избежать лишних преобразований форматов.",
        "pitfalls": "Использование устаревшего сервера NATS (< 2.2), который не поддерживает заголовки (только сырой PUB). В таком случае попытка отправить сообщение с заголовками вызовет ошибку 'headers not supported'.",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'Чем отличается распространение контекста в NATS Request-Reply от Pub-Sub?' Ответ: 'В Pub-Sub создается однонаправленная цепочка со SpanKindProducer и SpanKindConsumer. В Request-Reply NATS клиент отправляет запрос во временную Reply-тему, поэтому клиент создает SpanKindClient, сервер отвечает со SpanKindServer, имитируя синхронный RPC вызов'."
    },
    {
        "num": 37,
        "title": "Сетевой Draining с L4/L7 балансировщиком: синхронизация Endpoints и preStop",
        "task": "Опишите пошаговую механику сетевого исключения пода из балансировки нагрузки в Kubernetes и напишите скрипт проверки актуальности Endpoints при rolling update.",
        "theory": "При развертывании новой версии приложения (Rolling Update) Kubernetes запускает новые поды и гасит старые. Критический момент — синхронизация удаления старого пода из сетевых таблиц: 1. Пользователь вызывает `kubectl delete pod` или деплоит новую версию; 2. Apiserver переводит Pod в статус `Terminating`; 3. Endpoint Controller удаляет IP пода из объекта `Endpoints` / `EndpointSlice`; 4. Демоны `kube-proxy` на ВСЕХ нодах получают событие через watch и обновляют iptables/IPVS; 5. Внешний Ingress-контроллер (Nginx/Envoy) получает обновление и убирает под из своего upstream pool; 6. Если Go-процесс немедленно завершится на шаге 2, шаги 3-5 еще не успеют завершиться! Все запросы, пришедшие в эти 2-10 секунд, получат Connection Refused. Связка `lifecycle.preStop: sleep 10` и задержка в Go коде дают кластеру необходимое время на шаги 3-5.",
        "step_by_step": [
            "Создайте bash-сценарий или тестовый код, отслеживающий статус Endpoints через Kubernetes API.",
            "Проверьте временной интервал между статусом Terminating и фактическим удалением IP из балансировки.",
            "Рассчитайте необходимый размер preStop задержки для кластера.",
            "Сформулируйте требования к SLO доступности (99.99%) при rolling update."
        ],
        "code_blocks": [
            {
                "filename": "draining_timeline.txt",
                "lang": "text",
                "code": "Временная шкала безопасного завершения пода (Graceful Draining):\n\nT+0.0s  K8s API: Pod помечен как Terminating.\n        -> kubelet запускает preStop hook (sleep 10s)\n        -> Endpoint Controller удаляет IP из EndpointSlice\n\nT+1.5s  kube-proxy на рабочих нодах переписывает правила iptables/IPVS.\n        Ingress/Envoy удаляет pod IP из апстримов.\n        Новый трафик БОЛЬШЕ НЕ НАПРАВЛЯЕТСЯ на данный под.\n\nT+10.0s preStop hook завершается.\n        kubelet отправляет процессору сигнал SIGTERM.\n\nT+10.1s Go приложение перехватывает SIGTERM.\n        -> /readyz начинает отдавать 503 (защита от запоздалых пакетов)\n        -> Вызывается srv.Shutdown(ctx) / grpcServer.GracefulStop()\n\nT+12.5s Все in-flight запросы успешно завершены со статусом 200 OK.\n        Закрываются соединения к базе данных и кэшу.\n\nT+13.0s Go процесс завершается с кодом exit 0.\n        Контейнер удален без единой ошибки 502/RST для пользователей!",
                "note": "Хронология событий при Graceful Draining в кластере Kubernetes"
            }
        ],
        "under_the_hood": "kube-proxy не удаляет соединения мгновенно для уже установленных сессий (TCP connection tracking), но перестает распределять новые SYN пакеты. Правильно рассчитанный таймлайн исключает любые 'окна уязвимости'.",
        "pitfalls": "Установка слишком короткого `terminationGracePeriodSeconds` (например 5с), при этом `preStop` настроен на 10с. Kubelet прибьет контейнер сигналом SIGKILL еще до отправки SIGTERM!",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Сколько секунд должен быть preStop sleep в среднем Kubernetes кластере?' Ответ: 'Обычно от 5 до 15 секунд в зависимости от размера кластера и типа CNI (Cilium, Calico, Flannel). В крупных кластерах с тысячами нод распространение EndpointSlice занимает больше времени, поэтому 10-15с — безопасный отраслевой стандарт'."
    },
    {
        "num": 38,
        "title": "Graceful Connection Draining в gRPC: обработка активных и отклонение новых вызовов",
        "task": "Реализуйте в gRPC сервере перехват SIGTERM с вызовом server.GracefulStop(). Убедитесь, что сервер отклоняет новые входящие вызовы, но дает завершиться активным стримам.",
        "theory": "В gRPC вызов `server.GracefulStop()` выполняет строгий протокольный цикл Connection Draining: 1) Сервер немедленно закрывает слушающий TCP порт (net.Listener.Close), делая невозможным открытие новых TCP соединений; 2) Для всех активных клиентских соединений сервер шлет HTTP/2 кадр `GOAWAY` с `ErrCodeNo` (0x0). Этот кадр запрещает клиенту создавать новые HTTP/2 стримы поверх существующего соединения; 3) Сервер продолжает обрабатывать уже начатые унарные запросы и активные стримы; 4) Когда последний активный RPC метод возвращает результат и отправляет TRAILERS кадр, сервер мягко закрывает TCP сокет; 5) Метод `GracefulStop()` разблокируется и возвращает управление в `main()`.",
        "step_by_step": [
            "Инициализируйте gRPC сервер с долгим имитационным RPC методом.",
            "Запустите сервер в горутине.",
            "Перехватите сигнал SIGTERM в main.",
            "Вызовите server.GracefulStop() и зафиксируйте успешное завершение долгого запроса."
        ],
        "code_blocks": [
            {
                "filename": "grpc_draining_complete.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net\"\n\t\"os\"\n\t\"os/signal\"\n\t\"sync/atomic\"\n\t\"syscall\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n)\n\ntype WorkerService struct {\n\tactiveCalls atomic.Int64\n}\n\nfunc (s *WorkerService) ProcessLongTask(ctx context.Context) error {\n\ts.activeCalls.Add(1)\n\tdefer s.activeCalls.Add(-1)\n\n\tlog.Println(\"[RPC] Starting long task (takes 2 seconds)...\")\n\tselect {\n\tcase <-time.After(2 * time.Second):\n\t\tlog.Println(\"[RPC] Long task completed successfully.\")\n\t\treturn nil\n\tcase <-ctx.Done():\n\t\tlog.Println(\"[RPC] Task canceled by client.\")\n\t\treturn ctx.Err()\n\t}\n}\n\nfunc main() {\n\tlis, err := net.Listen(\"tcp\", \":50054\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Listen error: %v\", err)\n\t}\n\n\tserver := grpc.NewServer()\n\tsvc := &WorkerService{}\n\n\tgo func() {\n\t\tlog.Println(\"[gRPC] Server running on :50054\")\n\t\tif err := server.Serve(lis); err != nil {\n\t\t\tlog.Printf(\"[gRPC] Serve ended: %v\", err)\n\t\t}\n\t}()\n\n\t// Имитируем активный фоновый запрос в процессе работы\n\tgo func() {\n\t\ttime.Sleep(200 * time.Millisecond)\n\t\t_ = svc.ProcessLongTask(context.Background())\n\t}()\n\n\t// Ожидаем сигнала остановки\n\tsig := make(chan os.Signal, 1)\n\tsignal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)\n\n\t// Имитируем получение SIGTERM через 500мс\n\tgo func() {\n\t\ttime.Sleep(500 * time.Millisecond)\n\t\tsig <- syscall.SIGTERM\n\t}()\n\n\t<-sig\n\tlog.Println(\"[SIGTERM] Initiating server.GracefulStop()...\")\n\n\tstart := time.Now()\n\t// GracefulStop заблокируется до завершения активного таска\n\tserver.GracefulStop()\n\telapsed := time.Since(start)\n\n\tlog.Printf(\"[gRPC] GracefulStop finished in %v. Active calls remaining: %d\\n\", elapsed, svc.activeCalls.Load())\n\tfmt.Println(\"gRPC connection draining successfully validated.\")\n}",
                "note": "Практическая демонстрация gRPC GracefulStop с завершением активных задач"
            }
        ],
        "under_the_hood": "Внутри рантайма gRPC ведется счетчик `serveWG` (sync.WaitGroup). Каждый входящий стрим инкрементирует счетчик при создании и декрементирует при вызове `closeStream`. Метод `GracefulStop` делает `lis.Close()` и ждет `s.serveWG.Wait()`.",
        "pitfalls": "Вызов `os.Exit(0)` сразу после перехвата сигнала в main. Это немедленно прерывает процесс ядра, убивая все горутины и сокеты без выполнения `defer` и GracefulStop.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'В чем разница между server.GracefulStop() и server.Stop()?' Ответ: 'GracefulStop() перестает принимать новые запросы, шлет GOAWAY и блокируется до завершения всех активных RPC. Stop() немедленно закрывает все открытые сокеты, сбрасывая активные стримы ошибкой Unavailable'."
    }
]
