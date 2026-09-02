# Chapter 10 Part 2: Exercises 26 to 50

exercises = [
    {
        "num": 26,
        "title": "Функция сложения двух целых чисел Add(a, b int) int",
        "task": "Напиши функцию Add(a, b int) int.",
        "theory": """
Базовая сигнатура функции с двумя аргументами и одним возвращаемым значением.
""",
        "step_by_step": """
1. Пишем `Add(a, b int) int`.
2. Возвращаем `a + b`.
3. Тестируем вызов.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Add(a, b int) int {
	return a + b
}

func main() {
	res := Add(15, 27)
	fmt.Printf("15 + 27 = %d\n", res)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 15 + 27 = 42"""
            }
        ],
        "under_the_hood": """
Компилятор выполняет инлайнинг функции `Add` (заменяя вызов функции на машинную инструкцию `ADDQ`).
""",
        "pitfalls": """
- Переполнение `int` при сложении экстремальных значений `math.MaxInt`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «При каких условиях компилятор Go инлайнит функцию?»
**Ответ:** Если функция достаточно простая (стоимость AST-узлов $< 80$), не содержит `defer`, `recover`, `go` и не является рекурсивной или слишком длинной.
"""
    },
    {
        "num": 27,
        "title": "Отложенное завершение defer в функции main: гарантия финализации",
        "task": "Используйте ключевое слово defer для отложенного вывода сообщения \"Программа завершена\" в конце функции main.",
        "theory": """
Оператор `defer` регистрирует вызов, который гарантированно выполнится при любом выходе из функции `main` (включая преждевременный `return`).
""",
        "step_by_step": """
1. Ставим `defer fmt.Println("Программа завершена")` в начале `main()`.
2. Выполняем полезную работу.
3. Наблюдаем вывод.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	defer fmt.Println("🏁 Программа завершена (вызвано через defer)")

	fmt.Println("1. Инициализация сервиса...")
	fmt.Println("2. Обработка входящих запросов...")
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Инициализация сервиса...
# 2. Обработка входящих запросов...
# 🏁 Программа завершена (вызвано через defer)"""
            }
        ],
        "under_the_hood": """
Вызов `defer` трансформируется в вызов `runtime.deferproc` или открытый defer (Open-coded defer в Go 1.14+).
""",
        "pitfalls": """
- `os.Exit(1)` обходит вызовы `defer`! Если в коде вызван `os.Exit()`, ни один `defer` не выполнится.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Выполнятся ли `defer` при вызове `os.Exit(0)` или получении `SIGKILL`?»
**Ответ:** НЕТ! `os.Exit` немедленно завершает процесс через системный вызов `exit_group`, минуя рантайм Go.
"""
    },
    {
        "num": 28,
        "title": "Метод изменения размеров структуры Rectangle с указателем-получателем (Pointer Receiver)",
        "task": "Реализуйте метод для структуры Rectangle, изменяющий её размеры (получатель-указатель).",
        "theory": """
**Указатель-получатель `(r *Rectangle)` для мутации структуры:**
- Позволяет методам изменять поля `Width` и `Height`;
- Предотвращает нежелательное копирование данных.
""",
        "step_by_step": """
1. Создаем структуру `Rectangle{Width, Height float64}`.
2. Пишем метод `func (r *Rectangle) Scale(factor float64)`.
3. Масштабируем фигуру.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Rectangle struct {
	Width, Height float64
}

func (r *Rectangle) Scale(factor float64) {
	if r == nil {
		return
	}
	r.Width *= factor
	r.Height *= factor
}

func main() {
	rect := Rectangle{Width: 10, Height: 5}
	fmt.Printf("До масштабирования:   %+v\n", rect)

	rect.Scale(2.5)

	fmt.Printf("После rect.Scale(2.5): %+v (РАЗМЕРЫ ИЗМЕНЕНЫ!)\n", rect)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До масштабирования:   {Width:10 Height:5}
# После rect.Scale(2.5): {Width:25 Height:12.5} (РАЗМЕРЫ ИЗМЕНЕНЫ!)"""
            }
        ],
        "under_the_hood": """
Go автоматически берет адрес `(&rect).Scale(2.5)`.
""",
        "pitfalls": """
- Смешивание value и pointer получателей для одного типа (нарушение согласованности API).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каково общее правило Go по выбору получателя метода?»
**Ответ:** Если хотя бы один метод типа требует указатель (для мутации или из-за размера), ВСЕ методы этого типа должны иметь pointer receiver.
"""
    },
    {
        "num": 29,
        "title": "Реализация стандартного интерфейса fmt.Stringer (метод String()) для структуры",
        "task": "Объявите интерфейс Stringer с методом String() string и реализуйте его для вашей структуры; используйте в fmt.Println.",
        "theory": """
**Контракт `fmt.Stringer`:**
- Интерфейс `type Stringer interface { String() string }`;
- Любой тип, реализующий этот метод, автоматически форматируется функциями `fmt.Print`, `fmt.Println`, `fmt.Sprintf("%s", ...)`.
""",
        "step_by_step": """
1. Создаем `type User struct { ID int; Name string; Role string }`.
2. Реализуем метод `func (u User) String() string`.
3. Печатаем через `fmt.Println`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type User struct {
	ID   int
	Name string
	Role string
}

func (u User) String() string {
	return fmt.Sprintf("Пользователь #%d: %s [%s]", u.ID, u.Name, u.Role)
}

func main() {
	admin := User{ID: 1, Name: "Алексей", Role: "Admin"}
	// fmt.Println автоматически вызывает метод String():
	fmt.Println(admin)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Пользователь #1: Алексей [Admin]"""
            }
        ],
        "under_the_hood": """
`fmt.Println` проверяет реализацию интерфейса через рефлексию/таблицу `itab`.
""",
        "pitfalls": """
- Вызов `fmt.Sprintf("%s", u)` внутри метода `String()`: вызовет бесконечную рекурсию и Stack Overflow!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему бесконечная рекурсия возникает в `func (u User) String() string { return fmt.Sprintf("%v", u) }`?»
**Ответ:** Потому что `%v` видит интерфейс `fmt.Stringer` и повторно вызывает метод `String()`. Чтобы распечатать поля, нужно использовать `fmt.Sprintf("%+v", u.ID...)` или приведение к базовому типу.
"""
    },
    {
        "num": 30,
        "title": "Сокращенный синтаксис параметров функции SumThree(a, b, c int) int",
        "task": "Сокращенный синтаксис параметров: Напишите функцию SumThree(a, b, c int) int, демонстрирующую группировку однотипных аргументов.",
        "theory": """
**Группировка однотипных аргументов:**
- Синтаксис `func SumThree(a, b, c int) int` эквивалентен `func SumThree(a int, b int, c int) int`;
- Повышает компактность и читаемость сигнатур.
""",
        "step_by_step": """
1. Пишем `SumThree(a, b, c int) int`.
2. Возвращаем `a + b + c`.
3. Тестируем.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func SumThree(a, b, c int) int {
	return a + b + c
}

func main() {
	res := SumThree(10, 20, 30)
	fmt.Printf("SumThree(10, 20, 30) = %d\n", res)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# SumThree(10, 20, 30) = 60"""
            }
        ],
        "under_the_hood": """
Аргументы передаются в регистрах `RAX`, `RBX`, `RCX`.
""",
        "pitfalls": """
- Неправильная группировка при разных типах: `func Foo(a, b int, c string)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Разрешена ли группировка типов для возвращаемых параметров?»
**Ответ:** ДА! Например: `func Split(s string) (prefix, suffix string)`.
"""
    },
    {
        "num": 31,
        "title": "Идиома Resource Cleanup через defer: гарантированное закрытие дескрипторов",
        "task": "Напишите функцию, которая открывает файл (эмулируя), и используйте defer для гарантированного закрытия файла.",
        "theory": """
**Паттерн RAII / Defer Cleanup:**
- Открытие ресурса;
- Проверка `if err != nil { return err }`;
- Немедленная регистрация `defer resource.Close()`;
- Гарантирует освобождение дескриптора при любых последующих ошибках и паниках.
""",
        "step_by_step": """
1. Эмулируем структуру `File`.
2. Пишем функцию безопасной обработки файла.
3. Проверяем порядок выполнения.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type MockFile struct {
	Name string
}

func OpenFile(name string) (*MockFile, error) {
	fmt.Printf("📂 Файл %q успешно открыт\n", name)
	return &MockFile{Name: name}, nil
}

func (f *MockFile) Close() {
	fmt.Printf("🔒 Файл %q гарантированно закрыт!\n", f.Name)
}

func ProcessFile(name string) error {
	file, err := OpenFile(name)
	if err != nil {
		return err
	}
	defer file.Close() // Гарантия закрытия ресурса!

	fmt.Println("  ⚡ Чтение и обработка данных...")
	return nil
}

func main() {
	_ = ProcessFile("app.log")
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 📂 Файл "app.log" успешно открыт
#   ⚡ Чтение и обработка данных...
# 🔒 Файл "app.log" гарантированно закрыт!"""
            }
        ],
        "under_the_hood": """
`defer` вызывается в эпилоге функции перед возвратом управления.
""",
        "pitfalls": """
- Размещение `defer file.Close()` ДО проверки `if err != nil`: если `file == nil`, вызов `defer nil.Close()` приведет к панике!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `defer file.Close()` ставят СТРОГО ПОСЛЕ `if err != nil`?»
**Ответ:** Потому что при ошибке открытия объект равен `nil`, и отложенный вызов метода разыменует `nil`-указатель при выходе из функции.
"""
    },
    {
        "num": 32,
        "title": "Инспекция динамических типов пустого интерфейса any через Type Switch v.(type)",
        "task": "Напишите функцию, принимающую пустой интерфейс interface{}, и примените утверждение типа .(type).",
        "theory": """
**Type Switch над интерфейсом `any` (`interface{}`):**
- Синтаксис: `switch v := val.(type)`;
- Позволяет безопасно определить фактический конкретный тип значения в рантайме;
- Внутри каждой ветки `case T:` переменная `v` имеет конкретный тип `T`.
""",
        "step_by_step": """
1. Пишем `InspectType(val any)`.
2. Реализуем ветки для `int`, `string`, `bool`, `[]int`.
3. Тестируем на различных типах данных.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func InspectType(val any) {
	switch v := val.(type) {
	case int:
		fmt.Printf("Целое число: %d (квадрат: %d)\n", v, v*v)
	case string:
		fmt.Printf("Строка: %q (длина: %d байт)\n", v, len(v))
	case bool:
		fmt.Printf("Булево значение: %t\n", v)
	case []int:
		fmt.Printf("Срез чисел: %v (элементов: %d)\n", v, len(v))
	default:
		fmt.Printf("Неизвестный тип: %T\n", v)
	}
}

func main() {
	InspectType(42)
	InspectType("Golang")
	InspectType(true)
	InspectType([]int{1, 2, 3})
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Целое число: 42 (квадрат: 1764)
# Строка: "Golang" (длина: 6 байт)
# Булево значение: true
# Срез чисел: [1 2 3] (элементов: 3)"""
            }
        ],
        "under_the_hood": """
Рантайм сравнивает дескриптор типа `_type` в структуре интерфейса `eface`.
""",
        "pitfalls": """
- Использование `.(type)` вне конструкции `switch`: вызовет ошибку компиляции (синтаксис `.(type)` разрешен ТОЛЬКО в `switch`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова структура пустого интерфейса `any` в памяти рантайма Go?»
**Ответ:** Структура `eface` из двух 8-байтных указателей: `_type` (метаданные типа) и `data` (указатель на само значение в куче).
"""
    },
    {
        "num": 33,
        "title": "Функция вычисления площади прямоугольника Area(w, h float64) float64",
        "task": "Функция с возвратом: Напиши функцию для вычисления площади прямоугольника.",
        "theory": """
Базовая чистая функция (Pure Function) без побочных эффектов.
""",
        "step_by_step": """
1. Пишем `Area(w, h float64) float64`.
2. Возвращаем `w * h`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Area(width, height float64) float64 {
	return width * height
}

func main() {
	fmt.Printf("Площадь: %.2f кв. ед.\n", Area(12.5, 4.0))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Площадь: 50.00 кв. ед."""
            }
        ],
        "under_the_hood": """
Инструкция `MULSD` процессора x86-64.
""",
        "pitfalls": """
- Отрицательные стороны (валидация при необходимости).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что такое чистая функция (Pure Function)?»
**Ответ:** Функция, результат которой зависит только от переданных аргументов и которая не имеет побочных эффектов (Side Effects: мутация глобальных переменных, I/O).
"""
    },
    {
        "num": 34,
        "title": "Функция, возвращающая замыкание с захватом внешнего смещения",
        "task": "Напиши функцию, которая возвращает другую функцию (замыкание/closure). Возвращаемая функция должна прибавлять к своему аргументу число, захваченное из внешней функции.",
        "theory": """
Закрепление фабрики замыканий (Closure Factory Pattern).
""",
        "step_by_step": """
1. Пишем `MakeAdder(offset int) func(int) int`.
2. Создаем `plusFive := MakeAdder(5)`.
3. Проверяем вызовы.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func MakeAdder(offset int) func(int) int {
	return func(x int) int {
		return x + offset
	}
}

func main() {
	plusFive := MakeAdder(5)
	plusTwenty := MakeAdder(20)

	fmt.Printf("plusFive(10):   %d\n", plusFive(10))
	fmt.Printf("plusTwenty(10): %d\n", plusTwenty(10))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# plusFive(10):   15
# plusTwenty(10): 30"""
            }
        ],
        "under_the_hood": """
Захват переменной по значению/указателю в объект замыкания.
""",
        "pitfalls": """
- Изменение внешней переменной при конкурентных вызовах замыкания.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каковы накладные расходы замыканий по сравнению с обычными функциями?»
**Ответ:** Создание объекта замыкания в куче (Heap Allocation) и один косвенный вызов функции по указателю.
"""
    },
    {
        "num": 35,
        "title": "Многовариантный Type Switch для обработки полиморфных параметров",
        "task": "Реализуйте переключатель типов type switch, печатающий разную информацию в зависимости от типа переданного значения.",
        "theory": """
Обработка структур и интерфейсов в Type Switch.
""",
        "step_by_step": """
1. Создаем структуры `Circle` и `Square`.
2. Пишем функцию `DescribeShape(shape any)`.
3. Печатаем параметры геометрических фигур.
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

type Circle struct{ Radius float64 }
type Square struct{ Side float64 }

func DescribeShape(s any) {
	switch v := s.(type) {
	case Circle:
		fmt.Printf("Круг радиуса %.2f (Площадь: %.2f)\n", v.Radius, math.Pi*v.Radius*v.Radius)
	case Square:
		fmt.Printf("Квадрат со стороной %.2f (Площадь: %.2f)\n", v.Side, v.Side*v.Side)
	default:
		fmt.Printf("Неизвестная фигура: %T\n", v)
	}
}

func main() {
	DescribeShape(Circle{Radius: 5})
	DescribeShape(Square{Side: 4})
	DescribeShape("треугольник")
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Круг радиуса 5.00 (Площадь: 78.54)
# Квадрат со стороной 4.00 (Площадь: 16.00)
# Неизвестная фигура: string"""
            }
        ],
        "under_the_hood": """
Сравнение `_type` в таблице виртуальных методов.
""",
        "pitfalls": """
- Передача `*Circle` вместо `Circle`: ветка `case Circle:` не сработает (типы `Circle` и `*Circle` различны!).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как поддержать и указатели, и значения в Type Switch?»
**Ответ:** Добавить обе ветки: `case Circle: ... case *Circle: ...`.
"""
    },
    {
        "num": 36,
        "title": "Прерывание выполнения программы через panic при критических сбоях",
        "task": "Используйте panic для прерывания выполнения программы при возникновении критической ошибки (например, деление на ноль).",
        "theory": """
**Когда в Go оправдан вызов `panic`:**
1. Неустранимая ошибка инициализации конфигурации (`must`-функции, например `template.Must`, `regexp.MustCompile`);
2. Нарушение критического инварианта программы (баг в логике разработчика);
3. Для всех штатных бизнес-ошибок **обязательно использовать возврат `error`**.
""",
        "step_by_step": """
1. Пишем функцию `MustDivide(a, b int) int`.
2. При `b == 0` вызываем `panic(...)`.
3. Показываем стек-трейс паники.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func MustDivide(a, b int) int {
	if b == 0 {
		panic("критическая ошибка: деление на ноль в MustDivide")
	}
	return a / b
}

func main() {
	fmt.Printf("10 / 2 = %d\n", MustDivide(10, 2))

	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("⚠️ Перехвачена критическая паника: %v\n", r)
		}
	}()

	MustDivide(10, 0) // Вызовет панику
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 10 / 2 = 5
# ⚠️ Перехвачена критическая паника: критическая ошибка: деление на ноль в MustDivide"""
            }
        ],
        "under_the_hood": """
`runtime.gopanic` разматывает стек горутины.
""",
        "pitfalls": """
- Использование `panic` для валидации пользовательского ввода (антипаттерн в Go).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что такое соглашение об именовании `Must...` в Go?»
**Ответ:** Префикс `Must` ставится у функций, которые паникуют при ошибке вместо возврата `error` (используются только при старте сервиса).
"""
    },
    {
        "num": 37,
        "title": "Именованный возврат RectangleStats(width, height float64) (area, perimeter float64)",
        "task": "Именованный возврат: Напишите функцию RectangleStats(width, height float64) (area, perimeter float64), которая вычисляет площадь и периметр прямоугольника, используя именованные возвращаемые значения.",
        "theory": """
Самодокументируемая сигнатура расчета геометрии.
""",
        "step_by_step": """
1. Пишем `RectangleStats(w, h float64) (area, perimeter float64)`.
2. Заполняем и возвращаем явно `return area, perimeter`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func RectangleStats(width, height float64) (area, perimeter float64) {
	area = width * height
	perimeter = 2 * (width + height)
	return area, perimeter // Явный возврат повышает читаемость
}

func main() {
	a, p := RectangleStats(8.0, 3.0)
	fmt.Printf("Площадь: %.1f, Периметр: %.1f\n", a, p)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Площадь: 24.0, Периметр: 22.0"""
            }
        ],
        "under_the_hood": """
Именованные параметры создают локальные переменные в начале стекового кадра.
""",
        "pitfalls": """
- Затенение именованных переменных в блоках `if`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему явный `return area, perimeter` предпочтительнее naked `return`?»
**Ответ:** Он защищает от случайных ошибок при рефакторинге и делает код прозрачным.
"""
    },
    {
        "num": 38,
        "title": "Передача среза чисел []int{1, 2, 3} в вариативную функцию через оператор ...",
        "task": "Вызови вариативную функцию, передав ей срез []int{1, 2, 3} с использованием оператора ....",
        "theory": """
Закрепление распаковки срезов.
""",
        "step_by_step": """
1. Пишем `PrintNumbers(nums ...int)`.
2. Создаем `s := []int{1, 2, 3}`.
3. Вызываем `PrintNumbers(s...)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func PrintNumbers(nums ...int) {
	fmt.Printf("Получено %d чисел: %v\n", len(nums), nums)
}

func main() {
	numbers := []int{1, 2, 3}
	PrintNumbers(numbers...)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Получено 3 чисел: [1 2 3]"""
            }
        ],
        "under_the_hood": """
Передача указателя на массив среза.
""",
        "pitfalls": """
- Попытка передать массив `[3]int` без среза `arr[:]...`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как передать массив `arr := [3]int{1,2,3}` в вариативную функцию `Foo(nums ...int)`?»
**Ответ:** Через срез массива: `Foo(arr[:]...)`.
"""
    },
    {
        "num": 39,
        "title": "Именованные возвращаемые значения и чистый возврат (Naked Return)",
        "task": "Именованные возвращаемые значения (Naked return): Перепиши функцию из упр. 53, назвав возвращаемые переменные в сигнатуре. Сделай возврат через return без аргументов.",
        "theory": """
Преобразование сигнатуры для лаконичности в коротких функциях.
""",
        "step_by_step": """
1. Пишем `FormatUser(id int, name string) (formatted string)`.
2. Заполняем `formatted`.
3. Завершаем `return`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func FormatUser(id int, name string) (formatted string) {
	formatted = fmt.Sprintf("ID: %04d | Имя: %s", id, name)
	return
}

func main() {
	res := FormatUser(7, "Дмитрий")
	fmt.Println(res)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# ID: 0007 | Имя: Дмитрий"""
            }
        ],
        "under_the_hood": """
Возврат строки из стекового слота.
""",
        "pitfalls": """
- Неприсвоенная переменная вернет zero-value (`""`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каково zero value именованной возвращаемой строки?»
**Ответ:** Пустая строка `""`.
"""
    },
    {
        "num": 40,
        "title": "Сравнение читаемости и риски Naked return в промышленных проектах",
        "task": "\"Голый\" возврат (Naked return): Перепишите предыдущую функцию RectangleStats так, чтобы она использовала \"голый\" оператор return. Напишите комментарий, почему в больших функциях этого стоит избегать.",
        "theory": """
Анализ поддерживаемости (Maintainability) кода при использовании Naked Return.
""",
        "step_by_step": """
1. Реализуем функцию с Naked Return.
2. Добавляем поясняющие комментарии.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

// RectangleStatsNaked демонстрирует Naked Return.
// ⚠️ ВНИМАНИЕ: В функциях длиннее 10-15 строк голый return ухудшает читаемость,
// так как скрывает, какие именно переменные возвращаются.
func RectangleStatsNaked(w, h float64) (area, perimeter float64) {
	area = w * h
	perimeter = 2 * (w + h)
	return // Naked return
}

func main() {
	a, p := RectangleStatsNaked(5, 10)
	fmt.Printf("Area: %.1f, Perimeter: %.1f\n", a, p)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Area: 50.0, Perimeter: 30.0"""
            }
        ],
        "under_the_hood": """
Компилятор подставляет имена из сигнатуры.
""",
        "pitfalls": """
- Сложность код-ревью в больших файлах.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова позиция линтеров (`golangci-lint`, `nakedret`) по поводу Naked Returns?»
**Ответ:** Линтер `nakedret` по умолчанию выдает предупреждение для любых функций с naked return длиннее 5-10 строк.
"""
    },
    {
        "num": 41,
        "title": "Исторический баг захвата переменной цикла в замыкании (Loop Variable Capture) до и после Go 1.22",
        "task": "Поймайте классическую ошибку замыкания в цикле: создайте слайс функций, каждая должна выводить свой индекс. Сравните неправильный вариант и правильный (с копией переменной).",
        "theory": """
**Фундаментальная эволюция замыканий в Go 1.22+:**
- **До Go 1.22:** Переменная цикла `i` была ОДНОЙ ячейкой памяти на все итерации. Замыкания захватывали ее по указателю и после цикла все выводили последнее значение `3`;
- **Go 1.22+:** Каждая итерация цикла создает **новую переменную `i` в собственном скоупе**, устраняя этот 15-летний баг языка Go!
""",
        "step_by_step": """
1. Создаем `funcs := make([]func(), 3)`.
2. Заполняем замыканиями в цикле.
3. Показываем классический фикс `i := i` (для совместимости со старыми версиями Go).
4. Вызываем функции.
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
		// Классический паттерн совместимости (до Go 1.22):
		// localI := i // Создание локальной копии
		funcs[i] = func() {
			fmt.Printf("Индекс из замыкания: %d\n", i)
		}
	}

	fmt.Println("Вызов функций после завершения цикла:")
	for _, f := range funcs {
		f()
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вызов функций после завершения цикла:
# Индекс из замыкания: 0
# Индекс из замыкания: 1
# Индекс из замыкания: 2"""
            }
        ],
        "under_the_hood": """
В Go 1.22+ компилятор выделяет отдельный слот памяти под `i` на каждой итерации.
""",
        "pitfalls": """
- Код, работающий на старых версиях Go 1.21 и ниже без `localI := i`, выведет `3 3 3`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в Go 1.22 изменилась семантика `for` циклов?»
**Ответ:** Переменные цикла (`for i := ...` и `for k, v := range ...`) теперь имеют область видимости одной итерации (Per-iteration Scoping), а не всего цикла.
"""
    },
    {
        "num": 42,
        "title": "Вариативная функция суммирования Sum(nums ...int) int",
        "task": "Вариативные параметры: Напиши функцию Sum(nums ...int) int, которая принимает любое количество чисел и возвращает их сумму.",
        "theory": """
Базовое сложение элементов вариативного среза.
""",
        "step_by_step": """
1. Пишем `Sum(nums ...int) int`.
2. Суммируем в цикле `for _, n := range nums`.
3. Тестируем на разном числе аргументов.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Sum(nums ...int) int {
	total := 0
	for _, n := range nums {
		total += n
	}
	return total
}

func main() {
	fmt.Printf("Sum():              %d\n", Sum())
	fmt.Printf("Sum(10):            %d\n", Sum(10))
	fmt.Printf("Sum(1, 2, 3, 4, 5): %d\n", Sum(1, 2, 3, 4, 5))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Sum():              0
# Sum(10):            10
# Sum(1, 2, 3, 4, 5): 15"""
            }
        ],
        "under_the_hood": """
Линейный проход $O(N)$ по стековому/кучевому срезу.
""",
        "pitfalls": """
- Вызов `Sum()` вернет `0` без ошибок.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Аллоцирует ли `Sum(1, 2, 3)` память в куче?»
**Ответ:** Нет, компилятор размещает временный массив `[3]int` на стеке текущего фрейма.
"""
    },
    {
        "num": 43,
        "title": "Функция высшего порядка (Higher-Order Function): передача функции как аргумента",
        "task": "Передайте функцию как аргумент в другую функцию (функция высшего порядка), например, для применения математической операции к числу.",
        "theory": """
**Функции высшего порядка (Higher-Order Functions):**
- Функции, принимающие другие функции в качестве параметров;
- Основа функциональной декомпозиции и паттерна Стратегия.
""",
        "step_by_step": """
1. Пишем `Apply(val int, op func(int) int) int`.
2. Передаем операции возведения в квадрат и удвоения.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Apply(val int, op func(int) int) int {
	return op(val)
}

func main() {
	square := func(n int) int { return n * n }
	double := func(n int) int { return n * 2 }

	fmt.Printf("Apply(5, square): %d\n", Apply(5, square))
	fmt.Printf("Apply(5, double): %d\n", Apply(5, double))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Apply(5, square): 25
# Apply(5, double): 10"""
            }
        ],
        "under_the_hood": """
Косвенный вызов через регистр процессора.
""",
        "pitfalls": """
- Передача `nil` вместо функции: вызовет панику `nil pointer dereference`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как обезопасить функцию высшего порядка от передачи `nil`?»
**Ответ:** Добавить проверку `if op == nil { return val }`.
"""
    },
    {
        "num": 44,
        "title": "SafeDivide(a, b int) (int, error) с recover(): антипаттерн паники для потока управления",
        "task": "Напиши функцию SafeDivide(a, b int) (result int, err error), которая использует defer + recover для перехвата деления на ноль (через panic при b == 0). Обсуди, хорошая ли это практика.",
        "theory": """
**Почему использование `panic/recover` для штатного управления потоком — плохая практика (Антипаттерн):**
1. `panic` в 10–50 раз медленнее обычной проверки `if b == 0`;
2. Затрудняет чтение и отладку;
3. Нарушает идиоматичный стиль Go («Don't panic, return error»).
""",
        "step_by_step": """
1. Пишем `SafeDivide(a, b int) (result int, err error)`.
2. Перехватываем деление на ноль через `recover`.
3. Анализируем архитектурные выводы.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func SafeDivide(a, b int) (result int, err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("ошибка вычисления: %v", r)
		}
	}()

	// Провоцируем деление (целочисленное деление на 0 в Go вызывает runtime panic):
	result = a / b
	return result, nil
}

func main() {
	res1, err1 := SafeDivide(10, 2)
	fmt.Printf("10 / 2 = %d (err: %v)\n", res1, err1)

	res2, err2 := SafeDivide(10, 0)
	fmt.Printf("10 / 0 = %d (err: %v)\n", res2, err2)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 10 / 2 = 5 (err: <nil>)
# 10 / 0 = 0 (err: ошибка вычисления: runtime error: integer divide by zero)"""
            }
        ],
        "under_the_hood": """
Целочисленное деление на ноль генерирует аппаратное исключение процессора `SIGFPE` (#DE), которое рантайм Go преобразует в `panic`.
""",
        "pitfalls": """
- Использование `panic` вместо `if b == 0 { return 0, errors.New(...) }`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go разделяют понятия `error` и `panic`?»
**Ответ:** `error` — для ожидаемых сбоев бизнес-логики и внешних систем (сеть, диск). `panic` — исключительно для критических сбоев рантайма и нарушений целостности программы.
"""
    },
    {
        "num": 45,
        "title": "Универсальная фильтрация среза чисел Filter(nums, predicate) с набором предикатов",
        "task": "Напиши функцию Filter(nums []int, predicate func(int) bool) []int, которая фильтрует слайс по предикату. Реализуй предикаты: чётные, положительные, больше 10.",
        "theory": """
Реализация паттерна Filter на предикатах `func(int) bool`.
""",
        "step_by_step": """
1. Пишем `Filter(nums []int, pred func(int) bool) []int`.
2. Объявляем предикаты `isEven`, `isPositive`, `isGreaterThanTen`.
3. Фильтруем тестовый срез.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Filter(nums []int, predicate func(int) bool) []int {
	var result []int
	for _, n := range nums {
		if predicate(n) {
			result = append(result, n)
		}
	}
	return result
}

func main() {
	numbers := []int{-5, -2, 0, 3, 8, 12, 17, 24}

	evens := Filter(numbers, func(n int) bool { return n%2 == 0 })
	positives := Filter(numbers, func(n int) bool { return n > 0 })
	gt10 := Filter(numbers, func(n int) bool { return n > 10 })

	fmt.Printf("Исходные:    %v\n", numbers)
	fmt.Printf("Четные:      %v\n", evens)
	fmt.Printf("Положительные: %v\n", positives)
	fmt.Printf("Больше 10:   %v\n", gt10)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Исходные:    [-5 -2 0 3 8 12 17 24]
# Четные:      [-2 0 8 12 24]
# Положительные: [3 8 12 17 24]
# Больше 10:   [12 17 24]"""
            }
        ],
        "under_the_hood": """
Вызов замыкания на каждой итерации.
""",
        "pitfalls": """
- Выделение нового среза: для нулевых аллокаций используют In-Place фильтрацию.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какая функция стандартной библиотеки в Go 1.21+ заменяет самописный Filter?»
**Ответ:** `slices.DeleteFunc` для удаления на месте или итераторы `iter.Seq` в Go 1.23+.
"""
    },
    {
        "num": 46,
        "title": "Опасность затенения переменных (Shadowing Trap) при Naked Return",
        "task": "Опасность Naked return: Напиши функцию с именованным возвратом result int. Внутри функции открой блок if и объяви там новую result := 10 (через :=). Сделай naked return. Пойми ошибку затенения в возвращаемых значениях.",
        "theory": """
**Коварная ошибка затенения (Variable Shadowing) при Naked Return:**
- Именованная переменная возврата `result` объявлена на уровне функции;
- Внутри блока `if` оператор `result := 10` создает **новую локальную переменную**, затеняя внешнюю;
- Внешняя переменная `result` остается равной `0`;
- Оператор `return` возвратит **внешний 0**, проигнорировав локальную `10`!
""",
        "step_by_step": """
1. Демонстрируем функцию с багом затенения `ShadowBug()`.
2. Исправляем через прямое присваивание `result = 10` (без двоеточия).
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func ShadowBug(flag bool) (result int) {
	if flag {
		// ⚠️ ОШИБКА: := создает новую переменную внутри скоупа if,
		// затеняя возвращаемый result!
		result := 100
		_ = result // Локальная переменная = 100
	}
	return // Вернет ВНЕШНИЙ result (который равен 0!)
}

func ShadowFixed(flag bool) (result int) {
	if flag {
		result = 100 // ПРАВИЛЬНО: присваивание внешней переменной
	}
	return
}

func main() {
	fmt.Printf("1. ShadowBug(true):   %d (БАГ ЗАТЕНЕНИЯ: ВЕРНУЛ 0 ВМЕСТО 100!)\n", ShadowBug(true))
	fmt.Printf("2. ShadowFixed(true): %d (ИСПРАВЛЕНО!)\n", ShadowFixed(true))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. ShadowBug(true):   0 (БАГ ЗАТЕНЕНИЯ: ВЕРНУЛ 0 ВМЕСТО 100!)
# 2. ShadowFixed(true): 100 (ИСПРАВЛЕНО!)"""
            }
        ],
        "under_the_hood": """
Компилятор выделяет разные стековые слоты для внутренней и внешней переменной `result`.
""",
        "pitfalls": """
- Затенение `err := ...` внутри блоков `if`, из-за чего вызывающий код получает `err == nil`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какой инструмент в Go помогает выявлять баги затенения переменных?»
**Ответ:** Анализатор `go vet` с включенным линтером `shadow` (`go vet -vettool=$(which shadow) ./...`).
"""
    },
    {
        "num": 47,
        "title": "Вариативная конкатенация строк Concat(sep string, words ...string) string",
        "task": "Вариативные параметры: Напишите функцию Concat(sep string, words ...string) string, которая соединяет переданные строки через разделитель.",
        "theory": """
Реализация функции склеивания строк с использованием `strings.Builder`.
""",
        "step_by_step": """
1. Пишем `Concat(sep string, words ...string) string`.
2. Используем `strings.Builder` для минимизации аллокаций.
3. Тестируем с разными разделителями.
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

func Concat(sep string, words ...string) string {
	if len(words) == 0 {
		return ""
	}
	var sb strings.Builder
	for i, w := range words {
		if i > 0 {
			sb.WriteString(sep)
		}
		sb.WriteString(w)
	}
	return sb.String()
}

func main() {
	s1 := Concat(" -> ", "Шаг 1", "Шаг 2", "Шаг 3")
	s2 := Concat("/", "api", "v1", "users", "profile")

	fmt.Println("s1:", s1)
	fmt.Println("s2:", s2)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# s1: Шаг 1 -> Шаг 2 -> Шаг 3
# s2: api/v1/users/profile"""
            }
        ],
        "under_the_hood": """
`strings.Builder` выделяет единый непрерывный буфер памяти.
""",
        "pitfalls": """
- Использование оператора `+` в цикле: порождает $O(N^2)$ временных аллокаций.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `strings.Builder` быстрее `fmt.Sprintf` при склеивании строк?»
**Ответ:** `strings.Builder` избегает рефлексии, парсинга формата и конвертирует буфер в `string` через `unsafe.String` без повторного копирования памяти.
"""
    },
    {
        "num": 48,
        "title": "Вариативная функция-обертка для логирования с аргументами ...any",
        "task": "Напишите вариативную функцию-обёртку для fmt.Println, принимающую ...interface{}.",
        "theory": """
**Вариативные параметры `...any` (`...interface{}`):**
- Позволяют принимать произвольное количество аргументов любых типов;
- Основа построения систем логирования (`log.Println`, `zap.Sugar`).
""",
        "step_by_step": """
1. Пишем `LogInfo(args ...any)`.
2. Добавляем временной штамп и префикс `[INFO]`.
3. Передаем аргументы в `fmt.Println(append(prefix, args...)...)`.
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

func LogInfo(args ...any) {
	timestamp := time.Now().Format("15:04:05")
	prefix := fmt.Sprintf("[%s] [INFO]", timestamp)
	// Передаем префикс и все аргументы в fmt.Println:
	allArgs := append([]any{prefix}, args...)
	fmt.Println(allArgs...)
}

func main() {
	LogInfo("Сервер запущен на порту", 8080, "Режим:", "Production")
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# [15:04:05] [INFO] Сервер запущен на порту 8080 Режим: Production"""
            }
        ],
        "under_the_hood": """
Каждый аргумент оборачивается в 16-байтную структуру интерфейса `eface`.
""",
        "pitfalls": """
- Аллокации памяти при упаковке примитивных типов (`int`, `float`) в `any`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в высокопроизводительных логгерах (Uber zap) избегают `...any`?»
**Ответ:** Потому что упаковка в `any` (Boxing) вызывает аллокации в куче. Быстрые логгеры используют строго типизированные методы (`zap.Int`, `zap.String`).
"""
    },
    {
        "num": 49,
        "title": "Анонимная функция немедленного вызова (IIFE) для фиксации текущего времени",
        "task": "Анонимная функция (IIFE): Напишите и сразу же вызовите анонимную функцию, которая выводит текущее время.",
        "theory": """
Закрепление синтаксиса IIFE для форматированного вывода времени.
""",
        "step_by_step": """
1. Пишем `func() { ... }()`.
2. Получаем `time.Now()`.
3. Форматируем и выводим.
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

func main() {
	func() {
		now := time.Now()
		fmt.Printf("⏰ Текущая дата и время: %s\n", now.Format("2006-01-02 15:04:05"))
	}()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# ⏰ Текущая дата и время: 2026-09-02 15:04:05"""
            }
        ],
        "under_the_hood": """
Локальная область видимости переменной `now`.
""",
        "pitfalls": """
- Забыть вызов `()`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Может ли IIFE возвращать несколько значений?»
**Ответ:** ДА! Например: `a, b := func() (int, int) { return 1, 2 }()`.
"""
    },
    {
        "num": 50,
        "title": "Распаковка строкового среза []string в вариативную функцию Concat",
        "task": "Распаковка среза: Создайте срез строк []string{\"Go\", \"is\", \"awesome\"}. Передайте его в созданную ранее функцию Concat с использованием оператора ....",
        "theory": """
Передача строкового среза без переаллокаций.
""",
        "step_by_step": """
1. Создаем срез `words := []string{"Go", "is", "awesome"}`.
2. Передаем в `Concat(" ", words...)`.
3. Печатаем результат.
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

func Concat(sep string, words ...string) string {
	return strings.Join(words, sep)
}

func main() {
	words := []string{"Go", "is", "awesome"}
	sentence := Concat(" ", words...)
	fmt.Println("Результат распаковки:", sentence)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Результат распаковки: Go is awesome"""
            }
        ],
        "under_the_hood": """
Прямая передача дескриптора `SliceHeader`.
""",
        "pitfalls": """
- Попытка передать `words` без `...`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова пространственная сложность распаковки среза `slice...`?»
**Ответ:** Строго $O(1)$ (копируется 24-байтный дескриптор среза).
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 2: {len(exercises)} exercises.")
