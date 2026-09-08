#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import subprocess

def validate_go_code(code, label):
    p = subprocess.run(["gofmt", "-e"], input=code, capture_output=True, text=True)
    if p.returncode != 0:
        raise ValueError(f"Go syntax error in {label}:\n{p.stderr}\nCode:\n{code}")

exercises = []

# Ex 1
code1 = r'''package main

import (
	"fmt"
	"time"
)

// PlatformSLO определяет ключевые индикаторы качества обслуживания распределенной системы
type PlatformSLO struct {
	TargetRPS         int           // Целевой пиковый RPS (100 000)
	TargetP99Latency  time.Duration // Максимальная задержка p99 (50 мс)
	AvailabilitySLA   float64       // Доступность 99.99% (Four Nines)
	MaxDataLossRPO    time.Duration // Recovery Point Objective (0 сек для денег)
	MaxDowntimeRTO    time.Duration // Recovery Time Objective (< 30 сек)
}

func PrintPlatformSpec(slo PlatformSLO) {
	fmt.Println("=== АРХИТЕКТУРНЫЙ CAPSTONE: ТЕХНИЧЕСКИЙ МАНИФЕСТ ПЛАТФОРМЫ ===")
	fmt.Printf("Пиковая пропускная способность: %d RPS\n", slo.TargetRPS)
	fmt.Printf("Максимальная задержка (p99):     %v\n", slo.TargetP99Latency)
	fmt.Printf("Целевая доступность (SLA):      %.2f%% (допустимый простой < 52 мин/год)\n", slo.AvailabilitySLA)
	fmt.Printf("Финансовый RPO:                 %v (Zero Data Loss через синхронную репликацию)\n", slo.MaxDataLossRPO)
	fmt.Printf("Аварийное восстановление RTO:   <%v (автоматический Failover)\n", slo.MaxDowntimeRTO)
}

func main() {
	spec := PlatformSLO{
		TargetRPS:        100000,
		TargetP99Latency: 50 * time.Millisecond,
		AvailabilitySLA:  99.99,
		MaxDataLossRPO:   0,
		MaxDowntimeRTO:   30 * time.Second,
	}
	PrintPlatformSpec(spec)
}
'''
validate_go_code(code1, "Ex 1")
exercises.append({
    "num": 1,
    "title": "Постановка задачи Архитектурного Capstone (Staff / Principal Level)",
    "task": "Изучите глобальное техническое задание выпускного проекта Capstone: проектирование и сквозная реализация распределенной финансово-торговой платформы (FinTech / HighLoad Platform) с пиковой нагрузкой 100 000+ RPS, доступностью 99.99% (SLA), задержкой p99 < 50 мс, нулевой потерей финансовых данных (RPO=0) и автоматическим восстановлением (RTO < 30 сек).",
    "theory": """Архитектурный Capstone — кульминация курса Go Workout, объединяющая все пройденные компетенции (от низкоуровневых сокетов и GMP планировщика до распределенного консенсуса Raft, CQRS/Event Sourcing, Kubernetes Operators и LLM-агентов).
Требования к HighLoad платформе уровня Staff / Principal Engineer:
1. **Функциональные требования**:
   - Мультивалютные счета пользователей, учет балансов с защитой от овердрафта и двойного списания.
   - Каталог товаров с миллионным ассортиментом, поиск и остатки на складах.
   - Оформление заказов через распределенную Сагу (Saga Pattern).
   - Интеллектуальный ИИ-ассистент поддержки пользователей (RAG + Tool Use).
2. **Нефункциональные требования (SLA/SLO)**:
   - **100 000 RPS** пиковой нагрузки в Черную пятницу.
   - **p99 Latency < 50 ms**: 99% запросов выполняются быстрее 50 мс.
   - **Доступность 99.99% (Four Nines)**: суммарный неплановый простой не более 52.6 минут в год.
   - **RPO = 0 (Recovery Point Objective)**: ни одна завершенная финансовая транзакция не может быть потеряна при отказе ЦОД.""",
    "step_by_step": [
        "Определите структуру `PlatformSLO` с целевыми показателями надежности и скорости.",
        "Рассчитайте допустимый бюджет ошибок (Error Budget) для уровня доступности 99.99%.",
        "Сформулируйте функциональные ограничения финансовых агрегатов.",
        "Выведите технический манифест платформы."
    ],
    "code_blocks": [{
        "filename": "capstone_spec.go",
        "lang": "go",
        "code": code1
    }],
    "under_the_hood": "Достижение 100 000 RPS при p99 < 50 мс на Go требует устранения блокировок в рантайме: минимизация аллокаций в куче для предотвращения пауз GC (Stop-The-World), использование двухуровневого кэша L1/L2, оптимистические блокировки в PostgreSQL и асинхронная шина Kafka.",
    "pitfalls": "Попытка спроектировать единый монолитный ACID-контекст на распределенную платформу приведет к деградации базы данных при 5000 RPS из-за блокировок строк и двухфазных коммитов (2PC).",
    "bigtech_interview": "В чем разница между SLA, SLO и SLI в методологии Google SRE?\nОтвет: SLI (Service Level Indicator) — это фактическая измеряемая метрика в реальном времени (например, 'доля успешных HTTP-ответов за последние 5 минут'). SLO (Service Level Objective) — внутренняя инженерная цель команды (например, '99.99% запросов успешны за 30 дней'). SLA (Service Level Agreement) — внешнее юридическое или бизнес-обязательство перед клиентами с финансовыми штрафами при его нарушении."
})

# Ex 2
code2 = r'''package main

import "fmt"

type BoundedContext string

const (
	ContextIdentity     BoundedContext = "Identity & Access"
	ContextBillingCore  BoundedContext = "Billing & Financial Core"
	ContextInventory    BoundedContext = "Catalog & Inventory"
	ContextOrderFulfill BoundedContext = "Order Fulfillment"
	ContextNotification BoundedContext = "Notification Gateway"
	ContextAnalytics    BoundedContext = "Real-time Analytics"
)

type MicroserviceDefinition struct {
	Name            string
	Context         BoundedContext
	PrimaryStorage  string
	CommProtocol    string
}

func GetPlatformMicroservices() []MicroserviceDefinition {
	return []MicroserviceDefinition{
		{Name: "auth-service", Context: ContextIdentity, PrimaryStorage: "PostgreSQL + Redis", CommProtocol: "gRPC + HTTP"},
		{Name: "billing-service", Context: ContextBillingCore, PrimaryStorage: "PostgreSQL Event Store", CommProtocol: "gRPC + Kafka"},
		{Name: "catalog-service", Context: ContextInventory, PrimaryStorage: "PostgreSQL + Redis L1/L2", CommProtocol: "gRPC"},
		{Name: "order-service", Context: ContextOrderFulfill, PrimaryStorage: "PostgreSQL Saga State", CommProtocol: "gRPC + Kafka"},
		{Name: "notification-gw", Context: ContextNotification, PrimaryStorage: "Redis Queue", CommProtocol: "gRPC + Kafka"},
		{Name: "analytics-engine", Context: ContextAnalytics, PrimaryStorage: "ClickHouse", CommProtocol: "Kafka Consumer"},
	}
}

func main() {
	fmt.Println("=== Декомпозиция платформы на ограниченные контексты (DDD) ===")
	for i, ms := range GetPlatformMicroservices() {
		fmt.Printf("%d. [%s] %-18s -> База: %-24s (Протокол: %s)\n",
			i+1, ms.Context, ms.Name, ms.PrimaryStorage, ms.CommProtocol)
	}
}
'''
validate_go_code(code2, "Ex 2")
exercises.append({
    "num": 2,
    "title": "Декомпозиция на ограниченные контексты (DDD Bounded Contexts)",
    "task": "Спроектируйте границы микросервисов платформы по принципам Domain-Driven Design: выделите независимые ограниченные контексты (Identity, Billing Core, Inventory, Order Fulfillment, Notification, Analytics) с автономными базами данных (Database-per-Service).",
    "theory": """Главное правило микросервисной архитектуры в HighLoad: **Database-per-Service (База данных на каждый сервис)**.
Общая база данных для нескольких сервисов — это антипаттерн «распределенный монолит», создающий узкое место масштабирования и единую точку отказа.
Декомпозиция по Domain-Driven Design (DDD):
1. **Identity & Access**: Регистрация, аутентификация, выпуск JWT токенов, управление сессиями в Redis.
2. **Billing & Financial Core**: Критический агрегат балансов. CQRS + Event Sourcing. Никаких прямых мутаций баланса извне.
3. **Catalog & Inventory**: Высокоскоростной каталог товаров. Сверхвысокая нагрузка на чтение (95% Read / 5% Write), многоуровневое L1/L2 кэширование.
4. **Order Fulfillment**: Оркестрация жизненного цикла заказа через распределенную Сагу.
5. **Notification Gateway**: Асинхронная отправка пушей, SMS и email с защитой от спама.
6. **Real-time Analytics**: Потоковая OLAP-аналитика в ClickHouse для генерации финансовых отчетов.""",
    "step_by_step": [
        "Определите перечисление ограниченных контекстов `BoundedContext`.",
        "Опишите спецификацию каждого микросервиса `MicroserviceDefinition`.",
        "Закрепите независимое изолированное хранилище за каждым сервисом.",
        "Выведите архитектурную карту в консоль."
    ],
    "code_blocks": [{
        "filename": "bounded_contexts.go",
        "lang": "go",
        "code": code2
    }],
    "under_the_hood": "Изоляция контекстов устраняет распределенные блокировки таблиц. Межсервисное взаимодействие ведется строго по бинарным gRPC-контрактам (для синхронных запросов) и через события Apache Kafka (для асинхронных уведомлений).",
    "pitfalls": "Прямое чтение таблиц чужого микросервиса через SQL JOIN нарушает инкапсуляцию контекста и делает невозможным независимый деплой и рефакторинг сервисов.",
    "bigtech_interview": "Как избежать проблем распределенных транзакций при разделении данных на независимые базы в микросервисах?\nОтвет: Отказаться от распределенного двухфазного коммита (2PC/XA), так как он блокирует ресурсы и не масштабируется. Вместо этого использовать Event-Driven архитектуру: паттерн Saga (хореография или оркестрация) с компенсационными транзакциями и принцип Eventual Consistency (согласованность в конечном счете)."
})

# Ex 3
code3 = r'''package main

import (
	"context"
	"fmt"
)

// Domain Layer: чистые сущности и бизнес-ошибки (не зависят от внешних библиотек)
type AccountID string

type Account struct {
	ID      AccountID
	Balance int64 // в копейках/центах
}

// Port (Repository Interface)
type AccountRepository interface {
	GetByID(ctx context.Context, id AccountID) (*Account, error)
	Save(ctx context.Context, acc *Account) error
}

// UseCase Layer: оркестрация бизнес-сценариев
type TransferUseCase struct {
	repo AccountRepository
}

func NewTransferUseCase(repo AccountRepository) *TransferUseCase {
	return &TransferUseCase{repo: repo}
}

func (uc *TransferUseCase) Deposit(ctx context.Context, id AccountID, amount int64) error {
	if amount <= 0 {
		return fmt.Errorf("сумма пополнения должна быть положительной")
	}

	acc, err := uc.repo.GetByID(ctx, id)
	if err != nil {
		return fmt.Errorf("получение счета: %w", err)
	}

	acc.Balance += amount
	return uc.repo.Save(ctx, acc)
}

// Infrastructure Layer: Mock-адаптер репозитория
type InMemoryAccountRepo struct {
	storage map[AccountID]*Account
}

func (r *InMemoryAccountRepo) GetByID(ctx context.Context, id AccountID) (*Account, error) {
	if acc, ok := r.storage[id]; ok {
		return acc, nil
	}
	return &Account{ID: id, Balance: 0}, nil
}

func (r *InMemoryAccountRepo) Save(ctx context.Context, acc *Account) error {
	r.storage[acc.ID] = acc
	return nil
}

func main() {
	repo := &InMemoryAccountRepo{storage: make(map[AccountID]*Account)}
	useCase := NewTransferUseCase(repo)

	ctx := context.Background()
	_ = useCase.Deposit(ctx, "acc_1001", 50000)

	acc, _ := repo.GetByID(ctx, "acc_1001")
	fmt.Printf("Clean Architecture: Баланс счета %s успешно обновлен: %d коп. (%.2f руб.)\n",
		acc.ID, acc.Balance, float64(acc.Balance)/100.0)
}
'''
validate_go_code(code3, "Ex 3")
exercises.append({
    "num": 3,
    "title": "Проектирование Clean Architecture в кодовой базе каждого микросервиса",
    "task": "Организуйте кодовую базу микросервисов по правилам Clean Architecture / Hexagonal Architecture: разделение на слои domain, usecase, repository (ports & adapters), delivery. Обеспечьте строгое направление зависимостей внутрь к доменному ядру.",
    "theory": """**Clean Architecture (Чистая архитектура)** разделяет код на концентрические слои с Правилом Зависимостей (Dependency Rule):
*Внутренние слои ничего не знают о внешних слоях.*
Структура пакетов микросервиса на Go:
- `cmd/server/main.go`: Точка входа, инициализация DI контейнера, сборка графа зависимостей.
- `internal/domain/`: Сущности (Entities), объекты-значения (Value Objects) и доменные ошибки. Нулевые внешние зависимости!
- `internal/usecase/`: Сценарии использования приложения. Оперируют доменными сущностями через интерфейсы портов (`AccountRepository`, `EventPublisher`).
- `internal/adapter/repository/`: Реализация портов БД (pgx, Redis).
- `internal/adapter/delivery/`: Транспортные адаптеры (gRPC серверы, HTTP хендлеры, Kafka консьюмеры).""",
    "step_by_step": [
        "Определите доменную сущность `Account` без тегов JSON/SQL.",
        "Объявите порт вторичного адаптера `AccountRepository`.",
        "Реализуйте юзкейс `TransferUseCase`, зависящий только от интерфейса репозитория.",
        "Соберите адаптер `InMemoryAccountRepo` и протестируйте сценарий депозита средств."
    ],
    "code_blocks": [{
        "filename": "clean_architecture_core.go",
        "lang": "go",
        "code": code3
    }],
    "under_the_hood": "В Go полиморфизм интерфейсов компилируется в таблицы интерфейсных методов (`itab`). Вызов метода через интерфейс `uc.repo.Save` выполняется через dynamic dispatch с субнаносекундной стоимостью, обеспечивая идеальную тестируемость без ущерба для скорости.",
    "pitfalls": "Импорт внешних библиотек баз данных (`database/sql`, `pgx`) или фреймворков (`gin`, `grpc`) в пакет `internal/domain` категорически запрещен и нарушает Clean Architecture.",
    "bigtech_interview": "Почему в Go интерфейсы рекомендуется объявлять на стороне потребителя (consumer), а не на стороне реализации (producer)?\nОтвет: В соответствии с принципом Interface Segregation (ISP): объявление интерфейса в пакете usecase (`type AccountRepository interface`) гарантирует, что юзкейс требует ровно тот минимальный набор методов, который ему необходим для работы, и не привязывается к монолитным интерфейсам поставщика данных."
})

# Ex 4
code4 = r'''package main

import (
	"errors"
	"fmt"
)

var (
	ErrNegativeAmount  = errors.New("amount must be positive")
	ErrInsufficientFund = errors.New("insufficient funds for withdrawal")
)

// Money представляет финансовую сумму в неделимых базовых единицах (копейки, центы)
// Исключает ошибки округления IEEE-754 чисел с плавающей точкой (float64)
type Money struct {
	amount int64 // неделимые единицы (1 рубль = 100 копеек)
}

func NewMoneyFromSubunits(subunits int64) Money {
	return Money{amount: subunits}
}

func (m Money) Add(other Money) Money {
	return Money{amount: m.amount + other.amount}
}

func (m Money) Sub(other Money) (Money, error) {
	if m.amount < other.amount {
		return Money{}, ErrInsufficientFund
	}
	return Money{amount: m.amount - other.amount}, nil
}

func (m Money) String() string {
	rubles := m.amount / 100
	kopecks := m.amount % 100
	if kopecks < 0 {
		kopecks = -kopecks
	}
	return fmt.Sprintf("%d.%02d", rubles, kopecks)
}

func main() {
	// Демонстрация проблемы float64: 0.1 + 0.2 != 0.3
	var f1, f2 float64 = 0.1, 0.2
	fmt.Printf("Опасность float64: 0.1 + 0.2 = %.17f (потеря точности!)\n", f1+f2)

	// Финансовый тип Money на int64
	m1 := NewMoneyFromSubunits(10) // 10 копеек
	m2 := NewMoneyFromSubunits(20) // 20 копеек
	sum := m1.Add(m2)
	fmt.Printf("Безопасный тип Money: 10 коп + 20 коп = %s руб (абсолютная точность!)\n", sum.String())
}
'''
validate_go_code(code4, "Ex 4")
exercises.append({
    "num": 4,
    "title": "Модель данных финансового ядра: строгие типы и исключение ошибок округления",
    "task": "Спроектируйте финансовый тип данных Money на базе целочисленного типа int64 (хранение в минимальных неделимых единицах — копейках/центах). Докажите абсолютную точность арифметических операций и невозможность накопления ошибок округления, характерных для float64.",
    "theory": """Золотое правило финансовой инженерии: **ДЕНЬГИ НИКОГДА НЕ ХРАНЯТСЯ В ТИПАХ FLOAT32/FLOAT64!**
В стандарте IEEE 754 числа с плавающей точкой хранятся в двоичной системе.
Простейшие десятичные дроби (0.1, 0.2) не могут быть точно представлены в двоичном виде, порождая бесконечную периодическую дробь:
`0.1 + 0.2 = 0.30000000000000004`
При миллионах транзакций накапливающаяся погрешность приводит к расхождению бухгалтерских балансов на сотни тысяч рублей.
Два стандартных решения:
1. **Хранение в неделимых единицах (Subunits)**: Копейки, центы, сатоши в типе `int64`. Для 99% банковских систем диапазона `int64` ($9 \\times 10^{18}$ копеек = 92 квадриллиона рублей) хватает с колоссальным запасом.
2. **Fixed-Point Decimal**: Библиотека `shopspring/decimal` для сверхвысокой точности (криптобиржи, доли процентов).""",
    "step_by_step": [
        "Определите неизменяемую структуру `Money` с приватным полем `amount int64`.",
        "Реализуйте методы `Add` и `Sub` с контролем отрицательных остатков.",
        "Реализуйте форматированный вывод `String()` с выделением целой и дробной части.",
        "Продемонстрируйте разницу между float64 и Money в main."
    ],
    "code_blocks": [{
        "filename": "money_type.go",
        "lang": "go",
        "code": code4
    }],
    "under_the_hood": "Целочисленная арифметика `int64` исполняется процессором за 1 такт тактовой частоты (инструкции ADD/SUB) в регистрах общего назначения (RAX, RBX), в то время как операции с плавающей точкой требуют обращения к блокам FPU/SSE, работая медленнее и подвергаясь ошибкам потери значимости.",
    "pitfalls": "Использование типа `int` вместо `int64` опасно: на 32-битных архитектурах размер `int` составит 32 бита, что приведет к переполнению баланса уже при достижении суммы в 21 миллион рублей.",
    "bigtech_interview": "Как в реляционной базе данных PostgreSQL хранить денежные суммы для финансового сервиса на Go?\nОтвет: Либо в поле `BIGINT` (хранение в копейках/центах, что идеально мапится на `int64` в Go без каких-либо конвертаций), либо в типе `NUMERIC(18, 4)` / `DECIMAL` для поддержки долей копеек при начислении сложных процентов."
})

# Ex 5
code5 = r'''package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
)

var (
	ErrVersionMismatch = errors.New("optimistic concurrency conflict: version mismatch")
)

type AccountEvent struct {
	AccountID string
	Version   int64
	EventType string // "AccountOpened", "MoneyDeposited", "MoneyWithdrawn"
	Amount    int64
}

type EventSourcedAccount struct {
	ID      string
	Version int64
	Balance int64
}

func (a *EventSourcedAccount) Apply(event AccountEvent) {
	switch event.EventType {
	case "AccountOpened":
		a.ID = event.AccountID
	case "MoneyDeposited":
		a.Balance += event.Amount
	case "MoneyWithdrawn":
		a.Balance -= event.Amount
	}
	a.Version = event.Version
}

type EventStore struct {
	mu     sync.Mutex
	events map[string][]AccountEvent
}

func NewEventStore() *EventStore {
	return &EventStore{events: make(map[string][]AccountEvent)}
}

func (s *EventStore) AppendEvents(ctx context.Context, accountID string, expectedVersion int64, newEvents []AccountEvent) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	currentEvents := s.events[accountID]
	currentVersion := int64(len(currentEvents))

	if currentVersion != expectedVersion {
		return fmt.Errorf("%w: expected %d, but current is %d", ErrVersionMismatch, expectedVersion, currentVersion)
	}

	for i, e := range newEvents {
		e.Version = currentVersion + int64(i) + 1
		s.events[accountID] = append(s.events[accountID], e)
	}
	return nil
}

func main() {
	store := NewEventStore()
	ctx := context.Background()

	// 1. Открытие счета и пополнение
	_ = store.AppendEvents(ctx, "acc_42", 0, []AccountEvent{
		{AccountID: "acc_42", EventType: "AccountOpened"},
		{AccountID: "acc_42", EventType: "MoneyDeposited", Amount: 10000},
	})

	// 2. Воспроизведение состояния из истории событий
	acc := &EventSourcedAccount{}
	for _, ev := range store.events["acc_42"] {
		acc.Apply(ev)
	}

	fmt.Printf("Event Sourcing: Восстановлен счет %s | Баланс: %d коп. | Версия: %d\n",
		acc.ID, acc.Balance, acc.Version)
}
'''
validate_go_code(code5, "Ex 5")
exercises.append({
    "num": 5,
    "title": "CQRS и Event Sourcing в сервисе балансов: ядро финансовых транзакций",
    "task": "Реализуйте финансовый агрегат на базе паттерна Event Sourcing: состояние баланса воспроизводится путем применения потока неизменяемых событий (Append-Only Event Store), а конкурентные изменения защищаются оптимистической блокировкой версий (Expected Version Check).",
    "theory": """В классической модели баз данных (CRUD) баланс хранится как текущее число: `UPDATE accounts SET balance = balance + 100`.
Проблемы CRUD в банках:
- Потеря аудиторского следа: невозможно доказать, кто, когда и по какой причине изменил баланс.
- Уязвимость к гонкам данных при параллельных списаниях.
**Event Sourcing (Событийное порождение)**:
1. Состояние никогда не перезаписывается. Все изменения фиксируются в виде непрерывного потока событий: `AccountOpened`, `MoneyDeposited`, `MoneyWithdrawn`.
2. Текущий баланс — это левая свертка (Fold/Reduce) всех исторических событий от начала времен.
3. **Оптимистическая блокировка (Optimistic Locking)**: При сохранении нового события проверяется версия: `expected_version == current_version`. Если два запроса попытались списать деньги одновременно, первый побеждает, а второй падает с конфликтом версий, предотвращая двойное списание.""",
    "step_by_step": [
        "Определите структуру события `AccountEvent` и агрегата `EventSourcedAccount`.",
        "Реализуйте чистую функцию `Apply(event)` для мутации состояния агрегата.",
        "Создайте хранилище `EventStore` с проверкой ожидаемой версии `expectedVersion`.",
        "Продемонстрируйте воспроизведение баланса из потока событий."
    ],
    "code_blocks": [{
        "filename": "event_sourcing_core.go",
        "lang": "go",
        "code": code5
    }],
    "under_the_hood": "В PostgreSQL Event Store реализуется таблицей с ограничением `UNIQUE(account_id, version)`. При попытке двух параллельных транзакций вставить событие с одинаковой версией PostgreSQL автоматически выбрасывает ошибку `unique_violation (23505)`, гарантируя невозможность race condition на уровне движка СУБД.",
    "pitfalls": "Выполнение внешних побочных эффектов (отправка email или вызов платежного шлюза) внутри метода `Apply()` категорически запрещено: этот метод вызывается заново при каждом воспроизведении истории из базы данных.",
    "bigtech_interview": "Как решать проблему медленного восстановления состояния в Event Sourcing, если у клиента накопилось более 50 000 событий?\nОтвет: Через механизм Снимков Состояния (Snapshots). Каждые $N$ событий (например, каждые 100 событий) фоновый процесс сохраняет готовый снимок текущего баланса в отдельную таблицу. При чтении агрегат загружает последний снапшот и накатывает поверх только те события, которые произошли после момента создания снимка."
})

# Ex 6
code6 = r'''package main

import (
	"context"
	"fmt"
	"sync"
)

type AccountSnapshot struct {
	AccountID string
	Version   int64
	Balance   int64
}

type SnapshotRepository struct {
	mu        sync.RWMutex
	snapshots map[string]AccountSnapshot
}

func NewSnapshotRepository() *SnapshotRepository {
	return &SnapshotRepository{snapshots: make(map[string]AccountSnapshot)}
}

func (r *SnapshotRepository) SaveSnapshot(ctx context.Context, snap AccountSnapshot) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.snapshots[snap.AccountID] = snap
}

func (r *SnapshotRepository) GetLatestSnapshot(ctx context.Context, accountID string) (AccountSnapshot, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	snap, ok := r.snapshots[accountID]
	return snap, ok
}

func main() {
	snapRepo := NewSnapshotRepository()
	ctx := context.Background()

	// Сохранение снимка состояния на версии 100
	snapRepo.SaveSnapshot(ctx, AccountSnapshot{
		AccountID: "acc_9988",
		Version:   100,
		Balance:   750000, // 7500 руб.
	})

	latest, found := snapRepo.GetLatestSnapshot(ctx, "acc_9988")
	fmt.Printf("Снимок состояния найден: %t | Счет: %s | Баланс: %d коп. | Версия: %d\n",
		found, latest.AccountID, latest.Balance, latest.Version)
}
'''
validate_go_code(code6, "Ex 6")
exercises.append({
    "num": 6,
    "title": "Периодические снимки балансов (Snapshots) и кэширование L1",
    "task": "Реализуйте репозиторий снимков состояния (Snapshots) для оптимизации загрузки Event Sourced агрегатов: сохранение снапшота каждые N событий и восстановление баланса со сложностью O(1) независимо от общей длины истории.",
    "theory": """Если счет активного пользователя существует несколько лет и накопил 100 000 транзакций, вычитывание всех 100 000 строк из таблицы `account_events` при каждом запросе баланса вызовет недопустимую задержку (сотни миллисекунд) и нагрузит память базы данных.
Паттерн **Snapshots (Снимки состояния)**:
1. При сохранении очередного события проверяется условие: `if event.Version % SnapshotInterval == 0`.
2. Если условие выполнено, сериализованное состояние агрегата сохраняется в таблицу `account_snapshots(account_id, version, balance, timestamp)`.
3. При запросе баланса:
   - Извлекается последний снимок состояния (1 чтение по первичному ключу).
   - Из таблицы событий извлекаются только события с `version > snapshot.version`.
   - Если интервал равен 100, агрегат накатывает максимум 99 событий, восстанавливаясь за < 1 мс.""",
    "step_by_step": [
        "Определите структуру `AccountSnapshot`.",
        "Реализуйте потокобезопасный репозиторий `SnapshotRepository` с методами `SaveSnapshot` и `GetLatestSnapshot`.",
        "Организуйте проверку наличия снимка перед загрузкой событий.",
        "Продемонстрируйте мгновенную загрузку снимка состояния."
    ],
    "code_blocks": [{
        "filename": "snapshots_repo.go",
        "lang": "go",
        "code": code6
    }],
    "under_the_hood": "Снимки состояния могут сохраняться асинхронно в фоновой горутине через канал, чтобы не увеличивать латентность основной транзакции записи события.",
    "pitfalls": "Если сохранить снапшот с версией 100, но транзакция записи самого события 100 откатится, снапшот окажется неконсистентным. Сохранение снапшота должно производиться строго после успешного коммита событий.",
    "bigtech_interview": "Где эффективнее хранить снапшоты в распределенной архитектуре: в PostgreSQL или в Redis?\nОтвет: Оптимальна гибридная схема: мастер-копия снапшота хранится в PostgreSQL (персистентность и надежность), а горячая копия кэшируется в Redis со временем жизни TTL (например, 1 час). Это позволяет проверять баланс при авторизации транзакций за 0.5 мс прямо из кэша."
})

# Ex 7
code7 = r'''package main

import (
	"context"
	"fmt"
	"time"
)

type OutboxMessage struct {
	ID        string
	Topic     string
	Payload   string
	CreatedAt time.Time
	Published bool
}

// SQLOutboxSimulation демонстрирует атомарную запись бизнес-события в рамках транзакции БД
const SQLOutboxTransaction = `
BEGIN;

-- 1. Списание баланса
UPDATE accounts SET balance = balance - 500 WHERE id = 'acc_1' AND balance >= 500;

-- 2. Запись в Outbox таблицу в той же транзакции
INSERT INTO outbox_messages (id, topic, payload, created_at, published)
VALUES (gen_random_uuid(), 'payments.events', '{"account_id":"acc_1","amount":500}', NOW(), FALSE);

COMMIT;
`

func main() {
	fmt.Println("=== Паттерн Transactional Outbox ===")
	fmt.Println("Гарантирует атомарность: событие гарантированно попадет в брокер Kafka,")
	fmt.Println("только если финансовая транзакция в базе данных успешно закоммичена.")
	fmt.Printf("Размер DDL транзакции: %d байт\n", len(SQLOutboxTransaction))
}
'''
validate_go_code(code7, "Ex 7")
exercises.append({
    "num": 7,
    "title": "Паттерн Transactional Outbox для гарантированной публикации в Kafka",
    "task": "Спроектируйте реализацию паттерна Transactional Outbox для гарантированной публикации финансовых событий в Apache Kafka без риска рассинхронизации базы данных и брокера сообщений (Dual-Write Problem).",
    "theory": """Классическая ошибка начинающих инженеров — **Dual Write (Двойная запись)**:
```go
tx.Commit()               // 1. Успешно списали деньги в БД
kafkaProducer.Publish()   // 2. Сеть моргнула, брокер недоступен!
```
Итог: Деньги со счета списаны, но сообщение в Kafka не ушло. Сервис заказов не узнал об оплате, товар не отправлен, клиент в ярости.
Попытка поменять порядок (сначала публикация в Kafka, потом Commit) еще опаснее: если Commit упадет, клиент получит бесплатный товар!
**Паттерн Transactional Outbox**:
1. В реляционной БД создается служебная таблица `outbox_messages`.
2. Бизнес-мутация и вставка сообщения в `outbox_messages` выполняются **в единой ACID-транзакции PostgreSQL**.
3. Фоновый воркер на Go (Outbox Relay) считывает непомеченные записи (`published = FALSE`) с помощью `SELECT ... FOR UPDATE SKIP LOCKED`, отправляет их в Kafka и помечает как опубликованные.
4. Результат: 100% гарантия At-Least-Once доставки событий в Kafka!""",
    "step_by_step": [
        "Определите структуру `OutboxMessage`.",
        "Спроектируйте атомарный SQL-транзакционный блок с одновременным списанием и вставкой в outbox.",
        "Опишите механику работы фонового воркера публикации.",
        "Выведите спецификацию надежности."
    ],
    "code_blocks": [{
        "filename": "transactional_outbox.go",
        "lang": "go",
        "code": code7
    }],
    "under_the_hood": "Конструкция `FOR UPDATE SKIP LOCKED` в PostgreSQL позволяет масштабировать Outbox воркеры на несколько параллельных реплик без взаимных блокировок: каждый воркер мгновенно захватывает пачку свободных строк, пропуская уже заблокированные другими воркерами строки.",
    "pitfalls": "Накопление миллионов старых записей в таблице outbox_messages приведет к разрастанию таблицы (Table Bloat) и замедлению сканирования. Необходима регулярная очистка опубликованных сообщений через партиционирование по дням или удаление пачками.",
    "bigtech_interview": "В чем преимущество связки Transactional Outbox + Debezium (CDC) перед опросом таблицы через SELECT FOR UPDATE SKIP LOCKED?\nОтвет: Опрос через SELECT генерирует постоянную нагрузку на CPU базы данных (polling overhead). Debezium вычитывает события напрямую из журнала предзаписи PostgreSQL (Write-Ahead Log, WAL) через протокол логической репликации без выполнения SQL-запросов к таблице, обеспечивая нулевую задержку публикации и нулевую нагрузку на ядро СУБД."
})

# Ex 8
code8 = r'''package main

import (
	"fmt"
	"hash/fnv"
)

type KafkaTopicConfig struct {
	Name              string
	PartitionsCount   int
	ReplicationFactor int
	CleanupPolicy     string
}

// ComputePartitionByKey вычисляет целевую партицию по бизнес-ключу (AccountID / OrderID)
// гарантируя строгую последовательность событий по конкретному объекту
func ComputePartitionByKey(key string, totalPartitions int) int {
	h := fnv.New32a()
	_, _ = h.Write([]byte(key))
	return int(h.Sum32() % uint32(totalPartitions))
}

func main() {
	topics := []KafkaTopicConfig{
		{Name: "payments.events", PartitionsCount: 16, ReplicationFactor: 3, CleanupPolicy: "delete"},
		{Name: "orders.events", PartitionsCount: 16, ReplicationFactor: 3, CleanupPolicy: "delete"},
		{Name: "catalog.snapshots", PartitionsCount: 8, ReplicationFactor: 3, CleanupPolicy: "compact"},
	}

	fmt.Println("=== Топология топиков Apache Kafka ===")
	for _, t := range topics {
		fmt.Printf("Топик: %-18s | Партиций: %2d | Фактор репликации: %d | Политика: %s\n",
			t.Name, t.PartitionsCount, t.ReplicationFactor, t.CleanupPolicy)
	}

	acc := "acc_9981"
	p := ComputePartitionByKey(acc, 16)
	fmt.Printf("Все финансовые события аккаунта %s гарантированно направляются в партицию: #%d\n", acc, p)
}
'''
validate_go_code(code8, "Ex 8")
exercises.append({
    "num": 8,
    "title": "Топология топиков и партиционирование в Apache Kafka",
    "task": "Спроектируйте топологию топиков Kafka для HighLoad платформы: настройка количества партиций для параллельной обработки, фактор репликации RF=3 для отказоустойчивости и детерминированное шардирование по бизнес-ключам (AccountID) для сохранения строгого порядка событий.",
    "theory": """Kafka гарантирует строгий порядок сообщений **ТОЛЬКО В РАМКАХ ОДНОЙ ПАРТИЦИИ**.
Если отправлять события финансового аккаунта в разные партиции топика случайным образом (Round-Robin), событие снятия денег может быть прочитано консьюмером *раньше*, чем событие их зачисления!
**Правило партиционирования по ключу (Key-Based Partitioning)**:
- В качестве ключа сообщения (`kafka.Message.Key`) передается уникальный идентификатор финансового агрегата (`account_id` или `order_id`).
- Продюсер вычисляет хэш от ключа: `partition = Murmur2(key) % num_partitions`.
- Все события одного и того же счета строго попадают в одну и ту же партицию и обрабатываются одним и тем же консьюмером последовательно, исключая race conditions.""",
    "step_by_step": [
        "Определите структуру конфигурации топика `KafkaTopicConfig`.",
        "Реализуйте функцию вычисления партиции по хэшу ключа `ComputePartitionByKey`.",
        "Спроектируйте топологию топиков с фактором репликации 3 для исключения потери данных при падении брокера.",
        "Продемонстрируйте детерминированную привязку аккаунта к партиции."
    ],
    "code_blocks": [{
        "filename": "kafka_topology.go",
        "lang": "go",
        "code": code8
    }],
    "under_the_hood": "При изменении количества партиций в существующем топике хэш-функция перераспределяет ключи по другим партициям. Поэтому количество партиций для высоконагруженных топиков рассчитывается заранее с запасом на 2-3 года вперед.",
    "pitfalls": "Отправка сообщений с пустым ключом (`Key: nil`) включает балансировку Round-Robin, что гарантированно приведет к нарушению порядка финансовых проводок.",
    "bigtech_interview": "Как рассчитать оптимальное количество партиций для топика с целевой нагрузкой 100 000 сообщений в секунду?\nОтвет: По формуле $P = \\max(TargetRPS / ProducerThroughput, TargetRPS / ConsumerThroughput)$. Если один консьюмер на Go с записью в БД обрабатывает 5 000 сообщений/сек, то для обработки 100 000 RPS необходимо минимум $100000 / 5000 = 20$ партиций. С запасом выбирают 24 или 32 партиции."
})

# Ex 9
code9 = r'''package main

import (
	"context"
	"fmt"
	"sync"
)

type InboxConsumer struct {
	mu           sync.Mutex
	processedIDs map[string]bool // в продакшене — таблица processed_messages в PostgreSQL
}

func NewInboxConsumer() *InboxConsumer {
	return &InboxConsumer{processedIDs: make(map[string]bool)}
}

// ProcessMessageExactlyOnce реализует паттерн Transactional Inbox
func (c *InboxConsumer) ProcessMessageExactlyOnce(ctx context.Context, messageID, payload string) (bool, error) {
	c.mu.Lock()
	defer c.mu.Unlock()

	// 1. Проверка идемпотентности
	if c.processedIDs[messageID] {
		// Сообщение уже было обработано ранее (дубликат Kafka) — пропускаем без ошибок
		return false, nil
	}

	// 2. Исполнение бизнес-логики (в транзакции с вставкой messageID)
	// Имитация применения заказа
	c.processedIDs[messageID] = true
	return true, nil
}

func main() {
	inbox := NewInboxConsumer()
	ctx := context.Background()

	msgID := "msg_kafka_unique_991"

	// Первичная обработка
	firstRun, _ := inbox.ProcessMessageExactlyOnce(ctx, msgID, "OrderCreated")
	// Повторная доставка того же сообщения (например, после ребалансировки консьюмер-группы)
	secondRun, _ := inbox.ProcessMessageExactlyOnce(ctx, msgID, "OrderCreated")

	fmt.Printf("Первичная обработка сообщения: применено = %t (ожидается true)\n", firstRun)
	fmt.Printf("Повторная обработка дубликата: применено = %t (ожидается false, дубликат отсечен!)\n", secondRun)
}
'''
validate_go_code(code9, "Ex 9")
exercises.append({
    "num": 9,
    "title": "Идемпотентный консьюмер сообщений (Transactional Inbox Pattern)",
    "task": "Реализуйте паттерн Transactional Inbox для консьюмера Apache Kafka: обеспечение семантики ровно однократной обработки (Exactly-Once Semantics at Application Level) при гарантированной доставке At-Least-Once со стороны брокера.",
    "theory": """Apache Kafka в распределенном кластере обеспечивает семантику доставки **At-Least-Once (Как минимум один раз)**:
Если воркер обработал сообщение и обновил базу данных, но упал до отправки коммита смещения (Commit Offset) в Kafka, брокер передаст это же сообщение другому воркеру после ребалансировки группы.
Без защиты клиент получит двойное списание денег!
**Паттерн Transactional Inbox**:
1. В базе данных консьюмера создается таблица: `processed_messages (message_id VARCHAR(128) PRIMARY KEY, processed_at TIMESTAMPTZ)`.
2. При получении сообщения открывается локальная транзакция базы данных:
   ```sql
   INSERT INTO processed_messages (message_id) VALUES ($1);
   -- Если запись уже существует, транзакция падает с ошибкой уникальности primary key
   UPDATE orders SET status = 'PAID' WHERE id = $2;
   COMMIT;
   ```
3. Если транзакция зафиксировала дубликат, консьюмер коммитит офсет в Kafka и игнорирует повтор без каких-либо побочных эффектов.""",
    "step_by_step": [
        "Определите структуру `InboxConsumer` с реестром обработанных идентификаторов сообщений.",
        "Реализуйте метод `ProcessMessageExactlyOnce` с детекцией дубликатов.",
        "Обеспечьте потокобезопасность через `sync.Mutex`.",
        "Проверьте игнорирование повторно доставленного сообщения."
    ],
    "code_blocks": [{
        "filename": "transactional_inbox.go",
        "lang": "go",
        "code": code9
    }],
    "under_the_hood": "Поскольку вставка `message_id` и бизнес-изменения происходят внутри одной транзакции PostgreSQL, они неразрывно связаны: либо применятся оба действия, либо ни одно из них, что исключает рассинхронизацию даже при отключении питания сервера.",
    "pitfalls": "Использование внешнего кэша Redis для проверки `EXISTS message_id` без транзакционной связи с PostgreSQL опасно: сбой между проверкой Redis и записью в Postgres приведет к потере сообщения.",
    "bigtech_interview": "Почему Kafka 'Transactional Producer' (Exactly-Once Semantics в Kafka) не решает проблему идемпотентности во внешних базах данных?\nОтвет: Механизм транзакций Kafka (EOS) работает строго внутри контура самой Kafka (чтение из одного топика и запись в другой топик). Как только консьюмер начинает выполнять запись во внешнюю систему (PostgreSQL, Elastic, сторонний API), гарантии Kafka заканчиваются. Единственный способ обеспечить Exactly-Once для внешнего хранилища — паттерн Transactional Inbox или идемпотентные ключи обновления."
})

# Ex 10
code10 = r'''package main

import (
	"context"
	"errors"
	"fmt"
)

type SagaStep string

const (
	StepReserveInventory SagaStep = "ReserveInventory"
	StepDebitBalance     SagaStep = "DebitBalance"
	StepCreateShipment   SagaStep = "CreateShipment"
)

type OrderSagaOrchestrator struct{}

func (s *OrderSagaOrchestrator) ExecuteOrder(ctx context.Context, orderID string, simulateFailureAtStep SagaStep) error {
	fmt.Printf("--- Старт Саги оформления заказа %s ---\n", orderID)

	// Шаг 1: Резерв товара
	fmt.Println("1. [Action] Резервация товара на складе: УСПЕХ")

	// Шаг 2: Списание средств
	if simulateFailureAtStep == StepDebitBalance {
		fmt.Println("2. [Action] Списание средств с баланса: ОШИБКА (недостаточно средств!)")
		s.compensateInventory(orderID)
		return errors.New("saga aborted at StepDebitBalance")
	}
	fmt.Println("2. [Action] Списание средств: УСПЕХ")

	// Шаг 3: Доставка
	if simulateFailureAtStep == StepCreateShipment {
		fmt.Println("3. [Action] Создание доставки: ОШИБКА курьерской службы!")
		s.compensateBalance(orderID)
		s.compensateInventory(orderID)
		return errors.New("saga aborted at StepCreateShipment")
	}
	fmt.Println("3. [Action] Передача в доставку: УСПЕХ")

	fmt.Printf("Сага %s успешно завершена!\n", orderID)
	return nil
}

func (s *OrderSagaOrchestrator) compensateInventory(orderID string) {
	fmt.Printf("   [COMPENSATION] Отмена резерва товара на складе для заказа %s: УСПЕХ\n", orderID)
}

func (s *OrderSagaOrchestrator) compensateBalance(orderID string) {
	fmt.Printf("   [COMPENSATION] Возврат списанных средств на баланс для заказа %s: УСПЕХ\n", orderID)
}

func main() {
	orchestrator := &OrderSagaOrchestrator{}
	ctx := context.Background()

	_ = orchestrator.ExecuteOrder(ctx, "ORD-771", StepCreateShipment)
}
'''
validate_go_code(code10, "Ex 10")
exercises.append({
    "num": 10,
    "title": "Распределенная Сага (Saga Orchestrator) для оформления заказа",
    "task": "Реализуйте распределенную транзакцию покупки товара на базе паттерна Saga Orchestrator: последовательное выполнение прямых шагов (Резерв склада -> Списание средств -> Доставка) и гарантированный запуск компенсационных транзакций в обратном порядке при возникновении сбоя.",
    "theory": """В распределенной микросервисной архитектуре транзакция покупки затрагивает минимум 3 независимых сервиса с разными базами данных:
1. `Inventory Service` (резерв товара).
2. `Billing Service` (списание денег).
3. `Delivery Service` (курьерская доставка).
Если списание денег прошло успешно, но курьерская служба вернула отказ, система обязана вернуть деньги и снять резерв товара.
**Паттерн Saga (Оркестрация)**:
- Центральный координатор (Saga Orchestrator) управляет конечным автоматом состояний.
- Каждый прямой шаг имеет парное **компенсационное действие (Compensating Transaction)**:
  - Прямое: `ReserveInventory()` $\\rightarrow$ Компенсация: `ReleaseInventory()`.
  - Прямое: `DebitBalance()` $\\rightarrow$ Компенсация: `RefundBalance()`.
- При любой ошибке оркестратор вызывает компенсации строго в обратном порядке для всех ранее завершенных шагов.""",
    "step_by_step": [
        "Определите перечисление шагов Саги `SagaStep`.",
        "Реализуйте координатор `OrderSagaOrchestrator`.",
        "Смоделируйте аварийную ситуацию на третьем шаге (`StepCreateShipment`).",
        "Продемонстрируйте каскадный запуск компенсаций `compensateBalance` и `compensateInventory`."
    ],
    "code_blocks": [{
        "filename": "saga_orchestrator.go",
        "lang": "go",
        "code": code10
    }],
    "under_the_hood": "Компенсационные транзакции обязаны быть семантически идемпотентными: при падении сети оркестратор может повторить вызов `ReleaseInventory()` несколько раз, и каждый повторный вызов должен завершаться успешно без искажения остатков на складе.",
    "pitfalls": "Попытка отката через классический SQL ROLLBACK невозможна: локальные транзакции на складе и в банке уже закоммичены в своих независимых базах данных. Единственный способ отката — компенсационное бизнес-действие.",
    "bigtech_interview": "В чем отличие Саги на основе оркестрации (Orchestration) от Саги на основе хореографии (Choreography)?\nОтвет: В хореографии нет единого координатора: сервисы слушают события Kafka и сами решают, когда инициировать следующий шаг. Это приводит к размытию бизнес-логики и сложности трассировки ('Спагетти событий'). В оркестрации выделенный сервис-оркестратор явно управляет потоком шагов и компенсаций через State Machine, что обеспечивает 100% прозрачность и наблюдаемость."
})

# Ex 11
code11 = r'''package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

type CatalogProduct struct {
	ID    string
	Title string
	Price int64
}

// TwoLevelCache реализует L1 (In-Memory) + L2 (Redis simulation)
type TwoLevelCache struct {
	mu      sync.RWMutex
	l1Cache map[string]CatalogProduct
	l2Cache map[string]CatalogProduct
}

func NewTwoLevelCache() *TwoLevelCache {
	return &TwoLevelCache{
		l1Cache: make(map[string]CatalogProduct),
		l2Cache: make(map[string]CatalogProduct),
	}
}

func (c *TwoLevelCache) GetProduct(ctx context.Context, id string) (CatalogProduct, string) {
	c.mu.RLock()
	// Проверка L1
	if p, ok := c.l1Cache[id]; ok {
		c.mu.RUnlock()
		return p, "HIT L1 (Local RAM, 0.05ms)"
	}
	c.mu.RUnlock()

	// Проверка L2
	c.mu.RLock()
	if p, ok := c.l2Cache[id]; ok {
		c.mu.RUnlock()
		// Прогрев L1
		c.mu.Lock()
		c.l1Cache[id] = p
		c.mu.Unlock()
		return p, "HIT L2 (Redis Cluster, 1.2ms)"
	}
	c.mu.RUnlock()

	// Промах кэша — загрузка из PostgreSQL
	dbProduct := CatalogProduct{ID: id, Title: "MacBook Pro M3 Max", Price: 35000000}
	c.mu.Lock()
	c.l2Cache[id] = dbProduct
	c.l1Cache[id] = dbProduct
	c.mu.Unlock()

	return dbProduct, "MISS (PostgreSQL DB, 25ms)"
}

func main() {
	cache := NewTwoLevelCache()
	ctx := context.Background()

	p1, s1 := cache.GetProduct(ctx, "prod_101")
	p2, s2 := cache.GetProduct(ctx, "prod_101")

	fmt.Printf("1-й запрос: %s -> Статус: %s\n", p1.Title, s1)
	fmt.Printf("2-й запрос: %s -> Статус: %s\n", p2.Title, s2)
}
'''
validate_go_code(code11, "Ex 11")
exercises.append({
    "num": 11,
    "title": "Двухуровневое кэширование L1/L2 для каталога товаров",
    "task": "Спроектируйте архитектуру высокопроизводительного двухуровневого кэша (L1 In-Memory + L2 Redis Cluster) для сервиса каталога товаров с прогревом L1 при попадании в L2 и защитой базы данных от пробоя кэша.",
    "theory": """В каталоге интернет-магазина соотношение нагрузки составляет 95% чтений к 5% записей.
Обращение в Redis по сети на каждый из 100 000 RPS создает огромный сетевой трафик (100k TCP RTT/сек нагружают сетевой стек и Redis CPU).
**Двухуровневый кэш (L1/L2 Cache Architecture)**:
1. **L1 (Local RAM Cache)**: Располагается прямо внутри оперативной памяти пода Go (библиотеки Ristretto или FreeCache).
   - Задержка: 50–100 наносекунд.
   - Нулевые сетевые вызовы. Покрывает 85–90% всех запросов к топ-товарам.
2. **L2 (Distributed Redis Cluster)**: Общий распределенный кэш для сотен подов.
   - Задержка: 1–2 миллисекунды.
   - Хранит миллионы товаров, не помещающихся в оперативку одного пода.
3. При промахе L1 запрос идет в L2; при попадании в L2 значение автоматически кэшируется в локальный L1.""",
    "step_by_step": [
        "Определите структуру `TwoLevelCache` с мапами L1 и L2.",
        "Реализуйте метод `GetProduct` с каскадной проверкой L1 -> L2 -> PostgreSQL.",
        "Обеспечьте автоматическое заполнение L1 при попадании в L2.",
        "Продемонстрируйте ускорение ответа во втором запросе."
    ],
    "code_blocks": [{
        "filename": "two_level_cache.go",
        "lang": "go",
        "code": code11
    }],
    "under_the_hood": "Чтение из локальной памяти L1 не покидает процессорного сокета, обращаясь напрямую к L3 Cache процессора и оперативной памяти через шину DDR5 со скоростью до 80 ГБ/сек.",
    "pitfalls": "Без механизма распределенной инвалидации локальный кэш L1 на разных подах будет показывать разную устаревшую цену товара при ее изменении.",
    "bigtech_interview": "Как защитить базу данных от Cache Stampede (Dog-piling), когда при истечении TTL горячего товара 10 000 параллельных запросов одновременно идут в PostgreSQL?\nОтвет: С помощью паттерна Singleflight (пакет `golang.org/x/sync/singleflight`). Метод `Group.Do(key, fn)` подавляет дубликаты: только один запрос идет в базу данных, а остальные 9 999 запросов блокируются и ожидают единого результата первой горутины, снижая нагрузку на БД ровно в 10 000 раз."
})

# Ex 12
code12 = r'''package main

import (
	"context"
	"fmt"
	"sync"
)

type InvalidationMessage struct {
	ProductID string
	Action    string // "PURGE", "UPDATE"
}

type NodeLocalCache struct {
	nodeID string
	mu     sync.Mutex
	items  map[string]string
}

func (n *NodeLocalCache) Invalidate(productID string) {
	n.mu.Lock()
	defer n.mu.Unlock()
	delete(n.items, productID)
	fmt.Printf("[Node %s]: товар %s удален из L1 кэша\n", n.nodeID, productID)
}

func main() {
	nodes := []*NodeLocalCache{
		{nodeID: "pod-1", items: map[string]string{"prod_99": "Ноутбук"}},
		{nodeID: "pod-2", items: map[string]string{"prod_99": "Ноутбук"}},
		{nodeID: "pod-3", items: map[string]string{"prod_99": "Ноутбук"}},
	}

	msg := InvalidationMessage{ProductID: "prod_99", Action: "PURGE"}
	fmt.Printf("Публикация в Redis Pub/Sub шину: товар %s изменен менеджером!\n", msg.ProductID)

	// Все поды синхронно получают широковещательное уведомление
	for _, node := range nodes {
		node.Invalidate(msg.ProductID)
	}

	fmt.Println("Когерентность L1 кэшей по всем репликам в кластере восстановлена за 3 мс.")
}
'''
validate_go_code(code12, "Ex 12")
exercises.append({
    "num": 12,
    "title": "Распределенная инвалидация кэшей через Redis Pub/Sub",
    "task": "Спроектируйте механизм когерентности многоуровневых кэшей: при обновлении цены или остатка товара сервис публикует событие в Redis Pub/Sub, и все распределенные реплики в Kubernetes вычищают устаревший ключ из своего локального L1-кэша.",
    "theory": """Фундаментальная проблема локального кэша L1: **Рассинхронизация реплик (Cache Drift)**.
В Kubernetes запущено 50 подов каталога. Менеджер изменил цену товара со 100 000 руб. на 80 000 руб.
Под №1 обновил базу и L2 Redis. Но поды №2..№50 продолжают отдавать старую цену из своей локальной памяти L1!
**Архитектура распределенной инвалидации**:
1. При изменении данных сервис отправляет в Redis команду `PUBLISH cache:invalidate:products "prod_99"`.
2. Каждый под платформы при старте открывает постоянную фоновую горутину, слушающую канал `SUBSCRIBE cache:invalidate:products`.
3. При получении идентификатора товара под мгновенно удаляет его из своего локального L1 кэша (`delete(l1Cache, id)`).
4. Задержка распространения инвалидации по всему кластеру составляет 1–5 миллисекунд!""",
    "step_by_step": [
        "Определите структуру сообщения инвалидации `InvalidationMessage`.",
        "Реализуйте метод `Invalidate` у локального узла `NodeLocalCache`.",
        "Смоделируйте широковещательную рассылку события через шину Pub/Sub.",
        "Докажите очистку устаревших данных на всех подах."
    ],
    "code_blocks": [{
        "filename": "cache_invalidation_pubsub.go",
        "lang": "go",
        "code": code12
    }],
    "under_the_hood": "Redis Pub/Sub работает по принципу 'Fire and Forget' в памяти без сохранения сообщений на диск, что обеспечивает задержку публикации менее 100 микросекунд на стороне сервера Redis.",
    "pitfalls": "Если один из подов временно потерял связь с Redis, он пропустит Pub/Sub сообщения инвалидации. Поэтому ключи в L1 всегда обязаны иметь жесткий TTL (например, 60 секунд) как страховку от вечного рассинхрона.",
    "bigtech_interview": "В чем преимущество протокола Redis Client-Side Caching (RESP3 BCAST) перед классическим Redis Pub/Sub?\nОтвет: В RESP3 встроен серверный трекинг инвалидации (Client-Side Caching Tracking): сервер Redis сам запоминает, какие ключи запрашивал данный клиент, и автоматически отправляет пуш-уведомление об инвалидации только тем клиентам, которые реально закэшировали этот ключ, снижая объем широковещательного трафика."
})

# Ex 13
code13 = r'''package main

import (
	"fmt"
	"net/http"
)

// API Gateway маршрутизатор внешних запросов
type APIGateway struct {
	routes map[string]string // URL pattern -> Internal gRPC Service
}

func NewAPIGateway() *APIGateway {
	return &APIGateway{
		routes: map[string]string{
			"/api/v1/auth/*":     "identity-service:50051",
			"/api/v1/billing/*":  "billing-service:50052",
			"/api/v1/catalog/*":  "catalog-service:50053",
			"/api/v1/orders/*":   "order-service:50054",
		},
	}
}

func (gw *APIGateway) RouteInfo() {
	fmt.Println("=== Маршрутизация API Gateway (Contract-First gRPC-Gateway) ===")
	for path, target := range gw.routes {
		fmt.Printf("Внешний REST эндпоинт: %-20s -> Внутренний gRPC сервис: %s\n", path, target)
	}
}

func main() {
	gw := NewAPIGateway()
	gw.RouteInfo()
	fmt.Println("Шлюз объединяет OpenAPI v3 документацию и транслирует JSON в двоичный gRPC.")
}
'''
validate_go_code(code13, "Ex 13")
exercises.append({
    "num": 13,
    "title": "Единый контракт-ориентированный API-шлюз (gRPC-Gateway)",
    "task": "Спроектируйте архитектуру единого API-шлюза (API Gateway) на базе gRPC-Gateway: трансляция внешних клиентских REST/JSON запросов во внутренние бинарные gRPC вызовы и автоматическая отдача Swagger UI документации.",
    "theory": """Внешние клиенты (веб-браузеры, мобильные приложения iOS/Android, партнерские интеграции) предпочитают стандартные протоколы HTTPS + JSON REST.
Однако внутри защищенного периметра Kubernetes межсервисное взаимодействие на JSON неэффективно: большой размер payload, накладные расходы на парсинг строк и отсутствие строгой схемы.
**gRPC-Gateway**:
- Генерирует обратный прокси-сервер на Go из тех же самых `.proto` файлов.
- Внешний запрос `POST /api/v1/orders` принимается шлюзом, валидируется и транслируется в нативный двоичный вызов `OrderService.CreateOrder(OrderRequest)` по HTTP/2 сокетам.
- Разработчики пишут только proto-спецификацию, получая одновременно gRPC сервер, REST API сервер и актуальную интерактивную Swagger/OpenAPI документацию.""",
    "step_by_step": [
        "Определите карту маршрутов `APIGateway`.",
        "Опишите трансляцию REST путей во внутренние адреса gRPC сервисов.",
        "Объясните выигрыш в сетевой производительности за счет бинарного Protobuf внутри кластера.",
        "Выведите конфигурацию шлюза."
    ],
    "code_blocks": [{
        "filename": "api_gateway_routing.go",
        "lang": "go",
        "code": code13
    }],
    "under_the_hood": "gRPC-Gateway внутри использует мультиплексированные HTTP/2 соединения с пулом gRPC каналов (`grpc.ClientConn`), что устраняет необходимость открывать новые TCP-сокеты на каждый входящий HTTP-запрос.",
    "pitfalls": "Попытка парсить JSON вручную через `map[string]interface{}` на шлюзе убивает производительность аллокациями памяти. Следует использовать сгенерированные Protobuf-структуры.",
    "bigtech_interview": "Почему в архитектуре микросервисов запрещают прямой доступ клиентов к внутренним gRPC сервисам в обход API Gateway?\nОтвет: API Gateway выполняет критические сквозные функции периметра безопасности: централизованная проверка JWT/OAuth2 токенов, Rate Limiting против DDoS-атак, TLS Termination, санитаризация заголовков и маршрутизация версий API, защищая внутренние микросервисы от прямого воздействия из ненадежной внешней сети."
})

# Ex 14
code14 = r'''package main

import (
	"errors"
	"fmt"
	"regexp"
)

type CreateOrderRequest struct {
	CustomerID string `json:"customer_id"`
	ProductID  string `json:"product_id"`
	Quantity   int    `json:"quantity"`
	UserEmail  string `json:"user_email"`
}

var emailRegex = regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)

func ValidateCreateOrderRequest(req CreateOrderRequest) error {
	if req.CustomerID == "" {
		return errors.New("customer_id обязателен для заполнения")
	}
	if req.ProductID == "" {
		return errors.New("product_id обязателен для заполнения")
	}
	if req.Quantity <= 0 || req.Quantity > 100 {
		return errors.New("quantity должен быть в диапазоне от 1 до 100 единиц")
	}
	if !emailRegex.MatchString(req.UserEmail) {
		return errors.New("user_email имеет невалидный формат")
	}
	return nil
}

func main() {
	badReq := CreateOrderRequest{CustomerID: "c1", ProductID: "p1", Quantity: 0, UserEmail: "invalid"}
	err := ValidateCreateOrderRequest(badReq)
	fmt.Printf("Результат валидации некорректного запроса: err = %v\n", err)

	goodReq := CreateOrderRequest{CustomerID: "c1", ProductID: "p1", Quantity: 2, UserEmail: "user@corp.ru"}
	err = ValidateCreateOrderRequest(goodReq)
	fmt.Printf("Результат валидации корректного запроса: err = %v (успех)\n", err)
}
'''
validate_go_code(code14, "Ex 14")
exercises.append({
    "num": 14,
    "title": "Декларативная валидация входящих данных на шлюзе",
    "task": "Реализуйте строгую валидацию входящих контрактов на шлюзе: отсечение запросов с некорректными email, отрицательными количествами и пустыми идентификаторами до их передачи во внутренний кластер.",
    "theory": """Принцип **Fail Fast (Быстрый отказ)** на периметре:
Если клиент прислал заказ с количеством товаров `0` или невалидным email, этот запрос должен быть отклонен прямо на API-шлюзе с кодом HTTP 400 Bad Request за 0.1 мс.
Передача невалидного запроса во внутренние микросервисы впустую тратит сетевой трафик, ресурсы gRPC сериализации и создает мусорные транзакции в базе данных.
В современных Go микросервисах валидация описывается декларативно в Proto-файлах через `bufbuild/protovalidate-go`:
```protobuf
string email = 1 [(buf.validate.field).string.email = true];
int32 quantity = 2 [(buf.validate.field).int32 = {gte: 1, lte: 100}];
```
Шлюз автоматически перехватывает нарушения контракта без написания шаблонного кода вручную.""",
    "step_by_step": [
        "Определите контрактную структуру `CreateOrderRequest`.",
        "Напишите функцию валидатора `ValidateCreateOrderRequest` с проверкой бизнес-границ.",
        "Используйте скомпилированное регулярное выражение для валидации email.",
        "Проверьте работу валидатора на граничных условиях."
    ],
    "code_blocks": [{
        "filename": "request_validator.go",
        "lang": "go",
        "code": code14
    }],
    "under_the_hood": "Валидаторы на базе кодогенерации работают в разы быстрее runtime-библиотек с рефлексией (go-playground/validator), так как генерируют прямой код сравнения типов без аллокаций памяти.",
    "pitfalls": "Компиляция регулярных выражений внутри хендлера (`regexp.Compile`) на каждый запрос создаст колоссальную нагрузку на CPU. Регулярные выражения обязаны компилироваться один раз на уровне пакета (`regexp.MustCompile`).",
    "bigtech_interview": "Почему бизнес-валидацию нельзя полностью делегировать фронтенду?\nОтвет: Любой клиентский ввод может быть скомпрометирован злоумышленником через прямые HTTP-запросы (cURL, Postman). Валидация на фронтенде нужна исключительно для пользовательского интерфейса (UX); сервер обязан считать любой входящий трафик потенциально вредоносным и проводить 100% независимую серверную валидацию."
})

# Ex 15
code15 = r'''package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

type UserClaims struct {
	UserID string
	Role   string
	Exp    int64
}

type AuthContextKey string

const ClaimsKey AuthContextKey = "user_claims"

// MockJWTValidator имитирует валидацию асимметричной подписи RSA/Ed25519
func MockJWTValidator(token string) (*UserClaims, error) {
	if token == "valid_admin_token" {
		return &UserClaims{
			UserID: "usr_admin_01",
			Role:   "ADMIN",
			Exp:    time.Now().Add(1 * time.Hour).Unix(),
		}, nil
	}
	return nil, errors.New("invalid or expired JWT signature")
}

func AuthMiddleware(token string, next func(ctx context.Context)) error {
	claims, err := MockJWTValidator(token)
	if err != nil {
		return fmt.Errorf("401 Unauthorized: %w", err)
	}

	// Инъекция клеймов в контекст Go
	ctx := context.WithValue(context.Background(), ClaimsKey, claims)
	next(ctx)
	return nil
}

func main() {
	_ = AuthMiddleware("valid_admin_token", func(ctx context.Context) {
		claims := ctx.Value(ClaimsKey).(*UserClaims)
		fmt.Printf("Авторизация успешна! Пользователь: %s, Роль: %s\n", claims.UserID, claims.Role)
	})
}
'''
validate_go_code(code15, "Ex 15")
exercises.append({
    "num": 15,
    "title": "Централизованная аутентификация и авторизация (JWT + RBAC)",
    "task": "Спроектируйте архитектуру централизованной аутентификации на API Gateway: валидация асимметричной криптографической подписи JWT-токенов, извлечение UserClaims и проброс идентификатора пользователя во внутренний контекст Go.",
    "theory": """Централизация безопасности на API-шлюзе избавляет микросервисы от дублирования кода проверки авторизации.
Схема работы:
1. Клиент присылает заголовок `Authorization: Bearer <jwt>`.
2. Шлюз проверяет цифровую подпись токена с помощью публичного ключа Auth-сервиса (RSA / Ed25519). При этом шлюз не делает сетевых запросов в базу данных (Stateless Auth).
3. Шлюз проверяет срок действия токена (`exp`).
4. Шлюз извлекает `user_id` и роли `roles` и внедряет их во внутренние gRPC-метаданные (`x-user-id`, `x-user-role`).
5. Внутренние микросервисы получают уже проверенные данные о пользователе, мгновенно применяя проверки RBAC (Role-Based Access Control).""",
    "step_by_step": [
        "Определите структуру `UserClaims` и типизированный ключ контекста `AuthContextKey`.",
        "Реализуйте функцию проверки токена `MockJWTValidator`.",
        "Создайте middleware для извлечения клеймов и сохранения их в `context.Context`.",
        "Продемонстрируйте безопасное извлечение контекста в целевом обработчике."
    ],
    "code_blocks": [{
        "filename": "jwt_auth_gateway.go",
        "lang": "go",
        "code": code15
    }],
    "under_the_hood": "Использование типизированных ключей `type AuthContextKey string` в `context.WithValue` предотвращает коллизии ключей контекста между различными пакетами и middleware сторонних библиотек.",
    "pitfalls": "Использование симметричного алгоритма HMAC-SHA256 для межсервисной авторизации опасно: секретный ключ пришлось бы раздавать на все сервисы. При утечке ключа с любого сервиса злоумышленник сможет подделывать любые токены. Всегда используйте асимметричные пары RSA/ECDSA/Ed25519.",
    "bigtech_interview": "Как организовать мгновенный отзыв (Revocation) украденного JWT-токена до истечения его срока жизни (exp)?\nОтвет: Через паттерн Token Blacklist в Redis: при выходе пользователя или компрометации уникальный идентификатор токена `jti` помещается в Redis с TTL, равным остатку жизни токена. API Gateway при валидации проверяет наличие `jti` в Redis через быстрый `EXISTS` за 0.3 мс."
})

# Ex 16
code16 = r'''package main

import (
	"fmt"
	"sync"
	"time"
)

type SlidingWindowLimiter struct {
	mu          sync.Mutex
	limit       int           // допустимо запросов за окно
	window      time.Duration // размер окна (например, 1 секунда)
	requestLogs []time.Time
}

func NewSlidingWindowLimiter(limit int, window time.Duration) *SlidingWindowLimiter {
	return &SlidingWindowLimiter{
		limit:  limit,
		window: window,
	}
}

func (l *SlidingWindowLimiter) Allow() bool {
	l.mu.Lock()
	defer l.mu.Unlock()

	now := time.Now()
	threshold := now.Add(-l.window)

	// Удаляем устаревшие таймстемпы за пределами скользящего окна
	validIdx := 0
	for i, t := range l.requestLogs {
		if t.After(threshold) {
			validIdx = i
			break
		}
	}
	if len(l.requestLogs) > 0 && l.requestLogs[len(l.requestLogs)-1].Before(threshold) {
		l.requestLogs = l.requestLogs[:0]
	} else {
		l.requestLogs = l.requestLogs[validIdx:]
	}

	if len(l.requestLogs) < l.limit {
		l.requestLogs = append(l.requestLogs, now)
		return true
	}

	return false
}

func main() {
	limiter := NewSlidingWindowLimiter(3, 100*time.Millisecond)

	fmt.Println("=== Скользящее окно Rate Limiting ===")
	for i := 1; i <= 5; i++ {
		allowed := limiter.Allow()
		fmt.Printf("Запрос #%d: разрешен = %t\n", i, allowed)
	}
}
'''
validate_go_code(code16, "Ex 16")
exercises.append({
    "num": 16,
    "title": "Распределенный Rate Limiting для защиты от перегрузок и ботов",
    "task": "Реализуйте алгоритм ограничения частоты запросов Sliding Window Rate Limiter на Go: динамический учет временных меток запросов, точное ограничение всплесков трафика и защита API-шлюза от ботнетов и DoS-атак.",
    "theory": """Почему классический Fixed Window (Фиксированное окно) плох?
Если лимит 100 запросов в минуту, злоумышленник может отправить 100 запросов на 59-й секунде и еще 100 запросов на 01-й секунде следующей минуты. В итоге за 2 секунды сервер получит 200 запросов, что вызовет падение базы данных (Traffic Burst at Window Boundary).
**Sliding Window (Скользящее окно)**:
- Учитывает точные таймстемпы запросов за скользящий интервал $[now - window; now]$.
- Гарантирует, что ни в один скользящий секундный или минутный интервал лимит не будет превышен.
- В распределенной системе реализуется в Redis с помощью Sorted Set (`ZADD`, `ZREMRANGEBYSCORE`, `ZCARD`).""",
    "step_by_step": [
        "Определите структуру `SlidingWindowLimiter` со срезом `[]time.Time`.",
        "Реализуйте метод `Allow()` с отсечением устаревших меток времени.",
        "Проверьте текущее количество активных запросов в окне.",
        "Продемонстрируйте блокировку 4-го и 5-го запроса при лимите 3."
    ],
    "code_blocks": [{
        "filename": "sliding_window_limiter.go",
        "lang": "go",
        "code": code16
    }],
    "under_the_hood": "В Redis реализация скользящего окна укладывается в один атомарный вызов Lua-скрипта: `redis.call('ZREMRANGEBYSCORE', key, 0, threshold)` удаляет старые запросы, а `redis.call('ZCARD', key)` проверяет текущий счетчик.",
    "pitfalls": "Хранение миллионов таймстемпов в оперативной памяти может вызвать рост потребления памяти. Для сверхвысоких нагрузок используют Sliding Window Counter (гибрид фиксированного окна с интерполяцией взвешенных сумм).",
    "bigtech_interview": "Какой HTTP-заголовок обязан возвращать шлюз при срабатывании Rate Limiter?\nОтвет: Код статуса `429 Too Many Requests`, заголовок `Retry-After: <секунды>` (указывающий клиенту, через сколько времени можно повторить запрос) и стандартные заголовки `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`."
})

# Ex 17
code17 = r'''package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

type CircuitState string

const (
	StateClosed   CircuitState = "CLOSED"   // Сервис работает в штатном режиме
	StateOpen     CircuitState = "OPEN"     // Сервис сбоит, вызовы мгновенно блокируются (Fail Fast)
	StateHalfOpen CircuitState = "HALF_OPEN" // Пробные запросы для проверки восстановления
)

type SimpleCircuitBreaker struct {
	mu           sync.Mutex
	state        CircuitState
	failureCount int
	threshold    int
	lastOpened   time.Time
	cooldown     time.Duration
}

func NewSimpleCircuitBreaker(threshold int, cooldown time.Duration) *SimpleCircuitBreaker {
	return &SimpleCircuitBreaker{
		state:     StateClosed,
		threshold: threshold,
		cooldown:  cooldown,
	}
}

func (cb *SimpleCircuitBreaker) Execute(fn func() error) error {
	cb.mu.Lock()
	if cb.state == StateOpen {
		if time.Since(cb.lastOpened) > cb.cooldown {
			cb.state = StateHalfOpen
		} else {
			cb.mu.Unlock()
			return errors.New("circuit breaker is OPEN: fast failure")
		}
	}
	cb.mu.Unlock()

	err := fn()

	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err != nil {
		cb.failureCount++
		if cb.failureCount >= cb.threshold {
			cb.state = StateOpen
			cb.lastOpened = time.Now()
		}
		return err
	}

	// Успешный вызов
	if cb.state == StateHalfOpen {
		cb.state = StateClosed
		cb.failureCount = 0
	}
	return nil
}

func main() {
	cb := NewSimpleCircuitBreaker(2, 50*time.Millisecond)

	flakyService := func() error {
		return errors.New("503 Service Unavailable")
	}

	fmt.Printf("Вызов 1: %v\n", cb.Execute(flakyService))
	fmt.Printf("Вызов 2: %v (порог сбоев достигнут)\n", cb.Execute(flakyService))
	fmt.Printf("Вызов 3: %v (сработал автоматический размыкатель цепи!)\n", cb.Execute(flakyService))
}
'''
validate_go_code(code17, "Ex 17")
exercises.append({
    "num": 17,
    "title": "Изоляция сбоев: Circuit Breaker и Bulkhead на всех межсервисных клиентах",
    "task": "Реализуйте паттерн Circuit Breaker (Размыкатель цепи) на Go: состояния Closed, Open, Half-Open, изоляция каскадных сбоев и предотвращение блокировки горутин при падении второстепенных микросервисов.",
    "theory": """Каскадный сбой (Cascading Failure) — главный убийца микросервисных архитектур:
Сервис уведомлений завис под нагрузкой и стал отвечать по 30 секунд.
Сервис заказов вызывает сервис уведомлений и блокирует свои горутины.
Через минуту все горутины сервиса заказов исчерпаны, и он тоже падает. Затем падает API Gateway. Вся платформа лежит.
**Circuit Breaker (Размыкатель цепи)** предотвращает катастрофу:
1. **Closed**: Все запросы идут в обычном режиме. Ошибки подсчитываются.
2. **Open**: Если порог ошибок превышен (например, 5 сбоев подряд), цепь размыкается. ВСЕ последующие вызовы МГНОВЕННО отклоняются с ошибкой за 0.001 мс без сетевого обращения (Fast Fail). Падающий сервис получает передышку для восстановления.
3. **Half-Open**: По истечении времени остывания (`cooldown`) пропускается один пробный запрос. Если он успешен, цепь возвращается в статус `Closed`.""",
    "step_by_step": [
        "Определите состояния `CircuitState`: Closed, Open, HalfOpen.",
        "Реализуйте структуру `SimpleCircuitBreaker` с контролем `threshold` и `cooldown`.",
        "Реализуйте метод `Execute` с потокобезопасным переключением состояний.",
        "Продемонстрируйте мгновенный отказ на 3-м запросе."
    ],
    "code_blocks": [{
        "filename": "circuit_breaker.go",
        "lang": "go",
        "code": code17
    }],
    "under_the_hood": "В связке с Circuit Breaker применяют паттерн Bulkhead (Семафор на клиенте): ограничение количества одновременных горутин к одному зависимому сервису до фиксированного числа (например, максимум 50 горутин), чтобы сбой одного сервиса не мог занять все свободные ресурсы процессора.",
    "pitfalls": "Отсутствие таймаутов на сетевом вызове внутри `Execute` сведет на нет преимущества Circuit Breaker: горутина зависнет на первом же запросе до того, как счетчик ошибок успеет вырасти.",
    "bigtech_interview": "Что такое Fallback в контексте Circuit Breaker и как он реализуется в интернет-магазинах?\nОтвет: Fallback — это запасной сценарий при размыкании цепи. Например, если Recommendation Service упал и Circuit Breaker перешел в состояние Open, клиентский хендлер не выбрасывает ошибку пользователю, а возвращает статический закэшированный список топ-10 популярных товаров (Graceful Degradation). Пользователь даже не замечает, что рекомендательный сервис недоступен."
})

with open('/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch100_p1.json', 'w', encoding='utf-8') as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Chapter 100 Part 1 generated: {len(exercises)} exercises.")
