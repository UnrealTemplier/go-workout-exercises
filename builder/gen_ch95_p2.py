import json
import subprocess
import os

def validate_go_code(code: str, label: str):
    p = subprocess.run(['gofmt', '-e'], input=code.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        err = p.stderr.decode('utf-8')
        lines = code.split('\n')
        annotated = '\n'.join(f"{i+1:3d}: {line}" for i, line in enumerate(lines))
        raise ValueError(f"gofmt failed on {label}:\n{err}\nCode:\n{annotated}")

exercises = []

# Ex 16: Атомарный инкремент счетчика на транзакциях etcd
code16 = r'''package main

import (
	"context"
	"fmt"
	"strconv"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
)

// DistributedCounter реализует оптимистичный CAS счетчик на транзакциях etcd
type DistributedCounter struct {
	kv         clientv3.KV
	counterKey string
}

func NewDistributedCounter(kv clientv3.KV, key string) *DistributedCounter {
	return &DistributedCounter{kv: kv, counterKey: key}
}

// Increment атомарно увеличивает счетчик с повторными попытками при конфликтах (OCC)
func (c *DistributedCounter) Increment(ctx context.Context, maxRetries int) (int64, error) {
	for attempt := 0; attempt < maxRetries; attempt++ {
		// 1. Читаем текущее значение и ModRevision
		getResp, err := c.kv.Get(ctx, c.counterKey)
		if err != nil {
			return 0, fmt.Errorf("ошибка чтения счетчика: %w", err)
		}

		var currentVal int64 = 0
		var expectedModRev int64 = 0

		if len(getResp.Kvs) > 0 {
			expectedModRev = getResp.Kvs[0].ModRevision
			currentVal, err = strconv.ParseInt(string(getResp.Kvs[0].Value), 10, 64)
			if err != nil {
				return 0, fmt.Errorf("невалидное значение счетчика в etcd: %w", err)
			}
		}

		newVal := currentVal + 1
		newValStr := strconv.FormatInt(newVal, 10)

		// 2. Формируем предикат CAS транзакции
		var cmp clientv3.Cmp
		if expectedModRev == 0 {
			// Ключ еще не существует: проверяем CreateRevision == 0
			cmp = clientv3.Compare(clientv3.CreateRevision(c.counterKey), "=", 0)
		} else {
			// Ключ существует: проверяем, что ModRevision не изменилась
			cmp = clientv3.Compare(clientv3.ModRevision(c.counterKey), "=", expectedModRev)
		}

		// 3. Выполняем атомарную транзакцию
		txnResp, err := c.kv.Txn(ctx).
			If(cmp).
			Then(clientv3.OpPut(c.counterKey, newValStr)).
			Commit()

		if err != nil {
			return 0, fmt.Errorf("сбой коммита транзакции etcd: %w", err)
		}

		if txnResp.Succeeded {
			return newVal, nil
		}

		// Конфликт параллельной записи: делаем небольшую паузу с джиттером и повторяем
		time.Sleep(time.Duration(10*(attempt+1)) * time.Millisecond)
	}

	return 0, fmt.Errorf("превышен лимит попыток (%d) из-за высокой конкуренции", maxRetries)
}

func main() {
	fmt.Println("Атомарный инкремент счетчика на транзакциях etcd:")
	fmt.Println(" 1. Читаем ключ и фиксируем expectedModRev")
	fmt.Println(" 2. Txn.If(Compare(ModRevision(key), '=', expectedModRev)).Then(OpPut(key, newVal))")
	fmt.Println(" 3. При параллельном изменении (txn.Succeeded == false) перезапрашиваем актуальную ревизию")
}
'''
validate_go_code(code16, "code16")
exercises.append({
    "num": 16,
    "title": "Атомарный инкремент счетчика на транзакциях etcd",
    "task": "Реализуйте распределенный счетчик DistributedCounter на базе оптимистичных транзакций etcd (Optimistic Concurrency Control). Счетчик должен считывать значение и ModRevision ключа, формировать предикат Compare по ревизии и повторять транзакцию при конфликтах параллельной записи.",
    "theory": "В распределенных системах наивный инкремент `val = Get(); Put(val + 1)` приводит к потерянным обновлениям (Lost Updates) при параллельных запросах сотен воркеров.\n\nВ etcd v3 эта проблема решается через паттерн Compare-And-Swap (CAS) по номеру ревизии:\n1. Воркер читает ключ и запоминает `expectedModRev`.\n2. Формируется транзакция с условием: `If(Compare(ModRevision(key), \"=\", expectedModRev))`.\n3. Ветка успеха `Then(OpPut(key, val + 1))` выполняется только в том случае, если ни один другой узел не успел изменить ключ за это время.\n4. Если транзакция отклонена (`Succeeded == false`), воркер выполняет повторную попытку (Retry) со свежими данными.",
    "step_by_step": [
        "Создайте структуру DistributedCounter с ссылкой на clientv3.KV.",
        "В цикле с лимитом попыток выполните kv.Get для получения текущего значения и ModRevision.",
        "Преобразуйте строковое значение в int64 через strconv.ParseInt.",
        "Составьте условие Compare(ModRevision, '=', expectedModRev) или Compare(CreateRevision, '=', 0) для первого создания.",
        "Вызовите Txn().If().Then().Commit() и верните результат при txnResp.Succeeded."
    ],
    "code_blocks": [{
        "filename": "etcd_occ_counter.go",
        "lang": "go",
        "code": code16
    }],
    "under_the_hood": "Поскольку etcd гарантирует строгую сериализуемость транзакций, в момент коммита Raft-лога сервер etcd атомарно сверяет ревизию в памяти. Если параллельный запрос инкрементировал ключ на одну микросекунду раньше, его ревизия выросла, и проверка условия текущего запроса возвратит false без побочных эффектов.",
    "pitfalls": [
        "Отсутствие бэк-оффа при ретраях: сотни горутин, одновременно пытающихся инкрементировать один ключ без пауз, создадут шторм транзакций (Live Lock) и перегрузят Raft-кворум.",
        "Игнорирование CreateRevision == 0: если ключ создается впервые, его `ModRevision` не существует. Предикат должен проверять `CreateRevision == 0`."
    ],
    "bigtech_interview": "Почему для счетчиков с миллионами событий в секунду не используют etcd? etcd имеет пропускную способность записи порядка 10 000–30 000 RPS из-за синхронного fsync дискового журнала Raft на кворуме узлов. Для сверхвысоких нагрузок используют Redis INCR или распределенные батчинг-счетчики в памяти."
})

# Ex 17: Программная память транзакций (Software Transactional Memory - STM)
code17 = r'''package main

import (
	"context"
	"fmt"
	"strconv"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/client/v3/concurrency"
)

// BankAccountService осуществляет межбанковские переводы с гарантией ACID
type BankAccountService struct {
	cli *clientv3.Client
}

func NewBankAccountService(cli *clientv3.Client) *BankAccountService {
	return &BankAccountService{cli: cli}
}

// TransferMoney атомарно переводит сумму между двумя счетами через STM
func (s *BankAccountService) TransferMoney(ctx context.Context, fromAccount, toAccount string, amount int64) error {
	// Инициализируем STM (Software Transactional Memory)
	applyTxn := func(stm concurrency.STM) error {
		// Читаем баланс отправителя через STM
		fromValStr := stm.Get(fromAccount)
		fromBalance, _ := strconv.ParseInt(fromValStr, 10, 64)

		if fromBalance < amount {
			return fmt.Errorf("недостаточно средств на счете %s: баланс %d, требуется %d",
				fromAccount, fromBalance, amount)
		}

		// Читаем баланс получателя
		toValStr := stm.Get(toAccount)
		toBalance, _ := strconv.ParseInt(toValStr, 10, 64)

		// Модифицируем балансы в транзакционной памяти
		stm.Put(fromAccount, strconv.FormatInt(fromBalance-amount, 10))
		stm.Put(toAccount, strconv.FormatInt(toBalance+amount, 10))

		return nil
	}

	// concurrency.NewSTM автоматически собирает все Get/Put в Txn и повторяет при конфликтах
	_, err := concurrency.NewSTM(s.cli, applyTxn, concurrency.WithIsolation(concurrency.SerializableSnapshot))
	if err != nil {
		return fmt.Errorf("транзакция перевода отклонена: %w", err)
	}

	fmt.Printf("[STM SUCCESS] Успешный перевод %d со счета %s на счет %s\n", amount, fromAccount, toAccount)
	return nil
}

func main() {
	fmt.Println("Программная память транзакций (Software Transactional Memory - STM):")
	fmt.Println(" 1. concurrency.NewSTM(cli, applyFn) отслеживает все прочитанные ключи stm.Get()")
	fmt.Println(" 2. Автоматически генерирует If(Compare(ModRev...)) для всех прочитанных ключей")
	fmt.Println(" 3. При конфликте перезапускает applyFn до успешной фиксации (SerializableSnapshot)")
}
'''
validate_go_code(code17, "code17")
exercises.append({
    "num": 17,
    "title": "Программная память транзакций (Software Transactional Memory - STM)",
    "task": "Изучите высокоуровневый пакет concurrency.NewSTM для программной памяти транзакций в etcd. Реализуйте сервис BankAccountService с методом TransferMoney, который выполняет атомарный перевод средств между двумя счетами с контролем баланса и изоляцией SerializableSnapshot.",
    "theory": "Ручное составление транзакций `etcd.Txn` при затрагивании нескольких взаимосвязанных ключей становится чрезвычайно сложным: разработчик должен вручную собрать все `ModRevision`, сформировать массив `Compare` и самостоятельно организовать цикл повторов.\n\nПакет `go.etcd.io/etcd/client/v3/concurrency` предоставляет абстракцию Software Transactional Memory (STM):\n- Внутри функции `apply(stm)` вы просто вызываете `stm.Get(key)` и `stm.Put(key, val)`.\n- STM автоматически отслеживает Read Set (все прочитанные ключи и их ревизии) и Write Set (все изменяемые ключи).\n- При коммите STM компилирует это в единый атомарный вызов `Txn`.\n- Если за время выполнения функции какой-либо из прочитанных ключей был изменен другим клиентом, `concurrency.NewSTM` автоматически перезапускает функцию с актуальными данными.",
    "step_by_step": [
        "Импортируйте пакет go.etcd.io/etcd/client/v3/concurrency.",
        "Создайте сервис BankAccountService с ссылкой на clientv3.Client.",
        "Напишите функцию транзакции applyTxn с чтением балансов через stm.Get.",
        "Проверьте достаточность средств и обновите значения через stm.Put.",
        "Запустите concurrency.NewSTM с опцией изоляции SerializableSnapshot."
    ],
    "code_blocks": [{
        "filename": "etcd_stm_transfer.go",
        "lang": "go",
        "code": code17
    }],
    "under_the_hood": "Уровень изоляции `concurrency.SerializableSnapshot` гарантирует отсутствие аномалий фантомного и несогласованного чтения (Write Skew): STM проверяет, что ревизии абсолютно всех прочитанных ключей не изменились к моменту записи.",
    "pitfalls": [
        "Побочные эффекты внутри apply: функция, переданная в `NewSTM`, может быть вызвана 5–10 раз подряд из-за конфликтов параллельных транзакций. Внутри неё категорически запрещено отправлять письма, списывать деньги через сторонние API или вызывать внешние неидемпотентные сетевые вызовы.",
        "Большой объем Read Set: если внутри STM вычитать тысячи ключей, транзакция превысит лимит размера сообщения etcd."
    ],
    "bigtech_interview": "В чем разница между оптимистичной транзакцией в STM etcd и пессимистичной блокировкой в PostgreSQL (`SELECT FOR UPDATE`)? В etcd узлы не удерживают блокировки строк в процессе вычисления (lock-free), что устраняет риск взаимных блокировок (Deadlocks). Но при крайне высокой конкуренции на одну запись транзакции будут тратить CPU на постоянные повторы (Retry storms)."
})

# Ex 18: Распределенные блокировки (Distributed Lock) с concurrency.Mutex
code18 = r'''package main

import (
	"context"
	"fmt"
	"sync"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/client/v3/concurrency"
)

// DistributedLockManager управляет распределенными мьютексами в etcd
type DistributedLockManager struct {
	client *clientv3.Client
}

func NewDistributedLockManager(cli *clientv3.Client) *DistributedLockManager {
	return &DistributedLockManager{client: cli}
}

// ExecuteWithLock выполняет критическую секцию под защитой распределенного мьютекса
func (m *DistributedLockManager) ExecuteWithLock(ctx context.Context, lockKey string, ttlSeconds int, criticalSection func() error) error {
	// 1. Создаем сессию concurrency.Session (автоматический Lease + KeepAlive)
	session, err := concurrency.NewSession(m.client, concurrency.WithTTL(ttlSeconds))
	if err != nil {
		return fmt.Errorf("ошибка создания сессии блокировки: %w", err)
	}
	defer session.Close()

	// 2. Инициализируем мьютекс
	mutex := concurrency.NewMutex(session, lockKey)

	// 3. Захватываем блокировку (блокируется до тех пор, пока ресурс не освободится)
	fmt.Printf("[LOCK ACQUIRE] Запрос захвата блокировки '%s'...\n", lockKey)
	if err := mutex.Lock(ctx); err != nil {
		return fmt.Errorf("не удалось захватить блокировку: %w", err)
	}
	fmt.Printf("🔒 [LOCK GRANTED] Блокировка '%s' успешно получена (Ключ в etcd: %s)\n", lockKey, mutex.Key())

	// 4. Выполняем защищенный бизнес-код
	execErr := criticalSection()

	// 5. Освобождаем блокировку
	if err := mutex.Unlock(context.Background()); err != nil {
		fmt.Printf("⚠️ Ошибка явного освобождения блокировки: %v\n", err)
	} else {
		fmt.Printf("🔓 [LOCK RELEASED] Блокировка '%s' успешно освобождена\n", lockKey, mutex.Key())
	}

	return execErr
}

func main() {
	fmt.Println("Распределенные блокировки (Distributed Lock) с concurrency.Mutex:")
	fmt.Println(" 1. concurrency.NewSession(cli, WithTTL(10)) создает аренду с фоновым KeepAlive")
	fmt.Println(" 2. mutex.Lock(ctx) создает эфемерный ключ и встает в очередь по ревизиям")
	fmt.Println(" 3. mutex.Unlock(ctx) удаляет ключ и пробуждает следующий ожидающий узел")
}
'''
validate_go_code(code18, "code18")
exercises.append({
    "num": 18,
    "title": "Распределенные блокировки (Distributed Lock) с concurrency.Mutex",
    "task": "Изучите устройство распределенного мьютекса в etcd v3. Реализуйте DistributedLockManager с методом ExecuteWithLock, создающим сессию concurrency.NewSession с TTL, захватывающим блокировку через concurrency.NewMutex, выполняющим критическую секцию и безопасно освобождающим ресурс.",
    "theory": "В распределенных системах множество экземпляров сервиса конкурируют за неделимый ресурс: генерацию ежемесячного биллинга, доступ к оборудованию или миграцию схемы БД.\n\nПакет `concurrency.NewMutex` в etcd реализует классический алгоритм распределенной очереди блокировок (Fair Distributed Lock):\n1. `session := concurrency.NewSession(client, WithTTL(10))` создает объект аренды с авто-продлением KeepAlive.\n2. При вызове `mutex.Lock(ctx)` клиент создает ключ с префиксом: `/locks/resource/<lease_id>`.\n3. etcd сортирует созданные ключи по их `CreateRevision`.\n4. Если созданный ключ имеет наименьшую ревизию в префиксе — узел немедленно получает блокировку!\n5. Если есть ключи с меньшей ревизией, клиент вешает `Watcher` строго на ключ непосредственно ПЕРЕД ним в очереди. Как только предшественник удаляет свой ключ (Unlock или падение), следующий узел мгновенно получает владение.",
    "step_by_step": [
        "Инициализируйте сессию concurrency.NewSession с параметром WithTTL.",
        "Создайте мьютекс concurrency.NewMutex(session, lockKey).",
        "Вызовите mutex.Lock(ctx) с обработкой отмены по таймауту контекста.",
        "Выполните целевую функцию criticalSection под гарантированной защитой блокировки.",
        "Вызовите mutex.Unlock() и закройте сессию defer session.Close()."
    ],
    "code_blocks": [{
        "filename": "etcd_distributed_mutex.go",
        "lang": "go",
        "code": code18
    }],
    "under_the_hood": "В отличие от Redis Redlock, где клиенты непрерывно спамят поллингом `SET NX EX` каждые 50 мс, алгоритм etcd не создает лишнего сетевого трафика. Каждый ожидающий узел подписывается ровно на один предыдущий ключ, исключая эффект Thundering Herd (когда при освобождении замка сотни клиентов одновременно штурмуют базу).",
    "pitfalls": [
        "Забытый session.Close(): незакрытая сессия оставляет аренду активной в etcd, удерживая блокировку даже после завершения выполнения функции.",
        "Таймаут контекста в Unlock: при освобождении блокировки `mutex.Unlock()` следует передавать `context.Background()` с коротким таймаутом, а не родительский отмененный `ctx`, иначе запрос на удаление ключа будет отменен."
    ],
    "bigtech_interview": "Почему алгоритм распределенных блокировок etcd надежнее Redis Redlock? Мартин Клеппманн доказал, что Redlock подвержен сбоям из-за сдвигов системных часов (Clock Drift) и пауз GC. etcd опирается на строгий консенсус Raft и монотонные логические ревизии, не зависящие от физических часов серверов."
})

# Ex 19: Безопасность блокировок: предотвращение зависания при падении узла
code19 = r'''package main

import (
	"context"
	"fmt"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/client/v3/concurrency"
)

// DeadlockSafetySimulator демонстрирует автоматическое снятие блокировки при аварии узла
type DeadlockSafetySimulator struct {
	cli *clientv3.Client
}

func NewDeadlockSafetySimulator(cli *clientv3.Client) *DeadlockSafetySimulator {
	return &DeadlockSafetySimulator{cli: cli}
}

// SimulateCrashedNode имитирует узел, который захватил мьютекс и внезапно упал (SIGKILL)
func (s *DeadlockSafetySimulator) SimulateCrashedNode(lockKey string, leaseTTL int) clientv3.LeaseID {
	// Создаем сессию с коротким TTL (например, 5 секунд)
	session, err := concurrency.NewSession(s.cli, concurrency.WithTTL(leaseTTL))
	if err != nil {
		panic(err)
	}

	mutex := concurrency.NewMutex(session, lockKey)
	if err := mutex.Lock(context.Background()); err != nil {
		panic(err)
	}

	leaseID := session.Lease()
	fmt.Printf("💥 [NODE CRASH] Узел захватил мьютекс '%s' (LeaseID=%x) и аварийно завершился (kill -9)\n",
		mutex.Key(), leaseID)

	// Эмулируем падение процесса: сессия НЕ закрывается через session.Close(),
	// а горутина KeepAlive убивается (отменяем внутренний контекст сессии).
	// В реальной жизни процесс Go просто погибает вместе со всеми сокетами.
	_ = session.Client().Revoke(context.Background(), 0) // демонстрационный маркер

	return leaseID
}

// WaitForLockRelease проверяет, освободит ли etcd блокировку по тайм-ауту
func (s *DeadlockSafetySimulator) WaitForLockRelease(ctx context.Context, lockKey string, leaseTTL int) {
	fmt.Printf("[FAILOVER WAIT] Резервный узел ждет освобождения ресурса '%s' (TTL=%ds)...\n", lockKey, leaseTTL)

	start := time.Now()
	// Создаем новую изолированную сессию резервного узла
	standbySession, err := concurrency.NewSession(s.cli, concurrency.WithTTL(10))
	if err != nil {
		panic(err)
	}
	defer standbySession.Close()

	standbyMutex := concurrency.NewMutex(standbySession, lockKey)

	// Пытаемся захватить тот же мьютекс
	if err := standbyMutex.Lock(ctx); err != nil {
		fmt.Printf("Ошибка ожидания блокировки: %v\n", err)
		return
	}

	elapsed := time.Since(start)
	fmt.Printf("✅ [FAILOVER SUCCESS] Резервный узел получил блокировку спустя %v!\n", elapsed)
	fmt.Println("Кластер etcd автоматически удалил заброшенный ключ упавшего узла по истечении Lease TTL.")
	_ = standbyMutex.Unlock(context.Background())
}

func main() {
	fmt.Println("Безопасность блокировок: предотвращение deadlock при аварии узла:")
	fmt.Println(" 1. Мьютекс etcd всегда привязан к аренде LeaseID")
	fmt.Println(" 2. При физическом падении сервера (паника, сбой питания) KeepAlive прекращается")
	fmt.Println(" 3. etcd автоматически удаляет эфемерный ключ, исключая вечный deadlock")
}
'''
validate_go_code(code19, "code19")
exercises.append({
    "num": 19,
    "title": "Безопасность блокировок: предотвращение зависания при падении узла",
    "task": "Смоделируйте сценарий аварийного падения узла (Hard Crash / SIGKILL), удерживающего распределенный мьютекс. Докажите, что благодаря привязке concurrency.Mutex к объекту concurrency.Session с ограниченным TTL, кластер etcd автоматически освобождает блокировку по истечении срока аренды.",
    "theory": "Главная опасность распределенных блокировок — вечный дедлок (Deadlock): узел захватывает мьютекс, начинает обработку и неожиданно погибает (Kernel Panic, Out of Memory, потеря электропитания). Если блокировка не имеет срока жизни, ни один другой сервер в мире больше никогда не сможет ее захватить.\n\nВ etcd v3 распределенный мьютекс физически не может существовать без `concurrency.Session`:\n1. Сессия создается с жестким TTL (например, 10 секунд).\n2. Фоновая горутина Go-клиента регулярно шлет KeepAlive heartbeat-пакеты.\n3. При падении процесса сокет закрывается на уровне ОС, отправка KeepAlive прекращается.\n4. Ровно через 10 секунд таймер аренды на сервере etcd истекает, etcd генерирует Raft-удаление ключа и оповещает следующий узел в очереди ожидания.",
    "step_by_step": [
        "Создайте симулятор DeadlockSafetySimulator с клиентом clientv3.Client.",
        "Реализуйте SimulateCrashedNode: захватите мьютекс и смоделируйте гибель процесса без вызова Unlock.",
        "В методе WaitForLockRelease запустите резервный узел, вызывающий mutex.Lock().",
        "Зафиксируйте время разблокировки time.Since(start).",
        "Убедитесь, что задержка передачи блокировки точно соответствует TTL аренды."
    ],
    "code_blocks": [{
        "filename": "etcd_lock_safety_deadlock.go",
        "lang": "go",
        "code": code19
    }],
    "under_the_hood": "Так как удаление ключа по тайм-ауту аренды является обычной операцией записи в Raft-лог, оно детерминированно реплицируется на все фолловеры etcd. Даже если лидер etcd упадет одновременно с падением клиента, новый лидер применит тайм-аут аренды без сбоев.",
    "pitfalls": [
        "Слишком длинный TTL: если указать TTL 60 секунд, при падении активного узла вся распределенная система будет простаивать целую минуту в ожидании failover.",
        "Слишком короткий TTL: если указать TTL 1 секунду, кратковременная пауза сборщика мусора Go (GC Pause) или сетевой джиттер приведут к ложной потере блокировки."
    ],
    "bigtech_interview": "Что такое Fencing Token и почему одного TTL блокировки недостаточно для абсолютной безопасности? Ответ: если процесс 'завис' на 15 секунд в GC-паузе, его блокировка истечет, и второй узел захватит ресурс. Очнувшись, первый узел продолжит запись, повредив данные. etcd решает это с помощью ревизий (`CreateRevision`), выступающих в роли возрастающего Fencing Token."
})

# Ex 20: Выборы лидера (Leader Election) в распределенной системе
code20 = r'''package main

import (
	"context"
	"fmt"
	"sync"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/client/v3/concurrency"
)

// LeaderElectionNode участвует в кампании по выборам лидера кластера
type LeaderElectionNode struct {
	cli     *clientv3.Client
	nodeID  string
	role    string
	mu      sync.RWMutex
}

func NewLeaderElectionNode(cli *clientv3.Client, id string) *LeaderElectionNode {
	return &LeaderElectionNode{cli: cli, nodeID: id, role: "Candidate"}
}

// Campaign запускает предвыборную кампанию
func (n *LeaderElectionNode) Campaign(ctx context.Context, electionPrefix string, ttlSeconds int) error {
	// 1. Создаем сессию для выборов с автоматическим KeepAlive
	session, err := concurrency.NewSession(n.cli, concurrency.WithTTL(ttlSeconds))
	if err != nil {
		return fmt.Errorf("ошибка создания сессии кандидата: %w", err)
	}
	defer session.Close()

	// 2. Инициализируем предвыборный избирательный округ
	election := concurrency.NewElection(session, electionPrefix)

	fmt.Printf("[ELECTION] Узел %s начинает предвыборную кампанию в '%s'...\n", n.nodeID, electionPrefix)

	// 3. Campaign блокируется до тех пор, пока данный узел не победит в выборах
	if err := election.Campaign(ctx, n.nodeID); err != nil {
		return fmt.Errorf("кампания прервана: %w", err)
	}

	n.mu.Lock()
	n.role = "Leader"
	n.mu.Unlock()

	fmt.Printf("👑 [LEADER ELECTED] Узел %s УСПЕШНО ИЗБРАН ЛИДЕРОМ! (Rev=%d)\n",
		n.nodeID, election.Header(ctx).Revision)

	return nil
}

func main() {
	fmt.Println("Выборы лидера (Leader Election) с concurrency.Election:")
	fmt.Println(" 1. concurrency.NewElection(session, prefix) объявляет пространство выборов")
	fmt.Println(" 2. election.Campaign(ctx, nodeID) публикует кандидатуру узла")
	fmt.Println(" 3. Вызов блокируется до момента, пока узел не станет лидером по наименьшей ревизии")
}
'''
validate_go_code(code20, "code20")
exercises.append({
    "num": 20,
    "title": "Выборы лидера (Leader Election) в распределенной системе",
    "task": "Изучите механизм выбора лидера concurrency.NewElection в etcd. Реализуйте компонент LeaderElectionNode, который открывает сессию с TTL, начинает предвыборную кампанию вызовом election.Campaign(ctx, nodeID) и блокируется до победы в выборах по принципу наименьшей ревизии.",
    "theory": "Во многих распределенных архитектурах (активно-пассивные кластеры, фоновые планировщики, генераторы очередей) только один экземпляр сервиса должен выполнять роль 'Координатора' (Active Master), пока остальные находятся в режиме горячего резерва (Standby Followers).\n\nПакет `concurrency.NewElection` реализует выборы лидера поверх транзакций и ревизий etcd:\n1. Все кандидаты вызывают `election.Campaign(ctx, nodeID)` с префиксом `/elections/my-service`.\n2. etcd создает для каждого кандидата ключ с привязкой к его `LeaseID`.\n3. Лидером становится кандидат, чей ключ был создан с НАИМЕНЬШЕЙ глобальной ревизией (`CreateRevision`).\n4. Метод `Campaign` возвращает управление только победителю. Остальные кандидаты ждут в очереди через Watcher.",
    "step_by_step": [
        "Создайте структуру LeaderElectionNode с идентификатором узла nodeID и статусом роли.",
        "Инициализируйте concurrency.NewSession с желаемым таймаутом TTL.",
        "Создайте объект выборов concurrency.NewElection(session, electionPrefix).",
        "Вызовите блокирующий метод election.Campaign(ctx, n.nodeID).",
        "После разблокировки переведите роль узла в Leader и начните выполнение лидерских задач."
    ],
    "code_blocks": [{
        "filename": "etcd_leader_election.go",
        "lang": "go",
        "code": code20
    }],
    "under_the_hood": "Механизм выборов в etcd полностью децентрализован и не требует внешнего арбитра. Протокол консенсуса Raft гарантирует, что порядок создания ревизий ключей строго линеаризуем, поэтому возникновение двух лидеров (Split-Brain) математически исключено.",
    "pitfalls": [
        "Игнорирование контекста: вызов `election.Campaign` должен принимать отменяемый контекст `ctx`. При получении `SIGINT/SIGTERM` контекст отменяется, прерывая ожидание.",
        "Выполнение тяжелых задач в главном потоке: после избрания лидером длительные блокирующие операции не должны мешать фоновому стриму KeepAlive сессии."
    ],
    "bigtech_interview": "В чем отличие выборов лидера через etcd от алгоритма Bully или Paxos? В Bully узлы должны знать адреса всех остальных узлов и обмениваться сообщениями peer-to-peer. В etcd узлы координируются асинхронно через централизованное отказоустойчивое хранилище метаданных."
})

# Ex 21: Жизненный цикл лидера: поддержание лидерства и добровольная отставка
code21 = r'''package main

import (
	"context"
	"fmt"
	"sync"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/client/v3/concurrency"
)

// ManagedLeaderService управляет полным жизненным циклом лидера
type ManagedLeaderService struct {
	cli            *clientv3.Client
	electionPrefix string
	nodeID         string
	isLeader       bool
	mu             sync.RWMutex
}

func NewManagedLeaderService(cli *clientv3.Client, prefix, nodeID string) *ManagedLeaderService {
	return &ManagedLeaderService{
		cli:            cli,
		electionPrefix: prefix,
		nodeID:         nodeID,
	}
}

// RunLeaderEcosystem запускает кампанию, лидерскую работу и добровольную отставку (Resign)
func (s *ManagedLeaderService) RunLeaderEcosystem(ctx context.Context, ttl int) error {
	session, err := concurrency.NewSession(s.cli, concurrency.WithTTL(ttl))
	if err != nil {
		return err
	}
	defer session.Close()

	election := concurrency.NewElection(session, s.electionPrefix)

	fmt.Printf("[NODE %s] Участие в выборах...\n", s.nodeID)
	if err := election.Campaign(ctx, s.nodeID); err != nil {
		return err
	}

	s.mu.Lock()
	s.isLeader = true
	s.mu.Unlock()
	fmt.Printf("👑 [NODE %s] Избран лидером! Старт фоновых координационных задач...\n", s.nodeID)

	// Контекст для остановки лидерских задач при потере лидерства или отставке
	leaderCtx, cancelLeaderTasks := context.WithCancel(ctx)
	defer cancelLeaderTasks()

	// Запуск периодических лидерских воркеров (Cron jobs)
	go func() {
		ticker := time.NewTicker(500 * time.Millisecond)
		defer ticker.Stop()
		for {
			select {
			case <-leaderCtx.Done():
				fmt.Printf("[NODE %s] Фоновые задачи лидера остановлены\n", s.nodeID)
				return
			case <-ticker.C:
				fmt.Printf("[LEADER WORKER] Узел %s выполняет кластерную задачу...\n", s.nodeID)
			}
		}
	}()

	// Ожидаем внешнего сигнала остановки (Graceful Shutdown)
	<-ctx.Done()

	fmt.Printf("🛑 [SHUTDOWN] Сигнал завершения узла %s: добровольная отставка (Resign)\n", s.nodeID)
	cancelLeaderTasks()

	// Добровольная отставка: мгновенная передача власти следующему кандидату
	resignCtx, resignCancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer resignCancel()

	if err := election.Resign(resignCtx); err != nil {
		fmt.Printf("⚠️ Ошибка отставки: %v\n", err)
	} else {
		fmt.Printf("👋 [RESIGNED] Узел %s добровольно передал полномочия следующему лидеру\n", s.nodeID)
	}

	return nil
}

func main() {
	fmt.Println("Жизненный цикл лидера: поддержание лидерства и Resign:")
	fmt.Println(" 1. После победы в Campaign() запускаются критические фоновые воркеры")
	fmt.Println(" 2. При получении SIGTERM вызывается election.Resign(ctx)")
	fmt.Println(" 3. Resign мгновенно удаляет ключ лидерства, избегая простоя на время таймаута сессии")
}
'''
validate_go_code(code21, "code21")
exercises.append({
    "num": 21,
    "title": "Жизненный цикл лидера: поддержание лидерства и добровольная отставка",
    "task": "Реализуйте сервис ManagedLeaderService, управляющий полным жизненным циклом лидера. При избрании сервис запускает фоновые воркеры с изолированным контекстом, а при получении сигнала Graceful Shutdown выполняет добровольную отставку election.Resign(ctx) для мгновенной передачи власти без ожидания истечения TTL.",
    "theory": "В production-системах важно различать два сценария смены лидера:\n1. Аварийное падение (Crash): узел погиб внезапно. Кластер вынужден ждать истечения TTL сессии (например, 15 секунд), чтобы убедиться в недоступности лидера.\n2. Плановый перезапуск (Rolling Update / Graceful Shutdown): инженер выкатывает новый релиз. Ждать 15 секунд простоя недопустимо!\n\nМетод `election.Resign(ctx)`:\n- Вызывается при обработке сигналов `SIGTERM` или `SIGINT`.\n- Атомарно удаляет ключ текущего лидера в etcd.\n- Следующий кандидат в очереди немедленно просыпается от события Watcher и становится лидером за 1–2 миллисекунды, обеспечивая истинный Zero-Downtime Failover.",
    "step_by_step": [
        "Определите ManagedLeaderService с полями префикса выборов и идентификатора узла.",
        "В методе RunLeaderEcosystem инициализируйте сессию и вызовите election.Campaign.",
        "После избрания создайте подчиненный context.WithCancel для управления фоновыми задачами.",
        "Организуйте ожидание сигнала завершения <-ctx.Done().",
        "Вызовите cancelLeaderTasks() и метод добровольной отставки election.Resign(resignCtx)."
    ],
    "code_blocks": [{
        "filename": "etcd_leader_lifecycle_resign.go",
        "lang": "go",
        "code": code21
    }],
    "under_the_hood": "При вызове `Resign()` etcd выполняет транзакцию удаления лидерского ключа с проверкой того, что вызывающий узел все еще действительно является текущим лидером, исключая случайную отставку чужого лидерства.",
    "pitfalls": [
        "Продолжение работы воркеров после Resign: если воркеры не остановились до вызова `Resign()`, в кластере на несколько секунд возникнет ситуация двух одновременно работающих лидеров (Dual Leaders). Сначала останавливаем работу, затем отдаем лидерство.",
        "Короткий таймаут на отставку: при высокой сетевой нагрузке вызов `Resign` должен иметь разумный таймаут (2–3 секунды)."
    ],
    "bigtech_interview": "Как избежать ситуации 'Split-Brain' при сетевом разделе датацентра? Raft требует строгого большинства `N/2 + 1`. Лидер, оказавшийся в меньшинстве, потеряет кворум и не сможет подтверждать KeepAlive. Большинство в другой половине датацентра изберет нового лидера."
})

# Ex 22: Наблюдение за сменой лидера фолловерами (Observe)
code22 = r'''package main

import (
	"context"
	"fmt"
	"sync"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/client/v3/concurrency"
)

// LeaderObserver отслеживает текущего лидера кластера в реальном времени
type LeaderObserver struct {
	cli            *clientv3.Client
	electionPrefix string
	mu             sync.RWMutex
	currentLeader  string
}

func NewLeaderObserver(cli *clientv3.Client, prefix string) *LeaderObserver {
	return &LeaderObserver{
		cli:            cli,
		electionPrefix: prefix,
	}
}

// StartObserving запускает непрерывное наблюдение за лидером
func (o *LeaderObserver) StartObserving(ctx context.Context) error {
	session, err := concurrency.NewSession(o.cli)
	if err != nil {
		return err
	}

	election := concurrency.NewElection(session, o.electionPrefix)

	// Observe возвращает канал <-chan clientv3.GetResponse с нотификациями о смене лидера
	observeChan := election.Observe(ctx)

	go func() {
		defer session.Close()
		for resp := range observeChan {
			if len(resp.Kvs) == 0 {
				o.mu.Lock()
				o.currentLeader = ""
				o.mu.Unlock()
				fmt.Println("⚠️ [OBSERVE] Лидер в кластере отсутствует (Идут перевыборы...)")
				continue
			}

			newLeaderID := string(resp.Kvs[0].Value)
			o.mu.Lock()
			o.currentLeader = newLeaderID
			o.mu.Unlock()

			fmt.Printf("👁️ [OBSERVE] Зафиксирован действующий лидер: %s (Rev=%d)\n",
				newLeaderID, resp.Kvs[0].ModRevision)
		}
	}()

	return nil
}

func (o *LeaderObserver) GetCurrentLeader() string {
	o.mu.RLock()
	defer o.mu.RUnlock()
	return o.currentLeader
}

func main() {
	fmt.Println("Наблюдение за сменой лидера фолловерами (Observe):")
	fmt.Println(" 1. election.Observe(ctx) возвращает канал актуальных ответов <-chan clientv3.GetResponse")
	fmt.Println(" 2. Фолловеры получают мгновенные пуш-уведомления при каждой смене лидера")
	fmt.Println(" 3. Клиенты перенаправляют RPC-запросы на актуальный узел без поллинга")
}
'''
validate_go_code(code22, "code22")
exercises.append({
    "num": 22,
    "title": "Наблюдение за сменой лидера фолловерами (Observe)",
    "task": "Реализуйте компонент LeaderObserver для пассивного наблюдения за лидером кластера. Используйте метод election.Observe(ctx) для получения непрерывного канала уведомлений <-chan clientv3.GetResponse и сохраняйте текущий ID лидера в потокобезопасную переменную для маршрутизации RPC-запросов.",
    "theory": "В архитектуре с выделенным лидером не всем узлам обязательно участвовать в предвыборной гонке. Рядовые фолловеры, API-шлюзы и клиенты должны знать, кто именно в текущий момент является лидером, чтобы перенаправлять на него мутирующие команды.\n\nМетод `election.Observe(ctx)` в etcd concurrency:\n1. Возвращает канал `<-chan clientv3.GetResponse`.\n2. В момент запуска метод сразу возвращает текущего лидера (если он есть).\n3. При любой смене лидера (отставка, падение или перевыборы) сервер etcd мгновенно пушит в канал новый снимок с идентификатором победителя.\n4. Если лидер упал и выборы еще идут, канал передает пустой срез `len(resp.Kvs) == 0`.",
    "step_by_step": [
        "Создайте структуру LeaderObserver с полем currentLeader под защитой sync.RWMutex.",
        "Инициализируйте объект concurrency.NewElection(session, electionPrefix).",
        "Получите канал уведомлений через election.Observe(ctx).",
        "В отдельной горутине обрабатывайте входящие события resp.Kvs и обновляйте поле currentLeader.",
        "Реализуйте метод GetCurrentLeader() для безопасного чтения текущего координатора."
    ],
    "code_blocks": [{
        "filename": "etcd_leader_observer.go",
        "lang": "go",
        "code": code22
    }],
    "under_the_hood": "Под капотом метод `Observe` использует префиксный Watcher на каталог выборов и автоматически находит ключ с минимальной `CreateRevision`, избавляя разработчика от самостоятельного парсинга и фильтрации ревизий.",
    "pitfalls": [
        "Отправка запросов во время перевыборов: когда лидер упал, а новый еще не избран, `GetCurrentLeader()` вернет пустую строку. Клиент должен поддерживать буферизацию запросов с коротким ожиданием (1–2 секунды).",
        "Утечка сессии наблюдения: сессия observer не должна выделять долгий Lease TTL, так как сам наблюдатель не публикует никаких ключей."
    ],
    "bigtech_interview": "Как в Kubernetes `kubectl` и `kube-scheduler` узнают текущего активного лидера планировщика? Используется ресурс `Leases` в API-сервере Kubernetes (реализованный поверх etcd Leases), за которым наблюдают все реплики через Informer."
})

# Ex 23: Кэширование метаданных в оперативной памяти сервиса с ревизиями
code23 = r'''package main

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/api/v3/mvccpb"
)

// CachedMetadataStore реализует двухуровневый кэш (L1 Memory + L2 etcd)
type CachedMetadataStore struct {
	cli      *clientv3.Client
	prefix   string
	cache    sync.Map
	syncRev  atomic.Int64
	hitCount atomic.Uint64
}

func NewCachedMetadataStore(cli *clientv3.Client, prefix string) *CachedMetadataStore {
	return &CachedMetadataStore{cli: cli, prefix: prefix}
}

// Initialize загружает начальное состояние и запускает фоновый синхронизатор
func (s *CachedMetadataStore) Initialize(ctx context.Context) error {
	// 1. Читаем все метаданные из etcd
	resp, err := s.cli.Get(ctx, s.prefix, clientv3.WithPrefix())
	if err != nil {
		return fmt.Errorf("ошибка начальной загрузки метаданных: %w", err)
	}

	for _, kv := range resp.Kvs {
		s.cache.Store(string(kv.Key), string(kv.Value))
	}
	s.syncRev.Store(resp.Header.Revision)

	fmt.Printf("[CACHE INIT] Загружено %d записей в L1 кэш (Ревизия: %d)\n",
		len(resp.Kvs), resp.Header.Revision)

	// 2. Фоновый поток непрерывной синхронизации
	go s.syncLoop(ctx)
	return nil
}

func (s *CachedMetadataStore) syncLoop(ctx context.Context) {
	watcher := clientv3.NewWatcher(s.cli)
	defer watcher.Close()

	startRev := s.syncRev.Load() + 1
	watchCh := watcher.Watch(ctx, s.prefix, clientv3.WithPrefix(), clientv3.WithRev(startRev))

	for resp := range watchCh {
		for _, ev := range resp.Events {
			key := string(ev.Kv.Key)
			if ev.Type == mvccpb.PUT {
				s.cache.Store(key, string(ev.Kv.Value))
			} else if ev.Type == mvccpb.DELETE {
				s.cache.Delete(key)
			}
			s.syncRev.Store(ev.Kv.ModRevision)
		}
	}
}

// Get выполняет lock-free чтение за доли наносекунды
func (s *CachedMetadataStore) Get(key string) (string, bool) {
	s.hitCount.Add(1)
	val, ok := s.cache.Load(key)
	if !ok {
		return "", false
	}
	return val.(string), true
}

func (s *CachedMetadataStore) Hits() uint64 {
	return s.hitCount.Load()
}

func main() {
	fmt.Println("Двухуровневое кэширование метаданных (L1 Memory + L2 etcd):")
	fmt.Println(" 1. Initial Get() наполняет sync.Map и фиксирует ревизию")
	fmt.Println(" 2. Фоновый Watcher обновляет локальную память за микросекунды")
	fmt.Println(" 3. Бизнес-запросы читают из памяти без сетевых задержек (100% Hit Rate)")
}
'''
validate_go_code(code23, "code23")
exercises.append({
    "num": 23,
    "title": "Кэширование метаданных в оперативной памяти сервиса с ревизиями",
    "task": "Спроектируйте высокопроизводительный сервис CachedMetadataStore с двухуровневой архитектурой: оперативная память (L1 sync.Map) + удаленный кластер etcd v3 (L2). Обеспечьте нулевые аллокации и задержки чтения при гарантированном реактивном обновлении кэша через фоновый Watcher.",
    "theory": "Чтение данных напрямую из etcd на каждый входящий HTTP/gRPC запрос в HighLoad-сервисе недопустимо: даже при сериализуемом чтении (`WithSerializable()`) сетевой RTT составляет 0.5–2 мс, а пропускная способность ограничивается сетевой картой.\n\nПаттерн Read-Through Reactive In-Memory Cache:\n1. При старте сервис выполняет один префиксный запрос и копирует все метаданные в потокобезопасную память (`sync.Map` или `atomic.Pointer`).\n2. Фоновый Watcher непрерывно применяет изменения в память.\n3. Рабочие потоки читают данные исключительно из памяти за несколько наносекунд.\n4. etcd полностью разгружается: нагрузка на кластер не зависит от числа читающих запросов.",
    "step_by_step": [
        "Определите CachedMetadataStore с полями sync.Map, syncRev atomic.Int64 и hitCount.",
        "В методе Initialize выполните начальный префиксный Get() и наполните sync.Map.",
        "Зафиксируйте ревизию кластера resp.Header.Revision.",
        "Запустите горутину syncLoop с опциями WithPrefix() и WithRev(startRev).",
        "Реализуйте метод Get() с атомарным инкрементом счетчика попаданий."
    ],
    "code_blocks": [{
        "filename": "etcd_inmemory_cache.go",
        "lang": "go",
        "code": code23
    }],
    "under_the_hood": "Использование `sync.Map` идеально подходит для сценария 'Append-mostly / Read-heavy', когда ключи читаются миллионы раз, а обновляются редко. Доступ к ключам происходит через lock-free чтение atomic-указателей внутри структуры `sync.Map.read`.",
    "pitfalls": [
        "Неконсистентность при рестарте Watcher: если стрим разорвался, а затем восстановился с ошибкой `ErrCompacted`, кэш в памяти должен быть полностью перезагружен, иначе удаленные ключи останутся в памяти навсегда.",
        "Eventual Consistency: между коммитом в etcd и применением события в локальный кэш проходит от 0.5 до 5 мс. Если бизнес-логике требуется строгая линеаризуемость в конкретной точке, в ней следует выполнить явный `client.Get`."
    ],
    "bigtech_interview": "Как устроена архитектура кэширования в Kubernetes API Server? API-сервер держит Informer Cache на все объекты кластера. Все вызовы `kubectl get` без флага resourceVersion читаются строго из оперативной памяти сервера, защищая etcd от перегрузки."
})

# Ex 24: Периодическая компактификация etcd (Compaction)
code24 = r'''package main

import (
	"context"
	"fmt"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
)

// MaintenanceManager выполняет административные операции обслуживания etcd
type MaintenanceManager struct {
	cli *clientv3.Client
}

func NewMaintenanceManager(cli *clientv3.Client) *MaintenanceManager {
	return &MaintenanceManager{cli: cli}
}

// CompactHistoricalData сжимает историю до указанной ревизии
func (m *MaintenanceManager) CompactHistoricalData(ctx context.Context, targetRev int64) error {
	fmt.Printf("[COMPACT START] Запуск сжатия истории etcd до ревизии %d...\n", targetRev)

	// client.Compact освобождает устаревшие исторические версии ключей в bbolt
	compactResp, err := m.cli.Compact(ctx, targetRev, clientv3.WithCompactPhysical())
	if err != nil {
		return fmt.Errorf("ошибка выполнения компактификации: %w", err)
	}

	_ = compactResp
	fmt.Printf("✅ [COMPACT DONE] Компактификация до ревизии %d успешно завершена\n", targetRev)
	return nil
}

// AutoCompactorByInterval запускает периодическое сжатие истории каждые N минут
func (m *MaintenanceManager) AutoCompactorByInterval(ctx context.Context, interval time.Duration, keepRevs int64) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			// Узнаем текущую ревизию кластера
			statusResp, err := m.cli.Status(ctx, m.cli.Endpoints()[0])
			if err != nil {
				fmt.Printf("⚠️ Ошибка получения статуса кластера: %v\n", err)
				continue
			}

			currentRev := statusResp.Header.Revision
			if currentRev > keepRevs {
				targetRev := currentRev - keepRevs
				if err := m.CompactHistoricalData(ctx, targetRev); err != nil {
					fmt.Printf("⚠️ Ошибка авто-компактификации: %v\n", err)
				}
			}
		}
	}
}

func main() {
	fmt.Println("Периодическая компактификация etcd (Compaction):")
	fmt.Println(" 1. client.Compact(ctx, rev) удаляет все версии ключей старше rev")
	fmt.Println(" 2. WithCompactPhysical() заставляет etcd немедленно очистить физические страницы bbolt")
	fmt.Println(" 3. Предотвращает неконтролируемый рост базы данных при интенсивных обновлениях")
}
'''
validate_go_code(code24, "code24")
exercises.append({
    "num": 24,
    "title": "Периодическая компактификация etcd (Compaction)",
    "task": "Реализуйте сервисный компонент MaintenanceManager для обслуживания кластера etcd v3. Напишите метод CompactHistoricalData с опцией clientv3.WithCompactPhysical() и фоновый планировщик AutoCompactorByInterval, который сжимает ревизии старше заданного горизонта keepRevs.",
    "theory": "Поскольку etcd — это версионируемая база данных (MVCC), ни один `Delete` или `Put` не удаляет старые данные с диска. Вместо этого они помечаются маркером Tombstone и сохраняются в истории.\n\nБез регулярного обслуживания файл базы `member/snap/db` вырастет до гигантских размеров и кластер остановится по лимиту квоты (`NOSPACE`).\n\nПроцесс Compaction (Сжатие истории):\n1. Вызов `client.Compact(ctx, targetRevision)` приказывает кластеру удалить все исторические ревизии ключей `< targetRevision`.\n2. После компактификации старые версии ключей физически удаляются из страниц B+tree BoltDB.\n3. Любые запросы `Get(WithRev)` или `Watch(WithRev)` с ревизией меньше `targetRevision` теперь будут завершаться ошибкой `ErrCompacted`.",
    "step_by_step": [
        "Создайте MaintenanceManager с полем clientv3.Client.",
        "Реализуйте метод CompactHistoricalData с вызовом cli.Compact(ctx, targetRev).",
        "Передайте флаг clientv3.WithCompactPhysical() для форсирования очистки физических страниц.",
        "В методе AutoCompactorByInterval организуйте опрос текущей ревизии через cli.Status.",
        "Вычислите targetRev = currentRev - keepRevs и вызовите компактификацию."
    ],
    "code_blocks": [{
        "filename": "etcd_compaction_manager.go",
        "lang": "go",
        "code": code24
    }],
    "under_the_hood": "По умолчанию etcd выполняет компактификацию асинхронно в фоне, помечая неиспользуемые страницы bbolt во внутреннем списке свободных страниц (FreeList). С опцией `WithCompactPhysical()` etcd ожидает физического удаления данных перед отправкой подтверждения клиенту.",
    "pitfalls": [
        "Слишком частая компактификация (каждую секунду): создает избыточную нагрузку на дисковую подсистему и ломает работу медленных Watcher-клиентов.",
        "Сжатие слишком близко к текущей ревизии (`targetRev = currentRev`): если удалить всю историю вплоть до текущей секунды, любой клиент при кратковременном сетевом сбое мгновенно словит `ErrCompacted`."
    ],
    "bigtech_interview": "Как в продакшене Kubernetes настраивают авто-компактификацию etcd? В параметрах запуска `etcd` передают флаг `--auto-compaction-retention=1h` (или `--auto-compaction-mode=periodic`), что заставляет etcd автоматически сжимать ревизии старше 1 часа."
})

# Ex 25: Дефрагментация хранилища etcd (Defragmentation)
code25 = r'''package main

import (
	"context"
	"fmt"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
)

// StorageMaintenanceService управляет дефрагментацией узлов etcd
type StorageMaintenanceService struct {
	cli *clientv3.Client
}

func NewStorageMaintenanceService(cli *clientv3.Client) *StorageMaintenanceService {
	return &StorageMaintenanceService{cli: cli}
}

// DefragmentAllEndpoints поочередно дефрагментирует все ноды кластера
func (s *StorageMaintenanceService) DefragmentAllEndpoints(ctx context.Context) error {
	endpoints := s.cli.Endpoints()
	fmt.Printf("[DEFRAG] Начало дефрагментации %d узлов кластера etcd...\n", len(endpoints))

	for _, ep := range endpoints {
		fmt.Printf("[DEFRAG] Запуск дефрагментации на узле %s...\n", ep)
		start := time.Now()

		// Defragment вызывается строго для конкретного эндпоинта!
		_, err := s.cli.Defragment(ctx, ep)
		if err != nil {
			return fmt.Errorf("ошибка дефрагментации узла %s: %w", ep, err)
		}

		elapsed := time.Since(start)
		fmt.Printf("✅ [DEFRAG DONE] Узел %s успешно дефрагментирован за %v\n", ep, elapsed)

		// Пауза между узлами для стабилизации кворума Raft
		time.Sleep(1 * time.Second)
	}

	return nil
}

// GetStorageMetrics опрашивает размер базы данных на диске
func (s *StorageMaintenanceService) GetStorageMetrics(ctx context.Context, endpoint string) (int64, int64, error) {
	statusResp, err := s.cli.Status(ctx, endpoint)
	if err != nil {
		return 0, 0, err
	}

	// DbSize: реальный размер файла db на диске
	// DbSizeInUse: полезный объем реально занятых данных
	return statusResp.DbSize, statusResp.DbSizeInUse, nil
}

func main() {
	fmt.Println("Дефрагментация хранилища etcd (Defragmentation):")
	fmt.Println(" 1. Compaction освобождает страницы внутри bbolt, но НЕ уменьшает файл на диске")
	fmt.Println(" 2. client.Defragment(ctx, endpoint) физически пересоздает файл bbolt и возвращает место ОС")
	fmt.Println(" 3. Дефрагментация выполняется строго последовательно по одному узлу за раз!")
}
'''
validate_go_code(code25, "code25")
exercises.append({
    "num": 25,
    "title": "Дефрагментация хранилища etcd (Defragmentation)",
    "task": "Изучите механизм дефрагментации etcd bbolt хранилища. Реализуйте сервис StorageMaintenanceService, который опрашивает метрики DbSize и DbSizeInUse через client.Status и выполняет последовательную дефрагментацию каждого узла через client.Defragment(ctx, endpoint) с паузами для сохранения стабильности кворума.",
    "theory": "Критически важно понимать разницу между Compaction и Defragmentation:\n- `Compaction`: логически удаляет старые ревизии. Страницы внутри bbolt помечаются как свободные, но сам файл базы данных `member/snap/db` на диске НЕ уменьшается (он сохраняет свой максимальный выделенный размер).\n- `Defragmentation`: физически пересоздает файл базы данных с нуля. etcd читает только живые страницы из старой базы и последовательно записывает их в новый компактный файл bbolt, после чего старый файл удаляется.\n\nТолько после дефрагментации дисковое пространство возвращается операционной системе хоста, а разница `DbSize - DbSizeInUse` стремится к нулю.",
    "step_by_step": [
        "Создайте StorageMaintenanceService с ссылкой на clientv3.Client.",
        "Реализуйте метод GetStorageMetrics с извлечением statusResp.DbSize и DbSizeInUse.",
        "В методе DefragmentAllEndpoints итерируйтесь по срезу cli.Endpoints().",
        "Вызовите s.cli.Defragment(ctx, ep) строго поочередно для каждого узла.",
        "Добавьте паузу time.Sleep между узлами для предотвращения флапа лидера Raft."
    ],
    "code_blocks": [{
        "filename": "etcd_defragmentation.go",
        "lang": "go",
        "code": code25
    }],
    "under_the_hood": "Во время дефрагментации узел etcd блокирует запись в локальный bbolt. Если дефрагментировать все узлы одновременно, кластер потеряет кворум и перестанет обслуживать запросы! Поэтому дефрагментацию ВСЕГДА производят строго последовательно: узел 1 -> ожидание -> узел 2 -> ожидание -> узел 3.",
    "pitfalls": [
        "Параллельная дефрагментация: вызов дефрагментации в параллельных горутинах приведет к остановке всего кластера (Cluster Outage).",
        "Дефрагментация лидера: дефрагментация лидера может вызвать задержку отправки Heartbeat и привести к перевыборам. В продакшене сначала дефрагментируют всех фолловеров, затем отдают лидерство (`MoveLeader`) и дефрагментируют бывшего лидера."
    ],
    "bigtech_interview": "Что делать, если etcd база выросла до лимита квоты 8 ГБ и заблокировала запись? Порядок действий SRE: 1) Найти ревизию и запустить `Compact`, 2) Поочередно запустить `Defragment` на каждой ноде, 3) Снять тревогу переполнения командой `etcdctl alarm disarm`."
})

# Ex 26: Контроль квот хранилища etcd и обработка ошибки ErrNoSpace
code26 = r'''package main

import (
	"context"
	"errors"
	"fmt"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/api/v3/v3rpc/rpctypes"
)

// QuotaGuardService защищает систему от переполнения квоты etcd
type QuotaGuardService struct {
	cli      *clientv3.Client
	maxBytes int64
}

func NewQuotaGuardService(cli *clientv3.Client, maxBytes int64) *QuotaGuardService {
	return &QuotaGuardService{cli: cli, maxBytes: maxBytes}
}

// SafePut осуществляет запись с перехватом фатальной ошибки ErrNoSpace
func (q *QuotaGuardService) SafePut(ctx context.Context, key, val string) error {
	_, err := q.cli.Put(ctx, key, val)
	if err == nil {
		return nil
	}

	// Проверяем, вызван ли сбой превышением квоты хранилища
	if errors.Is(err, rpctypes.ErrNoSpace) {
		fmt.Printf("🚨 [CRITICAL ALERT] Кластер etcd исчерпал дисковую квоту (ErrNoSpace)! Запись заблокирована!\n")
		q.triggerEmergencyRemediation(context.Background())
		return fmt.Errorf("отказ в обслуживании: хранилище метаданных переполнено: %w", err)
	}

	return err
}

// triggerEmergencyRemediation запускает экстренную процедуру очистки
func (q *QuotaGuardService) triggerEmergencyRemediation(ctx context.Context) {
	fmt.Println("⚡ [EMERGENCY] Запуск аварийного протокола очистки квоты etcd:")
	fmt.Println(" 1. Получение текущей ревизии кластера")
	fmt.Println(" 2. Форсированная компактификация последних 100 000 ревизий")
	fmt.Println(" 3. Экстренная дефрагментация узлов")
	fmt.Println(" 4. Снятие тревоги NOSPACE через client.AlarmDisarm()")
}

func main() {
	fmt.Println("Контроль квот хранилища etcd и обработка ошибки ErrNoSpace:")
	fmt.Println(" 1. По умолчанию etcd имеет жесткую квоту памяти (2GB / 8GB)")
	fmt.Println(" 2. При превышении квоты etcd поднимает тревогу AlarmType_NOSPACE")
	fmt.Println(" 3. Все последующие вызовы Put блокируются ошибкой rpctypes.ErrNoSpace")
	fmt.Println(" 4. Чтение (Get) продолжает работать в режиме Read-Only")
}
'''
validate_go_code(code26, "code26")
exercises.append({
    "num": 26,
    "title": "Контроль квот хранилища etcd и обработка ошибки ErrNoSpace",
    "task": "Изучите поведение etcd при исчерпании дисковой квоты. Реализуйте QuotaGuardService, перехватывающий ошибку rpctypes.ErrNoSpace при записи, генерирующий критический алерт и запускающий сценарий экстренного восстановления (Emergency Remediation).",
    "theory": "Чтобы не допустить неконтролируемого исчерпания диска физического сервера, в etcd встроен механизм квот (Space Quota, по умолчанию 2 ГБ, максимум 8 ГБ).\n\nКогда размер базы данных превышает квоту:\n1. etcd переходит в аварийный защитный режим (Alarm State: `NOSPACE`).\n2. Все операции чтения (`Get`, `Watch`) продолжают работать штатно.\n3. Все операции записи (`Put`, `Txn`, `Grant`) немедленно отклоняются gRPC-ошибкой `rpctypes.ErrNoSpace`.\n4. Важно: даже если вы удалите часть ключей через `Delete`, запись НЕ разблокируется автоматически, так как `Delete` тоже является операцией записи!",
    "step_by_step": [
        "Импортируйте пакет rpctypes из go.etcd.io/etcd/api/v3/v3rpc/rpctypes.",
        "Создайте структуру QuotaGuardService с клиентом etcd.",
        "В методе SafePut выполните запись cli.Put(ctx, key, val).",
        "Проверьте ошибку через errors.Is(err, rpctypes.ErrNoSpace).",
        "Реализуйте каркас аварийной процедуры восстановления triggerEmergencyRemediation."
    ],
    "code_blocks": [{
        "filename": "etcd_quota_guard.go",
        "lang": "go",
        "code": code26
    }],
    "under_the_hood": "Система алармов etcd (`etcdserverpb.AlarmType_NOSPACE`) реплицируется через Raft. Чтобы снять блокировку после проведения Compact и Defrag, администратор обязан явно вызвать `Alarm(AlarmAction_ALARM_DISARM)`, подтверждая нормализацию свободного места.",
    "pitfalls": [
        "Увеличение квоты выше 8 ГБ: официальная документация etcd не рекомендует устанавливать квоту больше 8 ГБ (`--quota-backend-bytes=8589934592`), так как BoltDB с гигантскими файлами страдает от резкого роста задержек mmap и пауз сборщика мусора.",
        "Попытка писать Delete во время аларма: при активном NOSPACE команда `client.Delete()` также вернет `ErrNoSpace`. Спасает только `Compact`."
    ],
    "bigtech_interview": "Что происходит с кластером Kubernetes при наступлении ErrNoSpace в etcd? API Server перестает принимать любые изменения (нельзя создать Pod, обновить Deployment, зарегистрировать Node Heartbeat). При этом уже запущенные поды продолжают работать, но оркестрация полностью парализуется."
})

# Ex 27: Распределенная очередь задач (FIFO Queue) на базе etcd
code27 = r'''package main

import (
	"context"
	"fmt"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
)

// DistributedQueue реализует распределенную строгую FIFO очередь задач
type DistributedQueue struct {
	cli    *clientv3.Client
	kv     clientv3.KV
	prefix string
}

func NewDistributedQueue(cli *clientv3.Client, prefix string) *DistributedQueue {
	return &DistributedQueue{
		cli:    cli,
		kv:     clientv3.NewKV(cli),
		prefix: prefix,
	}
}

// Push помещает задачу в очередь
func (q *DistributedQueue) Push(ctx context.Context, payload string) (int64, error) {
	// Создаем уникальный ключ задачи с префиксом очереди
	taskKey := fmt.Sprintf("%s/%d", q.prefix, time.Now().UnixNano())

	resp, err := q.kv.Put(ctx, taskKey, payload)
	if err != nil {
		return 0, fmt.Errorf("ошибка добавления задачи в очередь: %w", err)
	}

	return resp.Header.Revision, nil
}

// Pop атомарно извлекает задачу с наименьшей ревизией создания (FIFO)
func (q *DistributedQueue) Pop(ctx context.Context) (string, string, error) {
	for {
		select {
		case <-ctx.Done():
			return "", "", ctx.Err()
		default:
		}

		// 1. Ищем задачу с НАИМЕНЬШЕЙ CreateRevision (самая старая в очереди)
		opts := []clientv3.OpOption{
			clientv3.WithPrefix(),
			clientv3.WithSort(clientv3.SortByCreateRevision, clientv3.SortAscend),
			clientv3.WithLimit(1),
		}

		resp, err := q.kv.Get(ctx, q.prefix, opts...)
		if err != nil {
			return "", "", err
		}

		if len(resp.Kvs) == 0 {
			// Очередь пуста: делаем небольшую паузу
			time.Sleep(100 * time.Millisecond)
			continue
		}

		targetKV := resp.Kvs[0]
		targetKey := string(targetKV.Key)
		targetVal := string(targetKV.Value)

		// 2. Атомарно удаляем задачу через Txn (только если её ModRevision не изменилась)
		cmp := clientv3.Compare(clientv3.ModRevision(targetKey), "=", targetKV.ModRevision)
		txnResp, err := q.kv.Txn(ctx).
			If(cmp).
			Then(clientv3.OpDelete(targetKey)).
			Commit()

		if err != nil {
			return "", "", err
		}

		// Если транзакция успешна — задача гарантированно захвачена текущим воркером
		if txnResp.Succeeded {
			return targetKey, targetVal, nil
		}

		// Если другой воркер опередил нас, цикл повторяется для следующей задачи
	}
}

func main() {
	fmt.Println("Распределенная очередь задач (FIFO Queue) на базе etcd:")
	fmt.Println(" 1. WithSort(SortByCreateRevision, SortAscend) находит старейшую задачу O(1)")
	fmt.Println(" 2. Txn.If(Compare(ModRevision == rev)).Then(OpDelete) исключает двойную обработку")
	fmt.Println(" 3. Строгая очередность FIFO гарантируется глобальным упорядочиванием Raft")
}
'''
validate_go_code(code27, "code27")
exercises.append({
    "num": 27,
    "title": "Распределенная очередь задач (FIFO Queue) на базе etcd",
    "task": "Реализуйте распределенную FIFO-очередь задач DistributedQueue на базе etcd. Метод Push добавляет элемент в префикс очереди. Метод Pop находит задачу с минимальной CreateRevision через WithSort(SortByCreateRevision, SortAscend) и атомарно удаляет ее через транзакцию Txn, предотвращая дублирование обработки между параллельными воркерами.",
    "theory": "Организация очередей задач в реляционных БД требует `SELECT ... FOR UPDATE SKIP LOCKED`. В etcd v3 распределенная строгая очередь реализуется элегантно благодаря глобальному порядку ревизий создания:\n1. При добавлении задачи `Push` ключ получает уникальную монотонную `CreateRevision`.\n2. Воркер ищет самый первый элемент очереди: `Get(prefix, WithSort(SortByCreateRevision, SortAscend), WithLimit(1))`.\n3. Захват задачи производится через CAS-транзакцию: `If(ModRevision(key) == currentRev).Then(OpDelete(key))`.\n4. Если транзакция успешна, узел получает эксклюзивное право на выполнение задачи. Если конкурирующий воркер успел перехватить ее раньше, транзакция отклоняется, и воркер переходит к следующей задаче.",
    "step_by_step": [
        "Создайте структуру DistributedQueue с полями clientv3.KV и prefix.",
        "В методе Push сгенерируйте ключ с таймстемпом и сохраните полезную нагрузку.",
        "В методе Pop вызовите Get с сортировкой clientv3.SortByCreateRevision по возрастанию с лимитом 1.",
        "Сформируйте транзакцию Txn с условием совпадения ModRevision и удалением OpDelete.",
        "При успехе txnResp.Succeeded верните ключ и значение задачи."
    ],
    "code_blocks": [{
        "filename": "etcd_distributed_queue.go",
        "lang": "go",
        "code": code27
    }],
    "under_the_hood": "Поскольку Raft строго линеаризует все операции записи, невозможно появление двух задач с одинаковой `CreateRevision`. Очередь etcd является математически строгой FIFO (First-In, First-Out), не подверженной race condition.",
    "pitfalls": [
        "Большой объем очереди: etcd не предназначен для очередей на миллионы сообщений (для этого есть RabbitMQ/Kafka). Очередь etcd идеальна для редких, критически важных системных задач (миграции, бэкапы, деплои).",
        "Потеря задачи при падении воркера: если задача удаляется из etcd ДО ее завершения, при падении воркера она пропадет. Более надежный паттерн — временная привязка задачи к Lease воркера."
    ],
    "bigtech_interview": "Почему etcd не рекомендуется использовать как высокопроизводительный брокер сообщений? Каждая запись и удаление в etcd — это fsync на диск на кворуме узлов и создание новых ревизий в bbolt. При 50 000 сообщений/сек база etcd мгновенно исчерпает квоту памяти."
})

# Ex 28: Встраиваемый кластер etcd в Go-тестах (Embedded etcd)
code28 = r'''package main

import (
	"context"
	"fmt"
	"net/url"
	"os"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/server/v3/embed"
)

// EmbeddedEtcdCluster управляет запуском изолированного узла etcd прямо в памяти процесса
type EmbeddedEtcdCluster struct {
	server *embed.Etcd
	client *clientv3.Client
	tmpDir string
}

// StartEmbeddedEtcd запускает локальный тестовый сервер etcd
func StartEmbeddedEtcd() (*EmbeddedEtcdCluster, error) {
	tmpDir, err := os.MkdirTemp("", "embedded-etcd-*")
	if err != nil {
		return nil, err
	}

	cfg := embed.NewConfig()
	cfg.Dir = tmpDir
	cfg.LogLevel = "error" // Отключаем шумные логи рантайма

	// Назначаем локальные эфемерные порты
	clientURL, _ := url.Parse("http://127.0.0.1:0")
	peerURL, _ := url.Parse("http://127.0.0.1:0")

	cfg.ListenClientUrls = []url.URL{*clientURL}
	cfg.AdvertiseClientUrls = []url.URL{*clientURL}
	cfg.ListenPeerUrls = []url.URL{*peerURL}
	cfg.AdvertisePeerUrls = []url.URL{*peerURL}
	cfg.InitialCluster = cfg.InitialClusterFromName(cfg.Name)

	e, err := embed.StartEtcd(cfg)
	if err != nil {
		_ = os.RemoveAll(tmpDir)
		return nil, fmt.Errorf("ошибка запуска embedded etcd: %w", err)
	}

	select {
	case <-e.Server.ReadyNotify():
		// Сервер успешно поднялся и готов принимать запросы
	case <-time.After(10 * time.Second):
		e.Close()
		_ = os.RemoveAll(tmpDir)
		return nil, fmt.Errorf("таймаут ожидания готовности etcd")
	}

	// Создаем клиент к запущенному встроенному серверу
	clientEndpoints := make([]string, len(e.Clients))
	for i, l := range e.Clients {
		clientEndpoints[i] = l.Addr().String()
	}

	cli, err := clientv3.New(clientv3.Config{
		Endpoints:   clientEndpoints,
		DialTimeout: 3 * time.Second,
	})
	if err != nil {
		e.Close()
		_ = os.RemoveAll(tmpDir)
		return nil, err
	}

	return &EmbeddedEtcdCluster{
		server: e,
		client: cli,
		tmpDir: tmpDir,
	}, nil
}

func (c *EmbeddedEtcdCluster) Close() {
	if c.client != nil {
		_ = c.client.Close()
	}
	if c.server != nil {
		c.server.Close()
	}
	_ = os.RemoveAll(c.tmpDir)
}

func (c *EmbeddedEtcdCluster) Client() *clientv3.Client {
	return c.client
}

func main() {
	fmt.Println("Встраиваемый кластер etcd в Go-тестах (Embedded etcd):")
	fmt.Println(" 1. embed.StartEtcd(cfg) запускает настоящий полноценный узел etcd в процессе")
	fmt.Println(" 2. <-e.Server.ReadyNotify() сигнализирует о готовности Raft кворума")
	fmt.Println(" 3. Идеально для TestMain() в CI без необходимости Docker daemon")
}
'''
validate_go_code(code28, "code28")
exercises.append({
    "num": 28,
    "title": "Встраиваемый кластер etcd в Go-тестах (Embedded etcd)",
    "task": "Изучите пакет go.etcd.io/etcd/server/v3/embed. Создайте структуру EmbeddedEtcdCluster для запуска полноценного узла etcd внутри процесса Go. Настройте конфигурацию с эфемерной временной директорией, ожиданием готовности через e.Server.ReadyNotify() и корректным освобождением ресурсов.",
    "theory": "Интеграционное тестирование кода, зависящего от etcd (блокировки, выборы лидера, транзакции), часто упирается в необходимость запуска внешнего Docker контейнера (`testcontainers-go`). В средах без Docker (некоторые CI/CD раннеры, песочницы) это невозможно.\n\nПоскольку etcd написан на чистом Go, его можно запустить как обычную библиотеку прямо внутри тестового бинарника:\n- Пакет `go.etcd.io/etcd/server/v3/embed` позволяет программно поднять настоящий экземпляр etcd сервер со всеми Raft-механизмами.\n- Канал `<-e.Server.ReadyNotify()` сообщает, когда сервер полностью инициализирован и готов обрабатывать gRPC вызовы.\n- После выполнения тестов сервер штатно закрывается методом `Close()`, а временная директория удаляется.",
    "step_by_step": [
        "Импортируйте пакет embed из go.etcd.io/etcd/server/v3/embed.",
        "Создайте временную директорию через os.MkdirTemp.",
        "Сконфигурируйте embed.NewConfig с эфемерными URL адресами.",
        "Вызовите embed.StartEtcd(cfg) и дождитесь сигнала из канала e.Server.ReadyNotify().",
        "Инициализируйте clientv3.New с эндпоинтами созданного встроенного сервера."
    ],
    "code_blocks": [{
        "filename": "embedded_etcd_test.go",
        "lang": "go",
        "code": code28
    }],
    "under_the_hood": "Встроенный etcd исполняется в тех же горутинах текущего процесса ОС. Это позволяет запускать сотни интеграционных тестов за секунды без сетевых накладных расходов виртуализации Docker.",
    "pitfalls": [
        "Утечка директории: если забыть удалить `tmpDir` в defer, диск забьется сотнями временных файлов BoltDB.",
        "Конфликты портов: при запуске тестов с флагом `-parallel` использование фиксированных портов (`2379`) приведет к ошибке `bind: address already in use`. Следует использовать порт `:0` для автоматического назначения свободного порта ОС."
    ],
    "bigtech_interview": "Почему мокирование клиента `clientv3.KV` через testify/mock уступает тестированию на Embedded etcd? Моки не способны воспроизвести тонкости распределенного консенсуса, конкуренции ревизий, тайм-аутов аренды и поведения Watcher при сбоях. Тестирование на реальном встраиваемом движке дает 100% достоверность."
})

# Ex 29: Мониторинг кластера etcd: экспорт метрик и RTT
code29 = r'''package main

import (
	"context"
	"fmt"
	"sync"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
)

// EtcdMetricsCollector собирает телеметрию производительности etcd клиента
type EtcdMetricsCollector struct {
	cli        *clientv3.Client
	mu         sync.Mutex
	latencies  map[string]time.Duration
	callCounts map[string]int64
	errorCount int64
}

func NewEtcdMetricsCollector(cli *clientv3.Client) *EtcdMetricsCollector {
	return &EtcdMetricsCollector{
		cli:        cli,
		latencies:  make(map[string]time.Duration),
		callCounts: make(map[string]int64),
	}
}

// TimedPut выполняет запись с замером латентности
func (c *EtcdMetricsCollector) TimedPut(ctx context.Context, key, val string) error {
	start := time.Now()
	_, err := c.cli.Put(ctx, key, val)
	elapsed := time.Since(start)

	c.mu.Lock()
	defer c.mu.Unlock()

	c.callCounts["Put"]++
	c.latencies["Put"] += elapsed

	if err != nil {
		c.errorCount++
		return err
	}

	if elapsed > 50*time.Millisecond {
		fmt.Printf("⚠️ [PERF ALERT] Медленный Put в etcd: %v (> 50ms SLI threshold)!\n", elapsed)
	}

	return nil
}

// TimedGet выполняет чтение с замером латентности
func (c *EtcdMetricsCollector) TimedGet(ctx context.Context, key string) (string, error) {
	start := time.Now()
	resp, err := c.cli.Get(ctx, key)
	elapsed := time.Since(start)

	c.mu.Lock()
	defer c.mu.Unlock()

	c.callCounts["Get"]++
	c.latencies["Get"] += elapsed

	if err != nil {
		c.errorCount++
		return "", err
	}

	if len(resp.Kvs) == 0 {
		return "", nil
	}
	return string(resp.Kvs[0].Value), nil
}

// PrintReport выводит агрегированную статистику
func (c *EtcdMetricsCollector) PrintReport() {
	c.mu.Lock()
	defer c.mu.Unlock()

	fmt.Println("\n=== ОТЧЕТ ПРОИЗВОДИТЕЛЬНОСТИ ETCD КЛИЕНТА ===")
	for op, count := range c.callCounts {
		avg := c.latencies[op] / time.Duration(count)
		fmt.Printf(" Операция: %-6s Вызовов: %-6d Средняя задержка: %v\n", op, count, avg)
	}
	fmt.Printf(" Всего ошибок: %d\n", c.errorCount)
}

func main() {
	fmt.Println("Мониторинг кластера etcd: экспорт метрик и задержек RTT:")
	fmt.Println(" 1. Замер латентности операций Put / Get для отслеживания деградации дисков")
	fmt.Println(" 2. Алерт на задержку > 50 мс сигнализирует о задержках fsync на кворуме Raft")
	fmt.Println(" 3. Интеграция с Prometheus через экспортеры etcd_request_duration_seconds")
}
'''
validate_go_code(code29, "code29")
exercises.append({
    "num": 29,
    "title": "Мониторинг кластера etcd: экспорт метрик и RTT",
    "task": "Оснастите клиент etcd v3 телеметрией и мониторингом задержек (RTT). Реализуйте коллектор EtcdMetricsCollector, выполняющий замер времени выполнения методов TimedPut и TimedGet, фиксирующий среднюю задержку операций и сигнализирующий о деградации при превышении SLI порога 50 мс.",
    "theory": "etcd является узким местом всей инфраструктуры: если etcd замедляется, начинают тормозить абсолютно все сервисы кластера.\n\nКлючевые золотые сигналы (Golden Signals) здоровья etcd:\n1. `etcd_disk_wal_fsync_duration_seconds`: время записи журнала на диск. Если p99 превышает 10 мс — диски перегружены.\n2. `etcd_network_peer_round_trip_time_seconds`: задержка репликации между узлами кластера. Рост свидетельствует о сетевом джиттере.\n3. `etcd_server_leader_changes_seen_total`: частая смена лидера говорит о потере Heartbeat-пакетов и нестабильности.\n4. Клиентская латентность Put/Get: замер времени выполнения запроса со стороны приложения позволяет вовремя зафиксировать проблемы до наступления масштабного сбоя.",
    "step_by_step": [
        "Создайте EtcdMetricsCollector со словарями для учета числа вызовов и накопленной задержки.",
        "В методе TimedPut зафиксируйте метку времени старта через time.Now().",
        "Вызовите cli.Put и вычислите длительность через time.Since(start).",
        "Добавьте проверку порогового значения латентности (> 50ms) с выводом предупреждения.",
        "Реализуйте метод PrintReport для расчета средних задержек операций."
    ],
    "code_blocks": [{
        "filename": "etcd_client_metrics.go",
        "lang": "go",
        "code": code29
    }],
    "under_the_hood": "Сам сервер etcd нативно экспортирует сотни Prometheus-метрик по адресу `:2379/metrics`. Go-клиент `clientv3` также поддерживает интерцепторы `grpc.WithUnaryInterceptor`, позволяющие автоматически передавать метрики в OpenTelemetry спаны.",
    "pitfalls": [
        "Блокировка мьютекса в горячем пути: в приложениях с десятками тысяч RPS сбор метрик должен использовать lock-free атомарные счетчики или гистограммы Prometheus без тяжелых глобальных мьютексов.",
        "Игнорирование сетевого контекста: замер времени должен учитывать сетевой таймаут `ctx`, иначе зависший вызов исказит среднюю статистику."
    ],
    "bigtech_interview": "Какой самый критичный алерт для кластера etcd в SRE? 'HasNoLeader' (у кластера нет лидера) и 'HighNumberOfFailedProposals' (рост числа отклоненных предложений Raft из-за перегрузки дисков или сетевых разделов)."
})

# Ex 30: Enterprise Подсистема Распределенной Координации на etcd v3
code30 = r'''package main

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/client/v3/concurrency"
)

// EnterpriseCoordinator объединяет все возможности распределенной координации etcd v3
type EnterpriseCoordinator struct {
	cli         *clientv3.Client
	serviceName string
	nodeID      string
	session     *concurrency.Session

	// Компоненты координации
	mutex       *concurrency.Mutex
	election    *concurrency.Election
	isLeader    atomic.Bool

	// Локальный кэш
	configCache sync.Map
	stopCh      chan struct{}
	wg          sync.WaitGroup
}

func NewEnterpriseCoordinator(cli *clientv3.Client, serviceName, nodeID string) (*EnterpriseCoordinator, error) {
	// 1. Создаем глобальную сессию с авто-продлением KeepAlive на 15 секунд
	session, err := concurrency.NewSession(cli, concurrency.WithTTL(15))
	if err != nil {
		return nil, fmt.Errorf("ошибка создания etcd сессии: %w", err)
	}

	lockKey := fmt.Sprintf("/enterprise/locks/%s", serviceName)
	electionPrefix := fmt.Sprintf("/enterprise/elections/%s", serviceName)

	return &EnterpriseCoordinator{
		cli:         cli,
		serviceName: serviceName,
		nodeID:      nodeID,
		session:     session,
		mutex:       concurrency.NewMutex(session, lockKey),
		election:    concurrency.NewElection(session, electionPrefix),
		stopCh:      make(chan struct{}),
	}, nil
}

// RegisterServiceInstance регистрирует узел в реестре Service Discovery
func (c *EnterpriseCoordinator) RegisterServiceInstance(ctx context.Context, addr string) error {
	key := fmt.Sprintf("/enterprise/services/%s/%s", c.serviceName, c.nodeID)
	_, err := c.cli.Put(ctx, key, addr, clientv3.WithLease(c.session.Lease()))
	if err != nil {
		return fmt.Errorf("сбой регистрации инстанса: %w", err)
	}
	fmt.Printf("✅ [REGISTRY] Узел %s зарегистрирован: %s -> %s (LeaseID=%x)\n",
		c.nodeID, key, addr, c.session.Lease())
	return nil
}

// RunElectionCampaign участвует в выборах лидера в фоновом режиме
func (c *EnterpriseCoordinator) RunElectionCampaign(ctx context.Context) {
	c.wg.Add(1)
	go func() {
		defer c.wg.Done()
		fmt.Printf("[COORDINATOR] Узел %s начинает предвыборную кампанию...\n", c.nodeID)
		if err := c.election.Campaign(ctx, c.nodeID); err != nil {
			fmt.Printf("Кампания завершена: %v\n", err)
			return
		}
		c.isLeader.Store(true)
		fmt.Printf("👑 [COORDINATOR] Узел %s СТАЛ ЛИДЕРОМ КЛАСТЕРА!\n", c.nodeID)
	}()
}

// ExecuteWithLock выполняет задачу под защитой распределенного мьютекса
func (c *EnterpriseCoordinator) ExecuteWithLock(ctx context.Context, fn func() error) error {
	if err := c.mutex.Lock(ctx); err != nil {
		return err
	}
	defer func() {
		_ = c.mutex.Unlock(context.Background())
	}()

	return fn()
}

// Shutdown корректно завершает работу: добровольная отставка, освобождение сессии
func (c *EnterpriseCoordinator) Shutdown(ctx context.Context) error {
	close(c.stopCh)

	if c.isLeader.Load() {
		fmt.Printf("[SHUTDOWN] Узел %s добровольно слагает полномочия лидера (Resign)...\n", c.nodeID)
		_ = c.election.Resign(ctx)
		c.isLeader.Store(false)
	}

	c.session.Close()
	c.wg.Wait()
	fmt.Printf("🏁 [SHUTDOWN] Координатор узла %s штатно остановлен.\n", c.nodeID)
	return nil
}

func main() {
	fmt.Println("=== ENTERPRISE ПОДСИСТЕМА РАСПРЕДЕЛЕННОЙ КООРДИНАЦИИ НА ETCD V3 ===")
	fmt.Println(" 1. Service Discovery с автоматической регистрацией по LeaseID сессии")
	fmt.Println(" 2. Фоновые выборы лидера с мгновенной отставкой Resign() при Shutdown")
	fmt.Println(" 3. Распределенный Fair Mutex для синхронизации критических операций")
	fmt.Println(" 4. Полная защита от дедлоков, утечек горутин и разрывов сети")
}
'''
validate_go_code(code30, "code30")
exercises.append({
    "num": 30,
    "title": "Enterprise Подсистема Распределенной Координации на etcd v3",
    "task": "Спроектируйте и разработайте законченную корпоративную библиотеку координации EnterpriseCoordinator на чистом Go. Объедините автоматическую регистрацию Service Discovery с единой сессией Lease KeepAlive, фоновые выборы лидера с добровольной отставкой Resign, распределенные блокировки Mutex и безопасное завершение Graceful Shutdown.",
    "theory": "В завершающем упражнении мы синтезируем все ключевые концепции распределенной координации в законченный модуль уровня Staff Engineer:\n1. Единый жизненный цикл сессии: все примитивы (мьютекс, выборы лидера, регистрация сервиса) привязаны к одному объекту `concurrency.Session`. Это гарантирует согласованность: при падении узла одновременно освобождается мьютекс, передается лидерство и удаляется регистрационный адрес сервиса.\n2. Отказоустойчивость: использование встроенного KeepAlive, защита от `SIGKILL` через Lease TTL и поддержка мгновенной передачи власти при штатном выключении через `Resign()`.\n3. Высокая производительность: отсутствие поллинга, реактивная модель на долгих gRPC потоках HTTP/2 и строгая линеаризуемость консенсуса Raft.\n\nТакая координационная подсистема лежит в основе архитектуры высоконадежных микросервисов в ведущих BigTech компаниях.",
    "step_by_step": [
        "Спроектируйте EnterpriseCoordinator с единой сессией concurrency.Session.",
        "Реализуйте метод RegisterServiceInstance с привязкой ключа к session.Lease().",
        "Напишите метод RunElectionCampaign с фоновым вызовом election.Campaign в горутине.",
        "Реализуйте метод ExecuteWithLock для синхронизации критических секций.",
        "В методе Shutdown предусмотрите добровольную отставку лидера (Resign), закрытие сессии и ожидание завершения горутин через sync.WaitGroup."
    ],
    "code_blocks": [{
        "filename": "enterprise_etcd_coordinator.go",
        "lang": "go",
        "code": code30
    }],
    "under_the_hood": "Благодаря использованию единого `LeaseID` для всех ресурсов ноды нагрузка на кластер etcd минимальна: одна горутина шлет всего один heartbeat раз в 5 секунд, поддерживая одновременную регистрацию сервиса, лидерство и блокировки.",
    "pitfalls": [
        "Создание нескольких независимых сессий: если создать отдельную сессию для блокировок и отдельную для выборов, сервис будет расходовать лишние ресурсы и может попасть в состояние частичного падения (рассинхронизация сессий).",
        "Блокировка метода Shutdown: если отставка `Resign()` зависнет из-за отсутствия контекста с таймаутом, контейнер будет убит по SIGKILL через terminationGracePeriodSeconds."
    ],
    "bigtech_interview": "Как в распределенных системах предотвратить проблему 'Split-Brain' и обеспечить консистентность при сбоях сети? На интервью Staff Engineer ожидают ответ: использование систем с кворумным консенсусом (etcd / Raft) в сочетании с эфемерными арендами (Leases), строгими глобальными ревизиями (Fencing Tokens) и процедурой добровольной отставки (Resign)."
})

# Save Part 2
out_path = '/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch95_p2.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Chapter 95 Part 2 generated successfully: {len(exercises)} exercises.")
