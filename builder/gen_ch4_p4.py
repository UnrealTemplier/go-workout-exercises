# Chapter 4 Part 4: Exercises 61 to 80

exercises = [
    {
        "num": 61,
        "title": "Сравнение байтовой длины строк Hello и Привет",
        "task": "Строки и байты: Измерь длину строки \"Hello\" и \"Привет\" с помощью встроенной функции len(). Изучи, почему результат для \"Привет\" больше 6.",
        "theory": """
Длина в байтах:
- `"Hello"` состоит из 5 ASCII символов по 1 байту $\rightarrow$ `len("Hello") == 5`;
- `"Привет"` состоит из 6 кириллических символов, каждый из которых занимает 2 байта в UTF-8 $\rightarrow$ `len("Привет") == 12`.
""",
        "step_by_step": """
1. Замеряем `len("Hello")` и `len("Привет")`.
2. Подсчитываем реальное количество рун через `utf8.RuneCountInString`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"unicode/utf8"
)

func main() {
	en := "Hello"
	ru := "Привет"

	fmt.Printf("Строка: %-8s | len() (байты): %2d | Руны: %d\\n", en, len(en), utf8.RuneCountInString(en))
	fmt.Printf("Строка: %-8s | len() (байты): %2d | Руны: %d\\n", ru, len(ru), utf8.RuneCountInString(ru))
}""",
                "note": "Сравнение ASCII и UTF-8 длины"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Строка: Hello    | len() (байты):  5 | Руны: 5
# Строка: Привет   | len() (байты): 12 | Руны: 6""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Встроенная функция `len()` генерирует чтение поля `Len` из заголовка строки за 1 инструкцию процессора без подсчета символов.
""",
        "pitfalls": """
- Выделение среза под срез строк по байтовой длине.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова алгоритмическая сложность функции `len(s)` и `utf8.RuneCountInString(s)`?»
**Ответ:** `len(s)` работает за $O(1)$ (чтение готового числа из памяти). `utf8.RuneCountInString(s)` работает за $O(N)$ (линейное сканирование всех байт строки).
"""
    },
    {
        "num": 62,
        "title": "Выделение памяти через new() и сравнение с nil-указателем",
        "task": "Создай переменную-указатель через new(): p := new(int). Измени значение через указатель. Сравни с var p *int (что внутри p?).",
        "theory": """
**Встроенная функция `new(T)`:**
1. Выделяет память под значение типа `T`;
2. Инициализирует её нулевым значением (`0`);
3. Возвращает валидный указатель `*T` на эту память;
4. В отличие от `var p *int` (который равен `nil`), указатель после `new(int)` никогда не равен `nil`.
""",
        "step_by_step": """
1. Создаем `p1 := new(int)` и `var p2 *int`.
2. Меняем `*p1 = 42`.
3. Сравниваем их адреса и безопасность разыменования.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	// 1. Инициализация через new(int)
	p1 := new(int)
	fmt.Printf("p1: адрес = %v, значение = %d, nil? %t\\n", p1, *p1, p1 == nil)

	*p1 = 42
	fmt.Printf("p1 после изменения: значение = %d\\n\\n", *p1)

	// 2. Объявление через var
	var p2 *int
	fmt.Printf("p2: адрес = %v, nil? %t\\n", p2, p2 == nil)
	// *p2 = 100 // ВЫЗОВЕТ ПАНИКУ: nil pointer dereference!
}""",
                "note": "new(T) vs nil-указатель"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# p1: адрес = 0xc0000180a8, значение = 0, nil? false
# p1 после изменения: значение = 42
# 
# p2: адрес = <nil>, nil? true""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
`new(int)` в рантайме вызывает `runtime.newobject`. Если переменная не убегает из функции, память аллоцируется на стеке.
""",
        "pitfalls": """
- Вызов `new(map[string]int)`: вернет указатель на неинициализированную `nil`-мапу `*map`, в которую по-прежнему нельзя писать. Для мап, срезов и каналов всегда используют `make()`, а не `new()`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем разница между `new()` и `make()` в Go?»
**Ответ:** `new(T)` только выделяет память, обнуляет её и возвращает указатель `*T`. `make(T, ...)` инициализирует внутренние структуры ссылочных типов (слайсы, мапы, каналы) и возвращает само готовое к использованию значение `T`, а не указатель.
"""
    },
    {
        "num": 63,
        "title": "Ловушка конвертации string(int) и правильный strconv.Itoa",
        "task": "Преобразуй int в string. Обрати внимание, что получится (число превратится в Unicode символ). Используй strconv.Itoa для правильного преобразования.",
        "theory": """
**Ловушка `string(int)`:**
- `string(65)` в Go исторически возвращает символ `'A'` (Unicode код 65), а не `"65"`;
- Для получения строки из цифр всегда используют `strconv.Itoa(n)`.
""",
        "step_by_step": """
1. Демонстрируем `string(65)`.
2. Демонстрируем `strconv.Itoa(65)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"strconv"
)

func main() {
	code := 65

	// 1. Преобразование кода символа:
	asChar := string(rune(code))

	// 2. Преобразование числа в строку цифр:
	asString := strconv.Itoa(code)

	fmt.Printf("string(rune(%d)) -> %q (символ Unicode)\\n", code, asChar)
	fmt.Printf("strconv.Itoa(%d)  -> %q (числовая строка)\\n", code, asString)
}""",
                "note": "Сравнение string(rune) и strconv.Itoa"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# string(rune(65)) -> "A" (символ Unicode)
# strconv.Itoa(65)  -> "65" (числовая строка)""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
`string(rune)` вызывает `runtime.intstring`, а `strconv.Itoa` форматирует цифры по основанию 10.
""",
        "pitfalls": """
- Написание `string(100500)` в надежде получить строку `"100500"`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в современных версиях Go компилятор выдает предупреждение на `string(x)` для `int`?»
**Ответ:** Потому что это вызывало частые логические ошибки у новичков. В Go 1.15+ добавлено предупреждение `conversion from int to string yields a string of one rune, not a string of digits`.
"""
    },
    {
        "num": 64,
        "title": "Универсальное применение нетипизированной константы к разным типам",
        "task": "Нетипизированные константы в действии: Создайте нетипизированную константу const X = 5. Объявите переменные типов int, float64, complex128. Попробуйте умножить каждую из переменных на X без явного приведения типов.",
        "theory": """
Нетипизированная константа `const X = 5` принимает тип того выражения, в котором она участвует.
""",
        "step_by_step": """
1. Объявляем `const X = 5`.
2. Умножаем на `int`, `float64`, `complex128`.
3. Анализируем типы результатов.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

const X = 5 // Нетипизированная

func main() {
	var i int = 10
	var f float64 = 2.5
	var c complex128 = 1 + 2i

	resI := i * X
	resF := f * X
	resC := c * X

	fmt.Printf("resI: %v (%T)\\n", resI, resI)
	fmt.Printf("resF: %v (%T)\\n", resF, resF)
	fmt.Printf("resC: %v (%T)\\n", resC, resC)
}""",
                "note": "Умножение разных типов на константу"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# resI: 50 (int)
# resF: 12.5 (float64)
# resC: (5+10i) (complex128)""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Семантический анализатор компилятора подставляет значение 5 в AST-узел умножения соответствующего типа.
""",
        "pitfalls": """
- Попытка использовать `X` с типом `string`: `var s string = "hi"; s * X` вызовет ошибку компиляции, так как умножение строк в Go не поддерживается.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как повторить строку N раз в Go?»
**Ответ:** Через функцию `strings.Repeat("Go", 3)` -> `"GoGoGo"`.
"""
    },
    {
        "num": 65,
        "title": "Арифметика комплексных чисел и вычисление модуля (math/cmplx)",
        "task": "Работа с complex64/complex128: создай два комплексных числа, сложи, умножь, найди модуль (cmplx.Abs). Выведи действительную и мнимую части.",
        "theory": """
Комплексные числа:
- Модуль $|z| = \sqrt{\text{Re}^2 + \text{Im}^2}$;
- Умножение: $(a + bi)(c + di) = (ac - bd) + (ad + bc)i$.
""",
        "step_by_step": """
1. Создаем `a := 3.0 + 4.0i` и `b := 1.0 - 1.0i`.
2. Вычисляем сумму, произведение и модуль.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"math/cmplx"
)

func main() {
	a := 3.0 + 4.0i
	b := 1.0 - 1.0i

	sum := a + b
	prod := a * b
	absA := cmplx.Abs(a)

	fmt.Printf("a = %v, b = %v\\n", a, b)
	fmt.Printf("Сумма:        %v\\n", sum)
	fmt.Printf("Произведение: %v\\n", prod)
	fmt.Printf("Модуль |a|:   %.2f\\n", absA)
	fmt.Printf("Re(a) = %.1f, Im(a) = %.1f\\n", real(a), imag(a))
}""",
                "note": "Комплексная арифметика"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# a = (3+4i), b = (1-1i)
# Сумма:        (4+3i)
# Произведение: (7+1i)
# Модуль |a|:   5.00
# Re(a) = 3.0, Im(a) = 4.0""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
`cmplx.Abs` использует алгоритм `math.Hypot` для предотвращения переполнения при промежуточном возведении в квадрат.
""",
        "pitfalls": """
- Смешивание `complex64` и `complex128` без явного каста.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `cmplx.Abs(z)` использует `math.Hypot`, а не `math.Sqrt(r*r + i*i)`?»
**Ответ:** Потому что если `r` или `i` очень велики (например, $10^{200}$), прямое возведение `r*r` переполнит `float64` в $+\infty$, тогда как алгоритм `Hypot` масштабирует числа и вычисляет модуль без переполнения.
"""
    },
    {
        "num": 66,
        "title": "Подсчет символов Unicode через utf8.RuneCountInString",
        "task": "Руны: Используй utf8.RuneCountInString для получения реального количества символов в строке \"Привет\".",
        "theory": """
Функция `utf8.RuneCountInString(s)`:
- Возвращает точное число кодовых точек Unicode;
- Для строки `"Привет"` вернет 6;
- Работает без выделения памяти.
""",
        "step_by_step": """
1. Создаем строку `"Привет"`.
2. Сравниваем `len(s)` и `utf8.RuneCountInString(s)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"unicode/utf8"
)

func main() {
	msg := "Привет"

	fmt.Printf("Текст:                  %s\\n", msg)
	fmt.Printf("Байт (len):             %d\\n", len(msg))
	fmt.Printf("Символов (RuneCount):   %d\\n", utf8.RuneCountInString(msg))
}""",
                "note": "Подсчет рун в строке"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Текст:                  Привет
# Байт (len):             12
# Символов (RuneCount):   6""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Сканер обходит байты, считывая длину каждого символа по маске старших бит.
""",
        "pitfalls": """
- Использование `len(msg)` для проверки максимальной длины текста сообщения в чате.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Может ли один визуальный символ (Grapheme Cluster) состоять из нескольких рун?»
**Ответ:** ДА! Например, составные эмодзи (семейные эмодзи с соединителем `ZWJ` или флаги стран) состоят из 2–4 рун. Для подсчета визуальных глифов используют библиотеку `rivo/uniseg`.
"""
    },
    {
        "num": 67,
        "title": "Полноценный Enum дней недели с iota (Sunday=0 .. Saturday=6)",
        "task": "Простой iota-enum: С помощью генератора констант iota создайте перечисление дней недели (от Sunday до Saturday), где каждому дню соответствует число от 0 до 6.",
        "theory": """
Канонический Enum дней недели в стандартной библиотеке `time`:
```go
const (
    Sunday Weekday = iota
    Monday
    Tuesday
    Wednesday
    Thursday
    Friday
    Saturday
)
```
""",
        "step_by_step": """
1. Создаем тип `Weekday int`.
2. Объявляем константы от `Sunday` до `Saturday`.
3. Печатаем все дни.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type Weekday int

const (
	Sunday Weekday = iota
	Monday
	Tuesday
	Wednesday
	Thursday
	Friday
	Saturday
)

func main() {
	days := []Weekday{Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday}
	names := []string{"Воскресенье", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"}

	for i, d := range days {
		fmt.Printf("День %d: %-12s (константа = %d)\\n", i, names[d], d)
	}
}""",
                "note": "Enum дней недели"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# День 0: Воскресенье  (константа = 0)
# День 1: Понедельник  (константа = 1)
# День 2: Вторник      (константа = 2)
# День 3: Среда        (константа = 3)
# День 4: Четверг      (константа = 4)
# День 5: Пятница      (константа = 5)
# День 6: Суббота      (константа = 6)""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Все значения встраиваются компилятором как целочисленные литералы 0..6.
""",
        "pitfalls": """
- В американском календаре неделя начинается с воскресенья (0 = Sunday), а в европейском — с понедельника.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как сделать так, чтобы при маршалинге в JSON enum `Weekday` выводился как строка `"Monday"`, а не число `1`?»
**Ответ:** Реализовать интерфейсы `json.Marshaler` (`MarshalJSON() ([]byte, error)`) и `json.Unmarshaler`.
"""
    },
    {
        "num": 68,
        "title": "Сравнение точности float32 vs float64 и проблема 0.1 + 0.2 != 0.3",
        "task": "Напиши программу, которая демонстрирует разницу между float32 и float64 в точности: сложи 0.1 + 0.2, сравни результаты. Покажи проблему точности с плавающей точкой.",
        "theory": """
**Стандарт IEEE 754:**
Двоичная система не может точно представить десятичные дроби $0.1$ и $0.2$:
- `float32` имеет 24 бита мантиссы ($\approx 7$ значащих десятичных цифр);
- `float64` имеет 53 бита мантиссы ($\approx 15-17$ значащих цифр);
- `0.1 + 0.2 == 0.30000000000000004` (поэтому прямое `0.1 + 0.2 == 0.3` возвращает `false`).
""",
        "step_by_step": """
1. Складываем `0.1 + 0.2` в `float32` и `float64`.
2. Сравниваем с `0.3`.
3. Пишем безопасное сравнение через эпсилон $\varepsilon$.
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

func main() {
	var a32, b32 float32 = 0.1, 0.2
	sum32 := a32 + b32

	var a64, b64 float64 = 0.1, 0.2
	sum64 := a64 + b64

	fmt.Printf("float32: 0.1 + 0.2 = %.10f (равно 0.3? %t)\\n", sum32, sum32 == 0.3)
	fmt.Printf("float64: 0.1 + 0.2 = %.20f (равно 0.3? %t)\\n", sum64, sum64 == 0.3)

	// Безопасное сравнение с погрешностью epsilon
	const eps = 1e-9
	isEqual := math.Abs(sum64-0.3) < eps
	fmt.Printf("Безопасное сравнение (|sum - 0.3| < 1e-9): %t\\n", isEqual)
}""",
                "note": "Проблема точности IEEE 754"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# float32: 0.1 + 0.2 = 0.3000000119 (равно 0.3? false)
# float64: 0.1 + 0.2 = 0.30000000000000004441 (равно 0.3? false)
# Безопасное сравнение (|sum - 0.3| < 1e-9): true""",
                "note": "Результат анализа точности"
            }
        ],
        "under_the_hood": """
Число 0.1 в двоичной записи представляет собой бесконечную периодическую дробь $0.0001100110011..._2$, которая обрезается разрядной сеткой мантиссы.
""",
        "pitfalls": """
- Использование оператора `==` для сравнения вещественных чисел в юнит-тестах. Всегда используйте `math.Abs(a - b) < eps` или `testify/assert.InDelta`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какой тип данных используют в финтехе для хранения баланса кошелька?»
**Ответ:** Целое число `int64` (хранение в копейках/центах/сатоши) или сторонний пакет `shopspring/decimal` (фиксированная точка).
"""
    },
    {
        "num": 69,
        "title": "Анализ ошибки компилятора при попытке модификации константы Pi",
        "task": "Объяви константу Pi = 3.14. Попробуй изменить её значение (поймай ошибку).",
        "theory": """
Константы защищены от любых модификаций на уровне грамматики языка.
""",
        "step_by_step": """
1. Объявляем `const Pi = 3.14`.
2. Показываем сообщение об ошибке сборки.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

const Pi = 3.14

func main() {
	fmt.Println("Pi =", Pi)
	// Pi = 3.1415 // ОШИБКА: cannot assign to Pi
}""",
                "note": "Попытка изменения константы"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# go run main.go
# ./main.go:9:2: cannot assign to Pi (neither addressable nor a map index expression)""",
                "note": "Ошибка компилятора"
            }
        ],
        "under_the_hood": """
Узел AST `Pi` является `ast.Ident` с объектом `ast.Con`.
""",
        "pitfalls": """
- Попытка создать динамическую константу во время выполнения.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли объявить константу внутри функции?»
**Ответ:** ДА! Константы могут быть объявлены как на уровне пакета, так и локально внутри любой функции или блока.
"""
    },
    {
        "num": 70,
        "title": "Сложение нетипизированной константы с переменной float64",
        "task": "Базовые константы: Объяви типизированную (const a int = 5) и нетипизированную (const b = 5) константы. Попробуй сложить b с float64.",
        "theory": """
Сравнение поведения:
- `const a int = 5` $\rightarrow$ сложение `a + floatVal` вызовет ошибку;
- `const b = 5` $\rightarrow$ сложение `b + floatVal` успешно скомпилируется.
""",
        "step_by_step": """
1. Создаем типизированную `a` и нетипизированную `b`.
2. Складываем с `var val float64 = 10.5`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

const a int = 5 // Типизированная
const b = 5     // Нетипизированная

func main() {
	var val float64 = 10.5

	// 1. Успешное сложение нетипизированной константы:
	sumB := b + val

	// 2. Типизированная константа требует явного каста:
	sumA := float64(a) + val

	fmt.Printf("sumB (b + val): %.1f\\n", sumB)
	fmt.Printf("sumA (float64(a) + val): %.1f\\n", sumA)
}""",
                "note": "Сложение констант с float64"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# sumB (b + val): 15.5
# sumA (float64(a) + val): 15.5""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
При `b + val` нетипизированная константа `b` неявно типизируется в `float64(5.0)`.
""",
        "pitfalls": """
- Излишняя типизация констант без необходимости.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какой тип получит переменная `x := b`, если `b` — нетипизированная константа `const b = 5`?»
**Ответ:** Тип по умолчанию (Default Type), то есть `int`.
"""
    },
    {
        "num": 71,
        "title": "Константы экстремальных значений пакета math (MaxInt, MaxFloat64)",
        "task": "Используй math.MaxInt, math.MaxUint, math.MaxFloat64 и другие константы из пакета math. Напиши функцию, которая возвращает максимальное значение для переданного типа (используй switch type или рефлексию).",
        "theory": """
Пакет `math` содержит стандартные пределы всех числовых типов:
- `math.MaxInt8`, `math.MaxInt16`, `math.MaxInt32`, `math.MaxInt64`, `math.MaxInt`;
- `math.MaxUint8`, `math.MaxUint16`, `math.MaxUint32`, `math.MaxUint64`;
- `math.MaxFloat32`, `math.MaxFloat64`.
""",
        "step_by_step": """
1. Пишем функцию `GetMaxBound(sample any) any`.
2. Используем `switch sample.(type)`.
3. Тестируем для `int8`, `uint16`, `float64`.
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

func GetMaxBound(sample any) string {
	switch sample.(type) {
	case int8:
		return fmt.Sprintf("int8: %d", math.MaxInt8)
	case uint8:
		return fmt.Sprintf("uint8: %d", math.MaxUint8)
	case int16:
		return fmt.Sprintf("int16: %d", math.MaxInt16)
	case uint16:
		return fmt.Sprintf("uint16: %d", math.MaxUint16)
	case int32:
		return fmt.Sprintf("int32: %d", math.MaxInt32)
	case int64:
		return fmt.Sprintf("int64: %d", math.MaxInt64)
	case float64:
		return fmt.Sprintf("float64: %e", math.MaxFloat64)
	default:
		return "Неизвестный тип"
	}
}

func main() {
	fmt.Println(GetMaxBound(int8(0)))
	fmt.Println(GetMaxBound(uint16(0)))
	fmt.Println(GetMaxBound(int64(0)))
	fmt.Println(GetMaxBound(float64(0)))
}""",
                "note": "Диспетчеризация пределов через Type Switch"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# int8: 127
# uint16: 65535
# int64: 9223372036854775807
# float64: 1.797693e+308""",
                "note": "Лимиты типов"
            }
        ],
        "under_the_hood": """
Type Switch сопоставляет указатель `_type` интерфейса `any` со статическими дескрипторами типов.
""",
        "pitfalls": """
- В Go нет `math.MinUint`: минимальное значение любого беззнакового типа всегда гарантированно равно 0.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Чему равен `math.MinInt` на 64-битной платформе?»
**Ответ:** `-9223372036854775808` ($-2^{63}$).
"""
    },
    {
        "num": 72,
        "title": "Генерация единиц измерения информации (KB, MB, GB, TB) через iota и <<",
        "task": "Битовые сдвиги с iota: Используя iota и оператор битового сдвига <<, создайте константы для размеров информации: KB, MB, GB, TB (1024, 1024^2, ...).",
        "theory": """
**Паттерн генерации степеней двойки:**
$$1 \ll (10 \cdot \text{iota})$$
- `iota = 1` $\rightarrow 1 \ll 10 = 1024$ (KB);
- `iota = 2` $\rightarrow 1 \ll 20 = 1\,048\,576$ (MB);
- `iota = 3` $\rightarrow 1 \ll 30 = 1\,073\,741\,824$ (GB);
- `iota = 4` $\rightarrow 1 \ll 40 = 1\,099\,511\,627\,776$ (TB).
""",
        "step_by_step": """
1. Создаем константный блок с пропуском нуля `_ = iota`.
2. Объявляем `KB, MB, GB, TB, PB`.
3. Печатаем таблицу объемов.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

const (
	_           = iota             // iota = 0 (пропускаем)
	KB uint64 = 1 << (10 * iota) // 1 << 10 = 1024 байт
	MB                           // 1 << 20 = 1048576 байт
	GB                           // 1 << 30 = 1073741824 байт
	TB                           // 1 << 40 = 1099511627776 байт
	PB                           // 1 << 50
)

func main() {
	fmt.Printf("1 KB = %15d байт\\n", KB)
	fmt.Printf("1 MB = %15d байт\\n", MB)
	fmt.Printf("1 GB = %15d байт\\n", GB)
	fmt.Printf("1 TB = %15d байт\\n", TB)
	fmt.Printf("1 PB = %15d байт\\n", PB)
}""",
                "note": "Размеры данных через iota и сдвиг"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1 KB =            1024 байт
# 1 MB =         1048576 байт
# 1 GB =      1073741824 байт
# 1 TB =   1099511627776 байт
# 1 PB = 1125899906842624 байт""",
                "note": "Результат вычислений"
            }
        ],
        "under_the_hood": """
Все сдвиги вычисляются на этапе компиляции, в бинарник попадают готовые 64-битные константы.
""",
        "pitfalls": """
- Попытка вычислить `1 << (10 * 7)` (ZB, $2^{70}$) в типизированный `uint64`: число превысит 64 бита.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как написать функцию красивого форматирования байт `FormatBytes(bytes int64) string` (например, 1048576 -> \"1.00 MB\")?»
**Ответ:** Разделить исходное число на константы `GB`, `MB`, `KB` в порядке убывания и отформатировать через `fmt.Sprintf("%.2f %s", val, unit)`.
"""
    },
    {
        "num": 73,
        "title": "Групповое объявление констант в скобках const ( ... )",
        "task": "Объяви группу констант в скобках const ( ... ).",
        "theory": """
Групповое объявление `const (...)` для конфигурационных параметров микросервиса.
""",
        "step_by_step": """
1. Создаем блок констант таймаутов и лимитов.
2. Выводим конфигурацию.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"time"
)

const (
	ReadTimeout  = 5 * time.Second
	WriteTimeout = 10 * time.Second
	MaxHeader    = 1 << 20 // 1 MB
	DefaultPort  = ":8080"
)

func main() {
	fmt.Println("=== СЕТЕВЫЕ НАСТРОЙКИ СЕРВЕРА ===")
	fmt.Printf("ReadTimeout:  %v\\n", ReadTimeout)
	fmt.Printf("WriteTimeout: %v\\n", WriteTimeout)
	fmt.Printf("MaxHeader:    %d байт\\n", MaxHeader)
	fmt.Printf("DefaultPort:  %s\\n", DefaultPort)
}""",
                "note": "Группа сетевых констант"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# === СЕТЕВЫЕ НАСТРОЙКИ СЕРВЕРА ===
# ReadTimeout:  5s
# WriteTimeout: 10s
# MaxHeader:    1048576 байт
# DefaultPort:  :8080""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Выражение `5 * time.Second` также вычисляется на этапе компиляции.
""",
        "pitfalls": """
- Использование переменных вместо констант для неизменяемых таймаутов.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `time.Duration` в Go является целым числом `int64` наносекунд?»
**Ответ:** Это обеспечивает абсолютную точность операций сложения и сравнения без проблем потери точности чисел с плавающей точкой.
"""
    },
    {
        "num": 74,
        "title": "Блок фундаментальных математических констант",
        "task": "Блоки констант: Сгруппируй 3 математические константы в блок const ( ... ).",
        "theory": """
Группировка математических констант в одном блоке.
""",
        "step_by_step": """
1. Создаем блок с `Pi`, `E`, `Ln2`.
2. Выводим значения.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

const (
	Pi  = 3.141592653589793
	E   = 2.718281828459045
	Ln2 = 0.693147180559945
)

func main() {
	fmt.Printf("Pi  = %.6f\\n", Pi)
	fmt.Printf("E   = %.6f\\n", E)
	fmt.Printf("Ln2 = %.6f\\n", Ln2)
}""",
                "note": "Математический блок констант"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Pi  = 3.141593
# E   = 2.718282
# Ln2 = 0.693147""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Константы подставляются прямо в регистры FPU / AVX.
""",
        "pitfalls": """
- Забыть экспортировать константу с заглавной буквы, если она нужна в других пакетах.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каковы правила экспорта констант в Go?»
**Ответ:** Имя константы, начинающееся с заглавной буквы (`Pi`), экспортируется наружу пакета. Имя со строчной буквы (`pi`) доступно только внутри текущего пакета.
"""
    },
    {
        "num": 75,
        "title": "Температурные типы Celsius и Fahrenheit и функции двусторонней конвертации",
        "task": "Создай псевдоним типа: type Celsius float64, type Fahrenheit float64. Напиши функции конвертации. Попробуй сложить Celsius и Fahrenheit — что произойдёт? Объясни, почему Go не позволяет (или позволяет?) это сделать.",
        "theory": """
**Строгая типизация защищает от физических катастроф:**
1. `type Celsius float64` и `type Fahrenheit float64` — это два изолированных типа;
2. Попытка сложить `c + f` вызывает ошибку компилятора `mismatched types Celsius and Fahrenheit`;
3. Сложение физически разнородных величин без явной конвертации запрещено на уровне языка!
""",
        "step_by_step": """
1. Объявляем типы `Celsius` и `Fahrenheit`.
2. Пишем функции `CToF(c Celsius) Fahrenheit` и `FToC(f Fahrenheit) Celsius`.
3. Демонстрируем ошибку и правильный расчет.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type Celsius float64
type Fahrenheit float64

func CToF(c Celsius) Fahrenheit {
	return Fahrenheit(c*9/5 + 32)
}

func FToC(f Fahrenheit) Celsius {
	return Celsius((f - 32) * 5 / 9)
}

func main() {
	var c Celsius = 100
	var f Fahrenheit = 212

	// Ошибка компиляции: invalid := c + f // mismatched types Celsius and Fahrenheit

	// Корректное сложение после конвертации:
	sumCelsius := c + FToC(f)

	fmt.Printf("100 °C в Фаренгейтах: %.1f °F\\n", CToF(c))
	fmt.Printf("212 °F в Цельсиях:    %.1f °C\\n", FToC(f))
	fmt.Printf("Сумма (в Цельсиях):   %.1f °C\\n", sumCelsius)
}""",
                "note": "Безопасная работа с физическими величинами"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 100 °C в Фаренгейтах: 212.0 °F
# 212 °F в Цельсиях:    100.0 °C
# Сумма (в Цельсиях):   200.0 °C""",
                "note": "Результат конвертации"
            }
        ],
        "under_the_hood": """
Типы имеют разные дескрипторы `_type`, предотвращая ошибочные присваивания.
""",
        "pitfalls": """
- Вспомните катастрофу зонда NASA Mars Climate Orbiter в 1999 году: из-за несоответствия единиц измерения (фунты-силы против ньютонов) зонд стоимостью $327 млн сгорел в атмосфере Марса. Строгая типизация Go предотвращает подобные баги.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как привязать метод `String() string` к типу `Celsius`, чтобы он автоматически печатался со значком `°C`?»
**Ответ:** `func (c Celsius) String() string { return fmt.Sprintf("%.1f°C", c) }`.
"""
    },
    {
        "num": 76,
        "title": "Сравнительный анализ знакового (int8) и беззнакового (uint8) переполнения",
        "task": "Напиши программу, которая демонстрирует переполнение uint8: прибавь 1 к 255. Что произойдёт? Сделай то же с int8 (127 + 1). Объясни результат.",
        "theory": """
Сравнение механики переполнения:
- `uint8(255) + 1` $\rightarrow$ `0` (сброс беззнакового регистра);
- `int8(127) + 1` $\rightarrow$ `-128` (бит 7 становится знаковым битом `1`, что в дополнительном коде означает минимальное отрицательное число).
""",
        "step_by_step": """
1. Инкрементируем `uint8(255)`.
2. Инкрементируем `int8(127)`.
3. Анализируем битовое представление.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	var u uint8 = 255
	var s int8 = 127

	uNext := u + 1
	sNext := s + 1

	fmt.Printf("uint8: %d + 1 = %d (двоичный: %08b -> %08b)\\n", u, uNext, u, uNext)
	fmt.Printf("int8:  %d + 1 = %d (двоичный: %08b -> %08b)\\n", s, sNext, uint8(s), uint8(sNext))
}""",
                "note": "Сравнение знакового и беззнакового переполнения"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# uint8: 255 + 1 = 0 (двоичный: 11111111 -> 00000000)
# int8:  127 + 1 = -128 (двоичный: 01111111 -> 10000000)""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
В дополнительном коде (Two's Complement) старший бит `10000000` интерпретируется процессором со знаком минус: $-128$.
""",
        "pitfalls": """
- Использование знаковых типов для счетчиков байт в сетевых пакетах.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в дополнительном коде диапазон отрицательных чисел на 1 больше, чем положительных (от -128 до 127)?»
**Ответ:** Потому что число `0` кодируется комбинацией `00000000` и входит в положительную половину диапазона.
"""
    },
    {
        "num": 77,
        "title": "Пропуск значений 0 и 1 в iota через множественный blank identifier",
        "task": "Пропуск значений в iota: Создайте перечисление, в котором значения 0 и 1 пропускаются с помощью пустого идентификатора _, а константы начинаются со значения 2.",
        "theory": """
Для пропуска нескольких значений `iota`:
- `_ = iota` (0)
- `_` (1)
- `ItemA` (2)
- `ItemB` (3)
""",
        "step_by_step": """
1. Создаем блок констант с пропуском 0 и 1.
2. Проверяем, что константы начинаются с 2.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type Priority int

const (
	_            Priority = iota // 0 (пропущен)
	_                            // 1 (пропущен)
	PriorityLow                  // 2
	PriorityMedium               // 3
	PriorityHigh                 // 4
)

func main() {
	fmt.Printf("PriorityLow:    %d\\n", PriorityLow)
	fmt.Printf("PriorityMedium: %d\\n", PriorityMedium)
	fmt.Printf("PriorityHigh:   %d\\n", PriorityHigh)
}""",
                "note": "Пропуск нескольких значений в iota"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# PriorityLow:    2
# PriorityMedium: 3
# PriorityHigh:   4""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Каждая строка блока увеличивает внутренний счетчик `iota` на 1.
""",
        "pitfalls": """
- Забыть, что пропуск `_` всё равно расходует индекс `iota`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как начать нумерацию `iota` сразу с 100?»
**Ответ:** `const ( First = iota + 100; Second; ... )`.
"""
    },
    {
        "num": 78,
        "title": "Определенный тип type UserID int и защита от семантических ошибок",
        "task": "Создай определённый тип type UserID int. Напиши функцию NewUserID(id int) UserID. Попробуй передать UserID туда, где ожидается int — получи ошибку. Объясни концепцию определённых типов.",
        "theory": """
**Концепция Defined Types:**
- Защищает от передачи случайного сырого `int` в методы, требующие валидированный `UserID`;
- Компилятор строго проверяет типы на этапе сборки.
""",
        "step_by_step": """
1. Объявляем `type UserID int`.
2. Создаем конструктор `NewUserID(id int) (UserID, error)`.
3. Показываем ошибку при попытке передать `UserID` в функцию `ProcessInt(v int)`.
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

type UserID int

func NewUserID(id int) (UserID, error) {
	if id <= 0 {
		return 0, errors.New("недопустимый ID пользователя")
	}
	return UserID(id), nil
}

func ProcessRawInt(val int) {
	fmt.Println("Обработка сырого int:", val)
}

func main() {
	uid, err := NewUserID(1050)
	if err != nil {
		return
	}

	fmt.Printf("Создан UserID: %d (тип: %T)\\n", uid, uid)

	// Ошибка компиляции: ProcessRawInt(uid) // cannot use uid (type UserID) as type int in argument

	// Явный каст:
	ProcessRawInt(int(uid))
}""",
                "note": "Защита через определенный тип UserID"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Создан UserID: 1050 (тип: main.UserID)
# Обработка сырого int: 1050""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Типы `UserID` и `int` не идентичны, несмотря на одинаковый Underlying Type `int`.
""",
        "pitfalls": """
- Случайное снятие типизации `int(uid)` без необходимости.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Наследует ли тип `type MySlice []int` методы типа `[]int`?»
**Ответ:** У базовых типов нет методов. Но если создать `type MyType OriginalType`, то новый тип **НЕ наследует методы исходного типа**. Все методы требуется объявлять заново или использовать встраивание (Embedding).
"""
    },
    {
        "num": 79,
        "title": "Битовые флаги прав доступа (Bitmask) через iota и сдвиг 1 << iota",
        "task": "Используй iota для создания битовых флагов (например, Read = 1 << iota, Write, Execute).",
        "theory": """
**Битовые маски (Bitmasks):**
- `Read = 1 << 0` ($001_2 = 1$)
- `Write = 1 << 1` ($010_2 = 2$)
- `Execute = 1 << 2` ($100_2 = 4$)
- Комбинирование прав: `Read | Write` ($011_2 = 3$);
- Проверка прав: `(perms & Read) != 0`.
""",
        "step_by_step": """
1. Объявляем `Permission = 1 << iota`.
2. Создаем комбинированные права.
3. Проверяем наличие конкретных прав.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type Permission uint8

const (
	PermRead    Permission = 1 << iota // 1 (0001)
	PermWrite                          // 2 (0010)
	PermExecute                        // 4 (0100)
	PermAdmin                          // 8 (1000)
)

func main() {
	// Комбинируем права: Чтение + Запись
	userPerms := PermRead | PermWrite

	fmt.Printf("userPerms: %04b (%d)\\n", userPerms, userPerms)

	// Проверка наличия прав
	canRead := (userPerms & PermRead) != 0
	canExec := (userPerms & PermExecute) != 0

	fmt.Printf("Право на чтение:     %t\\n", canRead)
	fmt.Printf("Право на исполнение: %t\\n", canExec)
}""",
                "note": "Битовые маски на iota"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# userPerms: 0011 (3)
# Право на чтение:     true
# Право на исполнение: false""",
                "note": "Результат проверки прав"
            }
        ],
        "under_the_hood": """
Операция `userPerms & PermRead` выделяет 0-й бит, результат сравнивается с нулем за 1 машинный такт.
""",
        "pitfalls": """
- Использование оператора `&&` (логическое И) вместо `&` (побитовое И).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как сбросить конкретный флаг (например `PermWrite`) из маски `userPerms`?»
**Ответ:** С помощью оператора AND NOT: `userPerms = userPerms &^ PermWrite`.
"""
    },
    {
        "num": 80,
        "title": "Изучение ошибки компиляции при попытке переопределения константы",
        "task": "Неизменяемость: Попытайся переопределить константу в процессе выполнения программы и изучи ошибку компиляции.",
        "theory": """
Финальное закрепление иммутабельности констант.
""",
        "step_by_step": """
1. Объявляем `const MaxRetries = 3`.
2. Показываем текст ошибки при `MaxRetries = 5`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

const MaxRetries = 3

func main() {
	fmt.Println("MaxRetries:", MaxRetries)
	// MaxRetries = 5 // ОШИБКА: cannot assign to MaxRetries
}""",
                "note": "Неизменяемость констант"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# go run main.go
# ./main.go:9:2: cannot assign to MaxRetries (neither addressable nor a map index expression)""",
                "note": "Ошибка компиляции"
            }
        ],
        "under_the_hood": """
Синтаксический чекер прерывает компиляцию на ранней стадии.
""",
        "pitfalls": """
- Попытка использовать константу как буфер для записи.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Может ли функция в Go возвращать константу?»
**Ответ:** Нет, функции возвращают переменные/значения. Константы вычисляются строго до старта программы.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 4: {len(exercises)} exercises.")
