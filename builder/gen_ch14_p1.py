# Chapter 14 Part 1: Exercises 1 to 26

exercises = [
    {
        "num": 1,
        "title": "Неявная реализация интерфейсов (Implicit Interface Satisfaction) без ключевого слова implements",
        "task": "Объяви интерфейс Greeter с методом Greet() string. Создай структуру Englishman, реализующую его. Покажи, что в Go нет ключевого слова implements — реализация неявная.",
        "theory": """
**Утиная типизация (Structural Typing / Implicit Satisfaction) в Go:**
- В Go **отсутствует ключевое слово `implements`**;
- Тип автоматически удовлетворяет интерфейсу, если он реализует **все методы**, объявленные в интерфейсе с совпадающими сигнатурами;
- Это исключает жесткую связь между поставщиком реализации и потребителем API (Loose Coupling).
""",
        "step_by_step": """
1. Объявляем интерфейс `Greeter` с методом `Greet() string`.
2. Создаем структуру `Englishman{}` и реализуем метод `Greet() string`.
3. Присваиваем структуру переменной интерфейса.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Greeter interface {
	Greet() string
}

type Englishman struct {
	Name string
}

// Englishman автоматически реализует интерфейс Greeter:
func (e Englishman) Greet() string {
	return fmt.Sprintf("Hello, my name is %s!", e.Name)
}

func main() {
	var g Greeter = Englishman{Name: "Arthur"}
	fmt.Println(g.Greet())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Hello, my name is Arthur!"""
            }
        ],
        "under_the_hood": """
Компилятор Go строит интерфейсную таблицу `runtime.iface` (состоящую из `itab` с таблицей указателей на функции и `data` с указателем на значение).
""",
        "pitfalls": """
- Попытка искать ключевое слово `implements` или забыть один из методов интерфейса (ошибка `does not implement ... (missing method)`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему создатели Go отказались от явного `implements`?»
**Ответ:** Неявные интерфейсы позволяют пакетам определять минимальные интерфейсы под свои нужды для типов из чужих библиотек без необходимости изменять исходный код этих библиотек.
"""
    },
    {
        "num": 2,
        "title": "Полиморфизм интерфейсов: динамическое переназначение структур Englishman и Spaniard",
        "task": "Создай переменную типа интерфейса var g Greeter. Присвой ей Englishman{}. Вызови метод. Затем присвой другую структуру Spaniard{} — покажи полиморфизм.",
        "theory": """
**Динамический полиморфизм (Runtime Polymorphism):**
- Переменная интерфейсного типа может в рантайме хранить значения любых конкретных типов, удовлетворяющих данному интерфейсу;
- При каждом вызове метода вызывается реализация текущего активного типа.
""",
        "step_by_step": """
1. Создаем структуры `Englishman` и `Spaniard`.
2. Присваиваем поочередно интерфейсу `var g Greeter`.
3. Демонстрируем полиморфный вызов.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Greeter interface {
	Greet() string
}

type Englishman struct{}

func (Englishman) Greet() string {
	return "Hello!"
}

type Spaniard struct{}

func (Spaniard) Greet() string {
	return "¡Hola!"
}

func main() {
	var g Greeter

	g = Englishman{}
	fmt.Printf("g (Englishman): %s\n", g.Greet())

	g = Spaniard{}
	fmt.Printf("g (Spaniard):   %s\n", g.Greet())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# g (Englishman): Hello!
# g (Spaniard):   ¡Hola!"""
            }
        ],
        "under_the_hood": """
При переприсваивании `g = Spaniard{}` обновляется указатель `itab` внутри интерфейсной структуры на таблицу методов `Spaniard`.
""",
        "pitfalls": """
- Вызов метода на неинициализированном интерфейсе `var g Greeter; g.Greet()` (паника `nil pointer dereference`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Из каких двух указателей состоит интерфейс `iface` под капотом?»
**Ответ:** 1) `*itab` (тип данных, метаинформация и таблица адресов методов); 2) `unsafe.Pointer` (указатель на сами данные объекта в памяти).
"""
    },
    {
        "num": 3,
        "title": "Интерфейс Animal с методом Speak() string для структур Dog и Cat",
        "task": "Создайте интерфейс Animal с методом Speak() string. Реализуйте его для структур Dog и Cat (неявная реализация).",
        "theory": """
Базовое моделирование предметной области с полиморфными сущностями.
""",
        "step_by_step": """
1. Создаем интерфейс `Animal`.
2. Реализуем `Speak()` для `Dog` (Гав!) и `Cat` (Мяу!).
3. Тестируем.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Animal interface {
	Speak() string
}

type Dog struct{}

func (Dog) Speak() string {
	return "Гав-гав!"
}

type Cat struct{}

func (Cat) Speak() string {
	return "Мяу-мяу!"
}

func main() {
	var a1 Animal = Dog{}
	var a2 Animal = Cat{}

	fmt.Printf("Собака: %s\n", a1.Speak())
	fmt.Printf("Кошка:  %s\n", a2.Speak())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Собака: Гав-гав!
# Кошка:  Мяу-мяу!"""
            }
        ],
        "under_the_hood": """
Вызов метода осуществляется через косвенный вызов `CALL (itab.fun[0])`.
""",
        "pitfalls": """
- Опечатка в сигнатуре метода (например, возврат `int` вместо `string`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова стоимость вызова метода интерфейса по сравнению с прямым вызовом структуры?»
**Ответ:** Вызов через интерфейс требует одного дополнительного разыменования указателя таблицы `itab.fun` (около 1-2 процессорных тактов) и препятствует инлайнингу (Inlining).
"""
    },
    {
        "num": 4,
        "title": "Полиморфизм в коллекциях: гетерогенный срез []Speaker и вызов методов в цикле",
        "task": "Полиморфизм: Создай срез []Speaker. Положи туда собаку и кошку. В цикле пройдись по срезу и вызови Speak() для каждого. Заметь: структуры нигде не заявляют implements Speaker, они просто имеют нужный метод.",
        "theory": """
**Гетерогенные коллекции интерфейсов:**
- Срез интерфейсов `[]Speaker` может объединять совершенно разнородные структуры в единую полиморфную последовательность.
""",
        "step_by_step": """
1. Объявляем `type Speaker interface { Speak() string }`.
2. Создаем срез `speakers := []Speaker{Dog{}, Cat{}}`.
3. Итерируемся в цикле `for range`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Speaker interface {
	Speak() string
}

type Dog struct{ Breed string }

func (d Dog) Speak() string {
	return fmt.Sprintf("[%s] Гав!", d.Breed)
}

type Cat struct{ Color string }

func (c Cat) Speak() string {
	return fmt.Sprintf("[%s] Мяу!", c.Color)
}

func main() {
	speakers := []Speaker{
		Dog{Breed: "Овчарка"},
		Cat{Color: "Рыжий"},
		Dog{Breed: "Хаски"},
	}

	fmt.Println("Полиморфный хор:")
	for _, s := range speakers {
		fmt.Printf("  • %s\n", s.Speak())
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Полиморфный хор:
#   • [Овчарка] Гав!
#   • [Рыжий] Мяу!
#   • [Хаски] Гав!"""
            }
        ],
        "under_the_hood": """
Каждый элемент среза занимает 16 байт (`itab` + `data`).
""",
        "pitfalls": """
- Попытка преобразовать `[]Dog` напрямую в `[]Speaker` без поэлементного копирования (в Go это запрещено!).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go нельзя напрямую привести `[]Dog` к `[]Speaker`?»
**Ответ:** Потому что размер элементов в памяти различается: `Dog` может занимать любой размер (например 8 байт), а интерфейс `Speaker` всегда занимает 16 байт (`itab + data`).
"""
    },
    {
        "num": 5,
        "title": "Универсальный переключатель типов Type Switch: функция PrintDetails(v any)",
        "task": "Напиши функцию PrintDetails(v interface{}), использующую type switch для определения типа и вывода информации. Обработай int, string, bool, []int, struct.",
        "theory": """
**Конструкция Type Switch (`v.(type)`):**
- Специальная конструкция Go для инспекции динамического типа значения, упакованного в пустой интерфейс `any` / `interface{}`;
- Внутри каждого `case T:` переменная автоматически приводится к конкретному типу `T`.
""",
        "step_by_step": """
1. Пишем `PrintDetails(v any)`.
2. Используем `switch val := v.(type)`.
3. Обрабатываем `int`, `string`, `bool`, `[]int`, структуры и `default`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Point struct {
	X, Y int
}

func PrintDetails(v any) {
	switch val := v.(type) {
	case int:
		fmt.Printf("Целое число: %d (квадрат: %d)\n", val, val*val)
	case string:
		fmt.Printf("Строка: %q (длина: %d байт)\n", val, len(val))
	case bool:
		fmt.Printf("Булево значение: %t\n", val)
	case []int:
		fmt.Printf("Срез чисел: %v (элементов: %d)\n", val, len(val))
	case Point:
		fmt.Printf("Координата Point: X=%d, Y=%d\n", val.X, val.Y)
	default:
		fmt.Printf("Неизвестный тип (%T): %v\n", val, val)
	}
}

func main() {
	PrintDetails(42)
	PrintDetails("Golang")
	PrintDetails(true)
	PrintDetails([]int{10, 20, 30})
	PrintDetails(Point{X: 5, Y: 10})
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Целое число: 42 (квадрат: 1764)
# Строка: "Golang" (длина: 6 байт)
# Булево значение: true
# Срез чисел: [10 20 30] (элементов: 3)
# Координата Point: X=5, Y=10"""
            }
        ],
        "under_the_hood": """
Type Switch сравнивает указатели на дескрипторы типов `_type` в `eface`.
""",
        "pitfalls": """
- Использование `v.(type)` вне оператора `switch` (синтаксическая ошибка компилятора).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем отличие `switch v.(type)` от `reflect.TypeOf(v)`?»
**Ответ:** `switch v.(type)` работает на уровне компилятора без динамических аллокаций рефлексии и типизирует переменную `val` внутри каждого `case`.
"""
    },
    {
        "num": 6,
        "title": "Функция PlayWithAnimal(a Animal) и демонстрация полиморфизма в аргументах",
        "task": "Напишите функцию, принимающую Animal и вызывающую Speak(). Передайте туда Dog и Cat, чтобы увидеть полиморфизм в действии.",
        "theory": """
Прием интерфейсов в качестве параметров функций — основа принципа Dependency Inversion (DIP).
""",
        "step_by_step": """
1. Объявляем `PlayWithAnimal(a Animal)`.
2. Передаем различные структуры.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Animal interface {
	Speak() string
}

type Dog struct{ Name string }

func (d Dog) Speak() string {
	return d.Name + " говорит: Гав!"
}

type Cat struct{ Name string }

func (c Cat) Speak() string {
	return c.Name + " говорит: Мяу!"
}

func PlayWithAnimal(a Animal) {
	fmt.Println("Звук животного:", a.Speak())
}

func main() {
	PlayWithAnimal(Dog{Name: "Бобик"})
	PlayWithAnimal(Cat{Name: "Мурка"})
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Звук животного: Бобик говорит: Гав!
# Звук животного: Мурка говорит: Мяу!"""
            }
        ],
        "under_the_hood": """
Структура оборачивается в `iface` при передаче в функцию.
""",
        "pitfalls": """
- Передача `nil`-указателя в `Animal`, если метод обращается к полям структуры.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какое золотое правило проектирования API в Go?»
**Ответ:** «Accept interfaces, return structs» (Принимай интерфейсы, возвращай конкретные структуры).
"""
    },
    {
        "num": 7,
        "title": "Утверждение типа Type Assertion s := v.(string) и паника при несовпадении типов",
        "task": "Напиши функцию AssertString(v interface{}) string, делающую type assertion: s := v.(string). Покажи панику при неверном типе (передай int).",
        "theory": """
**Опасность одинарного Type Assertion `s := v.(T)`:**
- Если тип значения внутри интерфейса не совпадает строго с `T`, рантайм **немедленно выбрасывает панику**: `panic: interface conversion: interface {} is int, not string`;
- В продакшене одинарный Type Assertion без `comma-ok` допустим только если тип гарантирован на 100%.
""",
        "step_by_step": """
1. Пишем `AssertString(v any) string`.
2. Вызываем со строкой (успех).
3. Демонстрируем перехват паники через `recover()` при передаче `int`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func AssertString(v any) (result string) {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("⚠️ ПЕРЕХВАЧЕНА ПАНИКА: %v\n", r)
			result = "<ОШИБКА ТИПА>"
		}
	}()

	// Одинарный Type Assertion (опасный):
	return v.(string)
}

func main() {
	res1 := AssertString("Корректная строка")
	fmt.Printf("1. Успешный вызов: %s\n", res1)

	res2 := AssertString(12345) // Передаем int вместо string!
	fmt.Printf("2. Результат:      %s\n", res2)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Успешный вызов: Корректная строка
# ⚠️ ПЕРЕХВАЧЕНА ПАНИКА: interface conversion: interface {} is int, not string
# 2. Результат:      <ОШИБКА ТИПА>"""
            }
        ],
        "under_the_hood": """
При несовпадении `_type` функция рантайма `runtime.panicdottypeE` инициирует панику.
""",
        "pitfalls": """
- Использование одинарного утверждения типа в HTTP-хэндлерах и микросервисах (крашит процесс).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как избежать паники при утверждении типа?»
**Ответ:** Всегда использовать двухэлементную идиому проверки: `val, ok := v.(T)`.
"""
    },
    {
        "num": 8,
        "title": "Пустой интерфейс any (interface{}) и гетерогенный срез []any",
        "task": "Используйте пустой интерфейс any (или interface{}), чтобы создать слайс, содержащий данные абсолютно разных типов (int, string, struct).",
        "theory": """
**Пустой интерфейс `any` (`interface{}`):**
- Не содержит ни одного метода;
- **Любой тип в Go удовлетворяет пустому интерфейсу**;
- Начиная с Go 1.18, `any` является официальным встроенным алиасом для `interface{}`.
""",
        "step_by_step": """
1. Создаем срез `[]any`.
2. Помещаем `int`, `string`, `bool`, `struct`.
3. Выводим типы и значения.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type User struct {
	Name string
}

func main() {
	heterogeneousSlice := []any{
		42,
		"Сообщение",
		3.1415,
		true,
		User{Name: "Илья"},
		[]byte{0xDE, 0xAD, 0xBE, 0xEF},
	}

	for idx, item := range heterogeneousSlice {
		fmt.Printf("Элемент #%d: Тип = %-18T | Значение = %v\n", idx, item, item)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Элемент #0: Тип = int                | Значение = 42
# Элемент #1: Тип = string             | Значение = Сообщение
# Элемент #2: Тип = float64            | Значение = 3.1415
# Элемент #3: Тип = bool               | Значение = true
# Элемент #4: Тип = main.User          | Значение = {Илья}
# Элемент #5: Тип = []uint8            | Значение = [222 173 190 239]"""
            }
        ],
        "under_the_hood": """
Пустой интерфейс представлен структурой `runtime.eface` (8 байт `_type` + 8 байт `data`).
""",
        "pitfalls": """
- Злоупотребление `[]any` вместо строгой статической типизации (приводит к потере безопасности типов и аллокациям в куче).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем отличие внутреннего представления `iface` и `eface`?»
**Ответ:** `iface` используется для непустых интерфейсов с методами (содержит `*itab` с таблицей методов), а `eface` — для пустых `any` (содержит только простой `*_type` без таблицы методов).
"""
    },
    {
        "num": 9,
        "title": "Безопасное утверждение типа с проверкой Comma-Ok: s, ok := v.(string)",
        "task": "Перепиши через \"comma ok\": s, ok := v.(string). Обработай false без паники. Напиши graceful degradation.",
        "theory": """
**Идиома `comma-ok` для Type Assertion:**
- `val, ok := v.(T)` возвращает `ok == true` и приведенное значение при совпадении типов;
- При несовпадении типов `ok == false`, `val` получает Zero Value типа `T`, и **паника не возникает**!
""",
        "step_by_step": """
1. Пишем безопасную функцию `ExtractString(v any) string`.
2. Проверяем `ok`.
3. Возвращаем дефолтное значение при сбое.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func ExtractString(v any) string {
	// Безопасное утверждение типа без риска паники:
	if str, ok := v.(string); ok {
		return fmt.Sprintf("Найдена строка: %q (длина %d)", str, len(str))
	}
	return fmt.Sprintf("⚠️ Предоставлен не строковый тип (%T)", v)
}

func main() {
	fmt.Println(ExtractString("Успешный текст"))
	fmt.Println(ExtractString(999))
	fmt.Println(ExtractString(nil))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Найдена строка: "Успешный текст" (длина 27)
# ⚠️ Предоставлен не строковый тип (int)
# ⚠️ Предоставлен не строковый тип (<nil>)"""
            }
        ],
        "under_the_hood": """
Инструкция рантайма `runtime.assertE2I` или проверка `eface._type == target_type`.
""",
        "pitfalls": """
- Забыть проверить `if ok` и использовать Zero Value `val`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что вернет `val, ok := v.(string)`, если `v == nil`?»
**Ответ:** Вернет `val = ""` (пустая строка) и `ok = false` без паники.
"""
    },
    {
        "num": 10,
        "title": "Извлечение длины строки через str, ok := v.(string)",
        "task": "Утверждение типа (Type Assertion): Внутри функции попытайся привести v к строке: str, ok := v.(string). Если ok — выведи длину строки, иначе выведи \"Не строка\".",
        "theory": """
Практика безопасной обработки полиморфных текстовых данных.
""",
        "step_by_step": """
1. Пишем `CheckLength(v any)`.
2. Используем `str, ok := v.(string)`.
3. Выводим `len(str)` или сообщение об ошибке.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"unicode/utf8"
)

func CheckLength(v any) {
	if str, ok := v.(string); ok {
		fmt.Printf("Строка %q: байт = %d, символов UTF-8 = %d\n",
			str, len(str), utf8.RuneCountInString(str))
	} else {
		fmt.Printf("Значение %v (%T): Не строка\n", v, v)
	}
}

func main() {
	CheckLength("Привет, Go!")
	CheckLength(100)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Строка "Привет, Go!": байт = 19, символов UTF-8 = 11
# Значение 100 (int): Не строка"""
            }
        ],
        "under_the_hood": """
Пакет `unicode/utf8` декодирует руны.
""",
        "pitfalls": """
- Путаница между байтовой длиной `len(s)` и числом символов `utf8.RuneCountInString`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `len("Привет") == 12`?»
**Ответ:** Потому что каждая кириллическая буква в UTF-8 кодируется 2 байтами.
"""
    },
    {
        "num": 11,
        "title": "Универсальный числовой конвертер ToInt(v any) (int, error) через Type Switch и strconv",
        "task": "Напиши функцию ToInt(v interface{}) (int, error), принимающую int, int8, int16, int32, int64, uint, string (через strconv) и возвращающую int. Используй type switch.",
        "theory": """
**Паттерн гибкого парсинга параметров (Flexible Type Coercion):**
- В микросервисах параметры конфигурации и JSON-поля могут приходить как числами, так и строками;
- `ToInt` нормализует все числовые типы и строковые представления к базовому типу `int`.
""",
        "step_by_step": """
1. Пишем `ToInt(v any) (int, error)`.
2. Обрабатываем `int, int8..int64, uint..uint64, float64, string, bool`.
3. Тестируем все варианты.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"strconv"
)

func ToInt(v any) (int, error) {
	switch val := v.(type) {
	case int:
		return val, nil
	case int8:
		return int(val), nil
	case int16:
		return int(val), nil
	case int32:
		return int(val), nil
	case int64:
		return int(val), nil
	case uint:
		return int(val), nil
	case float64:
		return int(val), nil
	case string:
		n, err := strconv.Atoi(val)
		if err != nil {
			return 0, fmt.Errorf("не удалось преобразовать строку %q в int: %w", val, err)
		}
		return n, nil
	case bool:
		if val {
			return 1, nil
		}
		return 0, nil
	default:
		return 0, fmt.Errorf("неподдерживаемый тип для преобразования в int: %T", v)
	}
}

func main() {
	tests := []any{
		42,
		int32(100),
		"777",
		3.99,
		true,
		"не_число",
	}

	for _, item := range tests {
		val, err := ToInt(item)
		if err != nil {
			fmt.Printf("Вход: %-10v (%-7T) -> Ошибка: %v\n", item, item, err)
		} else {
			fmt.Printf("Вход: %-10v (%-7T) -> int: %d\n", item, item, val)
		}
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вход: 42         (int    ) -> int: 42
# Вход: 100        (int32  ) -> int: 100
# Вход: 777        (string ) -> int: 777
# Вход: 3.99       (float64) -> int: 3
# Вход: true       (bool   ) -> int: 1
# Вход: не_число   (string ) -> Ошибка: не удалось преобразовать строку "не_число" в int: strconv.Atoi: parsing "не_число": invalid syntax"""
            }
        ],
        "under_the_hood": """
Type Switch использует оптимизированный jump-table компилятора.
""",
        "pitfalls": """
- Переполнение `int` при конвертации `int64` на 32-битных платформах.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в стандартной библиотеке Go парсятся нетипизированные JSON-числа?»
**Ответ:** Через тип `json.Number` (строковая обертка с методами `Int64()` и `Float64()`) или декодер `UseNumber()`.
"""
    },
    {
        "num": 12,
        "title": "Объявление интерфейса геометрических фигур Shape с методом Area() float64",
        "task": "Создай интерфейс Shape с методом Area() float64.",
        "theory": """
Базовый интерфейс контракта расчета площади.
""",
        "step_by_step": """
1. Объявляем `type Shape interface { Area() float64 }`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Shape interface {
	Area() float64
}

type Square struct {
	Side float64
}

func (s Square) Area() float64 {
	return s.Side * s.Side
}

func main() {
	var sh Shape = Square{Side: 5.0}
	fmt.Printf("Площадь квадрата: %.2f\n", sh.Area())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Площадь квадрата: 25.00"""
            }
        ],
        "under_the_hood": """
Таблица `itab` содержит один метод `Area`.
""",
        "pitfalls": """
- Добавление лишних методов в интерфейс без реальной потребности.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go популярны однометодные интерфейсы (`io.Reader`, `fmt.Stringer`)?»
**Ответ:** Однометодные интерфейсы обеспечивают максимальную гибкость и следование принципу Interface Segregation Principle (ISP).
"""
    },
    {
        "num": 13,
        "title": "Простейший интерфейс Greeter: структуры Russian и English, функция SaySomething(g Greeter)",
        "task": "Простейший интерфейс: Создайте интерфейс Greeter с методом Greet() string. Создайте структуру Russian и структуру English. Реализуйте этот метод для обеих структур (без явного указания implements!). Напишите функцию SaySomething(g Greeter), принимающую интерфейс, и передайте туда оба типа.",
        "theory": """
Интерфейс как граница между модулями.
""",
        "step_by_step": """
1. Объявляем `Russian` и `English`.
2. Пишем функцию `SaySomething(g Greeter)`.
3. Вызываем для обоих типов.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Greeter interface {
	Greet() string
}

type Russian struct{}

func (Russian) Greet() string {
	return "Привет, мир!"
}

type English struct{}

func (English) Greet() string {
	return "Hello, world!"
}

func SaySomething(g Greeter) {
	fmt.Println("Приветствие:", g.Greet())
}

func main() {
	SaySomething(Russian{})
	SaySomething(English{})
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Приветствие: Привет, мир!
# Приветствие: Hello, world!"""
            }
        ],
        "under_the_hood": """
Прямой вызов через интерфейсный указатель.
""",
        "pitfalls": """
- Создание интерфейса в том же пакете, где определены структуры (лучше определять интерфейс на стороне потребителя).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Где в Go идиоматично объявлять интерфейсы: на стороне создателя типа (producer) или потребителя (consumer)?»
**Ответ:** На стороне потребителя (consumer), так как потребитель точно знает, какие методы ему требуются.
"""
    },
    {
        "num": 14,
        "title": "Интерфейс Shape с Area() и Perimeter(): структуры Rectangle и Circle в срезе []Shape",
        "task": "Интерфейс геометрических фигур: Создайте интерфейс Shape с методами Area() float64 и Perimeter() float64. Реализуйте его для структур Rectangle и Circle. Создайте срез []Shape, наполните его разными фигурами и в цикле выведите площадь каждой.",
        "theory": """
Интерфейсы с несколькими методами.
""",
        "step_by_step": """
1. Объявляем `Shape` с методами `Area()` и `Perimeter()`.
2. Реализуем для `Rectangle` и `Circle`.
3. Итерируемся по срезу `[]Shape`.
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

type Shape interface {
	Area() float64
	Perimeter() float64
}

type Rectangle struct {
	Width, Height float64
}

func (r Rectangle) Area() float64      { return r.Width * r.Height }
func (r Rectangle) Perimeter() float64 { return 2 * (r.Width + r.Height) }

type Circle struct {
	Radius float64
}

func (c Circle) Area() float64      { return math.Pi * c.Radius * c.Radius }
func (c Circle) Perimeter() float64 { return 2 * math.Pi * c.Radius }

func main() {
	shapes := []Shape{
		Rectangle{Width: 10, Height: 5},
		Circle{Radius: 4},
		Rectangle{Width: 3, Height: 3},
	}

	for idx, sh := range shapes {
		fmt.Printf("Фигура #%d: Площадь = %6.2f | Периметр = %6.2f\n",
			idx+1, sh.Area(), sh.Perimeter())
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Фигура #1: Площадь =  50.00 | Периметр =  30.00
# Фигура #2: Площадь =  50.27 | Периметр =  25.13
# Фигура #3: Площадь =   9.00 | Периметр =  12.00"""
            }
        ],
        "under_the_hood": """
`itab` содержит 2 слота в массиве методов `fun[0]` и `fun[1]`.
""",
        "pitfalls": """
- Реализация только одного метода из двух (структура не будет удовлетворять интерфейсу).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что будет, если структура реализует `Area()`, но забыла `Perimeter()`?»
**Ответ:** Ошибка компиляции `does not implement Shape (missing method Perimeter)`.
"""
    },
    {
        "num": 15,
        "title": "Агрегация метрик фигур: функция TotalMetrics(shapes []Shape) (totalArea, totalPerimeter float64)",
        "task": "Напишите функцию, принимающую срез Shape и выводящую суммарную площадь и периметр.",
        "theory": """
Агрегирующие функции над интерфейсными срезами.
""",
        "step_by_step": """
1. Пишем `TotalMetrics(shapes []Shape) (float64, float64)`.
2. Суммируем площади и периметры.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Shape interface {
	Area() float64
	Perimeter() float64
}

type Square struct{ Side float64 }

func (s Square) Area() float64      { return s.Side * s.Side }
func (s Square) Perimeter() float64 { return 4 * s.Side }

func TotalMetrics(shapes []Shape) (totalArea, totalPerimeter float64) {
	for _, sh := range shapes {
		totalArea += sh.Area()
		totalPerimeter += sh.Perimeter()
	}
	return
}

func main() {
	shapes := []Shape{
		Square{Side: 2.0}, // S=4, P=8
		Square{Side: 3.0}, // S=9, P=12
	}

	area, perim := TotalMetrics(shapes)
	fmt.Printf("Итоговая площадь: %.2f | Итоговый периметр: %.2f\n", area, perim)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Итоговая площадь: 13.00 | Итоговый периметр: 20.00"""
            }
        ],
        "under_the_hood": """
Итератор вызывает методы через указатели `itab`.
""",
        "pitfalls": """
- Передача пустого или nil-среза (корректно вернет 0, 0).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как повысить производительность суммирования миллионов фигур?»
**Ответ:** Использовать конкретный тип данных вместо интерфейсов `[]Square` для устранения indirect call и поддержки векторизации SIMD.
"""
    },
    {
        "num": 16,
        "title": "Type Switch: switch val := v.(type) с обработкой базовых типов",
        "task": "Type Switch: Перепиши с использованием конструкции switch val := v.(type) { case string: ... case int: ... default: ... }.",
        "theory": """
Закрепление синтаксиса Type Switch.
""",
        "step_by_step": """
1. Пишем `DescribeType(v any)`.
2. Обрабатываем `int`, `string`, `default`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func DescribeType(v any) {
	switch val := v.(type) {
	case string:
		fmt.Printf("Строковый тип: %q\n", val)
	case int:
		fmt.Printf("Целое число: %d\n", val)
	default:
		fmt.Printf("Прочий тип: %v\n", val)
	}
}

func main() {
	DescribeType("Привет")
	DescribeType(100)
	DescribeType(3.14)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Строковый тип: "Привет"
# Целое число: 100
# Прочий тип: 3.14"""
            }
        ],
        "under_the_hood": """
Компилятор строит таблицу типов `type_descriptor`.
""",
        "pitfalls": """
- Использование fallthrough в Type Switch (запрещено спецификацией Go).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Разрешен ли `fallthrough` в `type switch`?»
**Ответ:** НЕТ! В `type switch` оператор `fallthrough` запрещен, так как тип переменной не может быть одновременно двумя разными типами.
"""
    },
    {
        "num": 17,
        "title": "Универсальная функция печати PrintAnything(v any) для чисел, строк и структур",
        "task": "Используй пустой интерфейс interface{} (или алиас any) для создания функции PrintAnything(v any). Передай в неё число, строку и структуру.",
        "theory": """
Прием произвольных аргументов через `any`.
""",
        "step_by_step": """
1. Создаем функцию `PrintAnything(v any)`.
2. Печатаем через `%v (%T)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Order struct {
	ID    int
	Total float64
}

func PrintAnything(v any) {
	fmt.Printf("Значение: %+v | Тип: %T\n", v, v)
}

func main() {
	PrintAnything(1024)
	PrintAnything("Универсальный интерфейс")
	PrintAnything(Order{ID: 1, Total: 4990.50})
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Значение: 1024 | Тип: int
# Значение: Универсальный интерфейс | Тип: string
# Значение: {ID:1 Total:4990.5} | Тип: main.Order"""
            }
        ],
        "under_the_hood": """
Упаковка объекта в `runtime.convT`.
""",
        "pitfalls": """
- Упаковка примитива `int` в интерфейс вызывает небольшую аллокацию в куче, если компилятор не может ее оптимизировать.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему передача `int` в `any` может приводить к аллокации памяти?»
**Ответ:** Потому что интерфейс хранит указатель на данные `data`, и если значение больше машинного слова или его адрес убегает, рантайм выделяет память в куче через `runtime.convT64`.
"""
    },
    {
        "num": 18,
        "title": "Неявное удовлетворение интерфейсу Shape структурами Circle и Rectangle",
        "task": "Создай структуры Circle и Rectangle. Реализуй для них метод Area(). (Теперь они неявно удовлетворяют интерфейсу Shape).",
        "theory": """
Однометодный интерфейс `Shape` и структуры.
""",
        "step_by_step": """
1. Создаем интерфейс `Shape`.
2. Реализуем `Area()` для `Circle` и `Rectangle`.
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

type Shape interface {
	Area() float64
}

type Circle struct{ R float64 }

func (c Circle) Area() float64 { return math.Pi * c.R * c.R }

type Rectangle struct{ W, H float64 }

func (r Rectangle) Area() float64 { return r.W * r.H }

func main() {
	var s1 Shape = Circle{R: 3}
	var s2 Shape = Rectangle{W: 4, H: 5}

	fmt.Printf("Circle Area:    %.2f\n", s1.Area())
	fmt.Printf("Rectangle Area: %.2f\n", s2.Area())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Circle Area:    28.27
# Rectangle Area: 20.00"""
            }
        ],
        "under_the_hood": """
Статическая проверка соответствия типов на этапе компиляции.
""",
        "pitfalls": """
- Опечатка в имени метода `area()` со строчной буквы (не экспортированный метод).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Имеет ли значение регистр первой буквы метода в интерфейсе?»
**Ответ:** ДА! Экспортируемые методы начинаются с заглавной буквы (`Area`), неэкспортируемые — со строчной (`area`).
"""
    },
    {
        "num": 19,
        "title": "Реализация интерфейса io.Reader для структуры MyBuffer и чтение через io.ReadAll",
        "task": "Реализуй io.Reader для структуры MyBuffer (метод Read(p []byte) (n int, err error)). Прочитай из неё через io.ReadAll и сравни содержимое.",
        "theory": """
**Стандартный контракт `io.Reader`:**
- Сигнатура: `Read(p []byte) (n int, err error)`;
- Заполняет переданный буфер `p`, возвращает число прочитанных байт `n` и `io.EOF` при достижении конца потока;
- Ключевой фундамент всей потоковой экосистемы Go.
""",
        "step_by_step": """
1. Создаем структуру `MyBuffer{data []byte, offset int}`.
2. Реализуем метод `Read(p []byte) (int, error)`.
3. Читаем через `io.ReadAll(buf)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"io"
)

type MyBuffer struct {
	data   []byte
	offset int
}

func NewMyBuffer(text string) *MyBuffer {
	return &MyBuffer{data: []byte(text)}
}

func (b *MyBuffer) Read(p []byte) (n int, err error) {
	if b.offset >= len(b.data) {
		return 0, io.EOF
	}

	n = copy(p, b.data[b.offset:])
	b.offset += n
	return n, nil
}

func main() {
	buf := NewMyBuffer("Потоковые данные из MyBuffer!")

	allBytes, err := io.ReadAll(buf)
	if err != nil {
		panic(err)
	}

	fmt.Printf("Прочитано: %q (всего %d байт)\n", string(allBytes), len(allBytes))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Прочитано: "Потоковые данные из MyBuffer!" (всего 48 байт)"""
            }
        ],
        "under_the_hood": """
`io.ReadAll` циклически вызывает `buf.Read` с динамическим расширением слайса.
""",
        "pitfalls": """
- Забыть вернуть `io.EOF` в конце данных (приведет к бесконечному циклу в `io.ReadAll`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Может ли `Read` вернуть одновременно `n > 0` и `err == io.EOF`?»
**Ответ:** ДА! Спецификация `io.Reader` разрешает вернуть последние прочитанные байты вместе с ошибкой `io.EOF`.
"""
    },
    {
        "num": 20,
        "title": "Каверзный кейс: Value vs Pointer Receiver в интерфейсах и ошибка Method Set",
        "task": "Каверзный случай: Value vs Pointer Receiver: Реализуй метод Speak() для *Dog (по указателю). Попробуй положить в срез []Speaker значение Dog{} (без &). Изучи ошибку: интерфейс не реализован для значения, только для указателя!",
        "theory": """
**Правила Method Set в Go:**
- **Для значения типа `T`:** Method Set содержит только методы с **Value Receiver `(t T)`**;
- **Для указателя типа `*T`:** Method Set содержит **И методы `(t T)`, И методы `(t *T)`**;
- Поэтому если метод объявлен на `*Dog`, значение `Dog{}` **НЕ реализует интерфейс**!
""",
        "step_by_step": """
1. Создаем структуру `Dog` с методом `(d *Dog) Speak() string`.
2. Показываем ошибку при попытке положить `Dog{}` в интерфейс.
3. Исправляем передачей указателя `&Dog{}`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Speaker interface {
	Speak() string
}

type Dog struct {
	Name string
}

// Метод объявлен СТРОГО на указателе *Dog:
func (d *Dog) Speak() string {
	return d.Name + ": Гав!"
}

func main() {
	// ❌ ОШИБКА КОМПИЛЯЦИИ:
	// var s Speaker = Dog{Name: "Шарик"}
	// cannot use Dog{...} as Speaker value: Dog does not implement Speaker (Speak method has pointer receiver)

	// ✅ ПРАВИЛЬНО: передавать указатель &Dog:
	var s Speaker = &Dog{Name: "Шарик"}
	fmt.Println("Интерфейсный вызов:", s.Speak())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Интерфейсный вызов: Шарик: Гав!"""
            }
        ],
        "under_the_hood": """
Компилятор проверяет Method Set типа во время тайпчекинга. Для `Dog` таблица методов пуста.
""",
        "pitfalls": """
- Попытка передать неадресуемое значение структуры в интерфейс, ожидающий pointer receiver.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему значение `T` не может автоматически вызывать pointer-методы внутри интерфейса?»
**Ответ:** Потому что значение внутри интерфейса копируется и не является адресуемым; взятие адреса от копии внутри интерфейса привело бы к мутации временной копии, а не исходного объекта.
"""
    },
    {
        "num": 21,
        "title": "Безопасное извлечение строки из переменной any: val, ok := myVar.(string)",
        "task": "Примените утверждение типа (type assertion) val, ok := myVar.(string), чтобы безопасно извлечь строку из переменной типа any без паники.",
        "theory": """
Практика защитного программирования.
""",
        "step_by_step": """
1. Создаем переменную `var myVar any = "Go 1.22"`.
2. Извлекаем через `val, ok := myVar.(string)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	var myVar any = "Стандарты разработки в Go"

	if str, ok := myVar.(string); ok {
		fmt.Printf("Успешно извлечено: %q\n", str)
	} else {
		fmt.Println("Ошибка: значение не является строкой")
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Успешно извлечено: "Стандарты разработки в Go" """
            }
        ],
        "under_the_hood": """
Прямая проверка типа.
""",
        "pitfalls": """
- Игнорирование переменной `ok`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что происходит при успешном Type Assertion?»
**Ответ:** Рантайм копирует данные из интерфейса `eface.data` в целевую типизированную переменную `str`.
"""
    },
    {
        "num": 22,
        "title": "Полиморфная функция PrintArea(s Shape) для круга и прямоугольника",
        "task": "Напиши функцию PrintArea(s Shape), которая принимает интерфейс. Передай в неё круг и прямоугольник.",
        "theory": """
Универсальный вывод площадей.
""",
        "step_by_step": """
1. Пишем `PrintArea(s Shape)`.
2. Передаем различные геометрические фигуры.
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

type Shape interface {
	Area() float64
}

type Circle struct{ Radius float64 }

func (c Circle) Area() float64 { return math.Pi * c.Radius * c.Radius }

type Rectangle struct{ W, H float64 }

func (r Rectangle) Area() float64 { return r.W * r.H }

func PrintArea(s Shape) {
	fmt.Printf("Площадь фигуры (%T): %.2f кв. ед.\n", s, s.Area())
}

func main() {
	PrintArea(Circle{Radius: 5})
	PrintArea(Rectangle{W: 10, H: 4})
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Площадь фигуры (main.Circle): 78.54 кв. ед.
# Площадь фигуры (main.Rectangle): 40.00 кв. ед."""
            }
        ],
        "under_the_hood": """
Форматирование `%T` обращается к имени типа в `itab._type`.
""",
        "pitfalls": """
- Передача `nil` в `PrintArea`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как `fmt.Printf("%T")` узнает точный тип структуры внутри интерфейса?»
**Ответ:** Через поле `itab._type.string()` метаданных типа рантайма.
"""
    },
    {
        "num": 23,
        "title": "Инспекция вариативных аргументов: функция PrintAll(v ...any)",
        "task": "Пустой интерфейс: функция PrintAll(v ...interface{}), которая печатает тип и значение каждого элемента.",
        "theory": """
Сочетание `...any` и рефлексивной печати типов.
""",
        "step_by_step": """
1. Пишем `PrintAll(items ...any)`.
2. Итерируемся по элементам.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func PrintAll(items ...any) {
	for i, item := range items {
		fmt.Printf("  [%d] Тип: %-10T | Значение: %v\n", i, item, item)
	}
}

func main() {
	fmt.Println("Список аргументов:")
	PrintAll(100, "Go", 3.14, false, []int{1, 2})
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Список аргументов:
#   [0] Тип: int        | Значение: 100
#   [1] Тип: string     | Значение: Go
#   [2] Тип: float64    | Значение: 3.14
#   [3] Тип: bool       | Значение: false
#   [4] Тип: []int      | Значение: [1 2]"""
            }
        ],
        "under_the_hood": """
`items` формируется как срез `[]any` из 16-байтных структур.
""",
        "pitfalls": """
- Передача готового среза `PrintAll(mySlice)` vs `PrintAll(mySlice...)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как устроен `fmt.Println` внутри?»
**Ответ:** Сигнатура `fmt.Println(a ...any)` принимает срез пустых интерфейсов и последовательно форматирует каждый элемент через внутренний буфер.
"""
    },
    {
        "num": 24,
        "title": "Реализация интерфейса io.Writer для MyBuffer и запись через fmt.Fprintf",
        "task": "Реализуй io.Writer для MyBuffer. Напиши в неё через fmt.Fprintf. Покажи, что MyBuffer теперь можно использовать везде, где ожидается io.Writer.",
        "theory": """
**Стандартный контракт `io.Writer`:**
- Сигнатура: `Write(p []byte) (n int, err error)`;
- Записывает байты из `p` в целевой поток;
- Позволяет подключать `MyBuffer` к любым сетевым, файловым и форматирующим функциям standard library.
""",
        "step_by_step": """
1. Создаем структуру `MyBuffer{data []byte}`.
2. Пишем метод `(b *MyBuffer) Write(p []byte) (int, error)`.
3. Пишем в буфер через `fmt.Fprintf(buf, "...")`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"io"
)

type MyBuffer struct {
	data []byte
}

func (b *MyBuffer) Write(p []byte) (n int, err error) {
	b.data = append(b.data, p...)
	return len(p), nil
}

func (b *MyBuffer) String() string {
	return string(b.data)
}

func main() {
	buf := &MyBuffer{}

	// Используем MyBuffer везде, где требуется io.Writer:
	var w io.Writer = buf
	fmt.Fprintf(w, "Пользователь #%d: баланс %.2f руб.\n", 101, 1500.75)

	fmt.Printf("Содержимое буфера:\n%s", buf.String())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Содержимое буфера:
# Пользователь #101: баланс 1500.75 руб."""
            }
        ],
        "under_the_hood": """
`fmt.Fprintf` вызывает `w.Write()` через виртуальную таблицу интерфейса `io.Writer`.
""",
        "pitfalls": """
- Объявление `Write` с Value Receiver `(b MyBuffer)` (будет мутировать локальную копию буфера и терять данные!).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему для `io.Writer` всегда используется Pointer Receiver?»
**Ответ:** Потому что запись по своей сути изменяет состояние буфера/файла/сокета, что требует сохранения мутаций в исходном объекте.
"""
    },
    {
        "num": 25,
        "title": "Реализация составного интерфейса io.ReadWriter единым буфером памяти",
        "task": "Создай структуру, реализующую io.ReadWriter (оба интерфейса одновременно). Покажи, что она удовлетворяет составному интерфейсу.",
        "theory": """
**Составной интерфейс `io.ReadWriter`:**
- Включает оба метода: `Read(p []byte) (int, error)` и `Write(p []byte) (int, error)`;
- Любой тип, реализующий оба метода, автоматически удовлетворяет `io.ReadWriter`.
""",
        "step_by_step": """
1. Создаем структуру `MemoryStream`.
2. Реализуем методы `Read` и `Write`.
3. Присваиваем `var rw io.ReadWriter = &MemoryStream{}`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"io"
)

type MemoryStream struct {
	buf    []byte
	offset int
}

func (m *MemoryStream) Write(p []byte) (int, error) {
	m.buf = append(m.buf, p...)
	return len(p), nil
}

func (m *MemoryStream) Read(p []byte) (int, error) {
	if m.offset >= len(m.buf) {
		return 0, io.EOF
	}
	n := copy(p, m.buf[m.offset:])
	m.offset += n
	return n, nil
}

func main() {
	var rw io.ReadWriter = &MemoryStream{}

	// 1. Запись:
	rw.Write([]byte("Сквозной поток данных"))

	// 2. Чтение:
	readData := make([]byte, 64)
	n, _ := rw.Read(readData)

	fmt.Printf("Прочитано из ReadWriter: %q\n", string(readData[:n]))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Прочитано из ReadWriter: "Сквозной поток данных" """
            }
        ],
        "under_the_hood": """
`itab` для `io.ReadWriter` объединяет методы `Read` и `Write`.
""",
        "pitfalls": """
- Чтение до записи или без сброса смещения.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какая стандартная структура в пакете `bytes` реализует `io.ReadWriter`?»
**Ответ:** Структура `*bytes.Buffer`.
"""
    },
    {
        "num": 26,
        "title": "Композиция интерфейсов: объединение Runner и Swimmer в интерфейс Triathlete",
        "task": "Композиция интерфейсов: Создай интерфейс Runner и Swimmer. Создай интерфейс Triathlete, который встраивает в себя оба предыдущих интерфейса.",
        "theory": """
**Встраивание интерфейсов в интерфейсы (Interface Embedding):**
- Интерфейс может встраивать другие интерфейсы;
- Итоговый интерфейс требует реализации объединения всех методов встроенных интерфейсов.
""",
        "step_by_step": """
1. Создаем интерфейсы `Runner` (`Run() string`) и `Swimmer` (`Swim() string`).
2. Объявляем `type Triathlete interface { Runner; Swimmer }`.
3. Создаем структуру `Athlete` и реализуем оба метода.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Runner interface {
	Run() string
}

type Swimmer interface {
	Swim() string
}

type Triathlete interface {
	Runner
	Swimmer
}

type Athlete struct {
	Name string
}

func (a Athlete) Run() string {
	return a.Name + " бежит 10 км"
}

func (a Athlete) Swim() string {
	return a.Name + " плывет 1.5 км"
}

func PerformTriathlon(t Triathlete) {
	fmt.Println("Старт соревнований:")
	fmt.Println("  •", t.Swim())
	fmt.Println("  •", t.Run())
}

func main() {
	athlete := Athlete{Name: "Алексей"}
	PerformTriathlon(athlete)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Старт соревнований:
#   • Алексей плывет 1.5 км
#   • Алексей бежит 10 км"""
            }
        ],
        "under_the_hood": """
Таблица методов `Triathlete` генерируется компилятором как объединение наборов методов.
""",
        "pitfalls": """
- Дублирование методов с одинаковыми именами, но разными сигнатурами (ошибка компиляции).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли встроить в интерфейс два других интерфейса с одинаковым методом `Close() error`?»
**Ответ:** Да! Начиная с Go 1.14 разрешено дублирование методов в пересекающихся интерфейсах, если их сигнатуры полностью идентичны.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 1: {len(exercises)} exercises.")
