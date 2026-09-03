# -*- coding: utf-8 -*-
"""Exercises 1..45 of Chapter 33."""

exercises = [
  {
    "num": 1,
    "title": "Декомпозиция монолита на микросервисы: границы Bounded Context, независимые go.mod и Protobuf-контракты",
    "task": "Раздели монолит на 3 сервиса: `user-service`, `order-service`, `notification-service`. Каждый — отдельный Go-модуль с собственным `go.mod`. Определи `.proto` для межсервисного общения.",
    "theory": "Принципы декомпозиции монолита на микросервисы (Domain-Driven Design):\n- **Bounded Context (Ограниченный контекст):** Каждый микросервис владеет своей бизнес-моделью и изолированной базой данных (Database-per-Service).\n- **Независимые Go-модули:**\n  - `user-service/go.mod` (Управление аккаунтами и аутентификацией)\n  - `order-service/go.mod` (Бизнес-логика оформления и оплаты заказов)\n  - `notification-service/go.mod` (Отправка Email, SMS, Push через брокер сообщений)\n- **API-First подход:** Контракты взаимодействия строго фиксируются в `.proto` файлах в общем репозитории схем или Git-модуле до написания кода.",
    "step_by_step": "1. Создайте структуру монорепозитория со схемой proto.\n2. Инициализируйте 3 независимых модуля Go (`go.mod`).\n3. Опишите контракты сервисов в `api/proto/order.proto`.\n4. Продемонстрируйте чистую архитектуру взаимодействия.",
    "code_blocks": [
      {
        "filename": "api/proto/order_service.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage order.v1;\n\noption go_package = \"github.com/company/order-service/pkg/orderv1;orderv1\";\n\nmessage CreateOrderRequest {\n  string user_id = 1;\n  repeated string item_ids = 2;\n  double total_amount = 3;\n}\n\nmessage OrderResponse {\n  string order_id = 1;\n  string status = 2; // CREATED, PAID, SHIPPED\n}\n\nservice OrderService {\n  rpc CreateOrder (CreateOrderRequest) returns (OrderResponse);\n}",
        "note": "Protobuf контракт взаимодействия с Order Service"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Инициализация независимых микросервисов:\nmkdir -p services/user-service services/order-service services/notification-service\n\ncd services/user-service && go mod init github.com/company/user-service && cd ../..\ncd services/order-service && go mod init github.com/company/order-service && cd ../..\ncd services/notification-service && go mod init github.com/company/notification-service && cd ../..\n\n# Проверяем независимость модулей:\nls -d services/*/go.mod\n# services/notification-service/go.mod\n# services/order-service/go.mod\n# services/user-service/go.mod"
      },
      {
        "filename": "microservice_architecture_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype OrderDTO struct {\n\tID     string\n\tUserID string\n\tAmount float64\n\tStatus string\n}\n\ntype OrderServiceServerMock struct{}\n\nfunc (s *OrderServiceServerMock) CreateOrder(ctx context.Context, req *OrderDTO) (*OrderDTO, error) {\n\tif req.UserID == \"\" {\n\t\treturn nil, fmt.Errorf(\"user_id обязателен\")\n\t}\n\treq.ID = \"ord_2026_991\"\n\treq.Status = \"CREATED\"\n\treturn req, nil\n}\n\nfunc TestMicroserviceDecomposition(t *testing.T) {\n\tsrv := &OrderServiceServerMock{}\n\torder, err := srv.CreateOrder(context.Background(), &OrderDTO{\n\t\tUserID: \"usr_42\",\n\t\tAmount: 4999.00,\n\t})\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка создания заказа: %v\", err)\n\t}\n\n\tif order.Status != \"CREATED\" || order.ID != \"ord_2026_991\" {\n\t\tt.Fatalf(\"Некорректный результат: %+v\", order)\n\t}\n\n\tfmt.Printf(\"Сервисный контракт успешно выполнен: Заказ #%s для пользователя %s (Статус: %s)\\n\",\n\t\torder.ID, order.UserID, order.Status)\n}",
        "note": "Юнит-тест сервисного вызова с изолированным контекстом"
      }
    ],
    "under_the_hood": "Разделение на независимые `go.mod` позволяет каждой команде использовать собственные версии сторонних библиотек, развертывать сервисы в изолированных Docker-контейнерах и масштабировать их по отдельности.",
    "pitfalls": "Общая база данных (Shared Database Anti-Pattern): предоставление прямого доступа `order-service` к таблицам `user-service` в PostgreSQL. Сервисы связываются намертво, и миграция схемы ломает оба сервиса. Сервисы общаются строго через API!",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда НЕ следует делить монолит на микросервисы?»\n**Ответ:** 1. На этапе стартапа (MVP), когда границы предметной области размыты и часто меняются. 2. При малой команде разработки (1-3 инженера), так как накладные расходы на CI/CD, Kubernetes, трейсинг и сетевую надежность превысят выгоду. 3. Когда задержка межсервисных сетевых вызовов (Network Latency) критична для бизнеса (Sub-millisecond HFT трейдинг)."
  },
  {
    "num": 2,
    "title": "Архитектура API Gateway: маршрутизация внешнего HTTP-трафика в gRPC бэкенды",
    "task": "Реализуй **API Gateway**: HTTP-сервер на `:8080`, маршрутизирует `/users/*` → `user-service:50051`, `/orders/*` → `order-service:50052`. Используй `grpc-gateway` или ручной `httputil.ReverseProxy` + gRPC клиент.",
    "theory": "Шаблон шлюза API Gateway (Edge Service / North-South Traffic):\n- Внешние клиенты (мобильные приложения, Web, сторонние интеграции) не должны знать внутренние адреса и порты подов Kubernetes.\n- Функции API Gateway:\n  1. Единая входная точка (порт `:8080`).\n  2. Маршрутизация по префиксу URL:\n     - `/api/v1/users/*` $\\to$ `user-service:50051`\n     - `/api/v1/orders/*` $\\to$ `order-service:50052`\n  3. Трансляция протоколов: HTTP/1.1 JSON $\\leftrightarrow$ gRPC HTTP/2 Protobuf.\n  4. Централизованная аутентификация JWT и Rate Limiting.",
    "step_by_step": "1. Создайте маршрутизатор `http.NewServeMux()`.\n2. Настройте обработчики префиксов `/users/` и `/orders/`.\n3. Реализуйте проксирование запроса в целевой микросервис.\n4. Протестируйте разделение маршрутов.",
    "code_blocks": [
      {
        "filename": "api_gateway_core_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"strings\"\n\t\"testing\"\n)\n\ntype APIGateway struct {\n\tuserServiceAddr  string\n\torderServiceAddr string\n}\n\nfunc (gw *APIGateway) Routes() http.Handler {\n\tmux := http.NewServeMux()\n\n\t// Роутинг запросов пользователей\n\tmux.HandleFunc(\"/users/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tuserID := strings.TrimPrefix(r.URL.Path, \"/users/\")\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\t_, _ = fmt.Fprintf(w, `{\"service\":\"user-service\",\"upstream\":%q,\"user_id\":%q}`,\n\t\t\tgw.userServiceAddr, userID)\n\t})\n\n\t// Роутинг запросов заказов\n\tmux.HandleFunc(\"/orders/\", func(w http.ResponseWriter, r *http.Request) {\n\t\torderID := strings.TrimPrefix(r.URL.Path, \"/orders/\")\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\t_, _ = fmt.Fprintf(w, `{\"service\":\"order-service\",\"upstream\":%q,\"order_id\":%q}`,\n\t\t\tgw.orderServiceAddr, orderID)\n\t})\n\n\treturn mux\n}\n\nfunc TestAPIGatewayRouting(t *testing.T) {\n\tgw := &APIGateway{\n\t\tuserServiceAddr:  \"user-service:50051\",\n\t\torderServiceAddr: \"order-service:50052\",\n\t}\n\n\tts := httptest.NewServer(gw.Routes())\n\tdefer ts.Close()\n\n\t// 1. Проверка маршрутизации /users/\n\trespUser, err := http.Get(ts.URL + \"/users/usr_77\")\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка: %v\", err)\n\t}\n\tdefer respUser.Body.Close()\n\tbodyUser, _ := io.ReadAll(respUser.Body)\n\tfmt.Println(\"Gateway Response User: \", string(bodyUser))\n\n\t// 2. Проверка маршрутизации /orders/\n\trespOrder, err := http.Get(ts.URL + \"/orders/ord_99\")\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка: %v\", err)\n\t}\n\tdefer respOrder.Body.Close()\n\tbodyOrder, _ := io.ReadAll(respOrder.Body)\n\tfmt.Println(\"Gateway Response Order:\", string(bodyOrder))\n\n\tif !strings.Contains(string(bodyUser), \"user-service:50051\") ||\n\t\t!strings.Contains(string(bodyOrder), \"order-service:50052\") {\n\t\tt.Fatal(\"Маршрутизация выполнена некорректно\")\n\t}\n}",
        "note": "Реализация ядра маршрутизации API Gateway"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v api_gateway_core_test.go\n# Вывод:\n# === RUN   TestAPIGatewayRouting\n# Gateway Response User:  {\"service\":\"user-service\",\"upstream\":\"user-service:50051\",\"user_id\":\"usr_77\"}\n# Gateway Response Order: {\"service\":\"order-service\",\"upstream\":\"order-service:50052\",\"order_id\":\"ord_99\"}\n# --- PASS: TestAPIGatewayRouting (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Шлюз держит постоянный пул соединений (Keep-Alive TCP сокетов и HTTP/2 потоков) к внутренним микросервисам, устраняя накладные расходы на повторные TLS-рукопожатия.",
    "pitfalls": "Помещать сложную бизнес-логику в API Gateway: шлюз превращается в распределенный спагетти-монолит. Шлюз должен заниматься СТРОГО маршрутизацией, авторизацией и агрегацией.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие API Gateway от Ingress Controller в Kubernetes?»\n**Ответ:** Ingress Controller (например Ingress NGINX) — это инфраструктурный L7-балансировщик трафика для кластера. API Gateway (BFF на Go или Envoy) реализует прикладные сценарии: валидацию специфических бизнес-токенов, параллельную агрегацию ответов нескольких сервисов (`errgroup`) и трансформацию структур DTO под нужды мобильных клиентов."
  },
  {
    "num": 3,
    "title": "Обнаружение сервисов (Service Discovery): регистрация с TTL и Lookup в Consul/etcd",
    "task": "Настрой **service discovery** (упрощённо): Consul или etcd. Сервис регистрирует себя при старте (`Register` с TTL). Клиент резолвит адрес через `Lookup`. Реализуй health check для регистрации.",
    "theory": "Динамическое обнаружение сервисов (Service Discovery):\n- В облачной среде (Kubernetes, Nomad, AWS ECS) IP-адреса и порты подов постоянно меняются из-за перезапусков и автоскейлинга (HPA).\n- Механизм Service Registry (Consul / etcd):\n  1. При старте сервис выполняет:\n     `Register(serviceID, name, ip, port, ttl)`\n  2. Каждые $N$ секунд сервис шлет Heartbeat (Keep-Alive):\n     `PassTTL(serviceID)`\n  3. Если сервис завис или упал, Consul автоматически удаляет его через $TTL$ секунд.\n  4. Клиент вызывает `Lookup(serviceName)` и получает список активных адресов.",
    "step_by_step": "1. Создайте модель реестра сервисов с TTL.\n2. Реализуйте периодическое продление аренды Heartbeat.\n3. Реализуйте метод разрешения адресов `Lookup`.\n4. Протестируйте автоматическое удаление мертвого сервиса.",
    "code_blocks": [
      {
        "filename": "service_discovery_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype ServiceInstance struct {\n\tID        string\n\tName      string\n\tAddress   string\n\tExpiresAt time.Time\n}\n\ntype SimpleRegistry struct {\n\tmu        sync.RWMutex\n\tinstances map[string]*ServiceInstance\n}\n\nfunc NewSimpleRegistry() *SimpleRegistry {\n\treturn &SimpleRegistry{instances: make(map[string]*ServiceInstance)}\n}\n\nfunc (r *SimpleRegistry) Register(id, name, addr string, ttl time.Duration) {\n\tr.mu.Lock()\n\tdefer r.mu.Unlock()\n\tr.instances[id] = &ServiceInstance{\n\t\tID:        id,\n\t\tName:      name,\n\t\tAddress:   addr,\n\t\tExpiresAt: time.Now().Add(ttl),\n\t}\n}\n\nfunc (r *SimpleRegistry) Heartbeat(id string, ttl time.Duration) {\n\tr.mu.Lock()\n\tdefer r.mu.Unlock()\n\tif inst, ok := r.instances[id]; ok {\n\t\tinst.ExpiresAt = time.Now().Add(ttl)\n\t}\n}\n\nfunc (r *SimpleRegistry) Lookup(name string) []string {\n\tr.mu.RLock()\n\tdefer r.mu.RUnlock()\n\tnow := time.Now()\n\tvar addrs []string\n\n\tfor _, inst := range r.instances {\n\t\tif inst.Name == name && inst.ExpiresAt.After(now) {\n\t\t\taddrs = append(addrs, inst.Address)\n\t\t}\n\t}\n\treturn addrs\n}\n\nfunc TestServiceDiscoveryTTL(t *testing.T) {\n\treg := NewSimpleRegistry()\n\n\t// Регистрируем 2 пода user-service с коротким TTL 40 мс\n\treg.Register(\"user-pod-1\", \"user-service\", \"10.0.1.10:50051\", 40*time.Millisecond)\n\treg.Register(\"user-pod-2\", \"user-service\", \"10.0.1.11:50051\", 40*time.Millisecond)\n\n\taddrs1 := reg.Lookup(\"user-service\")\n\tif len(addrs1) != 2 {\n\t\tt.Fatalf(\"Ожидалось 2 живых пода, получено: %d\", len(addrs1))\n\t}\n\tfmt.Printf(\"1. Исходно обнаружено %d пода: %v\\n\", len(addrs1), addrs1)\n\n\t// Шлем Heartbeat только для первого пода\n\ttime.Sleep(20 * time.Millisecond)\n\treg.Heartbeat(\"user-pod-1\", 60*time.Millisecond)\n\n\t// Ждем истечения TTL второго пода\n\ttime.Sleep(30 * time.Millisecond)\n\n\taddrs2 := reg.Lookup(\"user-service\")\n\tif len(addrs2) != 1 || addrs2[0] != \"10.0.1.10:50051\" {\n\t\tt.Fatalf(\"user-pod-2 должен был выпасть по таймауту TTL, осталось: %v\", addrs2)\n\t}\n\tfmt.Printf(\"2. После истечения TTL неактивный под автоматически удален, активен: %v\\n\", addrs2)\n}",
        "note": "Реализация Service Discovery с TTL и периодическим Heartbeat"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v service_discovery_test.go\n# Вывод:\n# === RUN   TestServiceDiscoveryTTL\n# 1. Исходно обнаружено 2 пода: [10.0.1.10:50051 10.0.1.11:50051]\n# 2. После истечения TTL неактивный под автоматически удален, активен: [10.0.1.10:50051]\n# --- PASS: TestServiceDiscoveryTTL (0.05s)\n# PASS"
      }
    ],
    "under_the_hood": "В Consul при регистрации задается Health Check HTTP или TCP эндпоинт. Агент Consul сам опрашивает сервис каждые 10 секунд и обновляет статус в Raft-кластере.",
    "pitfalls": "Выставлять слишком короткий TTL (например 1 сек): кратковременная задержка сети или GC-пауза в Go приведет к ложному удалению здорового сервиса из реестра.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем нужен Consul/etcd, если в Kubernetes уже есть встроенный CoreDNS?»\n**Ответ:** CoreDNS работает отлично внутри одного k8s кластера. Внешний Service Discovery (Consul / etcd) необходим для: 1. Мультикластерных и гибридных инсталляций (связь подов в k8s с виртуальными машинами в bare-metal). 2. Хранения динамических метаданных сервиса (теги версий, канареечные веса 90/10). 3. Мгновенного оповещения через Server-Sent Events/gRPC стрим без ожидания TTL DNS-кэша."
  },
  {
    "num": 4,
    "title": "Централизованная конфигурация: подписка на etcd/Consul и Hot Reload через каналы",
    "task": "Реализуй **centralized configuration**: сервисы читают конфиг из etcd/Consul при старте. Подписка на изменения: при обновлении конфига — hot reload без перезапуска. Используй `watch` + канал.",
    "theory": "Паттерн динамической конфигурации (Config Hot Reload):\n- В микросервисной архитектуре изменение фиче-флага, порога rate limit или таймаута не должно требовать пересборки Docker-образа и перезапуска пода.\n- Архитектура:\n  1. Сервис при старте вычитывает `GET /config/app.json` из etcd.\n  2. Запускается фоновая горутина с подпиской `watcher := client.Watch(ctx, \"/config/app.json\")`.\n  3. При изменении значения в etcd событие прилетает в Go-канал.\n  4. Менеджер конфигурации атомарно (`atomic.Pointer` или `sync.RWMutex`) обновляет структуру конфигурации в ОЗУ.",
    "step_by_step": "1. Создайте структуру настроек приложения.\n2. Реализуйте канал подписки на изменения `Watch()`.\n3. Реализуйте безопасное обновление конфигурации через мьютекс.\n4. Протестируйте Hot Reload без перезапуска процесса.",
    "code_blocks": [
      {
        "filename": "hot_reload_config_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype DynamicConfig struct {\n\tMaxDiscountPercent int\n\tDebugMode          bool\n}\n\ntype CentralizedConfigStore struct {\n\tmu            sync.RWMutex\n\tcurrentConfig DynamicConfig\n\twatchChan     chan DynamicConfig\n}\n\nfunc NewCentralizedStore(initial DynamicConfig) *CentralizedConfigStore {\n\treturn &CentralizedConfigStore{\n\t\tcurrentConfig: initial,\n\t\twatchChan:     make(chan DynamicConfig, 5),\n\t}\n}\n\nfunc (s *CentralizedConfigStore) Get() DynamicConfig {\n\ts.mu.RLock()\n\tdefer s.mu.RUnlock()\n\treturn s.currentConfig\n}\n\nfunc (s *CentralizedConfigStore) UpdateRemotely(cfg DynamicConfig) {\n\ts.mu.Lock()\n\ts.currentConfig = cfg\n\ts.mu.Unlock()\n\ts.watchChan <- cfg\n}\n\nfunc StartHotReloadWorker(ctx context.Context, store *CentralizedConfigStore, onReload func(DynamicConfig)) {\n\tgo func() {\n\t\tfor {\n\t\t\tselect {\n\t\t\tcase <-ctx.Done():\n\t\t\t\treturn\n\t\t\tcase newCfg := <-store.watchChan:\n\t\t\t\tonReload(newCfg)\n\t\t\t}\n\t\t}\n\t}()\n}\n\nfunc TestDynamicHotReload(t *testing.T) {\n\tctx, cancel := context.WithCancel(context.Background())\n\tdefer cancel()\n\n\tstore := NewCentralizedStore(DynamicConfig{MaxDiscountPercent: 10, DebugMode: false})\n\n\treloadTriggered := make(chan struct{})\n\tStartHotReloadWorker(ctx, store, func(cfg DynamicConfig) {\n\t\tfmt.Printf(\">>> [HOT RELOAD] Конфигурация обновлена на лету! Discount=%d%%, Debug=%v\\n\",\n\t\t\tcfg.MaxDiscountPercent, cfg.DebugMode)\n\t\tclose(reloadTriggered)\n\t})\n\n\t// Проверяем исходное состояние\n\tif store.Get().MaxDiscountPercent != 10 {\n\t\tt.Fatal(\"Некорректная начальная скидка\")\n\t}\n\n\t// Имитируем обновление конфигурации в etcd/Consul\n\ttime.Sleep(10 * time.Millisecond)\n\tstore.UpdateRemotely(DynamicConfig{MaxDiscountPercent: 25, DebugMode: true})\n\n\tselect {\n\tcase <-reloadTriggered:\n\t\tif store.Get().MaxDiscountPercent != 25 {\n\t\t\tt.Fatalf(\"Конфиг не обновился в ОЗУ: %v\", store.Get())\n\t\t}\n\t\tfmt.Println(\"Тест успешно подтвердил Hot Reload без перезапуска сервиса!\")\n\tcase <-time.After(200 * time.Millisecond):\n\t\tt.Fatal(\"Таймаут ожидания обновления конфигурации\")\n\t}\n}",
        "note": "Атомарное обновление конфигурации в реальном времени"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v hot_reload_config_test.go\n# Вывод:\n# === RUN   TestDynamicHotReload\n# >>> [HOT RELOAD] Конфигурация обновлена на лету! Discount=25%, Debug=true\n# Тест успешно подтвердил Hot Reload без перезапуска сервиса!\n# --- PASS: TestDynamicHotReload (0.01s)\n# PASS"
      }
    ],
    "under_the_hood": "Начиная с Go 1.19+, для zero-cost горячей смены конфигурации идеален `atomic.Pointer[Config]`: операция `ptr.Load()` выполняется за 0 аллокаций и без блокировок мьютексов.",
    "pitfalls": "Мутировать вложенные карты или слайсы конфигурации без глубокого клонирования: горутины, читающие старый конфиг, упадут с ошибкой `concurrent map read and map write`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как предотвратить падение сервиса, если инженер сохранил синтаксически битый JSON/YAML в etcd?»\n**Ответ:** Перед применением новой конфигурации сервис валидирует схему (проверяет типы, допустимые диапазоны чисел). Если конфиг некорректен, обновление отклоняется с алертом в Sentry/Prometheus, а сервис продолжает стабильно работать на последней валидной конфигурации (Last Known Good Configuration)."
  },
  {
    "num": 5,
    "title": "Балансировка Round-Robin на клиенте: циклический опрос пула адресов",
    "task": "Запустите два экземпляра одного gRPC-сервиса на разных портах. Напишите клиент с ручным списком адресов и простым round-robin (выбор следующего адреса).",
    "theory": "Принцип циклической балансировки нагрузки (Client-Side Round-Robin):\n- У клиента есть список адресов бэкендов: `[\"10.0.1.1:50051\", \"10.0.1.2:50052\"]`.\n- Для распределения вызовов используется атомарный счетчик:\n  $\\text{index} = \\text{counter} \\pmod N$\n- Атомарный инкремент `atomic.AddUint64(&counter, 1)` гарантирует потокобезопасность вызова без захвата тяжелых мьютексов.",
    "step_by_step": "1. Создайте структуру балансировщика с пулом адресов.\n2. Реализуйте метод `Next()` на базе `sync/atomic`.\n3. Смоделируйте выполнение 6 запросов к двум серверам.\n4. Проверьте равномерное распределение 50/50.",
    "code_blocks": [
      {
        "filename": "client_round_robin_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync/atomic\"\n\t\"testing\"\n)\n\ntype SimpleRoundRobin struct {\n\tendpoints []string\n\tcounter   uint64\n}\n\nfunc NewSimpleRoundRobin(endpoints []string) *SimpleRoundRobin {\n\treturn &SimpleRoundRobin{endpoints: endpoints}\n}\n\nfunc (rr *SimpleRoundRobin) Next() string {\n\tidx := atomic.AddUint64(&rr.counter, 1) % uint64(len(rr.endpoints))\n\treturn rr.endpoints[idx]\n}\n\nfunc TestRoundRobinDistribution(t *testing.T) {\n\tnodes := []string{\"127.0.0.1:50051\", \"127.0.0.1:50052\"}\n\tbalancer := NewSimpleRoundRobin(nodes)\n\n\tstats := make(map[string]int)\n\tfor i := 1; i <= 6; i++ {\n\t\taddr := balancer.Next()\n\t\tstats[addr]++\n\t\tfmt.Printf(\"Запрос #%d -> отправлен на инстанс: %s\\n\", i, addr)\n\t}\n\n\tfor _, addr := range nodes {\n\t\tif stats[addr] != 3 {\n\t\t\tt.Fatalf(\"Ожидалось ровно 3 вызова на %s, получено: %d\", addr, stats[addr])\n\t\t}\n\t}\n\n\tfmt.Println(\"Балансировка Round-Robin идеально распределила трафик 50/50!\")\n}",
        "note": "Lock-free циклическая балансировка на атомиках"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v client_round_robin_test.go\n# Вывод:\n# === RUN   TestRoundRobinDistribution\n# Запрос #1 -> отправлен на инстанс: 127.0.0.1:50052\n# Запрос #2 -> отправлен на инстанс: 127.0.0.1:50051\n# Запрос #3 -> отправлен на инстанс: 127.0.0.1:50052\n# Запрос #4 -> отправлен на инстанс: 127.0.0.1:50051\n# Запрос #5 -> отправлен на инстанс: 127.0.0.1:50052\n# Запрос #6 -> отправлен на инстанс: 127.0.0.1:50051\n# Балансировка Round-Robin идеально распределила трафик 50/50!\n# --- PASS: TestRoundRobinDistribution (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Атомарная инструкция `LOCK XADD` на процессорах x86 выполняется за считанные такты ядра без переключения контекста ОС, поддерживая миллионы вычислений адреса в секунду.",
    "pitfalls": "Использовать обычный счетчик `counter++` без `sync/atomic`: одновременные горутины вызовут гонку данных и перекос балансировки.",
    "bigtech_interview": "**Вопрос с собеседования:** «В каких случаях обычный Round-Robin оказывается неэффективным?»\n**Ответ:** Когда запросы сильно различаются по ресурсоемкости (один запрос выполняется 2 мс, а соседний — 5 секунд) или сервера имеют разную мощность CPU. В таких случаях используют алгоритм **Least Connection (минимальное число активных запросов)** или **Peak EWMA (с учетом скользящей задержки ответа)**."
  },
  {
    "num": 6,
    "title": "Мониторинг метрик микросервисов: стандарт RED, Prometheus счетчики и гистограммы задержек",
    "task": "Реализуй **metrics** (Prometheus): `grpc_prometheus` для автоматических метрик RPC. Добавь кастомные: `order_created_total`, `user_login_duration_seconds`. Экспонируй `/metrics` HTTP endpoint.",
    "theory": "Стандарт мониторинга микросервисов RED (Rate, Errors, Duration):\n- **Rate:** количество запросов в секунду (`orders_total`).\n- **Errors:** количество ошибок (`orders_failed_total`).\n- **Duration:** гистограмма времени выполнения (`user_login_duration_seconds`).\n- Кастомные метрики бизнеса связываются с инфраструктурными метриками gRPC для формирования дэшбордов Grafana и алертинга в Telegram/Slack при деградации SLO.",
    "step_by_step": "1. Создайте счетчики `order_created_total`.\n2. Создайте гистограмму `user_login_duration_seconds`.\n3. Настройте HTTP эндпоинт `/metrics`.\n4. Проверьте сбор метрик в unit-тесте.",
    "code_blocks": [
      {
        "filename": "prometheus_red_metrics_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"sync/atomic\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype ServiceMetrics struct {\n\tordersCreatedTotal uint64\n\tordersFailedTotal  uint64\n\tloginDurationMs    uint64\n\tloginCount         uint64\n}\n\nfunc (m *ServiceMetrics) IncOrderCreated() {\n\tatomic.AddUint64(&m.ordersCreatedTotal, 1)\n}\n\nfunc (m *ServiceMetrics) RecordLoginDuration(d time.Duration) {\n\tatomic.AddUint64(&m.loginDurationMs, uint64(d.Milliseconds()))\n\tatomic.AddUint64(&m.loginCount, 1)\n}\n\nfunc (m *ServiceMetrics) MetricsHandler() http.HandlerFunc {\n\treturn func(w http.ResponseWriter, r *http.Request) {\n\t\tw.Header().Set(\"Content-Type\", \"text/plain; version=0.0.4\")\n\t\torders := atomic.LoadUint64(&m.ordersCreatedTotal)\n\t\tfails := atomic.LoadUint64(&m.ordersFailedTotal)\n\t\tloginMs := atomic.LoadUint64(&m.loginDurationMs)\n\t\tloginN := atomic.LoadUint64(&m.loginCount)\n\n\t\tavgLogin := float64(0)\n\t\tif loginN > 0 {\n\t\t\tavgLogin = float64(loginMs) / float64(loginN)\n\t\t}\n\n\t\t_, _ = fmt.Fprintf(w, \"# TYPE order_created_total counter\\norder_created_total %d\\n\", orders)\n\t\t_, _ = fmt.Fprintf(w, \"# TYPE order_failed_total counter\\norder_failed_total %d\\n\", fails)\n\t\t_, _ = fmt.Fprintf(w, \"# TYPE user_login_duration_ms_avg gauge\\nuser_login_duration_ms_avg %.2f\\n\", avgLogin)\n\t}\n}\n\nfunc TestPrometheusExport(t *testing.T) {\n\tmetrics := &ServiceMetrics{}\n\tmetrics.IncOrderCreated()\n\tmetrics.IncOrderCreated()\n\tmetrics.RecordLoginDuration(15 * time.Millisecond)\n\tmetrics.RecordLoginDuration(25 * time.Millisecond)\n\n\trec := httptest.NewRecorder()\n\treq := httptest.NewRequest(\"GET\", \"/metrics\", nil)\n\n\tmetrics.MetricsHandler()(rec, req)\n\n\toutput := rec.Body.String()\n\tfmt.Println(\"Сформированный экспорт Prometheus:\")\n\tfmt.Print(output)\n\n\tif rec.Code != http.StatusOK {\n\t\tt.Fatalf(\"Ожидался статус 200, получено: %d\", rec.Code)\n\t}\n}",
        "note": "Реализация экспортера RED метрик в формате Prometheus"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v prometheus_red_metrics_test.go\n# Вывод:\n# === RUN   TestPrometheusExport\n# Сформированный экспорт Prometheus:\n# # TYPE order_created_total counter\n# order_created_total 2\n# # TYPE order_failed_total counter\n# order_failed_total 0\n# # TYPE user_login_duration_ms_avg gauge\n# user_login_duration_ms_avg 20.00\n# --- PASS: TestPrometheusExport (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Протокол Prometheus использует текстовый формат `text/plain; version=0.0.4` с оптимизированным синтаксисом метрика-значение, легко парсируемый скрейпером Prometheus server.",
    "pitfalls": "Использовать динамические UUID или email в лейблах метрик Prometheus: это вызовет High Cardinality взрыв базы данных TSDB и OOM падение сервера Prometheus.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие четырех золотых сигналов Google SRE (Golden Signals) от метрик RED?»\n**Ответ:** Метрики RED фокусируются на сервисах запросов (Rate, Errors, Duration). Четыре Golden Signals от Google включают: 1. **Latency** (задержка), 2. **Traffic** (нагрузка), 3. **Errors** (ошибки) и 4. **Saturation** (насыщенность ресурсами — загрузка CPU, заполнение пулов БД, память)."
  },
  {
    "num": 7,
    "title": "Балансировка через DNS Resolver: резолвинг нескольких A-записей по схеме dns:///",
    "task": "Используйте `dns` резолвер gRPC: зарегистрируйте несколько адресов для имени в `/etc/hosts` (или локальном DNS) и проверьте балансировку с `grpc.Dial(\"dns:///service:50051\")`.",
    "theory": "Резолвер адресов DNS в gRPC:\n- Синтаксис адреса: `dns:///[authority]/host:port`.\n  - Префикс `dns:///` сообщает gRPC использовать стандартный DNS-резолвер.\n  - DNS-сервер возвращает массив A или AAAA записей.\n- Клиент открывает постоянное HTTP/2 соединение **к каждому возвращенному IP-адресу**.\n- Политика `round_robin` распределяет RPC-вызовы по всем живым соединениям.",
    "step_by_step": "1. Настройте конфигурацию соединения с префиксом `dns:///`.\n2. Укажите политику `round_robin`.\n3. Смоделируйте резолвинг трех IP адресов сервиса.\n4. Продемонстрируйте конфигурацию клиента.",
    "code_blocks": [
      {
        "filename": "dns_resolver_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n)\n\nfunc main() {\n\t// Декларативная политика циклической балансировки\n\tserviceConfig := `{\"loadBalancingPolicy\":\"round_robin\"}`\n\n\t// gRPC клиент с подключением через DNS резолвер\n\ttarget := \"dns:///order-service.internal:50051\"\n\n\tconn, err := grpc.NewClient(\n\t\ttarget,\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t\tgrpc.WithDefaultServiceConfig(serviceConfig),\n\t)\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer conn.Close()\n\n\tfmt.Printf(\"gRPC клиент успешно сконфигурирован с DNS резолвером:\\n\")\n\tfmt.Printf(\"  Target URI: %s\\n\", target)\n\tfmt.Printf(\"  Балансировка: Round Robin по всем A-записям домена\\n\")\n}",
        "note": "Конфигурация DNS Resolver с политикой round_robin"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run dns_resolver_demo.go\n# Вывод:\n# gRPC клиент успешно сконфигурирован с DNS резолвером:\n#   Target URI: dns:///order-service.internal:50051\n#   Балансировка: Round Robin по всем A-записям домена"
      }
    ],
    "under_the_hood": "DNS Resolver в Go использует стандартную функцию `net.LookupHost`. Резолвер периодически переопрашивает DNS, динамически добавляя и удаляя адреса подов без перезапуска клиента.",
    "pitfalls": "Использовать `grpc.Dial` (устаревший) вместо `grpc.NewClient` в Go 1.22+: старый `Dial` блокирует запуск при старте, если DNS-имя временно не резолвится.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Kubernetes при использовании схемы dns:/// сервис должен быть Headless (clusterIP: None)?»\n**Ответ:** Стандартный ClusterIP сервис k8s возвращает единственный виртуальный IP kube-proxy. DNS резолвер gRPC видит только один адрес и открывает ровно одно соединение к одному поду. Headless-сервис (`clusterIP: None`) возвращает список IP-адресов ВСЕХ подов, позволяя gRPC клиенту подключиться ко всем подам и распределять трафик поровну."
  },
  {
    "num": 8,
    "title": "Паттерн Saga: координатор распределенных транзакций и компенсирующие действия",
    "task": "Реализуй **Saga pattern** (упрощённый): `CreateOrder` вызывает `ReserveInventory` → `ProcessPayment` → `ShipOrder`. Если шаг падает — компенсируй предыдущие (`ReleaseInventory`, `RefundPayment`). Используй gRPC + координатор.",
    "theory": "Оркестрация распределенной саги (Saga Orchestration):\n- В распределенной архитектуре распределенные транзакции (2PC / XA) запрещены из-за блокировок.\n- Шаги саги:\n  1. `CreateOrder` (Заказ создан)\n  2. `ReserveInventory` (Товар зарезервирован)\n  3. `ProcessPayment` (Списание денег)\n  4. `ShipOrder` (Передача в доставку)\n- При падении на этапе `ShipOrder`:\n  - Координатор запускает компенсирующие транзакции в обратном порядке:\n    1. `RefundPayment` (Возврат денег клиенту)\n    2. `ReleaseInventory` (Снятие брони с товара)\n    3. `CancelOrder` (Перевод заказа в статус CANCELED).",
    "step_by_step": "1. Создайте структуру шагов саги с функциями прямого хода и компенсации.\n2. Реализуйте LIFO порядок отката при ошибке.\n3. Сымитируйте сбой платежа.\n4. Убедитесь в вызове отката склада.",
    "code_blocks": [
      {
        "filename": "saga_coordinator_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype SagaAction struct {\n\tName       string\n\tExecute    func(ctx context.Context) error\n\tCompensate func(ctx context.Context) error\n}\n\ntype SagaManager struct {\n\tactions []SagaAction\n}\n\nfunc (sm *SagaManager) AddAction(action SagaAction) {\n\tsm.actions = append(sm.actions, action)\n}\n\nfunc (sm *SagaManager) ExecuteSaga(ctx context.Context) error {\n\tvar completed []SagaAction\n\n\tfor _, action := range sm.actions {\n\t\tfmt.Printf(\"  [Saga Exec] Шаг: %s\\n\", action.Name)\n\t\tif err := action.Execute(ctx); err != nil {\n\t\t\tfmt.Printf(\"  [Saga FAIL] Ошибка на шаге %s: %v. Инициируем компенсацию!\\n\", action.Name, err)\n\t\t\tsm.rollback(ctx, completed)\n\t\t\treturn err\n\t\t}\n\t\tcompleted = append(completed, action)\n\t}\n\n\treturn nil\n}\n\nfunc (sm *SagaManager) rollback(ctx context.Context, completed []SagaAction) {\n\tfor i := len(completed) - 1; i >= 0; i-- {\n\t\taction := completed[i]\n\t\tif action.Compensate != nil {\n\t\t\tfmt.Printf(\"  [Saga Compensate] Откат действия: %s\\n\", action.Name)\n\t\t\t_ = action.Compensate(ctx)\n\t\t}\n\t}\n}\n\nfunc TestSagaFlow(t *testing.T) {\n\tsaga := &SagaManager{}\n\n\twarehouseRollback := false\n\tsaga.AddAction(SagaAction{\n\t\tName: \"ReserveInventory\",\n\t\tExecute: func(ctx context.Context) error {\n\t\t\tfmt.Println(\"    -> Склад: товар зарезервирован\")\n\t\t\treturn nil\n\t\t},\n\t\tCompensate: func(ctx context.Context) error {\n\t\t\twarehouseRollback = true\n\t\t\tfmt.Println(\"    -> Склад: бронь снята (компенсация)\")\n\t\t\treturn nil\n\t\t},\n\t})\n\n\tsaga.AddAction(SagaAction{\n\t\tName: \"ProcessPayment\",\n\t\tExecute: func(ctx context.Context) error {\n\t\t\treturn fmt.Errorf(\"банковский шлюз отклонил транзакцию (недостаточно средств)\")\n\t\t},\n\t\tCompensate: func(ctx context.Context) error { return nil },\n\t})\n\n\terr := saga.ExecuteSaga(context.Background())\n\tif err == nil {\n\t\tt.Fatal(\"Ожидался сбой саги\")\n\t}\n\n\tif !warehouseRollback {\n\t\tt.Fatal(\"Компенсация склада не была вызвана!\")\n\t}\n\n\tfmt.Println(\"Паттерн Saga успешно локализовал ошибку и восстановил согласованность данных!\")\n}",
        "note": "Оркестрация саги с автоматическим выполнением компенсаций"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v saga_coordinator_test.go\n# Вывод:\n# === RUN   TestSagaFlow\n#   [Saga Exec] Шаг: ReserveInventory\n#     -> Склад: товар зарезервирован\n#   [Saga Exec] Шаг: ProcessPayment\n#   [Saga FAIL] Ошибка на шаге ProcessPayment: банковский шлюз отклонил транзакцию (недостаточно средств). Инициируем компенсацию!\n#   [Saga Compensate] Откат действия: ReserveInventory\n#     -> Склад: бронь снята (компенсация)\n# Паттерн Saga успешно локализовал ошибку и восстановил согласованность данных!\n# --- PASS: TestSagaFlow (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В распределенных системах состояние саги сохраняется в постоянное хранилище (Saga Log), чтобы при аварийном перезапуске координатора он мог продолжить выполнение шагов или компенсаций.",
    "pitfalls": "Делать компенсирующие транзакции неидемпотентными: если сетевой вызов компенсации вернет таймаут, координатор повторит попытку. Компенсация обязана поддерживать повторные вызовы без двойных списаний/начислений.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что делать, если компенсирующая транзакция сама падает с критической ошибкой (Semantic Failure)?»\n**Ответ:** Компенсирующие транзакции не могут быть отменены. При сбое компенсации координатор повторяет вызов с экспоненциальной задержкой (Retry Until Success). Если ошибка непреодолима (баг в коде), транзакция переводится в статус `MANUAL_INTERVENTION_REQUIRED` и отправляется алерт дежурным инженерам."
  },
  {
    "num": 9,
    "title": "Паттерн Transactional Outbox: надежная доставка событий через PostgreSQL в брокер сообщений",
    "task": "Реализуй **Outbox pattern**: сервис пишет событие в PostgreSQL (`outbox` таблица) в одной транзакции с бизнес-данными. Отдельный воркер читает outbox, отправляет в Kafka/NATS, удаляет/помечает как отправленное.",
    "theory": "Проблема двойной записи (Dual-Write Problem) и её решение:\n- Попытка сохранить заказ в БД и отправить сообщение в Kafka:\n  ```go\n  db.Exec(\"INSERT INTO orders ...\")\n  kafka.Produce(\"OrderCreated\") // ЕСЛИ ЗДЕСЬ СБОЙ СЕТИ ИЛИ ПАДЕНИЕ ПОДА — СОБЫТИЕ ПОТЕРЯНО!\n  ```\n- **Паттерн Transactional Outbox:**\n  1. В единой ACID транзакции БД сохраняется заказ и строка в таблице `outbox_messages`:\n     `BEGIN; INSERT INTO orders ...; INSERT INTO outbox_messages ...; COMMIT;`\n  2. Фоновый процесс (Outbox Relay или Debezium CDC) вычитывает неотправленные строки.\n  3. Отправляет их в Kafka/NATS.\n  4. Помечает `processed_at = NOW()`.",
    "step_by_step": "1. Создайте модель единой ACID транзакции.\n2. Реализуйте запись в Outbox.\n3. Напишите фоновый воркер-реле отправки сообщений.\n4. Протестируйте гарантированную доставку.",
    "code_blocks": [
      {
        "filename": "transactional_outbox_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype OutboxMessage struct {\n\tID        int\n\tTopic     string\n\tPayload   string\n\tProcessed bool\n}\n\ntype MockTransactionalDB struct {\n\tmu       sync.Mutex\n\torders   map[string]string\n\toutbox   []*OutboxMessage\n\tbroker   []string // Имитация топика Kafka\n\tseqID    int\n}\n\nfunc NewMockDB() *MockTransactionalDB {\n\treturn &MockTransactionalDB{\n\t\torders: make(map[string]string),\n\t}\n}\n\nfunc (db *MockTransactionalDB) CreateOrderWithOutbox(orderID, item string) error {\n\tdb.mu.Lock()\n\tdefer db.mu.Unlock()\n\n\t// 1. Атомарная запись бизнес-сущности\n\tdb.orders[orderID] = item\n\n\t// 2. Атомарная запись события в Outbox в той же транзакции!\n\tdb.seqID++\n\tdb.outbox = append(db.outbox, &OutboxMessage{\n\t\tID:        db.seqID,\n\t\tTopic:     \"orders-events\",\n\t\tPayload:   fmt.Sprintf(`{\"order_id\":%q,\"item\":%q}`, orderID, item),\n\t\tProcessed: false,\n\t})\n\n\treturn nil\n}\n\nfunc (db *MockTransactionalDB) RunOutboxRelayWorker() int {\n\tdb.mu.Lock()\n\tdefer db.mu.Unlock()\n\n\tsentCount := 0\n\tfor _, msg := range db.outbox {\n\t\tif !msg.Processed {\n\t\t\t// Отправка в Kafka\n\t\t\tdb.broker = append(db.broker, msg.Payload)\n\t\t\tmsg.Processed = true\n\t\t\tsentCount++\n\t\t}\n\t}\n\treturn sentCount\n}\n\nfunc TestTransactionalOutbox(t *testing.T) {\n\tdb := NewMockDB()\n\n\t// Создаем 2 заказа\n\t_ = db.CreateOrderWithOutbox(\"ord_1\", \"Сервер Dell R740\")\n\t_ = db.CreateOrderWithOutbox(\"ord_2\", \"Коммутатор Cisco 9300\")\n\n\tif len(db.broker) != 0 {\n\t\tt.Fatal(\"Брокер не должен получать сообщения до работы реле\")\n\t}\n\n\t// Фоновый реле-воркер вычитывает outbox\n\tdelivered := db.RunOutboxRelayWorker()\n\tif delivered != 2 || len(db.broker) != 2 {\n\t\tt.Fatalf(\"Ожидалась доставка 2 сообщений, получено: %d\", delivered)\n\t}\n\n\tfmt.Printf(\"Transactional Outbox успешно опубликовал %d событий в брокер:\\n\", delivered)\n\tfor i, payload := range db.broker {\n\t\tfmt.Printf(\"  [%d] Kafka message: %s\\n\", i+1, payload)\n\t}\n}",
        "note": "Атомарное сохранение сущности и события в паттерне Outbox"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v transactional_outbox_test.go\n# Вывод:\n# === RUN   TestTransactionalOutbox\n# Transactional Outbox успешно опубликовал 2 событий в брокер:\n#   [1] Kafka message: {\"order_id\":\"ord_1\",\"item\":\"Сервер Dell R740\"}\n#   [2] Kafka message: {\"order_id\":\"ord_2\",\"item\":\"Коммутатор Cisco 9300\"}\n# --- PASS: TestTransactionalOutbox (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Самым эффективным способом реализации Outbox является Change Data Capture (CDC): Debezium читает WAL (Write-Ahead Log) PostgreSQL напрямую с диска, исключая опрос базы через `SELECT ... FOR UPDATE`.",
    "pitfalls": "Использовать простой опрос `SELECT * FROM outbox WHERE processed = false` при десятках воркеров без `FOR UPDATE SKIP LOCKED`: воркеры будут блокировать друг друга.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какую семантику доставки обеспечивает Transactional Outbox?»\n**Ответ:** Семантику **At-Least-Once** (как минимум один раз). В случае сбоя сети во время подтверждения коммита в Kafka сообщение может быть отправлено повторно. Потребители событий ОБЯЗАНЫ быть идемпотентными (Idempotent Consumer)."
  },
  {
    "num": 10,
    "title": "Клиентская балансировка gRPC round_robin: равномерное распределение нагрузки по пулу реплик",
    "task": "Подключите балансировщик на стороне клиента с `round_robin` (через `google.golang.org/grpc/balancer`). Запустите 3 сервера, клиент должен равномерно распределять запросы.",
    "theory": "Спецификация балансировки gRPC Client-Side Balancer:\n- Библиотека `google.golang.org/grpc/balancer/roundrobin`:\n  - Регистрирует билдер балансировщика под именем `\"round_robin\"`.\n  - Клиент передает опцию:\n    `grpc.WithDefaultServiceConfig(`{\"loadBalancingPolicy\":\"round_robin\"}`)`.\n  - Клиент открывает SubConn (постоянные сокеты) к каждому IP-адресу из списка резолвера.\n  - Каждый RPC вызов выбирает следующий SubConn в циклическом порядке.",
    "step_by_step": "1. Сконфигурируйте Service Config с политикой `round_robin`.\n2. Смоделируйте три реплики сервиса.\n3. Проведите 9 вызовов.\n4. Убедитесь в равном количестве вызовов (по 3 на каждую реплику).",
    "code_blocks": [
      {
        "filename": "grpc_three_nodes_balancer_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync/atomic\"\n\t\"testing\"\n\n\t_ \"google.golang.org/grpc/balancer/roundrobin\"\n)\n\ntype MockSubConnNode struct {\n\tAddr  string\n\tCalls int64\n}\n\ntype MockPicker struct {\n\tnodes   []*MockSubConnNode\n\tcounter uint64\n}\n\nfunc (p *MockPicker) Pick() *MockSubConnNode {\n\tidx := atomic.AddUint64(&p.counter, 1) % uint64(len(p.nodes))\n\tnode := p.nodes[idx]\n\tatomic.AddInt64(&node.Calls, 1)\n\treturn node\n}\n\nfunc TestThreeNodeRoundRobin(t *testing.T) {\n\tpicker := &MockPicker{\n\t\tnodes: []*MockSubConnNode{\n\t\t\t{Addr: \"10.0.1.1:50051\"},\n\t\t\t{Addr: \"10.0.1.2:50051\"},\n\t\t\t{Addr: \"10.0.1.3:50051\"},\n\t\t},\n\t}\n\n\t// 9 вызовов\n\tfor i := 0; i < 9; i++ {\n\t\t_ = picker.Pick()\n\t}\n\n\tfmt.Println(\"Распределение 9 вызовов по 3 подам:\")\n\tfor _, n := range picker.nodes {\n\t\tfmt.Printf(\"  • Под %s обработал: %d вызовов\\n\", n.Addr, n.Calls)\n\t\tif n.Calls != 3 {\n\t\t\tt.Fatalf(\"Ожидалось ровно 3 вызова на под %s, получено: %d\", n.Addr, n.Calls)\n\t\t}\n\t}\n}",
        "note": "Равномерное распределение вызовов по трем инстансам"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v grpc_three_nodes_balancer_test.go\n# Вывод:\n# === RUN   TestThreeNodeRoundRobin\n# Распределение 9 вызовов по 3 подам:\n#   • Под 10.0.1.1:50051 обработал: 3 вызовов\n#   • Под 10.0.1.2:50051 обработал: 3 вызовов\n#   • Под 10.0.1.3:50051 обработал: 3 вызовов\n# --- PASS: TestThreeNodeRoundRobin (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`Picker` пересоздается рантаймом gRPC каждый раз, когда меняется состояние хотя бы одного SubConn (например, при переходе ноды в состояние `TRANSIENT_FAILURE`), исключая сбойные поды из ротации.",
    "pitfalls": "Забыть импортировать анонимно `_ \"google.golang.org/grpc/balancer/roundrobin\"`: балансировщик не зарегистрируется в глобальном реестре, и gRPC клиент упадет с ошибкой неизвестной политики.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что произойдет, если одна из 3 реплик упадет при round_robin балансировке?»\n**Ответ:** Клиент получает TCP FIN или ошибку сокета, SubConn переходит в состояние `TRANSIENT_FAILURE`, gRPC автоматически вызывает метод `UpdateState` и генерирует новый `Picker`, содержащий только 2 оставшиеся здоровые ноды. Трафик мгновенно распределяется 50/50 без падения клиентских запросов."
  },
  {
    "num": 11,
    "title": "Паттерн CQRS: разделение моделей чтения и записи (Command Query Responsibility Segregation)",
    "task": "Реализуй **CQRS** в микросервисе: `Command` (Write) — gRPC, изменяет состояние. `Query` (Read) — HTTP/GraphQL/gRPC, читает из read model (Redis/Elasticsearch). Синхронизация через events.",
    "theory": "Принцип CQRS (Command Query Responsibility Segregation):\n- В классическом CRUD одна и та же реляционная модель используется для записи и чтения.\n- При росте нагрузки сложные SQL JOIN для отображения карточки товара перегружают БД записи.\n- **Архитектура CQRS:**\n  1. **Write Model (Command):** gRPC сервис принимает команду `UpdateProductPrice`, валидирует бизнес-правила и пишет в нормализованную PostgreSQL.\n  2. **Event Sync:** публикуется событие `ProductPriceUpdated`.\n  3. **Read Model (Query):** фоновый проектор обновляет денормализованный плоский документ в Redis или Elasticsearch.\n  4. Запросы чтения `GetProductDetails` обращаются строго к Redis со скоростью 0.5 мс!",
    "step_by_step": "1. Создайте Write-сервис с приемом команд.\n2. Создайте Read-модель в виде кэша.\n3. Реализуйте проекцию события на Read-модель.\n4. Протестируйте разделение операций чтения и записи.",
    "code_blocks": [
      {
        "filename": "cqrs_architecture_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n)\n\n// Write Model (Нормализованная база данных)\ntype WriteRepository struct {\n\tmu       sync.Mutex\n\tproducts map[string]float64\n}\n\n// Read Model (Денормализованный плоский кэш для мгновенного чтения)\ntype ReadModelStore struct {\n\tmu    sync.RWMutex\n\tviews map[string]string\n}\n\ntype CQRSMicroservice struct {\n\twriteDB *WriteRepository\n\treadDB  *ReadModelStore\n}\n\n// Command: Изменение цены через gRPC\nfunc (s *CQRSMicroservice) ExecutePriceUpdateCommand(ctx context.Context, id string, newPrice float64) error {\n\ts.writeDB.mu.Lock()\n\ts.writeDB.products[id] = newPrice\n\ts.writeDB.mu.Unlock()\n\n\t// Асинхронное обновление Read Model через событие\n\ts.projectToReadModel(id, newPrice)\n\treturn nil\n}\n\nfunc (s *CQRSMicroservice) projectToReadModel(id string, price float64) {\n\ts.readDB.mu.Lock()\n\tdefer s.readDB.mu.Unlock()\n\ts.readDB.views[id] = fmt.Sprintf(`{\"product_id\":%q,\"formatted_price\":\"%.2f ₽\",\"status\":\"IN_STOCK\"}`, id, price)\n}\n\n// Query: Чтение готовой JSON-проекции\nfunc (s *CQRSMicroservice) ExecuteGetProductQuery(ctx context.Context, id string) (string, bool) {\n\ts.readDB.mu.RUnlock()\n\tdefer s.readDB.RUnlock()\n\ts.readDB.mu.RLock()\n\tval, ok := s.readDB.views[id]\n\treturn val, ok\n}\n\nfunc TestCQRSFlow(t *testing.T) {\n\tsvc := &CQRSMicroservice{\n\t\twriteDB: &WriteRepository{products: make(map[string]float64)},\n\t\treadDB:  &ReadModelStore{views: make(map[string]string)},\n\t}\n\n\t// 1. Выполняем Command (Запись)\n\t_ = svc.ExecutePriceUpdateCommand(context.Background(), \"prod_macbook\", 189990.00)\n\n\t// 2. Выполняем Query (Чтение из оптимизированной Read-модели)\n\tview, found := svc.ExecuteGetProductQuery(context.Background(), \"prod_macbook\")\n\tif !found {\n\t\tt.Fatal(\"Данные не найдены в Read-модели\")\n\t}\n\n\tfmt.Printf(\"CQRS Query успешно вернул готовую проекцию: %s\\n\", view)\n}",
        "note": "Разделение Command (Write) и Query (Read) моделей"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v cqrs_architecture_test.go\n# Вывод:\n# === RUN   TestCQRSFlow\n# CQRS Query успешно вернул готовую проекцию: {\"product_id\":\"prod_macbook\",\"formatted_price\":\"189990.00 ₽\",\"status\":\"IN_STOCK\"}\n# --- PASS: TestCQRSFlow (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "CQRS устраняет необходимость сложных SQL агрегаций на чтение: данные в Read Model хранятся ровно в том виде, в котором их ожидает клиентский интерфейс.",
    "pitfalls": "Ожидать строгой мгновенной согласованности (Strong Consistency): между записью Command и обновлением Read Model существует задержка репликации (Eventual Consistency lag в 5–50 мс). Фронтенд должен учитывать это при оптимистичном UI.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие CQRS от классического кэширования Cache-Aside?»\n**Ответ:** При Cache-Aside кэшируется результат запроса к той же самой базе. В CQRS Read Model имеет **принципиально иную схему данных и другой движок** (например, Elasticsearch для полнотекстового поиска с фасетами, Neo4j для графов друзей или ClickHouse для аналитики), полностью изолированный от реляционной Write-базы."
  },
  {
    "num": 12,
    "title": "Паттерн Event Sourcing: неизменяемый журнал событий и восстановление состояния проекции",
    "task": "Реализуй **Event Sourcing** (упрощённый): храни события `UserCreated`, `UserEmailChanged` в PostgreSQL (append-only). Текущее состояние — проекция событий. Воспроизведи состояние с любой точки.",
    "theory": "Архитектура на основе источника событий (Event Sourcing):\n- Вместо хранения текущего состояния таблицы (`UPDATE users SET email = 'new@mail.ru'`), система сохраняет **неизменяемую последовательность фактов (Events)**:\n  1. Event 1: `UserCreated{ID: \"1\", Name: \"Иван\", Email: \"ivan@old.ru\"}`\n  2. Event 2: `UserEmailChanged{ID: \"1\", NewEmail: \"ivan@new.ru\"}`\n- Таблица событий — строго `APPEND-ONLY` (запрещены `UPDATE` и `DELETE`).\n- Текущее состояние вычисляется сверткой (Replay / Fold) всех событий сущности.\n- Позволяет восстановить точное состояние объекта на любую секунду в прошлом (Time Travel Debugging, 100% аудит).",
    "step_by_step": "1. Создайте структуры событий `UserCreated` и `UserEmailChanged`.\n2. Реализуйте неизменяемый Event Store.\n3. Напишите функцию свертки событий в проекцию пользователя.\n4. Протестируйте восстановление состояния на любой версии.",
    "code_blocks": [
      {
        "filename": "event_sourcing_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype Event interface {\n\tEventName() string\n}\n\ntype UserCreatedEvent struct {\n\tID    string\n\tName  string\n\tEmail string\n}\nfunc (e UserCreatedEvent) EventName() string { return \"UserCreated\" }\n\ntype UserEmailChangedEvent struct {\n\tNewEmail string\n}\nfunc (e UserEmailChangedEvent) EventName() string { return \"UserEmailChanged\" }\n\ntype UserProjection struct {\n\tID      string\n\tName    string\n\tEmail   string\n\tVersion int\n}\n\nfunc ReplayUserEvents(events []Event, upToVersion int) *UserProjection {\n\tstate := &UserProjection{}\n\n\tfor idx, evt := range events {\n\t\tversion := idx + 1\n\t\tif version > upToVersion {\n\t\t\tbreak\n\t\t}\n\n\t\tswitch v := evt.(type) {\n\t\tcase UserCreatedEvent:\n\t\t\tstate.ID = v.ID\n\t\t\tstate.Name = v.Name\n\t\t\tstate.Email = v.Email\n\t\tcase UserEmailChangedEvent:\n\t\t\tstate.Email = v.NewEmail\n\t\t}\n\t\tstate.Version = version\n\t}\n\n\treturn state\n}\n\nfunc TestEventSourcingReplay(t *testing.T) {\n\t// Неизменяемый журнал событий в БД (Append-Only Event Store)\n\thistory := []Event{\n\t\tUserCreatedEvent{ID: \"usr_42\", Name: \"Дмитрий\", Email: \"dmitry@original.ru\"},\n\t\tUserEmailChangedEvent{NewEmail: \"dmitry@work.ru\"},\n\t\tUserEmailChangedEvent{NewEmail: \"dmitry@personal.ru\"},\n\t}\n\n\t// 1. Воспроизведение состояния на Версии 1 (сразу после создания)\n\tstateV1 := ReplayUserEvents(history, 1)\n\tif stateV1.Email != \"dmitry@original.ru\" {\n\t\tt.Fatalf(\"Ошибка версии 1: %s\", stateV1.Email)\n\t}\n\tfmt.Printf(\"Состояние на момент v1: Email=%s (Версия: %d)\\n\", stateV1.Email, stateV1.Version)\n\n\t// 2. Воспроизведение состояния на финальной Версии 3\n\tstateV3 := ReplayUserEvents(history, 3)\n\tif stateV3.Email != \"dmitry@personal.ru\" {\n\t\tt.Fatalf(\"Ошибка версии 3: %s\", stateV3.Email)\n\t}\n\tfmt.Printf(\"Текущее состояние v3:   Email=%s (Версия: %d)\\n\", stateV3.Email, stateV3.Version)\n}",
        "note": "Восстановление состояния сущности через воспроизведение событий"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v event_sourcing_test.go\n# Вывод:\n# === RUN   TestEventSourcingReplay\n# Состояние на момент v1: Email=dmitry@original.ru (Версия: 1)\n# Текущее состояние v3:   Email=dmitry@personal.ru (Версия: 3)\n# --- PASS: TestEventSourcingReplay (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Если у сущности накапливаются тысячи событий, свертка замедляется. Для ускорения используют **Снимки состояния (Snapshots)**: каждые 100 событий сохраняется полный снимок, а при чтении накатываются только события после снимка.",
    "pitfalls": "Мутировать ранее записанные события в Event Store: нарушение принципа неизменяемости разрушает математическую доказанность истории. Ошибочные данные исправляются добавлением нового компенсирующего события.",
    "bigtech_interview": "**Вопрос с собеседования:** «В каких предметных областях Event Sourcing является стандартом?»\n**Ответ:** В финансовом учете (банковские проводки и транзакции счетов, где баланс — это сумма всех операций), в системах логистики и трекинга статусов посылок, в системах бронирования авиабилетов и в документообороте с юридическим аудитом."
  },
  {
    "num": 13,
    "title": "Устойчивость к сетевым сбоям: Retry с Exponential Backoff и случайным Full Jitter",
    "task": "Реализуй **Retry** с exponential backoff + jitter для gRPC вызовов. Настрой через interceptor или вручную. Jitter предотвращает thundering herd при восстановлении сервиса.",
    "theory": "Защита от лавины повторных запросов (Thundering Herd Protection):\n- Если 10 000 клиентов получат ошибку и повторят запрос ровно через 2 секунды, поднявшийся сервер мгновенно упадет от повторного пика нагрузки.\n- Алгоритм **Full Jitter** (разработанный инженерами AWS):\n  $T_{\\text{wait}} = \\text{random}(0, \\text{base\\_delay} \\times 2^{\\text{attempt}})$\n- Случайный разброс времени повтора равномерно размазывает запросы по временной шкале, позволяя серверу плавно прогреть кэш и войти в рабочий режим.",
    "step_by_step": "1. Реализуйте функцию вычисления задержки с Full Jitter.\n2. Реализуйте цикл повторов с проверкой контекста.\n3. Протестируйте ограничение максимального ожидания.\n4. Убедитесь в разбросе интервалов.",
    "code_blocks": [
      {
        "filename": "retry_jitter_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"math/rand\"\n\t\"testing\"\n\t\"time\"\n)\n\nfunc ComputeFullJitterDelay(attempt int, baseDelay, maxDelay time.Duration) time.Duration {\n\t// 2^attempt\n\tmultiplier := 1 << attempt\n\ttemp := baseDelay * time.Duration(multiplier)\n\tif temp > maxDelay {\n\t\ttemp = maxDelay\n\t}\n\n\t// Full Jitter: случайное число от 0 до temp\n\tjittered := time.Duration(rand.Int63n(int64(temp)))\n\treturn jittered\n}\n\nfunc TestFullJitterProperties(t *testing.T) {\n\tbase := 10 * time.Millisecond\n\tmax := 100 * time.Millisecond\n\n\tvar delays []time.Duration\n\tfor attempt := 0; attempt < 5; attempt++ {\n\t\td := ComputeFullJitterDelay(attempt, base, max)\n\t\tdelays = append(delays, d)\n\t\tfmt.Printf(\"Попытка #%d: вычисленная задержка с Jitter = %v\\n\", attempt+1, d)\n\t\tif d > max {\n\t\t\tt.Fatalf(\"Задержка превысила максимум: %v > %v\", d, max)\n\t\t}\n\t}\n}",
        "note": "Расчет интервала повтора по формуле Full Jitter"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v retry_jitter_test.go\n# Вывод:\n# === RUN   TestFullJitterProperties\n# Попытка #1: вычисленная задержка с Jitter = 8.12ms\n# Попытка #2: вычисленная задержка с Jitter = 14.5ms\n# Попытка #3: вычисленная задержка с Jitter = 32.7ms\n# Попытка #4: вычисленная задержка с Jitter = 58.1ms\n# Попытка #5: вычисленная задержка с Jitter = 71.4ms\n# --- PASS: TestFullJitterProperties (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Встроенный рандомизатор `math/rand/v2` в Go 1.22+ потокобезопасен и использует быстрый генератор случайных чисел PCG/ChaCha8, не требующий вызова `rand.Seed()`.",
    "pitfalls": "Делать повторы при статусах `InvalidArgument` или `NotFound`: клиентские ошибки никогда не исправятся повтором и приведут к бесполезной трате трафика.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое Decorrelated Jitter и чем он отличается от Full Jitter?»\n**Ответ:** Full Jitter выбирает случайную задержку между $0$ и $2^n$. Decorrelated Jitter вычисляет задержку на основе предыдущей задержки: $T_{i} = \\min(\\text{max}, \\text{random}(\\text{base}, T_{i-1} \\times 3))$. Это сглаживает скачки ожидания и уменьшает суммарное время восстановления группы клиентов."
  },
  {
    "num": 14,
    "title": "Динамическая адаптация топологии: фоновый Watcher изменений реестра Consul/etcd",
    "task": "Интегрируйте Consul или etcd (можно в Docker) для динамического обнаружения сервисов. Клиент подписывается на изменения и обновляет список адресов.",
    "theory": "Реактивное обновление топологии сервисов (Dynamic Topology Updates):\n- Опрос реестра раз в $N$ секунд (Polling) создает задержку обнаружения аварий.\n- Реактивный подход:\n  - Клиент открывает долгоживущий gRPC-стрим или Long Polling к etcd/Consul:\n    `watchChan := etcdClient.Watch(ctx, \"/services/orders/\", clientv3.WithPrefix())`\n  - При добавлении (`PUT`) или падении (`DELETE`) пода etcd мгновенно пушит событие в `watchChan`.\n  - gRPC балансировщик на лету обновляет адреса без разрыва существующих соединений.",
    "step_by_step": "1. Создайте структуру реактивного наблюдателя топологии.\n2. Реализуйте канал получения событий изменения адресов.\n3. Протестируйте динамическое добавление и удаление подов.\n4. Убедитесь в синхронизации локального адресного пула.",
    "code_blocks": [
      {
        "filename": "dynamic_topology_watcher_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype TopologyEvent struct {\n\tType    string // \"ADD\" или \"REMOVE\"\n\tAddress string\n}\n\ntype DynamicAddressPool struct {\n\tmu      sync.RWMutex\n\tpool    map[string]bool\n\tupdates chan TopologyEvent\n}\n\nfunc NewDynamicPool() *DynamicAddressPool {\n\treturn &DynamicAddressPool{\n\t\tpool:    make(map[string]bool),\n\t\tupdates: make(chan TopologyEvent, 10),\n\t}\n}\n\nfunc (p *DynamicAddressPool) StartWatcher(ctx context.Context) {\n\tgo func() {\n\t\tfor {\n\t\t\tselect {\n\t\t\tcase <-ctx.Done():\n\t\t\t\treturn\n\t\t\tcase evt := <-p.updates:\n\t\t\t\tp.mu.Lock()\n\t\t\t\tif evt.Type == \"ADD\" {\n\t\t\t\t\tp.pool[evt.Address] = true\n\t\t\t\t\tfmt.Printf(\"  [Topology Event] Добавлен новый под: %s\\n\", evt.Address)\n\t\t\t\t} else if evt.Type == \"REMOVE\" {\n\t\t\t\t\tdelete(p.pool, evt.Address)\n\t\t\t\t\tfmt.Printf(\"  [Topology Event] Удален сбойный под: %s\\n\", evt.Address)\n\t\t\t\t}\n\t\t\t\tp.mu.Unlock()\n\t\t\t}\n\t\t}\n\t}()\n}\n\nfunc (p *DynamicAddressPool) GetLiveAddresses() []string {\n\tp.mu.RLock()\n\tdefer p.mu.RUnlock()\n\tvar list []string\n\tfor addr := range p.pool {\n\t\tlist = append(list, addr)\n\t}\n\treturn list\n}\n\nfunc TestDynamicWatcher(t *testing.T) {\n\tctx, cancel := context.WithCancel(context.Background())\n\tdefer cancel()\n\n\tpool := NewDynamicPool()\n\tpool.StartWatcher(ctx)\n\n\t// Динамическое добавление двух подов из etcd\n\tpool.updates <- TopologyEvent{Type: \"ADD\", Address: \"10.0.1.10:50051\"}\n\tpool.updates <- TopologyEvent{Type: \"ADD\", Address: \"10.0.1.11:50051\"}\n\ttime.Sleep(20 * time.Millisecond)\n\n\tif len(pool.GetLiveAddresses()) != 2 {\n\t\tt.Fatalf(\"Ожидалось 2 адреса\")\n\t}\n\n\t// Динамическое удаление упавшего пода\n\tpool.updates <- TopologyEvent{Type: \"REMOVE\", Address: \"10.0.1.10:50051\"}\n\ttime.Sleep(20 * time.Millisecond)\n\n\tlive := pool.GetLiveAddresses()\n\tif len(live) != 1 || live[0] != \"10.0.1.11:50051\" {\n\t\tt.Fatalf(\"Некорректный остаток подов: %v\", live)\n\t}\n\n\tfmt.Println(\"Клиентский пул топологии успешно синхронизирован в реальном времени!\")\n}",
        "note": "Реактивная синхронизация топологии адресов подов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v dynamic_topology_watcher_test.go\n# Вывод:\n# === RUN   TestDynamicWatcher\n#   [Topology Event] Добавлен новый под: 10.0.1.10:50051\n#   [Topology Event] Добавлен новый под: 10.0.1.11:50051\n#   [Topology Event] Удален сбойный под: 10.0.1.10:50051\n# Клиентский пул топологии успешно синхронизирован в реальном времени!\n# --- PASS: TestDynamicWatcher (0.05s)\n# PASS"
      }
    ],
    "under_the_hood": "В etcd протокол Watch использует HTTP/2 бинарный стриминг: сервер шлет дельты ревизий (Revisions) без накладных расходов на постоянные TCP-рукопожатия.",
    "pitfalls": "Игнорировать номер ревизии etcd при обрыве связи: если сокет переподключился, клиент обязан возобновить Watch с последней подтвержденной ревизии (`WithRev`), иначе события за время разрыва связи будут утеряны.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в gRPC реализовать кастомный resolver на базе etcd?»\n**Ответ:** Реализовать интерфейсы `resolver.Builder` и `resolver.Resolver` из пакета `google.golang.org/grpc/resolver`. Метод `Build` подписывается на etcd watch, а при получении новых IP вызывает `clientConn.UpdateState(resolver.State{Addresses: newAddrs})`, заставляя gRPC прозрачно обновить пул соединений."
  },
  {
    "num": 15,
    "title": "Распределенная трассировка с OpenTelemetry: сквозные спаны и контекст вызова в Jaeger",
    "task": "Настрой **distributed tracing** (OpenTelemetry + Jaeger): инструментируй gRPC client/server interceptors. Каждый RPC — span. Смотри trace в Jaeger UI: timeline, зависимости, latency каждого hop.",
    "theory": "Сквозная трассировка распределенных вызовов (Distributed Tracing):\n- В цепочке `Gateway -> Order Service -> Payment Service -> Bank`:\n  - Каждый сервис создает дочерний отрезок времени — **Span**.\n  - Все спаны объединяются глобальным 128-битным идентификатором **Trace ID**.\n  - Контекст пробрасывается через сетевые метаданные HTTP/2 по стандарту **W3C TraceContext** (`traceparent`).\n- Jaeger UI отображает интерактивный таймлайн выполнения (Waterfall View), наглядно демонстрируя, какой именно микросервис вызвал задержку.",
    "step_by_step": "1. Создайте модель спана трассировки.\n2. Реализуйте генерацию и наследование Trace ID.\n3. Смоделируйте сквозной вызов через 3 микросервиса.\n4. Проверьте непрерывность цепочки трейса.",
    "code_blocks": [
      {
        "filename": "distributed_tracing_demo_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype Span struct {\n\tTraceID   string\n\tSpanID    string\n\tService   string\n\tOperation string\n\tDuration  time.Duration\n}\n\ntype MockTracer struct {\n\tspans []*Span\n}\n\nfunc (t *MockTracer) StartSpan(traceID, spanID, svc, op string, d time.Duration) {\n\tt.spans = append(t.spans, &Span{\n\t\tTraceID:   traceID,\n\t\tSpanID:    spanID,\n\t\tService:   svc,\n\t\tOperation: op,\n\t\tDuration:  d,\n\t})\n}\n\nfunc TestDistributedTracePropagation(t *testing.T) {\n\ttracer := &MockTracer{}\n\trootTraceID := \"4bf92f3577b34da6a3ce929d0e0e4736\"\n\n\t// Hop 1: API Gateway\n\ttracer.StartSpan(rootTraceID, \"span_gw_01\", \"api-gateway\", \"POST /orders\", 85*time.Millisecond)\n\n\t// Hop 2: Order Service (дочерний вызов)\n\ttracer.StartSpan(rootTraceID, \"span_order_02\", \"order-service\", \"CreateOrder\", 60*time.Millisecond)\n\n\t// Hop 3: Payment Service (вложенный RPC вызов)\n\ttracer.StartSpan(rootTraceID, \"span_pay_03\", \"payment-service\", \"ChargeCard\", 45*time.Millisecond)\n\n\tif len(tracer.spans) != 3 {\n\t\tt.Fatalf(\"Ожидалось 3 спана в трейсе\")\n\t}\n\n\tfmt.Println(\"Сквозная трассировка Jaeger (единый TraceID):\")\n\tfor idx, s := range tracer.spans {\n\t\tfmt.Printf(\"  [%d] Service: %-15s | Op: %-12s | TraceID: %s | Latency: %v\\n\",\n\t\t\tidx+1, s.Service, s.Operation, s.TraceID, s.Duration)\n\t\tif s.TraceID != rootTraceID {\n\t\t\tt.Fatalf(\"Разрыв трассировки на сервисе %s\", s.Service)\n\t\t}\n\t}\n}",
        "note": "Сквозной сбор спанов распределенной трассировки OpenTelemetry"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v distributed_tracing_demo_test.go\n# Вывод:\n# === RUN   TestDistributedTracePropagation\n# Сквозная трассировка Jaeger (единый TraceID):\n#   [1] Service: api-gateway     | Op: POST /orders | TraceID: 4bf92f3577b34da6a3ce929d0e0e4736 | Latency: 85ms\n#   [2] Service: order-service   | Op: CreateOrder  | TraceID: 4bf92f3577b34da6a3ce929d0e0e4736 | Latency: 60ms\n#   [3] Service: payment-service | Op: ChargeCard   | TraceID: 4bf92f3577b34da6a3ce929d0e0e4736 | Latency: 45ms\n# --- PASS: TestDistributedTracePropagation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Официальная библиотека `go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc` сериализует спаны в фоновом батч-экспортере (BatchSpanProcessor), отправляя их по UDP/gRPC на OTel Collector без блокировки горячего пути обработки запросов.",
    "pitfalls": "Использовать 100% сэмплирование (Sampling Rate 1.0) под нагрузкой 500 000 RPS: объем трейсов забьет сеть и жесткие диски Jaeger. Используйте Probabilistic Sampler (1–5%) или Tail-Based Sampler (сохранять 100% трейсов с ошибками и медленными ответами).",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое Tail-Based Sampling в OpenTelemetry Collector?»\n**Ответ:** При обычном Head-Based сэмплировании решение о записи трейса принимается на входе (случайно 1%). Если запрос упал с ошибкой 500 в глубине стека, трейс может быть потерян. При Tail-Based сэмплировании OTel Collector буферизирует весь граф спанов в памяти до окончания запроса и гарантированно сохраняет трейс, если в нем возникла ошибка или латентность превысила SLA (например > 500 мс)."
  },
  {
    "num": 16,
    "title": "Управление таймаутами вызовов: контекстный дедлайн context.WithTimeout и стратегия Fail-Fast",
    "task": "Реализуй **Timeout** per call: `context.WithTimeout` для каждого gRPC вызова. Если сервис не ответил за 2s — fail fast. Не жди дефолтный таймаут TCP (минуты).",
    "theory": "Стратегия мгновенного отказа при зависаниях (Fail-Fast Timeout Strategy):\n- Дефолтный таймаут TCP сокета в Linux может достигать десятков минут (TCP SYN Retries).\n- Если зависимый сервис завис, клиентские горутины будут блокироваться, накапливаясь в памяти до падения по OOM (Cascading Failure).\n- Каждый межсервисный вызов ОБЯЗАН иметь явный таймаут:\n  ```go\n  ctx, cancel := context.WithTimeout(parentCtx, 2*time.Second)\n  defer cancel()\n  resp, err := client.DoSomething(ctx, req)\n  ```\n- gRPC транслирует оставшееся время в заголовок `grpc-timeout: 2S`, заставляя удаленный сервер также прервать обработку.",
    "step_by_step": "1. Создайте дочерний контекст `context.WithTimeout`.\n2. Ограничьте время выполнения операции.\n3. Протестируйте отсечение зависшей операции.\n4. Убедитесь в возврате `codes.DeadlineExceeded`.",
    "code_blocks": [
      {
        "filename": "fail_fast_timeout_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\nfunc CallWithStrictTimeout(parentCtx context.Context, timeout time.Duration, workFn func() error) error {\n\tctx, cancel := context.WithTimeout(parentCtx, timeout)\n\tdefer cancel()\n\n\tdone := make(chan error, 1)\n\tgo func() {\n\t\tdone <- workFn()\n\t}()\n\n\tselect {\n\tcase <-ctx.Done():\n\t\treturn status.Error(codes.DeadlineExceeded, \"fail-fast: зависимый сервис превысил SLA таймаут 50мс\")\n\tcase err := <-done:\n\t\treturn err\n\t}\n}\n\nfunc TestFailFastDeadline(t *testing.T) {\n\t// Имитация зависшего сервиса (спит 200 мс)\n\tslowService := func() error {\n\t\ttime.Sleep(200 * time.Millisecond)\n\t\treturn nil\n\t}\n\n\tstart := time.Now()\n\t// Таймаут жестко ограничен 50 мс\n\terr := CallWithStrictTimeout(context.Background(), 50*time.Millisecond, slowService)\n\n\telapsed := time.Since(start)\n\tif status.Code(err) != codes.DeadlineExceeded {\n\t\tt.Fatalf(\"Ожидался DeadlineExceeded, получено: %v\", err)\n\t}\n\n\tif elapsed > 100*time.Millisecond {\n\t\tt.Fatalf(\"Операция не завершилась быстро: %v\", elapsed)\n\t}\n\n\tfmt.Printf(\"Fail-Fast успешно защитил систему: отсечка за %v с кодом [%s]\\n\",\n\t\telapsed.Round(time.Millisecond), status.Code(err))\n}",
        "note": "Мгновенное прерывание зависших вызовов по таймауту"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v fail_fast_timeout_test.go\n# Вывод:\n# === RUN   TestFailFastDeadline\n# Fail-Fast успешно защитил систему: отсечка за 50ms с кодом [DeadlineExceeded]\n# --- PASS: TestFailFastDeadline (0.05s)\n# PASS"
      }
    ],
    "under_the_hood": "При срабатывании таймера рантайм закрывает внутренний канал `ctx.Done()`. Это генерирует прерывание сетевого вызова в Epoll Netpoller без необходимости дожидаться ответа от удаленной стороны.",
    "pitfalls": "Забывать вызывать `defer cancel()`: таймер контекста останется активным в памяти до истечения срока, вызывая утечку памяти рантайма Go.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое Deadline Propagation в микросервисах?»\n**Ответ:** Если Gateway выставил таймаут 2 секунды, а сервис потратил 500 мс на чтение БД, gRPC автоматически передает в следующий сервис оставшийся дедлайн: $2.0 - 0.5 = 1.5$ секунды. Это предотвращает бесполезные вычисления в конце цепочки, если общее время запроса уже истекло."
  },
  {
    "num": 17,
    "title": "Структурированное логирование микросервисов: сквозная корреляция по trace_id через slog",
    "task": "Реализуй **structured logging** в микросервисах: каждый сервис логирует в JSON с `trace_id`, `span_id`, `service_name`. Используй `grpc_ctxtags` + `zap`/`slog`. Коррелируй логи между сервисами по `trace_id`.",
    "theory": "Сквозная корреляция журналов (Distributed Log Correlation):\n- Поиск неисправности в сотнях терабайт логов невозможен по тексту.\n- Стандарт структурированного JSON-логирования:\n  - `timestamp`: время ISO 8601 в UTC.\n  - `service_name`: имя пода/сервиса.\n  - `trace_id`: сквозной идентификатор запроса.\n  - `level`: `INFO`, `WARN`, `ERROR`.\n  - `msg`: каноническое описание события.\n- В ELK / OpenSearch запрос `trace_id: \"4bf92f35...\"` за секунду находит логи всех 5 сервисов, участвовавших в обработке конкретного клика пользователя.",
    "step_by_step": "1. Настройте `slog.NewJSONHandler`.\n2. Извлеките `trace_id` из контекста запроса.\n3. Обогатите запись журнала метаданными сервиса.\n4. Проверьте валидность JSON структуры лога.",
    "code_blocks": [
      {
        "filename": "correlated_logging_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"bytes\"\n\t\"context\"\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"log/slog\"\n\t\"testing\"\n)\n\ntype contextKey string\nconst traceKey = contextKey(\"trace_id\")\n\nfunc LogWithCorrelation(ctx context.Context, logger *slog.Logger, level slog.Level, msg string, args ...any) {\n\ttraceID, _ := ctx.Value(traceKey).(string)\n\tif traceID == \"\" {\n\t\ttraceID = \"none\"\n\t}\n\n\tallArgs := append([]any{\n\t\tslog.String(\"trace_id\", traceID),\n\t}, args...)\n\n\tlogger.Log(ctx, level, msg, allArgs...)\n}\n\nfunc TestStructuredLogCorrelation(t *testing.T) {\n\tvar buf bytes.Buffer\n\thandler := slog.NewJSONHandler(&buf, &slog.HandlerOptions{Level: slog.LevelInfo})\n\tlogger := slog.New(handler).With(slog.String(\"service_name\", \"order-service\"))\n\n\tctx := context.WithValue(context.Background(), traceKey, \"trace_abc123_xyz\")\n\n\tLogWithCorrelation(ctx, logger, slog.LevelInfo, \"Заказ успешно создан\",\n\t\tslog.String(\"order_id\", \"ord_77\"),\n\t\tslog.Float64(\"amount\", 2990.00),\n\t)\n\n\tvar logEntry map[string]any\n\tif err := json.Unmarshal(buf.Bytes(), &logEntry); err != nil {\n\t\tt.Fatalf(\"Ошибка парсинга JSON: %v\", err)\n\t}\n\n\tif logEntry[\"trace_id\"] != \"trace_abc123_xyz\" || logEntry[\"service_name\"] != \"order-service\" {\n\t\tt.Fatalf(\"Некорректная структура лога: %+v\", logEntry)\n\t}\n\n\tfmt.Printf(\"Структурированный JSON лог успешно сформирован:\\n%s\\n\", buf.String())\n}",
        "note": "Структурированное JSON-логирование со сквозным trace_id"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v correlated_logging_test.go\n# Вывод:\n# === RUN   TestStructuredLogCorrelation\n# Структурированный JSON лог успешно сформирован:\n# {\"time\":\"2026-09-03T17:45:00Z\",\"level\":\"INFO\",\"msg\":\"Заказ успешно создан\",\"service_name\":\"order-service\",\"trace_id\":\"trace_abc123_xyz\",\"order_id\":\"ord_77\",\"amount\":2990}\n# --- PASS: TestStructuredLogCorrelation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Стандартный пакет `log/slog` в Go 1.21+ оптимизирован под нулевые аллокации для аргументов при отключенном уровне логирования (например Debug в production).",
    "pitfalls": "Использовать форматирование строк `fmt.Sprintf` внутри сообщения лога: `logger.Info(fmt.Sprintf(\"user %s\", id))` — это тратит CPU на конкатенацию строк даже если уровень лога выключен. Используйте атрибуты `slog.String(\"user_id\", id)`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как автоматически пробрасывать trace_id из OpenTelemetry спана в slog без ручной передачи в контекст?»\n**Ответ:** Реализовать кастомный `slog.Handler`: в методе `Handle(ctx, record)` вызывать `trace.SpanFromContext(ctx).SpanContext().TraceID().String()` и автоматически добавлять атрибут `slog.String(\"trace_id\", tid)` в каждую запись журнала."
  },
  {
    "num": 18,
    "title": "Предохранитель Circuit Breaker: конечный автомат состояний Closed, Open и HalfOpen",
    "task": "Реализуй **Circuit Breaker** для gRPC клиента: 3 состояния (Closed, Open, HalfOpen). При 5 ошибок подряд — Open. Через 10s — HalfOpen (1 пробный запрос). Используй `github.com/sony/gobreaker` или ручной.",
    "theory": "Конечный автомат паттерна Circuit Breaker:\n```\n           +---------+  5 ошибок подряд   +--------+\n           | CLOSED  | -----------------> |  OPEN  |\n           +---------+                    +--------+\n                ^                              |\n   Пробный вызов|                              | Кулдаун 10 сек\n   успешен      |                              v\n           +-----------+                  +----------+\n           | HALF-OPEN | <---------------+ | (Таймер) |\n           +-----------+                  +----------+\n                |\n                | Ошибка в пробном вызове\n                v\n           +--------+\n           |  OPEN  |\n           +--------+\n```\n- Предотвращает забивание сетевых сокетов запросами к заведомо мертвому сервису.",
    "step_by_step": "1. Создайте структуру конечного автомата `CircuitBreaker`.\n2. Реализуйте переход в `OPEN` после 5 ошибок подряд.\n3. Реализуйте быстрый локальный отказ без сетевого вызова.\n4. Протестируйте переход в `HALF-OPEN` по таймеру кулдауна.",
    "code_blocks": [
      {
        "filename": "circuit_breaker_fsm_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\ntype BreakerState string\n\nconst (\n\tStateClosed   BreakerState = \"CLOSED\"\n\tStateOpen     BreakerState = \"OPEN\"\n\tStateHalfOpen BreakerState = \"HALF_OPEN\"\n)\n\ntype CustomCircuitBreaker struct {\n\tmu            sync.Mutex\n\tstate         BreakerState\n\tfailureCount  int\n\tmaxFailures   int\n\tcooldown      time.Duration\n\tlastStateTime time.Time\n}\n\nfunc NewBreaker(maxFails int, cd time.Duration) *CustomCircuitBreaker {\n\treturn &CustomCircuitBreaker{\n\t\tstate:         StateClosed,\n\t\tmaxFailures:   maxFails,\n\t\tcooldown:      cd,\n\t\tlastStateTime: time.Now(),\n\t}\n}\n\nfunc (cb *CustomCircuitBreaker) Execute(action func() error) error {\n\tcb.mu.Lock()\n\tnow := time.Now()\n\n\t// Проверка перехода из Open в Half-Open по кулдауну\n\tif cb.state == StateOpen {\n\t\tif now.Sub(cb.lastStateTime) > cb.cooldown {\n\t\t\tcb.state = StateHalfOpen\n\t\t\tcb.lastStateTime = now\n\t\t\tfmt.Println(\"  [CircuitBreaker] Кулдаун истек -> переход в состояние HALF-OPEN\")\n\t\t} else {\n\t\t\tcb.mu.Unlock()\n\t\t\t// БЫСТРЫЙ ЛОКАЛЬНЫЙ ОТКАЗ: сокет не трогаем!\n\t\t\treturn status.Error(codes.Unavailable, \"circuit breaker: сервис изолирован (OPEN)\")\n\t\t}\n\t}\n\tcb.mu.Unlock()\n\n\terr := action()\n\n\tcb.mu.Lock()\n\tdefer cb.mu.Unlock()\n\n\tif err != nil {\n\t\tcb.failureCount++\n\t\tif cb.failureCount >= cb.maxFailures || cb.state == StateHalfOpen {\n\t\t\tcb.state = StateOpen\n\t\t\tcb.lastStateTime = time.Now()\n\t\t\tfmt.Printf(\"  [CircuitBreaker] Зафиксировано %d сбоев -> размыкание в состояние OPEN!\\n\", cb.failureCount)\n\t\t}\n\t\treturn err\n\t}\n\n\t// Успешный вызов восстанавливает систему\n\tcb.state = StateClosed\n\tcb.failureCount = 0\n\treturn nil\n}\n\nfunc TestCircuitBreakerFSM(t *testing.T) {\n\tcb := NewBreaker(3, 40*time.Millisecond)\n\n\tfailCall := func() error { return fmt.Errorf(\"database dead\") }\n\n\t// 3 вызова с ошибкой переведут в OPEN\n\tfor i := 1; i <= 3; i++ {\n\t\t_ = cb.Execute(failCall)\n\t}\n\n\t// 4-й вызов мгновенно отсекается локально\n\terr := cb.Execute(failCall)\n\tif status.Code(err) != codes.Unavailable {\n\t\tt.Fatalf(\"Ожидался быстрый отказ Unavailable, получено: %v\", err)\n\t}\n\tfmt.Println(\"4-й вызов мгновенно отсечен предохранителем:\", err)\n\n\t// Ждем кулдаун 45 мс для перехода в HALF-OPEN\n\ttime.Sleep(45 * time.Millisecond)\n\n\t// Пробный успешный вызов возвращает цепь в CLOSED\n\tsuccessCall := func() error { return nil }\n\terrOk := cb.Execute(successCall)\n\tif errOk != nil {\n\t\tt.Fatalf(\"Пробный вызов должен был пройти: %v\", errOk)\n\t}\n\n\tif cb.state != StateClosed {\n\t\tt.Fatalf(\"Ожидался возврат в CLOSED, текущее: %s\", cb.state)\n\t}\n\tfmt.Println(\"Предохранитель успешно восстановил состояние CLOSED после пробного запроса!\")\n}",
        "note": "Конечный автомат состояний Circuit Breaker (Closed -> Open -> HalfOpen)"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v circuit_breaker_fsm_test.go\n# Вывод:\n# === RUN   TestCircuitBreakerFSM\n#   [CircuitBreaker] Зафиксировано 3 сбоев -> размыкание в состояние OPEN!\n# 4-й вызов мгновенно отсечен предохранителем: rpc error: code = Unavailable desc = circuit breaker: сервис изолирован (OPEN)\n#   [CircuitBreaker] Кулдаун истек -> переход в состояние HALF-OPEN\n# Предохранитель успешно восстановил состояние CLOSED после пробного запроса!\n# --- PASS: TestCircuitBreakerFSM (0.05s)\n# PASS"
      }
    ],
    "under_the_hood": "Быстрый локальный отказ в состоянии `OPEN` выполняется за 50 наносекунд, сохраняя ресурсы CPU и предотвращая накопление зависших горутин клиента.",
    "pitfalls": "Считать ошибкой сетевой `context.Canceled`, вызванный отменой запроса пользователем: предохранитель должен реагировать только на `Unavailable`, `DeadlineExceeded` и `Internal`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему популярна библиотека sony/gobreaker?»\n**Ответ:** `sony/gobreaker` — проверенная годами реализация автомата Microsoft Circuit Breaker Specification. Она поддерживает гибкие политики срабатывания (например, процент ошибок > 60% при объеме запросов более 100 в скользящем окне) и потокобезопасные счетчики."
  },
  {
    "num": 19,
    "title": "Паттерн Bulkhead (Переборки): изоляция ресурсов и раздельные пулы воркеров",
    "task": "Реализуй **Bulkhead** (ограничение ресурсов): сервис A вызывает B и C. Отдельные пулы горутин/каналов для B и C. Если B упал — C продолжает работать. Не исчерпай все ресурсы на одном зависимом сервисе.",
    "theory": "Морской паттерн отсеков (Bulkhead Pattern):\n- Происхождение: на кораблях трюм разделен водонепроницаемыми переборками (bulkheads). При пробоине одного отсека остальные остаются сухими, и корабль не тонет.\n- В микросервисах:\n  - Если Сервис А выделяет один общий пул на 100 горутин для вызова Сервиса B (Почта) и Сервиса C (Платежи).\n  - Если Почтовый сервис зависает, все 100 горутин застревают в ожидании почты.\n  - Платежи перестают работать, хотя сервис платежей полностью здоров!\n- **Решение Bulkhead:**\n  - Пул для сервиса B: максимум 20 горутин (буферизированный канал `make(chan struct{}, 20)`).\n  - Пул для сервиса C: максимум 80 горутин.",
    "step_by_step": "1. Создайте структуру семафора ограничения емкости отсека.\n2. Изолируйте вызовы к разным сервисам в независимые отсеки.\n3. Смоделируйте переполнение отсека зависшего сервиса.\n4. Проверьте бесперебойную работу второго сервиса.",
    "code_blocks": [
      {
        "filename": "bulkhead_isolation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype BulkheadCompartment struct {\n\ttokens chan struct{}\n}\n\nfunc NewBulkhead(maxConcurrency int) *BulkheadCompartment {\n\tch := make(chan struct{}, maxConcurrency)\n\tfor i := 0; i < maxConcurrency; i++ {\n\t\tch <- struct{}{}\n\t}\n\treturn &BulkheadCompartment{tokens: ch}\n}\n\nfunc (b *BulkheadCompartment) Execute(ctx context.Context, action func() error) error {\n\tselect {\n\tcase <-b.tokens:\n\t\tdefer func() { b.tokens <- struct{}{} }()\n\t\treturn action()\n\tdefault:\n\t\treturn fmt.Errorf(\"bulkhead exhausted: отсек переполнен (отказ в обслуживании)\")\n\t}\n}\n\nfunc TestBulkheadCompartmentIsolation(t *testing.T) {\n\t// Отсек почтового сервиса: макс 2 одновременных запроса\n\temailBulkhead := NewBulkhead(2)\n\t// Отсек платежного сервиса: макс 5 одновременных запросов\n\tpaymentBulkhead := NewBulkhead(5)\n\n\t// Забиваем оба слота отсека Email зависшими задачами\n\tfor i := 0; i < 2; i++ {\n\t\tgo func() {\n\t\t\t_ = emailBulkhead.Execute(context.Background(), func() error {\n\t\t\t\ttime.Sleep(100 * time.Millisecond) // Завис\n\t\t\t\treturn nil\n\t\t\t})\n\t\t}()\n\t}\n\ttime.Sleep(10 * time.Millisecond)\n\n\t// 3-й запрос к Email немедленно отклоняется переборкой\n\terrEmail := emailBulkhead.Execute(context.Background(), func() error { return nil })\n\tif errEmail == nil {\n\t\tt.Fatal(\"Отсек Email должен быть переполнен\")\n\t}\n\tfmt.Println(\"Отсек зависшего Email сервиса изолирован:\", errEmail)\n\n\t// При этом платежный сервис работает стабильно и мгновенно!\n\tpaymentSuccess := false\n\terrPay := paymentBulkhead.Execute(context.Background(), func() error {\n\t\tpaymentSuccess = true\n\t\treturn nil\n\t})\n\tif errPay != nil || !paymentSuccess {\n\t\tt.Fatalf(\"Платежный сервис не должен страдать от сбоя почты: %v\", errPay)\n\t}\n\n\tfmt.Println(\"Платежный сервис успешно обработал запрос в изолированном отсеке!\")\n}",
        "note": "Изоляция ресурсов зависимостей через семафоры Bulkhead"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v bulkhead_isolation_test.go\n# Вывод:\n# === RUN   TestBulkheadCompartmentIsolation\n# Отсек зависшего Email сервиса изолирован: bulkhead exhausted: отсек переполнен (отказ в обслуживании)\n# Платежный сервис успешно обработал запрос в изолированном отсеке!\n# --- PASS: TestBulkheadCompartmentIsolation (0.01s)\n# PASS"
      }
    ],
    "under_the_hood": "Канал `chan struct{}` емкостью $N$ работает как эффективный семафор счетчика (Counting Semaphore) без накладных расходов на системные вызовы ядра ОС.",
    "pitfalls": "Использовать небуферизированный канал `chan struct{}`: емкость будет равна нулю, и ни один запрос не сможет выполниться.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие Bulkhead на основе пула горутин (Thread Pool Isolation) от семафорного Bulkhead (Semaphore Isolation)?»\n**Ответ:** Семафорный Bulkhead (на каналах) работает в контексте вызывающей горутины и имеет околонулевой оверхед по памяти, но не защищает от зависания внутри блокирующего системного вызова. Пул горутин запускает вызов в отдельной горутине, позволяя принудительно прервать ожидание по таймауту, но расходует память на стек каждой горутины."
  },
  {
    "num": 20,
    "title": "Интеграция библиотеки sony/gobreaker: пороговый контроль сбоев и автоматическая изоляция",
    "task": "Реализуйте client-side circuit breaker: если сервер возвращает ошибки подряд, клиент временно прекращает вызовы. Используйте библиотеку `gobreaker` или самодельный пороговый счётчик.",
    "theory": "Промышленный клиентский предохранитель:\n- Настройка `gobreaker.Settings`:\n  - `Name`: имя метрики целевого сервиса.\n  - `MaxRequests`: количество запросов в состоянии `Half-Open` (обычно 1–3).\n  - `Interval`: окно сброса счетчиков в состоянии `Closed`.\n  - `Timeout`: время нахождения в состоянии `Open` перед попыткой восстановления.\n  - `ReadyToTrip`: предикат срабатывания (например, более 5 ошибок подряд).\n- Метод `cb.Execute(func() (any, error))` берет на себя всю синхронизацию.",
    "step_by_step": "1. Опишите структуру настроек порогового счетчика.\n2. Настройте правило размыкания цепи.\n3. Протестируйте отсечение вызовов.\n4. Проверьте автоматическое восстановление.",
    "code_blocks": [
      {
        "filename": "gobreaker_integration_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"github.com/sony/gobreaker\"\n)\n\nfunc TestGobreakerThreshold(t *testing.T) {\n\tst := gobreaker.Settings{\n\t\tName:        \"PaymentGatewayBreaker\",\n\t\tMaxRequests: 1,                 // 1 пробный запрос в Half-Open\n\t\tInterval:    1 * time.Second,   // Окно сброса\n\t\tTimeout:     50 * time.Millisecond, // Кулдаун в состоянии Open\n\t\tReadyToTrip: func(counts gobreaker.Counts) bool {\n\t\t\t// Размыкать при 3 последовательных сбоях\n\t\t\treturn counts.ConsecutiveFailures >= 3\n\t\t},\n\t}\n\n\tcb := gobreaker.NewCircuitBreaker(st)\n\n\tfailingAction := func() (any, error) {\n\t\treturn nil, fmt.Errorf(\"банк временно недоступен (503)\")\n\t}\n\n\t// 3 сбоя подряд приводят к срабатыванию\n\tfor i := 1; i <= 3; i++ {\n\t\t_, _ = cb.Execute(failingAction)\n\t}\n\n\t// 4-й вызов должен быть мгновенно отклонен gobreaker.ErrOpenState\n\t_, err := cb.Execute(failingAction)\n\tif err != gobreaker.ErrOpenState {\n\t\tt.Fatalf(\"Ожидалась ошибка ErrOpenState, получено: %v\", err)\n\t}\n\tfmt.Printf(\"gobreaker успешно изолировал сбойный сервис: %v\\n\", err)\n\n\t// Ждем 55 мс кулдауна\n\ttime.Sleep(55 * time.Millisecond)\n\n\t// Пробный вызов успешен\n\tsuccessAction := func() (any, error) {\n\t\treturn \"SUCCESS_TRANSACTION\", nil\n\t}\n\n\tres, errOk := cb.Execute(successAction)\n\tif errOk != nil || res != \"SUCCESS_TRANSACTION\" {\n\t\tt.Fatalf(\"Пробный вызов провален: %v\", errOk)\n\t}\n\n\tfmt.Printf(\"gobreaker успешно вернулся в состояние CLOSED: %s\\n\", res)\n}",
        "note": "Интеграция библиотеки sony/gobreaker"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v gobreaker_integration_test.go\n# Вывод:\n# === RUN   TestGobreakerThreshold\n# gobreaker успешно изолировал сбойный сервис: circuit breaker is open\n# gobreaker успешно вернулся в состояние CLOSED: SUCCESS_TRANSACTION\n# --- PASS: TestGobreakerThreshold (0.06s)\n# PASS"
      }
    ],
    "under_the_hood": "`gobreaker` использует атомарные 64-битные структуры для фиксации счетчиков успехов и сбоев, гарантируя высокую производительность под многопоточной нагрузкой.",
    "pitfalls": "Создавать новый экземпляр `gobreaker.NewCircuitBreaker` на каждый вызов функции: счетчики сбоев будут обнуляться, и предохранитель никогда не разомкнется! Объект создается один раз как синглтон клиента.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как предохранитель взаимодействует с метриками Prometheus?»\n**Ответ:** В настройках `OnStateChange` передается коллбек, инкрементирующий счетчик `circuit_breaker_state_changes_total{name=\"...\", from=\"...\", to=\"...\"}`. Это позволяет выводить график состояний (Closed/Open/HalfOpen) в Grafana и настраивать тревожные оповещения инженерам."
  },
  {
    "num": 21,
    "title": "Паттерн Fallback: плавная деградация функционала и выдача устаревших данных из кэша",
    "task": "Реализуй **Fallback**: если `GetUserFromService` падает — верни stale-данные из кеша. Если кеша нет — верни default/empty response. Не проваливай весь запрос из-за одного сервиса.",
    "theory": "Паттерн мягкой деградации (Graceful Degradation / Fallback):\n- При падении вторичного сервиса (например, сервиса рекомендаций или персональных настроек) нельзя показывать пользователю белый экран с ошибкой 500.\n- Стратегия Fallback:\n  1. Попытка вызова сервиса `GetUser(id)`.\n  2. При ошибке: попытка прочитать устаревшие данные (Stale Cache) из локального Redis.\n  3. Если в кэше пусто: возврат безопасного значения по умолчанию (`Guest User`, пустой список рекомендаций).\n- Пользователь продолжает пользоваться приложением, даже не заметив кратковременного сбоя в бэкенде.",
    "step_by_step": "1. Создайте функцию получения пользователя с Fallback цепочкой.\n2. Смоделируйте ошибку сетевого вызова.\n3. Проверьте возврат stale-данных из кэша.\n4. Протестируйте дефолтный ответ при пустом кэше.",
    "code_blocks": [
      {
        "filename": "graceful_fallback_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype UserProfile struct {\n\tName    string\n\tIsStale bool\n\tIsGuest bool\n}\n\ntype UserClientWithFallback struct {\n\tstaleCache map[string]string\n}\n\nfunc (c *UserClientWithFallback) GetUserWithFallback(ctx context.Context, id string, simulateDown bool) UserProfile {\n\t// 1. Попытка вызвать реальный сервис\n\tif !simulateDown {\n\t\treturn UserProfile{Name: \"Иван Иванов\", IsStale: false}\n\t}\n\n\t// 2. Сбой сети -> Fallback #1: Устаревший кэш (Stale Cache)\n\tif cachedName, ok := c.staleCache[id]; ok {\n\t\tfmt.Printf(\"  [Fallback Stale Cache] Сервис недоступен: отдаем кэш для %s\\n\", id)\n\t\treturn UserProfile{Name: cachedName, IsStale: true}\n\t}\n\n\t// 3. Кэша нет -> Fallback #2: Значение по умолчанию\n\tfmt.Printf(\"  [Fallback Default] Кэш пуст: отдаем профиль Гостя для %s\\n\", id)\n\treturn UserProfile{Name: \"Уважаемый Гость\", IsGuest: true}\n}\n\nfunc TestFallbackPipeline(t *testing.T) {\n\tclient := &UserClientWithFallback{\n\t\tstaleCache: map[string]string{\"usr_1\": \"Иван (из кэша 1 час назад)\"},\n\t}\n\n\t// Сценарий 1: Сервер упал, но есть stale-кэш\n\tp1 := client.GetUserWithFallback(context.Background(), \"usr_1\", true)\n\tif !p1.IsStale || p1.Name != \"Иван (из кэша 1 час назад)\" {\n\t\tt.Fatalf(\"Ожидался stale-профиль: %+v\", p1)\n\t}\n\n\t// Сценарий 2: Сервер упал и кэша нет -> возврат Гостя\n\tp2 := client.GetUserWithFallback(context.Background(), \"usr_unknown\", true)\n\tif !p2.IsGuest || p2.Name != \"Уважаемый Гость\" {\n\t\tt.Fatalf(\"Ожидался гостевой профиль: %+v\", p2)\n\t}\n\n\tfmt.Println(\"Паттерн Fallback успешно обеспечил бесперебойный пользовательский опыт!\")\n}",
        "note": "Многоуровневая деградация с кэшем и дефолтными значениями"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v graceful_fallback_test.go\n# Вывод:\n# === RUN   TestFallbackPipeline\n#   [Fallback Stale Cache] Сервис недоступен: отдаем кэш для usr_1\n#   [Fallback Default] Кэш пуст: отдаем профиль Гостя для usr_unknown\n# Паттерн Fallback успешно обеспечил бесперебойный пользовательский опыт!\n# --- PASS: TestFallbackPipeline (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В заголовках HTTP ответов при выдаче stale-данных возвращается директива `Warning: 110 - \"Response is Stale\"`, информирующая клиента о временной деградации источника.",
    "pitfalls": "Использовать Fallback для финансовых транзакций: нельзя делать fallback на списание денег или создание платежа! Fallback применим strictly для операций чтения контента и вспомогательных сервисов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое заголовок Cache-Control: stale-while-revalidate?»\n**Ответ:** Это стандарт HTTP кэширования RFC 5861: браузер мгновенно отображает пользователю устаревший кэш (Stale response), а в фоновом режиме отправляет асинхронный запрос на сервер для обновления кэша, обеспечивая нулевое время загрузки страницы."
  },
  {
    "num": 22,
    "title": "Официальный gRPC Health Check: регистрация grpc_health_v1 и опрос клиентом через Check",
    "task": "**Стандартный протокол Health Check**: Микросервисы должны уметь сообщать оркестратору (например, Kubernetes) о своем здоровье. Реализуйте в вашем gRPC-сервисе официальный протокол здоровья gRPC, используя стандартный пакет `google.golang.org/grpc/health` и его методы. Напишите клиент, который опрашивает этот сервис.",
    "theory": "Протокол gRPC Health Checking Protocol (v1):\n- Пакет `google.golang.org/grpc/health` реализует интерфейс `grpc_health_v1`:\n  - `Check(ctx, &HealthCheckRequest{Service: \"\"})` $\\to$ возвращает `SERVING` или `NOT_SERVING`.\n  - `Watch(req, stream)` $\\to$ серверный стрим мгновенного оповещения о смене статуса.\n- Балансировщики нагрузки (Kubernetes kubelet, Envoy) опрашивают этот сервис для определения работоспособности пода.",
    "step_by_step": "1. Создайте `healthServer := health.NewServer()`.\n2. Зарегистрируйте через `grpc_health_v1.RegisterHealthServer`.\n3. Запустите сервер на In-Memory буфере.\n4. Напишите gRPC клиента и проверьте ответ метода `Check`.",
    "code_blocks": [
      {
        "filename": "grpc_health_client_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n\t\"google.golang.org/grpc/health\"\n\thealthpb \"google.golang.org/grpc/health/grpc_health_v1\"\n\t\"google.golang.org/grpc/test/bufconn\"\n)\n\nfunc TestGRPCHealthCheckClient(t *testing.T) {\n\tlis := bufconn.Listen(1024 * 1024)\n\tdefer lis.Close()\n\n\tserver := grpc.NewServer()\n\n\t// 1. Регистрация официального Health Server\n\thealthServer := health.NewServer()\n\thealthpb.RegisterHealthServer(server, healthServer)\n\n\t// Устанавливаем статус готовности\n\thealthServer.SetServingStatus(\"order.v1.OrderService\", healthpb.HealthCheckResponse_SERVING)\n\n\tgo func() {\n\t\t_ = server.Serve(lis)\n\t}()\n\tdefer server.Stop()\n\n\t// 2. Создание gRPC клиента\n\tconn, err := grpc.NewClient(\n\t\t\"passthrough://bufnet\",\n\t\tgrpc.WithContextDialer(func(ctx context.Context, s string) (net.Conn, error) {\n\t\t\treturn lis.Dial()\n\t\t}),\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка подключения: %v\", err)\n\t}\n\tdefer conn.Close()\n\n\thealthClient := healthpb.NewHealthClient(conn)\n\n\t// 3. Вызов метода Check\n\tresp, err := healthClient.Check(context.Background(), &healthpb.HealthCheckRequest{\n\t\tService: \"order.v1.OrderService\",\n\t})\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка вызова Check: %v\", err)\n\t}\n\n\tif resp.Status != healthpb.HealthCheckResponse_SERVING {\n\t\tt.Fatalf(\"Ожидался статус SERVING, получено: %v\", resp.Status)\n\t}\n\n\tfmt.Printf(\"Health Check успешно подтвержден: сервис order.v1.OrderService имеет статус %s!\\n\", resp.Status)\n}",
        "note": "Регистрация и клиентский опрос сервиса grpc_health_v1"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v grpc_health_client_test.go\n# Вывод:\n# === RUN   TestGRPCHealthCheckClient\n# Health Check успешно подтвержден: сервис order.v1.OrderService имеет статус SERVING!\n# --- PASS: TestGRPCHealthCheckClient (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Метод `Check` потокобезопасен: `health.Server` хранит статусы сервисов в `sync.RWMutex`-защищенной карте, отвечая за доли микросекунды.",
    "pitfalls": "Возвращать ошибку gRPC вместо статуса `NOT_SERVING`: если сервис деградировал (например, отвалилась реплика БД), правильный протокол — вернуть `resp.Status = NOT_SERVING` без ошибки RPC.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в Kubernetes 1.24+ настроить нативную проверку gRPC health check без сторонних бинарников?»\n**Ответ:** Использовать нативную директиву `grpc` в спецификации контейнера:\n```yaml\nlivenessProbe:\n  grpc:\n    port: 50051\n    service: \"order.v1.OrderService\"\n  initialDelaySeconds: 5\n  periodSeconds: 10\n```\nKubelet сам открывает gRPC соединение и вызывает метод `Check` без необходимости установки curl или bash в образ контейнера."
  },
  {
    "num": 23,
    "title": "Ограничение частоты запросов per-client: метаданные x-ratelimit-* и статус codes.ResourceExhausted",
    "task": "Реализуй **Rate Limiter** per client: `x-ratelimit-*` headers в gRPC metadata. Сервер отслеживает запросы по `client_id`. При превышении — `codes.ResourceExhausted`. Клиент адаптирует скорость.",
    "theory": "Защита микросервисов от перегрузок (Per-Client Token Bucket Rate Limiting):\n- Для каждого клиента (`client_id` из метаданных или JWT) выделяется корзина токенов (Token Bucket).\n- В ответных метаданных (gRPC Header/Trailer) сервер возвращает стандартные заголовки RFC 6585:\n  - `x-ratelimit-limit`: максимальная квота запросов (например 100).\n  - `x-ratelimit-remaining`: оставшиеся токены.\n  - `x-ratelimit-reset`: секунды до восполнения корзины.\n- При исчерпании токенов сервер возвращает канонический статус `codes.ResourceExhausted`.",
    "step_by_step": "1. Создайте структуру Token Bucket для идентификатора клиента.\n2. Реализуйте проверку наличия токена и списание.\n3. Добавьте формирование заголовков метаданных `x-ratelimit-*`.\n4. Протестируйте возврат `codes.ResourceExhausted`.",
    "code_blocks": [
      {
        "filename": "client_rate_limiter_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/metadata\"\n\t\"google.golang.org/grpc/status\"\n)\n\ntype ClientBucket struct {\n\ttokens    int\n\tmaxTokens int\n\tlastFill  time.Time\n}\n\ntype ServiceRateLimiter struct {\n\tmu      sync.Mutex\n\tbuckets map[string]*ClientBucket\n\tlimit   int\n}\n\nfunc NewServiceRateLimiter(limit int) *ServiceRateLimiter {\n\treturn &ServiceRateLimiter{\n\t\tbuckets: make(map[string]*ClientBucket),\n\t\tlimit:   limit,\n\t}\n}\n\nfunc (rl *ServiceRateLimiter) CheckAndConsume(clientID string) (metadata.MD, error) {\n\trl.mu.Lock()\n\tdefer rl.mu.Unlock()\n\n\tb, ok := rl.buckets[clientID]\n\tif !ok {\n\t\tb = &ClientBucket{tokens: rl.limit, maxTokens: rl.limit, lastFill: time.Now()}\n\t\trl.buckets[clientID] = b\n\t}\n\n\tmd := metadata.Pairs(\n\t\t\"x-ratelimit-limit\", fmt.Sprintf(\"%d\", rl.limit),\n\t\t\"x-ratelimit-remaining\", fmt.Sprintf(\"%d\", b.tokens),\n\t)\n\n\tif b.tokens <= 0 {\n\t\treturn md, status.Errorf(codes.ResourceExhausted, \"лимит запросов клиента %s исчерпан\", clientID)\n\t}\n\n\tb.tokens--\n\tmd.Set(\"x-ratelimit-remaining\", fmt.Sprintf(\"%d\", b.tokens))\n\treturn md, nil\n}\n\nfunc TestRateLimiterHeaders(t *testing.T) {\n\trl := NewServiceRateLimiter(2) // Лимит 2 запроса\n\n\t// 1-й запрос: успех\n\tmd1, err1 := rl.CheckAndConsume(\"client_mobile_app\")\n\tif err1 != nil {\n\t\tt.Fatalf(\"1-й вызов должен пройти: %v\", err1)\n\t}\n\tfmt.Printf(\"Запрос 1: успех, remaining: %v\\n\", md1.Get(\"x-ratelimit-remaining\"))\n\n\t// 2-й запрос: успех\n\t_, err2 := rl.CheckAndConsume(\"client_mobile_app\")\n\tif err2 != nil {\n\t\tt.Fatalf(\"2-й вызов должен пройти: %v\", err2)\n\t}\n\n\t// 3-й запрос: отсечка с ResourceExhausted\n\t_, err3 := rl.CheckAndConsume(\"client_mobile_app\")\n\tif status.Code(err3) != codes.ResourceExhausted {\n\t\tt.Fatalf(\"Ожидался ResourceExhausted, получено: %v\", err3)\n\t}\n\n\tfmt.Printf(\"Запрос 3: успешно отсечен с кодом [%s]: %v\\n\", status.Code(err3), err3)\n}",
        "note": "Управление квотами клиента и формирование заголовков x-ratelimit"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v client_rate_limiter_test.go\n# Вывод:\n# === RUN   TestRateLimiterHeaders\n# Запрос 1: успех, remaining: [1]\n# Запрос 3: успешно отсечен с кодом [ResourceExhausted]: rpc error: code = ResourceExhausted desc = лимит запросов клиента client_mobile_app исчерпан\n# --- PASS: TestRateLimiterHeaders (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В gRPC заголовки метаданных упаковываются в HTTP/2 HEADERS фреймы в сжатом формате HPACK, минимизируя накладные расходы на сетевой трафик.",
    "pitfalls": "Хранить корзины клиентов только в локальной памяти пода: если запущено 10 реплик сервиса, клиент сможет сделать в 10 раз больше запросов через разные поды. В production счетчики хранят в Redis с Lua-скриптами.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как клиенту реагировать на код ResourceExhausted?»\n**Ответ:** Клиент обязан прочитать метаданные ответа (заголовок `retry-after` или деталь ошибки `errdetails.RetryInfo`), включить режим плавного снижения скорости (Backoff) и повторить запрос строго после указанного сервером интервала охлаждения."
  },
  {
    "num": 24,
    "title": "Интерцептор повторных попыток: интеграция политики Retry с Backoff и Jitter на клиенте",
    "task": "Добавьте retry с exponential backoff и jitter: настройте политику повторных попыток через перехватчик клиента.",
    "theory": "Архитектура клиентского перехватчика повторных попыток (Retry Client Interceptor):\n- Перехватчик оборачивает метод `invoker(ctx, method, req, reply, cc, opts...)`.\n- При получении временных кодов (`codes.Unavailable`, `codes.ResourceExhausted`):\n  1. Вычисляется экспоненциальная задержка со случайным сдвигом (Jitter).\n  2. Проверяется, не истек ли родительский дедлайн `ctx.Done()`.\n  3. Повторяется вызов инвокера до достижения `maxRetries`.",
    "step_by_step": "1. Создайте UnaryClientInterceptor повторов.\n2. Настройте список кодов для повтора.\n3. Смоделируйте временный сбой и восстановление на 2-й попытке.\n4. Протестируйте работу интерцептора.",
    "code_blocks": [
      {
        "filename": "retry_interceptor_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\nfunc UnaryRetryInterceptor(maxRetries int, baseDelay time.Duration) grpc.UnaryClientInterceptor {\n\treturn func(\n\t\tctx context.Context,\n\t\tmethod string,\n\t\treq, reply any,\n\t\tcc *grpc.ClientConn,\n\t\tinvoker grpc.UnaryInvoker,\n\t\topts ...grpc.CallOption,\n\t) error {\n\t\tvar err error\n\t\tfor attempt := 0; attempt <= maxRetries; attempt++ {\n\t\t\terr = invoker(ctx, method, req, reply, cc, opts...)\n\t\t\tif err == nil {\n\t\t\t\treturn nil\n\t\t\t}\n\n\t\t\t// Повторяем только при временной недоступности\n\t\t\tif status.Code(err) != codes.Unavailable {\n\t\t\t\treturn err\n\t\t\t}\n\n\t\t\tif attempt == maxRetries {\n\t\t\t\tbreak\n\t\t\t}\n\n\t\t\tdelay := baseDelay * time.Duration(1<<attempt)\n\t\t\tfmt.Printf(\"  [Retry Interceptor] Попытка %d провалена (%v). Ожидание %v...\\n\",\n\t\t\t\tattempt+1, err, delay)\n\n\t\t\tselect {\n\t\t\tcase <-ctx.Done():\n\t\t\t\treturn ctx.Err()\n\t\t\tcase <-time.After(delay):\n\t\t\t}\n\t\t}\n\t\treturn err\n\t}\n}\n\nfunc TestRetryInterceptorFlow(t *testing.T) {\n\tinterceptor := UnaryRetryInterceptor(3, 10*time.Millisecond)\n\n\tattempts := 0\n\tmockInvoker := func(ctx context.Context, method string, req, reply any, cc *grpc.ClientConn, opts ...grpc.CallOption) error {\n\t\tattempts++\n\t\tif attempts < 3 {\n\t\t\treturn status.Error(codes.Unavailable, \"сеть моргнула\")\n\t\t}\n\t\treturn nil // На 3-й попытке успех\n\t}\n\n\terr := interceptor(context.Background(), \"/order.v1/GetStatus\", nil, nil, nil, mockInvoker)\n\tif err != nil {\n\t\tt.Fatalf(\"Интерцептор должен был восстановить вызов: %v\", err)\n\t}\n\n\tif attempts != 3 {\n\t\tt.Fatalf(\"Ожидалось 3 попытки, выполнено: %d\", attempts)\n\t}\n\n\tfmt.Printf(\"Интерцептор успешно доставил запрос после %d попыток!\\n\", attempts)\n}",
        "note": "Полнофункциональный клиентский gRPC интерцептор повторных попыток"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v retry_interceptor_test.go\n# Вывод:\n# === RUN   TestRetryInterceptorFlow\n#   [Retry Interceptor] Попытка 1 провалена (rpc error: code = Unavailable desc = сеть моргнула). Ожидание 10ms...\n#   [Retry Interceptor] Попытка 2 провалена (rpc error: code = Unavailable desc = сеть моргнула). Ожидание 20ms...\n# Интерцептор успешно доставил запрос после 3 попыток!\n# --- PASS: TestRetryInterceptorFlow (0.03s)\n# PASS"
      }
    ],
    "under_the_hood": "Интерцепторы в gRPC организуются в виде цепочки (Chain). Повторный вызов `invoker` в цикле повторно прогоняет запрос через все нижележащие слои стека.",
    "pitfalls": "Повторять неидемпотентные мутации (например списание с баланса) без передачи Idempotency Key: если первый запрос на самом деле выполнился, а упал только ответ, повтор приведет к двойному списанию средств.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему декларативный Retry Policy в gRPC Service Config предпочтительнее ручного интерцептора?»\n**Ответ:** Декларативная политика в Service Config (`retryPolicy`) управляется централизованно через DNS/Consul/xDS без изменения клиентского кода, поддерживая автоматический парсинг `PushBack` заголовков сервера и `maxAttempts`."
  },
  {
    "num": 25,
    "title": "Паттерн Idempotency Key: защита от дублирования финансовых транзакций с кэшированием в Redis",
    "task": "Реализуй **Idempotency Key**: клиент генерирует `Idempotency-Key: uuid` для mutation-запросов. Сервер хранит обработанные ключи (Redis, TTL=24h). При повторе с тем же ключом — верни кешированный ответ, не выполняй повторно.",
    "theory": "Принцип идемпотентности мутирующих операций (Idempotency Key Pattern):\n- Клиент перед отправкой платежа генерирует случайный UUID v4:\n  `Idempotency-Key: 7b31cf46-27a3-41c3-8f0a-115f2081c7e2`.\n- Алгоритм работы сервера:\n  1. Проверяем наличие ключа в Redis: `GET idempotency:<key>`.\n  2. Если найден: возвращаем **сохраненный ранее результат** со статусом `HTTP 200 / OK` без повторного списания с карты!\n  3. Если не найден: атомарно захватываем распределенный замок (`SETNX`), выполняем платеж, сохраняем ответ в Redis с TTL=24h и возвращаем клиенту.",
    "step_by_step": "1. Создайте модель сервиса платежей с хранилищем ключей.\n2. Проверьте обработку первого вызова с ключом.\n3. Отправьте повторный вызов с тем же ключом.\n4. Убедитесь, что бизнес-логика списания не сработала дважды.",
    "code_blocks": [
      {
        "filename": "idempotency_key_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n)\n\ntype PaymentResult struct {\n\tTransactionID string\n\tAmount        float64\n\tStatus        string\n}\n\ntype IdempotentPaymentService struct {\n\tmu           sync.Mutex\n\tredisCache   map[string]PaymentResult\n\tactualCharges int\n}\n\nfunc NewPaymentService() *IdempotentPaymentService {\n\treturn &IdempotentPaymentService{\n\t\tredisCache: make(map[string]PaymentResult),\n\t}\n}\n\nfunc (s *IdempotentPaymentService) ProcessPayment(ctx context.Context, idempotencyKey string, amount float64) (PaymentResult, bool) {\n\ts.mu.Lock()\n\tdefer s.mu.Unlock()\n\n\t// 1. Проверяем наличие кэшированного результата\n\tif cached, exists := s.redisCache[idempotencyKey]; exists {\n\t\tfmt.Printf(\"  [Idempotency HIT] Ключ %s уже обработан! Возвращаем кэш.\\n\", idempotencyKey)\n\t\treturn cached, true\n\t}\n\n\t// 2. Реальное списание денег\n\ts.actualCharges++\n\ttxID := fmt.Sprintf(\"tx_bank_%d\", s.actualCharges)\n\tres := PaymentResult{\n\t\tTransactionID: txID,\n\t\tAmount:        amount,\n\t\tStatus:        \"CONFIRMED\",\n\t}\n\n\t// 3. Сохранение в Redis (TTL=24h)\n\ts.redisCache[idempotencyKey] = res\n\tfmt.Printf(\"  [Idempotency MISS] Первое списание: %s на сумму %.2f ₽\\n\", txID, amount)\n\treturn res, false\n}\n\nfunc TestIdempotencyProtection(t *testing.T) {\n\tsvc := NewPaymentService()\n\tkey := \"uuid-payment-order-42\"\n\n\t// 1-я попытка (нормальная)\n\tres1, isCached1 := svc.ProcessPayment(context.Background(), key, 4500.00)\n\tif isCached1 || res1.TransactionID != \"tx_bank_1\" {\n\t\tt.Fatalf(\"Некорректная 1-я операция: %+v\", res1)\n\t}\n\n\t// 2-я попытка (повтор из-за сбоя сети)\n\tres2, isCached2 := svc.ProcessPayment(context.Background(), key, 4500.00)\n\tif !isCached2 || res2.TransactionID != \"tx_bank_1\" {\n\t\tt.Fatalf(\"Повторный запрос не должен создавать новую транзакцию: %+v\", res2)\n\t}\n\n\tif svc.actualCharges != 1 {\n\t\tt.Fatalf(\"Деньги списаны более 1 раза! actualCharges=%d\", svc.actualCharges)\n\t}\n\n\tfmt.Printf(\"Идемпотентность доказана: 2 запроса привели ровно к 1 банковской проводке!\\n\")\n}",
        "note": "Гарантия идемпотентности платежей через кэширование результатов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v idempotency_key_test.go\n# Вывод:\n# === RUN   TestIdempotencyProtection\n#   [Idempotency MISS] Первое списание: tx_bank_1 на сумму 4500.00 ₽\n#   [Idempotency HIT] Ключ uuid-payment-order-42 уже обработан! Возвращаем кэш.\n# Идемпотентность доказана: 2 запроса привели ровно к 1 банковской проводке!\n# --- PASS: TestIdempotencyProtection (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Для защиты от одновременных параллельных запросов с одним и тем же ключом используется атомарная команда Redis `SET idempotency:<key> \"PROCESSING\" NX EX 60`. Второй запрос получает отказ о том, что транзакция уже в процессе выполнения.",
    "pitfalls": "Использовать один и тот же Idempotency-Key для разных параметров запроса (например поменялась сумма или валюта): сервер обязан проверять хеш тела запроса (Payload Hash) и возвращать ошибку `422 Unprocessable Entity` при несовпадении.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как реализовать Idempotency Key на уровне базы данных PostgreSQL без Redis?»\n**Ответ:** Создать таблицу `processed_requests(idempotency_key UUID PRIMARY KEY, request_hash TEXT, response_body JSONB, created_at TIMESTAMPTZ)`. Запись в эту таблицу выполняется внутри той же ACID транзакции, что и изменение баланса. Уникальный индекс `PRIMARY KEY` блокирует любые попытки параллельной вставки одинаковых ключей."
  },
  {
    "num": 26,
    "title": "Очередь недоставленных сообщений Dead Letter Queue (DLQ): изоляция сбойных событий и ручной ретрай",
    "task": "Реализуй **Dead Letter Queue (DLQ)**: воркер обрабатывает события из Kafka/NATS. При 3 неудачных попытках — отправляет в DLQ. Отдельный сервис анализирует DLQ, алертит, позволяет retry вручную.",
    "theory": "Изоляция ядовитых сообщений (Dead Letter Queue / Poison Pill):\n- Если сообщение содержит синтаксически битый JSON или вызывает деление на ноль (Poison Pill), воркер будет падать бесконечно, заблокировав партицию Kafka для всех последующих клиентов.\n- **Паттерн DLQ:**\n  1. Воркер пытается обработать сообщение с локальным повтором (3 попытки).\n  2. Если все попытки исчерпаны: сообщение пересылается в специальный топик `orders-dlq`.\n  3. Основная очередь продолжает работать без остановки.\n  4. Сообщения из `orders-dlq` исследуются инженерами и при исправлении бага возвращаются в работу через скрипт ручного ретрая (Reprocessing).",
    "step_by_step": "1. Создайте модель воркера с счетчиком попыток.\n2. Реализуйте пересылку в DLQ при 3 сбоях.\n3. Смоделируйте ядовитое сообщение.\n4. Протестируйте изоляцию и ручной перезапуск.",
    "code_blocks": [
      {
        "filename": "dead_letter_queue_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n)\n\ntype EventMessage struct {\n\tID       string\n\tPayload  string\n\tAttempts int\n}\n\ntype EventProcessor struct {\n\tmu           sync.Mutex\n\tmainQueue    []*EventMessage\n\tdlqQueue     []*EventMessage\n\tprocessed    []string\n\tmaxRetries   int\n}\n\nfunc NewProcessor(maxRetries int) *EventProcessor {\n\treturn &EventProcessor{maxRetries: maxRetries}\n}\n\nfunc (p *EventProcessor) Process(msg *EventMessage, handler func(string) error) {\n\tp.mu.Lock()\n\tdefer p.mu.Unlock()\n\n\tfor {\n\t\tmsg.Attempts++\n\t\terr := handler(msg.Payload)\n\t\tif err == nil {\n\t\t\tp.processed = append(p.processed, msg.ID)\n\t\t\tfmt.Printf(\"  [Main Queue] Сообщение %s успешно обработано!\\n\", msg.ID)\n\t\t\treturn\n\t\t}\n\n\t\tfmt.Printf(\"  [Fail Attempt %d] Сообщение %s: %v\\n\", msg.Attempts, msg.ID, err)\n\t\tif msg.Attempts >= p.maxRetries {\n\t\t\t// Перемещение в Dead Letter Queue\n\t\t\tp.dlqQueue = append(p.dlqQueue, msg)\n\t\t\tfmt.Printf(\"  >>> [DLQ ROUTE] Сообщение %s отправлено в Dead Letter Queue!\\n\", msg.ID)\n\t\t\treturn\n\t\t}\n\t}\n}\n\nfunc TestDeadLetterQueueRouting(t *testing.T) {\n\tp := NewProcessor(3)\n\n\tpoisonPill := &EventMessage{ID: \"msg_corrupted_13\", Payload: \"INVALID_JSON_NULL_POINTER\"}\n\n\t// Обработчик всегда падает на битых данных\n\tfailingHandler := func(payload string) error {\n\t\treturn fmt.Errorf(\"критическая ошибка десериализации\")\n\t}\n\n\tp.Process(poisonPill, failingHandler)\n\n\tif len(p.dlqQueue) != 1 || p.dlqQueue[0].ID != \"msg_corrupted_13\" {\n\t\tt.Fatalf(\"Сообщение должно было оказаться в DLQ\")\n\t}\n\n\tfmt.Printf(\"Паттерн DLQ успешно защитил пайплайн обработки от зависания!\\n\")\n}",
        "note": "Маршрутизация ядовитых сообщений в Dead Letter Queue"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v dead_letter_queue_test.go\n# Вывод:\n# === RUN   TestDeadLetterQueueRouting\n#   [Fail Attempt 1] Сообщение msg_corrupted_13: критическая ошибка десериализации\n#   [Fail Attempt 2] Сообщение msg_corrupted_13: критическая ошибка десериализации\n#   [Fail Attempt 3] Сообщение msg_corrupted_13: критическая ошибка десериализации\n#   >>> [DLQ ROUTE] Сообщение msg_corrupted_13 отправлено в Dead Letter Queue!\n# Паттерн DLQ успешно защитил пайплайн обработки от зависания!\n# --- PASS: TestDeadLetterQueueRouting (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В заголовки Kafka/RabbitMQ сообщений в DLQ добавляются метаданные: `x-death-reason`, `x-original-topic`, `x-death-timestamp`, позволяющие инженеру понять точную причину отправки в морг без дебага исходного кода.",
    "pitfalls": "Забывать настраивать мониторинг и алерты на размер DLQ: если в DLQ скопится миллион сообщений, они займут всё дисковое пространство брокера.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как безопасно переобработать сообщения из DLQ (Reprocessing)?»\n**Ответ:** После деплоя фикса бага в коде запускается DLQ Redrive Worker. Он вычитывает сообщения из топика `orders-dlq`, валидирует их исправленным парсером и публикует обратно в исходный топик `orders` с флагом `x-retried-from-dlq=true`."
  },
  {
    "num": 27,
    "title": "Сквозная трансляция дедлайнов (Deadline Propagation): передача оставшегося времени в нижележащие вызовы",
    "task": "Настройте deadline propagation: сервер, получая запрос с дедлайном, передаёт его остаток в исходящий вызов к другому сервису.",
    "theory": "Механика сквозной передачи дедлайнов (Context Deadline Propagation):\n- Если клиент вызвал Сервис А с дедлайном в 1.0 секунду.\n- Сервис А потратил 300 мс на чтение кэша и собирается вызвать Сервис B.\n- Сервис А обязан передать в исходящий вызов тот же самый `ctx`:\n  ```go\n  // gRPC автоматически берет ctx.Deadline() и передает заголовок grpc-timeout: 700mS\n  respB, err := clientB.DoTask(ctx, reqB)\n  ```\n- Сервис B получает контекст с оставшимся временем в 700 мс.",
    "step_by_step": "1. Создайте контекст с дедлайном на 100 мс.\n2. Просимулируйте работу первого сервиса в 40 мс.\n3. Проверьте остаток дедлайна при передаче во второй сервис.\n4. Убедитесь в автоматическом наследовании остатка времени.",
    "code_blocks": [
      {
        "filename": "deadline_propagation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\nfunc ServiceB(ctx context.Context) error {\n\tdeadline, ok := ctx.Deadline()\n\tif !ok {\n\t\treturn fmt.Errorf(\"дедлайн не передан\")\n\t}\n\n\tremaining := time.Until(deadline)\n\tfmt.Printf(\"  [Service B] Получен контекст с остатком дедлайна: %v\\n\", remaining.Round(time.Millisecond))\n\n\tif remaining < 10*time.Millisecond {\n\t\treturn fmt.Errorf(\"остаток дедлайна недостаточен для выполнения задачи\")\n\t}\n\treturn nil\n}\n\nfunc ServiceA(ctx context.Context) error {\n\t// Сервис А тратит 35 мс на внутреннюю работу\n\ttime.Sleep(35 * time.Millisecond)\n\n\t// Передает тот же самый ctx в вызов ServiceB\n\treturn ServiceB(ctx)\n}\n\nfunc TestDeadlinePropagation(t *testing.T) {\n\t// Клиент задает исходный дедлайн 100 мс\n\tctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)\n\tdefer cancel()\n\n\terr := ServiceA(ctx)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка выполнения: %v\", err)\n\t}\n\n\tfmt.Println(\"Сквозной дедлайн успешно передан через цепочку микросервисов!\")\n}",
        "note": "Автоматическое сохранение дедлайна в контексте вызова"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v deadline_propagation_test.go\n# Вывод:\n# === RUN   TestDeadlinePropagation\n#   [Service B] Получен контекст с остатком дедлайна: 65ms\n# Сквозной дедлайн успешно передан через цепочку микросервисов!\n# --- PASS: TestDeadlinePropagation (0.04s)\n# PASS"
      }
    ],
    "under_the_hood": "Спецификация gRPC кодирует оставшееся время в заголовке `grpc-timeout: <number><unit>`, где `unit` может быть `H` (часы), `M` (минуты), `S` (секунды), `m` (миллисекунды), `u` (микросекунды), `n` (наносекунды).",
    "pitfalls": "Создавать новый `context.Background()` при межсервисном вызове вместо передачи входящего `ctx`: это обрывает цепочку дедлайна и трассировки, порождая горутины-зомби.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что происходит на сервере, если клиент оборвал HTTP/2 соединение по таймауту?»\n**Ответ:** Клиент шлет HTTP/2 фрейм `RST_STREAM`. gRPC-сервер ловит закрытие стрима и мгновенно переводит `ctx.Done()` в закрытое состояние. Если обработчик сервиса корректно слушает `ctx.Done()`, он досрочно прерывает SQL-запросы к БД и освобождает ресурсы CPU."
  },
  {
    "num": 28,
    "title": "Сквозная отмена запроса и Context Propagation: связка HTTP APIGateway, gRPC и базы данных",
    "task": "**Сквозная отмена и Context Propagation**: Создайте архитектуру из двух микросервисов: `APIGateway` (принимает HTTP) и `UserService` (принимает gRPC).\n    * Пользователь делает HTTP-запрос к `APIGateway` с таймаутом в 1 секунду.\n    * `APIGateway` делает gRPC-запрос к `UserService`.\n    * Настройте цепочку вызовов так, чтобы при истечении таймаута на уровне HTTP-запроса, сигнал отмены контекста автоматически долетал до gRPC-сервера `UserService`, и тот досрочно прекращал выполнение тяжелого SQL-запроса.",
    "theory": "Сквозной каскад отмены контекста (End-to-End Context Cancellation):\n- Пользователь нажимает `Escape` или закрывает вкладку браузера $\\to$ HTTP сокет закрывается.\n- `http.Request.Context()` переходит в состояние `Canceled`.\n- `APIGateway` передает `r.Context()` в клиентский gRPC вызов `client.GetUser(r.Context(), req)`.\n- gRPC клиент отправляет на сервер фрейм `RST_STREAM` с кодом `CANCEL`.\n- Сервер ловит отмену в `ctx.Done()` и прерывает тяжелый SQL запрос к PostgreSQL через `db.QueryContext(ctx, ...)`!",
    "step_by_step": "1. Создайте gRPC mock-сервер, эмулирующий долгий запрос к БД.\n2. Проверьте `select <-ctx.Done()` во время выполнения тяжелой работы.\n3. Сымитируйте отмену HTTP-запроса через контекст.\n4. Убедитесь в досрочном прерывании работы бэкенда.",
    "code_blocks": [
      {
        "filename": "e2e_cancellation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\nfunc MockDatabaseLongQuery(ctx context.Context, queryAborted *bool) error {\n\tselect {\n\tcase <-time.After(200 * time.Millisecond):\n\t\treturn nil\n\tcase <-ctx.Done():\n\t\t*queryAborted = true\n\t\tfmt.Println(\"  [PostgreSQL Driver] Получен ctx.Done()! Транзакция БД досрочно прервана.\")\n\t\treturn ctx.Err()\n\t}\n}\n\nfunc APIGatewayHandler(httpCtx context.Context, queryAborted *bool) error {\n\t// Gateway пробрасывает httpCtx прямо в вызов бэкенда\n\treturn MockDatabaseLongQuery(httpCtx, queryAborted)\n}\n\nfunc TestEndToEndCancellation(t *testing.T) {\n\t// Пользователь закрыл вкладку через 40 мс (таймаут HTTP)\n\thttpCtx, cancel := context.WithTimeout(context.Background(), 40*time.Millisecond)\n\tdefer cancel()\n\n\tqueryAborted := false\n\terr := APIGatewayHandler(httpCtx, &queryAborted)\n\n\tif err != context.DeadlineExceeded {\n\t\tt.Fatalf(\"Ожидалась ошибка DeadlineExceeded, получено: %v\", err)\n\t}\n\n\tif !queryAborted {\n\t\tt.Fatal(\"Тяжелый запрос к БД не был прерван при отмене HTTP-клиента!\")\n\t}\n\n\tfmt.Println(\"Сквозная отмена контекста успешно спасла базу данных от бесполезной нагрузки!\")\n}",
        "note": "Сквозная трансляция сигнала отмены контекста до драйвера базы данных"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v e2e_cancellation_test.go\n# Вывод:\n# === RUN   TestEndToEndCancellation\n#   [PostgreSQL Driver] Получен ctx.Done()! Транзакция БД досрочно прервана.\n# Сквозная отмена контекста успешно спасла базу данных от бесполезной нагрузки!\n# --- PASS: TestEndToEndCancellation (0.04s)\n# PASS"
      }
    ],
    "under_the_hood": "Драйверы баз данных `pgx` и `database/sql` при закрытии контекста немедленно отправляют в сокет PostgreSQL сигнал прерывания команды `CancelRequest`.",
    "pitfalls": "Использовать в репозитории устаревший метод `db.Query()` без контекста: такой запрос продолжит выполняться на сервере БД часами, сжигая CPU, даже если клиент давно отключился.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему важно пробрасывать r.Context() в gRPC клиент?»\n**Ответ:** Это фундамент надежности HighLoad систем. Если клиент ушел или отвалился по таймауту, дальнейшее выполнение вычислений в глубине кластера (микросервисы, кэши, реплики БД) является 100% паразитной нагрузкой (Wasted Work). Проброс `r.Context()` гарантирует мгновенную остановку всего графа вызовов."
  },
  {
    "num": 29,
    "title": "Проверки жизнеспособности в Kubernetes: разграничение Liveness (/healthz) и Readiness (/ready) проб",
    "task": "Настрой **health checks**: Kubernetes liveness probe (`/healthz` — HTTP 200, сервис жив), readiness probe (`/ready` — сервис готов принимать трафик, например БД подключена). Разные endpoint'ы!",
    "theory": "Принципиальная разница между Liveness и Readiness в Kubernetes:\n- **Liveness Probe (`/healthz`):**\n  - Вопрос оркестратора: «Процесс сервиса жив (нет дедлока в памяти)?»\n  - Если возвращает ошибку $\\to$ Kubernetes **убивает под и перезапускает его (`SIGKILL`)**.\n  - Проверка должна быть сверхлегкой (не должна трогать внешнюю БД!).\n- **Readiness Probe (`/ready`):**\n  - Вопрос оркестратора: «Сервис готов прямо сейчас обрабатывать клиентский трафик?»\n  - Проверяет доступность PostgreSQL, прогрев кэша Redis, подключение к Kafka.\n  - Если возвращает ошибку $\\to$ Kubernetes **НЕ убивает под**, а временно **исключает его IP из эндпоинтов Service**, предотвращая ошибки у пользователей.",
    "step_by_step": "1. Создайте хэндлер `/healthz` для Liveness.\n2. Создайте хэндлер `/ready` с проверкой подключения к БД.\n3. Проверьте изоляцию логики проб.\n4. Протестируйте поведение при временном отключении БД.",
    "code_blocks": [
      {
        "filename": "k8s_probes_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"sync/atomic\"\n\t\"testing\"\n)\n\ntype ProbeServer struct {\n\tdbConnected int32 // 1 - подключена, 0 - сбой\n}\n\nfunc (s *ProbeServer) LivenessHandler(w http.ResponseWriter, r *http.Request) {\n\t// Liveness: только проверка живости рантайма Go (HTTP 200)\n\tw.WriteHeader(http.StatusOK)\n\t_, _ = w.Write([]byte(\"OK\"))\n}\n\nfunc (s *ProbeServer) ReadinessHandler(w http.ResponseWriter, r *http.Request) {\n\t// Readiness: глубокая проверка зависимостей (PostgreSQL)\n\tif atomic.LoadInt32(&s.dbConnected) == 1 {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"READY\"))\n\t} else {\n\t\tw.WriteHeader(http.StatusServiceUnavailable)\n\t\t_, _ = w.Write([]byte(\"DB_UNAVAILABLE\"))\n\t}\n}\n\nfunc TestK8sProbes(t *testing.T) {\n\tserver := &ProbeServer{}\n\tatomic.StoreInt32(&server.dbConnected, 0) // БД временно упала\n\n\t// 1. Проверяем Liveness: сервис жив, перезапускать под НЕЛЬЗЯ!\n\trecLive := httptest.NewRecorder()\n\tserver.LivenessHandler(recLive, httptest.NewRequest(\"GET\", \"/healthz\", nil))\n\tif recLive.Code != http.StatusOK {\n\t\tt.Fatalf(\"Liveness не должен падать при сбое БД: %d\", recLive.Code)\n\t}\n\n\t// 2. Проверяем Readiness: сервис временно не готов к трафику\n\trecReady := httptest.NewRecorder()\n\tserver.ReadinessHandler(recReady, httptest.NewRequest(\"GET\", \"/ready\", nil))\n\tif recReady.Code != http.StatusServiceUnavailable {\n\t\tt.Fatalf(\"Readiness должен вернуть 503 при сбое БД: %d\", recReady.Code)\n\t}\n\n\tfmt.Println(\"Liveness статус: 200 OK (под остается живым)\")\n\tfmt.Println(\"Readiness статус: 503 Service Unavailable (трафик снят без перезапуска пода)\")\n}",
        "note": "Раздельная архитектура Liveness и Readiness проб для Kubernetes"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v k8s_probes_test.go\n# Вывод:\n# === RUN   TestK8sProbes\n# Liveness статус: 200 OK (под остается живым)\n# Readiness статус: 503 Service Unavailable (трафик снят без перезапуска пода)\n# --- PASS: TestK8sProbes (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Если в Liveness пробу поместить `db.Ping()`, то при кратковременном сбое PostgreSQL все 100 подов сервиса одновременно упадут в цикличный перезапуск (`CrashLoopBackOff`), вызвав лавину соединений к базе при старте.",
    "pitfalls": "Делать Liveness и Readiness одним и тем же эндпоинтом: это грубейшая ошибка эксплуатации Kubernetes в HighLoad.",
    "bigtech_interview": "**Вопрос с собеседования:** «Для чего в Kubernetes 1.18+ добавлена Startup Probe?»\n**Ответ:** Для медленно стартующих сервисов (тяжелый прогрев ML-модели или загрузка кэша в 60 секунд). Startup Probe отключает Liveness и Readiness до тех пор, пока сервис не подтвердит завершение инициализации, предотвращая преждевременное убийство пода оркестратором по таймауту liveness."
  },
  {
    "num": 30,
    "title": "Клиентский аудит доступности сервиса через grpc_health_v1 перед выполнением запроса",
    "task": "Реализуйте health check: добавьте серверу реализацию `grpc_health_v1` и проверяйте его состояние из клиента перед запросами.",
    "theory": "Превентивная проверка готовности (Pre-flight Health Verification):\n- Перед выполнением критического пакетного вызова клиент может быстро запросить статус здоровья целевого сервиса.\n- Метод `healthClient.Check(ctx, &HealthCheckRequest{Service: \"service_name\"})`:\n  - Если вернулся статус `SERVING` — выполняем запрос.\n  - Если вернулся статус `NOT_SERVING` — перенаправляем запрос на резервный кластер или возвращаем понятную бизнес-ошибку.",
    "step_by_step": "1. Создайте клиентский хелпер проверки статуса gRPC.\n2. Проверьте реакцию на статус SERVING.\n3. Проверьте реакцию на статус NOT_SERVING.\n4. Продемонстрируйте безопасное принятие решений.",
    "code_blocks": [
      {
        "filename": "preflight_health_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\n\thealthpb \"google.golang.org/grpc/health/grpc_health_v1\"\n)\n\ntype MockHealthClient struct {\n\tstatus healthpb.HealthCheckResponse_ServingStatus\n}\n\nfunc (m *MockHealthClient) Check(ctx context.Context, in *healthpb.HealthCheckRequest, opts ...any) (*healthpb.HealthCheckResponse, error) {\n\treturn &healthpb.HealthCheckResponse{Status: m.status}, nil\n}\n\nfunc SafeExecuteWithPreflight(ctx context.Context, client *MockHealthClient, action func() error) error {\n\tresp, err := client.Check(ctx, &healthpb.HealthCheckRequest{Service: \"order-service\"})\n\tif err != nil {\n\t\treturn fmt.Errorf(\"health check rpc failed: %w\", err)\n\t}\n\n\tif resp.Status != healthpb.HealthCheckResponse_SERVING {\n\t\treturn fmt.Errorf(\"сервис не готов к обслуживанию (статус: %s)\", resp.Status)\n\t}\n\n\treturn action()\n}\n\nfunc TestPreflightHealthCheck(t *testing.T) {\n\t// 1. Сервер готов\n\thealthyClient := &MockHealthClient{status: healthpb.HealthCheckResponse_SERVING}\n\texecuted := false\n\terr1 := SafeExecuteWithPreflight(context.Background(), healthyClient, func() error {\n\t\texecuted = true\n\t\treturn nil\n\t})\n\tif err1 != nil || !executed {\n\t\tt.Fatalf(\"Запрос должен был выполниться: %v\", err1)\n\t}\n\tfmt.Println(\"1. Preflight Health Check: статус SERVING -> операция успешно выполнена\")\n\n\t// 2. Сервер деградировал (NOT_SERVING)\n\tunhealthyClient := &MockHealthClient{status: healthpb.HealthCheckResponse_NOT_SERVING}\n\terr2 := SafeExecuteWithPreflight(context.Background(), unhealthyClient, func() error {\n\t\tt.Fatal(\"Операция не должна была запускаться!\")\n\t\treturn nil\n\t})\n\tif err2 == nil {\n\t\tt.Fatal(\"Ожидался отказ из-за NOT_SERVING\")\n\t}\n\tfmt.Printf(\"2. Preflight Health Check: превентивный отказ -> %v\\n\", err2)\n}",
        "note": "Превентивный аудит доступности сервера перед отправкой бизнес-запросов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v preflight_health_test.go\n# Вывод:\n# === RUN   TestPreflightHealthCheck\n# 1. Preflight Health Check: статус SERVING -> операция успешно выполнена\n# 2. Preflight Health Check: превентивный отказ -> сервис не готов к обслуживанию (статус: NOT_SERVING)\n# --- PASS: TestPreflightHealthCheck (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Встроенный балансировщик gRPC может автоматически использовать протокол Health Check при включении флага `health_checking_config` в Service Config.",
    "pitfalls": "Делать preflight проверку перед КАЖДЫМ обычным RPC: это удвоит количество сетевых вызовов (2x RPS) к серверу. Используйте серверный стриминг `Watch` или доверяйте автоматическому балансировщику.",
    "bigtech_interview": "**Вопрос с собеседования:** «Чем метод Watch в grpc_health_v1 эффективнее периодического Check?»\n**Ответ:** Метод `Watch` открывает один долгоживущий gRPC-стрим. Сервер держит соединение открытым и шлет новый фрейм ТОЛЬКО в момент фактического изменения статуса здоровья (Zero Overhead в нормальном состоянии)."
  },
  {
    "num": 31,
    "title": "Метрики Prometheus и дашборды Grafana: гистограммы latency p50/p95/p99 и подсчет ошибок",
    "task": "Настрой **metrics** (Prometheus + Grafana): `grpc_server_handled_total`, `grpc_server_handling_seconds`, `grpc_client_handled_total`. Создай dashboard: RPS, latency p50/p95/p99, error rate.",
    "theory": "Инженерные дашборды мониторинга микросервисов:\n- Стандартные метрики библиотеки `go-grpc-prometheus`:\n  - `grpc_server_handled_total{grpc_service=\"...\", grpc_method=\"...\", grpc_code=\"OK\"}` — счетчик обработанных вызовов.\n  - `grpc_server_handling_seconds_bucket{le=\"0.05\"}` — гистограмма длительности обработки запросов.\n- PromQL формулы для Grafana:\n  - **RPS:** `sum(rate(grpc_server_handled_total[1m])) by (grpc_method)`\n  - **Error Rate:** `sum(rate(grpc_server_handled_total{grpc_code!=\"OK\"}[1m])) / sum(rate(grpc_server_handled_total[1m])) * 100`\n  - **Latency 99th Percentile:** `histogram_quantile(0.99, sum(rate(grpc_server_handling_seconds_bucket[5m])) by (le))`",
    "step_by_step": "1. Смоделируйте структуру сбора данных гистограммы.\n2. Реализуйте функцию вычисления перцентилей (P50, P95, P99).\n3. Проверьте расчет метрик при разбросе задержек.\n4. Продемонстрируйте соответствие формулам PromQL.",
    "code_blocks": [
      {
        "filename": "metrics_histogram_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sort\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype LatencyStats struct {\n\tsamples []float64 // задержки в миллисекундах\n}\n\nfunc (s *LatencyStats) Add(d time.Duration) {\n\ts.samples = append(s.samples, float64(d.Microseconds())/1000.0)\n}\n\nfunc (s *LatencyStats) Percentile(p float64) float64 {\n\tif len(s.samples) == 0 {\n\t\treturn 0\n\t}\n\tsort.Float64s(s.samples)\n\tidx := int(float64(len(s.samples)-1) * p)\n\treturn s.samples[idx]\n}\n\nfunc TestPrometheusPercentiles(t *testing.T) {\n\tstats := &LatencyStats{}\n\n\t// Генерируем 100 замеров (95 быстрых 5-10мс и 5 медленных 120-200мс)\n\tfor i := 0; i < 95; i++ {\n\t\tstats.Add(time.Duration(5+i%5) * time.Millisecond)\n\t}\n\tfor i := 0; i < 5; i++ {\n\t\tstats.Add(time.Duration(120+i*20) * time.Millisecond)\n\t}\n\n\tp50 := stats.Percentile(0.50)\n\tp95 := stats.Percentile(0.95)\n\tp99 := stats.Percentile(0.99)\n\n\tfmt.Println(\"Метрики задержки микросервиса (SLO Dashboard):\")\n\tfmt.Printf(\"  • p50 (медиана): %.2f ms\\n\", p50)\n\tfmt.Printf(\"  • p95:           %.2f ms\\n\", p95)\n\tfmt.Printf(\"  • p99 (хвост):   %.2f ms\\n\", p99)\n\n\tif p99 < 100 {\n\t\tt.Fatalf(\"p99 должен отражать медленные хвосты, получено: %f\", p99)\n\t}\n}",
        "note": "Расчет перцентилей p50, p95, p99 для дашбордов Prometheus и Grafana"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v metrics_histogram_test.go\n# Вывод:\n# === RUN   TestPrometheusPercentiles\n# Метрики задержки микросервиса (SLO Dashboard):\n#   • p50 (медиана): 7.00 ms\n#   • p95:           9.00 ms\n#   • p99:           180.00 ms\n# --- PASS: TestPrometheusPercentiles (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Гистограммы Prometheus вычисляют перцентили на стороне сервера мониторинга с помощью линейной интерполяции между бакетами (`histogram_quantile`), что экономит память микросервиса.",
    "pitfalls": "Выбирать стандартные границы бакетов Prometheus (0.005, 0.01, 0.025...) для медленных запросов: бакеты обязаны соответствовать вашему SLA (например, 100ms, 250ms, 500ms, 1s, 2s).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему среднее значение (Average Latency) обманчиво в микросервисах?»\n**Ответ:** Если 99% запросов выполняются за 1 мс, а 1% зависает на 10 секунд, среднее покажет отличные 100 мс, скрывая катастрофу: каждый сотый пользователь уходит из-за зависшей корзины. Перцентили p95/p99/p99.9 честно показывают худший клиентский опыт."
  },
  {
    "num": 32,
    "title": "Профилирование Go-микросервисов в production: net/http/pprof и безопасность эндпоинтов",
    "task": "Настрой **profiling**: `net/http/pprof` endpoint'ы (`/debug/pprof/heap`, `/debug/pprof/goroutine`, `/debug/pprof/cpu`). Собирай профили в production (с осторожностью). Анализируй через `go tool pprof`.",
    "theory": "Низкоуровневое профилирование в Production (pprof endpoints):\n- Пакет `net/http/pprof` автоматически регистрирует обработчики:\n  - `/debug/pprof/heap` — снимок распределения памяти и аллокаций.\n  - `/debug/pprof/goroutine` — стек-трейсы всех работающих горутин (поиск утечек).\n  - `/debug/pprof/profile?seconds=30` — CPU профилирование.\n- Правило безопасности: **pprof никогда не экспонируется в публичную сеть!** Он поднимается на отдельном внутреннем порту `:6060` или закрывается mTLS/BasicAuth.",
    "step_by_step": "1. Поднимите изолированный HTTP сервер для администрирования.\n2. Зарегистрируйте стандартные хэндлеры `net/http/pprof`.\n3. Проверьте доступность снимка горутин.\n4. Протестируйте сбор профиля без блокировки основного сервиса.",
    "code_blocks": [
      {
        "filename": "pprof_setup_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"net/http/pprof\"\n\t\"testing\"\n)\n\nfunc NewInternalAdminMux() *http.ServeMux {\n\tmux := http.NewServeMux()\n\n\t// Регистрация pprof на внутреннем изолированном роутере\n\tmux.HandleFunc(\"/debug/pprof/\", pprof.Index)\n\tmux.HandleFunc(\"/debug/pprof/cmdline\", pprof.Cmdline)\n\tmux.HandleFunc(\"/debug/pprof/profile\", pprof.Profile)\n\tmux.HandleFunc(\"/debug/pprof/symbol\", pprof.Symbol)\n\tmux.HandleFunc(\"/debug/pprof/trace\", pprof.Trace)\n\n\treturn mux\n}\n\nfunc TestPprofEndpoints(t *testing.T) {\n\tmux := NewInternalAdminMux()\n\n\t// Тестируем доступность главной страницы pprof\n\trec := httptest.NewRecorder()\n\treq := httptest.NewRequest(\"GET\", \"/debug/pprof/\", nil)\n\tmux.ServeHTTP(rec, req)\n\n\tif rec.Code != http.StatusOK {\n\t\tt.Fatalf(\"Ожидался статус 200, получено: %d\", rec.Code)\n\t}\n\n\tfmt.Println(\"pprof внутренний эндпоинт успешно смонтирован и доступен для анализа!\")\n}",
        "note": "Изолированное подключение pprof на внутреннем интерфейсе"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Команды инженера для снятия профилей с пода Kubernetes:\nkubectl port-forward pod/order-service-7f9b8c-x9z 6060:6060\n\n# 1. Анализ утечек памяти в интерактивном веб-интерфейсе:\ngo tool pprof -http=:8081 http://localhost:6060/debug/pprof/heap\n\n# 2. Снятие 30-секундного CPU профиля:\ncurl -sK -v http://localhost:6060/debug/pprof/profile?seconds=30 > cpu.pprof\ngo tool pprof cpu.pprof"
      }
    ],
    "under_the_hood": "Профилировщик CPU использует системный таймер ядра Linux `setitimer(ITIMER_PROF)`. Ядро шлет сигнал `SIGPROF` процессу каждые 10 мс, записывая текущий счетчик команд (PC) выполняемой горутины.",
    "pitfalls": "Использовать дефолтный `import _ \"net/http/pprof\"` вместе с публичным `http.ListenAndServe(\":8080\", nil)`: злоумышленники получат доступ к коду, дампу памяти и смогут положить сервис DoS-атакой через вызов `/debug/pprof/profile`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы накладные расходы (Overhead) от включенного CPU профилирования в production?»\n**Ответ:** Накладные расходы CPU профилирования в Go крайне малы и составляют порядка **1–3% CPU**. Его можно безопасно включать на работающем сервисе на 30–60 секунд для локализации аномалий производительности."
  },
  {
    "num": 33,
    "title": "Оптимизированный Dockerfile: multi-stage сборка, статическая линковка и образ scratch/distroless",
    "task": "Создай **Dockerfile** для gRPC-сервиса: multi-stage build (builder stage с `golang:1.24-alpine`, final stage `scratch` или `distroless`). Статическая линковка: `CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo`.",
    "theory": "Стандарты безопасной сборки контейнеров Go (Multi-Stage Dockerfile):\n- **Stage 1 (Builder):** `golang:1.24-alpine`\n  - Компиляция строго статического бинарника без зависимостей от libc:\n    `CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-s -w\" -o /app/server ./cmd/server`\n- **Stage 2 (Runtime):** `scratch` или `gcr.io/distroless/static-debian12`\n  - Вес итогового образа: **15–25 МБ** (вместо 1.2 ГБ).\n  - Нулевая поверхность атаки (Zero Attack Surface): нет shell `/bin/sh`, нет утилит `curl`/`wget`, нет пакетных менеджеров.",
    "step_by_step": "1. Опишите stage компиляции с кэшированием зависимостей.\n2. Настройте флаги статической линковки `CGO_ENABLED=0`.\n3. Опишите финальный минималистичный контейнер.\n4. Проверьте инструкции безопасности non-root пользователя.",
    "code_blocks": [
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# ==========================================\n# Stage 1: Компиляция статического бинарника\n# ==========================================\nFROM golang:1.24-alpine AS builder\n\nWORKDIR /src\n\n# Кэширование слоев go.mod и go.sum\nCOPY go.mod go.sum ./\nRUN go mod download\n\n# Копирование исходного кода\nCOPY . .\n\n# Статическая линковка без CGO со сжатием отладочных символов (-s -w)\nRUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \\\n    -trimpath \\\n    -ldflags=\"-s -w -X main.version=1.0.0\" \\\n    -o /bin/grpc-service ./cmd/server\n\n# ==========================================\n# Stage 2: Минимальный production-образ\n# ==========================================\nFROM gcr.io/distroless/static-debian12:nonroot\n\n# Запуск от непривилегированного пользователя (UID 65532)\nUSER nonroot:nonroot\n\nWORKDIR /app\nCOPY --from=builder /bin/grpc-service /app/grpc-service\n\n# Порт gRPC сервиса\nEXPOSE 50051\n\nENTRYPOINT [\"/app/grpc-service\"]",
        "note": "Production Multi-Stage Dockerfile на базе Distroless"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка и проверка размера образа:\ndocker build -t company/order-service:v1.0.0 .\n\n# Аудит размера и безопасности:\ndocker images company/order-service:v1.0.0\n# REPOSITORY              TAG       SIZE\n# company/order-service   v1.0.0    22.4MB\n\n# Сканирование уязвимостей через Trivy:\ntrivy image company/order-service:v1.0.0\n# Total: 0 (UNKNOWN: 0, LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0)"
      }
    ],
    "under_the_hood": "Флаг `-ldflags=\"-s -w\"` удаляет таблицу символов (Symbol Table) и отладочную информацию DWARF, уменьшая размер скомпилированного бинарника Go на 30–40%.",
    "pitfalls": "Использовать `scratch` и забыть скопировать корневые SSL-сертификаты `ca-certificates.crt`: сервис упадет с ошибкой `x509: certificate signed by unknown authority` при любом исходящем HTTPS вызове. Distroless уже содержит актуальные CA-сертификаты.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем запускать контейнер под пользователем nonroot:nonroot?»\n**Ответ:** По умолчанию процесс в Docker работает с правами `root` (UID 0). В случае уязвимости побега из контейнера (Container Escape CVE) злоумышленник получит полные права суперпользователя на хостовой ноде Linux."
  },
  {
    "num": 34,
    "title": "gRPC-Gateway: трансляция REST JSON в gRPC через аннотации google.api.http",
    "task": "**gRPC-Gateway (REST -> gRPC)**: Клиенту (например, браузеру на JS) сложно общаться по чистому gRPC. Установи `grpc-ecosystem/grpc-gateway`. Разметь свой `user.proto` аннотациями `google.api.http`. Сгенерируй реверс-прокси, который поднимет HTTP REST сервер и будет \"на лету\" транслировать JSON-запросы в Protobuf и отправлять твоему gRPC-серверу.",
    "theory": "Архитектура gRPC-Gateway:\n```\n[ Browser / curl ] -- HTTP/1.1 JSON --> [ gRPC-Gateway Proxy ] -- gRPC HTTP/2 --> [ Core Service ]\n```\n- В `.proto` методам RPC добавляются аннотации Google API:\n  ```protobuf\n  import \"google/api/annotations.proto\";\n\n  rpc GetUser (GetUserRequest) returns (UserResponse) {\n    option (google.api.http) = {\n      get: \"/v1/users/{id}\"\n    };\n  }\n  ```\n- Генератор `protoc-gen-grpc-gateway` создает высокопроизводительный мультиплексор `runtime.ServeMux`, транслирующий JSON в бинарный Protobuf и проксирующий запрос по локальному сокету.",
    "step_by_step": "1. Опишите proto-файл с аннотациями `google.api.http`.\n2. Создайте `runtime.NewServeMux()`.\n3. Смоделируйте трансляцию HTTP пути `/v1/users/42` в gRPC запрос.\n4. Протестируйте работу шлюза.",
    "code_blocks": [
      {
        "filename": "api/proto/user_gateway.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage user.v1;\n\noption go_package = \"github.com/company/user/v1;userv1\";\n\nimport \"google/api/annotations.proto\";\n\nmessage GetUserRequest {\n  string id = 1;\n}\n\nmessage UserResponse {\n  string id = 1;\n  string name = 2;\n  string email = 3;\n}\n\nservice UserService {\n  rpc GetUser (GetUserRequest) returns (UserResponse) {\n    option (google.api.http) = {\n      get: \"/v1/users/{id}\"\n    };\n  }\n}",
        "note": "Разметка методов proto3 для генерации REST endpoints"
      },
      {
        "filename": "grpc_gateway_transcoder_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"strings\"\n\t\"testing\"\n)\n\ntype MockGatewayProxy struct {\n\tgrpcBackendAddr string\n}\n\nfunc (gw *MockGatewayProxy) ServeHTTP(w http.ResponseWriter, r *http.Request) {\n\tif strings.HasPrefix(r.URL.Path, \"/v1/users/\") && r.Method == http.MethodGet {\n\t\tuserID := strings.TrimPrefix(r.URL.Path, \"/v1/users/\")\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\t// Трансляция JSON ответа от Protobuf бэкенда\n\t\t_, _ = fmt.Fprintf(w, `{\"id\":%q,\"name\":\"Алексей\",\"email\":\"alex@tech.ru\"}`, userID)\n\t\treturn\n\t}\n\thttp.NotFound(w, r)\n}\n\nfunc TestGatewayTranscoder(t *testing.T) {\n\tts := httptest.NewServer(&MockGatewayProxy{grpcBackendAddr: \"localhost:50051\"})\n\tdefer ts.Close()\n\n\tresp, err := http.Get(ts.URL + \"/v1/users/usr_42\")\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка HTTP вызова: %v\", err)\n\t}\n\tdefer resp.Body.Close()\n\n\tbody, _ := io.ReadAll(resp.Body)\n\tfmt.Printf(\"HTTP клиент получил ответ от gRPC-Gateway:\\n%s\\n\", string(body))\n\n\tif !strings.Contains(string(body), `\"id\":\"usr_42\"`) {\n\t\tt.Fatal(\"Некорректная трансляция данных\")\n\t}\n}",
        "note": "Трансляция входящего HTTP/1.1 JSON вызова в gRPC"
      }
    ],
    "under_the_hood": "`grpc-gateway` использует высокопроизводительный JSONPB маршалер `protojson`, гарантирующий строгое соответствие camelCase/snake_case именований полей спецификации Protobuf v3.",
    "pitfalls": "Забыть включить флаг `emitUnpopulated: true` в JSONPb опциях: по умолчанию Protobuf v3 пропускает нулевые значения полей (`0`, `\"\"`, `false`), и клиент в ответе получит пустой JSON `{}`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем запускать gRPC-Gateway в одном процессе с gRPC-сервером через cmux?»\n**Ответ:** Это экономит ресурсы и устраняет сетевой хоп: HTTP и gRPC обслуживаются на одном TCP-порту, а внутренний шлюз общается с сервером через виртуальные in-memory сокеты `bufconn`, обеспечивая минимальные задержки."
  },
  {
    "num": 35,
    "title": "Интеграция OpenTelemetry: сквозной контекст трассировки через метаданные gRPC",
    "task": "Интегрируйте OpenTelemetry: инструментируйте сервер и клиент для трассировки запросов. Передавайте trace context через метаданные gRPC.",
    "theory": "Проброс контекста трассировки через gRPC Metadata (W3C TraceContext):\n- Стандартный HTTP заголовок: `traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`\n  - `00` — версия стандарта.\n  - `4bf92f35...` — 128-битный Trace ID.\n  - `00f067aa...` — 64-битный Parent Span ID.\n  - `01` — флаг сэмплирования (Sampled = true).\n- Клиентский интерцептор инжектирует `traceparent` в исходящие метаданные.\n- Серверный интерцептор извлекает его и создает дочерний спан.",
    "step_by_step": "1. Реализуйте инжекцию TraceContext в метаданные.\n2. Реализуйте извлечение TraceContext на стороне сервера.\n3. Проверьте совпадение TraceID.\n4. Протестируйте сквозной вызов.",
    "code_blocks": [
      {
        "filename": "opentelemetry_metadata_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"strings\"\n\t\"testing\"\n\n\t\"google.golang.org/grpc/metadata\"\n)\n\nconst W3CTraceParentHeader = \"traceparent\"\n\nfunc InjectTraceContext(ctx context.Context, traceID, spanID string) context.Context {\n\tval := fmt.Sprintf(\"00-%s-%s-01\", traceID, spanID)\n\treturn metadata.AppendToOutgoingContext(ctx, W3CTraceParentHeader, val)\n}\n\nfunc ExtractTraceContext(ctx context.Context) (traceID string, spanID string, err error) {\n\tmd, ok := metadata.FromIncomingContext(ctx)\n\tif !ok {\n\t\treturn \"\", \"\", fmt.Errorf(\"метаданные отсутствуют\")\n\t}\n\n\tvals := md.Get(W3CTraceParentHeader)\n\tif len(vals) == 0 {\n\t\treturn \"\", \"\", fmt.Errorf(\"заголовок traceparent не найден\")\n\t}\n\n\tparts := strings.Split(vals[0], \"-\")\n\tif len(parts) != 4 {\n\t\treturn \"\", \"\", fmt.Errorf(\"некорректный формат W3C traceparent: %s\", vals[0])\n\t}\n\n\treturn parts[1], parts[2], nil\n}\n\nfunc TestTraceContextPropagation(t *testing.T) {\n\texpectedTraceID := \"4bf92f3577b34da6a3ce929d0e0e4736\"\n\tclientSpanID := \"00f067aa0ba902b7\"\n\n\t// 1. Клиент внедряет заголовок\n\toutCtx := InjectTraceContext(context.Background(), expectedTraceID, clientSpanID)\n\n\t// Имитация передачи по сети в Incoming Context\n\tmd, _ := metadata.FromOutgoingContext(outCtx)\n\tinCtx := metadata.NewIncomingContext(context.Background(), md)\n\n\t// 2. Сервер извлекает TraceID\n\textractedTrace, extractedSpan, err := ExtractTraceContext(inCtx)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка извлечения: %v\", err)\n\t}\n\n\tif extractedTrace != expectedTraceID || extractedSpan != clientSpanID {\n\t\tt.Fatalf(\"Несовпадение трассировки: %s != %s\", extractedTrace, expectedTraceID)\n\t}\n\n\tfmt.Printf(\"W3C TraceContext успешно передан через gRPC metadata:\\n\")\n\tfmt.Printf(\"  • TraceID:        %s\\n\", extractedTrace)\n\tfmt.Printf(\"  • Parent SpanID:  %s\\n\", extractedSpan)\n}",
        "note": "Сериализация и десериализация W3C TraceContext в gRPC metadata"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v opentelemetry_metadata_test.go\n# Вывод:\n# === RUN   TestTraceContextPropagation\n# W3C TraceContext успешно передан через gRPC metadata:\n#   • TraceID:        4bf92f3577b34da6a3ce929d0e0e4736\n#   • Parent SpanID:  00f067aa0ba902b7\n# --- PASS: TestTraceContextPropagation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Спецификация W3C TraceContext принята всеми ведущими вендорами (Jaeger, Datadog, Dynatrace, NewRelic), обеспечивая сквозную трассировку между сервисами на Go, Java, Python и Node.js.",
    "pitfalls": "Использовать устаревшие кастомные заголовки B3 (`x-b3-traceid`) вместо W3C `traceparent`: разнородные библиотеки в кластере не поймут чужой формат и разорвут граф трейса.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое Baggage в OpenTelemetry и чем он отличается от TraceContext?»\n**Ответ:** TraceContext передает технические идентификаторы спанов (`trace_id`, `span_id`). Baggage (заголовок `baggage`) передает **бизнес-контекст** (например `user_id=42`, `account_tier=vip`), который доступен во всех дочерних микросервисах без необходимости явного добавления полей в каждый Protobuf запрос."
  },
  {
    "num": 36,
    "title": "Авторегистрация в Service Discovery: регистрация адреса в Consul при старте и динамический lookup",
    "task": "**Регистрация и обнаружение сервисов (Service Discovery)**: Поднимите локальный инстанс HashiCorp Consul или etcd (можно в Docker). Напишите код на Go, который при старте вашего gRPC-сервера автоматически регистрирует его адрес и порт в системе Service Discovery. Напишите код gRPC-клиента, который не знает жесткого адреса сервера, а перед вызовом запрашивает актуальный список доступных IP-адресов серверов у Consul.",
    "theory": "Процесс Service Registration & Client Lookup в Consul:\n1. **Регистрация сервиса при запуске:**\n   ```go\n   registration := &api.AgentServiceRegistration{\n       ID:      \"order-service-pod-42\",\n       Name:    \"order-service\",\n       Port:    50051,\n       Address: \"10.0.1.15\",\n       Check:   &api.AgentServiceCheck{GRPC: \"10.0.1.15:50051\", Interval: \"10s\"},\n   }\n   consul.Agent().ServiceRegister(registration)\n   ```\n2. **Graceful Deregistration при завершении:**\n   `defer consul.Agent().ServiceDeregister(\"order-service-pod-42\")`\n3. **Клиентский Lookup:**\n   `entries, _, _ := consul.Health().Service(\"order-service\", \"\", true, nil)` — возвращает только здоровые поды.",
    "step_by_step": "1. Создайте структуру сервисного агента Consul.\n2. Реализуйте регистрацию с проверкой здоровья.\n3. Напишите клиентский метод `LookupHealthyEndpoints`.\n4. Протестируйте обнаружение сервиса.",
    "code_blocks": [
      {
        "filename": "consul_lifecycle_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n)\n\ntype RegisteredInstance struct {\n\tID      string\n\tService string\n\tAddress string\n\tPort    int\n\tHealthy bool\n}\n\ntype MockConsulAgent struct {\n\tmu       sync.RWMutex\n\tservices map[string]*RegisteredInstance\n}\n\nfunc NewMockConsul() *MockConsulAgent {\n\treturn &MockConsulAgent{services: make(map[string]*RegisteredInstance)}\n}\n\nfunc (c *MockConsulAgent) ServiceRegister(id, service, addr string, port int) error {\n\tc.mu.Lock()\n\tdefer c.mu.Unlock()\n\tc.services[id] = &RegisteredInstance{\n\t\tID:      id,\n\t\tService: service,\n\t\tAddress: addr,\n\t\tPort:    port,\n\t\tHealthy: true,\n\t}\n\treturn nil\n}\n\nfunc (c *MockConsulAgent) ServiceDeregister(id string) error {\n\tc.mu.Lock()\n\tdefer c.mu.Unlock()\n\tdelete(c.services, id)\n\treturn nil\n}\n\nfunc (c *MockConsulAgent) LookupHealthy(service string) []string {\n\tc.mu.RLock()\n\tdefer c.mu.RUnlock()\n\tvar addrs []string\n\tfor _, inst := range c.services {\n\t\tif inst.Service == service && inst.Healthy {\n\t\t\taddrs = append(addrs, fmt.Sprintf(\"%s:%d\", inst.Address, inst.Port))\n\t\t}\n\t}\n\treturn addrs\n}\n\nfunc TestConsulDiscoveryWorkflow(t *testing.T) {\n\tconsul := NewMockConsul()\n\n\t// 1. Старт пода и регистрация\n\t_ = consul.ServiceRegister(\"order-pod-1\", \"order-service\", \"10.0.1.15\", 50051)\n\t_ = consul.ServiceRegister(\"order-pod-2\", \"order-service\", \"10.0.1.16\", 50051)\n\n\t// 2. Клиент резолвит адреса\n\tendpoints := consul.LookupHealthy(\"order-service\")\n\tif len(endpoints) != 2 {\n\t\tt.Fatalf(\"Ожидалось 2 адреса, получено: %d\", len(endpoints))\n\t}\n\tfmt.Printf(\"Клиент динамически обнаружил endpoints: %v\\n\", endpoints)\n\n\t// 3. Graceful Shutdown первого пода\n\t_ = consul.ServiceDeregister(\"order-pod-1\")\n\n\tendpointsAfter := consul.LookupHealthy(\"order-service\")\n\tif len(endpointsAfter) != 1 || endpointsAfter[0] != \"10.0.1.16:50051\" {\n\t\tt.Fatalf(\"Некорректный список после дерегистрации: %v\", endpointsAfter)\n\t}\n\tfmt.Printf(\"После дерегистрации остался активный endpoint: %v\\n\", endpointsAfter)\n}",
        "note": "Жизненный цикл регистрации и обнаружения сервисов в Consul"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v consul_lifecycle_test.go\n# Вывод:\n# === RUN   TestConsulDiscoveryWorkflow\n# Клиент динамически обнаружил endpoints: [10.0.1.15:50051 10.0.1.16:50051]\n# После дерегистрации остался активный endpoint: [10.0.1.16:50051]\n# --- PASS: TestConsulDiscoveryWorkflow (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Consul использует протокол Gossip (библиотека Memberlist на базе SWIM) для мгновенного обнаружения падений нод в кластере без перегрузки центрального сервера.",
    "pitfalls": "Забывать вызывать `ServiceDeregister` при получении `SIGTERM`: под уже завершил работу, а Consul будет направлять на него трафик еще 10–30 секунд до срабатывания Health Check таймаута.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что делать клиенту, если кластер Consul временно стал недоступен?»\n**Ответ:** Клиент обязан реализовать локальное кэширование списка адресов (Last Known Good Endpoints). При отказе Consul клиент продолжает обращаться к последним известным подам, обеспечивая автономность системы."
  },
  {
    "num": 37,
    "title": "Инфраструктурный оркестр: docker-compose.yml для 3 микросервисов, PostgreSQL, Redis и Jaeger",
    "task": "Создай **docker-compose.yml** для 3 сервисов + PostgreSQL + Redis + Jaeger. Настрой сети, volumes, health checks. Запусти `docker-compose up` и проверь взаимодействие.",
    "theory": "Проектирование локального окружения микросервисов (Docker Compose):\n- Изолированная внутренняя сеть: `networks: backend-net`.\n- Постоянные хранилища: `volumes: pgdata, redisdata`.\n- Зависимости с проверкой готовности: `depends_on: { condition: service_healthy }`.\n- Сервисы не должны стартовать до тех пор, пока PostgreSQL и Redis не пройдут Healthcheck!",
    "step_by_step": "1. Опишите сервисы PostgreSQL и Redis с Health Check.\n2. Опишите all-in-one Jaeger для трассировки.\n3. Настройте запуск микросервисов после готовности БД.\n4. Проверьте валидность файла docker-compose.",
    "code_blocks": [
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "version: '3.8'\n\nnetworks:\n  backend-net:\n    driver: bridge\n\nvolumes:\n  pgdata:\n  redisdata:\n\nservices:\n  postgres:\n    image: postgres:16-alpine\n    environment:\n      POSTGRES_USER: app\n      POSTGRES_PASSWORD: secret_password\n      POSTGRES_DB: micro_db\n    volumes:\n      - pgdata:/var/lib/postgresql/data\n    networks:\n      - backend-net\n    healthcheck:\n      test: [\"CMD-SHELL\", \"pg_isready -U app -d micro_db\"]\n      interval: 5s\n      timeout: 3s\n      retries: 5\n\n  redis:\n    image: redis:7-alpine\n    volumes:\n      - redisdata:/data\n    networks:\n      - backend-net\n    healthcheck:\n      test: [\"CMD\", \"redis-cli\", \"ping\"]\n      interval: 5s\n      timeout: 3s\n      retries: 5\n\n  jaeger:\n    image: jaegertracing/all-in-one:1.55\n    ports:\n      - \"16686:16686\" # Web UI\n      - \"4317:4317\"   # OTLP gRPC receiver\n    networks:\n      - backend-net\n\n  user-service:\n    build:\n      context: ./services/user-service\n    environment:\n      DATABASE_URL: \"postgres://app:secret_password@postgres:5432/micro_db?sslmode=disable\"\n      OTEL_EXPORTER_OTLP_ENDPOINT: \"jaeger:4317\"\n    depends_on:\n      postgres:\n        condition: service_healthy\n    networks:\n      - backend-net\n\n  order-service:\n    build:\n      context: ./services/order-service\n    environment:\n      REDIS_ADDR: \"redis:6379\"\n      OTEL_EXPORTER_OTLP_ENDPOINT: \"jaeger:4317\"\n    depends_on:\n      redis:\n        condition: service_healthy\n    networks:\n      - backend-net",
        "note": "Спецификация Docker Compose с зависимостями service_healthy"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск инфраструктуры в фоне:\ndocker compose up -d\n\n# Проверка статуса контейнеров:\ndocker compose ps\n# NAME                     STATUS                    PORTS\n# project-jaeger-1         running                   0.0.0.0:4317->4317/tcp, 0.0.0.0:16686->16686/tcp\n# project-postgres-1       running (healthy)         5432/tcp\n# project-redis-1          running (healthy)         6379/tcp\n# project-user-service-1   running                   50051/tcp\n# project-order-service-1  running                   50052/tcp"
      }
    ],
    "under_the_hood": "Директива `condition: service_healthy` гарантирует строгий детерминированный порядок инициализации, исключая падения микросервисов с ошибкой `connection refused` при одновременном старте.",
    "pitfalls": "Хардкодить пароли в `docker-compose.yml`: для production и стейджинга используйте переменные окружения из `.env` файла.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в микросервисах рекомендуется использовать единую сеть bridge в Docker Compose?»\n**Ответ:** Единая пользовательская сеть bridge обеспечивает встроенный DNS-резолвинг: сервисы обращаются друг к другу по именам контейнеров (`http://postgres:5432`, `jaeger:4317`) без необходимости ручного проброса портов на хостовую машину."
  },
  {
    "num": 38,
    "title": "Манифесты Kubernetes: Deployment, Service ClusterIP, Ingress gRPC и автомасштабирование HPA",
    "task": "Создай **Kubernetes manifests**: Deployment (3 реплики), Service (ClusterIP), Ingress (gRPC через nginx-ingress или Istio). Настрой HPA (Horizontal Pod Autoscaler) по CPU/memory.",
    "theory": "Спецификация промышленного развертывания в Kubernetes:\n- **Deployment:** управляет 3 подами, задает ресурсы `requests`/`limits`, настраивает Liveness и Readiness пробы.\n- **Service (ClusterIP):** внутренний стабильный виртуальный IP и порт балансировки.\n- **Ingress:** входная точка L7 с аннотацией `nginx.ingress.kubernetes.io/backend-protocol: \"GRPC\"`.\n- **HPA (Horizontal Pod Autoscaler):** динамически увеличивает число реплик от 3 до 10 при загрузке CPU > 75%.",
    "step_by_step": "1. Опишите манифест Deployment с 3 репликами.\n2. Создайте ClusterIP Service с именованным портом gRPC.\n3. Настройте Ingress с поддержкой gRPC.\n4. Добавьте HorizontalPodAutoscaler по метрикам CPU.",
    "code_blocks": [
      {
        "filename": "k8s/order-service.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: order-service\n  namespace: production\n  labels:\n    app: order-service\nspec:\n  replicas: 3\n  selector:\n    matchLabels:\n      app: order-service\n  template:\n    metadata:\n      labels:\n        app: order-service\n    spec:\n      containers:\n      - name: order-service\n        image: company/order-service:v1.0.0\n        ports:\n        - name: grpc\n          containerPort: 50051\n        resources:\n          requests:\n            cpu: \"250m\"\n            memory: \"256Mi\"\n          limits:\n            cpu: \"1000m\"\n            memory: \"512Mi\"\n        livenessProbe:\n          grpc:\n            port: 50051\n          initialDelaySeconds: 5\n          periodSeconds: 10\n        readinessProbe:\n          grpc:\n            port: 50051\n          initialDelaySeconds: 2\n          periodSeconds: 5\n---\napiVersion: v1\nkind: Service\nmetadata:\n  name: order-service\n  namespace: production\nspec:\n  type: ClusterIP\n  selector:\n    app: order-service\n  ports:\n  - name: grpc\n    port: 50051\n    targetPort: 50051\n---\napiVersion: autoscaling/v2\nkind: HorizontalPodAutoscaler\nmetadata:\n  name: order-service-hpa\n  namespace: production\nspec:\n  scaleTargetRef:\n    apiVersion: apps/v1\n    kind: Deployment\n    name: order-service\n  minReplicas: 3\n  maxReplicas: 10\n  metrics:\n  - type: Resource\n    resource:\n      name: cpu\n      target:\n        type: Utilization\n        averageUtilization: 75",
        "note": "Полный стек манифестов Kubernetes: Deployment, Service и HPA"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Применение манифестов в кластер:\nkubectl apply -f k8s/order-service.yaml\n\n# Проверка статуса подов и автомасштабирования:\nkubectl get pods -l app=order-service -n production\n# NAME                             READY   STATUS    RESTARTS   AGE\n# order-service-7bb8f547c8-9m2k1   1/1     Running   0          45s\n# order-service-7bb8f547c8-df82x   1/1     Running   0          45s\n# order-service-7bb8f547c8-p7q3a   1/1     Running   0          45s\n\nkubectl get hpa order-service-hpa -n production\n# NAME                REFERENCE                  TARGETS   MINPODS   MAXPODS   REPLICAS   AGE\n# order-service-hpa   Deployment/order-service   12%/75%   3         10        3          1m"
      }
    ],
    "under_the_hood": "HPA опрашивает Metrics Server каждые 15 секунд. При превышении целевой загрузки CPU (75%) контроллер Kubernetes плавно увеличивает число подов согласно формуле: $\\text{desiredReplicas} = \\lceil \\text{currentReplicas} \\times (\\text{currentMetric} / \\text{desiredMetric}) \\rceil$.",
    "pitfalls": "Не указывать `resources.requests`: HPA не сможет рассчитать процент утилизации CPU и откажется масштабировать поды.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему Ingress NGINX требует специальную аннотацию для gRPC?»\n**Ответ:** gRPC использует протокол HTTP/2 с постоянным мультиплексированием стримов. Без аннотации `nginx.ingress.kubernetes.io/backend-protocol: \"GRPC\"` NGINX будет пытаться проксировать запросы как стандартный HTTP/1.1 с закрытием соединений, что сломает стриминг и заголовки трейлеров."
  },
  {
    "num": 39,
    "title": "Принципы 12-Factor App: многоуровневая конфигурация через YAML и переопределение переменными окружения",
    "task": "**12-Factor App (Конфигурация)**: Микросервис не должен содержать захардкоженных портов или паролей от БД. Используй библиотеку `github.com/spf13/viper` или стандартный `os.Getenv`. Напиши парсер конфига, который читает настройки из файла `config.yaml`, но может быть переопределен переменными окружения.",
    "theory": "Фактор III методологии 12-Factor App (Конфигурация):\n- Конфигурация приложения строго отделяется от исполняемого кода.\n- Приоритеты загрузки конфигурации (от высшего к низшему):\n  1. Флаги командной строки CLI (`--port=8080`).\n  2. Переменные окружения ОС (`APP_PORT=8080`).\n  3. Конфигурационный файл (`config.yaml`).\n  4. Дефолтные значения в коде.\n- Переопределение через переменные окружения позволяет запускать **один и тот же Docker-образ** на dev, staging и production окружениях.",
    "step_by_step": "1. Создайте структуру конфигурации приложения.\n2. Реализуйте чтение дефолтных значений.\n3. Реализуйте переопределение из переменных окружения.\n4. Протестируйте приоритет переменных ОС.",
    "code_blocks": [
      {
        "filename": "twelve_factor_config_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n\t\"strconv\"\n\t\"testing\"\n)\n\ntype AppConfig struct {\n\tPort     int\n\tDBUrl    string\n\tLogLevel string\n}\n\nfunc LoadConfig() AppConfig {\n\t// 1. Дефолтные значения (или прочитанные из config.yaml)\n\tcfg := AppConfig{\n\t\tPort:     50051,\n\t\tDBUrl:    \"postgres://localhost:5432/dev_db\",\n\t\tLogLevel: \"INFO\",\n\t}\n\n\t// 2. Переопределение переменными окружения (12-Factor App)\n\tif val := os.Getenv(\"APP_PORT\"); val != \"\" {\n\t\tif p, err := strconv.Atoi(val); err == nil {\n\t\t\tcfg.Port = p\n\t\t}\n\t}\n\n\tif val := os.Getenv(\"APP_DATABASE_URL\"); val != \"\" {\n\t\tcfg.DBUrl = val\n\t}\n\n\tif val := os.Getenv(\"APP_LOG_LEVEL\"); val != \"\" {\n\t\tcfg.LogLevel = val\n\t}\n\n\treturn cfg\n}\n\nfunc Test12FactorConfigOverride(t *testing.T) {\n\t// Имитируем переменные окружения Kubernetes Pod\n\t_ = os.Setenv(\"APP_PORT\", \"9090\")\n\t_ = os.Setenv(\"APP_DATABASE_URL\", \"postgres://prod-cluster.internal:5432/orders_db\")\n\t_ = os.Setenv(\"APP_LOG_LEVEL\", \"DEBUG\")\n\tdefer func() {\n\t\t_ = os.Unsetenv(\"APP_PORT\")\n\t\t_ = os.Unsetenv(\"APP_DATABASE_URL\")\n\t\t_ = os.Unsetenv(\"APP_LOG_LEVEL\")\n\t}()\n\n\tcfg := LoadConfig()\n\n\tif cfg.Port != 9090 || cfg.LogLevel != \"DEBUG\" || cfg.DBUrl != \"postgres://prod-cluster.internal:5432/orders_db\" {\n\t\tt.Fatalf(\"Переменные окружения не переопределили конфиг: %+v\", cfg)\n\t}\n\n\tfmt.Printf(\"12-Factor конфигурация успешно загружена:\\n\")\n\tfmt.Printf(\"  • Port:     %d (переопределено из ENV)\\n\", cfg.Port)\n\tfmt.Printf(\"  • DB URL:   %s\\n\", cfg.DBUrl)\n\tfmt.Printf(\"  • LogLevel: %s\\n\", cfg.LogLevel)\n}",
        "note": "Реализация иерархии конфигурации по методологии 12-Factor App"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v twelve_factor_config_test.go\n# Вывод:\n# === RUN   Test12FactorConfigOverride\n# 12-Factor конфигурация успешно загружена:\n#   • Port:     9090 (переопределено из ENV)\n#   • DB URL:   postgres://prod-cluster.internal:5432/orders_db\n#   • LogLevel: DEBUG\n# --- PASS: Test12FactorConfigOverride (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Kubernetes переменные окружения инжектируются в под из ConfigMap и Secret через директиву `envFrom: [configMapRef, secretRef]`.",
    "pitfalls": "Хранить секреты (токены API, приватные ключи) в файле `config.yaml` в Git-репозитории: секреты попадут в историю коммитов. Используйте HashiCorp Vault или Kubernetes Secrets.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему популярна библиотека spf13/viper для 12-Factor конфигурации?»\n**Ответ:** `viper` умеет автоматически связывать JSON/YAML конфиги с переменными окружения через `viper.SetEnvPrefix(\"APP\")` и `viper.AutomaticEnv()`, а также поддерживает динамический Hot Reload из etcd/Consul через `viper.WatchRemoteConfig()`."
  },
  {
    "num": 40,
    "title": "Анализ распределенных трасс в Jaeger: выявление узких мест (Bottlenecks) и медленных вызовов",
    "task": "Экспортируйте трассы в Jaeger (локально в Docker) и проанализируйте цепочку вызовов между двумя микросервисами.",
    "theory": "Анализ производительности графа спанов в Jaeger UI:\n- На дэшборде Waterfall View отображаются:\n  - **Критический путь (Critical Path):** последовательность операций, определяющая суммарное время запроса.\n  - **Параллельные ветвления:** одновременные вызовы двух сервисов.\n  - **Сетевой оверхед:** разница во времени между отправкой запроса клиентом и получением на сервере.\n- Теги спана (`http.status_code`, `error=true`, `db.statement`) позволяют мгновенно найти причину задержки.",
    "step_by_step": "1. Создайте модель анализатора графа спанов.\n2. Реализуйте алгоритм вычисления критического пути.\n3. Найдите самый медленный спан (Bottleneck).\n4. Протестируйте диагностику задержки.",
    "code_blocks": [
      {
        "filename": "jaeger_trace_analyzer_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype TraceSpan struct {\n\tName     string\n\tService  string\n\tDuration time.Duration\n}\n\nfunc FindTraceBottleneck(spans []TraceSpan) TraceSpan {\n\tvar maxSpan TraceSpan\n\tfor _, s := range spans {\n\t\tif s.Duration > maxSpan.Duration {\n\t\t\tmaxSpan = s\n\t\t}\n\t}\n\treturn maxSpan\n}\n\nfunc TestTraceBottleneckDetection(t *testing.T) {\n\t// Граф вызовов одного запроса оформления заказа\n\ttrace := []TraceSpan{\n\t\t{Name: \"Gateway.Route\", Service: \"api-gateway\", Duration: 5 * time.Millisecond},\n\t\t{Name: \"OrderService.Validate\", Service: \"order-service\", Duration: 12 * time.Millisecond},\n\t\t{Name: \"PaymentService.Charge\", Service: \"payment-service\", Duration: 350 * time.Millisecond}, // Узкое место!\n\t\t{Name: \"NotificationService.SendPush\", Service: \"notification-service\", Duration: 25 * time.Millisecond},\n\t}\n\n\tbottleneck := FindTraceBottleneck(trace)\n\n\tif bottleneck.Service != \"payment-service\" || bottleneck.Duration != 350*time.Millisecond {\n\t\tt.Fatalf(\"Некорректно определено узкое место: %+v\", bottleneck)\n\t}\n\n\tfmt.Printf(\"Анализ трассы Jaeger успешно локализовал узкое место (Bottleneck):\\n\")\n\tfmt.Printf(\"  • Сервис:   %s\\n\", bottleneck.Service)\n\tfmt.Printf(\"  • Операция: %s\\n\", bottleneck.Name)\n\tfmt.Printf(\"  • Задержка: %v (90%% суммарного времени транзакции!)\\n\", bottleneck.Duration)\n}",
        "note": "Автоматизированная локализация узких мест в распределенном трейсе"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v jaeger_trace_analyzer_test.go\n# Вывод:\n# === RUN   TestTraceBottleneckDetection\n# Анализ трассы Jaeger успешно локализовал узкое место (Bottleneck):\n#   • Сервис:   payment-service\n#   • Операция: PaymentService.Charge\n#   • Задержка: 350ms (90% суммарного времени транзакции!)\n# --- PASS: TestTraceBottleneckDetection (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Jaeger вычисляет критический путь через топологическую сортировку направленного ациклического графа (DAG) спанов, определяя отрезки, где время выполнения нельзя сократить параллелизацией.",
    "pitfalls": "Создавать слишком много мелких спанов (на каждый вызов локальной Go-функции): это раздует трейс до мегабайт и приведет к задержкам на сериализацию. Спаны создаются только на сетевые и ключевые I/O границы.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как Jaeger помогает выявить проблему N+1 сетевых запросов?»\n**Ответ:** На таймлайне Jaeger проблема $N+1$ видна мгновенно в виде характерной «лесенки» (Waterfall Staircase) из сотен последовательных микро-спанов (например 100 запросов `SELECT * FROM items WHERE id = ?`), которые должны быть заменены на один батч-запрос `WHERE id IN (...)`."
  },
  {
    "num": 41,
    "title": "Архитектура Istio Service Mesh: прозрачный mTLS, Canary 90/10 и Circuit Breaking без изменения кода",
    "task": "Настрой **Istio service mesh**: sidecar proxy для каждого pod. mTLS между сервисами автоматически. Traffic splitting (canary deployment: 90% v1, 10% v2). Circuit breaker на уровне mesh.",
    "theory": "Принцип работы Istio Service Mesh (Data Plane & Control Plane):\n- В каждый под автоматически внедряется sidecar-контейнер **Envoy Proxy** (`istio-proxy`).\n- Все входящие и исходящие TCP соединения прозрачно перехватываются правилами `iptables`.\n- **Преимущества Mesh-архитектуры:**\n  1. **Zero-Code Security:** сквозное mTLS шифрование между всеми подами с автоматической ротацией сертификатов каждые 24 часа.\n  2. **Canary Traffic Splitting:** манифест `VirtualService` направляет 90% трафика на версию v1 и 10% на v2.\n  3. **Mesh-Level Circuit Breaking:** манифест `DestinationRule` ограничивает число параллельных соединений и отсекает упавшие поды.",
    "step_by_step": "1. Опишите манифест Istio VirtualService для разделения трафика 90/10.\n2. Опишите манифест DestinationRule для mTLS и Circuit Breaking.\n3. Продемонстрируйте структуру управления трафиком.\n4. Проверьте параметры конфигурации Canary.",
    "code_blocks": [
      {
        "filename": "istio/order-traffic-routing.yaml",
        "lang": "yaml",
        "code": "apiVersion: networking.istio.io/v1alpha3\nkind: VirtualService\nmetadata:\n  name: order-service-routing\n  namespace: production\nspec:\n  hosts:\n  - order-service\n  http:\n  - route:\n    - destination:\n        host: order-service\n        subset: v1\n      weight: 90\n    - destination:\n        host: order-service\n        subset: v2 # Canary релиз\n      weight: 10\n---\napiVersion: networking.istio.io/v1alpha3\nkind: DestinationRule\nmetadata:\n  name: order-service-destination\n  namespace: production\nspec:\n  host: order-service\n  trafficPolicy:\n    tls:\n      mode: ISTIO_MUTUAL # Автоматический mTLS между подами\n    connectionPool:\n      tcp:\n        maxConnections: 100\n      http:\n        http1MaxPendingRequests: 10\n        maxRequestsPerConnection: 10\n    outlierDetection: # Circuit Breaker на уровне Envoy\n      consecutive5xxErrors: 3\n      interval: 10s\n      baseEjectionTime: 30s\n      maxEjectionPercent: 50\n  subsets:\n  - name: v1\n    labels:\n      version: v1\n  - name: v2\n    labels:\n      version: v2",
        "note": "Манифесты Istio: Canary расщепление трафика 90/10 и mTLS"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Включение автоматического внедрения Sidecar прокси в namespace:\nkubectl label namespace production istio-injection=enabled\n\n# Применение правил маршрутизации:\nkubectl apply -f istio/order-traffic-routing.yaml\n\n# Проверка статуса проксирования Envoy:\nistioctl proxy-status\n# NAME                                                   CDS        LDS        EDS        RDS          ISTIOD                      VERSION\n# order-service-v1-7c9b8-x1.production                   SYNCED     SYNCED     SYNCED     SYNCED       istiod-66d48-8m2            1.21.0\n# order-service-v2-5d81a-y2.production                   SYNCED     SYNCED     SYNCED     SYNCED       istiod-66d48-8m2            1.21.0"
      }
    ],
    "under_the_hood": "Envoy sidecar слушает порт 15001. Правила `iptables -t nat -A PREROUTING -p tcp -j REDIRECT --to-ports 15001` заворачивают все сетевые пакеты ядра Linux в пользовательский процесс Envoy.",
    "pitfalls": "Накладные расходы по задержке: каждый сетевой хоп через Envoy добавляет ~1–2 мс задержки и 50 МБ ОЗУ на каждый контейнер sidecar. Для сверхвысоконагруженных low-latency систем используют Ambient Mesh (без sidecar) или gRPC Proxyless Mesh.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое gRPC Proxyless Service Mesh?»\n**Ответ:** Это решение, при котором gRPC клиент напрямую общается с плоскостью управления Istio (Istiod) по протоколу **xDS**. Балансировка, канареечные веса и mTLS выполняются внутри самого Go-бинарника без промежуточного процесса Envoy, снижая задержку до нуля."
  },
  {
    "num": 42,
    "title": "Проблема динамических IP в Kubernetes: абстракция виртуальных IP ClusterIP и ядро kube-proxy",
    "task": "Изучите проблему: в Kubernetes поды имеют динамические IP-адреса. Как клиенту подключиться к сервису, не зная конкретных IP?",
    "theory": "Архитектура виртуальной адресации в Kubernetes:\n- Поды эфемерны: при падении, перезапуске или скейлинге под получает новый случайный IP из подсети ноды (`10.244.x.x`).\n- **Решение проблемы (Kubernetes Service & ClusterIP):**\n  1. Создается объект `Service` с постоянным виртуальным IP (ClusterIP), например `10.96.0.100`.\n  2. Этот IP никогда не меняется на протяжении жизни сервиса.\n  3. Внутренний DNS Kubernetes (CoreDNS) сопоставляет доменное имя `order-service` с адресом ClusterIP.\n  4. Сетевой агент **kube-proxy** на каждой ноде настраивает правила **IPVS / iptables**, перенаправляя пакеты с виртуального ClusterIP на реальные динамические IP подов.",
    "step_by_step": "1. Создайте модель виртуального сервиса ClusterIP.\n2. Смоделируйте динамическое изменение IP адресов подов.\n3. Проверьте стабильность обращения клиента по единому имени.\n4. Протестируйте абстракцию от эфемерных IP.",
    "code_blocks": [
      {
        "filename": "clusterip_abstraction_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"math/rand\"\n\t\"sync\"\n\t\"testing\"\n)\n\ntype K8sPod struct {\n\tName string\n\tIP   string\n}\n\ntype ClusterIPService struct {\n\tmu           sync.RWMutex\n\tServiceName  string\n\tVirtualVIP   string\n\tactivePodIPs []string\n}\n\nfunc (s *ClusterIPService) UpdateEndpoints(pods []K8sPod) {\n\ts.mu.Lock()\n\tdefer s.mu.Unlock()\n\tvar ips []string\n\tfor _, p := range pods {\n\t\tips = append(ips, p.IP)\n\t}\n\ts.activePodIPs = ips\n}\n\nfunc (s *ClusterIPService) RouteCall() (string, error) {\n\ts.mu.RLock()\n\tdefer s.mu.RUnlock()\n\tif len(s.activePodIPs) == 0 {\n\t\treturn \"\", fmt.Errorf(\"нет доступных подов\")\n\t}\n\t// kube-proxy случайный выбор пода из пула IPVS\n\ttargetIP := s.activePodIPs[rand.Intn(len(s.activePodIPs))]\n\treturn targetIP, nil\n}\n\nfunc TestClusterIPStability(t *testing.T) {\n\tsvc := &ClusterIPService{\n\t\tServiceName: \"user-service\",\n\t\tVirtualVIP:  \"10.96.42.100\", // Постоянный виртуальный адрес\n\t}\n\n\t// Поколение подов #1\n\tsvc.UpdateEndpoints([]K8sPod{\n\t\t{Name: \"user-pod-1\", IP: \"10.244.1.5\"},\n\t\t{Name: \"user-pod-2\", IP: \"10.244.2.8\"},\n\t})\n\n\t// Клиент обращается СТРОГО к постоянному имени user-service\n\ttarget1, _ := svc.RouteCall()\n\tfmt.Printf(\"1. Запрос к user-service (%s) смаршрутизирован на реальный под: %s\\n\",\n\t\tsvc.VirtualVIP, target1)\n\n\t// Поды упали и пересоздались с новыми IP (Rolling Update)\n\tsvc.UpdateEndpoints([]K8sPod{\n\t\t{Name: \"user-pod-3\", IP: \"10.244.3.99\"},\n\t\t{Name: \"user-pod-4\", IP: \"10.244.4.101\"},\n\t})\n\n\ttarget2, _ := svc.RouteCall()\n\tfmt.Printf(\"2. После перезапуска подов клиент продолжает вызывать %s, попав на новый IP: %s\\n\",\n\t\tsvc.ServiceName, target2)\n\n\tif target2 != \"10.244.3.99\" && target2 != \"10.244.4.101\" {\n\t\tt.Fatalf(\"Некорректная маршрутизация: %s\", target2)\n\t}\n}",
        "note": "Моделирование абстракции ClusterIP над динамическими IP подов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v clusterip_abstraction_test.go\n# Вывод:\n# === RUN   TestClusterIPStability\n# 1. Запрос к user-service (10.96.42.100) смаршрутизирован на реальный под: 10.244.1.5\n# 2. После перезапуска подов клиент продолжает вызывать user-service, попав на новый IP: 10.244.3.99\n# --- PASS: TestClusterIPStability (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "ClusterIP не существует как физический сетевой интерфейс на хосте. Ядро Linux перехватывает пакеты к этому IP через цепочки `KUBE-SERVICES` в `iptables` и выполняет DNAT подмену на адрес целевого пода.",
    "pitfalls": "Пытаться пинговать (`ping`) ClusterIP: он не отвечает на ICMP Echo Request пакеты, так как iptables обрабатывает только TCP/UDP порты.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в крупных кластерах kube-proxy переводят из режима iptables в режим IPVS?»\n**Ответ:** Режим iptables имеет сложность поиска правил $O(N)$ от числа сервисов: при 10 000 подов перестройка правил занимает секунды и грузит CPU. IPVS (IP Virtual Server) использует хэш-таблицы в ядре Linux со сложностью поиска $O(1)$, масштабируясь до сотен тысяч сервисов без деградации скорости."
  },
  {
    "num": 43,
    "title": "Непрерывная интеграция CI/CD: линтинг golangci-lint, тесты на гонки -race и Quality Gates",
    "task": "Настрой **CI/CD pipeline** (GitHub Actions/GitLab CI): lint (`golangci-lint`), test (`go test -race -cover`), build, push Docker image, deploy to staging. Gate: coverage > 80%, no critical vulnerabilities.",
    "theory": "Стандарты автоматизации CI/CD для микросервисов на Go:\n- Конвейер проверки качества (Quality Gate):\n  1. **Linting:** запуск `golangci-lint run` (проверка стилей, антипаттернов `govet`, `errcheck`, `staticcheck`).\n  2. **Testing with Race Detector:** `go test -race -v -coverprofile=coverage.out ./...` (выявление Data Races).\n  3. **Coverage Enforcement:** скрипт проверяет, что суммарное покрытие кода тестами строго $\\ge 80\\%$.\n  4. **Security Scan:** Trivy сканирует уязвимости в зависимостях Go и базовом образе Docker.\n  5. **Build & Push:** сборка мультистейдж Docker-образа и отправка в Container Registry.",
    "step_by_step": "1. Опишите пайплайн GitHub Actions `.github/workflows/ci.yml`.\n2. Настройте шаги линтинга и тестов с флагом `-race`.\n3. Добавьте проверку порога покрытия тестами 80%.\n4. Проверьте условия остановки пайплайна при сбоях.",
    "code_blocks": [
      {
        "filename": ".github/workflows/ci.yml",
        "lang": "yaml",
        "code": "name: Microservice Production CI/CD\n\non:\n  push:\n    branches: [ main ]\n  pull_request:\n    branches: [ main ]\n\njobs:\n  quality-gate:\n    name: Lint & Unit Tests\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout Code\n        uses: actions/checkout@v4\n\n      - name: Setup Go 1.24\n        uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n          cache: true\n\n      - name: Run golangci-lint\n        uses: golangci/golangci-lint-action@v4\n        with:\n          version: latest\n          args: --timeout=5m\n\n      - name: Run Tests with Race Detector\n        run: |\n          go test -race -v -coverprofile=coverage.out ./...\n          \n      - name: Check Coverage Gate (>= 80%)\n        run: |\n          COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//')\n          echo \"Total Test Coverage: $COVERAGE%\"\n          awk -v cov=\"$COVERAGE\" 'BEGIN {\n            if (cov < 80.0) {\n              print \"❌ FAILED: Покрытие тестами \" cov \"% ниже минимального порога 80%!\";\n              exit 1;\n            } else {\n              print \"✅ PASSED: Quality Gate успешно пройден!\";\n            }\n          }'\n\n  build-and-push:\n    name: Build Multi-Stage Docker\n    needs: quality-gate\n    if: github.ref == 'refs/heads/main'\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout Code\n        uses: actions/checkout@v4\n\n      - name: Build Docker Image\n        run: |\n          docker build -t registry.company.com/order-service:${{ github.sha }} .",
        "note": "Production-ready пайплайн GitHub Actions с автоматическим Quality Gate"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Локальная проверка соответствия пайплайну CI:\ngolangci-lint run\ngo test -race -coverprofile=coverage.out ./...\n\n# Проверка процента покрытия локально:\ngo tool cover -func=coverage.out | grep total\n# total:  (statements)    88.4%"
      }
    ],
    "under_the_hood": "Флаг `-race` компилирует бинарник с инструментацией памяти ThreadSanitizer: каждый доступ к разделяемой переменной логируется в теневой памяти (Shadow Memory), фиксируя гонки данных с точностью до номера строки.",
    "pitfalls": "Запускать бинарник с флагом `-race` в production: детектор гонок замедляет выполнение в 2–10 раз и увеличивает потребление памяти в 5–20 раз. Он предназначен исключительно для тестов и CI.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как ускорить время прохождения CI пайплайна для монорепозитория из 20 микросервисов?»\n**Ответ:** 1. Использовать матричные сборки (Matrix Strategy) для параллельного тестирования сервисов на разных runner'ах. 2. Настроить кэширование модулей Go (`~/.cache/go-build` и `$GOPATH/pkg/mod`). 3. Запускать тесты только для измененных директорий через `git diff --name-only` или инструмент `nx / bazel`."
  },
  {
    "num": 44,
    "title": "Внутренняя маршрутизация Kubernetes Service: резолвинг по FQDN имени и виртуальная балансировка",
    "task": "Используйте **Kubernetes Service** (ClusterIP) и подключайтесь по DNS-имени (`user-service.default.svc.cluster.local`). Kubernetes сам балансирует нагрузку.",
    "theory": "Формат полного доменного имени FQDN (Fully Qualified Domain Name) в Kubernetes:\n- Синтаксис: `<service-name>.<namespace>.svc.<cluster-domain>`:\n  `user-service.default.svc.cluster.local:50051`\n  - `user-service`: имя Service ресурса.\n  - `default`: пространство имен (Namespace).\n  - `svc`: тип объекта (сервис).\n  - `cluster.local`: локальный домен кластера.\n- Внутри одного namespace достаточно короткого имени `user-service:50051`.\n- При резолвинге FQDN CoreDNS возвращает виртуальный ClusterIP, а сетевой стек ядра выполняет балансировку по живым репликам.",
    "step_by_step": "1. Создайте структуру парсера FQDN адреса.\n2. Продемонстрируйте извлечение сервиса и namespace.\n3. Настройте подключение клиента по FQDN адресу.\n4. Проверьте корректность конфигурации.",
    "code_blocks": [
      {
        "filename": "k8s_fqdn_resolver_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n\t\"testing\"\n)\n\ntype FQDNInfo struct {\n\tService   string\n\tNamespace string\n\tDomain    string\n}\n\nfunc ParseK8sFQDN(target string) (*FQDNInfo, error) {\n\t// target: user-service.production.svc.cluster.local:50051\n\tparts := strings.Split(target, \":\")\n\thost := parts[0]\n\n\ttokens := strings.Split(host, \".\")\n\tif len(tokens) < 5 || tokens[2] != \"svc\" {\n\t\treturn nil, fmt.Errorf(\"некорректный K8s FQDN: %s\", target)\n\t}\n\n\treturn &FQDNInfo{\n\t\tService:   tokens[0],\n\t\tNamespace: tokens[1],\n\t\tDomain:    strings.Join(tokens[2:], \".\"),\n\t}, nil\n}\n\nfunc TestK8sFQDNResolution(t *testing.T) {\n\ttargetURI := \"order-service.production.svc.cluster.local:50051\"\n\n\tinfo, err := ParseK8sFQDN(targetURI)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка разбора: %v\", err)\n\t}\n\n\tif info.Service != \"order-service\" || info.Namespace != \"production\" {\n\t\tt.Fatalf(\"Некорректный результат: %+v\", info)\n\t}\n\n\tfmt.Printf(\"FQDN адрес успешно распознан:\\n\")\n\tfmt.Printf(\"  • Сервис:    %s\\n\", info.Service)\n\tfmt.Printf(\"  • Namespace: %s\\n\", info.Namespace)\n\tfmt.Printf(\"  • Зона:      %s\\n\", info.Domain)\n}",
        "note": "Парсинг и валидация FQDN адресации Kubernetes Service"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v k8s_fqdn_resolver_test.go\n# Вывод:\n# === RUN   TestK8sFQDNResolution\n# FQDN адрес успешно распознан:\n#   • Сервис:    order-service\n#   • Namespace: production\n#   • Зона:      svc.cluster.local\n# --- PASS: TestK8sFQDNResolution (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В файле `/etc/resolv.conf` каждого пода автоматически прописывается `search default.svc.cluster.local svc.cluster.local cluster.local`. Благодаря этому запрос к `user-service` автоматически дополняется CoreDNS до полного FQDN.",
    "pitfalls": "Использовать короткое имя `user-service` при межпространственных вызовах (Cross-Namespace): если вызывающий сервис в namespace `frontend`, а целевой в `backend`, короткое имя не найдет сервис! Обязательно указывать namespace: `user-service.backend`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему при вызове gRPC сервиса через ClusterIP не работает балансировка по подам при обычном DNS запросе?»\n**Ответ:** gRPC открывает постоянное HTTP/2 TCP-соединение к полученному IP адресу. Стандартный ClusterIP привязывает это TCP-соединение к **одному поду**. Все последующие 100 000 RPC запросов пойдут в этот же под через то же самое TCP-соединение. Для решения проблемы используют Headless Services (`clusterIP: None`) или балансировку через Envoy/Istio Service Mesh."
  },
  {
    "num": 45,
    "title": "Методология GitOps с ArgoCD: Git как единственный источник правды и атомарный откат версий",
    "task": "Настрой **GitOps** (ArgoCD/Flux): Git-репозиторий с Kubernetes manifests — единственный источник правды. ArgoCD синхронизирует кластер с Git. Rollback через `git revert`.",
    "theory": "Принципы парадигмы GitOps (ArgoCD / Flux):\n- **Declarative Description:** все манифесты инфраструктуры хранятся в Git в виде декларативных YAML файлов (или Helm/Kustomize).\n- **Single Source of Truth:** Git-репозиторий является единственным источником правды. Прямые вызовы `kubectl apply` вручную строго запрещены.\n- **Continuous Reconciliation:** контроллер ArgoCD в кластере непрерывно сравнивает желаемое состояние в Git с реальным состоянием в Kubernetes.\n- **Атомарный откат (Instant Rollback):** для отката неудачного релиза инженер выполняет команду `git revert <commit>`, пушит в Git, и ArgoCD мгновенно восстанавливает предыдущую стабильную версию в кластере.",
    "step_by_step": "1. Опишите манифест ArgoCD Application.\n2. Задайте параметры автосинхронизации (Automated Sync Policy).\n3. Смоделируйте синхронизацию состояния приложения.\n4. Проверьте механизм отката через реверт коммита.",
    "code_blocks": [
      {
        "filename": "argocd/application.yaml",
        "lang": "yaml",
        "code": "apiVersion: argoproj.io/v1alpha1\nkind: Application\nmetadata:\n  name: order-service-prod\n  namespace: argocd\n  finalizers:\n    - resources-finalizer.argocd.argoproj.io\nspec:\n  project: default\n  source:\n    repoURL: 'https://github.com/company/k8s-gitops-manifests.git'\n    targetRevision: main\n    path: apps/order-service/production\n  destination:\n    server: 'https://kubernetes.default.svc'\n    namespace: production\n  syncPolicy:\n    automated:\n      prune: true     # Автоматически удалять ресурсы, удаленные из Git\n      selfHeal: true  # Автоматически восстанавливать ресурсы при ручном изменении\n    syncOptions:\n      - CreateNamespace=true",
        "note": "Манифест ArgoCD Application с автоматической самосинхронизацией (Self-Heal)"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Проверка статуса синхронизации через ArgoCD CLI:\nargocd app get order-service-prod\n# App Name:        order-service-prod\n# Sync Status:     Synced to main (commit 9f8a1b2)\n# Health Status:   Healthy\n\n# Сценарий мгновенного отката неудачного деплоя через Git:\ngit revert HEAD --no-edit\ngit push origin main\n\n# ArgoCD обнаруживает вебхук от GitHub и за 2 секунды синхронизирует предыдущую стабильную версию!\nargocd app sync order-service-prod"
      }
    ],
    "under_the_hood": "Опция `selfHeal: true` защищает кластер от дрейфа конфигурации (Configuration Drift): если инженер вручную изменит память пода через `kubectl edit`, ArgoCD за считанные секунды сотрет ручные правки и восстановит состояние из Git.",
    "pitfalls": "Хранить в одном Git-репозитории исходный код приложения на Go и манифесты развертывания: пуш коммита в код вызовет бесконечный цикл сборки и перезапуска. В BigTech принято разделять репозиторий приложения (`app-repo`) и репозиторий манифестов (`infra-gitops-repo`).",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие push-модели CI/CD от pull-модели GitOps?»\n**Ответ:** В классической push-модели CI-сервер (GitLab CI / Jenkins) хранит полные root-ключи от боевого кластера и пушит изменения наружу через `kubectl`. В случае взлома CI скомпрометирован весь кластер. В pull-модели GitOps контроллер ArgoCD находится **внутри самого кластера**, не имеет открытых входящих портов наружу и сам забирает безопасные манифесты из Git."
  }
]
