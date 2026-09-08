"""
Генератор упражнений Главы 84 (Часть 1: Упражнения 1–15).
CQRS и Event Sourcing на Go.
"""

exercises = [
    {
        "num": 1,
        "title": "Разделение моделей Command и Query в памяти",
        "task": "Спроектируйте базовую структуру CQRS-приложения для банковского счёта. Создайте пакет account с разделением на commands (структуры CreateAccountCommand, DepositMoneyCommand) и queries (GetAccountBalanceQuery). Реализуйте отдельные интерфейсы CommandHandler и QueryHandler. Объясните, почему модель записи (Write Model) должна быть оптимизирована под соблюдение инвариантов бизнес-логики, а модель чтения (Read Model) — под быстрые запросы к данным без транзакционных накладных расходов.",
        "theory": r"""Архитектурный паттерн **CQRS (Command Query Responsibility Segregation)**, сформулированный Грегом Янгом и Бертраном Мейером (CQS), утверждает фундаментальный принцип: **операция изменения состояния не должна возвращать данные, а операция чтения не должна модифицировать состояние**.

### Почему единая CRUD-модель деградирует в HighLoad:
В классическом CRUD один и тот же объект (или ORM-сущность) используется и для записи, и для чтения:
1. **Конфликт требований:** Для записи критична транзакционная целостность, нормализация (3НФ), валидация бизнес-инвариантов и строгие блокировки. Для чтения нужны денормализованные плоские выборки, быстрые составные индексы, кэширование и отсутствие блокировок.
2. **Асимметрия нагрузки:** В реальных enterprise-системах (банках, e-commerce, соцсетях) соотношение операций чтения и записи часто составляет от 10:1 до 1000:1. Единая модель заставляет масштабировать тяжелую транзакционную базу данных ради тривиальных выборок.

### Разделение ответственностей:
- **Command (Команда):** Императивное намерение изменить систему (`CreateAccount`, `DepositMoney`). Команда может быть отклонена бизнес-валидацией. Команда **не возвращает доменные данные** (только статус успеха/ошибки или ID созданной сущности).
- **Query (Запрос):** Декларативный запрос на чтение данных (`GetAccountBalance`). Запрос идемпотентен, никогда не мутирует состояние и возвращает специализированный DTO, оптимизированный под конкретный экран UI или контракт API.""",
        "step_by_step": [
            "Определите структуры команд `CreateAccountCommand` и `DepositMoneyCommand` с валидацией входных полей.",
            "Определите структуру запроса `GetAccountBalanceQuery` и DTO ответа `AccountBalanceDTO`.",
            "Объявите параметризованные дженериками или интерфейсные контракты `CommandHandler[C any]` и `QueryHandler[Q any, R any]`.",
            "Реализуйте Write Model: структуру `AccountRepository` в памяти с мьютексом для защиты баланса.",
            "Реализуйте Read Model: структуру кэша балансов для молниеносного чтения.",
            "Продемонстрируйте исполнение команд и последующее чтение через раздельные хэндлеры."
        ],
        "code_blocks": [
            {
                "filename": "account_cqrs.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

// --- COMMAND MODEL (Write Side) ---

type CreateAccountCommand struct {
	AccountID string
	Owner     string
}

type DepositMoneyCommand struct {
	AccountID string
	Amount    int64 // Сумма в копейках/центах для исключения ошибок float
}

type CommandHandler[C any] interface {
	Handle(ctx context.Context, cmd C) error
}

type AccountWriteModel struct {
	ID        string
	Owner     string
	Balance   int64
	CreatedAt time.Time
}

type AccountRepository struct {
	mu       sync.RWMutex
	accounts map[string]*AccountWriteModel
}

func NewAccountRepository() *AccountRepository {
	return &AccountRepository{accounts: make(map[string]*AccountWriteModel)}
}

type AccountCommandHandler struct {
	repo      *AccountRepository
	readCache *AccountReadStorage
}

func NewAccountCommandHandler(repo *AccountRepository, readCache *AccountReadStorage) *AccountCommandHandler {
	return &AccountCommandHandler{repo: repo, readCache: readCache}
}

func (h *AccountCommandHandler) HandleCreate(ctx context.Context, cmd CreateAccountCommand) error {
	if cmd.AccountID == "" || cmd.Owner == "" {
		return errors.New("невалидные параметры команды CreateAccount")
	}

	h.repo.mu.Lock()
	defer h.repo.mu.Unlock()

	if _, exists := h.repo.accounts[cmd.AccountID]; exists {
		return fmt.Errorf("счет %s уже существует", cmd.AccountID)
	}

	acc := &AccountWriteModel{
		ID:        cmd.AccountID,
		Owner:     cmd.Owner,
		Balance:   0,
		CreatedAt: time.Now(),
	}
	h.repo.accounts[cmd.AccountID] = acc

	// Синхронное обновление Read-модели (в простейшем in-memory варианте)
	h.readCache.Update(cmd.AccountID, cmd.Owner, 0)
	return nil
}

func (h *AccountCommandHandler) HandleDeposit(ctx context.Context, cmd DepositMoneyCommand) error {
	if cmd.Amount <= 0 {
		return errors.New("сумма пополнения должна быть строго положительной")
	}

	h.repo.mu.Lock()
	defer h.repo.mu.Unlock()

	acc, exists := h.repo.accounts[cmd.AccountID]
	if !exists {
		return fmt.Errorf("счет %s не найден", cmd.AccountID)
	}

	acc.Balance += cmd.Amount
	h.readCache.Update(cmd.AccountID, acc.Owner, acc.Balance)
	return nil
}

// --- QUERY MODEL (Read Side) ---

type GetAccountBalanceQuery struct {
	AccountID string
}

type AccountBalanceDTO struct {
	AccountID string `json:"account_id"`
	Owner     string `json:"owner"`
	Balance   int64  `json:"balance"`
}

type QueryHandler[Q any, R any] interface {
	Execute(ctx context.Context, query Q) (R, error)
}

type AccountReadStorage struct {
	mu    sync.RWMutex
	cache map[string]AccountBalanceDTO
}

func NewAccountReadStorage() *AccountReadStorage {
	return &AccountReadStorage{cache: make(map[string]AccountBalanceDTO)}
}

func (s *AccountReadStorage) Update(id, owner string, balance int64) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.cache[id] = AccountBalanceDTO{
		AccountID: id,
		Owner:     owner,
		Balance:   balance,
	}
}

type AccountQueryHandler struct {
	storage *AccountReadStorage
}

func NewAccountQueryHandler(storage *AccountReadStorage) *AccountQueryHandler {
	return &AccountQueryHandler{storage: storage}
}

func (h *AccountQueryHandler) Execute(ctx context.Context, q GetAccountBalanceQuery) (AccountBalanceDTO, error) {
	h.storage.mu.RLock()
	defer h.storage.mu.RUnlock()

	dto, exists := h.storage.cache[q.AccountID]
	if !exists {
		return AccountBalanceDTO{}, fmt.Errorf("read-model: счет %s не найден", q.AccountID)
	}
	return dto, nil
}

func main() {
	ctx := context.Background()
	repo := NewAccountRepository()
	readStorage := NewAccountReadStorage()

	cmdHandler := NewAccountCommandHandler(repo, readStorage)
	queryHandler := NewAccountQueryHandler(readStorage)

	// Выполнение команд
	_ = cmdHandler.HandleCreate(ctx, CreateAccountCommand{AccountID: "ACC-101", Owner: "Иван Иванов"})
	_ = cmdHandler.HandleDeposit(ctx, DepositMoneyCommand{AccountID: "ACC-101", Amount: 50000})

	// Выполнение запроса
	dto, err := queryHandler.Execute(ctx, GetAccountBalanceQuery{AccountID: "ACC-101"})
	if err != nil {
		panic(err)
	}
	fmt.Printf("Query Result: Владелец=%s, Баланс=%d руб.\n", dto.Owner, dto.Balance/100)
}
"""
            }
        ],
        "under_the_hood": r"""На уровне структурной организации приложения разделение Write и Read моделей устраняет contention на уровне блокировок. В Write-модели синхронизация выполняется через эксклюзивные блокировки мьютекса или транзакции СУБД с высоким уровнем изоляции (`SERIALIZABLE` / `REPEATABLE READ`), защищая инварианты. В Read-модели используются разделяемые блокировки `sync.RWMutex.RLock()` или `SELECT` с `READ COMMITTED`, что позволяет масштабировать чтение линейно по числу ядер CPU без деградации времени ответа.""",
        "pitfalls": r"""Главная архитектурная ловушка новичков в CQRS — попытка вернуть сущность из обработчика команды: `Handle(cmd) (*Account, error)`. Это нарушает чистоту контракта CQS. Если клиент немедленно требует данные после записи, он должен либо сформировать локальное оптимистичное состояние, либо выполнить отдельный Query, учитывая возможную задержку репликации (Eventual Consistency).""",
        "bigtech_interview": r"""**Вопрос с собеседования в Яндекс:** «Почему в высоконагруженных системах разделяют базу данных для записи (Master) и базы для чтения (Read Replicas/Elasticsearch), и какую проблему CQRS решает на прикладном уровне?»
**Ответ:** «CQRS на уровне кода снимает противоречие между нормализацией для транзакций и денормализацией для аналитики. Модель записи работает с узкими агрегатами и гарантирует ACID-инварианты. Модели чтения хранят готовые плоские проекции, оптимизированные под API/UI без необходимости дорогостоящих JOIN по десяткам таблиц на каждый HTTP-запрос.»"""
    },
    {
        "num": 2,
        "title": "Проектирование неизменяемого Domain Event",
        "task": "Определите обобщенный интерфейс DomainEvent с методами EventID() string, AggregateID() string, OccurredAt() time.Time и Version() int. Реализуйте конкретные события предметной области: AccountCreatedEvent и MoneyDepositedEvent. Объясните, почему доменные события в Event Sourcing обязаны быть строго неизменяемыми (immutable) и именоваться в прошедшем времени.",
        "theory": r"""В концепции **Event Sourcing** центральным первоисточником истины (Single Source of Truth) является не текущее состояние базы данных (снимок), а **упорядоченная последовательность фактов, произошедших в прошлом**.

### Принципы Domain Events:
1. **Именование в прошедшем времени:** Событие констатирует факт, который **уже произошел**: `AccountCreated`, `MoneyDeposited`, `OrderCancelled`. Мы не можем отменить то, что произошло в прошлом.
2. **Неизменяемость (Immutability):** После того как событие записано в хранилище (Event Store), оно никогда не редактируется оператором `UPDATE` и не удаляется оператором `DELETE`. Любые исправления фиксируются созданием **новых компенсирующих событий** (`TransactionReversed`).
3. **Самодостаточность (Self-Contained):** Событие содержит все данные, необходимые для изменения состояния агрегата и информирования внешних подписчиков, а также метаданные (ID события, временная метка, версия).""",
        "step_by_step": [
            "Объявите базовый интерфейс `DomainEvent` с обязательными методами метаданных.",
            "Создайте структуру `BaseEvent` для повторного использования полей метаданных.",
            "Определите доменные события `AccountCreatedEvent` и `MoneyDepositedEvent` с внедрением `BaseEvent`.",
            "Реализуйте конструкторы событий, гарантирующие генерацию уникального UUID и точного времени `time.Now().UTC()`.",
            "Напишите проверку неизменяемости: структуры событий передаются по значению или содержат неэкспортируемые поля."
        ],
        "code_blocks": [
            {
                "filename": "domain_event.go",
                "lang": "go",
                "code": r"""package main

import (
	"crypto/rand"
	"fmt"
	"time"
)

type DomainEvent interface {
	EventID() string
	AggregateID() string
	EventType() string
	OccurredAt() time.Time
	Version() int64
}

type BaseEvent struct {
	id          string
	aggregateID string
	eventType   string
	occurredAt  time.Time
	version     int64
}

func (e BaseEvent) EventID() string      { return e.id }
func (e BaseEvent) AggregateID() string  { return e.aggregateID }
func (e BaseEvent) EventType() string    { return e.eventType }
func (e BaseEvent) OccurredAt() time.Time { return e.occurredAt }
func (e BaseEvent) Version() int64       { return e.version }

func newUUID() string {
	b := make([]byte, 16)
	_, _ = rand.Read(b)
	return fmt.Sprintf("%x-%x-%x-%x-%x", b[0:4], b[4:6], b[6:8], b[8:10], b[10:])
}

// AccountCreatedEvent фиксирует создание счета
type AccountCreatedEvent struct {
	BaseEvent
	OwnerName string
	Currency  string
}

func NewAccountCreatedEvent(accID string, version int64, owner, currency string) AccountCreatedEvent {
	return AccountCreatedEvent{
		BaseEvent: BaseEvent{
			id:          newUUID(),
			aggregateID: accID,
			eventType:   "AccountCreated",
			occurredAt:  time.Now().UTC(),
			version:     version,
		},
		OwnerName: owner,
		Currency:  currency,
	}
}

// MoneyDepositedEvent фиксирует поступление средств
type MoneyDepositedEvent struct {
	BaseEvent
	Amount int64
	Reason string
}

func NewMoneyDepositedEvent(accID string, version int64, amount int64, reason string) MoneyDepositedEvent {
	return MoneyDepositedEvent{
		BaseEvent: BaseEvent{
			id:          newUUID(),
			aggregateID: accID,
			eventType:   "MoneyDeposited",
			occurredAt:  time.Now().UTC(),
			version:     version,
		},
		Amount: amount,
		Reason: reason,
	}
}

func PrintEvent(e DomainEvent) {
	fmt.Printf("[%s] Event=%s, AggID=%s, Version=%d, Time=%s\n",
		e.EventID()[:8], e.EventType(), e.AggregateID(), e.Version(), e.OccurredAt().Format(time.RFC3339Nano))
}

func main() {
	e1 := NewAccountCreatedEvent("acc-123", 1, "Алексей Смирнов", "RUB")
	e2 := NewMoneyDepositedEvent("acc-123", 2, 150000, "Зарплатный перевод")

	PrintEvent(e1)
	PrintEvent(e2)
}
"""
            }
        ],
        "under_the_hood": r"""Использование приватных полей (`id`, `occurredAt`, `version`) с публичными геттерами в `BaseEvent` делает структуру иммутабельной для внешних пакетов. Компилятор Go при передаче структуры по значению `func (e BaseEvent)` выполняет побайтовое копирование 40–64 байт в стек или регистры CPU, гарантируя, что ни одна горутина не сможет модифицировать поля исходного события в памяти.""",
        "pitfalls": r"""Никогда не используйте локальное системное время `time.Now()` без вызова `.UTC()`. Если микросервисы кластера развернуты в разных часовых поясах или на серверах с рассинхронизированными таймзонами, события в истории потеряют монотонный порядок при отображении и аудите. Всегда используйте строго `time.Now().UTC()`.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Ozon:** «Можно ли изменять тело исторического события в Event Store, если в нем обнаружена ошибка в данных?»
**Ответ:** «Категорически нет. В Event Sourcing хранилище событий является неизменяемым журналом аудита (Append-Only Log). Изменение исторического события разрушает криптографическую целостность, ломает детерминизм повторного воспроизведения (Replay) и искажает состояние всех асинхронных проекций, построенных на базе этого события. Ошибки исправляются исключительно выпуском компенсирующего события (Compensating Event).»"""
    },
    {
        "num": 3,
        "title": "Агрегат (Aggregate Root) и инкапсуляция инвариантов",
        "task": "Создайте структуру AccountAggregate, содержащую идентификатор, текущий баланс, версию агрегата и срез неподтвержденных событий uncommittedEvents []DomainEvent. Реализуйте метод NewAccountAggregate(id string) *AccountAggregate и методы доступа к неподтвержденным событиям (UncommittedEvents(), ClearUncommitted()). Объясните роль агрегата как границы транзакционной целостности в Domain-Driven Design.",
        "theory": r"""В Domain-Driven Design (DDD) **Агрегат (Aggregate)** — это кластер связанных доменных объектов (сущностей и объектов-значений), рассматриваемых как единое целое с точки зрения изменения данных.

### Корень агрегата (Aggregate Root):
1. **Единственная точка входа:** Внешний мир (командные обработчики) не имеет прямого доступа к внутренним полям агрегата. Любые изменения возможны только через вызов публичных методов корня агрегата (`Deposit()`, `Withdraw()`).
2. **Граница транзакционной согласованности:** Вся бизнес-логика и проверка инвариантов (например, «баланс не может опускаться ниже нуля») инкапсулированы внутри агрегата. Если операция нарушает инвариант, агрегат возвращает ошибку и **не порождает событий**.
3. **Неподтвержденные события (Uncommitted Events):** При успешном выполнении бизнес-метода агрегат формирует новое событие, сохраняет его в локальный буфер `uncommittedEvents` и ожидает, когда репозиторий атомарно запишет эти события в Event Store.""",
        "step_by_step": [
            "Определите структуру `AccountAggregate` с полями `id`, `balance`, `version` и `uncommitted []DomainEvent`.",
            "Реализуйте базовые методы управления буфером: `RecordEvent()`, `UncommittedEvents()`, `ClearUncommitted()`.",
            "Реализуйте проверку бизнес-инварианта в методе `Withdraw(amount int64)`: отказ при нехватке средств.",
            "Реализуйте метод `Deposit(amount int64)` с генерацией соответствующего события.",
            "Продемонстрируйте накопление событий и очистку буфера после имитации сохранения."
        ],
        "code_blocks": [
            {
                "filename": "aggregate_root.go",
                "lang": "go",
                "code": r"""package main

import (
	"errors"
	"fmt"
	"time"
)

type AccountAggregate struct {
	id          string
	balance     int64
	version     int64
	uncommitted []DomainEvent
}

func NewAccountAggregate(id string) *AccountAggregate {
	return &AccountAggregate{
		id:          id,
		balance:     0,
		version:     0,
		uncommitted: make([]DomainEvent, 0),
	}
}

func (a *AccountAggregate) ID() string      { return a.id }
func (a *AccountAggregate) Balance() int64  { return a.balance }
func (a *AccountAggregate) Version() int64  { return a.version }

func (a *AccountAggregate) UncommittedEvents() []DomainEvent {
	eventsCopy := make([]DomainEvent, len(a.uncommitted))
	copy(eventsCopy, a.uncommitted)
	return eventsCopy
}

func (a *AccountAggregate) ClearUncommitted() {
	a.uncommitted = a.uncommitted[:0]
}

func (a *AccountAggregate) record(event DomainEvent) {
	a.uncommitted = append(a.uncommitted, event)
}

// Deposit реализует пополнение баланса
func (a *AccountAggregate) Deposit(amount int64, reason string) error {
	if amount <= 0 {
		return errors.New("сумма пополнения должна быть больше нуля")
	}

	newVersion := a.version + 1
	event := NewMoneyDepositedEvent(a.id, newVersion, amount, reason)

	// Мутация внутреннего состояния
	a.balance += amount
	a.version = newVersion
	a.record(event)
	return nil
}

// Withdraw реализует списание с контролем инварианта платежеспособности
func (a *AccountAggregate) Withdraw(amount int64, reason string) error {
	if amount <= 0 {
		return errors.New("сумма списания должна быть больше нуля")
	}
	// Проверка бизнес-инварианта агрегата
	if a.balance < amount {
		return fmt.Errorf("недостаточно средств: текущий баланс %d, запрошено %d", a.balance, amount)
	}

	newVersion := a.version + 1
	event := NewMoneyDepositedEvent(a.id, newVersion, -amount, reason)

	a.balance -= amount
	a.version = newVersion
	a.record(event)
	return nil
}

func main() {
	acc := NewAccountAggregate("ACC-777")
	_ = acc.Deposit(1000, "Входящий перевод")

	err := acc.Withdraw(1500, "Покупка товара")
	if err != nil {
		fmt.Printf("Бизнес-инвариант защищен: %v\n", err)
	}

	_ = acc.Withdraw(400, "Оплата связи")

	fmt.Printf("Состояние агрегата: ID=%s, Баланс=%d, Версия=%d\n", acc.ID(), acc.Balance(), acc.Version())
	fmt.Printf("Количество неподтвержденных событий: %d\n", len(acc.UncommittedEvents()))

	// Имитация успешной записи в EventStore
	acc.ClearUncommitted()
	fmt.Printf("После коммита буфер очищен: %d событий\n", len(acc.UncommittedEvents()))
}
"""
            }
        ],
        "under_the_hood": r"""В памяти агрегат представляет собой компактную Go-структуру. Срез `uncommitted` аллоцируется с capacity с запасом, минимизируя аллокации в куче при частых мутациях. Метод `UncommittedEvents()` возвращает поверхностную копию среза через `copy()`, что предотвращает случайную модификацию внутреннего буфера агрегата сторонними горутинами.""",
        "pitfalls": r"""Критическая ошибка проектирования — мутировать состояние агрегата в обход проверки инвариантов или вызывать внутри методов агрегата внешние сетевые зависимости (HTTP-клиент, SQL-запросы). Агрегат в DDD обязан быть чистой доменной моделью (Pure Domain Model), оперирующей только переданными аргументами и собственным состоянием.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Авито:** «Может ли одна транзакция изменять состояние двух разных агрегатов в архитектуре Event Sourcing?»
**Ответ:** «В каноническом DDD и Event Sourcing — категорически нет. Агрегат является фундаментальной границей транзакционной целостности. Каждая команда и транзакция обязана изменять состояние ровно одного агрегата (`StreamID`). Если бизнес-процесс затрагивает несколько агрегатов (например, перевод денег с одного счета на другой), используется паттерн распределенной Саги (Saga / Process Manager) или хореография событий с гарантией Eventual Consistency.»"""
    },
    {
        "num": 4,
        "title": "Метод Apply и разделение валидации и мутации",
        "task": "Реализуйте в AccountAggregate разделение выполнения команды и мутации состояния: бизнес-метод Deposit(amount decimal.Decimal) error проверяет валидность входящих данных и генерирует событие, а внутренний метод apply(event DomainEvent) изменяет поле баланса и инкрементирует версию агрегата. Объясните, почему метод apply не должен содержать никакой логики проверок и никогда не должен возвращать ошибку.",
        "theory": r"""В классическом Event Sourcing выполнение бизнес-логики строго разделяется на две непересекающиеся фазы:

1. **Фаза валидации и генерации события (Command Handling Phase):**
   - Вызывается публичный доменный метод (например, `Withdraw()`).
   - Проверяются аргументы и инварианты текущего состояния агрегата.
   - В случае ошибки метод возвращает ошибку, мутации не происходит.
   - В случае успеха конструируется новое событие `DomainEvent`.

2. **Фаза мутации состояния (Event Application Phase):**
   - Вызывается внутренний метод `apply(event DomainEvent)`.
   - Метод сопоставляет тип события через `switch` и напрямую изменяет поля структуры агрегата.
   - Метод `apply` **никогда не возвращает ошибку** и **не содержит бизнес-валидаций**!

### Почему `apply` не должен содержать проверок:
Когда агрегат загружается из базы данных, его состояние восстанавливается (воспроизводится) из сотен исторических событий, произошедших дни или годы назад. Если бы в методе `apply` была валидация (например, проверка срока действия договора), изменение бизнес-правил в будущем сделало бы невозможным прочтение старых исторических событий, заблокировав работу всей системы.""",
        "step_by_step": [
            "Создайте метод `apply(event DomainEvent)` с диспетчеризацией по типу события.",
            "Убедитесь, что сигнатура `apply` не возвращает ошибку (`func (a *AccountAggregate) apply(e DomainEvent)`).",
            "Реализуйте метод `RaiseEvent(e DomainEvent)`, который вызывает `apply(e)` и помещает событие в `uncommittedEvents`.",
            "Перепишите бизнес-методы `Create()`, `Deposit()`, `Withdraw()` так, чтобы они только валидировали данные и вызывали `RaiseEvent`.",
            "Продемонстрируйте изменение полей агрегата строго через `apply`."
        ],
        "code_blocks": [
            {
                "filename": "apply_pattern.go",
                "lang": "go",
                "code": r"""package main

import (
	"errors"
	"fmt"
)

type AccountAggregateV2 struct {
	id          string
	owner       string
	balance     int64
	version     int64
	uncommitted []DomainEvent
}

func NewAccountAggregateV2(id string) *AccountAggregateV2 {
	return &AccountAggregateV2{id: id}
}

// apply - единственный метод, имеющий право мутировать поля агрегата!
// Он НЕ содержит валидаций и НЕ возвращает ошибок.
func (a *AccountAggregateV2) apply(event DomainEvent) {
	switch e := event.(type) {
	case AccountCreatedEvent:
		a.id = e.AggregateID()
		a.owner = e.OwnerName
		a.balance = 0
		a.version = e.Version()

	case MoneyDepositedEvent:
		a.balance += e.Amount
		a.version = e.Version()

	default:
		// Игнорируем неизвестные события для обеспечения прямой совместимости
	}
}

// RaiseEvent применяет событие к себе и буферизирует его
func (a *AccountAggregateV2) RaiseEvent(event DomainEvent) {
	a.apply(event)
	a.uncommitted = append(a.uncommitted, event)
}

// Бизнес-метод Create: проверяет инварианты и создает событие
func (a *AccountAggregateV2) Create(owner string) error {
	if a.version > 0 {
		return errors.New("счет уже был инициализирован ранее")
	}
	if owner == "" {
		return errors.New("владелец счета не может быть пустым")
	}

	event := NewAccountCreatedEvent(a.id, 1, owner, "RUB")
	a.RaiseEvent(event)
	return nil
}

// Бизнес-метод Deposit
func (a *AccountAggregateV2) Deposit(amount int64) error {
	if a.version == 0 {
		return errors.New("счет не существует")
	}
	if amount <= 0 {
		return errors.New("сумма пополнения должна быть строго положительной")
	}

	event := NewMoneyDepositedEvent(a.id, a.version+1, amount, "Пополнение")
	a.RaiseEvent(event)
	return nil
}

func main() {
	acc := NewAccountAggregateV2("ACC-999")
	_ = acc.Create("Мария Павлова")
	_ = acc.Deposit(50000)

	fmt.Printf("Агрегат: ID=%s, Владелец=%s, Баланс=%d, Версия=%d\n",
		acc.id, acc.owner, acc.balance, acc.version)
	fmt.Printf("Сгенерировано событий: %d\n", len(acc.uncommitted))
}
"""
            }
        ],
        "under_the_hood": r"""В Go type switch `switch e := event.(type)` использует проверку RTTI (интерфейсную структуру `iface`). Компилятор генерирует эффективную таблицу переходов, сравнивающую `_type` интерфейса со статическими типами событий, обеспечивая время диспетчеризации $O(1)$ без накладных расходов рефлексии `reflect`.""",
        "pitfalls": r"""Никогда не изменяйте поля агрегата напрямую внутри бизнес-метода до вызова `apply` (например: `a.balance += amount; a.RaiseEvent(...)`). Если состояние мутируется до `apply`, то при регидрации агрегата из истории метод `apply` будет вызван повторно поверх исторических событий, что приведет к задвоению данных! Все мутации — только внутри `apply`.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Т-Банк:** «Что произойдет, если в метод `apply` добавить валидацию, запрещающую отрицательный баланс, а спустя год в банке введут овердрафт?»
**Ответ:** «Если в `apply` была зашита старая проверка, то при попытке перезагрузить агрегат с овердрафтом из базы данных метод упадет с ошибкой. Исторические события не смогут быть применены, и счет окажется недоступным. Валидация принадлежит исключительно методам обработки команд, а `apply` обязан беспрекословно воспроизводить свершившиеся исторические факты.»"""
    },
    {
        "num": 5,
        "title": "Регидрация агрегата (Rehydrate / Load from History)",
        "task": "Реализуйте функцию RehydrateAccount(id string, history []DomainEvent) (*AccountAggregate, error). Функция инициализирует пустой агрегат и последовательно вызывает метод apply для каждого исторического события, восстанавливая актуальное состояние агрегата на текущий момент. Убедитесь, что после регидрации список uncommittedEvents пуст, а версия агрегата равна номеру последнего примененного события.",
        "theory": r"""**Регидрация (Rehydration / Replaying)** — это процесс восстановления актуального состояния агрегата в оперативной памяти путем последовательного проигрывания всех исторических событий из его потока (Event Stream).

### Алгоритм регидрации:
1. Создается чистый экземпляр агрегата с заданным `AggregateID` и нулевыми начальными значениями (`balance = 0`, `version = 0`).
2. Для каждого события из переданной истории вызывается внутренний метод `apply(event)`.
3. Метод `apply` восстанавливает поля агрегата и устанавливает `version = event.Version()`.
4. Список `uncommittedEvents` **остается абсолютно пустым**, так как эти события уже были зафиксированы в Event Store в прошлом.
5. Проверяется строгая монотонность версий ($V_{i} = V_{i-1} + 1$). Пропуск версии или нарушение порядка сигнализируют о повреждении данных.""",
        "step_by_step": [
            "Определите сигнатуру функции `RehydrateAccount(id string, history []DomainEvent) (*AccountAggregateV2, error)`.",
            "Проверьте историю на пустоту: если событий нет, возвращается ошибка отсутствия агрегата.",
            "В цикле вызовите метод `apply` для каждого события.",
            "Проверьте инвариант монотонности версий в цикле.",
            "Убедитесь, что буфер `uncommitted` пуст, и верните готовый к работе агрегат."
        ],
        "code_blocks": [
            {
                "filename": "rehydrate.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
)

// RehydrateAccount восстанавливает агрегат из упорядоченного среза исторических событий
func RehydrateAccount(id string, history []DomainEvent) (*AccountAggregateV2, error) {
	if len(history) == 0 {
		return nil, fmt.Errorf("агрегат %s не найден: история событий пуста", id)
	}

	acc := NewAccountAggregateV2(id)

	var expectedVersion int64 = 1
	for _, event := range history {
		if event.AggregateID() != id {
			return nil, fmt.Errorf("событие %s принадлежит другому агрегату %s", event.EventID(), event.AggregateID())
		}
		if event.Version() != expectedVersion {
			return nil, fmt.Errorf("нарушение последовательности версий: ожидалась %d, получена %d",
				expectedVersion, event.Version())
		}

		// Применение события без занесения в uncommitted буфер!
		acc.apply(event)
		expectedVersion++
	}

	return acc, nil
}

func main() {
	accID := "ACC-555"

	// Имитация исторической ленты событий из БД
	history := []DomainEvent{
		NewAccountCreatedEvent(accID, 1, "Елена Васильева", "RUB"),
		NewMoneyDepositedEvent(accID, 2, 100000, "Внесение через банкомат"),
		NewMoneyDepositedEvent(accID, 3, -25000, "Снятие наличных"),
		NewMoneyDepositedEvent(accID, 4, 15000, "Кэшбэк"),
	}

	acc, err := RehydrateAccount(accID, history)
	if err != nil {
		panic(err)
	}

	fmt.Printf("✅ Агрегат успешно регидрирован!\n")
	fmt.Printf("ID: %s | Владелец: %s | Баланс: %d | Версия: %d\n",
		acc.id, acc.owner, acc.balance, acc.version)
	fmt.Printf("Неподтвержденных событий в агрегате: %d (должно быть 0)\n", len(acc.uncommitted))

	// Агрегат готов принимать новые команды
	_ = acc.Deposit(5000)
	fmt.Printf("После новой команды uncommitted=%d, версия=%d\n",
		len(acc.uncommitted), acc.version)
}
"""
            }
        ],
        "under_the_hood": r"""При регидрации агрегата в Go рантайм выполняет последовательное обращение по срезу указателей интерфейсов. Так как события в истории отсортированы по `version`, обращения к кэш-линиям CPU происходят линейно (Hardware Prefetching), что дает колоссальную скорость регидрации — сотни тысяч событий в секунду на одно ядро процессора.""",
        "pitfalls": r"""Если при регидрации случайно вызвать публичный метод `RaiseEvent(event)` вместо приватного `apply(event)`, агрегат не только восстановит состояние, но и продублирует все старые исторические события в буфер `uncommitted`. При следующем сохранении репозиторий попытается повторно записать их в Event Store, вызвав конфликт уникального ключа.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Wildberries:** «Что делать, если в агрегате накопилось 500 000 событий, и регидрация при каждом запросе начинает занимать 200 мс?»
**Ответ:** «Использовать паттерн Snapshotting (Снимки состояния). Каждые N событий (например, каждые 100 или 500) сохраняется сериализованное состояние агрегата в таблицу снимков. При регидрации загружается последний снимок, а из Event Store дочитываются только события с `version > snapshot.version`. Это возвращает сложность регидрации к $O(1)$.»"""
    },
    {
        "num": 6,
        "title": "Схема таблицы Event Store в PostgreSQL",
        "task": "Спроектируйте и напишите SQL DDL для таблицы events в PostgreSQL. Таблица должна содержать столбцы: event_id UUID PRIMARY KEY, stream_id VARCHAR(64) NOT NULL, stream_type VARCHAR(64) NOT NULL, version BIGINT NOT NULL, event_type VARCHAR(128) NOT NULL, payload JSONB NOT NULL, metadata JSONB, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(). Создайте уникальный составной индекс UNIQUE (stream_id, version) и объясните его критическую роль для гарантии целостности.",
        "theory": r"""**Event Store** — это специализированное Append-Only хранилище данных, оптимизированное под запись и чтение потоков событий (Event Streams).

### Архитектура таблицы событий в PostgreSQL:
1. `stream_id` (идентификатор агрегата): определяет поток событий конкретной бизнес-сущности (например, UUID банковского счета).
2. `version` (монотонный номер версии): строго инкрементируемое целое число ($1, 2, 3 \dots$).
3. `payload JSONB`: бинарный JSON с полезной нагрузкой доменного события.
4. `metadata JSONB`: метаданные инфраструктуры (ID корреляции, TraceID OpenTelemetry, IP-клиента, User-Agent).
5. `global_position BIGSERIAL`: глобальный сквозной монотонный счетчик для вычитки событий асинхронными проекциями.

### Уникальный индекс `UNIQUE (stream_id, version)`:
Это краеугольный камень целостности в Event Sourcing. База данных на физическом уровне B-Tree индекса гарантирует, что два конкурентных процесса не смогут записать событие с одинаковым номером версии для одного и того же агрегата.""",
        "step_by_step": [
            "Напишите DDL создания таблицы `events` с необходимыми типами данных.",
            "Добавьте колонку `global_position BIGSERIAL` для глобального упорядочивания.",
            "Создайте уникальный составной индекс `UNIQUE (stream_id, version)`.",
            "Создайте индекс по `(stream_id, version ASC)` для быстрого чтения истории агрегата.",
            "Создайте индекс по `global_position` для вычитки событий воркерами проекций."
        ],
        "code_blocks": [
            {
                "filename": "schema.sql",
                "lang": "sql",
                "code": r"""-- DDL схема промышленного Event Store на PostgreSQL
CREATE TABLE IF NOT EXISTS event_streams (
    stream_id VARCHAR(64) PRIMARY KEY,
    stream_type VARCHAR(64) NOT NULL,
    current_version BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
    global_position BIGSERIAL PRIMARY KEY,
    event_id UUID NOT NULL UNIQUE,
    stream_id VARCHAR(64) NOT NULL,
    stream_type VARCHAR(64) NOT NULL,
    version BIGINT NOT NULL,
    event_type VARCHAR(128) NOT NULL,
    payload JSONB NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- ГАРАНТИЯ ЦЕЛОСТНОСТИ И ОПТИМИСТИЧЕСКОЙ БЛОКИРОВКИ:
    CONSTRAINT uq_stream_version UNIQUE (stream_id, version)
);

-- Индекс для мгновенной вычитки истории конкретного агрегата при регидрации
CREATE INDEX IF NOT EXISTS idx_events_stream_read 
ON events (stream_id, version ASC);

-- Индекс для проекторов (Outbox/CDC/Read Models), читающих события пачками
CREATE INDEX IF NOT EXISTS idx_events_global_pos 
ON events (global_position);
"""
            },
            {
                "filename": "migration_test.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
)

func main() {
	fmt.Println("Схема PostgreSQL Event Store спроектирована:")
	fmt.Println("- UNIQUE(stream_id, version) предотвращает гонки записи")
	fmt.Println("- global_position BIGSERIAL обеспечивает At-Least-Once вычитку проекциями")
}
"""
            }
        ],
        "under_the_hood": r"""В PostgreSQL B-Tree уникальный индекс `uq_stream_version` блокирует попытки конкурентной вставки на уровне блокировок страниц индекса (`lwlock`). Если две транзакции одновременно выполняют `INSERT` с одинаковым `(stream_id, version)`, вторая транзакция ждет завершения первой и при коммите первой немедленно завершается с кодом ошибки `23505 (unique_violation)`.""",
        "pitfalls": r"""Никогда не используйте `global_position` как номер версии агрегата. Глобальная позиция содержит пропуски (gaps) при откате отмененных транзакций PostgreSQL. Версия агрегата `version` обязана формироваться на уровне доменной модели как непрерывная монотонная последовательность $1, 2, 3 \dots$ без пропусков.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Lamoda:** «Почему для Event Store в PostgreSQL рекомендуется тип `JSONB`, а не обычный `TEXT` или `JSON`?»
**Ответ:** «`JSONB` хранится в декомпозированном бинарном формате. Он парсится один раз при вставке и не требует повторного синтаксического анализа при чтении. Кроме того, `JSONB` поддерживает индексацию GIN по атрибутам событий и устраняет незначимые пробелы, экономя дисковое пространство и объем буферного пула RAM.»"""
    },
    {
        "num": 7,
        "title": "Оптимистическая блокировка версий (Optimistic Concurrency Control)",
        "task": "Напишите репозиторий PostgresEventStore, реализующий метод Save(ctx context.Context, aggregate Aggregate) error. Метод должен открывать транзакцию pgx, проверять соответствие текущей версии в базе ожидаемой версии (expectedVersion), сохранять накопленные события с инкрементом версий и коммитить транзакцию. Продемонстрируйте, как база данных отклоняет дублирующуюся версию с ошибкой нарушения уникального индекса при конкурентной записи.",
        "theory": r"""В высоконагруженных распределенных системах пессимистические блокировки (`SELECT ... FOR UPDATE`) вызывают длительные задержки и взаимные блокировки (Deadlocks). В Event Sourcing стандартом является **оптимистическая блокировка версий (Optimistic Concurrency Control, OCC)**.

### Механика OCC:
1. Обработчик команды загружает агрегат с текущей версией $V_{current} = 5$. Значение 5 запоминается как `expectedVersion`.
2. Агрегат выполняет бизнес-логику и порождает новое событие с версией $V = 6$.
3. При сохранении в СУБД открывается транзакция:
   - Выполняется вставка `INSERT INTO events (stream_id, version, ...) VALUES ('acc-1', 6, ...)`.
4. Если параллельная горутина уже успела записать версию 6, СУБД отклоняет запрос с ошибкой `unique_violation`.
5. Текущая транзакция откатывается, доказывая, что состояние агрегата изменилось параллельно.""",
        "step_by_step": [
            "Создайте кастомную ошибку `ErrConcurrencyConflict`.",
            "Напишите метод `Save(ctx, aggregate)` с использованием транзакции.",
            "Выполните вставку всех неподтвержденных событий агрегата в цикле.",
            "Перехватите ошибку нарушения уникальности PostgreSQL (код `23505`) и преобразуйте в `ErrConcurrencyConflict`.",
            "Продемонстрируйте сценарий конфликта параллельных записей."
        ],
        "code_blocks": [
            {
                "filename": "event_store_occ.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"sync"
)

var ErrConcurrencyConflict = errors.New("конфликт оптимистической блокировки: версия устарела")

type EventRecord struct {
	StreamID  string
	Version   int64
	EventType string
	Payload   []byte
}

type MockDB struct {
	mu     sync.Mutex
	events []EventRecord
}

func (db *MockDB) Insert(rec EventRecord) error {
	db.mu.Lock()
	defer db.mu.Unlock()

	// Имитация уникального индекса UNIQUE(StreamID, Version)
	for _, e := range db.events {
		if e.StreamID == rec.StreamID && e.Version == rec.Version {
			return ErrConcurrencyConflict
		}
	}
	db.events = append(db.events, rec)
	return nil
}

type PostgresEventStore struct {
	db *MockDB
}

func NewPostgresEventStore(db *MockDB) *PostgresEventStore {
	return &PostgresEventStore{db: db}
}

func (es *PostgresEventStore) Save(ctx context.Context, acc *AccountAggregateV2) error {
	events := acc.uncommitted
	if len(events) == 0 {
		return nil
	}

	for _, e := range events {
		payload, err := json.Marshal(e)
		if err != nil {
			return fmt.Errorf("ошибка сериализации события: %w", err)
		}

		rec := EventRecord{
			StreamID:  e.AggregateID(),
			Version:   e.Version(),
			EventType: e.EventType(),
			Payload:   payload,
		}

		if err := es.db.Insert(rec); err != nil {
			if errors.Is(err, ErrConcurrencyConflict) {
				return fmt.Errorf("%w: агрегат %s уже имеет версию %d",
					ErrConcurrencyConflict, e.AggregateID(), e.Version())
			}
			return err
		}
	}

	acc.uncommitted = acc.uncommitted[:0]
	return nil
}

func main() {
	db := &MockDB{}
	store := NewPostgresEventStore(db)
	ctx := context.Background()

	// 1. Поток А создает счет
	accA := NewAccountAggregateV2("ACC-100")
	_ = accA.Create("Сергей")
	if err := store.Save(ctx, accA); err != nil {
		panic(err)
	}
	fmt.Println("Поток А успешно записал версию 1")

	// 2. Имитация параллельного чтения потоком B и потоком C той же версии 1
	accB := NewAccountAggregateV2("ACC-100")
	accB.version = 1
	_ = accB.Deposit(100) // Версия 2

	accC := NewAccountAggregateV2("ACC-100")
	accC.version = 1
	_ = accC.Deposit(200) // Тоже пытается записать Версию 2!

	// Поток B успевает первым
	if err := store.Save(ctx, accB); err != nil {
		panic(err)
	}
	fmt.Println("Поток B успешно записал версию 2")

	// Поток C пробует записать версию 2 и получает конфликт!
	err := store.Save(ctx, accC)
	if errors.Is(err, ErrConcurrencyConflict) {
		fmt.Printf("✅ Перехвачен ожидаемый конфликт: %v\n", err)
	} else {
		panic("Ожидался конфликт версий!")
	}
}
"""
            }
        ],
        "under_the_hood": r"""В реальном драйвере `jackc/pgx/v5` ошибка нарушения ограничения целостности определяется проверкой структуры `*pgconn.PgError` с полем `Code == "23505"`. Если имя ограничения совпадает с `uq_stream_version`, репозиторий безошибочно распознает гонку версий и возвращает доменную ошибку `ErrConcurrencyConflict`.""",
        "pitfalls": r"""Не пытайтесь выполнять `SELECT MAX(version)` перед вставкой в надежде проверить версию в приложении без использования уникального индекса. Между операцией `SELECT` и операцией `INSERT` возникает окно гонки (Time-of-Check to Time-of-Use), из-за которого две горутины прочитают одинаковую максимальную версию и испортят историю событий.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Касперский:** «Чем отличается Optimistic Concurrency Control от Pessimistic Locking в терминах пропускной способности и задержки (Latency)?»
**Ответ:** «Пессимистическая блокировка захватывает строку или ресурс на все время выполнения бизнес-логики, снижая конкурентность и приводя к ожиданию очередей потоков. Оптимистическая блокировка исходит из предположения, что конфликты редки: чтение и валидация происходят параллельно без блокировок, а проверка выполняется за микросекунды в момент коммита. При высоком contention OCC требует механизма повторов (Retry), но не вызывает зависаний и взаимных блокировок базы.»"""
    },
    {
        "num": 8,
        "title": "Обработка ошибки ErrConcurrencyConflict и Retry",
        "task": "Определите кастомную ошибку ErrConcurrencyConflict. Напишите декоратор RetryingCommandHandler, который перехватывает ошибку конфликта версий при сохранении, повторно загружает актуальную историю событий из Event Store, заново применяет команду поверх свежего состояния агрегата и повторяет попытку сохранения с экспоненциальным backoff. Опишите ситуации, когда повтор команды недопустим (например, если повторная проверка бизнес-инварианта вернула отказ).",
        "theory": r"""Поскольку Optimistic Concurrency Control отклоняет транзакцию при обнаружении параллельного изменения, клиент не должен получать ошибку 500. Архитектурным решением является **декоратор с политикой повторов (Retry with Exponential Backoff and Jitter)**.

### Алгоритм работы Retry Decorator:
1. Попытка выполнить команду:
   - Загрузить агрегат из Event Store (текущая версия $V$).
   - Выполнить метод агрегата (проверка инвариантов).
   - Попытаться сохранить агрегат (`Save`).
2. Если `Save` вернул `ErrConcurrencyConflict`:
   - Если количество попыток не исчерпано:
     - Ожидание с экспоненциальной задержкой: $T = Base \cdot 2^{attempt} + Jitter$.
     - Повторить цикл с шага 1 (загрузится уже обновленный агрегат!).
3. **Критическое правило бизнес-инварианта:** Если при повторном применении команды на свежем агрегате бизнес-логика вернула отказ (например: денег на счете уже не хватает из-за параллельного списания), **повторы немедленно прекращаются**, и клиенту возвращается доменная ошибка отказа!""",
        "step_by_step": [
            "Определите интерфейс сервиса команд `AccountService`.",
            "Реализуйте декоратор `RetryingAccountService` с лимитом попыток (`maxRetries = 3`).",
            "Реализуйте экспоненциальную паузу между попытками.",
            "Проверьте сценарий: при конфликте версий повтор успешно завершает пополнение баланса.",
            "Проверьте сценарий: при нехватке средств после повтора цикл немедленно прерывается с бизнес-ошибкой."
        ],
        "code_blocks": [
            {
                "filename": "retry_handler.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"math/rand"
	"time"
)

type AccountService interface {
	Deposit(ctx context.Context, id string, amount int64) error
}

type BaseAccountService struct {
	store *PostgresEventStore
}

func (s *BaseAccountService) Deposit(ctx context.Context, id string, amount int64) error {
	// Имитация вычитки истории и применения
	acc := NewAccountAggregateV2(id)
	acc.version = 1 // допустим, в БД версия 1
	if err := acc.Deposit(amount); err != nil {
		return err
	}
	return s.store.Save(ctx, acc)
}

type RetryingAccountService struct {
	next       AccountService
	maxRetries int
	baseDelay  time.Duration
}

func NewRetryingAccountService(next AccountService, maxRetries int, baseDelay time.Duration) *RetryingAccountService {
	return &RetryingAccountService{
		next:       next,
		maxRetries: maxRetries,
		baseDelay:  baseDelay,
	}
}

func (r *RetryingAccountService) Deposit(ctx context.Context, id string, amount int64) error {
	var err error
	for attempt := 0; attempt < r.maxRetries; attempt++ {
		err = r.next.Deposit(ctx, id, amount)
		if err == nil {
			return nil
		}

		// Если это НЕ конфликт оптимистической блокировки, повторы бесполезны
		if !errors.Is(err, ErrConcurrencyConflict) {
			return err // Бизнес-ошибка (например, недостаток средств) возвращается сразу!
		}

		// Экспоненциальный бэкофф с джиттером
		jitter := time.Duration(rand.Int63n(int64(r.baseDelay)))
		sleepTime := (r.baseDelay * (1 << attempt)) + jitter
		fmt.Printf("[Retry] Конфликт версий на попытке %d. Ожидание %v...\n", attempt+1, sleepTime)

		select {
		case <-time.After(sleepTime):
		case <-ctx.Done():
			return ctx.Err()
		}
	}
	return fmt.Errorf("исчерпан лимит повторов (%d): %w", r.maxRetries, err)
}

func main() {
	db := &MockDB{}
	// Имитируем, что версия 2 уже занята в БД
	_ = db.Insert(EventRecord{StreamID: "ACC-1", Version: 2, EventType: "Dummy"})
	store := NewPostgresEventStore(db)

	baseSvc := &BaseAccountService{store: store}
	retrySvc := NewRetryingAccountService(baseSvc, 3, 10*time.Millisecond)

	ctx := context.Background()
	err := retrySvc.Deposit(ctx, "ACC-1", 500)
	if err != nil {
		fmt.Printf("Итог работы retry-декоратора: %v\n", err)
	}
}
"""
            }
        ],
        "under_the_hood": r"""Экспоненциальный Backoff с добавлением случайного разброса (Jitter) предотвращает явление «Thundering Herd Problem». Если 100 параллельных горутин столкнулись с конфликтом версий одновременно, случайный джиттер разносит их повторные попытки по времени, снижая вероятность повторного столкновения почти до нуля.""",
        "pitfalls": r"""Никогда не выполняйте безусловный retry при всех ошибках подряд. Повтор допустим **только** для временных ошибок конкурентности (`ErrConcurrencyConflict`) и сетевых таймаутов. Если ошибка вызвана нарушением бизнес-инварианта (например, счет заблокирован или баланс недостаточен), повторные вызовы создадут бессмысленную нагрузку на СУБД.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Wildberries:** «Что такое Jitter в политике повторов и почему обычный экспоненциальный бэкофф без Jitter опасен для микросервисов?»
**Ответ:** «Обычный бэкофф без Jitter заставляет все сбойные клиенты повторять попытки синхронными волнами (через 100мс, 200мс, 400мс). Это порождает периодические всплески трафика, добивающие и без того перегруженную базу данных. Full Jitter распределяет повторы равномерно по времени, сглаживая пики нагрузки.»"""
    },
    {
        "num": 9,
        "title": "Реестр типов событий (Event Type Registry)",
        "task": "При чтении событий из базы данных столбец event_type содержит строковое имя типа, а payload — бинарный JSON. Реализуйте потокобезопасный EventRegistry с методами Register(eventType string, prototype DomainEvent) и Deserialize(eventType string, data []byte) (DomainEvent, error) с использованием рефлексии или фабричных замыканий. Покажите, как реестр защищает систему от паники при десериализации неизвестных событий.",
        "theory": r"""При сохранении событий в полиморфный Event Store реляционная таблица ничего не знает о конкретных типах Go. Столбец `event_type` содержит строку (например, `"AccountCreated"`), а полезная нагрузка хранится в формате `JSONB`.

При загрузке истории необходимо превратить срез байт в конкретную структуру Go (`AccountCreatedEvent`). Для этого используется паттерн **Event Registry (Реестр типов событий)**:
1. При инициализации приложения каждый пакет регистрирует свои типы событий: `registry.Register("AccountCreated", func() DomainEvent { return &AccountCreatedEvent{} })`.
2. При вычитке событий из БД фабричное замыкание создает пустой экземпляр нужного типа, в который затем десериализуется JSON.
3. Если встретился неизвестный тип события (например, событие из новой версии сервиса), реестр возвращает явную ошибку `ErrUnknownEventType`, защищая приложение от паники (`nil pointer dereference`).""",
        "step_by_step": [
            "Определите тип фабрики `type EventFactory func() DomainEvent`.",
            "Создайте структуру `EventRegistry` с защитой мапы через `sync.RWMutex`.",
            "Реализуйте потокобезопасные методы `Register` и `Deserialize`.",
            "Зарегистрируйте типы событий `AccountCreated` и `MoneyDeposited`.",
            "Протестируйте десериализацию валидного JSON и обработку неизвестного типа события."
        ],
        "code_blocks": [
            {
                "filename": "event_registry.go",
                "lang": "go",
                "code": r"""package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"sync"
)

var ErrUnknownEventType = errors.New("неизвестный тип доменного события")

type EventFactory func() DomainEvent

type EventRegistry struct {
	mu        sync.RWMutex
	factories map[string]EventFactory
}

func NewEventRegistry() *EventRegistry {
	return &EventRegistry{
		factories: make(map[string]EventFactory),
	}
}

func (r *EventRegistry) Register(eventType string, factory EventFactory) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.factories[eventType] = factory
}

func (r *EventRegistry) Deserialize(eventType string, data []byte) (DomainEvent, error) {
	r.mu.RLock()
	factory, exists := r.factories[eventType]
	r.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("%w: %s", ErrUnknownEventType, eventType)
	}

	eventInstance := factory()
	if err := json.Unmarshal(data, eventInstance); err != nil {
		return nil, fmt.Errorf("ошибка JSON unmarshal для события %s: %w", eventType, err)
	}
	return eventInstance, nil
}

func main() {
	reg := NewEventRegistry()

	// Регистрация фабрик
	reg.Register("AccountCreated", func() DomainEvent {
		return &AccountCreatedEvent{}
	})
	reg.Register("MoneyDeposited", func() DomainEvent {
		return &MoneyDepositedEvent{}
	})

	// Имитация полезной нагрузки из PostgreSQL
	rawJSON := []byte(`{"OwnerName": "Дмитрий", "Currency": "USD"}`)

	evt, err := reg.Deserialize("AccountCreated", rawJSON)
	if err != nil {
		panic(err)
	}
	fmt.Printf("Десериализовано успешно: Тип=%T, Значение=%+v\n", evt, evt)

	// Попытка разобрать неизвестный тип
	_, err = reg.Deserialize("UserPromotedToAdmin", rawJSON)
	if errors.Is(err, ErrUnknownEventType) {
		fmt.Printf("✅ Безопасная обработка: %v\n", err)
	}
}
"""
            }
        ],
        "under_the_hood": r"""Использование фабричных функций `func() DomainEvent` превосходит рефлексию `reflect.New(reflect.TypeOf(...))` по скорости в 3–5 раз, поскольку компилятор Go может инлайнить создание структур, избегая дорогостоящего динамического анализа метаданных типов в рантайме.""",
        "pitfalls": r"""Будьте внимательны с возвратом указателя из фабрики. Функция `json.Unmarshal` требует передавать указатель на структуру (`&AccountCreatedEvent{}`). Если фабрика вернет структуру по значению, `json.Unmarshal` завершится ошибкой `json: Unmarshal(non-pointer ...)`.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Ozon:** «Что должен делать сервис-проектор, если из Event Store вычитано событие неизвестного типа?»
**Ответ:** «Проектор обязан залогировать событие на уровне INFO/DEBUG, пропустить его и продвинуть свой чекпоинт вперед. Если падать в панику при каждом неизвестном событии, невозможно будет провести Canary релиз нового сервиса, добавляющего новые типы событий в общую шину.»"""
    },
    {
        "num": 10,
        "title": "Снимки состояния агрегата (Snapshots)",
        "task": "Когда история агрегата насчитывает десятки тысяч событий, последовательная регидрация становится узким местом по CPU и времени. Спроектируйте таблицу snapshots (stream_id VARCHAR PRIMARY KEY, version BIGINT NOT NULL, state JSONB NOT NULL, created_at TIMESTAMPTZ). Напишите интерфейс SnapshotStore и реализуйте загрузку агрегата по комбинированному алгоритму: сначала загружается последний снимок, а затем из events дочитываются только события с version > snapshot.version.",
        "theory": r"""С течением времени долгоживущие агрегаты (банковские счета, складские запасы, корзины пользователей) накапливают тысячи событий. Вычитка 50 000 строк из базы данных и их последовательная регидрация при каждом запросе приводит к неприемлемому росту задержки (Latency > 500 мс).

### Паттерн Snapshotting (Снимки состояния):
1. **Снимок (Snapshot):** Точечный слепок внутреннего состояния агрегата на конкретную версию $V_{snap}$.
2. **Оптимизированная регидрация:**
   - Запрашивается последний снимок из `snapshots WHERE stream_id = :id`.
   - Если снимок найден: агрегат инициализируется состоянием из снимка (`version = V_{snap}`).
   - Из таблицы `events` запрашиваются только события, произошедшие **после** создания снимка: `WHERE stream_id = :id AND version > V_{snap} ORDER BY version ASC`.
   - Если снимок не найден, загружаются все события с версии 1.""",
        "step_by_step": [
            "Определите структуру `Snapshot` с полями `StreamID`, `Version`, `State` и `CreatedAt`.",
            "Объявите интерфейс `SnapshotStore` с методами `GetSnapshot` и `SaveSnapshot`.",
            "Реализуйте методы сериализации агрегата в снимок и восстановления из снимка.",
            "Напишите комбинированный загрузчик агрегата `LoadAggregate(id string)`.",
            "Продемонстрируйте загрузку агрегата с 1000 версиями, где загружается снимок версии 950 и дочитываются 50 свежих событий."
        ],
        "code_blocks": [
            {
                "filename": "snapshots.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"encoding/json"
	"fmt"
	"time"
)

type Snapshot struct {
	StreamID  string
	Version   int64
	State     []byte
	CreatedAt time.Time
}

type AccountStateSnapshot struct {
	ID      string `json:"id"`
	Owner   string `json:"owner"`
	Balance int64  `json:"balance"`
	Version int64  `json:"version"`
}

type SnapshotStore interface {
	GetSnapshot(ctx context.Context, streamID string) (*Snapshot, error)
	SaveSnapshot(ctx context.Context, snap *Snapshot) error
}

type MemorySnapshotStore struct {
	snaps map[string]*Snapshot
}

func (m *MemorySnapshotStore) GetSnapshot(ctx context.Context, id string) (*Snapshot, error) {
	snap, exists := m.snaps[id]
	if !exists {
		return nil, nil // Снимок отсутствует - это не ошибка
	}
	return snap, nil
}

func (m *MemorySnapshotStore) SaveSnapshot(ctx context.Context, snap *Snapshot) error {
	m.snaps[snap.StreamID] = snap
	return nil
}

// LoadAccountWithSnapshot реализует комбинированную быструю загрузку
func LoadAccountWithSnapshot(
	ctx context.Context,
	id string,
	snapStore SnapshotStore,
	eventStore *PostgresEventStore,
) (*AccountAggregateV2, error) {
	acc := NewAccountAggregateV2(id)
	var fromVersion int64 = 0

	// 1. Проверяем наличие снимка
	snap, err := snapStore.GetSnapshot(ctx, id)
	if err != nil {
		return nil, fmt.Errorf("ошибка чтения снимка: %w", err)
	}

	if snap != nil {
		var state AccountStateSnapshot
		if err := json.Unmarshal(snap.State, &state); err != nil {
			return nil, fmt.Errorf("ошибка распаковки снимка: %w", err)
		}
		acc.id = state.ID
		acc.owner = state.Owner
		acc.balance = state.Balance
		acc.version = state.Version
		fromVersion = state.Version
		fmt.Printf("[Load] Загружен снимок версии %d (баланс: %d)\n", state.Version, state.Balance)
	}

	// 2. Дочитываем дельту событий: version > fromVersion
	// (В данном демо имитируем 2 свежих события после снимка)
	freshEvents := []DomainEvent{
		NewMoneyDepositedEvent(id, fromVersion+1, 500, "Новый депозит 1"),
		NewMoneyDepositedEvent(id, fromVersion+2, 700, "Новый депозит 2"),
	}

	for _, e := range freshEvents {
		acc.apply(e)
	}
	fmt.Printf("[Load] Применено %d свежих событий. Финальная версия: %d\n", len(freshEvents), acc.version)
	return acc, nil
}

func main() {
	snapStore := &MemorySnapshotStore{snaps: make(map[string]*Snapshot)}
	ctx := context.Background()

	// Сохраняем снимок на версии 100
	snapData, _ := json.Marshal(AccountStateSnapshot{
		ID:      "ACC-1",
		Owner:   "Ольга",
		Balance: 100000,
		Version: 100,
	})
	_ = snapStore.SaveSnapshot(ctx, &Snapshot{
		StreamID:  "ACC-1",
		Version:   100,
		State:     snapData,
		CreatedAt: time.Now(),
	})

	acc, _ := LoadAccountWithSnapshot(ctx, "ACC-1", snapStore, nil)
	fmt.Printf("Итоговое состояние: Баланс=%d, Версия=%d\n", acc.balance, acc.version)
}
"""
            }
        ],
        "under_the_hood": r"""Снимки — это исключительно оптимизация чтения и регидрации. С точки зрения архитектуры они являются производными данными (кэшем). Если таблица `snapshots` будет полностью очищена или повреждена, система сохраняет 100% работоспособность, поскольку любое состояние может быть заново вычислено из первоисточника — таблицы `events`.""",
        "pitfalls": r"""При изменении структуры агрегата (добавление новых полей) старые снимки в формате JSON могут десериализоваться некорректно. Обязательно добавляйте в снимок поле схемы `schema_version`, либо удаляйте устаревшие снимки при релизе новой версии агрегата, заставляя систему один раз пересчитать состояние из событий.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Яндекс:** «Как часто следует создавать снимки агрегатов в продакшене?»
**Ответ:** «Частота создания снимков — это классический компромисс между накладными расходами на запись и временем восстановления. Отраслевой стандарт — сохранять снимок каждые $N$ событий (обычно от 50 до 200 событий), либо по таймеру для активных агрегатов. Снимок создается асинхронно в фоновой горутине, чтобы не увеличивать латентность обработки команды.»"""
    },
    {
        "num": 11,
        "title": "Политика автоматического создания снимков",
        "task": "Реализуйте в EventStore фоновое или синхронное создание снимков состояния: если aggregate.Version() - lastSnapshotVersion >= SnapshotInterval (например, каждые 100 событий), асинхронно сериализуйте состояние агрегата и сохраните в snapshots. Напишите бенчмарк восстановления агрегата с 5000 событий с использованием снимков и без них.",
        "theory": r"""Для автоматизации процесса сохранения снимков репозиторий Event Store оснащается политикой **Snapshot Strategy**.

### Стратегия на основе интервала (Interval-Based Policy):
- Задается порог `SnapshotInterval` (например, 100).
- При успешном сохранении событий проверяется условие:
  $$\text{aggregate.Version()} - \text{lastSnapshotVersion} \ge \text{SnapshotInterval}$$
- Если условие выполнено, задача сериализации снимка отправляется в неблокирующий канал фонового воркера.
- Фоновый воркер записывает снимок в базу данных без задержки основного HTTP-запроса клиента.""",
        "step_by_step": [
            "Определите структуру `SnapshotPolicy` с порогом `Interval int64`.",
            "Реализуйте асинхронный воркер создания снимков через канал `chan *Snapshot`.",
            "Напишите проверку необходимости создания снимка при каждом `Save`.",
            "Напишите эталонный тест производительности (Benchmark), доказывающий эффективность снимков при 5000 событий."
        ],
        "code_blocks": [
            {
                "filename": "snapshot_policy.go",
                "lang": "go",
                "code": r"""package main

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"
)

type AutoSnapshotter struct {
	interval  int64
	snapChan  chan *Snapshot
	snapStore SnapshotStore
	wg        sync.WaitGroup
}

func NewAutoSnapshotter(interval int64, store SnapshotStore) *AutoSnapshotter {
	s := &AutoSnapshotter{
		interval:  interval,
		snapChan:  make(chan *Snapshot, 100),
		snapStore: store,
	}
	s.startWorker()
	return s
}

func (s *AutoSnapshotter) startWorker() {
	s.wg.Add(1)
	go func() {
		defer s.wg.Done()
		for snap := range s.snapChan {
			_ = s.snapStore.SaveSnapshot(nil, snap)
			fmt.Printf("[AutoSnapshotter] Снимок агрегата %s на версии %d успешно сохранен в фоне\n",
				snap.StreamID, snap.Version)
		}
	}()
}

func (s *AutoSnapshotter) CheckAndTrigger(acc *AccountAggregateV2, lastSnapVer int64) {
	if acc.version-lastSnapVer >= s.interval {
		stateData, _ := json.Marshal(AccountStateSnapshot{
			ID:      acc.id,
			Owner:   acc.owner,
			Balance: acc.balance,
			Version: acc.version,
		})
		snap := &Snapshot{
			StreamID:  acc.id,
			Version:   acc.version,
			State:     stateData,
			CreatedAt: time.Now(),
		}

		select {
		case s.snapChan <- snap:
		default:
			fmt.Println("[AutoSnapshotter] Очередь снимков переполнена, пропуск")
		}
	}
}

func (s *AutoSnapshotter) Stop() {
	close(s.snapChan)
	s.wg.Wait()
}

func main() {
	snapStore := &MemorySnapshotStore{snaps: make(map[string]*Snapshot)}
	snapshotter := NewAutoSnapshotter(50, snapStore)

	acc := NewAccountAggregateV2("ACC-AUTO")
	acc.id = "ACC-AUTO"
	acc.version = 100 // Накопилось 100 событий

	snapshotter.CheckAndTrigger(acc, 0)
	time.Sleep(50 * time.Millisecond) // Ожидание завершения воркера
	snapshotter.Stop()
}
"""
            }
        ],
        "under_the_hood": r"""Асинхронный воркер снимков использует буферизованный канал и паттерн `select with default` (Non-blocking Send). Если база данных снимков временно перегружена или диск медленный, воркер дропает задачу создания снимка вместо того, чтобы блокировать клиентский поток записи событий. Снимок будет создан на следующей итерации.""",
        "pitfalls": r"""При асинхронном создании снимка передавайте в канал **глубокую копию** состояния агрегата или сериализованный JSON байт-срез. Если передать указатель на сам агрегат, параллельные запросы могут продолжить мутировать его поля прямо во время сериализации в JSON, вызвав гонку данных (Data Race).""",
        "bigtech_interview": r"""**Вопрос с собеседования в Авито:** «Что произойдет, если процесс аварийно завершится (kill -9) до того, как фоновый воркер снимков запишет снимок в БД?»
**Ответ:** «Абсолютно ничего страшного. Снимок — это не первоисточник истины, а лишь кэш. Все события транзакции уже надежно зафиксированы в таблице `events`. При следующем старте агрегат просто восстановит состояние из предыдущего снимка или с версии 1, не потеряв ни одного байта доменных данных.»"""
    },
    {
        "num": 12,
        "title": "Синхронные vs Асинхронные проекции (Read Models)",
        "task": "Создайте таблицу для Read-модели account_views (account_id VARCHAR PRIMARY KEY, owner_name TEXT, balance NUMERIC, last_updated_at TIMESTAMPTZ). Реализуйте синхронный проектор, который вызывается в той же транзакции базы данных, что и вставка в events. Проанализируйте плюсы и минусы: гарантия немедленной консистентности (Read-Your-Own-Writes) ценой увеличения задержки записи и связывания модели чтения с хранилищем событий.",
        "theory": r"""В CQRS модель чтения (Read Model) формируется специализированными компонентами — **Проекторами (Projectors / Event Handlers)**.

### Синхронные проекции (Synchronous Projections):
Проектор вызывается **внутри той же транзакции базы данных**, в которой сохраняются события в `events`:
- **Плюсы:** Немедленная консистентность (**Strong Consistency**). Пользователь гарантированно сразу видит результат своей операции («Read-Your-Own-Writes»). Нет риска рассинхронизации.
- **Минусы:**
  - Модель чтения жестко привязана к той же реляционной СУБД (нельзя синхронно обновить Elasticsearch или Redis в ACID-транзакции PostgreSQL).
  - Задержка записи (Write Latency) возрастает пропорционально числу обновляемых проекций.
  - Ошибка в обновлении проекции откатывает всю доменную команду.

### Асинхронные проекции (Asynchronous Projections):
События записываются в `events`, а независимые фоновые воркеры вычитывают их и обновляют модели чтения (Postgres, Redis, Elastic) асинхронно:
- **Плюсы:** Высочайшая скорость записи, полная изоляция систем, поддержка гетерогенных хранилищ.
- **Минусы:** Согласованность в конечном счете (**Eventual Consistency**). Задержка обновления от десятков миллисекунд до секунд.""",
        "step_by_step": [
            "Спроектируйте реляционную таблицу `account_views`.",
            "Реализуйте синхронный проектор, обновляющий представление в той же транзакции.",
            "Продемонстрируйте атомарный откат: если проектор падает, доменное событие также не сохраняется.",
            "Сравните накладные расходы синхронного и асинхронного подходов."
        ],
        "code_blocks": [
            {
                "filename": "sync_projection.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

type AccountView struct {
	AccountID     string
	OwnerName     string
	Balance       int64
	LastUpdatedAt time.Time
}

type SyncProjector struct {
	mu    sync.Mutex
	views map[string]AccountView
}

func (p *SyncProjector) Project(ctx context.Context, event DomainEvent) error {
	p.mu.Lock()
	defer p.mu.Unlock()

	switch e := event.(type) {
	case AccountCreatedEvent:
		p.views[e.AggregateID()] = AccountView{
			AccountID:     e.AggregateID(),
			OwnerName:     e.OwnerName,
			Balance:       0,
			LastUpdatedAt: e.OccurredAt(),
		}
	case MoneyDepositedEvent:
		view, exists := p.views[e.AggregateID()]
		if !exists {
			return errors.New("read model view не найдена")
		}
		view.Balance += e.Amount
		view.LastUpdatedAt = e.OccurredAt()
		p.views[e.AggregateID()] = view
	}
	return nil
}

func main() {
	projector := &SyncProjector{views: make(map[string]AccountView)}
	ctx := context.Background()

	e1 := NewAccountCreatedEvent("ACC-SYNC", 1, "Артем", "RUB")
	e2 := NewMoneyDepositedEvent("ACC-SYNC", 2, 45000, "Зарплата")

	// Синхронный вызов проектора
	_ = projector.Project(ctx, e1)
	_ = projector.Project(ctx, e2)

	view := projector.views["ACC-SYNC"]
	fmt.Printf("Синхронная Read-модель: Владелец=%s, Баланс=%d, Обновлено=%s\n",
		view.OwnerName, view.Balance, view.LastUpdatedAt.Format(time.TimeOnly))
}
"""
            }
        ],
        "under_the_hood": r"""Синхронная проекция в реляционной базе данных реализуется через конструкцию `INSERT ... ON CONFLICT (account_id) DO UPDATE SET balance = account_views.balance + EXCLUDED.balance`. Так как операция выполняется внутри одной транзакции с `INSERT INTO events`, СУБД удерживает строчные блокировки обеих таблиц вплоть до момента `COMMIT`.""",
        "pitfalls": r"""Никогда не пытайтесь вызывать внутри синхронного проектора внешние HTTP-сервисы, сторонние брокеры сообщений или RPC-вызовы. Если внешний сервис зависнет, транзакция PostgreSQL останется открытой, удерживая блокировки строк и исчерпывая пул соединений СУБД.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Wildberries:** «В каких случаях в микросервисной архитектуре допустимо использовать синхронные проекции вместо асинхронных?»
**Ответ:** «Синхронные проекции оправданы в строго ограниченных случаях: 1) Критические финансовые операции, где недопустима задержка консистентности даже на 10 миллисекунд; 2) Когда и хранилище событий, и модель чтения находятся в одной физической СУБД; 3) На ранних этапах MVP, когда сложность поддержки Kafka/CDC превышает выгоду от масштабирования.»"""
    },
    {
        "num": 13,
        "title": "Асинхронные проекции и отслеживание смещения (Checkpoints)",
        "task": "Для масштабируемых систем проекции строятся асинхронно. Создайте таблицу projection_checkpoints (projection_name VARCHAR PRIMARY KEY, last_event_id UUID, last_position BIGINT, updated_at TIMESTAMPTZ). Напишите воркер, который периодически опрашивает таблицу events порциями (LIMIT 100) по условию position > last_position, обновляет денормализованные представления и атомарно фиксирует новый чекпоинт.",
        "theory": r"""Для обеспечения максимальной масштабируемости проекции выносятся в фоновые воркеры. Чтобы воркер знал, с какого места продолжить обработку после рестарта, используется механизм **Чекпоинтов (Checkpoints / Offsets)**.

### Алгоритм работы Catch-Up Projection Worker:
1. Воркер считывает свой последний сохраненный оффсет из таблицы чекпоинтов:
   `SELECT last_position FROM projection_checkpoints WHERE projection_name = 'user_profiles'`.
2. Выбирает следующую порцию событий:
   `SELECT * FROM events WHERE global_position > :last_position ORDER BY global_position ASC LIMIT 100`.
3. В рамках единой транзакции воркер:
   - Применяет изменения к денормализованной таблице Read-модели.
   - Обновляет смещение: `UPDATE projection_checkpoints SET last_position = :new_max_pos`.
4. Коммитит транзакцию. При аварийном падении воркера обработка возобновится строго с `last_position`.""",
        "step_by_step": [
            "Создайте схему таблицы `projection_checkpoints`.",
            "Определите структуру `CheckpointTracker` для работы со смещениями.",
            "Реализуйте цикл вычитки батчами с паузой (`PollInterval`) при отсутствии новых событий.",
            "Обеспечьте атомарность обновления проекции и фиксации чекпоинта.",
            "Продемонстрируйте восстановление воркера после имитации падения."
        ],
        "code_blocks": [
            {
                "filename": "checkpoint_worker.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

type Checkpoint struct {
	ProjectionName string
	LastPosition   int64
	UpdatedAt      time.Time
}

type ProjectionWorker struct {
	name         string
	lastPosition int64
	mu           sync.Mutex
	views        map[string]int64
}

func NewProjectionWorker(name string) *ProjectionWorker {
	return &ProjectionWorker{
		name:  name,
		views: make(map[string]int64),
	}
}

type StoredEvent struct {
	GlobalPosition int64
	StreamID       string
	EventType      string
	Amount         int64
}

// ProcessBatch обрабатывает пачку событий и атомарно фиксирует смещение
func (w *ProjectionWorker) ProcessBatch(events []StoredEvent) {
	w.mu.Lock()
	defer w.mu.Unlock()

	for _, e := range events {
		if e.GlobalPosition <= w.lastPosition {
			continue // Защита от дублей
		}

		// Обновление представления
		w.views[e.StreamID] += e.Amount
		w.lastPosition = e.GlobalPosition
	}
	fmt.Printf("[%s] Обработан батч до позиции %d. Всего аккаунтов в кэше: %d\n",
		w.name, w.lastPosition, len(w.views))
}

func main() {
	worker := NewProjectionWorker("AccountBalanceProjector")

	batch1 := []StoredEvent{
		{GlobalPosition: 1, StreamID: "acc-1", Amount: 100},
		{GlobalPosition: 2, StreamID: "acc-2", Amount: 250},
		{GlobalPosition: 3, StreamID: "acc-1", Amount: 50},
	}

	worker.ProcessBatch(batch1)

	// Имитация повторной отправки части батча (семантика At-Least-Once)
	batch2 := []StoredEvent{
		{GlobalPosition: 3, StreamID: "acc-1", Amount: 50}, // Дубликат
		{GlobalPosition: 4, StreamID: "acc-3", Amount: 500},
	}
	worker.ProcessBatch(batch2)

	fmt.Printf("Финальный баланс acc-1: %d (ожидается 150)\n", worker.views["acc-1"])
	fmt.Printf("Финальный чекпоинт: %d\n", worker.lastPosition)
}
"""
            }
        ],
        "under_the_hood": r"""Атомарная фиксация `(projection_data, checkpoint)` в единой транзакции PostgreSQL превращает семантику доставки **At-Least-Once** в семантику **Effectively-Once Processing**. Даже если воркер упадет в процессе вычитки, база данных откатит незакоммиченные строки проекции вместе со смещением, предотвратив рассинхронизацию данных.""",
        "pitfalls": r"""Если воркер сохраняет чекпоинт в Redis, а саму проекцию обновляет в Elasticsearch, невозможно обеспечить атомарность между двумя независимыми хранилищами без двухфазного коммита (2PC). Решением является хранение смещения версии прямо внутри документа Elasticsearch (поля `_version` или `last_processed_version`).""",
        "bigtech_interview": r"""**Вопрос с собеседования в Т-Банк:** «Как воркеру проекции обрабатывать ситуацию, когда в последовательности `global_position` образовалась дыра: после позиции 10 сразу идет позиция 12?»
**Ответ:** «В PostgreSQL при откате транзакций счетчик `BIGSERIAL` не откатывается, поэтому пропуски в последовательности неизбежны. Воркер не должен останавливаться и паниковать из-за пропусков. Он ориентируется на условие строгого неравенства `global_position > last_position`, сохраняя в качестве чекпоинта максимальный фактически обработанный номер позиции.»"""
    },
    {
        "num": 14,
        "title": "Идемпотентность обработчиков проекций",
        "task": "В распределенных системах события могут доставляться повторно (семантика At-Least-Once). Реализуйте идемпотентное обновление проекций: при получении события проектор проверяет, не была ли уже обработана данная версия агрегата (WHERE version < :new_version), либо использует конструкцию INSERT ... ON CONFLICT (account_id) DO UPDATE ... WHERE account_views.version < EXCLUDED.version. Объясните, почему идемпотентность критична для надежности Read-моделей.",
        "theory": r"""В реальных распределенных архитектурах доставка сообщений через брокеры (Kafka, RabbitMQ, NATS) гарантирует только семантику **At-Least-Once** (как минимум один раз). События могут приходить повторно из-за сетевых сбоев, перезапуска потребителей или повторного перебалансирования партиций.

### Угроза неидемпотентного проектора:
Если событие `MoneyDepositedEvent{Amount: 1000}` обработается дважды:
- Баланс пользователя в Read-модели увеличится на 2000 вместо 1000!
- Модель чтения разойдется с реальной историей агрегата.

### Реализация идемпотентности:
1. **Отслеживание версий сущности:** Каждая строка в таблице Read-модели содержит столбец `version`.
2. **Условное обновление в SQL:**
   ```sql
   INSERT INTO account_views (account_id, balance, version)
   VALUES ($1, $2, $3)
   ON CONFLICT (account_id) DO UPDATE
   SET balance = account_views.balance + EXCLUDED.balance,
       version = EXCLUDED.version
   WHERE account_views.version < EXCLUDED.version;
   ```
   Если событие с версией 3 придет повторно, предикат `WHERE version < 3` вернет `false`, и строка базы останется нетронутой.""",
        "step_by_step": [
            "Определите структуру `AccountViewWithVersion` с полями `Balance` и `Version`.",
            "Реализуйте проектор с проверкой номера версии перед модификацией состояния.",
            "Протестируйте повторную отправку одного и того же события и убедитесь, что баланс не задваивается.",
            "Проверьте игнорирование устаревших событий, пришедших с задержкой."
        ],
        "code_blocks": [
            {
                "filename": "idempotent_projector.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
)

type AccountViewWithVersion struct {
	AccountID string
	Balance   int64
	Version   int64
}

type IdempotentProjector struct {
	mu    sync.Mutex
	views map[string]AccountViewWithVersion
}

func NewIdempotentProjector() *IdempotentProjector {
	return &IdempotentProjector{views: make(map[string]AccountViewWithVersion)}
}

func (p *IdempotentProjector) Handle(event DomainEvent) {
	p.mu.Lock()
	defer p.mu.Unlock()

	currentView, exists := p.views[event.AggregateID()]

	// КЛЮЧЕВАЯ ПРОВЕРКА ИДЕМПОТЕНТНОСТИ:
	// Если версия события меньше или равна текущей версии проекции - событие уже учтено!
	if exists && event.Version() <= currentView.Version {
		fmt.Printf("[Projector] ДУБЛИКАТ: событие %s версии %d пропущено (текущая версия %d)\n",
			event.EventType(), event.Version(), currentView.Version)
		return
	}

	switch e := event.(type) {
	case AccountCreatedEvent:
		p.views[e.AggregateID()] = AccountViewWithVersion{
			AccountID: e.AggregateID(),
			Balance:   0,
			Version:   e.Version(),
		}
	case MoneyDepositedEvent:
		p.views[e.AggregateID()] = AccountViewWithVersion{
			AccountID: e.AggregateID(),
			Balance:   currentView.Balance + e.Amount,
			Version:   e.Version(),
		}
	}
	fmt.Printf("[Projector] УСПЕХ: применены данные события %s версии %d\n", event.EventType(), event.Version())
}

func main() {
	p := NewIdempotentProjector()

	e1 := NewAccountCreatedEvent("ACC-1", 1, "Мария", "RUB")
	e2 := NewMoneyDepositedEvent("ACC-1", 2, 5000, "Перевод")

	p.Handle(e1)
	p.Handle(e2)

	// Имитация повторной доставки из брокера сообщений
	fmt.Println("\n--- Повторная доставка дубликатов ---")
	p.Handle(e2) // Дубликат версии 2
	p.Handle(e1) // Дубликат версии 1

	finalView := p.views["ACC-1"]
	fmt.Printf("\nИтоговый баланс: %d руб. (Версия: %d)\n", finalView.Balance, finalView.Version)
}
"""
            }
        ],
        "under_the_hood": r"""На уровне СУБД проверка `WHERE version < EXCLUDED.version` внутри конструкции `ON CONFLICT DO UPDATE` предотвращает запись в WAL-журнал и обновление страниц индекса, если условие не выполнено. Это не только гарантирует корректность бизнес-данных, но и экономит I/O дисковой подсистемы при повторных накатах событий.""",
        "pitfalls": r"""Идемпотентность по версии агрегата работает идеально, если события поступают упорядоченными в рамках одного потока (`stream_id`). Но если события из разных партиций пришли с нарушением порядка (версия 3 раньше версии 2), простая проверка `version <= currentVersion` отбросит версию 2 навсегда, вызвав потерю данных! Для таких случаев требуется буфер ожидания (Out-of-Order Buffer).""",
        "bigtech_interview": r"""**Вопрос с собеседования в Авито:** «Что такое семантика Exactly-Once Processing и почему многие эксперты утверждают, что в распределенных сетях ее физически невозможно достичь без идемпотентности потребителя?»
**Ответ:** «Из-за ненадежности сетей (проблема двух генералов, сбои подтверждений ACK) брокер сообщений не может отличить потерю сообщения от потери подтверждения о доставке. Поэтому брокер вынужден слать повторы (At-Least-Once). "Exactly-Once" на практике достигается связкой: доставка At-Least-Once + идемпотентная обработка на стороне получателя (дедупликация по ключу или проверка версий).»"""
    },
    {
        "num": 15,
        "title": "Построение проекции в Elasticsearch для полнотекстового поиска",
        "task": "Напишите проектор, который слушает события создания и изменения профилей пользователей и асинхронно индексирует документы в Elasticsearch с помощью elastic/go-elasticsearch. Настройте Bulk API для пакетной вставки и обработку ошибок недоступности кластера поиска с сохранением смещения (checkpoint) без потери данных.",
        "theory": r"""Одним из главных преимуществ CQRS является возможность строить специализированные модели чтения на базе принципиально разных движков данных:
- Реляционные таблицы в PostgreSQL — для финансовых балансов.
- Хранилище Redis — для высоконагруженных счетчиков и сессий.
- Поисковый движок **Elasticsearch / OpenSearch** — для фасетного, нечеткого (Fuzzy) и полнотекстового поиска пользователей, товаров или документов.

### Паттерн Elasticsearch Bulk Projector:
1. Проектор собирает входящие события в локальный буфер (батч до 500 документов или по таймеру 100 мс).
2. Формирует тело запроса для **Bulk API** (`/_bulk`).
3. При индексации использует идентификатор агрегата как `_id` документа (`index: { _index: "users", _id: event.AggregateID() }`), что автоматически обеспечивает идемпотентность обновления.
4. В документе сохраняется поле `version`: Elasticsearch проверяет `version_type=external`, предотвращая перезапись более свежих данных устаревшими событиями.""",
        "step_by_step": [
            "Определите структуру документа Elasticsearch `UserSearchDocument`.",
            "Смоделируйте буферизованный процессор пакетов с таймером сброса (Flush Interval).",
            "Реализуйте сериализацию пакета документов в формат NDJSON, требуемый Elasticsearch Bulk API.",
            "Добавьте обработку сетевых ошибок с отказом продвижения чекпоинта при недоступности поискового кластера.",
            "Продемонстрируйте сборку NDJSON полезной нагрузки."
        ],
        "code_blocks": [
            {
                "filename": "elastic_projector.go",
                "lang": "go",
                "code": r"""package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"time"
)

type UserSearchDocument struct {
	ID        string    `json:"id"`
	FullName  string    `json:"full_name"`
	Email     string    `json:"email"`
	Version   int64     `json:"version"`
	UpdatedAt time.Time `json:"updated_at"`
}

type ElasticBulkProjector struct {
	buffer     []UserSearchDocument
	batchSize  int
	flushTimer *time.Ticker
}

func NewElasticBulkProjector(batchSize int) *ElasticBulkProjector {
	return &ElasticBulkProjector{
		buffer:    make([]UserSearchDocument, 0, batchSize),
		batchSize: batchSize,
	}
}

func (p *ElasticBulkProjector) Add(doc UserSearchDocument) {
	p.buffer = append(p.buffer, doc)
	if len(p.buffer) >= p.batchSize {
		_ = p.Flush(context.Background())
	}
}

// Flush формирует NDJSON пакет для Elasticsearch Bulk API
func (p *ElasticBulkProjector) Flush(ctx context.Context) error {
	if len(p.buffer) == 0 {
		return nil
	}

	var buf bytes.Buffer
	for _, doc := range p.buffer {
		// 1. Метаданные действия Bulk API
		meta := fmt.Sprintf(`{"index": {"_index": "users", "_id": "%s", "version": %d, "version_type": "external"}}`+"\n",
			doc.ID, doc.Version)
		buf.WriteString(meta)

		// 2. Тело документа
		docBytes, err := json.Marshal(doc)
		if err != nil {
			return err
		}
		buf.Write(docBytes)
		buf.WriteString("\n")
	}

	// Имитация отправки в Elasticsearch HTTP Client
	fmt.Printf("[Elasticsearch] Отправлен Bulk-запрос с %d документами (%d байт):\n", len(p.buffer), buf.Len())
	fmt.Print(buf.String())

	p.buffer = p.buffer[:0] // Очистка буфера после успешного коммита
	return nil
}

func main() {
	projector := NewElasticBulkProjector(2)

	projector.Add(UserSearchDocument{
		ID:        "usr-1",
		FullName:  "Константин Хабенский",
		Email:     "khabensky@theatre.ru",
		Version:   1,
		UpdatedAt: time.Now().UTC(),
	})

	projector.Add(UserSearchDocument{
		ID:        "usr-2",
		FullName:  "Данила Козловский",
		Email:     "danila@cinema.ru",
		Version:   2,
		UpdatedAt: time.Now().UTC(),
	})
}
"""
            }
        ],
        "under_the_hood": r"""Параметр `version_type=external` в Elasticsearch Bulk API заставляет движок Lucene сверять переданную версию с версией существующего документа. Если переданная версия меньше или равна текущей версии документа в индексе, Elasticsearch отклоняет обновление конкретной записи со статусом 409 Conflict, не прерывая вставку остальных документов батча.""",
        "pitfalls": r"""В Elasticsearch операции индексации становятся доступными для поиска только после операции `refresh` (по умолчанию раз в секунду). Не пытайтесь сразу после выполнения команды записи выполнять поисковый запрос к Elasticsearch в тестах без явного ожидания или вызова `?refresh=wait_for`, иначе тест упадет с ложным `NotFound`.""",
        "bigtech_interview": r"""**Вопрос с собеседования в Яндекс:** «Что делать, если поисковый кластер Elasticsearch упал на 3 часа, в то время как Event Store в PostgreSQL продолжает принимать терабайты данных?»
**Ответ:** «Поскольку проектор асинхронен и хранит свой чекпоинт в надежном хранилище (Postgres или координаторе), отказ Elasticsearch никак не влияет на прием записей. Когда кластер восстановится, воркер на максимальной скорости пакетами Bulk API вычитает накопившуюся историю и нагонит смещение (Catch-up).»"""
    }
]
