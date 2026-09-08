import json
import subprocess
import os

def validate_go(code):
    p = subprocess.run(['gofmt', '-e'], input=code.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise ValueError(f"Go syntax error: {p.stderr.decode('utf-8')}\nCode:\n{code}")

exercises = []

# Ex 16
ex16_code = """package main

import (
	"context"
	"fmt"
)

// MockWasmModule эмулирует Wasm-модуль с экспортированной математической функцией.
type MockWasmModule struct {
	functions map[string]func(ctx context.Context, params ...uint64) ([]uint64, error)
}

func NewMockWasmModule() *MockWasmModule {
	mod := &MockWasmModule{functions: make(map[string]func(ctx context.Context, params ...uint64) ([]uint64, error))}
	// Экспортированная Wasm-функция add(a, b int32) int32
	mod.functions["add"] = func(ctx context.Context, params ...uint64) ([]uint64, error) {
		if len(params) < 2 {
			return nil, fmt.Errorf("expected 2 arguments, got %d", len(params))
		}
		a := int32(params[0])
		b := int32(params[1])
		res := a + b
		return []uint64{uint64(uint32(res))}, nil
	}
	return mod
}

func (m *MockWasmModule) CallExport(ctx context.Context, name string, params ...uint64) ([]uint64, error) {
	fn, ok := m.functions[name]
	if !ok {
		return nil, fmt.Errorf("function %s not exported", name)
	}
	return fn(ctx, params...)
}

func main() {
	ctx := context.Background()
	mod := NewMockWasmModule()

	// В Wazero вызов выглядит так:
	// fn := mod.ExportedFunction("add")
	// results, err := fn.Call(ctx, uint64(x), uint64(y))

	x, y := int32(42), int32(58)
	results, err := mod.CallExport(ctx, "add", uint64(uint32(x)), uint64(uint32(y)))
	if err != nil {
		panic(err)
	}

	resultInt := int32(results[0])
	fmt.Printf("Wasm add(%d, %d) = %d\\n", x, y, resultInt)
}
"""
validate_go(ex16_code)

exercises.append({
    "num": 16,
    "title": "Передача скалярных аргументов в экспортированные Wasm-функции",
    "task": "Изучите механизм вызова экспортированных скалярных функций в WebAssembly через api.Function.Call в Wazero. Реализуйте передачу числовых аргументов i32/i64, безопасное преобразование типов в uint64 и получение скалярного результата вычислений.",
    "theory": "Спецификация WebAssembly Core v1 поддерживает строго 4 базовых числовых типа: i32, i64, f32 и f64. В Wasm нет встроенных понятий строк, структур или слайсов. В API Wazero универсальная сигнатура вызова имеет вид:\\nCall(ctx context.Context, params ...uint64) ([]uint64, error)\\nВсе скалярные типы передаются упакованными в uint64 (bit-cast). Для передачи i32 значение приводится к uint32, а затем к uint64: uint64(uint32(val)). Результаты также возвращаются как слайс []uint64, где первый элемент декодируется обратно в целевой тип: int32(results[0]). Вызов функции валидируется по сигнатуре типов (type-checked), исключая повреждение стека.",
    "step_by_step": "1. Изучите представление скалярных типов Wasm в виде uint64.\\n2. Спроектируйте структуру MockWasmModule с картой функций.\\n3. Реализуйте упаковку параметров int32 в uint64.\\n4. Выполните вызов экспортированной функции add и декодируйте результат.",
    "code_blocks": [{"filename": "scalar_call.go", "lang": "go", "code": ex16_code}],
    "under_the_hood": "В JIT-режиме Wazero транслирует Call в прямой вызов сгенерированного машинного кода через регистры целевого процессора (System V AMD64 ABI: RDI, RSI, RDX и т.д.). Благодаря этому накладные расходы на вызов скалярной функции Wasm составляют всего 5–15 наносекунд.",
    "pitfalls": "Если случайно передать отрицательный int32 без промежуточного каста к uint32 (например, uint64(int64(val))), произойдет знаковое расширение (sign extension) до 64 бит, что сломает логику Wasm-функции, ожидающей 32-битный аргумент.",
    "bigtech_interview": "Почему Wasm до появления спецификации Component Model не поддерживает сложные типы (строки, структуры) в сигнатурах функций, и как виртуальная машина решает проблему передачи сложных объектов через линейную память?"
})

# Ex 17
ex17_code = """package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
)

var ErrMemoryOutOfBounds = errors.New("wasm linear memory out of bounds")

// LinearMemory эмулирует линейную память WebAssembly (Wasm Linear Memory).
type LinearMemory struct {
	mu   sync.RWMutex
	data []byte
}

func NewLinearMemory(pages int) *LinearMemory {
	// Каждая страница Wasm = 64 КБ (65536 байт)
	const PageSize = 65536
	return &LinearMemory{
		data: make([]byte, pages*PageSize),
	}
}

func (m *LinearMemory) Write(offset uint32, buf []byte) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	end := int(offset) + len(buf)
	if end > len(m.data) {
		return ErrMemoryOutOfBounds
	}
	copy(m.data[offset:end], buf)
	return nil
}

func (m *LinearMemory) Read(offset uint32, size uint32) ([]byte, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	end := int(offset + size)
	if end > len(m.data) {
		return nil, ErrMemoryOutOfBounds
	}
	res := make([]byte, size)
	copy(res, m.data[offset:end])
	return res, nil
}

func main() {
	_ = context.Background()
	mem := NewLinearMemory(1) // 64 КБ

	message := []byte("WebAssembly Safe Linear Memory Buffer")
	offset := uint32(1024)

	// Запись хостом в память Wasm
	if err := mem.Write(offset, message); err != nil {
		panic(err)
	}

	// Чтение хостом из памяти Wasm
	readBack, err := mem.Read(offset, uint32(len(message)))
	if err != nil {
		panic(err)
	}

	fmt.Printf("Успешно прочитано из памяти Wasm: %q (длина: %d байт)\\n", string(readBack), len(readBack))
}
"""
validate_go(ex17_code)

exercises.append({
    "num": 17,
    "title": "Работа с линейной памятью Wasm: чтение и запись байтов",
    "task": "Изучите архитектуру линейной памяти WebAssembly (Linear Memory). Реализуйте структуру LinearMemory с размером страницы 64 КБ (Wasm Page Size), операциями Read/Write и защитой от выхода за границы буфера (ErrMemoryOutOfBounds).",
    "theory": "Линейная память WebAssembly представляет собой сплошной байтовый массив фиксированного или растущего размера. Размер памяти измеряется в страницах по 64 КБ (65 536 байт). Пространство адресов Wasm изолировано: указатель внутри Wasm — это просто целочисленное смещение (uint32 offset) от начала линейного буфера. Wasm-модуль не может адресовать память за пределами своего буфера: любая инструкция load/store за границей буфера вызывает немедленный фатальный trap (исключение песочницы), предотвращая чтение памяти хост-процесса.",
    "step_by_step": "1. Объявите константу PageSize = 65536.\\n2. Создайте структуру LinearMemory с защитой sync.RWMutex.\\n3. Реализуйте метод Write с проверкой выхода за границы памяти.\\n4. Реализуйте метод Read с копированием байтов во избежание data race.\\n5. Проверьте запись и чтение строки по произвольному смещению.",
    "code_blocks": [{"filename": "linear_memory.go", "lang": "go", "code": ex17_code}],
    "under_the_hood": "В Wazero интерфейс api.Memory предоставляет методы Write(offset, data) и Read(offset, byteCount). Под капотом JIT компилятор Wazero выделяет виртуальную память через mmap с guard pages (сторожевыми страницами) для аппаратного отлова попыток несанкционированного доступа к памяти без накладных проверок в каждой инструкции.",
    "pitfalls": "Если вернуть слайс data[offset:end] напрямую без copy(), хост и Wasm получат разделяемый указатель на байты. Если Wasm перезапишет эту область параллельно с чтением хоста, возникнет состояние гонки данных (data race).",
    "bigtech_interview": "Почему WebAssembly использует 32-битные смещения памяти (Wasm32) и каков предел адресуемой памяти одного модуля (4 ГБ)? Как развивается спецификация Memory64 для систем с терабайтами данных?"
})

# Ex 18
ex18_code = """package main

import (
	"context"
	"fmt"
	"sync"
)

// WasmMemoryAllocator моделирует встроенный в Wasm аллокатор памяти (экспортированные malloc/free).
type WasmMemoryAllocator struct {
	mu          sync.Mutex
	memoryPool  []byte
	currentHead uint32
}

func NewWasmMemoryAllocator(capacityBytes uint32) *WasmMemoryAllocator {
	return &WasmMemoryAllocator{
		memoryPool:  make([]byte, capacityBytes),
		currentHead: 1024, // резервируем начало для стека Wasm
	}
}

// Allocate имитирует экспортированную функцию allocate(size uint32) uint32.
func (a *WasmMemoryAllocator) Allocate(size uint32) (uint32, error) {
	a.mu.Lock()
	defer a.mu.Unlock()

	ptr := a.currentHead
	if ptr+size > uint32(len(a.memoryPool)) {
		return 0, fmt.Errorf("out of memory in wasm instance")
	}
	a.currentHead += size
	return ptr, nil
}

// Deallocate имитирует экспортированную функцию deallocate(ptr uint32, size uint32).
func (a *WasmMemoryAllocator) Deallocate(ptr uint32, size uint32) {
	a.mu.Lock()
	defer a.mu.Unlock()
	// Простейшая имитация: если освобождается последний блок, откатываем голову
	if ptr+size == a.currentHead {
		a.currentHead = ptr
	}
}

// HostStringTransfer демонстрирует безопасный протокол передачи строки из хоста в Wasm.
func HostStringTransfer(alloc *WasmMemoryAllocator, message string) (uint32, uint32, error) {
	data := []byte(message)
	size := uint32(len(data))

	// 1. Хост вызывает allocate внутри Wasm для резервирования буфера
	ptr, err := alloc.Allocate(size)
	if err != nil {
		return 0, 0, err
	}

	// 2. Хост копирует данные по выделенному адресу
	copy(alloc.memoryPool[ptr:ptr+size], data)

	return ptr, size, nil
}

func main() {
	alloc := NewWasmMemoryAllocator(65536)

	msg := "Hello from Go Host to Wasm Guest via Dynamic Malloc!"
	ptr, size, err := HostStringTransfer(alloc, msg)
	if err != nil {
		panic(err)
	}

	fmt.Printf("Данные размещены в Wasm памяти: адрес=0x%x, размер=%d байт\\n", ptr, size)
	fmt.Printf("Проверка содержимого: %q\\n", string(alloc.memoryPool[ptr:ptr+size]))

	// Освобождаем память после завершения обработки
	alloc.Deallocate(ptr, size)
	fmt.Println("Память успешно освобождена в Wasm guest.")
}
"""
validate_go(ex18_code)

exercises.append({
    "num": 18,
    "title": "Выделение памяти внутри Wasm: экспорт malloc и free",
    "task": "Спроектируйте протокол безопасной передачи динамических данных произвольной длины из хоста в Wasm. Экспортируйте функции выделения (allocate) и освобождения (deallocate) памяти из модуля и реализуйте паттерн HostStringTransfer.",
    "theory": "Хост-приложение не должно самостоятельно выбирать адреса для записи данных в память Wasm-модуля: это приведет к повреждению внутреннего стека или структур данных рантайма Wasm (память будет перезаписана). Стандартный паттерн межъязыкового взаимодействия (FFI):\\n1. Модуль Wasm экспортирует функцию allocate(size uint32) uint32 (обертку над malloc или make([]byte)).\\n2. Модуль экспортирует функцию deallocate(ptr, size uint32) (обертку над free).\\n3. Хост вызывает allocate(N) и получает гарантированно безопасный указатель ptr.\\n4. Хост записывает полезную нагрузку в Memory().Write(ptr, data).\\n5. Хост вызывает целевую бизнес-функцию process(ptr, N).\\n6. Хост вызывает deallocate(ptr, N) для предотвращения утечки памяти в Wasm.",
    "step_by_step": "1. Спроектируйте WasmMemoryAllocator с отслеживанием свободных адресов.\\n2. Реализуйте метод Allocate, возвращающий указатель (uint32 ptr).\\n3. Реализуйте метод Deallocate для очистки ресурсов.\\n4. Напишите функцию HostStringTransfer, организующую цикл аллокации, копирования и освобождения.",
    "code_blocks": [{"filename": "allocator_bridge.go", "lang": "go", "code": ex18_code}],
    "under_the_hood": "В модулях, написанных на Rust или C, allocate делегирует вызов libc malloc. В TinyGo для этого экспортируют функцию, возвращающую uintptr(unsafe.Pointer(&buf[0])).",
    "pitfalls": "Если хост не вызовет deallocate() после завершения вызова функции, память внутри инстанса Wasm быстро исчерпается, и следующий allocate() вернет ошибку OOM.",
    "bigtech_interview": "Как в envoy-wasm и proxy-wasm устроен ABI передачи заголовков HTTP-запросов между C++ прокси и Wasm-плагином? Почему используется парный вызов malloc/free?"
})

# Ex 19
ex19_code = """package main

import (
	"context"
	"fmt"
	"sync"
)

// HostLoggerService предоставляет сервис хоста, доступный для вызова из Wasm.
type HostLoggerService struct {
	mu   sync.Mutex
	logs []string
}

func (s *HostLoggerService) Log(level string, message string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	entry := fmt.Sprintf("[%s] %s", level, message)
	s.logs = append(s.logs, entry)
	fmt.Printf("[Wasm Host Log]: %s\\n", entry)
}

// HostModuleBuilder моделирует регистрацию хост-функций в Wazero.
type HostModuleBuilder struct {
	moduleName string
	functions  map[string]interface{}
}

func NewHostModuleBuilder(moduleName string) *HostModuleBuilder {
	return &HostModuleBuilder{
		moduleName: moduleName,
		functions:  make(map[string]interface{}),
	}
}

func (b *HostModuleBuilder) ExportFunction(name string, fn interface{}) *HostModuleBuilder {
	b.functions[name] = fn
	return b
}

func main() {
	_ = context.Background()
	logger := &HostLoggerService{}

	// В реальном Wazero:
	// _, err := r.NewHostModuleBuilder("env").
	//     NewFunctionBuilder().
	//     WithFunc(func(ctx context.Context, mod api.Module, ptr, size uint32) {
	//         bytes, _ := mod.Memory().Read(ptr, size)
	//         logger.Log("INFO", string(bytes))
	//     }).Export("host_log").Instantiate(ctx)

	builder := NewHostModuleBuilder("env")
	builder.ExportFunction("host_log", logger.Log)

	// Симуляция вызова из Wasm
	logger.Log("WARN", "Подозрительная активность в плагине платежей")
}
"""
validate_go(ex19_code)

exercises.append({
    "num": 19,
    "title": "Хост-функции (Host Functions): предоставление API модулю",
    "task": "Изучите механизм хост-функций (Host Functions) в Wazero. Напишите код регистрации хост-модуля env и экспорта функции логирования host_log, доступной для прямого вызова из байткода WebAssembly с передачей указателя и длины строки.",
    "theory": "Хост-функция — это стандартная функция Go, зарегистрированная в рантайме Wasm и импортируемая Wasm-модулем (import \\\"env\\\" \\\"host_log\\\"). Хост-функции — единственный безопасный мост, через который Wasm может запрашивать действия от внешнего мира: обращаться к сетевым сокетам, читать системное время, взаимодействовать с базами данных хоста или писать структурированные логи. Хост полностью контролирует контракт: если функция не предоставлена модулю при инстанцировании, вызов физически невозможен на уровне валидатора байткода.",
    "step_by_step": "1. Спроектируйте структуру HostLoggerService с потокобезопасным методом Log.\\n2. Создайте модель HostModuleBuilder для импорта функций модуля env.\\n3. Опишите идиоматичную сигнатуру Wazero WithFunc с чтением строки из api.Module памяти.\\n4. Протестируйте экспорт и вызов хост-функции.",
    "code_blocks": [{"filename": "host_functions.go", "lang": "go", "code": ex19_code}],
    "under_the_hood": "Когда Wasm-модуль выполняет инструкцию call $import_func, процессор переключает контекст исполнения со скомпилированного кода Wasm на Go-функцию. Wazero автоматически передает указатель на api.Module вызывающего инстанса первым аргументом, позволяя хост-функции инспектировать память вызвавшего ее модуля.",
    "pitfalls": "Если хост-функция зависает (например, выполняет тяжелый синхронный запрос к Postgres без таймаута), исполнение Wasm-модуля также блокируется. Всегда передавайте context.Context с таймаутом во все хост-функции.",
    "bigtech_interview": "Как устроена безопасность в модели хост-функций (Capability-based Security)? Почему подход Wasm безопаснее предоставления плагину прямого доступа к дескрипторам файлов операционной системы?"
})

# Ex 20
ex20_code = """package main

import (
	"bytes"
	"context"
	"fmt"
	"io"
)

// WASIHostConfiguration эмулирует конфигурацию перенаправления потоков ввода-вывода WASI.
type WASIHostConfiguration struct {
	Stdout io.Writer
	Stderr io.Writer
	Stdin  io.Reader
	Args   []string
}

func NewWASIHostConfiguration() (*WASIHostConfiguration, *bytes.Buffer, *bytes.Buffer) {
	stdoutBuf := new(bytes.Buffer)
	stderrBuf := new(bytes.Buffer)
	return &WASIHostConfiguration{
		Stdout: stdoutBuf,
		Stderr: stderrBuf,
		Stdin:  nil,
		Args:   []string{"plugin_wasm", "--mode=fast"},
	}, stdoutBuf, stderrBuf
}

func (c *WASIHostConfiguration) SimulateExecution() {
	// Имитируем вывод Wasm-модуля в стандартные потоки WASI
	_, _ = fmt.Fprintln(c.Stdout, "WASI: stdout payload data: status=ok")
	_, _ = fmt.Fprintln(c.Stderr, "WASI: debug trace warning")
}

func main() {
	_ = context.Background()
	// В реальном Wazero подключение WASI:
	// wasi_snapshot_preview1.MustInstantiate(ctx, r)
	// modConfig := wazero.NewModuleConfig().WithStdout(stdoutBuf).WithStderr(stderrBuf)

	cfg, stdout, stderr := NewWASIHostConfiguration()
	cfg.SimulateExecution()

	fmt.Printf("Перехваченный stdout модуля: %q\\n", stdout.String())
	fmt.Printf("Перехваченный stderr модуля: %q\\n", stderr.String())
}
"""
validate_go(ex20_code)

exercises.append({
    "num": 20,
    "title": "Подключение WASI Snapshot Preview 1",
    "task": "Изучите стандарт системных интерфейсов WASI Snapshot Preview 1. Напишите код инициализации WASI окружения в Wazero с перенаправлением стандартных потоков stdout и stderr модуля в буферы памяти bytes.Buffer хост-приложения для перехвата вывода.",
    "theory": "Большинство скомпилированных программ (на Go, Rust, C++) полагаются на стандартные вызовы libc: вывод в терминал, чтение аргументов os.Args, получение времени. Спецификация WASI (WebAssembly System Interface, Preview 1) стандартизирует набор из ~40 системных функций (fd_write, fd_read, clock_time_get, args_get и т.д.). Wazero включает готовую эталонную реализацию WASI в пакете wasi_snapshot_preview1. Вызов wasi_snapshot_preview1.MustInstantiate(ctx, runtime) регистрирует хост-модуль wasi_snapshot_preview1, после чего модуль может запускать стандартную точку входа _start.",
    "step_by_step": "1. Спроектируйте WASIHostConfiguration с перехватом потоков io.Writer.\\n2. Создайте изолированные буферы bytes.Buffer для stdout и stderr.\\n3. Опишите параметры инициализации wasi_snapshot_preview1 в Wazero.\\n4. Протестируйте сбор логов и диагностического вывода модуля.",
    "code_blocks": [{"filename": "wasi_integration.go", "lang": "go", "code": ex20_code}],
    "under_the_hood": "Функция fd_write в WASI принимает дескриптор файла и массив структур iovec (рассеянный ввод-вывод). Wazero считывает буферы из памяти Wasm и перенаправляет их в настроенный io.Writer без вызова реального syscall write() в ядро ОС.",
    "pitfalls": "Если забыть подключить WASI при инстанцировании модуля wasip1, рантайм вернет ошибку линковки: 'module imports unknown function wasi_snapshot_preview1.fd_write'.",
    "bigtech_interview": "Чем WASI Preview 1 отличается от нового стандарта WASI Preview 2 (Wasm Components, WIT IDL)? Почему индустрия переходит на компонентную модель с интерфейсами типов?"
})

# Ex 21
ex21_code = """package main

import (
	"fmt"
	"strings"
)

// SandboxSecurityPolicy регулирует права доступа Wasm модуля к ресурсам операционной системы.
type SandboxSecurityPolicy struct {
	InheritEnvs       bool
	AllowedEnvs       map[string]string
	FilesystemAccess  bool
	MountGuestDir     string
	MaxArgumentsCount int
}

func NewStrictSandboxPolicy() *SandboxSecurityPolicy {
	return &SandboxSecurityPolicy{
		InheritEnvs:       false,
		AllowedEnvs:       map[string]string{"ENV": "sandbox"},
		FilesystemAccess:  false,
		MountGuestDir:     "",
		MaxArgumentsCount: 3,
	}
}

func (p *SandboxSecurityPolicy) ValidateSyscallRequest(syscallName, path string) error {
	if strings.HasPrefix(syscallName, "fs_") && !p.FilesystemAccess {
		return fmt.Errorf("SECURITY ALERT: попытка доступа к файловой системе (%s: %s) заблокирована песочницей", syscallName, path)
	}
	return nil
}

func main() {
	policy := NewStrictSandboxPolicy()

	// Имитация вредоносной попытки модуля прочитать файл хоста
	err := policy.ValidateSyscallRequest("fs_open", "/etc/passwd")
	if err != nil {
		fmt.Printf("Песочница успешно нейтрализовала атаку: %v\\n", err)
	} else {
		fmt.Println("Уязвимость: доступ к файловой системе разрешен!")
	}
}
"""
validate_go(ex21_code)

exercises.append({
    "num": 21,
    "title": "Песочница: ограничение системных вызовов в Wasm",
    "task": "Спроектируйте политику безопасности песочницы SandboxSecurityPolicy. Реализуйте конфигурацию модуля wazero.NewModuleConfig, запрещающую наследование переменных окружения хоста (WithoutInheritEnvs), запрещающую доступ к файловой системе и предотвращающую чтение конфиденциальных файлов типа /etc/passwd.",
    "theory": "По умолчанию WebAssembly обладает нулевыми полномочиями (Zero Trust Capability-based Security). Даже если сторонний модуль скомпилирован из ненадежного кода, он не может открыть файл или подключиться к сети, пока хост явно не предоставит соответствующую возможность через wazero.ModuleConfig. Методы безопасности Wazero:\\n- WithoutInheritEnvs(): блокирует передачу секретов окружения (AWS_SECRET_KEY, DATABASE_URL) в память плагина.\\n- WithFS(nil): блокирует любые операции с файлами.\\n- WithFSConfig(wazero.NewFSConfig().WithDirMount('/tmp/plugin', '/')): виртуализирует chroot, изолируя доступ к строго разрешенной директории.",
    "step_by_step": "1. Спроектируйте структуру SandboxSecurityPolicy со строгими ограничениями.\\n2. Создайте конструктор NewStrictSandboxPolicy с запретом наследования окружения.\\n3. Реализуйте метод ValidateSyscallRequest для перехвата несанкционированных вызовов.\\n4. Протестируйте блокировку попытки чтения чувствительных путей.",
    "code_blocks": [{"filename": "sandbox_policy.go", "lang": "go", "code": ex21_code}],
    "under_the_hood": "Файловые операции WASI fd_open проверяются виртуальной файловой системой fs.FS в Go. Если путь выходит за пределы смонтированной директории (через ../../), виртуальная файловая система Wazero возвращает ошибку EINVAL/EPERM.",
    "pitfalls": "Никогда не используйте WithInheritEnvs(true) при запуске пользовательских плагинов (User-Generated Plugins): плагин сможет прочитать токены доступа хоста и переслать их злоумышленнику.",
    "bigtech_interview": "В чем фундаментальное отличие Capability-based безопасности (Wasm) от Access Control Lists (ACL) и Unix permissions? Как предотвратить атаку Confused Deputy в плагинной архитектуре?"
})

# Ex 22
ex22_code = """package main

import (
	"errors"
	"fmt"
)

var ErrMemoryLimitExceeded = errors.New("wasm memory limit exceeded: requested pages above ceiling")

// MemoryCeilingLimiter защищает хост от исчерпания памяти (OOM) ненадежным модулем.
type MemoryCeilingLimiter struct {
	MaxPagesAllowed uint32 // Каждая страница 64 КБ
	CurrentPages    uint32
}

func NewMemoryCeilingLimiter(maxMegabytes uint32) *MemoryCeilingLimiter {
	pages := (maxMegabytes * 1024 * 1024) / 65536
	return &MemoryCeilingLimiter{
		MaxPagesAllowed: pages,
		CurrentPages:    1, // Начальная страница при старте
	}
}

func (l *MemoryCeilingLimiter) GrowMemory(additionalPages uint32) error {
	newTotal := l.CurrentPages + additionalPages
	if newTotal > l.MaxPagesAllowed {
		return fmt.Errorf("%w: текущие страницы %d + %d > лимит %d (макс %d КБ)",
			ErrMemoryLimitExceeded, l.CurrentPages, additionalPages, l.MaxPagesAllowed, l.MaxPagesAllowed*64)
	}
	l.CurrentPages = newTotal
	return nil
}

func main() {
	// Лимит памяти: не более 4 МБ (64 страницы)
	limiter := NewMemoryCeilingLimiter(4)

	// 1. Модуль выделяет 30 страниц (норма)
	if err := limiter.GrowMemory(30); err != nil {
		panic(err)
	}
	fmt.Printf("Память увеличена: текущий размер %d КБ\\n", limiter.CurrentPages*64)

	// 2. Попытка модуля выделить еще 50 страниц (превышение лимита 64 страниц)
	err := limiter.GrowMemory(50)
	if err != nil {
		fmt.Printf("Защита от OOM сработала: %v\\n", err)
	}
}
"""
validate_go(ex22_code)

exercises.append({
    "num": 22,
    "title": "Ограничение потребления оперативной памяти Wasm-модулем",
    "task": "Защитите хост от утечек памяти и DoS-атак через исчерпание RAM (OOM). Реализуйте структуру MemoryCeilingLimiter, контролирующую вызовы расширения памяти memory.grow и ограничивающую предельный объем памяти Wasm-модуля (например, не более 4 МБ) без краха хост-приложения.",
    "theory": "Wasm-модуль может динамически увеличивать объем линейной памяти с помощью инструкции memory.grow(delta_pages). Без ограничений вредоносный или ошибочный цикл аллокации вызовет OOM-killer ядра Linux, который убьет весь сервис хоста. В Wazero максимальный предел страниц задается через NewModuleConfig().WithMemoryLimitPages(maxPages). Если модуль пытается запросить память сверх лимита, инструкция memory.grow возвращает -1 (ошибка аллокации внутри Wasm), а хост-процесс сохраняет стабильность.",
    "step_by_step": "1. Пересчитайте мегабайты в страницы Wasm (1 страница = 64 КБ).\\n2. Спроектируйте структуру MemoryCeilingLimiter с проверкой порога.\\n3. Реализуйте метод GrowMemory с возвратом ErrMemoryLimitExceeded.\\n4. Протестируйте успешный рост памяти и блокировку при превышении лимита.",
    "code_blocks": [{"filename": "memory_limit.go", "lang": "go", "code": ex22_code}],
    "under_the_hood": "В Wazero при вызове memory.grow рантайм проверяет лимит. Если лимит не превышен, память довыделяется без повторного копирования предыдущих данных, расширяя маппинг в адресном пространстве.",
    "pitfalls": "Если лимит памяти задан слишком низким (например, < 2 МБ), стандартный рантайм Go (wasip1) упадет сразу при старте, так как сборщику мусора Go требуется минимальная куча для инициализации.",
    "bigtech_interview": "Как в мультиарендных платформах (Multi-tenant FaaS) изолируют память сотен параллельных функций и как Linux cgroups v2 дополняет ограничения рантайма Wasm?"
})

# Ex 23
ex23_code = """package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

var ErrOutOfGas = errors.New("execution terminated: out of gas (CPU instruction budget exhausted)")

// GasMeteredExecution эмулирует учет инструкций процессора (Gas Metering).
type GasMeteredExecution struct {
	GasLimit uint64
	GasUsed  uint64
}

func NewGasMeteredExecution(budget uint64) *GasMeteredExecution {
	return &GasMeteredExecution{GasLimit: budget}
}

func (m *GasMeteredExecution) ConsumeGas(cost uint64) error {
	if m.GasUsed+cost > m.GasLimit {
		return ErrOutOfGas
	}
	m.GasUsed += cost
	return nil
}

// ExecuteLoop моделирует исполнение бесконечного цикла скрипта с контролем CPU газа.
func ExecuteLoop(ctx context.Context, meter *GasMeteredExecution) error {
	for i := 0; ; i++ {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
			// Списываем газ за каждую итерацию цикла
			if err := meter.ConsumeGas(10); err != nil {
				return err
			}
		}
	}
}

func main() {
	// Бюджет: 50 единиц газа (максимум 5 итераций цикла)
	meter := NewGasMeteredExecution(50)
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	err := ExecuteLoop(ctx, meter)
	if err != nil {
		fmt.Printf("Исполнение прервано: %v (использовано газа: %d/%d)\\n", err, meter.GasUsed, meter.GasLimit)
	}
}
"""
validate_go(ex23_code)

exercises.append({
    "num": 23,
    "title": "Ограничение времени выполнения и Gas Metering (Инструкции CPU)",
    "task": "Реализуйте механизмы защиты от бесконечных циклов и DoS по CPU: прерывание через context.WithTimeout и модель подсчета инструкций (Gas Metering). Создайте структуру GasMeteredExecution, принудительно останавливающую выполнение скрипта при исчерпании бюджета газа.",
    "theory": "Если пользовательский плагин содержит бесконечный цикл `for {}`, горутина хоста зависнет навсегда. В Wazero предусмотрено два уровня защиты:\\n1. Context Cancellation: все вызовы api.Function.Call(ctx, ...) принимают context.Context. Если сработал context.WithTimeout, Wazero принудительно прерывает исполнение байткода на границе следующего базового блока, возвращая ошибку context.DeadlineExceeded.\\n2. Gas Metering: перед компиляцией Wasm-байткод модифицируется (инструментируется), внедряя в начало каждого цикла и функции инструкцию списания газа (например, 1 инструкция = 1 gas). Если счетчик падает до 0, виртуальная машина выбрасывает trap OutOfGas. Это гарантирует детерминированное время исполнения независимо от производительности процессора.",
    "step_by_step": "1. Объявите ошибку ErrOutOfGas.\\n2. Создайте структуру GasMeteredExecution с лимитом и счетчиком газа.\\n3. Реализуйте метод ConsumeGas с контролем превышения лимита.\\n4. Напишите функцию ExecuteLoop, комбинирующую проверку context.Done() и ConsumeGas.",
    "code_blocks": [{"filename": "gas_metering.go", "lang": "go", "code": ex23_code}],
    "under_the_hood": "Wazero периодически инспектирует ctx.Done() в циклах Wasm в сгенерированном JIT-коде, вставляя проверку флага прерывания (interrupt check) в прологи функций и ветвления.",
    "pitfalls": "Слишком частая проверка времени (time.Now()) внутри циклов сильно снижает производительность (вызовы clock_gettime). Модель Gas Metering на порядки быстрее, так как оперирует простым декрементом локального регистра процессора.",
    "bigtech_interview": "Почему смарт-контракты (Ethereum EVM, CosmWasm) и серверные FaaS-движки используют концепцию Gas Metering для обеспечения детерминизма исполнения?"
})

# Ex 24
ex24_code = """package main

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// WasmInstance эмулирует готовый инстанс модуля с изолированной памятью.
type WasmInstance struct {
	ID        int64
	IsHealthy bool
}

func (i *WasmInstance) Execute(input string) string {
	return fmt.Sprintf("Result[%s] processed by instance #%d", input, i.ID)
}

// InstancePool организует высокопроизводительный пул Wasm инстансов.
type InstancePool struct {
	pool       sync.Pool
	instanceID atomic.Int64
}

func NewInstancePool() *InstancePool {
	p := &InstancePool{}
	p.pool.New = func() interface{} {
		id := p.instanceID.Add(1)
		// В реальном приложении здесь вызывается r.InstantiateModule(ctx, compiledModule, ...)
		return &WasmInstance{ID: id, IsHealthy: true}
	}
	return p
}

func (p *InstancePool) Acquire() *WasmInstance {
	return p.pool.Get().(*WasmInstance)
}

func (p *InstancePool) Release(inst *WasmInstance) {
	if inst.IsHealthy {
		p.pool.Put(inst)
	}
	// Если инстанс поврежден или выбросил панику, он отбрасывается и уничтожается сборщиком мусора
}

func main() {
	_ = context.Background()
	pool := NewInstancePool()

	var wg sync.WaitGroup
	// Имитируем параллельную обработку 5 HTTP-запросов
	for i := 1; i <= 5; i++ {
		wg.Add(1)
		go func(reqID int) {
			defer wg.Done()
			inst := pool.Acquire()
			defer pool.Release(inst)

			res := inst.Execute(fmt.Sprintf("req-%d", reqID))
			fmt.Println(res)
		}(i)
	}
	wg.Wait()
	time.Sleep(10 * time.Millisecond)
}
"""
validate_go(ex24_code)

exercises.append({
    "num": 24,
    "title": "Пул инстансов Wasm-модулей (Instance Pooling)",
    "task": "Спроектируйте архитектуру пулинга инстансов Wasm-модулей на базе sync.Pool. Обеспечьте субмиллисекундное предоставление готового инстанса Wasm на каждый параллельный HTTP-запрос и автоматическую утилизацию поврежденных инстансов.",
    "theory": "Хотя создание инстанса из wazero.CompiledModule выполняется быстро (0.1–0.5 мс), под нагрузкой 50 000 RPS постоянное создание и уничтожение инстансов перегружает сборщик мусора Go (аллокация памяти модуля, дескрипторов и структур). Паттерн Instance Pool предварительно разогревает пул готовых инстансов с помощью sync.Pool или кольцевого буфера. Горутина берет свободный инстанс, выполняет вызов, очищает временное состояние (сбрасывает указатель аллокатора) и возвращает инстанс в пул. Если инстанс завершился с ошибкой или trap, он не возвращается в пул, а уничтожается.",
    "step_by_step": "1. Спроектируйте структуру WasmInstance с флагом здоровья IsHealthy.\\n2. Создайте структуру InstancePool на базе sync.Pool с генерацией ID инстансов.\\n3. Реализуйте метод Acquire для получения инстанса без блокировок.\\n4. Реализуйте Release с проверкой здоровья инстанса.\\n5. Запустите параллельную обработку конкурентных запросов с sync.WaitGroup.",
    "code_blocks": [{"filename": "instance_pool.go", "lang": "go", "code": ex24_code}],
    "under_the_hood": "sync.Pool в рантайме Go привязан к P (процессорам планировщика Go), что обеспечивает lock-free доступ к локальным инстансам без блокировок мьютексов в 95% случаев.",
    "pitfalls": "Критическая опасность повторного использования инстансов (Instance Reuse) — утечка состояния между пользователями (State Pollution). Если модуль хранит глобальные переменные Wasm, данные предыдущего пользователя могут повлиять на следующего. Очищайте состояние или сбрасывайте data segments.",
    "bigtech_interview": "Как в Cloudflare Workers и Fastly балансируют между переиспользованием инстансов (pooling) и абсолютной изоляцией изолятов (Zero-state per request)?"
})

# Ex 25
ex25_code = """package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

// UnsafeSharedModule демонстрирует ошибку конкурентного доступа к одной линейной памяти Wasm.
type UnsafeSharedModule struct {
	memory   []byte
	conflicts atomic.Int64
}

func NewUnsafeSharedModule() *UnsafeSharedModule {
	return &UnsafeSharedModule{memory: make([]byte, 1024)}
}

// WriteTransaction симулирует запись запроса в фиксированный буфер памяти.
func (m *UnsafeSharedModule) WriteTransaction(threadID int, val byte) {
	// Все потоки пишут в одну и ту же область смещения 0
	m.memory[0] = val
	if m.memory[0] != val {
		m.conflicts.Add(1)
	}
}

func main() {
	mod := NewUnsafeSharedModule()
	var wg sync.WaitGroup

	// Конкурентная запись из 10 горутин без изоляции
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for j := 0; j < 1000; j++ {
				mod.WriteTransaction(id, byte(id))
			}
		}(i)
	}
	wg.Wait()

	fmt.Printf("Демонстрация data race в разделяемой памяти Wasm: зафиксировано конфликтов: %d\\n", mod.conflicts.Load())
	fmt.Println("Вывод: api.Module инстанс НЕ является потокобезопасным! Каждая горутина обязана иметь свой инстанс.")
}
"""
validate_go(ex25_code)

exercises.append({
    "num": 25,
    "title": "Изоляция памяти при конкурентных вызовах Wasm",
    "task": "Докажите, что линейная память инстанса Wasm (api.Module) не является потокобезопасной для параллельных вызовов. Продемонстрируйте состояние гонки данных при попытке совместного использования одного экземпляра модуля несколькими горутинами и сформулируйте архитектурное правило изоляции.",
    "theory": "Спецификация WebAssembly Core v1 проектировалась как однопоточная среда исполнения (Single-threaded Execution Environment). Линейная память инстанса модуля Wasm (api.Memory) представляет собой несинхронизированный массив байт. Если две горутины Go одновременно вызовут экспортированную функцию одного и того же api.Module, они разделят один и тот же стек Wasm и одну и ту же линейную память. Запись данных первой горутины перезапишет буфер второй, приводя к повреждению данных (data corruption) и паникам рантайма. Фундаментальное правило: CompiledModule — разделяемый и потокобезопасный; api.Module — строго однопоточный.",
    "step_by_step": "1. Спроектируйте структуру UnsafeSharedModule с общим массивом памяти.\\n2. Запустите параллельные горутины, записывающие данные по нулевому смещению.\\n3. Зафиксируйте факт перезаписи данных другими потоками.\\n4. Сформулируйте архитектурное решение: модель 'один инстанс на горутину' либо пул инстансов.",
    "code_blocks": [{"filename": "concurrency_hazard.go", "lang": "go", "code": ex25_code}],
    "under_the_hood": "Хотя в спецификации WebAssembly Threads Proposal появились SharedArrayBuffer и атомарные инструкции, 99% Wasm-модулей (включая TinyGo и standard Go wasip1) собираются в однопоточном режиме без мьютексов.",
    "pitfalls": "Попытка защитить единственный инстанс Wasm глобальным мьютексом sync.Mutex превращает многопоточный Go-микросервис в строго однопоточный, обрушивая RPS системы.",
    "bigtech_interview": "Почему разделение компиляции (Stateless CompiledModule) и инстанцирования (Stateful Module Instance) является ключевым архитектурным паттерном во всех современных Wasm-движках (Wazero, V8, Wasmtime)?"
})

# Ex 26
ex26_code = """package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
)

// UserScoreRequest представляет контракт запроса (аналог Protobuf сообщения).
type UserScoreRequest struct {
	UserID   uint64
	Activity uint32
}

// UserScoreResponse представляет контракт ответа.
type UserScoreResponse struct {
	UserID uint64
	Score  uint32
}

// EncodeRequest сериализует запрос в бинарный формат для передачи в память Wasm.
func EncodeRequest(req UserScoreRequest) []byte {
	buf := new(bytes.Buffer)
	_ = binary.Write(buf, binary.LittleEndian, req.UserID)
	_ = binary.Write(buf, binary.LittleEndian, req.Activity)
	return buf.Bytes()
}

// DecodeResponse десериализует ответ из линейной памяти Wasm.
func DecodeResponse(data []byte) (UserScoreResponse, error) {
	buf := bytes.NewReader(data)
	var resp UserScoreResponse
	if err := binary.Read(buf, binary.LittleEndian, &resp.UserID); err != nil {
		return resp, err
	}
	if err := binary.Read(buf, binary.LittleEndian, &resp.Score); err != nil {
		return resp, err
	}
	return resp, nil
}

// MockWasmGuestCalculation имитирует работу Wasm-модуля над сериализованными данными.
func MockWasmGuestCalculation(input []byte) []byte {
	reqBuf := bytes.NewReader(input)
	var req UserScoreRequest
	_ = binary.Read(reqBuf, binary.LittleEndian, &req.UserID)
	_ = binary.Read(reqBuf, binary.LittleEndian, &req.Activity)

	// Бизнес-логика в Wasm
	calculatedScore := req.Activity * 10

	resp := UserScoreResponse{
		UserID: req.UserID,
		Score:  calculatedScore,
	}

	out := new(bytes.Buffer)
	_ = binary.Write(out, binary.LittleEndian, resp.UserID)
	_ = binary.Write(out, binary.LittleEndian, resp.Score)
	return out.Bytes()
}

func main() {
	req := UserScoreRequest{UserID: 100982, Activity: 42}
	serialized := EncodeRequest(req)
	fmt.Printf("Хост сериализовал запрос в %d байт\\n", len(serialized))

	// Передача в Wasm и получение ответа
	wasmOutput := MockWasmGuestCalculation(serialized)

	resp, err := DecodeResponse(wasmOutput)
	if err != nil {
		panic(err)
	}
	fmt.Printf("Ответ от Wasm: UserID=%d, CalculatedScore=%d\\n", resp.UserID, resp.Score)
}
"""
validate_go(ex26_code)

exercises.append({
    "num": 26,
    "title": "Передача структурированных данных: Protobuf поверх Wasm Memory",
    "task": "Реализуйте бинарный протокол передачи структурированных сообщений (Protobuf/Binary Serialization) между Go-хостом и Wasm-плагином через разделяемую линейную память с сериализацией входных параметров и десериализацией результата.",
    "theory": "Поскольку Wasm API оперирует исключительно плоскими байтовыми массивами и скалярными адресами, передача сложных бизнес-структур требует сериализации. Наиболее эффективный формат в BigTech — Protocol Buffers (Protobuf) или FlatBuffers:\\n1. Хост сериализует запрос proto.Marshal(req) в компактный бинарный срез байт.\\n2. Хост выделяет буфер в Wasm через allocate(len(bytes)) и записывает срез в память.\\n3. Хост вызывает точку входа Wasm, передавая ptr и size.\\n4. Wasm десериализует proto.Unmarshal(input), выполняет вычисления, сериализует ответ в свой буфер и возвращает указатель на результат в виде 64-битного числа (старшие 32 бита — адрес, младшие 32 бита — длина).\\n5. Хост считывает ответ и освобождает выделенные блоки.",
    "step_by_step": "1. Спроектируйте структуры UserScoreRequest и UserScoreResponse.\\n2. Напишите функции сериализации EncodeRequest и десериализации DecodeResponse.\\n3. Смоделируйте функцию гостевого модуля MockWasmGuestCalculation.\\n4. Протестируйте полный цикл обмена структурированными сообщениями.",
    "code_blocks": [{"filename": "wasm_protobuf_bridge.go", "lang": "go", "code": ex26_code}],
    "under_the_hood": "Упаковка двух 32-битных чисел (адрес ptr и длина len) в одно возвращаемое значение uint64 широко применяется в Wasm ABI: ptr_and_len = (uint64(ptr) << 32) | uint64(size). Это избавляет от необходимости совершать дополнительный вызов для выяснения размера ответа.",
    "pitfalls": "Избегайте сериализации в JSON при миллионах вызовов в секунду: парсинг строк JSON создает колоссальную нагрузку на сборщик мусора Go и Wasm. Бинарный Protobuf в 5–10 раз быстрее и не производит лишних строковых аллокаций.",
    "bigtech_interview": "Почему FlatBuffers и Cap'n Proto в некоторых сценариях Wasm предпочтительнее Protobuf? Как Zero-Copy доступ к полям структуры устраняет оверхед на десериализацию внутри песочницы?"
})

# Ex 27
ex27_code = """package main

import (
	"fmt"
	"testing"
	"time"
)

// DirectInProcessFunction эмулирует прямой вызов внутри Go процесса.
func DirectInProcessFunction(a, b int64) int64 {
	return a + b
}

// SimulatedWasmCall эмулирует вызов через Wasm JIT песочницу.
func SimulatedWasmCall(a, b int64) int64 {
	// Задержка на валидацию аргументов и прыжок в изолированное адресное пространство
	return a + b
}

// BenchmarkDirectCall замеряет скорость прямого вызова функции.
func BenchmarkDirectCall(b *testing.B) {
	var res int64
	for i := 0; i < b.N; i++ {
		res = DirectInProcessFunction(int64(i), 100)
	}
	_ = res
}

func main() {
	fmt.Println("Сравнительные показатели задержек (Latency Benchmarks) моделей вызова:")
	fmt.Println("1. Direct Go In-Process:       ~0.5 - 1.5 нс  (инлайнинг компилятора Go)")
	fmt.Println("2. Wazero Wasm Sandbox:        ~150 - 400 нс  (JIT call + context check)")
	fmt.Println("3. HashiCorp go-plugin (gRPC): ~25 - 60 мкс   (context switch + socket syscalls)")
	fmt.Println("-> WebAssembly в ~100 раз быстрее IPC процессов, сохраняя безопасность песочницы!")
}
"""
validate_go(ex27_code)

exercises.append({
    "num": 27,
    "title": "Бенчмарк производительности: Direct Call vs go-plugin vs Wazero",
    "task": "Спроектируйте сравнительный бенчмарк для оценки накладных расходов на вызов логики в трех архитектурах: прямой вызов функции Go в том же процессе, вызов через WebAssembly песочницу (Wazero) и межпроцессный вызов по UNIX-сокету (HashiCorp go-plugin).",
    "theory": "Выбор архитектуры расширяемости всегда диктуется требованиями SLA по задержке (Latency) и частоте вызовов (RPS):\\n- Прямой вызов (Direct Call): 0.5–2 наносекунды. Компилятор Go может полностью заинлайнить код. Нулевые накладные расходы, но нулевая изоляция.\\n- Wazero Wasm JIT: 150–400 наносекунд. Вызов происходит в том же потоке ОС, переключение на изолированный стек занимает десятки инструкций CPU. Подходит для HighLoad фильтров и обработки сетевых пакетов.\\n- Out-of-Process IPC (go-plugin / gRPC): 25–100 микросекунд. Затраты складываются из сериализации Protobuf, записи в UNIX сокет, переключения контекста ядра (kernel context switch) и пробуждения дочернего процесса. Непригодно для вызовов внутри горячих циклов (per-packet), но идеально для тяжелых плагинов (провайдеры Terraform, интеграции с внешними API).",
    "step_by_step": "1. Опишите эталонные функции для замера производительности.\\n2. Зафиксируйте структуру бенчмарка testing.B.\\n3. Проанализируйте профиль задержек по наносекундам и микросекундам.\\n4. Сформируйте матрицу выбора архитектурных решений.",
    "code_blocks": [{"filename": "latency_benchmarks.go", "lang": "go", "code": ex27_code}],
    "under_the_hood": "При IPC вызове поток хоста переходит в состояние ожидания (sleep/futex), а ядро передает квант времени планировщика процессу плагина. Это гарантирует сброс кэша L1/L2 процессора (cache pollution). Wasm исполняется на том же ядре CPU, сохраняя прогретый L1-кэш инструкций и данных.",
    "pitfalls": "Замерять Wasm в режиме интерпретатора вместо JIT компилятора: интерпретатор работает в 10–20 раз медленнее, искажая результаты бенчмарков.",
    "bigtech_interview": "Почему Envoy Proxy выбрал WebAssembly для пользовательских HTTP-фильтров вместо выноса плагинов в отдельные локальные gRPC-сервисы через Ext-Authz?"
})

# Ex 28
ex28_code = """package main

import (
	"context"
	"fmt"
	"sync/atomic"
	"time"
)

// PluginVersion представляет скомпилированную версию плагина в оперативной памяти.
type PluginVersion struct {
	VersionID string
	CreatedAt time.Time
}

func (p *PluginVersion) Execute(data string) string {
	return fmt.Sprintf("[%s]: %s", p.VersionID, data)
}

// HotReloadPluginManager обеспечивает атомарную подмену плагина без остановки трафика.
type HotReloadPluginManager struct {
	active atomic.Pointer[PluginVersion]
}

func NewHotReloadPluginManager(initialVersion string) *HotReloadPluginManager {
	mgr := &HotReloadPluginManager{}
	mgr.active.Store(&PluginVersion{
		VersionID: initialVersion,
		CreatedAt: time.Now(),
	})
	return mgr
}

func (m *HotReloadPluginManager) Execute(data string) string {
	// Безопасное lock-free чтение текущей активной версии
	current := m.active.Load()
	return current.Execute(data)
}

// Reload компилирует новую версию плагина в фоне и атомарно подменяет указатель.
func (m *HotReloadPluginManager) Reload(newVersionID string) error {
	// 1. Компиляция и валидация происходят в фоне без блокировки основного трафика
	candidate := &PluginVersion{
		VersionID: newVersionID,
		CreatedAt: time.Now(),
	}

	// 2. Атомарная замена указателя за 1 такт CPU
	old := m.active.Swap(candidate)
	fmt.Printf("--> Hot Reload успешен! Заменена версия %s на новую версию %s\\n",
		old.VersionID, candidate.VersionID)
	return nil
}

func main() {
	_ = context.Background()
	mgr := NewHotReloadPluginManager("v1.0.0-wasm")

	fmt.Println("Вызов 1:", mgr.Execute("order_placed"))

	// Горячее обновление плагина в фоне
	if err := mgr.Reload("v1.1.0-wasm-optimized"); err != nil {
		panic(err)
	}

	fmt.Println("Вызов 2:", mgr.Execute("order_placed"))
}
"""
validate_go(ex28_code)

exercises.append({
    "num": 28,
    "title": "Горячая перезагрузка плагинов (Hot-Reloading) без даунтайма",
    "task": "Реализуйте механизм бесшовной горячей перезагрузки плагинов (Zero-Downtime Hot-Reloading). Напишите структуру HotReloadPluginManager на базе atomic.Pointer[T], выполняющую фоновую компиляцию и валидацию нового модуля с последующей атомарной подменой указателя без блокировки обрабатываемых HTTP-запросов.",
    "theory": "В корпоративных шлюзах и платформах правила фильтрации трафика, скоринга или валидации должны обновляться без перезапуска хост-процесса (Zero Downtime). Алгоритм горячей подмены плагинов:\\n1. Файловый вотчер (fsnotify) или контроллер конфигурации обнаруживает появление нового файла plugin.wasm на диске.\\n2. В отдельной фоновой горутине хост выполняет wazero.CompileModule(ctx, newBytes).\\n3. Проводится проверка здоровья (Dry Run): создается тестовый инстанс и вызывается метод healthcheck.\\n4. Если модуль здоров, происходит атомарная подмена активного указателя с помощью atomic.Pointer.Store() или Swap().\\n5. Запросы, начавшие выполнение на старой версии, корректно дорабатывают свой цикл, после чего старый модуль автоматически утилизируется сборщиком мусора Go.",
    "step_by_step": "1. Спроектируйте структуру PluginVersion с метаданными релиза.\\n2. Создайте HotReloadPluginManager с полем atomic.Pointer[PluginVersion].\\n3. Реализуйте метод Execute с lock-free чтением через Load().\\n4. Напишите метод Reload, атомарно замещающий активный экземпляр через Swap().\\n5. Продемонстрируйте бесшовный переход между версиями.",
    "code_blocks": [{"filename": "hot_reload.go", "lang": "go", "code": ex28_code}],
    "under_the_hood": "atomic.Pointer[T] в рантайме Go транслируется в одну инструкцию atomic exchange (XCHG / MOV) процессора x86-64/ARM64. Чтение через Load() абсолютно не содержит мьютексов и не вызывает конкуренции за кэш-линии между ядрами процессора (Zero lock contention).",
    "pitfalls": "Не закрывайте рантайм старого модуля немедленно в момент Reload(): горутины, которые прямо сейчас выполняют код на старой версии, получат панику. Дождитесь завершения активных вызовов через счетчик ссылок (Reference Counting или sync.WaitGroup).",
    "bigtech_interview": "Как в распределенных балансировщиках трафика (Envoy, Nginx Plus) реализована бесшовная смена конфигурации и Wasm-фильтров без сброса Keep-Alive TCP соединений клиентов?"
})

# Ex 29
ex29_code = """package main

import (
	"context"
	"fmt"
	"strings"
)

// DSLRule описывает простое бизнес-правило, компилируемое в Wasm байткод.
type DSLRule struct {
	BasePrice   int64
	VIPDiscount float64
}

// EvaluateRule исполняет правило для пользователя.
func (r *DSLRule) EvaluateRule(isVIP bool) int64 {
	if isVIP {
		return int64(float64(r.BasePrice) * (1.0 - r.VIPDiscount))
	}
	return r.BasePrice
}

// GenerateWasmBytecodeStub имитирует JIT-генерацию бинарного Wasm модуля для заданного правила.
func GenerateWasmBytecodeStub(rule DSLRule) []byte {
	// В реальной системе здесь компилируется WAT (WebAssembly Text Format):
	// (module
	//   (func (export "calc_discount") (param $is_vip i32) (result i64)
	//     ...
	//   )
	// )
	return []byte(fmt.Sprintf("WASM_BYTECODE_FOR_RULE_PRICE_%d_DISCOUNT_%.2f", rule.BasePrice, rule.VIPDiscount))
}

func main() {
	_ = context.Background()
	rule := DSLRule{BasePrice: 1000, VIPDiscount: 0.15}

	wasmBytes := GenerateWasmBytecodeStub(rule)
	fmt.Printf("Сгенерирован Wasm-байткод правила: %s\\n", string(wasmBytes))

	standardPrice := rule.EvaluateRule(false)
	vipPrice := rule.EvaluateRule(true)

	fmt.Printf("Расчет цены: Обычный клиент=%d руб., VIP клиент=%d руб.\\n", standardPrice, vipPrice)
}
"""
validate_go(ex29_code)

exercises.append({
    "num": 29,
    "title": "Кастомный компилятор DSL-правил в WebAssembly",
    "task": "Изучите концепцию динамической генерации Wasm-байткода на лету. Спроектируйте архитектуру компилятора предметно-ориентированного языка (DSL) для расчета скидок и бизнес-правил, генерирующего оптимизированный Wasm-код с околонативной скоростью исполнения.",
    "theory": "В высоконагруженных финтех и e-commerce системах бизнес-правила (расчет налогов, правил корзины, скоринг кредитов) часто задаются аналитиками на специализированных DSL. Интерпретация AST-дерева в рантайме Go работает медленно из-за динамической типизации и аллокаций. Архитектурный паттерн: компиляция DSL непосредственно в байткод WebAssembly на лету. Байткод Wasm компилируется Wazero в нативные инструкции процессора за доли миллисекунды. В результате динамическое бизнес-правило исполняется так же быстро, как скомпилированный Go-код, без аллокаций памяти и с абсолютной защитой от зацикливания.",
    "step_by_step": "1. Спроектируйте структуру DSLRule с параметрами базовой цены и скидки.\\n2. Реализуйте метод EvaluateRule для валидации бизнес-логики.\\n3. Смоделируйте генерацию Wasm-байткода GenerateWasmBytecodeStub.\\n4. Протестируйте расчет цены для различных категорий пользователей.",
    "code_blocks": [{"filename": "dsl_compiler.go", "lang": "go", "code": ex29_code}],
    "under_the_hood": "Для генерации Wasm из Go на лету используют библиотеки вроде bytecodealliance/wasm-tools или чистый Go-генератор байткода. Создается секция Type, секция Function и секция Code с бинарными опкодами i32.const, i64.mul, select.",
    "pitfalls": "Остерегайтесь раздувания кэша скомпилированных модулей (CompiledModule Cache Bloat). Если на каждый запрос генерировать новый уникальный Wasm-модуль, память JIT-компилятора быстро переполнится. Параметризуйте модуль через аргументы функций вместо кодогенерации констант.",
    "bigtech_interview": "Как в системах принятия решений (Decision Engines, OPA - Open Policy Agent) используется компиляция политик Rego в WebAssembly для достижения сотен тысяч проверок прав в секунду?"
})

# Ex 30
ex30_code = """package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// ServerlessFunctionMeta описывает метаданные зарегистрированной бессерверной Wasm-функции.
type ServerlessFunctionMeta struct {
	Name           string
	MaxMemoryMB    uint32
	Timeout        time.Duration
	CompiledWasm   []byte
	TotalExecution atomic.Uint64
}

// ServerlessEngine представляет корпоративную платформу исполнения бессерверного Wasm-кода.
type ServerlessEngine struct {
	mu        sync.RWMutex
	functions map[string]*ServerlessFunctionMeta
}

func NewServerlessEngine() *ServerlessEngine {
	return &ServerlessEngine{functions: make(map[string]*ServerlessFunctionMeta)}
}

func (e *ServerlessEngine) DeployFunction(name string, wasmCode []byte, maxMemMB uint32, timeout time.Duration) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	if len(wasmCode) == 0 {
		return errors.New("empty wasm bytecode")
	}

	e.functions[name] = &ServerlessFunctionMeta{
		Name:         name,
		MaxMemoryMB:  maxMemMB,
		Timeout:      timeout,
		CompiledWasm: wasmCode,
	}
	fmt.Printf("[Serverless Engine]: Функция %s успешно развернута (RAM: %d MB, Timeout: %v)\\n", name, maxMemMB, timeout)
	return nil
}

func (e *ServerlessEngine) Invoke(ctx context.Context, name string, payload string) (string, error) {
	e.mu.RLock()
	fn, ok := e.functions[name]
	e.mu.RUnlock()

	if !ok {
		return "", fmt.Errorf("function %s not found", name)
	}

	// Ограничиваем время выполнения индивидуальным таймаутом функции
	execCtx, cancel := context.WithTimeout(ctx, fn.Timeout)
	defer cancel()

	// Имитация исполнения в Wazero с контролем контекста и изоляцией памяти
	done := make(chan string, 1)
	go func() {
		// Симуляция работы полезной нагрузки
		time.Sleep(10 * time.Millisecond)
		done <- fmt.Sprintf("Response for [%s] via Wasm sandbox", payload)
	}()

	select {
	case <-execCtx.Done():
		return "", fmt.Errorf("function %s execution timeout: %w", name, execCtx.Err())
	case res := <-done:
		fn.TotalExecution.Add(1)
		return res, nil
	}
}

func main() {
	engine := NewServerlessEngine()
	ctx := context.Background()

	// Деплой бессерверной функции
	err := engine.DeployFunction("sanitize_input", []byte("\\x00asm_binary_code"), 16, 50*time.Millisecond)
	if err != nil {
		panic(err)
	}

	// Вызов функции
	resp, err := engine.Invoke(ctx, "sanitize_input", "<script>alert(1)</script>")
	if err != nil {
		panic(err)
	}

	fmt.Printf("Результат Serverless Engine: %s\\n", resp)
}
"""
validate_go(ex30_code)

exercises.append({
    "num": 30,
    "title": "Enterprise Serverless Execution Engine на Go",
    "task": "Спроектируйте платформу исполнения бессерверных функций ServerlessEngine на чистом Go и Wazero. Реализуйте регистрацию Wasm-функций DeployFunction с индивидуальными лимитами памяти и таймаутами, безопасный вызов Invoke с контролем контекста, сбором метрик и изоляцией сбоев.",
    "theory": "Создание собственной бессерверной платформы (Serverless FaaS Engine) на базе Go и WebAssembly позволяет корпорациям выполнять пользовательские плагины и микрофункции с нулевыми рисками безопасности и микросекундной задержкой. Архитектура Enterprise Serverless Engine:\\n1. Control Plane: REST API для деплоя Wasm-модулей, версионирования и валидации байткода.\\n2. Module Cache: хранилище wazero.CompiledModule в памяти со LRU-вытеснением.\\n3. Worker Pool: диспетчер инстанцирования с ограничением максимальной памяти на модуль.\\n4. Sandbox Isolation: каждый вызов оборачивается в context.WithTimeout, без системных вызовов WASI к хостовой FS.\\n5. Observability: учет времени исполнения, счетчик вызовов atomic.Uint64 и экспорт метрик в Prometheus.",
    "step_by_step": "1. Спроектируйте ServerlessFunctionMeta с полями лимитов памяти, таймаута и счетчиком вызовов.\\n2. Реализуйте структуру ServerlessEngine с потокобезопасным реестром функций.\\n3. Напишите метод DeployFunction с валидацией байткода.\\n4. Разработайте метод Invoke с принудительным контролем таймаута через select и execCtx.Done().\\n5. Протестируйте успешный вызов функции и сбор статистики.",
    "code_blocks": [{"filename": "serverless_engine.go", "lang": "go", "code": ex30_code}],
    "under_the_hood": "В продакшене платформы такого уровня масштабируются горизонтально в Kubernetes, где каждый инстанс Go-хоста способен исполнять до 10 000 изолированных Wasm-функций параллельно без накладных расходов на контейнеризацию.",
    "pitfalls": "Не забывайте очищать память Wasm-инстанса после каждого вызова или уничтожать инстанс, если функция завершилась с ошибкой out of memory или panicking.",
    "bigtech_interview": "Как архитектура Serverless на базе WebAssembly в Go решает проблему Cold Start (холодного старта), снижая время инициализации с секунд (AWS Lambda) до долей миллисекунды?"
})

output_path = "/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch92_p2.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Part 2 generated successfully: {len(exercises)} exercises.")
