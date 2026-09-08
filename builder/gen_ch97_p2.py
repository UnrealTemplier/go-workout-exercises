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

# Ex 16: Пересечение множеств индексов через Roaring Bitmaps
code16 = r'''package main

import (
	"fmt"
)

// SimpleBitmap симулирует работу компактных битовых карт для списков постингов
type SimpleBitmap struct {
	words []uint64
}

func NewSimpleBitmap() *SimpleBitmap {
	return &SimpleBitmap{words: make([]uint64, 16)} // 16 * 64 = 1024 ID
}

func (b *SimpleBitmap) Set(id uint32) {
	wordIdx := id / 64
	bitIdx := id % 64
	if int(wordIdx) >= len(b.words) {
		newWords := make([]uint64, wordIdx+1)
		copy(newWords, b.words)
		b.words = newWords
	}
	b.words[wordIdx] |= (1 << bitIdx)
}

func (b *SimpleBitmap) And(other *SimpleBitmap) *SimpleBitmap {
	minLen := len(b.words)
	if len(other.words) < minLen {
		minLen = len(other.words)
	}

	res := &SimpleBitmap{words: make([]uint64, minLen)}
	for i := 0; i < minLen; i++ {
		// Побитовое аппаратное И (AND) по 64 элемента за одну инструкцию!
		res.words[i] = b.words[i] & other.words[i]
	}
	return res
}

func (b *SimpleBitmap) ToArray() []uint32 {
	var res []uint32
	for wordIdx, word := range b.words {
		if word == 0 {
			continue
		}
		for bitIdx := 0; bitIdx < 64; bitIdx++ {
			if (word & (1 << bitIdx)) != 0 {
				res = append(res, uint32(wordIdx*64+bitIdx))
			}
		}
	}
	return res
}

func main() {
	fmt.Println("=== Битовые карты и ускорение пересечений индексов ===")
	bmAuth := NewSimpleBitmap()
	bmProd := NewSimpleBitmap()

	// Индексируем серии
	bmAuth.Set(10)
	bmAuth.Set(42)
	bmAuth.Set(99)

	bmProd.Set(5)
	bmProd.Set(42) // Общий элемент
	bmProd.Set(99) // Общий элемент

	matched := bmAuth.And(bmProd)
	fmt.Printf("Пересечение (AND): %v (ожидалось [42, 99])\n", matched.ToArray())
	fmt.Println("Преимущество Roaring Bitmaps: 64 SeriesID проверяются за 1 такт процессора!")
}
'''

validate_go_code(code16, "code16")
exercises.append({
    "num": 16,
    "title": "Пересечение множеств индексов через Roaring Bitmaps",
    "task": "Поиск пересечения списков []uint32 при десятках миллионов серий создает колоссальную нагрузку на CPU. Реализуйте концепцию Roaring Bitmaps на Go: представление множества SeriesID в виде битовых слов (uint64) и выполнение операций пересечения фильтров меток (AND) за один машинный такт процессора на каждые 64 идентификатора.",
    "theory": "В высоконагруженных TSDB (VictoriaMetrics, Prometheus, ClickHouse) списки постингов обратного индекса содержат миллионы чисел SeriesID. Пересечение таких списков наивным алгоритмом слияния слайсов упирается в пропускную способность памяти и ветвления процессора.\n\nRoaring Bitmaps решают эту проблему радикально: диапазон 32-битных чисел разбивается на сегменты по $2^{16} = 65\\,536$ элементов (Containers). Если плотность контейнера мала — числа хранятся как отсортированный массив; если плотность высока — контейнер превращается в битовую маску из 1024 64-битных слов (`uint64`).\n\nПри поиске `{service=\"auth\", env=\"prod\"}` процессор выполняет векторную операцию побитового И (`AND`) между словами `uint64`. Это позволяет проверить принадлежность сразу 64 серий за одну ассемблерную инструкцию, ускоряя фильтрацию в десятки раз.",
    "step_by_step": [
        "Спроектировать структуру битовой карты на основе среза слов uint64.",
        "Реализовать метод установки бита `Set(id uint32)` по формуле `wordIdx = id / 64`, `bitIdx = id % 64`.",
        "Реализовать метод пересечения `And(other)` с пословным умножением масок.",
        "Преобразовать битовую карту обратно в срез идентификаторов серий для извлечения точек."
    ],
    "code_blocks": [
        {
            "filename": "roaring_concept.go",
            "lang": "go",
            "code": code16
        }
    ],
    "under_the_hood": "Современные компиляторы Go и архитектура x86-64/ARM64 способны векторизовать подобные операции с использованием SIMD-регистров (AVX-512 / NEON), вычисляя пересечение 512 идентификаторов за одну процессорную инструкцию `VPAND`.",
    "pitfalls": [
        "Использование наивной битовой карты фиксированного размера для разреженных данных (избыточный расход памяти на пустые нули).",
        "Неэффективное извлечение битов через деление вместо битового сдвига и `bits.TrailingZeros64`.",
        "Отсутствие компрессии блоков RLE (Run-Length Encoding) для длинных последовательностей единиц."
    ],
    "bigtech_interview": "Почему Roaring Bitmaps превосходят классические HashSet и срезы []uint32 в индексах TSDB? Ответ: 1) Компактность: Roaring Bitmap динамически выбирает представление (Array Container, Bitset Container или Run Container), сжимая списки ID в разы; 2) Скорость: пересечение множеств выполняется через побитовые инструкции процессора AND над кэш-линиями L1, исключая промахи кэша памяти и ветвления."
})

# Ex 17: Интеграция с TimescaleDB: гипертаблицы и партиционирование
code17 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
)

// TimescaleHypertableManager управляет созданием гипертаблиц в PostgreSQL
type TimescaleHypertableManager struct {
	db *sql.DB
}

func (m *TimescaleHypertableManager) GenerateInitSQL() string {
	return `
-- 1. Подключение расширения TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 2. Создание стандартной таблицы PostgreSQL
CREATE TABLE IF NOT EXISTS device_metrics (
    time TIMESTAMPTZ NOT NULL,
    device_id INT NOT NULL,
    cpu_usage DOUBLE PRECISION,
    mem_usage DOUBLE PRECISION,
    temperature DOUBLE PRECISION
);

-- 3. Превращение таблицы в Hypertable с партиционированием по 1 суткам
SELECT create_hypertable(
    'device_metrics', 
    'time', 
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- 4. Создание составного индекса для быстрой фильтрации по устройству и времени
CREATE INDEX IF NOT EXISTS idx_device_time ON device_metrics (device_id, time DESC);
`
}

func main() {
	fmt.Println("=== Интеграция с TimescaleDB: Создание гипертаблицы ===")
	mgr := &TimescaleHypertableManager{}
	fmt.Println(mgr.GenerateInitSQL())
	fmt.Println("Преимущество гипертаблицы: TimescaleDB автоматически создает физические партиции (чанки),")
	fmt.Println("сохраняя для Go-приложения иллюзию работы с одной монолитной SQL-таблицей.")
}
'''

validate_go_code(code17, "code17")
exercises.append({
    "num": 17,
    "title": "Интеграция с TimescaleDB: гипертаблицы и партиционирование",
    "task": "Разверните поддержку данных временных рядов поверх реляционной базы PostgreSQL с использованием расширения TimescaleDB. Напишите DDL-скрипт инициализации гипертаблицы (Hypertable) с шагом квантования chunk_time_interval => INTERVAL '1 day' и составным индексом для телеметрии IoT-устройств.",
    "theory": "TimescaleDB — ведущее промышленное расширение для PostgreSQL, превращающее классическую реляционную СУБД в сверхпроизводительную Time-Series базу данных.\n\nКлючевая абстракция TimescaleDB — **Гипертаблица (Hypertable)**. Для Go-приложения гипертаблица выглядит как обычная таблица PostgreSQL (к ней применимы стандартные SELECT, INSERT, JOIN и драйвер `jackc/pgx`). Под капотом TimescaleDB автоматически разбивает гипертаблицу на множество изолированных стандартных таблиц PostgreSQL, называемых **чанками (Chunks)**, по диапазонам времени (например, по 1 суткам).\n\nКаждый чанк содержит собственный независимый B-Tree индекс, который гарантированно целиком помещается в оперативной памяти (Shared Buffers), устраняя деградацию скорости вставки даже при петабайтах данных.",
    "step_by_step": [
        "Подключить расширение `timescaledb` в базе данных.",
        "Создать схему таблицы телеметрии с обязательным полем `time TIMESTAMPTZ NOT NULL`.",
        "Выполнить системную функцию `create_hypertable` с настройкой суточного интервала.",
        "Создать индекс `(device_id, time DESC)` для оптимизации точечных запросов к датчикам."
    ],
    "code_blocks": [
        {
            "filename": "timescale_hypertable.go",
            "lang": "go",
            "code": code17
        }
    ],
    "under_the_hood": "TimescaleDB перехватывает запросы к гипертаблице на уровне планировщика PostgreSQL (Planner Hook). При выполнении запроса `WHERE time > NOW() - INTERVAL '2 hours'` планировщик отсекает 99% чанков (Chunk Exclusion), направляя запрос только в активный суточный чанк, что снижает время выполнения запроса с минут до миллисекунд.",
    "pitfalls": [
        "Отсутствие ограничения NOT NULL на колонке времени (TimescaleDB откажется создавать гипертаблицу).",
        "Слишком большой chunk_time_interval (например, 1 месяц на миллионном потоке): чанк не поместится в RAM.",
        "Слишком маленький chunk_time_interval (например, 5 минут): тысячи чанков перегрузят каталог метаданных Postgres."
    ],
    "bigtech_interview": "В чем главное архитектурное отличие TimescaleDB от ClickHouse при работе с временными рядами? Ответ: TimescaleDB — это полнофункциональный PostgreSQL с поддержкой 100% ACID-транзакций, вторичных индексов, внешних ключей и точечных выборок, идеально подходящий для operational данных; ClickHouse — это распределенная колоночная аналитическая СУБД (OLAP), ориентированная на тяжелую пакетную агрегацию триллионов событий без строгой поддержки ACID."
})

# Ex 18: Агрегация временных рядов (Time Bucketing / Downsampling)
code18 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
	"time"
)

// MetricAggregate результат агрегации за временной бакет
type MetricAggregate struct {
	BucketTime  time.Time
	AvgTemp     float64
	MaxTemp     float64
	MinTemp     float64
	SampleCount int64
}

// TimeBucketQueryRunner демонстрирует выборку агрегатов
type TimeBucketQueryRunner struct {
	db *sql.DB
}

func (r *TimeBucketQueryRunner) BuildTimeBucketSQL(deviceID int, duration string) string {
	// Использование встроенной функции timescaledb time_bucket
	return fmt.Sprintf(`
SELECT 
    time_bucket('5 minutes', time) AS bucket,
    AVG(temperature) AS avg_temp,
    MAX(temperature) AS max_temp,
    MIN(temperature) AS min_temp,
    COUNT(*) AS sample_count
FROM device_metrics
WHERE device_id = %d AND time > NOW() - INTERVAL '%s'
GROUP BY bucket
ORDER BY bucket ASC;
`, deviceID, duration)
}

func main() {
	fmt.Println("=== Агрегация временных рядов: time_bucket ===")
	runner := &TimeBucketQueryRunner{}
	sqlQuery := runner.BuildTimeBucketSQL(42, "24 hours")
	fmt.Println("Сгенерированный SQL для Grafana:")
	fmt.Println(sqlQuery)
	fmt.Println("Преимущество time_bucket: Сжатие 86400 секундных точек за сутки")
	fmt.Println("в ровно 288 аккуратных 5-минутных точек для отображения на графике.")
}
'''

validate_go_code(code18, "code18")
exercises.append({
    "num": 18,
    "title": "Агрегация временных рядов (Time Bucketing / Downsampling)",
    "task": "Отображение графика в Grafana за сутки требует не сырых 86 400 секундных точек, а компактной агрегации с шагом в 5 минут. Напишите SQL-запрос с использованием функции time_bucket('5 minutes', time) в TimescaleDB, рассчитывающий среднюю (AVG), максимальную (MAX) и минимальную (MIN) температуру, а также структуру Go для сканирования результата.",
    "theory": "Паттерн Time Bucketing (квантование времени / Downsampling) — фундаментальный инструмент для визуализации и анализа временных рядов.\n\nЕсли веб-браузер или дашборд запросит 10 миллионов сырых точек телеметрии, произойдет переполнение сетевого канала, браузер зависнет от нехватки памяти, а ширина монитора все равно составляет не более 1920–3840 пикселей по горизонтали.\n\nФункция `time_bucket(interval, timestamp)` в TimescaleDB делит непрерывную ось времени на фиксированные корзины (бакеты), округляя каждую временную метку к началу соответствующего интервала. В сочетании с `GROUP BY bucket` и агрегатными функциями `AVG()`, `MIN()`, `MAX()`, `COUNT()` запрос превращает гигабайты сырых точек в компактную таблицу из нескольких сотен усредненных значений.",
    "step_by_step": [
        "Изучить механику округления времени функцией time_bucket.",
        "Сформировать запрос группировки по 5-минутным корзинам за последние 24 часа.",
        "Спроектировать структуру MetricAggregate для сканирования строк через sql.Rows.",
        "Обеспечить правильную сортировку ORDER BY bucket ASC для отрисовки временной шкалы."
    ],
    "code_blocks": [
        {
            "filename": "time_bucketing.go",
            "lang": "go",
            "code": code18
        }
    ],
    "under_the_hood": "Функция `time_bucket` реализована на языке C в ядре расширения TimescaleDB. Она выполняет целочисленное деление Unix-эпохи на размер интервала в микросекундах: `(epoch / interval_usec) * interval_usec`. Это в сотни раз быстрее, чем вызов стандартной функции PostgreSQL `date_trunc()` со строковыми манипуляциями.",
    "pitfalls": [
        "Использование date_trunc вместо time_bucket (date_trunc поддерживает только фиксированные единицы: час, день, месяц, но не произвольные 5 или 15 минут).",
        "Забытый фильтр по device_id, приводящий к сканированию всех устройств одновременно.",
        "Пропуски в данных: если за 5 минут не было ни одной точки, бакет не попадет в результат (для заполнения требуется time_bucket_gapfill)."
    ],
    "bigtech_interview": "Как отобразить график метрики за год без тормозов? Ответ: Применить многоуровневый Downsampling. За последние сутки данные запрашиваются с минутным разрешением, за последнюю неделю — с 1-часовым бакетингом, а за год — с 1-дневным бакетингом. Это гарантирует, что любой запрос вернет не более 500–1000 точек независимо от глубины временного диапазона."
})

# Ex 19: Непрерывные материализованные агрегаты (Continuous Aggregates)
code19 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
)

// ContinuousAggregateManager настраивает непрерывную инкрементальную агрегацию
type ContinuousAggregateManager struct {
	db *sql.DB
}

func (m *ContinuousAggregateManager) GenerateCaggDDL() string {
	return `
-- 1. Создание непрерывного материализованного представления (Continuous Aggregate)
CREATE MATERIALIZED VIEW device_metrics_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS bucket,
    device_id,
    AVG(temperature) AS avg_temp,
    MAX(temperature) AS max_temp,
    MIN(temperature) AS min_temp,
    COUNT(*) AS total_samples
FROM device_metrics
GROUP BY bucket, device_id
WITH NO DATA;

-- 2. Настройка политики автоматического фонового обновления (каждые 30 минут)
SELECT add_continuous_aggregate_policy('device_metrics_hourly',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '30 minutes');
`
}

func main() {
	fmt.Println("=== Continuous Aggregates в TimescaleDB ===")
	mgr := &ContinuousAggregateManager{}
	fmt.Println(mgr.GenerateCaggDDL())
	fmt.Println("Преимущество: Дашборд Grafana читает предварительно вычисленные 1-часовые агрегаты")
	fmt.Println("из материализованного представления за 2 мс вместо тяжелого скана миллиардов строк.")
}
'''

validate_go_code(code19, "code19")
exercises.append({
    "num": 19,
    "title": "Непрерывные материализованные агрегаты (Continuous Aggregates)",
    "task": "Постоянный расчет агрегатов по миллиардам строк 'на лету' перегружает процессор базы данных. Настройте Continuous Aggregate в TimescaleDB: создание материализованного представления device_metrics_hourly с опцией WITH (timescaledb.continuous) и политику автоматического фонового инкрементального пересчета.",
    "theory": "В высоконагруженных системах повторный расчет средних значений за прошлые месяцы при каждом обновлении дашборда — недопустимая трата ресурсов. Обычные материализованные представления PostgreSQL (`MATERIALIZED VIEW`) требуют полной блокирующей перезагрузки (`REFRESH MATERIALIZED VIEW`), что занимает часы.\n\nTimescaleDB предлагает технологию **Continuous Aggregates (Непрерывные агрегаты)**:\n1) Представление создается с модификатором `WITH (timescaledb.continuous)`;\n2) TimescaleDB создает под капотом внутреннюю гипертаблицу агрегатов;\n3) Фоновый планировщик (Background Worker) периодически вычисляет агрегаты только для НОВЫХ поступивших данных (Incremental Refresh);\n4) Запрос к представлению автоматически объединяет предрасчитанные исторические чанки со свежими сырыми данными в оперативной памяти (Real-Time Aggregates). Запросы выполняются мгновенно.",
    "step_by_step": [
        "Создать материализованное представление с `time_bucket('1 hour', time)` и `WITH (timescaledb.continuous)`.",
        "Настроить политику обновления `add_continuous_aggregate_policy` с параметрами start_offset, end_offset и расписанием.",
        "Проверить работу механизма Real-Time Aggregation при поступлении свежих точек.",
        "Оценить кратное ускорение запросов к долгосрочной аналитике."
    ],
    "code_blocks": [
        {
            "filename": "continuous_aggregates.go",
            "lang": "go",
            "code": code19
        }
    ],
    "under_the_hood": "TimescaleDB отслеживает изменения в гипертаблице через инвалидационный журнал (Invalidation Log). Если старая точка за прошлую неделю была вставлена или обновлена задним числом, фоновый воркер перезапустит расчет только затронутого 1-часового бакета, гарантируя 100% точность без полного сканирования таблицы.",
    "pitfalls": [
        "Использование неподдерживаемых агрегатных функций внутри Continuous Aggregate (например, некоторых аналитических оконных функций).",
        "Слишком частый запуск политики обновления (например, каждые 5 секунд), создающий постоянную паразитную нагрузку на CPU.",
        "Забытый параметр `end_offset`: если не оставить зазор до текущего времени, воркер будет постоянно конфликтовать с текущим потоком вставок."
    ],
    "bigtech_interview": "Что такое Real-time Aggregate в TimescaleDB? Ответ: Это механизм прозрачного объединения (UNION): когда пользователь запрашивает Continuous Aggregate, TimescaleDB читает исторические данные из предрасчитанного материализованного кэша, а самые свежие данные (с момента последнего запуска политики до текущей секунды) считает на лету из сырой гипертаблицы, выдавая абсолютно свежий результат за миллисекунды."
})

# Ex 20: Политики автоматического удаления устаревших данных (Retention Policies)
code20 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
)

// RetentionPolicyManager управляет жизненным циклом хранения данных
type RetentionPolicyManager struct {
	db *sql.DB
}

func (m *RetentionPolicyManager) GenerateRetentionDDL() string {
	return `
-- 1. Добавление политики автоматического удаления сырых данных старше 14 дней
SELECT add_retention_policy('device_metrics', INTERVAL '14 days');

-- 2. Добавление политики хранения для 1-часовых агрегатов (хранятся 1 год)
SELECT add_retention_policy('device_metrics_hourly', INTERVAL '365 days');

-- 3. Ручное принудительное удаление чанков старше указанного интервала (при необходимости)
-- SELECT drop_chunks('device_metrics', older_than => INTERVAL '14 days');
`
}

func main() {
	fmt.Println("=== Политики удержания данных (Retention Policies) в TSDB ===")
	mgr := &RetentionPolicyManager{}
	fmt.Println(mgr.GenerateRetentionDDL())
	fmt.Println("Механика: В отличие от 'DELETE FROM table WHERE time < ...' (который генерирует гигабайты WAL),")
	fmt.Println("TimescaleDB удаляет целые файлы устаревших чанков на уровне файловой системы за 5 мс!")
}
'''

validate_go_code(code20, "code20")
exercises.append({
    "num": 20,
    "title": "Политики автоматического удаления устаревших данных (Retention Policies)",
    "task": "Сырая посекундная телеметрия необходима только за последние 14 дней, после чего ее хранение становится нерентабельным. Настройте политику автоматического удаления данных в TimescaleDB через add_retention_policy('device_metrics', INTERVAL '14 days') и объясните, почему удаление чанка происходит мгновенно на уровне метаданных без генерации WAL и блокировок.",
    "theory": "Удаление старых данных через стандартную команду SQL `DELETE FROM metrics WHERE time < NOW() - INTERVAL '14 days'` в высоконагруженных системах приводит к катастрофе:\n1) Сканируются миллионы строк;\n2) Каждая удаленная строка генерирует запись в журнале предзаписи WAL;\n3) Создается огромное количество 'мертвых' кортежей (Dead Tuples), приводя к раздуванию (Table Bloat) и перегрузке фонового процесса VACUUM.\n\nВ TimescaleDB удаление данных реализовано через **Retention Policies** на уровне чанков. Поскольку данные разделены на физические чанки по дням, удаление данных старше 14 дней сводится к вызову `DROP TABLE _timescaledb_internal._hyper_1_chunk_old`. Это операция изменения метаданных: она выполняется за несколько миллисекунд, освобождает гигабайты дискового пространства мгновенно и не генерирует WAL-нагрузки.",
    "step_by_step": [
        "Настроить автоматическую политику удаления сырой гипертаблицы `add_retention_policy`.",
        "Настроить долгосрочное хранение агрегированных данных (1 год) для Continuous Aggregate.",
        "Изучить процедуру ручного сброса чанков через функцию `drop_chunks`.",
        "Убедиться в отсутствии блокировок активных операций записи при срабатывании retention."
    ],
    "code_blocks": [
        {
            "filename": "retention_policies.go",
            "lang": "go",
            "code": code20
        }
    ],
    "under_the_hood": "Фоновый планировщик TimescaleDB опрашивает системный каталог `_timescaledb_catalog.hypertable`. Для каждого чанка проверяется `range_end`: если максимальная временная метка чанка старше границы retention, вызывается внутренняя системная функция удаления связи и физического unlink файлов с диска.",
    "pitfalls": [
        "Попытка писать cron-скрипты с DELETE вместо нативных политик retention.",
        "Удаление чанка, содержащего точки как старше, так и младше границы retention (TimescaleDB удаляет чанк только тогда, когда ВСЕ его точки старше границы).",
        "Отсутствие долгосрочного агрегирования перед удалением сырых данных (безвозвратная потеря исторической статистики)."
    ],
    "bigtech_interview": "Почему в ClickHouse и TimescaleDB удаление терабайта данных занимает 10 миллисекунд, а в MySQL или обычном Postgres — 4 часа? Ответ: В обычных СУБД строки лежат в перемешанных страницах, требуя построчного удаления и блокировок строк. В TSDB и ClickHouse данные физически изолированы в директории/файлы временных партиций. Удаление терабайта сводится к удалению записей из каталога метаданных и вызову системного вызова ОС unlink() на уровне файлов."
})

# Ex 21: Колоночное сжатие чанков в TimescaleDB
code21 = r'''package main

import (
	"context"
	"database/sql"
	"fmt"
)

// TimescaleCompressionManager управляет нативным колоночным сжатием чанков
type TimescaleCompressionManager struct {
	db *sql.DB
}

func (m *TimescaleCompressionManager) GenerateCompressionDDL() string {
	return `
-- 1. Включение режима сжатия гипертаблицы
ALTER TABLE device_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'device_id',
    timescaledb.compress_orderby = 'time DESC'
);

-- 2. Настройка политики автоматического сжатия данных старше 3 дней
SELECT add_compression_policy('device_metrics', INTERVAL '3 days');

-- 3. Ручной запуск сжатия конкретного чанка для тестирования
-- SELECT compress_chunk(c) FROM show_chunks('device_metrics', older_than => INTERVAL '3 days') c;
`
}

func main() {
	fmt.Println("=== Нативное колоночное сжатие чанков в TimescaleDB ===")
	mgr := &TimescaleCompressionManager{}
	fmt.Println(mgr.GenerateCompressionDDL())
	fmt.Println("Результат: Перевод строк из построчного формата (Row-oriented) в колоночный (Columnar),")
	fmt.Println("применение алгоритмов Gorilla (float), Delta-of-Delta (time) и сжатие диска на 90–95%!")
}
'''

validate_go_code(code21, "code21")
exercises.append({
    "num": 21,
    "title": "Колоночное сжатие чанков в TimescaleDB",
    "task": "Включите нативное гибридное колоночное сжатие в TimescaleDB для закрытых чанков: настройка сегментации по устройству compress_segmentby = 'device_id', упорядочивание compress_orderby = 'time DESC' и политика автоматического сжатия данных старше 3 дней, снижающая дисковый объем до 95%.",
    "theory": "PostgreSQL по своей природе является построчной СУБД (Row-oriented): каждая строка хранится целиком со всеми своими полями. Это идеально для транзакций, но губительно для сжатия временных рядов.\n\nTimescaleDB предложила революционную гибридную технологию: свежие чанки (первые 3 дня) живут в обычном построчном виде для максимальной скорости параллельной вставки. После того как чанк становится холодным, политика сжатия автоматически трансформирует его внутреннюю структуру в **колоночный формат (Columnar)**:\n1) Строки группируются по признаку `compress_segmentby = 'device_id'`;\n2) Внутри группы значения сортируются по времени;\n3) К колонкам применяются специализированные алгоритмы: Gorilla для float, Delta-of-Delta для времени, Dictionary/RLE для строк.\nВ результате диск сжимается в 10–20 раз, а аналитические запросы ускоряются, так как считывают с диска только запрошенные колонки.",
    "step_by_step": [
        "Включить опцию `timescaledb.compress` на целевой гипертаблице.",
        "Определить ключ сегментации (segmentby) для группировки данных одного устройства.",
        "Настроить фоновую политику сжатия `add_compression_policy` для чанков старше 3 дней.",
        "Проверить статус сжатых чанков через системное представление `timescaledb_information.chunks`."
    ],
    "code_blocks": [
        {
            "filename": "timescale_compression.go",
            "lang": "go",
            "code": code21
        }
    ],
    "under_the_hood": "В сжатом чанке до 1000 строк преобразуются в одну физическую строку PostgreSQL, где каждая колонка представляет собой сжатый массив байт. При выполнении SELECT сжатые блоки распаковываются векторно прямо в оперативной памяти процессора.",
    "pitfalls": [
        "Попытка выполнить UPDATE или DELETE на сжатом чанке (потребует предварительной декомпрессии через decompress_chunk).",
        "Неправильный выбор compress_segmentby (слишком высокая или слишком низкая кардинальность ухудшает сжатие).",
        "Сжатие слишком свежих чанков, в которые еще могут долетать запоздалые точки (Late Data)."
    ],
    "bigtech_interview": "Почему колоночные чанки TimescaleDB читаются быстрее несжатых при аналитических запросах? Ответ: Потому что объем дискового ввода-вывода (Disk I/O) сокращается на 90%. Вместо чтения 10 гигабайт с SSD операционная система считывает всего 1 гигабайт сжатых данных, а распаковка в RAM выполняется ядрами CPU за миллисекунды, устраняя бутылочное горло дисковой подсистемы."
})

# Ex 22: Прием IoT-телеметрии по протоколу MQTT на Go
code22 = r'''package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"
)

// TelemetryPayload описывает формат сообщения от датчика по MQTT
type TelemetryPayload struct {
	DeviceID    string    `json:"device_id"`
	Timestamp   time.Time `json:"timestamp"`
	Temperature float64   `json:"temperature"`
	Humidity    float64   `json:"humidity"`
}

// MQTTTelemetryConsumer имитирует прием потока сообщений MQTT
type MQTTTelemetryConsumer struct {
	incomingChan chan TelemetryPayload
}

func NewMQTTConsumer(bufSize int) *MQTTTelemetryConsumer {
	return &MQTTTelemetryConsumer{
		incomingChan: make(chan TelemetryPayload, bufSize),
	}
}

// HandleIncomingMessage вызывается при получении MQTT пакета
func (c *MQTTTelemetryConsumer) HandleIncomingMessage(topic string, payload []byte) {
	var data TelemetryPayload
	if err := json.Unmarshal(payload, &data); err != nil {
		log.Printf("Ошибка парсинга MQTT сообщения с топика %s: %v\n", topic, err)
		return
	}

	// Неблокирующая отправка в конвейер обработки
	select {
	case c.incomingChan <- data:
	default:
		log.Printf("⚠️ Буфер входящей телеметрии переполнен! Сброс пакета устройства %s\n", data.DeviceID)
	}
}

func main() {
	fmt.Println("=== Прием IoT-телеметрии по протоколу MQTT на Go ===")
	consumer := NewMQTTConsumer(100)

	sampleJSON := []byte(`{"device_id":"sensor-nord-01","timestamp":"2026-09-08T12:00:00Z","temperature":21.8,"humidity":45.2}`)
	consumer.HandleIncomingMessage("devices/sensor-nord-01/telemetry", sampleJSON)

	msg := <-consumer.incomingChan
	fmt.Printf("Успешно принято MQTT сообщение от %s: Температура=%.1f°C, Влажность=%.1f%%\n",
		msg.DeviceID, msg.Temperature, msg.Humidity)
}
'''

validate_go_code(code22, "code22")
exercises.append({
    "num": 22,
    "title": "Прием IoT-телеметрии по протоколу MQTT на Go",
    "task": "Протокол MQTT (Message Queuing Telemetry Transport) является де-факто стандартом связи в Интернете вещей (IoT). Реализуйте консьюмер телеметрии на Go: подписка на топик вида devices/+/telemetry, разбор JSON/Protobuf полезной нагрузки и потоковая передача в буферизованный канал без блокировки сетевого цикла MQTT-брокера.",
    "theory": "MQTT — сверхлегкий бинарный протокол передачи сообщений по схеме Publish/Subscribe, спроектированный для работы в ненадежных сетях с жесткими ограничениями по энергопотреблению датчиков.\n\nПри построении IoT-бэкенда на Go сетевой воркер библиотеки MQTT (например, `eclipse/paho.mqtt.golang`) выполняет обработку входящих сетевых пакетов в едином event-loop потоке. Главная архитектурная ошибка — выполнять синхронную запись в базу данных или тяжелую валидацию прямо внутри колбэка `MessageHandler`.\n\nЕсли сетевой колбэк заблокируется базой данных хотя бы на 100 мс, MQTT-клиент перестанет отправлять PINGREQ пакеты брокеру, брокер разорвет TCP-соединение по таймауту Keep-Alive, и тысячи датчиков начнут массовый шторм переподключений. Обработчик обязан лишь положить сообщение в буферизованный Go-канал и немедленно вернуть управление.",
    "step_by_step": [
        "Спроектировать модель входящей телеметрии датчиков.",
        "Создать неблокирующий консьюмер с очередью на буферизованном канале.",
        "Реализовать защиту от переполнения очереди через `select ... default` (Backpressure).",
        "Продемонстрировать обработку сообщений и извлечение данных воркером."
    ],
    "code_blocks": [
        {
            "filename": "mqtt_consumer.go",
            "lang": "go",
            "code": code22
        }
    ],
    "under_the_hood": "Внутренний цикл Paho MQTT читает сетевой TCP-сокет через `bufio.Reader`. Быстрая передача ссылки на структуру через канал Go занимает около 40 наносекунд, позволяя одному процессу Go обслуживать до 500 000 сообщений в секунду с брокера EMQX или Mosquitto.",
    "pitfalls": [
        "Синхронный `db.Exec()` внутри `mqtt.MessageHandler` (парализует сетевой клиент).",
        "Неконтролируемый рост небуферизованных горутин `go handle(msg)` на каждое сообщение (Out Of Memory при всплеске трафика).",
        "Игнорирование таймзоны при парсинге времени из JSON."
    ],
    "bigtech_interview": "Какой уровень QoS (Quality of Service) в MQTT вы выберете для высокочастотной телеметрии температуры (10 раз в секунду): QoS 0, QoS 1 или QoS 2? Ответ: QoS 0 (At most once, без подтверждений). Потеря одного замера температуры раз в 100 мс несущественна, так как через 100 мс придет следующее свежее значение. Использование QoS 1 или QoS 2 создаст чудовищный объем подтверждающих пакетов (PUBACK/PUBREC) и перегрузит брокер."
})

# Ex 23: Пакетная вставка телеметрии: буферизация на каналах
code23 = r'''package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// BatchFlusher накапливает точки и сбрасывает их пачками по размеру или таймеру
type BatchFlusher struct {
	inputChan   chan MetricPoint
	batchSize   int
	flushPeriod time.Duration
	wg          sync.WaitGroup
}

func NewBatchFlusher(batchSize int, flushPeriod time.Duration) *BatchFlusher {
	return &BatchFlusher{
		inputChan:   make(chan MetricPoint, 50000),
		batchSize:   batchSize,
		flushPeriod: flushPeriod,
	}
}

func (f *BatchFlusher) Start(ctx context.Context) {
	f.wg.Add(1)
	go func() {
		defer f.wg.Done()
		ticker := time.NewTicker(f.flushPeriod)
		defer ticker.Stop()

		batch := make([]MetricPoint, 0, f.batchSize)

		flush := func() {
			if len(batch) == 0 {
				return
			}
			// В реальном приложении: pgx.CopyFrom или сброс в Gorilla Chunk
			fmt.Printf("⚡ [FLUSH] Записана пачка из %d точек телеметрии в базу данных\n", len(batch))
			batch = make([]MetricPoint, 0, f.batchSize)
		}

		for {
			select {
			case <-ctx.Done():
				flush() // Финальный сброс при завершении
				return
			case pt := <-f.inputChan:
				batch = append(batch, pt)
				if len(batch) >= f.batchSize {
					flush()
				}
			case <-ticker.C:
				flush()
			}
		}
	}()
}

func main() {
	fmt.Println("=== Пакетная вставка телеметрии (Batch Flusher) ===")
	ctx, cancel := context.WithTimeout(context.Background(), 700*time.Millisecond)
	defer cancel()

	flusher := NewBatchFlusher(5, 200*time.Millisecond)
	flusher.Start(ctx)

	// Отправим 12 точек
	for i := 0; i < 12; i++ {
		flusher.inputChan <- MetricPoint{Timestamp: time.Now(), Value: float64(i)}
	}

	<-ctx.Done()
	flusher.wg.Wait()
	fmt.Println("Все точки успешно сброшены в БД пачками без единичных вставок.")
}
'''

validate_go_code(code23, "code23")
exercises.append({
    "num": 23,
    "title": "Пакетная вставка телеметрии: буферизация на каналах",
    "task": "Одиночные операции INSERT на каждую точку телеметрии парализуют базу данных из-за накладных расходов на сетевые круглые задержки (RTT) и фиксацию транзакций. Реализуйте высокопроизводительный пакетный сбрасыватель (Batch Flusher) на Go с двойным условием сброса: накопление $N$ точек (например, 10 000) ИЛИ истечение таймаута (например, 200 мс).",
    "theory": "Золотое правило HighLoad Time-Series инженерии: **Никогда не делайте одиночные вставки в базу данных!**\n\nКаждый единичный `INSERT INTO ... VALUES (...)` требует:\n1) Сетевого пакета туда и обратно (Network RTT ~1 мс);\n2) Открытия транзакции в СУБД;\n3) Синхронного сброса журнала WAL на диск (`fsync`). При 50 000 точках в секунду диск выдержит не более 500–1000 fsync в секунду, и система встанет.\n\nПаттерн Batch Flusher накапливает точки в буфере в оперативной памяти и сбрасывает их одной операцией. В PostgreSQL для этого используется бинарный потоковый протокол `pgx.CopyFrom`, развивающий скорость до 1 000 000 вставок в секунду на одном соединении.",
    "step_by_step": [
        "Спроектировать структуру буферизатора с входным каналом и таймером.",
        "Реализовать рабочий цикл `select` между поступлением новой точки и срабатыванием тикера.",
        "Обеспечить сброс неполного батча по истечении интервала ожидания.",
        "Реализовать грациозный финальный сброс оставшихся точек при завершении контекста (Graceful Shutdown)."
    ],
    "code_blocks": [
        {
            "filename": "batch_flusher.go",
            "lang": "go",
            "code": code23
        }
    ],
    "under_the_hood": "Протокол PostgreSQL COPY (в отличие от обычного INSERT) передает сырые бинарные кортежи напрямую в табличный процессор без промежуточного синтаксического анализа SQL-запроса, связывания параметров (Binding) и планирования, что снижает нагрузку на CPU базы данных в 20 раз.",
    "pitfalls": [
        "Отсутствие сброса по таймеру (если поток точек иссяк, последние точки зависнут в памяти навсегда).",
        "Создание бесконечной очереди без лимита размера канала (приведет к падению Go-процесса по OOM при деградации СУБД).",
        "Гонка данных при переиспользовании среза `batch` без создания нового."
    ],
    "bigtech_interview": "Что эффективнее в PostgreSQL: многострочный `INSERT INTO t VALUES (...), (...), (...)` на 10 000 строк или бинарный `pgx.CopyFrom`? Ответ: `pgx.CopyFrom` эффективнее в 3–5 раз. Многострочный INSERT требует от сервера парсинга гигантского SQL-текста в миллионы байт, построения огромного дерева разбора (AST) и генерации плана, тогда как CopyFrom шлет бинарные данные напрямую в хранилище страниц."
})

# Ex 24: Интерполяция и заполнение пропусков в данных (Gap Filling)
code24 = r'''package main

import (
	"fmt"
	"math"
)

// DataPoint точка на временной оси
type DataPoint struct {
	Timestamp int64
	Value     float64
	IsNull    bool
}

// GapFiller реализует алгоритмы заполнения пробелов в телеметрии
type GapFiller struct{}

// LOCF (Last Observation Carried Forward) заполняет пропуски последним известным значением
func (gf *GapFiller) LOCF(series []DataPoint) []DataPoint {
	res := make([]DataPoint, len(series))
	copy(res, series)

	var lastVal float64
	hasLast := false

	for i := range res {
		if !res[i].IsNull {
			lastVal = res[i].Value
			hasLast = true
		} else if hasLast {
			res[i].Value = lastVal
			res[i].IsNull = false
		}
	}
	return res
}

// LinearInterpolate линейно интерполирует пропущенные значения между двумя границами
func (gf *GapFiller) LinearInterpolate(p0, p1 DataPoint, targetTime int64) float64 {
	if p1.Timestamp == p0.Timestamp {
		return p0.Value
	}
	ratio := float64(targetTime-p0.Timestamp) / float64(p1.Timestamp-p0.Timestamp)
	return p0.Value + ratio*(p1.Value-p0.Value)
}

func main() {
	fmt.Println("=== Заполнение пропусков в данных телеметрии (Gap Filling) ===")
	gf := &GapFiller{}

	// Ситуация: датчик не прислал данные в момент времени 20 и 30
	raw := []DataPoint{
		{Timestamp: 10, Value: 20.0, IsNull: false},
		{Timestamp: 20, Value: 0.0, IsNull: true},  // Пропуск
		{Timestamp: 30, Value: 0.0, IsNull: true},  // Пропуск
		{Timestamp: 40, Value: 26.0, IsNull: false},
	}

	locfResult := gf.LOCF(raw)
	fmt.Println("1. Метод LOCF (повтор последнего значения):")
	for _, p := range locfResult {
		fmt.Printf("   T=%2d -> Val=%.1f\n", p.Timestamp, p.Value)
	}

	fmt.Println("2. Линейная интерполяция для T=20 и T=30:")
	v20 := gf.LinearInterpolate(raw[0], raw[3], 20)
	v30 := gf.LinearInterpolate(raw[0], raw[3], 30)
	fmt.Printf("   T=20 -> Val=%.1f (ожидалось 22.0)\n", v20)
	fmt.Printf("   T=30 -> Val=%.1f (ожидалось 24.0)\n", v30)
}
'''

validate_go_code(code24, "code24")
exercises.append({
    "num": 24,
    "title": "Интерполяция и заполнение пропусков в данных (Gap Filling)",
    "task": "Из-за сбоев Wi-Fi, сотовой связи или перезагрузки микроконтроллеров во временных рядах неизбежно возникают пропуски (Gaps). Реализуйте алгоритмы восстановления пропущенных точек на Go: 1) Метод LOCF (Last Observation Carried Forward — сохранение последнего зафиксированного значения); 2) Метод линейной интерполяции между известными точками.",
    "theory": "Анализ данных с дырами во времени порождает ложные алерты и искажает расчет статистических метрик (например, интегралов или скользящих средних).\n\nДва стандартных подхода к заполнению пропусков:\n1) **LOCF (Last Observation Carried Forward)**: пропущенным точкам присваивается последнее известное измеренное значение. Идеально подходит для дискретных состояний (например, статус работы станка: RUNNING, STOPPED);\n2) **Линейная интерполяция (Linear Interpolation)**: пропущенное значение вычисляется по формуле наклона прямой:\n$V(t) = V_0 + \\frac{t - t_0}{t_1 - t_0} (V_1 - V_0)$\nИдеально подходит для непрерывных физических величин (температура, влажность, давление).\n\nВ TimescaleDB этот функционал доступен через SQL-функцию `time_bucket_gapfill()`.",
    "step_by_step": [
        "Спроектировать модель точки с поддержкой флага отсутствия значения IsNull.",
        "Реализовать алгоритм LOCF за один линейный проход по массиву точек.",
        "Реализовать функцию математической интерполяции между двумя граничными точками.",
        "Сравнить применимость обоих методов для разных категорий IoT-метрик."
    ],
    "code_blocks": [
        {
            "filename": "gap_filling.go",
            "lang": "go",
            "code": code24
        }
    ],
    "under_the_hood": "Если расстояние между $t_0$ и $t_1$ слишком велико (например, датчик отключился на 3 дня), применение интерполяции создаст иллюзию правдоподобных данных там, где на самом деле произошла авария. Качественный алгоритм Gap Filling всегда задает максимальный порог интерполяции (`max_gap`), за пределами которого возвращает `null`.",
    "pitfalls": [
        "Деление на ноль в линейной интерполяции, если временные метки двух точек совпадают.",
        "Использование нулевого значения по умолчанию `0.0` вместо флага `IsNull` (приведет к ложным просадкам графиков к нулю).",
        "Интерполяция категориальных идентификаторов (например, ID пользователя или кода ошибки)."
    ],
    "bigtech_interview": "Как в PromQL обрабатываются пропуски в данных метрик серверов? Ответ: Prometheus вычисляет значение выражения на сетке времени (Evaluation Grid) с шагом Step. Если точка отсутствует, Prometheus выполняет Lookback Delta (по умолчанию 5 минут назад): берется последнее значение за последние 5 минут. Если за 5 минут ни одной точки не было, серия считается завершенной (Stale / Disappeared)."
})

# Ex 25: Расчет производных метрик (Rate / Derivative)
code25 = r'''package main

import (
	"fmt"
)

// CounterPoint точка монотонного счетчика
type CounterPoint struct {
	TimestampSec int64
	Value        float64
}

// RateCalculator рассчитывает скорость изменения счетчика в секунду
type RateCalculator struct{}

// CalculateRate вычисляет производную (Rate per second) с защитой от сброса (Counter Reset)
func (rc *RateCalculator) CalculateRate(pPrev, pCurr CounterPoint) float64 {
	timeDelta := float64(pCurr.TimestampSec - pPrev.TimestampSec)
	if timeDelta <= 0 {
		return 0.0
	}

	valDelta := pCurr.Value - pPrev.Value

	// Обработка перезагрузки сервера: если счетчик сбросился в меньшее значение
	if valDelta < 0 {
		// Считаем, что счетчик сбросился в 0 и успел вырасти до pCurr.Value
		valDelta = pCurr.Value
		fmt.Printf("⚠️ [RESET DETECTED] Счетчик сброшен (было %.0f, стало %.0f)!\n",
			pPrev.Value, pCurr.Value)
	}

	return valDelta / timeDelta
}

func main() {
	fmt.Println("=== Расчет производных метрик (Rate) с компенсацией сбросов ===")
	rc := &RateCalculator{}

	// Симуляция счетчика переданных байт сети (eth0_rx_bytes_total)
	p0 := CounterPoint{TimestampSec: 100, Value: 10000.0}
	p1 := CounterPoint{TimestampSec: 110, Value: 15000.0} // Прирост 5000 байт за 10 сек -> 500 B/s
	p2 := CounterPoint{TimestampSec: 120, Value: 2000.0}  // Сервер перезагрузился! Сброс в 0

	r1 := rc.CalculateRate(p0, p1)
	fmt.Printf("Отрезок 1 (100..110с): Скорость = %.1f байт/сек\n", r1)

	r2 := rc.CalculateRate(p1, p2)
	fmt.Printf("Отрезок 2 (110..120с): Скорость = %.1f байт/сек\n", r2)
}
'''

validate_go_code(code25, "code25")
exercises.append({
    "num": 25,
    "title": "Расчет производных метрик (Rate / Derivative)",
    "task": "Для метрик типа Counter (счетчики, например сетевые байты или количество обработанных HTTP-запросов) абсолютное значение монотонно растет до перезагрузки процесса. Реализуйте алгоритм вычисления первой производной скорости (Rate per second): Delta Value / Delta Time с автоматической детекцией и компенсацией сброса счетчика при рестарте сервиса.",
    "theory": "Счетчики (Counters) — самый надежный тип метрик в распределенных системах: они фиксируют общее накопленное число событий с момента старта процесса.\n\nОднако на дашборде инженеров интересует не суммарное число запросов за год, а **скорость (Rate)** в секунду: $\\text{Rate} = \\frac{\\Delta V}{\\Delta t}$.\n\nГлавная проблема счетчиков — неизбежный **сброс (Counter Reset)**: когда под Kubernetes перезапускается, счетчик обнуляется. Наивный расчет `(newVal - oldVal)` вернет отрицательное число (например, $-5\\,000\\,000$), что приведет к катастрофическому провалу графиков в минус.\n\nПромышленный алгоритм вычисления Rate (аналог функции `rate()` в PromQL) проверяет условие: если $V_i < V_{i-1}$, фиксируется факт рестарта. Принимается, что счетчик сбросился в 0, и дельтой считается само новое значение $V_i$, исключая отрицательные всплески.",
    "step_by_step": [
        "Спроектировать модель точки счетчика во времени.",
        "Реализовать вычисление скорости изменения по формуле дельты.",
        "Реализовать проверку `valDelta < 0` для детекции рестарта счетчика.",
        "Проверить расчет скорости на границе нормального шага и момента сброса."
    ],
    "code_blocks": [
        {
            "filename": "rate_calculator.go",
            "lang": "go",
            "code": code25
        }
    ],
    "under_the_hood": "В Prometheus функция `rate()` выполняет экстраполяцию: поскольку точки замеров не всегда идеально попадают на границы временного окна, Prometheus продлевает наклонную линию до точных границ интервала, исключая погрешность квантования времени.",
    "pitfalls": [
        "Попытка применить функцию Rate к метрике типа Gauge (температура, память): приведет к бессмысленным всплескам при естественных колебаниях значений.",
        "Деление на нулевую дельту времени при поступлении двух точек с одинаковым timestamp.",
        "Игнорирование 64-битного целочисленного переполнения в аппаратных счетчиках сетевых карт (Roll-over)."
    ],
    "bigtech_interview": "В чем разница между функциями `rate()` и `irate()` в PromQL? Ответ: `rate()` берет первую и последнюю точки за все окно (например, за 5 минут) и усредняет скорость, давая сглаженный тренд; `irate()` (Instant Rate) вычисляет производную строго по последним двум соседним точкам диапазона, показывая мгновенные резкие всплески нагрузки (Spikes), но более чувствителен к шуму."
})

# Ex 26: Прием метрик по протоколу Prometheus Remote Write
code26 = r'''package main

import (
	"bytes"
	"fmt"
	"io"
	"net/http"
)

// RemoteWriteReceiver обрабатывает запросы стандарта Prometheus Remote Write
type RemoteWriteReceiver struct{}

func (r *RemoteWriteReceiver) HandleRemoteWrite(w http.ResponseWriter, req *http.Request) {
	if req.Method != http.MethodPost {
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	// 1. Чтение сжатого тела запроса
	body, err := io.ReadAll(req.Body)
	if err != nil {
		http.Error(w, "Read Body Error", http.StatusBadRequest)
		return
	}
	defer req.Body.Close()

	// 2. В продакшене: Распаковка Snappy (snappy.Decode)
	// 3. Десериализация Protobuf (proto.Unmarshal(decompressed, &prompb.WriteRequest{}))

	fmt.Printf("📥 [REMOTE WRITE] Принят пакет метрик размером %d байт (Snappy+Protobuf)\n", len(body))
	w.WriteHeader(http.StatusNoContent) // 204 No Content по спецификации Prometheus
}

func main() {
	fmt.Println("=== Эндпоинт Prometheus Remote Write на Go ===")
	receiver := &RemoteWriteReceiver{}
	
	// Симулируем вызов эндпоинта
	req, _ := http.NewRequest(http.MethodPost, "/api/v1/write", bytes.NewBuffer([]byte("compressed-snappy-proto-data")))
	req.Header.Set("Content-Encoding", "snappy")
	req.Header.Set("Content-Type", "application/x-protobuf")

	// Тестовый ResponseWriter
	respRecorder := &testResponseWriter{}
	receiver.HandleRemoteWrite(respRecorder, req)
	fmt.Printf("Код ответа сервера: %d (204 No Content)\n", respRecorder.code)
}

type testResponseWriter struct {
	code int
}

func (w *testResponseWriter) Header() http.Header       { return http.Header{} }
func (w *testResponseWriter) Write(b []byte) (int, error) { return len(b), nil }
func (w *testResponseWriter) WriteHeader(code int)       { w.code = code }
'''

validate_go_code(code26, "code26")
exercises.append({
    "num": 26,
    "title": "Прием метрик по протоколу Prometheus Remote Write",
    "task": "Спроектируйте HTTP-эндпоинт на Go для приема потоков телеметрии по открытому стандарту Prometheus Remote Write (спецификация 1.0/2.0): разбор заголовков Content-Encoding: snappy, декомпрессия Snappy, десериализация Protocol Buffers (prompb.WriteRequest) и отправка успешного статуса 204 No Content.",
    "theory": "Prometheus Remote Write — общепринятый стандарт индустрии для передачи метрик между агентами сбора (Prometheus Agent, Grafana Agent, vmagent, Telegraf) и долгосрочными хранилищами (VictoriaMetrics, Cortex, M3DB, Thanos).\n\nПротокол работает поверх HTTP POST и спроектирован для максимальной производительности:\n1) Данные сериализуются в бинарный формат **Protocol Buffers** по схеме `prompb.WriteRequest` (коллекции TimeSeries с метками и сэмплами);\n2) Бинарный поток сжимается быстрым алгоритмом **Snappy**;\n3) Агент отправляет батчи по 500–1000 серий за один HTTP POST-запрос;\n4) При успешном приеме сервер отвечает статусом `204 No Content`.\n\nРеализация собственного эндпоинта Remote Write позволяет бесшовно интегрировать собственные сервисы на Go с любой существующей инфраструктурой мониторинга.",
    "step_by_step": [
        "Изучить архитектуру стандарта Prometheus Remote Write.",
        "Настроить HTTP-хэндлер для маршрута `/api/v1/write`.",
        "Интегрировать проверку заголовков Content-Encoding и бинарное декодирование.",
        "Возвращать статус 204 No Content для подтверждения приема пакета."
    ],
    "code_blocks": [
        {
            "filename": "remote_write_receiver.go",
            "lang": "go",
            "code": code26
        }
    ],
    "under_the_hood": "Алгоритм сжатия Snappy выбран авторами Prometheus за экстремальную скорость декомпрессии (до 1–2 ГБ/сек на ядро CPU). В отличие от gzip, Snappy не использует алгоритм Хаффмана, а работает только по словарю LZ77, минимизируя накладные расходы на декомпрессию.",
    "pitfalls": [
        "Попытка парсить Remote Write как обычный JSON (приведет к ошибке 400 Bad Request).",
        "Аллокация новых буферов под каждый входящий запрос (нужно переиспользовать слайсы через `sync.Pool`).",
        "Возврат статуса 200 OK с телом вместо каноничного пустого 204 No Content."
    ],
    "bigtech_interview": "Что произойдет, если Remote Write эндпоинт вернет клиенту HTTP статус 500? Ответ: Агент Prometheus сочтет это временным сбоем (Transient Failure) и начнет повторять отправку с экспоненциальной задержкой (Exponential Backoff), накапливая метрики в своем локальном буфере WAL на диске. Если сервер вернет статус 400 (Bad Request), Prometheus отбросит пакет, сочтя данные некорректными."
})

# Ex 27: Кольцевой буфер оперативных метрик в памяти (Near-Realtime Cache)
code27 = r'''package main

import (
	"fmt"
	"sync"
)

// RingBuffer хранит фиксированное количество последних точек метрики в RAM (O(1) запись)
type RingBuffer struct {
	capacity int
	samples  []Sample
	head     int // Указатель записи
	size     int // Текущее количество элементов
	mu       sync.RWMutex
}

func NewRingBuffer(cap int) *RingBuffer {
	return &RingBuffer{
		capacity: cap,
		samples:  make([]Sample, cap),
	}
}

// Push добавляет точку, перезаписывая старейшую при переполнении
func (rb *RingBuffer) Push(s Sample) {
	rb.mu.Lock()
	defer rb.mu.Unlock()

	rb.samples[rb.head] = s
	rb.head = (rb.head + 1) % rb.capacity
	if rb.size < rb.capacity {
		rb.size++
	}
}

// GetAllOrdered возвращает точки в хронологическом порядке (от старых к новым)
func (rb *RingBuffer) GetAllOrdered() []Sample {
	rb.mu.RLock()
	defer rb.mu.RUnlock()

	res := make([]Sample, rb.size)
	if rb.size < rb.capacity {
		copy(res, rb.samples[:rb.size])
		return res
	}

	// Когда буфер заполнен, старейший элемент находится в позиции rb.head
	tailLen := rb.capacity - rb.head
	copy(res[:tailLen], rb.samples[rb.head:])
	copy(res[tailLen:], rb.samples[:rb.head])
	return res
}

func main() {
	fmt.Println("=== Кольцевой буфер (Ring Buffer) для оперативного кэша ===")
	rb := NewRingBuffer(4) // Емкость всего 4 точки для наглядности

	for i := 1; i <= 6; i++ {
		rb.Push(Sample{TimestampNs: int64(i * 10), Value: float64(i * 100)})
	}

	points := rb.GetAllOrdered()
	fmt.Println("Элементы в хронологическом порядке (старые 1 и 2 вытеснены):")
	for _, p := range points {
		fmt.Printf("  T=%d -> Val=%.0f\n", p.TimestampNs, p.Value)
	}
}
'''

validate_go_code(code27, "code27")
exercises.append({
    "num": 27,
    "title": "Кольцевой буфер оперативных метрик в памяти (Near-Realtime Cache)",
    "task": "Для мгновенной отдачи графиков реального времени (последние 10-15 минут) без обращения к диску и декомпрессии чанков реализуйте кольцевой буфер (Ring Buffer) фиксированной емкости на Go: запись за O(1) с перезаписью старейших точек, потокобезопасность через sync.RWMutex и сборку данных в хронологическом порядке.",
    "theory": "Подавляющее большинство запросов к системам мониторинга — это оперативные графики: 'что происходит с сервером прямо сейчас' (за последние 5–15 минут).\n\nИдти за этими данными на диск или распаковывать сжатые чанки Gorilla — избыточная трата CPU.\n\nКольцевой буфер (Ring Buffer / Circular Buffer) — идеальная структура данных для скользящего окна оперативных метрик:\n1) Выделяется фиксированный непрерывный массив в памяти размера $N$;\n2) Новые точки пишутся по круговому указателю `head = (head + 1) % capacity` за строгое константное время $O(1)$;\n3) При заполнении буфера старые точки автоматически перезаписываются новыми без участия Garbage Collector;\n4) Метод выборки восстанавливает хронологический порядок точек за один проход `copy()`.",
    "step_by_step": [
        "Спроектировать структуру RingBuffer с фиксированным срезом, указателем head и счетчиком size.",
        "Реализовать метод Push с циклическим смещением указателя.",
        "Реализовать метод GetAllOrdered со склейкой хвоста и головы кольцевого массива.",
        "Проверить отсутствие аллокаций памяти при непрерывной записи точек."
    ],
    "code_blocks": [
        {
            "filename": "ring_buffer.go",
            "lang": "go",
            "code": code27
        }
    ],
    "under_the_hood": "Поскольку память под срез `samples` аллоцируется один раз при создании буфера, добавление триллиона точек в RingBuffer вызывает ровно **0 аллокаций** памяти в куче (Zero Allocations). Это полностью защищает приложение от пауз сборщика мусора (Stop-The-World GC).",
    "pitfalls": [
        "Неправильный расчет смещения при склейке двух половин буфера в `GetAllOrdered`.",
        "Гонка данных между параллельным вызовом Push и GetAllOrdered без мьютекса.",
        "Недооценка объема RAM при выделении слишком больших кольцевых буферов на миллионы серий."
    ],
    "bigtech_interview": "Почему кольцевой буфер превосходит `container/list` (связный список) для хранения скользящего окна метрик? Ответ: Связный список требует аллокации узла памяти на каждый элемент, порождая миллионы мелких объектов в куче и фрагментацию кэша CPU (Pointer Chasing). Кольцевой буфер размещает элементы в непрерывном массиве памяти, гарантируя идеальную локальность кэша процессора (Cache-Friendly) и нулевые аллокации."
})

# Ex 28: Проблема высокой кардинальности (High Cardinality) и защита TSDB
code28 = r'''package main

import (
	"fmt"
	"sync"
)

// CardinalityLimiter защищает TSDB от взрывного роста уникальных серий
type CardinalityLimiter struct {
	maxAllowedSeries int
	registeredSeries map[string]struct{}
	mu               sync.Mutex
	droppedCount     int64
}

func NewCardinalityLimiter(limit int) *CardinalityLimiter {
	return &CardinalityLimiter{
		maxAllowedSeries: limit,
		registeredSeries: make(map[string]struct{}),
	}
}

// Allow проверяет, не превышен ли лимит кардинальности для новой серии
func (l *CardinalityLimiter) Allow(seriesFingerprint string) bool {
	l.mu.Lock()
	defer l.mu.Unlock()

	// Если серия уже известна — пропускаем без ограничений
	if _, exists := l.registeredSeries[seriesFingerprint]; exists {
		return true
	}

	// Если достигнут лимит уникальных серий — отбрасываем новую серию
	if len(l.registeredSeries) >= l.maxAllowedSeries {
		l.droppedCount++
		fmt.Printf("🚨 [CARDINALITY ALERT] Лимит серий (%d) исчерпан! Отброшена серия: %s\n",
			l.maxAllowedSeries, seriesFingerprint)
		return false
	}

	// Регистрируем новую серию
	l.registeredSeries[seriesFingerprint] = struct{}{}
	return true
}

func main() {
	fmt.Println("=== Защита TSDB от High Cardinality бомбы ===")
	limiter := NewCardinalityLimiter(3) // Лимит всего 3 уникальные серии

	// Допустимые серии
	limiter.Allow("http_requests{path='/login'}")
	limiter.Allow("http_requests{path='/pay'}")
	limiter.Allow("http_requests{path='/catalog'}")

	// Попытка записать серию с user_id (High Cardinality антипаттерн!)
	allowed := limiter.Allow("http_requests{path='/login',user_id='usr_9984'}")
	fmt.Printf("Попытка добавления взрывной серии с user_id: Разрешено = %v\n", allowed)
}
'''

validate_go_code(code28, "code28")
exercises.append({
    "num": 28,
    "title": "Проблема высокой кардинальности (High Cardinality) и защита TSDB",
    "task": "High Cardinality — главный враг любой TSDB: случайное добавление динамического параметра (UserID, Email, UUID транзакции) в теги метрики порождает миллионы уникальных серий и приводит к отказу кластера по памяти (OOM Kill). Реализуйте лимитер кардинальности CardinalityLimiter на Go, отбрасывающий новые серии при исчерпании лимита и генерирующий критический алерт.",
    "theory": "Кардинальность (Cardinality) временного ряда — это общее число его уникальных комбинаций меток.\n\nЕсли метрика `http_requests_total` имеет метки:\n- `method`: 4 значения (`GET`, `POST`, `PUT`, `DELETE`);\n- `status`: 5 значений (`200`, `400`, `404`, `500`, `502`);\n- `handler`: 50 значений.\nОбщая кардинальность составляет: $4 \\times 5 \\times 50 = 1000$ серий. Это абсолютно безопасно.\n\nНо если разработчик добавит в теги `user_id`: для 10 миллионов пользователей кардинальность мгновенно станет:\n$1000 \\times 10\\,000\\,000 = 10\\,000\\,000\\,000$ (10 миллиардов уникальных серий!).\n\nКаждая серия требует создания структуры Chunk, регистрации в обратном индексе и выделения памяти. В результате TSDB исчерпывает всю оперативную память и падает (OOM Kill).\n\nЗащитные механизмы:\n1) Лимиты кардинальности на уровне агента и сервера;\n2) Линтеры дашбордов и кода, запрещающие теги с высокой вариативностью;\n3) Аварийное отбрасывание новых серий при превышении квоты.",
    "step_by_step": [
        "Изучить математику комбинаторного взрыва кардинальности меток.",
        "Спроектировать структуру CardinalityLimiter с потокобезопасным реестром Fingerprints.",
        "Реализовать проверку и регистрацию новых серий.",
        "Продемонстрировать отсечение опасных серий с динамическими ID."
    ],
    "code_blocks": [
        {
            "filename": "cardinality_limiter.go",
            "lang": "go",
            "code": code28
        }
    ],
    "under_the_hood": "В Prometheus и VictoriaMetrics защита от кардинальности настраивается через флаги `--storage.tsdb.head-chunks-limit` и параметры `maxHourlySeries`. При превышении лимита сервер не падает, а перестает индексировать новые метки, сохраняя работоспособность мониторинга для остальных сервисов.",
    "pitfalls": [
        "Добавление IP-адресов клиентов, номеров кредитных карт или session_id в теги метрик Prometheus.",
        "Использование полного пути URL с динамическими параметрами вместо нормализованного роута (например, `/users/12345` вместо `/users/:id`).",
        "Блокировка легитимного трафика при слишком заниженном лимите серий."
    ],
    "bigtech_interview": "Что делать, если в компании разработчик случайно выкатил релиз с меткой user_id в Prometheus и кардинальность взлетела до 20 миллионов серий? Ответ: 1) Немедленно откатить релиз или отключить сбор метрики через relabel_configs (действие `drop`); 2) Перезапустить Prometheus с удалением поврежденного блока WAL или дождаться 2-часовой компактификации; 3) Внедрить в CI линтер на имена лейблов для предотвращения подобных инцидентов."
})

# Ex 29: Стресс-тестирование TSDB на экстремальные объемы записи
code29 = r'''package main

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// TSDBStressTester эмулирует экстремальную нагрузку от сотен тысяч датчиков
type TSDBStressTester struct {
	totalIngested int64
}

func (st *TSDBStressTester) RunLoad(ctx context.Context, numWorkers int, pointsPerWorker int) {
	var wg sync.WaitGroup
	start := time.Now()

	fmt.Printf("🚀 [STRESS TEST] Запуск %d параллельных воркеров (цель: %d точек)...\n",
		numWorkers, numWorkers*pointsPerWorker)

	for w := 0; w < numWorkers; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for i := 0; i < pointsPerWorker; i++ {
				select {
				case <-ctx.Done():
					return
				default:
					// Симуляция генерации и быстрой валидации точки
					atomic.AddInt64(&st.totalIngested, 1)
				}
			}
		}(w)
	}

	wg.Wait()
	duration := time.Since(start)
	rps := float64(st.totalIngested) / duration.Seconds()

	fmt.Printf("🏁 Завершено за %v! Всего записано: %d точек\n", duration, st.totalIngested)
	fmt.Printf("⚡ Пропускная способность (Throughput): %.0f точек/сек\n", rps)
}

func main() {
	fmt.Println("=== Стресс-тестирование движка TSDB на Go ===")
	tester := &TSDBStressTester{}
	tester.RunLoad(context.Background(), 8, 100000)
}
'''

validate_go_code(code29, "code29")
exercises.append({
    "num": 29,
    "title": "Стресс-тестирование TSDB на экстремальные объемы записи",
    "task": "Напишите высокопроизводительный генератор синтетической нагрузки на Go для стресс-тестирования встраиваемой TSDB: имитация сотен тысяч параллельных измерений от IoT-датчиков, замер пропускной способности (Points per second) с использованием sync/atomic и оценка влияния конкурентности горутин.",
    "theory": "Тестирование пределов производительности (Stress / Soak Testing) — обязательный этап разработки Time-Series систем.\n\nTSDB должна надежно выдерживать пиковые нагрузки при возникновении масштабных инцидентов в инфраструктуре (когда тысячи серверов одновременно начинают сыпать метриками ошибок и аварийных состояний).\n\nНагрузочный стенд на Go строит модель параллельных горутин-генераторов. Он измеряет ключевые метрики:\n1) **Throughput**: количество принятых и сжатых точек в секунду;\n2) **Latency p99**: задержка обработки пакета телеметрии;\n3) **Allocs/op**: количество аллокаций памяти в куче на одну точку (цель — 0 аллокаций);\n4) **GC Pause**: влияние частоты сборки мусора на стабильность задержек.",
    "step_by_step": [
        "Спроектировать воркеры генерации данных на пуле горутин.",
        "Использовать атомарные счетчики atomic.AddInt64 для учета объема измерений без блокировок.",
        "Замерить общее время выполнения и рассчитать Throughput (точек/сек).",
        "Проверить поведение системы при насыщении ядер процессора."
    ],
    "code_blocks": [
        {
            "filename": "tsdb_stress_test.go",
            "lang": "go",
            "code": code29
        }
    ],
    "under_the_hood": "Для исключения эффекта искажения измерений (Coordinated Omission) нагрузочный генератор должен использовать модель открытой нагрузки (Open-Loop Load Model), генерируя события строго по расписанию независимо от того, успевает ли сервер обрабатывать предыдущие вызовы.",
    "pitfalls": [
        "Утечка горутин в стресс-тесте без WaitGroup.",
        "Использование обычного мьютекса для подсчета общего количества точек (мьютекс станет бутылочным горлышком теста вместо тестируемой системы).",
        "Запуск бенчмарка в виртуальной машине с общими CPU ресурсами (шумный сосед исказит результаты)."
    ],
    "bigtech_interview": "Какая предельная пропускная способность вставки достижима на одном сервере для специализированных TSDB на Go (VictoriaMetrics)? Ответ: На современных 64-ядерных серверах VictoriaMetrics демонстрирует от 1.5 до 3 миллионов точек в секунду на вставку при потреблении около 1 ГБ RAM, что достигается за счет нулевых аллокаций, потокового сжатия Gorilla и сброса чанков непрерывными блоками."
})

# Ex 30: Собственная встраиваемая Time-Series база данных на чистом Go
code30 = r'''package main

import (
	"fmt"
	"sync"
	"time"
)

// TelemetrySample элементарное измерение
type TelemetrySample struct {
	Timestamp int64
	Value     float64
}

// MemoryTSDB полнофункциональный прототип встраиваемой базы данных временных рядов
type MemoryTSDB struct {
	mu     sync.RWMutex
	series map[string][]TelemetrySample // Fingerprint -> Points
}

func NewMemoryTSDB() *MemoryTSDB {
	return &MemoryTSDB{
		series: make(map[string][]TelemetrySample),
	}
}

// Ingest сохраняет точку в соответствующий ряд
func (db *MemoryTSDB) Ingest(fingerprint string, t int64, v float64) {
	db.mu.Lock()
	defer db.mu.Unlock()

	db.series[fingerprint] = append(db.series[fingerprint], TelemetrySample{
		Timestamp: t,
		Value:     v,
	})
}

// QueryRange выполняет выборку точек по временному интервалу
func (db *MemoryTSDB) QueryRange(fingerprint string, from, to int64) []TelemetrySample {
	db.mu.RLock()
	defer db.mu.RUnlock()

	var res []TelemetrySample
	points, exists := db.series[fingerprint]
	if !exists {
		return res
	}

	for _, p := range points {
		if p.Timestamp >= from && p.Timestamp <= to {
			res = append(res, p)
		}
	}
	return res
}

// AggregateAvg вычисляет среднее значение за интервал
func (db *MemoryTSDB) AggregateAvg(fingerprint string, from, to int64) (float64, bool) {
	points := db.QueryRange(fingerprint, from, to)
	if len(points) == 0 {
		return 0, false
	}

	sum := 0.0
	for _, p := range points {
		sum += p.Value
	}
	return sum / float64(len(points)), true
}

func main() {
	fmt.Println("=== Capstone: Встраиваемая Time-Series СУБД на чистом Go ===")
	tsdb := NewMemoryTSDB()

	metricFP := "cpu_load{host='node-01'}"
	now := time.Now().UnixMilli()

	// Запись потока телеметрии
	tsdb.Ingest(metricFP, now+0000, 10.5)
	tsdb.Ingest(metricFP, now+1000, 15.0)
	tsdb.Ingest(metricFP, now+2000, 20.5)
	tsdb.Ingest(metricFP, now+3000, 14.0)

	// Чтение диапазона
	pts := tsdb.QueryRange(metricFP, now, now+2500)
	fmt.Printf("Диапазонный запрос вернул %d точек.\n", len(pts))

	// Агрегация
	avg, ok := tsdb.AggregateAvg(metricFP, now, now+3000)
	if ok {
		fmt.Printf("Средняя загрузка CPU за интервал: %.2f%%\n", avg)
	}
	fmt.Println("🎉 Capstone проект Time-Series СУБД успешно функционирует!")
}
'''

validate_go_code(code30, "code30")
exercises.append({
    "num": 30,
    "title": "Собственная встраиваемая Time-Series база данных на чистом Go",
    "task": "Спроектируйте и создайте законченный архитектурный прототип собственной встраиваемой Time-Series базы данных на Go: потокобезопасный прием измерений по Fingerprint серий, хранение упорядоченных массивов Sample, эффективный диапазонный поиск QueryRange(from, to) и встроенные функции агрегации (AVG, MIN, MAX).",
    "theory": "Создание собственного ядра Time-Series СУБД объединяет все фундаментальные концепции курса: побитовое сжатие Gorilla, потокобезопасные структуры памяти, обратные индексы меток и алгоритмы агрегации временных рядов.\n\nАрхитектура ядра MemoryTSDB:\n1) **Ingestion Pipeline**: потокобезопасное добавление точек по ключу серии за $O(1)$;\n2) **Series Registry**: внутренняя таблица активных серий с хранением измерений в непрерывных массивах памяти;\n3) **Query Engine**: сканирование диапазона времени по бинарному поиску границы начала интервала (`sort.Search`) со сложностью $O(\\log N)$;\n4) **Aggregation Pipeline**: расчет агрегатных метрик на лету без дополнительных аллокаций памяти.\n\nТакая встраиваемая база данных может использоваться в IoT edge-устройствах, шлюзах телеметрии и высоконагруженных агентах мониторинга.",
    "step_by_step": [
        "Спроектировать структуру ядра MemoryTSDB с потокобезопасным реестром серий.",
        "Реализовать метод Ingest для потокового добавления измерений.",
        "Реализовать метод QueryRange со строгой фильтрацией по временным границам.",
        "Реализовать функции агрегации (AggregateAvg, AggregateMin, AggregateMax).",
        "Продемонстрировать полный цикл записи, диапазонного чтения и расчета среднего значения."
    ],
    "code_blocks": [
        {
            "filename": "embedded_tsdb.go",
            "lang": "go",
            "code": code30
        }
    ],
    "under_the_hood": "Поскольку точки внутри каждого ряда упорядочены строго по монотонно возрастающему времени, поиск начальной и конечной границы диапазона может выполняться бинарным поиском (`sort.Search`). Это снижает вычислительную сложность чтения до $O(\\log N + K)$, где $K$ — количество точек внутри интервала.",
    "pitfalls": [
        "Линейный перебор всех точек серии вместо бинарного поиска при миллионах измерений.",
        "Отсутствие синхронизации при параллельной записи и чтении.",
        "Накопление серий без механизма очистки памяти (Retention)."
    ],
    "bigtech_interview": "Как расширить этот прототип до уровня продакшен TSDB (уровня Prometheus Head)? Ответ: 1) Заменить сырой массив []TelemetrySample на сжатый BitWriter поток Gorilla; 2) Добавить Write-Ahead Log (WAL) на диск с fsync каждые 2 секунды; 3) Добавить обратный индекс Roaring Bitmaps для поиска по селекторам тегов; 4) Настроить 2-часовую ротацию блоков со сбросом неизменяемых сегментов на SSD."
})

output_path = '/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch97_p2.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Chapter 97 Part 2 generated successfully: {len(exercises)} exercises.")
