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
	"context"
	"fmt"
	"net/http"
	"runtime"
	"sync/atomic"
	"time"
)

// AIGatewayStats аккумулирует метрики высокой конкурентности шлюза
type AIGatewayStats struct {
	ActiveStreams atomic.Int64
	TotalRequests atomic.Int64
}

var stats AIGatewayStats

// FastGatewayHandler демонстрирует преимущество Go: обработка тысяч конкурентных SSE-стримов
// с минимальным потреблением памяти (стек горутины всего 2 КБ против 1-8 МБ потока ОС в Python/C++)
func FastGatewayHandler(w http.ResponseWriter, r *http.Request) {
	stats.ActiveStreams.Add(1)
	stats.TotalRequests.Add(1)
	defer stats.ActiveStreams.Add(-1)

	// Настройка HTTP/2 Server-Sent Events заголовков
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("X-Accel-Buffering", "no")

	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming unsupported", http.StatusInternalServerError)
		return
	}

	ctx := r.Context()
	ticker := time.NewTicker(20 * time.Millisecond)
	defer ticker.Stop()

	tokens := []string{"Go", " идеально", " подходит", " для", " LLM", " шлюзов", " благодаря", " GMP", " планировщику."}
	for i, token := range tokens {
		select {
		case <-ctx.Done():
			// Клиент отключился — немедленный возврат горутины без утечек памяти
			return
		case <-ticker.C:
			fmt.Fprintf(w, "data: {\"index\": %d, \"token\": %q}\n\n", i, token)
			flusher.Flush()
		}
	}
	fmt.Fprintf(w, "data: [DONE]\n\n")
	flusher.Flush()
}

func main() {
	var mem runtime.MemStats
	runtime.ReadMemStats(&mem)
	fmt.Printf("Инициализация Go LLM Gateway. Выделено памяти: %d КБ, Горутин: %d\n",
		mem.Alloc/1024, runtime.NumGoroutine())
}
'''
validate_go_code(code1, "Ex 1")
exercises.append({
    "num": 1,
    "title": "Экосистема ИИ и LLM-инженерии на Go",
    "task": "Изучите ключевые преимущества Go в инфраструктуре ИИ и LLM: мультиплексирование тысяч SSE-потоков, эффективную работу сокетов через Netpoller, минимальный footprint памяти на соединение (2 КБ стек горутины) и создание высокопроизводительных API-шлюзов перед Python-серверами инференса (vLLM, Ollama, Triton, TGI).",
    "theory": """В современной экосистеме генеративного ИИ вычисления нейросетей (матричные перемножения FP16/BF16/FP8, KV-кэш на GPU) традиционно ведутся на C++/CUDA и фреймворках вроде vLLM, TensorRT-LLM или Triton Inference Server с Python-обертками. Однако организация внешнего контура — **AI Gateway, RAG Pipeline, Ingestion, Vector Search Orchestration, Token Rate Limiting и Connection Multiplexing** — предъявляет жесткие требования к системному вводу-выводу:
1. **Server-Sent Events (SSE) Concurrency**: Модель генерирует ответ по токенам со скоростью 30–100 токенов/сек, удерживая открытое HTTP-соединение на протяжении 5–30 секунд. В классических Python WSGI/ASGI серверах (Uvicorn, Gunicorn) 10 000 параллельных SSE-сессий вызывают взрывное потребление RAM и деградацию event loop из-за GIL.
2. **Низкий оверхед памяти в Go**: Начальный стек горутины составляет всего 2 КБ (расширяясь динамически). 50 000 параллельных активных стримов в Go требуют лишь ~100 МБ памяти, а epoll/kqueue Netpoller рантайма исключает блокировку системных тредов.
3. **Строгая типизация контрактов и бинарная дистрибьюция**: Go компилируется в единый статический бинарник без проблем с виртуальными окружениями Python, CUDA версиями и зависимостями, обеспечивая субмиллисекундный холодный старт контейнеров.""",
    "step_by_step": [
        "Настройте HTTP-хендлер со стримингом токенов text/event-stream и валидацией интерфейса http.Flusher.",
        "Используйте atomic.Int64 для потокобезопасного учета метрик активных стримов без блокировок мьютексом.",
        "Реализуйте обработку ctx.Done() для немедленного освобождения ресурсов при преждевременном разрыве связи клиентом.",
        "Изучите статистику потребления памяти через runtime.ReadMemStats."
    ],
    "code_blocks": [code1],
    "under_the_hood": "Планировщик Go GMP паркует горутины, ожидающие сетевых ответов от инференс-бэкенда (vLLM/Ollama), в системный epoll (Netpoller) без удержания OS-треда (M). Когда очередной токен приходит в сокет, netpoller пробуждает горутину (G) и помещает её в локальную очередь запуска (runq) процессора (P). Это снижает переключение контекста до субмикросекундных величин.",
    "pitfalls": "Отсутствие проверки интерфейса http.Flusher при использовании HTTP-прокси или кастомных ResponseWriter-оберток приводит к панике или полной буферизации ответа, превращая потоковую передачу токенов в пакетную (chunked batching).",
    "bigtech_interview": "В чем архитектурное преимущество разделения инференса на Python/C++ и оркестрации на Go в HighLoad AI сервисах?\nОтвет: Инференс требует прямого доступа к CUDA/GPU ядрам и динамическим тензорам (PyTorch/vLLM), где доминирует compute-bound нагрузка. Оркестрация, RAG, валидация JSON Schema, авторизация и удержание десятков тысяч SSE-сокетов — чисто I/O-bound задача. Go обеспечивает идеальную пропускную способность ввода-вывода с минимальным расходом памяти и CPU, выступая надежным барьером перед дорогими GPU-нодами."
})

# Ex 2
code2 = r'''package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type ChatMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type ChatCompletionRequest struct {
	Model       string        `json:"model"`
	Messages    []ChatMessage `json:"messages"`
	Temperature float64       `json:"temperature,omitempty"`
	Stream      bool          `json:"stream"`
}

type ChatChoice struct {
	Index        int         `json:"index"`
	Message      ChatMessage `json:"message"`
	FinishReason string      `json:"finish_reason"`
}

type ChatUsage struct {
	PromptTokens     int `json:"prompt_tokens"`
	CompletionTokens int `json:"completion_tokens"`
	TotalTokens      int `json:"total_tokens"`
}

type ChatCompletionResponse struct {
	ID      string       `json:"id"`
	Object  string       `json:"object"`
	Created int64        `json:"created"`
	Model   string       `json:"model"`
	Choices []ChatChoice `json:"choices"`
	Usage   ChatUsage    `json:"usage"`
}

type LLMClient struct {
	baseURL    string
	apiKey     string
	httpClient *http.Client
}

func NewLLMClient(baseURL, apiKey string) *LLMClient {
	return &LLMClient{
		baseURL: baseURL,
		apiKey:  apiKey,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
			Transport: &http.Transport{
				MaxIdleConns:        100,
				MaxIdleConnsPerHost: 20,
				IdleConnTimeout:     90 * time.Second,
			},
		},
	}
}

func (c *LLMClient) CreateChatCompletion(ctx context.Context, req ChatCompletionRequest) (*ChatCompletionResponse, error) {
	req.Stream = false
	payload, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/v1/chat/completions", bytes.NewReader(payload))
	if err != nil {
		return nil, fmt.Errorf("create http request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	if c.apiKey != "" {
		httpReq.Header.Set("Authorization", "Bearer "+c.apiKey)
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("execute http call: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 4096))
		return nil, fmt.Errorf("llm api error: status %d, body: %s", resp.StatusCode, string(body))
	}

	var chatResp ChatCompletionResponse
	if err := json.NewDecoder(resp.Body).Decode(&chatResp); err != nil {
		return nil, fmt.Errorf("decode json response: %w", err)
	}

	return &chatResp, nil
}

func main() {
	client := NewLLMClient("http://localhost:11434", "")
	fmt.Printf("LLM Client инициализирован с базовым URL: %s, таймаут: 60с\n", client.baseURL)
}
'''
validate_go_code(code2, "Ex 2")
exercises.append({
    "num": 2,
    "title": "Взаимодействие с LLM API на чистом Go без сторонних SDK",
    "task": "Напишите надежный, production-grade клиент к OpenAI-совместимым API (vLLM, Ollama, OpenAI) на чистом Go с использованием стандартной библиотеки net/http, поддержкой пула Keep-Alive соединений, context таймаутов и строгой типизацией ChatCompletionRequest/Response.",
    "theory": """Многие разработчики начинают работу с LLM через громоздкие неофициальные SDK, которые часто устаревают при выходе новых версий API провайдеров. В Go создание клиента на базе `net/http` требует всего 80 строк кода и дает 100% контроль над жизненным циклом сокетов, заголовками авторизации и пулом соединений (`http.Transport`).
OpenAI-совместимый эндпоинт `/v1/chat/completions` является де-факто стандартом индустрии. Он поддерживается OpenAI, Ollama, vLLM, DeepSeek, Anthropic (через прокси), Mistral и LocalAI.
Основные элементы контракта:
- Роли сообщений (`system`, `user`, `assistant`, `tool`).
- Параметры стохастичности: `temperature` (0.0 — детерминированный ответ, 1.0+ — креативный), `top_p`.
- Метрики расхода токенов: `prompt_tokens`, `completion_tokens`, `total_tokens`.""",
    "step_by_step": [
        "Определите структуры `ChatMessage`, `ChatCompletionRequest`, `ChatChoice`, `ChatUsage` и `ChatCompletionResponse` с JSON-тегами.",
        "Настройте кастомный `http.Client` с пулом постоянных TCP-соединений (`MaxIdleConnsPerHost = 20`) во избежание TIME_WAIT истощения сокетов.",
        "Реализуйте метод `CreateChatCompletion` с использованием `http.NewRequestWithContext`.",
        "При ошибках HTTP считывайте ограниченное количество байт через `io.LimitReader(resp.Body, 4096)` для предотвращения DoS-атак переполнения памяти ответом сервера."
    ],
    "code_blocks": [code2],
    "under_the_hood": "Использование `io.LimitReader` при обработке ошибочных ответов гарантирует, что если некорректно настроенный API-сервер отдаст HTML-страницу ошибки в сотни мегабайт, горутина Go не вызовет OOM-панику аллокатора кучи (mheap). Пул `http.Transport` сохраняет открытые TCP-хэндлы с TLS-сессиями, устраняя задержку 3-way handshake + TLS 1.3 handshake (30-80 мс) на каждый вызов модели.",
    "pitfalls": "Забытый `defer resp.Body.Close()` приводит к утечке файловых дескрипторов и невозможности повторного использования TCP-сокета из пула `http.Transport`.",
    "bigtech_interview": "Почему в продакшене нельзя использовать стандартный http.DefaultClient для запросов к LLM?\nОтвет: http.DefaultClient не имеет сконфигурированного таймаута (Timeout = 0). В случае подвисания инференс-сервера или сетевого сбоя горутина зависнет навечно, что при высокой нагрузке приведет к лавинообразному исчерпанию лимита горутин и падению всего сервиса."
})

# Ex 3
code3 = r'''package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"strings"
)

type StreamDelta struct {
	Role    string `json:"role,omitempty"`
	Content string `json:"content,omitempty"`
}

type StreamChoice struct {
	Index        int         `json:"index"`
	Delta        StreamDelta `json:"delta"`
	FinishReason *string     `json:"finish_reason"`
}

type StreamChunkResponse struct {
	ID      string         `json:"id"`
	Choices []StreamChoice `json:"choices"`
}

type StreamCallback func(token string) error

func StreamChatCompletion(ctx context.Context, client *http.Client, url, apiKey string, reqPayload []byte, onToken StreamCallback) error {
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, url+"/v1/chat/completions", bytes.NewReader(reqPayload))
	if err != nil {
		return fmt.Errorf("create stream req: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Accept", "text/event-stream")
	if apiKey != "" {
		httpReq.Header.Set("Authorization", "Bearer "+apiKey)
	}

	resp, err := client.Do(httpReq)
	if err != nil {
		return fmt.Errorf("do stream req: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
		return fmt.Errorf("stream failed with status %d: %s", resp.StatusCode, string(body))
	}

	reader := bufio.NewReader(resp.Body)
	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			if errors.Is(err, io.EOF) {
				break
			}
			return fmt.Errorf("read sse line: %w", err)
		}

		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, ":") {
			// Пустая строка или SSE keep-alive комментарий
			continue
		}

		if !strings.HasPrefix(line, "data: ") {
			continue
		}

		data := strings.TrimPrefix(line, "data: ")
		if data == "[DONE]" {
			// Маркер завершения генерации в спецификации OpenAI
			break
		}

		var chunk StreamChunkResponse
		if err := json.Unmarshal([]byte(data), &chunk); err != nil {
			// Пропускаем некорректные или служебные фреймы
			continue
		}

		for _, choice := range chunk.Choices {
			if choice.Delta.Content != "" {
				if err := onToken(choice.Delta.Content); err != nil {
					return fmt.Errorf("onToken callback error: %w", err)
				}
			}
		}
	}

	return nil
}

func main() {
	fmt.Println("Парсер Server-Sent Events (SSE) для LLM стриминга скомпилирован успешно.")
}
'''
validate_go_code(code3, "Ex 3")
exercises.append({
    "num": 3,
    "title": "Потоковый вывод токенов (Server-Sent Events Streaming)",
    "task": "Реализуйте потоковый парсер Server-Sent Events (SSE) на чистом Go для обработки параметра 'stream': true. Парсер должен построчно считывать поток данных через bufio.Reader, корректно обрабатывать префиксы 'data: ', игнорировать keep-alive комментарии, распознавать маркер завершения '[DONE]' и вызывать коллбек передачи токена.",
    "theory": """Генерация ответов современными LLM занимает от нескольких секунд до десятков секунд. Заставлять пользователя ожидать завершения всей генерации ухудшает Time to Value (пользовательский опыт). Потоковая передача (Streaming) на базе спецификации **W3C Server-Sent Events (SSE)** передает токены по мере их декодирования видеокартой.
Формат SSE протокола:
- Передача ведется через текстовый поток с заголовком `Content-Type: text/event-stream`.
- Каждое полезное сообщение начинается с префикса `data: ` и завершается двумя переводами строк `\\n\\n`.
- Служебные сообщения keep-alive начинаются с двоеточия `: ping`.
- Спецификация OpenAI завершает поток специальным служебным фреймом `data: [DONE]`.
Построчное чтение с помощью `bufio.Reader.ReadString('\\n')` предотвращает аллокацию гигантских буферов в памяти, обрабатывая поток токенов в режиме O(1) памяти.""",
    "step_by_step": [
        "Сформируйте HTTP-запрос с заголовком `Accept: text/event-stream` и телом, содержащим `\"stream\": true`.",
        "Инициализируйте буферизованный ридер `bufio.NewReader(resp.Body)`.",
        "В цикле считывайте строки до символа `\\n`, удаляя концевые пробелы и переносы.",
        "Фильтруйте строки, игнорируя пустые строки и комментарии, начинающиеся с `:`.",
        "При обнаружении `[DONE]` корректно завершайте цикл чтения.",
        "Десериализуйте `chunk.Choices[].Delta.Content` и передавайте в коллбек `onToken`."
    ],
    "code_blocks": [code3],
    "under_the_hood": "`bufio.Reader` использует внутренний буфер фиксированного размера (по умолчанию 4096 байт). При чтении строки он сдвигает указатели внутри буфера и лишь при необходимости делает следующий системный вызов `read(2)`. Это минимизирует количество контекстных переключений между пространством пользователя и ядром ОС при получении каждого отдельного токена.",
    "pitfalls": "Использование `bufio.Scanner` вместо `bufio.Reader` опасно: при генерации очень длинной непрерывной строки без переноса `bufio.Scanner` вернет ошибку `bufio.Scanner: token too long` при превышении буфера по умолчанию (64 КБ). `bufio.Reader.ReadString` не имеет такого ограничения.",
    "bigtech_interview": "Что произойдет, если в стриминговом обработчике SSE не сбрасывать буфер через flusher.Flush()?\nОтвет: Пакеты данных будут накапливаться во внутреннем буфере сокета или промежуточных прокси (Nginx, Envoy) до тех пор, пока буфер не заполнится (обычно 4-16 КБ), либо пока соединение не закроется. В результате пользователь увидит задержку в несколько секунд, после чего весь текст отобразится одновременно, что полностью нивелирует смысл стриминга."
})

# Ex 4
code4 = r'''package main

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"time"
)

// LLMServerMock имитирует медленный инференс языковой модели
func LLMServerMock(aborted *atomic.Bool) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/event-stream")
		flusher, _ := w.(http.Flusher)

		notify := r.Context().Done()
		for i := 0; i < 50; i++ {
			select {
			case <-notify:
				// Сервер инференса зафиксировал разрыв TCP сокета со стороны Go-клиента
				aborted.Store(true)
				return
			case <-time.After(50 * time.Millisecond):
				fmt.Fprintf(w, "data: token_%d\n\n", i)
				flusher.Flush()
			}
		}
	}
}

func ExecuteCancellablePrompt(ctx context.Context, serverURL string) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, serverURL, nil)
	if err != nil {
		return err
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		if errors.Is(err, context.Canceled) {
			return fmt.Errorf("запрос отменен вызывающей стороной: %w", err)
		}
		return err
	}
	defer resp.Body.Close()

	buf := make([]byte, 128)
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
			_, err := resp.Body.Read(buf)
			if err != nil {
				return err
			}
		}
	}
}

func main() {
	var aborted atomic.Bool
	server := httptest.NewServer(LLMServerMock(&aborted))
	defer server.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 120*time.Millisecond)
	defer cancel()

	err := ExecuteCancellablePrompt(ctx, server.URL)
	time.Sleep(50 * time.Millisecond) // Даем серверу зафиксировать закрытие

	fmt.Printf("Результат выполнения: err=%v, Сервер инференса прервал работу: %t\n", err != nil, aborted.Load())
}
'''
validate_go_code(code4, "Ex 4")
exercises.append({
    "num": 4,
    "title": "Прерывание генерации и управление контекстом",
    "task": "Спроектируйте отказоустойчивый механизм отмены генерации токенов через context.Context. Докажите, что при вызове cancel() или срабатывании context.WithTimeout Go-клиент немедленно разрывает TCP-сессию, что освобождает вычислительные ресурсы GPU на сервере инференса.",
    "theory": """Генерация каждого токена на современных видеокартах (H100, A100, RTX 4090) требует реального времени инференса и потребляет электроэнергию. Если пользователь закрыл мобильное приложение, переключил страницу или нажал «Остановить генерацию», продолжение стриминга со стороны бэкенда впустую сжигает квоту токенов и перегружает очереди инференс-кластера.
В Go механизм отмены строится на **`context.Context`**:
- При передаче `ctx` в `http.NewRequestWithContext(ctx, ...)` стандартный HTTP-транспорт Go связывает жизненный цикл контекста с базовым сетевым сокетом.
- Как только `ctx.Done()` переходит в закрытое состояние, HTTP-транспорт вызывает `net.Conn.Close()`.
- Сервер инференса (vLLM, Ollama, Python FastAPI) при попытке записи очередного токена в сокет получает системную ошибку `EPIPE` или `ECONNRESET`, перехватывает исключение и немедленно прерывает фазу decoding в нейросети.""",
    "step_by_step": [
        "Создайте имитационный тестовый сервер `LLMServerMock`, который слушает `r.Context().Done()`.",
        "Напишите функцию `ExecuteCancellablePrompt`, передающую контекст в `http.NewRequestWithContext`.",
        "Запустите запрос с жестким таймаутом `context.WithTimeout` (120 мс).",
        "Убедитесь, что сервер инференса зафиксировал прерывание сокета (`aborted.Load() == true`) и освободил ресурсы."
    ],
    "code_blocks": [code4],
    "under_the_hood": "При разрыве соединения со стороны клиента TCP-стек ядра Linux отправляет пакет `FIN` или `RST`. В Go рантайме netpoller фиксирует событие сокета `HUP/ERR`, и метод `resp.Body.Read` мгновенно возвращает ошибку ввода-вывода, не блокируя горутину в ожидании оставшихся байтов.",
    "pitfalls": "Использование устаревшего `http.NewRequest` без передачи контекста (`http.NewRequestWithContext`) приводит к тому, что отмена родительского контекста никак не влияет на выполняющийся HTTP-запрос, продолжая выкачивать токены до полного исчерпания таймаута сокета.",
    "bigtech_interview": "Как в распределенной микросервисной архитектуре гарантировать прерывание дорогостоящего вызова LLM через цепочку из 3 сервисов (API Gateway -> RAG Orchestrator -> LLM Service)?\nОтвет: Через сквозное распространение контекста (Context Propagation) по протоколам gRPC (контекст передается встроенными дедлайнами) или HTTP (заголовок request-timeout / traceparent). При разрыве связи клиентом на Gateway контекст каскадно отменяется по всей цепочке, приводя к разрыву сокетов и остановке вычислений на каждом звене."
})

# Ex 5
code5 = r'''package main

import (
	"fmt"
	"math"
)

// EmbeddingVector инкапсулирует плотный вещественный вектор фиксированной размерности (например, 1536 для OpenAI text-embedding-3-small)
type EmbeddingVector []float32

// Magnitude вычисляет евклидову норму (длину) вектора L2: ||v|| = sqrt(sum(v_i^2))
func (v EmbeddingVector) Magnitude() float32 {
	var sum float64
	for _, val := range v {
		sum += float64(val) * float64(val)
	}
	return float32(math.Sqrt(sum))
}

// Normalize выполняет L2-нормализацию вектора, приводя его длину к 1.0.
// Это критически важно: скалярное произведение двух нормализованных векторов строго равно их косинусному сходству!
func (v EmbeddingVector) Normalize() {
	mag := v.Magnitude()
	if mag == 0 {
		return
	}
	for i := range v {
		v[i] /= mag
	}
}

func main() {
	vec := EmbeddingVector{0.3, 0.4, 0.5, 0.1}
	fmt.Printf("Исходная длина вектора: %.4f\n", vec.Magnitude())
	vec.Normalize()
	fmt.Printf("Длина вектора после L2-нормализации: %.4f, значения: %v\n", vec.Magnitude(), vec)
}
'''
validate_go_code(code5, "Ex 5")
exercises.append({
    "num": 5,
    "title": "Концепция векторных представлений (Embeddings)",
    "task": "Изучите математическую природу текстовых векторных эмбеддингов: плотное представление смыслового пространства в виде массива float32 (1536 или 3072 измерений). Реализуйте структуру EmbeddingVector, метод расчета евклидовой нормы L2 и алгоритм L2-нормализации вектора на чистом Go.",
    "theory": """Языковые модели не оперируют словами напрямую; слова и фразы отображаются в плотные многомерные пространства эмбеддингов (**Embedding Space**).
- **Плотный вектор (Dense Vector)**: В отличие от разреженных представлений (One-Hot Encoding, TF-IDF), где вектор состоит из десятков тысяч нулей и редких единиц, эмбеддинг представляет собой компактный массив чисел `float32` (типичные размерности: 384, 768, 1024, 1536, 3072).
- **Семантическая топология**: Тексты с близким смыслом (*«Ошибки выделения памяти в Go»* и *«Go heap out of memory OOM panic»*) проецируются в близкие точки многомерного пространства, даже если в них нет ни одного общего слова.
- **Евклидова длина (L2-норма)**: $||v|| = \\sqrt{\\sum_{i=1}^n v_i^2}$.
- **Свойство L2-нормализации**: Если вектор нормализован ($||v|| = 1$), то косинусное сходство между $u$ и $v$ превращается в простейшее скалярное произведение:
$$\\cos(\\theta) = \\frac{u \\cdot v}{||u|| \\cdot ||v||} = u \\cdot v = \\sum_{i=1}^n u_i v_i$$
Это позволяет СУБД (pgvector, Redis, Qdrant) заменять ресурсоемкое деление на быстрый Dot Product.""",
    "step_by_step": [
        "Определите тип `EmbeddingVector` как срез `[]float32`.",
        "Реализуйте метод `Magnitude()` с суммированием квадратов элементов во `float64` во избежание переполнения разрядной сетки.",
        "Реализуйте метод `Normalize()`, делящий каждый элемент вектора на его норму L2.",
        "Докажите с помощью теста, что длина нормализованного вектора с точностью до тысячных равна 1.0."
    ],
    "code_blocks": [code5],
    "under_the_hood": "В Go срез `[]float32` размещается в памяти как непрерывный плоский массив 4-байтовых вещественных чисел IEEE 754. Это обеспечивает плотную упаковку: 1536-мерный вектор занимает ровно 6144 байта (1536 * 4), что идеально укладывается в процессорные кэш-линии (L1/L2 Cache Lines по 64 байта) и позволяет процессору эффективно задействовать SIMD инструкции (AVX2/AVX-512/NEON).",
    "pitfalls": "Использование `float64` вместо `float32` для хранения миллионов векторов удваивает потребление памяти (12 КБ на вектор вместо 6 КБ) и нагрузку на шину памяти без какого-либо ощутимого выигрыша в точности семантического поиска.",
    "bigtech_interview": "Почему эмбеддинги для RAG баз данных почти всегда нормализуют перед сохранением в индекс?\nОтвет: L2-нормализация позволяет вычислять косинусное расстояние между запросом и миллионами документов через обычное скалярное произведение (Dot Product), исключая необходимость вычисления квадратных корней и деления для каждого документа при каждом запросе. Это ускоряет вычисление k-NN в 3-5 раз."
})

# Ex 6
code6 = r'''package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type EmbeddingRequest struct {
	Model string `json:"model"`
	Input string `json:"input"`
}

type EmbeddingData struct {
	Object    string    `json:"object"`
	Index     int       `json:"index"`
	Embedding []float32 `json:"embedding"`
}

type EmbeddingResponse struct {
	Object string          `json:"object"`
	Data   []EmbeddingData `json:"data"`
	Model  string          `json:"model"`
	Usage  struct {
		PromptTokens int `json:"prompt_tokens"`
		TotalTokens  int `json:"total_tokens"`
	} `json:"usage"`
}

type Embedder struct {
	baseURL    string
	apiKey     string
	model      string
	httpClient *http.Client
}

func NewEmbedder(baseURL, apiKey, model string) *Embedder {
	return &Embedder{
		baseURL: baseURL,
		apiKey:  apiKey,
		model:   model,
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

func (e *Embedder) GetEmbedding(ctx context.Context, text string) ([]float32, error) {
	reqBody := EmbeddingRequest{
		Model: e.model,
		Input: text,
	}

	payload, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, e.baseURL+"/v1/embeddings", bytes.NewReader(payload))
	if err != nil {
		return nil, fmt.Errorf("create req: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	if e.apiKey != "" {
		httpReq.Header.Set("Authorization", "Bearer "+e.apiKey)
	}

	resp, err := e.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("execute embedding call: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
		return nil, fmt.Errorf("embedding api returned %d: %s", resp.StatusCode, string(body))
	}

	var res EmbeddingResponse
	if err := json.NewDecoder(resp.Body).Decode(&res); err != nil {
		return nil, fmt.Errorf("decode embedding response: %w", err)
	}

	if len(res.Data) == 0 {
		return nil, fmt.Errorf("empty embedding data in response")
	}

	return res.Data[0].Embedding, nil
}

func main() {
	embedder := NewEmbedder("http://localhost:11434", "", "nomic-embed-text")
	fmt.Printf("Embedder инициализирован для модели %s на URL %s\n", embedder.model, embedder.baseURL)
}
'''
validate_go_code(code6, "Ex 6")
exercises.append({
    "num": 6,
    "title": "Генерация текстовых эмбеддингов через API на Go",
    "task": "Напишите модуль векторизации текста GetEmbedding(ctx context.Context, text string) ([]float32, error) через вызов эндпоинта /v1/embeddings. Обеспечьте валидацию структуры ответа, учет расхода токенов и обработку сетевых ошибок.",
    "theory": """Эндпоинт `/v1/embeddings` принимает текстовую строку (или массив строк для батчевой векторизации) и возвращает вектор числовых признаков `[]float32`.
При выборе модели эмбеддингов учитываются параметры:
- **Размерность вектора**: от 384 (`all-MiniLM-L6-v2`) до 1536 (`text-embedding-3-small`) и 3072 (`text-embedding-3-large`).
- **Контекстное окно**: предельное количество токенов во входящем фрагменте (обычно 512, 2048 или 8192 токена).
- **MTEB Benchmark**: рейтинг качества извлечения информации (Massive Text Embedding Benchmark).
В Go критически важно десериализовать массив `embedding` строго в `[]float32`, так как стандартный `encoding/json` при десериализации в `interface{}` преобразует все числа во `float64`, что приводит к лишним аллокациям и двойному расходу RAM.""",
    "step_by_step": [
        "Объявите контрактные структуры `EmbeddingRequest`, `EmbeddingData` и `EmbeddingResponse`.",
        "Инициализируйте клиента с таймаутом `10s` (генерация эмбеддинга для одного абзаца занимает 20–100 мс).",
        "Сформируйте POST-запрос с JSON телом к `/v1/embeddings`.",
        "Проверьте код ответа HTTP и извлеките вектор первого элемента `res.Data[0].Embedding`."
    ],
    "code_blocks": [code6],
    "under_the_hood": "При передаче среза `[]float32` в `json.NewDecoder(resp.Body).Decode(&res)` декодер Go парсит числа напрямую в IEEE-754 binary32 представление, минимизируя промежуточные аллокации. Для пула повторяющихся запросов эмбеддингов рекомендуется переиспользовать байтовые буферы через `sync.Pool`.",
    "pitfalls": "Отправка в эндпоинт эмбеддингов текстов, превышающих контекстный лимит модели (например, >8192 токенов), вызовет ошибку HTTP 400 Bad Request (`context_length_exceeded`). Текст обязан проходить предварительное чанкование (Chunking).",
    "bigtech_interview": "Как организовать батчевую векторизацию (Batch Ingestion) 1 000 000 документов на Go с минимальными затратами?\nОтвет: Передавать в `EmbeddingRequest.Input` не по одному документу, а массив строк батчами по 64-128 элементов. Это многократно сокращает количество HTTP-запросов и позволяет GPU обрабатывать матрицы батчами (Batch Tensor Parallelism) на максимальной утилизации ядер, ускоряя индексацию в 10–20 раз."
})

# Ex 7
code7 = r'''package main

import (
	"errors"
	"fmt"
	"math"
)

var (
	ErrDimensionMismatch = errors.New("dimension mismatch between vectors")
	ErrEmptyVector       = errors.New("vector is empty")
	ErrZeroMagnitude     = errors.New("vector magnitude is zero")
)

// CosineSimilarity вычисляет косинусное сходство между векторами a и b:
// cos(theta) = (a . b) / (||a|| * ||b||)
// Результат находится в диапазоне [-1.0; 1.0], где 1.0 — полное совпадение направления
func CosineSimilarity(a, b []float32) (float32, error) {
	if len(a) == 0 || len(b) == 0 {
		return 0, ErrEmptyVector
	}
	if len(a) != len(b) {
		return 0, ErrDimensionMismatch
	}

	var dotProduct float64
	var normA float64
	var normB float64

	for i := 0; i < len(a); i++ {
		valA := float64(a[i])
		valB := float64(b[i])

		dotProduct += valA * valB
		normA += valA * valA
		normB += valB * valB
	}

	if normA == 0 || normB == 0 {
		return 0, ErrZeroMagnitude
	}

	similarity := dotProduct / (math.Sqrt(normA) * math.Sqrt(normB))
	return float32(similarity), nil
}

func main() {
	v1 := []float32{1.0, 2.0, 3.0}
	v2 := []float32{1.0, 2.0, 3.0}
	v3 := []float32{-1.0, -2.0, -3.0}

	simSame, _ := CosineSimilarity(v1, v2)
	simOpposite, _ := CosineSimilarity(v1, v3)

	fmt.Printf("Сходство идентичных векторов: %.4f (ожидается 1.0000)\n", simSame)
	fmt.Printf("Сходство противоположных векторов: %.4f (ожидается -1.0000)\n", simOpposite)
}
'''
validate_go_code(code7, "Ex 7")
exercises.append({
    "num": 7,
    "title": "Математика векторного сходства на Go: Cosine Similarity",
    "task": "Реализуйте функцию вычисления косинусного сходства (Cosine Similarity) между двумя произвольными срезами []float32 на чистом Go. Предусмотрите проверку совпадения размерностей, защиту от деления на ноль для нулевых векторов и аккумулирование промежуточных сумм во float64.",
    "theory": """Косинусное сходство измеряет угол между двумя многомерными векторами независимо от их амплитуды:
$$\\text{CosineSimilarity}(u, v) = \\frac{\\sum_{i=1}^n u_i v_i}{\\sqrt{\\sum_{i=1}^n u_i^2} \\cdot \\sqrt{\\sum_{i=1}^n v_i^2}}$$
Интерпретация значений:
- `1.0`: Векторы сонаправлены (тексты идентичны по смыслу).
- `0.0`: Векторы ортогональны (тексты не имеют смысловой связи).
- `-1.0`: Векторы диаметрально противоположны по значению.
Косинусное расстояние (Cosine Distance), используемое в базах данных:
$$\\text{CosineDistance}(u, v) = 1 - \\text{CosineSimilarity}(u, v)$$
Диапазон расстояния: от 0.0 (ближайшие) до 2.0 (противоположные).""",
    "step_by_step": [
        "Проверьте краевые условия: пустые срезы и несовпадение размерностей `len(a) != len(b)`.",
        "Вычислите скалярное произведение `dotProduct` и квадраты длин `normA`, `normB` в одном проходе по массиву.",
        "Используйте `float64` для внутренних аккумуляторов для предотвращения потери точности на векторах большой размерности (1536+).",
        "Обработайте случай нулевой нормы вектора, возвращая типизированную ошибку `ErrZeroMagnitude`."
    ],
    "code_blocks": [code7],
    "under_the_hood": "Объединение вычисления dotProduct, normA и normB в единый цикл `for i := 0; i < len(a); i++` позволяет компилятору Go задействовать одни и те же регистры процессора без повторных обращений к оперативной памяти, загружая элементы обоих срезов в L1 Data Cache синхронно.",
    "pitfalls": "Вычисление сумм в типе `float32` при размерности 3072 элемента может привести к эффекту поглощения малых величин (Floating Point Absorption) из-за ограниченной 24-битной мантиссы IEEE 754. Аккумуляторы обязаны быть `float64`.",
    "bigtech_interview": "В чем разница между Косинусным сходством (Cosine Similarity), Евклидовым расстоянием (L2 Distance) и Скалярным произведением (Dot Product)?\nОтвет: Косинусное сходство учитывает только угол между векторами, игнорируя их длину. L2 Distance (Евклидово расстояние) учитывает абсолютное геометрическое расстояние между точками. Dot Product учитывает и угол, и длины векторов. Если векторы предварительно L2-нормализованы к длине 1.0, все три метрики дают эквивалентный порядок ранжирования, но Dot Product вычисляется быстрее всего, так как не требует извлечения корней."
})

# Ex 8
code8 = r'''package main

import (
	"fmt"
	"math/rand"
	"time"
)

// DotProductStandard — базовая реализация скалярного произведения
func DotProductStandard(a, b []float32) float32 {
	var sum float32
	for i := 0; i < len(a); i++ {
		sum += a[i] * b[i]
	}
	return sum
}

// DotProductUnrolled8 — оптимизированная реализация со сплошным разворачиванием цикла (Loop Unrolling по 8 элементов)
// и 8 независимыми аккумуляторами, позволяющая CPU задействовать конвейеризацию суперскалярного ядра (ILP)
func DotProductUnrolled8(a, b []float32) float32 {
	n := len(a)
	idx := 0

	var (
		s0, s1, s2, s3 float32
		s4, s5, s6, s7 float32
	)

	limit := n - 7
	for idx < limit {
		s0 += a[idx+0] * b[idx+0]
		s1 += a[idx+1] * b[idx+1]
		s2 += a[idx+2] * b[idx+2]
		s3 += a[idx+3] * b[idx+3]
		s4 += a[idx+4] * b[idx+4]
		s5 += a[idx+5] * b[idx+5]
		s6 += a[idx+6] * b[idx+6]
		s7 += a[idx+7] * b[idx+7]
		idx += 8
	}

	sum := (s0 + s1) + (s2 + s3) + (s4 + s5) + (s6 + s7)

	// Досчитываем оставшийся хвост
	for ; idx < n; idx++ {
		sum += a[idx] * b[idx]
	}

	return sum
}

func main() {
	dim := 1536
	vecA := make([]float32, dim)
	vecB := make([]float32, dim)
	r := rand.New(rand.NewSource(42))
	for i := 0; i < dim; i++ {
		vecA[i] = r.Float32()
		vecB[i] = r.Float32()
	}

	start := time.Now()
	var resStandard float32
	for i := 0; i < 100000; i++ {
		resStandard = DotProductStandard(vecA, vecB)
	}
	durStandard := time.Since(start)

	start = time.Now()
	var resUnrolled float32
	for i := 0; i < 100000; i++ {
		resUnrolled = DotProductUnrolled8(vecA, vecB)
	}
	durUnrolled := time.Since(start)

	fmt.Printf("Стандартный: res=%.2f, время=%v\n", resStandard, durStandard)
	fmt.Printf("Unrolled x8:  res=%.2f, время=%v (Ускорение: %.2fx)\n",
		resUnrolled, durUnrolled, float64(durStandard)/float64(durUnrolled))
}
'''
validate_go_code(code8, "Ex 8")
exercises.append({
    "num": 8,
    "title": "Оптимизация векторных вычислений на Go (SIMD и разворачивание циклов)",
    "task": "Реализуйте оптимизированную функцию скалярного произведения DotProductUnrolled8 с разворачиванием цикла (Loop Unrolling) по 8 элементов и раздельными аккумуляторами для утилизации Instruction-Level Parallelism (ILP). Замерьте ускорение по сравнению со стандартным циклом на векторе размерностью 1536.",
    "theory": """При поиске в оперативной памяти среди 100 000 векторов скалярное произведение вычисляется сотни тысяч раз.
Почему простой цикл `for i := 0; i < n; i++` не утилизирует мощь процессора?
1. **Зависимость данных (Data Hazard)**: В цикле `sum += a[i] * b[i]` каждая следующая операция сложения обязана ожидать завершения предыдущей, блокируя конвейер вещественного FPU (латентность FADD/FMUL составляет 3–5 тактов).
2. **Накладные расходы ветвления (Branch Overhead)**: На каждой итерации процессор проверяет условие `i < n` и инкрементирует счетчик.
3. **Разворачивание с несколькими аккумуляторами (ILP)**:
Разделив сумму на 8 независимых переменных `s0...s7`, мы позволяем современному суперскалярному CPU (Out-of-Order execution) параллельно выполнять до 4 умножений и сложений за такт в разных портах исполнения FPU.""",
    "step_by_step": [
        "Объявите 8 независимых аккумуляторов `s0...s7` типа `float32`.",
        "Организуйте основной цикл с шагом 8: `idx < limit`.",
        "Выполняйте независимые операции умножения и сложения без взаимных блокировок конвейера.",
        "В завершении сложите аккумуляторы древовидным способом и обработайте остаток элементов вектора."
    ],
    "code_blocks": [code8],
    "under_the_hood": "Компилятор Go при использовании нескольких независимых аккумуляторов аллоцирует их в разные регистры SSE/AVX (xmm0-xmm7). Это полностью исключает регистровые коллизии и позволяет суперскалярному планировщику CPU конвейеризовать операции с минимальными задержками (IPC > 2.5).",
    "pitfalls": "Использование единого аккумулятора при разворачивании цикла (`sum += a[i]*b[i] + a[i+1]*b[i+1]...`) не дает эффекта ускорения, так как сохраняется линейная зависимость по данным для переменной `sum`.",
    "bigtech_interview": "Почему разворачивание циклов с несколькими аккумуляторами дает почти такое же ускорение, как ассемблерные SIMD-инструкции в чистом Go?\nОтвет: Современные процессоры с микроархитектурой x86-64 и ARM64 обладают широкими суперскалярными конвейерами (до 6-8 инструкций за такт). Устраняя зависимости по данным через раздельные аккумуляторы, мы даем механизму внеочередного исполнения (Out-of-Order Execution) возможность самостоятельно заполнять все функциональные блоки FPU на 100%."
})

# Ex 9
code9 = r'''package main

import (
	"context"
	"fmt"
	"strings"
)

// SQLMigration демонстрирует DDL-миграцию для PostgreSQL с pgvector
const SQLMigration = `
-- Шаг 1: Активация векторного расширения
CREATE EXTENSION IF NOT EXISTS vector;

-- Шаг 2: Таблица чанков базы знаний
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id VARCHAR(128) NOT NULL,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(1536) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_doc_chunk UNIQUE(document_id, chunk_index)
);

-- Шаг 3: B-Tree индексы для метаданных
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON knowledge_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON knowledge_chunks USING gin (metadata);
`

// VectorToPostgresString преобразует срез float32 в строковый формат pgvector: '[0.123,0.456,...]'
func VectorToPostgresString(vec []float32) string {
	var sb strings.Builder
	sb.Grow(len(vec)*10 + 2)
	sb.WriteByte('[')
	for i, v := range vec {
		if i > 0 {
			sb.WriteByte(',')
		}
		fmt.Fprintf(&sb, "%.6f", v)
	}
	sb.WriteByte(']')
	return sb.String()
}

func main() {
	sample := []float32{0.012345, -0.987654, 0.555555}
	pgStr := VectorToPostgresString(sample)
	fmt.Printf("Строковое представление pgvector: %s\n", pgStr)
	fmt.Printf("Схема миграции содержит %d символов DDL.\n", len(SQLMigration))
}
'''
validate_go_code(code9, "Ex 9")
exercises.append({
    "num": 9,
    "title": "Векторная база данных PostgreSQL с расширением pgvector",
    "task": "Спроектируйте схему хранения векторных эмбеддингов в PostgreSQL с использованием расширения pgvector. Напишите миграцию DDL (CREATE EXTENSION, таблица knowledge_chunks с полем vector(1536), GIN-индекс метаданных) и эффективный конвертер Go-среза []float32 в текстовый формат pgvector.",
    "theory": """**pgvector** — ведущее open-source расширение для PostgreSQL, превращающее классическую реляционную СУБД в полноценную векторную базу данных.
Ключевые преимущества pgvector перед специализированными векторными БД (Pinecone, Milvus):
1. **ACID и единый контур транзакций**: Текстовый контент, реляционные связи пользователей, списки прав доступа (RBAC), JSON-метаданные и векторные эмбеддинги хранятся в одной базе без необходимости синхронизации между разными системами.
2. **Тип данных vector(N)**: Поддерживает размерности до 16 000 измерений. Внутри представляет собой непрерывный C-массив чисел `float4`.
3. **Операторы расстояния в SQL**:
   - `<->` : Евклидово расстояние (L2 Distance).
   - `<=>` : Косинусное расстояние (Cosine Distance).
   - `<#>` : Отрицательное скалярное произведение (Negative Inner Product).""",
    "step_by_step": [
        "Сформируйте DDL-скрипт с созданием расширения `CREATE EXTENSION IF NOT EXISTS vector`.",
        "Создайте таблицу `knowledge_chunks` с полями `id`, `document_id`, `content`, `metadata (jsonb)` и `embedding vector(1536)`.",
        "Добавьте ограничение уникальности `(document_id, chunk_index)` для поддержки идемпотентной перезаписи чанков.",
        "Реализуйте функцию сериализации `VectorToPostgresString` с предварительной аллокацией `strings.Builder.Grow`."
    ],
    "code_blocks": [code9],
    "under_the_hood": "Драйвер `jackc/pgx/v5` поддерживает регистрацию кастомных бинарных кодеков для типа pgvector через пакет `github.com/pgvector/pgvector-go`. Это позволяет передавать срезы `[]float32` в бинарном формате PostgreSQL wire protocol без накладных расходов на промежуточную конвертацию во фреймы строк ASCII.",
    "pitfalls": "Забытое указание размерности в `vector(1536)` позволяет сохранять векторы произвольной длины, что исключит возможность создания HNSW/IVFFlat индексов, требующих строго фиксированной размерности.",
    "bigtech_interview": "Почему для RAG-систем энтерпрайз-уровня компании часто предпочитают PostgreSQL + pgvector отдельным базам данных вроде Pinecone или Qdrant?\nОтвет: В реальных enterprise-системах поиск никогда не бывает «чисто векторным». Требуется строгая изоляция по тенантам (Multi-Tenancy), фильтрация по правам доступа пользователя в реальном времени (`WHERE company_id = $1 AND role IN (...)`), транзакционная целостность при удалении документов и единое резервное копирование (pg_dump, WAL-G). PostgreSQL с pgvector решает все эти задачи без риска рассинхронизации данных."
})

# Ex 10
code10 = r'''package main

import "fmt"

const HNSWIndexSQL = `
-- Создание HNSW индекса для косинусного расстояния:
-- vector_cosine_ops связывает индекс с оператором <=>
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw 
ON knowledge_chunks 
USING hnsw (embedding vector_cosine_ops)
WITH (
    m = 16,               -- Максимальное количество связей у вершины на каждом уровне графа (типично: 16-64)
    ef_construction = 64  -- Размер динамического списка кандидатов при построении графа (типично: 64-128)
);
`

const IVFFlatIndexSQL = `
-- Создание IVFFlat индекса для косинусного расстояния:
-- ТРЕБУЕТ предварительного заполнения таблицы данными для качественного обучения центроидов k-means!
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_ivfflat 
ON knowledge_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (
    lists = 1000          -- Количество кластеров центроидов (эмпирически: rows / 1000 для <1M строк)
);
`

func main() {
	fmt.Println("=== Сравнение индексов векторов в PostgreSQL pgvector ===")
	fmt.Printf("1. HNSW: Идеален для динамических баз данных, высокая точность (Recall > 98%%), быстрый поиск.\n")
	fmt.Printf("2. IVFFlat: Строится быстрее, требует меньше RAM, но чувствителен к добавлению новых векторов.\n")
	fmt.Printf("Размер DDL HNSW: %d байт, IVFFlat: %d байт\n", len(HNSWIndexSQL), len(IVFFlatIndexSQL))
}
'''
validate_go_code(code10, "Ex 10")
exercises.append({
    "num": 10,
    "title": "Индексы векторов в pgvector: IVFFlat vs HNSW",
    "task": "Изучите и сравните алгоритмы приближенного поиска k-ближайших соседей (ANN) в pgvector: IVFFlat и HNSW. Напишите корректные SQL-выражения для создания HNSW-индекса с параметрами m=16, ef_construction=64 и классами операторов vector_cosine_ops.",
    "theory": """Точный поиск k-NN (Flat / Sequential Scan) требует полного перебора всех строк в таблице ($O(N)$), что при объеме свыше 100 000 векторов вызывает неприемлемые задержки (сотни миллисекунд).
Для ускорения применяются алгоритмы **Approximate Nearest Neighbors (ANN)**:
1. **IVFFlat (Inverted File Flat)**:
   - Векторное пространство делится на кластеры ($lists$) методом k-means.
   - Поиск проверяет только векторы в ближайших к запросу кластерах ($probes$).
   - *Плюсы*: Быстрое построение, минимальное потребление памяти.
   - *Минусы*: Низкий Recall при плохом обучении центроидов; индекс нельзя эффективно строить на пустой таблице.
2. **HNSW (Hierarchical Navigable Small World)**:
   - Строит многоуровневый иерархический граф по аналогии с Skip List. Верхние слои графа имеют длинные «экспресс-связи» для быстрого перелета по пространству, нижние слои — плотные связи для точной локализации.
   - *Параметр $m$*: максимальное число ребер на узел (16–64). Больше $m$ — выше точность, но больше RAM.
   - *Параметр $ef\\_construction$*: глубина поиска при построении (64–200).
   - *Плюсы*: Выдающийся Recall (98-99%), высочайшая скорость поиска, не требует предварительного обучения.
   - *Минусы*: Индекс строится дольше и занимает значительный объем памяти в shared_buffers.""",
    "step_by_step": [
        "Изучите спецификацию параметров HNSW: `m`, `ef_construction`.",
        "Укажите класс операторов `vector_cosine_ops` для косинусного поиска (или `vector_l2_ops` для L2).",
        "Сформируйте SQL-запрос создания индекса HNSW с конструкцией `WITH (m = 16, ef_construction = 64)`.",
        "Сравните накладные расходы по памяти и скорости между HNSW и IVFFlat."
    ],
    "code_blocks": [code10],
    "under_the_hood": "Индекс HNSW полностью хранится в страничном кэше PostgreSQL (`shared_buffers`). При поиске алгоритм стартует с точки входа на самом верхнем слое графа, жадно перемещаясь к ближайшему узлу, затем спускается на слой ниже. Это снижает алгоритмическую сложность поиска с $O(N)$ до $O(\\log N)$.",
    "pitfalls": "Создание индекса IVFFlat на пустой таблице с последующей вставкой 500 000 векторов приведет к катастрофической потере точности (Recall упадет до 20-30%), так как центроиды k-means обучены на нуле данных.",
    "bigtech_interview": "Как настроить параметр ef_search при выполнении запросов к HNSW индексу в сессии PostgreSQL?\nОтвет: Через команду `SET hnsw.ef_search = 100;`. Параметр ef_search определяет размер динамического списка кандидатов во время выполнения запроса. По умолчанию он равен 40. Увеличение до 100-200 повышает точность поиска (Recall) ценой небольшого увеличения латентности запроса."
})

# Ex 11
code11 = r'''package main

import (
	"context"
	"fmt"
	"time"
)

type DocumentChunk struct {
	ID         string  `json:"id"`
	DocumentID string  `json:"document_id"`
	Content    string  `json:"content"`
	Similarity float64 `json:"similarity"`
}

// VectorStoreQuery имитирует SQL-запрос векторного поиска через pgxpool
type VectorStoreQuery struct {
	SQL string
}

func BuildSearchQuery(limit int) string {
	// В PostgreSQL с pgvector оператор <=> означает косинусное расстояние.
	// Косинусное сходство вычисляется как 1 - (embedding <=> $1).
	return fmt.Sprintf(`
		SELECT 
			id::text, 
			document_id, 
			content, 
			1 - (embedding <=> $1) AS similarity
		FROM knowledge_chunks
		WHERE 1 - (embedding <=> $1) > 0.70
		ORDER BY embedding <=> $1 ASC
		LIMIT %d;
	`, limit)
}

func main() {
	querySQL := BuildSearchQuery(5)
	fmt.Printf("Сгенерированный SQL-запрос векторного поиска:\n%s\n", querySQL)
}
'''
validate_go_code(code11, "Ex 11")
exercises.append({
    "num": 11,
    "title": "Векторный поиск ближайших документов через pgx",
    "task": "Напишите функцию векторного поиска релевантных фрагментов документации через пул соединений pgxpool. Поиск должен использовать оператор косинусного расстояния <=>, фильтровать результаты по порогу сходства (> 0.70) и сортировать документы по возрастанию расстояния.",
    "theory": """Векторный поиск в pgvector формулируется в стандартном SQL:
```sql
SELECT id, content, 1 - (embedding <=> $1) AS similarity
FROM knowledge_chunks
ORDER BY embedding <=> $1 ASC
LIMIT 5;
```
Механика работы:
1. В качестве параметра `$1` передается вектор запроса (в бинарном виде или в виде строки `'[0.12, 0.45, ...]'`).
2. Оператор `<=>` возвращает косинусное расстояние ($1 - \\cos(\\theta)$).
3. Индекс HNSW использует оператор `<=>` для навигации по графу и находит k ближайших соседей за $O(\\log N)$.
4. Выражение `1 - (embedding <=> $1)` возвращает нормализованную метрику косинусного сходства от 0.0 до 1.0 для удобной фильтрации порога релевантности.""",
    "step_by_step": [
        "Спроектируйте SQL-запрос с сортировкой `ORDER BY embedding <=> $1 ASC`.",
        "Добавьте вычисление нормализованного сходства `1 - (embedding <=> $1) AS similarity`.",
        "Предусмотрите фильтрацию порога отсечения нерелевантного шума (`WHERE ... > 0.70`).",
        "Ограничьте размер выборки директивой `LIMIT`."
    ],
    "code_blocks": [code11],
    "under_the_hood": "Когда в запросе присутствует конструкция `ORDER BY embedding <=> $1 LIMIT K`, планировщик PostgreSQL выбирает план `Index Scan using idx_chunks_embedding_hnsw`. Граф сканируется ровно до нахождения K вершин с минимальным расстоянием, исключая сортировку всей таблицы в оперативной памяти (Sort / Materialize nodes отсутствуют в Explain Analyze).",
    "pitfalls": "Добавление неиндексированных условий `WHERE other_field = 'value'` в запрос может заставить планировщик отказаться от HNSW-индекса в пользу Sequential Scan (эффект Post-Filtering). Для исправления используют составные индексы или частичные HNSW индексы.",
    "bigtech_interview": "Что такое проблема Post-Filtering при векторном поиске и как ее решать в pgvector?\nОтвет: Если запрос содержит `WHERE category = 'tech' ORDER BY embedding <=> $1 LIMIT 5`, база может сначала найти 5 ближайших векторов по индексу HNSW, а затем отфильтровать их по категории. Если среди найденных 5 векторов нет нужной категории, запрос вернет пустой результат, хотя в базе есть подходящие документы. В последних версиях pgvector реализован Iterative Index Scan, который продолжает обход графа HNSW до тех пор, пока не будет набрано запрошенное количество строк, удовлетворяющих фильтрам WHERE."
})

# Ex 12
code12 = r'''package main

import (
	"context"
	"fmt"
	"strings"
)

type RAGContext struct {
	Query     string
	Documents []string
}

// BuildAugmentedPrompt формирует системный контекст и финальный промпт с инъекцией фактов из векторной базы
func BuildAugmentedPrompt(ragCtx RAGContext) string {
	var sb strings.Builder

	sb.WriteString("Вы — надежный корпоративный ИИ-ассистент по архитектуре Go.\n")
	sb.WriteString("Отвечайте на вопрос пользователя СТРОГО на основе предоставленной ниже документации.\n")
	sb.WriteString("Если информации для ответа недостаточно в контексте, честно ответьте: 'Недостаточно данных в базе знаний'.\n")
	sb.WriteString("Не придумывайте факты от себя (zero hallucination).\n\n")

	sb.WriteString("=== НАЧАЛО КОНТЕКСТА ===\n")
	for i, doc := range ragCtx.Documents {
		fmt.Fprintf(&sb, "[Документ %d]:\n%s\n\n", i+1, strings.TrimSpace(doc))
	}
	sb.WriteString("=== КОНЕЦ КОНТЕКСТА ===\n\n")

	fmt.Fprintf(&sb, "Вопрос пользователя: %s\n", ragCtx.Query)
	sb.WriteString("Ответ:")

	return sb.String()
}

func main() {
	ctx := RAGContext{
		Query: "Как настроить GOMEMLIMIT для предотвращения OOM в Kubernetes?",
		Documents: []string{
			"GOMEMLIMIT задает мягкий лимит памяти для рантайма Go (введен в Go 1.19). При приближении к лимиту GC инициирует более частые циклы сборки мусора.",
			"Рекомендуемое значение GOMEMLIMIT составляет 90% от лимита контейнера cgroup (memory.limit_in_bytes) для запаса на стек и структуры ОС.",
		},
	}

	prompt := BuildAugmentedPrompt(ctx)
	fmt.Printf("Сформированный RAG-промпт:\n%s\n", prompt)
}
'''
validate_go_code(code12, "Ex 12")
exercises.append({
    "num": 12,
    "title": "Архитектура Retrieval-Augmented Generation (RAG)",
    "task": "Спроектируйте архитектуру классического RAG-конвейера: извлечение релевантных документов из векторного индекса -> сборка системного промпта с инъекцией фактов -> передача в языковую модель с инструкцией исключения галлюцинаций.",
    "theory": """**RAG (Retrieval-Augmented Generation)** — ведущий архитектурный паттерн преодоления фундаментальных ограничений LLM:
1. **Галлюцинации (Hallucinations)**: Языковые модели статистически предсказывают следующие токены и склонны уверенно генерировать вымышленные API, ссылки и факты.
2. **Устаревание знаний (Knowledge Cutoff)**: Модель не знает данных, появившихся после завершения ее обучения.
3. **Приватность корпоративных данных**: Обучение или Fine-Tuning модели на закрытых репозиториях дорого и несет риск утечки данных через промпты.
Конвейер RAG разделяет знание на две части:
- **Параметрическая память**: Сама модель (способность рассуждать, следовать синтаксису Go, анализировать логику).
- **Непараметрическая память**: Векторная база данных (актуальная документация, регламенты, код).
Входящий запрос векторизуется, векторный поиск находит Top-K релевантных абзацев, которые подставляются в контекст запроса с жесткой инструкцией: *«Отвечай строго по контексту, не додумывая факты»*.""",
    "step_by_step": [
        "Определите структуру `RAGContext` с полями `Query` и срезом найденных фрагментов `Documents`.",
        "Реализуйте функцию `BuildAugmentedPrompt` с четким разграничением системной инструкции и контекста фактов.",
        "Добавьте защиту от галлюцинаций с требованием возвращать 'Недостаточно данных', если ответ не найден в документах.",
        "Проверьте форматирование через тесты."
    ],
    "code_blocks": [code12],
    "under_the_hood": "Инъекция контекста в промпт увеличивает количество входящих токенов (Prompt Tokens). В современных моделях Attention-механизм (FlashAttention-2) обрабатывает длинный промпт параллельно на этапе Prefill фазы, после чего генерация ответа идет по токенам (Decode фаза).",
    "pitfalls": "Подстановка слишком большого объема документов в контекст (более 20 чанков) приводит к эффекту 'Lost in the Middle', когда модель обращает внимание только на начало и конец промпта, игнорируя факты из середины.",
    "bigtech_interview": "Что такое 'Lost in the Middle' в контексте больших промптов и как RAG-инженеры борются с этим явлением?\nОтвет: Это феномен архитектуры Transformer: при длинном контексте внимание (Self-Attention) распределяется U-образно — модель лучше всего извлекает факты, расположенные в самом начале или самом конце контекста. Для борьбы с этим применяют: 1) Ограничение Top-K до 3–5 наиболее релевантных чанков; 2) Пересортировку (Re-ranking), помещающую самый релевантный документ в самое начало или конец секции контекста."
})

# Ex 13
code13 = r'''package main

import (
	"fmt"
	"strings"
	"unicode/utf8"
)

type TextChunk struct {
	Index   int
	Content string
	Tokens  int
}

// SimpleChunker разбивает длинный текст на фрагменты фиксированного размера с перекрытием (Overlap)
func SimpleChunker(text string, chunkSizeChars, overlapChars int) []TextChunk {
	if chunkSizeChars <= 0 {
		chunkSizeChars = 1000
	}
	if overlapChars >= chunkSizeChars {
		overlapChars = chunkSizeChars / 4
	}

	var chunks []TextChunk
	runes := []rune(text)
	totalRunes := len(runes)
	start := 0
	chunkIdx := 0

	for start < totalRunes {
		end := start + chunkSizeChars
		if end > totalRunes {
			end = totalRunes
		}

		// Пытаемся подвинуть границу к концу предложения или абзаца
		if end < totalRunes {
			for i := end; i > start+chunkSizeChars/2; i-- {
				if runes[i] == '\n' || runes[i] == '.' {
					end = i + 1
					break
				}
			}
		}

		chunkText := strings.TrimSpace(string(runes[start:end]))
		if chunkText != "" {
			chunks = append(chunks, TextChunk{
				Index:   chunkIdx,
				Content: chunkText,
				Tokens:  utf8.RuneCountInString(chunkText) / 4, // Эвристическая оценка токенов (~4 символа на токен)
			})
			chunkIdx++
		}

		if end == totalRunes {
			break
		}

		start = end - overlapChars
	}

	return chunks
}

func main() {
	doc := `Пакет net/http в Go предоставляет мощные инструменты для создания HTTP-серверов.
Он поддерживает HTTP/1.1 и HTTP/2 из коробки.
Для высоконагруженных систем критически важно настраивать таймауты ReadTimeout, WriteTimeout и IdleTimeout.
Никогда не используйте http.ListenAndServe без кастомного http.Server в продакшене.
Это позволит избежать утечек горутин и зависания соединений.`

	chunks := SimpleChunker(doc, 120, 30)
	fmt.Printf("Текст разбит на %d чанков:\n", len(chunks))
	for _, c := range chunks {
		fmt.Printf("--- Чанк #%d (оценка %d токенов) ---\n%s\n", c.Index, c.Tokens, c.Content)
	}
}
'''
validate_go_code(code13, "Ex 13")
exercises.append({
    "num": 13,
    "title": "Стратегии чанкования документов (Document Chunking)",
    "task": "Напишите модуль чанкования текстовых документов на Go: разбиение на фрагменты фиксированного размера с скользящим окном перекрытия (Overlap) и привязкой границ чанков к окончаниям предложений и переносам строк.",
    "theory": """Нельзя передавать в модель векторизации книги и многостраничные мануалы целиком.
Причины необходимости **Чанкования (Chunking)**:
1. **Лимит размера входа модели эмбеддингов**: Модель эмбеддингов имеет строгое контекстное окно (512–8192 токена).
2. **Размытие семантического вектора (Information Dilution)**: Если сжать статью на 50 страниц в один 1536-мерный вектор, он превратится в «усредненный шум». Точечные факты будут потеряны.
3. **Гранулярность поиска**: Чем меньше чанк (например, 200–500 токенов), тем точнее векторное сходство отражает конкретную мысль или функцию.
Зачем нужно **Перекрытие (Overlap)**?
Если критически важное утверждение (*«При значении флага X функция Y вернет ошибку»*) окажется разрезано пополам границей чанков, ни один из двух фрагментов не сохранит цельный смысл. Перекрытие в 10–20% (50–100 токенов) гарантирует целостность пограничных утверждений.""",
    "step_by_step": [
        "Преобразуйте строку в срез рун `[]rune` для корректной поддержки UTF-8 (русский язык занимает по 2 байта на символ).",
        "Реализуйте смещение окна `start` и `end` с шагом `chunkSize - overlap`.",
        "Реализуйте откат границы `end` влево до ближайшей точки `.` или переноса строки `\\n` для предотвращения обрыва предложений на полуслове.",
        "Удалите лишние пробелы и сохраните срез чанков `[]TextChunk`."
    ],
    "code_blocks": [code13],
    "under_the_hood": "Прямая итерация по байтам строки в Go `string[start:end]` для кириллицы приведет к повреждению UTF-8 последовательностей (рассечению 2-байтовой буквы на невалидные байты). Преобразование в `[]rune` гарантирует работу с кодовыми точками Юникода, исключая кракозябры `\\uFFFD`.",
    "pitfalls": "Установка `overlap >= chunkSize` приведет к бесконечному циклу генерации чанков с нулевым прогрессом `start`.",
    "bigtech_interview": "Какие продвинутые стратегии чанкования (Chunking Strategies) применяются в продакшене вместо фиксированного размера?\nОтвет: 1) **Markdown / Semantic Chunking**: разбиение по заголовкам H1, H2, H3 и блокам кода; 2) **Recursive Character Chunking**: рекурсивная попытка разделить текст сначала по двойным переносам `\\n\\n`, затем по `\\n`, затем по предложениям и только в крайнем случае по словам; 3) **Parent-Document (Hierarchical) Chunking**: поиск по мелким дочерним чанкам (200 токенов), но передача в LLM родительского блока целиком (1500 токенов)."
})

# Ex 14
code14 = r'''package main

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

type DocumentFile struct {
	Path    string
	Content string
}

type IngestionPipeline struct {
	workers int
}

func NewIngestionPipeline(workers int) *IngestionPipeline {
	return &IngestionPipeline{workers: workers}
}

func (p *IngestionPipeline) ProcessDocuments(ctx context.Context, docs []DocumentFile) (int64, error) {
	docChan := make(chan DocumentFile, len(docs))
	for _, d := range docs {
		docChan <- d
	}
	close(docChan)

	var wg sync.WaitGroup
	var totalChunksProcessed atomic.Int64

	// Fan-Out: пул конкурентных воркеров
	for w := 0; w < p.workers; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for {
				select {
				case <-ctx.Done():
					return
				case doc, ok := <-docChan:
					if !ok {
						return
					}
					// 1. Чанкование
					chunksCount := int64(len(doc.Content) / 100)
					if chunksCount == 0 {
						chunksCount = 1
					}

					// 2. Имитация обращения к API эмбеддингов
					time.Sleep(10 * time.Millisecond)

					// 3. Аккумулирование
					totalChunksProcessed.Add(chunksCount)
				}
			}
		}(w)
	}

	wg.Wait()
	return totalChunksProcessed.Load(), nil
}

func main() {
	pipeline := NewIngestionPipeline(4)
	docs := []DocumentFile{
		{Path: "doc1.md", Content: "Конкурентность в Go строится на базе CSP моделей и каналов связи."},
		{Path: "doc2.md", Content: "Планировщик GMP распределяет горутины по операционным потокам ядра."},
		{Path: "doc3.md", Content: "Аллокатор кучи mcache mcentral mheap минимизирует глобальные блокировки."},
	}

	ctx := context.Background()
	count, _ := pipeline.ProcessDocuments(ctx, docs)
	fmt.Printf("Конвейер индексации успешно обработал %d документов, создано чанков: %d\n", len(docs), count)
}
'''
validate_go_code(code14, "Ex 14")
exercises.append({
    "num": 14,
    "title": "Конвейер индексации базы знаний (Ingestion Pipeline)",
    "task": "Спроектируйте масштабируемый конкурентный конвейер пакетной индексации документации на Go с применением паттерна Fan-Out/Fan-In (Worker Pool), потокобезопасным учетом обработанных чанков через atomic.Int64 и защитой от утечек горутин при отмене контекста.",
    "theory": """Индексация корпоративной базы знаний (сотни тысяч Markdown файлов из Confluence, Notion, GitLab) — тяжелый вычислительный процесс.
Последовательная индексация одного документа за другим занимает часы.
Паттерн **Fan-Out / Fan-In** на Go позволяет масштабировать процесс:
1. **Producer**: Сканирует директории с файлами или опрашивает S3-бакет и отправляет задачи в буферизованный канал.
2. **Worker Pool (Fan-Out)**: Пул из $N$ горутин (например, 16–32 воркера) параллельно:
   - Читает файл.
   - Выполняет чанкование текста.
   - Отправляет батч в модель эмбеддингов.
3. **Consumer / Batch Flusher (Fan-In)**: Агрегирует готовые векторы и выполняет массовую вставку в PostgreSQL через `pgx.CopyFrom` пачками по 500–1000 строк, минуя оверхед построчных SQL INSERT.""",
    "step_by_step": [
        "Определите структуру `IngestionPipeline` с настраиваемым количеством воркеров.",
        "Создайте канал передачи документов и организуйте `sync.WaitGroup` для ожидания завершения всех горутин пула.",
        "Реализуйте обработку `select` с ветками `<-ctx.Done()` и `doc, ok := <-docChan`.",
        "Используйте `atomic.Int64` для учета суммарного количества обработанных чанков."
    ],
    "code_blocks": [code14],
    "under_the_hood": "Использование буферизованного канала задач снижает contention между воркерами. В связке с пулом `pgxpool.Pool` воркеры не конкурируют за глобальный lock, так как каждый воркер получает собственное TCP-соединение из пула для выполнения пакетных операций.",
    "pitfalls": "Запуск отдельной горутины на каждый файл без ограничения размера пула (`go process(file)`) на директории с 500 000 файлов приведет к исчерпанию лимита открытых дескрипторов `ulimit -n` (too many open files) и падению процесса.",
    "bigtech_interview": "Почему при массовой вставке сотен тысяч векторов в PostgreSQL pgvector рекомендуется сначала вставить данные через pgx.CopyFrom, и только ПОСЛЕ этого создавать индекс HNSW?\nОтвет: Построение индекса HNSW «на лету» при каждой одиночной вставке вынуждает СУБД для каждого нового вектора искать соседей и перестраивать ребра многослойного графа, что приводит к замедлению вставки в 10–50 раз. Пакетная загрузка в чистую таблицу с последующим однократным `CREATE INDEX` занимает в десятки раз меньше времени и оперативной памяти."
})

# Ex 15
code15 = r'''package main

import (
	"fmt"
	"sort"
)

type SearchResultItem struct {
	DocID string
	Score float64
}

// ReciprocalRankFusion объединяет ранжированные списки от полнотекстового поиска (BM25)
// и векторного поиска (Dense Retrieval) по формуле RRF: Score = sum(1 / (k + rank))
func ReciprocalRankFusion(vectorResults, keywordResults []string, k float64) []SearchResultItem {
	if k <= 0 {
		k = 60.0 // Стандартная константа k в алгоритме Cormack et al.
	}

	scores := make(map[string]float64)

	// Ранжирование векторного поиска
	for rank, id := range vectorResults {
		scores[id] += 1.0 / (k + float64(rank+1))
	}

	// Ранжирование поиска по ключевым словам
	for rank, id := range keywordResults {
		scores[id] += 1.0 / (k + float64(rank+1))
	}

	var combined []SearchResultItem
	for id, score := range scores {
		combined = append(combined, SearchResultItem{DocID: id, Score: score})
	}

	// Сортировка по убыванию результирующего RRF скора
	sort.Slice(combined, func(i, j int) bool {
		return combined[i].Score > combined[j].Score
	})

	return combined
}

func main() {
	// Результаты векторного поиска (семантическое сходство)
	vectorDocs := []string{"doc_A", "doc_B", "doc_C", "doc_D"}
	// Результаты полнотекстового поиска (точное совпадение артикула/термина)
	keywordDocs := []string{"doc_C", "doc_E", "doc_A", "doc_F"}

	merged := ReciprocalRankFusion(vectorDocs, keywordDocs, 60.0)

	fmt.Println("=== Результаты гибридного поиска (Reciprocal Rank Fusion) ===")
	for i, item := range merged {
		fmt.Printf("%d. ID: %s, Скор RRF: %.5f\n", i+1, item.DocID, item.Score)
	}
}
'''
validate_go_code(code15, "Ex 15")
exercises.append({
    "num": 15,
    "title": "Семантический поиск с гибридной фильтрацией (Hybrid Search)",
    "task": "Спроектируйте алгоритм гибридного поиска (Hybrid Search) на базе Reciprocal Rank Fusion (RRF). Объедините результаты семантического векторного поиска pgvector и точного полнотекстового поиска PostgreSQL (tsvector/BM25) для устранения слепых зон чисто векторного поиска.",
    "theory": """Чистый векторный поиск обладает известным недостатком: он плохо находит **точные ключевые слова, артикулы, коды ошибок, имена переменных и сокращения** (например, `ERR_CONN_REFUSED_502` или `RFC-7519`), так как они могут отсутствовать в обучающем словаре модели эмбеддингов.
Классический полнотекстовый поиск (BM25, PostgreSQL `tsvector`) идеально ищет редкие ключевые слова, но совершенно бессилен перед синонимами и концептуальным описанием смысла.
**Гибридный поиск (Hybrid Search)** объединяет обе парадигмы с помощью алгоритма **Reciprocal Rank Fusion (RRF)**:
$$RRF\\_Score(d) = \\sum_{m \\in M} \\frac{1}{k + r_m(d)}$$
- $M$: множество поисковых систем (векторная + полнотекстовая).
- $r_m(d)$: позиция (ранг, начиная с 1) документа $d$ в выдаче системы $m$.
- $k$: константа сглаживания (эмпирически $k = 60$).
Документы, оказавшиеся высоко в обоих списках, получают максимальный синергетический скор и поднимаются на вершину выдачи.""",
    "step_by_step": [
        "Определите структуру `SearchResultItem` с идентификатором документа и скором.",
        "Реализуйте формулу RRF с итерацией по ранжированным спискам идентификаторов.",
        "Используйте `k = 60.0` для минимизации влияния единичных аномальных скачков ранга.",
        "Отсортируйте объединенный список по убыванию скора с помощью `sort.Slice`."
    ],
    "code_blocks": [code15],
    "under_the_hood": "Алгоритм RRF не требует нормализации сырых скоров косинусного сходства (0.0-1.0) и BM25 (0.0 - 50.0+), оперируя исключительно порядковыми рангами (индексами элементов в срезе). Это исключает проблему калибровки шкал различных поисковых движков.",
    "pitfalls": "Использование сложения сырых скоров `CosineSimilarity + BM25_Score` приведет к доминированию BM25, так как его значения могут достигать десятков, полностью перекрывая диапазон косинуса [0.0; 1.0].",
    "bigtech_interview": "Как реализовать гибридный поиск средствами одного SQL-запроса в PostgreSQL?\nОтвет: Через объединение двух CTE (Common Table Expressions) и FULL OUTER JOIN: первый CTE выполняет векторный поиск по HNSW индексу (`ORDER BY embedding <=> $1 LIMIT 50`), второй CTE выполняет полнотекстовый поиск через `ts_rank(tsv, query)`. Финальный SELECT производит расчет RRF скора `COALESCE(1.0/(60 + r1.rank), 0) + COALESCE(1.0/(60 + r2.rank), 0)` и возвращает Top-10 результатов."
})

with open('/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch99_p1.json', 'w', encoding='utf-8') as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Chapter 99 Part 1 generated: {len(exercises)} exercises.")
