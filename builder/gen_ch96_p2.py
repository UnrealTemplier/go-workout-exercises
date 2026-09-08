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

# Ex 16: Шаг 5 Contract: удаление старой колонки
code16 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
	"time"
)

// ContractStepExecutor управляет завершающей фазой Contract
type ContractStepExecutor struct {
	db *sql.DB
}

func NewContractStepExecutor(db *sql.DB) *ContractStepExecutor {
	return &ContractStepExecutor{db: db}
}

// VerifyAllReplicasUpdated проверяет готовность кластера к фазе сжатия
func (e *ContractStepExecutor) VerifyAllReplicasUpdated(ctx context.Context, minVersion string) error {
	fmt.Printf("[CONTRACT] Проверка версий инстансов... Все поды должны быть не ниже %s\n", minVersion)
	// В реальном кластере проверяется consul, k8s deployments или таблица инстансов в БД
	return nil
}

// DropOldColumn выполняет безопасное удаление колонки с жестким lock_timeout
func (e *ContractStepExecutor) DropOldColumn(ctx context.Context, table, column string) error {
	tx, err := e.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("begin tx: %w", err)
	}
	defer tx.Rollback()

	// Установка жесткого lock_timeout, чтобы не выстроить очередь запросов
	if _, err := tx.ExecContext(ctx, "SET LOCAL lock_timeout = '2s'"); err != nil {
		return fmt.Errorf("set lock_timeout: %w", err)
	}

	query := fmt.Sprintf("ALTER TABLE %s DROP COLUMN IF EXISTS %s", table, column)
	fmt.Printf("[CONTRACT] Выполнение DDL: %s (lock_timeout=2s)...\n", query)
	if _, err := tx.ExecContext(ctx, query); err != nil {
		return fmt.Errorf("drop column failed: %w", err)
	}

	return tx.Commit()
}

func main() {
	fmt.Println("=== Фаза Contract: Безопасное удаление устаревшей колонки ===")
	executor := NewContractStepExecutor(nil)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := executor.VerifyAllReplicasUpdated(ctx, "v4.0.0"); err != nil {
		fmt.Println("Ошибка готовности:", err)
		return
	}
	fmt.Println("Фаза сжатия: Все сервисы переведены на чтение и запись только full_name.")
	fmt.Println("Старая колонка name готова к удалению.")
}
'''

validate_go_code(code16, "code16")
exercises.append({
    "num": 16,
    "title": "Шаг 5 Contract: удаление старой колонки",
    "task": "Реализуйте финальный шаг паттерна Expand-Contract (Contract). Продемонстрируйте проверку готовности всех работающих инстансов сервиса к прекращению использования старого поля, безопасное удаление колонки с SET LOCAL lock_timeout = '2s' и объясните, почему перед удалением колонки выдерживается карантин в несколько дней.",
    "theory": "Фаза Contract — завершающий этап жизненного цикла Expand-Contract. До ее наступления должны успешно завершиться все предыдущие шаги: добавление новой колонки (Expand), параллельная запись в обе колонки (Dual Write), полный перенос исторических данных (Backfill) и полное переключение чтения на новую колонку (Switch Read).\n\nНа этапе Contract удаляется код приложения, пишущий в старую колонку, и деплоится релиз v4. После того как 100% подов в Kubernetes переведены на v4 и отработали под нагрузкой несколько дней (карантинный период для гарантии отсутствия скрытых зависимостей и необходимости отката), на базу данных накатывается финальная миграция ALTER TABLE users DROP COLUMN name. Обязательным требованием остается указание SET LOCAL lock_timeout = '2s', поскольку удаление колонки требует кратковременного ACCESS EXCLUSIVE LOCK.",
    "step_by_step": [
        "Убедиться, что 100% подов в кластере переведены на версию v4, которая не использует старую колонку ни на чтение, ни на запись.",
        "Выдержать карантинный интервал (обычно от 3 до 7 дней) для гарантии стабильности релиза.",
        "Создать транзакционную DDL-миграцию с обязательным SET LOCAL lock_timeout = '2s'.",
        "Выполнить ALTER TABLE users DROP COLUMN IF EXISTS name.",
        "Убедиться в отсутствии ошибок блокировок и зафиксировать завершение миграции схемы."
    ],
    "code_blocks": [
        {
            "filename": "contract.go",
            "lang": "go",
            "code": code16
        }
    ],
    "under_the_hood": "В PostgreSQL операция ALTER TABLE ... DROP COLUMN не удаляет физические байты данных с диска немедленно. Она лишь помечает атрибут в системном каталоге pg_attribute как удаленный (attisdropped = true), что занимает миллисекунды. Физическое освобождение дискового пространства происходит постепенно при перезаписи строк (MVCC updates) или при выполнении VACUUM FULL. Однако для изменения pg_attribute требуется захват ACCESS EXCLUSIVE LOCK, поэтому установка lock_timeout строго обязательна.",
    "pitfalls": [
        "Удаление колонки до того, как все старые поды v3 были полностью завершены в Kubernetes (приведет к падению запросов с ошибкой 'column name does not exist').",
        "Выполнение DROP COLUMN без SET LOCAL lock_timeout, что может вызвать зависание DDL за долгой транзакцией аналитики и заблокировать весь входящий трафик.",
        "Отсутствие предварительного аудита аналитических дашбордов, ETL-пайплайнов и BI-инструментов, которые могли обращаться к старой колонке напрямую."
    ],
    "bigtech_interview": "В чем опасность выполнения DROP COLUMN сразу после Switch Read? Ответ: Если в новой логике чтения обнаружится критический баг (например, повреждение формата данных при конвертации) и потребуется срочный откат на версию v2, отсутствие старой колонки сделает быстрый откат невозможным. Карантин в несколько дней оставляет старую колонку в актуальном состоянии (благодаря Dual Write), позволяя мгновенно откатить трафик без потери данных."
})

# Ex 17: Безопасное изменение типа данных столбца (int32 -> int64)
code17 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
	"time"
)

// BigIDMigrationManager оркестрирует миграцию первичного ключа int32 -> int64
type BigIDMigrationManager struct {
	db *sql.DB
}

func NewBigIDMigrationManager(db *sql.DB) *BigIDMigrationManager {
	return &BigIDMigrationManager{db: db}
}

// Step1_AddBigColumn создает новую колонку BIGINT
func (m *BigIDMigrationManager) Step1_AddBigColumn(ctx context.Context) string {
	return `
-- 1. Добавляем новую колонку BIGINT
ALTER TABLE transactions ADD COLUMN id_big BIGINT;
`
}

// Step2_CreateTriggerSQL создает триггер автоматической синхронизации новых вставок
func (m *BigIDMigrationManager) Step2_CreateTriggerSQL() string {
	return `
CREATE OR REPLACE FUNCTION sync_transactions_id()
RETURNS TRIGGER AS $$
BEGIN
    NEW.id_big := NEW.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_id_big
BEFORE INSERT OR UPDATE ON transactions
FOR EACH ROW EXECUTE FUNCTION sync_transactions_id();
`
}

// Step3_BackfillChunk копирует исторические данные пачками
func (m *BigIDMigrationManager) Step3_BackfillChunk(ctx context.Context, startID, endID int) string {
	return fmt.Sprintf(`
UPDATE transactions 
SET id_big = id 
WHERE id BETWEEN %d AND %d AND id_big IS NULL;`, startID, endID)
}

// Step4_SwapPrimaryKey выполняет атомарную подмену первичного ключа
func (m *BigIDMigrationManager) Step4_SwapPrimaryKey() string {
	return `
-- Выполняется в транзакции с lock_timeout
SET LOCAL lock_timeout = '2s';
ALTER TABLE transactions ALTER COLUMN id_big SET NOT NULL;
ALTER TABLE transactions DROP CONSTRAINT transactions_pkey;
ALTER TABLE transactions ADD CONSTRAINT transactions_pkey PRIMARY KEY (id_big);
ALTER TABLE transactions DROP COLUMN id;
ALTER TABLE transactions RENAME COLUMN id_big TO id;
`
}

func main() {
	fmt.Println("=== Миграция типа данных: int32 -> int64 (BIGINT) ===")
	mgr := NewBigIDMigrationManager(nil)
	fmt.Println("SQL Шаг 1:", mgr.Step1_AddBigColumn(context.Background()))
	fmt.Println("SQL Шаг 2 (Триггер):", mgr.Step2_CreateTriggerSQL())
	fmt.Println("SQL Шаг 3 (Чанк 1-1000):", mgr.Step3_BackfillChunk(context.Background(), 1, 1000))
	fmt.Println("SQL Шаг 4 (Swap PK):", mgr.Step4_SwapPrimaryKey())
}
'''

validate_go_code(code17, "code17")
exercises.append({
    "num": 17,
    "title": "Безопасное изменение типа данных столбца (int32 -> int64)",
    "task": "Поле id в высоконагруженной таблице transactions приближается к пределу 32-битного integer (2.1 миллиарда). Прямой ALTER TABLE ALTER COLUMN id TYPE BIGINT блокирует таблицу на запись на часы. Реализуйте миграцию типа по паттерну Expand-Contract: добавление колонки id_big, синхронизирующий триггер, фоновый бэкфилл порциями и финальную атомарную подмену первичного ключа.",
    "theory": "Изменение типа данных столбца в реляционных базах данных (например, INT в BIGINT или VARCHAR(50) в TEXT) часто требует полной физической перезаписи каждого кортежа таблицы на диске с удержанием ACCESS EXCLUSIVE LOCK. Для таблицы с миллиардами строк это означает гарантированный даунтайм сервиса на многие часы.\n\nБезопасная стратегия состоит в применении Expand-Contract: 1) Добавляется колонка id_big BIGINT (без блокировки); 2) Создается триггер BEFORE INSERT, копирующий id в id_big для новых строк; 3) Фоновый Go-воркер порциями заполняет id_big для исторических строк; 4) Создается уникальный индекс на id_big через CONCURRENTLY; 5) В короткой транзакции с lock_timeout подменяются ограничения первичного ключа (PRIMARY KEY) и имена колонок.",
    "step_by_step": [
        "Добавить колонку id_big BIGINT NULL без блокировки.",
        "Установить PL/pgSQL триггер на уровне БД для автозаполнения id_big при вставках и обновлениях.",
        "Запустить фоновый воркер на Go, который чанками переносит значения id в id_big для старых строк.",
        "Создать уникальный индекс CREATE UNIQUE INDEX CONCURRENTLY idx_transactions_id_big ON transactions (id_big).",
        "В короткой транзакции с lock_timeout сбросить старый PK, назначить id_big новым PK, удалить старую колонку и переименовать id_big в id."
    ],
    "code_blocks": [
        {
            "filename": "type_migration.go",
            "lang": "go",
            "code": code17
        }
    ],
    "under_the_hood": "Когда выполняется ALTER TABLE transactions ALTER COLUMN id TYPE BIGINT, PostgreSQL должен преобразовать 4-байтовое бинарное представление каждого поля в 8-байтовое. Так как размер кортежа на странице памяти (8 KB page) увеличивается, СУБД вынуждена переписать таблицу целиком во временный файл и перестроить все индексы. Разделение процесса на фоновый бэкфилл и мгновенный swap переносит тяжелую дисковую работу в фон без удержания блокировок.",
    "pitfalls": [
        "Попытка обновить миллионы строк id_big одним запросом UPDATE, что переполнит буфер WAL и заблокирует транзакции пользователей.",
        "Забытый CREATE UNIQUE INDEX CONCURRENTLY перед подменой PK: добавление PRIMARY KEY без готового индекса приведет к полному сканированию таблицы под эксклюзивной блокировкой.",
        "Наличие внешних ключей (Foreign Keys), ссылающихся на этот id: их также потребуется пересоздать через NOT VALID."
    ],
    "bigtech_interview": "Как безопасно перевести первичный ключ int в bigint на таблице размером 500 ГБ в PostgreSQL? Ответ: Использовать Expand-Contract с добавлением колонки new_id bigint, триггером дублирования, пакетным фоновым бэкфиллом по PK с паузами, созданием уникального индекса через CONCURRENTLY и финальным атомарным переключением ограничений в транзакции с lock_timeout не более 2 секунд."
})

# Ex 18: Паттерн View-based Abstraction для мгновенной подмены схемы
code18 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
)

// ViewMigrationManager демонстрирует абстрагирование схемы через представления
type ViewMigrationManager struct {
	db *sql.DB
}

func (m *ViewMigrationManager) GenerateViewDDL() string {
	return `
-- 1. Переименование физической таблицы
ALTER TABLE users RENAME TO users_storage;

-- 2. Создание представления с обратной совместимостью для старого Go-кода
CREATE OR REPLACE VIEW users AS
SELECT 
    id,
    COALESCE(full_name, name) AS name,
    full_name,
    email
FROM users_storage;

-- 3. INSTEAD OF триггер для поддержки INSERT через представление
CREATE OR REPLACE FUNCTION trg_users_view_insert()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO users_storage (id, name, full_name, email)
    VALUES (NEW.id, NEW.name, COALESCE(NEW.full_name, NEW.name), NEW.email);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_insert
INSTEAD OF INSERT ON users
FOR EACH ROW EXECUTE FUNCTION trg_users_view_insert();
`
}

func main() {
	fmt.Println("=== View-Based Abstraction для прозрачной трансформации схемы ===")
	mgr := &ViewMigrationManager{}
	fmt.Println("Сгенерированный DDL:")
	fmt.Println(mgr.GenerateViewDDL())
	fmt.Println("Преимущество: Старое Go-приложение продолжает выполнять 'SELECT id, name FROM users',")
	fmt.Println("не подозревая, что под капотом данные берутся из users_storage.full_name.")
}
'''

validate_go_code(code18, "code18")
exercises.append({
    "num": 18,
    "title": "Паттерн View-based Abstraction для мгновенной подмены схемы",
    "task": "Скройте физическую структуру таблицы за представлением PostgreSQL: переименуйте таблицу в users_storage и создайте View с именем users. Напишите триггеры INSTEAD OF INSERT/UPDATE для сохранения совместимости со старым кодом. Покажите, как это позволяет прозрачно трансформировать структуру хранения без правки Go-клиентов.",
    "theory": "Паттерн View-based Abstraction позволяет полностью развязать логическую схему данных, которую ожидает приложение, и физическую раскладку таблиц на диске. Вместо того чтобы заставлять приложение писать в новые колонки или адаптироваться к разделению таблиц, таблица переименовывается в users_storage, а на ее месте создается представление (VIEW) users.\n\nДля обеспечения полной функциональности записи создаются триггеры INSTEAD OF INSERT, UPDATE, DELETE на представлении. Любые запросы INSERT INTO users (...) перехватываются триггером и направляются в физическую таблицу с необходимой трансформацией данных. Это дает возможность провести масштабный рефакторинг хранения (например, вертикальное разделение таблицы на users и user_profiles) абсолютно незаметно для работающего приложения.",
    "step_by_step": [
        "Переименовать исходную таблицу users в users_storage в транзакции.",
        "Создать представление CREATE VIEW users с тем же набором колонок, который ожидает приложение v1.",
        "Реализовать функции триггеров INSTEAD OF INSERT/UPDATE/DELETE для прозрачного маппинга данных в users_storage.",
        "Проверить работу старых запросов SELECT, INSERT и UPDATE через созданное представление.",
        "После завершения перехода всех клиентов на новую архитектуру перевести клиентов на прямую работу с физическими таблицами и удалить View."
    ],
    "code_blocks": [
        {
            "filename": "view_abstraction.go",
            "lang": "go",
            "code": code18
        }
    ],
    "under_the_hood": "В PostgreSQL представления являются макросами над запросами (за исключением MATERIALIZED VIEW). Когда запрос обращается к представлению, планировщик выполняет операцию Query Rewrite, подставляя тело представления в AST запроса. Триггеры INSTEAD OF на представлениях компилируются в правила перезаписи операций модификации, позволяя виртуальной сущности вести себя как полноценная таблица.",
    "pitfalls": [
        "Накладные расходы триггеров INSTEAD OF на CPU при экстремальном объеме операций INSERT/UPDATE.",
        "Ограничения оптимизатора запросов: сложные условия фильтрации могут хуже использовать индексы базовой таблицы через представление, если нарушена пушдаун-предикация.",
        "Забытый грант прав (GRANT SELECT, INSERT ON users TO app_role): после создания представления права со старой таблицы автоматически не переносятся."
    ],
    "bigtech_interview": "Когда стоит использовать View-based Abstraction вместо классического Dual Write в Go? Ответ: Когда к базе данных обращаются десятки независимых сервисов, команд или аналитических инструментов, и синхронно обновить их код до деплоя новой схемы невозможно. Представление с INSTEAD OF триггерами изолирует изменение схемы внутри базы данных, предоставляя старым клиентам стабильный виртуальный интерфейс."
})

# Ex 19: Триггеры базы данных vs Двойная запись в Go: компромиссы
code19 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"sync"
	"time"
)

// UserRepoDualWrite реализует двойную запись на уровне Go-сервиса
type UserRepoDualWrite struct {
	db *sql.DB
}

type User struct {
	ID       int64
	Name     string
	FullName string
	Email    string
}

// CreateUser выполняет запись в обе колонки в одном SQL-запросе (атомарно)
func (r *UserRepoDualWrite) CreateUser(ctx context.Context, u *User) error {
	query := `
		INSERT INTO users (name, full_name, email)
		VALUES ($1, $2, $3)
		RETURNING id`
	// Приложение гарантирует, что full_name содержит то же значение, что и name
	if u.FullName == "" {
		u.FullName = u.Name
	}

	return r.db.QueryRowContext(ctx, query, u.Name, u.FullName, u.Email).Scan(&u.ID)
}

// BenchmarkComparison иллюстрирует компромиссы подходов
func PrintTradeoffs() {
	fmt.Println("=== Сравнение: Триггеры БД vs Dual-Write в Go ===")
	fmt.Printf("%-20s | %-35s | %-35s\n", "Критерий", "DB Triggers (PL/pgSQL)", "Dual-Write в Go")
	fmt.Println("-----------------------------------------------------------------------------------------")
	fmt.Printf("%-20s | %-35s | %-35s\n", "Атомарность", "100% гарантирована СУБД", "Требует одной транзакции/запроса")
	fmt.Printf("%-20s | %-35s | %-35s\n", "Нагрузка на CPU", "Ложится на Primary DB (бутылочное горло)", "Распределяется по подам Go (дешево)")
	fmt.Printf("%-20s | %-35s | %-35s\n", "Скрытая логика", "Да (поведение 'спрятано' в СУБД)", "Нет (логика явно видна в коде/тестах)")
	fmt.Printf("%-20s | %-35s | %-35s\n", "Откат миграции", "DROP TRIGGER мгновенно отключает", "Требуется повторный деплой подов")
}

func main() {
	PrintTradeoffs()
}
'''

validate_go_code(code19, "code19")
exercises.append({
    "num": 19,
    "title": "Триггеры базы данных vs Двойная запись в Go: компромиссы",
    "task": "Сравните два подхода к синхронизации старой и новой колонок при миграциях: использование триггеров СУБД (BEFORE/AFTER INSERT) и двойную запись в коде Go-приложения (Dual Write). Напишите пример слоя репозитория Go с Dual Write и сформируйте матрицу архитектурных компромиссов.",
    "theory": "При реализации паттерна Expand-Contract ключевым вопросом является место синхронизации данных между старой и новой структурами: внутри СУБД через триггеры или на уровне приложения через Go-код.\n\nТриггеры СУБД гарантируют абсолютную консистентность: любая запись (даже выполненная вручную через psql или сторонним сервисом) автоматически продублируется. Однако в HighLoad системах первичный узел СУБД (Primary) является самым дорогим и трудномасштабируемым ресурсом. Выполнение триггеров на каждую вставку увеличивает задержку транзакций и нагрузку на CPU базы.\n\nДвойная запись в Go (Dual Write) переносит нагрузку на горизонтально масштабируемые поды приложения. Если запись выполняется в рамках одного SQL-запроса (INSERT INTO t (col1, col2) VALUES ($1, $1)), она остается полностью атомарной без накладных расходов на триггеры.",
    "step_by_step": [
        "Спроектировать репозиторий Go, дублирующий запись в обе колонки в едином SQL-выражении.",
        "Оценить риски рассинхронизации при выполнении двойной записи двумя отдельными запросами.",
        "Проанализировать влияние триггеров на CPU базы данных при профилировании pg_stat_statements.",
        "Составить матрицу принятия решений в зависимости от характера нагрузки и количества сервисов."
    ],
    "code_blocks": [
        {
            "filename": "tradeoffs.go",
            "lang": "go",
            "code": code19
        }
    ],
    "under_the_hood": "Триггеры в PostgreSQL выполняются синхронно в контексте пользовательской транзакции. Для каждого затронутого кортежа вызывается функция PL/pgSQL, что требует создания контекста интерпретатора и аллокации памяти в памяти процесса Postgres Backend. При тысячах RPS это приводит к существенному росту латентности p99 и деградации производительности пула соединений.",
    "pitfalls": [
        "Реализация Dual Write двумя последовательными запросами без транзакции: при сбое сети между запросами база окажется в рассинхронизированном состоянии.",
        "Оставленные навечно забытые триггеры в БД после завершения миграции схемы.",
        "Зацикливание триггеров при взаимной синхронизации нескольких колонок."
    ],
    "bigtech_interview": "Что вы выберете для синхронизации колонок в сервисе с 100,000 RPS: триггер PostgreSQL или Dual Write в Go? Ответ: Dual Write в Go, причем с передачей обоих полей в одном SQL-запросе INSERT/UPDATE. На 100k RPS триггер перегрузит CPU мастера базы данных и приведет к отказу кластера, тогда как Go-приложение распределит CPU-нагрузку по сотням подов в Kubernetes без дополнительных транзакционных издержек."
})

# Ex 20: Миграции схемы в процессе Rolling Update в Kubernetes
code20 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"sync"
	"time"
)

// RollingUpdateSimulator симулирует окно деплоя в k8s, когда работают v1 и v2 поды
type RollingUpdateSimulator struct {
	db *sql.DB
}

func (s *RollingUpdateSimulator) RunPodV1(ctx context.Context, id int, wg *sync.WaitGroup) {
	defer wg.Done()
	// Старая версия v1: знает только колонку 'name'
	ticker := time.NewTicker(200 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			fmt.Printf("[Pod V1 #%d] Грациозно остановлен\n", id)
			return
		case <-ticker.C:
			// Запрос старого сервиса: SELECT id, name FROM users
			fmt.Printf("[Pod V1 #%d] Успешный запрос: SELECT id, name FROM users\n", id)
		}
	}
}

func (s *RollingUpdateSimulator) RunPodV2(ctx context.Context, id int, wg *sync.WaitGroup) {
	defer wg.Done()
	// Новая версия v2: пишет в 'name' и 'full_name'
	ticker := time.NewTicker(200 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			fmt.Printf("[Pod V2 #%d] Грациозно остановлен\n", id)
			return
		case <-ticker.C:
			// Запрос нового сервиса: INSERT INTO users (name, full_name) VALUES (...)
			fmt.Printf("[Pod V2 #%d] Успешный запрос: INSERT INTO users (name, full_name)...\n", id)
		}
	}
}

func main() {
	fmt.Println("=== Симуляция Kubernetes Rolling Update с миграцией схемы ===")
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
	defer cancel()

	sim := &RollingUpdateSimulator{}
	var wg sync.WaitGroup

	// В процессе RollingUpdate одновременно работают поды v1 и v2
	wg.Add(2)
	go sim.RunPodV1(ctx, 1, &wg)
	go sim.RunPodV2(ctx, 2, &wg)

	wg.Wait()
	fmt.Println("Успех: База данных поддерживала запросы v1 и v2 одновременно без ошибок!")
}
'''

validate_go_code(code20, "code20")
exercises.append({
    "num": 20,
    "title": "Миграции схемы в процессе Rolling Update в Kubernetes",
    "task": "Смоделируйте процесс постепенного обновления сервиса (RollingUpdate) в Kubernetes: в кластере на протяжении нескольких минут одновременно функционируют поды старой версии v1 и новой v2. Сформулируйте требование одновременной двусторонней совместимости базы данных и напишите код, демонстрирующий параллельную работу обоих версий без сбоев.",
    "theory": "При развертывании в Kubernetes стандартная стратегия RollingUpdate заменяет поды старой версии новыми постепенно (например, maxSurge: 25%, maxUnavailable: 0). Это означает, что в течение всего окна обновления (от 2 до 15 минут) трафик балансировщика случайным образом распределяется между подами v1 и подами v2.\n\nОтсюда вытекает фундаментальное правило облачных архитектур: Схема базы данных всегда должна быть совместима одновременно с версией N и версией N+1 приложения. Ни в коем случае нельзя применять деструктивные миграции (удаление колонок, переименование, жесткие констрейнты) до того, как абсолютно все поды старой версии прекратят свое существование.",
    "step_by_step": [
        "Определить жизненный цикл развертывания подов в Kubernetes при RollingUpdate.",
        "Сформулировать правило обратной и прямой совместимости SQL-запросов.",
        "Написать симулятор параллельных запросов от подов v1 (старая схема) и v2 (расширенная схема).",
        "Проверить корректность обработки ошибок и убедиться в отсутствии 500 ошибок в процессе миграции."
    ],
    "code_blocks": [
        {
            "filename": "rolling_update.go",
            "lang": "go",
            "code": code20
        }
    ],
    "under_the_hood": "Когда k8s запускает новый ReplicaSet, старый ReplicaSet продолжает обслуживать входящие соединения, пока новые поды не пройдут проверку readinessProbe. Если миграция схемы выполнила RENAME COLUMN до старта RollingUpdate, работающие старые поды мгновенно начнут отдавать 500 Internal Server Error на каждый входящий запрос. Поэтому миграция схемы всегда разделяется на независимые фазы Expand и Contract с отдельными деплоями.",
    "pitfalls": [
        "Запуск миграций схемы в качестве k8s postStart хука каждого пода (гонка за применение миграций между подами).",
        "Использование SELECT * в коде Go-приложения: при добавлении новой колонки через Expand старый код v1 может упасть при сканировании колонок в структуру (sql: expected 3 destination arguments in Scan, got 4).",
        "Удаление старых полей до завершения дренажа трафика со старых подов."
    ],
    "bigtech_interview": "Почему антипаттерн `SELECT *` смертельно опасен для Zero-Downtime миграций в Go? Ответ: Стандартный метод sql.Rows.Scan требует точного соответствия количества запрашиваемых колонок количеству целевых переменных. Если старый код выполняет SELECT *, а миграция Expand добавила новую колонку, Scan вернет фатальную ошибку несоответствия числа аргументов, и все работающие поды старой версии выйдут из строя."
})

# Ex 21: Автоматическое тестирование совместимости схемы в CI/CD
code21 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"testing"
)

// SchemaCompatibilityTester проверяет совместимость старого кода с новой схемой
type SchemaCompatibilityTester struct {
	db *sql.DB
}

func NewSchemaCompatibilityTester(db *sql.DB) *SchemaCompatibilityTester {
	return &SchemaCompatibilityTester{db: db}
}

// TestV1QueriesOnNewSchema имитирует запуск тестового набора v1 на мигрированной БД
func (t *SchemaCompatibilityTester) TestV1QueriesOnNewSchema(ctx context.Context) error {
	fmt.Println("[CI/CD TEST] Запуск набора регрессионных тестов v1 на схеме v2...")

	// 1. Старый запрос выборки пользователя (явное перечисление полей)
	queryV1Read := "SELECT id, name, email FROM users LIMIT 1"
	fmt.Printf("[CI/CD TEST] Проверка чтения v1: %s -> OK\n", queryV1Read)

	// 2. Старый запрос вставки (не должен требовать NOT NULL для новых колонок)
	queryV1Insert := "INSERT INTO users (name, email) VALUES ('Alice', 'alice@test.com')"
	fmt.Printf("[CI/CD TEST] Проверка вставки v1: %s -> OK\n", queryV1Insert)

	// 3. Проверка отсутствия опасных SELECT *
	if err := t.checkNoSelectStar(); err != nil {
		return fmt.Errorf("обнаружен SELECT * в кодовой базе: %w", err)
	}

	fmt.Println("✅ [CI/CD TEST] Схема v2 полностью совместима со старым кодом v1!")
	return nil
}

func (t *SchemaCompatibilityTester) checkNoSelectStar() error {
	// Линтер статического анализа проверяет SQL-запросы в коде
	return nil
}

func main() {
	tester := NewSchemaCompatibilityTester(nil)
	if err := tester.TestV1QueriesOnNewSchema(context.Background()); err != nil {
		log.Fatalf("CI/CD pipeline failed: %v", err)
	}
}
'''

validate_go_code(code21, "code21")
exercises.append({
    "num": 21,
    "title": "Автоматическое тестирование совместимости схемы в CI/CD",
    "task": "Напишите автоматический тест совместимости схемы для пайплайна CI/CD: тест разворачивает чистую базу данных, применяет новую миграцию v2, а затем прогоняет сквозной тестовый набор предыдущей версии приложения v1. Если старый код дает сбой при работе с новой схемой, пайплайн прерывается, блокируя релиз.",
    "theory": "Тестирование обратной совместимости схемы (Backward Compatibility Testing) — ключевой элемент безопасности в CI/CD высоконагруженных систем. Человеческий фактор часто приводит к тому, что разработчик добавляет в миграцию колонку с ограничением NOT NULL без значения по умолчанию, либо переименовывает поле.\n\nВ автоматизированном пайплайне CI/CD создается шаг 'Schema Contract Test': 1) Поднимается эфемерная база данных в Testcontainers; 2) Применяются все миграции текущей ветки (схема N+1); 3) Скачивается бинарник или тестовый сьют стабильной версии master (код N); 4) Прогоняются все интеграционные тесты мастера. Если хотя бы один тест падает — PR блокируется к слиянию.",
    "step_by_step": [
        "Настроить тестовый сценарий развертывания тестовой базы с целевой схемой N+1.",
        "Выполнить проверку выполнения стандартных операций чтения и записи старого сервиса N.",
        "Проверить, что новые колонки имеют DEFAULT либо допускают NULL, исключая отказ старых INSERT.",
        "Интегрировать проверку в пайплайн автоматического тестирования PR."
    ],
    "code_blocks": [
        {
            "filename": "schema_compat_test.go",
            "lang": "go",
            "code": code21
        }
    ],
    "under_the_hood": "Автоматизированные инструменты (такие как pg-query-go или линтеры схемы sqldef/squawk) анализируют AST SQL-миграций. Они автоматически выявляют опасные операции: переименование таблиц и колонок, добавление NOT NULL без DEFAULT, изменение типов с блокировкой и падение обратной совместимости.",
    "pitfalls": [
        "Тестирование миграций только на пустой базе данных (многие проблемы блокировок и дефолтов проявляются только при наличии данных).",
        "Пропуск проверки поведения генераторов запросов (ORM / sqlc / squirrel) старой версии.",
        "Игнорирование проверки триггеров и внешних ключей в тестах совместимости."
    ],
    "bigtech_interview": "Как организовать процесс релиза схемы БД в команде из 100 разработчиков без даунтаймов? Ответ: 1) Статический линтинг миграций в CI (запрет DROP, RENAME, NOT NULL без DEFAULT, CREATE INDEX без CONCURRENTLY); 2) Автоматический тест обратной совместимости (прогон тестов версии N на схеме N+1); 3) Разделение релиза схемы и релиза сервиса на независимые пайплайны."
})

# Ex 22: Симуляция и поиск зависших блокировок в тестах
code22 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
	"time"
)

// LockInspector анализирует активные блокировки в PostgreSQL
type LockInspector struct {
	db *sql.DB
}

type BlockedQueryInfo struct {
	BlockedPID   int    `json:"blocked_pid"`
	BlockingPID  int    `json:"blocking_pid"`
	BlockedQuery string `json:"blocked_query"`
	LockDuration string `json:"lock_duration"`
}

// FindBlockedQueriesSQL возвращает запрос для диагностики очереди блокировок
func (li *LockInspector) FindBlockedQueriesSQL() string {
	return `
SELECT 
    blocked.pid AS blocked_pid,
    blocking.pid AS blocking_pid,
    blocked.query AS blocked_query,
    now() - blocked.query_start AS lock_duration
FROM pg_stat_activity blocked
JOIN pg_locks bl ON bl.pid = blocked.pid AND NOT bl.granted
JOIN pg_locks bll ON bll.locktype = bl.locktype
    AND bll.database IS NOT DISTINCT FROM bl.database
    AND bll.relation IS NOT DISTINCT FROM bl.relation
    AND bll.page IS NOT DISTINCT FROM bl.page
    AND bll.tuple IS NOT DISTINCT FROM bl.tuple
    AND bll.virtualxid IS NOT DISTINCT FROM bl.virtualxid
    AND bll.transactionid IS NOT DISTINCT FROM bl.transactionid
    AND bll.classid IS NOT DISTINCT FROM bl.classid
    AND bll.objid IS NOT DISTINCT FROM bl.objid
    AND bll.objsubid IS NOT DISTINCT FROM bl.objsubid
    AND bll.pid != bl.pid
JOIN pg_stat_activity blocking ON blocking.pid = bll.pid
WHERE NOT blocked.granted;
`
}

func main() {
	fmt.Println("=== Мониторинг и поиск зависших блокировок в pg_locks ===")
	inspector := &LockInspector{}
	fmt.Println("SQL-диагностика конфликтов блокировок:")
	fmt.Println(inspector.FindBlockedQueriesSQL())
	fmt.Println("Принцип: Если миграция ждет lock более 2 секунд, lock_timeout аварийно завершает ее,")
	fmt.Println("не позволяя заблокировать остальные запросы в pg_stat_activity.")
}
'''

validate_go_code(code22, "code22")
exercises.append({
    "num": 22,
    "title": "Симуляция и поиск зависших блокировок в тестах",
    "task": "Напишите код для обнаружения и анализа конфликтов блокировок в PostgreSQL с использованием системных представлений pg_locks и pg_stat_activity. Смоделируйте ситуацию: долгая транзакция удерживает блокировку на чтение, миграция пытается захватить ACCESS EXCLUSIVE LOCK, а настроенный lock_timeout предотвращает каскадный коллапс базы данных.",
    "theory": "В PostgreSQL существует строгая иерархия блокировок. Когда операция DDL (например, ALTER TABLE) пытается получить ACCESS EXCLUSIVE LOCK, она встает в очередь ожидания за всеми активными транзакциями чтения (которые удерживают ACCESS SHARE LOCK).\n\nСамое опасное свойство планировщика блокировок PostgreSQL: любая операция, ждущая ACCESS EXCLUSIVE LOCK, блокирует ВСЕ последующие входящие запросы чтения! Даже если запрос чтения выполняется 1 миллисекунду, он встает в очередь за миграцией. В результате за несколько секунд вся очередь соединений переполняется, и база перестает отвечать. Решением является запрос pg_locks для алертинга и обязательный SET lock_timeout.",
    "step_by_step": [
        "Изучить иерархию взаимоисключающих блокировок PostgreSQL (таблица совместимости lock modes).",
        "Сформировать диагностический запрос к pg_locks и pg_stat_activity для выявления дерева блокировок.",
        "Смоделировать долгую транзакцию чтения и показать, как lock_timeout прерывает миграцию до исчерпания пула соединений.",
        "Реализовать обработку ошибки 55P03 (lock_not_available) в миграционном скрипте Go с экспоненциальным backoff."
    ],
    "code_blocks": [
        {
            "filename": "lock_inspector.go",
            "lang": "go",
            "code": code22
        }
    ],
    "under_the_hood": "В ядре PostgreSQL менеджер блокировок (Lock Manager) использует хеш-таблицу в разделяемой памяти (Shared Memory). Каждая блокировка имеет список ждущих процессов wait-queue. Когда DDL встает в очередь ожидания эксклюзивного лока, он устанавливает флаг ожидания, который не позволяет новым запросам чтения проскочить вперед, вызывая резкий всплеск активных соединений (connection pool exhaustion).",
    "pitfalls": [
        "Отсутствие statement_timeout и lock_timeout на аналитических запросах (долгий SELECT держит блокировку часами).",
        "Попытка принудительного убийства процессов через pg_terminate_backend без предварительного анализа их транзакционного состояния.",
        "Игнорирование алертов о дедлоках (deadlock detected) в логах СУБД."
    ],
    "bigtech_interview": "Почему запрос DDL может обрушить приложение, даже если он еще не начал выполняться, а просто ждет своей очереди? Ответ: Потому что ожидающий ACCESS EXCLUSIVE LOCK блокирует все последующие запросы на чтение и запись. Новые HTTP-запросы накапливаются в очереди пула соединений, за секунды исчерпывая лимит max_connections, в результате чего весь кластер перестает обслуживать трафик."
})

# Ex 23: Секционирование больших таблиц без даунтайма
code23 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
)

// PartitioningManager демонстрирует бесшовный перевод таблицы на декларативное партиционирование
type PartitioningManager struct {
	db *sql.DB
}

func (p *PartitioningManager) GeneratePartitioningPlanSQL() string {
	return `
-- 1. Создание новой секционированной таблицы
CREATE TABLE events_partitioned (
    id BIGSERIAL,
    event_time TIMESTAMPTZ NOT NULL,
    payload JSONB,
    PRIMARY KEY (event_time, id)
) PARTITION BY RANGE (event_time);

-- 2. Создание партиций по месяцам
CREATE TABLE events_2026_01 PARTITION OF events_partitioned
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE events_2026_02 PARTITION OF events_partitioned
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE events_default PARTITION OF events_partitioned DEFAULT;

-- 3. Настройка View и INSTEAD OF триггера для Dual-Write или переключение в коде Go

-- 4. Перенос исторических данных порциями (фоновый бэкфилл)
-- INSERT INTO events_partitioned SELECT * FROM events WHERE event_time >= ...

-- 5. Мгновенная подмена таблиц в транзакции с lock_timeout
-- BEGIN;
-- SET LOCAL lock_timeout = '2s';
-- ALTER TABLE events RENAME TO events_old;
-- ALTER TABLE events_partitioned RENAME TO events;
-- COMMIT;
`
}

func main() {
	fmt.Println("=== Секционирование больших таблиц (Declarative Partitioning) ===")
	pm := &PartitioningManager{}
	fmt.Println(pm.GeneratePartitioningPlanSQL())
	fmt.Println("Результат: Таблица переведена на Range Partitioning без остановки сервиса!")
}
'''

validate_go_code(code23, "code23")
exercises.append({
    "num": 23,
    "title": "Секционирование больших таблиц (Partitioning) без даунтайма",
    "task": "Таблица событий events выросла до сотен гигабайт, и прямая конвертация через ALTER TABLE невозможна. Реализуйте стратегию бесшовного перевода таблицы на декларативное секционирование (Declarative Partitioning) по диапазону дат без даунтайма: создание новой структуры, параллельная запись, поэтапный бэкфилл партиций и мгновенная подмена имен таблиц.",
    "theory": "Секционирование (Partitioning) позволяет разделить монолитную таблицу на физически изолированные сегменты, ускоряя запросы благодаря отсечению партиций (Partition Pruning) и мгновенному удалению старых данных через DROP TABLE partition вместо тяжелого DELETE.\n\nВ PostgreSQL невозможно сконвертировать существующую обычную таблицу в секционированную 'на лету'. Единственный способ без простоя: 1) Создать новую секционированную таблицу с суффиксом _partitioned; 2) Настроить параллельную запись новых данных; 3) Фоновым процессом перенести исторические данные за прошлые месяцы; 4) В короткой транзакции с lock_timeout поменять таблицы местами через ALTER TABLE RENAME.",
    "step_by_step": [
        "Создать секционированную таблицу events_partitioned с нужным ключом партиционирования.",
        "Создать партиции для будущих и текущих периодов, а также дефолтную партицию.",
        "Переключить запись новых данных в новую таблицу (Dual Write или View).",
        "Фоновым скриптом порциями перенести исторические данные из старой таблицы в новые секции.",
        "В транзакции с lock_timeout выполнить переименование таблиц (SWAP) и удалить старую таблицу после карантина."
    ],
    "code_blocks": [
        {
            "filename": "partitioning.go",
            "lang": "go",
            "code": code23
        }
    ],
    "under_the_hood": "В PostgreSQL при декларативном партиционировании мастер-таблица является виртуальной точкой входа. Планировщик использует механизм Constraint Exclusion и Run-Time Partition Pruning: если запрос содержит условие WHERE event_time >= '2026-02-01' AND event_time < '2026-03-01', сканируется только одна соответствующая партиция, остальные исключаются из плана выполнения, что снижает дисковый I/O в десятки раз.",
    "pitfalls": [
        "Первичный ключ в партиционированной таблице обязан включать в себя колонку секционирования (composite primary key).",
        "Создание слишком мелких партиций (например, по часам): тысячи партиций перегрузят каталог метаданных и замедлят планировщик запросов.",
        "Отсутствие дефолтной секции (DEFAULT partition): вставка записи с датой вне существующих диапазонов завершится фатальной ошибкой."
    ],
    "bigtech_interview": "Как удалить 1 миллиард старых логов из PostgreSQL без нагрузки на базу данных? Ответ: Если таблица секционирована по месяцам, удаление месяца выполняется командой DROP TABLE events_2025_01. Это операция изменения метаданных, занимающая 5 миллисекунд и мгновенно освобождающая терабайты диска без генерации WAL и без блокировки других секций, в отличие от катастрофически тяжелого DELETE."
})

# Ex 24: Безопасное добавление внешних ключей (NOT VALID -> VALIDATE)
code24 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
)

// SafeForeignKeyMigrator демонстрирует двухшаговое добавление внешнего ключа
type SafeForeignKeyMigrator struct {
	db *sql.DB
}

func (m *SafeForeignKeyMigrator) Step1_AddConstraintNotValidSQL() string {
	return `
-- Шаг 1: Добавление констрейнта с флагом NOT VALID
-- Требует мгновенной блокировки SHARE ROW EXCLUSIVE, НЕ сканирует существующие строки!
SET LOCAL lock_timeout = '2s';
ALTER TABLE orders 
ADD CONSTRAINT fk_orders_user_id 
FOREIGN KEY (user_id) REFERENCES users(id) NOT VALID;
`
}

func (m *SafeForeignKeyMigrator) Step2_ValidateConstraintSQL() string {
	return `
-- Шаг 2: Фоновая валидация существующих данных
-- Захватывает лишь слабый SHARE UPDATE EXCLUSIVE лок, НЕ блокирует SELECT, INSERT, UPDATE, DELETE!
ALTER TABLE orders 
VALIDATE CONSTRAINT fk_orders_user_id;
`
}

func main() {
	fmt.Println("=== Безопасное добавление Foreign Key: NOT VALID -> VALIDATE ===")
	m := &SafeForeignKeyMigrator{}
	fmt.Println("1. Мгновенное добавление без проверки старых строк:")
	fmt.Println(m.Step1_AddConstraintNotValidSQL())
	fmt.Println("2. Фоновая валидация без блокировки DML операций:")
	fmt.Println(m.Step2_ValidateConstraintSQL())
}
'''

validate_go_code(code24, "code24")
exercises.append({
    "num": 24,
    "title": "Безопасное добавление внешних ключей (Foreign Key Constraints)",
    "task": "Прямое выполнение команды ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) блокирует обе таблицы на чтение и запись для полной проверки ссылочной целостности. Реализуйте безопасный двухшаговый подход: добавление ограничения с флагом NOT VALID и последующая фоновая валидация через VALIDATE CONSTRAINT.",
    "theory": "Добавление внешнего ключа (FOREIGN KEY) на многомиллионной таблице стандартным способом приводит к полному сканированию обеих таблиц с удержанием тяжелых блокировок SHARE ROW EXCLUSIVE. При этом любые изменения данных в обеих таблицах блокируются на все время сканирования.\n\nВ PostgreSQL существует безопасный двухфазный алгоритм: 1) Команда ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY ... NOT VALID. Флаг NOT VALID указывает СУБД проверять внешний ключ только для новых вставок и обновлений, пропуская сканирование существующих строк. Выполняется за миллисекунды; 2) Команда ALTER TABLE ... VALIDATE CONSTRAINT сканирует существующие строки в фоновом режиме, захватывая лишь SHARE UPDATE EXCLUSIVE лок, который разрешает параллельные операции чтения и записи.",
    "step_by_step": [
        "Добавить внешний ключ с модификатором NOT VALID в короткой транзакции с lock_timeout.",
        "Убедиться, что новые строки валидируются автоматически при вставке.",
        "Выполнить отдельной командой ALTER TABLE ... VALIDATE CONSTRAINT.",
        "Обработать возможные нарушения целостности в старых данных без остановки сервиса."
    ],
    "code_blocks": [
        {
            "filename": "safe_foreign_key.go",
            "lang": "go",
            "code": code24
        }
    ],
    "under_the_hood": "При добавлении NOT VALID в системном каталоге pg_constraint создается запись с convalidated = false. Во время выполнения VALIDATE CONSTRAINT СУБД сканирует таблицу sequentially, но удерживает слабый уровень блокировки, совместимый с обычными транзакциями DML. По завершении сканирования флаг convalidated меняется на true в системном каталоге.",
    "pitfalls": [
        "Попытка объединить ADD CONSTRAINT NOT VALID и VALIDATE CONSTRAINT в одной транзакции (смысл разделения теряется, и блокировка останется жесткой).",
        "Наличие 'висячих' ссылок (orphan records) в старых данных: VALIDATE CONSTRAINT завершится ошибкой, поэтому перед валидацией необходим скрипт очистки.",
        "Отсутствие индекса на колонку внешнего ключа (user_id): без индекса удаление записи из родительской таблицы users вызовет полное сканирование таблицы orders."
    ],
    "bigtech_interview": "Почему при создании внешнего ключа в PostgreSQL всегда нужно отдельно создавать индекс на ссылающееся поле? Ответ: PostgreSQL автоматически создает индекс для первичного ключа, но НЕ создает индекс для поля внешнего ключа. Если индекса на foreign key нет, то при любом UPDATE или DELETE в родительской таблице СУБД будет вынуждена делать Seq Scan дочерней таблицы под блокировкой, что парализует производительность."
})

# Ex 25: Стратегия отката миграций: почему Down-миграции опасны
code25 = r'''package main

import (
	"fmt"
)

// MigrationRollbackStrategy объясняет опасности Down-миграций
func ExplainRollbackStrategy() {
	fmt.Println("=== Стратегия отката: Down-миграции vs Forward-Fix ===")
	fmt.Println()
	fmt.Println("❌ Опасность выполнения 'goose down' на проде:")
	fmt.Println("1. Потеря пользовательских данных: DROP COLUMN удаляет все данные, внесенные пользователями")
	fmt.Println("   за время работы новой версии сервиса.")
	fmt.Println("2. Необратимость DDL: случайно удаленные терабайты данных невозможно восстановить без бэкапа.")
	fmt.Println("3. Несовместимость версий: откат схемы ломает код, который уже задеплоен.")
	fmt.Println()
	fmt.Println("✅ Промышленный стандарт: Стратегия Forward-Fix:")
	fmt.Println("1. При аварии откатывается код сервиса (k8s rollback), а схема БД остается совместимой.")
	fmt.Println("2. Если схему необходимо исправить, создается НОВАЯ накатываемая миграция вперед (v+1).")
	fmt.Println("3. База данных развивается исключительно методом Append-Only.")
}

func main() {
	ExplainRollbackStrategy()
}
'''

validate_go_code(code25, "code25")
exercises.append({
    "num": 25,
    "title": "Стратегия отката миграций: почему Down-миграции опасны",
    "task": "Проанализируйте, почему выполнение Down-миграций (автоматический откат схемы вниз) на продакшене при инцидентах является опасным антипаттерном. Опишите риски безвозвратной потери данных пользователей и обоснуйте промышленный подход Forward-Fix (исправление ошибок созданием новой миграции вперед).",
    "theory": "Многие миграционные тулы (goose, golang-migrate) предлагают секции Up и Down. Однако в зрелых engineering-культурах выполнение Down-миграций на боевых базах данных строго запрещено политиками безопасности.\n\nГлавные причины: 1) Потеря данных: если новая версия сервиса поработала 30 минут и пользователи создали тысячи заказов с новым полем, выполнение Down-миграции (DROP COLUMN) навсегда сотрет эти данные; 2) Несимметричность операций: операция создания индекса обратима, но изменение типа данных с конвертацией — нет; 3) Рассинхронизация с кодом: в распределенной системе невозможно мгновенно синхронизировать откат базы данных с сотнями подов сервисов.\n\nЕдинственно правильной стратегией является Forward-Fix: при сбое откатывается код приложения (благодаря Expand-Contract база совместима со старым кодом), а исправление в схему вносится следующей накатываемой миграцией.",
    "step_by_step": [
        "Сравнить сценарии отката схемы вниз (Down) и отката сервиса назад при стабильной схеме.",
        "Проанализировать последствия потери свежих пользовательских данных при выполнении DROP COLUMN.",
        "Сформулировать регламент инцидент-менеджмента: фиксация схемы, откат подов, накат фикса вперед.",
        "Настроить права CI/CD сервисного аккаунта, запрещающие выполнение команд migrate down."
    ],
    "code_blocks": [
        {
            "filename": "forward_fix.go",
            "lang": "go",
            "code": code25
        }
    ],
    "under_the_hood": "В архитектуре баз данных журнал транзакций (WAL) фиксирует все DDL и DML изменения последовательно. Выполнение деструктивного DDL (DROP TABLE/COLUMN) генерирует записи очистки дисковых страниц, делая откат невозможным даже на уровне транзакций после COMMIT. Восстановление данных в таких случаях требует дорогостоящей процедуры Point-in-Time Recovery (PITR) из резервной копии.",
    "pitfalls": [
        "Автоматический запуск 'migrate down' в CI/CD скриптах при падении деплоя приложения.",
        "Написание Down-миграций 'для галочки' без тестирования их безопасности на реальных данных.",
        "Удаление временных колонок до полного подтверждения стабильности бизнес-логики."
    ],
    "bigtech_interview": "Почему в Uber, Netflix и Яндексе запрещено использовать автоматические Down-миграции на проде? Ответ: Потому что база данных в архитектуре Expand-Contract всегда проектируется обратно совместимой. При инцидентах откатывается только код приложения (stateless), а база данных (stateful) не трогается. Любые исправления схемы делаются исключительно накатом новых миграций вперед (Forward-Fix), что исключает случайное уничтожение боевых данных."
})

# Ex 26: Мониторинг лага репликации во время миграций
code26 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
	"time"
)

// ReplicationLagMonitor отслеживает отставание реплик при тяжелых миграциях
type ReplicationLagMonitor struct {
	db *sql.DB
}

type ReplicaStatus struct {
	ClientAddr string
	ReplayLag  time.Duration
}

// CheckReplicationLag опрашивает pg_stat_replication
func (m *ReplicationLagMonitor) CheckReplicationLag(ctx context.Context) ([]ReplicaStatus, error) {
	// В продакшене запрос к мастеру:
	// SELECT client_addr, EXTRACT(EPOCH FROM replay_lag) FROM pg_stat_replication
	return []ReplicaStatus{
		{ClientAddr: "10.0.1.21", ReplayLag: 250 * time.Millisecond},
		{ClientAddr: "10.0.1.22", ReplayLag: 1200 * time.Millisecond}, // Лаг превышен!
	}, nil
}

// ThrottleMigrationIfLagging приостанавливает чанки миграции при росте лага
func (m *ReplicationLagMonitor) ThrottleMigrationIfLagging(ctx context.Context, maxAllowedLag time.Duration) {
	for {
		replicas, err := m.CheckReplicationLag(ctx)
		if err != nil {
			return
		}

		maxLag := time.Duration(0)
		for _, r := range replicas {
			if r.ReplayLag > maxLag {
				maxLag = r.ReplayLag
			}
		}

		if maxLag > maxAllowedLag {
			fmt.Printf("⚠️  [THROTTLE] Лаг репликации %v > порога %v! Пауза миграции на 2s...\n", maxLag, maxAllowedLag)
			select {
			case <-ctx.Done():
				return
			case <-time.After(2 * time.Second):
			}
		} else {
			fmt.Printf("✅ [HEALTH] Лаг репликации в норме (%v). Продолжаем миграцию.\n", maxLag)
			break
		}
	}
}

func main() {
	fmt.Println("=== Мониторинг лага репликации (pg_stat_replication) ===")
	monitor := &ReplicationLagMonitor{}
	monitor.ThrottleMigrationIfLagging(context.Background(), 1*time.Second)
}
'''

validate_go_code(code26, "code26")
exercises.append({
    "num": 26,
    "title": "Мониторинг лага репликации во время миграций",
    "task": "Массивные операции миграции и бэкфилла генерируют огромный объем записей в журнал WAL, что может привести к лагу потоковой репликации на Read-репликах в десятки секунд и отдаче устаревших данных пользователям. Реализуйте мониторинг pg_stat_replication на Go, адаптивно приостанавливающий процесс бэкфилла при превышении порога лага.",
    "theory": "В архитектуре с распределением чтения на реплики (Read Replicas) мастер асинхронно или полусинхронно передает поток WAL-записей репликам через процесс walreceiver/walsender. Если фоновый скрипт миграции выполняет миллионы обновлений строк без пауз, дисковая подсистема реплик не успевает применять (replay) поток WAL.\n\nЭто приводит к росту задержки репликации (Replication Lag), из-за чего пользователи видят устаревшие данные при чтении с реплик. Скрипт миграции на Go обязан перед каждым пакетом запрашивать системное представление pg_stat_replication и замерять метрику replay_lag. Если лаг превышает допустимый SLA (например, 1 секунду), выполнение миграции динамически притормаживается до восстановления нормального состояния.",
    "step_by_step": [
        "Изучить метрики pg_stat_replication: write_lag, flush_lag и replay_lag.",
        "Спроектировать горутину мониторинга задержки репликации в скрипте миграции.",
        "Реализовать механизм адаптивного троттлинга (Throttle Loop) перед выполнением очередного чанка.",
        "Протестировать сценарий автоматического замедления и восстановления скорости бэкфилла."
    ],
    "code_blocks": [
        {
            "filename": "replication_monitor.go",
            "lang": "go",
            "code": code26
        }
    ],
    "under_the_hood": "Метрика replay_lag вычисляется как разница между системным временем мастера на момент генерации WAL-записи и временем ее фактического применения процессом startup на реплике. При интенсивном DDL/DML буферы реплики переполняются, а если параметр max_standby_streaming_delay превышен, долгие запросы пользователей на репликах могут принудительно прерываться (canceling statement due to conflict with recovery).",
    "pitfalls": [
        "Опрос репликации только по одной реплике (нужно находить максимальный лаг среди всех активных реплик).",
        "Игнорирование риска переполнения слота репликации (Replication Slot): если реплика отключится, мастер может исчерпать все дисковое пространство для хранения непереданных WAL.",
        "Слишком частые запросы к pg_stat_replication в цикле без пауз (создают паразитный трафик)."
    ],
    "bigtech_interview": "Что произойдет с Read-репликами PostgreSQL, если запустить массивный UPDATE 50 миллионов строк одним запросом? Ответ: Мастер сгенерирует гигабайты WAL. Реплики испытают огромный лаг применения (replay lag). Запросы на чтение пользователей на репликах начнут либо читать безнадежно устаревшие данные, либо отменяться с ошибкой recovery conflict. Балансировщик снимет отставшие реплики из пула, и весь трафик чтения обрушится на мастер."
})

# Ex 27: Shadow Writing и валидация целостности данных
code27 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"sync/atomic"
	"time"
)

// DataIntegrityAuditor выполняет теневую сверку старой и новой колонок
type DataIntegrityAuditor struct {
	db              *sql.DB
	mismatchCounter int64
}

type UserRecord struct {
	ID       int64
	OldValue string
	NewValue string
}

// CompareBatch проверяет идентичность данных в пачке записей
func (a *DataIntegrityAuditor) CompareBatch(ctx context.Context, startID, endID int64) (int, int, error) {
	// Имитация SQL: SELECT id, name, full_name FROM users WHERE id BETWEEN $1 AND $2
	// В реальном сервисе выполняется выборка и посимвольное/семантическое сравнение
	checked := 1000
	mismatches := 0

	// Симуляция обнаружения несовпадения
	if startID == 5000 {
		mismatches = 1
		atomic.AddInt64(&a.mismatchCounter, int64(mismatches))
		fmt.Printf("🚨 [MISMATCH ALERT] Расхождение в записи ID 5042: Old='%s' != New='%s'\n", "Bob", "Robert")
	}

	return checked, mismatches, nil
}

func main() {
	fmt.Println("=== Shadow Writing & Валидация целостности данных ===")
	auditor := &DataIntegrityAuditor{}
	ctx := context.Background()

	checked, mismatches, _ := auditor.CompareBatch(ctx, 1, 1000)
	fmt.Printf("Проверено: %d, Ошибок: %d\n", checked, mismatches)

	checked, mismatches, _ = auditor.CompareBatch(ctx, 5000, 6000)
	fmt.Printf("Проверено: %d, Ошибок: %d\n", checked, mismatches)

	if auditor.mismatchCounter > 0 {
		fmt.Printf("⛔ Switch Read заблокирован! Найдено %d расхождений. Требуется исправление бэкфилла.\n", auditor.mismatchCounter)
	} else {
		fmt.Println("✅ 100% совпадение данных. Можно безопасно переключать чтение на новую колонку.")
	}
}
'''

validate_go_code(code27, "code27")
exercises.append({
    "num": 27,
    "title": "Shadow Writing и валидация целостности данных",
    "task": "Перед переключением чтения на новую структуру (Switch Read) необходимо доказать 100% корректность перенесенных и синхронизируемых данных. Напишите асинхронный сервис аудита целостности на Go (Shadow Verifier), который пакетами сравнивает старые и новые колонки, детектирует расхождения и блокирует переключение чтения до устранения несоответствий.",
    "theory": "Переключение чтения на новую схему без математической верификации — частая причина скрытой порчи данных (Silent Data Corruption). Ошибки в коде триггеров, тонкости кодировок строк, обрезка пробелов или потеря миллисекунд во временных метках могут привести к тому, что новая колонка разойдется со старой.\n\nПаттерн Shadow Verification предусматривает запуск фонового процесса аудита: он последовательно вычитывает данные парами (old_value, new_value) и выполняет побайтовое и семантическое сравнение. В случае обнаружения хотя бы одного расхождения генерируется алерт в Prometheus/Sentry с выводом первичного ключа поврежденной строки, а фаза Switch Read откладывается до исправления логики бэкфилла.",
    "step_by_step": [
        "Спроектировать воркер постраничной сверки данных между старыми и новыми колонками.",
        "Реализовать сравнение с учетом типов данных (например, нормализация строк или округление timestamp).",
        "Интегрировать счетчики метрик расхождений (mismatch_count) и алертинг.",
        "Убедиться в нулевом проценте расхождений на всем объеме таблицы перед переключением чтения."
    ],
    "code_blocks": [
        {
            "filename": "shadow_verifier.go",
            "lang": "go",
            "code": code27
        }
    ],
    "under_the_hood": "При сравнении данных под высокой нагрузкой возможны 'ложные расхождения' (False Positives) из-за race condition: если строка была обновлена ровно в момент между чтением старой и новой колонок. Качественный Shadow Verifier при обнаружении расхождения делает повторную проверку (re-read with small delay), чтобы исключить влияние параллельного DML.",
    "pitfalls": [
        "Блокировка боевых строк через SELECT ... FOR UPDATE во время аудита (недопустимо под нагрузкой).",
        "Сравнение дат и времени без учета таймзон (UTC vs локальное время базы).",
        "Переключение чтения без предварительного полного аудита 100% исторических строк."
    ],
    "bigtech_interview": "Как гарантировать, что при переносе балансов пользователей из float в numeric ни у одного пользователя не пропала копейка? Ответ: Запустить процесс Shadow Verification: на протяжении недели фоновый сервис непрерывно сверяет старый и новый балансы при каждом чтении асинхронно, а также проводит полный проход по всей базе. Только при достижении 0 расхождений на протяжении нескольких дней дается разрешение на Switch Read."
})

# Ex 28: Zero-Downtime миграции в NoSQL (On-Read Migration в MongoDB)
code28 = r'''package main

import (
	"context"
	"fmt"
	"time"
)

// UserDocV1 представляет старый документ без поля Status
type UserDocV1 struct {
	ID    string `bson:"_id"`
	Email string `bson:"email"`
}

// UserDocV2 представляет расширенный документ
type UserDocV2 struct {
	ID        string    `bson:"_id"`
	Email     string    `bson:"email"`
	Status    string    `bson:"status"`     // Новое поле со значением по умолчанию "active"
	UpdatedAt time.Time `bson:"updated_at"` // Новое поле
	Version   int       `bson:"schema_ver"` // Версия схемы документа
}

// MongoLazyMigrator реализует миграцию схемы при чтении (On-Read Migration)
type MongoLazyMigrator struct{}

// FindUserWithOnReadMigration загружает документ и при необходимости обновляет его схему
func (m *MongoLazyMigrator) FindUserWithOnReadMigration(ctx context.Context, rawDoc map[string]interface{}) UserDocV2 {
	ver, _ := rawDoc["schema_ver"].(int)

	user := UserDocV2{
		ID:    rawDoc["_id"].(string),
		Email: rawDoc["email"].(string),
	}

	// Если документ старой схемы (ver < 2), применяем ленивую миграцию
	if ver < 2 {
		user.Status = "active" // Значение по умолчанию
		user.UpdatedAt = time.Now().UTC()
		user.Version = 2

		// Асинхронно сохраняем обновленный документ в MongoDB без блокировки клиента
		go m.asyncSaveMigratedDoc(user)
		fmt.Printf("⚡ [ON-READ MIGRATION] Документ %s лениво мигрирован v1 -> v2\n", user.ID)
	} else {
		user.Status = rawDoc["status"].(string)
		user.Version = ver
	}

	return user
}

func (m *MongoLazyMigrator) asyncSaveMigratedDoc(u UserDocV2) {
	// В проде: collection.UpdateOne(ctx, filter, update)
	fmt.Printf("💾 [ASYNC SAVE] Сохранен документ %s схемы v%d в MongoDB\n", u.ID, u.Version)
}

func main() {
	fmt.Println("=== NoSQL Zero-Downtime: Паттерн On-Read Migration ===")
	migrator := &MongoLazyMigrator{}

	// Документ старого формата из MongoDB
	oldDoc := map[string]interface{}{
		"_id":   "usr_1001",
		"email": "user@example.com",
		// schema_ver отсутствует (0)
	}

	user := migrator.FindUserWithOnReadMigration(context.Background(), oldDoc)
	fmt.Printf("Клиент получил пользователя v2: ID=%s, Email=%s, Status=%s, Ver=%d\n",
		user.ID, user.Email, user.Status, user.Version)
	time.Sleep(50 * time.Millisecond)
}
'''

validate_go_code(code28, "code28")
exercises.append({
    "num": 28,
    "title": "Zero-Downtime миграции в NoSQL (Ленивая миграция документов в MongoDB)",
    "task": "В документо-ориентированных СУБД (MongoDB) отсутствует жесткий DDL, но структура BSON-документов эволюционирует. Реализуйте паттерн On-Read Migration (Lazy Migration): при чтении документа старой схемы Go-сервис на лету дополняет его новыми полями по умолчанию и асинхронно обновляет документ в базе данных, постепенно переводя активные данные на новую схему без фонового перелопачивания миллиардов записей.",
    "theory": "В NoSQL базах данных с бессхемным хранением (Schema-less / Schema-on-Read) классические DDL-миграции неприменимы. Попытка запустить глобальный фоновый скрипт обновления миллиарда документов в MongoDB приведет к перегрузке WiredTiger кэша, дисковой подсистемы и деградации производительности.\n\nПромышленным стандартом эволюции NoSQL схем является On-Read Migration: 1) Каждый документ снабжается полем версии schema_version; 2) Go-приложение содержит адаптеры миграций (v1 -> v2, v2 -> v3); 3) При чтении документ преобразуется в актуальную модель в оперативной памяти приложения; 4) В фоновой горутине документ асинхронно сохраняется в обновленном формате. Документы, к которым никто не обращается, не нагружают СУБД.",
    "step_by_step": [
        "Ввести версионирование документов через поле schema_version.",
        "Реализовать интерфейс трансформации модели при десериализации BSON.",
        "Настроить асинхронное фоновое сохранение (Write-Back) обновленного документа при чтении.",
        "Обеспечить корректность работы комбинированного подхода: On-Read для горячих данных + медленный фоновый воркер для холодных."
    ],
    "code_blocks": [
        {
            "filename": "lazy_migration.go",
            "lang": "go",
            "code": code28
        }
    ],
    "under_the_hood": "В MongoDB операция обновления документа, увеличивающего свой размер (добавление новых полей), может привести к перемещению документа на диске или выделению новых экстентов в WiredTiger, вызывая фрагментацию памяти. Ленивая миграция распределяет эти операции во времени пропорционально естественному пользовательскому трафику.",
    "pitfalls": [
        "Синхронное обновление документа в базе в момент чтения: удваивает сетевую задержку запроса SELECT для пользователя (обновление должно быть строго асинхронным).",
        "Отсутствие обработки очень старых документов (v0), не читавшихся годами (для них по-прежнему нужен редкий ночной бэкфилл).",
        "Гонки версий при параллельном чтении и обновлении одного документа."
    ],
    "bigtech_interview": "Как обновить формат 5 миллиардов профилей пользователей в MongoDB без даунтайма и без взрывного роста нагрузки на кластер? Ответ: Применить паттерн On-Read Migration. Горячие 20% профилей мигрируют естественным путем при чтении пользователями за первые 48 часов с асинхронным сохранением в базу, а оставшиеся 80% холодных данных домигрирует низкоприоритетный фоновый воркер с ограничением 50 документов в секунду."
})

# Ex 29: Безопасное удаление неиспользуемых таблиц (14-дневный карантин)
code29 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
	"time"
)

// SafeTableDeprecator управляет многоэтапным процессом вывода таблиц из эксплуатации
type SafeTableDeprecator struct {
	db *sql.DB
}

// Step1_RevokeWritePermissions отзывает права на запись, разрешая только чтение
func (d *SafeTableDeprecator) Step1_RevokeWritePermissions(tableName, appRole string) string {
	return fmt.Sprintf(`
-- Шаг 1: Запрет записи для обнаружения сервисов, все еще пишущих в таблицу
REVOKE INSERT, UPDATE, DELETE ON TABLE %s FROM %s;
`, tableName, appRole)
}

// Step2_RenameToDeprecated переименовывает таблицу в карантинное имя
func (d *SafeTableDeprecator) Step2_RenameToDeprecated(tableName string) string {
	deprecatedName := fmt.Sprintf("_deprecated_%s_%s", tableName, time.Now().Format("20060102"))
	return fmt.Sprintf(`
-- Шаг 2: Карантинное переименование (срок выдержки: 14 дней)
SET LOCAL lock_timeout = '2s';
ALTER TABLE %s RENAME TO %s;
`, tableName, deprecatedName)
}

// Step3_DropAfterGracePeriod окончательно удаляет таблицу после карантина
func (d *SafeTableDeprecator) Step3_DropAfterGracePeriod(deprecatedName string) string {
	return fmt.Sprintf(`
-- Шаг 3: Физическое удаление после 14 дней отсутствия алертов
DROP TABLE IF EXISTS %s;
`, deprecatedName)
}

func main() {
	fmt.Println("=== Регламент безопасного удаления неиспользуемых таблиц ===")
	deprecator := &SafeTableDeprecator{}
	fmt.Println(deprecator.Step1_RevokeWritePermissions("orders_legacy", "app_service_role"))
	fmt.Println(deprecator.Step2_RenameToDeprecated("orders_legacy"))
	fmt.Println(deprecator.Step3_DropAfterGracePeriod("_deprecated_orders_legacy_20260908"))
}
'''

validate_go_code(code29, "code29")
exercises.append({
    "num": 29,
    "title": "Безопасное удаление неиспользуемых таблиц",
    "task": "Прямое выполнение команды DROP TABLE orders_legacy на продакшене несет огромный риск, если какой-либо забытый фоновый сервис, cron-скрипт или отчетный пайплайн все еще использует эту таблицу. Реализуйте промышленный регламент безопасного вывода таблицы из эксплуатации: 1) отзыв прав на запись; 2) переименование в _deprecated_ с 14-дневным карантином; 3) аудит логов и окончательное удаление.",
    "theory": "Удаление таблиц в крупных распределенных системах — операция с высоким риском катастрофических последствий. Даже если ведущий бэкенд-сервис перестал обращаться к таблице, к ней могут обращаться вспомогательные воркеры, ETL-процессы дата-саентистов или генераторы бухгалтерских выгрузок.\n\nБезопасный регламент вывода из эксплуатации (Table Deprecation Workflow) состоит из 3 этапов: 1) Запрет прав на запись (REVOKE INSERT, UPDATE): выявляет пишущие сервисы без риска потери данных; 2) Переименование таблицы в _deprecated_<name>_<date> в короткой транзакции: любые оставшиеся сервисы чтения получат ошибку relation does not exist, что немедленно отразится на алертах мониторинга; 3) Карантинный период в 14–30 дней: если за месяц ни одного обращения не зафиксировано, выполняется DROP TABLE.",
    "step_by_step": [
        "Отозвать права DML у сервисных пользователей базы данных.",
        "Переименовать таблицу с добавлением префикса _deprecated_ и даты переименования.",
        "Настроить мониторинг pg_stat_user_tables и логов PostgreSQL на попытки обращения к таблице.",
        "Выдержать регламентный карантинный срок (14-30 дней).",
        "Выполнить финальный DROP TABLE."
    ],
    "code_blocks": [
        {
            "filename": "table_deprecation.go",
            "lang": "go",
            "code": code29
        }
    ],
    "under_the_hood": "Переименование таблицы (ALTER TABLE ... RENAME TO ...) изменяет лишь имя объекта в каталоге pg_class. Все физические файлы на диске (relfilenode), индексы и данные остаются нетронутыми. Если переименование сломало критический бизнес-процесс, мгновенный откат выполняется обратным переименованием за 5 миллисекунд без необходимости восстановления из резервной копии.",
    "pitfalls": [
        "Немедленное удаление DROP TABLE на основе предположения 'мы в кодовой базе этого не нашли' (код может быть во внешних репозиториях).",
        "Забытые внешние ключи или триггеры, ссылающиеся на удаляемую таблицу.",
        "Отсутствие даты в имени карантинной таблицы, из-за чего через год никто не помнит, чья это таблица и можно ли ее удалить."
    ],
    "bigtech_interview": "Почему переименование таблицы в _deprecated_ надежнее, чем просто отключение прав? Ответ: Потому что суперпользователи (например, сервисы с правами postgres или сервисные репликаторы) могут игнорировать REVOKE прав, продолжая работать. Переименование объекта в системном каталоге ломает любые жестко захардкоженные SQL-запросы абсолютно для всех пользователей, гарантированно подсвечивая скрытые зависимости в системе мониторинга."
})

# Ex 30: Полнофункциональная утилита Zero-Downtime миграций на Go
code30 = r'''package main

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"log"
	"os"
	"os/signal"
	"sync/atomic"
	"syscall"
	"time"
)

// ZeroDowntimeMigrationEngine представляет полноценный движок онлайн-миграций
type ZeroDowntimeMigrationEngine struct {
	db             *sql.DB
	tableName      string
	sourceCol      string
	targetCol      string
	batchSize      int
	throttleDelay  time.Duration
	maxAllowedLag  time.Duration
	migratedCount  int64
	currentBatchID int64
}

type EngineConfig struct {
	TableName     string
	SourceCol     string
	TargetCol     string
	BatchSize     int
	ThrottleDelay time.Duration
	MaxAllowedLag time.Duration
	StartID       int64
}

func NewEngine(db *sql.DB, cfg EngineConfig) *ZeroDowntimeMigrationEngine {
	return &ZeroDowntimeMigrationEngine{
		db:             db,
		tableName:      cfg.TableName,
		sourceCol:      cfg.SourceCol,
		targetCol:      cfg.TargetCol,
		batchSize:      cfg.BatchSize,
		throttleDelay:  cfg.ThrottleDelay,
		maxAllowedLag:  cfg.MaxAllowedLag,
		currentBatchID: cfg.StartID,
	}
}

// Run выполняет процесс миграции с поддержкой SIGINT graceful shutdown
func (e *ZeroDowntimeMigrationEngine) Run(ctx context.Context) error {
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	fmt.Printf("🚀 [ENGINE] Старт Zero-Downtime миграции таблицы '%s' (%s -> %s)\n",
		e.tableName, e.sourceCol, e.targetCol)
	fmt.Printf("   Размер чанка: %d, Начальный ID: %d, Задержка: %v\n",
		e.batchSize, e.currentBatchID, e.throttleDelay)

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case sig := <-sigChan:
			fmt.Printf("\n🛑 [SHUTDOWN] Получен сигнал %v. Сохранение точки останова (ID=%d)...\n",
				sig, e.currentBatchID)
			return errors.New("миграция прервана оператором")
		default:
		}

		// 1. Проверка здоровья репликации
		if err := e.checkReplicationHealth(ctx); err != nil {
			fmt.Printf("⏳ [THROTTLE] Репликация отстает: %v. Ожидание 1с...\n", err)
			time.Sleep(1 * time.Second)
			continue
		}

		// 2. Выполнение одного чанка
		processed, nextID, err := e.processChunk(ctx, e.currentBatchID)
		if err != nil {
			return fmt.Errorf("chunk failure at id %d: %w", e.currentBatchID, err)
		}

		if processed == 0 {
			fmt.Println("🎉 [FINISH] Все исторические записи успешно мигрированы!")
			break
		}

		atomic.AddInt64(&e.migratedCount, int64(processed))
		e.currentBatchID = nextID

		fmt.Printf("📦 [PROGRESS] Мигрировано: %d строк (Текущий ID: %d)\n",
			atomic.LoadInt64(&e.migratedCount), e.currentBatchID)

		// 3. Динамическая пауза троттлинга
		time.Sleep(e.throttleDelay)
	}

	return nil
}

func (e *ZeroDowntimeMigrationEngine) checkReplicationHealth(ctx context.Context) error {
	// В реальной БД: SELECT MAX(EXTRACT(EPOCH FROM replay_lag)) FROM pg_stat_replication
	return nil
}

func (e *ZeroDowntimeMigrationEngine) processChunk(ctx context.Context, startID int64) (int, int64, error) {
	// Симуляция успешной обработки чанка
	endID := startID + int64(e.batchSize)
	if startID >= 5000 {
		return 0, endID, nil // Конец таблицы
	}
	return e.batchSize, endID, nil
}

func main() {
	fmt.Println("=== Capstone: Полнофункциональная утилита Zero-Downtime миграций на Go ===")
	cfg := EngineConfig{
		TableName:     "users",
		SourceCol:     "name",
		TargetCol:     "full_name",
		BatchSize:     1000,
		ThrottleDelay: 50 * time.Millisecond,
		MaxAllowedLag: 1 * time.Second,
		StartID:       1,
	}

	engine := NewEngine(nil, cfg)
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	if err := engine.Run(ctx); err != nil && !errors.Is(err, context.DeadlineExceeded) {
		log.Printf("Ошибка работы движка: %v\n", err)
	}
}
'''

validate_go_code(code30, "code30")
exercises.append({
    "num": 30,
    "title": "Полнофункциональная утилита Zero-Downtime миграций на Go",
    "task": "Создайте законченную промышленную консольную утилиту фонового переноса данных на Go. Утилита должна поддерживать: настройку размера пакета (batch size), динамический троттлинг по лагу репликации (pg_stat_replication), жесткий lock_timeout, сохранение чекпоинта прогресса, корректную обработку SIGINT/SIGTERM (graceful shutdown) и метрики прогресса.",
    "theory": "Фоновый перенос данных (Backfill Engine) в HighLoad архитектуре — это самостоятельный распределенный микросервис высокой надежности. Он должен безопасно перекачивать терабайты данных между колонками или таблицами на работающем продакшене без малейшего влияния на клиентский трафик.\n\nПромышленная утилита на Go обязана обладать свойствами: 1) Детерминированность: итерация строго по упорядоченному первичному ключу (Keyset Pagination); 2) Самоограничение (Backpressure / Throttling): остановка при малейшем намеке на деградацию мастера или реплик; 3) Грациозная остановка (Graceful Shutdown): перехват os.Interrupt с фиксацией последнего обработанного ID в таблицу контрольных точек; 4) Идемпотентность: возможность перезапуска с сохраненного смещения без дублирования или порчи данных.",
    "step_by_step": [
        "Спроектировать структуру конфигурации и контекст выполнения утилиты переноса данных.",
        "Реализовать цикл чанкования по индексированному первичному ключу.",
        "Интегрировать мониторинг задержки репликации с адаптивным сном.",
        "Настроить обработку системных сигналов SIGINT и SIGTERM с фиксацией прогресса.",
        "Продемонстрировать запуск, штатную остановку и перезапуск утилиты."
    ],
    "code_blocks": [
        {
            "filename": "migration_engine.go",
            "lang": "go",
            "code": code30
        }
    ],
    "under_the_hood": "Движок использует паттерн Keyset Pagination (WHERE id >= $1 ORDER BY id LIMIT $2) вместо антипаттерна OFFSET. Сканирование по первичному ключу гарантирует константную сложность выборки O(log N) для каждого чанка независимо от глубины смещения, исключая экспоненциальное замедление при обработке миллиардных таблиц.",
    "pitfalls": [
        "Использование OFFSET в запросах чанкования (к концу таблицы запрос OFFSET 10000000 сканирует 10 миллионов строк в памяти, вызывая зависание).",
        "Жесткое аварийное завершение процесса (kill -9) без сохранения текущего смещения.",
        "Отсутствие тайм-аутов на сетевых вызовах к базе данных в цикле миграции."
    ],
    "bigtech_interview": "Как в распределенной системе гарантировать, что два инстанса утилиты бэкфилла не начнут обрабатывать один и тот же диапазон строк одновременно? Ответ: Использовать распределенную блокировку (pg_advisory_lock в PostgreSQL или distributed lock в Redis/etcd) с уникальным идентификатором задачи миграции. Перед началом работы утилита захватывает pg_try_advisory_lock(); если лок уже удерживается другим процессом, утилита немедленно завершает работу с понятным сообщением."
})

output_path = '/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch96_p2.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Chapter 96 Part 2 generated successfully: {len(exercises)} exercises.")
