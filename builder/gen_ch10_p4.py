# Chapter 10 Part 4: Exercises 76 to 100

exercises = [
    {
        "num": 76,
        "title": "Базовый defer: гарантия завершения в конце main",
        "task": "Базовый defer: Поставь defer fmt.Println(\"Конец\") в начале main. Убедись, что вывод происходит перед самым выходом из функции.",
        "theory": """
Иллюстрация порядка исполнения defer в главной функции программы.
""",
        "step_by_step": """
1. В первой строке `main()` объявляем `defer fmt.Println("Конец")`.
2. Печатаем тело программы.
3. Проверяем порядок.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	defer fmt.Println("Конец (выполнено через defer перед завершением main)")

	fmt.Println("Начало выполнения main")
	fmt.Println("Выполнение основных операций...")
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Начало выполнения main
# Выполнение основных операций...
# Конец (выполнено через defer перед завершением main)"""
            }
        ],
        "under_the_hood": """
Регистрация вызова в структуре горутины.
""",
        "pitfalls": """
- Вызов `os.Exit()` предотвратит выполнение `defer`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова стоимость одного вызова `defer` в современных версиях Go (1.14+)?»
**Ответ:** Практически 0 нс (Open-coded defer инлайнится компилятором напрямую в код выхода из функции).
"""
    },
    {
        "num": 77,
        "title": "Пользовательский функциональный тип type MathFunc func(int, int) int",
        "task": "Определи тип функции: type MathFunc func(int, int) int. Используй этот тип в качестве аргумента для другой функции.",
        "theory": """
**Именованные функциональные типы (Function Types):**
- Синтаксис: `type MathFunc func(int, int) int`;
- Повышает читаемость сигнатур функций высшего порядка;
- Позволяет определять методы прямо на типах функций!
""",
        "step_by_step": """
1. Объявляем `type MathFunc func(int, int) int`.
2. Пишем `Compute(a, b int, op MathFunc) int`.
3. Передаем сложение и вычитание.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type MathFunc func(int, int) int

func Compute(a, b int, op MathFunc) int {
	return op(a, b)
}

func main() {
	add := MathFunc(func(a, b int) int { return a + b })
	sub := MathFunc(func(a, b int) int { return a - b })

	fmt.Printf("Compute(10, 5, add): %d\n", Compute(10, 5, add))
	fmt.Printf("Compute(10, 5, sub): %d\n", Compute(10, 5, sub))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Compute(10, 5, add): 15
# Compute(10, 5, sub): 5"""
            }
        ],
        "under_the_hood": """
Тип проверяется статически во время компиляции.
""",
        "pitfalls": """
- Передача функции с другой сигнатурой `func(int64, int64) int64`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в стандартном пакете `net/http` определен тип `http.HandlerFunc`?»
**Ответ:** `type HandlerFunc func(ResponseWriter, *Request)`, и на этом типе реализован метод `ServeHTTP(w, r) { f(w, r) }`.
"""
    },
    {
        "num": 78,
        "title": "Рекурсивное вычисление n-го числа Фибоначчи и глубина стека вызовов",
        "task": "Рекурсия: Напишите рекурсивную функцию для нахождения n-го числа Фибоначчи.",
        "theory": """
Классическая рекурсивная модель дерева вычислений $F(n) = F(n-1) + F(n-2)$.
""",
        "step_by_step": """
1. Пишем `FibRecursive(n int) int`.
2. Базовый случай `if n <= 1 { return n }`.
3. Вычисляем значения для $n = 0..10$.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func FibRecursive(n int) int {
	if n <= 1 {
		return n
	}
	return FibRecursive(n-1) + FibRecursive(n-2)
}

func main() {
	for i := 0; i <= 8; i++ {
		fmt.Printf("F(%d) = %d\n", i, FibRecursive(i))
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# F(0) = 0
# F(1) = 1
# F(2) = 1
# F(3) = 2
# F(4) = 3
# F(5) = 5
# F(6) = 8
# F(7) = 13
# F(8) = 21"""
            }
        ],
        "under_the_hood": """
Дерево рекурсивных вызовов растет как $O(2^N)$.
""",
        "pitfalls": """
- Вызов `FibRecursive(50)`: программа зависнет на несколько минут из-за триллионов рекурсивных вызовов.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова асимптотическая сложность наивной рекурсии Фибоначчи?»
**Ответ:** Временная $O(2^N)$ (точнее $O(1.618^N)$ — золотое сечение), пространственная $O(N)$ (глубина стека).
"""
    },
    {
        "num": 79,
        "title": "Вариативное форматирование PrintAll(format string, args ...any) через fmt.Sprintf",
        "task": "Напиши функцию PrintAll(format string, args ...interface{}), которая форматирует и выводит аргументы. Используй fmt.Sprintf внутри.",
        "theory": """
Создание собственных функций форматирования по шаблону.
""",
        "step_by_step": """
1. Пишем `PrintAll(format string, args ...any)`.
2. Вызываем `msg := fmt.Sprintf(format, args...)`.
3. Печатаем результат.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func PrintAll(format string, args ...any) {
	formattedMessage := fmt.Sprintf(format, args...)
	fmt.Print(formattedMessage)
}

func main() {
	PrintAll("Пользователь: %s | Баланс: %.2f руб. | ID: %d\n", "Анна", 1450.50, 42)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Пользователь: Анна | Баланс: 1450.50 руб. | ID: 42"""
            }
        ],
        "under_the_hood": """
Распаковка среза `args...` передает интерфейсные заголовки в парсер спецификаторов `fmt`.
""",
        "pitfalls": """
- Несовпадение количества спецификаторов `%s` и переданных аргументов (предупреждение `go vet`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как пометить функцию для линтера `go vet`, чтобы он проверял форматные строки `printf`?»
**Ответ:** Добавить директиву компилятора или использовать имя, оканчивающееся на `f` (например `Printf`, `Logf`), либо зарегистрировать функцию в `vet`.
"""
    },
    {
        "num": 80,
        "title": "Замер времени выполнения функции через defer и time.Since(): паттерн TrackDuration()",
        "task": "Замер времени выполнения: Напишите функцию SlowWorker(), которая засыпает на 100 миллисекунд (time.Sleep). С помощью связки defer и функции time.Now() / time.Since() сделайте автоматический замер и вывод времени её работы при завершении.",
        "theory": """
**Идиоматичный паттерн профилирования времени через `defer`:**
- Синтаксис: `defer func(start time.Time) { fmt.Printf("Заняло: %v\n", time.Since(start)) }(time.Now())`;
- `time.Now()` вычисляется **сразу при входе в функцию**;
- `time.Since(start)` вычисляется **при выходе из функции**.
""",
        "step_by_step": """
1. Пишем `SlowWorker()`.
2. Регистрируем `defer func(start time.Time) { ... }(time.Now())`.
3. Имитируем работу через `time.Sleep(100 * time.Millisecond)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"time"
)

func SlowWorker() {
	// time.Now() вычисляется немедленно, передается аргументом в анонимную функцию,
	// а time.Since() замеряет дельту в момент завершения SlowWorker!
	defer func(start time.Time) {
		fmt.Printf("⏱️ SlowWorker завершен за %v\n", time.Since(start))
	}(time.Now())

	fmt.Println("Выполнение тяжелой фоновой задачи...")
	time.Sleep(100 * time.Millisecond)
}

func main() {
	SlowWorker()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Выполнение тяжелой фоновой задачи...
# ⏱️ SlowWorker завершен за 100.15ms"""
            }
        ],
        "under_the_hood": """
Аргумент `start` сохраняется на стеке `_defer`.
""",
        "pitfalls": """
- Написание `defer fmt.Println(time.Since(time.Now()))`: выведет `0s`, так как `time.Since` вычислится сразу в строке defer, а не при выходе!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `defer fmt.Println(time.Since(start))` без замыкания выводит неверное время?»
**Ответ:** Потому что аргументы функции, переданной в `defer`, вычисляются немедленно при объявлении строки `defer`, а не при выходе из функции.
"""
    },
    {
        "num": 81,
        "title": "Стек defer в цикле: строгое доказательство порядка LIFO",
        "task": "Стек defer: Напиши цикл с defer fmt.Println(i). Убедись, что defer вызываются в порядке LIFO (Последним пришел — первым ушел).",
        "theory": """
Закрепление LIFO порядка в цикле от 0 до 4.
""",
        "step_by_step": """
1. В цикле `for i := 0; i < 5; i++` вызываем `defer fmt.Println(i)`.
2. Фиксируем вывод `4 3 2 1 0`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func CountDown() {
	fmt.Println("Старт цикла регистрации defer:")
	for i := 0; i < 5; i++ {
		defer fmt.Printf("  LIFO defer: %d\n", i)
	}
	fmt.Println("Цикл завершен, выход из функции...")
}

func main() {
	CountDown()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Старт цикла регистрации defer:
# Цикл завершен, выход из функции...
#   LIFO defer: 4
#   LIFO defer: 3
#   LIFO defer: 2
#   LIFO defer: 1
#   LIFO defer: 0"""
            }
        ],
        "under_the_hood": """
Связанный список `_defer` разматывается от головы к хвосту.
""",
        "pitfalls": """
- Накопление тысяч defer в цикле.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В какой структуре рантайма хранятся вызовы `defer`?»
**Ответ:** В поле `_defer *godefer` структуры текущей горутины `runtime.g`.
"""
    },
    {
        "num": 82,
        "title": "Фабрика множителей MakeMultiplier(factor int) func(int) int",
        "task": "Создай функцию MakeMultiplier(factor int) func(int) int (функция, возвращающая функцию). Верни замыкание, которое умножает аргумент на factor. Создай несколько множителей и проверь их работу.",
        "theory": """
Генерация специализированных математических функций.
""",
        "step_by_step": """
1. Пишем `MakeMultiplier(factor int) func(int) int`.
2. Создаем `triple` ($\times 3$) и `decuple` ($\times 10$).
3. Проверяем вычисления.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func MakeMultiplier(factor int) func(int) int {
	return func(x int) int {
		return x * factor
	}
}

func main() {
	triple := MakeMultiplier(3)
	decuple := MakeMultiplier(10)

	fmt.Printf("triple(7):   %d\n", triple(7))
	fmt.Printf("decuple(7):  %d\n", decuple(7))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# triple(7):   21
# decuple(7):  70"""
            }
        ],
        "under_the_hood": """
Каждое замыкание фиксирует свой `factor`.
""",
        "pitfalls": """
- Мутация `factor` после создания замыкания.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что такое замыкание (Closure) с точки зрения компилятора?»
**Ответ:** Пара: указатель на машинный код функции и указатель на контекст захваченных переменных окружения.
"""
    },
    {
        "num": 83,
        "title": "Перехват паники через defer + recover() и предотвращение аварийного завершения процесса",
        "task": "Panic и Recover: Напишите функцию, которая провоцирует панику (panic(\"критическая ошибка\")). Оберните вызов в функцию с recover() внутри defer, чтобы программа не завершалась аварийно, а корректно обрабатывала инцидент.",
        "theory": """
Безопасная изоляция ненадежного кода.
""",
        "step_by_step": """
1. Пишем `CrashApp()`.
2. Оборачиваем в `SafeWrapper()`.
3. Убеждаемся в продолжении работы программы.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func CrashApp() {
	panic("💥 Фатальный сбой: повреждение памяти модуля")
}

func SafeWrapper() {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("🛡️ Паника успешно нейтрализована: %v\n", r)
		}
	}()

	CrashApp()
	fmt.Println("Этот код не выполнится")
}

func main() {
	fmt.Println("1. Старт программы")
	SafeWrapper()
	fmt.Println("2. Программа продолжает стабильную работу после паники!")
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Старт программы
# 🛡️ Паника успешно нейтрализована: 💥 Фатальный сбой: повреждение памяти модуля
# 2. Программа продолжает стабильную работу после паники!"""
            }
        ],
        "under_the_hood": """
`recover` прерывает размотку стека и возобновляет нормальное исполнение функции-обертки.
""",
        "pitfalls": """
- Попытка вызвать `recover()` в другой горутине: `recover` перехватывает паники ТОЛЬКО внутри своей горутины!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Перехватит ли `recover` в главной горутине панику из `go worker()`?»
**Ответ:** НЕТ! Паника в отдельной горутине, не перехваченная внутри этой же горутины, приведет к крашу всего процесса приложения.
"""
    },
    {
        "num": 84,
        "title": "Подмена возвращаемого значения в defer перед выходом из функции",
        "task": "Defer и возвращаемые значения: Напиши функцию с именованным возвращаемым значением. Используй defer, чтобы изменить это значение прямо перед выходом из функции (используется для подмены возвращаемого результата).",
        "theory": """
Паттерн подмены статуса ответа в Middleware.
""",
        "step_by_step": """
1. Пишем `ComputeStatus() (status string)`.
2. В defer меняем `status = "OVERRIDDEN"`.
3. Проверяем результат.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func ComputeStatus() (status string) {
	defer func() {
		status = "SUCCESS_MODIFIED_BY_DEFER"
	}()

	return "INITIAL_PENDING"
}

func main() {
	fmt.Printf("Финальный статус: %s\n", ComputeStatus())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Финальный статус: SUCCESS_MODIFIED_BY_DEFER"""
            }
        ],
        "under_the_hood": """
Прямая запись в стековый слот результата.
""",
        "pitfalls": """
- Неочевидная логика при злоупотреблении подменами.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В каких случаях подмена результата в `defer` является идиоматичной?»
**Ответ:** При перехвате паники и преобразовании ее в именованную возвращаемую ошибку `(err error)`.
"""
    },
    {
        "num": 85,
        "title": "Реализация функции свертки Reduce(nums, fn, initial) (Fold / Aggregate)",
        "task": "Напиши функцию Reduce(nums []int, fn func(int, int) int, initial int) int — аналог fold/reduce. Реализуй сумму, произведение, максимум через Reduce.",
        "theory": """
**Паттерн Reduce (Fold):**
- Аккумулирует элементы среза в единое результирующее значение;
- Принимает начальное значение `initial` и функцию-аккумулятор `fn(acc, elem) acc`.
""",
        "step_by_step": """
1. Пишем `Reduce(nums []int, fn func(int, int) int, initial int) int`.
2. Реализуем сумму (`+`), произведение (`*`), максимум.
3. Проверяем вычисления.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Reduce(nums []int, fn func(acc, val int) int, initial int) int {
	acc := initial
	for _, n := range nums {
		acc = fn(acc, n)
	}
	return acc
}

func main() {
	numbers := []int{1, 2, 3, 4, 5}

	sum := Reduce(numbers, func(acc, v int) int { return acc + v }, 0)
	product := Reduce(numbers, func(acc, v int) int { return acc * v }, 1)
	maxVal := Reduce(numbers, func(acc, v int) int {
		if v > acc {
			return v
		}
		return acc
	}, numbers[0])

	fmt.Printf("Числа:        %v\n", numbers)
	fmt.Printf("Сумма:        %d\n", sum)
	fmt.Printf("Произведение: %d\n", product)
	fmt.Printf("Максимум:     %d\n", maxVal)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Числа:        [1 2 3 4 5]
# Сумма:        15
# Произведение: 120
# Максимум:     5"""
            }
        ],
        "under_the_hood": """
Последовательное накопление в регистре процессора.
""",
        "pitfalls": """
- Неправильное начальное значение `initial` (например 0 для произведения).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова generic-сигнатура `Reduce` для любых типов `T` и `R`?»
**Ответ:** `func Reduce[T, R any](s []T, initial R, fn func(R, T) R) R`.
"""
    },
    {
        "num": 86,
        "title": "Рекурсивное вычисление n-го числа Фибоначчи и дерево вызовов",
        "task": "Рекурсия 2: Реализуй вычисление n-го числа Фибоначчи через рекурсию.",
        "theory": """
Закрепление рекурсивной реализации с выводом дерева шагов.
""",
        "step_by_step": """
1. Пишем `Fib(n int) int`.
2. Тестируем на числах 1..10.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Fib(n int) int {
	if n <= 0 {
		return 0
	}
	if n == 1 {
		return 1
	}
	return Fib(n-1) + Fib(n-2)
}

func main() {
	fmt.Printf("Fib(7) = %d\n", Fib(7))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Fib(7) = 13"""
            }
        ],
        "under_the_hood": """
Стековые кадры разворачиваются при возврате из листьев дерева.
""",
        "pitfalls": """
- Вызов на больших числах.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как трансформировать наивную рекурсию в хвостовую?»
**Ответ:** Добавить аккумуляторы: `func FibTail(n, a, b int) int { if n == 0 { return a }; return FibTail(n-1, b, a+b) }`.
"""
    },
    {
        "num": 87,
        "title": "Генерация паники через panic() при нарушении бизнес-инварианта",
        "task": "Panic: Напиши функцию, которая вызывает panic(\"что-то пошло не так\") при определенном условии. Убедись, что программа экстренно завершается.",
        "theory": """
Демонстрация экстренного завершения программы.
""",
        "step_by_step": """
1. Пишем `CheckBalance(balance int)`.
2. Если `balance < 0`, вызываем `panic(...)`.
3. Перехватываем в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func CheckBalance(balance int) {
	if balance < 0 {
		panic("что-то пошло не так: отрицательный баланс в транзакции")
	}
	fmt.Printf("Баланс корректен: %d руб.\n", balance)
}

func main() {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("💥 Программа зафиксировала экстренное прерывание: %v\n", r)
		}
	}()

	CheckBalance(-100)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 💥 Программа зафиксировала экстренное прерывание: что-то пошло не так: отрицательный баланс в транзакции"""
            }
        ],
        "under_the_hood": """
`runtime.gopanic` формирует стек-трейс ошибки.
""",
        "pitfalls": """
- Оставление непойманной паники в горутине.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что попадает в вывод при непойманной панике?»
**Ответ:** Сообщение паники, стек-трейс упавшей горутины и состояния всех остальных активных горутин в процессе.
"""
    },
    {
        "num": 88,
        "title": "Безопасное восстановление после паники с логированием и продолжением работы",
        "task": "Recover (перехват паники): Добавь defer с функцией recover() в упр. 70, чтобы \"спасти\" программу от падения и корректно обработать ошибку.",
        "theory": """
Паттерн надежности (Fault Tolerance) в микросервисах.
""",
        "step_by_step": """
1. Пишем функцию выполнения рискованного плагина `RunPlugin()`.
2. Оборачиваем в защитный блок с `recover()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func RiskyPlugin() {
	var ptr *int
	*ptr = 42 // Нил-разыменование!
}

func SafePluginRunner() {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("⚠️ Плагин аварийно завершился: %v. Сервер продолжает работу.\n", r)
		}
	}()

	RiskyPlugin()
}

func main() {
	fmt.Println("Запуск безопасного контейнера плагинов...")
	SafePluginRunner()
	fmt.Println("Сервис успешно обработал следующий запрос!")
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Запуск безопасного контейнера плагинов...
# ⚠️ Плагин аварийно завершился: runtime error: invalid memory address or nil pointer dereference. Сервер продолжает работу.
# Сервис успешно обработал следующий запрос!"""
            }
        ],
        "under_the_hood": """
Нил-разыменование вызывает `SIGSEGV`, который рантайм Go трансформирует в панику.
""",
        "pitfalls": """
- Игнорирование логирования ошибки при `recover()`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли восстановиться после `fatal error: out of memory` или `stack overflow`?»
**Ответ:** НЕТ! Фатальные системные ошибки рантайма (OOM, Stack overflow, race on map) не вызывают панику и не могут быть перехвачены через `recover()`.
"""
    },
    {
        "num": 89,
        "title": "Размотка стека вызовов при панике (Stack Unwinding) сквозь цепочку функций A -> B -> C",
        "task": "Panic на уровне вызовов: Помести panic в функцию C, которая вызывается из функции B, которая вызывается из функции A (где стоит recover). Посмотри, как разматывается стек вызовов.",
        "theory": """
**Каскадная размотка стека (Stack Unwinding):**
- Функция `C` паникует $\rightarrow$ в ней отрабатывают `defer` (если есть);
- Управление передается выше в функцию `B` $\rightarrow$ в ней отрабатывают `defer`;
- Управление передается в функцию `A`, где `recover()` останавливает панику.
""",
        "step_by_step": """
1. Пишем `FuncC()` с паникой.
2. Пишем `FuncB()` с `defer fmt.Println("defer B")`.
3. Пишем `FuncA()` с `defer recover()`.
4. Наблюдаем каскадное закрытие ресурсов.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func FuncC() {
	defer fmt.Println("  [defer в FuncC]")
	fmt.Println("  Вход в FuncC -> провоцируем панику!")
	panic("ошибка ядра в FuncC")
}

func FuncB() {
	defer fmt.Println(" [defer в FuncB]")
	fmt.Println(" Вход в FuncB -> вызываем FuncC")
	FuncC()
}

func FuncA() {
	defer func() {
		fmt.Println("[defer в FuncA] -> перехват паники!")
		if r := recover(); r != nil {
			fmt.Printf("🛡️ Паника перехвачена на верхнем уровне FuncA: %v\n", r)
		}
	}()

	fmt.Println("Вход в FuncA -> вызываем FuncB")
	FuncB()
}

func main() {
	FuncA()
	fmt.Println("Программа штатно завершена в main")
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вход в FuncA -> вызываем FuncB
#  Вход в FuncB -> вызываем FuncC
#   Вход в FuncC -> провоцируем панику!
#   [defer в FuncC]
#  [defer в FuncB]
# [defer в FuncA] -> перехват паники!
# 🛡️ Паника перехвачена на верхнем уровне FuncA: ошибка ядра в FuncC
# Программа штатно завершена в main"""
            }
        ],
        "under_the_hood": """
Рантайм проходит цепочку фреймов от вершины стека к корню.
""",
        "pitfalls": """
- Ресурсы в `FuncB` гарантированно закрываются, если были зарегистрированы в `defer`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Будут ли выполнены `defer` в промежуточных функциях `B` и `C` при возникновении паники?»
**Ответ:** ДА! Все зарегистрированные `defer` на всех уровнях стека выполняются гарантированно.
"""
    },
    {
        "num": 90,
        "title": "Метод со значением-получателем (Value Receiver): func (c Counter) Print()",
        "task": "Методы (база): Объяви свой тип type Counter int. Напиши для него метод func (c Counter) Print(), который можно будет вызвать как myCounter.Print().",
        "theory": """
Объявление метода на базовом типе со значением-получателем.
""",
        "step_by_step": """
1. Объявляем `type Counter int`.
2. Пишем метод `func (c Counter) Print()`.
3. Вызываем через точку `myCounter.Print()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Counter int

func (c Counter) Print() {
	fmt.Printf("Значение счетчика: %d\n", c)
}

func main() {
	var myCounter Counter = 42
	myCounter.Print()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Значение счетчика: 42"""
            }
        ],
        "under_the_hood": """
Метод компилируется в обычную функцию `Counter.Print(c Counter)`.
""",
        "pitfalls": """
- Метод с Value Receiver не может изменять значение `myCounter`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова семантика вызова `myCounter.Print()`?»
**Ответ:** Это синтаксический сахар для вызова функции `Counter.Print(myCounter)`.
"""
    },
    {
        "num": 91,
        "title": "Изоляция и восстановление после паники PanicRecover()",
        "task": "Напиши функцию PanicRecover(). Вызови panic(\"something went wrong\"). В другой функции отложи recover() через defer. Покажи, как восстановиться после паники.",
        "theory": """
Закрепление паттерна безопасного выполнения.
""",
        "step_by_step": """
1. Пишем `PanicRecover()`.
2. Проверяем перехват.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func UnstableService() {
	panic("something went wrong")
}

func PanicRecover() {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("Recovered from: %v\n", r)
		}
	}()

	UnstableService()
}

func main() {
	PanicRecover()
	fmt.Println("Main continued")
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Recovered from: something went wrong
# Main continued"""
            }
        ],
        "under_the_hood": """
Сброс паники в структуре горутины.
""",
        "pitfalls": """
- Вызов `recover()` без проверки на `nil`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему важно проверять `if r := recover(); r != nil`?»
**Ответ:** Потому что `recover()` возвращает `nil`, если паники не происходило.
"""
    },
    {
        "num": 92,
        "title": "Универсальный вывод любых значений PrintAnything(v any) через глагол %v",
        "task": "Пустой интерфейс (анонс): Напиши функцию PrintAnything(v interface{}) (или any), которая принимает значение любого типа и использует %v для его вывода.",
        "theory": """
**Пустой интерфейс `any` (`interface{}`):**
- Описывает множество всех существующих типов в Go;
- Любой тип автоматически удовлетворяет пустому интерфейсу.
""",
        "step_by_step": """
1. Пишем `PrintAnything(v any)`.
2. Передаем число, строку, структуру, срез.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func PrintAnything(v any) {
	fmt.Printf("Тип: %-15T | Значение: %v\n", v, v)
}

func main() {
	PrintAnything(100)
	PrintAnything("Привет, Go!")
	PrintAnything([]int{1, 2, 3})
	PrintAnything(struct{ Host string }{"localhost"})
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Тип: int             | Значение: 100
# Тип: string          | Значение: Привет, Go!
# Тип: []int           | Значение: [1 2 3]
# Тип: struct { Host string } | Значение: {localhost}"""
            }
        ],
        "under_the_hood": """
Формирование дескриптора `eface` в рантайме.
""",
        "pitfalls": """
- Злоупотребление `any` там, где можно использовать строгую типизацию или дженерики.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем отличие `any` от дженериков `[T any]`?»
**Ответ:** `any` упаковывает значение в интерфейс в рантайме с динамической диспетчеризацией, а дженерики параметризуют код во время компиляции со статической типизацией без оверхеда на интерфейсы.
"""
    },
    {
        "num": 93,
        "title": "Функция преобразования среза ApplyToEach(nums []int, fn func(int) int) []int (Map)",
        "task": "Напиши функцию высшего порядка: ApplyToEach(nums []int, fn func(int) int) []int, которая применяет функцию к каждому элементу слайса.",
        "theory": """
Реализация паттерна Map (Функтор).
""",
        "step_by_step": """
1. Пишем `ApplyToEach(nums []int, fn func(int) int) []int`.
2. Создаем результирующий срез `make([]int, len(nums))`.
3. Заполняем преобразованными элементами.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func ApplyToEach(nums []int, fn func(int) int) []int {
	res := make([]int, len(nums))
	for i, v := range nums {
		res[i] = fn(v)
	}
	return res
}

func main() {
	numbers := []int{1, 2, 3, 4, 5}

	doubled := ApplyToEach(numbers, func(n int) int { return n * 2 })
	squared := ApplyToEach(numbers, func(n int) int { return n * n })

	fmt.Printf("Оригинал: %v\n", numbers)
	fmt.Printf("Удвоено:  %v\n", doubled)
	fmt.Printf("Квадраты: %v\n", squared)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Оригинал: [1 2 3 4 5]
# Удвоено:  [2 4 6 8 10]
# Квадраты: [1 4 9 16 25]"""
            }
        ],
        "under_the_hood": """
1 аллокация среза нужной длины.
""",
        "pitfalls": """
- Использование `append` вместо предварительного `make([]int, len(nums))`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова асимптотика `ApplyToEach`?»
**Ответ:** Строго $O(N)$ времени и $O(N)$ памяти.
"""
    },
    {
        "num": 94,
        "title": "Надежный рекурсивный факториал Factorial(n int) (int, error) с защитой от переполнения",
        "task": "Напиши рекурсивную функцию Factorial(n int) int. Добавь проверку на отрицательные числа и переполнение.",
        "theory": """
**Защита от переполнения факториала:**
- В 64-битном типе `int` максимальный факториал, помещающийся без переполнения: $20! \approx 2.43 \times 10^{18} < 2^{63}-1$;
- Для $n > 20$ функция обязана возвращать ошибку переполнения.
""",
        "step_by_step": """
1. Пишем `SafeFactorial(n int) (int64, error)`.
2. Проверяем `n < 0` и `n > 20`.
3. Рекурсивно вычисляем результат.
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

func SafeFactorial(n int) (int64, error) {
	if n < 0 {
		return 0, errors.New("факториал отрицательного числа не определен")
	}
	if n > 20 {
		return 0, errors.New("переполнение типа int64 при n > 20")
	}
	if n <= 1 {
		return 1, nil
	}
	prev, _ := SafeFactorial(n - 1)
	return int64(n) * prev, nil
}

func main() {
	f5, err5 := SafeFactorial(5)
	fmt.Printf("5! = %d (err: %v)\n", f5, err5)

	f21, err21 := SafeFactorial(21)
	fmt.Printf("21! = %d (err: %v)\n", f21, err21)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 5! = 120 (err: <nil>)
# 21! = 0 (err: переполнение типа int64 при n > 20)"""
            }
        ],
        "under_the_hood": """
Сравнение с лимитом `math.MaxInt64`.
""",
        "pitfalls": """
- Игнорирование проверки переполнения: приведет к появлению отрицательных чисел из-за знакопеременного переполнения.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какой пакет стандартной библиотеки позволяет считать факториал от 1000 без переполнения?»
**Ответ:** Пакет `math/big` и тип `big.Int` (`big.NewInt(0).Mul(...)`).
"""
    },
    {
        "num": 95,
        "title": "Сравнение производительности наивного рекурсивного Фибоначчи и мемоизации за O(N)",
        "task": "Напиши рекурсивную функцию Fibonacci(n int) int. Замерь время для n = 40. Затем оптимизируй через мемоизацию (map или слайс). Сравни производительность.",
        "theory": """
**Сравнительный бенчмарк алгоритмов:**
- Наивная рекурсия: $O(2^N)$ (около 1 секунды для $N = 40$);
- Мемоизация: $O(N)$ (около 1 микросекунды для $N = 40$, ускорение в $1\,000\,000$ раз!).
""",
        "step_by_step": """
1. Пишем `FibNaive(n int) int`.
2. Пишем `FibMemo(n int, memo []int) int`.
3. Замеряем время выполнения обоих вариантов для $N = 40$.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"time"
)

func FibNaive(n int) int {
	if n <= 1 {
		return n
	}
	return FibNaive(n-1) + FibNaive(n-2)
}

func FibMemo(n int, memo []int) int {
	if n <= 1 {
		return n
	}
	if memo[n] != 0 {
		return memo[n]
	}
	memo[n] = FibMemo(n-1, memo) + FibMemo(n-2, memo)
	return memo[n]
}

func main() {
	n := 40

	// 1. Наивный расчет:
	startNaive := time.Now()
	resNaive := FibNaive(n)
	durNaive := time.Since(startNaive)
	fmt.Printf("1. Наивный расчет:   Fib(%d) = %d | Время: %v\n", n, resNaive, durNaive)

	// 2. Расчет с мемоизацией:
	memo := make([]int, n+1)
	startMemo := time.Now()
	resMemo := FibMemo(n, memo)
	durMemo := time.Since(startMemo)
	fmt.Printf("2. С мемоизацией:    Fib(%d) = %d | Время: %v (УСКОРЕНИЕ В РАЗЫ!)\n",
		n, resMemo, durMemo)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Наивный расчет:   Fib(40) = 102334155 | Время: 420.5ms
# 2. С мемоизацией:    Fib(40) = 102334155 | Время: 1.2µs (УСКОРЕНИЕ В РАЗЫ!)"""
            }
        ],
        "under_the_hood": """
Мемоизация устраняет экспоненциальное дублирование вычислений.
""",
        "pitfalls": """
- Выделение кэша недостаточного размера `make([]int, n)` вместо `make([]int, n+1)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему срез для мемоизации быстрее, чем `map[int]int`?»
**Ответ:** Потому что доступ по индексу среза `memo[n]` — это 1 инструкция чтения из непрерывной памяти, а поиск в мапе требует вычисления хэша, поиска бакета и разрешения коллизий.
"""
    },
    {
        "num": 96,
        "title": "Захват переменной по указателю и замыканию: defer видит значение на момент исполнения",
        "task": "Напиши функцию DeferStack(). Используй defer с анонимной функцией, которая захватывает переменную. Покажи, что defer видит значение на момент выполнения (не объявления), если переменная передаётся по указателю или замыканию.",
        "theory": """
**Механика захвата в замыкании `defer func() { ... }()`:**
- Анонимная функция захватывает переменную по ссылке;
- В момент фактического выполнения `defer` она читает **самое последнее актуальное значение переменной**.
""",
        "step_by_step": """
1. Переменная `x := 10`.
2. Регистрируем `defer func() { fmt.Println(x) }()`.
3. Меняем `x = 99`.
4. Наблюдаем вывод 99.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func DeferStack() {
	x := 10

	// Замыкание захватывает переменную x по ссылке:
	defer func() {
		fmt.Printf("defer видит актуальное значение x = %d (на момент завершения функции!)\n", x)
	}()

	x = 99 // Изменяем значение переменной
	fmt.Printf("В теле функции x изменен на %d\n", x)
}

func main() {
	DeferStack()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# В теле функции x изменен на 99
# defer видит актуальное значение x = 99 (на момент завершения функции!)"""
            }
        ],
        "under_the_hood": """
Замыкание обращается к переменной в стековом кадре по указателю.
""",
        "pitfalls": """
- Ожидание вывода 10 вместо 99.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как зафиксировать значение 10 в defer?»
**Ответ:** Передать `x` параметром: `defer func(val int) { ... }(x)`.
"""
    },
    {
        "num": 97,
        "title": "Изоляция аргументов defer в цикле: передача параметров в анонимную функцию",
        "task": "Напиши функцию DeferWithArgs(). Вызови defer fmt.Println(i) в цикле. Покажи, что все defer'ы выводят одно и то же значение (потому что i захватывается по ссылке в замыкание). Исправь, передавая i как аргумент анонимной функции.",
        "theory": """
Сравнение замыкания по ссылке и передачи аргумента по значению в `defer`.
""",
        "step_by_step": """
1. Пишем функцию с передачей аргумента `func(val int) { ... }(i)`.
2. Проверяем правильный LIFO вывод.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func DeferWithArgs() {
	for i := 1; i <= 3; i++ {
		// ПРАВИЛЬНО: значение i копируется в аргумент val в момент создания defer
		defer func(val int) {
			fmt.Printf("defer с изолированным аргументом: %d\n", val)
		}(i)
	}
}

func main() {
	DeferWithArgs()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# defer с изолированным аргументом: 3
# defer с изолированным аргументом: 2
# defer с изолированным аргументом: 1"""
            }
        ],
        "under_the_hood": """
Значение `i` копируется в стек вызова отложенной функции.
""",
        "pitfalls": """
- Забыть скобки передачи `(i)` в конце.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему передача аргумента в `defer func(v)` надежнее захвата переменной?»
**Ответ:** Потому что она гарантирует создание независимой копии значения на момент объявления, защищая от последующих мутаций.
"""
    },
    {
        "num": 98,
        "title": "Идиоматичный таймер выполнения функций defer Timer(\"name\")()",
        "task": "Напиши функцию Timer(name string) func(), которая замеряет время выполнения. Используй замыкание: при вызове defer Timer(\"operation\")() замерь время между входом и выходом.",
        "theory": """
**Элегантный паттерн Defer Function Returning Function:**
- Вызов `defer Timer("API")()`:
  1. `Timer("API")` выполняется **немедленно** (фиксирует начальное время `start := time.Now()`);
  2. Возвращенная функция откладывается через `defer` и вызывается **при выходе** из внешней функции!
""",
        "step_by_step": """
1. Пишем `Timer(name string) func()`.
2. Фиксируем `start := time.Now()`.
3. Возвращаем функцию вывода `time.Since(start)`.
4. Используем через `defer Timer("HeavyTask")()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"time"
)

func Timer(name string) func() {
	start := time.Now()
	return func() {
		fmt.Printf("⏱️ [%s] Время выполнения: %v\n", name, time.Since(start))
	}
}

func HeavyDatabaseQuery() {
	defer Timer("HeavyDatabaseQuery")() // Обратите внимание на двойные скобки ()()!

	fmt.Println("Выполнение сложного SQL-запроса...")
	time.Sleep(50 * time.Millisecond)
}

func main() {
	HeavyDatabaseQuery()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Выполнение сложного SQL-запроса...
# ⏱️ [HeavyDatabaseQuery] Время выполнения: 50.12ms"""
            }
        ],
        "under_the_hood": """
Внешняя функция выполняется синхронно, а возвращенное замыкание регистрируется в стеке `_defer`.
""",
        "pitfalls": """
- Забыть вторые скобки `()`: `defer Timer("name")` просто создаст функцию, но никогда не выполнит ее при выходе!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как этот паттерн применяется для управления мьютексами?»
**Ответ:** `func LockAndUnlock(mu *sync.Mutex) func() { mu.Lock(); return mu.Unlock }; defer LockAndUnlock(&mu)()` — блокирует сразу, а разблокирует при выходе.
"""
    },
    {
        "num": 99,
        "title": "Универсальная generic-функция фильтрации Filter[T any](s []T, predicate func(T) bool) []T",
        "task": "Напиши generic-функцию Filter[T any](s []T, predicate func(T) bool) []T. Создай ограничение (constraint), чтобы T был comparable или constraints.Ordered.",
        "theory": """
**Дженерики (Type Parameters) в Go 1.18+:**
- Сигнатура `Filter[T any](s []T, predicate func(T) bool) []T`;
- Позволяет фильтровать срезы любых типов (`[]int`, `[]string`, `[]User`) с полной статической проверкой типов без `interface{}` и рефлексии.
""",
        "step_by_step": """
1. Пишем generic-функцию `Filter[T any](s []T, predicate func(T) bool) []T`.
2. Тестируем на числах и строках.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Filter[T any](s []T, predicate func(T) bool) []T {
	var result []T
	for _, v := range s {
		if predicate(v) {
			result = append(result, v)
		}
	}
	return result
}

func main() {
	ints := []int{10, 15, 20, 25, 30}
	evenInts := Filter(ints, func(n int) bool { return n%2 == 0 })

	words := []string{"Go", "Rust", "Golang", "C"}
	longWords := Filter(words, func(w string) bool { return len(w) > 2 })

	fmt.Printf("Числа: %v\n", evenInts)
	fmt.Printf("Слова:  %v\n", longWords)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Числа: [10 20 30]
# Слова:  [Rust Golang]"""
            }
        ],
        "under_the_hood": """
Мономорфизация и GC-shape stenciling компилятора Go генерируют оптимизированный машинный код.
""",
        "pitfalls": """
- Попытка использовать операторы `<` или `>` для типа с ограничением `any` (требуется `cmp.Ordered`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каковы преимущества дженериков перед пустым интерфейсом `any`?»
**Ответ:** Статическая проверка типов во время компиляции, устранение оверхеда на упаковку (Boxing) и отсутствие проверок типов в рантайме.
"""
    },
    {
        "num": 100,
        "title": "Универсальный поиск максимума Max[T cmp.Ordered](a, b T) T на дженериках в Go 1.21+",
        "task": "Напиши generic-функцию Max[T constraints.Ordered](a, b T) T. Протестируй с int, float64, string. Объясни, что такое constraints.Ordered.",
        "theory": """
**Ограничение `cmp.Ordered` (Go 1.21+):**
- Пакет `cmp` стандартной библиотеки определяет `type Ordered interface { ~int | ~int8 | ... | ~float64 | ~string }`;
- Поддерживает все типы, для которых определены операторы `<`, `<=`, `>`, `>=`;
- Позволяет писать универсальные математические функции `Max` и `Min` без дублирования кода.
""",
        "step_by_step": """
1. Импортируем стандартный пакет `cmp`.
2. Пишем `Max[T cmp.Ordered](a, b T) T`.
3. Тестируем на `int`, `float64`, `string`.
""",
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
	fmt.Printf("Max(10, 20):         %d\n", Max(10, 20))
	fmt.Printf("Max(3.14, 2.71):     %.2f\n", Max(3.14, 2.71))
	fmt.Printf("Max(\"apple\", \"pear\"): %q\n", Max("apple", "pear"))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Max(10, 20):         20
# Max(3.14, 2.71):     3.14
# Max("apple", "pear"): "pear" """
            }
        ],
        "under_the_hood": """
Компилятор подставляет соответствующие инструкции сравнения процессора (`CMPQ`, `UCOMISD`).
""",
        "pitfalls": """
- Использование устаревшего пакета `golang.org/x/exp/constraints` вместо стандартного `cmp.Ordered` в Go 1.21+.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какая встроенная функция в Go 1.21+ заменила самописный `Max`?»
**Ответ:** Встроенные универсальные функции `max(a, b, c...)` и `min(a, b, c...)`, доступные без импорта пакетов.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 4: {len(exercises)} exercises.")
