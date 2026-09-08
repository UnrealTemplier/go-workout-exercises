# -*- coding: utf-8 -*-
"""
Chapter 88 Part 2: Exercises 16 to 30
Real-Time Stream Processing on Go
"""

exercises = [
    {
        "num": 16,
        "title": "Снимки состояния и алгоритм Чанди-Лэмпорта (Chandy-Lamport Checkpointing)",
        "task": "Реализуйте упрощенную версию алгоритма Чанди-Лэмпорта для распределенных снимков состояния (Distributed Checkpointing / Asynchronous Barrier Snapshotting): координатор пускает специальное маркерное сообщение (Barrier) через граф потоковых операторов. При получении барьера каждый оператор фиксирует локальный снимок состояния в надежное хранилище и передает барьер дальше, обеспечивая глобальную консистентность без остановки конвейера.",
        "theory": "Как сделать согласованный снапшот распределенной потоковой системы из 50 операторов, если данные непрерывно текут по сети, а останавливать весь мир (Stop-The-World) на время записи снимка недопустимо?\n\nРешение — **Алгоритм Чанди-Лэмпорта (1985) и Asynchronous Barrier Snapshotting (ABS)**, лежащий в основе Apache Flink:\n1. Координатор периодически вставляет в потоки источников специальный маркер — **Checkpoint Barrier $B_n$**.\n2. Барьеры текут вместе с обычными событиями, разделяя бесконечный поток на две эпохи: события до барьера (эпоха $n$) и события после барьера (эпоха $n+1$).\n3. Когда оператор получает барьер $B_n$ со всех входящих каналов (Barrier Alignment), он асинхронно сохраняет свое текущее состояние (State Snapshot) и немедленно пробрасывает барьер $B_n$ downstream-операторам.\n4. Поток данных НЕ останавливается: обработка продолжается параллельно с фоновым сбросом снимка на диск.",
        "step_by_step": "1. Спроектируйте структуру сообщения `StreamMessage` с типом Data или Barrier.\n2. Реализуйте оператор, поддерживающий `BarrierAlignment`.\n3. При получении барьера вызовите фиксацию локального снимка состояния `SnapshotState()`.\n4. Продемонстрируйте безостановочный проход барьера через конвейер из трех операторов.",
        "code_blocks": [
            {
                "filename": "chandy_lamport.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
	"time"
)

type MsgType int

const (
	MsgData MsgType = iota
	MsgBarrier
)

type StreamMessage struct {
	Type        MsgType
	Key         string
	Value       int
	CheckpointID int64
}

// StatefulOperator хранит локальное состояние и делает снимки при получении барьера.
type StatefulOperator struct {
	name      string
	mu        sync.Mutex
	state     map[string]int
	snapshots map[int64]map[string]int
}

func NewOperator(name string) *StatefulOperator {
	return &StatefulOperator{
		name:      name,
		state:     make(map[string]int),
		snapshots: make(map[int64]map[string]int),
	}
}

// ProcessStream обрабатывает поток данных и корректно реагирует на Checkpoint Barrier.
func (op *StatefulOperator) ProcessStream(in <-chan StreamMessage) <-chan StreamMessage {
	out := make(chan StreamMessage, 100)

	go func() {
		defer close(out)
		for msg := range in {
			if msg.Type == MsgBarrier {
				// ПОЛУЧЕН БАРЬЕР: Фиксируем снимок состояния эпохи!
				op.takeSnapshot(msg.CheckpointID)
				// Пробрасываем барьер дальше по цепочке
				out <- msg
			} else {
				// Обычная обработка данных
				op.mu.Lock()
				op.state[msg.Key] += msg.Value
				op.mu.Unlock()
				out <- msg
			}
		}
	}()

	return out
}

func (op *StatefulOperator) takeSnapshot(checkpointID int64) {
	op.mu.Lock()
	defer op.mu.Unlock()

	// Асинхронный/Copy-on-Write снимок состояния
	snap := make(map[string]int, len(op.state))
	for k, v := range op.state {
		snap[k] = v
	}
	op.snapshots[checkpointID] = snap

	fmt.Printf(" 📸 [CHECKPOINT %d] Оператор '%s' зафиксировал согласованный снимок! Ключей: %d\n",
		checkpointID, op.name, len(snap))
}

func main() {
	op1 := NewOperator("FilterOperator")
	op2 := NewOperator("AggregatorOperator")

	sourceChan := make(chan StreamMessage, 20)

	// Собираем конвейер
	stage1 := op1.ProcessStream(sourceChan)
	stage2 := op2.ProcessStream(stage1)

	// Запускаем чтение финала
	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		for msg := range stage2 {
			if msg.Type == MsgBarrier {
				fmt.Printf(" ✅ [BARRIER COMPLETED] Checkpoint %d успешно прошел весь конвейер!\n", msg.CheckpointID)
			}
		}
	}()

	// Подаем данные
	sourceChan <- StreamMessage{Type: MsgData, Key: "user_a", Value: 10}
	sourceChan <- StreamMessage{Type: MsgData, Key: "user_b", Value: 25}

	// Координатор пускает в поток Checkpoint Barrier #101
	time.Sleep(10 * time.Millisecond)
	sourceChan <- StreamMessage{Type: MsgBarrier, CheckpointID: 101}

	// Данные следующей эпохи идут сразу следом без паузы!
	sourceChan <- StreamMessage{Type: MsgData, Key: "user_a", Value: 5}
	sourceChan <- StreamMessage{Type: MsgData, Key: "user_c", Value: 50}

	close(sourceChan)
	wg.Wait()
}
"""
            }
        ],
        "under_the_hood": "Алгоритм ABS (Asynchronous Barrier Snapshotting) гарантирует, что состояние в снимке $S_n$ отражает результаты ровно тех событий, которые предшествовали барьеру $B_n$, и ни одного события после него. Если оператор имеет несколько входных каналов (например, после Shuffle), применяется выравнивание барьеров (Barrier Alignment): оператор приостанавливает вычитку из канала, приславшего барьер первым, и дожидается барьеров из остальных каналов, сохраняя консистентность.",
        "pitfalls": "При медленном сетевом I/O процесс Barrier Alignment может вызывать задержки (Backpressure). Для устранения лагов в современных версиях Flink применяется невыровненный чекпоинтинг (Unaligned Checkpoints): барьер обгоняет данные в буфере каналов, а содержимое самого буфера сохраняется в файл чекпоинта.",
        "interview_qa": "В: Как восстановить систему после аварии одного из серверов с помощью чекпоинта Чанди-Лэмпорта?\nО: При падении система останавливает вычитку из Kafka, откатывает оффсеты консьюмеров до оффсетов, сохраненных в последнем успешном чекпоинте $n$, загружает локальные состояния всех операторов из хранилища чекпоинта $n$ и возобновляет обработку. Это гарантирует восстановление без потери данных."
    },
    {
        "num": 17,
        "title": "Фреймворк Goka для Kafka на Go",
        "task": "Изучите и примените библиотеку `lovoo/goka`: разработайте компактную потоковую топологию с эмиттером (Emitter), процессором (Processor) и групповой таблицей состояния (Group Table). Покажите, как Goka абстрагирует подписку на партиции Kafka, локальный кэш на базе LevelDB/Pebble и архитектуру акторов для масштабируемой обработки событий.",
        "theory": "Библиотека **Goka** (разработка Lovoo) — это мощный компактный потоковый фреймворк для языка Go, вдохновленный Apache Kafka Streams и моделью акторов (Actor Model):\n1. **Emitter**: компонент, отправляющий строго типизированные сообщения в топик Kafka.\n2. **Processor Callback**: чистая функция `func(ctx goka.Context, msg interface{})`, вызываемая для каждого события определенного ключа.\n3. **Group Table & View**: локальное персистентное key-value состояние на базе LevelDB/Pebble, автоматически реплицируемое через Kafka Compacted Topics.\n4. **Акторная изоляция**: для одного ключа (например, `user_123`) вызовы процессора строго последовательны и потокобезопасны. Внутри функции можно вызывать `ctx.SetValue(...)` без ручных мьютексов!",
        "step_by_step": "1. Спроектируйте кодек сериализации (Codec) для типа `UserProfile`.\n2. Опишите потоковый процессор с групповой таблицей через интерфейсы Goka.\n3. Реализуйте функцию обработки событий с обновлением состояния `ctx.SetValue`.\n4. Продемонстрируйте концепцию материализованного представления (View) для чтения состояния из HTTP API.",
        "code_blocks": [
            {
                "filename": "goka_stream.go",
                "lang": "go",
                "code": r"""package main

import (
	"encoding/json"
	"fmt"
	"sync"
)

// UserStats — структура состояния в Group Table.
type UserStats struct {
	TotalClicks int `json:"total_clicks"`
	TotalScore  int `json:"total_score"`
}

// GokaContextMock симулирует интерфейс goka.Context для демонстрации акторной модели.
type GokaContextMock struct {
	key   string
	state *UserStats
}

func (c *GokaContextMock) Key() string {
	return c.key
}

func (c *GokaContextMock) Value() interface{} {
	return c.state
}

func (c *GokaContextMock) SetValue(v interface{}) {
	c.state = v.(*UserStats)
}

// UserEvent — входное событие из топика Kafka.
type UserEvent struct {
	Clicks int
	Score  int
}

// ClickProcessorCallback — обработчик Goka в стиле Kafka Streams.
func ClickProcessorCallback(ctx *GokaContextMock, msg UserEvent) {
	var stats *UserStats
	if val := ctx.Value(); val != nil {
		stats = val.(*UserStats)
	} else {
		stats = &UserStats{}
	}

	// Инкрементальное обновление состояния актора (строго последовательно по ключу!)
	stats.TotalClicks += msg.Clicks
	stats.TotalScore += msg.Score

	ctx.SetValue(stats)

	fmt.Printf(" [GOKA PROCESSOR] Ключ: %s -> Обновлено состояние: Кликов=%d, Счет=%d\n",
		ctx.Key(), stats.TotalClicks, stats.TotalScore)
}

func main() {
	fmt.Println("=== Потоковая обработка на базе модели акторов Goka ===")

	// Имитация таблицы состояния акторов (Group Table на LevelDB)
	storage := make(map[string]*UserStats)
	var mu sync.Mutex

	processEvent := func(userKey string, evt UserEvent) {
		mu.Lock()
		defer mu.Unlock()

		ctx := &GokaContextMock{
			key:   userKey,
			state: storage[userKey],
		}

		ClickProcessorCallback(ctx, evt)
		storage[userKey] = ctx.state
	}

	// Серия входящих сообщений
	processEvent("user_alex", UserEvent{Clicks: 1, Score: 10})
	processEvent("user_olga", UserEvent{Clicks: 5, Score: 50})
	processEvent("user_alex", UserEvent{Clicks: 2, Score: 25})

	fmt.Println("\nФинальное материализованное представление (View):")
	for k, v := range storage {
		data, _ := json.Marshal(v)
		fmt.Printf("   Пользователь %s: %s\n", k, string(data))
	}
}
"""
            }
        ],
        "under_the_hood": "Под капотом Goka распределяет партиции Kafka между экземплярами сервиса. Для каждой партиции создается отдельный локальный инстанс LevelDB/Pebble. Все обновления состояния записываются в локальную БД и одновременно транслируются в топик Kafka (`<group>-table`). Это гарантирует восстановление состояния любого пода при миграциях в Kubernetes.",
        "pitfalls": "Категорически запрещено внутри процессора Goka выполнять долгие блокирующие операции или сетевые запросы без таймаутов, так как это заблокирует обработку всех сообщений, приходящих в данную партицию Kafka.",
        "interview_qa": "В: Чем подход Goka отличается от классического чтения Kafka через sarama/kafka-go?\nО: При обычном чтении через sarama разработчик вынужден вручную управлять потокобезопасностью состояния, дедупликацией, синхронизацией оффсетов и локальным кэшем. Goka берет на себя всю сложность Stateful Stream Processing, предоставляя высокоуровневый декларативный DSL с локальным LSM-хранилищем и авто-восстановлением."
    },
    {
        "num": 18,
        "title": "Партиционирование по ключу и строгий порядок обработки",
        "task": "Спроектируйте распределение событий по воркерам: события с одинаковым бизнес-ключом (`user_id` или `sensor_id`) обязаны попадать в один и тот же воркер и обрабатываться строго последовательно. Реализуйте роутинг событий по алгоритму консистентного хэширования (`fnv.New32a(key) % num_workers`) с защитой от изменения порядка и race conditions.",
        "theory": "В высоконагруженных потоках (100k RPS) обработка распараллеливается на пул воркеров. Однако параллелизм не должен нарушать хронологию событий одной сущности:\n- Если от пользователя пришли события: 1) Создать заказ -> 2) Оплатить заказ -> 3) Отменить заказ.\n- При случайном распределении по горутинам событие 'Оплатить' может обогнать 'Создать', вызвав ошибку рассинхронизации!\n\n**Key-Based Partitioning (Партиционирование по ключу)**:\n1. Для каждого события извлекается ключ маршрутизации (`Key`).\n2. Вычисляется детерминированный хэш: `workerID = Hash(Key) % NumWorkers`.\n3. Все события с данным ключом направляются в **один и тот же выделенный канал воркера**.\n4. Это гарантирует строгий порядок (FIFO) и устраняет необходимость использования мьютексов между воркерами!",
        "step_by_step": "1. Реализуйте хэш-функцию распределения `HashPartition(key string, numPartitions int) int`.\n2. Создайте N независимых горутин-воркеров, каждая со своим входным каналом.\n3. Реализуйте роутер (Dispatcher), направляющий события в соответствующий канал.\n4. Продемонстрируйте строгий хронологический порядок обработки событий одного пользователя.",
        "code_blocks": [
            {
                "filename": "partitioning.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"hash/fnv"
	"sync"
	"time"
)

type UserStreamEvent struct {
	UserID    string
	SeqNum    int
	Action    string
	Timestamp time.Time
}

// HashPartition детерминированно сопоставляет ключ с номером партиции.
func HashPartition(key string, numPartitions int) int {
	h := fnv.New32a()
	_, _ = h.Write([]byte(key))
	return int(h.Sum32()) % numPartitions
}

func main() {
	const numPartitions = 4
	workerChannels := make([]chan UserStreamEvent, numPartitions)
	var wg sync.WaitGroup

	// Запуск 4 независимых воркеров (каждый обрабатывает свою партицию)
	for i := 0; i < numPartitions; i++ {
		workerChannels[i] = make(chan UserStreamEvent, 100)
		wg.Add(1)

		go func(partitionID int, ch <-chan UserStreamEvent) {
			defer wg.Done()
			for e := range ch {
				fmt.Printf(" [WORKER %d] Key: %-10s | Seq: #%d | Action: %s\n",
					partitionID, e.UserID, e.SeqNum, e.Action)
				// Имитация полезной работы
				time.Sleep(10 * time.Millisecond)
			}
		}(i, workerChannels[i])
	}

	// Поток событий разных пользователей с порядковыми номерами
	events := []UserStreamEvent{
		{UserID: "usr_alice", SeqNum: 1, Action: "CartCreated"},
		{UserID: "usr_bob", SeqNum: 1, Action: "Login"},
		{UserID: "usr_alice", SeqNum: 2, Action: "ItemAdded"},
		{UserID: "usr_charlie", SeqNum: 1, Action: "Search"},
		{UserID: "usr_alice", SeqNum: 3, Action: "Checkout"},
		{UserID: "usr_bob", SeqNum: 2, Action: "Logout"},
	}

	fmt.Println("=== Маршрутизация событий по хэш-партициям ===")
	for _, e := range events {
		partition := HashPartition(e.UserID, numPartitions)
		workerChannels[partition] <- e
	}

	// Закрываем каналы и ждем завершения
	for _, ch := range workerChannels {
		close(ch)
	}
	wg.Wait()
	fmt.Println("✅ Все события обработаны с гарантией строгого сохранения порядка!")
}
"""
            }
        ],
        "under_the_hood": "Этот подход лежит в основе архитектуры Apache Kafka: брокер гарантирует строгий порядок сообщений ТОЛЬКО в пределах одной партиции (`TopicPartition`). Когда продюсер использует стандартный партиционер (`Murmur2` или `CRC32`), все события с одинаковым ключом попадают в одну партицию и последовательно вычитываются одним консьюмером группы.",
        "pitfalls": "Проблема горячего ключа (Hot Key / Data Skew): если один ключ (например, аккаунт агрегатора или крупного ритейлера) генерирует 50% всех событий системы, воркер этой партиции будет перегружен на 100%, а остальные 3 воркера будут простаивать. Для горячих ключей применяют технику солирования (Key Salting: `key + '_' + rand(0, 3)`), если для части операций строгий порядок не критичен.",
        "interview_qa": "В: Что произойдет со строгим порядком обработки, если изменить количество партиций с 4 до 8 на лету?\nО: Изменится знаменатель в формуле `Hash(Key) % N`. События одного и того же ключа начнут попадать в другие партиции, что может привести к параллельной обработке старых и новых событий и нарушению хронологии. Поэтому изменение количества партиций требует миграции с временной паузой или дренажем конвейера."
    },
    {
        "num": 19,
        "title": "Адаптивное обратное давление (Backpressure)",
        "task": "Если стадия агрегации не справляется со входящим потоком (100k событий/сек), буферы каналов переполняются, вызывая неконтролируемый рост памяти. Реализуйте механизм обратного давления (Backpressure): при заполнении входного канала воркера более чем на 80%, читатель временно приостанавливает вычитку или замедляет темп запросов.",
        "theory": "Проблема **Fast Producer, Slow Consumer** — главная причина падений высоконагруженных микросервисов по OOM (Out Of Memory):\n- Продюсер шлет 100 000 сообщений в секунду.\n- Воркер успевает обработать только 20 000 в секунду.\n- Разница оседает в буферах каналов и оперативной памяти, пока процесс не уничтожит ядро ОС.\n\n**Механизм Backpressure (Обратное давление)**:\n1. **Естественное противодавление Go**: небуферизованный канал `make(chan T)` или переполненный буферизованный канал `make(chan T, 100)` блокирует операцию отправки `ch <- data` на стороне продюсера.\n2. **Управление скоростью (Rate Throttling)**: читатель измеряет уровень заполненности канала `len(ch) / cap(ch)`. Если он превышает 80%, процессор вызывает `Pause()` на партиции Kafka, давая воркерам время разобрать очередь.",
        "step_by_step": "1. Спроектируйте конвейер с медленным воркером (Slow Consumer).\n2. Реализуйте мониторинг заполнения входного канала.\n3. Реализуйте логику адаптивной задержки (Throttling) или переключения флага `isPaused`.\n4. Продемонстрируйте стабилизацию потребления памяти.",
        "code_blocks": [
            {
                "filename": "backpressure.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"
)

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	const queueCapacity = 10
	queue := make(chan int, queueCapacity)

	// Медленный консьюмер: обрабатывает 1 элемент за 50 мс (макс 20 элементов/сек)
	go func() {
		for item := range queue {
			time.Sleep(50 * time.Millisecond)
			_ = item
		}
	}()

	// Быстрый продюсер с адаптивным Backpressure
	produced := 0
	pausedCount := 0

	for {
		select {
		case <-ctx.Done():
			fmt.Printf("\nИтог: Создано %d элементов | Срабатываний Backpressure: %d раз\n",
				produced, pausedCount)
			return
		default:
			// Проверяем заполненность буфера (порог 80%)
			currentLoad := float64(len(queue)) / float64(queueCapacity)
			if currentLoad >= 0.8 {
				pausedCount++
				fmt.Printf(" 🛑 [BACKPRESSURE] Очередь заполнена на %.0f%% (%d/%d). Приостановка чтения на 30 мс...\n",
					currentLoad*100, len(queue), queueCapacity)
				time.Sleep(30 * time.Millisecond)
				continue
			}

			// Штатная отправка
			queue <- produced
			produced++
			time.Sleep(5 * time.Millisecond) // Продюсер пытается генерировать 200 событий/сек!
		}
	}
}
"""
            }
        ],
        "under_the_hood": "В сетевых библиотеках (TCP / HTTP/2 / gRPC) обратное давление реализуется через размер скользящего окна приема (TCP Receive Window / HTTP/2 Flow Control Window). Когда воркер перестает читать данные из сокета, окно приема схлопывается до 0 байт (Zero Window), и операционная система отправителя аппаратно блокирует вызовы `write()`, предотвращая потерю пакетов.",
        "pitfalls": "Никогда не используйте каналы с бесконечным ростом буфера (Unbounded Channel на связных списках) в продакшене без жесткого лимита памяти! Неограниченный буфер скрывает проблему перегрузки системы до тех пор, пока сервер не упадет с паникой out of memory.",
        "interview_qa": "В: Как механизм Backpressure реализован в библиотеке sarama для Apache Kafka?\nО: В sarama консьюмер запрашивает данные батчами (`Fetch.MinBytes`, `MaxWaitTime`). Если внутренний канал воркера переполняется, консьюмер просто не отправляет следующий gRPC-запрос `FetchRequest` брокеру Kafka. Сообщения остаются надежно лежать на диске кластера Kafka, пока локальный сервис не освободит свои очереди."
    },
    {
        "num": 20,
        "title": "Потоковое обнаружение аномалий (Z-Score / Moving StdDev)",
        "task": "Напишите алгоритм детектирования аномалий во временных рядах телеметрии датчиков давления: поддерживайте скользящее среднее и стандартное отклонение (алгоритм Welford в скользящем окне). Если входящее значение отклоняется более чем на $3\\sigma$ ($|Z| > 3$), немедленно генерируйте событие тревоги `AnomalyDetectedEvent`.",
        "theory": "Обнаружение аномалий в реальном времени (Real-Time Anomaly Detection) — критическая задача мониторинга HighLoad-систем, телеметрии IoT и антифрода.\n\n**Метрика Z-Score (Z-оценка)**:\nПоказывает, на сколько стандартных отклонений $\\sigma$ значение $x$ удалено от математического ожидания $\\mu$:\n$$Z = \\frac{x - \\mu}{\\sigma}$$\n- Согласно правилу трех сигм (Three-Sigma Rule), для нормально распределенных величин 99.73% значений лежат в интервале $[\\mu - 3\\sigma, \\mu + 3\\sigma]$.\n- Если $|Z| > 3$, вероятность случайного всплеска составляет менее 0.27% — это математически строгое определение аномалии (выброса / фрода / аварии датчика)!",
        "step_by_step": "1. Реализуйте кольцевой буфер (Ring Buffer) на 100 точек для хранения истории скользящего окна.\n2. При поступлении нового измерения пересчитывайте скользящее среднее и $\\sigma$.\n3. Вычисляйте $Z = (x - \\mu) / \\sigma$.\n4. При $|Z| > 3.0$ генерируйте структурированный алерт `AnomalyAlert`.",
        "code_blocks": [
            {
                "filename": "anomaly_detection.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"math"
)

type SensorReading struct {
	SensorID  string
	Pressure  float64
	Timestamp int64
}

type AnomalyAlert struct {
	SensorID float64
	Value    float64
	ZScore   float64
	Mean     float64
	StdDev   float64
}

// MovingZScoreDetector детектирует аномалии в скользящем окне N элементов.
type MovingZScoreDetector struct {
	windowSize int
	values     []float64
	index      int
	isFull     bool
}

func NewDetector(size int) *MovingZScoreDetector {
	return &MovingZScoreDetector{
		windowSize: size,
		values:     make([]float64, size),
	}
}

func (d *MovingZScoreDetector) AddAndCheck(x float64) (bool, float64, float64, float64) {
	// Если окно еще не набрало минимальную статистику (хотя бы 20 точек)
	if !d.isFull && d.index < 20 {
		d.values[d.index] = x
		d.index++
		if d.index == d.windowSize {
			d.isFull = true
			d.index = 0
		}
		return false, 0, 0, 0
	}

	// 1. Вычисляем текущее среднее и стандартное отклонение по заполненному окну
	count := d.windowSize
	if !d.isFull {
		count = d.index
	}

	sum := 0.0
	for i := 0; i < count; i++ {
		sum += d.values[i]
	}
	mean := sum / float64(count)

	varianceSum := 0.0
	for i := 0; i < count; i++ {
		varianceSum += math.Pow(d.values[i]-mean, 2)
	}
	stdDev := math.Sqrt(varianceSum / float64(count))

	// Защита от деления на ноль при строго константных значениях
	if stdDev < 1e-6 {
		stdDev = 1e-6
	}

	// 2. Расчет Z-Score
	zScore := (x - mean) / stdDev

	// 3. Записываем новое значение в кольцевой буфер
	d.values[d.index] = x
	d.index = (d.index + 1) % d.windowSize
	if d.index == 0 {
		d.isFull = true
	}

	// 4. Проверяем правило трех сигм (|Z| > 3.0)
	isAnomaly := math.Abs(zScore) > 3.0
	return isAnomaly, zScore, mean, stdDev
}

func main() {
	detector := NewDetector(50) // Окно из 50 измерений

	fmt.Println("=== Потоковое обнаружение аномалий (Z-Score) ===")

	// 1. Подаем 30 нормальных измерений давления (около 100.0 ± 1.0 бар)
	for i := 1; i <= 30; i++ {
		val := 100.0 + (float64(i%5) - 2.0)*0.5
		detector.AddAndCheck(val)
	}

	// 2. Подаем проверочные значения
	testReadings := []float64{101.2, 100.5, 125.0 /* АНОМАЛИЯ! */, 99.8, 45.0 /* АНОМАЛИЯ! */}

	for _, val := range testReadings {
		isAnomaly, z, mean, std := detector.AddAndCheck(val)
		if isAnomaly {
			fmt.Printf("🚨 [АНОМАЛИЯ ОБНАРУЖЕНА!] Значение: %.1f | Z-Score: %+.2f | База: Mean=%.2f, StdDev=%.2f\n",
				val, z, mean, std)
		} else {
			fmt.Printf("✅ [НОРМА] Значение: %.1f | Z-Score: %+.2f\n", val, z)
		}
	}
}
"""
            }
        ],
        "under_the_hood": "Алгоритм Z-Score работает со сложностью $O(1)$ при использовании инкрементального пересчета сумм $\sum x$ и $\sum x^2$ в кольцевом буфере. При поступлении нового элемента из сумм вычитается старый вытесняемый элемент и прибавляется новый, исключая полный проход по массиву окна.",
        "pitfalls": "Если в потоке происходит скачкообразный сдвиг нормы (Concept Drift, например, перевод оборудования на новый технологический режим с 100 до 200 бар), все последующие точки будут признаваться аномалиями, пока окно не заполнится новыми значениями. Для таких сценариев применяют адаптивный экспоненциальный сглаживатель (EWMA) или алгоритм CUSUM.",
        "interview_qa": "В: Почему в потоковом анализе финансовых транзакций часто используют Robust Z-Score на базе MAD (Median Absolute Deviation) вместо обычного Z-Score?\nО: Классическое среднее и стандартное отклонение чрезвычайно чувствительны к экстремальным выбросам: один гигантский платеж на миллиард рублей раздует $\sigma$, из-за чего последующие реальные аномалии перестанут детектироваться. Оценка MAD использует медиану вместо среднего, что делает алгоритм устойчивым к одиночным катастрофическим выбросам."
    },
    {
        "num": 21,
        "title": "Построение направленного ациклического графа (DAG) обработки",
        "task": "Создайте декларативный fluent-DSL для описания потоковой топологии на Go: `topology.Source('orders').Filter(isPaid).Map(calcMetrics).Sink('clickhouse')`. Реализуйте валидацию топологии на отсутствие циклов (Acyclic Validation) и автоматическую компиляцию графа операторов в работающую сеть каналов и горутин.",
        "theory": "Во всех ведущих движках потоковой обработки (Apache Flink, Spark Structured Streaming, Kafka Streams) логика задается не ручным спавном горутин, а в виде **Directed Acyclic Graph (DAG)**:\n- **Source Nodes**: узлы генерации/чтения данных.\n- **Transform Nodes**: промежуточные фильтры, мапперы, оконные агрегаторы.\n- **Sink Nodes**: терминальные узлы выгрузки.\n\nПреимущества топологического DAG:\n1. **Декларативность**: четкое визуальное описание конвейера.\n2. **Оптимизация компилятором**: возможность объединения нескольких операций (Operator Chaining / Fusion) в одну горутину для устранения накладных расходов каналов.\n3. **Валидация**: проверка отсутствия взаимных циклов (дедлоков) до запуска конвейера.",
        "step_by_step": "1. Спроектируйте структуры `Node`, `Edge` и `TopologyBuilder`.\n2. Реализуйте fluent API: `Source()`, `Filter()`, `Map()`, `Sink()`.\n3. Напишите алгоритм топологической сортировки Кана (Kahn's Algorithm) для проверки ацикличности.\n4. Скомпилируйте и запустите граф в памяти.",
        "code_blocks": [
            {
                "filename": "dag_topology.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

type NodeKind string

const (
	KindSource    NodeKind = "Source"
	KindFilter    NodeKind = "Filter"
	KindTransform NodeKind = "Transform"
	KindSink      NodeKind = "Sink"
)

type TopologyNode struct {
	Name string
	Kind NodeKind
}

// TopologyBuilder предоставляет Fluent DSL для построения потокового DAG.
type TopologyBuilder struct {
	nodes []TopologyNode
}

func NewTopology() *TopologyBuilder {
	return &TopologyBuilder{}
}

func (t *TopologyBuilder) Source(name string) *TopologyBuilder {
	t.nodes = append(t.nodes, TopologyNode{Name: name, Kind: KindSource})
	return t
}

func (t *TopologyBuilder) Filter(name string) *TopologyBuilder {
	t.nodes = append(t.nodes, TopologyNode{Name: name, Kind: KindFilter})
	return t
}

func (t *TopologyBuilder) Map(name string) *TopologyBuilder {
	t.nodes = append(t.nodes, TopologyNode{Name: name, Kind: KindTransform})
	return t
}

func (t *TopologyBuilder) Sink(name string) *TopologyBuilder {
	t.nodes = append(t.nodes, TopologyNode{Name: name, Kind: KindSink})
	return t
}

func (t *TopologyBuilder) Validate() error {
	if len(t.nodes) < 2 {
		return fmt.Errorf("топология должна содержать минимум Source и Sink")
	}
	if t.nodes[0].Kind != KindSource {
		return fmt.Errorf("первым узлом обязан быть Source")
	}
	if t.nodes[len(t.nodes)-1].Kind != KindSink {
		return fmt.Errorf("последним узлом обязан быть Sink")
	}
	return nil
}

// Run компилирует декларативный DAG в цепочку каналов Go.
func (t *TopologyBuilder) Run(ctx context.Context, inputData []int) {
	if err := t.Validate(); err != nil {
		panic(err)
	}

	fmt.Println("=== Запуск скомпилированной DAG-топологии ===")
	for i, n := range t.nodes {
		fmt.Printf("   Шаг %d: [%s] '%s'\n", i+1, n.Kind, n.Name)
	}

	// Компиляция: Source
	c1 := make(chan int, 10)
	go func() {
		defer close(c1)
		for _, x := range inputData {
			c1 <- x
		}
	}()

	// Компиляция: Filter (только четные)
	c2 := make(chan int, 10)
	go func() {
		defer close(c2)
		for x := range c1 {
			if x%2 == 0 {
				c2 <- x
			}
		}
	}()

	// Компиляция: Transform (умножение на 10)
	c3 := make(chan int, 10)
	go func() {
		defer close(c3)
		for x := range c2 {
			c3 <- x * 10
		}
	}()

	// Компиляция: Sink
	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		for x := range c3 {
			fmt.Printf(" [DAG SINK -> ClickHouse] Записано значение: %d\n", x)
		}
	}()

	wg.Wait()
}

func main() {
	topo := NewTopology().
		Source("kafka-raw-orders").
		Filter("discard-odd-items").
		Map("multiply-by-ten").
		Sink("clickhouse-metrics")

	topo.Run(context.Background(), []int{1, 2, 3, 4, 5, 6})
}
"""
            }
        ],
        "under_the_hood": "В промышленных компиляторах топологий (например, Flink JobGraph) перед запуском выполняется оптимизация Fusion (Operator Chaining): если два оператора `Filter` и `Map` имеют параллелизм $1:1$ и не требуют перетасовки данных (No Shuffle), компилятор объединяет их в одну горутину `out <- mapFn(filterFn(in))` без передачи через промежуточный канал, что снижает нагрузку на планировщик Go и устраняет переключения контекста.",
        "pitfalls": "Опасайтесь циклических зависимостей в графе. Если узел $A$ шлет данные узлу $B$, а узел $B$ возвращает часть сообщений узлу $A$ через синхронные каналы, система гарантированно войдет в дедлок (Goroutine Deadlock). Потоковый граф обязан быть строго ациклическим (DAG).",
        "interview_qa": "В: В чем разница между физическим планом выполнения (Execution Plan) и логическим графом (Logical DAG)?\nО: **Logical DAG** описывает бизнес-преобразования (Filter, Join, GroupBy) без привязки к инфраструктуре. **Execution Plan** учитывает физический параллелизм: один логический узел 'Map' компилируется в 64 независимые параллельные горутины (Tasks), привязанные к конкретным партициям брокера сообщений."
    },
    {
        "num": 22,
        "title": "Оконные триггеры (Window Triggers) и ранний сброс (Early Emission)",
        "task": "В длительных окнах (суточное окно подсчета выручки) клиенты не хотят ждать конца суток для получения метрик. Реализуйте составной оконный триггер: окно сбрасывает промежуточные результаты каждые 5 минут ИЛИ при накоплении каждых 10 000 новых событий, а финальный результат публикует по достижении водяного знака времени суток.",
        "theory": "По умолчанию оконные агрегации выдают результат ровно один раз — при закрытии окна по водяному знаку ($Watermark \ge WindowEnd$). Для 1-минутного окна это приемлемо. Но для 1-дневного или 30-дневного окна ожидание финального результата делает аналитику бесполезной для оперативного реагирования.\n\n**Оконные триггеры (Window Triggers)** управляют тем, *когда* именно окно должно сбросить промежуточные результаты:\n1. **EventTimeTrigger**: срабатывает, когда водяной знак проходит дедлайн окна (стандартное поведение).\n2. **ProcessingTimeTrigger (Early Emission)**: срабатывает каждые $N$ секунд физического времени, сбрасывая спекулятивную оценку текущей суммы.\n3. **CountTrigger**: срабатывает, как только внутри окна накопилось $M$ новых событий.\n4. **Composite Trigger**: объединение через `OR`: сбросить результат, если прошло 5 минут ИЛИ пришло 10 000 событий!",
        "step_by_step": "1. Спроектируйте структуру `TriggerState` (EventCount, LastEmitTime, Accumulator).\n2. Реализуйте функцию проверки триггера `ShouldFire(event, watermark, now)`.\n3. Реализуйте раннюю эмиссию (Early Emission) промежуточных значений.\n4. Продемонстрируйте корректную финализацию окна при наступлении водяного знака.",
        "code_blocks": [
            {
                "filename": "triggers.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"time"
)

type SalesEvent struct {
	Amount    float64
	Timestamp time.Time
}

// EarlyFiringWindow реализует ранний сброс метрик по порогу количества или таймеру.
type EarlyFiringWindow struct {
	windowStart time.Time
	windowEnd   time.Time
	sum         float64
	countSinceEmit int
	maxBatchCount  int
}

func NewDailyWindow(start time.Time) *EarlyFiringWindow {
	return &EarlyFiringWindow{
		windowStart:   start,
		windowEnd:     start.Add(24 * time.Hour),
		maxBatchCount: 3, // Для наглядности демо: сброс каждые 3 события
	}
}

func (w *EarlyFiringWindow) Add(e SalesEvent, watermark time.Time) {
	w.sum += e.Amount
	w.countSinceEmit++

	// Проверка Триггера 1: Финальное закрытие окна по Водяному Знаку
	if !watermark.Before(w.windowEnd) {
		fmt.Printf(" 🔔 [FINAL EMISSION] Сутки закрыты! Финальная выручка: %.2f руб\n", w.sum)
		return
	}

	// Проверка Триггера 2: Ранний сброс (Early Trigger) по накоплению батча
	if w.countSinceEmit >= w.maxBatchCount {
		fmt.Printf(" ⚡ [EARLY EMIT] Промежуточный сброс (накоплено %d покупок): Текущая выручка: %.2f руб\n",
			w.countSinceEmit, w.sum)
		w.countSinceEmit = 0
	}
}

func main() {
	t0 := time.Date(2026, 9, 8, 0, 0, 0, 0, time.UTC)
	window := NewDailyWindow(t0)

	fmt.Println("=== Демонстрация оконных триггеров и Early Emission ===")

	// Покупки в течение дня
	window.Add(SalesEvent{Amount: 1000, Timestamp: t0.Add(1 * time.Hour)}, t0.Add(2*time.Hour))
	window.Add(SalesEvent{Amount: 2500, Timestamp: t0.Add(3 * time.Hour)}, t0.Add(4*time.Hour))
	// 3-я покупка активирует Early Emission!
	window.Add(SalesEvent{Amount: 1500, Timestamp: t0.Add(5 * time.Hour)}, t0.Add(6*time.Hour))

	window.Add(SalesEvent{Amount: 4000, Timestamp: t0.Add(10 * time.Hour)}, t0.Add(11*time.Hour))
	window.Add(SalesEvent{Amount: 3000, Timestamp: t0.Add(15 * time.Hour)}, t0.Add(16*time.Hour))
	// 6-я покупка снова активирует Early Emission!
	window.Add(SalesEvent{Amount: 2000, Timestamp: t0.Add(20 * time.Hour)}, t0.Add(21*time.Hour))

	// Наступает конец суток: Watermark >= WindowEnd
	window.Add(SalesEvent{Amount: 500, Timestamp: t0.Add(23 * time.Hour)}, t0.Add(24*time.Hour))
}
"""
            }
        ],
        "under_the_hood": "При использовании ранней эмиссии downstream-системы получают несколько сообщений для одного и того же интервала окна. Поэтому сообщения раннего сброса помечаются флагом `IsSpeculative: true`, а финальное сообщение — `IsFinal: true`. В хранилищах данных (ClickHouse/PostgreSQL) записи обновляются через `UPSERT` по ключу окна `window_start`.",
        "pitfalls": "Слишком частый ранний сброс (например, на каждое отдельное событие) превратит оконную агрегацию в шторм сетевых запросов к базе данных, нивелируя всю пользу буферизации.",
        "interview_qa": "В: Что такое Trigger Purge в потоковых окнах?\nО: Метод триггера может возвращать не только команду `FIRE` (сбросить результат), но и `FIRE_AND_PURGE` (сбросить результат и полностью удалить состояние окна из памяти). Это необходимо, например, в триггерах экстренной остановки торгов при обнаружении опасной аномалии."
    },
    {
        "num": 23,
        "title": "Компактификация и вытеснение локального состояния",
        "task": "Если сервис отслеживает сессии миллиарда пользователей, локальный State Store на диске неизбежно переполнится. Настройте политику устаревания (State TTL): напишите фоновый сборщик (Cleaner / Compactor), который удаляет ключи пользователей, не проявлявших активности более 7 дней, и запускает управляемую компактификацию LSM-хранилища.",
        "theory": "Локальное состояние потокового процессора (Embedded RocksDB/Pebble) растет с каждым новым ключом. Если ключ — это `user_id`, то со временем в базе скопятся сотни миллионов неактивных 'мертвых' пользователей, покинувших приложение годы назад.\n\nДля поддержания стабильного размера базы применяется **State Time-To-Live (State TTL)**:\n1. При каждой записи к значению прикрепляется метка времени последнего обновления (`LastAccessTimestamp`).\n2. **Read-Time Filtering**: если при вызове `Get(key)` выясняется, что $T_{current} - T_{access} > TTL$, запись считается несуществующей и удаляется.\n3. **Background Cleanup**: фоновый поток периодически сканирует диапазон ключей (Range Scan) и удаляет протухшие записи.\n4. **LSM Compaction**: удаление в LSM создает маркеры удаления (Tombstones). Для физического освобождения места на диске вызывается принудительная компактификация диапазонов (`CompactRange`).",
        "step_by_step": "1. Спроектируйте структуру обертки `TTLRecord[T]` с меткой `ExpiresAt`.\n2. Реализуйте проверку срока жизни при чтении.\n3. Напишите фоновую горутину сборщика мусора состояния (State Sweeper).\n4. Продемонстрируйте очистку устаревших ключей и сохранение активных.",
        "code_blocks": [
            {
                "filename": "state_ttl.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
	"time"
)

type TTLWrapper struct {
	Value     string
	ExpiresAt time.Time
}

// ManagedStateStore управляет жизненным циклом и вытеснением устаревших ключей.
type ManagedStateStore struct {
	mu    sync.RWMutex
	store map[string]TTLWrapper
	ttl   time.Duration
}

func NewManagedStateStore(ttl time.Duration) *ManagedStateStore {
	return &ManagedStateStore{
		store: make(map[string]TTLWrapper),
		ttl:   ttl,
	}
}

func (s *ManagedStateStore) Put(key, value string, now time.Time) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.store[key] = TTLWrapper{
		Value:     value,
		ExpiresAt: now.Add(s.ttl),
	}
}

func (s *ManagedStateStore) Get(key string, now time.Time) (string, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	item, exists := s.store[key]
	if !exists {
		return "", false
	}
	// Если ключ уже протух
	if now.After(item.ExpiresAt) {
		return "", false
	}
	return item.Value, true
}

// RunCompaction имитирует фоновую компактификацию и удаление протухших записей.
func (s *ManagedStateStore) RunCompaction(now time.Time) int {
	s.mu.Lock()
	defer s.mu.Unlock()

	evicted := 0
	for k, v := range s.store {
		if now.After(v.ExpiresAt) {
			delete(s.store, k)
			evicted++
		}
	}
	return evicted
}

func main() {
	store := NewManagedStateStore(7 * 24 * time.Hour) // TTL 7 дней
	baseTime := time.Date(2026, 9, 1, 0, 0, 0, 0, time.UTC)

	// Добавляем пользователей
	store.Put("user_active", "StateData_A", baseTime)
	store.Put("user_abandoned", "StateData_B", baseTime)

	// Прошло 3 дня: активный пользователь обновил состояние
	store.Put("user_active", "StateData_A_Updated", baseTime.Add(3*24*time.Hour))

	fmt.Println("=== Проверка состояния спустя 8 дней (09 сентября 2026) ===")
	checkTime := baseTime.Add(8 * 24 * time.Hour)

	valActive, okActive := store.Get("user_active", checkTime)
	valAbandoned, okAbandoned := store.Get("user_abandoned", checkTime)

	fmt.Printf("user_active: найден? %v (Значение: %s)\n", okActive, valActive)
	fmt.Printf("user_abandoned: найден? %v (Истек срок TTL 7 дней)\n", okAbandoned, valAbandoned)

	evicted := store.RunCompaction(checkTime)
	fmt.Printf("🧹 Компактификация хранилища: удалено %d устаревших записей.\n", evicted)
}
"""
            }
        ],
        "under_the_hood": "В реальных LSM-движках (RocksDB / Pebble) вытеснение по TTL реализуется через плагины `CompactionFilter`. Во время слияния файлов SSTable на диске фильтр на лету инспектирует заголовок записи. Если $Timestamp + TTL < CurrentTime$, запись просто отбрасывается и не записывается в результирующий файл нового уровня, освобождая дисковое пространство абсолютно без накладных расходов на чтение.",
        "pitfalls": "При удалении миллионов записей в LSM-дереве создаются 'надгробия' (Tombstones). Если после этого выполнить диапазонное сканирование (Range Scan), итератор будет медленно перебирать миллионы удаленных надгробий, вызывая деградацию производительности. Обязательно вызывайте ручную компактификацию после массовых удалений.",
        "interview_qa": "В: Чем отличается TTL на базе Event Time от TTL на базе Processing Time?\nО: TTL на базе **Processing Time** вытесняет запись по часам сервера (например, 'не было запросов 7 суток'). TTL на базе **Event Time** привязан к продвижению водяного знака. При повторном историческом прогоне (Replay) данных за 2020 год TTL по Processing Time удалит все данные мгновенно, тогда как Event Time TTL отработает корректно по виртуальным часам."
    },
    {
        "num": 24,
        "title": "Replay потока и повторный расчет аналитики",
        "task": "В формулу расчета аналитических метрик закралась ошибка. Реализуйте процедуру безопасного повторного прогона (Stream Replay / Backfill): новый экземпляр консьюмера подключается к брокеру Kafka с оффсета за прошлую неделю, рассчитывает исправленные метрики в отдельную таблицу `metrics_recalculated`, после чего оператор переключает чтение без потери данных и даунтайма.",
        "theory": "Главное преимущество лог-ориентированных брокеров (Apache Kafka, Redpanda) перед традиционными очередями (RabbitMQ) — **персистентность данных (Retention)**:\n- Сообщения не удаляются после прочтения консьюмером!\n- Они хранятся на диске заданный срок (Retention Period: 7 дней, 30 дней или вечно).\n- В любой момент времени консьюмер может переставить свой указатель (Offset) назад во времени и заново проиграть весь поток событий с самого начала.\n\nПаттерн **Stream Replay / Dual-Track Migration**:\n1. Разработчики исправляют баг в коде агрегации.\n2. Запускается независимый Consumer Group `analytics-v2` с оффсетом за нужную дату (`SeekToTimestamp`).\n3. Версия v2 пишет результат в параллельную таблицу `analytics_v2`.\n4. Когда версия v2 догоняет текущий реальный трафик (Lag = 0), трафик дашбордов и API переключается на таблицу v2, а старая версия v1 выключается.",
        "step_by_step": "1. Спроектируйте интерфейс `OffsetResetter` для перемещения указателя потока.\n2. Смоделируйте журнал сообщений брокера с оффсетами 0..N.\n3. Реализуйте обработку в версии v1 с ошибкой в бизнес-формуле.\n4. Выполните Replay с оффсета 0 для версии v2 с исправленной формулой.\n5. Сравните результаты двух запусков.",
        "code_blocks": [
            {
                "filename": "stream_replay.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
)

type KafkaLogMessage struct {
	Offset  int64
	UserID  string
	Amount  float64
}

func main() {
	// Персистентный лог Kafka за прошедшие дни
	kafkaLog := []KafkaLogMessage{
		{Offset: 0, UserID: "alice", Amount: 100.0},
		{Offset: 1, UserID: "bob", Amount: 200.0},
		{Offset: 2, UserID: "alice", Amount: 50.0},
		{Offset: 3, UserID: "charlie", Amount: 300.0},
	}

	fmt.Println("=== Этап 1: Запуск старой версии v1 (с багом: забыли учесть НДС) ===")
	v1State := make(map[string]float64)
	for _, msg := range kafkaLog {
		// Ошибка в формуле v1
		v1State[msg.UserID] += msg.Amount
	}
	fmt.Printf("Результат v1: %v\n", v1State)

	fmt.Println("\n=== Этап 2: Обнаружен баг! Запуск Stream Replay для версии v2 ===")
	fmt.Println("Перемещение оффсета Consumer Group 'analytics-v2' на Offset = 0...")

	v2State := make(map[string]float64)
	for _, msg := range kafkaLog {
		// Исправленная формула в v2: расчет чистой выручки за вычетом 20% НДС
		netAmount := msg.Amount / 1.20
		v2State[msg.UserID] += netAmount
	}

	fmt.Println("\n✅ Replay успешно завершен! Исправленный расчет v2:")
	for user, val := range v2State {
		fmt.Printf("   Пользователь %-8s: Было (v1)=%.2f руб -> Стало (v2)=%.2f руб\n",
			user, v1State[user], val)
	}
}
"""
            }
        ],
        "under_the_hood": "Перемещение оффсета в Kafka выполняется вызовом API `OffsetResetPolicy` или CLI `kafka-consumer-groups --reset-offsets --to-datetime ... --execute`. Брокер не копирует данные — он просто меняет числовую отметку в системной партиции `__consumer_offsets`. Клиент начинает вычитывать исторические сегменты лога с диска со скоростью пропускной способности сети и диска (до 1 ГБ/сек), догоняя реальное время в десятки раз быстрее, чем события генерировались изначально.",
        "pitfalls": "При Replay потока убедитесь, что операторы конвейера не отправляют повторные нотификации во внешний мир (SMS, пуши, списания денег)! Сайд-эффекты должны быть отключены, либо направляться в тестовые заглушки.",
        "interview_qa": "В: Как избежать переполнения локального State Store при высокоскоростном Replay истории за 6 месяцев?\nО: При Replay скорость потока в десятки раз выше нормы, что создает огромную нагрузку на диск. Для ускорения отключают фоновую синхронизацию WAL на диск (`DisableWAL: true`), увеличивают размер `MemTable` в 5 раз и отключают автоматическую публикацию промежуточных оконных триггеров до момента выхода на актуальное время (Lag < 100)."
    },
    {
        "num": 25,
        "title": "Мониторинг задержки обработки (Processing Lag)",
        "task": "Экспортируйте метрики Prometheus для потокового процессора: `stream_processing_lag_seconds` ($T_{current} - T_{event}$), `watermark_delay_seconds`, `events_in_flight` и `state_store_bytes`. Настройте правила алертинга на рост лага обработки, сигнализирующего о нехватке вычислительных ресурсов воркеров.",
        "theory": "В потоковой обработке классический CPU/RAM мониторинг недостаточен. Главная метрика здоровья конвейера — **Lag (Отставание / Задержка)**:\n\n1. **Event Time Processing Lag**:\n   $$\text{Lag} = T_{\text{current\_system\_time}} - T_{\text{event\_time}}$$\n   Показывает, насколько старые события обрабатываются прямо сейчас. Если лаг растет, система не справляется с потоком данных.\n\n2. **Consumer Group Lag (Kafka Lag)**:\n   Количество непрочитанных сообщений в очереди брокера: $\text{LatestLogEndOffset} - \text{CurrentConsumerOffset}$.\n\n3. **Watermark Lag**:\n   Разница между часами реального времени и текущим водяным знаком: $T_{now} - W$.",
        "step_by_step": "1. Подключите метрики Prometheus через `prometheus.NewGauge` и `prometheus.NewCounter`.\n2. При обработке каждого события вычисляйте разницу `time.Since(e.Timestamp)`.\n3. Экспортируйте метрики через HTTP-эндпоинт `/metrics`.\n4. Напишите PromQL правило алертинга на рост лага более 60 секунд.",
        "code_blocks": [
            {
                "filename": "metrics.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"net/http"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	eventsProcessed = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "stream_events_processed_total",
		Help: "Общее количество обработанных потоковых событий",
	})

	processingLagSeconds = prometheus.NewGauge(prometheus.GaugeOpts{
		Name: "stream_processing_lag_seconds",
		Help: "Задержка обработки: разница между текущим временем и Event Time",
	})
)

func init() {
	prometheus.MustRegister(eventsProcessed)
	prometheus.MustRegister(processingLagSeconds)
}

func ProcessStreamingRecord(eventTimestamp time.Time) {
	eventsProcessed.Inc()

	// Вычисление лага обработки
	lag := time.Since(eventTimestamp).Seconds()
	processingLagSeconds.Set(lag)

	fmt.Printf(" [METRICS] Обработано событие. Текущий лаг: %.2f сек\r", lag)
}

func main() {
	go func() {
		http.Handle("/metrics", promhttp.Handler())
		_ = http.ListenAndServe(":2112", nil)
	}()

	fmt.Println("Prometheus метрики запущены на http://localhost:2112/metrics")
	fmt.Println("\n=== PromQL правило алертинга ===")
	fmt.Println("alert: HighStreamProcessingLag")
	fmt.Println("expr: stream_processing_lag_seconds > 60")
	fmt.Println("for: 3m")
	fmt.Println("labels: { severity: 'critical' }")
	fmt.Println("annotations: { summary: 'Потоковый воркер отстает от реального времени более чем на 1 минуту!' }")

	// Симуляция потока с растущим отставанием
	tPast := time.Now().Add(-15 * time.Second)
	for i := 0; i < 5; i++ {
		ProcessStreamingRecord(tPast)
		time.Sleep(200 * time.Millisecond)
	}
	fmt.Println()
}
"""
            }
        ],
        "under_the_hood": "Метрика `stream_processing_lag_seconds` экспортируется в виде Gauge. В оркестраторах (Kubernetes KEDA / HPA) эта метрика связывается с автомасштабированием: если `stream_processing_lag_seconds > 30`, KEDA автоматически увеличивает количество реплик подов воркеров с 5 до 20, ликвидируя накопившийся лаг.",
        "pitfalls": "При обработке исторических данных (Stream Replay) лаг намеренно будет составлять миллионы секунд. Во время проведения Replay алерты на `processing_lag` необходимо временно отключать (Silencing в Alertmanager).",
        "interview_qa": "В: Почему лаг в секундах (Event Time Lag) надежнее для бизнеса, чем лаг в количестве сообщений (Message Count Lag)?\nО: 10 000 сообщений лага при потоке 100k RPS — это всего 100 миллисекунд задержки (абсолютная норма). Но те же 10 000 сообщений при потоке 1 сообщение в минуту — это 7 дней задержки (катастрофа). Время отставания (Time Lag) дает объективную оценку свежести данных независимо от текущей плотности трафика."
    },
    {
        "num": 26,
        "title": "Тестирование потоковой топологии с виртуальным временем",
        "task": "Напишите детерминированный тестовый стенд для юнит-тестирования потоковых окон: вместо реального брокера Kafka используйте тестовый драйвер, который генерирует события с контролируемыми метками времени и принудительными водяными знаками. Докажите, что логика агрегации окон отрабатывает идентично независимо от задержек CPU тестовой машины.",
        "theory": "Тестирование потоковых конвейеров с реальным временем (`time.Sleep`) — источник нестабильных (Flaky) тестов в CI/CD: медленный раннер перегрузится, таймер сработает на 10 мс позже, и тест упадет.\n\nПрофессиональный подход — **Virtual Clock Testing (Драйвер виртуального времени)**:\n1. Тест оперирует полностью абстрактным временем.\n2. Тестовый стенд подает события строго с заданными метками $T$.\n3. Водяные знаки продвигаются вручную: `driver.AdvanceWatermark(time)`.\n4. Тест выполняется за 1–2 миллисекунды и гарантирует 100% повторяемость на любых процессорах.",
        "step_by_step": "1. Спроектируйте интерфейс `TestStreamDriver`.\n2. Реализуйте метод `Send(event)` и `AdvanceWatermark(w)`.\n3. Напишите юнит-тест проверки закрытия 10-минутного тумблингового окна.\n4. Проверьте результат ассертами.",
        "code_blocks": [
            {
                "filename": "stream_test.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"testing"
	"time"
)

type TestEvent struct {
	Key       string
	Value     int
	Timestamp time.Time
}

type WindowTestHarness struct {
	windowSize  time.Duration
	accumulator map[string]int
	closed      bool
}

func NewHarness(size time.Duration) *WindowTestHarness {
	return &WindowTestHarness{
		windowSize:  size,
		accumulator: make(map[string]int),
	}
}

func (h *WindowTestHarness) SendEvent(e TestEvent) {
	if !h.closed {
		h.accumulator[e.Key] += e.Value
	}
}

func (h *WindowTestHarness) AdvanceWatermark(w time.Time, windowEnd time.Time) {
	if !w.Before(windowEnd) {
		h.closed = true
	}
}

func TestTumblingWindow_Deterministic(t *testing.T) {
	harness := NewHarness(10 * time.Minute)
	t0 := time.Date(2026, 9, 8, 12, 0, 0, 0, time.UTC)
	windowEnd := t0.Add(10 * time.Minute)

	// Подаем события виртуального времени
	harness.SendEvent(TestEvent{Key: "item_a", Value: 10, Timestamp: t0.Add(1 * time.Minute)})
	harness.SendEvent(TestEvent{Key: "item_a", Value: 15, Timestamp: t0.Add(5 * time.Minute)})

	// Продвигаем виртуальный водяной знак до 12:08:00 (окно еще открыто)
	harness.AdvanceWatermark(t0.Add(8*time.Minute), windowEnd)
	if harness.closed {
		t.Fatalf("Окно не должно было закрыться в 12:08!")
	}

	// Продвигаем водяной знак до 12:10:00 (окно обязано закрыться!)
	harness.AdvanceWatermark(t0.Add(10*time.Minute), windowEnd)
	if !harness.closed {
		t.Fatalf("Окно обязано было закрыться в 12:10!")
	}

	if harness.accumulator["item_a"] != 25 {
		t.Fatalf("Ожидалась сумма 25, получено: %d", harness.accumulator["item_a"])
	}

	fmt.Println("✅ Детерминированный тест окна успешно пройден без единого вызова time.Sleep!")
}

func main() {
	TestTumblingWindow_Deterministic(nil)
}
"""
            }
        ],
        "under_the_hood": "Такой подход реализован в Flink Harness (`OneInputStreamOperatorTestHarness`) и Kafka Streams `TopologyTestDriver`. Тестовый драйвер полностью перехватывает системное колесо таймеров, позволяя симулировать многомесячные сессионные окна и терабайтные потоки за миллисекунды выполнения `go test ./...`.",
        "pitfalls": "Если в тестируемом коде где-то случайно остался прямой вызов `time.Now()`, тест перестанет быть детерминированным. Всегда внедряйте интерфейс часов (`Clock`) через DI.",
        "interview_qa": "В: Как протестировать реакцию потокового оператора на сбой воркера и перезапуск из чекпоинта?\nО: С помощью тестового стенда: 1) Подать 100 событий, 2) Запустить барьер и вызвать `harness.Snapshot()`, 3) Создать новый экземпляр оператора, 4) Вызвать `newOperator.Restore(snapshot)`, 5) Подать оставшиеся 100 событий и проверить консистентность финального агрегата."
    },
    {
        "num": 27,
        "title": "Высокопроизводительный кольцевой буфер (Disruptor Pattern) на Go",
        "task": "Каналы Go имеют накладные расходы на блокировки мьютексов при экстремальной конкуренции (десятки миллионов сообщений в секунду). Изучите паттерн LMAX Disruptor: реализуйте lock-free кольцевой буфер на атомарных операциях (`sync/atomic`) для межпоточной передачи событий. Покажите на бенчмарке субмикросекундную задержку передачи.",
        "theory": "Стандартный канал Go `make(chan T, N)` внутри использует структуру `hchan` с мьютексом `hchan.lock`. При миллионах операций в секунду борьба за этот мьютекс (Lock Contention) и сброс строк кэша процессора (Cache Line Invalidation) становятся узким горлышком.\n\n**LMAX Disruptor Pattern (Mechanical Sympathy)**:\n1. Фиксированный кольцевой буфер (Ring Buffer) размером степени двойки ($2^k$).\n2. Однонаправленные монотонно возрастающие 64-битные курсоры (`Sequence`).\n3. Быстрое деление по модулю через битовую маску: `index = sequence & (size - 1)`.\n4. Полное отсутствие тяжелых мьютексов ОС: синхронизация исключительно на атомарных CAS-операциях (`atomic.LoadUint64`, `atomic.CompareAndSwapUint64`).\n5. **Cache Line Padding**: курсоры дополняются пустыми байтами (64 байта) для защиты от эффекта False Sharing между ядрами CPU!",
        "step_by_step": "1. Спроектируйте кольцевой буфер `DisruptorRingBuffer[T]` фиксированного размера $2^k$.\n2. Добавьте курсоры чтения и записи с выравниванием кэш-линий.\n3. Реализуйте методы публикации `Publish` и чтения `Consume` на базе `sync/atomic`.\n4. Продемонстрируйте передачу 1 000 000 сообщений между двумя ядрами процессора.",
        "code_blocks": [
            {
                "filename": "disruptor.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"runtime"
	"sync"
	"sync/atomic"
	"time"
)

// PaddedSequence предотвращает эффект False Sharing на L1/L2 кэш-линиях (64 байта).
type PaddedSequence struct {
	value uint64
	_pad  [7]uint64 // 56 байт выравнивания до полных 64 байт кэш-линии
}

// LockFreeRingBuffer — высокопроизводительный буфер передачи данных без мьютексов.
type LockFreeRingBuffer struct {
	buffer []int64
	mask   uint64
	cursor PaddedSequence // Курсор записи
	read   PaddedSequence // Курсор чтения
}

func NewRingBuffer(powerOfTwo uint64) *LockFreeRingBuffer {
	return &LockFreeRingBuffer{
		buffer: make([]int64, powerOfTwo),
		mask:   powerOfTwo - 1,
	}
}

func (rb *LockFreeRingBuffer) Publish(item int64) {
	for {
		writeSeq := atomic.LoadUint64(&rb.cursor.value)
		readSeq := atomic.LoadUint64(&rb.read.value)

		// Проверка переполнения буфера
		if writeSeq-readSeq > rb.mask {
			runtime.Gosched() // Уступаем квант времени планировщику
			continue
		}

		idx := writeSeq & rb.mask
		rb.buffer[idx] = item
		atomic.StoreUint64(&rb.cursor.value, writeSeq+1)
		return
	}
}

func (rb *LockFreeRingBuffer) Consume() int64 {
	for {
		readSeq := atomic.LoadUint64(&rb.read.value)
		writeSeq := atomic.LoadUint64(&rb.cursor.value)

		// Буфер пуст
		if readSeq >= writeSeq {
			runtime.Gosched()
			continue
		}

		idx := readSeq & rb.mask
		item := rb.buffer[idx]
		atomic.StoreUint64(&rb.read.value, readSeq+1)
		return item
	}
}

func main() {
	const totalItems = 1_000_000
	const bufferSize = 1024 // Степень двойки

	rb := NewRingBuffer(bufferSize)
	var wg sync.WaitGroup
	wg.Add(2)

	start := time.Now()

	// Продюсер
	go func() {
		defer wg.Done()
		for i := int64(1); i <= totalItems; i++ {
			rb.Publish(i)
		}
	}()

	// Консьюмер
	var sum int64
	go func() {
		defer wg.Done()
		for i := 0; i < totalItems; i++ {
			sum += rb.Consume()
		}
	}()

	wg.Wait()
	elapsed := time.Since(start)

	opsPerSec := float64(totalItems) / elapsed.Seconds()
	nsPerOp := float64(elapsed.Nanoseconds()) / float64(totalItems)

	fmt.Printf("=== Результаты LMAX Disruptor на Go ===\n")
	fmt.Printf("Передано сообщений: %d\n", totalItems)
	fmt.Printf("Затраченное время:  %v\n", elapsed)
	fmt.Printf("Пропускная способность: %.0f ops/sec\n", opsPerSec)
	fmt.Printf("Задержка операции:      %.1f наносекунд (ns/op)!\n", nsPerOp)
}
"""
            }
        ],
        "under_the_hood": "LMAX Disruptor устраняет contention за счет разделения курсоров чтения и записи. Атомарные операции `atomic.LoadUint64` компилируются в одну процессорную инструкцию `MOVQ` (на x86-64 с моделью памяти TSO), а `StoreUint64` компилируется в `MOVQ` с барьером памяти, полностью минуя системные вызовы ядра ОС `futex`.",
        "pitfalls": "В цикле ожидания `runtime.Gosched()` или спинлоке процессор потребляет 100% CPU. Для систем со средними нагрузками Disruptor конфигурируют со стратегией ожидания `YieldingWaitStrategy` или `SleepingWaitStrategy` для экономии энергии и процессорных квантов.",
        "interview_qa": "В: Зачем нужно выравнивание кэш-линий (Cache Line Padding) в структурах данных высокой производительности?\nО: Процессор считывает память из RAM в кэш L1/L2 блоками по 64 байта. Если курсор чтения и курсор записи лежат рядом в одном 64-байтном блоке, запись одного ядра сделает недействительным (Invalidate) весь блок в кэше второго ядра (эффект False Sharing), что снизит скорость обмена данными в 10–50 раз."
    },
    {
        "num": 28,
        "title": "Потоковая пакетная запись в ClickHouse с фиксацией оффсетов",
        "task": "ClickHouse категорически не приемлет построчную вставку одиночных записей (Single Row Inserts) — это вызывает взрывное размножение мелких кусков данных (Too many parts error). Напишите потоковый Sink, который накапливает события из Kafka в памяти, периодически сбрасывает их в ClickHouse крупными пачками (батчами) и коммитит оффсеты в Kafka ТОЛЬКО после успешного подтверждения вставки.",
        "theory": "Архитектура ClickHouse (движок MergeTree) оптимизирована для вставки данных крупными пакетами (от 10 000 до 100 000 строк в одном `INSERT`):\n- Каждая операция `INSERT` создает отдельную директорию (Part) на диске с индексами и сжатыми колонками.\n- Если слать 10 000 одиночных INSERT в секунду, сервер ClickHouse упадет с ошибкой `DB::Exception: Too many parts in all data in table`.\n\nПаттерн **Buffered Transactional Batch Sink**:\n1. Воркер вычитывает события из Kafka и складывает их в локальный срез `batch []Row`.\n2. Сброс инициируется по составному условию: накопилось 10 000 строк ИЛИ прошло 2 секунды (Debounce Timer).\n3. Выполняется пакетная вставка в ClickHouse: `batch.AppendStruct(...)` затем `batch.Send()`.\n4. Только после успешного ответа СУБД воркер вызывает `consumer.CommitOffsets()` в Kafka, гарантируя семантику At-Least-Once!",
        "step_by_step": "1. Спроектируйте структуру `BatchBuffer` со срезом записей и таймером сброса.\n2. Реализуйте накопление строк с блокировкой мьютекса.\n3. Реализуйте метод `Flush(ctx)` с транзакционной записью.\n4. Настройте коммит оффсета Kafka строго после успешного завершения Flush.",
        "code_blocks": [
            {
                "filename": "clickhouse_sink.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

type ClickMetric struct {
	UserID    string
	URL       string
	Duration  int
	Offset    int64
}

// ClickHouseBatchSink аккумулирует строки и делает вставки пачками.
type ClickHouseBatchSink struct {
	mu            sync.Mutex
	buffer        []ClickMetric
	maxBatchSize  int
	flushInterval time.Duration
	highestOffset int64
}

func NewBatchSink(maxSize int, interval time.Duration) *ClickHouseBatchSink {
	return &ClickHouseBatchSink{
		maxBatchSize:  maxSize,
		flushInterval: interval,
		buffer:        make([]ClickMetric, 0, maxSize),
	}
}

func (s *ClickHouseBatchSink) Add(m ClickMetric) bool {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.buffer = append(s.buffer, m)
	if m.Offset > s.highestOffset {
		s.highestOffset = m.Offset
	}

	return len(s.buffer) >= s.maxBatchSize
}

func (s *ClickHouseBatchSink) Flush(ctx context.Context) error {
	s.mu.Lock()
	if len(s.buffer) == 0 {
		s.mu.Unlock()
		return nil
	}

	// Забираем текущий батч и освобождаем буфер
	batchToSend := s.buffer
	lastOffset := s.highestOffset
	s.buffer = make([]ClickMetric, 0, s.maxBatchSize)
	s.mu.Unlock()

	// 1. Пакетная вставка в ClickHouse
	fmt.Printf(" 🚀 [CLICKHOUSE SINK] Пакетная вставка %d строк в ClickHouse...\n", len(batchToSend))
	// Имитация clickhouse-go batch.Send()
	time.Sleep(20 * time.Millisecond)

	// 2. Только ПОСЛЕ успеха ClickHouse коммитим оффсет в Kafka!
	fmt.Printf(" 📌 [KAFKA COMMIT] Коммит оффсета Kafka: Offset = %d (Гарантия надежности)\n", lastOffset)
	return nil
}

func main() {
	sink := NewBatchSink(5, 500*time.Millisecond)
	ctx := context.Background()

	// Поток событий
	for i := int64(1); i <= 12; i++ {
		metric := ClickMetric{
			UserID:   fmt.Sprintf("usr_%d", i),
			URL:      "/catalog",
			Duration: int(i * 10),
			Offset:   1000 + i,
		}

		if sink.Add(metric) {
			// Достигнут лимит батча
			_ = sink.Flush(ctx)
		}
	}

	// Сброс оставшегося 'хвоста' буфера
	_ = sink.Flush(ctx)
}
"""
            }
        ],
        "under_the_hood": "В драйвере `clickhouse-go/v2` метод `conn.PrepareBatch` открывает нативный бинарный TCP-протокол ClickHouse. Драйвер сериализует срез Go-структур напрямую в сжатые бинарные колонки (Column-Oriented Block) без преобразования в текстовые SQL-запросы, что позволяет вставлять до 500 000 строк в секунду на одном процессорном ядре.",
        "pitfalls": "Если сервер упадет в момент между `batch.Send()` в ClickHouse и `CommitOffsets()` в Kafka, при рестарте те же строки будут прочитаны заново и вставлены повторно (дублирование данных). Для предотвращения дублей в ClickHouse используют таблицу с движком `ReplacingMergeTree` с первичным ключом по `EventID`.",
        "interview_qa": "В: Как обеспечить корректное закрытие батча при плановой остановке (Graceful Shutdown) сервиса?\nО: Воркер перехватывает системный сигнал `SIGTERM`, немедленно прекращает читать новые сообщения из Kafka, вызывает финальный метод `sink.Flush(ctx)` для сброса накопленного буфера в ClickHouse, коммитит последний оффсет и только после этого завершает процесс."
    },
    {
        "num": 29,
        "title": "Graceful Drain потокового процессора при выкатке",
        "task": "При обновлении версии пода в Kubernetes потоковый процессор должен корректно остановиться: прекратить прием новых сообщений из брокера, довести до конца обработку всех событий, находящихся в каналах конвейера (Drain in-flight), сбросить промежуточное состояние окон в локальный State Store, зафиксировать оффсеты и закрыть соединения без потерь данных.",
        "theory": "В Kubernetes поды постоянно перезапускаются: плановые деплои, масштабирование (HPA Scale-Down), миграция между нодами.\n\nЕсли при получении сигнала `SIGTERM` процесс мгновенно завершится (`os.Exit(0)`):\n- Сообщения, уже вычитанные из Kafka, но еще находящиеся внутри буферов каналов Go, будут потеряны или вызовут дубликаты.\n- Незавершенные расчеты окон будут повреждены.\n\n**Graceful Drain Pattern (Контролируемый слив конвейера)**:\n1. Перехват сигналов `SIGINT / SIGTERM`.\n2. Приостановка чтения из брокера (`Consumer.Pause()`).\n3. Закрытие входного канала Source: сигнал EOF распространяется вниз по цепочке горутин конвейера.\n4. Все промежуточные горутины дочитывают остаток очередей и завершаются через `sync.WaitGroup`.\n5. Терминальный Sink сбрасывает остатки батчей и фиксирует оффсеты.\n6. Закрытие State Store и выход.",
        "step_by_step": "1. Реализуйте перехват сигналов ОС через `signal.Notify`.\n2. Настройте координацию закрытия конвейера через `close(sourceChan)`.\n3. Дождитесь завершения обработки всех in-flight сообщений через `wg.Wait()`.\n4. Зафиксируйте корректный порядок закрытия ресурсов.",
        "code_blocks": [
            {
                "filename": "graceful_drain.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"
)

func main() {
	// Канал системных сигналов завершения от Kubernetes
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	sourceChan := make(chan int, 100)
	var wg sync.WaitGroup

	// Горутина-генератор (Source)
	ctx, cancelSource := context.WithCancel(context.Background())
	go func() {
		defer close(sourceChan)
		id := 1
		for {
			select {
			case <-ctx.Done():
				fmt.Println(" [SOURCE] Прием новых сообщений из брокера остановлен.")
				return
			default:
				sourceChan <- id
				id++
				time.Sleep(50 * time.Millisecond)
			}
		}
	}()

	// Горутина-воркер (Processing Stage)
	processedCount := 0
	wg.Add(1)
	go func() {
		defer wg.Done()
		for item := range sourceChan {
			processedCount++
			fmt.Printf(" [WORKER] Обработка in-flight сообщения #%d...\n", item)
			time.Sleep(30 * time.Millisecond)
		}
		fmt.Println(" [WORKER] Все in-flight сообщения конвейера успешно дочитаны (Drain Complete)!")
	}()

	// Ожидание сигнала завершения (или имитация через 200 мс)
	go func() {
		time.Sleep(200 * time.Millisecond)
		sigChan <- syscall.SIGTERM
	}()

	sig := <-sigChan
	fmt.Printf("\n🚨 Получен сигнал завершения: %v! Запуск Graceful Drain...\n", sig)

	// Шаг 1: останавливаем генератор
	cancelSource()

	// Шаг 2: дожидаемся, пока воркер полностью вычитает оставшиеся сообщения из sourceChan
	wg.Wait()

	// Шаг 3: коммит оффсетов и закрытие баз данных
	fmt.Printf("💾 [SINK] Финальная фиксация оффсетов и сброс состояния. Всего обработано: %d\n", processedCount)
	fmt.Println("✅ Процесс безопасно остановлен без потери данных.")
}
"""
            }
        ],
        "under_the_hood": "В Kubernetes при удалении пода отправляется сигнал `SIGTERM`, после чего запускается таймер `terminationGracePeriodSeconds` (по умолчанию 30 секунд). Если под успевает выполнить Graceful Drain за это время, Kubernetes удаляет контейнер штатно. Если под зависает, через 30 секунд отправляется `SIGKILL`, принудительно убивающий процесс. Поэтому время дренажа конвейера всегда ограничивают контекстом с дедлайном 20–25 секунд.",
        "pitfalls": "Если в цепочке конвейера одна из горутин заблокируется на записи в незакрытый канал, `wg.Wait()` зависнет навсегда, и под будет принудительно убит по `SIGKILL`. Всегда используйте `defer close(outChan)` на каждой промежуточной стадии.",
        "interview_qa": "В: Как обеспечить Graceful Drain при использовании Apache Kafka Consumer Group?\nО: При получении `SIGTERM` вызывается метод `consumerGroup.Close()`. Клиент Kafka отправляет брокеру запрос `LeaveGroupRequest`. Брокер немедленно начинает ребалансировку (Rebalance), переназначая партиции другим живым воркерам без ожидания истечения таймаута `session.timeout.ms` (который обычно составляет 45 секунд)."
    },
    {
        "num": 30,
        "title": "Реализация движка обнаружения мошенничества в реальном времени (Fraud Detection)",
        "task": "Объедините все изученные техники в комплексный сервис финансового мониторинга: прием потока платежей, дедупликация в скользящем окне, фильтрация по частотному порогу (Velocity Check: более 3 транзакций за 10 секунд), детектирование аномалий сумм через скользящий Z-Score, сохранение состояния актора в локальном State Store, генерация алертов и экспорт метрик Prometheus.",
        "theory": "Флагманский проект главы: архитектура банковского сервиса противодействия мошенничеству (Real-Time Anti-Fraud Engine). Это критическая система класса HighLoad, где решение о блокировке карты принимается менее чем за **10 миллисекунд** прямо в потоке авторизации транзакций.\n\nВ этой системе синтезируются все компоненты промышленного Stream Processing:\n1. **Streaming Pipeline**: многостадийный конвейер с изоляцией горутин.\n2. **Stateful Actor**: партиционирование по `CardNumber` для последовательной обработки транзакций одной карты.\n3. **Sliding Windows & Velocity Rules**: проверка частоты операций (например, всплеск транзакций с разных банкоматов за минуту).\n4. **Statistical Anomaly Detection**: динамический расчет $Z$-Score для выявления резких нетипичных сумм списаний.\n5. **Embedded State Store**: хранение профиля трат карты в локальном LSM-кэше.\n6. **Deduplication**: отсечение дублирующих списаний по `TransactionID`.",
        "step_by_step": "1. Спроектируйте модель входящей транзакции `PaymentAuthRequest`.\n2. Реализуйте профиль карты `CardState` с историей последних списаний.\n3. Реализуйте правила антифрода: Velocity Check (частота) и Z-Score (сумма).\n4. Напишите потоковый обработчик с локальным хранилищем состояния.\n5. Продемонстрируйте мгновенную блокировку подозрительных операций.",
        "code_blocks": [
            {
                "filename": "fraud_engine.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"math"
	"time"
)

type PaymentAuthRequest struct {
	TxID       string
	CardNumber string
	Amount     float64
	EventTime  time.Time
}

type FraudDecision struct {
	Blocked bool
	Reason  string
}

// CardProfile хранит локальную историю трат по карте в памяти воркера.
type CardProfile struct {
	RecentTimestamps []time.Time
	Amounts          []float64
}

// RealTimeFraudEngine — комплексный движок финансового мониторинга.
type RealTimeFraudEngine struct {
	profiles map[string]*CardProfile
}

func NewFraudEngine() *RealTimeFraudEngine {
	return &RealTimeFraudEngine{
		profiles: make(map[string]*CardProfile),
	}
}

func (e *RealTimeFraudEngine) Evaluate(tx PaymentAuthRequest) FraudDecision {
	profile, exists := e.profiles[tx.CardNumber]
	if !exists {
		profile = &CardProfile{}
		e.profiles[tx.CardNumber] = profile
	}

	// 1. Правило Velocity: очищаем историю старше 10 секунд
	cutoff := tx.EventTime.Add(-10 * time.Second)
	validTimes := profile.RecentTimestamps[:0]
	for _, t := range profile.RecentTimestamps {
		if t.After(cutoff) {
			validTimes = append(validTimes, t)
		}
	}
	profile.RecentTimestamps = validTimes

	// Проверка: более 3 транзакций за последние 10 секунд!
	if len(profile.RecentTimestamps) >= 3 {
		return FraudDecision{
			Blocked: true,
			Reason:  fmt.Sprintf("VELOCITY_LIMIT_EXCEEDED: 4-я транзакция за 10 сек (Подозрение на брутфорс/кражу)"),
		}
	}

	// 2. Правило Z-Score: аномальный размер платежа относительно типичных трат
	if len(profile.Amounts) >= 10 {
		sum := 0.0
		for _, a := range profile.Amounts {
			sum += a
		}
		mean := sum / float64(len(profile.Amounts))

		varianceSum := 0.0
		for _, a := range profile.Amounts {
			varianceSum += math.Pow(a-mean, 2)
		}
		stdDev := math.Sqrt(varianceSum / float64(len(profile.Amounts)))

		if stdDev > 100.0 {
			zScore := (tx.Amount - mean) / stdDev
			if zScore > 3.5 {
				return FraudDecision{
					Blocked: true,
					Reason:  fmt.Sprintf("STATISTICAL_ANOMALY: Сумма %.2f руб отклоняется на +%.1f сигма (Mean: %.2f)", tx.Amount, zScore, mean),
				}
			}
		}
	}

	// Обновляем состояние профиля карты
	profile.RecentTimestamps = append(profile.RecentTimestamps, tx.EventTime)
	profile.Amounts = append(profile.Amounts, tx.Amount)

	return FraudDecision{Blocked: false, Reason: "APPROVED"}
}

func main() {
	engine := NewFraudEngine()
	t0 := time.Now()
	testCard := "4111_2222_3333_4444"

	fmt.Println("=== Потоковый процессинг транзакций в Real-Time Fraud Engine ===")

	// Наполняем типичный профиль трат клиента (покупки в супермаркетах около 1500 руб)
	for i := 0; i < 15; i++ {
		engine.Evaluate(PaymentAuthRequest{
			TxID:       fmt.Sprintf("init_%d", i),
			CardNumber: testCard,
			Amount:     1500.0 + float64(i*50),
			EventTime:  t0.Add(time.Duration(i) * time.Hour),
		})
	}

	// Сценарий 1: Внезапная транзакция на 300 000 руб (Z-Score аномалия)
	fraudTx1 := PaymentAuthRequest{
		TxID:       "fraud_1",
		CardNumber: testCard,
		Amount:     300_000.0,
		EventTime:  t0.Add(20 * time.Hour),
	}
	dec1 := engine.Evaluate(fraudTx1)
	fmt.Printf("Транзакция %.0f руб: Блокировка? %v | Причина: %s\n\n", fraudTx1.Amount, dec1.Blocked, dec1.Reason)

	// Сценарий 2: Атака перебором (Velocity Check: 4 транзакции за 3 секунды)
	fmt.Println("Проверка Velocity: серия быстрых транзакций подряд...")
	for i := 1; i <= 4; i++ {
		tx := PaymentAuthRequest{
			TxID:       fmt.Sprintf("rapid_%d", i),
			CardNumber: testCard,
			Amount:     200.0,
			EventTime:  t0.Add(25*time.Hour + time.Duration(i)*time.Second),
		}
		dec := engine.Evaluate(tx)
		fmt.Printf("   Транзакция #%d: Блокировка? %v | Статус: %s\n", i, dec.Blocked, dec.Reason)
	}
}
"""
            }
        ],
        "under_the_hood": "Этот сервис объединяет детерминированное партиционирование Kafka по хэшу номера карты с локальным хранилищем профиля в оперативной памяти. Благодаря тому, что транзакции одной карты всегда попадают на один и тот же поток, оценка правил Velocity и Z-Score выполняется за **0.05 миллисекунды** без распределенных блокировок и без сетевых вызовов в СУБД.",
        "pitfalls": "Не храните историю временных меток в неограниченно растущих срезах. Всегда очищайте срез `RecentTimestamps` до начала окна проверки (10 секунд), чтобы исключить утечки оперативной памяти при длительной работе сервиса.",
        "interview_qa": "В: Как масштабировать данный движок антифрода на 100 000 транзакций в секунду в продакшене ведущего банка?\nО: Архитектура строится на кластере Kafka с 64 партициями по топику `transactions`. Развертывается 64 реплики подов Go-воркеров. Каждому поду назначается одна партиция. Воркер держит профили своих карт в локальном Pebble/Badger с NVMe SSD. Это обеспечивает линейную горизонтальную масштабируемость и суммарную задержку принятия решений менее 5 миллисекунд."
    }
]
