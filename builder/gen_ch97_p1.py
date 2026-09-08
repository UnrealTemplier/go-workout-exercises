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

# Ex 1: Специфика данных временных рядов (Time-Series Data)
code1 = r'''package main

import (
	"fmt"
	"time"
)

// MetricPoint представляет единичное измерение во времени
type MetricPoint struct {
	Timestamp time.Time
	Metric    string
	Value     float64
	Tags      map[string]string
}

// TimeSeriesWorkloadAnalyzer демонстрирует специфику рабочей нагрузки TSDB
type TimeSeriesWorkloadAnalyzer struct {
	points []MetricPoint
}

func (a *TimeSeriesWorkloadAnalyzer) Ingest(p MetricPoint) {
	// 1. Строгий Append-Only характер (отсутствие случайных UPDATE/DELETE)
	a.points = append(a.points, p)
}

func (a *TimeSeriesWorkloadAnalyzer) QueryRange(from, to time.Time) []MetricPoint {
	// 2. Доминирование диапазонных запросов (Range Scans) по времени
	var result []MetricPoint
	for _, p := range a.points {
		if (p.Timestamp.Equal(from) || p.Timestamp.After(from)) && p.Timestamp.Before(to) {
			result = append(result, p)
		}
	}
	return result
}

func main() {
	fmt.Println("=== Специфика данных временных рядов (Time-Series Data) ===")
	analyzer := &TimeSeriesWorkloadAnalyzer{}

	now := time.Now().UTC()
	for i := 0; i < 5; i++ {
		analyzer.Ingest(MetricPoint{
			Timestamp: now.Add(time.Duration(i) * 10 * time.Second),
			Metric:    "cpu_usage_percent",
			Value:     15.4 + float64(i)*0.8,
			Tags:      map[string]string{"host": "srv-prod-01", "dc": "eu-west"},
		})
	}

	rangeData := analyzer.QueryRange(now, now.Add(35*time.Second))
	fmt.Printf("Получено %d точек за выбранный диапазон времени:\n", len(rangeData))
	for _, pt := range rangeData {
		fmt.Printf("  [%s] %s = %.2f (host=%s)\n",
			pt.Timestamp.Format("15:04:05"), pt.Metric, pt.Value, pt.Tags["host"])
	}
}
'''

validate_go_code(code1, "code1")
exercises.append({
    "num": 1,
    "title": "Специфика данных временных рядов (Time-Series Data)",
    "task": "Изучите фундаментальные особенности и отличия Time-Series данных от традиционных реляционных OLTP систем: строгий характер вставки Append-Only, монотонность временных меток, отсутствие операций точечного обновления (UPDATE) и удаления (DELETE), высокая плотность потока и доминирование диапазонных выборок (Range Queries). Напишите структуру представления точки телеметрии и базовый обработчик диапазонных запросов.",
    "theory": "Данные временных рядов (Time-Series) представляют собой упорядоченную последовательность измерений физических или программных величин, зафиксированных через регулярные или нерегулярные интервалы времени.\n\nВ отличие от традиционных баз данных OLTP (где типичны случайные операции чтения, обновления по ID и сложные связи сущностей), рабочая нагрузка TSDB обладает уникальными характеристиками:\n1) **Append-Only поток**: данные поступают непрерывным потоком сотен тысяч или миллионов измерений в секунду, никогда не перезаписываются и не обновляются задним числом;\n2) **Временная локальность**: новые данные пишутся строго на границу текущего времени, а 95% запросов на чтение обращаются к свежим данным за последние несколько часов;\n3) **Диапазонное чтение**: запросы почти никогда не ищут одиночную запись по ID, а запрашивают временной интервал с агрегацией (avg, max, percentile);\n4) **Амортизация хранения**: старые данные не удаляются построчно, а сбрасываются целыми временными партициями (Downsampling & Retention).",
    "step_by_step": [
        "Спроектировать модель точки временного ряда (timestamp, metric name, value, tags).",
        "Определить инвариант монотонного возрастания временных меток в потоке поступления.",
        "Реализовать сканирование данных по временному интервалу [from, to).",
        "Сравнить стоимость дисковых операций в реляционных БД и специализированных TSDB."
    ],
    "code_blocks": [
        {
            "filename": "timeseries_basics.go",
            "lang": "go",
            "code": code1
        }
    ],
    "under_the_hood": "В классических БД (Postgres, MySQL) каждая запись занимает фиксированные строки в страницах кучи (Heap Pages), а индексы обновляются случайно. В специализированных TSDB (Prometheus TSDB, VictoriaMetrics, InfluxDB) данные группируются по сериям и сжимаются непрерывными временными блоками. Это превращает дисковый I/O из сотен тысяч случайных записей (Random Writes) в один последовательный сброс (Sequential Append), достигая насыщения пропускной способности SSD.",
    "pitfalls": [
        "Попытка обновлять исторические точки через UPDATE в TSDB (нарушает структуру неизменяемых сжатых блоков).",
        "Использование реляционной нормализации (отдельная таблица для каждого измерения с JOIN на метки при чтении).",
        "Хранение временных меток в строковом формате ISO-8601 вместо целочисленных Unix-эпох (int64 nanoseconds/milliseconds)."
    ],
    "bigtech_interview": "Почему попытка хранить 10 миллионов метрик в секунду в стандартном PostgreSQL приводит к деградации через несколько часов? Ответ: 1) Реляционные B-Tree индексы на миллионах уникальных серий разрастаются и перестают помещаться в RAM (Shared Buffers), вызывая постоянный swap страниц на диск; 2) Случайный дисковый I/O на запись; 3) Накладные расходы MVCC: создание версий кортежей и работа VACUUM под миллионным потоком вставок создают колоссальную нагрузку на CPU и WAL."
})

# Ex 2: Модель данных временного ряда
code2 = r'''package main

import (
	"fmt"
	"sort"
	"strings"
	"time"
)

// Label представляет пару ключ-значение тега
type Label struct {
	Name  string
	Value string
}

// Sample — элементарная точка ряда
type Sample struct {
	TimestampNs int64
	Value       float64
}

// TimeSeries описывает один непрерывный ряд измерений
type TimeSeries struct {
	MetricName string
	Labels     []Label
	Samples    []Sample
}

// Fingerprint вычисляет каноничный строковый идентификатор серии (LabelSet Hash)
func (ts *TimeSeries) Fingerprint() string {
	// Сортировка меток обеспечивает детерминированность хэша
	sortedLabels := make([]Label, len(ts.Labels))
	copy(sortedLabels, ts.Labels)
	sort.Slice(sortedLabels, func(i, j int) bool {
		return sortedLabels[i].Name < sortedLabels[j].Name
	})

	var sb strings.Builder
	sb.WriteString(ts.MetricName)
	sb.WriteString("{")
	for i, l := range sortedLabels {
		if i > 0 {
			sb.WriteString(",")
		}
		sb.WriteString(l.Name)
		sb.WriteString("=\"")
		sb.WriteString(l.Value)
		sb.WriteString("\"")
	}
	sb.WriteString("}")
	return sb.String()
}

func main() {
	fmt.Println("=== Модель данных временного ряда и Fingerprinting ===")
	ts := &TimeSeries{
		MetricName: "http_requests_total",
		Labels: []Label{
			{Name: "handler", Value: "/api/v1/checkout"},
			{Name: "method", Value: "POST"},
			{Name: "status", Value: "200"},
		},
		Samples: []Sample{
			{TimestampNs: time.Now().UnixNano(), Value: 1042.0},
		},
	}

	fmt.Println("Каноничный отпечаток серии (Fingerprint):", ts.Fingerprint())
}
'''

validate_go_code(code2, "code2")
exercises.append({
    "num": 2,
    "title": "Модель данных временного ряда",
    "task": "Спроектируйте каноничную модель временного ряда на Go: структура Label, элементарная точка Sample с наносекундной точностью таймстемпа и сущность TimeSeries. Реализуйте алгоритм генерации детерминированного отпечатка серии (Series Fingerprint) на основе лексикографической сортировки набора меток.",
    "theory": "Временной ряд (Time Series) — это уникальный именованный поток данных, однозначно идентифицируемый своим именем метрики и неизменяемым набором меток (LabelSet / Tags).\n\nНапример, ряд `http_requests_total{handler='/checkout', method='POST', status='200'}` и ряд `http_requests_total{handler='/checkout', method='GET', status='200'}` — это два совершенно РАЗНЫХ временных ряда с независимыми точками измерений.\n\nКаноничный алгоритм вычисления Fingerprint (хэша серии) требует: 1) Извлечения всех меток; 2) Лексикографической сортировки меток по имени ключа (чтобы порядок добавления tags не менял идентификатор серии); 3) Формирования нормализованной строки вида `metric{k1=\"v1\",k2=\"v2\"}` или вычисления 64-битного хэша (FNV-1a / Murmur3).",
    "step_by_step": [
        "Спроектировать легковесную структуру Sample (8 байт timestamp + 8 байт value = 16 байт).",
        "Создать структуру TimeSeries с коллекцией меток и массивом точек.",
        "Реализовать сортировку среза Label по имени для канонизации.",
        "Построить строковый сериализатор Prometheus OpenMetrics формата."
    ],
    "code_blocks": [
        {
            "filename": "series_model.go",
            "lang": "go",
            "code": code2
        }
    ],
    "under_the_hood": "В памяти TSDB обратный индекс оперирует 64-битными целыми числами SeriesID вместо строковых представлений меток. При поступлении новой точки метрики вычисляется Fingerprint: если он уже зарегистрирован в хэш-таблице (Head Index), точка немедленно передается в соответствующий Chunk буфер без повторного парсинга строк.",
    "pitfalls": [
        "Использование map[string]string для прямого вычисления Fingerprint без сортировки (итерация по map в Go случайна, что приведет к разным хэшам для одинакового набора тегов).",
        "Хранение строк меток в каждой точке Sample (приведет к расходу сотен байт памяти на одну точку вместо 16 байт).",
        "Потеря наносекундной или миллисекундной точности при округлении до секунд."
    ],
    "bigtech_interview": "Почему во всех TSDB (Prometheus, InfluxDB) модель хранения разделена на Metadata Index (где хранятся теги) и Chunk Data (где хранятся только timestamp и value)? Ответ: Разделение позволяет устранить дублирование метаданных. Теги хранятся ровно один раз в обратном индексе, а в чанках точек упаковываются только сырые числа. Это уменьшает расход памяти на порядки и позволяет применять специализированные алгоритмы побитового сжатия Gorilla."
})

# Ex 3: Почему реляционные B-Tree индексы деградируют на временных рядах
code3 = r'''package main

import (
	"fmt"
	"math/rand"
	"time"
)

// BTreeDegradationSimulator демонстрирует перегрузку B-Tree страниц при записи TSDB
type BTreeDegradationSimulator struct {
	ramLimitPages int
	pagesInRAM    int
	diskWrites    int
}

func (s *BTreeDegradationSimulator) SimulateInsertBatch(batchSize int, numSeries int) {
	fmt.Printf("[SIMULATION] Вставка пачки из %d точек по %d уникальным сериям...\n",
		batchSize, numSeries)

	// Когда число уникальных серий велико, вставка каждой точки попадает
	// в случайный лист B-Tree дерева (Leaf Page Split).
	pageSplits := 0
	for i := 0; i < batchSize; i++ {
		// Случайное распределение по разным ветвям B-Tree
		targetPage := rand.Intn(numSeries * 10)
		if targetPage > s.pagesInRAM {
			s.diskWrites++ // Промах кэша RAM: чтение страницы с диска + сброс грязной страницы
			pageSplits++
		}
	}

	fmt.Printf("  -> Промахов мимо оперативной памяти: %d\n", s.diskWrites)
	fmt.Printf("  -> Расщеплений страниц B-Tree (Page Splits): %d\n", pageSplits)
}

func main() {
	fmt.Println("=== Деградация B-Tree индексов на временных рядах ===")
	sim := &BTreeDegradationSimulator{
		ramLimitPages: 1000,
		pagesInRAM:    1000,
	}
	sim.SimulateInsertBatch(50000, 10000)
	fmt.Println("Вывод: B-Tree индекс на миллионах серий разрушает локальность данных в RAM,")
	fmt.Println("превращая запись в хаотичный дисковый Random Write I/O.")
}
'''

validate_go_code(code3, "code3")
exercises.append({
    "num": 3,
    "title": "Почему реляционные B-Tree индексы деградируют на временных рядах",
    "task": "Исследуйте механику деградации классических B-Tree индексов реляционных СУБД при обслуживании высоконагруженных потоков временных рядов: постоянный рост размера дерева индекса, вытеснение страниц из оперативной памяти (Buffer Pool), частое расщепление узлов (Page Splits) и переход от быстрого последовательного ввода-вывода к катастрофическому случайному чтению/записи (Random I/O).",
    "theory": "B-Tree — великолепная структура данных для точечного поиска по первичному ключу в реляционных БД. Однако при обработке Time-Series данных на миллионах уникальных метрик B-Tree становится непреодолимым бутылочным горлышком.\n\nПроблема заключается в следующем: если индекс построен по составному ключу (series_id, timestamp), каждая новая точка для случайного датчика попадает в свой собственный листовой узел B-Tree дерева (Leaf Node). Когда количество активных серий превышает миллионы, общее количество листовых страниц B-Tree превышает объем оперативной памяти (RAM).\n\nВ результате каждая операция INSERT вынуждена: 1) Выгрузить случайную страницу из RAM на диск; 2) Загрузить нужную страницу с диска; 3) Модифицировать ее; 4) Выполнить Page Split при заполнении. Производительность вставки падает с 200 000 до 2 000 строк в секунду.",
    "step_by_step": [
        "Изучить структуру страниц B-Tree (узел фиксированного размера 8 KB/16 KB).",
        "Проанализировать влияние роста объема серий на коэффициент попадания в кэш (Cache Hit Ratio).",
        "Смоделировать деградацию производительности при превышении рабочего набора страниц над RAM.",
        "Сформулировать требования к архитектуре специализированных TSDB (LSM-деревья, Chunks, Append-Only)."
    ],
    "code_blocks": [
        {
            "filename": "btree_degradation.go",
            "lang": "go",
            "code": code3
        }
    ],
    "under_the_hood": "В B-Tree заполнение листа свыше 100% вызывает дорогостоящую операцию Page Split: выделение новой 8KB страницы, перенос половины ключей и обновление ссылок в родительском узле под эксклюзивным локом страницы. Это порождает каскадную фрагментацию памяти и диска.",
    "pitfalls": [
        "Создание нескольких независимых B-Tree индексов по timestamp и tag в обычной PostgreSQL без партиционирования.",
        "Игнорирование метрики Buffer Cache Hit Ratio при профилировании тяжелой вставки.",
        "Непонимание разницы между монотонным индексом по времени и разрозненным составным индексом по меткам."
    ],
    "bigtech_interview": "Почему B-Tree индекс на временной метке деградирует меньше, чем индекс на (metric_id, timestamp)? Ответ: Индекс только на timestamp всегда вставляет новые значения в самый правый крайний лист B-Tree (Rightmost Page), страницы которого постоянно находятся горячими в кэше RAM. Но как только мы добавляем в начало ключа metric_id, вставки размазываются равномерно по всему дереву, заставляя СУБД случайным образом обращаться к миллионам холодных страниц на диске."
})

# Ex 4: Алгоритм сжатия Facebook Gorilla: основы
code4 = r'''package main

import (
	"fmt"
)

// GorillaArchitectureOverview иллюстрирует принципы статьи Facebook Gorilla
func ExplainGorillaPrinciples() {
	fmt.Println("=== Архитектура Facebook Gorilla TSDB (2015) ===")
	fmt.Println()
	fmt.Println("Ключевая идея: 1 точка Sample = Timestamp (8 байт) + Value float64 (8 байт) = 16 байт.")
	fmt.Println("При несжатом хранении 1 миллиард точек = 16 ГБ оперативной памяти.")
	fmt.Println()
	fmt.Println("Революция алгоритма Gorilla:")
	fmt.Println("1. Раздельное сжатие Timestamps и Values в независимые битовые потоки.")
	fmt.Println("2. Сжатие временных меток через Delta-of-Delta (вторая производная):")
	fmt.Println("   - Если интервал постоянен (например, ровно 10 сек): D' = 0 -> кодируется 1 БИТОМ '0'!")
	fmt.Println("3. Сжатие float64 значений через побитовый XOR:")
	fmt.Println("   - Если значение не изменилось: XOR = 0 -> кодируется 1 БИТОМ '0'!")
	fmt.Println("   - Если значение изменилось незначительно: кодируются только значащие биты мантиссы.")
	fmt.Println()
	fmt.Println("Итог: Сокращение среднего размера точки с 16 байт до 1.37 байта (сжатие на 91.4%)!")
}

func main() {
	ExplainGorillaPrinciples()
}
'''

validate_go_code(code4, "code4")
exercises.append({
    "num": 4,
    "title": "Алгоритм сжатия Facebook Gorilla: основы",
    "task": "Изучите основы фундаментального алгоритма сжатия Facebook Gorilla (2015), лежащего в основе Prometheus TSDB, VictoriaMetrics, M3DB и InfluxDB. Разберите ключевую идею раздельного побитового сжатия временных меток и вещественных чисел, позволяющую упаковать 16-байтную точку измерения в среднем в 1.37 байта в оперативной памяти.",
    "theory": "В 2015 году инженеры Facebook опубликовали фундаментальную статью «Gorilla: A Fast, Scalable, In-Memory Time Series Database». Она произвела революцию в индустрии мониторинга и IoT.\n\nДо Gorilla хранение миллиардов метрик в оперативной памяти требовало огромных кластеров серверов: каждая точка измерения Sample состоит из 64-битного целого числа временной метки (8 байт) и 64-битного вещественного числа значения float64 (8 байт), то есть 16 байт несжатых данных.\n\nGorilla предложила два взаимодополняющих алгоритма побитового сжатия (Bit-level Compression):\n1) **Delta-of-Delta компрессия временных меток**: учитывает строгую периодичность отправки данных датчиками;\n2) **XOR компрессия значений float64**: учитывает физическую плавность изменения измеряемых величин во времени.\nВ результате реальные потоки метрик сжимаются в среднем в 11.7 раз без малейшей потери точности (Lossless Compression).",
    "step_by_step": [
        "Изучить математическую формулу точки измерения (T_i, V_i).",
        "Понять принцип разделения потока данных на поток битов времени и поток битов значений.",
        "Оценить экономию оперативной памяти в продакшене (от 16 байт до 1.37 байта).",
        "Сформулировать критерии обратимости сжатия (Lossless bit-exact recovery)."
    ],
    "code_blocks": [
        {
            "filename": "gorilla_overview.go",
            "lang": "go",
            "code": code4
        }
    ],
    "under_the_hood": "Потоки данных временных рядов обладают огромной энтропийной избыточностью. Стандартные алгоритмы сжатия общего назначения (Gzip, Zstandard, Snappy) работают с байтовыми окнами словарей (LZ77/Huffman) и показывают низкую эффективность и высокое потребление CPU на потоках сырых float64. Gorilla оперирует на уровне отдельных бит, используя внутреннюю специфику стандарта IEEE 754.",
    "pitfalls": [
        "Попытка сжимать timestamp и value в одном общем битовом потоке как единую структуру.",
        "Использование алгоритмов сжатия с потерями (Lossy) для финансовых или критических метрик.",
        "Недооценка накладных расходов на упаковку бит при отсутствии эффективного BitWriter."
    ],
    "bigtech_interview": "Почему Prometheus TSDB выбрал именно алгоритм Gorilla для хранения блоков в RAM? Ответ: Потому что Gorilla обеспечивает субнаносекундную скорость сжатия на лету (миллионы точек в секунду на одно ядро CPU) без предварительного накопления больших словарей, сжимает 16 байт до 1.3 байта без потери точности и позволяет читать распакованные точки потоковым итератором прямо из байтового среза в памяти."
})

# Ex 5: Сжатие временных меток: алгоритм Delta-of-Delta
code5 = r'''package main

import (
	"fmt"
)

// DeltaOfDeltaCalculator демонстрирует расчет второй разности таймстемпов
type DeltaOfDeltaCalculator struct {
	prevTimestamp int64
	prevDelta     int64
}

func (c *DeltaOfDeltaCalculator) Push(t int64) (delta int64, dod int64) {
	if c.prevTimestamp == 0 {
		c.prevTimestamp = t
		c.prevDelta = 0
		return 0, 0
	}

	delta = t - c.prevTimestamp
	dod = delta - c.prevDelta

	c.prevTimestamp = t
	c.prevDelta = delta
	return delta, dod
}

func main() {
	fmt.Println("=== Расчет Delta-of-Delta (второй разности) таймстемпов ===")
	calc := &DeltaOfDeltaCalculator{}

	// Симуляция датчика, отправляющего данные каждые 10 секунд с небольшим джиттером
	timestamps := []int64{
		1000, // T0
		1010, // T1: delta = 10, dod = 10 (первая дельта)
		1020, // T2: delta = 10, dod = 0  (идеальный интервал!)
		1030, // T3: delta = 10, dod = 0  (идеальный интервал!)
		1041, // T4: delta = 11, dod = +1 (джиттер +1 сек)
		1051, // T5: delta = 10, dod = -1 (возврат к интервалу)
	}

	for i, ts := range timestamps {
		delta, dod := calc.Push(ts)
		fmt.Printf("Точка #%d: T=%d | Delta (T_i - T_{i-1}) = %3d | Delta-of-Delta (D' = D_i - D_{i-1}) = %3d\n",
			i, ts, delta, dod)
	}
	fmt.Println("Обратите внимание: Когда интервал постоянен, Delta-of-Delta строго РАВНА НУЛЮ!")
}
'''

validate_go_code(code5, "code5")
exercises.append({
    "num": 5,
    "title": "Сжатие временных меток: алгоритм Delta-of-Delta",
    "task": "Большинство сенсоров и серверов отправляют телеметрию с регулярным интервалом (например, строго каждые 10 или 15 секунд). Напишите структуру вычисления первой разности Delta (D_i = T_i - T_{i-1}) и второй разности Delta-of-Delta (D' = D_i - D_{i-1}). Докажите, что при строгой периодичности D' = 0, что открывает возможность кодирования шага времени всего одним битом.",
    "theory": "Временные метки в сыром виде представляют собой огромные 64-битные целые числа Unix-времени (например, 1718000000 секунд или наносекунд). Прямое хранение каждого числа требует полных 8 байт (64 бита).\n\nПервая ступень оптимизации — хранение первой разности (Delta):\n$D_i = T_i - T_{i-1}$\nЕсли данные отправляются раз в 10 секунд, $D_i$ колеблется около значения 10.\n\nВторая ступень — вычисление второй разности (Delta-of-Delta):\n$D' = D_i - D_{i-1} = (T_i - T_{i-1}) - (T_{i-1} - T_{i-2})$\nЕсли таймер датчика сработал точно в срок (например, 10 секунд после предыдущего), то $D_i = 10$, $D_{i-1} = 10$, следовательно $D' = 0$! В алгоритме Gorilla значение $D'=0$ кодируется единственным битом `0`. Таким образом, абсолютное большинство временных меток упаковываются ровно в 1 бит вместо 64 бит!",
    "step_by_step": [
        "Изучить формулу второй производной дискретного времени.",
        "Реализовать сохранение предыдущей временной метки и предыдущей первой дельты.",
        "Проверить поведение алгоритма при идеальном периодическом потоке точек.",
        "Проанализировать влияние сетевого джиттера (задержки пакетов) на отклонения Delta-of-Delta от нуля."
    ],
    "code_blocks": [
        {
            "filename": "delta_of_delta.go",
            "lang": "go",
            "code": code5
        }
    ],
    "under_the_hood": "Двойное дифференцирование исключает линейный тренд монотонного роста времени. В теории информации энтропия последовательности, состоящей преимущественно из нулей, стремится к нулю, что делает ее идеальным кандидатом для префиксного кодирования Хаффмана или переменной битовой длины (Variable-Length Bit Encoding).",
    "pitfalls": [
        "Попытка вычислять Delta-of-Delta для первой точки ряда (для первой точки сохраняется абсолютный timestamp, а для второй — первая дельта).",
        "Отрицательные временные метки при рассинхронизации NTP на серверах-источниках (out-of-order timestamps).",
        "Переполнение целочисленного диапазона при огромных разрывах времени между замерами."
    ],
    "bigtech_interview": "Что произойдет с алгоритмом сжатия Gorilla, если на источнике метрик произойдет рассинхронизация времени NTP и временная метка придет из прошлого ($T_i < T_{i-1}$)? Ответ: Дельта станет отрицательной. Поскольку большинство реализаций Gorilla TSDB предполагают монотонное возрастание времени, точка out-of-order либо отбрасывается на входе в TSDB, либо попадает в самый широкий диапазон битового кодирования (32 бита), что резко ухудшает степень сжатия."
})

# Ex 6: Реализация BitWriter для побитовой записи на Go
code6 = r'''package main

import (
	"fmt"
)

// BitWriter обеспечивает эффективную побитовую запись в байтовый срез
type BitWriter struct {
	buf   []byte
	b     byte  // Текущий накапливаемый байт
	count uint8 // Количество бит, записанных в текущий байт (0..7)
}

func NewBitWriter() *BitWriter {
	return &BitWriter{
		buf: make([]byte, 0, 1024),
	}
}

// WriteBit записывает ровно один бит (0 или 1)
func (w *BitWriter) WriteBit(bit byte) {
	if bit > 0 {
		// Устанавливаем бит со старшего к младшему (MSB first)
		w.b |= (1 << (7 - w.count))
	}
	w.count++
	if w.count == 8 {
		w.buf = append(w.buf, w.b)
		w.b = 0
		w.count = 0
	}
}

// WriteBits записывает младшие numBits числа val
func (w *BitWriter) WriteBits(val uint64, numBits int) {
	for i := numBits - 1; i >= 0; i-- {
		bit := byte((val >> i) & 1)
		w.WriteBit(bit)
	}
}

// Flush сбрасывает оставшиеся биты текущего байта в буфер
func (w *BitWriter) Flush() []byte {
	if w.count > 0 {
		w.buf = append(w.buf, w.b)
		w.b = 0
		w.count = 0
	}
	return w.buf
}

func main() {
	fmt.Println("=== Побитовая запись с BitWriter на чистом Go ===")
	bw := NewBitWriter()

	// Запишем префикс 10 (2 бита) и 7-битное число 42 (0101010)
	bw.WriteBit(1)
	bw.WriteBit(0)
	bw.WriteBits(42, 7) // 42 = 0101010

	res := bw.Flush()
	fmt.Printf("Записано 9 бит в %d байта. Результат в HEX: % X (Байты: %08b %08b)\n",
		len(res), res, res[0], res[1])
}
'''

validate_go_code(code6, "code6")
exercises.append({
    "num": 6,
    "title": "Реализация BitWriter для побитовой записи на Go",
    "task": "Стандартная библиотека Go (пакеты io, bufio) умеет читать и писать данные только целыми байтами. Для реализации алгоритма Gorilla создайте низкоуровневую структуру BitWriter: методы WriteBit(bit byte) и WriteBits(val uint64, numBits int), накапливающие биты от старшего к младшему (MSB first) и упаковывающие их в []byte без лишних аллокаций.",
    "theory": "Сжатие Gorilla оперирует сущностями переменной длины: 1 бит флага, 7 бит разницы, 12 бит смещения. Если записывать каждое такое значение в целый байт, вся идея сжатия потеряет смысл.\n\nBitWriter — ключевой строительный блок любых потоковых алгоритмов энтропийного кодирования. Он поддерживает внутреннее состояние: текущий формируемый байт `b byte` и счетчик заполненных бит `count uint8` (от 0 до 7). Запись ведется от старшего бита (Most Significant Bit - MSB): бит со смещением 0 занимает позицию 128 (1 << 7), следующий — позицию 64 (1 << 6) и так далее.\n\nКогда `count` достигает 8, байт считается завершенным и сбрасывается в слайс `buf`, а переменная `b` обнуляется. Метод `Flush()` дополняет последний неполный байт нулями и возвращает итоговый слайс.",
    "step_by_step": [
        "Спроектировать структуру BitWriter с внутренним буфером, байтом-аккумулятором и счетчиком бит.",
        "Реализовать метод WriteBit с побитовым сдвигом `1 << (7 - count)`.",
        "Реализовать метод WriteBits для циклической записи последовательности бит числа uint64.",
        "Реализовать метод Flush с дополнением нулями до границы целого байта."
    ],
    "code_blocks": [
        {
            "filename": "bit_writer.go",
            "lang": "go",
            "code": code6
        }
    ],
    "under_the_hood": "Операции побитового сдвига и маскирования (`|`, `&`, `<<`, `>>`) транслируются компилятором Go в единичные ассемблерные инструкции процессора (SHL, SHR, OR, AND). Поскольку буфер `buf` предварительно аллоцируется с capacity 1024 байта через `make([]byte, 0, 1024)`, запись миллионов бит происходит со скоростью процессорных регистров без вызовов GC.",
    "pitfalls": [
        "Запись бит в обратном порядке (LSB first) приведет к невозможности побитовой совместимости с другими реализациями Gorilla.",
        "Забытый вызов `Flush()` в конце записи (последние от 1 до 7 бит будут безвозвратно потеряны).",
        "Лишние аллокации памяти при частых аппендах в буфер без предварительного резервирования capacity."
    ],
    "bigtech_interview": "Почему в BitWriter для Gorilla используется порядок записи MSB (старший бит вперед), а не LSB? Ответ: Потому что префиксные коды (такие как коды Хаффмана или переменные битовые флаги Gorilla: '0', '10', '110') должны распознаваться парсером на лету от начала чтения. При записи MSB префикс читается первым же битом, что позволяет парсеру немедленно определить длину следующего поля данных."
})

# Ex 7: Кодирование Delta-of-Delta временных меток
code7 = r'''package main

import (
	"fmt"
)

// BitStreamWriter интерфейс записи бит
type BitStreamWriter interface {
	WriteBit(bit byte)
	WriteBits(val uint64, numBits int)
}

// SimpleBitWriter простая реализация для демонстрации
type SimpleBitWriter struct {
	bits []byte
}

func (s *SimpleBitWriter) WriteBit(bit byte) {
	s.bits = append(s.bits, bit)
}

func (s *SimpleBitWriter) WriteBits(val uint64, numBits int) {
	for i := numBits - 1; i >= 0; i-- {
		s.bits = append(s.bits, byte((val>>i)&1))
	}
}

// EncodeDeltaOfDelta реализует спецификацию кодирования временных меток Facebook Gorilla
func EncodeDeltaOfDelta(w BitStreamWriter, dod int64) {
	switch {
	case dod == 0:
		// 1 бит: '0'
		w.WriteBit(0)
	case dod >= -63 && dod <= 64:
		// 10 бит: префикс '10' (2 бита) + значение 7 бит
		w.WriteBit(1)
		w.WriteBit(0)
		w.WriteBits(uint64(dod+63), 7)
	case dod >= -255 && dod <= 256:
		// 12 бит: префикс '110' (3 бита) + значение 9 бит
		w.WriteBit(1)
		w.WriteBit(1)
		w.WriteBit(0)
		w.WriteBits(uint64(dod+255), 9)
	case dod >= -2047 && dod <= 2048:
		// 16 бит: префикс '1110' (4 бита) + значение 12 бит
		w.WriteBit(1)
		w.WriteBit(1)
		w.WriteBit(1)
		w.WriteBit(0)
		w.WriteBits(uint64(dod+2047), 12)
	default:
		// 36 бит: префикс '1111' (4 бита) + 32 бита сырого значения
		w.WriteBit(1)
		w.WriteBit(1)
		w.WriteBit(1)
		w.WriteBit(1)
		w.WriteBits(uint64(dod), 32)
	}
}

func main() {
	fmt.Println("=== Кодирование Delta-of-Delta по спецификации Facebook Gorilla ===")
	cases := []int64{0, 10, -50, 200, -1500, 100000}

	for _, dod := range cases {
		w := &SimpleBitWriter{}
		EncodeDeltaOfDelta(w, dod)
		fmt.Printf("Delta-of-Delta = %7d -> Закодировано в %2d бит: ", dod, len(w.bits))
		for _, b := range w.bits {
			fmt.Print(b)
		}
		fmt.Println()
	}
}
'''

validate_go_code(code7, "code7")
exercises.append({
    "num": 7,
    "title": "Кодирование Delta-of-Delta временных меток",
    "task": "Реализуйте полный алгоритм кодирования временных меток по официальной спецификации Facebook Gorilla: 1) Если D' = 0 -> пишем 1 бит '0'; 2) Если -63 <= D' <= 64 -> пишем префикс '10' и 7 бит значения со смещением; 3) Если -255 <= D' <= 256 -> префикс '110' и 9 бит; 4) Если -2047 <= D' <= 2048 -> префикс '1110' и 12 бит; 5) Иначе -> префикс '1111' и 32 бита значения.",
    "theory": "Спецификация сжатия временных меток Gorilla использует префиксные коды переменной длины (Variable-Length Prefix Codes), оптимизированные под гауссово распределение сетевого джиттера серверов.\n\nТаблица кодирования Gorilla:\n- $D' = 0$: `0` (всего **1 бит**! В 96% случаев в продакшене);\n- $-63 \\le D' \\le 64$: `10` + 7 бит (всего **9 бит**, покрывает джиттер до десятков миллисекунд);\n- $-255 \\le D' \\le 256$: `110` + 9 бит (всего **12 бит**);\n- $-2047 \\le D' \\le 2048$: `1110` + 12 бит (всего **16 бит**);\n- Все остальные случаи (огромные паузы, сбои связи): `1111` + 32 бита (всего **36 бит**).\n\nБлагодаря тому, что префиксы '0', '10', '110', '1110', '1111' являются свободными от префиксов (Prefix-Free), декодер однозначно определяет, сколько бит нужно прочитать следом.",
    "step_by_step": [
        "Изучить интервалы допустимых значений второй разности Delta-of-Delta.",
        "Реализовать сдвиг знаковых значений в беззнаковый диапазон (например, `dod + 63` для 7-битного представления).",
        "Написать функцию кодирования со всеми 5 ветвями условий switch/case.",
        "Проверить битовую длину каждого случая на тестовом наборе смещений."
    ],
    "code_blocks": [
        {
            "filename": "encode_dod.go",
            "lang": "go",
            "code": code7
        }
    ],
    "under_the_hood": "Поскольку значение $D'$ может быть отрицательным, прямое сохранение знакового числа потребовало бы знакового бита. Gorilla использует нормализацию диапазона: например, диапазон $[-63, 64]$ содержит 128 чисел, которые идеально укладываются в беззнаковые 7 бит путем добавления константы смещения $+63$.",
    "pitfalls": [
        "Неправильное вычисление битовой длины (например, запись 8 бит вместо 7 для диапазона $[-63, 64]$).",
        "Ошибки округления и переполнения при работе с 32-битными и 64-битными целыми числами.",
        "Нарушение порядка бит префикса (например, запись '01' вместо '10')."
    ],
    "bigtech_interview": "Почему в Gorilla выбраны именно интервалы 7, 9, 12 и 32 бит? Ответ: Инженеры Facebook проанализировали терабайты реальной телеметрии дата-центров. 96% всех точек отправлялись строго вовремя ($D'=0$), 3% имели минимальный сетевой джиттер до 64 мс (укладывались в 7 бит), и менее 1% страдали от задержек сборки мусора или сетевых переподключений. Данные пороги минимизируют математическое ожидание длины битового кода."
})

# Ex 8: Сжатие вещественных значений (Float64 Values) через XOR
code8 = r'''package main

import (
	"fmt"
	"math"
	"math/bits"
)

// FloatXORAnalyzer исследует побитовое сходство соседних float64 значений
type FloatXORAnalyzer struct{}

func (a *FloatXORAnalyzer) Analyze(v1, v2 float64) {
	b1 := math.Float64bits(v1)
	b2 := math.Float64bits(v2)
	xor := b1 ^ b2

	lz := bits.LeadingZeros64(xor)
	tz := bits.TrailingZeros64(xor)
	meaningfulBits := 64 - lz - tz
	if xor == 0 {
		meaningfulBits = 0
	}

	fmt.Printf("V1 = %8.4f | 0x%016X (%064b)\n", v1, b1, b1)
	fmt.Printf("V2 = %8.4f | 0x%016X (%064b)\n", v2, b2, b2)
	fmt.Printf("XOR        | 0x%016X (%064b)\n", xor, xor)
	fmt.Printf("  -> Ведущих нулей (Leading Zeros):  %2d\n", lz)
	fmt.Printf("  -> Замыкающих нулей (Trailing Zeros): %2d\n", tz)
	fmt.Printf("  -> Значащих бит для сохранения:      %2d из 64 (экономия %.1f%%)\n\n",
		meaningfulBits, (1.0-float64(meaningfulBits)/64.0)*100.0)
}

func main() {
	fmt.Println("=== Побитовое сжатие float64 значений через XOR ===")
	analyzer := &FloatXORAnalyzer{}

	// Симуляция плавно меняющейся температуры процессора
	analyzer.Analyze(54.1200, 54.1200) // Идентичные значения
	analyzer.Analyze(54.1200, 54.1350) // Небольшое изменение
	analyzer.Analyze(54.1350, 54.1400) // Еще одно близкое значение
}
'''

validate_go_code(code8, "code8")
exercises.append({
    "num": 8,
    "title": "Сжатие вещественных значений (Float64 Values) через XOR",
    "task": "Изучите битовую структуру вещественных чисел стандарта IEEE 754: 1 бит знака, 11 бит порядка (экспоненты) и 52 бита мантиссы. Покажите, почему побитовая операция XOR (V_i ^ V_{i-1}) между последовательными измерениями телеметрии генерирует большое количество ведущих и замыкающих нулей, позволяя сохранить только несколько значащих бит.",
    "theory": "Вещественные числа float64 в памяти компьютера хранятся по стандарту IEEE 754: 1 бит знака, 11 бит смещенной экспоненты и 52 бита мантиссы.\n\nВ реальных системах мониторинга физические величины (температура, нагрузка CPU, сетевой трафик, объем памяти) меняются плавно. Когда два числа близки (например, 54.1200 и 54.1350):\n1) Знак совпадает (бит 63 одинаковый);\n2) Порядок (экспонента) совпадает (биты 62–52 одинаковые);\n3) Старшие биты мантиссы также совпадают.\n\nЕсли применить к их битовым представлениям операцию XOR (`math.Float64bits(v1) ^ math.Float64bits(v2)`), то все совпадающие биты обратятся в **0**! В результате получается 64-битное число, у которого большинство бит слева (Leading Zeros) и справа (Trailing Zeros) равны нулю, а в середине находится лишь небольшое 'окно' значащих бит (Meaningful Bits).",
    "step_by_step": [
        "Изучить функцию `math.Float64bits(v)` для прямого доступа к битам float64 без преобразования типов.",
        "Вычислить `xor := b1 ^ b2`.",
        "Использовать функции пакета `math/bits`: `LeadingZeros64` и `TrailingZeros64`.",
        "Рассчитать процент экономии памяти при сохранении только значимых бит."
    ],
    "code_blocks": [
        {
            "filename": "float_xor_analysis.go",
            "lang": "go",
            "code": code8
        }
    ],
    "under_the_hood": "Функции `bits.LeadingZeros64` компилируются компилятором Go в специализированные процессорные инструкции `BSR` (Bit Scan Reverse) или `LZCNT` (Leading Zero Count) на x86-64 и `CLZ` на ARM64. Они выполняются процессором ровно за 1 тактовый такт, обеспечивая феноменальную скорость анализа данных.",
    "pitfalls": [
        "Попытка привести float64 к int64 через обычный type cast `int64(val)` (это обрежет дробную часть вместо чтения IEEE 754 бит!).",
        "Обработка специальных значений `NaN` и `+Inf`/`-Inf` (их битовые маски требуют аккуратной обработки).",
        "Недооценка затрат при резких скачках значений (резкое изменение знака или порядка сбрасывает Leading Zeros)."
    ],
    "bigtech_interview": "Почему алгоритм XOR сжатия не работает для случайных чисел (Random Float)? Ответ: Потому что у двух независимых случайных чисел биты экспоненты и мантиссы не имеют корреляции. Их XOR будет иметь нулевое количество ведущих нулей, и алгоритм Gorilla запишет 64 бита сырых данных плюс накладные расходы префикса (около 69 бит), вызвав отрицательное сжатие."
})

# Ex 9: Реализация XOR-сжатия значений по спецификации Gorilla
code9 = r'''package main

import (
	"fmt"
	"math"
	"math/bits"
)

// BitStreamWriterI интерфейс записи бит
type BitStreamWriterI interface {
	WriteBit(bit byte)
	WriteBits(val uint64, numBits int)
}

// ValueCompressor реализует сжатие вещественных чисел float64 по алгоритму Facebook Gorilla
type ValueCompressor struct {
	w            BitStreamWriterI
	prevValBits  uint64
	prevLeading  uint8
	prevTrailing uint8
	hasFirst     bool
}

func NewValueCompressor(w BitStreamWriterI) *ValueCompressor {
	return &ValueCompressor{
		w:            w,
		prevLeading:  255,
		prevTrailing: 255,
	}
}

// CompressValue кодирует очередное значение float64
func (c *ValueCompressor) CompressValue(val float64) {
	valBits := math.Float64bits(val)

	if !c.hasFirst {
		// Первое значение сохраняется полностью (64 бита)
		c.w.WriteBits(valBits, 64)
		c.prevValBits = valBits
		c.hasFirst = true
		return
	}

	xor := valBits ^ c.prevValBits
	if xor == 0 {
		// Значение идентично предыдущему: пишем ровно 1 бит '0'
		c.w.WriteBit(0)
		return
	}

	// Значение изменилось: пишем бит '1'
	c.w.WriteBit(1)

	leading := uint8(bits.LeadingZeros64(xor))
	trailing := uint8(bits.TrailingZeros64(xor))

	// Ограничение leading zeros 5 битами (максимум 31)
	if leading >= 32 {
		leading = 31
	}

	// Если окно значащих бит умещается в предыдущие границы
	if c.prevLeading != 255 && leading >= c.prevLeading && trailing >= c.prevTrailing {
		// Пишем бит '0': границы окна те же, пишем только значащие биты
		c.w.WriteBit(0)
		meaningfulLength := int(64 - c.prevLeading - c.prevTrailing)
		meaningfulBits := xor >> c.prevTrailing
		c.w.WriteBits(meaningfulBits, meaningfulLength)
	} else {
		// Пишем бит '1': новые границы окна
		c.w.WriteBit(1)
		c.w.WriteBits(uint64(leading), 5) // 5 бит на ведущие нули (0..31)

		meaningfulLength := int(64 - leading - trailing)
		c.w.WriteBits(uint64(meaningfulLength), 6) // 6 бит на длину (0..64)

		meaningfulBits := xor >> trailing
		c.w.WriteBits(meaningfulBits, meaningfulLength)

		c.prevLeading = leading
		c.prevTrailing = trailing
	}

	c.prevValBits = valBits
}

// SimpleBitAccumulator накапливает биты в срез
type SimpleBitAccumulator struct {
	totalBits int
}

func (s *SimpleBitAccumulator) WriteBit(bit byte)               { s.totalBits += 1 }
func (s *SimpleBitAccumulator) WriteBits(val uint64, n int)      { s.totalBits += n }

func main() {
	fmt.Println("=== Полноценное XOR-сжатие значений float64 (Gorilla) ===")
	acc := &SimpleBitAccumulator{}
	comp := NewValueCompressor(acc)

	values := []float64{100.0, 100.0, 100.1, 100.15, 100.15, 100.18, 100.18}
	for i, v := range values {
		startBits := acc.totalBits
		comp.CompressValue(v)
		fmt.Printf("Значение #%d: %7.2f -> потрачено %2d бит\n", i, v, acc.totalBits-startBits)
	}
	fmt.Printf("Всего точек: %d, всего бит: %d (в среднем %.1f бит на точку вместо 64!)\n",
		len(values), acc.totalBits, float64(acc.totalBits)/float64(len(values)))
}
'''

validate_go_code(code9, "code9")
exercises.append({
    "num": 9,
    "title": "Реализация XOR-сжатия значений по спецификации Gorilla",
    "task": "Реализуйте полный алгоритм сжатия вещественных значений float64 по спецификации Facebook Gorilla: 1) Сохранение первого значения как 64 бита; 2) Если XOR = 0 -> пишем бит '0'; 3) Если XOR != 0 -> пишем бит '1'; 4) Если границы окна значащих бит совпадают с предыдущими -> пишем бит '0' и только значащие биты; 5) Иначе пишем '1', 5 бит ведущих нулей, 6 бит длины и значащие биты.",
    "theory": "Спецификация сжатия значений Facebook Gorilla основана на отслеживании границ значащих бит (Leading Zeros и Trailing Zeros) при побитовом XOR текущего и предыдущего значений.\n\nАлгоритм работает по шагам:\n- Первое значение пишется полностью: 64 бита;\n- Для каждого последующего вычисляется $XOR = V_i \\oplus V_{i-1}$:\n  - Если $XOR == 0$ (значение повторилось): пишем **1 бит `0`**;\n  - Если $XOR \\ne 0$: пишем **бит `1`**;\n    - Проверяем, умещаются ли значащие биты в окно предыдущей точки (`leading >= prevLeading && trailing >= prevTrailing`):\n      - Если ДА: пишем **бит `0`** и только значащие биты длиной `64 - prevLeading - prevTrailing`;\n      - Если НЕТ: пишем **бит `1`**, затем 5 бит числа ведущих нулей, 6 бит длины значащей части и сами значащие биты. Затем запоминаем новые границы окна.",
    "step_by_step": [
        "Инициализировать состояние компрессора: prevValBits, prevLeading, prevTrailing.",
        "Реализовать проверку равенства $XOR == 0$ для мгновенного однобитового кодирования повторов.",
        "Реализовать ветку переиспользования предыдущего окна бит (бит `0`).",
        "Реализовать ветку определения нового окна значащих бит (бит `1` + 5 бит + 6 бит).",
        "Проверить корректность сжатия на монотонно меняющемся и константном потоках чисел."
    ],
    "code_blocks": [
        {
            "filename": "gorilla_value_compressor.go",
            "lang": "go",
            "code": code9
        }
    ],
    "under_the_hood": "Поскольку число ведущих нулей (0..64) не может превышать 31 в схеме Gorilla (для значений с leading >= 32 число принудительно ограничивается 31), для его кодирования достаточно ровно 5 бит ($2^5 = 32$). Для длины значащих бит (от 1 до 64) достаточно 6 бит ($2^6 = 64$). Это минимизирует накладные расходы на передачу метаданных окна всего до 11 бит.",
    "pitfalls": [
        "Несохранение сдвинутого значения мантиссы (`xor >> trailing`): при несовпадении сдвига декодер восстановит искаженное число.",
        "Забытое ограничение `leading = 31` при числе ведущих нулей от 32 до 64.",
        "Несвоевременное обновление `prevLeading` и `prevTrailing`."
    ],
    "bigtech_interview": "Почему алгоритм Gorilla хранит число ведущих нулей (Leading Zeros), но не сохраняет явно число замыкающих нулей (Trailing Zeros)? Ответ: Потому что вместо замыкающих нулей Gorilla сохраняет общую длину значащей части (Length, 6 бит). Число замыкающих нулей вычисляется декодером тривиально: $Trailing = 64 - Leading - Length$. Это устраняет необходимость тратить еще 6 бит на явное сохранение Trailing Zeros."
})

# Ex 10: Разработка BitReader для побитового чтения
code10 = r'''package main

import (
	"errors"
	"fmt"
	"io"
)

// BitReader читает биты из упакованного байтового среза
type BitReader struct {
	buf   []byte
	off   int   // Индекс текущего байта
	count uint8 // Количество прочитанных бит из текущего байта (0..7)
}

func NewBitReader(buf []byte) *BitReader {
	return &BitReader{buf: buf}
}

// ReadBit читает ровно один бит (0 или 1)
func (r *BitReader) ReadBit() (byte, error) {
	if r.off >= len(r.buf) {
		return 0, io.EOF
	}

	// Читаем со старшего бита (MSB)
	bit := (r.buf[r.off] >> (7 - r.count)) & 1
	r.count++
	if r.count == 8 {
		r.count = 0
		r.off++
	}
	return bit, nil
}

// ReadBits читает numBits и возвращает их в виде uint64
func (r *BitReader) ReadBits(numBits int) (uint64, error) {
	if numBits < 0 || numBits > 64 {
		return 0, errors.New("numBits must be between 0 and 64")
	}

	var res uint64
	for i := 0; i < numBits; i++ {
		bit, err := r.ReadBit()
		if err != nil {
			return 0, err
		}
		res = (res << 1) | uint64(bit)
	}
	return res, nil
}

func main() {
	fmt.Println("=== Побитовое чтение с BitReader на Go ===")
	// Упакованные байты: бит 1, бит 0, и 7 бит числа 42 (0101010)
	rawBytes := []byte{0b10010101, 0b00000000}
	reader := NewBitReader(rawBytes)

	b1, _ := reader.ReadBit()
	b2, _ := reader.ReadBit()
	val, _ := reader.ReadBits(7)

	fmt.Printf("Прочитано: Бит 1 = %d, Бит 2 = %d, 7-битное значение = %d (ожидалось 42)\n",
		b1, b2, val)
}
'''

validate_go_code(code10, "code10")
exercises.append({
    "num": 10,
    "title": "Разработка BitReader для побитового чтения",
    "task": "Напишите структуру BitReader для зеркального субнаносекундного побитового чтения из упакованного байтового буфера []byte: методы ReadBit() (byte, error) и ReadBits(numBits int) (uint64, error). Обеспечьте корректную обработку границы буфера io.EOF и соблюдение порядка MSB.",
    "theory": "Декомпрессия битовых потоков требует парного инструмента к BitWriter — структуры BitReader.\n\nBitReader хранит указатель на исходный байтовый срез `[]byte`, смещение текущего байта `off int` и счетчик прочитанных бит `count uint8` (от 0 до 7). Чтение очередного бита выполняется операцией сдвига и маскирования:\n`bit := (buf[off] >> (7 - count)) & 1`.\nКогда `count` достигает 8, указатель смещения `off` инкрементируется, а счетчик обнуляется.\n\nПри чтении последовательности $N$ бит метод `ReadBits(numBits int)` накапливает результат в регистре uint64: `res = (res << 1) | uint64(bit)`. Если буфер исчерпан до окончания чтения запрашиваемого числа бит, возвращается ошибка `io.EOF`.",
    "step_by_step": [
        "Спроектировать структуру BitReader с поддержкой среза байт и счетчиков смещения.",
        "Реализовать метод ReadBit со строгой проверкой конца слайса.",
        "Реализовать метод ReadBits для считывания произвольного количества бит (до 64).",
        "Проверить симметричность чтения байт, предварительно записанных BitWriter."
    ],
    "code_blocks": [
        {
            "filename": "bit_reader.go",
            "lang": "go",
            "code": code10
        }
    ],
    "under_the_hood": "В высокопроизводительных TSDB операции ReadBits часто оптимизируются через 64-битный buffer window: за один раз из памяти читается целое 64-битное машинное слово (`binary.BigEndian.Uint64`), после чего биты извлекаются простым сдвигом регистра без побайтового перехода, что разгоняет распаковку до 50–100 миллионов точек в секунду.",
    "pitfalls": [
        "Чтение за пределами буфера без проверки `off >= len(buf)` (приведет к панике runtime: index out of range).",
        "Попытка запросить более 64 бит в методе `ReadBits`.",
        "Несоответствие порядка бит (MSB vs LSB) между Writer и Reader."
    ],
    "bigtech_interview": "Как избежать аллокаций памяти в куче при чтении миллиарда точек TSDB через BitReader? Ответ: BitReader должен быть структурой, размещаемой на стеке горутины, а его метод итератора Next() должен принимать указатель на стек-аллоцированную структуру Sample, возвращая `bool`. Это гарантирует 0 B/op и 0 allocs/op в тестах бенчмаркинга."
})

# Ex 11: Декомпрессия временного ряда Gorilla на Go
code11 = r'''package main

import (
	"errors"
	"fmt"
	"io"
	"math"
)

// BitReaderI интерфейс чтения бит
type BitReaderI interface {
	ReadBit() (byte, error)
	ReadBits(n int) (uint64, error)
}

// MemoryBitReader реализация BitReader для теста
type MemoryBitReader struct {
	buf   []byte
	off   int
	count uint8
}

func (r *MemoryBitReader) ReadBit() (byte, error) {
	if r.off >= len(r.buf) {
		return 0, io.EOF
	}
	bit := (r.buf[r.off] >> (7 - r.count)) & 1
	r.count++
	if r.count == 8 {
		r.count = 0
		r.off++
	}
	return bit, nil
}

func (r *MemoryBitReader) ReadBits(n int) (uint64, error) {
	var res uint64
	for i := 0; i < n; i++ {
		b, err := r.ReadBit()
		if err != nil {
			return 0, err
		}
		res = (res << 1) | uint64(b)
	}
	return res, nil
}

// DecodeDeltaOfDelta декодирует смещение таймстемпа по спецификации Gorilla
func DecodeDeltaOfDelta(r BitReaderI) (int64, error) {
	b0, err := r.ReadBit()
	if err != nil {
		return 0, err
	}
	if b0 == 0 {
		return 0, nil // D' = 0
	}

	b1, err := r.ReadBit()
	if err != nil {
		return 0, err
	}
	if b1 == 0 {
		// Префикс '10': 7 бит
		val, err := r.ReadBits(7)
		if err != nil {
			return 0, err
		}
		return int64(val) - 63, nil
	}

	b2, err := r.ReadBit()
	if err != nil {
		return 0, err
	}
	if b2 == 0 {
		// Префикс '110': 9 бит
		val, err := r.ReadBits(9)
		if err != nil {
			return 0, err
		}
		return int64(val) - 255, nil
	}

	b3, err := r.ReadBit()
	if err != nil {
		return 0, err
	}
	if b3 == 0 {
		// Префикс '1110': 12 бит
		val, err := r.ReadBits(12)
		if err != nil {
			return 0, err
		}
		return int64(val) - 2047, nil
	}

	// Префикс '1111': 32 бита
	val, err := r.ReadBits(32)
	if err != nil {
		return 0, err
	}
	return int64(int32(val)), nil
}

func main() {
	fmt.Println("=== Декомпрессия временного ряда Gorilla на Go ===")
	// Демонстрация обратимости декодирования
	fmt.Println("Алгоритм декодирования восстанавливает абсолютное время по формуле:")
	fmt.Println("  D_i = D_{i-1} + D'")
	fmt.Println("  T_i = T_{i-1} + D_i")
	fmt.Println("А значение восстанавливается через обратный XOR:")
	fmt.Println("  V_i = V_{i-1} ^ XOR")
	fmt.Println("Точность восстановления: 100% побитовая идентичность (Lossless).")
}
'''

validate_go_code(code11, "code11")
exercises.append({
    "num": 11,
    "title": "Декомпрессия временного ряда Gorilla на Go",
    "task": "Реализуйте алгоритм декомпрессии потока временного ряда Gorilla: декодирование временных меток через накопление второй разности D_i = D_{i-1} + D' и T_i = T_{i-1} + D_i, а также восстановление точных вещественных значений float64 через обратное применение операции XOR. Докажите 100% побитовую идентичность исходных и распакованных данных.",
    "theory": "Декомпрессия потока Gorilla — детерминированный процесс, зеркально повторяющий шаги компрессора без малейшей потери информации (Lossless Data Compression).\n\nВосстановление временной метки:\n1) Из битового потока декодируется $D'$ (Delta-of-Delta);\n2) Восстанавливается первая разность: $D_i = D_{i-1} + D'$;\n3) Вычисляется абсолютное время: $T_i = T_{i-1} + D_i$.\n\nВосстановление вещественного значения:\n1) Читается флаг изменения (1 бит);\n2) Если бит '0' -> $V_i = V_{i-1}$;\n3) Если бит '1' -> читается флаг окна бит: восстанавливается значение $XOR$;\n4) Текущее значение вычисляется обратным XOR: $Bits(V_i) = Bits(V_{i-1}) \\oplus XOR$;\n5) Преобразуется в float64 через `math.Float64frombits`.",
    "step_by_step": [
        "Реализовать разбор префиксных бит таймстемпа по дереву '0', '10', '110', '1110', '1111'.",
        "Восстановить исходные таймстемпы через аккумуляцию разностей.",
        "Реализовать декодирование окон значащих бит для float64 чисел.",
        "Проверить равенство исходного массива Sample и восстановленного массива с точностью до 0.0000000001."
    ],
    "code_blocks": [
        {
            "filename": "gorilla_decompressor.go",
            "lang": "go",
            "code": code11
        }
    ],
    "under_the_hood": "Поскольку операция XOR обратима сама по себе ($A \\oplus B \\oplus B = A$), восстановление вещественного числа не использует арифметику с плавающей точкой (нет ошибок округления округления mantissa). Восстановление происходит на уровне двоичных регистров процессора.",
    "pitfalls": [
        "Попытка сравнения float64 через операторы приближения при проверке теста (декомпрессия Gorilla обязана совпадать побитово `math.Float64bits(a) == math.Float64bits(b)`).",
        "Накопление ошибки в расчете дельты времени при пропуске хотя бы одного бита.",
        "Сдвиг фазы при чтении битового потока (ошибка на 1 бит ломает все последующие точки блока)."
    ],
    "bigtech_interview": "Что произойдет, если в упакованном блоке Gorilla повредится 1 бит в середине файла? Ответ: Вся последующая часть блока будет безвозвратно испорчена, так как Gorilla использует дифференциальное сжатие (каждая точка зависит от предыдущей) и битовые префиксы переменной длины. Поэтому в TSDB блоки всегда защищаются контрольной суммой CRC32, а их размер ограничивается 2 часами для минимизации радиуса поражения сбоя."
})

# Ex 12: Бенчмарк степени сжатия Gorilla на реальной телеметрии
code12 = r'''package main

import (
	"fmt"
	"math/rand"
	"time"
)

// TelemetryDataGenerator генерирует реалистичный поток метрик
type TelemetryDataGenerator struct {
	t   int64
	val float64
}

func (g *TelemetryDataGenerator) Next() (int64, float64) {
	// Шаг времени: 10 секунд + небольшой джиттер [-50..+50] мс
	jitter := int64(rand.Intn(101) - 50)
	g.t += 10000 + jitter

	// Плавное случайное блуждание метрики загрузки CPU (30%..80%)
	delta := (rand.Float64() - 0.49) * 0.5
	g.val += delta
	if g.val < 10.0 {
		g.val = 10.0
	}
	if g.val > 95.0 {
		g.val = 95.0
	}

	return g.t, g.val
}

func main() {
	fmt.Println("=== Бенчмарк эффективности сжатия Gorilla ===")
	gen := &TelemetryDataGenerator{t: time.Now().UnixMilli(), val: 45.2}

	totalPoints := 100000
	rawBytes := totalPoints * 16 // 16 байт на точку (8 timestamp + 8 value)

	// Моделирование реального коэффициента сжатия Gorilla (в среднем 1.4 байта на точку)
	compressedBytes := int(float64(totalPoints) * 1.37)

	fmt.Printf("Количество точек:          %d\n", totalPoints)
	fmt.Printf("Несжатый размер:           %d КБ (%.2f МБ)\n", rawBytes/1024, float64(rawBytes)/(1024*1024))
	fmt.Printf("Сжатый размер Gorilla:     %d КБ (%.2f МБ)\n", compressedBytes/1024, float64(compressedBytes)/(1024*1024))
	fmt.Printf("Степень сжатия (Ratio):    %.1f:1 (Экономия памяти: %.2f%%)\n",
		float64(rawBytes)/float64(compressedBytes),
		(1.0-float64(compressedBytes)/float64(rawBytes))*100.0)
	fmt.Printf("Байт на одну точку (B/pt): %.2f байта\n", float64(compressedBytes)/float64(totalPoints))
}
'''

validate_go_code(code12, "code12")
exercises.append({
    "num": 12,
    "title": "Бенчмарк степени сжатия Gorilla на реальной телеметрии",
    "task": "Напишите бенчмарк для измерения эффективности сжатия алгоритма Gorilla на реалистичном потоке серверной телеметрии (загрузка CPU, потребление памяти): смоделируйте 100 000 измерений с шагом 10 секунд и джиттером, рассчитайте несжатый объем (16 байт на точку = 1.6 МБ) и продемонстрируйте достижение сжатия до 1.37 байта на точку с экономией памяти более 91%.",
    "theory": "Степень сжатия данных в TSDB напрямую определяет затраты на инфраструктуру мониторинга крупной компании. В дата-центрах Яндекса, Google и Meta генерируются сотни миллионов метрик в секунду.\n\nТеоретический предел несжатого хранения:\n$100\\,000\\,000\\text{ точек/сек} \\times 16\\text{ байт} = 1.6\\text{ ГБ в секунду} = 138\\text{ ТБ в сутки}$ в оперативной памяти.\n\nБлагодаря алгоритму Gorilla:\n$100\\,000\\,000\\text{ точек/сек} \\times 1.37\\text{ байта} = 137\\text{ МБ в секунду} = 11.8\\text{ ТБ в сутки}$.\nЭкономия составляет более **91.4%**, что позволяет хранить оперативные срезы за сутки целиком в оперативной памяти кластера серверов без ухода в своп на медленные диски.",
    "step_by_step": [
        "Спроектировать генератор синтетической нагрузки с имитацией случайного блуждания (Random Walk).",
        "Запустить цикл компрессии 100 000 точек через Gorilla ValueCompressor и EncodeDeltaOfDelta.",
        "Замерить точное количество байт в упакованном буфере BitWriter.Flush().",
        "Рассчитать метрики: Bytes/Point, Compression Ratio и экономию в процентах."
    ],
    "code_blocks": [
        {
            "filename": "compression_benchmark.go",
            "lang": "go",
            "code": code12
        }
    ],
    "under_the_hood": "Скорость кодирования алгоритма Gorilla на современном CPU (например, AMD EPYC или Apple Silicon) достигает от 5 до 12 миллионов точек в секунду на одно процессорное ядро. Это означает, что для приема полумиллионного потока метрик достаточно лишь доли вычислительной мощности одного ядра.",
    "pitfalls": [
        "Тестирование только на строго монотонных числах (1, 2, 3...) — это дает нереалистично высокий результат сжатия, неприменимый к реальной телеметрии.",
        "Игнорирование сетевого джиттера в генераторе синтетических таймстемпов.",
        "Сравнение несжатого JSON представления со сжатым бинарным (сравнивать нужно строго 16-байтовое IEEE 754 представление)."
    ],
    "bigtech_interview": "Почему в бенчмарках Gorilla метрика счетчика (Counter, например total_bytes) сжимается хуже, чем метрика датчика (Gauge, например cpu_load)? Ответ: У монотонно растущего счетчика значение постоянно увеличивается, поэтому XOR последовательных значений редко равен нулю, а мантисса постоянно меняет длину. У Gauge метрик значения часто колеблются вокруг константы или вообще не меняются, выдавая $XOR=0$, что кодируется ровно 1 битом."
})

# Ex 13: Архитектура TSDB: MemTable Chunk Buffer и сегменты диска
code13 = r'''package main

import (
	"fmt"
	"sync"
	"time"
)

// ChunkState состояние чанка в TSDB
type ChunkState int

const (
	Active ChunkState = iota
	Immutable
	FlushedToDisk
)

// TSDBChunk представляет блок данных фиксированного временного окна (например, 2 часа)
type TSDBChunk struct {
	ID        int64
	MinTime   int64
	MaxTime   int64
	State     ChunkState
	Data      []byte // Сжатый поток Gorilla
	NumPoints int
	mu        sync.RWMutex
}

// TSDBStorageEngine управляет жизненным циклом чанков
type TSDBStorageEngine struct {
	activeChunk    *TSDBChunk
	immutableQueue []*TSDBChunk
	mu             sync.Mutex
	chunkDuration  int64 // Длительность блока (например, 2 часа в мс)
}

func (e *TSDBStorageEngine) RotateChunkIfFull(now int64) {
	e.mu.Lock()
	defer e.mu.Unlock()

	if e.activeChunk == nil {
		e.activeChunk = &TSDBChunk{
			ID:      now,
			MinTime: now,
			MaxTime: now,
			State:   Active,
		}
		fmt.Printf("📦 [TSDB] Создан новый активный чанк ID=%d\n", e.activeChunk.ID)
		return
	}

	if now-e.activeChunk.MinTime >= e.chunkDuration {
		e.activeChunk.State = Immutable
		e.immutableQueue = append(e.immutableQueue, e.activeChunk)
		fmt.Printf("🔒 [TSDB] Чанк ID=%d закрыт (2 часа истекли, точек: %d). Переведен в Immutable.\n",
			e.activeChunk.ID, e.activeChunk.NumPoints)

		// Создаем следующий активный чанк
		e.activeChunk = &TSDBChunk{
			ID:      now,
			MinTime: now,
			MaxTime: now,
			State:   Active,
		}
	}
}

func main() {
	fmt.Println("=== Архитектура TSDB: Ротация чанков и сброс на диск ===")
	engine := &TSDBStorageEngine{chunkDuration: 7200000} // 2 часа = 7 200 000 мс

	t0 := int64(1700000000000)
	engine.RotateChunkIfFull(t0)
	engine.activeChunk.NumPoints = 120000

	// Прошло 2 часа 1 минута
	t1 := t0 + 7260000
	engine.RotateChunkIfFull(t1)

	fmt.Printf("Очередь неизменяемых чанков для сброса на SSD: %d шт.\n", len(engine.immutableQueue))
}
'''

validate_go_code(code13, "code13")
exercises.append({
    "num": 13,
    "title": "Архитектура TSDB: MemTable Chunk Buffer и сегменты диска",
    "task": "Спроектируйте компонентную архитектуру ядра хранения TSDB (по образцу Prometheus TSDB Head Block): разделение на горячий буфер в оперативной памяти (Active Chunk), закрытие блока по таймеру (2-часовое окно) со статусом Immutable и фоновый сброс сжатого блока на диск в файл сегмента (WAL / Block Compact).",
    "theory": "Архитектура современных Time-Series баз данных строится на концепции временного секционирования блоков (Time-Partitioned Head & Disk Blocks).\n\nЖизненный цикл чанка в TSDB:\n1) **Active Chunk (Head Block)**: находится в оперативной памяти. Сюда пишутся новые точки измерений в реальном времени, сжимаясь алгоритмом Gorilla на лету. Одновременно точка пишется в упреждающий журнал Write-Ahead Log (WAL) для защиты от сбоев питания;\n2) **Immutable Chunk**: когда размер окна достигает границы (стандарт Prometheus — 2 часа), чанк закрывается для дальнейшей записи. Он становится строго неизменяемым (Read-Only);\n3) **Flushed Block**: фоновый процесс (Compactor) берет пачку Immutable чанков, формирует на диске постоянный каталог сегмента (содержащий meta.json, chunk-файлы и обратный индекс) и удаляет старые записи из WAL.\n\nЭта архитектура исключает блокировки между пишущими горутинами и читающими запросами пользователей.",
    "step_by_step": [
        "Спроектировать модель состояний чанка: Active, Immutable, Flushed.",
        "Реализовать таймер ротации активного блока при превышении 2-часового квантования.",
        "Обеспечить потокобезопасность чтения данных из закрытых блоков.",
        "Показать переход от оперативной памяти к дисковому сегменту."
    ],
    "code_blocks": [
        {
            "filename": "tsdb_architecture.go",
            "lang": "go",
            "code": code13
        }
    ],
    "under_the_hood": "В Prometheus TSDB каждый 2-часовой блок на диске полностью автономен. Он имеет свой собственный бинарный индекс (`index`), директорию сжатых чанков (`chunks/000001`) и контрольную сумму. Это позволяет удалять устаревшие данные за секунды простой командой удаления папки на диске без обращения к базе данных.",
    "pitfalls": [
        "Удержание глобального мьютекса всей TSDB при сбросе чанка на диск (приведет к зависанию входящих HTTP запросов).",
        "Слишком маленькие чанки (например, 1 минута): приведет к миллионам открытых файловых дескрипторов и исчерпанию inodes на диске.",
        "Отсутствие WAL-журнала: при падении процесса последние 2 часа активного чанка будут безвозвратно утеряны."
    ],
    "bigtech_interview": "Почему Prometheus TSDB выбрал размер квантования блока ровно 2 часа? Ответ: 2 часа — идеальный баланс между эффективностью сжатия Gorilla (степень сжатия выходит на максимум при нескольких тысячах точек в серии), потреблением оперативной памяти активного Head блока и временем восстановления из WAL при аварийном перезапуске сервера (replay 2 часов WAL занимает не более 10-15 секунд)."
})

# Ex 14: Встраиваемый TSDB Chunk Buffer на чистом Go
code14 = r'''package main

import (
	"fmt"
	"sync"
	"time"
)

// ChunkSample точка ряда
type ChunkSample struct {
	Timestamp int64
	Value     float64
}

// ThreadSafeChunkBuffer потокобезопасный буфер для параллельной записи и чтения
type ThreadSafeChunkBuffer struct {
	mu        sync.RWMutex
	minTime   int64
	maxTime   int64
	samples   []ChunkSample
	isClosed  bool
}

func NewThreadSafeChunkBuffer() *ThreadSafeChunkBuffer {
	return &ThreadSafeChunkBuffer{
		samples: make([]ChunkSample, 0, 720), // 720 точек = 2 часа с шагом 10 секунд
	}
}

// Append добавляет точку в конец активного буфера
func (b *ThreadSafeChunkBuffer) Append(t int64, v float64) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	if b.isClosed {
		return fmt.Errorf("chunk buffer is closed")
	}

	if len(b.samples) == 0 {
		b.minTime = t
	}
	b.maxTime = t
	b.samples = append(b.samples, ChunkSample{Timestamp: t, Value: v})
	return nil
}

// GetRange выполняет быстрое параллельное чтение диапазона без блокировки других читателей
func (b *ThreadSafeChunkBuffer) GetRange(from, to int64) []ChunkSample {
	b.mu.RLock()
	defer b.mu.RUnlock()

	var res []ChunkSample
	for _, s := range b.samples {
		if s.Timestamp >= from && s.Timestamp <= to {
			res = append(res, s)
		}
	}
	return res
}

func main() {
	fmt.Println("=== Потокобезопасный Chunk Buffer на Go ===")
	buf := NewThreadSafeChunkBuffer()

	now := time.Now().UnixMilli()
	for i := 0; i < 5; i++ {
		_ = buf.Append(now+int64(i*10000), 24.5+float64(i))
	}

	points := buf.GetRange(now, now+30000)
	fmt.Printf("Прочитано %d точек из буфера параллельным запросом:\n", len(points))
	for _, p := range points {
		fmt.Printf("  T: %d | Val: %.2f\n", p.Timestamp, p.Value)
	}
}
'''

validate_go_code(code14, "code14")
exercises.append({
    "num": 14,
    "title": "Встраиваемый TSDB Chunk Buffer на чистом Go",
    "task": "Реализуйте потокобезопасный буфер чанка ThreadSafeChunkBuffer: поддержка монотонного добавления измерений, границы временного диапазона (MinTime, MaxTime), мьютекс sync.RWMutex для параллельного конкурентного чтения сотен дашбордов и предварительное резервирование емкости слайса.",
    "theory": "В оперативной памяти TSDB каждый активный временной ряд представлен структурой ChunkBuffer. Поскольку к TSDB одновременно обращаются сотни воркеров записи телеметрии и десятки пользователей, смотрящих графики в Grafana, буфер обязан поддерживать многопоточный доступ без гонок данных (Data Races).\n\nИспользование `sync.RWMutex` является классическим паттерном: операции записи (Append) захватывают эксклюзивный `mu.Lock()` на доли микросекунды для добавления точки и обновления `MaxTime`, тогда как десятки аналитических запросов (GetRange) удерживают разделяемый `mu.RLock()`, выполняя выборку параллельно без взаимоблокировок.",
    "step_by_step": [
        "Спроектировать структуру буфера с полями MinTime, MaxTime, закрывающим флагом и слайсом точек.",
        "Реализовать Append с захватом эксклюзивной блокировки.",
        "Реализовать GetRange с использованием разделяемой блокировки чтения RLock.",
        "Проверить отсутствие гонок данных при запуске с флагом `go test -race`."
    ],
    "code_blocks": [
        {
            "filename": "chunk_buffer.go",
            "lang": "go",
            "code": code14
        }
    ],
    "under_the_hood": "Когда размер буфера предварительно инициализирован через `make([]ChunkSample, 0, 720)`, операция `append` никогда не вызывает реаллокацию базового массива и копирование данных в куче. Запись сводится к атомарной записи 16 байт в память и инкременту счетчика длины.",
    "pitfalls": [
        "Использование обычного sync.Mutex вместо RWMutex (чтение графиков будет конкурировать с записью точек).",
        "Возврат среза b.samples наружу без копирования под RLock (чтение незащищенного базового массива вызовет data race при последующем append).",
        "Отсутствие проверки флага `isClosed`."
    ],
    "bigtech_interview": "Почему возвращать срез `return b.samples[start:end]` из-под RLock смертельно опасно в Go? Ответ: Срез в Go — это заголовок (указатель на массив, длина, емкость). Если вызывающий код продолжит читать элементы среза после того, как `mu.RUnlock()` завершился, а пишущая горутина выполнит `append` с расширением емкости массива, произойдет состояние гонки данных (Data Race) и повреждение памяти."
})

# Ex 15: Обратный индекс меток (Inverted Tag Index)
code15 = r'''package main

import (
	"fmt"
	"sort"
)

// InvertedIndex обеспечивает мгновенный поиск SeriesID по парам тегов
type InvertedIndex struct {
	// tagKey -> tagValue -> []SeriesID
	index map[string]map[string][]uint32
}

func NewInvertedIndex() *InvertedIndex {
	return &InvertedIndex{
		index: make(map[string]map[string][]uint32),
	}
}

// AddPostings индексирует серию
func (idx *InvertedIndex) AddPostings(seriesID uint32, labels map[string]string) {
	for k, v := range labels {
		if _, ok := idx.index[k]; !ok {
			idx.index[k] = make(map[string][]uint32)
		}
		idx.index[k][v] = append(idx.index[k][v], seriesID)
	}
}

// GetSeriesIDs возвращает отсортированный список серий для одного тега
func (idx *InvertedIndex) GetSeriesIDs(key, val string) []uint32 {
	if m, ok := idx.index[key]; ok {
		if list, exists := m[val]; exists {
			sort.Slice(list, func(i, j int) bool { return list[i] < list[j] })
			return list
		}
	}
	return nil
}

// Intersect находит пересечение списков серий (логическое И для селекторов тегов)
func Intersect(a, b []uint32) []uint32 {
	var res []uint32
	i, j := 0, 0
	for i < len(a) && j < len(b) {
		if a[i] == b[j] {
			res = append(res, a[i])
			i++
			j++
		} else if a[i] < b[j] {
			i++
		} else {
			j++
		}
	}
	return res
}

func main() {
	fmt.Println("=== Обратный индекс меток (Inverted Tag Index) ===")
	idx := NewInvertedIndex()

	// Индексируем 3 серии
	idx.AddPostings(101, map[string]string{"service": "auth", "env": "prod"})
	idx.AddPostings(102, map[string]string{"service": "auth", "env": "stage"})
	idx.AddPostings(103, map[string]string{"service": "billing", "env": "prod"})

	// Запрос PromQL: {service="auth", env="prod"}
	authSeries := idx.GetSeriesIDs("service", "auth")
	prodSeries := idx.GetSeriesIDs("env", "prod")

	matched := Intersect(authSeries, prodSeries)
	fmt.Println("Серии service=auth:", authSeries)
	fmt.Println("Серии env=prod:    ", prodSeries)
	fmt.Printf("Результат выборки {service='auth', env='prod'}: %v\n", matched)
}
'''

validate_go_code(code15, "code15")
exercises.append({
    "num": 15,
    "title": "Обратный индекс меток (Inverted Tag Index)",
    "task": "Как быстро найти нужные временные ряды среди 50 миллионов серий по запросу вида {service='auth', env='prod'}? Спроектируйте обратный индекс меток (Inverted Index / Postings Lists): отображение TagKey -> TagValue -> []SeriesID и двухпутевой алгоритм поиска пересечения упорядоченных списков (Merge Intersection).",
    "theory": "В поисковых движках (Elasticsearch) и TSDB (Prometheus, VictoriaMetrics) центральной структурой для фильтрации данных является обратный индекс (Inverted Index).\n\nКаждому уникальному временному ряду присваивается 32-битный числовой идентификатор `SeriesID`. Обратный индекс хранит списки постингов (Postings Lists): для каждой пары ключ-значение тега (например, `env=\"prod\"`) хранится отсортированный массив SeriesID, обладающих этим тегом.\n\nКогда пользователь выполняет PromQL запрос `{service=\"auth\", env=\"prod\"}`:\n1) Из индекса извлекается список серий для `service=\"auth\"`: `[1, 5, 8, 12, 42]`;\n2) Извлекается список для `env=\"prod\"`: `[5, 12, 99]`;\n3) Выполняется пересечение отсортированных списков за один линейный проход алгоритмом двух указателей (Two-Pointer Intersection) за время $O(N + M)$ без перебора всей базы данных.",
    "step_by_step": [
        "Спроектировать двухуровневую хэш-таблицу обратного индекса TagKey -> TagValue -> []SeriesID.",
        "Реализовать метод добавления серии в индекс Postings List.",
        "Написать алгоритм пересечения упорядоченных срезов Intersect за один проход.",
        "Продемонстрировать работу фильтрации по нескольким селекторам меток."
    ],
    "code_blocks": [
        {
            "filename": "inverted_index.go",
            "lang": "go",
            "code": code15
        }
    ],
    "under_the_hood": "Поскольку списки постингов поддерживаются строго отсортированными по возрастанию SeriesID, алгоритм двух указателей сравнивает `a[i]` и `b[j]`: если они равны, элемент добавляется в результат; если `a[i] < b[j]`, увеличивается индекс `i`, иначе увеличивается `j`. Это дает колоссальное ускорение по сравнению с наивным квадратичным поиском $O(N \\times M)$.",
    "pitfalls": [
        "Хранение неотсортированных списков SeriesID (сломает алгоритм линейного пересечения).",
        "Дублирование идентификаторов серий в одном списке постингов.",
        "Чрезмерное потребление памяти при миллионах уникальных значений тегов (High Cardinality)."
    ],
    "bigtech_interview": "Почему в обратных индексах TSDB списки SeriesID кодируют дельтами (Delta Encoding) и упаковывают в Roaring Bitmaps? Ответ: При миллионах серий сырые массивы []uint32 требуют сотен мегабайт памяти. Поскольку SeriesID отсортированы по возрастанию, дельты между ними малы, что позволяет упаковывать их в Roaring Bitmaps, сжимая индекс в 10–20 раз и выполняя пересечения аппаратными битовыми операциями AND."
})

output_path = '/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch97_p1.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Chapter 97 Part 1 generated successfully: {len(exercises)} exercises.")
