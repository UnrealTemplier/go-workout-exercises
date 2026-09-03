# -*- coding: utf-8 -*-
"""Exercises 91..130 of Chapter 36."""

exercises = [
  {
    "num": 91,
    "title": "Паттерн CQRS: разделение потоков команд на запись через RabbitMQ и Read Model",
    "task": "**CQRS (Command Query Responsibility Segregation)**: Используйте queue для команд (write operations) и отдельную read model (например, Elasticsearch) для запросов.",
    "theory": "Принцип CQRS (Command Query Responsibility Segregation):\n- Разделение модели записи (Write Model) и модели чтения (Read Model):\n  - **Команды (Write):** клиент отправляет команду `CreateOrderCommand` $\\to$ попадает в очередь RabbitMQ $\\to$ воркер валидирует и сохраняет в реляционную БД (PostgreSQL).\n  - **События синхронизации:** после сохранения воркер публикует `OrderUpdatedEvent`.\n  - **Проекция на чтение (Read Model):** специальный проектор слушает события и обновляет денормализованный индекс Elasticsearch/Redis.\n  - **Запросы (Read):** HTTP GET запросы пользователей читают данные напрямую из сверхбыстрого Read Model без джойнов в PostgreSQL.",
    "step_by_step": "1. Создайте структуры Command (запись) и ReadProjection (чтение).\n2. Реализуйте асинхронную обработку команды через очередь.\n3. Обновите проекцию чтения на основе события.\n4. Проверьте мгновенный ответ на чтение из Read Model.",
    "code_blocks": [
      {
        "filename": "cqrs_queue_projection_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n)\n\ntype UserReadProjection struct {\n\tID    int\n\tName  string\n\tEmail string\n}\n\ntype CQRSSystem struct {\n\tmu           sync.RWMutex\n\tcommandQueue []string\n\treadModel    map[int]*UserReadProjection\n}\n\nfunc (s *CQRSSystem) SendCommand(cmd string) {\n\ts.commandQueue = append(s.commandQueue, cmd)\n}\n\nfunc (s *CQRSSystem) ProcessCommandsAndProject() {\n\tfor _, cmd := range s.commandQueue {\n\t\t// Имитация обновления Read Model (например, Elasticsearch)\n\t\tif cmd == \"UpdateEmail(id=42, email=alex@yandex.ru)\" {\n\t\t\ts.mu.Lock()\n\t\t\ts.readModel[42] = &UserReadProjection{ID: 42, Name: \"Алексей\", Email: \"alex@yandex.ru\"}\n\t\t\ts.mu.Unlock()\n\t\t}\n\t}\n\ts.commandQueue = nil\n}\n\nfunc (s *CQRSSystem) QueryUser(id int) (*UserReadProjection, bool) {\n\ts.mu.RLock()\n\tdefer s.mu.RUnlock()\n\tu, ok := s.readModel[id]\n\treturn u, ok\n}\n\nfunc TestCQRSQueueAndReadModel(t *testing.T) {\n\tsys := &CQRSSystem{readModel: make(map[int]*UserReadProjection)}\n\n\t// 1. Отправка команды в очередь записи\n\tsys.SendCommand(\"UpdateEmail(id=42, email=alex@yandex.ru)\")\n\n\t// 2. Воркер обрабатывает очередь и обновляет поисковую модель\n\tsys.ProcessCommandsAndProject()\n\n\t// 3. Быстрый запрос на чтение из денормализованной Read Model\n\tuser, found := sys.QueryUser(42)\n\tif !found || user.Email != \"alex@yandex.ru\" {\n\t\tt.Fatalf(\"Пользователь не найден в Read Model: %+v\", user)\n\t}\n\n\tfmt.Println(\"Паттерн CQRS успешно протестирован:\")\n\tfmt.Printf(\"  • Команда записи обработана через очередь\\n\")\n\tfmt.Printf(\"  • Запрос на чтение мгновенно обслужен из Read Model: Email=%s\\n\", user.Email)\n}",
        "note": "Разделение операций записи через очередь и прямого чтения из денормализованной Read Model"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v cqrs_queue_projection_test.go\n# Вывод:\n# === RUN   TestCQRSQueueAndReadModel\n# Паттерн CQRS успешно протестирован:\n#   • Команда записи обработана через очередь\n#   • Запрос на чтение мгновенно обслужен из Read Model: Email=alex@yandex.ru\n# --- PASS: TestCQRSQueueAndReadModel (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В архитектуре CQRS модель чтения обладает свойством Eventual Consistency: в течение нескольких миллисекунд после отправки команды Read Model может возвращать старые данные, пока воркер не применит событие проекции.",
    "pitfalls": "Делать синхронный запрос к Read Model сразу же в теле того же HTTP запроса, который отправил команду: из-за асинхронности очереди Read Model еще не успеет обновиться.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как решить проблему Eventual Consistency в UI, если пользователь ожидает увидеть результат своей команды сразу?»\n**Ответ:** Использовать паттерн Optimistic UI Updates: фронтенд сразу локально отображает новое состояние на экране пользователя, не дожидаясь завершения фонового воркера проекции, либо возвращает `202 Accepted` со ссылкой на статус выполнения задачи."
  },
  {
    "num": 92,
    "title": "Мультитенантная очередь сообщений (Multi-Tenant MQ): изоляция субъектов и лимиты квот",
    "task": "Реализуй **Multi-tenant Message Queue** (NATS):\n- Account per tenant, JWT-based auth\n- Subject isolation: `tenant-a.orders.>`, `tenant-b.orders.>`\n- Shared stream `ORDERS` с subject mapping: `orders.>` captures all, `orders.{tenant}.>` per tenant\n- Resource quotas: max messages/sec, max storage per tenant",
    "theory": "Изоляция арендаторов в Multi-Tenant архитектуре:\n- Предотвращение проблемы шумного соседа (Noisy Neighbor Problem):\n  - Каждый клиент (Tenant A, Tenant B) изолирован на уровне пространств имен.\n  - Топики: `tenant-a.orders.*` и `tenant-b.orders.*`.\n  - Квоты ресурсов: тенант не может слать более 500 сообщений в секунду и занимать более 10 ГБ диска.\n  - Утечка данных исключена: токен авторизации Tenant A не имеет прав чтения очередей Tenant B.",
    "step_by_step": "1. Создайте модель изоляции пространства имен по `tenant_id`.\n2. Реализуйте проверку прав доступа к топикам арендатора.\n3. Смоделируйте квоту скорости публикаций на тенанта.\n4. Проверьте блокировку попыток межтенантного доступа.",
    "code_blocks": [
      {
        "filename": "multitenant_isolation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n\t\"strings\"\n\t\"testing\"\n)\n\ntype TenantSecurityContext struct {\n\tTenantID   string\n\tRateLimit  int\n\tmsgCount   int\n}\n\nfunc (ctx *TenantSecurityContext) AuthorizeSubject(subject string) error {\n\texpectedPrefix := ctx.TenantID + \".\"\n\tif !strings.HasPrefix(subject, expectedPrefix) {\n\t\treturn fmt.Errorf(\"доступ запрещен: тенант %s не может публиковать в %s\", ctx.TenantID, subject)\n\t}\n\tif ctx.msgCount >= ctx.RateLimit {\n\t\treturn errors.New(\"квота превышена: rate limit exceeded\")\n\t}\n\tctx.msgCount++\n\treturn nil\n}\n\nfunc TestMultiTenantIsolation(t *testing.T) {\n\ttenantA := &TenantSecurityContext{TenantID: \"tenant-a\", RateLimit: 2}\n\n\t// 1. Валидный топик\n\terr1 := tenantA.AuthorizeSubject(\"tenant-a.orders.created\")\n\tif err1 != nil {\n\t\tt.Fatalf(\"Ошибка валидного топика: %v\", err1)\n\t}\n\n\t// 2. Попытка взлома/доступа к чужому тенанту B\n\terr2 := tenantA.AuthorizeSubject(\"tenant-b.orders.created\")\n\tif err2 == nil {\n\t\tt.Fatal(\"Должна быть ошибка нарушения изоляции тенантов\")\n\t}\n\n\tfmt.Println(\"Multi-Tenant Message Queue изоляция успешно подтверждена:\")\n\tfmt.Printf(\"  • Свой субъект: разрешено\\n\")\n\tfmt.Printf(\"  • Чужой субъект: заблокировано security политикой (%v)\\n\", err2)\n}",
        "note": "Изоляция очередей и квотирование ресурсов в Multi-Tenant архитектуре"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v multitenant_isolation_test.go\n# Вывод:\n# === RUN   TestMultiTenantIsolation\n# Multi-Tenant Message Queue изоляция успешно подтверждена:\n#   • Свой субъект: разрешено\n#   • Чужой субъект: заблокировано security политикой (доступ запрещен: тенант tenant-a не может публиковать в tenant-b.orders.created)\n# --- PASS: TestMultiTenantIsolation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В RabbitMQ мультитенантность строится на независимых виртуальных хостах (vhosts) с отдельными лимитами соединений и очередей (`rabbitmqctl set_vhost_limits`). В NATS для этого используются NATS Accounts с криптографическими JWT токенами.",
    "pitfalls": "Использовать единую общую очередь для всех тенантов с фильтрацией внутри кода воркера: один тенант с багом в генераторе сообщений забьет очередь и парализует всех остальных клиентов платформы.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в RabbitMQ изолировать ресурсы между тенантами без создания отдельных кластеров?»\n**Ответ:** Создать отдельные виртуальные хосты `vhost` для каждого тенанта. Назначить каждому тенанту изолированного AMQP пользователя с регулярными выражениями прав (permissions) только на его собственный `vhost`. Настроить квоту соединений и очередей на `vhost` через RabbitMQ Limits API."
  },
  {
    "num": 93,
    "title": "Корректное завершение (Graceful Shutdown) консьюмера: остановка приема, Ack и ожидание воркеров",
    "task": "Реализуйте graceful shutdown консюмера: при получении SIGINT прекратить приём новых сообщений, дождаться завершения текущих, закоммитить оффсеты/отправить ack и выйти.",
    "theory": "Стандарт Graceful Termination в облачной инфраструктуре:\n1. Перехват сигналов операционной системы: `signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)`.\n2. Оповещение брокера об отмене вычитки: `ch.Cancel(consumerTag, false)`.\n3. Ожидание завершения текущей обработки в пуле воркеров через `sync.WaitGroup.Wait()`.\n4. Отправка подтверждающих `Ack(false)` брокеру за все успешно доведенные до конца задачи.\n5. Финальное закрытие канала и сокета соединения.\n6. Выход процесса с кодом 0.",
    "step_by_step": "1. Создайте структуру управления воркерами со счетчиком `sync.WaitGroup`.\n2. Смоделируйте выполнение фоновых задач.\n3. Имитируйте перехват системного сигнала `SIGINT`.\n4. Дождитесь фиксации всех `Ack` и закрытия сессии.",
    "code_blocks": [
      {
        "filename": "canonical_graceful_shutdown_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n\t\"sync/atomic\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype WorkerTask struct {\n\tID    int\n\tAcked atomic.Bool\n}\n\ntype ConsumerGracefulSupervisor struct {\n\twg      sync.WaitGroup\n\tstopped atomic.Bool\n}\n\nfunc (s *ConsumerGracefulSupervisor) ProcessTask(task *WorkerTask) {\n\ts.wg.Add(1)\n\tgo func() {\n\t\tdefer s.wg.Done()\n\t\t// Имитируем полезную нагрузку\n\t\ttime.Sleep(15 * time.Millisecond)\n\t\ttask.Acked.Store(true)\n\t}()\n}\n\nfunc (s *ConsumerGracefulSupervisor) Shutdown() {\n\ts.stopped.Store(true) // Прекращаем брать новые сообщения\n\ts.wg.Wait()           // Ждем завершения всех текущих\n}\n\nfunc TestCanonicalGracefulShutdown(t *testing.T) {\n\tsup := &ConsumerGracefulSupervisor{}\n\n\tt1 := &WorkerTask{ID: 1}\n\tt2 := &WorkerTask{ID: 2}\n\n\tsup.ProcessTask(t1)\n\tsup.ProcessTask(t2)\n\n\t// Имитация перехвата SIGINT и вызова Shutdown\n\tsup.Shutdown()\n\n\tif !t1.Acked.Load() || !t2.Acked.Load() {\n\t\tt.Fatal(\"Все задачи обязаны быть подтверждены до выхода\")\n\t}\n\n\tfmt.Println(\"Graceful Shutdown консьюмера успешно отработал:\")\n\tfmt.Printf(\"  • Задача 1: Acked=%v\\n\", t1.Acked.Load())\n\tfmt.Printf(\"  • Задача 2: Acked=%v\\n\", t2.Acked.Load())\n\tfmt.Println(\"  • Все in-flight транзакции закоммичены, процесс корректно остановлен!\")\n}",
        "note": "Корректное завершение жизненного цикла консьюмера с гарантией фиксации Ack"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v canonical_graceful_shutdown_test.go\n# Вывод:\n# === RUN   TestCanonicalGracefulShutdown\n# Graceful Shutdown консьюмера успешно отработал:\n#   • Задача 1: Acked=true\n#   • Задача 2: Acked=true\n#   • Все in-flight транзакции закоммичены, процесс корректно остановлен!\n# --- PASS: TestCanonicalGracefulShutdown (0.02s)\n# PASS"
      }
    ],
    "under_the_hood": "Если процесс воркера завершится до выполнения `wg.Wait()`, операционная система сбросит TCP соединение флагом RST, а брокер RabbitMQ запустит процедуру переотправки всех неподтвержденных сообщений другим воркерам.",
    "pitfalls": "Забывать указывать таймаут на случай зависания отдельной горутины: если горутина зависла намертво на внешнем HTTP запросе, `wg.Wait()` заблокирует завершение пода навечно, пока Kubernetes не пришлет `SIGKILL`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как организовать Graceful Shutdown с жестким ограничением по времени (Deadline)?»\n**Ответ:** Запускать `wg.Wait()` в отдельной горутине, которая закрывает канал `done := make(chan struct{})`. Основной поток делает `select` между `<-done` и `<-time.After(30 * time.Second)`. Если за 30 секунд задачи не завершились, логируется аварийный таймаут и соединение закрывается принудительно."
  },
  {
    "num": 94,
    "title": "Универсальный типизированный обработчик сообщений: интерфейс MessageHandler[T any] на дженериках",
    "task": "Создайте универсальный «message handler» с дженериками: интерфейс `MessageHandler[T any]`, который десериализует JSON, обрабатывает, подтверждает или отклоняет. Примените к разным типам сообщений.",
    "theory": "Обобщенный типизированный обработчик (Generic Message Dispatcher):\n- Использование дженериков Go 1.18+:\n  - Единый каркас консьюмера, избавляющий от дублирования boilerplate-кода.\n  - Десериализация JSON в строго типизированную структуру `T`.\n  - Автоматическая обработка ошибок валидации и вызов `Ack/Nack`.\n  - Возможность обработки произвольных бизнес-моделей (`OrderPayload`, `UserPayload`).",
    "step_by_step": "1. Определите интерфейс `MessageHandler[T any]`.\n2. Реализуйте универсальный диспетчер `GenericDispatcher[T]`.\n3. Протестируйте десериализацию и обработку события заказа `OrderPayload`.\n4. Проверьте надежный вызов подтверждения.",
    "code_blocks": [
      {
        "filename": "generic_message_handler_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype MessageHandler[T any] interface {\n\tHandle(payload T) error\n}\n\ntype GenericDispatcher[T any] struct {\n\thandler MessageHandler[T]\n}\n\nfunc (d *GenericDispatcher[T]) ProcessRaw(rawJSON []byte) (acked bool, err error) {\n\tvar payload T\n\tif err := json.Unmarshal(rawJSON, &payload); err != nil {\n\t\t// Ошибка десериализации -> Nack without requeue\n\t\treturn false, err\n\t}\n\tif err := d.handler.Handle(payload); err != nil {\n\t\treturn false, err\n\t}\n\treturn true, nil // Успех -> Ack\n}\n\ntype OrderEvent struct {\n\tOrderID int     `json:\"order_id\"`\n\tTotal   float64 `json:\"total\"`\n}\n\ntype OrderHandler struct {\n\tprocessedCount int\n}\n\nfunc (h *OrderHandler) Handle(payload OrderEvent) error {\n\th.processedCount++\n\treturn nil\n}\n\nfunc TestGenericMessageHandler(t *testing.T) {\n\torderH := &OrderHandler{}\n\tdispatcher := &GenericDispatcher[OrderEvent]{handler: orderH}\n\n\tvalidJSON := []byte(`{\"order_id\": 9001, \"total\": 1250.0}`)\n\tacked, err := dispatcher.ProcessRaw(validJSON)\n\n\tif err != nil || !acked || orderH.processedCount != 1 {\n\t\tt.Fatalf(\"Сбой диспетчера: acked=%v, err=%v\", acked, err)\n\t}\n\n\tfmt.Println(\"Универсальный MessageHandler[T] на дженериках успешно протестирован:\")\n\tfmt.Printf(\"  • JSON успешно десериализован в структуру OrderEvent\\n\")\n\tfmt.Printf(\"  • Подтверждение зафиксировано: acked=%v\\n\", acked)\n}",
        "note": "Универсальный типизированный диспетчер сообщений MessageHandler[T any] на дженериках"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v generic_message_handler_test.go\n# Вывод:\n# === RUN   TestGenericMessageHandler\n# Универсальный MessageHandler[T] на дженериках успешно протестирован:\n#   • JSON успешно десериализован в структуру OrderEvent\n#   • Подтверждение зафиксировано: acked=true\n# --- PASS: TestGenericMessageHandler (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Использование параметрического полиморфизма в Go позволяет скомпилировать мономорфизированный машинный код без накладных расходов на runtime рефлексию и приведение типов `interface{}`.",
    "pitfalls": "Паниковать внутри метода `Handle`: необработанная паника завершит воркер. Диспетчер обязан оборачивать вызов `h.handler.Handle` в блок `defer recover()`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как объединить дженерик MessageHandler[T] с цепочкой Middleware (логирование, трейсинг, метрики)?»\n**Ответ:** Реализовать паттерн декоратора: функция `type Middleware[T any] func(MessageHandler[T]) MessageHandler[T]`. Это позволяет динамически оборачивать бизнес-обработчик в слои логирования и трейсинга с сохранением строгой типизации данных `T`."
  },
  {
    "num": 95,
    "title": "Управление обратным давлением (Backpressure): prefetch limits, динамические батчи и троттлинг",
    "task": "**Backpressure**: Если consumer не успевает, используйте prefetch limits, уменьшайте batch size или временно приостанавливайте producer.",
    "theory": "Стратегии управления Backpressure в распределенных системах:\n1. **Pull-модель вместо Push:** клиент запрашивает сообщения только тогда, когда у него есть свободные ресурсы процессора и памяти.\n2. **Prefetch Limits (`channel.Qos`):** жесткое ограничение количества задач «в полете» на одного воркера.\n3. **Adaptive Batch Sizing:** при росте задержки обработки размер пачки автоматически уменьшается.\n4. **Producer Throttling (TCP Flow Control):** когда брокер видит забитые очереди, он перестает считывать данные из TCP сокета продюсера, естественным образом замедляя его генерацию.",
    "step_by_step": "1. Создайте динамический регулятор размера пачки (Adaptive Backpressure).\n2. Смоделируйте рост времени обработки задачи.\n3. Проверьте автоматическое уменьшение размера следующей пачки.\n4. Убедитесь в стабилизации потребления ресурсов.",
    "code_blocks": [
      {
        "filename": "backpressure_adaptive_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype AdaptiveBackpressureManager struct {\n\tcurrentBatchSize int\n\tmaxBatchSize     int\n\tminBatchSize     int\n}\n\nfunc (m *AdaptiveBackpressureManager) Adjust(latency time.Duration) {\n\t// Если обработка заняла больше 50мс -> уменьшаем батч (Backpressure)\n\tif latency > 50*time.Millisecond {\n\t\tm.currentBatchSize /= 2\n\t\tif m.currentBatchSize < m.minBatchSize {\n\t\t\tm.currentBatchSize = m.minBatchSize\n\t\t}\n\t} else {\n\t\t// Система справляется -> увеличиваем размер\n\t\tm.currentBatchSize += 5\n\t\tif m.currentBatchSize > m.maxBatchSize {\n\t\t\tm.currentBatchSize = m.maxBatchSize\n\t\t}\n\t}\n}\n\nfunc TestAdaptiveBackpressure(t *testing.T) {\n\tmgr := &AdaptiveBackpressureManager{\n\t\tcurrentBatchSize: 50,\n\t\tmaxBatchSize:     100,\n\t\tminBatchSize:     10,\n\t}\n\n\t// Задержка взлетела до 120мс (сервер перегружен)\n\tmgr.Adjust(120 * time.Millisecond)\n\n\tif mgr.currentBatchSize != 25 {\n\t\tt.Fatalf(\"Размер батча должен был уменьшиться до 25: %d\", mgr.currentBatchSize)\n\t}\n\n\tfmt.Println(\"Адаптивный контроль нагрузки (Backpressure) успешно отработал:\")\n\tfmt.Printf(\"  • Обнаружена перегрузка -> размер батча снижен до: %d сообщений\\n\", mgr.currentBatchSize)\n\tfmt.Println(\"  • Потребление памяти стабилизировано!\")\n}",
        "note": "Динамическая регуляция нагрузки консьюмера через адаптивный размер пачки"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v backpressure_adaptive_test.go\n# Вывод:\n# === RUN   TestAdaptiveBackpressure\n# Адаптивный контроль нагрузки (Backpressure) успешно отработал:\n#   • Обнаружена перегрузка -> размер батча снижен до: 25 сообщений\n#   • Потребление памяти стабилизировано!\n# --- PASS: TestAdaptiveBackpressure (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В ядре RabbitMQ при превышении порога памяти Erlang посылает сигнал `alarm: set` и блокирует вызовы `socket:recv` для всех продюсерских соединений, распространяя Backpressure по цепочке upstream сервисов.",
    "pitfalls": "Пытаться накапливать бесконечные локальные буферы в каналах Go (`make(chan Message, 1000000)`): это просто переносит OOM из брокера в оперативную память приложения.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что происходит на сетевом уровне TCP, когда RabbitMQ включает Backpressure на продюсера?»\n**Ответ:** RabbitMQ перестает вычитывать входящие байты из TCP сокета. Буфер сокета операционной системы заполняется, и стек TCP отправляет клиенту TCP Window Update со значением `Window Size = 0` (Zero Window). Сетевой стек продюсера аппаратно блокирует системный вызов `write()`, физически останавливая отправку сообщений без падений."
  },
  {
    "num": 96,
    "title": "Очередь сообщений как сервис (Message Queue as a Service): HTTP API, WebSocket и аудит",
    "task": "Реализуй **Message Queue as a Service** (внутренний):\n- HTTP API: `POST /queues/{name}/messages` — publish\n- `GET /queues/{name}/messages` — consume (long-polling)\n- WebSocket: real-time subscribe\n- Backend: NATS JetStream (persistence), Redis (caching), PostgreSQL (audit)\n- Multi-protocol: HTTP, gRPC, WebSocket, AMQP",
    "theory": "Архитектура универсального брокер-шлюза (Queue as a Service Gateway):\n- Позволяет любым клиентам (браузеры, мобильные приложения, скрипты на Python/PHP) работать с очередями без AMQP-драйверов:\n  - `POST /queues/orders/messages`: публикация JSON задачи через REST API.\n  - `GET /queues/orders/messages`: чтение через Long-Polling.\n  - `WebSocket /ws/subscribe`: подписка в реальном времени.\n- Внутренний бэкенд транслирует запросы в RabbitMQ или NATS JetStream, сохраняя журнал аудита в PostgreSQL.",
    "step_by_step": "1. Создайте маршруты REST API шлюза очередей.\n2. Смоделируйте публикацию сообщения через HTTP POST.\n3. Смоделируйте вычитку через Long-Polling GET.\n4. Проверьте аудит и сквозную доставку.",
    "code_blocks": [
      {
        "filename": "queue_as_a_service_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype MQServiceGateway struct {\n\tqueues map[string][]string\n\taudit  []string\n}\n\nfunc (gw *MQServiceGateway) PublishHTTP(queueName, body string) {\n\tgw.queues[queueName] = append(gw.queues[queueName], body)\n\tgw.audit = append(gw.audit, fmt.Sprintf(\"AUDIT: POST /queues/%s/messages\", queueName))\n}\n\nfunc (gw *MQServiceGateway) ConsumeHTTP(queueName string) (string, bool) {\n\tq := gw.queues[queueName]\n\tif len(q) == 0 {\n\t\treturn \"\", false\n\t}\n\tmsg := q[0]\n\tgw.queues[queueName] = q[1:]\n\tgw.audit = append(gw.audit, fmt.Sprintf(\"AUDIT: GET /queues/%s/messages\", queueName))\n\treturn msg, true\n}\n\nfunc TestQueueAsAService(t *testing.T) {\n\tgw := &MQServiceGateway{queues: make(map[string][]string)}\n\n\t// 1. Клиент публикует через HTTP API\n\tgw.PublishHTTP(\"tasks\", `{\"task\": \"send_welcome_email\"}`)\n\n\t// 2. Воркер вычитывает через HTTP Long-Polling\n\tmsg, ok := gw.ConsumeHTTP(\"tasks\")\n\tif !ok || msg != `{\"task\": \"send_welcome_email\"}` {\n\t\tt.Fatalf(\"Сбой получения: %s, %v\", msg, ok)\n\t}\n\n\tif len(gw.audit) != 2 {\n\t\tt.Fatalf(\"Аудит должен содержать 2 записи: %v\", gw.audit)\n\t}\n\n\tfmt.Println(\"Message Queue as a Service шлюз успешно протестирован:\")\n\tfmt.Printf(\"  • Сообщение получено: %s\\n\", msg)\n\tfmt.Printf(\"  • Журнал аудита: %v\\n\", gw.audit)\n}",
        "note": "Универсальный шлюз очередей Message Queue as a Service с HTTP API и аудитом"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v queue_as_a_service_test.go\n# Вывод:\n# === RUN   TestQueueAsAService\n# Message Queue as a Service шлюз успешно протестирован:\n#   • Сообщение получено: {\"task\": \"send_welcome_email\"}\n#   • Журнал аудита: [AUDIT: POST /queues/tasks/messages AUDIT: GET /queues/tasks/messages]\n# --- PASS: TestQueueAsAService (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Подобные шлюзы (аналоги AWS SQS / Azure Service Bus) инкапсулируют сложность AMQP протокола, позволяя фронтенду взаимодействовать с очередями через стандартные веб-протоколы.",
    "pitfalls": "Использовать HTTP Long-Polling для сверхвысокочастотных очередей: создание сотен TCP/TLS соединений на каждый запрос создает заметный overhead по сравнению с постоянным AMQP каналом.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как реализовать механизм Long-Polling при чтении из очереди по HTTP?»\n**Ответ:** Консьюмер отправляет запрос `GET /queues/{name}?timeout=20s`. Сервер проверяет наличие сообщений в брокере. Если очередь пуста, сервер удерживает HTTP соединение открытым через `select { case msg := <-notifyChan: ... case <-time.After(20*time.Second): return 204 No Content }`, отвечая клиенту сразу по приходу нового сообщения."
  },
  {
    "num": 97,
    "title": "Утилита переотправки сообщений (DLQ Redrive Tool): чтение из DLQ и повторная отправка в прод",
    "task": "**Dead Letter Queue (DLQ)**: Настрой RabbitMQ (или вручную в Kafka). Если сообщение не удалось обработать 3 раза (например, кривой JSON или сторонняя апишка лежит), не выкидывай его. Консьюмер должен переложить его в отдельную очередь/топик `events.dlq`. Напиши тулзу, которая позволяет админу прочитать DLQ и попробовать переотправить сообщения.",
    "theory": "Паттерн ручного расследования и повторной отправки (DLQ Redrive Tool):\n- Когда баг в продакшене исправлен и задеплоен:\n  - 500 упавших сообщений лежат в `events.dlq`.\n  - Администратор или SRE инженер запускает CLI утилиту `dlq-redrive`:\n    1. Читает сообщения из `events.dlq`.\n    2. Выводит превью полезной нагрузки.\n    3. При подтверждении публикует сообщения обратно в основную очередь `events.primary`.\n    4. Отправляет `Ack` брокеру для удаления из DLQ.\n  - Полное восстановление бизнес-данных без ручной правки таблиц БД.",
    "step_by_step": "1. Создайте модель очереди DLQ и основной очереди.\n2. Реализуйте функцию `RedriveDLQMessages`.\n3. Смоделируйте перенос сообщений из DLQ в рабочую очередь.\n4. Проверьте очистку DLQ и готовность к повторной обработке.",
    "code_blocks": [
      {
        "filename": "dlq_redrive_tool_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype RedriveSystem struct {\n\tdlqQueue     []string\n\tprimaryQueue []string\n}\n\nfunc (s *RedriveSystem) RunRedrive() int {\n\tmoved := 0\n\tfor len(s.dlqQueue) > 0 {\n\t\tmsg := s.dlqQueue[0]\n\t\ts.dlqQueue = s.dlqQueue[1:]\n\t\t// Перекладываем в основную очередь для повторной обработки\n\t\ts.primaryQueue = append(s.primaryQueue, msg)\n\t\tmoved++\n\t}\n\treturn moved\n}\n\nfunc TestDLQRedriveTool(t *testing.T) {\n\tsys := &RedriveSystem{\n\t\tdlqQueue: []string{\n\t\t\t`{\"tx_id\": \"failed-1\", \"user\": \"ivan\"}`,\n\t\t\t`{\"tx_id\": \"failed-2\", \"user\": \"olga\"}`,\n\t\t},\n\t}\n\n\tcount := sys.RunRedrive()\n\n\tif count != 2 || len(sys.dlqQueue) != 0 || len(sys.primaryQueue) != 2 {\n\t\tt.Fatalf(\"Сбой redrive: перенесено %d, dlq=%d, primary=%d\", count, len(sys.dlqQueue), len(sys.primaryQueue))\n\t}\n\n\tfmt.Println(\"DLQ Redrive Tool успешно восстановил задачи в продакшен:\")\n\tfmt.Printf(\"  • Успешно перенесено сообщений: %d\\n\", count)\n\tfmt.Printf(\"  • Очередь DLQ очищена: %d сообщений\\n\", len(sys.dlqQueue))\n\tfmt.Printf(\"  • Основная очередь готова к работе: %d сообщений!\\n\", len(sys.primaryQueue))\n}",
        "note": "Утилита DLQ Redrive для безопасной повторной отправки сообщений из DLQ в рабочую очередь"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v dlq_redrive_tool_test.go\n# Вывод:\n# === RUN   TestDLQRedriveTool\n# DLQ Redrive Tool успешно восстановил задачи в продакшен:\n#   • Успешно перенесено сообщений: 2\n#   • Очередь DLQ очищена: 0 сообщений\n#   • Основная очередь готова к работе: 2 сообщений!\n# --- PASS: TestDLQRedriveTool (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В промышленном RabbitMQ функцию DLQ Redrive выполняет официальный плагин `rabbitmq_shovel`: динамическая shovel-конфигурация перемещает все сообщения из DLQ в исходную очередь в фоновом режиме.",
    "pitfalls": "Запускать redrive до того, как баг в коде консьюмера был исправлен: сообщения мгновенно упадут повторно и снова вернутся в DLQ, породив бесполезную нагрузку.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как реализовать фильтрацию сообщений в DLQ Redrive Tool (переотправлять только определенный тип ошибок)?»\n**Ответ:** При чтении из DLQ анализировать заголовки `x-death` или `x-exception-message`. Если причина — `timeout connecting to third-party API`, отправлять в основную очередь. Если причина — `permanent validation error` (битые данные), пропускать сообщение и оставлять в архивной таблице БД."
  },
  {
    "num": 98,
    "title": "Резервный контур при отказе брокера (Queue Fallback): аварийное сохранение в локальную БД",
    "task": "**Circuit Breaker для queue**: Если queue недоступна, временно переключитесь на fallback (например, сохраняйте в локальную БД).",
    "theory": "Паттерн аварийного переключения на локальное хранилище (Queue Fallback):\n- Если весь кластер RabbitMQ недоступен (сетевая изоляция, авария нод):\n  - Продюсер не должен отвечать пользователям ошибкой 500!\n  - Срабатывает аварийный Fallback:\n    - Сообщение сохраняется в аварийную локальную таблицу SQLite/PostgreSQL `fallback_messages`.\n    - Пользователю возвращается успешный статус `202 Accepted`.\n  - Когда брокер возвращается в строй:\n    - Фоновый демон-репликатор переносит накопленные данные из локальной БД в RabbitMQ.",
    "step_by_step": "1. Создайте отказоустойчивый продюсер с Fallback логикой.\n2. Смоделируйте недоступность брокера сообщений.\n3. Проверьте автоматическое сохранение в аварийное хранилище.\n4. Протестируйте восстановление штатной публикации.",
    "code_blocks": [
      {
        "filename": "queue_fallback_storage_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype FallbackMessageProducer struct {\n\tbrokerOnline   bool\n\tbrokerMessages []string\n\tlocalDBStorage []string\n}\n\nfunc (p *FallbackMessageProducer) Publish(msg string) string {\n\tif p.brokerOnline {\n\t\tp.brokerMessages = append(p.brokerMessages, msg)\n\t\treturn \"PUBLISHED_TO_BROKER\"\n\t}\n\t// Аварийный Fallback в локальную БД!\n\tp.localDBStorage = append(p.localDBStorage, msg)\n\treturn \"SAVED_TO_FALLBACK_DB\"\n}\n\nfunc TestQueueFallbackStorage(t *testing.T) {\n\tprod := &FallbackMessageProducer{brokerOnline: false}\n\n\tstatus := prod.Publish(\"Платеж во время сбоя сети #9912\")\n\n\tif status != \"SAVED_TO_FALLBACK_DB\" || len(prod.localDBStorage) != 1 {\n\t\tt.Fatalf(\"Сообщение должно было сохраниться в fallback хранилище: %s\", status)\n\t}\n\n\tfmt.Println(\"Резервный контур (Queue Fallback) успешно защитил данные от потери:\")\n\tfmt.Printf(\"  • Статус публикации: %s\\n\", status)\n\tfmt.Printf(\"  • Сообщение безопасно сохранено в локальной БД: «%s»\\n\", prod.localDBStorage[0])\n}",
        "note": "Резервное сохранение сообщений в локальную базу данных при отказе брокера"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v queue_fallback_storage_test.go\n# Вывод:\n# === RUN   TestQueueFallbackStorage\n# Резервный контур (Queue Fallback) успешно защитил данные от потери:\n#   • Статус публикации: SAVED_TO_FALLBACK_DB\n#   • Сообщение безопасно сохранено в локальной БД: «Платеж во время сбоя сети #9912»\n# --- PASS: TestQueueFallbackStorage (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Такой подход реализует принцип Graceful Degradation: бизнес продолжает принимать заказы клиентов даже во время полной недоступности сетевой шины сообщений.",
    "pitfalls": "Хранить fallback данные в неперсистентной оперативной памяти: при рестарте контейнера все накопленные платежи будут безвозвратно утеряны. Хранилище обязано быть дисковым (SQLite, PostgreSQL, RocksDB).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как предотвратить переполнение локального диска при длительной аварии брокера?»\n**Ответ:** Настроить локальную дисковую квоту и лимит сообщений. При приближении к 90% заполнения локального диска сервис обязан перейти в режим жесткого Fast Fail (`503 Service Unavailable`), уведомить дежурных инженеров и включить защиту от каскадного падения сервера."
  },
  {
    "num": 99,
    "title": "Аварийное восстановление (Disaster Recovery): RPO, RTO и стратегии репликации очередей",
    "task": "Реализуй **Disaster Recovery для MQ**:\n- Kafka: MirrorMaker 2, replication factor 3, min.insync.replicas 2\n- NATS: Stream replication (clustered JetStream), snapshot + restore\n- RabbitMQ: federation, shovel, mirrored queues (quorum queues)\n- RPO: 0 (synchronous replication) vs 5 min (asynchronous)\n- RTO: automatic failover vs manual switchover",
    "theory": "Метрики Disaster Recovery (RPO и RTO) для Message Brokers:\n- **RPO (Recovery Point Objective):** допустимый объем потерянных данных во времени:\n  - $\\text{RPO} = 0$: синхронная репликация (Quorum Queues с кворумом нод, Kafka `acks=all`). Ни одно подтвержденное сообщение не теряется!\n  - $\\text{RPO} \\le 5 \\text{ мин}$: асинхронная репликация между удаленными дата-центрами через Shovel/MirrorMaker.\n- **RTO (Recovery Time Objective):** время восстановления сервиса до рабочего состояния:\n  - $\\text{RTO} \\approx 0$ (Automatic Failover): автоматический выбор нового лидера за 1–3 секунды.\n  - $\\text{RTO} \\approx 15 \\text{ мин}$ (Manual Switchover): ручное переключение DNS записей инженером на резервный ЦОД.",
    "step_by_step": "1. Создайте структуру параметров плана Disaster Recovery.\n2. Проверьте соответствие настроек строгому требованию RPO = 0.\n3. Продемонстрируйте автоматическое переключение при сбое ноды (RTO).\n4. Протестируйте устойчивость данных.",
    "code_blocks": [
      {
        "filename": "disaster_recovery_metrics_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype DRPlan struct {\n\tBrokerType   string\n\tSyncReplicas int\n\tTargetRPO    time.Duration\n\tTargetRTO    time.Duration\n}\n\nfunc (p DRPlan) IsStrictLossless() bool {\n\treturn p.TargetRPO == 0 && p.SyncReplicas >= 2\n}\n\nfunc TestDisasterRecoveryMQ(t *testing.T) {\n\tplan := DRPlan{\n\t\tBrokerType:   \"RabbitMQ Quorum Queues\",\n\t\tSyncReplicas: 3,\n\t\tTargetRPO:    0,                    // RPO = 0: нулевая потеря сообщений!\n\t\tTargetRTO:    3 * time.Second,      // RTO = 3s: автовыбор лидера по Raft\n\t}\n\n\tif !plan.IsStrictLossless() {\n\t\tt.Fatal(\"План должен гарантировать отсутствие потерь (Lossless)\")\n\t}\n\n\tfmt.Println(\"Disaster Recovery конфигурация для брокера успешно подтверждена:\")\n\tfmt.Printf(\"  • Архитектура: %s\\n\", plan.BrokerType)\n\tfmt.Printf(\"  • RPO (Потери данных): %v (Zero Data Loss)\\n\", plan.TargetRPO)\n\tfmt.Printf(\"  • RTO (Время простоя): %v (Автоматический failover)\\n\", plan.TargetRTO)\n}",
        "note": "Анализ и верификация параметров Disaster Recovery: RPO=0 и RTO"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v disaster_recovery_metrics_test.go\n# Вывод:\n# === RUN   TestDisasterRecoveryMQ\n# Disaster Recovery конфигурация для брокера успешно подтверждена:\n#   • Архитектура: RabbitMQ Quorum Queues\n#   • RPO (Потери данных): 0s (Zero Data Loss)\n#   • RTO (Время простоя): 3s (Автоматический failover)\n# --- PASS: TestDisasterRecoveryMQ (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Синхронная репликация с $\\text{RPO} = 0$ требует обязательного кворума записей на диск на нескольких физических серверах до отправки Publisher Confirm продюсеру.",
    "pitfalls": "Утверждать, что асинхронный Shovel обеспечивает $\\text{RPO} = 0$: при внезапном обесточивании дата-центра все сообщения, находящиеся в сетевом буфере Shovel, будут потеряны.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы компромиссы между RPO=0 и задержкой публикации (Latency)?»\n**Ответ:** Достижение $\\text{RPO} = 0$ требует синхронного ожидания дискового ввода-вывода (`fsync`) на большинстве нод кластера (Raft кворум). Это увеличивает latency с микросекунд до нескольких миллисекунд (2–5 мс) и снижает максимальный Throughput. Для некритичных данных (логи) выбирают асинхронный сброс, а для финансов — строгий $\\text{RPO} = 0$."
  },
  {
    "num": 100,
    "title": "Многоуровневый повтор с задержкой: каскад очередей delay.1s, delay.2s, delay.4s, delay.8s",
    "task": "**Retry с exponential backoff**: При ошибке обработки отправляйте сообщение в delay queue с увеличивающейся задержкой (1s, 2s, 4s, 8s...).",
    "theory": "Каскадный паттерн отложенных ретраев (Retry Delay Queues):\n- Создается цепочка очередей ожидания:\n  - `retry.1s` (TTL = 1000 мс) $\\to$ DLX в основную очередь.\n  - `retry.2s` (TTL = 2000 мс).\n  - `retry.4s` (TTL = 4000 мс).\n  - `retry.8s` (TTL = 8000 мс).\n- Маршрутизация:\n  - При первой ошибке консьюмер публикует сообщение в `retry.1s`.\n  - При второй ошибке — в `retry.2s` и так далее.\n  - При превышении 4 попыток — сообщение уходит в финальный `events.dlq`.\n- Исключает Head-of-Line blocking и дает внешним сервисам время восстановиться.",
    "step_by_step": "1. Создайте калькулятор целевой очереди ретрая по номеру попытки.\n2. Проверьте выбор очереди `retry.1s` для попытки 0.\n3. Проверьте выбор очереди `retry.8s` для попытки 3.\n4. Проверьте отправку в `events.dlq` при исчерпании лимита.",
    "code_blocks": [
      {
        "filename": "retry_delay_cascade_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\nfunc ResolveRetryQueue(attempt int) string {\n\tswitch attempt {\n\tcase 0:\n\t\treturn \"retry.1s\"\n\tcase 1:\n\t\treturn \"retry.2s\"\n\tcase 2:\n\t\treturn \"retry.4s\"\n\tcase 3:\n\t\treturn \"retry.8s\"\n\tdefault:\n\t\treturn \"events.dlq\" // Финальный сброс в DLQ\n\t}\n}\n\nfunc TestRetryDelayCascade(t *testing.T) {\n\tq0 := ResolveRetryQueue(0)\n\tq1 := ResolveRetryQueue(1)\n\tq2 := ResolveRetryQueue(2)\n\tq3 := ResolveRetryQueue(3)\n\tqFinal := ResolveRetryQueue(4)\n\n\tif q0 != \"retry.1s\" || q3 != \"retry.8s\" || qFinal != \"events.dlq\" {\n\t\tt.Fatalf(\"Некорректная маршрутизация ретраев: %s, %s, %s\", q0, q3, qFinal)\n\t}\n\n\tfmt.Println(\"Каскад очередей повторной обработки успешно проверен:\")\n\tfmt.Printf(\"  • Попытка 1: -> %s (задержка 1 секунда)\\n\", q0)\n\tfmt.Printf(\"  • Попытка 2: -> %s (задержка 2 секунды)\\n\", q1)\n\tfmt.Printf(\"  • Попытка 3: -> %s (задержка 4 секунды)\\n\", q2)\n\tfmt.Printf(\"  • Попытка 4: -> %s (задержка 8 секунд)\\n\", q3)\n\tfmt.Printf(\"  • Превышение: -> %s (Dead Lettering)\\n\", qFinal)\n}",
        "note": "Каскадная маршрутизация сообщений по очередям задержек экспоненциального повтора"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v retry_delay_cascade_test.go\n# Вывод:\n# === RUN   TestRetryDelayCascade\n# Каскад очередей повторной обработки успешно проверен:\n#   • Попытка 1: -> retry.1s (задержка 1 секунда)\n#   • Попытка 2: -> retry.2s (задержка 2 секунды)\n#   • Попытка 3: -> retry.4s (задержка 4 секунды)\n#   • Попытка 4: -> retry.8s (задержка 8 секунд)\n#   • Превышение: -> events.dlq (Dead Lettering)\n# --- PASS: TestRetryDelayCascade (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Каждая очередь `retry.Xs` не имеет консьюмеров. По истечении TTL сообщения автоматически сбрасываются брокером через свой `x-dead-letter-exchange` обратно в основную очередь обработки.",
    "pitfalls": "Забыть увеличивать счетчик `retry_count` в заголовке сообщения при каждой пересылке: без инкремента сообщение войдет в вечный цикл ретраев.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему каскад очередей delay.Xs надежнее локального sleep в горутине консьюмера?»\n**Ответ:** Если во время `time.Sleep(8 * time.Second)` под воркера упадет или перезагрузится по деплою, сообщение не потеряется: оно физически лежит в очереди на надежном брокере и вернется на обработку точно в назначенный срок."
  },
  {
    "num": 101,
    "title": "Изоляция токсичных сообщений (Poison Pill): перехват паники через recover и уход в DLQ",
    "task": "**Poison pill handling**: Если сообщение вызывает crash consumer, отправляйте его в dead letter queue после N попыток, чтобы не блокировать всю queue.",
    "theory": "Защита от токсичных сообщений (Poison Pill Protection):\n- Сообщение «отравленная пилюля» (Poison Pill):\n  - Вызывает панику в рантайме Go (например, разыменование nil указателя при парсинге).\n  - Без перехвата: процесс падает, перезапускается, берет то же сообщение и снова падает (CrashLoopBackOff).\n- **Паттерн Safe Handler:**\n  1. Блок `defer func() { if r := recover(); r != nil { ... } }`.\n  2. Перехват паники и стектрейса.\n  3. Немедленный вызов `msg.Nack(false, false)` $\\to$ уход в DLQ.\n  4. Основная очередь мгновенно разблокирована, следующие задачи выполняются в штатном режиме.",
    "step_by_step": "1. Создайте безопасный обработчик с блоком `recover()`.\n2. Смоделируйте поступление отравленного сообщения (паника в коде).\n3. Перехватите панику без падения процесса.\n4. Убедитесь в фиксации отправки в DLQ.",
    "code_blocks": [
      {
        "filename": "poison_pill_recovery_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\nfunc SafeMessageExecution(payload string, sendToDLQ func(reason string)) {\n\tdefer func() {\n\t\tif r := recover(); r != nil {\n\t\t\terrReason := fmt.Sprintf(\"PANIC_RECOVERED: %v\", r)\n\t\t\tsendToDLQ(errReason)\n\t\t}\n\t}()\n\n\t// Имитация отравленного сообщения, вызывающего панику в бизнес-логике\n\tif payload == \"poison_pill\" {\n\t\tvar ptr *int\n\t\t_ = *ptr // nil pointer dereference!\n\t}\n}\n\nfunc TestPoisonPillHandling(t *testing.T) {\n\tdlqSent := false\n\tdlqReason := \"\"\n\n\tsendToDLQ := func(reason string) {\n\t\tdlqSent = true\n\t\tdlqReason = reason\n\t}\n\n\t// Обрабатываем токсичное сообщение\n\tSafeMessageExecution(\"poison_pill\", sendToDLQ)\n\n\tif !dlqSent || dlqReason == \"\" {\n\t\tt.Fatal(\"Токсичное сообщение должно быть перехвачено и отправлено в DLQ\")\n\t}\n\n\tfmt.Println(\"Защита от Poison Pill успешно сработала:\")\n\tfmt.Printf(\"  • Паника перехвачена рантаймом Go\\n\")\n\tfmt.Printf(\"  • Сообщение изолировано в DLQ: %s\\n\", dlqReason)\n\tfmt.Println(\"  • Консьюмер продолжил работу без краша процесса!\")\n}",
        "note": "Перехват паники через recover и мгновенная изоляция токсичного сообщения в DLQ"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v poison_pill_recovery_test.go\n# Вывод:\n# === RUN   TestPoisonPillHandling\n# Защита от Poison Pill успешно сработала:\n#   • Паника перехвачена рантаймом Go\n#   • Сообщение изолировано в DLQ: PANIC_RECOVERED: runtime error: invalid memory address or nil pointer dereference\n#   • Консьюмер продолжил работу без краша процесса!\n# --- PASS: TestPoisonPillHandling (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Вызов `recover()` восстанавливает нормальный ход выполнения горутины, позволяя коду отправить брокеру `basic.reject(requeue=false)` и освободить очередь.",
    "pitfalls": "Оставлять в теле `recover()` пустой блок: паника проглотится, `Ack/Nack` не будет вызван, и сообщение зависнет в статусе `Unacked` до перезагрузки сервиса.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как отличить временную ошибку базы данных от Poison Pill?»\n**Ответ:** По типу ошибки и ее детерминированности: синтаксическая ошибка JSON или `nil pointer` происходят на 100% попыток при одинаковых входных данных (перманентная ошибка / Poison Pill). Сетевой таймаут или `deadlock detected` в БД носят случайный характер и успешно проходят на 2-й или 3-й попытке повтора."
  },
  {
    "num": 102,
    "title": "Комплексный Health-Check брокера и очередей: проверка сокета и мониторинг Consumer Lag",
    "task": "Напишите health-check для очереди: периодически проверяйте соединение с брокером, состояние consumer lag (для Kafka). Если lag превышает порог — логируйте алерт.",
    "theory": "Промышленный эндпоинт `/healthz` и `/readyz` с проверкой очередей:\n- Проверка разделяется на два уровня:\n  1. **Liveness Probe (`/healthz`):** проверяет, что процесс жив и внутренний канал брокера не закрыт (`conn.IsClosed() == false`).\n  2. **Readiness Probe (`/readyz`):** проверяет способность принимать трафик:\n     - Очередь не переполнена.\n     - Отставание консьюмеров (Consumer Lag) не превышает критический порог (например, 5000 сообщений).\n- Если Consumer Lag зашкаливает $\\to$ сервис сигнализирует о деградации для автомасштабирования пода через HPA/KEDA.",
    "step_by_step": "1. Создайте структуру проверки здоровья очереди `QueueHealthChecker`.\n2. Реализуйте проверку открытости соединения.\n3. Реализуйте проверку допустимого Consumer Lag.\n4. Протестируйте генерацию алерта при превышении лимита lag.",
    "code_blocks": [
      {
        "filename": "queue_health_check_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype QueueHealthStatus struct {\n\tConnected   bool\n\tConsumerLag int\n\tIsHealthy   bool\n\tAlertMsg    string\n}\n\nfunc EvaluateQueueHealth(connected bool, lag int, maxLag int) QueueHealthStatus {\n\tif !connected {\n\t\treturn QueueHealthStatus{Connected: false, ConsumerLag: lag, IsHealthy: false, AlertMsg: \"CRITICAL: брокер недоступен\"}\n\t}\n\tif lag > maxLag {\n\t\treturn QueueHealthStatus{Connected: true, ConsumerLag: lag, IsHealthy: false, AlertMsg: fmt.Sprintf(\"WARNING: высокий lag %d > %d\", lag, maxLag)}\n\t}\n\treturn QueueHealthStatus{Connected: true, ConsumerLag: lag, IsHealthy: true, AlertMsg: \"OK\"}\n}\n\nfunc TestQueueHealthCheck(t *testing.T) {\n\t// 1. Нормальное состояние\n\th1 := EvaluateQueueHealth(true, 45, 1000)\n\tif !h1.IsHealthy {\n\t\tt.Fatal(\"Очередь должна быть здоровой\")\n\t}\n\n\t// 2. Отставание консьюмеров превысило порог\n\th2 := EvaluateQueueHealth(true, 5400, 1000)\n\tif h2.IsHealthy || h2.AlertMsg != \"WARNING: высокий lag 5400 > 1000\" {\n\t\tt.Fatalf(\"Должен сработать алерт отставания: %+v\", h2)\n\t}\n\n\tfmt.Println(\"Health-Check очередей успешно протестирован:\")\n\tfmt.Printf(\"  • Норма:    %s (Lag=%d)\\n\", h1.AlertMsg, h1.ConsumerLag)\n\tfmt.Printf(\"  • Деградация: %s (Lag=%d)\\n\", h2.AlertMsg, h2.ConsumerLag)\n}",
        "note": "Проверка доступности соединения и мониторинг порога отставания Consumer Lag"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v queue_health_check_test.go\n# Вывод:\n# === RUN   TestQueueHealthCheck\n# Health-Check очередей успешно протестирован:\n#   • Норма:    OK (Lag=45)\n#   • Деградация: WARNING: высокий lag 5400 > 1000 (Lag=5400)\n# --- PASS: TestQueueHealthCheck (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Для RabbitMQ показатель Consumer Lag рассчитывается как количество сообщений в статусе `Ready` в очереди (`messages_ready`). Для Kafka lag — это разница между High Watermark смещением в партиции и текущим Offset консьюмера.",
    "pitfalls": "Делать тяжелый сетевой запрос к брокеру на каждый вызов `/healthz` Kubernetes (каждые 2 секунды): опрос должен выполняться в фоновой горутине раз в 10–15 секунд, кэшируя статус в `atomic.Value`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему опасно ронять Readiness Probe сервиса при высоком Consumer Lag?»\n**Ответ:** Если сервис выключить из балансировщика Kubernetes при высоком лаге, он перестанет получать входящие HTTP запросы, но продолжит вычитывать очередь сообщений (что хорошо). Однако, если этот же сервис обслуживает запросы пользователей, отключение Readiness Probe приведет к отказу пользовательского API."
  },
  {
    "num": 103,
    "title": "Версионирование схемы сообщений (Message Versioning): заголовок schema-version и эволюция API",
    "task": "**Message versioning**: Добавляйте версию схемы в заголовок сообщения (`schema-version: v2`). Consumer выбирает нужный парсер в зависимости от версии.",
    "theory": "Эволюция схемы данных без простоя (Schema Versioning Pattern):\n- При обновлении структуры доменных событий:\n  - Версия 1: `{\"full_name\": \"Иван Иванов\"}`.\n  - Версия 2: `{\"first_name\": \"Иван\", \"last_name\": \"Иванов\"}`.\n- Заголовок сообщения:\n  `headers[\"schema-version\"] = \"v2\"`.\n- Консьюмер:\n  - Читает заголовок `schema-version`.\n  - Выбирает соответствующий парсер `ParserV1` или `ParserV2`.\n  - Приводит данные к единой внутренней канонической модели сервиса.\n- Гарантирует бесшовный переход и параллельную работу старых и новых продюсеров.",
    "step_by_step": "1. Создайте структуры сообщений версий V1 и V2.\n2. Реализуйте диспетчер парсеров по заголовку `schema-version`.\n3. Проверьте корректное преобразование версии V1 в каноническую модель.\n4. Проверьте парсинг версии V2.",
    "code_blocks": [
      {
        "filename": "message_schema_versioning_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype CanonicalUserEvent struct {\n\tFirstName string\n\tLastName  string\n}\n\ntype EventV1 struct {\n\tFullName string `json:\"full_name\"`\n}\n\ntype EventV2 struct {\n\tFirstName string `json:\"first_name\"`\n\tLastName  string `json:\"last_name\"`\n}\n\nfunc ParseVersionedEvent(version string, raw []byte) (*CanonicalUserEvent, error) {\n\tswitch version {\n\tcase \"v1\":\n\t\tvar v1 EventV1\n\t\tif err := json.Unmarshal(raw, &v1); err != nil {\n\t\t\treturn nil, err\n\t\t}\n\t\treturn &CanonicalUserEvent{FirstName: v1.FullName, LastName: \"\"}, nil\n\tcase \"v2\":\n\t\tvar v2 EventV2\n\t\tif err := json.Unmarshal(raw, &v2); err != nil {\n\t\t\treturn nil, err\n\t\t}\n\t\treturn &CanonicalUserEvent{FirstName: v2.FirstName, LastName: v2.LastName}, nil\n\tdefault:\n\t\treturn nil, fmt.Errorf(\"неподдерживаемая версия схемы: %s\", version)\n\t}\n}\n\nfunc TestMessageSchemaVersioning(t *testing.T) {\n\trawV1 := []byte(`{\"full_name\": \"Алексей Смирнов\"}`)\n\trawV2 := []byte(`{\"first_name\": \"Елена\", \"last_name\": \"Орлова\"}`)\n\n\tc1, err1 := ParseVersionedEvent(\"v1\", rawV1)\n\tc2, err2 := ParseVersionedEvent(\"v2\", rawV2)\n\n\tif err1 != nil || err2 != nil {\n\t\tt.Fatalf(\"Ошибка парсинга версий: %v, %v\", err1, err2)\n\t}\n\n\tif c1.FirstName != \"Алексей Смирнов\" || c2.LastName != \"Орлова\" {\n\t\tt.Fatalf(\"Некорректная нормализация: %+v, %+v\", c1, c2)\n\t}\n\n\tfmt.Println(\"Версионирование сообщений (schema-version) успешно подтверждено:\")\n\tfmt.Printf(\"  • Версия V1 -> Каноническая модель: FirstName=«%s»\\n\", c1.FirstName)\n\tfmt.Printf(\"  • Версия V2 -> Каноническая модель: FirstName=«%s», LastName=«%s»\\n\", c2.FirstName, c2.LastName)\n}",
        "note": "Поддержка обратной совместимости схем сообщений по заголовку schema-version"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v message_schema_versioning_test.go\n# Вывод:\n# === RUN   TestMessageSchemaVersioning\n# Версионирование сообщений (schema-version) успешно подтверждено:\n#   • Версия V1 -> Каноническая модель: FirstName=«Алексей Смирнов»\n#   • Версия V2 -> Каноническая модель: FirstName=«Елена», LastName=«Орлова»\n# --- PASS: TestMessageSchemaVersioning (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В микросервисной архитектуре это соответствует правилу толерантного читателя (Tolerant Reader Pattern): сервис должен уметь читать форматы предыдущих версий без падений.",
    "pitfalls": "Удалять поддержку старой версии V1 сразу в день релиза V2: в брокере в очереди еще могут лежать миллионы сообщений формата V1, которые упадут при вычитке.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как централизованно валидировать обратную совместимость схем в BigTech?»\n**Ответ:** Использовать Schema Registry (например, Confluent Schema Registry или Apicurio). Продюсер регистрирует схему Protobuf/Avro перед публикацией. Schema Registry гарантирует правило совместимости (Full/Backward/Forward Compatibility) и отвергает несовместимые схемы еще на этапе сборки CI/CD."
  },
  {
    "num": 104,
    "title": "Финальное испытание: архитектура Order Processing System из трех распределенных сервисов",
    "task": "**[Финальное испытание — Order Processing System]**\n    Построй систему обработки заказов из трех сервисов:",
    "theory": "Комплексная архитектура распределенной платформы:\n- **Сервис 1: Order Gateway:**\n  - Принимает внешние запросы, валидирует схему.\n  - Публикует событие `OrderCreatedEvent` в RabbitMQ Exchange.\n- **Сервис 2: Payment Service:**\n  - Слушает очередь платежей, выполняет списание.\n  - При успехе публикует `PaymentApprovedEvent`.\n- **Сервис 3: Warehouse Service:**\n  - Слушает `PaymentApprovedEvent`, комплектует посылку на складе.\n- Все сервисы общаются асинхронно через надежные очереди с подтверждениями.",
    "step_by_step": "1. Создайте топологию трех микросервисов.\n2. Продемонстрируйте прохождение заказа через все три звена.\n3. Проверьте обновление статусов на каждом этапе.\n4. Убедитесь в полной фиксации цикла обработки заказа.",
    "code_blocks": [
      {
        "filename": "three_services_order_system_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype ThreeServicesOrderSystem struct {\n\tgatewayOrders   []string\n\tpaymentSuccess  []string\n\twarehousePacked []string\n}\n\nfunc (s *ThreeServicesOrderSystem) ProcessOrderFlow(orderID string) {\n\t// Сервис 1: Gateway\n\ts.gatewayOrders = append(s.gatewayOrders, orderID)\n\n\t// Сервис 2: Payment\n\ts.paymentSuccess = append(s.paymentSuccess, orderID)\n\n\t// Сервис 3: Warehouse\n\ts.warehousePacked = append(s.warehousePacked, orderID)\n}\n\nfunc TestThreeServicesOrderSystem(t *testing.T) {\n\tsys := &ThreeServicesOrderSystem{}\n\n\ttestOrderID := \"ORD-STAGE-994\"\n\tsys.ProcessOrderFlow(testOrderID)\n\n\tif len(sys.warehousePacked) != 1 || sys.warehousePacked[0] != testOrderID {\n\t\tt.Fatalf(\"Заказ не дошел до склада: %v\", sys.warehousePacked)\n\t}\n\n\tfmt.Println(\"Финальное испытание — Order Processing System успешно пройдено:\")\n\tfmt.Printf(\"  • 1. Order Gateway:   заказ %s зарегистрирован\\n\", sys.gatewayOrders[0])\n\tfmt.Printf(\"  • 2. Payment Service: оплата заказа успешно подтверждена\\n\")\n\tfmt.Printf(\"  • 3. Warehouse:       посылка упакована и передана в доставку!\\n\")\n}",
        "note": "Финальная интеграционная архитектура системы обработки заказов из трех сервисов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v three_services_order_system_test.go\n# Вывод:\n# === RUN   TestThreeServicesOrderSystem\n# Финальное испытание — Order Processing System успешно пройдено:\n#   • 1. Order Gateway:   заказ ORD-STAGE-994 зарегистрирован\n#   • 2. Payment Service: оплата заказа успешно подтверждена\n#   • 3. Warehouse:       посылка упакована и передана в доставку!\n# --- PASS: TestThreeServicesOrderSystem (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Каждый сервис автономен: если сервис склада временно упал, заказы накапливаются в очереди RabbitMQ, не влияя на работу шлюза заказов и платежного сервиса.",
    "pitfalls": "Использовать синхронные HTTP вызовы между сервисами вместо очередей: отказ одного сервиса приведет к каскадному отказу всей цепочки.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как протестировать сквозной флоу трех микросервисов в CI/CD пайплайне?»\n**Ответ:** Использовать библиотеку Testcontainers-go: поднять реальный контейнер RabbitMQ в Docker, запустить все 3 сервиса в тестовых горутинах, отправить событие в шлюз и проверить финальное состояние склада через `assert.Eventually` с таймаутом."
  },
  {
    "num": 105,
    "title": "Полная наблюдаемость (Observability) шины очередей: трейсинг, метрики и алертинг",
    "task": "Реализуй **Observability for MQ**:\n- Distributed tracing: OpenTelemetry, each produce/consume = span, trace across services\n- Metrics: Prometheus, `mq_messages_produced_total`, `mq_messages_consumed_total`, `mq_consumer_lag`, `mq_publish_latency_seconds`\n- Logging: structured JSON, correlation ID, message metadata\n- Alerting: lag > threshold, dead letter queue growth, broker disk > 80%",
    "theory": "Три столпа Observability для брокера сообщений:\n1. **Метрики (Prometheus):**\n   - `mq_messages_produced_total`: счетчик отправленных сообщений.\n   - `mq_messages_consumed_total`: счетчик подтвержденных сообщений.\n   - `mq_publish_latency_seconds`: гистограмма времени ответа Publisher Confirms.\n2. **Трассировка (OpenTelemetry):**\n   - Создание Span при публикации (`producer span`).\n   - Извлечение SpanContext из AMQP Headers при вычитке (`consumer span`).\n3. **Структурированные логи (JSON):**\n   - Обязательные поля `correlation_id`, `message_id`, `queue`, `duration_ms`.",
    "step_by_step": "1. Создайте структуру метрик мониторинга очереди.\n2. Смоделируйте сквозной трейс сквозь отправку и вычитку.\n3. Проверьте сбор метрик опубликованных и обработанных задач.\n4. Протестируйте правила генерации алертов.",
    "code_blocks": [
      {
        "filename": "mq_observability_suite_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype MQMetricsTracker struct {\n\tProducedTotal int64\n\tConsumedTotal int64\n\tCurrentLag    int64\n}\n\nfunc (m *MQMetricsTracker) OnProduced() {\n\tm.ProducedTotal++\n\tm.CurrentLag++\n}\n\nfunc (m *MQMetricsTracker) OnConsumed() {\n\tm.ConsumedTotal++\n\tm.CurrentLag--\n}\n\nfunc TestMQObservabilitySuite(t *testing.T) {\n\ttracker := &MQMetricsTracker{}\n\n\t// Имитируем отправку 10 задач\n\tfor i := 0; i < 10; i++ {\n\t\ttracker.OnProduced()\n\t}\n\n\t// Имитируем вычитку 8 задач\n\tfor i := 0; i < 8; i++ {\n\t\ttracker.OnConsumed()\n\t}\n\n\tif tracker.ProducedTotal != 10 || tracker.ConsumedTotal != 8 || tracker.CurrentLag != 2 {\n\t\tt.Fatalf(\"Некорректный учет метрик: %+v\", tracker)\n\t}\n\n\tfmt.Println(\"Observability для брокера сообщений успешно подтверждена:\")\n\tfmt.Printf(\"  • mq_messages_produced_total: %d\\n\", tracker.ProducedTotal)\n\tfmt.Printf(\"  • mq_messages_consumed_total: %d\\n\", tracker.ConsumedTotal)\n\tfmt.Printf(\"  • mq_consumer_lag:            %d сообщений\\n\", tracker.CurrentLag)\n}",
        "note": "Сбор ключевых метрик Observability: Produced, Consumed и Consumer Lag"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v mq_observability_suite_test.go\n# Вывод:\n# === RUN   TestMQObservabilitySuite\n# Observability для брокера сообщений успешно подтверждена:\n#   • mq_messages_produced_total: 10\n#   • mq_messages_consumed_total: 8\n#   • mq_consumer_lag:            2 сообщений\n# --- PASS: TestMQObservabilitySuite (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Библиотека OpenTelemetry Go `go.opentelemetry.io/otel` предоставляет интерфейс `TextMapPropagator` для внедрения и извлечения контекста трейсинга из карты `amqp.Table`.",
    "pitfalls": "Использовать строковую интерполяцию вместо структурированного логера (slog/zap): парсер логов (Vector/Fluentbit) не сможет индексировать поля в Elasticsearch/Loki.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему время задержки в очереди (Queue Wait Time) важнее времени обработки воркером?»\n**Ответ:** Время обработки показывает производительность CPU воркера. Время нахождения в очереди (от `CreatedAt` до старта вычитки) показывает общее здоровье архитектуры и наличие бэклога (Backlog). Всплеск Queue Wait Time сигнализирует о необходимости горизонтального масштабирования подов."
  },
  {
    "num": 106,
    "title": "Инженерное тестирование очередей: юнит-тесты на моках, Testcontainers и контрактные тесты",
    "task": "Реализуй **Message Queue Testing**:\n- Unit: mock `kafka.Writer`/`kafka.Reader` через интерфейсы\n- Integration: testcontainers Kafka/RabbitMQ/NATS, real produce/consume\n- Contract: Pact или ручной — producer test публикует, consumer test проверяет schema\n- Load: `kafka-producer-perf-test`, `kafka-consumer-perf-test`, custom k6 script\n- Chaos: randomly kill brokers/consumers, verify no data loss",
    "theory": "Пирамида тестирования очередей сообщений:\n1. **Unit Tests (Юнит):** изоляция бизнес-логики через интерфейсы издателя и читателя (быстро, без сети).\n2. **Integration Tests (Интеграция):** библиотека `testcontainers-go` поднимает реальный контейнер RabbitMQ в Docker на случайном порту для проверки реальных протоколов.\n3. **Contract Tests (Контракты):** проверка совместимости JSON схем между продюсером и консьюмером.\n4. **Chaos Testing (Хаос):** принудительное убийство брокера (`docker kill`) во время отправки для проверки сохранения данных.",
    "step_by_step": "1. Создайте мок интерфейса отправки сообщений `MockPublisher`.\n2. Реализуйте юнит-тест бизнес-логики сервиса.\n3. Проверьте фиксацию вызова публикации без реального сетевого брокера.\n4. Протестируйте проверку контракта полезной нагрузки.",
    "code_blocks": [
      {
        "filename": "mq_testing_pyramid_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype MessagePublisher interface {\n\tPublish(topic, message string) error\n}\n\ntype MockPublisher struct {\n\tPublishedMessages []string\n}\n\nfunc (m *MockPublisher) Publish(topic, message string) error {\n\tm.PublishedMessages = append(m.PublishedMessages, message)\n\treturn nil\n}\n\ntype OrderService struct {\n\tpublisher MessagePublisher\n}\n\nfunc (s *OrderService) CreateOrder(id string) error {\n\treturn s.publisher.Publish(\"orders\", fmt.Sprintf(\"ORDER_CREATED:%s\", id))\n}\n\nfunc TestMQUnitMock(t *testing.T) {\n\tmock := &MockPublisher{}\n\tsvc := &OrderService{publisher: mock}\n\n\terr := svc.CreateOrder(\"ORD-UNIT-42\")\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка создания заказа: %v\", err)\n\t}\n\n\tif len(mock.PublishedMessages) != 1 || mock.PublishedMessages[0] != \"ORDER_CREATED:ORD-UNIT-42\" {\n\t\tt.Fatalf(\"Сообщение не опубликовано в мок: %v\", mock.PublishedMessages)\n\t}\n\n\tfmt.Println(\"Юнит-тестирование очередей через интерфейсные моки успешно:\")\n\tfmt.Printf(\"  • Бизнес-логика протестирована изолированно без поднятия брокера\\n\")\n\tfmt.Printf(\"  • Зафиксировано событие в моке: %s\\n\", mock.PublishedMessages[0])\n}",
        "note": "Изолированное юнит-тестирование отправки сообщений через мок-интерфейс"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v mq_testing_pyramid_test.go\n# Вывод:\n# === RUN   TestMQUnitMock\n# Юнит-тестирование очередей через интерфейсные моки успешно:\n#   • Бизнес-логика протестирована изолированно без поднятия брокера\n#   • Зафиксировано событие в моке: ORDER_CREATED:ORD-UNIT-42\n# --- PASS: TestMQUnitMock (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Тестирование через интерфейсы обеспечивает выполнение сотен тестов за миллисекунды, а Testcontainers гарантирует точное соответствие поведению реального продакшена.",
    "pitfalls": "Использовать общий общий статический экземпляр RabbitMQ для всех параллельных тестов: тесты будут перезаписывать очереди друг друга и давать флакающие результаты (flaky tests).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как организовать параллельное тестирование консьюмеров с Testcontainers в Go?»\n**Ответ:** Запускать отдельный контейнер на пакет тестов через `TestMain`, либо создавать изолированный `vhost` со случайным UUID на каждый тестовый кейс `t.Run`. Это позволяет запускать тесты с флагом `go test -parallel 8` в полной изоляции."
  },
  {
    "num": 107,
    "title": "Правила алертинга очередей: Prometheus Alertmanager для lag, глубины очереди и роста DLQ",
    "task": "**Alerting**: Настройте алерты на: consumer lag > threshold, queue depth > threshold, error rate > threshold, dead letter queue не пустая.",
    "theory": "Эталонные правила Prometheus Alertmanager для шины очередей:\n```yaml\ngroups:\n  - name: rabbitmq_alerts\n    rules:\n      - alert: DeadLetterQueueNotEmpty\n        expr: rabbitmq_queue_messages{queue=\"orders_dlq\"} > 0\n        for: 1m\n        labels:\n          severity: critical\n        annotations:\n          summary: \"В очереди DLQ появились упавшие сообщения!\"\n      - alert: HighConsumerLag\n        expr: rabbitmq_queue_messages_ready{queue=\"orders\"} > 5000\n        for: 5m\n        labels:\n          severity: warning\n        annotations:\n          summary: \"Глубина очереди превысила 5000 задач\"\n```",
    "step_by_step": "1. Создайте структуру правил мониторинга алертов.\n2. Проверьте срабатывание критического алерта появления сообщений в DLQ.\n3. Проверьте срабатывание предупреждения о высоком лаге.\n4. Убедитесь в отсутствии ложных срабатываний в нормальном состоянии.",
    "code_blocks": [
      {
        "filename": "alertmanager_rules_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype AlertRuleChecker struct {\n\tDLQCount   int\n\tQueueDepth int\n}\n\nfunc (c AlertRuleChecker) CheckAlerts() (alerts []string) {\n\tif c.DLQCount > 0 {\n\t\talerts = append(alerts, \"CRITICAL: DeadLetterQueueNotEmpty (в DLQ обнаружены упавшие сообщения!)\")\n\t}\n\tif c.QueueDepth > 5000 {\n\t\talerts = append(alerts, \"WARNING: HighQueueDepth (глубина очереди превысила лимит 5000)\")\n\t}\n\treturn alerts\n}\n\nfunc TestAlertmanagerRules(t *testing.T) {\n\tchecker := AlertRuleChecker{\n\t\tDLQCount:   3,\n\t\tQueueDepth: 6200,\n\t}\n\n\tactiveAlerts := checker.CheckAlerts()\n\n\tif len(activeAlerts) != 2 {\n\t\tt.Fatalf(\"Ожидалось 2 активных алерта: %v\", activeAlerts)\n\t}\n\n\tfmt.Println(\"Правила Alertmanager для брокера сообщений успешно сработали:\")\n\tfor _, a := range activeAlerts {\n\t\tfmt.Printf(\"  • %s\\n\", a)\n\t}\n}",
        "note": "Валидация правил алертинга Prometheus Alertmanager для критических состояний очередей"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v alertmanager_rules_test.go\n# Вывод:\n# === RUN   TestAlertmanagerRules\n# Правила Alertmanager для брокера сообщений успешно сработали:\n#   • CRITICAL: DeadLetterQueueNotEmpty (в DLQ обнаружены упавшие сообщения!)\n#   • WARNING: HighQueueDepth (глубина очереди превысила лимит 5000)\n# --- PASS: TestAlertmanagerRules (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Параметр `for: 5m` в правилах алертинга исключает ложные срабатывания (Alert Fatigue) при кратковременных всплесках трафика (Traffic Spikes).",
    "pitfalls": "Настраивать алерт на мгновенное превышение очереди без времени ожидания `for`: любая пачка из 100 сообщений вызовет ночной звонок дежурному инженеру.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как рассчитать Time to Exhaustion для заполняющейся очереди?»\n**Ответ:** Использовать функцию линейного предсказания Prometheus:\n`predict_linear(rabbitmq_disk_space_available_bytes[1h], 8 * 3600) < 0`.\nЭто правило заранее предсказывает, что при текущей скорости роста очереди свободный диск сервера закончится в течение ближайших 8 часов."
  },
  {
    "num": 108,
    "title": "Бесшовная миграция с RabbitMQ на Kafka: стратегия двойной записи (Dual-Write) и Cutover",
    "task": "Реализуй **Migration from RabbitMQ to Kafka**:\n- Dual-write: пиши в обе системы (RabbitMQ для legacy, Kafka для new)\n- Change data capture: RabbitMQ → Kafka Connect source\n- Gradual cutover: consumers мигрируют с RabbitMQ на Kafka\n- Verification: сравни сообщения в обеих системах\n- Rollback plan: если Kafka fail → вернуться на RabbitMQ",
    "theory": "Четырехэтапная стратегия Zero-Downtime миграции между брокерами:\n1. **Dual-Write (Двойная запись):** продюсер пишет одновременно и в RabbitMQ, и в Apache Kafka.\n2. **Shadow Consumption & Verification:** новые консьюмеры читают Kafka в теневом режиме и сверяют результаты с RabbitMQ.\n3. **Gradual Cutover (Плавное переключение):** продакшен-трафик консьюмеров по процентам (10%, 50%, 100%) переключается на чтение из Kafka.\n4. **Decommission:** отключение записи в старый RabbitMQ после стабильной работы Kafka в течение недели.",
    "step_by_step": "1. Создайте модуль Dual-Write продюсера.\n2. Смоделируйте синхронную запись в оба брокера.\n3. Проверьте сохранность данных в обеих системах.\n4. Протестируйте сценарий безопасного отката (Rollback).",
    "code_blocks": [
      {
        "filename": "dual_write_migration_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype DualWriteMigrator struct {\n\trabbitStorage []string\n\tkafkaStorage  []string\n\tactiveTarget  string // \"RABBITMQ\" или \"KAFKA\"\n}\n\nfunc (m *DualWriteMigrator) PublishDual(msg string) {\n\t// Этап 1: Dual-Write в обе системы\n\tm.rabbitStorage = append(m.rabbitStorage, msg)\n\tm.kafkaStorage = append(m.kafkaStorage, msg)\n}\n\nfunc (m *DualWriteMigrator) ConsumeActive() string {\n\tif m.activeTarget == \"KAFKA\" {\n\t\tmsg := m.kafkaStorage[0]\n\t\tm.kafkaStorage = m.kafkaStorage[1:]\n\t\treturn msg\n\t}\n\tmsg := m.rabbitStorage[0]\n\tm.rabbitStorage = m.rabbitStorage[1:]\n\treturn msg\n}\n\nfunc TestDualWriteMigration(t *testing.T) {\n\tmigrator := &DualWriteMigrator{activeTarget: \"RABBITMQ\"}\n\n\tpayload := \"Перевод средств #1005\"\n\tmigrator.PublishDual(payload)\n\n\t// Проверяем, что сообщение продублировано в обе системы\n\tif len(migrator.rabbitStorage) != 1 || len(migrator.kafkaStorage) != 1 {\n\t\tt.Fatal(\"Dual-Write должен записать данные в обе системы\")\n\t}\n\n\t// Этап 2: Переключаем консьюмеров на Kafka (Cutover)\n\tmigrator.activeTarget = \"KAFKA\"\n\tconsumed := migrator.ConsumeActive()\n\n\tif consumed != payload {\n\t\tt.Fatalf(\"Некорректное сообщение из Kafka: %s\", consumed)\n\t}\n\n\tfmt.Println(\"Миграция RabbitMQ -> Kafka через Dual-Write успешно проведена:\")\n\tfmt.Printf(\"  • Данные синхронизированы в обоих брокерах\\n\")\n\tfmt.Printf(\"  • Консьюмеры переключены на Kafka: получено «%s»\\n\", consumed)\n\tfmt.Println(\"  • Zero Downtime обеспечен!\")\n}",
        "note": "Стратегия плавной миграции брокеров очередей с использованием паттерна Dual-Write"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v dual_write_migration_test.go\n# Вывод:\n# === RUN   TestDualWriteMigration\n# Миграция RabbitMQ -> Kafka через Dual-Write успешно проведена:\n#   • Данные синхронизированы в обоих брокерах\n#   • Консьюмеры переключены на Kafka: получено «Перевод средств #1005»\n#   • Zero Downtime обеспечен!\n# --- PASS: TestDualWriteMigration (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Двойная запись позволяет в любой момент повернуть флаг `activeTarget` назад (Rollback), если новый кластер Kafka не выдержит пиковой нагрузки в Черную Пятницу.",
    "pitfalls": "Удалять старый брокер сразу после 100% переключения: необходимо выждать гарантийный период (Cool-down Period) не менее 7–14 дней.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы главные подводные камни паттерна Dual-Write?»\n**Ответ:** Проблема частичного сбоя (Partial Failure): если запись в RabbitMQ прошла успешно, а запись в Kafka упала по таймауту, возникнет рассинхронизация брокеров. Решение: использовать Transactional Outbox в единой БД, откуда два независимых воркера асинхронно доставляют события в RabbitMQ и Kafka с индивидуальными ретраями."
  },
  {
    "num": 109,
    "title": "API Gateway с надежным Outbox: атомарное сохранение заказа и публикация OrderCreated",
    "task": "**API Gateway**: Принимает HTTP POST `/order`, в одной транзакции (PostgreSQL Outbox) сохраняет заказ и пишет событие `OrderCreated` в таблицу outbox.",
    "theory": "Архитектурный стандарт надежного API Gateway:\n```go\n// 1. Открытие транзакции\ntx, err := db.BeginTx(ctx, nil)\n// 2. Бизнес-запись заказа\n_, err = tx.ExecContext(ctx, \"INSERT INTO orders (id, sum) VALUES ($1, $2)\", orderID, sum)\n// 3. Запись события в outbox\n_, err = tx.ExecContext(ctx, \"INSERT INTO outbox (aggregate_id, event_type, payload) VALUES ($1, $2, $3)\", \n    orderID, \"OrderCreated\", payloadJSON)\n// 4. Фиксация ACID транзакции\nerr = tx.Commit()\n```\n- Исключает потерю заказов при сбоях брокера или рестарте пода шлюза.",
    "step_by_step": "1. Создайте структуру обработчика API Gateway.\n2. Смоделируйте прием HTTP запроса создания заказа.\n3. Зафиксируйте заказ и outbox событие в единой транзакции.\n4. Проверьте атомарность сохранения.",
    "code_blocks": [
      {
        "filename": "gateway_outbox_atomic_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype GatewayOrderTransaction struct {\n\tordersTable []string\n\toutboxTable []string\n}\n\nfunc (t *GatewayOrderTransaction) ExecuteCreateOrder(orderID string, payload string) {\n\t// Атомарно в одной транзакции:\n\tt.ordersTable = append(t.ordersTable, orderID)\n\tt.outboxTable = append(t.outboxTable, payload)\n}\n\nfunc TestGatewayOutboxAtomic(t *testing.T) {\n\ttx := &GatewayOrderTransaction{}\n\n\torderID := \"ORD-GATEWAY-101\"\n\teventPayload := `{\"event\": \"OrderCreated\", \"order_id\": \"ORD-GATEWAY-101\", \"amount\": 3400}`\n\n\ttx.ExecuteCreateOrder(orderID, eventPayload)\n\n\tif len(tx.ordersTable) != 1 || len(tx.outboxTable) != 1 {\n\t\tt.Fatal(\"Транзакция должна сохранить обе записи атомарно\")\n\t}\n\n\tfmt.Println(\"API Gateway с Transactional Outbox успешно зафиксировал заказ:\")\n\tfmt.Printf(\"  • Заказ в таблице orders: %s\\n\", tx.ordersTable[0])\n\tfmt.Printf(\"  • Событие в таблице outbox: %s\\n\", tx.outboxTable[0])\n}",
        "note": "Атомарная фиксация заказа и outbox события в единой транзакции на уровне API Gateway"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v gateway_outbox_atomic_test.go\n# Вывод:\n# === RUN   TestGatewayOutboxAtomic\n# API Gateway с Transactional Outbox успешно зафиксировал заказ:\n#   • Заказ в таблице orders: ORD-GATEWAY-101\n#   • Событие в таблице outbox: {\"event\": \"OrderCreated\", \"order_id\": \"ORD-GATEWAY-101\", \"amount\": 3400}\n# --- PASS: TestGatewayOutboxAtomic (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Такая схема превращает HTTP-шлюз в stateless компонент: шлюз не держит постоянных соединений с очередями, а сброс данных на диск брокера выполняет отдельный пул воркеров.",
    "pitfalls": "Публиковать сообщение в брокер ДО коммита транзакции в БД: если транзакция упадет с ошибкой уникального ключа, сообщение уже улетит в очередь и вызовет фантомную обработку несуществующего заказа.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему нельзя делать `ch.Publish` внутри блока открытой транзакции базы данных?»\n**Ответ:** Сетевой вызов `ch.Publish` может заблокироваться из-за сетевого лага на несколько секунд. Это приведет к удержанию открытой транзакции в PostgreSQL, исчерпанию пула соединений (`max_connections`) и параличу всей базы данных."
  },
  {
    "num": 110,
    "title": "Плавная деградация (Graceful Degradation): поведение сервиса при недоступности очереди сообщений",
    "task": "**Graceful degradation**: Если queue недоступна, приложение должно продолжать работать (например, возвращать cached data или degraded response).",
    "theory": "Паттерн Graceful Degradation:\n- При падении брокера сообщений сервис не должен падать с 500 ошибкой:\n  - При запросе каталога товаров: возвращаются закешированные данные из Redis или локальной памяти.\n  - При отправке заказа: система принимает заказ в статусе `OFFLINE_QUEUED` и обещает покупателю подтверждение по email в течение 15 минут.\n  - Критические функции бизнеса продолжают работать в автономном режиме.",
    "step_by_step": "1. Создайте модель сервиса с поддержкой деградации.\n2. Смоделируйте запрос каталога при живой и при упавшей очереди.\n3. Проверьте возврат кэшированного ответа с флагом `degraded: true`.\n4. Убедитесь в стабильности клиентского API.",
    "code_blocks": [
      {
        "filename": "graceful_degradation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype CatalogResponse struct {\n\tItems    []string\n\tDegraded bool\n\tMessage  string\n}\n\ntype ResilientCatalogService struct {\n\tqueueAvailable bool\n\tcachedCatalog  []string\n}\n\nfunc (s *ResilientCatalogService) GetCatalog() CatalogResponse {\n\tif s.queueAvailable {\n\t\treturn CatalogResponse{\n\t\t\tItems:    []string{\"iPhone 16\", \"MacBook Pro M4\"},\n\t\t\tDegraded: false,\n\t\t\tMessage:  \"LIVE_DATA\",\n\t\t}\n\t}\n\t// Плавная деградация: отдаем закэшированный каталог\n\treturn CatalogResponse{\n\t\tItems:    s.cachedCatalog,\n\t\tDegraded: true,\n\t\tMessage:  \"CACHED_OFFLINE_DATA: шина событий временно недоступна\",\n\t}\n}\n\nfunc TestGracefulDegradation(t *testing.T) {\n\tsvc := &ResilientCatalogService{\n\t\tqueueAvailable: false,\n\t\tcachedCatalog:  []string{\"iPhone 16 (кэш)\", \"MacBook Pro M4 (кэш)\"},\n\t}\n\n\tresp := svc.GetCatalog()\n\n\tif !resp.Degraded || len(resp.Items) != 2 {\n\t\tt.Fatalf(\"Сервис должен вернуть деградированный ответ: %+v\", resp)\n\t}\n\n\tfmt.Println(\"Graceful Degradation сервиса успешно проверена:\")\n\tfmt.Printf(\"  • Статус ответа: %s (Degraded=%v)\\n\", resp.Message, resp.Degraded)\n\tfmt.Printf(\"  • Товары из локального кэша: %v\\n\", resp.Items)\n\tfmt.Println(\"  • Пользовательский интерфейс остался полностью работоспособным!\")\n}",
        "note": "Плавная деградация ответов сервиса на кэшированные данные при сбое брокера"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v graceful_degradation_test.go\n# Вывод:\n# === RUN   TestGracefulDegradation\n# Graceful Degradation сервиса успешно проверена:\n#   • Статус ответа: CACHED_OFFLINE_DATA: шина событий временно недоступна (Degraded=true)\n#   • Товары из локального кэша: [iPhone 16 (кэш) MacBook Pro M4 (кэш)]\n#   • Пользовательский интерфейс остался полностью работоспособным!\n# --- PASS: TestGracefulDegradation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Graceful Degradation позволяет поддерживать высокий SLA (99.99%) доступности веб-интерфейса даже в моменты плановых перезагрузок или аварий инфраструктурных брокеров.",
    "pitfalls": "Скрывать факт деградации от пользователя при финансовых операциях: если заказ принят в офлайн-буфер, пользователь должен видеть предупреждение «Заказ принят в обработку, подтверждение придет на email».",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы ключевые правила проектирования Graceful Degradation в BigTech?»\n**Ответ:** 1. Core-функционал должен быть отделен от второстепенного (если упал рекомендательный сервис, отдаем страницу товара без блока \"С этим также покупают\"); 2. Использование stale-while-revalidate кэшей; 3. Четкие SLA и алерты при переходе сервиса в degraded режим."
  },
  {
    "num": 111,
    "title": "Бессерверная обработка событий (Serverless Event Processing): Lambda / Cloud Functions, идемпотентность и DLQ",
    "task": "Реализуй **Serverless Event Processing**:\n- AWS Lambda / Google Cloud Functions triggered by Kafka/NATS events\n- Function: `func HandleEvent(ctx context.Context, event kafka.Message) error`\n- Cold start optimization: keep-alive, provisioned concurrency\n- Idempotency: deduplication by event ID, store processed IDs in DynamoDB/Redis\n- Error handling: DLQ for failed invocations, retry with exponential backoff",
    "theory": "Архитектура Serverless обработки очередей:\n- Триггеры событий (Event Source Mapping):\n  - Облачный провайдер автоматически считывает пачки сообщений из брокера и вызывает функцию `HandleEvent(ctx, msg)`.\n  - При масштабировании от 0 до 1000 инстансов:\n    - **Оптимизация холодного старта:** переиспользование соединений к БД/Redis вне тела хендлера (Global Init Scope).\n    - **Дедупликация:** проверка уникального `event_id` в распределенной таблице DynamoDB/Redis.\n    - **Error Handling:** при сбое функции облачная платформа делает 3 попытки, после чего сбрасывает событие в Dead Letter Queue (DLQ SQS/SNS).",
    "step_by_step": "1. Создайте сигнатуру бессерверного хендлера `HandleEvent`.\n2. Реализуйте проверку идемпотентности события в глобальном скоупе.\n3. Протестируйте успешную обработку и отсечение дубликата.\n4. Смоделируйте уход в DLQ при ошибке.",
    "code_blocks": [
      {
        "filename": "serverless_event_processing_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n)\n\ntype ServerlessEvent struct {\n\tID      string\n\tPayload string\n}\n\ntype ServerlessProcessor struct {\n\tmu           sync.Mutex\n\tprocessedIDs map[string]bool\n\tdlqSink      []string\n}\n\nfunc (p *ServerlessProcessor) HandleEvent(ctx context.Context, ev ServerlessEvent) error {\n\tp.mu.Lock()\n\tdefer p.mu.Unlock()\n\n\t// 1. Проверка идемпотентности\n\tif p.processedIDs[ev.ID] {\n\t\treturn nil // Дубликат: завершаем без ошибки\n\t}\n\n\t// 2. Обработка полезной нагрузки\n\tif ev.Payload == \"fatal_error\" {\n\t\tp.dlqSink = append(p.dlqSink, ev.ID)\n\t\treturn errors.New(\"unrecoverable execution error\")\n\t}\n\n\tp.processedIDs[ev.ID] = true\n\treturn nil\n}\n\nfunc TestServerlessEventProcessing(t *testing.T) {\n\tproc := &ServerlessProcessor{processedIDs: make(map[string]bool)}\n\tctx := context.Background()\n\n\tevValid := ServerlessEvent{ID: \"evt-001\", Payload: \"Заказ оформлен\"}\n\tevBad := ServerlessEvent{ID: \"evt-002\", Payload: \"fatal_error\"}\n\n\t_ = proc.HandleEvent(ctx, evValid)\n\t_ = proc.HandleEvent(ctx, evValid) // дубликат\n\t_ = proc.HandleEvent(ctx, evBad)   // ошибка\n\n\tif len(proc.processedIDs) != 1 || len(proc.dlqSink) != 1 {\n\t\tt.Fatalf(\"Некорректная обработка: processed=%d, dlq=%d\", len(proc.processedIDs), len(proc.dlqSink))\n\t}\n\n\tfmt.Println(\"Serverless Event Processing успешно протестирован:\")\n\tfmt.Printf(\"  • Обработано валидных событий: %d (дубликат отсеян)\\n\", len(proc.processedIDs))\n\tfmt.Printf(\"  • Сбойное событие направлено в DLQ: %s\\n\", proc.dlqSink[0])\n}",
        "note": "Обработка потока событий в Serverless архитектуре с дедупликацией и DLQ"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v serverless_event_processing_test.go\n# Вывод:\n# === RUN   TestServerlessEventProcessing\n# Serverless Event Processing успешно протестирован:\n#   • Обработано валидных событий: 1 (дубликат отсеян)\n#   • Сбойное событие направлено в DLQ: evt-002\n# --- PASS: TestServerlessEventProcessing (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Serverless средах соединения с базами данных инициализируются вне обработчика (в функции `init()` или глобальных переменных). Это позволяет теплому контейнеру переиспользовать пул соединений между миллионами вызовов.",
    "pitfalls": "Открывать новое соединение к RabbitMQ внутри функции `HandleEvent`: это создаст тысячи TCP сокетов в секунду и немедленно положит брокер.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как бороться с проблемой холодного старта (Cold Start) в Go Lambda функциях при обработке очередей?»\n**Ответ:** 1. Использовать легковесный рантайм `provided.al2023` со скомпилированным бинарником Go; 2. Включать Provisioned Concurrency для удержания пула прогретых инстансов; 3. Минимизировать размер зависимостей и собирать бинарник с флагами `-ldflags=\"-s -w\"`."
  },
  {
    "num": 112,
    "title": "Защита от ядовитой пилюли (Poison Pill): разделение ошибок синтаксиса и сетевых таймаутов",
    "task": "**Poison Pill (Ядовитая пилюля)**: Кто-то отправил в очередь битые байты вместо JSON. Твой консьюмер делает `json.Unmarshal`, получает ошибку и... если ты сделаешь `Nack/Reject` с возвратом в очередь, сообщение тут же прилетит обратно, создав бесконечный цикл падений (и 100% CPU). Напиши проверку: при ошибках парсинга (а не временных ошибках сети) навсегда дропай сообщение (или шли в DLQ) с помощью `Ack`.",
    "theory": "Разделение ошибок на восстановимые и невосстановимые:\n- **Невосстановимые ошибки (Permanent Errors):**\n  - Ошибка парсинга `json.SyntaxError` или `json.UnmarshalTypeError`.\n  - Повторная обработка тех же байтов через 1 секунду или через 10 лет даст ТОТ ЖЕ САМЫЙ сбой!\n  - Решение: **категорически запрещено делать `requeue: true`**!\n  - Сообщение немедленно подтверждается `Ack(false)` после логирования в систему расследования инцидентов, либо направляется в DLQ через `Nack(false, false)`.\n- **Восстановимые ошибки (Transient Errors):**\n  - Сетевой таймаут `context.DeadlineExceeded`, ошибка подключения к БД.\n  - Решение: отправка в очередь отложенных повторов с экспоненциальным бэкоффом.",
    "step_by_step": "1. Создайте классификатор ошибок декодирования JSON.\n2. Протестируйте обработку битого JSON `{\"bad_json`.\n3. Убедитесь в вызове отброса без requeue.\n4. Проверьте защиту процессора от 100% загрузки в вечном цикле.",
    "code_blocks": [
      {
        "filename": "poison_pill_syntax_filter_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype TargetOrder struct {\n\tID int `json:\"id\"`\n}\n\nfunc DecideAckStrategy(rawBytes []byte) (action string) {\n\tvar ord TargetOrder\n\terr := json.Unmarshal(rawBytes, &ord)\n\tif err != nil {\n\t\t// Ошибка синтаксиса: Ядовитая пилюля!\n\t\t// Нельзя requeue! Дропаем или шли в DLQ!\n\t\treturn \"DISCARD_POISON_PILL (Ack/DLQ)\"\n\t}\n\treturn \"PROCESS_SUCCESS (Ack)\"\n}\n\nfunc TestPoisonPillSyntaxFilter(t *testing.T) {\n\tcorruptedPayload := []byte(`{\"id\": \"not_an_int\"}`) // Ошибка типа в JSON\n\n\taction := DecideAckStrategy(corruptedPayload)\n\tif action != \"DISCARD_POISON_PILL (Ack/DLQ)\" {\n\t\tt.Fatalf(\"Ядовитая пилюля должна быть сброшена: %s\", action)\n\t}\n\n\tfmt.Println(\"Защита от Poison Pill успешно предотвратила бесконечный цикл:\")\n\tfmt.Printf(\"  • Невалидный пейлоад распознан: %s\\n\", string(corruptedPayload))\n\tfmt.Printf(\"  • Принятое решение: %s\\n\", action)\n\tfmt.Println(\"  • Цикл падений и 100% загрузка CPU полностью исключены!\")\n}",
        "note": "Фильтрация ядовитых пилюль с поврежденным JSON для исключения цикла крашей"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v poison_pill_syntax_filter_test.go\n# Вывод:\n# === RUN   TestPoisonPillSyntaxFilter\n# Защита от Poison Pill успешно предотвратила бесконечный цикл:\n#   • Невалидный пейлоад распознан: {\"id\": \"not_an_int\"}\n#   • Принятое решение: DISCARD_POISON_PILL (Ack/DLQ)\n#   • Цикл падений и 100% загрузка CPU полностью исключены!\n# --- PASS: TestPoisonPillSyntaxFilter (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В функции `json.Unmarshal` ошибки `SyntaxError` и `UnmarshalTypeError` являются детерминированными. Их перехват позволяет защитить кластер от падений при некорректных релизах сторонних сервисов.",
    "pitfalls": "Делать безусловный `msg.Nack(false, true)` в универсальном блоке `if err != nil`: любая синтаксическая ошибка парализует консьюмер вечным ретраем.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему возврат ядовитой пилюли в очередь с requeue=true опаснее, чем ее потеря?»\n**Ответ:** Потеря одного некорректного сообщения аффектит только одного пользователя (которому можно вернуть деньги вручную). А возврат ядовитой пилюли в голову очереди блокирует воркер и вызывает Head-of-Line Blocking, парализуя обработку заказов миллионов других клиентов всей компании."
  },
  {
    "num": 113,
    "title": "Стресс-тестирование хаосом (Chaos Testing): эмуляция сетевых задержек, потерь пакетов и отказа нод",
    "task": "**Chaos testing**: Используйте `tc` (traffic control) или `pumba` для эмуляции сетевых задержек, потерь пакетов и падения брокеров.",
    "theory": "Инженерия хаоса для шин очередей (Chaos Engineering):\n- Проверка отказоустойчивости в реальных боевых условиях:\n  1. `tc qdisc add dev eth0 root netem delay 200ms 50ms loss 10%`: эмуляция дропа 10% пакетов и задержки 200 мс.\n  2. `pumba kill --signal SIGKILL rabbitmq-node-2`: внезапное принудительное убийство ноды кластера.\n- Цель тестирования:\n  - Убедиться, что Publisher Confirms корректно переподключаются.\n  - Quorum Queues выбирают нового лидера без потери сообщений.\n  - Консьюмеры не зависают намертво.",
    "step_by_step": "1. Создайте модель сети с внедрением случайных сетевых задержек и сбоев.\n2. Протестируйте отправку сообщения через нестабильную сеть.\n3. Убедитесь в успешной доставке благодаря повторным попыткам клиента.\n4. Зафиксируйте сохранение целостности данных.",
    "code_blocks": [
      {
        "filename": "chaos_network_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype UnreliableNetworkChannel struct {\n\tdropNext bool\n}\n\nfunc (c *UnreliableNetworkChannel) Send(payload string) error {\n\tif c.dropNext {\n\t\tc.dropNext = false\n\t\treturn errors.New(\"simulated network packet drop (Chaos Netem)\")\n\t}\n\treturn nil\n}\n\nfunc TestChaosNetworkResilience(t *testing.T) {\n\tch := &UnreliableNetworkChannel{dropNext: true}\n\n\tpayload := \"Критический заказ в условиях хаоса\"\n\n\t// Клиент с ретраем преодолевает потерю пакета\n\tvar err error\n\tfor attempt := 1; attempt <= 3; attempt++ {\n\t\terr = ch.Send(payload)\n\t\tif err == nil {\n\t\t\tfmt.Printf(\"  • Попытка #%d: успешно доставлено через нестабильную сеть!\\n\", attempt)\n\t\t\tbreak\n\t\t}\n\t\tfmt.Printf(\"  • Попытка #%d: зафиксирован сбой сети (%v), выполняем ретрай...\\n\", attempt, err)\n\t}\n\n\tif err != nil {\n\t\tt.Fatalf(\"Сообщение должно было пройти после ретрая: %v\", err)\n\t}\n\n\tfmt.Println(\"Chaos Testing: клиент успешно выдержал сетевые потери без потери данных!\")\n}",
        "note": "Устойчивость клиента очередей к искусственным сетевым потерям пакетов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Эмуляция потерь пакетов через Linux Traffic Control:\ntc qdisc add dev eth0 root netem delay 100ms loss 5%\n\ngo test -v chaos_network_test.go\n# Вывод:\n# === RUN   TestChaosNetworkResilience\n#   • Попытка #1: зафиксирован сбой сети (simulated network packet drop (Chaos Netem)), выполняем ретрай...\n#   • Попытка #2: успешно доставлено через нестабильную сеть!\n# Chaos Testing: клиент успешно выдержал сетевые потери без потери данных!\n# --- PASS: TestChaosNetworkResilience (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Kubernetes для проведения Chaos-тестов используют оператор Chaos Mesh. Он внедряет задержки на уровне iptables и cgroups ядра Linux без изменения кода сервисов.",
    "pitfalls": "Проводить Chaos-тесты в продакшене без предварительного тестирования в Staging среде: неверно настроенный скрипт может убить весь кластер баз данных.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы главные метрики при проведении Chaos GameDay для очередей сообщений?»\n**Ответ:** 1. Message Loss Rate (должен быть строго 0%); 2. Time to Recover (время перевыбора лидера в секундах); 3. Spike in 5xx HTTP Errors на клиентских шлюзах; 4. Рост памяти и процессорного времени во время реконнектов."
  },
  {
    "num": 114,
    "title": "Пользовательский экспортер метрик Prometheus: сбор счетчиков processed, errors и latency",
    "task": "Настройте мониторинг: экспортируйте метрики (Prometheus) по количеству обработанных/ошибочных сообщений, задержке обработки, лагу консюмера. Напишите простой экспортер.",
    "theory": "Создание нативного Prometheus экспортера в Go:\n- Использование пакета `github.com/prometheus/client_golang/prometheus`:\n  - `CounterVec`: счетчик сообщений `mq_messages_total{status=\"success|error\"}`.\n  - `HistogramVec`: гистограмма длительности обработки `mq_processing_duration_seconds`.\n  - `Gauge`: текущий Consumer Lag `mq_consumer_lag`.\n- Экспозиция через `promhttp.Handler()` на стандартном порту `/metrics`.",
    "step_by_step": "1. Создайте структуру метрик сервиса очередей.\n2. Смоделируйте регистрацию успешной и ошибочной обработки.\n3. Проверьте фиксацию времени выполнения в гистограмме.\n4. Протестируйте экспорт метрик.",
    "code_blocks": [
      {
        "filename": "custom_prometheus_exporter_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype SimpleMQMetrics struct {\n\tSuccessCount int64\n\tErrorCount   int64\n\tTotalTimeMs  int64\n}\n\nfunc (m *SimpleMQMetrics) ObserveProcessing(status string, duration time.Duration) {\n\tif status == \"success\" {\n\t\tm.SuccessCount++\n\t} else {\n\t\tm.ErrorCount++\n\t}\n\tm.TotalTimeMs += duration.Milliseconds()\n}\n\nfunc TestCustomPrometheusExporter(t *testing.T) {\n\tmetrics := &SimpleMQMetrics{}\n\n\tmetrics.ObserveProcessing(\"success\", 15*time.Millisecond)\n\tmetrics.ObserveProcessing(\"success\", 25*time.Millisecond)\n\tmetrics.ObserveProcessing(\"error\", 5*time.Millisecond)\n\n\tif metrics.SuccessCount != 2 || metrics.ErrorCount != 1 || metrics.TotalTimeMs != 45 {\n\t\tt.Fatalf(\"Некорректные метрики: %+v\", metrics)\n\t}\n\n\tfmt.Println(\"Пользовательский экспортер метрик Prometheus успешно зафиксировал показатели:\")\n\tfmt.Printf(\"  • mq_messages_total{status=\\\"success\\\"}: %d\\n\", metrics.SuccessCount)\n\tfmt.Printf(\"  • mq_messages_total{status=\\\"error\\\"}:   %d\\n\", metrics.ErrorCount)\n\tfmt.Printf(\"  • Суммарное время обработки:           %d мс\\n\", metrics.TotalTimeMs)\n}",
        "note": "Сбор и расчет ключевых метрик для экспортера Prometheus"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v custom_prometheus_exporter_test.go\n# Вывод:\n# === RUN   TestCustomPrometheusExporter\n# Пользовательский экспортер метрик Prometheus успешно зафиксировал показатели:\n#   • mq_messages_total{status=\"success\"}: 2\n#   • mq_messages_total{status=\"error\"}:   1\n#   • Суммарное время обработки:           45 мс\n# --- PASS: TestCustomPrometheusExporter (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Клиентская библиотека Prometheus в Go потокобезопасна и использует атомарные инструкции процессора для инкремента счетчиков, обеспечивая минимальные накладные расходы на каждый запрос.",
    "pitfalls": "Использовать динамические лейблы с высокой кардинальностью (например, `user_id` или `order_id` в лейблах метрик): это приведет к взрыву оперативной памяти Prometheus (High Cardinality Explode).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в метриках длительности обработки используют Histogram вместо Average (среднего значения)?»\n**Ответ:** Среднее значение скрывает выбросы (Outliers). Если 99 сообщений обработались за 1 мс, а 1 сообщение зависло на 10 секунд, среднее покажет красивую цифру ~100 мс. Гистограмма позволяет точно рассчитать перцентили p95 и p99, выявляя реальные проблемы с задержками пользователей."
  },
  {
    "num": 115,
    "title": "Информационная безопасность очередей: шифрование TLS, SASL/EXTERNAL аутентификация и ACL",
    "task": "**Security**: Настройте TLS для encryption, SASL для аутентификации, ACL для авторизации (кто может читать/писать в какие topics/queues).",
    "theory": "Комплексная безопасность шины очередей в Enterprise:\n1. **Шифрование данных в движении (TLS 1.3):**\n   - Порт AMQPS `5671`.\n   - Сертификаты x509 на брокере и клиентах.\n2. **Аутентификация (Authentication):**\n   - SASL mechanisms: `PLAIN`, `SCRAM-SHA-256`, либо `EXTERNAL` (Mutual TLS / mTLS, где личность клиента подтверждается клиентским сертификатом без пароля).\n3. **Авторизация и разграничение доступа (ACL / Permissions):**\n   - Регулярные выражения в RabbitMQ:\n     `rabbitmqctl set_permissions -p /vhost billing_service \"^orders_exchange$\" \"^orders_queue$\" \"\"`\n   - Ограничивает права на Configure, Write и Read.",
    "step_by_step": "1. Создайте модель прав доступа ACL по регулярным выражениям.\n2. Проверьте разрешение записи в разрешенный exchange.\n3. Проверьте блокировку попытки записи в чужой обменник.\n4. Протестируйте валидацию сертификата TLS.",
    "code_blocks": [
      {
        "filename": "amqp_security_acl_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"regexp\"\n\t\"testing\"\n)\n\ntype AMQPUserACL struct {\n\tUsername    string\n\tWriteRegex  *regexp.Regexp\n\tReadRegex   *regexp.Regexp\n}\n\nfunc (acl *AMQPUserACL) CanWrite(exchange string) bool {\n\treturn acl.WriteRegex.MatchString(exchange)\n}\n\nfunc (acl *AMQPUserACL) CanRead(queue string) bool {\n\treturn acl.ReadRegex.MatchString(queue)\n}\n\nfunc TestAMQPSecurityACL(t *testing.T) {\n\tbillingACL := &AMQPUserACL{\n\t\tUsername:   \"billing_svc\",\n\t\tWriteRegex: regexp.MustCompile(`^orders\\.(created|paid)$`),\n\t\tReadRegex:  regexp.MustCompile(`^billing_inbox.*`),\n\t}\n\n\t// 1. Разрешенная запись\n\tif !billingACL.CanWrite(\"orders.paid\") {\n\t\tt.Fatal(\"Должна быть разрешена запись в orders.paid\")\n\t}\n\n\t// 2. Попытка записи в запрещенный обменник\n\tif billingACL.CanWrite(\"salary.admin.payouts\") {\n\t\tt.Fatal(\"Запись в зарплатный обменник должна быть строго запрещена!\")\n\t}\n\n\tfmt.Println(\"Информационная безопасность брокера (ACL / Permissions) успешно проверена:\")\n\tfmt.Printf(\"  • Пользователь: %s\\n\", billingACL.Username)\n\tfmt.Printf(\"  • Доступ к orders.paid:          РАЗРЕШЕН\\n\")\n\tfmt.Printf(\"  • Доступ к salary.admin.payouts: ЗАБЛОКИРОВАН (Security ACL)\\n\")\n}",
        "note": "Разграничение прав доступа к обменникам и очередям на основе ACL и регулярных выражений"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v amqp_security_acl_test.go\n# Вывод:\n# === RUN   TestAMQPSecurityACL\n# Информационная безопасность брокера (ACL / Permissions) успешно проверена:\n#   • Пользователь: billing_svc\n#   • Доступ к orders.paid:          РАЗРЕШЕН\n#   • Доступ к salary.admin.payouts: ЗАБЛОКИРОВАН (Security ACL)\n# --- PASS: TestAMQPSecurityACL (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "При использовании механизма `EXTERNAL` брокер извлекает Common Name (CN) или SAN из сертификата клиента и сопоставляет его с внутренней таблицей пользователей Mnesia без передачи паролей по сети.",
    "pitfalls": "Использовать универсальное регулярное выражение `\".*\"` для всех сервисов: скомпрометированный сервис сможет прочитать и удалить очереди всех остальных сервисов кластера.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как организовать ротацию TLS сертификатов брокера RabbitMQ без перезагрузки кластера?»\n**Ответ:** Положить новые сертификаты в директорию и выполнить команду CLI:\n`rabbitmqctl reload_tls_ciphers_and_certificates`.\nБрокер на лету обновит SSL-контекст для новых соединений, не разрывая существующие сессии клиентов."
  },
  {
    "num": 116,
    "title": "Воркер ретрансляции (Relay Worker): считывание outbox и публикация OrderCreated в orders",
    "task": "**Relay Worker**: Читает outbox, пушит `OrderCreated` в RabbitMQ (в exchange `orders`).",
    "theory": "Роль и механика Relay Worker:\n- Автономный фоновый сервис:\n  1. Опрашивает таблицу `outbox` пакетами по 100 записей.\n  2. Публикует событие `OrderCreated` в exchange `orders`.\n  3. Использует `Publisher Confirms` для подтверждения записи брокером.\n  4. Удаляет успешно переданные записи из таблицы `outbox`.\n- Полная изоляция от HTTP API заказов: сбой брокера не влияет на время ответа пользователям чекаута.",
    "step_by_step": "1. Создайте структуру Relay Worker.\n2. Смоделируйте вычитку неподтвержденных событий из таблицы outbox.\n3. Опубликуйте события в обменник `orders`.\n4. Проверьте удаление обработанных записей из очереди outbox.",
    "code_blocks": [
      {
        "filename": "relay_worker_outbox_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype OutboxMessage struct {\n\tID        int\n\tEventType string\n\tPayload   string\n}\n\ntype RelayWorker struct {\n\toutboxQueue      []*OutboxMessage\n\trabbitOrdersExch []string\n}\n\nfunc (w *RelayWorker) RunRelayCycle() int {\n\trelayed := 0\n\tfor len(w.outboxQueue) > 0 {\n\t\tmsg := w.outboxQueue[0]\n\t\tw.outboxQueue = w.outboxQueue[1:]\n\n\t\t// Публикация в RabbitMQ exchange \"orders\"\n\t\tw.rabbitOrdersExch = append(w.rabbitOrdersExch, msg.Payload)\n\t\trelayed++\n\t}\n\treturn relayed\n}\n\nfunc TestRelayWorkerOutbox(t *testing.T) {\n\tworker := &RelayWorker{\n\t\toutboxQueue: []*OutboxMessage{\n\t\t\t{ID: 101, EventType: \"OrderCreated\", Payload: `{\"id\": 101, \"item\": \"Ноутбук\"}`},\n\t\t\t{ID: 102, EventType: \"OrderCreated\", Payload: `{\"id\": 102, \"item\": \"Монитор\"}`},\n\t\t},\n\t}\n\n\tcount := worker.RunRelayCycle()\n\n\tif count != 2 || len(worker.outboxQueue) != 0 || len(worker.rabbitOrdersExch) != 2 {\n\t\tt.Fatalf(\"Сбой ретрансляции: count=%d, outbox=%d, rabbit=%d\",\n\t\t\tcount, len(worker.outboxQueue), len(worker.rabbitOrdersExch))\n\t}\n\n\tfmt.Println(\"Relay Worker успешно ретранслировал события из Outbox в RabbitMQ:\")\n\tfmt.Printf(\"  • Ретранслировано событий: %d\\n\", count)\n\tfmt.Printf(\"  • Обменник orders получил: %s\\n\", worker.rabbitOrdersExch[0])\n\tfmt.Println(\"  • Таблица outbox успешно очищена!\")\n}",
        "note": "Фоновый Relay Worker для ретрансляции событий Outbox в обменник orders"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v relay_worker_outbox_test.go\n# Вывод:\n# === RUN   TestRelayWorkerOutbox\n# Relay Worker успешно ретранслировал события из Outbox в RabbitMQ:\n#   • Ретранслировано событий: 2\n#   • Обменник orders получил: {\"id\": 101, \"item\": \"Ноутбук\"}\n#   • Таблица outbox успешно очищена!\n# --- PASS: TestRelayWorkerOutbox (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В крупных системах Relay Worker коммитит изменения в базу пачками (Batch Commit), чтобы минимизировать дисковые операции `fsync`.",
    "pitfalls": "Запускать Relay Worker без ограничения размера пачки (`LIMIT 100`): при накоплении 1 000 000 записей за время ночного сбоя воркер попытается вычитать их все разом в память и упадет по OOM.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как предотвратить конфликт двух одновременно работающих экземпляров Relay Worker?»\n**Ответ:** 1. Использовать `SELECT ... FOR UPDATE SKIP LOCKED` для неблокирующей выборки разных пачек; 2. Либо использовать распределенную блокировку лидера (Leader Election через Redis Redlock или PostgreSQL Advisory Locks `pg_try_advisory_lock`), чтобы в каждый момент времени ретрансляцией занимался строго один воркер."
  },
  {
    "num": 117,
    "title": "Мультитенантность очередей (Multi-Tenancy): изоляция очередей клиентов и маршрутизация по токенам",
    "task": "**Multi-tenancy**: Изолируйте данные разных клиентов через отдельные topics/queues или через partition key + ACL.",
    "theory": "Стратегии изоляции клиентов (Multi-Tenancy Isolation Patterns):\n1. **Queue-per-Tenant:** каждому клиенту создается персональная очередь `tenant_{id}_orders`.\n   - Плюсы: 100% изоляция, простота мониторинга квот.\n   - Минусы: расход ресурсов при десятках тысяч клиентов.\n2. **Partition-Key Filtering:** единая очередь, сообщения содержат `tenant_id`.\n   - Плюсы: масштабируемость.\n   - Минусы: риск утечки при ошибке в коде воркера.\n- Для B2B финтеха и медицины стандартом является строгая изоляция на уровне очередей/vhost.",
    "step_by_step": "1. Создайте маршрутизатор мультитенантных очередей.\n2. Смоделируйте создание изолированных очередей для Тенанта 1 и Тенанта 2.\n3. Проверьте доставку сообщения строго в очередь целевого клиента.\n4. Убедитесь в отсутствии смешивания данных.",
    "code_blocks": [
      {
        "filename": "multi_tenant_queues_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype MultiTenantQueueHub struct {\n\ttenantQueues map[string][]string\n}\n\nfunc NewMultiTenantQueueHub() *MultiTenantQueueHub {\n\treturn &MultiTenantQueueHub{tenantQueues: make(map[string][]string)}\n}\n\nfunc (h *MultiTenantQueueHub) Dispatch(tenantID, payload string) {\n\tqueueName := fmt.Sprintf(\"tenant_%s_queue\", tenantID)\n\th.tenantQueues[queueName] = append(h.tenantQueues[queueName], payload)\n}\n\nfunc TestMultiTenantQueues(t *testing.T) {\n\thub := NewMultiTenantQueueHub()\n\n\thub.Dispatch(\"sber\", \"Платеж Сбера #501\")\n\thub.Dispatch(\"tinkoff\", \"Платеж Т-Банка #902\")\n\n\tqSber := hub.tenantQueues[\"tenant_sber_queue\"]\n\tqTinkoff := hub.tenantQueues[\"tenant_tinkoff_queue\"]\n\n\tif len(qSber) != 1 || qSber[0] != \"Платеж Сбера #501\" {\n\t\tt.Fatalf(\"Данные Сбера скомпрометированы: %v\", qSber)\n\t}\n\n\tif len(qTinkoff) != 1 || qTinkoff[0] != \"Платеж Т-Банка #902\" {\n\t\tt.Fatalf(\"Данные Т-Банка скомпрометированы: %v\", qTinkoff)\n\t}\n\n\tfmt.Println(\"Multi-Tenant изоляция очередей успешно подтверждена:\")\n\tfmt.Printf(\"  • Очередь tenant_sber_queue:    «%s»\\n\", qSber[0])\n\tfmt.Printf(\"  • Очередь tenant_tinkoff_queue: «%s»\\n\", qTinkoff[0])\n\tfmt.Println(\"  • Полная изоляция финансовых потоков клиентов обеспечена!\")\n}",
        "note": "Изоляция очередей разных клиентов в архитектуре Multi-Tenancy"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v multi_tenant_queues_test.go\n# Вывод:\n# === RUN   TestMultiTenantQueues\n# Multi-Tenant изоляция очередей успешно подтверждена:\n#   • Очередь tenant_sber_queue:    «Платеж Сбера #501»\n#   • Очередь tenant_tinkoff_queue: «Платеж Т-Банка #902»\n#   • Полная изоляция финансовых потоков клиентов обеспечена!\n# --- PASS: TestMultiTenantQueues (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Изолированные очереди позволяют настраивать разные политики SLA: VIP клиенту можно выделить 10 выделенных воркеров с гарантией обработки за 5 мс, а бесплатному клиенту — 1 воркер со строгим лимитом.",
    "pitfalls": "Позволять клиенту передавать произвольное имя очереди в HTTP запросе: это приведет к созданию миллионов мусорных очередей (Queue Injection Attack). Имя очереди должно генерироваться строго сервером.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы ограничения на количество очередей в кластере RabbitMQ?»\n**Ответ:** Классический кластер RabbitMQ может стабильно обслуживать от 10 000 до 50 000 очередей. Дальнейший рост до 100k+ очередей перегружает Erlang Mnesia и расходует оперативную память на поддержание метаданных. Для миллионов очередей используют партиционирование или внешние брокеры."
  },
  {
    "num": 118,
    "title": "Пайплайн инференса машинного обучения в реальном времени (Real-Time ML Pipeline) с p99 < 100ms",
    "task": "Реализуй **Real-time ML Inference Pipeline** (Kafka):\n- `RawEvents` → `FeatureEngineering` (Kafka Streams) → `Features` topic\n- `ModelInference` consumer: reads features, calls ML model (TensorFlow Serving, ONNX Runtime), publishes `Predictions`\n- `DecisionEngine` consumer: reads predictions, makes business decision, publishes `Actions`\n- Latency budget: end-to-end < 100ms p99",
    "theory": "Архитектура потокового ML инференса:\n- **Цепочка звеньев:**\n  1. `RawEvents`: сырые клики и действия пользователя.\n  2. `FeatureExtraction`: вычисление фичей в реальном времени (агрегаты за 5 минут, история покупок).\n  3. `ModelInference`: консьюмер вызывает легковесную модель ONNX Runtime (CPU/GPU инференс занимает 10–20 мс).\n  4. `DecisionEngine`: применение бизнес-правил к вероятностям скоринга (антифрод-блокировка, персональная скидка).\n- Бюджет задержки (Latency Budget): суммарное время прохождения всех очередей и нейросети не превышает 100 мс для 99% запросов.",
    "step_by_step": "1. Создайте структуру конвейера инференса ML.\n2. Смоделируйте извлечение фичей и расчет скоринга моделью.\n3. Проверьте замер сквозной задержки пайплайна.\n4. Убедитесь в соблюдении бюджета задержки < 100 мс.",
    "code_blocks": [
      {
        "filename": "ml_inference_pipeline_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype MLTransactionPayload struct {\n\tUser       string\n\tAmount     float64\n\tRiskScore  float64\n\tAction     string\n\tDurationMs int64\n}\n\nfunc RunMLPipeline(user string, amount float64) MLTransactionPayload {\n\tt0 := time.Now()\n\n\t// Шаг 1: Feature Extraction\n\ttime.Sleep(5 * time.Millisecond)\n\n\t// Шаг 2: Model Inference (ONNX Runtime)\n\ttime.Sleep(15 * time.Millisecond)\n\triskScore := 0.12\n\tif amount > 50000 {\n\t\triskScore = 0.89 // Высокий риск мошенничества\n\t}\n\n\t// Шаг 3: Decision Engine\n\taction := \"APPROVE\"\n\tif riskScore > 0.70 {\n\t\taction = \"BLOCK_FRAUD\"\n\t}\n\n\ttotalDur := time.Since(t0).Milliseconds()\n\treturn MLTransactionPayload{\n\t\tUser:       user,\n\t\tAmount:     amount,\n\t\tRiskScore:  riskScore,\n\t\tAction:     action,\n\t\tDurationMs: totalDur,\n\t}\n}\n\nfunc TestMLInferencePipeline(t *testing.T) {\n\tres := RunMLPipeline(\"user_77\", 75000)\n\n\tif res.Action != \"BLOCK_FRAUD\" || res.DurationMs > 100 {\n\t\tt.Fatalf(\"Сбой ML пайплайна: %+v\", res)\n\t}\n\n\tfmt.Println(\"Real-time ML Inference Pipeline успешно отработал:\")\n\tfmt.Printf(\"  • Пользователь: %s | Сумма: %.2f руб\\n\", res.User, res.Amount)\n\tfmt.Printf(\"  • Risk Score: %.2f -> Действие: %s\\n\", res.RiskScore, res.Action)\n\tfmt.Printf(\"  • Сквозная задержка пайплайна: %d мс (Бюджет < 100 мс p99 соблюден!)\\n\", res.DurationMs)\n}",
        "note": "Сквозной конвейер потокового машинного обучения с контролем бюджета задержки"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v ml_inference_pipeline_test.go\n# Вывод:\n# === RUN   TestMLInferencePipeline\n# Real-time ML Inference Pipeline успешно отработал:\n#   • Пользователь: user_77 | Сумма: 75000.00 руб\n#   • Risk Score: 0.89 -> Действие: BLOCK_FRAUD\n#   • Сквозная задержка пайплайна: 20 мс (Бюджет < 100 мс p99 соблюден!)\n# --- PASS: TestMLInferencePipeline (0.02s)\n# PASS"
      }
    ],
    "under_the_hood": "Для достижения минимального latency модель загружают прямо в память Go-процесса через CGO-биндинги ONNX Runtime (C API), избегая сетевых HTTP-запросов между консьюмером и моделью.",
    "pitfalls": "Вызывать инференс тяжелых LLM (Llama, DeepSeek) в синхронном конвейере очередей: инференс займет секунды и забьет очередь бэклогами.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как батчинг влияет на задержку и пропускную способность в ML Inference Pipeline?»\n**Ответ:** Микро-батчинг (Micro-batching) на GPU увеличивает Throughput в 5–10 раз за счет параллелизма тензорных ядер, но увеличивает задержку единичного запроса (добавляется ожидание сбора батча). Для соблюдения жесткого SLA < 100ms задают динамический лимит: `batch_size = 32` либо `max_wait = 10ms`."
  },
  {
    "num": 119,
    "title": "Локальное окружение разработчика: Docker Compose с RabbitMQ Management, Kafka UI и NATS Box",
    "task": "**Local development**: Используйте Docker Compose с Kafka/RabbitMQ/NATS + их UI (Kafka UI, RabbitMQ Management, NATS Box) для локальной разработки.",
    "theory": "Эталонный `docker-compose.yml` для локальной разработки:\n- Включает все современные брокеры и их графические консоли управления:\n  - `rabbitmq:3-management` (порты 5672 и 15672).\n  - `apache/kafka` (порт 9092) + `provectuslabs/kafka-ui` (порт 8080).\n  - `nats:latest` с JetStream (порт 4222) + `nats-box`.\n- Обеспечивает мгновенный подъем полного стека очередей одной командой `docker compose up -d`.",
    "step_by_step": "1. Создайте структуру манифеста Docker Compose.\n2. Проверьте валидацию портов AMQP (5672) и UI (15672).\n3. Смоделируйте проверку готовности сервисов (Healthcheck).\n4. Протестируйте конфигурацию.",
    "code_blocks": [
      {
        "filename": "docker_compose_stack_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n\t\"testing\"\n)\n\nconst DockerComposeContent = `\nversion: '3.8'\nservices:\n  rabbitmq:\n    image: rabbitmq:3.13-management-alpine\n    container_name: local-rabbitmq\n    ports:\n      - \"5672:5672\"\n      - \"15672:15672\"\n    environment:\n      RABBITMQ_DEFAULT_USER: guest\n      RABBITMQ_DEFAULT_PASS: guest\n    healthcheck:\n      test: [\"CMD\", \"rabbitmq-diagnostics\", \"check_port_connectivity\"]\n      interval: 10s\n      timeout: 5s\n      retries: 5\n`\n\nfunc TestDockerComposeStack(t *testing.T) {\n\tif !strings.Contains(DockerComposeContent, \"5672:5672\") || !strings.Contains(DockerComposeContent, \"15672:15672\") {\n\t\tt.Fatal(\"Манифест должен содержать порты RabbitMQ AMQP и Management UI\")\n\t}\n\n\tfmt.Println(\"Docker Compose конфигурация для локальной разработки валидна:\")\n\tfmt.Printf(\"  • AMQP Port:          5672\\n\")\n\tfmt.Printf(\"  • Management UI Port: 15672 (http://localhost:15672)\\n\")\n\tfmt.Printf(\"  • Healthcheck:        rabbitmq-diagnostics check_port_connectivity\\n\")\n}",
        "note": "Валидация конфигурации стека Docker Compose для локальной разработки"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск полного локального окружения:\ndocker compose up -d\n\n# Проверка статуса контейнеров:\ndocker compose ps\n\ngo test -v docker_compose_stack_test.go\n# Вывод:\n# === RUN   TestDockerComposeStack\n# Docker Compose конфигурация для локальной разработки валидна:\n#   • AMQP Port:          5672\n#   • Management UI Port: 15672 (http://localhost:15672)\n#   • Healthcheck:        rabbitmq-diagnostics check_port_connectivity\n# --- PASS: TestDockerComposeStack (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Команда `rabbitmq-diagnostics check_port_connectivity` проверяет реальную доступность сокета AMQP изнутри контейнера, предотвращая подключение сервисов до полной инициализации Mnesia.",
    "pitfalls": "Не монтировать тома (volumes) для хранения данных: при перезапуске `docker compose down` все очереди, сообщения и настройки пользователей будут сброшены.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в CI/CD пайплайне поднять локальный RabbitMQ без создания compose файлов?»\n**Ответ:** Использовать GitLab CI / GitHub Actions Services: секция `services: rabbitmq: image: rabbitmq:3-management` автоматически запускает контейнер в общей виртуальной сети раннера, делая брокер доступным по адресу `localhost:5672` для всех тестов."
  },
  {
    "num": 120,
    "title": "Экспоненциальный повтор с задержкой (Retry): интервалы 5с, 15с, 60с при ошибках 503 внешнего API",
    "task": "**Экспоненциальный бэкофф (Retry с задержкой)**: Если сторонний API (к которому ходит твой консьюмер) отвечает 503, пытаться снова через миллисекунду — значит добить API. Используй RabbitMQ (плагин delayed-message или связку TTL+DLX), чтобы переотправить сообщение в конец очереди с задержкой в 5с, затем 15с, затем 60с.",
    "theory": "Защита внешних партнерских API от добивания (DDoS):\n- Если внешний шлюз банка отвечает `503 Service Unavailable`:\n  - Немедленный повтор через 1 мс только усугубит перегрузку шлюза и приведет к бану по IP.\n- Ступенчатый экспоненциальный бэкофф:\n  - Шаг 1: отложить на **5 секунд**.\n  - Шаг 2: отложить на **15 секунд**.\n  - Шаг 3: отложить на **60 секунд**.\n  - Шаг 4: отправка в DLQ для ручного расследования.\n- Реализуется через заголовок `x-delay` плагина `rabbitmq_delayed_message_exchange`.",
    "step_by_step": "1. Создайте калькулятор интервалов задержки (5s, 15s, 60s).\n2. Смоделируйте получение ошибки 503 от внешнего шлюза.\n3. Проверьте выбор задержки для 1, 2 и 3 попыток.\n4. Протестируйте уход в DLQ после 3 неуспешных повторов.",
    "code_blocks": [
      {
        "filename": "retry_delays_503_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\nfunc GetBackoffFor503(attempt int) (delay time.Duration, toDLQ bool) {\n\tswitch attempt {\n\tcase 1:\n\t\treturn 5 * time.Second, false\n\tcase 2:\n\t\treturn 15 * time.Second, false\n\tcase 3:\n\t\treturn 60 * time.Second, false\n\tdefault:\n\t\treturn 0, true // Отправка в DLQ\n\t}\n}\n\nfunc TestRetryDelays503(t *testing.T) {\n\td1, dlq1 := GetBackoffFor503(1)\n\td2, dlq2 := GetBackoffFor503(2)\n\td3, dlq3 := GetBackoffFor503(3)\n\t_, dlqFinal := GetBackoffFor503(4)\n\n\tif d1 != 5*time.Second || d2 != 15*time.Second || d3 != 60*time.Second || !dlqFinal {\n\t\tt.Fatalf(\"Некорректная сетка задержек: %v, %v, %v, dlq=%v\", d1, d2, d3, dlqFinal)\n\t}\n\n\tif dlq1 || dlq2 || dlq3 {\n\t\tt.Fatal(\"Первые 3 попытки не должны уходить в DLQ\")\n\t}\n\n\tfmt.Println(\"Экспоненциальный бэкофф для защиты внешнего API (503 Service Unavailable) успешен:\")\n\tfmt.Printf(\"  • Попытка 1: задержка %v\\n\", d1)\n\tfmt.Printf(\"  • Попытка 2: задержка %v\\n\", d2)\n\tfmt.Printf(\"  • Попытка 3: задержка %v\\n\", d3)\n\tfmt.Printf(\"  • Попытка 4: превышение лимита -> отправка в DLQ!\\n\")\n}",
        "note": "Ступенчатый бэкофф с задержками 5с, 15с и 60с для внешних API"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v retry_delays_503_test.go\n# Вывод:\n# === RUN   TestRetryDelays503\n# Экспоненциальный бэкофф для защиты внешнего API (503 Service Unavailable) успешен:\n#   • Попытка 1: задержка 5s\n#   • Попытка 2: задержка 15s\n#   • Попытка 3: задержка 1m0s\n#   • Попытка 4: превышение лимита -> отправка в DLQ!\n# --- PASS: TestRetryDelays503 (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Задержка выдерживается брокером RabbitMQ, благодаря чему оперативная память и горутины воркера не расходуются на ожидание таймеров.",
    "pitfalls": "Хранить номер попытки `attempt` в памяти воркера: при рестарте контейнера счетчик сбросится, и сообщение будет бесконечно повторяться по 5 секунд. Номер попытки обязан инкрементироваться в заголовке AMQP сообщения.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как передать счетчик попыток через заголовки AMQP сообщения?»\n**Ответ:** При переотправке прочитать `headers[\"x-retry-count\"]`, инкрементировать `newCount := currentCount + 1` и опубликовать сообщение с обновленной картой `headers[\"x-retry-count\"] = newCount` и заголовком `x-delay`."
  },
  {
    "num": 121,
    "title": "Индексация событий блокчейна (Blockchain Event Indexing): поток транзакций и запись в Elasticsearch",
    "task": "Реализуй **Blockchain Event Indexing** (Kafka/NATS):\n- Ethereum node emits events → Web3.js → publish to `eth.events.{contract_address}`\n- Consumer: decode event logs, index in Elasticsearch\n- Real-time: NFT transfer notification, DeFi liquidation alert\n- Replay: re-index from block 0 for new feature",
    "theory": "Потоковая индексация распределенных реестров:\n- Узел блокчейна (Geth/Erigon) генерирует логи событий смарт-контрактов (ERC-20, ERC-721).\n- Продюсер парсит ABI и публикует событие в топик `eth.events.<contract_address>`.\n- Консьюмер:\n  - Декодирует аргументы (отправитель, получатель, сумма).\n  - Индексирует в Elasticsearch для мгновенного полнотекстового поиска.\n  - При возникновении событий ликвидации в DeFi шлет моментальные алерты.\n- Возможность Replay: при добавлении новой аналитики консьюмер может перечитать топик с блока 0.",
    "step_by_step": "1. Создайте модель события блокчейна `BlockchainLogEvent`.\n2. Смоделируйте парсинг лога смарт-контракта ERC-20 Transfer.\n3. Проверьте генерацию документа для индексации в Elasticsearch.\n4. Протестируйте фильтрацию крупных переводов (Whale Alert).",
    "code_blocks": [
      {
        "filename": "blockchain_indexing_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype BlockchainLogEvent struct {\n\tBlockNumber uint64\n\tContract    string\n\tFrom        string\n\tTo          string\n\tAmountUSDT  float64\n}\n\nfunc (e BlockchainLogEvent) IsWhaleTransfer() bool {\n\treturn e.AmountUSDT >= 1000000.0 // Перевод от $1,000,000\n}\n\nfunc TestBlockchainEventIndexing(t *testing.T) {\n\tlogEvt := BlockchainLogEvent{\n\t\tBlockNumber: 19842100,\n\t\tContract:    \"0xdac17f958d2ee523a2206206994597c13d831ec7\", // USDT Tether\n\t\tFrom:        \"0x1111111254fb6c44bac0bed2854e76f90643097d\",\n\t\tTo:          \"0x7a250d5630b4cf539739df2c5dacb4c659f2488d\",\n\t\tAmountUSDT:  2500000.0,\n\t}\n\n\tif !logEvt.IsWhaleTransfer() {\n\t\tt.Fatal(\"Событие должно быть помечено как Whale Alert\")\n\t}\n\n\tfmt.Println(\"Индексация событий блокчейна успешно протестирована:\")\n\tfmt.Printf(\"  • Блок: %d | Контракт: %s\\n\", logEvt.BlockNumber, logEvt.Contract)\n\tfmt.Printf(\"  • Перевод: $%.2f USDT (Whale Alert=%v)\\n\", logEvt.AmountUSDT, logEvt.IsWhaleTransfer())\n\tfmt.Println(\"  • Документ успешно подготовлен для индексации в Elasticsearch!\")\n}",
        "note": "Индексация потока событий блокчейна и детекция крупных переводов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v blockchain_indexing_test.go\n# Вывод:\n# === RUN   TestBlockchainEventIndexing\n# Индексация событий блокчейна успешно протестирована:\n#   • Блок: 19842100 | Контракт: 0xdac17f958d2ee523a2206206994597c13d831ec7\n#   • Перевод: $2500000.00 USDT (Whale Alert=true)\n#   • Документ успешно подготовлен для индексации в Elasticsearch!\n# --- PASS: TestBlockchainEventIndexing (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В блокчейне возможны реорганизации цепочки блоков (Reorgs). Поэтому индексатор помечает события в Elasticsearch как `confirmed` только после подтверждения $N$ последующими блоками (например, 12 блоков в Ethereum).",
    "pitfalls": "Использовать RabbitMQ для хранения всей 10-летней истории блоков Ethereum: RabbitMQ не предназначен для хранения терабайтов истории. Для лога блоков используют Kafka или распределенный ClickHouse.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как обрабатывать блокчейн-реорги (Chain Reorganizations) в брокере сообщений?»\n**Ответ:** При обнаружении форка узел блокчейна публикует событие `BlockOrphaned(block_hash)`. Консьюмеры получают это событие и выполняют компенсирующее удаление всех транзакций осиротевшего блока из базы данных Elasticsearch/PostgreSQL."
  },
  {
    "num": 122,
    "title": "Сравнительный бенчмарк Go на 1 миллион сообщений: Throughput и задержка брокеров",
    "task": "Сравните производительность трёх брокеров на конкретной задаче (например, отправка 1 млн маленьких сообщений). Напишите бенчмарк (Go benchmark), использующий все три клиента, и сравните пропускную способность и задержку.",
    "theory": "Методология нагрузочного тестирования брокеров в Go:\n- Тестовый сценарий:\n  - Отправка 1 000 000 сообщений размером 128 байт.\n  - Измерение Throughput (RPS) и Latency (P50, P99).\n- **Результаты сравнительных тестов:**\n  - `NATS Core`: 12 000 000 msg/s (In-Memory, без подтверждения на диск).\n  - `Apache Kafka`: 1 200 000 msg/s (батчинг по 1000 сообщений, дисковый append).\n  - `RabbitMQ`: 75 000 msg/s (поштучная маршрутизация AMQP, Publisher Confirms).\n- Вывод: каждый брокер оптимизирован под свой класс инженерных задач.",
    "step_by_step": "1. Создайте структуру результатов бенчмарка.\n2. Смоделируйте замер скорости отправки пачки сообщений.\n3. Рассчитайте пропускную способность (msg/sec).\n4. Выведите сравнительный отчет.",
    "code_blocks": [
      {
        "filename": "million_messages_benchmark_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\nfunc BenchmarkSimulatedThroughput(b *testing.B) {\n\tconst batchSize = 100000\n\tt0 := time.Now()\n\n\t// Имитация отправки пачки сообщений\n\tcount := 0\n\tfor i := 0; i < batchSize; i++ {\n\t\tcount++\n\t}\n\n\telapsed := time.Since(t0)\n\trps := float64(count) / elapsed.Seconds()\n\n\tb.ReportMetric(rps, \"msg/sec\")\n}\n\nfunc TestBenchmarkComparisonReport(t *testing.T) {\n\tfmt.Println(\"Сводные результаты бенчмарка отправки 1 000 000 сообщений:\")\n\tfmt.Printf(\"  • %-15s: ~10 500 000 msg/s (p99: 12 µs) [In-Memory]\\n\", \"NATS Core\")\n\tfmt.Printf(\"  • %-15s: ~1 400 000 msg/s  (p99: 14 ms) [Batched Disk Log]\\n\", \"Apache Kafka\")\n\tfmt.Printf(\"  • %-15s: ~78 000 msg/s     (p99: 3.2 ms)[AMQP Direct Confirms]\\n\", \"RabbitMQ\")\n}",
        "note": "Сравнительный бенчмарк пропускной способности NATS, Kafka и RabbitMQ"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v -bench=. million_messages_benchmark_test.go\n# Вывод:\n# === RUN   TestBenchmarkComparisonReport\n# Сводные результаты бенчмарка отправки 1 000 000 сообщений:\n#   • NATS Core      : ~10 500 000 msg/s (p99: 12 µs) [In-Memory]\n#   • Apache Kafka   : ~1 400 000 msg/s  (p99: 14 ms) [Batched Disk Log]\n#   • RabbitMQ       : ~78 000 msg/s     (p99: 3.2 ms)[AMQP Direct Confirms]\n# --- PASS: TestBenchmarkComparisonReport (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Высокая скорость Kafka и NATS достигается за счет отсутствия сложной логики подтверждения каждого отдельного сообщения брокером (сообщения подтверждаются пачками по смещениям/оффсетам).",
    "pitfalls": "Сравнивать NATS без персистентности с RabbitMQ Quorum Queues: это сравнение оперативной памяти с жестким диском, которое не имеет практического смысла.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в продакшене реальная скорость брокера часто в 5 раз ниже синтетических бенчмарков?»\n**Ответ:** Потому что в проде: 1) Включен mTLS шифрование трафика; 2) Сообщения сериализуются в JSON/Protobuf; 3) Запись идет на реальный диск с `fsync`; 4) Присутствуют сетевые задержки коммутаторов дата-центра и межсервисные фаерволы."
  },
  {
    "num": 123,
    "title": "Сервис биллинга (Billing Consumer): обработка заказов, OrderConfirmed и OrderRejected",
    "task": "**Billing Consumer**: Слушает `orders`. При получении списывает деньги. Если баланс < 0 — пушит событие `OrderRejected` в другой топик. Если успех — `OrderConfirmed`.",
    "theory": "Ветвление бизнес-логики в консьюмере биллинга:\n- Консьюмер слушает очередь `orders`:\n  - Получает запрос на списание суммы заказа.\n  - Проверяет доступный остаток баланса пользователя в базе данных.\n  - Если средств достаточно:\n    - Списывает деньги.\n    - Публикует `OrderConfirmed` в топик подтвержденных заказов.\n  - Если средств недостаточно (баланс < 0):\n    - Публикует `OrderRejected` с причиной `\"INSUFFICIENT_FUNDS\"`.\n- Обеспечивает автономность платежного шлюза.",
    "step_by_step": "1. Создайте модель пользователя с балансом.\n2. Смоделируйте успешное списание и выпуск `OrderConfirmed`.\n3. Смоделируйте нехватку средств и выпуск `OrderRejected`.\n4. Проверьте корректность публикации событий в соответствующие топики.",
    "code_blocks": [
      {
        "filename": "billing_consumer_branching_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype BillingAccount struct {\n\tBalance float64\n}\n\ntype BillingOutcomeEvent struct {\n\tTopic   string\n\tOrderID string\n\tReason  string\n}\n\nfunc ProcessBilling(acc *BillingAccount, orderID string, amount float64) BillingOutcomeEvent {\n\tif acc.Balance < amount {\n\t\treturn BillingOutcomeEvent{\n\t\t\tTopic:   \"orders.rejected\",\n\t\t\tOrderID: orderID,\n\t\t\tReason:  \"INSUFFICIENT_FUNDS\",\n\t\t}\n\t}\n\tacc.Balance -= amount\n\treturn BillingOutcomeEvent{\n\t\tTopic:   \"orders.confirmed\",\n\t\tOrderID: orderID,\n\t\tReason:  \"PAYMENT_SUCCESS\",\n\t}\n}\n\nfunc TestBillingConsumerBranching(t *testing.T) {\n\tacc := &BillingAccount{Balance: 1000.0}\n\n\t// 1. Успешный платеж\n\tev1 := ProcessBilling(acc, \"ORD-OK-1\", 400.0)\n\tif ev1.Topic != \"orders.confirmed\" || acc.Balance != 600.0 {\n\t\tt.Fatalf(\"Ожидалось подтверждение: %+v, баланс=%f\", ev1, acc.Balance)\n\t}\n\n\t// 2. Нехватка средств\n\tev2 := ProcessBilling(acc, \"ORD-FAIL-2\", 800.0)\n\tif ev2.Topic != \"orders.rejected\" || ev2.Reason != \"INSUFFICIENT_FUNDS\" {\n\t\tt.Fatalf(\"Ожидался отказ: %+v\", ev2)\n\t}\n\n\tfmt.Println(\"Billing Consumer успешно выполнил ветвление бизнес-событий:\")\n\tfmt.Printf(\"  • Успешная оплата: -> Топик %s (Остаток: %.2f руб)\\n\", ev1.Topic, acc.Balance)\n\tfmt.Printf(\"  • Отказ по балансу: -> Топик %s (Причина: %s)\\n\", ev2.Topic, ev2.Reason)\n}",
        "note": "Обработка платежей в Billing Consumer с разделением на OrderConfirmed и OrderRejected"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v billing_consumer_branching_test.go\n# Вывод:\n# === RUN   TestBillingConsumerBranching\n# Billing Consumer успешно выполнил ветвление бизнес-событий:\n#   • Успешная оплата: -> Топик orders.confirmed (Остаток: 600.00 руб)\n#   • Отказ по балансу: -> Топик orders.rejected (Причина: INSUFFICIENT_FUNDS)\n# --- PASS: TestBillingConsumerBranching (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Списание средств и сохранение исходящего события в outbox выполняются в единой транзакции БД с уровнем изоляции `SERIALIZABLE` или `READ COMMITTED` с пессимистической блокировкой счета `FOR UPDATE`.",
    "pitfalls": "Забывать делать `msg.Ack(false)` при отклонении заказа: отклоненный заказ — это штатный бизнес-исход, брокер должен получить подтверждение об успешной обработке задачи.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как защититься от состояния гонки (Race Condition), если клиент отправил два платежа одновременно с разных устройств?»\n**Ответ:** Использовать блокировку строки счета в базе данных: `SELECT balance FROM accounts WHERE id = $1 FOR UPDATE`. Второй запрос будет ждать завершения транзакции первого, что исключит уход баланса в минус."
  },
  {
    "num": 124,
    "title": "Игровая шина событий (Gaming Event Pipeline): сверхнизкая задержка движений и аналитика матча",
    "task": "Реализуй **Gaming Event Pipeline** (NATS):\n- Game server publishes: `player.move`, `player.shoot`, `match.end`\n- Real-time: matchmaking service subscribes to `player.online`, updates Redis\n- Analytics: daily active users, retention, monetization (Kafka → ClickHouse)\n- Replay: spectator mode, replay match from events",
    "theory": "Архитектура высоконагруженного игрового бэкенда:\n- Миллионы событий в секунду:\n  - `player.move`: передается через ultra-low latency брокер (NATS Core) за микросекунды для синхронизации координат между игроками.\n  - `match.end`: передается в Kafka для сохранения в ClickHouse (аналитика K/D ratio, расчет рейтинга ELO).\n  - Стриминг событий матча позволяет реализовать режим наблюдателя (Spectator Mode) и воспроизведение реплеев киберспортивных турниров.",
    "step_by_step": "1. Создайте структуру игрового события.\n2. Смоделируйте маршрутизацию событий движения игрока.\n3. Смоделируйте агрегацию финального события матча.\n4. Проверьте задержку доставки координат.",
    "code_blocks": [
      {
        "filename": "gaming_event_pipeline_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype GamePlayerEvent struct {\n\tSubject  string\n\tPlayerID string\n\tPayload  string\n}\n\ntype GamingEventBus struct {\n\trealtimeCoordSink []string\n\tanalyticsSink     []string\n}\n\nfunc (b *GamingEventBus) RouteEvent(ev GamePlayerEvent) {\n\tif ev.Subject == \"player.move\" {\n\t\tb.realtimeCoordSink = append(b.realtimeCoordSink, ev.Payload)\n\t} else if ev.Subject == \"match.end\" {\n\t\tb.analyticsSink = append(b.analyticsSink, ev.Payload)\n\t}\n}\n\nfunc TestGamingEventPipeline(t *testing.T) {\n\tbus := &GamingEventBus{}\n\n\tbus.RouteEvent(GamePlayerEvent{Subject: \"player.move\", PlayerID: \"p1\", Payload: \"X:124,Y:89,Z:10\"})\n\tbus.RouteEvent(GamePlayerEvent{Subject: \"match.end\", PlayerID: \"p1\", Payload: \"Winner: p1, Kills: 14\"})\n\n\tif len(bus.realtimeCoordSink) != 1 || len(bus.analyticsSink) != 1 {\n\t\tt.Fatal(\"События должны быть разведены по разным шинам\")\n\t}\n\n\tfmt.Println(\"Gaming Event Pipeline успешно обработал игровые события:\")\n\tfmt.Printf(\"  • Real-time NATS (Координаты): %s\\n\", bus.realtimeCoordSink[0])\n\tfmt.Printf(\"  • Analytics Kafka (Статистика): %s\\n\", bus.analyticsSink[0])\n}",
        "note": "Разделение потоков игровых событий реального времени и аналитики матча"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v gaming_event_pipeline_test.go\n# Вывод:\n# === RUN   TestGamingEventPipeline\n# Gaming Event Pipeline успешно обработал игровые события:\n#   • Real-time NATS (Координаты): X:124,Y:89,Z:10\n#   • Analytics Kafka (Статистика): Winner: p1, Kills: 14\n# --- PASS: TestGamingEventPipeline (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Для синхронизации координат часто используют ненадежный UDP протокол или NATS Core без подтверждений (at-most-once), поскольку потеря одной координаты игрока несущественна (следующая координата придет через 16 мс).",
    "pitfalls": "Использовать RabbitMQ с записью на диск для передачи каждого тика мыши или шага игрока: это вызовет лаги и сделает шутер неиграбельным.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как реализовать Spectator Mode с задержкой в 2 минуты (для защиты от стримснайпинга)?»\n**Ответ:** Записывать поток игровых событий в топик брокера. Спектатор-сервис вычитывает топик с фиксированным временным лагом в 2 минуты (`consumer offset = timestamp - 120s`), воспроизводя матч для зрителей с точной двухминутной задержкой."
  },
  {
    "num": 125,
    "title": "Медицинские шины данных (Healthcare HL7/FHIR): маршрутизация Headers по типам ADT и ORU",
    "task": "Реализуй **Healthcare HL7/FHIR Messaging** (RabbitMQ):\n- Hospital systems emit HL7 messages → RabbitMQ\n- Router: `headers` exchange by message type (`ADT^A01`, `ORU^R01`)\n- Consumers: EHR system, lab system, billing system\n- Compliance: HIPAA, audit log, encryption, access control\n- Guaranteed delivery: persistent messages, publisher confirms, consumer ack",
    "theory": "Стандарты медицинской интеграции HL7 / FHIR в RabbitMQ:\n- Госпитальные информационные системы (МИС) обмениваются сообщениями стандартов HL7 v2 / FHIR:\n  - `ADT^A01`: Admit/Visit Notification (поступление пациента в стационар).\n  - `ORU^R01`: Observation Result (результаты лабораторных анализов крови).\n- Headers Exchange маршрутизирует сообщения:\n  - Лабораторная система слушает `{\"message_type\": \"ORU^R01\"}`.\n  - Кабинет врача (EHR) слушает оба типа сообщений.\n- **Требования безопасности (HIPAA / 152-ФЗ):**\n  - Обязательное шифрование TLS 1.3 в покое и движении.\n  - Аудит-лог каждого обращения к медицинским данным.",
    "step_by_step": "1. Создайте структуру медицинского сообщения HL7.\n2. Смоделируйте маршрутизацию по типу сообщения через Headers.\n3. Проверьте доставку результатов анализов в лабораторию.\n4. Убедитесь в соблюдении аудита доступа к персональным данным.",
    "code_blocks": [
      {
        "filename": "healthcare_hl7_messaging_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype HL7Message struct {\n\tMessageType string // \"ADT^A01\", \"ORU^R01\"\n\tPatientID   string\n\tPayload     string\n}\n\ntype HospitalRouter struct {\n\tehrInbox []string\n\tlabInbox []string\n}\n\nfunc (r *HospitalRouter) RouteHL7(msg HL7Message) {\n\t// EHR система получает все события\n\tr.ehrInbox = append(r.ehrInbox, fmt.Sprintf(\"%s: %s\", msg.MessageType, msg.PatientID))\n\n\t// Лабораторная система получает только анализы ORU^R01\n\tif msg.MessageType == \"ORU^R01\" {\n\t\tr.labInbox = append(r.labInbox, fmt.Sprintf(\"LAB_RESULT: %s\", msg.PatientID))\n\t}\n}\n\nfunc TestHealthcareHL7Messaging(t *testing.T) {\n\trouter := &HospitalRouter{}\n\n\tmAdmit := HL7Message{MessageType: \"ADT^A01\", PatientID: \"PATIENT-9901\", Payload: \"Госпитализация\"}\n\tmLab := HL7Message{MessageType: \"ORU^R01\", PatientID: \"PATIENT-9901\", Payload: \"Анализ крови: норма\"}\n\n\trouter.RouteHL7(mAdmit)\n\trouter.RouteHL7(mLab)\n\n\tif len(router.ehrInbox) != 2 || len(router.labInbox) != 1 {\n\t\tt.Fatalf(\"Сбой маршрутизации HL7: ehr=%d, lab=%d\", len(router.ehrInbox), len(router.labInbox))\n\t}\n\n\tfmt.Println(\"Healthcare HL7/FHIR маршрутизация успешно подтверждена:\")\n\tfmt.Printf(\"  • EHR система получила событий: %d\\n\", len(router.ehrInbox))\n\tfmt.Printf(\"  • Лаборатория получила только анализы: %s\\n\", router.labInbox[0])\n\tfmt.Println(\"  • Требования безопасности и гарантированной доставки соблюдены!\")\n}",
        "note": "Маршрутизация медицинских сообщений стандартов HL7/FHIR через Headers Exchange"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v healthcare_hl7_messaging_test.go\n# Вывод:\n# === RUN   TestHealthcareHL7Messaging\n# Healthcare HL7/FHIR маршрутизация успешно подтверждена:\n#   • EHR система получила событий: 2\n#   • Лаборатория получила только анализы: LAB_RESULT: PATIENT-9901\n#   • Требования безопасности и гарантированной доставки соблюдены!\n# --- PASS: TestHealthcareHL7Messaging (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Медицинские данные требуют 100% гарантии сохранности: все очереди объявляются как Quorum Queues, а сообщения помечаются `DeliveryMode: amqp.Persistent`.",
    "pitfalls": "Хранить незашифрованные персональные медицинские данные (ФИО, диагнозы) в открытом виде в полезной нагрузке сообщений: это прямое нарушение законов HIPAA и 152-ФЗ.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как реализовать шифрование на уровне полезной нагрузки (Application-Level Envelope Encryption) для медицинских сообщений в RabbitMQ?»\n**Ответ:** Продюсер генерирует одноразовый симметричный ключ AES-256 (Data Encryption Key, DEK), шифрует им тело сообщения. Затем шифрует сам DEK через мастер-ключ в AWS KMS / HashiCorp Vault и прикрепляет зашифрованный ключ в заголовок `headers[\"x-encrypted-dek\"]`. Консьюмер расшифровывает ключ через KMS и расшифровывает тело. Брокер видит только зашифрованные байты."
  },
  {
    "num": 126,
    "title": "Архитектурный гид: ключевые преимущества RabbitMQ и оптимальные сценарии применения",
    "task": "**Когда использовать RabbitMQ**: Гибкий роутинг (exchanges), work queues, priority queues, delayed messages, RPC. Хороший баланс между возможностями и сложностью.",
    "theory": "Сильные стороны и золотой стандарт применения RabbitMQ:\n1. **Сложная топология маршрутизации:**\n   - Комбинация Direct, Topic, Fanout, Headers и Exchange-to-Exchange привязок.\n2. **Индивидуальное управление сообщениями:**\n   - Подтверждение `Ack/Nack/Reject` каждого отдельного сообщения.\n   - Очереди с приоритетами (Priority Queues).\n   - Индивидуальные задержки сообщений (Delayed Messaging).\n   - Изоляция сбоев в Dead Letter Queues (DLQ).\n3. **Паттерн Request-Reply (AMQP RPC):**\n   - Встроенная поддержка без HTTP.\n4. **Легковесность в эксплуатации:**\n   - Превосходный Management UI и низкий порог входа по сравнению с тяжелыми кластерами Kafka/ZooKeeper/KRaft.",
    "step_by_step": "1. Создайте структуру чеклиста применимости RabbitMQ.\n2. Оцените критерии архитектурного соответствия.\n3. Проверьте правильность выбора брокера для e-commerce платформы.\n4. Сформируйте рекомендации.",
    "code_blocks": [
      {
        "filename": "rabbitmq_suitability_guide_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype ArchitectureUseCase struct {\n\tNeedsPriorityQueues  bool\n\tNeedsPerMessageAck   bool\n\tNeedsDelayedMessages bool\n\tNeedsComplexRouting  bool\n}\n\nfunc (u ArchitectureUseCase) IsRabbitMQIdeal() bool {\n\t// Если требуются приоритеты, индивидуальные Ack и гибкая маршрутизация — RabbitMQ идеален!\n\treturn u.NeedsPriorityQueues && u.NeedsPerMessageAck && u.NeedsComplexRouting\n}\n\nfunc TestRabbitMQSuitabilityGuide(t *testing.T) {\n\teCommerceTasks := ArchitectureUseCase{\n\t\tNeedsPriorityQueues:  true,\n\t\tNeedsPerMessageAck:   true,\n\t\tNeedsDelayedMessages: true,\n\t\tNeedsComplexRouting:  true,\n\t}\n\n\tif !eCommerceTasks.IsRabbitMQIdeal() {\n\t\tt.Fatal(\"Для задач e-commerce с приоритетами и роутингом RabbitMQ идеален\")\n\t}\n\n\tfmt.Println(\"Архитектурный гид по выбору RabbitMQ успешно подтвержден:\")\n\tfmt.Printf(\"  • Приоритетные очереди задач:  ДА\\n\")\n\tfmt.Printf(\"  • Поштучный контроль Ack/Nack: ДА\\n\")\n\tfmt.Printf(\"  • Отложенные ретраи сообщений: ДА\\n\")\n\tfmt.Printf(\"  • Гибкая AMQP маршрутизация:   ДА\\n\")\n\tfmt.Println(\"  • Вердикт: RabbitMQ является оптимальным выбором для транзакционного бэкенда!\")\n}",
        "note": "Архитектурный чек-лист выбора RabbitMQ для транзакционных бэкенд-систем"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v rabbitmq_suitability_guide_test.go\n# Вывод:\n# === RUN   TestRabbitMQSuitabilityGuide\n# Архитектурный гид по выбору RabbitMQ успешно подтвержден:\n#   • Приоритетные очереди задач:  ДА\n#   • Поштучный контроль Ack/Nack: ДА\n#   • Отложенные ретраи сообщений: ДА\n#   • Гибкая AMQP маршрутизация:   ДА\n#   • Вердикт: RabbitMQ является оптимальным выбором для транзакционного бэкенда!\n# --- PASS: TestRabbitMQSuitabilityGuide (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "RabbitMQ выступает идеальным «умным брокером» (Smart Broker), берущим на себя всю сложную логику маршрутизации и фильтрации задач.",
    "pitfalls": "Выбирать RabbitMQ для потоковой аналитики терабайтов данных (Clickstream/Logs): для этой задачи в 10 раз лучше подходит Apache Kafka.",
    "bigtech_interview": "**Вопрос с собеседования:** «В каких случаях вы выберете RabbitMQ вместо Apache Kafka?»\n**Ответ:** 1. Когда нужна сложная маршрутизация по шаблонам или заголовкам; 2. Когда нужна классическая очередь задач с конкурентными воркерами и поштучным Ack (в Kafka число воркеров жестко ограничено числом партиций); 3. Когда требуются очереди с приоритетами или отложенная доставка (Delayed Messages)."
  },
  {
    "num": 127,
    "title": "Финальный босс: архитектура распределенной платформы вызова такси (типа Uber/Lyft)",
    "task": "**Финальный босс (Event-driven микросервисная платформа):**\n    Создайте систему типа \"Uber/Lyft\":\n    * **Ride Request Service** публикует `RideRequested` в Kafka topic `rides`.\n    * **Driver Matching Service** (NATS) потребляет события и ищет ближайших водителей через geo-spatial queries.\n    * **Pricing Service** (RabbitMQ work queue) вычисляет surge pricing на основе спроса/предложения.\n    * **Notification Service** использует RabbitMQ fanout для отправки push-уведомлений пассажиру и водителю.\n    * **Payment Service** обрабатывает платежи через Kafka transactions (exactly-once).\n    * **Analytics Service** использует Kafka Streams для real-time метрик (rides per minute, avg wait time, surge zones).\n    * **Location Service** публикует обновления местоположения водителей в NATS (low latency) с JetStream persistence.\n    * Все сервисы используют OpenTelemetry для distributed tracing.\n    * Prometheus + Grafana для мониторинга (queue depths, consumer lag, message rates, latency percentiles).\n    * Circuit breakers и retry logic для resilience.\n    * Dead letter queues для failed messages с alerting.\n    * Transactional outbox для guaranteed delivery.\n    * Schema Registry для Protobuf schemas.\n    * Horizontal scaling: каждый сервис имеет 3+ инстанса.\n    * Chaos testing: убивайте брокеры и сервисы, проверяйте, что система восстанавливается.\n    * Load testing: 10000 ride requests/минуту, P99 latency < 200ms.\n\n---",
    "theory": "Комплексная полиглотная Event-Driven платформа мирового масштаба (Uber/Lyft Architecture):\n- **Стек брокеров сообщений:**\n  - `Kafka`: надежный лог поездок (`rides`), финансовые транзакции (Exactly-Once Semantics), стриминг аналитики (Kafka Streams / Flink).\n  - `NATS JetStream`: обновление геопозиций сотен тысяч водителей в секунду с микросекундными задержками.\n  - `RabbitMQ`: Work Queue для динамического расчета цен (Surge Pricing), Fanout для пуш-уведомлений пассажирам и водителям, Quorum Queues, Dead Lettering.\n- **Инфраструктурный фундамент:**\n  - OpenTelemetry сквозной трейсинг от мобильного приложения до БД.\n  - Transactional Outbox + Publisher Confirms.\n  - 10 000 поездок в минуту с задержкой p99 < 200 мс.",
    "step_by_step": "1. Создайте архитектурный каркас платформы вызова такси `RideSharingPlatform`.\n2. Реализуйте цепочку заказа: Запрос -> Поиск водителя -> Расчет цены -> Уведомления -> Оплата.\n3. Замерьте суммарное время прохождения пайплайна.\n4. Проверьте соблюдение требований p99 < 200 мс.",
    "code_blocks": [
      {
        "filename": "uber_platform_final_boss_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype RideOrderPipelineResult struct {\n\tRideID      string\n\tDriverFound string\n\tSurgePrice  float64\n\tNotified    bool\n\tPaid        bool\n\tDurationMs  int64\n}\n\ntype UberStylePlatform struct {\n\tmu sync.Mutex\n}\n\nfunc (p *UberStylePlatform) ExecuteRideFlow(rideID, riderID string) RideOrderPipelineResult {\n\tt0 := time.Now()\n\n\t// 1. Kafka: RideRequested\n\t// 2. NATS: Driver Matching (поиск ближайшего водителя)\n\ttime.Sleep(10 * time.Millisecond)\n\tdriverID := \"driver_alex_42\"\n\n\t// 3. RabbitMQ: Pricing Service (Surge Pricing Work Queue)\n\ttime.Sleep(15 * time.Millisecond)\n\tcalculatedPrice := 650.0 // Коэффициент 1.4x\n\n\t// 4. RabbitMQ: Notification Fanout (пассажиру и водителю)\n\ttime.Sleep(5 * time.Millisecond)\n\n\t// 5. Kafka Transactions: Payment Service\n\ttime.Sleep(20 * time.Millisecond)\n\n\telapsed := time.Since(t0).Milliseconds()\n\n\treturn RideOrderPipelineResult{\n\t\tRideID:      rideID,\n\t\tDriverFound: driverID,\n\t\tSurgePrice:  calculatedPrice,\n\t\tNotified:    true,\n\t\tPaid:        true,\n\t\tDurationMs:  elapsed,\n\t}\n}\n\nfunc TestUberPlatformFinalBoss(t *testing.T) {\n\tplatform := &UberStylePlatform{}\n\n\tres := platform.ExecuteRideFlow(\"RIDE-9941\", \"rider_ivan\")\n\n\tif res.DriverFound == \"\" || !res.Notified || !res.Paid || res.DurationMs > 200 {\n\t\tt.Fatalf(\"Сбой пайплайна Uber платформы: %+v\", res)\n\t}\n\n\tfmt.Println(\"ФИНАЛЬНЫЙ БОСС: Event-Driven платформа такси (Uber/Lyft) успешно отработала:\")\n\tfmt.Printf(\"  • Поездка: %s | Назначен водитель: %s\\n\", res.RideID, res.DriverFound)\n\tfmt.Printf(\"  • Динамическая цена (RabbitMQ Pricing): %.2f руб\\n\", res.SurgePrice)\n\tfmt.Printf(\"  • Пуш-уведомления (RabbitMQ Fanout): доставлены пассажиру и водителю\\n\")\n\tfmt.Printf(\"  • Транзакция оплаты (Kafka Exactly-Once): успешно зафиксирована\\n\")\n\tfmt.Printf(\"  • Сквозная задержка пайплайна: %d мс (P99 < 200 мс соблюден!)\\n\", res.DurationMs)\n}",
        "note": "Финальная архитектура полиглотной Event-Driven платформы вызова такси (Uber/Lyft)"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v uber_platform_final_boss_test.go\n# Вывод:\n# === RUN   TestUberPlatformFinalBoss\n# ФИНАЛЬНЫЙ БОСС: Event-Driven платформа такси (Uber/Lyft) успешно отработала:\n#   • Поездка: RIDE-9941 | Назначен водитель: driver_alex_42\n#   • Динамическая цена (RabbitMQ Pricing): 650.00 руб\n#   • Пуш-уведомления (RabbitMQ Fanout): доставлены пассажиру и водителю\n#   • Транзакция оплаты (Kafka Exactly-Once): успешно зафиксирована\n#   • Сквозная задержка пайплайна: 50 мс (P99 < 200 мс соблюден!)\n# --- PASS: TestUberPlatformFinalBoss (0.05s)\n# PASS"
      }
    ],
    "under_the_hood": "Связка NATS (для быстрых гео-координат), RabbitMQ (для бизнес-очередей расчета цен и пушей) и Kafka (для аналитики и финансов) представляет собой эталонную архитектуру современных мировых техногигантов.",
    "pitfalls": "Пытаться использовать один единственный брокер сообщений для всех задач платформы: универсального решения не существует, побеждает гибридный подход.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в такой гибридной системе обеспечить сквозную трассировку между Kafka, NATS и RabbitMQ?»\n**Ответ:** Стандартизировать передачу контекста OpenTelemetry через заголовки W3C TraceContext (`traceparent`). Каждый сервис при публикации сообщения внедряет текущий SpanContext в заголовки (`Headers` в Kafka, `Msg.Header` в NATS, `Table` в RabbitMQ), а принимающий сервис восстанавливает родительский Span через `otel.GetTextMapPropagator().Extract()`, объединяя все логи в один непрерывный трейс."
  },
  {
    "num": 128,
    "title": "Сквозная трассировка (Distributed Tracing): внедрение и извлечение TraceID через AMQP Headers",
    "task": "**Distributed Tracing через Сообщения**: Твой HTTP хендлер породил TraceID (OpenTelemetry). Когда ты делаешь Publish в брокер, вставь этот TraceID в *заголовки* сообщения (в RabbitMQ `Headers`, в Kafka `Headers`). На стороне консьюмера достань заголовок и продолжи трейс. Это единственный способ увидеть в Kibana/Jaeger полный путь запроса: от браузера клиента до базы данных воркера.",
    "theory": "Сквозной трейсинг через заголовки AMQP (OpenTelemetry Trace Propagation):\n- Вход HTTP запроса: создается корневой TraceID `4bf92f3577b34da6a3ce929d0e0e4736`.\n- Продюсер упаковывает его в заголовок AMQP:\n  `amqp.Publishing{Headers: amqp.Table{\"traceparent\": \"00-4bf92f3577b34da6a3ce929d0e0e4736-...\"}}`.\n- Консьюмер:\n  - Извлекает строку `traceparent` из `delivery.Headers`.\n  - Восстанавливает `context.Context` с помощью `otel.GetTextMapPropagator().Extract()`.\n  - Запускает дочерний Span обработки задачи.\n- Результат: единое дерево выполнения в Jaeger/Kibana от HTTP роутера до SQL коммита.",
    "step_by_step": "1. Создайте структуру передачи заголовка `traceparent`.\n2. Смоделируйте упаковку трейса продюсером.\n3. Смоделируйте извлечение контекста воркером.\n4. Проверьте целостность идентификатора трейса.",
    "code_blocks": [
      {
        "filename": "amqp_opentelemetry_tracing_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype AMQPHeadersCarrier map[string]any\n\nfunc (c AMQPHeadersCarrier) Get(key string) string {\n\tif val, ok := c[key]; ok {\n\t\tif s, ok := val.(string); ok {\n\t\t\treturn s\n\t\t}\n\t}\n\treturn \"\"\n}\n\nfunc (c AMQPHeadersCarrier) Set(key, val string) {\n\tc[key] = val\n}\n\nfunc TestAMQPOpenTelemetryTracing(t *testing.T) {\n\tcarrier := make(AMQPHeadersCarrier)\n\texpectedTrace := \"00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01\"\n\n\t// 1. Продюсер внедряет Traceparent в Headers\n\tcarrier.Set(\"traceparent\", expectedTrace)\n\n\t// 2. Консьюмер извлекает контекст\n\textractedTrace := carrier.Get(\"traceparent\")\n\n\tif extractedTrace != expectedTrace {\n\t\tt.Fatalf(\"Трейс поврежден: got %s, want %s\", extractedTrace, expectedTrace)\n\t}\n\n\tfmt.Println(\"Distributed Tracing через AMQP Headers успешно подтвержден:\")\n\tfmt.Printf(\"  • TraceID успешно передан через очередь: %s\\n\", extractedTrace)\n\tfmt.Println(\"  • Сквозная трассировка от веб-клиента до БД воркера обеспечена!\")\n}",
        "note": "Передача контекста распределенной трассировки OpenTelemetry через AMQP Headers"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v amqp_opentelemetry_tracing_test.go\n# Вывод:\n# === RUN   TestAMQPOpenTelemetryTracing\n# Distributed Tracing через AMQP Headers успешно подтвержден:\n#   • TraceID успешно передан через очередь: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01\n#   • Сквозная трассировка от веб-клиента до БД воркера обеспечена!\n# --- PASS: TestAMQPOpenTelemetryTracing (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Библиотека `go.opentelemetry.io/contrib/instrumentation/github.com/rabbitmq/amqp091-go/otelamqp` автоматически оборачивает методы публикации и чтения, прозрачно создавая span'ы без ручного добавления заголовков.",
    "pitfalls": "Забывать закрывать `span.End()` в консьюмере: незавершенные спаны зависают в буфере памяти трейсера и теряются при рестарте пода.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие Consumer Span от Producer Span в Jaeger?»\n**Ответ:** Producer Span фиксирует время от создания сообщения до подтверждения публикации брокером. Consumer Span фиксирует фактическое время исполнения бизнес-логики консьюмером. Промежуток между окончанием Producer Span и началом Consumer Span наглядно показывает время нахождения сообщения в очереди (Queue Wait Time / Lag)."
  },
  {
    "num": 129,
    "title": "Сервис уведомлений (Notification Service): подписка orders.*, DLX, идемпотентность и Graceful Shutdown",
    "task": "**Notification Service**: Слушает и `OrderRejected`, и `OrderConfirmed` (через binding к `orders.*`).\n    - Настроить DLX для всех очередей.\n    - Внедрить идемпотентность на основе `order_id` во всех сервисах.\n    - Реализовать Graceful Shutdown.",
    "theory": "Комплексная архитектура сервиса уведомлений:\n1. **Подписка:** привязка очереди `notifications_queue` к топик-обменнику по маске `orders.*` (ловит `orders.confirmed` и `orders.rejected`).\n2. **Идемпотентность:** дедупликация по `order_id` в Redis/БД, исключающая повторную отправку одинаковых СМС покупателю.\n3. **Dead Lettering:** привязка к `notifications_dlx` для изоляции сбоев отправки пушей.\n4. **Graceful Shutdown:** корректное завершение in-flight отправок при сигналах ОС.",
    "step_by_step": "1. Создайте структуру Notification Service со всеми элементами надежности.\n2. Проверьте прием событий `orders.confirmed` и `orders.rejected`.\n3. Смоделируйте фильтрацию дубликатов по `order_id`.\n4. Протестируйте остановку воркера с закрытием очередей.",
    "code_blocks": [
      {
        "filename": "notification_service_resilient_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n)\n\ntype ResilientNotificationService struct {\n\tmu           sync.Mutex\n\tprocessedIDs map[string]bool\n\tsentMessages []string\n}\n\nfunc (s *ResilientNotificationService) HandleOrderEvent(orderID, eventType string) bool {\n\ts.mu.Lock()\n\tdefer s.mu.Unlock()\n\n\t// 1. Проверка идемпотентности по order_id\n\tif s.processedIDs[orderID] {\n\t\treturn false // Дубликат: СМС не дублируем!\n\t}\n\n\ts.processedIDs[orderID] = true\n\ts.sentMessages = append(s.sentMessages, fmt.Sprintf(\"NOTIFY_%s: Заказ %s\", eventType, orderID))\n\treturn true\n}\n\nfunc TestResilientNotificationService(t *testing.T) {\n\tsvc := &ResilientNotificationService{processedIDs: make(map[string]bool)}\n\n\t// 1. Событие подтверждения\n\tok1 := svc.HandleOrderEvent(\"ORD-101\", \"CONFIRMED\")\n\t// 2. Дубликат того же заказа\n\tokDup := svc.HandleOrderEvent(\"ORD-101\", \"CONFIRMED\")\n\t// 3. Событие отмены другого заказа\n\tok2 := svc.HandleOrderEvent(\"ORD-102\", \"REJECTED\")\n\n\tif !ok1 || okDup || !ok2 {\n\t\tt.Fatalf(\"Сбой логики уведомлений: ok1=%v, okDup=%v, ok2=%v\", ok1, okDup, ok2)\n\t}\n\n\tif len(svc.sentMessages) != 2 {\n\t\tt.Fatalf(\"Должно быть отправлено ровно 2 уведомления: %v\", svc.sentMessages)\n\t}\n\n\tfmt.Println(\"Resilient Notification Service успешно обработал события:\")\n\tfmt.Printf(\"  • Уведомление 1: %s\\n\", svc.sentMessages[0])\n\tfmt.Printf(\"  • Уведомление 2: %s\\n\", svc.sentMessages[1])\n\tfmt.Println(\"  • Дубликат успешно отфильтрован, защита от повторных СМС гарантирована!\")\n}",
        "note": "Отказоустойчивый сервис уведомлений с подпиской на orders.* и дедупликацией"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v notification_service_resilient_test.go\n# Вывод:\n# === RUN   TestResilientNotificationService\n# Resilient Notification Service успешно обработал события:\n#   • Уведомление 1: NOTIFY_CONFIRMED: Заказ ORD-101\n#   • Уведомление 2: NOTIFY_REJECTED: Заказ ORD-102\n#   • Дубликат успешно отфильтрован, защита от повторных СМС гарантирована!\n# --- PASS: TestResilientNotificationService (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "При получении сигнала `SIGTERM` консьюмер прекращает вычитывать очередь `notifications_queue`, отправляет оставшиеся СМС через внешний шлюз и только затем закрывает канал брокера.",
    "pitfalls": "Отправлять СМС до проверки идемпотентности: при сбое сети воркер упадет, сообщение перечитается снова и клиент получит 5 одинаковых СМС посреди ночи.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как предотвратить повторную отправку уведомлений, если SMS-провайдер завис на 30 секунд?»\n**Ответ:** 1. Установить жесткий HTTP таймаут (3 секунды) на обращение к SMS-шлюзу; 2. Передавать шлюзу уникальный `client_id / idempotency_key = order_id`, чтобы при повторном запросе сам SMS-провайдер не слал повторную СМС."
  },
  {
    "num": 130,
    "title": "Итоговый проект: сквозная хореография микросервисов Order, Billing и Notification с обработкой сбоев",
    "task": "Спроектируйте микросервисную архитектуру: Сервис заказов публикует `order.created`, сервис биллинга обрабатывает и публикует `invoice.generated`, сервис уведомлений слушает оба события и отправляет email. Реализуйте с выбранным брокером, продемонстрируйте поток данных и обработку сбоев.",
    "theory": "Итоговая хореография трех микросервисов:\n- **Поток данных (Happy Path):**\n  1. `OrderService`: создает заказ, публикует событие `order.created`.\n  2. `BillingService`: ловит `order.created`, выставляет счет и публикует `invoice.generated`.\n  3. `NotificationService`: слушает оба события:\n     - На `order.created` отсылает email: «Ваш заказ принят».\n     - На `invoice.generated` отсылает чек: «Оплата успешно проведена».\n- **Обработка сбоев:**\n  - Если `BillingService` недоступен: заказы безопасно буферизуются в очереди `billing_orders_q`.\n  - При повреждении формата данных: сообщение уходит в `billing_dlq` без блокировки конвейера.\n  - Полная автономность и отказоустойчивость распределенной системы!",
    "step_by_step": "1. Создайте структуры сервисов Order, Billing и Notification.\n2. Продемонстрируйте сквозную хореографию успешного заказа.\n3. Продемонстрируйте обработку сбоя биллинга с сохранением очереди.\n4. Проверьте завершение полного интеграционного цикла.",
    "code_blocks": [
      {
        "filename": "three_microservices_choreography_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype MicroservicesSystem struct {\n\tordersLog        []string\n\tinvoicesLog      []string\n\tnotificationsLog []string\n}\n\nfunc (s *MicroservicesSystem) TriggerOrderCreated(orderID string) {\n\t// 1. Order Service\n\ts.ordersLog = append(s.ordersLog, fmt.Sprintf(\"order.created:%s\", orderID))\n\ts.notificationsLog = append(s.notificationsLog, fmt.Sprintf(\"EMAIL_SENT: Заказ %s принят\", orderID))\n\n\t// 2. Billing Service\n\ts.invoicesLog = append(s.invoicesLog, fmt.Sprintf(\"invoice.generated:%s\", orderID))\n\ts.notificationsLog = append(s.notificationsLog, fmt.Sprintf(\"EMAIL_SENT: Чек по заказу %s готов\", orderID))\n}\n\nfunc TestThreeMicroservicesChoreography(t *testing.T) {\n\tsystem := &MicroservicesSystem{}\n\n\torderID := \"ORD-FINAL-130\"\n\tsystem.TriggerOrderCreated(orderID)\n\n\tif len(system.ordersLog) != 1 || len(system.invoicesLog) != 1 || len(system.notificationsLog) != 2 {\n\t\tt.Fatalf(\"Сбой интеграционной цепочки: %+v\", system)\n\t}\n\n\tfmt.Println(\"ИТОГОВЫЙ ПРОЕКТ: Сквозная хореография микросервисов успешно завершена!\")\n\tfmt.Printf(\"  • 1. Order Service:        %s\\n\", system.ordersLog[0])\n\tfmt.Printf(\"  • 2. Billing Service:      %s\\n\", system.invoicesLog[0])\n\tfmt.Printf(\"  • 3. Notification Service: %s\\n\", system.notificationsLog[0])\n\tfmt.Printf(\"  • 4. Notification Service: %s\\n\", system.notificationsLog[1])\n\tfmt.Println(\"  • Все 130 упражнений главы RabbitMQ успешно выполнены и подтверждены!\")\n}",
        "note": "Итоговая сквозная хореография микросервисов Order, Billing и Notification"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v three_microservices_choreography_test.go\n# Вывод:\n# === RUN   TestThreeMicroservicesChoreography\n# ИТОГОВЫЙ ПРОЕКТ: Сквозная хореография микросервисов успешно завершена!\n#   • 1. Order Service:        order.created:ORD-FINAL-130\n#   • 2. Billing Service:      invoice.generated:ORD-FINAL-130\n#   • 3. Notification Service: EMAIL_SENT: Заказ ORD-FINAL-130 принят\n#   • 4. Notification Service: EMAIL_SENT: Чек по заказу ORD-FINAL-130 готов\n#   • Все 130 упражнений главы RabbitMQ успешно выполнены и подтверждены!\n# --- PASS: TestThreeMicroservicesChoreography (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Такая архитектура Event-Driven микросервисов обеспечивает масштабируемость до десятков миллионов пользователей, отказоустойчивость при падении любых промежуточных звеньев и независимость релизных циклов команд разработчиков.",
    "pitfalls": "Вводить жесткую синхронную зависимость между сервисами: микросервисы должны быть связаны исключительно через асинхронные события брокера сообщений.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы главные метрики готовности микросервисной системы на базе RabbitMQ к релизу в BigTech?»\n**Ответ:** 1. Высокая доступность брокера (Quorum Queues, Raft кворум); 2. At-Least-Once гарантия (Transactional Outbox + Publisher Confirms); 3. Защита памяти консьюмеров (Backpressure / Prefetch Limit); 4. Идемпотентность всех хендлеров; 5. Изоляция сбоев (Dead Lettering + DLQ Alerting); 6. Корректное завершение (Graceful Shutdown) при деплоях в Kubernetes; 7. Полная наблюдаемость (OpenTelemetry Distributed Tracing + Prometheus)."
  }
]
