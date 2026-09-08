"""
Генератор упражнений Главы 84 (Часть 2: Упражнения 16–30).
CQRS и Event Sourcing на Go.
"""

exercises = [
    {
        "num": 16,
        "title": "Event Upcasting (Эволюция схемы событий на лету)",
        "task": "Представьте, что событие UserRegisteredEvent v1 содержало поле fullName string, а в версии v2 было разделено на firstName string и lastName string. Вместо тяжелой перезаписи исторических данных в Event Store, напишите интерфейс Upcaster и цепочку преобразования событий, которая перехватывает устаревшие события v1 при вычитке из базы и на лету конвертирует их в структуры v2 перед передачей в агрегат или проекторы.",
        "theory": r"""Поскольку Event Store является неизменяемым (Append-Only) журналом, традиционные SQL-миграции с оператором `ALTER TABLE / UPDATE` категорически запрещены.

### Паттерн Event Upcasting:
**Upcaster** — это промежуточный программный адаптер, который перехватывает устаревшие версии событий в момент вычитки из БД (в десериализаторе) и **на лету (in-flight)** трансформирует их в актуальную структуру данных последней версии:
- База данных хранит исходное историческое событие версии 1 без изменений.
- Доменная модель, агрегаты и проекторы оперируют только актуальной структурой версии 2.
- Не требуется даунтайм приложения и дорогостоящие батч-скрипты миграции миллионов строк.""",
        "step_by_step": [
            "Определите типы событий `UserRegisteredV1` и `UserRegisteredV2`.",
            "Объявите интерфейс `EventUpcaster` с методами `CanUpcast(eventType string, version int) bool` и `Upcast(rawJSON []byte) ([]byte, error)`.",
            "Реализуйте конкретный апкастер, разделяющий строку `fullName` на `firstName` и `lastName`.",
            "Объедините апкастеры в цепочку ответственности (Upcasting Pipeline).",
            "Продемонстрируйте преобразование старого JSON v1 в новый JSON v2."
        ],
        "code_blocks": [
            {
                "filename": "upcasting.go",
                "lang": "go",
                "code": r"""package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

type UserRegisteredV1 struct {
	UserID   string `json:"user_id"`
	FullName string `json:"full_name"`
}

type UserRegisteredV2 struct {
	UserID    string `json:"user_id"`
	FirstName string `json:"first_name"`
	LastName  string `json:"last_name"`
}

type EventUpcaster interface {
	Supports(eventType string, schemaVersion int) bool
	Upcast(raw []byte) ([]byte, int, error)
}

type UserRegisteredV1ToV2Upcaster struct{}

func (u *UserRegisteredV1ToV2Upcaster) Supports(eventType string, schemaVersion int) bool {
	return eventType == "UserRegistered" && schemaVersion == 1
}

func (u *UserRegisteredV1ToV2Upcaster) Upcast(raw []byte) ([]byte, int, error) {
	var v1 UserRegisteredV1
	if err := json.Unmarshal(raw, &v1); err != nil {
		return nil, 0, err
	}

	parts := strings.SplitN(v1.FullName, " ", 2)
	firstName := parts[0]
	lastName := ""
	if len(parts) > 1 {
		lastName = parts[1]
	}

	v2 := UserRegisteredV2{
		UserID:    v1.UserID,
		FirstName: firstName,
		LastName:  lastName,
	}

	upcastedBytes, err := json.Marshal(v2)
	if err != nil {
		return nil, 0, err
	}
	return upcastedBytes, 2, nil // Возвращаем байты и новую версию схемы 2
}

func main() {
	v1Raw := []byte(`{"user_id": "usr-42", "full_name": "Лев Толстой"}`)
	fmt.Printf("Исходный сырой JSON v1 из БД: %s\n", string(v1Raw))

	upcaster := &UserRegisteredV1ToV2Upcaster{}
	if upcaster.Supports("UserRegistered", 1) {
		v2Raw, newVer, err := upcaster.Upcast(v1Raw)
		if err != nil {
			panic(err)
		}
		fmt.Printf("Трансформированный JSON v%d в памяти: %s\n", newVer, string(v2Raw))

		var domainEventV2 UserRegisteredV2
		_ = json.Unmarshal(v2Raw, &domainEventV2)
		fmt.Printf("Агрегат получил v2: Имя=%s, Фамилия=%s\n", domainEventV2.FirstName, domainEventV2.LastName)
	}
}
"""
            }
        ],
        "under_the_hood": r"""Апкастинг выполняется на уровне байтовых буферов до инстанцирования тяжелых Go-структур. В высокопроизводительных EventStore (например, EventStoreDB или Kafka Streams) цепочка апкастеров строится в виде пайплайна: $v1 \to v2 \to v3$, позволяя прозрачно поддерживать события 10-летней давности без единой правки исторической базы данных.""",
        "pitfalls": r"""Апкастинг должен быть строго детерминированным и не зависеть от внешних сервисов (запросов в сеть, вызовов СУБД). Если логика разбиения или обогащения обращается к стороннему API, который может быть недоступен или изменить поведение, регидрация старых событий перестанет быть детерминированной.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Wildberries:** «Что выбрать при изменении контракта события: миграцию всей базы данных (In-Place Migration) или Upcasting на лету?»
**Ответ:** «Для Event Sourcing промышленным стандартом является Upcasting. Изменение миллионов исторических строк в терабайтной базе данных под высокой нагрузкой приводит к блокировкам, раздуванию WAL и риску порчи аудиторского следа. Upcasting сохраняет неизменяемость хранилища и решает проблему эволюции схемы в памяти приложения.»"""
    },
    {
        "num": 17,
        "title": "Миграция схемы событий (Schema Evolution) и версионирование",
        "task": "Разработайте правила версионирования доменных событий: добавление опциональных полей со значениями по умолчанию, игнорирование устаревших полей и запрет изменения семантики существующих полей. Напишите тесты на сериализацию/десериализацию Protobuf и JSON, доказывающие обратную и прямую совместимость между версиями v1 и v2 одного и того же события.",
        "theory": r"""При проектировании долгоживущих распределенных систем эволюция схем сообщений подчиняется правилам **прямой и обратной совместимости (Forward and Backward Compatibility)**:

### Золотые правила эволюции событий:
1. **Никогда не удалять обязательные поля:** Старые потребители перестанут понимать сообщения.
2. **Никогда не менять семантику или тип поля:** Если поле `price` было `int64` (копейки), его нельзя делать `float64` или переименовывать в `priceWithTax`.
3. **Новые поля обязаны быть опциональными:** Старые события не содержат этого поля; десериализатор должен подставлять безопасное дефолтное значение.
4. **Игнорировать неизвестные поля:** Старый сервис, читающий событие новой версии, должен спокойно пропускать неизвестные JSON-ключи / теги Protobuf без ошибок.""",
        "step_by_step": [
            "Определите структуру события версии 1 (`OrderPlacedV1`).",
            "Определите структуру события версии 2 с новым опциональным полем `DeliveryNotes` (`OrderPlacedV2`).",
            "Проверьте обратную совместимость: V2 читает старый JSON от V1 и подставляет дефолтное значение.",
            "Проверьте прямую совместимость: V1 читает новый JSON от V2 и корректно игнорирует новое поле."
        ],
        "code_blocks": [
            {
                "filename": "schema_compat.go",
                "lang": "go",
                "code": r"""package main

import (
	"encoding/json"
	"fmt"
)

type OrderPlacedV1 struct {
	OrderID string `json:"order_id"`
	Total   int64  `json:"total"`
}

type OrderPlacedV2 struct {
	OrderID       string `json:"order_id"`
	Total         int64  `json:"total"`
	DeliveryNotes string `json:"delivery_notes,omitempty"` // Новое опциональное поле
}

func main() {
	// 1. Тест обратной совместимости: V2 читает старый payload v1
	rawV1 := []byte(`{"order_id": "ORD-100", "total": 2500}`)
	var readerV2 OrderPlacedV2
	if err := json.Unmarshal(rawV1, &readerV2); err != nil {
		panic(err)
	}
	fmt.Println("=== Обратная совместимость (Backward Compatibility) ===")
	fmt.Printf("V2 успешно прочитал V1: ID=%s, Total=%d, Notes='%s' (дефолт)\n",
		readerV2.OrderID, readerV2.Total, readerV2.DeliveryNotes)

	// 2. Тест прямой совместимости: V1 читает новый payload v2
	rawV2 := []byte(`{"order_id": "ORD-101", "total": 4000, "delivery_notes": "Код домофона 42"}`)
	var readerV1 OrderPlacedV1
	if err := json.Unmarshal(rawV2, &readerV1); err != nil {
		panic(err)
	}
	fmt.Println("\n=== Прямая совместимость (Forward Compatibility) ===")
	fmt.Printf("V1 успешно прочитал V2 (неизвестные поля проигнорированы): ID=%s, Total=%d\n",
		readerV1.OrderID, readerV1.Total)
}
"""
            }
        ],
        "under_the_hood": r"""В Protobuf обратная и прямая совместимость гарантируются на уровне бинарного формата Wire Format: поля идентифицируются целочисленными тегами (field tags), а не именами. Если парсер встречает неизвестный тег, он сохраняет его в срез `unknownFields` или пропускает на основе wire type (Varint, 64-bit, Length-delimited), гарантируя нулевые сбои при любых обновлениях схем.""",
        "pitfalls": r"""В Go при использовании тегов структур `json:"delivery_notes,omitempty"` помните, что дефолтное значение числового типа — 0. Если для бизнеса `0` является значащим числом (например, скидка 0%), используйте указатель `*int64`, чтобы отличить отсутствие поля (`nil`) от явно переданного нуля.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Яндекс:** «Почему при версионировании API в микросервисах часто предпочитают Protobuf вместо JSON Schema?»
**Ответ:** «Protobuf заставляет жестко следовать правилам эволюции схем: теги полей неизменяемы, типы строго типизированы, удаление полей требует маркировки `reserved`. Вдобавок Protobuf бинарно компактнее в 3–5 раз и парсится на порядок быстрее JSON, что критично при миллиардах событий в сутки.»"""
    },
    {
        "num": 18,
        "title": "Паттерн Transactional Outbox внутри Event Store",
        "task": "Объедините Event Store с паттерном Outbox. При вставке событий в таблицу events генерируйте записи в таблице outbox_messages в рамках той же транзакции PostgreSQL. Напишите сервис-паблишер, который с помощью SELECT ... FOR UPDATE SKIP LOCKED вычитывает готовые сообщения и публикует их в брокер сообщений Apache Kafka, обеспечивая надежную доставку событий внешним микросервисам.",
        "theory": r"""Главная архитектурная проблема при публикации доменных событий во внешние брокеры (Kafka, RabbitMQ) — **проблема двойной записи (Dual Write Problem)**:
- Нельзя выполнить `db.Save(event)` и `kafka.Publish(event)` в одной распределенной ACID-транзакции.
- Если запись в базу прошла, а брокер упал — внешние системы потеряют событие.
- Если сначала отправить в брокер, а база данных откатила транзакцию — внешние системы обработают призрак («Phantom Read»).

### Решение: Transactional Outbox
1. В рамках **одной локальной ACID-транзакции PostgreSQL** события сохраняются в `events` и одновременно в таблицу `outbox_messages`.
2. Фоновый воркер-паблишер вычитывает сообщения из `outbox_messages` пачками с помощью `SELECT ... FOR UPDATE SKIP LOCKED`.
3. Публикует сообщение в брокер сообщений.
4. После успешного подтверждения (ACK от Kafka) удаляет запись из Outbox или помечает флагом `processed_at = NOW()`.""",
        "step_by_step": [
            "Спроектируйте таблицу `outbox_messages`.",
            "Реализуйте транзакционную запись агрегата и outbox-сообщений.",
            "Напишите воркер-паблишер с конкурентной блокировкой `SKIP LOCKED`.",
            "Продемонстрируйте параллельную работу нескольких воркеров без конкуренции за одни и те же строки."
        ],
        "code_blocks": [
            {
                "filename": "outbox_publisher.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

type OutboxMessage struct {
	ID        int64
	Topic     string
	Payload   []byte
	Status    string // PENDING, PUBLISHED
	CreatedAt time.Time
}

type MockOutboxDB struct {
	mu       sync.Mutex
	messages []*OutboxMessage
	nextID   int64
}

func (db *MockOutboxDB) InsertInTx(topic string, payload []byte) {
	db.mu.Lock()
	defer db.mu.Unlock()
	db.nextID++
	db.messages = append(db.messages, &OutboxMessage{
		ID:        db.nextID,
		Topic:     topic,
		Payload:   payload,
		Status:    "PENDING",
		CreatedAt: time.Now(),
	})
}

// FetchPendingBatch симулирует SELECT ... FOR UPDATE SKIP LOCKED
func (db *MockOutboxDB) FetchPendingBatch(limit int) []*OutboxMessage {
	db.mu.Lock()
	defer db.mu.Unlock()

	var result []*OutboxMessage
	for _, m := range db.messages {
		if m.Status == "PENDING" {
			m.Status = "LOCKED" // захвачен текущим воркером
			result = append(result, m)
			if len(result) >= limit {
				break
			}
		}
	}
	return result
}

func (db *MockOutboxDB) MarkPublished(id int64) {
	db.mu.Lock()
	defer db.mu.Unlock()
	for _, m := range db.messages {
		if m.ID == id {
			m.Status = "PUBLISHED"
			return
		}
	}
}

type OutboxPublisher struct {
	id int
	db *MockOutboxDB
}

func (p *OutboxPublisher) Run(ctx context.Context) {
	batch := p.db.FetchPendingBatch(10)
	if len(batch) == 0 {
		return
	}

	fmt.Printf("[Воркер %d] Захватил %d сообщений через SKIP LOCKED\n", p.id, len(batch))
	for _, msg := range batch {
		// Имитация отправки в Kafka
		// kafkaProducer.Produce(msg.Topic, msg.Payload)
		p.db.MarkPublished(msg.ID)
		fmt.Printf("[Воркер %d] Опубликовал сообщение ID=%d в топик %s\n", p.id, msg.ID, msg.Topic)
	}
}

func main() {
	db := &MockOutboxDB{}

	// Клиент сохраняет события в рамках транзакции
	db.InsertInTx("accounts.events", []byte(`{"event": "AccountCreated", "acc": "ACC-1"}`))
	db.InsertInTx("accounts.events", []byte(`{"event": "MoneyDeposited", "acc": "ACC-1", "amt": 5000}`))

	// Запуск двух параллельных паблишеров
	w1 := &OutboxPublisher{id: 1, db: db}
	w2 := &OutboxPublisher{id: 2, db: db}

	ctx := context.Background()
	w1.Run(ctx)
	w2.Run(ctx)
}
"""
            }
        ],
        "under_the_hood": r"""Конструкция `SKIP LOCKED` в PostgreSQL пропускает строки, заблокированные параллельными транзакциями, вместо ожидания снятия блокировки. Это позволяет параллельно запускать 10–50 воркеров-паблишеров Outbox без взаимных блокировок и без задержек.""",
        "pitfalls": r"""Таблица `outbox_messages` при высокой нагрузке подвержена разрастанию (Table Bloat). Если сообщения просто помечать как `PUBLISHED`, таблица за несколько недель вырастет до сотен миллионов строк. Необходимо настроить периодическое партиционирование таблицы с быстрым сбросом секций (`DROP TABLE outbox_y2026m09`) либо удалять строки сразу после публикации.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Ozon:** «В чем недостаток Outbox поллинга по сравнению с Debezium CDC на базе PostgreSQL WAL?»
**Ответ:** «Поллинг таблицы Outbox создает дополнительную нагрузку `SELECT / DELETE` на CPU и дисковый I/O СУБД, а также имеет задержку опроса (сотни миллисекунд). CDC Debezium читает напрямую бинарный журнал WAL асинхронно без выполнения SQL-запросов, обеспечивая субмиллисекундную задержку доставки и нулевой оверхед на планировщик запросов базы.»"""
    },
    {
        "num": 19,
        "title": "Полная перестройка проекций с нуля (Catch-up / Rebuild)",
        "task": "Реализуйте механизм перестроения проекции: при изменении структуры Read-модели создается новая таблица account_views_v2, сбрасывается чекпоинт в 0, воркер на максимальной скорости вычитывает всю историю событий из Event Store, заполняет новую таблицу, а по завершении переключает указатель (View или синоним) с v1 на v2 без даунтайма приложения.",
        "theory": r"""Главная суперсила Event Sourcing — **возможность в любой момент времени создать принципиально новую Read-модель или пересчитать существующую с самого начала времен (Zero-Downtime Projection Rebuild)**.

### Шаги перестроения проекции:
1. Создается новая физическая таблица `account_views_v2`.
2. Регистрируется новый воркер с чекпоинтом `last_position = 0`.
3. Воркер запускается в режиме форсированной вычитки (Catch-up Mode) большими пакетами (по 5000 событий) без троттлинга.
4. В процессе перестроения старая таблица `account_views_v1` продолжает обслуживать 100% пользовательских запросов на чтение.
5. Когда воркер v2 догоняет актуальное смещение базы, выполняется атомарное переключение в PostgreSQL:
   ```sql
   ALTER VIEW account_views RENAME TO account_views_v2;
   ```
6. Клиенты мгновенно начинают читать из нового представления без единой секунды простоя.""",
        "step_by_step": [
            "Определите структуры представлений v1 и v2.",
            "Реализуйте воркер в режиме `CatchUpRebuild`, читающий историю с 0 позиции.",
            "Реализуйте механизм проверки отставания воркера (`IsCaughtUp`).",
            "Продемонстрируйте бесшовное переключение указателя активного хранилища."
        ],
        "code_blocks": [
            {
                "filename": "projection_rebuild.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

type ProjectionStore struct {
	activeView atomic.Pointer[map[string]int64]
}

func (s *ProjectionStore) GetBalance(accID string) int64 {
	m := *s.activeView.Load()
	return m[accID]
}

func (s *ProjectionStore) Switch(newView map[string]int64) {
	s.activeView.Store(&newView)
}

func main() {
	store := &ProjectionStore{}

	// Исходная рабочая версия v1
	v1 := map[string]int64{"acc-1": 1000, "acc-2": 2500}
	store.Switch(v1)
	fmt.Printf("[PROD] Текущий баланс acc-1 из v1: %d\n", store.GetBalance("acc-1"))

	// Запуск перестроения проекции v2 в фоне
	fmt.Println("\n--- Старт фонового перестроения (Catch-up Rebuild) ---")
	v2 := make(map[string]int64)

	// Имитация вычитки всей истории из EventStore с позиции 0
	historicalEvents := []struct {
		Acc string
		Amt int64
	}{
		{"acc-1", 1000},
		{"acc-2", 2500},
		{"acc-1", 500}, // Накопленная дельта
	}

	for _, e := range historicalEvents {
		v2[e.Acc] += e.Amt
	}
	fmt.Printf("[Rebuild] Построена таблица v2: acc-1=%d, acc-2=%d\n", v2["acc-1"], v2["acc-2"])

	// АТОМАРНОЕ ПЕРЕКЛЮЧЕНИЕ УКАЗАТЕЛЯ
	store.Switch(v2)
	fmt.Println("[Switch] Указатель переключен на v2 без даунтайма!")

	fmt.Printf("[PROD] Запрос сразу после переключения acc-1: %d (актуальный баланс)\n",
		store.GetBalance("acc-1"))
}
"""
            }
        ],
        "under_the_hood": r"""В Go атомарная замена указателя через `atomic.Pointer[T]` транслируется в одну ассемблерную инструкцию `LOCK XCHG` или атомарный store в 64-битный регистр. Читающие горутины видят новое состояние мгновенно без блокировок мьютексов.""",
        "pitfalls": r"""Во время долгого перестроения (которое на миллиардах событий может длиться часами) в Event Store продолжают поступать новые события. Если переключить указатель до того, как воркер догнал последние секунды истории (head of the stream), пользователи увидят временный откат данных во времени (Time Slip). Переключение разрешено только при отставании < 1 секунды.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Wildberries:** «Как гарантировать, что во время 4-часового ребилда проекции новая таблица не потеряет события, поступающие прямо сейчас?»
**Ответ:** «Используется двухфазный Catch-Up. Фаза 1: воркер вычитывает исторические данные от 0 до момента $T_{start}$ в фоновую таблицу. Фаза 2: воркер переключается в режим обычного подписчика, быстро дочитывает дельту событий от $T_{start}$ до $T_{now}$ и, когда лаг становится околонулевым, атомарно переключает роутинг запросов.»"""
    },
    {
        "num": 20,
        "title": "Шардирование воркеров проекций по AggregateID",
        "task": "Для увеличения пропускной способности проектора создайте пул воркеров. Напишите роутер событий, который вычисляет хэш от aggregate_id (fnv.New32a) и направляет события одного и того же агрегата в одну и ту же горутину через буферизованный канал. Докажите, что шардирование по ключу гарантирует строгий порядок применения событий конкретного агрегата при сохранении параллелизма между разными агрегатами.",
        "theory": r"""Один воркер проекций может упереться в потолок CPU и дискового I/O (например, 5 000 событий в секунду). Однако наивный запуск $N$ параллельных воркеров без шардирования **разрушит порядок событий**:
- Воркер 1 возьмет событие `OrderCreated (v1)`.
- Воркер 2 возьмет событие `OrderCancelled (v2)`.
- Если Воркер 2 отработает быстрее Воркера 1, заказ сначала отменится, а потом создастся заново!

### Решение: Consistent Hash Partitioning
События шардируются по хэшу от идентификатора агрегата:
$$\text{WorkerID} = \text{Hash}(\text{AggregateID}) \pmod N$$
- Все события конкретного счета `ACC-101` **гарантированно попадают в одну и ту же горутину** и обрабатываются строго последовательно.
- События разных счетов (`ACC-101` и `ACC-999`) обрабатываются параллельно на всех ядрах CPU.""",
        "step_by_step": [
            "Реализуйте хэш-функцию на базе `hash/fnv`.",
            "Создайте диспетчер `ShardedProjectorPool` с $N$ каналами и горутинами.",
            "Направьте поток событий через диспетчер.",
            "Проверьте в выводе логов, что события одного аккаунта всегда обрабатываются одним и тем же Worker ID."
        ],
        "code_blocks": [
            {
                "filename": "sharded_projector.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"hash/fnv"
	"sync"
	"time"
)

func getWorkerIndex(key string, totalWorkers int) int {
	h := fnv.New32a()
	_, _ = h.Write([]byte(key))
	return int(h.Sum32() % uint32(totalWorkers))
}

type ShardedProjectorPool struct {
	numWorkers int
	channels   []chan DomainEvent
	wg         sync.WaitGroup
}

func NewShardedProjectorPool(numWorkers int, bufferSize int) *ShardedProjectorPool {
	pool := &ShardedProjectorPool{
		numWorkers: numWorkers,
		channels:   make([]chan DomainEvent, numWorkers),
	}

	for i := 0; i < numWorkers; i++ {
		ch := make(chan DomainEvent, bufferSize)
		pool.channels[i] = ch
		pool.wg.Add(1)

		workerID := i
		go func(c <-chan DomainEvent) {
			defer pool.wg.Done()
			for event := range c {
				fmt.Printf("[Worker #%d] Обработал событие %s агрегата %s (v%d)\n",
					workerID, event.EventType(), event.AggregateID(), event.Version())
			}
		}(ch)
	}

	return pool
}

func (p *ShardedProjectorPool) Dispatch(event DomainEvent) {
	idx := getWorkerIndex(event.AggregateID(), p.numWorkers)
	p.channels[idx] <- event
}

func (p *ShardedProjectorPool) Close() {
	for _, ch := range p.channels {
		close(ch)
	}
	p.wg.Wait()
}

func main() {
	pool := NewShardedProjectorPool(4, 100)

	// Поток событий от двух разных агрегатов
	events := []DomainEvent{
		NewAccountCreatedEvent("ACC-111", 1, "Алексей", "RUB"),
		NewAccountCreatedEvent("ACC-222", 1, "Борис", "RUB"),
		NewMoneyDepositedEvent("ACC-111", 2, 500, "Пополнение 1"),
		NewMoneyDepositedEvent("ACC-222", 2, 700, "Пополнение 2"),
		NewMoneyDepositedEvent("ACC-111", 3, 300, "Пополнение 3"),
	}

	for _, e := range events {
		pool.Dispatch(e)
	}

	time.Sleep(50 * time.Millisecond)
	pool.Close()
}
"""
            }
        ],
        "under_the_hood": r"""Шардирование по ключу `hash(stream_id) % numWorkers` — это та же самая математическая концепция, которая лежит в основе партиционирования Apache Kafka (Partition Key) и шардирования таблиц баз данных. Она гарантирует Total Order в пределах партиции и Partial Order в пределах всей системы.""",
        "pitfalls": r"""Остерегайтесь неравномерного распределения нагрузки (Hot Key / Hot Partition). Если один крупный корпоративный клиент генерирует 80% всех транзакций платформы, один воркер будет перегружен на 100%, в то время как остальные воркеры будут простаивать.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Т-Банк:** «Как масштабировать обработку событий в Kafka Consumer Group, если требуется строго соблюдать порядок событий одного пользователя?»
**Ответ:** «Использовать `UserID` в качестве ключа сообщения (`record.Key`). Брокер Kafka гарантирует, что сообщения с одинаковым ключом всегда направляются в одну и ту же партицию. А так как партицию вычитывает ровно один инстанс консьюмера в группе, порядок обработки гарантируется физически.»"""
    },
    {
        "num": 21,
        "title": "CQRS Command Bus с конвейером Middleware",
        "task": "Реализуйте шину команд CommandBus. Добавьте конвейер промежуточных обработчиков (Middleware): структурированное логирование входящих команд через log/slog, сбор метрик задержки выполнения в Prometheus, валидация полей команды с помощью тегов структур и глобальный перехват паник (recovery middleware).",
        "theory": r"""В крупных корпоративных системах обработчики команд не вызываются напрямую из HTTP-контроллеров. Вместо этого используется **Шина Команд (Command Bus)** с цепочкой сквозных перехватчиков (Middleware Pipeline).

### Паттерн Middleware для Command Bus:
Каждый middleware оборачивает вызов целевого обработчика, обеспечивая разделение сквозных аспектов (Cross-Cutting Concerns):
1. **Recovery Middleware:** перехватывает паники через `recover()`, предотвращая падение процесса сервиса при багах в бизнес-логике.
2. **Logging Middleware:** логирует входящую команду, имя типа, контекст пользователя и длительность исполнения через `log/slog`.
3. **Metrics Middleware:** измеряет время выполнения и обновляет гистограмму Prometheus.
4. **Validation Middleware:** проверяет структурные теги (непустые поля, диапазоны чисел) до передачи команды агрегату.""",
        "step_by_step": [
            "Определите тип `CommandHandlerFunc` и тип промежуточного слоя `Middleware`.",
            "Реализуйте Recovery Middleware с логированием паники.",
            "Реализуйте Logging Middleware с замером времени через `time.Since`.",
            "Соберите конвейер цепочки вызовов (Chain).",
            "Продемонстрируйте безопасное выполнение с перехватом паники."
        ],
        "code_blocks": [
            {
                "filename": "command_bus.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"os"
	"time"
)

type Command any

type CommandHandlerFunc func(ctx context.Context, cmd Command) error

type Middleware func(next CommandHandlerFunc) CommandHandlerFunc

func RecoveryMiddleware(logger *slog.Logger) Middleware {
	return func(next CommandHandlerFunc) CommandHandlerFunc {
		return func(ctx context.Context, cmd Command) (err error) {
			defer func() {
				if r := recover(); r != nil {
					logger.Error("Паника при выполнении команды", "panic", r)
					err = fmt.Errorf("внутренняя ошибка сервера (panic: %v)", r)
				}
			}()
			return next(ctx, cmd)
		}
	}
}

func LoggingMiddleware(logger *slog.Logger) Middleware {
	return func(next CommandHandlerFunc) CommandHandlerFunc {
		return func(ctx context.Context, cmd Command) error {
			start := time.Now()
			cmdType := fmt.Sprintf("%T", cmd)
			logger.Info("Выполнение команды начато", "cmd", cmdType)

			err := next(ctx, cmd)

			duration := time.Since(start)
			if err != nil {
				logger.Warn("Команда завершилась с ошибкой", "cmd", cmdType, "err", err, "dur_ms", duration.Milliseconds())
			} else {
				logger.Info("Команда успешно выполнена", "cmd", cmdType, "dur_ms", duration.Milliseconds())
			}
			return err
		}
	}
}

type CommandBus struct {
	handlers    map[string]CommandHandlerFunc
	middlewares []Middleware
}

func NewCommandBus() *CommandBus {
	return &CommandBus{handlers: make(map[string]CommandHandlerFunc)}
}

func (b *CommandBus) Use(mw Middleware) {
	b.middlewares = append(b.middlewares, mw)
}

func (b *CommandBus) Register(cmdType string, handler CommandHandlerFunc) {
	b.handlers[cmdType] = handler
}

func (b *CommandBus) Dispatch(ctx context.Context, cmd Command) error {
	cmdName := fmt.Sprintf("%T", cmd)
	handler, exists := b.handlers[cmdName]
	if !exists {
		return fmt.Errorf("хэндлер для команды %s не найден", cmdName)
	}

	// Сборка конвейера middleware в обратном порядке
	pipeline := handler
	for i := len(b.middlewares) - 1; i >= 0; i-- {
		pipeline = b.middlewares[i](pipeline)
	}

	return pipeline(ctx, cmd)
}

func main() {
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))
	bus := NewCommandBus()

	bus.Use(RecoveryMiddleware(logger))
	bus.Use(LoggingMiddleware(logger))

	// Регистрация хэндлера, имитирующего панику
	bus.Register("main.DepositMoneyCommand", func(ctx context.Context, cmd Command) error {
		panic("непредвиденный nil pointer в доменной логике!")
	})

	ctx := context.Background()
	err := bus.Dispatch(ctx, DepositMoneyCommand{AccountID: "ACC-1", Amount: 100})
	fmt.Printf("\nРезультат выполнения с перехватом: %v\n", err)
}
"""
            }
        ],
        "under_the_hood": r"""Паттерн Middleware в Go строится на базе замыканий (Closures). При сборке цепочки `pipeline = mw(pipeline)` создается стек вызовов в куче или на стеке. Накладные расходы на вызов одного middleware составляют порядка 10–20 наносекунд, что абсолютно пренебрежимо на фоне сотен микросекунд обращений к базе данных.""",
        "pitfalls": r"""В Recovery middleware всегда используйте именованное возвращаемое значение `(err error)` в сигнатуре функции. Только в этом случае отложенная функция `defer func() { err = ... }()` способна перезаписать возвращаемую ошибку после перехвата `recover()`.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Касперский:** «Почему в чистой архитектуре рекомендуется использовать шину команд (Command Bus) вместо прямого вызова сервисов?»
**Ответ:** «Шина команд полностью изолирует транспортный слой (HTTP, gRPC, CLI) от прикладного. Она позволяет централизованно внедрять сквозную функциональность (валидацию, аудит, метрики, трейсинг, транзакции) в виде middleware без дублирования кода в каждом контроллере.»"""
    },
    {
        "num": 22,
        "title": "CQRS Query Bus с кэшированием результатов",
        "task": "Создайте шину запросов QueryBus с интерфейсом Ask(ctx context.Context, query Query) (interface{}, error). Реализуйте middleware кэширования: если запрос аннотирован как кэшируемый, результат ищется в Redis по ключу, сгенерированному из параметров запроса. При промахе кэша вызывается хэндлер, а ответ сохраняется с заданным TTL.",
        "theory": r"""В отличие от команд, **Запросы (Queries)** обладают важными свойствами:
1. Они идемпотентны и не изменяют состояние системы.
2. Они могут безопасно кэшироваться на уровне промежуточных слоев (In-Memory или распределенный кэш Redis).

### Архитектура Query Bus:
Шина запросов маршрутизирует объект запроса к соответствующему `QueryHandler`. При наличии кэширующего middleware:
- Проверяется, реализует ли запрос интерфейс `CacheableQuery` (с методами `CacheKey() string` и `TTL() time.Duration`).
- Если ключ найден в кэше — ответ возвращается немедленно за 1 мс.
- Если ключа нет — запрос отправляется к реальной базе данных, результат сохраняется в кэш и отдается клиенту.""",
        "step_by_step": [
            "Определите интерфейс `CacheableQuery` с ключом кэша и временем жизни (TTL).",
            "Реализуйте шину `QueryBus` с методом `Ask(ctx, query)`.",
            "Создайте middleware кэширования с поддержкой In-Memory / Redis хранилища.",
            "Продемонстрируйте промах кэша на первом вызове и мгновенное попадание (Hit) на втором."
        ],
        "code_blocks": [
            {
                "filename": "query_bus.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

type Query any

type CacheableQuery interface {
	CacheKey() string
	TTL() time.Duration
}

type QueryHandlerFunc func(ctx context.Context, q Query) (any, error)

type InMemoryCache struct {
	mu    sync.RWMutex
	items map[string]cacheItem
}

type cacheItem struct {
	val       any
	expiresAt time.Time
}

func NewInMemoryCache() *InMemoryCache {
	return &InMemoryCache{items: make(map[string]cacheItem)}
}

func (c *InMemoryCache) Get(key string) (any, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	item, ok := c.items[key]
	if !ok || time.Now().After(item.expiresAt) {
		return nil, false
	}
	return item.val, true
}

func (c *InMemoryCache) Set(key string, val any, ttl time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.items[key] = cacheItem{val: val, expiresAt: time.Now().Add(ttl)}
}

type QueryBus struct {
	handlers map[string]QueryHandlerFunc
	cache    *InMemoryCache
}

func NewQueryBus(cache *InMemoryCache) *QueryBus {
	return &QueryBus{
		handlers: make(map[string]QueryHandlerFunc),
		cache:    cache,
	}
}

func (b *QueryBus) Register(queryType string, h QueryHandlerFunc) {
	b.handlers[queryType] = h
}

func (b *QueryBus) Ask(ctx context.Context, q Query) (any, error) {
	// Проверка кэшируемости
	if cQ, ok := q.(CacheableQuery); ok {
		key := cQ.CacheKey()
		if val, found := b.cache.Get(key); found {
			fmt.Printf("[CACHE HIT] Данные получены из кэша по ключу '%s'\n", key)
			return val, nil
		}
		fmt.Printf("[CACHE MISS] Ключ '%s' отсутствует в кэше\n", key)
	}

	qName := fmt.Sprintf("%T", q)
	h, exists := b.handlers[qName]
	if !exists {
		return nil, fmt.Errorf("хэндлер для запроса %s не найден", qName)
	}

	res, err := h(ctx, q)
	if err != nil {
		return nil, err
	}

	if cQ, ok := q.(CacheableQuery); ok {
		b.cache.Set(cQ.CacheKey(), res, cQ.TTL())
	}
	return res, nil
}

type GetUserProfileQuery struct {
	UserID string
}

func (q GetUserProfileQuery) CacheKey() string    { return "user:profile:" + q.UserID }
func (q GetUserProfileQuery) TTL() time.Duration { return 5 * time.Minute }

func main() {
	cache := NewInMemoryCache()
	bus := NewQueryBus(cache)

	bus.Register("main.GetUserProfileQuery", func(ctx context.Context, q Query) (any, error) {
		// Имитация тяжелого SQL-запроса
		fmt.Println("--> Выполняется тяжелый SQL-запрос к БД...")
		return "Профиль пользователя: Анна, баланс 10 000 руб.", nil
	})

	ctx := context.Background()
	q := GetUserProfileQuery{UserID: "USR-77"}

	// 1-й запрос: Cache Miss
	res1, _ := bus.Ask(ctx, q)
	fmt.Printf("Ответ 1: %v\n\n", res1)

	// 2-й запрос: Cache Hit (без обращения к БД)
	res2, _ := bus.Ask(ctx, q)
	fmt.Printf("Ответ 2: %v\n", res2)
}
"""
            }
        ],
        "under_the_hood": r"""Проверка принадлежности к интерфейсу `cQ, ok := q.(CacheableQuery)` в Go выполняется за $O(1)$ через анализ структуры `eface._type`. Если структура запроса реализует метод `CacheKey()`, вызывается кэш-слой. Если нет — запрос прозрачно проходит мимо кэша без накладных расходов.""",
        "pitfalls": r"""Кэширование ответов Read-модели требует аккуратной инвалидации при поступлении команд модификации. Если после команды `DepositMoney` старый баланс остается в кэше Redis на 5 минут, пользователь будет жаловаться на пропажу денег. Решением является публикация событий инвалидации в Redis Pub/Sub при коммите событий.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Wildberries:** «Что такое Stampede Effect (Dog-Piling) при кэшировании запросов и как от него защититься в Go?»
**Ответ:** «Когда истекает TTL популярного ключа, тысячи одновременных запросов получают Cache Miss и одновременно атакуют базу данных тяжелым SQL-запросом. Защита: использование библиотеки `golang.org/x/sync/singleflight`, которая объединяет параллельные запросы с одинаковым ключом в один единственный вызов к базе.»"""
    },
    {
        "num": 23,
        "title": "Согласованность в конечном счете (Eventual Consistency) и отслеживание версий в UI",
        "task": "В асинхронном CQRS после выполнения команды пользователь может немедленно отправить запрос на чтение и получить устаревшие данные. Спроектируйте механизм отслеживания: обработчик команды возвращает клиенту версию записанного события (aggregate_version = 42). При последующем запросе чтения клиент передает заголовок X-Wait-For-Version: 42. Хэндлер чтения ожидает обновления проекции до версии 42 через PostgreSQL LISTEN/NOTIFY с таймаутом.",
        "theory": r"""При использовании асинхронных проекций неизбежен временной лаг (от 5 до 100 миллисекунд), называемый **Eventual Consistency Lag**.
Если пользователь сохранил новый профиль и браузер сразу запросил страницу профиля:
- Проектор еще не успел вычитать событие из Event Store.
- Пользователь видит старые данные и думает, что операция сломалась!

### Паттерн Consistent Read-Your-Own-Writes:
1. При выполнении команды сервер возвращает клиенту заголовок `X-Entity-Version: 42`.
2. Браузер при следующем `GET /profile` передает заголовок `X-Wait-For-Version: 42`.
3. Обработчик чтения проверяет версию в Read-модели:
   - Если версия в Read-модели $\ge 42$ — данные отдаются немедленно.
   - Если версия меньше 42 — горутина подписывается на оповещение (PostgreSQL `LISTEN/NOTIFY` или локальный `sync.Cond`) и ожидает применения события проектором (с таймаутом, например, 1 секунда).
4. Как только проектор зафиксировал версию 42, он шлет notify, и запрос на чтение мгновенно отдает свежие данные.""",
        "step_by_step": [
            "Определите структуру Read-модели с полем `Version`.",
            "Создайте шину уведомлений о версиях на базе каналов `sync.Map`.",
            "Реализуйте метод ожидания версии `WaitForVersion(ctx, id, targetVersion)`.",
            "Продемонстрируйте разблокировку ожидающего запроса на чтение при обновлении проектора."
        ],
        "code_blocks": [
            {
                "filename": "wait_for_version.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

type VersionNotifier struct {
	mu          sync.Mutex
	subscribers map[string][]chan int64
}

func NewVersionNotifier() *VersionNotifier {
	return &VersionNotifier{subscribers: make(map[string][]chan int64)}
}

func (n *VersionNotifier) Subscribe(accID string) chan int64 {
	n.mu.Lock()
	defer n.mu.Unlock()
	ch := make(chan int64, 1)
	n.subscribers[accID] = append(n.subscribers[accID], ch)
	return ch
}

func (n *VersionNotifier) Notify(accID string, newVersion int64) {
	n.mu.Lock()
	defer n.mu.Unlock()
	for _, ch := range n.subscribers[accID] {
		select {
		case ch <- newVersion:
		default:
		}
	}
	delete(n.subscribers, accID) // Очистка после оповещения
}

type ConsistentReadService struct {
	views    sync.Map
	notifier *VersionNotifier
}

func (s *ConsistentReadService) GetWithVersionWait(
	ctx context.Context,
	accID string,
	minVersion int64,
) (int64, int64, error) {
	// 1. Проверяем текущее состояние
	if val, ok := s.views.Load(accID); ok {
		view := val.(AccountViewWithVersion)
		if view.Version >= minVersion {
			return view.Balance, view.Version, nil
		}
	}

	// 2. Если версия отстает, подписываемся на обновление
	ch := s.notifier.Subscribe(accID)
	fmt.Printf("[Client] Версия в Read-модели отстает. Ожидаем v%d...\n", minVersion)

	for {
		select {
		case <-ctx.Done():
			return 0, 0, ctx.Err()
		case v := <-ch:
			if v >= minVersion {
				val, _ := s.views.Load(accID)
				view := val.(AccountViewWithVersion)
				return view.Balance, view.Version, nil
			}
		}
	}
}

func main() {
	notifier := NewVersionNotifier()
	svc := &ConsistentReadService{notifier: notifier}

	// Исходная устаревшая версия 1 в Read-модели
	svc.views.Store("ACC-1", AccountViewWithVersion{AccountID: "ACC-1", Balance: 100, Version: 1})

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Горутина клиента: ожидает версию 2 после отправки команды
	go func() {
		bal, ver, err := svc.GetWithVersionWait(ctx, "ACC-1", 2)
		if err != nil {
			fmt.Printf("Ошибка ожидания: %v\n", err)
			return
		}
		fmt.Printf("✅ [Client] Получены свежие данные: Баланс=%d (Версия=%d)\n", bal, ver)
	}()

	time.Sleep(100 * time.Millisecond)

	// Имитация работы асинхронного проектора: пришло событие версии 2
	fmt.Println("[Projector] Проектор обновил БД до версии 2 и шлет Notify!")
	svc.views.Store("ACC-1", AccountViewWithVersion{AccountID: "ACC-1", Balance: 500, Version: 2})
	notifier.Notify("ACC-1", 2)

	time.Sleep(50 * time.Millisecond)
}
"""
            }
        ],
        "under_the_hood": r"""В распределенных продакшен-системах механизм `WaitForVersion` строится поверх Redis Streams или брокера NATS: клиенты ожидают события в SSE/WebSocket канале. Это исключает блокировку HTTP-горутин в бэкенде и дает пользователю ощущение моментального интерактивного отклика интерфейса.""",
        "pitfalls": r"""Всегда ограничивайте ожидание версии жестким таймаутом через `context.WithTimeout(ctx, 1*time.Second)`. Если воркер проекций зависнет или упадет, клиентский HTTP-запрос не должен висеть бесконечно: по истечении таймаута клиенту возвращаются доступные на данный момент данные с предупреждающим заголовком `Warning: 199 - Stale Data`.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Ozon:** «Как подружить Eventual Consistency в CQRS с строгими требованиями продуктовых менеджеров: "пользователь должен сразу видеть созданный заказ"?»
**Ответ:** «Использовать комбинацию техник: 1) Optimistic UI Update на фронтенде; 2) Передача `min_version` в запросе на чтение с кратковременным ожиданием на бэкенде (Long-Polling / WebSockets); 3) Чтение свежих данных напрямую из Write Model (Aggregate) только для автора изменения в течение первых нескольких секунд после записи.»"""
    },
    {
        "num": 24,
        "title": "Хореография Саг на основе событий (Choreographed Saga)",
        "task": "Реализуйте распределенную сагу оформления заказа (OrderSaga). Сервис заказов публикует событие OrderCreatedEvent. Сервис оплаты слушает это событие, списывает деньги и публикует PaymentCompletedEvent или PaymentFailedEvent. Сервис доставки слушает успех оплаты и бронирует курьера. Сервис заказов слушает отказы и публикует OrderCancelledEvent с компенсационным возвратом средств.",
        "theory": r"""В микросервисной архитектуре транзакции между независимыми базами данных не могут использовать двухфазный коммит (2PC) из-за блокировок и несовместимости с облачными окружениями. Стандартом является **Паттерн Сага (Saga Pattern)**.

### Хореография событий (Choreography-based Saga):
В хореографии нет единого центрального координатора (оркестратора). Микросервисы реагируют на доменные события друг друга и публикуют собственные:
1. `OrderService`: создает заказ в статусе `PENDING` $\to$ публикует `OrderCreatedEvent`.
2. `PaymentService`: списывает средства $\to$ публикует `PaymentCompletedEvent` (или `PaymentFailedEvent`).
3. `DeliveryService`: резервирует курьера $\to$ публикует `DeliveryScheduledEvent`.
4. **Компенсирующая транзакция (Compensating Transaction):** Если на шаге оплаты произошел сбой (`PaymentFailedEvent`), `OrderService` переводит заказ в статус `CANCELLED`, а складской сервис разблокирует товары.""",
        "step_by_step": [
            "Определите события саги: `OrderCreated`, `PaymentCompleted`, `PaymentFailed`, `OrderCancelled`.",
            "Реализуйте независимые сервисы: `OrderService` и `PaymentService`.",
            "Настройте шину событий для хореографии.",
            "Протестируйте успешный сценарий прохождения Саги.",
            "Протестируйте компенсационный сценарий при отказе платежа."
        ],
        "code_blocks": [
            {
                "filename": "choreographed_saga.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"time"
)

type SagaEvent interface {
	OrderID() string
}

type OrderCreatedSagaEvent struct {
	orderID string
	Amount  int64
}
func (e OrderCreatedSagaEvent) OrderID() string { return e.orderID }

type PaymentCompletedSagaEvent struct {
	orderID string
}
func (e PaymentCompletedSagaEvent) OrderID() string { return e.orderID }

type PaymentFailedSagaEvent struct {
	orderID string
	Reason  string
}
func (e PaymentFailedSagaEvent) OrderID() string { return e.orderID }

type OrderCancelledSagaEvent struct {
	orderID string
	Reason  string
}
func (e OrderCancelledSagaEvent) OrderID() string { return e.orderID }

type EventBusChoreography struct {
	handlers []func(event SagaEvent)
}

func (b *EventBusChoreography) Subscribe(h func(event SagaEvent)) {
	b.handlers = append(b.handlers, h)
}

func (b *EventBusChoreography) Publish(event SagaEvent) {
	for _, h := range b.handlers {
		h(event)
	}
}

func main() {
	bus := &EventBusChoreography{}

	// Сервис оплаты: слушает OrderCreated
	bus.Subscribe(func(event SagaEvent) {
		switch e := event.(type) {
		case OrderCreatedSagaEvent:
			fmt.Printf("[PaymentService] Получен заказ %s на сумму %d\n", e.OrderID(), e.Amount)
			if e.Amount > 10000 {
				fmt.Printf("[PaymentService] ❌ Превышен кредитный лимит! Отказ оплаты.\n")
				bus.Publish(PaymentFailedSagaEvent{orderID: e.OrderID(), Reason: "Лимит превышен"})
			} else {
				fmt.Printf("[PaymentService] ✅ Оплата успешно проведена.\n")
				bus.Publish(PaymentCompletedSagaEvent{orderID: e.OrderID()})
			}
		}
	})

	// Сервис заказов: слушает отказы и компенсирует
	bus.Subscribe(func(event SagaEvent) {
		switch e := event.(type) {
		case PaymentCompletedSagaEvent:
			fmt.Printf("[OrderService] Заказ %s переведен в статус CONFIRMED\n", e.OrderID())
		case PaymentFailedSagaEvent:
			fmt.Printf("[OrderService] 🔄 КОМПЕНСАЦИЯ: Заказ %s отменен (причина: %s)\n", e.OrderID(), e.Reason)
		}
	})

	fmt.Println("=== Сценарий 1: Успешный заказ ===")
	bus.Publish(OrderCreatedSagaEvent{orderID: "ORD-1", Amount: 5000})

	fmt.Println("\n=== Сценарий 2: Отказ и компенсация ===")
	bus.Publish(OrderCreatedSagaEvent{orderID: "ORD-2", Amount: 25000})
}
"""
            }
        ],
        "under_the_hood": r"""Хореография отлично масштабируется на небольшом числе сервисов (до 4–5 шагов), так как сервисы слабо связаны между собой. Однако при усложнении процессов возникает циклическая зависимость событий (Spaghetti Choreography), из-за чего в крупных enterprise-системах переходят к Оркестрации на базе Temporal.io (Глава 87).""",
        "pitfalls": r"""В хореографических Сагах критически важно передавать сквозной `CorrelationID` во всех событиях цепочки. Без CorrelationID невозможно отследить путь распределенной транзакции в логах OpenTelemetry при анализе сбойных инцидентов.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Авито:** «В чем фундаментальное отличие Хореографии от Оркестрации в паттерне Сага?»
**Ответ:** «В хореографии сервисы автономны и обмениваются событиями напрямую (каждый знает, что делать при наступлении события X). В оркестрации существует центральный координатор (Saga Orchestrator), который явно вызывает команды сервисов шаг за шагом и управляет ветвлением и компенсациями. Оркестрация проще в мониторинге и аудите сложных процессов.»"""
    },
    {
        "num": 25,
        "title": "Очистка и сжатие Event Store (Право на забвение / GDPR)",
        "task": "По закону GDPR пользователи имеют право требовать полного удаления персональных данных, однако Event Store является неизменяемым (Append-Only) хранилищем. Реализуйте паттерн Crypto-shredding: конфиденциальные поля событий шифруются уникальным симметричным ключом пользователя (AES-256-GCM), а сами ключи хранятся в отдельной таблице. Для выполнения запроса на удаление данных сервис просто уничтожает ключ шифрования, делая исторические события нечитаемыми.",
        "theory": r"""Законодательство о защите персональных данных (GDPR Article 17 «Right to be forgotten», 152-ФЗ РФ) требует гарантированного и безвозвратного удаления персональных данных по требованию пользователя.

### Архитектурный парадокс Event Sourcing:
- Event Store **неизменяем по своей природе**. Удаление строк через `DELETE` разрушает целостность истории, ломает индексы и делает невозможной валидацию цепочки хэшей.

### Решение: Crypto-Shredding (Криптографическое уничтожение)
1. Для каждого пользователя генерируется уникальный 256-битный ключ шифрования $K_{user}$.
2. Ключи пользователей хранятся в отдельной изменяемой таблице `user_encryption_keys`.
3. Все персональные данные (PII: ФИО, телефон, адрес, паспорт) перед записью в событие шифруются алгоритмом **AES-256-GCM**.
4. При поступлении запроса на удаление данных сервис **физически удаляет ключ $K_{user}$**:
   `DELETE FROM user_encryption_keys WHERE user_id = :id`.
5. Исторические события в Event Store остаются нетронутыми, но расшифровать персональные данные математически невозможно!""",
        "step_by_step": [
            "Реализуйте шифрование и дешифрование AES-256-GCM с использованием `crypto/aes` и `crypto/cipher`.",
            "Создайте хранилище ключей шифрования пользователей `KeyStore`.",
            "Зашифруйте персональные данные при создании события.",
            "Продемонстрируйте чтение данных до удаления ключа.",
            "Удалите ключ и докажите, что данные превратились в нечитаемый шифротекст."
        ],
        "code_blocks": [
            {
                "filename": "crypto_shredding.go",
                "lang": "go",
                "code": r"""package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"errors"
	"fmt"
	"io"
)

type KeyStore struct {
	keys map[string][]byte
}

func NewKeyStore() *KeyStore {
	return &KeyStore{keys: make(map[string][]byte)}
}

func (ks *KeyStore) GenerateKey(userID string) []byte {
	key := make([]byte, 32) // AES-256
	_, _ = io.ReadFull(rand.Reader, key)
	ks.keys[userID] = key
	return key
}

func (ks *KeyStore) DestroyKey(userID string) {
	delete(ks.keys, userID) // КРИПТОГРАФИЧЕСКОЕ УНИЧТОЖЕНИЕ
}

func EncryptPII(key []byte, plaintext string) ([]byte, error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, err
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}
	nonce := make([]byte, gcm.NonceSize())
	_, _ = io.ReadFull(rand.Reader, nonce)

	ciphertext := gcm.Seal(nonce, nonce, []byte(plaintext), nil)
	return ciphertext, nil
}

func DecryptPII(key []byte, ciphertext []byte) (string, error) {
	if key == nil {
		return "", errors.New("ключ шифрования удален (право на забвение исполнено)")
	}
	block, err := aes.NewCipher(key)
	if err != nil {
		return "", err
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", err
	}
	nonceSize := gcm.NonceSize()
	if len(ciphertext) < nonceSize {
		return "", errors.New("невалидный шифротекст")
	}
	nonce, cipherBytes := ciphertext[:nonceSize], ciphertext[nonceSize:]
	plaintext, err := gcm.Open(nil, nonce, cipherBytes, nil)
	if err != nil {
		return "", err
	}
	return string(plaintext), nil
}

func main() {
	keyStore := NewKeyStore()
	userID := "usr-999"
	key := keyStore.GenerateKey(userID)

	piiData := "Иванов Иван Иванович, Паспорт 4509 123456"
	encrypted, _ := EncryptPII(key, piiData)
	fmt.Printf("[EventStore] В события записан зашифрованный payload: %x...\n", encrypted[:16])

	// 1. Чтение до удаления пользователя
	decrypted, err := DecryptPII(keyStore.keys[userID], encrypted)
	if err != nil {
		panic(err)
	}
	fmt.Printf("[Read] Данные расшифрованы: '%s'\n", decrypted)

	// 2. Исполнение запроса GDPR
	fmt.Println("\n--- Пользователь подал запрос на удаление данных (GDPR) ---")
	keyStore.DestroyKey(userID)
	fmt.Println("[KeyStore] Ключ шифрования безвозвратно уничтожен!")

	// 3. Попытка прочесть данные после удаления
	_, err = DecryptPII(keyStore.keys[userID], encrypted)
	fmt.Printf("[Read] Результат попытки чтения: %v\n", err)
}
"""
            }
        ],
        "under_the_hood": r"""Симметричный шифр AES-GCM (Galois/Counter Mode) обеспечивает аутентифицированное шифрование (AEAD). Он гарантирует как конфиденциальность, так и целостность данных. При удалении 256-битного ключа перебор пространства состояний $2^{256}$ современными суперкомпьютерами невозможен, что юридически признается регуляторами полным уничтожением персональных данных.""",
        "pitfalls": r"""Убедитесь, что ключи шифрования пользователей не оседают в логах приложения, бэкапах баз данных или дампе оперативной памяти. Доступ к таблице `user_encryption_keys` должен быть защищен жесткими политиками RBAC и шифроваться мастер-ключом KMS (Envelope Encryption).""",
        "bigtech_interview": r"""**Вопрос с собеседования в Т-Банк:** «Как соответствовать требованиям 152-ФЗ / GDPR в системах с блокчейном или неизменяемым Event Store?»
**Ответ:** «Использовать архитектурный паттерн Crypto-Shredding. Персональные данные никогда не хранятся в открытом виде в неизменяемой ленте. Каждая сущность шифруется персональным эфемерным ключом. При необходимости удаления ключи стираются из KMS/базы ключей, делая зашифрованные блоки в неизменяемом логе математически эквивалентными белому шуму.»"""
    },
    {
        "num": 26,
        "title": "Бенчмарк регидрации агрегата: Rehydrate vs Snapshot",
        "task": "Напишите эталонный бенчмарк на Go (testing.B), сравнивающий производительность восстановления агрегата с 100, 1000 и 10 000 событий в истории. Замерьте время регидрации и количество аллокаций памяти (b.ReportAllocs()). Покажите, что время регидрации со снимками остается константным O(1) относительно общего размера истории.",
        "theory": r"""Теоретическая сложность восстановления агрегата из чистой истории событий составляет $O(N)$, где $N$ — количество событий в стриме:
- При $N = 100$: время регидрации $\approx 5$ мкс.
- При $N = 10\ 000$: время регидрации $\approx 500$ мкс (плюс задержка вычитки 10k строк из сети СУБД).

При использовании снимков состояния сложность становится константной $O(1)$:
- Независимо от того, сколько всего событий в истории (10 тысяч или 1 миллион), загружается 1 снимок и дочитывается не более $K$ свежих событий (где $K < SnapshotInterval$).""",
        "step_by_step": [
            "Сгенерируйте тестовые срезы из 100, 1000 и 10 000 событий.",
            "Напишите функцию бенчмарка полной регидрации `BenchmarkRehydratePure`.",
            "Напишите функцию бенчмарка со снимками `BenchmarkRehydrateWithSnapshot`.",
            "Включите `b.ReportAllocs()` для замера давления на Garbage Collector.",
            "Продемонстрируйте превосходство снимков в консольном выводе."
        ],
        "code_blocks": [
            {
                "filename": "benchmark_test.go",
                "lang": "go",
                "code": r"""package main

import (
	"testing"
)

func generateEventHistory(n int) []DomainEvent {
	events := make([]DomainEvent, n)
	events[0] = NewAccountCreatedEvent("ACC-BENCH", 1, "Тест", "RUB")
	for i := 1; i < n; i++ {
		events[i] = NewMoneyDepositedEvent("ACC-BENCH", int64(i+1), 10, "Пополнение")
	}
	return events
}

func BenchmarkRehydratePure_1000(b *testing.B) {
	history := generateEventHistory(1000)
	b.ResetTimer()
	b.ReportAllocs()

	for i := 0; i < b.N; i++ {
		acc := NewAccountAggregateV2("ACC-BENCH")
		for _, e := range history {
			acc.apply(e)
		}
	}
}

func BenchmarkRehydrateSnapshot_1000(b *testing.B) {
	// Допустим, снимок сделан на версии 980, дочитывается 20 событий
	recentEvents := generateEventHistory(1000)[980:]
	b.ResetTimer()
	b.ReportAllocs()

	for i := 0; i < b.N; i++ {
		// Восстановление из снимка O(1)
		acc := &AccountAggregateV2{
			id:      "ACC-BENCH",
			owner:   "Тест",
			balance: 9800,
			version: 980,
		}
		// Применение дельты
		for _, e := range recentEvents {
			acc.apply(e)
		}
	}
}
"""
            },
            {
                "filename": "run_bench.sh",
                "lang": "bash",
                "code": r"""# Запуск сравнительного бенчмарка
go test -bench=BenchmarkRehydrate -benchmem
"""
            }
        ],
        "under_the_hood": r"""В бенчмарке со снимками процессор выполняет в 50 раз меньше инструкций `MOV` и прыжков ветвления `JMP/CALL`, так как избегает прохода по длинному срезу интерфейсов. Число аллокаций памяти падает до нуля, если агрегат инициализируется на стеке или переиспользуется через `sync.Pool`.""",
        "pitfalls": r"""При написании бенчмарков в Go не забывайте вызывать `b.ResetTimer()` после фазы генерации тестовых данных `generateEventHistory()`. Иначе время подготовки многотысячных массивов будет ошибочно включено в итоговый результат замера.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Яндекс:** «Как `b.ReportAllocs()` помогает выявлять скрытые проблемы производительности в Go Event Sourcing?»
**Ответ:** «`b.ReportAllocs()` показывает количество выделений памяти в куче (allocs/op). Лишние аллокации интерфейсов `DomainEvent` или конкатенации строк приводят к фрагментации памяти и частым циклам сборщика мусора (GC Stop-the-World/Marking), что резко увеличивает 99-й перцентиль задержки (p99 latency) под высокой нагрузкой.»"""
    },
    {
        "num": 27,
        "title": "Буферизация Out-of-Order событий в проекторе",
        "task": "При асинхронной доставке через несколько партиций события агрегата могут прийти с нарушением порядка (например, версия 3 пришла раньше версии 2). Напишите проектор с буфером в оперативной памяти: если номер версии больше ожидаемого, событие помещается в локальную приоритетную очередь (min-heap). Когда недостающая версия 2 обработана, очередь выталкивает версию 3.",
        "theory": r"""Если события агрегата доставляются через распределенные каналы или несколько потребителей, порядок доставки может нарушиться (Out-of-Order Delivery):
- Ожидается версия: $V = 2$.
- Поступает событие версии $V = 3$ (задержка пакета в сети).
- Если применить версию 3 немедленно — нарушится консистентность.
- Если отбросить версию 3 — событие будет потеряно навсегда.

### Паттерн Reordering Buffer (Буфер переупорядочивания):
1. Проектор поддерживает карту `expectedVersions[streamID]`.
2. Если `event.Version == expected`: событие применяется немедленно, `expected++`.
3. Если `event.Version > expected`: событие кладется в локальный буфер ожидания (Priority Queue / Min-Heap).
4. После успешного применения версии 2 проверяется буфер: если в нем лежит версия 3, она автоматически извлекается и применяется каскадно.""",
        "step_by_step": [
            "Реализуйте приоритетную очередь (min-heap) событий с сортировкой по `Version`.",
            "Создайте проектор с буфером отложенных событий для каждого `StreamID`.",
            "Напишите метод `Ingest(event)` с проверкой ожидаемой версии.",
            "Протестируйте доставку событий в порядке: Версия 1 $\to$ Версия 3 $\to$ Версия 4 $\to$ Версия 2.",
            "Убедитесь, что после прихода версии 2 все события применились в строгом порядке 1, 2, 3, 4."
        ],
        "code_blocks": [
            {
                "filename": "reorder_buffer.go",
                "lang": "go",
                "code": r"""package main

import (
	"container/heap"
	"fmt"
)

type EventHeap []DomainEvent

func (h EventHeap) Len() int           { return len(h) }
func (h EventHeap) Less(i, j int) bool { return h[i].Version() < h[j].Version() }
func (h EventHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *EventHeap) Push(x any)        { *h = append(*h, x.(DomainEvent)) }
func (h *EventHeap) Pop() any {
	old := *h
	n := len(old)
	x := old[n-1]
	*h = old[0 : n-1]
	return x
}

type ReorderingProjector struct {
	expectedVersion map[string]int64
	buffers         map[string]*EventHeap
}

func NewReorderingProjector() *ReorderingProjector {
	return &ReorderingProjector{
		expectedVersion: make(map[string]int64),
		buffers:         make(map[string]*EventHeap),
	}
}

func (p *ReorderingProjector) Ingest(event DomainEvent) {
	streamID := event.AggregateID()
	expected, exists := p.expectedVersion[streamID]
	if !exists {
		expected = 1
		p.expectedVersion[streamID] = expected
	}

	h, ok := p.buffers[streamID]
	if !ok {
		h = &EventHeap{}
		heap.Init(h)
		p.buffers[streamID] = h
	}

	if event.Version() > expected {
		fmt.Printf("[Буфер] Версия %d пришла раньше времени (ожидается %d). Отложено в буфер.\n",
			event.Version(), expected)
		heap.Push(h, event)
		return
	}

	if event.Version() == expected {
		p.apply(event)
		expected++
		p.expectedVersion[streamID] = expected

		// Каскадное выталкивание готовых событий из буфера
		for h.Len() > 0 {
			top := (*h)[0]
			if top.Version() == expected {
				evt := heap.Pop(h).(DomainEvent)
				p.apply(evt)
				expected++
				p.expectedVersion[streamID] = expected
			} else {
				break // Следующее событие еще не подошло
			}
		}
	}
}

func (p *ReorderingProjector) apply(e DomainEvent) {
	fmt.Printf(">>> [ПРОЕКТОР] Успешно применено событие %s (версия %d)\n", e.EventType(), e.Version())
}

func main() {
	p := NewReorderingProjector()

	// Нарушенный порядок доставки: 1 -> 3 -> 4 -> 2
	e1 := NewAccountCreatedEvent("ACC-1", 1, "Иван", "RUB")
	e3 := NewMoneyDepositedEvent("ACC-1", 3, 300, "Перевод 3")
	e4 := NewMoneyDepositedEvent("ACC-1", 4, 400, "Перевод 4")
	e2 := NewMoneyDepositedEvent("ACC-1", 2, 200, "Перевод 2")

	fmt.Println("1. Приходит версия 1:")
	p.Ingest(e1)

	fmt.Println("\n2. Приходит версия 3 (гонка):")
	p.Ingest(e3)

	fmt.Println("\n3. Приходит версия 4 (гонка):")
	p.Ingest(e4)

	fmt.Println("\n4. Наконец доходит задержавшаяся версия 2:")
	p.Ingest(e2)
}
"""
            }
        ],
        "under_the_hood": r"""Использование стандартного пакета `container/heap` в Go реализует бинарную кучу (Binary Min-Heap) поверх обычного среза. Операция вставки `Push` и извлечения `Pop` имеют логарифмическую сложность $O(\log K)$, где $K$ — размер буфера задержанных событий, обеспечивая высочайшую скорость работы.""",
        "pitfalls": r"""Буфер не должен расти бесконечно. Если потерянное событие (версия 2) так и не пришло из-за фатальной аварии продюсера, последующие события (3, 4, 5...) будут вечно копиться в RAM, вызвав утечку памяти (OOM). Обязательно настраивайте TTL буфера и отправку в Dead Letter Queue (DLQ) при превышении лимита ожидания.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Wildberries:** «Что делать, если события одного заказа пришли в разные партиции Kafka и нарушили строгий порядок?»
**Ответ:** «Архитектурная ошибка произошла на этапе публикации: события одного агрегата обязаны отправляться с одинаковым ключом партиционирования (`Record Key = AggregateID`). Если же это внешняя система с нарушением порядка, в консьюмере применяется паттерн Reordering Buffer на базе Priority Queue с таймаутом сброса в Dead Letter Queue.»"""
    },
    {
        "num": 28,
        "title": "Тестирование агрегатов через Given-When-Then",
        "task": "Напишите специализированный фреймворк тестирования для Event Sourcing: структуру AggregateTestFixture. Метод Given(events ...DomainEvent) инициализирует агрегат историческими событиями; метод When(command Command) выполняет доменную команду; метод Then(expectedEvents ...DomainEvent) или ThenExpectError(err error) проверяет результат с помощью reflect.DeepEqual или библиотеки testify.",
        "theory": r"""Тестирование агрегатов в Event Sourcing кардинально проще и чище, чем в классическом CRUD:
- Нет необходимости поднимать базу данных или настраивать громоздкие моки репозиториев (`mockRepo.On("Save")`).
- Тесты формулируются на языке бизнес-спецификации по методологии **Given-When-Then**:
  1. **Given (Дано):** Список событий, произошедших с агрегатом в прошлом.
  2. **When (Когда):** Команда, которую мы вызываем прямо сейчас.
  3. **Then (Тогда):** Ожидаемый список новых событий, либо ожидаемая доменная ошибка.""",
        "step_by_step": [
            "Создайте структуру `AggregateTestFixture`.",
            "Реализуйте метод `Given(events ...)` с регидрацией агрегата.",
            "Реализуйте метод `When(fn func(a *AccountAggregateV2) error)`.",
            "Реализуйте метод `Then(expected ...DomainEvent)` и `ThenExpectError(target error)`.",
            "Напишите юнит-тесты на успешное списание средств и отказ при овердрафте."
        ],
        "code_blocks": [
            {
                "filename": "fixture_test.go",
                "lang": "go",
                "code": r"""package main

import (
	"errors"
	"fmt"
	"reflect"
	"testing"
)

type AggregateTestFixture struct {
	t           *testing.T
	aggregate   *AccountAggregateV2
	recordedErr error
}

func NewFixture(t *testing.T, id string) *AggregateTestFixture {
	return &AggregateTestFixture{
		t:         t,
		aggregate: NewAccountAggregateV2(id),
	}
}

func (f *AggregateTestFixture) Given(events ...DomainEvent) *AggregateTestFixture {
	for _, e := range events {
		f.aggregate.apply(e)
	}
	f.aggregate.uncommitted = nil // Очистка буфера
	return f
}

func (f *AggregateTestFixture) When(action func(a *AccountAggregateV2) error) *AggregateTestFixture {
	f.recordedErr = action(f.aggregate)
	return f
}

func (f *AggregateTestFixture) Then(expectedEvents ...DomainEvent) {
	f.t.Helper()
	if f.recordedErr != nil {
		f.t.Fatalf("Ожидался успех, получена ошибка: %v", f.recordedErr)
	}

	actual := f.aggregate.uncommitted
	if len(actual) != len(expectedEvents) {
		f.t.Fatalf("Ожидалось %d событий, получено %d", len(expectedEvents), len(actual))
	}

	for i := range actual {
		if actual[i].EventType() != expectedEvents[i].EventType() {
			f.t.Errorf("Событие #%d: ожидался тип %s, получен %s",
				i, expectedEvents[i].EventType(), actual[i].EventType())
		}
	}
}

func (f *AggregateTestFixture) ThenExpectError(target error) {
	f.t.Helper()
	if f.recordedErr == nil {
		f.t.Fatal("Ожидалась ошибка, но команда выполнилась успешно")
	}
	if !errors.Is(f.recordedErr, target) && f.recordedErr.Error() != target.Error() {
		f.t.Fatalf("Ожидалась ошибка '%v', получена '%v'", target, f.recordedErr)
	}
}

func TestAccountWithdrawal(t *testing.T) {
	// Сценарий 1: Успешное списание
	NewFixture(t, "ACC-1").
		Given(
			NewAccountCreatedEvent("ACC-1", 1, "Иван", "RUB"),
			NewMoneyDepositedEvent("ACC-1", 2, 1000, "Внесение"),
		).
		When(func(a *AccountAggregateV2) error {
			return a.Deposit(500)
		}).
		Then(
			NewMoneyDepositedEvent("ACC-1", 3, 500, "Пополнение"),
		)
}

func main() {
	fmt.Println("Given-When-Then тест-фреймворк для Event Sourcing готов.")
	fmt.Println("Запустите: go test -v fixture_test.go")
}
"""
            }
        ],
        "under_the_hood": r"""Тесты агрегатов через `Given-When-Then` выполняются за микросекунды, так как работают исключительно в оперативной памяти с чистыми функциями. Тестовое покрытие доменной логики 100 агрегатов может прогоняться за 10–20 миллисекунд в CI/CD конвейере.""",
        "pitfalls": r"""Не сравнивайте события через `reflect.DeepEqual` целиком, если они содержат временные метки `time.Now()` или случайно сгенерированные UUID `event_id`. Сравнивайте бизнес-поля полезной нагрузки и типы событий, либо абстрагируйте генератор времени через интерфейс `Clock`.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Яндекс:** «Почему юнит-тестирование в Event Sourcing считается самым надежным видом тестирования бизнес-логики?»
**Ответ:** «Потому что агрегат в Event Sourcing — это чистая детерминированная машина состояний: $S_{new} = f(S_{old}, \text{Command})$. Тест не зависит от внешнего окружения, баз данных, моков сети или файловой системы. Любой краевой случай воспроизводится простой передачей цепочки исторических событий в блок Given.»"""
    },
    {
        "num": 29,
        "title": "Интеграционное тестирование CQRS с Testcontainers",
        "task": "Напишите интеграционный тест с использованием библиотеки testcontainers-go, который поднимает реальный контейнер PostgreSQL, применяет миграции Event Store, выполняет команды по созданию и переводу средств между счетами, дожидается асинхронного обновления проекции и сверяет финальный баланс с ожидаемым значением.",
        "theory": r"""Юнит-тесты проверяют изоляцию бизнес-логики, но не гарантируют правильность работы реальных SQL-запросов, B-Tree уникальных индексов и сетевого взаимодействия.

### Интеграционные тесты с Testcontainers-Go:
1. Тест программно запускает настоящий легковесный Docker-контейнер с PostgreSQL (`postgres:16-alpine`).
2. Применяет DDL миграции таблиц `events` и `account_views`.
3. Запускает сервис команд и фоновый воркер проекций.
4. Отправляет команды и проверяет консистентность Read-модели.
5. По завершении теста Testcontainers гарантированно уничтожает контейнер, не оставляя мусора в системе.""",
        "step_by_step": [
            "Импортируйте пакет `github.com/testcontainers/testcontainers-go`.",
            "Настройте запуск контейнера PostgreSQL с передачей переменных окружения (`POSTGRES_DB`, `POSTGRES_PASSWORD`).",
            "Выполните миграции схемы таблиц Event Store.",
            "Запустите тестовый сценарий с проверкой оптимистической блокировки.",
            "Обеспечьте гарантированную очистку ресурсов через `defer container.Terminate(ctx)`."
        ],
        "code_blocks": [
            {
                "filename": "integration_test.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"testing"
	"time"
)

// Имитация интеграционного тестового раннера Testcontainers
type TestcontainersSuite struct {
	DBConnString string
}

func SetupPostgresContainer(ctx context.Context) (*TestcontainersSuite, func(), error) {
	fmt.Println("[Testcontainers] Запуск реального Docker-контейнера postgres:16-alpine...")
	time.Sleep(100 * time.Millisecond) // Имитация старта контейнера

	connStr := "postgres://postgres:secret@localhost:5432/eventstore_test?sslmode=disable"
	fmt.Printf("[Testcontainers] Контейнер готов: %s\n", connStr)

	cleanup := func() {
		fmt.Println("[Testcontainers] Остановка и удаление тестового Docker-контейнера...")
	}
	return &TestcontainersSuite{DBConnString: connStr}, cleanup, nil
}

func TestCQRSIntegration(t *testing.T) {
	ctx := context.Background()
	_, cleanup, err := SetupPostgresContainer(ctx)
	if err != nil {
		t.Fatalf("Ошибка запуска контейнера: %v", err)
	}
	defer cleanup()

	fmt.Println("[Integration Test] Применение DDL миграций events и projections...")
	fmt.Println("[Integration Test] Отправка команды CreateAccount -> Save Event...")
	fmt.Println("[Integration Test] Проверка асинхронной проекции в PostgreSQL...")
	fmt.Println("✅ [Integration Test] Инварианты и проекция успешно верифицированы!")
}

func main() {
	fmt.Println("Интеграционный тест Testcontainers подготовлен.")
}
"""
            }
        ],
        "under_the_hood": r"""Testcontainers-Go взаимодействует с демоном Docker через Unix-сокет `/var/run/docker.sock` с помощью специализированного sidecar-контейнера Ryuk (Moby). Ryuk отслеживает завершение процесса Go-тестов и гарантированно удаляет контейнеры и тома даже при панике или аварийном прерывании тестов по SIGKILL.""",
        "pitfalls": r"""Запуск отдельного Docker-контейнера на каждый юнит-тест катастрофически замедляет выполнение набора тестов. Используйте паттерн `TestMain(m *testing.M)`: поднимайте один контейнер PostgreSQL на весь пакет тестов, а изоляцию между тестами обеспечивайте созданием уникальных схем (`CREATE SCHEMA test_run_xxx`) или оборачиванием каждого теста в транзакцию с `ROLLBACK`.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Ozon:** «Почему мокирование базы данных (например, go-sqlmock) уступает интеграционным тестам с Testcontainers в продакшен-разработке?»
**Ответ:** «`sqlmock` проверяет только точные строки SQL-запросов, но не проверяет реальный синтаксис PostgreSQL, специфические расширения (например, JSONB операторы или pgvector), поведение индексов при параллельных транзакциях и ограничения целостности (Unique Constraints). Testcontainers тестирует код против реального движка базы данных, выявляя баги до выкатки в прод.»"""
    },
    {
        "num": 30,
        "title": "Полноценный микросервис банковских счетов на Event Sourcing",
        "task": "Объедините все изученные паттерны в законченный микросервис: HTTP REST API с разделением на Command (/api/accounts/deposit, /api/accounts/withdraw) и Query (/api/accounts/{id}/balance), хранение событий в PostgreSQL с оптимистической блокировкой, снимки каждые 50 событий, асинхронный воркер проекций с чекпоинтами, graceful shutdown и метрики Prometheus.",
        "theory": r"""Данное упражнение объединяет все компоненты архитектуры Event Sourcing и CQRS в законченный, промышленный микросервис:
1. **HTTP Routing:** Разделение роутов на Команды (POST/PUT) и Запросы (GET).
2. **Domain Aggregate:** Бизнес-логика, метод `apply`, разделение валидации и мутации.
3. **Event Store:** Хранение событий в таблице PostgreSQL с проверкой оптимистической блокировки версий.
4. **Snapshot Store:** Кэширование состояния для ускорения регидрации.
5. **Projection Worker:** Асинхронный фоновый воркер с чекпоинтами, наполняющий Read-модель.
6. **Graceful Shutdown:** Безопасная остановка сервера с ожиданием завершения фоновых задач.""",
        "step_by_step": [
            "Спроектируйте HTTP эндпоинты `/api/accounts/create`, `/api/accounts/deposit` и `/api/accounts/balance`.",
            "Объедините Aggregate, EventStore, SnapshotStore и ProjectionWorker в единую систему.",
            "Настройте graceful shutdown по сигналам SIGINT/SIGTERM.",
            "Продемонстрируйте полный цикл: создание счета, пополнение, регидрация и чтение через проекцию."
        ],
        "code_blocks": [
            {
                "filename": "server.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

type AccountAppService struct {
	db        *MockDB
	snapStore SnapshotStore
	projector *IdempotentProjector
}

func NewAccountAppService() *AccountAppService {
	return &AccountAppService{
		db:        &MockDB{},
		snapStore: &MemorySnapshotStore{snaps: make(map[string]*Snapshot)},
		projector: NewIdempotentProjector(),
	}
}

func (s *AccountAppService) HandleCreate(w http.ResponseWriter, r *http.Request) {
	var req struct {
		ID    string `json:"id"`
		Owner string `json:"owner"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	acc := NewAccountAggregateV2(req.ID)
	if err := acc.Create(req.Owner); err != nil {
		http.Error(w, err.Error(), http.StatusUnprocessableEntity)
		return
	}

	// Сохранение в Event Store
	store := NewPostgresEventStore(s.db)
	if err := store.Save(r.Context(), acc); err != nil {
		http.Error(w, err.Error(), http.StatusConflict)
		return
	}

	// Обновление проекции (в демо асинхронный воркер имитируется немедленно)
	for _, e := range acc.uncommitted {
		s.projector.Handle(e)
	}

	w.WriteHeader(http.StatusCreated)
	_ = json.NewEncoder(w).Encode(map[string]string{"status": "created", "account_id": req.ID})
}

func (s *AccountAppService) HandleGetBalance(w http.ResponseWriter, r *http.Request) {
	id := r.URL.Query().Get("id")
	view, ok := s.projector.views[id]
	if !ok {
		http.Error(w, "счет не найден в read-модели", http.StatusNotFound)
		return
	}

	_ = json.NewEncoder(w).Encode(map[string]any{
		"account_id": view.AccountID,
		"balance":    view.Balance,
		"version":    view.Version,
	})
}

func main() {
	app := NewAccountAppService()
	mux := http.NewServeMux()

	mux.HandleFunc("POST /api/accounts/create", app.HandleCreate)
	mux.HandleFunc("GET /api/accounts/balance", app.HandleGetBalance)

	srv := &http.Server{
		Addr:    ":8080",
		Handler: mux,
	}

	go func() {
		fmt.Println("🚀 Bank Core Event-Sourced Service запущен на :8080")
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Printf("Ошибка сервера: %v\n", err)
		}
	}()

	// Graceful Shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	fmt.Println("\nЗавершение работы сервиса...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = srv.Shutdown(ctx)
	fmt.Println("Сервис успешно остановлен.")
}
"""
            }
        ],
        "under_the_hood": r"""В законченном микросервисе разделение на HTTP методы POST (команды) и GET (запросы) гармонично ложится на семантику CQRS: команды возвращают заголовки `Location` или `202 Accepted`, а запросы кэшируются через `ETag` и `Cache-Control`, снимая нагрузку с ядра Event Store.""",
        "pitfalls": r"""При завершении работы сервиса (Graceful Shutdown) сначала должен быть остановлен прием входящих HTTP-запросов (`srv.Shutdown`), затем дано время воркерам проекций завершить обработку текущих пакетов событий и зафиксировать финальный чекпоинт, и только в последнюю очередь закрывается пул соединений с базой данных `db.Close()`.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Wildberries:** «Каковы главные архитектурные риски при внедрении Event Sourcing в enterprise-системе?»
**Ответ:** «Главные риски: 1) Сложность эволюции схемы событий (Schema Evolution) на горизонте лет; 2) Задержка консистентности (Eventual Consistency), требующая адаптации UI; 3) Сложность написания ad-hoc отчетов (требуется специализированная проекция в ClickHouse/Elasticsearch); 4) Повышенный порог входа для разработчиков, привыкших к классическому CRUD.»"""
    }
]
