# -*- coding: utf-8 -*-
"""
Chapter 87 Part 2: Exercises 26 to 50
Orchestration of Distributed Processes (Durable Execution) on Temporal.io in Go
"""

exercises = [
    {
        "num": 26,
        "title": "Мокирование Activities в тестах",
        "task": "В тестовом наборе `testsuite.WorkflowTestSuite` замените реальные Activity-функции на моки с помощью `env.OnActivity(ProcessPaymentActivity, mock.Anything, mock.Anything).Return(expectedResp, nil)`. Проверьте корректность бизнес-логики Workflow при имитации сетевых ошибок, таймаутов и успешных ответов внешнего платежного шлюза.",
        "theory": "При юнит-тестировании Workflow мы тестируем чистую логику оркестрации, ветвления и обработки ошибок, абстрагируясь от реальных баз данных и внешних HTTP API.\n\nПакет `go.temporal.io/sdk/testsuite` предоставляет глубокую интеграцию со стандартной библиотекой `github.com/stretchr/testify/mock`:\n- `env.OnActivity(ActivityFunc, mock.Anything...).Return(mockResult, nil)` позволяет замокать результат любой активности.\n- Можно симулировать возвращение кастомных ошибок, таких как `temporal.NewApplicationError('card expired', 'CARD_EXPIRED')`.\n- Можно эмулировать задержки выполнения и последовательные ответы для проверки ретраев: `.Return(nil, errTemporary).Once()` затем `.Return(respSuccess, nil)`.",
        "step_by_step": "1. Опишите активность `ChargePaymentActivity`.\n2. Напишите тестируемый `CheckoutWorkflow`.\n3. В тестовом методе настройте мок через `env.OnActivity` на возврат ошибки.\n4. Проверьте, что Workflow корректно перехватил ошибку и перевел статус заказа в `FAILED`.\n5. Напишите второй тестовый сценарий с успешной оплатой.",
        "code_blocks": [
            {
                "filename": "mock_test.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/suite"
	"go.temporal.io/sdk/testsuite"
	"go.temporal.io/sdk/workflow"
)

type PaymentReq struct {
	CardToken string
	Amount    int
}

func ChargePaymentActivity(ctx context.Context, req PaymentReq) (string, error) {
	// Реальный вызов Stripe/ЮKassa
	return "tx_real_123", nil
}

func CheckoutWorkflow(ctx workflow.Context, req PaymentReq) (string, error) {
	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 5 * time.Second,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var txID string
	err := workflow.ExecuteActivity(ctx, ChargePaymentActivity, req).Get(ctx, &txID)
	if err != nil {
		return "ORDER_PAYMENT_FAILED", err
	}

	return "ORDER_PAID: " + txID, nil
}

type CheckoutTestSuite struct {
	suite.Suite
	testsuite.WorkflowTestSuite
}

// Тест успешного списания с моком
func (s *CheckoutTestSuite) Test_Checkout_Success() {
	env := s.NewTestWorkflowEnvironment()

	// Настройка мока активности
	env.OnActivity(ChargePaymentActivity, mock.Anything, PaymentReq{CardToken: "tok_visa", Amount: 5000}).
		Return("tx_mock_999", nil)

	env.ExecuteWorkflow(CheckoutWorkflow, PaymentReq{CardToken: "tok_visa", Amount: 5000})

	s.True(env.IsWorkflowCompleted())
	s.NoError(env.GetWorkflowError())

	var result string
	s.NoError(env.GetWorkflowResult(&result))
	s.Equal("ORDER_PAID: tx_mock_999", result)
}

// Тест сбоя шлюза
func (s *CheckoutTestSuite) Test_Checkout_GatewayError() {
	env := s.NewTestWorkflowEnvironment()

	// Имитация ошибки шлюза
	env.OnActivity(ChargePaymentActivity, mock.Anything, mock.Anything).
		Return("", errors.New("gateway connection timeout"))

	env.ExecuteWorkflow(CheckoutWorkflow, PaymentReq{CardToken: "tok_bad", Amount: 1000})

	s.True(env.IsWorkflowCompleted())
	s.Error(env.GetWorkflowError())
}

func TestCheckoutSuite(t *testing.T) {
	suite.Run(t, new(CheckoutTestSuite))
}

func main() {}
"""
            }
        ],
        "under_the_hood": "Метод `env.OnActivity` регистрирует перехватчик (Mock Interceptor) в in-memory движке эмулятора. Когда код Workflow генерирует команду планирования задачи `ScheduleActivityTask`, эмулятор проверяет таблицу моков. Если зарегистрировано совпадение типов и параметров, эмулятор не помещает задачу в очередь воркера, а мгновенно создает псевдо-событие `ActivityTaskCompleted` или `ActivityTaskFailed` с указанным возвращаемым значением.",
        "pitfalls": "При проверке аргументов через `mock.MatchedBy` будьте аккуратны с указателями. Если в активность передается указатель на структуру, поля которой мутируются в коде, мок может вести себя непредсказуемо. Передавайте неизменяемые структуры по значению.",
        "interview_qa": "В: Как проверить в тесте, что определенная Activity НЕ вызывалась вовсе при заданных условиях?\nО: Вызовите `env.AssertNotCalled(t, \"ActivityName\", mock.Anything)` или проверьте вызовы через метод testify `mock.AssertNotCalled` после завершения исполнения Workflow."
    },
    {
        "num": 27,
        "title": "Распределенная трассировка и логирование через Interceptors",
        "task": "Подключите интерцепторы OpenTelemetry в клиент и воркер Temporal: `opentelemetry.NewTracingInterceptor()`. Убедитесь, что W3C Trace Context (traceparent, tracestate) прозрачно пробрасывается из входящего HTTP-запроса в родительский Workflow, а оттуда во все дочерние Activities, обеспечивая сквозную визуализацию пути запроса в Jaeger и Grafana Tempo.",
        "theory": "В распределенных системах критически важно иметь сквозную трассировку (Distributed Tracing): когда пользователь делает клик в веб-приложении, один и тот же `TraceID` должен связывать HTTP-шлюз, вызов Temporal Client, старт Workflow, исполнение пяти Activities на разных машинах и обращение к БД.\n\nTemporal SDK предоставляет мощный механизм интерцепторов (Interceptors):\n1. **Client Interceptor**: перехватывает вызовы `ExecuteWorkflow` и `SignalWorkflow`, считывает активный OTel Span из Go `context.Context` и упаковывает W3C заголовки в метаданные Temporal Headers.\n2. **Worker Interceptor**: при извлечении задачи из очереди достает OTel Span Context из метаданных, создает дочерний спан для Workflow Task или Activity и пробрасывает его в контекст выполнения функции.\n\nБлагодаря этому в Jaeger или Tempo видна идеальная иерархическая диаграмма со всеми задержками каждого шага.",
        "step_by_step": "1. Изучите пакет `go.temporal.io/sdk/contrib/opentelemetry`.\n2. Сконфигурируйте Tracing Interceptor через `interceptor.NewTracingInterceptor`.\n3. Передайте интерцептор в `client.Options`.\n4. Передайте интерцептор в `worker.Options`.\n5. Напишите код извлечения активного TraceID внутри Activity.",
        "code_blocks": [
            {
                "filename": "tracing.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.opentelemetry.io/otel/trace"
	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/contrib/opentelemetry"
	"go.temporal.io/sdk/interceptor"
	"go.temporal.io/sdk/worker"
	"go.temporal.io/sdk/workflow"
)

// TraceableActivity считывает активный SpanID из контекста.
func TraceableActivity(ctx context.Context, data string) (string, error) {
	// Извлекаем OTel спан, автоматически проброшенный интерцептором SDK
	span := trace.SpanFromContext(ctx)
	traceID := span.SpanContext().TraceID().String()
	spanID := span.SpanContext().SpanID().String()

	logger := activity.GetLogger(ctx)
	logger.Info("Activity исполняется в рамках распределенного спана",
		"trace_id", traceID,
		"span_id", spanID,
	)

	fmt.Printf(" [ACTIVITY] 📡 Обработка данных. OpenTelemetry TraceID: %s, SpanID: %s\n", traceID, spanID)
	return "PROCESSED: " + data, nil
}

func TraceableWorkflow(ctx workflow.Context, data string) (string, error) {
	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 5 * time.Second,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var res string
	err := workflow.ExecuteActivity(ctx, TraceableActivity, data).Get(ctx, &res)
	return res, err
}

// SetupTracingEnvironment демонстрирует инициализацию интерцепторов сквозной трассировки.
func SetupTracingEnvironment() (client.Client, worker.Worker, error) {
	// Создаем Tracing Interceptor
	tracingInterceptor, err := opentelemetry.NewTracingInterceptor(opentelemetry.TracerOptions{})
	if err != nil {
		return nil, nil, err
	}

	// Настройка клиента с интерцептором
	c, err := client.Dial(client.Options{
		HostPort:     "localhost:7233",
		Interceptors: []interceptor.ClientInterceptor{tracingInterceptor},
	})
	if err != nil {
		return nil, nil, err
	}

	// Настройка воркера с интерцептором
	w := worker.New(c, "tracing-tasks", worker.Options{
		Interceptors: []interceptor.WorkerInterceptor{tracingInterceptor},
	})

	w.RegisterWorkflow(TraceableWorkflow)
	w.RegisterActivity(TraceableActivity)

	return c, w, nil
}

func main() {
	fmt.Println("Демонстрация распределенной трассировки OpenTelemetry в Temporal SDK.")
}
"""
            }
        ],
        "under_the_hood": "Кластер Temporal ничего не знает о протоколе OpenTelemetry. SDK использует поле `Header` в gRPC сообщениях `WorkflowExecutionStartedRequest` и `PollActivityTaskQueueResponse`. Интерцептор сериализует заголовки W3C Trace Context (`traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`) в бинарные метаданные заголовка. При получении задачи воркер извлекает контекст и делает `tracer.Start(ctx, 'RunActivity: TraceableActivity')`.",
        "pitfalls": "Не создавайте новый корневой трейс внутри Activity (`tracer.Start(context.Background())`), иначе сквозная связь с родительским процессом будет потеряна! Всегда передавайте входящий `ctx` из первого аргумента Activity.",
        "interview_qa": "В: Создаются ли OTel-спаны во время детерминированного Replay старых событий?\nО: Нет! Интерцепторы Temporal SDK проверяют, находится ли рантайм в режиме воспроизведения (`env.IsReplaying()`). Во время Replay создание спанов и отправка телеметрии в Jaeger/Tempo автоматически блокируются, предотвращая искажение метрик реального трафика миллионами фантомных спанов."
    },
    {
        "num": 28,
        "title": "Сквозное шифрование полезной нагрузки (Custom DataConverter)",
        "task": "Политики безопасности и требования PCI-DSS/GDPR запрещают хранить персональные данные (номера паспортов, реквизиты карт) в открытом виде в базе данных кластера Temporal. Реализуйте кастомный `converter.DataConverter`, который прозрачно шифрует все аргументы и результаты функций алгоритмом AES-256-GCM на стороне воркера до отправки в кластер и расшифровывает их при получении.",
        "theory": "По умолчанию Temporal SDK сериализует аргументы и результаты функций в формат JSON или Protobuf и отправляет их в кластер по gRPC. Кластер сохраняет эти пейлоады в неизменяемом журнале событий в PostgreSQL / Cassandra.\n\nЕсли база данных кластера будет скомпрометирована или к ней получат доступ инженеры сопровождения инфраструктуры, незашифрованные ПДн клиентов окажутся уязвимы.\n\nАрхитектура безопасности Temporal решает это через **Custom DataConverter / PayloadCodec**:\n- Шифрование происходит ИСКЛЮЧИТЕЛЬНО на стороне доверенного воркера (Client-Side Encryption).\n- В базу данных кластера Temporal записываются только нечитаемые байты шифротекста (AES-256-GCM).\n- Сам кластер Temporal выступает в роли 'слепого брокера' — он надежно сохраняет события, не имея ключей дешифрования и не видя конфиденциальные данные.",
        "step_by_step": "1. Реализуйте структуру кодека `AESGCMCodec`, реализующую интерфейс `converter.PayloadCodec`.\n2. Реализуйте методы `Encode` (шифрование полезной нагрузки симметричным ключом AES-256) и `Decode`.\n3. Соберите кастомный DataConverter через `converter.NewCodecDataConverter`.\n4. Подключите DataConverter в `client.Options`.\n5. Убедитесь, что полезные данные в кластере зашифрованы.",
        "code_blocks": [
            {
                "filename": "encryption.go",
                "lang": "go",
                "code": r"""package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"fmt"
	"io"

	commonpb "go.temporal.io/api/common/v1"
	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/converter"
)

// AESGCMCodec реализует сквозное шифрование полезной нагрузки (PayloadCodec).
type AESGCMCodec struct {
	key []byte // 32 байта для AES-256
}

func NewAESGCMCodec(key []byte) *AESGCMCodec {
	return &AESGCMCodec{key: key}
}

// Encode шифрует срез Payload перед отправкой в кластер Temporal.
func (c *AESGCMCodec) Encode(payloads []*commonpb.Payload) ([]*commonpb.Payload, error) {
	result := make([]*commonpb.Payload, len(payloads))

	block, err := aes.NewCipher(c.key)
	if err != nil {
		return nil, err
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}

	for i, p := range payloads {
		// Сериализуем оригинальный Payload в байты
		rawBytes, err := p.Marshal()
		if err != nil {
			return nil, err
		}

		// Генерируем уникальный nonce для каждого шифрования
		nonce := make([]byte, gcm.NonceSize())
		if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
			return nil, err
		}

		// Шифруем данные
		ciphertext := gcm.Seal(nonce, nonce, rawBytes, nil)

		// Упаковываем в новый зашифрованный Payload
		result[i] = &commonpb.Payload{
			Metadata: map[string][]byte{
				"encoding": []byte("binary/encrypted-aes256-gcm"),
			},
			Data: ciphertext,
		}
	}
	return result, nil
}

// Decode расшифровывает Payload при получении воркером из кластера.
func (c *AESGCMCodec) Decode(payloads []*commonpb.Payload) ([]*commonpb.Payload, error) {
	result := make([]*commonpb.Payload, len(payloads))

	block, err := aes.NewCipher(c.key)
	if err != nil {
		return nil, err
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}

	for i, p := range payloads {
		if string(p.Metadata["encoding"]) != "binary/encrypted-aes256-gcm" {
			// Не зашифрованный пейлоад — пропускаем как есть
			result[i] = p
			continue
		}

		nonceSize := gcm.NonceSize()
		if len(p.Data) < nonceSize {
			return nil, fmt.Errorf("длина зашифрованных данных меньше размера nonce")
		}

		nonce, ciphertext := p.Data[:nonceSize], p.Data[nonceSize:]
		plaintext, err := gcm.Open(nil, nonce, ciphertext, nil)
		if err != nil {
			return nil, fmt.Errorf("ошибка расшифровки полезной нагрузки: %w", err)
		}

		var origPayload commonpb.Payload
		if err := origPayload.Unmarshal(plaintext); err != nil {
			return nil, err
		}
		result[i] = &origPayload
	}
	return result, nil
}

// SetupEncryptedClient демонстрирует инициализацию защищенного клиента Temporal.
func SetupEncryptedClient(secretKey32Bytes []byte) (client.Client, error) {
	codec := NewAESGCMCodec(secretKey32Bytes)

	// Оборачиваем стандартный DataConverter в кастомный кодек-конвертер
	encryptedDataConverter := converter.NewCodecDataConverter(
		converter.GetDefaultDataConverter(),
		codec,
	)

	return client.Dial(client.Options{
		HostPort:      "localhost:7233",
		DataConverter: encryptedDataConverter,
	})
}

func main() {
	fmt.Println("Сквозное шифрование PayloadCodec (AES-256-GCM) для защиты ПДн в Temporal успешно реализовано.")
}
"""
            }
        ],
        "under_the_hood": "Когда воркер отправляет `RespondWorkflowTaskCompleted` или клиент вызывает `ExecuteWorkflow`, SDK прогоняет все аргументы через цепочку кодеков `DataConverter.ToPayloads`. Кастомный `PayloadCodec.Encode` заменяет исходный JSON-пейлоад на зашифрованный блоб со специальным заголовком `encoding: binary/encrypted`. Сервер видит только непрозрачные байты, благодаря чему даже полный дамп БД кластера не приведет к утечке клиентских секретов.",
        "pitfalls": "Если один воркер настроен с кастомным `DataConverter`, а второй воркер подключен со стандартным без кодека — второй воркер не сможет прочитать входные аргументы и упадет с паникой десериализации. Конфигурация DataConverter обязана быть абсолютно идентичной на всех клиентах и воркерах периметра.",
        "interview_qa": "В: Если все пейлоады в базе кластера зашифрованы, как служба поддержки и разработчики могут просматривать историю процессов в Temporal Web UI?\nО: Для этого разворачивается защищенный корпоративный микросервис **Temporal Payload Codec Server**. Temporal Web UI настраивается на обращение к этому Codec Server: браузер инженера отправляет зашифрованные данные через прокси с корпоративным SSO токеном, Codec Server расшифровывает их доверенным ключом, и инженер видит красивый читаемый JSON прямо в браузере."
    },
    {
        "num": 29,
        "title": "Тюнинг производительности воркеров под HighLoad",
        "task": "Оптимизируйте конфигурацию воркера под высокие нагрузки (10 000+ задач в секунду): настройка `MaxConcurrentActivityExecutionSize`, `MaxConcurrentWorkflowTaskExecutionSize`, тюнинг кэша рабочих процессов `worker.SetStickyWorkflowCacheSize(10000)` и пула горутин. Объясните влияние Sticky Execution на снижение задержки исполнения задач.",
        "theory": "По умолчанию Temporal Worker сконфигурирован консервативно, чтобы безопасно работать на локальных машинах разработчиков. При переходе в высоконагруженный продакшен (HighLoad) параметры воркера требуют тонкой настройки под профиль нагрузок:\n\n1. **`MaxConcurrentWorkflowTaskExecutionSize`**:\n   - Максимальное число параллельно исполняемых задач Workflow на воркере (по умолчанию 1000). Регулирует нагрузку на CPU.\n\n2. **`MaxConcurrentActivityExecutionSize`**:\n   - Максимальное число параллельных Activities (по умолчанию 1000). Если активности I/O-bound (сетевые запросы), размер можно безопасно повышать до 5 000–10 000.\n\n3. **Sticky Execution & Sticky Workflow Cache**:\n   - Когда процесс выполняется, его стек и локальные переменные кэшируются в памяти воркера.\n   - Кластер старается направлять последующие задачи того же процесса на ТОТ ЖЕ САМЫЙ воркер (Sticky Task Queue).\n   - Это исключает необходимость заново проигрывать Replay всей истории при каждом шаге! Время отклика сокращается с 50 мс до 0.5 мс.",
        "step_by_step": "1. Сконфигурируйте размер Sticky-кэша через `worker.SetStickyWorkflowCacheSize`.\n2. Настройте параметры пула поллеров: `MaxConcurrentWorkflowTaskPollers` и `MaxConcurrentActivityTaskPollers`.\n3. Сбалансируйте лимиты параллелизма для CPU-bound и IO-bound нагрузок.\n4. Проанализируйте мониторинг потребления оперативной памяти.",
        "code_blocks": [
            {
                "filename": "tuning.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"log"

	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/worker"
)

// ConfigureHighLoadWorker демонстрирует промышленный тюнинг воркера под 10k RPS.
func ConfigureHighLoadWorker(c client.Client, taskQueue string) worker.Worker {
	// 1. Увеличиваем размер кэша долгоживущих процессов в памяти воркера.
	// 10 000 закэшированных экземпляров процессов дают почти мгновенный Sticky Replay!
	worker.SetStickyWorkflowCacheSize(10000)

	workerOptions := worker.Options{
		// 2. Параллелизм Workflow Tasks (CPU bound)
		MaxConcurrentWorkflowTaskExecutionSize: 2000,

		// 3. Параллелизм Activities (IO bound: HTTP, DB)
		MaxConcurrentActivityExecutionSize: 5000,

		// 4. Количество параллельных gRPC поллеров очередей к Matching Service.
		// Увеличение количества поллеров устраняет задержки ожидания при высоком входящем трафике.
		MaxConcurrentWorkflowTaskPollers: 8,
		MaxConcurrentActivityTaskPollers: 16,

		// 5. Ограничение скорости (Rate Limiting) воркера для защиты нижележащих систем
		// Не более 10 000 выполненных активностей в секунду на данный под
		WorkerActivitiesPerSecond: 10000,

		// 6. Отключение автодетерминированного кэша при нехватке памяти (опционально)
		DisableStickyExecution: false,
	}

	w := worker.New(c, taskQueue, workerOptions)
	fmt.Printf("🚀 Высоконагруженный воркер успешно сконфигурирован для очереди '%s'!\n", taskQueue)
	return w
}

func main() {
	c, err := client.Dial(client.Options{HostPort: "localhost:7233"})
	if err != nil {
		log.Fatalf("Ошибка подключения к кластеру: %v", err)
	}
	defer c.Close()

	w := ConfigureHighLoadWorker(c, "highload-order-queue")
	_ = w
	fmt.Println("Параметры тюнинга HighLoad воркера успешно проверены.")
}
"""
            }
        ],
        "under_the_hood": "Механизм **Sticky Execution** работает следующим образом: когда воркер завершает Workflow Task, он регистрирует в кластере временную персональную очередь задач `StickyTaskQueue`. Кластер направляет следующее событие этого процесса именно в персональную очередь воркера. Воркер находит состояние в памяти `cache.Lookup()` и продолжает выполнение без вычитки истории из базы данных и без повторного Replay! Если воркер не отвечает за 5 секунд (StickyScheduleToStartTimeout), кластер возвращает задачу в общую очередь.",
        "pitfalls": "Большой размер Sticky Cache (`SetStickyWorkflowCacheSize(100000)`) при тяжелых процессах с большими локальными переменными может привести к тому, что под выйдет за пределы K8s Memory Limit и будет уничтожен OOM-киллером ОС. Всегда рассчитывайте лимиты памяти контейнера (`Memory Limit = StickyCacheSize * AvgWorkflowMemorySize * 1.5`).",
        "interview_qa": "В: Как понять по метрикам Prometheus, эффективно ли работает Sticky Execution?\nО: Отслеживайте метрику `temporal_sticky_cache_hit_total` и `temporal_sticky_cache_miss_total`. В хорошо настроенном высоконагруженном кластере процент попадания в кэш (Cache Hit Ratio) должен составлять 90–98%. Если хит-рейт падает ниже 80%, значит размер кэша недостаточен или поды воркеров постоянно перезагружаются."
    },
    {
        "num": 30,
        "title": "Сквозной бизнес-процесс E-Commerce Order Fulfillment",
        "task": "Спроектируйте законченный комплексный рабочий процесс интернет-магазина: резервация товаров на складе -> списание платежа -> ожидание ручного подтверждения службой безопасности при подозрительной транзакции (Signal) -> отправка курьерской службой -> трекинг статуса доставки с таймерами -> начисление кэшбэка. Включите полную обработку сбоев, компенсации Саги и версионирование.",
        "theory": "Настоящая сила Temporal раскрывается в сквозных сквозных бизнес-процессах (End-to-End Orchestration). До появления Temporal такие системы строились на десятках сервисов, сотнях топиков Kafka, кронах и тяжелых базах данных, где расследование зависшего заказа занимало дни.\n\nВ этом упражнении мы объединяем все изученные фундаментальные паттерны в единый промышленный Workflow:\n1. Идемпотентные активности с таймаутами и RetryPolicy.\n2. Распределенная Сага (Saga Pattern) с гарантированным откатом шагов при ошибках.\n3. Human-in-the-Loop через детерминированный `workflow.Selector`.\n4. Долговечные таймеры `workflow.Sleep` для мониторинга курьерской доставки.\n5. Версионирование через `workflow.GetVersion`.\n6. Чтение статуса через синхронный Query API.",
        "step_by_step": "1. Опишите DTO заказа `OrderFulfillmentRequest` и `OrderStatus`.\n2. Реализуйте прямые и компенсирующие активности склада, банка, службы доставки.\n3. Спроектируйте Workflow, связывающий шаги в единый детерминированный сценарий.\n4. Добавьте проверку службы безопасности с сигналом `FraudApprovalSignal`.\n5. Добавьте мониторинг доставки и Query-хэндлер статуса.",
        "code_blocks": [
            {
                "filename": "order_fulfillment.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/workflow"
)

type OrderRequest struct {
	OrderID   string  `json:"order_id"`
	UserID    string  `json:"user_id"`
	Amount    float64 `json:"amount"`
	IsVIP     bool    `json:"is_vip"`
	Address   string  `json:"address"`
}

type OrderState struct {
	Status      string    `json:"status"`
	TrackingNum string    `json:"tracking_num"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// Активности
func ReserveStockAct(ctx context.Context, orderID string) error {
	fmt.Printf(" [WAREHOUSE] Товары заказа %s зарезервированы на складе.\n", orderID)
	return nil
}

func CancelStockAct(ctx context.Context, orderID string) error {
	fmt.Printf(" [WAREHOUSE] 🔄 Расформирование брони заказа %s.\n", orderID)
	return nil
}

func ChargeCardAct(ctx context.Context, orderID string, amount float64) (string, error) {
	fmt.Printf(" [BANK] Списание %.2f руб по заказу %s...\n", amount, orderID)
	return "PAY_SUCCESS_TXN", nil
}

func RefundCardAct(ctx context.Context, orderID string) error {
	fmt.Printf(" [BANK] 🔄 Возврат средств по заказу %s.\n", orderID)
	return nil
}

func DispatchCourierAct(ctx context.Context, orderID, address string) (string, error) {
	fmt.Printf(" [DELIVERY] Курьер назначен на адрес %s.\n", address)
	return "TRACK_RU_77492", nil
}

// ECommerceFulfillmentWorkflow — флагманский сквозной процесс интернет-магазина.
func ECommerceFulfillmentWorkflow(ctx workflow.Context, req OrderRequest) (state OrderState, err error) {
	logger := workflow.GetLogger(ctx)
	ao := workflow.ActivityOptions{StartToCloseTimeout: 10 * time.Second}
	ctx = workflow.WithActivityOptions(ctx, ao)

	state = OrderState{
		Status:    "PENDING",
		UpdatedAt: workflow.Now(ctx),
	}

	// Query хэндлер для мониторинга
	_ = workflow.SetQueryHandler(ctx, "getOrderState", func() (OrderState, error) {
		return state, nil
	})

	var compensations []func(ctx workflow.Context)

	// Гарантированный откат Саги
	defer func() {
		if err != nil {
			logger.Warn("Заказ завершился сбоем! Выполнение компенсаций Саги...")
			state.Status = "CANCELLED_FAILED"
			state.UpdatedAt = workflow.Now(ctx)

			cleanCtx, _ := workflow.NewDisconnectedContext(ctx)
			for i := len(compensations) - 1; i >= 0; i-- {
				compensations[i](cleanCtx)
			}
		}
	}()

	// 1. Резервация склада
	state.Status = "RESERVING_STOCK"
	if err = workflow.ExecuteActivity(ctx, ReserveStockAct, req.OrderID).Get(ctx, nil); err != nil {
		return state, err
	}
	compensations = append(compensations, func(c workflow.Context) {
		_ = workflow.ExecuteActivity(c, CancelStockAct, req.OrderID).Get(c, nil)
	})

	// 2. Списание оплаты
	state.Status = "CHARGING_PAYMENT"
	var txnID string
	if err = workflow.ExecuteActivity(ctx, ChargeCardAct, req.OrderID, req.Amount).Get(ctx, &txnID); err != nil {
		return state, err
	}
	compensations = append(compensations, func(c workflow.Context) {
		_ = workflow.ExecuteActivity(c, RefundCardAct, req.OrderID).Get(c, nil)
	})

	// 3. Проверка антифрода (Human-in-the-Loop при сумме > 500 000 руб)
	if req.Amount > 500_000 {
		state.Status = "AWAITING_FRAUD_CHECK"
		logger.Warn("Подозрительно крупная сумма! Ожидание ручной проверки антифрода (до 24 часов)...")

		fraudChan := workflow.GetSignalChannel(ctx, "FraudApprovalSignal")
		var isApproved bool
		signalReceived := false

		selector := workflow.NewSelector(ctx)
		selector.AddReceive(fraudChan, func(c workflow.ReceiveChannel, more bool) {
			c.Receive(ctx, &isApproved)
			signalReceived = true
		})
		selector.AddFuture(workflow.NewTimer(ctx, 24*time.Hour), func(f workflow.Future) {
			logger.Warn("Таймаут антифрод-проверки истек")
		})
		selector.Select(ctx)

		if !signalReceived || !isApproved {
			return state, fmt.Errorf("заказ отклонен службой безопасности")
		}
	}

	// 4. Отправка курьерской службой
	state.Status = "DISPATCHING_COURIER"
	if err = workflow.ExecuteActivity(ctx, DispatchCourierAct, req.OrderID, req.Address).Get(ctx, &state.TrackingNum); err != nil {
		return state, err
	}

	// 5. Ожидание доставки покупателю (в реальности может спать несколько дней)
	state.Status = "IN_TRANSIT"
	logger.Info("Заказ передан в доставку. Ожидание вручения клиенту...", "tracking", state.TrackingNum)
	_ = workflow.Sleep(ctx, 2*time.Second) // Имитация времени в пути

	state.Status = "DELIVERED_SUCCESSFULLY"
	state.UpdatedAt = workflow.Now(ctx)
	logger.Info("🎉 Заказ успешно выполнен в полном объеме!", "order_id", req.OrderID)
	return state, nil
}

func main() {
	fmt.Println("Сквозной процесс E-Commerce Order Fulfillment на Temporal успешно спроектирован.")
}
"""
            }
        ],
        "under_the_hood": "Этот Workflow объединяет распределенные транзакции в согласованный автомат. При падении сети на любом этапе (например, при вызове банка или курьера) состояние сохраняется в History Service. В случае возврата ошибки блок `defer` с `NewDisconnectedContext` раскручивает стек вызовов обратно, гарантируя отсутствие несогласованного состояния (зависших броней или списанных без товара денег).",
        "pitfalls": "Не забывайте очищать или сбрасывать переменные статуса перед выходом из defer, чтобы клиенты, опрашивающие Query `getOrderState`, не получали устаревший статус в процессе отката компенсаций.",
        "interview_qa": "В: Как спроектировать масштабируемость такого процесса под 100 000 заказов в час?\nО: Разделите очереди задач: активности склада на `warehouse-tasks`, платежи на `payment-tasks`, а курьеров на `logistics-tasks`. Масштабируйте воркеры независимо через Kubernetes HPA по метрике лага очередей задач Temporal Matching Service."
    },
    {
        "num": 31,
        "title": "Workflow Update API (Синхронная валидация и мутация состояния)",
        "task": "Изучите современный механизм Workflow Update, заменивший устаревший двухфазный шаблон Signal + Query. Реализуйте метод `workflow.SetUpdateHandler(ctx, 'updateShippingAddress', handler, validator)`: валидатор синхронно проверяет корректность нового адреса доставки и статус заказа, а хэндлер мутирует состояние процесса и возвращает клиенту результат за один сетевой round-trip.",
        "theory": "Исторически для изменения состояния Workflow извне использовался шаблон 'Signal + Query':\n1. Клиент посылал асинхронный Signal `client.SignalWorkflow` (операция без возврата результата).\n2. Затем клиент в цикле опрашивал Query `client.QueryWorkflow`, чтобы узнать, применился ли сигнал и не было ли ошибки валидации.\n\nЭто приводило к race conditions, лишним сетевым задержкам и усложнению клиентского кода.\n\n**Workflow Update API** объединил Signal и Query в единую атомарную синхронную операцию:\n- Клиент вызывает `client.UpdateWorkflow(...)` и **синхронно блокируется** в ожидании ответа.\n- **Validator**: функция проверки, исполняемая первой. Если данные некорректны (например, заказ уже передан курьеру и сменить адрес нельзя), валидатор возвращает ошибку Go, и запрос отклоняется мгновенно без записи в историю событий кластера!\n- **Handler**: функция мутации. Если валидация прошла успешно, кластер записывает событие `WorkflowExecutionUpdateAccepted`, хэндлер обновляет состояние процесса и возвращает типизированный результат прямо в HTTP-ответ клиенту.",
        "step_by_step": "1. Спроектируйте структуру запроса `AddressUpdateRequest` и ответа `AddressUpdateResponse`.\n2. Реализуйте функцию-валидатор `validateAddressUpdate`.\n3. Реализуйте функцию-хэндлер `handleAddressUpdate`.\n4. Зарегистрируйте Update Handler через `workflow.SetUpdateHandler` внутри Workflow.\n5. Напишите вызов `c.UpdateWorkflow` со стороны клиента.",
        "code_blocks": [
            {
                "filename": "workflow_update.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"time"

	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/workflow"
)

type AddressUpdateRequest struct {
	NewAddress string `json:"new_address"`
}

type AddressUpdateResponse struct {
	PreviousAddress string `json:"previous_address"`
	UpdatedAddress  string `json:"updated_address"`
	ConfirmedAt     time.Time `json:"confirmed_at"`
}

const UpdateAddressType = "updateShippingAddress"

// UpdatableOrderWorkflow демонстрирует работу Workflow Update API.
func UpdatableOrderWorkflow(ctx workflow.Context, initialAddress string) (string, error) {
	currentAddress := initialAddress
	isDispatched := false

	// Валидатор: вызывается ПЕРЕД фиксацией события в истории!
	validator := func(ctx workflow.Context, req AddressUpdateRequest) error {
		if isDispatched {
			return errors.New("невозможно изменить адрес: заказ уже передан курьеру")
		}
		if len(strings.TrimSpace(req.NewAddress)) < 5 {
			return errors.New("некорректный адрес доставки: слишком короткая строка")
		}
		return nil
	}

	// Хэндлер: выполняется только при успешной валидации
	handler := func(ctx workflow.Context, req AddressUpdateRequest) (AddressUpdateResponse, error) {
		prev := currentAddress
		currentAddress = req.NewAddress

		resp := AddressUpdateResponse{
			PreviousAddress: prev,
			UpdatedAddress:  currentAddress,
			ConfirmedAt:     workflow.Now(ctx),
		}
		return resp, nil
	}

	// Регистрация Update Handler
	err := workflow.SetUpdateHandlerWithOptions(
		ctx,
		UpdateAddressType,
		handler,
		workflow.UpdateHandlerOptions{Validator: validator},
	)
	if err != nil {
		return "", err
	}

	// Имитация ожидания сборки (в это время можно менять адрес)
	_ = workflow.Sleep(ctx, 5*time.Second)

	// Заказ отправлен курьеру: после этого момента валидатор будет отклонять изменения
	isDispatched = true

	return fmt.Sprintf("Заказ доставлен по адресу: %s", currentAddress), nil
}

// ClientUpdateCall демонстрирует синхронный вызов обновления клиентом.
func ClientUpdateCall(c client.Client, workflowID, newAddress string) (*AddressUpdateResponse, error) {
	handle, err := c.UpdateWorkflow(context.Background(), client.UpdateWorkflowOptions{
		WorkflowID:   workflowID,
		UpdateName:   UpdateAddressType,
		Args:         []interface{}{AddressUpdateRequest{NewAddress: newAddress}},
		WaitForStage: client.WorkflowUpdateStageCompleted, // Ждем полного выполнения и результата
	})
	if err != nil {
		return nil, fmt.Errorf("ошибка отправки update: %w", err)
	}

	var result AddressUpdateResponse
	if err := handle.Get(context.Background(), &result); err != nil {
		return nil, fmt.Errorf("валидация или хэндлер отклонили обновление: %w", err)
	}

	return &result, nil
}

func main() {
	fmt.Println("Демонстрация Workflow Update API: атомарная синхронная валидация и мутация.")
}
"""
            }
        ],
        "under_the_hood": "Кластер Temporal разделяет обработку Update на две фазы: фаза проверки (Validation) и фаза применения (Commit). Валидатор исполняется воркером спекулятивно. Если валидатор вернул ошибку, клиент сразу получает gRPC статус `InvalidArgument` или `FailedPrecondition`, а журнал истории в БД не увеличивается ни на байт! Если валидатор успешен, в историю записываются события `WorkflowExecutionUpdateAccepted` и `WorkflowExecutionUpdateCompleted`.",
        "pitfalls": "Внутри функции валидатора категорически запрещено выполнять мутации переменных Workflow или вызывать `workflow.ExecuteActivity`! Валидатор обязан быть чистой read-only функцией, проверяющей текущие переменные и входной аргумент.",
        "interview_qa": "В: В чем главное преимущество Update API перед связкой Signal + Query?\nО: Update API гарантирует строгую линеаризуемость (Read-Your-Own-Writes Consistency). При Signal + Query клиент мог отправить сигнал, но при немедленном вызове query попасть на отстающий воркер и получить устаревшее состояние. Update гарантирует атомарное применение мутации и немедленный синхронный возврат подтверждения за 1 round-trip."
    },
    {
        "num": 32,
        "title": "Temporal Schedule API (Управление регулярными расписаниями)",
        "task": "Настройте периодические рабочие процессы с помощью Temporal Schedule Client: создайте расписание запуска биллинга (`client.ScheduleClient().Create(ctx, options)`), настройте спецификации `ScheduleSpec` (cron-выражения, интервалы), политики перекрытия `ScheduleOverlapPolicySkip` (пропуск при незавершенном предыдущем запуске) и выполните ручной запуск пропущенных интервалов (Backfill).",
        "theory": "Исторически для периодических задач использовались классические Linux crontab или внешние планировщики (Kubernetes CronJob). Однако в распределенных системах традиционный cron страдает фатальными недостатками: потеря задач при падении пода, отсутствие контроля перекрытия (Overlap), невозможность запаузить процесс или сделать безопасный догон пропущенных запусков (Backfill).\n\n**Temporal Schedule API** — первоклассный механизм управления расписаниями на уровне кластера:\n1. **Расписание живет в кластере**: Schedule сохраняется как устойчивая сущность в БД кластера и работает автономно.\n2. **Управление политиками перекрытия (Overlap Policy)**:\n   - `ScheduleOverlapPolicySkip`: пропустить новый запуск, если предыдущий еще работает.\n   - `ScheduleOverlapPolicyBufferOne`: поставить в очередь один следующий запуск.\n   - `ScheduleOverlapPolicyCancelOther`: отменить старый процесс и запустить свежий.\n3. **Backfill**: возможность в один вызов API запустить выполнение всех пропущенных запусков за прошлый месяц.",
        "step_by_step": "1. Спроектируйте структуру расписания через `client.ScheduleOptions`.\n2. Настройте спецификацию `client.ScheduleSpec` с интервалом запуска раз в сутки.\n3. Установите политику `ScheduleOverlapPolicySkip`.\n4. Продемонстрируйте создание расписания через `c.ScheduleClient().Create`.\n5. Покажите выполнение Backfill за заданный диапазон дат.",
        "code_blocks": [
            {
                "filename": "schedules.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/api/enums/v1"
	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/workflow"
)

func DailyBillingWorkflow(ctx workflow.Context) error {
	logger := workflow.GetLogger(ctx)
	logger.Info("Выполнение регламентного ежедневного биллинга клиентов...")
	return nil
}

// SetupBillingSchedule создает и настраивает расписание в кластере Temporal.
func SetupBillingSchedule(c client.Client, scheduleID string) error {
	scheduleClient := c.ScheduleClient()

	// Настройка расписания
	options := client.ScheduleOptions{
		ID: scheduleID,
		Spec: client.ScheduleSpec{
			// Запуск каждый день в 02:00 UTC
			CronExpressions: []string{"0 2 * * *"},
		},
		Action: &client.ScheduleWorkflowAction{
			Workflow:  DailyBillingWorkflow,
			TaskQueue: "billing-schedule-queue",
		},
		// Если вчерашний биллинг еще работает — пропускаем новый запуск!
		Overlap: enums.SCHEDULE_OVERLAP_POLICY_SKIP,
	}

	scheduleHandle, err := scheduleClient.Create(context.Background(), options)
	if err != nil {
		return fmt.Errorf("ошибка создания расписания: %w", err)
	}

	fmt.Printf(" [SCHEDULE] Расписание '%s' успешно зарегистрировано в кластере!\n", scheduleHandle.GetID())

	// Демонстрация Backfill: ручной запуск пропущенных интервалов (например, за время аварии)
	backfillPeriod := client.ScheduleBackfillOptions{
		Backfill: []client.ScheduleBackfill{
			{
				StartTime: time.Now().AddDate(0, 0, -3), // 3 дня назад
				EndTime:   time.Now().AddDate(0, 0, -1), // вчера
				Overlap:   enums.SCHEDULE_OVERLAP_POLICY_BUFFER_ALL,
			},
		},
	}

	err = scheduleHandle.Backfill(context.Background(), backfillPeriod)
	if err != nil {
		return fmt.Errorf("ошибка выполнения Backfill: %w", err)
	}

	fmt.Println(" [SCHEDULE] Backfill успешно запущен для 3 пропущенных дней.")
	return nil
}

func main() {
	fmt.Println("Демонстрация Temporal Schedule API и механизма Backfill.")
}
"""
            }
        ],
        "under_the_hood": "Расписания в Temporal реализованы как внутренние системные Workflow внутри пространства имен. Сервер Temporal самостоятельно отслеживает cron-выражения и по наступлении времени инициирует создание клиентских процессов через команду `StartWorkflowExecution`. Благодаря этому расписания обладают такой же 100% отказоустойчивостью и сохранением истории, как и любые пользовательские процессы.",
        "pitfalls": "Не создавайте расписания внутри функций Workflow. Расписания настраиваются один раз административным кодом инициализации (migration runner) или через CLI утилиту `temporal schedule create`.",
        "interview_qa": "В: Как временно приостановить расписание на время технических работ в базе данных?\nО: Вызовом метода `scheduleHandle.Pause(ctx, client.SchedulePauseOptions{Note: \"Технические работы по апгрейду PostgreSQL\"})`. Кластер перестанет инициировать новые запуски. После завершения работ вызов `scheduleHandle.Unpause(ctx, ...)` возобновит работу расписания."
    },
    {
        "num": 33,
        "title": "Dynamic Workflows и Dynamic Activities",
        "task": "Реализуйте универсальные динамические обработчики через `workflow.RegisterDynamic` и `activity.RegisterDynamic`. Покажите, как перехватывать вызовы процессов и активностей с именами, неизвестными на этапе компиляции, извлекать метаданные из `EncodedValues` и динамически маршрутизировать задачи, создавая платформу для выполнения пользовательских no-code/low-code сценариев.",
        "theory": "Обычно в Temporal все Workflow и Activity жестко типизированы и регистрируются статически по имени функции Go (`w.RegisterWorkflow(MyFunc)`).\n\nОднако при создании универсальных платформ оркестрации (PaaS, no-code конструкторы процессов, динамические ETL конвейеры) список типов процессов неизвестен во время компиляции бинарника воркера.\n\nДля таких задач Temporal SDK предоставляет **Dynamic Workflows & Activities**:\n- Функция регистрируется через `w.RegisterWorkflowWithOptions(DynamicWorkflowHandler, workflow.RegisterOptions{Dynamic: true})`.\n- Любой вызов процесса с неизвестным именем перехватывается динамическим обработчиком.\n- Тип вызванного процесса извлекается через `workflow.GetInfo(ctx).WorkflowType.Name`.\n- Аргументы извлекаются динамически из контейнера `workflow.EncodedValues`.",
        "step_by_step": "1. Реализуйте функцию `DynamicWorkflowHandler(ctx workflow.Context, encArgs *workflow.EncodedValues)`.\n2. Извлеките имя вызванного типа процесса через `workflow.GetInfo(ctx)`.\n3. Реализуйте динамический диспетчер по внутреннему DSL.\n4. Зарегистрируйте динамический воркер.\n5. Продемонстрируйте исполнение произвольного сценария.",
        "code_blocks": [
            {
                "filename": "dynamic.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/workflow"
)

// DynamicActivityHandler перехватывает вызовы любых неизвестных активностей.
func DynamicActivityHandler(ctx context.Context, args *activity.EncodedValues) (string, error) {
	info := activity.GetInfo(ctx)
	logger := activity.GetLogger(ctx)

	logger.Info("Вызов динамической активности", "activity_name", info.ActivityType.Name)

	var payload string
	if err := args.Get(&payload); err != nil {
		return "", err
	}

	fmt.Printf(" [DYNAMIC ACTIVITY] Исполнение операции '%s' с аргументом: %s\n",
		info.ActivityType.Name, payload)

	return fmt.Sprintf("Executed dynamic action '%s' with payload '%s'", info.ActivityType.Name, payload), nil
}

// DynamicWorkflowHandler перехватывает запуск любых динамических сценариев.
func DynamicWorkflowHandler(ctx workflow.Context, args *workflow.EncodedValues) (string, error) {
	info := workflow.GetInfo(ctx)
	logger := workflow.GetLogger(ctx)

	workflowName := info.WorkflowType.Name
	logger.Info("Запуск динамического процесса", "workflow_name", workflowName)

	ao := workflow.ActivityOptions{StartToCloseTimeout: 10 * time.Second}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var input string
	if err := args.Get(&input); err != nil {
		return "", err
	}

	// Динамический вызов активности по строковому имени
	var actResult string
	dynamicActName := "execute_user_script"
	err := workflow.ExecuteActivity(ctx, dynamicActName, input).Get(ctx, &actResult)
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("DynamicWorkflow [%s] finished: %s", workflowName, actResult), nil
}

func main() {
	fmt.Println("Демонстрация Dynamic Workflows & Activities для low-code/no-code платформ.")
}
"""
            }
        ],
        "under_the_hood": "Внутри структуры воркера есть две таблицы маппинга: `workflows map[string]interface{}` и указатель `dynamicWorkflow interface{}`. Когда Matching Service присылает воркеру задачу с именем `WorkflowType = 'custom_dsl_pipeline_44'`, воркер ищет имя в точной таблице. Если имя не найдено, но зарегистрирован динамический обработчик, задача передается в него, а аргументы упаковываются в `EncodedValues` без предварительной строгой десериализации.",
        "pitfalls": "Динамические Workflow обязаны так же строго подчиняться золотому правилу детерминизма! Любая интерпретация динамического скрипта (Lua, Python, JSON-DSL) внутри динамического Workflow обязана быть абсолютно детерминированной при Replay.",
        "interview_qa": "В: Как реализовать no-code систему автоматизации (аналог Zapier/Make) поверх Temporal?\nО: Пользователь в UI собирает граф шагов (JSON). Бэкенд сохраняет JSON в БД и запускает `DynamicWorkflow`, передавая JSON графа в аргументы. Внутри динамического процесса цикл обходит узлы графа и детерминированно запускает соответствующие `DynamicActivities` (HTTP Webhook, Telegram Alert, Google Sheets Update)."
    },
    {
        "num": 34,
        "title": "Nexus RPC: Межнеймспейсное и межкластерное взаимодействие",
        "task": "Спроектируйте архитектуру взаимодействия между микросервисами в разных неймспейсах и кластерах Temporal с помощью Nexus RPC: регистрация операций Nexus Operation Handler, асинхронный вызов долгих внешних процессов через стандартный контракт Temporal и отслеживание статуса без необходимости предоставления прямого сетевого доступа к внутренней базе данных.",
        "theory": "В крупных корпорациях сервисы разделены по изолированным пространствам имен (Namespaces), разным Kubernetes-кластерам и даже разным регионам (Multi-Cluster / Cross-Account).\n\nТрадиционные способы интеграции между разными неймспейсами (прямые вызовы через Temporal Client или очереди Kafka) нарушают границы изоляции и требуют сложных сетевых доступов.\n\n**Temporal Nexus** — это новый стандарт межсервисного взаимодействия поверх Temporal:\n1. Сервис-провайдер регистрирует операцию Nexus (Nexus Operation Handler) с четким контрактом ввода-вывода.\n2. Сервис-потребитель вызывает внешнюю операцию прямо из своего Workflow через `workflow.ExecuteNexusOperation`.\n3. Nexus автоматически координирует асинхронное долгоживущее выполнение: отмену, передачу результата, трансляцию контекста безопасности через защищенный шлюз кластера.",
        "step_by_step": "1. Изучите архитектурные контракты Temporal Nexus.\n2. Опишите интерфейс Nexus Operation для внешней проверки комплаенса.\n3. Реализуйте регистрацию обработчика операций на стороне провайдера.\n4. Напишите код вызова Nexus Operation из вызывающего Workflow.\n5. Продемонстрируйте безопасную межнеймспейсную оркестрацию.",
        "code_blocks": [
            {
                "filename": "nexus_demo.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/workflow"
)

type ComplianceCheckInput struct {
	EntityID   string `json:"entity_id"`
	CountryISO string `json:"country_iso"`
}

type ComplianceCheckOutput struct {
	Approved bool   `json:"approved"`
	RiskTier string `json:"risk_tier"`
}

// CallerWorkflow демонстрирует вызов внешней Nexus-операции из изолированного процесса.
func CallerWorkflow(ctx workflow.Context, entityID string) (string, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Вызов внешней Nexus-операции в изолированном банковском контуре...")

	input := ComplianceCheckInput{
		EntityID:   entityID,
		CountryISO: "RU",
	}

	// Nexus вызов настраивается с таймаутами выполнения
	// В реальном SDK используется workflow.ExecuteNexusOperation
	logger.Info("Отправка асинхронного запроса через Nexus Gateway...", "input", input)

	// Имитация детерминированного ожидания ответа внешнего контура
	_ = workflow.Sleep(ctx, 1*time.Second)

	output := ComplianceCheckOutput{
		Approved: true,
		RiskTier: "LOW",
	}

	logger.Info("Nexus-операция успешно завершена", "approved", output.Approved, "tier", output.RiskTier)
	return fmt.Sprintf("ENTITY_%s_VERIFIED_RISK_%s", entityID, output.RiskTier), nil
}

func main() {
	fmt.Println("Архитектура Temporal Nexus для безопасной межкластерной и межнеймспейсной оркестрации.")
}
"""
            }
        ],
        "under_the_hood": "Temporal Nexus использует открытую спецификацию Nexus RPC поверх HTTP/2. Кластер выступает в роли защищенного доверенного роутера. Вызывающий Workflow получает долговечный `NexusOperationFuture`. Сервер провайдера получает запрос, может запустить внутренний закрытый Workflow и по завершении отправить ответ через Nexus Callback API. Это полностью устраняет необходимость открывать прямой сетевой доступ между разными закрытыми периметрами.",
        "pitfalls": "Nexus предназначен для асинхронных операций с четкими бизнес-границами команд. Не используйте Nexus для ультра-высокочастотных мелких операций с микросекундной латентностью.",
        "interview_qa": "В: Чем Temporal Nexus принципиально отличается от обычного gRPC вызова из Activity?\nО: Обычный gRPC вызов из Activity привязан к одному TCP соединению и ограничен таймаутом сокета. Если операция длится 2 недели (например, ручной комплаенс-аудит регулятором), обычный HTTP/gRPC упадет по таймауту. Nexus операция — долговечная (Durable): она может длиться недели, корректно передает отмену процесса и не держит открытых соединений."
    },
    {
        "num": 35,
        "title": "Worker Versioning и Build IDs (Детерминизм без Patching)",
        "task": "Откажитесь от ручного добавления вызовов `workflow.GetVersion` в кодовую базу в пользу современной системы версионирования воркеров на базе Build ID. Настройте регистрацию воркеров с указанием версии сборки (`worker.Options{BuildID: 'v1.2.0', UseBuildIDForVersioning: true}`), настройте правила маршрутизации в кластере Temporal, направляя новые запуски на последнюю версию, а активные Workflow оставляя на старых воркерах.",
        "theory": "Исторически версионирование процессов через `workflow.GetVersion` требовало ручной модификации кода, засоряя кодовую базу сотнями устаревших `if version == ...` условий, которые страшно удалять.\n\n**Worker-Based Versioning (на базе Build ID)** — революция в деплое Temporal:\n1. Код пишется без единого вызова `GetVersion`!\n2. При сборке Docker-образа компилятор передает хэш коммита или тег релиза в качестве `BuildID` (например, `git-sha-7a91bf4`).\n3. Воркер регистрируется с этим `BuildID` и флагом `UseBuildIDForVersioning: true`.\n4. Кластер Temporal через набор правил совместимости (Target / Compatible Rules) знает, какие версии кода совместимы между собой.\n5. Старые процессы автоматически продолжают исполняться на старых подах до завершения, а все новые запуски направляются на новые поды!",
        "step_by_step": "1. Сконфигурируйте `worker.Options` с полями `BuildID` и `UseBuildIDForVersioning`.\n2. Напишите Workflow новой версии без вызовов `GetVersion`.\n3. Продемонстрируйте вызовы API клиента для назначения версии по умолчанию (Set Default Build ID).\n4. Объясните алгоритм безопасного Blue-Green деплоя.",
        "code_blocks": [
            {
                "filename": "worker_versioning.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"log"

	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/worker"
	"go.temporal.io/sdk/workflow"
)

func ModernPaymentWorkflow(ctx workflow.Context, orderID string) (string, error) {
	// Чистый код БЕЗ GetVersion!
	logger := workflow.GetLogger(ctx)
	logger.Info("Исполнение платежа на современной версии воркера", "order_id", orderID)
	return "PAID_V2_CLEAN", nil
}

// StartVersionedWorker запускает воркер с явной фиксацией BuildID сборки.
func StartVersionedWorker(c client.Client, buildID string) worker.Worker {
	taskQueue := "versioned-payment-queue"

	options := worker.Options{
		// Уникальный идентификатор сборки (Git SHA / Docker Tag)
		BuildID:                 buildID,
		UseBuildIDForVersioning: true,
	}

	w := worker.New(c, taskQueue, options)
	w.RegisterWorkflow(ModernPaymentWorkflow)

	fmt.Printf("🚀 Воркер запущен с BuildID '%s' на очереди '%s'!\n", buildID, taskQueue)
	return w
}

// PromoteBuildIDToDefault переключает трафик новых процессов на свежую версию воркера.
func PromoteBuildIDToDefault(c client.Client, taskQueue, newBuildID string) error {
	// В реальном продакшене вызывается через CLI:
	// temporal task-queue versioning update-build-id-compatibility --task-queue <q> --build-id <id>
	fmt.Printf(" [DEPLOY] Назначение BuildID '%s' версией по умолчанию для новых запусков в очереди '%s'\n",
		newBuildID, taskQueue)
	return nil
}

func main() {
	c, err := client.Dial(client.Options{HostPort: "localhost:7233"})
	if err != nil {
		log.Fatalf("Ошибка подключения: %v", err)
	}
	defer c.Close()

	currentGitSHA := "release-v2.4.1"
	w := StartVersionedWorker(c, currentGitSHA)
	_ = w
	_ = PromoteBuildIDToDefault(c, "versioned-payment-queue", currentGitSHA)
}
"""
            }
        ],
        "under_the_hood": "Matching Service кластера сопоставляет Build ID задачи с правилами совместимости очереди задач. Если запущенный процесс начался на воркере с Build ID `v1.0.0`, кластер будет направлять его задачи только на воркеры с `v1.0.0` (или совместимые с ним). Новые запуски направляются исключительно на версию, помеченную как `Default`. Когда старых процессов не останется, поды со старым Build ID удаляются из Kubernetes.",
        "pitfalls": "Если перед деплоем новой версии с несовместимым изменением кода вы забудете добавить правило версионирования в кластер, воркер с новым Build ID попытается выполнить старую задачу и кластер заблокирует ее во избежание сбоя.",
        "interview_qa": "В: Чем версионирование на базе Build ID лучше классического Patching (GetVersion)?\nО: Build ID оставляет код идеально чистым: разработчикам больше не нужно писать запутанные ветвления `if GetVersion()`, помнить идентификаторы патчей и проводить мучительный рефакторинг по очистке старых веток. Вся ответственность за версионирование переносится на уровень инфраструктуры деплоя (CI/CD)."
    },
    {
        "num": 36,
        "title": "Custom Search Attributes и расширенный поиск через Elasticsearch",
        "task": "Добавьте кастомные поисковые атрибуты в Workflow: зарегистрируйте атрибуты `AccountType` (Keyword), `Tier` (Int) и `IsVIP` (Bool). Реализуйте динамическое обновление атрибутов в ходе исполнения процесса с помощью `workflow.UpsertSearchAttributes`. Выполните поиск и фильтрацию активных процессов через Temporal Client API с использованием SQL-подобных запросов (`WorkflowType = 'Billing' AND IsVIP = true`).",
        "theory": "В кластере с миллионами процессов стандартного поиска по `WorkflowID` недостаточно. Бизнесу и поддержке необходимо искать процессы по произвольным критериям:\n- 'Найти все заказы клиента X за вчера, находящиеся в статусе AWAITING_PAYMENT'.\n- 'Найти все зависшие биллинги с тарифом Enterprise'.\n\nДля этого Temporal интегрируется с **Elasticsearch / OpenSearch** через механизм **Search Attributes**:\n1. В кластере регистрируются типизированные атрибуты (Keyword, Int, Double, Bool, Datetime, Text).\n2. При старте процесса или прямо в процессе его выполнения через `workflow.UpsertSearchAttributes` атрибуты обновляются.\n3. Кластер автоматически индексирует их в Elasticsearch.\n4. Любой сервис может выполнить быстрый поиск (List / Count) через SQL-подобный синтаксис Temporal Visibility.",
        "step_by_step": "1. Сформируйте карту поисковых атрибутов через `temporal.SearchAttributeKey`.\n2. Передайте начальные Search Attributes при запуске Workflow.\n3. В процессе выполнения обновите атрибуты через `workflow.UpsertSearchAttributes`.\n4. Напишите код запроса фильтрации `client.ListWorkflowExecutions` по условию.",
        "code_blocks": [
            {
                "filename": "search_attributes.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
)

// Определение ключей кастомных поисковых атрибутов
var (
	SearchAttrAccountType = temporal.NewSearchAttributeKeyKeyword("AccountType")
	SearchAttrTier        = temporal.NewSearchAttributeKeyInt64("Tier")
	SearchAttrIsVIP       = temporal.NewSearchAttributeKeyBool("IsVIP")
)

// SearchableWorkflow демонстрирует динамическое обновление поисковых атрибутов.
func SearchableWorkflow(ctx workflow.Context, isVip bool) error {
	logger := workflow.GetLogger(ctx)

	// Динамическое обновление Search Attributes прямо в процессе исполнения!
	err := workflow.UpsertTypedSearchAttributes(
		ctx,
		SearchAttrAccountType.ValueSet("Enterprise"),
		SearchAttrTier.ValueSet(3),
		SearchAttrIsVIP.ValueSet(isVip),
	)
	if err != nil {
		logger.Error("Ошибка обновления Search Attributes", "error", err)
		return err
	}

	logger.Info("Search Attributes успешно проиндексированы в Elasticsearch")

	// Имитация полезной работы
	_ = workflow.Sleep(ctx, 2*time.Second)

	return nil
}

// FindVipBillingWorkflows ищет активные VIP процессы через Visibility API.
func FindVipBillingWorkflows(c client.Client) error {
	query := "WorkflowType = 'SearchableWorkflow' AND IsVIP = true AND ExecutionStatus = 'Running'"
	fmt.Printf(" [SEARCH] Выполнение поиска в кластере по запросу: %s\n", query)

	request := &client.ListWorkflowExecutionsRequest{
		Query: query,
	}

	resp, err := c.ListWorkflow(context.Background(), request)
	if err != nil {
		return fmt.Errorf("ошибка поиска в Elasticsearch кластера: %w", err)
	}

	for _, execution := range resp.Executions {
		fmt.Printf(" [FOUND] Найден процесс: WorkflowID=%s, RunID=%s\n",
			execution.Execution.WorkflowId, execution.Execution.RunId)
	}

	return nil
}

func main() {
	fmt.Println("Демонстрация кастомных Search Attributes и Visibility API в Temporal.")
}
"""
            }
        ],
        "under_the_hood": "Когда вызывается `UpsertSearchAttributes`, воркер передает новые значения атрибутов в команду `WorkflowTaskCompleted`. History Service асинхронно записывает событие в Visibility Queue кластера. Внутренний Visibility Processor вычитывает эту очередь и отправляет bulk-запрос в индекс Elasticsearch. В течение долей секунды процесс становится доступен для фильтрации в Web UI и Client API.",
        "pitfalls": "Кастомные атрибуты должны быть предварительно зарегистрированы в кластере администратором через `temporal operator search-attribute create`. Попытка записать незарегистрированный атрибут вызовет ошибку `WorkflowTaskFailed`.",
        "interview_qa": "В: Чем отличается атрибут типа Keyword от типа Text в Search Attributes?\nО: `Keyword` индексируется строго как точное совпадение строки (exact match, регистрозависимо, без токенизации) — идеален для ID, статусов, перечислений. `Text` индексируется с использованием полнотекстового анализатора (tokenization, stemming) и поддерживает нечеткий поиск через `LIKE` или совпадение по подстроке."
    },
    {
        "num": 37,
        "title": "Temporal Batch Operations: Массовое управление процессами",
        "task": "Разработайте утилиту на Go для выполнения массовых операций над сотнями тысяч активных процессов: создание задания `client.WorkflowClient.StartBatchOperation` для массовой отправки сигналов об изменении тарифного плана, массовой отмены (Cancellation) или принудительного перезапуска сбойных инстансов по поисковому критерию Search Attributes.",
        "theory": "В крупных сервисах возникают ситуации, когда необходимо выполнить действие сразу над десятками тысяч работающих процессов:\n- Внешний платежный шлюз поменял URL: нужно послать сигнал во все 50 000 процессов заказов.\n- Обнаружена ошибка в старой версии Workflow: нужно массово отменить (Terminate/Cancel) все зависшие процессы.\n- Изменился регламент: нужно массово сбросить процессы до контрольной точки (Reset).\n\nЗапускать в цикле `for` 50 000 индивидуальных вызовов `client.SignalWorkflow` недопустимо — это перегрузит сеть и займет часы. Для этого Temporal предоставляет **Batch Operations API**: кластер принимает один поисковый запрос (Visibility Query), сам находит подходящие процессы и массово применяет операцию параллельно внутри ядра кластера.",
        "step_by_step": "1. Сформируйте поисковый запрос (например, `ExecutionStatus = 'Running' AND Tier = 1`).\n2. Настройте параметры массовой операции отмены или отправки сигнала.\n3. Инициируйте запуск Batch Job через клиентский вызов.\n4. Реализуйте мониторинг прогресса выполнения задания (Check Batch Status).",
        "code_blocks": [
            {
                "filename": "batch_operations.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/api/batch/v1"
	"go.temporal.io/api/workflowservice/v1"
	"go.temporal.io/sdk/client"
)

// StartMassCancellationJob запускает серверную пакетную отмену зависших процессов.
func StartMassCancellationJob(c client.Client, reason string) (string, error) {
	query := "WorkflowType = 'LegacyOrderWorkflow' AND ExecutionStatus = 'Running'"
	jobID := fmt.Sprintf("batch-cancel-%d", time.Now().Unix())

	req := &workflowservice.StartBatchOperationRequest{
		Namespace: "default",
		JobId:     jobID,
		Reason:    reason,
		VisibilityQuery: query,
		Operation: &workflowservice.StartBatchOperationRequest_CancellationOperation{
			CancellationOperation: &batch.BatchOperationCancellation{
				Identity: "admin-sre-tool",
			},
		},
	}

	// Отправка запроса на старт пакетной операции в кластер
	_, err := c.WorkflowService().StartBatchOperation(context.Background(), req)
	if err != nil {
		return "", fmt.Errorf("ошибка запуска Batch операции: %w", err)
	}

	fmt.Printf(" [BATCH ENGINE] 🚀 Пакетная операция '%s' успешно запущена на сервере!\n", jobID)
	fmt.Printf(" [BATCH ENGINE] Критерий выборки: %s\n", query)
	return jobID, nil
}

// CheckBatchJobStatus опрашивает прогресс серверной операции.
func CheckBatchJobStatus(c client.Client, jobID string) error {
	req := &workflowservice.DescribeBatchOperationRequest{
		Namespace: "default",
		JobId:     jobID,
	}

	resp, err := c.WorkflowService().DescribeBatchOperation(context.Background(), req)
	if err != nil {
		return err
	}

	fmt.Printf(" [BATCH STATUS] Статус: %s | Обработано: %d | Ошибок: %d\n",
		resp.State.String(), resp.GetState(), len(resp.Reason))

	return nil
}

func main() {
	fmt.Println("Демонстрация Temporal Batch Operations для высокопроизводительного массового управления.")
}
"""
            }
        ],
        "under_the_hood": "Пакетная операция исполняется системным внутренним Worker Service самого кластера Temporal. Он постранично считывает идентификаторы из Elasticsearch по Visibility Query и распределяет команды отмены/сигналов по шардам History Service с контролируемым темпом (Rate Limiting), предотвращая деградацию СУБД.",
        "pitfalls": "Перед запуском массовой операции всегда проверяйте ваш поисковый запрос через команду `temporal workflow list --query '...'`. Ошибка в условии (например, забытый фильтр `WorkflowType`) может случайно отменить критические финансовые процессы всей компании!",
        "interview_qa": "В: Какие типы пакетных операций (Batch Operations) поддерживает Temporal из коробки?\nО: Temporal поддерживает: 1) `Cancel` (вежливая отмена), 2) `Terminate` (принудительное уничтожение), 3) `Signal` (массовая отправка события), 4) `Reset` (откат процессов к первому шагу WorkflowTaskStarted для устранения багов новой версии)."
    },
    {
        "num": 38,
        "title": "Activity Execution Heartbeat с сохранением прогресса (Checkpoints)",
        "task": "Спроектируйте долгоживущую Activity по пакетной обработке терабайтного CSV-файла: воркер каждые несколько секунд отправляет контрольные сигналы жизнедеятельности `activity.RecordHeartbeat(ctx, currentOffset)`. Продемонстрируйте, как при аварийном падении узла воркера новая попытка (retry attempt) извлекает последнее зафиксированное смещение через `activity.GetHeartbeatDetails` и возобновляет обработку без потерь и повторов.",
        "theory": "При обработке огромных массивов данных (миграция 10 миллионов строк из legacy БД, обработка 50 ГБ логов) Activity может выполняться несколько часов. Если воркер упадет на 99% выполнения, повторный запуск задачи с самого начала приведет к чудовищной потере ресурсов и времени.\n\nПаттерн **Activity Checkpointing** позволяет возобновлять тяжелые операции с последней контрольной точки:\n1. Activity считывает данные пачками (батчами).\n2. После каждого батча вызывается `activity.RecordHeartbeat(ctx, checkpointState)`.\n3. Данные контрольной точки сохраняются кластером Temporal.\n4. При аварийном падении воркера кластер запускает повторную попытку на другом сервере.\n5. Новая попытка проверяет `activity.HasHeartbeatDetails(ctx)` и мгновенно возобновляет работу ровно с того места, где упал погибший воркер!",
        "step_by_step": "1. Опишите структуру `MigrationCheckpoint` (LastProcessedID, TotalRowsProcessed).\n2. Реализуйте чтение контрольной точки при старте Activity.\n3. В цикле имитируйте постраничную обработку строк.\n4. Фиксируйте прогресс через `activity.RecordHeartbeat`.\n5. Завершите задачу с итоговым отчетом.",
        "code_blocks": [
            {
                "filename": "checkpointing.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/activity"
)

type MigrationCheckpoint struct {
	LastRecordID int64 `json:"last_record_id"`
	TotalRows    int64 `json:"total_rows"`
}

// MigrateTableActivity демонстрирует надежную обработку больших данных с чекпоинтами.
func MigrateTableActivity(ctx context.Context, targetTable string) error {
	logger := activity.GetLogger(ctx)

	// Инициализация точки старта: по умолчанию с нуля
	checkpoint := MigrationCheckpoint{
		LastRecordID: 0,
		TotalRows:    0,
	}

	// 1. Проверяем наличие предыдущей контрольной точки после возможного сбоя
	if activity.HasHeartbeatDetails(ctx) {
		var saved MigrationCheckpoint
		if err := activity.GetHeartbeatDetails(ctx, &saved); err == nil {
			checkpoint = saved
			logger.Info("Возобновление обработки с контрольной точки!",
				"last_id", checkpoint.LastRecordID, "processed", checkpoint.TotalRows)
			fmt.Printf(" [ACTIVITY] 🔄 Восстановление с чекпоинта: ID=%d, строк=%d\n",
				checkpoint.LastRecordID, checkpoint.TotalRows)
		}
	}

	const batchSize = 100
	const maxBatches = 10

	for batch := 0; batch < maxBatches; batch++ {
		// Проверка на случай отмены задачи
		if ctx.Err() != nil {
			logger.Warn("Обработка прервана по контексту")
			return ctx.Err()
		}

		// Имитация чтения и записи батча строк
		time.Sleep(100 * time.Millisecond)
		checkpoint.LastRecordID += batchSize
		checkpoint.TotalRows += batchSize

		// 2. Отправка Heartbeat с актуальным чекпоинтом в кластер Temporal!
		activity.RecordHeartbeat(ctx, checkpoint)

		fmt.Printf(" [ACTIVITY] ✅ Зафиксирован чекпоинт: обработано %d строк (LastID: %d)\n",
			checkpoint.TotalRows, checkpoint.LastRecordID)
	}

	logger.Info("Миграция таблицы успешно завершена", "table", targetTable, "total", checkpoint.TotalRows)
	return nil
}

func main() {
	fmt.Println("Демонстрация чекпоинтов и возобновления тяжелых Activities через Heartbeat.")
}
"""
            }
        ],
        "under_the_hood": "Кластер Temporal хранит последнее значение `HeartbeatDetails` в оперативной памяти History Service и сбрасывает его в БД при закрытии попытки. Когда воркер падает по таймауту `HeartbeatTimeout`, кластер генерирует новую задачу и вкладывает эти детали в ответ `PollActivityTaskQueue`. Таким образом, состояние чекпоинта передается новому воркеру гарантированно и без внешних баз данных.",
        "pitfalls": "Не используйте сложные циклические указатели в объекте чекпоинта. Структура должна легко и однозначно сериализоваться в JSON/Protobuf.",
        "interview_qa": "В: Как часто нужно вызывать RecordHeartbeat при пакетной обработке 1 000 000 записей?\nО: Не на каждую отдельную запись, а пачками: например, раз в 500–1000 записей или раз в 1–2 секунды. Хотя Go SDK автоматически выполняет троттлинг сетевых запросов к кластеру, слишком частые вызовы функции внутри горячего цикла создают ненужную нагрузку на CPU воркера."
    },
    {
        "num": 39,
        "title": "Local Activities vs Standard Activities: Оптимизация задержек",
        "task": "Проанализируйте различия между Standard Activities и Local Activities. Реализуйте выполнение ультра-легковесных операций (чтение ключа из локального кэша, генерация токена, валидация по регулярному выражению) через `workflow.ExecuteLocalActivity`: замерьте снижение нагрузки на Temporal Server и сокращение латентности выполнения за счет отсутствия записи отдельных событий планирования в журнал истории.",
        "theory": "В Temporal стандартная Activity требует минимум 3 сетевых раунд-трипа и записи 3 событий в историю кластера (`ActivityTaskScheduled`, `ActivityTaskStarted`, `ActivityTaskCompleted`). Для тяжелой операции (запрос в Stripe на 500 мс) это оправдано.\n\nНо если вам нужно сделать операцию на 1 миллисекунду (прочитать ключ из локального Redis, сгенерировать хэш пароля, распарсить JSON), накладные расходы стандартной активности становятся узким горлышком.\n\n**Local Activities** решают эту проблему:\n1. **Zero Task Queue**: задача НЕ отправляется в очередь Matching Service и не опрашивается поллерами.\n2. **Локальное исполнение**: активность выполняется прямо в том же процессе воркера, где крутится Workflow Task.\n3. **Минимальная история**: вместо трех событий в историю записывается всего один маркер `MarkerRecorded`.\n4. **Субмиллисекундная задержка**: вызов выполняется со скоростью прямого вызова функции Go (менее 1 мс)!",
        "step_by_step": "1. Реализуйте быструю функцию `ComputeSHA256Activity`.\n2. Настройте `workflow.LocalActivityOptions` с коротким таймаутом.\n3. Вызовите функцию через `workflow.ExecuteLocalActivity`.\n4. Сравните накладные расходы с классической `ExecuteActivity`.",
        "code_blocks": [
            {
                "filename": "local_activities.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"time"

	"go.temporal.io/sdk/workflow"
)

// ComputeHashLocalAct — ультра-быстрая функция, идеальная для Local Activity.
func ComputeHashLocalAct(ctx context.Context, payload string) (string, error) {
	h := sha256.Sum256([]byte(payload))
	return hex.EncodeToString(h[:]), nil
}

// FastWorkflow оптимизирует производительность с помощью Local Activities.
func FastWorkflow(ctx workflow.Context, data string) (string, error) {
	logger := workflow.GetLogger(ctx)

	// Настройка параметров Local Activity
	laOpts := workflow.LocalActivityOptions{
		// Быстрый таймаут одного выполнения
		ScheduleToCloseTimeout: 1 * time.Second,
	}
	ctxLocal := workflow.WithLocalActivityOptions(ctx, laOpts)

	var hashResult string
	logger.Info("Запуск легковесной Local Activity...")

	// Выполняется локально в памяти текущего воркера без обращения к Task Queue!
	err := workflow.ExecuteLocalActivity(ctxLocal, ComputeHashLocalAct, data).Get(ctxLocal, &hashResult)
	if err != nil {
		logger.Error("Ошибка Local Activity", "error", err)
		return "", err
	}

	logger.Info("Хэш успешно вычислен локально", "hash", hashResult)
	return hashResult, nil
}

func main() {
	fmt.Println("Демонстрация Local Activities для экстремальной оптимизации задержек в Temporal.")
}
"""
            }
        ],
        "under_the_hood": "В отличие от Standard Activity, Local Activity выполняется внутри текущей корутины Workflow Task Execution. Если локальная активность завершается успешно, ее результат прикрепляется к общему ответу `RespondWorkflowTaskCompleted`. Кластер сохраняет одно компактное событие `MarkerRecorded` в историю, полностью минуя Matching Service и очереди очередей.",
        "pitfalls": "Не запускайте в Local Activity долгие задачи (>5–10 секунд). Local Activity удерживает выполнение задачи Workflow Task. Если она зависнет, весь Workflow Task упадет по таймауту `WorkflowTaskTimeout` (по умолчанию 10 секунд). Local Activity предназначены исключительно для коротких операций.",
        "interview_qa": "В: Когда следует предпочесть Standard Activity вместо Local Activity?\nО: Standard Activity необходима, если: 1) Операция длится дольше нескольких секунд, 2) Нужен независимый пул специализированных воркеров (маршрутизация по Task Queue), 3) Требуется Heartbeating для отслеживания прогресса, 4) Требуется жесткий лимит параллелизма на уровне пула серверов."
    },
    {
        "num": 40,
        "title": "Workflow Replay Replayer: Локальная отладка детерминизма из продакшена",
        "task": "Экспортируйте JSON-историю сбойного Workflow из продакшен-кластера с помощью CLI `temporal workflow show --output json`. Напишите тест с использованием `worker.WorkflowReplayer`, загружающий экспортированную историю и проигрывающий её против текущего кода Go: определите точное место и причину паники `NonDeterministicWorkflowPolicy` прямо в IDE под дебаггером.",
        "theory": "Когда в продакшене падает инцидент с ошибкой недетерминированности (`WorkflowTaskFailed: NonDeterministicWorkflowPolicy`), воспроизвести такой баг традиционными методами практически невозможно — в базе лежат сотни событий, а логи воркера не дают полной картины.\n\nУникальная суперсила Temporal — **локальный дебаг истории продакшена**:\n1. Инженер одной командой выгружает историю сбойного процесса: `temporal workflow show -w order-1024 -o json > crash_history.json`.\n2. В локальной IDE создается юнит-тест с `worker.NewWorkflowReplayer()`.\n3. Тест запускается под стандартным Go дебаггером (Delve в VS Code / GoLand) с брейкпоинтами в коде Workflow.\n4. Replayer шаг за шагом воспроизводит поведение продакшена локально, позволяя за 5 минут найти забытую мапу, изменившийся порядок условий или неучтенную ветку!",
        "step_by_step": "1. Изучите методы структуры `worker.WorkflowReplayer`.\n2. Напишите Workflow с имитацией эволюции логики.\n3. Зарегистрируйте Workflow в Replayer.\n4. Продемонстрируйте вызов `ReplayWorkflowHistory` из строки JSON или файла.\n5. Перехватите и локализуйте ошибку детерминизма.",
        "code_blocks": [
            {
                "filename": "debug_replayer.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"log"

	"go.temporal.io/sdk/worker"
	"go.temporal.io/sdk/workflow"
)

// ProductionTargetWorkflow — процесс, который мы отлаживаем.
func ProductionTargetWorkflow(ctx workflow.Context, orderID string) error {
	logger := workflow.GetLogger(ctx)
	logger.Info("Локальный Replay для отладки инцидента", "order_id", orderID)

	// Допустим, здесь находится логика процесса
	return nil
}

// DebugProductionIncident запускает локальное воспроизведение истории сбойного инстанса.
func DebugProductionIncident(jsonHistoryFilePath string) error {
	replayer := worker.NewWorkflowReplayer()

	// Регистрируем локальную версию Workflow
	replayer.RegisterWorkflow(ProductionTargetWorkflow)

	fmt.Printf("🔍 Запуск дебаггера истории из файла: %s\n", jsonHistoryFilePath)

	// Метод загружает JSON продакшена и воспроизводит выполнение с точным сопоставлением команд
	err := replayer.ReplayWorkflowHistoryFromJSONFile(nil, jsonHistoryFilePath)
	if err != nil {
		return fmt.Errorf("обнаружено расхождение с историей продакшена: %w", err)
	}

	fmt.Println("✅ История воспроизведена безупречно. Код 100% детерминирован!")
	return nil
}

func main() {
	fmt.Println("Утилита отладки недетерминированных инцидентов через WorkflowReplayer.")
	// В реальном сценарии передается путь к дампу истории:
	_ = DebugProductionIncident("testdata/prod_crash_history.json")
}
"""
            }
        ],
        "under_the_hood": "WorkflowReplayer имитирует протокол взаимодействия History Service и воркера. Он парсит массив protobuf-событий из JSON файла и скармливает их во внутренний планировщик корутин Temporal SDK. Если код Workflow генерирует команду `ScheduleActivity`, а в истории на этом шаге записан `TimerStarted`, Replayer немедленно генерирует панику с подробным стек-трейсом точной строки Go-кода, вызвавшей рассинхронизацию.",
        "pitfalls": "Файл JSON-истории должен быть полным. Если выгрузить дамп незавершенного процесса, Replayer выполнит Replay до последней точки дампа и успешно остановится, не дойдя до возможной будущей ошибки.",
        "interview_qa": "В: Можно ли программно выгрузить историю завершенного процесса прямо из Go-кода без использования терминального CLI?\nО: Да, с помощью метода `client.GetWorkflowHistory(ctx, workflowID, runID, isLongPoll, filterType)`. Полученный итератор истории можно сериализовать в JSON или напрямую передать в `replayer.ReplayWorkflowHistory(nil, history)`."
    },
    {
        "num": 41,
        "title": "Temporal Cloud и mTLS-аутентификация с ротацией сертификатов",
        "task": "Настройте безопасное подключение Go-воркера к управляемому кластеру Temporal Cloud: конфигурация TLS-сертификатов, закрытых ключей и пространства имен. Реализуйте кастомный провайдер сертификатов с автоматической фоновой перезагрузкой mTLS-сертификатов при их ротации (Cert-Manager / Vault) без перезапуска процессов и потери сетевых соединений.",
        "theory": "В enterprise-окружениях Temporal часто разворачивается в управляемом облаке **Temporal Cloud**:\n- Подключение осуществляется по адресу `<namespace>.<account>.tmprl.cloud:7233`.\n- Доступ строго защищен взаимной аутентификацией (mTLS).\n- Сертификаты выпускаются корпоративным Vault или Kubernetes Cert-Manager со сроком жизни от 24 часов до нескольких дней и непрерывно ротируются.\n\nЕсли просто загрузить сертификат при старте через `tls.LoadX509KeyPair`, через сутки сертификат на диске обновится, а запущенный воркер продолжит использовать старый протухший сертификат из памяти, что приведет к аварийному отключению от кластера!\n\nРешение — использование коллбэка **`tls.Config.GetClientCertificate`**, который динамически перечитывает сертификаты из памяти или файла при каждом новом TLS-хэндшейке.",
        "step_by_step": "1. Спроектируйте структуру `RotatingKeypairManager`, периодически перечитывающую файлы сертификатов с диска.\n2. Настройте потокобезопасное обновление `*tls.Certificate` через `sync.RWMutex`.\n3. Сконфигурируйте `tls.Config.GetClientCertificate` с возвратом актуального сертификата.\n4. Подключите клиент Temporal Cloud с поддержкой горячей ротации.",
        "code_blocks": [
            {
                "filename": "cloud_mtls.go",
                "lang": "go",
                "code": r"""package main

import (
	"crypto/tls"
	"fmt"
	"sync"
	"time"

	"go.temporal.io/sdk/client"
)

// RotatingKeypairManager обеспечивает непрерывную ротацию mTLS сертификатов без даунтайма.
type RotatingKeypairManager struct {
	mu       sync.RWMutex
	certPath string
	keyPath  string
	current  *tls.Certificate
}

func NewRotatingKeypairManager(certPath, keyPath string) (*RotatingKeypairManager, error) {
	m := &RotatingKeypairManager{
		certPath: certPath,
		keyPath:  keyPath,
	}
	if err := m.reload(); err != nil {
		return nil, err
	}
	return m, nil
}

func (m *RotatingKeypairManager) reload() error {
	cert, err := tls.LoadX509KeyPair(m.certPath, m.keyPath)
	if err != nil {
		return fmt.Errorf("ошибка перезагрузки mTLS пары: %w", err)
	}

	m.mu.Lock()
	m.current = &cert
	m.mu.Unlock()

	fmt.Printf(" [mTLS] 🔑 Сертификаты успешно обновлены из %s в %s\n", m.certPath, time.Now().Format(time.RFC3339))
	return nil
}

// GetClientCertificate возвращает самый свежий сертификат при TLS хэндшейках.
func (m *RotatingKeypairManager) GetClientCertificate(*tls.CertificateRequestInfo) (*tls.Certificate, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.current, nil
}

// StartAutoReload запускает фоновый таймер проверки обновления сертификатов на диске.
func (m *RotatingKeypairManager) StartAutoReload(interval time.Duration) {
	go func() {
		ticker := time.NewTicker(interval)
		defer ticker.Stop()
		for range ticker.C {
			_ = m.reload()
		}
	}()
}

// ConnectToTemporalCloud демонстрирует подключение к облаку с авторотацией.
func ConnectToTemporalCloud(namespace, hostPort, certPath, keyPath string) (client.Client, error) {
	certManager, err := NewRotatingKeypairManager(certPath, keyPath)
	if err != nil {
		return nil, err
	}
	certManager.StartAutoReload(1 * time.Hour)

	tlsConfig := &tls.Config{
		GetClientCertificate: certManager.GetClientCertificate,
		MinVersion:           tls.VersionTLS13,
	}

	return client.Dial(client.Options{
		HostPort:  hostPort,
		Namespace: namespace,
		ConnectionOptions: client.ConnectionOptions{
			TLS: tlsConfig,
		},
	})
}

func main() {
	fmt.Println("Демонстрация интеграции с Temporal Cloud и горячей ротации mTLS-сертификатов.")
}
"""
            }
        ],
        "under_the_hood": "Библиотека `crypto/tls` в Go вызывает функцию `GetClientCertificate` каждый раз, когда сервер инициирует TLS пересогласование (Renegotiation) или клиент открывает новое subchannel соединение в gRPC пуле. Благодаря блокировке `RWMutex` подхватывание нового сертификата занимает микросекунды, гарантируя 100% непрерывность работы воркеров при регулярной ротации сертификатов в Kubernetes.",
        "pitfalls": "Не используйте системный пул доверенных CA сертификатов при работе с Temporal Cloud без проверки имени хоста (`ServerName`). Имя хоста в сертификате облака должно соответствовать шаблону `*.tmprl.cloud`.",
        "interview_qa": "В: Как защитить трафик между воркером и Temporal Cloud от перехвата и MITM атак?\nО: Использовать TLS версии не ниже TLS 1.3 с принудительной проверкой сертификата сервера и взаимной аутентификацией (mTLS), где клиентский сертификат привязан к публичному ключу пространства имен в Temporal Cloud Console."
    },
    {
        "num": 42,
        "title": "Паттерн Fan-Out / Fan-In с параллельными Child Workflows",
        "task": "Реализуйте распределенную обработку каталога товаров: родительский процесс запускает 500 дочерних процессов `workflow.ExecuteChildWorkflow`. С помощью `workflow.Selector` организуйте сбор результатов завершения дочерних процессов с ограничением степени параллелизма (не более 20 одновременно исполняемых процессов) и агрегацией финального отчета.",
        "theory": "Паттерн **Fan-Out / Fan-In** — основа масштабируемой пакетной обработки данных:\n- **Fan-Out (Разветвление)**: разделение большого массива задач на сотни независимых параллельных подпроцессов.\n- **Fan-In (Схлопывание / Агрегация)**: сбор результатов, фильтрация ошибок и формирование единого отчета.\n\nПри масштабировании Fan-Out важно контролировать степень параллелизма (Concurrency Throttling). Если одновременно запустить 50 000 дочерних процессов, кластер испытает колоссальный всплеск нагрузки. Профессиональный подход — использование семафора или буферизованного пула (Worker Pool pattern внутри Workflow с `workflow.Selector`), ограничивающего число активных дочерних процессов фиксированным лимитом (например, 20 параллельно).",
        "step_by_step": "1. Опишите дочерний процесс `ProcessSKUChildWorkflow`.\n2. В родительском процессе реализуйте контролируемый Fan-Out на 100 товаров с параллелизмом не более 5.\n3. Используйте `workflow.Selector` для динамического запуска следующей задачи по мере завершения предыдущей.\n4. Агрегируйте результаты и сформируйте итоговую статистику.",
        "code_blocks": [
            {
                "filename": "fan_out_fan_in.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"time"

	"go.temporal.io/sdk/workflow"
)

type ItemResult struct {
	SKU     string
	Success bool
}

// ProcessSKUChildWorkflow обрабатывает единичный товар.
func ProcessSKUChildWorkflow(ctx workflow.Context, sku string) (ItemResult, error) {
	_ = workflow.Sleep(ctx, 500*time.Millisecond) // Имитация обработки
	return ItemResult{SKU: sku, Success: true}, nil
}

// ThrottledCatalogFanOutWorkflow выполняет Fan-Out с жестким ограничением параллелизма.
func ThrottledCatalogFanOutWorkflow(ctx workflow.Context, skus []string) ([]ItemResult, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Старт пакетной обработки каталога", "total_items", len(skus))

	const maxConcurrent = 5 // Максимум 5 процессов одновременно
	results := make([]ItemResult, 0, len(skus))

	selector := workflow.NewSelector(ctx)
	inFlight := 0
	skuIndex := 0

	// Функция запуска очередного дочернего процесса
	startNext := func() {
		if skuIndex >= len(skus) {
			return
		}
		sku := skus[skuIndex]
		skuIndex++
		inFlight++

		cwo := workflow.ChildWorkflowOptions{
			WorkflowID: fmt.Sprintf("sku-child-%s", sku),
		}
		childCtx := workflow.WithChildOptions(ctx, cwo)
		future := workflow.ExecuteChildWorkflow(childCtx, ProcessSKUChildWorkflow, sku)

		// Добавляем Future в Selector: когда завершится, освободится слот!
		selector.AddFuture(future, func(f workflow.Future) {
			inFlight--
			var res ItemResult
			if err := f.Get(ctx, &res); err == nil {
				results = append(results, res)
			}
		})
	}

	// Заполняем первоначальный пул параллелизма
	for i := 0; i < maxConcurrent && i < len(skus); i++ {
		startNext()
	}

	// Цикл Fan-In: ждем завершения и подкидываем новые задачи, пока всё не завершится
	for inFlight > 0 {
		selector.Select(ctx)
		// Если освободилось место и есть еще элементы — запускаем следующий!
		for inFlight < maxConcurrent && skuIndex < len(skus) {
			startNext()
		}
	}

	logger.Info("Fan-Out / Fan-In успешно завершен!", "processed", len(results))
	return results, nil
}

func main() {
	fmt.Println("Демонстрация контролируемого параллелизма Fan-Out/Fan-In на Child Workflows.")
}
"""
            }
        ],
        "under_the_hood": "Благодаря `workflow.Selector` и локальному счетчику `inFlight`, Workflow никогда не создает больше `maxConcurrent` одновременных вызовов к кластеру. Это предотвращает скачки размера истории событий (History Size Spike) и бережет базы данных кластера от перегрузки.",
        "pitfalls": "Если в Fan-Out массиве содержатся десятки тысяч элементов, один Workflow не должен запускать их все напрямую, даже по очереди, иначе его собственная история переполнится. При объемах > 5 000 элементов используйте двухуровневую иерархию (батчи батчей) или паттерн `Continue-As-New`.",
        "interview_qa": "В: Что произойдет с запущенными дочерними процессами, если родительский Workflow упадет по таймауту?\nО: Это определяется политикой `ParentClosePolicy`. Если установлено `PARENT_CLOSE_POLICY_TERMINATE`, кластер мгновенно убьет все активные дочерние процессы. Если установлено `ABANDON`, они продолжат исполнение независимо."
    },
    {
        "num": 43,
        "title": "Приоритезация задач через Task Queues и Rate Limiting воркеров",
        "task": "Разделите критический и фоновый трафик по независимым очередям задач: `order-processing-high-priority` и `analytics-low-priority`. Сконфигурируйте распределенный Rate Limiting воркеров: настройка `MaxWorkerActivitiesPerSecond` для гарантированной защиты сторонних внешних REST API от превышения лимитов запросов (429 Too Many Requests).",
        "theory": "В корпоративных системах разные бизнес-процессы имеют кардинально разный SLA:\n- Оформление заказа клиентом в корзине: High Priority (SLA < 1 сек).\n- Ежедневный расчет аналитических витрин: Low Priority (может подождать часы).\n\nЕсли направить оба типа задач в одну общую очередь, многомиллионный фоновый аналитический отчет забьет очередь, и реальные покупатели не смогут оформить заказ!\n\nРешение включает два механизма:\n1. **Изоляция очередей задач (Queue Partitioning)**: физическое разделение очередей задач и пулов воркеров с гарантированным выделением ресурсов критическому трафику.\n2. **Worker Rate Limiting (`WorkerActivitiesPerSecond`)**: аппаратное ограничение количества выполняемых активностей в секунду на уровне воркера для защиты партнерских API от бана по лимитам запросов.",
        "step_by_step": "1. Сконфигурируйте два независимых воркера для очередей High Priority и Low Priority.\n2. Настройте ограничение `WorkerActivitiesPerSecond: 50.0` для воркера интеграций.\n3. Продемонстрируйте маршрутизацию задач в зависимости от бизнес-приоритета.\n4. Объясните алгоритм распределения ресурсов.",
        "code_blocks": [
            {
                "filename": "priority_ratelimit.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"log"

	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/worker"
)

func CriticalPaymentActivity(ctx context.Context, orderID string) error {
	fmt.Printf(" [HIGH PRIORITY] ⚡ Мгновенная авторизация платежа заказа %s\n", orderID)
	return nil
}

func HeavyExportActivity(ctx context.Context, reportID string) error {
	fmt.Printf(" [LOW PRIORITY] ⏳ Фоновая выгрузка аналитического отчета %s...\n", reportID)
	return nil
}

// SetupPrioritizedWorkers настраивает изолированные пулы с Rate Limiting.
func SetupPrioritizedWorkers(c client.Client) (worker.Worker, worker.Worker) {
	// 1. Пул воркеров высокой доступности (High Priority): максимальный параллелизм, без ограничений
	highPriorityWorker := worker.New(c, "order-processing-high-priority", worker.Options{
		MaxConcurrentActivityExecutionSize: 1000,
	})
	highPriorityWorker.RegisterActivity(CriticalPaymentActivity)

	// 2. Пул воркеров фоновых задач (Low Priority): жесткий Rate Limiting!
	// Не более 10 операций в секунду для защиты внешнего стороннего API от 429 ошибки
	lowPriorityWorker := worker.New(c, "analytics-low-priority", worker.Options{
		WorkerActivitiesPerSecond:          10.0, // Лимит скорости воркера!
		MaxConcurrentActivityExecutionSize: 20,
	})
	lowPriorityWorker.RegisterActivity(HeavyExportActivity)

	fmt.Println("🚀 Изолированные пулы воркеров High Priority и Low Priority успешно инициализированы!")
	return highPriorityWorker, lowPriorityWorker
}

func main() {
	c, err := client.Dial(client.Options{HostPort: "localhost:7233"})
	if err != nil {
		log.Fatalf("Ошибка подключения: %v", err)
	}
	defer c.Close()

	wHigh, wLow := SetupPrioritizedWorkers(c)
	_ = wHigh
	_ = wLow
}
"""
            }
        ],
        "under_the_hood": "Параметр `WorkerActivitiesPerSecond` использует встроенный токен-бакет (Token Bucket Rate Limiter) прямо в коде Go SDK. Перед вызовом функции Activity воркер запрашивает токен из локального лимитера. Если лимит исчерпан, воркер приостанавливает вычитку задач из очереди Matching Service, предотвращая образование заторов.",
        "pitfalls": "Обратите внимание: `WorkerActivitiesPerSecond` действует на уровне ОДНОГО экземпляра воркера (пода). Если вы масштабируете деплоймент до 100 подов в Kubernetes, суммарный лимит запросов составит `100 * WorkerActivitiesPerSecond`. Для глобального ограничения на всю систему настраивайте лимит на уровне Task Queue в Temporal Cluster.",
        "interview_qa": "В: Как реализовать глобальный Rate Limiting на всю очередь задач независимо от количества запущенных воркеров?\nО: Через настройку `TaskQueueActivitiesPerSecond` при регистрации или обновлении конфигурации очереди в кластере Temporal. Matching Service будет самостоятельно контролировать скорость выдачи задач всем подключенным воркерам суммарно."
    },
    {
        "num": 44,
        "title": "Fault Injection и тестирование надежности через Chaos Testing",
        "task": "Напишите стресс-тест устойчивости процесса оформления кредита: смоделируйте хаос в инфраструктуре с внезапной гибелью воркеров прямо посреди шага списания средств, сетевыми задержками до кластера Temporal и перезапуском серверов. Докажите, что процесс гарантированно восстанавливается из последней контрольной точки и доходит до завершения.",
        "theory": "В распределенных системах недостаточно написать код — нужно доказать его устойчивость в условиях реального хаоса инфраструктуры (Chaos Engineering):\n- Убийство воркера по `kill -9` посреди шага.\n- Временная потеря связи с базой данных кластера.\n- Зависание сетевых сокетов сторонних сервисов.\n\nБлагодаря архитектуре Durable Execution в Temporal такие аварии не приводят к потере данных. Мы можем смоделировать падение рабочего процесса в юнит-тесте или интеграционном тесте, перезапустить воркер и убедиться, что бизнес-транзакция завершилась успешно и в строгом соответствии с контрактом.",
        "step_by_step": "1. Реализуйте многошаговый процесс кредитования.\n2. Напишите тест с имитацией падения воркера на шаге 2 через тестовое окружение `testsuite`.\n3. Перезапустите воркер и вызовите повторное исполнение.\n4. Проверьте, что процесс успешно восстановил состояние и финализировался.",
        "code_blocks": [
            {
                "filename": "chaos_test.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"testing"
	"time"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/suite"
	"go.temporal.io/sdk/testsuite"
	"go.temporal.io/sdk/workflow"
)

func DebitAccountStep(ctx context.Context) error {
	return nil
}

func CreditAccountStep(ctx context.Context) error {
	return nil
}

func ResilientTransferWorkflow(ctx workflow.Context) (string, error) {
	ao := workflow.ActivityOptions{StartToCloseTimeout: 5 * time.Second}
	ctx = workflow.WithActivityOptions(ctx, ao)

	// Шаг 1: Дебет
	if err := workflow.ExecuteActivity(ctx, DebitAccountStep).Get(ctx, nil); err != nil {
		return "", err
	}

	// Шаг 2: Кредит
	if err := workflow.ExecuteActivity(ctx, CreditAccountStep).Get(ctx, nil); err != nil {
		return "", err
	}

	return "TRANSFER_COMPLETED", nil
}

type ChaosTestSuite struct {
	suite.Suite
	testsuite.WorkflowTestSuite
}

func (s *ChaosTestSuite) Test_SimulateWorkerCrash_Recovery() {
	env := s.NewTestWorkflowEnvironment()

	// Шаг 1 успешен
	env.OnActivity(DebitAccountStep, mock.Anything).Return(nil)

	// Шаг 2 падает на первой попытке (симуляция краха пода), но успешен на второй
	attempt := 0
	env.OnActivity(CreditAccountStep, mock.Anything).Return(func(ctx context.Context) error {
		attempt++
		if attempt == 1 {
			fmt.Println(" 💥 [CHAOS] Воркер внезапно упал прямо посреди перевода средств!")
			return errors.New("SIGKILL: worker process terminated unexpectedly")
		}
		fmt.Println(" 🔄 [RECOVERY] Новый воркер поднялся, вычитал историю и успешно завершил перевод!")
		return nil
	})

	env.ExecuteWorkflow(ResilientTransferWorkflow)

	s.True(env.IsWorkflowCompleted())
	s.NoError(env.GetWorkflowError())

	var result string
	s.NoError(env.GetWorkflowResult(&result))
	s.Equal("TRANSFER_COMPLETED", result)
	fmt.Printf("✅ Стресс-тест пройден: процесс выдержал крах воркера и сохранил целостность данных!\n")
}

func TestChaosSuite(t *testing.T) {
	suite.Run(t, new(ChaosTestSuite))
}

func main() {}
"""
            }
        ],
        "under_the_hood": "При имитации сбоя тестовое окружение Temporal фиксирует событие сбоя попытки в журнале, пересчитывает таймер повтора согласно `RetryPolicy` и заново активирует Workflow Task на новом виртуальном воркере. Воркер восстанавливает состояние шага 1 через детерминированный Replay и повторяет шаг 2, доказывая полную неуязвимость процесса к аппаратным сбоям.",
        "pitfalls": "При проведении хаос-тестирования в реальном стейджинге (через Chaos Mesh или Toxiproxy) убедитесь, что ваши внешние сервисы поддерживают идемпотентность, иначе повторные вызовы после краха узла приведут к дублирующим операциям на стороне третьих лиц.",
        "interview_qa": "В: Как проверить поведение системы при падении самого кластера Temporal (например, остановке базы данных History)?\nО: Воркеры перейдут в режим ожидания с экспоненциальными повторами gRPC соединений. Как только база данных кластера оживет, воркеры восстановят стримы без потери состояния, продолжат Replay и доведут все активные процессы до успешного завершения."
    },
    {
        "num": 45,
        "title": "Асинхронные внешние коллбэки через Activity Completion Token",
        "task": "Реализуйте Activity, которая ожидает решения кредитного инспектора (которое может занять несколько дней). Метод активности отправляет запрос во внешнюю CRM-систему, сохраняет токен завершения задачи (`activity.GetInfo(ctx).TaskToken`) в базу данных и возвращает специальную ошибку `activity.ErrResultPending`. Реализуйте внешний HTTP-хэндлер, который при получении вебхука от инспектора завершает активность через `client.CompleteActivity(taskToken, result)`.",
        "theory": "В классических микросервисах интеграция с долгими асинхронными внешними системами (ручной скоринг андеррайтером, ожидание физической подписи документов, асинхронный ответ от государственной базы данных через сутки) приводит к созданию костылей.\n\nTemporal предоставляет нативный паттерн **Asynchronous Activity Completion**:\n1. Activity стартует на воркере.\n2. Функция извлекает уникальный бинарный токен задачи: `taskToken := activity.GetInfo(ctx).TaskToken`.\n3. Activity отправляет токен во внешнюю систему (например, в CRM) и возвращает специальную сигнальную ошибку: `return activity.ErrResultPending`.\n4. Воркер освобождается! Никаких горутин не висит в памяти!\n5. Через 3 дня, когда человек нажимает кнопку в CRM, внешний HTTP-сервис вызывает `client.CompleteActivity(ctx, taskToken, result, nil)`.\n6. Кластер завершает активность и передает результат спящему Workflow!",
        "step_by_step": "1. В Activity извлеките `activity.GetInfo(ctx).TaskToken`.\n2. Сохраните токен и верните `activity.ErrResultPending`.\n3. Спроектируйте HTTP-хэндлер вебхука согласования.\n4. Вызовите метод `c.CompleteActivity(ctx, token, result, nil)`.\n5. Дождитесь успешного продолжения Workflow.",
        "code_blocks": [
            {
                "filename": "async_completion.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"encoding/base64"
	"fmt"
	"time"

	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/workflow"
)

// AwaitManualReviewActivity регистрирует внешнюю задачу и освобождает воркер.
func AwaitManualReviewActivity(ctx context.Context, applicationID string) (string, error) {
	info := activity.GetInfo(ctx)

	// Получаем бинарный TaskToken
	taskToken := info.TaskToken
	encodedToken := base64.StdEncoding.EncodeToString(taskToken)

	fmt.Printf(" [ACTIVITY] Заявка %s отправлена в CRM инспектору. TaskToken: %s\n",
		applicationID, encodedToken[:20]+"...")

	// Возвращаем специальную ошибку: активность НЕ завершена, результат будет позже асинхронно!
	return "", activity.ErrResultPending
}

// CompleteReviewWebhook имитирует внешний вебхук, когда инспектор принял решение через 2 дня.
func CompleteReviewWebhook(c client.Client, encodedToken string, approved bool) error {
	taskToken, err := base64.StdEncoding.DecodeString(encodedToken)
	if err != nil {
		return err
	}

	resultText := "REJECTED_BY_OFFICER"
	if approved {
		resultText = "APPROVED_BY_OFFICER"
	}

	// Асинхронное завершение активности из внешнего сервиса по токену!
	err = c.CompleteActivity(context.Background(), taskToken, resultText, nil)
	if err != nil {
		return fmt.Errorf("не удалось асинхронно завершить Activity: %w", err)
	}

	fmt.Println(" [WEBHOOK] ✅ Активность успешно завершена внешним вызовом CompleteActivity!")
	return nil
}

func UnderwritingWorkflow(ctx workflow.Context, appID string) (string, error) {
	// Допустим, даем 7 дней на ручную проверку
	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 7 * 24 * time.Hour,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var decision string
	err := workflow.ExecuteActivity(ctx, AwaitManualReviewActivity, appID).Get(ctx, &decision)
	if err != nil {
		return "", err
	}

	return "FINAL_DECISION: " + decision, nil
}

func main() {
	fmt.Println("Демонстрация Asynchronous Activity Completion через TaskToken.")
}
"""
            }
        ],
        "under_the_hood": "`TaskToken` — это сериализованная protobuf-структура, содержащая `Namespace`, `WorkflowID`, `RunID`, `ScheduleEventID` и номер попытки. Когда клиент вызывает `CompleteActivity(token, res)`, кластер напрямую маршрутизирует событие в нужный шард History Service и завершает ожидающую активность, не требуя работы воркера во время многодневного ожидания.",
        "pitfalls": "Обязательно настраивайте `StartToCloseTimeout` с учетом максимального времени ожидания человека. Если инспектор не примет решение до истечения этого таймаута, активность завершится ошибкой по таймауту.",
        "interview_qa": "В: В чем различие между асинхронным завершением Activity (TaskToken) и приемом внешнего Сигнала (Signal)?\nО: Сигнал доставляется напрямую в Workflow и требует реализации логики приема канала внутри процесса. Асинхронное завершение Activity скрывает внешнее многодневное ожидание за обычным вызовом `workflow.ExecuteActivity`: код Workflow выглядит как обычный синхронный вызов функции, что делает код чище и модульное."
    },
    {
        "num": 46,
        "title": "Temporal Payload Codec Server: Внешний сервер расшифровки данных",
        "task": "Разверните удаленный HTTP-сервер кодеков (Codec Server) на Go с авторизацией по токенам: интегрируйте его с веб-интерфейсом Temporal Web UI. Продемонстрируйте, как зашифрованные полезные нагрузки процессов (AES-256) безопасно расшифровываются прямо в браузере авторизованного инженера поддержки без раскрытия закрытых ключей серверу Temporal.",
        "theory": "Когда в компании включено сквозное шифрование (Custom DataConverter), база данных кластера хранит только зашифрованные шифротексты. В результате в стандартном веб-интерфейсе Temporal Web UI разработчики и служба поддержки видят только base64-строки `binary/encrypted`.\n\nДля решения этой проблемы архитектура Temporal включает **Payload Codec Server**:\n1. Инженер открывает Temporal Web UI в браузере и настраивает адрес корпоративного Codec Server (например, `https://codec.internal.company.com/decode`).\n2. Браузер авторизуется через корпоративный SSO (OAuth2 / OIDC токен).\n3. Web UI отправляет зашифрованные пейлоады напрямую в Codec Server по HTTPS с токеном пользователя.\n4. Codec Server валидирует права доступа сотрудника, расшифровывает JSON с помощью мастер-ключа из KMS и возвращает открытый JSON в браузер.\n5. Сам кластер Temporal и интернет НИКОГДА не получают доступа к открытым данным!",
        "step_by_step": "1. Спроектируйте HTTP-сервер на Go, реализующий спецификацию Temporal Codec Server API (`/decode` и `/encode`).\n2. Реализуйте middleware проверки Bearer токена авторизации.\n3. Реализуйте дешифрование полезной нагрузки AES-256.\n4. Настройте CORS заголовки для безопасных кросс-доменных вызовов из Web UI.\n5. Продемонстрируйте работу сервера.",
        "code_blocks": [
            {
                "filename": "codec_server.go",
                "lang": "go",
                "code": r"""package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"

	commonpb "go.temporal.io/api/common/v1"
)

type PayloadList struct {
	Payloads []*commonpb.Payload `json:"payloads"`
}

// CodecServer обрабатывает запросы расшифровки данных от Temporal Web UI.
type CodecServer struct {
	secretKey []byte
}

func (s *CodecServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// 1. Настройка CORS для разрешения запросов из Temporal Web UI
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}

	// 2. Проверка авторизации инженера
	authHeader := r.Header.Get("Authorization")
	if !strings.HasPrefix(authHeader, "Bearer valid-sso-token") {
		http.Error(w, "Unauthorized: invalid engineer token", http.StatusUnauthorized)
		return
	}

	if r.URL.Path == "/decode" && r.Method == http.MethodPost {
		var req PayloadList
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		// Имитация расшифровки пейлоадов
		fmt.Printf(" [CODEC SERVER] 🔓 Расшифровка %d пейлоадов для авторизованного инженера...\n", len(req.Payloads))

		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(req)
		return
	}

	http.NotFound(w, r)
}

func main() {
	server := &CodecServer{secretKey: []byte("very-secret-32-byte-key-aes-256")}
	fmt.Println("🚀 Temporal Remote Payload Codec Server запущен на порту :8081...")
	_ = server
}
"""
            }
        ],
        "under_the_hood": "Temporal Web UI выполняет вызовы к Codec Server прямо из JavaScript в браузере клиента. Трафик не проходит через сервер Temporal. Codec Server может быть развернут внутри закрытого VPN-контура компании, гарантируя, что конфиденциальные данные расшифровываются исключительно на рабочей станции авторизованного сотрудника.",
        "pitfalls": "Всегда реализуйте строгую валидацию CORS и аутентификацию по токенам в Codec Server. Развертывание незащищенного Codec Server без авторизации сводит на нет всю защиту сквозного шифрования.",
        "interview_qa": "В: Как ограничить расшифровку определенных чувствительных полей (например, CVV карты) даже для инженеров с доступом к Codec Server?\nО: В Codec Server можно настроить маскирование данных (Data Masking / Redaction): при расшифровке JSON парсится, поле `cvv` заменяется на `***`, а номер карты маскируется до `4111****1111` перед отправкой в веб-интерфейс."
    },
    {
        "num": 47,
        "title": "Мониторинг очередей и производительности SDK через Prometheus",
        "task": "Подключите Prometheus-метрики Temporal SDK к сервису: настройте отслеживание задержек `temporal_workflow_task_schedule_to_start_latency` (время ожидания задачи в очереди до захвата воркером), `temporal_activity_execution_failed_total`, количества активных кэшированных процессов и пула горутин. Сформируйте правила алертинга на рост лага очередей.",
        "theory": "Эксплуатация Temporal в продакшене невозможна без глубокой телеметрии. Ключевые метрики делятся на две группы:\n\n1. **Метрики задержки очередей (Queue Latency / Schedule-To-Start)**:\n   - `temporal_workflow_task_schedule_to_start_latency` и `temporal_activity_schedule_to_start_latency`.\n   - Показывают, сколько миллисекунд задача ждала свободного воркера в Task Queue.\n   - Рост этой метрики — главный сигнал для немедленного автомасштабирования (HPA) подов воркеров!\n\n2. **Метрики надежности и кэша**:\n   - `temporal_activity_execution_failed_total`: всплеск ошибок внешних API.\n   - `temporal_sticky_cache_size` и `temporal_sticky_cache_hit_total`: эффективность использования оперативной памяти.",
        "step_by_step": "1. Подключите адаптер Prometheus через пакет `github.com/uber-go/tally/v4/prometheus`.\n2. Сконфигурируйте `client.Options{MetricsHandler: ...}`.\n3. Настройте HTTP-эндпоинт `/metrics`.\n4. Опишите PromQL правила для алертинга на превышение лага очереди более 2 секунд.",
        "code_blocks": [
            {
                "filename": "metrics_setup.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"net/http"

	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.temporal.io/sdk/client"
)

// SetupPrometheusMetricsClient демонстрирует подключение экспортера метрик.
func SetupPrometheusMetricsClient() (client.Client, error) {
	// В реальном проекте подключается sdkmiddleware или tally/prometheus handler:
	// metricsHandler := sdkmiddleware.NewPrometheusHandler(promConfig)

	// Запуск HTTP сервера метрик для сбора Prometheus Scraper
	go func() {
		http.Handle("/metrics", promhttp.Handler())
		fmt.Println("📊 Prometheus метрики доступны по адресу http://localhost:9090/metrics")
		_ = http.ListenAndServe(":9090", nil)
	}()

	return client.Dial(client.Options{
		HostPort: "localhost:7233",
		// MetricsHandler: metricsHandler,
	})
}

func main() {
	fmt.Println("=== PromQL правила алертинга для Temporal Worker ===")
	fmt.Println("1. Алерт на лаг очередей: histogram_quantile(0.99, sum(rate(temporal_workflow_task_schedule_to_start_latency_seconds_bucket[5m])) by (le, task_queue)) > 2.0")
	fmt.Println("2. Алерт на всплеск падений Activities: sum(rate(temporal_activity_execution_failed_total[5m])) > 10")
}
"""
            }
        ],
        "under_the_hood": "Go SDK замеряет временные метрики с помощью монотонных системных часов `time.Now()`. Задержка `Schedule-To-Start` вычисляется как разница между серверной меткой времени `ScheduledTime` из события очереди и моментом вызова функции на воркере. Метрики экспортируются в стандартные гистограммы Prometheus.",
        "pitfalls": "Не используйте слишком детализированные лейблы (High Cardinality) в кастомных метриках, такие как `WorkflowID` или `UserID`. Это приведет к взрывному росту временных рядов в Prometheus и падению базы метрик.",
        "interview_qa": "В: По какой ключевой метрике следует настраивать горизонтальное авто-масштабирование (HPA) воркеров в Kubernetes?\nО: По задержке `Schedule-To-Start` (`temporal_workflow_task_schedule_to_start_latency` p95) или по метрике размера неразобранной очереди `temporal_task_queue_backlog` из Temporal Cluster. Если задачи ждут в очереди дольше 500 мс, HPA обязан добавлять новые реплики подов воркеров."
    },
    {
        "num": 48,
        "title": "Temporal Multi-Cluster Replication: Построение Active-Passive гео-распределения",
        "task": "Сконфигурируйте клиентское приложение и воркеры для работы в отказоустойчивой мультикластерной среде с репликацией между датацентрами (Active-Passive Geo-Redundancy). Смоделируйте аварийное переключение пространства имен (Namespace Failover) на резервный кластер: покажите, как активные рабочие процессы продолжают исполнение на резервной площадке с сохраненным состоянием.",
        "theory": "В критических банковских и телеком-системах отказ одного датацентра не должен прерывать исполнение бизнес-процессов.\n\n**Temporal Multi-Cluster Replication** обеспечивает гео-распределенную отказоустойчивость:\n1. Кластеры Temporal развертываются в двух независимых датацентрах (например, `dc-primary` и `dc-standby`).\n2. Пространство имен (Namespace) настраивается как Global Namespace с репликацией истории событий через асинхронный Replication Queue.\n3. Воркеры запущены в ОБОИХ датацентрах и подключены к своим локальным кластерам.\n4. При аварии датацентра Primary администратор выполняет одну команду переключения: `temporal operator namespace update --active-cluster dc-standby`.\n5. Резервный кластер становится Active, воркеры в Standby подхватывают исполнение задач ровно с той точки, где произошел сбой, без потери данных!",
        "step_by_step": "1. Спроектируйте архитектурную схему Global Namespace с двумя кластерами.\n2. Напишите код подключения воркера к локальному кластеру площадки.\n3. Смоделируйте переключение Active Cluster.\n4. Продемонстрируйте подхватывание процесса резервным воркером.",
        "code_blocks": [
            {
                "filename": "multi_cluster.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"time"

	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/workflow"
)

// GeoResilientWorkflow устойчив к падению целого датацентра.
func GeoResilientWorkflow(ctx workflow.Context, orderID string) error {
	logger := workflow.GetLogger(ctx)
	logger.Info("Процесс запущен в глобальном пространстве имен с репликацией", "order_id", orderID)

	// Долгий процесс с несколькими шагами
	_ = workflow.Sleep(ctx, 5*time.Second)

	logger.Info("Процесс пережил гео-переключение кластера и успешно финализирован!")
	return nil
}

// MultiClusterTopologyDemo иллюстрирует архитектуру Active-Passive.
func MultiClusterTopologyDemo() {
	fmt.Println("=== Архитектура Temporal Multi-Cluster Replication ===")
	fmt.Println("1. Кластер DC-1 (Primary): активен, пишет историю в БД Spanner/Postgres.")
	fmt.Println("2. Кластер DC-2 (Standby): принимает репликацию событий через gRPC Replication Stream.")
	fmt.Println("3. Воркеры запущены в обоих DC и слушают единую очередь 'geo-orders'.")
	fmt.Println("4. При падении DC-1 выполняется команда: temporal operator namespace update --active-cluster dc-2")
	fmt.Println("5. DC-2 мгновенно переходит в режим Active и начинает раздавать задачи воркерам в DC-2!")
}

func main() {
	MultiClusterTopologyDemo()
}
"""
            }
        ],
        "under_the_hood": "History Service кластера генерирует репликационные задачи для каждого зафиксированного события. Сервер на резервной площадке непрерывно вычитывает этот поток изменений и применяет их к своей копии базы данных. При переключении площадки (Failover) кластер генерирует маркер `VersionHistory`, разрешая возможные конфликты параллельных записей и гарантируя линеаризуемость.",
        "pitfalls": "Репликация между датацентрами является асинхронной. При внезапной полной физической гибели первичного ЦОД возможна потеря нескольких последних миллисекунд событий, которые еще не успели долететь по сети до резервной площадки (RPO > 0, но стремится к долям секунды).",
        "interview_qa": "В: Могут ли воркеры в резервном датацентре исполнять задачи до выполнения команды Failover?\nО: Нет! Пока Namespace находится в статусе Standby в данном кластере, Matching Service этого кластера не выдает задачи на исполнение воркерам, чтобы исключить риск конфликтов (Split-Brain). Задачи начнут выдаваться только после того, как кластер станет Active."
    },
    {
        "num": 49,
        "title": "Паттерн Durable Poller: Долгоживущий опрос внешних систем",
        "task": "Разработайте надежный долгоживущий процесс опроса статуса банковского перевода в стороннем шлюзе (Long-running Poller): периодическое выполнение Activity с адаптивным интервалом опроса (Exponential Backoff), обработка сетевых сбоев, предотвращение разрастания истории через паттерн `Continue-As-New` и корректная обработка сигнала отмены.",
        "theory": "Во многих интеграциях внешние системы не поддерживают вебхуки, а предлагают только метод проверки статуса `GET /payments/{id}/status` (Polling). Банковский перевод может обрабатываться от 10 минут до 3 суток.\n\nОрганизация такого опроса через обычные cron-задачи или горутины неэффективна и грозит потерей состояния.\n\nПаттерн **Durable Poller** на Temporal:\n1. Workflow вызывает Activity проверки статуса.\n2. Если статус 'PENDING', процесс засыпает через `workflow.Sleep(ctx, currentInterval)` с экспоненциальным ростом интервала (сначала каждые 10 сек, затем раз в минуту, затем раз в час).\n3. Если процесс опрашивает систему дольше 24 часов, он сбрасывает историю через `Continue-As-New`.\n4. Процесс в любой момент готов прерваться по сигналу отмены от пользователя.",
        "step_by_step": "1. Реализуйте активность `CheckStatusActivity`.\n2. Спроектируйте Workflow с циклом опроса и адаптивным интервалом `backoff`.\n3. Добавьте счетчик итераций и вызов `workflow.NewContinueAsNewError`.\n4. Обеспечьте корректный выход при достижении статуса `SUCCESS` или `REJECTED`.",
        "code_blocks": [
            {
                "filename": "durable_poller.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/workflow"
)

type PollerState struct {
	PaymentID    string        `json:"payment_id"`
	AttemptCount int           `json:"attempt_count"`
	Interval     time.Duration `json:"interval"`
}

func CheckExternalStatusActivity(ctx context.Context, paymentID string) (string, error) {
	fmt.Printf(" [POLLER ACTIVITY] Опрос банковского шлюза для платежа %s...\n", paymentID)
	// В реальном API: возврат "PENDING", "COMPLETED", "REJECTED"
	return "PENDING", nil
}

// DurablePollerWorkflow реализует адаптивный долгоживущий опрос.
func DurablePollerWorkflow(ctx workflow.Context, state PollerState) (string, error) {
	logger := workflow.GetLogger(ctx)
	ao := workflow.ActivityOptions{StartToCloseTimeout: 10 * time.Second}
	ctx = workflow.WithActivityOptions(ctx, ao)

	if state.Interval == 0 {
		state.Interval = 5 * time.Second
	}

	const maxInterval = 1 * time.Hour
	const iterationsPerRun = 200 // Сброс истории каждые 200 итераций

	for i := 0; i < iterationsPerRun; i++ {
		state.AttemptCount++

		var status string
		err := workflow.ExecuteActivity(ctx, CheckExternalStatusActivity, state.PaymentID).Get(ctx, &status)
		if err == nil && status == "COMPLETED" {
			logger.Info("Платеж успешно завершен банком!", "payment_id", state.PaymentID)
			return "SUCCESS", nil
		}

		// Адаптивный экспоненциальный backoff интервала опроса
		state.Interval = time.Duration(float64(state.Interval) * 1.5)
		if state.Interval > maxInterval {
			state.Interval = maxInterval
		}

		logger.Info("Статус еще PENDING. Сон перед следующим опросом...", "interval", state.Interval)
		if err := workflow.Sleep(ctx, state.Interval); err != nil {
			return "", err // Обработка отмены
		}
	}

	// Достигнут лимит итераций: очищаем историю и продолжаем опрос с чистого листа
	logger.Info("Ротация истории Durable Poller через Continue-As-New...")
	return "", workflow.NewContinueAsNewError(ctx, DurablePollerWorkflow, state)
}

func main() {
	fmt.Println("Демонстрация паттерна Durable Poller с адаптивным Backoff и Continue-As-New.")
}
"""
            }
        ],
        "under_the_hood": "Во время фазы сна между опросами воркер полностью выгружает процесс из памяти. Если опрос длится 5 дней, кластер Temporal активирует воркер ровно на 100 миллисекунд раз в час для совершения вызова Activity и снова усыпляет его, обеспечивая микроскопическое потребление вычислительных ресурсов.",
        "pitfalls": "Не забывайте задавать потолок максимального интервала (`maxInterval`), иначе экспоненциальный backoff быстро увеличит время между опросами до десятков суток.",
        "interview_qa": "В: Как позволить пользователю принудительно запросить опрос статуса прямо сейчас, не дожидаясь таймера сна?\nО: Используйте `workflow.Selector` параллельно с таймером сна и каналом внешнего сигнала `RefreshStatusSignal`. При получении сигнала селектор мгновенно разблокируется, прервет сон и выполнит Activity опроса немедленно."
    },
    {
        "num": 50,
        "title": "Корпоративный процессинг международных банковских переводов (SWIFT / SEPA)",
        "task": "Спроектируйте законченный комплексный рабочий процесс валютного перевода корпоративного уровня: проверка комплаенса (KYC/AML), блокировка средств на счете, вызов внешнего межбанковского шлюза с асинхронным Completion Token, конвертация валют, рассылка уведомлений, автоматическая Сага с компенсациями при отказах, аудит через Search Attributes и сквозное шифрование.",
        "theory": "Флагманский проект главы: банковский процессинг международных переводов (Cross-Border Wire Transfers via SWIFT / SEPA). Это вершина надежности распределенных систем, где цена сбоя — миллионы долларов и отзыв банковской лицензии.\n\nВ этом проекте синтезируются все продвинутые возможности Temporal:\n1. **Строгая дедупликация**: `WorkflowID = 'swift-txn-' + paymentRef` с `WorkflowIdReusePolicyRejectDuplicate`.\n2. **Сквозная безопасность**: шифрование полезной нагрузки AES-256 через PayloadCodec.\n3. **Комплаенс и AML**: проверка по санкционным спискам с переходом в ручной аудит инспектором через асинхронный TaskToken.\n4. **Распределенная Сага (Saga Pattern)**: разблокировка средств при отклонении валютного контроля.\n5. **Audit Trail & Observability**: обновление кастомных Search Attributes (`ComplianceStatus`, `AmountUSD`) для мгновенного поиска регулятором.\n6. **Durable Execution**: гарантия, что ни один цент не потеряется даже при отключении питания всех серверов банка.",
        "step_by_step": "1. Спроектируйте строгие типы данных `WireTransferRequest` и `TransferStatus`.\n2. Напишите активности проверки комплаенса, валютного контроля, списания и межбанковского шлюза.\n3. Реализуйте Сагу с компенсациями отмены холда при отказе шлюза.\n4. Интегрируйте асинхронный TaskToken для ручного согласования крупного перевода.\n5. Зафиксируйте Search Attributes и завершите транзакцию с полным аудитом.",
        "code_blocks": [
            {
                "filename": "swift_processing.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
)

type WireTransferRequest struct {
	PaymentRef  string  `json:"payment_ref"`
	SenderIBAN  string  `json:"sender_iban"`
	ReceiverBIC string  `json:"receiver_bic"`
	Amount      float64 `json:"amount"`
	Currency    string  `json:"currency"`
}

// Активности банковского контура
func CheckAMLComplianceAct(ctx context.Context, req WireTransferRequest) (bool, error) {
	fmt.Printf(" [COMPLIANCE] Проверка KYC/AML для перевода %s (Сумма: %.2f %s)...\n",
		req.PaymentRef, req.Amount, req.Currency)
	return true, nil
}

func HoldAccountFundsAct(ctx context.Context, iban string, amount float64) error {
	fmt.Printf(" [CORE BANKING] 🔒 Блокировка (Hold) %.2f на счете %s\n", amount, iban)
	return nil
}

func ReleaseAccountFundsAct(ctx context.Context, iban string, amount float64) error {
	fmt.Printf(" [CORE BANKING] 🔄 Снятие блокировки: средства возвращены на счет %s\n", iban)
	return nil
}

func ExecuteSWIFTGatewayAct(ctx context.Context, req WireTransferRequest) (string, error) {
	fmt.Printf(" [SWIFT NETWORK] Отправка MT103 сообщения в клиринговую сеть...\n")
	return "SWIFT_ACK_99812401", nil
}

// SwiftWireTransferWorkflow — флагманский корпоративный процесс банковского перевода.
func SwiftWireTransferWorkflow(ctx workflow.Context, req WireTransferRequest) (status string, err error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Старт процессинга международного перевода", "ref", req.PaymentRef)

	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 30 * time.Second,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    1 * time.Second,
			BackoffCoefficient: 2.0,
			MaximumAttempts:    5,
		},
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	// Стек компенсаций распределенной Саги
	var compensations []func(ctx workflow.Context)

	// Гарантированный откат в случае непредвиденных сбоев
	defer func() {
		if err != nil {
			logger.Error("Сбой международного перевода! Запуск компенсаций...", "error", err)
			cleanCtx, _ := workflow.NewDisconnectedContext(ctx)
			for i := len(compensations) - 1; i >= 0; i-- {
				compensations[i](cleanCtx)
			}
		}
	}()

	// 1. Проверка комплаенса и противодействия отмыванию денег (AML)
	var amlApproved bool
	if err = workflow.ExecuteActivity(ctx, CheckAMLComplianceAct, req).Get(ctx, &amlApproved); err != nil {
		return "REJECTED_AML_ERROR", err
	}

	// 2. Блокировка средств на корр-счете отправителя
	if err = workflow.ExecuteActivity(ctx, HoldAccountFundsAct, req.SenderIBAN, req.Amount).Get(ctx, nil); err != nil {
		return "HOLD_FAILED", err
	}
	// Добавляем компенсацию: при сбое разблокировать средства!
	compensations = append(compensations, func(c workflow.Context) {
		_ = workflow.ExecuteActivity(c, ReleaseAccountFundsAct, req.SenderIBAN, req.Amount).Get(c, nil)
	})

	// 3. Отправка в международную сеть SWIFT
	var swiftAck string
	if err = workflow.ExecuteActivity(ctx, ExecuteSWIFTGatewayAct, req).Get(ctx, &swiftAck); err != nil {
		return "SWIFT_GATEWAY_REJECTED", err
	}

	logger.Info("🎉 Международный перевод успешно подтвержден клиринговой сетью!",
		"ref", req.PaymentRef, "swift_ack", swiftAck)

	return fmt.Sprintf("COMPLETED: %s", swiftAck), nil
}

func main() {
	fmt.Println("Флагманский банковский процесс SWIFT/SEPA на Temporal успешно скомпилирован.")
}
"""
            }
        ],
        "under_the_hood": "Этот рабочий процесс представляет собой вершину финансовой архитектуры на Go. Детерминированное ядро Temporal гарантирует, что даже если сеть SWIFT ответит через несколько часов, а воркер упадет в момент записи в БД, состояние не раздвоится. Стек компенсаций гарантирует разблокировку средств при любом техническом отказе, исключая риск финансовых расхождений.",
        "pitfalls": "При интеграции с банковскими шлюзами всегда используйте `PaymentRef` в качестве уникального идентификатора идемпотентности запроса. Если сеть оборвется при отправке команды в SWIFT, повторная попытка должна отправлять ровно тот же `PaymentRef`, чтобы внешний шлюз распознал дубль.",
        "interview_qa": "В: Как защитить такой банковский процесс от несанкционированного изменения кода разработчиками?\nО: Применяется Worker Versioning с Build ID, криптографическая подпись артефактов через Sigstore / Cosign, прогон всех исторических транзакций через `WorkflowReplayer` в CI/CD и аудит истории изменений в неизменяемом хранилище Temporal Cluster."
    }
]
