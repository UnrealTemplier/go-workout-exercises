import json
import subprocess
import os

def validate_go(code):
    p = subprocess.run(['gofmt', '-e'], input=code.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise ValueError(f"Go syntax error: {p.stderr.decode('utf-8')}\nCode:\n{code}")

exercises = []

# Ex 1
ex1_code = """package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

// PaymentRequest инкапсулирует данные для авторизации транзакции.
type PaymentRequest struct {
	TransactionID string
	AmountCents   int64
	Currency      string
	CustomerID    string
}

// PaymentResponse содержит результат обработки платежа шлюзом.
type PaymentResponse struct {
	Success       bool
	AuthCode      string
	TransactionID string
	ErrorReason   string
}

// PaymentGateway определяет архитектурный контракт для любого внешнего шлюза платежей.
type PaymentGateway interface {
	Authorize(ctx context.Context, req PaymentRequest) (PaymentResponse, error)
	Capture(ctx context.Context, authCode string, amountCents int64) (PaymentResponse, error)
}

// MockStripeGateway — внутренняя in-process реализация без изоляции процесса.
type MockStripeGateway struct{}

func (s *MockStripeGateway) Authorize(ctx context.Context, req PaymentRequest) (PaymentResponse, error) {
	if req.AmountCents <= 0 {
		return PaymentResponse{Success: false, ErrorReason: "invalid amount"}, errors.New("amount must be positive")
	}
	return PaymentResponse{
		Success:       true,
		AuthCode:      fmt.Sprintf("AUTH_STRIPE_%s", req.TransactionID),
		TransactionID: req.TransactionID,
	}, nil
}

func (s *MockStripeGateway) Capture(ctx context.Context, authCode string, amountCents int64) (PaymentResponse, error) {
	return PaymentResponse{
		Success:       true,
		AuthCode:      authCode,
		TransactionID: "CAP_" + authCode,
	}, nil
}

// GatewayRegistry представляет реестр расширений ядра (микроядро).
type GatewayRegistry struct {
	mu       sync.RWMutex
	gateways map[string]PaymentGateway
}

func NewGatewayRegistry() *GatewayRegistry {
	return &GatewayRegistry{gateways: make(map[string]PaymentGateway)}
}

func (r *GatewayRegistry) Register(name string, gw PaymentGateway) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.gateways[name] = gw
}

func (r *GatewayRegistry) Get(name string) (PaymentGateway, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	gw, ok := r.gateways[name]
	if !ok {
		return nil, fmt.Errorf("gateway %q not found", name)
	}
	return gw, nil
}

func main() {
	registry := NewGatewayRegistry()
	registry.Register("stripe", &MockStripeGateway{})

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	gw, err := registry.Get("stripe")
	if err != nil {
		panic(err)
	}

	resp, err := gw.Authorize(ctx, PaymentRequest{
		TransactionID: "tx_991823",
		AmountCents:   45000,
		Currency:      "RUB",
		CustomerID:    "cust_404",
	})
	if err != nil {
		fmt.Printf("Authorize failed: %v\\n", err)
		return
	}
	fmt.Printf("Платеж авторизован: %+v\\n", resp)
}
"""
validate_go(ex1_code)

exercises.append({
    "num": 1,
    "title": "Архитектура расширяемости (Extensibility Architecture)",
    "task": "Изучите фундаментальные паттерны расширяемости программных систем: микроядро (Microkernel), плагины (Plugins), межпроцессное взаимодействие (IPC) и изолированные песочницы (Sandboxes). Спроектируйте интерфейс PaymentGateway с методами Authorize и Capture, реализуйте потокобезопасный реестр GatewayRegistry и проанализируйте trade-off между изоляцией, безопасностью и latency.",
    "theory": "В архитектуре корпоративных платформ (BigTech) расширяемость (extensibility) позволяет сторонним командам и клиентам внедрять кастомную бизнес-логику без модификации и перекомпиляции ядра системы. Выделяют 4 основных уровня расширяемости:\\n1. In-process интерфейсы / микроядро (Microkernel): минимальная задержка (единицы наносекунд), но нулевая изоляция — ошибка или паника в расширении роняет весь сервис хоста.\\n2. Динамические библиотеки (.so): запуск в том же адресном пространстве, но сопряжен с жесточайшими ограничениями рантайма Go на совпадение версий компилятора и зависимостей.\\n3. Out-of-Process IPC (gRPC/UNIX domain sockets): полная изоляция сбоев памяти и независимость версий компиляторов/библиотек, но накладные расходы на контекстные переключения ядра ОС и сериализацию (~20–100 микросекунд).\\n4. WebAssembly (Wasm) Sandboxing: безопасное исполнение недоверенного кода в детерминированной виртуальной машине внутри процесса Go с задержкой в сотни наносекунд и гранулярным контролем памяти и системных вызовов.",
    "step_by_step": "1. Спроектируйте структуры PaymentRequest и PaymentResponse с детализированными полями авторизации.\\n2. Объявите контракт интерфейса PaymentGateway с поддержкой context.Context.\\n3. Разработайте MockStripeGateway с валидацией суммы транзакции.\\n4. Создайте потокобезопасный реестр GatewayRegistry с sync.RWMutex.\\n5. Зарегистрируйте реализацию и выполните авторизацию с контролем таймаута.",
    "code_blocks": [{"filename": "main.go", "lang": "go", "code": ex1_code}],
    "under_the_hood": "Внутри рантайма вызов метода через интерфейс Go (iface) транслируется в косвенный вызов функции через таблицу методов (itab). Накладные расходы составляют около 1-2 нс, что на 4-5 порядков быстрее любого межпроцессного IPC. Однако если сторонний код вызовет panic() или повредит память через CGO/unsafe, ядро упадет вместе с ним.",
    "pitfalls": "Главная ловушка in-process расширений в многопоточной среде — отсутствие контроля времени выполнения: зависшая горутина плагина может заблокировать системный поток OS-thread или исчерпать память хост-процесса.",
    "bigtech_interview": "Как в распределенных системах (например, в платежных шлюзах Ozon или биллинге Wildberries) разделяют доверенные внутренние интеграции и недоверенный пользовательский код? Почему для критичных путей применяют out-of-process IPC или Wasm вместо динамических библиотек .so?"
})

# Ex 2
ex2_code = """package main

import (
	"fmt"
	"plugin"
)

// Greeter — контракт, ожидаемый хост-приложением от плагина.
type Greeter interface {
	Greet(name string) string
}

func main() {
	// В реальной среде путь указывает на собранный артефакт plugin.so.
	// Компиляция: go build -buildmode=plugin -o plugin.so plugin.go
	soPath := "plugin.so"

	p, err := plugin.Open(soPath)
	if err != nil {
		fmt.Printf("Не удалось открыть .so (ожидаемо в песочнице без компиляции CGO): %v\\n", err)
		return
	}

	// Поиск экспортированной переменной или функции
	symGreeter, err := p.Lookup("PluginGreeter")
	if err != nil {
		fmt.Printf("Символ PluginGreeter не найден: %v\\n", err)
		return
	}

	// Приведение типов к целевому интерфейсу
	greeter, ok := symGreeter.(Greeter)
	if !ok {
		fmt.Printf("Экспортированный символ не реализует интерфейс Greeter\\n")
		return
	}

	msg := greeter.Greet("Gopher")
	fmt.Printf("Ответ от динамического плагина: %s\\n", msg)
}
"""
validate_go(ex2_code)

exercises.append({
    "num": 2,
    "title": "Стандартный пакет plugin и динамические библиотеки .so",
    "task": "Изучите работу стандартного пакета Go plugin. Напишите код хост-приложения, загружающего скомпилированную библиотеку plugin.so через plugin.Open, осуществляющего поиск экспортированного символа с помощью Lookup и вызывающего метод через интерфейсное приведение типов.",
    "theory": "Пакет plugin (появился в Go 1.8 для Linux и 1.10 для macOS) предоставляет низкоуровневый механизм динамической линковки shared objects (.so) во время выполнения программы с помощью системного вызова dlopen(3). Экспортируемые переменные и функции пакета main плагина сохраняются в таблице динамических символов ELF. Функция plugin.Open загружает образ .so в адресное пространство процесса, инициализирует пакетный рантайм и возвращает объект *plugin.Plugin. Метод Lookup(symName) ищет адрес символа через dlsym(3).",
    "step_by_step": "1. Определите интерфейс контракта Greeter с методом Greet(name string) string.\\n2. Вызовите plugin.Open для загрузки файла shared object.\\n3. Через p.Lookup найдите экспортированный символ PluginGreeter.\\n4. Выполните безопасное приведение типов (type assertion) к интерфейсу Greeter.\\n5. Вызовите логику плагина и обработайте возвращаемый результат.",
    "code_blocks": [{"filename": "host.go", "lang": "go", "code": ex2_code}],
    "under_the_hood": "При plugin.Open рантайм Go проверяет хеш интерфейса типов и структур runtime. Если структура типов в .so хотя бы на байт не совпадает со структурами хоста, происходит фатальная ошибка рантайма. Кроме того, динамически загруженный .so физически невозможно выгрузить из памяти процесса — dlclose в рантайме Go намеренно не поддерживается из-за GC и указателей на типы.",
    "pitfalls": "Для сборки плагинов строго обязательно включение CGO (CGO_ENABLED=1). Невозможно скомпилировать плагин со статической линковкой (CGO_ENABLED=0). Также пакет полностью не работает на платформе Windows.",
    "bigtech_interview": "Почему в Go стандартный пакет plugin не позволяет выгружать плагины из памяти (unloading), и как сборщик мусора (GC) связан с метаинформацией типов динамических библиотек?"
})

# Ex 3
ex3_code = """package main

import (
	"fmt"
	"runtime"
)

// LimitationReport документирует критические архитектурные недостатки пакета plugin.
type LimitationReport struct {
	Requirement string
	Consequence string
	ProductionImpact string
}

func GetPluginLimitations() []LimitationReport {
	return []LimitationReport{
		{
			Requirement:      "Строго идентичная версия компилятора Go",
			Consequence:      "Хост и .so должны быть собраны ровно одним бинарником go (вплоть до патч-версии go1.22.4)",
			ProductionImpact: "Крах сборки при малейшем обновлении CI/CD пайплайна",
		},
		{
			Requirement:      "Идентичные версии общих зависимостей",
			Consequence:      "Если хост использует libA v1.2.0, а плагин скомпилирован с v1.2.1, plugin.Open завершится ошибкой",
			ProductionImpact: "Dependency hell: невозможно обновлять библиотеки независимо",
		},
		{
			Requirement:      "Одинаковые флаги сборки и CGO_ENABLED=1",
			Consequence:      "Обязательно наличие GCC/Clang; невозможна статическая кросс-компиляция",
			ProductionImpact: "Большие docker-образы, уязвимости C-библиотек, сложность сборки",
		},
		{
			Requirement:      "Отсутствие dlclose (невозможность выгрузки)",
			Consequence:      "Все загруженные модули навсегда остаются в оперативной памяти процесса",
			ProductionImpact: "Утечка памяти при горячем обновлении плагинов (Hot-Reload)",
		},
		{
			Requirement:      "Отсутствие поддержки Windows",
			Consequence:      "Пакет plugin возвращает ошибку на этапе компиляции на платформе Windows",
			ProductionImpact: "Невозможность распространять кроссплатформенные CLI-утилиты",
		},
	}
}

func main() {
	fmt.Printf("Анализ пакета Go plugin на платформе %s/%s:\\n", runtime.GOOS, runtime.GOARCH)
	for i, report := range GetPluginLimitations() {
		fmt.Printf("%d. [%s]\\n   Причина: %s\\n   Влияние на прод: %s\\n",
			i+1, report.Requirement, report.Consequence, report.ProductionImpact)
	}
}
"""
validate_go(ex3_code)

exercises.append({
    "num": 3,
    "title": "Фатальные ограничения стандартного пакета plugin",
    "task": "Проанализируйте, почему стандартный пакет plugin практически не используется в production. Напишите диагностическую утилиту, документирующую пять критических ограничений: требование строго одинаковой версии компилятора, идентичных версий зависимостей, одинаковых build tags/флагов, обязательного наличия CGO, отсутствия выгрузки из памяти и отсутствия поддержки Windows.",
    "theory": "Стандартный пакет plugin в Go страдает от фундаментальной проблемы хрупкости ABI (Application Binary Interface). В Go нет стабильного C++-подобного ABI между релизами компилятора. Рантайм Go проверяет совпадение хешей символов и типов зависимостей. Если хост скомпилирован с флагом -tags prod, а плагин без него, или версии indirect-зависимостей расходятся, plugin.Open вернет ошибку вида: 'plugin was built with a different version of package X'. Кроме того, рантайм Go не умеет безопасно выгружать модули из-за того, что указатели на типы и структуры метаданных интерфейсов регистрируются глобально в runtime-heap, и выгрузка кода привела бы к висячим указателям (dangling pointers) при работе Garbage Collector.",
    "step_by_step": "1. Сформируйте структуру LimitationReport для классификации архитектурных проблем.\\n2. Задокументируйте требования к одинаковости компилятора и зависимостей.\\n3. Опишите влияние отсутствия механизма dlclose на утечки памяти при Hot Reload.\\n4. Выведите сводный инженерный отчет для аудита платформы.",
    "code_blocks": [{"filename": "limitations.go", "lang": "go", "code": ex3_code}],
    "under_the_hood": "При вызове plugin.Open рантайм выполняет функцию runtime.pluginOpen. Внутри нее сверяются хеши структуры runtime.modulehash. Если хеш модуля в плагине не совпадает с хешем модуля в хосте с точностью до бита, возвращается ошибка 'plugin was built with a different version of package'.",
    "pitfalls": "Попытка реализовать плагины через .so для корпоративной платформы с открытым маркетплейсом плагинов гарантированно приводит к невозможности их сборки сторонними разработчиками без предоставления точного Docker-образа сборочного окружения хоста.",
    "bigtech_interview": "Почему такие популярные инструменты экосистемы Go, как Terraform, Vault, Kubernetes CNI и Envoy, категорически отказались от стандартного пакета plugin в пользу внешних процессов (gRPC IPC) или WebAssembly?"
})

# Ex 4
ex4_code = """package main

import (
	"bufio"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os/exec"
	"sync"
	"time"
)

// Request — контракт запроса через stdin дочернего процесса.
type Request struct {
	ID     string `json:"id"`
	Method string `json:"method"`
	Input  string `json:"input"`
}

// Response — контракт ответа через stdout дочернего процесса.
type Response struct {
	ID     string `json:"id"`
	Result string `json:"result"`
	Error  string `json:"error,omitempty"`
}

// ProcessPlugin управляет жизненным циклом внешнего процесса-плагина.
type ProcessPlugin struct {
	cmd    *exec.Cmd
	stdin  io.WriteCloser
	stdout *bufio.Scanner
	mu     sync.Mutex
}

func NewProcessPlugin(command string, args ...string) (*ProcessPlugin, error) {
	cmd := exec.Command(command, args...)
	stdin, err := cmd.StdinPipe()
	if err != nil {
		return nil, fmt.Errorf("stdin pipe failed: %w", err)
	}

	stdoutPipe, err := cmd.StdoutPipe()
	if err != nil {
		return nil, fmt.Errorf("stdout pipe failed: %w", err)
	}

	if err := cmd.Start(); err != nil {
		return nil, fmt.Errorf("command start failed: %w", err)
	}

	return &ProcessPlugin{
		cmd:    cmd,
		stdin:  stdin,
		stdout: bufio.NewScanner(stdoutPipe),
	}, nil
}

func (p *ProcessPlugin) Execute(ctx context.Context, req Request) (Response, error) {
	p.mu.Lock()
	defer p.mu.Unlock()

	data, err := json.Marshal(req)
	if err != nil {
		return Response{}, err
	}
	data = append(data, '\\n')

	if _, err := p.stdin.Write(data); err != nil {
		return Response{}, fmt.Errorf("failed to write to child stdin: %w", err)
	}

	// Читаем ответ с поддержкой отмены контекста
	respChan := make(chan Response, 1)
	errChan := make(chan error, 1)

	go func() {
		if p.stdout.Scan() {
			line := p.stdout.Bytes()
			var resp Response
			if err := json.Unmarshal(line, &resp); err != nil {
				errChan <- fmt.Errorf("json unmarshal failed: %w", err)
				return
			}
			respChan <- resp
		} else {
			if err := p.stdout.Err(); err != nil {
				errChan <- err
			} else {
				errChan <- io.EOF
			}
		}
	}()

	select {
	case <-ctx.Done():
		return Response{}, ctx.Err()
	case err := <-errChan:
		return Response{}, err
	case resp := <-respChan:
		if resp.Error != "" {
			return resp, errors.New(resp.Error)
		}
		return resp, nil
	}
}

func (p *ProcessPlugin) Close() error {
	p.mu.Lock()
	defer p.mu.Unlock()
	_ = p.stdin.Close()
	return p.cmd.Wait()
}

func main() {
	fmt.Println("Демонстрация концепции Out-of-Process IPC плагина через stdin/stdout")
}
"""
validate_go(ex4_code)

exercises.append({
    "num": 4,
    "title": "Внепроцессные плагины через IPC (Out-of-Process Plugins)",
    "task": "Спроектируйте архитектуру плагинов, работающих как независимые процессы операционной системы. Реализуйте структуру ProcessPlugin, запускающую дочерний процесс через os/exec, передающую JSON-запросы в поток stdin и построчно считывающую JSON-ответы из stdout с потокобезопасностью и поддержкой context.Context.",
    "theory": "Паттерн Out-of-Process Plugins переносит код плагина в изолированный процесс ОС. Хост и плагин взаимодействуют через межпроцессное взаимодействие (IPC): стандартные дескрипторы ввода-вывода (stdin/stdout pipes) или UNIX Domain Sockets. Ключевые преимущества:\\n1. Полная изоляция памяти: крах или Segmentation Fault плагина не нарушает стабильность хоста.\\n2. Полиглотичность: плагин может быть написан на Go, Rust, Python или Node.js.\\n3. Независимость зависимостей: хост и плагин компилируются совершенно разными версиями компиляторов и библиотек.\\n4. Мониторинг ресурсов: ядро ОС позволяет вешать cgroups на процесс плагина для ограничения CPU и RAM.",
    "step_by_step": "1. Объявите структуры Request и Response для JSON-RPC протокола.\\n2. Создайте структуру ProcessPlugin, инкапсулирующую exec.Cmd, stdin и stdout.\\n3. Реализуйте метод Execute с синхронизацией sync.Mutex для предотвращения перемешивания запросов.\\n4. Организуйте горутину считывания ответа со сканера с контролем select и ctx.Done().\\n5. Реализуйте метод Close для корректного освобождения файловых дескрипторов и ожидания завершения процесса.",
    "code_blocks": [{"filename": "ipc_plugin.go", "lang": "go", "code": ex4_code}],
    "under_the_hood": "При создании pipe через os/exec создается пара анонимных каналов pipe(2) в ядре Linux. Запись в stdin блокируется, если заполнен буфер канала (по умолчанию 64 КБ в Linux). Построчное чтение bufio.Scanner гарантирует корректное кадрирование сообщений (framing) без необходимости ручного парсинга длины заголовка.",
    "pitfalls": "Если дочерний процесс начнет писать отладочный мусор в stdout вместо stderr, JSON-парсер хоста сломается. Всегда настраивайте cmd.Stderr = os.Stderr для отделения логов от протокольных данных.",
    "bigtech_interview": "В чем разница между анонимными пайпами (pipe2) и локальными UNIX Domain Sockets (AF_UNIX) при реализации IPC плагинов с высокой пропускной способностью? Какой механизм обеспечивает полнодуплексный обмен?"
})

# Ex 5
ex5_code = """package main

import (
	"fmt"
	"os"
)

// HandshakeConfig инкапсулирует параметры согласования подключения хоста и плагина.
type HandshakeConfig struct {
	ProtocolVersion  uint
	MagicCookieKey   string
	MagicCookieValue string
}

// SharedHandshake — эталонная конфигурация рукопожатия HashiCorp go-plugin.
var SharedHandshake = HandshakeConfig{
	ProtocolVersion:  1,
	MagicCookieKey:   "APP_PLUGIN_MAGIC_COOKIE",
	MagicCookieValue: "44e28e4e-0a56-42bb-9279-d6e06cfabefb",
}

// ValidateHandshakeEnvironment проверяет наличие магической куки в окружении процесса.
func ValidateHandshakeEnvironment(cfg HandshakeConfig) error {
	val := os.Getenv(cfg.MagicCookieKey)
	if val == "" {
		return fmt.Errorf("переменная окружения %s не найдена: плагин не может быть запущен напрямую", cfg.MagicCookieKey)
	}
	if val != cfg.MagicCookieValue {
		return fmt.Errorf("неверное значение магической куки: получено %q, ожидалось %q", val, cfg.MagicCookieValue)
	}
	return nil
}

func main() {
	// Имитация запуска плагина хост-процессом
	os.Setenv(SharedHandshake.MagicCookieKey, SharedHandshake.MagicCookieValue)

	if err := ValidateHandshakeEnvironment(SharedHandshake); err != nil {
		fmt.Printf("Ошибка рукопожатия: %v\\n", err)
		return
	}
	fmt.Printf("Рукопожатие успешно! Версия протокола: %d, Магический ключ проверен.\\n", SharedHandshake.ProtocolVersion)
}
"""
validate_go(ex5_code)

exercises.append({
    "num": 5,
    "title": "Введение во фреймворк HashiCorp go-plugin",
    "task": "Изучите архитектуру библиотеки hashicorp/go-plugin (используемой в Terraform, Vault, Nomad). Разберите структуру рукопожатия HandshakeConfig: магический ключ (MagicCookieKey), значение куки и версию протокола. Напишите алгоритм валидации окружения, предотвращающий случайный запуск бинарника плагина пользователем вне хоста.",
    "theory": "Библиотека hashicorp/go-plugin — золотой стандарт out-of-process плагинов в экосистеме Go. Плагины являются самостоятельными бинарниками, запускаемыми хостом. Коммуникация происходит по gRPC или net/rpc поверх UNIX сокетов (или именованных пайпов на Windows). Для защиты от непреднамеренного выполнения плагина пользователем (например, кликом в проводнике или в терминале без хоста) используется HandshakeConfig. Хост передает случайный секрет (Magic Cookie) через переменные окружения дочернего процесса. Плагин при старте проверяет наличие куки, и если она отсутствует — немедленно завершается с ошибкой.",
    "step_by_step": "1. Спроектируйте структуру HandshakeConfig с полями ProtocolVersion, MagicCookieKey и MagicCookieValue.\\n2. Создайте глобальную константу SharedHandshake для хоста и плагина.\\n3. Реализуйте функцию ValidateHandshakeEnvironment, инспектирующую переменные окружения.\\n4. Проверьте поведение как при корректной установке переменной, так и при ее отсутствии.",
    "code_blocks": [{"filename": "handshake.go", "lang": "go", "code": ex5_code}],
    "under_the_hood": "Помимо переменной окружения, плагин в go-plugin выводит в stdout специальную строку вида: '1|1|unix|/tmp/plugin123.sock|grpc|'. Хост считывает эту строку, извлекает путь к созданному UNIX сокету и подключается к нему gRPC клиентом, после чего закрывает захват stdout.",
    "pitfalls": "Магическая кука не является криптографической защитой от злоумышленников (так как любой локальный процесс может прочитать окружение через /proc/$PID/environ). Ее цель — защита от случайного запуска человеком и проверка согласованности протоколов.",
    "bigtech_interview": "Как HashiCorp go-plugin организует безопасный gRPC-транспорт между хостом и плагином? Используется ли там mTLS (Mutual TLS) с ephemeral-сертификатами, генерируемыми на лету при старте процесса?"
})

# Ex 6
ex6_code = """package main

import (
	"context"
	"fmt"
	"net"

	"google.golang.org/grpc"
)

// DataRequest представляет контракт входных данных.
type DataRequest struct {
	Payload []byte
	Format  string
}

// DataResponse представляет контракт результата обработки.
type DataResponse struct {
	Transformed []byte
	Records     int64
}

// DataProcessor — Go-интерфейс, который видят хост и бизнес-логика.
type DataProcessor interface {
	ProcessData(ctx context.Context, req DataRequest) (DataResponse, error)
}

// GRPCClient реализует DataProcessor со стороны хост-приложения.
type GRPCClient struct {
	conn *grpc.ClientConn
}

func (c *GRPCClient) ProcessData(ctx context.Context, req DataRequest) (DataResponse, error) {
	// В реальном приложении здесь вызывается сгенерированный gRPC стаб pb.NewDataProcessorClient(c.conn)
	return DataResponse{
		Transformed: append([]byte("PROCESSED:"), req.Payload...),
		Records:     1,
	}, nil
}

// GRPCServer реализует gRPC сервис на стороне сервера плагина.
type GRPCServer struct {
	Impl DataProcessor
}

func (s *GRPCServer) HandleProcess(ctx context.Context, req DataRequest) (DataResponse, error) {
	return s.Impl.ProcessData(ctx, req)
}

func main() {
	client := &GRPCClient{}
	resp, err := client.ProcessData(context.Background(), DataRequest{
		Payload: []byte("col1,col2,col3"),
		Format:  "csv",
	})
	if err != nil {
		panic(err)
	}
	fmt.Printf("Результат gRPC-адаптера плагина: Records=%d, Data=%s\\n", resp.Records, string(resp.Transformed))
}
"""
validate_go(ex6_code)

exercises.append({
    "num": 6,
    "title": "Проектирование Protobuf контракта для go-plugin",
    "task": "Спроектируйте архитектурный мост для интеграции go-plugin с gRPC. Объявите интерфейс DataProcessor, клиентский адаптер GRPCClient и серверный адаптер GRPCServer, транслирующие вызовы между идиоматичными типами Go и gRPC структурами.",
    "theory": "Пакет go-plugin абстрагирует транспортный протокол gRPC с помощью интерфейса plugin.Plugin и plugin.GRPCPlugin. Разработчик определяет стандартный интерфейс Go (например, DataProcessor). Чтобы плагин работал по gRPC, необходимо реализовать два адаптера:\\n1. GRPCServer(broker, server): регистрирует gRPC сервис на сервере плагина, делегируя вызовы реальной реализации интерфейса.\\n2. GRPCClient(ctx, broker, clientConn): оборачивает сгенерированный gRPC-клиент и реализует интерфейс DataProcessor для хоста.\\nБлагодаря этому хост вызывает методы плагина как обычный Go-интерфейс, не зная деталей gRPC.",
    "step_by_step": "1. Определите интерфейс DataProcessor с контекстом и структурами данных.\\n2. Реализуйте GRPCClient, скрывающий сетевые вызовы gRPC за локальным интерфейсом.\\n3. Создайте GRPCServer, принимающий сетевые запросы и перенаправляющий их в бизнес-логику.\\n4. Напишите тест вызова через адаптер.",
    "code_blocks": [{"filename": "plugin_bridge.go", "lang": "go", "code": ex6_code}],
    "under_the_hood": "Благодаря паттерну 'Адаптер' (Adapter Pattern), бизнес-логика хоста и плагина полностью отвязана от зависимостей protobuf и grpc. Вы можете заменить gRPC на JSON-RPC или внутрипроцессные каналы без изменения единой строчки вызывающего кода хоста.",
    "pitfalls": "Частая ошибка — передача каналов chan T или замыканий func() через интерфейс плагина. Поскольку вызовы идут по сети через gRPC, параметры должны быть строго сериализуемы в Protobuf.",
    "bigtech_interview": "Почему передача потоковых данных (Streaming) в go-plugin требует осторожности с буферизацией gRPC, и как настроить максимальный размер сообщения MaxRecvMsgSize при обработке гигабайтных файлов?"
})

# Ex 7
ex7_code = """package main

import (
	"context"
	"fmt"
	"strings"
)

// CSVProcessorImpl — реализация бизнес-логики внутри бинарника плагина.
type CSVProcessorImpl struct{}

func (p *CSVProcessorImpl) ProcessCSV(ctx context.Context, rawCSV string) ([]string, error) {
	lines := strings.Split(rawCSV, "\\n")
	var cleaned []string
	for _, line := range lines {
		trimmed := strings.TrimSpace(line)
		if trimmed != "" && !strings.HasPrefix(trimmed, "#") {
			cleaned = append(cleaned, strings.ToUpper(trimmed))
		}
	}
	return cleaned, nil
}

// PluginServerConfig описывает параметры старта плагина.
type PluginServerConfig struct {
	SocketType string
	Address    string
	PluginName string
}

func StartPluginServer(cfg PluginServerConfig, impl *CSVProcessorImpl) {
	fmt.Printf("Плагин %s инициализирован на %s://%s\\n", cfg.PluginName, cfg.SocketType, cfg.Address)
	// В HashiCorp go-plugin вызывается:
	// plugin.Serve(&plugin.ServeConfig{
	//     HandshakeConfig: handshakeConfig,
	//     Plugins: map[string]plugin.Plugin{ "csv_processor": &CSVPlugin{Impl: impl} },
	//     GRPCServer: plugin.DefaultGRPCServer,
	// })
}

func main() {
	processor := &CSVProcessorImpl{}
	res, err := processor.ProcessCSV(context.Background(), "id,name\\n# comment\\n101,order_created\\n102,order_paid")
	if err != nil {
		panic(err)
	}
	fmt.Printf("Очищенные строки плагином: %v\\n", res)

	StartPluginServer(PluginServerConfig{
		SocketType: "unix",
		Address:    "/tmp/plugin_csv.sock",
		PluginName: "csv_processor",
	}, processor)
}
"""
validate_go(ex7_code)

exercises.append({
    "num": 7,
    "title": "Реализация бинарного сервера плагина",
    "task": "Реализуйте независимый бинарный сервер плагина plugin-csv. Напишите логику очистки CSV данных, исключающую пустые строки и комментарии, и структуру конфигурации сервера плагина, моделирующую вызов plugin.Serve из фреймворка go-plugin.",
    "theory": "Бинарник плагина в go-plugin компилируется как стандартный исполняемый файл main (go build -o plugin-csv). Точкой входа является функция plugin.Serve(). При запуске она выполняет следующие действия:\\n1. Проверяет HandshakeConfig через переменные окружения.\\n2. Создает слушатель локального сокета (UNIX domain socket в /tmp на Linux/macOS или именованный пайп на Windows).\\n3. Генерирует одноразовые TLS-сертификаты для mTLS шифрования локального трафика между хостом и плагином.\\n4. Запускает gRPC сервер с зарегистрированными плагинами.\\n5. Выводит в stdout хоста метаданные подключения и переходит в режим блокирующей обработки запросов.",
    "step_by_step": "1. Создайте структуру CSVProcessorImpl с методом обработки сырых данных.\\n2. Реализуйте фильтрацию комментариев и нормализацию строк.\\n3. Сформируйте конфигурацию PluginServerConfig.\\n4. Смоделируйте инициализацию сокета и логику ожидания запросов.",
    "code_blocks": [{"filename": "plugin_main.go", "lang": "go", "code": ex7_code}],
    "under_the_hood": "Сервер плагина слушает системные сигналы SIGINT/SIGTERM. Когда хост-процесс завершается или закрывает канал связи, библиотека плагина перехватывает обрыв сокета и вызывает graceful shutdown gRPC-сервера, удаляя временный .sock файл с файловой системы.",
    "pitfalls": "Если в main() плагина написать fmt.Println(\"Hello\"), эти байты попадут в stdout, который слушает хост для получения адреса сокета. Это приведет к ошибке парсинга хостом 'Unrecognized handshake'. Все логирование в плагине должно идти строго в stderr или через специальный hclog.Logger.",
    "bigtech_interview": "Почему для IPC между локальными процессами на Linux выбирают UNIX Domain Socket вместо TCP localhost? Каковы преимущества с точки зрения безопасности файловых прав (chmod) и производительности TCP-стека (отсутствие loopback IP routing, TCP checksums и ACK)?"
})

# Ex 8
ex8_code = """package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// PluginClientManager управляет жизненным циклом подключения к дочернему процессу.
type PluginClientManager struct {
	mu        sync.RWMutex
	binary    string
	isRunning bool
	client    *MockGRPCClient
}

type MockGRPCClient struct {
	Endpoint string
}

func (c *MockGRPCClient) CallMethod(ctx context.Context, input string) (string, error) {
	return fmt.Sprintf("Processed[%s] at %s", input, c.Endpoint), nil
}

func NewPluginClientManager(binaryPath string) *PluginClientManager {
	return &PluginClientManager{binary: binaryPath}
}

func (m *PluginClientManager) Start(ctx context.Context) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.isRunning {
		return nil
	}

	// Имитация запуска процесса и подключения по UNIX сокету:
	// client := plugin.NewClient(&plugin.ClientConfig{
	//     HandshakeConfig: handshakeConfig,
	//     Plugins: pluginMap,
	//     Cmd: exec.Command(m.binary),
	//     AllowedProtocols: []plugin.Protocol{plugin.ProtocolGRPC},
	// })
	m.client = &MockGRPCClient{Endpoint: "/tmp/mock_plugin.sock"}
	m.isRunning = true
	fmt.Printf("Плагин %s успешно запущен и соединен по UNIX-сокету\\n", m.binary)
	return nil
}

func (m *PluginClientManager) Execute(ctx context.Context, input string) (string, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if !m.isRunning || m.client == nil {
		return "", fmt.Errorf("плагин %s не запущен", m.binary)
	}
	return m.client.CallMethod(ctx, input)
}

func (m *PluginClientManager) Stop() {
	m.mu.Lock()
	defer m.mu.Unlock()

	if !m.isRunning {
		return
	}
	// m.client.Kill() отправляет SIGKILL процессу плагина и чистит сокет
	m.isRunning = false
	m.client = nil
	fmt.Printf("Плагин %s корректно остановлен (killed)\\n", m.binary)
}

func main() {
	mgr := NewPluginClientManager("./plugin-csv")
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	if err := mgr.Start(ctx); err != nil {
		panic(err)
	}
	defer mgr.Stop()

	res, err := mgr.Execute(ctx, "record_123")
	if err != nil {
		panic(err)
	}
	fmt.Printf("Ответ от менеджера плагинов: %s\\n", res)
}
"""
validate_go(ex8_code)

exercises.append({
    "num": 8,
    "title": "Хост-приложение: обнаружение и запуск плагина",
    "task": "Напишите архитектуру управления плагинами на стороне хост-приложения. Реализуйте структуру PluginClientManager, инкапсулирующую запуск дочернего процесса, подключение по сокету, выполнение запросов с контролем таймаута и гарантированное освобождение ресурсов через Kill.",
    "theory": "Хост-приложение управляет жизненным циклом плагина через объект plugin.Client. При вызове client.Start() или client.Client() хост выполняет fork/exec указанного бинарного файла плагина, перехватывает дескриптор stdout, дожидается завершения рукопожатия и строки с адресом сокета. Затем хост устанавливает gRPC соединение и возвращает RPC-клиент. Важнейшая обязанность хоста — вызов client.Kill() при завершении работы или деинициализации плагина. Функция Kill отправляет сигнал SIGTERM/SIGKILL процессу плагина, ждет освобождения дескрипторов и удаляет временные сокеты.",
    "step_by_step": "1. Спроектируйте PluginClientManager с RWMutex для защиты состояния процесса.\\n2. Реализуйте метод Start для запуска и установки соединения.\\n3. Добавьте метод Execute с безопасной валидацией доступности плагина.\\n4. Реализуйте Stop() с гарантированным вызовом Kill() для предотвращения процессов-зомби.",
    "code_blocks": [{"filename": "host_manager.go", "lang": "go", "code": ex8_code}],
    "under_the_hood": "Если хост-приложение аварийно завершится без вызова Kill(), плагин не останется висеть вечно: библиотека go-plugin запускает внутри плагина фоновый монитор ppid (parent PID). Если родительский процесс погибает, дочерний плагин обнаруживает смену PPID на 1 (init/systemd) и выполняет самоубийство os.Exit(0).",
    "pitfalls": "Забытый defer client.Kill() при раннем выходе из функции или ошибке инициализации оставляет висячие дочерние процессы (orphaned processes), потребляющие оперативную память и файловые дескрипторы.",
    "bigtech_interview": "Как в Terraform реализован механизм плагинов-провайдеров (AWS, GCP, Kubernetes)? Почему Terraform запускает отдельный бинарный процесс для каждого провайдера и как он решает проблему сотен параллельных RPC-вызовов?"
})

# Ex 9
ex9_code = """package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

var ErrPluginCrashed = errors.New("rpc error: code = Unavailable desc = transport is closing")

// ResilientHostSupervisor обеспечивает автоматический перезапуск упавшего плагина.
type ResilientHostSupervisor struct {
	mu           sync.Mutex
	restarts     atomic.Int64
	isAlive      bool
	simulateFail bool
}

func NewResilientHostSupervisor() *ResilientHostSupervisor {
	return &ResilientHostSupervisor{isAlive: true}
}

func (s *ResilientHostSupervisor) Call(ctx context.Context, req string) (string, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if !s.isAlive || s.simulateFail {
		s.isAlive = false
		return "", ErrPluginCrashed
	}
	return fmt.Sprintf("Success[%s]", req), nil
}

func (s *ResilientHostSupervisor) TriggerCrash() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.simulateFail = true
	s.isAlive = false
	fmt.Println("--> Смоделирован критический сбой плагина (SIGSEGV/Panic)!")
}

func (s *ResilientHostSupervisor) Restart() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.simulateFail = false
	s.isAlive = true
	s.restarts.Add(1)
	fmt.Printf("--> Supervisor: плагин успешно перезапущен (всего рестартов: %d)\\n", s.restarts.Load())
}

// ExecuteWithRetry выполняет вызов к плагину с автоматическим перезапуском при крахе.
func (s *ResilientHostSupervisor) ExecuteWithRetry(ctx context.Context, req string) (string, error) {
	res, err := s.Call(ctx, req)
	if err != nil {
		if errors.Is(err, ErrPluginCrashed) {
			fmt.Println("Хост перехватил крах плагина. Запуск процедуры восстановления...")
			s.Restart()
			// Повторная попытка после рестарта
			return s.Call(ctx, req)
		}
		return "", err
	}
	return res, nil
}

func main() {
	supervisor := NewResilientHostSupervisor()
	ctx := context.Background()

	// 1. Нормальный вызов
	res1, err := supervisor.ExecuteWithRetry(ctx, "req_1")
	fmt.Printf("Результат 1: %s, err=%v\\n", res1, err)

	// 2. Симулируем крах процесса плагина
	supervisor.TriggerCrash()

	// 3. Вызов должен восстановиться без падения хоста
	res2, err := supervisor.ExecuteWithRetry(ctx, "req_2")
	fmt.Printf("Результат 2 после сбоя: %s, err=%v\\n", res2, err)
}
"""
validate_go(ex9_code)

exercises.append({
    "num": 9,
    "title": "Изоляция сбоев: защита хоста от аварийного падения плагина",
    "task": "Смоделируйте аварийное падение плагина (Panic, SIGSEGV) и докажите, что хост-процесс сохраняет стабильность. Реализуйте супервизор ResilientHostSupervisor, перехватывающий сетевую ошибку codes.Unavailable, перезапускающий дочерний процесс и повторяющий операцию.",
    "theory": "Ключевое преимущество Out-of-Process плагинов перед динамическими библиотеками (.so) — жесткая изоляция сбоев на уровне ядра операционной системы (Fault Domain Isolation). Если плагин совершает разыменование нулевого указателя (Segmentation Fault), вызывает C-функцию с переполнением буфера или паникует: падает исключительно процесс плагина. Хост-приложение не падает, а получает ошибку закрытия сетевого сокета (EOF или codes.Unavailable). Паттерн Supervisor отслеживает такие события, автоматически перезапускает бинарник плагина и возвращает систему в рабочее состояние.",
    "step_by_step": "1. Объявите ошибку ErrPluginCrashed, эквивалентную gRPC transport closed.\\n2. Создайте ResilientHostSupervisor с атомарным счетчиком перезапусков.\\n3. Реализуйте метод TriggerCrash для имитации падения дочернего процесса.\\n4. Напишите метод ExecuteWithRetry, перехватывающий сбой, вызывающий Restart() и прозрачно повторяющий запрос.",
    "code_blocks": [{"filename": "supervisor.go", "lang": "go", "code": ex9_code}],
    "under_the_hood": "При падении процесса ядро ОС отправляет сигнал SIGCHLD родительскому процессу хоста. Функция cmd.Wait() разблокируется и возвращает ExitError с кодом завершения. При этом сокет закрывается на стороне ядра, вызывая немедленный сброс незавершенных RPC вызовов.",
    "pitfalls": "Остерегайтесь бесконечного цикла перезапусков (CrashLoopBackOff). Если запрос содержит 'ядовитую пилюлю' (poison pill), вызывающую панику плагина на одних и тех же входных данных, супервизор должен ввести экспоненциальную задержку и прерывать попытки после N неудач.",
    "bigtech_interview": "Как устроена изоляция процессов плагинов в Envoy (Wasm filter crash) и Nginx? Почему архитектура с несколькими воркерами или отдельными процессами плагинов делает шлюзы устойчивыми к DoS-атакам на уязвимости в коде плагинов?"
})

# Ex 10
ex10_code = """package main

import (
	"errors"
	"fmt"
)

var ErrIncompatibleVersion = errors.New("incompatible protocol version")

// VersionedNegotiator управляет согласованием версий между хостом и подключаемым плагином.
type VersionedNegotiator struct {
	SupportedVersions map[uint]string
}

func NewVersionedNegotiator(versions ...uint) *VersionedNegotiator {
	vmap := make(map[uint]string)
	for _, v := range versions {
		vmap[v] = fmt.Sprintf("v%d-stable", v)
	}
	return &VersionedNegotiator{SupportedVersions: vmap}
}

// Negotiate проверяет совместимость версий протокола плагина и хоста.
func (n *VersionedNegotiator) Negotiate(pluginVersion uint) (string, error) {
	desc, ok := n.SupportedVersions[pluginVersion]
	if !ok {
		return "", fmt.Errorf("%w: плагин запросил v%d, хост поддерживает только %v",
			ErrIncompatibleVersion, pluginVersion, n.SupportedVersions)
	}
	return desc, nil
}

func main() {
	// Хост поддерживает версии протокола 2 и 3
	host := NewVersionedNegotiator(2, 3)

	// Тест 1: плагин со старой версией 1
	_, err := host.Negotiate(1)
	fmt.Printf("Попытка подключения плагина v1: %v\\n", err)

	// Тест 2: плагин с поддерживаемой версией 2
	desc, err := host.Negotiate(2)
	if err != nil {
		panic(err)
	}
	fmt.Printf("Успешное согласование плагина v2: протокол %s\\n", desc)
}
"""
validate_go(ex10_code)

exercises.append({
    "num": 10,
    "title": "Версионирование протокола плагинов (Protocol Versioning)",
    "task": "Реализуйте механизм версионирования протокола между хостом и плагинами. Напишите структуру VersionedNegotiator, которая отклоняет устаревшие или несовместимые версии плагинов с ошибкой ErrIncompatibleVersion и поддерживает параллельную работу нескольких версий контракта.",
    "theory": "В распределенных системах и платформенных продуктах (например, плагины для Vault или Terraform) хост и плагины развиваются с разной скоростью. Изменение Protobuf-схемы или сигнатур методов может сломать обратную совместимость. Механизм Protocol Versioning в go-plugin позволяет плагину объявлять поддерживаемую версию (например, Version = 2), а хосту — поддерживать карту версий map[uint]plugin.Plugin. Если плагин предоставляет более старую версию, хост использует адаптер обратной совместимости. Если версия не поддерживается вовсе, рукопожатие немедленно прерывается без отправки некорректных данных.",
    "step_by_step": "1. Объявите ошибку ErrIncompatibleVersion.\\n2. Реализуйте VersionedNegotiator со списком поддерживаемых версий.\\n3. Напишите метод Negotiate для валидации версии плагина.\\n4. Протестируйте поведение при несовпадении версий и при успешном согласовании.",
    "code_blocks": [{"filename": "negotiator.go", "lang": "go", "code": ex10_code}],
    "under_the_hood": "В go-plugin согласование происходит в момент чтения заголовка: хост передает список поддерживаемых версий, плагин выбирает максимальную пересекающуюся версию. Если пересечения нет, плагин не запускает gRPC сервер, а выходит с ненулевым кодом завершения.",
    "pitfalls": "Ловушка версионирования — смешивание версий Protobuf сообщений и версии самого протокола взаимодействия (транспорта). Версионируйте как транспортный handshake, так и схемы gRPC пакетов (например, package myplugin.v1 vs myplugin.v2).",
    "bigtech_interview": "Как в Google и Yandex поддерживают эволюцию gRPC API плагинов без ломающих изменений? Почему добавление новых полей в Protobuf безопасно, а изменение номеров тегов (tag numbers) — катастрофично?"
})

# Ex 11
ex11_code = """package main

import (
	"context"
	"fmt"
	"sync"
)

// HostCallbackService — интерфейс сервиса хоста, к которому плагин может обращаться назад.
type HostCallbackService interface {
	CheckPermission(ctx context.Context, userID, action string) (bool, error)
	LogAudit(ctx context.Context, event string) error
}

// MockHostService реализует сервис хоста.
type MockHostService struct {
	mu     sync.Mutex
	audits []string
}

func (s *MockHostService) CheckPermission(ctx context.Context, userID, action string) (bool, error) {
	if userID == "admin" {
		return true, nil
	}
	return false, nil
}

func (s *MockHostService) LogAudit(ctx context.Context, event string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.audits = append(s.audits, event)
	fmt.Printf("[Host Audit Log]: %s\\n", event)
	return nil
}

// PluginContext эмулирует обратный вызов из плагина в хост через двусторонний канал.
type PluginContext struct {
	HostAPI HostCallbackService
}

func (p *PluginContext) RunPluginTask(ctx context.Context, user string) error {
	// Плагин обращается к хосту за проверкой прав
	allowed, err := p.HostAPI.CheckPermission(ctx, user, "execute_report")
	if err != nil {
		return err
	}
	if !allowed {
		_ = p.HostAPI.LogAudit(ctx, fmt.Sprintf("Отказ в доступе пользователю %s", user))
		return fmt.Errorf("доступ запрещен для %s", user)
	}

	_ = p.HostAPI.LogAudit(ctx, fmt.Sprintf("Пользователь %s успешно выполнил задачу", user))
	return nil
}

func main() {
	hostService := &MockHostService{}
	pluginInstance := &PluginContext{HostAPI: hostService}

	ctx := context.Background()
	_ = pluginInstance.RunPluginTask(ctx, "guest")
	_ = pluginInstance.RunPluginTask(ctx, "admin")
}
"""
validate_go(ex11_code)

exercises.append({
    "num": 11,
    "title": "Двусторонняя коммуникация: вызов функций хоста из плагина (Callbacks)",
    "task": "Спроектируйте архитектуру обратных вызовов (Callbacks), позволяющую внешнему плагину обращаться назад к хост-приложению (например, для проверки прав доступа или записи в лог аудита). Реализуйте интерфейс HostCallbackService и продемонстрируйте вызовы из плагина к хосту.",
    "theory": "Во многих сценариях плагин не просто получает входные данные и возвращает результат, но и нуждается в контексте хоста: запрос токенов авторизации, обращение к пулу БД хоста или запись метрик. В go-plugin это решается с помощью компонента GRPCBroker. При инициализации хост запускает вспомогательный gRPC сервер на том же или выделенном UNIX сокете и передает уникальный BrokerID плагину. Плагин использует этот ID, открывая обратное gRPC соединение к хосту. Таким образом реализуется полноценный двусторонний мост (Bidirectional RPC).",
    "step_by_step": "1. Объявите интерфейс HostCallbackService с методами CheckPermission и LogAudit.\\n2. Реализуйте структуру MockHostService с потокобезопасной записью журнала.\\n3. Создайте PluginContext, имитирующий окружение исполнения плагина.\\n4. Протестируйте выполнение задачи плагином с обращением к хосту.",
    "code_blocks": [{"filename": "callback_bridge.go", "lang": "go", "code": ex11_code}],
    "under_the_hood": "GRPCBroker мультиплексирует несколько виртуальных gRPC серверов и клиентов поверх единого физического соединения или локального сокета. Это исключает необходимость открывать десятки сетевых портов для каждого плагина.",
    "pitfalls": "Опасность взаимной блокировки (Distributed Deadlock): если хост вызывает плагин в синхронной блокирующей транзакции БД, а плагин внутри своего метода пытается открыть новую транзакцию через callback к хосту, пул соединений может исчерпаться, вызвав вечный дэдлок.",
    "bigtech_interview": "Как избежать рекурсивных взаимных блокировок (Deadlocks) при проектировании двусторонних RPC систем (Host <-> Plugin)? Какие таймауты и паттерны контекста (context propagation) здесь критически важны?"
})

# Ex 12
ex12_code = """package main

import (
	"fmt"
)

// ExecutionModelComparison сравнивает различные модели расширяемости систем.
type ExecutionModelComparison struct {
	Model             string
	StartupLatency    string
	MemoryFootprint   string
	SandboxIsolation  string
	CgoRequired       bool
}

func GetModels() []ExecutionModelComparison {
	return []ExecutionModelComparison{
		{
			Model:            "Shared Objects (.so plugin)",
			StartupLatency:   "< 5 ms",
			MemoryFootprint:  "Высокий (shared runtime)",
			SandboxIsolation: "Нулевая (общая память, паника роняет хост)",
			CgoRequired:      true,
		},
		{
			Model:            "Out-of-Process IPC (go-plugin)",
			StartupLatency:   "20 - 100 ms (fork/exec + gRPC)",
			MemoryFootprint:  "> 15 MB на процесс плагина",
			SandboxIsolation: "Высокая (изоляция процессов ОС)",
			CgoRequired:      false,
		},
		{
			Model:            "Docker / Pod Sandboxing",
			StartupLatency:   "500 ms - 2 s",
			MemoryFootprint:  "> 50 MB",
			SandboxIsolation: "Максимальная (namespaces, cgroups, seccomp)",
			CgoRequired:      false,
		},
		{
			Model:            "WebAssembly (Wazero Wasm)",
			StartupLatency:   "< 1 ms (instantiation)",
			MemoryFootprint:  "< 1 MB (изолированная память модуля)",
			SandboxIsolation: "Абсолютная песочница (байткод без sys-calls)",
			CgoRequired:      false,
		},
	}
}

func main() {
	fmt.Println("Сравнительный анализ моделей изоляции для бессерверных расширений на Go:")
	for _, m := range GetModels() {
		fmt.Printf("--> [%s]\\n    Latency старта: %s\\n    Потребление памяти: %s\\n    Изоляция: %s\\n    Требует CGO: %v\\n",
			m.Model, m.StartupLatency, m.MemoryFootprint, m.SandboxIsolation, m.CgoRequired)
	}
}
"""
validate_go(ex12_code)

exercises.append({
    "num": 12,
    "title": "Введение в WebAssembly (Wasm) для серверного Go",
    "task": "Изучите технологию WebAssembly (Wasm) как универсальный, безопасный байткод для серверных расширений. Напишите сравнительную матрицу характеристик различных моделей исполнения (Shared Objects, IPC, Containers, Wasm) по критериям: скорость старта, потребление памяти, уровень изоляции и зависимость от CGO.",
    "theory": "WebAssembly (Wasm) — это открытый бинарный формат инструкций для стековой виртуальной машины. Изначально созданный для браузеров, на сервере Wasm стал стандартом для безопасного исполнения недоверенного пользовательского кода (User-Defined Functions, Serverless, Envoy filters). Wasm исполняется в изолированной песочнице (Software Fault Isolation): модуль имеет доступ только к своему линейному массиву памяти и не может напрямую совершать системные вызовы ядра ОС. Запуск инстанса скомпилированного Wasm занимает доли миллисекунды, а потребление памяти составляет десятки килобайт, что в тысячи раз эффективнее контейнеров.",
    "step_by_step": "1. Спроектируйте структуру ExecutionModelComparison с ключевыми характеристиками.\\n2. Заполните эталонные метрики для .so, go-plugin, Docker и Wasm.\\n3. Напишите функцию форматированного вывода сравнительного отчета.\\n4. Проанализируйте применимость Wasm для HighLoad платформ с тысячами микрофункций.",
    "code_blocks": [{"filename": "wasm_overview.go", "lang": "go", "code": ex12_code}],
    "under_the_hood": "Wasm-байткод валидируется перед запуском: проверяется корректность типов на стеке, границы переходов (jump targets) и отсутствие недопустимых инструкций. Это исключает атаки класса Return-Oriented Programming (ROP) и переполнение буфера на уровне машинного кода хоста.",
    "pitfalls": "Wasm по умолчанию не имеет прямого доступа к файловой системе, сетевым сокетам и аппаратуре. Любое взаимодействие с внешним миром должно явно предоставляться хостом через хост-функции или спецификацию WASI.",
    "bigtech_interview": "Почему сервисы CDN и Edge Computing (Cloudflare Workers, Fastly Compute@Edge) используют WebAssembly вместо легковесных контейнеров Docker или виртуальных машин Firecracker?"
})

# Ex 13
ex13_code = """package main

import (
	"fmt"
)

// WasmRuntimeAudit описывает технические различия рантаймов WebAssembly в Go.
type WasmRuntimeAudit struct {
	RuntimeName  string
	EngineType   string
	CgoDependent bool
	CrossCompile string
	JITSupport   string
}

func GetRuntimeAudits() []WasmRuntimeAudit {
	return []WasmRuntimeAudit{
		{
			RuntimeName:  "Wasmtime-Go (Bytecode Alliance)",
			EngineType:   "Rust-based core via C-bindings",
			CgoDependent: true,
			CrossCompile: "Сложная (требуются кросс-компиляторы C и glibc)",
			JITSupport:   "Cranelift JIT compiler",
		},
		{
			RuntimeName:  "Wasmer-Go",
			EngineType:   "Rust-based core via C-bindings",
			CgoDependent: true,
			CrossCompile: "Сложная (бинарные зависимости libwasmer.so)",
			JITSupport:   "LLVM / Singlepass / Cranelift",
		},
		{
			RuntimeName:  "Wazero (Tetrate)",
			EngineType:   "100% Pure Go",
			CgoDependent: false,
			CrossCompile: "Мгновенная (CGO_ENABLED=0 go build)",
			JITSupport:   "Собственный pure Go AOT/JIT компилятор для amd64 и arm64",
		},
	}
}

func main() {
	fmt.Println("Аудит Wasm-рантаймов для Go-экосистемы:")
	for _, r := range GetRuntimeAudits() {
		fmt.Printf("-> %s:\\n   Движок: %s\\n   CGO: %v\\n   Кросс-компиляция: %s\\n   JIT: %s\\n",
			r.RuntimeName, r.EngineType, r.CgoDependent, r.CrossCompile, r.JITSupport)
	}
}
"""
validate_go(ex13_code)

exercises.append({
    "num": 13,
    "title": "Выбор Wasm-рантайма: CGO vs Чистый Go (Wazero)",
    "task": "Сравните доступные рантаймы WebAssembly для Go (Wasmtime, Wasmer, Wazero). Напишите отчет, доказывающий преимущества Wazero как независимого Wasm-рантайма на чистом Go с собственным JIT-компилятором для amd64/arm64 и нулевой зависимостью от CGO.",
    "theory": "При выборе Wasm-движка для серверного Go инженеры сталкиваются с дилеммой: использовать CGO-биндинги к зрелым Rust-движкам (Wasmtime, Wasmer) или рантайм на чистом Go (Wazero от компании Tetrate). Wazero стал индустриальным стандартом для Go по следующим причинам:\\n1. Чистый Go (Zero CGO): компилируется со статическим флагом CGO_ENABLED=0, исключая зависимости от libm, libc и gcc.\\n2. Тривиальная кросс-компиляция: сборка бинарников под linux/arm64, darwin/arm64 и linux/amd64 работает из коробки.\\n3. Высокая скорость JIT: Wazero содержит написанный на Go транслятор Wasm-инструкций в машинный код amd64 и arm64, почти не уступающий Cranelift.\\n4. Безопасность памяти: отсутствие C-кода гарантирует отсутствие утечек памяти мимо Go GC.",
    "step_by_step": "1. Создайте структуру WasmRuntimeAudit для фиксации технических параметров.\\n2. Заполните сравнительные данные для Wasmtime, Wasmer и Wazero.\\n3. Напишите код презентации результатов аудита.\\n4. Сформулируйте архитектурные рекомендации по использованию Wazero.",
    "code_blocks": [{"filename": "runtime_comparison.go", "lang": "go", "code": ex13_code}],
    "under_the_hood": "Wazero парсит бинарный заголовок Wasm (magic bytes \\x00asm) и компилирует базовые блоки Wasm в нативные машинные инструкции целевого процессора (machine code generation). При отсутствии JIT на экзотических архитектурах Wazero автоматически переключается в режим быстрого интерпретатора.",
    "pitfalls": "При использовании интерпретатора вместо JIT скорость математических вычислений Wasm падает в 5–15 раз. Убедитесь, что в продакшене Wazero работает на поддерживаемых JIT архитектурах (amd64, arm64).",
    "bigtech_interview": "Почему исключение CGO (Zero CGO) является критическим требованием для развертывания Go-микросервисов в облачных окружениях (Kubernetes Scratch containers, Alpine)?"
})

# Ex 14
ex14_code = """package main

import (
	"context"
	"fmt"
)

// MockWazeroRuntime демонстрирует архитектуру инициализации Wasm-рантайма Wazero.
type MockWazeroRuntime struct {
	compiledModules map[string][]byte
}

func NewMockWazeroRuntime() *MockWazeroRuntime {
	return &MockWazeroRuntime{compiledModules: make(map[string][]byte)}
}

// CompileModule парсит Wasm-байткод и компилирует его в оптимизированный машинный код.
func (r *MockWazeroRuntime) CompileModule(ctx context.Context, name string, wasmBinary []byte) error {
	if len(wasmBinary) < 4 || string(wasmBinary[:4]) != "\\x00asm" {
		return fmt.Errorf("invalid wasm binary header: expected \\\\x00asm")
	}
	r.compiledModules[name] = wasmBinary
	fmt.Printf("[Wazero JIT]: Модуль %s успешно скомпилирован в машинный код (%d байт)\\n", name, len(wasmBinary))
	return nil
}

// InstantiateModule создает изолированный инстанс с собственной линейной памятью.
func (r *MockWazeroRuntime) InstantiateModule(ctx context.Context, name string) error {
	_, ok := r.compiledModules[name]
	if !ok {
		return fmt.Errorf("module %s not compiled", name)
	}
	fmt.Printf("[Wazero Runtime]: Инстанс модуля %s создан (выделено 64 КБ памяти)\\n", name)
	return nil
}

func main() {
	ctx := context.Background()
	runtime := NewMockWazeroRuntime()

	// Минимальный валидный бинарный заголовок WebAssembly (версия 1)
	minimalWasm := []byte{'\\x00', 'a', 's', 'm', 0x01, 0x00, 0x00, 0x00}

	if err := runtime.CompileModule(ctx, "sample_plugin", minimalWasm); err != nil {
		panic(err)
	}

	if err := runtime.InstantiateModule(ctx, "sample_plugin"); err != nil {
		panic(err)
	}
}
"""
validate_go(ex14_code)

exercises.append({
    "num": 14,
    "title": "Запуск первого Wasm-модуля с помощью Wazero",
    "task": "Изучите жизненный цикл исполнения WebAssembly в Wazero: инициализация рантайма wazero.NewRuntime, компиляция байткода CompileModule и создание экземпляра InstantiateModule. Напишите валидатор бинарного заголовка Wasm (\\x00asm) и смоделируйте шаги развертывания модуля.",
    "theory": "Жизненный цикл Wasm в Wazero строго разделен на два этапа:\\n1. Компиляция (CompileModule): Wazero принимает массив байт Wasm-файла, проверяет валидность байткода и с помощью JIT-компилятора транслирует его в машинные инструкции хостового процессора. Скомпилированный объект wazero.CompiledModule не содержит изменяемого состояния (stateless), потокобезопасен и может храниться в кэше сервиса неограниченно долго.\\n2. Инстанцирование (InstantiateModule): из скомпилированного шаблона создается изолированный экземпляр (Instance). Для него аллоцируется независимый блок линейной памяти (Memory) и стек вызовов. Инстанцирование происходит быстрее 100 микросекунд.",
    "step_by_step": "1. Изучите структуру заголовка WebAssembly (4 байта magic '\\x00asm' + 4 байта версии 1).\\n2. Создайте модель MockWazeroRuntime с реестром скомпилированных модулей.\\n3. Реализуйте CompileModule с проверкой сигнатуры байткода.\\n4. Реализуйте InstantiateModule для выделения изолированной памяти инстанса.\\n5. Протестируйте компиляцию и запуск минимального бинарного модуля.",
    "code_blocks": [{"filename": "wazero_init.go", "lang": "go", "code": ex14_code}],
    "under_the_hood": "В реальном Wazero функция wazero.NewRuntime(ctx) создает движок с JIT (wazero.NewRuntimeConfigCompiler()) или интерпретатором. При инстанцировании вызывается стартовая функция _start (если есть WASI) или инициализатор секции данных (data segment initialization).",
    "pitfalls": "Никогда не компилируйте модуль (CompileModule) заново на каждый входящий HTTP-запрос! Компиляция требует работы JIT и занимает 10–50 мс CPU. Компилируйте модуль один раз при старте сервиса, а на запросы делайте только InstantiateModule.",
    "bigtech_interview": "В чем разница между CompiledModule и api.Module (Instance) в Wazero? Почему CompiledModule можно безопасно разделять между сотнями горутин, а api.Module требует изоляции?"
})

# Ex 15
ex15_code = """package main

import (
	"context"
	"fmt"
	"strings"
)

// SpamFilterLogic содержит бизнес-логику, которая компилируется в Wasm (GOOS=wasip1 GOARCH=wasm).
type SpamFilterLogic struct {
	ForbiddenKeywords []string
}

func NewSpamFilter() *SpamFilterLogic {
	return &SpamFilterLogic{
		ForbiddenKeywords: []string{"CRYPTO", "CASINO", "FREE_MONEY", "URGENT_LOAN"},
	}
}

// CheckSpam возвращает true, если текст признан спамом.
func (f *SpamFilterLogic) CheckSpam(content string) (bool, string) {
	upper := strings.ToUpper(content)
	for _, kw := range f.ForbiddenKeywords {
		if strings.Contains(upper, kw) {
			return true, kw
		}
	}
	return false, ""
}

func main() {
	// Инструкция по сборке в Wasm:
	// GOOS=wasip1 GOARCH=wasm go build -o spam_filter.wasm main.go
	filter := NewSpamFilter()

	samples := []string{
		"Hello, please review my pull request on GitHub.",
		"Super offer! Win FREE_MONEY now at our casino!",
	}

	for _, sample := range samples {
		isSpam, kw := filter.CheckSpam(sample)
		fmt.Printf("Текст: %q -> Спам: %v (триггер: %s)\\n", sample, isSpam, kw)
	}
}
"""
validate_go(ex15_code)

exercises.append({
    "num": 15,
    "title": "Компиляция кода Go в WebAssembly (WASI)",
    "task": "Напишите плагин фильтрации спама на Go. Спроектируйте алгоритм детекции запрещенных ключевых слов и задокументируйте процесс компиляции Go-кода в стандартный бинарный Wasm/WASI модуль с использованием целевой платформы GOOS=wasip1 GOARCH=wasm (Go 1.21+).",
    "theory": "Начиная с версии Go 1.21, в компилятор добавлена официальная поддержка целевой платформы wasip1 (WebAssembly System Interface preview 1). Команда:\\nGOOS=wasip1 GOARCH=wasm go build -o plugin.wasm main.go\\nгенерирует полностью самодостаточный Wasm-файл. В отличие от устаревшего js/wasm, модуль wasip1 не привязан к браузерному JavaScript, а использует стандартные системные вызовы WASI (работа с часами, печать в stdout/stderr, чтение аргументов). Рантайм Go упаковывается внутрь Wasm-файла (размер около 2–3 МБ без сжатия), включая миниатюрный сборщик мусора и планировщик горутин.",
    "step_by_step": "1. Спроектируйте структуру SpamFilterLogic со списком запрещенных токенов.\\n2. Реализуйте метод CheckSpam с нормализацией регистра строк.\\n3. Опишите команду сборки GOOS=wasip1 GOARCH=wasm.\\n4. Протестируйте работу алгоритма на тестовых сообщениях.",
    "code_blocks": [{"filename": "spam_filter.go", "lang": "go", "code": ex15_code}],
    "under_the_hood": "При компиляции под wasip1 системные вызовы Go (пакет syscall) транслируются в импорты WASI-функций вида wasi_snapshot_preview1.fd_write или clock_time_get. Рантайм Wazero предоставляет эти функции модулю через вызов wasi_snapshot_preview1.MustInstantiate.",
    "pitfalls": "Стандартный компилятор Go генерирует Wasm-файлы размером от 2 МБ, так как включает Go-рантайм. Для создания сверхлегких модулей размером в единицы килобайт часто используют TinyGo (tinygo build -target=wasi -o plugin.wasm).",
    "bigtech_interview": "В чем разница между стандартным компилятором Go и TinyGo при сборке под WebAssembly? Какие ограничения TinyGo накладывает на рефлексию (reflect) и сложные сторонние библиотеки?"
})

output_path = "/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch92_p1.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Part 1 generated successfully: {len(exercises)} exercises.")
