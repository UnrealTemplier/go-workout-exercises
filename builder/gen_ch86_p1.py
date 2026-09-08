# -*- coding: utf-8 -*-
"""
Chapter 86 Part 1: Exercises 1 to 15
Scalable Distributed Schedulers and Task Queues in Go
"""

exercises = [
    {
        "num": 1,
        "title": "Архитектура асинхронной обработки фоновых задач",
        "task": "Спроектируйте архитектуру системы фоновых задач на Go. Определите интерфейсы Producer (постановщик задач), Consumer / Worker (обработчик), Broker (очередь хранения) и структуру Task с уникальным ID, типом задачи, полезной нагрузкой (payload) и метаданными. Реализуйте базовый сценарий: клиент синхронно ставит задачу 'send_welcome_email', получает task_id за 1 мс, а воркер асинхронно обрабатывает ее в фоне.",
        "theory": "В современных веб-приложениях синхронное выполнение тяжелых операций (отправка email/SMS, генерация PDF, экспорт отчетов, обработка видео, вызовы сторонних платежных шлюзов) в рамках HTTP-запроса является грубой антипаттерной практикой. Это блокирует HTTP-потоки, приводит к таймаутам клиентов (504 Gateway Timeout) и делает систему уязвимой к отказам внешних API.\n\nАрхитектура асинхронных очередей задач (Task Queue / Job Scheduler) делит систему на три слабосвязанных компонента:\n1. **Producer (Клиент)**: Быстро формирует задачу, записывает ее в персистентную очередь (Broker) и немедленно возвращает пользователю статус '202 Accepted' с уникальным Task ID.\n2. **Broker (Хранилище очередей)**: Надежное промежуточное хранилище (PostgreSQL, Redis, RabbitMQ, Kafka), гарантирующее сохранность задач даже при аварийном перезапуске сервисов.\n3. **Consumer / Worker Pool**: Пул изолированных фоновых процессов, которые вычитывают задачи, выполняют бизнес-логику, управляют повторными попытками при сбоях и фиксируют финальный результат.",
        "step_by_step": "1. Определите структуру `Task` с полями ID, TypeName, Payload, CreatedAt, Status.\n2. Спроектируйте интерфейсы `QueueBroker` и `TaskHandler`.\n3. Реализуйте диспетчер задач `TaskManager` с регистрацией обработчиков по строковому имени типа задачи.\n4. Напишите сценарий в main.go: Producer ставит задачу, воркер извлекает ее и выполняет имитацию отправки письма.\n5. Зафиксируйте субмиллисекундное время отклика Producer.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"sync"
	"time"
)

type TaskStatus string

const (
	StatusPending TaskStatus = "pending"
	StatusRunning TaskStatus = "running"
	StatusSuccess TaskStatus = "success"
	StatusFailed  TaskStatus = "failed"
)

type Task struct {
	ID        string          `json:"id"`
	TypeName  string          `json:"type_name"`
	Payload   json.RawMessage `json:"payload"`
	CreatedAt time.Time       `json:"created_at"`
	Status    TaskStatus      `json:"status"`
}

type TaskHandler func(ctx context.Context, payload []byte) error

type InMemoryBroker struct {
	mu    sync.Mutex
	queue chan *Task
	tasks map[string]*Task
}

func NewInMemoryBroker(capacity int) *InMemoryBroker {
	return &InMemoryBroker{
		queue: make(chan *Task, capacity),
		tasks: make(map[string]*Task),
	}
}

func (b *InMemoryBroker) Enqueue(ctx context.Context, task *Task) error {
	b.mu.Lock()
	task.Status = StatusPending
	task.CreatedAt = time.Now()
	b.tasks[task.ID] = task
	b.mu.Unlock()

	select {
	case b.queue <- task:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func (b *InMemoryBroker) Dequeue(ctx context.Context) (*Task, error) {
	select {
	case task := <-b.queue:
		b.mu.Lock()
		task.Status = StatusRunning
		b.mu.Unlock()
		return task, nil
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}

type WorkerServer struct {
	broker   *InMemoryBroker
	handlers map[string]TaskHandler
	wg       sync.WaitGroup
	quit     chan struct{}
}

func NewWorkerServer(broker *InMemoryBroker) *WorkerServer {
	return &WorkerServer{
		broker:   broker,
		handlers: make(map[string]TaskHandler),
		quit:     make(chan struct{}),
	}
}

func (s *WorkerServer) RegisterHandler(typeName string, h TaskHandler) {
	s.handlers[typeName] = h
}

func (s *WorkerServer) Start(workerCount int) {
	for i := 1; i <= workerCount; i++ {
		s.wg.Add(1)
		go s.workerLoop(i)
	}
}

func (s *WorkerServer) workerLoop(workerID int) {
	defer s.wg.Done()
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	for {
		select {
		case <-s.quit:
			return
		default:
			task, err := s.broker.Dequeue(ctx)
			if err != nil {
				return
			}

			handler, exists := s.handlers[task.TypeName]
			if !exists {
				fmt.Printf("[Worker #%d] Неизвестный тип задачи: %s\n", workerID, task.TypeName)
				continue
			}

			// Выполнение задачи
			err = handler(ctx, task.Payload)
			s.broker.mu.Lock()
			if err != nil {
				task.Status = StatusFailed
				fmt.Printf("[Worker #%d] Ошибка задачи %s: %v\n", workerID, task.ID, err)
			} else {
				task.Status = StatusSuccess
				fmt.Printf("[Worker #%d] Успешно завершена задача %s (%s)\n", workerID, task.ID, task.TypeName)
			}
			s.broker.mu.Unlock()
		}
	}
}

func (s *WorkerServer) Stop() {
	close(s.quit)
	s.wg.Wait()
}

type EmailPayload struct {
	Recipient string `json:"recipient"`
	Subject   string `json:"subject"`
}

func main() {
	broker := NewInMemoryBroker(100)
	server := NewWorkerServer(broker)

	// Регистрируем бизнес-обработчик отправки email
	server.RegisterHandler("email:welcome", func(ctx context.Context, payload []byte) error {
		var p EmailPayload
		if err := json.Unmarshal(payload, &p); err != nil {
			return err
		}
		time.Sleep(50 * time.Millisecond) // Имитация обращения к SMTP-шлюзу
		fmt.Printf("   -> Письмо отправлено на адрес: %s с темой: '%s'\n", p.Recipient, p.Subject)
		return nil
	})

	server.Start(3) // Запускаем 3 параллельных воркера

	// Клиент (HTTP Handler) ставит задачу
	ctx := context.Background()
	payloadBytes, _ := json.Marshal(EmailPayload{
		Recipient: "senior.gopher@bigtech.ru",
		Subject:   "Добро пожаловать в команду платформенных инженеров!",
	})

	start := time.Now()
	taskID := "task_email_9981"
	err := broker.Enqueue(ctx, &Task{
		ID:       taskID,
		TypeName: "email:welcome",
		Payload:  payloadBytes,
	})
	fmt.Printf("Клиент: Задача поставлена за %v (err: %v)\n", time.Since(start), err)

	time.Sleep(100 * time.Millisecond) // Ожидаем завершения обработки воркером

	server.Stop()
	fmt.Println("Пул воркеров остановлен штатно.")
}
"""
            }
        ],
        "under_the_hood": "Постановка задачи через неблокирующий буферизованный канал выполняется за десятки наносекунд: указатель на Task копируется в буфер канала без переключения в пространство ядра ОС. Горутина-воркер, спящая на декьюировании (`Dequeue`), пробуждается рантаймом Go через механизм семафоров и `sudog` очереди канала.",
        "pitfalls": "Отсутствие персистентности в памяти (In-Memory channel): если контейнер с приложением перезапустится в процессе обработки, все задачи в канале будут безвозвратно утеряны. В продакшене брокером должен выступать персистентный демон (PostgreSQL, Redis AOF/RDB, NATS JetStream).",
        "bigtech_interview": "'Чем очередь задач отличается от шины сообщений вроде Apache Kafka?' Ответ: Kafka оптимизирована для потоковой передачи последовательных логов событий (Event Streams) с упорядочиванием по партициям и хранением истории. Очередь задач (Task Queue) оптимизирована для управления дискретными заданиями: индивидуальные статусы исполнения, экспоненциальные повторные попытки (Retry), отложенный запуск (Delayed Tasks), таймауты и отмена конкретного Task ID."
    },
    {
        "num": 2,
        "title": "Потокобезопасная очередь задач в памяти (In-Memory Worker Pool)",
        "task": "Реализуйте масштабируемый воркер-пул в оперативной памяти на Go с поддержкой динамического изменения количества воркеров, очередей с ограничением емкости (Bounded Queue) и защиты от утечек горутин. Напишите метод Dispatch(job func()), который при заполнении очереди не блокирует вызывающий поток навсегда, а возвращает ошибку ErrQueueFull (или применяет политику сброса CallerRunsPolicy).",
        "theory": "Неограниченное порождение горутин вида `go handle(task)` на каждый входящий запрос — главная причина OOM-аварий в Go-сервисах под нагрузкой. Каждая горутина аллоцирует минимум 2 КБ стека (а под нагрузкой расширяется до мегабайт).\n\nПул воркеров (Worker Pool) фиксирует максимальное количество параллельно работающих исполнителей (например, $N = NumCPU \times 2$), защищая процессор от избыточного переключения контекстов (Context Switching Overhead) и базу данных от превышения пула соединений.\n\nПолитики переполнения (Backpressure Policies):\n- **Block**: Вызывающий поток блокируется, пока не освободится слот.\n- **Abort**: Немедленный отказ с `ErrQueueFull` (позволяет клиенту повторить позже).\n- **Caller-Runs**: Вызывающий поток сам выполняет задачу, естественным образом замедляя входящий поток запросов.",
        "step_by_step": "1. Спроектируйте структуру `WorkerPool` с фиксированным размером пула и буферизованным каналом задач `chan func()`.\n2. Реализуйте запуск фиксированного количества горутин-воркеров.\n3. Реализуйте метод `Submit(job func()) error` с неблокирующей проверкой переполнения через `select/default`.\n4. Добавьте метод `Shutdown()` с ожиданием завершения всех начатых задач через `sync.WaitGroup`.\n5. Напишите тест в main.go, демонстрирующий обработку переполнения очереди.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

var ErrPoolFull = errors.New("workerpool: job queue is full")

type Job func()

type BoundedWorkerPool struct {
	workerCount int
	jobQueue    chan Job
	wg          sync.WaitGroup
	closed      atomic.Bool
	jobsDone    int64
	rejected    int64
}

func NewBoundedWorkerPool(workerCount, queueCap int) *BoundedWorkerPool {
	p := &BoundedWorkerPool{
		workerCount: workerCount,
		jobQueue:    make(chan Job, queueCap),
	}

	p.start()
	return p
}

func (p *BoundedWorkerPool) start() {
	for i := 1; i <= p.workerCount; i++ {
		p.wg.Add(1)
		go func(workerID int) {
			defer p.wg.Done()
			for job := range p.jobQueue {
				job()
				atomic.AddInt64(&p.jobsDone, 1)
			}
		}(i)
	}
}

// Submit отправляет задачу в очередь. Если очередь полна, возвращает ErrPoolFull.
func (p *BoundedWorkerPool) Submit(j Job) error {
	if p.closed.Load() {
		return errors.New("workerpool: closed")
	}

	select {
	case p.jobQueue <- j:
		return nil
	default:
		atomic.AddInt64(&p.rejected, 1)
		return ErrPoolFull // Backpressure!
	}
}

func (p *BoundedWorkerPool) Shutdown() {
	if p.closed.CompareAndSwap(false, true) {
		close(p.jobQueue)
		p.wg.Wait()
	}
}

func main() {
	// Создаем пул из 3 воркеров с буфером очереди всего на 5 задач
	pool := NewBoundedWorkerPool(3, 5)

	totalTasks := 15
	var submitted int

	fmt.Printf("Попытка отправки %d задач в пул (3 воркера, очередь на 5 мест)...\n", totalTasks)

	for i := 1; i <= totalTasks; i++ {
		taskID := i
		err := pool.Submit(func() {
			time.Sleep(30 * time.Millisecond) // Имитация полезной работы
		})

		if err != nil {
			fmt.Printf("Задача #%d отклонена: %v (Backpressure сработал!)\n", taskID, err)
		} else {
			submitted++
		}
	}

	fmt.Printf("\nУспешно принято в очередь: %d задач, отклонено: %d\n", submitted, pool.rejected)

	// Штатная остановка с ожиданием завершения
	pool.Shutdown()
	fmt.Printf("Все принятые задачи выполнены: %d (ожидалось %d)\n", pool.jobsDone, submitted)
}
"""
            }
        ],
        "under_the_hood": "Конструкция `select { case ch <- item: default: }` превращается компилятором Go в вызов рантайм-функции `selectnbsend(c, elem)`. Это атомарная неблокирующая попытка записи: если в буфере канала нет свободного места, функция возвращает `false` без парковки текущей горутины в планировщике, экономя такты CPU.",
        "pitfalls": "Закрытие канала задач при работающих отправителях: вызов `close(p.jobQueue)` в момент, когда другие горутины еще вызывают `Submit()`, вызовет фатальную панику `panic: send on closed channel`. Для безопасного завершения используется атомарный флаг `closed.CompareAndSwap` или `sync.RWMutex`.",
        "bigtech_interview": "'Как выбрать оптимальное количество воркеров в пуле?' Ответ: Зависит от характера нагрузки. Для CPU-bound задач (криптография, парсинг, сжатие) оптимум: $N = runtime.NumCPU()$. Для I/O-bound задач (сетевые HTTP-запросы, SQL-запросы к БД, обращение к дискам) оптимум: $N = NumCPU \times \frac{WaitTime + ComputeTime}{ComputeTime}$, что на практике составляет от 20 до 200 воркеров на инстанс."
    },
    {
        "num": 3,
        "title": "Очереди задач на Redis Streams vs Sorted Sets",
        "task": "Сравните две популярные архитектуры построения распределенных очередей задач в Redis: Redis Streams (XADD/XREADGROUP/XACK) и Redis Sorted Sets (ZADD с оценкой по времени/ZRANGEBYSCORE). Напишите Go-код, реализующий: 1) Очередь немедленного исполнения на базе Consumer Groups в Redis Streams с подтверждением обработки (ACK); 2) Очередь отложенных задач на базе ZSet, где score равен UnixNano времени запуска.",
        "theory": "В экосистеме Redis для очередей применяются две фундаментальные структуры данных:\n\n1. **Redis Streams (XADD / XREADGROUP / XACK)**:\n   - Появился в Redis 5.0, аналог легковесной Kafka.\n   - Поддерживает Consumer Groups: несколько воркеров делят задачи без гонок данных.\n   - Pending Entries List (PEL): Redis отслеживает, какие задачи взяты воркерами, но еще не подтверждены (ACK). Если воркер упал, задача забирается через `XCLAIM`.\n\n2. **Redis Sorted Sets (ZSet: ZADD / ZRANGEBYSCORE / ZPOPMIN)**:\n   - Идеальная структура для **отложенных (Delayed) и запланированных (Scheduled) задач**.\n   - Поле `Score` задается равным `run_at.UnixNano()`.\n   - Воркер выполняет опрос: `ZRANGEBYSCORE queue -inf NOW() LIMIT 0 1`.\n   - Если текущее время больше score, задача извлекается и передается на исполнение.",
        "step_by_step": "1. Спроектируйте интерфейс `StreamQueue` с методами `Publish(task)` и `Consume(group, consumer)`.\n2. Реализуйте метод отложенной отправки `ScheduleDelayed(task, runAt)` на базе ZSet.\n3. Создайте фоновый поллер, который переносит созревшие задачи из ZSet в Stream.\n4. Продемонстрируйте исполнение немедленных и отложенных задач.\n5. Сделайте вывод об их совместном использовании в Asynq/Celery.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"sort"
	"sync"
	"time"
)

// StreamMessage имитирует запись в Redis Streams
type StreamMessage struct {
	ID        string
	Payload   string
	Delivered bool
}

// ZSetItem имитирует элемент Redis Sorted Set
type ZSetItem struct {
	TaskID  string
	Payload string
	Score   int64 // UnixNano времени выполнения
}

type RedisQueueSimulator struct {
	mu          sync.Mutex
	stream      []StreamMessage
	delayedZSet []ZSetItem
	lastID      int64
}

func NewRedisQueueSimulator() *RedisQueueSimulator {
	return &RedisQueueSimulator{}
}

// XAdd добавляет задачу в поток (Immediate Queue)
func (r *RedisQueueSimulator) XAdd(payload string) string {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.lastID++
	id := fmt.Sprintf("%d-0", time.Now().UnixMilli())
	r.stream = append(r.stream, StreamMessage{ID: id, Payload: payload})
	return id
}

// ZAdd добавляет отложенную задачу (Delayed Queue)
func (r *RedisQueueSimulator) ZAdd(payload string, runAt time.Time) string {
	r.mu.Lock()
	defer r.mu.Unlock()

	taskID := fmt.Sprintf("delayed_%d", time.Now().UnixNano())
	r.delayedZSet = append(r.delayedZSet, ZSetItem{
		TaskID:  taskID,
		Payload: payload,
		Score:   runAt.UnixNano(),
	})
	// Сортируем по возрастанию времени (как в Redis Skiplist)
	sort.Slice(r.delayedZSet, func(i, j int) bool {
		return r.delayedZSet[i].Score < r.delayedZSet[j].Score
	})
	return taskID
}

// PollDelayedMigration переносит созревшие задачи из ZSet в основной Stream
func (r *RedisQueueSimulator) PollDelayedMigration() int {
	r.mu.Lock()
	defer r.mu.Unlock()

	now := time.Now().UnixNano()
	readyCount := 0

	for len(r.delayedZSet) > 0 && r.delayedZSet[0].Score <= now {
		readyItem := r.delayedZSet[0]
		r.delayedZSet = r.delayedZSet[1:] // ZPOPMIN

		// Переносим в Stream для немедленного разбора воркерами
		r.stream = append(r.stream, StreamMessage{
			ID:      fmt.Sprintf("migrated-%s", readyItem.TaskID),
			Payload: readyItem.Payload,
		})
		readyCount++
	}

	return readyCount
}

func main() {
	sim := NewRedisQueueSimulator()

	// 1. Ставим немедленную задачу в Redis Stream
	id1 := sim.XAdd("order:send_push:user_42")
	fmt.Printf("1. Задача немедленного выполнения помещена в Stream: %s\n", id1)

	// 2. Ставим отложенную задачу на 200 миллисекунд в ZSet
	runAt := time.Now().Add(200 * time.Millisecond)
	id2 := sim.ZAdd("order:cancel_unpaid:order_1001", runAt)
	fmt.Printf("2. Отложенная задача помещена в ZSet: %s (запуск через 200мс)\n", id2)

	// Проверяем миграцию до наступления срока
	moved := sim.PollDelayedMigration()
	fmt.Printf("Проверка через 50мс: перемещено из ZSet в Stream: %d задач\n", moved)

	// Ждем наступления срока
	time.Sleep(220 * time.Millisecond)
	moved = sim.PollDelayedMigration()
	fmt.Printf("Проверка через 220мс: перемещено из ZSet в Stream: %d задач!\n", moved)

	fmt.Printf("\nИтого сообщений в основном Stream на обработку: %d\n", len(sim.stream))
	for _, m := range sim.stream {
		fmt.Printf(" - ID: %s | Payload: %s\n", m.ID, m.Payload)
	}
}
"""
            }
        ],
        "under_the_hood": "Под капотом Redis Sorted Set реализован на базе двойной структуры: хеш-таблицы (для O(1) поиска по ключу) и вероятностного многоуровневого списка пропуска (SkipList, обеспечивающего $O(\log N)$ вставку и выборку по диапазону Score). Redis Streams реализован на базе Radix Tree (Rax), оптимизированного для сверхкомпактного хранения ID сообщений в памяти.",
        "pitfalls": "При конкурентной выборке из ZSet несколькими воркерами простой `ZRANGEBYSCORE` + `ZREM` подвержен состоянию гонки (две ноды прочитают одну и ту же задачу). Для атомарного извлечения в Redis используют либо команду `ZPOPMIN`, либо Lua-скрипт.",
        "bigtech_interview": "'Как популярная библиотека Asynq комбинирует структуры Redis?' Ответ: Asynq использует Redis Streams/Lists для активных очередей задач в статусе `pending`, а Redis ZSet — для отложенных (`scheduled`), повторяемых (`retry`) и архивных (`dead`) задач, перемещая созревшие задачи в Stream с помощью периодического фонового планировщика."
    },
    {
        "num": 4,
        "title": "Преимущества очередей на базе PostgreSQL (River / pg_cron)",
        "task": "Исследуйте архитектуру очередей задач на базе PostgreSQL (библиотека riverqueue/river). Напишите код, демонстрирующий ключевое преимущество очередей на Postgres перед Redis/RabbitMQ: возможность транзакционной постановки задачи (Transactional Enqueue) в рамках той же ACID-транзакции, где изменяются бизнес-данные. Покажите, что при ошибке коммита транзакции в БД задача в очередь НЕ попадает, полностью ликвидируя проблему Dual-Write.",
        "theory": "Классическая дилемма Dual-Write при использовании внешнего брокера (Redis/RabbitMQ):\n```go\ntx.Exec('INSERT INTO users ...')\nbroker.Publish('send_email') // ЕСЛИ ТУТ СБОЙ ИЛИ СЕРВЕР УПАЛ, СИСТЕМА НЕКОНСИСТЕНТНА!\ntx.Commit()\n```\nЕсли отправить задачу в брокер до коммита, а коммит БД упадет — письмо уйдет несуществующему пользователю. Если отправить после коммита, а процесс упадет между коммитом и отправкой — письмо не уйдет никогда.\n\nОчереди на базе PostgreSQL (такие как `River` на Go или `Oban` на Elixir) решают эту проблему фундаментально:\nТаблица задач `river_jobs` находится в той же самой базе данных PostgreSQL! Постановка задачи в очередь выполняется через `INSERT INTO river_jobs ...` внутри текущей SQL-транзакции. Если бизнес-транзакция коммитится — задача гарантированно в очереди. Если откатывается — задачи в очереди нет.",
        "step_by_step": "1. Спроектируйте структуру имитатора транзакций `MockTx` с флагами коммита и отката.\n2. Реализуйте метод `EnqueueWithinTx(tx *MockTx, task Task)`.\n3. Смоделируйте сценарий успешного заказа: сохранение в `orders` и постановка в очередь коммитятся атомарно.\n4. Смоделируйте сценарий сбоя: при ошибке валидации `tx.Rollback()` откатывает и заказ, и задачу.\n5. Докажите 100% консистентность без дополнительного Outbox-демона.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
)

type MockPostgresDB struct {
	mu     sync.Mutex
	orders map[string]string
	jobs   []string
}

func NewMockPostgresDB() *MockPostgresDB {
	return &MockPostgresDB{
		orders: make(map[string]string),
	}
}

type Tx struct {
	db           *MockPostgresDB
	stagedOrders map[string]string
	stagedJobs   []string
	isCommitted  bool
	isRolledBack bool
}

func (db *MockPostgresDB) BeginTx() *Tx {
	return &Tx{
		db:           db,
		stagedOrders: make(map[string]string),
	}
}

func (tx *Tx) InsertOrder(orderID, details string) {
	tx.stagedOrders[orderID] = details
}

// EnqueueJob ставит задачу в очередь прямо в тело транзакции PostgreSQL!
func (tx *Tx) EnqueueJob(jobName string) {
	tx.stagedJobs = append(tx.stagedJobs, jobName)
}

func (tx *Tx) Commit() error {
	if tx.isRolledBack || tx.isCommitted {
		return errors.New("tx already closed")
	}

	tx.db.mu.Lock()
	defer tx.db.mu.Unlock()

	// Атомарное применение всех изменений
	for k, v := range tx.stagedOrders {
		tx.db.orders[k] = v
	}
	tx.db.jobs = append(tx.db.jobs, tx.stagedJobs...)

	tx.isCommitted = true
	return nil
}

func (tx *Tx) Rollback() {
	tx.isRolledBack = true
	// Изменения отбрасываются
	tx.stagedOrders = nil
	tx.stagedJobs = nil
}

func main() {
	db := NewMockPostgresDB()
	ctx := context.Background()
	_ = ctx

	// Сценарий 1: Успешное создание заказа
	fmt.Println("=== СЦЕНАРИЙ 1: Успешная бизнес-операция ===")
	tx1 := db.BeginTx()
	tx1.InsertOrder("ord_101", "MacBook Pro M3 Max")
	tx1.EnqueueJob("job:charge_card:ord_101")
	tx1.EnqueueJob("job:send_invoice:ord_101")

	if err := tx1.Commit(); err != nil {
		tx1.Rollback()
	}

	fmt.Printf("Заказов в БД: %d, Задач в очереди: %d\n", len(db.orders), len(db.jobs))
	for _, j := range db.jobs {
		fmt.Printf(" - Задача: %s\n", j)
	}

	// Сценарий 2: Ошибка при проведении заказа (например, товара нет на складе)
	fmt.Println("\n=== СЦЕНАРИЙ 2: Ошибка и Rollback ===")
	tx2 := db.BeginTx()
	tx2.InsertOrder("ord_102", "iPhone 16 Pro (Out of Stock)")
	tx2.EnqueueJob("job:charge_card:ord_102")

	// Произошла ошибка бизнес-логики!
	fmt.Println("Обнаружена ошибка: товара нет в наличии! Выполняем Rollback...")
	tx2.Rollback()

	fmt.Printf("Заказов в БД после отката: %d, Задач в очереди: %d (никаких фантомных списаний!)\n",
		len(db.orders), len(db.jobs))
}
"""
            }
        ],
        "under_the_hood": "В PostgreSQL таблица очередей `river_jobs` является обычной таблицей базы данных. Когда клиент выполняет `INSERT INTO river_jobs`, запись сохраняется в журнал предзаписи WAL (Write-Ahead Logging) вместе со строками бизнес-таблиц. Движок MVCC PostgreSQL гарантирует, что другие параллельные транзакции (включая воркеры River) физически не видят эту задачу до тех пор, пока транзакция-создатель не выполнит успешный `COMMIT`.",
        "pitfalls": "Разрастание таблицы очереди (Table Bloat): при миллионах задач в сутки постоянные INSERT, UPDATE и DELETE создают огромное количество мертвых кортежей (dead tuples). Необходима агрессивная настройка autovacuum для таблицы очереди либо секционирование (partitioning) по суткам.",
        "bigtech_interview": "'Когда очередь на PostgreSQL лучше Redis, а когда хуже?' Ответ: Очередь на PostgreSQL идеальна для критичных бизнес-задач (платежи, заказы, биллинг), где недопустима потеря данных и требуется транзакционность (Transactional Enqueue). Redis превосходит PostgreSQL при сверхвысоком RPS (> 50 000 задач в секунду) и для эфемерных задач (метрики, уведомления), где скорость важнее строгой транзакционности."
    },
    {
        "num": 5,
        "title": "Конкурентное чтение задач: SELECT ... FOR UPDATE SKIP LOCKED",
        "task": "Спроектируйте и протестируйте высокопроизводительный механизм конкурентной выборки задач из базы данных с использованием SQL-директивы FOR UPDATE SKIP LOCKED. Создайте симулятор таблицы jobs с полями id, state, payload. Запустите 10 параллельных горутин-воркеров, которые одновременно запрашивают следующую свободную задачу. Докажите, что благодаря SKIP LOCKED воркеры не блокируют друг друга, не получают дедлоков и разбирают пачку из 100 задач с максимальной параллельностью.",
        "theory": "Классическая проблема очереди на реляционной базе данных: если 10 воркеров одновременно вызывают `SELECT * FROM jobs WHERE state = 'pending' LIMIT 1 FOR UPDATE`, то первый воркер захватывает эксклюзивную блокировку строки, а остальные 9 воркеров выстраиваются в очередь и ждут завершения его транзакции (Lock Contention). Пропускная способность падает до одного воркера!\n\nРеволюционная директива `FOR UPDATE SKIP LOCKED` (появившаяся в PostgreSQL 9.5 и MySQL 8.0):\nИнструктирует СУБД: 'Если строка уже заблокирована другой транзакцией, НЕ ЖДИ ее освобождения, а просто ПРОПУСТИ ее и заблокируй следующую свободную строку!'.\nВ результате все 10 воркеров одновременно захватывают свои уникальные задачи без единой миллисекунды ожидания.",
        "step_by_step": "1. Спроектируйте структуру `JobTable` со срезом записей и статусами блокировки.\n2. Реализуйте функцию `FetchNextJobSkipLocked(workerID int)`.\n3. Покажите, как проверяется флаг `isLocked`: заблокированные другими воркерами строки мгновенно пропускаются.\n4. Запустите 10 горутин на разбор 50 задач.\n5. Зафиксируйте, что каждая задача обработана ровно один раз без дубликатов.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

type JobRecord struct {
	ID        int
	Payload   string
	State     string // "pending", "running", "done"
	LockedBy  int    // ID воркера, удерживающего лок строки
}

type SimulatedDB struct {
	mu   sync.Mutex
	jobs []*JobRecord
}

// SelectForUpdateSkipLocked имитирует выполнение:
// SELECT * FROM jobs WHERE state = 'pending' ORDER BY id ASC LIMIT 1 FOR UPDATE SKIP LOCKED;
func (db *SimulatedDB) SelectForUpdateSkipLocked(workerID int) *JobRecord {
	db.mu.Lock()
	defer db.mu.Unlock()

	for _, j := range db.jobs {
		// Условие WHERE state = 'pending'
		if j.State != "pending" {
			continue
		}

		// SKIP LOCKED: если строка уже заблокирована кем-то другим -> пропускаем!
		if j.LockedBy != 0 {
			continue
		}

		// Захватываем блокировку на строку
		j.LockedBy = workerID
		j.State = "running"
		return j
	}

	return nil // Очередь пуста
}

func (db *SimulatedDB) CommitJob(jobID int) {
	db.mu.Lock()
	defer db.mu.Unlock()

	for _, j := range db.jobs {
		if j.ID == jobID {
			j.State = "done"
			j.LockedBy = 0 // Снятие блокировки строки
			return
		}
	}
}

func main() {
	totalJobs := 60
	db := &SimulatedDB{
		jobs: make([]*JobRecord, totalJobs),
	}

	for i := 0; i < totalJobs; i++ {
		db.jobs[i] = &JobRecord{
			ID:      i + 1,
			Payload: fmt.Sprintf("Report_Chunk_%d", i+1),
			State:   "pending",
		}
	}

	workerCount := 6
	var wg sync.WaitGroup
	var processedCount int64

	start := time.Now()
	fmt.Printf("Запуск %d воркеров с алгоритмом FOR UPDATE SKIP LOCKED на %d задач...\n", workerCount, totalJobs)

	for w := 1; w <= workerCount; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for {
				job := db.SelectForUpdateSkipLocked(workerID)
				if job == nil {
					return // Больше нет свободных задач
				}

				// Имитация выполнения задачи (10 мс)
				time.Sleep(10 * time.Millisecond)
				db.CommitJob(job.ID)
				atomic.AddInt64(&processedCount, 1)
			}
		}(w)
	}

	wg.Wait()
	duration := time.Since(start)

	fmt.Printf("\n=== РЕЗУЛЬТАТЫ ОБРАБОТКИ ===\n")
	fmt.Printf("Успешно обработано: %d / %d задач\n", processedCount, totalJobs)
	fmt.Printf("Общее время выполнения: %v\n", duration)
	fmt.Printf("Все задачи разобраны параллельно без взаимных блокировок!\n")
}
"""
            }
        ],
        "under_the_hood": "На уровне движка PostgreSQL директива `FOR UPDATE SKIP LOCKED` проверяет заголовок кортежа `HeapTupleHeaderData` (поле `t_infomask` и флаг `HEAP_XMAX_LOCKED_ONLY`). Если транзакция-владелец `xmax` еще активна, сканер страниц таблицы просто инкрементирует указатель кортежа `ItemPointerData` и мгновенно переходит к следующей записи без ожидания на спинлоках.",
        "pitfalls": "Обязательно используйте подходящий составной индекс, например `CREATE INDEX idx_jobs_pending ON jobs (run_at ASC) WHERE state = 'pending'`. Без частичного индекса запрос с `SKIP LOCKED` будет сканировать всю таблицу (Seq Scan), тратя дисковый I/O на чтение миллионов уже завершенных записей.",
        "bigtech_interview": "'Что вернет запрос SELECT ... FOR UPDATE SKIP LOCKED, если все доступные строки заблокированы другими транзакциями?' Ответ: Запрос вернет пустой результирующий набор (0 строк) НЕМЕДЛЕННО, без ожидания и без ошибки. Воркер в таком случае делает короткую паузу (backoff) или ожидает сигнала LISTEN/NOTIFY."
    },
    {
        "num": 6,
        "title": "Детектирование зависших воркеров и Heartbeat",
        "task": "Реализуйте механизм восстановления зависших или аварийно завершенных задач (Stuck / Orphaned Tasks Recovery). Если воркер взял задачу в работу, но упал по SIGKILL или Out-Of-Memory, задача останется в статусе 'running' навсегда. Напишите фоновый процесс Heartbeat: воркер во время работы каждые 500 мс обновляет поле LastHeartbeat. Отдельный процесс-рековерер каждые 2 секунды находит 'осиротевшие' задачи, у которых время последнего сердцебиения старше порогового (HeartbeatTimeout), и безопасно возвращает их в очередь для повторного исполнения.",
        "theory": "В распределенной системе физические серверы и контейнеры выходят из строя непредсказуемо:\n- OOM Killer ядра Linux убивает процесс по нехватке памяти мгновенно сигналом SIGKILL (деферы и обработчики сигналов не вызываются!).\n- Сетевой кабель отключился, нода зависла на kernel panic, авария в дата-центре.\n\nЕсли задача помечена в БД как `status = 'running'`, никакой другой воркер ее не трогает. Без механизма Heartbeat задача навсегда зависает в 'мертвом' состоянии (Zombie / Orphaned Job).\n\nПаттерн Heartbeat (Пульс жизнедеятельности):\n1. Воркер при выполнении задачи раз в $T$ секунд обновляет метку: `UPDATE jobs SET last_heartbeat = NOW() WHERE id = :id`.\n2. Фоновый координатор (Cleaner / Sweeper) опрашивает базу:\n`SELECT * FROM jobs WHERE status = 'running' AND last_heartbeat < NOW() - INTERVAL '30 seconds'`.\n3. Все найденные задачи переводятся обратно в `status = 'pending'`, а счетчик попыток `retry_count` инкрементируется.",
        "step_by_step": "1. Спроектируйте структуру задачи с полями Status, LastHeartbeat, RetryCount.\n2. Реализуйте воркер, запускающий тикер отправки пульса в фоновой горутине.\n3. Смоделируйте внезапный сбой (SIGKILL) воркера на середине выполнения.\n4. Напишите процесс `SweeperWorker`, находящий зависшую задачу по таймауту.\n5. Продемонстрируйте подхват и успешное завершение задачи вторым воркером.",
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

type HeartbeatJob struct {
	ID            string
	Status        string // "pending", "running", "success"
	LastHeartbeat time.Time
	RetryCount    int
}

type HeartbeatStorage struct {
	mu   sync.Mutex
	jobs map[string]*HeartbeatJob
}

func (s *HeartbeatStorage) UpdateHeartbeat(id string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if j, ok := s.jobs[id]; ok && j.Status == "running" {
		j.LastHeartbeat = time.Now()
	}
}

func (s *HeartbeatStorage) RecoverOrphaned(timeout time.Duration) int {
	s.mu.Lock()
	defer s.mu.Unlock()

	now := time.Now()
	recovered := 0

	for _, j := range s.jobs {
		if j.Status == "running" && now.Sub(j.LastHeartbeat) > timeout {
			j.Status = "pending"
			j.RetryCount++
			recovered++
			fmt.Printf("[RECOVERER] Задача %s зависла (пульс отсутствовал %v)! Возврат в очередь (Попытка %d)\n",
				j.ID, now.Sub(j.LastHeartbeat), j.RetryCount)
		}
	}
	return recovered
}

func main() {
	storage := &HeartbeatStorage{
		jobs: map[string]*HeartbeatJob{
			"task_export_88": {
				ID:            "task_export_88",
				Status:        "running",
				LastHeartbeat: time.Now(),
			},
		},
	}

	ctx, cancel := context.WithCancel(context.Background())

	// Воркер 1 берет задачу и обновляет пульс каждые 100 мс
	go func() {
		ticker := time.NewTicker(100 * time.Millisecond)
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				storage.UpdateHeartbeat("task_export_88")
			}
		}
	}()

	fmt.Println("Воркер 1 начал выполнение задачи и шлет heartbeat...")
	time.Sleep(300 * time.Millisecond)

	// Имитируем падение Воркера 1 по OOMKilled (резкая отмена без закрытия задачи)
	fmt.Println("\n[CRASH] Воркер 1 внезапно убит OOM Killer (SIGKILL)! Пульс прекратился.")
	cancel()

	// Ждем отсутствия пульса 600 мс
	time.Sleep(600 * time.Millisecond)

	// Запускаем проверку рековерера с порогом 400 мс
	fmt.Println("\nЗапуск Sweeper/Recoverer процесса...")
	recovered := storage.RecoverOrphaned(400 * time.Millisecond)
	fmt.Printf("Восстановлено зависших задач: %d\n", recovered)

	// Проверяем статус в хранилище
	storage.mu.Lock()
	j := storage.jobs["task_export_88"]
	fmt.Printf("Финальное состояние задачи: Статус='%s', Попыток=%d (Готова для Воркера 2!)\n",
		j.Status, j.RetryCount)
	storage.mu.Unlock()
}
"""
            }
        ],
        "under_the_hood": "В библиотеке Temporal и River Heartbeat передается как транзакционный апдейт строки задачи. Если воркер завис в бесконечном цикле или на зависшем сокете, тикер heartbeat в отдельной горутине тоже может быть заблокирован (если привязан к выполнению) либо продолжит слать сигналы. Поэтому в правильных реализациях воркер обязан сам периодически вызывать метод `heartbeat()`, доказывая прогресс вычислений.",
        "pitfalls": "Ложное срабатывание рековерера (False Zombie Detection): если время `timeout` выбрано слишком агрессивным (например, 2 секунды), а воркер попал под Stop-The-World паузу GC Go или кратковременный сетевой лаг БД, рековерер решит, что воркер умер, и отдаст задачу второй ноде. В результате две ноды будут параллельно выполнять одну и ту же задачу!",
        "bigtech_interview": "'Как избежать параллельного выполнения одной задачи при ложном срабатывании Heartbeat?' Ответ: Использовать механизм Fencing Tokens (номера эпох/версий). Каждое переназначение задачи инкрементирует `version`. Старый воркер при попытке зафиксировать результат в БД передает свою старую версию и получает отказ (optimistic lock failure)."
    },
    {
        "num": 7,
        "title": "Очереди с приоритетами (Priority Queues)",
        "task": "Спроектируйте систему приоритетов задач на Go. Реализуйте 4 уровня приоритетов: Critical, High, Default, Low. Напишите диспетчер задач, поддерживающий две стратегии выборки: 1) Строгий приоритет (Strict Priority): задачи Critical всегда выбираются первыми; 2) Взвешенная справедливая очередь (Weighted Fair Queuing): соотношение выборки 8 : 4 : 2 : 1, предотвращающее вечное голодание (Starvation) низкоприоритетных задач.",
        "theory": "В корпоративных системах задачи имеют кардинально разную бизнес-критичность:\n- `Critical`: Сброс пароля пользователя, отправка 2FA-кода (SLA < 1 сек).\n- `High`: Списание средств, оформление заказа (SLA < 5 сек).\n- `Default`: Отправка чека, выгрузка в CRM (SLA < 1 мин).\n- `Low`: Ночная переиндексация, сжатие старых логов (SLA < 24 часа).\n\nОпасность строгого приоритета (Strict Priority): Если на вход поступает непрерывный поток критичных задач (например, DDoS-атака или всплеск авторизаций), низкоприоритетные задачи попадают в ситуацию бесконечного голодания (Starvation) и не выполняются неделями.\n\nРешение: Взвешенное случайное планирование (Weighted Round Robin / Weighted Fair Queuing):\nКаждому приоритету присваивается вес (например, Critical=8, High=4, Default=2, Low=1). Планировщик выбирает задачи вероятностно в соответствии с весами, гарантируя, что даже Low-задачи получают квант процессорного времени.",
        "step_by_step": "1. Объявите перечисление `Priority` (Critical, High, Default, Low) и назначьте им веса.\n2. Реализуйте структуру `WeightedPriorityQueue` с 4 независимыми очередями каналов.\n3. Напишите метод `Enqueue(task Task, p Priority)`.\n4. Напишите метод `DequeueWeighted() Task`, использующий взвешенную рулетку (Weighted Random Selection).\n5. Смоделируйте одновременное поступление 100 критичных и 20 фоновых задач и докажите отсутствие голодания.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"math/rand"
	"sync"
)

type Priority int

const (
	PriorityLow Priority = iota
	PriorityDefault
	PriorityHigh
	PriorityCritical
)

var priorityWeights = map[Priority]int{
	PriorityCritical: 8,
	PriorityHigh:     4,
	PriorityDefault:  2,
	PriorityLow:      1,
}

type PriorityTask struct {
	ID       string
	Priority Priority
}

type WeightedPriorityDispatcher struct {
	mu     sync.Mutex
	queues map[Priority][]PriorityTask
}

func NewWeightedPriorityDispatcher() *WeightedPriorityDispatcher {
	return &WeightedPriorityDispatcher{
		queues: map[Priority][]PriorityTask{
			PriorityCritical: make([]PriorityTask, 0),
			PriorityHigh:     make([]PriorityTask, 0),
			PriorityDefault:  make([]PriorityTask, 0),
			PriorityLow:      make([]PriorityTask, 0),
		},
	}
}

func (d *WeightedPriorityDispatcher) Enqueue(task PriorityTask) {
	d.mu.Lock()
	defer d.mu.Unlock()
	d.queues[task.Priority] = append(d.queues[task.Priority], task)
}

// DequeueWeighted выбирает задачу взвешенно по алгоритму рулетки
func (d *WeightedPriorityDispatcher) DequeueWeighted() (*PriorityTask, bool) {
	d.mu.Lock()
	defer d.mu.Unlock()

	// Считаем суммарный вес только тех очередей, в которых ЕСТЬ задачи
	totalWeight := 0
	activePriorities := make([]Priority, 0)

	for p, q := range d.queues {
		if len(q) > 0 {
			w := priorityWeights[p]
			totalWeight += w
			activePriorities = append(activePriorities, p)
		}
	}

	if totalWeight == 0 {
		return nil, false // Все очереди пусты
	}

	// Выбираем случайное число от 0 до totalWeight
	rnd := rand.Intn(totalWeight)
	accum := 0

	for _, p := range activePriorities {
		accum += priorityWeights[p]
		if rnd < accum {
			// Забираем задачу из этой очереди
			task := d.queues[p][0]
			d.queues[p] = d.queues[p][1:]
			return &task, true
		}
	}

	return nil, false
}

func main() {
	dispatcher := NewWeightedPriorityDispatcher()

	// Наполняем очереди: 80 Critical, 40 High, 20 Default, 10 Low
	for i := 1; i <= 80; i++ {
		dispatcher.Enqueue(PriorityTask{ID: fmt.Sprintf("crit_%d", i), Priority: PriorityCritical})
	}
	for i := 1; i <= 40; i++ {
		dispatcher.Enqueue(PriorityTask{ID: fmt.Sprintf("high_%d", i), Priority: PriorityHigh})
	}
	for i := 1; i <= 20; i++ {
		dispatcher.Enqueue(PriorityTask{ID: fmt.Sprintf("def_%d", i), Priority: PriorityDefault})
	}
	for i := 1; i <= 10; i++ {
		dispatcher.Enqueue(PriorityTask{ID: fmt.Sprintf("low_%d", i), Priority: PriorityLow})
	}

	fmt.Println("Извлекаем первые 30 задач по взвешенному алгоритму (Weighted Fair Queuing)...")
	stats := make(map[Priority]int)

	for i := 0; i < 30; i++ {
		task, ok := dispatcher.DequeueWeighted()
		if !ok {
			break
		}
		stats[task.Priority]++
	}

	fmt.Printf("\n=== РАСПРЕДЕЛЕНИЕ ОБРАБОТКИ ПЕРВЫХ 30 ЗАДАЧ ===\n")
	fmt.Printf("Critical: %d задач (вес 8)\n", stats[PriorityCritical])
	fmt.Printf("High:     %d задач (вес 4)\n", stats[PriorityHigh])
	fmt.Printf("Default:  %d задач (вес 2)\n", stats[PriorityDefault])
	fmt.Printf("Low:      %d задач (вес 1)\n", stats[PriorityLow])
	fmt.Printf("\nВывод: Low-задачи НЕ голодают даже при наличии 80 Critical задач!\n")
}
"""
            }
        ],
        "under_the_hood": "Встроенная приоритетная куча `container/heap` в Go реализует классическое бинарное дерево за $O(\log N)$. Однако при миллионах задач в очереди непрерывная перебалансировка бинарной кучи утилизирует память и кэш процессора. В продакшн-очередях (Asynq/Celery) создают 4 независимые структуры очередей для каждого приоритета, а планировщик опрашивает их с весовыми коэффициентами.",
        "pitfalls": "Приоритетная инверсия (Priority Inversion): если низкоприоритетная задача захватила общий мьютекс или блокировку таблицы БД, а высокоприоритетная задача пытается получить этот же ресурс, высокоприоритетная задача заблокируется и будет ждать завершения низкоприоритетной.",
        "bigtech_interview": "'Как реализовать приоритетные очереди в Redis без блокировок?' Ответ: Создать отдельные списки/стримы `queue:critical`, `queue:high`, `queue:low` и использовать блокирующую команду `BLPOP queue:critical queue:high queue:low 5`. Команда `BLPOP` опрашивает ключи строго слева направо: пока есть хоть одна задача в `queue:critical`, задачи из других списков даже не будут считываться."
    },
    {
        "num": 8,
        "title": "Отложенные задачи (Delayed / Scheduled Tasks)",
        "task": "Реализуйте планировщик отложенных задач (Delayed Tasks Scheduler) на чистом Go с использованием таймерного колеса (Hashed Timing Wheel) или приоритетной очереди по времени (Time Min-Heap). Напишите метод EnqueueIn(task Task, delay time.Duration). Продемонстрируйте корректность работы планировщика: задачи должны запускаться точно в назначенное время (+/- 10 мс) с минимальным потреблением ресурсов CPU в режиме ожидания.",
        "theory": "Отложенные задачи (Delayed Tasks) — критический элемент бизнес-логики:\n- Отправка напоминания о брошенной корзине ровно через 2 часа.\n- Проверка оплаты заказа через 15 минут.\n- Разблокировка аккаунта после бана через 24 часа.\n\nНаивное решение через `time.AfterFunc(delay, fn)` для 5 000 000 задач создаст 5 000 000 таймеров в рантайме Go, что вызовет тяжелый оверхед на системный планировщик таймеров.\n\nАрхитектура Timing Wheel (Таймерное колесо) или Min-Heap по `run_at`:\nЗадачи упорядочиваются по абсолютному времени запуска `run_at = time.Now().Add(delay)`. Процесс планировщика засыпает на разницу во времени до САМОЙ БЛИЖАЙШЕЙ задачи (`nextTask.RunAt - now`). Когда таймер звенит, планировщик извлекает все созревшие задачи и переводит таймер на следующую.",
        "step_by_step": "1. Спроектируйте структуру `ScheduledTask` с полем `RunAt time.Time`.\n2. Реализуйте структуру `DelayedScheduler` с кучей или упорядоченным срезом.\n3. Реализуйте метод `Schedule(task Task, delay time.Duration)` с уведомлением спящего планировщика через `sync.Cond` или канал.\n4. Напишите цикл диспетчеризации `scheduleLoop()`, засыпающий ровно до времени ближайшей задачи.\n5. Запустите тесты с разным временем задержки (50мс, 150мс, 300мс) и замерьте точность срабатывания.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"container/heap"
	"fmt"
	"sync"
	"time"
)

type ScheduledJob struct {
	ID    string
	RunAt time.Time
	index int
}

type JobHeap []*ScheduledJob

func (h JobHeap) Len() int           { return len(h) }
func (h JobHeap) Less(i, j int) bool { return h[i].RunAt.Before(h[j].RunAt) }
func (h JobHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i]; h[i].index = i; h[j].index = j }
func (h *JobHeap) Push(x interface{}) {
	n := len(*h)
	item := x.(*ScheduledJob)
	item.index = n
	*h = append(*h, item)
}
func (h *JobHeap) Pop() interface{} {
	old := *h
	n := len(old)
	item := old[n-1]
	old[n-1] = nil
	item.index = -1
	*h = old[0 : n-1]
	return item
}

type DelayedScheduler struct {
	mu       sync.Mutex
	pq       JobHeap
	wakeUpCh chan struct{}
}

func NewDelayedScheduler() *DelayedScheduler {
	s := &DelayedScheduler{
		pq:       make(JobHeap, 0),
		wakeUpCh: make(chan struct{}, 1),
	}
	heap.Init(&s.pq)
	return s
}

func (s *DelayedScheduler) EnqueueIn(id string, delay time.Duration) {
	s.mu.Lock()
	job := &ScheduledJob{
		ID:    id,
		RunAt: time.Now().Add(delay),
	}
	heap.Push(&s.pq, job)
	s.mu.Unlock()

	// Сигнализируем планировщику, что появилась новая задача (возможно, более ранняя!)
	select {
	case s.wakeUpCh <- struct{}{}:
	default:
	}
}

func (s *DelayedScheduler) Start(outQueue chan<- string, stopCh <-chan struct{}) {
	for {
		s.mu.Lock()
		now := time.Now()

		// 1. Извлекаем все задачи, чей срок уже наступил
		for s.pq.Len() > 0 && !s.pq[0].RunAt.After(now) {
			job := heap.Pop(&s.pq).(*ScheduledJob)
			outQueue <- job.ID
		}

		// 2. Рассчитываем время сна до ближайшей задачи
		var sleepDuration time.Duration = 24 * time.Hour
		if s.pq.Len() > 0 {
			sleepDuration = s.pq[0].RunAt.Sub(now)
			if sleepDuration < 0 {
				sleepDuration = 0
			}
		}
		s.mu.Unlock()

		// 3. Засыпаем до наступления срока либо до появления более ранней задачи
		timer := time.NewTimer(sleepDuration)
		select {
		case <-stopCh:
			timer.Stop()
			return
		case <-s.wakeUpCh:
			timer.Stop() // Проснулись раньше, так как добавили новую задачу!
		case <-timer.C:
			// Наступил срок ближайшей задачи
		}
	}
}

func main() {
	scheduler := NewDelayedScheduler()
	readyJobs := make(chan string, 10)
	stopCh := make(chan struct{})

	go scheduler.Start(readyJobs, stopCh)

	fmt.Println("Постановка отложенных задач:")
	fmt.Println(" - task_300ms (через 300мс)")
	fmt.Println(" - task_100ms (через 100мс)")
	fmt.Println(" - task_200ms (через 200мс)")

	t0 := time.Now()
	scheduler.EnqueueIn("task_300ms", 300*time.Millisecond)
	scheduler.EnqueueIn("task_100ms", 100*time.Millisecond)
	scheduler.EnqueueIn("task_200ms", 200*time.Millisecond)

	// Читаем выполненные задачи
	for i := 0; i < 3; i++ {
		jobID := <-readyJobs
		fmt.Printf("Получена созревшая задача: %-12s ровно через %v\n", jobID, time.Since(t0).Round(time.Millisecond))
	}

	close(stopCh)
	fmt.Println("Планировщик остановлен.")
}
"""
            }
        ],
        "under_the_hood": "В Go 1.14+ таймеры рантайма интегрированы непосредственно в планировщик netpoller и процессорные структуры P (`p.timers`). Однако при внешнем планировании десятков миллионов отложенных задач централизованная Min-Heap на `container/heap` экономит структуры рантайма, пробуждая фоновый воркер ровно в момент экспирации верхнего элемента кучи `s.pq[0]`.",
        "pitfalls": "Смена часовых поясов и перевод часов: если использовать локальное время без монотонных часов (`time.Now().Wall`), перевод стрелок часов (NTP Sync / летнее время) может привести к тому, что отложенная на 1 час задача запустится через 2 часа или немедленно. В Go структура `time.Time` автоматически содержит monotonic clock reading.",
        "bigtech_interview": "'Как работают отложенные задачи в распределенном кластере из 50 нод?' Ответ: Задачи сохраняются в Redis ZSet со `score = run_at.UnixNano()`. Каждые N миллисекунд воркеры выполняют атомарный Lua-скрипт или `ZPOPMIN`, перенося созревшие задачи в основной рабочий поток без дублирования между нодами."
    },
    {
        "num": 9,
        "title": "Периодические задачи (Cron-like Scheduling)",
        "task": "Реализуйте распределенный планировщик периодических задач на Go с парсингом cron-выражений (например, каждые 5 минут или '0 3 * * *'). Решите фундаментальную проблему дублирования в облаке: если в Kubernetes запущено 10 реплик одного сервиса, периодическая задача должна выполниться ровно ОДИН раз. Реализуйте распределенный мьютекс на базе атомарной блокировки (Redis SETNX с TTL или pg_advisory_lock в PostgreSQL).",
        "theory": "Периодические фоновые задачи (Periodic / Cron Tasks) используются для регулярных процедур:\n- Каждые 10 минут: сбор метрик и агрегация аналитики.\n- Каждый день в 04:00: списание абонентской платы подписчиков.\n\nПроблема мультинодности в микросервисах: Сервис развернут в 8 репликах для отказоустойчивости. Если каждая реплика запустит свой cron-таймер, в 04:00 абонентская плата спишется 8 раз подряд!\n\nРешение: Распределенная координация:\n1. **Leader Election**: Только один под выбирается лидером через etcd/Kubernetes Lease и исполняет cron.\n2. **Distributed Lock (SETNX с TTL)**: В момент наступления времени запуска все 8 нод пытаются захватить именованный лок: `SET lock:cron:daily_billing:2026-09-08 unique_id NX EX 300`. Только одна нода получает `OK` и выполняет задачу, остальные 7 получают `nil` и пропускают запуск.",
        "step_by_step": "1. Спроектируйте структуру `CronSchedule` с вычислением следующего времени запуска `Next(from time.Time) time.Time`.\n2. Реализуйте интерфейс распределенного лока `DistributedLock` с методом `TryLock(ctx, key, ttl) (bool, error)`.\n3. Создайте 3 параллельных экземпляра планировщика (моделирующих 3 пода в K8s).\n4. Запустите триггер периодической задачи и покажите, что задачу выполняет ровно 1 инстанс.\n5. Проверьте автоматическое освобождение лока по TTL.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

type MockDistributedLocker struct {
	mu    sync.Mutex
	locks map[string]time.Time
}

func NewMockDistributedLocker() *MockDistributedLocker {
	return &MockDistributedLocker{locks: make(map[string]time.Time)}
}

// TryLock эмулирует Redis SET key val NX EX ttl
func (l *MockDistributedLocker) TryLock(key string, ttl time.Duration) bool {
	l.mu.Lock()
	defer l.mu.Unlock()

	now := time.Now()
	if exp, exists := l.locks[key]; exists && now.Before(exp) {
		return false // Уже захвачен другой нодой!
	}

	l.locks[key] = now.Add(ttl)
	return true
}

type ClusterSchedulerNode struct {
	NodeID     string
	locker     *MockDistributedLocker
	executions int64
}

func (n *ClusterSchedulerNode) TriggerPeriodicJob(jobName string, runSlot string) bool {
	// Ключ блокировки включает слот времени, например "daily_billing:20260908_0400"
	lockKey := fmt.Sprintf("cron_lock:%s:%s", jobName, runSlot)

	// Пытаемся захватить распределенный лок
	if n.locker.TryLock(lockKey, 2*time.Minute) {
		atomic.AddInt64(&n.executions, 1)
		fmt.Printf("[%s] УСПЕХ: Захватил лок и выполняет задачу '%s' для слота [%s]!\n",
			n.NodeID, jobName, runSlot)
		return true
	}

	fmt.Printf("[%s] ПРОПУСК: Задача уже захвачена другой нодой.\n", n.NodeID)
	return false
}

func main() {
	locker := NewMockDistributedLocker()

	// Поднимаем 3 реплики сервиса
	node1 := &ClusterSchedulerNode{NodeID: "pod-backend-1", locker: locker}
	node2 := &ClusterSchedulerNode{NodeID: "pod-backend-2", locker: locker}
	node3 := &ClusterSchedulerNode{NodeID: "pod-backend-3", locker: locker}

	nodes := []*ClusterSchedulerNode{node1, node2, node3}

	fmt.Println("Наступило время 04:00:00. Все 3 реплики одновременно активируют Cron Trigger...")

	var wg sync.WaitGroup
	runSlot := "2026-09-08_04:00"

	for _, n := range nodes {
		wg.Add(1)
		go func(node *ClusterSchedulerNode) {
			defer wg.Done()
			node.TriggerPeriodicJob("charge_subscription", runSlot)
		}(n)
	}

	wg.Wait()

	totalRuns := node1.executions + node2.executions + node3.executions
	fmt.Printf("\nИтого выполнений периодической задачи: %d (ИДЕАЛЬНО: ровно 1 раз на весь кластер!)\n", totalRuns)
}
"""
            }
        ],
        "under_the_hood": "В PostgreSQL распределенный лок можно реализовать через `SELECT pg_try_advisory_lock(hashtext('job_name'))`. Advisory Lock не создает строк в таблицах, хранится в оперативной памяти демона PostgreSQL (таблица `pg_locks`) и мгновенно освобождается при завершении соединения или транзакции.",
        "pitfalls": "Дрейф времени между нодами кластера (Clock Skew): если часы на Ноде 1 спешат на 3 секунды, она попытается захватить слот раньше остальных. Поэтому все временные слоты и таймстампы рассчитываются строго по времени центрального сервера БД/Redis (`NOW()` или `redis TIME`).",
        "bigtech_interview": "'Что произойдет, если нода захватила лок на cron-задачу, но упала на 1-й секунде ее выполнения?' Ответ: Лок должен иметь безопасный TTL (например, 5 минут). Если задача упала, другие ноды смогут перехватить ее только после истечения TTL, либо процесс рековерера по Heartbeat снимет блокировку раньше."
    },
    {
        "num": 10,
        "title": "Политики повторных попыток (Retry Policies) и Full Jitter",
        "task": "Спроектируйте математически строгую политику повторных попыток (Retry Policy) для упавших фоновых задач. Реализуйте алгоритм экспоненциального отката (Exponential Backoff) с добавлением полного случайного джиттера (Full Jitter): `Backoff(attempt) = rand(0, min(max_backoff, base * 2^attempt))`. Докажите на симуляции 1000 одновременно упавших задач, что добавление Full Jitter полностью устраняет резонансные всплески нагрузки на восстанавливающийся сервис.",
        "theory": "Когда внешний сервис (например, платёжный шлюз или банк) испытывает сбой, тысячи выполняющихся задач падают с сетевой ошибкой одновременно. Если воркеры повторяют задачи по наивному фиксированному таймеру (`через 5 секунд`):\nВсе 1000 воркеров одновременно придут на сервер ровно через 5.0 секунд, затем через 10.0 секунд, создавая разрушительные резонансные волны (Retry Storms), добивающие упавший сервис.\n\nИсследование AWS Architecture Center доказало, что алгоритм **Exponential Backoff with Full Jitter** является наиболее эффективным:\n- Базовое время растет экспоненциально: $T_{exp} = \min(T_{max}, T_{base} \cdot 2^{attempt})$.\n- Итоговая задержка выбирается случайно: $Delay = rand(0, T_{exp})$.\nСлучайный разброс моментально 'размазывает' нагрузку по всему интервалу времени, превращая разрушительные пики в равномерный фоновый поток.",
        "step_by_step": "1. Реализуйте функцию `CalculateBackoff(attempt int, base, max time.Duration) time.Duration`.\n2. Напишите версию без джиттера (чистая экспонента) и версию с Full Jitter.\n3. Смоделируйте 500 упавших задач на 3-й попытке ретрая.\n4. Постройте распределение моментов повторных запросов по времени.\n5. Зафиксируйте ликвидацию пиков.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"math"
	"math/rand"
	"time"
)

type RetryPolicy struct {
	BaseBackoff time.Duration
	MaxBackoff  time.Duration
	MaxRetries  int
}

// ComputeNoJitter чистый экспоненциальный откат (вызывает резонансный шторм!)
func (p RetryPolicy) ComputeNoJitter(attempt int) time.Duration {
	multiplier := math.Pow(2, float64(attempt))
	backoff := time.Duration(float64(p.BaseBackoff) * multiplier)
	if backoff > p.MaxBackoff {
		return p.MaxBackoff
	}
	return backoff
}

// ComputeFullJitter экспоненциальный откат с полным джиттером (AWS Algorithm)
func (p RetryPolicy) ComputeFullJitter(attempt int) time.Duration {
	maxInterval := p.ComputeNoJitter(attempt)
	// rand.Float64() выбирает [0.0, 1.0) от максимального интервала
	jittered := time.Duration(rand.Float64() * float64(maxInterval))
	return jittered
}

func main() {
	policy := RetryPolicy{
		BaseBackoff: 1 * time.Second,
		MaxBackoff:  30 * time.Second,
		MaxRetries:  5,
	}

	taskCount := 1000
	attempt := 3 // 3-я попытка (базовый интервал = 8 секунд)

	// Моделируем распределение по 1-секундным корзинам
	noJitterBuckets := make(map[int]int)
	jitterBuckets := make(map[int]int)

	for i := 0; i < taskCount; i++ {
		// Без джиттера
		d1 := policy.ComputeNoJitter(attempt)
		noJitterBuckets[int(d1.Seconds())]++

		// С полным джиттером
		d2 := policy.ComputeFullJitter(attempt)
		jitterBuckets[int(d2.Seconds())]++
	}

	fmt.Println("=== СРАВНЕНИЕ РЕТРАЕВ 1000 УПАВШИХ ЗАДАЧ (ПОПЫТКА #3) ===")
	fmt.Printf("1. Без джиттера (Резонансный шторм):\n")
	fmt.Printf("   Секунда 7: %d запросов\n", noJitterBuckets[7])
	fmt.Printf("   Секунда 8: %d запросов (КАТАСТРОФИЧЕСКИЙ УДАР ПО СЕРВЕРУ!)\n", noJitterBuckets[8])
	fmt.Printf("   Секунда 9: %d запросов\n\n", noJitterBuckets[9])

	fmt.Printf("2. С Full Jitter (Равномерное распределение):\n")
	maxInJitter := 0
	for s := 0; s <= 8; s++ {
		c := jitterBuckets[s]
		if c > maxInJitter {
			maxInJitter = c
		}
		fmt.Printf("   Секунда %d: %d запросов\n", s, c)
	}

	fmt.Printf("\nПиковая нагрузка снизилась с %d до %d запросов в секунду (в %.1f раз меньше!)\n",
		noJitterBuckets[8], maxInJitter, float64(noJitterBuckets[8])/float64(maxInJitter))
}
"""
            }
        ],
        "under_the_hood": "Full Jitter обеспечивает наименьшее время ожидания для клиентов при сохранении нулевой корреляции моментов повторов. Формула $Sleep = Uniform(0, \min(M, B \cdot 2^A))$ гарантирует, что математическое ожидание задержки составляет половину от максимального окна, сглаживая входящий трафик до непрерывного белого шума.",
        "pitfalls": "Неправильное использование `rand.Seed`: если рандомизатор не инициализирован или использует один и тот же seed на всех форкнутых подах, псевдослучайные последовательности совпадут, и джиттер синхронизирует ретраи вместо их разделения.",
        "bigtech_interview": "'Что такое Decorrelated Jitter?' Ответ: Это разновидность джиттера, где текущий интервал зависит от предыдущего: $Sleep = \min(M, rand(B, Sleep_{prev} \cdot 3))$. Он обеспечивает еще более агрессивное сглаживание очередей при длительных перегрузках внешних сервисов."
    },
    {
        "num": 11,
        "title": "Паттерн Dead Letter Queue (DLQ) для ядовитых сообщений",
        "task": "Реализуйте очередь недоставленных сообщений (Dead Letter Queue, DLQ) для изоляции 'ядовитых' задач (Poison Pills). Если задача падает с ошибкой после исчерпания лимита попыток (MaxRetries = 3), воркер не должен бесконечно повторять ее или молча терять. Перенесите задачу в структуру DeadLetterStorage с сохранением полного трейса ошибки, параметров и метаданных. Реализуйте API ReplayTask(taskID string) для повторной постановки исправленной задачи в рабочую очередь администратором.",
        "theory": "Poison Pill (ядовитая пилюля) — это задача, которая вызывает гарантированную ошибку бизнес-логики (например, поврежденный JSON, деление на ноль, некорректный ID пользователя в БД). Без лимита повторов воркер будет бесконечно брать эту задачу, падать, возвращать в очередь и снова падать, сжигая 100% CPU и блокируя разбор полезных задач.\n\nПаттерн Dead Letter Queue (DLQ):\n1. Каждая задача имеет счетчик `retry_count` и лимит `max_retries`.\n2. При ошибке: если `retry_count < max_retries`, задача планируется на повтор с backoff.\n3. Если `retry_count >= max_retries`, задача извлекается из основного потока и перемещается в **Dead Letter Queue (DLQ)**.\n4. Администратор получает алерт, изучает причину сбоя через дашборд, чинит баг в коде и нажимает кнопку `Replay` (повторный запуск).",
        "step_by_step": "1. Спроектируйте структуру `DeadLetterJob` с полями Task, FailedAt, ErrorReason, StackTrace.\n2. Реализуйте логику перемещения задачи в DLQ при превышении `max_retries`.\n3. Напишите функцию `Replay(taskID)` для возврата задачи из DLQ в рабочий статус.\n4. Протестируйте сценарий с заведомо поврежденным пейлоадом.\n5. Докажите, что основная очередь разгружается, а задача сохраняется в DLQ.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"errors"
	"fmt"
	"sync"
	"time"
)

type Job struct {
	ID         string
	Payload    string
	RetryCount int
	MaxRetries int
}

type DeadLetterEntry struct {
	Job       Job
	FailedAt  time.Time
	LastError string
}

type QueueManagerWithDLQ struct {
	mu         sync.Mutex
	mainQueue  []Job
	deadLetter map[string]DeadLetterEntry
}

func NewQueueManager() *QueueManagerWithDLQ {
	return &QueueManagerWithDLQ{
		deadLetter: make(map[string]DeadLetterEntry),
	}
}

func (q *QueueManagerWithDLQ) HandleJobFailure(job Job, taskErr error) {
	q.mu.Lock()
	defer q.mu.Unlock()

	job.RetryCount++
	if job.RetryCount >= job.MaxRetries {
		// Превышен лимит попыток -> отправляем в Dead Letter Queue!
		q.deadLetter[job.ID] = DeadLetterEntry{
			Job:       job,
			FailedAt:  time.Now(),
			LastError: taskErr.Error(),
		}
		fmt.Printf("[DLQ ALARM] Задача %s исчерпала лимит попыток (%d/%d) и отправлена в DLQ!\n",
			job.ID, job.RetryCount, job.MaxRetries)
		return
	}

	// Возвращаем в очередь на повтор
	q.mainQueue = append(q.mainQueue, job)
	fmt.Printf("[RETRY] Задача %s вернется на попытку %d/%d\n",
		job.ID, job.RetryCount, job.MaxRetries)
}

func (q *QueueManagerWithDLQ) ReplayFromDLQ(jobID string) error {
	q.mu.Lock()
	defer q.mu.Unlock()

	entry, ok := q.deadLetter[jobID]
	if !ok {
		return errors.New("job not found in dlq")
	}

	delete(q.deadLetter, jobID)
	replayedJob := entry.Job
	replayedJob.RetryCount = 0 // Сбрасываем счетчик ошибок
	q.mainQueue = append(q.mainQueue, replayedJob)

	fmt.Printf("[ADMIN REPLAY] Задача %s успешно возвращена из DLQ в рабочую очередь!\n", jobID)
	return nil
}

func main() {
	manager := NewQueueManager()

	poisonJob := Job{
		ID:         "job_corrupted_payload_99",
		Payload:    "INVALID_CORRUPTED_JSON",
		RetryCount: 0,
		MaxRetries: 3,
	}

	taskErr := errors.New("syntax error: invalid character 'I' looking for beginning of value")

	// Симулируем 3 последовательных падения задачи
	manager.HandleJobFailure(poisonJob, taskErr)
	manager.HandleJobFailure(poisonJob, taskErr)
	manager.HandleJobFailure(poisonJob, taskErr) // 3-е падение -> в DLQ!

	fmt.Printf("\nКоличество задач в DLQ: %d\n", len(manager.deadLetter))
	dlqEntry := manager.deadLetter["job_corrupted_payload_99"]
	fmt.Printf("Запись в DLQ: ID=%s, Ошибка='%s'\n", dlqEntry.Job.ID, dlqEntry.LastError)

	// Администратор исправил баг и перезапускает задачу
	fmt.Println("\nАдминистратор вызывает Replay API...")
	_ = manager.ReplayFromDLQ("job_corrupted_payload_99")
	fmt.Printf("Задач в DLQ после replay: %d, Задач в основной очереди: %d\n",
		len(manager.deadLetter), len(manager.mainQueue))
}
"""
            }
        ],
        "under_the_hood": "DLQ защищает конвейер очередей от блокировок (Head-of-Line Blocking). В архитектуре брокеров RabbitMQ DLQ реализуется через аргументы `x-dead-letter-exchange` и `x-dead-letter-routing-key`. В Amazon SQS — через атрибут `RedrivePolicy.deadLetterTargetArn`.",
        "pitfalls": "Забытый мониторинг DLQ: если в системе нет алертов на появление записей в DLQ, 'ядовитые' задачи будут годами тихо копиться в DLQ без внимания разработчиков. На размер DLQ обязательно вешают алерт `dlq_messages_count > 0` в Slack/Telegram.",
        "bigtech_interview": "'Как организовать авто-архивацию DLQ при миллионных потоках сообщений?' Ответ: Задачи из DLQ после определенного срока (например, 14 дней) экспортируются в холодное хранилище (Amazon S3 / ClickHouse) для последующего пост-мортем анализа, а оперативная память брокера очищается."
    },
    {
        "num": 12,
        "title": "Версионирование схемы полезной нагрузки задач",
        "task": "Разработайте строгую систему версионирования схемы полезной нагрузки фоновых задач (Payload Schema Evolution). Смоделируйте задачу генерации отчета: версия v1 содержала поле UserID int, версия v2 была расширена структурой UserUUID string и Format string. Реализуйте диспетчер, который валидирует поле schema_version, автоматически преобразует устаревший payload v1 к формату v2 (Upcasting на лету) и передает актуализированную структуру в бизнес-воркер.",
        "theory": "В непрерывном процессе развертывания (Continuous Deployment / Rolling Updates) в кластере одновременно работают поды старой версии v1.4 и новой версии v1.5.\n\nПроблема несовместимости очередей:\n1. Новая версия сервиса ставит в очередь задачу с новой схемой полей.\n2. Воркер на поде старой версии вычитывает эту задачу и падает при десериализации (неизвестные поля, изменение типов).\n\nПравила эволюции схем задач:\n- Каждая задача содержит поле метаданных: `schema_version int`.\n- **Обратная совместимость**: Воркер обязан уметь обрабатывать задачи старых версий (v1, v2) либо применять цепочку миграций (Upcasters).\n- **Неизменяемость типов**: Нельзя менять тип существующего поля (например, int -> string). Создается новое поле, либо инкрементируется `schema_version`.",
        "step_by_step": "1. Объявите структуры полезной нагрузки `ReportPayloadV1` и `ReportPayloadV2`.\n2. Спроектируйте общий конверт `VersionedJobEnvelope` с полем `SchemaVersion`.\n3. Реализуйте интерфейс `PayloadUpcaster`, конвертирующий v1 в v2.\n4. Напишите воркер, который принимает задачу, при необходимости производит upcasting и исполняет бизнес-логику.\n5. Продемонстрируйте корректную обработку задач версий v1 и v2.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"encoding/json"
	"fmt"
)

type VersionedEnvelope struct {
	JobID         string          `json:"job_id"`
	SchemaVersion int             `json:"schema_version"`
	RawPayload    json.RawMessage `json:"payload"`
}

type ReportPayloadV1 struct {
	UserID int `json:"user_id"`
}

type ReportPayloadV2 struct {
	UserUUID string `json:"user_uuid"`
	Format   string `json:"format"` // "pdf", "csv", "xlsx"
}

func UpcastReportV1ToV2(raw []byte) (*ReportPayloadV2, error) {
	var v1 ReportPayloadV1
	if err := json.Unmarshal(raw, &v1); err != nil {
		return nil, err
	}

	// Бизнес-логика конвертации устаревших данных v1 в v2
	return &ReportPayloadV2{
		UserUUID: fmt.Sprintf("legacy-usr-%06d", v1.UserID),
		Format:   "pdf", // Значение по умолчанию для старых задач
	}, nil
}

func ProcessReportJob(env VersionedEnvelope) error {
	var finalPayload *ReportPayloadV2

	switch env.SchemaVersion {
	case 1:
		fmt.Printf("[Upcaster] Задача %s имеет устаревшую схему v1. Выполняем Upcast до v2...\n", env.JobID)
		upcasted, err := UpcastReportV1ToV2(env.RawPayload)
		if err != nil {
			return err
		}
		finalPayload = upcasted

	case 2:
		var v2 ReportPayloadV2
		if err := json.Unmarshal(env.RawPayload, &v2); err != nil {
			return err
		}
		finalPayload = &v2

	default:
		return fmt.Errorf("unsupported schema version: %d", env.SchemaVersion)
	}

	// Единый бизнес-обработчик всегда работает со свежей структурой v2!
	fmt.Printf("   -> Генерация отчета для %s в формате [%s] успешно завершена!\n",
		finalPayload.UserUUID, finalPayload.Format)
	return nil
}

func main() {
	// Задача 1: Создана старой версией сервиса (v1)
	rawV1, _ := json.Marshal(ReportPayloadV1{UserID: 42})
	jobV1 := VersionedEnvelope{
		JobID:         "job_legacy_001",
		SchemaVersion: 1,
		RawPayload:    rawV1,
	}

	// Задача 2: Создана новой версией сервиса (v2)
	rawV2, _ := json.Marshal(ReportPayloadV2{UserUUID: "uuid-99-staff-lead", Format: "xlsx"})
	jobV2 := VersionedEnvelope{
		JobID:         "job_modern_002",
		SchemaVersion: 2,
		RawPayload:    rawV2,
	}

	fmt.Println("1. Обработка старой задачи v1:")
	_ = ProcessReportJob(jobV1)

	fmt.Println("\n2. Обработка современной задачи v2:")
	_ = ProcessReportJob(jobV2)
}
"""
            }
        ],
        "under_the_hood": "Применение паттерна Upcasting изолирует бизнес-обработчики от исторического мусора. Воркер всегда принимает целевую DTO-структуру текущей версии, а слой десериализации трансформирует входящий JSON с помощью промежуточных адаптеров.",
        "pitfalls": "Удаление старых версий обработчиков: если удалить поддержку схемы v1 через неделю после релиза, а в очереди или DLQ зависла старая отложенная задача, при ее вычитке произойдет фатальный сбой. Поддержку версий держат минимум 2–3 релизных цикла.",
        "bigtech_interview": "'Как Protobuf решает проблему версионирования полезной нагрузки задач?' Ответ: Protobuf решает версионирование на уровне бинарного протокола: поля нумеруются тегами, новые поля игнорируются старыми воркерами, а отсутствующие поля заполняются значениями по умолчанию без паники десериализации."
    },
    {
        "num": 13,
        "title": "Идемпотентность исполнения задач и дедупликация",
        "task": "Реализуйте надежный механизм идемпотентного выполнения фоновых задач с защитой от дублирования (Task Deduplication). Спроектируйте дедупликатор на базе ключей идемпотентности (Dedup Key). При попытке постановки дублирующей задачи с тем же ключом в течение окна дедупликации (Deduplication Window, например 10 минут) брокер не должен создавать вторую задачу. Если же дубликат все же поступил на исполнение, воркер обязан проверить таблицу выполненных операций и вернуть успешный статус без повторного выполнения действия.",
        "theory": "В распределенных системах большинство очередей задач гарантируют семантику доставки **At-Least-Once** (как минимум один раз). Это означает, что из-за сетевых ретраев, сбоев ACK или перезапуска нод одна и та же задача может прийти на исполнение дважды или трижды.\n\nЕсли задача 'списать 10 000 рублей со счета' выполнится трижды, клиент потеряет деньги, а бизнес получит судебный иск. Следовательно, обработчик задачи ОБЯЗАН быть идемпотентным: $f(x) = f(f(x))$.\n\nДвухуровневая защита от дубликатов:\n1. **Дедупликация на входе (Enqueue Dedup)**: Хэш от аргументов `dedup_key = hash('transfer', sender, receiver, amount)`. Брокер сохраняет ключ в Redis с `SET key 1 NX EX 600`. Повторные вызовы в течение 10 минут отсекаются.\n2. **Идемпотентность в БД (Execution Idempotency)**: В таблице транзакций базы данных поле `idempotency_key` имеет ограничение `UNIQUE`. При повторном исполнении SQL-запрос `INSERT ... ON CONFLICT DO NOTHING` не делает повторной мутации.",
        "step_by_step": "1. Спроектируйте структуру `IdempotentTask` с полем `DedupKey`.\n2. Реализуйте интерфейс `DedupStore` с методом атомарной резервации ключа `ReserveKey(key, ttl)`.\n3. В методе постановки проверяйте дедупликацию.\n4. На стороне воркера проверьте фиксацию результата в таблице завершенных операций.\n5. Запустите параллельную отправку 5 одинаковых задач и покажите, что выполнилась ровно одна.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

var ErrDuplicateTask = errors.New("dedup: task with this key is already queued or processed")

type IdempotentJob struct {
	ID       string
	DedupKey string
	Action   string
	Amount   int
}

type IdempotencyManager struct {
	mu           sync.Mutex
	dedupKeys    map[string]time.Time
	completedDB  map[string]bool // Имитация UNIQUE индекса в PostgreSQL
	actionCount  int64
}

func NewIdempotencyManager() *IdempotencyManager {
	return &IdempotencyManager{
		dedupKeys:   make(map[string]time.Time),
		completedDB: make(map[string]bool),
	}
}

func GenerateDedupKey(action string, entityID string, amount int) string {
	raw := fmt.Sprintf("%s:%s:%d", action, entityID, amount)
	h := sha256.Sum256([]byte(raw))
	return hex.EncodeToString(h[:16])
}

// TryEnqueue с защитой от дублирования на входе
func (m *IdempotencyManager) TryEnqueue(job IdempotentJob, window time.Duration) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	now := time.Now()
	if exp, ok := m.dedupKeys[job.DedupKey]; ok && now.Before(exp) {
		return ErrDuplicateTask // Отсекаем дубликат на входе!
	}

	m.dedupKeys[job.DedupKey] = now.Add(window)
	return nil
}

// ExecuteWithIdempotency безопасное исполнение воркером
func (m *IdempotencyManager) ExecuteWithIdempotency(job IdempotentJob) string {
	m.mu.Lock()
	defer m.mu.Unlock()

	// Проверяем таблицу завершенных операций в БД (Execution Idempotency)
	if m.completedDB[job.DedupKey] {
		return "ALREADY_PROCESSED_SKIPPED"
	}

	// Реальное выполнение бизнес-операции (списание средств)
	atomic.AddInt64(&m.actionCount, 1)
	m.completedDB[job.DedupKey] = true // Фиксируем в БД атомарно

	return "SUCCESS_EXECUTED"
}

func main() {
	mgr := NewIdempotencyManager()

	key := GenerateDedupKey("transfer_money", "user_acc_505", 2500)
	job := IdempotentJob{
		ID:       "task_1",
		DedupKey: key,
		Action:   "transfer_money",
		Amount:   2500,
	}

	fmt.Println("1. Первая попытка постановки задачи в очередь...")
	err := mgr.TryEnqueue(job, 5*time.Minute)
	fmt.Printf("   Результат постановки: err=%v\n", err)

	fmt.Println("\n2. Вторая попытка постановки той же самой задачи (сетевой дубликат)...")
	errDuplicate := mgr.TryEnqueue(job, 5*time.Minute)
	fmt.Printf("   Результат постановки дубликата: err=%v (УСПЕШНО ОТСЕЧЕН!)\n", errDuplicate)

	fmt.Println("\n3. Имитация исполнения воркером (первый запуск)...")
	res1 := mgr.ExecuteWithIdempotency(job)
	fmt.Printf("   Исполнение 1: %s\n", res1)

	fmt.Println("\n4. Имитация повторного ошибочного прилета задачи воркеру (At-Least-Once)...")
	res2 := mgr.ExecuteWithIdempotency(job)
	fmt.Printf("   Исполнение 2: %s (Идемпотентность сработала, баланс не списан повторно!)\n", res2)

	fmt.Printf("\nИтого реальных списаний: %d (ожидается ровно 1!)\n", mgr.actionCount)
}
"""
            }
        ],
        "under_the_hood": "Дедупликация на уровне базы данных опирается на уникальные индексы B-Tree. При попытке повторной вставки одинакового `idempotency_key` СУБД возвращает ошибку `unique_violation` (код 23505 в PostgreSQL), которая перехватывается воркером и интерпретируется как успешное завершение операции без повторного выполнения полезного действия.",
        "pitfalls": "Слишком короткое окно дедупликации: если окно дедупликации составляет 30 секунд, а сетевой ретрай пришел через 35 секунд, дубликат проскочит фильтр на входе. Окно дедупликации должно быть больше максимального времени жизни задачи (обычно от 10 минут до 24 часов).",
        "bigtech_interview": "'Как сгенерировать правильный ключ идемпотентности на клиенте?' Ответ: Клиент генерирует криптографический UUIDv4 или хэш от параметров бизнес-запроса (ID заказа + сумма + таймстамп действия) и передает его в HTTP-заголовке `Idempotency-Key`."
    },
    {
        "num": 14,
        "title": "Прерывание задач через Context и Graceful Abortion",
        "task": "Реализуйте систему отмены и прерывания длительных фоновых задач на Go с использованием context.Context и распределенного сигнала аборта. Пользователь в интерфейсе нажимает кнопку 'Отменить экспорт данных'. Сервис публикует сигнал отмены (в Redis или канал координатора). Воркер, выполняющий генерацию многогигабайтного файла, периодически проверяет ctx.Err(), прерывает цикл обработки, выполняет очистку временных файлов на диске (cleanup) и переводит задачу в статус 'canceled'.",
        "theory": "Длительные фоновые задачи (обработка видео, обучение ML-моделей, тяжелые аналитические выгрузки) могут выполняться от нескольких минут до нескольких часов. Если пользователь закрыл задачу или понял, что ошибся в фильтрах, продолжение вычислений бесполезно сжигает дорогостоящие ресурсы CPU/памяти сервера.\n\nПаттерн Graceful Abortion:\n1. При старте воркер создает `ctx, cancel := context.WithCancel(parentCtx)`.\n2. Функция `cancel` связывается с ID задачи в реестре активных воркеров: `activeTasks[taskID] = cancel`.\n3. При поступлении команды аборта (`AbortTask(id)`) сервис вызывает сохраненную функцию `cancel()`.\n4. Горутина-воркер внутри длительного цикла периодически опрашивает `ctx.Done()`:\n```go\nselect {\ncase <-ctx.Done():\n    cleanupTempFiles()\n    return ctx.Err()\ndefault:\n    // Продолжаем обработку следующего чанка данных\n}\n```\n5. Задача фиксируется в статусе `canceled` без зависания процесса.",
        "step_by_step": "1. Спроектируйте реестр активных задач `TaskManager` с картой функций отмены `map[string]context.CancelFunc`.\n2. Реализуйте тяжелый воркер, обрабатывающий 100 чанков с задержкой.\n3. В цикле чанков добавьте проверку `select <-ctx.Done()` с удалением временных файлов в блоке defer/cleanup.\n4. Напишите метод `AbortTask(id string)`.\n5. Продемонстрируйте прерывание задачи на 30% прогресса с освобождением ресурсов.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

type CancellationRegistry struct {
	mu          sync.Mutex
	cancels     map[string]context.CancelFunc
	taskStatus  map[string]string
	cleanedDirs []string
}

func NewCancellationRegistry() *CancellationRegistry {
	return &CancellationRegistry{
		cancels:    make(map[string]context.CancelFunc),
		taskStatus: make(map[string]string),
	}
}

func (r *CancellationRegistry) Register(taskID string, cancel context.CancelFunc) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.cancels[taskID] = cancel
	r.taskStatus[taskID] = "running"
}

func (r *CancellationRegistry) Abort(taskID string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	cancel, ok := r.cancels[taskID]
	if !ok {
		return errors.New("task not active or already finished")
	}

	cancel() // Отменяем контекст горутины
	delete(r.cancels, taskID)
	r.taskStatus[taskID] = "canceled"
	fmt.Printf("[ABORT] Отправлен сигнал отмены для задачи %s!\n", taskID)
	return nil
}

func (r *CancellationRegistry) ExecuteHeavyExport(ctx context.Context, taskID string) error {
	tempFolder := fmt.Sprintf("/tmp/export_workspace_%s", taskID)

	// Гарантированная очистка ресурсов при любом исходе
	defer func() {
		r.mu.Lock()
		r.cleanedDirs = append(r.cleanedDirs, tempFolder)
		r.mu.Unlock()
		fmt.Printf("   [CLEANUP] Временная папка '%s' удалена с диска.\n", tempFolder)
	}()

	totalChunks := 10
	for chunk := 1; chunk <= totalChunks; chunk++ {
		// Проверка отмены перед каждым квантом работы
		select {
		case <-ctx.Done():
			fmt.Printf("   [WORKER] Задача %s обнаружила отмену на шаге %d/%d: %v\n",
				taskID, chunk, totalChunks, ctx.Err())
			return ctx.Err()
		default:
			// Имитация полезной работы по генерации чанка отчета
			time.Sleep(50 * time.Millisecond)
			fmt.Printf("   [WORKER] Задача %s: чанк %d/%d сформирован...\n", taskID, chunk, totalChunks)
		}
	}

	r.mu.Lock()
	r.taskStatus[taskID] = "completed"
	r.mu.Unlock()
	return nil
}

func main() {
	registry := NewCancellationRegistry()
	taskID := "export_csv_huge_table_01"

	ctx, cancel := context.WithCancel(context.Background())
	registry.Register(taskID, cancel)

	var wg sync.WaitGroup
	wg.Add(1)

	// Запускаем воркер в фоне
	go func() {
		defer wg.Done()
		err := registry.ExecuteHeavyExport(ctx, taskID)
		if err != nil {
			fmt.Printf("Задача завершилась с ошибкой: %v\n", err)
		}
	}()

	// Пользователь ждет 120 мс и нажимает "Отменить"
	time.Sleep(120 * time.Millisecond)
	_ = registry.Abort(taskID)

	wg.Wait()

	registry.mu.Lock()
	fmt.Printf("\nФинальный статус задачи: %s\n", registry.taskStatus[taskID])
	fmt.Printf("Очищено временных директорий: %v\n", registry.cleanedDirs)
	registry.mu.Unlock()
}
"""
            }
        ],
        "under_the_hood": "Метод `ctx.Done()` возвращает канал `<-chan struct{}`. Вызов `cancel()` закрывает этот канал с помощью рантайм-функции `closechan()`. В инструкции `select` закрытый канал мгновенно становится готовым к чтению (возвращает нулевое значение), выводя горутину из ожидания за единицы наносекунд.",
        "pitfalls": "Отсутствие проверок ctx.Done() внутри блокирующих операций: если горутина зависла на `io.ReadAll(socket)` или длинном SQL-запросе без передачи контекста в драйвер, вызов `cancel()` не прервет выполнение, пока не истечет системный TCP-таймаут.",
        "bigtech_interview": "'Как передать сигнал отмены задачи между разными серверами в кластере?' Ответ: Через Redis Pub/Sub на канал `tasks:abort` или распределенный ключ с коротким TTL. Воркер слушает канал абортов или периодически проверяет статус задачи в центральной БД."
    },
    {
        "num": 15,
        "title": "Динамическое масштабирование пула воркеров по длине очереди (Queue Lag)",
        "task": "Спроектируйте автоскейлер пула воркеров (Dynamic Autoscaling Worker Pool) на Go. Напишите фоновый монитор, который периодически замеряет глубину очереди (Queue Lag: количество задач в статусе pending). Если очередь превышает верхний порог (High Watermark, например 50 задач), монитор динамически спавнит дополнительные горутины-воркеры вплоть до MaxWorkers = 20. Когда глубина очереди опускается ниже нижнего порога (Low Watermark), избыточные простаивающие воркеры корректно завершают работу, возвращаясь к MinWorkers = 2.",
        "theory": "Статический размер пула воркеров неэффективен:\n- В периоды затишья (ночью) 50 работающих воркеров впустую удерживают соединения к БД и память.\n- В моменты пиков (утренняя рассылка, распродажа) 5 воркеров не справляются с потоком задач, и очередь растягивается на часы (Queue Lag растет лавинообразно).\n\nАвтоскейлинг по Queue Lag (аналог KEDA в Kubernetes):\n1. Монитор замеряет метрику `QueueDepth` каждые $T$ миллисекунд.\n2. **Scale Up**: Если `QueueDepth > HighWatermark` и текущее число воркеров $< MaxWorkers$, запускаются $K$ новых горутин.\n3. **Scale Down (Cool-down)**: Если `QueueDepth == 0` и воркер простаивает дольше времени `IdleTimeout`, он завершает работу через `return`, снижая число активных горутин до `MinWorkers`.",
        "step_by_step": "1. Спроектируйте структуру `DynamicWorkerPool` со счетчиками `activeWorkers`, `minWorkers`, `maxWorkers`.\n2. Реализуйте канал задач и канал сигналов остановки лишних воркеров.\n3. Напишите метод `scaleMonitor()`, отслеживающий размер `len(jobQueue)`.\n4. Смоделируйте резкий наплыв 80 задач: покажите расширение пула с 2 до 8 воркеров.\n5. Покажите автоматическое сужение пула обратно до 2 воркеров после разбора очереди.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

type DynamicWorkerPool struct {
	minWorkers    int32
	maxWorkers    int32
	activeWorkers int32
	queue         chan func()
	stopWorkerCh  chan struct{}
	wg            sync.WaitGroup
	processed     int64
}

func NewDynamicWorkerPool(min, max int32, queueCap int) *DynamicWorkerPool {
	p := &DynamicWorkerPool{
		minWorkers:   min,
		maxWorkers:   max,
		queue:        make(chan func(), queueCap),
		stopWorkerCh: make(chan struct{}),
	}

	// Запускаем минимальное число воркеров
	for i := int32(0); i < min; i++ {
		p.spawnWorker()
	}

	go p.autoScaleMonitor(100 * time.Millisecond)
	return p
}

func (p *DynamicWorkerPool) spawnWorker() {
	p.wg.Add(1)
	atomic.AddInt32(&p.activeWorkers, 1)

	go func() {
		defer func() {
			atomic.AddInt32(&p.activeWorkers, -1)
			p.wg.Done()
		}()

		for {
			select {
			case <-p.stopWorkerCh:
				return // Приказ на сокращение пула
			case job, ok := <-p.queue:
				if !ok {
					return
				}
				job()
				atomic.AddInt64(&p.processed, 1)
			}
		}
	}()
}

func (p *DynamicWorkerPool) autoScaleMonitor(interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for range ticker.C {
		lag := len(p.queue)
		current := atomic.LoadInt32(&p.activeWorkers)

		// Scale Up: если в очереди накопились задачи, а воркеров меньше максимума
		if lag > 10 && current < p.maxWorkers {
			toAdd := int32(2)
			if current+toAdd > p.maxWorkers {
				toAdd = p.maxWorkers - current
			}
			for i := int32(0); i < toAdd; i++ {
				p.spawnWorker()
			}
			fmt.Printf("[AUTOSCALER +] Очередь=%d. Пул расширен: %d -> %d воркеров!\n",
				lag, current, current+toAdd)
		}

		// Scale Down: если очередь пуста, а воркеров больше минимума
		if lag == 0 && current > p.minWorkers {
			select {
			case p.stopWorkerCh <- struct{}{}:
				fmt.Printf("[AUTOSCALER -] Очередь пуста. Пул сокращен: %d -> %d воркеров.\n",
					current, current-1)
			default:
			}
		}
	}
}

func (p *DynamicWorkerPool) Submit(j func()) {
	p.queue <- j
}

func main() {
	pool := NewDynamicWorkerPool(2, 6, 100)

	fmt.Printf("Инициализирован пул: Min=%d, Max=%d. Активно сейчас: %d\n",
		pool.minWorkers, pool.maxWorkers, pool.activeWorkers)

	// Наплыв 40 задач
	fmt.Println("\nВсплеск нагрузки: отправка 40 задач в очередь...")
	for i := 1; i <= 40; i++ {
		pool.Submit(func() {
			time.Sleep(20 * time.Millisecond)
		})
	}

	time.Sleep(300 * time.Millisecond)
	fmt.Printf("В момент пика активно воркеров: %d\n", atomic.LoadInt32(&pool.activeWorkers))

	// Ждем завершения разбора
	time.Sleep(800 * time.Millisecond)

	fmt.Printf("\nПосле разбора очереди активно воркеров: %d (плавно вернулись к Min!)\n",
		atomic.LoadInt32(&pool.activeWorkers))
	fmt.Printf("Всего успешно обработано задач: %d\n", atomic.LoadInt64(&pool.processed))
}
"""
            }
        ],
        "under_the_hood": "В Kubernetes для внешнего автомасштабирования очередей используется KEDA (Kubernetes Event-driven Autoscaling). KEDA опрашивает размер очереди в Redis/PostgreSQL через метрики и динамически масштабирует число подов (ReplicaSet) от 0 до N через Custom Metrics API.",
        "pitfalls": "Флаппинг масштабирования (Flapping / Thrashing): если увеличивать и уменьшать пул слишком часто, система потратит больше CPU на запуск и остановку горутин/подов, чем на работу. Для предотвращения флаппинга вводят окно охлаждения (Cool-down Period / ScaleDownDelay) не менее 30–60 секунд.",
        "bigtech_interview": "'По какой метрике правильнее скейлить воркеры: по утилизации CPU или по длине очереди?' Ответ: Только по длине очереди (Queue Lag / Time-in-Queue)! Воркеры, ожидающие ответов внешних API по I/O, могут потреблять всего 5% CPU, но при этом очередь задач будет катастрофически расти."
    }
]
