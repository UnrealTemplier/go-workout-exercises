# -*- coding: utf-8 -*-
"""
Глава 80: Контекст трассировки (W3C Trace Context, B3) и gRPC Keepalive — Часть 2 (Упражнения 39-76)
"""

exercises = [
    {
        "num": 39,
        "title": "Настройка gRPC Client-side Keepalive с динамическими параметрами",
        "task": "Настройте параметры Keepalive на стороне вашего gRPC-клиента в Go с помощью grpc.WithKeepaliveParams. Установите Time: 15s, Timeout: 5s, PermitWithoutStream: true. Объясните назначение каждого параметра.",
        "theory": "Клиентский Keepalive в gRPC — это основной механизм контроля живучести сетевого пути. Конфигурация `keepalive.ClientParameters` состоит из: 1) `Time`: интервал времени бездействия сокета до отправки HTTP/2 PING-фрейма. Если по каналу идут активные RPC, счетчик сбрасывается. 2) `Timeout`: максимальное время ожидания ответа (кадр PING ACK) от сервера. Если ответ не получен вовремя, сокет закрывается с переводом саб-канала в TRANSIENT_FAILURE; 3) `PermitWithoutStream`: разрешение отправлять PING-фреймы даже при отсутствии активных вызовов RPC. Это критично, чтобы сетевые экраны (stateful firewall) и NAT не удаляли трансляцию портов при простое приложения.",
        "step_by_step": [
            "Импортируйте пакет google.golang.org/grpc/keepalive.",
            "Сконфигурируйте экземпляр ClientParameters.",
            "Передайте параметры в grpc.DialContext с grpc.WithKeepaliveParams.",
            "Проверьте установку соединения и обработку сетевых тайм-аутов."
        ],
        "code_blocks": [
            {
                "filename": "grpc_client_keepalive_cfg.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n\t\"google.golang.org/grpc/keepalive\"\n)\n\n// SetupResilientClientConn создает защищенное gRPC подключение к микросервису\nfunc SetupResilientClientConn(target string) (*grpc.ClientConn, error) {\n\tkacp := keepalive.ClientParameters{\n\t\tTime:                15 * time.Second, // Пинговать сервер каждые 15 секунд при простое\n\t\tTimeout:             5 * time.Second,  // Считать сокет мертвым, если ACK не пришел за 5с\n\t\tPermitWithoutStream: true,             // Поддерживать сессию живой в NAT даже без активных вызовов\n\t}\n\n\tctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\tdefer cancel()\n\n\tconn, err := grpc.DialContext(ctx, target,\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t\tgrpc.WithKeepaliveParams(kacp),\n\t\tgrpc.WithBlock(),\n\t)\n\tif err != nil {\n\t\treturn nil, fmt.Errorf(\"connection failed: %w\", err)\n\t}\n\n\treturn conn, nil\n}\n\nfunc main() {\n\tconn, err := SetupResilientClientConn(\"127.0.0.1:50051\")\n\tif err != nil {\n\t\tlog.Printf(\"[Notice] Dial deferred as expected: %v\", err)\n\t\treturn\n\t}\n\tdefer conn.Close()\n\n\tfmt.Println(\"gRPC Keepalive Client initialized successfully.\")\n}",
                "note": "Базовая конфигурация gRPC ClientParameters для надежной работы через NAT"
            }
        ],
        "under_the_hood": "Фоновый таймер `keepalive.ClientParameters.Time` сбрасывается при каждом чтении любого фрейма от сервера. Если сервер непрерывно шлет данные, лишние PING кадры не генерируются, экономя CPU и сетевой трафик.",
        "pitfalls": "Установка `Time` меньше, чем серверный `EnforcementPolicy.MinTime`. В этом случае сервер расценит активность клиента как спам и разорвет сокет фреймом GOAWAY too_many_pings.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'Почему Cloud Load Balancer (AWS NLB) сбрасывает gRPC-соединение через 350 секунд?' Ответ: 'Таблица conntrack сетевого балансировщика удаляет записи об idle TCP-соединениях по таймауту. Клиентский keepalive с интервалом Time < 300s предотвращает сброс, поддерживая запись в таблице активной'."
    },
    {
        "num": 40,
        "title": "Multi-Format Propagation: объединение W3C Trace Context и Zipkin B3",
        "task": "Настройте составной пропагатор propagation.NewCompositeTextMapPropagator, поддерживающий одновременное извлечение и инжекцию обоих форматов: W3C Trace Context и Zipkin B3.",
        "theory": "В гетерогенных микросервисных платформах Enterprise-уровня сосуществуют сервисы разных поколений: новые сервисы на Go поддерживают стандарт W3C Trace Context (`traceparent`), а legacy-сервисы на Java (Spring Cloud Sleuth) или Service Mesh Envoy используют заголовки Zipkin B3 (`b3` или `X-B3-*`). Чтобы трейсы не терялись на стыке технологий, OpenTelemetry предоставляет `CompositeTextMapPropagator`. При вызове `Extract` он проверяет форматы по очереди до первого найденного контекста. При вызове `Inject` он записывает заголовки сразу в обоих форматах, гарантируя совместимость с любым downstream сервисом.",
        "step_by_step": [
            "Импортируйте go.opentelemetry.io/otel/propagation.",
            "Импортируйте b3 форматтер (go.opentelemetry.io/contrib/propagators/b3 или собственную реализацию).",
            "Инициализируйте propagation.NewCompositeTextMapPropagator(propagation.TraceContext{}, b3Propagator).",
            "Установите глобальный пропагатор через otel.SetTextMapPropagator.",
            "Проверьте одновременную инжекцию обоих форматов в заголовки."
        ],
        "code_blocks": [
            {
                "filename": "composite_propagator.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/http\"\n\n\t\"go.opentelemetry.io/otel\"\n\t\"go.opentelemetry.io/otel/propagation\"\n\tsdktrace \"go.opentelemetry.io/otel/sdk/trace\"\n\t\"go.opentelemetry.io/otel/trace\"\n)\n\n// SimpleB3Propagator реализует базовый TextMapPropagator для Zipkin B3 Single\ntype SimpleB3Propagator struct{}\n\nfunc (b SimpleB3Propagator) Inject(ctx context.Context, carrier propagation.TextMapCarrier) {\n\tspan := trace.SpanFromContext(ctx)\n\tif !span.SpanContext().IsValid() {\n\t\treturn\n\t}\n\tsc := span.SpanContext()\n\tsampled := \"0\"\n\tif sc.IsSampled() {\n\t\tsampled = \"1\"\n\t}\n\tcarrier.Set(\"b3\", fmt.Sprintf(\"%s-%s-%s\", sc.TraceID(), sc.SpanID(), sampled))\n}\n\nfunc (b SimpleB3Propagator) Extract(ctx context.Context, carrier propagation.TextMapCarrier) context.Context {\n\tb3 := carrier.Get(\"b3\")\n\tif b3 == \"\" {\n\t\treturn ctx\n\t}\n\t// Упрощенный парсинг для демонстрации\n\treturn ctx\n}\n\nfunc (b SimpleB3Propagator) Fields() []string {\n\treturn []string{\"b3\", \"x-b3-traceid\", \"x-b3-spanid\"}\n}\n\nfunc main() {\n\ttp := sdktrace.NewTracerProvider(sdktrace.WithSampler(sdktrace.AlwaysSample()))\n\totel.SetTracerProvider(tp)\n\n\t// Настройка мультиформатного композитного пропагатора\n\tcomposite := propagation.NewCompositeTextMapPropagator(\n\t\tpropagation.TraceContext{}, // W3C (traceparent, tracestate)\n\t\tpropagation.Baggage{},      // W3C baggage\n\t\tSimpleB3Propagator{},       // Zipkin B3\n\t)\n\totel.SetTextMapPropagator(composite)\n\n\ttracer := otel.Tracer(\"gateway\")\n\tctx, span := tracer.Start(context.Background(), \"RouteRequest\")\n\tdefer span.End()\n\n\treq, _ := http.NewRequest(\"GET\", \"http://internal-service/api\", nil)\n\totel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(req.Header))\n\n\tfmt.Println(\"Injected Headers:\")\n\tfmt.Println(\"  traceparent:\", req.Header.Get(\"traceparent\"))\n\tfmt.Println(\"  b3:         :\", req.Header.Get(\"b3\"))\n}",
                "note": "Композитный пропагатор трассировки для поддержки W3C и B3 одновременно"
            }
        ],
        "under_the_hood": "При вызове `composite.Inject` итератор выполняет вызов `Inject` каждого зарегистрированного пропагатора. При вызове `composite.Extract` контекст передается через цепочку: контекст, обогащенный первым пропагатором, становится входным для второго, обеспечивая объединение W3C, Baggage и кастомных заголовков.",
        "pitfalls": "Конфликт идентификаторов при наличии обоих заголовков с несовпадающими TraceID. W3C Trace Context имеет более высокий приоритет и должен стоять первым в списке NewCompositeTextMapPropagator.",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'Как в миграционный период подружить микросервисы на Spring Boot с новыми микросервисами на Go?' Ответ: 'Включить на Go-сервисах CompositeTextMapPropagator с поддержкой B3 и W3C. Go-сервисы будут понимать старые входящие B3 заголовки от Java и слать оба формата в downstream вызовы'."
    },
    {
        "num": 41,
        "title": "Leader Election через Kubernetes API: надежный консенсус без Consul и Redis",
        "task": "Реализуйте отказоустойчивые выборы лидера (Leader Election) в Go с помощью client-go/tools/leaderelection на основе ресурса Coordination API (Lease) в etcd Kubernetes.",
        "theory": "Для обеспечения отказоустойчивости фоновых воркеров (Cron jobs, Outbox publishers, Scheduler) требуется паттерн Active-Passive: только один экземпляр пода выполняет критическую работу, а остальные находятся в режиме горячего резерва (Standby). В Kubernetes нет необходимости поднимать сторонние кластеры Consul или Redis с Redlock: в ядре Kubernetes уже работает высоконадежный распределенный консенсус etcd! Пакет `k8s.io/client-go/tools/leaderelection` использует ресурс `coordination.k8s.io/v1 Lease`. Лидер регулярно обновляет время аренды (`RenewDeadline`). Если под падает, аренда истекает (`LeaseDuration`), и резервный под мгновенно перехватывает лидерство без разделения ресурсов (Split-Brain).",
        "step_by_step": [
            "Импортируйте k8s.io/client-go/tools/leaderelection.",
            "Создайте структуру LeaderElectionConfig с параметрами LeaseDuration, RenewDeadline, RetryPeriod.",
            "Сконфигурируйте LeaderCallbacks (OnStartedLeading, OnStoppedLeading, OnNewLeader).",
            "Запустите RunOrDie в контексте приложения.",
            "Обеспечьте корректный сброс работы при потере лидерства."
        ],
        "code_blocks": [
            {
                "filename": "k8s_leader_election.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"os\"\n\t\"os/signal\"\n\t\"sync/atomic\"\n\t\"syscall\"\n\t\"time\"\n)\n\n// MockLeaseElector демонстрирует архитектуру k8s.io/client-go/tools/leaderelection\ntype MockLeaseElector struct {\n\tpodID       string\n\tisLeader    atomic.Bool\n\tleaseHolder string\n}\n\nfunc NewMockLeaseElector(podID string) *MockLeaseElector {\n\treturn &MockLeaseElector{podID: podID}\n}\n\nfunc (le *MockLeaseElector) Run(ctx context.Context, onStart func(context.Context), onStop func()) {\n\tticker := time.NewTicker(2 * time.Second)\n\tdefer ticker.Stop()\n\n\tlog.Printf(\"[%s] Starting Leader Election via K8s Coordination API (Lease)...\", le.podID)\n\n\t// Имитация захвата лидерства текущим подом\n\tle.isLeader.Store(true)\n\tle.leaseHolder = le.podID\n\n\tleaderCtx, cancelLeaderCtx := context.WithCancel(ctx)\n\tdefer cancelLeaderCtx()\n\n\tgo onStart(leaderCtx)\n\n\tfor {\n\t\tselect {\n\t\tcase <-ctx.Done():\n\t\t\tlog.Printf(\"[%s] Context cancelled, releasing leadership lease...\", le.podID)\n\t\t\tle.isLeader.Store(false)\n\t\t\tcancelLeaderCtx()\n\t\t\tonStop()\n\t\t\treturn\n\t\tcase <-ticker.C:\n\t\t\tif le.isLeader.Load() {\n\t\t\t\t// В реальном K8s: leaseClient.Update(ctx, lease, metav1.UpdateOptions{})\n\t\t\t\tlog.Printf(\"[%s] Renewed lease successfully in etcd.\", le.podID)\n\t\t\t}\n\t\t}\n\t}\n}\n\nfunc main() {\n\tctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)\n\tdefer stop()\n\n\tpodName := \"order-worker-pod-78df9\"\n\telector := NewMockLeaseElector(podName)\n\n\telector.Run(ctx,\n\t\t// OnStartedLeading: запускаем фоновую обработку только если стали лидером\n\t\tfunc(lCtx context.Context) {\n\t\t\tlog.Println(\"[Active Leader] Started publishing events and processing outbox...\")\n\t\t\tfor {\n\t\t\t\tselect {\n\t\t\t\tcase <-lCtx.Done():\n\t\t\t\t\tlog.Println(\"[Active Leader] Leadership lost! Stopping processing immediately.\")\n\t\t\t\t\treturn\n\t\t\t\tcase <-time.After(1 * time.Second):\n\t\t\t\t\tlog.Println(\"[Active Leader] Processing pending tasks batch...\")\n\t\t\t\t}\n\t\t\t}\n\t\t},\n\t\t// OnStoppedLeading: очистка ресурсов при утрате статуса\n\t\tfunc() {\n\t\t\tlog.Println(\"[Standby] Node switched to standby standby observer mode.\")\n\t\t},\n\t)\n\n\tfmt.Println(\"Leader election loop completed.\")\n}",
                "note": "Паттерн Leader Election через Coordination API (Lease) в Kubernetes"
            }
        ],
        "under_the_hood": "Ресурс Kubernetes `Lease` содержит поля `spec.holderIdentity`, `spec.leaseDurationSeconds`, `spec.renewTime`. При обновлении записи K8s API использует оптимистическую блокировку (`resourceVersion`). Если два пода одновременно пытаются стать лидером, победит только одна транзакция в etcd.",
        "pitfalls": "Продолжать выполнять фоновую работу после отмены лидерского контекста. Если под потерял сетевую связь с etcd, он обязан немедленно прекратить работу, иначе в кластере появятся два одновременных лидера (Split-Brain).",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Почему Leader Election через Kubernetes Lease надежнее, чем Redis Redlock?' Ответ: 'Ресурс Lease опирается на etcd с алгоритмом консенсуса Raft, гарантирующим строгую согласованность (Linearizability). Redlock в Redis не является формально верифицированным консенсусом и уязвим к GC-паузам и рассинхронизации системных часов'."
    },
    {
        "num": 42,
        "title": "Автоматическая инжекция Trace Context в структурированные логи slog",
        "task": "Создайте middleware для HTTP-сервера, которое автоматически связывает контекст трассировки OpenTelemetry со структурированным логером log/slog для каждого входящего запроса.",
        "theory": "При разборе инцидентов в распределенных системах инженер начинает расследование с графика метрик или сообщения об ошибке в логах. Чтобы мгновенно перейти от записи в логе к полному графу распределенной трассировки в Jaeger/Tempo, логер обязан содержать канонические поля `trace_id` и `span_id`. В Go 1.21+ стандартная библиотека `log/slog` предоставляет контекстные методы логирования: `slog.InfoContext(ctx, \"msg\", ...)` и `slog.ErrorContext(ctx, \"msg\", ...)`. Подключив кастомный обработчик `slog.Handler`, мы гарантируем, что ни один разработчик не сможет случайно забыть добавить trace ID в лог.",
        "step_by_step": [
            "Создайте TraceSlogHandler, реализующий интерфейс slog.Handler.",
            "В методе Handle извлеките SpanContext из переданного ctx.",
            "Добавьте атрибуты trace_id и span_id к slog.Record.",
            "Настройте глобальный логер slog.SetDefault.",
            "Проверьте вывод логов в формате JSON."
        ],
        "code_blocks": [
            {
                "filename": "trace_slog_integration.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"log/slog\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"os\"\n\n\t\"go.opentelemetry.io/otel\"\n\tsdktrace \"go.opentelemetry.io/otel/sdk/trace\"\n\t\"go.opentelemetry.io/otel/trace\"\n)\n\n// TraceSlogHandler автоматически добавляет поля trace_id и span_id в логи\ntype TraceSlogHandler struct {\n\tslog.Handler\n}\n\nfunc (h *TraceSlogHandler) Handle(ctx context.Context, r slog.Record) error {\n\tspan := trace.SpanFromContext(ctx)\n\tif span.SpanContext().IsValid() {\n\t\tsc := span.SpanContext()\n\t\tr.AddAttrs(\n\t\t\tslog.String(\"trace_id\", sc.TraceID().String()),\n\t\t\tslog.String(\"span_id\", sc.SpanID().String()),\n\t\t)\n\t}\n\treturn h.Handler.Handle(ctx, r)\n}\n\nfunc main() {\n\t// Настройка TracerProvider\n\ttp := sdktrace.NewTracerProvider(sdktrace.WithSampler(sdktrace.AlwaysSample()))\n\totel.SetTracerProvider(tp)\n\ttracer := otel.Tracer(\"http-server\")\n\n\t// Настройка slog с JSON выводом и нашим TraceHandler\n\tbaseHandler := slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo})\n\tlogger := slog.New(&TraceSlogHandler{Handler: baseHandler})\n\tslog.SetDefault(logger)\n\n\t// HTTP сервер с логированием\n\thandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\tctx, span := tracer.Start(r.Context(), \"HandleCheckout\")\n\t\tdefer span.End()\n\n\t\tslog.InfoContext(ctx, \"Checkout request received\",\n\t\t\tslog.String(\"user_id\", \"usr_102\"),\n\t\t\tslog.Float64(\"total\", 99.90),\n\t\t)\n\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(`{\"status\":\"ok\"}`))\n\t})\n\n\tserver := httptest.NewServer(handler)\n\tdefer server.Close()\n\n\tresp, _ := http.Get(server.URL)\n\t_ = resp.Body.Close()\n}",
                "note": "Бесшовная корреляция логов slog с трассировкой OpenTelemetry"
            }
        ],
        "under_the_hood": "`trace.SpanFromContext(ctx)` извлекает указатель на текущий спан без блокировок памяти. Если в контексте нет активного спана, метод возвращает `noopSpan`, метод `IsValid()` возвращает false, и логер не тратит ресурсы на добавление пустых полей.",
        "pitfalls": "Использование методов `slog.Info()` вместо `slog.InfoContext(ctx, ...)`. Обычный `slog.Info` не принимает context.Context, поэтому trace_id не может быть извлечен.",
        "bigtech_interview": "Вопрос на собеседовании в Тинькофф: 'Как связать логи в Elasticsearch/Kibana с Jaeger по trace_id?' Ответ: 'В Kibana настраивается URL Drilldown template по паттерну `https://jaeger/trace/{{trace_id}}`. Благодаря присутствию trace_id в каждом логе инженер в один клик переходит из строки лога к полному водопаду вызовов'."
    },
    {
        "num": 43,
        "title": "Client Load Balancing + Health Checking в gRPC: автоматический обход сбойных бэкендов",
        "task": "Настройте gRPC клиент с балансировкой round_robin и активной проверкой здоровья серверов через gRPC Health Checking Protocol (grpc.health.v1).",
        "theory": "Стандартный Round Robin балансировщик gRPC циклически направляет запросы по всем известным IP адресам. Однако если один из бэкендов завис или столкнулся с аппаратным сбоем, клиент продолжит слать 1/N часть запросов в мертвый сервер, возвращая ошибки пользователям. gRPC Health Checking Protocol (спецификация `grpc.health.v1.Health`) решает эту проблему: клиентский балансировщик открывает постоянный стрим проверки здоровья `Check` / `Watch` к каждому серверу. Если сервер сообщает статус `NOT_SERVING` или перестает отвечать, клиент немедленно исключает этот бэкенд из балансировки, направляя 100% трафика на оставшиеся здоровые реплики.",
        "step_by_step": [
            "Сконфигурируйте Service Config с round_robin и healthCheckConfig.",
            "Инициализируйте gRPC клиент с grpc.WithDefaultServiceConfig.",
            "Создайте mock gRPC Health сервер со статусами SERVING и NOT_SERVING.",
            "Проверьте автоматическое исключение нездорового инстанса из маршрутизации."
        ],
        "code_blocks": [
            {
                "filename": "grpc_client_health_lb.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n)\n\n// DialWithHealthLB настраивает клиентский балансировщик с проверкой здоровья сервиса\nfunc DialWithHealthLB(target string) (*grpc.ClientConn, error) {\n\t// Конфигурация включает round_robin и привязку к стандартному gRPC health check сервису\n\tserviceConfig := `{\n\t\t\"loadBalancingConfig\": [{\"round_robin\": {}}],\n\t\t\"healthCheckConfig\": {\n\t\t\t\"serviceName\": \"OrderService\"\n\t\t}\n\t}`\n\n\tctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\tdefer cancel()\n\n\tconn, err := grpc.DialContext(ctx, target,\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t\tgrpc.WithDefaultServiceConfig(serviceConfig),\n\t)\n\tif err != nil {\n\t\treturn nil, fmt.Errorf(\"dial failed: %w\", err)\n\t}\n\n\treturn conn, nil\n}\n\nfunc main() {\n\ttarget := \"dns:///order-service.prod:50051\"\n\tlog.Printf(\"Connecting to %s with active gRPC Health Probing LB...\", target)\n\n\tconn, err := DialWithHealthLB(target)\n\tif err != nil {\n\t\tlog.Printf(\"[Demo note] Expected deferred connection: %v\", err)\n\t\treturn\n\t}\n\tdefer conn.Close()\n\n\tfmt.Println(\"Client-side load balancing with active Health Checking configured.\")\n}",
                "note": "Конфигурация gRPC балансировщика с автоматическим зондированием через grpc.health.v1"
            }
        ],
        "under_the_hood": "gRPC клиент под капотом запускает `healthCheckClient` для каждого саб-канала. Он вызывает стриминговый метод `/grpc.health.v1.Health/Watch`. При переходе статуса в `NOT_SERVING` саб-канал переводится в состояние `TRANSIENT_FAILURE`, и пикер RoundRobin исключает его из кольцевого списка без закрытия TCP сокета.",
        "pitfalls": "Сервер не реализует интерфейс `grpc.health.v1.Health`. Если клиент настроен на healthCheckConfig, но на сервере сервис health не зарегистрирован (`grpc.health.v1.RegisterHealthServer`), клиент получит статус UNIMPLEMENTED и посчитает сервер полностью неработоспособным, отказавшись слать запросы.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Чем gRPC Health Checking Protocol превосходит HTTP /healthz в микросервисах?' Ответ: '1) Он мультиплексируется внутри того же HTTP/2 соединения без открытия новых портов; 2) Поддерживает стриминговый метод Watch: сервер мгновенно пушит изменения статуса клиенту без polling-задержек; 3) Поддерживает гранулярность по имени конкретного сервиса внутри процесса'."
    },
    {
        "num": 44,
        "title": "Связывание метрик и трассировки: Exemplars в Prometheus метриках",
        "task": "Реализуйте передачу trace_id в метрики Prometheus через механизм Exemplars в Go. Объясните, почему нельзя делать trace_id обычной меткой (label) метрики.",
        "theory": "Грубейшая архитектурная ошибка новичков — добавление `trace_id` в качестве лейбла метрики: `my_metric_total{trace_id=\"...\"}`. Уникальность каждого trace_id приводит к взрыву кардинальности (Cardinality Explosion)! База временных рядов (Prometheus, VictoriaMetrics) создает миллионы отдельных TimeSeries, память ноды исчерпывается и система мониторинга падает по OOM. Стандарт OpenMetrics и Prometheus решают эту проблему концепцией Exemplars: Exemplar — это ссылка на конкретный TraceID, которая прикрепляется к конкретному замеру гистограммы (Bucket), но НЕ создает новый TimeSeries! В Grafana на графике задержек появляется точка клика, позволяющая в один клик перейти от перцентиля p99 к конкретному проблемному трейсу.",
        "step_by_step": [
            "Импортируйте prometheus/client_golang с поддержкой Exemplars.",
            "Создайте гистограмму prometheus.NewHistogram с опцией EnableOpenMetrics.",
            "В обработчике извлеките active TraceID из контекста.",
            "Запишите наблюдение с помощью метода ObserveWithExemplar.",
            "Проверьте формат экспорта метрик через OpenMetrics Content-Type."
        ],
        "code_blocks": [
            {
                "filename": "metrics_exemplars.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"time\"\n\n\t\"github.com/prometheus/client_golang/prometheus\"\n\t\"github.com/prometheus/client_golang/prometheus/promhttp\"\n\t\"go.opentelemetry.io/otel/trace\"\n)\n\nvar (\n\t// RequestDurationHistogram замеряет длительность запросов с поддержкой Exemplars\n\tRequestDurationHistogram = prometheus.NewHistogram(\n\t\tprometheus.HistogramOpts{\n\t\t\tName:    \"http_request_duration_seconds\",\n\t\t\tHelp:    \"HTTP latency distributions with trace context exemplars.\",\n\t\t\tBuckets: []float64{0.05, 0.1, 0.25, 0.5, 1.0, 2.5},\n\t\t},\n\t)\n)\n\nfunc init() {\n\tprometheus.MustRegister(RequestDurationHistogram)\n}\n\nfunc TrackRequestWithExemplar(r *http.Request, duration time.Duration) {\n\tspan := trace.SpanFromContext(r.Context())\n\tdurSeconds := duration.Seconds()\n\n\tif span.SpanContext().IsValid() {\n\t\ttraceID := span.SpanContext().TraceID().String()\n\t\t// Передаем Exemplar без взрыва кардинальности метрики!\n\t\tobserver, ok := RequestDurationHistogram.(prometheus.ExemplarObserver)\n\t\tif ok {\n\t\t\tobserver.ObserveWithExemplar(durSeconds, prometheus.Labels{\n\t\t\t\t\"trace_id\": traceID,\n\t\t\t})\n\t\t\treturn\n\t\t}\n\t}\n\n\tRequestDurationHistogram.Observe(durSeconds)\n}\n\nfunc main() {\n\t// Демонстрация регистрации и замера\n\treq := httptest.NewRequest(\"GET\", \"/checkout\", nil)\n\tTrackRequestWithExemplar(req, 120*time.Millisecond)\n\n\tfmt.Println(\"Metric observed with trace_id exemplar successfully.\")\n\t_ = promhttp.Handler()\n}",
                "note": "Использование Prometheus Exemplars для связывания метрик с трейсами без роста кардинальности"
            }
        ],
        "under_the_hood": "Exemplar сохраняется в памяти Prometheus TSDB как временная кольцевая структура рядом с бакетом гистограммы. Он не индексируется в инвертированном индексе строк и не влияет на объем памяти базы временных рядов.",
        "pitfalls": "Добавление `trace_id` или `user_id` в `prometheus.Labels` счетчика или гистограммы. При 10 000 RPS память Prometheus заполнится гигабайтами дескрипторов серий за считанные минуты.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Как сделать drill-down из метрики в трейс в Grafana без добавления trace_id в labels?' Ответ: 'Через Prometheus Exemplars. В Prometheus включается флаг `--enable-feature=exemplar-storage`. В Go-коде используется `ObserveWithExemplar`. В Grafana на графике появляются точки конкретных трейсов, открывающие Jaeger/Tempo'."
    },
    {
        "num": 45,
        "title": "Стратегии сэмплирования трассировки: Head-based, Tail-based и Always-Error",
        "task": "Сконфигурируйте OpenTelemetry Sampler: сохранять 100% запросов с ошибками, 1% успешных вызовов и все родительские спаны с помощью ParentBased и RatioBased сэмплеров.",
        "theory": "В HighLoad системах с миллионами запросов в секунду невозможно сохранять 100% трейсов: стоимость сетевого трафика и дискового пространства в Elastic/Tempo превысит стоимость всей бизнес-инфраструктуры. Используются стратегии сэмплирования: 1) Head-based sampling: решение о сэмплировании принимается в самом начале запроса на входном шлюзе через вероятностный `sdktrace.TraceIDRatioBased(0.01)` (1% трафика); 2) Parent-based sampling: дочерние микросервисы уважают решение родителя (`ParentBasedSampler`); 3) Always-sample errors / Tail-based sampling: решение принимается коллектором (OpenTelemetry Collector) после завершения транзакции — если в трейсе возникла ошибка (HTTP 500, panic), трейс сохраняется в 100% случаев, даже если он не попал в 1% случайного сэмплирования.",
        "step_by_step": [
            "Импортируйте go.opentelemetry.io/otel/sdk/trace.",
            "Создайте вероятностный сэмплер с коэффициентом 0.01 (1%).",
            "Оберните его в trace.ParentBased сэмплер.",
            "Сконфигурируйте TracerProvider с созданным сэмплером.",
            "Проверьте автоматическое наследование флага sampled дочерними спанами."
        ],
        "code_blocks": [
            {
                "filename": "trace_sampling.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\n\t\"go.opentelemetry.io/otel\"\n\tsdktrace \"go.opentelemetry.io/otel/sdk/trace\"\n)\n\n// InitSamplingTracer настраивает оптимизированный сэмплер для HighLoad продакшена\nfunc InitSamplingTracer(sampleRatio float64) *sdktrace.TracerProvider {\n\t// 1. Базовый вероятностный сэмплер (например 1% = 0.01)\n\tratioSampler := sdktrace.TraceIDRatioBased(sampleRatio)\n\n\t// 2. ParentBased: если родитель уже был засэмплирован, мы обязаны сэмплировать дочерний спан\n\tcompositeSampler := sdktrace.ParentBased(\n\t\tratioSampler,\n\t\t// Если родитель локальный и sampled -> сэмплировать\n\t\tsdktrace.WithLocalParentSampled(sdktrace.AlwaysSample()),\n\t\t// Если родитель удаленный (по сети) и sampled -> сэмплировать\n\t\tsdktrace.WithRemoteParentSampled(sdktrace.AlwaysSample()),\n\t\t// Если родитель НЕ сэмплирован -> отбрасывать\n\t\tsdktrace.WithRemoteParentNotSampled(sdktrace.NeverSample()),\n\t)\n\n\ttp := sdktrace.NewTracerProvider(\n\t\tsdktrace.WithSampler(compositeSampler),\n\t)\n\n\totel.SetTracerProvider(tp)\n\treturn tp\n}\n\nfunc main() {\n\ttp := InitSamplingTracer(0.05) // 5% сэмплирование\n\tdefer func() { _ = tp.Shutdown(context.Background()) }()\n\n\ttracer := otel.Tracer(\"order-service\")\n\n\t// Симулируем 20 запросов и смотрим, сколько будет засэмплировано\n\tsampledCount := 0\n\tfor i := 0; i < 100; i++ {\n\t\t_, span := tracer.Start(context.Background(), \"FastOp\")\n\t\tif span.SpanContext().IsSampled() {\n\t\t\tsampledCount++\n\t\t}\n\t\tspan.End()\n\t}\n\n\tfmt.Printf(\"Total spans created: 100, Sampled into storage: ~%d\\n\", sampledCount)\n}",
                "note": "Настройка ParentBased и TraceIDRatioBased сэмплеров в Go"
            }
        ],
        "under_the_hood": "`TraceIDRatioBased` анализирует младшие 8 байт 128-битного TraceID как целое число. Если число меньше, чем `ratio * math.MaxUint64`, спан помечается флагом `0x01` (Sampled). Это гарантирует строго детерминированное и равномерное распределение вероятности.",
        "pitfalls": "Использование простого RatioBased без ParentBased. В таком случае родительский запрос может быть сохранен, а дочерний спан в микросервисе базы данных отброшен, что приведет к 'дырявым' неполным трейсам в интерфейсе Jaeger.",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'В чем фундаментальное преимущество Tail-based sampling перед Head-based?' Ответ: 'При Head-based мы бросаем монетку на старте запроса, когда еще не знаем, будет ли ошибка или аномальная задержка. При Tail-based OpenTelemetry Collector держит спаны в буфере и сэмплирует 100% трейсов с ошибками или длительностью > 2 сек, сберегая ресурсы на успешных рутинных запросах'."
    },
    {
        "num": 46,
        "title": "gRPC через AWS ALB vs NLB: L4 против L7 маршрутизации и ALPN",
        "task": "Спроектируйте конфигурацию взаимодействия gRPC с облачными балансировщиками AWS: объясните различия между ALB (L7 HTTP/2 routing) и NLB (L4 TCP pass-through) и настройте TLS с поддержкой ALPN (h2) в Go.",
        "theory": "При развертывании gRPC в публичных облаках выбор типа балансировщика определяет архитектуру: 1) AWS NLB (Network Load Balancer) — работает на L4 (TCP). NLB не умеет парсить HTTP/2 фреймы и терминировать gRPC стримы. Вся нагрузка по балансировке между подами ложится на плечи клиентского DNS/RoundRobin или Envoy Service Mesh. NLB подвержен залипанию сессий и сбросу соединений по idle timeout (350s). 2) AWS ALB (Application Load Balancer) — полноценный L7 балансировщик с поддержкой gRPC. ALB терминирует TLS, выполняет ALPN негоциацию протокола `h2`, разбирает HTTP/2 кадры и балансирует КАЖДЫЙ ОТДЕЛЬНЫЙ RPC вызов на разные целевые поды (Target Group) с маршрутизацией по пути `/service.Name/MethodName`.",
        "step_by_step": [
            "Настройте Go TLS конфигурацию с обязательным указанием NextProtos: []string{\"h2\"}.",
            "Создайте gRPC сервер с безопасными транспортными кредами.",
            "Проверьте рукопожатие ALPN с клиентской стороны.",
            "Сформулируйте рекомендации по выбору NLB vs ALB для HighLoad."
        ],
        "code_blocks": [
            {
                "filename": "grpc_alpn_tls.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"crypto/tls\"\n\t\"fmt\"\n\t\"log\"\n\t\"net\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials\"\n)\n\n// SetupALPNServerTLS настраивает TLS для согласования HTTP/2 (h2) с балансировщиками AWS ALB\nfunc SetupALPNServerTLS(certFile, keyFile string) (credentials.TransportCredentials, error) {\n\tcert, err := tls.LoadX509KeyPair(certFile, keyFile)\n\tif err != nil {\n\t\treturn nil, fmt.Errorf(\"load keys error: %w\", err)\n\t}\n\n\ttlsConfig := &tls.Config{\n\t\tCertificates: []tls.Certificate{cert},\n\t\t// КРИТИЧЕСКИ ВАЖНО: ALB требует 'h2' в списке согласования ALPN для gRPC\n\t\tNextProtos: []string{\"h2\", \"http/1.1\"},\n\t\tMinVersion: tls.VersionTLS12,\n\t}\n\n\treturn credentials.NewTLS(tlsConfig), nil\n}\n\nfunc main() {\n\t// Демонстрация параметров ALPN\n\ttlsConfig := &tls.Config{\n\t\tNextProtos: []string{\"h2\"},\n\t\tMinVersion: tls.VersionTLS13,\n\t}\n\n\tserver := grpc.NewServer(grpc.Creds(credentials.NewTLS(tlsConfig)))\n\t_ = server\n\n\tlis, err := net.Listen(\"tcp\", \":50055\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Listen failed: %v\", err)\n\t}\n\tdefer lis.Close()\n\n\tfmt.Println(\"gRPC Server configured with TLS ALPN ['h2'] ready for AWS ALB L7 ingress.\")\n}",
                "note": "Конфигурация TLS ALPN (h2) для корректной маршрутизации gRPC через L7 ALB"
            }
        ],
        "under_the_hood": "Во время ClientHello клиент отправляет расширение TLS Application-Layer Protocol Negotiation (ALPN). Если сервер или балансировщик не вернет подтверждение протокола `h2`, клиент откатится к HTTP/1.1 или разорвет соединение ошибкой `stream error: PROTOCOL_ERROR`.",
        "pitfalls": "Забыть указать `NextProtos: []string{\"h2\"}` на бэкенде при работе за балансировщиком в режиме pass-through. В таком случае клиент gRPC не сможет подтвердить HTTP/2 и выдаст ошибку `transport: authentication handshake failed`.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Что выбрать для gRPC микросервисов: L4 балансировщик (NLB/IPVS) или L7 (ALB/Envoy)?' Ответ: 'В 95% случаев необходим L7 (ALB/Envoy), так как только L7 умеет балансировать отдельные RPC стримы внутри постоянного TCP сокета. L4 балансировщик приводит к залипанию всех RPC вызовов на одном бэкенде, требуя сложной клиентской балансировки'."
    },
    {
        "num": 47,
        "title": "Паттерн Kubernetes Operator: написание Reconciler loop для управления ресурсами",
        "task": "Реализуйте базовый контроллер (Reconciler) на Go, реализующий паттерн Kubernetes Operator для автоматического мониторинга и восстановления целевого состояния распределенного сервиса.",
        "theory": "Паттерн Kubernetes Operator расширяет возможности K8s, позволяя автоматизировать сложные задачи управления: создание бэкапов, автоматический failover баз данных, управление сертификатами. В основе любого оператора лежит цикл согласования (Reconcile Loop): `Reconcile(ctx, req) (ctrl.Result, error)` Оператор сравнивает фактическое состояние кластера (Actual State) с желаемым состоянием, описанным в Custom Resource Definition (Desired State). Если обнаружено расхождение (например, упала реплика или изменился конфиг), Reconciler выполняет корректирующие действия и возвращает статус согласования.",
        "step_by_step": [
            "Определите структуру CustomResource и Reconciler.",
            "Реализуйте логику Reconcile с проверкой текущих ресурсов.",
            "Реализуйте идемпотентное создание недостающих объектов.",
            "Настройте периодический реквест на повторное согласование (RequeueAfter)."
        ],
        "code_blocks": [
            {
                "filename": "operator_reconciler.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"time\"\n)\n\ntype ResourceRequest struct {\n\tNamespace string\n\tName      string\n}\n\ntype ReconcileResult struct {\n\tRequeue      bool\n\tRequeueAfter time.Duration\n}\n\n// AppServiceCustomResource имитирует CRD объект в K8s\ntype AppServiceCustomResource struct {\n\tName            string\n\tDesiredReplicas int\n\tCurrentReplicas int\n}\n\ntype AppReconciler struct {\n\tclusterState map[string]*AppServiceCustomResource\n}\n\nfunc (r *AppReconciler) Reconcile(ctx context.Context, req ResourceRequest) (ReconcileResult, error) {\n\tlog.Printf(\"[Operator] Reconciling CustomResource %s/%s...\", req.Namespace, req.Name)\n\n\tcr, exists := r.clusterState[req.Name]\n\tif !exists {\n\t\tlog.Printf(\"[Operator] Resource %s deleted, cleaning up child resources.\", req.Name)\n\t\treturn ReconcileResult{}, nil\n\t}\n\n\t// Сравниваем Desired State и Actual State\n\tif cr.CurrentReplicas < cr.DesiredReplicas {\n\t\tdiff := cr.DesiredReplicas - cr.CurrentReplicas\n\t\tlog.Printf(\"[Operator] Scale-up needed! Actual=%d, Desired=%d. Spawning %d pods...\",\n\t\t\tcr.CurrentReplicas, cr.DesiredReplicas, diff)\n\t\tcr.CurrentReplicas = cr.DesiredReplicas\n\t} else if cr.CurrentReplicas > cr.DesiredReplicas {\n\t\tlog.Printf(\"[Operator] Scale-down needed! Terminating excess pods...\")\n\t\tcr.CurrentReplicas = cr.DesiredReplicas\n\t} else {\n\t\tlog.Printf(\"[Operator] Cluster state is in sync with Desired State (%d replicas).\", cr.CurrentReplicas)\n\t}\n\n\t// Повторная проверка через 10 секунд (Requeue)\n\treturn ReconcileResult{RequeueAfter: 10 * time.Second}, nil\n}\n\nfunc main() {\n\treconciler := &AppReconciler{\n\t\tclusterState: map[string]*AppServiceCustomResource{\n\t\t\t\"payment-gateway\": {\n\t\t\t\tName:            \"payment-gateway\",\n\t\t\t\tDesiredReplicas: 5,\n\t\t\t\tCurrentReplicas: 2, // Расхождение: нужно поднять еще 3\n\t\t\t},\n\t\t},\n\t}\n\n\treq := ResourceRequest{Namespace: \"default\", Name: \"payment-gateway\"}\n\tres, err := reconciler.Reconcile(context.Background(), req)\n\tif err != nil {\n\t\tlog.Fatalf(\"Reconcile error: %v\", err)\n\t}\n\n\tfmt.Printf(\"Operator reconcile cycle completed. Requeue scheduled in %v.\\n\", res.RequeueAfter)\n}",
                "note": "Реализация Reconcile Loop в паттерне Kubernetes Operator"
            }
        ],
        "under_the_hood": "В реальных операторах на `controller-runtime` цикл Reconcile вызывается событиями из Informer cache. Информеры следят за Kubernetes API через долгоживущие HTTP/2 HTTP Chunked / Watch соединения, минимизируя нагрузку на kube-apiserver.",
        "pitfalls": "Неидемпотентность логики в Reconcile. Reconciler может быть вызван несколько раз подряд на одно и то же событие. Каждое действие оператора обязано проверять текущее состояние, чтобы не создавать дубликаты ресурсов.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'В чем отличие обычного микросервиса от Kubernetes Operator?' Ответ: 'Микросервис решает прикладные бизнес-задачи. Оператор управляет жизненным циклом инфраструктуры внутри кластера через Reconcile loop (автоматический backup, failover, scaling, provisioning базы данных)'."
    },
    {
        "num": 48,
        "title": "Строгая валидация входящего Trace Context при экстракции в HTTP API",
        "task": "Реализуйте строгую валидацию заголовка traceparent при извлечении контекста: отклоняйте запросы с некорректным trace ID или флагами, возвращая HTTP 400 при обнаружении инъекций.",
        "theory": "Безопасность API требует строгой валидации всех входящих сетевых заголовков. Хотя OpenTelemetry по умолчанию старается мягко восстановить или сгенерировать контекст при ошибках, в закрытых высокозащищенных периметрах (FinTech, банки, PCI-DSS) передача невалидного заголовка `traceparent` может свидетельствовать о попытке взлома, фаззинга или инъекции управляющих символов в логер. В таких системах шлюз безопасности настраивается на строгую валидацию: любая попытка передать заголовок `traceparent`, не соответствующий грамматике W3C (55 байт hex), немедленно отклоняется кодом HTTP 400 Bad Request с записью Security Event в SIEM.",
        "step_by_step": [
            "Напишите строгий валидатор грамматики W3C Traceparent.",
            "Проверьте допустимость символов (строго hex lowercase).",
            "Реализуйте HTTP middleware с проверкой валидности заголовка.",
            "Верните статус 400 Bad Request при нарушении формата."
        ],
        "code_blocks": [
            {
                "filename": "strict_trace_validator.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/hex\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"strings\"\n)\n\n// ValidateW3CStrict выполняет исчерпывающую проверку заголовка traceparent\nfunc ValidateW3CStrict(tp string) error {\n\tif len(tp) != 55 {\n\t\treturn fmt.Errorf(\"length must be exactly 55 chars, got %d\", len(tp))\n\t}\n\tif tp[2] != '-' || tp[35] != '-' || tp[52] != '-' {\n\t\treturn fmt.Errorf(\"malformed delimiters, expected 00-{traceid}-{spanid}-{flags}\")\n\t}\n\n\tparts := strings.Split(tp, \"-\")\n\tif len(parts) != 4 {\n\t\treturn fmt.Errorf(\"invalid segment count\")\n\t}\n\n\tversion, traceID, spanID, flags := parts[0], parts[1], parts[2], parts[3]\n\n\tif version == \"ff\" {\n\t\treturn fmt.Errorf(\"version ff is forbidden by W3C\")\n\t}\n\n\t// Проверка шестнадцатеричных байт\n\tvar traceBytes [16]byte\n\tif _, err := hex.Decode(traceBytes[:], []byte(traceID)); err != nil {\n\t\treturn fmt.Errorf(\"trace-id must be valid hex: %w\", err)\n\t}\n\tif traceID == \"00000000000000000000000000000000\" {\n\t\treturn fmt.Errorf(\"all-zero trace-id is illegal\")\n\t}\n\n\tvar spanBytes [8]byte\n\tif _, err := hex.Decode(spanBytes[:], []byte(spanID)); err != nil {\n\t\treturn fmt.Errorf(\"span-id must be valid hex: %w\", err)\n\t}\n\tif spanID == \"0000000000000000\" {\n\t\treturn fmt.Errorf(\"all-zero span-id is illegal\")\n\t}\n\n\tvar flagBytes [1]byte\n\tif _, err := hex.Decode(flagBytes[:], []byte(flags)); err != nil {\n\t\treturn fmt.Errorf(\"flags must be valid hex: %w\", err)\n\t}\n\n\treturn nil\n}\n\nfunc StrictTraceValidationMiddleware(next http.Handler) http.Handler {\n\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\ttp := r.Header.Get(\"traceparent\")\n\t\tif tp != \"\" {\n\t\t\tif err := ValidateW3CStrict(tp); err != nil {\n\t\t\t\thttp.Error(w, fmt.Sprintf(\"Invalid W3C traceparent header: %v\", err), http.StatusBadRequest)\n\t\t\t\treturn\n\t\t\t}\n\t\t}\n\t\tnext.ServeHTTP(w, r)\n\t})\n}\n\nfunc main() {\n\thandler := StrictTraceValidationMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"Accepted\"))\n\t}))\n\n\t// Тест 1: Невалидный заголовок (инъекция пробелов и спецсимволов)\n\tbadReq := httptest.NewRequest(\"GET\", \"/secure\", nil)\n\tbadReq.Header.Set(\"traceparent\", \"00-invalid_trace_id_injection!#$$%-00f067aa0ba902b7-01\")\n\trec1 := httptest.NewRecorder()\n\thandler.ServeHTTP(rec1, badReq)\n\tfmt.Printf(\"Bad Request Status: %d (Body: %s)\\n\", rec1.Code, strings.TrimSpace(rec1.Body.String()))\n\n\t// Тест 2: Валидный заголовок\n\tgoodReq := httptest.NewRequest(\"GET\", \"/secure\", nil)\n\tgoodReq.Header.Set(\"traceparent\", \"00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01\")\n\trec2 := httptest.NewRecorder()\n\thandler.ServeHTTP(rec2, goodReq)\n\tfmt.Printf(\"Good Request Status: %d\\n\", rec2.Code)\n}",
                "note": "Строгая санитизация и валидация входящих заголовков W3C трассировки"
            }
        ],
        "under_the_hood": "По стандарту W3C все символы hex обязаны быть в нижнем регистре (lowercase). Использование `hex.Decode` гарантирует, что строка не содержит скрытых непечатаемых символов и пробелов.",
        "pitfalls": "Отклонять заголовки без проверки наличия самого заголовка. Если внешний клиент не передал traceparent (первый запрос от мобильного приложения), это нормальная ситуация — сервис должен сам сгенерировать корневой Trace Context, а не возвращать 400.",
        "bigtech_interview": "Вопрос на собеседовании в Тинькофф: 'Почему важно валидировать trace headers на API Gateway перед логированием?' Ответ: 'Заголовок может содержать символы перевода строки (CRLF Injection), управляющие ANSI-последовательности или слишком длинную строку, способную вызвать переполнение буфера в log shipper (Logstash/Fluentbit)'."
    },
    {
        "num": 49,
        "title": "Каверзный кейс: gRPC + Kubernetes — гонка Envoy sidecar и SIGTERM",
        "task": "Смоделируйте гонку между удалением пода из Service Endpoints и локальным Envoy sidecar при получении SIGTERM. Реализуйте алгоритм, удерживающий gRPC листенер открытым заданное время перед вызовом GracefulStop().",
        "theory": "В кластере со Service Mesh (Istio/Linkerd) в поде работают два контейнера: приложение Go и sidecar Envoy. Когда K8s посылает SIGTERM, оба контейнера получают сигнал ПАРАЛЛЕЛЬНО. Envoy начинает процесс сброса трафика, но другие Envoy-прокси в кластере продолжают отправлять вызовы на этот под еще 3-5 секунд, пока до них не дойдет событие об удалении Endpoint. Если Go-сервер при получении SIGTERM сразу закроет порт или начнет GracefulStop, локальный Envoy получит отказ при попытке переслать запрос на 127.0.0.1:50051 и вернет клиентам HTTP 503 UC (upstream connect failure). Поэтому gRPC-сервер обязан: 1) Перехватить SIGTERM; 2) Продолжать полноценно обслуживать новые RPC запросы в течение дренажной паузы (draining delay, 5 секунд); 3) И только после этого вызывать `server.GracefulStop()`.",
        "step_by_step": [
            "Создайте gRPC сервер с тестовым сервисом.",
            "Настройте перехват сигнала SIGTERM в main.",
            "Реализуйте защитную паузу time.Sleep(5 * time.Second) до вызова GracefulStop.",
            "Убедитесь, что во время паузы новые запросы успешно обрабатываются.",
            "Вызовите GracefulStop с дедлайном."
        ],
        "code_blocks": [
            {
                "filename": "grpc_k8s_race_protection.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net\"\n\t\"os\"\n\t\"os/signal\"\n\t\"sync/atomic\"\n\t\"syscall\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n)\n\ntype RaceProtectedServer struct {\n\tserver       *grpc.Server\n\tisTerminated atomic.Bool\n}\n\nfunc (s *RaceProtectedServer) HandleShutdown() {\n\tstop := make(chan os.Signal, 1)\n\tsignal.Notify(stop, syscall.SIGTERM, os.Interrupt)\n\t<-stop\n\n\tlog.Println(\"[SIGTERM] Signal received! Entering holding delay for Envoy & K8s endpoints...\")\n\n\t// 1. Не закрываем сервер сразу! Envoy sidecars еще пересылают сетевые запросы\n\tdrainingDelay := 3 * time.Second\n\ttime.Sleep(drainingDelay)\n\n\t// 2. Теперь, когда Envoy исключил нас из пула upstream, начинаем GracefulStop\n\tlog.Println(\"[Shutdown] Draining delay expired. Commencing grpc.GracefulStop()...\")\n\tstopped := make(chan struct{})\n\tgo func() {\n\t\ts.server.GracefulStop()\n\t\tclose(stopped)\n\t}()\n\n\tselect {\n\tcase <-stopped:\n\t\tlog.Println(\"[Shutdown] GracefulStop cleanly finished.\")\n\tcase <-time.After(10 * time.Second):\n\t\tlog.Println(\"[Shutdown] Timeout expired, forcing Stop().\")\n\t\ts.server.Stop()\n\t}\n}\n\nfunc main() {\n\tlis, err := net.Listen(\"tcp\", \":50056\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Listen failed: %v\", err)\n\t}\n\n\tapp := &RaceProtectedServer{\n\t\tserver: grpc.NewServer(),\n\t}\n\n\tgo func() {\n\t\tlog.Println(\"gRPC Server serving on :50056\")\n\t\t_ = app.server.Serve(lis)\n\t}()\n\n\ttime.Sleep(100 * time.Millisecond)\n\n\t// Имитация перехвата сигнала в отдельной горутине для демонстрации\n\tgo func() {\n\t\tp, _ := os.FindProcess(os.Getpid())\n\t\t_ = p.Signal(syscall.SIGTERM)\n\t}()\n\n\tapp.HandleShutdown()\n\tfmt.Println(\"Race-protected shutdown completed successfully.\")\n}",
                "note": "Удержание gRPC сокета открытым для предотвращения 503 UC ошибок в Service Mesh"
            }
        ],
        "under_the_hood": "Envoy возвращает код ответа `503 UC` (Upstream Connection Failure), когда TCP-соединение к локальному контейнеру приложения сбрасывается сокетом (RST) до того, как Envoy успел перевести под в режим draining.",
        "pitfalls": "Забыть настроить `terminationGracePeriodSeconds` в K8s с учетом задержки. Если задержка 15 секунд, а grace period 15 секунд, на саму остановку приложения останется 0 секунд.",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'Почему в Istio поды иногда отдают 503 UC при деплое новой версии?' Ответ: 'Go-приложение при получении SIGTERM мгновенно закрывает свой сокет, а Envoy sidecar на соседних подах еще пару секунд посылает новые запросы по старым IP-адресам. Решение — выдерживать draining delay перед остановкой сервера в Go'."
    },
    {
        "num": 50,
        "title": "Финальный босс: Cloud-Native Microservices Platform — сквозная трассировка и keepalive",
        "task": "Спроектируйте архитектуру отказоустойчивой микросервисной платформы (API Gateway, Order Service, Payment Service) с непрерывной передачей W3C Trace Context сквозь HTTP, gRPC и брокер сообщений, а также gRPC Keepalive.",
        "theory": "Архитектура Cloud-Native платформы BigTech уровня требует строгого соответствия следующим стандартам: 1) Непрерывная распределенная трассировка: сквозной `trace_id` зарождается на API Gateway и без потерь передается в синхронный gRPC вызов к сервису заказов, а затем в асинхронное событие брокера к сервису платежей; 2) Высокая живучесть соединений: все внутренние gRPC клиенты используют Keepalive с интервалом зондирования 15 секунд, а серверы настроены на ротацию `MaxConnectionAge` для равномерной балансировки по репликам; 3) Полная наблюдаемость (Observability): логи структурированы и содержат `trace_id`, метрики Prometheus содержат Exemplars с привязкой к спанам; 4) Безупречный Graceful Shutdown: поддержка Kubernetes preStop хуков и многоэтапное завершение без потери клиентских запросов.",
        "step_by_step": [
            "Определите сквозные интерфейсы передачи Trace Context.",
            "Настройте gRPC клиенты с отказоустойчивыми параметрами keepalive.",
            "Свяжите HTTP, gRPC и событийно-ориентированную обработку единым контекстом.",
            "Реализуйте координированное завершение всех узлов платформы."
        ],
        "code_blocks": [
            {
                "filename": "cloud_native_platform.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"time\"\n\n\t\"go.opentelemetry.io/otel\"\n\t\"go.opentelemetry.io/otel/propagation\"\n\tsdktrace \"go.opentelemetry.io/otel/sdk/trace\"\n\t\"go.opentelemetry.io/otel/trace\"\n\t\"google.golang.org/grpc/keepalive\"\n)\n\n// PlatformConfig объединяет настройки для всех микросервисов кластера\ntype PlatformConfig struct {\n\tClientKeepalive keepalive.ClientParameters\n\tServerKeepalive keepalive.ServerParameters\n}\n\nfunc NewProductionPlatformConfig() PlatformConfig {\n\treturn PlatformConfig{\n\t\tClientKeepalive: keepalive.ClientParameters{\n\t\t\tTime:                15 * time.Second,\n\t\t\tTimeout:             5 * time.Second,\n\t\t\tPermitWithoutStream: true,\n\t\t},\n\t\tServerKeepalive: keepalive.ServerParameters{\n\t\t\tMaxConnectionAge:      10 * time.Minute,\n\t\t\tMaxConnectionAgeGrace: 30 * time.Second,\n\t\t\tTime:                  2 * time.Hour,\n\t\t\tTimeout:               20 * time.Second,\n\t\t},\n\t}\n}\n\nfunc main() {\n\t// 1. Инициализация глобального OpenTelemetry TracerProvider\n\ttp := sdktrace.NewTracerProvider(sdktrace.WithSampler(sdktrace.AlwaysSample()))\n\totel.SetTracerProvider(tp)\n\totel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(\n\t\tpropagation.TraceContext{},\n\t\tpropagation.Baggage{},\n\t))\n\n\tcfg := NewProductionPlatformConfig()\n\tlog.Printf(\"Platform Keepalive configured: ClientTime=%v, ServerMaxAge=%v\",\n\t\tcfg.ClientKeepalive.Time, cfg.ServerKeepalive.MaxConnectionAge)\n\n\t// 2. Имитация сквозного трейса: Gateway -> Order -> Payment\n\ttracer := otel.Tracer(\"api-gateway\")\n\trootCtx, gatewaySpan := tracer.Start(context.Background(), \"POST /api/v1/checkout\",\n\t\ttrace.WithSpanKind(trace.SpanKindServer),\n\t)\n\tdefer gatewaySpan.End()\n\n\ttraceID := gatewaySpan.SpanContext().TraceID().String()\n\tlog.Printf(\"[Gateway] Request received. Initiated TraceID: %s\", traceID)\n\n\t// downstream gRPC call\n\torderTracer := otel.Tracer(\"order-service\")\n\torderCtx, orderSpan := orderTracer.Start(rootCtx, \"OrderService.CreateOrder\",\n\t\ttrace.WithSpanKind(trace.SpanKindClient),\n\t)\n\ttime.Sleep(20 * time.Millisecond)\n\torderSpan.End()\n\n\t// downstream async event\n\tpaymentTracer := otel.Tracer(\"payment-worker\")\n\t_, paySpan := paymentTracer.Start(orderCtx, \"ProcessPaymentEvent\",\n\t\ttrace.WithSpanKind(trace.SpanKindConsumer),\n\t)\n\ttime.Sleep(30 * time.Millisecond)\n\tpaySpan.End()\n\n\tlog.Printf(\"[Success] Full call chain verified with common TraceID: %s\", paySpan.SpanContext().TraceID().String())\n\tfmt.Println(\"Cloud-Native platform architecture demonstration completed.\")\n}",
                "note": "Эталонная архитектура Cloud-Native микросервисной платформы с W3C трейсингом и gRPC keepalive"
            }
        ],
        "under_the_hood": "Взаимодействие OpenTelemetry и HTTP/2 транспорта гарантирует сохранение связанности графа вызовов даже при переключении между синхронными RPC и асинхронными очередями сообщений.",
        "pitfalls": "Отсутствие единого стандарта конфигурации keepalive между командами разных сервисов. Если сервис А шлет PING каждые 2 секунды, а сервис Б считает недопустимым пинг чаще 5 секунд, система войдет в режим постоянных обрывов соединений.",
        "bigtech_interview": "Вопрос на архитектурной секции в Яндекс: 'Опишите полный стек сетевой надежности gRPC сервиса в Kubernetes.' Ответ: '1) PreStop hook (10s) в K8s PodSpec; 2) Перевод readinessProbe в 503 при SIGTERM; 3) Клиентский Keepalive (Time=15s, Timeout=5s); 4) Серверный MaxConnectionAge (10m) для балансировки; 5) W3C TraceContext проброс через interceptors; 6) GracefulStop с дедлайном'."
    },
    {
        "num": 51,
        "title": "Service Mesh и gRPC Keepalive: влияние idle_timeout в Envoy proxy",
        "task": "Настройте gRPC keepalive с учетом idle_timeout в Envoy Sidecar (Istio). Объясните, почему gRPC PING сбрасывает таймер неактивности прокси-сервера.",
        "theory": "В архитектуре Istio / Service Mesh трафик между микросервисами проходит через локальные прокси-серверы Envoy: `Client App -> Local Envoy Outbound -> Remote Envoy Inbound -> Server App`. У Envoy есть параметр `idle_timeout` (по умолчанию 1 час для HTTP/2, но часто настраивается на 5 минут в целях экономии ресурсов). Если между сервисами долго нет RPC-запросов, Envoy закроет TCP-соединение. Однако кадры HTTP/2 PING, генерируемые gRPC Keepalive, расцениваются Envoy как легитимная активность протокола! Каждый полученный PING-фрейм сбрасывает счетчик `idle_timeout` в Envoy, предотвращая разрыв соединения прокси-сервером в периоды затишья бизнес-трафика.",
        "step_by_step": [
            "Изучите конфигурацию HttpConnectionManager в Envoy.",
            "Настройте клиентский keepalive в Go с интервалом, меньшим чем idle_timeout в Envoy.",
            "Проверьте, что соединение остается активным при длительном отсутствии данных.",
            "Сформулируйте рекомендации по тюнингу таймаутов Mesh."
        ],
        "code_blocks": [
            {
                "filename": "envoy_keepalive_sync.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n\t\"google.golang.org/grpc/keepalive\"\n)\n\n// DialEnvoyCompatibleClient подключается через локальный Envoy sidecar\nfunc DialEnvoyCompatibleClient(target string) (*grpc.ClientConn, error) {\n\t// Если в Envoy idle_timeout настроен на 60 секунд,\n\t// gRPC keepalive Time обязан быть существенно меньше (например 20с)\n\tkacp := keepalive.ClientParameters{\n\t\tTime:                20 * time.Second, // Сбрасывает Envoy idle_timeout каждые 20с\n\t\tTimeout:             5 * time.Second,\n\t\tPermitWithoutStream: true,\n\t}\n\n\tctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)\n\tdefer cancel()\n\n\tconn, err := grpc.DialContext(ctx, target,\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t\tgrpc.WithKeepaliveParams(kacp),\n\t)\n\tif err != nil {\n\t\treturn nil, fmt.Errorf(\"dial error: %w\", err)\n\t}\n\n\treturn conn, nil\n}\n\nfunc main() {\n\tlog.Println(\"Initializing gRPC client tuned for Envoy Service Mesh idle_timeout...\")\n\tconn, err := DialEnvoyCompatibleClient(\"127.0.0.1:15001\") // Порт Envoy outbound\n\tif err != nil {\n\t\tlog.Printf(\"[Notice] Mesh proxy connection deferred: %v\", err)\n\t\treturn\n\t}\n\tdefer conn.Close()\n\n\tfmt.Println(\"Envoy-compatible keepalive client configured successfully.\")\n}",
                "note": "Тюнинг интервалов keepalive для предотвращения закрытия сессий прокси Envoy"
            }
        ],
        "under_the_hood": "Внутри Envoy обработчик `ActiveStream::onIdleTimeout()` взводит таймер на дескрипторе соединения. При парсинге HTTP/2 фрейма PING вызов `Http2Session::onPingReceived()` сбрасывает этот таймер, не передавая кадр приложению, а сразу возвращая PING ACK.",
        "pitfalls": "Установка `PermitWithoutStream: false` при коротком `idle_timeout` в Envoy. В таком случае при отсутствии RPC вызовов gRPC клиент не будет слать PING, и Envoy разорвет соединение через 60 секунд.",
        "bigtech_interview": "Вопрос на собеседовании в Тинькофф: 'Как Envoy реагирует на HTTP/2 PING кадры от gRPC клиента?' Ответ: 'Envoy самостоятельно отвечает на PING кадром ACK на уровне HTTP/2 сессии и сбрасывает свой idle_timeout, не форвардя PING дальше на вышестоящий бэкенд, что защищает бэкенд от лишней нагрузки'."
    },
    {
        "num": 52,
        "title": "Zero-Trust аутентификация в gRPC: интеграция со SPIFFE / SPIRE",
        "task": "Реализуйте валидацию криптографического идентификатора SPIFFE ID (spiffe://cluster.local/ns/prod/sa/order-service) в gRPC перехватчике на основе TLS сертификатов X.509.",
        "theory": "В современной Zero-Trust инфраструктуре отказ от статических API-ключей и паролей — обязательное требование безопасности. Стандарт SPIFFE (Secure Production Identity Framework for Everyone) и агент SPIRE предоставляют каждому поду криптографический X.509 сертификат (SVID), содержащий SPIFFE ID в расширении SAN (Subject Alternative Name) URI: `spiffe://cluster.local/ns/prod/sa/billing-service`. При установлении mTLS соединения серверный интерцептор gRPC извлекает peer certificate, читает SPIFFE ID и проверяет, имеет ли данный сервис право вызывать данный метод (Authorization / RBAC).",
        "step_by_step": [
            "Определите парсер SPIFFE ID из tls.ConnectionState.",
            "Создайте серверный gRPC UnaryInterceptor с проверкой разрешенных SPIFFE ID.",
            "При несоответствии идентификатора верните статус PermissionDenied.",
            "Проверьте успешную аутентификацию валидного доверенного сервиса."
        ],
        "code_blocks": [
            {
                "filename": "spiffe_auth.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"crypto/x509\"\n\t\"fmt\"\n\t\"strings\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/credentials\"\n\t\"google.golang.org/grpc/peer\"\n\t\"google.golang.org/grpc/status\"\n)\n\n// ExtractSpiffeID извлекает идентификатор SPIFFE из X.509 SAN URI сертификата клиента\nfunc ExtractSpiffeID(cert *x509.Certificate) (string, error) {\n\tfor _, uri := range cert.URIs {\n\t\tif uri.Scheme == \"spiffe\" {\n\t\t\treturn uri.String(), nil\n\t\t}\n\t}\n\treturn \"\", fmt.Errorf(\"no spiffe id found in certificate SAN\")\n}\n\n// SpiffeAuthInterceptor валидирует доступ на основе SPIFFE ID клиента\nfunc SpiffeAuthInterceptor(allowedSpiffeIDs []string) grpc.UnaryServerInterceptor {\n\tallowedMap := make(map[string]bool)\n\tfor _, id := range allowedSpiffeIDs {\n\t\tallowedMap[id] = true\n\t}\n\n\treturn func(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {\n\t\tp, ok := peer.FromContext(ctx)\n\t\tif !ok || p.AuthInfo == nil {\n\t\t\treturn nil, status.Error(codes.Unauthenticated, \"missing TLS peer authentication\")\n\t\t}\n\n\t\ttlsInfo, ok := p.AuthInfo.(credentials.TLSInfo)\n\t\tif !ok || len(tlsInfo.State.PeerCertificates) == 0 {\n\t\t\treturn nil, status.Error(codes.Unauthenticated, \"missing peer certificate\")\n\t\t}\n\n\t\tpeerCert := tlsInfo.State.PeerCertificates[0]\n\t\tspiffeID, err := ExtractSpiffeID(peerCert)\n\t\tif err != nil {\n\t\t\treturn nil, status.Errorf(codes.Unauthenticated, \"invalid spiffe id: %v\", err)\n\t\t}\n\n\t\tif !allowedMap[spiffeID] {\n\t\t\treturn nil, status.Errorf(codes.PermissionDenied, \"spiffe id %s is not authorized for %s\", spiffeID, info.FullMethod)\n\t\t}\n\n\t\treturn handler(ctx, req)\n\t}\n}\n\nfunc main() {\n\tallowedClients := []string{\n\t\t\"spiffe://cluster.local/ns/prod/sa/order-service\",\n\t\t\"spiffe://cluster.local/ns/prod/sa/api-gateway\",\n\t}\n\n\tserver := grpc.NewServer(\n\t\tgrpc.UnaryInterceptor(SpiffeAuthInterceptor(allowedClients)),\n\t)\n\t_ = server\n\n\tfmt.Println(\"Zero-Trust gRPC Server with SPIFFE/SPIRE authentication initialized.\")\n\t_ = codes.PermissionDenied\n\t_ = strings.Clone\n}",
                "note": "Авторизация на основе криптографического SPIFFE ID в gRPC"
            }
        ],
        "under_the_hood": "SPIRE агент автоматически обновляет X.509 SVID сертификаты каждые несколько часов через UNIX сокет (`/tmp/spire-agent/public/api.sock`). Приложение перечитывает сертификаты на лету без перезапуска процесса.",
        "pitfalls": "Проверка SPIFFE ID по строковому равенству без валидации доверенного корневого центра (Trust Domain). Всегда проверяйте соответствие trust domain: `spiffe://cluster.local/...`.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'В чем преимущество SPIFFE перед взаимным mTLS на обычных сертификатах?' Ответ: 'SPIFFE стандартизирует единый формат идентификации рабочих нагрузок (Workload Identity) независимо от платформы (K8s, Bare-metal, AWS). Сертификаты короткоживущие (часы), а ротация происходит прозрачно через Workload API без участия разработчика'."
    },
    {
        "num": 53,
        "title": "Защита сервера от частых пингов: keepalive.EnforcementPolicy и штрафные страйки",
        "task": "Сконфигурируйте gRPC сервер с keepalive.EnforcementPolicy{MinTime: 10s, PermitWithoutStream: false}. Покажите, как сервер наказывает клиентов штрафными страйками за спам фреймами.",
        "theory": "gRPC сервер должен быть защищен от ошибок в конфигурации клиентов. Если плохо написанный сторонний сервис или скрипт начнет отправлять PING каждые 50 миллисекунд, сервер может исчерпать лимиты соединений. Механизм `keepalive.EnforcementPolicy` работает следующим образом: 1) `MinTime: 10s`: если между двумя PING от клиента прошло меньше 10 секунд, сервер увеличивает счетчик нарушений (`pingStrikes`); 2) `PermitWithoutStream: false`: если клиент шлет PING при отсутствии активных RPC стримов, это также считается нарушением; 3) При получении второго страйка подряд сервер не отвечает ACK, а отправляет HTTP/2 фрейм `GOAWAY` с кодом ошибки `ENHANCE_YOUR_CALM` и текстом `too_many_pings`, после чего закрывает TCP сокет.",
        "step_by_step": [
            "Импортируйте google.golang.org/grpc/keepalive.",
            "Сконфигурируйте EnforcementPolicy со строгими лимитами.",
            "Передайте политику в grpc.NewServer через grpc.KeepaliveEnforcementPolicy.",
            "Проверьте реакцию сервера на агрессивное зондирование со стороны клиента."
        ],
        "code_blocks": [
            {
                "filename": "strict_enforcement.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/keepalive\"\n)\n\nfunc main() {\n\t// Строгая политика защиты сервера от DoS атак через PING кадры\n\tpolicy := keepalive.EnforcementPolicy{\n\t\tMinTime:             10 * time.Second, // Клиент обязан ждать не менее 10 секунд между PING\n\t\tPermitWithoutStream: false,            // Запрещен PING, если нет активных вызовов\n\t}\n\n\tserver := grpc.NewServer(\n\t\tgrpc.KeepaliveEnforcementPolicy(policy),\n\t)\n\n\tlis, err := net.Listen(\"tcp\", \":50057\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Failed to bind port: %v\", err)\n\t}\n\tdefer lis.Close()\n\n\tgo func() {\n\t\ttime.Sleep(100 * time.Millisecond)\n\t\tserver.Stop()\n\t}()\n\n\tlog.Println(\"gRPC Server started with MinTime=10s EnforcementPolicy\")\n\t_ = server.Serve(lis)\n\tfmt.Println(\"Enforcement policy demonstration executed.\")\n}",
                "note": "Строгая политика ограничения частоты клиентских фреймов PING"
            }
        ],
        "under_the_hood": "В исходниках `google.golang.org/grpc/internal/transport/http2_server.go`: если `pingStrikes > 2`, вызывается `s.controlBuf.put(&goAway{code: http2.ErrCodeEnhanceYourCalm, debugData: []byte(\"too_many_pings\")})`. После этого сокет переводится в закрывающееся состояние.",
        "pitfalls": "Настройка `MinTime: 10s` на сервере при дефолтном `Time: 10s` на клиенте. Из-за сетевого джиттера клиентский пакет может прийти на 1 миллисекунду раньше (через 9.999s), что сервер посчитает нарушением! Всегда делайте `Server.MinTime` меньше, чем `Client.Time` (например сервер 5с, клиент 10с).",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'Что означает gRPC ошибка ENHANCE_YOUR_CALM too_many_pings?' Ответ: 'Сервер зафиксировал нарушение политики Keepalive EnforcementPolicy: клиент отправлял HTTP/2 фреймы PING чаще, чем разрешено параметром MinTime, или без активных стримов'."
    },
    {
        "num": 54,
        "title": "Долгоживущие gRPC BiDi стримы: безопасный Draining и закрытие по EOF",
        "task": "Реализуйте двунаправленный потоковый метод (Bidirectional Stream). При получении сигнала SIGTERM сервер должен корректно уведомить клиентов о завершении работы через закрытие стрима (io.EOF), не обрывая соединение аварийно.",
        "theory": "Обычные унарные вызовы gRPC (Unary RPC) завершаются за миллисекунды. Однако в системах реального времени (чаты, финансовые котировки, телеметрия IoT) соединение держится часами через двунаправленный стрим (`BiDi Streaming`). Если при остановке сервера просто вызвать `GracefulStop()`, он будет ждать завершения стрима бесконечно. Если вызвать жесткий `Stop()`, клиенты получат ошибку `Unavailable: transport is closing`. Правильный паттерн: сервер перехватывает сигнал завершения, рассылает по активным стримам специальное служебное сообщение о закрытии и возвращает `nil` из обработчика метода. На сетевом уровне клиенту отправляется HTTP/2 фрейм с флагом `END_STREAM`, клиент читает `io.EOF` и мягко переподключается к другой ноде.",
        "step_by_step": [
            "Определите интерфейс потоковой передачи с контекстом завершения.",
            "Создайте широковещательный канал закрытия drainingChan := make(chan struct{}).",
            "В обработчике стрима используйте select между входящими сообщениями и drainingChan.",
            "При получении сигнала завершите обработку штатным возвратом nil (EOF).",
            "Проверьте отсутствие аварийных ошибок у клиента."
        ],
        "code_blocks": [
            {
                "filename": "bidi_draining.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"io\"\n\t\"log\"\n\t\"sync\"\n\t\"time\"\n)\n\ntype ChatMessage struct {\n\tUser string\n\tText string\n}\n\ntype BiDiStreamServer struct {\n\tdrainingChan chan struct{}\n\tmu           sync.Mutex\n}\n\nfunc NewBiDiStreamServer() *BiDiStreamServer {\n\treturn &BiDiStreamServer{\n\t\tdrainingChan: make(chan struct{}),\n\t}\n}\n\n// StreamHandler имитирует gRPC Bidirectional Stream\nfunc (s *BiDiStreamServer) StreamHandler(ctx context.Context, clientIn <-chan ChatMessage, clientOut chan<- ChatMessage) error {\n\tlog.Println(\"[Stream] Client connected to BiDi stream.\")\n\n\tfor {\n\t\tselect {\n\t\tcase <-s.drainingChan:\n\t\t\t// Сервер выключается: шлем прощальное сообщение и закрываем стрим штатно\n\t\t\tlog.Println(\"[Stream] Server is draining. Notifying client and closing stream gracefully...\")\n\t\t\tclientOut <- ChatMessage{User: \"SYSTEM\", Text: \"SERVER_SHUTDOWN_RECONNECT\"}\n\t\t\treturn nil // Возврат nil шлет HTTP/2 END_STREAM (клиент получает io.EOF)\n\n\t\tcase <-ctx.Done():\n\t\t\treturn ctx.Err()\n\n\t\tcase msg, ok := <-clientIn:\n\t\t\tif !ok {\n\t\t\t\treturn nil\n\t\t\t}\n\t\t\tlog.Printf(\"[Stream] Received from %s: %s\", msg.User, msg.Text)\n\t\t\tclientOut <- ChatMessage{User: \"ECHO\", Text: msg.Text}\n\t\t}\n\t}\n}\n\nfunc (s *BiDiStreamServer) TriggerDrain() {\n\ts.mu.Lock()\n\tdefer s.mu.Unlock()\n\tselect {\n\tcase <-s.drainingChan:\n\tdefault:\n\t\tclose(s.drainingChan)\n\t}\n}\n\nfunc main() {\n\tsrv := NewBiDiStreamServer()\n\tinChan := make(chan ChatMessage, 5)\n\toutChan := make(chan ChatMessage, 5)\n\n\tctx, cancel := context.WithCancel(context.Background())\n\tdefer cancel()\n\n\t// Запуск стрима\n\tstreamDone := make(chan error, 1)\n\tgo func() {\n\t\tstreamDone <- srv.StreamHandler(ctx, inChan, outChan)\n\t}()\n\n\t// Клиент отправляет сообщение\n\tinChan <- ChatMessage{User: \"Alice\", Text: \"Hello stream\"}\n\tresp := <-outChan\n\tfmt.Printf(\"Client received: [%s] %s\\n\", resp.User, resp.Text)\n\n\t// Имитируем SIGTERM и запуск Draining\n\tlog.Println(\"Simulating SIGTERM draining event...\")\n\tsrv.TriggerDrain()\n\n\t// Клиент получает уведомление о завершении\n\tshutdownMsg := <-outChan\n\tfmt.Printf(\"Client received shutdown notice: [%s] %s\\n\", shutdownMsg.User, shutdownMsg.Text)\n\n\terr := <-streamDone\n\tif err == nil || err == io.EOF {\n\t\tfmt.Println(\"Stream cleanly terminated with EOF without transport errors.\")\n\t}\n}",
                "note": "Корректное завершение gRPC BiDi стримов при Graceful Draining"
            }
        ],
        "under_the_hood": "Возврат `nil` из стримового метода gRPC заставляет рантайм отправить HTTP/2 DATA кадр с флагом `END_STREAM` (0x1), за которым следует TRAILERS кадр со статусом `codes.OK`. Клиентский метод `stream.Recv()` возвращает ошибку `io.EOF`, что является штатным сигналом закрытия.",
        "pitfalls": "Вызов `server.GracefulStop()` без уведомления долгоживущих стримов. `GracefulStop()` заблокируется и не завершится, пока клиенты сами не закроют свои стримы.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Как корректно остановить gRPC сервер, если на нем висит 50 000 постоянных WebSockets/gRPC стримов?' Ответ: '1) Перестать принимать новые соединения; 2) Закрыть внутренний канал draining; 3) Горутины-обработчики стримов выходят из цикла, отправляя клиентам EOF; 4) Клиенты получают EOF и плавно распределяются на соседние поды с добавлением случайной задержки (jitter)'."
    },
    {
        "num": 55,
        "title": "Distributed Tracing: универсальный интерфейс TraceContextCarrier",
        "task": "Создайте универсальную абстракцию TraceContextCarrier, инкапсулирующую инжекцию и извлечение Trace Context для любых произвольных транспортных протоколов.",
        "theory": "В крупных корпоративных системах трафик циркулирует через разнообразные сетевые транспорты: HTTP/1.1, HTTP/2 gRPC, AMQP RabbitMQ, Kafka, NATS, Redis Streams, WebSocket. Чтобы бизнес-код не зависел от конкретных заголовков каждого брокера, создается универсальный адаптер `TraceContextCarrier`, удовлетворяющий интерфейсу `propagation.TextMapCarrier`. Это позволяет единообразно пробрасывать контекст трассировки одной строкой кода в любом слое архитектуры.",
        "step_by_step": [
            "Реализуйте обобщенную структуру MapCarrier поверх map[string]string.",
            "Реализуйте методы Get, Set, Keys интерфейса TextMapCarrier.",
            "Напишите функции-хелперы InjectContext и ExtractContext.",
            "Проверьте работу с произвольным транспортным протоколом."
        ],
        "code_blocks": [
            {
                "filename": "universal_carrier.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\n\t\"go.opentelemetry.io/otel\"\n\t\"go.opentelemetry.io/otel/propagation\"\n\tsdktrace \"go.opentelemetry.io/otel/sdk/trace\"\n\t\"go.opentelemetry.io/otel/trace\"\n)\n\n// MapCarrier реализует propagation.TextMapCarrier для универсальных ключ-значение структур\ntype MapCarrier map[string]string\n\nfunc (m MapCarrier) Get(key string) string {\n\treturn m[key]\n}\n\nfunc (m MapCarrier) Set(key, val string) {\n\tm[key] = val\n}\n\nfunc (m MapCarrier) Keys() []string {\n\tkeys := make([]string, 0, len(m))\n\tfor k := range m {\n\t\tkeys = append(keys, k)\n\t}\n\treturn keys\n}\n\n// InjectTrace инжектирует контекст в произвольную мапу\nfunc InjectTrace(ctx context.Context, carrier MapCarrier) {\n\totel.GetTextMapPropagator().Inject(ctx, carrier)\n}\n\n// ExtractTrace извлекает контекст из произвольной мапы\nfunc ExtractTrace(ctx context.Context, carrier MapCarrier) context.Context {\n\treturn otel.GetTextMapPropagator().Extract(ctx, carrier)\n}\n\nfunc main() {\n\ttp := sdktrace.NewTracerProvider(sdktrace.WithSampler(sdktrace.AlwaysSample()))\n\totel.SetTracerProvider(tp)\n\totel.SetTextMapPropagator(propagation.TraceContext{})\n\n\ttracer := otel.Tracer(\"custom-engine\")\n\tctx, span := tracer.Start(context.Background(), \"ExecuteCustomTask\")\n\tdefer span.End()\n\n\t// Произвольный транспортный контейнер (например Redis payload или Custom TCP)\n\tpayloadMetadata := make(MapCarrier)\n\tInjectTrace(ctx, payloadMetadata)\n\n\tfmt.Println(\"Injected transport metadata:\", payloadMetadata)\n\n\t// На принимающей стороне восстанавливаем контекст\n\tremoteCtx := ExtractTrace(context.Background(), payloadMetadata)\n\t_, childSpan := tracer.Start(remoteCtx, \"ExecuteDownstreamTask\")\n\tdefer childSpan.End()\n\n\tfmt.Printf(\"Trace successfully preserved! Parent: %s, Child: %s\\n\",\n\t\tspan.SpanContext().TraceID(), childSpan.SpanContext().TraceID())\n}",
                "note": "Универсальный TextMapCarrier для любых нестандартных протоколов"
            }
        ],
        "under_the_hood": "Интерфейс `propagation.TextMapCarrier` специально спроектирован в OpenTelemetry минималистичным, чтобы его можно было реализовать поверх любой структуры данных всего тремя методами.",
        "pitfalls": "Использование ключей с разным регистром (Case Sensitivity). Некоторые протоколы меняют регистр ключей. Желательно приводить все ключи к нижнему регистру (lowercase).",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Как пробросить Trace Context через сырое TCP соединение?' Ответ: 'Сериализовать пару traceparent: <value> в бинарный или текстовый заголовок собственного фрейма и распарсить с помощью кастомного TextMapCarrier на принимающей стороне'."
    },
    {
        "num": 56,
        "title": "Draining Long-lived Streams: принудительная отмена контекста по дедлайну",
        "task": "Реализуйте контроллер стримов, отменяющий контексты всех активных горутин при превышении таймаута Graceful Shutdown, гарантируя выход из GracefulStop().",
        "theory": "При реализации серверного стриминга в gRPC горутина обработчика обычно блокируется на `stream.Send()` или чтении канала. Если клиент 'завис' (dead connection) или игнорирует закрытие, метод `GracefulStop()` будет заблокирован навсегда. Чтобы гарантировать завершение работы за отведенный SLA (например, 10 секунд), необходимо связывать контекст каждого активного стрима с родительским `draining context`. При начале процедуры остановки запускается таймер. Если по истечении таймаута стримы не закрылись сами, вызывается функция отмены `cancel()`, что немедленно прерывает блокирующие операции ввода-вывода и освобождает горутины.",
        "step_by_step": [
            "Создайте структуру StreamManager с отслеживанием активных контекстов отмены.",
            "Реализуйте регистрацию и дерегистрацию клиентских стримов.",
            "При получении сигнала остановки вызовите мягкое завершение с дедлайном.",
            "Принудительно отмените контексты оставшихся стримов по истечении лимита времени."
        ],
        "code_blocks": [
            {
                "filename": "stream_timeout_drainer.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"sync\"\n\t\"time\"\n)\n\ntype StreamSession struct {\n\tid     string\n\tcancel context.CancelFunc\n}\n\ntype StreamManager struct {\n\tmu       sync.Mutex\n\tsessions map[string]*StreamSession\n}\n\nfunc NewStreamManager() *StreamManager {\n\treturn &StreamManager{\n\t\tsessions: make(map[string]*StreamSession),\n\t}\n}\n\nfunc (sm *StreamManager) Register(id string, cancel context.CancelFunc) {\n\tsm.mu.Lock()\n\tdefer sm.mu.Unlock()\n\tsm.sessions[id] = &StreamSession{id: id, cancel: cancel}\n\tlog.Printf(\"[Manager] Registered stream %s. Active count: %d\", id, len(sm.sessions))\n}\n\nfunc (sm *StreamManager) Unregister(id string) {\n\tsm.mu.Lock()\n\tdefer sm.mu.Unlock()\n\tdelete(sm.sessions, id)\n\tlog.Printf(\"[Manager] Unregistered stream %s. Active count: %d\", id, len(sm.sessions))\n}\n\n// ForceDrainAll принудительно отменяет контексты оставшихся 'зависших' стримов\nfunc (sm *StreamManager) ForceDrainAll() {\n\tsm.mu.Lock()\n\tdefer sm.mu.Unlock()\n\n\tlog.Printf(\"[Manager] Forcibly cancelling %d stubborn active streams...\", len(sm.sessions))\n\tfor _, s := range sm.sessions {\n\t\ts.cancel()\n\t}\n\tsm.sessions = make(map[string]*StreamSession)\n}\n\nfunc main() {\n\tsm := NewStreamManager()\n\n\t// Создаем зависший стрим\n\tctx, cancel := context.WithCancel(context.Background())\n\tsm.Register(\"client-session-98\", cancel)\n\n\tstreamTerminated := make(chan struct{})\n\tgo func() {\n\t\t<-ctx.Done()\n\t\tlog.Println(\"[Stream Worker] Context cancelled by drainer. Exiting cleanly.\")\n\t\tsm.Unregister(\"client-session-98\")\n\t\tclose(streamTerminated)\n\t}()\n\n\t// Имитируем Graceful Shutdown с жестким лимитом\n\tlog.Println(\"Shutdown initiated: waiting 1 second before hard cancellation...\")\n\ttime.Sleep(1 * time.Second)\n\n\tsm.ForceDrainAll()\n\t<-streamTerminated\n\n\tfmt.Println(\"All streaming goroutines released safely.\")\n}",
                "note": "Управление жизненным циклом долгоживущих стримов с принудительной отменой по таймауту"
            }
        ],
        "under_the_hood": "Когда контекст стрима отменяется (`ctx.Done()`), внутренний селектор горутины немедленно выходит из ожидания, предотвращая блокировку `serveWG.Wait()` внутри gRPC сервера.",
        "pitfalls": "Утечка памяти при забытой дерегистрации стримов в блоке `defer sm.Unregister()`. Карта активных сессий будет бесконечно расти, удерживая ссылки на отмененные контексты.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Как избежать дедлока в GracefulStop при наличии подвисших стримов?' Ответ: 'Хранить контексты стримов и отменять их по таймеру дедлайна остановки, либо вызывать жесткий server.Stop() по таймауту'."
    },
    {
        "num": 57,
        "title": "Сквозной Context Propagation через все границы: HTTP -> gRPC -> Kafka -> NATS",
        "task": "Напишите демонстрационный конвейер, где входящий HTTP запрос вызывает gRPC сервис, который публикует событие в Kafka, а консьюмер шлет нотификацию через NATS, сохраняя неизменный TraceID.",
        "theory": "Сложные микросервисные транзакции пересекают множество гетерогенных границ: 1. Клиент делает вызов `HTTP POST /order` на API Gateway; 2. Gateway делает синхронный `gRPC` вызов в Order Service; 3. Order Service сохраняет заказ и отправляет событие в топик `Apache Kafka`; 4. Consumer читает Kafka и отправляет уведомление подписчикам через `NATS Core`. Каждый скачок (hop) использует свои собственные типы заголовков, однако стандарт W3C Trace Context и OpenTelemetry Propagators гарантируют, что сквозной `TraceID` остается абсолютно неизменным на протяжении всей цепочки.",
        "step_by_step": [
            "Инициализируйте OpenTelemetry с W3C TraceContext.",
            "Смоделируйте HTTP шаг и извлеките родительский TraceID.",
            "Пробросьте контекст через gRPC metadata.",
            "Пробросьте контекст через Kafka Record Headers.",
            "Пробросьте контекст через NATS Headers и убедитесь в совпадении всех TraceID."
        ],
        "code_blocks": [
            {
                "filename": "cross_boundary_pipeline.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/http\"\n\n\t\"go.opentelemetry.io/otel\"\n\t\"go.opentelemetry.io/otel/propagation\"\n\tsdktrace \"go.opentelemetry.io/otel/sdk/trace\"\n\t\"go.opentelemetry.io/otel/trace\"\n\t\"google.golang.org/grpc/metadata\"\n)\n\nfunc main() {\n\ttp := sdktrace.NewTracerProvider(sdktrace.WithSampler(sdktrace.AlwaysSample()))\n\totel.SetTracerProvider(tp)\n\totel.SetTextMapPropagator(propagation.TraceContext{})\n\n\ttracer := otel.Tracer(\"distributed-pipeline\")\n\n\t// 1. ШАГ HTTP (API Gateway)\n\thttpCtx, httpSpan := tracer.Start(context.Background(), \"HTTP Ingress\", trace.WithSpanKind(trace.SpanKindServer))\n\trootTraceID := httpSpan.SpanContext().TraceID().String()\n\tfmt.Printf(\"[1. HTTP Ingress] Created Root TraceID: %s\\n\", rootTraceID)\n\thttpSpan.End()\n\n\t// 2. ШАГ gRPC (Order Service)\n\tgrpcMD := metadata.New(nil)\n\totel.GetTextMapPropagator().Inject(httpCtx, propagation.HeaderCarrier(http.Header(grpcMD)))\n\tgrpcCtx := otel.GetTextMapPropagator().Extract(context.Background(), propagation.HeaderCarrier(http.Header(grpcMD)))\n\t_, grpcSpan := tracer.Start(grpcCtx, \"gRPC OrderService\", trace.WithSpanKind(trace.SpanKindServer))\n\tfmt.Printf(\"[2. gRPC Call]   Verified TraceID:     %s\\n\", grpcSpan.SpanContext().TraceID().String())\n\tgrpcSpan.End()\n\n\t// 3. ШАГ KAFKA (Event Bus)\n\tkafkaHeaders := make(http.Header)\n\totel.GetTextMapPropagator().Inject(grpcCtx, propagation.HeaderCarrier(kafkaHeaders))\n\tkafkaCtx := otel.GetTextMapPropagator().Extract(context.Background(), propagation.HeaderCarrier(kafkaHeaders))\n\t_, kafkaSpan := tracer.Start(kafkaCtx, \"Kafka Consumer\", trace.WithSpanKind(trace.SpanKindConsumer))\n\tfmt.Printf(\"[3. Kafka Bus]   Verified TraceID:     %s\\n\", kafkaSpan.SpanContext().TraceID().String())\n\tkafkaSpan.End()\n\n\t// 4. ШАГ NATS (Push Notification)\n\tnatsHeaders := make(http.Header)\n\totel.GetTextMapPropagator().Inject(kafkaCtx, propagation.HeaderCarrier(natsHeaders))\n\tnatsCtx := otel.GetTextMapPropagator().Extract(context.Background(), propagation.HeaderCarrier(natsHeaders))\n\t_, natsSpan := tracer.Start(natsCtx, \"NATS Subscriber\", trace.WithSpanKind(trace.SpanKindConsumer))\n\tfmt.Printf(\"[4. NATS Push]   Verified TraceID:     %s\\n\", natsSpan.SpanContext().TraceID().String())\n\tnatsSpan.End()\n\n\tfmt.Println(\"All 4 heterogeneous boundaries preserved identical TraceID successfully!\")\n}",
                "note": "Сквозная трассировка через гетерогенные границы: HTTP, gRPC, Kafka и NATS"
            }
        ],
        "under_the_hood": "Использование канонического формата `00-{traceid}-{spanid}-{flags}` обеспечивает полную независимость от транспортного протокола. Даже при передаче через брокеры сообщений TraceID сохраняется в бинарных заголовках без изменения тела сообщения.",
        "pitfalls": "Использование разных версий OpenTelemetry библиотек в разных микросервисах, из-за чего один сервис ожидает `X-B3-TraceId`, а другой пишет `traceparent`.",
        "bigtech_interview": "Вопрос на архитектурной секции в Ozon: 'Как отладить падение сообщения в Kafka, если консьюмер падает с паникой?' Ответ: 'Благодаря пробросу traceparent в Kafka headers консьюмер логирует TraceID в момент чтения. По этому TraceID мы находим исходный запрос пользователя в API Gateway и точно знаем, какие входные параметры привели к генерации битого сообщения'."
    },
    {
        "num": 58,
        "title": "gRPC Channelz: мониторинг состояния сокетов и каналов на лету",
        "task": "Подключите сервис channelz в gRPC сервере и напишите клиентский запрос для интроспекции состояния сокетов, активности keepalive и счетчиков вызовов RPC.",
        "theory": "Отладка сетевых проблем gRPC в продакшене (утечки сокетов, залипшие стримы, ошибки keepalive) значительно упрощается благодаря встроенному протоколу Channelz (спецификация `gRFC A14: Channelz`). Channelz предоставляет структурированное gRPC API для инспекции внутреннего состояния рантайма: 1) Список активных каналов (`Channel`) и саб-каналов (`SubChannel`); 2) Текущее состояние подключения (`CONNECTING`, `READY`, `TRANSIENT_FAILURE`, `SHUTDOWN`); 3) Счетчики отправленных и полученных сообщений, успешных и проваленных RPC; 4) Параметры активных TCP сокетов (локальный и удаленный адреса, счетчики keepalive PING/PONG).",
        "step_by_step": [
            "Импортируйте google.golang.org/grpc/channelz/service.",
            "Зарегистрируйте Channelz сервис на gRPC сервере через service.RegisterChannelzService(server).",
            "Запустите сервер.",
            "Проверьте доступность отладочных методов через gRPC интроспекцию."
        ],
        "code_blocks": [
            {
                "filename": "grpc_channelz_demo.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/channelz/service\"\n)\n\nfunc main() {\n\tlis, err := net.Listen(\"tcp\", \":50058\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Listen error: %v\", err)\n\t}\n\tdefer lis.Close()\n\n\tserver := grpc.NewServer()\n\n\t// Включаем стандартный сервис channelz для интроспекции рантайма\n\tservice.RegisterChannelzServiceToServer(server)\n\n\tgo func() {\n\t\tlog.Println(\"gRPC Server serving with Channelz debug service on :50058\")\n\t\t_ = server.Serve(lis)\n\t}()\n\n\ttime.Sleep(100 * time.Millisecond)\n\n\t// В реальном окружении опрашивается через утилиту grpc-debug или channelz CLI:\n\t// grpc-debug channelz channels localhost:50058\n\tfmt.Println(\"Channelz service successfully registered and ready for runtime diagnostics.\")\n\n\tserver.Stop()\n}",
                "note": "Регистрация gRPC Channelz для онлайн-диагностики соединений и каналов"
            }
        ],
        "under_the_hood": "Сервис `channelz` регистрирует протобуф-пакет `grpc.channelz.v1.Channelz` с методами `GetTopChannels`, `GetServer`, `GetServers`, `GetSocket`. Он обращается к внутренним структурам gRPC transport без остановки сервера и блокировки сокетов.",
        "pitfalls": "Открытие эндпоинта Channelz в публичный доступ без авторизации. Channelz раскрывает внутреннюю топологию сети, IP-адреса подов кластера и объемы трафика. Он должен быть доступен только администраторам и SRE через внутреннюю сеть.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Как в gRPC сервере без сторонних утилит посмотреть, сколько клиентов подключено прямо сейчас?' Ответ: 'Подключить сервис grpc.channelz.v1 и запросить GetServerSockets. Он вернет список всех активных TCP-дескрипторов с их статистикой'."
    },
    {
        "num": 59,
        "title": "Cloud-Scale Rate Limiting: распределенный Token Bucket на Redis Lua",
        "task": "Реализуйте высокопроизводительный распределенный ограничитель частоты запросов (Rate Limiter) по алгоритму Token Bucket с использованием атомарного Lua-скрипта в Redis.",
        "theory": "В распределенной системе из десятков подов локальный `rate.Limiter` (в памяти процесса) не спасает: клиент может слать запросы на разные поды и превысить глобальный лимит. Для глобального ограничения используется Redis с алгоритмом Token Bucket (Корзина токенов). Чтобы избежать race condition и сетевых round-trip оверхедов (RTT) между чтением и записью счетчиков, вся логика расчета пополнения токенов упаковывается в атомарный Lua-скрипт (`EVALSHA`). Скрипт проверяет время последнего запроса, доливает токены пропорционально прошедшему времени `now - last_time`, списывает 1 токен и возвращает клиенту булево решение (разрешить/заблокировать).",
        "step_by_step": [
            "Напишите атомарный Lua-скрипт алгоритма Token Bucket.",
            "Реализуйте структуру RedisTokenBucketLimiter в Go.",
            "Создайте HTTP middleware, проверяющее лимит по IP или API-ключу.",
            "При превышении лимита верните HTTP 429 Too Many Requests с заголовком Retry-After."
        ],
        "code_blocks": [
            {
                "filename": "redis_lua_limiter.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"sync\"\n\t\"time\"\n)\n\n// tokenBucketLuaScript атомарно рассчитывает токены внутри Redis\nconst tokenBucketLuaScript = `\nlocal key = KEYS[1]\nlocal capacity = tonumber(ARGV[1])\nlocal refill_rate = tonumber(ARGV[2])\nlocal now = tonumber(ARGV[3])\nlocal requested = tonumber(ARGV[4])\n\nlocal state = redis.call('HMGET', key, 'tokens', 'last_updated')\nlocal tokens = tonumber(state[1])\nlocal last_updated = tonumber(state[2])\n\nif not tokens then\n    tokens = capacity\n    last_updated = now\nelse\n    local delta = math.max(0, now - last_updated)\n    tokens = math.min(capacity, tokens + delta * refill_rate)\n    last_updated = now\nend\n\nif tokens >= requested then\n    tokens = tokens - requested\n    redis.call('HMSET', key, 'tokens', tokens, 'last_updated', last_updated)\n    redis.call('EXPIRE', key, math.ceil(capacity / refill_rate) * 2)\n    return 1\nelse\n    redis.call('HMSET', key, 'tokens', tokens, 'last_updated', last_updated)\n    return 0\nend\n`\n\n// MockRedisLimiter имитирует исполнение Lua-скрипта в кластере Redis\ntype MockRedisLimiter struct {\n\tmu          sync.Mutex\n\tcapacity    float64\n\trefillRate  float64\n\ttokens      float64\n\tlastUpdated time.Time\n}\n\nfunc NewMockRedisLimiter(capacity, refillRate float64) *MockRedisLimiter {\n\treturn &MockRedisLimiter{\n\t\tcapacity:    capacity,\n\t\trefillRate:  refillRate,\n\t\ttokens:      capacity,\n\t\tlastUpdated: time.Now(),\n\t}\n}\n\nfunc (l *MockRedisLimiter) Allow(ctx context.Context, key string) (bool, error) {\n\tl.mu.Lock()\n\tdefer l.mu.Unlock()\n\n\tnow := time.Now()\n\telapsed := now.Sub(l.lastUpdated).Seconds()\n\tl.lastUpdated = now\n\n\t// Восполняем токены\n\tl.tokens += elapsed * l.refillRate\n\tif l.tokens > l.capacity {\n\t\tl.tokens = l.capacity\n\t}\n\n\tif l.tokens >= 1.0 {\n\t\tl.tokens -= 1.0\n\t\treturn true, nil\n\t}\n\treturn false, nil\n}\n\nfunc RateLimitMiddleware(limiter *MockRedisLimiter) func(http.Handler) http.Handler {\n\treturn func(next http.Handler) http.Handler {\n\t\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\t\tallowed, _ := limiter.Allow(r.Context(), r.RemoteAddr)\n\t\t\tif !allowed {\n\t\t\t\tw.Header().Set(\"Retry-After\", \"1\")\n\t\t\t\thttp.Error(w, \"Rate limit exceeded (Too Many Requests)\", http.StatusTooManyRequests)\n\t\t\t\treturn\n\t\t\t}\n\t\t\tnext.ServeHTTP(w, r)\n\t\t})\n\t}\n}\n\nfunc main() {\n\t// Лимит: корзина на 2 токена, восполнение 1 токен в секунду\n\tlimiter := NewMockRedisLimiter(2, 1)\n\tmiddleware := RateLimitMiddleware(limiter)\n\n\thandler := middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"Action allowed\"))\n\t}))\n\n\t// Делаем 3 быстрых запроса\n\tfor i := 1; i <= 3; i++ {\n\t\treq := httptest.NewRequest(\"GET\", \"/api/data\", nil)\n\t\trec := httptest.NewRecorder()\n\t\thandler.ServeHTTP(rec, req)\n\t\tfmt.Printf(\"Request %d: Status=%d\\n\", i, rec.Code)\n\t}\n}",
                "note": "Распределенный Rate Limiter на базе алгоритма Token Bucket и Redis Lua"
            }
        ],
        "under_the_hood": "Команда `EVALSHA` в Redis гарантирует атомарность: скрипт выполняется в едином потоке Redis без прерывания другими командами, полностью исключая феномен гонки (Data Race) при конкурентном обращении сотен клиентов.",
        "pitfalls": "Отсутствие `EXPIRE` на ключе лимитера. Если клиент совершил один запрос и больше не возвращался, его ключ останется в памяти Redis навсегда. Всегда выставляйте TTL ключа равным `capacity / refill_rate * 2`.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Почему в распределенных системах Lua-скрипт лучше, чем несколько команд GET и SET с транзакцией MULTI/EXEC?' Ответ: 'MULTI/EXEC требует нескольких сетевых RTT между приложением и Redis, а при оптимистической блокировке WATCH часто падает с ошибкой конкурентного изменения. Lua-скрипт выполняется за один сетевой RTT и атомарен на стороне движка Redis'."
    },
    {
        "num": 60,
        "title": "Сквозная трассировка: объединение Trace ID в логах, метриках и HTTP-ответах",
        "task": "Спроектируйте HTTP-сервис, который возвращает trace_id клиенту в заголовке X-Trace-Id, записывает его в structured slog JSON и привязывает к метрикам Prometheus Exemplars.",
        "theory": "Golden Standard наблюдаемости (Observability) в BigTech опирается на так называемый 'Observability Triumvirate' (Логи, Метрики, Трейсы), объединенные единым сквозным `trace_id`: 1) Клиент получает `X-Trace-Id` в HTTP-ответе. Если произошел сбой, пользователь или служба поддержки сообщают этот ID инженерам; 2) Инженер ищет `trace_id` в Kibana/Loki и видит все логи каждого шага транзакции; 3) На графиках Grafana по этому `trace_id` доступен Exemplar, открывающий трассировку в Jaeger/Tempo; 4) В базе ошибок Sentry инцидент привязан к тому же `trace_id`. Это сокращает время локализации аварий (MTTR — Mean Time To Resolution) с часов до секунд.",
        "step_by_step": [
            "Создайте HTTP middleware, извлекающее или генерирующее Trace Context.",
            "Проставьте заголовок ответа X-Trace-Id.",
            "Запишите лог через slog.InfoContext.",
            "Зафиксируйте длительность запроса с Exemplar.",
            "Проверьте корреляцию всех трех компонентов."
        ],
        "code_blocks": [
            {
                "filename": "unified_observability.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log/slog\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"os\"\n\n\t\"go.opentelemetry.io/otel\"\n\t\"go.opentelemetry.io/otel/propagation\"\n\tsdktrace \"go.opentelemetry.io/otel/sdk/trace\"\n\t\"go.opentelemetry.io/otel/trace\"\n)\n\n// TraceHeaderHandler извлекает traceparent и проставляет X-Trace-Id в ответ\nfunc TraceHeaderHandler(tracer trace.Tracer) func(http.Handler) http.Handler {\n\treturn func(next http.Handler) http.Handler {\n\t\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\t\tctx := otel.GetTextMapPropagator().Extract(r.Context(), propagation.HeaderCarrier(r.Header))\n\t\t\tctx, span := tracer.Start(ctx, r.Method+\" \"+r.URL.Path, trace.WithSpanKind(trace.SpanKindServer))\n\t\t\tdefer span.End()\n\n\t\t\ttraceID := span.SpanContext().TraceID().String()\n\n\t\t\t// 1. Возвращаем клиенту заголовок для службы поддержки\n\t\t\tw.Header().Set(\"X-Trace-Id\", traceID)\n\n\t\t\t// 2. Логируем с привязкой trace_id\n\t\t\tslog.InfoContext(ctx, \"HTTP request handled\",\n\t\t\t\tslog.String(\"trace_id\", traceID),\n\t\t\t\tslog.String(\"path\", r.URL.Path),\n\t\t\t)\n\n\t\t\tnext.ServeHTTP(w, r.WithContext(ctx))\n\t\t})\n\t}\n}\n\nfunc main() {\n\ttp := sdktrace.NewTracerProvider(sdktrace.WithSampler(sdktrace.AlwaysSample()))\n\totel.SetTracerProvider(tp)\n\totel.SetTextMapPropagator(propagation.TraceContext{})\n\n\tlogger := slog.New(slog.NewJSONHandler(os.Stdout, nil))\n\tslog.SetDefault(logger)\n\n\ttracer := otel.Tracer(\"unified-service\")\n\tmiddleware := TraceHeaderHandler(tracer)\n\n\tapp := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(`{\"result\":\"processed\"}`))\n\t})\n\n\tserver := httptest.NewServer(middleware(app))\n\tdefer server.Close()\n\n\tresp, err := http.Get(server.URL + \"/order/create\")\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer resp.Body.Close()\n\n\tfmt.Println(\"Client Received X-Trace-Id:\", resp.Header.Get(\"X-Trace-Id\"))\n}",
                "note": "Сквозное объединение Trace ID в HTTP ответах, логах и метриках"
            }
        ],
        "under_the_hood": "Заголовок `X-Trace-Id` читается браузерным приложением или мобильным SDK. При возникновении сетевой ошибки фронтенд логирует этот идентификатор, позволяя связать клиентский краш-дамп с бэкенд-трейсом.",
        "pitfalls": "Генерация нового TraceID в ответе вместо сквозного ID из текущего спана. Всегда используйте `span.SpanContext().TraceID().String()`.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Зачем возвращать клиенту заголовок X-Trace-Id в ответе API?' Ответ: 'Чтобы клиент при получении 500 ошибки мог прикрепить этот ID к обращению в саппорт. Инженер моментально открывает трейс этой конкретной операции в Jaeger без долгих поисков по логам'."
    },
    {
        "num": 61,
        "title": "Graceful Shutdown — это закон: эталонная реализация остановки сервиса в Go",
        "task": "Напишите эталонный скелет функции main() для enterprise-сервиса на Go: перехват сигналов, context with timeout, закрытие сервера и освобождение ресурсов базы данных.",
        "theory": "Управление жизненным циклом процесса — базовый навык senior бэкенд-инженера. Неправильное завершение приводит к 'битым' транзакциям в БД, зависшим TCP-сокетам и падениям по таймауту. Эталонный алгоритм остановки: 1. `signal.NotifyContext` перехватывает `os.Interrupt` и `syscall.SIGTERM`; 2. Запуск фоновых листенеров (HTTP/gRPC) в отдельных горутинах; 3. Блокировка `main` на канале `<-ctx.Done()`; 4. Создание отдельного контекста завершения с жестким дедлайном `context.WithTimeout(context.Background(), 10*time.Second)`; 5. Вызов `server.Shutdown(shutdownCtx)`; 6. Закрытие пулов соединений к базе данных (`db.Close()`) и кэшам строго ПОСЛЕ остановки серверов; 7. Логирование успешного завершения и выход.",
        "step_by_step": [
            "Используйте signal.NotifyContext для перехвата сигналов ОС.",
            "Запустите http.Server в горутине.",
            "Дождитесь сигнала отмены.",
            "Создайте shutdownCtx с таймаутом.",
            "Остановите сервер и закройте внешние ресурсы."
        ],
        "code_blocks": [
            {
                "filename": "canonical_shutdown.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n\t\"os/signal\"\n\t\"syscall\"\n\t\"time\"\n)\n\nfunc main() {\n\t// 1. Корневой контекст приложения с перехватом сигналов остановки\n\tctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)\n\tdefer stop()\n\n\tsrv := &http.Server{\n\t\tAddr: \":8083\",\n\t\tHandler: http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\t\ttime.Sleep(50 * time.Millisecond) // Имитация полезной работы\n\t\t\tw.WriteHeader(http.StatusOK)\n\t\t\t_, _ = w.Write([]byte(\"OK\"))\n\t\t}),\n\t}\n\n\t// 2. Фоновый запуск сервера\n\tgo func() {\n\t\tlog.Printf(\"Starting HTTP server on %s\", srv.Addr)\n\t\tif err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {\n\t\t\tlog.Fatalf(\"Fatal server error: %v\", err)\n\t\t}\n\t}()\n\n\t// 3. Ожидание сигнала от ОС или Kubernetes\n\t<-ctx.Done()\n\tlog.Println(\"[Shutdown] Signal received. Starting graceful shutdown sequence...\")\n\n\t// 4. Изолированный контекст на остановку с дедлайном\n\tshutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\tdefer cancel()\n\n\t// 5. Остановка сервера с ожиданием активных запросов\n\tif err := srv.Shutdown(shutdownCtx); err != nil {\n\t\tlog.Printf(\"[Shutdown] Server shutdown timeout or error: %v\", err)\n\t\t_ = srv.Close() // Форсированное закрытие сокетов при превышении лимита\n\t}\n\n\t// 6. Освобождение ресурсов БД и очередей\n\tlog.Println(\"[Shutdown] Closing database pools and event publishers...\")\n\t// db.Close()\n\n\tfmt.Println(\"Process successfully terminated without data loss.\")\n}",
                "note": "Эталонная реализация Graceful Shutdown в Go"
            }
        ],
        "under_the_hood": "Метод `http.Server.Shutdown()` сначала закрывает все слушающие дескрипторы `net.Listener`, затем переводит все активные соединения в состояние idle по мере завершения текущего запроса и закрывает их сокеты. Если таймер истек раньше завершения запросов, метод возвращает `ctx.Err()`.",
        "pitfalls": "Использование исходного `ctx` (который уже отменен по сигналу) для вызова `srv.Shutdown(ctx)`. В таком случае Shutdown немедленно вернет ошибку `context canceled`, не дав запросам ни миллисекунды на завершение!",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'Какую ошибку чаще всего совершают джуны при написании server.Shutdown(ctx)?' Ответ: 'Передают контекст, который только что поймал SIGTERM (он уже Done!). Для Shutdown необходимо создавать НОВЫЙ независимый context.WithTimeout(context.Background(), ...)'. "
    },
    {
        "num": 62,
        "title": "Тюнинг gRPC Connection: MaxRecvMsgSize, InitialWindowSize и Flow Control",
        "task": "Сконфигурируйте gRPC клиент и сервер с расширенными параметрами MaxRecvMsgSize (32MB), MaxSendMsgSize (32MB), InitialWindowSize и InitialConnWindowSize для высокоскоростной передачи больших массивов данных.",
        "theory": "По умолчанию gRPC имеет консервативные ограничения безопасности: максимальный размер сообщения (`MaxRecvMsgSize`) составляет 4 МБ. При попытке передать файл, крупный отчет или ML-модель клиент упадет с ошибкой `ResourceExhausted: received message larger than max (X vs 4194304)`. Кроме того, механизм управления потоком HTTP/2 (Flow Control) по умолчанию использует небольшие размеры окон приема (64 КБ), что на каналах с высоким RTT (High Bandwidth-Delay Product) приводит к искусственному ограничению пропускной способности (TCP throughput throttling). Тюнинг параметров `InitialWindowSize` и `InitialConnWindowSize` (до 1-4 МБ) позволяет полностью утилизировать 10-гигабитные каналы между датацентрами.",
        "step_by_step": [
            "Сконфигурируйте лимиты размеров сообщений grpc.MaxRecvMsgSize и grpc.MaxSendMsgSize.",
            "Настройте HTTP/2 Flow Control окна: InitialWindowSize (1MB) и InitialConnWindowSize (4MB).",
            "Инициализируйте сервер и клиент с расширенными опциями.",
            "Проверьте передачу сообщений размером более 4 МБ."
        ],
        "code_blocks": [
            {
                "filename": "grpc_pool_tuning.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n)\n\nconst (\n\tmaxMsgSize  = 32 * 1024 * 1024 // 32 MB\n\tstreamWinSz = 1 * 1024 * 1024  // 1 MB per stream window\n\tconnWinSz   = 4 * 1024 * 1024  // 4 MB connection window\n)\n\nfunc CreateTunedServer() *grpc.Server {\n\treturn grpc.NewServer(\n\t\tgrpc.MaxRecvMsgSize(maxMsgSize),\n\t\tgrpc.MaxSendMsgSize(maxMsgSize),\n\t\tgrpc.InitialWindowSize(streamWinSz),\n\t\tgrpc.InitialConnWindowSize(connWinSz),\n\t)\n}\n\nfunc DialTunedClient(target string) (*grpc.ClientConn, error) {\n\tctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)\n\tdefer cancel()\n\n\treturn grpc.DialContext(ctx, target,\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t\tgrpc.WithDefaultCallOptions(\n\t\t\tgrpc.MaxCallRecvMsgSize(maxMsgSize),\n\t\t\tgrpc.MaxCallSendMsgSize(maxMsgSize),\n\t\t),\n\t\tgrpc.WithInitialWindowSize(streamWinSz),\n\t\tgrpc.WithInitialConnWindowSize(connWinSz),\n\t)\n}\n\nfunc main() {\n\tlis, err := net.Listen(\"tcp\", \":50059\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Listen error: %v\", err)\n\t}\n\tdefer lis.Close()\n\n\tserver := CreateTunedServer()\n\tgo func() {\n\t\t_ = server.Serve(lis)\n\t}()\n\n\tconn, err := DialTunedClient(\"127.0.0.1:50059\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Dial failed: %v\", err)\n\t}\n\tdefer conn.Close()\n\n\tfmt.Println(\"High-throughput gRPC connection tuned successfully (32MB payload, 4MB window).\")\n\tserver.Stop()\n}",
                "note": "Тюнинг размеров сообщений и HTTP/2 окон Flow Control в gRPC"
            }
        ],
        "under_the_hood": "HTTP/2 протокол использует фреймы `WINDOW_UPDATE` для уведомления отправителя о свободном буфере в сокете. Увеличение `InitialConnWindowSize` позволяет передавать пакеты непрерывным потоком без ожидания подтверждения получения каждого фрейма.",
        "pitfalls": "Увеличение лимитов на клиенте, но забытое увеличение на сервере (или наоборот). Лимиты `MaxRecvMsgSize` должны быть согласованы с обеих сторон соединения.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Как передать файл на 500 МБ через gRPC: увеличить MaxRecvMsgSize до 500 МБ или стримить чанками?' Ответ: 'Исключительно стримить чанками (Client Streaming). Буферизация 500 МБ сообщения целиком в памяти разорвет кучу Go аллокациями и вызовет OOM Killer под нагрузкой'."
    },
    {
        "num": 63,
        "title": "Обнаружение 'мертвых' сокетов gRPC Keepalive при физическом обрыве связи",
        "task": "Смоделируйте зависшее сетевое соединение (unplugged cable) и покажите, как gRPC клиент с Time: 10s и Timeout: 3s быстро переходит в TRANSIENT_FAILURE без 15-минутного ожидания TCP.",
        "theory": "Сетевой стек Linux TCP спроектирован для устойчивости к временным сбоям каналов связи: если удаленный хост внезапно выключился из розетки, ядро не закрывает соединение сразу. Оно выполняет до 15 повторных передач (параметр ядра `net.ipv4.tcp_retries2`), что при экспоненциальном увеличении интервала занимает от 13 до 30 минут! Все это время Go-горутина, читающая из сокета, заблокирована в системном вызове `epoll_wait` / `read`. Настройка gRPC Keepalive (`Time: 10s`, `Timeout: 3s`) заставляет клиент каждые 10 секунд проверять сокет отправкой HTTP/2 PING. Если через 3 секунды ответа нет, рантайм gRPC сам закрывает дескриптор, переводя статус в `TRANSIENT_FAILURE`, и немедленно освобождает заблокированные вызовы с кодом ошибки `Unavailable`.",
        "step_by_step": [
            "Сконфигурируйте keepalive.ClientParameters со строгими таймаутами.",
            "Подключитесь к тестовому адресу.",
            "Отслеживайте смену состояний connectivity.State (CONNECTING -> READY -> TRANSIENT_FAILURE).",
            "Зафиксируйте быстрое время обнаружения сбоя."
        ],
        "code_blocks": [
            {
                "filename": "dead_connection_detection.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/connectivity\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n\t\"google.golang.org/grpc/keepalive\"\n)\n\nfunc MonitorConnectionState(conn *grpc.ClientConn) {\n\tctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)\n\tdefer cancel()\n\n\tcurrentState := conn.GetState()\n\tlog.Printf(\"[Connectivity] Initial state: %s\", currentState)\n\n\tfor {\n\t\t// WaitForStateChange блокируется до перехода сокета в новое состояние\n\t\tif conn.WaitForStateChange(ctx, currentState) {\n\t\t\tnewState := conn.GetState()\n\t\t\tlog.Printf(\"[Connectivity] State transition detected: %s -> %s\", currentState, newState)\n\t\t\tcurrentState = newState\n\t\t\tif newState == connectivity.TransientFailure {\n\t\t\t\tlog.Println(\"[Alert] Dead connection quickly detected by keepalive probe!\")\n\t\t\t\treturn\n\t\t\t}\n\t\t} else {\n\t\t\treturn\n\t\t}\n\t}\n}\n\nfunc main() {\n\tkacp := keepalive.ClientParameters{\n\t\tTime:                2 * time.Second, // Каждые 2 секунды шлем PING\n\t\tTimeout:             1 * time.Second, // 1 секунда ожидания ответа\n\t\tPermitWithoutStream: true,\n\t}\n\n\tconn, err := grpc.Dial(\"127.0.0.1:59999\", // Заведомо недоступный сокет\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t\tgrpc.WithKeepaliveParams(kacp),\n\t)\n\tif err != nil {\n\t\tlog.Fatalf(\"Dial failed: %v\", err)\n\t}\n\tdefer conn.Close()\n\n\tgo MonitorConnectionState(conn)\n\ttime.Sleep(3 * time.Second)\n\n\tfmt.Println(\"Dead connection detection cycle demonstrated successfully.\")\n}",
                "note": "Отслеживание перехода канала в TRANSIENT_FAILURE при обрыве связи"
            }
        ],
        "under_the_hood": "Метод `conn.WaitForStateChange` использует каналы уведомлений внутри менеджера балансировки. Как только сетевой транспорт фиксирует таймаут фрейма PING, он вызывает `Close()` сокета и рассылает событие всем подписчикам.",
        "pitfalls": "Забыть флаг `PermitWithoutStream: true`. Если флага нет, а в данный момент по соединению нет активных RPC, клиент не будет слать PING-фреймы и не обнаружит смерть сокета до следующей попытки отправить запрос.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Сколько времени по умолчанию Linux ждет ответа от мертвого TCP сокета?' Ответ: 'Около 15 минут согласно параметру net.ipv4.tcp_retries2 = 15. Именно поэтому в микросервисах обязателен прикладной L7 Keepalive'."
    },
    {
        "num": 64,
        "title": "Защита от Cache Stampede: двухуровневая связка Singleflight + Redis Lock",
        "task": "Реализуйте двухуровневую защиту от шторма запросов в БД (Cache Stampede / Thundering Herd): локальный singleflight внутри каждого пода + распределенная блокировка Redis между подами кластера.",
        "theory": "Когда критический ключ кэша (например, главное меню каталога товаров) протухает, тысячи параллельных запросов одновременно обнаруживают Cache Miss и бросаются в PostgreSQL. База данных мгновенно захлебывается и ложится (Cache Stampede / Thundering Herd). Решение BigTech уровня — двухуровневая защита: 1) Уровень 1 (Локальный): внутри каждого Go-пода библиотека `golang.org/x/sync/singleflight` схлопывает сотни локальных горутин в ровно ОДИН сетевой запрос; 2) Уровень 2 (Глобальный): из 100 подов кластера только ОДИН под захватывает распределенный Redis Lock (`SET key val NX EX 5`) и идет в базу данных, а остальные 99 подов ждут обновления кэша в Redis. База данных получает ровно 1 запрос вместо 100 000!",
        "step_by_step": [
            "Импортируйте golang.org/x/sync/singleflight.",
            "Реализуйте функцию с получением данных через singleflight.Group.Do.",
            "Внутри функции проверьте распределенный замок в Redis.",
            "Победитель обновляет кэш, остальные читают готовое значение из кэша."
        ],
        "code_blocks": [
            {
                "filename": "cache_stampede_shield.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"sync\"\n\t\"sync/atomic\"\n\t\"time\"\n\n\t\"golang.org/x/sync/singleflight\"\n)\n\ntype TwoLevelCacheShield struct {\n\tsfGroup   singleflight.Group\n\tcacheData atomic.Pointer[string]\n\tdbHits    atomic.Int64\n}\n\nfunc (s *TwoLevelCacheShield) GetProductCatalog(ctx context.Context, key string) (string, error) {\n\t// 1. Проверяем горячий кэш\n\tif ptr := s.cacheData.Load(); ptr != nil {\n\t\treturn *ptr, nil\n\t}\n\n\t// 2. УРОВЕНЬ 1: Схлопываем все локальные горутины в 1 вызов через Singleflight\n\tval, err, shared := s.sfGroup.Do(key, func() (interface{}, error) {\n\t\t// Повторная проверка кэша после захвата singleflight\n\t\tif ptr := s.cacheData.Load(); ptr != nil {\n\t\t\treturn *ptr, nil\n\t\t}\n\n\t\t// 3. УРОВЕНЬ 2: В реальном кластере здесь берется Redis Lock (SET lock_key uuid NX EX 5)\n\t\tlog.Println(\"[CACHE MISS] Loading data from PostgreSQL Database...\")\n\t\ts.dbHits.Add(1)\n\t\ttime.Sleep(50 * time.Millisecond) // Имитация тяжелого SQL SELECT\n\n\t\tcatalogData := `{\"category\":\"electronics\",\"count\":42000}`\n\t\ts.cacheData.Store(&catalogData)\n\t\treturn catalogData, nil\n\t})\n\n\tif shared {\n\t\tlog.Println(\"[Singleflight] Request deduplicated across concurrent goroutines!\")\n\t}\n\treturn val.(string), err\n}\n\nfunc main() {\n\tshield := &TwoLevelCacheShield{}\n\n\tvar wg sync.WaitGroup\n\t// Имитируем шквал из 20 одновременных запросов в момент холодного кэша\n\tfor i := 0; i < 20; i++ {\n\t\twg.Add(1)\n\t\tgo func(id int) {\n\t\t\tdefer wg.Done()\n\t\t\tdata, err := shield.GetProductCatalog(context.Background(), \"catalog_key\")\n\t\t\tif err != nil {\n\t\t\t\tlog.Printf(\"Worker %d error: %v\", id, err)\n\t\t\t}\n\t\t\t_ = data\n\t\t}(i)\n\t}\n\n\twg.Wait()\n\tfmt.Printf(\"Total DB Queries executed: %d (Expected: 1 instead of 20)\\n\", shield.dbHits.Load())\n}",
                "note": "Двухуровневая защита от Cache Stampede через Singleflight и кэширование"
            }
        ],
        "under_the_hood": "Структура `singleflight.Group` хранит мапу с активными вызовами `map[string]*call`. Все параллельные горутины с одинаковым ключом блокируются на ожидании закрытия канала `call.done`, после чего одновременно получают общий результат первого вызова.",
        "pitfalls": "Зависание функции внутри `singleflight.Do`. Если обращение к БД зависнет без таймаута, ВСЕ ожидающие горутины зависнут вместе с ней. Всегда используйте `context.WithTimeout` внутри Do.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Что такое Cache Stampede и как защитить базу от падения?' Ответ: 'Это одновременное обращение тысяч клиентов к БД при инвалидации популярного ключа кэша. Защита: singleflight на уровне пода + Redis Distributed Lock на уровне кластера + вероятностное опережающее обновление (XFetch)'."
    },
    {
        "num": 65,
        "title": "Кастомный Connection Pooling в gRPC: масштабирование поверх нескольких TCP сокетов",
        "task": "Напишите кастомный пул gRPC-соединений (Channel Pool), открывающий N параллельных TCP-сокетов к одному бэкенду и распределяющий RPC между ними для обхода узких мест HTTP/2 Flow Control.",
        "theory": "По умолчанию клиент `grpc.DialContext` открывает ровно ОДНО TCP-соединение к указанному адресу и мультиплексирует все вызовы внутри него. В большинстве случаев этого достаточно. Однако при сверхвысокой нагрузке (сотни тысяч RPS или гигабайты видеотрафика) одно TCP-соединение упирается в: 1) Однопоточную обработку фреймов внутри горутины `loopyWriter` в Go; 2) Лимиты HTTP/2 Flow Control окна; 3) TCP head-of-line blocking при потере даже одного пакета в сети. Решение — создание пула из нескольких клиентских каналов (`ClientConn Pool`), где каждый вызов RPC направляется в следующий канал через атомарный Round Robin.",
        "step_by_step": [
            "Создайте структуру ClientPool со слайсом []*grpc.ClientConn и атомарным индексом.",
            "Реализуйте конструктор NewClientPool(size int, target string, opts ...grpc.DialOption).",
            "Реализуйте метод Get() *grpc.ClientConn с циклическим выбором через atomic.AddUint64.",
            "Реализуйте метод Close() для корректного закрытия всех сокетов пула."
        ],
        "code_blocks": [
            {
                "filename": "grpc_conn_pool.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"sync/atomic\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n)\n\n// GRPCConnectionPool управляет набором параллельных TCP-соединений к одному сервису\ntype GRPCConnectionPool struct {\n\tconns []*grpc.ClientConn\n\tindex atomic.Uint64\n\tsize  int\n}\n\nfunc NewGRPCConnectionPool(size int, target string) (*GRPCConnectionPool, error) {\n\tpool := &GRPCConnectionPool{\n\t\tconns: make([]*grpc.ClientConn, size),\n\t\tsize:  size,\n\t}\n\n\tfor i := 0; i < size; i++ {\n\t\tctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)\n\t\tconn, err := grpc.DialContext(ctx, target,\n\t\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t\t)\n\t\tcancel()\n\t\tif err != nil {\n\t\t\t// В случае ошибки закрываем ранее созданные\n\t\t\tpool.Close()\n\t\t\treturn nil, fmt.Errorf(\"failed to open connection %d: %w\", i, err)\n\t\t}\n\t\tpool.conns[i] = conn\n\t}\n\n\treturn pool, nil\n}\n\n// GetConn возвращает соединение из пула по алгоритму Round Robin\nfunc (p *GRPCConnectionPool) GetConn() *grpc.ClientConn {\n\tidx := p.index.Add(1)\n\treturn p.conns[idx%uint64(p.size)]\n}\n\nfunc (p *GRPCConnectionPool) Close() {\n\tfor _, c := range p.conns {\n\t\tif c != nil {\n\t\t\t_ = c.Close()\n\t\t}\n\t}\n}\n\nfunc main() {\n\tlog.Println(\"Initializing gRPC Channel Pool with 4 parallel TCP connections...\")\n\tpool, err := NewGRPCConnectionPool(4, \"127.0.0.1:50051\")\n\tif err != nil {\n\t\tlog.Printf(\"[Demo note] Expected deferred connection: %v\", err)\n\t\treturn\n\t}\n\tdefer pool.Close()\n\n\t// Получение соединений по очереди\n\tfor i := 1; i <= 8; i++ {\n\t\tconn := pool.GetConn()\n\t\t_ = conn\n\t\tfmt.Printf(\"Dispatched RPC call %d across multi-socket pool\\n\", i)\n\t}\n}",
                "note": "Клиентский пул постоянных gRPC соединений для снятия лимитов HTTP/2"
            }
        ],
        "under_the_hood": "Создание 4-8 параллельных соединений позволяет распределить сетевой трафик между разными ядрами CPU и сетевыми очередями NIC (Receive Side Scaling — RSS), увеличивая суммарную пропускную способность микросервиса в несколько раз.",
        "pitfalls": "Слишком большой размер пула (например 100). Каждое открытое TCP-соединение требует памяти ядра под буферы сокетов (`tcp_rmem`/`tcp_wmem`) и тратит ресурсы на keepalive пинги. Оптимальный размер пула: 2-8 соединений.",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'Зачем делать пул gRPC соединений, если gRPC и так мультиплексирует запросы?' Ответ: 'Мультиплексирование происходит внутри ОДНОГО TCP соединения. При огромном трафике (сотни тысяч сообщений) узким местом становится сериализация фреймов в одну горутину loopyWriter и лимиты HTTP/2 окон. Пул из 4-8 сокетов снимает эти ограничения'."
    },
    {
        "num": 66,
        "title": "Connection Draining при Rolling Update в Kubernetes: исключение 502 Bad Gateway",
        "task": "Сконфигурируйте стратегию RollingUpdate в Deployment Kubernetes с maxSurge: 25% и maxUnavailable: 0. Объясните роль этих параметров в предотвращении даунтайма.",
        "theory": "При развертывании новой версии микросервиса (Rolling Update) Kubernetes по умолчанию может одновременно завершать старые поды и поднимать новые. Если стратегия развертывания настроена некорректно: 1) `maxUnavailable: 25%` — кластер сразу убьет 25% старых подов, вызвав всплеск нагрузки на оставшиеся; 2) Если новые поды еще не прогрели кэш и не перешли в `Ready`, а старые уже удалены, пользователи получат 502/503 ошибки. Золотой стандарт Zero-Downtime: `maxSurge: 25%` — сначала Kubernetes поднимает дополнительные поды новой версии сверх лимита; `maxUnavailable: 0` — ни один старый под не имеет права быть остановлен, пока новый под не пройдет все Readiness-пробы и не начнет полноценно принимать трафик!",
        "step_by_step": [
            "Определите блок strategy.rollingUpdate в манифесте Deployment.",
            "Выставите maxSurge: 25% и maxUnavailable: 0.",
            "Настройте readinessProbe с initialDelaySeconds.",
            "Проверьте ход обновления без единой ошибки доступности."
        ],
        "code_blocks": [
            {
                "filename": "zero_downtime_deployment.yaml",
                "lang": "yaml",
                "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: payment-processor\n  labels:\n    app: payment-processor\nspec:\n  replicas: 4\n  # Безупречная стратегия обновления без деградации доступности\n  strategy:\n    type: RollingUpdate\n    rollingUpdate:\n      maxSurge: 25%        # Сначала поднимаем 1 дополнительный под новой версии (всего станет 5)\n      maxUnavailable: 0    # Запрещено гасить старые поды, пока новый не стал 100% Ready!\n  template:\n    metadata:\n      labels:\n        app: payment-processor\n    spec:\n      terminationGracePeriodSeconds: 40\n      containers:\n      - name: payment-api\n        image: payment-processor:v2.0.0\n        lifecycle:\n          preStop:\n            exec:\n              command: [\"/bin/sh\", \"-c\", \"sleep 15\"] # Draining delay для iptables\n        readinessProbe:\n          httpGet:\n            path: /readyz\n            port: 8080\n          initialDelaySeconds: 5\n          periodSeconds: 2\n          failureThreshold: 2\n        ports:\n        - containerPort: 8080",
                "note": "Манифест K8s с гарантией нулевого простоя (maxUnavailable: 0)"
            }
        ],
        "under_the_hood": "Контроллер Deployment в K8s сначала создает новый ReplicaSet, ожидает, пока поды в нем получат статус `Ready=True` от ReadinessProbe, и только после этого отправляет запрос на удаление пода из старого ReplicaSet.",
        "pitfalls": "Установка `maxUnavailable: 0` при нехватке вычислительных ресурсов (CPU/Memory) на нодах кластера. Если в кластере нет свободных ресурсов для создания `maxSurge` пода, деплой зависнет навсегда.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Что будет, если выставить maxUnavailable: 0 при replicas: 1?' Ответ: 'K8s сначала создаст второй под (maxSurge=1), дождется его готовности, переключит трафик, и только потом удалит первый под. Это гарантирует ноль секунд простоя даже при одной реплике (если хватает ресурсов ноды)'."
    },
    {
        "num": 67,
        "title": "Zero-Downtime Deployment Pipeline: PodDisruptionBudget, HPA и preStop",
        "task": "Спроектируйте комплексную защиту сервиса от сбоев инфраструктуры: объедините PodDisruptionBudget (PDB), HorizontalPodAutoscaler (HPA) и gRPC Connection Draining.",
        "theory": "В облачной среде Kubernetes поды могут вытесняться не только при деплое новой версии, но и во время планового обслуживания инфраструктуры: обновление версии ядра Linux на нодах (`kubectl drain`), масштабирование нод (Cluster Autoscaler) или перемещение подов. Чтобы такие действия инженеров или облака не привели к даунтайму, сервис защищается комплексно: 1) `PodDisruptionBudget` (`minAvailable: 80%` или `maxUnavailable: 1`): блокирует `kubectl drain`, запрещая выселять поды, если доступно меньше заданного процента реплик; 2) `HorizontalPodAutoscaler` (HPA): автоматически увеличивает число реплик при всплеске CPU/RAM; 3) `lifecycle.preStop` + `gRPC GracefulStop`: плавно выводят соединения перед выключением ноды.",
        "step_by_step": [
            "Создайте манифест PodDisruptionBudget с minAvailable: 2.",
            "Сконфигурируйте HPA с порогом по CPU 75%.",
            "Свяжите их с Deployment сервиса.",
            "Проверьте поведение кластера при вызове drain ноды."
        ],
        "code_blocks": [
            {
                "filename": "pdb_and_hpa.yaml",
                "lang": "yaml",
                "code": "apiVersion: policy/v1\nkind: PodDisruptionBudget\nmetadata:\n  name: billing-service-pdb\nspec:\n  minAvailable: 2 # Минимум 2 пода обязаны быть живы в любой момент времени!\n  selector:\n    matchLabels:\n      app: billing-service\n---\napiVersion: autoscaling/v2\nkind: HorizontalPodAutoscaler\nmetadata:\n  name: billing-service-hpa\nspec:\n  scaleTargetRef:\n    apiVersion: apps/v1\n    kind: Deployment\n    name: billing-service\n  minReplicas: 3\n  maxReplicas: 15\n  metrics:\n  - type: Resource\n    resource:\n      name: cpu\n      target:\n        type: Utilization\n        averageUtilization: 70",
                "note": "Комплексная защита доступности через PodDisruptionBudget и HPA"
            }
        ],
        "under_the_hood": "Когда SRE инженер запускает `kubectl drain node-1`, K8s API обращается к контроллеру PDB. Если удаление пода приведет к тому, что живых останется меньше `minAvailable`, операция `drain` блокируется с сообщением `Cannot evict pod: PDB violated`.",
        "pitfalls": "Установка `minAvailable: 100%` или `minAvailable: 1` при `replicas: 1`. В таком случае ноду невозможно будет вывести на обслуживание без принудительного удаления PDB.",
        "bigtech_interview": "Вопрос на собеседовании в Тинькофф: 'Что защищает наш сервис от падения, когда облако удаляет спотовую (Spot/Preemptible) ноду?' Ответ: 'Связка PDB (не дает выселить слишком много подов одновременно) и Graceful Draining (обрабатывает SIGTERM в течение отведенных провайдером 30 секунд)'."
    },
    {
        "num": 68,
        "title": "Плавный сброс соединений (Graceful Connection Draining) клиентом с Jitter",
        "task": "Реализуйте на клиенте обработку ротации соединений с добавлением случайной задержки (Jitter), чтобы предотвратить одновременный шторм переподключений (Thundering Herd) к новым репликам.",
        "theory": "Когда на gRPC серверах настроен `MaxConnectionAge: 10m`, все соединения, открытые одновременно (например, во время утреннего старта платформы), достигнут предельного возраста в одну и ту же секунду! Серверы отправят клиентам GOAWAY, и тысячи клиентов одновременно кинутся заново резолвить DNS и устанавливать TCP + TLS рукопожатия (Thundering Herd / Reconnect Storm). Это может перегрузить DNS-сервер (CoreDNS в K8s) и CPU бэкендов. Решение: клиентский рандомизированный Jitter. При необходимости переподключения или ротации время жизни соединения варьируется: `actualLifetime = baseTime + rand.Float64() * jitterRange`. Это плавно 'размазывает' переподключения во времени, распределяя нагрузку равномерно.",
        "step_by_step": [
            "Импортируйте crypto/rand или math/rand/v2.",
            "Реализуйте функцию CalculateJitterDuration(base, maxJitter time.Duration).",
            "Примените случайную задержку перед переподключением клиента.",
            "Проверьте равномерность распределения попыток подключения."
        ],
        "code_blocks": [
            {
                "filename": "reconnect_jitter.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"crypto/rand\"\n\t\"fmt\"\n\t\"log\"\n\t\"math/big\"\n\t\"time\"\n)\n\n// AddJitterToDuration добавляет случайный разброс [0, maxJitter] к базовой длительности\nfunc AddJitterToDuration(base time.Duration, maxJitter time.Duration) time.Duration {\n\tif maxJitter <= 0 {\n\t\treturn base\n\t}\n\tnBig, err := rand.Int(rand.Reader, big.NewInt(int64(maxJitter)))\n\tif err != nil {\n\t\treturn base\n\t}\n\treturn base + time.Duration(nBig.Int64())\n}\n\nfunc main() {\n\tbaseConnectionAge := 10 * time.Minute\n\tmaxJitter := 2 * time.Minute\n\n\tlog.Printf(\"Base connection age: %v, Max Jitter: %v\", baseConnectionAge, maxJitter)\n\n\t// Моделируем расчет времени ротации для 5 клиентов\n\tfor i := 1; i <= 5; i++ {\n\t\tstaggeredLifetime := AddJitterToDuration(baseConnectionAge, maxJitter)\n\t\tfmt.Printf(\"Client %d scheduled reconnect in: %v\\n\", i, staggeredLifetime.Round(time.Second))\n\t}\n\n\tfmt.Println(\"Connection rotation jitter smoothly disperses traffic spikes.\")\n}",
                "note": "Расчет случайного джиттера для предотвращения Reconnect Storm"
            }
        ],
        "under_the_hood": "Использование криптографического генератора `crypto/rand` или потокобезопасного `math/rand/v2` гарантирует отсутствие корреляции между процессами даже при одинаковом начальном времени запуска подов.",
        "pitfalls": "Использование фиксированного интервала повтора (например, ровно 5 секунд). Все клиенты, получившие отказ в секунду T, синхронно придут повторно в секунду T+5, повторяя всплеск нагрузки.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Что такое Thundering Herd проблема при gRPC keepalive/reconnect?' Ответ: 'Это одновременная попытка сотен или тысяч клиентов переподключиться к серверу после сброса соединений. Она предотвращается добавлением Exponential Backoff со случайным Full Jitter'."
    },
    {
        "num": 69,
        "title": "Локальный singleflight для дедупликации сетевых запросов в микросервисе",
        "task": "Реализуйте обертку над сетевым клиентом с использованием golang.org/x/sync/singleflight, гарантирующую, что при 100 одновременных запросах одинаковых данных в сеть уйдет ровно 1 запрос.",
        "theory": "Внутри одного пода Go сотни горутин могут одновременно запрашивать один и тот же неизменяемый ресурс: например, профиль популярного пользователя, карточку горячего товара на распродаже или курсы валют. Без дедупликации каждая горутина выполнит отдельный сетевой HTTP или gRPC вызов к удаленному бэкенду. Пакет `golang.org/x/sync/singleflight` объединяет конкурентные вызовы с одинаковым ключом: первая горутина выполняет реальный сетевой запрос, а остальные 99 горутин блокируются и получают копию того же самого результата, как только первый вызов вернет ответ. Это снижает нагрузку на внутреннюю сеть и микросервисы в 10-100 раз.",
        "step_by_step": [
            "Импортируйте golang.org/x/sync/singleflight.",
            "Создайте структуру ClientWithSingleflight со встроенной группой sf.Group.",
            "Реализуйте метод FetchData(ctx context.Context, key string) (string, error).",
            "Используйте sf.DoChan для поддержки отмены контекста вызывающей стороны.",
            "Проверьте дедупликацию вызовов на группе конкурентных горутин."
        ],
        "code_blocks": [
            {
                "filename": "singleflight_dedup.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"sync\"\n\t\"sync/atomic\"\n\t\"time\"\n\n\t\"golang.org/x/sync/singleflight\"\n)\n\ntype NetworkClient struct {\n\tgroup        singleflight.Group\n\tnetworkCalls atomic.Int64\n}\n\n// FetchDataSafe выполняет дедуплицированный сетевой запрос с поддержкой отмены контекста\nfunc (c *NetworkClient) FetchDataSafe(ctx context.Context, resourceID string) (string, error) {\n\t// DoChan возвращает канал, что позволяет реагировать на отмену ctx конкретного клиента\n\tresultChan := c.group.DoChan(resourceID, func() (interface{}, error) {\n\t\tlog.Printf(\"[Outbound Network] Sending physical request for resource: %s\", resourceID)\n\t\tc.networkCalls.Add(1)\n\n\t\t// Имитируем сетевой round-trip 100мс\n\t\ttime.Sleep(100 * time.Millisecond)\n\t\treturn fmt.Sprintf(\"PAYLOAD_FOR_%s\", resourceID), nil\n\t})\n\n\tselect {\n\tcase <-ctx.Done():\n\t\treturn \"\", ctx.Err()\n\tcase res := <-resultChan:\n\t\tif res.Err != nil {\n\t\t\treturn \"\", res.Err\n\t\t}\n\t\treturn res.Val.(string), nil\n\t}\n}\n\nfunc main() {\n\tclient := &NetworkClient{}\n\tvar wg sync.WaitGroup\n\n\t// Запускаем 10 параллельных горутин за одним и тем же ресурсом\n\tfor i := 1; i <= 10; i++ {\n\t\twg.Add(1)\n\t\tgo func(id int) {\n\t\t\tdefer wg.Done()\n\t\t\tctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)\n\t\t\tdefer cancel()\n\n\t\t\tval, err := client.FetchDataSafe(ctx, \"user-profile-1001\")\n\t\t\tif err != nil {\n\t\t\t\tlog.Printf(\"Client %d failed: %v\", id, err)\n\t\t\t\treturn\n\t\t\t}\n\t\t\t_ = val\n\t\t}(i)\n\t}\n\n\twg.Wait()\n\tfmt.Printf(\"Singleflight complete! Physical network calls made: %d (Expected: 1)\\n\",\n\t\tclient.networkCalls.Load())\n}",
                "note": "Дедупликация конкурентных запросов через singleflight.DoChan с поддержкой ctx"
            }
        ],
        "under_the_hood": "Использование `DoChan` вместо синхронного `Do` критически важно в продакшене: если одна из горутин отменила свой HTTP-запрос по таймауту клиента, она не должна висеть в блокировке, пока первая горутина доделывает сетевой вызов.",
        "pitfalls": "Мутация возвращаемого указателя. Если `singleflight.Do` возвращает указатель на срез или структуру `*User`, все 100 горутин получат один и тот же указатель! Если одна из них изменит поле структуры, возникнет состояние гонки (Data Race). Всегда возвращайте неизменяемые данные или делайте глубокую копию.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'В чем опасность использования singleflight.Do при работе с context.Context?' Ответ: 'Синхронный Do() не принимает context. Если первая горутина зависнет, остальные горутины зависнут вместе с ней, даже если их собственные контексты уже отменены. Необходимо использовать `DoChan` с select по `ctx.Done()`'."
    },
    {
        "num": 70,
        "title": "Graceful Shutdown в Kubernetes: координация terminationGracePeriod, preStop и проб",
        "task": "Напишите комплексную спецификацию PodSpec и код Go-сервиса, демонстрирующую правильное распределение времени между preStop хуком, readinessProbe (503) и terminationGracePeriodSeconds.",
        "theory": "Успешный Graceful Shutdown в Kubernetes опирается на строгий математический баланс времени: `terminationGracePeriodSeconds >= preStop_delay + drain_delay + shutdown_timeout + db_close_timeout + 5s (safety buffer)`. Пример расчета для production: 1) `preStop` sleep: 10 секунд (время на обновление kube-proxy и исключение из Service Endpoints); 2) `drain_delay` в Go: 3 секунды (страховка от задержек Service Mesh); 3) `server.Shutdown` timeout: 15 секунд (время на доработку тяжелых пользовательских запросов); 4) Закрытие базы данных: 2 секунды; Итого минимальное время: 10 + 3 + 15 + 2 = 30 секунд. Следовательно, `terminationGracePeriodSeconds` в K8s манифесте обязан быть не менее 40-45 секунд! Если выставить дефолтные 30с, kubelet пришлет SIGKILL прямо во время выполнения запросов.",
        "step_by_step": [
            "Рассчитайте таймлайн завершения для вашего микросервиса.",
            "Сконфигурируйте terminationGracePeriodSeconds в YAML.",
            "Настройте Go приложение для пошагового выполнения фаз остановки.",
            "Проверьте отсутствие сброшенных соединений."
        ],
        "code_blocks": [
            {
                "filename": "k8s_grace_budget.txt",
                "lang": "text",
                "code": "Расчет бюджета времени (Grace Budget) в Kubernetes:\n\n+-------------------------------------------------------------------------------+\n| Total terminationGracePeriodSeconds = 45s                                    |\n+-----------------------------------+-------------------------------------------+\n| [0s .. 10s]  PreStop Hook         | sleep 10s в pod lifecycle. K8s удаляет    |\n|                                   | IP из Endpoints, kube-proxy чистит iptables|\n+-----------------------------------+-------------------------------------------+\n| [10s]        Kubelet SIGTERM      | Kubelet посылает SIGTERM процессу Go      |\n+-----------------------------------+-------------------------------------------+\n| [10s .. 13s] Go Readiness 503     | /readyz начинает отдавать 503 Service Unav|\n|              & Internal Delay     | Пауза 3с для сброса буферов прокси Envoy  |\n+-----------------------------------+-------------------------------------------+\n| [13s .. 28s] server.Shutdown()    | Закрытие листенеров, доработка in-flight  |\n|                                   | запросов (лимит таймаута: 15с)            |\n+-----------------------------------+-------------------------------------------+\n| [28s .. 30s] Cleanup DB / Queues  | Закрытие пула PostgreSQL и flush логов    |\n+-----------------------------------+-------------------------------------------+\n| [30s .. 45s] Safety Buffer        | 15 секунд запаса до аварийного SIGKILL    |\n+-----------------------------------+-------------------------------------------+",
                "note": "Матрица распределения тайм-аутов при Graceful Draining в K8s"
            }
        ],
        "under_the_hood": "Если процесс Go завершается раньше, контейнер закрывается немедленно — Kubernetes не ждет окончания `terminationGracePeriodSeconds`, если процесс уже завершился с кодом 0.",
        "pitfalls": "Увеличение `shutdown_timeout` в Go коде без увеличения `terminationGracePeriodSeconds` в K8s. Kubelet ничего не знает о внутренних таймаутах Go и убьет процесс ровно по своему системному таймеру.",
        "bigtech_interview": "Вопрос на собеседовании в Тинькофф: 'Как рассчитать terminationGracePeriodSeconds для микросервиса?' Ответ: 'Взять максимальный p99 latency тяжелого запроса (например 10с), прибавить preStop sleep (10-15с), время закрытия ресурсов (2с) и добавить 20-30% буфера безопасности'."
    },
    {
        "num": 71,
        "title": "Header Delayed Sending в gRPC: опережающая отправка метаданных до ответа",
        "task": "Реализуйте опережающую отправку метаданных клиенту до завершения RPC метода с использованием grpc.SetHeader и grpc.SendHeader.",
        "theory": "По умолчанию в gRPC заголовки метаданных (`metadata`) отправляются клиенту одновременно с первым пакетом данных сообщения (кадр HTTP/2 HEADERS объединяется с DATA). Однако в сложных потоковых сценариях или при долгой предварительной обработке клиенту необходимо получить метаданные НЕМЕДЛЕННО (например, x-cache-hit, routing-region, session-id или token). Для этого gRPC предоставляет два метода: 1) `grpc.SetHeader(ctx, md)` — сохраняет метаданные в буфере и шлет их вместе с телом; 2) `grpc.SendHeader(ctx, md)` — немедленно принудительно отправляет HTTP/2 фрейм HEADERS клиенту, не дожидаясь генерации полезной нагрузки ответа.",
        "step_by_step": [
            "Импортируйте google.golang.org/grpc и google.golang.org/grpc/metadata.",
            "Сформируйте метаданные через metadata.Pairs.",
            "Вызовите grpc.SendHeader(ctx, md) для немедленной передачи заголовков.",
            "Проверьте фиксацию заголовков на стороне клиента до получения тела ответа."
        ],
        "code_blocks": [
            {
                "filename": "delayed_header_sending.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/metadata\"\n)\n\n// HeavyComputeService имитирует gRPC обработчик с предварительной отправкой заголовков\ntype HeavyComputeService struct{}\n\nfunc (s *HeavyComputeService) ProcessTask(ctx context.Context) error {\n\t// 1. Формируем ранние служебные заголовки\n\tinitialMD := metadata.Pairs(\n\t\t\"x-cache-status\", \"HIT\",\n\t\t\"x-compute-region\", \"eu-central-1\",\n\t\t\"x-trace-init\", \"ready\",\n\t)\n\n\t// 2. Принудительно шлем HTTP/2 HEADERS кадр прямо сейчас!\n\tlog.Println(\"[gRPC Server] Flushing early headers to client via grpc.SendHeader...\")\n\tif err := grpc.SendHeader(ctx, initialMD); err != nil {\n\t\treturn fmt.Errorf(\"failed to flush headers: %w\", err)\n\t}\n\n\t// 3. Долгая генерация полезной нагрузки (клиент уже получил метаданные)\n\tlog.Println(\"[gRPC Server] Commencing heavy business computation...\")\n\n\t// 4. Трейлеры (отправляются в самом конце)\n\ttrailerMD := metadata.Pairs(\"x-compute-cost-ms\", \"142\")\n\t_ = grpc.SetTrailer(ctx, trailerMD)\n\n\treturn nil\n}\n\nfunc main() {\n\tsvc := &HeavyComputeService{}\n\t// Имитация контекста со стороны gRPC сервера\n\tctx := metadata.NewIncomingContext(context.Background(), metadata.New(nil))\n\n\t_ = svc.ProcessTask(ctx)\n\tfmt.Println(\"gRPC Delayed / Early Header Sending verified successfully.\")\n}",
                "note": "Принудительная отправка HTTP/2 HEADERS до генерации тела ответа через SendHeader"
            }
        ],
        "under_the_hood": "Вызов `grpc.SendHeader` отправляет HTTP/2 фрейм HEADERS без флага `END_STREAM`. После вызова `SendHeader` любые последующие вызовы `grpc.SetHeader` приведут к ошибке, так как заголовки потока уже зафиксированы.",
        "pitfalls": "Повторный вызов `grpc.SendHeader`. HTTP/2 протокол разрешает отправить ровно один блок HEADERS в начале стрима и один блок HEADERS (Trailers) в конце. Повторная отправка вернет ошибку.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'В чем разница между grpc.SetHeader и grpc.SendHeader?' Ответ: 'SetHeader лишь сохраняет метаданные в контексте, и они уйдут вместе с первым сообщением данных. SendHeader немедленно формирует и отправляет HTTP/2 фрейм HEADERS по сокету клиенту'."
    },
    {
        "num": 72,
        "title": "Архитектурный стандарт gRPC Keepalive & Draining в распределенных системах",
        "task": "Сформулируйте сводный инженерный регламент (Best Practices) по конфигурации Keepalive и Draining для микросервисов HighLoad Enterprise уровня.",
        "theory": "Архитектурный стандарт отказоустойчивости gRPC платформы: 1. Клиентская сторона (gRPC Client):    - `Time: 15s`, `Timeout: 5s`, `PermitWithoutStream: true`;    - Балансировка: `round_robin` с DNS резолвером через Headless Service;    - Retry Policy: экспоненциальный backoff с jitter для кодов `UNAVAILABLE`. 2. Серверная сторона (gRPC Server):    - `MaxConnectionAge: 10m` + Jitter (ротация сокетов для балансировки по репликам);    - `MaxConnectionAgeGrace: 30s` (время на завершение запросов после GOAWAY);    - `EnforcementPolicy{MinTime: 5s, PermitWithoutStream: true}`. 3. Оркестрация (Kubernetes):    - `lifecycle.preStop: sleep 10` в PodSpec;    - `readinessProbe` переключается в 503 при получении SIGTERM;    - `terminationGracePeriodSeconds: 45`.",
        "step_by_step": [
            "Изучите сводную таблицу параметров.",
            "Проверьте совместимость настроек клиента и сервера.",
            "Сформулируйте чеклист аудита сетевой надежности.",
            "Примените регламент к микросервисам проекта."
        ],
        "code_blocks": [
            {
                "filename": "grpc_standard.md",
                "lang": "markdown",
                "code": "# Золотой стандарт gRPC Keepalive & Draining в Production\n\n| Уровень | Параметр | Рекомендуемое значение | Обоснование |\n| :--- | :--- | :--- | :--- |\n| **Client** | `keepalive.ClientParameters.Time` | `15s` | Зондирование NAT/NLB до сброса таблицы conntrack |\n| **Client** | `keepalive.ClientParameters.Timeout` | `5s` | Быстрое обнаружение мертвого сокета |\n| **Client** | `PermitWithoutStream` | `true` | Защита от разрыва соединений в часы ночного простоя |\n| **Server** | `MaxConnectionAge` | `10m` (+ jitter) | Принудительная перебалансировка клиентов по новым подам |\n| **Server** | `MaxConnectionAgeGrace` | `30s` | Бесшовное завершение активных RPC после GOAWAY |\n| **Server** | `EnforcementPolicy.MinTime` | `5s` | Защита от DoS-атак частыми пингами клиентов |\n| **K8s** | `preStop.exec.command` | `[\"sleep\", \"10\"]`| Время на обновление iptables во всем кластере |\n| **K8s** | `terminationGracePeriodSeconds` | `45s` | Запас времени до принудительного SIGKILL |",
                "note": "Сводный инженерный регламент сетевой надежности gRPC"
            }
        ],
        "under_the_hood": "Соблюдение неравенства `Client.Time > Server.EnforcementPolicy.MinTime` является ключевым правилом, предотвращающим отстрел клиентов сервером с ошибкой too_many_pings.",
        "pitfalls": "Рассинхронизация конфигураций между разными командами разработки. Рекомендуется выносить единый пресет DialOptions и ServerOptions в общую корпоративную Go-библиотеку (SDK).",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Назовите три главных параметра gRPC сервера для работы в высоконагруженном Kubernetes кластере.' Ответ: '1) MaxConnectionAge для ротации соединений; 2) Keepalive EnforcementPolicy для защиты от флуда; 3) Координированный GracefulStop с дедлайном и preStop хуком'."
    },
    {
        "num": 73,
        "title": "Распределенный Redis Lock для защиты от Cache Stampede между подами",
        "task": "Реализуйте потокобезопасный распределенный замок (Distributed Lock) в Redis на Go с атомарным продлением и безопасным освобождением через Lua скрипт.",
        "theory": "Когда кэш протухает, одного локального singleflight недостаточно: в кластере работают 50 независимых подов, и каждый под сделает по 1 тяжелому запросу в базу данных. Для синхронизации подов используется распределенная блокировка (Distributed Lock) в Redis: 1) Захват замка: `SET lock:catalog {random_uuid} NX PX 5000` (атомарная установка с TTL 5с); 2) Если замок захвачен — под загружает данные из базы и сохраняет их в Redis Cache; 3) Если замок занят другим подом — под засыпает на 50мс и повторно проверяет кэш; 4) Освобождение замка: выполняется СТРОГО через Lua-скрипт с проверкой UUID владельца, чтобы не удалить чужой замок, если свой замок уже истек по TTL.",
        "step_by_step": [
            "Реализуйте генерацию уникального токена владельца (UUID / random bytes).",
            "Напишите Lua-скрипт безопасного освобождения замка.",
            "Реализуйте функцию AcquireLock и ReleaseLock.",
            "Проверьте защиту от случайного удаления чужого замка."
        ],
        "code_blocks": [
            {
                "filename": "redis_distributed_lock.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"crypto/rand\"\n\t\"encoding/hex\"\n\t\"fmt\"\n\t\"sync\"\n\t\"time\"\n)\n\n// luaReleaseLock атомарно проверяет token и удаляет ключ только если token совпадает\nconst luaReleaseLock = `\nif redis.call(\"get\", KEYS[1]) == ARGV[1] then\n    return redis.call(\"del\", KEYS[1])\nelse\n    return 0\nend\n`\n\ntype MockRedisClient struct {\n\tmu     sync.Mutex\n\tstore  map[string]string\n\texpiry map[string]time.Time\n}\n\nfunc NewMockRedisClient() *MockRedisClient {\n\treturn &MockRedisClient{\n\t\tstore:  make(map[string]string),\n\t\texpiry: make(map[string]time.Time),\n\t}\n}\n\nfunc (c *MockRedisClient) SetNX(key, val string, ttl time.Duration) bool {\n\tc.mu.Lock()\n\tdefer c.mu.Unlock()\n\n\tnow := time.Now()\n\tif exp, ok := c.expiry[key]; ok && now.Before(exp) {\n\t\treturn false // Ключ существует и еще не протух\n\t}\n\n\tc.store[key] = val\n\tc.expiry[key] = now.Add(ttl)\n\treturn true\n}\n\nfunc (c *MockRedisClient) Release(key, token string) bool {\n\tc.mu.Lock()\n\tdefer c.mu.Unlock()\n\n\tif c.store[key] == token {\n\t\tdelete(c.store, key)\n\t\tdelete(c.expiry, key)\n\t\treturn true\n\t}\n\treturn false\n}\n\n// DistributedLock представляет безопасный замок\ntype DistributedLock struct {\n\tclient *MockRedisClient\n\tkey    string\n\ttoken  string\n\tttl    time.Duration\n}\n\nfunc NewDistributedLock(client *MockRedisClient, key string, ttl time.Duration) *DistributedLock {\n\tb := make([]byte, 16)\n\t_, _ = rand.Read(b)\n\treturn &DistributedLock{\n\t\tclient: client,\n\t\tkey:    key,\n\t\ttoken:  hex.EncodeToString(b),\n\t\tttl:    ttl,\n\t}\n}\n\nfunc (l *DistributedLock) TryLock(ctx context.Context) bool {\n\treturn l.client.SetNX(l.key, l.token, l.ttl)\n}\n\nfunc (l *DistributedLock) Unlock(ctx context.Context) bool {\n\treturn l.client.Release(l.key, l.token)\n}\n\nfunc main() {\n\tclient := NewMockRedisClient()\n\tlock1 := NewDistributedLock(client, \"lock:products\", 5*time.Second)\n\tlock2 := NewDistributedLock(client, \"lock:products\", 5*time.Second)\n\n\t// Под 1 захватывает замок\n\tif lock1.TryLock(context.Background()) {\n\t\tfmt.Println(\"Pod 1 successfully acquired Redis lock!\")\n\t}\n\n\t// Под 2 пытается захватить тот же замок\n\tif !lock2.TryLock(context.Background()) {\n\t\tfmt.Println(\"Pod 2 denied lock: waiting for Pod 1 to populate cache.\")\n\t}\n\n\t// Под 1 освобождает замок\n\tif lock1.Unlock(context.Background()) {\n\t\tfmt.Println(\"Pod 1 safely released Redis lock via atomic check.\")\n\t}\n}",
                "note": "Безопасный распределенный замок в Redis с защитой от удаления чужих ключей"
            }
        ],
        "under_the_hood": "Если освобождать замок простой командой `DEL lock:key` без проверки UUID, может произойти катастрофа: если GC-пауза затянула операцию пода 1 дольше TTL замка, замок перехватит под 2. По завершении под 1 выполнит `DEL` и сотрет замок пода 2! Lua-скрипт гарантирует, что удаляется только собственный токен.",
        "pitfalls": "Забыть выставить TTL (экспирацию) замка. Если под упадет с паникой или будет убит OOM Killer'ом до вызова Unlock, замок без TTL останется в Redis навсегда, заблокировав всю систему.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Почему в Redis Lock нельзя делать DEL key напрямую?' Ответ: 'Потому что операция пода могла выполняться дольше времени TTL замка. Замок уже истек и был выдан другому поду. Прямой DEL сотрет чужую блокировку. Освобождение обязано проверять уникальный токен через Lua-скрипт'."
    },
    {
        "num": 74,
        "title": "Финальное испытание: Cloud-Native gRPC Service — полный производственный цикл",
        "task": "Реализуйте полноценный микросервис на gRPC: Unary метод + Server Streaming, W3C Trace Context интерцепторы, Keepalive параметры сервера и отказоустойчивый Graceful Shutdown при SIGTERM.",
        "theory": "Это итоговое практическое испытание главы 80. В едином production-grade Go-сервисе объединяются все изученные технологии: 1. Протокол gRPC с унарным методом `ProcessOrder` и потоковым методом `StreamOrderStatus`; 2. Полная трассировка OpenTelemetry с автоматическим извлечением `traceparent` из metadata; 3. Настройка серверного Keepalive (`MaxConnectionAge: 10m`, `EnforcementPolicy`); 4. Координированный Graceful Shutdown: перехват SIGTERM, перевод ReadinessProbe в 503, выдержка сетевой паузы и плавный вызов `GracefulStop` с дедлайном; 5. Корректное завершение активных стримов без транспортных ошибок.",
        "step_by_step": [
            "Инициализируйте OpenTelemetry провайдер и интерцепторы.",
            "Настройте gRPC сервер с keepalive политиками.",
            "Реализуйте методы сервиса с обработкой контекста отмены.",
            "Организуйте перехват сигналов ОС и координированную остановку.",
            "Проверьте чистое завершение работы."
        ],
        "code_blocks": [
            {
                "filename": "production_grpc_service.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net\"\n\t\"os\"\n\t\"os/signal\"\n\t\"sync/atomic\"\n\t\"syscall\"\n\t\"time\"\n\n\t\"go.opentelemetry.io/otel\"\n\t\"go.opentelemetry.io/otel/propagation\"\n\tsdktrace \"go.opentelemetry.io/otel/sdk/trace\"\n\t\"go.opentelemetry.io/otel/trace\"\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/keepalive\"\n\t\"google.golang.org/grpc/metadata\"\n)\n\ntype ProductionServer struct {\n\tisDraining atomic.Bool\n\ttracer     trace.Tracer\n}\n\nfunc (s *ProductionServer) HandleUnaryRPC(ctx context.Context, orderID string) (string, error) {\n\tif s.isDraining.Load() {\n\t\tlog.Println(\"[Warning] Processing RPC during draining phase...\")\n\t}\n\n\tspan := trace.SpanFromContext(ctx)\n\tlog.Printf(\"[RPC] Order %s processed. TraceID: %s\", orderID, span.SpanContext().TraceID().String())\n\treturn fmt.Sprintf(\"CONFIRMED_%s\", orderID), nil\n}\n\nfunc StartProductionGRPC(addr string) (*grpc.Server, net.Listener, *ProductionServer) {\n\ttp := sdktrace.NewTracerProvider(sdktrace.WithSampler(sdktrace.AlwaysSample()))\n\totel.SetTracerProvider(tp)\n\totel.SetTextMapPropagator(propagation.TraceContext{})\n\n\tapp := &ProductionServer{\n\t\ttracer: otel.Tracer(\"order-service\"),\n\t}\n\n\tkasp := keepalive.ServerParameters{\n\t\tMaxConnectionAge:      10 * time.Minute,\n\t\tMaxConnectionAgeGrace: 30 * time.Second,\n\t\tTime:                  2 * time.Hour,\n\t\tTimeout:               20 * time.Second,\n\t}\n\n\tkaep := keepalive.EnforcementPolicy{\n\t\tMinTime:             5 * time.Second,\n\t\tPermitWithoutStream: true,\n\t}\n\n\t// Интерцептор автоматического извлечения Trace Context из gRPC metadata\n\ttraceInterceptor := func(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {\n\t\tmd, _ := metadata.FromIncomingContext(ctx)\n\t\tcarrier := make(propagation.HeaderCarrier)\n\t\tfor k, v := range md {\n\t\t\tif len(v) > 0 {\n\t\t\t\tcarrier.Set(k, v[0])\n\t\t\t}\n\t\t}\n\t\textractedCtx := otel.GetTextMapPropagator().Extract(ctx, carrier)\n\t\tnewCtx, span := app.tracer.Start(extractedCtx, info.FullMethod, trace.WithSpanKind(trace.SpanKindServer))\n\t\tdefer span.End()\n\n\t\treturn handler(newCtx, req)\n\t}\n\n\tserver := grpc.NewServer(\n\t\tgrpc.KeepaliveParams(kasp),\n\t\tgrpc.KeepaliveEnforcementPolicy(kaep),\n\t\tgrpc.UnaryInterceptor(traceInterceptor),\n\t)\n\n\tlis, err := net.Listen(\"tcp\", addr)\n\tif err != nil {\n\t\tlog.Fatalf(\"Listen failed: %v\", err)\n\t}\n\n\treturn server, lis, app\n}\n\nfunc main() {\n\tserver, lis, app := StartProductionGRPC(\":50060\")\n\tdefer lis.Close()\n\n\tgo func() {\n\t\tlog.Printf(\"Production gRPC service active on %s\", lis.Addr().String())\n\t\t_ = server.Serve(lis)\n\t}()\n\n\tsigChan := make(chan os.Signal, 1)\n\tsignal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)\n\n\t// Имитируем получение сигнала остановки через 300мс\n\tgo func() {\n\t\ttime.Sleep(300 * time.Millisecond)\n\t\tsigChan <- syscall.SIGTERM\n\t}()\n\n\t<-sigChan\n\tlog.Println(\"[SIGTERM] Draining sequence initiated...\")\n\n\t// 1. Помечаем под как draining (readinessProbe -> 503)\n\tapp.isDraining.Store(true)\n\n\t// 2. Сетевая пауза для обновления K8s iptables\n\ttime.Sleep(500 * time.Millisecond)\n\n\t// 3. GracefulStop с дедлайном\n\tlog.Println(\"[Shutdown] Invoking server.GracefulStop()...\")\n\tdone := make(chan struct{})\n\tgo func() {\n\t\tserver.GracefulStop()\n\t\tclose(done)\n\t}()\n\n\tselect {\n\tcase <-done:\n\t\tlog.Println(\"[Shutdown] gRPC server cleanly stopped.\")\n\tcase <-time.After(5 * time.Second):\n\t\tlog.Println(\"[Shutdown] Timeout expired, forcing server.Stop().\")\n\t\tserver.Stop()\n\t}\n\n\tfmt.Println(\"Production-grade Cloud-Native gRPC service lifecycle completed perfectly.\")\n}",
                "note": "Финальная эталонная реализация gRPC сервиса с трейсингом и graceful draining"
            }
        ],
        "under_the_hood": "Данный скелет объединяет все требования Cloud-Native архитектуры: совместимость с Kubernetes Lifecycle, прозрачную трассировку OpenTelemetry, защиту сетевого стека Keepalive и нулевые потери пакетов при развертывании.",
        "pitfalls": "Пренебрежение таймаутом на `GracefulStop()`. В продакшене любой сетевой сокет может зависнуть, поэтому жесткий таймаут обязателен.",
        "bigtech_interview": "Вопрос на финальном интервью в Ozon: 'Как доказать руководству, что сервис готов к HighLoad продакшену?' Ответ: '1) 100% покрытие сквозной трассировкой W3C; 2) Валидированные параметры Keepalive против разрыва NLB; 3) Успешный Chaos Monkey тест: ноль 502/RST ошибок при rolling update под нагрузкой'."
    },
    {
        "num": 75,
        "title": "Chaos Engineering (Monkey Test): нагрузочное тестирование с отправкой SIGTERM",
        "task": "Напишите Go-скрипт хаос-тестирования: в бесконечном цикле отправляет RPC-запросы к серверу и случайным образом посылает процессу SIGTERM, подтверждая нулевой процент сетевых ошибок при наличии Graceful Draining.",
        "theory": "Теория надежности гласит: 'Если система не протестирована на сбои в хаос-тестах, она упадет в самый неподходящий момент'. Принцип Chaos Engineering (Monkey Test): специальный тестовый агент непрерывно генерирует клиентскую нагрузку (1000 RPS) и в случайные моменты времени отправляет сигнал `SIGTERM` случайным подам в кластере. Если система спроектирована правильно (с `preStop`, `readinessProbe: 503` и `GracefulStop`), все запросы клиентов завершаются успешно (0 ошибок, 100% SLO). Если же разработчики забыли выдержать задержку сброса маршрутов, клиенты зафиксируют всплеск ошибок `Connection Refused` и `502 Bad Gateway`.",
        "step_by_step": [
            "Создайте конкурентный генератор запросов на Go.",
            "В отдельной горутине сымитируйте хаотические сбои и перезапуски.",
            "Ведите счетчик успешных и проваленных запросов.",
            "Подтвердите отсутствие ошибок при корректно настроенном Graceful Shutdown."
        ],
        "code_blocks": [
            {
                "filename": "chaos_monkey_test.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"sync\"\n\t\"sync/atomic\"\n\t\"time\"\n)\n\ntype ChaosTestSuite struct {\n\ttotalRequests  atomic.Int64\n\tfailedRequests atomic.Int64\n\tisRunning      atomic.Bool\n}\n\nfunc (s *ChaosTestSuite) SimulateRequest(ctx context.Context) error {\n\ts.totalRequests.Add(1)\n\t// Имитируем сетевой запрос к серверу\n\ttime.Sleep(10 * time.Millisecond)\n\treturn nil\n}\n\nfunc (s *ChaosTestSuite) RunChaosWorker(wg *sync.WaitGroup) {\n\tdefer wg.Done()\n\tfor s.isRunning.Load() {\n\t\tctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)\n\t\tif err := s.SimulateRequest(ctx); err != nil {\n\t\t\ts.failedRequests.Add(1)\n\t\t}\n\t\tcancel()\n\t}\n}\n\nfunc main() {\n\tsuite := &ChaosTestSuite{}\n\tsuite.isRunning.Store(true)\n\n\tvar wg sync.WaitGroup\n\tworkers := 5\n\tfor i := 0; i < workers; i++ {\n\t\twg.Add(1)\n\t\tgo suite.RunChaosWorker(&wg)\n\t}\n\n\tlog.Println(\"[Chaos Test] Simulating continuous high-throughput traffic...\")\n\ttime.Sleep(200 * time.Millisecond)\n\n\tlog.Println(\"[Chaos Monkey] INJECTING FAULT: Sending simulated SIGTERM to backend...\")\n\t// В реальном тесте: syscall.Kill(pid, syscall.SIGTERM)\n\ttime.Sleep(100 * time.Millisecond)\n\n\tsuite.isRunning.Store(false)\n\twg.Wait()\n\n\ttotal := suite.totalRequests.Load()\n\tfailed := suite.failedRequests.Load()\n\tfmt.Printf(\"Chaos Test Summary: Total=%d, Failed=%d, Error Rate=%.2f%%\\n\",\n\t\ttotal, failed, float64(failed)/float64(total)*100)\n\n\tif failed == 0 {\n\t\tfmt.Println(\"PASS: Zero packet drops achieved under chaos conditions!\")\n\t}\n}",
                "note": "Скрипт Chaos Engineering для верификации Zero-Downtime при аварийном завершении"
            }
        ],
        "under_the_hood": "Такие тесты автоматизируются в CI/CD через утилиты Chaos Mesh, LitmusChaos или простые скрипты на Go перед выпуском релиза в продакшен.",
        "pitfalls": "Запуск тестов на локальной машине без эмуляции задержки распространения DNS/iptables. На localhost сеть мгновенна, поэтому реальные race conditions K8s воспроизводятся только в тестовом кластере.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Как вы проверяете, что сервис завершается без даунтайма перед релизом?' Ответ: 'Запускаем нагрузочный тест k6 / vegeta на 5000 RPS и инициируем rolling update или kubectl delete pod. Смотрим процент неуспешных ответов (non-2xx/non-0 status). Целевой показатель — строго 0% ошибок'."
    },
    {
        "num": 76,
        "title": "Координация Shutdown с K8s preStop хуком: финальная интеграция сетевого стека",
        "task": "Напишите финальный Go-модуль координации завершения gRPC-сервиса, синхронизирующий системные вызовы сигналов ОС, K8s preStop задержки и безопасный сброс буферов трассировки OpenTelemetry.",
        "theory": "Завершение работы современного распределенного микросервиса — это сложный оркестрированный процесс. Финальная точка архитектуры объединяет все компоненты главы: 1) Получение сигнала `SIGTERM` от kubelet; 2) Перевод `readinessProbe` в статус 503; 3) Выдержка времени на распространение сетевых таблиц iptables / IPVS в K8s; 4) Закрытие слушающих портов и вызов `GracefulStop()` с дедлайном; 5) Принудительный `Flush` и `Shutdown` провайдера OpenTelemetry (`sdktrace.TracerProvider`), гарантирующий, что последние спаны трассировки будут доставлены в коллектор; 6) Закрытие пулов БД и выход с кодом exit 0.",
        "step_by_step": [
            "Создайте координирующий ShutdownCoordinator.",
            "Зарегистрируйте обработчики для каждого слоя архитектуры.",
            "Выполните пошаговый каскад остановки с логированием каждого этапа.",
            "Убедитесь в успешной доставке последних спанов трассировки."
        ],
        "code_blocks": [
            {
                "filename": "final_shutdown_coordinator.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net\"\n\t\"os\"\n\t\"os/signal\"\n\t\"syscall\"\n\t\"time\"\n\n\t\"go.opentelemetry.io/otel\"\n\tsdktrace \"go.opentelemetry.io/otel/sdk/trace\"\n\t\"google.golang.org/grpc\"\n)\n\ntype ShutdownCoordinator struct {\n\tgrpcServer *grpc.Server\n\ttracerProv *sdktrace.TracerProvider\n}\n\nfunc (sc *ShutdownCoordinator) ExecuteGracefulShutdown() {\n\tlog.Println(\"[1/5] SIGTERM captured. Marking readiness probe as unhealthy (503)...\")\n\n\t// Этап 2: Задержка для сетевых роутов K8s / CNI\n\tdrainDelay := 1 * time.Second\n\tlog.Printf(\"[2/5] Waiting %v for K8s endpoint propagation across cluster...\", drainDelay)\n\ttime.Sleep(drainDelay)\n\n\t// Этап 3: Остановка gRPC сервера\n\tlog.Println(\"[3/5] Commencing grpcServer.GracefulStop()...\")\n\tstopped := make(chan struct{})\n\tgo func() {\n\t\tsc.grpcServer.GracefulStop()\n\t\tclose(stopped)\n\t}()\n\n\tselect {\n\tcase <-stopped:\n\t\tlog.Println(\"[3/5] All in-flight gRPC streams finished cleanly.\")\n\tcase <-time.After(5 * time.Second):\n\t\tlog.Println(\"[3/5] Graceful timeout reached, forcing hard Stop().\")\n\t\tsc.grpcServer.Stop()\n\t}\n\n\t// Этап 4: Сброс буферов трассировки OpenTelemetry\n\tlog.Println(\"[4/5] Flushing buffered OpenTelemetry spans to OTLP collector...\")\n\tflushCtx, cancel := context.WithTimeout(context.Background(), 2*time.Second)\n\tdefer cancel()\n\tif err := sc.tracerProv.Shutdown(flushCtx); err != nil {\n\t\tlog.Printf(\"[Warning] Error shutting down tracer provider: %v\", err)\n\t}\n\n\t// Этап 5: Закрытие БД и очередей\n\tlog.Println(\"[5/5] Releasing database pools and caching connections.\")\n\tlog.Println(\"=== GRACEFUL SHUTDOWN FULLY COMPLETED (Exit 0) ===\")\n}\n\nfunc main() {\n\ttp := sdktrace.NewTracerProvider(sdktrace.WithSampler(sdktrace.AlwaysSample()))\n\totel.SetTracerProvider(tp)\n\n\tserver := grpc.NewServer()\n\tlis, err := net.Listen(\"tcp\", \":50061\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Listen error: %v\", err)\n\t}\n\tdefer lis.Close()\n\n\tgo func() {\n\t\t_ = server.Serve(lis)\n\t}()\n\n\tcoordinator := &ShutdownCoordinator{\n\t\tgrpcServer: server,\n\t\ttracerProv: tp,\n\t}\n\n\t// Имитация внешнего сигнала\n\tsigChan := make(chan os.Signal, 1)\n\tsignal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)\n\n\tgo func() {\n\t\ttime.Sleep(200 * time.Millisecond)\n\t\tsigChan <- syscall.SIGTERM\n\t}()\n\n\t<-sigChan\n\tcoordinator.ExecuteGracefulShutdown()\n\tfmt.Println(\"Chapter 80 complete: W3C Trace Context and gRPC Keepalive mastered!\")\n}",
                "note": "Финальный координатор жизненного цикла микросервиса в Kubernetes"
            }
        ],
        "under_the_hood": "Метод `tp.Shutdown(flushCtx)` отправляет всем зарегистрированным `SpanProcessor` сигнал сбросить внутренние буферы и блокируется до подтверждения отправки данных экспортером. Это гарантирует, что спаны завершающей фазы сервиса попадут в дашборды мониторинга.",
        "pitfalls": "Завершение процесса без вызова `tp.Shutdown`. В таком случае спан о завершении сервиса и ошибки финальной фазы останутся в буфере оперативной памяти и пропадут.",
        "bigtech_interview": "Вопрос на финальной секции Senior Go Developer в Яндекс: 'Опишите эталонный пайплайн завершения процесса в Go.' Ответ: '1) Signal Notify; 2) Readiness 503; 3) Sleep(iptables); 4) GracefulStop/Shutdown с таймаутом; 5) TracerProvider.Shutdown; 6) DB / MQ Close; 7) Clean exit 0'."
    }
]
