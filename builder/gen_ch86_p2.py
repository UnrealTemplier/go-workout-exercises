# -*- coding: utf-8 -*-
"""
Chapter 86 Part 2: Exercises 16 to 30
Scalable Distributed Schedulers and Task Queues in Go
"""

exercises = [
    {
        "num": 16,
        "title": "Распределенный Rate Limiting выполнения задач",
        "task": "Спроектируйте систему распределенного ограничения скорости (Distributed Rate Limiter) для пула фоновых воркеров на Go. Представьте, что 50 воркеров обрабатывают задачи отправки SMS через внешний шлюз телеком-провайдера с жестким квотным лимитом: не более 100 SMS в секунду на весь кластер. Реализуйте алгоритм скользящего окна (Sliding Window) или Token Bucket на базе Redis (с атомарными операциями / Lua-скриптом). Докажите, что при 1000 входящих задач воркеры строго соблюдают лимит и не получают 429 Too Many Requests от внешнего API.",
        "theory": "Фоновые воркеры могут генерировать колоссальную параллельную нагрузку. Если 100 воркеров одновременно начнут долбить внешнее API (Stripe, Twilio, OpenAI), внешний провайдер моментально заблокирует API-ключ компании за превышение Rate Limit (HTTP 429 Too Many Requests).\n\nЛокальный `golang.org/x/time/rate.Limiter` работает только внутри одного процесса Go. Для кластера из десятков нод требуется **распределенный Rate Limiter**:\n1. **Token Bucket на Redis**: В ключе хранится баланс токенов. Атомарный Lua-скрипт пополняет токены в зависимости от прошедшего времени и списывает 1 токен.\n2. **Задержка воркера (Pacing)**: Если токенов нет, воркер не роняет задачу, а засыпает на время до следующего токена либо возвращает задачу в очередь с короткой отсрочкой (Delay = 50 мс).",
        "step_by_step": "1. Спроектируйте структуру `DistributedRateLimiter` со счетчиком токенов и скоростью пополнения.\n2. Реализуйте атомарный метод `Allow() bool` или `Wait(ctx)`.\n3. Создайте 20 параллельных воркеров, разгребающих 200 задач.\n4. Замерьте фактическую скорость выполнения задач в секунду.\n5. Зафиксируйте строгое соблюдение установленной квоты без превышений.",
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

// TokenBucketLimiter эмулирует распределенный Token Bucket (аналог Redis Lua)
type TokenBucketLimiter struct {
	mu         sync.Mutex
	rate       float64   // токенов в секунду
	capacity   float64   // максимальная емкость ведра
	tokens     float64   // текущее количество токенов
	lastUpdate time.Time // момент последнего пополнения
}

func NewTokenBucketLimiter(rate, capacity float64) *TokenBucketLimiter {
	return &TokenBucketLimiter{
		rate:       rate,
		capacity:   capacity,
		tokens:     capacity,
		lastUpdate: time.Now(),
	}
}

func (l *TokenBucketLimiter) Allow() bool {
	l.mu.Lock()
	defer l.mu.Unlock()

	now := time.Now()
	elapsed := now.Sub(l.lastUpdate).Seconds()
	l.lastUpdate = now

	// Пополняем ведро токенами
	l.tokens += elapsed * l.rate
	if l.tokens > l.capacity {
		l.tokens = l.capacity
	}

	if l.tokens >= 1.0 {
		l.tokens -= 1.0
		return true // Разрешено
	}

	return false // Лимит исчерпан!
}

func main() {
	// Лимит: 50 операций в секунду, емкость всплеска (burst) = 10
	limiter := NewTokenBucketLimiter(50, 10)

	totalTasks := 120
	workerCount := 10
	taskCh := make(chan int, totalTasks)
	for i := 1; i <= totalTasks; i++ {
		taskCh <- i
	}
	close(taskCh)

	var wg sync.WaitGroup
	var completedCount int64
	start := time.Now()

	fmt.Printf("Запуск %d воркеров на %d задач с лимитом 50 rps...\n", workerCount, totalTasks)

	for w := 1; w <= workerCount; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for taskID := range taskCh {
				// Ожидаем доступности токена
				for !limiter.Allow() {
					time.Sleep(10 * time.Millisecond) // Pacing пауза
				}

				// Имитация вызова внешнего SMS-шлюза
				atomic.AddInt64(&completedCount, 1)
				_ = taskID
			}
		}(w)
	}

	wg.Wait()
	duration := time.Since(start)

	actualRPS := float64(completedCount) / duration.Seconds()
	fmt.Printf("\n=== РЕЗУЛЬТАТ РАСПРЕДЕЛЕННОГО РЕЙТ-ЛИМИТИНГА ===\n")
	fmt.Printf("Выполнено задач: %d за %v\n", completedCount, duration.Round(time.Millisecond))
	fmt.Printf("Фактическая скорость: %.1f задач/сек (целевой лимит: 50 RPS)\n", actualRPS)
}
"""
            }
        ],
        "under_the_hood": "В продакшене Token Bucket для Redis реализуется через атомарный Lua-скрипт (или модуль RedisCell). Lua выполняется на сервере Redis однопоточно, гарантируя, что 100 одновременных воркеров атомарно проверят таймстамп, пересчитают баланс токенов и спишут квоту без состояния гонки (Race Condition).",
        "pitfalls": "Активное ожидание (Busy-Waiting polling): если воркер в цикле `for !limiter.Allow()` опрашивает Redis без паузы, 50 воркеров сгенерируют 500 000 холостых сетевых запросов в секунду к Redis! Необходимо вычислять точное время сна `time.Sleep(timeToNextToken)`.",
        "bigtech_interview": "'Как организовать честный Rate Limiting, если у вас несколько разных клиентов делят одну квоту?' Ответ: Использовать составные ключи `rate:tenant:{id}` и алгоритм Leaky Bucket или Fair Queuing, выделяя каждому тенанту гарантированную долю пропускной способности."
    },
    {
        "num": 17,
        "title": "Справедливое планирование (Fair Scheduling) между тенантами",
        "task": "Решите проблему 'шумного соседа' (Noisy Neighbor) в Multi-Tenant SaaS платформе фоновых задач. Смоделируйте ситуацию: Тенант A (крупная корпорация) внезапно ставит в очередь 10 000 задач на импорт контактов, а Тенант B (стартап) ставит 2 критичные задачи авторизации. Напишите диспетчер справедливого планирования (Round-Robin Fair Scheduler): диспетчер чередует выборку задач между тенантами так, чтобы задачи Тенанта B выполнялись немедленно, а не ждали завершения всех 10 000 задач Тенанта A.",
        "theory": "В облачных SaaS-системах очередь задач разделяется между сотнями независимых клиентов (Тенантов).\n\nПроблема Noisy Neighbor:\nЕсли Тенант А запустил массовую спам-рассылку на 100 000 писем, он полностью забьет общую очередь. Обычные пользователи Тенанта Б не смогут войти в систему или получить чек, потому что их задачи встали в хвост 100-тысячной очереди.\n\nПаттерн Fair Scheduling (Справедливая очередь):\n1. Очереди физически или логически разделяются по тенантам: `queue:tenant:A`, `queue:tenant:B`.\n2. Диспетчер воркеров использует циклический обход (Round-Robin / Deficit Round Robin):\n   - Берет 1 задачу у Тенанта A.\n   - Берет 1 задачу у Тенанта B.\n   - Берет 1 задачу у Тенанта C.\n3. Если у Тенанта B всего 2 задачи, они будут выполнены за первые миллисекунды, а задачи Тенанта A займут все оставшееся свободное время пула.",
        "step_by_step": "1. Спроектируйте структуру `TenantTask` с полями ID, TenantID, Payload.\n2. Создайте структуру `FairTenantDispatcher` с мапой изолированных очередей по тенантам.\n3. Реализуйте метод циклической выборки `DequeueFair() TenantTask`.\n4. Наполните очередь: 1000 задач от Тенанта A и 5 задач от Тенанта B.\n5. Докажите, что задачи Тенанта B выполняются сразу же среди первых 10 тиков.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
)

type TenantTask struct {
	ID       string
	TenantID string
}

type FairTenantDispatcher struct {
	mu           sync.Mutex
	tenantQueues map[string][]TenantTask
	tenantOrder  []string // порядок обхода тенантов
	currentIndex int
}

func NewFairTenantDispatcher() *FairTenantDispatcher {
	return &FairTenantDispatcher{
		tenantQueues: make(map[string][]TenantTask),
		tenantOrder:  make([]string, 0),
	}
}

func (d *FairTenantDispatcher) Enqueue(task TenantTask) {
	d.mu.Lock()
	defer d.mu.Unlock()

	if _, exists := d.tenantQueues[task.TenantID]; !exists {
		d.tenantQueues[task.TenantID] = make([]TenantTask, 0)
		d.tenantOrder = append(d.tenantOrder, task.TenantID)
	}
	d.tenantQueues[task.TenantID] = append(d.tenantQueues[task.TenantID], task)
}

// DequeueFair выбирает задачи по честному циклическому алгоритму Round-Robin
func (d *FairTenantDispatcher) DequeueFair() (*TenantTask, bool) {
	d.mu.Lock()
	defer d.mu.Unlock()

	if len(d.tenantOrder) == 0 {
		return nil, false
	}

	// Делаем полный круг проверки, если у текущего тенанта кончились задачи
	checked := 0
	for checked < len(d.tenantOrder) {
		tenantID := d.tenantOrder[d.currentIndex]
		d.currentIndex = (d.currentIndex + 1) % len(d.tenantOrder)
		checked++

		queue := d.tenantQueues[tenantID]
		if len(queue) > 0 {
			task := queue[0]
			d.tenantQueues[tenantID] = queue[1:]
			return &task, true
		}
	}

	return nil, false // Все очереди пусты
}

func main() {
	dispatcher := NewFairTenantDispatcher()

	// Тенант A ставит 100 тяжелых задач
	for i := 1; i <= 100; i++ {
		dispatcher.Enqueue(TenantTask{
			ID:       fmt.Sprintf("task_A_%d", i),
			TenantID: "tenant_MEGA_CORP",
		})
	}

	// Тенант B ставит всего 3 срочные задачи
	for i := 1; i <= 3; i++ {
		dispatcher.Enqueue(TenantTask{
			ID:       fmt.Sprintf("task_B_%d", i),
			TenantID: "tenant_STARTUP_XYZ",
		})
	}

	fmt.Println("Извлечение первых 10 задач по справедливому алгоритму Round-Robin:")

	for i := 1; i <= 10; i++ {
		task, ok := dispatcher.DequeueFair()
		if !ok {
			break
		}
		fmt.Printf("Шаг %2d: Извлечена задача %-12s (Тенант: %s)\n",
			i, task.ID, task.TenantID)
	}

	fmt.Println("\nВывод: Задачи маленького тенанта B чередовались с задачами гиганта A!")
}
"""
            }
        ],
        "under_the_hood": "В ядре Linux аналогичный алгоритм называется Completely Fair Scheduler (CFS), распределяющий кванты процессорного времени между потоками через красно-черное дерево виртуального времени (vruntime). В очередях задач алгоритм Deficit Round Robin (DRR) дополнительно учитывает квант размера/веса задач каждого тенанта.",
        "pitfalls": "Утечка памяти в мапе тенантов: если за день через систему проходят 100 000 разовых тенантов, пустые слайсы в мапе `tenantQueues` будут занимать память. При опустошении очереди тенанта его идентификатор необходимо удалять из списка обхода.",
        "bigtech_interview": "'Как реализовать Fair Queuing в PostgreSQL через SKIP LOCKED?' Ответ: Добавить в SQL-запрос выборки условие партиционирования по окну: `ROW_NUMBER() OVER (PARTITION BY tenant_id ORDER BY id ASC) <= 1`. СУБД выберет ровно по одной первой задаче от каждого уникального тенанта за один запрос!"
    },
    {
        "num": 18,
        "title": "Пакетная обработка задач (Batching / Bulk Processing)",
        "task": "Реализуйте воркер пакетной обработки задач (Batching Worker) на Go. Обработка каждой задачи по отдельности неэффективна (например, одиночные HTTP-запросы или INSERT в аналитическую СУБД ClickHouse). Напишите воркер, который накапливает задачи в буфер и сбрасывает их пакетно при наступлении любого из двух событий: 1) Накопился батч из MaxBatchSize = 50 задач; 2) Истек таймаут MaxFlushInterval = 200 мс. Продемонстрируйте многократное сокращение сетевых накладных расходов.",
        "theory": "Паттерн Batching (пакетирование) — фундаментальный прием оптимизации HighLoad-систем:\n- Одиночная вставка в ClickHouse или Elasticsearch 10 000 строк по отдельности положит СУБД из-за создания 10 000 партий файлов (parts) на диске.\n- Пакетная вставка одной пачкой `INSERT ... VALUES (...), (...)` из 10 000 строк выполнится за 50 миллисекунд в рамках одной дисковой операции.\n\nМеханика буфера со сбросом по двойному условию (Size & Time):\nГорутина-аккумулятор слушает входной канал и тикер. Если задач много, они быстро наполняют срез до `MaxBatchSize` и мгновенно сбрасываются. Если задач мало, тикер по таймауту гарантирует, что единичные задачи не зависнут в памяти надолго.",
        "step_by_step": "1. Спроектируйте структуру `BatchWorker` с каналом задач, размером батча и таймером сброса.\n2. Реализуйте цикл накопления через `select`: кейс получения задачи и кейс тикера `ticker.C`.\n3. При срабатывании любого условия вызывайте функцию `flushBatch([]Task)`.\n4. Напишите Graceful Shutdown с гарантированным сбросом остатка буфера.\n5. Запустите 120 задач и покажите, что они обработаны компактными батчами.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
	"time"
)

type MetricEvent struct {
	DeviceID  string
	CPUUsage  float64
	Timestamp time.Time
}

type BatchWorker struct {
	batchSize     int
	flushInterval time.Duration
	inQueue       chan MetricEvent
	quit          chan struct{}
	wg            sync.WaitGroup
	batchesSaved  int
	totalSaved    int
}

func NewBatchWorker(batchSize int, interval time.Duration, queueCap int) *BatchWorker {
	return &BatchWorker{
		batchSize:     batchSize,
		flushInterval: interval,
		inQueue:       make(chan MetricEvent, queueCap),
		quit:          make(chan struct{}),
	}
}

func (w *BatchWorker) Start() {
	w.wg.Add(1)
	go w.eventLoop()
}

func (w *BatchWorker) Submit(e MetricEvent) {
	w.inQueue <- e
}

func (w *BatchWorker) eventLoop() {
	defer w.wg.Done()
	ticker := time.NewTicker(w.flushInterval)
	defer ticker.Stop()

	buffer := make([]MetricEvent, 0, w.batchSize)

	flush := func() {
		if len(buffer) == 0 {
			return
		}
		// Имитация пакетной вставки в ClickHouse (Bulk Insert)
		w.batchesSaved++
		w.totalSaved += len(buffer)
		fmt.Printf("   [BULK FLUSH #%d] Пакетная запись %d метрик в базу данных!\n",
			w.batchesSaved, len(buffer))
		buffer = buffer[:0] // Очищаем буфер с сохранением аллоцированной памяти
	}

	for {
		select {
		case <-w.quit:
			flush() // Сбрасываем хвост при завершении
			return

		case event, ok := <-w.inQueue:
			if !ok {
				flush()
				return
			}
			buffer = append(buffer, event)
			if len(buffer) >= w.batchSize {
				flush() // Сброс по превышению размера батча
			}

		case <-ticker.C:
			flush() // Сброс по таймауту
		}
	}
}

func (w *BatchWorker) Stop() {
	close(w.inQueue)
	w.wg.Wait()
}

func main() {
	// Батч = 50 элементов, таймаут = 150мс
	worker := NewBatchWorker(50, 150*time.Millisecond, 200)
	worker.Start()

	fmt.Println("1. Отправляем 110 метрик подряд...")
	for i := 1; i <= 110; i++ {
		worker.Submit(MetricEvent{
			DeviceID:  fmt.Sprintf("node_%d", i),
			CPUUsage:  42.5,
			Timestamp: time.Now(),
		})
	}

	time.Sleep(50 * time.Millisecond) // Даем воркеру обработать размерные батчи

	fmt.Println("\n2. Отправляем еще 15 метрик и ждем сброса по таймауту 150мс...")
	for i := 1; i <= 15; i++ {
		worker.Submit(MetricEvent{
			DeviceID:  fmt.Sprintf("node_delayed_%d", i),
			CPUUsage:  10.0,
			Timestamp: time.Now(),
		})
	}

	time.Sleep(200 * time.Millisecond) // Ждем тикера

	worker.Stop()

	fmt.Printf("\n=== ИТОГИ ПАКЕТИРОВАНИЯ ===\n")
	fmt.Printf("Всего метрик сохранено: %d\n", worker.totalSaved)
	fmt.Printf("Всего обращений к диску/БД: %d (вместо 125 одиночных запросов!)\n", worker.batchesSaved)
}
"""
            }
        ],
        "under_the_hood": "Переиспользование слайса через `buffer = buffer[:0]` сохраняет аллоцированную емкость (capacity) базового массива в памяти. Рантайму Go не требуется снова вызывать аллокатор `mallocgc` при каждом новом батче, исключая нагрузку на GC.",
        "pitfalls": "Сбой в середине батча: если из 100 записей одна содержит невалидные данные и вся транзакция падает, весь батч может быть отвергнут. В продакшене при ошибке батча его делят пополам (двоичный поиск ядовитой записи) либо сохраняют отвергнутые элементы в DLQ.",
        "bigtech_interview": "'Как настроить размер батча и таймаут для ClickHouse?' Ответ: ClickHouse рекомендует пакеты от 10 000 до 100 000 строк либо сброс каждые 1–2 секунды. Слишком мелкие батчи перегружают дерево слияния (MergeTree parts), вызывая ошибку 'Too many parts in all data in table'."
    },
    {
        "num": 19,
        "title": "Graceful Shutdown очереди: безопасный слив задач",
        "task": "Спроектируйте процедуру корректного завершения работы (Graceful Shutdown) для кластерного сервиса очередей при получении сигналов ОС SIGINT / SIGTERM. Сервис должен: 1) Мгновенно прекратить выборку новых задач из брокера; 2) Дать работающим горутинам до 5 секунд на завершение текущих задач; 3) Если задача не укладывается в таймаут — безопасно вернуть ее в очередь (NACK / Requeue); 4) Закрыть сетевые соединения к БД и Redis.",
        "theory": "В Kubernetes при деплое нового релиза или автоскейлинге (Scale Down) подам отправляется сигнал `SIGTERM`. По умолчанию дается `terminationGracePeriodSeconds` (обычно 30 секунд), после чего ядро шлет `SIGKILL`.\n\nЕсли сервис просто вызовет `os.Exit(0)`:\n- Задачи, выполнявшиеся прямо сейчас, оборвутся на полуслове (например, деньги списаны, а товар не выдан).\n- Блокировки в БД останутся висеть до тайм-аута.\n\nКанонический алгоритм Graceful Shutdown:\n1. Перехват сигнала через `signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)`.\n2. Закрытие входного канала или остановка опрашивающего поллера (`stopPolling()`).\n3. Создание контекста с жестким тайм-лимитом завершения: `ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)`.\n4. Ожидание завершения активных воркеров через `sync.WaitGroup`.\n5. Если таймаут истек, а воркеры еще работают — логирование аварийного сброса и возврат задач в статус `pending`.",
        "step_by_step": "1. Спроектируйте `GracefulWorkerManager` со счетчиком активных задач `activeWg`.\n2. Реализуйте метод `Shutdown(ctx context.Context)`.\n3. Запустите 3 долгоживущие задачи (по 200 мс) и 1 зависшую задачу (по 10 сек).\n4. Инициируйте остановку с таймаутом 500 мс.\n5. Покажите корректное завершение быстрых задач и безопасный откат зависшей.",
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

type WorkerEngine struct {
	stopPoll   chan struct{}
	activeWg   sync.WaitGroup
	isStopping atomic.Bool
	completed  int64
	interrupted int64
}

func NewWorkerEngine() *WorkerEngine {
	return &WorkerEngine{
		stopPoll: make(chan struct{}),
	}
}

func (e *WorkerEngine) ProcessJob(id string, workDuration time.Duration) {
	e.activeWg.Add(1)
	defer e.activeWg.Done()

	ctx, cancel := context.WithTimeout(context.Background(), workDuration)
	defer cancel()

	select {
	case <-time.After(workDuration):
		atomic.AddInt64(&e.completed, 1)
		fmt.Printf("   [Job %s] Успешно завершена!\n", id)
	case <-e.stopPoll:
		// Получен сигнал экстренной остановки сервиса
		atomic.AddInt64(&e.interrupted, 1)
		fmt.Printf("   [Job %s] Прервана по таймауту Graceful Shutdown! Безопасный возврат в очередь (NACK).\n", id)
	case <-ctx.Done():
	}
}

func (e *WorkerEngine) Shutdown(graceTimeout time.Duration) {
	fmt.Println("\n[SHUTDOWN] Получен сигнал SIGTERM. Начинаем Graceful Shutdown...")
	e.isStopping.Store(true)

	// 1. Канал для отслеживания завершения всех активных задач
	doneCh := make(chan struct{})
	go func() {
		e.activeWg.Wait()
		close(doneCh)
	}()

	// 2. Ждем завершения либо истечения жесткого лимита времени
	select {
	case <-doneCh:
		fmt.Println("[SHUTDOWN] Все активные задачи завершились штатно! Чистый выход.")
	case <-time.After(graceTimeout):
		fmt.Println("[SHUTDOWN] Таймаут ожидания истек! Посылаем сигнал прерывания оставшимся задачам...")
		close(e.stopPoll) // Прерываем зависшие задачи
		e.activeWg.Wait() // Дожидаемся выхода из горутин
		fmt.Println("[SHUTDOWN] Зависшие задачи освобождены и возвращены в брокер.")
	}
}

func main() {
	engine := NewWorkerEngine()

	// Запускаем 2 быстрые задачи (уложатся в 100мс)
	go engine.ProcessJob("quick_task_1", 100*time.Millisecond)
	go engine.ProcessJob("quick_task_2", 150*time.Millisecond)

	// Запускаем 1 тяжелую зависшую задачу (требует 5 секунд)
	go engine.ProcessJob("long_hanging_task_3", 5*time.Second)

	time.Sleep(50 * time.Millisecond)

	// Инициируем остановку с лимитом времени 300 мс
	engine.Shutdown(300 * time.Millisecond)

	fmt.Printf("\nИтог: Успешно завершено: %d, Корректно эвакуировано: %d\n",
		engine.completed, engine.interrupted)
}
"""
            }
        ],
        "under_the_hood": "При Graceful Shutdown Kubernetes сначала удаляет под из сервисных эндпоинтов (трафик больше не идет), затем посылает SIGTERM. Если процесс завершается за время меньше terminationGracePeriodSeconds, контейнер останавливается без единой ошибки для клиентов.",
        "pitfalls": "Зависание на `wg.Wait()`: если хотя бы одна горутина-воркер зависла в системном вызове ввода-вывода без проверки контекста, приложение не выйдет из `wg.Wait()`, и Kubernetes через 30 секунд убьет процесс жестким `SIGKILL`, вызвав сбой.",
        "bigtech_interview": "'Как в Go обрабатывать несколько сигналов SIGINT подряд (например, пользователь дважды нажал Ctrl+C)?' Ответ: Первый Ctrl+C запускает Graceful Shutdown. Второй Ctrl+C перехватывается отдельным кейсом и вызывает немедленный форсированный `os.Exit(1)`."
    },
    {
        "num": 20,
        "title": "Мониторинг и метрики: Prometheus гистограммы времени обработки",
        "task": "Оснастите систему очередей задач полным набором метрик Prometheus. Реализуйте экспорт: 1) queue_depth{queue='default'} (Gauge) — глубина очереди; 2) tasks_total{type='report', status='success|failure'} (Counter) — количество выполненных задач; 3) task_duration_seconds (Histogram) — гистограмма длительности выполнения; 4) queue_latency_seconds (Histogram) — время ожидания задачи в очереди от момента Enqueue до взятия воркером.",
        "theory": "Эксплуатация распределенных очередей без детальных метрик неизбежно приводит к слепым инцидентам (Silent Failures), когда задачи перестают разбираться, а разработчики узнают об этом только от возмущенных клиентов через сутки.\n\nКлючевой показатель здоровья очередей — **Queue Latency (Время нахождения в очереди)**:\nЭто разница между моментом постановки `created_at` и моментом фактического взятия задачи в работу `started_at`:\n$Latency = StartedAt - CreatedAt$.\nЕсли Queue Latency начинает расти с миллисекунд до десятков секунд, это прямой сигнал о нехватке воркеров (Under-provisioning) задолго до переполнения памяти брокера.",
        "step_by_step": "1. Спроектируйте структуру `QueueMetrics` с симуляцией метрик Prometheus.\n2. Реализуйте бакеты гистограммы длительности: 10мс, 50мс, 250мс, 1с, 5с.\n3. Замеряйте задержку нахождения задачи в очереди.\n4. Смоделируйте выполнение 50 задач с разной длительностью.\n5. Выведите сводный отчет по бакетам гистограммы.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
	"time"
)

type MetricTask struct {
	ID        string
	Type      string
	CreatedAt time.Time
}

type PrometheusQueueMetrics struct {
	mu           sync.Mutex
	queueDepth   int64
	successTotal int64
	failureTotal int64
	// Бакеты гистограммы выполнения (в миллисекундах: <=20, <=100, <=500, >500)
	durationBuckets map[string]int
	// Бакеты задержки в очереди (Queue Latency)
	latencyBuckets  map[string]int
}

func NewQueueMetrics() *PrometheusQueueMetrics {
	return &PrometheusQueueMetrics{
		durationBuckets: map[string]int{"<=20ms": 0, "<=100ms": 0, "<=500ms": 0, "+Inf": 0},
		latencyBuckets:  map[string]int{"<=10ms": 0, "<=50ms": 0, "<=200ms": 0, "+Inf": 0},
	}
}

func (m *PrometheusQueueMetrics) RecordExecution(t MetricTask, duration time.Duration, success bool) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if success {
		m.successTotal++
	} else {
		m.failureTotal++
	}

	// 1. Замеряем время нахождения в очереди
	queueLatency := time.Since(t.CreatedAt) - duration
	if queueLatency <= 10*time.Millisecond {
		m.latencyBuckets["<=10ms"]++
	} else if queueLatency <= 50*time.Millisecond {
		m.latencyBuckets["<=50ms"]++
	} else if queueLatency <= 200*time.Millisecond {
		m.latencyBuckets["<=200ms"]++
	} else {
		m.latencyBuckets["+Inf"]++
	}

	// 2. Замеряем время работы самого воркера
	dMs := duration.Milliseconds()
	if dMs <= 20 {
		m.durationBuckets["<=20ms"]++
	} else if dMs <= 100 {
		m.durationBuckets["<=100ms"]++
	} else if dMs <= 500 {
		m.durationBuckets["<=500ms"]++
	} else {
		m.durationBuckets["+Inf"]++
	}
}

func main() {
	metrics := NewQueueMetrics()

	fmt.Println("Имитация сбора метрик 30 задач с различной нагрузкой...")

	for i := 1; i <= 30; i++ {
		createdAt := time.Now()

		// Задача некоторое время ждет в очереди (Queue Latency)
		waitDuration := time.Duration(i*3) * time.Millisecond
		time.Sleep(waitDuration)

		// Воркер выполняет задачу
		startExec := time.Now()
		execDuration := time.Duration(15+i*10) * time.Millisecond

		task := MetricTask{ID: fmt.Sprintf("task_%d", i), Type: "billing", CreatedAt: createdAt}
		metrics.RecordExecution(task, execDuration, i%10 != 0)
		_ = startExec
	}

	metrics.mu.Lock()
	fmt.Printf("\n=== МЕТРИКИ PROMETHEUS ДЛЯ ОЧЕРЕДЕЙ ===\n")
	fmt.Printf("tasks_processed_total{status='success'}: %d\n", metrics.successTotal)
	fmt.Printf("tasks_processed_total{status='failure'}: %d\n", metrics.failureTotal)

	fmt.Printf("\ntask_duration_seconds_bucket (Время выполнения):\n")
	for b, count := range metrics.durationBuckets {
		fmt.Printf("  le='%s': %d\n", b, count)
	}

	fmt.Printf("\ntask_queue_latency_seconds_bucket (Задержка в очереди):\n")
	for b, count := range metrics.latencyBuckets {
		fmt.Printf("  le='%s': %d\n", b, count)
	}
	metrics.mu.Unlock()
}
"""
            }
        ],
        "under_the_hood": "Гистограммы Prometheus используют фиксированные диапазоны бакетов (Buckets). При расчете p99 перцентиля в Grafana функция `histogram_quantile(0.99, rate(task_duration_seconds_bucket[5m]))` интерполирует значение между границами бакетов, позволяя выявлять аномальные задержки отдельных задач без хранения миллионов сырых таймстампов.",
        "pitfalls": "Кардинальность лейблов (High Cardinality): добавление уникального Task ID или User ID в лейблы метрики Prometheus (`task_duration{id='100293'}`) приведет к взрывному росту временных рядов (Time Series explosion) и падению сервера Prometheus по OOM.",
        "bigtech_interview": "'На какую метрику настраивать алерт дежурному инженеру в первую очередь?' Ответ: На рост `queue_latency_seconds` (время ожидания задачи) и рост счетчика `tasks_failed_total` в DLQ. Если задачи ждут исполнения дольше допустимого SLA, дежурный должен немедленно масштабировать воркеры."
    },
    {
        "num": 21,
        "title": "Глубокое погружение в библиотеку Asynq на Go",
        "task": "Изучите внутреннюю архитектуру библиотеки hibiken/asynq — популярнейшего брокера фоновых задач на базе Redis для Go. Напишите полноценную программу: инициализация asynq.Server с пулом воркеров, настройка concurrency = 10, регистрация middleware логирования и трассировки, обработка задач генерации отчетов с кастомным RetryDelayFunc. Продемонстрируйте структуру клиента (Client) и сервера (Server).",
        "theory": "Библиотека `hibiken/asynq` стала де-факто стандартом для очередей задач в Go-сообществе благодаря своей надежности и богатому функционалу:\n1. **Эффективность**: Построена на базе Redis Streams и Sorted Sets с оптимизированными Lua-скриптами.\n2. **Гарантия At-Least-Once**: Задачи не теряются при падении воркеров благодаря механизму автоматического восстановления активных задач.\n3. **Встроенный функционал**: Очереди с приоритетами, отложенные задачи (`ProcessIn`), периодический планировщик (`PeriodicTaskManager`), уникальные задачи (`UniqueKey`), Rate Limiting и поддержка Middleware.\n4. **Web UI & CLI**: Наличие готовой веб-панели управления `asynqmon` для инспекции очередей и ручного перезапуска упавших задач прямо в браузере.",
        "step_by_step": "1. Спроектируйте структуру конфигурации `AsynqMockConfig`.\n2. Реализуйте интерфейс `TaskMux` для маршрутизации типов задач к хэндлерам.\n3. Добавьте цепочку Middleware (Logging, Panic Recovery).\n4. Смоделируйте отправку задачи клиентом и исполнение сервером.\n5. Запустите программу и проанализируйте логи выполнения.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"
)

// Архитектурная модель библиотеки Asynq
type AsynqTask struct {
	Type     string
	Payload  []byte
	MaxRetry int
}

type HandlerFunc func(ctx context.Context, task AsynqTask) error

type MiddlewareFunc func(HandlerFunc) HandlerFunc

type AsynqServeMux struct {
	handlers    map[string]HandlerFunc
	middlewares []MiddlewareFunc
}

func NewAsynqServeMux() *AsynqServeMux {
	return &AsynqServeMux{handlers: make(map[string]HandlerFunc)}
}

func (m *AsynqServeMux) Use(mw MiddlewareFunc) {
	m.middlewares = append(m.middlewares, mw)
}

func (m *AsynqServeMux) HandleFunc(taskType string, h HandlerFunc) {
	m.handlers[taskType] = h
}

func (m *AsynqServeMux) ProcessTask(ctx context.Context, task AsynqTask) error {
	handler, ok := m.handlers[task.Type]
	if !ok {
		return fmt.Errorf("handler for %s not found", task.Type)
	}

	// Оборачиваем в цепочку middleware
	for i := len(m.middlewares) - 1; i >= 0; i-- {
		handler = m.middlewares[i](handler)
	}

	return handler(ctx, task)
}

// Middleware логирования длительности выполнения
func LoggingMiddleware(next HandlerFunc) HandlerFunc {
	return func(ctx context.Context, task AsynqTask) error {
		start := time.Now()
		fmt.Printf("[Asynq-Logger] Старт обработки задачи: %s\n", task.Type)
		err := next(ctx, task)
		fmt.Printf("[Asynq-Logger] Финиш задачи %s за %v (err=%v)\n",
			task.Type, time.Since(start).Round(time.Millisecond), err)
		return err
	}
}

type PDFReportPayload struct {
	ReportID int    `json:"report_id"`
	Title    string `json:"title"`
}

func main() {
	mux := NewAsynqServeMux()
	mux.Use(LoggingMiddleware)

	// Регистрируем хэндлер создания отчета
	mux.HandleFunc("report:generate_pdf", func(ctx context.Context, t AsynqTask) error {
		var p PDFReportPayload
		if err := json.Unmarshal(t.Payload, &p); err != nil {
			return err
		}
		time.Sleep(60 * time.Millisecond) // Имитация сборки PDF
		fmt.Printf("   -> PDF-отчет #%d '%s' успешно сформирован и сохранен в S3!\n",
			p.ReportID, p.Title)
		return nil
	})

	// Клиент создает задачу
	payloadBytes, _ := json.Marshal(PDFReportPayload{
		ReportID: 1045,
		Title:    "Годовой финансовый аудит HighLoad платформы",
	})
	task := AsynqTask{
		Type:     "report:generate_pdf",
		Payload:  payloadBytes,
		MaxRetry: 3,
	}

	// Исполнение задачи сервером
	ctx := context.Background()
	_ = mux.ProcessTask(ctx, task)
}
"""
            }
        ],
        "under_the_hood": "В Asynq каждый экземпляр сервера запускает несколько фоновых подсистем: `processor` (пул горутин-исполнителей), `syncer` (синхронизация состояния воркеров с Redis), `heartbeater` (отправка статуса жива ли нода) и `subscriber` (подписка на отмену задач). Это обеспечивает максимальную отказоустойчивость.",
        "pitfalls": "Отсутствие таймаута на уровне задачи: если в `asynq.ProcessIn` или конфигурации хэндлера не задан `Timeout(time.Minute)`, зависшая горутина навсегда заблокирует слот воркера в пуле.",
        "bigtech_interview": "'Как в Asynq реализовать уникальные задачи (Unique Tasks)?' Ответ: Использовать опцию `asynq.Unique(ttl)`. Asynq сохраняет в Redis распределенный ключ блокировки на время TTL: если задача с таким же типом и полезной нагрузкой уже стоит в очереди, повторная постановка возвратит ошибку `ErrDuplicateTask`."
    },
    {
        "num": 22,
        "title": "Глубокое погружение в библиотеку River на базе pgx/PostgreSQL",
        "task": "Изучите внутреннюю архитектуру библиотеки riverqueue/river — современной enterprise-очереди задач на чистом PostgreSQL с драйвером pgx/v5. Напишите типобезопасный воркер: определите структуру аргументов задачи, реализующую интерфейс river.JobArgs с методом Kind(), реализуйте структуру воркера с интерфейсом river.WorkerDefaults[Args], и напишите метод Work(ctx context.Context, job *river.Job[Args]) error с корректной обработкой ошибок.",
        "theory": "Библиотека `River` создана для решения главной боли очередей в распределенных системах: раздельного состояния между БД и брокером сообщений.\n\nКлючевые преимущества River:\n1. **Абсолютная типобезопасность**: Задачи и их аргументы описываются строгими Go-структурами с автогенерацией `Kind()`.\n2. **pgx/v5 Integration**: Использует нативный высокопроизводительный драйвер `jackc/pgx/v5` и connection pool `pgxpool.Pool`.\n3. **LISTEN/NOTIFY + Polling**: River не долбит базу бессмысленными частыми запросами. При появлении новой задачи PostgreSQL отправляет мгновенный сигнал `NOTIFY river_insert`, пробуждая спящий воркер.\n4. **FOR UPDATE SKIP LOCKED**: Параллельная выборка задач сотнями воркеров без блокировок строк.",
        "step_by_step": "1. Спроектируйте структуру аргументов задачи `UserWelcomeEmailArgs` с методом `Kind() string`.\n2. Создайте структуру воркера `UserWelcomeEmailWorker` с методом `Work(ctx, job)`.\n3. Реализуйте регистрацию воркеров в `RiverBundle`.\n4. Смоделируйте транзакционную вставку задачи и выполнение.\n5. Запустите программу.",
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

// RiverJobArgs аналог интерфейса river.JobArgs
type RiverJobArgs interface {
	Kind() string
}

// UserWelcomeEmailArgs строго типизированные аргументы задачи
type UserWelcomeEmailArgs struct {
	UserID int64  `json:"user_id"`
	Email  string `json:"email"`
}

func (UserWelcomeEmailArgs) Kind() string {
	return "user_welcome_email"
}

// RiverJob обертка над задачей с метаданными
type RiverJob[T RiverJobArgs] struct {
	ID        int64
	Args      T
	CreatedAt time.Time
	Attempt   int
}

// RiverWorker аналог интерфейса river.Worker[T]
type RiverWorker[T RiverJobArgs] interface {
	Work(ctx context.Context, job *RiverJob[T]) error
}

// UserWelcomeEmailWorker реализует логику отправки приветствия
type UserWelcomeEmailWorker struct{}

func (w *UserWelcomeEmailWorker) Work(ctx context.Context, job *RiverJob[UserWelcomeEmailArgs]) error {
	fmt.Printf("[River Worker] Обработка задачи #%d (Попытка %d)...\n", job.ID, job.Attempt)
	fmt.Printf("   -> Отправка приветственного письма для User #%d (%s)\n",
		job.Args.UserID, job.Args.Email)
	time.Sleep(40 * time.Millisecond) // Имитация I/O
	return nil
}

func main() {
	worker := &UserWelcomeEmailWorker{}

	args := UserWelcomeEmailArgs{
		UserID: 77701,
		Email:  "principal.architect@go.dev",
	}

	job := &RiverJob[UserWelcomeEmailArgs]{
		ID:        4001,
		Args:      args,
		CreatedAt: time.Now(),
		Attempt:   1,
	}

	ctx := context.Background()
	fmt.Printf("Регистрация воркера для задачи типа: '%s'\n", args.Kind())

	err := worker.Work(ctx, job)
	fmt.Printf("Исполнение завершено: err=%v\n", err)
}
"""
            }
        ],
        "under_the_hood": "River использует PostgreSQL команду `LISTEN river_insert`. Когда клиент вызывает `Insert(ctx, tx, args)`, триггер базы данных выполняет `NOTIFY river_insert`. Драйвер pgx перехватывает сигнал по открытому TCP-сокету через `conn.WaitForNotification()`, что обеспечивает задержку старта задачи менее 1 миллисекунды без накладных расходов периодического опроса.",
        "pitfalls": "Ограничение размера очереди: PostgreSQL оптимизирован для хранения данных, а не для гигантских очередей с миллионами мелких сообщений в секунду. Если пропускная способность превышает 20 000 задач в секунду, необходимо переходить на Redis Streams или Kafka.",
        "bigtech_interview": "'Почему River безопаснее для финансового биллинга, чем Redis Asynq?' Ответ: Потому что River позволяет вставить задачу `DebitAccountArgs` внутри той же SQL-транзакции PostgreSQL, где создается строка списания денег. Это гарантирует, что задача никогда не потеряется при сбое сети или падении сервера."
    },
    {
        "num": 23,
        "title": "Цепочки и зависимости задач (Job Chaining & Workflows)",
        "task": "Реализуйте конвейер связанных задач (Job Chaining Workflow) на Go: Задача 1 (FetchData) -> Задача 2 (ProcessData) -> Задача 3 (StoreResult). Каждая задача должна передавать результат своей работы в качестве входных параметров следующей задаче цепочки. При сбое на любом промежуточном этапе конвейер должен прерываться и запускать компенсирующее действие (Compensating Job / Rollback), очищая промежуточные артефакты.",
        "theory": "Сложные бизнес-процессы редко укладываются в одну атомарную задачу. Типичный конвейер:\n1. Шаг 1: `DownloadVideo` -> скачивает файл в локальный кэш.\n2. Шаг 2: `TranscodeVideo` -> сжимает в форматы 1080p, 720p, 480p.\n3. Шаг 3: `UploadToCDN` -> заливает результаты в S3.\n4. Шаг 4: `NotifyUser` -> шлет push в мобильное приложение.\n\nПаттерн Job Chaining:\n- Каждая задача при успешном завершении формирует полезную нагрузку для следующей и ставит ее в очередь.\n- В метаданных передается `WorkflowID` и список завершенных шагов.\n- В случае ошибки на шаге 3 воркер запускает компенсирующую задачу `CleanupOrphanedFiles(WorkflowID)`, удаляющую временные гигабайты с диска.",
        "step_by_step": "1. Спроектируйте структуру `WorkflowContext` с WorkflowID, текущим шагом и данными.\n2. Реализуйте шаги конвейера как независимые функции-обработчики.\n3. Добавьте логику перехода к следующему шагу при успехе.\n4. Смоделируйте ошибку на 2-м шаге и подтвердите вызов компенсирующего действия.\n5. Зафиксируйте корректность отката.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
)

type WorkflowState struct {
	WorkflowID string
	RawData    string
	Processed  string
	ResultID   int
	StepFailed bool
}

type PipelineRunner struct {
	compensations []string
}

func (r *PipelineRunner) Step1Fetch(ctx context.Context, state *WorkflowState) error {
	fmt.Printf("[%s] Шаг 1: Выгрузка данных из внешнего хранилища...\n", state.WorkflowID)
	state.RawData = "raw_financial_records_2026"
	r.compensations = append(r.compensations, "DeleteRawDataTempFile")
	return nil
}

func (r *PipelineRunner) Step2Transform(ctx context.Context, state *WorkflowState, simError bool) error {
	fmt.Printf("[%s] Шаг 2: Трансформация и агрегация показателей...\n", state.WorkflowID)
	if simError {
		return errors.New("transformation error: divide by zero in division B")
	}
	state.Processed = "AGGREGATED_TOTAL_SUM: 1,450,000$"
	r.compensations = append(r.compensations, "DropIntermediateAggregates")
	return nil
}

func (r *PipelineRunner) Step3Store(ctx context.Context, state *WorkflowState) error {
	fmt.Printf("[%s] Шаг 3: Сохранение финального отчета в DWH...\n", state.WorkflowID)
	state.ResultID = 99120
	return nil
}

func (r *PipelineRunner) RunCompensations(state *WorkflowState) {
	fmt.Printf("\n[COMPENSATION] Запуск компенсирующих действий для %s:\n", state.WorkflowID)
	for i := len(r.compensations) - 1; i >= 0; i-- {
		fmt.Printf("   -> Выполнен откат шага: %s\n", r.compensations[i])
	}
	r.compensations = nil
}

func (r *PipelineRunner) ExecuteWorkflow(ctx context.Context, workflowID string, simulateErrorOnStep2 bool) error {
	state := &WorkflowState{WorkflowID: workflowID}

	if err := r.Step1Fetch(ctx, state); err != nil {
		r.RunCompensations(state)
		return err
	}

	if err := r.Step2Transform(ctx, state, simulateErrorOnStep2); err != nil {
		fmt.Printf("[ERROR] Сбой на шаге 2: %v\n", err)
		r.RunCompensations(state)
		return err
	}

	if err := r.Step3Store(ctx, state); err != nil {
		r.RunCompensations(state)
		return err
	}

	fmt.Printf("[%s] ВЕСЬ КОНВЕЙЕР УСПЕШНО ЗАВЕРШЕН! Результат: ReportID=%d\n\n",
		workflowID, state.ResultID)
	return nil
}

func main() {
	runner := &PipelineRunner{}
	ctx := context.Background()

	fmt.Println("=== ТЕСТ 1: Успешное выполнение всех шагов конвейера ===")
	_ = runner.ExecuteWorkflow(ctx, "wf_success_100", false)

	fmt.Println("=== ТЕСТ 2: Ошибка на шаге 2 с запуском компенсаций ===")
	_ = runner.ExecuteWorkflow(ctx, "wf_failure_200", true)
}
"""
            }
        ],
        "under_the_hood": "Цепочки задач реализуют паттерн Saga (хореография или оркестрация). При хореографии каждая задача публикует событие завершения, на которое подписан следующий воркер. При оркестрации центральный воркер координирует переходы между шагами и гарантирует исполнение саги.",
        "pitfalls": "Зависание промежуточного состояния: если воркер упал прямо между завершением Задачи 1 и постановкой Задачи 2, конвейер зависнет навсегда. Для предотвращения этого метаданные пайплайна сохраняются в центральной БД с тайм-аутом шага.",
        "bigtech_interview": "'Когда вместо очередей задач для цепочек стоит использовать Temporal.io?' Ответ: Если конвейер содержит ветвления, ожидания внешних событий (human-in-the-loop, подтверждение по email), таймеры на дни/недели и сложные графы зависимостей, ручная реализация на очередях становится громоздкой. Платформы Durable Execution (Temporal) берут оркестрацию и сохранение истории событий на себя."
    },
    {
        "num": 24,
        "title": "Обработка паник (Panic Recovery) и изоляция Poison Pill",
        "task": "Спроектируйте защитное middleware восстановления после паник (Panic Recovery Middleware) для пула воркеров. Если некорректная задача вызывает разыменование nil-указателя (nil pointer dereference) или выход за границы среза внутри бизнес-кода, горутина воркера не должна приводить к краху (Crash) всего Go-процесса приложения. Перехватите панику через recover(), зафиксируйте трассировку стека (debug.Stack()), переведите задачу в статус failed и отправьте алерт в мониторинг.",
        "theory": "В языке Go необработанная паника (`panic()`) в любой изолированной горутине немедленно убивает ВЕСЬ процесс приложения со всеми сотнями параллельно работающих воркеров и HTTP-соединений!\n\nЕсли один клиент отправил поврежденные данные, вызвавшие панику в одном воркере, весь сервис упадет, оборвав транзакции всех остальных клиентов (Denial of Service).\n\nЗащитный паттерн Panic Recovery Middleware:\nКаждый запуск пользовательского обработчика задачи оборачивается в функцию с отложенным блоком `defer`:\n```go\ndefer func() {\n    if r := recover(); r != nil {\n        stack := debug.Stack()\n        log.Error('worker panic recovered', 'err', r, 'stack', string(stack))\n        markTaskFailed(taskID, r)\n    }\n}()\n```\nВоркер изолирует сбой, помечает ядовитую задачу как упавшую и спокойно продолжает разбор следующих задач.",
        "step_by_step": "1. Спроектируйте функцию-обертку `SafeExecute(taskID string, fn func() error) error`.\n2. Внутри вызовите `defer` с проверкой `recover()`.\n3. Сформируйте информативное сообщение об ошибке с сохранением типа паники.\n4. Запустите 3 задачи: нормальную, задачу с nil-pointer dereference и третью нормальную задачу.\n5. Докажите, что процесс выжил, а упавшая задача изолирована.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"runtime/debug"
)

type WorkerEngineSafe struct {
	recoveredPanics int
	successCount    int
}

func (e *WorkerEngineSafe) ExecuteJobSafely(jobID string, jobFn func() error) (err error) {
	// Защитный барьер Panic Recovery
	defer func() {
		if r := recover(); r != nil {
			e.recoveredPanics++
			stackTrace := string(debug.Stack())
			err = fmt.Errorf("panic in job %s: %v", jobID, r)
			fmt.Printf("[CRITICAL PANIC RECOVERED] Задача %s вызвала панику: %v\n", jobID, r)
			fmt.Printf("   --- Стек ошибки (первые 200 байт) ---\n%s...\n", stackTrace[:200])
		}
	}()

	err = jobFn()
	if err == nil {
		e.successCount++
	}
	return err
}

func main() {
	engine := &WorkerEngineSafe{}

	// Задача 1: Обычная корректная задача
	_ = engine.ExecuteJobSafely("job_1_normal", func() error {
		fmt.Println("Задача 1 успешно выполнена.")
		return nil
	})

	// Задача 2: Ядовитая пилюля (Poison Pill) с разыменованием nil-указателя!
	_ = engine.ExecuteJobSafely("job_2_poison_pill", func() error {
		var ptr *string
		fmt.Println("Задача 2 пытается прочитать nil-указатель...")
		_ = *ptr // ВЫЗЫВАЕТ ПАНИКУ: runtime error: invalid memory address or nil pointer dereference
		return nil
	})

	// Задача 3: Следующая корректная задача (должна выполниться штатно!)
	_ = engine.ExecuteJobSafely("job_3_normal", func() error {
		fmt.Println("Задача 3 успешно выполнена после восстановления от паники!")
		return nil
	})

	fmt.Printf("\n=== РЕЗУЛЬТАТЫ РАБОТЫ ДВИЖКА ===\n")
	fmt.Printf("Успешно выполненных задач: %d\n", engine.successCount)
	fmt.Printf("Перехваченных фатальных паник: %d (Процесс остался жив!)\n", engine.recoveredPanics)
}
"""
            }
        ],
        "under_the_hood": "Функция `recover()` эффективна только тогда, когда вызывается напрямую внутри отложенной функции `defer`. В рантайме Go паника разворачивает стек вызовов текущей горутины, последовательно вызывая зарегистрированные структуры `_defer`. Если `recover()` вернул ненулевое значение, рантайм останавливает раскрутку стека и возобновляет нормальное исполнение горутины с точки завершения отложенной функции.",
        "pitfalls": "Паники, возникшие в дочерних горутинах: если внутри обработчика задачи разработчик написал `go doAsyncWork()`, и паника произошла внутри этой фоновой горутины, родительский `defer recover()` ее НЕ перехватит! Процесс упадет. Каждая порожденная горутина обязана иметь собственный `recover()`.",
        "bigtech_interview": "'Можно ли перехватить через recover() фатальную ошибку fatal error: concurrent map read and map write?' Ответ: НЕТ! Ошибки гонок данных рантайма (concurrent map writes), переполнение стека (stack overflow) и нехватка памяти (OOM) вызывают мгновенный `runtime.throw()` / `SIGABRT` и в принципе не могут быть перехвачены через `recover()`."
    },
    {
        "num": 25,
        "title": "Обратное давление (Backpressure) и защита от переполнения брокера",
        "task": "Реализуйте комплексный механизм обратного давления (Backpressure Mechanism) для системы очередей. Если в брокере накопилось больше критического лимита задач (High Watermark, например 5000 задач), метод Enqueue должен переходить в режим защиты: сначала блокировать продюсера на время до 100 мс в ожидании разгрузки, а при непрекращающемся давлении — возвращать ошибку ErrQueueOverloaded (транслируемую в HTTP 429 Too Many Requests / 503 Service Unavailable), защищая память Redis и PostgreSQL от исчерпания.",
        "theory": "В распределенных системах дисбаланс скорости генерации и скорости обработки задач неизбежен:\nПродюсеры могут генерировать 50 000 задач в секунду (во время распродажи), а воркеры способны разбирать только 5 000 задач в секунду.\n\nЕсли очередь ничем не ограничена (Unbounded Queue), размер таблицы в базе данных или памяти в Redis начнет расти в геометрической прогрессии. В итоге:\n- Redis упадет по OOM (`OOM command not allowed when used memory > 'maxmemory'`).\n- PostgreSQL забьет диск временными файлами и остановит запись (Disk Full).\n\nЗащита через Backpressure:\nБрокер выставляет лимит емкости (Hard Limit). Когда глубина очереди приближается к лимиту, система создает сопротивление продюсерам: замедляет их либо отбрасывает низкоприоритетные запросы, сигнализируя upstream-сервисам о необходимости сбросить темп.",
        "step_by_step": "1. Спроектируйте структуру `BackpressureQueue` с емкостью и порогом перегрузки.\n2. В методе `Enqueue` проверяйте текущий размер очереди `queueDepth`.\n3. Реализуйте ожидание освобождения места через канал или `sync.Cond` с таймаутом.\n4. Если таймаут истек — возвращайте явную ошибку переполнения `ErrQueueOverloaded`.\n5. Продемонстрируйте защиту системы от потока из 1000 быстрых запросов.",
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

var ErrQueueOverloaded = errors.New("backpressure: queue is overloaded, reject request (HTTP 429)")

type SafeQueue struct {
	mu           sync.Mutex
	items        []string
	maxCapacity  int
	highWatermark int
	notFull      *sync.Cond
}

func NewSafeQueue(maxCapacity, highWatermark int) *SafeQueue {
	q := &SafeQueue{
		maxCapacity:   maxCapacity,
		highWatermark: highWatermark,
	}
	q.notFull = sync.NewCond(&q.mu)
	return q
}

// EnqueueWithBackpressure пытается поставить задачу с ограниченным временем ожидания
func (q *SafeQueue) EnqueueWithBackpressure(ctx context.Context, item string, waitTimeout time.Duration) error {
	q.mu.Lock()
	defer q.mu.Unlock()

	// Если очередь превысила критический порог -> ждем освобождения
	if len(q.items) >= q.highWatermark {
		// Канал для отслеживания таймаута ожидания
		timer := time.NewTimer(waitTimeout)
		defer timer.Stop()

		done := make(chan struct{})
		go func() {
			select {
			case <-timer.C:
				q.mu.Lock()
				q.notFull.Broadcast() // Будим ждущего, если время вышло
				q.mu.Unlock()
			case <-done:
			}
		}()

		for len(q.items) >= q.highWatermark {
			// Проверяем, не истек ли таймер
			select {
			case <-timer.C:
				close(done)
				return ErrQueueOverloaded // Отказываем продюсеру!
			default:
				q.notFull.Wait() // Спим до сигнала освобождения места
				if len(q.items) >= q.highWatermark {
					close(done)
					return ErrQueueOverloaded
				}
			}
		}
		close(done)
	}

	q.items = append(q.items, item)
	return nil
}

func (q *SafeQueue) Dequeue() (string, bool) {
	q.mu.Lock()
	defer q.mu.Unlock()

	if len(q.items) == 0 {
		return "", false
	}

	item := q.items[0]
	q.items = q.items[1:]
	q.notFull.Signal() // Сигнализируем продюсерам, что появилось место!
	return item, true
}

func main() {
	// Лимит 10 элементов, порог защиты = 5 элементов
	queue := NewSafeQueue(10, 5)
	ctx := context.Background()

	fmt.Println("1. Заполняем очередь до порога перегрузки (5 задач)...")
	for i := 1; i <= 5; i++ {
		_ = queue.EnqueueWithBackpressure(ctx, fmt.Sprintf("task_%d", i), 50*time.Millisecond)
	}
	fmt.Printf("   Задач в очереди: %d (достигнут High Watermark!)\n", len(queue.items))

	fmt.Println("\n2. Продюсер пытается вставить 6-ю задачу (срабатывает Backpressure-ожидание)...")
	start := time.Now()
	err := queue.EnqueueWithBackpressure(ctx, "task_overflow_6", 50*time.Millisecond)
	fmt.Printf("   Результат: err=%v за %v (Продюсер получил отказ, память брокера защищена!)\n",
		err, time.Since(start).Round(time.Millisecond))

	fmt.Println("\n3. Воркер освобождает 2 задачи...")
	queue.Dequeue()
	queue.Dequeue()
	fmt.Printf("   Задач в очереди после разбора: %d\n", len(queue.items))

	fmt.Println("\n4. Повторная попытка постановки после разгрузки очереди...")
	errAfterDrain := queue.EnqueueWithBackpressure(ctx, "task_retry_6", 50*time.Millisecond)
	fmt.Printf("   Результат: err=%v (Задача успешно принята!)\n", errAfterDrain)
}
"""
            }
        ],
        "under_the_hood": "Backpressure создает гидравлическое сопротивление в сетевом графе микросервисов. Когда очередь задач отвергает вызовы с кодом 429, API Gateway начинает отвечать 429 клиентам, заставляя браузеры и мобильные приложения задействовать экспоненциальный откат (Backoff) на стороне клиента.",
        "pitfalls": "Блокировка продюсера без таймаута (`sync.Cond.Wait()` навсегда): если воркеры упали, а продюсеры заблокировались без таймаута, все входящие HTTP-горутины зависнут, исчерпав память веб-сервера.",
        "bigtech_interview": "'Как настроить Backpressure в брокере Redis?' Ответ: Задать в redis.conf директиву `maxmemory 4gb` и политику `maxmemory-policy noeviction`. При исчерпании памяти Redis возвратит явную ошибку `OOM command not allowed`, предотвращая неконтролируемое удаление других данных."
    },
    {
        "num": 26,
        "title": "Профилирование утечек памяти в долгоживущих воркерах через pprof",
        "task": "Исследуйте и устраните типичную утечку памяти в долгоживущих Go-воркерах. Создайте воркер, обрабатывающий задачи в бесконечном цикле. Смоделируйте утечку памяти: накопление ссылок на старые задачи в глобальном срезе или не закрытые тикеры / контексты. Подключите pprof, снимите дамп кучи (Heap Profile) с помощью runtime/pprof, найдите точную строчку кода, удерживающую миллионы байт, и исправьте утечку.",
        "theory": "Воркеры очередей — это долгоживущие демоны, работающие месяцами без перезапуска. Медленная утечка памяти всего в 10 КБ на задачу при разборе 1 000 000 задач в сутки приведет к утечке 10 ГБ оперативной памяти за 24 часа и неминуемому убийству процесса ядром Linux (OOMKilled).\n\nЧастые причины утечек в воркерах Go:\n1. **Неочищенные глобальные кэши/срезы**: добавление элементов в слайс без последующей очистки.\n2. **Забытые горутины и таймеры**: вызов `time.Tick()` вместо `time.NewTicker()` с `defer ticker.Stop()`.\n3. **Подслайсинг больших срезов (Sub-slice memory retention)**: `small = hugeBuffer[:10]`. Срез `small` удерживает ссылку на весь базовый массив в куче, не позволяя GC освободить мегабайты памяти.",
        "step_by_step": "1. Напишите код воркера с утечкой памяти через глобальный срез логов.\n2. Вызовите `runtime.GC()` и замерьте аллоцированную память через `runtime.ReadMemStats`.\n3. Снимите профиль кучи через `pprof.WriteHeapProfile`.\n4. Исправьте код: используйте кольцевой буфер фиксированного размера или обнуляйте ссылки.\n5. Докажите стабильное плато потребления памяти после исправления.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"runtime"
	"time"
)

// LeakSimulator накапливает историю задач в глобальном срезе (ТИПИЧНАЯ УТЕЧКА!)
type LeakyWorker struct {
	history [][]byte // удерживает ссылки в куче!
}

func (w *LeakyWorker) ProcessLeaky(data []byte) {
	// Ошибка: сохраняем ссылку на срез навсегда
	w.history = append(w.history, data)
}

// FixedWorker использует кольцевой буфер фиксированной емкости
type FixedWorker struct {
	ringBuffer [][]byte
	index      int
	capacity   int
}

func NewFixedWorker(cap int) *FixedWorker {
	return &FixedWorker{
		ringBuffer: make([][]byte, cap),
		capacity:   cap,
	}
}

func (w *FixedWorker) ProcessFixed(data []byte) {
	// Перезаписываем старые слоты, освобождая память для GC!
	w.ringBuffer[w.index] = data
	w.index = (w.index + 1) % w.capacity
}

func getHeapAllocMB() float64 {
	runtime.GC()
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	return float64(m.Alloc) / 1024 / 1024
}

func main() {
	const iterations = 50_000
	payloadSize := 1024 // 1 КБ на задачу

	// 1. Тест воркера с утечкой
	fmt.Printf("1. Запуск дырявого воркера (%d задач по 1 КБ)...\n", iterations)
	leaky := &LeakyWorker{}
	for i := 0; i < iterations; i++ {
		data := make([]byte, payloadSize)
		leaky.ProcessLeaky(data)
	}
	memLeaky := getHeapAllocMB()
	fmt.Printf("   Память в куче после работы LeakyWorker: %.2f МБ (УТЕЧКА ПАМЯТИ!)\n\n", memLeaky)

	// Очищаем память
	leaky = nil
	runtime.GC()
	time.Sleep(50 * time.Millisecond)

	// 2. Тест исправленного воркера с кольцевым буфером на 100 элементов
	fmt.Printf("2. Запуск исправленного воркера с кольцевым буфером на 100 элементов...\n")
	fixed := NewFixedWorker(100)
	for i := 0; i < iterations; i++ {
		data := make([]byte, payloadSize)
		fixed.ProcessFixed(data)
	}
	memFixed := getHeapAllocMB()
	fmt.Printf("   Память в куче после работы FixedWorker: %.2f МБ (СТАБИЛЬНОЕ ПЛАТО!)\n", memFixed)

	savedMB := memLeaky - memFixed
	fmt.Printf("\nЭкономия памяти: %.2f МБ (потребление снижено в %.1f раз!)\n",
		savedMB, memLeaky/memFixed)
}
"""
            }
        ],
        "under_the_hood": "Сборщик мусора Go отслеживает достижимость объектов от корней (стеки, глобальные переменные). Пока на слайс ссылается живая переменная структуры `LeakyWorker`, сборщик мусора не имеет права освободить ни один байт из массива, даже если эти данные больше никогда не будут прочитаны.",
        "pitfalls": "Утечка горутин через незакрытые каналы: если воркер ожидает ответа из канала в `select`, а отправитель отвалился и не закрыл канал, горутина зависает навсегда, удерживая свой стек (2 КБ) и захваченные контексты.",
        "bigtech_interview": "'Как в продакшене автоматически обнаружить утечку памяти в воркерах?' Ответ: Настроить непрерывное профилирование (Continuous Profiling через Grafana Pyroscope или Google Cloud Profiler) и алерт в Prometheus на устойчивый положительный тренд производной `deriv(go_memstats_alloc_bytes[1h]) > 0`."
    },
    {
        "num": 27,
        "title": "Тестирование воркеров: подмена времени и мокирование брокера",
        "task": "Разработайте методику детерминированного тестирования очередей задач без нестабильных вызовов time.Sleep. Реализуйте интерфейс виртуальных часов (MockClock / FakeClock) с возможностью мгновенного перемещения времени вперед Clock.Advance(2 * time.Hour). Напишите модульный тест для воркера, проверяющий: 1) Точное срабатывание отложенной задачи через 1 час; 2) Экспоненциальный откат повторов без реального ожидания реального времени.",
        "theory": "Тестирование распределенных планировщиков и отложенных задач — частый источник медленных и нестабильных (flaky) тестов в CI/CD:\n- Если отложенная задача должна сработать через 10 секунд, наивный тест вызывает `time.Sleep(10 * time.Second)`. Тестовый сьют начинает выполняться часами!\n- Сетевые лаги в раннерах GitHub Actions приводят к случайным падениям проверок таймингов.\n\nРешение: Подмена времени через виртуальные часы (Virtual / Mock Clock, например библиотека `jonboulle/clockwork`):\n- Код сервиса зависит не от глобального `time.Now()`, а от интерфейса `Clock`.\n- В тестах используется `FakeClock`. Тест может мгновенно сдвинуть время на 24 часа вперед: `clock.Advance(24 * time.Hour)`.\n- Все таймеры, тикеры и отложенные задачи срабатывают за микросекунды в строго детерминированном порядке!",
        "step_by_step": "1. Спроектируйте интерфейс `Clock` с методами `Now() time.Time` и `After(d time.Duration) <-chan time.Time`.\n2. Реализуйте структуру `FakeClock` с методом `Advance(d time.Duration)`.\n3. Напишите воркер, использующий виртуальные часы для проверки срока исполнения задач.\n4. Протестируйте отложенную на 3 часа задачу мгновенно без вызова Sleep.\n5. Зафиксируйте выполнение теста за менее чем 5 миллисекунд.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
	"time"
)

type Clock interface {
	Now() time.Time
}

type FakeClock struct {
	mu  sync.Mutex
	now time.Time
}

func NewFakeClock(initial time.Time) *FakeClock {
	return &FakeClock{now: initial}
}

func (c *FakeClock) Now() time.Time {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.now
}

func (c *FakeClock) Advance(d time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.now = c.now.Add(d)
}

type ScheduledJob struct {
	ID    string
	RunAt time.Time
}

type FastTestScheduler struct {
	clock Clock
	jobs  []ScheduledJob
}

func (s *FastTestScheduler) EnqueueAt(id string, runAt time.Time) {
	s.jobs = append(s.jobs, ScheduledJob{ID: id, RunAt: runAt})
}

func (s *FastTestScheduler) GetReadyJobs() []string {
	now := s.clock.Now()
	ready := make([]string, 0)
	remaining := make([]ScheduledJob, 0)

	for _, j := range s.jobs {
		if !j.RunAt.After(now) {
			ready = append(ready, j.ID)
		} else {
			remaining = append(remaining, j)
		}
	}
	s.jobs = remaining
	return ready
}

func main() {
	startRealTime := time.Now()

	// Устанавливаем виртуальное время: 2026-09-08 12:00:00
	initialTime := time.Date(2026, 9, 8, 12, 0, 0, 0, time.UTC)
	fakeClock := NewFakeClock(initialTime)

	scheduler := &FastTestScheduler{clock: fakeClock}

	// Ставим задачу, которая должна сработать через 3 часа (в 15:00)
	runAt := initialTime.Add(3 * time.Hour)
	scheduler.EnqueueAt("daily_report_generation", runAt)

	fmt.Println("Текущее виртуальное время:", fakeClock.Now().Format(time.RFC3339))
	ready := scheduler.GetReadyJobs()
	fmt.Printf("Проверка сразу: готово к запуску: %d задач (ожидалось 0)\n", len(ready))

	// Мгновенно перемещаем виртуальное время на 1 час вперед (13:00)
	fakeClock.Advance(1 * time.Hour)
	fmt.Println("\nПеремотка на +1 час вперед:", fakeClock.Now().Format(time.RFC3339))
	ready = scheduler.GetReadyJobs()
	fmt.Printf("Проверка через 1 час: готово к запуску: %d задач (ожидалось 0)\n", len(ready))

	// Мгновенно перематываем еще на 2 часа 5 минут вперед (15:05)
	fakeClock.Advance(2*time.Hour + 5*time.Minute)
	fmt.Println("\nПеремотка еще на +2 часа 5 минут:", fakeClock.Now().Format(time.RFC3339))
	ready = scheduler.GetReadyJobs()
	fmt.Printf("Проверка после наступления срока: готово к запуску: %d задач (ID: %v)\n",
		len(ready), ready)

	duration := time.Since(startRealTime)
	fmt.Printf("\nТест эмуляции 3 часов ожидания выполнен за реальные: %v!\n", duration)
}
"""
            }
        ],
        "under_the_hood": "Инверсия зависимостей (Dependency Inversion) времени позволяет отвязать рантайм от тиков системного кварцевого генератора CPU (TSC - Time Stamp Counter). В боевых тестах подменяется не только Now(), но и каналы таймеров через структуру каналов-триггеров.",
        "pitfalls": "Использование реального time.Now() внутри глубоко вложенных вспомогательных функций библиотеки. Если хотя бы одна строчка проверяет реальные часы, тест потеряет детерминированность.",
        "bigtech_interview": "'Как протестировать распределенный дедлок воркеров?' Ответ: Использовать интеграционные тесты с Testcontainers (запуск реального PostgreSQL/Redis в Docker) и симуляцией сетевых задержек через Toxiproxy."
    },
    {
        "num": 28,
        "title": "Сравнение производительности: Redis vs PostgreSQL Queue",
        "task": "Напишите бенчмарк и профилировщик пропускной способности для очередей задач: сравните реализацию на Redis (In-Memory списки/стримы) и PostgreSQL (SELECT FOR UPDATE SKIP LOCKED). Замерьте максимальный RPS постановки (Enqueue Throughput) и разбора (Dequeue Throughput) при 50 параллельных горутинах. Проанализируйте затраты дискового I/O (WAL sync) и утилизацию процессора.",
        "theory": "Выбор движка очереди — классический архитектурный спор на собеседованиях:\n\n1. **Redis Queue**:\n   - Все данные в оперативной памяти.\n   - Задержка операции: 0.1–0.5 мс.\n   - Пропускная способность: до 80 000 – 150 000 задач в секунду на одном инстансе.\n   - Слабость: Ограничен объемом RAM, нет транзакционности с реляционными данными (Dual-Write risk).\n\n2. **PostgreSQL Queue (River / FOR UPDATE SKIP LOCKED)**:\n   - Транзакционность: постановка задачи в одной ACID-транзакции с бизнес-данными.\n   - Задержка операции: 1.0–5.0 мс (зависит от дискового `fsync` WAL).\n   - Пропускная способность: от 3 000 до 15 000 задач в секунду на мощном NVMe SSD.\n   - Слабость: Table Bloat (мертвые строки), нагрузка на диск и процессор базы данных.",
        "step_by_step": "1. Реализуйте бенчмарк-интерфейс `QueueBenchmark`.\n2. Смоделируйте Redis Queue (чистая память со спинлоками) и Postgres Queue (имитация фиксации на диск 0.5 мс).\n3. Запустите 50 горутин на постановку 5000 задач в обе системы.\n4. Замерьте итоговое время и пропускную способность (RPS).\n5. Сделайте инженерный вывод.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
	"time"
)

type BenchResults struct {
	Name       string
	TotalJobs  int
	Duration   time.Duration
	Throughput float64
}

// SimRedisQueue чистая память, нулевой I/O
type SimRedisQueue struct {
	mu    sync.Mutex
	items []string
}

func (q *SimRedisQueue) Enqueue(item string) {
	q.mu.Lock()
	q.items = append(q.items, item)
	q.mu.Unlock()
}

// SimPostgresQueue имитирует запись в WAL на NVMe SSD (0.2 мс)
type SimPostgresQueue struct {
	mu       sync.Mutex
	items    []string
	walDelay time.Duration
}

func (q *SimPostgresQueue) Enqueue(item string) {
	time.Sleep(q.walDelay) // Имитация fsync журнала WAL на диск
	q.mu.Lock()
	q.items = append(q.items, item)
	q.mu.Unlock()
}

func runBenchmark(name string, totalJobs, concurrency int, enqueueFn func(string)) BenchResults {
	var wg sync.WaitGroup
	jobsPerWorker := totalJobs / concurrency

	start := time.Now()
	for w := 0; w < concurrency; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for i := 0; i < jobsPerWorker; i++ {
				enqueueFn("job_payload_bytes_sample")
			}
		}(w)
	}

	wg.Wait()
	dur := time.Since(start)

	return BenchResults{
		Name:       name,
		TotalJobs:  totalJobs,
		Duration:   dur,
		Throughput: float64(totalJobs) / dur.Seconds(),
	}
}

func main() {
	totalJobs := 10_000
	concurrency := 20

	fmt.Printf("Запуск сравнительного бенчмарка очередей (%d задач, %d горутин)...\n\n",
		totalJobs, concurrency)

	// 1. Тест Redis Queue
	redisQ := &SimRedisQueue{}
	resRedis := runBenchmark("Redis In-Memory Queue", totalJobs, concurrency, redisQ.Enqueue)

	// 2. Тест PostgreSQL Queue (WAL latency 0.15 мс)
	pgQ := &SimPostgresQueue{walDelay: 150 * time.Microsecond}
	resPG := runBenchmark("PostgreSQL Table Queue (WAL sync)", totalJobs, concurrency, pgQ.Enqueue)

	fmt.Println("=== СРАВНИТЕЛЬНЫЕ РЕЗУЛЬТАТЫ ПРОИЗВОДИТЕЛЬНОСТИ ===")
	fmt.Printf("1. %-35s: %v | %.1f оп/сек\n",
		resRedis.Name, resRedis.Duration.Round(time.Millisecond), resRedis.Throughput)
	fmt.Printf("2. %-35s: %v | %.1f оп/сек\n\n",
		resPG.Name, resPG.Duration.Round(time.Millisecond), resPG.Throughput)

	ratio := resRedis.Throughput / resPG.Throughput
	fmt.Printf("Вывод: Redis быстрее PostgreSQL в %.1f раз по чистой скорости постановки.\n", ratio)
	fmt.Printf("Однако PostgreSQL гарантирует ACID-транзакционность и отсутствие риска потери данных при аварии!\n")
}
"""
            }
        ],
        "under_the_hood": "Разница в скорости обусловлена системным вызовом `fdatasync / fsync`. Операционная система буферизует запись в дисковый кэш (Page Cache), но для соблюдения ACID PostgreSQL обязан дождаться физической записи секторов на пластины/чипы памяти SSD. Redis по умолчанию использует асинхронный сброс (appendfsync everysec), что и обеспечивает колоссальный отрыв по RPS.",
        "pitfalls": "Преждевременная оптимизация: выбор Redis вместо PostgreSQL только ради скорости в системе, где создается всего 100 задач в минуту. Дополнительный инфраструктурный демон Redis увеличивает сложность DevOps и риски потери данных без реальной потребности в скорости.",
        "bigtech_interview": "'Какое эмпирическое правило выбора между Redis и PostgreSQL для очередей в BigTech?' Ответ: Если объем задач < 5 000 в секунду и критична финансовая надежность — строго PostgreSQL (River). Если объем задач > 20 000 в секунду или задачи эфемерны (уведомления, аналитика) — Redis (Asynq) или Kafka."
    },
    {
        "num": 29,
        "title": "Очереди в геораспределенных окружениях (Multi-Region)",
        "task": "Спроектируйте архитектуру очередей фоновых задач в Multi-Region инфраструктуре (например, датацентры Москва и Санкт-Петербург или регионы Cloud EU/US). Проанализируйте проблемы задержки синхронизации асинхронных реплик БД (Replication Lag) и риск параллельного исполнения одной задачи в двух регионах (Split-Brain). Реализуйте маршрутизацию задач на базе регионального шардирования с глобальным арбитром.",
        "theory": "При масштабировании сервиса на несколько географических регионов (Multi-Region Active-Active) создание очередей сталкивается с законами физики (скорость света в оптоволокне: пинг между Москвой и Франкфуртом ~40 мс, между США и Европой ~80–120 мс):\n\nОшибки наивной архитектуры:\n1. Если все регионы читают общую централизованную БД в одном датацентре, воркеры в удаленном регионе тратят 100 мс на каждый чих `SELECT FOR UPDATE`.\n2. Если реплицировать таблицу очередей асинхронно между регионами, неизбежен Split-Brain: две ноды в разных регионах одновременно возьмут одну и ту же задачу до того, как репликация доставит флаг `running`.\n\nАрхитектура локальных очередей с региональной изоляцией:\n- Каждый регион имеет СВОЙ локальный брокер очередей (`queue-dc-1`, `queue-dc-2`).\n- Задачи обрабатываются локальными воркерами с нулевой сетевой задержкой.\n- Межрегиональные задачи передаются асинхронно через надежный репликатор или глобальный Outbox.",
        "step_by_step": "1. Спроектируйте структуру `RegionalQueue` с идентификатором региона (RegionID).\n2. Реализуйте региональный роутер задач `RegionalRouter`.\n3. Смоделируйте маршрутизацию: европейские пользователи отправляются в очередь EU, российские — в RU.\n4. Продемонстрируйте сценарий изоляции сбоя одного из регионов (Failover).\n5. Сделайте вывод об архитектурной изоляции.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
)

type RegionalTask struct {
	ID       string
	Region   string // "dc-msk", "dc-spb"
	Payload  string
}

type RegionalDatacenter struct {
	RegionID string
	mu       sync.Mutex
	localQueue []RegionalTask
}

func (dc *RegionalDatacenter) EnqueueLocal(task RegionalTask) {
	dc.mu.Lock()
	defer dc.mu.Unlock()
	dc.localQueue = append(dc.localQueue, task)
}

func (dc *RegionalDatacenter) DequeueLocal() (*RegionalTask, bool) {
	dc.mu.Lock()
	defer dc.mu.Unlock()
	if len(dc.localQueue) == 0 {
		return nil, false
	}
	t := dc.localQueue[0]
	dc.localQueue = dc.localQueue[1:]
	return &t, true
}

type GlobalQueueRouter struct {
	regions map[string]*RegionalDatacenter
}

func NewGlobalQueueRouter() *GlobalQueueRouter {
	return &GlobalQueueRouter{
		regions: map[string]*RegionalDatacenter{
			"msk": {RegionID: "dc-msk"},
			"spb": {RegionID: "dc-spb"},
		},
	}
}

func (r *GlobalQueueRouter) Dispatch(task RegionalTask) {
	dc, exists := r.regions[task.Region]
	if !exists {
		// Дефолтный fallback на центральный ДЦ
		dc = r.regions["msk"]
	}
	dc.EnqueueLocal(task)
	fmt.Printf("[Global Router] Задача %s направлена в локальный кластер [%s]\n",
		task.ID, dc.RegionID)
}

func main() {
	router := NewGlobalQueueRouter()

	fmt.Println("Поступление задач из разных географических локаций:")
	router.Dispatch(RegionalTask{ID: "task_msk_101", Region: "msk", Payload: "User from Moscow"})
	router.Dispatch(RegionalTask{ID: "task_spb_202", Region: "spb", Payload: "User from Saint Petersburg"})
	router.Dispatch(RegionalTask{ID: "task_spb_203", Region: "spb", Payload: "User from Saint Petersburg"})

	fmt.Println("\nЛокальный разбор задач воркерами в каждом датацентре:")
	for name, dc := range router.regions {
		count := len(dc.localQueue)
		fmt.Printf("Датацентр [%s]: в локальной очереди %d задач (обработка без межрегионального пинга!)\n",
			name, count)
		for {
			t, ok := dc.DequeueLocal()
			if !ok {
				break
			}
			fmt.Printf("   -> Воркер %s обработал: %s\n", dc.RegionID, t.ID)
		}
	}
}
"""
            }
        ],
        "under_the_hood": "Региональная изоляция очередей опирается на принцип Data Locality. Задачи обрабатываются там, где физически расположены данные пользователя, исключая блокировки по WAN-сетям и сохраняя доступность сервиса даже при полном обрыве оптоволоконного кабеля между датацентрами.",
        "pitfalls": "Перенос задач между регионами при аварии ДЦ (Disaster Recovery): если ДЦ Санкт-Петербург полностью сгорел, задачи из его очереди должны быть безопасно эвакуированы в Москву с использованием распределенного консенсуса (Raft / etcd).",
        "bigtech_interview": "'Как избежать Split-Brain при синхронизации очередей между тремя датацентрами?' Ответ: Использовать кворумный консенсус (Raft / Paxos) с нечетным числом нод (минимум 3 региона). Только регионы, входящие в состав кворумного большинства (2 из 3), имеют право выбирать и обрабатывать распределенные задачи."
    },
    {
        "num": 30,
        "title": "Enterprise Распределенный Менеджер Задач на Go",
        "task": "Спроектируйте и соберите законченный Enterprise Распределенный Менеджер Задач (Production-Grade Task Engine) на Go. Объедините все созданные архитектурные компоненты: 1) Очередь с поддержкой приоритетов (Critical, High, Low); 2) Надежное выполнение с Heartbeat и восстановлением зависших задач; 3) Экспоненциальный Retry с Full Jitter; 4) Изоляцию Poison Pill в Dead Letter Queue (DLQ); 5) Panic Recovery; 6) Graceful Shutdown при получении сигналов ОС. Протестируйте под нагрузкой без гонок данных.",
        "theory": "Финальный синтез архитектуры распределенных планировщиков и очередей задач:\nПолноценный корпоративный менеджер задач — это высоконадежная платформа, гарантирующая надежность финансового уровня, отказоустойчивость при падении нод, защиту от резонансных штормов и прозрачную наблюдаемость.",
        "step_by_step": "1. Спроектируйте законченную структуру `EnterpriseTaskManager`.\n2. Интегрируйте Priority Queue, Retry с Jitter, Heartbeat и DLQ.\n3. Реализуйте метод `Submit(task)` и фоновые воркеры.\n4. Продемонстрируйте обработку нормальных задач, авто-ретрай сбойных задач и уход в DLQ ядовитых задач.\n5. Завершите работу через Graceful Shutdown.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"math/rand"
	"sync"
	"sync/atomic"
	"time"
)

type EntTask struct {
	ID         string
	Type       string
	RetryCount int
	MaxRetries int
	IsPoison   bool
}

type EnterpriseTaskManager struct {
	mu           sync.Mutex
	queue        chan EntTask
	dlq          map[string]EntTask
	quit         chan struct{}
	wg           sync.WaitGroup
	successTotal int64
	dlqTotal     int64
}

func NewEnterpriseTaskManager(queueCap int) *EnterpriseTaskManager {
	return &EnterpriseTaskManager{
		queue: make(chan EntTask, queueCap),
		dlq:   make(map[string]EntTask),
		quit:  make(chan struct{}),
	}
}

func (m *EnterpriseTaskManager) Submit(t EntTask) {
	m.queue <- t
}

func (m *EnterpriseTaskManager) Start(workers int) {
	for w := 1; w <= workers; w++ {
		m.wg.Add(1)
		go m.workerLoop(w)
	}
}

func (m *EnterpriseTaskManager) workerLoop(workerID int) {
	defer m.wg.Done()

	for {
		select {
		case <-m.quit:
			return
		case task, ok := <-m.queue:
			if !ok {
				return
			}
			m.executeWithSafety(workerID, task)
		}
	}
}

func (m *EnterpriseTaskManager) executeWithSafety(workerID int, task EntTask) {
	// 1. Panic Recovery
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("[Worker #%d] PANIC перехвачена для задачи %s: %v\n", workerID, task.ID, r)
			m.handleFailure(task, fmt.Errorf("panic: %v", r))
		}
	}()

	// 2. Бизнес-логика
	if task.IsPoison {
		panic("nil pointer dereference inside business logic")
	}

	if task.Type == "unstable_network" && task.RetryCount < 2 {
		m.handleFailure(task, errors.New("network timeout 504"))
		return
	}

	atomic.AddInt64(&m.successTotal, 1)
	fmt.Printf("[Worker #%d] УСПЕХ: Задача %s (%s) выполнена!\n",
		workerID, task.ID, task.Type)
}

func (m *EnterpriseTaskManager) handleFailure(task EntTask, err error) {
	task.RetryCount++
	if task.RetryCount >= task.MaxRetries {
		m.mu.Lock()
		m.dlq[task.ID] = task
		m.mu.Unlock()
		atomic.AddInt64(&m.dlqTotal, 1)
		fmt.Printf("[DLQ ALERT] Задача %s отправлена в DLQ после %d попыток (err: %v)\n",
			task.ID, task.RetryCount, err)
		return
	}

	// Экспоненциальный откат с джиттером
	backoff := time.Duration(rand.Intn(50)+20) * time.Millisecond
	time.AfterFunc(backoff, func() {
		m.queue <- task
	})
	fmt.Printf("[RETRY] Задача %s вернется на повтор через %v (Попытка %d)\n",
		task.ID, backoff, task.RetryCount)
}

func (m *EnterpriseTaskManager) Shutdown() {
	close(m.quit)
	m.wg.Wait()
}

func main() {
	manager := NewEnterpriseTaskManager(100)
	manager.Start(3)

	fmt.Println("Постановка задач в Enterprise Task Manager:")

	// 1. Успешная задача
	manager.Submit(EntTask{ID: "task_1_good", Type: "email", MaxRetries: 3})

	// 2. Нестабильная задача (восстановится на 2-м ретрае)
	manager.Submit(EntTask{ID: "task_2_flaky", Type: "unstable_network", MaxRetries: 3})

	// 3. Ядовитая задача с паникой (уйдет в DLQ)
	manager.Submit(EntTask{ID: "task_3_poison", Type: "corrupted", MaxRetries: 2, IsPoison: true})

	// Ожидаем завершения обработки и ретраев
	time.Sleep(300 * time.Millisecond)

	manager.Shutdown()

	fmt.Printf("\n=== ФИНАЛЬНЫЙ СТАТУС ПЛАТФОРМЫ ===\n")
	fmt.Printf("Успешно выполненных задач: %d\n", manager.successTotal)
	fmt.Printf("Задач в Dead Letter Queue:  %d\n", manager.dlqTotal)
	fmt.Println("Платформа отработала надежно и завершилась штатно!")
}
"""
            }
        ],
        "under_the_hood": "Менеджер объединяет все инженерные слои: неблокирующую диспетчеризацию, адаптивные ретраи, защиту от краха через panic recovery и безопасную изоляцию в DLQ.",
        "pitfalls": "Отсутствие таймаута на очереди при shutdown может привести к потере задач, находящихся в буфере ретрая (`time.AfterFunc`). В проде таймеры ретраев сохраняются в персистентную базу данных.",
        "bigtech_interview": "'Как защитить менеджер задач от потери сообщений при аварии датацентра?' Ответ: Использовать распределенный кластер брокера (Kafka, RabbitMQ Quorum Queues, PostgreSQL синхронная репликация с кворумом) и подтверждение ACK только после гарантированной фиксации на диск."
    }
]
