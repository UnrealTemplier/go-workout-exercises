# Chapter 10 Part 3: Exercises 51 to 75

exercises = [
    {
        "num": 51,
        "title": "Функция высшего порядка ApplyOperation(a, b, op) и передача анонимных лямбд",
        "task": "Напиши функцию ApplyOperation(a, b int, op func(int, int) int) int. Передай ей анонимную функцию для умножения.",
        "theory": """
Применение функциональных параметров для динамической смены алгоритма вычислений.
""",
        "step_by_step": """
1. Пишем `ApplyOperation(a, b int, op func(int, int) int) int`.
2. Передаем анонимную функцию умножения `func(x, y int) int { return x * y }`.
3. Печатаем результат.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func ApplyOperation(a, b int, op func(int, int) int) int {
	return op(a, b)
}

func main() {
	res := ApplyOperation(7, 8, func(x, y int) int {
		return x * y
	})
	fmt.Printf("ApplyOperation(7, 8, mul): %d\n", res)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# ApplyOperation(7, 8, mul): 56"""
            }
        ],
        "under_the_hood": """
Инлайнинг замыкания при статической оптимизации компилятора.
""",
        "pitfalls": """
- Передача `nil`-функции в `ApplyOperation`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова сигнатура функции `strings.Map`?»
**Ответ:** `func Map(mapping func(rune) rune, s string) string`.
"""
    },
    {
        "num": 52,
        "title": "Многокритериальная сортировка среза структур через sort.Slice с замыканием",
        "task": "Используйте sort.Slice с функцией-замыканием для сортировки среза структур по разным полям.",
        "theory": """
**Замыкание в `sort.Slice`:**
- Функция `less func(i, j int) bool` замыкает срез структур;
- Сравнивает элементы по нескольким критериям (например: сначала по убыванию рейтинга, затем по алфавиту имени).
""",
        "step_by_step": """
1. Создаем структуру `Product{Name string, Price float64, Rating float64}`.
2. Сортируем срез через `sort.Slice`.
3. Печатаем отсортированный список.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sort"
)

type Product struct {
	Name   string
	Price  float64
	Rating float64
}

func main() {
	products := []Product{
		{Name: "Ноутбук", Price: 80000, Rating: 4.8},
		{Name: "Мышь", Price: 1500, Rating: 4.5},
		{Name: "Клавиатура", Price: 4500, Rating: 4.8},
		{Name: "Монитор", Price: 25000, Rating: 4.2},
	}

	// Сортировка: сначала по убыванию Rating, затем по возрастанию Price
	sort.Slice(products, func(i, j int) bool {
		if products[i].Rating != products[j].Rating {
			return products[i].Rating > products[j].Rating // Высокий рейтинг вначале
		}
		return products[i].Price < products[j].Price // При равном рейтинге — дешевле
	})

	fmt.Println("Отсортированный каталог товаров:")
	for _, p := range products {
		fmt.Printf("  • %-12s | Рейтинг: %.1f | Цена: %6.0f руб.\n", p.Name, p.Rating, p.Price)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Отсортированный каталог товаров:
#   • Клавиатура   | Рейтинг: 4.8 | Цена:   4500 руб.
#   • Ноутбук      | Рейтинг: 4.8 | Цена:  80000 руб.
#   • Мышь         | Рейтинг: 4.5 | Цена:   1500 руб.
#   • Монитор      | Рейтинг: 4.2 | Цена:  25000 руб.
"""
            }
        ],
        "under_the_hood": """
`sort.Slice` использует рефлексию `reflect.Swapper` для обмена элементов по индексам.
""",
        "pitfalls": """
- Использование оператора `>=` вместо `>`: нарушает Strict Weak Ordering и приводит к багам сортировки.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go 1.21+ рекомендуется использовать `slices.SortFunc` вместо `sort.Slice`?»
**Ответ:** `slices.SortFunc` построен на дженериках, не использует рефлексию и работает на $30-50\%$ быстрее.
"""
    },
    {
        "num": 53,
        "title": "Базовая функция с параметром Greet(name string)",
        "task": "Напиши функцию Greet(name string), которая выводит приветствие. Вызови её из main.",
        "theory": """
Базовая передача строки по значению.
""",
        "step_by_step": """
1. Пишем `Greet(name string)`.
2. Печатаем `"Привет, %s!"`.
3. Вызываем из `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Greet(name string) {
	fmt.Printf("Привет, %s! Успешной компиляции.\n", name)
}

func main() {
	Greet("Александр")
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Привет, Александр! Успешной компиляции."""
            }
        ],
        "under_the_hood": """
Строка передается как 16-байтный дескриптор `(Data uintptr, Len int)`.
""",
        "pitfalls": """
- Передача `""` (пустой строки).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Копируются ли байты строки при передаче в функцию `Greet(name string)`?»
**Ответ:** НЕТ! Копируется только 16-байтный заголовок `StringHeader`, а сам массив байт в памяти не дублируется (Read-Only).
"""
    },
    {
        "num": 54,
        "title": "Калькулятор вещественных чисел на базе таблицы операций map[string]func",
        "task": "Реализуйте калькулятор с операциями, хранящимися в map[string]func(float64, float64) float64.",
        "theory": """
Таблица диспетчеризации для вещественных чисел с обработкой степеней и деления.
""",
        "step_by_step": """
1. Создаем `map[string]func(float64, float64) float64`.
2. Заполняем `+`, `-`, `*`, `/`, `^`.
3. Вычисляем выражения.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"math"
)

func main() {
	calc := map[string]func(float64, float64) float64{
		"+": func(a, b float64) float64 { return a + b },
		"-": func(a, b float64) float64 { return a - b },
		"*": func(a, b float64) float64 { return a * b },
		"/": func(a, b float64) float64 { return a / b },
		"^": func(a, b float64) float64 { return math.Pow(a, b) },
	}

	fmt.Printf("10 + 5 = %.1f\n", calc["+"](10, 5))
	fmt.Printf("10 / 4 = %.2f\n", calc["/"](10, 4))
	fmt.Printf("2 ^ 10 = %.0f\n", calc["^"](2, 10))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 10 + 5 = 15.0
# 10 / 4 = 2.50
# 2 ^ 10 = 1024"""
            }
        ],
        "under_the_hood": """
Хранение указателей на функции в бакетах `hmap`.
""",
        "pitfalls": """
- Вызов неизвестного оператора `calc["%"](10, 2)` без проверки `ok`: вызовет панику разыменования `nil`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каковы преимущества таблицы диспетчеризации перед `eval` интерпретатором?»
**Ответ:** Статическая типизация, безопасность (отсутствие инъекций кода) и высокая скорость выполнения.
"""
    },
    {
        "num": 55,
        "title": "Передача динамического среза в вариативную функцию Sum(nums ...int)",
        "task": "Распаковка слайса: Создай обычный срез (slice) []int. Передай его в функцию Sum с помощью оператора ... (распаковка).",
        "theory": """
Закрепление распаковки динамического среза.
""",
        "step_by_step": """
1. Пишем `Sum(nums ...int) int`.
2. Создаем `scores := []int{10, 20, 30, 40}`.
3. Передаем `Sum(scores...)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Sum(nums ...int) int {
	res := 0
	for _, v := range nums {
		res += v
	}
	return res
}

func main() {
	scores := []int{10, 20, 30, 40}
	total := Sum(scores...)
	fmt.Printf("Сумма элементов среза %v = %d\n", scores, total)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Сумма элементов среза [10 20 30 40] = 100"""
            }
        ],
        "under_the_hood": """
Срезовый дескриптор передается по значению.
""",
        "pitfalls": """
- Попытка передать `Sum(scores)` без `...`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли объединить явные параметры и вариативный срез?»
**Ответ:** Да: `func Log(prefix string, nums ...int)`.
"""
    },
    {
        "num": 56,
        "title": "Возврат ошибки errors.New при делении на ноль и проверка err != nil",
        "task": "Напиши функцию Divide(a, b float64) (float64, error). При b == 0 верни ошибку (errors.New). Обработай ошибку в вызывающем коде.",
        "theory": """
Обработка ошибок через пакет `errors`.
""",
        "step_by_step": """
1. Пишем `Divide(a, b float64) (float64, error)`.
2. Используем `errors.New("division by zero")`.
3. Проверяем `if err != nil`.
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

var ErrDivideByZero = errors.New("деление на ноль недопустимо")

func Divide(a, b float64) (float64, error) {
	if b == 0 {
		return 0, ErrDivideByZero
	}
	return a / b, nil
}

func main() {
	val, err := Divide(50, 0)
	if err != nil {
		fmt.Printf("❌ Ошибка вычислений: %v\n", err)
		return
	}
	fmt.Printf("Результат: %.2f\n", val)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# ❌ Ошибка вычислений: деление на ноль недопустимо"""
            }
        ],
        "under_the_hood": """
Паттерн Sentinel Error (`var ErrDivideByZero`) позволяет проверять ошибку через `errors.Is(err, ErrDivideByZero)`.
""",
        "pitfalls": """
- Создание новой ошибки `errors.New(...)` на каждый вызов вместо Sentinel ошибки в пакете.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что такое Sentinel Error в Go?»
**Ответ:** Экспортируемая глобальная переменная ошибки (например `io.EOF`, `sql.ErrNoRows`), позволяющая вызывающему коду точно идентифицировать причину сбоя.
"""
    },
    {
        "num": 57,
        "title": "Рекурсивный метод String() для древовидной структуры данных (Binary Tree)",
        "task": "Создайте метод String() string для сложной структуры (например, дерева), обеспечивающий её красивое рекурсивное представление.",
        "theory": """
**Рекурсивная печать структур данных:**
- Метод `String()` структуры `TreeNode` рекурсивно обходит левое и правое поддеревья;
- Обеспечивает наглядную визуализацию дерева в консоли.
""",
        "step_by_step": """
1. Создаем `type TreeNode struct { Val int; Left, Right *TreeNode }`.
2. Пишем метод `func (n *TreeNode) String() string`.
3. Создаем бинарное дерево и выводим через `fmt.Println`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type TreeNode struct {
	Val   int
	Left  *TreeNode
	Right *TreeNode
}

func (n *TreeNode) String() string {
	if n == nil {
		return "nil"
	}
	if n.Left == nil && n.Right == nil {
		return fmt.Sprintf("%d", n.Val)
	}
	return fmt.Sprintf("(%d L:%s R:%s)", n.Val, n.Left.String(), n.Right.String())
}

func main() {
	// Дерево:        10
	//              /    \
	//             5      15
	//            / \
	//           2   7
	root := &TreeNode{
		Val: 10,
		Left: &TreeNode{
			Val:   5,
			Left:  &TreeNode{Val: 2},
			Right: &TreeNode{Val: 7},
		},
		Right: &TreeNode{Val: 15},
	}

	fmt.Println("Древовидная структура:")
	fmt.Println(root)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Древовидная структура:
# (10 L:(5 L:2 R:7) R:15)"""
            }
        ],
        "under_the_hood": """
Рекурсивный обход дерева формирует строковый буфер.
""",
        "pitfalls": """
- Циклические ссылки в графах (вызовут бесконечную рекурсию).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова сложность метода `String()` для бинарного дерева из $N$ узлов?»
**Ответ:** $O(N)$ времени (каждый узел посещается ровно один раз).
"""
    },
    {
        "num": 58,
        "title": "Переменная функционального типа operation и динамическая замена алгоритма",
        "task": "Функция как переменная: Создайте переменную operation типа \"функция, принимающая два int и возвращающая int\". Присвойте ей анонимную функцию сложения, а затем замените её на функцию умножения.",
        "theory": """
Динамическая замена поведения переменной типа `func(int, int) int`.
""",
        "step_by_step": """
1. Объявляем `var operation func(a, b int) int`.
2. Присваиваем сложение.
3. Заменяем на умножение.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	var operation func(int, int) int

	// 1. Сложение:
	operation = func(a, b int) int { return a + b }
	fmt.Printf("1. Сложение: 10 + 20 = %d\n", operation(10, 20))

	// 2. Замена на умножение:
	operation = func(a, b int) int { return a * b }
	fmt.Printf("2. Умножение: 10 * 20 = %d\n", operation(10, 20))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Сложение: 10 + 20 = 30
# 2. Умножение: 10 * 20 = 200"""
            }
        ],
        "under_the_hood": """
Перезапись указателя на функцию в стековом слоте.
""",
        "pitfalls": """
- Попытка присвоить функцию с несовпадающей сигнатурой `func(float64, float64) float64` (ошибка компиляции).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Является ли имя параметров частью сигнатуры типа функции?»
**Ответ:** НЕТ! Сигнатура типа функции определяется только типами принимаемых параметров и типами возвращаемых значений.
"""
    },
    {
        "num": 59,
        "title": "Локальная анонимная функция немедленного вызова прямо в теле main()",
        "task": "Анонимные функции: Объяви функцию прямо внутри main() без имени и тут же вызови её.",
        "theory": """
Базовый синтаксис немедленного выполнения анонимной лямбды.
""",
        "step_by_step": """
1. Пишем `func() { fmt.Println(...) }()`.
2. Запускаем.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	func() {
		fmt.Println("Анонимная функция выполнена успешно!")
	}()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Анонимная функция выполнена успешно!"""
            }
        ],
        "under_the_hood": """
Инлайнинг тела функции в тело `main`.
""",
        "pitfalls": """
- Отсутствие `()` в конце.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли запустить анонимную функцию в отдельной горутине?»
**Ответ:** ДА! С помощью ключевого слова `go func() { ... }()`.
"""
    },
    {
        "num": 60,
        "title": "Хронология отложенного вызова: Start в теле функции, End в defer",
        "task": "Напиши функцию с отложенным вызовом defer. Внутри функции выведи \"Start\", в defer выведи \"End\". Вызови функцию.",
        "theory": """
Иллюстрация границ выполнения функции и оператора `defer`.
""",
        "step_by_step": """
1. Пишем `RunTask()`.
2. Регистрируем `defer fmt.Println("End")`.
3. Печатаем `"Start"`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func RunTask() {
	defer fmt.Println("End (вызвано из defer при выходе)")

	fmt.Println("Start (вызвано в теле функции)")
	fmt.Println("Работа функции продолжается...")
}

func main() {
	RunTask()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Start (вызвано в теле функции)
# Работа функции продолжается...
# End (вызвано из defer при выходе)"""
            }
        ],
        "under_the_hood": """
`defer` выполняется строго после завершения основного тела функции.
""",
        "pitfalls": """
- Вызов `os.Exit()` внутри тела функции (defer не сработает).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Когда именно вызывается `defer`: до или после `return`?»
**Ответ:** Значения для `return` вычисляются ДО вызова `defer`, но физический выход из функции и возврат управления вызывающей стороне происходит ПОСЛЕ отработки всех `defer`.
"""
    },
    {
        "num": 61,
        "title": "Функция высшего порядка Filter(nums []int, predicate func(int) bool) []int",
        "task": "Функции высшего порядка (Аргумент): Напиши функцию Filter, которая принимает срез чисел и функцию-условие (func(int) bool). Она должна вернуть только те числа, для которых условие вернуло true.",
        "theory": """
Изолированная функция фильтрации данных по предикату.
""",
        "step_by_step": """
1. Пишем `Filter(s []int, pred func(int) bool) []int`.
2. Фильтруем числа, кратные 3.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Filter(s []int, predicate func(int) bool) []int {
	var out []int
	for _, v := range s {
		if predicate(v) {
			out = append(out, v)
		}
	}
	return out
}

func main() {
	data := []int{1, 3, 4, 6, 7, 9, 10, 12}
	multiplesOfThree := Filter(data, func(n int) bool {
		return n%3 == 0
	})
	fmt.Printf("Числа, кратные 3: %v\n", multiplesOfThree)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Числа, кратные 3: [3 6 9 12]"""
            }
        ],
        "under_the_hood": """
Динамический вызов предиката.
""",
        "pitfalls": """
- Забыть инициализировать срез `out`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как реализовать `Filter` без аллокаций памяти?»
**Ответ:** Модифицировать срез на месте (In-Place) и вернуть подсрез `s[:w]`.
"""
    },
    {
        "num": 62,
        "title": "Цикл с тремя вызовами defer и фиксация LIFO порядка исполнения",
        "task": "Создай цикл с тремя вызовами defer. Посмотри, в каком порядке они выполнятся (LIFO).",
        "theory": """
Размещение вызовов `defer` внутри цикла `for`.
""",
        "step_by_step": """
1. В цикле от 1 до 3 регистрируем `defer fmt.Println(...)`.
2. Фиксируем обратный порядок (3, 2, 1).
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func LoopDefer() {
	for i := 1; i <= 3; i++ {
		defer fmt.Printf("defer в цикле: шаг #%d\n", i)
	}
	fmt.Println("Тело цикла завершено")
}

func main() {
	LoopDefer()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Тело цикла завершено
# defer в цикле: шаг #3
# defer в цикле: шаг #2
# defer в цикле: шаг #1"""
            }
        ],
        "under_the_hood": """
Каждая итерация цикла пушит новый вызов в стек `_defer`.
""",
        "pitfalls": """
- Размещение `defer` в цикле на 1 000 000 итераций: приведет к накоплению 1 млн объектов в стеке `_defer` до самого конца функции.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему опасно использовать `defer` внутри бесконечных или больших циклов?»
**Ответ:** Потому что `defer` привязан к завершению ФУНКЦИИ, а не итерации цикла. Ресурсы не освободятся до выхода из функции, что может исчерпать дескрипторы или память.
"""
    },
    {
        "num": 63,
        "title": "Генератор уникальных автоинкрементных идентификаторов NewIDGenerator() func() int",
        "task": "Замыкание (Closure): Создайте генератор идентификаторов NewIDGenerator() func() int. Каждый вызов возвращенной функции должен возвращать число на 1 больше предыдущего (начиная с 1).",
        "theory": """
Инкапсуляция генератора ID через замыкание.
""",
        "step_by_step": """
1. Пишем `NewIDGenerator() func() int`.
2. Замыкаем `id := 0`.
3. При вызове возвращаем `id++`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func NewIDGenerator() func() int {
	id := 0
	return func() int {
		id++
		return id
	}
}

func main() {
	nextID := NewIDGenerator()

	fmt.Printf("ID: %d\n", nextID())
	fmt.Printf("ID: %d\n", nextID())
	fmt.Printf("ID: %d\n", nextID())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# ID: 1
# ID: 2
# ID: 3"""
            }
        ],
        "under_the_hood": """
Изолированная переменная `id` в куче.
""",
        "pitfalls": """
- В конкурентной среде требует атомиков (`atomic.AddInt64`) или мьютекса.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как сделать генератор ID потокобезопасным без мьютексов?»
**Ответ:** Использовать пакет `sync/atomic` и функцию `atomic.AddInt64(&id, 1)`.
"""
    },
    {
        "num": 64,
        "title": "Каверзный кейс: defer func() { println(i) } в цикле и передача аргумента",
        "task": "[Каверзный кейс]: Напиши цикл for i := 0; i < 3; i++ с defer fmt.Println(i) внутри. Объясни, почему выведутся двойки (и как это исправить, передавая аргумент в функцию).",
        "theory": """
**Разница между прямой передачей аргумента и анонимным замыканием в `defer`:**
1. `defer fmt.Println(i)` вычисляет аргумент `i` **немедленно в момент объявления** (выведет `2 1 0`);
2. `defer func() { fmt.Println(i) }()` захватывает переменную `i` по ссылке (в старых версиях Go до 1.22 выводил `3 3 3`);
3. Для надежной изоляции аргумент передают явно: `defer func(val int) { fmt.Println(val) }(i)`.
""",
        "step_by_step": """
1. Демонстрируем поведение `defer fmt.Println(i)`.
2. Демонстрируем поведение анонимного замыкания `func(val int)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	fmt.Println("1. Прямая передача аргумента в defer fmt.Println(i):")
	func() {
		for i := 0; i < 3; i++ {
			// Аргумент i вычисляется СРАЗУ при достижении строки defer:
			defer fmt.Printf("  defer прямая передача: %d\n", i)
		}
	}()

	fmt.Println("\n2. Передача параметра в анонимную функцию defer:")
	func() {
		for i := 0; i < 3; i++ {
			defer func(val int) {
				fmt.Printf("  defer через аргумент: %d\n", val)
			}(i) // Значение i копируется в момент вызова defer!
		}
	}()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Прямая передача аргумента в defer fmt.Println(i):
#   defer прямая передача: 2
#   defer прямая передача: 1
#   defer прямая передача: 0
# 
# 2. Передача параметра в анонимную функцию defer:
#   defer через аргумент: 2
#   defer через аргумент: 1
#   defer через аргумент: 0"""
            }
        ],
        "under_the_hood": """
Аргументы `defer` упаковываются на стек в момент регистрации вызова.
""",
        "pitfalls": """
- Предположение, что аргументы `defer fmt.Println(x)` вычисляются в момент выхода из функции.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Когда именно вычисляются аргументы функции, переданной в `defer`?»
**Ответ:** Аргументы вычисляются НЕМЕДЛЕННО в момент выполнения строки с ключевым словом `defer`.
"""
    },
    {
        "num": 65,
        "title": "Замыкания: функция Counter() с инкрементом при каждом вызове",
        "task": "Замыкания (Closures) 1: Напиши функцию Counter() func() int, которая при каждом вызове возвращает число, на 1 большее предыдущего. (Сохранение состояния в замыкании).",
        "theory": """
Закрепление паттерна счетчика на замыкании.
""",
        "step_by_step": """
1. Пишем `Counter() func() int`.
2. Инициализируем `c := 0`.
3. Тестируем вызовы.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Counter() func() int {
	c := 0
	return func() int {
		c++
		return c
	}
}

func main() {
	cnt := Counter()
	fmt.Printf("1. Вызов: %d\n", cnt())
	fmt.Printf("2. Вызов: %d\n", cnt())
	fmt.Printf("3. Вызов: %d\n", cnt())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Вызов: 1
# 2. Вызов: 2
# 3. Вызов: 3"""
            }
        ],
        "under_the_hood": """
Переменная `c` сохраняет состояние между кадрами стека.
""",
        "pitfalls": """
- Вызов `Counter()()` без сохранения переменной (каждый раз вернет 1).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что вернет `Counter()()` при двух вызовах подряд?»
**Ответ:** Оба раза вернет `1`, так как каждый вызов `Counter()` создает новый счетчик.
"""
    },
    {
        "num": 66,
        "title": "Срез замыканий и анализ поведения переменной цикла в Go 1.22+",
        "task": "Замыкание в цикле (Исторический баг): Создайте срез функций funcs := make([]func(), 3). В цикле for i := 0; i < 3; i++ заполните этот срез анонимными функциями, каждая из которых выводит i. Запустите эти функции после цикла. Какое поведение вы увидите? (Учтите особенности версий Go до 1.22 и современных).",
        "theory": """
Демонстрация работы замыканий в современных версиях Go (1.22+).
""",
        "step_by_step": """
1. Создаем срез `funcs := make([]func(), 3)`.
2. Заполняем `funcs[i] = func() { fmt.Println(i) }`.
3. Вызываем после цикла.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	funcs := make([]func(), 3)

	for i := 0; i < 3; i++ {
		funcs[i] = func() {
			fmt.Printf("Значение i: %d\n", i)
		}
	}

	fmt.Println("Выполнение сохраненных функций:")
	for idx, f := range funcs {
		fmt.Printf("Функция #%d -> ", idx)
		f()
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Выполнение сохраненных функций:
# Функция #0 -> Значение i: 0
# Функция #1 -> Значение i: 1
# Функция #2 -> Значение i: 2"""
            }
        ],
        "under_the_hood": """
Go 1.22 создает независимый экземпляр `i` на каждой итерации.
""",
        "pitfalls": """
- Полагаться на старое поведение Go $\le 1.21$ в новых проектах.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какая переменная окружения управляла изменением поведения цикла в Go 1.21?»
**Ответ:** `GOEXPERIMENT=loopvar`. В Go 1.22 это поведение стало стандартом языка.
"""
    },
    {
        "num": 67,
        "title": "Именованный возврат func Add(a, b int) (sum int) и самодокументирование API",
        "task": "Напиши функцию Add(a, b int) int с именованными параметрами: func Add(a, b int) (sum int) { sum = a + b; return }. Объясни, зачем именованные возвращаемые значения.",
        "theory": """
Именованные параметры в документации `godoc`.
""",
        "step_by_step": """
1. Пишем `Add(a, b int) (sum int)`.
2. Присваиваем `sum = a + b`.
3. Возвращаем `return`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Add(a, b int) (sum int) {
	sum = a + b
	return
}

func main() {
	fmt.Printf("Add(10, 20) = %d\n", Add(10, 20))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Add(10, 20) = 30"""
            }
        ],
        "under_the_hood": """
Стековый слот `sum`.
""",
        "pitfalls": """
- Забыть присвоить значение `sum`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как именованные возвращаемые параметры отображаются в `godoc`?»
**Ответ:** Они отображаются в сигнатуре функции, документируя назначение возвращаемых результатов без необходимости дополнительных комментариев.
"""
    },
    {
        "num": 68,
        "title": "Паттерн Декоратор (Decorator / Middleware) с замером времени и логированием Before/After",
        "task": "[Высокая сложность]: Напиши функцию-обертку (decorator), которая принимает любую функцию (через interface{} или reflect) и выводит \"Before\" до её вызова и \"After\" после.",
        "theory": """
**Паттерн Декоратор (Decorator / Middleware):**
- Оборачивает вызов целевой функции, добавляя логирование, трейсинг или замер метрик;
- Строгая типизация через функциональные типы `type HandlerFunc func(string) error`.
""",
        "step_by_step": """
1. Объявляем тип `type ServiceFunc func(req string) string`.
2. Пишем декоратор `WithLogging(next ServiceFunc) ServiceFunc`.
3. Оборачиваем бизнес-функцию.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type ServiceFunc func(req string) string

func WithLogging(next ServiceFunc) ServiceFunc {
	return func(req string) string {
		fmt.Printf(">>> [BEFORE] Входящий запрос: %q\n", req)
		res := next(req)
		fmt.Printf("<<< [AFTER]  Ответ сформирован: %q\n", res)
		return res
	}
}

func HandleUser(req string) string {
	return fmt.Sprintf("User(%s) успешно обработан", req)
}

func main() {
	// Оборачиваем функцию декоратором:
	decoratedHandler := WithLogging(HandleUser)

	response := decoratedHandler("user_101")
	fmt.Println("Итог:", response)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# >>> [BEFORE] Входящий запрос: "user_101"
# <<< [AFTER]  Ответ сформирован: "User(user_101) успешно обработан"
# Итог: User(user_101) успешно обработан"""
            }
        ],
        "under_the_hood": """
Формирование цепочки вызовов (Chain of Responsibility) в памяти.
""",
        "pitfalls": """
- Использование тяжелой рефлексии `reflect.ValueOf`: типизированные сигнатуры работают в 100 раз быстрее.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как строится цепочка Middleware в веб-фреймворках (Gin, Chi, Echo)?»
**Ответ:** Путем последовательного оборачивания `handler = Middleware1(Middleware2(Middleware3(finalHandler)))`.
"""
    },
    {
        "num": 69,
        "title": "Базовый defer: гарантированное освобождение ресурсов ресурса",
        "task": "Базовый defer: Напишите функцию, которая открывает гипотетический ресурс (выводит \"ресурс открыт\"), затем производит вычисления, а закрытие ресурса (\"ресурс закрыт\") гарантирует с помощью defer.",
        "theory": """
Идиома гарантированного освобождения соединений, транзакций и мьютексов.
""",
        "step_by_step": """
1. Пишем `ManageResource()`.
2. Открываем ресурс.
3. Ставим `defer Close()`.
4. Производим вычисления.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func ManageResource() {
	fmt.Println("1. 🔌 Ресурс (БД соединение) открыт")
	defer fmt.Println("3. 🔒 Ресурс (БД соединение) закрыт")

	fmt.Println("2. ⚡ Выполнение транзакции и вычислений...")
}

func main() {
	ManageResource()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. 🔌 Ресурс (БД соединение) открыт
# 2. ⚡ Выполнение транзакции и вычислений...
# 3. 🔒 Ресурс (БД соединение) закрыт"""
            }
        ],
        "under_the_hood": """
`defer` вызывается компилятором перед инструкцией возврата `RET`.
""",
        "pitfalls": """
- Забыть `defer` при наличии 10 разных веток `return err`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем главное преимущество `defer` перед ручным вызовом закрытия ресурсов в блоках `if err != nil`?»
**Ответ:** Исключение человеческого фактора (забытый `Close()` в одной из 15 веток ошибок) и устранение дублирования кода очистки.
"""
    },
    {
        "num": 70,
        "title": "Изолированное состояние нескольких экземпляров замыкания",
        "task": "Замыкания 2: Создай несколько независимых счетчиков из упр. 62. Убедись, что каждый ведет свой счет независимо.",
        "theory": """
Доказательство независимости кучевых аллокаций каждого экземпляра замыкания.
""",
        "step_by_step": """
1. Создаем `c1 := MakeCounter()`, `c2 := MakeCounter()`.
2. Инкрементируем `c1` дважды, `c2` трижды.
3. Сравниваем результаты.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func MakeCounter() func() int {
	val := 0
	return func() int {
		val++
		return val
	}
}

func main() {
	counterA := MakeCounter()
	counterB := MakeCounter()

	counterA()
	counterA()
	fmt.Printf("Counter A: %d\n", counterA()) // 3

	fmt.Printf("Counter B: %d\n", counterB()) // 1
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Counter A: 3
# Counter B: 1"""
            }
        ],
        "under_the_hood": """
Два разных адреса в куче для `val`.
""",
        "pitfalls": """
- Использование глобальной переменной вместо локальной в фабрике замыканий.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какому паттерну ООП эквивалентно замыкание с локальным состоянием?»
**Ответ:** Объекту с приватным полем и одним публичным методом (`class Counter { private int val; public int Inc() { ... } }`).
"""
    },
    {
        "num": 71,
        "title": "Стековый порядок исполнения defer (LIFO): вывод чисел 1, 2, 3",
        "task": "Порядок выполнения defer (LIFO): Напишите функцию, в которой друг за другом вызываются три оператора defer с выводом чисел 1, 2 и 3. Убедитесь в порядке их выполнения (стек).",
        "theory": """
LIFO проверка порядка: `defer 1`, `defer 2`, `defer 3` $\rightarrow$ вывод `3`, `2`, `1`.
""",
        "step_by_step": """
1. Регистрируем `defer 1`, `defer 2`, `defer 3`.
2. Проверяем порядок.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func TestLIFO() {
	defer fmt.Println("defer 1")
	defer fmt.Println("defer 2")
	defer fmt.Println("defer 3")
}

func main() {
	TestLIFO()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# defer 3
# defer 2
# defer 1"""
            }
        ],
        "under_the_hood": """
Стек вызовов разматывается сверху вниз.
""",
        "pitfalls": """
- Ожидание порядка 1, 2, 3.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что происходит со стеком `defer`, если функция завершается паникой?»
**Ответ:** Все зарегистрированные до момента паники `defer` гарантированно выполняются в обычном порядке LIFO.
"""
    },
    {
        "num": 72,
        "title": "Захват переменной цикла в срез анонимных функций (Go 1.22+ Per-Iteration Scoping)",
        "task": "Каверзный случай с циклами (Go до 1.22): Напиши цикл for i := 0; i < 3; i++, внутри которого в слайс добавляются анонимные функции, возвращающие i. Вызови функции после цикла. Изучи проблему захвата переменной цикла (с версии 1.22 поведение изменилось, поэкспериментируй!).",
        "theory": """
Сравнительный анализ работы замыканий в Go 1.22+.
""",
        "step_by_step": """
1. Создаем `slice := make([]func() int, 3)`.
2. Заполняем `slice[i] = func() int { return i }`.
3. Печатаем результаты.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	var funcs []func() int

	for i := 0; i < 3; i++ {
		funcs = append(funcs, func() int {
			return i
		})
	}

	fmt.Println("Результаты вызова функций:")
	for idx, fn := range funcs {
		fmt.Printf("  Функция #%d вернула: %d\n", idx, fn())
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Результаты вызова функций:
#   Функция #0 вернула: 0
#   Функция #1 вернула: 1
#   Функция #2 вернула: 2"""
            }
        ],
        "under_the_hood": """
Per-iteration переменная `i` аллоцируется отдельно для каждого замыкания.
""",
        "pitfalls": """
- Запуск старых проектов Go 1.20 на новом компиляторе без проверки семантики циклов.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go 1.22 изменили семантику цикла `for`?»
**Ответ:** По статистике Google, баг захвата переменной цикла был самой частой причиной скрытых ошибок в конкурентном Go-коде (горутины и замыкания в цикле).
"""
    },
    {
        "num": 73,
        "title": "Множественный возврат минимума и максимума MinMax(nums ...int) (min, max int)",
        "task": "Напиши функцию с множественным возвратом: MinMax(nums ...int) (min, max int). Найди минимум и максимум в слайсе.",
        "theory": """
Эффективный одновременный поиск экстремумов за $O(N)$.
""",
        "step_by_step": """
1. Пишем `MinMax(nums ...int) (min, max int, err error)`.
2. Проверяем `len(nums) == 0`.
3. Находим минимум и максимум за 1 проход.
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

func MinMax(nums ...int) (min, max int, err error) {
	if len(nums) == 0 {
		return 0, 0, errors.New("пустой список чисел")
	}
	min, max = nums[0], nums[0]
	for _, n := range nums[1:] {
		if n < min {
			min = n
		}
		if n > max {
			max = n
		}
	}
	return min, max, nil
}

func main() {
	minVal, maxVal, err := MinMax(15, -3, 42, 99, 0, -8)
	if err == nil {
		fmt.Printf("Min: %d, Max: %d\n", minVal, maxVal)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Min: -8, Max: 99"""
            }
        ],
        "under_the_hood": """
1 проход по массиву с минимумом сравнений.
""",
        "pitfalls": """
- Инициализация `min = 0` вместо `nums[0]` (ошибочно для положительных чисел).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каково минимальное число сравнений для нахождения минимума и максимума одновременно?»
**Ответ:** Попарное сравнение элементов требует $\approx 1.5 N$ сравнений вместо $2N$.
"""
    },
    {
        "num": 74,
        "title": "Удвоение именованного возвращаемого значения result в defer",
        "task": "Изменение именованного возврата в defer: Напишите функцию DoubleValue(x int) (result int). В теле функции присвойте result = x. Внутри defer удвойте значение result. Проверьте, какое значение вернет функция при вызове.",
        "theory": """
Мутация именованного возврата перед выходом.
""",
        "step_by_step": """
1. Пишем `DoubleValue(x int) (result int)`.
2. Регистрируем `defer func() { result *= 2 }()`.
3. Присваиваем `result = x`.
4. Проверяем удвоение.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func DoubleValue(x int) (result int) {
	defer func() {
		result *= 2 // Удваивает финальное значение перед выходом!
	}()

	result = x
	return
}

func main() {
	res := DoubleValue(21)
	fmt.Printf("DoubleValue(21) = %d (Удвоено в defer!)\n", res)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# DoubleValue(21) = 42 (Удвоено в defer!)"""
            }
        ],
        "under_the_hood": """
Модификация значения в стековом кадре перед возвратом.
""",
        "pitfalls": """
- Ожидание возврата 21 вместо 42.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что вернет функция `func F() (r int) { defer func() { r++ }(); return 1 }`?»
**Ответ:** Вернет `2`.
"""
    },
    {
        "num": 75,
        "title": "Универсальное вариативное суммирование с вызовом от списка и среза",
        "task": "Напиши функцию с variadic-параметром: Sum(nums ...int) int. Сложи все переданные числа. Вызови с разным количеством аргументов и со слайсом (через ...).",
        "theory": """
Комплексный пример вызова вариативной функции.
""",
        "step_by_step": """
1. Пишем `Sum(nums ...int) int`.
2. Вызываем с 0, 1, 3 аргументами.
3. Вызываем со срезом `s...`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Sum(nums ...int) int {
	sum := 0
	for _, v := range nums {
		sum += v
	}
	return sum
}

func main() {
	fmt.Printf("1. Без аргументов: %d\n", Sum())
	fmt.Printf("2. Три аргумента:  %d\n", Sum(10, 20, 30))

	items := []int{5, 15, 25, 35}
	fmt.Printf("3. Через срез...:  %d\n", Sum(items...))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Без аргументов: 0
# 2. Три аргумента:  60
# 3. Через срез...:  80"""
            }
        ],
        "under_the_hood": """
Оптимизация передачи аргументов в ABIInternal.
""",
        "pitfalls": """
- Забыть троеточие при передаче среза.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как передать вариативные аргументы дальше в другую вариативную функцию?»
**Ответ:** Вызвать `NextFunc(nums...)` с оператором распаковки.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 3: {len(exercises)} exercises.")
