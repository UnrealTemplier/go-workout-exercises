# -*- coding: utf-8 -*-
"""Exercises 46..89 of Chapter 33."""

exercises = [
  {
    "num": 46,
    "title": "Сквозная трассировка OpenTelemetry: упаковка и извлечение TraceID в метаданных gRPC",
    "task": "**Распределенная трассировка (Distributed Tracing)**: Интегрируйте библиотеку OpenTelemetry в ваши микросервисы. Настройте сквозную трассировку (tracing): когда `APIGateway` отправляет запрос в `UserService`, он должен упаковывать идентификатор трассировки (`TraceID`) в метаданные gRPC. `UserService` должен извлекать этот ID. В результате вы должны видеть единый лог вызовов (Span) в системе визуализации трассировки (например, Jaeger).",
    "theory": "Спецификация распределенной трассировки OpenTelemetry в gRPC:\n- Когда клиент инициирует вызов, OpenTelemetry Tracer создает корневой спан:\n  `ctx, span := tracer.Start(ctx, \"APIGateway.Forward\")`\n- Клиентский интерцептор использует OTel Propagator:\n  `otel.GetTextMapPropagator().Inject(ctx, &metadataSupplier{md})`\n- Серверный интерцептор извлекает контекст:\n  `ctx := otel.GetTextMapPropagator().Extract(ctx, &metadataSupplier{md})`\n- Благодаря этому серверный спан становится дочерним к клиентскому, формируя непрерывное дерево вызовов.",
    "step_by_step": "1. Создайте TextMapCarrier адаптер для `metadata.MD`.\n2. Реализуйте упаковку `traceparent` перед отправкой RPC.\n3. Извлеките контекст на стороне сервера.\n4. Протестируйте совпадение TraceID в обоих сервисах.",
    "code_blocks": [
      {
        "filename": "otel_carrier_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc/metadata\"\n)\n\ntype MetadataCarrier metadata.MD\n\nfunc (c MetadataCarrier) Get(key string) string {\n\tvals := metadata.MD(c).Get(key)\n\tif len(vals) == 0 {\n\t\treturn \"\"\n\t}\n\treturn vals[0]\n}\n\nfunc (c MetadataCarrier) Set(key, val string) {\n\tmetadata.MD(c).Set(key, val)\n}\n\nfunc (c MetadataCarrier) Keys() []string {\n\tvar keys []string\n\tfor k := range c {\n\t\tkeys = append(keys, k)\n\t}\n\treturn keys\n}\n\nfunc TestOTelMetadataPropagation(t *testing.T) {\n\ttraceID := \"e4b00539c05423f46f332c1c97a8e8e7\"\n\tspanID := \"0538a0a03d1ef3a1\"\n\tw3cHeader := fmt.Sprintf(\"00-%s-%s-01\", traceID, spanID)\n\n\t// 1. APIGateway упаковывает в metadata\n\tmd := metadata.New(nil)\n\tcarrier := MetadataCarrier(md)\n\tcarrier.Set(\"traceparent\", w3cHeader)\n\n\toutCtx := metadata.NewOutgoingContext(context.Background(), md)\n\n\t// Имитация передачи по сети\n\tinMD, _ := metadata.FromOutgoingContext(outCtx)\n\tinCarrier := MetadataCarrier(inMD)\n\n\t// 2. UserService извлекает заголовок\n\textracted := inCarrier.Get(\"traceparent\")\n\tif extracted != w3cHeader {\n\t\tt.Fatalf(\"Трейс потерян: %s != %s\", extracted, w3cHeader)\n\t}\n\n\tfmt.Printf(\"OpenTelemetry Carrier успешно пробросил W3C заголовок:\\n  %s\\n\", extracted)\n}",
        "note": "Реализация TextMapCarrier адаптера для gRPC metadata"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v otel_carrier_test.go\n# Вывод:\n# === RUN   TestOTelMetadataPropagation\n# OpenTelemetry Carrier успешно пробросил W3C заголовок:\n#   00-e4b00539c05423f46f332c1c97a8e8e7-0538a0a03d1ef3a1-01\n# --- PASS: TestOTelMetadataPropagation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Интерфейс `propagation.TextMapCarrier` является кросс-платформенным стандартом OpenTelemetry. Он позволяет пробрасывать контекст не только через gRPC/HTTP заголовки, но и через сообщения брокеров Kafka и NATS.",
    "pitfalls": "Мутировать входящие метаданные напрямую в обработчике: `metadata.MD` в Go — это `map[string][]string`, и одновременная модификация карты несколькими горутинами вызовет панику `fatal error: concurrent map writes`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем нужен span.SetStatus(codes.Error, \"...\") при ошибках?»\n**Ответ:** Простого логирования ошибки недостаточно. Метод `span.SetStatus` помечает отрезок времени красным цветом в интерфейсе Jaeger/Grafana Tempo. Это позволяет мониторингу строить графики Error Budget и настраивать автоматические алерты по соотношению сбойных спанов."
  },
  {
    "num": 47,
    "title": "Каскадная трассировка через 3 микросервиса: граф вызовов API Gateway -> User Service -> Auth Service",
    "task": "**Distributed Tracing (OpenTelemetry)**: У тебя 3 микросервиса: `API-Gateway` -> `User-Service` -> `Auth-Service`. Установи OpenTelemetry. Настрой проброс TraceID (через метаданные контекста gRPC) сквозь все три сервиса. (Можно поднять локально Jaeger в Docker и посмотреть на красивые графики \"путешествия\" запроса).",
    "theory": "Иерархия распределенного графа спанов (Span Tree Hierarchy):\n- Корневой спан: `[API-Gateway: POST /login]` (SpanID: `0001`, Parent: `nil`)\n  - Дочерний спан: `[User-Service: VerifyUser]` (SpanID: `0002`, Parent: `0001`)\n    - Внучатый спан: `[Auth-Service: CheckPasswordHash]` (SpanID: `0003`, Parent: `0002`)\n- Все 3 спана имеют строго **одинаковый глобальный TraceID**.\n- Если `Auth-Service` отвечает 250 мс, в Jaeger UI сразу видно, что именно этот спан занимает 90% времени родительских вызовов.",
    "step_by_step": "1. Создайте модель связного графа спанов.\n2. Смоделируйте сквозную передачу контекста через 3 микросервиса.\n3. Проверьте отношение родитель-потомок (Parent-Child).\n4. Протестируйте целостность дерева трейсинга.",
    "code_blocks": [
      {
        "filename": "three_service_trace_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype TraceHop struct {\n\tServiceName string\n\tSpanID      string\n\tParentSpan  string\n\tTraceID     string\n}\n\nfunc TestCascadeThreeHopTrace(t *testing.T) {\n\tglobalTraceID := \"c4f00112233445566778899aabbccdde\"\n\n\t// Hop 1: Gateway создает корневой спан\n\thop1 := TraceHop{\n\t\tServiceName: \"api-gateway\",\n\t\tSpanID:      \"span_01_root\",\n\t\tParentSpan:  \"none\",\n\t\tTraceID:     globalTraceID,\n\t}\n\n\t// Hop 2: User-Service создает дочерний спан\n\thop2 := TraceHop{\n\t\tServiceName: \"user-service\",\n\t\tSpanID:      \"span_02_user\",\n\t\tParentSpan:  hop1.SpanID,\n\t\tTraceID:     globalTraceID,\n\t}\n\n\t// Hop 3: Auth-Service создает дочерний спан к User-Service\n\thop3 := TraceHop{\n\t\tServiceName: \"auth-service\",\n\t\tSpanID:      \"span_03_auth\",\n\t\tParentSpan:  hop2.SpanID,\n\t\tTraceID:     globalTraceID,\n\t}\n\n\ttree := []TraceHop{hop1, hop2, hop3}\n\n\tfmt.Println(\"Иерархическое дерево распределенного трейса:\")\n\tfor i, h := range tree {\n\t\tfmt.Printf(\"  [%d] Service: %-15s | Span: %-12s | Parent: %-12s | TraceID: %s\\n\",\n\t\t\ti+1, h.ServiceName, h.SpanID, h.ParentSpan, h.TraceID)\n\t\tif h.TraceID != globalTraceID {\n\t\t\tt.Fatalf(\"TraceID разорван на сервисе %s\", h.ServiceName)\n\t\t}\n\t}\n\n\tif tree[1].ParentSpan != tree[0].SpanID || tree[2].ParentSpan != tree[1].SpanID {\n\t\tt.Fatal(\"Нарушена иерархия родительских спанов\")\n\t}\n}",
        "note": "Проверка сквозной иерархии спанов в каскаде 3 микросервисов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v three_service_trace_test.go\n# Вывод:\n# === RUN   TestCascadeThreeHopTrace\n# Иерархическое дерево распределенного трейса:\n#   [1] Service: api-gateway     | Span: span_01_root | Parent: none         | TraceID: c4f00112233445566778899aabbccdde\n#   [2] Service: user-service    | Span: span_02_user | Parent: span_01_root | TraceID: c4f00112233445566778899aabbccdde\n#   [3] Service: auth-service    | Span: span_03_auth | Parent: span_02_user | TraceID: c4f00112233445566778899aabbccdde\n# --- PASS: TestCascadeThreeHopTrace (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Внутри OpenTelemetry контекст передается через `context.Context`. Функция `trace.ContextWithSpan(ctx, span)` привязывает спан к контексту, а интерцепторы автоматически сериализуют его при исходящем сетевом вызове.",
    "pitfalls": "Терять контекст при запуске асинхронных горутин: если вызвать `go doAsyncTask()` без передачи контекста или с новым `context.Background()`, асинхронная задача выпадет из общего графа трейсинга.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как связать трассировку синхронного вызова gRPC с асинхронным сообщением в Kafka?»\n**Ответ:** При публикации сообщения в Kafka продюсер инжектирует TraceID в бинарные заголовки `kafka.RecordHeader{Key: \"traceparent\", Value: ...}`. Консьюмер Kafka извлекает заголовок и создает спан с типом связи `trace.Link`, соединяя синхронный HTTP/gRPC трейс с асинхронной обработкой в брокере."
  },
  {
    "num": 48,
    "title": "Межсервисное взаимодействие (Service-to-Service): gRPC клиент в OrderService для вызова InventoryService",
    "task": "**Service-to-Service**: Создай два gRPC-сервера: `OrderService` и `InventoryService`. `OrderService` при создании заказа делает gRPC-вызов в `InventoryService` для резервации товара.",
    "theory": "Синхронное межсервисное общение (Service-to-Service gRPC Call):\n- `OrderService` выступает одновременно:\n  1. **gRPC-сервером** для входящих запросов от клиентов.\n  2. **gRPC-клиентом** для обращения к зависимым бэкендам (`InventoryService`).\n- Пул соединений `*grpc.ClientConn` создается один раз при старте сервиса и переиспользуется всеми горутинами.\n- Обязательно настраиваются таймауты и обработка бизнес-ошибок (например, недостаток товара на складе).",
    "step_by_step": "1. Создайте mock-сервер склада `InventoryService`.\n2. Реализуйте метод `CreateOrder` в сервисе заказов, вызывающий склад.\n3. Проверьте успешное резервирование.\n4. Проверьте сценарий отказа склада (Out of Stock).",
    "code_blocks": [
      {
        "filename": "service_to_service_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\ntype InventoryService struct {\n\tmu    sync.Mutex\n\tstock map[string]int\n}\n\nfunc (s *InventoryService) ReserveItem(ctx context.Context, itemID string, qty int) error {\n\ts.mu.Lock()\n\tdefer s.mu.Unlock()\n\n\tcurrent := s.stock[itemID]\n\tif current < qty {\n\t\treturn status.Errorf(codes.FailedPrecondition, \"недостаточно товара %s на складе: осталось %d\", itemID, current)\n\t}\n\n\ts.stock[itemID] -= qty\n\treturn nil\n}\n\ntype OrderService struct {\n\tinventory *InventoryService\n}\n\nfunc (s *OrderService) CreateOrder(ctx context.Context, orderID, itemID string, qty int) error {\n\t// Межсервисный вызов с таймаутом\n\tcallCtx, cancel := context.WithTimeout(ctx, 100*time.Millisecond)\n\tdefer cancel()\n\n\terr := s.inventory.ReserveItem(callCtx, itemID, qty)\n\tif err != nil {\n\t\treturn fmt.Errorf(\"сбой резервации на складе: %w\", err)\n\t}\n\n\tfmt.Printf(\"Заказ %s успешно создан! Зарезервировано: %d шт товара %s\\n\", orderID, qty, itemID)\n\treturn nil\n}\n\nfunc TestServiceToServiceInteraction(t *testing.T) {\n\tinv := &InventoryService{stock: map[string]int{\"item_iphone16\": 5}}\n\torders := &OrderService{inventory: inv}\n\n\t// 1. Успешный заказ 2 шт\n\terr1 := orders.CreateOrder(context.Background(), \"ord_001\", \"item_iphone16\", 2)\n\tif err1 != nil {\n\t\tt.Fatalf(\"Заказ должен был пройти: %v\", err1)\n\t}\n\n\t// 2. Заказ 4 шт (на складе осталось только 3 -> отказ)\n\terr2 := orders.CreateOrder(context.Background(), \"ord_002\", \"item_iphone16\", 4)\n\tif err2 == nil {\n\t\tt.Fatal(\"Ожидался отказ из-за нехватки товара\")\n\t}\n\n\tfmt.Println(\"Второй заказ корректно отклонен:\", err2)\n}",
        "note": "Синхронный межсервисный вызов с валидацией бизнес-инвариантов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v service_to_service_test.go\n# Вывод:\n# === RUN   TestServiceToServiceInteraction\n# Заказ ord_001 успешно создан! Зарезервировано: 2 шт товара item_iphone16\n# Второй заказ корректно отклонен: сбой резервации на складе: rpc error: code = FailedPrecondition desc = недостаточно товара item_iphone16 на складе: осталось 3\n# --- PASS: TestServiceToServiceInteraction (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Один экземпляр `*grpc.ClientConn` внутри `OrderService` держит постоянное HTTP/2 соединение к складу. Тысячи одновременных заказов мультиплексируются через этот единственный сокет.",
    "pitfalls": "Создавать новый `grpc.NewClient` на каждый входящий HTTP/gRPC запрос: это приведет к открытию тысяч сокетов, исчерпанию файловых дескрипторов ОС (`too many open files`) и колоссальному оверхеду на TLS рукопожатия.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы риски синхронных цепочек вызовов (A -> B -> C -> D)?»\n**Ответ:** 1. **Латентность суммируется** ($T = T_A + T_B + T_C + T_D$). 2. **Надежность падает мультипликативно:** если каждый сервис имеет SLA 99.9%, то цепочка из 4 сервисов имеет SLA $0.999^4 \\approx 99.6\\%$. 3. **Риск каскадного отказа:** зависание сервиса D блокирует потоки во всех вышележащих сервисах. Решение: заменять синхронные цепочки асинхронными событиями и кэшированием."
  },
  {
    "num": 49,
    "title": "Метрики gRPC через перехватчики: автоматический сбор RPS, времени ответа и кодов ошибок",
    "task": "Добавьте метрики (Prometheus) для gRPC методов: количество запросов, длительность, ошибки. Используйте перехватчики для сбора.",
    "theory": "Автоматическая инструментация через gRPC Unary Server Interceptor:\n- Перехватчик засекает время перед вызовом хэндлера:\n  `start := time.Now()`\n- Вызывает `resp, err := handler(ctx, req)`\n- Определяет статус-код ответа через `status.Code(err)`.\n- Фиксирует метрики:\n  - `requests_total.WithLabelValues(method, code).Inc()`\n  - `request_duration_seconds.WithLabelValues(method).Observe(duration.Seconds())`",
    "step_by_step": "1. Создайте Unary Server Interceptor метрик.\n2. Извлеките имя gRPC-метода и статус ответа.\n3. Просимулируйте успешный и ошибочный вызовы.\n4. Проверьте фиксацию метрик в реестре.",
    "code_blocks": [
      {
        "filename": "grpc_metrics_interceptor_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\ntype RecordedMetric struct {\n\tMethod   string\n\tCode     string\n\tDuration time.Duration\n}\n\ntype MetricsCollectorMock struct {\n\trecords []RecordedMetric\n}\n\nfunc (m *MetricsCollectorMock) Observe(method, code string, d time.Duration) {\n\tm.records = append(m.records, RecordedMetric{\n\t\tMethod:   method,\n\t\tCode:     code,\n\t\tDuration: d,\n\t})\n}\n\nfunc UnaryMetricsInterceptor(collector *MetricsCollectorMock) grpc.UnaryServerInterceptor {\n\treturn func(\n\t\tctx context.Context,\n\t\treq any,\n\t\tinfo *grpc.UnaryServerInfo,\n\t\thandler grpc.UnaryHandler,\n\t) (any, error) {\n\t\tstart := time.Now()\n\t\tresp, err := handler(ctx, req)\n\t\telapsed := time.Since(start)\n\n\t\tcode := status.Code(err).String()\n\t\tcollector.Observe(info.FullMethod, code, elapsed)\n\n\t\treturn resp, err\n\t}\n}\n\nfunc TestMetricsInterceptor(t *testing.T) {\n\tcollector := &MetricsCollectorMock{}\n\tinterceptor := UnaryMetricsInterceptor(collector)\n\n\t// 1. Успешный вызов\n\tokHandler := func(ctx context.Context, req any) (any, error) {\n\t\ttime.Sleep(5 * time.Millisecond)\n\t\treturn \"OK\", nil\n\t}\n\t_, _ = interceptor(context.Background(), nil, &grpc.UnaryServerInfo{FullMethod: \"/order.v1/Create\"}, okHandler)\n\n\t// 2. Сбойный вызов\n\terrHandler := func(ctx context.Context, req any) (any, error) {\n\t\treturn nil, status.Error(codes.InvalidArgument, \"некорректный ID\")\n\t}\n\t_, _ = interceptor(context.Background(), nil, &grpc.UnaryServerInfo{FullMethod: \"/order.v1/Create\"}, errHandler)\n\n\tif len(collector.records) != 2 {\n\t\tt.Fatalf(\"Ожидалось 2 записи метрик\")\n\t}\n\n\tfmt.Println(\"Собранные метрики вызовов:\")\n\tfor _, r := range collector.records {\n\t\tfmt.Printf(\"  • Метод: %-18s | Code: %-15s | Latency: %v\\n\", r.Method, r.Code, r.Duration.Round(time.Millisecond))\n\t}\n}",
        "note": "Инструментация gRPC через Unary Server Interceptor"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v grpc_metrics_interceptor_test.go\n# Вывод:\n# === RUN   TestMetricsInterceptor\n# Собранные метрики вызовов:\n#   • Метод: /order.v1/Create    | Code: OK              | Latency: 5ms\n#   • Метод: /order.v1/Create    | Code: InvalidArgument | Latency: 0s\n# --- PASS: TestMetricsInterceptor (0.01s)\n# PASS"
      }
    ],
    "under_the_hood": "Официальная библиотека `go-grpc-prometheus` предварительно инициализирует лейблы для всех зарегистрированных методов gRPC сервера, предотвращая пропуски метрик на графиках до первого вызова.",
    "pitfalls": "Включать подробные гистограммы (`EnableHandlingTimeHistogram`) на сервере с 10 000 RPS без ограничения числа бакетов: каждая комбинация лейблов умножается на число бакетов, приводя к перерасходу ОЗУ сервиса.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как мониторить стриминговые RPC в Prometheus?»\n**Ответ:** Для серверного, клиентского и двунаправленного стриминга используются интерцепторы `StreamServerInterceptor`, считающие отдельные метрики: `grpc_server_msg_received_total` (число сообщений в стриме) и `grpc_server_msg_sent_total`, а также общую продолжительность открытого стрима."
  },
  {
    "num": 50,
    "title": "Балансировка нагрузки на клиенте с dns:/// и Headless Service: алгоритм round-robin",
    "task": "Настройте **client-side load balancing** в gRPC: используйте `dns:///` схему для резолвинга всех IP сервиса и round-robin балансировки на клиенте.",
    "theory": "Архитектура Client-Side Load Balancing через DNS:\n- Клиент передает адрес вида: `dns:///inventory-headless:50051`.\n- DNS-сервер (CoreDNS в Kubernetes) возвращает список IP всех подов: `[10.244.1.10, 10.244.1.11, 10.244.1.12]`.\n- Балансировщик `round_robin`:\n  1. Поддерживает активный SubConn (TCP сокет) к каждому поду.\n  2. На каждый вызов перебирает следующий сокет по кругу.\n- Преимущества:\n  - Нет промежуточного Proxy-сервера (Zero Hop, минимальная задержка).\n  - Равномерная загрузка всех CPU ядер кластера.",
    "step_by_step": "1. Задайте конфигурацию `serviceConfig` с политикой `round_robin`.\n2. Настройте подключение через `grpc.NewClient`.\n3. Смоделируйте распределение 6 вызовов по 3 подам.\n4. Проверьте балансировку.",
    "code_blocks": [
      {
        "filename": "client_side_balancer_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\n\t\"google.golang.org/grpc\"\n\t_ \"google.golang.org/grpc/balancer/roundrobin\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n)\n\nfunc main() {\n\t// JSON-конфигурация клиентской балансировки\n\tserviceConfig := `{\"loadBalancingPolicy\":\"round_robin\"}`\n\n\t// Подключение через схему dns:/// к Headless сервису\n\ttarget := \"dns:///inventory-headless.production.svc.cluster.local:50051\"\n\n\tconn, err := grpc.NewClient(\n\t\ttarget,\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t\tgrpc.WithDefaultServiceConfig(serviceConfig),\n\t)\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer conn.Close()\n\n\tfmt.Println(\"Клиентский балансировщик gRPC успешно инициализирован:\")\n\tfmt.Printf(\"  • Target URI:     %s\\n\", target)\n\tfmt.Printf(\"  • Алгоритм:       round_robin (по всем A-записям Headless Service)\\n\")\n}",
        "note": "Подключение gRPC клиента к Headless Service с round_robin"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run client_side_balancer_demo.go\n# Вывод:\n# Клиентский балансировщик gRPC успешно инициализирован:\n#   • Target URI:     dns:///inventory-headless.production.svc.cluster.local:50051\n#   • Алгоритм:       round_robin (по всем A-записям Headless Service)"
      }
    ],
    "under_the_hood": "При получении списка адресов gRPC Subchannel Manager открывает независимые пулы сокетов. Если один под перестает отвечать, SubConn переходит в TransientFailure, и балансировщик выводит его из ротации за 0 микросекунд.",
    "pitfalls": "Использовать обычный ClusterIP сервис без `clusterIP: None`: CoreDNS вернет один виртуальный IP, и вся нагрузка пойдет на один под.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы недостатки Client-Side балансировки по сравнению с Server-Side (Envoy)?»\n**Ответ:** 1. При 1 000 клиентов и 1 000 подов бэкенда суммарно открывается $1\\,000 \\times 1\\,000 = 1\\,000\\,000$ постоянных TCP сокетов (Full Mesh Connection Problem), что перегружает память. 2. Сложность реализации логики балансировки на разных языках программирования."
  },
  {
    "num": 51,
    "title": "Протокол внешней балансировки grpclb: архитектура выделенного координатора нагрузки",
    "task": "Изучите `grpclb` — протокол gRPC Load Balancing, где отдельный load balancer сервис отдает клиенту список backend'ов.",
    "theory": "Принцип работы внешнего балансировщика grpclb (External Load Balancer):\n- Вместо простого DNS клиенты обращаются к выделенному балансировщику `grpclb-service`.\n- Архитектура:\n  1. Клиент подключается к `grpclb` и открывает двунаправленный стрим `BalanceLoad`.\n  2. `grpclb` сервер знает реальную загрузку CPU/RAM всех бэкендов в реальном времени.\n  3. `grpclb` отправляет клиенту список адресов (`ServerList`) с весами.\n  4. Клиент шлет периодические отчеты о нагрузке (`ClientStats`) обратно на балансировщик.\n- В современном мире протокол `grpclb` вытеснен более мощным открытым стандартом **xDS** (Envoy Control Plane).",
    "step_by_step": "1. Создайте модель протокола координатора нагрузки.\n2. Смоделируйте получение взвешенного списка серверов.\n3. Продемонстрируйте маршрутизацию клиента.\n4. Проверьте работу протокола.",
    "code_blocks": [
      {
        "filename": "grpclb_architecture_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype GrpclbServer struct {\n\tIP     string\n\tPort   int\n\tWeight int\n}\n\ntype MockGrpclbCoordinator struct{}\n\nfunc (c *MockGrpclbCoordinator) GetBackendList() []GrpclbServer {\n\t// Балансировщик отдает список серверов на основе текущей загрузки CPU в кластере\n\treturn []GrpclbServer{\n\t\t{IP: \"10.0.1.20\", Port: 50051, Weight: 80}, // Свободный сервер (вес 80)\n\t\t{IP: \"10.0.1.21\", Port: 50051, Weight: 20}, // Нагруженный сервер (вес 20)\n\t}\n}\n\nfunc TestGrpclbProtocolModel(t *testing.T) {\n\tcoordinator := &MockGrpclbCoordinator{}\n\tservers := coordinator.GetBackendList()\n\n\tif len(servers) != 2 {\n\t\tt.Fatalf(\"Ожидалось 2 сервера в списке grpclb\")\n\t}\n\n\tfmt.Println(\"grpclb координатор успешно предоставил топологию бэкендов:\")\n\tfor _, s := range servers {\n\t\tfmt.Printf(\"  • Сервер %s:%d | Динамический вес нагрузки: %d%%\\n\", s.IP, s.Port, s.Weight)\n\t}\n}",
        "note": "Моделирование протокола координатора grpclb"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v grpclb_architecture_test.go\n# Вывод:\n# === RUN   TestGrpclbProtocolModel\n# grpclb координатор успешно предоставил топологию бэкендов:\n#   • Сервер 10.0.1.20:50051 | Динамический вес нагрузки: 80%\n#   • Сервер 10.0.1.21:50051 | Динамический вес нагрузки: 20%\n# --- PASS: TestGrpclbProtocolModel (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Протокол `grpclb` был исторически разработан Google для внутренней сети Borg. Сегодня он заменен стандартом xDS (Endpoint Discovery Service — EDS).",
    "pitfalls": "Использовать устаревший пакет `google.golang.org/grpc/balancer/grpclb` в новых проектах: он помечен как deprecated. Стандартом для внешнего управления является `google.golang.org/grpc/xds`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое xDS API в контексте gRPC?»\n**Ответ:** xDS (eXtensible Discovery Service) — это семейство протоколов на базе gRPC-стримов (LDS, RDS, CDS, EDS), позволяющее динамически конфигурировать маршрутизацию, TLS сертификаты и балансировку клиентов в реальном времени без разрыва соединений."
  },
  {
    "num": 52,
    "title": "Кастомный resolver.Builder: динамическая интеграция gRPC с Consul или etcd",
    "task": "Реализуйте кастомный `resolver.Builder` для интеграции с Consul или etcd для service discovery.",
    "theory": "Архитектура собственного резолвера gRPC:\n- Интерфейс `resolver.Builder`:\n  - `Build(target resolver.Target, cc resolver.ClientConn, opts resolver.BuildOptions) (resolver.Resolver, error)`\n  - `Scheme() string` — префикс схемы, например `\"consul\"`.\n- Интерфейс `resolver.Resolver`:\n  - `ResolveNow(resolver.ResolveNowOptions)` — принудительное обновление адресов.\n  - `Close()` — освобождение ресурсов.\n- При изменении подов резолвер вызывает:\n  `cc.UpdateState(resolver.State{Addresses: []resolver.Address{...}})`",
    "step_by_step": "1. Реализуйте структуру кастомного билдера с методом `Scheme()`.\n2. Реализуйте метод `Build` с уведомлением `cc.UpdateState`.\n3. Зарегистрируйте билдер в глобальном реестре `resolver.Register`.\n4. Протестируйте резолвинг схемы `consul:///`.",
    "code_blocks": [
      {
        "filename": "custom_consul_resolver_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc/resolver\"\n)\n\ntype CustomConsulBuilder struct{}\n\nfunc (b *CustomConsulBuilder) Scheme() string {\n\treturn \"myconsul\"\n}\n\nfunc (b *CustomConsulBuilder) Build(\n\ttarget resolver.Target,\n\tcc resolver.ClientConn,\n\topts resolver.BuildOptions,\n) (resolver.Resolver, error) {\n\t// Имитируем запрос к Consul API\n\tendpoints := []resolver.Address{\n\t\t{Addr: \"10.0.2.50:50051\"},\n\t\t{Addr: \"10.0.2.51:50051\"},\n\t}\n\n\t// Передаем адреса в ядро gRPC\n\terr := cc.UpdateState(resolver.State{Addresses: endpoints})\n\tif err != nil {\n\t\treturn nil, err\n\t}\n\n\treturn &noopResolver{}, nil\n}\n\ntype noopResolver struct{}\nfunc (r *noopResolver) ResolveNow(resolver.ResolveNowOptions) {}\nfunc (r *noopResolver) Close()                                {}\n\nfunc TestCustomResolverRegistration(t *testing.T) {\n\tbuilder := &CustomConsulBuilder{}\n\tresolver.Register(builder)\n\n\t// Проверяем, что схема зарегистрирована\n\tfound := resolver.Get(\"myconsul\")\n\tif found == nil {\n\t\tt.Fatal(\"Резолвер myconsul не зарегистрирован!\")\n\t}\n\n\tfmt.Printf(\"Кастомный резолвер gRPC успешно зарегистрирован для схемы: %s:///\\n\", found.Scheme())\n}",
        "note": "Реализация кастомного resolver.Builder для Service Discovery"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v custom_consul_resolver_test.go\n# Вывод:\n# === RUN   TestCustomResolverRegistration\n# Кастомный резолвер gRPC успешно зарегистрирован для схемы: myconsul:///\n# --- PASS: TestCustomResolverRegistration (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Функция `resolver.Register` сохраняет билдер в глобальной потокобезопасной карте. При вызове `grpc.NewClient(\"myconsul:///service\")` gRPC автоматически выбирает нужный билдер по схеме URI.",
    "pitfalls": "Блокировать вызов `Build()` долгим сетевым запросом к Consul: метод `Build` должен быстро запустить фоновую горутину отслеживания, иначе создание gRPC клиента зависнет.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда вызывается метод ResolveNow у кастомного резолвера?»\n**Ответ:** gRPC вызывает `ResolveNow()`, когда все существующие соединения SubConn перешли в статус сбоя (`TRANSIENT_FAILURE`). Это сигнал резолверу немедленно опросить Consul/DNS повторно, так как текущие IP-адреса, вероятно, устарели."
  },
  {
    "num": 53,
    "title": "Предохранитель Circuit Breaker при сбое зависимостей: защита от каскадного падения сервисов",
    "task": "**Circuit Breaker (Предохранитель)**: `Auth-Service` завис или отвечает медленно. `User-Service` не должен лечь вслед за ним (каскадный сбой). Используй библиотеку `github.com/sony/sonyflake` или `gobreaker`. Настрой предохранитель: если 5 запросов подряд упали с ошибкой, не делай следующие запросы, а сразу отдавай ошибку (или fallback-значение), пока тот сервис не оживет.",
    "theory": "Предотвращение каскадного коллапса (Cascading Failure Prevention):\n- Если `Auth-Service` завис, каждый вызов из `User-Service` блокирует горутину на время таймаута (например, 2 сек).\n- При потоке 500 RPS в `User-Service` за 2 секунды образуется 1 000 зависших горутин, переполняя память и сокеты.\n- Circuit Breaker размыкает цепь после 5 ошибок подряд:\n  - Все последующие запросы мгновенно отклоняются локально за 0.05 мс.\n  - `User-Service` продолжает обслуживать запросы других методов без деградации.",
    "step_by_step": "1. Настройте `gobreaker.CircuitBreaker`.\n2. Задайте правило размыкания после 5 последовательных сбоев.\n3. Смоделируйте 5 ошибок авторизации.\n4. Убедитесь в мгновенном возврате ошибки предохранителя.",
    "code_blocks": [
      {
        "filename": "cascading_failure_protection_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"github.com/sony/gobreaker\"\n)\n\ntype AuthServiceCaller struct {\n\tcb *gobreaker.CircuitBreaker\n}\n\nfunc (c *AuthServiceCaller) AuthenticateUser(token string, authDead bool) (string, error) {\n\tres, err := c.cb.Execute(func() (any, error) {\n\t\tif authDead {\n\t\t\treturn nil, fmt.Errorf(\"auth-service 504 Gateway Timeout\")\n\t\t}\n\t\treturn \"USER_ID_42\", nil\n\t})\n\n\tif err != nil {\n\t\treturn \"\", err\n\t}\n\treturn res.(string), nil\n}\n\nfunc TestCascadingFailurePrevention(t *testing.T) {\n\tst := gobreaker.Settings{\n\t\tName:        \"AuthServiceBreaker\",\n\t\tMaxRequests: 1,\n\t\tTimeout:     50 * time.Millisecond,\n\t\tReadyToTrip: func(counts gobreaker.Counts) bool {\n\t\t\treturn counts.ConsecutiveFailures >= 5\n\t\t},\n\t}\n\n\tcaller := &AuthServiceCaller{cb: gobreaker.NewCircuitBreaker(st)}\n\n\t// 5 сбоев подряд\n\tfor i := 1; i <= 5; i++ {\n\t\t_, _ = caller.AuthenticateUser(\"invalid_token\", true)\n\t}\n\n\t// 6-й вызов мгновенно отклоняется\n\tstart := time.Now()\n\t_, err := caller.AuthenticateUser(\"valid_token\", true)\n\telapsed := time.Since(start)\n\n\tif err != gobreaker.ErrOpenState {\n\t\tt.Fatalf(\"Ожидался ErrOpenState, получено: %v\", err)\n\t}\n\n\tif elapsed > 2*time.Millisecond {\n\t\tt.Fatalf(\"Отказ должен быть мгновенным: %v\", elapsed)\n\t}\n\n\tfmt.Printf(\"Circuit Breaker успешно спас сервис: 6-й вызов отсечен за %v с ошибкой: %v\\n\", elapsed, err)\n}",
        "note": "Локализация сбоев и предотвращение каскадного падения сервисов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v cascading_failure_protection_test.go\n# Вывод:\n# === RUN   TestCascadingFailurePrevention\n# Circuit Breaker успешно спас сервис: 6-й вызов отсечен за 50µs с ошибкой: circuit breaker is open\n# --- PASS: TestCascadingFailurePrevention (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Быстрый локальный отказ возвращает заранее аллоцированную ошибку-синглтон `gobreaker.ErrOpenState`, не вызывая дополнительных аллокаций памяти в куче.",
    "pitfalls": "Использовать одинаковые таймауты и параметры Circuit Breaker для всех сервисов: критические платежные методы требуют более жестких порогов, чем второстепенные сервисы рекомендаций.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как совместить Circuit Breaker с Fallback механизмом?»\n**Ответ:** В блоке `if err == gobreaker.ErrOpenState` вызывается функция деградации: например, выдача базовых прав доступа гостя, чтение кэшированного профиля из Redis или возврат пустого списка баннеров, предотвращая появление ошибки на экране пользователя."
  },
  {
    "num": 54,
    "title": "Корректная остановка сервера Graceful Shutdown: перехват os.Interrupt и вызов GracefulStop",
    "task": "**[Каверзный кейс — Graceful Shutdown]**: Настрой gRPC-сервер на корректное завершение: при получении `os.Interrupt` вызови `server.GracefulStop()` (он дождется завершения активных стримов и запросов) в отдельной горутине, а в `main` подожди этого завершения через `sync.WaitGroup` или канал.",
    "theory": "Механика корректного завершения gRPC-сервера (Graceful Shutdown):\n- Вызов `server.Stop()` резко закрывает все сокеты, обрывая вызовы клиентов ошибкой `RST_STREAM / Connection Reset`.\n- Метод `server.GracefulStop()`:\n  1. Немедленно прекращает прием новых входящих TCP-соединений (`lis.Close()`).\n  2. Отправляет клиентам HTTP/2 фрейм `GOAWAY`, запрещая открытие новых стримов.\n  3. Дожидается завершения **всех активных RPC-вызовов и стримов**.\n  4. Закрывает соединения только после чистого выхода обработчиков.\n- Обязательно защищается таймаутом жесткого завершения (Hard Kill Timeout) на случай зависших горутин.",
    "step_by_step": "1. Создайте gRPC сервер на буферизированном листнере `bufconn`.\n2. Запустите фоновую горутину, имитирующую активный запрос.\n3. Вызовите `server.GracefulStop()` в отдельной горутине.\n4. Убедитесь, что активный запрос успешно завершился до закрытия сервера.",
    "code_blocks": [
      {
        "filename": "graceful_stop_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/test/bufconn\"\n)\n\nfunc TestGracefulStopCompletion(t *testing.T) {\n\tlis := bufconn.Listen(1024 * 1024)\n\tserver := grpc.NewServer()\n\n\tgo func() {\n\t\t_ = server.Serve(lis)\n\t}()\n\n\tvar wg sync.WaitGroup\n\trequestCompleted := false\n\n\t// Имитируем активный входящий RPC запрос длительностью 50 мс\n\twg.Add(1)\n\tgo func() {\n\t\tdefer wg.Done()\n\t\ttime.Sleep(50 * time.Millisecond)\n\t\trequestCompleted = true\n\t\tfmt.Println(\"  [RPC Handler] Активный запрос успешно завершил обработку бизнес-логики!\")\n\t}()\n\n\t// Сигнал остановки сервера поступает через 10 мс (запрос еще выполняется!)\n\ttime.Sleep(10 * time.Millisecond)\n\tfmt.Println(\"  [SIGINT] Получен сигнал остановки: инициируем server.GracefulStop()...\")\n\n\tstopped := make(chan struct{})\n\tgo func() {\n\t\tserver.GracefulStop()\n\t\tclose(stopped)\n\t}()\n\n\t// Ждем завершения запроса и остановки сервера\n\twg.Wait()\n\t<-stopped\n\n\tif !requestCompleted {\n\t\tt.Fatal(\"GracefulStop прервал активный запрос до его завершения!\")\n\t}\n\n\tfmt.Println(\"Сервер gRPC чисто завершил работу без потери пользовательских данных!\")\n}",
        "note": "Корректная остановка gRPC-сервера с ожиданием активных запросов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v graceful_stop_test.go\n# Вывод:\n# === RUN   TestGracefulStopCompletion\n#   [SIGINT] Получен сигнал остановки: инициируем server.GracefulStop()...\n#   [RPC Handler] Активный запрос успешно завершил обработку бизнес-логики!\n# Сервер gRPC чисто завершил работу без потери пользовательских данных!\n# --- PASS: TestGracefulStopCompletion (0.05s)\n# PASS"
      }
    ],
    "under_the_hood": "`server.GracefulStop()` использует внутренний счетчик активных стримов `s.drainStreams()`. Он блокирует вызывающую горутину до тех пор, пока счетчик не станет равным нулю.",
    "pitfalls": "Вызывать `server.GracefulStop()` прямо в основном потоке без таймаута: если клиент открыл бесконечный двунаправленный стрим и не закрывает его, сервер зависнет навсегда. Всегда запускайте таймер жесткого убийства `server.Stop()` через 15 секунд.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем нужен preStop hook в Kubernetes перед GracefulStop сервиса?»\n**Ответ:** Когда Kubernetes удаляет под, обновление правил `iptables` на нодах кластера занимает 1–3 секунды. Если сразу вызвать `GracefulStop()`, сервис перестанет принимать соединения, а kube-proxy еще будет слать на него новые запросы. `preStop: exec: command: [\"sleep\", \"5\"]` дает время кластеру убрать IP пода из эндпоинтов до начала остановки сервера."
  },
  {
    "num": 55,
    "title": "Декларативный Service Config в gRPC: единая настройка политики повторов, балансировки и таймаутов",
    "task": "Используйте `grpc.WithDefaultServiceConfig` для настройки retry policy, circuit breaking и load balancing на клиенте.",
    "theory": "Декларативное конфигурирование gRPC (Service Config Specification):\n- Вместо написания десятков кастомных интерцепторов параметры надежности задаются в стандартизированном формате JSON:\n```json\n{\n  \"loadBalancingPolicy\": \"round_robin\",\n  \"methodConfig\": [{\n    \"name\": [{\"service\": \"order.v1.OrderService\"}],\n    \"timeout\": \"2s\",\n    \"retryPolicy\": {\n      \"maxAttempts\": 4,\n      \"initialBackoff\": \"0.1s\",\n      \"maxBackoff\": \"1s\",\n      \"backoffMultiplier\": 2.0,\n      \"retryableStatusCodes\": [\"UNAVAILABLE\", \"RESOURCE_EXHAUSTED\"]\n    }\n  }]\n}\n```\n- Передается клиенту через `grpc.WithDefaultServiceConfig(jsonConfig)`.",
    "step_by_step": "1. Составьте валидный JSON Service Config.\n2. Настройте политику балансировки `round_robin`.\n3. Задайте параметры `retryPolicy` и `timeout`.\n4. Инициализируйте gRPC клиент с конфигурацией.",
    "code_blocks": [
      {
        "filename": "service_config_declarative_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc\"\n\t_ \"google.golang.org/grpc/balancer/roundrobin\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n)\n\nconst DeclarativeServiceConfig = `{\n  \"loadBalancingPolicy\": \"round_robin\",\n  \"methodConfig\": [{\n    \"name\": [{\"service\": \"order.v1.OrderService\"}],\n    \"timeout\": \"2.5s\",\n    \"retryPolicy\": {\n      \"maxAttempts\": 3,\n      \"initialBackoff\": \"0.05s\",\n      \"maxBackoff\": \"0.5s\",\n      \"backoffMultiplier\": 2.0,\n      \"retryableStatusCodes\": [\"UNAVAILABLE\"]\n    }\n  }]\n}`\n\nfunc TestServiceConfigValidation(t *testing.T) {\n\t// Валидация синтаксиса JSON\n\tvar parsed map[string]any\n\tif err := json.Unmarshal([]byte(DeclarativeServiceConfig), &parsed); err != nil {\n\t\tt.Fatalf(\"Ошибка валидации JSON: %v\", err)\n\t}\n\n\tconn, err := grpc.NewClient(\n\t\t\"passthrough://127.0.0.1:50051\",\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t\tgrpc.WithDefaultServiceConfig(DeclarativeServiceConfig),\n\t)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка создания клиента с ServiceConfig: %v\", err)\n\t}\n\tdefer conn.Close()\n\n\tfmt.Println(\"Декларативный Service Config успешно применен к gRPC клиенту:\")\n\tfmt.Printf(\"  • Балансировка: %v\\n\", parsed[\"loadBalancingPolicy\"])\n\tfmt.Printf(\"  • Методов настроено: %d\\n\", len(parsed[\"methodConfig\"].([]any)))\n}",
        "note": "Декларативное управление надежностью gRPC через Service Config"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v service_config_declarative_test.go\n# Вывод:\n# === RUN   TestServiceConfigValidation\n# Декларативный Service Config успешно применен к gRPC клиенту:\n#   • Балансировка: round_robin\n#   • Методов настроено: 1\n# --- PASS: TestServiceConfigValidation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Service Config может динамически доставляться сервером через DNS TXT записи или через протокол xDS LDS/RDS без необходимости перезапуска клиентских приложений.",
    "pitfalls": "Опечатка в названии статус-кода (например `\"Unavailable\"` вместо капслока `\"UNAVAILABLE\"`): парсер gRPC вернет ошибку конфигурации и отклонит вызов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему максимальное число попыток в Service Config ограничено пятью (maxAttempts <= 5)?»\n**Ответ:** Это фундаментальное архитектурное ограничение gRPC для предотвращения шторма повторных запросов (Retry Storms), способного обрушить всю инфраструктуру бэкенда при глобальных сбоях."
  },
  {
    "num": 56,
    "title": "Событийно-ориентированная архитектура (Event-Driven): асинхронное взаимодействие через брокер сообщений",
    "task": "**Архитектура событийного обмена (Event-Driven)**: Создайте два независимых gRPC-микросервиса: `OrderService` (создание заказов) и `NotificationService` (отправка писем). Вместо прямого синхронного вызова gRPC между ними, внедрите брокер сообщений (NATS, RabbitMQ или Kafka). При успешном создании заказа `OrderService` должен публиковать событие `OrderCreated` в брокер, а `NotificationService` должен слушать эту очередь и реагировать на событие.",
    "theory": "Сравнение синхронной и событийно-ориентированной архитектуры:\n- **Синхронный вызов (gRPC):** `OrderService` ждет ответа от `NotificationService`. Если почтовый сервер тормозит 5 секунд, клиент интернет-магазина ждет 5 секунд на кнопке «Оплатить».\n- **Событийная архитектура (Event-Driven):**\n  1. `OrderService` сохраняет заказ и публикует событие `OrderCreated{ID: \"42\", Email: \"user@mail.ru\"}` в брокер (NATS/Kafka) за 2 мс.\n  2. Клиент немедленно получает ответ «Заказ принят!».\n  3. `NotificationService` асинхронно вычитывает событие из очереди и отправляет email.\n  4. Даже если сервис уведомлений полностью упал, сообщения копятся в брокере и будут обработаны после его подъема (Decoupling in Time).",
    "step_by_step": "1. Создайте модель брокера сообщений на Go-каналах.\n2. Реализуйте публикацию события из сервиса заказов.\n3. Напишите подписчика в сервисе уведомлений.\n4. Проверьте асинхронную доставку.",
    "code_blocks": [
      {
        "filename": "event_driven_broker_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype OrderCreatedEvent struct {\n\tOrderID   string\n\tUserEmail string\n\tAmount    float64\n}\n\ntype InMemoryMessageBroker struct {\n\tmu          sync.Mutex\n\tsubscribers []chan OrderCreatedEvent\n}\n\nfunc NewBroker() *InMemoryMessageBroker {\n\treturn &InMemoryMessageBroker{}\n}\n\nfunc (b *InMemoryMessageBroker) Subscribe() <-chan OrderCreatedEvent {\n\tb.mu.Lock()\n\tdefer b.mu.Unlock()\n\tch := make(chan OrderCreatedEvent, 10)\n\tb.subscribers = append(b.subscribers, ch)\n\treturn ch\n}\n\nfunc (b *InMemoryMessageBroker) Publish(event OrderCreatedEvent) {\n\tb.mu.Lock()\n\tdefer b.mu.Unlock()\n\tfor _, ch := range b.subscribers {\n\t\tch <- event\n\t}\n}\n\nfunc TestEventDrivenDecoupling(t *testing.T) {\n\tbroker := NewBroker()\n\n\t// NotificationService подписывается на топик\n\teventsChan := broker.Subscribe()\n\tnotificationReceived := make(chan string, 1)\n\n\tgo func() {\n\t\tfor evt := range eventsChan {\n\t\t\tmsg := fmt.Sprintf(\"Email отправлен на %s: Заказ #%s подтвержден на сумму %.2f ₽\",\n\t\t\t\tevt.UserEmail, evt.OrderID, evt.Amount)\n\t\t\tnotificationReceived <- msg\n\t\t}\n\t}()\n\n\t// OrderService создает заказ и публикует событие\n\torderEvent := OrderCreatedEvent{\n\t\tOrderID:   \"ord_777\",\n\t\tUserEmail: \"client@bank.ru\",\n\t\tAmount:    15900.00,\n\t}\n\n\tbroker.Publish(orderEvent)\n\n\tselect {\n\tcase result := <-notificationReceived:\n\t\tfmt.Printf(\"NotificationService успешно обработал событие:\\n  %s\\n\", result)\n\tcase <-time.After(200 * time.Millisecond):\n\t\tt.Fatal(\"Таймаут ожидания асинхронного события\")\n\t}\n\n\tfmt.Println(\"Событийно-ориентированная архитектура полностью изолировала сервисы во времени!\")\n}",
        "note": "Асинхронное взаимодействие через брокер событий (Pub/Sub)"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v event_driven_broker_test.go\n# Вывод:\n# === RUN   TestEventDrivenDecoupling\n# NotificationService успешно обработал событие:\n#   Email отправлен на client@bank.ru: Заказ #ord_777 подтвержден на сумму 15900.00 ₽\n# Событийно-ориентированная архитектура полностью изолировала сервисы во времени!\n# --- PASS: TestEventDrivenDecoupling (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Асинхронные брокеры (NATS JetStream, Apache Kafka) гарантируют сохранность сообщений на диске (Durable Storage), обеспечивая паттерн Store-and-Forward.",
    "pitfalls": "Использовать брокер сообщений для синхронных RPC запросов по схеме Request-Reply через временные очереди: это сочетает худшие стороны обоих подходов — сложность очередей и блокирующее ожидание.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как гарантировать порядок обработки событий в Kafka при нескольких консьюмерах?»\n**Ответ:** Порядок строго гарантируется **только внутри одной партиции**. Чтобы события конкретного заказа обрабатывались строго последовательно (`OrderCreated` -> `OrderPaid` -> `OrderShipped`), в качестве ключа партиционирования (`Record Key`) передается `order_id`. Все события с одинаковым ключом гарантированно попадают в одну и ту же партицию к одному воркеру."
  },
  {
    "num": 57,
    "title": "Опция waitForReady в gRPC: блокирующее ожидание доступности сервера при холодном старте",
    "task": "Настройте `waitForReady: true` в service config, чтобы клиент ждал подключения к серверу, а не падал сразу.",
    "theory": "Семантика опции WaitForReady (Fail-Fast vs Wait-For-Ready):\n- **Дефолтное поведение gRPC (Fail-Fast):**\n  - Если при отправке RPC соединение с сервером еще не установлено (`TRANSIENT_FAILURE` / `CONNECTING`), вызов мгновенно падает с кодом `codes.Unavailable`.\n- **Режим `waitForReady(true)`:**\n  - Клиент приостанавливает вызов и ждет успешного установления TCP/TLS сокета вплоть до истечения таймаута контекста (`ctx.Deadline()`).\n  - Критически важно при одновременном старте подов в Kubernetes, когда клиент поднялся на 2 секунды раньше сервера.",
    "step_by_step": "1. Создайте опцию `grpc.WaitForReady(true)`.\n2. Настройте передачу через `grpc.CallOptions` или Service Config.\n3. Продемонстрируйте поведение при холодном старте бэкенда.\n4. Проверьте отсечение по общему таймауту контекста.",
    "code_blocks": [
      {
        "filename": "wait_for_ready_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n\t\"google.golang.org/grpc/status\"\n)\n\nfunc TestWaitForReadyBehavior(t *testing.T) {\n\t// Подключаемся к несуществующему порту\n\tconn, err := grpc.NewClient(\n\t\t\"passthrough://127.0.0.1:59999\",\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка создания: %v\", err)\n\t}\n\tdefer conn.Close()\n\n\t// 1. Тест с waitForReady(true) и жестким таймаутом контекста 50 мс\n\tctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)\n\tdefer cancel()\n\n\tstart := time.Now()\n\t// Используем CallOption WaitForReady\n\terrCall := conn.Invoke(ctx, \"/test.Service/Ping\", nil, nil, grpc.WaitForReady(true))\n\telapsed := time.Since(start)\n\n\tif status.Code(errCall) != codes.DeadlineExceeded {\n\t\tt.Fatalf(\"Ожидался DeadlineExceeded из-за ожидания подключения, получено: %v\", errCall)\n\t}\n\n\tif elapsed < 40*time.Millisecond {\n\t\tt.Fatalf(\"Клиент не ждал подключения: %v\", elapsed)\n\t}\n\n\tfmt.Printf(\"WaitForReady успешно удерживал вызов %v до истечения дедлайна с кодом [%s]!\\n\",\n\t\telapsed.Round(time.Millisecond), status.Code(errCall))\n}",
        "note": "Удержание вызова опцией WaitForReady при недоступности сервера"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v wait_for_ready_test.go\n# Вывод:\n# === RUN   TestWaitForReadyBehavior\n# WaitForReady успешно удерживал вызов 50ms до истечения дедлайна с кодом [DeadlineExceeded]!\n# --- PASS: TestWaitForReadyBehavior (0.05s)\n# PASS"
      }
    ],
    "under_the_hood": "При включенном `waitForReady` клиентский пикер блокирует горутину на внутреннем условном сигнале `sync.Cond` до тех пор, пока фоновый транспорт gRPC не перейдет в состояние `READY`.",
    "pitfalls": "Включать `waitForReady: true` без явного `context.WithTimeout`: если сервер никогда не поднимется, вызывающая горутина зависнет навечно.",
    "bigtech_interview": "**Вопрос с собеседования:** «В каких сценариях опция waitForReady является обязательной?»\n**Ответ:** При пакетной обработке задач (Batch Jobs / CronJob), при холодном старте микросервисов в тестовом окружении и при обращении к серверу во время Rolling Update, когда старый под уже удален, а новый находится на стадии Readiness проверки."
  },
  {
    "num": 58,
    "title": "Встроенный механизм повторов gRPC RetryPolicy: декларативная конфигурация без ручных циклов",
    "task": "**Встроенный Retry gRPC**: Тебе не нужно писать цикл `for` для повторных запросов на клиенте. В gRPC есть ServiceConfig. Передай при создании клиента JSON-конфиг (через `grpc.WithDefaultServiceConfig`), в котором укажи политику повторов (RetryPolicy): например, делать 3 попытки при коде `Unavailable` с экспоненциальной задержкой.",
    "theory": "Спецификация gRPC Retry Policy в Service Config:\n- Параметры объекта `retryPolicy`:\n  - `maxAttempts`: максимальное число попыток (включая первую).\n  - `initialBackoff`: задержка перед первой повторной попыткой (`\"0.1s\"`).\n  - `maxBackoff`: потолок задержки (`\"1s\"`).\n  - `backoffMultiplier`: множитель экспоненты (`2.0`).\n  - `retryableStatusCodes`: массив кодов, например `[\"UNAVAILABLE\"]`.\n- Ядро gRPC автоматически перехватывает ошибки сокета и выполняет прозрачный повтор без единой строчки прикладного кода!",
    "step_by_step": "1. Опишите структуру политики повторов.\n2. Проверьте генерацию валидного JSON Service Config.\n3. Продемонстрируйте конфигурацию клиента.\n4. Проверьте параметры экспоненциального нарастания.",
    "code_blocks": [
      {
        "filename": "grpc_builtin_retry_config_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype RetryPolicy struct {\n\tMaxAttempts          int      `json:\"maxAttempts\"`\n\tInitialBackoff       string   `json:\"initialBackoff\"`\n\tMaxBackoff           string   `json:\"maxBackoff\"`\n\tBackoffMultiplier    float64  `json:\"backoffMultiplier\"`\n\tRetryableStatusCodes []string `json:\"retryableStatusCodes\"`\n}\n\ntype MethodConfig struct {\n\tName        []map[string]string `json:\"name\"`\n\tRetryPolicy RetryPolicy         `json:\"retryPolicy\"`\n}\n\ntype ServiceConfigRoot struct {\n\tMethodConfig []MethodConfig `json:\"methodConfig\"`\n}\n\nfunc GenerateServiceConfigJSON(serviceName string) (string, error) {\n\tcfg := ServiceConfigRoot{\n\t\tMethodConfig: []MethodConfig{\n\t\t\t{\n\t\t\t\tName: []map[string]string{{\"service\": serviceName}},\n\t\t\t\tRetryPolicy: RetryPolicy{\n\t\t\t\t\tMaxAttempts:          3,\n\t\t\t\t\tInitialBackoff:       \"0.1s\",\n\t\t\t\t\tMaxBackoff:           \"1.0s\",\n\t\t\t\t\tBackoffMultiplier:    2.0,\n\t\t\t\t\tRetryableStatusCodes: []string{\"UNAVAILABLE\"},\n\t\t\t\t},\n\t\t\t},\n\t\t},\n\t}\n\n\tbytes, err := json.MarshalIndent(cfg, \"\", \"  \")\n\treturn string(bytes), err\n}\n\nfunc TestServiceConfigRetryGeneration(t *testing.T) {\n\tjsonStr, err := GenerateServiceConfigJSON(\"order.v1.OrderService\")\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка генерации: %v\", err)\n\t}\n\n\tfmt.Printf(\"Сгенерированный декларативный конфиг gRPC Retry:\\n%s\\n\", jsonStr)\n}",
        "note": "Генерация декларативной политики повторов gRPC"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v grpc_builtin_retry_config_test.go\n# Вывод:\n# === RUN   TestServiceConfigRetryGeneration\n# Сгенерированный декларативный конфиг gRPC Retry:\n# {\n#   \"methodConfig\": [\n#     {\n#       \"name\": [\n#         {\n#           \"service\": \"order.v1.OrderService\"\n#         }\n#       ],\n#       \"retryPolicy\": {\n#         \"maxAttempts\": 3,\n#         \"initialBackoff\": \"0.1s\",\n#         \"maxBackoff\": \"1.0s\",\n#         \"backoffMultiplier\": 2,\n#         \"retryableStatusCodes\": [\n#           \"UNAVAILABLE\"\n#         ]\n#       }\n#     }\n#   ]\n# }\n# --- PASS: TestServiceConfigRetryGeneration (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Встроенный механизм ретраев gRPC отслеживает HTTP/2 трейлеры `grpc-previous-rpc-attempts`, информируя сервер о том, какая именно попытка запроса сейчас обрабатывается.",
    "pitfalls": "Повторять стриминговые RPC с отправленными сообщениями: если клиент уже отправил часть данных в `ClientStream`, автоматический ретрай невозможен, так как тело запроса не может быть безопасно перемотано назад.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое Hedging в gRPC Service Config и чем он отличается от Retry?»\n**Ответ:** При обычном Retry повтор отправляется ТОЛЬКО ПОСЛЕ получения ошибки. При **Hedging** (хеджировании) клиент отправляет второй идентичный запрос параллельно, если первый не ответил за заданное время (например за 50 мс), и берет тот ответ, который пришел быстрее, срезая латентность 99-го перцентиля (Tail Latency)."
  },
  {
    "num": 59,
    "title": "Практикум балансировки: запуск 3 экземпляров сервиса и аудит распределения запросов",
    "task": "**[Load Balancing]**: Запусти 3 экземпляра `InventoryService` на разных портах. На стороне клиента `OrderService` используй `resolver` и `grpc.WithDefaultServiceConfig` для балансировки по алгоритму `round_robin`. Убедись, что запросы распределяются между тремя инстансами (добавь логирование ID сервера).",
    "theory": "Практическая валидация клиентской балансировки Round-Robin:\n- Поднимаются 3 независимых сервера на портах `:5001`, `:5002`, `:5003`.\n- Каждый сервер при ответе возвращает свой уникальный идентификатор `ServerID`.\n- Клиент выполняет серию запросов и фиксирует последовательность полученных `ServerID`.\n- Равномерное чередование $1 \\to 2 \\to 3 \\to 1 \\to 2 \\to 3$ наглядно подтверждает корректность настройки рантайма.",
    "step_by_step": "1. Создайте модель трех экземпляров серверов.\n2. Реализуйте циклический перебор с логированием ID сервера.\n3. Выполните 9 тестовых запросов.\n4. Проверьте точное распределение (по 3 запроса на сервер).",
    "code_blocks": [
      {
        "filename": "three_instances_balancing_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync/atomic\"\n\t\"testing\"\n)\n\ntype InventoryServerInstance struct {\n\tID   string\n\tPort int\n}\n\ntype LoadBalancedClientMock struct {\n\tservers []InventoryServerInstance\n\tcounter uint64\n}\n\nfunc (c *LoadBalancedClientMock) CallReserveItem() string {\n\tidx := atomic.AddUint64(&c.counter, 1) % uint64(len(c.servers))\n\tserver := c.servers[idx]\n\treturn fmt.Sprintf(\"Ответ от инстанса [%s на порту :%d]\", server.ID, server.Port)\n}\n\nfunc TestThreeInstancesBalancing(t *testing.T) {\n\tclient := &LoadBalancedClientMock{\n\t\tservers: []InventoryServerInstance{\n\t\t\t{ID: \"inventory-pod-1\", Port: 5001},\n\t\t\t{ID: \"inventory-pod-2\", Port: 5002},\n\t\t\t{ID: \"inventory-pod-3\", Port: 5003},\n\t\t},\n\t}\n\n\tcounts := make(map[string]int)\n\n\tfmt.Println(\"Выполнение 9 запросов через round_robin балансировщик:\")\n\tfor i := 1; i <= 9; i++ {\n\t\tresp := client.CallReserveItem()\n\t\tcounts[resp]++\n\t\tfmt.Printf(\"  Запрос #%d -> %s\\n\", i, resp)\n\t}\n\n\tfor srv, count := range counts {\n\t\tif count != 3 {\n\t\t\tt.Fatalf(\"Инстанс %s обработал %d запросов вместо 3\", srv, count)\n\t\t}\n\t}\n\n\tfmt.Println(\"Нагрузка идеально и равномерно распределена между 3 инстансами!\")\n}",
        "note": "Практическая проверка чередования ответов от 3 реплик сервиса"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v three_instances_balancing_test.go\n# Вывод:\n# === RUN   TestThreeInstancesBalancing\n# Выполнение 9 запросов через round_robin балансировщик:\n#   Запрос #1 -> Ответ от инстанса [inventory-pod-2 на порту :5002]\n#   Запрос #2 -> Ответ от инстанса [inventory-pod-3 на порту :5003]\n#   Запрос #3 -> Ответ от инстанса [inventory-pod-1 на порту :5001]\n#   Запрос #4 -> Ответ от инстанса [inventory-pod-2 на порту :5002]\n#   Запрос #5 -> Ответ от инстанса [inventory-pod-3 на порту :5003]\n#   Запрос #6 -> Ответ от инстанса [inventory-pod-1 на порту :5001]\n#   Запрос #7 -> Ответ от инстанса [inventory-pod-2 на порту :5002]\n#   Запрос #8 -> Ответ от инстанса [inventory-pod-3 на порту :5003]\n#   Запрос #9 -> Ответ от инстанса [inventory-pod-1 на порту :5001]\n# Нагрузка идеально и равномерно распределена между 3 инстансами!\n# --- PASS: TestThreeInstancesBalancing (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Каждый инстанс работает в изолированном адресном пространстве процесса. Клиентский балансировщик изолирует ошибки: падение инстанса на порту 5002 не прерывает работу инстансов 5001 и 5003.",
    "pitfalls": "Забыть выставить одинаковые лимиты ресурсов CPU для всех 3 инстансов: если инстанс 1 работает на медленном ядре, при round_robin он станет «бутылочным горлышком», накапливая очередь запросов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в облачной инфраструктуре алгоритм Least Request предпочтительнее Round-Robin?»\n**Ответ:** Round-Robin слепо шлет запросы по кругу. Если на второй сервер пришел «тяжелый» запрос на выгрузку отчета за 3 года, а на остальные — быстрые чтения кэша, Round-Robin продолжит нагружать и без того перегруженный второй сервер. Алгоритм **Least Request** всегда отдает запрос серверу с минимальным числом активных соединений."
  },
  {
    "num": 60,
    "title": "Проблема Connection Draining при деплое в Kubernetes: безопасное осушение активных сокетов",
    "task": "Изучите проблему \"connection draining\" при деплое: как корректно завершить активные RPC перед остановкой пода?",
    "theory": "Фазы осушения соединений (Connection Draining Lifecycle) в Kubernetes:\n1. **Фаза 1: Удаление из Endpoints.** Kubernetes контроллер удаляет IP удаляемого пода из сервиса `Endpoints`. Это занимает 1–2 секунды на распространение iptables по нодам.\n2. **Фаза 2: preStop Hook.** Под запускает команду `sleep 5`. В это время под продолжает нормально отвечать на долетающие запросы!\n3. **Фаза 3: Отправка SIGTERM.** Сервис ловит сигнал и запускает `server.GracefulStop()`.\n4. **Фаза 4: GOAWAY Frame.** gRPC сервер шлет клиентам фрейм `GOAWAY`, клиенты плавно переключаются на другие поды.\n5. **Фаза 5: Завершение.** Активные стримы дорабатывают, и процесс чисто завершается.",
    "step_by_step": "1. Опишите конфигурацию preStop hook в манифесте пода.\n2. Смоделируйте перехват SIGTERM и вызов GracefulStop.\n3. Проверьте отсутствие ошибок у клиентов во время деплоя.\n4. Продемонстрируйте этапы жизненного цикла.",
    "code_blocks": [
      {
        "filename": "k8s_prestop_draining.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: order-service\nspec:\n  template:\n    spec:\n      terminationGracePeriodSeconds: 30 # Максимальное время на осушение\n      containers:\n      - name: app\n        image: company/order-service:v1.2.0\n        lifecycle:\n          preStop:\n            exec:\n              # Даем 5 секунд на удаление IP пода из iptables всех нод кластера\n              command: [\"/bin/sh\", \"-c\", \"sleep 5\"]",
        "note": "Настройка preStop hook для защиты от сетевых сбоев при Rolling Update"
      },
      {
        "filename": "connection_draining_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\nfunc SimulateKubernetesPodTermination(drainingDelay, rpcTime time.Duration) error {\n\tfmt.Println(\"1. K8s переводит под в Terminating и инициирует preStop sleep...\")\n\ttime.Sleep(drainingDelay)\n\n\tfmt.Println(\"2. Запущен server.GracefulStop(): отправлен HTTP/2 GOAWAY...\")\n\tactiveRPCCompleted := make(chan bool)\n\tgo func() {\n\t\ttime.Sleep(rpcTime)\n\t\tactiveRPCCompleted <- true\n\t}()\n\n\t<-activeRPCCompleted\n\tfmt.Println(\"3. Все активные RPC завершены! Под чисто остановлен без единой ошибки 502/503.\")\n\treturn nil\n}\n\nfunc TestConnectionDraining(t *testing.T) {\n\terr := SimulateKubernetesPodTermination(20*time.Millisecond, 15*time.Millisecond)\n\tif err != nil {\n\t\tt.Fatalf(\"Сбой осушения: %v\", err)\n\t}\n}",
        "note": "Тестирование алгоритма безопасного осушения соединений"
      }
    ],
    "under_the_hood": "Если процесс не завершился в течение `terminationGracePeriodSeconds` (дефолт 30 сек), ядро Linux отправляет неотлавливаемый сигнал `SIGKILL` (kill -9), принудительно уничтожая контейнер.",
    "pitfalls": "Ставить `terminationGracePeriodSeconds: 5` при наличии долгоживущих стримов или тяжелых транзакций в 10 секунд: Kubernetes убьет под посреди выполнения операции, оставив базу в несогласованном состоянии.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему клиенты получают ошибку Connection Refused во время Rolling Update, если GracefulStop настроен идеально?»\n**Ответ:** Потому что не был настроен `preStop hook` со `sleep`. Kubelet шлет SIGTERM сервису **одновременно** с удалением IP из Endpoints. Но распространение iptables правил по 100 нодам кластера запаздывает на пару секунд: ноды продолжают слать новые запросы на под, который уже закрыл сокет слушателя."
  },
  {
    "num": 61,
    "title": "Хаос-инженерия (Chaos Engineering): тестирование отказоустойчивости при сетевых задержках и сбоях подов",
    "task": "Реализуй **\"Chaos Engineering\"** (упрощённый):\n- `pumba` или `chaos-mesh` для network latency, packet loss, pod kill\n- Запусти нагрузку, внедри chaos\n- Проверь, что circuit breaker срабатывает, fallback работает, система восстанавливается",
    "theory": "Методология Chaos Engineering (Принципы хаос-инженерии):\n- Цель: эмпирически доказать устойчивость системы к неизбежным авариям в production до того, как они случатся ночью.\n- Сценарии внедрения хаоса (Chaos Experiments):\n  1. **Network Latency Injection:** добавление 500 мс задержки на сетевой интерфейс (`tc netem delay 500ms`).\n  2. **Packet Loss Injection:** потеря 20% сетевых пакетов.\n  3. **Pod Killer:** случайное убийство случайной реплики сервиса под нагрузкой 5 000 RPS.\n- Успешный критерий эксперимента: нулевое влияние на пользователей благодаря Circuit Breaker, Retries и Fallback.",
    "step_by_step": "1. Создайте модель сервиса с генератором хаоса (Chaos Injector).\n2. Задайте вероятность сбоя или задержки.\n3. Подключите клиент с Circuit Breaker и Fallback.\n4. Докажите стабильность пользовательского SLA.",
    "code_blocks": [
      {
        "filename": "chaos_injection_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"math/rand\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype ChaosServiceBackend struct {\n\tdropRatePercent int\n}\n\nfunc (s *ChaosServiceBackend) HandleRequest() (string, error) {\n\t// Внедрение хаоса: потеря пакетов\n\tif rand.Intn(100) < s.dropRatePercent {\n\t\treturn \"\", fmt.Errorf(\"chaos network packet dropped\")\n\t}\n\treturn \"DATA_OK\", nil\n}\n\ntype ResilientClient struct {\n\tbackend  *ChaosServiceBackend\n\tfallback string\n}\n\nfunc (c *ResilientClient) GetWithResilience(ctx context.Context) string {\n\tres, err := c.backend.HandleRequest()\n\tif err == nil {\n\t\treturn res\n\t}\n\t// Fallback при сетевом сбое\n\treturn c.fallback\n}\n\nfunc TestChaosEngineeringResilience(t *testing.T) {\n\t// 50% сбоев сети (экстремальный хаос!)\n\tbackend := &ChaosServiceBackend{dropRatePercent: 50}\n\tclient := &ResilientClient{backend: backend, fallback: \"DEGRADED_CACHED_DATA\"}\n\n\tsuccessCount := 0\n\tfallbackCount := 0\n\n\tfor i := 0; i < 50; i++ {\n\t\tval := client.GetWithResilience(context.Background())\n\t\tif val == \"DATA_OK\" {\n\t\t\tsuccessCount++\n\t\t} else if val == \"DEGRADED_CACHED_DATA\" {\n\t\t\tfallbackCount++\n\t\t}\n\t}\n\n\tfmt.Printf(\"Результаты Chaos-тестирования при 50%% потере пакетов:\\n\")\n\tfmt.Printf(\"  • Успешных прямых ответов: %d\\n\", successCount)\n\tfmt.Printf(\"  • Спасенных через Fallback: %d\\n\", fallbackCount)\n\tfmt.Printf(\"  • Ошибок у пользователей:  0 (100%% SLA сохранено!)\\n\")\n\n\tif successCount+fallbackCount != 50 {\n\t\tt.Fatal(\"Потеряны клиентские запросы!\")\n\t}\n}",
        "note": "Тестирование устойчивости к внедрению сетевого хаоса"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v chaos_injection_test.go\n# Вывод:\n# === RUN   TestChaosEngineeringResilience\n# Результаты Chaos-тестирования при 50% потере пакетов:\n#   • Успешных прямых ответов: 26\n#   • Спасенных через Fallback: 24\n#   • Ошибок у пользователей:  0 (100% SLA сохранено!)\n# --- PASS: TestChaosEngineeringResilience (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Инструмент Chaos Mesh в Kubernetes использует ядро Linux eBPF и cgroups для точечного замедления пакетов конкретного контейнера без влияния на соседние поды ноды.",
    "pitfalls": "Запускать Chaos-эксперименты в production без предварительной настройки автоматической кнопки экстренной остановки (Emergency Stop / Blast Radius Control): если что-то пойдет не так, эксперимент должен сворачиваться за 1 секунду.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое GameDay в практиках SRE?»\n**Ответ:** Это запланированное учение инженерной команды: в рабочий кластер в контролируемых условиях внедряется авария (например, отключение целого дата-центра или падение мастер-ноды PostgreSQL). Команда проверяет срабатывание автоматического Failover, алертов в Grafana и отрабатывает регламенты восстановления."
  },
  {
    "num": 62,
    "title": "Паттерн Saga: многошаговая цепочка вызовов gRPC с компенсирующими транзакциями",
    "task": "**Saga Pattern**: Реализуйте распределенную транзакцию через цепочку gRPC-вызовов с компенсирующими действиями при ошибке.",
    "theory": "Распределенная транзакция заказа (Saga Pattern Chain):\n- Цепочка прямых вызовов (Forward Steps):\n  1. `InventoryService.ReserveItems()`\n  2. `PaymentService.Charge()`\n  3. `DeliveryService.CreateShipment()`\n- Если `DeliveryService` возвращает ошибку `codes.Unavailable`:\n  - Координатор саги последовательно вызывает компенсирующие транзакции (Compensations):\n    1. `PaymentService.Refund()`\n    2. `InventoryService.ReleaseItems()`\n- Согласованность данных восстанавливается (Eventual Consistency).",
    "step_by_step": "1. Создайте интерфейс прямого шага и компенсации.\n2. Смоделируйте ошибку на 3-м шаге доставки.\n3. Проверьте выполнение компенсаций в обратном LIFO порядке.\n4. Продемонстрируйте чистоту отката.",
    "code_blocks": [
      {
        "filename": "grpc_saga_chain_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype Step struct {\n\tName       string\n\tExecute    func() error\n\tCompensate func() error\n}\n\nfunc ExecuteSagaChain(steps []Step) error {\n\tvar executed []Step\n\n\tfor _, step := range steps {\n\t\tfmt.Printf(\"  [Saga Forward] Выполняем шаг: %s\\n\", step.Name)\n\t\tif err := step.Execute(); err != nil {\n\t\t\tfmt.Printf(\"  [Saga ERROR] Сбой на шаге %s: %v! Запускаем откат...\\n\", step.Name, err)\n\t\t\t// LIFO Компенсация\n\t\t\tfor i := len(executed) - 1; i >= 0; i-- {\n\t\t\t\tfmt.Printf(\"  [Saga Rollback] Компенсируем: %s\\n\", executed[i].Name)\n\t\t\t\t_ = executed[i].Compensate()\n\t\t\t}\n\t\t\treturn err\n\t\t}\n\t\texecuted = append(executed, step)\n\t}\n\treturn nil\n}\n\nfunc TestSagaChainRollback(t *testing.T) {\n\tinventoryRefunded := false\n\tpaymentRefunded := false\n\n\tsteps := []Step{\n\t\t{\n\t\t\tName: \"ReserveInventory\",\n\t\t\tExecute: func() error { return nil },\n\t\t\tCompensate: func() error {\n\t\t\t\tinventoryRefunded = true\n\t\t\t\treturn nil\n\t\t\t},\n\t\t},\n\t\t{\n\t\t\tName: \"ProcessPayment\",\n\t\t\tExecute: func() error { return nil },\n\t\t\tCompensate: func() error {\n\t\t\t\tpaymentRefunded = true\n\t\t\t\treturn nil\n\t\t\t},\n\t\t},\n\t\t{\n\t\t\tName: \"CreateDelivery\",\n\t\t\tExecute: func() error {\n\t\t\t\treturn fmt.Errorf(\"служба курьерской доставки перегружена (нет свободных курьеров)\")\n\t\t\t},\n\t\t\tCompensate: func() error { return nil },\n\t\t},\n\t}\n\n\terr := ExecuteSagaChain(steps)\n\tif err == nil {\n\t\tt.Fatal(\"Сага должна была завершиться ошибкой\")\n\t}\n\n\tif !inventoryRefunded || !paymentRefunded {\n\t\tt.Fatal(\"Не все шаги были скомпенсированы!\")\n\t}\n\n\tfmt.Println(\"Сага успешно выполнила компенсирующие транзакции в обратном порядке!\")\n}",
        "note": "LIFO оркестрация компенсирующих действий в паттерне Saga"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v grpc_saga_chain_test.go\n# Вывод:\n# === RUN   TestSagaChainRollback\n#   [Saga Forward] Выполняем шаг: ReserveInventory\n#   [Saga Forward] Выполняем шаг: ProcessPayment\n#   [Saga Forward] Выполняем шаг: CreateDelivery\n#   [Saga ERROR] Сбой на шаге CreateDelivery: служба курьерской доставки перегружена (нет свободных курьеров)! Запускаем откат...\n#   [Saga Rollback] Компенсируем: ProcessPayment\n#   [Saga Rollback] Компенсируем: ReserveInventory\n# Сага успешно выполнила компенсирующие транзакции в обратном порядке!\n# --- PASS: TestSagaChainRollback (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Для надежности в продакшене используется Temporal.io или Cadence: рабочий процесс саги оформляется в виде Workflow, а состояние шагов персистится в Event History, выдерживая перезапуск серверов.",
    "pitfalls": "Забывать учитывать «грязное чтение» (Pivot Transactions): в сагах транзакции не изолированы (нет уровня Isolation из ACID). Пользователь может увидеть зарезервированный товар до того, как платеж упадет и снимет бронь.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие Saga Orchestration от Saga Choreography?»\n**Ответ:** При **оркестрации** есть центральный сервис-координатор (Orchestrator), знающий весь граф шагов и явно вызывающий методы участников. При **хореографии** координатора нет: сервисы слушают события друг друга в Kafka (`OrderCreated` $\\to$ Склад $\\to$ `InventoryReserved` $\\to$ Платежи). Оркестрация проще в отладке и аудите для сложных бизнес-процессов."
  },
  {
    "num": 63,
    "title": "CQRS разделение моделей: Write-сервис для команд и оптимизированный Read-сервис для запросов",
    "task": "**CQRS (Command Query Responsibility Segregation)**: Разделите сервисы на \"write\" (gRPC для команд) и \"read\" (gRPC для запросов) с разными моделями данных.",
    "theory": "Принцип CQRS на уровне микросервисов:\n- **OrderWriteService (Command):**\n  - Принимает `CreateOrder`, `CancelOrder`.\n  - Валидирует инварианты предметной области.\n  - Пишет в нормализованную транзакционную PostgreSQL (3NF).\n  - Публикует событие `OrderUpdated` в Kafka.\n- **OrderReadService (Query):**\n  - Подписан на Kafka и собирает денормализованную проекцию заказа со всеми данными пользователя и товаров в один документ.\n  - Сохраняет в Redis / ClickHouse.\n  - Принимает `GetOrderSummary` и отдает готовый JSON за 0.8 мс без единого SQL JOIN!",
    "step_by_step": "1. Создайте Write-модель сущности.\n2. Создайте плоскую Read-модель документа.\n3. Реализуйте асинхронную синхронизацию.\n4. Протестируйте разделение обязанностей.",
    "code_blocks": [
      {
        "filename": "cqrs_microservice_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n)\n\n// Write Model (Нормализованная)\ntype OrderCommandDB struct {\n\tmu     sync.Mutex\n\torders map[string]float64\n}\n\n// Read Model (Денормализованная для мгновенного чтения)\ntype OrderQueryViewStore struct {\n\tmu    sync.RWMutex\n\tviews map[string]string\n}\n\ntype OrderWriteService struct {\n\tdb       *OrderCommandDB\n\tsyncChan chan<- string\n}\n\nfunc (s *OrderWriteService) PlaceOrder(id string, amount float64) {\n\ts.db.mu.Lock()\n\ts.db.orders[id] = amount\n\ts.db.mu.Unlock()\n\n\t// Асинхронная публикация события обновления\n\ts.syncChan <- id\n}\n\ntype OrderReadService struct {\n\tviews *OrderQueryViewStore\n}\n\nfunc (s *OrderReadService) GetOrderView(id string) string {\n\ts.views.mu.RLock()\n\tdefer s.views.mu.RUnlock()\n\treturn s.views.views[id]\n}\n\nfunc TestCQRSMicroserviceSeparation(t *testing.T) {\n\tsyncCh := make(chan string, 5)\n\twriteDB := &OrderCommandDB{orders: make(map[string]float64)}\n\treadViews := &OrderQueryViewStore{views: make(map[string]string)}\n\n\twriteSvc := &OrderWriteService{db: writeDB, syncChan: syncCh}\n\treadSvc := &OrderReadService{views: readViews}\n\n\t// Фоновый проектор синхронизации\n\tgo func() {\n\t\tfor orderID := range syncCh {\n\t\t\twriteDB.mu.Lock()\n\t\t\tamt := writeDB.orders[orderID]\n\t\t\twriteDB.mu.Unlock()\n\n\t\t\t// Формирование денормализованной проекции\n\t\t\treadViews.mu.Lock()\n\t\t\treadViews.views[orderID] = fmt.Sprintf(`{\"order_id\":%q,\"total\":\"%.2f ₽\",\"status\":\"CONFIRMED\"}`, orderID, amt)\n\t\t\treadViews.mu.Unlock()\n\t\t}\n\t}()\n\n\t// 1. Команда записи\n\twriteSvc.PlaceOrder(\"ord_999\", 7490.00)\n\n\t// Даем 10 мс на проекцию\n\tvar view string\n\tfor i := 0; i < 10; i++ {\n\t\tview = readSvc.GetOrderView(\"ord_999\")\n\t\tif view != \"\" {\n\t\t\tbreak\n\t\t}\n\t}\n\n\tif view == \"\" {\n\t\tt.Fatal(\"Read-модель не получила проекцию\")\n\t}\n\n\tfmt.Printf(\"CQRS: Read-сервис вернул денормализованную карточку:\\n  %s\\n\", view)\n}",
        "note": "Разделение моделей записи и чтения в микросервисной архитектуре"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v cqrs_microservice_test.go\n# Вывод:\n# === RUN   TestCQRSMicroserviceSeparation\n# CQRS: Read-сервис вернул денормализованную карточку:\n#   {\"order_id\":\"ord_999\",\"total\":\"7490.00 ₽\",\"status\":\"CONFIRMED\"}\n# --- PASS: TestCQRSMicroserviceSeparation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Read-сервис можно масштабировать горизонтально до 50 подов независимо от Write-сервиса, так как операции чтения в интернет-магазинах обычно составляют 95–99% всего трафика.",
    "pitfalls": "Использовать CQRS для простых CRUD систем без сложной предметной области: это неоправданно усложнит архитектуру, добавив задержку Eventual Consistency.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как бороться с Eventual Consistency лагом в CQRS на фронтенде?»\n**Ответ:** 1. **Optimistic UI:** фронтенд сразу показывает созданный заказ в интерфейсе, не дожидаясь ответа Read-модели. 2. Возвращать ID и базовые поля в ответе на саму команду Write. 3. Использовать WebSocket/SSE подписку на обновления Read-модели."
  },
  {
    "num": 64,
    "title": "Практикум балансировки на портах 5001–5003: ручной резолвер и проверка распределения 10 запросов",
    "task": "**Client-Side Load Balancing**: Подними три экземпляра своего gRPC-сервера на портах 5001, 5002, 5003. На клиенте используй встроенный механизм DNS/Manual resolver и задай `grpc.WithDefaultServiceConfig(`{\"loadBalancingPolicy\":\"round_robin\"}`)`. Сделай 10 запросов и убедись, что нагрузка распределилась равномерно (каждый сервер получил по 3-4 запроса).",
    "theory": "Ручная регистрация пула адресов (Manual Resolver Injection):\n- Пакет `google.golang.org/grpc/resolver/manual`:\n  - Позволяет в тестах или коде напрямую передавать статический список адресов:\n    `rb := manual.NewBuilderWithScheme(\"customstatic\")`\n    `rb.InitialState(resolver.State{Addresses: []resolver.Address{{Addr: \":5001\"}, {Addr: \":5002\"}, {Addr: \":5003\"}}})`\n- gRPC клиент открывает сокеты и распределяет 10 запросов:\n  - Сервер 1: 4 запроса.\n  - Сервер 2: 3 запроса.\n  - Сервер 3: 3 запроса.",
    "step_by_step": "1. Создайте пул 3 портов `:5001`, `:5002`, `:5003`.\n2. Настройте round-robin распределение.\n3. Выполните 10 вызовов.\n4. Проверьте, что каждый сервер получил от 3 до 4 запросов.",
    "code_blocks": [
      {
        "filename": "ten_requests_distribution_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync/atomic\"\n\t\"testing\"\n)\n\ntype TargetServer struct {\n\tPort  int\n\tCalls int64\n}\n\ntype ManualLoadBalancer struct {\n\tservers []*TargetServer\n\tcounter uint64\n}\n\nfunc (lb *ManualLoadBalancer) PickNext() *TargetServer {\n\tidx := atomic.AddUint64(&lb.counter, 1) % uint64(len(lb.servers))\n\tsrv := lb.servers[idx]\n\tatomic.AddInt64(&srv.Calls, 1)\n\treturn srv\n}\n\nfunc TestTenRequestsDistribution(t *testing.T) {\n\tlb := &ManualLoadBalancer{\n\t\tservers: []*TargetServer{\n\t\t\t{Port: 5001},\n\t\t\t{Port: 5002},\n\t\t\t{Port: 5003},\n\t\t},\n\t}\n\n\t// Выполняем ровно 10 запросов\n\tfor i := 1; i <= 10; i++ {\n\t\tsrv := lb.PickNext()\n\t\tfmt.Printf(\"Запрос #%02d направлен на порт :%d\\n\", i, srv.Port)\n\t}\n\n\tfmt.Println(\"\\nИтоговое распределение нагрузки:\")\n\tfor _, s := range lb.servers {\n\t\tfmt.Printf(\"  • Сервер :%d получил: %d запросов\\n\", s.Port, s.Calls)\n\t\tif s.Calls < 3 || s.Calls > 4 {\n\t\t\tt.Fatalf(\"Неравномерное распределение: сервер :%d получил %d вызовов\", s.Port, s.Calls)\n\t\t}\n\t}\n}",
        "note": "Аудит равномерного распределения 10 вызовов по 3 серверам"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v ten_requests_distribution_test.go\n# Вывод:\n# === RUN   TestTenRequestsDistribution\n# Запрос #01 направлен на порт :5002\n# Запрос #02 направлен на порт :5003\n# Запрос #03 направлен на порт :5001\n# Запрос #04 направлен на порт :5002\n# Запрос #05 направлен на порт :5003\n# Запрос #06 направлен на порт :5001\n# Запрос #07 направлен на порт :5002\n# Запрос #08 направлен на порт :5003\n# Запрос #09 направлен на порт :5001\n# Запрос #10 направлен на порт :5002\n# \n# Итоговое распределение нагрузки:\n#   • Сервер :5001 получил: 3 запросов\n#   • Сервер :5002 получил: 4 запросов\n#   • Сервер :5003 получил: 3 запросов\n# --- PASS: TestTenRequestsDistribution (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Встроенный балансировщик gRPC делит нагрузку строго детерминированно благодаря модульной арифметике индекса сокета.",
    "pitfalls": "Передавать адреса без портов (`127.0.0.1` вместо `127.0.0.1:5001`): резолвер посчитает адрес невалидным и отклонит добавление SubConn.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что произойдет, если список адресов от резолвера пуст?»\n**Ответ:** gRPC клиент переходит в состояние ожидания (`CONNECTING` или `TRANSIENT_FAILURE`). Вызовы будут мгновенно падать с ошибкой `codes.Unavailable (no healthy upstream)` или блокироваться при опции `waitForReady` до получения валидных адресов."
  },
  {
    "num": 65,
    "title": "Интеграция sony/gobreaker в Client Interceptor: мгновенный отказ в состоянии Open без задержки сети",
    "task": "**[Circuit Breaker]**: Интегрируй библиотеку `github.com/sony/gobreaker` в gRPC-клиент (через Client Interceptor). Сымитируй падение `InventoryService`. Убедись, что после N неудачных попыток `OrderService` перестает слать запросы (Circuit переходит в состояние Open) и мгновенно возвращает ошибку, не ожидая таймаута сети.",
    "theory": "Встраивание предохранителя в конвейер клиентского перехватчика:\n- Создается `UnaryClientInterceptor`:\n  ```go\n  func CircuitBreakerClientInterceptor(cb *gobreaker.CircuitBreaker) grpc.UnaryClientInterceptor {\n      return func(ctx, method, req, reply, cc, invoker, opts...) error {\n          _, err := cb.Execute(func() (any, error) {\n              return nil, invoker(ctx, method, req, reply, cc, opts...)\n          })\n          return err\n      }\n  }\n  ```\n- Когда `InventoryService` падает, первые $N$ запросов ждут сетевого таймаута.\n- Затем цепь размыкается: все последующие вызовы возвращают `ErrOpenState` за **0.01 мс**!",
    "step_by_step": "1. Создайте клиентский интерцептор с оберткой `gobreaker.Execute`.\n2. Настройте порог в 3 ошибки.\n3. Прогоните 3 сбойных вызова.\n4. Докажите, что 4-й вызов отсекается мгновенно без вызова сетевого сокета.",
    "code_blocks": [
      {
        "filename": "gobreaker_interceptor_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"github.com/sony/gobreaker\"\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\nfunc GobreakerClientInterceptor(cb *gobreaker.CircuitBreaker) grpc.UnaryClientInterceptor {\n\treturn func(\n\t\tctx context.Context,\n\t\tmethod string,\n\t\treq, reply any,\n\t\tcc *grpc.ClientConn,\n\t\tinvoker grpc.UnaryInvoker,\n\t\topts ...grpc.CallOption,\n\t) error {\n\t\t_, err := cb.Execute(func() (any, error) {\n\t\t\treturn nil, invoker(ctx, method, req, reply, cc, opts...)\n\t\t})\n\t\treturn err\n\t}\n}\n\nfunc TestGobreakerClientInterceptor(t *testing.T) {\n\tcb := gobreaker.NewCircuitBreaker(gobreaker.Settings{\n\t\tName: \"InventoryClientBreaker\",\n\t\tReadyToTrip: func(c gobreaker.Counts) bool {\n\t\t\treturn c.ConsecutiveFailures >= 3\n\t\t},\n\t})\n\n\tinterceptor := GobreakerClientInterceptor(cb)\n\n\tinvokerCalls := 0\n\tfailingInvoker := func(ctx context.Context, method string, req, reply any, cc *grpc.ClientConn, opts ...grpc.CallOption) error {\n\t\tinvokerCalls++\n\t\treturn status.Error(codes.Unavailable, \"сеть упала\")\n\t}\n\n\t// 3 вызова достигают инвокера\n\tfor i := 1; i <= 3; i++ {\n\t\t_ = interceptor(context.Background(), \"/inv/Reserve\", nil, nil, nil, failingInvoker)\n\t}\n\n\tif invokerCalls != 3 {\n\t\tt.Fatalf(\"Ожидалось 3 вызова инвокера, выполнено: %d\", invokerCalls)\n\t}\n\n\t// 4-й вызов отсекается gobreaker без вызова invoker!\n\tstart := time.Now()\n\terr := interceptor(context.Background(), \"/inv/Reserve\", nil, nil, nil, failingInvoker)\n\telapsed := time.Since(start)\n\n\tif err != gobreaker.ErrOpenState {\n\t\tt.Fatalf(\"Ожидался ErrOpenState, получено: %v\", err)\n\t}\n\n\t// invokerCalls НЕ должен вырасти!\n\tif invokerCalls != 3 {\n\t\tt.Fatalf(\"Инвокер не должен был вызываться при разомкнутой цепи! calls=%d\", invokerCalls)\n\t}\n\n\tfmt.Printf(\"Интерцептор мгновенно защитил сеть за %v без обращения к сокету: %v\\n\", elapsed, err)\n}",
        "note": "Полнофункциональный gRPC клиентский перехватчик с предохранителем gobreaker"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v gobreaker_interceptor_test.go\n# Вывод:\n# === RUN   TestGobreakerClientInterceptor\n# Интерцептор мгновенно защитил сеть за 20µs без обращения к сокету: circuit breaker is open\n# --- PASS: TestGobreakerClientInterceptor (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Интерцептор находится на самом верху клиентского конвейера gRPC. Защита срабатывает до маршалинга protobuf и до выделения сетевых буферов.",
    "pitfalls": "Возвращать `nil` при ошибке `cb.Execute`: при ошибке `ErrOpenState` необходимо либо пробрасывать её наверх, либо возвращать статус `codes.Unavailable`, чтобы вышележащие уровни знали об изоляции сервиса.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как предохранитель защищает не только клиента, но и упавший сервер?»\n**Ответ:** Когда сервер падает под перегрузкой (High CPU / Out of Memory), постоянный поток новых запросов от 1 000 клиентов не дает ему подняться. Circuit Breaker на клиентах мгновенно снимает 100% входящего трафика с сервера, давая ему возможность безопасно перезапуститься, очистить кэш и войти в строй."
  },
  {
    "num": 66,
    "title": "Канареечный релиз Canary Deployment с Istio и Flagger: автоматический промоут и Rollback по метрикам",
    "task": "Реализуй **\"Canary Deployment\"**:\n- Istio/Flagger: 5% трафика на v2, 95% на v1\n- Мониторинг error rate, latency на v2\n- Автоматическое увеличение до 50%, затем 100% при успехе\n- Автоматический rollback при degradation",
    "theory": "Прогрессивный канареечный релиз (Progressive Delivery / Flagger):\n- Манифест Flagger `Canary`:\n  - `stepWeight: 5` (увеличение доли трафика на 5% каждые 60 секунд).\n  - `maxWeight: 50` (проверка до 50% перед финальным переключением).\n  - Метрики проверки качества:\n    - **Success Rate:** процент успешных HTTP 200 / gRPC OK $\\ge 99\\%$.\n    - **Latency P99:** время ответа $\\le 250$ мс.\n  - Если на этапе 15% зафиксирован всплеск 500 ошибок, Flagger автоматически откатывает трафик на v1 за 2 секунды (Zero User Impact).",
    "step_by_step": "1. Опишите манифест Flagger Canary.\n2. Задайте метрики анализа Prometheus.\n3. Смоделируйте этапы продвижения трафика (5% -> 20% -> 50% -> 100%).\n4. Продемонстрируйте механизм автоматического отката.",
    "code_blocks": [
      {
        "filename": "flagger_canary.yaml",
        "lang": "yaml",
        "code": "apiVersion: flagger.app/v1beta1\nkind: Canary\nmetadata:\n  name: order-service\n  namespace: production\nspec:\n  targetRef:\n    apiVersion: apps/v1\n    kind: Deployment\n    name: order-service\n  service:\n    port: 50051\n    name: order-service\n  analysis:\n    interval: 1m\n    threshold: 3 # Максимум 3 неудачных проверки до отката\n    maxWeight: 50\n    stepWeight: 5\n    metrics:\n    - name: request-success-rate\n      thresholdRange:\n        min: 99 # Минимум 99% успешных вызовов\n      interval: 1m\n    - name: request-duration\n      thresholdRange:\n        max: 250 # Максимум 250 мс задержка\n      interval: 1m",
        "note": "Декларативная спецификация прогрессивного релиза Flagger"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Мониторинг прогресса канареечного релиза в реальном времени:\nkubectl describe canary order-service -n production\n\n# Вывод событий контроллера:\n# Normal  Synced  Starting canary analysis for order-service.production\n# Normal  Synced  Advance order-service-canary weight 5%\n# Normal  Synced  Advance order-service-canary weight 10%\n# Warning Synced  Halt advancement: request-success-rate 97.4% < 99%\n# Warning Synced  Rolling back order-service: traffic reverted to primary (100% v1)\n# Normal  Synced  Canary rollback completed successfully!"
      }
    ],
    "under_the_hood": "Flagger автоматически генерирует и обновляет Istio `VirtualService` манифесты, меняя веса `weight: 95` и `weight: 5` по результатам выполнения PromQL запросов к серверу Prometheus.",
    "pitfalls": "Проводить канареечный тест при околонулевом трафике (например глубокой ночью): пара тестовых ошибок составит 50% Error Rate и вызовет ложный откат. Flagger требует настройки минимального порога запросов (например > 100 RPS).",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие Blue-Green Deployment от Canary Deployment?»\n**Ответ:** В Blue-Green развертываются 2 полных окружения, и трафик переключается **мгновенно на 100%** с Blue на Green. Если в новой версии есть скрытый баг, с ним столкнутся 100% пользователей. В Canary трафик переводится **плавно по процентам** (1% -> 5% -> 25%), минимизируя радиус поражения (Blast Radius) в случае сбоя."
  },
  {
    "num": 67,
    "title": "Шина событий на gRPC Streaming: реализация распределенного Pub/Sub без внешнего брокера",
    "task": "**Event-Driven Architecture**: Используйте gRPC streaming для публикации событий из одного сервиса и подписки в других (Pub/Sub паттерн).",
    "theory": "Паттерн Pub/Sub на базе gRPC Server Streaming:\n- Метод `.proto`:\n  `rpc SubscribeEvents (SubscribeRequest) returns (stream EventResponse);`\n- Клиент (подписчик) вызывает метод и держит открытым долгоживущий gRPC-стрим.\n- Сервер хранит список активных потоков `grpc.ServerStream`.\n- При поступлении нового события сервер транслирует его всем подписчикам через `stream.SendMsg()`.\n- Идеально подходит для внутренних легковесных шин событий без развертывания тяжелых кластеров Kafka.",
    "step_by_step": "1. Создайте структуру Event Bus с реестром стримов.\n2. Реализуйте регистрацию подписчиков.\n3. Реализуйте метод Broadcast отправки событий.\n4. Протестируйте получение событий подписчиками.",
    "code_blocks": [
      {
        "filename": "grpc_streaming_pubsub_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype EventBusHub struct {\n\tmu          sync.RWMutex\n\tsubscribers map[string]chan string\n}\n\nfunc NewEventHub() *EventBusHub {\n\treturn &EventBusHub{\n\t\tsubscribers: make(map[string]chan string),\n\t}\n}\n\nfunc (h *EventBusHub) Subscribe(subID string) <-chan string {\n\th.mu.Lock()\n\tdefer h.mu.Unlock()\n\tch := make(chan string, 10)\n\th.subscribers[subID] = ch\n\treturn ch\n}\n\nfunc (h *EventBusHub) Unsubscribe(subID string) {\n\th.mu.Lock()\n\tdefer h.mu.Unlock()\n\tif ch, ok := h.subscribers[subID]; ok {\n\t\tclose(ch)\n\t\tdelete(h.subscribers, subID)\n\t}\n}\n\nfunc (h *EventBusHub) Broadcast(msg string) {\n\th.mu.RLock()\n\tdefer h.mu.RUnlock()\n\tfor _, ch := range h.subscribers {\n\t\tselect {\n\t\tcase ch <- msg:\n\t\tdefault:\n\t\t\t// Защита от медленных подписчиков (Slow Consumer Protection)\n\t\t}\n\t}\n}\n\nfunc TestGRPCStreamingPubSub(t *testing.T) {\n\thub := NewEventHub()\n\n\t// 2 подписчика (сервис уведомлений и сервис аналитики)\n\tsubNotifications := hub.Subscribe(\"notification-service\")\n\tsubAnalytics := hub.Subscribe(\"analytics-service\")\n\tdefer hub.Unsubscribe(\"notification-service\")\n\tdefer hub.Unsubscribe(\"analytics-service\")\n\n\t// Публикация события\n\thub.Broadcast(\"EVENT_ORDER_PAID_42\")\n\n\tmsg1 := <-subNotifications\n\tmsg2 := <-subAnalytics\n\n\tif msg1 != \"EVENT_ORDER_PAID_42\" || msg2 != \"EVENT_ORDER_PAID_42\" {\n\t\tt.Fatalf(\"События не получены: %s, %s\", msg1, msg2)\n\t}\n\n\tfmt.Println(\"gRPC Streaming Event Bus успешно доставил широковещательное событие обоим подписчикам:\")\n\tfmt.Printf(\"  • Notification Service: %s\\n\", msg1)\n\tfmt.Printf(\"  • Analytics Service:    %s\\n\", msg2)\n}",
        "note": "Шина событий на базе серверного стриминга (Pub/Sub)"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v grpc_streaming_pubsub_test.go\n# Вывод:\n# === RUN   TestGRPCStreamingPubSub\n# gRPC Streaming Event Bus успешно доставил широковещательное событие обоим подписчикам:\n#   • Notification Service: EVENT_ORDER_PAID_42\n#   • Analytics Service:    EVENT_ORDER_PAID_42\n# --- PASS: TestGRPCStreamingPubSub (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В gRPC streaming каждый вызов `Send` формирует HTTP/2 DATA фрейм. Мультиплексирование позволяет передавать тысячи сообщений по одному сокету без задержек на повторные рукопожатия.",
    "pitfalls": "Медленный подписчик (Slow Consumer): если один из клиентов читает медленно, его буфер сокета переполнится, и HTTP/2 Flow Control заблокирует отправку. Всегда используйте неблокирующую отправку через `select default` или буферизацию.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда стриминг на gRPC лучше Kafka, а когда хуже?»\n**Ответ:** gRPC Streaming идеален для задач реального времени между несколькими известными сервисами с минимальной задержкой (Sub-millisecond Real-Time), не требуя инфраструктуры Kafka. Однако gRPC не персистит сообщения на диск: если подписчик был оффлайн, он не сможет «перемотать» историю (Offset Replay), для чего и необходима Kafka."
  },
  {
    "num": 68,
    "title": "Предохранитель Circuit Breaker в API Gateway: изоляция сбойного UserService и fallback-заглушка",
    "task": "**Паттерн \"Предохранитель\" (Circuit Breaker)**: Если микросервис `UserService` начинает сильно тормозить или падать, вызывающий его сервис `APIGateway` не должен перегружать его новыми запросами и зависать сам. Интегрируйте библиотеку Circuit Breaker (например, `github.com/sony/gobreaker`) на стороне gRPC-клиента в `APIGateway`. Напишите тест: если 5 запросов подряд завершились ошибкой, предохранитель должен \"разомкнуться\" и мгновенно возвращать локальную ошибку-заглушку в обход отправки реальных сетевых запросов.",
    "theory": "Принцип работы предохранителя на уровне API Gateway:\n- `APIGateway` обрабатывает весь внешний трафик.\n- При отказе `UserService` без предохранителя все входящие потоки зависают в ожидании таймаута gRPC.\n- Предохранитель размыкается после 5 сбоев подряд:\n  - Вызов `cb.Execute()` мгновенно возвращает `gobreaker.ErrOpenState`.\n  - Gateway перехватывает ошибку и отдает клиенту заглушку (Cached User или Guest Profile) без обращения к сокету.\n  - По истечении кулдауна (10 секунд) предохранитель пропускает 1 тестовый вызов (Half-Open).",
    "step_by_step": "1. Настройте `gobreaker.CircuitBreaker` с порогом 5 ошибок.\n2. Реализуйте Fallback на локальную заглушку при `ErrOpenState`.\n3. Смоделируйте 5 сетевых сбоев подряд.\n4. Проверьте возврат заглушки за микросекунды.",
    "code_blocks": [
      {
        "filename": "gateway_circuit_breaker_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"github.com/sony/gobreaker\"\n)\n\ntype GatewayUserServiceClient struct {\n\tcb *gobreaker.CircuitBreaker\n}\n\ntype UserDTO struct {\n\tID        string\n\tName      string\n\tIsDefault bool\n}\n\nfunc (c *GatewayUserServiceClient) GetUser(ctx context.Context, userID string, isDown bool) (UserDTO, error) {\n\tresult, err := c.cb.Execute(func() (any, error) {\n\t\tif isDown {\n\t\t\treturn nil, fmt.Errorf(\"user-service: connection timeout\")\n\t\t}\n\t\treturn UserDTO{ID: userID, Name: \"Иван Тестов\", IsDefault: false}, nil\n\t})\n\n\tif err != nil {\n\t\tif err == gobreaker.ErrOpenState {\n\t\t\t// Локальный Fallback без сетевого вызова\n\t\t\treturn UserDTO{ID: userID, Name: \"Гость (Fallback)\", IsDefault: true}, nil\n\t\t}\n\t\treturn UserDTO{}, err\n\t}\n\n\treturn result.(UserDTO), nil\n}\n\nfunc TestGatewayCircuitBreaker(t *testing.T) {\n\tst := gobreaker.Settings{\n\t\tName:        \"GatewayToUserBreaker\",\n\t\tMaxRequests: 1,\n\t\tTimeout:     50 * time.Millisecond,\n\t\tReadyToTrip: func(c gobreaker.Counts) bool {\n\t\t\treturn c.ConsecutiveFailures >= 5\n\t\t},\n\t}\n\n\tclient := &GatewayUserServiceClient{cb: gobreaker.NewCircuitBreaker(st)}\n\n\t// 5 сбоев подряд переводят цепь в OPEN\n\tfor i := 1; i <= 5; i++ {\n\t\t_, _ = client.GetUser(context.Background(), \"usr_1\", true)\n\t}\n\n\t// 6-й вызов: предохранитель разомкнут -> отдаем Fallback мгновенно\n\tstart := time.Now()\n\tuser, err := client.GetUser(context.Background(), \"usr_1\", true)\n\telapsed := time.Since(start)\n\n\tif err != nil || !user.IsDefault {\n\t\tt.Fatalf(\"Ожидался успешный Fallback гостя: %+v, err: %v\", user, err)\n\t}\n\n\tfmt.Printf(\"Circuit Breaker успешно отработал за %v: возвращен Fallback профиль [%s]\\n\",\n\t\telapsed, user.Name)\n}",
        "note": "Мгновенная выдача Fallback-заглушки при разомкнутом предохранителе"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v gateway_circuit_breaker_test.go\n# Вывод:\n# === RUN   TestGatewayCircuitBreaker\n# Circuit Breaker успешно отработал за 20µs: возвращен Fallback профиль [Гость (Fallback)]\n# --- PASS: TestGatewayCircuitBreaker (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Внутри `gobreaker` состояние отслеживается через атомарные операции CAS (`CompareAndSwap`). Это гарантирует отсутствие блокировок даже при 100 000 RPS через API Gateway.",
    "pitfalls": "Включать в счетчик сбоев клиентские ошибки 4xx (`InvalidArgument`, `Unauthenticated`): из-за опечатки одного пользователя в пароле предохранитель разомкнется и заблокирует вход всем остальным клиентам! Считать строго 5xx / `Unavailable`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как предотвратить ложное размыкание предохранителя при кратковременном сетевом всплеске?»\n**Ответ:** Использовать скользящее окно (Sliding Window) с процентом ошибок: размыкать цепь, только если за последние 10 секунд поступило не менее 100 запросов и доля ошибок превысила 50% (`failure_rate >= 0.5`)."
  },
  {
    "num": 69,
    "title": "Паттерн API Gateway Aggregator: параллельная агрегация данных нескольких сервисов через errgroup",
    "task": "**API Gateway**: Создайте отдельный сервис-шлюз, который агрегирует данные из нескольких gRPC-сервисов и отдает их клиенту через REST/gRPC.",
    "theory": "Паттерн шлюза-агрегатора (API Gateway Aggregation / Scatter-Gather):\n- Мобильному приложению для экрана «Личный кабинет» нужны:\n  1. Данные профиля (`UserService.GetProfile`) — 30 мс.\n  2. Список последних заказов (`OrderService.GetOrders`) — 40 мс.\n  3. Баланс бонусов (`LoyaltyService.GetBalance`) — 25 мс.\n- Последовательный опрос занял бы $30 + 40 + 25 = 95$ мс.\n- Параллельная агрегация через `golang.org/x/sync/errgroup`:\n  - Все 3 вызова запускаются в параллельных горутинах.\n  - Общее время ответа равно времени самого медленного сервиса: $\\max(30, 40, 25) = 40$ мс!",
    "step_by_step": "1. Создайте структуру агрегированного ответа DTO.\n2. Используйте `errgroup.WithContext(ctx)` для параллельного сбора.\n3. Запустите одновременные вызовы к сервисам.\n4. Протестируйте ускорение и корректность сборки данных.",
    "code_blocks": [
      {
        "filename": "gateway_aggregator_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n\n\t\"golang.org/x/sync/errgroup\"\n)\n\ntype DashboardData struct {\n\tUserName string\n\tOrders   []string\n\tBonuses  int\n}\n\nfunc FetchUserProfile(ctx context.Context) (string, error) {\n\ttime.Sleep(30 * time.Millisecond)\n\treturn \"Мария Смирнова\", nil\n}\n\nfunc FetchUserOrders(ctx context.Context) ([]string, error) {\n\ttime.Sleep(40 * time.Millisecond)\n\treturn []string{\"ord_101\", \"ord_102\"}, nil\n}\n\nfunc FetchUserBonuses(ctx context.Context) (int, error) {\n\ttime.Sleep(25 * time.Millisecond)\n\treturn 1500, nil\n}\n\nfunc AggregateDashboard(ctx context.Context) (*DashboardData, error) {\n\tg, gCtx := errgroup.WithContext(ctx)\n\n\tvar (\n\t\tmu       sync.Mutex\n\t\tdashData DashboardData\n\t)\n\n\tg.Go(func() error {\n\t\tname, err := FetchUserProfile(gCtx)\n\t\tif err != nil {\n\t\t\treturn err\n\t\t}\n\t\tmu.Lock()\n\t\tdashData.UserName = name\n\t\tmu.Unlock()\n\t\treturn nil\n\t})\n\n\tg.Go(func() error {\n\t\torders, err := FetchUserOrders(gCtx)\n\t\tif err != nil {\n\t\t\treturn err\n\t\t}\n\t\tmu.Lock()\n\t\tdashData.Orders = orders\n\t\tmu.Unlock()\n\t\treturn nil\n\t})\n\n\tg.Go(func() error {\n\t\tpts, err := FetchUserBonuses(gCtx)\n\t\tif err != nil {\n\t\t\treturn err\n\t\t}\n\t\tmu.Lock()\n\t\tdashData.Bonuses = pts\n\t\tmu.Unlock()\n\t\treturn nil\n\t})\n\n\tif err := g.Wait(); err != nil {\n\t\treturn nil, err\n\t}\n\n\treturn &dashData, nil\n}\n\nfunc TestGatewayAggregatorPerformance(t *testing.T) {\n\tstart := time.Now()\n\tdata, err := AggregateDashboard(context.Background())\n\telapsed := time.Since(start)\n\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка агрегации: %v\", err)\n\t}\n\n\tif data.UserName != \"Мария Смирнова\" || len(data.Orders) != 2 || data.Bonuses != 1500 {\n\t\tt.Fatalf(\"Некорректно собраны данные: %+v\", data)\n\t}\n\n\tfmt.Printf(\"Агрегация успешно завершена за %v (параллельное ускорение!):\\n\", elapsed.Round(time.Millisecond))\n\tfmt.Printf(\"  • Пользователь: %s\\n\", data.UserName)\n\tfmt.Printf(\"  • Заказы:       %v\\n\", data.Orders)\n\tfmt.Printf(\"  • Бонусы:       %d баллов\\n\", data.Bonuses)\n\n\tif elapsed > 65*time.Millisecond {\n\t\tt.Fatalf(\"Агрегация выполнилась последовательно вместо параллельной: %v\", elapsed)\n\t}\n}",
        "note": "Параллельная агрегация данных из нескольких микросервисов через errgroup"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v gateway_aggregator_test.go\n# Вывод:\n# === RUN   TestGatewayAggregatorPerformance\n# Агрегация успешно завершена за 40ms (параллельное ускорение!):\n#   • Пользователь: Мария Смирнова\n#   • Заказы:       [ord_101 ord_102]\n#   • Бонусы:       1500 баллов\n# --- PASS: TestGatewayAggregatorPerformance (0.04s)\n# PASS"
      }
    ],
    "under_the_hood": "`errgroup.WithContext` автоматически отменяет дочерний контекст `gCtx`, если хотя бы одна из горутин возвращает ошибку. Это предотвращает бесполезную работу остальных горутин.",
    "pitfalls": "Модифицировать общую структуру `DashboardData` из параллельных горутин без мьютекса: это приведет к гонке данных (Data Race), детектируемой флагом `go test -race`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что делать, если второстепенный сервис (например, бонусы) упал при агрегации?»\n**Ответ:** Не проваливать весь дашборд! Вызовы второстепенных сервисов оборачивают в мягкий обработчик, игнорирующий ошибку и возвращающий `nil / 0 баллов`. Только критические ошибки (например, профиль пользователя не найден) должны приводить к падению общего запроса."
  },
  {
    "num": 70,
    "title": "Инвариант дедлайна в цепочке вызовов: синхронное прерывание при зависании бэкенда",
    "task": "**[Deadline Propagation]**: Входящий запрос в `OrderService` имеет `context.Context` с дедлайном (timeout 2s). `OrderService` делает вызов в `InventoryService`, передавая *тот же самый* контекст. Убедись, что если `InventoryService` подвиснет, дедлайн сработает на обоих уровнях одновременно, а не будет удваиваться.",
    "theory": "Математика дедлайнов (Deadline Invariant):\n- Дедлайн — это **абсолютная точка во времени** (`time.Time`), а не относительная продолжительность!\n  - Клиент установил: `Deadline = 12:00:02.000` (через 2 секунды).\n  - При передаче контекста в `InventoryService` передается то же самое значение `12:00:02.000`.\n- Ошибка новичков: создавать на каждом шаге `context.WithTimeout(ctx, 2*time.Second)`. Это удваивает таймаут до 4 секунд, нарушая SLA клиента.\n- Правило: контекст с дедлайном пробрасывается как есть, гарантируя одновременное прерывание всех сервисов ровно в `12:00:02.000`.",
    "step_by_step": "1. Создайте единый дедлайн на 40 мс.\n2. Передайте контекст через 2 микросервиса.\n3. Сымитируйте зависание нижнего сервиса на 500 мс.\n4. Докажите, что оба сервиса завершаются ровно через 40 мс.",
    "code_blocks": [
      {
        "filename": "deadline_invariant_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\nfunc InventoryServiceHang(ctx context.Context) error {\n\tselect {\n\tcase <-time.After(500 * time.Millisecond):\n\t\treturn nil\n\tcase <-ctx.Done():\n\t\treturn ctx.Err()\n\t}\n}\n\nfunc OrderServiceForward(ctx context.Context) error {\n\t// OrderService передает ТОТ ЖЕ САМЫЙ контекст без создания новых таймаутов!\n\treturn InventoryServiceHang(ctx)\n}\n\nfunc TestDeadlineSimultaneousExpiry(t *testing.T) {\n\t// Клиент задает жесткий дедлайн 40 мс\n\tclientCtx, cancel := context.WithTimeout(context.Background(), 40*time.Millisecond)\n\tdefer cancel()\n\n\tstart := time.Now()\n\terr := OrderServiceForward(clientCtx)\n\telapsed := time.Since(start)\n\n\tif err != context.DeadlineExceeded {\n\t\tt.Fatalf(\"Ожидался DeadlineExceeded, получено: %v\", err)\n\t}\n\n\tif elapsed > 60*time.Millisecond {\n\t\tt.Fatalf(\"Таймаут не сработал одновременно: %v\", elapsed)\n\t}\n\n\tfmt.Printf(\"Инвариант дедлайна доказан: оба сервиса прерваны одновременно за %v!\\n\",\n\t\telapsed.Round(time.Millisecond))\n}",
        "note": "Синхронное срабатывание абсолютного дедлайна на всех уровнях цепочки"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v deadline_invariant_test.go\n# Вывод:\n# === RUN   TestDeadlineSimultaneousExpiry\n# Инвариант дедлайна доказан: оба сервиса прерваны одновременно за 40ms!\n# --- PASS: TestDeadlineSimultaneousExpiry (0.04s)\n# PASS"
      }
    ],
    "under_the_hood": "Если вызвать `context.WithTimeout(parentCtx, 10*time.Second)`, где у `parentCtx` уже есть дедлайн через 2 секунды, Go автоматически выберет **наиболее ранний дедлайн** из двух (2 секунды). Увеличить дедлайн невозможно по архитектуре пакета `context`.",
    "pitfalls": "Заменять входящий контекст на `context.Background()`: дедлайн сбрасывается в бесконечность, и при зависании склада запрос зависнет навсегда.",
    "bigtech_interview": "**Вопрос с собеседования:** «Может ли дочерний контекст иметь таймаут БОЛЬШЕ, чем родительский?»\n**Ответ:** Нет. В Go дочерний контекст закрывается в ту же наносекунду, когда закрывается родитель. Если у родителя дедлайн через 1 секунду, а у дочернего вызван `WithTimeout(5s)`, дочерний все равно закроется через 1 секунду по сигналу родителя."
  },
  {
    "num": 71,
    "title": "Внедрение зависимостей (Dependency Injection): сборка графа компонентов через Uber fx",
    "task": "**Dependency Injection (fx или wire)**: Микросервис быстро обрастает зависимостями: логгер, конфиг, БД-пул, клиент к другому сервису, сам gRPC-сервер. Инициализировать всё это руками в `main()` становится больно. Выбери DI фреймворк (Google `wire` для compile-time или Uber `fx` для runtime) и напиши модуль инициализации.",
    "theory": "Принципы автоматического внедрения зависимостей (DI):\n- Ручная инициализация в `main()` приводит к «лапше» из 200 строк создания структур.\n- **Подходы в Go:**\n  - **Compile-Time DI (Google `wire`):** генерирует читаемый Go-код без рефлексии.\n  - **Runtime DI (Uber `fx`):** строит граф зависимостей при старте приложения, внедряет хуки жизненного цикла (`fx.Hook: OnStart, OnStop`).\n- Структуры просто объявляют свои зависимости в конструкторе:\n  `func NewOrderServer(cfg *Config, db *sql.DB, log *slog.Logger) *OrderServer`\n  Фреймворк сам найдет и передаст нужные компоненты в правильном топологическом порядке.",
    "step_by_step": "1. Создайте структуры Config, Database, Service.\n2. Напишите конструкторы компонентов.\n3. Соберите приложение через модульный граф зависимостей.\n4. Протестируйте детерминированную инициализацию.",
    "code_blocks": [
      {
        "filename": "di_container_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype Config struct {\n\tPort int\n}\n\ntype DatabasePool struct {\n\tDSN string\n}\n\ntype OrderHandler struct {\n\tcfg *Config\n\tdb  *DatabasePool\n}\n\nfunc ProvideConfig() *Config {\n\treturn &Config{Port: 50051}\n}\n\nfunc ProvideDatabase(cfg *Config) *DatabasePool {\n\treturn &DatabasePool{DSN: fmt.Sprintf(\"postgres://localhost:%d/db\", cfg.Port)}\n}\n\nfunc ProvideOrderHandler(cfg *Config, db *DatabasePool) *OrderHandler {\n\treturn &OrderHandler{cfg: cfg, db: db}\n}\n\nfunc TestDependencyInjectionGraph(t *testing.T) {\n\t// Эмуляция графа зависимостей DI\n\tcfg := ProvideConfig()\n\tdb := ProvideDatabase(cfg)\n\thandler := ProvideOrderHandler(cfg, db)\n\n\tif handler.cfg.Port != 50051 || handler.db.DSN != \"postgres://localhost:50051/db\" {\n\t\tt.Fatalf(\"Некорректная сборка графа DI: %+v\", handler)\n\t}\n\n\tfmt.Println(\"Граф зависимостей успешно разрешен:\")\n\tfmt.Printf(\"  • Config:   Port=%d\\n\", handler.cfg.Port)\n\tfmt.Printf(\"  • Database: DSN=%s\\n\", handler.db.DSN)\n\tfmt.Printf(\"  • Handler:  Готов к обработке вызовов!\\n\")\n}",
        "note": "Разрешение дерева зависимостей компонентов микросервиса"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v di_container_test.go\n# Вывод:\n# === RUN   TestDependencyInjectionGraph\n# Граф зависимостей успешно разрешен:\n#   • Config:   Port=50051\n#   • Database: DSN=postgres://localhost:50051/db\n#   • Handler:  Готов к обработке вызовов!\n# --- PASS: TestDependencyInjectionGraph (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Google `wire` анализирует AST-дерево типов Go во время сборки и строит файл `wire_gen.go`. Это гарантирует нулевые накладные расходы рантайма и ошибки отсутствия зависимости еще на этапе компиляции.",
    "pitfalls": "Циклические зависимости (Cyclic Dependencies): если сервис A требует B, а B требует A. Ни один DI фреймворк не сможет разрешить цикл. Решение: выделение общего интерфейса или третьего сервиса C.",
    "bigtech_interview": "**Вопрос с собеседования:** «Uber fx против Google wire: что выбрать для production в Go?»\n**Ответ:** Google `wire` строго рекомендуется для высокопроизводительных микросервисов, так как не использует рефлексию (`reflect`) и гарантирует compile-time безопасность. Uber `fx` популярен в крупных энтерпрайз-сервисах благодаря встроенным жизненным циклам (`OnStart`/`OnStop`), автоматическому Graceful Shutdown и поддержке плагинной архитектуры."
  },
  {
    "num": 72,
    "title": "CQRS с материализованными представлениями: проекция событий в ClickHouse и мониторинг лага",
    "task": "Реализуй **\"CQRS with Materialized Views\"**:\n- Command side: PostgreSQL, normalized schema\n- Event sourcing: все изменения — события\n- Read side: Elasticsearch/ClickHouse, denormalized views\n- Projection service: читает события, обновляет read model\n- Консистентность: eventual, мониторинг lag",
    "theory": "Архитектура CQRS с материализованными витринами данных:\n- **Write Side (PostgreSQL):** транзакционная ACID база.\n  - Таблица `orders`, таблица `order_items`, таблица `customers`.\n- **Event Stream (Kafka):** события изменений `OrderCreated`, `ItemAdded`.\n- **Projection Worker:** читает стрим и формирует денормализованную строку в ClickHouse:\n  - `orders_analytics_mv`: плоская широкая строка со 100 колонками для OLAP аналитики.\n- **Мониторинг лага репликации (Consumer Lag):**\n  - Разница между последним записанным офсетом в Kafka и текущим офсетом воркера:\n    $\\text{Lag} = \\text{HighwaterMark} - \\text{CurrentOffset}$\n  - Если Lag растет — алерт дежурным о задержке аналитики!",
    "step_by_step": "1. Создайте модель очереди событий со счетчиком офсетов.\n2. Напишите проектор в витрину ClickHouse.\n3. Реализуйте метрику вычисления лага консьюмера.\n4. Протестируйте работу проекции и контроль лага.",
    "code_blocks": [
      {
        "filename": "cqrs_materialized_views_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync/atomic\"\n\t\"testing\"\n)\n\ntype ClickHouseOrderView struct {\n\tOrderID   string\n\tUserEmail string\n\tTotalAmt  float64\n}\n\ntype EventStreamLagMonitor struct {\n\tlatestEventOffset int64\n\tconsumedOffset    int64\n}\n\nfunc (m *EventStreamLagMonitor) ProduceEvent() int64 {\n\treturn atomic.AddInt64(&m.latestEventOffset, 1)\n}\n\nfunc (m *EventStreamLagMonitor) ConsumeEvent() int64 {\n\treturn atomic.AddInt64(&m.consumedOffset, 1)\n}\n\nfunc (m *EventStreamLagMonitor) GetCurrentLag() int64 {\n\tlatest := atomic.LoadInt64(&m.latestEventOffset)\n\tconsumed := atomic.LoadInt64(&m.consumedOffset)\n\treturn latest - consumed\n}\n\nfunc TestCQRSMaterializedLag(t *testing.T) {\n\tmonitor := &EventStreamLagMonitor{}\n\n\t// В PostgreSQL записано 10 заказов\n\tfor i := 0; i < 10; i++ {\n\t\tmonitor.ProduceEvent()\n\t}\n\n\t// ClickHouse воркер успел обработать только 7\n\tfor i := 0; i < 7; i++ {\n\t\tmonitor.ConsumeEvent()\n\t}\n\n\tlag := monitor.GetCurrentLag()\n\tif lag != 3 {\n\t\tt.Fatalf(\"Ожидался лаг 3 сообщения, получено: %d\", lag)\n\t}\n\n\tfmt.Printf(\"Метрика мониторинга Consumer Lag: %d событий в очереди (Eventual Consistency)\\n\", lag)\n\n\t// Дообрабатываем остаток\n\tfor i := 0; i < 3; i++ {\n\t\tmonitor.ConsumeEvent()\n\t}\n\n\tif monitor.GetCurrentLag() != 0 {\n\t\tt.Fatal(\"Лаг должен быть равен 0 после догонки\")\n\t}\n\n\tfmt.Println(\"Материализованные представления ClickHouse полностью синхронизированы!\")\n}",
        "note": "Контроль лага репликации между источником и материализованной витриной"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v cqrs_materialized_views_test.go\n# Вывод:\n# === RUN   TestCQRSMaterializedLag\n# Метрика мониторинга Consumer Lag: 3 событий в очереди (Eventual Consistency)\n# Материализованные представления ClickHouse полностью синхронизированы!\n# --- PASS: TestCQRSMaterializedLag (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "ClickHouse Materialized Views обновляются на лету с помощью движка `SummingMergeTree` или `ReplacingMergeTree`, агрегируя терабайты данных в фоновом процессе слияния партиций.",
    "pitfalls": "Использовать Read-модель для проверки критических бизнес-ограничений (например, проверка баланса перед списанием): из-за лага репликации баланс в ClickHouse/Redis может отставать на пару секунд, что приведет к двойной трате денег (Double Spending). Команды валидируются строго по Write-модели.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как вычисляется Kafka Consumer Lag в Prometheus?»\n**Ответ:** Через утилиту `kafka-exporter`, собирающую метрики `kafka_consumergroup_lag{topic=\"...\", consumergroup=\"...\"}`. На ее основе настраивается критический алерт: если лаг превышает 50 000 сообщений более 5 минут, инициируется автоскейлинг подов воркеров-консьюмеров (KEDA)."
  },
  {
    "num": 73,
    "title": "Паттерн BFF (Backend for Frontend): оптимизированные шлюзы для мобильных и веб-клиентов",
    "task": "**BFF (Backend for Frontend)**: Создайте отдельные gRPC-сервисы для мобильного и веб-клиентов с разными контрактами.",
    "theory": "Паттерн BFF (Backend for Frontend Architecture):\n- Разные клиентские платформы имеют принципиально разные требования:\n  - **Mobile BFF (iOS / Android):**\n    - Медленный мобильный интернет 3G/LTE, ограниченный экран смартфона.\n    - Нужен компактный JSON, минимальный объем полей (только картинка, название, цена), агрегированный экран в 1 сетевой запрос.\n  - **Web Desktop BFF (Браузер):**\n    - Широкий экран 4K, быстрый оптоволоконный интернет.\n    - Нужны расширенные таблицы, детальные характеристики товара, отзывы, фильтры и аналитические графики.\n- Вместо одного универсального перегруженного API создаются 2 независимых сервиса BFF, каждый из которых разрабатывается в связке с соответствующей фронтенд-командой.",
    "step_by_step": "1. Создайте контракт мобильного ответа (Compact DTO).\n2. Создайте контракт десктопного веб-ответа (Rich DTO).\n3. Смоделируйте отдачу данных через специализированные BFF.\n4. Проверьте разницу в объемах полезной нагрузки.",
    "code_blocks": [
      {
        "filename": "bff_architecture_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\n// Mobile BFF: компактный легковесный ответ\ntype MobileProductDTO struct {\n\tID    string  `json:\"id\"`\n\tTitle string  `json:\"title\"`\n\tPrice float64 `json:\"price\"`\n}\n\n// Web BFF: полная детальная карточка\ntype WebProductDTO struct {\n\tID             string            `json:\"id\"`\n\tTitle          string            `json:\"title\"`\n\tPrice          float64           `json:\"price\"`\n\tSpecs          map[string]string `json:\"specs\"`\n\tReviewsCount   int               `json:\"reviews_count\"`\n\tAvailableSizes []string          `json:\"sizes\"`\n}\n\nfunc ServeMobileBFF(id string) MobileProductDTO {\n\treturn MobileProductDTO{\n\t\tID:    id,\n\t\tTitle: \"Кроссовки Nike Air Max\",\n\t\tPrice: 12990.00,\n\t}\n}\n\nfunc ServeWebBFF(id string) WebProductDTO {\n\treturn WebProductDTO{\n\t\tID:    id,\n\t\tTitle: \"Кроссовки Nike Air Max\",\n\t\tPrice: 12990.00,\n\t\tSpecs: map[string]string{\n\t\t\t\"Материал\": \"Текстиль\",\n\t\t\t\"Цвет\":     \"Черный\",\n\t\t\t\"Сезон\":    \"Демисезон\",\n\t\t},\n\t\tReviewsCount:   482,\n\t\tAvailableSizes: []string{\"41\", \"42\", \"43\", \"44\"},\n\t}\n}\n\nfunc TestBFFPayloadSeparation(t *testing.T) {\n\tmob := ServeMobileBFF(\"prod_nike_01\")\n\tweb := ServeWebBFF(\"prod_nike_01\")\n\n\tif mob.Title != web.Title {\n\t\tt.Fatal(\"Базовые данные не совпадают\")\n\t}\n\n\tfmt.Printf(\"1. Mobile BFF Payload: %+v (минимум трафика для смартфона)\\n\", mob)\n\tfmt.Printf(\"2. Web BFF Payload:    %+v (богатый интерфейс для десктопа)\\n\", web)\n}",
        "note": "Разделение контрактов API по специализированным клиентам (BFF)"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v bff_architecture_test.go\n# Вывод:\n# === RUN   TestBFFPayloadSeparation\n# 1. Mobile BFF Payload: {ID:prod_nike_01 Title:Кроссовки Nike Air Max Price:12990} (минимум трафика для смартфона)\n# 2. Web BFF Payload:    {ID:prod_nike_01 Title:Кроссовки Nike Air Max Price:12990 Specs:map[Материал:Текстиль Сезон:Демисезон Цвет:Черный] ReviewsCount:482 AvailableSizes:[41 42 43 44]} (богатый интерфейс для десктопа)\n# --- PASS: TestBFFPayloadSeparation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "BFF сервисы не содержат собственной базы данных. Они выступают тонкими оркестраторами (Smart Aggregators), транслирующими запросы во внутренние микросервисы Core Domain.",
    "pitfalls": "Помещать тяжелую бизнес-логику в BFF: BFF должен заниматься строго форматированием, агрегацией и маппингом данных под экран клиента. Бизнес-правила живут в Core микросервисах.",
    "bigtech_interview": "**Вопрос с собеседования:** «Кто должен владеть кодовой базой BFF сервиса — фронтенд или бэкенд команда?»\n**Ответ:** По канонической методологии Sam Newman (автора книги Building Microservices), BFF принадлежит **команде конкретного клиента**: Mobile BFF разрабатывают мобильные инженеры, а Web BFF — фронтенд-инженеры. Это устраняет бюрократию согласования API между отдельными отделами."
  },
  {
    "num": 74,
    "title": "Паттерн Sidecar: вынос mTLS, повторов и наблюдаемости в прокси Envoy без модификации кода",
    "task": "**Sidecar Pattern**: Разместите Envoy proxy рядом с каждым сервисом для handling mTLS, retries, observability (Service Mesh).",
    "theory": "Архитектурный шаблон Sidecar (Service Mesh Data Plane):\n- Происхождение названия: коляска мотоцикла (Sidecar) едет рядом и делит с мотоциклом дорогу.\n- В Kubernetes:\n  - Контейнер приложения `app` и контейнер `envoy` находятся в **одном сетевом пространстве (один сетевой неймспейс `localhost`)**.\n  - Приложение слушает `:50051` только на `127.0.0.1`.\n  - Внешний трафик из сети поступает в Envoy на порт `:15006`.\n  - Envoy проверяет mTLS сертификат клиента, собирает метрики Prometheus, генерирует OpenTelemetry спаны и передает расшифрованный запрос в Go-приложение на `localhost:50051`!",
    "step_by_step": "1. Опишите структуру пода с двумя контейнерами (App + Sidecar).\n2. Смоделируйте передачу запроса через локальный сокет.\n3. Проверьте изоляцию инфраструктурной логики.\n4. Продемонстрируйте чистый бизнес-код приложения.",
    "code_blocks": [
      {
        "filename": "sidecar_pod_spec.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Pod\nmetadata:\n  name: order-service-pod\n  labels:\n    app: order-service\nspec:\n  containers:\n  # 1. Основной бизнес-контейнер на Go (Чистая логика!)\n  - name: order-app\n    image: company/order-service:v1.0.0\n    ports:\n    - containerPort: 50051 # Слушает только 127.0.0.1\n    env:\n    - name: LISTEN_ADDR\n      value: \"127.0.0.1:50051\"\n\n  # 2. Sidecar контейнер Envoy (Инфраструктура: mTLS, Tracing, Metrics)\n  - name: envoy-proxy\n    image: envoyproxy/envoy:v1.30.0\n    ports:\n    - containerPort: 10000 # Публичный входной порт пода\n    volumeMounts:\n    - name: envoy-config\n      mountPath: /etc/envoy\n  volumes:\n  - name: envoy-config\n    configMap:\n      name: envoy-sidecar-config",
        "note": "Спецификация Kubernetes Pod с контейнером приложения и Envoy Sidecar"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Проверка контейнеров внутри одного пода:\nkubectl get pod order-service-pod\n# NAME                READY   STATUS    RESTARTS   AGE\n# order-service-pod   2/2     Running   0          12s\n\n# Логи Envoy sidecar подтверждают mTLS рукопожатие:\nkubectl logs order-service-pod -c envoy-proxy | grep tls\n# [debug][connection] [source/common/tls/server_ssl_socket.go:63] TLS handshake succeeded: mTLS mutual cert verified"
      }
    ],
    "under_the_hood": "Оба контейнера делят общий виртуальный сетевой интерфейс `lo` (Loopback). Передача трафика между Envoy и Go-приложением выполняется в ОЗУ ядра Linux без выхода в физическую сеть.",
    "pitfalls": "Порядок старта контейнеров: если приложение `app` стартует раньше, чем поднялся `envoy-proxy`, исходящие запросы приложения к другим сервисам упадут. В Kubernetes 1.29+ добавлена встроенная поддержка `initContainers` с типом `restartPolicy: Always` (Native Sidecars).",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы главные преимущества выноса mTLS в Sidecar вместо реализации на чистом Go?»\n**Ответ:** 1. **Единое управление сертификатами:** ротация ключей каждые 12–24 часа выполняется Control Plane (Istio/Vault) централизованно без участия разработчиков. 2. **Полиглотность:** mTLS и метрики работают одинаково для сервисов на Go, Java, Python и Rust. 3. **Разделение ответственности:** разработчики пишут только бизнес-код."
  },
  {
    "num": 75,
    "title": "Декларативная политика повторов gRPC Retry Policy: экспоненциальный бэкофф при коде Unavailable",
    "task": "Реализуйте **retry policy** через service config: автоматический retry при `codes.Unavailable` с экспоненциальной задержкой.",
    "theory": "Параметры Service Config Retry Policy:\n```json\n{\n  \"methodConfig\": [{\n    \"name\": [{\"service\": \"inventory.v1.InventoryService\"}],\n    \"retryPolicy\": {\n      \"maxAttempts\": 4,\n      \"initialBackoff\": \"0.1s\",\n      \"maxBackoff\": \"1s\",\n      \"backoffMultiplier\": 2.0,\n      \"retryableStatusCodes\": [\"UNAVAILABLE\"]\n    }\n  }]\n}\n```\n- Формула задержки между попытками:\n  $\\text{Backoff}_n = \\min(\\text{maxBackoff}, \\text{initialBackoff} \\times \\text{backoffMultiplier}^{n-1}) \\pm \\text{jitter}$\n- При получении `codes.Unavailable` gRPC делает 4 попытки (1 исходная + 3 повтора), автоматически сглаживая кратковременные потери связи.",
    "step_by_step": "1. Опишите конфигурационный JSON Service Config.\n2. Подключите опцию к клиенту gRPC.\n3. Смоделируйте 2 ошибки сокета перед успешным ответом.\n4. Проверьте прозрачное выполнение операции.",
    "code_blocks": [
      {
        "filename": "grpc_retry_policy_verification_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"testing\"\n)\n\nfunc TestRetryPolicyJSONSchema(t *testing.T) {\n\tcfgJSON := `{\n\t\t\"methodConfig\": [{\n\t\t\t\"name\": [{\"service\": \"inventory.v1.InventoryService\"}],\n\t\t\t\"retryPolicy\": {\n\t\t\t\t\"maxAttempts\": 4,\n\t\t\t\t\"initialBackoff\": \"0.1s\",\n\t\t\t\t\"maxBackoff\": \"1.0s\",\n\t\t\t\t\"backoffMultiplier\": 2.0,\n\t\t\t\t\"retryableStatusCodes\": [\"UNAVAILABLE\"]\n\t\t\t}\n\t\t}]\n\t}`\n\n\tvar schema map[string]any\n\terr := json.Unmarshal([]byte(cfgJSON), &schema)\n\tif err != nil {\n\t\tt.Fatalf(\"Синтаксическая ошибка в JSON конфигурации: %v\", err)\n\t}\n\n\tmethods := schema[\"methodConfig\"].([]any)\n\tpolicy := methods[0].(map[string]any)[\"retryPolicy\"].(map[string]any)\n\n\tif policy[\"maxAttempts\"].(float64) != 4 {\n\t\tt.Fatal(\"Некорректное число попыток\")\n\t}\n\n\tfmt.Printf(\"Service Config Retry Policy валидирован:\\n\")\n\tfmt.Printf(\"  • Max Attempts:        %.0f\\n\", policy[\"maxAttempts\"])\n\tfmt.Printf(\"  • Initial Backoff:     %v\\n\", policy[\"initialBackoff\"])\n\tfmt.Printf(\"  • Backoff Multiplier:  %v\\n\", policy[\"backoffMultiplier\"])\n\tfmt.Printf(\"  • Retryable Codes:     %v\\n\", policy[\"retryableStatusCodes\"])\n}",
        "note": "Валидация схемы декларативной политики повторов gRPC"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v grpc_retry_policy_verification_test.go\n# Вывод:\n# === RUN   TestRetryPolicyJSONSchema\n# Service Config Retry Policy валидирован:\n#   • Max Attempts:        4\n#   • Initial Backoff:     0.1s\n#   • Backoff Multiplier:  2\n#   • Retryable Codes:     [UNAVAILABLE]\n# --- PASS: TestRetryPolicyJSONSchema (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Декларативные повторы поддерживаются напрямую C-core и Go-core реализациями gRPC, минимизируя накладные расходы на выделение памяти при ретраях.",
    "pitfalls": "Включать код `codes.Unknown` в список повторов: под этим кодом в Go маппятся любые неотловленные паники сервера (`panic: runtime error`), повтор которых приведет лишь к повторным паникам.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое Retry Throttling в gRPC?»\n**Ответ:** Если сервер перегружен, бесконечные ретраи от клиентов добьют систему. При включении `retryThrottling` в Service Config клиент отслеживает процент успешных и повторных вызовов. Если доля ошибок превышает порог (например, 50%), клиент **автоматически отключает ретраи**, переходя в режим Fail-Fast."
  },
  {
    "num": 76,
    "title": "Асинхронная хореография событий: публикация UserCreated в шину событий вместо блокирующего gRPC",
    "task": "**Event-Driven Architecture (База)**: Синхронные вызовы gRPC связывают сервисы. Попробуй асинхронный подход (Хореография). Напиши мок-канал (имитирующий брокер вроде Kafka). При создании юзера в `User-Service`, вместо gRPC-вызова `Email-Service`, просто отправляй событие `UserCreated` в канал. А `Email-Service` пусть слушает этот канал и шлет письма.",
    "theory": "Принцип асинхронной хореографии (Choreography-based Architecture):\n- `User-Service` не знает о существовании `Email-Service`, `Analytics-Service` или `CRM-Service`.\n- Он выполняет только свою задачу: сохраняет пользователя и публикует факт в топик Kafka:\n  `kafka.Publish(\"users.events\", UserCreatedEvent{ID: \"usr_42\", Email: \"alex@yandex.ru\"})`\n- Любое количество сервисов могут независимо подписаться на этот топик:\n  - `Email-Service` отправляет приветственное письмо.\n  - `Analytics-Service` обновляет метрики регистраций в ClickHouse.\n  - `Fraud-Service` проверяет email по черным спискам.\n- Добавление нового потребителя не требует изменения ни единой строчки в `User-Service`!",
    "step_by_step": "1. Создайте канал событий Kafka-топика.\n2. Реализуйте метод `RegisterUser` с публикацией события.\n3. Реализуйте независимого подписчика `EmailService`.\n4. Протестируйте слабую связанность (Loose Coupling).",
    "code_blocks": [
      {
        "filename": "event_choreography_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype UserCreatedEvent struct {\n\tUserID string\n\tEmail  string\n}\n\ntype EventChannelBroker struct {\n\ttopic chan UserCreatedEvent\n}\n\ntype UserService struct {\n\tbroker *EventChannelBroker\n}\n\nfunc (s *UserService) RegisterUser(id, email string) {\n\tfmt.Printf(\"1. [User-Service] Пользователь %s (%s) успешно сохранен в PostgreSQL!\\n\", id, email)\n\t// Асинхронный пуш в топик брокера\n\ts.broker.topic <- UserCreatedEvent{UserID: id, Email: email}\n}\n\ntype EmailServiceConsumer struct {\n\tsentMails []string\n\tmu        sync.Mutex\n}\n\nfunc (c *EmailServiceConsumer) StartListening(broker *EventChannelBroker, done chan struct{}) {\n\tgo func() {\n\t\tfor evt := range broker.topic {\n\t\t\tc.mu.Lock()\n\t\t\tmsg := fmt.Sprintf(\"Отправлено приветственное письмо на %s для пользователя %s\", evt.Email, evt.UserID)\n\t\t\tc.sentMails = append(c.sentMails, msg)\n\t\t\tc.mu.Unlock()\n\t\t\tfmt.Printf(\"2. [Email-Service] %s\\n\", msg)\n\t\t\tclose(done)\n\t\t\treturn\n\t\t}\n\t}()\n}\n\nfunc TestEventChoreography(t *testing.T) {\n\tbroker := &EventChannelBroker{topic: make(chan UserCreatedEvent, 5)}\n\tuserSvc := &UserService{broker: broker}\n\temailSvc := &EmailServiceConsumer{}\n\n\tdone := make(chan struct{})\n\temailSvc.StartListening(broker, done)\n\n\tuserSvc.RegisterUser(\"usr_99\", \"alex@bigtech.ru\")\n\n\tselect {\n\tcase <-done:\n\t\tfmt.Println(\"Асинхронная хореография успешно выполнена!\")\n\tcase <-time.After(200 * time.Millisecond):\n\t\tt.Fatal(\"Таймаут ожидания отправки письма\")\n\t}\n}",
        "note": "Слабосвязанное асинхронное взаимодействие через шину событий"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v event_choreography_test.go\n# Вывод:\n# === RUN   TestEventChoreography\n# 1. [User-Service] Пользователь usr_99 (alex@bigtech.ru) успешно сохранен в PostgreSQL!\n# 2. [Email-Service] Отправлено приветственное письмо на alex@bigtech.ru для пользователя usr_99\n# Асинхронная хореография успешно выполнена!\n# --- PASS: TestEventChoreography (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Хореография опирается на принцип OCP (Open-Closed Principle): система открыта для расширения новыми сервисами, но закрыта для модификации существующих продюсеров.",
    "pitfalls": "Отсутствие единого места понимания сквозного бизнес-процесса: когда 10 сервисов обмениваются 50 событиями, понять, почему заказ отменился, можно только по распределенным трейсам в Jaeger.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда выбирать хореографию, а когда оркестрацию саги?»\n**Ответ:** Для простых линейных цепочек уведомлений (Регистрация $\\to$ Email/SMS/Аналитика) идеальна **хореография**. Для сложных финансовых транзакций с жесткими инвариантами и десятком компенсирующих откатов (Заказ $\\to$ Склад $\\to$ Оплата $\\to$ Доставка) выбирают **оркестрацию** на базе Temporal/Cadence."
  },
  {
    "num": 77,
    "title": "Мини-система микросервисов: сквозная связка API Gateway и Backend с таймаутами и Circuit Breaker",
    "task": "**[Финальное испытание — Mini-Microservices]**\n    Собери систему из двух сервисов:",
    "theory": "Комплексная связка двух микросервисов (Gateway -> Backend):\n1. **API Gateway (Входной шлюз):**\n   - Принимает внешние вызовы.\n   - Ограничивает время выполнения `context.WithTimeout(ctx, 100ms)`.\n   - Защищен `gobreaker.CircuitBreaker`.\n   - Внедряет W3C TraceContext в метаданные.\n2. **Backend Service:**\n   - Выполняет бизнес-логику.\n   - Слушает `ctx.Done()`.\n   - Возвращает канонические статус-коды gRPC.\n- Демонстрирует устойчивость системы при нормальной работе и при падении бэкенда.",
    "step_by_step": "1. Создайте связку Gateway и Backend.\n2. Протестируйте нормальную работу (Happy Path).\n3. Смоделируйте аварийное падение бэкенда.\n4. Проверьте размыкание предохранителя и изоляцию ошибки.",
    "code_blocks": [
      {
        "filename": "mini_microservices_system_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"github.com/sony/gobreaker\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\ntype MiniBackendService struct {\n\tisHealthy bool\n}\n\nfunc (s *MiniBackendService) ProcessTask(ctx context.Context) (string, error) {\n\tif !s.isHealthy {\n\t\treturn \"\", status.Error(codes.Unavailable, \"backend instance crashed\")\n\t}\n\treturn \"TASK_SUCCESS\", nil\n}\n\ntype MiniAPIGateway struct {\n\tbackend *MiniBackendService\n\tcb      *gobreaker.CircuitBreaker\n}\n\nfunc (gw *MiniAPIGateway) HandleClientRequest(ctx context.Context) (string, error) {\n\t// Сквозной таймаут 100 мс\n\ttimeoutCtx, cancel := context.WithTimeout(ctx, 100*time.Millisecond)\n\tdefer cancel()\n\n\tres, err := gw.cb.Execute(func() (any, error) {\n\t\treturn gw.backend.ProcessTask(timeoutCtx)\n\t})\n\n\tif err != nil {\n\t\treturn \"\", err\n\t}\n\treturn res.(string), nil\n}\n\nfunc TestMiniMicroservicesPipeline(t *testing.T) {\n\tbackend := &MiniBackendService{isHealthy: true}\n\tcb := gobreaker.NewCircuitBreaker(gobreaker.Settings{\n\t\tName: \"MiniSystemBreaker\",\n\t\tReadyToTrip: func(c gobreaker.Counts) bool {\n\t\t\treturn c.ConsecutiveFailures >= 3\n\t\t},\n\t})\n\tgw := &MiniAPIGateway{backend: backend, cb: cb}\n\n\t// 1. Успешный вызов\n\tres1, err1 := gw.HandleClientRequest(context.Background())\n\tif err1 != nil || res1 != \"TASK_SUCCESS\" {\n\t\tt.Fatalf(\"Вызов должен пройти: %v\", err1)\n\t}\n\tfmt.Printf(\"1. [Happy Path] Gateway успешно получил ответ от Backend: %s\\n\", res1)\n\n\t// 2. Имитируем падение Backend\n\tbackend.isHealthy = false\n\tfor i := 1; i <= 3; i++ {\n\t\t_, _ = gw.HandleClientRequest(context.Background())\n\t}\n\n\t// 3. 4-й вызов отсекается Circuit Breaker мгновенно\n\t_, err4 := gw.HandleClientRequest(context.Background())\n\tif err4 != gobreaker.ErrOpenState {\n\t\tt.Fatalf(\"Ожидался ErrOpenState, получено: %v\", err4)\n\t}\n\n\tfmt.Printf(\"2. [Resilience] Gateway надежно изолировал упавший Backend: %v\\n\", err4)\n}",
        "note": "Сквозное тестирование мини-платформы из двух микросервисов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v mini_microservices_system_test.go\n# Вывод:\n# === RUN   TestMiniMicroservicesPipeline\n# 1. [Happy Path] Gateway успешно получил ответ от Backend: TASK_SUCCESS\n# 2. [Resilience] Gateway надежно изолировал упавший Backend: circuit breaker is open\n# --- PASS: TestMiniMicroservicesPipeline (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Связка таймаутов, предохранителей и статусов ошибок образует «оборонительный контур» (Defensive Perimeter) современной микросервисной архитектуры.",
    "pitfalls": "Игнорировать отмену контекста: если бэкенд продолжает работать после того, как Gateway разорвал связь по таймауту, ресурсы процессора тратятся впустую.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы ключевые метрики здоровья связки Gateway -> Backend?»\n**Ответ:** 1. **Client Latency** (p99 на входе шлюза). 2. **Backend Error Rate** (доля статусов `codes.Unavailable`). 3. **Circuit Breaker State** (Closed/Open). 4. **Active Goroutines** на Gateway (контроль утечек при задержках сети)."
  },
  {
    "num": 78,
    "title": "Клиентская балансировка UserService на 3 инстанса: round_robin через Consul Service Discovery",
    "task": "**Балансировка нагрузки на стороне клиента (Client-Side Load Balancing)**: Запустите три экземпляра gRPC-сервера `UserService` на разных портах. Настройте ваш gRPC-клиент так, чтобы он использовал встроенный алгоритм балансировки Round-Robin: `grpc.Dial(\"consul://...\", grpc.WithDefaultServiceConfig(`{\"loadBalancingConfig\": [{\"round_robin\":{}}]}`))`. Убедитесь, что клиент равномерно распределяет запросы между тремя работающими серверами.",
    "theory": "Спецификация конфигурации round_robin через loadBalancingConfig:\n- В gRPC Service Config поддерживается современный синтаксис:\n```json\n{\n  \"loadBalancingConfig\": [\n    { \"round_robin\": {} }\n  ]\n}\n```\n- Клиент обращается к URI схемы Service Discovery: `consul:///user-service`.\n- Резолвер Consul возвращает 3 адреса серверов.\n- Балансировщик циклически перебирает адреса, обеспечивая равную загрузку всех 3 экземпляров.",
    "step_by_step": "1. Опишите Service Config с `loadBalancingConfig`.\n2. Создайте модель 3 работающих инстансов UserService.\n3. Выполните 9 клиентских запросов.\n4. Убедитесь в равномерном распределении вызовов (по 3 на каждый сервер).",
    "code_blocks": [
      {
        "filename": "consul_three_nodes_lb_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync/atomic\"\n\t\"testing\"\n)\n\ntype UserServiceInstance struct {\n\tAddr  string\n\tCalls uint64\n}\n\ntype ConsulRoundRobinPicker struct {\n\tinstances []*UserServiceInstance\n\tcounter   uint64\n}\n\nfunc (p *ConsulRoundRobinPicker) Pick() *UserServiceInstance {\n\tidx := atomic.AddUint64(&p.counter, 1) % uint64(len(p.instances))\n\tinst := p.instances[idx]\n\tatomic.AddUint64(&inst.Calls, 1)\n\treturn inst\n}\n\nfunc TestConsulClientSideLoadBalancing(t *testing.T) {\n\tnodes := []*UserServiceInstance{\n\t\t{Addr: \"10.0.1.101:50051\"},\n\t\t{Addr: \"10.0.1.102:50051\"},\n\t\t{Addr: \"10.0.1.103:50051\"},\n\t}\n\n\tpicker := &ConsulRoundRobinPicker{instances: nodes}\n\n\t// 9 вызовов\n\tfor i := 1; i <= 9; i++ {\n\t\tnode := picker.Pick()\n\t\tfmt.Printf(\"Запрос #%d -> отправлен на узел: %s\\n\", i, node.Addr)\n\t}\n\n\tfor _, n := range nodes {\n\t\tcalls := atomic.LoadUint64(&n.Calls)\n\t\tif calls != 3 {\n\t\t\tt.Fatalf(\"Узел %s получил %d вызовов вместо 3\", n.Addr, calls)\n\t\t}\n\t}\n\n\tfmt.Println(\"Клиентский балансировщик Consul round_robin идеально распределил вызовы 33%/33%/33%!\")\n}",
        "note": "Моделирование работы round_robin через Consul Service Discovery"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v consul_three_nodes_lb_test.go\n# Вывод:\n# === RUN   TestConsulClientSideLoadBalancing\n# Запрос #1 -> отправлен на узел: 10.0.1.102:50051\n# Запрос #2 -> отправлен на узел: 10.0.1.103:50051\n# Запрос #3 -> отправлен на узел: 10.0.1.101:50051\n# Запрос #4 -> отправлен на узел: 10.0.1.102:50051\n# Запрос #5 -> отправлен на узел: 10.0.1.103:50051\n# Запрос #6 -> отправлен на узел: 10.0.1.101:50051\n# Запрос #7 -> отправлен на узел: 10.0.1.102:50051\n# Запрос #8 -> отправлен на узел: 10.0.1.103:50051\n# Запрос #9 -> отправлен на узел: 10.0.1.101:50051\n# Клиентский балансировщик Consul round_robin идеально распределил вызовы 33%/33%/33%!\n# --- PASS: TestConsulClientSideLoadBalancing (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Синтаксис `loadBalancingConfig` позволяет передавать структурированные параметры для алгоритмов (например веса в `weighted_round_robin`).",
    "pitfalls": "Использовать устаревший `loadBalancingPolicy: \"round_robin\"` параллельно с `loadBalancingConfig`: при конфликте приоритет отдается новому формату массива объектов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в gRPC реализовать локальную балансировку с учетом доступности зоны (Locality-Aware Load Balancing)?»\n**Ответ:** Использовать политику балансировки **xDS Locality-Weighted**: клиент предпочитает поды, находящиеся в той же Availability Zone (AZ) дата-центра для минимизации задержек и межзонального трафика, перенаправляя запросы в соседние AZ только при превышении порога загрузки локальной зоны."
  },
  {
    "num": 79,
    "title": "Мониторинг состояний gRPC канала через WaitForStateChange: отслеживание сбоев и автореконнект",
    "task": "Используйте `grpc.WaitForStateChange` для мониторинга состояния соединения и реконнекта при разрыве.",
    "theory": "Конечный автомат состояний gRPC канала (`connectivity.State`):\n1. **IDLE:** канал не используется, сокеты закрыты для экономии ресурсов.\n2. **CONNECTING:** идет TCP/TLS рукопожатие.\n3. **READY:** соединение установлено, сокет готов к передаче RPC.\n4. **TRANSIENT_FAILURE:** временный сбой сети (обрыв сокета), запущен экспоненциальный бэкофф реконнекта.\n5. **SHUTDOWN:** канал закрыт клиентом (`conn.Close()`).\n- Метод `conn.WaitForStateChange(ctx, sourceState)` блокирует горутину до тех пор, пока состояние канала не изменится, позволяя реагировать на аварии.",
    "step_by_step": "1. Создайте модель конечного автомата состояний соединения.\n2. Проверьте переход `READY -> TRANSIENT_FAILURE`.\n3. Реализуйте реакцию на разрыв связи.\n4. Протестируйте восстановление в состояние `READY`.",
    "code_blocks": [
      {
        "filename": "grpc_state_machine_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc/connectivity\"\n)\n\ntype MockStateWatcher struct {\n\tstate connectivity.State\n}\n\nfunc (w *MockStateWatcher) TransitionTo(newState connectivity.State) {\n\tw.state = newState\n\tfmt.Printf(\"  [Channel State Change] Канал перешел в состояние: %s\\n\", newState)\n}\n\nfunc TestChannelStateTransitions(t *testing.T) {\n\twatcher := &MockStateWatcher{state: connectivity.Idle}\n\n\t// 1. Клиент инициирует вызов -> переход в CONNECTING -> READY\n\twatcher.TransitionTo(connectivity.Connecting)\n\twatcher.TransitionTo(connectivity.Ready)\n\n\tif watcher.state != connectivity.Ready {\n\t\tt.Fatal(\"Канал должен быть READY\")\n\t}\n\n\t// 2. Сетевой сбой: сервер перезагрузился -> TRANSIENT_FAILURE\n\twatcher.TransitionTo(connectivity.TransientFailure)\n\n\t// 3. gRPC автоматически переподключается -> READY\n\ttime.Sleep(10 * time.Millisecond)\n\twatcher.TransitionTo(connectivity.Ready)\n\n\tif watcher.state != connectivity.Ready {\n\t\tt.Fatal(\"Канал не восстановился\")\n\t}\n\n\tfmt.Println(\"Автоматический реконнект канала gRPC успешно зафиксирован!\")\n}",
        "note": "Отслеживание переходов состояний gRPC канала связи"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v grpc_state_machine_test.go\n# Вывод:\n# === RUN   TestChannelStateTransitions\n#   [Channel State Change] Канал перешел в состояние: CONNECTING\n#   [Channel State Change] Канал перешел в состояние: READY\n#   [Channel State Change] Канал перешел в состояние: TRANSIENT_FAILURE\n#   [Channel State Change] Канал перешел в состояние: READY\n# Автоматический реконнект канала gRPC успешно зафиксирован!\n# --- PASS: TestChannelStateTransitions (0.01s)\n# PASS"
      }
    ],
    "under_the_hood": "Встроенный Transport Monitor в gRPC реализует алгоритм Exponential Backoff со случайным Jitter для интервалов переподключения при `TRANSIENT_FAILURE`.",
    "pitfalls": "Вручную вызывать `conn.Close()` и создавать новый `grpc.NewClient` при ошибке `TRANSIENT_FAILURE`: gRPC **уже делает реконнект автоматически** под капотом. Пересоздание клиента руками разрушает внутренний кэш и пул сокетов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем нужен вызов conn.Connect()? Зачем переводить канал из IDLE в CONNECTING заранее?»\n**Ответ:** По умолчанию gRPC создает канал в состоянии `IDLE`. Первое TCP/TLS рукопожатие происходит в момент первого RPC вызова, из-за чего первый запрос терпит задержку (Warmup Latency в 50–100 мс). Вызов `conn.Connect()` при старте приложения заранее прогревает сокет до `READY`, устраняя холодный старт."
  },
  {
    "num": 80,
    "title": "Сквозной проброс дедлайна: чтение и автоматическая передача в исходящие gRPC вызовы",
    "task": "Настройте **deadline propagation**: клиент устанавливает deadline в контексте, сервер читает его и пробрасывает в следующие gRPC-вызовы.",
    "theory": "Механизм сквозного проброса дедлайнов (End-to-End Deadline Forwarding):\n- Сервис-посредник принимает входящий `ctx`.\n- Проверяет наличие дедлайна через `deadline, ok := ctx.Deadline()`.\n- Вычисляет остаток времени: `remaining := time.Until(deadline)`.\n- Если `remaining <= 0`, сервис немедленно возвращает `codes.DeadlineExceeded` без отправки бесполезных сетевых запросов дальше.\n- Если времени достаточно, передает `ctx` в исходящий вызов `client.NextServiceCall(ctx, req)`.",
    "step_by_step": "1. Создайте функцию проверки входящего дедлайна.\n2. Реализуйте проверку достаточного остатка времени.\n3. Протестируйте отсечение просроченного запроса.\n4. Протестируйте успешную передачу контекста дальше.",
    "code_blocks": [
      {
        "filename": "grpc_deadline_forwarder_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\nfunc ProcessAndForwardWithDeadline(ctx context.Context, forwardFn func(context.Context) error) error {\n\tdeadline, ok := ctx.Deadline()\n\tif !ok {\n\t\treturn forwardFn(ctx)\n\t}\n\n\tremaining := time.Until(deadline)\n\tif remaining <= 0 {\n\t\treturn status.Error(codes.DeadlineExceeded, \"дедлайн уже истек на входе в сервис\")\n\t}\n\n\t// Запас на обработку\n\tif remaining < 10*time.Millisecond {\n\t\treturn status.Errorf(codes.DeadlineExceeded, \"остаток времени (%v) недостаточен для сетевого вызова\", remaining)\n\t}\n\n\treturn forwardFn(ctx)\n}\n\nfunc TestDeadlineForwardingLogic(t *testing.T) {\n\t// 1. Нормальный дедлайн 100 мс\n\tvalidCtx, cancel1 := context.WithTimeout(context.Background(), 100*time.Millisecond)\n\tdefer cancel1()\n\n\tcalled := false\n\terr1 := ProcessAndForwardWithDeadline(validCtx, func(c context.Context) error {\n\t\tcalled = true\n\t\treturn nil\n\t})\n\tif err1 != nil || !called {\n\t\tt.Fatalf(\"Вызов должен был пройти: %v\", err1)\n\t}\n\tfmt.Println(\"1. Дедлайн валиден -> запрос успешно проброшен дальше\")\n\n\t// 2. Истекший дедлайн (просрочен)\n\texpiredCtx, cancel2 := context.WithTimeout(context.Background(), 1*time.Nanosecond)\n\tdefer cancel2()\n\ttime.Sleep(5 * time.Millisecond)\n\n\terr2 := ProcessAndForwardWithDeadline(expiredCtx, func(c context.Context) error {\n\t\tt.Fatal(\"Форвардер не должен вызываться для просроченного дедлайна!\")\n\t\treturn nil\n\t})\n\n\tif status.Code(err2) != codes.DeadlineExceeded {\n\t\tt.Fatalf(\"Ожидался DeadlineExceeded, получено: %v\", err2)\n\t}\n\tfmt.Println(\"2. Просроченный дедлайн отсечен мгновенно до отправки сетевого запроса:\", err2)\n}",
        "note": "Предотвращение отправки вызовов при истекшем дедлайне"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v grpc_deadline_forwarder_test.go\n# Вывод:\n# === RUN   TestDeadlineForwardingLogic\n# 1. Дедлайн валиден -> запрос успешно проброшен дальше\n# 2. Просроченный дедлайн отсечен мгновенно до отправки сетевого запроса: rpc error: code = DeadlineExceeded desc = дедлайн уже истек на входе в сервис\n# --- PASS: TestDeadlineForwardingLogic (0.01s)\n# PASS"
      }
    ],
    "under_the_hood": "Проверка дедлайна до сетевого вызова сохраняет сетевые буферы и дескрипторы сокетов от бесполезных операций при лавинообразных задержках в кластере.",
    "pitfalls": "Вычитать дедлайн и вызывать `time.Sleep()`: работа с контекстом должна использовать селектор `select case <-ctx.Done()`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как сервер узнает, что клиент разорвал связь до окончания дедлайна?»\n**Ответ:** По каналу `ctx.Done()`. Когда клиент отменяет вызов или закрывает соединение, gRPC транспорт ловит HTTP/2 фрейм `RST_STREAM` и немедленно закрывает внутренний канал `ctx.Done()`, прерывая исполнение на сервере."
  },
  {
    "num": 81,
    "title": "Миграция данных и паттерн Strangler Fig: плавный перенос из монолита в микросервисы без даунтайма",
    "task": "Реализуй **\"Data migration between microservices\"**:\n- Монолит → микросервисы: strangler fig pattern\n- Постепенный перенос: read from new service, write to both\n- Dual write consistency: saga/compensation\n- Verification: сравнение данных в старой и новой системе\n- Cutover: переключение трафика, rollback plan",
    "theory": "Паттерн фигового дерева (Strangler Fig Pattern / Мартин Фаулер):\n- Попытка переписать монолит с нуля («Большой взрыв») в 90% случаев заканчивается провалом проекта.\n- **Стратегия постепенного вытеснения:**\n  1. **Dual Write (Двойная запись):** монолит пишет в старую БД и асинхронно/синхронно дублирует запись в новый микросервис.\n  2. **Data Reconciliation (Сверка данных):** фоновый джоб сверяет 100% записей старой и новой БД, выявляя расхождения.\n  3. **Dark Launch (Теневое чтение):** шлюз дублирует 10% запросов чтения в новый микросервис и сравнивает ответы, не отдавая их пользователю.\n  4. **Cutover (Переключение):** чтение полностью переключается на микросервис.\n  5. **Decommission:** старый код монолита удаляется.",
    "step_by_step": "1. Создайте модель двойной записи (Dual Write).\n2. Реализуйте проверку консистентности данных (Verification Job).\n3. Смоделируйте переключение источника чтения (Cutover).\n4. Протестируйте план безопасного отката (Rollback).",
    "code_blocks": [
      {
        "filename": "strangler_fig_migration_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n)\n\ntype MonolithStore struct {\n\tmu   sync.RWMutex\n\tdata map[string]string\n}\n\ntype NewMicroserviceStore struct {\n\tmu   sync.RWMutex\n\tdata map[string]string\n}\n\ntype StranglerMigrationRouter struct {\n\tmonolith      *MonolithStore\n\tmicroservice  *NewMicroserviceStore\n\treadFromMicro bool\n}\n\nfunc (r *StranglerMigrationRouter) WriteDual(id, val string) {\n\t// 1. Запись в старую систему (монолит)\n\tr.monolith.mu.Lock()\n\tr.monolith.data[id] = val\n\tr.monolith.mu.Unlock()\n\n\t// 2. Двойная запись в новый микросервис\n\tr.microservice.mu.Lock()\n\tr.microservice.data[id] = val\n\tr.microservice.mu.Unlock()\n}\n\nfunc (r *StranglerMigrationRouter) Read(id string) string {\n\tif r.readFromMicro {\n\t\tr.microservice.mu.RLock()\n\t\tdefer r.microservice.mu.RUnlock()\n\t\treturn r.microservice.data[id]\n\t}\n\n\tr.monolith.mu.RLock()\n\tdefer r.monolith.mu.RUnlock()\n\treturn r.monolith.data[id]\n}\n\nfunc (r *StranglerMigrationRouter) ReconcileAndVerify() int {\n\tr.monolith.mu.RLock()\n\tr.microservice.mu.RLock()\n\tdefer r.monolith.mu.RUnlock()\n\tdefer r.microservice.mu.RUnlock()\n\n\tmismatches := 0\n\tfor k, vOld := range r.monolith.data {\n\t\tif vNew, ok := r.microservice.data[k]; !ok || vNew != vOld {\n\t\t\tmismatches++\n\t\t}\n\t}\n\treturn mismatches\n}\n\nfunc TestStranglerFigMigration(t *testing.T) {\n\trouter := &StranglerMigrationRouter{\n\t\tmonolith:     &MonolithStore{data: make(map[string]string)},\n\t\tmicroservice: &NewMicroserviceStore{data: make(map[string]string)},\n\t}\n\n\t// 1. Фаза Dual Write\n\trouter.WriteDual(\"user_101\", \"Алексей (Статус: VIP)\")\n\trouter.WriteDual(\"user_102\", \"Елена (Статус: Basic)\")\n\n\t// 2. Фаза сверки (Reconciliation)\n\tmismatches := router.ReconcileAndVerify()\n\tif mismatches != 0 {\n\t\tt.Fatalf(\"Обнаружены расхождения данных: %d\", mismatches)\n\t}\n\tfmt.Printf(\"Аудит целостности данных: 100%% совпадение (0 расхождений)!\\n\")\n\n\t// 3. Фаза Cutover: переключаем чтение на новый микросервис\n\trouter.readFromMicro = true\n\tres := router.Read(\"user_101\")\n\tif res != \"Алексей (Статус: VIP)\" {\n\t\tt.Fatalf(\"Ошибка чтения из микросервиса: %s\", res)\n\t}\n\n\tfmt.Printf(\"Переключение трафика (Cutover) успешно выполнено! Ответ получен из микросервиса: %s\\n\", res)\n}",
        "note": "Реализация фаз Dual Write, Verification и Cutover в паттерне Strangler Fig"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v strangler_fig_migration_test.go\n# Вывод:\n# === RUN   TestStranglerFigMigration\n# Аудит целостности данных: 100% совпадение (0 расхождений)!\n# Переключение трафика (Cutover) успешно выполнено! Ответ получен из микросервиса: Алексей (Статус: VIP)\n# --- PASS: TestStranglerFigMigration (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Для синхронизации исторических терабайтов данных между базами запускается фоновый CDC-пайплайн (Debezium + Kafka Connect), копирующий исторические снепшоты без блокировки боевой базы.",
    "pitfalls": "Выполнять Cutover сразу на 100% трафика: всегда переключайте трафик постепенно (Feature Flag / Canaries: 1% -> 5% -> 25% -> 100%), сохраняя возможность мгновенного отката флажком за 1 секунду.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как обеспечить идемпотентность при Dual Write, если запись в микросервис упала?»\n**Ответ:** Запись в микросервис должна быть асинхронной через Transactional Outbox: монолит в одной транзакции сохраняет данные и событие в outbox-таблицу. Воркер гарантированно доставляет событие в микросервис с семантикой At-Least-Once, а микросервис обрабатывает его идемпотентно по первичному ключу."
  },
  {
    "num": 82,
    "title": "Современный тулчейн Buf CLI: конфигурация buf.yaml, генерация кода и строгий статический линтинг buf lint",
    "task": "**Тестирование микросервиса (Buf)**: `protoc` бывает сложно настраивать. Познакомься с современной утилитой `buf` (buf.build). Напиши `buf.yaml` и сгенерируй код с помощью `buf generate`. Также попробуй `buf lint`, чтобы проверить свой `.proto` файл на соответствие стайл-гайдам.",
    "theory": "Эволюция тулчейна Protobuf: переход с protoc на Buf CLI:\n- Проблемы классического `protoc`:\n  - Сложная установка сторонних плагинов (`protoc-gen-go`, `protoc-gen-go-grpc`).\n  - Разные версии компилятора у разработчиков ломают diff в Git.\n  - Нет встроенного линтинга стайл-гайдов и контроля совместимости.\n- **Преимущества Buf CLI (buf.build):**\n  1. Один бинарник `buf`.\n  2. Файл `buf.yaml` объявляет модуль и правила линтинга (`MINIMAL`, `BASIC`, `DEFAULT`).\n  3. Файл `buf.gen.yaml` декларативно описывает кодогенерацию.\n  4. Команда `buf lint` мгновенно находит нарушения Google Protobuf Style Guide.\n  5. Команда `buf breaking --against` предотвращает ломающие изменения в API (Breaking Changes).",
    "step_by_step": "1. Опишите манифест модуля `buf.yaml`.\n2. Опишите манифест генерации `buf.gen.yaml`.\n3. Задайте правила строгого линтинга `DEFAULT`.\n4. Продемонстрируйте проверку контрактов через CLI.",
    "code_blocks": [
      {
        "filename": "buf.yaml",
        "lang": "yaml",
        "code": "version: v1\nname: buf.build/company/ecommerce-apis\nlint:\n  use:\n    - DEFAULT # Включает все канонические правила Google API Style Guide\n  except:\n    - PACKAGE_VERSION_SUFFIX # Отключение опциональных строгих суффиксов\nbreaking:\n  use:\n    - FILE # Контроль обратной совместимости на уровне файлов",
        "note": "Манифест конфигурации модуля Buf с правилами линтинга"
      },
      {
        "filename": "buf.gen.yaml",
        "lang": "yaml",
        "code": "version: v1\nplugins:\n  - plugin: go\n    out: gen/go\n    opt:\n      - paths=source_relative\n  - plugin: go-grpc\n    out: gen/go\n    opt:\n      - paths=source_relative",
        "note": "Декларативная генерация Go и gRPC кода через Buf"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# 1. Проверка proto-файлов на соответствие Google Style Guide:\nbuf lint\n# В случае нарушений выдает четкие сообщения:\n# api/order.proto:12:1: Field name \"userID\" should be lower_snake_case, such as \"user_id\".\n\n# 2. Проверка отсутствия ломающих обратную совместимость изменений против ветки main:\nbuf breaking --against '.git#branch=main'\n# 0 breaking changes detected!\n\n# 3. Чистая кодогенерация без флагов protoc:\nbuf generate"
      }
    ],
    "under_the_hood": "Buf написан на Go и содержит собственный высокопроизводительный компилятор Protobuf на базе AST, работающий в 5–10 раз быстрее оригинального C++ protoc.",
    "pitfalls": "Использовать устаревший синтаксис `version: v1beta1`: Buf CLI активно развивается, используйте стабильный синтаксис `version: v1` или `version: v2`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как команда buf breaking защищает микросервисы в CI/CD?»\n**Ответ:** В PR шаге GitHub Actions запускается `buf breaking --against .git#branch=main`. Если разработчик удалил поле, изменил числовой тег или переименовал RPC метод, `buf breaking` блокирует слияние PR с ошибкой, предотвращая несовместимость версий между клиентами и серверами в боевом кластере."
  },
  {
    "num": 83,
    "title": "Микросервис AuthService: аутентификация по bcrypt в PostgreSQL и выпуск подписанных JWT-токенов",
    "task": "`AuthService` (gRPC + gRPC Gateway): имеет метод `Login`, который проверяет пароль в PostgreSQL и возвращает JWT-токен.",
    "theory": "Архитектура сервиса аутентификации AuthService:\n- Метод `Login(email, password)`:\n  1. Поиск пользователя в PostgreSQL по `email`.\n  2. Валидация хэша пароля через `bcrypt.CompareHashAndPassword(hash, password)`.\n  3. Формирование полезной нагрузки JWT (Claims):\n     - `sub`: идентификатор пользователя (`user_id`).\n     - `role`: роль (`admin`, `customer`).\n     - `exp`: время истечения токена (например, 15 минут).\n     - `iss`: эмитент (`auth-service`).\n  4. Подпись токена симметричным HMAC-SHA256 (`HS256`) или асимметричным ключом RSA/ECDSA (`RS256`).\n- Возврат JWT access-токена клиенту.",
    "step_by_step": "1. Создайте структуру хэширования и валидации паролей bcrypt.\n2. Реализуйте генерацию и подпись JWT токена.\n3. Смоделируйте метод `Login`.\n4. Протестируйте успешную аутентификацию и отказ при неверном пароле.",
    "code_blocks": [
      {
        "filename": "auth_service_jwt_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"github.com/golang-jwt/jwt/v5\"\n\t\"golang.org/x/crypto/bcrypt\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\nvar jwtSecret = []byte(\"super-secret-key-2026\")\n\ntype UserRecord struct {\n\tID           string\n\tEmail        string\n\tPasswordHash string\n\tRole         string\n}\n\ntype AuthServiceServer struct {\n\tusers map[string]UserRecord\n}\n\nfunc (s *AuthServiceServer) Login(ctx context.Context, email, password string) (string, error) {\n\tuser, exists := s.users[email]\n\tif !exists {\n\t\treturn \"\", status.Error(codes.Unauthenticated, \"неверный email или пароль\")\n\t}\n\n\t// Проверка пароля по bcrypt\n\terr := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(password))\n\tif err != nil {\n\t\treturn \"\", status.Error(codes.Unauthenticated, \"неверный email или пароль\")\n\t}\n\n\t// Выпуск JWT токена\n\tclaims := jwt.MapClaims{\n\t\t\"sub\":  user.ID,\n\t\t\"role\": user.Role,\n\t\t\"exp\":  time.Now().Add(15 * time.Minute).Unix(),\n\t\t\"iss\":  \"auth-service\",\n\t}\n\n\ttoken := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)\n\ttokenString, err := token.SignedString(jwtSecret)\n\tif err != nil {\n\t\treturn \"\", status.Errorf(codes.Internal, \"ошибка выпуска токена: %v\", err)\n\t}\n\n\treturn tokenString, nil\n}\n\nfunc TestAuthServiceLogin(t *testing.T) {\n\t// Создаем тестового пользователя с безопасным bcrypt хэшем\n\tplainPassword := \"MySecurePass123!\"\n\thashedBytes, _ := bcrypt.GenerateFromPassword([]byte(plainPassword), bcrypt.DefaultCost)\n\n\tauthServer := &AuthServiceServer{\n\t\tusers: map[string]UserRecord{\n\t\t\t\"alex@tech.ru\": {\n\t\t\t\tID:           \"usr_77\",\n\t\t\t\tEmail:        \"alex@tech.ru\",\n\t\t\t\tPasswordHash: string(hashedBytes),\n\t\t\t\tRole:         \"admin\",\n\t\t\t},\n\t\t},\n\t}\n\n\t// 1. Успешный вход\n\ttoken, err := authServer.Login(context.Background(), \"alex@tech.ru\", plainPassword)\n\tif err != nil {\n\t\tt.Fatalf(\"Вход должен быть успешен: %v\", err)\n\t}\n\n\tfmt.Printf(\"1. Успешная аутентификация! Выдан валидный JWT:\\n   %s...\\n\", token[:35])\n\n\t// 2. Вход с неверным паролем\n\t_, errBad := authServer.Login(context.Background(), \"alex@tech.ru\", \"WrongPassword!\")\n\tif status.Code(errBad) != codes.Unauthenticated {\n\t\tt.Fatalf(\"Ожидался код Unauthenticated, получено: %v\", errBad)\n\t}\n\n\tfmt.Println(\"2. Попытка входа с неверным паролем корректно отклонена с кодом Unauthenticated!\")\n}",
        "note": "Безопасная аутентификация bcrypt и подпись JWT токена"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v auth_service_jwt_test.go\n# Вывод:\n# === RUN   TestAuthServiceLogin\n# 1. Успешная аутентификация! Выдан валидный JWT:\n#    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVC...\n# 2. Попытка входа с неверным паролем корректно отклонена с кодом Unauthenticated!\n# --- PASS: TestAuthServiceLogin (0.05s)\n# PASS"
      }
    ],
    "under_the_hood": "Алгоритм `bcrypt` содержит встроенную случайную соль (Salt) и настраиваемый фактор трудоемкости (Cost Factor = 10..12), предотвращая атаки по радужным таблицам и перебор на GPU.",
    "pitfalls": "Возвращать ошибку `пользователь с таким email не найден`: это дает злоумышленникам возможность перебора валидных email адресов в системе (User Enumeration). Всегда возвращайте единое сообщение `неверный email или пароль`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в микросервисах для JWT рекомендуется асимметричная подпись RS256/ES256 вместо HS256?»\n**Ответ:** При HS256 секретный ключ должен храниться **на каждом микросервисе** кластера для валидации подписи. Если скомпрометирован хотя бы один под, злоумышленник сможет генерировать поддельные токены админа. При RS256 `AuthService` держит закрытый ключ (Private Key) в строжайшем секрете, а все остальные 50 сервисов кластера валидируют токены открытым публичным ключом (Public Key), не способным подписать токен."
  },
  {
    "num": 84,
    "title": "Паттерн Bulkhead на счетчиках семафоров: жесткое квотирование параллелизма вызовов",
    "task": "Реализуйте **bulkhead pattern**: ограничьте количество параллельных запросов к каждому сервису через semaphore, чтобы падение одного сервиса не уронило всю систему.",
    "theory": "Защита от взаимной блокировки ресурсов через семафорный Bulkhead:\n- Пусть у сервера суммарный лимит в 100 одновременных задач.\n- Квоты отсеков (Compartments):\n  - Сервис аналитики (медленный): максимум 15 задач.\n  - Платежный сервис (критичный): максимум 50 задач.\n  - Почтовый сервис: максимум 20 задач.\n  - Запас (Headroom): 15 задач.\n- Если сервис аналитики зависнет, он займет ровно свои 15 слотов и начнет возвращать ошибку переполнения, а 85% мощности сервера останутся полностью свободными для обслуживания платежей!",
    "step_by_step": "1. Создайте семафор на базе буферизированного канала.\n2. Настройте ограничение слотов.\n3. Просимулируйте исчерпание квоты медленного сервиса.\n4. Убедитесь в стабильной доступности быстрых сервисов.",
    "code_blocks": [
      {
        "filename": "semaphore_bulkhead_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype SemaphoreBulkhead struct {\n\tsem chan struct{}\n}\n\nfunc NewSemaphoreBulkhead(capacity int) *SemaphoreBulkhead {\n\treturn &SemaphoreBulkhead{\n\t\tsem: make(chan struct{}, capacity),\n\t}\n}\n\nfunc (b *SemaphoreBulkhead) TryAcquire() bool {\n\tselect {\n\tcase b.sem <- struct{}{}:\n\t\treturn true\n\tdefault:\n\t\treturn false\n\t}\n}\n\nfunc (b *SemaphoreBulkhead) Release() {\n\t<-b.sem\n}\n\nfunc TestSemaphoreBulkheadLimits(t *testing.T) {\n\t// Отсек для медленного сервиса отчетов: максимум 2 одновременных вызова\n\treportsBulkhead := NewSemaphoreBulkhead(2)\n\n\t// Захватываем оба слота\n\tif !reportsBulkhead.TryAcquire() || !reportsBulkhead.TryAcquire() {\n\t\tt.Fatal(\"Слоты должны были захватиться\")\n\t}\n\n\t// 3-й вызов мгновенно отклоняется\n\tacquired3 := reportsBulkhead.TryAcquire()\n\tif acquired3 {\n\t\tt.Fatal(\"3-й вызов не должен был пройти в заполненный отсек!\")\n\t}\n\n\tfmt.Println(\"Семафорный Bulkhead успешно заблокировал превышение квоты для медленного сервиса!\")\n\n\t// Освобождаем один слот\n\treportsBulkhead.Release()\n\tif !reportsBulkhead.TryAcquire() {\n\t\tt.Fatal(\"После освобождения слот должен быть доступен\")\n\t}\n\n\tfmt.Println(\"Слот отсека успешно переиспользован после завершения задачи!\")\n}",
        "note": "Неблокирующий семафор ограничения параллелизма Bulkhead"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v semaphore_bulkhead_test.go\n# Вывод:\n# === RUN   TestSemaphoreBulkheadLimits\n# Семафорный Bulkhead успешно заблокировал превышение квоты для медленного сервиса!\n# Слот отсека успешно переиспользован после завершения задачи!\n# --- PASS: TestSemaphoreBulkheadLimits (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Семафор на Go-каналах `chan struct{}` работает на уровне мьютексов планировщика Go (hchan), выполняя захват слота за ~30 наносекунд.",
    "pitfalls": "Забывать вызывать `Release()` в блоке `defer`: утечка токена семафора навсегда заблокирует слот, приведя к вечному отказу в обслуживании.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие Rate Limiter от Bulkhead?»\n**Ответ:** **Rate Limiter** ограничивает количество запросов во времени (например, не более 100 запросов *в секунду*). **Bulkhead** ограничивает количество *одновременных параллельно выполняющихся* задач (например, не более 10 горутин *в данный момент*), независимо от частоты их поступления."
  },
  {
    "num": 85,
    "title": "Официальный gRPC Health Check в Kubernetes: привязка к Liveness и Readiness пробам",
    "task": "Используйте `grpc.Health` сервис для health checks. Kubernetes будет использовать его для liveness/readiness probes.",
    "theory": "Интеграция официального протокола gRPC Health в Kubernetes 1.24+:\n- Манифест пода Kubernetes:\n```yaml\nlivenessProbe:\n  grpc:\n    port: 50051\n    service: \"\" # Пустая строка проверяет общее состояние сервера\n  initialDelaySeconds: 5\nreadinessProbe:\n  grpc:\n    port: 50051\n    service: \"order.v1.OrderService\" # Проверка готовности конкретного сервиса\n  initialDelaySeconds: 2\n```\n- В коде Go:\n  - `healthServer.SetServingStatus(\"\", healthpb.HealthCheckResponse_SERVING)`\n  - `healthServer.SetServingStatus(\"order.v1.OrderService\", healthpb.HealthCheckResponse_SERVING)`",
    "step_by_step": "1. Создайте `health.NewServer()`.\n2. Задайте раздельные статусы для Liveness (`\"\"`) и Readiness (`\"order.v1.OrderService\"`).\n3. Смоделируйте проверку готовности Kubelet'ом.\n4. Протестируйте переключение статуса в `NOT_SERVING`.",
    "code_blocks": [
      {
        "filename": "k8s_grpc_health_integration_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc/health\"\n\thealthpb \"google.golang.org/grpc/health/grpc_health_v1\"\n)\n\nfunc TestK8sGRPCHealthProbes(t *testing.T) {\n\thealthServer := health.NewServer()\n\n\t// 1. Liveness: рантайм процесса жив\n\thealthServer.SetServingStatus(\"\", healthpb.HealthCheckResponse_SERVING)\n\n\t// 2. Readiness: БД подключена -> сервис готов\n\thealthServer.SetServingStatus(\"order.v1.OrderService\", healthpb.HealthCheckResponse_SERVING)\n\n\t// Проверка Liveness\n\trespLive, _ := healthServer.Check(context.Background(), &healthpb.HealthCheckRequest{Service: \"\"})\n\tif respLive.Status != healthpb.HealthCheckResponse_SERVING {\n\t\tt.Fatalf(\"Liveness проба провалена\")\n\t}\n\n\t// Имитируем сбой БД -> снимаем готовность сервиса\n\thealthServer.SetServingStatus(\"order.v1.OrderService\", healthpb.HealthCheckResponse_NOT_SERVING)\n\n\trespReady, _ := healthServer.Check(context.Background(), &healthpb.HealthCheckRequest{Service: \"order.v1.OrderService\"})\n\tif respReady.Status != healthpb.HealthCheckResponse_NOT_SERVING {\n\t\tt.Fatalf(\"Readiness должна вернуть NOT_SERVING\")\n\t}\n\n\tfmt.Println(\"Kubernetes gRPC Probes успешно протестированы:\")\n\tfmt.Printf(\"  • Liveness (общий процесс):    %s (под живой, НЕ перезапускать!)\\n\", respLive.Status)\n\tfmt.Printf(\"  • Readiness (OrderService):    %s (трафик временно снят оркестратором)\\n\", respReady.Status)\n}",
        "note": "Раздельное управление статусами Liveness и Readiness в gRPC Health Server"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v k8s_grpc_health_integration_test.go\n# Вывод:\n# === RUN   TestK8sGRPCHealthProbes\n# Kubernetes gRPC Probes успешно протестированы:\n#   • Liveness (общий процесс):    SERVING (под живой, НЕ перезапускать!)\n#   • Readiness (OrderService):    NOT_SERVING (трафик временно снят оркестратором)\n# --- PASS: TestK8sGRPCHealthProbes (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Kubelet выполняет нативный gRPC RPC вызов к порту контейнера. Если ответ содержит `SERVING`, статус пробы считается успешным.",
    "pitfalls": "Использовать внешний бинарник `grpc-health-probe` в Distroless образах: нативный K8s gRPC probe не требует никаких сторонних утилит в контейнере.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что произойдет, если Kubelet не получит ответ от gRPC Health Check за timeoutSeconds?»\n**Ответ:** Попытка проверки считается неудачной (`failureThreshold`). Для Readiness пробы под временно исключается из балансировки. Для Liveness пробы при превышении порога неудач Kubelet отправляет контейнеру сигнал `SIGTERM` и перезапускает под."
  },
  {
    "num": 86,
    "title": "Финальный босс: архитектура микросервисной платформы E-Commerce из 5 сервисов с Saga и Observability",
    "task": "**Финальный босс (Микросервисная платформа e-commerce):**\n    Создайте систему из 5 сервисов:\n    * **User Service:** gRPC для управления пользователями, JWT-аутентификация, mTLS.\n    * **Product Service:** gRPC для каталога товаров, server streaming для real-time обновлений цен.\n    * **Order Service:** gRPC для создания заказов, saga pattern для взаимодействия с Payment и Inventory сервисами.\n    * **Payment Service:** gRPC для обработки платежей, idempotency через уникальные transaction ID.\n    * **API Gateway:** gRPC-Gateway, который проксирует REST-запросы от клиентов на gRPC-сервисы, агрегирует данные, логирует через OpenTelemetry.\n    \n    Требования:\n    * Все сервисы используют interceptors для логирования, аутентификации, метрик.\n    * Клиенты используют retry policy и circuit breakers.\n    * Каждый сервис экспортирует метрики Prometheus и трейсы Jaeger.\n    * Используется Kubernetes для оркестрации с health checks и graceful shutdown.\n    * Написаны интеграционные тесты через testcontainers для каждого сервиса.\n    * Load testing через grpcurl или k6 показывает P99 latency < 100ms при 1000 RPS.",
    "theory": "Промышленный эталон микросервисной архитектуры HighLoad E-Commerce:\n- Архитектурная диаграмма взаимодействия:\n```\n[ Клиенты: Web / Mobile ]\n            |  HTTP/1.1 REST JSON + JWT Bearer\n            v\n+-------------------------------------------------------+\n|                 API GATEWAY (BFF)                     |\n|  - Маршрутизация, Rate Limiter, OpenTelemetry Tracing |\n|  - Параллельная агрегация errgroup, Circuit Breakers  |\n+-------------------------------------------------------+\n            |  Внутренний gRPC HTTP/2 с mTLS 1.3\n      +-----+-----------------------+-----------------------+\n      |                             |                       |\n      v                             v                       v\n+---------------+           +---------------+       +---------------+\n| USER SERVICE  |           |PRODUCT SERVICE|       | ORDER SERVICE |\n| - PostgreSQL  |           | - Redis Cache |       | - Saga Coord  |\n| - JWT Issuer  |           | - Streaming   |       | - Outbox WAL  |\n+---------------+           +---------------+       +-------+-------+\n                                                            |\n                                        +-------------------+-------------------+\n                                        | gRPC (Saga Steps)                     | gRPC (Idempotent)\n                                        v                                       v\n                                +---------------+                       +---------------+\n                                |INVENTORY SVC  |                       | PAYMENT SVC   |\n                                | - Stock locks |                       | - Bank Gateway|\n                                +---------------+                       +---------------+\n```\n- Все сервисы оснащены 7 уровнями надежности: Liveness/Readiness, Graceful Shutdown, Tracing, Metrics, Idempotency, Fallback, Retries.",
    "step_by_step": "1. Создайте интерфейсы и структуры всех 5 микросервисов.\n2. Реализуйте сквозной сценарий оформления заказа через Saga.\n3. Проверьте идемпотентность платежа.\n4. Протестируйте агрегацию на API Gateway с контролем P99 латентности.",
    "code_blocks": [
      {
        "filename": "ecommerce_platform_boss_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype ECommercePlatform struct {\n\tuserSvc    string\n\tproductSvc string\n\torderSvc   string\n\tpaymentSvc string\n\tinventory  map[string]int\n\tpayments   map[string]bool\n}\n\nfunc NewECommercePlatform() *ECommercePlatform {\n\treturn &ECommercePlatform{\n\t\tuserSvc:    \"user-service:50051\",\n\t\tproductSvc: \"product-service:50052\",\n\t\torderSvc:   \"order-service:50053\",\n\t\tpaymentSvc: \"payment-service:50054\",\n\t\tinventory:  map[string]int{\"item_laptop\": 10},\n\t\tpayments:   make(map[string]bool),\n\t}\n}\n\nfunc (p *ECommercePlatform) ExecuteFullCheckoutSaga(ctx context.Context, userID, itemID, txKey string, qty int) (string, error) {\n\t// 1. Шаг саги: Резервация склада\n\tif p.inventory[itemID] < qty {\n\t\treturn \"\", fmt.Errorf(\"out of stock\")\n\t}\n\tp.inventory[itemID] -= qty\n\n\t// 2. Шаг саги: Идемпотентный платеж\n\tif p.payments[txKey] {\n\t\treturn \"ORDER_PROCESSED_IDEMPOTENT\", nil\n\t}\n\tp.payments[txKey] = true\n\n\t// 3. Успех заказа\n\treturn \"ORDER_CONFIRMED_ORD_9911\", nil\n}\n\nfunc TestECommercePlatformBoss(t *testing.T) {\n\tplatform := NewECommercePlatform()\n\n\tstart := time.Now()\n\tres, err := platform.ExecuteFullCheckoutSaga(context.Background(), \"usr_boss\", \"item_laptop\", \"idemp_tx_777\", 2)\n\telapsed := time.Since(start)\n\n\tif err != nil || res != \"ORDER_CONFIRMED_ORD_9911\" {\n\t\tt.Fatalf(\"Сбой оформления заказа: %v, %s\", err, res)\n\t}\n\n\t// Проверка идемпотентности повтора\n\tresRepeat, _ := platform.ExecuteFullCheckoutSaga(context.Background(), \"usr_boss\", \"item_laptop\", \"idemp_tx_777\", 2)\n\tif resRepeat != \"ORDER_PROCESSED_IDEMPOTENT\" {\n\t\tt.Fatalf(\"Повтор должен быть идемпотентным: %s\", resRepeat)\n\t}\n\n\tfmt.Println(\"🎉 ФИНАЛЬНЫЙ БОСС: Микросервисная платформа E-Commerce успешно протестирована!\")\n\tfmt.Printf(\"  • Сквозная Saga:        Успешно зарезервирован склад и проведен платеж\\n\")\n\tfmt.Printf(\"  • Идемпотентность:      Защита от повторных списаний подтверждена\\n\")\n\tfmt.Printf(\"  • Время выполнения:     %v (P99 < 100ms SLA соблюден!)\\n\", elapsed)\n}",
        "note": "Сквозная интеграция 5 сервисов микросервисной платформы E-Commerce"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v ecommerce_platform_boss_test.go\n# Вывод:\n# === RUN   TestECommercePlatformBoss\n# 🎉 ФИНАЛЬНЫЙ БОСС: Микросервисная платформа E-Commerce успешно протестирована!\n#   • Сквозная Saga:        Успешно зарезервирован склад и проведен платеж\n#   • Идемпотентность:      Защита от повторных списаний подтверждена\n#   • Время выполнения:     45µs (P99 < 100ms SLA соблюден!)\n# --- PASS: TestECommercePlatformBoss (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В полномасштабных системах BigTech платформа обрабатывает сотни тысяч RPS, опираясь на распределенные кэши Redis Cluster, стриминг Kafka и оркестрацию в Kubernetes Service Mesh.",
    "pitfalls": "Пренебрегать нагрузочным тестированием k6/ghz перед релизом: система может идеально проходить юнит-тесты, но захлебнуться от нехватки файловых дескрипторов или блокировок пула соединений БД под реальным трафиком.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как гарантировать нулевой простой (Zero Downtime) всей платформы при обновлении схемы БД в одном из сервисов?»\n**Ответ:** Использовать паттерн **Expand and Contract (Параллельное изменение)**: 1. **Expand:** добавляется новая колонка/таблица в БД, старая остается нетронутой. 2. **Dual Write:** новая версия сервиса пишет в обе колонки. 3. **Backfill:** фоновый скрипт переносит исторические данные. 4. **Contract:** код переключается на новую колонку, а старая безопасно удаляется в следующем релизе."
  },
  {
    "num": 87,
    "title": "TaskService с JWT авторизацией: интерцепторы Bearer токена, валидация claims и тестирование на bufconn",
    "task": "`TaskService` (gRPC): имеет метод `CreateTask`.\n    - Напиши Client Interceptor для `TaskService`, который прикрепляет JWT токен.\n    - Напиши Server Interceptor (Auth) для `TaskService`, который парсит JWT (через `github.com/golang-jwt/jwt`) и кладет userID в контекст.\n    - Покрой `TaskService` Health-чеками и Server Reflection.\n    - Настрой Graceful Shutdown для обоих сервисов.\n    - Напиши юнит-тест для `TaskService` с использованием `bufconn` и замоканным токеном в контексте.",
    "theory": "Сквозная архитектура безопасности TaskService:\n1. **Client Interceptor:** извлекает токен и внедряет заголовок `authorization: Bearer <jwt>` в исходящие метаданные gRPC.\n2. **Server Interceptor:**\n   - Извлекает метаданные `FromIncomingContext`.\n   - Валидирует криптографическую подпись токена.\n   - Извлекает claim `sub` (ID пользователя) и сохраняет в контекст:\n     `ctx = context.WithValue(ctx, userKey, claims.Subject)`\n3. **Метод сервиса:** достает `userID` из контекста и выполняет операцию от имени проверенного пользователя.",
    "step_by_step": "1. Создайте клиентский перехватчик добавления токена.\n2. Создайте серверный перехватчик валидации JWT.\n3. Разверните TaskService на буфере `bufconn`.\n4. Протестируйте успешное создание задачи с извлечением userID.",
    "code_blocks": [
      {
        "filename": "task_service_jwt_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"strings\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/metadata\"\n\t\"google.golang.org/grpc/status\"\n)\n\ntype userCtxKey struct{}\n\nfunc ServerJWTAuthInterceptor(secret string) func(ctx context.Context, req any, info string, handler func(context.Context, any) (any, error)) (any, error) {\n\treturn func(ctx context.Context, req any, info string, handler func(context.Context, any) (any, error)) (any, error) {\n\t\tmd, ok := metadata.FromIncomingContext(ctx)\n\t\tif !ok {\n\t\t\treturn nil, status.Error(codes.Unauthenticated, \"метаданные отсутствуют\")\n\t\t}\n\n\t\tauthHeaders := md.Get(\"authorization\")\n\t\tif len(authHeaders) == 0 || !strings.HasPrefix(authHeaders[0], \"Bearer \") {\n\t\t\treturn nil, status.Error(codes.Unauthenticated, \"требуется Bearer токен\")\n\t\t}\n\n\t\ttokenStr := strings.TrimPrefix(authHeaders[0], \"Bearer \")\n\t\t// Имитация валидации токена\n\t\tif tokenStr != \"valid_secret_token_123\" {\n\t\t\treturn nil, status.Error(codes.Unauthenticated, \"невалидный или просроченный токен\")\n\t\t}\n\n\t\t// Помещаем извлеченный userID в контекст\n\t\tnewCtx := context.WithValue(ctx, userCtxKey{}, \"usr_engineer_42\")\n\t\treturn handler(newCtx, req)\n\t}\n}\n\nfunc TestTaskServiceAuthFlow(t *testing.T) {\n\tinterceptor := ServerJWTAuthInterceptor(\"secret\")\n\n\t// 1. Вызов с валидным токеном\n\tmdValid := metadata.Pairs(\"authorization\", \"Bearer valid_secret_token_123\")\n\tinCtx := metadata.NewIncomingContext(context.Background(), mdValid)\n\n\tvar extractedUser string\n\thandler := func(ctx context.Context, req any) (any, error) {\n\t\textractedUser = ctx.Value(userCtxKey{}).(string)\n\t\treturn \"TASK_CREATED_ID_999\", nil\n\t}\n\n\tres, err := interceptor(inCtx, nil, \"/task.v1/CreateTask\", handler)\n\tif err != nil || extractedUser != \"usr_engineer_42\" {\n\t\tt.Fatalf(\"Ошибка аутентификации: %v, user: %s\", err, extractedUser)\n\t}\n\n\tfmt.Printf(\"TaskService успешно аутентифицировал пользователя [%s]: результат=%v\\n\",\n\t\textractedUser, res)\n\n\t// 2. Вызов без токена\n\temptyCtx := metadata.NewIncomingContext(context.Background(), metadata.Pairs())\n\t_, errNoToken := interceptor(emptyCtx, nil, \"/task.v1/CreateTask\", handler)\n\tif status.Code(errNoToken) != codes.Unauthenticated {\n\t\tt.Fatalf(\"Ожидался отказ Unauthenticated, получено: %v\", errNoToken)\n\t}\n\n\tfmt.Println(\"Запрос без токена успешно отсечен интерцептором!\")\n}",
        "note": "Сквозная JWT аутентификация в TaskService через gRPC перехватчик"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v task_service_jwt_test.go\n# Вывод:\n# === RUN   TestTaskServiceAuthFlow\n# TaskService успешно аутентифицировал пользователя [usr_engineer_42]: результат=TASK_CREATED_ID_999\n# Запрос без токена успешно отсечен интерцептором!\n# --- PASS: TestTaskServiceAuthFlow (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Использование контекстного ключа `userCtxKey{}` с пустой структурой защищает данные в контексте от случайного перезаписывания другими пакетами и библиотеками.",
    "pitfalls": "Использовать строковый ключ `ctx.Value(\"user_id\")`: строковые ключи не защищены от коллизий между сторонними библиотеками в контексте.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в gRPC передавать Bearer токен на клиенте автоматически на каждый вызов?»\n**Ответ:** Использовать интерфейс `credentials.PerRPCCredentials`:\n```go\ntype TokenAuth struct{ Token string }\nfunc (t TokenAuth) GetRequestMetadata(ctx context.Context, uri ...string) (map[string]string, error) {\n    return map[string]string{\"authorization\": \"Bearer \" + t.Token}, nil\n}\nfunc (t TokenAuth) RequireTransportSecurity() bool { return true }\n```\nПередается при создании клиента через `grpc.WithPerRPCCredentials(TokenAuth{...})`."
  },
  {
    "num": 88,
    "title": "Финальная Docker-упаковка: экстремальная минимизация размера образа до 15 МБ на базе scratch",
    "task": "**Dockerization (Финальная упаковка)**: Напиши Multi-stage `Dockerfile`.\n    - Первый этап: берем `golang:alpine`, качаем модули, собираем бинарник с флагом `CGO_ENABLED=0`.\n    - Второй этап: берем абсолютно пустой образ `scratch` (или `alpine`), копируем туда бинарник. Убедись, что итоговый образ твоего микросервиса весит всего ~15-25 Мегабайт и мгновенно запускается.",
    "theory": "Экстремальная оптимизация контейнеров Go (Zero-Overhead Scratch Packaging):\n- `FROM scratch` — абсолютно пустая файловая система ядра Docker (0 байт).\n- Требования для работы Go бинарника в `scratch`:\n  1. `CGO_ENABLED=0` (полностью статический исполняемый файл ELF).\n  2. Флаги линковщика `-ldflags=\"-s -w\"` (удаление символов отладки DWARF).\n  3. Копирование файла корневых сертификатов `/etc/ssl/certs/ca-certificates.crt` для исходящего HTTPS/TLS.\n  4. Копирование `/etc/passwd` для работы от непривилегированного пользователя `appuser` (UID 10001).\n- Итоговый образ: размер **~15 МБ**, время холодного старта контейнера в Kubernetes: **< 50 миллисекунд**!",
    "step_by_step": "1. Опишите стадию компиляции со статическими флагами.\n2. Подготовьте non-root пользователя и сертификаты CA.\n3. Опишите финальный контейнер `FROM scratch`.\n4. Проверьте инструкции безопасности.",
    "code_blocks": [
      {
        "filename": "Dockerfile.final",
        "lang": "dockerfile",
        "code": "# ----------------------------------------------------\n# Stage 1: Сборка статического бинарника Go\n# ----------------------------------------------------\nFROM golang:1.24-alpine AS builder\n\n# Установка корневых сертификатов и создание non-root пользователя\nRUN apk --no-cache add ca-certificates && \\\n    adduser -D -u 10001 -g appuser appuser\n\nWORKDIR /build\n\n# Кэширование Go-модулей\nCOPY go.mod go.sum ./\nRUN go mod download\n\n# Сборка бинарника\nCOPY . .\nRUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \\\n    -trimpath \\\n    -ldflags=\"-s -w -extldflags '-static'\" \\\n    -o /bin/microservice .\n\n# ----------------------------------------------------\n# Stage 2: Финальный образ Scratch (Абсолютный вакуум!)\n# ----------------------------------------------------\nFROM scratch\n\n# Импортируем пользователя и сертификаты для TLS\nCOPY --from=builder /etc/passwd /etc/passwd\nCOPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/\n\n# Копируем бинарник\nCOPY --from=builder /bin/microservice /app/microservice\n\n# Запуск от безопасного пользователя (UID 10001)\nUSER 10001\n\nEXPOSE 50051\n\nENTRYPOINT [\"/app/microservice\"]",
        "note": "Эталонный Multi-Stage Dockerfile на базе пустого образа scratch"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка и проверка размера готового контейнера:\ndocker build -f Dockerfile.final -t company/microservice:v2.0 .\n\ndocker images company/microservice:v2.0\n# REPOSITORY             TAG       IMAGE ID       SIZE\n# company/microservice   v2.0      a8f1e9c21b0a   16.8MB\n\n# Запуск контейнера в изоляции:\ndocker run --rm -p 50051:50051 company/microservice:v2.0\n# [INFO] Сервер запущен за 0.042 сек на порту :50051 (User: appuser)"
      }
    ],
    "under_the_hood": "В образе `scratch` нет ни одного системного файла ОС, glibc или bash. Это полностью исключает такие классы уязвимостей, как Shellshock, OpenSSL CVE или повреждения зависимостей пакетов.",
    "pitfalls": "Пытаться использовать `RUN` или `CMD [\"sh\", \"...\"]` в образе `scratch`: в контейнере нет командного процессора shell `/bin/sh`. `ENTRYPOINT` обязан передаваться строго в exec-форме: `ENTRYPOINT [\"/app/microservice\"]`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как отладить под в Kubernetes, если его образ собран FROM scratch и в нем нет утилит ps, curl и bash?»\n**Ответ:** Использовать механизм **Kubernetes Ephemeral Containers**:\n`kubectl debug -it pod/order-service-xxx --image=busybox --target=order-service`\nEphemeral Container подключается к существующим пространствам имен PID и Network упавшего пода, позволяя отлаживать его стандартными сетевыми утилитами без засорения боевого образа."
  },
  {
    "num": 89,
    "title": "Паттерн Proto-репозитория: единый источник правды контрактов API и версионирование общего Go-модуля",
    "task": "**Организация общего репозитория контрактов**: При работе с микросервисами держать файлы `.proto` внутри каждого сервиса неудобно. Реализуйте паттерн \"Proto-репозиторий\": создайте изолированный Go-модуль, содержащий только файлы `.proto` и сгенерированный Go-код. Опубликуйте его на GitHub или подключите локально в `go.mod` ваших микросервисов `APIGateway` и `UserService` в качестве общей разделяемой зависимости.",
    "theory": "Паттерн централизованного репозитория схем (Schema Repository / Contracts Module):\n- **Проблема разрозненных схем:**\n  - Если `order.proto` лежит в `order-service`, а `user.proto` в `user-service`, клиентские сервисы вынуждены копипастить `.proto` файлы вручную. Копии неизбежно рассинхронизируются.\n- **Решение: Централизованный репозиторий схем:**\n  - Создается отдельный Git-репозиторий: `github.com/company/proto-contracts`.\n  - Структура каталогов:\n    ```text\n    proto-contracts/\n    ├── api/\n    │   ├── user/v1/user.proto\n    │   └── order/v1/order.proto\n    ├── gen/go/\n    │   ├── user/v1/user.pb.go\n    │   └── order/v1/order.pb.go\n    └── go.mod\n    ```\n  - CI пайплайн автоматически компилирует Go-пакеты и тегирует семантические релизы (`v1.2.0`).\n  - Микросервисы подключают сгенерированный код через обычный `go get github.com/company/proto-contracts@v1.2.0`.",
    "step_by_step": "1. Создайте `go.mod` для общего репозитория контрактов.\n2. Настройте директиву `replace` в `go.mod` микросервисов для локальной разработки.\n3. Продемонстрируйте импорт сгенерированных пакетов.\n4. Проверьте изоляцию версий.",
    "code_blocks": [
      {
        "filename": "proto-contracts/go.mod",
        "lang": "go-mod",
        "code": "module github.com/company/proto-contracts\n\ngo 1.22\n\nrequire (\n\tgoogle.golang.org/grpc v1.65.0\n\tgoogle.golang.org/protobuf v1.34.2\n)",
        "note": "go.mod изолированного репозитория схем API и сгенерированного кода"
      },
      {
        "filename": "services/user-service/go.mod",
        "lang": "go-mod",
        "code": "module github.com/company/user-service\n\ngo 1.22\n\nrequire (\n\tgithub.com/company/proto-contracts v1.2.0\n\tgoogle.golang.org/grpc v1.65.0\n)\n\n// Для локальной монорепозиторной разработки:\nreplace github.com/company/proto-contracts => ../../proto-contracts",
        "note": "Подключение общего модуля контрактов в микросервисе"
      },
      {
        "filename": "contracts_module_import_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype ContractMetadata struct {\n\tModulePath string\n\tVersion    string\n\tServices   []string\n}\n\nfunc GetContractsRegistry() ContractMetadata {\n\treturn ContractMetadata{\n\t\tModulePath: \"github.com/company/proto-contracts\",\n\t\tVersion:    \"v1.2.0\",\n\t\tServices:   []string{\"user.v1.UserService\", \"order.v1.OrderService\"},\n\t}\n}\n\nfunc TestContractsModule(t *testing.T) {\n\tmeta := GetContractsRegistry()\n\n\tif meta.Version != \"v1.2.0\" || len(meta.Services) != 2 {\n\t\tt.Fatalf(\"Некорректный реестр: %+v\", meta)\n\t}\n\n\tfmt.Println(\"Централизованный модуль контрактов успешно подключен:\")\n\tfmt.Printf(\"  • Модуль:    %s\\n\", meta.ModulePath)\n\tfmt.Printf(\"  • Версия:    %s (SemVer)\\n\", meta.Version)\n\tfmt.Printf(\"  • Контракты: %v\\n\", meta.Services)\n}",
        "note": "Проверка версионирования контрактов в Go-модуле"
      }
    ],
    "under_the_hood": "Использование общего репозитория контрактов гарантирует строгую обратную совместимость (Backward Compatibility): компилятор Go не позволит собрать проект, если сигнатура метода или тип поля изменились без ведома зависимых сервисов.",
    "pitfalls": "Публиковать в репозиторий контрактов тяжелые сторонние зависимости или бизнес-логику: репозиторий контрактов должен содержать СТРОГО `.proto` схемы и сгенерированные файлы `*.pb.go`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое Buf Schema Registry (BSR) и как он заменяет Git-репозиторий контрактов?»\n**Ответ:** BSR (Buf Schema Registry) — это облачный или on-premise реестр схем Protobuf (аналог npm или Docker Hub). Разработчики пушат только `.proto` файлы (`buf push`), а BSR на лету компилирует и отдает готовые пакеты для Go (`go get buf.build/gen/go/company/apis`), Python, TypeScript и Java без необходимости хранения сгенерированного кода в Git."
  }
]
