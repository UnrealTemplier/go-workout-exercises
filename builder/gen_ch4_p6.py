# Chapter 4 Part 6: Exercises 96 to 111

exercises = [
    {
        "num": 96,
        "title": "Игнорирование нескольких возвращаемых значений функции через _",
        "task": "Используй \"blank identifier\" (_): прочитай три значения из функции, но используй только одно. Напиши функцию getCoords() (x, y, z int) и вызови её, игнорируя y и z.",
        "theory": """
Функция `getCoords() (int, int, int)` возвращает 3 координаты:
- Если требуется только координата `x`, остальные значения отбрасываются с помощью `x, _, _ := getCoords()`;
- Компилятор не выделяет память под неиспользуемые переменные.
""",
        "step_by_step": """
1. Объявляем `func getCoords() (int, int, int)`.
2. Вызываем функцию с `x, _, _ := getCoords()`.
3. Печатаем только `x`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func getCoords() (x, y, z int) {
	return 100, 250, -50
}

func main() {
	// Извлекаем только координату X
	x, _, _ := getCoords()

	fmt.Printf("Координата X: %d (Y и Z успешно проигнорированы)\\n", x)
}""",
                "note": "Отбрасывание значений функции"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Координата X: 100 (Y и Z успешно проигнорированы)""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
При вызове функции значения `y` и `z` возвращаются в регистрах процессора, но не сохраняются в стек фрейма `main`.
""",
        "pitfalls": """
- Игнорирование всех возвращаемых значений без присваивания: `getCoords()` просто отбросит все три значения.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Зачем нужен `_` в импортах пакетов (Blank Import `import _ "net/http/pprof"`)?»
**Ответ:** Для выполнения побочных эффектов: инициализации пакета (вызова его функций `init()`) без прямого обращения к его экспортируемым идентификаторам.
"""
    },
    {
        "num": 97,
        "title": "Compile-time константные выражения vs runtime вызовы функций",
        "task": "Compile-time вычисления: Объяви константу, равную результату арифметической операции других констант. Затем попробуй присвоить константе результат вызова функции (например, math.Sqrt(4)). Пойми разницу между compile-time и runtime.",
        "theory": """
**Граница Compile-Time и Runtime в Go:**
1. Константами могут быть только выражения, состоящие из других констант и встроенных операторов (`+`, `-`, `*`, `len()`, `unsafe.Sizeof()`);
2. **Любой вызов пользовательской или стандартной функции** (например, `math.Sqrt(4)`) является **Runtime-операцией** и НЕ может быть присвоен константе `const`.
""",
        "step_by_step": """
1. Объявляем константы `HoursInDay = 24`, `DaysInWeek = 7`, `HoursInWeek = HoursInDay * DaysInWeek`.
2. Показываем ошибку при попытке `const Sqrt4 = math.Sqrt(4)`.
3. Исправляем через `var`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"math"
)

// 1. Успешные Compile-Time вычисления:
const (
	HoursInDay  = 24
	DaysInWeek  = 7
	HoursInWeek = HoursInDay * DaysInWeek // 168
)

// 2. Не скомпилируется в const:
// const SqrtVal = math.Sqrt(4) // ОШИБКА: math.Sqrt(4) (value of type float64) is not constant

// Runtime вычисление через var:
var SqrtVal = math.Sqrt(4)

func main() {
	fmt.Printf("Часов в неделе (Compile-Time const): %d\\n", HoursInWeek)
	fmt.Printf("Квадратный корень (Runtime var):       %.1f\\n", SqrtVal)
}""",
                "note": "Compile-Time vs Runtime вычисления"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Часов в неделе (Compile-Time const): 168
# Квадратный корень (Runtime var):       2.0""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Компилятор Go не имеет полноценного интерпретатора (constexpr/consteval, как в C++20), поэтому вызовы функций в константах запрещены архитектурно.
""",
        "pitfalls": """
- Попытка инициализировать константу через `time.Now()`: время выполнения известно только при запуске.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какие встроенные функции Go разрешено вызывать внутри выражений `const`?»
**Ответ:** Только `len()`, `cap()` (для массивов), `unsafe.Sizeof()`, `unsafe.Alignof()`, `unsafe.Offsetof()`, `complex()`, `real()`, `imag()`.
"""
    },
    {
        "num": 98,
        "title": "Гарантия обнуления всех полей сложной структуры без инициализации",
        "task": "Напиши программу, которая демонстрирует нулевые значения переменных разных типов. Создай структуру с полями разных типов и выведи её без инициализации — все поля должны быть нулевыми.",
        "theory": """
При создании структуры `var s MyStruct` абсолютно **все её поля** (примитивные, вложенные структуры, указатели, слайсы) гарантированно получают свои Zero Values.
""",
        "step_by_step": """
1. Создаем структуру `UserProfile` со всеми типами полей.
2. Объявляем `var u UserProfile`.
3. Печатаем через `%+v`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type Stats struct {
	LoginCount int
	Rating     float64
}

type UserProfile struct {
	ID        int64
	Username  string
	IsAdmin   bool
	AvatarURL *string
	Roles     []string
	Settings  map[string]bool
	UserStats Stats
}

func main() {
	var u UserProfile

	fmt.Println("=== НУЛЕВЫЕ ЗНАЧЕНИЯ ПОЛЕЙ СТРУКТУРЫ ===")
	fmt.Printf("ID:        %d\\n", u.ID)
	fmt.Printf("Username:  %q\\n", u.Username)
	fmt.Printf("IsAdmin:   %t\\n", u.IsAdmin)
	fmt.Printf("AvatarURL: %v\\n", u.AvatarURL)
	fmt.Printf("Roles:     %v (nil? %t)\\n", u.Roles, u.Roles == nil)
	fmt.Printf("Settings:  %v (nil? %t)\\n", u.Settings, u.Settings == nil)
	fmt.Printf("UserStats: %+v\\n", u.UserStats)
}""",
                "note": "Zero value для сложной структуры"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# === НУЛЕВЫЕ ЗНАЧЕНИЯ ПОЛЕЙ СТРУКТУРЫ ===
# ID:        0
# Username:  ""
# IsAdmin:   false
# AvatarURL: <nil>
# Roles:     [] (nil? true)
# Settings:  map[] (nil? true)
# UserStats: {LoginCount:0 Rating:0}""",
                "note": "Идеально обнуленная структура"
            }
        ],
        "under_the_hood": """
Рантайм за один системный вызов `memset` обнуляет всю память структуры.
""",
        "pitfalls": """
- Попытка записи в `u.Settings["dark_mode"] = true`: мапа `nil`, поэтому запись вызовет панику. Перед записью мапу нужно инициализировать через `make()`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Безопасно ли читать из `u.Settings["dark_mode"]`, если мапа равна `nil`?»
**Ответ:** ДА! Чтение из `nil`-мапы в Go абсолютно безопасно и вернет нулевое значение типа значения (`false`), без паники.
"""
    },
    {
        "num": 99,
        "title": "Инициализация ссылочных типов через make() (slice, map, channel)",
        "task": "Используй make() для создания slice, map, channel. Объясни, почему make() нужен именно для этих типов, а для других — нет.",
        "theory": """
**Почему `make()` существует только для slice, map и channel?**
Эти три типа являются сложными дескрипторами (ссылочными типами рантайма):
1. **`slice`** требует аллокации базового массива и настройки полей `Data`, `Len`, `Cap`;
2. **`map`** требует создания структуры `hmap` и массива бакетов;
3. **`channel`** требует создания структуры `hchan`, кольцевого буфера и очередей ожидания горутин `sudog`.

Обычные типы (`int`, `struct`) не имеют внутренних сложных структур и создаются через `var` или `new()`.
""",
        "step_by_step": """
1. Создаем срез через `make([]int, len, cap)`.
2. Создаем мапу через `make(map[string]int, hint)`.
3. Создаем буферизованный канал через `make(chan int, buffer)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	// 1. Slice: len = 3, cap = 10
	s := make([]int, 3, 10)

	// 2. Map с предварительным хинтом емкости 50
	m := make(map[string]int, 50)
	m["connections"] = 100

	// 3. Channel: буферизованный канал на 5 сообщений
	ch := make(chan int, 5)
	ch <- 42

	fmt.Printf("Slice:   len=%d, cap=%d\\n", len(s), cap(s))
	fmt.Printf("Map:     len=%d, key[connections]=%d\\n", len(m), m["connections"])
	fmt.Printf("Channel: len=%d, cap=%d, received=%d\\n", len(ch), cap(ch), <-ch)
}""",
                "note": "Инициализация через make()"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Slice:   len=3, cap=10
# Map:     len=1, key[connections]=100
# Channel: len=1, cap=5, received=42""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Компилятор транслирует вызовы `make` в рантайм функции: `runtime.makeslice`, `runtime.makemap_small` / `runtime.makemap` и `runtime.makechan`.
""",
        "pitfalls": """
- Вызов `make(int)`: компилятор выдаст ошибку `cannot make type int`. `make` применим **только** к слайсам, мапам и каналам.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Зачем указывать второй аргумент hint в `make(map[string]int, 1000)`?»
**Ответ:** Это заранее аллоцирует нужное количество бакетов памяти. При добавлении 1000 элементов мапе не придется многократно реаллоцироваться и перестраивать хэш-таблицу (Rehashing), что ускоряет заполнение в 3–5 раз.
"""
    },
    {
        "num": 100,
        "title": "Отложенные вызовы defer и порядок выполнения LIFO (стек)",
        "task": "Напиши программу с defer: отложи несколько вызовов функций. Покажи, что они выполняются в порядке LIFO (последний defer — первым).",
        "theory": """
**Ключевое слово `defer`:**
1. Откладывает выполнение функции до момента выхода из текущей окружающей функции;
2. Аргументы функции вычисляются **немедленно** в точке вызова `defer`;
3. Вызовы накапливаются в стек горутины и исполняются в порядке **LIFO (Last In, First Out)** — последний добавленный `defer` сработает самым первым.
""",
        "step_by_step": """
1. В цикле откладываем вызовы `defer fmt.Println(i)`.
2. Наблюдаем обратный порядок вывода 3 -> 2 -> 1 -> 0.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	fmt.Println("Старт функции main")

	defer fmt.Println("Defer #1 (первый зарегистрирован -> сработает третьим)")
	defer fmt.Println("Defer #2 (второй зарегистрирован -> сработает вторым)")
	defer fmt.Println("Defer #3 (третий зарегистрирован -> сработает ПЕРВЫМ)")

	for i := 1; i <= 3; i++ {
		defer fmt.Printf("Цикл defer i = %d\\n", i)
	}

	fmt.Println("Конец тела функции main (сейчас начнут выполняться defer)")
}""",
                "note": "Порядок LIFO в defer"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Старт функции main
# Конец тела функции main (сейчас начнут выполняться defer)
# Цикл defer i = 3
# Цикл defer i = 2
# Цикл defer i = 1
# Defer #3 (третий зарегистрирован -> сработает ПЕРВЫМ)
# Defer #2 (второй зарегистрирован -> сработает вторым)
# Defer #1 (первый зарегистрирован -> сработает третьим)""",
                "note": "Демонстрация LIFO стека"
            }
        ],
        "under_the_hood": """
Начиная с Go 1.14 компилятор оптимизирует `defer` через Open-Coded Defers (встраивание вызовов прямо перед `RET` инструкцией функции), сводя накладные расходы на вызов `defer` почти к нулю ($\approx 1.5$ нс).
""",
        "pitfalls": """
- Вызов `defer file.Close()` внутри длинного цикла: файлы не закроются до завершения всей функции `main`, что приведет к исчерпанию файловых дескрипторов. В циклах используют замыкания или явное закрытие.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Когда вычисляются аргументы функции, переданной в `defer`?»
**Ответ:** Аргументы вычисляются **немедленно в момент вызова строки `defer`**, а не в момент фактического исполнения функции при выходе.
"""
    },
    {
        "num": 101,
        "title": "Самоссылающиеся структуры (Self-Referential Structs) и односвязный список",
        "task": "Создай \"self-referential\" структуру: type Node struct { Value int; Next *Node }. Создай связный список из 3 узлов вручную. Обойди список и выведи значения.",
        "theory": """
**Самоссылающиеся структуры (Связные списки, Деревья, Графы):**
- Структура не может содержать саму себя по значению (`type Node struct { Next Node }` — бесконечный размер);
- Структура может содержать **указатель на саму себя** (`Next *Node`), так как указатель имеет фиксированный размер 8 байт;
- Завершение списка обозначается `Next == nil`.
""",
        "step_by_step": """
1. Объявляем `type Node struct { Value int; Next *Node }`.
2. Создаем 3 узла и связываем их: `n1 -> n2 -> n3`.
3. В цикле `for curr != nil` обходим список.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type Node struct {
	Value int
	Next  *Node
}

func main() {
	// Создаем 3 узла связного списка
	n3 := &Node{Value: 30, Next: nil}
	n2 := &Node{Value: 20, Next: n3}
	n1 := &Node{Value: 10, Next: n2}

	fmt.Println("Обход односвязного списка:")
	curr := n1
	for curr != nil {
		fmt.Printf("[%d] -> ", curr.Value)
		curr = curr.Next
	}
	fmt.Println("nil")
}""",
                "note": "Односвязный список на структурах"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Обход односвязного списка:
# [10] -> [20] -> [30] -> nil""",
                "note": "Результат обхода"
            }
        ],
        "under_the_hood": """
Каждый узел аллоцируется в куче, поле `Next` хранит 64-битный адрес следующего узла.
""",
        "pitfalls": """
- Создание кольцевой ссылки (`n3.Next = n1`): цикл `for curr != nil` станет бесконечным и зависнет.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как обнаружить цикл в связном списке за $O(N)$ времени и $O(1)$ памяти?»
**Ответ:** Алгоритмом двух указателей Флойда («Черепаха и Заяц» / Fast and Slow pointers).
"""
    },
    {
        "num": 102,
        "title": "Матрица всех способов объявления констант в языке Go",
        "task": "Объяви константы всеми способами: const Pi = 3.14; const Pi float64 = 3.14; const ( Monday = iota; Tuesday; Wednesday ); const ( _ = iota; KB = 1 << (10 * iota); MB; GB; TB ). Выведи все значения.",
        "theory": """
Обобщение всех синтаксических форм `const`:
1. Одиночная нетипизированная;
2. Одиночная типизированная;
3. Перечисление `iota`;
4. Вычисляемые битовые сдвиги.
""",
        "step_by_step": """
1. Объявляем константы всеми 4 способами.
2. Выводим значения.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

// Способ 1: Нетипизированная константа
const PiUntyped = 3.14159

// Способ 2: Типизированная константа
const PiTyped float64 = 3.14159

// Способ 3: Автоинкремент iota
const (
	Monday = iota
	Tuesday
	Wednesday
)

// Способ 4: Степени сдвига iota
const (
	_          = iota
	KB uint64 = 1 << (10 * iota)
	MB
	GB
	TB
)

func main() {
	fmt.Printf("1. PiUntyped: %v (%T)\\n", PiUntyped, PiUntyped)
	fmt.Printf("2. PiTyped:   %v (%T)\\n", PiTyped, PiTyped)
	fmt.Printf("3. Monday: %d, Tuesday: %d, Wednesday: %d\\n", Monday, Tuesday, Wednesday)
	fmt.Printf("4. KB: %d, MB: %d, GB: %d, TB: %d\\n", KB, MB, GB, TB)
}""",
                "note": "Все способы объявления констант"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. PiUntyped: 3.14159 (float64)
# 2. PiTyped:   3.14159 (float64)
# 3. Monday: 0, Tuesday: 1, Wednesday: 2
# 4. KB: 1024, MB: 1048576, GB: 1073741824, TB: 1099511627776""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Все константы подставляются в код компилятором без оверхеда.
""",
        "pitfalls": """
- Использование `var` для неизменяемых настроек.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем преимущество `const` перед `var` для производительности?»
**Ответ:** Компилятор может выполнять Constant Folding, удалять мертвые ветки кода (`Dead Code Elimination`) и подставлять значения непосредственно в регистры.
"""
    },
    {
        "num": 103,
        "title": "Функция DayName(day int) string и валидация iota-перечислений",
        "task": "Напиши программу с константами-перечислениями для дней недели (Sunday = iota ... Saturday). Напиши функцию DayName(day int) string, возвращающую название дня.",
        "theory": """
Реализация функции отображения кода дня в русскоязычное название с валидацией диапазона $[0, 6]$.
""",
        "step_by_step": """
1. Объявляем константы `Sunday` .. `Saturday`.
2. Реализуем функцию `DayName(day int) string`.
3. Тестируем валидные дни и ошибочные значения.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

const (
	Sunday = iota
	Monday
	Tuesday
	Wednesday
	Thursday
	Friday
	Saturday
)

func DayName(day int) string {
	names := [...]string{
		"Воскресенье",
		"Понедельник",
		"Вторник",
		"Среда",
		"Четверг",
		"Пятница",
		"Суббота",
	}

	if day < 0 || day >= len(names) {
		return "Некорректный день"
	}
	return names[day]
}

func main() {
	fmt.Printf("День %d: %s\\n", Monday, DayName(Monday))
	fmt.Printf("День %d: %s\\n", Friday, DayName(Friday))
	fmt.Printf("День %d: %s\\n", 99, DayName(99))
}""",
                "note": "Маппинг enum в строку"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# День 1: Понедельник
# День 5: Пятница
# День 99: Некорректный день""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Срез `names` размещается в `.rodata`, поиск по индексу выполняется за $O(1)$.
""",
        "pitfalls": """
- Паника `index out of range` при отсутствии проверки `day >= len(names)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему использование массива `[...]string` быстрее, чем `switch-case` для плотных enum?»
**Ответ:** Доступ по индексу массива компилируется в одну команду косвенной адресации памяти `MOVQ names(,%rax,8), %rax`, тогда как большой `switch` может превратиться в серию условных переходов `CMP/JNE`.
"""
    },
    {
        "num": 104,
        "title": "Менеджер битовых флагов: функции HasFlag, AddFlag, RemoveFlag",
        "task": "Создай константы с iota для битовых флагов: FlagRead = 1 << iota, FlagWrite, FlagExecute. Напиши функции HasFlag(flags, flag int) bool, AddFlag, RemoveFlag.",
        "theory": """
**Паттерны битовых операций:**
- Проверка: `(flags & flag) != 0`
- Добавление: `flags | flag`
- Удаление: `flags &^ flag` (Bit Clear)
- Переключение: `flags ^ flag`
""",
        "step_by_step": """
1. Объявляем флаги `FlagRead`, `FlagWrite`, `FlagExecute`.
2. Реализуем хелперы `HasFlag`, `AddFlag`, `RemoveFlag`.
3. Тестируем полный жизненный цикл прав.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

const (
	FlagRead    = 1 << iota // 1 (001)
	FlagWrite               // 2 (010)
	FlagExecute             // 4 (100)
)

func HasFlag(flags, flag int) bool { return (flags & flag) != 0 }
func AddFlag(flags, flag int) int  { return flags | flag }
func RemoveFlag(flags, flag int) int { return flags &^ flag }

func main() {
	var perms int

	// Добавляем Read и Execute
	perms = AddFlag(perms, FlagRead)
	perms = AddFlag(perms, FlagExecute)

	fmt.Printf("Права: %03b\\n", perms)
	fmt.Printf("Есть чтение?    %t\\n", HasFlag(perms, FlagRead))
	fmt.Printf("Есть запись?    %t\\n", HasFlag(perms, FlagWrite))
	fmt.Printf("Есть исполнение?%t\\n\\n", HasFlag(perms, FlagExecute))

	// Удаляем исполнение
	perms = RemoveFlag(perms, FlagExecute)
	fmt.Printf("После RemoveFlag(Execute): %03b\\n", perms)
	fmt.Printf("Есть исполнение? %t\\n", HasFlag(perms, FlagExecute))
}""",
                "note": "Менеджер битовых прав"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Права: 101
# Есть чтение?    true
# Есть запись?    false
# Есть исполнение?true
# 
# После RemoveFlag(Execute): 001
# Есть исполнение? false""",
                "note": "Результат работы"
            }
        ],
        "under_the_hood": """
Все три функции встраиваются компилятором (Function Inlining) в вызывающий код без накладных расходов на вызов функции.
""",
        "pitfalls": """
- Использование `flags - flag` для удаления: если флага не было, вычитание сломает всю маску. Всегда используйте `&^`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в Go объявить атомарный флаг состояния для конкурентного доступа без мьютексов?»
**Ответ:** С помощью пакета `sync/atomic`: `atomic.Uint32` и методов `Load()`, `Store()`, `Or()`, `And()`.
"""
    },
    {
        "num": 105,
        "title": "Сверхбольшие нетипизированные константы (1 << 100) и пакет math/big",
        "task": "Напиши программу, которая демонстрирует \"untyped constants\": const Big = 1 << 100. Присвой это значение float64 и big.Int. Объясни, почему это работает.",
        "theory": """
**Нетипизированные константы произвольной точности:**
- Число $2^{100} = 1\,267\,650\,600\,228\,229\,401\,496\,703\,205\,376$;
- Оно не помещается в `int64` ($< 2^{63}$), но помещается в `float64` (диапазон до $10^{308}$) и в `big.Int` из пакета `math/big`;
- Компилятор вычисляет константу без переполнения.
""",
        "step_by_step": """
1. Объявляем `const Big = 1 << 100`.
2. Присваиваем `var f float64 = Big`.
3. Создаем `big.Int` через строковое представление.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"math/big"
)

const Big = 1 << 100 // 2^100

func main() {
	// 1. Присвоение во float64 (с экспоненциальным округлением)
	var f float64 = Big
	fmt.Printf("Big как float64: %e\\n", f)

	// 2. Точное представление через math/big
	bigInt := new(big.Int)
	bigInt.SetString("1267650600228229401496703205376", 10)
	fmt.Printf("Big как big.Int: %s\\n", bigInt.String())
}""",
                "note": "Сверхбольшие константы в Go"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Big как float64: 1.267651e+30
# Big как big.Int: 1267650600228229401496703205376""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Пакет `math/big` использует срез машинных слов `[]big.Word` для хранения чисел произвольной разрядности.
""",
        "pitfalls": """
- Попытка написать `var i int64 = Big`: компилятор выдаст ошибку `constant 12676506... overflows int64`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каковы накладные расходы использования `math/big.Int` в сравнении с примитивными числами?»
**Ответ:** `math/big.Int` аллоцирует память в куче на каждую математическую операцию и работает в сотни раз медленнее нативных регистров процессора. Его используют только в криптографии (RSA, эллиптические кривые) и блокчейне (Ethereum wei).
"""
    },
    {
        "num": 106,
        "title": "Сырые многострочные литералы (Raw String) vs интерпретируемые строки",
        "task": "Создай константу строку с многострочным значением (raw string literal с backticks). И константу с интерпретируемыми escape-последовательностями (двойные кавычки). Покажи разницу.",
        "theory": """
Два типа строковых констант:
1. **Raw String (`\`...\``):** сохраняет все переносы строк, пробелы и символы без интерпретации `\\n` или `\\t` (идеально для SQL, JSON, HTML, Regexp);
2. **Interpreted String (`"..."`):** обрабатывает спецсимволы `\\n`, `\\t`, `\\"`.
""",
        "step_by_step": """
1. Создаем Raw JSON константу в бэктиках.
2. Создаем Interpreted строку с `\\n` и `\\t`.
3. Сравниваем вывод.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

// 1. Raw String Literal (обратные кавычки):
const RawJSON = `{
  "service": "billing",
  "port": 8080,
  "status": "active"
}`

// 2. Interpreted String (двойные кавычки):
const Interpreted = "Строка 1\\n\\tСтрока 2 (с табуляцией)\\nСтрока 3"

func main() {
	fmt.Println("=== RAW STRING ===")
	fmt.Println(RawJSON)

	fmt.Println("\\n=== INTERPRETED STRING ===")
	fmt.Println(Interpreted)
}""",
                "note": "Сравнение типов строковых литералов"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# === RAW STRING ===
# {
#   "service": "billing",
#   "port": 8080,
#   "status": "active"
# }
# 
# === INTERPRETED STRING ===
# Строка 1
# 	Строка 2 (с табуляцией)
# Строка 3""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
В Raw строках символ перевода каретки Windows `\\r` автоматически удаляется компилятором для обеспечения идентичности строк на Linux и Windows.
""",
        "pitfalls": """
- В Raw строке невозможно экранировать символ обратной кавычки `\``: для его вставки приходится использовать конкатенацию `"foo` + "`" + `bar"`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему SQL-запросы и регулярные выражения в Go всегда оформляют в бэктиках `\`...\``?»
**Ответ:** Чтобы не экранировать спецсимволы регулярок `\\d+` как `\\\\d+` и форматировать сложные SQL-запросы на нескольких строках без конкатенации.
"""
    },
    {
        "num": 107,
        "title": "Имитация константного эффекта для композитных типов через интерфейсы",
        "task": "Напиши программу, которая пытается изменить константу (получи ошибку компиляции). Затем создай \"константный\" эффект через const vs var с неизменяемым типом.",
        "theory": """
Так как в Go нельзя объявить `const config = Config{...}`, константный эффект для структур создают через:
1. Приватную переменную пакета;
2. Экспорт только геттеров или интерфейса без сеттеров.
""",
        "step_by_step": """
1. Создаем структуру с приватными полями.
2. Предоставляем доступ только на чтение.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type ReadOnlyConfig struct {
	host string
	port int
}

func (c ReadOnlyConfig) Host() string { return c.host }
func (c ReadOnlyConfig) Port() int    { return c.port }

var DefaultConfig = ReadOnlyConfig{host: "10.0.0.1", port: 9000}

func main() {
	fmt.Printf("Конфигурация: %s:%d\\n", DefaultConfig.Host(), DefaultConfig.Port())
	// Внешний код не имеет доступа к приватным полям host/port для изменения!
}""",
                "note": "Имитация константности для структур"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Конфигурация: 10.0.0.1:9000""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
При вызове геттеров структура передается по значению (Value Receiver), исключая мутацию оригинала.
""",
        "pitfalls": """
- Возврат указателя `*Config` из геттера: клиент сможет изменить поля по указателю.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как сделать срез неизменяемым в Go?»
**Ответ:** Возвращать копию среза через `make` + `copy`, либо возвращать элементы поштучно через функцию `Get(index int) T`.
"""
    },
    {
        "num": 108,
        "title": "Запрет константных срезов и мап и паттерн безопасного доступа через копирование",
        "task": "Создай константный массив (или слайс-литерал) через const — получи ошибку. Объясни, почему в Go нельзя создать константу-слайс или константу-мапу. Найди обходной путь (функция, возвращающая копию).",
        "theory": """
**Почему в Go нет `const mySlice = []int{1, 2}`:**
1. Слайсы и мапы требуют динамической аллокации памяти в куче (Heap Allocation) в рантайме;
2. Константы обязаны разрешаться статически на этапе компиляции без участия рантайма;
3. Паттерн безопасного доступа: приватная переменная + функция возврата независимой копии `copy()`.
""",
        "step_by_step": """
1. Показываем ошибку при `const List = []int{1, 2}`.
2. Реализуем безопасную функцию `GetAllowedRoles() []string`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

// const BadSlice = []string{"admin", "user"} // ОШИБКА: const initializer []string{...} is not a constant

// Приватный срез пакета:
var allowedRoles = []string{"admin", "operator", "auditor"}

// Безопасный доступ: возвращаем независимую копию
func GetAllowedRoles() []string {
	cp := make([]string, len(allowedRoles))
	copy(cp, allowedRoles)
	return cp
}

func main() {
	roles := GetAllowedRoles()
	roles[0] = "HACKER" // Мутация копии не затрагивает оригинал!

	fmt.Println("Локальная копия:", roles)
	fmt.Println("Оригинал в пакете:", GetAllowedRoles())
}""",
                "note": "Безопасный возврат копии среза"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Локальная копия: [HACKER operator auditor]
# Оригинал в пакете: [admin operator auditor]""",
                "note": "Оригинал защищен от изменений"
            }
        ],
        "under_the_hood": """
Функция `copy()` вызывает ассемблерный метод `runtime.memmove` для быстрого копирования байт.
""",
        "pitfalls": """
- Прямой возврат `return allowedRoles`: клиент сможет изменить `allowedRoles[0] = "hacker"`, взломав безопасность всего сервиса.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go нет ключевого слова `readonly` или `const` для параметров функций, как в C++ (`const std::vector&`)?»
**Ответ:** Создатели Go сознательно стремились к максимальной простоте системы типов. Вместо усложнения компилятора модификаторами константности в Go используется передача по значению (копирование) или инкапсуляция через интерфейсы.
"""
    },
    {
        "num": 109,
        "title": "Изоляция и сброс iota в 0 в независимых константных блоках",
        "task": "Используй iota в разных константных группах. Покажи, что iota сбрасывается в 0 в каждой новой группе const ().",
        "theory": """
Область действия `iota`:
- `iota` строго привязана к конкретному блоку `const (...)`;
- При завершении блока `}` счетчик `iota` уничтожается;
- В следующем блоке `const (...)` счетчик гарантированно начинается заново с `0`.
""",
        "step_by_step": """
1. Создаем блок констант цветов (0, 1, 2).
2. Создаем отдельный блок констант размеров (0, 1, 2).
3. Проверяем сброс `iota`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

// Группа 1: Цвета
const (
	Red   = iota // 0
	Green        // 1
	Blue         // 2
)

// Группа 2: Размеры (iota сбрасывается в 0)
const (
	Small  = iota // 0
	Medium        // 1
	Large         // 2
)

func main() {
	fmt.Printf("Цвета:   Red=%d, Green=%d, Blue=%d\\n", Red, Green, Blue)
	fmt.Printf("Размеры: Small=%d, Medium=%d, Large=%d\\n", Small, Medium, Large)
}""",
                "note": "Сброс iota в каждой группе"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Цвета:   Red=0, Green=1, Blue=2
# Размеры: Small=0, Medium=1, Large=2""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Компилятор сбрасывает внутреннюю переменную `iota = 0` при входе в обработчик грамматики `parseConstGroup`.
""",
        "pitfalls": """
- Объединение несвязанных констант в один блок `const (...)`, из-за чего их значения начнут смешиваться.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Чему будет равен `iota` в одиночном объявлении `const X = iota`?»
**Ответ:** `0`.
"""
    },
    {
        "num": 110,
        "title": "Диспетчер математических операций Calculate через iota-enum и switch",
        "task": "Создай константы для математических операций с iota и оператором: OpAdd = iota, OpSub и т.д. Напиши функцию Calculate(op int, a, b float64) float64, использующую switch.",
        "theory": """
Паттерн Command Dispatcher на базе `iota`:
- `OpAdd = iota`
- `OpSub`
- `OpMul`
- `OpDiv`
""",
        "step_by_step": """
1. Объявляем константы операций.
2. Реализуем функцию `Calculate(op int, a, b float64) (float64, error)`.
3. Тестируем все операции и деление на ноль.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"errors"
	"fmt"
)

type Operation int

const (
	OpAdd Operation = iota
	OpSub
	OpMul
	OpDiv
)

func Calculate(op Operation, a, b float64) (float64, error) {
	switch op {
	case OpAdd:
		return a + b, nil
	case OpSub:
		return a - b, nil
	case OpMul:
		return a * b, nil
	case OpDiv:
		if b == 0 {
			return 0, errors.New("деление на ноль")
		}
		return a / b, nil
	default:
		return 0, errors.New("неизвестная операция")
	}
}

func main() {
	res1, _ := Calculate(OpAdd, 15, 5)
	res2, _ := Calculate(OpMul, 15, 5)
	res3, _ := Calculate(OpDiv, 15, 5)

	fmt.Printf("15 + 5 = %.1f\\n", res1)
	fmt.Printf("15 * 5 = %.1f\\n", res2)
	fmt.Printf("15 / 5 = %.1f\\n", res3)
}""",
                "note": "Калькулятор на iota и switch"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 15 + 5 = 20.0
# 15 * 5 = 75.0
# 15 / 5 = 3.0""",
                "note": "Результаты вычислений"
            }
        ],
        "under_the_hood": """
Плотный `switch` по `iota` (0, 1, 2, 3) компилятор оптимизирует в Jump Table (таблицу прямых переходов), работающую за $O(1)$ без последовательных сравнений.
""",
        "pitfalls": """
- Забыть ветку `default` для обработки невалидных кодов операций.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «При каких условиях компилятор Go превращает `switch` в Jump Table?»
**Ответ:** Когда значения `case` являются плотными целыми константами (например, 0, 1, 2, 3, 4 как в `iota`), а количество веток $\ge 4$.
"""
    },
    {
        "num": 111,
        "title": "Глубокий сравнительный анализ типизированных и нетипизированных констант",
        "task": "Напиши программу с \"typed\" и \"untyped\" константами. Покажи, что untyped константу можно присвоить любому совместимому типу, а typed — только своему типу.",
        "theory": """
**Финальное закрепление теории констант:**
- **Typed (`const Max int32 = 100`):** жестко привязана к `int32`. Попытка присвоить `var y int64 = Max` вызовет ошибку компиляции;
- **Untyped (`const Limit = 100`):** может быть присвоена `int`, `int8`, `int16`, `int32`, `int64`, `uint`, `float32`, `float64`, `complex128` без единой строки явного каста!
""",
        "step_by_step": """
1. Объявляем `const UntypedVal = 50` и `const TypedVal int32 = 50`.
2. Демонстрируем присвоение в переменные `int8`, `uint64`, `float64`.
3. Анализируем разницу.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

const UntypedVal = 50       // Нетипизированная
const TypedVal int32 = 50   // Типизированная (int32)

func main() {
	// UntypedVal свободно присваивается в любые совместимые типы:
	var vInt8 int8 = UntypedVal
	var vUint64 uint64 = UntypedVal
	var vFloat float64 = UntypedVal
	var vComplex complex128 = UntypedVal

	fmt.Printf("vInt8:    %d (%T)\\n", vInt8, vInt8)
	fmt.Printf("vUint64:  %d (%T)\\n", vUint64, vUint64)
	fmt.Printf("vFloat:   %.1f (%T)\\n", vFloat, vFloat)
	fmt.Printf("vComplex: %v (%T)\\n\\n", vComplex, vComplex)

	// TypedVal жестко требует совпадения типа:
	var target32 int32 = TypedVal
	// var target64 int64 = TypedVal // ОШИБКА: cannot use TypedVal (type int32) as type int64

	fmt.Printf("target32: %d (%T)\\n", target32, target32)
}""",
                "note": "Финальное сравнение typed и untyped констант"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# vInt8:    50 (int8)
# vUint64:  50 (uint64)
# vFloat:   50.0 (float64)
# vComplex: (50+0i) (complex128)
# 
# target32: 50 (int32)""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Нетипизированные константы дают языку Go ту же гибкость и лаконичность, что и динамические языки, сохраняя при этом 100% строгую статическую безопасность типов во время компиляции.
""",
        "pitfalls": """
- Ограничение: нетипизированное число не может быть присвоено типу, если его значение выходит за границы этого типа (например `const Huge = 300; var b int8 = Huge` вызовет ошибку `300 overflows int8`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go нетипизированные константы называют \"секретным оружием системы типов\"?»
**Ответ:** Потому что они избавляют разработчика от тысяч громоздких явных кастов `float64(2) * r` или `time.Duration(10) * time.Second`, сохраняя исходный код чистым, лаконичным и абсолютно типобезопасным.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 6: {len(exercises)} exercises.")
