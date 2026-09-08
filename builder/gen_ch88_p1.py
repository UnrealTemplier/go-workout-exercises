# -*- coding: utf-8 -*-
"""
Chapter 88 Part 1: Exercises 1 to 15
Real-Time Stream Processing on Go
"""

exercises = [
    {
        "num": 1,
        "title": "Концепция потоковой обработки (Stream vs Batch Processing)",
        "task": "Изучите фундаментальные различия между пакетной обработкой (Batch) и непрерывными бесконечными потоками данных (Unbounded Streams). Спроектируйте базовую модель потокового события на Go: универсальную структуру `Event[T any]` с полями `ID string`, `Key string`, `Payload T`, `Timestamp time.Time`. Реализуйте инкрементальную потоковую обработку в памяти и объясните, почему потоковые системы не могут сохранять весь бесконечный поток в RAM.",
        "theory": "В компьютерных науках обработка данных традиционно делится на две фундаментальные парадигмы:\n\n1. **Пакетная обработка (Batch Processing / Bounded Data)**:\n   - Данные статичны, конечны и уже сохранены на диск (HDFS, S3, ClickHouse, PostgreSQL).\n   - Алгоритм знает общий размер выборки, может прочитать данные целиком, отсортировать их и построить индекс.\n   - Главные метрики: пропускная способность (Throughput) и общее время выполнения пакета (Job Duration: часы, сутки).\n\n2. **Потоковая обработка (Stream Processing / Unbounded Streams)**:\n   - Данные представляют собой непрерывный, бесконечный поток событий, порождаемых внешним миром (клики пользователей, GPS координаты курьеров, датчики IoT, биржевые котировки, финансовые транзакции).\n   - Поток никогда не завершается: у него есть начало, но нет конца.\n   - Главные метрики: задержка обработки единичного события (Latency: миллисекунды) и поддержание актуального промежуточного состояния (Internal State) без деградации по памяти $O(1)$.\n\nВ Go потоковая обработка организуется вокруг каналов, инкрементальных агрегаторов и встраиваемых хранилищ состояния (State Stores).",
        "step_by_step": "1. Спроектируйте обобщенную (generic) структуру `Event[T any]` с ключевыми атрибутами (ID, Key для партиционирования, Payload, EventTime).\n2. Реализуйте интерфейс `StreamProcessor[T In, R Out]`.\n3. Напишите потоковый агрегатор, вычисляющий скользящие метрики в потоке.\n4. Продемонстрируйте обработку бесконечного генератора событий с константным потреблением оперативной памяти.",
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

// Event представляет единичное неизменяемое событие в бесконечном потоке данных.
type Event[T any] struct {
	ID        string    `json:"id"`
	Key       string    `json:"key"` // Ключ партиционирования (UserID, DeviceID)
	Payload   T         `json:"payload"`
	Timestamp time.Time `json:"timestamp"` // Event Time
}

// PaymentPayload — полезная нагрузка финансового события.
type PaymentPayload struct {
	Amount float64
	Status string
}

// StreamingMetrics хранит инкрементальное состояние потока в памяти O(1).
type StreamingMetrics struct {
	mu           sync.Mutex
	TotalCount   int64
	TotalAmount  float64
	SuccessCount int64
}

func (m *StreamingMetrics) ProcessEvent(e Event[PaymentPayload]) {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.TotalCount++
	m.TotalAmount += e.Payload.Amount
	if e.Payload.Status == "SUCCESS" {
		m.SuccessCount++
	}
}

func (m *StreamingMetrics) Snapshot() (int64, float64, float64) {
	m.mu.Lock()
	defer m.mu.Unlock()
	successRate := 0.0
	if m.TotalCount > 0 {
		successRate = (float64(m.SuccessCount) / float64(m.TotalCount)) * 100.0
	}
	return m.TotalCount, m.TotalAmount, successRate
}

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	eventStream := make(chan Event[PaymentPayload], 100)
	metrics := &StreamingMetrics{}

	// Горутина-генератор непрерывного потока событий (Source)
	go func() {
		defer close(eventStream)
		id := 1
		for {
			select {
			case <-ctx.Done():
				return
			default:
				status := "SUCCESS"
				if id%5 == 0 {
					status = "FAILED"
				}
				eventStream <- Event[PaymentPayload]{
					ID:        fmt.Sprintf("evt_%d", id),
					Key:       fmt.Sprintf("user_%d", id%10),
					Payload:   PaymentPayload{Amount: float64(id * 10), Status: status},
					Timestamp: time.Now(),
				}
				id++
				time.Sleep(50 * time.Millisecond)
			}
		}
	}()

	// Консьюмер потока: инкрементальная обработка без накопления истории в RAM
	for evt := range eventStream {
		metrics.ProcessEvent(evt)
		count, sum, rate := metrics.Snapshot()
		fmt.Printf(" [STREAM] Обработано событий: %d | Оборот: %.2f руб | Успешных: %.1f%%\r",
			count, sum, rate)
	}

	fmt.Println("\n✅ Потоковая обработка завершена корректно.")
}
"""
            }
        ],
        "under_the_hood": "В отличие от пакетной модели (Hadoop MapReduce / Spark), где данные пишутся на диск между фазами (Shuffle write), в потоковых архитектурах (Flink, Kafka Streams, Go-конвейеры) данные никогда не 'останавливаются'. События передаются через буферизованные кольцевые буферы и каналы Go по конвейеру операторов. Промежуточное состояние агрегации удерживается в быстрых регистрах или LSM-деревьях, сохраняя временную сложность обработки одного события $O(1)$ и исключая утечки памяти.",
        "pitfalls": "Главная ошибка разработчиков, пришедших из веб-бэкенда — сохранение среза входящих событий (`events = append(events, event)`) в память для последующего анализа. В бесконечном потоке со скоростью 50 000 событий в секунду процесс исчерпает оперативную память сервера (OOM Kill) за считанные минуты. Все алгоритмы обязаны работать инкрементально в фиксированном объеме RAM.",
        "interview_qa": "В: Чем отличается unbounded stream от bounded dataset в контексте теории потоковой обработки Тайлера Акидау (Google Dataflow Model)?\nО: По Акидау, пакетная обработка — это всего лишь частный случай потоковой обработки, где границы потока искусственно зафиксированы (Bounded). В реальном мире любые данные рождаются как бесконечный непрерывный поток (Unbounded), и только ограничения систем вынуждали нас исторически резать их на суточные и часовые батчи. Современный Stream Processing работает с данными в их естественной непрерывной форме."
    },
    {
        "num": 2,
        "title": "Потоковые конвейеры на Go-каналах (Pipelines, Fan-In, Fan-Out)",
        "task": "Реализуйте конвейер обработки потока кликов в реальном времени: генератор событий -> стадия фильтрации (отсечение ботов) -> параллельная стадия обогащения данных (Fan-Out на 8 горутин-воркеров) -> слияние потоков в единый канал (Fan-In) -> агрегатор. Обеспечьте корректную передачу отмены через `context.Context` и закрытие каналов без паник и утечек горутин.",
        "theory": "Паттерн **Stream Pipeline (Потоковый конвейер)** в Go строится на композиции однонаправленных каналов (`<-chan T`) и горутин:\n1. **Source**: горутина-генератор, читающая брокер или сеть и пишущая в исходящий канал.\n2. **Filter / Transformer**: промежуточный оператор, принимающий входной канал и возвращающий преобразованный канал.\n3. **Fan-Out**: распределение тяжелой работы (например, вычисление криптографического хэша или парсинг User-Agent) между несколькими параллельными горутинами-воркерами, читающими из одного общего канала.\n4. **Fan-In**: слияние нескольких выходных каналов воркеров в единый агрегирующий канал с помощью `sync.WaitGroup`.\n5. **Sink**: терминальный оператор, сбрасывающий сагрегированные данные в базу данных или сокет.",
        "step_by_step": "1. Опишите модель `ClickEvent` (IP, UserAgent, IsBot, Latency).\n2. Реализуйте стадию `filterStage`, отсекающую события ботов.\n3. Реализуйте стадию `enrichStage` с параллельным Fan-Out на N горутин.\n4. Напишите мультиплексор `fanIn`, корректно закрывающий результирующий канал после завершения всех воркеров.\n5. Свяжите все стадии конвейера в единую цепочку в main.go.",
        "code_blocks": [
            {
                "filename": "pipeline.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

type ClickEvent struct {
	ID        int
	IP        string
	UserAgent string
	IsBot     bool
	Country   string
}

// Stage 1: Generator (Source)
func clickSource(ctx context.Context, total int) <-chan ClickEvent {
	out := make(chan ClickEvent, 100)
	go func() {
		defer close(out)
		for i := 1; i <= total; i++ {
			event := ClickEvent{
				ID:        i,
				IP:        fmt.Sprintf("192.168.1.%d", i%255),
				UserAgent: "Mozilla/5.0",
				IsBot:     i%4 == 0, // Каждый 4-й — бот
			}
			select {
			case <-ctx.Done():
				return
			case out <- event:
			}
		}
	}()
	return out
}

// Stage 2: Filter (Отсечение ботов)
func filterBots(ctx context.Context, in <-chan ClickEvent) <-chan ClickEvent {
	out := make(chan ClickEvent, 100)
	go func() {
		defer close(out)
		for e := range in {
			if !e.IsBot {
				select {
				case <-ctx.Done():
					return
				case out <- e:
				}
			}
		}
	}()
	return out
}

// Stage 3: Worker (Обогащение данных GeoIP)
func enrichWorker(ctx context.Context, in <-chan ClickEvent) <-chan ClickEvent {
	out := make(chan ClickEvent, 20)
	go func() {
		defer close(out)
		for e := range in {
			// Имитация тяжелого лукапа в MaxMind GeoIP БД
			time.Sleep(5 * time.Millisecond)
			e.Country = "RU"
			select {
			case <-ctx.Done():
				return
			case out <- e:
			}
		}
	}()
	return out
}

// Stage 4: Fan-In (Слияние N каналов воркеров в один)
func fanIn(ctx context.Context, channels ...<-chan ClickEvent) <-chan ClickEvent {
	out := make(chan ClickEvent, 100)
	var wg sync.WaitGroup

	for _, ch := range channels {
		wg.Add(1)
		go func(c <-chan ClickEvent) {
			defer wg.Done()
			for e := range c {
				select {
				case <-ctx.Done():
					return
				case out <- e:
				}
			}
		}(ch)
	}

	go func() {
		wg.Wait()
		close(out)
	}()

	return out
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	const totalEvents = 100
	const numWorkers = 8

	// Сборка потокового конвейера
	sourceChan := clickSource(ctx, totalEvents)
	filteredChan := filterBots(ctx, sourceChan)

	// Fan-Out: запускаем 8 параллельных воркеров обогащения
	workerChannels := make([]<-chan ClickEvent, numWorkers)
	for i := 0; i < numWorkers; i++ {
		workerChannels[i] = enrichWorker(ctx, filteredChan)
	}

	// Fan-In: собираем результат всех 8 воркеров в единый канал
	sinkChan := fanIn(ctx, workerChannels...)

	processed := 0
	for event := range sinkChan {
		processed++
		fmt.Printf(" [PIPELINE SINK] EventID: %d | Country: %s | Processed: %d\r",
			event.ID, event.Country, processed)
	}

	fmt.Printf("\n🎉 Конвейер успешно обработал %d легитимных кликов!\n", processed)
}
"""
            }
        ],
        "under_the_hood": "В паттерне Fan-Out несколько горутин читают из одного общего канала `filteredChan`. В рантайме Go чтение из канала защищено встроенным `hchan.lock`. Рантайм по очереди будит ожидающие горутины в FIFO-порядке через структуру `sudog`, что обеспечивает автоматическую сбалансированную очередь задач (Work Stealing / Worker Pool) прямо на уровне каналов без внешних блокировок.",
        "pitfalls": "Закрытие канала несколькими отправителями или отправка в закрытый канал вызывает фатальную неперехватываемую панику рантайма `panic: send on closed channel`. Правило: канал закрывается ТОЛЬКО той горутиной, которая в него пишет, и только один раз. В паттерне Fan-In канал закрывается выделенной фоновой горутиной строго после `wg.Wait()`.",
        "interview_qa": "В: Как предотвратить утечку горутин (Goroutine Leak), если консьюмер в середине конвейера завершился раньше времени из-за ошибки?\nО: Каждая стадия конвейера обязана принимать `ctx context.Context` и оборачивать операции отправки/приема в `select { case <-ctx.Done(): return case out <- val: }`. Когда консьюмер отменяет родительский контекст через `cancel()`, все upstream-горутины мгновенно завершают свои циклы и освобождают память стека."
    },
    {
        "num": 3,
        "title": "Проблема времени: Event Time vs Processing Time vs Ingestion Time",
        "task": "Разберите три концепции времени в распределенных потоковых системах: Event Time (время генерации события на клиенте), Ingestion Time (время попадания в брокер Kafka) и Processing Time (время обработки горутиной на сервере). Напишите код, демонстрирующий, как задержки мобильной сети и рассинхронизация часов приводят к искажению аналитики при использовании Processing Time вместо Event Time.",
        "theory": "В распределенных системах понятие времени не является тривиальным. Существуют три разные временные шкалы:\n\n1. **Event Time (Время события)**:\n   - Момент времени, когда событие физически произошло на источнике (сенсор зафиксировал температуру, пользователь нажал кнопку в iOS-приложении).\n   - Записывается в тело сообщения самим клиентом (`Timestamp`).\n   - Единственно верное время для бизнес-аналитики!\n\n2. **Ingestion Time (Время поступления)**:\n   - Момент времени, когда событие было сохранено в партицию Kafka брокером.\n\n3. **Processing Time (Время обработки)**:\n   - Момент времени, когда серверный процессор на Go начал вычислять функцию над этим событием (`time.Now()`).\n\n**Проблема Skew / Out-Of-Order**:\nЕсли пользователь ехал в поезде в метро 30 минут без интернета, а затем вышел на станции, его телефон отправит пачку из 100 событий, накопленных за полчаса. Если сервер считает аналитику по `Processing Time`, все 100 событий попадут в текущую секундную корзину, вызвав колоссальный ложный всплеск активности (Spike) и оставив полупустыми исторические интервалы!",
        "step_by_step": "1. Создайте симулятор событий с искусственной сетевой задержкой (Network Lag).\n2. Реализуйте два агрегатора: один группирует по `time.Now()` (Processing Time), второй — по `event.Timestamp` (Event Time).\n3. Подайте на вход события с перемешанным порядком поступления (Out-Of-Order).\n4. Сравните гистограммы результатов и покажите искажение аналитики.",
        "code_blocks": [
            {
                "filename": "time_skew.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sort"
	"time"
)

type UserAction struct {
	UserID    string
	EventTime time.Time // Время генерации на телефоне
}

func main() {
	// Базовое время: 12:00:00
	baseTime := time.Date(2026, 9, 8, 12, 0, 0, 0, time.UTC)

	// Моделируем события, произошедшие в разное время
	// Но из-за лагов сети пришедшие на сервер в случайном порядке в 12:05:00
	events := []UserAction{
		{UserID: "alice", EventTime: baseTime.Add(10 * time.Second)}, // 12:00:10
		{UserID: "bob", EventTime: baseTime.Add(20 * time.Second)},   // 12:00:20
		{UserID: "charlie", EventTime: baseTime.Add(15 * time.Second)}, // 12:00:15 (опоздал!)
		{UserID: "dave", EventTime: baseTime.Add(70 * time.Second)},    // 12:01:10
		{UserID: "eve", EventTime: baseTime.Add(85 * time.Second)},     // 12:01:25
	}

	fmt.Println("=== Сравнение Processing Time vs Event Time ===")

	// 1. Агрегация по Processing Time: сервер смотрит на текущие часы
	processingBuckets := make(map[string]int)
	currentServerTime := "12:05:00" // Время, когда сервер вычитывает пачку
	for range events {
		processingBuckets[currentServerTime]++
	}

	fmt.Println("\n❌ Результат по Processing Time (Все свалилось в одну корзину из-за сетевой задержки):")
	for bucket, count := range processingBuckets {
		fmt.Printf("   Интервал [%s]: %d событий (Ложный всплеск!)\n", bucket, count)
	}

	// 2. Агрегация по Event Time: группировка по 1-минутным корзинам реального времени
	eventTimeBuckets := make(map[string]int)
	for _, e := range events {
		bucket := e.EventTime.Truncate(1 * time.Minute).Format("15:04:00")
		eventTimeBuckets[bucket]++
	}

	fmt.Println("\n✅ Истинный результат по Event Time (Реальное распределение действий клиентов):")
	keys := make([]string, 0, len(eventTimeBuckets))
	for k := range eventTimeBuckets {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, bucket := range keys {
		fmt.Printf("   Интервал [%s]: %d событий\n", bucket, eventTimeBuckets[bucket])
	}
}
"""
            }
        ],
        "under_the_hood": "В реальных брокерах (Kafka) сообщения приходят пачками из разных TCP соединений. Сетевые очереди, ретраи сетевых пакетов TCP, партиционирование и GC-паузы мобильных приложений неизбежно приводят к тому, что порядок поступления сообщений на сервер (Arrival Order) отличается от хронологического порядка их физического возникновения (Creation Order). Поэтому надежная аналитика в HighLoad всегда опирается на Event Time с использованием механизмов Watermarks.",
        "pitfalls": "Клиентские часы на смартфонах пользователей могут быть переведены вручную в 1970 или 2038 год. Нельзя слепо доверять Event Time от внешних клиентов без валидации! Всегда отсекайте аномалии: если $EventTime > ServerTime + 5m$ или $EventTime < ServerTime - 30d$, событие бракуется как испорченное.",
        "interview_qa": "В: В каких сценариях допустимо использовать Processing Time вместо Event Time?\nО: Processing Time допустим только в операционном мониторинге инфраструктуры реального времени (SLO, Rate Limiting входящих запросов, обнаружение DDoS-атак прямо сейчас), где важна минимальная задержка без буферизации, а задержка данных не имеет исторического значения."
    },
    {
        "num": 4,
        "title": "Механизм водяных знаков (Watermarks) и задержка данных",
        "task": "Водяные знаки (Watermarks) сообщают потоковому обработчику, что события с меткой времени $T \le W$ гарантированно получены. Реализуйте генератор водяных знаков с допустимым отставанием (Bounded Out-Of-Orderness Watermark Generator): $W(t) = \max(EventTime) - \Delta t_{delay}$. Продемонстрируйте, как водяной знак продвигает виртуальное время конвейера и позволяет безопасно закрывать оконные вычисления.",
        "theory": "При обработке по Event Time возникает дилемма: когда оператор может считать, что все события за интервал `[12:00, 12:01)` уже пришли, чтобы закрыть окно и сбросить финальный расчет в ClickHouse?\n- Если закрыть окно ровно в 12:01 по часам сервера, мы потеряем опоздавшие события из-за задержек сети.\n- Если ждать вечно, окно никогда не закроется!\n\nРешение — **Watermarks (Водяные знаки)**:\nВодяной знак $W$ — это монотонно возрастающая метка времени, текущая внутри потока вместе с обычными событиями. Запись $W = 12:01:00$ означает: 'Система гарантирует с высокой вероятностью, что больше не придет ни одного события с $EventTime \le 12:01:00$'.\n\nСамый популярный алгоритм — **Bounded Out-Of-Orderness**:\n$W = \max_{seen}(EventTime) - \text{AllowedDelay}$. Мы позволяем событиям опаздывать максимум на $\Delta t$ (например, на 5 секунд).",
        "step_by_step": "1. Спроектируйте структуру `WatermarkGenerator` с параметром `maxDelay`.\n2. При поступлении каждого события обновляйте `maxEventTime`.\n3. Генерируйте водяной знак по формуле `maxEventTime - maxDelay`.\n4. Покажите, как водяной знак инициирует закрытие окон, чей дедлайн меньше $W$.",
        "code_blocks": [
            {
                "filename": "watermarks.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"time"
)

type StreamRecord struct {
	Key       string
	Value     float64
	Timestamp time.Time // Event Time
}

// BoundedOutOfOrdernessGenerator вычисляет водяные знаки с допустимым лагом.
type BoundedOutOfOrdernessGenerator struct {
	maxDelay     time.Duration
	maxEventTime time.Time
}

func NewWatermarkGenerator(maxDelay time.Duration) *BoundedOutOfOrdernessGenerator {
	return &BoundedOutOfOrdernessGenerator{
		maxDelay: maxDelay,
	}
}

// OnEvent вызывается при поступлении каждого входящего события.
func (g *BoundedOutOfOrdernessGenerator) OnEvent(event StreamRecord) time.Time {
	if event.Timestamp.After(g.maxEventTime) {
		g.maxEventTime = event.Timestamp
	}

	// Watermark = MaxEventTime - MaxDelay
	currentWatermark := g.maxEventTime.Add(-g.maxDelay)
	return currentWatermark
}

func main() {
	// Допустимое отставание данных — 5 секунд
	gen := NewWatermarkGenerator(5 * time.Second)

	baseTime := time.Date(2026, 9, 8, 10, 0, 0, 0, time.UTC)

	// Поток событий, приходящих с нарушением хронологического порядка
	stream := []StreamRecord{
		{Key: "k1", Value: 10, Timestamp: baseTime.Add(10 * time.Second)}, // 10:00:10 -> W = 10:00:05
		{Key: "k2", Value: 20, Timestamp: baseTime.Add(12 * time.Second)}, // 10:00:12 -> W = 10:00:07
		{Key: "k3", Value: 15, Timestamp: baseTime.Add(8 * time.Second)},  // 10:00:08 (Опоздавшее, но до W!)
		{Key: "k4", Value: 30, Timestamp: baseTime.Add(20 * time.Second)}, // 10:00:20 -> W = 10:00:15
		{Key: "k5", Value: 40, Timestamp: baseTime.Add(14 * time.Second)}, // 10:00:14 (Опоздавшее после W: Late Data!)
	}

	// Окно агрегации: [10:00:00, 10:00:15)
	windowEnd := baseTime.Add(15 * time.Second)
	windowClosed := false

	fmt.Println("=== Симуляция движения водяного знака (Watermark) ===")
	for i, record := range stream {
		w := gen.OnEvent(record)
		fmt.Printf("Шаг %d: Пришло событие %s (EventTime: %s) -> Текущий Watermark: %s\n",
			i+1, record.Key, record.Timestamp.Format("15:04:05"), w.Format("15:04:05"))

		// Проверка триггера закрытия окна
		if !windowClosed && !w.Before(windowEnd) {
			fmt.Printf("   🚨 [TRIGGER] Watermark (%s) >= Окончания окна (%s)! Окно закрыто и сброшено в БД.\n",
				w.Format("15:04:05"), windowEnd.Format("15:04:05"))
			windowClosed = true
		}

		if windowClosed && record.Timestamp.Before(windowEnd) {
			fmt.Printf("   ⚠️ [LATE DATA] Событие %s опоздало! Окно уже было закрыто водяным знаком.\n", record.Key)
		}
	}
}
"""
            }
        ],
        "under_the_hood": "Водяные знаки являются фундаментальным механизмом прогресса времени в таких движках, как Apache Flink и Google Cloud Dataflow. В распределенном графе операторов водяной знак продвигается по минимальному водяному знаку среди всех входящих каналов оператора: $W_{operator} = \min_{channel}(W_{channel})$. Это гарантирует, что если один из 10 брокеров Kafka задерживает отправку, оператор не закроет окно преждевременно, предотвращая потерю данных.",
        "pitfalls": "Слишком маленький `maxDelay` (например, 100 мс) приведет к тому, что множество легитимных опоздавших событий будет выброшено как Late Data. Слишком большой `maxDelay` (например, 1 час) приведет к тому, что результаты оконных расчетов будут задерживаться на целый час, увеличивая латентность системы. Баланс выбирается на основе 99.9-го перцентиля сетевой задержки клиентов.",
        "interview_qa": "В: Что происходит с водяным знаком, если в одной из партиций Kafka временно перестали появляться новые сообщения (Idle Partition)?\nО: Без новых сообщений `maxEventTime` в этой партиции не растет, что заморозит минимальный общий водяной знак всей системы ($W_{min}$) и заблокирует закрытие окон! Для решения проблемы применяется таймаут праздности (Idle Source Detection): если от партиции нет данных дольше $N$ секунд, она временно исключается из расчета общего водяного знака."
    },
    {
        "num": 5,
        "title": "Тумблинговые фиксированные окна (Tumbling Windows)",
        "task": "Реализуйте неперекрывающиеся тумблинговые окна фиксированного размера (например, 1-минутные окна подсчета заказов). Напишите структуру `TumblingWindowAssigner`, распределяющую входящие события по временным корзинам (Buckets) по математической формуле: `window_start = timestamp - (timestamp % window_size)`. При продвижении водяного знака окно сбрасывает результат и очищает память.",
        "theory": "Окна (Windows) — ключевой механизм нарезки бесконечного потока событий на конечные фрагменты для агрегации.\n\n**Тумблинговые окна (Tumbling / Fixed Windows)**:\n1. Имеют фиксированную длительность (например, 1 минута, 5 минут, 1 час).\n2. Строго не перекрываются: каждое событие принадлежит **ровно одному окну**.\n3. Границы окон привязаны к сетке эпохи времени:\n   - `WindowStart = Timestamp - (Timestamp % WindowSize)`\n   - `WindowEnd = WindowStart + WindowSize`\n4. Например, при размере окна 60 сек события с метками 12:00:15, 12:00:44 и 12:00:59 попадут в окно `[12:00:00, 12:01:00)`. Событие 12:01:00 откроет следующее окно.",
        "step_by_step": "1. Опишите структуру `WindowBucket` с полями Start, End, Sum, Count.\n2. Реализуйте функцию вычисления границ окна по формуле деления по модулю.\n3. Напишите менеджер окон, агрегирующий события в памяти.\n4. Реализуйте сброс и удаление окон при поступлении водяного знака.",
        "code_blocks": [
            {
                "filename": "tumbling_windows.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"time"
)

type TradeEvent struct {
	Symbol    string
	Volume    int
	Timestamp time.Time
}

type WindowKey struct {
	Start time.Time
	End   time.Time
}

type WindowAccumulator struct {
	TotalVolume int
	TradeCount  int
}

// TumblingWindowAssigner управляет фиксированными неперекрывающимися окнами.
type TumblingWindowAssigner struct {
	size    time.Duration
	windows map[WindowKey]*WindowAccumulator
}

func NewTumblingWindowAssigner(size time.Duration) *TumblingWindowAssigner {
	return &TumblingWindowAssigner{
		size:    size,
		windows: make(map[WindowKey]*WindowAccumulator),
	}
}

// AssignWindow определяет границы окна по Event Time.
func (a *TumblingWindowAssigner) AssignWindow(t time.Time) WindowKey {
	// Математическое выравнивание по сетке времени
	startUnix := t.Unix() - (t.Unix() % int64(a.size.Seconds()))
	start := time.Unix(startUnix, 0).UTC()
	end := start.Add(a.size)
	return WindowKey{Start: start, End: end}
}

// AddEvent добавляет событие в соответствующую корзину окна.
func (a *TumblingWindowAssigner) AddEvent(event TradeEvent) {
	windowKey := a.AssignWindow(event.Timestamp)
	acc, exists := a.windows[windowKey]
	if !exists {
		acc = &WindowAccumulator{}
		a.windows[windowKey] = acc
	}
	acc.TotalVolume += event.Volume
	acc.TradeCount++
}

// EmitAndPurge закрывает и очищает окна, чей End <= Watermark.
func (a *TumblingWindowAssigner) EmitAndPurge(watermark time.Time) {
	for wKey, acc := range a.windows {
		if !wKey.End.After(watermark) {
			// Окно готово к сбросу в БД
			fmt.Printf(" [WINDOW CLOSED] Интервал [%s - %s) | Сделок: %d | Объем: %d\n",
				wKey.Start.Format("15:04:05"), wKey.End.Format("15:04:05"),
				acc.TradeCount, acc.TotalVolume)

			// Очистка памяти: удаляем закрытое окно
			delete(a.windows, wKey)
		}
	}
}

func main() {
	assigner := NewTumblingWindowAssigner(1 * time.Minute)
	t0 := time.Date(2026, 9, 8, 14, 0, 0, 0, time.UTC)

	// Серия сделок в течение 3 минут
	trades := []TradeEvent{
		{Symbol: "BTC", Volume: 5, Timestamp: t0.Add(10 * time.Second)},  // Окно 14:00
		{Symbol: "BTC", Volume: 12, Timestamp: t0.Add(45 * time.Second)}, // Окно 14:00
		{Symbol: "BTC", Volume: 8, Timestamp: t0.Add(75 * time.Second)},  // Окно 14:01
		{Symbol: "BTC", Volume: 20, Timestamp: t0.Add(130 * time.Second)},// Окно 14:02
	}

	for _, tr := range trades {
		assigner.AddEvent(tr)
	}

	fmt.Println("=== Поступление Водяного Знака 14:01:30 ===")
	// Водяной знак закрывает окно 14:00-14:01, но оставляет открытым 14:01-14:02
	assigner.EmitAndPurge(t0.Add(90 * time.Second))

	fmt.Println("\n=== Поступление Водяного Знака 14:03:00 ===")
	// Водяной знак закрывает оставшиеся окна
	assigner.EmitAndPurge(t0.Add(180 * time.Second))
}
"""
            }
        ],
        "under_the_hood": "В тумблинговых окнах каждое событие обновляет ровно одну ячейку мапы. Использование инкрементального аккумулятора `WindowAccumulator` гарантирует, что мы не храним сами события в памяти, а поддерживаем только агрегированные счетчики ($O(1)$ памяти на окно). При удалении ключа из мапы рантайм Go освобождает память бакетов при последующих сборках мусора (GC).",
        "pitfalls": "При работе с часовыми поясами (Timezones) наивное деление `timestamp % 86400` для суточных окон вызовет сдвиг, так как полночь по UTC не совпадает с локальной полночью в Москве (UTC+3) или Токио (UTC+9). Всегда учитывайте смещение локального часового пояса (Zone Offset) при расчете границ окон.",
        "interview_qa": "В: Чем тумблинговое окно отличается от скользящего (sliding) окна?\nО: В тумблинговом окне длина окна равна шагу сдвига (`WindowSize == SlideStep`), поэтому окна стыкуются встык без зазоров и без перекрытий. В скользящем окне шаг сдвига меньше размера окна (`SlideStep < WindowSize`), поэтому окна перекрываются, и одно событие входит сразу в несколько соседних окон."
    },
    {
        "num": 6,
        "title": "Скользящие окна (Sliding / Hopping Windows)",
        "task": "Реализуйте скользящие окна с перекрытием: размер окна 10 минут, шаг сдвига (slide) 2 минуты. Покажите, что каждое входящее событие должно быть добавлено одновременно в несколько активных окон ($N = \text{WindowSize} / \text{SlideStep}$). Реализуйте эффективное хранение и инкрементальное обновление суммы, исключающее полный пересчет всех элементов при каждом сдвиге.",
        "theory": "Скользящие окна (Sliding / Hopping Windows) используются, когда метрики должны сглаживаться и обновляться чаще, чем длительность самого окна:\n- Пример: 'Скользящее среднее RPS за последние 10 минут, обновляемое каждые 2 минуты'.\n- Размер окна: $W = 10\text{ мин}$, шаг сдвига: $S = 2\text{ мин}$.\n- Коэффициент перекрытия: $K = W / S = 5$.\n\nЭто означает, что в любой момент времени одновременно активны 5 перекрывающихся окон, и каждое входящее событие обязано зарегистрироваться во всех 5 окнах!\n\n**Оптимизация хранения**:\nВместо наивного дублирования события в 5 списков, поток нарезается на мелкие неделимые кванты длительностью $S = 2\text{ мин}$ (Микро-бакеты / Panes). Большое окно вычисляется как быстрая сумма 5 готовых предвычисленных микро-бакетов!",
        "step_by_step": "1. Спроектируйте структуру `SlidingWindowAssigner` с параметрами `WindowSize` и `SlideStep`.\n2. Реализуйте метод генерации среза окон, в которые попадает событие.\n3. Добавьте событие во все релевантные перекрывающиеся корзины.\n4. Продемонстрируйте корректный вывод значений при сдвигах времени.",
        "code_blocks": [
            {
                "filename": "sliding_windows.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sort"
	"time"
)

type MetricEvent struct {
	Value     int
	Timestamp time.Time
}

type WindowRange struct {
	Start time.Time
	End   time.Time
}

// SlidingWindowAssigner распределяет событие по нескольким перекрывающимся окнам.
type SlidingWindowAssigner struct {
	windowSize time.Duration
	slideStep  time.Duration
	windows    map[WindowRange]int
}

func NewSlidingWindowAssigner(size, slide time.Duration) *SlidingWindowAssigner {
	return &SlidingWindowAssigner{
		windowSize: size,
		slideStep:  slide,
		windows:    make(map[WindowRange]int),
	}
}

// AssignWindows находит все активные перекрывающиеся окна для временной метки.
func (a *SlidingWindowAssigner) AssignWindows(t time.Time) []WindowRange {
	var result []WindowRange
	tUnix := t.Unix()
	slideSec := int64(a.slideStep.Seconds())
	sizeSec := int64(a.windowSize.Seconds())

	// Последнее окно, которое закрывается сразу после t
	lastStart := tUnix - (tUnix % slideSec)

	for start := lastStart; start > tUnix-sizeSec; start -= slideSec {
		wStart := time.Unix(start, 0).UTC()
		wEnd := wStart.Add(a.windowSize)
		// Проверяем, что событие лежит строго внутри интервала [Start, End)
		if !t.Before(wStart) && t.Before(wEnd) {
			result = append(result, WindowRange{Start: wStart, End: wEnd})
		}
	}
	return result
}

func (a *SlidingWindowAssigner) AddEvent(event MetricEvent) {
	ranges := a.AssignWindows(event.Timestamp)
	for _, r := range ranges {
		a.windows[r] += event.Value
	}
}

func (a *SlidingWindowAssigner) PrintActiveWindows() {
	var sortedKeys []WindowRange
	for k := range a.windows {
		sortedKeys = append(sortedKeys, k)
	}
	sort.Slice(sortedKeys, func(i, j int) bool {
		return sortedKeys[i].Start.Before(sortedKeys[j].Start)
	})

	for _, k := range sortedKeys {
		fmt.Printf("   Окно [%s - %s) -> Сумма: %d\n",
			k.Start.Format("15:04"), k.End.Format("15:04"), a.windows[k])
	}
}

func main() {
	// Окно 10 минут, шаг 2 минуты (коэффициент перекрытия 5)
	assigner := NewSlidingWindowAssigner(10*time.Minute, 2*time.Minute)

	baseTime := time.Date(2026, 9, 8, 12, 5, 30, 0, time.UTC) // 12:05:30

	fmt.Println("Событие произошло в 12:05:30 со значением 100.")
	assigner.AddEvent(MetricEvent{Value: 100, Timestamp: baseTime})

	fmt.Println("\nСобытие зарегистрировано одновременно в 5 перекрывающихся окнах:")
	assigner.PrintActiveWindows()
}
"""
            }
        ],
        "under_the_hood": "Если $WindowSize / SlideStep$ велико (например, окно 1 час с шагом 1 секунда, коэффициент $K = 3600$), наивная вставка в 3600 окон приведет к падению производительности процессора. Промышленные движки (Flink/Blink) используют технику **Pane Aggregation**: поток агрегируется в кванты по 1 секунде, а при сдвиге скользящего окна из суммы вычитается самый старый квант и прибавляется самый новый по принципу очереди со скользящей суммой: $Sum_{new} = Sum_{prev} - Pane_{oldest} + Pane_{newest}$ за $O(1)$.",
        "pitfalls": "При наивной реализации скользящих окон память расходуется пропорционально коэффициенту перекрытия $K$. Следите за тем, чтобы шаг сдвига (Slide) не был слишком мелким без применения техники квантования (Pane Aggregation).",
        "interview_qa": "В: Как реализовать скользящее окно с вычислением 99-го перцентиля (p99 latency), где нельзя просто применить формулу вычитания старого кванта?\nО: Перцентиль не является дистрибутивной или абелевой операцией (его нельзя вычесть). В таких случаях кванты (Panes) сохраняют сжатые гистограммы (t-digest, HdrHistogram или DDSketch). Скользящий перцентиль вычисляется объединением (Merge) гистограмм нескольких активных квантов окна за $O(K)$, что в тысячи раз быстрее пересчета всех сырых событий."
    },
    {
        "num": 7,
        "title": "Сессионные окна (Session Windows) по интервалу неактивности",
        "task": "В веб-аналитике действия пользователя объединяются в сессию, если пауза между кликами не превышает заданный порог (Inactivity Gap, например, 30 минут). Напишите алгоритм слияния сессионных окон (Session Window Merger): при поступлении события в промежуток между двумя окнами эти окна динамически объединяются в одну непрерывную сессию.",
        "theory": "В отличие от тумблинговых и скользящих окон, **Сессионные окна (Session Windows)** не имеют фиксированной длительности и не привязаны к сетке времени:\n- Окно определяется периодом активности пользователя, за которым следует период неактивности длительностью не менее `InactivityGap`.\n- Каждое новое событие изначально создает микро-сессию `[EventTime, EventTime + Gap)`.\n- **Алгоритм слияния (Window Merging)**: если два окна пересекаются или соприкасаются, они объединяются в одно расширенное окно `[min(Start), max(End))`.\n- Если событие приходит 'из прошлого' и попадает в зазор между двумя ранее изолированными сессиями, происходит слияние трех окон в одну большую непрерывную сессию!",
        "step_by_step": "1. Спроектируйте структуру `Session` (UserID, Start, End, EventCount).\n2. Реализуйте алгоритм слияния интервалов (Interval Merge Algorithm).\n3. При поступлении события проверьте пересечение с существующими сессиями пользователя.\n4. Объедините пересекающиеся сессии и сагрегируйте счетчики.",
        "code_blocks": [
            {
                "filename": "session_windows.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sort"
	"time"
)

type UserClick struct {
	UserID    string
	Timestamp time.Time
}

type Session struct {
	Start      time.Time
	End        time.Time
	EventCount int
}

type SessionTracker struct {
	gap      time.Duration
	sessions map[string][]Session // UserID -> список сессий
}

func NewSessionTracker(gap time.Duration) *SessionTracker {
	return &SessionTracker{
		gap:      gap,
		sessions: make(map[string][]Session),
	}
}

// AddEvent добавляет событие и динамически сливает пересекающиеся сессии.
func (st *SessionTracker) AddEvent(event UserClick) {
	// Новое событие порождает начальный интервал [t, t + gap]
	newSession := Session{
		Start:      event.Timestamp,
		End:        event.Timestamp.Add(st.gap),
		EventCount: 1,
	}

	userSessions := st.sessions[event.UserID]
	userSessions = append(userSessions, newSession)

	// Сортируем интервалы по времени старта
	sort.Slice(userSessions, func(i, j int) bool {
		return userSessions[i].Start.Before(userSessions[j].Start)
	})

	// Алгоритм слияния (Merge Intervals)
	var merged []Session
	current := userSessions[0]

	for i := 1; i < len(userSessions); i++ {
		next := userSessions[i]
		// Если следующий интервал начинается ДО окончания текущего (пересечение или стык)
		if !next.Start.After(current.End) {
			// Сливаем интервалы!
			if next.End.After(current.End) {
				current.End = next.End
			}
			current.EventCount += next.EventCount
		} else {
			merged = append(merged, current)
			current = next
		}
	}
	merged = append(merged, current)

	st.sessions[event.UserID] = merged
}

func main() {
	tracker := NewSessionTracker(30 * time.Minute) // Порог разрыва сессии — 30 минут
	t0 := time.Date(2026, 9, 8, 15, 0, 0, 0, time.UTC)

	// События пользователя Alice
	clicks := []UserClick{
		{UserID: "alice", Timestamp: t0},                      // 15:00 -> [15:00 - 15:30]
		{UserID: "alice", Timestamp: t0.Add(10 * time.Minute)}, // 15:10 -> продлевает до 15:40
		{UserID: "alice", Timestamp: t0.Add(90 * time.Minute)}, // 16:30 -> новая сессия [16:30 - 17:00]
	}

	for _, c := range clicks {
		tracker.AddEvent(c)
	}

	fmt.Println("=== Сессии Alice после 3 кликов ===")
	for i, s := range tracker.sessions["alice"] {
		fmt.Printf("Сессия %d: [%s - %s] (Кликов: %d)\n",
			i+1, s.Start.Format("15:04"), s.End.Format("15:04"), s.EventCount)
	}

	fmt.Println("\nВнезапно приходит опоздавшее событие за 15:50, соединяющее две сессии!")
	tracker.AddEvent(UserClick{UserID: "alice", Timestamp: t0.Add(50 * time.Minute)}) // 15:50

	fmt.Println("=== Сессии Alice после слияния ===")
	for i, s := range tracker.sessions["alice"] {
		fmt.Printf("Сессия %d: [%s - %s] (Кликов: %d)\n",
			i+1, s.Start.Format("15:04"), s.End.Format("15:04"), s.EventCount)
	}
}
"""
            }
        ],
        "under_the_hood": "Сессионные окна являются наиболее сложным типом окон, поскольку они мутируют (Merge) уже существующее состояние. В распределенных системах при слиянии двух окон оператор обязан слить не только временные границы, но и их внутренние состояния (State Aggregates). Это требует, чтобы функции агрегации поддерживали интерфейс `MergeableAccumulator`.",
        "pitfalls": "Если `InactivityGap` выбран слишком большим для пользователя-бота, непрерывно кликающего сайт раз в 20 минут, его сессия никогда не прервется и будет расти неделями, переполняя память. Всегда ограничивайте максимальную продолжительность одной сессии параметром `MaxSessionDuration` (например, принудительное закрытие через 24 часа).",
        "interview_qa": "В: Как закрываются сессионные окна в присутствии Watermark?\nО: Сессионное окно считается завершенным и сбрасывается в хранилище, когда текущий водяной знак $W \ge Session.End$. После этого сессия финализируется, а опоздавшие события могут обрабатываться только через механизм Side Output или создание новой сессии."
    },
    {
        "num": 8,
        "title": "Встроенное хранилище состояния (State Store) на Pebble / BadgerDB",
        "task": "Потоковая обработка не может зависеть от внешних сетевых запросов в СУБД для каждого события. Подключите встраиваемый LSM-движок `cockroachdb/pebble` или `dgraph-io/badger` как локальный State Store. Реализуйте методы `PutState(key, state)`, `GetState(key)` и замерьте задержку чтения/записи (субмиллисекундный доступ под микросекундные SLA).",
        "theory": "В потоковых конвейерах со скоростью 100 000+ событий в секунду делать сетевой запрос в PostgreSQL или даже Redis на каждое событие невозможно из-за сетевой латентности (0.5–2 мс на RTT сокета исчерпают пул соединений).\n\nПо этой причине все промышленные движки (Flink RocksDB StateBackend, Kafka Streams RocksDB) используют **встраиваемые локальные LSM-хранилища (Embedded State Stores)**:\n- База данных компилируется прямо внутрь Go-бинарника.\n- Данные хранятся на локальном сверхбыстром NVMe SSD того же сервера.\n- Чтение и запись выполняются через оперативную память (MemTable) и блочный кэш за **1–5 микросекунд** без сетевых накладных расходов!\n\nВ экосистеме Go лучшими решениями являются `cockroachdb/pebble` (LSM-движок от CockroachDB, вдохновленный RocksDB/LevelDB) и `dgraph-io/badger` (чистый Go с разделением ключей и значений по схеме WiscKey).",
        "step_by_step": "1. Спроектируйте потокобезопасный интерфейс `StateStore`.\n2. Реализуйте легковесный in-memory LSM симулятор или обертку над Pebble/Badger.\n3. Реализуйте сериализацию и десериализацию промежуточного состояния агрегата.\n4. Замерьте бенчмарк задержки записи 50 000 операций.",
        "code_blocks": [
            {
                "filename": "state_store.go",
                "lang": "go",
                "code": r"""package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"sync"
	"time"
)

// UserSessionState представляет сериализуемое состояние агрегата в LSM-хранилище.
type UserSessionState struct {
	TotalSpendCents int64
	LastEventUnix   int64
	ItemCount       int32
}

func (s *UserSessionState) Encode() []byte {
	buf := new(bytes.Buffer)
	_ = binary.Write(buf, binary.LittleEndian, s.TotalSpendCents)
	_ = binary.Write(buf, binary.LittleEndian, s.LastEventUnix)
	_ = binary.Write(buf, binary.LittleEndian, s.ItemCount)
	return buf.Bytes()
}

func (s *UserSessionState) Decode(data []byte) error {
	buf := bytes.NewReader(data)
	if err := binary.Read(buf, binary.LittleEndian, &s.TotalSpendCents); err != nil {
		return err
	}
	if err := binary.Read(buf, binary.LittleEndian, &s.LastEventUnix); err != nil {
		return err
	}
	return binary.Read(buf, binary.LittleEndian, &s.ItemCount)
}

// EmbeddedLSMStore — концептуальная модель встроенного хранилища (Badger/Pebble).
type EmbeddedLSMStore struct {
	mu   sync.RWMutex
	data map[string][]byte
}

func NewEmbeddedStore() *EmbeddedLSMStore {
	return &EmbeddedLSMStore{
		data: make(map[string][]byte),
	}
}

func (s *EmbeddedLSMStore) PutState(key string, state *UserSessionState) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.data[key] = state.Encode()
}

func (s *EmbeddedLSMStore) GetState(key string) (*UserSessionState, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	raw, exists := s.data[key]
	if !exists {
		return nil, false
	}
	var state UserSessionState
	_ = state.Decode(raw)
	return &state, true
}

func main() {
	store := NewEmbeddedStore()
	const operations = 100_000

	fmt.Println("=== Тестирование производительности встроенного State Store ===")
	start := time.Now()

	// Имитация высоконагруженной записи в локальное состояние
	for i := 0; i < operations; i++ {
		key := fmt.Sprintf("user_session_%d", i%1000)
		state := &UserSessionState{
			TotalSpendCents: int64(i * 15),
			LastEventUnix:   time.Now().Unix(),
			ItemCount:       int32(i % 50),
		}
		store.PutState(key, state)
	}

	elapsed := time.Since(start)
	opsPerSec := float64(operations) / elapsed.Seconds()
	avgLatencyMicro := float64(elapsed.Microseconds()) / float64(operations)

	fmt.Printf("✅ Выполнено %d операций за %v\n", operations, elapsed)
	fmt.Printf("⚡ Скорость: %.0f ops/sec\n", opsPerSec)
	fmt.Printf("⏱ Средняя задержка: %.2f микросекунд (μs)\n", avgLatencyMicro)

	// Чтение состояния
	sampleState, _ := store.GetState("user_session_42")
	fmt.Printf("Проверка чтения: TotalSpend = %d центов, Items = %d\n",
		sampleState.TotalSpendCents, sampleState.ItemCount)
}
"""
            }
        ],
        "under_the_hood": "LSM-деревья (Log-Structured Merge-tree) организуют запись исключительно последовательно (Sequential Append-Only) в MemTable и журнал предзаписи (WAL). Это дает субмикросекундную запись без блокировок случайного доступа диска. При переполнении MemTable сбрасывается на диск в виде неизменяемых SSTable-файлов. Чтение ускоряется фильтрами Блума в оперативной памяти, отсекающими ненужные чтения с диска.",
        "pitfalls": "Если локальный диск контейнера переполнится из-за отсутствия TTL-очистки или остановки компактификации LSM, процесс аварийно завершится. Всегда монтируйте отдельный персистентный том (PersistentVolumeClaim) для State Store и настраивайте периодическую компактификацию.",
        "interview_qa": "В: Как восстановить локальное состояние встроенного State Store, если сервер или Kubernetes-под сгорел?\nО: Для этого используется паттерн **Changelog Topic**: каждое изменение состояния дублируется в специальный компактный топик Kafka (Compacted Topic). При поднятии нового пода на другой машине воркер вычитывает компактный топик с нулевого оффсета и за считанные секунды восстанавливает локальное LSM-хранилище до актуального состояния."
    },
    {
        "num": 9,
        "title": "Инкрементальные агрегации в потоке (Streaming Aggregations)",
        "task": "Вместо накопления всех событий окна в памяти напишите агрегатор с инкрементальным свертыванием: структуры `Count`, `Sum`, `MinMax` обновляются по формулам онлайн-статистики (алгоритм Велфорда для дисперсии и стандартного отклонения). Докажите, что потребление памяти остается строго константным $O(1)$ независимо от миллионов событий внутри окна.",
        "theory": "Худший антипаттерн потоковой обработки — сбор всех событий за 1 час в срез (`[]Event`) для последующего вызова `CalculateStats(events)`. Если за час придет 100 000 000 событий, сервер исчерпает 50 ГБ оперативной памяти.\n\nПрофессиональная потоковая обработка опирается на **онлайн-алгоритмы инкрементального свертывания (Streaming Aggregations)**:\n- Сумма: $S_{n} = S_{n-1} + x_n$\n- Минимум/Максимум: $\min_n = \min(\min_{n-1}, x_n)$\n- **Алгоритм Велфорда (Welford's Algorithm)**: вычисляет математическое ожидание (Mean) и дисперсию (Variance) за один проход с абсолютной числовой стабильностью без риска переполнения float64:\n  $$M_k = M_{k-1} + (x_k - M_{k-1}) / k$$\n  $$S_k = S_{k-1} + (x_k - M_{k-1})(x_k - M_k)$$\n  $$\sigma^2 = S_k / (k - 1)$$\nПамять: ровно 3 числа (`count`, `mean`, `M2`) вместо сохранения миллионов точек!",
        "step_by_step": "1. Реализуйте структуру `WelfordAggregator` для расчета среднего и дисперсии.\n2. Реализуйте метод `Update(val float64)` с пересчетом по алгоритму Велфорда.\n3. Сгенерируйте поток из 1 000 000 случайных измерений.\n4. Докажите, что потребление памяти составляет ровно 24 байта.",
        "code_blocks": [
            {
                "filename": "welford_aggregation.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"math"
	"math/rand"
	"unsafe"
)

// WelfordAggregator вычисляет точное среднее и стандартное отклонение в потоке O(1) памяти.
type WelfordAggregator struct {
	count int64
	mean  float64
	m2    float64
	min   float64
	max   float64
}

func NewWelfordAggregator() *WelfordAggregator {
	return &WelfordAggregator{
		min: math.MaxFloat64,
		max: -math.MaxFloat64,
	}
}

// Update выполняет онлайн-свертывание нового значения за O(1).
func (w *WelfordAggregator) Update(x float64) {
	w.count++
	delta := x - w.mean
	w.mean += delta / float64(w.count)
	delta2 := x - w.mean
	w.m2 += delta * delta2

	if x < w.min {
		w.min = x
	}
	if x > w.max {
		w.max = x
	}
}

func (w *WelfordAggregator) Variance() float64 {
	if w.count < 2 {
		return 0.0
	}
	return w.m2 / float64(w.count-1)
}

func (w *WelfordAggregator) StdDev() float64 {
	return math.Sqrt(w.Variance())
}

func main() {
	agg := NewWelfordAggregator()
	const streamSize = 1_000_000

	fmt.Println("=== Инкрементальная агрегация Велфорда в потоке ===")
	fmt.Printf("Размер структуры аккумулятора в RAM: %d байт!\n", unsafe.Sizeof(*agg))

	// Генерируем 1 000 000 событий с нормальным распределением (Mean=50.0, StdDev=5.0)
	r := rand.New(rand.NewSource(42))
	for i := 0; i < streamSize; i++ {
		val := r.NormFloat64()*5.0 + 50.0
		agg.Update(val)
	}

	fmt.Printf("\nРезультаты обработки 1 000 000 событий:\n")
	fmt.Printf("   Количество: %d событий\n", agg.count)
	fmt.Printf("   Среднее (Mean): %.4f (Ожидалось: 50.0)\n", agg.mean)
	fmt.Printf("   Стандартное отклонение (StdDev): %.4f (Ожидалось: 5.0)\n", agg.StdDev())
	fmt.Printf("   Min: %.2f | Max: %.2f\n", agg.min, agg.max)
	fmt.Println("✅ Доказано: 1 миллион чисел обработан в неизменных 40 байтах оперативной памяти!")
}
"""
            }
        ],
        "under_the_hood": "Классическая формула дисперсии $\text{Var} = \frac{\sum x^2 - (\sum x)^2 / n}{n}$ страдает от катастрофической потери значимости (Catastrophic Cancellation) при вычислениях с плавающей точкой в float64, когда два близких больших числа вычитаются друг из друга. Алгоритм Б. П. Велфорда (1962) решает эту проблему путем обновления отклонений от бегущего среднего, гарантируя численную устойчивость на миллиардах итераций.",
        "pitfalls": "Не пытайтесь вычислять медиану (50th percentile) простым аккумулятором. Медиана не является инкрементальной алгебраической величиной. Для расчета медианы и перцентилей в потоке $O(1)$ памяти используйте вероятностные структуры (t-digest, HdrHistogram).",
        "interview_qa": "В: Какие функции агрегации в потоковой обработке называют Algebraic, а какие Holistic?\nО: **Algebraic** функции (Mean, Variance, Count, Sum) могут быть вычислены из конечного набора промежуточных аккумуляторов фиксированного размера. **Holistic** функции (Median, Mode, Exact Distinct Count) требуют анализа всего распределения данных и не могут быть вычислены точно без сохранения всех элементов или применения вероятностных эвристик."
    },
    {
        "num": 10,
        "title": "Вероятностный подсчет уникальных пользователей (HyperLogLog)",
        "task": "Подсчет уникальных посетителей (Unique Active Users) в потоковом окне требует сохранения множества `map[string]struct{}`, что приводит к исчерпанию RAM при миллионах ключей. Интегрируйте вероятностный алгоритм HyperLogLog. Покажите, как HLL оценивает кардинальность с точностью до 1–2% при потреблении всего 1.5 КБ памяти вместо сотен мегабайт.",
        "theory": "Подсчет точного количества уникальных элементов (Count-Distinct Problem / Cardinality Estimation):\n- Для 100 000 000 UUID ключей сохранение в `map[string]struct{}` потребует более **5–8 ГБ RAM**!\n- При наличии сотен тысяч окон или тенантов сервер мгновенно упадет по памяти.\n\nРешение — **HyperLogLog (Flajolet et al., 2007)**:\n1. Хэширует входящий ключ в 64-битное число.\n2. Смотрит на количество лидирующих нулей в бинарном представлении хэша.\n3. Вероятность встретить последовательность из $k$ нулей подряд равна $2^{-k}$. Заметив длинную последовательность нулей, алгоритм оценивает общий объем множества.\n4. Для подавления дисперсии пространство делится на $m = 2^p$ регистров (например, $m=1024$ при $p=10$). Оценка вычисляется как гармоническое среднее по всем регистрам.\n5. Стандартная ошибка составляет $\approx 1.04 / \sqrt{m}$.\n6. Память: фиксированные **1.5 КБ** независимо от того, 100 человек пришло или 10 миллиардов!",
        "step_by_step": "1. Реализуйте компактную версию HyperLogLog на чистом Go.\n2. Настройте массив регистров $m=1024$ байт.\n3. Реализуйте метод `Add(key string)` с 64-битным хэшированием FNV-1a.\n4. Вычислите оценку кардинальности по формуле гармонического среднего.\n5. Сравните точность оценки с точным `map[string]struct{}` на 100 000 элементов.",
        "code_blocks": [
            {
                "filename": "hyperloglog.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"hash/fnv"
	"math"
	"math/bits"
	"unsafe"
)

// MiniHyperLogLog реализует вероятностный подсчет кардинальности.
type MiniHyperLogLog struct {
	p         uint8    // Число бит для индекса регистра (10 -> m=1024)
	m         uint32   // Количество регистров
	registers []uint8  // Массив регистров
	alphaMM   float64  // Константа нормализации
}

func NewMiniHyperLogLog(precision uint8) *MiniHyperLogLog {
	m := uint32(1) << precision
	var alpha float64
	switch m {
	case 16:
		alpha = 0.673
	case 32:
		alpha = 0.697
	case 64:
		alpha = 0.709
	default:
		alpha = 0.7213 / (1.0 + 1.079/float64(m))
	}

	return &MiniHyperLogLog{
		p:         precision,
		m:         m,
		registers: make([]uint8, m),
		alphaMM:   alpha * float64(m) * float64(m),
	}
}

func (hll *MiniHyperLogLog) hash(s string) uint64 {
	h := fnv.New64a()
	_, _ = h.Write([]byte(s))
	return h.Sum64()
}

func (hll *MiniHyperLogLog) Add(item string) {
	x := hll.hash(item)
	// Первые p бит определяют индекс регистра
	idx := x >> (64 - hll.p)
	// Оставшиеся биты используются для подсчета лидирующих нулей
	w := (x << hll.p) | (1 << (hll.p - 1))
	leadingZeros := uint8(bits.LeadingZeros64(w)) + 1

	if leadingZeros > hll.registers[idx] {
		hll.registers[idx] = leadingZeros
	}
}

func (hll *MiniHyperLogLog) Count() uint64 {
	sum := 0.0
	for _, val := range hll.registers {
		sum += 1.0 / math.Pow(2.0, float64(val))
	}

	estimate := hll.alphaMM / sum

	// Коррекция малых множеств (Linear Counting)
	if estimate <= 2.5*float64(hll.m) {
		zeros := 0
		for _, val := range hll.registers {
			if val == 0 {
				zeros++
			}
		}
		if zeros > 0 {
			estimate = float64(hll.m) * math.Log(float64(hll.m)/float64(zeros))
		}
	}

	return uint64(estimate)
}

func main() {
	// Точность p=10 -> 1024 регистра (ровно 1024 байта RAM!)
	hll := NewMiniHyperLogLog(10)
	exactMap := make(map[string]struct{})

	const uniqueUsers = 100_000

	fmt.Println("=== Сравнение точного Map vs HyperLogLog ===")
	for i := 0; i < uniqueUsers; i++ {
		userID := fmt.Sprintf("user_uuid_v4_%d", i)
		exactMap[userID] = struct{}{}
		hll.Add(userID)
	}

	hllEstimate := hll.Count()
	errorPercent := math.Abs(float64(hllEstimate)-float64(uniqueUsers)) / float64(uniqueUsers) * 100.0

	fmt.Printf("Истинное количество уникальных пользователей: %d\n", uniqueUsers)
	fmt.Printf("Оценка алгоритма HyperLogLog:             %d\n", hllEstimate)
	fmt.Printf("Погрешность оценки:                         %.2f%%\n", errorPercent)
	fmt.Printf("Память точной мапы:                         ~%d КБ\n", (len(exactMap)*64)/1024)
	fmt.Printf("Память структуры HyperLogLog:               %d байт!\n", unsafe.Sizeof(*hll)+uintptr(len(hll.registers)))
}
"""
            }
        ],
        "under_the_hood": "HyperLogLog обладает свойством ассоциативности и коммутативности слияния (Mergeable State): два HLL аккумулятора можно мгновенно объединить покомпонентной операцией `merged[i] = max(hllA[i], hllB[i])`. Это позволяет параллельно вычислять уникальных пользователей на сотнях воркеров и объединять результаты без передачи сырых данных по сети.",
        "pitfalls": "Качество хэш-функции критично для HyperLogLog. Использование слабых хэшей с неравномерным распределением битов (например, простая CRC32) приведет к смещению оценки и ошибкам в десятки процентов. Используйте 64-битные или 128-битные криптографически стойкие или качественные некриптографические хэши (MurmurHash3, MetroHash, xxHash).",
        "interview_qa": "В: Как HyperLogLog решает проблему подсчета уникальных пользователей в пересекающихся скользящих окнах?\nО: Поскольку из HyperLogLog нельзя 'вычесть' ушедшие элементы, для скользящих окон применяют комбинацию: временная шкала нарезается на мелкие кванты, в каждом из которых ведется свой HLL. Большое окно вычисляется операцией `Merge` соответствующих квантов за доли миллисекунды."
    },
    {
        "num": 11,
        "title": "Соединение потоков (Stream-Stream Join)",
        "task": "Реализуйте потоковое соединение двух независимых потоков событий: поток показов рекламы (`AdImpressionEvent`) и поток покупок товаров (`OrderEvent`). Соединение выполняется по `user_id` в пределах 15-минутного временного окна (Join Window). События буферизуются в локальном State Store до прихода пары или истечения окна.",
        "theory": "Соединение потоков (Stream-Stream Join) — одна из сложнейших задач распределенной обработки:\n- В реляционных БД операция `JOIN` выполняется над двумя статическими таблицами на диске.\n- В потоках оба источника бесконечны, а события приходят в произвольное время с сетевыми задержками.\n\nДля соединения потоков вводится **временное окно соединения (Join Window)**:\n'Событие $A$ соединяется с событием $B$, если $Key_A == Key_B$ и $|Timestamp_A - Timestamp_B| \le \Delta t$'.\n\n**Механика исполнения**:\n1. При получении события из Потока 1 мы сохраняем его в локальный State Store 1 и проверяем, нет ли уже подходящего события в State Store 2.\n2. При получении события из Потока 2 мы сохраняем его в State Store 2 и проверяем State Store 1.\n3. Если совпадение найдено — генерируется соединенное событие `EnrichedAttributionEvent`.\n4. По наступлении водяного знака устаревшие события, не дождавшиеся пары, удаляются из хранилища (TTL Eviction).",
        "step_by_step": "1. Опишите структуры `AdImpression` (AdID, UserID, Time) и `Purchase` (OrderID, UserID, Amount, Time).\n2. Реализуйте структуру `StreamJoiner` с двумя внутренними буферами по ключу UserID.\n3. При поступлении события из любого потока выполняйте поиск пары в пределах `15*time.Minute`.\n4. Продемонстрируйте сопоставление клика и покупки.",
        "code_blocks": [
            {
                "filename": "stream_join.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"time"
)

type AdImpression struct {
	AdID      string
	UserID    string
	Timestamp time.Time
}

type Purchase struct {
	OrderID   string
	UserID    string
	Amount    float64
	Timestamp time.Time
}

type AttributionResult struct {
	UserID     string
	AdID       string
	OrderID    string
	Amount     float64
	TimeToConv time.Duration
}

// StreamJoiner выполняет соединение двух потоков во временном окне.
type StreamJoiner struct {
	joinWindow time.Duration
	leftStore  map[string][]AdImpression // UserID -> показы
	rightStore map[string][]Purchase     // UserID -> покупки
}

func NewStreamJoiner(window time.Duration) *StreamJoiner {
	return &StreamJoiner{
		joinWindow: window,
		leftStore:  make(map[string][]AdImpression),
		rightStore: make(map[string][]Purchase),
	}
}

// ProcessImpression обрабатывает событие левого потока (показ рекламы).
func (j *StreamJoiner) ProcessImpression(imp AdImpression) *AttributionResult {
	// Сохраняем в левый буфер
	j.leftStore[imp.UserID] = append(j.leftStore[imp.UserID], imp)

	// Ищем совпадения в правом буфере
	if purchases, exists := j.rightStore[imp.UserID]; exists {
		for _, p := range purchases {
			diff := p.Timestamp.Sub(imp.Timestamp)
			if diff >= 0 && diff <= j.joinWindow {
				return &AttributionResult{
					UserID:     imp.UserID,
					AdID:       imp.AdID,
					OrderID:    p.OrderID,
					Amount:     p.Amount,
					TimeToConv: diff,
				}
			}
		}
	}
	return nil
}

// ProcessPurchase обрабатывает событие правого потока (покупка).
func (j *StreamJoiner) ProcessPurchase(p Purchase) *AttributionResult {
	// Сохраняем в правый буфер
	j.rightStore[p.UserID] = append(j.rightStore[p.UserID], p)

	// Ищем совпадения в левом буфере
	if impressions, exists := j.leftStore[p.UserID]; exists {
		for _, imp := range impressions {
			diff := p.Timestamp.Sub(imp.Timestamp)
			if diff >= 0 && diff <= j.joinWindow {
				return &AttributionResult{
					UserID:     p.UserID,
					AdID:       imp.AdID,
					OrderID:    p.OrderID,
					Amount:     p.Amount,
					TimeToConv: diff,
				}
			}
		}
	}
	return nil
}

func main() {
	joiner := NewStreamJoiner(15 * time.Minute)
	t0 := time.Date(2026, 9, 8, 16, 0, 0, 0, time.UTC)

	// 1. Пользователь "user_10" видит баннер в 16:00
	imp := AdImpression{AdID: "banner_black_friday", UserID: "user_10", Timestamp: t0}
	res1 := joiner.ProcessImpression(imp)
	fmt.Printf("16:00 - Показ баннера: Match found? %v\n", res1 != nil)

	// 2. Пользователь "user_10" покупает товар через 5 минут (в 16:05)
	pur := Purchase{OrderID: "ord_9901", UserID: "user_10", Amount: 4990.0, Timestamp: t0.Add(5 * time.Minute)}
	res2 := joiner.ProcessPurchase(pur)

	if res2 != nil {
		fmt.Printf("\n🎉 [STREAM JOIN УСПЕШЕН!] Найдена конверсия!\n")
		fmt.Printf("   User: %s | Реклама: %s | Заказ: %s | Сумма: %.2f руб | Время до покупки: %v\n",
			res2.UserID, res2.AdID, res2.OrderID, res2.Amount, res2.TimeToConv)
	}
}
"""
            }
        ],
        "under_the_hood": "В распределенном Stream-Stream Join (например, в Apache Flink или Kafka Streams) оба входных топика обязаны быть ко-партиционированы (Co-Partitioned): события из обоих потоков с одинаковым ключом `user_id` должны попадать в партиции с одинаковым номером. Это гарантирует, что один воркер обрабатывает обе половины ключа локально в своем State Store без межнодового сетевого обмена.",
        "pitfalls": "Если не настроить удаление старых событий по Watermark (Eviction), размер State Store в Stream-Stream Join будет непрерывно расти и переполнит диск. Храните только события в пределах `JoinWindow + AllowedLateness`.",
        "interview_qa": "В: В чем разница между Inner Join, Left Outer Join и Full Outer Join в потоковой обработке?\nО: При **Inner Join** событие эмитится только при нахождении пары в окне. При **Left Outer Join**, если для события левого потока пара из правого потока так и не пришла до момента истечения окна (Watermark > WindowEnd), система эмитит событие с пустыми полями правой стороны (`AdImpression + NULL`)."
    },
    {
        "num": 12,
        "title": "Обогащение потока данными таблицы (Stream-Table Join / Enrichment)",
        "task": "Поток событий заказов содержит только `product_id`. Реализуйте обогащение потока метаданными товара (название, категория, вес) из таблицы справочника. Примените паттерн локального кэширования с периодическим обновлением (Cache Refresh) или подпиской на Change Data Capture (CDC), чтобы исключить сетевые задержки при обработке потока.",
        "theory": "В потоках сообщений полезная нагрузка часто нормализована для экономии сетевого трафика: событие транзакции содержит лишь `product_id: 1042`, но аналитике и скорингу требуются название бренда, категория товара, цена и страна происхождения.\n\nПаттерн **Stream-Table Join (Обогащение потока)**:\n1. **Антипаттерн**: вызывать `db.Query('SELECT * FROM products WHERE id = ?')` на каждое событие в потоке из 50k RPS. База ляжет за секунды.\n2. **Решение 1 (Local Cache)**: репликация справочника продуктов в локальную in-memory таблицу с периодической инвалидацией.\n3. **Решение 2 (CDC / KTable Dual-Stream)**: подписка на топик изменений таблицы из Debezium/Kafka. Воркер держит обновляемую копию таблицы в локальном RocksDB/Pebble и обогащает поток за микросекунды.",
        "step_by_step": "1. Опишите структуру `ProductMetadata` и событие `OrderEvent`.\n2. Реализуйте потокобезопасный `MetadataCache` со сжатым хранением справочника.\n3. Реализуйте фоновое обновление кэша (Refresh Loop).\n4. Напишите функцию обогащения потока `EnrichOrderStream`.",
        "code_blocks": [
            {
                "filename": "enrichment.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

type ProductMetadata struct {
	Name     string
	Category string
	Price    float64
}

type OrderEvent struct {
	OrderID   string
	ProductID int
	Quantity  int
}

type EnrichedOrderEvent struct {
	OrderID     string
	ProductID   int
	ProductName string
	Category    string
	TotalCost   float64
}

// MetadataCache хранит локальную реплику справочной таблицы.
type MetadataCache struct {
	mu       sync.RWMutex
	products map[int]ProductMetadata
}

func NewMetadataCache() *MetadataCache {
	return &MetadataCache{
		products: make(map[int]ProductMetadata),
	}
}

func (c *MetadataCache) Get(productID int) (ProductMetadata, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	meta, exists := c.products[productID]
	return meta, exists
}

func (c *MetadataCache) Update(productID int, meta ProductMetadata) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.products[productID] = meta
}

func main() {
	cache := NewMetadataCache()

	// Первоначальная загрузка справочника в память
	cache.Update(101, ProductMetadata{Name: "Ноутбук ThinkPad", Category: "Электроника", Price: 120_000.0})
	cache.Update(102, ProductMetadata{Name: "Кофемашина DeLonghi", Category: "Бытовая техника", Price: 45_000.0})

	// Входящий поток заказов
	orders := []OrderEvent{
		{OrderID: "ord_1", ProductID: 101, Quantity: 1},
		{OrderID: "ord_2", ProductID: 102, Quantity: 2},
		{OrderID: "ord_3", ProductID: 999, Quantity: 1}, // Неизвестный товар
	}

	fmt.Println("=== Потоковое обогащение (Stream-Table Join) ===")
	for _, ord := range orders {
		meta, found := cache.Get(ord.ProductID)
		if !found {
			fmt.Printf(" [ENRICH ERROR] Товар %d не найден в кэше! Отправка в Dead Letter Queue.\n", ord.ProductID)
			continue
		}

		enriched := EnrichedOrderEvent{
			OrderID:     ord.OrderID,
			ProductID:   ord.ProductID,
			ProductName: meta.Name,
			Category:    meta.Category,
			TotalCost:   meta.Price * float64(ord.Quantity),
		}

		fmt.Printf(" [ENRICHED] Заказ %s: '%s' (%s) x%d = %.2f руб\n",
			enriched.OrderID, enriched.ProductName, enriched.Category, ord.Quantity, enriched.TotalCost)
	}
}
"""
            }
        ],
        "under_the_hood": "В архитектуре Kafka Streams концепция Stream-Table Join формализована как объединение `KStream` (бесконечный поток изменений) и `KTable` (материализованное состояние таблицы). Каждое событие из KTable обновляет локальный RocksDB State Store. Когда через KStream проходит запись, она делает мгновенный `Get()` в локальный RocksDB без сетевых раунд-трипов, обеспечивая задержку обогащения менее 10 микросекунд.",
        "pitfalls": "Проблема рассинхронизации времени (Temporal Join Problem): если заказ был сделан 1 сентября по старой цене 100 руб, а поток догнал таблицу 2 сентября, когда цена поднялась до 150 руб, наивное обогащение из текущей таблицы применит неверную цену! Для исторических потоков используйте Versioned KTable (Temporal Tables) с поиском цены на момент `Order.EventTime`.",
        "interview_qa": "В: Что делать, если справочная таблица слишком велика и не помещается целиком в оперативную память воркера?\nО: Используйте шардирование по ключу (Key-Partitioning) в Kafka: партиционируйте поток заказов и топик таблицы по `product_id`. В этом случае каждый воркер будет хранить в локальном State Store только свою 1/N часть справочника товаров."
    },
    {
        "num": 13,
        "title": "Дедупликация событий в скользящем окне",
        "task": "Из-за сетевых сбоев и повторных попыток продюсеры могут присылать дублирующиеся события. Реализуйте потоковый дедупликатор: идентификаторы событий `event_id` сохраняются в кольцевой буфер или фильтр Блума со скользящим окном жизни (TTL 10 минут). Если событие уже встречалось в окне, оно отбрасывается без передачи вниз по конвейеру.",
        "theory": "В распределенных сетях сбои отправки неизбежны. Продюсер отправляет платеж, брокер сохраняет его, но подтверждение (ACK) теряется в сети. Продюсер повторяет отправку (Retry), в результате чего в поток попадает дубликат события.\n\nДля предотвращения повторного списания денег или искажения аналитики на входе конвейера устанавливается **Deduplication Filter**:\n1. Каждое событие обязано содержать уникальный детерминированный ключ идемпотентности `EventID` (UUID или хэш бизнес-полей).\n2. Дедупликатор хранит множество недавно увиденных ID за скользящий интервал (Deduplication Window, например, 10 минут).\n3. Если `ID` уже есть в фильтре — событие отбрасывается как дубликат.\n4. Старые ID автоматически удаляются по истечении TTL, предотвращая переполнение памяти.",
        "step_by_step": "1. Спроектируйте структуру `SlidingDeduplicator` с временным индексом `seenIDs map[string]time.Time`.\n2. Реализуйте метод `IsDuplicate(eventID string, eventTime time.Time) bool`.\n3. Реализуйте очистку устаревших ключей (Eviction) старше заданного TTL.\n4. Продемонстрируйте фильтрацию дубликатов на тестовой последовательности.",
        "code_blocks": [
            {
                "filename": "dedup.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
	"time"
)

type EventRecord struct {
	EventID   string
	Payload   string
	Timestamp time.Time
}

// SlidingDeduplicator фильтрует дубликаты в скользящем окне времени.
type SlidingDeduplicator struct {
	mu      sync.Mutex
	ttl     time.Duration
	seenIDs map[string]time.Time
}

func NewSlidingDeduplicator(ttl time.Duration) *SlidingDeduplicator {
	return &SlidingDeduplicator{
		ttl:     ttl,
		seenIDs: make(map[string]time.Time),
	}
}

// IsDuplicate проверяет уникальность события и запоминает его.
func (d *SlidingDeduplicator) IsDuplicate(eventID string, now time.Time) bool {
	d.mu.Lock()
	defer d.mu.Unlock()

	// 1. Проверяем наличие
	if seenTime, exists := d.seenIDs[eventID]; exists {
		// Если ключ еще не протух по TTL
		if now.Sub(seenTime) <= d.ttl {
			return true // Это дубликат!
		}
	}

	// 2. Запоминаем новое событие
	d.seenIDs[eventID] = now
	return false
}

// Cleanup удаляет устаревшие ID из памяти для предотвращения утечек.
func (d *SlidingDeduplicator) Cleanup(now time.Time) int {
	d.mu.Lock()
	defer d.mu.Unlock()

	evicted := 0
	for id, seenTime := range d.seenIDs {
		if now.Sub(seenTime) > d.ttl {
			delete(d.seenIDs, id)
			evicted++
		}
	}
	return evicted
}

func main() {
	dedup := NewSlidingDeduplicator(5 * time.Minute)
	t0 := time.Now()

	events := []EventRecord{
		{EventID: "evt_101", Payload: "Pay 500", Timestamp: t0},
		{EventID: "evt_102", Payload: "Pay 1200", Timestamp: t0.Add(1 * time.Second)},
		{EventID: "evt_101", Payload: "Pay 500", Timestamp: t0.Add(2 * time.Second)}, // Дубликат evt_101!
		{EventID: "evt_103", Payload: "Pay 300", Timestamp: t0.Add(3 * time.Second)},
	}

	fmt.Println("=== Потоковая дедупликация событий ===")
	for _, e := range events {
		if dedup.IsDuplicate(e.EventID, e.Timestamp) {
			fmt.Printf(" ⚠️ [DUPLICATE DROPPED] Событие %s отброшено как дубликат!\n", e.EventID)
		} else {
			fmt.Printf(" ✅ [ACCEPTED] Событие %s принято к обработке: '%s'\n", e.EventID, e.Payload)
		}
	}

	// Симуляция очистки через 10 минут
	evicted := dedup.Cleanup(t0.Add(10 * time.Minute))
	fmt.Printf("\n🧹 Очистка TTL: удалено %d устаревших идентификаторов из памяти.\n", evicted)
}
"""
            }
        ],
        "under_the_hood": "При ультра-высоких нагрузках (миллионы уникальных ID в секунду) хранение строк в `map[string]time.Time` потребляет слишком много памяти. В таких системах применяют **Counting Bloom Filter** или **Cuckoo Filter** со скользящей ротацией поколений: два фильтра Блума работают параллельно (текущее и предыдущее окно). Каждые $N$ минут старый фильтр очищается, а новый становится текущим, обеспечивая $O(1)$ память и ноль аллокаций.",
        "pitfalls": "Если дубликат придет позже размера окна TTL (например, через 24 часа), дедупликатор не сможет его распознать и пропустит повторно. Дедупликация в окне защищает от сетевых ретраев и кратковременных сбоев, но для многодневной дедупликации требуется персистентное хранилище (БД с UNIQUE constraint).",
        "interview_qa": "В: Как реализовать дедупликацию событий без сохранения идентификаторов в памяти воркера?\nО: Если брокер поддерживает идемпотентное продюсирование (Kafka Idempotent Producer), брокер сам дедуплицирует сообщения по паре `(ProducerID, SequenceNumber)` на уровне партиции. В этом случае воркер гарантированно получает поток без дубликатов (Exactly-Once delivery per partition)."
    },
    {
        "num": 14,
        "title": "Обработка запаздывающих событий (Late Arriving Data) и Side Outputs",
        "task": "Что делать, если мобильное устройство вышло из зоны отсутствия сети и прислало событие с задержкой в 2 часа, когда соответствующее окно уже закрыто? Реализуйте обработку с порогом допустимого опоздания (Allowed Lateness): незначительно опоздавшие события обновляют результат окна, а безнадежно устаревшие события направляются в резервный поток (Dead Letter Stream / Side Output) для аудита.",
        "theory": "В идеальном мире все события приходят вовремя. В реальности мобильные устройства, корабельные датчики или оффлайн-кассы могут присылать данные с задержками в часы и дни.\n\nВ теории потоковой обработки (Google Dataflow Model) жизненный цикл окна делится на три фазы:\n1. **On-Time Emission**: окно закрывается по наступлению водяного знака ($Watermark \ge WindowEnd$) и выдает первичный результат.\n2. **Allowed Lateness (Допустимое опоздание)**: окно не уничтожается из памяти еще некоторое время (например, 15 минут). Если в этот период приходит опоздавшее событие, окно пересчитывает результат и выдает корректирующую поправку (Retraction / Update).\n3. **Dropping / Side Output**: если событие пришло после `WindowEnd + AllowedLateness`, окно уже стерто из памяти. Такое событие нельзя молча выбросить — оно направляется в резервный поток **Side Output (Dead Letter Stream)** для ручного аудита или пакетного пересчета.",
        "step_by_step": "1. Спроектируйте `WindowLifecycleManager` с параметрами `WindowSize` и `AllowedLateness`.\n2. Реализуйте классификацию входящих событий: On-Time, Late Update, Dropped to Side Output.\n3. Направьте безнадежно опоздавшие события в специальный канал `sideOutputChan`.\n4. Продемонстрируйте обработку всех трех категорий событий.",
        "code_blocks": [
            {
                "filename": "late_data.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"time"
)

type TelemetryEvent struct {
	DeviceID  string
	Metric    float64
	Timestamp time.Time
}

type WindowState struct {
	End             time.Time
	Sum             float64
	IsClosed        bool
	AllowedLateness time.Duration
}

// WindowLifecycleManager управляет жизненным циклом и опоздавшими данными.
type WindowLifecycleManager struct {
	windowEnd       time.Time
	allowedLateness time.Duration
	sum             float64
	closed          bool
	purged          bool
}

func (m *WindowLifecycleManager) ProcessEvent(e TelemetryEvent, currentWatermark time.Time, sideOutput chan<- TelemetryEvent) {
	// 1. Окно уже физически удалено из памяти (безнадежное опоздание)
	if m.purged || currentWatermark.After(m.windowEnd.Add(m.allowedLateness)) {
		fmt.Printf(" 🚨 [SIDE OUTPUT] Событие %s безнадежно опоздало! Отправлено в Side Output топик.\n", e.DeviceID)
		sideOutput <- e
		m.purged = true
		return
	}

	// 2. Опоздавшее событие в пределах Allowed Lateness (Корректировка!)
	if m.closed {
		m.sum += e.Metric
		fmt.Printf(" ⚠️ [LATE CORRECTION] Опоздавшее событие %s принято! Обновленная сумма окна: %.1f\n",
			e.DeviceID, m.sum)
		return
	}

	// 3. Штатное событие до закрытия окна
	m.sum += e.Metric
	fmt.Printf(" ✅ [ON-TIME] Событие %s принято штатно. Текущая сумма: %.1f\n", e.DeviceID, m.sum)

	// Проверяем, не наступил ли водяной знак закрытия окна
	if !currentWatermark.Before(m.windowEnd) {
		m.closed = true
		fmt.Printf(" 🔔 [EMIT ON-TIME] Окно закрыто водяным знаком! Финальная сумма: %.1f\n", m.sum)
	}
}

func main() {
	t0 := time.Date(2026, 9, 8, 12, 0, 0, 0, time.UTC)
	windowEnd := t0.Add(1 * time.Minute)        // Окно: [12:00, 12:01)
	lateness := 30 * time.Second                // Допустимое опоздание: 30 сек (до 12:01:30)

	mgr := &WindowLifecycleManager{
		windowEnd:       windowEnd,
		allowedLateness: lateness,
	}

	sideOutputChan := make(chan TelemetryEvent, 10)

	// 1. Событие вовремя
	mgr.ProcessEvent(TelemetryEvent{DeviceID: "sensor_1", Metric: 10.0, Timestamp: t0.Add(20 * time.Second)},
		t0.Add(25*time.Second), sideOutputChan)

	// 2. Водяной знак продвинулся до 12:01:05 -> Окно закрывается On-Time!
	mgr.ProcessEvent(TelemetryEvent{DeviceID: "sensor_2", Metric: 20.0, Timestamp: t0.Add(40 * time.Second)},
		t0.Add(65*time.Second), sideOutputChan)

	// 3. Опоздавшее событие (EventTime 12:00:50), но Watermark 12:01:15 < 12:01:30 -> Корректировка!
	mgr.ProcessEvent(TelemetryEvent{DeviceID: "sensor_3", Metric: 5.0, Timestamp: t0.Add(50 * time.Second)},
		t0.Add(75*time.Second), sideOutputChan)

	// 4. Безнадежно опоздавшее событие: Watermark 12:02:00 > 12:01:30 -> Side Output!
	mgr.ProcessEvent(TelemetryEvent{DeviceID: "sensor_4", Metric: 15.0, Timestamp: t0.Add(10 * time.Second)},
		t0.Add(120*time.Second), sideOutputChan)

	close(sideOutputChan)
	fmt.Printf("\nВсего событий в Side Output (Dead Letter): %d\n", len(sideOutputChan))
}
"""
            }
        ],
        "under_the_hood": "Механизм Side Outputs во Flink и Dataflow опирается на типизированные теги вывода (`OutputTag[T]`). Когда оператор встречает запись, не укладывающуюся в правила основного потока, он мультиплексирует ее в альтернативный буфер без прерывания конвейера. В Kafka это транслируется в запись в отдельный топик `telemetry-late-events-dlq`.",
        "pitfalls": "Каждое обновление окна в фазе `Allowed Lateness` генерирует новое сообщение в downstream-хранилище (Retraction / Upsert). Если последующая система не поддерживает идемпотентные апдейты (например, только INSERT), это приведет к дублированию строк в аналитических таблицах.",
        "interview_qa": "В: Что такое Retraction Stream при обработке опоздавших данных?\nО: Это модель потока, в которой система генерирует два сообщения: сообщение отмены предыдущего значения (Retract message: `- старая сумма`) и сообщение с новым скорректированным значением (Accumulate message: `+ новая сумма`). Это позволяет реляционным СУБД корректно пересчитывать материализованные представления."
    },
    {
        "num": 15,
        "title": "Семантика Exactly-Once Processing (EoS)",
        "task": "Разберите различия между семантиками доставки: At-Most-Once, At-Least-Once и Exactly-Once. Покажите, как комбинация идемпотентного продюсера, транзакционной фиксации оффсетов Kafka и двухфазного коммита (Two-Phase Commit / 2PC) в State Store обеспечивает гарантию Exactly-Once в распределенном конвейере на Go.",
        "theory": "Гарантии доставки и обработки в распределенных системах:\n\n1. **At-Most-Once (Не более одного раза)**:\n   - Сообщения могут теряться, но никогда не дублируются.\n   - Оффсет коммитится ДО обработки.\n   - При падении воркера необработанное сообщение теряется.\n\n2. **At-Least-Once (Как минимум один раз)**:\n   - Сообщения никогда не теряются, но могут дублироваться.\n   - Оффсет коммитится ПОСЛЕ обработки.\n   - Если воркер упал после записи в БД, но до коммита оффсета в Kafka, после перезапуска сообщение обработается второй раз!\n\n3. **Exactly-Once Semantics (EoS / Ровно один раз)**:\n   - Каждое входящее событие влияет на конечное состояние системы и исходящие топики **ровно один раз**, как если бы сбоев в природе не существовало.\n   - Достигается через **Atomic Transactional Processing**: считывание оффсета, обновление внутреннего состояния State Store и отправка исходящего сообщения объединяются в единую атомарную распределенную транзакцию (Two-Phase Commit).",
        "step_by_step": "1. Спроектируйте симулятор транзакционного координатора (2PC Coordinator).\n2. Реализуйте двухфазный протокол: `Prepare` (блокировка и валидация) и `Commit`.\n3. Смоделируйте сбой перед фазой коммита и покажите откат (Abort/Rollback).\n4. Продемонстрируйте гарантию Exactly-Once при повторном запуске.",
        "code_blocks": [
            {
                "filename": "eos_2pc.go",
                "lang": "go",
                "code": r"""package main

import (
	"errors"
	"fmt"
)

// TransactionalSink имитирует внешнее хранилище с поддержкой двухфазного коммита (2PC).
type TransactionalSink struct {
	committedState map[string]int
	pendingState   map[string]int
	txActive       bool
}

func NewTransactionalSink() *TransactionalSink {
	return &TransactionalSink{
		committedState: make(map[string]int),
		pendingState:   make(map[string]int),
	}
}

func (s *TransactionalSink) BeginTransaction() {
	s.pendingState = make(map[string]int)
	for k, v := range s.committedState {
		s.pendingState[k] = v
	}
	s.txActive = true
}

func (s *TransactionalSink) WritePending(key string, delta int) {
	if s.txActive {
		s.pendingState[key] += delta
	}
}

// Prepare — Фаза 1 протокола 2PC: проверка готовности фиксации.
func (s *TransactionalSink) Prepare() error {
	if !s.txActive {
		return errors.New("нет активной транзакции")
	}
	// Проверка целостности и запись в WAL
	return nil
}

// Commit — Фаза 2 протокола 2PC: атомарное применение изменений.
func (s *TransactionalSink) Commit() {
	s.committedState = s.pendingState
	s.txActive = false
}

// Abort — откат изменений при сбое.
func (s *TransactionalSink) Abort() {
	s.pendingState = nil
	s.txActive = false
}

func main() {
	sink := NewTransactionalSink()

	fmt.Println("=== Сценарий 1: Успешная транзакция Exactly-Once ===")
	sink.BeginTransaction()
	sink.WritePending("account_alice", 100)
	sink.WritePending("account_bob", 200)

	if err := sink.Prepare(); err == nil {
		sink.Commit()
		fmt.Printf("Транзакция закоммичена! Баланс Alice: %d, Bob: %d\n",
			sink.committedState["account_alice"], sink.committedState["account_bob"])
	}

	fmt.Println("\n=== Сценарий 2: Авария воркера перед коммитом (Откат 2PC) ===")
	sink.BeginTransaction()
	sink.WritePending("account_alice", 500) // Попытка списания

	// Симуляция сбоя сети или паники горутины
	crash := true
	if crash {
		fmt.Println("💥 [CRASH] Авария сервера перед коммитом оффсета Kafka! Вызов Abort()...")
		sink.Abort()
	}

	fmt.Printf("Состояние после отката: Баланс Alice остался прежним: %d (Никаких дублей!)\n",
		sink.committedState["account_alice"])
}
"""
            }
        ],
        "under_the_hood": "В Kafka Streams и Apache Flink семантика Exactly-Once строится на базе транзакций Kafka (Transaction Coordinator). Когда воркер берет батч из входного топика, он открывает транзакцию `producer.BeginTx()`. Внутри одной транзакции продюсер отправляет результирующие сообщения в выходной топик И записывает оффсеты прочитанных сообщений в системный топик `__consumer_offsets`. Вызов `producer.CommitTx()` атомарно коммитит оба действия. Если воркер падает, транзакция сбрасывается брокером по таймауту, исключая дубликаты.",
        "pitfalls": "Семантика Exactly-Once работает ТОЛЬКО внутри экосистемы, поддерживающей распределенные транзакции (Kafka-to-Kafka или Flink-to-Pebble). Если ваш потоковый процессор отправляет HTTP вебхуки в сторонний шлюз или шлет email, гарантировать EoS невозможно — там действует At-Least-Once, и получатель обязан реализовывать собственную идемпотентность по ключам.",
        "interview_qa": "В: Возможно ли физически гарантировать Exactly-Once при передаче пакетов по ненадежной сети (задача двух генералов)?\nО: На физическом сетевом уровне доставить пакет 'ровно один раз' математически невозможно (пакет либо потеряется, либо будет отправлен повторно). Термин **Exactly-Once Semantics** в распределенных системах означает не магию физической сети, а **Exactly-Once Processing**: комбинацию повторной доставки (At-Least-Once) с дедупликацией на стороне State Store или двухфазным коммитом (2PC), гарантирующую, что итоговый сайд-эффект эквивалентен однократному исполнению."
    }
]
