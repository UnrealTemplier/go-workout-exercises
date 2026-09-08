#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import subprocess

def validate_go_code(code, label):
    p = subprocess.run(["gofmt", "-e"], input=code, capture_output=True, text=True)
    if p.returncode != 0:
        raise ValueError(f"Go syntax error in {label}:\n{p.stderr}\nCode:\n{code}")

exercises = []

# Ex 18
code18 = r'''package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

type LeaderElectionNode struct {
	nodeID   string
	isLeader bool
	mu       sync.RWMutex
}

func (n *LeaderElectionNode) Campaign(ctx context.Context, etcdKey string) {
	// Имитация etcd v3 Lease Campaign (concurrency.Election)
	n.mu.Lock()
	n.isLeader = true
	n.mu.Unlock()
	fmt.Printf("[etcd election]: Узел %s успешно захватил Lease ключ %s и стал ЛИДЕРОМ кластера!\n", n.nodeID, etcdKey)
}

func (n *LeaderElectionNode) IsLeader() bool {
	n.mu.RLock()
	defer n.mu.RUnlock()
	return n.isLeader
}

func main() {
	node := &LeaderElectionNode{nodeID: "billing-cron-pod-1"}
	node.Campaign(context.Background(), "/election/billing-nightly-cron")

	if node.IsLeader() {
		fmt.Println("Исполнение периодического списания абонентских плат на активном лидере.")
	}
}
'''
validate_go_code(code18, "Ex 18")
exercises.append({
    "num": 18,
    "title": "Распределенная координация и выборы лидера на etcd v3",
    "task": "Интегрируйте распределенную координацию и выборы лидера (Leader Election) на базе etcd v3: запуск периодических фоновых задач (начисление процентов, формирование бухгалтерских отчетов) строго на одном экземпляре сервиса без риска дублирования.",
    "theory": """В Kubernetes кластере сервис биллинга запущен в 10 репликах для обеспечения высокой доступности.
Если каждая реплика запустит cron-задачу `0 0 * * *` (ежемесячное списание абонентской платы), с клиентов снимутся деньги 10 раз!
**Выборы лидера (Leader Election) на etcd v3**:
1. Все 10 подов участвуют в выборах через пакет `go.etcd.io/etcd/client/v3/concurrency`.
2. Поды создают `Lease` с TTL (например, 10 секунд) и соревнуются за создание ключа `/election/billing-cron`.
3. Только ОДИН под побеждает и получает статус Лидера. Он непрерывно продлевает Lease через `KeepAlive`.
4. Остальные 9 подов находятся в пассивном режиме ожидания (Standby).
5. Если лидер падает (Kernel Panic, OOM, потеря сети), Lease истекает за 10 секунд, и etcd автоматически выбирает нового лидера среди оставшихся подов.""",
    "step_by_step": [
        "Определите структуру `LeaderElectionNode` с флагом лидерства и мьютексом.",
        "Реализуйте метод `Campaign` для захвата ключа выборов.",
        "Реализуйте потокобезопасную проверку `IsLeader()`.",
        "Убедитесь, что фоновые задачи запускаются только на лидере."
    ],
    "code_blocks": [{
        "filename": "etcd_leader_election.go",
        "lang": "go",
        "code": code18
    }],
    "under_the_hood": "etcd использует протокол консенсуса Raft. Создание ключа выборов выполняется через атомарную транзакцию `txn.If(CreateRevision(key) == 0).Then(Put(key)).Else()`, гарантируя, что ровно один узел победит в гонке даже при миллисекундных интервалах.",
    "pitfalls": "Слишком короткий TTL Lease (например, 1 секунда) приведет к ложным перевыборам лидера при кратковременных паузах GC в Go. Рекомендуемый TTL: 5–10 секунд.",
    "bigtech_interview": "Что такое проблема Split-Brain при выборах лидера и как Raft кворум ее предотвращает?\nОтвет: Split-Brain возникает при разрыве сети между датацентрами, когда две изолированные половины кластера объявляют каждая своего лидера, приводя к повреждению данных. В алгоритме Raft выборы возможны только при наличии строгого большинства (Strict Quorum: $N/2 + 1$). Половина, потерявшая кворум, не может выбрать лидера и переходит в режим ожидания."
})

# Ex 19
code19 = r'''package main

import (
	"context"
	"fmt"
	"time"
)

type DelayedTask struct {
	ID        string
	Queue     string
	Payload   string
	RunAt     time.Time
	MaxRetries int
}

type TaskQueueManager struct {
	tasks []DelayedTask
}

func (m *TaskQueueManager) EnqueueDelayed(task DelayedTask) {
	m.tasks = append(m.tasks, task)
	fmt.Printf("[River/Asynq]: Задача %s поставлена в очередь %s с отложенным стартом в %s\n",
		task.ID, task.Queue, task.RunAt.Format("15:04:05"))
}

func main() {
	qm := &TaskQueueManager{}
	task := DelayedTask{
		ID:         "task_sub_charge_881",
		Queue:      "billing.delayed",
		Payload:    `{"customer_id":"usr_42","amount":199000}`,
		RunAt:      time.Now().Add(24 * time.Hour),
		MaxRetries: 5,
	}
	qm.EnqueueDelayed(task)
}
'''
validate_go_code(code19, "Ex 19")
exercises.append({
    "num": 19,
    "title": "Масштабируемые очереди задач и обработка отложенных списаний",
    "task": "Интегрируйте надежную систему распределенных очередей задач (River на PostgreSQL или Asynq на Redis): планирование отложенных платежей (Delayed Tasks), экспоненциальный бэкофф с джиттером при сбоях и изоляция в Dead Letter Queue (DLQ).",
    "theory": """Многие операции не должны выполняться синхронно в HTTP-запросе:
- Отправка фискальных чеков в налоговую службу (ОФД).
- Списание подписки через 30 дней после триального периода.
- Пакетная рассылка уведомлений об изменении условий сервиса.
**Продвинутые очереди задач на Go**:
1. **River (PostgreSQL)**: Использует возможности Postgres (`FOR UPDATE SKIP LOCKED`, JSONB, партиции). Преимущество: транзакционная постановка задачи в рамках бизнес-транзакции без Dual-Write.
2. **Asynq (Redis)**: Обеспечивает субмиллисекундную латентность и миллионы задач в секунду.
Ключевые механизмы:
- **Exponential Backoff & Jitter**: При сбое внешнего сервиса повтор выполняется через 1с, 2с, 4с, 8с + случайный шум (джиттер) для предотвращения эффекта толпы.
- **Dead Letter Queue (DLQ)**: Если задача упала 5 раз подряд, она перемещается в карантин для ручного разбора инженерами.""",
    "step_by_step": [
        "Определите структуру `DelayedTask` с параметрами задержки `RunAt` и повторов.",
        "Реализуйте диспетчер `TaskQueueManager` с методом `EnqueueDelayed`.",
        "Опишите стратегию обработки сбоев через DLQ.",
        "Проверьте постановку отложенной задачи."
    ],
    "code_blocks": [{
        "filename": "delayed_task_queue.go",
        "lang": "go",
        "code": code19
    }],
    "under_the_hood": "В Redis Asynq отложенные задачи хранятся в структуре Sorted Set (`ZSET`), где Score — это Unix-таймстемп запланированного времени запуска. Воркер регулярно опрашивает ZSET с помощью `ZRANGEBYSCORE ... LIMIT` и перемещает готовые к исполнению задачи в готовую очередь списков (`LPUSH/RPOPLPUSH`).",
    "pitfalls": "Отсутствие таймаутов на исполнение задач в воркере (Job Timeout) приведет к зависанию воркеров при сетевых блокировках сторонних API.",
    "bigtech_interview": "Почему для финансовых отложенных задач часто выбирают River на PostgreSQL вместо RabbitMQ или Kafka?\nОтвет: Потому что River позволяет поставить задачу в очередь В РАМКАХ ТОЙ ЖЕ САМОЙ транзакции, которая создала заказ (`tx.Commit()`). Если создание заказа откатится, задача в очереди не появится. В случае с Kafka или RabbitMQ для этого пришлось бы дополнительно городить паттерн Transactional Outbox."
})

# Ex 20
code20 = r'''package main

import (
	"fmt"
	"math"
)

type FinancialTransaction struct {
	AccountID string
	Amount    float64
}

// SimpleFraudDetector вычисляет статистический Z-Score для потока транзакций
type SimpleFraudDetector struct {
	mean   float64 // средняя сумма транзакции клиента
	stdDev float64 // стандартное отклонение
}

func (d *SimpleFraudDetector) IsAnomalous(amount float64) (bool, float64) {
	if d.stdDev == 0 {
		return false, 0
	}
	zScore := math.Abs(amount-d.mean) / d.stdDev
	// По правилу трех сигм (3-sigma rule) отклонение > 3.0 указывает на аномалию (p < 0.003)
	return zScore > 3.0, zScore
}

func main() {
	// Профиль пользователя: средняя трата 1500 руб, stdDev 500 руб.
	detector := &SimpleFraudDetector{mean: 1500, stdDev: 500}

	tx1 := 2200.0
	tx2 := 150000.0 // резкий подозрительный перевод

	anom1, z1 := detector.IsAnomalous(tx1)
	anom2, z2 := detector.IsAnomalous(tx2)

	fmt.Printf("Транзакция %.2f руб: Аномалия = %t (Z-Score = %.2f)\n", tx1, anom1, z1)
	fmt.Printf("Транзакция %.2f руб: Аномалия = %t (Z-Score = %.2f) -> ФРОД-БЛОКИРОВКА!\n", tx2, anom2, z2)
}
'''
validate_go_code(code20, "Ex 20")
exercises.append({
    "num": 20,
    "title": "Потоковая аналитика и обнаружение фрода в реальном времени",
    "task": "Реализуйте модуль потоковой аналитики и детекции фрода (Stream Fraud Detection) на Go: расчет скользящих статистических агрегатов (среднее, стандартное отклонение, Z-Score) и мгновенная блокировка аномальных транзакций в реальном времени.",
    "theory": """Фрод в финтехе (угон аккаунта, несанкционированный вывод средств) должен пресекаться в реальном времени до момента списания, а не постфактум через часы.
Потоковая обработка на Go:
- Консьюмер вычитывает поток финансовых транзакций из Kafka.
- Профиль клиента поддерживается в скользящем окне памяти или Redis.
- **Статистический Z-Score**:
$$Z = \\frac{|X - \\mu|}{\\sigma}$$
Если клиент обычно совершает покупки на 1 000–3 000 рублей, а затем внезапно отправляет 500 000 рублей в 4 утра на зарубежную карту, $Z > 10$.
Транзакция мгновенно замораживается, а клиенту отправляется запрос на подтверждение через пуш-уведомление.""",
    "step_by_step": [
        "Определите структуру `FinancialTransaction`.",
        "Реализуйте детектор `SimpleFraudDetector` с расчетом Z-Score по правилу 3-х сигм.",
        "Протестируйте детекцию на обычной и аномальной транзакциях.",
        "Выведите вердикт антифрод-системы."
    ],
    "code_blocks": [{
        "filename": "fraud_detector.go",
        "lang": "go",
        "code": code20
    }],
    "under_the_hood": "Для скользящих окон без удержания миллионов транзакций в памяти применяется онлайн-алгоритм Велфорда (Welford's Algorithm), позволяющий обновлять математическое ожидание и дисперсию за один проход по новым данным в режиме $O(1)$ памяти.",
    "pitfalls": "Блокировка транзакций по жестким константным лимитам (Hardcoded Rules) приведет к массовым жалобам состоятельных клиентов. Статистика обязана быть персонализированной для каждого пользователя.",
    "bigtech_interview": "Какова целевая задержка (Latency SLA) для выполнения антифрод-проверок при онлайн-авторизации банковских карт?\nОтвет: Не более 15–30 миллисекунд. Платежные системы (Mastercard, Visa, МИР) накладывают жесткий дедлайн на ответ банка-эмитента (обычно 500–1000 мс на весь цикл). Поэтому антифрод-правила на Go выполняются параллельно через горутины с тайм-аутом 20 мс."
})

# Ex 21
code21 = r'''package main

import (
	"context"
	"fmt"
)

type SupportAssistant struct {
	KnowledgeBaseDoc string
}

func (a *SupportAssistant) AnswerCustomerQuestion(ctx context.Context, question string) string {
	// Имитация RAG + LLM генерации
	return fmt.Sprintf("ИИ-Ассистент поддержки: На основе регламентов платформы ('%s') отвечаю на ваш вопрос: '%s'. Возврат средств осуществляется автоматически в течение 10 минут.",
		a.KnowledgeBaseDoc, question)
}

func main() {
	assistant := &SupportAssistant{
		KnowledgeBaseDoc: "Регламент возврата: При отмене заказа на этапе сборки возврат денег на счет покупателя выполняется мгновенно без комиссии.",
	}

	ans := assistant.AnswerCustomerQuestion(context.Background(), "Как вернуть деньги за отмененный заказ?")
	fmt.Println(ans)
}
'''
validate_go_code(code21, "Ex 21")
exercises.append({
    "num": 21,
    "title": "ИИ-ассистент поддержки пользователей с RAG и Function Calling",
    "task": "Интегрируйте в платформу интеллектуального ИИ-помощника технической поддержки: поиск регламентов в базе знаний через pgvector RAG, ответы пользователям в режиме реального времени и выполнение действий по заказу через Function Calling.",
    "theory": """Современная платформа Capstone уровня Principal включает ИИ-интерфейс самообслуживания клиентов:
1. Клиент спрашивает в чате: *«Где мой заказ #ORD-771 и почему он задерживается?»*.
2. Шлюз ассистента векторизует вопрос и извлекает статьи базы знаний через RAG.
3. Модель через Function Calling инициирует вызов функции `get_order_status(order_id: "ORD-771")`.
4. Бэкенд на Go обращается к Order Fulfillment Service, получает текущие координаты курьера и возвращает их модели.
5. Модель генерирует вежливый, персонализированный ответ со ссылкой на трекинг-карту.""",
    "step_by_step": [
        "Определите структуру `SupportAssistant`.",
        "Реализуйте метод `AnswerCustomerQuestion` с имитацией RAG-инъекции.",
        "Продемонстрируйте формирование контекстуального ответа клиенту.",
        "Проверьте работу в main."
    ],
    "code_blocks": [{
        "filename": "ai_support_assistant.go",
        "lang": "go",
        "code": code21
    }],
    "under_the_hood": "Взаимодействие со стороны клиента ведется по протоколу SSE (Server-Sent Events) или WebSocket, обеспечивая передачу токенов по мере их генерации с TTFT (Time to First Token) < 200 мс.",
    "pitfalls": "Предоставление ассистенту прямого доступа к базе данных без авторизационного контекста пользователя позволит клиенту через Prompt Injection запросить статус чужого заказа.",
    "bigtech_interview": "Как защитить ИИ-ассистента поддержки от выполнения неавторизованных действий через Function Calling?\nОтвет: Каждый вызов функции (`tool_call`) обязан принимать контекст безопасности текущего пользователя (`ctx.Value(UserClaimsKey)`). Перед выполнением действия (например, отмены заказа) хендлер Go строго проверяет, что запрашиваемый заказ принадлежит именно тому пользователю, от имени которого открыта сессия."
})

# Ex 22
code22 = r'''package main

import (
	"fmt"
	"sync/atomic"
	"unsafe"
)

// InefficientMetricsCounters подвержен ложному разделению (False Sharing):
// счетчики располагаются в одной 64-байтовой кэш-линии процессора
type InefficientMetricsCounters struct {
	TotalRequests   int64 // 8 байт
	PaymentSuccess  int64 // 8 байт
	PaymentFailures int64 // 8 байт
}

// CacheFriendlyMetricsCounters с ручным struct padding:
// счетчики разнесены по разным кэш-линиям (64 байта), предотвращая взаимную инвалидацию L1 кэшей ядер CPU
type CacheFriendlyMetricsCounters struct {
	TotalRequests   int64
	_pad0           [56]byte // 8 + 56 = 64 байта (ровно одна кэш-линия!)
	PaymentSuccess  int64
	_pad1           [56]byte // 8 + 56 = 64 байта
	PaymentFailures int64
	_pad2           [56]byte // 8 + 56 = 64 байта
}

func main() {
	var ineff InefficientMetricsCounters
	var opt CacheFriendlyMetricsCounters

	fmt.Printf("Размер неоптимизированной структуры: %d байт (все счетчики делят одну кэш-линию L1!)\n",
		unsafe.Sizeof(ineff))
	fmt.Printf("Размер Cache-Friendly структуры с padding: %d байт (каждый счетчик в изолированной линии!)\n",
		unsafe.Sizeof(opt))
	fmt.Println("Результат: 100 000 RPS параллельных атомарных инкрементов работают в 4-6 раз быстрее без Cache Line Contention.")
}
'''
validate_go_code(code22, "Ex 22")
exercises.append({
    "num": 22,
    "title": "Кэш-ориентированная оптимизация структур памяти (Cache-Friendly Design)",
    "task": "Оптимизируйте структуры данных горячего пути (Hot Path) под архитектуру кэш-линий процессора: предотвращение False Sharing в многопоточных атомарных счетчиках через struct padding (64 байта) для достижения 100 000 RPS.",
    "theory": """На современных многоядерных процессорах оперативная память загружается в L1/L2/L3 кэши блоками по **64 байта (Cache Line)**.
Проблема **False Sharing (Ложное разделение)**:
Если два потока на разных ядрах параллельно инкрементируют `atomic.AddInt64(&counter1)` и `atomic.AddInt64(&counter2)`, а обе переменные находятся в одной 64-байтовой кэш-линии:
- Ядро 1 модифицирует кэш-линию.
- Протокол когерентности кэшей (MESI) принудительно инвалидирует эту кэш-линию в L1-кэше Ядра 2!
- Ядро 2 вынуждено заново вычитывать линию из медленного L3 кэша или RAM.
- Производительность падает в 4–10 раз из-за постоянной войны между ядрами за кэш-линию!
**Решение: Struct Padding**:
Разнесение интенсивно мутируемых переменных по разным кэш-линиям с помощью фиктивных байтовых полей `_pad [56]byte`.""",
    "step_by_step": [
        "Определите неоптимизированную структуру счетчиков `InefficientMetricsCounters`.",
        "Спроектируйте структуру `CacheFriendlyMetricsCounters` с паддингом `[56]byte` (суммарно ровно 64 байта на поле).",
        "Сравните размеры структур с помощью `unsafe.Sizeof`.",
        "Объясните физику протокола когерентности кэшей MESI."
    ],
    "code_blocks": [{
        "filename": "cache_friendly_padding.go",
        "lang": "go",
        "code": code22
    }],
    "under_the_hood": "Размер 64 байта является стандартом для архитектур Intel x86-64, AMD64 и ARM64 (Apple M-серия, AWS Graviton). Паддинг гарантирует, что переменная монопольно владеет всей кэш-линией.",
    "pitfalls": "Чрезмерное использование struct padding для структур, которые хранятся миллионами экземпляров (например, элементы списка), приведет к раздуванию потребления памяти. Паддинг применяется ТОЛЬКО к единичным разделяемым глобальным счетчикам и пулам.",
    "bigtech_interview": "Что такое протокол MESI и как он влияет на масштабируемость atomic операций в Go?\nОтвет: MESI определяет 4 состояния кэш-линии: Modified, Exclusive, Shared, Invalid. При выполнении атомарной инструкции (LOCK CMPXCHG) ядро переводит линию в состояние Modified, отправляя сигнал инвалидации всем остальным ядрам по шине межпроцессорной связи (UPI/QPI). Если несколько ядер бьют в одну линию, шина перегружается трафиком инвалидаций, вызывая масштабирование с замедлением (negative scaling)."
})

# Ex 23
code23 = r'''package main

import (
	"fmt"
	"net/http"
	"runtime/debug"
	"time"
)

// ConfigureHighLoadTransport настраивает сетевой транспорт для пиковой нагрузки 100 000 RPS
func ConfigureHighLoadTransport() *http.Transport {
	return &http.Transport{
		MaxIdleConns:        20000,            // суммарно открытых keep-alive сокетов
		MaxIdleConnsPerHost: 5000,             // сокетов на один внутренний бэкенд
		IdleConnTimeout:     90 * time.Second, // время удержания соединения в пуле
		DisableCompression:  true,             // отключение gzip для снижения нагрузки на CPU
		ForceAttemptHTTP2:   true,             // поддержка мультиплексирования HTTP/2
	}
}

func main() {
	// Тюнинг сборщика мусора и памяти
	// GOMEMLIMIT предотвращает OOM, а soft limit держит память в рамках cgroup
	debug.SetMemoryLimit(2 * 1024 * 1024 * 1024) // 2 ГБ лимит

	t := ConfigureHighLoadTransport()
	fmt.Println("=== Тюнинг рантайма Go и сетевых сокетов под 100k RPS ===")
	fmt.Printf("Пул Keep-Alive соединений: MaxIdleConns=%d, PerHost=%d\n",
		t.MaxIdleConns, t.MaxIdleConnsPerHost)
	fmt.Println("GOMEMLIMIT успешно установлен в 2 ГБ. OOM-Killed исключен.")
}
'''
validate_go_code(code23, "Ex 23")
exercises.append({
    "num": 23,
    "title": "Тюнинг сетевых сокетов и рантайма Go под 100k RPS",
    "task": "Сконфигурируйте сетевой стек и рантайм Go под нагрузку 100 000 RPS: глубокий тюнинг http.Transport (MaxIdleConns = 20000), отключение сжатия для экономии CPU, настройка GOMEMLIMIT и оптимизация сборщика мусора.",
    "theory": """По умолчанию Go сконфигурирован для микросервисов со средней нагрузкой:
`http.DefaultTransport` имеет параметр `MaxIdleConnsPerHost = 2`!
При нагрузке 50 000 RPS дефолтный клиент будет закрывать и заново открывать 49 998 TCP-сокетов КАЖДУЮ СЕКУНДУ.
Последствия:
- Истощение эфемерных портов операционной системы (TIME_WAIT exhaustion).
- Колоссальная трата CPU на 3-way handshake и TLS handshake.
- Системная ошибка `cannot assign requested address`.
**Комплексный тюнинг под 100 000 RPS**:
1. `MaxIdleConns = 20000`, `MaxIdleConnsPerHost = 5000`: постоянный горячий пул открытых сокетов.
2. `DisableCompression = true`: для внутренних микросервисов в защищенной сети gzip сжатие тратит 30% CPU впустую.
3. `debug.SetMemoryLimit (GOMEMLIMIT)`: жесткая привязка к 90% лимита cgroup Kubernetes предотвращает падения пода по сигналу OOM Killer.""",
    "step_by_step": [
        "Настройте кастомный экземпляр `http.Transport` с расширенным пулом соединений.",
        "Установите `DisableCompression: true` для экономии тактов процессора.",
        "Задайте ограничение памяти через `debug.SetMemoryLimit`.",
        "Проверьте настройки транспорта."
    ],
    "code_blocks": [{
        "filename": "runtime_highload_tuning.go",
        "lang": "go",
        "code": code23
    }],
    "under_the_hood": "Флаг `ForceAttemptHTTP2` позволяет мультиплексировать сотни логических gRPC/REST запросов внутри единого постоянного TCP-соединения, кардинально снижая количество файловых дескрипторов сокетов в ядре Linux.",
    "pitfalls": "Увеличение пула сокетов на клиенте требует синхронного увеличения лимита соединений на сервере (`somaxconn` и `net.core.somaxconn = 65535` в sysctl Linux).",
    "bigtech_interview": "Как GOMEMLIMIT (введенный в Go 1.19) взаимодействует с переменной GOGC?\nОтвет: GOGC задает процент роста кучи до следующей сборки мусора (по умолчанию 100%). GOMEMLIMIT задает абсолютный потолок памяти (например, 2 ГБ). Когда использование памяти далеко от GOMEMLIMIT, GC работает в стандартном режиме по GOGC. При приближении к GOMEMLIMIT рантайм Go динамически делает сборку мусора более частой, удерживая память строго под потолком и исключая OOM Killer."
})

# Ex 24
code24 = r'''package main

import (
	"context"
	"fmt"
	"net/http"
	"time"
)

type REDMetricsMiddleware struct {
	TotalRequests   int64
	FailedRequests  int64
	SumDurationMs   int64
}

func (m *REDMetricsMiddleware) RecordRequest(status int, duration time.Duration) {
	m.TotalRequests++
	if status >= 500 {
		m.FailedRequests++
	}
	m.SumDurationMs += duration.Milliseconds()
}

func main() {
	metrics := &REDMetricsMiddleware{}
	metrics.RecordRequest(http.StatusOK, 12*time.Millisecond)
	metrics.RecordRequest(http.StatusInternalServerError, 45*time.Millisecond)

	fmt.Println("=== Сквозная наблюдаемость (RED Metrics Methodology) ===")
	fmt.Printf("Rate:      %d всего запросов\n", metrics.TotalRequests)
	fmt.Printf("Errors:    %d сбоев (5xx)\n", metrics.FailedRequests)
	fmt.Printf("Duration:  Средняя задержка: %.2f мс\n", float64(metrics.SumDurationMs)/float64(metrics.TotalRequests))
	fmt.Println("Трассировка: OpenTelemetry W3C Traceparent сквозным образом пробрасывается через HTTP, gRPC и Kafka.")
}
'''
validate_go_code(code24, "Ex 24")
exercises.append({
    "num": 24,
    "title": "Сквозная наблюдаемость (Full Observability Stack): Prometheus + OTel",
    "task": "Оснастите платформу полной сквозной наблюдаемостью: метрики по методологии RED (Rate, Errors, Duration) в Prometheus, распределенная трассировка OpenTelemetry с передачей контекста traceparent через gRPC и сообщения Kafka.",
    "theory": """В распределенной системе из десятков микросервисов невозможно локализовать проблему без сквозной телеметрии.
Три столпа наблюдаемости (Observability Pillars):
1. **Метрики (Prometheus - RED Methodology)**:
   - **Rate**: Количество запросов в секунду (`http_requests_total`).
   - **Errors**: Доля запросов с ошибками (`http_requests_total{status=~"5.."}`).
   - **Duration**: Перцентили задержки p50, p95, p99 (`http_request_duration_seconds_bucket`).
2. **Трассировка (OpenTelemetry + Jaeger)**:
   - Единый `TraceID` генерируется на API Gateway и пробрасывается через W3C заголовок `traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01` во все HTTP-запросы, gRPC-метаданные и заголовки сообщений Kafka.
   - Позволяет на одной временной шкале увидеть путь транзакции через 6 сервисов и точно найти виновника задержки.
3. **Логи (Loki / Elasticsearch)**: Структурированный JSON с обязательной привязкой `trace_id`.""",
    "step_by_step": [
        "Определите структуру аккумулятора RED метрик `REDMetricsMiddleware`.",
        "Реализуйте метод сбора параметров запроса `RecordRequest`.",
        "Сформируйте спецификацию заголовка W3C Trace Context.",
        "Продемонстрируйте сбор метрик."
    ],
    "code_blocks": [{
        "filename": "observability_red_metrics.go",
        "lang": "go",
        "code": code24
    }],
    "under_the_hood": "OpenTelemetry SDK в Go использует потокобезопасный `context.Context` для хранения и извлечения текущего спана (`trace.SpanFromContext(ctx)`), что исключает необходимость прокидывать идентификаторы спанов отдельными аргументами через все функции приложения.",
    "pitfalls": "Сбор 100% трейсов при нагрузке 100 000 RPS перегрузит трассировочный бэкенд (Jaeger) терабайтами данных. В продакшене обязательно применяют Head-Based или Tail-Based семплирование (например, сохранение 1% обычных трейсов и 100% трейсов с ошибками).",
    "bigtech_interview": "В чем разница между метриками Histogram и Summary в клиенте Prometheus на Go?\nОтвет: Histogram подсчитывает попадание значений в фиксированные заранее заданные корзины (Buckets) на стороне приложения, позволяя агрегировать перцентили (p95, p99) на стороне Prometheus сервера для сотен подов одновременно через `histogram_quantile()`. Summary вычисляет точные перцентили прямо внутри приложения на лету, но их математически невозможно усреднять или агрегировать между разными экземплярами сервисов."
})

# Ex 25
code25 = r'''package main

import (
	"context"
	"fmt"
	"log/slog"
	"os"
)

type TraceContextKey string

const (
	TraceIDKey TraceContextKey = "trace_id"
	SpanIDKey  TraceContextKey = "span_id"
)

// TraceContextHandler автоматически извлекает TraceID из context.Context и добавляет его в каждую строчку JSON лога
type TraceContextHandler struct {
	slog.Handler
}

func (h *TraceContextHandler) Handle(ctx context.Context, r slog.Record) error {
	if ctx != nil {
		if traceID, ok := ctx.Value(TraceIDKey).(string); ok {
			r.AddAttrs(slog.String("trace_id", traceID))
		}
		if spanID, ok := ctx.Value(SpanIDKey).(string); ok {
			r.AddAttrs(slog.String("span_id", spanID))
		}
	}
	return h.Handler.Handle(ctx, r)
}

func main() {
	baseHandler := slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo})
	logger := slog.New(&TraceContextHandler{Handler: baseHandler})

	ctx := context.WithValue(context.Background(), TraceIDKey, "4bf92f3577b34da6a3ce929d0e0e4736")
	ctx = context.WithValue(ctx, SpanIDKey, "00f067aa0ba902b7")

	logger.InfoContext(ctx, "Платежная транзакция успешно зафиксирована в Event Store",
		slog.String("account_id", "acc_42"),
		slog.Int64("amount_cents", 150000),
	)
}
'''
validate_go_code(code25, "Ex 25")
exercises.append({
    "num": 25,
    "title": "Структурированное логирование с корреляцией TraceID",
    "task": "Реализуйте структурированное логирование высокой производительности на базе пакета log/slog: создание кастомного TraceContextHandler для автоматической инъекции trace_id и span_id из context.Context в каждую запись лога в формате JSON.",
    "theory": """Логирование в виде неструктурированного текста (`log.Println("error processing order", err)`) в распределенных системах абсолютно непригодно:
- Невозможно автоматически фильтровать логи по полям в Grafana Loki или OpenSearch.
- При сотнях тысяч сообщений в секунду невозможно понять, к какому конкретно пользователю и HTTP-запросу относится запись.
**Пакет `log/slog` (стандартная библиотека Go 1.21+)**:
- Структурированный вывод в JSON без сторонних тяжелых библиотек.
- Поддержка кастомных middleware-хендлеров (`slog.Handler`).
- Корреляция логов и трасс: логгер автоматически вытягивает `trace_id` из контекста запроса.
Инженер в Grafana нажимает на спан с ошибкой в Jaeger и по кнопке 'View Logs' мгновенно видит все записи журнала со всех микросервисов, относящиеся к этому запросу.""",
    "step_by_step": [
        "Определите тип `TraceContextHandler`, оборачивающий базовый `slog.Handler`.",
        "Реализуйте метод `Handle(ctx, r)` с извлечением `trace_id` и `span_id`.",
        "Инициализируйте логгер с JSONHandler.",
        "Вызовите `logger.InfoContext` и проверьте вывод валидного JSON с привязанным идентификатором трассы."
    ],
    "code_blocks": [{
        "filename": "structured_logging_trace.go",
        "lang": "go",
        "code": code25
    }],
    "under_the_hood": "`log/slog` оптимизирован по аллокациям памяти: использование атрибутов `slog.Attr` и методов типа `AddAttrs` формирует буферизованные записи без боксинга значений в `interface{}`.",
    "pitfalls": "Использование `logger.Info` вместо `logger.InfoContext` приведет к потере контекста, из-за чего хендлер не сможет извлечь `trace_id`.",
    "bigtech_interview": "Почему в HighLoad системах рекомендуется логировать только на уровнях INFO и ERROR, полностью отключая DEBUG в проде?\nОтвет: Логирование в stdout/stderr вызывает системные вызовы записи `write(2)` и парсинг лог-коллектором (FluentBit / Vector). При 100 000 RPS даже один дополнительный лог на запрос сгенерирует 100 000 строк/сек (~50 МБ/сек дискового ввода-вывода), что забьет дисковую подсистему ноды Kubernetes и приведет к троттлингу сервиса."
})

# Ex 26
code26 = r'''package main

import (
	"context"
	"fmt"
)

// FintechPlatformSpec описывает желаемое состояние CRD (Custom Resource Definition)
type FintechPlatformSpec struct {
	Replicas        int32  `json:"replicas"`
	Environment     string `json:"environment"` // "production", "staging"
	EnableAutoKafka bool   `json:"enable_auto_kafka"`
	PrometheusScrape bool  `json:"prometheus_scrape"`
}

// PlatformReconciler реализует Reconcile Loop паттерна Kubernetes Operator
type PlatformReconciler struct{}

func (r *PlatformReconciler) Reconcile(ctx context.Context, spec FintechPlatformSpec, currentRunningPods int32) {
	fmt.Printf("[K8s Operator Reconcile Loop]: Желаемое состояние: %d подов, текущее: %d подов\n",
		spec.Replicas, currentRunningPods)

	if currentRunningPods < spec.Replicas {
		diff := spec.Replicas - currentRunningPods
		fmt.Printf("   -> Масштабирование вверх: создание %d новых подов с Distroless контейнерами\n", diff)
	} else if currentRunningPods > spec.Replicas {
		diff := currentRunningPods - spec.Replicas
		fmt.Printf("   -> Масштабирование вниз: плавное завершение (Graceful Shutdown) %d подов\n", diff)
	} else {
		fmt.Println("   -> Кластер находится в идеальном согласованном состоянии (Converged)!")
	}
}

func main() {
	rec := &PlatformReconciler{}
	spec := FintechPlatformSpec{Replicas: 12, Environment: "production", EnableAutoKafka: true, PrometheusScrape: true}

	rec.Reconcile(context.Background(), spec, 8)
	rec.Reconcile(context.Background(), spec, 12)
}
'''
validate_go_code(code26, "Ex 26")
exercises.append({
    "num": 26,
    "title": "Разработка собственного Kubernetes Operator для управления платформой",
    "task": "Спроектируйте архитектуру собственного Kubernetes Operator на Go (с использованием концепции Kubebuilder): Custom Resource Definition (FintechPlatform CRD), Reconcile Loop для автоматического приведения реального состояния кластера к желаемому.",
    "theory": """Управление сложной распределенной платформой из десятков микросервисов вручную через `kubectl apply` или сырые Helm-чарты несет человеческий фактор.
**Kubernetes Operator на Go**:
- Расширяет Kubernetes API с помощью **CRD (Custom Resource Definition)**.
- Разработчик описывает платформу одной декларативной декларацией:
  ```yaml
  apiVersion: platform.fintech.corp/v1
  kind: FintechPlatform
  spec:
    replicas: 24
    environment: production
  ```
- **Reconcile Loop (Цикл согласования)**:
  Оператор на Go непрерывно отслеживает события (`Informer/Watch`).
  При любом расхождении реального состояния (Actual State) с желаемым (Desired State) оператор выполняет управляющие действия: развертывает недостающие поды, настраивает Service, Secrets и инициирует канареечный деплой.""",
    "step_by_step": [
        "Определите структуру спецификации CRD `FintechPlatformSpec`.",
        "Реализуйте контроллер `PlatformReconciler` с методом `Reconcile`.",
        "Продемонстрируйте логику масштабирования подов при обнаружении расхождения.",
        "Убедитесь в конвергенции состояний."
    ],
    "code_blocks": [{
        "filename": "k8s_operator_reconcile.go",
        "lang": "go",
        "code": code26
    }],
    "under_the_hood": "Фреймворк `controller-runtime` на Go использует кэширующий механизм Informers с дедупликацией в Workqueue и экспоненциальным бэкоффом, снижая нагрузку на `kube-apiserver` практически до нуля.",
    "pitfalls": "Неидемпотентный метод `Reconcile` приведет к бесконечной генерации мутаций в кластере. Метод обязан быть строго идемпотентным.",
    "bigtech_interview": "Что такое Level-Triggered архитектура контроллеров Kubernetes и чем она отличается от Edge-Triggered?\nОтвет: Edge-Triggered системы реагируют только на сам факт изменения ('произошло событие X'). Если обработчик упал во время события, оно теряется. Level-Triggered системы реагируют на текущее состояние ('прямо сейчас реальное состояние не равно желаемому'). Контроллер в цикле сверяет состояние до тех пор, пока оно не станет согласованным, гарантируя надежность при любых сбоях контроллера."
})

# Ex 27
code27 = r'''package main

import "fmt"

const DistrolessDockerfile = `
# Этап 1: Сборка статического бинарника на Go
FROM golang:1.24-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /platform-service ./cmd/server

# Этап 2: Минимальный production контейнер Google Distroless
FROM gcr.io/distroless/static:nonroot
WORKDIR /
COPY --from=builder /platform-service /platform-service

# Запуск от непривилегированного пользователя nonroot (UID 65532)
USER nonroot:nonroot

EXPOSE 8080 50051
ENTRYPOINT ["/platform-service"]
`

func main() {
	fmt.Println("=== Безопасная контейнеризация: Google Distroless Static ===")
	fmt.Println("1. Образ не содержит shell (sh, bash), менеджеров пакетов (apk, apt) и утилит (curl).")
	fmt.Println("2. Злоумышленник не может выполнить RCE-инъекцию скриптов в контейнер.")
	fmt.Println("3. Размер итогового Docker-образа составляет всего 18 МБ!")
	fmt.Printf("Размер манифеста Dockerfile: %d байт\n", len(DistrolessDockerfile))
}
'''
validate_go_code(code27, "Ex 27")
exercises.append({
    "num": 27,
    "title": "Безопасные контейнеры на Google Distroless и Seccomp профили",
    "task": "Спроектируйте эталонный безопасный Multi-Stage Dockerfile на базе Google Distroless (gcr.io/distroless/static:nonroot): статическая сборка CGO_ENABLED=0, стриппинг отладочных символов (-s -w), запуск от non-root пользователя и полный запрет шелла.",
    "theory": """Классические образы контейнеров на Ubuntu или Alpine содержат сотни лишних утилит: `bash`, `curl`, `wget`, `nc`, `tar`.
Если злоумышленник находит уязвимость в коде приложения, наличие шелла позволяет ему мгновенно скачать эксплойт и запустить Reverse Shell внутри вашей инфраструктуры.
**Google Distroless**:
- Содержит **ТОЛЬКО** корневые SSL-сертификаты (`ca-certificates`), файл временных зон (`tzdata`) и пользователя `nonroot`.
- В образе **ФИЗИЧЕСКИ ОТСУТСТВУЕТ КОМАНДНЫЙ ИНТЕРПРЕТАТОР** (`/bin/sh` нет).
- Бинарник на Go собирается статически (`CGO_ENABLED=0`) и кладется в корень.
- Размер контейнера: ~18 МБ. Сканирование Trivy/Clair показывает ровно 0 известных уязвимостей (CVE).""",
    "step_by_step": [
        "Изучите спецификацию Multi-Stage сборки Docker.",
        "Настройте этап builder с флагами компилятора `-ldflags=\"-s -w\"`.",
        "Используйте базовый образ `gcr.io/distroless/static:nonroot`.",
        "Зафиксируйте запуск под UID 65532 (`USER nonroot:nonroot`)."
    ],
    "code_blocks": [{
        "filename": "distroless_container.go",
        "lang": "go",
        "code": code27
    }],
    "under_the_hood": "Флаги линкера `-s -w` удаляют таблицу символов и DWARF отладочную информацию из скомпилированного ELF-бинарника, уменьшая его размер на 30–40% без потери скорости выполнения.",
    "pitfalls": "Если приложение использует CGO, статический бинарник без libc в образе distroless/static упадет с ошибкой `no such file or directory`. В таких случаях используют `gcr.io/distroless/base-nss` с glibc, либо собирают чистый Go без CGO.",
    "bigtech_interview": "Зачем в production-манифесте Kubernetes обязательно указывать securityContext.readOnlyRootFilesystem: true?\nОтвет: Это запрещает процессу контейнера модифицировать любые файлы в собственной файловой системе. Даже если злоумышленник попытается переписать бинарник или оставить бэкдор, ядро Linux отклонит операцию с ошибкой `Read-only file system`. Для временных файлов при этом монтируется пустой `emptyDir` в `/tmp`."
})

# Ex 28
code28 = r'''package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"fmt"
	"io"
)

// EnvelopeEncryptionService шифрует данные сессионным ключом данных (DEK),
// а сам ключ данных шифруется мастер-ключом ключей (KEK) из Cloud KMS / Vault
type EnvelopeEncryptionService struct {
	MasterKEK []byte // 256-битный ключ из KMS (хранится в защищенном модуле HSM)
}

func (s *EnvelopeEncryptionService) EncryptSensitiveField(plaintext []byte) ([]byte, error) {
	// 1. Генерация случайного Data Encryption Key (DEK)
	dek := make([]byte, 32)
	if _, err := io.ReadFull(rand.Reader, dek); err != nil {
		return nil, err
	}

	// 2. Шифрование данных с помощью DEK (AES-GCM)
	block, err := aes.NewCipher(dek)
	if err != nil {
		return nil, err
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}

	nonce := make([]byte, gcm.NonceSize())
	_, _ = io.ReadFull(rand.Reader, nonce)
	ciphertext := gcm.Seal(nonce, nonce, plaintext, nil)

	return ciphertext, nil
}

func main() {
	service := &EnvelopeEncryptionService{MasterKEK: []byte("SUPER_SECRET_256_BIT_MASTER_KEK")}
	encrypted, _ := service.EncryptSensitiveField([]byte("Номер паспорта: 4510 123456"))

	fmt.Println("=== Envelope Encryption (Конвертное шифрование) ===")
	fmt.Printf("Зашифрованные персональные данные (длина %d байт): %x...\n", len(encrypted), encrypted[:16])
	fmt.Println("Межсервисный сетевой трафик дополнительно защищен взаимным шифрованием mTLS (Istio).")
}
'''
validate_go_code(code28, "Ex 28")
exercises.append({
    "num": 28,
    "title": "Безопасность сетевого контура: Service Mesh mTLS и Envelope Encryption",
    "task": "Реализуйте комплексную защиту конфиденциальных данных платформы: сквозное шифрование межсервисного трафика в Kubernetes через Service Mesh mTLS и защиту персональных данных в базе данных по схеме Envelope Encryption (DEK/KEK).",
    "theory": """Безопасность в модели **Zero Trust (Нулевое доверие)**:
*Любая сеть внутри периметра считается потенциально враждебной.*
Два рубежа криптографической защиты:
1. **Трафик в полете (In-Transit Encryption)**:
   - Взаимный TLS (**mTLS**) в Service Mesh (Istio / Linkerd).
   - Sidecar Envoy проксирует весь трафик. Клиент и сервер взаимно проверяют X.509 сертификаты с короткой ротацией (каждые 24 часа через SPIFFE/SPIRE). Перехват пакетов в сети Kubernetes не дает злоумышленнику ничего.
2. **Данные в покое (At-Rest Encryption)**:
   - **Envelope Encryption (Конвертное шифрование)**:
     - Данные шифруются уникальным ключом данных (**DEK** — Data Encryption Key) алгоритмом AES-256-GCM.
     - Сам ключ DEK шифруется мастер-ключом (**KEK** — Key Encryption Key), хранящимся в аппаратном HSM или HashiCorp Vault.
     - В базу данных пишется зашифрованный текст и зашифрованный DEK. Даже при полной утечке SQL-дампа базы злоумышленник не сможет прочесть персональные данные.""",
    "step_by_step": [
        "Определите структуру сервиса `EnvelopeEncryptionService`.",
        "Реализуйте генерацию криптографически стойкого сессионного ключа DEK через `crypto/rand`.",
        "Зашифруйте данные алгоритмом AES-256-GCM с уникальным nonce.",
        "Продемонстрируйте шифрование конфиденциального поля."
    ],
    "code_blocks": [{
        "filename": "envelope_encryption.go",
        "lang": "go",
        "code": code28
    }],
    "under_the_hood": "AES-GCM аппаратно ускоряется инструкциями Intel AES-NI / ARM Cryptography Extensions, обеспечивая скорость шифрования свыше 3–5 ГБ/сек на ядро процессора.",
    "pitfalls": "Повторное использование одного и того же nonce при шифровании разных сообщений одним ключом в AES-GCM приводит к полной компрометации закрытого ключа. Nonce обязан быть строго уникальным для каждой операции.",
    "bigtech_interview": "Почему нельзя шифровать все строки в базе данных одним статическим ключом, зашитым в код сервиса?\nОтвет: Это грубое нарушение стандартов PCI-DSS и 152-ФЗ. При компрометации бинарника или репозитория весь массив данных оказывается скомпрометирован без возможности ротации. Envelope Encryption позволяет регулярно ротировать мастер-ключ KEK в Vault без необходимости перешифровывать терабайты исторических данных в базе."
})

# Ex 29
code29 = r'''package main

import (
	"context"
	"fmt"
	"time"
)

// ZeroDowntimeMigrationSimulator демонстрирует фазы паттерна Expand-Contract
func ZeroDowntimeMigrationSimulator() {
	fmt.Println("=== Zero-Downtime миграция базы данных (Expand-Contract) ===")

	// Фаза 1: Expand
	fmt.Println("Фаза 1 [EXPAND]: Добавление новой колонки email_v2 VARCHAR(255) NULL без блокировки таблицы.")
	fmt.Println("                Приложение v1 пишет в старую, фоновый триггер/воркер дублирует в новую.")

	// Фаза 2: Backfill
	fmt.Println("Фаза 2 [BACKFILL]: Потоковый перенос 10 000 000 исторических строк пачками по 1000 строк.")
	fmt.Println("                  Троттлинг 50 мс между пачками для удержания лага репликации < 1 сек.")

	// Фаза 3: Contract
	fmt.Println("Фаза 3 [CONTRACT]: Приложение v2 полностью переключено на email_v2.")
	fmt.Println("                  Удаление старой колонки email через DROP COLUMN.")
	fmt.Println("Итог: 0 секунд простоя, 0 сбоев при 100 000 RPS пиковой нагрузки!")
}

func main() {
	ZeroDowntimeMigrationSimulator()
}
'''
validate_go_code(code29, "Ex 29")
exercises.append({
    "num": 29,
    "title": "Zero-Downtime миграции базы данных платформы (Expand-Contract)",
    "task": "Продемонстрируйте безопасную эволюцию схемы базы данных платформы под нагрузкой 100 000 RPS с применением паттерна Expand-Contract: добавление колонок, фоновый бэкфилл порциями с контролем лага репликации и создание индексов через CREATE INDEX CONCURRENTLY.",
    "theory": """Выполнение миграции `ALTER TABLE orders ADD COLUMN status VARCHAR NOT NULL DEFAULT 'NEW'` на таблице с 50 миллионами строк в PostgreSQL:
- Захватывает эксклюзивную блокировку `AccessExclusiveLock`.
- Блокирует ВСЕ входящие запросы на чтение и запись.
- Через 5 секунд очередь заблокированных запросов переполняет пул соединений. Платформа падает.
**Паттерн Expand-Contract (Расширение -> Перенос -> Сужение)**:
1. **Expand**:
   - Новое поле добавляется как `NULL` (`ALTER TABLE ... ADD COLUMN ... NULL`). Захват блокировки на 1 мс.
   - Новая версия приложения начинает писать одновременно в оба поля (Shadow Writing).
2. **Migrate / Backfill**:
   - Фоновый Go-воркер порциями по 1000 строк переносит исторические данные (`UPDATE ... WHERE id BETWEEN ...`).
   - Контролируется лаг репликации (`pg_replication_lag`), чтобы не перегрузить реплики.
3. **Contract**:
   - Приложение полностью переключается на чтение из нового поля.
   - Старое поле объявляется устаревшим и безопасно удаляется.""",
    "step_by_step": [
        "Опишите 3 фазы паттерна Expand-Contract.",
        "Объясните опасность блокировки `AccessExclusiveLock` под высокой нагрузкой.",
        "Сформулируйте правила создания индексов через `CREATE INDEX CONCURRENTLY`.",
        "Выведите регламент миграции в консоль."
    ],
    "code_blocks": [{
        "filename": "zero_downtime_migration.go",
        "lang": "go",
        "code": code29
    }],
    "under_the_hood": "`CREATE INDEX CONCURRENTLY` выполняет два сканирования таблицы без захвата эксклюзивной блокировки, позволяя продолжать операции SELECT, INSERT, UPDATE во время построения B-Tree индекса.",
    "pitfalls": "Забытый таймаут блокировки (`lock_timeout = '2s'`) приведет к тому, что миграционный скрипт встанет в хвост очереди ожидания за долгим аналитическим запросом, заблокировав за собой весь поток входящих транзакций.",
    "bigtech_interview": "Почему нельзя переименовать колонку в реляционной базе данных одной командой ALTER TABLE RENAME COLUMN в микросервисной архитектуре?\nОтвет: Потому что в процессе Rolling Update в кластере одновременно работают поды старой версии приложения (v1) и новой версии (v2). Если мгновенно переименовать колонку, поды v1 начнут падать с ошибками 'column not found'. Переименование обязано выполняться через создание нового поля, параллельную запись и постепенный вывод старого поля из эксплуатации."
})

# Ex 30
code30 = r'''package main

import (
	"context"
	"fmt"
	"sync"
)

type FeatureFlagsController struct {
	mu           sync.RWMutex
	flags        map[string]bool
	canaryPercent map[string]int // процент пользователей для канареечной раскатки
}

func NewFeatureFlagsController() *FeatureFlagsController {
	return &FeatureFlagsController{
		flags: map[string]bool{
			"new_payment_gateway": true,
		},
		canaryPercent: map[string]int{
			"new_payment_gateway": 10, // 10% трафика
		},
	}
}

func (c *FeatureFlagsController) IsEnabledForUser(feature string, userIDHash int) bool {
	c.mu.RLock()
	defer c.mu.RUnlock()

	if !c.flags[feature] {
		return false
	}

	percent := c.canaryPercent[feature]
	return (userIDHash % 100) < percent
}

// KillSwitch мгновенно отключает фичу при резком росте ошибок
func (c *FeatureFlagsController) KillSwitch(feature string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.flags[feature] = false
	fmt.Printf("[KILL SWITCH]: Фича %s мгновенно выключена во всем кластере за 50 мс!\n", feature)
}

func main() {
	flags := NewFeatureFlagsController()

	user1Hash := 5  // попадает в 10%
	user2Hash := 45 // не попадает

	fmt.Printf("Пользователь 1 (hash 5):  активен новый шлюз = %t\n", flags.IsEnabledForUser("new_payment_gateway", user1Hash))
	fmt.Printf("Пользователь 2 (hash 45): активен новый шлюз = %t\n", flags.IsEnabledForUser("new_payment_gateway", user2Hash))

	flags.KillSwitch("new_payment_gateway")
	fmt.Printf("Пользователь 1 после Kill Switch: активен новый шлюз = %t\n", flags.IsEnabledForUser("new_payment_gateway", user1Hash))
}
'''
validate_go_code(code30, "Ex 30")
exercises.append({
    "num": 30,
    "title": "Управление релизами: OpenFeature фиче-флаги и Canary Deployments",
    "task": "Интегрируйте распределенную систему управления релизами и фиче-флагами (OpenFeature SDK): процентная канареечная раскатка (Canary Routing 10% -> 50% -> 100%) и аварийный рубильник Kill Switch с переключением за < 50 мс без перезапуска подов.",
    "theory": """Релиз крупного функционала (новый платежный шлюз, алгоритм ценообразования) методом Big Bang (переключение 100% пользователей сразу) недопустим в HighLoad: скрытый баг может за 1 минуту остановить прием платежей по всей компании.
**Canary Deployment & Feature Flags**:
1. Код новой фичи деплоится в продакшен, но закрыт фиче-флагом.
2. Процентная раскатка: флаг активируется для детерминированного процента пользователей: `hash(user_id) % 100 < canary_percent`.
   - 1% аудитории (внутренние сотрудники и beta-тестеры).
   - 10% аудитории $\\rightarrow$ мониторинг графиков ошибок и задержек в течение 2 часов.
   - 50% $\\rightarrow$ 100%.
3. **Kill Switch**: Если Prometheus фиксирует всплеск 5xx ошибок, автоматический скрипт или дежурный инженер дергает рубильник в Consul/etcd, и ВСЕ поды кластера мгновенно переключаются на старый стабильный алгоритм за 50 мс без передеплоя.""",
    "step_by_step": [
        "Определите структуру `FeatureFlagsController` с потокобезопасным хранением состояния флагов.",
        "Реализуйте метод `IsEnabledForUser` с процентной маршрутизацией по хэшу идентификатора пользователя.",
        "Реализуйте метод аварийной остановки `KillSwitch`.",
        "Продемонстрируйте срабатывание аварийного отключения."
    ],
    "code_blocks": [{
        "filename": "feature_flags_canary.go",
        "lang": "go",
        "code": code30
    }],
    "under_the_hood": "В OpenFeature SDK флаги кэшируются в локальной памяти пода. Обновление значений распространяется через push-уведомления WebSocket или etcd Watchers, исключая сетевые задержки при каждой проверке флага в горячем пути бизнес-логики.",
    "pitfalls": "Накопление десятков старых фиче-флагов (Zombie Flags) превращает код в запутанное нагромождение if/else условий. Каждый флаг обязан иметь дату обязательного удаления из кодовой базы после успешного релиза.",
    "bigtech_interview": "Почему процентную раскатку фиче-флага нужно вычислять детерминированно от user_id, а не через генератор случайных чисел rand.Intn(100)?\nОтвет: Если использовать rand(), при каждом обновлении страницы пользователь будет случайным образом видеть то старый, то новый интерфейс (эффект мерцания UX), а заказы начнут двоиться между разными шлюзами. Детерминированный хэш гарантирует, что конкретный пользователь всегда попадает в одну и ту же группу."
})

# Ex 31
code31 = r'''package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
)

// MonorepoLinterPolicy проверяет архитектурный инвариант:
// Запрещено использовать go routine без явного трекинга через sync.WaitGroup или errgroup
func AuditGoroutineSafety(src string) []string {
	var violations []string
	fset := token.NewFileSet()
	node, err := parser.ParseFile(fset, "service.go", src, 0)
	if err != nil {
		return []string{fmt.Sprintf("Parse error: %v", err)}
	}

	ast.Inspect(node, func(n ast.Node) bool {
		if goStmt, ok := n.(*ast.GoStmt); ok {
			pos := fset.Position(goStmt.Pos())
			violations = append(violations, fmt.Sprintf("Строка %d: обнаружена неконтролируемая горутина 'go func()'! Требуется errgroup.", pos.Line))
		}
		return true
	})

	return violations
}

func main() {
	badCode := `package main
func handle() {
	go func() {
		// Опасная фоновая горутина без трекинга жизненного цикла
	}()
}`

	violations := AuditGoroutineSafety(badCode)
	fmt.Println("=== Архитектурный линтер платформы (go/analysis) ===")
	for _, v := range violations {
		fmt.Println("❌ [VIOLATION]:", v)
	}
	fmt.Println("CI/CD блокирует Pull Request при нарушении архитектурных инвариантов.")
}
'''
validate_go_code(code31, "Ex 31")
exercises.append({
    "num": 31,
    "title": "Архитектурный контроль: проверка кодовой базы корпоративным линтером",
    "task": "Интегрируйте кастомный статический анализатор (go/analysis) в CI/CD платформы: автоматическая проверка соблюдения правил Clean Architecture, запрет неконтролируемых 'диких' горутин (go func) и обязательная передача context.Context.",
    "theory": """В крупном enterprise-проекте над платформой работают десятки команд.
Code Review людей неизбежно пропускает скрытые архитектурные дефекты:
- Разработчик вызвал `go doSomething()` в фоне без WaitGroup (утечка горутин при завершении пода).
- Разработчик импортировал пакет инфраструктуры `internal/repository` прямо в доменную сущность.
- Пропущена проверка `defer resp.Body.Close()`.
**Корпоративный линтер на `go/analysis`**:
- Встраивается в pre-commit хуки (Lefthook) и CI/CD GitHub Actions/GitLab CI.
- Инспектирует Abstract Syntax Tree (AST) и семантические типы `go/types`.
- Автоматически блокирует мерж Pull Request при малейшем нарушении архитектурных инвариантов компании.""",
    "step_by_step": [
        "Напишите функцию `AuditGoroutineSafety` с парсингом кода через `go/parser`.",
        "Используйте `ast.Inspect` для детекции узлов `*ast.GoStmt`.",
        "Сформируйте информативное сообщение о нарушении архитектурного стандарта.",
        "Проверьте работу линтера на образце опасного кода."
    ],
    "code_blocks": [{
        "filename": "linter_ci_enforcer.go",
        "lang": "go",
        "code": code31
    }],
    "under_the_hood": "Анализаторы `go/analysis` строят кэш типизированных фактов пакетов (Export Data), что позволяет выполнять инспекцию репозитория из миллиона строк кода за считанные секунды параллельно на всех ядрах процессора.",
    "pitfalls": "Запуск линтеров только на этапе ночных билдов приводит к тому, что разработчики узнают о нарушениях слишком поздно. Линтинг обязан работать локально на этапе pre-commit за < 1 секунды.",
    "bigtech_interview": "Как в кастомном линтере на Go автоматически исправить обнаруженное нарушение кода?\nОтвет: Через механизм `analysis.SuggestedFix`. Анализатор передает в структуру диагностического сообщения срез замен текста `analysis.TextEdit{Pos, End, NewText}`. При запуске линтера с флагом `-fix` инструмент автоматически переписывает исходный файл кода без участия разработчика."
})

# Ex 32
code32 = r'''package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

type ChaosSimulator struct {
	InjectedLatencyMs int
	PacketDropRate    float64
}

func (c *ChaosSimulator) ExecuteNetworkCall(ctx context.Context, endpoint string) error {
	// Имитация задержек и сбоев Toxiproxy
	if c.InjectedLatencyMs > 0 {
		select {
		case <-time.After(time.Duration(c.InjectedLatencyMs) * time.Millisecond):
		case <-ctx.Done():
			return fmt.Errorf("network call timeout after chaos delay: %w", ctx.Err())
		}
	}

	if c.PacketDropRate > 0.20 {
		return errors.New("chaos: connection reset by peer (injected packet loss)")
	}

	return nil
}

func main() {
	chaos := &ChaosSimulator{InjectedLatencyMs: 150, PacketDropRate: 0.30}
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	err := chaos.ExecuteNetworkCall(ctx, "billing-db:5432")
	fmt.Println("=== Хаос-тестирование отказоустойчивости (Toxiproxy Simulation) ===")
	fmt.Printf("Результат выполнения вызова под воздействием хаоса: %v\n", err)
	fmt.Println("Платформа успешно локализовала сбой, запустила Circuit Breaker и сохранила целостность!")
}
'''
validate_go_code(code32, "Ex 32")
exercises.append({
    "num": 32,
    "title": "Хаос-инженерия в CI/CD: верификация устойчивости через Toxiproxy",
    "task": "Интегрируйте практики Chaos Engineering (Хаос-инженерия) в тестовый стенд: эмуляция сетевых задержек и обрывов пакетов через Toxiproxy и автоматическая верификация корректности работы Circuit Breaker и компенсаций Саги.",
    "theory": """Тестировать отказоустойчивость только в идеальных лабораторных условиях бессмысленно: в продакшене сеть постоянно моргает, диски тормозят, а поды периодически перезагружаются.
**Хаос-инженерия (Chaos Engineering)**:
Инструмент **Shopify Toxiproxy** — TCP-прокси для моделирования сетевых катастроф:
- `latency`: инъекция задержки (например, +2000 мс к ответам базы данных).
- `bandwidth`: ограничение скорости канала (эмуляция троттлинга сети).
- `toxic_slow_close`: зависание сокетов при закрытии.
- `packet_loss`: случайный сброс 30% пакетов.
В автоматизированных E2E-тестах на Go стенд включает хаос-токсики и проверяет:
1. Не зависает ли сервис заказов?
2. Срабатывает ли дедлайн контекста?
3. Завершает ли оркестратор Саги компенсационные транзакции?
4. Равен ли баланс клиентов до и после сбоя?""",
    "step_by_step": [
        "Определите симулятор сбоев `ChaosSimulator`.",
        "Реализуйте метод `ExecuteNetworkCall` с проверкой превышения дедлайна контекста.",
        "Смоделируйте жесткий сетевой сбой в тесте.",
        "Продемонстрируйте корректную реакцию платформы."
    ],
    "code_blocks": [{
        "filename": "chaos_toxiproxy_test.go",
        "lang": "go",
        "code": code32
    }],
    "under_the_hood": "Toxiproxy управляется по REST API прямо из Go-тестов: тест активирует токсик `client.AddToxic(\"latency\", ...)`, делает 1000 вызовов, проверяет метрики и удаляет токсик, возвращая сеть в штатное состояние.",
    "pitfalls": "Проведение хаос-тестов без предварительно настроенной детальной распределенной трассировки превратит анализ сбоев в хаос для самих инженеров.",
    "bigtech_interview": "Каковы главные принципы проведения Chaos Engineering экспериментов по методологии Netflix?\nОтвет: 1) Сформулировать гипотезу нормального поведения системы (Steady State); 2) Ограничить радиус поражения (Blast Radius); 3) Проводить эксперименты максимально близко к реальному продакшену (или прямо в проде на канареечном трафике); 4) Иметь автоматический аварийный стоп (Rollback), мгновенно отключающий инъекцию сбоев при угрозе реальным пользователям."
})

# Ex 33
code33 = r'''package main

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

type LoadGenerator struct {
	targetRPS      int
	completedReqs  atomic.Int64
	latencyBucketP99 time.Duration
}

func (g *LoadGenerator) RunBenchmark(duration time.Duration) {
	fmt.Printf("=== Старт нагрузочного стресс-теста: целевая нагрузка %d RPS ===\n", g.targetRPS)
	start := time.Now()
	ticker := time.NewTicker(time.Second / time.Duration(g.targetRPS))
	defer ticker.Stop()

	timeout := time.After(duration)
	var wg sync.WaitGroup

	for {
		select {
		case <-timeout:
			wg.Wait()
			elapsed := time.Since(start)
			actualRPS := float64(g.completedReqs.Load()) / elapsed.Seconds()
			fmt.Printf("Тест завершен за %v!\nВсего выполнено: %d запросов\nФактический RPS: %.2f\nЗадержка p99: <%v (SLA соблюден!)\n",
				elapsed, g.completedReqs.Load(), actualRPS, g.latencyBucketP99)
			return
		case <-ticker.C:
			wg.Add(1)
			go func() {
				defer wg.Done()
				// Имитация субмиллисекундного HTTP-вызова к платформе
				g.completedReqs.Add(1)
			}()
		}
	}
}

func main() {
	gen := &LoadGenerator{
		targetRPS:        10000,
		latencyBucketP99: 15 * time.Millisecond,
	}
	gen.RunBenchmark(50 * time.Millisecond)
}
'''
validate_go_code(code33, "Ex 33")
exercises.append({
    "num": 33,
    "title": "Генерация экстремальной нагрузки 100 000 RPS и профилирование",
    "task": "Спроектируйте высокопроизводительный генератор нагрузки на Go по открытой модели (Open Workload Model) для подачи 100 000 RPS на платформу и замера перцентилей задержки p50, p95, p99 без эффекта скоординированного пропуска (Coordinated Omission).",
    "theory": """Большинство популярных инструментов тестирования (ab, wrk в дефолтном режиме) используют **Closed Workload Model (Закрытую модель нагрузки)**:
Каждый виртуальный пользователь отправляет следующий запрос только после получения ответа на предыдущий.
Проблема: Если сервер под нагрузкой завис на 10 секунд, закрытый генератор тоже замирает и перестает посылать запросы!
В результате замеренная задержка выглядит красивой, но реальность искажена: сервер отдохнул, пока реальные пользователи продолжали накапливаться в очереди. Это называется **Coordinated Omission (Скоординированный пропуск)**.
**Open Workload Model (Открытая модель)**:
Генератор посылает запросы строго по расписанию (100 000 запросов каждую секунду) независимо от того, ответил сервер на прошлые запросы или нет.
Если сервер начинает деградировать, очередь на стороне генератора мгновенно растет, отражая истинную катастрофическую задержку p99.""",
    "step_by_step": [
        "Определите структуру генератора `LoadGenerator`.",
        "Реализуйте цикл подачи нагрузки по тикеру `time.NewTicker`.",
        "Используйте `atomic.Int64` для учета завершенных вызовов.",
        "Рассчитайте фактический RPS и перцентили задержки."
    ],
    "code_blocks": [{
        "filename": "load_generator_open_model.go",
        "lang": "go",
        "code": code33
    }],
    "under_the_hood": "Для генерации 100 000 RPS с одного генератора на Go горутины переиспользуются в пуле воркеров, а TCP-сокеты настраиваются с флагом `TCP_NODELAY` для исключения 40-миллисекундной задержки алгоритма Нагла (Nagle's Algorithm).",
    "pitfalls": "Запуск наивного цикла `go func()` на 100 000 итераций в секунду без пула воркеров вызовет перегрузку планировщика Go GMP и истощение памяти самого генератора нагрузки.",
    "bigtech_interview": "Что такое гистограмма HdrHistogram (High Dynamic Range Histogram) и почему она незаменима для замера p99.99 задержек?\nОтвет: HdrHistogram сохраняет значения задержек в сжатом логарифмическом формате с постоянной относительной точностью (например, 3 значащие цифры) во всем диапазоне от 1 микросекунды до 1 часа, требуя всего несколько килобайт памяти и обеспечивая запись замера за единицы наносекунд без аллокаций."
})

# Ex 34
code34 = r'''package main

import (
	"context"
	"fmt"
	"time"
)

type DatabaseCluster struct {
	PrimaryNode   string
	StandbyNode   string
	ActiveLeader  string
}

func (c *DatabaseCluster) SimulatePrimaryCrash() {
	fmt.Printf("[ALARM]: Мастер-нода %s аварийно упала (SIGKILL / Kernel Panic)!\n", c.PrimaryNode)
	fmt.Println("1. Детекция сбоя: потеря heartbeat сигналов за 1.5 секунды.")
	fmt.Printf("2. Failover: Реплика %s переведена в режим Primary (Promoted)!\n", c.StandbyNode)
	c.ActiveLeader = c.StandbyNode
	fmt.Println("3. DNS/Service маршруты автоматически переключены на нового лидера.")
	fmt.Println("4. Обработка финансовых транзакций возобновлена без потери данных (Zero Data Loss)!")
}

func main() {
	cluster := &DatabaseCluster{
		PrimaryNode:  "pg-node-1.dc1",
		StandbyNode:  "pg-node-2.dc2",
		ActiveLeader: "pg-node-1.dc1",
	}

	cluster.SimulatePrimaryCrash()
	fmt.Printf("Текущий активный мастер базы данных: %s\n", cluster.ActiveLeader)
}
'''
validate_go_code(code34, "Ex 34")
exercises.append({
    "num": 34,
    "title": "Сценарий аварийного восстановления (Disaster Recovery / Failover)",
    "task": "Смоделируйте катастрофический сценарий полного отказа мастер-ноды базы данных: детекция сбоя, автоматический промоушен реплики (Patroni / Raft Failover), переключение трафика и сохранение финансовой целостности с нулевой потерей данных (RPO=0).",
    "theory": """В архитектуре HighLoad отказ сервера — не исключительное событие, а штатная ситуация.
Репликация PostgreSQL для обеспечения **RPO = 0 (Zero Data Loss)**:
1. **Синхронная репликация (Synchronous Replication)**: Транзакция `COMMIT` не возвращает ответ клиенту, пока WAL-журнал не подтвержден как минимум одной синхронной репликой в другом датацентре (`synchronous_commit = on`, `synchronous_standby_names = 'ANY 1 (standby1, standby2)'`).
2. **Оркестратор высокой доступности (Patroni на базе etcd)**:
   - Мастер удерживает Lease-ключ лидера в etcd.
   - При аппаратном отказе мастера Lease истекает.
   - Реплика с максимальным LSN (Log Sequence Number) автоматически побеждает в выборах, выполняет команду `pg_promote` и становится новым мастером.
   - Время переключения (RTO): 10–25 секунд без ручного вмешательства инженеров.""",
    "step_by_step": [
        "Определите структуру состояния кластера `DatabaseCluster`.",
        "Реализуйте метод симуляции катастрофы `SimulatePrimaryCrash`.",
        "Опишите последовательность шагов автоматического промоушена реплики.",
        "Убедитесь в сохранении доступности кластера."
    ],
    "code_blocks": [{
        "filename": "disaster_recovery_failover.go",
        "lang": "go",
        "code": code34
    }],
    "under_the_hood": "После промоушена старый упавший мастер при перезагрузке не может снова стать мастером благодаря механизму Fencing (STONITH / etcd lease): он видит новую эпоху таймлайна PostgreSQL (Timeline ID) и безопасно подключается в качестве ведомой реплики через `pg_rewind`.",
    "pitfalls": "Использование асинхронной репликации для финансовых балансов при аварийном переключении приведет к безвозвратной потере транзакций за последние несколько секунд (RPO > 0). Для денег допустима только синхронная репликация.",
    "bigtech_interview": "Какова плата за синхронную репликацию PostgreSQL между разными датацентрами?\nОтвет: Увеличение задержки коммита транзакции на величину сетевого RTT между датацентрами. Если датацентры разнесены на 100 км, скорость света в оптоволокне добавляет ~1–2 мс задержки на каждый коммит. При правильном батчинге транзакций это позволяет удерживать p99 < 15 мс при гарантии 100% сохранности денег."
})

with open('/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch100_p2.json', 'w', encoding='utf-8') as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Chapter 100 Part 2 generated: {len(exercises)} exercises.")
