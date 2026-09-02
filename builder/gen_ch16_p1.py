# builder/gen_ch16_p1.py
# -*- coding: utf-8 -*-

exercises = [
    {
        "num": 1,
        "title": "Обобщённая функция Min с constraints.Ordered",
        "task": r"""Обобщённая функция `Min[T constraints.Ordered](a, b T) T`. Проверьте с `int` и `float64`.""",
        "theory": r"""До Go 1.18 для поиска минимума требовалось писать отдельные функции для каждого типа данных (`minInt`, `minFloat`). С введением Type Parameters (дженериков) ограничение `cmp.Ordered` (или `constraints.Ordered`) объединяет все типы, поддерживающие операторы `<`, `<=`, `>`, `>=` (целые числа, числа с плавающей точкой и строки).

Сигнатура `func Min[T cmp.Ordered](a, b T) T` гарантирует, что оба аргумента имеют строго одинаковый тип и возвращается значение того же типа без приведений.""",
        "step_by_step": r"""1. Импортируем стандартный пакет `cmp` (Go 1.21+).
2. Объявим функцию `Min[T cmp.Ordered](a, b T) T`.
3. Внутри выполним проверку: `if a < b { return a }; return b`.
4. В `main` протестируем вызов для `int`, `float64` и `string`.
5. Убедимся, что вызов `Min(42, 17)` работает с автоматическим выводом типов (Type Inference).""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"cmp"
	"fmt"
)

// Min возвращает меньшее из двух значений любого упорядоченного типа.
func Min[T cmp.Ordered](a, b T) T {
	if a < b {
		return a
	}
	return b
}

func main() {
	fmt.Printf("Min int: %d\n", Min(42, 17))
	fmt.Printf("Min float64: %.4f\n", Min(3.1415, 2.7182))
	fmt.Printf("Min string: %s\n", Min("golang", "docker"))
}""",
                "note": "Универсальный Min для любых упорядоченных типов"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Min int: 17
# Min float64: 2.7182
# Min string: docker"""
            }
        ],
        "under_the_hood": r"""Компилятор Go использует гибридную схему: мономорфизацию для скалярных типов разного размера и GC Shape Stenciling со словарями для типов-указателей, избегая создания тяжелых `eface` интерфейсов.""",
        "pitfalls": r"""Попытка передать аргументы разных типов `Min(10, 3.14)` вызовет ошибку компиляции `mismatched types int and untyped float`.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Почему в Go не используется полная мономорфизация, как в C++?»
**Ответ:** Полная мономорфизация приводит к экспоненциальному росту бинарного файла и замедляет сборку. Go применяет GC Shape Stenciling для сохранения быстрой скорости компиляции."""
    },
    {
        "num": 2,
        "title": "Обобщённая фильтрация слайса: Filter[T any]",
        "task": r"""Обобщённая `Filter[T any](s []T, fn func(T) bool) []T`. Отфильтровать только положительные числа.""",
        "theory": r"""Параметр типа `[T any]` указывает, что функция принимает срез элементов любого типа. Ключевое слово `any` — псевдоним `interface{}`.

При реализации функции фильтрации рекомендуется предвыделять емкость `make([]T, 0, len(s))` для предотвращения лишних реаллокаций базового массива при частых вызовах `append`.""",
        "step_by_step": r"""1. Объявим сигнатуру `Filter[T any](s []T, fn func(T) bool) []T`.
2. Выделим слайс `result := make([]T, 0, len(s))`.
3. В цикле добавим элементы, удовлетворяющие предикату `fn(v)`.
4. В `main` отфильтруем срез чисел, оставив только положительные значения.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Filter[T any](s []T, fn func(T) bool) []T {
	result := make([]T, 0, len(s))
	for _, v := range s {
		if fn(v) {
			result = append(result, v)
		}
	}
	return result
}

func main() {
	numbers := []int{-10, 15, 0, -3, 42, -99, 100, 7}

	positives := Filter(numbers, func(n int) bool {
		return n > 0
	})

	fmt.Printf("Исходный срез: %v\n", numbers)
	fmt.Printf("Положительные: %v\n", positives)
}""",
                "note": "Типобезопасная фильтрация слайса"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Исходный срез: [-10 15 0 -3 42 -99 100 7]
# Положительные: [15 42 100 7]"""
            }
        ],
        "under_the_hood": r"""Функция `Filter` работает со структурой заголовка среза напрямую без промежуточных вызовов runtime-конверсий интерфейсов.""",
        "pitfalls": r"""Инициализация `var result []T` без начальной емкости вызовет ступенчатую реаллокацию массива с ростом емкости 1 -> 2 -> 4 -> 8...""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Почему в стандартный пакет slices не добавили функцию Map и Filter?»
**Ответ:** В Go стремятся минимизировать скрытые аллокации памяти в куче при цепочечных вызовах методов, поощряя явные циклы `for` или `slices.DeleteFunc`."""
    },
    {
        "num": 3,
        "title": "Универсальный вывод Print[T any]",
        "task": r"""Напиши дженерик-функцию `Print[T any](val T)`, которая просто выводит значение через `fmt.Println`. Вызови её с числом, строкой и структурой.""",
        "theory": r"""Ограничение `any` позволяет функции принимать аргумент произвольного типа, сохраняя при этом информацию о типе на этапе компиляции.""",
        "step_by_step": r"""1. Объявим структуру `User` с полями `Name string` и `Age int`.
2. Объявим функцию `Print[T any](val T)`.
3. Выведем значение и тип через `fmt.Printf`.
4. В `main` вызовем `Print` с числом, строкой и структурой `User`.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type User struct {
	Name string
	Age  int
}

func Print[T any](val T) {
	fmt.Printf("Тип: %-15T | Значение: %v\n", val, val)
}

func main() {
	Print(42)
	Print("Hello, Go Generics!")
	Print(User{Name: "Алексей", Age: 29})
}""",
                "note": "Параметризованная функция печати"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Тип: int             | Значение: 42
# Тип: string          | Значение: Hello, Go Generics!
# Тип: main.User       | Значение: {Алексей 29}"""
            }
        ],
        "under_the_hood": r"""Значение `val T` передается в функцию по регистрам/стеку без динамической упаковки до момента передачи в вариативный срез `fmt.Printf`.""",
        "pitfalls": r"""Не путайте `[T any](v T)` и `(v any)`: в первом случае компилятор знает точный тип при возврате, во втором происходит стирание типа до динамического интерфейса.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «В чем отличие any от interface{} в Go 1.18+?»
**Ответ:** Никакого отличия в рантайме нет. `any` — это встроенный type alias для `interface{}` (`type any = interface{}`)."""
    },
    {
        "num": 4,
        "title": "Обобщенная функция Max с проверкой оператора сравнения",
        "task": r"""Напиши generic-функцию `Max[T constraints.Ordered](a, b T) T`. Протестируй с `int`, `float64`, `string`. Покажи, что компилятор проверяет, что тип поддерживает оператор `<`.""",
        "theory": r"""Ограничение `cmp.Ordered` гарантирует поддержку операторов `<`, `<=`, `>`, `>=`. Попытка передать структуру или срез приведет к ошибке компиляции `T does not satisfy cmp.Ordered`.""",
        "step_by_step": r"""1. Объявим функцию `Max[T cmp.Ordered](a, b T) T`.
2. Реализуем проверку: `if a > b { return a }; return b`.
3. В `main` протестируем с `int`, `float64`, `string`.
4. В комментариях покажем ошибку сборки при передаче структуры `Point`.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"cmp"
	"fmt"
)

func Max[T cmp.Ordered](a, b T) T {
	if a > b {
		return a
	}
	return b
}

type Point struct {
	X, Y int
}

func main() {
	fmt.Println("Max(100, 200):", Max(100, 200))
	fmt.Println("Max(3.14, 2.71):", Max(3.14, 2.71))
	fmt.Println("Max(\"apple\", \"banana\"):", Max("apple", "banana"))

	// Point не скомпилируется:
	// p1, p2 := Point{1, 2}, Point{3, 4}
	// _ = Max(p1, p2) // ОШИБКА: Point does not satisfy cmp.Ordered
}""",
                "note": "Статическая проверка поддержки оператора >"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Max(100, 200): 200
# Max(3.14, 2.71): 3.14
# Max("apple", "banana"): banana"""
            }
        ],
        "under_the_hood": r"""Фаза typecheck компилятора строит Type Set для `cmp.Ordered` и сверяет тип аргументов с этим множеством на этапе компиляции.""",
        "pitfalls": r"""В Go структуры не поддерживают перегрузку операторов. К структурам нельзя применить `>`, поэтому они не удовлетворяют `cmp.Ordered`.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Почему в Go нет перегрузки операторов?»
**Ответ:** Для простоты и однозначности чтения кода. Выражение `a > b` всегда означает сравнение скалярных типов или строк без скрытых тяжелых методов или аллокаций."""
    },
    {
        "num": 5,
        "title": "Type Approximation: оператор тильды ~ для пользовательских типов",
        "task": r"""Напиши `Min[T constraints.Ordered]`. Протестируй с пользовательским типом `type Score int` — покажи, что работает благодаря **type approximation** в `constraints.Ordered`.""",
        "theory": r"""Если тип объявлен как `type Score int`, его базовый тип (underlying type) равен `int`.

Символ тильды `~int` в интерфейсе-ограничении означает: разрешить использование `int` и любых пользовательских типов, у которых базовым типом является `int`.""",
        "step_by_step": r"""1. Объявим `type Score int` и `type Temperature float64`.
2. Объявим функцию `Min[T cmp.Ordered](a, b T) T`.
3. В `main` вызовем `Min` с переменными типа `Score` и `Temperature`.
4. Убедимся, что возвращаемое значение сохраняет свой точный тип `Score`.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"cmp"
	"fmt"
)

type Score int
type Temperature float64

func Min[T cmp.Ordered](a, b T) T {
	if a < b {
		return a
	}
	return b
}

func main() {
	s1, s2 := Score(85), Score(92)
	minScore := Min(s1, s2)
	fmt.Printf("Min Score: %d (тип: %T)\n", minScore, minScore)

	t1, t2 := Temperature(36.6), Temperature(38.2)
	minTemp := Min(t1, t2)
	fmt.Printf("Min Temp: %.1f (тип: %T)\n", minTemp, minTemp)
}""",
                "note": "Type approximation для кастомных типов"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Min Score: 85 (тип: main.Score)
# Min Temp: 36.6 (тип: main.Temperature)"""
            }
        ],
        "under_the_hood": r"""Компилятор проверяет `Score.Underlying() == types.Basic(int)`, подтверждая соответствие `~int`.""",
        "pitfalls": r"""Тильду `~` можно применять только к базовым типам. Нельзя писать `~Score` или `~MyInterface`.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «В чем отличие type definition от type alias в контексте дженериков?»
**Ответ:** `type ID = int` (alias) идентичен `int` и не требует `~`. `type ID int` (definition) создает новый именованный тип, требующий `~int` в constraint."""
    },
    {
        "num": 6,
        "title": "Параметризованный Min с пакетом cmp (Go 1.21+)",
        "task": r"""Напишите параметризованную функцию `Min[T cmp.Ordered](a, b T) T` (используя пакет `cmp` из Go 1.21+), которая возвращает меньшее из двух значений.""",
        "theory": r"""Пакет `cmp` стал частью стандартной библиотеки в Go 1.21. Он предоставляет интерфейс `cmp.Ordered` и функции `cmp.Less` и `cmp.Compare`.""",
        "step_by_step": r"""1. Импортируем `"cmp"`.
2. Реализуем `Min[T cmp.Ordered](a, b T) T` через `cmp.Less(a, b)`.
3. В `main` вызовем `Min` для чисел и строк.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"cmp"
	"fmt"
)

func Min[T cmp.Ordered](a, b T) T {
	if cmp.Less(a, b) {
		return a
	}
	return b
}

func main() {
	fmt.Println("Min(10, 20) =", Min(10, 20))
	fmt.Println("Min(99.9, 12.3) =", Min(99.9, 12.3))
	fmt.Println("Min(\"Go\", \"Rust\") =", Min("Go", "Rust"))
}""",
                "note": "Стандартный пакет cmp из Go 1.21+"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Min(10, 20) = 10
# Min(99.9, 12.3) = 12.3
# Min("Go", "Rust") = Go"""
            }
        ],
        "under_the_hood": r"""`cmp.Less` корректно обрабатывает `NaN` для чисел с плавающей точкой, гарантируя строгое отношение порядка.""",
        "pitfalls": r"""Не используйте устаревший внешний пакет `golang.org/x/exp/constraints` в проектах Go 1.21+.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Как cmp.Compare обрабатывает NaN?»
**Ответ:** `cmp.Compare(NaN, x)` возвращает `-1`, а `cmp.Compare(NaN, NaN)` возвращает `0`, обеспечивая детерминированную работу алгоритмов сортировки `slices.Sort`."""
    },
    {
        "num": 7,
        "title": "Два параметра типов: Map[T, U any]",
        "task": r"""Напиши `Map[T, U any](s []T, fn func(T) U) []U`. Преобразуй `[]int` в `[]string` (числа → строки). Покажи работу с **двумя type parameters**.""",
        "theory": r"""Функции могут принимать несколько независимых параметров типов `[T, U any]`, позволяя безопасно преобразовывать коллекции сущностей.""",
        "step_by_step": r"""1. Объявим `Map[T, U any](s []T, fn func(T) U) []U`.
2. Выделим слайс `res := make([]U, len(s))`.
3. Заполним элементы `res[i] = fn(v)`.
4. В `main` преобразуем `[]int` в `[]string` и `[]string` в `[]int` (длины).""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"strconv"
)

func Map[T, U any](s []T, fn func(T) U) []U {
	result := make([]U, len(s))
	for i, v := range s {
		result[i] = fn(v)
	}
	return result
}

func main() {
	numbers := []int{10, 25, 42, 100}

	strings := Map(numbers, func(n int) string {
		return "ID-" + strconv.Itoa(n)
	})
	fmt.Printf("Числа в строки: %v (%T)\n", strings, strings)

	words := []string{"Go", "Generics", "Backend"}
	lengths := Map(words, func(w string) int {
		return len(w)
	})
	fmt.Printf("Длины слов: %v (%T)\n", lengths, lengths)
}""",
                "note": "Трансформация типов через Map"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Числа в строки: [ID-10 ID-25 ID-42 ID-100] ([]string)
# Длины слов: [2 8 7] ([]int)"""
            }
        ],
        "under_the_hood": r"""Компилятор автоматически выводит `T = int` из слайса и `U = string` из сигнатуры переданной лямбды.""",
        "pitfalls": r"""Всегда используйте `make([]U, len(s))` вместо `append`, так как длина результирующего слайса известна заранее.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Как работает Unification Algorithm при выводе нескольких параметров типа?»
**Ответ:** Компилятор сопоставляет типы аргументов с сигнатурой функции и решает систему типовых равенств. Если тип `T` выведен как `int`, а замыкание `func(int) string` возвращает `string`, то `U` однозначно разрешается в `string`."""
    },
    {
        "num": 8,
        "title": "Ограничение comparable и несравнимые типы",
        "task": r"""Напиши `Equal[T comparable](a, b T) bool`. Протестируй с `int`, `struct{Age int}`. Попробуй передать `[]int` — получи ошибку компиляции (слайс не `comparable`). Объясни.""",
        "theory": r"""Ограничение `comparable` допускает типы, для которых определены операторы `==` и `!=`. Слайсы, мапы и функции не являются `comparable`.""",
        "step_by_step": r"""1. Объявим `Equal[T comparable](a, b T) bool { return a == b }`.
2. Протестируем `Equal` с `int` и со структурой `User{ID int, Name string}`.
3. В комментариях зафиксируем ошибку компиляции при передаче `[]int`.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Equal[T comparable](a, b T) bool {
	return a == b
}

type User struct {
	ID   int
	Name string
}

func main() {
	fmt.Println("Equal(10, 10):", Equal(10, 10))
	fmt.Println("Equal(10, 20):", Equal(10, 20))

	u1 := User{ID: 1, Name: "Иван"}
	u2 := User{ID: 1, Name: "Иван"}
	u3 := User{ID: 2, Name: "Анна"}
	fmt.Println("Equal(u1, u2):", Equal(u1, u2))
	fmt.Println("Equal(u1, u3):", Equal(u1, u3))

	// Слайсы не скомпилируются:
	// s1, s2 := []int{1}, []int{1}
	// _ = Equal(s1, s2) // ОШИБКА: []int does not satisfy comparable
}""",
                "note": "Сравнение структур и чисел через comparable"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Equal(10, 10): true
# Equal(10, 20): false
# Equal(u1, u2): true
# Equal(u1, u3): false"""
            }
        ],
        "under_the_hood": r"""Оператор `==` для структур выполняет побитовое или пополевое сравнение в памяти. Для слайсов `==` запрещен спецификацией Go.""",
        "pitfalls": r"""Если структура содержит хотя бы одно поле-слайс, она автоматически перестает быть `comparable`.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Почему в Go запрещен оператор == для слайсов?»
**Ответ:** Глубокое сравнение слайсов требует $O(N)$ операций и рекурсивных проверок. Включение `==` сделало бы оператор равенства непредсказуемо тяжелым по CPU и памяти."""
    },
    {
        "num": 9,
        "title": "Ограничение constraints.Integer для целочисленной суммы",
        "task": r"""Изучите пакет `constraints`. Используйте `constraints.Integer` вместо `Ordered`, чтобы функция `Sum[T constraints.Integer]` работала только с целыми числами.""",
        "theory": r"""Интерфейс `Integer` объединяет все знаковые и беззнаковые целочисленные типы (`~int | ~int64 | ~uint32...`), исключая `float` и `string`.""",
        "step_by_step": r"""1. Объявим интерфейс `Integer`.
2. Реализуем `Sum[T Integer](nums []T) T`.
3. В `main` просуммируем `[]int` и `[]uint64`.
4. В комментариях покажем невозможность вызова с `[]float64`.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Integer interface {
	~int | ~int8 | ~int16 | ~int32 | ~int64 |
		~uint | ~uint8 | ~uint16 | ~uint32 | ~uint64 | ~uintptr
}

func Sum[T Integer](nums []T) T {
	var total T
	for _, n := range nums {
		total += n
	}
	return total
}

func main() {
	intSlice := []int{10, 20, 30, 40}
	fmt.Println("Сумма int:", Sum(intSlice))

	uintSlice := []uint64{100, 200, 300}
	fmt.Println("Сумма uint64:", Sum(uintSlice))

	// floatSlice := []float64{1.5, 2.5}
	// fmt.Println(Sum(floatSlice)) // ОШИБКА: float64 does not satisfy Integer
}""",
                "note": "Целочисленное ограничение Integer"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Сумма int: 100
# Сумма uint64: 600"""
            }
        ],
        "under_the_hood": r"""`var total T` инициализируется `0` соответствующего типа без аллокаций памяти.""",
        "pitfalls": r"""Следите за переполнением целочисленных типов (`integer overflow`).""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Почему оператор `+` разрешен внутри `Sum[T Integer]`?»
**Ответ:** Потому что бинарный оператор `+` определен для абсолютно каждого типа, входящего в union `Integer`."""
    },
    {
        "num": 10,
        "title": "any как псевдоним interface{} в generic-функциях",
        "task": r"""Напиши `Print[T any](v T)`. Покажи, что `any` — это псевдоним `interface{}`, и функция принимает любой тип.""",
        "theory": r"""`any` — это встроенный псевдоним (`type any = interface{}`). Они абсолютно взаимозаменяемы во всех контекстах языка Go.""",
        "step_by_step": r"""1. Объявим `Print[T any](v T)`.
2. Выведем значение и тип через `fmt.Printf`.
3. В `main` вызовем функцию с различными типами: `int`, `string`, `bool`, `chan int`.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Print[T any](v T) {
	fmt.Printf("Тип: %-20T | Значение: %v\n", v, v)
}

func main() {
	Print(123)
	Print("Golang 1.22")
	Print(true)
	Print(make(chan int))

	var a any = "тест"
	var b interface{} = a
	fmt.Printf("a == b: %v\n", a == b)
}""",
                "note": "Использование any в параметрах типов"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Тип: int                  | Значение: 123
# Тип: string               | Значение: Golang 1.22
# Тип: bool                 | Значение: true
# Тип: chan int             | Значение: 0x...
# a == b: true"""
            }
        ],
        "under_the_hood": r"""В AST компилятора токен `any` транслируется в дескриптор пустого интерфейса `EmptyInterface`.""",
        "pitfalls": r"""Не злоупотребляйте `any` там, где можно применить конкретный контракт.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Зачем ввели `any`?»
**Ответ:** Для лаконичности синтаксиса `[T any]` и четкого семантического разделения произвольного типа от контракта интерфейса."""
    },
    {
        "num": 11,
        "title": "Универсальный обмен значений Swap[T any]",
        "task": r"""Напиши `Swap[T any](a, b *T)`. Обменяй значения двух переменных любого типа (например, строк и чисел) одной функцией.""",
        "theory": r"""`Swap[T any](a, b *T)` компилируется в прямой обмен значений по указателям через регистры CPU без рефлексии и аллокаций.""",
        "step_by_step": r"""1. Объявим `Swap[T any](a, b *T)`.
2. Выполним `*a, *b = *b, *a`.
3. В `main` обменяем числа, строки и структуры.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Swap[T any](a, b *T) {
	*a, *b = *b, *a
}

type Coords struct {
	Lat, Lon float64
}

func main() {
	x, y := 100, 200
	Swap(&x, &y)
	fmt.Printf("Числа после Swap: x=%d, y=%d\n", x, y)

	s1, s2 := "Alpha", "Omega"
	Swap(&s1, &s2)
	fmt.Printf("Строки после Swap: s1=%s, s2=%s\n", s1, s2)

	c1 := Coords{Lat: 55.75, Lon: 37.61}
	c2 := Coords{Lat: 59.93, Lon: 30.33}
	Swap(&c1, &c2)
	fmt.Printf("Структуры: c1=%v, c2=%v\n", c1, c2)
}""",
                "note": "Универсальный Swap без рефлексии"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Числа после Swap: x=200, y=100
# Строки после Swap: s1=Omega, s2=Alpha
# Структуры: c1={59.93 30.33}, c2={55.75 37.61}"""
            }
        ],
        "under_the_hood": r"""Компилятор инлайнит `Swap`, превращая вызов в 2-3 инструкции `MOVQ` без создания стекового фрейма.""",
        "pitfalls": r"""Передавайте указатели `&x, &y`, иначе будет ошибка компиляции.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Утекают ли переменные в кучу при вызове `Swap(&a, &b)`?»
**Ответ:** Нет, если функция инлайнится и указатели не сохраняются во внешние структуры, переменные остаются на стеке."""
    },
    {
        "num": 12,
        "title": "Классическая функция Map из функционального программирования",
        "task": r"""Напишите функцию `Map[T, U any](s []T, f func(T) U) []U`, которая применяет функцию к каждому элементу слайса (классическая функция из функционального программирования).""",
        "theory": r"""Паттерн Map применяет чистую функцию к каждому элементу коллекции, создавая новый слайс без изменения исходного.""",
        "step_by_step": r"""1. Объявим `Map[T, U any](s []T, f func(T) U) []U`.
2. Выделим память `make([]U, len(s))`.
3. Заполним элементы `res[i] = f(v)`.
4. В `main` вычислим площади кругов по радиусам.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"math"
)

func Map[T, U any](s []T, f func(T) U) []U {
	if s == nil {
		return nil
	}
	res := make([]U, len(s))
	for i, v := range s {
		res[i] = f(v)
	}
	return res
}

func main() {
	radii := []float64{1.0, 2.5, 5.0, 10.0}

	areas := Map(radii, func(r float64) float64 {
		return math.Pi * r * r
	})

	for i, r := range radii {
		fmt.Printf("Радиус: %4.1f -> Площадь: %7.2f\n", r, areas[i])
	}
}""",
                "note": "Классический Map с вычислением площадей"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Радиус:  1.0 -> Площадь:    3.14
# Радиус:  2.5 -> Площадь:   19.63
# Радиус:  5.0 -> Площадь:   78.54
# Радиус: 10.0 -> Площадь:  314.16"""
            }
        ],
        "under_the_hood": r"""Выделяется ровно один блок памяти под `res` без повторных аллокаций.""",
        "pitfalls": r"""Функция `f` не должна мутировать разделяемое состояние.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Как сделать параллельный Map?»
**Ответ:** Разбить слайс на чанки по числу ядер CPU (`runtime.GOMAXPROCS`) и обработать сегменты параллельно через `sync.WaitGroup`."""
    },
    {
        "num": 13,
        "title": "Универсальная свёртка Reduce[T, U any]",
        "task": r"""Напиши `Reduce[T, U any](s []T, init U, fn func(U, T) U) U`. Реализуй через него: сумму чисел, произведение, конкатенацию строк, поиск максимума.""",
        "theory": r"""`Reduce` агрегирует элементы коллекции в единое значение с помощью начального аккумулятора `init` и функции свертки.""",
        "step_by_step": r"""1. Объявим `Reduce[T, U any](s []T, init U, fn func(U, T) U) U`.
2. Инициализируем `acc := init` и в цикле обновляем `acc = fn(acc, v)`.
3. В `main` реализуем сумму, произведение, конкатенацию и максимум.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Reduce[T, U any](s []T, init U, fn func(U, T) U) U {
	acc := init
	for _, v := range s {
		acc = fn(acc, v)
	}
	return acc
}

func main() {
	numbers := []int{1, 2, 3, 4, 5}

	sum := Reduce(numbers, 0, func(acc, n int) int { return acc + n })
	fmt.Println("Сумма:", sum)

	prod := Reduce(numbers, 1, func(acc, n int) int { return acc * n })
	fmt.Println("Произведение:", prod)

	words := []string{"Go", "is", "fast", "and", "simple"}
	sentence := Reduce(words, "", func(acc, w string) string {
		if acc == "" {
			return w
		}
		return acc + " " + w
	})
	fmt.Println("Предложение:", sentence)

	maxVal := Reduce(numbers, numbers[0], func(acc, n int) int {
		if n > acc {
			return n
		}
		return acc
	})
	fmt.Println("Максимум:", maxVal)
}""",
                "note": "Свертка Reduce для различных типов операций"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Сумма: 15
# Произведение: 120
# Предложение: Go is fast and simple
# Максимум: 5"""
            }
        ],
        "under_the_hood": r"""`Reduce` выполняется за $O(N)$ без промежуточных аллокаций слайсов.""",
        "pitfalls": r"""Неверное начальное значение (например 0 при умножении) приведет к нулевому результату.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Почему в коде Go часто предпочитают явный for вместо Reduce?»
**Ответ:** Явный `for` проще читать, легче профилировать и он позволяет компилятору эффективно выполнять автовекторизацию (SIMD)."""
    },
    {
        "num": 14,
        "title": "Поиск первого совпадения Find[T any] и нулевое значение",
        "task": r"""Напиши `Find[T any](slice []T, predicate func(T) bool) (T, bool)`. Найди первый элемент, удовлетворяющий предикату. Верни zero value и `false`, если не найден.""",
        "theory": r"""Для возврата zero value произвольного типа `T` в Go используется паттерн `var zero T; return zero, false`.""",
        "step_by_step": r"""1. Объявим `Find[T any](slice []T, predicate func(T) bool) (T, bool)`.
2. Если `predicate(v)` истинно, возвращаем `(v, true)`.
3. После цикла объявляем `var zero T` и возвращаем `(zero, false)`.
4. В `main` найдем первое четное число и число > 100.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Find[T any](slice []T, predicate func(T) bool) (T, bool) {
	for _, v := range slice {
		if predicate(v) {
			return v, true
		}
	}
	var zero T
	return zero, false
}

func main() {
	nums := []int{7, 13, 24, 35, 48}

	if val, ok := Find(nums, func(n int) bool { return n%2 == 0 }); ok {
		fmt.Printf("Найдено первое четное: %d\n", val)
	}

	if val, ok := Find(nums, func(n int) bool { return n > 100 }); ok {
		fmt.Printf("Найдено: %d\n", val)
	} else {
		fmt.Printf("Элемент > 100 не найден. Zero value: %d\n", val)
	}
}""",
                "note": "Идиоматичный возврат zero value"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Найдено первое четное: 24
# Элемент > 100 не найден. Zero value: 0"""
            }
        ],
        "under_the_hood": r"""`var zero T` зануляет область памяти размером `sizeof(T)`.""",
        "pitfalls": r"""Попытка написать `return nil, false` вызовет ошибку компиляции `cannot use nil as T value`.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Как получить нулевое значение параметризованного типа в одну строку?»
**Ответ:** Через разыменование свежевыделенного указателя `*new(T)`."""
    },
    {
        "num": 15,
        "title": "Сравнение элементов с помощью Max и cmp.Ordered",
        "task": r"""**Простейший дженерик (Сравнение)**: Напишите обобщенную функцию `Max[T cmp.Ordered](a, b T) T`, которая принимает два значения любого сравниваемого типа и возвращает наибольшее из них. Протестируйте функцию на типах `int`, `float64` и `string` (используйте пакет `cmp` из стандартной библиотеки).""",
        "theory": r"""`cmp.Ordered` гарантирует поддержку строгой операции сравнения на этапе компиляции.""",
        "step_by_step": r"""1. Напишем `Max[T cmp.Ordered](a, b T) T`.
2. В `main` вызовем для `int`, `float64`, `string`.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"cmp"
	"fmt"
)

func Max[T cmp.Ordered](a, b T) T {
	if a > b {
		return a
	}
	return b
}

func main() {
	fmt.Printf("Max int: %d\n", Max(10, 20))
	fmt.Printf("Max float: %.2f\n", Max(3.14, 2.71))
	fmt.Printf("Max string: %s\n", Max("яблоко", "груша"))
}""",
                "note": "Универсальный Max с cmp.Ordered"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Max int: 20
# Max float: 3.14
# Max string: яблоко"""
            }
        ],
        "under_the_hood": r"""Лексикографическое сравнение строк выполняется ассемблерной функцией `runtime.cmpstring`.""",
        "pitfalls": r"""Строки сравниваются побайтово (байты UTF-8). Заглавные буквы меньше строчных в таблице ASCII.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Как сортировать строки с учетом локали?»
**Ответ:** Использовать пакет `golang.org/x/text/collate`."""
    },
    {
        "num": 16,
        "title": "Первый дженерик: PrintAnything[T any] против interface{}",
        "task": r"""**Первый дженерик**: Напиши обобщенную функцию `PrintAnything[T any](val T)`, которая принимает значение любого типа и выводит его. Сравни с использованием `interface{}`.""",
        "theory": r"""`[T any]` сохраняет статический тип во время компиляции и передает значение напрямую, в то время как `interface{}` создает структуру `eface` с динамической упаковкой.""",
        "step_by_step": r"""1. Напишем `PrintGeneric[T any](val T)`.
2. Напишем `PrintInterface(val any)`.
3. Сравним в `main`.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func PrintGeneric[T any](val T) {
	fmt.Printf("[Generic]   Значение: %v | Тип: %T\n", val, val)
}

func PrintInterface(val any) {
	fmt.Printf("[Interface] Значение: %v | Тип: %T\n", val, val)
}

func main() {
	PrintGeneric(42)
	PrintInterface(42)

	PrintGeneric("Gopher")
	PrintInterface("Gopher")
}""",
                "note": "Сравнение дженерика и dynamic interface{}"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# [Generic]   Значение: 42 | Тип: int
# [Interface] Значение: 42 | Тип: int
# [Generic]   Значение: Gopher | Тип: string
# [Interface] Значение: Gopher | Тип: string"""
            }
        ],
        "under_the_hood": r"""Передача примитива в `interface{}` вызывает `runtime.convT2E`, аллоцируя память под значение.""",
        "pitfalls": r"""Внутри generic-функции вызов `fmt.Println(val)` все равно упакует аргумент в интерфейс.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Когда предпочесть `any`, а когда `[T any]`?»
**Ответ:** Дженерики `[T any]` — для типобезопасных коллекций и возврата типов. `any` — для гетерогенных слайсов и динамического парсинга JSON."""
    },
    {
        "num": 17,
        "title": "Обязательность constraint comparable в Contains",
        "task": r"""Создайте параметризованную функцию `Contains[T comparable](s []T, val T) bool`. Почему здесь обязательно нужен constraint `comparable`? Что будет, если убрать его?""",
        "theory": r"""Ограничение `any` разрешает несравнимые типы (слайсы, мапы), для которых `==` запрещен. Компилятор требует `comparable`, чтобы гарантировать поддержку `==`.""",
        "step_by_step": r"""1. Объявим `Contains[T comparable](s []T, val T) bool`.
2. В цикле сравним `v == val`.
3. В `main` проверим со строками и числами.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Contains[T comparable](s []T, val T) bool {
	for _, v := range s {
		if v == val {
			return true
		}
	}
	return false
}

func main() {
	fruits := []string{"apple", "banana", "orange"}
	fmt.Println("Contains 'banana':", Contains(fruits, "banana"))
	fmt.Println("Contains 'grape':", Contains(fruits, "grape"))

	ids := []int{101, 102, 103}
	fmt.Println("Contains 102:", Contains(ids, 102))
}""",
                "note": "Использование comparable для оператора =="
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Contains 'banana': true
# Contains 'grape': false
# Contains 102: true"""
            }
        ],
        "under_the_hood": r"""Для `comparable` компилятор подставляет инструкцию `CMPQ` или вызов `runtime.memequal`.""",
        "pitfalls": r"""Для несравнимых типов используйте предикат `ContainsFunc`.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Как разделены функции поиска в пакете slices Go 1.21+?»
**Ответ:** `slices.Contains` требует `comparable`, а `slices.ContainsFunc` принимает `any` и функцию-предикат."""
    },
    {
        "num": 18,
        "title": "Линейный поиск Contains[T comparable]",
        "task": r"""Напиши дженерик-функцию `Contains[T comparable](slice []T, target T) bool`, которая ищет элемент в слайсе. Обрати внимание на констрейнт `comparable` (допускает только сравнимые типы).""",
        "theory": r"""Линейный поиск в слайсе работает со структурами, числами, строками и указателями.""",
        "step_by_step": r"""1. Объявим структуру `Task{ID int, Done bool}`.
2. Реализуем `Contains[T comparable](slice []T, target T) bool`.
3. В `main` выполним поиск структуры `Task`.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Task struct {
	ID   int
	Done bool
}

func Contains[T comparable](slice []T, target T) bool {
	for _, item := range slice {
		if item == target {
			return true
		}
	}
	return false
}

func main() {
	tasks := []Task{
		{ID: 1, Done: true},
		{ID: 2, Done: false},
	}

	search1 := Task{ID: 1, Done: true}
	search2 := Task{ID: 3, Done: false}

	fmt.Println("Поиск задачи 1:", Contains(tasks, search1))
	fmt.Println("Поиск задачи 3:", Contains(tasks, search2))
}""",
                "note": "Поиск структур через comparable"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Поиск задачи 1: true
# Поиск задачи 3: false"""
            }
        ],
        "under_the_hood": r"""Сравнение структуры без паддингов выполняется побайтово.""",
        "pitfalls": r"""Если структура содержит указатели, сравниваются адреса памяти, а не значения объектов.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Почему линейный поиск в слайсе иногда быстрее map lookup?»
**Ответ:** Благодаря кэшам процессора (L1/L2 data cache) и непрерывной раскладке слайса в памяти."""
    },
    {
        "num": 19,
        "title": "Ограничение comparable: глубокий разбор сравнимых и несравнимых типов",
        "task": r"""**Ограничение `comparable`**: Напишите обобщенную функцию `IsEqual[T comparable](a, b T) bool`, проверяющую равенство двух элементов. Объясните, какие типы данных удовлетворяют ограничению `comparable` (а какие — нет, например, слайсы и мапы).""",
        "theory": r"""Сравнимы: числа, строки, булевы флаги, указатели, каналы, массивы `[N]T`, структуры из comparable полей. Не сравнимы: слайсы, мапы, функции.""",
        "step_by_step": r"""1. Напишем `IsEqual[T comparable](a, b T) bool`.
2. Проверим массивы `[3]int` и указатели.
3. В комментариях зафиксируем запрет на слайсы.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func IsEqual[T comparable](a, b T) bool {
	return a == b
}

func main() {
	arr1 := [3]int{1, 2, 3}
	arr2 := [3]int{1, 2, 3}
	arr3 := [3]int{1, 2, 4}
	fmt.Println("arr1 == arr2:", IsEqual(arr1, arr2))
	fmt.Println("arr1 == arr3:", IsEqual(arr1, arr3))

	x, y := 10, 10
	fmt.Println("&x == &x:", IsEqual(&x, &x))
	fmt.Println("&x == &y:", IsEqual(&x, &y))

	// s1, s2 := []int{1}, []int{1}
	// _ = IsEqual(s1, s2) // ОШИБКА: []int does not satisfy comparable
}""",
                "note": "Сравнение массивов и указателей"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# arr1 == arr2: true
# arr1 == arr3: false
# &x == &x: true
# &x == &y: false"""
            }
        ],
        "under_the_hood": r"""Для массивов `[N]T` вызывается `runtime.memequal` размером `N * sizeof(T)`.""",
        "pitfalls": r"""Сравнение интерфейсов с динамическим слайсом приведет к runtime panic.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Почему слайсы и мапы нельзя использовать в качестве ключей map?»
**Ответ:** Ключ мапы обязан быть иммутабельным и поддерживать `==`. Мутация слайса после вставки сломала бы внутреннюю структуру хэш-таблицы."""
    },
    {
        "num": 20,
        "title": "Иммутабельный разворот слайса Reverse[T any]",
        "task": r"""Напиши `Reverse[T any](s []T) []T`. Верни **новый** слайс в обратном порядке (не меняя оригинал).""",
        "theory": r"""Иммутабельный разворот создает новый массив в памяти, гарантируя отсутствие побочных эффектов.""",
        "step_by_step": r"""1. Объявим `Reverse[T any](s []T) []T`.
2. Выделим `res := make([]T, len(s))`.
3. Заполним `res[n - 1 - i] = s[i]`.
4. В `main` развернем срез строк.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Reverse[T any](s []T) []T {
	n := len(s)
	res := make([]T, n)
	for i, v := range s {
		res[n-1-i] = v
	}
	return res
}

func main() {
	original := []string{"первый", "второй", "третий", "четвертый"}
	reversed := Reverse(original)

	fmt.Println("Оригинал:  ", original)
	fmt.Println("Развернутый:", reversed)
}""",
                "note": "Иммутабельный разворот слайса"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Оригинал:   [первый второй третий четвертый]
# Развернутый: [четвертый третий второй первый]"""
            }
        ],
        "under_the_hood": r"""Новый слайс получает независимый базовый массив в памяти кучи.""",
        "pitfalls": r"""Для экономии памяти используйте in-place разворот `slices.Reverse`.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Когда предпочесть иммутабельный Reverse, а когда in-place slices.Reverse?»
**Ответ:** Иммутабельный — при многопоточном доступе без мьютексов. In-place — в высоконагруженных циклах для исключения аллокаций памяти."""
    },
    {
        "num": 21,
        "title": "Ограничение с тильдой: интерфейс Number и функция Sum",
        "task": r"""Ограничение с тильдой: интерфейс `Number` (`~int | ~float64`). Функция `Sum[T Number](nums []T) T`, вычисляющая сумму.""",
        "theory": r"""Объединение типов с тильдой `~int | ~float64` разрешает базовые и производные типы.""",
        "step_by_step": r"""1. Объявим `type Number interface { ~int | ~float64 }`.
2. Объявим `type Meters int` и `type Weight float64`.
3. Реализуем `Sum[T Number](nums []T) T`.
4. В `main` просуммируем `[]Meters` и `[]Weight`.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Number interface {
	~int | ~float64
}

type Meters int
type Weight float64

func Sum[T Number](nums []T) T {
	var total T
	for _, n := range nums {
		total += n
	}
	return total
}

func main() {
	ints := []int{1, 2, 3, 4, 5}
	fmt.Printf("Sum ints: %d (%T)\n", Sum(ints), Sum(ints))

	meters := []Meters{10, 20, 30}
	fmt.Printf("Sum meters: %d (%T)\n", Sum(meters), Sum(meters))

	weights := []Weight{75.5, 82.3}
	fmt.Printf("Sum weights: %.1f (%T)\n", Sum(weights), Sum(weights))
}""",
                "note": "Суммирование с type approximation"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Sum ints: 15 (int)
# Sum meters: 60 (main.Meters)
# Sum weights: 157.8 (main.Weight)"""
            }
        ],
        "under_the_hood": r"""Компилятор создает специализированные версии функций под аппаратные регистры `RAX` и `XMM0`.""",
        "pitfalls": r"""В `Number` нельзя использовать операторы, отсутствующие у одного из типов (например `%` для float64).""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Можно ли объявить переменную var x Number = 5?»
**Ответ:** Нет. Интерфейсы с Type Elements могут использоваться исключительно как generic constraints, но не как динамические типы переменных."""
    },
    {
        "num": 22,
        "title": "Линейный поиск в структурах и строках",
        "task": r"""Напиши `Contains[T comparable](slice []T, item T) bool`. Реализуй линейный поиск. Протестируй с `[]string` и `[]struct{ X, Y int }`.""",
        "theory": r"""Структуры с comparable полями поддерживают оператор `==` автоматически.""",
        "step_by_step": r"""1. Объявим `type Point struct{ X, Y int }`.
2. Реализуем `Contains[T comparable](slice []T, item T) bool`.
3. Проверим поиск в `[]Point` и `[]string`.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Point struct {
	X, Y int
}

func Contains[T comparable](slice []T, item T) bool {
	for _, v := range slice {
		if v == item {
			return true
		}
	}
	return false
}

func main() {
	tags := []string{"backend", "golang", "k8s"}
	fmt.Println("Contains 'golang':", Contains(tags, "golang"))

	points := []Point{
		{X: 0, Y: 0},
		{X: 10, Y: 20},
	}
	target := Point{X: 10, Y: 20}
	fmt.Println("Contains target Point:", Contains(points, target))
}""",
                "note": "Поиск по структурам и строкам"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Contains 'golang': true
# Contains target Point: true"""
            }
        ],
        "under_the_hood": r"""Сравнение структуры размером 16 байт выполняется за 2 машинные инструкции.""",
        "pitfalls": r"""Добавление поля `[]string` лишит структуру статуса `comparable`.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Как выравнивание полей структуры влияет на оператор ==?»
**Ответ:** При наличии байтов паддинга компилятор сравнивает поля структуры по отдельности, чтобы избежать ложных несовпадений из-за мусора в паддингах."""
    },
    {
        "num": 23,
        "title": "Поиск индекса элемента: IndexOf[T comparable]",
        "task": r"""Напиши `IndexOf[T comparable](s []T, item T) int`. Верни индекс или `-1`. Покажи, почему `T` должен быть `comparable` (нужен `==`).""",
        "theory": r"""`IndexOf` возвращает индекс первого совпадения или `-1`.""",
        "step_by_step": r"""1. Объявим `IndexOf[T comparable](s []T, item T) int`.
2. Пройдемся циклом `for i, v := range s`.
3. В `main` найдем индекс элемента в срезе строк и срезе чисел.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func IndexOf[T comparable](s []T, item T) int {
	for i, v := range s {
		if v == item {
			return i
		}
	}
	return -1
}

func main() {
	languages := []string{"C++", "Java", "Go", "Python", "Rust"}
	fmt.Println("Индекс 'Go':", IndexOf(languages, "Go"))
	fmt.Println("Индекс 'Kotlin':", IndexOf(languages, "Kotlin"))

	nums := []int{100, 200, 300}
	fmt.Println("Индекс 200:", IndexOf(nums, 200))
}""",
                "note": "Поиск индекса элемента"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Индекс 'Go': 2
# Индекс 'Kotlin': -1
# Индекс 200: 1"""
            }
        ],
        "under_the_hood": r"""В Go 1.21+ аналогичная функция `slices.Index` оптимизирована векторными инструкциями.""",
        "pitfalls": r"""Не возвращайте 0 при отсутствии элемента, стандарт Go — `-1`.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Почему в Go нет методов вроде slice.indexOf()?»
**Ответ:** Для сохранения простоты и минимализма срезов. Все операции вынесены в стандартный обобщенный пакет `slices`."""
    },
    {
        "num": 24,
        "title": "Кастомный constraint и концепция aliased/defined types",
        "task": r"""Создайте свой кастомный constraint. Например, `type Number interface { ~int | ~float64 }`. Объясните, зачем нужен символ тильды `~` (tilde) и как он разрешает использование кастомных типов (aliased types).""",
        "theory": r"""`~T` разрешает любые типы, чей underlying type совпадает с `T`.""",
        "step_by_step": r"""1. Объявим `type Number interface { ~int | ~float64 }`.
2. Объявим `type Port int` и `type Percentage float64`.
3. Напишем `Double[T Number](val T) T { return val * 2 }`.
4. В `main` вызовем `Double` для кастомных типов.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Number interface {
	~int | ~float64
}

type Port int
type Percentage float64

func Double[T Number](val T) T {
	return val * 2
}

func main() {
	var p Port = 8080
	var pct Percentage = 49.5

	fmt.Printf("Doubled Port: %d (тип %T)\n", Double(p), Double(p))
	fmt.Printf("Doubled Percentage: %.1f (тип %T)\n", Double(pct), Double(pct))
}""",
                "note": "Поддержка пользовательских типов через ~"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Doubled Port: 16160 (тип main.Port)
# Doubled Percentage: 99.0 (тип main.Percentage)"""
            }
        ],
        "under_the_hood": r"""Компилятор вызывает `types.Type.Underlying()` для сверки базового типа.""",
        "pitfalls": r"""Без тильды кастомные типы вызовут ошибку `does not satisfy Number`.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Можно ли написать ~MyStruct?»
**Ответ:** Да, если `MyStruct` — конкретная структура, а не интерфейс."""
    },
    {
        "num": 25,
        "title": "Inline constraint: объединение типов прямо в сигнатуре",
        "task": r"""Напиши дженерик-функцию `Sum[T int | float64](slice []T) T`, которая суммирует числа. Используй inline constraint (объединение типов прямо в сигнатуре).""",
        "theory": r"""Inline constraint позволяет объединять типы прямо в объявлении функции `[T int | float64]`.""",
        "step_by_step": r"""1. Объявим `Sum[T int | float64](slice []T) T`.
2. Сложим элементы в цикле.
3. В `main` проверим `[]int` и `[]float64`.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Sum[T int | float64](slice []T) T {
	var total T
	for _, v := range slice {
		total += v
	}
	return total
}

func main() {
	intSum := Sum([]int{10, 20, 30})
	floatSum := Sum([]float64{1.5, 2.5, 3.5})

	fmt.Printf("Int Sum: %d\n", intSum)
	fmt.Printf("Float Sum: %.2f\n", floatSum)
}""",
                "note": "Inline constraints"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Int Sum: 60
# Float Sum: 7.50"""
            }
        ],
        "under_the_hood": r"""Парсер преобразует `[T int | float64]` в анонимный интерфейс.""",
        "pitfalls": r"""Inline constraint без `~` не примет `type MyInt int`.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Когда писать inline constraint?»
**Ответ:** Для простых однократных функций из 2-3 типов. Для переиспользуемых ограничений объявляют именованный интерфейс."""
    },
    {
        "num": 26,
        "title": "Обобщенный фильтр Filter: четные числа и длинные строки",
        "task": r"""**Обобщенный фильтр (Filter)**: Напишите функцию `Filter[T any](slice []T, predicate func(T) bool) []T`. Функция должна возвращать новый срез, содержащий только элементы, для которых функция `predicate` вернула `true`. Протестируйте на срезе чисел (фильтрация четных) и срезе строк (фильтрация строк длиннее 5 символов).""",
        "theory": r"""`Filter` возвращает строго типизированный срез элементов, прошедших предикат.""",
        "step_by_step": r"""1. Реализуем `Filter[T any](slice []T, predicate func(T) bool) []T`.
2. В `main` отфильтруем четные числа и строки длиннее 5 символов.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Filter[T any](slice []T, predicate func(T) bool) []T {
	res := make([]T, 0, len(slice))
	for _, item := range slice {
		if predicate(item) {
			res = append(res, item)
		}
	}
	return res
}

func main() {
	nums := []int{1, 2, 3, 4, 5, 6, 7, 8}
	evens := Filter(nums, func(n int) bool { return n%2 == 0 })
	fmt.Println("Четные числа:", evens)

	words := []string{"Go", "Kubernetes", "Docker", "Git"}
	longWords := Filter(words, func(w string) bool { return len(w) > 5 })
	fmt.Println("Длинные слова:", longWords)
}""",
                "note": "Практический Filter"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Четные числа: [2 4 6 8]
# Длинные слова: [Kubernetes Docker]"""
            }
        ],
        "under_the_hood": r"""`make([]T, 0, len(slice))` предотвращает множественные реаллокации памяти.""",
        "pitfalls": r"""Используйте `slices.Clip` для освобождения избыточной емкости, если отфильтровано мало элементов.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Что делает slices.Clip?»
**Ответ:** Уменьшает емкость среза до текущей длины (`cap = len`), позволяя освободить неиспользуемую память."""
    },
    {
        "num": 27,
        "title": "Эксперимент с ~: точный тип против базового типа",
        "task": r"""Создай `type MyInt int`. Покажи, что `Sum[MyInt]` работает только если constraint содержит `~int`, а не просто `int`. Без `~` — ошибка компиляции. Объясни разницу.""",
        "theory": r"""`int` требует точного совпадения типа, а `~int` принимает любые производные типы с underlying type `int`.""",
        "step_by_step": r"""1. Объявим `type MyInt int`.
2. Объявим `StrictInt interface { int }` и `ApproxInt interface { ~int }`.
3. Покажем, что `SumApprox` работает с `MyInt`, а `SumStrict` требует строгий `int`.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type MyInt int

type StrictInt interface {
	int
}

type ApproxInt interface {
	~int
}

func SumStrict[T StrictInt](a, b T) T { return a + b }
func SumApprox[T ApproxInt](a, b T) T { return a + b }

func main() {
	var n int = 10
	var c MyInt = 20

	fmt.Println("SumStrict(int):", SumStrict(n, 20))
	fmt.Println("SumApprox(MyInt):", SumApprox(c, 30))

	// fmt.Println(SumStrict(c, 30)) // ОШИБКА: MyInt does not satisfy StrictInt
}""",
                "note": "Сравнение строгого типа и type approximation"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# SumStrict(int): 30
# SumApprox(MyInt): 50"""
            }
        ],
        "under_the_hood": r"""`StrictInt` проверяет `types.Identical(T, int)`, а `ApproxInt` проверяет `types.Identical(T.Underlying(), int)`.""",
        "pitfalls": r"""Не забывайте, что литерал константы `30` автоматически приводится к `MyInt`.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Почему в Go не сделали поведение ~int по умолчанию?»
**Ответ:** Для строгого контроля в системных библиотеках и FFI cgo, где несовпадение конкретных типов недопустимо."""
    },
    {
        "num": 28,
        "title": "Ошибки типов компилятора в ограничениях",
        "task": r"""**Использование стандартных ограничений**: Напишите обобщенную функцию `Sum[T int | float64](a, b T) T`. Попробуйте передать туда строки и зафиксируйте ошибку компиляции.""",
        "theory": r"""Компилятор Go статически гарантирует соблюдение ограничений, выдавая ошибку при попытке передать несовместимый тип.""",
        "step_by_step": r"""1. Объявим `Sum[T int | float64](a, b T) T { return a + b }`.
2. В `main` вызовем с числами.
3. В комментариях покажем текст ошибки компилятора для строк.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Sum[T int | float64](a, b T) T {
	return a + b
}

func main() {
	fmt.Println("Sum(10, 20) =", Sum(10, 20))
	fmt.Println("Sum(1.2, 3.4) =", Sum(1.2, 3.4))

	// res := Sum("hello", "world")
	// Ошибка: string does not satisfy int | float64
}""",
                "note": "Статическая проверка ограничений"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Sum(10, 20) = 30
# Sum(1.2, 3.4) = 4.6"""
            }
        ],
        "under_the_hood": r"""Проверка выполняется фазой `typecheck` без затрат в рантайме.""",
        "pitfalls": r"""Для поддержки строк добавьте `string` в constraint.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Влияют ли проверки ограничений на скорость работы скомпилированной программы?»
**Ответ:** Нет, проверки происходят исключительно во время компиляции."""
    },
    {
        "num": 29,
        "title": "Обобщенная структура Stack[T any] (LIFO)",
        "task": r"""**Обобщенный Стек (Generic Struct)**: Напиши структуру `Stack[T any]`, представляющую LIFO стек. Внутри храни данные в слайсе `[]T`. Напиши методы `Push(val T)` и `Pop() (T, error)`.""",
        "theory": r"""Структуры с параметрами типов `type Stack[T any]` позволяют создавать типобезопасные коллекции данных.""",
        "step_by_step": r"""1. Объявим `Stack[T any] struct { items []T }`.
2. Реализуем `Push(val T)` и `Pop() (T, error)`.
3. В `main` протестируем со стеком чисел и стеком строк.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"errors"
	"fmt"
)

type Stack[T any] struct {
	items []T
}

func (s *Stack[T]) Push(val T) {
	s.items = append(s.items, val)
}

func (s *Stack[T]) Pop() (T, error) {
	if len(s.items) == 0 {
		var zero T
		return zero, errors.New("стек пуст")
	}
	lastIdx := len(s.items) - 1
	val := s.items[lastIdx]
	s.items = s.items[:lastIdx]
	return val, nil
}

func (s *Stack[T]) Len() int {
	return len(s.items)
}

func main() {
	intStack := &Stack[int]{}
	intStack.Push(10)
	intStack.Push(20)

	v, _ := intStack.Pop()
	fmt.Println("Pop int:", v)

	strStack := &Stack[string]{}
	strStack.Push("Alpha")
	vStr, _ := strStack.Pop()
	fmt.Println("Pop string:", vStr)
}""",
                "note": "Generic стек на базе слайса"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Pop int: 20
# Pop string: Alpha"""
            }
        ],
        "under_the_hood": r"""Срезка `s.items[:lastIdx]` сохраняет емкость слайса для повторных вставок.""",
        "pitfalls": r"""При хранении указателей зануляйте удаляемую ячейку `s.items[lastIdx] = nil` во избежание утечек памяти.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Почему важно занулять ячейку при удалении указателя из слайса?»
**Ответ:** Потому что базовый массив слайса сохраняет ссылку на объект в куче, препятствуя его сборке мусором."""
    },
    {
        "num": 30,
        "title": "In-place разворот слайса Reverse[T any]",
        "task": r"""Напишите параметризованную функцию `Reverse[T any](s []T) []T`, которая разворачивает слайс любого типа in-place.""",
        "theory": r"""In-place разворот выполняется за $O(N/2)$ шагов с $O(1)$ памяти через перестановку симметричных элементов.""",
        "step_by_step": r"""1. Объявим `ReverseInPlace[T any](s []T) []T`.
2. Запустим цикл с двумя индексами `i` и `j`.
3. В `main` развернем срез чисел и строк.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func ReverseInPlace[T any](s []T) []T {
	for i, j := 0, len(s)-1; i < j; i, j = i+1, j-1 {
		s[i], s[j] = s[j], s[i]
	}
	return s
}

func main() {
	nums := []int{1, 2, 3, 4, 5}
	ReverseInPlace(nums)
	fmt.Println("Развернутые числа:", nums)

	words := []string{"Go", "is", "fast"}
	ReverseInPlace(words)
	fmt.Println("Развернутые строки:", words)
}""",
                "note": "Разворот in-place без аллокаций"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Развернутые числа: [5 4 3 2 1]
# Развернутые строки: [fast is Go]"""
            }
        ],
        "under_the_hood": r"""In-place разворот не выделяет память в куче (0 allocations).""",
        "pitfalls": r"""Функция меняет оригинальный массив, что может вызвать побочные эффекты при совместном доступе.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Какова сложность slices.Reverse?»
**Ответ:** Время $O(N)$, память $O(1)$."""
    },
    {
        "num": 31,
        "title": "Побитовые операции и ограничение Integer",
        "task": r"""Создай constraint `Integer` с `~int | ~int8 | ... | ~uint64` (без float). Используй для generic-функции битовых операций: `BitwiseAnd[T Integer](a, b T) T`.""",
        "theory": r"""Побитовые операции определены только для целочисленных типов языка Go.""",
        "step_by_step": r"""1. Объявим `Integer interface { ~int | ... | ~uint64 }`.
2. Напишем `BitwiseAnd` и `BitwiseOr`.
3. В `main` проверим битовые флаги прав доступа.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Integer interface {
	~int | ~int8 | ~int16 | ~int32 | ~int64 |
		~uint | ~uint8 | ~uint16 | ~uint32 | ~uint64 | ~uintptr
}

func BitwiseAnd[T Integer](a, b T) T { return a & b }
func BitwiseOr[T Integer](a, b T) T  { return a | b }

const (
	ReadPermission  = 1 << 0
	WritePermission = 1 << 1
	ExecPermission  = 1 << 2
)

func main() {
	perms := BitwiseOr(ReadPermission, WritePermission)
	fmt.Printf("Права: %03b\n", perms)

	fmt.Println("Чтение:", BitwiseAnd(perms, ReadPermission) != 0)
	fmt.Println("Выполнение:", BitwiseAnd(perms, ExecPermission) != 0)
}""",
                "note": "Побитовые операции с ограничением Integer"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Права: 011
# Чтение: true
# Выполнение: false"""
            }
        ],
        "under_the_hood": r"""Компилируется в ассемблерную инструкцию `ANDQ` процессора.""",
        "pitfalls": r"""Правый операнд сдвигов обязан быть `uint` или нетипизированной константой.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Что делает оператор &^ в Go?»
**Ответ:** `x &^ y` (AND NOT) очищает биты: сбрасывает в `0` те биты `x`, которые установлены в `1` в `y`."""
    },
    {
        "num": 32,
        "title": "Union Type: кастомное ограничение Number",
        "task": r"""**Кастомное ограничение (Union Type)**: Создай интерфейс `Number`, который разрешает только типы `int`, `int64` и `float64` (`type Number interface { int | int64 | float64 }`). Напиши функцию `Sum[T Number](a, b T) T`.""",
        "theory": r"""Union Type формирует замкнутое множество типов, для которых компилируется функция.""",
        "step_by_step": r"""1. Объявим `type Number interface { int | int64 | float64 }`.
2. Реализуем `Sum[T Number](a, b T) T { return a + b }`.
3. В `main` вызовем с каждым из типов.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Number interface {
	int | int64 | float64
}

func Sum[T Number](a, b T) T {
	return a + b
}

func main() {
	var a int = 10
	var b int64 = 100
	var c float64 = 3.14

	fmt.Println("Sum int:", Sum(a, 20))
	fmt.Println("Sum int64:", Sum(b, 200))
	fmt.Println("Sum float64:", Sum(c, 2.71))
}""",
                "note": "Union Type ограничение"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Sum int: 30
# Sum int64: 300
# Sum float64: 5.85"""
            }
        ],
        "under_the_hood": r"""Создаются специализированные копии функции под каждый размер типа.""",
        "pitfalls": r"""Без `~` производные типы не будут удовлетворять интерфейсу.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Можно ли в Union интерфейс добавить методы?»
**Ответ:** Да. Тогда тип обязан входить в объединение типов **И** реализовывать указанные методы."""
    },
    {
        "num": 33,
        "title": "Ограничение Set[T comparable] и проверка несравнимости []byte",
        "task": r"""Используй `comparable` constraint: создай generic `Set[T comparable]` (реализация позже). Покажи, что можно использовать `struct` с comparable полями как элемент, но **нельзя** `[]byte` (слайс не comparable).""",
        "theory": r"""Множество `Set` на базе `map[T]struct{}` требует, чтобы тип `T` был `comparable`. Слайс `[]byte` не может быть ключом мапы.""",
        "step_by_step": r"""1. Объявим `Set[T comparable] struct { items map[T]struct{} }`.
2. Реализуем `Add` и `Contains`.
3. В `main` проверим `Set[string]` и `Set[struct{UUID string}]`.
4. В комментариях зафиксируем ошибку для `Set[[]byte]`.""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Set[T comparable] struct {
	items map[T]struct{}
}

func NewSet[T comparable]() *Set[T] {
	return &Set[T]{items: make(map[T]struct{})}
}

func (s *Set[T]) Add(val T) {
	s.items[val] = struct{}{}
}

func (s *Set[T]) Contains(val T) bool {
	_, exists := s.items[val]
	return exists
}

type UserID struct {
	UUID string
}

func main() {
	strSet := NewSet[string]()
	strSet.Add("admin")
	fmt.Println("Contains 'admin':", strSet.Contains("admin"))

	userSet := NewSet[UserID]()
	userSet.Add(UserID{UUID: "usr-101"})
	fmt.Println("Contains usr-101:", userSet.Contains(UserID{UUID: "usr-101"}))

	// byteSet := NewSet[[]byte]() // ОШИБКА: []byte does not satisfy comparable
}""",
                "note": "Generic Set с comparable"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вывод:
# Contains 'admin': true
# Contains usr-101: true"""
            }
        ],
        "under_the_hood": r"""`struct{}` занимает 0 байт памяти в значениях мапы.""",
        "pitfalls": r"""Для бинарных данных приводите `[]byte` к `string` или массиву `[32]byte`.""",
        "bigtech_interview": r"""**Вопрос с собеседования:** «Почему поиск по m[string(bytes)] в Go оптимизирован?»
**Ответ:** Компилятор использует `runtime.mapaccess2_faststr`, не аллоцируя строку в куче при поиске по мапе."""
    }
]
