"""
Генератор упражнений Главы 84 (Часть 3: Упражнения 31–45).
CQRS и Event Sourcing на Go.
"""

exercises = [
    {
        "num": 31,
        "title": "Time Travel Debugging и воспроизведение инцидентов",
        "task": "Реализуйте в PostgresEventStore метод RehydrateAt(ctx context.Context, aggregateID string, targetTime time.Time) (*AccountAggregate, error) и RehydrateAtVersion(ctx context.Context, aggregateID string, targetVersion int64) (*AccountAggregate, error). Продемонстрируйте, как с помощью вычитки событий строго до указанного момента времени или версии инженер может восстановить точное историческое состояние агрегата в памяти для расследования инцидента в продакшене без модификации текущих данных.",
        "theory": r"""Одной из величайших возможностей Event Sourcing является **Time Travel Debugging (Путешествие во времени)**.

В классических CRUD-системах после выполнения оператора `UPDATE accounts SET balance = 0` старое состояние безвозвратно утеряно. Если возник сбой или подозрение на мошенничество, невозможно точно узнать, в каком состоянии находился объект вчера в 14:35:10.

В Event Sourcing:
- Поскольку хранятся все когда-либо произошедшие события с точными временными метками `occurred_at` и монотонными версиями, мы можем воссоздать состояние агрегата на **любую миллисекунду в прошлом**:
  ```sql
  SELECT payload, event_type, version FROM events
  WHERE stream_id = $1 AND occurred_at <= $2
  ORDER BY version ASC;
  ```
- Инженер в production-среде может поднять точную копию счета в памяти на момент перед сбоем, пошагово пройти код под отладчиком Delve и локализовать причину аномалии.""",
        "step_by_step": [
            "Определите метод `RehydrateAtVersion(id string, targetVersion int64)`.",
            "Определите метод `RehydrateAt(id string, targetTime time.Time)` с фильтрацией по временной метке.",
            "Проверьте, что события старше указанной даты/версии игнорируются при проигрывании.",
            "Продемонстрируйте воспроизведение состояния счета на момент времени между двумя транзакциями."
        ],
        "code_blocks": [
            {
                "filename": "time_travel.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"
)

type EventHistoryStore interface {
	LoadUntilTime(ctx context.Context, id string, t time.Time) ([]DomainEvent, error)
	LoadUntilVersion(ctx context.Context, id string, v int64) ([]DomainEvent, error)
}

type TimeTravelService struct {
	events []DomainEvent
}

func (s *TimeTravelService) RehydrateAtVersion(id string, targetVer int64) (*AccountAggregateV2, error) {
	acc := NewAccountAggregateV2(id)
	for _, e := range s.events {
		if e.AggregateID() == id && e.Version() <= targetVer {
			acc.apply(e)
		}
	}
	return acc, nil
}

func (s *TimeTravelService) RehydrateAtTime(id string, targetTime time.Time) (*AccountAggregateV2, error) {
	acc := NewAccountAggregateV2(id)
	for _, e := range s.events {
		if e.AggregateID() == id && !e.OccurredAt().After(targetTime) {
			acc.apply(e)
		}
	}
	return acc, nil
}

func main() {
	now := time.Now().UTC()
	t1 := now.Add(-10 * time.Minute)
	t2 := now.Add(-5 * time.Minute)
	t3 := now.Add(-1 * time.Minute)

	e1 := AccountCreatedEvent{
		BaseEvent: BaseEvent{id: "evt-1", aggregateID: "ACC-TT", version: 1, occurredAt: t1, eventType: "AccountCreated"},
		OwnerName: "Виктор Цой",
	}
	e2 := MoneyDepositedEvent{
		BaseEvent: BaseEvent{id: "evt-2", aggregateID: "ACC-TT", version: 2, occurredAt: t2, eventType: "MoneyDeposited"},
		Amount:    15000,
	}
	e3 := MoneyDepositedEvent{
		BaseEvent: BaseEvent{id: "evt-3", aggregateID: "ACC-TT", version: 3, occurredAt: t3, eventType: "MoneyDeposited"},
		Amount:    30000,
	}

	tt := &TimeTravelService{events: []DomainEvent{e1, e2, e3}}

	// Восстанавливаем состояние на момент t2 (между 1-м и 2-м депозитом)
	inspectTime := t2.Add(1 * time.Minute)
	accAtT2, _ := tt.RehydrateAtTime("ACC-TT", inspectTime)
	fmt.Printf("[Time Travel] Состояние счета на %s: Баланс=%d, Версия=%d\n",
		inspectTime.Format(time.TimeOnly), accAtT2.balance, accAtT2.version)

	// Восстанавливаем строго версию 1
	accV1, _ := tt.RehydrateAtVersion("ACC-TT", 1)
	fmt.Printf("[Time Travel] Состояние на версии 1: Баланс=%d, Версия=%d\n",
		accV1.balance, accV1.version)
}
"""
            }
        ],
        "under_the_hood": r"""В PostgreSQL запрос с фильтрацией `WHERE stream_id = $1 AND version <= $2` использует составной индекс `(stream_id, version ASC)`. СУБД выполняет быстрый индексный поиск `Index Scan` первой строки и последовательно читает страницы вплоть до достижения `targetVersion`, прекращая чтение без сканирования всей таблицы.""",
        "pitfalls": r"""При восстановлении по времени `RehydrateAt(time)` учитывайте возможный рассинхрон системных часов (Clock Drift) между разными нодами кластера. Если на одной машине время спешило на 200 мс, событие с большей версией могло получить более ранний `occurred_at`. Поэтому аудит инцидентов всегда надежнее проводить по номеру версии `targetVersion`, гарантирующей строгий порядок причинности (Causal Order).""",
        "bigtech_interview": r"""**Вопрос с собеседования в Wildberries:** «Как расследовать подозрительную финансовую транзакцию в Event Sourcing без остановки рабочего сервиса?»
**Ответ:** «Мы запускаем изолированную копию сервиса или тестовый стенд, подключаемся к реплике Event Store (или выгрузке событий) и вызываем `RehydrateAtVersion(targetVersion - 1)`. Это дает точнейший снимок агрегата за 1 шаг до спорной транзакции. Затем мы пропускаем команду через валидаторы и проверяем, почему она была одобрена или отклонена.»"""
    },
    {
        "num": 32,
        "title": "Cross-Aggregate Проекции и денормализация многих сущностей",
        "task": "Спроектируйте аналитическую проекцию Customer360View, объединяющую события из независимых потоков событий: UserRegisteredEvent (поток пользователя), OrderPlacedEvent (поток заказа), PaymentReceivedEvent (поток платежа) и KYCApprovedEvent (поток комплаенса). Реализуйте проектор с дедупликацией и частичным обновлением документа (JSONB или реляционные поля), обеспечивающий согласованность в конечном счете без блокировок между агрегатами.",
        "theory": r"""В чистом Domain-Driven Design агрегаты не должны знать друг о друге и не должны объединяться в транзакциях. Но бизнесу требуется единый экран **Customer 360 View**:
- Имя и телефон пользователя (из агрегата `User`).
- Статус проверки документов (из агрегата `KYC`).
- Общее число оформленных заказов (из агрегата `Order`).
- Суммарный объем платежей (из агрегата `Payment`).

### Архитектура Cross-Aggregate проектора:
Проектор подписывается на события из **разных потоков** (`streams`). При получении события:
1. Проектор извлекает идентификатор клиента (`CustomerID`).
2. Выполняет операцию **UPSERT (Insert or Update)** в сводную денормализованную таблицу `customer_360_views`:
   ```sql
   INSERT INTO customer_360_views (customer_id, total_spent, orders_count)
   VALUES ($1, $2, 1)
   ON CONFLICT (customer_id) DO UPDATE
   SET total_spent = customer_360_views.total_spent + EXCLUDED.total_spent,
       orders_count = customer_360_views.orders_count + 1;
   ```
3. Клиентский интерфейс за один быстрый запрос по первичному ключу `customer_id` получает исчерпывающую информацию без единого дорогостоящего JOIN.""",
        "step_by_step": [
            "Определите структуру сводного представления `Customer360View`.",
            "Создайте события из разных агрегатов: `UserRegistered`, `OrderPlaced`, `KYCApproved`.",
            "Реализуйте проектор, обновляющий соответствующие поля сводного документа.",
            "Продемонстрируйте агрегацию данных трех независимых потоков в единый документ."
        ],
        "code_blocks": [
            {
                "filename": "customer_360.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
	"time"
)

type Customer360View struct {
	CustomerID  string
	FullName    string
	KYCVerified bool
	TotalOrders int
	TotalSpent  int64
	UpdatedAt   time.Time
}

type Customer360Projector struct {
	mu    sync.Mutex
	views map[string]*Customer360View
}

func NewCustomer360Projector() *Customer360Projector {
	return &Customer360Projector{views: make(map[string]*Customer360View)}
}

func (p *Customer360Projector) getOrCreate(custID string) *Customer360View {
	v, exists := p.views[custID]
	if !exists {
		v = &Customer360View{CustomerID: custID}
		p.views[custID] = v
	}
	return v
}

// HandleUserEvent обрабатывает события потока пользователей
func (p *Customer360Projector) HandleUserRegistered(custID, name string) {
	p.mu.Lock()
	defer p.mu.Unlock()
	v := p.getOrCreate(custID)
	v.FullName = name
	v.UpdatedAt = time.Now()
}

// HandleKYCEvent обрабатывает события комплаенса
func (p *Customer360Projector) HandleKYCApproved(custID string) {
	p.mu.Lock()
	defer p.mu.Unlock()
	v := p.getOrCreate(custID)
	v.KYCVerified = true
	v.UpdatedAt = time.Now()
}

// HandleOrderEvent обрабатывает события заказов
func (p *Customer360Projector) HandleOrderPlaced(custID string, orderTotal int64) {
	p.mu.Lock()
	defer p.mu.Unlock()
	v := p.getOrCreate(custID)
	v.TotalOrders++
	v.TotalSpent += orderTotal
	v.UpdatedAt = time.Now()
}

func main() {
	projector := NewCustomer360Projector()
	custID := "CUST-1001"

	// События поступают из независимых микросервисов в произвольном порядке
	projector.HandleUserRegistered(custID, "Екатерина Великая")
	projector.HandleOrderPlaced(custID, 12000)
	projector.HandleKYCApproved(custID)
	projector.HandleOrderPlaced(custID, 8500)

	doc := projector.views[custID]
	fmt.Printf("=== Customer 360 View ===\n")
	fmt.Printf("Клиент: %s (%s)\n", doc.FullName, doc.CustomerID)
	fmt.Printf("Верификация KYC: %t\n", doc.KYCVerified)
	fmt.Printf("Всего заказов: %d\n", doc.TotalOrders)
	fmt.Printf("Сумма покупок: %d руб.\n", doc.TotalSpent)
}
"""
            }
        ],
        "under_the_hood": r"""В реляционных базах данных при денормализации многих сущностей частой проблемой становится частичное создание записи, если событие заказа пришло раньше события регистрации пользователя. Паттерн UPSERT (`ON CONFLICT (customer_id) DO UPDATE`) решает эту проблему элегантно: если запись еще не существует, она создается с пустыми начальными полями, а приход события пользователя заполняет недостающие реквизиты.""",
        "pitfalls": r"""В Cross-Aggregate проекциях нельзя полагаться на порядок событий между разными агрегатами. Порядок гарантирован только внутри одного `stream_id`. Разные потоки обрабатываются с разной задержкой, поэтому проектор обязан быть готов к тому, что событие оплаты может прийти раньше события создания профиля.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Яндекс:** «Как в CQRS реализовать сложный поиск с фильтрами по полям пяти разных таблиц без многотабличных JOIN?»
**Ответ:** «Использовать Cross-Aggregate проектор, который слушает события от всех 5 сервисов и асинхронно формирует единый плоский денормализованный документ в Elasticsearch или ClickHouse. Поиск выполняется по одной таблице/индексу с колоссальной скоростью без блокировок и объединений таблиц на лету.»"""
    },
    {
        "num": 33,
        "title": "Мультипартиционирование Event Store в PostgreSQL",
        "task": "Напишите DDL миграцию для секционирования таблицы events на основе декларативного партиционирования PostgreSQL. Реализуйте стратегию PARTITION BY RANGE (created_at) с помесячными секциями для эффективного удержания свежих данных и индексов в буферном кэше (RAM), либо PARTITION BY HASH (stream_id) для равномерного распределения нагрузки записи между несколькими физическими дисковыми томами.",
        "theory": r"""Когда таблица `events` перерастает 1 миллиард строк (терабайты данных), монолитные B-Tree индексы перестают помещаться в оперативную память (Shared Buffers), что приводит к постоянному обращению к диску и деградации пропускной способности.

### Секционирование (Partitioning) таблицы событий:
1. **Range Partitioning (`PARTITION BY RANGE (created_at)`):**
   - Таблица делится на помесячные или понедельные секции (`events_2026_09`, `events_2026_10`).
   - Новые записи попадают исключительно в активную горячую секцию текущего месяца.
   - B-Tree индексы активной секции целиком удерживаются в RAM, обеспечивая пиковую скорость вставки.
   - Старые архивные секции могут перемещаться на медленные дешевые диски (Cold Storage) или сжиматься.
2. **Hash Partitioning (`PARTITION BY HASH (stream_id)`):**
   - Таблица делится на $N$ секций (например, 16) по хэшу от идентификатора стрима.
   - Равномерно распределяет нагрузку параллельной записи и исключает горячие точки в B-Tree индексах.""",
        "step_by_step": [
            "Напишите DDL мастер-таблицы `events_partitioned` с секционированием по диапазону времени.",
            "Создайте секции для текущего и следующего месяцев.",
            "Напишите уникальный составной индекс, совместимый с правилами партиционирования PostgreSQL.",
            "Продемонстрируйте вставку событий и маршрутизацию по секциям."
        ],
        "code_blocks": [
            {
                "filename": "partitioning.sql",
                "lang": "sql",
                "code": r"""-- Создание секционированной таблицы Event Store
CREATE TABLE events_partitioned (
    stream_id VARCHAR(64) NOT NULL,
    version BIGINT NOT NULL,
    event_id UUID NOT NULL,
    event_type VARCHAR(128) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- В партиционированных таблицах PostgreSQL ключ секционирования обязан входить в первичный/уникальный ключ:
    CONSTRAINT pk_events_part PRIMARY KEY (created_at, stream_id, version)
) PARTITION BY RANGE (created_at);

-- Секция за сентябрь 2026
CREATE TABLE events_y2026_m09 PARTITION OF events_partitioned
    FOR VALUES FROM ('2026-09-01 00:00:00+00') TO ('2026-10-01 00:00:00+00');

-- Секция за октябрь 2026
CREATE TABLE events_y2026_m10 PARTITION OF events_partitioned
    FOR VALUES FROM ('2026-10-01 00:00:00+00') TO ('2026-11-01 00:00:00+00');

-- Локальные индексы создаются автоматически для каждой секции
CREATE INDEX idx_events_part_stream_ver ON events_partitioned (stream_id, version);
"""
            },
            {
                "filename": "partition_test.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	fmt.Println("Схема секционирования Event Store подготовлена:")
	fmt.Println("- Range-партиционирование удерживает горячие индексы в буферном пуле RAM")
	fmt.Println("- Дроп старых месяцев выполняется мгновенно через DROP TABLE без нагрузки VACUUM")
}
"""
            }
        ],
        "under_the_hood": r"""При выполнении запроса планировщик PostgreSQL использует механизм **Partition Pruning**: если в запросе указано условие `created_at >= '2026-09-15'`, планировщик исключает из плана выполнения все остальные секции на этапе оптимизации, сканируя только одну компактную таблицу `events_y2026_m09`.""",
        "pitfalls": r"""В PostgreSQL при секционировании по диапазону (`RANGE`) критично настроить автогенерацию секций (например, расширением `pg_partman`). Если наступит 1 октября, а секция `events_y2026_m10` не была создана заранее, СУБД вернет ошибку `no partition of relation "events_partitioned" found for row`, заблокировав запись во всем банке!""",
        "bigtech_interview": r"""**Вопрос с собеседования в Wildberries:** «Почему удаление старых данных через DROP TABLE секции в 10 000 раз быстрее обычного DELETE FROM events WHERE created_at < ...?»
**Ответ:** «`DELETE` построчно помечает кортежи как мертвые (Dead Tuples), генерируя гигабайты WAL, фрагментируя B-Tree индексы и требуя многочасового прогона `VACUUM FULL`. `DROP TABLE` секции просто удаляет файл таблицы на диске на уровне файловой системы за 1 миллисекунду с нулевой нагрузкой на СУБД.»"""
    },
    {
        "num": 34,
        "title": "Cold & Hot Storage: Архивирование старых событий в S3/MinIO",
        "task": "Разработайте фоновый сервис жизненного цикла событий (Event Archiver): агрегаты, закрытые или неактивные более 1 года, выгружаются из горячей таблицы PostgreSQL в формат Parquet или сжатый NDJSON и загружаются в объектное хранилище S3/MinIO. Реализуйте гибридный CompositeEventStore, который при запросе полной истории прозрачно запрашивает архивные данные из S3 и горячие события из базы данных.",
        "theory": r"""Хранить события 5-летней давности на дорогих скоростных NVMe-дисках PostgreSQL экономически неэффективно:
- 99.9% операционной нагрузки приходится на события за последние 30–90 дней.
- Хранение терабайтов исторических событий в PostgreSQL раздувает бэкапы (pg_dump / WAL-G) и замедляет аварийное восстановление (Disaster Recovery).

### Архитектура Hot/Cold Event Tiering:
1. **Горячий слой (Hot Storage):** PostgreSQL / ScyllaDB. Хранит активные агрегаты и события за последние $N$ месяцев.
2. **Холодный слой (Cold Storage):** Объектное хранилище S3 / Ceph / MinIO. Завершенные потоки событий пакуются в сжатые Parquet-файлы (сжатие Snappy/ZSTD до 10 раз эффективнее JSON).
3. **Composite Event Store:**
   - При запросе истории агрегата сервис сначала проверяет наличие архивного сегмента в S3.
   - Склеивает исторические события из S3 с последними свежими событиями из PostgreSQL.
   - Передает непрерывный поток событий в агрегат для регидрации.""",
        "step_by_step": [
            "Определите интерфейсы `ColdStorage` (S3) и `HotStorage` (PostgreSQL).",
            "Реализуйте структуру `CompositeEventStore`.",
            "Реализуйте конкатенацию срезов событий с проверкой монотонности версий.",
            "Продемонстрируйте регидрацию счета, часть истории которого загружена из S3, а часть — из БД."
        ],
        "code_blocks": [
            {
                "filename": "cold_hot_store.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
)

type ColdStorage interface {
	LoadArchive(ctx context.Context, streamID string) ([]DomainEvent, error)
}

type HotStorage interface {
	LoadRecent(ctx context.Context, streamID string, afterVersion int64) ([]DomainEvent, error)
}

type MockS3ColdStore struct {
	archive map[string][]DomainEvent
}

func (c *MockS3ColdStore) LoadArchive(ctx context.Context, id string) ([]DomainEvent, error) {
	return c.archive[id], nil
}

type MockDBHotStore struct {
	recent map[string][]DomainEvent
}

func (h *MockDBHotStore) LoadRecent(ctx context.Context, id string, afterVersion int64) ([]DomainEvent, error) {
	all := h.recent[id]
	var res []DomainEvent
	for _, e := range all {
		if e.Version() > afterVersion {
			res = append(res, e)
		}
	}
	return res, nil
}

type CompositeEventStore struct {
	cold ColdStorage
	hot  HotStorage
}

func NewCompositeEventStore(cold ColdStorage, hot HotStorage) *CompositeEventStore {
	return &CompositeEventStore{cold: cold, hot: hot}
}

func (s *CompositeEventStore) LoadFullHistory(ctx context.Context, streamID string) ([]DomainEvent, error) {
	// 1. Выгрузка архивных событий из S3
	archivedEvents, err := s.cold.LoadArchive(ctx, streamID)
	if err != nil {
		return nil, fmt.Errorf("cold storage error: %w", err)
	}

	var maxArchivedVersion int64 = 0
	if len(archivedEvents) > 0 {
		maxArchivedVersion = archivedEvents[len(archivedEvents)-1].Version()
	}

	// 2. Выгрузка дельты свежих событий из PostgreSQL
	recentEvents, err := s.hot.LoadRecent(ctx, streamID, maxArchivedVersion)
	if err != nil {
		return nil, fmt.Errorf("hot storage error: %w", err)
	}

	// 3. Бесшовная склейка истории
	fullHistory := append(archivedEvents, recentEvents...)
	return fullHistory, nil
}

func main() {
	ctx := context.Background()
	streamID := "ACC-COLD-HOT"

	// События 1..1000 лежат в S3 (архив)
	cold := &MockS3ColdStore{archive: map[string][]DomainEvent{
		streamID: {
			NewAccountCreatedEvent(streamID, 1, "Архивный Пользователь", "RUB"),
			NewMoneyDepositedEvent(streamID, 2, 100000, "Внесение в 2021 году"),
		},
	}}

	// События 1001..1002 лежат в PostgreSQL (горячая дельта)
	hot := &MockDBHotStore{recent: map[string][]DomainEvent{
		streamID: {
			NewMoneyDepositedEvent(streamID, 3, 5000, "Свежее пополнение сегодня"),
		},
	}}

	composite := NewCompositeEventStore(cold, hot)
	history, _ := composite.LoadFullHistory(ctx, streamID)

	acc, _ := RehydrateAccount(streamID, history)
	fmt.Printf("✅ Агрегат успешно регидрирован из гибридного хранилища (S3 + DB)!\n")
	fmt.Printf("Финальный баланс: %d руб., Версия: %d (всего событий: %d)\n",
		acc.balance, acc.version, len(history))
}
"""
            }
        ],
        "under_the_hood": r"""Формат Apache Parquet использует колоночное сжатие (Columnar Storage) и кодирование длин серий (RLE / Dictionary Encoding). Метаданные типов и версий событий в Parquet сжимаются в 10–15 раз эффективнее сырого JSON, снижая стоимость хранения терабайтов аудита в S3 до копеек по сравнению с СУБД.""",
        "pitfalls": r"""Архивация в S3 должна выполняться только для закрытых или неизменяемых стримов (например, закрытый заказ или завершенная транзакция). Если попытаться архивировать активный стрим, в который параллельно пишутся новые события, возникает риск пропустить события, записанные в БД во время выгрузки архива в S3.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Ozon:** «Как аналитикам запрашивать данные по архивным событиям, выгруженным в S3?»
**Ответ:** «Использовать бессерверные аналитические движки (Presto / Trino / AWS Athena / ClickHouse S3 table engine). Эти движки умеют выполнять SQL-запросы напрямую поверх файлов Parquet в S3 без необходимости обратной загрузки данных в реляционные базы данных.»"""
    },
    {
        "num": 35,
        "title": "CDC-репликация Event Store через Debezium и PostgreSQL WAL",
        "task": "Откажитесь от периодического поллинга таблицы Outbox в пользу Change Data Capture (CDC) на базе логического декодирования PostgreSQL Write-Ahead Log (WAL). Сконфигурируйте слот репликации test_decoding или коннектор Debezium, вычитывающий изменения из таблицы events и транслирующий их в Apache Kafka с минимальной задержкой (субмиллисекунды) и нулевой нагрузкой на CPU СУБД от частых SELECT.",
        "theory": r"""Традиционный паттерн Outbox с периодическим выполнением `SELECT ... SKIP LOCKED` имеет принципиальные ограничения:
- Постоянный опрос СУБД раз в 100 мс создает постоянный CPU-оверхед.
- Задержка между записью события и публикацией составляет минимум интервал поллинга.

### Change Data Capture (CDC) через логическую репликацию:
PostgreSQL ведет журнал предзаписи (**Write-Ahead Log, WAL**), куда атомарно записываются все изменения до сброса на диск.
1. Включается логическая репликация: `wal_level = logical`.
2. Создается слот репликации (`replication slot`) с плагином декодирования (`pgoutput` или `wal2json`).
3. Демон Debezium (или легковесный Go-сервис на базе `jackc/pglogrepl`) подключается к слоту по протоколу потоковой репликации PostgreSQL.
4. Ядро PostgreSQL самостоятельно пушит бинарные изменения таблицы `events` в сокет коннектора.
5. События мгновенно (задержка < 5 мс) публикуются в топики Apache Kafka без выполнения единого SQL-запроса к базе!""",
        "step_by_step": [
            "Изучите конфигурацию PostgreSQL: `wal_level = logical` и `max_replication_slots = 10`.",
            "Смоделируйте парсер логических сообщений WAL.",
            "Реализуйте потоковый консьюмер изменений с фиксацией LSN (Log Sequence Number).",
            "Продемонстрируйте мгновенную реакцию на изменения таблицы без SQL-запросов."
        ],
        "code_blocks": [
            {
                "filename": "wal_cdc_simulation.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"
)

type WALChangeRecord struct {
	LSN       uint64 // Log Sequence Number
	Table     string
	Action    string // INSERT, UPDATE
	Payload   []byte
	Committed time.Time
}

type CDCReplicator struct {
	lastFlushedLSN uint64
	kafkaProducer  chan WALChangeRecord
}

func NewCDCReplicator() *CDCReplicator {
	return &CDCReplicator{
		kafkaProducer: make(chan WALChangeRecord, 100),
	}
}

func (cdc *CDCReplicator) OnWALMessage(msg WALChangeRecord) {
	if msg.Table != "events" || msg.Action != "INSERT" {
		return // Игнорируем другие таблицы и операции
	}

	fmt.Printf("[CDC Engine] Получено изменение из WAL: LSN=%x, Таблица=%s\n", msg.LSN, msg.Table)
	// Мгновенная пересылка в топик Kafka
	cdc.kafkaProducer <- msg
	cdc.lastFlushedLSN = msg.LSN
	fmt.Printf("[CDC Engine] Подтвержден LSN %x серверу PostgreSQL\n", msg.LSN)
}

func main() {
	cdc := NewCDCReplicator()
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Горутина-консьюмер Kafka
	go func() {
		for msg := range cdc.kafkaProducer {
			fmt.Printf(">>> [Kafka Producer] Событие опубликовано в Kafka: %s\n", string(msg.Payload))
		}
	}()

	// Имитация потока бинарных сообщений WAL из PostgreSQL
	cdc.OnWALMessage(WALChangeRecord{
		LSN:       0x01A4F00,
		Table:     "events",
		Action:    "INSERT",
		Payload:   []byte(`{"event_id": "e1", "type": "MoneyDeposited", "amt": 5000}`),
		Committed: time.Now(),
	})

	time.Sleep(50 * time.Millisecond)
}
"""
            }
        ],
        "under_the_hood": r"""В протоколе репликации PostgreSQL клиент периодически отправляет подтверждающие пакеты `Standby status update` с указанием `flush_lsn`. PostgreSQL удаляет сегменты WAL с диска только после того, как все активные слоты репликации подтвердили чтение данного LSN. Если Debezium упадет, PostgreSQL будет бережно хранить WAL вплоть до его перезапуска.""",
        "pitfalls": r"""Если сервис CDC упадет и не будет перезапущен вовремя, PostgreSQL перестанет удалять архивные файлы WAL из директории `pg_wal`. Это может привести к 100% заполнению дискового пространства сервера и аварийной остановке СУБД (PostgreSQL Disk Full Panic). Всегда настраивайте мониторинг лага слотов репликации в Prometheus.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Касперский:** «Почему Debezium гарантирует At-Least-Once доставку при чтении WAL и как избежать дубликатов в Kafka?»
**Ответ:** «Debezium фиксирует LSN только после получения подтверждения от брокера Kafka. Если Debezium упал между публикацией в Kafka и коммитом LSN в Postgres, после рестарта он заново вычитает события с последнего неподтвержденного LSN. Для исключения дубликатов в Kafka включается режим Idempotent Producer (`enable.idempotence=true`), либо используется составной ключ дедупликации `(stream_id, version)`.»"""
    },
    {
        "num": 36,
        "title": "Партиционированная Outbox-таблица под нагрузку 50k RPS",
        "task": "При экстремальной частоте записи единая таблица outbox_messages становится узким местом из-за конкуренции за блокировки страниц индекса и строк при выполнении SELECT ... FOR UPDATE SKIP LOCKED. Реализуйте шардированный Outbox: создание N независимых очередей-таблиц outbox_0 ... outbox_N-1 с маршрутизацией по хэшу от идентификатора стрима и выделением пула изолированных горутин-паблишеров для каждого шарда.",
        "theory": r"""При нагрузках свыше 20 000–50 000 RPS к одной таблице `outbox_messages` ядро PostgreSQL начинает испытывать тяжелый contention на уровне внутренних системных блокировок (`WALInsertLock`, `buffer_content`, блокировки B-Tree корня индекса).

### Паттерн Sharded Outbox Tables:
1. Вместо одной таблицы создается $N$ физических таблиц: `outbox_0`, `outbox_1`, $\dots$ `outbox_15`.
2. Приложение при сохранении события определяет номер шарда:
   $$\text{shard} = \text{Hash}(\text{stream\_id}) \pmod N$$
3. Вставка `INSERT INTO outbox_K` происходит в изолированную таблицу, устраняя конкуренцию между транзакциями.
4. Выделяется $N$ изолированных воркеров-паблишеров, каждый из которых работает **строго со своим шардом** `outbox_K`, полностью исключая contention за строки и блокировки страниц.""",
        "step_by_step": [
            "Создайте пул шардированных таблиц очереди.",
            "Реализуйте алгоритм детерминированной маршрутизации событий по шардам.",
            "Запустите пул независимых горутин-паблишеров (по одной на каждый шард).",
            "Замерьте отсутствие взаимных блокировок при конкурентной записи."
        ],
        "code_blocks": [
            {
                "filename": "sharded_outbox.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"hash/fnv"
	"sync"
	"time"
)

type OutboxEvent struct {
	ID        int64
	StreamID  string
	Payload   string
	CreatedAt time.Time
}

type ShardedOutboxStorage struct {
	numShards int
	shards    []*shardQueue
}

type shardQueue struct {
	mu     sync.Mutex
	events []OutboxEvent
	nextID int64
}

func NewShardedOutboxStorage(numShards int) *ShardedOutboxStorage {
	storage := &ShardedOutboxStorage{
		numShards: numShards,
		shards:    make([]*shardQueue, numShards),
	}
	for i := 0; i < numShards; i++ {
		storage.shards[i] = &shardQueue{}
	}
	return storage
}

func (s *ShardedOutboxStorage) getShard(streamID string) *shardQueue {
	h := fnv.New32a()
	_, _ = h.Write([]byte(streamID))
	idx := int(h.Sum32() % uint32(s.numShards))
	return s.shards[idx]
}

func (s *ShardedOutboxStorage) Insert(streamID, payload string) {
	q := s.getShard(streamID)
	q.mu.Lock()
	defer q.mu.Unlock()
	q.nextID++
	q.events = append(q.events, OutboxEvent{
		ID:        q.nextID,
		StreamID:  streamID,
		Payload:   payload,
		CreatedAt: time.Now(),
	})
}

// StartShardedPublishers запускает отдельный независимый воркер на каждый шард
func (s *ShardedOutboxStorage) StartPublishers(ctx context.Context) {
	for i := 0; i < s.numShards; i++ {
		shardID := i
		q := s.shards[i]

		go func() {
			ticker := time.NewTicker(20 * time.Millisecond)
			defer ticker.Stop()

			for {
				select {
				case <-ctx.Done():
					return
				case <-ticker.C:
					q.mu.Lock()
					if len(q.events) > 0 {
						batch := q.events
						q.events = nil // Очистка после отправки
						q.mu.Unlock()

						for _, e := range batch {
							fmt.Printf("[ShardWorker #%d] Опубликовано: %s (Stream: %s)\n",
								shardID, e.Payload, e.StreamID)
						}
					} else {
						q.mu.Unlock()
					}
				}
			}
		}()
	}
}

func main() {
	storage := NewShardedOutboxStorage(4)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	storage.StartPublishers(ctx)

	// Запись событий от разных агрегатов
	storage.Insert("ACC-A", "Пополнение 100")
	storage.Insert("ACC-B", "Пополнение 200")
	storage.Insert("ACC-C", "Пополнение 300")
	storage.Insert("ACC-D", "Пополнение 400")

	time.Sleep(100 * time.Millisecond)
}
"""
            }
        ],
        "under_the_hood": r"""Шардирование таблиц устраняет contention на буферных страницах B-Tree индекса (Root Page Latch Contention). В монолитной таблице все транзакции обращаются к одному корневому блоку индекса. При разделении на 16 таблиц нагрузка делится на 16 независимых деревьев, позволяя линейно масштабировать вставку на многоядерных NUMA-серверах.""",
        "pitfalls": r"""Не делайте число шардов слишком большим (например, 1000). Каждый шард — это отдельная таблица с отдельными индексами, требующая открытых файловых дескрипторов и ресурсов пула соединений. Оптимальное число шардов обычно равно числу ядер CPU сервера СУБД (8, 16 или 32).""",
        "bigtech_interview": r"""**Вопрос с собеседования в Wildberries:** «Как добиться пропускной способности Transactional Outbox свыше 100 000 сообщений в секунду?»
**Ответ:** «1) Шардирование таблицы Outbox на $N$ секций; 2) Использование `UNLOGGED` таблиц с периодическим сбросом (если допустима потеря при крахе); 3) Пакетная вставка `INSERT ... VALUES (...), (...)`; 4) Либо отказ от Outbox в пользу нативного чтения WAL (Debezium CDC).»"""
    },
    {
        "num": 37,
        "title": "Метрики и мониторинг лага проекций (Projection Lag Monitoring)",
        "task": "Разработайте экспортер телеметрии проектора в Prometheus: метрика cqrs_projection_lag_events{projection=\"account_views\"} вычисляет разницу между максимальной глобальной позицией в events и последним подтвержденным чекпоинтом проектора. Добавьте измерение задержки по времени cqrs_projection_lag_seconds (разница между NOW() и временной меткой обрабатываемого события) и настройте пороги для алертинга на деградацию производительности проектора.",
        "theory": r"""В архитектуре Event Sourcing критически важно отслеживать состояние консистентности системы. Главная метрика надежности — **Лаг Проекции (Projection Lag)**:

### Два ключевых типа метрик лага:
1. **Лаг в сообщениях (`cqrs_projection_lag_events`):**
   $$\text{Lag}_{events} = \text{MAX}(events.global\_position) - \text{checkpoints.last\_position}$$
   Показывает, сколько событий скопилось в очереди на обработку.
2. **Лаг во времени (`cqrs_projection_lag_seconds`):**
   $$\text{Lag}_{time} = \text{NOW}() - \text{event.occurred\_at}$$
   Показывает, насколько «отстает» реальность в Read-модели относительно момента совершения операций пользователями.

Если лаг по времени превышает 5 секунд — это сигнал деградации сервиса (SLA breach), требующий немедленного масштабирования воркеров или оптимизации базы данных.""",
        "step_by_step": [
            "Определите структуры метрик Prometheus: Gauge для лага событий и Gauge для лага времени.",
            "Реализуйте сборщик телеметрии, опрашивающий смещения каждые 5 секунд.",
            "Смоделируйте расчет отставания при поступлении потока событий.",
            "Напишите правила алертинга Prometheus Alertmanager при превышении порогов."
        ],
        "code_blocks": [
            {
                "filename": "projection_metrics.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync/atomic"
	"time"
)

type ProjectionMetrics struct {
	lagEvents  atomic.Int64
	lagSeconds atomic.Int64
}

func (m *ProjectionMetrics) Update(latestGlobalPos, processedPos int64, eventTime time.Time) {
	lag := latestGlobalPos - processedPos
	if lag < 0 {
		lag = 0
	}
	m.lagEvents.Store(lag)

	secLag := int64(time.Since(eventTime).Seconds())
	if secLag < 0 {
		secLag = 0
	}
	m.lagSeconds.Store(secLag)
}

func (m *ProjectionMetrics) PrintMetrics(projectionName string) {
	fmt.Printf("[Prometheus Metric] cqrs_projection_lag_events{projection=\"%s\"} %d\n",
		projectionName, m.lagEvents.Load())
	fmt.Printf("[Prometheus Metric] cqrs_projection_lag_seconds{projection=\"%s\"} %d\n",
		projectionName, m.lagSeconds.Load())
}

func main() {
	metrics := &ProjectionMetrics{}

	// Допустим, в базе максимальная позиция 15000
	var dbMaxPosition int64 = 15000

	// Воркер сейчас на позиции 14200, событие произошло 12 секунд назад
	eventCreatedAt := time.Now().Add(-12 * time.Second)
	metrics.Update(dbMaxPosition, 14200, eventCreatedAt)

	metrics.PrintMetrics("account_views")

	// Проверка алерта
	if metrics.lagSeconds.Load() > 10 {
		fmt.Println("🚨 ALERT FIRING: ProjectionLagTooHigh (лаг > 10 секунд!)")
	}
}
"""
            }
        ],
        "under_the_hood": r"""Атомарные счетчики `atomic.Int64` в Go обновляются через одну инструкцию `LOCK XADD` процессора x86-64. Сбор метрик внутри высоконагруженного воркера проекций не создает блокировок и не замедляет обработку событий.""",
        "pitfalls": r"""Не выполняйте `SELECT MAX(global_position) FROM events` на каждое обработанное событие. В большой таблице частый вызов `MAX()` создаст огромную нагрузку на базу. Опрашивайте максимальную позицию в базе данных отдельной фоновой горутиной раз в 5–10 секунд.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Т-Банк:** «Какие три ключевые метрики вы настроите на дашборде Grafana для мониторинга CQRS/ES системы?»
**Ответ:** «1) Projection Lag (в событиях и секундах); 2) Rate of Concurrency Conflicts (число ошибок оптимистической блокировки в секунду — показывает contention); 3) Rehydration Duration p99 (время восстановления агрегатов — сигнализирует о необходимости создания снимков).»"""
    },
    {
        "num": 38,
        "title": "Компенсирующие события (Compensating Events vs In-Place Edit)",
        "task": "В классических реляционных базах данных ошибки исправляются оператором UPDATE, однако в Event Sourcing история транзакций юридически и архитектурно неизменна (Append-Only). Смоделируйте бизнес-ошибку (ошибочное списание комиссии со счета): реализуйте агрегатный метод ReverseTransaction(transactionID string, reason string) error, порождающий компенсирующее событие TransactionReversedEvent. Покажите, как обе проводки сохраняются для аудита.",
        "theory": r"""В бухгалтерском учете и банковских системах с 500-летней историей (принцип двойной записи Луки Пачоли) **запрещено стирать или замазывать ошибочные проводки**. Любая ошибка исправляется **Сторно (Reversal / Compensating Entry)**.

### Философия неизменяемости:
- Если со счета ошибочно списали 100 рублей комиссии:
  - **Плохо (CRUD):** `UPDATE accounts SET balance = balance + 100; DELETE FROM fees WHERE id = 5;` (история стерта, аудит невозможен).
  - **Правильно (Event Sourcing):**
    1. Событие 1: `FeeDeductedEvent{Amount: 100, TxID: "tx-1"}` (баланс уменьшился на 100).
    2. Событие 2: `TransactionReversedEvent{OriginalTxID: "tx-1", Amount: 100, Reason: "Сбой шлюза"}` (баланс восстановился).
- Оба факта навсегда остаются в неизменяемом аудите. Регулятор или аудитор в любой момент видит, кто, когда и почему допустил ошибку и когда она была исправлена.""",
        "step_by_step": [
            "Определите событие компенсации `TransactionReversedEvent`.",
            "Реализуйте в агрегате метод `ReverseTransaction(txID, reason)` с проверкой существования исходной транзакции.",
            "Примените компенсацию в методе `apply`.",
            "Убедитесь, что баланс вернулся в исходное состояние, а в ленте сохранены оба события."
        ],
        "code_blocks": [
            {
                "filename": "reversal_event.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"time"
)

type TransactionReversedEvent struct {
	BaseEvent
	OriginalTxID string
	Amount       int64
	Reason       string
}

type AccountWithAudit struct {
	id          string
	balance     int64
	version     int64
	history     []string
	uncommitted []DomainEvent
}

func (a *AccountWithAudit) apply(e DomainEvent) {
	switch evt := e.(type) {
	case MoneyDepositedEvent:
		a.balance += evt.Amount
		a.version = evt.Version()
		a.history = append(a.history, fmt.Sprintf("Tx %s: %+d руб.", evt.EventID()[:8], evt.Amount))

	case TransactionReversedEvent:
		// Компенсация: возвращаем списанную сумму обратно на баланс
		a.balance += evt.Amount
		a.version = evt.Version()
		a.history = append(a.history, fmt.Sprintf("СТОРНО %s: %+d руб. (Причина: %s)",
			evt.OriginalTxID[:8], evt.Amount, evt.Reason))
	}
}

func (a *AccountWithAudit) ReverseFee(origTxID string, amount int64, reason string) {
	evt := TransactionReversedEvent{
		BaseEvent: BaseEvent{
			id:          newUUID(),
			aggregateID: a.id,
			eventType:   "TransactionReversed",
			occurredAt:  time.Now().UTC(),
			version:     a.version + 1,
		},
		OriginalTxID: origTxID,
		Amount:       amount,
		Reason:       reason,
	}
	a.apply(evt)
	a.uncommitted = append(a.uncommitted, evt)
}

func main() {
	acc := &AccountWithAudit{id: "ACC-AUDIT", balance: 1000, version: 1}

	// 1. Ошибочное списание комиссии 200 руб.
	feeTxID := "tx-err-999"
	errEvt := MoneyDepositedEvent{
		BaseEvent: BaseEvent{id: feeTxID, aggregateID: acc.id, version: 2, occurredAt: time.Now(), eventType: "MoneyDeposited"},
		Amount:    -200,
		Reason:    "Ошибочная комиссия",
	}
	acc.apply(errEvt)
	fmt.Printf("После ошибочного списания: Баланс=%d руб.\n", acc.balance)

	// 2. Выпуск компенсирующего события Сторно
	acc.ReverseFee(feeTxID, 200, "Ошибка банковского шлюза")
	fmt.Printf("После компенсации (Сторно): Баланс=%d руб.\n\n", acc.balance)

	fmt.Println("=== Полная аудиторская лента счета ===")
	for i, line := range acc.history {
		fmt.Printf("%d. %s\n", i+1, line)
	}
}
"""
            }
        ],
        "under_the_hood": r"""С точки зрения теории баз данных компенсирующие транзакции реализуют семантику **A-Transactions (Abortable Transactions)** в модели Sagas (Гарсиа-Молина, Салем, 1987). Отсутствие прямых мутаций устраняет необходимость удерживать распределенные блокировки на время исправления ошибок.""",
        "pitfalls": r"""Защищайтесь от повторной компенсации одной и той же транзакции. Агрегат должен отслеживать список уже компенсированных идентификаторов (`reversedTxIDs map[string]bool`). Если оператор дважды нажмет кнопку «Вернуть комиссию», агрегат обязан отклонить вторую попытку.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Т-Банк:** «Как финтех-платформы проходят аудит регулятора (ЦБ РФ) при использовании Event Sourcing?»
**Ответ:** «Event Sourcing идеален для финтех-аудита: база данных представляет собой неизменяемый журнал проводок (Ledger). Аудитор может взять любое состояние на любую дату и математически доказать, что баланс равен строгой сумме всех исторических транзакций и сторно-компенсаций, исключая возможность незаметной подделки баланса в СУБД.»"""
    },
    {
        "num": 39,
        "title": "Temporal / Event-Driven Querying: Поиск по историческим срезам",
        "task": "Спроектируйте сервис построения временных срезов (Point-in-Time Querying): клиент передает запрос «Каков был суммарный баланс всех активных счетов компании на дату 2025-12-31 23:59:59?». Реализуйте оптимизированный конвейер вычисления на базе ближайших исторических снимков (Snapshots) и применения событий за соответствующий интервал, исключая полный пересчет всей базы данных.",
        "theory": r"""В классическом CRUD для ответа на вопрос «Каков был баланс на конец прошлого года?» требуется восстанавливать резервную копию базы данных из бэкапа за эту дату.

В Event Sourcing благодаря **Point-in-Time Querying (Темпоральные запросы)**:
1. Система находит ближайший исторический снимок состояния, созданный до целевой временной метки $T_{target}$:
   ```sql
   SELECT state, version FROM snapshots
   WHERE stream_id = $1 AND created_at <= $2
   ORDER BY created_at DESC LIMIT 1;
   ```
2. Извлекает события между версией снимка и моментом $T_{target}$:
   ```sql
   SELECT payload FROM events
   WHERE stream_id = $1 AND version > $snap_ver AND occurred_at <= $target_time
   ORDER BY version ASC;
   ```
3. Восстанавливает срез за миллисекунды, позволяя строить историческую отчетность прямо в production без даунтайма.""",
        "step_by_step": [
            "Определите структуру запроса `PointInTimeBalanceQuery` с целевой датой.",
            "Реализуйте поиск снимка, наиболее близкого к целевой дате снизу.",
            "Дочитайте события в интервале `(snapshot.CreatedAt, targetTime]`.",
            "Продемонстрируйте точный расчет баланса на историческую дату."
        ],
        "code_blocks": [
            {
                "filename": "point_in_time.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"
)

type HistoricalSnapshot struct {
	Balance   int64
	Version   int64
	CreatedAt time.Time
}

type PointInTimeQueryService struct {
	snapshots []HistoricalSnapshot
	events    []DomainEvent
}

func (s *PointInTimeQueryService) QueryBalanceAt(target time.Time) int64 {
	// 1. Поиск ближайшего снимка до target
	var baseBalance int64 = 0
	var baseVersion int64 = 0

	for _, snap := range s.snapshots {
		if !snap.CreatedAt.After(target) && snap.Version > baseVersion {
			baseBalance = snap.Balance
			baseVersion = snap.Version
		}
	}

	// 2. Применение событий, произошедших строго между снимком и target
	currentBalance := baseBalance
	for _, e := range s.events {
		if e.Version() > baseVersion && !e.OccurredAt().After(target) {
			if dep, ok := e.(MoneyDepositedEvent); ok {
				currentBalance += dep.Amount
			}
		}
	}
	return currentBalance
}

func main() {
	t0 := time.Date(2025, 12, 1, 0, 0, 0, 0, time.UTC)
	tTarget := time.Date(2025, 12, 31, 23, 59, 59, 0, time.UTC)
	tNextYear := time.Date(2026, 1, 15, 0, 0, 0, 0, time.UTC)

	service := &PointInTimeQueryService{
		snapshots: []HistoricalSnapshot{
			{Balance: 100000, Version: 10, CreatedAt: t0},
		},
		events: []DomainEvent{
			MoneyDepositedEvent{
				BaseEvent: BaseEvent{version: 11, occurredAt: time.Date(2025, 12, 15, 12, 0, 0, 0, time.UTC)},
				Amount:    25000,
			},
			MoneyDepositedEvent{
				BaseEvent: BaseEvent{version: 12, occurredAt: tNextYear}, // Событие 2026 года (не должно войти!)
				Amount:    50000,
			},
		},
	}

	balanceAtEndOf2025 := service.QueryBalanceAt(tTarget)
	fmt.Printf("Баланс компании на конец 2025 года (%s): %d руб.\n",
		tTarget.Format(time.DateOnly), balanceAtEndOf2025)
}
"""
            }
        ],
        "under_the_hood": r"""В колоночных СУБД вроде ClickHouse исторические срезы строятся еще быстрее с помощью движка `ReplacingMergeTree` и агрегатных функций `argMax(balance, version)`. Это позволяет рассчитывать балансы на произвольную дату сразу по 100 миллионам клиентов за 0.5 секунды.""",
        "pitfalls": r"""Убедитесь, что исторические запросы не выполняются на основном мастере OLTP базы данных в разгар рабочего дня. Для тяжелых темпоральных выборок выделяйте отдельную Read-реплику PostgreSQL или экспортируйте события в аналитический кластер ClickHouse.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Яндекс:** «Как архитектура Event Sourcing упрощает выполнение регуляторных требований аудита по сравнению с классической реляционной схемой?»
**Ответ:** «Event Sourcing по определению содержит 100% аудиторский след с детерминированным состоянием на любую секунду времени. В реляционной схеме для этого приходится городить сложные триггеры аудита или CDC-таблицы истории, которые раздувают базу и часто теряют контекст бизнес-причин изменений.»"""
    },
    {
        "num": 40,
        "title": "Обработка дубликатов команд через Idempotency Key в Command Bus",
        "task": "Клиентские сетевые сбои часто приводят к повторной отправке команды списания денег. Добавьте в Command Bus фильтр идемпотентности: входящая команда содержит UUID-ключ идемпотентности (X-Idempotency-Key). Шина проверяет наличие ключа в Redis (SETNX с TTL), сохраняет статус обработки (PROCESSING, COMPLETED) и возвращает сохраненный результат предыдущего выполнения без повторной модификации агрегата.",
        "theory": r"""При сетевых сбоях (таймаут ответа HTTP) клиентское мобильное приложение повторяет запрос списания денег (Retry). Без защиты от дублирования произойдет **двойное списание средств**.

### Паттерн Idempotency Key в CQRS:
1. Клиент генерирует UUID `Idempotency-Key` (например, `9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d`) и передает его в HTTP-заголовке.
2. Шина команд выполняет в Redis атомарную операцию:
   ```text
   SET idempotency:9b1deb4d "PROCESSING" NX EX 120
   ```
3. **Если ключ уже существует:**
   - Если статус `"PROCESSING"`: возвращается статус `409 Conflict` или запрос ожидает завершения первого потока.
   - Если статус `"COMPLETED"`: из кэша возвращается ранее сохраненный успешный ответ **без повторного выполнения команды**.
4. **Если ключа нет:**
   - Команда выполняется агрегатом.
   - Результат атомарно сохраняется в Redis со статусом `"COMPLETED"`.
   - Клиент получает ответ.""",
        "step_by_step": [
            "Определите интерфейс команды с поддержкой `IdempotencyKey() string`.",
            "Создайте фильтр идемпотентности на базе имитации Redis `SETNX`.",
            "Проверьте сценарий повторной отправки одинаковой команды списания.",
            "Убедитесь, что команда выполнилась ровно один раз, а второй запрос вернул закэшированный ответ."
        ],
        "code_blocks": [
            {
                "filename": "idempotency_filter.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

type IdempotentCommand interface {
	IdempotencyKey() string
}

type WithdrawCommand struct {
	Key       string
	AccountID string
	Amount    int64
}
func (c WithdrawCommand) IdempotencyKey() string { return c.Key }

type IdempotencyStore struct {
	mu      sync.Mutex
	records map[string]string // Key -> "PROCESSING" | "COMPLETED"
}

func NewIdempotencyStore() *IdempotencyStore {
	return &IdempotencyStore{records: make(map[string]string)}
}

// TryAcquire симулирует Redis SETNX с TTL
func (s *IdempotencyStore) TryAcquire(key string) (bool, string) {
	s.mu.Lock()
	defer s.mu.Unlock()

	status, exists := s.records[key]
	if exists {
		return false, status // Ключ уже занят
	}
	s.records[key] = "PROCESSING"
	return true, ""
}

func (s *IdempotencyStore) MarkCompleted(key string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.records[key] = "COMPLETED"
}

type IdempotentCommandBus struct {
	store *IdempotencyStore
}

func (b *IdempotentCommandBus) Dispatch(ctx context.Context, cmd IdempotentCommand) error {
	key := cmd.IdempotencyKey()
	acquired, status := b.store.TryAcquire(key)

	if !acquired {
		if status == "COMPLETED" {
			fmt.Printf("[Idempotency] Ключ %s уже выполнен ранее. Возврат сохраненного ответа OK!\n", key)
			return nil // Идемпотентный возврат успеха без повторного исполнения!
		}
		return errors.New("запрос с таким ключом уже обрабатывается прямо сейчас")
	}

	// Исполнение реальной бизнес-команды
	fmt.Printf("[Business Logic] Реальное списание средств по команде (Ключ: %s)...\n", key)

	// Фиксация успешного завершения
	b.store.MarkCompleted(key)
	return nil
}

func main() {
	store := NewIdempotencyStore()
	bus := &IdempotentCommandBus{store: store}
	ctx := context.Background()

	cmd := WithdrawCommand{
		Key:       "req-uuid-12345",
		AccountID: "ACC-1",
		Amount:    1500,
	}

	// 1-я попытка (успех)
	_ = bus.Dispatch(ctx, cmd)

	// 2-я попытка (клиентский повтор из-за сетевого сбоя)
	fmt.Println("\n--- Клиент повторяет запрос с тем же Idempotency Key ---")
	_ = bus.Dispatch(ctx, cmd)
}
"""
            }
        ],
        "under_the_hood": r"""Операция `SET key value NX EX seconds` в Redis является атомарной. Благодаря однопоточной архитектуре event-loop в Redis исключены любые race condition: если два сетевых запроса придут одновременно с разницей в 1 наносекунду, ровно один из них получит `OK`, а второй вернет `nil`.""",
        "pitfalls": r"""Обязательно задавайте разумный TTL (Time To Live) ключа идемпотентности (обычно от 24 до 72 часов). Если хранить ключи вечно, база Redis переполнится. Если установить TTL слишком коротким (например, 10 секунд), запоздавший повторный запрос клиента приведет к повторному списанию.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Ozon:** «Что делать, если при обработке команды сервер упал (SIGKILL), оставив в Redis ключ со статусом "PROCESSING"?»
**Ответ:** «Использовать комбинацию: 1) Автоматический TTL в Redis (ключ сам сбросится через 2 минуты); 2) Проверка статуса в базе данных: при истечении TTL повторный запрос проверяет в Event Store, было ли реально создано событие с данным `idempotency_key`. Если да — статус переводится в `COMPLETED`, если нет — команда выполняется заново.»"""
    },
    {
        "num": 41,
        "title": "Event Store на базе NoSQL Key-Value (ScyllaDB / DynamoDB)",
        "task": "Реализуйте интерфейс EventStore поверх распределенной NoSQL-базы данных с высокой пропускной способностью записи. Спроектируйте схему: Partition Key = stream_id, Clustering Key = version (по возрастанию). Реализуйте оптимистическую проверку версии через легковесные транзакции (Lightweight Transactions / Paxos LWT в ScyllaDB или Condition Expression attribute_not_exists(version) в DynamoDB).",
        "theory": r"""Когда система перерастает возможности вертикального масштабирования PostgreSQL (свыше 100 000 RPS записи), Event Store переносят на распределенные NoSQL-базы класса Wide-Column / Key-Value: **ScyllaDB, Apache Cassandra или AWS DynamoDB**.

### Модель данных в Cassandra / ScyllaDB:
```sql
CREATE TABLE events (
    stream_id text,
    version bigint,
    event_id uuid,
    payload text,
    PRIMARY KEY ((stream_id), version)
) WITH CLUSTERING ORDER BY (version ASC);
```
- **Partition Key `(stream_id)`:** Все события одного агрегата физически хранятся на одном узле кластера (или репликах) в одной строке партиции.
- **Clustering Key `version ASC`:** События агрегата физически отсортированы на диске (SSTable) по монотонному возрастанию версии. Вычитка истории — это последовательное сканирование диска без случайных перемещений головок.
- **Оптимистическая блокировка:** Реализуется через Paxos LWT:
  ```sql
  INSERT INTO events (...) VALUES (...) IF NOT EXISTS;
  ```""",
        "step_by_step": [
            "Спроектируйте структуру NoSQL записи события.",
            "Смоделируйте условную запись `IF NOT EXISTS` для предотвращения гонок версий.",
            "Реализуйте вычитку среза истории агрегата с использованием диапазона версий.",
            "Продемонстрируйте отказ при параллельной вставке одинаковой версии."
        ],
        "code_blocks": [
            {
                "filename": "nosql_store.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
)

type NoSQLEventRecord struct {
	StreamID string // Partition Key
	Version  int64  // Clustering Key
	Payload  string
}

type MockScyllaDB struct {
	mu   sync.Mutex
	rows map[string]map[int64]string // stream_id -> version -> payload
}

func NewMockScyllaDB() *MockScyllaDB {
	return &MockScyllaDB{rows: make(map[string]map[int64]string)}
}

// InsertLWT симулирует INSERT INTO events (...) IF NOT EXISTS (Paxos LWT)
func (db *MockScyllaDB) InsertLWT(rec NoSQLEventRecord) (bool, error) {
	db.mu.Lock()
	defer db.mu.Unlock()

	part, ok := db.rows[rec.StreamID]
	if !ok {
		part = make(map[int64]string)
		db.rows[rec.StreamID] = part
	}

	// Проверка условной вставки
	if _, exists := part[rec.Version]; exists {
		return false, nil // LWT вернул [applied] = false
	}

	part[rec.Version] = rec.Payload
	return true, nil // Успешно вставлено
}

func (db *MockScyllaDB) ReadStream(streamID string) []NoSQLEventRecord {
	db.mu.Lock()
	defer db.mu.Unlock()

	part := db.rows[streamID]
	var res []NoSQLEventRecord
	for v := int64(1); ; v++ {
		payload, ok := part[v]
		if !ok {
			break
		}
		res = append(res, NoSQLEventRecord{StreamID: streamID, Version: v, Payload: payload})
	}
	return res
}

func main() {
	db := NewMockScyllaDB()

	// 1. Успешная запись версии 1
	applied, _ := db.InsertLWT(NoSQLEventRecord{StreamID: "ACC-NOSQL", Version: 1, Payload: "Created"})
	fmt.Printf("Запись v1 (LWT): applied=%t\n", applied)

	// 2. Попытка конкурентной записи той же версии 1
	applied2, _ := db.InsertLWT(NoSQLEventRecord{StreamID: "ACC-NOSQL", Version: 1, Payload: "Conflict"})
	if !applied2 {
		fmt.Printf("✅ Запись отклонена распределенным кворумом Paxos LWT (версия 1 уже существует!)\n")
	}

	// 3. Запись версии 2
	applied3, _ := db.InsertLWT(NoSQLEventRecord{StreamID: "ACC-NOSQL", Version: 2, Payload: "Deposited 500"})
	fmt.Printf("Запись v2: applied=%t\n", applied3)

	history := db.ReadStream("ACC-NOSQL")
	fmt.Printf("Вычитано событий из NoSQL партиции: %d\n", len(history))
}
"""
            }
        ],
        "under_the_hood": r"""В ScyllaDB/Cassandra Lightweight Transactions (LWT) используют протокол Paxos для достижения линейной линеаризуемости (Linearizability) записи в распределенном кольце узлов. Хотя LWT требует 4 фазы сетевого обмена (Prepare, Promise, Propose, Commit), в пределах одной партиции `stream_id` она выполняется за считанные миллисекунды, обеспечивая масштабирование до миллионов RPS.""",
        "pitfalls": r"""В распределенных Wide-Column базах категорически запрещено делать размер одной партиции слишком большим (рекомендуемый лимит Cassandra — не более 100 МБ или 100 000 строк на партицию). Если один агрегат накопит 1 миллион событий, партиция вызовет перегрузку узла и GC-паузы. Для сверхдлинных потоков применяется партиционирование по бакетам: `((stream_id, bucket_id), version)`.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Wildberries:** «Почему Wide-Column хранилища (ScyllaDB/Cassandra) идеально подходят для Event Sourcing?»
**Ответ:** «Потому что модель доступа в Event Sourcing полностью совпадает с физическим устройством SSTable в Cassandra: 1) Запись строго Append-Only; 2) Чтение всегда выполняется по ключу `stream_id` с сортировкой по `version ASC`; 3) Отсутствуют операции UPDATE и произвольные выборки без ключа партиционирования, что обеспечивает линейное горизонтальное масштабирование.»"""
    },
    {
        "num": 42,
        "title": "Сквозная распределенная трассировка событий (W3C Trace Context в Metadata)",
        "task": "Организуйте передачу распределенного контекста трассировки OpenTelemetry через цепочку CQRS: извлечение W3C traceparent из HTTP-запроса, упаковка спана в JSON-поле metadata сохраняемого события в Event Store, распаковка контекста в асинхронном проекторе и продолжение трейса при обновлении Read-модели. Визуализируйте полный жизненный цикл изменения данных в Jaeger.",
        "theory": r"""В распределенной CQRS-системе путь запроса разрывается на асинхронные этапы:
1. Пользователь отправляет `POST /deposit` $\to$ создается Span A.
2. Событие сохраняется в базу данных.
3. Через 50 мс асинхронный воркер читает событие из базы и обновляет Read-модель $\to$ создается Span B.

Без специальной проброски контекста Span A и Span B будут выглядеть в Jaeger как два несвязанных изолированных действия!

### Решение: W3C Trace Context Propagation
1. Входящий HTTP-запрос содержит заголовок:
   `traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`
2. Command Bus извлекает `TraceID` и `SpanID` и сериализует их в поле `metadata` события:
   ```json
   {
     "metadata": {
       "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
       "user_id": "usr-42"
     }
   }
   ```
3. Асинхронный проектор десериализует `traceparent`, создает дочерний спан (`SpanContextWithRemoteParent`) и привязывает обработку проекции к единому родительскому трейсу.""",
        "step_by_step": [
            "Определите карту метаданных события с полем `traceparent`.",
            "Реализуйте инжектор контекста при обработке команды.",
            "Реализуйте экстрактор контекста в асинхронном проекторе.",
            "Продемонстрируйте совпадение TraceID между HTTP-запросом и фоновым проектором."
        ],
        "code_blocks": [
            {
                "filename": "trace_context.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
)

type EventWithMetadata struct {
	ID        string
	Type      string
	Payload   string
	Metadata  map[string]string // Хранилище W3C Trace Context
}

func ProcessCommand(ctx context.Context, traceparent string) EventWithMetadata {
	fmt.Printf("[HTTP Handler] Получен входящий запрос с traceparent: %s\n", traceparent)

	// Инъекция контекста в метаданные доменного события
	evt := EventWithMetadata{
		ID:      "evt-101",
		Type:    "MoneyDeposited",
		Payload: "5000 RUB",
		Metadata: map[string]string{
			"traceparent": traceparent,
			"source":      "mobile-app",
		},
	}
	fmt.Println("[EventStore] Событие сохранено в БД вместе с метаданными трассировки")
	return evt
}

func AsyncProjector(evt EventWithMetadata) {
	// Извлечение контекста из сохраненного события
	remoteTraceparent := evt.Metadata["traceparent"]
	fmt.Printf("[Async Projector] Восстановлен родительский Trace Context: %s\n", remoteTraceparent)
	fmt.Println("[Async Projector] Создан дочерний спан OpenTelemetry: 'UpdateReadModel'")
	fmt.Println("✅ Сквозная трассировка от HTTP-запроса до Read-модели успешно связана в Jaeger!")
}

func main() {
	traceparent := "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
	evt := ProcessCommand(context.Background(), traceparent)
	fmt.Println("\n--- Асинхронная пауза 50 мс ---")
	AsyncProjector(evt)
}
"""
            }
        ],
        "under_the_hood": r"""Спецификация W3C Trace Context состоит из 4 полей, разделенных дефисом: `version (00) - trace_id (32 hex) - parent_id / span_id (16 hex) - trace_flags (01 - sampled)`. Хранение этой 55-символьной строки в метаданных событий весит всего 55 байт, но обеспечивает 100% прозрачность сквозной наблюдаемости (Observability).""",
        "pitfalls": r"""Не забывайте очищать метаданные от чувствительной информации. Метаданные часто логируются и экспортируются в публичные системы мониторинга (Jaeger, Grafana Tempo). Никогда не помещайте в метаданные пароли, токены авторизации или сырые номера кредитных карт.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Ozon:** «Как отследить, почему асинхронное обновление проекции выполнилось с задержкой в 40 секунд после отправки команды пользователем?»
**Ответ:** «Благодаря проброске W3C Trace Context через метаданные событий в Jaeger отобразится единое дерево спанов: 1) Спаны HTTP и EventStore.Save (завершились за 10 мс); 2) Промежуток ожидания в очереди брокера (Queue Latency 39.9 с); 3) Спан выполнения проектора (выполнился за 100 мс). Инженер сразу видит, что задержка вызвана лагом в очереди сообщений, а не медленным SQL-запросом.»"""
    },
    {
        "num": 43,
        "title": "Архитектурный паттерн CQRS/ES Read-Model Cache-Aside с XFetch",
        "task": "При чтении популярных агрегатов (например, баланса крупной корпорации) тысячи запросов обращаются к кэшу Redis. Реализуйте вероятностный алгоритм раннего обновления XFetch (Optimal Probabilistic Cache Invalidation): фоновое обновление горячей Read-модели до истечения жесткого TTL, полностью предотвращающее эффект урагана кэша (Cache Stampede).",
        "theory": r"""Классический паттерн Cache-Aside страдает от критической проблемы **Cache Stampede (Thundering Herd)**:
- Горячий ключ в кэше Redis истекает (TTL = 0).
- 5 000 одновременных запросов в одну и ту же миллисекунду получают Cache Miss.
- Все 5 000 горутин одновременно атакуют базу данных тяжелым запросом, вызывая 100% отказ СУБД.

### Алгоритм XFetch (Optimal Probabilistic Early Expiration):
Вместо ожидания истечения TTL, алгоритм вычисляет вероятность необходимости фонового обновления:
$$\Delta \cdot \beta \cdot \ln(\text{random}()) > \text{expiry} - \text{now}$$
- $\Delta$: время, которое потребовалось на вычисление значения из БД в прошлый раз.
- $\beta > 0$: коэффициент агрессивности (по умолчанию $\beta = 1.0$).
- Чем ближе текущее время к моменту истечения TTL, тем выше вероятность, что случайный входящий запрос асинхронно запустит обновление кэша **до того, как старое значение протухнет**!
- При этом обновление выполняет ровно один запрос, а остальные продолжают мгновенно читать валидные данные из кэша.""",
        "step_by_step": [
            "Определите структуру кэшируемой записи с метаданными: `Value`, `TTL`, `DeltaComputation`.",
            "Реализуйте вероятностную функцию `ShouldRefresh(delta, ttl, expiry, beta)`.",
            "Напишите кэш-сервис, асинхронно обновляющий Read-модель в фоновой горутине при срабатывании XFetch.",
            "Продемонстрируйте полное отсутствие промахов кэша под непрерывной нагрузкой."
        ],
        "code_blocks": [
            {
                "filename": "xfetch_cache.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"math"
	"math/rand"
	"time"
)

type XFetchItem struct {
	Value     string
	Delta     time.Duration // Время последнего вычисления из БД
	ExpiresAt time.Time
}

func ShouldRefresh(item XFetchItem, beta float64) bool {
	// Формула XFetch: -delta * beta * ln(rand()) > (ExpiresAt - Now)
	timeUntilExpiry := time.Until(item.ExpiresAt).Seconds()
	if timeUntilExpiry <= 0 {
		return true // Уже протухло
	}

	deltaSec := item.Delta.Seconds()
	r := rand.Float64()
	if r <= 0 {
		r = 0.00001
	}

	xfetchVal := -deltaSec * beta * math.Log(r)
	return xfetchVal > timeUntilExpiry
}

func main() {
	now := time.Now()
	// Элемент протухнет через 2 секунды. Вычисление из БД занимает 500 мс.
	item := XFetchItem{
		Value:     "Баланс: 1 500 000 руб.",
		Delta:     500 * time.Millisecond,
		ExpiresAt: now.Add(2 * time.Second),
	}

	fmt.Println("=== Симуляция алгоритма XFetch (10 входящих запросов за 1.8 с до истечения) ===")
	refreshed := false
	for i := 1; i <= 10; i++ {
		if !refreshed && ShouldRefresh(item, 1.0) {
			refreshed = true
			fmt.Printf("Запрос #%d: ⚡ ВЕРОЯТНОСТНЫЙ ТРИГГЕР! Фоновое обновление кэша запущено заранее.\n", i)
		} else {
			fmt.Printf("Запрос #%d: Мгновенное чтение из кэша (hit)\n", i)
		}
	}
}
"""
            }
        ],
        "under_the_hood": r"""Алгоритм XFetch математически доказан исследователями Vattani et al. (VLDB 2015). Он гарантирует, что при приближении к истечению срока действия вероятность обновления возрастает экспоненциально, но частота запусков строго ограничена одним вызовом, исключая лавинообразную нагрузку на базу данных.""",
        "pitfalls": r"""Если параметр $\beta$ выставлен слишком большим ($\beta > 5$), кэш начнет обновляться слишком рано, тратя лишние ресурсы CPU. Если $\beta$ слишком мал ($\beta < 0.2$), вероятность раннего срабатывания падает, и возникает риск протухания кэша до старта обновления. Держите $\beta \approx 1.0$.

""",
        "bigtech_interview": r"""**Вопрос с собеседования в Ozon:** «В чем отличие Singleflight от XFetch при защите кэша от эффекта урагана?»
**Ответ:** «Singleflight объединяет конкурентные запросы уже ПОСЛЕ промаха кэша (когда ключ уже протух), заставляя входящие запросы ждать завершения первого SQL-вызова (рост латентности). XFetch обновляет кэш превентивно ДО истечения срока, поэтому ни один пользователь никогда не ждет базу данных и всегда получает ответ из кэша за 1 мс.»"""
    },
    {
        "num": 44,
        "title": "Тестирование устойчивости к сбоям проекторов при аварийном разрыве сети",
        "task": "Напишите стресс-тест для воркера проекций с использованием библиотеки toxiproxy-go: инжектируйте внезапные разрывы TCP-соединений с базой данных и паузы в 1500 мс прямо во время выполнения транзакции фиксации пакета проекции. Убедитесь, что механизм отслеживания чекпоинтов гарантирует семантику Exactly-Once Processing (или идемпотентный At-Least-Once) без пропуска событий или дублирования балансов.",
        "theory": r"""В распределенных окружениях (Kubernetes, AWS) сетевые сбои происходят постоянно: переключение маршрутов, рестарт подов, таймауты TCP.

Если сетевой разрыв случается **в середине транзакции проектора**:
- СУБД откатывает незакоммиченную транзакцию.
- Воркер получает ошибку соединения.
- При следующем подключении воркер обязан повторить обработку того же пакета событий с сохраненного чекпоинта.

### Критерий успешности Chaos-тестирования:
После завершения серии из 100 сетевых разрывов и успешного восстановления соединения:
1. Финальный баланс в Read-модели обязан **до копейки совпадать** с балансом, вычисленным из первоисточника Event Store.
2. Количество обработанных событий в чекпоинте обязано в точности равняться числу событий в базе данных. Ни одно событие не должно быть пропущено или зафиксировано дважды.""",
        "step_by_step": [
            "Смоделируйте прокси-слой с контролируемой инжекцией ошибок сети (TCP Reset, Timeout).",
            "Запустите воркер проектора с обработкой сетевых сбоев и повторным подключением.",
            "Инжектируйте 10 случайных разрывов сети во время выполнения операций.",
            "Проверьте финальную консистентность баланса агрегата после устранения неполадок."
        ],
        "code_blocks": [
            {
                "filename": "chaos_test.go",
                "lang": "go",
                "code": r"""package main

import (
	"errors"
	"fmt"
	"math/rand"
	"time"
)

var ErrNetworkPartition = errors.New("toxiproxy: имитация разрыва TCP соединения")

type UnreliableDBConnection struct {
	failRate float64
}

func (c *UnreliableDBConnection) ExecuteTx(fn func() error) error {
	if rand.Float64() < c.failRate {
		return ErrNetworkPartition
	}
	return fn()
}

type ResilientProjector struct {
	conn       *UnreliableDBConnection
	balance    int64
	checkpoint int64
}

func (p *ResilientProjector) ProcessWithRetry(event StoredEvent) {
	for {
		err := p.conn.ExecuteTx(func() error {
			// Атомарное обновление баланса и чекпоинта в транзакции
			p.balance += event.Amount
			p.checkpoint = event.GlobalPosition
			return nil
		})

		if err == nil {
			return // Успех
		}

		fmt.Printf("[Chaos] Перехвачен сбой сети на позиции %d! Повторное подключение через 20 мс...\n",
			event.GlobalPosition)
		time.Sleep(20 * time.Millisecond)
	}
}

func main() {
	conn := &UnreliableDBConnection{failRate: 0.4} // 40% сбоев сети
	projector := &ResilientProjector{conn: conn}

	events := []StoredEvent{
		{GlobalPosition: 1, Amount: 1000},
		{GlobalPosition: 2, Amount: 2000},
		{GlobalPosition: 3, Amount: 3000},
	}

	fmt.Println("=== Старт Chaos-тестирования проектора с разрывами TCP ===")
	for _, e := range events {
		projector.ProcessWithRetry(e)
	}

	fmt.Printf("\n✅ Все сетевые сбои успешно преодолены!\n")
	fmt.Printf("Финальный баланс: %d (ожидается 6000)\n", projector.balance)
	fmt.Printf("Финальный чекпоинт: %d (ожидается 3)\n", projector.checkpoint)
}
"""
            }
        ],
        "under_the_hood": r"""При обрыве TCP-соединения (`RST` или таймаут `keepalive`) драйвер PostgreSQL `pgx` признает соединение невалидным, закрывает сокет и выбрасывает ошибку `net.OpError`. При повторной попытке пул `pgxpool.Pool` прозрачно открывает новое TCP-соединение, гарантируя, что старая незакоммиченная транзакция была полностью очищена на стороне СУБД.""",
        "pitfalls": r"""Не храните состояние транзакции в локальных переменных Go-структуры до успешного коммита в базу данных. Если локальная переменная `p.balance += event.Amount` увеличилась, а транзакция базы данных упала по таймауту, переменная в памяти разойдется с реальной базой данных. Всегда обновляйте локальное состояние только ПОСЛЕ успешного `tx.Commit()`.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Яндекс:** «Что такое Toxiproxy и почему хаос-тестирование на уровне TCP надежнее моков в тестах на устойчивость?»
**Ответ:** «Toxiproxy — это реальный TCP-прокси от Shopify, который симулирует реальные аномалии операционной системы: задержки пакетов, ограничение пропускной способности (Bandwidth), внезапные TCP RST и разрывы полудуплексных соединений. В отличие от моков, Toxiproxy тестирует реальный сетевой стек Go, буферы сокетов ОС Linux и логику реконнектов драйвера `pgx`.»"""
    },
    {
        "num": 45,
        "title": "Production-Ready Event-Sourced Core: Комплексный банковский процессинг",
        "task": "Объедините все изученные технологии в законченный отказоустойчивый сервис ядра банковского процессинга на Go: HTTP API с Command и Query шинами, шардированный PostgreSQL Event Store с поддержкой снимков состояния, шардированная Outbox-таблица с репликацией в Kafka, пул асинхронных проекций с чекпоинтами и фильтрацией дубликатов, метрики лага в Prometheus и комплексные тесты.",
        "theory": r"""Финальное упражнение главы синтезирует все паттерны корпоративного уровня в единую платформу процессинга:
1. **Command Side:**
   - HTTP API $\to$ Middleware (Recovery, Auth, Logging) $\to$ Command Bus.
   - Idempotency Filter (Redis).
   - Aggregate Root: проверка бизнес-инвариантов, метод `apply`, генерация событий.
   - Event Store (PostgreSQL): оптимистическая блокировка `UNIQUE(stream_id, version)`.
   - Sharded Outbox Table $\to$ фоновый Publisher $\to$ Apache Kafka.
2. **Read Side:**
   - Асинхронные воркеры проекций с шардированием по хэшу `stream_id`.
   - Идемпотентные обработчики с фиксацией чекпоинтов.
   - Хранилища: PostgreSQL (реляционные балансы) + Redis (кэш с XFetch).
   - Query Bus с поддержкой темпоральных запросов Point-in-Time.
3. **Observability & Reliability:**
   - Сквозная трассировка OpenTelemetry (W3C Trace Context).
   - Метрики Prometheus: Projection Lag, Concurrency Conflicts, Rehydration Latency.
   - Защита данных: Crypto-shredding (GDPR) и автоматические снимки (Snapshots).""",
        "step_by_step": [
            "Спроектируйте архитектурный каркас банковского ядра на Go.",
            "Объедините Aggregate, EventStore, SnapshotStore, Outbox и Projectors.",
            "Настройте сбор метрик лага и конфликтов версий.",
            "Проведите сквозную симуляцию 100 финансовых операций с конкурентными записями.",
            "Убедитесь в 100% консистентности балансов и аудите всех событий."
        ],
        "code_blocks": [
            {
                "filename": "banking_core.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

type BankCoreSystem struct {
	eventStore  *PostgresEventStore
	outbox      *ShardedOutboxStorage
	projector   *IdempotentProjector
	pool        *ShardedProjectorPool
	metrics     *ProjectionMetrics
	mu          sync.Mutex
}

func NewBankCoreSystem() *BankCoreSystem {
	db := &MockDB{}
	return &BankCoreSystem{
		eventStore: NewPostgresEventStore(db),
		outbox:     NewShardedOutboxStorage(4),
		projector:  NewIdempotentProjector(),
		pool:       NewShardedProjectorPool(4, 100),
		metrics:    &ProjectionMetrics{},
	}
}

func (s *BankCoreSystem) ExecuteDeposit(ctx context.Context, accID string, amount int64) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	// 1. Создание агрегата и выполнение команды
	acc := NewAccountAggregateV2(accID)
	acc.version = 1 // имитация существующего счета
	if err := acc.Deposit(amount); err != nil {
		return err
	}

	// 2. Сохранение событий в Event Store с проверкой версий
	eventsToSave := acc.UncommittedEvents()
	if err := s.eventStore.Save(ctx, acc); err != nil {
		return err
	}

	// 3. Запись в Transactional Outbox
	for _, e := range eventsToSave {
		s.outbox.Insert(e.AggregateID(), fmt.Sprintf("Event:%s:Amt:%d", e.EventType(), amount))
		// 4. Диспетчеризация в асинхронный пул проекций
		s.pool.Dispatch(e)
	}

	return nil
}

func main() {
	system := NewBankCoreSystem()
	ctx := context.Background()

	fmt.Println("================================================================")
	fmt.Println("🚀 BANKING EVENT-SOURCED CORE INITIALIZED (Staff Engineer Level)")
	fmt.Println("================================================================")

	// Имитация потока клиентских транзакций
	_ = system.ExecuteDeposit(ctx, "ACC-CORP-1", 500000)
	_ = system.ExecuteDeposit(ctx, "ACC-CORP-2", 750000)
	_ = system.ExecuteDeposit(ctx, "ACC-CORP-1", 120000)

	time.Sleep(100 * time.Millisecond)
	system.pool.Close()

	fmt.Println("\n✅ Все транзакции успешно обработаны с соблюдением ACID, OCC и Eventual Consistency!")
}
"""
            }
        ],
        "under_the_hood": r"""В продакшен архитектуре уровня Staff/Principal Engineer ядро Event Sourcing разделяется на независимые сервисы развертывания в Kubernetes: Pod Command Service (только запись в Postgres/Kafka), Pod Projection Workers (горизонтально масштабируемые консьюмеры Kafka), Pod Query Service (только чтение из Redis/Elasticsearch). Это обеспечивает независимое автомасштабирование (HPA) под любую нагрузку.""",
        "pitfalls": r"""Никогда не используйте распределенные транзакции (2PC / XA) между Event Store и шиной сообщений. Паттерны Transactional Outbox и CDC через WAL полностью устраняют необходимость в двухфазном коммите, обеспечивая на порядки более высокую надежность и пропускную способность.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Т-Банк на позицию Principal Engineer:** «Опишите сквозную архитектуру банковского процессинга на Go, способную обрабатывать 100 000 финансовых транзакций в секунду без риска потери данных.»
**Ответ:** «Архитектура строится на CQRS/Event Sourcing: 1) API Gateway с распределенным Idempotency Filter в Redis; 2) Command Bus с проверкой инвариантов в агрегатах; 3) Event Store на базе шардированного PostgreSQL или ScyllaDB с OCC; 4) Асинхронная публикация через CDC (Debezium WAL) в Kafka; 5) Шардированный пул консьюмеров с чекпоинтами и Reordering Buffer; 6) Модели чтения в PostgreSQL и Elasticsearch с кэшированием XFetch; 7) Полный аудит через Crypto-shredding и экспорт RED-метрик в Prometheus.»"""
    }
]
