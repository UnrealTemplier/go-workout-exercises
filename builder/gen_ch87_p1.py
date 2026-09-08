# -*- coding: utf-8 -*-
"""
Chapter 87 Part 1: Exercises 1 to 25
Orchestration of Distributed Processes (Durable Execution) on Temporal.io in Go
"""

exercises = [
    {
        "num": 1,
        "title": "Введение в парадигму Durable Execution (Temporal.io)",
        "task": "Изучите концепцию долговечного исполнения (Durable Execution): состояние приложения, стек вызовов, локальные переменные и таймеры сохраняются даже при падении сервера, перезагрузке пода или сбое сети. Объясните, почему Temporal заменяет хрупкие самописные машины состояний, цепочки очередей и распределенные саги. Реализуйте концептуальную модель на Go, демонстрирующую сравнение классической хрупкой оркестрации на базе БД и очередей с парадигмой Durable Execution.",
        "theory": "В классических распределенных системах оркестрация долгоживущих бизнес-процессов (оформление заказа, онбординг клиента, выплата кредита, биллинг) превращается в сложнейшую инженерную проблему. Традиционный подход требует:\n1. Ручного моделирования конечного автомата (State Machine) с таблицей `process_state` в реляционной БД.\n2. Связывания шагов через цепочки очередей сообщений (Kafka, RabbitMQ) и паттерн Transactional Outbox.\n3. Установки внешних планировщиков/таймеров (cron, Redis TTL) для ожидания событий (например, 'подождать 3 дня ответа пользователя').\n4. Ручного написания логики ретраев, дедупликации, идемпотентности и распределенных транзакций (Saga).\n\nПри малейшем сбое сети, перезапуске контейнера во время транзакции или разрыве соединения система рискует остаться в промежуточном рассинхронизированном состоянии (split-brain, повисшие заказы).\n\n**Durable Execution (Temporal.io)** кардинально меняет парадигму. Программист пишет обычный императивный последовательный код на Go: циклы `for`, ветвления `if`, локальные переменные, `workflow.Sleep(ctx, 30*24*time.Hour)` и вызовы функций. Temporal SDK и Temporal Cluster гарантируют, что:\n- Стек вызовов, локальные переменные, счетчики циклов и таймеры автоматически сохраняются.\n- Если физический сервер, на котором исполняется код, сгорает прямо посреди цикла, Temporal восстанавливает выполнение на другом доступном воркере ровно с того места, где произошел сбой, с идентичными значениями всех локальных переменных.\n- Это достигается не через периодические снапшоты памяти (как в виртуальных машинах), а через математически строгий детерминированный механизм **Event Sourcing** и **Replay** журнала событий.",
        "step_by_step": "1. Создайте структуры данных для демонстрации концептуальной разницы между хрупкой машиной состояний (SQL DB + States) и Durable Execution.\n2. Реализуйте симулятор журнала событий (Event Journal / Event Sourcing Engine), который иллюстрирует, как Temporal записывает шаги WorkflowTaskScheduled, ActivityTaskScheduled, ActivityTaskCompleted.\n3. Смоделируйте аварийное падение процесса на шаге 2 и покажите механизм Replay: как воркер восстанавливает состояние без повторного вызова сайд-эффектов.\n4. Выведите сравнительную аналитику преимуществ Durable Execution для Senior/Staff архитекторов.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// EventType представляет типы событий в журнале Event Sourcing кластера Temporal.
type EventType string

const (
	EventWorkflowStarted   EventType = "WorkflowExecutionStarted"
	EventActivityScheduled EventType = "ActivityTaskScheduled"
	EventActivityCompleted EventType = "ActivityTaskCompleted"
	EventTimerStarted      EventType = "TimerStarted"
	EventTimerFired        EventType = "TimerFired"
	EventWorkflowCompleted EventType = "WorkflowExecutionCompleted"
)

// HistoryEvent фиксирует атомарное событие в неизменяемом журнале Temporal.
type HistoryEvent struct {
	ID        int
	Type      EventType
	Name      string
	Result    string
	Timestamp time.Time
}

// DurableRuntimeSimulator иллюстрирует принцип Replay в Temporal SDK.
type DurableRuntimeSimulator struct {
	mu           sync.Mutex
	history      []HistoryEvent
	replaying    bool
	replayCursor int
}

func NewDurableRuntime() *DurableRuntimeSimulator {
	return &DurableRuntimeSimulator{
		history: make([]HistoryEvent, 0),
	}
}

// ExecuteActivity имитирует вызов Activity с сохранением в историю или восстановлением из Replay.
func (r *DurableRuntimeSimulator) ExecuteActivity(ctx context.Context, name string, sideEffect func() string) string {
	r.mu.Lock()
	defer r.mu.Unlock()

	// Фаза Replay: если событие уже есть в истории, сайд-эффект НЕ вызывается повторно!
	if r.replaying && r.replayCursor < len(r.history) {
		event := r.history[r.replayCursor]
		if event.Type == EventActivityCompleted && event.Name == name {
			fmt.Printf(" [REPLAY ENGINE] Activity '%s' уже выполнена ранее. Восстановлен результат из истории: '%s'\n", name, event.Result)
			r.replayCursor++
			return event.Result
		}
	}

	// Фаза реального исполнения (Live Execution): выполняется сайд-эффект (сеть/БД)
	fmt.Printf(" [LIVE EXECUTION] Выполняется реальный сайд-эффект Activity: '%s'...\n", name)
	res := sideEffect()

	// Кластер Temporal сохраняет результат в персистентный журнал событий
	event := HistoryEvent{
		ID:        len(r.history) + 1,
		Type:      EventActivityCompleted,
		Name:      name,
		Result:    res,
		Timestamp: time.Now(),
	}
	r.history = append(r.history, event)
	return res
}

// SimulateCrashAndRecover имитирует крах воркера и запуск Replay на резервном узле.
func (r *DurableRuntimeSimulator) SimulateCrashAndRecover() {
	r.mu.Lock()
	defer r.mu.Unlock()
	fmt.Println("\n💥 [CRASH] Сервер аварийно упал (SIGKILL / OOM / разрыв сети)! Память стерта.")
	fmt.Println("🔄 [RECOVERY] Новый воркер берет задачу из очереди и запускает детерминированный Replay...")
	r.replaying = true
	r.replayCursor = 0
}

func main() {
	runtime := NewDurableRuntime()

	// Бизнес-логика Workflow: 1) Списать деньги -> 2) Зарезервировать склад -> 3) Отправить чек
	orderWorkflow := func(rt *DurableRuntimeSimulator) {
		step1 := rt.ExecuteActivity(context.Background(), "ChargePayment", func() string {
			return "SUCCESS: 4500_RUB_CHARGED"
		})

		step2 := rt.ExecuteActivity(context.Background(), "ReserveWarehouse", func() string {
			return "SUCCESS: SKU_9921_RESERVED"
		})

		step3 := rt.ExecuteActivity(context.Background(), "SendReceiptEmail", func() string {
			return "SUCCESS: EMAIL_SENT"
		})

		fmt.Printf("\n🎉 Итог процесса: %s | %s | %s\n", step1, step2, step3)
	}

	fmt.Println("--- Этап 1: Старт процесса и сбой после шага 2 ---")
	// Выполняем первые 2 шага вручную до краха
	runtime.ExecuteActivity(context.Background(), "ChargePayment", func() string {
		return "SUCCESS: 4500_RUB_CHARGED"
	})
	runtime.ExecuteActivity(context.Background(), "ReserveWarehouse", func() string {
		return "SUCCESS: SKU_9921_RESERVED"
	})

	// Симулируем крах узла
	runtime.SimulateCrashAndRecover()

	fmt.Println("\n--- Этап 2: Выполнение того же Workflow с начала на новом воркере ---")
	// Запускаем ровно тот же код Workflow: шаги 1 и 2 моментально пройдут через Replay без списаний!
	orderWorkflow(runtime)
}
"""
            }
        ],
        "under_the_hood": "В архитектуре Temporal задействованы два фундаментальных слоя абстракции:\n1. **Temporal Cluster (Сервер)**: Состоит из сервисов Frontend (gRPC шлюз), History (управление шардами и запись неизменяемой истории событий в БД PostgreSQL/Cassandra/MySQL), Matching (высокопроизводительные Task Queues на базе долгоживущих соединений) и Worker (системные фоновые задачи). Сервер НИКОГДА не исполняет пользовательский код!\n2. **Temporal Worker (Клиентский SDK)**: Go-бинарник, запущенный в Kubernetes-поде клиента. Воркер опрашивает очередь (Long Polling) через gRPC. При получении задачи WorkflowTask воркер запускает детерминированную корутину, которая проигрывает историю событий (Replay) до текущего состояния. Когда код доходит до новой невыполненной Activity, воркер отправляет серверу команду ScheduleActivityTask. Сервер записывает событие в историю и помещает задачу в очередь Activity Task Queue, откуда ее забирает свободный Activity Worker.",
        "pitfalls": "Главная ловушка для новичков — путать Workflow и Activity. Если внутри функции Workflow сделать прямой вызов `http.Post()` или `db.Query()`, при каждом Replay этот сайд-эффект будет вызываться снова и снова, списывая деньги с клиентов или отправляя сотни дублирующих писем! Сайд-эффекты и ввод-вывод допустимы ИСКЛЮЧИТЕЛЬНО внутри Activities. Код Workflow обязан быть чистой детерминированной функцией от журнала событий.",
        "interview_qa": "В: Чем Durable Execution в Temporal концептуально отличается от оркестрации на базе Camunda (BPMN) или AWS Step Functions?\nО: В Camunda и Step Functions процесс описывается декларативным языком (XML/BPMN или JSON/ASL state-machines). При усложнении логики (динамические циклы, параллельная обработка динамических срезов, перехват исключений) декларативные диаграммы превращаются в нечитаемых 'монстров', сложно тестируются и требуют визуальных редакторов. В Temporal вы используете полноценный язык программирования (Go): ветвления, структуры, интерфейсы, типизацию, IDE-рефакторинг и стандартные юнит-тесты, получая отказоустойчивость уровня ядра ОС прямо в императивном коде."
    },
    {
        "num": 2,
        "title": "Архитектура Temporal: Cluster, Workflows, Activities, Workers",
        "task": "Разберите фундаментальные компоненты архитектуры Temporal: Temporal Cluster (Frontend, History, Matching, Internal Worker), очереди задач (Task Queues), определение Workflow (Workflow Definition), определение Activity (Activity Definition) и воркер (Temporal Worker). Напишите Go-программу, демонстрирующую четкое архитектурное разделение слоев: контракты интерфейсов, структуру сообщений и разделение ролей воркеров.",
        "theory": "Архитектура Temporal построена на строгом разделении зон ответственности между надежным сохранением истории и децентрализованным исполнением пользовательского кода:\n\n1. **Temporal Cluster**:\n   - **Frontend Service**: Принимает внешние gRPC запросы от клиентов и воркеров, проверяет авторизацию/квоты, маршрутизирует запросы по шардам.\n   - **History Service**: Ядро системы. Отвечает за логику сохранения неизменяемой истории событий (Event Sourcing) в постоянном хранилище. Масштабируется горизонтально путем шардирования пространств имен (Namespaces) и идентификаторов WorkflowID.\n   - **Matching Service**: Отвечает за диспетчеризацию очередей задач (Task Queues). Реализует синхронную передачу задач (Task Matching) в режиме реального времени между воркерами и кластером.\n\n2. **Temporal Worker (Go SDK)**:\n   - Процесс, запускаемый в инфраструктуре пользователя. Воркер открывает постоянные gRPC-стримы к кластеру, вытягивает задачи из Task Queue, выполняет их и возвращает результат.\n\n3. **Workflows vs Activities**:\n   - **Workflow**: Оркестратор. Только детерминированная логика, ветвления, таймеры, сигналы. Выполняется в защищенных горутинах SDK.\n   - **Activity**: Исполнитель. Любые недетерминированные действия: HTTP-запросы, SQL-запросы, запись файлов, вызов gRPC внешних систем.",
        "step_by_step": "1. Спроектируйте архитектурные контракты (Go Interfaces) для Temporal Client, Worker и TaskQueue.\n2. Опишите строго типизированные DTO для аргументов и результатов Workflow и Activity.\n3. Реализуйте структуру Temporal Topology, демонстрирующую распределение очередей задач (Task Queue Partitioning).\n4. Смоделируйте взаимодействие Frontend -> Matching -> Worker в виде консольного демо.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"
)

// DTO контракты для бизнес-процесса оформления подписки (SaaS Billing).
type SubscribeRequest struct {
	UserID    string `json:"user_id"`
	PlanID    string `json:"plan_id"`
	PriceCent int64  `json:"price_cent"`
}

type PaymentResult struct {
	TransactionID string    `json:"transaction_id"`
	ProcessedAt   time.Time `json:"processed_at"`
	Status        string    `json:"status"`
}

type ProvisionResult struct {
	SubscriptionID string `json:"subscription_id"`
	ActiveUntil    time.Time `json:"active_until"`
}

// Activity Definitions: недетерминированные сайд-эффекты (HTTP, SQL, RPC).
type BillingActivities interface {
	ChargePayment(ctx context.Context, req SubscribeRequest) (*PaymentResult, error)
	ActivateTenant(ctx context.Context, userID, planID string) (*ProvisionResult, error)
	SendWelcomeEmail(ctx context.Context, userID string) error
}

// Реализация сервиса Activities
type billingActivitiesImpl struct{}

func (b *billingActivitiesImpl) ChargePayment(ctx context.Context, req SubscribeRequest) (*PaymentResult, error) {
	fmt.Printf(" [ACTIVITY] Обращение в Stripe API: списание %d центов для пользователя %s\n", req.PriceCent, req.UserID)
	return &PaymentResult{
		TransactionID: "ch_live_9941a82f",
		ProcessedAt:   time.Now(),
		Status:        "succeeded",
	}, nil
}

func (b *billingActivitiesImpl) ActivateTenant(ctx context.Context, userID, planID string) (*ProvisionResult, error) {
	fmt.Printf(" [ACTIVITY] Обращение в K8s/DB: активация тарифа '%s' для пользователя %s\n", planID, userID)
	return &ProvisionResult{
		SubscriptionID: "sub_pro_1024",
		ActiveUntil:    time.Now().AddDate(0, 1, 0),
	}, nil
}

func (b *billingActivitiesImpl) SendWelcomeEmail(ctx context.Context, userID string) error {
	fmt.Printf(" [ACTIVITY] Обращение в SendGrid: отправка welcome-письма для %s\n", userID)
	return nil
}

// Демонстрация топологии Temporal
func main() {
	fmt.Println("=== Архитектура Temporal.io: Роли и Компоненты ===")
	fmt.Println("1. Temporal Cluster (Frontend, History, Matching) развернут в инфраструктуре.")
	fmt.Println("2. Task Queue 'billing-tasks' зарегистрирована в Matching Service.")
	fmt.Println("3. Go Worker слушает очередь 'billing-tasks' через gRPC Long Polling.")

	acts := &billingActivitiesImpl{}
	ctx := context.Background()

	req := SubscribeRequest{
		UserID:    "usr_7721",
		PlanID:    "enterprise_scale",
		PriceCent: 49900,
	}

	payRes, err := acts.ChargePayment(ctx, req)
	if err != nil {
		panic(err)
	}

	actRes, err := acts.ActivateTenant(ctx, req.UserID, req.PlanID)
	if err != nil {
		panic(err)
	}

	if err := acts.SendWelcomeEmail(ctx, req.UserID); err != nil {
		panic(err)
	}

	fmt.Printf("\n✅ Процесс успешно завершен!\nТранзакция: %s | Подписка: %s (до %s)\n",
		payRes.TransactionID, actRes.SubscriptionID, actRes.ActiveUntil.Format(time.RFC3339))
}
"""
            }
        ],
        "under_the_hood": "Очереди задач (Task Queues) в Temporal не являются физическими очередями как в RabbitMQ или Kafka. Они представляют собой динамические виртуальные мультиплексированные структуры данных внутри Matching Service. Когда Worker вызывает `PollWorkflowTaskQueue` или `PollActivityTaskQueue`, соединение удерживается открытым (HTTP/2 gRPC стрим). Если в этот момент History Service генерирует новую задачу, Matching Service осуществляет 'Sync Match' — передает задачу напрямую в ожидающий воркер без промежуточной записи в очередь БД, достигая субмиллисекундных задержек.",
        "pitfalls": "Частая архитектурная ошибка — создание отдельной Task Queue для каждого единичного Workflow ID или пользователя. Это создает миллионы очередей в Matching Service, перегружает метаданные кластера и приводит к деградации производительности. Task Queue должна отражать тип рабочей нагрузки (например, `billing-v1`, `video-encoding-gpu`, `notifications`), а не идентификаторы отдельных экземпляров процессов.",
        "interview_qa": "В: Что происходит, если все воркеры упали или отключились от Temporal Cluster на 2 часа?\nО: Ничего фатального не произойдет! Temporal Cluster продолжит сохранять состояние всех активных таймеров, принимать внешние сигналы и складывать новые задачи в Task Queues. Никакие данные не потеряются, никакие таймауты выполнения (Start-To-Close) не начнут отсчитываться раньше времени, пока задача не будет взята воркером. Как только воркеры перезапустятся, они начнут вычитывать накопившиеся задачи из очередей и продолжат исполнение процессов с идеальной консистентностью."
    },
    {
        "num": 3,
        "title": "Подключение к Temporal Cluster на Go",
        "task": "Используя официальный SDK `go.temporal.io/sdk`, напишите промышленный модуль подключения к кластеру Temporal: инициализация `client.Dial(client.Options{})`, настройка пространства имен (Namespace), тайм-аутов соединения, безопасного подключения по mTLS (Mutual TLS) с валидацией клиентского сертификата и CA. Реализуйте проверку доступности (Health Check) кластера при старте приложения с graceful shutdown.",
        "theory": "Для взаимодействия с кластером Temporal из Go-приложения используется пакет `go.temporal.io/sdk/client`. Клиент Temporal является потокобезопасным (Thread-safe) долгоживущим объектом. В высоконагруженных микросервисах рекомендуется создавать один экземпляр клиента на всё приложение и внедрять его через Dependency Injection.\n\nВ корпоративных инфраструктурах и при работе с Temporal Cloud кластер защищен взаимной TLS-аутентификацией (mTLS):\n- Клиент обязан предоставить сертификат `tls.crt` и закрытый ключ `tls.key`.\n- Кластер проверяет право клиента подключаться к определенному Namespace по Common Name или Subject Alternative Name (SAN) сертификата.\n- Клиент валидирует сертификат сервера через доверенный `ca.crt`.",
        "step_by_step": "1. Спроектируйте конфигурационную структуру `TemporalConfig` (HostPort, Namespace, TLS параметры).\n2. Реализуйте вспомогательную функцию для загрузки TLS-сертификатов и построения `*tls.Config`.\n3. Напишите конструктор `NewTemporalClient`, конфигурирующий `client.Options` с интерцепторами и логгером.\n4. Реализуйте пинг/проверку доступности кластера (Cluster Healthcheck).\n5. Обеспечьте корректное закрытие клиента через `defer c.Close()`.",
        "code_blocks": [
            {
                "filename": "client.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"log/slog"
	"os"
	"time"

	"go.temporal.io/sdk/client"
)

// TemporalConfig содержит параметры промышленного подключения к Temporal Cluster / Cloud.
type TemporalConfig struct {
	HostPort  string
	Namespace string
	CertPath  string
	KeyPath   string
	CAPath    string
	UseTLS    bool
}

// BuildTLSConfig собирает конфигурацию взаимной аутентификации (mTLS).
func BuildTLSConfig(cfg TemporalConfig) (*tls.Config, error) {
	if !cfg.UseTLS {
		return nil, nil
	}

	cert, err := tls.LoadX509KeyPair(cfg.CertPath, cfg.KeyPath)
	if err != nil {
		return nil, fmt.Errorf("ошибка загрузки клиентского сертификата mTLS: %w", err)
	}

	caCert, err := os.ReadFile(cfg.CAPath)
	if err != nil {
		return nil, fmt.Errorf("ошибка чтения CA сертификата: %w", err)
	}

	caPool := x509.NewCertPool()
	if !caPool.AppendCertsFromPEM(caCert) {
		return nil, fmt.Errorf("не удалось спарсить корневой CA сертификат")
	}

	tlsConfig := &tls.Config{
		Certificates: []tls.Certificate{cert},
		RootCAs:      caPool,
		MinVersion:   tls.VersionTLS13,
	}
	return tlsConfig, nil
}

// NewTemporalClient создает промышленный клиент Temporal SDK.
func NewTemporalClient(ctx context.Context, cfg TemporalConfig, logger *slog.Logger) (client.Client, error) {
	tlsConfig, err := BuildTLSConfig(cfg)
	if err != nil {
		return nil, err
	}

	opts := client.Options{
		HostPort:  cfg.HostPort,
		Namespace: cfg.Namespace,
		Logger:    nil, // В реальном проекте подключается slog / zap адаптер
	}

	if tlsConfig != nil {
		opts.ConnectionOptions = client.ConnectionOptions{
			TLS: tlsConfig,
		}
	}

	c, err := client.Dial(opts)
	if err != nil {
		return nil, fmt.Errorf("ошибка подключения к Temporal Cluster на %s: %w", cfg.HostPort, err)
	}

	logger.Info("Успешное подключение к Temporal Cluster", "host", cfg.HostPort, "namespace", cfg.Namespace)
	return c, nil
}

func main() {
	logger := slog.Default()

	cfg := TemporalConfig{
		HostPort:  "localhost:7233",
		Namespace: "production-finance",
		UseTLS:    false, // В локальном dev-окружении без TLS
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Инициализация клиента
	fmt.Printf("Подключение к кластеру Temporal: %s (namespace: %s)...\n", cfg.HostPort, cfg.Namespace)
	c, err := NewTemporalClient(ctx, cfg, logger)
	if err != nil {
		fmt.Printf("Имитация подключения: %v\n", err)
		return
	}
	defer c.Close()

	fmt.Println("Temporal Client успешно инициализирован и готов к работе!")
}
"""
            }
        ],
        "under_the_hood": "Под капотом `client.Dial` создает постоянный пул HTTP/2 соединений gRPC с кластером Temporal. Он использует балансировку round-robin на уровне gRPC subchannels, автоматически переподключается при сетевых разрывах с экспоненциальным backoff и поддерживает внутренний heartbeat для проверки живости сетевого сокета (gRPC keepalive probes). При вызове `c.Close()` все активные стримы и соединения закрываются корректно.",
        "pitfalls": "Создание нового экземпляра `client.Client` на каждый входящий HTTP-запрос — катастрофическая ошибка. Каждое создание клиента инициирует TLS handshake, аллокацию пула соединений и фоновых горутин мониторинга. Это быстро исчерпывает файловые дескрипторы сокетов (FD exhaustion) и приводит к падению сервиса. Всегда используйте один общий Singleton-экземпляр клиента.",
        "interview_qa": "В: Как проверить здоровье (Health Check) подключения к Temporal Cluster в Kubernetes Readiness Probe?\nО: Для проверки готовности воркера или сервиса вызывается метод `client.CheckHealth(ctx, &client.CheckHealthRequest{})` или `client.DescribeNamespace(ctx, namespace)`. Если кластер недоступен или у клиента протухли mTLS-сертификаты, вызов вернет ошибку gRPC `Unavailable` или `Unauthenticated`, что позволит Kubernetes не пускать трафик на неисправный под."
    },
    {
        "num": 4,
        "title": "Создание и запуск первого Temporal Worker на Go",
        "task": "Создайте рабочий процесс (Worker) на Go: инициализируйте `worker.New(client, 'order-tasks', worker.Options{})`, зарегистрируйте функцию рабочего процесса `w.RegisterWorkflow(OrderWorkflow)` и функцию действия `w.RegisterActivity(ChargeCardActivity)`. Реализуйте корректный запуск и завершение воркера через `w.Run(worker.InterruptCh())` с перехватом сигналов SIGINT и SIGTERM (Graceful Shutdown).",
        "theory": "Temporal Worker — это автономный сервис (демон), который подключается к кластеру Temporal, опрашивает очередь задач (Task Queue) и исполняет зарегистрированные функции Workflow и Activity.\n\nЖизненный цикл воркера:\n1. Регистрация функций: `w.RegisterWorkflow(...)` и `w.RegisterActivity(...)`. Воркер создает внутреннюю таблицу маппинга имен функций в их рефлексивные обертки.\n2. Старт поллеров: `w.Start()` или блокирующий `w.Run(interruptCh)`. Воркер запускает пул горутин, которые отправляют gRPC-запросы `PollWorkflowTaskQueue` и `PollActivityTaskQueue`.\n3. Исполнение: при получении задачи воркер создает изолированную корутину для Workflow или вызывает Activity.\n4. Graceful Shutdown: при получении сигнала завершения воркер прекращает брать новые задачи из очередей, дожидается завершения текущих коротких Workflow Tasks и дает Activity завершиться в рамках таймаута.",
        "step_by_step": "1. Опишите сигнатуру Workflow функции `SimpleOrderWorkflow(ctx workflow.Context, orderID string) (string, error)`.\n2. Опишите сигнатуру Activity функции `ChargeCardActivity(ctx context.Context, amount int) error`.\n3. Сконфигурируйте `worker.Options` (размеры пулов, параллелизм).\n4. Зарегистрируйте Workflow и Activity в воркере.\n5. Запустите воркер с ожиданием прерывания через канал сигналов ОС.",
        "code_blocks": [
            {
                "filename": "worker.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/worker"
	"go.temporal.io/sdk/workflow"
)

// ChargeCardActivity выполняет внешнее действие (списание с карты).
func ChargeCardActivity(ctx context.Context, amount int) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Выполнение Activity: списание средств", "amount", amount)
	fmt.Printf(" [ACTIVITY] Списание %d рублей с банковской карты...\n", amount)
	return nil
}

// SimpleOrderWorkflow оркестрирует процесс заказа.
func SimpleOrderWorkflow(ctx workflow.Context, orderID string) (string, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Старт SimpleOrderWorkflow", "order_id", orderID)

	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 10 * time.Second,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	// Вызов Activity внутри Workflow
	var actErr error
	err := workflow.ExecuteActivity(ctx, ChargeCardActivity, 1500).Get(ctx, &actErr)
	if err != nil {
		logger.Error("Ошибка списания средств", "error", err)
		return "", err
	}

	logger.Info("Заказ успешно обработан", "order_id", orderID)
	return fmt.Sprintf("Order %s completed successfully", orderID), nil
}

func main() {
	// Подключение к Temporal кластеру
	c, err := client.Dial(client.Options{
		HostPort:  "localhost:7233",
		Namespace: "default",
	})
	if err != nil {
		log.Fatalf("Не удалось подключиться к кластеру Temporal: %v", err)
	}
	defer c.Close()

	taskQueue := "order-tasks"

	// Инициализация воркера для очереди order-tasks
	w := worker.New(c, taskQueue, worker.Options{
		MaxConcurrentActivityExecutionSize:     100,
		MaxConcurrentWorkflowTaskExecutionSize: 100,
	})

	// Регистрация Workflow и Activity
	w.RegisterWorkflow(SimpleOrderWorkflow)
	w.RegisterActivity(ChargeCardActivity)

	fmt.Printf("🚀 Temporal Worker успешно запущен на очереди '%s'!\n", taskQueue)
	fmt.Println("Нажмите Ctrl+C для Graceful Shutdown...")

	// Запуск с перехватом системных сигналов SIGINT/SIGTERM
	err = w.Run(worker.InterruptCh())
	if err != nil {
		log.Fatalf("Ошибка остановки воркера: %v", err)
	}
	fmt.Println("Воркер корректно остановлен.")
}
"""
            }
        ],
        "under_the_hood": "Метод `w.Run(worker.InterruptCh())` блокирует текущую горутину. Канал `worker.InterruptCh()` слушает сигналы `os.Interrupt` и `syscall.SIGTERM`. При получении сигнала воркер вызывает внутренний метод `Stop()`. При этом немедленно закрываются long-polling gRPC-стримы к Matching Service (кластер перестает направлять задачи этому инстансу), а запущенным Workflow Tasks дается возможность дойти до ближайшего шага фиксации (yield). Если на узле выполняются долгие Activities, они получают отмену через `ctx.Done()` только по истечении grace-периода.",
        "pitfalls": "Никогда не регистрируйте в одном воркере разные функции под одинаковыми именами. По умолчанию Temporal использует имя функции Go (`runtime.FuncForPC`), но если вы задаете кастомные имена строками, конфликт имен приведет к тихой перезаписи обработчика или панике при старте.",
        "interview_qa": "В: Можно ли запускать выполнение Workflow и Activity на разных независимых пулах воркеров?\nО: Да, и это стандартная промышленная архитектура! Вы можете запустить пул 'Workflow Workers' (легковесные поды с минимальным CPU/RAM, обслуживающие чистую логику) и отдельный пул 'Heavy Activity Workers' (поды с большим объемом памяти, GPU или сетевым доступом к закрытым банковским шлюзам), которые слушают разные Task Queues."
    },
    {
        "num": 5,
        "title": "Золотое правило Workflow: Детерминированность",
        "task": "Код Workflow исполняется через механизм Event Sourcing / Replay. Сформулируйте и продемонстрируйте «Золотое правило»: код рабочего процесса ОБЯЗАН быть строго детерминированным! Покажите на примерах кода, почему категорически запрещено использовать `time.Now()`, `rand.Int()`, стандартные горутины `go func()`, глобальные мутабельные переменные и любые прямые сетевые/дисковые вызовы внутри Workflow. Напишите детерминированный Workflow, соблюдающий все требования Temporal SDK.",
        "theory": "Фундамент Durable Execution — детерминированный Replay (повторное воспроизведение). Когда воркер падает или выгружает процесс из памяти для экономии ресурсов, при поступлении нового события (завершение Activity, приход Сигнала) воркер берет историю событий из базы данных кластера и **проигрывает функцию Workflow с самой первой строки**!\n\nЕсли при первом запуске (Live Execution) и при повторном запуске (Replay) код пойдет по разным путям исполнения — кластер Temporal зафиксирует ошибку недетерминированности (`NonDeterministicWorkflowPolicy / DeterminismError`) и заблокирует процесс.\n\nЗапрещенные операции внутри Workflow:\n1. ❌ `time.Now()` — при Replay вернет другое время! Используйте `workflow.Now(ctx)`.\n2. ❌ `time.Sleep()` — заблокирует системный поток воркера! Используйте `workflow.Sleep(ctx, d)`.\n3. ❌ `rand.Int()`, `uuid.New()` — сгенерируют другие значения! Используйте `workflow.SideEffect`.\n4. ❌ `go func()` — стандартный планировщик Go недетерминирован! Используйте `workflow.Go(ctx, ...)`.\n5. ❌ Прямой I/O (`http.Get`, `db.Query`, `os.ReadFile`) — сетевые ответы могут измениться. Сайд-эффекты разрешены ТОЛЬКО внутри Activities.\n6. ❌ Итерация по Go-мапе `for k := range m` — в Go порядок обхода мапы рандомизирован рантаймом! Сортируйте ключи перед итерацией.",
        "step_by_step": "1. Сравните недетерминированный антипаттерн и правильный детерминированный код Temporal.\n2. Покажите использование `workflow.Now(ctx)` вместо `time.Now()`.\n3. Реализуйте детерминированную генерацию случайного числа или ID через `workflow.SideEffect`.\n4. Продемонстрируйте детерминированный обход мапы с предварительной сортировкой ключей.",
        "code_blocks": [
            {
                "filename": "workflow.go",
                "lang": "go",
                "code": r"""package main

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"sort"
	"time"

	"go.temporal.io/sdk/workflow"
)

// DeterministicWorkflow демонстрирует строгое следование правилам детерминизма Temporal.
func DeterministicWorkflow(ctx workflow.Context, items map[string]int) (string, error) {
	logger := workflow.GetLogger(ctx)

	// 1. ДЕТЕРМИНИРОВАННОЕ ВРЕМЯ
	// НЕЛЬЗЯ: now := time.Now()
	// ПРАВИЛЬНО: workflow.Now(ctx) возвращает время фиксации события в истории!
	startTime := workflow.Now(ctx)
	logger.Info("Workflow стартовал в детерминированное время", "time", startTime.Format(time.RFC3339))

	// 2. ДЕТЕРМИНИРОВАННЫЙ SIDE EFFECT (генерация UUID / токена)
	// НЕЛЬЗЯ напрямую вызывать rand.Read или uuid.New() в Workflow!
	// workflow.SideEffect выполняет функцию ровно ОДИН раз, сохраняет результат в историю
	// и при Replay просто возвращает сохраненное значение без повторного вызова!
	var requestToken string
	err := workflow.SideEffect(ctx, func(ctx workflow.Context) interface{} {
		b := make([]byte, 8)
		_, _ = rand.Read(b)
		return hex.EncodeToString(b)
	}).Get(&requestToken)
	if err != nil {
		return "", err
	}
	logger.Info("Сгенерирован токен через SideEffect", "token", requestToken)

	// 3. ДЕТЕРМИНИРОВАННЫЙ ОБХОД МАПЫ
	// НЕЛЬЗЯ делать 'for k, v := range items', так как в Go порядок обхода map рандомен!
	// ПРАВИЛЬНО: сортируем ключи перед итерацией
	keys := make([]string, 0, len(items))
	for k := range items {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	totalPrice := 0
	for _, key := range keys {
		totalPrice += items[key]
		logger.Info("Обработка товара", "sku", key, "price", items[key])
	}

	// 4. ДЕТЕРМИНИРОВАННЫЙ ТАЙМЕР
	// НЕЛЬЗЯ: time.Sleep(5 * time.Second)
	// ПРАВИЛЬНО: workflow.Sleep создает durable таймер в кластере Temporal
	if err := workflow.Sleep(ctx, 2*time.Second); err != nil {
		return "", err
	}

	return fmt.Sprintf("Token: %s | Total: %d RUB", requestToken, totalPrice), nil
}

func main() {
	fmt.Println("Демонстрация детерминированного Workflow кода для Temporal.")
	fmt.Println("Все правила проверены: детерминированное время, SideEffect для ID, сортировка map.")
}
"""
            }
        ],
        "under_the_hood": "Под капотом Temporal SDK запускает каждую корутину Workflow в отдельном контролируемом контексте с кастомным планировщиком (Cooperative Coroutine Dispatcher). Когда вызывается `workflow.Now(ctx)`, SDK не обращается к системным часам ядра ОС (TSC / VDSO), а считывает метку времени из заголовка текущего события `WorkflowTaskStarted` в истории событий. При Replay метка времени из истории остается в точности той же самой с наносекундной точностью, обеспечивая 100% повторяемость.",
        "pitfalls": "Коварная ловушка — использование несинхронизированных глобальных переменных или синглтонов. Если два параллельно исполняемых инстанса Workflow будут читать и модифицировать глобальную переменную `var Counter int`, их порядок доступа будет недетерминированным, что гарантированно приведет к сбою Replay и рассинхронизации состояния с кластером.",
        "interview_qa": "В: Что произойдет, если в прод выкатить Workflow с недетерминированным кодом, и кластер обнаружит расхождение при Replay?\nО: Кластер Temporal обнаружит несоответствие команды из кода с историей событий и зафиксирует `WorkflowTaskFailed` с причиной `UnhandledCommand` или `NonDeterministicWorkflowPolicy`. По умолчанию рабочий процесс НЕ завершится с фатальной ошибкой (чтобы не потерять состояние данных). Воркер будет бесконечно повторять выполнение задачи с backoff, ожидая, пока разработчики исправят баг в коде или применят версионирование (`workflow.GetVersion`)."
    },
    {
        "num": 6,
        "title": "Workflow Context vs Стандартный Go context.Context",
        "task": "Изучите интерфейс `workflow.Context`. В чем его фундаментальное отличие от стандартного `context.Context` из стандартной библиотеки Go? Покажите, как `workflow.Context` управляет детерминированным временем через `workflow.Now(ctx)`, логированием через `workflow.GetLogger(ctx)`, перехватом отмены через `workflow.Context.Done()` и передачей параметров выполнения. Напишите код, демонстрирующий безопасную работу с `workflow.Context`.",
        "theory": "В стандартном Go `context.Context` используется для отмены горутин, передачи дедлайнов и значений запроса между системными потоками. Однако стандартный контекст абсолютно не знает о механизме Replay и виртуальном времени Temporal.\n\nПо этой причине Temporal SDK ввел собственный интерфейс `workflow.Context`:\n1. **Виртуализация времени**: стандартный контекст `context.WithTimeout` оперирует физическими системными часами, что сломало бы детерминизм. В `workflow.Context` таймауты привязаны к истории событий кластера.\n2. **Управление отменой**: `workflow.Context.Done()` возвращает `workflow.Channel`, а не стандартный `<-chan struct{}`. Это позволяет координировать отмену через `workflow.Selector`.\n3. **Логирование без дублей**: стандартный `log.Println` или `slog.Info` писал бы логи в stdout при каждом Replay. `workflow.GetLogger(ctx)` автоматически подавляет вывод логов во время Replay, выводя сообщения только при первичном (живом) выполнении кода!\n4. **Передача метаданных и опций**: через `workflow.WithActivityOptions`, `workflow.WithChildOptions` контекст обогащается настройками выполнения.",
        "step_by_step": "1. Продемонстрируйте структуру интерфейса `workflow.Context`.\n2. Покажите правильное получение детерминированного логгера `workflow.GetLogger(ctx)`.\n3. Настройте `workflow.WithActivityOptions` и передайте контекст в выполнение Activity.\n4. Проиллюстрируйте работу с `workflow.Context.Done()` при обработке внешней отмены.",
        "code_blocks": [
            {
                "filename": "context_demo.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/workflow"
)

// SendNotificationActivity — стандартная активность, использующая context.Context из Go.
func SendNotificationActivity(ctx context.Context, message string) error {
	select {
	case <-time.After(100 * time.Millisecond):
		fmt.Printf(" [ACTIVITY] Уведомление отправлено: %s\n", message)
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

// ManagedContextWorkflow демонстрирует работу с workflow.Context.
func ManagedContextWorkflow(ctx workflow.Context, alertText string) (string, error) {
	// 1. Получение логгера, который автоматически фильтрует дубликаты при Replay!
	logger := workflow.GetLogger(ctx)
	logger.Info("Запуск ManagedContextWorkflow", "alert", alertText)

	// 2. Обогащение контекста параметрами Activities (Таймауты, ретраи)
	actOpts := workflow.ActivityOptions{
		StartToCloseTimeout: 5 * time.Second,
		ScheduleToStartTimeout: 10 * time.Second,
	}
	ctxWithOpts := workflow.WithActivityOptions(ctx, actOpts)

	// 3. Вызов активности через workflow.Context
	var actErr error
	err := workflow.ExecuteActivity(ctxWithOpts, SendNotificationActivity, alertText).Get(ctxWithOpts, &actErr)
	if err != nil {
		logger.Error("Ошибка при вызове Activity", "error", err)
		return "", err
	}

	// 4. Проверка отмены процесса
	if ctx.Err() != nil {
		logger.Warn("Workflow был отменен!", "cause", ctx.Err())
		return "CANCELLED", ctx.Err()
	}

	return "SUCCESS", nil
}

func main() {
	fmt.Println("=== Сравнение workflow.Context и context.Context ===")
	fmt.Println("workflow.Context: используется ТОЛЬКО внутри функций Workflow (детерминизм).")
	fmt.Println("context.Context: используется внутри функций Activities (реальный I/O).")
}
"""
            }
        ],
        "under_the_hood": "Под капотом `workflow.Context` хранит указатель на внутреннюю структуру `workflowEnvironmentImpl`. В ней находится таблица детерминированных каналов, инстанс `replayer`, планировщик корутин и текущий срез выполненных событий. Когда воркер находится в режиме Replay, `workflow.GetLogger` проверяет флаг `env.IsReplaying()`. Если флаг равен `true`, логгер мгновенно отбрасывает запись (no-op), предотвращая загрязнение логов в ELK / Loki тысячами дублей при каждом перезапуске воркера.",
        "pitfalls": "Категорически запрещено передавать `workflow.Context` внутрь функции Activity или передавать стандартный `context.Context` в функцию Workflow! В первом случае код просто не скомпилируется, во втором — попытка использовать функции стандартного контекста приведет к недетерминированному поведению и краху Replay.",
        "interview_qa": "В: Как внутри Activity узнать, что родительский Workflow был отменен, чтобы прервать долгий SQL-запрос?\nО: При отмене Workflow кластер Temporal уведомляет воркера, и воркер автоматически отменяет стандартный `context.Context`, переданный в функцию Activity (`ctx.Done()` закрывается). Поэтому, если внутри Activity вы пробрасываете стандартный `ctx context.Context` во все вызовы `db.QueryContext(ctx, ...)` или `http.NewRequestWithContext(ctx, ...)`, запрос мгновенно прервется при отмене процесса."
    },
    {
        "num": 7,
        "title": "Реализация первой Activity (Сетевые вызовы и сайд-эффекты)",
        "task": "Напишите полноценную Activity-функцию `ProcessPaymentActivity(ctx context.Context, req PaymentRequest) (PaymentResponse, error)`. Поскольку Activity выполняется вне детерминированного replay, в ней разрешены любые операции ввода-вывода (HTTP, gRPC, SQL). Продемонстрируйте использование стандартного `context.Context` для обработки сетевых таймаутов, логирование через `activity.GetLogger(ctx)` и извлечение метаданных исполнения через `activity.GetInfo(ctx)`.",
        "theory": "Activities (Действия) в Temporal — это место, где происходит вся реальная работа с внешним миром:\n- Вызовы внешних REST / gRPC API (Stripe, Twilio, SendGrid).\n- Запросы к базам данных (PostgreSQL, MongoDB, Redis).\n- Работа с файловой системой и сетью.\n\nВ отличие от Workflow, функция Activity:\n1. Принимает стандартный `context.Context` в качестве первого аргумента.\n2. Выполняется ровно столько раз, сколько решит кластер в соответствии с `RetryPolicy`.\n3. Не подчиняется правилам детерминизма — в ней можно использовать `time.Now()`, `rand`, горутины и сторонние библиотеки.\n4. Предоставляет доступ к контекстной информации через `activity.GetInfo(ctx)` (WorkflowID, ActivityID, номер текущей попытки `Attempt`, дедлайн).",
        "step_by_step": "1. Определите DTO `PaymentRequest` и `PaymentResponse`.\n2. Реализуйте функцию `ProcessPaymentActivity` с проверкой контекста и имитацией внешнего HTTP-вызова.\n3. Извлеките метаданные выполнения через `activity.GetInfo(ctx)` (Attempt, ActivityType).\n4. Напишите Workflow, вызывающий данную активность и получающий типизированный ответ.",
        "code_blocks": [
            {
                "filename": "activity.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/workflow"
)

type PaymentRequest struct {
	CustomerID string  `json:"customer_id"`
	Amount     float64 `json:"amount"`
	Currency   string  `json:"currency"`
}

type PaymentResponse struct {
	TransactionID string    `json:"transaction_id"`
	Status        string    `json:"status"`
	ProcessedAt   time.Time `json:"processed_at"`
}

// ProcessPaymentActivity — промышленная активность для интеграции с платежным шлюзом.
func ProcessPaymentActivity(ctx context.Context, req PaymentRequest) (*PaymentResponse, error) {
	// Получение логгера активности и метаданных выполнения
	logger := activity.GetLogger(ctx)
	info := activity.GetInfo(ctx)

	logger.Info("Старт ProcessPaymentActivity",
		"activity_id", info.ActivityID,
		"attempt", info.Attempt,
		"workflow_id", info.WorkflowExecution.ID,
		"customer_id", req.CustomerID,
		"amount", req.Amount,
	)

	// Имитация внешнего сетевого запроса с уважением к контексту
	select {
	case <-time.After(200 * time.Millisecond):
		// Успешный ответ внешнего шлюза
		resp := &PaymentResponse{
			TransactionID: fmt.Sprintf("txn_%s_%d", req.CustomerID, time.Now().UnixNano()),
			Status:        "CONFIRMED",
			ProcessedAt:   time.Now().UTC(),
		}
		logger.Info("Платеж успешно авторизован", "txn_id", resp.TransactionID)
		return resp, nil

	case <-ctx.Done():
		logger.Warn("Таймаут или отмена Activity", "error", ctx.Err())
		return nil, ctx.Err()
	}
}

// PaymentWorkflow — рабочий процесс, оркестрирующий вызов активности.
func PaymentWorkflow(ctx workflow.Context, req PaymentRequest) (*PaymentResponse, error) {
	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 10 * time.Second,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var resp PaymentResponse
	err := workflow.ExecuteActivity(ctx, ProcessPaymentActivity, req).Get(ctx, &resp)
	if err != nil {
		return nil, err
	}

	return &resp, nil
}

func main() {
	fmt.Println("Activity успешно реализована с поддержкой context.Context, ActivityInfo и логгера.")
}
"""
            }
        ],
        "under_the_hood": "Когда Workflow вызывает `workflow.ExecuteActivity(ctx, ActivityFunc, args)`, SDK не вызывает функцию напрямую. Вместо этого в кластер Temporal отправляется команда `ScheduleActivityTask`. Кластер кладет задачу в Activity Task Queue. Свободный воркер забирает задачу `PollActivityTaskQueue`, создает новый `context.Context` с дедлайном `StartToCloseTimeout`, вызывает функцию активности, сериализует результат в JSON/Protobuf и отправляет команду `RespondActivityTaskCompleted` обратно в кластер.",
        "pitfalls": "Опасная ошибка — игнорирование `ctx.Done()` в сетевых или долгих вызовах внутри Activity. Если Activity зависнет на вечном чтении сокета без таймаута, воркер исчерпает пул потоков. Всегда передавайте входящий `ctx` в HTTP-клиенты, базы данных и файловые дескрипторы.",
        "interview_qa": "В: Должна ли функция Activity быть строго идемпотентной?\nО: Да, абсолютно! Так как сеть ненадежна, а воркеры могут перезагружаться из-за сбоев инфраструктуры прямо во время выполнения, Temporal может повторить выполнение Activity (Retry). Если Activity не идемпотентна (например, списывает деньги без ключа идемпотентности `Idempotency-Key`), повтор вызовет двойное списание средств с карты клиента."
    },
    {
        "num": 8,
        "title": "Конфигурация таймаутов Activity",
        "task": "Настройте параметры вызова Activity в `workflow.ActivityOptions`: детально разберите различия между `StartToCloseTimeout` (время одного выполнения), `ScheduleToStartTimeout` (время ожидания в очереди), `ScheduleToCloseTimeout` (общее время выполнения со всеми ретраями) и `HeartbeatTimeout`. Напишите Go-код с правильной настройкой каждого таймаута для критической финансовой операции.",
        "theory": "В Temporal таймауты Activity настраиваются через структуру `workflow.ActivityOptions`. Грамотная настройка таймаутов — ключевой навык инженера распределенных систем:\n\n1. **`StartToCloseTimeout` (ОБЯЗАТЕЛЬНЫЙ)**:\n   - Максимальное время, отведенное воркеру на ОДНУ попытку выполнения функции с момента ее старта до завершения.\n   - Если воркер завис или ушел в бесконечный цикл, кластер по истечении этого таймаута признает попытку неудачной и запустит ретрай.\n\n2. **`ScheduleToStartTimeout` (Опциональный)**:\n   - Время, в течение которого задача может находиться в очереди (Task Queue) в ожидании свободного воркера.\n   - Защищает от ситуации, когда очередь переполнена или все воркеры упали. Если таймаут истек — активность отменяется без старта.\n\n3. **`ScheduleToCloseTimeout` (Опциональный)**:\n   - Общее время всего жизненного цикла активности: ожидание в очереди + исполнение + ВСЕ повторные попытки (ретраи).\n   - Задает жесткий SLA (например, операция должна выполниться максимум за 30 минут, сколько бы раз она ни падала).\n\n4. **`HeartbeatTimeout` (Для долгих операций)**:\n   - Максимальный интервал между подтверждениями жизнедеятельности (`RecordHeartbeat`) от воркера.",
        "step_by_step": "1. Изучите поля структуры `workflow.ActivityOptions`.\n2. Настройте конфигурацию таймаутов для быстрой синхронной операции (валидация карты).\n3. Настройте конфигурацию таймаутов для долгой пакетной задачи (генерация выписки за год).\n4. Продемонстрируйте обработку ошибки таймаута `temporal.TimeoutError` в коде Workflow.",
        "code_blocks": [
            {
                "filename": "timeouts.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"time"

	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
)

func FastValidationActivity(ctx context.Context, accountID string) (bool, error) {
	return true, nil
}

func LongReportActivity(ctx context.Context, year int) (string, error) {
	return "s3://reports/2026/annual.pdf", nil
}

// TimeoutWorkflow демонстрирует профессиональную настройку таймаутов.
func TimeoutWorkflow(ctx workflow.Context, accountID string) error {
	logger := workflow.GetLogger(ctx)

	// 1. Быстрая операция (REST API): строгий StartToCloseTimeout
	fastOpts := workflow.ActivityOptions{
		// Обязателен! Если воркер завис — через 5 сек попытка считается сбойной
		StartToCloseTimeout: 5 * time.Second,
		// Если за 30 секунд ни один воркер не взял задачу — значит воркеры лежат
		ScheduleToStartTimeout: 30 * time.Second,
	}
	ctxFast := workflow.WithActivityOptions(ctx, fastOpts)

	var isValid bool
	err := workflow.ExecuteActivity(ctxFast, FastValidationActivity, accountID).Get(ctxFast, &isValid)
	if err != nil {
		var timeoutErr *temporal.TimeoutError
		if errors.As(err, &timeoutErr) {
			logger.Error("Превышен таймаут валидации карты", "timeout_type", timeoutErr.TimeoutType())
		}
		return err
	}

	// 2. Долгая фоновая операция: HeartbeatTimeout + ScheduleToCloseTimeout
	longOpts := workflow.ActivityOptions{
		// Общий SLA: не более 2 часов на всю задачу со всеми ретраями
		ScheduleToCloseTimeout: 2 * time.Hour,
		// Каждая попытка генерации не более 30 минут
		StartToCloseTimeout: 30 * time.Minute,
		// Воркер обязан слать heartbeat минимум раз в 1 минуту
		HeartbeatTimeout: 1 * time.Minute,
	}
	ctxLong := workflow.WithActivityOptions(ctx, longOpts)

	var reportURL string
	err = workflow.ExecuteActivity(ctxLong, LongReportActivity, 2026).Get(ctxLong, &reportURL)
	if err != nil {
		logger.Error("Ошибка генерации отчета", "error", err)
		return err
	}

	logger.Info("Все задачи успешно завершены", "report_url", reportURL)
	return nil
}

func main() {
	fmt.Println("Конфигурация таймаутов проверена: StartToClose, ScheduleToStart, ScheduleToClose, Heartbeat.")
}
"""
            }
        ],
        "under_the_hood": "Кластер Temporal управляет таймаутами с помощью распределенного колеса таймеров (Hashed Wheel Timer / Timer Queue) внутри History Service. Когда активность планируется, в очередь таймеров БД записывается событие с дедлайном. Сервер отслеживает время вне зависимости от того, живы ли воркеры. Если таймер `StartToClose` истекает, History Service генерирует событие `ActivityTaskTimedOut` и принимает решение о перезапуске согласно RetryPolicy.",
        "pitfalls": "Распространенная ошибка — задавать слишком большой `StartToCloseTimeout` (например, 24 часа) для коротких сетевых вызовов в надежде 'чтобы точно успело'. Если узел воркера физически сгорит прямо во время выполнения этой функции, кластер будет ждать целые сутки перед тем, как понять, что воркер мертв, и перезапустить задачу на другом сервере! Для быстрых операций `StartToCloseTimeout` должен быть минимальным (секунды).",
        "interview_qa": "В: В чем разница между таймаутом ScheduleToClose и StartToClose?\nО: `StartToClose` ограничивает время ОДНОЙ конкретной попытки исполнения на воркере. Если попытка завершилась ошибкой или упала по таймауту, Temporal запустит вторую попытку. `ScheduleToClose` ограничивает ОБЩЕЕ время задачи от момента постановки в очередь клиентом до финального завершения, включая все сетевые задержки в очереди и все 10–20 повторных попыток."
    },
    {
        "num": 9,
        "title": "Автоматические повторные попытки (RetryPolicy) в Temporal",
        "task": "Сконфигурируйте политику повторов `temporal.RetryPolicy`: `InitialInterval: 1 * time.Second`, `BackoffCoefficient: 2.0`, `MaximumInterval: 100 * time.Second`, `MaximumAttempts: 5`. Продемонстрируйте, как Temporal автоматически повторяет временно сбоящую Activity без необходимости писать циклы ретраев в Go-коде, а также покажите тонкости настройки экспоненциальной задержки с джиттером (Jitter).",
        "theory": "В распределенных системах временные сбои (Transient Errors) неизбежны: моргание сети, перезапуск базы данных, HTTP 503 Service Unavailable, Rate Limiting внешнего API.\n\nВ традиционном Go-коде разработчики вынуждены вручную писать циклы `for i := 0; i < maxRetries; i++`, нагромождать `time.Sleep` и библиотеки ретраев. В Temporal политика ретраев встроена в ядро платформы на уровне `temporal.RetryPolicy`.\n\nКлючевые параметры `RetryPolicy`:\n- `InitialInterval`: задержка перед первой повторной попыткой.\n- `BackoffCoefficient`: множитель экспоненциального роста задержки (обычно 2.0).\n- `MaximumInterval`: верхняя граница задержки между попытками.\n- `MaximumAttempts`: максимальное число попыток (0 = бесконечное число попыток).\n- `NonRetryableErrorTypes`: список типов ошибок, при которых ретраи немедленно прекращаются.\n\nTemporal автоматически добавляет случайный джиттер (Jitter ±10-20%) к каждому интервалу повтора, предотвращая проблему 'Thundering Herd' (одновременный наплыв сотен ретраев на упавший сервис).",
        "step_by_step": "1. Сконфигурируйте структуру `temporal.RetryPolicy`.\n2. Свяжите политику ретраев с `workflow.ActivityOptions`.\n3. Реализуйте Activity, которая падает с ошибкой на первых двух попытках и успешно завершается на третьей.\n4. Проанализируйте логи, показывающие автоматические повторы кластера Temporal.",
        "code_blocks": [
            {
                "filename": "retry_policy.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"time"

	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
)

// FlakyRemoteServiceActivity имитирует нестабильный внешний сервис.
func FlakyRemoteServiceActivity(ctx context.Context, payload string) (string, error) {
	info := activity.GetInfo(ctx)
	logger := activity.GetLogger(ctx)

	logger.Info("Выполнение попытки Activity", "attempt", info.Attempt)
	fmt.Printf(" [ACTIVITY] Попытка №%d вызова внешнего API...\n", info.Attempt)

	// Первые две попытки падают с временной сетевой ошибкой
	if info.Attempt < 3 {
		return "", errors.New("503 Service Unavailable: upstream connection reset")
	}

	// На третьей попытке сервис отвечает успешно
	fmt.Println(" [ACTIVITY] Внешний API ответил 200 OK!")
	return "RESPONSE_DATA: " + payload, nil
}

// ResilientWorkflow использует RetryPolicy для прозрачной компенсации сбоев.
func ResilientWorkflow(ctx workflow.Context, data string) (string, error) {
	retryPolicy := &temporal.RetryPolicy{
		InitialInterval:        1 * time.Second,
		BackoffCoefficient:     2.0,
		MaximumInterval:        10 * time.Second,
		MaximumAttempts:        5, // Максимум 5 попыток
		NonRetryableErrorTypes: []string{"InvalidInputError"},
	}

	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 5 * time.Second,
		RetryPolicy:         retryPolicy,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var result string
	err := workflow.ExecuteActivity(ctx, FlakyRemoteServiceActivity, data).Get(ctx, &result)
	if err != nil {
		return "", fmt.Errorf("все попытки исчерпаны: %w", err)
	}

	return result, nil
}

func main() {
	fmt.Println("Демонстрация экспоненциального RetryPolicy в Temporal SDK.")
}
"""
            }
        ],
        "under_the_hood": "При падении Activity воркер отправляет в кластер Temporal команду `RespondActivityTaskFailed`. Кластер смотрит на `RetryPolicy`. Если лимит попыток не исчерпан, кластер НЕ будит Workflow! Вместо этого Matching Service планирует отложенную задачу в очереди с таймером backoff. Во время ожидания повторной попытки воркер освобожден и не тратит оперативную память. Только когда попытка увенчается успехом или исчерпает лимит, кластер передаст управление обратно в Workflow.",
        "pitfalls": "По умолчанию в Temporal `MaximumAttempts` равен 0 (бесконечные ретраи)! Для критических бизнес-задач это благо, но если вы обращаетесь к внешнему сервису без настроенного таймаута `ScheduleToCloseTimeout`, упавший сторонний API может заставить ваш процесс висеть на ретраях месяцами. Всегда осознанно настраивайте либо `MaximumAttempts`, либо `ScheduleToCloseTimeout`.",
        "interview_qa": "В: Зачем Temporal добавляет джиттер (Jitter) к интервалам RetryPolicy?\nО: Если внешняя база данных перезагрузилась, и 10 000 одновременно выполнявшихся транзакций упали ровно в 12:00:00, то при фиксированном интервале ретрая в 2 секунды все 10 000 процессов одновременно ударят по только что поднявшейся БД в 12:00:02, снова уронив ее (Thundering herd / Retry storm). Джиттер размазывает моменты повторных запросов во времени по случайному гауссовскому распределению."
    },
    {
        "num": 10,
        "title": "Неповторяемые ошибки (Non-Retryable Application Errors)",
        "task": "Если платежная карта заблокирована, введен неверный CVV или на счете недостаточно средств, повторять вызов через RetryPolicy бессмысленно — это лишь потратит квоты и время. Реализуйте возврат неповторяемой ошибки: `temporal.NewNonRetryableApplicationError('insufficient funds', 'INSUFFICIENT_FUNDS', nil)`. Убедитесь, что Temporal мгновенно прерывает ретраи и немедленно возвращает ошибку в Workflow для обработки альтернативной бизнес-ветки.",
        "theory": "Ошибки в распределенных приложениях делятся на две фундаментальные категории:\n\n1. **Transient Errors (Временные сбои)**:\n   - Таймауты сокетов, HTTP 500, 502, 503, дедлоки в БД.\n   - Их ОБЯЗАТЕЛЬНО нужно повторять (Retry).\n\n2. **Business / Permanent Errors (Бизнес-ошибки / Фатальные ошибки)**:\n   - 400 Bad Request, 401 Unauthorized, 'Недостаточно средств', 'Пользователь заблокирован', 'Неверный формат email'.\n   - Повторять такие вызовы бессмысленно — результат никогда не изменится.\n\nДля классификации таких ошибок Temporal предоставляет функцию `temporal.NewNonRetryableApplicationError(msg, errType, details)`. Когда Activity возвращает такую ошибку, Temporal SDK и кластер мгновенно отключают политику повторов (даже если настроено `MaximumAttempts: 100`) и немедленно пробрасывают ошибку в код Workflow.",
        "step_by_step": "1. Создайте структуру ошибки бизнес-валидации.\n2. В Activity проверьте баланс счета: если баланс < суммы, верните `temporal.NewNonRetryableApplicationError`.\n3. В коде Workflow настройте RetryPolicy с 10 попытками.\n4. Перехватите ошибку в Workflow с помощью `errors.As` и `temporal.ApplicationError`.\n5. Зафиксируйте мгновенное прерывание ретраев.",
        "code_blocks": [
            {
                "filename": "non_retryable.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"time"

	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
)

type AccountDebitRequest struct {
	AccountID string
	Amount    int
}

// DebitAccountActivity списывает деньги со счета клиента.
func DebitAccountActivity(ctx context.Context, req AccountDebitRequest) error {
	fmt.Printf(" [ACTIVITY] Проверка баланса аккаунта %s на сумму %d руб...\n", req.AccountID, req.Amount)

	// Имитация бизнес-проверки: недостаточно средств
	if req.Amount > 10000 {
		fmt.Println(" [ACTIVITY] ❌ Ошибка: Недостаточно средств на балансе!")
		// Возвращаем специальную ошибку, отменяющую любые ретраи!
		return temporal.NewNonRetryableApplicationError(
			"на счете недостаточно средств для списания",
			"ERR_INSUFFICIENT_FUNDS",
			nil,
		)
	}

	fmt.Println(" [ACTIVITY] ✅ Средства успешно списаны.")
	return nil
}

// PurchaseWorkflow оркестрирует покупку с обработкой бизнес-ошибок.
func PurchaseWorkflow(ctx workflow.Context, req AccountDebitRequest) (string, error) {
	logger := workflow.GetLogger(ctx)

	// Настроена агрессивная политика ретраев
	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 5 * time.Second,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    1 * time.Second,
			BackoffCoefficient: 2.0,
			MaximumAttempts:    10, // Должно было повторяться 10 раз!
		},
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	err := workflow.ExecuteActivity(ctx, DebitAccountActivity, req).Get(ctx, nil)
	if err != nil {
		var appErr *temporal.ApplicationError
		if errors.As(err, &appErr) {
			logger.Warn("Перехвачена бизнес-ошибка в Workflow",
				"type", appErr.Type(),
				"message", appErr.Error(),
				"non_retryable", appErr.NonRetryable(),
			)

			if appErr.Type() == "ERR_INSUFFICIENT_FUNDS" {
				return "PURCHASE_REJECTED: Пополните баланс", nil
			}
		}
		return "", err
	}

	return "PURCHASE_SUCCESS", nil
}

func main() {
	fmt.Println("Демонстрация работы NonRetryableApplicationError в Temporal.")
}
"""
            }
        ],
        "under_the_hood": "При возврате ошибки из Activity Go SDK проверяет, реализует ли ошибка интерфейс с методом `NonRetryable() bool`. Если флаг установлен, воркер передает в protobuf-сообщении `RespondActivityTaskFailed` поле `Failure.ApplicationFailureInfo.NonRetryable = true`. Matching и History Service кластера видят этот флаг, игнорируют счетчик попыток и сразу планируют событие `ActivityTaskFailed` для рабочего процесса.",
        "pitfalls": "Опасность кроется в оборачивании ошибки. Если вы обернете `temporal.NewNonRetryableApplicationError` через стандартный `fmt.Errorf('context: %v', err)` без спецификатора `%w`, вы потеряете структуру типа ошибки, и Temporal посчитает ее обычной временной ошибкой, начав бесполезно повторять вызов 10 раз.",
        "interview_qa": "В: Как добавить ошибки определенного стороннего пакета в список неповторяемых, не изменяя код самой Activity?\nО: В поле `RetryPolicy.NonRetryableErrorTypes` можно передать срез строк с именами типов ошибок (например, `[]string{'InvalidCardError', 'AccountNotFoundError'}`). Temporal автоматически сравнит имя типа возвращенной ошибки с этим списком и отменит ретраи."
    },
    {
        "num": 11,
        "title": "Activity Heartbeating для длительных операций",
        "task": "При выполнении тяжелой длительной задачи (транскодирование видео на 2 часа, парсинг архивов) воркер может зависнуть или умереть. Реализуйте отправку контрольных сигналов жизнедеятельности `activity.RecordHeartbeat(ctx, progress)`. Установите `HeartbeatTimeout: 30 * time.Second`. Продемонстрируйте, как при аварийном падении воркера Temporal быстро обнаруживает сбой и перезапускает активность на другом воркере с последней контрольной точки (Checkpointed Details).",
        "theory": "Если Activity длится 1–2 часа, нельзя устанавливать `StartToCloseTimeout: 2h` без дополнительного контроля. Если сервер сгорит на первой минуте, кластер узнает об этом лишь через 2 часа!\n\nРешение проблемы — **Heartbeating (Пульс)**:\n1. В `ActivityOptions` задается `HeartbeatTimeout: 30s`.\n2. Воркер в цикле обработки вызывает `activity.RecordHeartbeat(ctx, progressData)` каждые несколько секунд.\n3. Если кластер не получает heartbeat дольше 30 секунд, воркер объявляется мертвым, а активность немедленно переназначается другому воркеру.\n4. Новый воркер через `activity.GetHeartbeatDetails(ctx, &savedProgress)` извлекает последнюю сохраненную контрольную точку и продолжает работу с того места, где упал предшественник!",
        "step_by_step": "1. Сконфигурируйте `HeartbeatTimeout` в `workflow.ActivityOptions`.\n2. В Activity организуйте цикл обработки 100 чанков данных.\n3. На каждой итерации вызывайте `activity.RecordHeartbeat(ctx, currentStep)`.\n4. Реализуйте восстановление прогресса через `activity.HasHeartbeatDetails` и `activity.GetHeartbeatDetails`.\n5. Обработайте отмену через проверку контекста `ctx.Done()`.",
        "code_blocks": [
            {
                "filename": "heartbeat.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/workflow"
)

type BatchProgress struct {
	ProcessedChunks int `json:"processed_chunks"`
	TotalChunks     int `json:"total_chunks"`
}

// TranscodeVideoActivity выполняет тяжелую задачу с отправкой Heartbeat и чекпоинтами.
func TranscodeVideoActivity(ctx context.Context, totalChunks int) error {
	logger := activity.GetLogger(ctx)

	// Проверяем: это повторная попытка после сбоя?
	startChunk := 0
	if activity.HasHeartbeatDetails(ctx) {
		var lastProgress BatchProgress
		if err := activity.GetHeartbeatDetails(ctx, &lastProgress); err == nil {
			startChunk = lastProgress.ProcessedChunks
			logger.Info("Восстановление прогресса из Heartbeat Details", "start_chunk", startChunk)
			fmt.Printf(" [ACTIVITY] 🔄 Восстановлен прогресс: продолжаем с чанка %d из %d\n", startChunk, totalChunks)
		}
	}

	for i := startChunk; i < totalChunks; i++ {
		// Проверка отмены или таймаута
		if ctx.Err() != nil {
			logger.Warn("Activity отменена во время выполнения чанка", "chunk", i)
			return ctx.Err()
		}

		// Имитация полезной работы над чанком видео
		time.Sleep(100 * time.Millisecond)

		// Фиксация пульса и сохранение чекпоинта
		progress := BatchProgress{
			ProcessedChunks: i + 1,
			TotalChunks:     totalChunks,
		}
		activity.RecordHeartbeat(ctx, progress)
		fmt.Printf(" [ACTIVITY] Обработан чанк %d/%d (Heartbeat записан)\n", i+1, totalChunks)
	}

	logger.Info("Транскодирование успешно завершено!")
	return nil
}

// VideoWorkflow запускает тяжелую задачу с HeartbeatTimeout.
func VideoWorkflow(ctx workflow.Context, chunks int) error {
	ao := workflow.ActivityOptions{
		// Общий таймаут попытки может быть большим
		StartToCloseTimeout: 1 * time.Hour,
		// Но пульс должен приходить не реже, чем раз в 5 секунд!
		HeartbeatTimeout: 5 * time.Second,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	return workflow.ExecuteActivity(ctx, TranscodeVideoActivity, chunks).Get(ctx, nil)
}

func main() {
	fmt.Println("Демонстрация Heartbeating с сохранением чекпоинтов в Temporal.")
}
"""
            }
        ],
        "under_the_hood": "Чтобы не заспамить кластер тысячами сетевых вызовов, Temporal Go SDK реализует внутренний троттлинг (Throttling) вызовов `activity.RecordHeartbeat`. По умолчанию SDK отправляет heartbeat в кластер по gRPC не чаще, чем раз в 80% от `HeartbeatTimeout`. Данные чекпоинта сохраняются в памяти кластера и при перезапуске задачи передаются новому воркеру в поле `PollActivityTaskQueueResponse.HeartbeatDetails`.",
        "pitfalls": "Не передавайте в `RecordHeartbeat` мегабайтные структуры данных. Детали пульса сохраняются в историю событий кластера. Если отправлять гигантские пейлоады каждую секунду, история превысит лимиты кластера (Blob size limit) и приведет к ошибке.",
        "interview_qa": "В: Как Heartbeat помогает в оперативной отмене (Cancellation) долгой Activity?\nО: Если пользователь отменил Workflow, кластер не может принудительно убить поток воркера по сети. Вместо этого кластер отвечает на очередной вызов `activity.RecordHeartbeat` специальной ошибкой `ErrActivityCanceled`. SDK ловит этот ответ и немедленно отменяет `context.Context` функции Activity, позволяя коду быстро и корректно освободить ресурсы."
    },
    {
        "num": 12,
        "title": "Параллельное выполнение Activities через workflow.Go",
        "task": "Вам необходимо одновременно забронировать отель, авиабилеты и аренду автомобиля для путешествия. Используйте детерминированную конкурентность Temporal: запустите действия параллельно с помощью `workflow.Go(ctx, func(ctx workflow.Context) { ... })` и соберите результаты через `workflow.Selector` или детерминированные каналы `workflow.Channel`. Покажите, почему стандартные каналы и `go func()` запрещены.",
        "theory": "В стандартном Go для конкурентного выполнения задач используются горутины `go func()` и каналы `make(chan T)`. Однако планировщик Go рантайма недетерминирован — очередность переключения горутин зависит от загрузки ядер процессора и операционной системы. Использование `go func()` в Workflow гарантированно сломает Replay!\n\nTemporal SDK предоставляет детерминированную замену:\n- `workflow.Go(ctx, func(ctx workflow.Context) { ... })` — запускает легковесную корутину, управляемую детерминированным планировщиком Temporal.\n- `workflow.NewChannel(ctx)` — детерминированный аналог каналов Go.\n- `workflow.NewSelector(ctx)` — детерминированный аналог оператора `select`.\n- `workflow.Future` — объект будущего результата (Promise), позволяющий запустить несколько активностей и дождаться их завершения параллельно.",
        "step_by_step": "1. Опишите три активности: `BookFlight`, `BookHotel`, `BookCar`.\n2. Реализуйте параллельный запуск трех активностей через `workflow.ExecuteActivity` без немедленного вызова `.Get()`.\n3. Соберите несколько `workflow.Future`.\n4. Используйте `workflow.NewSelector` или параллельное ожидание фьючерсов для сбора результатов.\n5. Замерьте суммарное время исполнения процесса (оно равно времени самой долгой активности).",
        "code_blocks": [
            {
                "filename": "parallel.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/workflow"
)

func BookFlightActivity(ctx context.Context, destination string) (string, error) {
	fmt.Printf(" [ACTIVITY] Бронирование авиабилетов в %s...\n", destination)
	return "FLIGHT_SU_102", nil
}

func BookHotelActivity(ctx context.Context, hotelName string) (string, error) {
	fmt.Printf(" [ACTIVITY] Бронирование отеля %s...\n", hotelName)
	return "HOTEL_RES_991", nil
}

func BookCarActivity(ctx context.Context, carModel string) (string, error) {
	fmt.Printf(" [ACTIVITY] Аренда автомобиля %s...\n", carModel)
	return "CAR_RENT_554", nil
}

type TravelPackage struct {
	FlightRef string
	HotelRef  string
	CarRef    string
}

// ParallelTravelWorkflow запускает бронирования параллельно.
func ParallelTravelWorkflow(ctx workflow.Context) (*TravelPackage, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Старт параллельного бронирования путешествия")

	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 10 * time.Second,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	// Запуск активностей без блокирующего .Get() — они выполняются параллельно!
	futureFlight := workflow.ExecuteActivity(ctx, BookFlightActivity, "Tokyo")
	futureHotel := workflow.ExecuteActivity(ctx, BookHotelActivity, "Hilton Tokyo")
	futureCar := workflow.ExecuteActivity(ctx, BookCarActivity, "Toyota Prius")

	pkg := &TravelPackage{}

	// Дожидаемся результатов параллельных Futures
	if err := futureFlight.Get(ctx, &pkg.FlightRef); err != nil {
		return nil, fmt.Errorf("ошибка бронирования авиабилетов: %w", err)
	}
	if err := futureHotel.Get(ctx, &pkg.HotelRef); err != nil {
		return nil, fmt.Errorf("ошибка бронирования отеля: %w", err)
	}
	if err := futureCar.Get(ctx, &pkg.CarRef); err != nil {
		return nil, fmt.Errorf("ошибка бронирования авто: %w", err)
	}

	logger.Info("Все бронирования успешно подтверждены параллельно!",
		"flight", pkg.FlightRef, "hotel", pkg.HotelRef, "car", pkg.CarRef)

	return pkg, nil
}

func main() {
	fmt.Println("Демонстрация параллельного запуска Activities через workflow.Future.")
}
"""
            }
        ],
        "under_the_hood": "Когда в одном цикле Workflow вызываются три `ExecuteActivity`, SDK формирует три команды `ScheduleActivityTask` и отправляет их в кластер в одном пакете (Batch). Кластер помещает все три задачи в очередь одновременно. Если у вас запущено несколько воркеров, они параллельно разберут эти задачи. Завершение активностей фиксируется событиями `ActivityTaskCompleted`. При Replay порядок завершения строго воспроизводится из сохраненной истории событий.",
        "pitfalls": "Никогда не используйте стандартный `sync.WaitGroup` или `sync.Mutex` внутри кода Workflow! Используйте `workflow.WaitGroup` или `workflow.Channel` из пакета `go.temporal.io/sdk/workflow`. Использование стандартных примитивов синхронизации заблокирует рантайм Temporal и вызовет дедлок воркера.",
        "interview_qa": "В: Как реализовать паттерн 'Кто первый ответит' (Fastest Responder) среди трех внешних сервисов котировок?\nО: Запустите три `workflow.Future` и используйте `selector := workflow.NewSelector(ctx)`. Добавьте каждый future через `selector.AddFuture(f, callback)`. Метод `selector.Select(ctx)` разблокируется, как только завершится САМЫЙ ПЕРВЫЙ future. После этого не забудьте отменить оставшиеся активности."
    },
    {
        "num": 13,
        "title": "Сигналы (Signals): Асинхронное взаимодействие с Workflow",
        "task": "Реализуйте прием внешних асинхронных сигналов в работающий Workflow. Создайте канал сигналов `signalChan := workflow.GetSignalChannel(ctx, 'PaymentConfirmedSignal')`. Напишите Workflow заказа, который засыпает и ждет сигнал оплаты. Напишите клиентский HTTP-хэндлер, который при получении вебхука от платежного шлюза отправляет сигнал в работающий процесс через `client.SignalWorkflow(...)`.",
        "theory": "Сигналы (Signals) в Temporal — это механизм асинхронной доставки внешних событий в работающий экземпляр Workflow.\n\nПримеры использования сигналов:\n- Вебхук подтверждения платежа от банка.\n- Пользователь нажал кнопку 'Отменить заказ' в мобильном приложении.\n- Изменение адреса доставки в ходе сборки посылки.\n\nСвойства сигналов:\n1. **Durable & Buffered**: если сигнал отправлен в процесс до того, как код Workflow дошел до чтения канала, сигнал НЕ теряется. Он буферизуется в кластере и будет доставлен сразу же, как откроется канал.\n2. **Гарантия доставки**: отправка сигнала фиксируется в неизменяемой истории событий (`WorkflowExecutionSignaled`).\n3. **Не нарушает детерминизм**: сигналы обрабатываются строго последовательно в детерминированном порядке их записи в историю.",
        "step_by_step": "1. Определите структуру сигнала `PaymentSignalPayload` (TransactionID, Amount).\n2. В Workflow откройте сигнальный канал через `workflow.GetSignalChannel`.\n3. Организуйте ожидание сигнала через `workflow.Selector` с таймаутом ожидания в 1 час.\n4. Напишите код отправки сигнала через `client.Client.SignalWorkflow`.",
        "code_blocks": [
            {
                "filename": "signals.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/workflow"
)

type PaymentSignalPayload struct {
	PaymentID string  `json:"payment_id"`
	Amount    float64 `json:"amount"`
}

const PaymentSignalName = "PaymentConfirmedSignal"

// AwaitPaymentWorkflow ожидает внешний сигнал оплаты.
func AwaitPaymentWorkflow(ctx workflow.Context, orderID string) (string, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Workflow запущен. Ожидание сигнала оплаты...", "order_id", orderID)

	// Получаем сигнальный канал
	signalChan := workflow.GetSignalChannel(ctx, PaymentSignalName)

	var signalData PaymentSignalPayload
	hasSignal := false

	// Используем Selector для ожидания сигнала ИЛИ истечения таймаута
	selector := workflow.NewSelector(ctx)

	// Ветка 1: получение сигнала
	selector.AddReceive(signalChan, func(c workflow.ReceiveChannel, more bool) {
		c.Receive(ctx, &signalData)
		hasSignal = true
		logger.Info("Сигнал оплаты успешно получен!", "payment_id", signalData.PaymentID)
	})

	// Ветка 2: таймаут 24 часа (детерминированный таймер)
	timerFuture := workflow.NewTimer(ctx, 24*time.Hour)
	selector.AddFuture(timerFuture, func(f workflow.Future) {
		logger.Warn("Таймаут оплаты истек! Заказ отменяется.")
	})

	// Ожидаем срабатывания одной из веток
	selector.Select(ctx)

	if !hasSignal {
		return "ORDER_EXPIRED", nil
	}

	return fmt.Sprintf("ORDER_PAID: txn=%s amount=%.2f", signalData.PaymentID, signalData.Amount), nil
}

// SendPaymentWebhook имитирует внешний HTTP-хэндлер вебхука.
func SendPaymentWebhook(c client.Client, workflowID, paymentID string, amount float64) error {
	payload := PaymentSignalPayload{
		PaymentID: paymentID,
		Amount:    amount,
	}

	// Отправка сигнала в работающий Workflow
	err := c.SignalWorkflow(context.Background(), workflowID, "", PaymentSignalName, payload)
	if err != nil {
		return fmt.Errorf("не удалось отправить сигнал в Temporal: %w", err)
	}

	fmt.Printf(" [CLIENT] Сигнал '%s' успешно отправлен в Workflow '%s'\n", PaymentSignalName, workflowID)
	return nil
}

func main() {
	fmt.Println("Демонстрация сигналов (Signals) в Temporal.")
}
"""
            }
        ],
        "under_the_hood": "Когда внешний клиент вызывает `c.SignalWorkflow`, gRPC-запрос идет в Frontend -> History Service. History Service проверяет, существует ли запущенный процесс, и атомарно записывает событие `WorkflowExecutionSignaled` в журнал истории в БД. Если воркер в этот момент спал или был выгружен из памяти, кластер планирует задачу `WorkflowTaskScheduled` в Task Queue, будит воркера и доставляет сигнал в сигнальный канал детерминированного селектора.",
        "pitfalls": "Сигнал — это операция типа 'Fire-and-Forget'. Метод `SignalWorkflow` подтверждает лишь то, что сигнал записан в базу данных кластера, но НЕ возвращает результат обработки из Workflow клиенту! Если клиенту необходимо синхронно валидировать данные и получить результат выполнения команды, используйте **Workflow Update API**.",
        "interview_qa": "В: Что произойдет, если в Workflow отправить 10 000 сигналов подряд за одну секунду?\nО: Возникнет деградация производительности (Signal Flooding). Каждое получение сигнала добавляет минимум два события в историю. Если история превысит рекомендуемый лимит (10 000–50 000 событий), кластер начнет предупреждать об опасности, а Replay замедлится. Для защиты от перегрузки история должна периодически сбрасываться через паттерн `Continue-As-New`."
    },
    {
        "num": 14,
        "title": "Запросы (Queries): Синхронное чтение состояния Workflow",
        "task": "Как узнать текущий статус выполнения многодневного бизнес-процесса без изменения его истории и состояния? Зарегистрируйте Query-хэндлер внутри Workflow: `workflow.SetQueryHandler(ctx, 'getStatus', func() (OrderStatus, error) { return currentStatus, nil })`. Напишите клиентский код, вызывающий `client.QueryWorkflow(...)` для мгновенного синхронного получения статуса.",
        "theory": "Запросы (Queries) в Temporal — это механизм строго синхронного чтения внутреннего состояния Workflow в реальном времени.\n\nКлючевые свойства Queries:\n1. **Zero Side Effects**: Query является строго read-only операцией. Запрос НЕ записывает никаких событий в журнал истории Temporal Cluster.\n2. **Мгновенный ответ**: клиент делает вызов `c.QueryWorkflow(...)` и получает текущие значения локальных переменных Workflow.\n3. **Как это работает**: Кластер направляет запрос свободному воркеру. Воркер берет текущее состояние процесса из кэша (Sticky Cache) или быстро проигрывает Replay и вызывает зарегистрированную функцию Query Handler, возвращая результат клиенту.",
        "step_by_step": "1. Опишите структуру состояния `WorkflowStatus` (CurrentStep, Percent, UpdatedAt).\n2. Внутри Workflow зарегистрируйте хэндлер через `workflow.SetQueryHandler(ctx, 'getProgress', ...)`.\n3. В процессе выполнения долгой логики обновляйте локальную переменную статуса.\n4. Напишите клиентскую функцию для отправки синхронного запроса `c.QueryWorkflow`.",
        "code_blocks": [
            {
                "filename": "queries.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/workflow"
)

type ProcessProgress struct {
	CurrentStep string    `json:"current_step"`
	Percent     int       `json:"percent"`
	LastUpdated time.Time `json:"last_updated"`
}

const ProgressQueryType = "getProgress"

// MonitoredWorkflow демонстрирует использование Query для мониторинга состояния.
func MonitoredWorkflow(ctx workflow.Context) (string, error) {
	state := ProcessProgress{
		CurrentStep: "INITIALIZING",
		Percent:     0,
		LastUpdated: workflow.Now(ctx),
	}

	// Регистрация синхронного Query Handler
	err := workflow.SetQueryHandler(ctx, ProgressQueryType, func() (ProcessProgress, error) {
		return state, nil
	})
	if err != nil {
		return "", err
	}

	// Шаг 1
	state.CurrentStep = "DOWNLOADING_DATA"
	state.Percent = 25
	state.LastUpdated = workflow.Now(ctx)
	_ = workflow.Sleep(ctx, 2*time.Second)

	// Шаг 2
	state.CurrentStep = "PROCESSING_AI_MODEL"
	state.Percent = 75
	state.LastUpdated = workflow.Now(ctx)
	_ = workflow.Sleep(ctx, 2*time.Second)

	// Финал
	state.CurrentStep = "COMPLETED"
	state.Percent = 100
	state.LastUpdated = workflow.Now(ctx)

	return "SUCCESS", nil
}

// CheckWorkflowProgress синхронно опрашивает состояние процесса из API шлюза.
func CheckWorkflowProgress(c client.Client, workflowID string) (*ProcessProgress, error) {
	resp, err := c.QueryWorkflow(context.Background(), workflowID, "", ProgressQueryType)
	if err != nil {
		return nil, fmt.Errorf("ошибка выполнения Query: %w", err)
	}

	var progress ProcessProgress
	if err := resp.Get(&progress); err != nil {
		return nil, fmt.Errorf("ошибка десериализации результата: %w", err)
	}

	return &progress, nil
}

func main() {
	fmt.Println("Демонстрация QueryHandler в Temporal для безопасного синхронного чтения.")
}
"""
            }
        ],
        "under_the_hood": "Когда клиент вызывает `QueryWorkflow`, кластер Temporal отправляет команду `WorkflowTaskQuery` воркеру. Если процесс уже закэширован в Sticky Cache памяти воркера, воркер мгновенно вызывает замыкание QueryHandler и возвращает ответ за 1–2 миллисекунды без обращения к БД! Если кэш пуст, воркер за доли секунды проигрывает Replay истории, восстанавливая точное состояние переменных.",
        "pitfalls": "Категорически запрещено внутри Query Handler мутировать переменные состояния Workflow или вызывать сайд-эффекты! Поскольку Query не оставляет следов в истории, любая мутация сделает состояние процесса недетерминированным и сломает систему.",
        "interview_qa": "В: Можно ли отправить Query в Workflow, который уже завершился (Completed / Failed / Canceled)?\nО: Да! Вы можете вызывать Query даже к процессам, завершившимся год назад (если их история сохранена в кластере). Воркер скачает историю, проиграет Replay до финального состояния и вернет вам финальный статус."
    },
    {
        "num": 15,
        "title": "Таймеры в Temporal: Сон на дни и месяцы без расхода ресурсов",
        "task": "Реализуйте шаг бизнес-логики: 'Если пользователь не активировал аккаунт в течение 7 дней, отправить напоминание; если не активировал за 30 дней — деактивировать профиль'. Используйте `workflow.Sleep(ctx, 7 * 24 * time.Hour)`. Объясните, почему во время сна процесс не потребляет CPU и RAM сервера, и как Temporal надежно пробуждает миллионы спящих процессов точно в срок.",
        "theory": "В классическом программировании вызов `time.Sleep(30 * 24 * time.Hour)` в веб-сервере — безумие: горутина удерживает память стека, процесс привязан к серверу, а при первом перезапуске пода таймер сбрасывается и теряется.\n\nВ Temporal метод `workflow.Sleep(ctx, duration)` превращает сон в надежную инфраструктурную операцию:\n1. **Zero Resource Consumption**: при вызове сна воркер выгружает экземпляр Workflow из оперативной памяти (Eviction). Ни один байт RAM или CPU воркера не расходуется.\n2. **Durable Timers в БД**: кластер сохраняет в постоянную БД событие `TimerStarted` с точной меткой времени пробуждения.\n3. **Масштабируемость**: в одном кластере Temporal могут одновременно спать сотни миллионов процессов на протяжении недель, месяцев и даже лет.\n4. **Надежность**: если вся инфраструктура упадет на неделю, после восстановления Temporal мгновенно определит просроченные таймеры и запустит все накопившиеся процессы.",
        "step_by_step": "1. Спроектируйте Workflow онбординга пользователя.\n2. Реализуйте фазу ожидания 7 дней через `workflow.Sleep`.\n3. Отправьте напоминание через Activity `SendReminderActivity`.\n4. Реализуйте вторую фазу сна еще на 23 дня (суммарно 30 дней).\n5. Вызовите финальную деактивацию аккаунта при отсутствии активности.",
        "code_blocks": [
            {
                "filename": "durable_timers.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/workflow"
)

func SendReminderActivity(ctx context.Context, email string) error {
	fmt.Printf(" [ACTIVITY] Отправка напоминания на %s: 'Не забудьте подтвердить email!'\n", email)
	return nil
}

func DeactivateAccountActivity(ctx context.Context, email string) error {
	fmt.Printf(" [ACTIVITY] ❌ Аккаунт %s деактивирован из-за неактивности (прошло 30 дней).\n", email)
	return nil
}

// UserOnboardingWorkflow иллюстрирует долгоживущие таймеры Temporal.
func UserOnboardingWorkflow(ctx workflow.Context, userEmail string) error {
	logger := workflow.GetLogger(ctx)
	logger.Info("Старт онбординга пользователя", "email", userEmail)

	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 10 * time.Second,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	// Этап 1: Спим 7 дней без расхода CPU и памяти!
	logger.Info("Процесс уходит в сон на 7 дней...")
	if err := workflow.Sleep(ctx, 7*24*time.Hour); err != nil {
		return err // Обработка отмены
	}

	// Пробуждение через 7 дней
	logger.Info("Пробуждение через 7 дней. Отправка напоминания...")
	if err := workflow.ExecuteActivity(ctx, SendReminderActivity, userEmail).Get(ctx, nil); err != nil {
		return err
	}

	// Этап 2: Спим еще 23 дня (суммарно 30 дней со старта)
	logger.Info("Процесс уходит в сон еще на 23 дня...")
	if err := workflow.Sleep(ctx, 23*24*time.Hour); err != nil {
		return err
	}

	// Финал: удаление неактивного профиля
	logger.Info("30 дней истекли без подтверждения. Деактивация...")
	return workflow.ExecuteActivity(ctx, DeactivateAccountActivity, userEmail).Get(ctx, nil)
}

func main() {
	fmt.Println("Демонстрация долгоживущих durable таймеров в Temporal.")
}
"""
            }
        ],
        "under_the_hood": "Сервис History в Temporal Cluster организует таймеры в шардированную таблицу очередей таймеров (Timer Queue). Фоновые системные шарды периодически вычитывают батчи таймеров, чей `VisibilityTime <= Now()`. Когда время наступает, генерируется событие `TimerFired`, и в Matching Service ставится задача на пробуждение соответствующего Workflow.",
        "pitfalls": "Помните, что `workflow.Sleep` возвращает ошибку, если Workflow был принудительно отменен (Canceled). Всегда проверяйте возвращаемую ошибку `if err := workflow.Sleep(...); err != nil`, чтобы корректно отреагировать на отмену процесса.",
        "interview_qa": "В: Насколько точны таймеры в Temporal? Можно ли использовать workflow.Sleep для миллисекундных высокочастотных пауз?\nО: Таймеры Temporal оптимизированы для надежной бизнес-логики (секунды, минуты, дни). Гарантированная точность таймеров обычно составляет от 100 миллисекунд до 1 секунды из-за распределенного цикла таймер-очереди кластера. Для ультра-низколатентных пауз в микросекунды следует использовать локальные паузы внутри Activity."
    },
    {
        "num": 16,
        "title": "Паттерн Human-in-the-Loop (Согласование человеком)",
        "task": "Спроектируйте процесс выдачи кредита: автоматический скоринг -> если сумма > 1 000 000 руб, Workflow засыпает и ждет сигнал согласования от менеджера (`ManagerApprovalSignal`) в течение 3 дней. При получении сигнала кредит одобряется, при истечении 3 дней без ответа — автоматически отклоняется по таймауту. Реализуйте паттерн Human-in-the-Loop на Go.",
        "theory": "Паттерн **Human-in-the-Loop (HITL)** — одна из сильнейших сторон Temporal. Во многих enterprise-системах автоматические шаги чередуются с ручными решениями людей:\n- Одобрение выдачи крупного кредита андеррайтером.\n- Подтверждение возврата дорогостоящего товара службой безопасности.\n- Ручной аудит подозрительного платежа финмониторингом.\n\nВ традиционной архитектуре для этого создают отдельные таблицы ожидания, cron-скрипты проверки просрочки и сложные связки API. В Temporal этот паттерн реализуется одной конструкцией: ожидание сигнала через `workflow.Selector` параллельно с durable-таймером.",
        "step_by_step": "1. Опишите модель заявки на кредит `LoanApplication`.\n2. Реализуйте автоматический скоринг через Activity.\n3. Если сумма > 1 млн рублей, активируйте ожидание сигнала `ManagerApprovalSignal` с таймером на 3 дня.\n4. Обработайте одобрение, отклонение менеджером или автоотклонение по таймауту.\n5. Зафиксируйте финальный статус заявки.",
        "code_blocks": [
            {
                "filename": "human_in_the_loop.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/workflow"
)

type LoanApplication struct {
	ApplicationID string
	ApplicantName string
	Amount        float64
}

type ApprovalDecision struct {
	Approved bool   `json:"approved"`
	Manager  string `json:"manager"`
	Reason   string `json:"reason"`
}

func AutomatedScoringActivity(ctx context.Context, app LoanApplication) (int, error) {
	fmt.Printf(" [ACTIVITY] Скоринг заявки %s: кредитный рейтинг 780/1000\n", app.ApplicationID)
	return 780, nil
}

func DisburseLoanActivity(ctx context.Context, app LoanApplication) error {
	fmt.Printf(" [ACTIVITY] 💰 Выплата кредита %.2f руб клиенту %s произведена!\n", app.Amount, app.ApplicantName)
	return nil
}

// LoanApprovalWorkflow реализует паттерн Human-in-the-Loop.
func LoanApprovalWorkflow(ctx workflow.Context, app LoanApplication) (string, error) {
	logger := workflow.GetLogger(ctx)
	ao := workflow.ActivityOptions{StartToCloseTimeout: 10 * time.Second}
	ctx = workflow.WithActivityOptions(ctx, ao)

	// Шаг 1: Автоматический скоринг
	var score int
	if err := workflow.ExecuteActivity(ctx, AutomatedScoringActivity, app).Get(ctx, &score); err != nil {
		return "", err
	}

	// Если сумма до 1 000 000 руб — одобряем автоматически
	if app.Amount <= 1_000_000 {
		logger.Info("Сумма в пределах лимита автоодобрения")
		_ = workflow.ExecuteActivity(ctx, DisburseLoanActivity, app).Get(ctx, nil)
		return "APPROVED_AUTOMATICALLY", nil
	}

	// Шаг 2: Human-in-the-Loop: сумма > 1 млн, требуется одобрение менеджера!
	logger.Info("Крупный кредит! Переход в режим ожидания согласования менеджером (до 3 дней)...")

	approvalChan := workflow.GetSignalChannel(ctx, "ManagerApprovalSignal")
	var decision ApprovalDecision
	signalReceived := false

	selector := workflow.NewSelector(ctx)

	// Ветка согласования менеджером
	selector.AddReceive(approvalChan, func(c workflow.ReceiveChannel, more bool) {
		c.Receive(ctx, &decision)
		signalReceived = true
	})

	// Ветка таймаута: 3 дня на решение
	approvalTimeout := workflow.NewTimer(ctx, 3*24*time.Hour)
	selector.AddFuture(approvalTimeout, func(f workflow.Future) {
		logger.Warn("Истекли 3 дня ожидания согласования!")
	})

	selector.Select(ctx)

	if !signalReceived {
		return "REJECTED_TIMEOUT: Менеджер не ответил за 3 дня", nil
	}

	if !decision.Approved {
		logger.Info("Заявка отклонена менеджером", "manager", decision.Manager, "reason", decision.Reason)
		return fmt.Sprintf("REJECTED_BY_MANAGER: %s (%s)", decision.Manager, decision.Reason), nil
	}

	logger.Info("Заявка согласована менеджером! Выплата...", "manager", decision.Manager)
	_ = workflow.ExecuteActivity(ctx, DisburseLoanActivity, app).Get(ctx, nil)

	return fmt.Sprintf("APPROVED_BY_MANAGER: %s", decision.Manager), nil
}

func main() {
	fmt.Println("Демонстрация паттерна Human-in-the-Loop в Temporal.")
}
"""
            }
        ],
        "under_the_hood": "Во время трехдневного ожидания под с воркером может перезагружаться сотни раз в процессе деплоев. Экземпляр процесса мирно спит в базе данных кластера. Когда менеджер в админ-панели нажимает кнопку 'Одобрить', бэкенд шлет сигнал через `client.SignalWorkflow`. Кластер будит любой доступный воркер, передает сигнал, и воркер выполняет оставшуюся ветку кода.",
        "pitfalls": "Обязательно используйте таймаут при ожидании человеческого решения. Люди склонны уходить в отпуск, болеть или забывать про задачи. Без детерминированного таймера Workflow зависнет в ожидании сигнала навсегда.",
        "interview_qa": "В: Как уведомить менеджера о том, что заявка ждет его решения?\nО: Перед входом в ожидание сигнала вызовите Activity `SendManagerSlackNotificationActivity`, которая отправляет в корпоративный мессенджер сообщение с кнопками 'Одобрить'/'Отклонить' и ссылкой на админку. При клике бэкенд админки вызывает `client.SignalWorkflow`."
    },
    {
        "num": 17,
        "title": "Дочерние рабочие процессы (Child Workflows)",
        "task": "Разбейте сложный монолитный Workflow на композируемые дочерние процессы с помощью `workflow.ExecuteChildWorkflow(ctx, SubWorkflow, args)`. Настройте политику завершения родителя `ParentClosePolicy` (должен ли дочерний процесс прерываться при отмене родителя) и получите типизированный результат работы дочернего процесса.",
        "theory": "Child Workflows (Дочерние процессы) позволяют масштабировать и декомпозировать сложные распределенные системы:\n\n1. **Модульность и переиспользование**: сложный подпроцесс (например, скоринг или генерация документов) оформляется как отдельный Workflow и вызывается из разных родительских процессов.\n2. **Управление размером истории (History Size Limit)**: если родительский процесс обрабатывает миллион элементов, выполнение всех шагов в одном процессе раздует историю до гигабайтов. Запуск независимых Child Workflows создает отдельный чистый журнал событий для каждого дочернего процесса.\n3. **Политики ParentClosePolicy**:\n   - `PARENT_CLOSE_POLICY_TERMINATE`: при завершении/отмене родителя дочерний процесс мгновенно завершается.\n   - `PARENT_CLOSE_POLICY_ABANDON`: дочерний процесс продолжает выполняться автономно, даже если родитель умер.\n   - `PARENT_CLOSE_POLICY_REQUEST_CANCEL`: родителем отправляется запрос на graceful отмену дочернего процесса.",
        "step_by_step": "1. Напишите сигнатуру дочернего процесса `ProcessItemChildWorkflow`.\n2. Настройте `workflow.ChildWorkflowOptions` с `ParentClosePolicy`.\n3. В родительском процессе запустите несколько дочерних процессов.\n4. Дождитесь их выполнения и сагрегируйте результаты.",
        "code_blocks": [
            {
                "filename": "child_workflow.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"time"

	"go.temporal.io/api/enums/v1"
	"go.temporal.io/sdk/workflow"
)

// ProcessItemChildWorkflow — независимый дочерний процесс с собственной историей.
func ProcessItemChildWorkflow(ctx workflow.Context, itemID string) (string, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Старт дочернего процесса", "item_id", itemID)

	// Имитация шага обработки внутри дочернего процесса
	_ = workflow.Sleep(ctx, 1*time.Second)

	return fmt.Sprintf("PROCESSED_%s", itemID), nil
}

// ParentBatchWorkflow оркестрирует запуск дочерних процессов.
func ParentBatchWorkflow(ctx workflow.Context, itemIDs []string) ([]string, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Старт родительского процесса", "total_items", len(itemIDs))

	var childFutures []workflow.ChildWorkflowFuture

	for _, id := range itemIDs {
		cwo := workflow.ChildWorkflowOptions{
			WorkflowID:        fmt.Sprintf("child-item-%s", id),
			ParentClosePolicy: enums.PARENT_CLOSE_POLICY_TERMINATE, // При падении родителя убить дочерний
			WorkflowExecutionTimeout: 10 * time.Minute,
		}
		childCtx := workflow.WithChildOptions(ctx, cwo)

		// Асинхронный запуск дочернего процесса
		future := workflow.ExecuteChildWorkflow(childCtx, ProcessItemChildWorkflow, id)
		childFutures = append(childFutures, future)
	}

	results := make([]string, 0, len(childFutures))
	for _, f := range childFutures {
		var res string
		if err := f.Get(ctx, &res); err != nil {
			logger.Error("Ошибка в дочернем процессе", "error", err)
			return nil, err
		}
		results = append(results, res)
	}

	logger.Info("Все дочерние процессы успешно завершены!")
	return results, nil
}

func main() {
	fmt.Println("Демонстрация Child Workflows и ParentClosePolicy в Temporal.")
}
"""
            }
        ],
        "under_the_hood": "При вызове `ExecuteChildWorkflow` родительский процесс отправляет в кластер команду `StartChildWorkflowExecution`. Кластер создает полностью самостоятельный экземпляр Workflow с новым уникальным `RunID` и собственной изолированной цепочкой событий в таблице истории. Связь 'родитель-дитя' отслеживается кластером через системные атрибуты.",
        "pitfalls": "Не используйте Child Workflow там, где достаточно обычной Activity. Запуск Child Workflow требует значительно больше системных накладных расходов (создание отдельного контекста, несколько событий старта/завершения в двух журналах). Child Workflow оправдан только тогда, когда вам нужна многошаговая логика, собственные сигналы или изоляция истории.",
        "interview_qa": "В: Как получить WorkflowID запущенного Child Workflow до того, как он завершился?\nО: Объект `workflow.ChildWorkflowFuture` предоставляет метод `GetChildWorkflowExecutionPromise()`. Разрешение этого промиса происходит сразу после подтверждения старта кластером и возвращает структуру `WorkflowExecution` с полями `ID` и `RunID`."
    },
    {
        "num": 18,
        "title": "Реализация распределенной Саги на Temporal",
        "task": "Реализуйте паттерн распределенной транзакции (Saga Pattern) для бронирования путешествия: последовательно бронируются рейс, отель и авто. Напишите стек компенсаций (срез замыканий `compensations = append(compensations, cancelFlightActivity)`). При возникновении ошибки на любом этапе Workflow в обратном порядке выполняет все накопленные компенсации, гарантируя строгую консистентность.",
        "theory": "Паттерн Saga — стандарт де-факто для обеспечения согласованности данных в микросервисной архитектуре без тяжелых двухфазных коммитов (2PC).\n\nВ традиционной разработке Саги реализуются крайне тяжело: координатор должен слушать очереди, сохранять состояние шагов в БД и обрабатывать частичные отказы компенсаций. В Temporal написание распределенной Саги становится тривиальным и элегантным:\n1. Мы создаем слайс функций-компенсаций `var compensations []func(ctx workflow.Context)`.\n2. При успешном выполнении каждого прямого действия мы добавляем компенсирующее действие в начало или конец стека компенсаций.\n3. В блоке обработки ошибок (или в `defer`) мы итерируемся по стеку компенсаций в обратном порядке (LIFO) и вызываем компенсирующие Activities.\n4. Для гарантированного выполнения компенсаций даже при отмене процесса используется `workflow.NewDisconnectedContext(ctx)`.",
        "step_by_step": "1. Реализуйте прямые активности: `BookFlight`, `BookHotel`, `BookCar`.\n2. Реализуйте компенсирующие активности: `CancelFlight`, `CancelHotel`.\n3. Спроектируйте стек компенсаций внутри Workflow.\n4. Смоделируйте сбой на шаге 3 (бронирование авто) и покажите автоматический откат броней отеля и рейса.",
        "code_blocks": [
            {
                "filename": "saga.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"time"

	"go.temporal.io/sdk/workflow"
)

// Прямые действия
func BookFlightAct(ctx context.Context, id string) error {
	fmt.Printf(" [ACTIVITY] ✅ Рейс %s забронирован.\n", id)
	return nil
}

func BookHotelAct(ctx context.Context, id string) error {
	fmt.Printf(" [ACTIVITY] ✅ Отель %s забронирован.\n", id)
	return nil
}

func BookCarAct(ctx context.Context, id string) error {
	fmt.Printf(" [ACTIVITY] ❌ Сбой аренды авто %s: нет доступных машин!\n", id)
	return errors.New("CAR_UNAVAILABLE")
}

// Компенсирующие действия
func CancelFlightAct(ctx context.Context, id string) error {
	fmt.Printf(" [COMPENSATION] 🔄 Отмена брони рейса %s...\n", id)
	return nil
}

func CancelHotelAct(ctx context.Context, id string) error {
	fmt.Printf(" [COMPENSATION] 🔄 Отмена брони отеля %s...\n", id)
	return nil
}

// TravelSagaWorkflow реализует паттерн Saga с гарантированным откатом.
func TravelSagaWorkflow(ctx workflow.Context) (err error) {
	logger := workflow.GetLogger(ctx)
	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 5 * time.Second,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	// Стек компенсаций
	var compensations []func(ctx workflow.Context)

	// Гарантированный запуск компенсаций при выходе с ошибкой
	defer func() {
		if err != nil {
			logger.Warn("Транзакция провалилась! Запуск компенсаций Саги в обратном порядке...")
			// Отсоединенный контекст гарантирует выполнение компенсаций даже при отмене Workflow!
			disconnectedCtx, _ := workflow.NewDisconnectedContext(ctx)
			for i := len(compensations) - 1; i >= 0; i-- {
				compensations[i](disconnectedCtx)
			}
		}
	}()

	// Шаг 1: Рейс
	if err = workflow.ExecuteActivity(ctx, BookFlightAct, "FL-771").Get(ctx, nil); err != nil {
		return err
	}
	compensations = append(compensations, func(c workflow.Context) {
		_ = workflow.ExecuteActivity(c, CancelFlightAct, "FL-771").Get(c, nil)
	})

	// Шаг 2: Отель
	if err = workflow.ExecuteActivity(ctx, BookHotelAct, "HT-404").Get(ctx, nil); err != nil {
		return err
	}
	compensations = append(compensations, func(c workflow.Context) {
		_ = workflow.ExecuteActivity(c, CancelHotelAct, "HT-404").Get(c, nil)
	})

	// Шаг 3: Автомобиль (намеренно упадет!)
	if err = workflow.ExecuteActivity(ctx, BookCarAct, "CR-990").Get(ctx, nil); err != nil {
		return err
	}

	return nil
}

func main() {
	fmt.Println("Демонстрация распределенной Саги на Temporal с NewDisconnectedContext.")
}
"""
            }
        ],
        "under_the_hood": "В отличие от традиционных брокеров, где компенсационное сообщение может потеряться при сбое сети, в Temporal компенсирующие активности защищены общей гарантией Durable Execution. Если во время выполнения `CancelHotelAct` упадет сервер, кластер продолжит ретраить компенсацию до тех пор, пока внешний сервис не подтвердит успешный откат. Это гарантирует абсолютную eventual consistency.",
        "pitfalls": "Главная ошибка новичков в Сагах — выполнение компенсаций в стандартном `ctx`. Если Workflow был прерван внешней отменой (`client.CancelWorkflow`), стандартный `ctx` уже находится в состоянии `Canceled`, и все вызовы `ExecuteActivity(ctx, Compensation)` мгновенно упадут с ошибкой `Canceled`! Всегда используйте `workflow.NewDisconnectedContext(ctx)` для компенсирующих активностей.",
        "interview_qa": "В: Что делать, если сама компенсирующая Activity возвращает ошибку (например, банк недоступен)?\nО: Компенсирующая Activity должна быть снабжена надежной `RetryPolicy` (возможно, с бесконечными попытками). Если внешний сервис лежит, воркер будет продолжать попытки компенсации до его оживления. В крайних случаях при критических бизнес-ошибках отправляется алерт в PagerDuty / Sentry для ручного вмешательства дежурного инженера."
    },
    {
        "num": 19,
        "title": "Версионирование рабочих процессов (Workflow Versioning)",
        "task": "Вы обновили бизнес-логику в коде (добавили новый обязательный шаг проверки или заменили старую Activity на новую). Старые запущенные экземпляры процессов при выкатке упадут с фатальной ошибкой недетерминированности (`DeterminismError`)! Примените метод `workflow.GetVersion(ctx, 'changeID', workflow.DefaultVersion, 1)` для безопасного разделения веток исполнения старого и нового кода.",
        "theory": "Долгоживущие процессы в Temporal могут работать дни, месяцы и годы. За это время команда разработчиков успеет выпустить десятки релизов, поменять бизнес-логику, добавить новые Activities или изменить порядок их вызова.\n\nЕсли вы просто измените код Workflow: старый процесс проснется через месяц, попытается выполнить Replay по старой истории, наткнется на новую Activity в коде и упадет с паникой недетерминированности!\n\nДля решения этой проблемы Temporal SDK предоставляет механизм **Patching / Versioning**:\n- Функция `workflow.GetVersion(ctx, changeID, minSupportedVersion, maxSupportedVersion)`.\n- При первом исполнении (Live Execution) нового процесса функция возвращает максимальную версию (например, 1) и записывает маркер версии в историю событий.\n- При Replay старых процессов, в чьей истории маркера нет, функция возвращает `workflow.DefaultVersion` (-1), и код направляется по старой ветке!",
        "step_by_step": "1. Изучите сигнатуру `workflow.GetVersion`.\n2. Реализуйте Workflow, поддерживающий две версии бизнес-логики: v0 (DefaultVersion) и v1 (новая версия с дополнительной валидацией).\n3. Покажите разделение ветвления через `if version == workflow.DefaultVersion`.\n4. Объясните жизненный цикл удаления старых версий кода.",
        "code_blocks": [
            {
                "filename": "versioning.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/workflow"
)

func LegacyStepActivity(ctx context.Context) error {
	fmt.Println(" [ACTIVITY] Исполнение старой логики v0...")
	return nil
}

func ModernStepActivity(ctx context.Context) error {
	fmt.Println(" [ACTIVITY] 🚀 Исполнение новой оптимизированной логики v1...")
	return nil
}

// VersionedOrderWorkflow безопасно поддерживает старые и новые процессы.
func VersionedOrderWorkflow(ctx workflow.Context) error {
	logger := workflow.GetLogger(ctx)
	ao := workflow.ActivityOptions{StartToCloseTimeout: 5 * time.Second}
	ctx = workflow.WithActivityOptions(ctx, ao)

	// Получение версии для изменения "migrate-to-modern-step"
	// workflow.DefaultVersion (-1) — для старых историй, где этой отметки еще не было
	// Версия 1 — для всех новых запусков
	version := workflow.GetVersion(ctx, "migrate-to-modern-step", workflow.DefaultVersion, 1)

	if version == workflow.DefaultVersion {
		// Ветка для старых процессов, которые уже находились в полете до деплоя
		logger.Info("Исполнение по старой ветке v0 (DefaultVersion)")
		if err := workflow.ExecuteActivity(ctx, LegacyStepActivity).Get(ctx, nil); err != nil {
			return err
		}
	} else {
		// Ветка для всех новых процессов после выкатки v1
		logger.Info("Исполнение по новой ветке v1")
		if err := workflow.ExecuteActivity(ctx, ModernStepActivity).Get(ctx, nil); err != nil {
			return err
		}
	}

	return nil
}

func main() {
	fmt.Println("Демонстрация версионирования через workflow.GetVersion.")
}
"""
            }
        ],
        "under_the_hood": "Когда `workflow.GetVersion` вызывается впервые, SDK записывает в кластер событие `MarkerRecorded` с именем изменения и номером версии. При последующих Replay SDK видит этот маркер в истории и мгновенно возвращает зафиксированную версию без риска расхождения кода.",
        "pitfalls": "Категорически запрещено удалять вызовы `workflow.GetVersion` из кода сразу после деплоя! Вызов `GetVersion` обязан оставаться в кодовой базе до тех пор, пока в кластере не завершится самый последний старый процесс, запущенный до изменения.",
        "interview_qa": "В: Когда можно безопасно удалить старую ветку `workflow.GetVersion` из кода Go?\nО: Только тогда, когда в кластере больше нет ни одного активного процесса старой версии. Это можно проверить запросом в Temporal Web UI или через CLI `temporal workflow list --query 'WorkflowType=\"Order\" AND ExecutionStatus=\"Running\"'`. После этого старая ветка удаляется, а `workflow.GetVersion` заменяется на `workflow.GetVersion(ctx, id, 1, 1)` или удаляется целиком."
    },
    {
        "num": 20,
        "title": "Тестирование на недетерминированность (Replay Testing)",
        "task": "Перед деплоем новой версии Workflow в прод необходимо убедиться, что новый код совместим со всей историей завершенных и текущих процессов. Напишите тест с использованием `worker.WorkflowReplayer`: выгрузите JSON-историю событий реального продакшен-процесса и прогоните ее через новый код. Убедитесь в отсутствии ошибок `DeterminismError`.",
        "theory": "Самый страшный баг в Temporal — случайное внесение недетерминированного изменения в Workflow, который находится в проде с тысячами активных инстансов. Если разработчик случайно поменял порядок вызова активностей или убрал таймер, при следующем событии воркер упадет с ошибкой детерминизма.\n\nДля предотвращения таких катастроф в CI/CD пайплайн встраивают **Replay Testing**:\n1. Из продакшен-кластера Temporal выгружаются реальные JSON-истории выполненных процессов: `temporal workflow show --workflow-id <id> --output json > history.json`.\n2. В Go-тесте инициализируется `worker.NewWorkflowReplayer()`.\n3. Функция `replayer.ReplayWorkflowHistoryFromJSONFile(nil, 'history.json')` прогоняет сохраненные события через текущую версию кода Workflow.\n4. Если код попытается сгенерировать команду, которой нет в истории — тест упадет с понятным diff-описанием ошибки.",
        "step_by_step": "1. Спроектируйте структуру Replay теста на Go с использованием `go.temporal.io/sdk/worker`.\n2. Зарегистрируйте тестируемую функцию Workflow в `replayer`.\n3. Выполните прогон тестовой истории событий.\n4. Продемонстрируйте проверку совместимости в юнит-тесте.",
        "code_blocks": [
            {
                "filename": "replay_test.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"testing"

	"go.temporal.io/sdk/worker"
	"go.temporal.io/sdk/workflow"
)

func SampleWorkflow(ctx workflow.Context) error {
	// Допустим, здесь находится логика процесса
	return nil
}

// TestWorkflowHistoryReplay иллюстрирует проверку совместимости истории в CI/CD.
func TestWorkflowHistoryReplay(t *testing.T) {
	replayer := worker.NewWorkflowReplayer()

	// Регистрируем Workflow, который мы проверяем
	replayer.RegisterWorkflow(SampleWorkflow)

	// В реальном CI файлик history.json экспортируется из прода
	historyFilePath := "history.json"

	// Запуск Replay проверки
	err := replayer.ReplayWorkflowHistoryFromJSONFile(nil, historyFilePath)
	if err != nil {
		t.Fatalf("🚨 КРИТИЧЕСКАЯ ОШИБКА ДЕТЕРМИНИЗМА: новый код не совместим со старой историей! %v", err)
	}

	fmt.Println("✅ Replay Test успешно пройден: 100% обратная совместимость кода доказана!")
}

func main() {
	fmt.Println("Шаблон Replay-тестирования для предотвращения аварий недетерминизма в CI/CD.")
}
"""
            }
        ],
        "under_the_hood": "Под капотом `WorkflowReplayer` создает изолированный рантайм без подключения к сети или реальному кластеру. Он парсит события из JSON, имитирует входящие сообщения от сервера и сверяет команды, которые отдает Go-функция, с командами, записанными в истории. При любом расхождении немедленно возвращается `NonDeterministicWorkflowPolicyError`.",
        "pitfalls": "Часто забывают тестировать не только успешно завершенные истории, но и истории отмененных процессов или процессов с ошибками. Всегда сохраняйте в тестовый набор несколько историй с разными ветками исполнения.",
        "interview_qa": "В: Как автоматически проверять обратную совместимость сотен тысяч различных процессов в компании перед релизом?\nО: В крупных компаниях настраивают ночной CI-джоб: скрипт делает выборку 100 случайных историй каждого типа Workflow из продакшена за последнюю неделю и прогоняет их через `WorkflowReplayer`. Если хотя бы одна история падает — релизный пайплайн блокируется."
    },
    {
        "num": 21,
        "title": "Политики повторного использования Workflow ID",
        "task": "Сконфигурируйте `WorkflowIdReusePolicy`: `ALLOW_DUPLICATE`, `ALLOW_DUPLICATE_FAILED_ONLY`, `REJECT_DUPLICATE`. Продемонстрируйте, как использование осмысленного бизнес-идентификатора заказа (например, `order-uuid-12345`) в качестве `WorkflowID` защищает систему от случайного повторного запуска одного и того же заказа (Deduping) на уровне кластера Temporal.",
        "theory": "В Temporal каждый запущенный процесс идентифицируется парой `(WorkflowID, RunID)`:\n- `WorkflowID` — бизнес-идентификатор, задаваемый клиентом (например, `order-7721` или `user-reg-ivan`).\n- `RunID` — уникальный системный UUID конкретного запуска.\n\nВ один момент времени в кластере может существовать ТОЛЬКО ОДИН активный (Running) процесс с данным `WorkflowID`! Попытка запустить второй процесс с тем же ID вернет ошибку `WorkflowExecutionAlreadyStarted`.\n\nЧто происходит, когда предыдущий процесс с этим ID уже завершился? Это определяется политикой **`WorkflowIdReusePolicy`**:\n1. `WORKFLOW_ID_REUSE_POLICY_ALLOW_DUPLICATE`: разрешить повторный запуск всегда.\n2. `WORKFLOW_ID_REUSE_POLICY_ALLOW_DUPLICATE_FAILED_ONLY`: разрешить повторный запуск только если предыдущий процесс упал, был отменен или завершился по таймауту.\n3. `WORKFLOW_ID_REUSE_POLICY_REJECT_DUPLICATE`: никогда повторно не запускать с таким ID.",
        "step_by_step": "1. Сконфигурируйте `client.StartWorkflowOptions` с осмысленным `WorkflowID`.\n2. Установите политику `WorkflowIdReusePolicy: enums.WORKFLOW_ID_REUSE_POLICY_ALLOW_DUPLICATE_FAILED_ONLY`.\n3. Продемонстрируйте вызов `client.ExecuteWorkflow`.\n4. Покажите перехват ошибки дублирующего запуска.",
        "code_blocks": [
            {
                "filename": "id_reuse.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"log"

	"go.temporal.io/api/enums/v1"
	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/workflow"
)

func DummyOrderWorkflow(ctx workflow.Context, orderID string) (string, error) {
	return "ORDER_PROCESSED: " + orderID, nil
}

// StartDeduplicatedOrder запускает заказ с защитой от дублей.
func StartDeduplicatedOrder(c client.Client, orderID string) error {
	workflowOptions := client.StartWorkflowOptions{
		ID:        fmt.Sprintf("order-%s", orderID), // Бизнес-идентификатор
		TaskQueue: "order-tasks",
		// Если предыдущий заказ с таким ID был успешно выполнен — повторный запуск ЗАПРЕЩЕН!
		// Если же он упал — повторный запуск РАЗРЕШЕН.
		WorkflowIDReusePolicy: enums.WORKFLOW_ID_REUSE_POLICY_ALLOW_DUPLICATE_FAILED_ONLY,
	}

	we, err := c.ExecuteWorkflow(context.Background(), workflowOptions, DummyOrderWorkflow, orderID)
	if err != nil {
		return fmt.Errorf("ошибка запуска Workflow: %w", err)
	}

	fmt.Printf(" [SUCCESS] Workflow запущен! WorkflowID: %s, RunID: %s\n", we.GetID(), we.GetRunID())
	return nil
}

func main() {
	fmt.Println("Демонстрация политик WorkflowIdReusePolicy для идеальной дедупликации.")
}
"""
            }
        ],
        "under_the_hood": "Кластер Temporal гарантирует уникальность `WorkflowID` на уровне распределенных транзакций в СУБД (ACID). Таблица `executions` имеет составной первичный ключ по `shard_id` и `workflow_id`. Это означает, что дедупликация работает со 100% гарантией даже при одновременной атаке миллионом параллельных одинаковых HTTP-запросов.",
        "pitfalls": "Генерация случайного `uuid.New().String()` в качестве `WorkflowID` лишает вас важнейшего встроенного механизма дедупликации Temporal! Всегда привязывайте `WorkflowID` к реальным бизнес-ключам сущности (ID заказа, ID транзакции, ID пользователя).",
        "interview_qa": "В: Как реализовать паттерн 'Один активный биллинг-процесс на организацию'?\nО: Установите `WorkflowID = 'billing-org-' + orgID`. Ни при каких условиях два воркера не смогут запустить параллельный биллинг для одной организации, так как кластер гарантирует взаимное исключение по `WorkflowID`."
    },
    {
        "num": 22,
        "title": "Динамические очереди задач (Task Routing per Worker Pool)",
        "task": "Некоторые задачи требуют специальных аппаратных ресурсов (наличие GPU, высокий объем RAM, доступ к изолированной закрытой банковской сети). Покажите, как маршрутизировать конкретные Activities на специализированные пулы воркеров, динамически передавая кастомное имя `TaskQueue` в `workflow.ActivityOptions`.",
        "theory": "По умолчанию все Activities запускаются на той же очереди задач (`TaskQueue`), на которой запущен Workflow. Однако в enterprise-системах разные шаги процесса требуют кардинально разного окружения:\n- Тяжелое машинное обучение / OCR требует серверов с Nvidia GPU (`gpu-task-queue`).\n- Платежные операции требуют запуска внутри изолированного защищенного PCI-DSS периметра (`banking-pci-queue`).\n- Массовая отправка email может выполняться на дешевых спотовых инстансах (`spot-email-queue`).\n\nTemporal позволяет легко маршрутизировать вызовы: достаточно в `workflow.ActivityOptions` указать поле `TaskQueue: 'gpu-task-queue'`. Кластер направит задачу именно в этот пул воркеров.",
        "step_by_step": "1. Опишите активность транскодирования видео на GPU.\n2. Опишите активность отправки пуш-уведомлений.\n3. В едином Workflow настройте вызов первой активности на очереди `gpu-worker-pool`, а второй — на очереди `notifications-pool`.\n4. Продемонстрируйте прозрачную оркестрацию разнородных узлов.",
        "code_blocks": [
            {
                "filename": "routing.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/workflow"
)

func GPURenderActivity(ctx context.Context, modelPath string) (string, error) {
	fmt.Printf(" [GPU WORKER] Рендеринг 3D сцены на видеокарте Nvidia H100: %s\n", modelPath)
	return "rendered_scene.mp4", nil
}

func SendPushActivity(ctx context.Context, userID, message string) error {
	fmt.Printf(" [STANDARD WORKER] Отправка пуша пользователю %s: %s\n", userID, message)
	return nil
}

// HeterogeneousPipelineWorkflow оркестрирует задачи по разным пулам серверов.
func HeterogeneousPipelineWorkflow(ctx workflow.Context, userID, model string) error {
	logger := workflow.GetLogger(ctx)

	// Шаг 1: Направляем тяжелую активность в изолированный пул GPU-воркеров
	gpuOptions := workflow.ActivityOptions{
		TaskQueue:           "gpu-worker-pool", // Маршрутизация на специальную очередь!
		StartToCloseTimeout: 30 * time.Minute,
	}
	ctxGPU := workflow.WithActivityOptions(ctx, gpuOptions)

	var videoFile string
	logger.Info("Отправка задачи в GPU-кластер...")
	if err := workflow.ExecuteActivity(ctxGPU, GPURenderActivity, model).Get(ctxGPU, &videoFile); err != nil {
		return err
	}

	// Шаг 2: Обычное уведомление отправляем на стандартные легковесные воркеры
	standardOptions := workflow.ActivityOptions{
		TaskQueue:           "notifications-pool",
		StartToCloseTimeout: 10 * time.Second,
	}
	ctxStd := workflow.WithActivityOptions(ctx, standardOptions)

	logger.Info("Отправка уведомления через стандартный пул...")
	return workflow.ExecuteActivity(ctxStd, SendPushActivity, userID, "Ваше видео готово: "+videoFile).Get(ctxStd, nil)
}

func main() {
	fmt.Println("Демонстрация динамической маршрутизации задач по очередям (Task Queue Routing).")
}
"""
            }
        ],
        "under_the_hood": "Matching Service в Temporal поддерживает неограниченное количество независимых очередей задач. Когда Workflow указывает кастомную `TaskQueue`, задача помещается в отдельный раздел Matching Service. Сервер сопоставляет задачу только с теми воркерами, которые при вызове `worker.New` подписались именно на эту очередь.",
        "pitfalls": "Если в `TaskQueue` опечататься в строковом имени (например, `gpu-wokrer-pool`), активность зависнет в очереди навсегда, ожидая воркера, которого не существует в природе! Для предотвращения таких багов выносите имена очередей задач в строгие строковые константы общего пакета.",
        "interview_qa": "В: Можно ли запустить Workflow в одной очереди, а его Activities — в трех других очередях?\nО: Да! Это абсолютно естественный паттерн архитектуры Temporal. Более того, воркеры разных очередей могут быть написаны на разных языках программирования (например, Workflow на Go, Activity 1 на Python с PyTorch, а Activity 2 на Java/C#)."
    },
    {
        "num": 23,
        "title": "Паттерн Continue-As-New для бесконечных процессов",
        "task": "Если процесс работает непрерывно годами (мониторинг IoT-устройства, цикл подписки), история событий Temporal Cluster превысит рекомендуемый лимит в 10 000 событий. Реализуйте метод `workflow.NewContinueAsNewError(ctx, ProcessDeviceWorkflow, updatedState)`: текущая история архивируется, а процесс атомарно перезапускается с чистого листа с обновленным состоянием.",
        "theory": "В Temporal история событий сохраняется персистентно в БД. Если Workflow работает непрерывно (например, в бесконечном цикле `for` раз в минуту опрашивает сенсор), через пару месяцев в истории накопится 50 000 событий.\n\nПроблемы гигантской истории:\n1. Замедление Replay (воркеру нужно проиграть все 50 000 событий для восстановления состояния).\n2. Нагрузка на базу данных кластера при чтении блобов истории.\n3. Кластер начнет выдавать предупреждения при 10 000 событий и принудительно заблокирует процесс при 50 000 событий.\n\nРешение — **`workflow.NewContinueAsNewError`**:\nWorkflow выполняет N итераций (например, 500 итераций), после чего возвращает специальную ошибку `workflow.NewContinueAsNewError(ctx, WorkflowFunc, newState)`. Текущая история закрывается со статусом `ContinuedAsNew`, и немедленно создается новый инстанс процесса с тем же `WorkflowID`, но с новым чистым журналом истории событий!",
        "step_by_step": "1. Спроектируйте долгоживущий Workflow `DeviceDaemonWorkflow`.\n2. В цикле отслеживайте количество выполненных итераций.\n3. При достижении порога (например, 1000 итераций) сформируйте аккумулированное состояние.\n4. Завершите процесс через `return workflow.NewContinueAsNewError`.",
        "code_blocks": [
            {
                "filename": "continue_as_new.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/workflow"
)

type DeviceState struct {
	DeviceID       string `json:"device_id"`
	IterationCount int    `json:"iteration_count"`
	TotalAlerts    int    `json:"total_alerts"`
}

func PollDeviceTelemetryActivity(ctx context.Context, deviceID string) (bool, error) {
	// Возвращает true, если датчик зафиксировал перегрев
	return false, nil
}

// DeviceDaemonWorkflow работает бесконечно, периодически очищая историю через Continue-As-New.
func DeviceDaemonWorkflow(ctx workflow.Context, state DeviceState) error {
	logger := workflow.GetLogger(ctx)
	ao := workflow.ActivityOptions{StartToCloseTimeout: 5 * time.Second}
	ctx = workflow.WithActivityOptions(ctx, ao)

	const maxIterationsBeforeReset = 500

	for i := 0; i < 100; i++ {
		state.IterationCount++

		// Опрос сенсора
		var hasAlert bool
		_ = workflow.ExecuteActivity(ctx, PollDeviceTelemetryActivity, state.DeviceID).Get(ctx, &hasAlert)
		if hasAlert {
			state.TotalAlerts++
		}

		// Сон 1 минуту
		_ = workflow.Sleep(ctx, 1*time.Minute)

		// Проверяем порог очистки истории
		if state.IterationCount >= maxIterationsBeforeReset {
			logger.Info("Достигнут лимит истории. Перезапуск процесса с чистого листа...",
				"iteration", state.IterationCount, "total_alerts", state.TotalAlerts)

			// Атомарная ротация истории: сброс журнала и старт с новым состоянием
			return workflow.NewContinueAsNewError(ctx, DeviceDaemonWorkflow, state)
		}
	}

	return nil
}

func main() {
	fmt.Println("Демонстрация паттерна Continue-As-New для бесконечных процессов.")
}
"""
            }
        ],
        "under_the_hood": "При возврате ошибки `ContinueAsNewError` History Service кластера фиксирует событие `WorkflowExecutionContinuedAsNew`. Текущий `RunID` финализируется, и атомарно генерируется новый `RunID` с событием `WorkflowExecutionStarted`. В новое событие записываются переданные аргументы `state`. Новая история стартует с 1-го события, а навигация между поколениями процессов связывается ссылками в Temporal Web UI.",
        "pitfalls": "Если в фоновом режиме остались незавершенные `workflow.Go` корутины или незакрытые каналы сигналов, вызов `NewContinueAsNewError` оборвет их выполнение. Перед вызовом Continue-As-New убедитесь, что все асинхронные операции завершены.",
        "interview_qa": "В: Как узнать количество событий в текущей истории Workflow программно прямо из кода Go?\nО: Вызовом `workflow.GetInfo(ctx).GetCurrentHistoryLength()`. Это позволяет настроить динамический порог: перезапускать процесс не по абстрактному счетчику итераций, а строго при достижении, например, 5000 реальных событий в истории кластера."
    },
    {
        "num": 24,
        "title": "Отмена процессов (Workflow Cancellation) и очистка ресурсов",
        "task": "Реализуйте обработку сигнала отмены Workflow (`client.CancelWorkflow`). Внутри рабочего процесса перехватите отмену через канал `ctx.Done()`. Создайте новый отсоединенный контекст `workflow.NewDisconnectedContext(ctx)` для гарантированного выполнения завершающих очищающих Activities (освобождение блокировок, закрытие сокетов, возврат средств).",
        "theory": "Отмена Workflow в Temporal — это кооперативный процесс (Graceful Cancellation):\n- Внешний сервис вызывает `client.CancelWorkflow(ctx, workflowID, runID)`.\n- Кластер записывает событие `WorkflowExecutionCancelRequested`.\n- При следующем шаге воркер переводит `workflow.Context` в отмененное состояние: закрывается канал `ctx.Done()`.\n\nПроблема заключается в том, что если Workflow просто упадет с ошибкой отмены, он не успеет освободить внешние ресурсы (очистить временные таблицы в БД, отменить бронь). Вызов любой обычной Activity в отмененном `ctx` немедленно завершится ошибкой `context canceled`.\n\nДля надежной очистки используется `workflow.NewDisconnectedContext(ctx)`: этот контекст копирует все метаданные и опции, но отвязывается от родительского сигнала отмены, позволяя гарантированно выполнить финализирующие активности.",
        "step_by_step": "1. Спроектируйте процесс `OrderProcessingWorkflow` с длительным этапом ожидания.\n2. Перехватите сигнал отмены через `workflow.Selector` и `ctx.Done()`.\n3. Создайте отсоединенный контекст через `workflow.NewDisconnectedContext(ctx)`.\n4. Вызовите очищающую активность `ReleaseHoldActivity`.\n5. Завершите процесс с ошибкой отмены `workflow.ErrCanceled`.",
        "code_blocks": [
            {
                "filename": "cancellation.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/workflow"
)

func ReleaseHoldActivity(ctx context.Context, orderID string) error {
	fmt.Printf(" [ACTIVITY] 🧹 Очистка ресурсов: снятие холда с товаров заказа %s\n", orderID)
	return nil
}

// CancellableOrderWorkflow демонстрирует профессиональную обработку отмены.
func CancellableOrderWorkflow(ctx workflow.Context, orderID string) (err error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Старт процесса с поддержкой Graceful Cancellation", "order_id", orderID)

	// Гарантированная очистка в defer
	defer func() {
		// Проверяем, был ли процесс отменен
		if ctx.Err() != nil {
			logger.Warn("Процесс был отменен! Выполнение аварийной очистки ресурсов...")

			// КРИТИЧНО: создаем отсоединенный контекст, чтобы активность очистки не упала по отмене!
			cleanCtx, _ := workflow.NewDisconnectedContext(ctx)
			ao := workflow.ActivityOptions{StartToCloseTimeout: 10 * time.Second}
			cleanCtx = workflow.WithActivityOptions(cleanCtx, ao)

			_ = workflow.ExecuteActivity(cleanCtx, ReleaseHoldActivity, orderID).Get(cleanCtx, nil)
		}
	}()

	// Имитация долгого ожидания шага сборки
	logger.Info("Ожидание сборки заказа...")
	err = workflow.Sleep(ctx, 10*time.Minute)
	if err != nil {
		logger.Warn("Сон прерван сигналом отмены", "error", err)
		return err // Возвращаем ошибку отмены
	}

	return nil
}

func main() {
	fmt.Println("Демонстрация обработки отмены Workflow с NewDisconnectedContext.")
}
"""
            }
        ],
        "under_the_hood": "Внутренняя реализация `workflow.NewDisconnectedContext(parentCtx)` создает новую структуру `disconnectedContext`, которая перенаправляет вызовы методов к родительскому контексту, но переопределяет метод `Done()` на собственный пустой канал, который никогда не закрывается родительским сигналом отмены. Это изолирует дерево горутин очистки от общего сигнала аборта.",
        "pitfalls": "Если в блоке очистки с `NewDisconnectedContext` не задать `StartToCloseTimeout` для активностей, зависшая активность очистки заблокирует завершение процесса навсегда. Всегда ограничивайте время очистки жесткими таймаутами.",
        "interview_qa": "В: В чем разница между client.CancelWorkflow и client.TerminateWorkflow?\nО: `CancelWorkflow` отправляет запрос на отмену, который Workflow перехватывает в коде и может выполнить корректную очистку, сагу и логирование. `TerminateWorkflow` — это эквивалент жесткого `kill -9`: кластер мгновенно убивает процесс без уведомления воркера и без возможности выполнить хотя бы одну строчку кода очистки."
    },
    {
        "num": 25,
        "title": "Модульное тестирование Workflow с Time Skipping",
        "task": "Напишите юнит-тесты на Temporal с использованием пакета `go.temporal.io/sdk/testsuite`. Протестируйте 30-дневный таймер: покажите, как тестовое окружение Temporal автоматически перематывает виртуальное время вперед (Time Skipping) без реального ожидания, позволяя выполнить многомесячный процесс за считанные миллисекунды.",
        "theory": "Тестирование распределенных процессов с длительными таймаутами (дни, недели) в традиционных системах — огромная боль. Разработчики либо выносят таймауты в конфиги и уменьшают их до 100 мс, либо используют нестабильные моки.\n\nTemporal решает эту проблему на уровне тестового фреймворка `testsuite.WorkflowTestSuite`:\n- Встроенный механизм **Time Skipping (Перемотка времени)**.\n- Когда код Workflow вызывает `workflow.Sleep(ctx, 30*24*time.Hour)`, тестовое окружение не ждет 30 дней в реальности! Оно мгновенно перематывает виртуальные часы кластера на 30 дней вперед.\n- Все таймеры срабатывают мгновенно, и юнит-тест, покрывающий многомесячный бизнес-процесс, выполняется за 5–10 миллисекунд в обычном `go test ./...`!",
        "step_by_step": "1. Создайте экземпляр `testsuite.WorkflowTestSuite`.\n2. Инициализируйте тестовое окружение `env := s.NewTestWorkflowEnvironment()`.\n3. Зарегистрируйте моки активностей или реальные активности.\n4. Запустите Workflow с 30-дневным таймером.\n5. Убедитесь, что тест прошел успешно за доли секунды через `env.IsWorkflowCompleted()`.",
        "code_blocks": [
            {
                "filename": "workflow_test.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/suite"
	"go.temporal.io/sdk/testsuite"
	"go.temporal.io/sdk/workflow"
)

func SendSubscriptionExpiredEmail(ctx context.Context, userID string) error {
	return nil
}

// SubscriptionWorkflow ждет 30 дней и шлет уведомление об окончании подписки.
func SubscriptionWorkflow(ctx workflow.Context, userID string) (string, error) {
	ao := workflow.ActivityOptions{StartToCloseTimeout: 5 * time.Second}
	ctx = workflow.WithActivityOptions(ctx, ao)

	// Сон на целых 30 дней!
	if err := workflow.Sleep(ctx, 30*24*time.Hour); err != nil {
		return "", err
	}

	if err := workflow.ExecuteActivity(ctx, SendSubscriptionExpiredEmail, userID).Get(ctx, nil); err != nil {
		return "", err
	}

	return "EXPIRED_HANDLED", nil
}

// UnitTestSuite демонстрирует юнит-тестирование с Time Skipping.
type UnitTestSuite struct {
	suite.Suite
	testsuite.WorkflowTestSuite
}

func (s *UnitTestSuite) Test_SubscriptionWorkflow_TimeSkipping() {
	env := s.NewTestWorkflowEnvironment()

	// Мокируем активность
	env.OnActivity(SendSubscriptionExpiredEmail, mock.Anything, "user-991").Return(nil)

	startRealTime := time.Now()

	// Запуск процесса, который внутри спит 30 дней!
	env.ExecuteWorkflow(SubscriptionWorkflow, "user-991")

	duration := time.Since(startRealTime)
	s.True(env.IsWorkflowCompleted())
	s.NoError(env.GetWorkflowError())

	var result string
	s.NoError(env.GetWorkflowResult(&result))
	s.Equal("EXPIRED_HANDLED", result)

	// Доказываем, что 30 дней виртуального времени выполнились быстрее чем за 1 секунду!
	s.Less(duration, 1*time.Second)
	fmt.Printf("✅ Тест 30-дневного процесса выполнен за %v реального времени благодаря Time Skipping!\n", duration)
}

func TestWorkflowSuite(t *testing.T) {
	suite.Run(t, new(UnitTestSuite))
}

func main() {
	fmt.Println("Демонстрация Time Skipping в юнит-тестах Temporal SDK.")
}
"""
            }
        ],
        "under_the_hood": "Класс `TestWorkflowEnvironment` запускает полноценный in-memory эмулятор Temporal Server. Он использует виртуальный генератор тактов. Когда все корутины засыпают на таймерах или активности ждут расписания, тестовый рантайм находит ближайший таймер в очереди и мгновенно перемещает виртуальные часы вперед на нужную дельту времени, незамедлительно пробуждая спящий Workflow.",
        "pitfalls": "Если внутри кода Workflow случайно использовать `time.Sleep()` вместо `workflow.Sleep()`, механизм Time Skipping сломается: тест реально зависнет на 30 дней, а рантайм упадет по таймауту теста. Всегда используйте методы пакета `workflow`.",
        "interview_qa": "В: Как в юнит-тесте отправить сигнал в Workflow в определенный момент виртуального времени (например, ровно на 15-й день)?\nО: Метод `env.RegisterDelayedCallback(func() { env.SignalWorkflow(...) }, 15*24*time.Hour)` позволяет зарегистрировать коллбэк, который тестовое окружение вызовет ровно тогда, когда виртуальные часы отмотают 15 дней!"
    }
]
