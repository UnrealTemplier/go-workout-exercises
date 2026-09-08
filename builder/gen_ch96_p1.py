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

# Ex 1: Проблема даунтайма при миграциях схемы в HighLoad
code1 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
	"sync"
	"time"
)

// MigrationLockAnalyzer анализирует влияние эксклюзивных блокировок на пул соединений
type MigrationLockAnalyzer struct {
	maxPoolSize int
}

func NewMigrationLockAnalyzer(poolSize int) *MigrationLockAnalyzer {
	return &MigrationLockAnalyzer{maxPoolSize: poolSize}
}

// SimulateLockContention демонстрирует, как долгий DDL лок забивает пул соединений
func (a *MigrationLockAnalyzer) SimulateLockContention(ctx context.Context, ddlDuration time.Duration, incomingRPS int) {
	fmt.Printf("[SIMULATION] Старт симуляции DDL блокировки (Длительность DDL: %v, RPS: %d, Пул: %d)...\n",
		ddlDuration, incomingRPS, a.maxPoolSize)

	var activeConns int
	var queuedRequests int
	var mu sync.Mutex

	stopCh := make(chan struct{})
	ticker := time.NewTicker(time.Second / time.Duration(incomingRPS))
	defer ticker.Stop()

	// 1. Поток миграции захватывает ACCESS EXCLUSIVE LOCK
	go func() {
		fmt.Println("🔒 [DDL] Начало выполнения: ALTER TABLE users ADD COLUMN age INT (ACCESS EXCLUSIVE LOCK)")
		time.Sleep(ddlDuration)
		fmt.Println("🔓 [DDL] Миграция завершена, блокировка снята")
		close(stopCh)
	}()

	// 2. Входящие клиентские запросы выстраиваются в очередь ожидания
	for {
		select {
		case <-stopCh:
			mu.Lock()
			fmt.Printf("Итог аварии: Очередь запросов: %d, Использовано соединений: %d/%d (Пул исчерпан)\n",
				queuedRequests, activeConns, a.maxPoolSize)
			mu.Unlock()
			return
		case <-ticker.C:
			mu.Lock()
			if activeConns < a.maxPoolSize {
				activeConns++
			} else {
				queuedRequests++
			}
			mu.Unlock()
		}
	}
}

func main() {
	analyzer := NewMigrationLockAnalyzer(20) // Пул на 20 соединений
	ctx := context.Background()

	// Эмулируем DDL лок на 200 мс при 150 RPS
	analyzer.SimulateLockContention(ctx, 200*time.Millisecond, 150)
	fmt.Println("Золотое правило Zero-Downtime: Ни одна DDL блокировка не должна длиться более нескольких миллисекунд!")
}
'''
validate_go_code(code1, "code1")
exercises.append({
    "num": 1,
    "title": "Проблема даунтайма при миграциях схемы в HighLoad",
    "task": "Изучите механизм деградации базы данных при выполнении DDL-команд под нагрузкой. Смоделируйте структуру MigrationLockAnalyzer, демонстрирующую исчерпание пула соединений (Connection Pool Exhaustion) и лавинообразный рост очереди запросов при захвате таблицей ACCESS EXCLUSIVE LOCK.",
    "theory": "В реляционных СУБД (PostgreSQL, MySQL) операции изменения схемы (DDL) требуют захвата блокировок определенного уровня. Самый жесткий уровень — `ACCESS EXCLUSIVE LOCK` (PostgreSQL), который блокирует абсолютно все входящие операции чтения (`SELECT`) и записи (`INSERT`, `UPDATE`, `DELETE`).\n\nАнатомия каскадной аварии при наивной миграции:\n1. Инженер запускает `ALTER TABLE users ADD COLUMN ...` под боевой нагрузкой 5 000 RPS.\n2. Даже если сам DDL выполняется всего 3–5 секунд, за это время скапливаются 15 000–25 000 входящих HTTP-запросов.\n3. Каждый ожидающий запрос удерживает соединение из пула (например, `pgxpool.Pool` на 50 коннектов).\n4. Пул соединений моментально исчерпывается: новые HTTP-хендлеры начинают возвращать 504 Gateway Timeout, веб-серверы захлебываются, и весь сервис падает.\n\nЗолотое правило Zero-Downtime: Любая миграция схемы на production должна занимать минимальное время (микросекунды для DDL метаданных) и никогда не сканировать строки таблицы под эксклюзивным локом.",
    "step_by_step": [
        "Определите структуру MigrationLockAnalyzer с параметром максимального размера пула maxPoolSize.",
        "Запустите имитацию захвата ACCESS EXCLUSIVE LOCK в фоновом потоке.",
        "Смоделируйте поступление пользовательских запросов через time.Ticker.",
        "Зафиксируйте исчерпание пула соединений и выстраивание очереди ожидающих вызовов.",
        "Сформулируйте архитектурные требования к бездаунтаймным миграциям."
    ],
    "code_blocks": [{
        "filename": "lock_contention_simulator.go",
        "lang": "go",
        "code": code1
    }],
    "under_the_hood": "В очереди блокировок PostgreSQL действует правило FIFO с приоритетом эксклюзивных замков: если тяжелый DDL встал в очередь на получение `ACCESS EXCLUSIVE`, все последующие легкие `SELECT` блокируются позади него, даже если таблица в этот момент читается другой транзакцией.",
    "pitfalls": [
        "Тестирование миграций на пустой локальной БД: команда `ALTER TABLE` на 1 000 записей выполняется за 1 мс, но на таблице со 100 млн записей и 50 ГБ данных тот же запрос уронит прод.",
        "Игнорирование очередей: блокирует систему не сама операция, а очередь заблокированных ею запросов клиентов."
    ],
    "bigtech_interview": "Что такое 'Lock Queue Starvation' в PostgreSQL? Когда транзакция DDL запрашивает эксклюзивный лок, она ждет завершения всех текущих читающих транзакций. Но пока она ждет, она блокирует ВСЕ новые запросы, мгновенно останавливая прием трафика в сервисе."
})

# Ex 2: Паттерн Expand-Contract (Parallel Run)
code2 = r'''package main

import (
	"fmt"
)

// MigrationPhase описывает этап эволюции схемы
type MigrationPhase string

const (
	Phase1Expand     MigrationPhase = "1. Expand (Расширение схемы)"
	Phase2DualWrite  MigrationPhase = "2. Dual Write (Двойная запись)"
	Phase3Backfill   MigrationPhase = "3. Backfill (Фоновый перенос данных)"
	Phase4SwitchRead MigrationPhase = "4. Switch Read (Переключение чтения)"
	Phase5Contract   MigrationPhase = "5. Contract (Сжатие и удаление старого)"
)

// UserDataV1 модель данных до миграции
type UserDataV1 struct {
	ID   int64
	Name string
}

// UserDataV2 модель данных после миграции (разделение на FirstName и LastName)
type UserDataV2 struct {
	ID        int64
	FirstName string
	LastName  string
}

// ExpandContractDemo иллюстрирует состояние репозитория на каждом этапе
func ExpandContractDemo() {
	phases := []struct {
		phase MigrationPhase
		db    string
		app   string
	}{
		{
			phase: Phase1Expand,
			db:    "ALTER TABLE users ADD COLUMN first_name TEXT NULL, ADD COLUMN last_name TEXT NULL;",
			app:   "Версия v1.0 продолжает писать и читать только из столбца 'name'",
		},
		{
			phase: Phase2DualWrite,
			db:    "Схема содержит: name, first_name, last_name",
			app:   "Версия v2.0 пишет в name И в (first_name, last_name), читает из name",
		},
		{
			phase: Phase3Backfill,
			db:    "Фоновый Go-воркер порциями сплитит исторические name -> (first_name, last_name)",
			app:   "Версия v2.0 в проде, Dual-Write обеспечивает свежесть новых записей",
		},
		{
			phase: Phase4SwitchRead,
			db:    "100% строк перенесены и проверены",
			app:   "Версия v3.0 читает из first_name/last_name, сохраняет Dual-Write для безопасности",
		},
		{
			phase: Phase5Contract,
			db:    "ALTER TABLE users DROP COLUMN name;",
			app:   "Версия v4.0 пишет и читает только first_name/last_name. Миграция завершена!",
		},
	}

	fmt.Println("=== ФАЗЫ ЖИЗНЕННОГО ЦИКЛА EXPAND-CONTRACT ===")
	for _, p := range phases {
		fmt.Printf("\n▶ %s\n   БД:  %s\n   КОД: %s\n", p.phase, p.db, p.app)
	}
}

func main() {
	ExpandContractDemo()
}
'''
validate_go_code(code2, "code2")
exercises.append({
    "num": 2,
    "title": "Паттерн Expand-Contract (Parallel Run)",
    "task": "Изучите фундаментальный архитектурный паттерн эволюции схем данных Expand-Contract (также известный как Parallel Run или Tolerant Reader). Разберите 5 обязательных фаз жизненного цикла миграции при изменении структуры таблицы под непрерывной нагрузкой.",
    "theory": "Паттерн Expand-Contract — единственный математически корректный способ изменения схемы базы данных без простоя:\n\n1. Expand (Расширение): в базу добавляются новые структуры (столбцы, таблицы), обязательно допускающие `NULL` или имеющие значения по умолчанию. Старые структуры не изменяются. Старая версия кода v1 продолжает работать.\n2. Dual Write (Двойная запись): выкатывается версия кода v2, которая начинает записывать данные ОДНОВРЕМЕННО в старую и новую структуру. Чтение пока идет из старой.\n3. Backfill (Миграция истории): отдельный фоновый воркер чанками переносит исторические данные из старой структуры в новую. Новые данные уже пишутся шагом 2, поэтому рассинхронизации нет.\n4. Switch Read (Переключение чтения): выкатывается версия v3, которая переключает чтение на новую структуру данных. Если обнаружится ошибка, можно мгновенно откатить чтение назад на v2 без потери данных.\n5. Contract (Сжатие / Удаление): удаление старых столбцов и вспомогательного кода двойной записи (версия v4).",
    "step_by_step": [
        "Изучите назначение каждой из 5 фаз паттерна Expand-Contract.",
        "Определите структуры данных UserDataV1 и UserDataV2.",
        "Сопоставьте состояние схемы БД и поведение кода приложения на каждом этапе.",
        "Проанализируйте, почему удаление старых колонок всегда выполняется в самом конце отдельным независимым релизом."
    ],
    "code_blocks": [{
        "filename": "expand_contract_phases.go",
        "lang": "go",
        "code": code2
    }],
    "under_the_hood": "Expand-Contract разделяет одну опасную операцию изменения схемы на 3 независимых деплоя приложения и 2 легкие DDL-миграции, растянутые во времени. Это полностью устраняет зависимость деплоя кода от деплоя БД.",
    "pitfalls": [
        "Попытка сделать все за один релиз: если добавить колонку, перенести данные и удалить старую колонку в одном релизе, старые поды упадут с ошибкой отсутствия колонок во время rolling update.",
        "Забытый этап Contract: если не удалять старые неиспользуемые столбцы, база данных зарастет техническим долгом из сотен колонок-призраков."
    ],
    "bigtech_interview": "Как паттерн Expand-Contract соотносится с архитектурным принципом Decoupling? Он разрывает временную связь (Temporal Coupling) между миграцией хранилища и обновлением прикладных микросервисов, позволяя им эволюционировать с разной скоростью."
})

# Ex 3: Инструменты миграций на Go: golang-migrate vs goose
code3 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
)

// MigrationToolComparison сравнивает библиотеки миграций
type MigrationToolComparison struct {
	ToolName        string
	SupportsSQL     bool
	SupportsGoCode  bool
	Transactional   bool
	OutOfOrderRun   bool
}

// CustomGoMigrationFunction имитирует миграцию на Go для сложного преобразования данных
type CustomGoMigrationFunction func(ctx context.Context, tx *sql.Tx) error

func CompareMigrationTools() []MigrationToolComparison {
	return []MigrationToolComparison{
		{
			ToolName:       "pressly/goose",
			SupportsSQL:    true,
			SupportsGoCode: true,  // Поддерживает чистый Go код внутри миграций (goose.AddMigration)
			Transactional:  true,
			OutOfOrderRun:  false,
		},
		{
			ToolName:       "golang-migrate/migrate",
			SupportsSQL:    true,
			SupportsGoCode: false, // Только SQL-файлы
			Transactional:  true,
			OutOfOrderRun:  false,
		},
	}
}

func main() {
	tools := CompareMigrationTools()
	fmt.Println("Сравнение ведущих инструментов миграций в экосистеме Go:")
	for _, t := range tools {
		fmt.Printf(" ▶ %-25s SQL: %v | Go-код: %-5v | Транзакции: %v\n",
			t.ToolName, t.SupportsSQL, t.SupportsGoCode, t.Transactional)
	}

	fmt.Println("\nВывод для HighLoad: goose предпочтителен для сложных данных благодаря поддержке Go-функций,")
	fmt.Println("а golang-migrate идеален для стандартных чисто SQL-пайплайнов.")
}
'''
validate_go_code(code3, "code3")
exercises.append({
    "num": 3,
    "title": "Инструменты миграций на Go: golang-migrate vs goose",
    "task": "Проведите сравнительный анализ двух главных инструментов версионирования схемы БД на Go: golang-migrate/migrate и pressly/goose. Опишите сценарии, когда чистых SQL-скриптов недостаточно и требуются Go-миграции с программной логикой трансформации данных.",
    "theory": "В Go-сообществе доминируют два инструмента миграций:\n1. `pressly/goose`: поддерживает как классические `.sql` файлы с маркерами `-- +goose Up` и `-- +goose Down`, так и регистрацию Go-функций через `goose.AddMigration(upFn, downFn)`. Это критически важно при сложном хэшировании паролей, обращении к внешним сервисам или сложной десериализации JSON в процессе миграции.\n2. `golang-migrate/migrate`: мощный инструмент с поддержкой десятков СУБД (PostgreSQL, MySQL, ClickHouse, Cassandra, Spanner). Работает со строгими парами файлов `000001_init.up.sql` и `000001_init.down.sql`. Не поддерживает нативный Go-код внутри миграций.\n\nОба инструмента ведут учет примененных версий в специальной системной таблице (`schema_migrations` или `goose_db_version`).",
    "step_by_step": [
        "Изучите структуру таблицы версионирования миграций.",
        "Сравните синтаксис аннотаций goose (-- +goose Up) и golang-migrate.",
        "Объясните, почему для Zero-Downtime миграций с трансформацией данных часто требуются Go-скрипты.",
        "Определите критерии выбора инструмента для корпоративного микросервиса."
    ],
    "code_blocks": [{
        "filename": "migration_tools_comparison.go",
        "lang": "go",
        "code": code3
    }],
    "under_the_hood": "Оба инструмента по умолчанию оборачивают каждую миграцию в `BEGIN ... COMMIT` (если СУБД поддерживает транзакционный DDL). Если скрипт упал на середине, версия миграции не инкрементируется, а база остается чистой.",
    "pitfalls": [
        "Грязное состояние (Dirty State): в golang-migrate при падении миграции без транзакции статус помечается `dirty=true`, блокируя все последующие запуски до ручного вмешательства инженера `migrate force`.",
        "Параллельный запуск миграций: если 10 подов стартуют одновременно, они начнут применять миграции параллельно. Goose и golang-migrate используют advisory locks (`pg_advisory_lock`), чтобы запускать миграции строго в одном экземпляре."
    ],
    "bigtech_interview": "Почему запускать миграции базы данных прямо внутри `main.go` микросервиса в Kubernetes считается анти-паттерном? При одновременном рестарте десятков подов возникает конкуренция за advisory locks. Лучшая практика — запуск мигратора в виде отдельного Kubernetes Job перед стартом Deployment (Init Container или CI/CD step)."
})

# Ex 4: Транзакционные DDL-миграции в PostgreSQL
code4 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
)

// TransactionalMigrationRunner демонстрирует транзакционный DDL в PostgreSQL
type TransactionalMigrationRunner struct {
	db *sql.DB
}

func NewTransactionalMigrationRunner(db *sql.DB) *TransactionalMigrationRunner {
	return &TransactionalMigrationRunner{db: db}
}

// RunTransactionalDDL выполняет DDL изменения внутри транзакции с авто-откатом при ошибке
func (r *TransactionalMigrationRunner) RunTransactionalDDL(ctx context.Context, ddlQueries []string) error {
	// В PostgreSQL CREATE TABLE, ALTER TABLE, ADD COLUMN поддерживают транзакции!
	tx, err := r.db.BeginTx(ctx, &sql.TxOptions{Isolation: sql.LevelReadCommitted})
	if err != nil {
		return fmt.Errorf("ошибка открытия транзакции: %w", err)
	}
	defer tx.Rollback() // Безопасный откат при панике или ошибке

	for idx, query := range ddlQueries {
		fmt.Printf("[TX DDL] Выполнение шага %d: %s\n", idx+1, query)
		if _, err := tx.ExecContext(ctx, query); err != nil {
			return fmt.Errorf("сбой на шаге %d (%s): изменения полностью откатаны: %w", idx+1, query, err)
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("ошибка коммита транзакции DDL: %w", err)
	}

	fmt.Println("✅ [TX DDL] Все DDL операции успешно закоммичены атомарно")
	return nil
}

func main() {
	fmt.Println("Транзакционные DDL-миграции в PostgreSQL:")
	fmt.Println(" 1. В отличие от MySQL/Oracle, в PostgreSQL команды ALTER TABLE / CREATE TABLE атомарны")
	fmt.Println(" 2. При ошибке на 3-м шаге вся миграция полностью откатывается (Rollback)")
	fmt.Println(" 3. Исключение: CREATE INDEX CONCURRENTLY не может выполняться внутри транзакции")
}
'''
validate_go_code(code4, "code4")
exercises.append({
    "num": 4,
    "title": "Транзакционные DDL-миграции в PostgreSQL",
    "task": "Изучите механизм транзакционного DDL в PostgreSQL. Реализуйте метод RunTransactionalDDL, объединяющий серию DDL команд внутри sql.Tx. Докажите, что при возникновении синтаксической ошибки или конфликта на промежуточном шаге база данных не остается в полу-примененном состоянии благодаря автоматическому Rollback.",
    "theory": "Огромное архитектурное преимущество PostgreSQL перед MySQL — поддержка транзакционного DDL (Transactional DDL):\n- В MySQL любая команда `ALTER TABLE` или `CREATE TABLE` неявно вызывает невидимый `COMMIT` текущей транзакции. Если ваш скрипт содержит 3 DDL-команды и упал на 2-й, первая команда уже закоммичена, а база находится в 'сломанном' промежуточном состоянии, требующем ручной починки.\n- В PostgreSQL операции с метаданными каталога (`pg_class`, `pg_attribute`) являются обычными строками системных таблиц. Поэтому блок `BEGIN ... ALTER TABLE ... COMMIT` полностью атомарен: либо применились все изменения схемы, либо ни одного.",
    "step_by_step": [
        "Откройте транзакцию db.BeginTx с уровнем изоляции ReadCommitted.",
        "Настройте отложенный откат через defer tx.Rollback().",
        "Последовательно выполните команды изменения схемы через tx.ExecContext.",
        "Зафиксируйте транзакцию через tx.Commit().",
        "Объясните исключения (команды, которые не могут выполняться в транзакции: CREATE INDEX CONCURRENTLY, VACUUM)."
    ],
    "code_blocks": [{
        "filename": "transactional_ddl_runner.go",
        "lang": "go",
        "code": code4
    }],
    "under_the_hood": "PostgreSQL блокирует таблицы в транзакции в соответствии с уровнем операции. При `Rollback` транзакции все изменения системных каталогов откатываются по журналу WAL, а захваченные блокировки мгновенно снимаются.",
    "pitfalls": [
        "Попытка запустить `CREATE INDEX CONCURRENTLY` внутри транзакции: PostgreSQL вернет ошибку `ERROR: CREATE INDEX CONCURRENTLY cannot run inside a transaction block`.",
        "Слишком длинные транзакции DDL: удержание открытой DDL-транзакции с `time.Sleep` блокирует авто-вакуум и доступ к таблице."
    ],
    "bigtech_interview": "Почему в PostgreSQL не рекомендуется объединять тяжелые DDL операции с манипуляцией данными (`UPDATE`) в одной транзакции? DDL захватывает эксклюзивный лок, а `UPDATE` миллионов строк заставляет этот лок удерживаться на все время обновления, гарантируя отказ в обслуживании всего сервиса."
})

# Ex 5: Обязательное правило: установка lock_timeout
code5 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
	"time"
)

// SafeMigrationExecutor применяет миграции с обязательной защитой lock_timeout
type SafeMigrationExecutor struct {
	db *sql.DB
}

func NewSafeMigrationExecutor(db *sql.DB) *SafeMigrationExecutor {
	return &SafeMigrationExecutor{db: db}
}

// ExecuteMigrationWithTimeout выполняет миграцию с ограничением ожидания блокировки
func (e *SafeMigrationExecutor) ExecuteMigrationWithTimeout(ctx context.Context, migrationSQL string, lockTimeout time.Duration) error {
	tx, err := e.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// 1. Устанавливаем строгий таймаут ожидания блокировки (lock_timeout)
	// Если таблица занята долгим чтением/записью, DDL не будет ждать вечно и не выстроит очередь
	timeoutQuery := fmt.Sprintf("SET LOCAL lock_timeout = '%dms';", lockTimeout.Milliseconds())
	if _, err := tx.ExecContext(ctx, timeoutQuery); err != nil {
		return fmt.Errorf("ошибка установки lock_timeout: %w", err)
	}

	// 2. Устанавливаем statement_timeout для ограничения самого выполнения
	if _, err := tx.ExecContext(ctx, "SET LOCAL statement_timeout = '5s';"); err != nil {
		return fmt.Errorf("ошибка установки statement_timeout: %w", err)
	}

	fmt.Printf("[SAFE MIGRATION] Применение DDL с защитой lock_timeout=%v...\n", lockTimeout)
	if _, err := tx.ExecContext(ctx, migrationSQL); err != nil {
		return fmt.Errorf("миграция отклонена (предотвращена блокировка пула): %w", err)
	}

	return tx.Commit()
}

func main() {
	fmt.Println("Обязательное правило Zero-Downtime: установка lock_timeout:")
	fmt.Println(" 1. SET LOCAL lock_timeout = '2s' гарантирует аварийный выход, если таблица занята")
	fmt.Println(" 2. Предотвращает выстраивание входящих запросов в очередь за миграцией")
	fmt.Println(" 3. Если лок не получен за 2 секунды — миграция падает, но прод ПРОДОЛЖАЕТ ЖИТЬ")
}
'''
validate_go_code(code5, "code5")
exercises.append({
    "num": 5,
    "title": "Обязательное правило: установка lock_timeout",
    "task": "Спроектируйте компонент SafeMigrationExecutor, гарантирующий исполнение главного правила Zero-Downtime: установка SET LOCAL lock_timeout перед выполнением любой DDL-миграции. Докажите, что ограничение времени ожидания лока спасает production от выстраивания очереди запросов.",
    "theory": "По умолчанию в PostgreSQL параметр `lock_timeout = 0`, что означает БЕСКОНЕЧНОЕ ожидание блокировки.\n\nЧто происходит без `lock_timeout`:\n1. В базе идет долгий аналитический запрос `SELECT` длительностью 30 секунд.\n2. Мигратор выполняет `ALTER TABLE users ADD COLUMN age INT;`.\n3. Мигратор встает в очередь ожидания за `SELECT`.\n4. Все новые входящие запросы к таблице `users` встают в очередь ЗА мигратором.\n5. За 30 секунд скапливаются тысячи запросов, соединения заканчиваются, сервис падает.\n\nРешение: директива `SET LOCAL lock_timeout = '2s'`. Если мигратор не может получить блокировку за 2 секунды, PostgreSQL аварийно прерывает миграцию (`canceling statement due to lock timeout`), снимает запрос из очереди, и сервис продолжает бесперебойно обслуживать пользователей.",
    "step_by_step": [
        "Откройте транзакцию через db.BeginTx.",
        "Выполните команду SET LOCAL lock_timeout = '2000ms' внутри транзакции.",
        "Дополнительно настройте statement_timeout для ограничения длительности самого запроса.",
        "Выполните целевой DDL-запрос.",
        "Продемонстрируйте безопасный откат при конфликте блокировок."
    ],
    "code_blocks": [{
        "filename": "safe_migration_lock_timeout.go",
        "lang": "go",
        "code": code5
    }],
    "under_the_hood": "Ключевое слово `LOCAL` в `SET LOCAL` привязывает действие параметра строго к текущей транзакции. Как только транзакция завершается (коммитом или откатом), значение параметров сбрасывается к глобальным дефолтам сессии пула соединений.",
    "pitfalls": [
        "Забытое слово `LOCAL`: вызов `SET lock_timeout = ...` без `LOCAL` изменит параметр для всего соединения в пуле (connection pool pollution), повлияв на последующие обычные запросы этого коннекта.",
        "Слишком большой таймаут: установка `lock_timeout = '30s'` полностью нивелирует защиту — за 30 секунд прод успеет упасть."
    ],
    "bigtech_interview": "Что делать, если миграция постоянно отваливается по `lock_timeout` из-за непрерывного потока транзакций? Применяется алгоритм повторов с джиттером: скрипт пытается захватить лок с таймаутом 500 мс раз в несколько минут (например, ночью в часы минимального трафика), пока не поймает свободное окно."
})

# Ex 6: Безопасное добавление столбцов со значениями по умолчанию
code6 = r'''package main

import (
	"fmt"
)

// ColumnAdditionStrategy описывает различия версий PostgreSQL
type ColumnAdditionStrategy struct {
	PGVersion        string
	Syntax           string
	RewritesTable    bool
	LockDurationDesc string
	IsZeroDowntime   bool
}

func GetColumnAdditionStrategies() []ColumnAdditionStrategy {
	return []ColumnAdditionStrategy{
		{
			PGVersion:        "PostgreSQL < 11",
			Syntax:           "ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'pending';",
			RewritesTable:    true, // Полная перезапись всех страниц таблицы на диске!
			LockDurationDesc: "Минуты или часы (пропорционально объему таблицы)",
			IsZeroDowntime:   false,
		},
		{
			PGVersion:        "PostgreSQL >= 11",
			Syntax:           "ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'pending';",
			RewritesTable:    false, // Только метаданные в pg_attribute!
			LockDurationDesc: "Доли миллисекунды (мгновенное обновление каталога)",
			IsZeroDowntime:   true,
		},
		{
			PGVersion:        "Универсальный (Legacy)",
			Syntax:           "1) ADD COLUMN status TEXT NULL; 2) UPDATE по чанкам; 3) SET DEFAULT 'pending';",
			RewritesTable:    false,
			LockDurationDesc: "Микросекунды на шагах 1 и 3",
			IsZeroDowntime:   true,
		},
	}
}

func main() {
	fmt.Println("Безопасное добавление столбцов со значениями по умолчанию (DEFAULT):")
	for _, s := range GetColumnAdditionStrategies() {
		fmt.Printf("\nВерсия: %s (Zero-Downtime: %v)\n", s.PGVersion, s.IsZeroDowntime)
		fmt.Printf(" SQL:        %s\n", s.Syntax)
		fmt.Printf(" Перезапись: %v | Задержка лока: %s\n", s.RewritesTable, s.LockDurationDesc)
	}
}
'''
validate_go_code(code6, "code6")
exercises.append({
    "num": 6,
    "title": "Безопасное добавление столбцов со значениями по умолчанию",
    "task": "Изучите эволюцию механики добавления столбцов со значением по умолчанию (DEFAULT) в PostgreSQL. Сравните поведение в PostgreSQL < 11 (полная перезапись таблицы на диске) и PostgreSQL >= 11 (fast default через метаданные каталога pg_attribute).",
    "theory": "Добавление столбца — самая частая операция в жизненном цикле приложения.\n\nИсторическая ловушка (PostgreSQL 10 и старше):\nКоманда `ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'pending';` приводила к тому, что СУБД физически переписывала каждый блок таблицы на диске, добавляя значение `'pending'` во все существующие строки. На таблице в 100 млн записей это вызывало эксклюзивную блокировку на 40–60 минут и гарантированный даунтайн.\n\nРеволюция в PostgreSQL 11+ (Fast Column Default):\nНачиная с PG 11, добавление столбца со статическим значением по умолчанию больше НЕ переписывает таблицу. Значение по умолчанию сохраняется в системном каталоге `pg_attribute` в колонках `atthasmissing` и `attmissingval`. При последующем чтении старых строк движок подставляет значение на лету. Блокировка длится менее 1 миллисекунды!",
    "step_by_step": [
        "Изучите различия в физическом хранении строк в версиях PostgreSQL.",
        "Проанализируйте синтаксис быстрого добавления столбца в PG 11+.",
        "Изучите ограничения: значение по умолчанию должно быть иммутабельным (нельзя использовать функции вида `DEFAULT clock_timestamp()`).",
        "Сформулируйте стратегию для старых версий баз данных (через NULL и чанковый бэкфилл)."
    ],
    "code_blocks": [{
        "filename": "fast_default_column.go",
        "lang": "go",
        "code": code6
    }],
    "under_the_hood": "Если значение `DEFAULT` содержит волатильную функцию (например, `DEFAULT random()`), PostgreSQL не сможет применить оптимизацию Fast Default и будет вынужден переписать таблицу даже в PostgreSQL 16. Значения по умолчанию для Zero-Downtime обязаны быть константными или детерминированными.",
    "pitfalls": [
        "Использование non-immutable default: `DEFAULT now()` или `DEFAULT gen_random_uuid()` приводят к вычислению значения для каждой строки и перезаписи всей таблицы.",
        "Заблуждение о MySQL: в MySQL до версии 8.0 добавление колонки всегда блокировало таблицу (Instant DDL появился только в MySQL 8.0)."
    ],
    "bigtech_interview": "Как безопасно добавить колонку с динамическим UUID по умолчанию в PostgreSQL? 1) Добавить колонку `NULL`, 2) Фоновым скриптом на Go чанками сгенерировать UUID для старых строк, 3) Установить `DEFAULT gen_random_uuid()` только для новых строк."
})

# Ex 7: Добавление ограничения NOT NULL без блокировки таблицы
code7 = r'''package main

import (
	"fmt"
)

// NotNullMigrationPlan описывает трехшаговый алгоритм безопасного добавления NOT NULL
type NotNullMigrationPlan struct {
	Step        int
	Description string
	SQL         string
	LockLevel   string
	Duration    string
}

func GenerateSafeNotNullPlan(tableName, columnName string) []NotNullMigrationPlan {
	return []NotNullMigrationPlan{
		{
			Step:        1,
			Description: "Добавление проверочного ограничения CHECK с флагом NOT VALID",
			SQL:         fmt.Sprintf("ALTER TABLE %s ADD CONSTRAINT check_%s_not_null CHECK (%s IS NOT NULL) NOT VALID;", tableName, columnName, columnName),
			LockLevel:   "SHARE ROW EXCLUSIVE (Микросекунды, запись продолжается)",
			Duration:    "< 5 миллисекунд",
		},
		{
			Step:        2,
			Description: "Фоновая валидация существующих строк без блокировки чтения и записи",
			SQL:         fmt.Sprintf("ALTER TABLE %s VALIDATE CONSTRAINT check_%s_not_null;", tableName, columnName),
			LockLevel:   "SHARE UPDATE EXCLUSIVE (Не блокирует SELECT, INSERT, UPDATE, DELETE)",
			Duration:    "Зависит от размера таблицы (но сервис работает 100% стабильно)",
		},
		{
			Step:        3,
			Description: "Установка нативного NOT NULL (мгновенно, так как CHECK уже доказал валидность) и удаление CHECK",
			SQL:         fmt.Sprintf("ALTER TABLE %s ALTER COLUMN %s SET NOT NULL;\nALTER TABLE %s DROP CONSTRAINT check_%s_not_null;", tableName, columnName, tableName, columnName),
			LockLevel:   "ACCESS EXCLUSIVE (Доли миллисекунды, проверка строк пропускается)",
			Duration:    "< 5 миллисекунд",
		},
	}
}

func main() {
	plan := GenerateSafeNotNullPlan("users", "email")
	fmt.Println("Безопасное добавление ограничения NOT NULL без даунтайма:")
	for _, p := range plan {
		fmt.Printf("\n[Шаг %d] %s\n", p.Step, p.Description)
		fmt.Printf(" SQL:       %s\n", p.SQL)
		fmt.Printf(" Лок:       %s | Время: %s\n", p.LockLevel, p.Duration)
	}
}
'''
validate_go_code(code7, "code7")
exercises.append({
    "num": 7,
    "title": "Добавление ограничения NOT NULL без блокировки таблицы",
    "task": "Изучите проблему блокировки при прямом выполнении команды ALTER TABLE ... ALTER COLUMN ... SET NOT NULL. Разработайте и задокументируйте трехшаговый алгоритм безопасного добавления ограничения через проверочные ограничения CHECK ... NOT VALID и VALIDATE CONSTRAINT.",
    "theory": "Прямая команда `ALTER TABLE users ALTER COLUMN email SET NOT NULL;` опасна на больших таблицах:\nPostgreSQL обязан убедиться, что ни в одной строке таблицы нет значения `NULL`. Для этого он выполняет полный последовательный скан (Sequential Scan) таблицы, удерживая `ACCESS EXCLUSIVE LOCK`. На таблице в 50 ГБ это заморозит запись на 5–10 минут!\n\nБезопасный трехшаговый подход (Zero-Downtime NOT NULL):\n1. Добавляем проверочное ограничение `CHECK (email IS NOT NULL) NOT VALID`. Ключевое слово `NOT VALID` указывает PostgreSQL проверять ограничение ТОЛЬКО для новых входящих записей. Существующие строки не сканируются, лок длится 2 миллисекунды.\n2. Выполняем `ALTER TABLE users VALIDATE CONSTRAINT check_email_not_null;`. СУБД сканирует таблицу в фоновом режиме под слабым замком `SHARE UPDATE EXCLUSIVE`, который НЕ блокирует параллельные операции записи и чтения!\n3. В PostgreSQL 12+ после валидации CHECK-констрейнта команда `ALTER COLUMN email SET NOT NULL` выполняется мгновенно, так как оптимизатор видит уже доказанную валидность данных.",
    "step_by_step": [
        "Сформулируйте SQL-запрос добавления CHECK ограничения с флагом NOT VALID.",
        "Объясните механику фоновой валидации команды VALIDATE CONSTRAINT.",
        "Покажите установку нативного ограничения NOT NULL и последующее удаление временного CHECK констрейнта.",
        "Опишите уровни блокировок на каждом из трех этапов."
    ],
    "code_blocks": [{
        "filename": "safe_not_null_migration.go",
        "lang": "go",
        "code": code7
    }],
    "under_the_hood": "В PostgreSQL 12 оптимизатор компилятора запросов был улучшен: если на колонке есть валидированный `CHECK (col IS NOT NULL)`, вызов `SET NOT NULL` распознает это и пропускает скан таблицы, делая переключение мгновенным.",
    "pitfalls": [
        "Попытка валидации при наличии хотя бы одного NULL: команда `VALIDATE CONSTRAINT` упадет с ошибкой, если в старых данных остался `NULL`. Перед валидацией все строки должны быть предварительно заполнены через Backfill.",
        "Объединение шагов 1 и 2 в одну транзакцию: выполнение `ADD CONSTRAINT ... NOT VALID` и `VALIDATE CONSTRAINT` в одной транзакции уничтожает всю пользу, удерживая эксклюзивный лок на все время валидации."
    ],
    "bigtech_interview": "Почему нативный `NOT NULL` лучше, чем постоянное оставление `CHECK (col IS NOT NULL)`? Нативный `NOT NULL` сохраняется в битовой маске заголовка строки PostgreSQL (HeapTupleHeader), что ускоряет выборки и дает оптимизатору больше информации при построении планов соединения таблиц."
})

# Ex 8: Безопасное создание индексов: CREATE INDEX CONCURRENTLY
code8 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
	"time"
)

// SafeIndexManager управляет конкурентным созданием индексов в PostgreSQL
type SafeIndexManager struct {
	db *sql.DB
}

func NewSafeIndexManager(db *sql.DB) *SafeIndexManager {
	return &SafeIndexManager{db: db}
}

// CreateIndexConcurrently создает индекс без блокировки записи с обработкой сбоев
func (m *SafeIndexManager) CreateIndexConcurrently(ctx context.Context, indexName, tableName, column string) error {
	query := fmt.Sprintf("CREATE INDEX CONCURRENTLY IF NOT EXISTS %s ON %s (%s);", indexName, tableName, column)
	fmt.Printf("[INDEX] Запуск создания индекса: %s\n", query)

	// ВАЖНО: CREATE INDEX CONCURRENTLY НЕЛЬЗЯ выполнять внутри sql.Tx! Вызываем напрямую у db.
	_, err := m.db.ExecContext(ctx, query)
	if err != nil {
		fmt.Printf("⚠️ Сбой создания индекса %s: %v. Проверка статуса INVALID...\n", indexName, err)
		_ = m.cleanupInvalidIndex(ctx, indexName)
		return err
	}

	fmt.Printf("✅ [INDEX DONE] Индекс %s успешно построен без блокировки записи!\n", indexName)
	return nil
}

// cleanupInvalidIndex удаляет поврежденный индекс при сетевых сбоях или дедлоках
func (m *SafeIndexManager) cleanupInvalidIndex(ctx context.Context, indexName string) error {
	// Проверяем, остался ли индекс в статусе INVALID в каталоге pg_index
	checkQuery := `SELECT indisvalid FROM pg_index JOIN pg_class ON pg_class.oid = pg_index.indexrelid WHERE pg_class.relname = $1;`
	var isValid bool
	err := m.db.QueryRowContext(ctx, checkQuery, indexName).Scan(&isValid)
	if err == sql.ErrNoRows {
		return nil // Индекса нет
	}
	if err == nil && !isValid {
		fmt.Printf("🧹 [CLEANUP] Удаление невалидного индекса %s (DROP INDEX CONCURRENTLY)...\n", indexName)
		_, _ = m.db.ExecContext(ctx, fmt.Sprintf("DROP INDEX CONCURRENTLY IF EXISTS %s;", indexName))
	}
	return nil
}

func main() {
	fmt.Println("Безопасное создание индексов: CREATE INDEX CONCURRENTLY:")
	fmt.Println(" 1. Обычный CREATE INDEX захватывает SHARE лок и блокирует все INSERT/UPDATE/DELETE")
	fmt.Println(" 2. CREATE INDEX CONCURRENTLY делает 2 прохода по таблице, позволяя писать во время построения")
	fmt.Println(" 3. При ошибке (дедлок/таймаут) индекс остается в статусе INVALID и требует удаления")
}
'''
validate_go_code(code8, "code8")
exercises.append({
    "num": 8,
    "title": "Безопасное создание индексов: CREATE INDEX CONCURRENTLY",
    "task": "Изучите устройство конкурентного создания индексов в PostgreSQL. Реализуйте сервис SafeIndexManager, выполняющий построение индекса с ключевым словом CONCURRENTLY вне транзакции, и напишите процедуру очистки cleanupInvalidIndex для удаления поврежденных невалидных индексов в случае сбоя.",
    "theory": "Обычная команда `CREATE INDEX ON orders (user_id);` захватывает замок `SHARE LOCK`. Это позволяет читать таблицу (`SELECT`), но полностью блокирует любые модификации (`INSERT`, `UPDATE`, `DELETE`) на все время сканирования и сортировки данных (десятки минут на терабайтных таблицах).\n\nДиректива `CREATE INDEX CONCURRENTLY` решает эту проблему:\n1. Она не блокирует запись: пользователи продолжают оформлять заказы.\n2. Внутреннее устройство: выполняется в два прохода (Two-Pass Architecture):\n   - Проход 1: строится снимок таблицы и первичное дерево индекса.\n   - Ожидание завершения всех параллельных транзакций.\n   - Проход 2: дочитываются изменения, произошедшие за время первого прохода.\n3. Особенность: `CREATE INDEX CONCURRENTLY` категорически не может выполняться внутри транзакции `BEGIN ... COMMIT`.",
    "step_by_step": [
        "Объясните, почему CONCURRENTLY нельзя оборачивать в транзакцию sql.Tx.",
        "Реализуйте метод CreateIndexConcurrently с прямым вызовом db.ExecContext.",
        "Изучите статус indisvalid в системной таблице pg_index.",
        "Напишите метод cleanupInvalidIndex для поиска и удаления незавершенных индексов через DROP INDEX CONCURRENTLY."
    ],
    "code_blocks": [{
        "filename": "concurrent_index_builder.go",
        "lang": "go",
        "code": code8
    }],
    "under_the_hood": "Если во время второго прохода произошел сбой (таймаут, падение узла, нарушение уникальности для UNIQUE), индекс остается в каталоге с флагом `indisvalid = false`. Такой индекс занимает место на диске и замедляет запись, но НЕ используется планировщиком для ускорения чтения. Его необходимо удалить и пересоздать.",
    "pitfalls": [
        "Запуск внутри транзакции: популярные инструменты миграций по умолчанию оборачивают скрипты в транзакции. Для CONCURRENTLY необходимо явно указывать директиву отключения транзакции (в goose: `-- +goose NO TRANSACTION`).",
        "Увеличенное время построения: CONCURRENTLY строится в 2–3 раза дольше обычного индекса из-за двух проходов и ожидания транзакций."
    ],
    "bigtech_interview": "Что произойдет, если запустить `CREATE INDEX CONCURRENTLY` в момент, когда в базе висит забытая незакрытая транзакция `idle in transaction`? Построение индекса зависнет на этапе ожидания завершения транзакции и не завершится до тех пор, пока зависшее соединение не будет убито (`pg_terminate_backend`)."
})

# Ex 9: Паттерн безопасного переименования столбца (Rename Column)
code9 = r'''package main

import (
	"fmt"
)

// RenameColumnStep шаг процесса безопасного переименования столбца
type RenameColumnStep struct {
	StepNumber int
	Action     string
	SQL        string
	AppVersion string
	CanRollback bool
}

func GetRenameColumnLifecycle() []RenameColumnStep {
	return []RenameColumnStep{
		{
			StepNumber:  1,
			Action:      "Expand: Добавление новой колонки",
			SQL:         "ALTER TABLE users ADD COLUMN full_name TEXT NULL;",
			AppVersion:  "v1.0 (читает и пишет в 'name')",
			CanRollback: true,
		},
		{
			StepNumber:  2,
			Action:      "Dual Write: Релиз кода с двойной записью",
			SQL:         "Нет DDL изменений",
			AppVersion:  "v2.0 (пишет в 'name' И 'full_name', читает из 'name')",
			CanRollback: true,
		},
		{
			StepNumber:  3,
			Action:      "Backfill: Фоновое копирование исторических данных",
			SQL:         "UPDATE users SET full_name = name WHERE id BETWEEN ... AND full_name IS NULL;",
			AppVersion:  "v2.0 (Dual Write гарантирует целостность)",
			CanRollback: true,
		},
		{
			StepNumber:  4,
			Action:      "Switch Read: Переключение чтения",
			SQL:         "Нет DDL изменений",
			AppVersion:  "v3.0 (читает из 'full_name', пишет в 'name' И 'full_name')",
			CanRollback: true,
		},
		{
			StepNumber:  5,
			Action:      "Contract: Удаление старой колонки",
			SQL:         "ALTER TABLE users DROP COLUMN name;",
			AppVersion:  "v4.0 (пишет и читает только 'full_name')",
			CanRollback: false,
		},
	}
}

func main() {
	fmt.Println("Паттерн безопасного переименования столбца (Rename Column):")
	for _, s := range GetRenameColumnLifecycle() {
		fmt.Printf("\n[Этап %d] %s\n", s.StepNumber, s.Action)
		fmt.Printf(" Версия сервиса: %s\n", s.AppVersion)
		fmt.Printf(" SQL миграция:   %s (Откат возможен: %v)\n", s.SQL, s.CanRollback)
	}
}
'''
validate_go_code(code9, "code9")
exercises.append({
    "num": 9,
    "title": "Паттерн безопасного переименования столбца (Rename Column)",
    "task": "Изучите, почему простая операция RENAME COLUMN невозможна в HighLoad без даунтайма. Спроектируйте пятиэтапный процесс безопасного переименования столбца name в full_name по методологии Expand-Contract с сохранением возможности мгновенного отката на каждом этапе.",
    "theory": "Казалось бы, переименовать колонку просто: `ALTER TABLE users RENAME COLUMN name TO full_name;`.\nОднако в распределенной системе с Rolling Update это фатально:\n- В момент применения DDL старые поды v1 мгновенно падают с ошибкой `column \"name\" does not exist` при каждом SQL-запросе.\n- Если сначала обновить поды до v2, они упадут с ошибкой `column \"full_name\" does not exist`, потому что миграция еще не накатана.\n\nЕдинственный способ безопасного переименования без даунтайма — представить 'переименование' как добавление новой колонки + копирование данных + удаление старой через Expand-Contract.",
    "step_by_step": [
        "Проанализируйте взаимную несовместимость версий кода и схемы БД.",
        "Разбейте задачу переименования на 5 шагов: Expand -> Dual Write -> Backfill -> Switch Read -> Contract.",
        "Определите поведение слоя данных приложения на каждом шаге.",
        "Покажите, что на шагах 1–4 откат на предыдущую версию кода или БД безопасен и не приводит к потере данных."
    ],
    "code_blocks": [{
        "filename": "rename_column_lifecycle.go",
        "lang": "go",
        "code": code9
    }],
    "under_the_hood": "Альтернативным решением в PostgreSQL может быть создание `VIEW` с алиасом столбца или генерируемая колонка `GENERATED ALWAYS AS (name) STORED`, однако в высоконагруженных OLTP-системах явный Expand-Contract остается золотым стандартом надежности.",
    "pitfalls": [
        "Удаление старой колонки до обновления всех клиентов: если хотя бы один вспомогательный скрипт (ETL, аналитика, кэш-воркер) продолжает читать `name`, `DROP COLUMN` сломает его.",
        "Забытый Dual Write: если запустить Backfill без Dual Write, новые строки, созданные пользователями во время работы бэкфилла, останутся с пустым значением в новой колонке."
    ],
    "bigtech_interview": "Сколько релизов сервиса требуется для безопасного переименования одной колонки в проде? Ответ: минимум 3 независимых релиза приложения (v2 Dual Write, v3 Switch Read, v4 Cleanup) и 2 миграции БД (Expand и Contract)."
})

# Ex 10: Шаг 1 Expand: добавление нового столбца
code10 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
)

// UserRepositoryV1 представляет старую версию репозитория (v1)
type UserRepositoryV1 struct {
	db *sql.DB
}

func NewUserRepositoryV1(db *sql.DB) *UserRepositoryV1 {
	return &UserRepositoryV1{db: db}
}

// CreateUser создает пользователя, зная только старую колонку 'name'
func (r *UserRepositoryV1) CreateUser(ctx context.Context, id int64, name string) error {
	// Запрос жестко фиксирует перечень колонок (никогда не используйте SELECT * или INSERT без колонок!)
	query := `INSERT INTO users (id, name) VALUES ($1, $2);`
	_, err := r.db.ExecContext(ctx, query, id, name)
	return err
}

// GetUser считывает пользователя по ID
func (r *UserRepositoryV1) GetUser(ctx context.Context, id int64) (string, error) {
	query := `SELECT name FROM users WHERE id = $1;`
	var name string
	err := r.db.QueryRowContext(ctx, query, id).Scan(&name)
	return name, err
}

func main() {
	fmt.Println("Шаг 1 Expand: Добавление нового столбца full_name TEXT NULL:")
	fmt.Println(" 1. Выполняется миграция: ALTER TABLE users ADD COLUMN full_name TEXT NULL;")
	fmt.Println(" 2. Колонка обязана быть NULL (или иметь static default в PG 11+)")
	fmt.Println(" 3. Текущий код v1 продолжает стабильно работать, полностью игнорируя новую колонку")
	fmt.Println(" 4. Правило: явное перечисление столбцов в INSERT/SELECT исключает сбои при добавлении полей")
}
'''
validate_go_code(code10, "code10")
exercises.append({
    "num": 10,
    "title": "Шаг 1 Expand: добавление нового столбца",
    "task": "Реализуйте фазу 1 (Expand) паттерна: напишите SQL-миграцию добавления нового столбца full_name TEXT NULL и продемонстрируйте структуру UserRepositoryV1. Докажите, что при явном перечислении полей в SQL-запросах работающий сервис v1 не замечает добавления новой колонки в таблицу.",
    "theory": "Фаза Expand расширяет возможности базы данных, сохраняя полную обратную совместимость (Backward Compatibility) со старым кодом.\n\nКлючевые правила первого шага:\n1. Новый столбец ОБЯЗАН допускать значение `NULL` (`TEXT NULL`) либо иметь безопасное значение по умолчанию. Если попытаться сразу добавить `NOT NULL`, старый сервис v1 упадет на первом же `INSERT`, так как он ничего не знает о новой колонке и не передает для нее значение.\n2. В кодовой базе Go категорически запрещено использовать `SELECT * FROM users` и `INSERT INTO users VALUES (...)`. При добавлении столбца `SELECT *` сломает вызовы `rows.Scan(&id, &name)` из-за несовпадения числа столбцов. Всегда используйте явный перечень колонок: `SELECT id, name FROM users`.",
    "step_by_step": [
        "Сформируйте DDL-скрипт миграции добавления столбца full_name TEXT NULL.",
        "Реализуйте методы CreateUser и GetUser с явным указанием столбцов.",
        "Объясните, почему новый столбец не ломает активные запросы сервиса v1.",
        "Покажите опасность использования SELECT * при эволюции схемы."
    ],
    "code_blocks": [{
        "filename": "step1_expand_repository.go",
        "lang": "go",
        "code": code10
    }],
    "under_the_hood": "Добавление nullable столбца в PostgreSQL происходит исключительно на уровне системного каталога: создается новая запись в `pg_attribute`, а физические страницы данных таблицы не модифицируются. Операция занимает менее 1 мс независимо от объема таблицы.",
    "pitfalls": [
        "Использование `SELECT *`: добавление столбца приведет к ошибке `sql: expected 2 destination arguments in Scan, got 3` в Go.",
        "Забытый `NULL`: попытка добавить `full_name TEXT NOT NULL` без дефолта вызовет немедленный отказ во всех операциях `INSERT` старого сервиса."
    ],
    "bigtech_interview": "Как статический анализатор кода (Linter) может предотвратить проблемы при миграциях? В BigTech используют линтеры, запрещающие использование `SELECT *` в SQL-запросах на уровне сборки CI/CD (например, правила golangci-lint)."
})

# Ex 11: Шаг 2 Dual Write: двойная запись в Go-коде
code11 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
)

// UserRepositoryV2 реализует шаг 2 (Dual Write): одновременная запись в старую и новую колонки
type UserRepositoryV2 struct {
	db *sql.DB
}

func NewUserRepositoryV2(db *sql.DB) *UserRepositoryV2 {
	return &UserRepositoryV2{db: db}
}

// CreateUser выполняет двойную запись (Dual Write) в одном атомарном SQL-запросе
func (r *UserRepositoryV2) CreateUser(ctx context.Context, id int64, fullName string) error {
	// Записываем одно и то же значение И в name, И в full_name!
	query := `INSERT INTO users (id, name, full_name) VALUES ($1, $2, $2);`
	_, err := r.db.ExecContext(ctx, query, id, fullName)
	return err
}

// UpdateUser обновляет обе колонки синхронно
func (r *UserRepositoryV2) UpdateUser(ctx context.Context, id int64, newFullName string) error {
	query := `UPDATE users SET name = $1, full_name = $1 WHERE id = $2;`
	_, err := r.db.ExecContext(ctx, query, newFullName, id)
	return err
}

// GetUser на шаге Dual-Write по-прежнему читает из СТАРОЙ колонки name
func (r *UserRepositoryV2) GetUser(ctx context.Context, id int64) (string, error) {
	query := `SELECT name FROM users WHERE id = $1;`
	var name string
	err := r.db.QueryRowContext(ctx, query, id).Scan(&name)
	return name, err
}

func main() {
	fmt.Println("Шаг 2 Dual Write: двойная запись в Go-коде:")
	fmt.Println(" 1. Релиз версии сервиса v2")
	fmt.Println(" 2. При создании и обновлении данные пишутся ОДНОВРЕМЕННО в name и full_name")
	fmt.Println(" 3. Чтение по-прежнему идет из старой колонки name")
	fmt.Println(" 4. Гарантирует: все новые и измененные строки с этого момента актуальны в обеих колонках!")
}
'''
validate_go_code(code11, "code11")
exercises.append({
    "num": 11,
    "title": "Шаг 2 Dual Write: двойная запись в Go-коде",
    "task": "Реализуйте фазу 2 (Dual Write) паттерна в коде репозитория UserRepositoryV2. Обеспечьте одновременную атомарную запись значения в старый столбец name и новый full_name в одном SQL-запросе INSERT и UPDATE, сохраняя чтение из старого столбца.",
    "theory": "После того как новая колонка успешно добавлена в базу (Шаг 1), выкатывается версия сервиса v2.\n\nСуть Dual Write (Двойной записи):\n1. Все новые операции модификации данных (`INSERT`, `UPDATE`) пишут данные сразу в оба столбца (`INSERT INTO users (id, name, full_name) VALUES ($1, $2, $2)`).\n2. Чтение по-прежнему производится из старого столбца `name`.\n\nЗачем это нужно?\nС момента релиза версии v2 все вновь создаваемые и обновляемые пользователями строки автоматически содержат актуальные данные в новом столбце. Это позволяет безопасно запустить фоновый перенос исторических данных (Backfill), не опасаясь, что новые записи потеряются.",
    "step_by_step": [
        "Создайте структуру UserRepositoryV2 с подключением к БД.",
        "В методе CreateUser измените запрос на одновременную запись в name и full_name.",
        "В методе UpdateUser обновите обе колонки одновременно.",
        "Убедитесь, что метод GetUser по-прежнему считывает данные из name.",
        "Объясните, почему запись в оба столбца в рамках одного SQL-вызова исключает race conditions."
    ],
    "code_blocks": [{
        "filename": "step2_dual_write_repository.go",
        "lang": "go",
        "code": code11
    }],
    "under_the_hood": "Выполнение записи в оба столбца в рамках единого SQL-запроса `INSERT ... VALUES ($1, $2, $2)` гарантирует 100% атомарность на уровне ядра базы данных без накладных расходов на сетевые вызовы и двухфазные коммиты.",
    "pitfalls": [
        "Раздельные запросы: выполнение сначала `INSERT INTO ... (name)`, а затем отдельного `UPDATE ... SET full_name` создает окно несогласованности и удваивает нагрузку на БД.",
        "Переключение чтения раньше времени: нельзя переключать чтение на `full_name` на шаге 2, так как исторические строки еще не скопированы и содержат `NULL`."
    ],
    "bigtech_interview": "Что произойдет, если на этапе Dual-Write потребуется срочно откатить сервис v2 назад на v1? Откат абсолютно безопасен! Старый сервис v1 просто продолжит читать и писать в `name`, а колонка `full_name` останется нетронутой."
})

# Ex 12: Шаг 3 Backfill: фоновый перенос исторических данных
code12 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
	"time"
)

// HistoricalBackfiller копирует данные из старой колонки в новую
type HistoricalBackfiller struct {
	db        *sql.DB
	batchSize int
}

func NewHistoricalBackfiller(db *sql.DB, batchSize int) *HistoricalBackfiller {
	return &HistoricalBackfiller{db: db, batchSize: batchSize}
}

// MigrateLegacyBatch переносит одну пачку записей
func (b *HistoricalBackfiller) MigrateLegacyBatch(ctx context.Context) (int64, error) {
	// Копируем данные только для тех строк, где full_name еще не заполнен
	query := `
		UPDATE users
		SET full_name = name
		WHERE id IN (
			SELECT id FROM users
			WHERE full_name IS NULL
			ORDER BY id ASC
			LIMIT $1
		);
	`

	res, err := b.db.ExecContext(ctx, query, b.batchSize)
	if err != nil {
		return 0, fmt.Errorf("ошибка выполнения батча бэкфилла: %w", err)
	}

	rowsAffected, _ := res.RowsAffected()
	return rowsAffected, nil
}

func main() {
	fmt.Println("Шаг 3 Backfill: фоновый перенос исторических данных:")
	fmt.Println(" 1. Записи, созданные до релиза Dual Write, содержат full_name = NULL")
	fmt.Println(" 2. Фоновый воркер переносит данные небольшими порциями (батчами)")
	fmt.Println(" 3. Не блокирует боевые транзакции пользователей")
}
'''
validate_go_code(code12, "code12")
exercises.append({
    "num": 12,
    "title": "Шаг 3 Backfill: фоновый перенос исторических данных",
    "task": "Спроектируйте базовый фоновый воркер HistoricalBackfiller для копирования данных из старого столбца name в новый full_name для строк, созданных до внедрения Dual Write. Реализуйте пакетную обработку через подзапрос с LIMIT $1.",
    "theory": "После развертывания Dual Write в базе данных сосуществуют два типа строк:\n1. Новые строки: заполнены и `name`, и `full_name`.\n2. Старые исторические строки: заполнен только `name`, а `full_name IS NULL`.\n\nПроцесс Backfill (Бэкфилл):\nСпециальный скрипт на Go в фоновом режиме находит строки, где `full_name IS NULL`, и копирует значение из `name`.\n\nГлавное архитектурное требование к бэкфиллу в HighLoad — батчинг (Batching):\nКатегорически запрещено выполнять один гигантский запрос `UPDATE users SET full_name = name WHERE full_name IS NULL;`. На миллионах строк это заблокирует строки таблицы, переполнит WAL-лог репликации и вызовет каскадный отказ. Бэкфилл выполняется небольшими порциями (батчами по 500–5 000 строк).",
    "step_by_step": [
        "Создайте структуру HistoricalBackfiller с параметром batchSize.",
        "Сформируйте SQL-запрос обновления с фильтрацией WHERE full_name IS NULL и LIMIT $1.",
        "Вызовите ExecContext с замером rowsAffected.",
        "Покажите, как батчинг предотвращает раздувание транзакционного журнала СУБД."
    ],
    "code_blocks": [{
        "filename": "step3_basic_backfiller.go",
        "lang": "go",
        "code": code12
    }],
    "under_the_hood": "Каждый отдельный вызов `UPDATE ... LIMIT N` выполняется в своей собственной отдельной короткой транзакции. Строки блокируются только на 5–10 миллисекунд, после чего блокировки снимаются, позволяя пользователям работать без задержек.",
    "pitfalls": [
        "Медленный подзапрос с `ORDER BY id LIMIT N`: если по колонке `full_name` нет индекса, поиск `WHERE full_name IS NULL` будет выполнять последовательный скан (Seq Scan) всей таблицы на каждом батче! Как оптимизировать это через Keyspace Chunking, разберем в упражнении 13.",
        "Бесконечный цикл: если в таблице есть строки, где `name IS NULL`, запрос будет выбирать их снова и снова."
    ],
    "bigtech_interview": "Почему бэкфилл лучше делать на уровне прикладного Go-скрипта, а не одного фонового скрипта в `psql`? Go-скрипт имеет доступ к контексту, метрикам лага репликации, может плавно регулировать паузы и корректно реагировать на сигналы завершения `SIGTERM` в Kubernetes."
})

# Ex 13: Потоковый бэкфилл порциями по первичному ключу (Chunking)
code13 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
	"time"
)

// ChunkedBackfiller переносит данные диапазонами первичного ключа
type ChunkedBackfiller struct {
	db        *sql.DB
	chunkSize int64
}

func NewChunkedBackfiller(db *sql.DB, chunkSize int64) *ChunkedBackfiller {
	return &ChunkedBackfiller{db: db, chunkSize: chunkSize}
}

// RunChunkedBackfill сканирует диапазон ID от minID до maxID
func (b *ChunkedBackfiller) RunChunkedBackfill(ctx context.Context, minID, maxID int64) error {
	fmt.Printf("[CHUNK BACKFILL] Старт переноса по первичному ключу [%d ... %d] чанками по %d строк\n",
		minID, maxID, b.chunkSize)

	currentID := minID

	for currentID <= maxID {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}

		endID := currentID + b.chunkSize - 1
		start := time.Now()

		// Запрос использует B-Tree индекс первичного ключа: O(log N) поиск диапазона!
		query := `
			UPDATE users
			SET full_name = name
			WHERE id >= $1 AND id <= $2 AND full_name IS NULL;
		`

		res, err := b.db.ExecContext(ctx, query, currentID, endID)
		if err != nil {
			return fmt.Errorf("ошибка обработки чанка [%d-%d]: %w", currentID, endID, err)
		}

		affected, _ := res.RowsAffected()
		elapsed := time.Since(start)

		fmt.Printf(" 📦 Чанк ID [%10d - %10d] -> обновлено: %4d строк за %v\n",
			currentID, endID, affected, elapsed)

		// Пауза (Джиттер) для разгрузки репликации и I/O диска
		time.Sleep(20 * time.Millisecond)
		currentID = endID + 1
	}

	fmt.Println("✅ [CHUNK BACKFILL] Фоновый перенос всех данных успешно завершен!")
	return nil
}

func main() {
	fmt.Println("Потоковый бэкфилл порциями по первичному ключу (Keyspace Chunking):")
	fmt.Println(" 1. Вместо WHERE full_name IS NULL используем сканирование по первичному ключу id")
	fmt.Println(" 2. WHERE id >= $1 AND id <= $2 использует индекс Primary Key с нулевым оверхедом")
	fmt.Println(" 3. Исключает медленные Sequential Scan на больших таблицах")
}
'''
validate_go_code(code13, "code13")
exercises.append({
    "num": 13,
    "title": "Потоковый бэкфилл порциями по первичному ключу (Chunking)",
    "task": "Оптимизируйте перенос данных с помощью техники Keyspace Chunking (пагинация по первичному ключу). Реализуйте метод RunChunkedBackfill, сканирующий диапазоны WHERE id >= $1 AND id <= $2 с использованием индекса первичного ключа, контролируя время выполнения одного чанка (< 100 мс).",
    "theory": "Запрос `WHERE full_name IS NULL LIMIT 1000` плох тем, что по мере выполнения бэкфилла строк с `NULL` становится все меньше. Базе данных приходится просканировать миллионы записей, чтобы найти очередную тысячу незаполненных строк, что приводит к деградации дискового I/O.\n\nТехника Keyspace Chunking (Чанкование по первичному ключу):\n1. Узнаем минимальный и максимальный ID: `SELECT min(id), max(id) FROM users`.\n2. Итерируемся фиксированными окнами ID: `[1..5000]`, `[5001..10000]`, `[10001..15000]`.\n3. Запрос: `UPDATE users SET full_name = name WHERE id >= :start AND id <= :end AND full_name IS NULL`.\n4. Благодаря B-Tree индексу по первичному ключу `id`, база данных мгновенно находит нужный диапазон страниц за константное время `O(log N)`.",
    "step_by_step": [
        "Создайте ChunkedBackfiller с параметром размера чанка chunkSize.",
        "Реализуйте цикл от minID до maxID с шагом chunkSize.",
        "Сформируйте запрос обновления с фильтром по диапазону id >= $1 AND id <= $2.",
        "Замеряйте задержку выполнения каждого чанка через time.Since(start).",
        "Добавьте паузу time.Sleep между чанками для предотвращения перегрева CPU базы."
    ],
    "code_blocks": [{
        "filename": "chunked_keyspace_backfiller.go",
        "lang": "go",
        "code": code13
    }],
    "under_the_hood": "При чанковании размер одного окна выбирается так, чтобы выполнение `UPDATE` занимало не более 50–100 мс. Это гарантирует, что автовакуум PostgreSQL (autovacuum) успевает очищать мертвые версии строк (Dead Tuples), предотвращая раздувание таблицы (Table Bloat).",
    "pitfalls": [
        "Дырки в последовательности ID: если в таблице много удаленных записей (например, ID идут `1, 1000000`), часть чанков будет обрабатывать 0 строк — это нормально и работает молниеносно.",
        "Составные первичные ключи: если первичный ключ составной `(tenant_id, user_id)`, чанкование усложняется и требует использования кортежного сравнения `(tenant_id, user_id) > ($1, $2)`."
    ],
    "bigtech_interview": "Почему при чанковании нельзя использовать `OFFSET / LIMIT`? `OFFSET 10000000` заставляет базу данных прочитать и отбросить 10 миллионов строк в памяти, деградируя производительность до нуля. Пагинация по первичному ключу (Keyset Pagination) свободна от этой проблемы."
})

# Ex 14: Динамический троттлинг фонового бэкфилла
code14 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
	"time"
)

// DBHealthChecker опрашивает метрики нагрузки СУБД
type DBHealthChecker interface {
	GetActiveConnections(ctx context.Context) (int, error)
	GetReplicationLagSeconds(ctx context.Context) (float64, error)
}

// ThrottledBackfiller адаптирует скорость работы к нагрузке базы данных
type ThrottledBackfiller struct {
	db           *sql.DB
	health       DBHealthChecker
	maxConns     int
	maxReplLag   float64
	baseSleep    time.Duration
	currentSleep time.Duration
}

func NewThrottledBackfiller(db *sql.DB, health DBHealthChecker) *ThrottledBackfiller {
	return &ThrottledBackfiller{
		db:           db,
		health:       health,
		maxConns:     80,  // Порог активных соединений
		maxReplLag:   1.0, // Максимальный лаг репликации: 1 секунда
		baseSleep:    20 * time.Millisecond,
		currentSleep: 20 * time.Millisecond,
	}
}

// Throttle проверяет метрики и динамически регулирует задержку
func (b *ThrottledBackfiller) Throttle(ctx context.Context) {
	conns, err := b.health.GetActiveConnections(ctx)
	if err != nil {
		return
	}

	lag, err := b.health.GetReplicationLagSeconds(ctx)
	if err != nil {
		return
	}

	// Если нагрузка или отставание реплик растет — замедляем бэкфилл
	if conns > b.maxConns || lag > b.maxReplLag {
		b.currentSleep = min(b.currentSleep*2, 2*time.Second)
		fmt.Printf("⚠️ [THROTTLE ON] Нагрузка высока (Conns=%d, Lag=%.2fs)! Пауза увеличена до %v\n",
			conns, lag, b.currentSleep)
	} else if b.currentSleep > b.baseSleep {
		// Постепенное ускорение при нормализации метрик
		b.currentSleep = max(b.currentSleep/2, b.baseSleep)
	}

	time.Sleep(b.currentSleep)
}

func min(a, b time.Duration) time.Duration {
	if a < b {
		return a
	}
	return b
}

func max(a, b time.Duration) time.Duration {
	if a > b {
		return a
	}
	return b
}

func main() {
	fmt.Println("Динамический троттлинг фонового бэкфилла (Adaptive Throttling):")
	fmt.Println(" 1. Перед каждым чанком опрашиваются метрики pg_stat_activity и pg_stat_replication")
	fmt.Println(" 2. При росте лага репликации > 1.0s скорость бэкфилла автоматически снижается")
	fmt.Println(" 3. Фоновая миграция НИКОГДА не конкурирует с реальными покупками пользователей")
}
'''
validate_go_code(code14, "code14")
exercises.append({
    "num": 14,
    "title": "Динамический троттлинг фонового бэкфилла",
    "task": "Реализуйте механизм адаптивного троттлинга ThrottledBackfiller. Перед обработкой каждого чанка сервис опрашивает число активных соединений и лаг репликации (pg_stat_replication). При превышении порогов задержка между батчами экспоненциально увеличивается, защищая прод от деградации.",
    "theory": "Фоновый перенос данных не должен конкурировать с пользовательским трафиком за ресурсы процессора, диска и сети репликации.\n\nДва главных фактора риска при бэкфилле:\n1. Конкуренция за I/O диска: при всплеске дневного трафика бэкфилл может забить диск, увеличив p99 latency пользовательских запросов.\n2. Отставание реплик (Replication Lag): активная генерация WAL-логов при массовых `UPDATE` приводит к тому, что read-реплики начинают отставать от мастера на десятки секунд. Пользователи видят устаревшие данные.\n\nАдаптивный троттлинг (Adaptive Throttling):\nБэкфиллер непрерывно опрашивает телеметрию БД. Если лаг репликации превышает 1 секунду, скрипт автоматически увеличивает задержку `time.Sleep` с 20 мс до 2 секунд, давая репликам догнать мастер.",
    "step_by_step": [
        "Определите интерфейс DBHealthChecker с методами проверки соединений и лага репликации.",
        "Создайте ThrottledBackfiller с базовым и текущим временем задержки currentSleep.",
        "Реализуйте метод Throttle: при превышении порогов удваивайте задержку (до 2 секунд).",
        "При нормализации метрик плавно уменьшайте задержку до baseSleep.",
        "Вызывайте Throttle между обработкой соседних чанков."
    ],
    "code_blocks": [{
        "filename": "adaptive_throttling_backfill.go",
        "lang": "go",
        "code": code14
    }],
    "under_the_hood": "В PostgreSQL запрос к представлению `pg_stat_replication` возвращает поле `replay_lag` — точное физическое отставание применения WAL-блоков на реплике. Опрос занимает доли миллисекунды и безопасен для вызова в цикле.",
    "pitfalls": [
        "Слишком агрессивный троттлинг: если порог лага выставлен в `10ms`, скрипт может встать на паузу навсегда. Порог должен учитывать естественный сетевой джиттер (обычно 0.5–2 секунды).",
        "Отсутствие проверки контекста: во время долгого сна `time.Sleep(2*time.Second)` скрипт должен проверять `ctx.Done()`, чтобы корректно останавливаться при `SIGTERM`."
    ],
    "bigtech_interview": "Как в GitHub и Shopify автоматизируют бэкфиллы петабайтных баз данных? Используются инструменты вроде `gh-ost` или `pt-online-schema-change`, которые имеют встроенный адаптивный throttling по метрикам `Threads_running` и replication delay."
})

# Ex 15: Шаг 4 Switch Read: переключение чтения на новую колонку
code15 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
)

// UserRepositoryV3 реализует шаг 4 (Switch Read): чтение из нового столбца, сохранение Dual Write
type UserRepositoryV3 struct {
	db *sql.DB
}

func NewUserRepositoryV3(db *sql.DB) *UserRepositoryV3 {
	return &UserRepositoryV3{db: db}
}

// GetUser ТЕПЕРЬ ЧИТАЕТ ИЗ НОВОГО СТОЛБЦА full_name!
func (r *UserRepositoryV3) GetUser(ctx context.Context, id int64) (string, error) {
	// Переключение чтения: данные на 100% скопированы и проверены
	query := `SELECT full_name FROM users WHERE id = $1;`
	var fullName string
	err := r.db.QueryRowContext(ctx, query, id).Scan(&fullName)
	return fullName, err
}

// CreateUser по-прежнему пишет в ОБА столбца для безопасного отката
func (r *UserRepositoryV3) CreateUser(ctx context.Context, id int64, fullName string) error {
	query := `INSERT INTO users (id, name, full_name) VALUES ($1, $2, $2);`
	_, err := r.db.ExecContext(ctx, query, id, fullName)
	return err
}

// UpdateUser также сохраняет двойную запись
func (r *UserRepositoryV3) UpdateUser(ctx context.Context, id int64, newFullName string) error {
	query := `UPDATE users SET name = $1, full_name = $1 WHERE id = $2;`
	_, err := r.db.ExecContext(ctx, query, newFullName, id)
	return err
}

func main() {
	fmt.Println("Шаг 4 Switch Read: переключение чтения на новую колонку:")
	fmt.Println(" 1. Релиз версии сервиса v3")
	fmt.Println(" 2. Метод GetUser переключен на чтение из full_name")
	fmt.Println(" 3. Двойная запись (Dual Write) СОХРАНЯЕТСЯ в коде!")
	fmt.Println(" 4. Если в v3 обнаружится баг, мгновенный откат на v2 безопасен (колонка name актуальна)")
}
'''
validate_go_code(code15, "code15")
exercises.append({
    "num": 15,
    "title": "Шаг 4 Switch Read: переключение чтения на новую колонку",
    "task": "Реализуйте фазу 4 (Switch Read) в репозитории UserRepositoryV3. Переключите чтение метода GetUser на новый столбец full_name, обязательно сохранив двойную запись (Dual Write) в методы CreateUser и UpdateUser для обеспечения мгновенного отката в случае выявления скрытых дефектов.",
    "theory": "После того как фоновый Backfill завершился и проверка целостности показала 0 строк с `full_name IS NULL`, наступает момент переключения чтения (Switch Read):\n\n1. Выкатывается версия приложения v3.\n2. Все операции `SELECT` переключаются на чтение из нового столбца `full_name`.\n3. КРИТИЧЕСКИ ВАЖНО: операции записи (`INSERT`, `UPDATE`) ПО-ПРЕЖНЕМУ пишут в ОБА столбца (`name` и `full_name`)!\n\nПочему нельзя сразу отключить запись в старый столбец?\nЕсли в коде версии v3 обнаружится критический баг (например, некорректная логика в другом месте) и дежурный инженер откатит сервис назад на v2, старый сервис начнет читать из `name`. Если бы мы отключили запись в `name`, все данные, созданные за время работы v3, были бы потеряны для v2!",
    "step_by_step": [
        "Создайте структуру UserRepositoryV3.",
        "В методе GetUser замените запрос на SELECT full_name FROM users WHERE id = $1.",
        "В методах CreateUser и UpdateUser оставьте двойную запись без изменений.",
        "Объясните концепцию симметричной готовности к откату (Rollback Readiness)."
    ],
    "code_blocks": [{
        "filename": "step4_switch_read_repository.go",
        "lang": "go",
        "code": code15
    }],
    "under_the_hood": "На этапе Switch Read база данных работает под минимальной нагрузкой: чтение идет из нового столбца, план запроса использует те же B-Tree индексы, а запись остается полностью симметричной.",
    "pitfalls": [
        "Отключение Dual Write одновременно со Switch Read: самая частая ошибка. При аварийном откате новые записи не будут видны старой версии сервиса, вызвав повреждение целостности бизнес-данных.",
        "Отсутствие верификации перед переключением: если запустить Switch Read, пока Backfill дошел только до 95%, оставшиеся 5% пользователей получат пустые имена."
    ],
    "bigtech_interview": "Сколько времени рекомендуется выдерживать систему в состоянии Switch Read с активным Dual Write перед переходом к Contract? В ведущих компаниях (Ozon, Stripe) этот период составляет от 3 до 7 дней, чтобы убедиться в стабильности на всех типах недельной нагрузки."
})

# Save Part 1
out_path = '/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch96_p1.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Chapter 96 Part 1 generated successfully: {len(exercises)} exercises.")
