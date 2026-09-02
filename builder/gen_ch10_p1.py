# Chapter 10 Part 1: Exercises 1 to 25

exercises = [
    {
        "num": 1,
        "title": "Базовая функция без параметров и возвращаемого значения",
        "task": "Напишите функцию без параметров и возврата, печатающую приветствие.",
        "theory": """
**Синтаксис объявления функции в Go:**
- Ключевое слово `func`, имя функции в PascalCase (для экспорта) или camelCase (внутри пакета);
- Пустые круглые скобки `()` указывают на отсутствие принимаемых параметров;
- Отсутствие списка типов после скобок означает, что функция ничего не возвращает (`void` в терминологии C/C++).
""",
        "step_by_step": """
1. Объявляем функцию `PrintGreeting()`.
2. В теле функции вызываем `fmt.Println`.
3. Вызываем функцию из `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func PrintGreeting() {
	fmt.Println("Добро пожаловать в мир высоконагруженной разработки на Go!")
}

func main() {
	PrintGreeting()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Добро пожаловать в мир высоконагруженной разработки на Go!"""
            }
        ],
        "under_the_hood": """
Функция компилируется в ассемблерную инструкцию `TEXT ·PrintGreeting(SB), $0-0`, где `$0-0` означает 0 байт стекового фрейма и 0 байт аргументов.
""",
        "pitfalls": """
- Вызов `return value` в функции без сигнатуры возврата (ошибка компиляции `too many return values`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Чем функции в Go отличаются от методов?»
**Ответ:** Функция объявляется глобально на уровне пакета (`func Foo()`), а метод привязан к конкретному типу-получателю (Receiver: `func (r Receiver) Foo()`).
"""
    },
    {
        "num": 2,
        "title": "Именованные возвращаемые значения (Named Returns) и 'голый' return (Naked Return)",
        "task": "Примените именованные возвращаемые значения: функция, возвращающая площадь и периметр прямоугольника, использует return без аргументов.",
        "theory": """
**Именованные возвращаемые значения (Named Return Values):**
- Переменные объявляются прямо в сигнатуре: `(area, perimeter float64)`;
- Инициализируются zero-значениями (`0.0`) в начале стекового фрейма;
- Оператор `return` без аргументов (Naked Return) автоматически возвращает текущие значения этих переменных.
""",
        "step_by_step": """
1. Объявляем `RectangleProps(w, h float64) (area, perimeter float64)`.
2. Присваиваем `area = w * h` и `perimeter = 2 * (w + h)`.
3. Завершаем выполнение 'голым' `return`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func RectangleProps(width, height float64) (area, perimeter float64) {
	area = width * height
	perimeter = 2 * (width + height)
	return // Naked return: возвращает значения area и perimeter
}

func main() {
	a, p := RectangleProps(10.5, 4.0)
	fmt.Printf("Прямоугольник 10.5 x 4.0:\n")
	fmt.Printf("  Площадь:   %.2f\n", a)
	fmt.Printf("  Периметр:  %.2f\n", p)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Прямоугольник 10.5 x 4.0:
#   Площадь:   42.00
#   Периметр:  29.00"""
            }
        ],
        "under_the_hood": """
Именованные переменные размещаются в области стека для возвращаемых параметров вызывающей функции.
""",
        "pitfalls": """
- Использование Naked Return в длинных функциях (> 15 строк): ухудшает читаемость и провоцирует скрытые баги затенения.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в гайдлайнах Google Go Style Guide рекомендуют избегать Naked Returns в больших функциях?»
**Ответ:** Потому что разработчик, читая конец длинной функции, вынужден скроллить наверх, чтобы понять, какие именно переменные неявно возвращаются.
"""
    },
    {
        "num": 3,
        "title": "Вариативные функции (Variadic Functions) и вычисление среднего арифметического",
        "task": "Создайте вариативную функцию (variadic function), принимающую произвольное количество чисел и возвращающую их среднее арифметическое.",
        "theory": """
**Специфика вариативных параметров `...T`:**
- Синтаксис `...float64` позволяет передавать от 0 до сотен аргументов через запятую;
- Внутри функции параметр `numbers` ведет себя как обычный срез `[]float64`;
- Вариативный параметр может быть **только последним** в списке аргументов.
""",
        "step_by_step": """
1. Пишем `Average(nums ...float64) float64`.
2. Проверяем граничный случай `len(nums) == 0`.
3. Суммируем элементы в цикле и делим на `len(nums)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Average(nums ...float64) float64 {
	if len(nums) == 0 {
		return 0.0
	}
	sum := 0.0
	for _, n := range nums {
		sum += n
	}
	return sum / float64(len(nums))
}

func main() {
	fmt.Printf("Average(10, 20, 30): %.2f\n", Average(10, 20, 30))
	fmt.Printf("Average(5, 15):       %.2f\n", Average(5, 15))
	fmt.Printf("Average():           %.2f\n", Average())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Average(10, 20, 30): 20.00
# Average(5, 15):       10.00
# Average():           0.00"""
            }
        ],
        "under_the_hood": """
Компилятор перед вызовом аллоцирует временный массив и передает срез в функцию.
""",
        "pitfalls": """
- Деление на 0 при вызове без аргументов `Average()`: обязательно проверять `len(nums) == 0`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Сколько вариативных параметров может принимать функция в Go?»
**Ответ:** Строго один, и он обязан стоять на последней позиции в сигнатуре (`func Foo(prefix string, args ...int)`).
"""
    },
    {
        "num": 4,
        "title": "Поиск максимума в вариативной функции max(numbers ...int) и распаковка среза slice...",
        "task": "Сделайте вариативную функцию max(numbers ...int) int, передайте в неё срез через slice....",
        "theory": """
**Распаковка среза (Slice Unpacking `s...`):**
- Для передачи существующего среза `s := []int{1, 2, 3}` в вариативную функцию `Max(nums ...int)` используется суффикс `s...`;
- При этом новый массив не создается: функция получает тот же срез напрямую.
""",
        "step_by_step": """
1. Пишем `FindMax(nums ...int) (int, bool)`.
2. Создаем срез `data := []int{15, 88, 42, 99, 23}`.
3. Вызываем `FindMax(data...)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func FindMax(nums ...int) (int, bool) {
	if len(nums) == 0 {
		return 0, false
	}
	maxVal := nums[0]
	for _, v := range nums[1:] {
		if v > maxVal {
			maxVal = v
		}
	}
	return maxVal, true
}

func main() {
	// 1. Прямая передача аргументов через запятую:
	m1, _ := FindMax(10, 50, 30)
	fmt.Printf("1. Max(10, 50, 30): %d\n", m1)

	// 2. Распаковка среза через data...:
	data := []int{15, 88, 42, 99, 23}
	m2, _ := FindMax(data...)
	fmt.Printf("2. Max(data...):     %d\n", m2)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Max(10, 50, 30): 50
# 2. Max(data...):     99"""
            }
        ],
        "under_the_hood": """
При `data...` компилятор передает оригинальный `SliceHeader` без промежуточных аллокаций.
""",
        "pitfalls": """
- Попытка передать `FindMax(data)` без троеточия (ошибка компиляции `cannot use data (variable of type []int) as int value`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем отличие `append(dst, src...)` от вызова обычной вариативной функции?»
**Ответ:** `append` — это встроенная generic-функция рантайма, работающая со срезами любого типа `[]T`.
"""
    },
    {
        "num": 5,
        "title": "Оператор троеточия (...) для передачи срезов в вариативные функции",
        "task": "Используйте оператор ... для передачи слайса в вариативную функцию.",
        "theory": """
Закрепление синтаксиса `...` для передачи срезов строк и чисел.
""",
        "step_by_step": """
1. Создаем вариативную функцию `PrintTags(prefix string, tags ...string)`.
2. Создаем срез `[]string{"backend", "golang", "highload"}`.
3. Передаем через `tags...`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"strings"
)

func PrintTags(prefix string, tags ...string) {
	fmt.Printf("[%s] %s\n", prefix, strings.Join(tags, " #"))
}

func main() {
	items := []string{"golang", "concurrency", "docker"}
	PrintTags("ТЕГИ", items...)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# [ТЕГИ] golang #concurrency #docker"""
            }
        ],
        "under_the_hood": """
Срезы передаются по значению как 24-байтный дескриптор.
""",
        "pitfalls": """
- Изменение элементов внутри функции: так как `tags` ссылается на тот же базовый массив, модификация `tags[0] = ...` изменит оригинальный срез `items`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Может ли вариативная функция модифицировать переданный через `...` срез?»
**Ответ:** ДА! Элементы базового массива разделяются.
"""
    },
    {
        "num": 6,
        "title": "Разворот Unicode-строки с корректной обработкой рун ReverseString(s string) string",
        "task": "Напишите функцию, которая принимает строку и возвращает её реверс (учитывая Unicode-символы, а не просто байты).",
        "theory": """
**Разворот Unicode строк в Go:**
- Строки в Go хранят байты в кодировке UTF-8;
- Побайтовый разворот ломает многобайтовые символы (кириллица, иероглифы, эмодзи);
- Правильный алгоритм: преобразовать строку в срез рун `[]rune(s)`, развернуть срез методом Two Pointers и сконвертировать обратно в `string`.
""",
        "step_by_step": """
1. Пишем `ReverseString(s string) string`.
2. Преобразуем `runes := []rune(s)`.
3. Разворачиваем `runes[i], runes[j] = runes[j], runes[i]`.
4. Возвращаем `string(runes)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func ReverseString(s string) string {
	runes := []rune(s)
	for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
		runes[i], runes[j] = runes[j], runes[i]
	}
	return string(runes)
}

func main() {
	words := []string{"Hello, World!", "Привет, Мир! 🚀", "日本語"}
	for _, w := range words {
		fmt.Printf("Оригинал: %-20s -> Реверс: %s\n", w, ReverseString(w))
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Оригинал: Hello, World!        -> Реверс: !dlroW ,olleH
# Оригинал: Привет, Мир! 🚀      -> Реверс: 🚀 !риМ ,тевирП
# Оригинал: 日本語                -> Реверс: 語本日"""
            }
        ],
        "under_the_hood": """
Преобразование `[]rune(s)` вызывает `runtime.stringtoslicerune`.
""",
        "pitfalls": """
- Побайтовый разворот `s[len-1-i]`: превратит русские буквы в нечитаемый мусор (Unicode Replacement Character ).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Корректно ли работает `[]rune` для комбинированных эмодзи (Grapheme Clusters, например флаги или цвет кожи)?»
**Ответ:** Для графемных кластеров требуются специализированные библиотеки (например `golang.org/x/exp/utf8string` или `uniseg`), так как комбинированные эмодзи состоят из нескольких рун с соединителем ZWJ (Zero-Width Joiner).
"""
    },
    {
        "num": 7,
        "title": "Функция-замыкание (Closure): инкапсуляция внутреннего счетчика вызовов",
        "task": "Создайте замыкание — функцию, возвращающую счётчик вызовов.",
        "theory": """
**Механика замыканий (Closures) в Go:**
- Замыкание — это функция, которая ссылается на переменные вне своего тела (за пределами своего стека);
- Рантайм Go перемещает захваченную переменную из стека в кучу (**Escape Analysis**);
- Возвращенная функция сохраняет ссылку на эту переменную между вызовами.
""",
        "step_by_step": """
1. Пишем `MakeCounter() func() int`.
2. Локальная переменная `count := 0`.
3. Возвращаем анонимную функцию `func() int { count++; return count }`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func MakeCounter() func() int {
	count := 0
	return func() int {
		count++
		return count
	}
}

func main() {
	c1 := MakeCounter()
	c2 := MakeCounter()

	fmt.Printf("c1: %d\n", c1())
	fmt.Printf("c1: %d\n", c1())
	fmt.Printf("c1: %d\n", c1())

	fmt.Printf("c2 (независимый): %d\n", c2())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# c1: 1
# c1: 2
# c1: 3
# c2 (независимый): 1"""
            }
        ],
        "under_the_hood": """
Компилятор создает анонимную структуру, хранящую указатель на захваченную переменную `&count`.
""",
        "pitfalls": """
- Предположение, что `c1` и `c2` делят один счетчик: каждый вызов `MakeCounter()` создает новый независимый экземпляр в куче.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Куда компилятор аллоцирует переменную `count` в `MakeCounter`?»
**Ответ:** В кучу (Heap), так как escape-анализ определяет, что время жизни переменной превышает время жизни фрейма функции `MakeCounter`.
"""
    },
    {
        "num": 8,
        "title": "Множественный булев возврат CheckAge(age int) (isAdult, isSenior bool)",
        "task": "Создайте функцию, которая принимает возраст и возвращает две булевы переменные: isAdult и isSenior.",
        "theory": """
Идиоматичный множественный возврат логических признаков.
""",
        "step_by_step": """
1. Пишем `CheckAge(age int) (isAdult, isSenior bool)`.
2. Проверяем `age >= 18` и `age >= 65`.
3. Тестируем на разных возрастах.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func CheckAge(age int) (isAdult, isSenior bool) {
	isAdult = age >= 18
	isSenior = age >= 65
	return isAdult, isSenior
}

func main() {
	ages := []int{15, 25, 70}
	for _, a := range ages {
		adult, senior := CheckAge(a)
		fmt.Printf("Возраст %2d: Совершеннолетний = %-5t | Пенсионер = %-5t\n", a, adult, senior)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Возраст 15: Совершеннолетний = false | Пенсионер = false
# Возраст 25: Совершеннолетний = true  | Пенсионер = false
# Возраст 70: Совершеннолетний = true  | Пенсионер = true"""
            }
        ],
        "under_the_hood": """
Булевы значения возвращаются в регистрах процессора `AL` и `BL`.
""",
        "pitfalls": """
- Игнорирование второго аргумента без `_`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каковы преимущества множественного возврата перед возвратом структуры?»
**Ответ:** Нулевые накладные расходы на создание структуры и удобная распаковка `a, b := fn()`.
"""
    },
    {
        "num": 9,
        "title": "Множественный возврат результатов арифметических операций (Sum, Diff, Prod, Quot)",
        "task": "Напишите функцию, которая принимает два числа и возвращает их сумму, разность, произведение и частное (множественный возврат).",
        "theory": """
Возврат кортежа из 4 значений с обработкой деления на ноль.
""",
        "step_by_step": """
1. Пишем `CalcAll(a, b float64) (sum, diff, prod, quot float64, err error)`.
2. Проверяем `b == 0`.
3. Возвращаем 5 параметров.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"errors"
	"fmt"
)

func CalcAll(a, b float64) (sum, diff, prod, quot float64, err error) {
	sum = a + b
	diff = a - b
	prod = a * b
	if b == 0 {
		return sum, diff, prod, 0, errors.New("деление на ноль")
	}
	quot = a / b
	return sum, diff, prod, quot, nil
}

func main() {
	s, d, p, q, err := CalcAll(20, 5)
	if err == nil {
		fmt.Printf("20 и 5: Сумма=%.1f, Разность=%.1f, Произведение=%.1f, Частное=%.1f\n", s, d, p, q)
	}

	_, _, _, _, errZero := CalcAll(20, 0)
	if errZero != nil {
		fmt.Printf("Ошибка при делении на ноль: %v\n", errZero)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 20 и 5: Сумма=25.0, Разность=15.0, Произведение=100.0, Частное=4.0
# Ошибка при делении на ноль: деление на ноль"""
            }
        ],
        "under_the_hood": """
В архитектуре ABIInternal (Go 1.17+) до 9 целочисленных и вещественных аргументов/результатов передаются напрямую через регистры CPU (RAX, RBX, RCX...).
""",
        "pitfalls": """
- Возврат слишком большого количества значений (> 4-5): перегружает вызов. В таких случаях лучше использовать структуру-ответ `struct`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как ABIInternal ускорил множественный возврат функций в Go?»
**Ответ:** За счет устранения обращений к оперативной памяти/стеку и передачи всех возвращаемых значений через регистры процессора.
"""
    },
    {
        "num": 10,
        "title": "Итеративный генератор чисел Фибоначчи через замыкание",
        "task": "Через замыкание реализуйте генератор чисел Фибоначчи (функция возвращает очередное число).",
        "theory": """
**Генератор состояния (Stateful Stream Generator):**
- Замыкание хранит пару текущих чисел `a, b = 0, 1`;
- При каждом вызове возвращает `a` и производит сдвиг `a, b = b, a+b`;
- Работает за $O(1)$ по времени и $O(1)$ памяти без рекурсии.
""",
        "step_by_step": """
1. Пишем `FibGenerator() func() int`.
2. Инициализируем `a, b := 0, 1`.
3. Возвращаем очередное значение.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func FibGenerator() func() int {
	a, b := 0, 1
	return func() int {
		curr := a
		a, b = b, a+b
		return curr
	}
}

func main() {
	nextFib := FibGenerator()

	fmt.Println("Первые 10 чисел Фибоначчи из замыкания-генератора:")
	for i := 0; i < 10; i++ {
		fmt.Printf("%d ", nextFib())
	}
	fmt.Println()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Первые 10 чисел Фибоначчи из замыкания-генератора:
# 0 1 1 2 3 5 8 13 21 34"""
            }
        ],
        "under_the_hood": """
Переменные `a` и `b` живут в куче в структуре замыкания.
""",
        "pitfalls": """
- Переполнение `int` при генерации более 92 чисел.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова пространственная сложность генератора на замыкании?»
**Ответ:** Строго $O(1)$ дополнительной памяти.
"""
    },
    {
        "num": 11,
        "title": "Генерация N чисел последовательности Фибоначчи в срез []int",
        "task": "Создайте функцию, которая генерирует последовательность Фибоначчи до N-го элемента и возвращает её в виде слайса.",
        "theory": """
Алгоритм предвыделения среза `make([]int, n)` и заполнения за $O(N)$.
""",
        "step_by_step": """
1. Пишем `FibSlice(n int) []int`.
2. Обрабатываем `n <= 0`, `n == 1`, `n >= 2`.
3. Заполняем срез в цикле.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func FibSlice(n int) []int {
	if n <= 0 {
		return []int{}
	}
	if n == 1 {
		return []int{0}
	}
	res := make([]int, n)
	res[0] = 0
	res[1] = 1
	for i := 2; i < n; i++ {
		res[i] = res[i-1] + res[i-2]
	}
	return res
}

func main() {
	fmt.Printf("FibSlice(8): %v\n", FibSlice(8))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# FibSlice(8): [0 1 1 2 3 5 8 13]"""
            }
        ],
        "under_the_hood": """
1 аллокация памяти под срез нужного размера.
""",
        "pitfalls": """
- Вызов `FibSlice(0)` без проверки: может вызвать панику `index out of range [1]`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему итеративное заполнение среза быстрее наивной рекурсии?»
**Ответ:** Итеративный алгоритм имеет сложность $O(N)$ времени, а наивная рекурсия — $O(2^N)$.
"""
    },
    {
        "num": 12,
        "title": "Рекурсивное вычисление факториала и базовый случай рекурсии",
        "task": "Реализуйте рекурсивное вычисление факториала.",
        "theory": """
**Анатомия рекурсии в Go:**
- **Базовый случай (Base Case):** условие выхода `if n <= 1 { return 1 }`;
- **Шаг рекурсии:** `n * Factorial(n-1)`;
- В Go стековые фреймы горутин динамически растут (от 2 КБ до 1 ГБ на 64-бит), но хвостовая рекурсия компилятором не оптимизируется.
""",
        "step_by_step": """
1. Пишем `Factorial(n int) int`.
2. Задаем базовый случай `n <= 1`.
3. Тестируем на числах 0..6.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Factorial(n int) int {
	if n <= 1 {
		return 1
	}
	return n * Factorial(n-1)
}

func main() {
	for i := 0; i <= 6; i++ {
		fmt.Printf("%d! = %d\n", i, Factorial(i))
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 0! = 1
# 1! = 1
# 2! = 2
# 3! = 6
# 4! = 24
# 5! = 120
# 6! = 720"""
            }
        ],
        "under_the_hood": """
Каждый рекурсивный вызов создает новый стековый фрейм.
""",
        "pitfalls": """
- Вызов с отрицательными числами `Factorial(-5)`: без проверки `n <= 1` вызовет бесконечную рекурсию и Stack Overflow.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Оптимизирует ли компилятор `gc` хвостовую рекурсию (Tail Call Optimization)?»
**Ответ:** НЕТ! Компилятор Go намеренно не делает TCO, чтобы сохранять точный стек-трейс при сборе паник и профилировании `pprof`.
"""
    },
    {
        "num": 13,
        "title": "Каррирование функций (Currying): adder(a int) func(int) int",
        "task": "Реализуйте «каррированную» функцию: adder(a int) func(int) int, возвращающую функцию, прибавляющую a.",
        "theory": """
**Каррирование (Currying / Partial Application):**
- Преобразование функции от нескольких аргументов в цепочку функций от одного аргумента;
- Позволяет фиксировать часть параметров (конфигурацию, смещения, логгеры) для повторного использования.
""",
        "step_by_step": """
1. Пишем `Adder(a int) func(int) int`.
2. Создаем специализированные функции `add10` и `add100`.
3. Применяем к числам.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Adder(a int) func(int) int {
	return func(b int) int {
		return a + b
	}
}

func main() {
	add10 := Adder(10)
	add100 := Adder(100)

	fmt.Printf("add10(5):   %d\n", add10(5))
	fmt.Printf("add10(25):  %d\n", add10(25))
	fmt.Printf("add100(50): %d\n", add100(50))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# add10(5):   15
# add10(25):  35
# add100(50): 150"""
            }
        ],
        "under_the_hood": """
Аргумент `a` захватывается замыканием и хранится в объекте функции.
""",
        "pitfalls": """
- Избыточное каррирование простых функций: усложняет код без практической необходимости.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Где в Go повсеместно применяется частичное применение функций?»
**Ответ:** В HTTP-мидлварях (`func AuthMiddleware(secret string) func(http.Handler) http.Handler`).
"""
    },
    {
        "num": 14,
        "title": "Влияние именованных возвращаемых значений (Naked Return) на читаемость и самодокументирование кода",
        "task": "Создайте функцию с именованными возвращаемыми значениями (naked return) и изучите, как это влияет на читаемость кода.",
        "theory": """
**Инженерные стандарты использования Named Returns:**
1. **Рекомендуется:** для коротких функций, где имена служат документацией (`(width, height int, err error)`);
2. **Запрещается:** для сложных функций с множеством ветвлений `if/else`, циклов и более 20 строк кода.
""",
        "step_by_step": """
1. Пишем компактную функцию `MinMax(a, b int) (min, max int)`.
2. Сравниваем читаемость.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func MinMax(a, b int) (min, max int) {
	if a < b {
		min, max = a, b
	} else {
		min, max = b, a
	}
	return // Naked return уместен в коротких функциях
}

func main() {
	min, max := MinMax(42, 17)
	fmt.Printf("Min: %d, Max: %d\n", min, max)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Min: 17, Max: 42"""
            }
        ],
        "under_the_hood": """
Имена `min` и `max` используются как подсказки в IDE и документации `godoc`.
""",
        "pitfalls": """
- Случайное затенение через `min := ...` внутри блока `if`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как именованные возвращаемые значения помогают `defer`?»
**Ответ:** Они позволяют отложенной функции `defer` читать и модифицировать финальный возвращаемый результат (например, логировать ошибку или оборачивать ее в `fmt.Errorf`).
"""
    },
    {
        "num": 15,
        "title": "Передача массива [5]int по значению в функцию: изоляция памяти и отсутствие мутаций",
        "task": "Реализуйте функцию, которая принимает массив (не слайс!) и изменяет его элементы. Убедитесь, что массив передается по значению.",
        "theory": """
**Семантика передачи массивов в функции:**
- В отличие от C/C++ (где массив вырождается в указатель), в Go массивы `[N]T` являются **значимыми типами (Value Types)**;
- При передаче массива в функцию создается **полная побайтовая копия** всех элементов;
- Изменения внутри функции остаются в локальной копии и не влияют на оригинал.
""",
        "step_by_step": """
1. Пишем `ModifyArray(arr [5]int)`.
2. Изменяем `arr[0] = 999`.
3. Проверяем оригинальный массив в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func ModifyArray(arr [5]int) {
	arr[0] = 999
	fmt.Printf("Внутри функции ModifyArray: %v\n", arr)
}

func main() {
	original := [5]int{1, 2, 3, 4, 5}
	fmt.Printf("До вызова функции:           %v\n", original)

	ModifyArray(original)

	fmt.Printf("После вызова функции:        %v (ОРИГИНАЛ НЕ ИЗМЕНИЛСЯ!)\n", original)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До вызова функции:           [1 2 3 4 5]
# Внутри функции ModifyArray: [999 2 3 4 5]
# После вызова функции:        [1 2 3 4 5] (ОРИГИНАЛ НЕ ИЗМЕНИЛСЯ!)"""
            }
        ],
        "under_the_hood": """
При вызове функции процессор выполняет `memmove` для копирования $5 \times 8 = 40$ байт на стек.
""",
        "pitfalls": """
- Передача гигантских массивов `[1000000]int` по значению: копирует 8 МБ на каждый вызов и переполняет стек.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как разрешить функции модифицировать массив?»
**Ответ:** Передать указатель на массив `*[5]int` или срез `[]int`.
"""
    },
    {
        "num": 16,
        "title": "Множественный возврат Divide(a, b float64) (float64, error) и обработка ошибок в стиле Go",
        "task": "Множественный возврат: Напишите функцию Divide(a, b float64) (float64, error), которая возвращает результат деления и ошибку, если делитель равен нулю.",
        "theory": """
**Золотой стандарт обработки ошибок в Go:**
- Сигнатура `(T, error)`: ошибки возвращаются как обычные значения, а не исключения (`try/catch`);
- При успешном выполнении возвращается `(result, nil)`;
- При сбое возвращается `(zeroValue, fmt.Errorf(...))`;
- Вызывающий код обязан немедленно проверить `if err != nil`.
""",
        "step_by_step": """
1. Пишем `Divide(a, b float64) (float64, error)`.
2. Проверяем `if b == 0`.
3. Тестируем корректное и ошибочное деление.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"errors"
	"fmt"
)

func Divide(a, b float64) (float64, error) {
	if b == 0 {
		return 0, errors.New("деление на ноль невозможно")
	}
	return a / b, nil
}

func main() {
	res1, err1 := Divide(100, 4)
	if err1 != nil {
		fmt.Printf("Ошибка: %v\n", err1)
	} else {
		fmt.Printf("100 / 4 = %.2f\n", res1)
	}

	res2, err2 := Divide(100, 0)
	if err2 != nil {
		fmt.Printf("Ошибка: %v (перехвачена успешно!)\n", err2)
	} else {
		fmt.Printf("100 / 0 = %.2f\n", res2)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 100 / 4 = 25.00
# Ошибка: деление на ноль невозможно (перехвачена успешно!)"""
            }
        ],
        "under_the_hood": """
`errors.New` создает структуру `errorString` в куче.
""",
        "pitfalls": """
- Игнорирование ошибки `res, _ := Divide(100, 0)` в продакшене.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go нет исключений `try-catch`?»
**Ответ:** Потому что явная проверка `if err != nil` делает поток управления предсказуемым, локальным и очевидным при чтении кода, исключая скрытые прыжки стека.
"""
    },
    {
        "num": 17,
        "title": "Модификация именованного возвращаемого значения внутри отложенной функции defer",
        "task": "Покажите, как defer может изменить именованное возвращаемое значение (ловушка с defer func() { result = 42 }()).",
        "theory": """
**Хронология выполнения `return` и `defer`:**
1. Оператор `return x` вычисляет выражение и записывает его в именованные переменные возврата;
2. Выполняются все отложенные функции `defer` (в порядке LIFO);
3. Функции `defer` **имеют прямой доступ к именованным возвращаемым переменным** и могут перезаписать их;
4. Происходит физический возврат из функции.
""",
        "step_by_step": """
1. Пишем `GetMagicNumber() (result int)`.
2. В теле функции пишем `result = 10`.
3. В `defer func() { result = 42 }()` меняем значение.
4. Проверяем результат.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func GetMagicNumber() (result int) {
	defer func() {
		// defer выполняется ПОСЛЕ присваивания в return,
		// поэтому может изменить финальный результат!
		result = 42
	}()

	return 10 // Назначает result = 10, но defer перезапишет в 42!
}

func main() {
	val := GetMagicNumber()
	fmt.Printf("Результат GetMagicNumber(): %d (ПОДМЕНЕН В DEFER!)\n", val)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Результат GetMagicNumber(): 42 (ПОДМЕНЕН В DEFER!)"""
            }
        ],
        "under_the_hood": """
Инструкция `RET` выполняется только после отработки цепочки `_defer`.
""",
        "pitfalls": """
- Попытка изменить неименованный возврат `func Foo() int { defer func() { ... }() }`: не сработает, так как у возвращаемого значения нет имени в замыкании.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как используется модификация именованного возврата в `defer` в продакшене?»
**Ответ:** Для автоматического оборачивания ошибок (`defer func() { if err != nil { err = fmt.Errorf("context: %w", err) } }()`) или фиксации времени выполнения транзакции БД.
"""
    },
    {
        "num": 18,
        "title": "Анонимная функция немедленного исполнения (IIFE — Immediately Invoked Function Expression)",
        "task": "Объявите анонимную функцию и немедленно её вызовите (IIFE).",
        "theory": """
**Паттерн IIFE в Go:**
- Синтаксис: `func(args) { ... }(params)`;
- Используется для локальной изоляции переменных, однократной сложной инициализации или безопасного выполнения блоков с собственным `defer`.
""",
        "step_by_step": """
1. Пишем анонимную функцию `func(x, y int) int { return x * y }(6, 7)`.
2. Печатаем результат.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	// IIFE без аргументов:
	func() {
		fmt.Println("1. IIFE выполнена немедленно!")
	}()

	// IIFE с аргументами и возвратом значения:
	product := func(a, b int) int {
		return a * b
	}(6, 7)

	fmt.Printf("2. Результат вычисления в IIFE: 6 * 7 = %d\n", product)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. IIFE выполнена немедленно!
# 2. Результат вычисления в IIFE: 6 * 7 = 42"""
            }
        ],
        "under_the_hood": """
Компилятор инлайнит IIFE напрямую в точку вызова без оверхеда на вызов функции.
""",
        "pitfalls": """
- Забыть круглые скобки вызова `()` в конце (ошибка `value computed is not used`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Зачем применять IIFE внутри долгоживущих циклов `for`?»
**Ответ:** Чтобы изолировать вызовы `defer` (например, закрытие дескрипторов файлов на каждой итерации), предотвращая накопление незакрытых ресурсов до конца всего цикла.
"""
    },
    {
        "num": 19,
        "title": "Перехват критической паники panic через recover() в defer с возвратом ошибки",
        "task": "Организуйте panic в одной функции и перехватите его через recover в отложенной функции, вернув ошибку.",
        "theory": """
**Механизм Panic & Recover:**
- `panic(v)` прерывает нормальный поток управления и начинает размотку стека (Stack Unwinding);
- `recover()` может быть вызван **только напрямую внутри `defer`**;
- `recover()` останавливает размотку стека и возвращает переданное в `panic` значение `any`;
- Паттерн превращения паники в обычную `error`: `SafeCall() (err error)`.
""",
        "step_by_step": """
1. Пишем `SafeExecute(fn func()) (err error)`.
2. В `defer` перехватываем `r := recover()`.
3. Формируем `err = fmt.Errorf("паника: %v", r)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func DangerousOperation(val int) {
	if val < 0 {
		panic("отрицательное значение недопустимо")
	}
	fmt.Printf("Успешная обработка значения: %d\n", val)
}

func SafeExecute(val int) (err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("перехвачена паника: %v", r)
		}
	}()

	DangerousOperation(val)
	return nil
}

func main() {
	err1 := SafeExecute(100)
	fmt.Printf("1. Вызов с 100: err = %v\n", err1)

	err2 := SafeExecute(-50)
	fmt.Printf("2. Вызов с -50: err = %v (ПРОГРАММА НЕ УПАЛА!)\n", err2)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Успешная обработка значения: 100
# 1. Вызов с 100: err = <nil>
# 2. Вызов с -50: err = перехвачена паника: отрицательное значение недопустимо (ПРОГРАММА НЕ УПАЛА!)"""
            }
        ],
        "under_the_hood": """
`recover` сбрасывает флаг `_panic` в структуре текущей горутины `g`.
""",
        "pitfalls": """
- Вызов `recover()` вне функции `defer`: вернет `nil` и не перехватит панику.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Где в стандартной библиотеке Go обязательно используется `recover`?»
**Ответ:** В HTTP-сервере `net/http` (в каждой горутине обработчика запроса `conn.serve`), чтобы паника в одном клиентском хэндлере не роняла весь веб-сервер.
"""
    },
    {
        "num": 20,
        "title": "Порядок исполнения отложенных вызовов defer: Стек LIFO (Last-In-First-Out)",
        "task": "В одной функции напишите три отложенных вызова defer и определите порядок их исполнения.",
        "theory": """
**Стековая природа `defer` (LIFO):**
- Каждый оператор `defer` помещает функцию в односвязный список (стек) текущего фрейма;
- При выходе из функции отложенные вызовы извлекаются в **обратном порядке** (последний объявленный выполняется первым).
""",
        "step_by_step": """
1. Объявляем 3 вызова `defer fmt.Println(...)` с номерами 1, 2, 3.
2. Фиксируем порядок вывода.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func DeferOrderDemo() {
	fmt.Println("--- Начало функции ---")

	defer fmt.Println("defer #1 (объявлен первым)")
	defer fmt.Println("defer #2 (объявлен вторым)")
	defer fmt.Println("defer #3 (объявлен третьим)")

	fmt.Println("--- Конец тела функции ---")
}

func main() {
	DeferOrderDemo()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# --- Начало функции ---
# --- Конец тела функции ---
# defer #3 (объявлен третьим)
# defer #2 (объявлен вторым)
# defer #1 (объявлен первым)"""
            }
        ],
        "under_the_hood": """
Структура `_defer` прикрепляется к заголовку списка `g._defer`.
""",
        "pitfalls": """
- Ожидание выполнения `defer` в порядке объявления (FIFO).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему для `defer` выбран именно порядок LIFO?»
**Ответ:** Это идеально соответствует симметричному управлению ресурсами: ресурс B, зависящий от ресурса A, должен быть закрыт РАНЬШЕ ресурса A (например: сначала закрываем транзакцию, затем соединение с БД).
"""
    },
    {
        "num": 21,
        "title": "Мутация полей структуры через указатель *Person в аргументах функции",
        "task": "Создайте функцию, принимающую указатель на структуру Person и изменяющую возраст.",
        "theory": """
**Передача структур по указателю `*T`:**
- Позволяет функции модифицировать поля исходного объекта;
- Экономит память и такты CPU при передаче тяжелых структур (копируется только 8-байтный адрес).
""",
        "step_by_step": """
1. Создаем структуру `type Person struct { Name string; Age int }`.
2. Пишем функцию `Birthday(p *Person)`.
3. Проверяем изменение возраста.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Person struct {
	Name string
	Age  int
}

func Birthday(p *Person) {
	if p == nil {
		return
	}
	p.Age++ // Автоматическое разыменование указателя в Go
	fmt.Printf("🎉 С днем рождения, %s! Теперь вам %d лет.\n", p.Name, p.Age)
}

func main() {
	user := Person{Name: "Иван", Age: 29}
	fmt.Printf("До дня рождения:   %+v\n", user)

	Birthday(&user)

	fmt.Printf("После дня рождения: %+v (МУТАЦИЯ СОХРАНИЛАСЬ!)\n", user)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До дня рождения:   {Name:Иван Age:29}
# 🎉 С днем рождения, Иван! Теперь вам 30 лет.
# После дня рождения: {Name:Иван Age:30} (МУТАЦИЯ СОХРАНИЛАСЬ!)"""
            }
        ],
        "under_the_hood": """
`p.Age` компилируется в `MOVQ 8(AX), BX; INCQ BX; MOVQ BX, 8(AX)`.
""",
        "pitfalls": """
- Вызов `Birthday(nil)` без проверки `if p == nil`: вызовет панику `nil pointer dereference`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Когда структуру следует передавать по значению, а когда по указателю?»
**Ответ:** По значению — если структура маленькая ($\le 64$ байт) и иммутабельная. По указателю — если требуется мутация полей или структура крупная/содержит `sync.Mutex`.
"""
    },
    {
        "num": 22,
        "title": "Генератор последовательности четных чисел через замыкание EvenGenerator()",
        "task": "Напишите функцию-генератор последовательности четных чисел с использованием замыкания.",
        "theory": """
Инкапсуляция генератора арифметической прогрессии `current += 2`.
""",
        "step_by_step": """
1. Пишем `EvenGenerator() func() int`.
2. Замыкаем переменную `even := 0`.
3. Возвращаем функцию генерации.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func EvenGenerator() func() int {
	even := 0
	return func() int {
		res := even
		even += 2
		return res
	}
}

func main() {
	nextEven := EvenGenerator()

	fmt.Print("Последовательность четных чисел: ")
	for i := 0; i < 6; i++ {
		fmt.Printf("%d ", nextEven())
	}
	fmt.Println()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Последовательность четных чисел: 0 2 4 6 8 10"""
            }
        ],
        "under_the_hood": """
Переменная `even` экранируется в кучу (Heap Escape).
""",
        "pitfalls": """
- Забыть инициализировать генератор отдельной переменной `gen := EvenGenerator()`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова альтернатива замыканиям для генерации бесконечных потоков в Go?»
**Ответ:** Горутина, пишущая в канал `<-chan int`, или итераторы Go 1.23+ (`iter.Seq[int]`).
"""
    },
    {
        "num": 23,
        "title": "Метод типа с указателем-получателем (Pointer Receiver): func (c *Counter) Inc()",
        "task": "Определите метод Inc для типа type Counter int с получателем-указателем; продемонстрируйте вызов.",
        "theory": """
**Методы на пользовательских типах:**
- Go позволяет определять методы на любых типах (не только структурах);
- Указатель-получатель `(c *Counter)` позволяет методу изменять значение самого базового типа `Counter`.
""",
        "step_by_step": """
1. Объявляем `type Counter int`.
2. Пишем метод `func (c *Counter) Inc()`.
3. Пишем метод `func (c Counter) Value() int`.
4. Тестируем инкремент.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Counter int

func (c *Counter) Inc() {
	*c++
}

func (c Counter) Value() int {
	return int(c)
}

func main() {
	var cnt Counter
	fmt.Printf("Начальное значение: %d\n", cnt.Value())

	cnt.Inc()
	cnt.Inc()
	cnt.Inc()

	fmt.Printf("После 3 Inc():      %d\n", cnt.Value())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Начальное значение: 0
# После 3 Inc():      3"""
            }
        ],
        "under_the_hood": """
Синтаксис `cnt.Inc()` автоматически преобразуется компилятором в `(&cnt).Inc()`.
""",
        "pitfalls": """
- Объявление `func (c Counter) Inc()` без указателя: метод изменит только локальную копию `c`, а исходный счетчик останется `0`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем разница между Method Value и Method Expression?»
**Ответ:** Method Value (`fn := cnt.Inc`) привязан к конкретному экземпляру. Method Expression (`fn := (*Counter).Inc`) принимает объект первым явным аргументом `fn(&cnt)`.
"""
    },
    {
        "num": 24,
        "title": "Функции первого класса (First-Class Functions): хранение функций в переменных",
        "task": "Функция как переменная: Присвой анонимную функцию переменной и вызови её несколько раз через эту переменную.",
        "theory": """
**Функции как объекты первого класса (First-Class Citizens):**
- В Go функции могут быть присвоены переменным, переданы в качестве аргументов и возвращены из других функций;
- Переменная типа `func(int, int) int` хранит указатель на машинный код функции.
""",
        "step_by_step": """
1. Объявляем переменную `var multiplier func(int, int) int`.
2. Присваиваем анонимную функцию умножения.
3. Вызываем через переменную.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	// Присваиваем анонимную функцию переменной:
	multiplier := func(a, b int) int {
		return a * b
	}

	fmt.Printf("1. multiplier(3, 4):  %d\n", multiplier(3, 4))
	fmt.Printf("2. multiplier(10, 5): %d\n", multiplier(10, 5))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. multiplier(3, 4):  12
# 2. multiplier(10, 5): 50"""
            }
        ],
        "under_the_hood": """
Вызов `multiplier(3, 4)` компилируется в косвенный вызов `CALL RAX`.
""",
        "pitfalls": """
- Вызов неинициализированной переменной `var f func(); f()`: вызовет панику `nil pointer dereference`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каков размер переменной типа `func()` в памяти?»
**Ответ:** Ровно 8 байт (указатель на функцию).
"""
    },
    {
        "num": 25,
        "title": "Создание и вызов функции SayHello()",
        "task": "Простая функция: Напишите функцию SayHello(), которая просто печатает приветствие в консоль.",
        "theory": """
Закрепление объявления глобальных функций пакета.
""",
        "step_by_step": """
1. Пишем `SayHello()`.
2. Вызываем из `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func SayHello() {
	fmt.Println("Привет из функции SayHello!")
}

func main() {
	SayHello()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Привет из функции SayHello!"""
            }
        ],
        "under_the_hood": """
Символ `SayHello` регистрируется в таблице символов линкера.
""",
        "pitfalls": """
- Несовпадение регистра (экспортируемая `SayHello` vs внутренняя `sayHello`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что определяет экспорт функции за пределы пакета?»
**Ответ:** Заглавная первая буква имени функции (PascalCase).
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 1: {len(exercises)} exercises.")
