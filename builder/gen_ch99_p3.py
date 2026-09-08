#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import subprocess

def validate_go_code(code, label):
    p = subprocess.run(["gofmt", "-e"], input=code, capture_output=True, text=True)
    if p.returncode != 0:
        raise ValueError(f"Go syntax error in {label}:\n{p.stderr}\nCode:\n{code}")

exercises = []

# Ex 31
code31 = r'''package main

import (
	"context"
	"fmt"
	"strings"
)

type ReActStep struct {
	Thought     string
	Action      string
	ActionInput string
	Observation string
}

type ReActAgent struct {
	maxIterations int
}

func NewReActAgent(maxIterations int) *ReActAgent {
	return &ReActAgent{maxIterations: maxIterations}
}

// ExecuteTool имитирует исполнение Go-инструмента
func (a *ReActAgent) ExecuteTool(action, input string) string {
	switch strings.ToLower(action) {
	case "calculator":
		return "42" // Имитация вычисления математического выражения
	case "database_lookup":
		return fmt.Sprintf("Найдена запись для '%s': статус=ACTIVE, регион=RU-CENTRAL", input)
	default:
		return fmt.Sprintf("Неизвестный инструмент: %s", action)
	}
}

// RunReActLoop эмулирует пошаговый цикл рассуждения и действий агента
func (a *ReActAgent) RunReActLoop(ctx context.Context, goal string) (string, []ReActStep) {
	var steps []ReActStep

	// Шаг 1: Рассуждение и вызов базы данных
	step1 := ReActStep{
		Thought:     "Мне нужно проверить статус сервера в базе данных.",
		Action:      "database_lookup",
		ActionInput: "server-prod-01",
	}
	step1.Observation = a.ExecuteTool(step1.Action, step1.ActionInput)
	steps = append(steps, step1)

	// Шаг 2: Рассуждение и формулирование финального ответа
	finalAnswer := fmt.Sprintf("Сервер server-prod-01 находится в статусе ACTIVE на основе наблюдения: %s", step1.Observation)
	return finalAnswer, steps
}

func main() {
	agent := NewReActAgent(5)
	ans, steps := agent.RunReActLoop(context.Background(), "Проверить состояние server-prod-01")

	fmt.Printf("Финальный ответ ReAct агента: %s\nШагов выполнено: %d\n", ans, len(steps))
	for i, s := range steps {
		fmt.Printf("Шаг %d | Thought: %s | Action: %s(%s) | Obs: %s\n",
			i+1, s.Thought, s.Action, s.ActionInput, s.Observation)
	}
}
'''
validate_go_code(code31, "Ex 31")
exercises.append({
    "num": 31,
    "title": "ReAct Агенты (Reasoning + Acting) на чистом Go",
    "task": "Реализуйте автономный цикл ReAct (Reasoning + Acting) на чистом Go: пошаговая смена состояний 'Thought -> Action -> Observation -> Final Answer', управление счетчиком максимальных шагов и изоляция исполнения внешних инструментов.",
    "theory": """**ReAct (Reasoning and Acting)** — парадигма автономных агентов, объединяющая генерацию логических цепочек рассуждений (Chain-of-Thought) с вызовом внешних API:
1. **Thought (Рассуждение)**: Модель анализирует текущий прогресс к цели: *«Пользователь спросил возраст компании X. Сначала мне нужно найти дату ее основания в базе данных»*.
2. **Action (Действие)**: Модель выбирает инструмент и формирует аргументы: `wiki_search("Company X foundation date")`.
3. **Observation (Наблюдение)**: Бэкенд на Go исполняет инструмент и возвращает сырой результат в контекст: `Observation: 1997 год`.
4. Цикл повторяется, пока модель не сделает вывод `Final Answer: Компании X сейчас 29 лет`.""",
    "step_by_step": [
        "Определите структуру `ReActStep` для фиксации цепочки рассуждений.",
        "Реализуйте диспетчер инструментов `ExecuteTool`.",
        "Организуйте цикл `RunReActLoop` с контролем `maxIterations` и `context.Context`.",
        "Проверьте формирование трассировки шагов."
    ],
    "code_blocks": [code31],
    "under_the_hood": "В цикле ReAct история диалога линейно растет на каждом шаге, так как каждое новое наблюдение добавляется в промпт следующей итерации. В Go важно переиспользовать срезы истории через `make([]ReActStep, 0, maxIterations)` для исключения лишних реаллокаций в куче.",
    "pitfalls": "Отсутствие жесткого счетчика `maxIterations` приведет к бесконечному циклу, если модель начнет повторять одно и то же действие из-за непонятного ответа инструмента.",
    "bigtech_interview": "В чем отличие классического ReAct цикла от Function Calling?\nОтвет: В классическом ReAct агент генерирует текст рассуждения ('Thought:') в едином текстовом потоке вместе с вызовом, что позволяет наблюдать за ходом мыслей модели (CoT). В нативном Function Calling вызов происходит через специальный протокол структурированных фреймов API провайдера без текстовых рассуждений. В современных системах эти подходы объединяют: модель сначала выводит CoT-рассуждения, а затем генерирует нативный tool_call."
})

# Ex 32
code32 = r'''package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
)

type InvoiceExtraction struct {
	InvoiceNumber string  `json:"invoice_number"`
	VendorName    string  `json:"vendor_name"`
	TotalAmount   float64 `json:"total_amount"`
	Currency      string  `json:"currency"`
	InvoiceDate   string  `json:"invoice_date"`
}

type MultimodalImagePayload struct {
	Type     string `json:"type"` // "image_url"
	ImageURL struct {
		URL string `json:"url"` // "data:image/jpeg;base64,..."
	} `json:"image_url"`
}

func EncodeImageToBase64(imgBytes []byte, mimeType string) MultimodalImagePayload {
	encoded := base64.StdEncoding.EncodeToString(imgBytes)
	dataURL := fmt.Sprintf("data:%s;base64,%s", mimeType, encoded)

	var payload MultimodalImagePayload
	payload.Type = "image_url"
	payload.ImageURL.URL = dataURL
	return payload
}

func main() {
	sampleImageBytes := []byte("FAKE_JPEG_IMAGE_BINARY_DATA_FOR_OCR")
	payload := EncodeImageToBase64(sampleImageBytes, "image/jpeg")

	expectedJSON := `{
		"invoice_number": "INV-2026-9901",
		"vendor_name": "Cloud Infra LLC",
		"total_amount": 145000.00,
		"currency": "RUB",
		"invoice_date": "2026-09-08"
	}`

	var invoice InvoiceExtraction
	_ = json.Unmarshal([]byte(expectedJSON), &invoice)

	fmt.Printf("Multimodal Image Payload Data URI префикс: %.30s...\n", payload.ImageURL.URL)
	fmt.Printf("Извлечен счет: №%s от %s на сумму %.2f %s\n",
		invoice.InvoiceNumber, invoice.InvoiceDate, invoice.TotalAmount, invoice.Currency)
}
'''
validate_go_code(code32, "Ex 32")
exercises.append({
    "num": 32,
    "title": "Multimodal API: Обработка изображений, аудио и документов",
    "task": "Спроектируйте интеграцию с мультимодальными моделями (GPT-4o, Claude 3.5 Sonnet): кодирование графических файлов в Base64 Data URL и структурированное извлечение атрибутов финансовых документов (счетов-фактур) в Go-структуру InvoiceExtraction.",
    "theory": """Современные передовые модели являются **мультимодальными (Vision/Audio Multimodal)** — они способны одновременно анализировать текст, архитектурные диаграммы, сканы счетов, скриншоты интерфейсов и таблицы.
Передача изображений в API поддерживается двумя путями:
1. **Публичный HTTPS URL**: Модель самостоятельно скачивает изображение по ссылке. Не подходит для приватных корпоративных данных и локальных инсталляций.
2. **Base64 Data URI Scheme**: Изображение кодируется в ASCII-строку вида `data:image/png;base64,iVBORw0KGgo...` и передается напрямую в теле JSON-запроса.
В связке с режимом Structured Outputs мультимодальный конвейер на Go заменяет сложные устаревшие OCR-системы (Tesseract), безошибочно извлекая табличные данные, печати и подписи напрямую в строго типизированные структуры.""",
    "step_by_step": [
        "Определите типы `MultimodalImagePayload` и `InvoiceExtraction`.",
        "Реализуйте функцию `EncodeImageToBase64` с использованием `base64.StdEncoding`.",
        "Сформируйте Data URL строку с корректным MIME-типом (`image/jpeg`, `image/png`, `image/webp`).",
        "Проверьте парсинг структурированного ответа в поля структуры счета."
    ],
    "code_blocks": [code32],
    "under_the_hood": "Кодирование в Base64 увеличивает размер передаваемых бинарных данных ровно на 33% (каждые 3 байта преобразуются в 4 ASCII-символа). При передаче изображений высокого разрешения в Go критически важно сжимать картинки на лету или уменьшать разрешение до 1024x1024 через стандартный пакет `image/jpeg`.",
    "pitfalls": "Отправка картинок весом более 10 МБ в Base64 может вызвать ошибку 413 Payload Too Large веб-сервера API провайдера.",
    "bigtech_interview": "Как рассчитывается расход токенов при передаче изображений в Vision-модели?\nОтвет: Модель не читает байты картинки по буквам; изображение разбивается на сетку тайлов (патчей) фиксированного размера (например, 512x512 пикселей). Каждый тайл кодируется фиксированным количеством Vision-токенов (обычно 170-255 токенов на тайл) плюс базовый оверхед заголовочного тайла. Поэтому масштабирование разрешения до отправки напрямую снижает затраты на инференс."
})

# Ex 33
code33 = r'''package main

import (
	"context"
	"fmt"
)

type HyDEPipeline struct {
	MockLLMResponse string
}

// GenerateHypotheticalDocument эмулирует генерацию гипотетического документа (Zero-Shot Passage)
func (p *HyDEPipeline) GenerateHypotheticalDocument(ctx context.Context, shortQuery string) string {
	// Если вопрос: "Что такое epoll в Go?", модель генерирует правдоподобный отрывок статьи:
	return fmt.Sprintf("Сетевой стек Go использует системный вызов epoll в Linux для реализации Netpoller. Он обеспечивает неблокирующий ввод-вывод для сокетов без блокировки тредов операционной системы. Вопрос был: %s", shortQuery)
}

func main() {
	hyde := &HyDEPipeline{}
	userQuery := "Netpoller epoll"

	// 1. Вместо векторизации короткого запроса из 2 слов генерируем гипотетический документ
	hypotheticalDoc := hyde.GenerateHypotheticalDocument(context.Background(), userQuery)

	fmt.Printf("Исходный запрос пользователя: %q\n", userQuery)
	fmt.Printf("Сгенерированный гипотетический документ для векторизации (HyDE):\n%s\n", hypotheticalDoc)
}
'''
validate_go_code(code33, "Ex 33")
exercises.append({
    "num": 33,
    "title": "Гипотетические документы (HyDE: Hypothetical Document Embeddings)",
    "task": "Изучите и реализуйте технику повышения качества векторного поиска HyDE (Hypothetical Document Embeddings): трансформация короткого абстрактного запроса пользователя в подробный гипотетический ответ перед векторизацией.",
    "theory": """Фундаментальная проблема классического векторного поиска: **Асимметрия запроса и документа**.
- Запрос пользователя: Короткий, вопросительный, неполный (*«Netpoller epoll Go»* — 3 слова).
- Документ в базе знаний: Длинный, утвердительный, повествовательный абзац технической документации.
Поскольку эти тексты имеют совершенно разную грамматическую структуру и длину, их векторы в пространстве эмбеддингов могут находиться далеко друг от друга!
**Техника HyDE (Hypothetical Document Embeddings)**:
1. Запрос пользователя отправляется в быструю LLM с промптом: *«Напиши краткий гипотетический абзац статьи, отвечающий на вопрос»*.
2. Модель генерирует черновой текст ответа (он может содержать мелкие фактические неточности, но обладает идеальной семантической структурой и лексикой документа).
3. Векторизуется именно этот **гипотетический документ**, а не исходный 3-словный запрос.
4. Векторный поиск в pgvector ищет «документ, похожий на документ», что повышает Recall на 15–30%.""",
    "step_by_step": [
        "Спроектируйте пайплайн `HyDEPipeline`.",
        "Реализуйте метод `GenerateHypotheticalDocument`.",
        "Объясните, почему вектор гипотетического документа ближе к целевым статьям базы знаний.",
        "Продемонстрируйте работу в консоли."
    ],
    "code_blocks": [code33],
    "under_the_hood": "Эмбеддинг-модели обучаются методом Contrastive Learning на парах (документ, похожий документ). При использовании HyDE мы переводим задачу из плоскости Asymmetric Search (Query-to-Doc) в плоскость Symmetric Search (Doc-to-Doc), где плотность векторного пространства наиболее однородна.",
    "pitfalls": "HyDE добавляет задержку одного вызова LLM (200–500 мс). Не рекомендуется применять HyDE для простых точных запросов с артикулами, где эффективнее использовать BM25.",
    "bigtech_interview": "Что произойдет, если LLM при генерации гипотетического документа допустит фактическую ошибку (галлюцинацию)?\nОтвет: На удивление, HyDE устойчив к мелким фактологическим ошибкам модели. Главная ценность гипотетического документа — семантический каркас, профессиональная терминология и контекстуальное распределение слов. Даже если модель ошиблась в конкретной цифре, вектор текста все равно укажет в точную предметную область документации."
})

# Ex 34
code34 = r'''package main

import (
	"fmt"
)

type ChildChunk struct {
	ID        string
	ParentID  string
	Content   string
	Embedding []float32
}

type ParentChunk struct {
	ID      string
	Content string
}

type HierarchicalVectorStore struct {
	parents map[string]ParentChunk
	children []ChildChunk
}

func NewHierarchicalVectorStore() *HierarchicalVectorStore {
	return &HierarchicalVectorStore{
		parents: make(map[string]ParentChunk),
	}
}

func (s *HierarchicalVectorStore) AddDocument(parentID, fullText string, subSections []string) {
	s.parents[parentID] = ParentChunk{ID: parentID, Content: fullText}
	for i, sub := range subSections {
		s.children = append(s.children, ChildChunk{
			ID:       fmt.Sprintf("%s_c%d", parentID, i+1),
			ParentID: parentID,
			Content:  sub,
		})
	}
}

// RetrieveContext возвращает родительский контекст целиком при совпадении дочернего чанка
func (s *HierarchicalVectorStore) RetrieveContext(matchedChildID string) (ParentChunk, bool) {
	for _, child := range s.children {
		if child.ID == matchedChildID {
			parent, ok := s.parents[child.ParentID]
			return parent, ok
		}
	}
	return ParentChunk{}, false
}

func main() {
	store := NewHierarchicalVectorStore()
	parentDoc := "Глава 48: Планировщик GMP в Go. Включает устройство структур G, M, P, системный монитор sysmon и алгоритм work-stealing."
	children := []string{
		"Структура G представляет горутину с собственным стеком.",
		"Sysmon работает в отдельном потоке без P и выполняет упреждающую вытесняющую многозадачность.",
	}

	store.AddDocument("ch48", parentDoc, children)
	parent, found := store.RetrieveContext("ch48_c2")

	fmt.Printf("Поиск совпал по детальному дочернему чанку ch48_c2.\nВ контекст LLM подставляется родительский блок целиком (found=%t):\n%s\n",
		found, parent.Content)
}
'''
validate_go_code(code34, "Ex 34")
exercises.append({
    "num": 34,
    "title": "Иерархическое чанкование: Parent-Child Chunking",
    "task": "Спроектируйте архитектуру двухуровневого иерархического хранения чанков (Parent-Child Chunking): поиск векторного сходства выполняется по гранулярным дочерним фрагментам (200 токенов), но в системный промпт LLM подставляется родительский раздел целиком (1500 токенов).",
    "theory": """В проектировании RAG существует фундаментальная дилемма размера чанка:
- **Маленькие чанки (100–200 токенов)**: Идеальны для векторного поиска (высокая плотность смысла, точечные совпадения), но содержат слишком мало контекста для полноценного ответа LLM.
- **Большие чанки (1000–2000 токенов)**: Идеальны для понимания моделью причинно-следственных связей, но «размывают» векторный эмбеддинг, ухудшая точность поиска.
**Parent-Child (Hierarchical) Chunking**:
1. Большой документ делится на крупные родительские фрагменты (`Parent Chunks` по 1500 токенов).
2. Каждый родительский фрагмент нарезается на мелкие дочерние чанки (`Child Chunks` по 200 токенов).
3. Векторизуются только дочерние чанки.
4. При поиске находится дочерний чанк, но система по ссылке `ParentID` извлекает родительский блок целиком и передает его в модель!""",
    "step_by_step": [
        "Определите типы `ParentChunk` и `ChildChunk` с внешним ключом `ParentID`.",
        "Реализуйте хранилище `HierarchicalVectorStore`.",
        "Напишите метод `RetrieveContext`, возвращающий полный контекст родителя по ID дочернего элемента.",
        "Проверьте работу в консоли."
    ],
    "code_blocks": [code34],
    "under_the_hood": "В PostgreSQL такая схема реализуется двумя таблицами `parent_documents` и `child_chunks` со связью Foreign Key `ON DELETE CASCADE`. Векторный индекс HNSW строится только по дочерней таблице, а извлечение родителя выполняется по первичному B-Tree ключу за микросекунды.",
    "pitfalls": "Если несколько дочерних чанков из одного родителя попали в Top-5 поисковой выдачи, необходимо выполнить дедупликацию по `ParentID`, чтобы не передавать в промпт дубликаты одного и того же родительского текста.",
    "bigtech_interview": "Почему Parent-Child Chunking превосходит наивное увеличение размера чанков с 500 до 2000 токенов?\nОтвет: При размере чанка 2000 токенов вектор эмбеддинга представляет собой математическое среднее от сотен разнородных предложений, из-за чего косинусное расстояние до точечного вопроса пользователя сильно деградирует. Parent-Child сохраняет идеальную резкость векторного поиска (маленький чанк) при сохранении максимальной полноты контекста для генерации (большой чанк)."
})

# Ex 35
code35 = r'''package main

import (
	"fmt"
	"sort"
)

type CandidateDocument struct {
	ID           string
	Content      string
	VectorScore  float64
	RerankScore  float64
}

// MockCrossEncoderRerank имитирует работу Cross-Encoder модели (например, bge-reranker-large или Cohere Rerank)
func MockCrossEncoderRerank(query string, candidates []CandidateDocument) []CandidateDocument {
	for i := range candidates {
		// Кросс-энкодер оценивает глубокое внимание [CLS] query [SEP] document [SEP]
		// Имитация: если в тексте документа есть совпадение ключевой фразы, скор резко растет
		score := candidates[i].VectorScore * 0.5
		if len(candidates[i].Content) > 20 {
			score += 0.45
		}
		candidates[i].RerankScore = score
	}

	sort.Slice(candidates, func(i, j int) bool {
		return candidates[i].RerankScore > candidates[i].RerankScore // по убыванию
	})

	return candidates
}

func main() {
	candidates := []CandidateDocument{
		{ID: "doc_1", Content: "Сборщик мусора Go", VectorScore: 0.88},
		{ID: "doc_2", Content: "Управление памятью в Go: TCMalloc, mcache и детальный разбор триколор GC", VectorScore: 0.82},
		{ID: "doc_3", Content: "Обзор сборщиков мусора в Java и Python", VectorScore: 0.85},
	}

	reranked := MockCrossEncoderRerank("триколор GC", candidates)
	fmt.Println("=== Результаты двухэтапного поиска с Cross-Encoder Reranking ===")
	for i, c := range reranked {
		fmt.Printf("%d. ID: %s | Исходный векторный скор: %.2f | Rerank скор: %.2f | Текст: %s\n",
			i+1, c.ID, c.VectorScore, c.RerankScore, c.Content)
	}
}
'''
validate_go_code(code35, "Ex 35")
exercises.append({
    "num": 35,
    "title": "Двухэтапный поиск с кросс-энкодером (Cross-Encoder Re-ranking)",
    "task": "Спроектируйте архитектуру двухэтапного поиска (Two-Stage Retrieval): быстрый отбор кандидатов векторным индексом (Top-50) и высокоточное переранжирование через модель-кросс-энкодер (Top-5).",
    "theory": """В информационном поиске существует разделение моделей на Bi-Encoder и Cross-Encoder:
1. **Bi-Encoder (Векторный поиск)**:
   - Векторизует запрос и документ независимо друг от друга ($v_q = f(q), v_d = f(d)$).
   - Быстрый ($O(\\log N)$ благодаря HNSW), но не учитывает перекрестное внимание между словами запроса и документа.
2. **Cross-Encoder (Reranker)**:
   - Принимает пару строк на один вход: `[CLS] Вопрос [SEP] Документ [SEP]`.
   - Механизм Self-Attention вычисляет внимание каждого слова вопроса к каждому слову документа одновременно.
   - Дает непревзойденную точность, но работает медленно (вычисление для 100 000 документов заняло бы минуты).
**Двухэтапный конвейер (Two-Stage Pipeline)**:
- Этап 1: Bi-Encoder в pgvector мгновенно отбирает 50 кандидатов из миллиона.
- Этап 2: Cross-Encoder (локальная ONNX модель или API) переранжирует 50 кандидатов за 20 мс и отбирает 5 лучших в промпт.""",
    "step_by_step": [
        "Определите структуру кандидата `CandidateDocument` с исходным и финальным скором.",
        "Реализуйте функцию `MockCrossEncoderRerank`.",
        "Выполните сортировку кандидатов по `RerankScore` с помощью `sort.Slice`.",
        "Продемонстрируйте изменение порядка ранжирования."
    ],
    "code_blocks": [code35],
    "under_the_hood": "Кросс-энкодер не использует векторные индексы, возвращая скалярный логит вероятности соответствия (Logits). В Go вызов локального кросс-энкодера часто реализуется через привязку к C++ библиотеке ONNX Runtime через CGO, инференс батча из 50 пар занимает ~15-25 мс на CPU.",
    "pitfalls": "Отправка более 100 кандидатов на этап реранкинга создаст узкое место по latency всего сервиса (>500 мс). Оптимальный размер пула кандидатов: 30–50 документов.",
    "bigtech_interview": "Почему связка pgvector (Bi-Encoder) + Reranker (Cross-Encoder) считается золотым стандартом Enterprise RAG систем?\nОтвет: Она объединяет масштабируемость векторных баз данных на миллиардах записей со снайперской точностью полного механизма внимания Transformers. Bi-Encoder отсекает 99.99% нерелевантного пространства, а Cross-Encoder гарантирует, что в ограниченное контекстное окно LLM попадут только безупречно точные фрагменты."
})

# Ex 36
code36 = r'''package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

// StreamingTokenJSONParser демонстрирует базовый алгоритм извлечения готовых полей из незавершенного JSON-потока
type StreamingTokenJSONParser struct {
	buffer strings.Builder
}

func (p *StreamingTokenJSONParser) AppendChunk(token string) {
	p.buffer.WriteString(token)
}

func (p *StreamingTokenJSONParser) TryExtractField(fieldName string) (string, bool) {
	raw := p.buffer.String()
	needle := fmt.Sprintf("%q:", fieldName)
	idx := strings.Index(raw, needle)
	if idx == -1 {
		return "", false
	}

	rest := strings.TrimSpace(raw[idx+len(needle):])
	if strings.HasPrefix(rest, "\"") {
		// Поле является строкой
		endQuote := strings.Index(rest[1:], "\"")
		if endQuote != -1 {
			return rest[1 : 1+endQuote], true
		}
	}

	return "", false
}

func main() {
	parser := &StreamingTokenJSONParser{}

	// Имитация потокового поступления токенов
	streamTokens := []string{
		"{\n",
		"  \"status\":",
		" \"SUCCESS\",\n",
		"  \"message\": \"Система работа",
		"ет штатно\",\n",
		"  \"latency_ms\": 42\n}",
	}

	for i, tok := range streamTokens {
		parser.AppendChunk(tok)
		if val, ok := parser.TryExtractField("status"); ok {
			fmt.Printf("Токен %d: Успешно извлечено поле 'status' = %q до завершения всего JSON!\n", i, val)
			break
		}
	}
}
'''
validate_go_code(code36, "Ex 36")
exercises.append({
    "num": 36,
    "title": "Структурированный потоковый парсер (Partial JSON Streaming Parser)",
    "task": "Реализуйте потоковый синтаксический анализатор неполного JSON (Partial JSON Streaming Parser) на Go, способный на лету извлекать готовые поля структуры данных до завершения полной генерации ответа моделью.",
    "theory": """При использовании Structured Outputs в сочетании с SSE-стримингом токены JSON-структуры прибывают по частям на протяжении секунд:
```
Token 1: { "title":
Token 2: "Анализ
Token 3: нагрузки",
Token 4: "details": ...
```
Стандартный парсер `json.Unmarshal` бессилен: при передаче неполной строки он возвращает ошибку синтаксиса `unexpected end of JSON input`.
**Потоковый Partial JSON парсер**:
- Анализирует поток токенов в реальном времени.
- Закрывает незавершенные кавычки, скобки и фигурные скобки виртуальными маркерами.
- Позволяет фронтенду и клиентским интерфейсам отображать готовые поля (например, заголовок отчета или прогресс-бар) мгновенно, не дожидаясь окончания всей генерации.""",
    "step_by_step": [
        "Создайте структуру `StreamingTokenJSONParser` с накопительным буфером.",
        "Реализуйте метод `AppendChunk` для добавления входящих токенов.",
        "Реализуйте метод `TryExtractField` для поиска и извлечения завершенных строковых полей.",
        "Продемонстрируйте извлечение поля на промежуточном шаге стриминга."
    ],
    "code_blocks": [code36],
    "under_the_hood": "В продакшене потоковые парсеры строятся на базе конечного автомата (Finite State Machine, FSM) с отслеживанием стека открытых скобок `['{', '[']`. Когда требуется распарсить текущее состояние, парсер создает временный срез байт, дописывает в конец недостающие закрывающие скобки и вызывает декодер.",
    "pitfalls": "Наивный парсинг регулярными выражениями падает на экранированных кавычках внутри строк `\\\"`. Необходимо учитывать escape-последовательности.",
    "bigtech_interview": "Зачем в UI/UX ИИ-ассистентов нужен частичный парсинг JSON, если можно подождать завершения ответа?\nОтвет: Пользователи ожидают немедленной визуальной реакции (Time to First Visual Cue). Если модель генерирует форму из 10 полей, частичный парсер позволяет отрисовывать поля формы в браузере одно за другим по мере генерации, создавая ощущение мгновенного отклика вместо долгого пустого спиннера загрузки."
})

# Ex 37
code37 = r'''package main

import (
	"fmt"
)

type RouteTarget string

const (
	RouteSupport RouteTarget = "CUSTOMER_SUPPORT"
	RouteBilling RouteTarget = "BILLING_SERVICE"
	RouteTech    RouteTarget = "TECH_ARCH_HELP"
)

type SemanticRoute struct {
	Target    RouteTarget
	Embedding []float32
}

type SemanticRouter struct {
	routes []SemanticRoute
}

func (r *SemanticRouter) Classify(queryEmbedding []float32) RouteTarget {
	var bestTarget RouteTarget
	var maxSim float32 = -1.0

	for _, route := range r.routes {
		sim := dotProductNorm(queryEmbedding, route.Embedding)
		if sim > maxSim {
			maxSim = sim
			bestTarget = route.Target
		}
	}
	return bestTarget
}

func dotProductNorm(a, b []float32) float32 {
	var sum float32
	for i := 0; i < len(a); i++ {
		sum += a[i] * b[i]
	}
	return sum
}

func main() {
	router := &SemanticRouter{
		routes: []SemanticRoute{
			{Target: RouteBilling, Embedding: []float32{0.9, 0.1, 0.0}},
			{Target: RouteTech, Embedding: []float32{0.1, 0.9, 0.0}},
			{Target: RouteSupport, Embedding: []float32{0.0, 0.1, 0.9}},
		},
	}

	// Запрос про оплату
	billingQuery := []float32{0.85, 0.15, 0.0}
	route := router.Classify(billingQuery)

	fmt.Printf("Семантический маршрутизатор направил запрос в: %s (задержка < 1 мс)\n", route)
}
'''
validate_go_code(code37, "Ex 37")
exercises.append({
    "num": 37,
    "title": "Семантический маршрутизатор запросов (Semantic Router)",
    "task": "Реализуйте сверхбыстрый классификатор намерений пользователя (Semantic Router) на Go: классификация маршрута запроса ('Биллинг', 'Архитектура', 'Саппорт') через векторное сходство за время < 1 мс без дорогих вызовов языковой модели.",
    "theory": """Традиционный подход к классификации входящих интентов (маршрутизации запроса пользователя к нужному микросервису или RAG-индексу) — вызов отдельной языковой модели с промптом: *«Определи категорию вопроса: A, B или C»*.
Недостатки:
- Задержка 500–1500 мс на каждый запрос.
- Дополнительные финансовые затраты на токены.
**Семантический маршрутизатор (Semantic Router)**:
1. Для каждой целевой категории заранее вычисляется усредненный векторный центроид эталонных фраз.
2. Входящий вопрос векторизуется моделью эмбеддингов.
3. В памяти Go вычисляется скалярное произведение с центроидами маршрутов.
4. Маршрут с максимальным косинусным сходством выбирается за 0.05 миллисекунды!""",
    "step_by_step": [
        "Определите типы `RouteTarget` и `SemanticRoute`.",
        "Реализуйте структуру `SemanticRouter` со срезом зарегистрированных маршрутов.",
        "Напишите метод `Classify`, находящий ближайший центроид по косинусному расстоянию.",
        "Продемонстрируйте мгновенную маршрутизацию запроса."
    ],
    "code_blocks": [code37],
    "under_the_hood": "Поскольку количество маршрутов в компании обычно не превышает нескольких десятков, поиск в срезе Go укладывается в процессорный кэш L1, выполняясь за сотни наносекунд без единого системного вызова.",
    "pitfalls": "Если запрос находится на границе двух тем (низкая уверенность, малая разница между скорами), классификатор должен иметь fallback-маршрут по умолчанию.",
    "bigtech_interview": "В чем преимущество Semantic Router перед классическими ML-классификаторами (например, Random Forest или Naive Bayes)?\nОтвет: Semantic Router не требует долгого переобучения модели при добавлении новых маршрутов. Чтобы добавить новую категорию, достаточно добавить пару примеров предложений в конфигурацию сервиса, получить их эмбеддинги и добавить в срез маршрутизатора прямо во время работы (Zero-Downtime Hot Reload)."
})

# Ex 38
code38 = r'''package main

import (
	"context"
	"fmt"
	"strings"
	"sync"
)

type DialogueHistory struct {
	mu       sync.Mutex
	messages []string
	summary  string
}

func (h *DialogueHistory) AddMessage(msg string) {
	h.mu.Lock()
	defer h.mu.Unlock()
	h.messages = append(h.messages, msg)
}

// CompressIfNeeded запускает фоновую суммаризацию при превышении лимита сообщений
func (h *DialogueHistory) CompressIfNeeded(ctx context.Context, threshold int) {
	h.mu.Lock()
	defer h.mu.Unlock()

	if len(h.messages) <= threshold {
		return
	}

	// Суммаризируем старые сообщения
	toSummarize := h.messages[:len(h.messages)-2]
	h.messages = h.messages[len(h.messages)-2:] // оставляем только последние 2 реплики

	// Имитация сжатия через LLM
	h.summary = fmt.Sprintf("Ранее обсуждалось: %s", strings.Join(toSummarize, "; "))
}

func (h *DialogueHistory) GetFullContext() string {
	h.mu.Lock()
	defer h.mu.Unlock()

	var sb strings.Builder
	if h.summary != "" {
		sb.WriteString("[СВОДКА ДИАЛОГА]: " + h.summary + "\n")
	}
	for _, m := range h.messages {
		sb.WriteString("- " + m + "\n")
	}
	return sb.String()
}

func main() {
	history := &DialogueHistory{}
	history.AddMessage("User: Привет, расскажи про каналы в Go")
	history.AddMessage("Assistant: Каналы обеспечивают связь между горутинами")
	history.AddMessage("User: А что если канал закрыт?")
	history.AddMessage("Assistant: Чтение вернет дефолтное значение и false")

	history.CompressIfNeeded(context.Background(), 3)
	fmt.Printf("Итоговый контекст диалога после компрессии памяти:\n%s", history.GetFullContext())
}
'''
validate_go_code(code38, "Ex 38")
exercises.append({
    "num": 38,
    "title": "Контекстное окно и сжатие диалога (Conversation Summary Memory)",
    "task": "Спроектируйте систему долговременной диалоговой памяти Conversation Summary Memory: фоновая суммаризация устаревших реплик при превышении порогового лимита сообщений и бесшовная склейка сводки с активными сообщениями.",
    "theory": """При многочасовом диалоге с ассистентом (например, при парном программировании или расследовании инцидента) количество сообщений превышает десятки.
Паттерн **Conversation Summary Memory**:
1. Ведется учет количества реплик или токенов.
2. При превышении порога (например, 10 сообщений) ранние реплики передаются в легковесную модель для генерации краткой выжимки (Summary).
3. Старые сообщения удаляются из оперативного контекста, а выжимка помещается в специальный системный блок: `[SUMMARY OF CONVERSATION SO FAR: ...]`.
4. Последние $K$ сообщений (например, 2–4 реплики) сохраняются в неизменном виде для сохранения оперативной нити разговора.""",
    "step_by_step": [
        "Определите структуру `DialogueHistory` с полями `messages`, `summary` и мьютексом.",
        "Реализуйте метод `CompressIfNeeded`.",
        "Реализуйте сборку контекста `GetFullContext`.",
        "Проверьте работу сжатия диалога."
    ],
    "code_blocks": [code38],
    "under_the_hood": "Суммаризация может выполняться асинхронно в фоновой горутине, чтобы не блокировать текущий ответ пользователю. Новая сводка атомарно подменяет старую ссылку через указатель, обеспечивая Lock-Free чтение для активных стримов.",
    "pitfalls": "Если суммаризировать всю историю включая последнюю реплику, модель потеряет контекст текущего вопроса пользователя. Последние сообщения обязаны оставаться нетронутыми.",
    "bigtech_interview": "Как сохранить критически важные факты (например, пароль или имя пользователя) от утери при циклической суммаризации диалога?\nОтвет: Через паттерн Entity Memory: параллельно с текстовой суммаризацией ведется Key-Value хранилище извлеченных сущностей (`user_id = 42, preferred_language = Go`). Этот блок сущностей инжектируется в системный промпт независимо от текстовой выжимки диалога."
})

# Ex 39
code39 = r'''package main

import (
	"fmt"
	"math"
)

// PureGoEmbeddingSimulation демонстрирует концепцию инференса плотных представлений без внешних сетевых вызовов
type LocalModelRunner struct {
	dimensions int
}

func NewLocalModelRunner(dimensions int) *LocalModelRunner {
	return &LocalModelRunner{dimensions: dimensions}
}

// ComputeLocalEmbedding эмулирует вычисление эмбеддинга прямо в процессе Go (через Wasm Wazero или ONNX Runtime CGO)
func (r *LocalModelRunner) ComputeLocalEmbedding(text string) []float32 {
	vec := make([]float32, r.dimensions)
	// Детерминированная имитация работы нейросетевого слоя инференса
	for i := 0; i < len(text); i++ {
		idx := int(text[i]) % r.dimensions
		vec[idx] += float32(text[i])
	}

	// L2-нормализация
	var sum float64
	for _, v := range vec {
		sum += float64(v * v)
	}
	norm := float32(math.Sqrt(sum))
	if norm > 0 {
		for i := range vec {
			vec[i] /= norm
		}
	}
	return vec
}

func main() {
	runner := NewLocalModelRunner(384) // Размерность all-MiniLM-L6-v2
	emb := runner.ComputeLocalEmbedding("Golang High Performance In-Process AI")

	fmt.Printf("Локальный In-Process эмбеддинг успешно сгенерирован: размерность=%d, первые 3 значения: [%.4f, %.4f, %.4f]\n",
		len(emb), emb[0], emb[1], emb[2])
}
'''
validate_go_code(code39, "Ex 39")
exercises.append({
    "num": 39,
    "title": "Inference ONNX-моделей прямо внутри Go через CGO / Pure Go Wasm",
    "task": "Изучите способы запуска локального инференса нейросетей непосредственно внутри Go-процесса (In-Process Inference): CGO-биндинги к ONNX Runtime и WebAssembly-песочницы (Wazero) для вычисления эмбеддингов за < 2 мс без сетевых вызовов.",
    "theory": """Обращение к внешним микросервисам на Python для векторизации каждого короткого предложения добавляет 5–15 мс сетевой задержки (TCP Handshake, HTTP сериализация, context switch).
Способы запуска моделей внутри Go:
1. **ONNX Runtime через CGO**: Microsoft ONNX Runtime написан на C++ и предоставляет бинарный C API. С помощью CGO Go-процесс загружает файл `.onnx` и исполняет модель на ядрах процессора с задействованием инструкций AVX-512. Задержка: 1–3 мс.
2. **WebAssembly (Wazero)**: Модель компилируется в Wasm байткод и выполняется чистым Go-рантаймом Wazero без необходимости CGO и компиляторов gcc/clang. 100% кросс-платформенность и безопасная изоляция памяти.""",
    "step_by_step": [
        "Определите структуру `LocalModelRunner` с заданной размерностью вектора.",
        "Реализуйте метод `ComputeLocalEmbedding` с нормализацией L2.",
        "Объясните различия между CGO и WebAssembly подходами для инференса.",
        "Проверьте генерацию нормализованного вектора."
    ],
    "code_blocks": [code39],
    "under_the_hood": "В связке с CGO вызов функции C-кода переключает стек горутины на системный стек потока ОС (`pthread`) и блокирует текущую $M$. При высокой частоте вызовов рекомендуется выделять отдельный пул системных потоков через `runtime.LockOSThread`.",
    "pitfalls": "При сборке с CGO теряется возможность легкой статической компиляции (`CGO_ENABLED=0`) для образов Scratch Docker.",
    "bigtech_interview": "Когда оправдан In-Process инференс в Go вместо выделенного кластера vLLM/Triton?\nОтвет: Для легковесных моделей (эмбеддинги MiniLM, классификация токсичности, детекция языка, сентимент-анализ), где задержка сети превышает время самого вычисления. Для гигантских генеративных LLM (7B-70B параметров) инференс обязан оставаться на выделенных GPU-нодах (Triton/vLLM)."
})

# Ex 40
code40 = r'''package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

type TokenBucketLimiter struct {
	mu           sync.Mutex
	capacity     float64
	tokens       float64
	refillRate   float64 // токенов в секунду
	lastRefilled time.Time
}

func NewTokenBucketLimiter(capacity, refillRatePerSec float64) *TokenBucketLimiter {
	return &TokenBucketLimiter{
		capacity:     capacity,
		tokens:       capacity,
		refillRate:   refillRatePerSec,
		lastRefilled: time.Now(),
	}
}

func (l *TokenBucketLimiter) Allow(requestedTokens float64) bool {
	l.mu.Lock()
	defer l.mu.Unlock()

	now := time.Now()
	elapsed := now.Sub(l.lastRefilled).Seconds()
	l.lastRefilled = now

	// Пополнение корзины
	l.tokens += elapsed * l.refillRate
	if l.tokens > l.capacity {
		l.tokens = l.capacity
	}

	if l.tokens >= requestedTokens {
		l.tokens -= requestedTokens
		return true
	}

	return false
}

func main() {
	// Лимит: емкость 1000 токенов, пополнение 500 токенов/сек
	limiter := NewTokenBucketLimiter(1000, 500)

	call1 := limiter.Allow(600)
	call2 := limiter.Allow(500) // превысит доступный остаток

	fmt.Printf("Запрос 1 (600 токенов): разрешен = %t\n", call1)
	fmt.Printf("Запрос 2 (500 токенов): разрешен = %t (ожидается false)\n", call2)
}
'''
validate_go_code(code40, "Ex 40")
exercises.append({
    "num": 40,
    "title": "Rate Limiting и управление бюджетом токенов (Token Bucket Per Model)",
    "task": "Реализуйте алгоритм ограничения скорости и расхода токенов Token Bucket Rate Limiter на Go: учет лимитов TPM (Tokens Per Minute) и RPM (Requests Per Minute) с защитой от непредвиденных перерасходов квот.",
    "theory": """API провайдеры накладывают строгие квоты двух типов:
1. **RPM (Requests Per Minute)**: Ограничение на количество HTTP-запросов.
2. **TPM (Tokens Per Minute)**: Ограничение на суммарный объем токенов (входных + выходных).
Если корпоративный шлюз превышает TPM, провайдер возвращает ошибку 429 Too Many Requests, обрывая пользовательские сессии.
Алгоритм **Token Bucket (Корзина токенов)**:
- Корзина имеет максимальную емкость `capacity`.
- Непрерывно пополняется с постоянной скоростью `refillRate` (токенов в секунду).
- При поступлении запроса на $N$ токенов проверяется наличие токенов в корзине. При успехе токены списываются, иначе запрос ставится в очередь ожидания или отклоняется.""",
    "step_by_step": [
        "Определите структуру `TokenBucketLimiter` с полями `capacity`, `tokens`, `refillRate` и мьютексом.",
        "Реализуйте ленивое пополнение токенов на основе `elapsed = now.Sub(lastRefilled).Seconds()`.",
        "Реализуйте проверку `Allow(requestedTokens)` со списанием токенов.",
        "Продемонстрируйте блокировку запроса при превышении лимита."
    ],
    "code_blocks": [code40],
    "under_the_hood": "Ленивое пополнение корзины (Lazy Refill) вычисляет баланс только в момент входящего вызова по формуле дельты времени, исключая необходимость фоновых тикеров `time.Ticker` и сохраняя ресурсы процессора в моменты простоя.",
    "pitfalls": "Ограничение только по RPM без учета TPM не защитит от блокировки: один запрос с промптом на 30 000 токенов мгновенно исчерпает минутный бюджет провайдера.",
    "bigtech_interview": "Как распределенный Token Bucket реализуется в кластере из 50 подов Go шлюза?\nОтвет: С помощью Redis и скрипта на Lua. Скрипт атомарно выполняет считывание текущего баланса, расчет `elapsed`, пополнение и списание токенов по ключу `ratelimit:{tenant_id}:{model}` за один сетевой round-trip (RTT < 1 мс), исключая гонки данных между репликами приложения."
})

# Ex 41
code41 = r'''package main

import (
	"fmt"
	"regexp"
	"strings"
)

type GuardrailResult struct {
	IsSafe    bool
	Violations []string
}

type SafetyGuardrail struct {
	piiEmailRegex *regexp.Regexp
	piiPhoneRegex *regexp.Regexp
	toxicKeywords []string
}

func NewSafetyGuardrail() *SafetyGuardrail {
	return &SafetyGuardrail{
		piiEmailRegex: regexp.MustCompile(`[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`),
		piiPhoneRegex: regexp.MustCompile(`\+?[0-9]{10,13}`),
		toxicKeywords: []string{"ненавижу", "уничтожить", "взломать"},
	}
}

func (g *SafetyGuardrail) InspectText(text string) GuardrailResult {
	var violations []string

	if g.piiEmailRegex.MatchString(text) {
		violations = append(violations, "PII: Обнаружен персональный email адрес")
	}
	if g.piiPhoneRegex.MatchString(text) {
		violations = append(violations, "PII: Обнаружен номер телефона")
	}

	lower := strings.ToLower(text)
	for _, kw := range g.toxicKeywords {
		if strings.Contains(lower, kw) {
			violations = append(violations, fmt.Sprintf("TOXICITY: Обнаружено запрещенное слово '%s'", kw))
		}
	}

	return GuardrailResult{
		IsSafe:     len(violations) == 0,
		Violations: violations,
	}
}

func main() {
	guard := NewSafetyGuardrail()
	badText := "Мой телефон +79991234567, хочу взломать сервер."
	res := guard.InspectText(badText)

	fmt.Printf("Результат проверки Guardrails: Безопасно = %t\n", res.IsSafe)
	for _, v := range res.Violations {
		fmt.Printf("- %s\n", v)
	}
}
'''
validate_go_code(code41, "Ex 41")
exercises.append({
    "num": 41,
    "title": "Анализ сентимента и детекция токсичности в режиме реального времени",
    "task": "Разработайте шлюз безопасности (Input/Output Guardrails) на Go: автоматическая детекция утечки персональных данных (PII: телефоны, email) и фильтрация недопустимого контента перед отправкой в модель и перед показом пользователю.",
    "theory": """**Guardrails (Защитные барьеры)** — обязательный компонент корпоративных LLM приложений.
Шлюз проверяет потоки данных на двух рубежах:
1. **Input Guardrails (Входящий контроль)**:
   - Проверка пользовательского ввода на PII (Personally Identifiable Information). Если пользователь случайно вставил паспортные данные или номер кредитной карты, шлюз маскирует их звёздочками `[REDACTED]`.
   - Защита от Jailbreak и токсичности.
2. **Output Guardrails (Исходящий контроль)**:
   - Проверка ответа модели на соответствие нормам корпоративной этики, отсутствие клеветы и утечки коммерческой тайны.
Выполнение проверок на Go занимает доли миллисекунды, гарантируя безопасность без ощутимого увеличения задержки.""",
    "step_by_step": [
        "Скомпилируйте регулярные выражения для поиска персональных данных.",
        "Реализуйте метод `InspectText` с возвратом списка зафиксированных нарушений `GuardrailResult`.",
        "Добавьте правила проверки на запрещенные ключевые слова.",
        "Протестируйте детекцию на примере подозрительного сообщения."
    ],
    "code_blocks": [code41],
    "under_the_hood": "Регулярные выражения в Go (`regexp`) работают на базе безопасного конечного автомата Резерфорда (linear time complexity $O(N)$), гарантируя полную неуязвимость к атакам ReDoS (Regular Expression Denial of Service).",
    "pitfalls": "Маскирование данных регулярками не гарантирует 100% очистки нестандартно записанных данных. В критических контурах поверх регулярок применяют специализированные легковесные NER-модели (Named Entity Recognition).",
    "bigtech_interview": "Что такое ReDoS и почему стандартный пакет regexp в Go к нему неуязвим?\nОтвет: ReDoS (Regular Expression Denial of Service) — атака, при которой специально подобранная строка вызывает экспоненциальный бэктрекинг в движках регулярных выражений на базе NFA (как в Python, Java, JS), подвешивая CPU на 100%. Пакет regexp в Go использует алгоритм RE2/Thompson NFA, который принципиально не использует бэктрекинг и гарантирует время выполнения, строго линейное от длины строки $O(N)$."
})

# Ex 42
code42 = r'''package main

import "fmt"

const ShardedTableDDL = `
-- Партиционирование таблицы векторов по диапазону или хэшу организации (Multi-Tenancy)
CREATE TABLE IF NOT EXISTS tenant_embeddings (
    tenant_id VARCHAR(64) NOT NULL,
    id UUID NOT NULL,
    embedding vector(1536) NOT NULL,
    PRIMARY KEY (tenant_id, id)
) PARTITION BY HASH (tenant_id);

-- Создание 4 независимых партиций
CREATE TABLE tenant_embeddings_p0 PARTITION OF tenant_embeddings FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE tenant_embeddings_p1 PARTITION OF tenant_embeddings FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE tenant_embeddings_p2 PARTITION OF tenant_embeddings FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE tenant_embeddings_p3 PARTITION OF tenant_embeddings FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Индекс HNSW строится локально внутри каждой партиции, что сокращает размер графа и ускоряет поиск
CREATE INDEX idx_p0_hnsw ON tenant_embeddings_p0 USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
`

func main() {
	fmt.Println("Схема партиционирования pgvector для HighLoad баз данных успешно спроектирована.")
	fmt.Printf("Размер DDL схемы: %d байт\n", len(ShardedTableDDL))
}
'''
validate_go_code(code42, "Ex 42")
exercises.append({
    "num": 42,
    "title": "Векторное шардирование pgvector с HNSW и IVFFlat",
    "task": "Спроектируйте архитектуру шардирования и партиционирования векторных таблиц в PostgreSQL pgvector: декларативное секционирование PARTITION BY HASH(tenant_id) и построение локальных HNSW индексов для изоляции данных арендаторов и масштабирования свыше 10 миллионов векторов.",
    "theory": """При росте объема векторной базы свыше 1 000 000 записей единый монолитный граф HNSW перестает помещаться в `shared_buffers` оперативной памяти:
1. Чтение узлов графа начинает вызывать случайный дисковый ввод-вывод (Random Disk I/O), вызывая деградацию латентности с 2 мс до 150 мс.
2. Блокировки при вставке новых узлов вызывают конкуренцию между пишущими транзакциями.
**Партиционирование (Partitioning / Sharding)** решает проблему:
- Таблица секционируется по идентификатору клиента `tenant_id` (`PARTITION BY HASH`).
- Каждая секция имеет собственный независимый граф HNSW.
- При запросе с условием `WHERE tenant_id = 'org_42'` планировщик PostgreSQL выполняет **Partition Pruning**, сканируя только одну компактную секцию, которая целиком помещается в RAM.""",
    "step_by_step": [
        "Спроектируйте DDL мастер-таблицы с `PARTITION BY HASH (tenant_id)`.",
        "Создайте партиции с распределением по остатку от деления `(MODULUS 4, REMAINDER X)`.",
        "Постройте локальные индексы HNSW на каждой секции.",
        "Убедитесь в изоляции данных."
    ],
    "code_blocks": [code42],
    "under_the_hood": "Partition Pruning в планировщике PostgreSQL исключает ненужные партиции на этапе построения плана выполнения запроса. Это снижает объем используемой оперативной памяти ровно в $N$ раз (где $N$ — количество секций).",
    "pitfalls": "Запрос без указания `tenant_id` приведет к параллельному сканированию всех партиций, что нивелирует преимущества партиционирования.",
    "bigtech_interview": "В чем разница между шардированием векторов в PostgreSQL через Citus/pg_partman и специализированными векторными кластерами (Qdrant/Milvus)?\nОтвет: PostgreSQL с Citus позволяет сохранить ACID-транзакции, реляционные JOIN'ы и привычный SQL в распределенном кластере. Специализированные векторные кластеры (Qdrant) обеспечивают более высокую плотность упаковки векторов на гигабайт RAM за счет скалярного квантования векторов (SQ8/PQ), но требуют поддержки отдельной распределенной инфраструктуры."
})

# Ex 43
code43 = r'''package main

import (
	"encoding/json"
	"fmt"
)

type EvaluationResult struct {
	AccuracyScore int    `json:"accuracy_score"` // 1 - 5
	ToneScore     int    `json:"tone_score"`     // 1 - 5
	Reasoning     string `json:"reasoning"`
	Passed        bool   `json:"passed"`
}

func ParseJudgeVerdict(rawJSON string) (EvaluationResult, error) {
	var res EvaluationResult
	if err := json.Unmarshal([]byte(rawJSON), &res); err != nil {
		return EvaluationResult{}, err
	}
	res.Passed = res.AccuracyScore >= 4 && res.ToneScore >= 4
	return res, nil
}

func main() {
	sampleJudgeOutput := `{
		"accuracy_score": 5,
		"tone_score": 5,
		"reasoning": "Ответ полностью точен, приведен рабочий код на Go с корректной обработкой ошибок.",
		"passed": true
	}`

	verdict, err := ParseJudgeVerdict(sampleJudgeOutput)
	fmt.Printf("Вердикт LLM-as-a-Judge в CI/CD: err=%v, Тест пройден=%t, Оценка точности: %d/5\n",
		err, verdict.Passed, verdict.AccuracyScore)
}
'''
validate_go_code(code43, "Ex 43")
exercises.append({
    "num": 43,
    "title": "Оценка качества генерации с LLM-as-a-Judge в CI/CD",
    "task": "Разработайте пайплайн автоматизированного регрессионного тестирования промптов в CI/CD: эталонная модель (LLM-as-a-Judge) оценивает сгенерированные ответы новой версии приложения по критериям точности и тональности с автоматическим прерыванием билда при падении метрик.",
    "theory": """Как гарантировать, что изменение системного промпта не ухудшило качество ответов ассистента?
Юнит-тесты на точное совпадение строк бессильны: LLM формулирует мысли каждый раз с вариациями слов.
Паттерн **LLM-as-a-Judge**:
1. Формируется тестовый датасет эталонных вопросов и ответов (Ground Truth Dataset).
2. Новая версия сервиса генерирует ответы.
3. Модель-судья более высокого класса (например, GPT-4o) получает промпт: *«Оцени качество ответа кандидата по сравнению с эталоном по шкале от 1 до 5»*.
4. Ответ судьи десериализуется в структуру `EvaluationResult`.
5. Если средний балл регрессирует ниже порога (например, < 4.5), CI/CD пайплайн падает с ошибкой.""",
    "step_by_step": [
        "Определите контрактную структуру вердикта судьи `EvaluationResult`.",
        "Напишите функцию валидации `ParseJudgeVerdict`.",
        "Задайте пороговые критерии прохождения регрессионного теста.",
        "Продемонстрируйте вердикт в консоли."
    ],
    "code_blocks": [code43],
    "under_the_hood": "В CI/CD автоматизации тесты запускаются параллельно в пуле горутин с ограничением параллелизма через семафор `chan struct{}`, прогоняя сотни тест-кейсов за 10–20 секунд.",
    "pitfalls": "Судья-модель подвержена эффекту 'Position Bias' (предпочтение первому показанному варианту) и 'Verbosity Bias' (завышение оценки более длинным ответам). Для компенсации промпт судьи требует четких критериев оценки без субъективных формулировок.",
    "bigtech_interview": "Как автоматизировать запуск LLM-as-a-Judge в GitHub Actions или GitLab CI без риска утечки секретов?\nОтвет: Через защищенные переменные окружения (CI Secrets / Vault), вызов Go-тест раннера `go test -v -tags=integration ./e2e/...` и генерацию стандартного отчета в формате JUnit XML (`gotestsum`), который отображает статусы прохождения тестов прямо в интерфейсе Pull Request."
})

# Ex 44
code44 = r'''package main

import (
	"fmt"
	"sync"
)

type DynamicSemanticCache struct {
	mu           sync.RWMutex
	strictRoutes map[string]float32 // адаптивные пороги для разных типов запросов
}

func NewDynamicSemanticCache() *DynamicSemanticCache {
	return &DynamicSemanticCache{
		strictRoutes: map[string]float32{
			"financial": 0.98, // Жесткий порог для финансовых расчетов
			"general":   0.90, // Мягкий порог для общих справочных вопросов
		},
	}
}

func (c *DynamicSemanticCache) GetThreshold(category string) float32 {
	c.mu.RLock()
	defer c.mu.RUnlock()
	if val, ok := c.strictRoutes[category]; ok {
		return val
	}
	return 0.95 // Дефолтный безопасный порог
}

func main() {
	cache := NewDynamicSemanticCache()
	fmt.Printf("Динамический порог схожести: Финансы = %.2f, Общие вопросы = %.2f\n",
		cache.GetThreshold("financial"), cache.GetThreshold("general"))
}
'''
validate_go_code(code44, "Ex 44")
exercises.append({
    "num": 44,
    "title": "Семантическое кэширование с динамическим порогом схожести",
    "task": "Оптимизируйте векторный кэш запросов: внедрите адаптивный динамический порог косинусного сходства в зависимости от категории запроса (0.98 для критических финансовых данных и 0.90 для общих справочных вопросов).",
    "theory": """Фиксированный порог сходства в семантическом кэше — источник проблем:
- Если установить жесткий порог `0.98`, процент попаданий (Cache Hit Ratio) на общих вопросах упадет до 2%, лишая кэш смысла.
- Если установить мягкий порог `0.90`, в финансовых или медицинских вопросах кэш выдаст ответ на другой вопрос, что чревато катастрофическими последствиями.
**Динамическое адаптивное кэширование (Dynamic Thresholding)**:
- Классификатор запроса определяет степень критичности темы.
- Для критических операций (расчет процентов, баланс, регламенты безопасности) порог повышается до `0.98`.
- Для свободных диалогов, приветствий и общих определений порог снижается до `0.90–0.92`, максимизируя экономию токенов.""",
    "step_by_step": [
        "Определите структуру `DynamicSemanticCache` с мапой категориальных порогов.",
        "Реализуйте метод `GetThreshold` с защитой через `sync.RWMutex`.",
        "Предусмотрите безопасный дефолтный порог на случай неизвестной категории.",
        "Проверьте работу в консоли."
    ],
    "code_blocks": [code44],
    "under_the_hood": "Конфигурация порогов может динамически обновляться через etcd или Consul без перезапуска сервиса, позволяя инженерам тюнить Cache Hit Ratio на лету.",
    "pitfalls": "Установка порога ниже 0.88 недопустима для любых типов семантического кэша, так как на этом уровне начинаются грубые смысловые подмены ответов.",
    "bigtech_interview": "Как рассчитать финансовую эффективность внедрения семантического кэша?\nОтвет: Через метрику Saved Cost: `(Количество Cache Hits * Средняя стоимость вызова LLM) - Стоимость вычислений эмбеддингов и хранения в Redis`. При 1 000 000 запросов в сутки и Hit Ratio 30% экономия может составлять десятки тысяч долларов в месяц."
})

# Ex 45
code45 = r'''package main

import (
	"context"
	"fmt"
	"time"
)

type AutonomousIncidentAgent struct {
	serviceName string
}

func NewAutonomousIncidentAgent(serviceName string) *AutonomousIncidentAgent {
	return &AutonomousIncidentAgent{serviceName: serviceName}
}

// InvestigateIncident выполняет полный автономный цикл расследования инцидента
func (a *AutonomousIncidentAgent) InvestigateIncident(ctx context.Context, alertName string) string {
	// 1. Опрос телеметрии Prometheus через Function Calling
	time.Sleep(10 * time.Millisecond)
	metricObservation := "HTTP 500 error rate = 14.5% на подах платежного шлюза"

	// 2. Анализ логов в Loki
	time.Sleep(10 * time.Millisecond)
	logObservation := "connection timeout to postgresql-primary:5432"

	// 3. Формирование RCA отчета
	report := fmt.Sprintf(`=== ОТЧЕТ РАССЛЕДОВАНИЯ АВАРИИ [%s] ===
Время инцидента: %s
Сервис: %s
Первопричина (Root Cause): Недоступность пула соединений PostgreSQL (connection timeout).
Рекомендованное действие: Перезапуск PgBouncer и проверка сетевой связности между нодами.
Метрики: %s | Логи: %s`, alertName, time.Now().Format(time.RFC3339), a.serviceName, metricObservation, logObservation)

	return report
}

func main() {
	agent := NewAutonomousIncidentAgent("payment-service")
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	report := agent.InvestigateIncident(ctx, "HighErrorRatePaymentGateway")
	fmt.Println(report)
}
'''
validate_go_code(code45, "Ex 45")
exercises.append({
    "num": 45,
    "title": "Production-Ready ИИ-Агент для автоматизации инженерных инцидентов",
    "task": "Объедините все изученные технологии в законченный автономный микросервис расследования инженерных инцидентов (Autonomous Incident Responder): перехват алертов Alertmanager, опрос Prometheus и Loki через инструменты, локализация первопричины (RCA) и формирование отчета.",
    "theory": """Финальный синтез технологий главы 99:
**Автономный агент дежурного инженера (SRE AI Agent)**:
1. Получает Webhook от Prometheus Alertmanager о деградации сервиса.
2. В цикле ReAct инициирует серию Function Calls:
   - Запрашивает графики задержек и ошибок в Prometheus.
   - Запрашивает стек-трейсы ошибок в Loki.
   - Ищет в векторной базе документации (pgvector) аналогичные инциденты и инструкции по устранению (Runbooks).
3. Формирует структурированный отчет о первопричине аварии (Root Cause Analysis).
4. Публикует отчет в инженерный чат дежурной смены, сокращая время локализации аварии (MTTR) с 40 минут до 30 секунд.""",
    "step_by_step": [
        "Определите структуру `AutonomousIncidentAgent`.",
        "Реализуйте метод `InvestigateIncident` с опросом систем мониторинга.",
        "Сформируйте структурированный RCA-отчет.",
        "Продемонстрируйте завершение расследования аварии."
    ],
    "code_blocks": [code45],
    "under_the_hood": "Такой агент дежурит в Kubernetes в виде отдельного DaemonSet или Deployment, потребляя менее 30 МБ памяти в режиме ожидания благодаря нулевому оверхеду рантайма Go.",
    "pitfalls": "Предоставление агенту прав на автоматическое применение разрушительных исправлений (`kubectl delete pod`, `DROP TABLE`) без явного подтверждения человеком (Human-in-the-Loop) несет колоссальные риски.",
    "bigtech_interview": "Как организовать безопасный паттерн Human-in-the-Loop для ИИ-агентов, управляющих инфраструктурой?\nОтвет: Разделением действий на Read-Only (сбор метрик, поиск логов, анализ — агент выполняет автономно) и Mutating Actions (перезапуск подов, смена конфигурации). Для мутирующих действий агент генерирует интерактивное сообщение с кнопками подтверждения в Slack/Telegram, и реальное исполнение команды происходит только после нажатия кнопки авторизованным дежурным инженером."
})

with open('/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch99_p3.json', 'w', encoding='utf-8') as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Chapter 99 Part 3 generated: {len(exercises)} exercises.")
