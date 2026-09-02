# Chapter 14 Part 2: Exercises 27 to 52

exercises = [
    {
        "num": 27,
        "title": "Безопасное извлечение строки из any с расчетом длины через str, ok := val.(string)",
        "task": "Приведение типов (Type Assertion): Создайте функцию, принимающую пустой интерфейс any (или interface{}). Внутри функции проверьте, лежит ли там строка, используя синтаксис str, ok := val.(string). Если это строка, выведите её длину, если нет — выведите сообщение \"Не строка\".",
        "theory": """
Закрепление паттерна `comma-ok` для проверки динамических типов.
""",
        "step_by_step": """
1. Пишем `InspectString(val any)`.
2. Используем `str, ok := val.(string)`.
3. Тестируем.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func InspectString(val any) {
	if str, ok := val.(string); ok {
		fmt.Printf("Строка найдена: %q | Длина: %d символов\n", str, len(str))
	} else {
		fmt.Printf("Значение %v (%T): Не строка\n", val, val)
	}
}

func main() {
	InspectString("Высоконагруженный бэкенд")
	InspectString(3.14)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Строка найдена: "Высоконагруженный бэкенд" | Длина: 45 символов
# Значение 3.14 (float64): Не строка"""
            }
        ],
        "under_the_hood": """
Сравнение `_type` дескриптора.
""",
        "pitfalls": """
- Вызов без `ok` в production коде.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова алгоритмическая сложность `val, ok := v.(T)`?»
**Ответ:** Для конкретных типов `T` (структуры, примитивы) — $O(1)$ (прямое сравнение адресов указателей типов `_type`).
"""
    },
    {
        "num": 28,
        "title": "Type Switch по any с дифференцированной бизнес-логикой для разных типов",
        "task": "Напишите type switch, который принимает any и выполняет разные действия в зависимости от динамического типа переменной.",
        "theory": """
Диспетчеризация логики на основе типов.
""",
        "step_by_step": """
1. Пишем `ProcessPayload(data any)`.
2. Обрабатываем `[]byte`, `string`, `int`, `map[string]any`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func ProcessPayload(data any) {
	switch v := data.(type) {
	case []byte:
		fmt.Printf("Бинарный буфер (%d байт): %x\n", len(v), v)
	case string:
		fmt.Printf("Текстовый payload: %q\n", v)
	case int:
		fmt.Printf("Числовой код статуса: %d\n", v)
	case map[string]any:
		fmt.Printf("JSON-подобная карта с %d ключами\n", len(v))
	default:
		fmt.Printf("Неизвестный формат данных: %T\n", v)
	}
}

func main() {
	ProcessPayload([]byte{0x47, 0x6F})
	ProcessPayload("status:ok")
	ProcessPayload(200)
	ProcessPayload(map[string]any{"user_id": 10})
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Бинарный буфер (2 байт): 476f
# Текстовый payload: "status:ok"
# Числовой код статуса: 200
# JSON-подобная карта с 1 ключами"""
            }
        ],
        "under_the_hood": """
Генерация бинарного дерева условий в ассемблере.
""",
        "pitfalls": """
- Пропуск ветки `default`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли перечислить несколько типов в одном `case` в `type switch`?»
**Ответ:** ДА (`case int, int64:`), но в таком случае переменная `v` внутри `case` будет иметь тип `any` (исходный интерфейс), а не конкретный тип.
"""
    },
    {
        "num": 29,
        "title": "Композиция интерфейсов: ReadWriteCloser и структура сетевой сессии NetworkSession",
        "task": "Создай интерфейс ReadWriteCloser, встраивающий io.Reader, io.Writer, io.Closer. Создай структуру, реализующую все три. Покажи, что встраивание интерфейсов работает как композиция.",
        "theory": """
**Составной контракт `io.ReadWriteCloser`:**
- Объединяет `Read`, `Write` и `Close`;
- Фундаментальный интерфейс для сетевых TCP/TLS-сокетов (`net.Conn`).
""",
        "step_by_step": """
1. Объявляем интерфейс `ReadWriteCloser`.
2. Создаем `NetworkSession` и реализуем все три метода.
3. Проверяем полиморфизм.
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

type ReadWriteCloser interface {
	io.Reader
	io.Writer
	io.Closer
}

type NetworkSession struct {
	data   []byte
	closed bool
}

func (s *NetworkSession) Read(p []byte) (int, error) {
	if s.closed {
		return 0, fmt.Errorf("сессия закрыта")
	}
	n := copy(p, s.data)
	return n, nil
}

func (s *NetworkSession) Write(p []byte) (int, error) {
	if s.closed {
		return 0, fmt.Errorf("сессия закрыта")
	}
	s.data = append(s.data, p...)
	return len(p), nil
}

func (s *NetworkSession) Close() error {
	s.closed = true
	fmt.Println("Сетевая сессия корректно закрыта")
	return nil
}

func main() {
	var rwc ReadWriteCloser = &NetworkSession{}

	rwc.Write([]byte("PING"))
	rwc.Close()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Сетевая сессия корректно закрыта"""
            }
        ],
        "under_the_hood": """
`itab` содержит адреса трех функций: `Read`, `Write`, `Close`.
""",
        "pitfalls": """
- Забыть метод `Close()` (компилятор не позволит присвоить структуру интерфейсу).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какому стандартному интерфейсу удовлетворяет сетевое подключение `net.Conn`?»
**Ответ:** `net.Conn` реализует `io.Reader`, `io.Writer`, `io.Closer`, а также методы настройки таймаутов (`SetDeadline`).
"""
    },
    {
        "num": 30,
        "title": "Динамическая проверка интерфейса: опциональный вызов fmt.Stringer через Type Assertion",
        "task": "Утверждение типа: проверьте, реализует ли переданный interface{} интерфейс fmt.Stringer, и если да, вызовите его.",
        "theory": """
**Паттерн опционального интерфейса (Optional Interface Query):**
- Проверяет в рантайме, поддерживает ли переданный объект расширенный интерфейс (например, `fmt.Stringer` или `io.Closer`);
- Если да — вызывает специализированный метод, если нет — использует стандартное поведение (Graceful Fallback).
""",
        "step_by_step": """
1. Пишем `PrintCustom(v any)`.
2. Проверяем `if s, ok := v.(fmt.Stringer); ok`.
3. Тестируем со структурой, реализующей `String()`, и обычной структурой.
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

func (u User) String() string {
	return fmt.Sprintf("Пользователь: %s", u.Name)
}

type RawData struct {
	Value int
}

func PrintCustom(v any) {
	// Динамическая проверка реализации интерфейса fmt.Stringer:
	if stringer, ok := v.(fmt.Stringer); ok {
		fmt.Printf("✅ Найден fmt.Stringer: %s\n", stringer.String())
	} else {
		fmt.Printf("ℹ️ Обычный вывод: %+v\n", v)
	}
}

func main() {
	PrintCustom(User{Name: "Сергей"})
	PrintCustom(RawData{Value: 42})
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# ✅ Найден fmt.Stringer: Пользователь: Сергей
# ℹ️ Обычный вывод: {Value:42}"""
            }
        ],
        "under_the_hood": """
Рантайм ищет метод `String()` в таблице методов типа объекта через `runtime.assertI2I`.
""",
        "pitfalls": """
- Реализация `String()` на указателе `*User`, а передача значения `User{}` (в этом случае проверка `v.(fmt.Stringer)` вернет `false`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в стандартной библиотеке `io.Copy` проверяется поддержка `io.WriterTo` / `io.ReaderFrom`?»
**Ответ:** Через динамический Type Assertion `if wt, ok := src.(io.WriterTo); ok { return wt.WriteTo(dst) }`, что позволяет использовать оптимизированный системный вызов `sendfile(2)` ядра Linux.
"""
    },
    {
        "num": 31,
        "title": "Полиморфизм потоков: универсальная функция ProcessStream(r io.Reader)",
        "task": "Напиши функцию ProcessStream(r io.Reader), которая работает с любым ридером: os.File, bytes.Buffer, strings.NewReader, MyBuffer. Продемонстрируй полиморфизм.",
        "theory": """
Универсальная обработка любых источников потоковых данных.
""",
        "step_by_step": """
1. Пишем `ProcessStream(r io.Reader)`.
2. Передаем `strings.NewReader` и `bytes.NewBuffer`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"bytes"
	"fmt"
	"io"
	"strings"
)

func ProcessStream(r io.Reader) {
	buf := make([]byte, 32)
	total := 0

	for {
		n, err := r.Read(buf)
		if n > 0 {
			total += n
			fmt.Printf("  • Прочитана порция: %q\n", string(buf[:n]))
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			fmt.Println("Ошибка чтения:", err)
			return
		}
	}
	fmt.Printf("Итого обработано байт: %d\n\n", total)
}

func main() {
	fmt.Println("1. Чтение из strings.Reader:")
	ProcessStream(strings.NewReader("Строковый поток данных"))

	fmt.Println("2. Чтение из bytes.Buffer:")
	ProcessStream(bytes.NewBufferString("Буферизованные бинарные данные"))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Чтение из strings.Reader:
#   • Прочитана порция: "Строковый поток данных"
# Итого обработано байт: 41
# 
# 2. Чтение из bytes.Buffer:
#   • Прочитана порция: "Буферизованные бинарн"
#   • Прочитана порция: "ые данные"
# Итого обработано байт: 56"""
            }
        ],
        "under_the_hood": """
Интерфейсный вызов `r.Read` связывается с конкретной реализацией в рантайме.
""",
        "pitfalls": """
- Вызов `io.ReadAll` на бесконечных ридерах (приведет к Out-of-Memory).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `io.Reader` спроектирован так, что вызывающий код выделяет буфер `p []byte`, а не сам `Reader`?»
**Ответ:** Это фундаментальный принцип Zero-Allocation: вызывающий код может переиспользовать один и тот же буфер в цикле, не нагружая сборщик мусора постоянными аллокациями.
"""
    },
    {
        "num": 32,
        "title": "Извлечение конкретного типа из any через Type Assertion str, ok := v.(string)",
        "task": "Используй type assertion для извлечения конкретного типа из any: str, ok := v.(string).",
        "theory": """
Базовое извлечение типов из динамических структур данных.
""",
        "step_by_step": """
1. Инициализируем `var data any = "Golang Backend"`.
2. Извлекаем строку с проверкой `ok`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	var data any = "Golang Backend"

	if str, ok := data.(string); ok {
		fmt.Printf("Строковое значение: %s\n", str)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Строковое значение: Golang Backend"""
            }
        ],
        "under_the_hood": """
Копирование заголовка строки (16 байт) из интерфейса.
""",
        "pitfalls": """
- Ошибочное утверждение `data.(int)` приведет к `ok == false`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как быстро проверить, что в `any` лежит `nil`?»
**Ответ:** `if data == nil` (проверяет, что не установлен ни тип, ни значение).
"""
    },
    {
        "num": 33,
        "title": "Реализация интерфейса fmt.Stringer для структуры Book и автоматический вызов в fmt.Println",
        "task": "Создай интерфейс fmt.Stringer (или используй существующий). Реализуй его для структуры Book. Покажи, что fmt.Println автоматически вызывает String().",
        "theory": """
**Интерфейс `fmt.Stringer`:**
- Стандартный интерфейс с методом `String() string`;
- Функции `fmt.Print`, `fmt.Println`, `fmt.Sprintf` автоматически вызывают `String()`, если объект реализует этот интерфейс.
""",
        "step_by_step": """
1. Создаем структуру `Book{Title, Author string, Year int}`.
2. Реализуем `(b Book) String() string`.
3. Передаем в `fmt.Println(book)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Book struct {
	Title  string
	Author string
	Year   int
}

func (b Book) String() string {
	return fmt.Sprintf("«%s» (%s, %d г.)", b.Title, b.Author, b.Year)
}

func main() {
	b := Book{
		Title:  "Head First Go",
		Author: "Jay McGavren",
		Year:   2019,
	}

	// fmt.Println автоматически вызывает метод String():
	fmt.Println("Книга:", b)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Книга: «Head First Go» (Jay McGavren, 2019 г.)"""
            }
        ],
        "under_the_hood": """
`fmt.Println` внутри делает type assertion `if s, ok := p.(Stringer); ok { return s.String() }`.
""",
        "pitfalls": """
- Вызов `fmt.Sprintf("%s", b)` внутри метода `(b Book) String()` — приведет к **бесконечной рекурсии и переполнению стека (Stack Overflow Panic)**!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему вызов `fmt.Sprintf("%v", s)` внутри `s.String()` приводит к крашу программы?»
**Ответ:** Потому что `fmt.Sprintf` внутри снова проверяет `fmt.Stringer` и рекурсивно вызывает `s.String()`, приводя к исчерпанию стека (`runtime: goroutine stack exceeds 1000000000-byte limit`).
"""
    },
    {
        "num": 34,
        "title": "Композиция интерфейсов: Reader + Writer = ReadWriter и структура File",
        "task": "Композиция интерфейсов: Создайте интерфейс Reader с методом Read(). Создайте интерфейс Writer с методом Write(). Создайте объединенный интерфейс ReadWriter, встроив в него оба интерфейса. Создайте структуру File, реализующую ReadWriter.",
        "theory": """
Пошаговое построение композитного интерфейса.
""",
        "step_by_step": """
1. Объявляем `Reader`, `Writer`, `ReadWriter`.
2. Создаем структуру `VirtualFile`.
3. Тестируем работу.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Reader interface {
	ReadData() string
}

type Writer interface {
	WriteData(data string)
}

type ReadWriter interface {
	Reader
	Writer
}

type VirtualFile struct {
	content string
}

func (f *VirtualFile) ReadData() string {
	return f.content
}

func (f *VirtualFile) WriteData(data string) {
	f.content = data
}

func main() {
	var rw ReadWriter = &VirtualFile{}

	rw.WriteData("Контент виртуального файла")
	fmt.Println("Прочитано:", rw.ReadData())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Прочитано: Контент виртуального файла"""
            }
        ],
        "under_the_hood": """
Таблица `itab` связывает методы `ReadData` и `WriteData`.
""",
        "pitfalls": """
- Забыть один из методов.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли разбить `ReadWriter` обратно на `Reader` и `Writer`?»
**Ответ:** Да! Переменная типа `ReadWriter` может быть напрямую присвоена переменной типа `Reader` или `Writer`, так как содержит надмножество их методов.
"""
    },
    {
        "num": 35,
        "title": "Универсальная запись WriteToMultiple(w io.Writer, data string) в os.Stdout и bytes.Buffer",
        "task": "Напиши функцию WriteToMultiple(w io.Writer, data string), передай туда os.File и bytes.Buffer. Покажи, что оба реализуют io.Writer.",
        "theory": """
Полиморфный вывод в файлы, сеть и память.
""",
        "step_by_step": """
1. Пишем `WriteToMultiple(w io.Writer, data string)`.
2. Передаем `os.Stdout` и `bytes.Buffer`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"bytes"
	"fmt"
	"io"
	"os"
)

func WriteToMultiple(w io.Writer, data string) {
	fmt.Fprintf(w, "[Лог]: %s\n", data)
}

func main() {
	var memoryBuf bytes.Buffer

	// Запись в память:
	WriteToMultiple(&memoryBuf, "Запись в буфер памяти")

	// Запись в консоль (os.Stdout - это *os.File):
	WriteToMultiple(os.Stdout, "Запись в стандартный поток вывода")

	fmt.Printf("Содержимое bytes.Buffer: %s", memoryBuf.String())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# [Лог]: Запись в стандартный поток вывода
# Содержимое bytes.Buffer: [Лог]: Запись в буфер памяти"""
            }
        ],
        "under_the_hood": """
`os.Stdout` использует системный вызов `write(1, ...)`, а `bytes.Buffer` — `append`.
""",
        "pitfalls": """
- Передача `memoryBuf` по значению вместо указателя `&memoryBuf`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как объединить запись в несколько `io.Writer` одновременно?»
**Ответ:** Использовать функцию стандартной библиотеки `io.MultiWriter(w1, w2, w3)`.
"""
    },
    {
        "num": 36,
        "title": "Кастомный тип ошибки ValidationError со структурой полей и реализацией интерфейса error",
        "task": "Создай интерфейс error. Реализуй кастомный тип ошибки ValidationError (struct с полями Field, Message). Реализуй метод Error() string.",
        "theory": """
**Интерфейс `error` в Go:**
- Встроенный стандартный интерфейс: `type error interface { Error() string }`;
- Кастомные структуры ошибок позволяют передавать контекст (имя невалидного поля, код ошибки, HTTP-статус).
""",
        "step_by_step": """
1. Создаем структуру `ValidationError{Field, Message string}`.
2. Реализуем метод `(e ValidationError) Error() string`.
3. Возвращаем как `error` и проверяем через `errors.As`.
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

type ValidationError struct {
	Field   string
	Message string
}

func (e ValidationError) Error() string {
	return fmt.Sprintf("ошибка валидации поля %q: %s", e.Field, e.Message)
}

func ValidateAge(age int) error {
	if age < 18 {
		return ValidationError{Field: "age", Message: "возраст должен быть не менее 18 лет"}
	}
	return nil
}

func main() {
	err := ValidateAge(15)
	if err != nil {
		fmt.Printf("Текст ошибки: %s\n", err)

		// Проверка типа ошибки через errors.As:
		var valErr ValidationError
		if errors.As(err, &valErr) {
			fmt.Printf("⚠️ Ошибочное поле: %s\n", valErr.Field)
		}
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Текст ошибки: ошибка валидации поля "age": возраст должен быть не менее 18 лет
# ⚠️ Ошибочное поле: age"""
            }
        ],
        "under_the_hood": """
Функция `errors.As` ищет совпадение типа в цепочке обернутых ошибок.
""",
        "pitfalls": """
- Возврат неинициализированного указателя на кастомную ошибку (ловушка nil pointer in error interface).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем преимущество `errors.As` перед прямым Type Assertion `err.(ValidationError)`?»
**Ответ:** `errors.As` умеет рекурсивно разворачивать цепочки ошибок, обернутых через `fmt.Errorf("%w", err)` (Unwrap).
"""
    },
    {
        "num": 37,
        "title": "Классический интерфейс sort.Interface (Len, Less, Swap) для сортировки среза []User",
        "task": "Стандартный sort.Interface: Создай срез структур []User. Изучи интерфейс sort.Interface (методы Len, Less, Swap) и реализуй его для своего типа среза, чтобы отсортировать пользователей по возрасту (или используй sort.Slice с анонимной функцией, что современнее).",
        "theory": """
**Интерфейс `sort.Interface`:**
- Требует 3 метода: `Len() int`, `Less(i, j int) bool`, `Swap(i, j int)`;
- Позволяет функции `sort.Sort()` сортировать любые структуры данных.
""",
        "step_by_step": """
1. Создаем `type User struct { Name string; Age int }`.
2. Создаем `type ByAge []User`.
3. Реализуем `Len`, `Less`, `Swap` и сортируем через `sort.Sort`.
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

type User struct {
	Name string
	Age  int
}

// Пользовательский тип среза для реализации sort.Interface:
type ByAge []User

func (a ByAge) Len() int           { return len(a) }
func (a ByAge) Less(i, j int) bool { return a[i].Age < a[j].Age }
func (a ByAge) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }

func main() {
	users := []User{
		{Name: "Иван", Age: 30},
		{Name: "Анна", Age: 22},
		{Name: "Борис", Age: 27},
	}

	sort.Sort(ByAge(users))

	fmt.Println("Пользователи, отсортированные по возрасту:")
	for _, u := range users {
		fmt.Printf("  • %-10s (%d лет)\n", u.Name, u.Age)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Пользователи, отсортированные по возрасту:
#   • Анна       (22 лет)
#   • Борис      (27 лет)
#   • Иван       (30 лет)"""
            }
        ],
        "under_the_hood": """
`sort.Sort` применяет алгоритм QuickSort / InsertionSort через интерфейсные вызовы.
""",
        "pitfalls": """
- Забыть объявить свой тип среза `type ByAge []User`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go 1.21+ рекомендуют `slices.SortFunc` вместо `sort.Sort`?»
**Ответ:** Потому что `slices.SortFunc` типизирован дженериками и компилируется в прямой машинный код без интерфейсного оверхеда на вызовы `Less` и `Swap`.
"""
    },
    {
        "num": 38,
        "title": "Анатомия интерфейса: Nil Interface (true) против Nil Pointer in Interface (false!)",
        "task": "Напиши программу с nil interface: var r io.Reader = nil. Проверь r == nil (true). Затем: var p *os.File = nil; var r io.Reader = p. Проверь r == nil (false!). Объясни внутреннее устройство интерфейса (type descriptor + value).",
        "theory": """
**Интерфейсная ловушка номер 1 в Go (Nil Pointer in Interface):**
- Интерфейс `iface` состоит из **двух полей**: `itab` (тип) и `data` (значение);
- Интерфейс равен `nil` **ТОЛЬКО ТОГДА, КОГДА ОБА ПОЛЯ РАВНЫ `nil`**;
- Если в интерфейс помещен типизированный `nil`-указатель `var p *os.File = nil`, поле `itab` получает дескриптор типа `*os.File`, поэтому `r == nil` возвращает **`false`**!
""",
        "step_by_step": """
1. Создаем чистый `var r1 io.Reader = nil` (равен nil).
2. Создаем `var p *os.File = nil; var r2 io.Reader = p`.
3. Сравниваем оба с `nil` и анализируем разницу.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"io"
	"os"
)

func main() {
	// 1. Чистый nil-интерфейс:
	var r1 io.Reader = nil
	fmt.Printf("1. Чистый r1 == nil:                  %t (itab=nil, data=nil)\n", r1 == nil)

	// 2. Типизированный nil-указатель внутри интерфейса:
	var p *os.File = nil
	var r2 io.Reader = p
	fmt.Printf("2. r2 == nil (с nil *os.File внутри): %t (itab=*os.File, data=nil) ❌ ЛОВУШКА!\n", r2 == nil)

	// Вызов метода приведет к панике nil pointer dereference:
	// r2.Read(make([]byte, 10))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Чистый r1 == nil:                  true (itab=nil, data=nil)
# 2. r2 == nil (с nil *os.File внутри): false (itab=*os.File, data=nil) ❌ ЛОВУШКА!"""
            }
        ],
        "under_the_hood": """
Ассемблерное сравнение `CMPQ itab, $0` возвращает false, так как `itab != 0`.
""",
        "pitfalls": """
- Возврат `var err *CustomError = nil` из функции с типом возврата `error` (вызывающий код сочтет, что ошибка произошла!).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Когда переменная типа `error` равна `nil`?»
**Ответ:** Только когда она содержит чистый `nil` (без информации о конкретном типе ошибки).
"""
    },
    {
        "num": 39,
        "title": "Переключатель типов Type Switch: обработка int, string, []int и default в одной функции",
        "task": "Переключатель типов: обработайте int, string, []int и default в одной функции.",
        "theory": """
Группировка обработки данных.
""",
        "step_by_step": """
1. Пишем функцию `HandleItem(x any)`.
2. Обрабатываем типы.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func HandleItem(x any) {
	switch v := x.(type) {
	case int:
		fmt.Println("Число:", v)
	case string:
		fmt.Println("Строка:", v)
	case []int:
		fmt.Println("Срез чисел:", v)
	default:
		fmt.Println("Другой тип:", v)
	}
}

func main() {
	HandleItem(10)
	HandleItem("Go")
	HandleItem([]int{1, 2, 3})
	HandleItem(true)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Число: 10
# Строка: Go
# Срез чисел: [1 2 3]
# Другой тип: true"""
            }
        ],
        "under_the_hood": """
Прямая трансляция в таблицу меток.
""",
        "pitfalls": """
- Забыть ветку default.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каков тип переменной `v` в ветке `default`?»
**Ответ:** В ветке `default` переменная `v` имеет исходный интерфейсный тип `any`.
"""
    },
    {
        "num": 40,
        "title": "Конструкция switch v := x.(type) для разбора примитивов int, string, bool",
        "task": "Используй switch v := x.(type) (type switch) для обработки различных типов внутри any (int, string, bool, default).",
        "theory": """
Базовый синтаксис Type Switch.
""",
        "step_by_step": """
1. Пишем `Classify(x any)`.
2. Тестируем.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Classify(x any) string {
	switch v := x.(type) {
	case int:
		return fmt.Sprintf("Целое: %d", v)
	case string:
		return fmt.Sprintf("Строка: %s", v)
	case bool:
		return fmt.Sprintf("Булево: %t", v)
	default:
		return "Неизвестно"
	}
}

func main() {
	fmt.Println(Classify(55))
	fmt.Println(Classify("Gopher"))
	fmt.Println(Classify(false))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Целое: 55
# Строка: Gopher
# Булево: false"""
            }
        ],
        "under_the_hood": """
Эффективный type switch.
""",
        "pitfalls": """
- Опечатки в типах.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли использовать type switch для интерфейса с методами, а не `any`?»
**Ответ:** ДА! Type switch работает над любым интерфейсным типом.
"""
    },
    {
        "num": 41,
        "title": "Каверзный кейс: nil interface vs nil pointer in interface и хранение информации о типе",
        "task": "Каверзный случай: Изучите \"nil interface vs nil pointer in interface\". Создайте указатель на структуру (равный nil), присвойте его переменной интерфейса и проверьте, равно ли myInterface == nil. (Спойлер: интерфейс не будет nil, так как хранит информацию о типе!).",
        "theory": """
Детальный анализ внутренней структуры `iface`.
""",
        "step_by_step": """
1. Создаем структуру `MyStruct{}`.
2. Создаем `var ptr *MyStruct = nil`.
3. Присваиваем интерфейсу `var iface any = ptr`.
4. Сравниваем `iface == nil`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Worker interface {
	Work()
}

type Developer struct{}

func (d *Developer) Work() {
	fmt.Println("Пишет код на Go")
}

func main() {
	var dev *Developer = nil
	var w Worker = dev

	fmt.Printf("dev == nil: %t (указатель nil)\n", dev == nil)
	fmt.Printf("w == nil:   %t (ИНТЕРФЕЙС НЕ NIL, ТАК КАК СОДЕРЖИТ ТИП *Developer!)\n", w == nil)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# dev == nil: true (указатель nil)
# w == nil:   false (ИНТЕРФЕЙС НЕ NIL, ТАК КАК СОДЕРЖИТ ТИП *Developer!)"""
            }
        ],
        "under_the_hood": """
`w` содержит `itab` типа `*Developer`, поэтому проверка равенства нулю возвращает false.
""",
        "pitfalls": """
- Проверка `if w != nil` перед вызовом метода не защищает от nil-указателя внутри.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что произойдет при вызове `w.Work()`, если `w` содержит `nil *Developer`?»
**Ответ:** Метод `Work()` будет вызван! Если метод не обращается к полям структуры (`d.Field`), он успешно выполнится. Если обращается — произойдет паника `nil pointer dereference`.
"""
    },
    {
        "num": 42,
        "title": "Универсальный детектор истинного nil: функция IsReallyNil(v any) bool через reflect",
        "task": "Напиши функцию IsReallyNil(v interface{}) bool, которая корректно определяет \"настоящий\" nil (через reflect.ValueOf(v).IsNil() с осторожностью). Обработай panic от IsNil на non-pointer types.",
        "theory": """
**Безопасная детекция nil внутри интерфейсов:**
- Метод `reflect.ValueOf(v).IsNil()` паникует, если тип не является указателем, срезом, мапой, каналом, интерфейсом или функцией;
- Корректный детектор обязан сначала проверить `Kind()`, чтобы избежать паники.
""",
        "step_by_step": """
1. Пишем `IsReallyNil(v any) bool`.
2. Проверяем `v == nil`.
3. Проверяем допустимые `Kind()` перед вызовом `IsNil()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"reflect"
)

func IsReallyNil(v any) bool {
	if v == nil {
		return true
	}

	val := reflect.ValueOf(v)
	switch val.Kind() {
	case reflect.Pointer, reflect.Slice, reflect.Map, reflect.Chan, reflect.Func, reflect.Interface:
		return val.IsNil()
	default:
		return false
	}
}

func main() {
	var cleanNil any = nil
	var nilPtr *int = nil
	var ifaceWithNil any = nilPtr
	var number int = 0

	fmt.Printf("1. cleanNil:       IsReallyNil = %t\n", IsReallyNil(cleanNil))
	fmt.Printf("2. ifaceWithNil:   IsReallyNil = %t\n", IsReallyNil(ifaceWithNil))
	fmt.Printf("3. number (0):     IsReallyNil = %t\n", IsReallyNil(number))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. cleanNil:       IsReallyNil = true
# 2. ifaceWithNil:   IsReallyNil = true
# 3. number (0):     IsReallyNil = false"""
            }
        ],
        "under_the_hood": """
`reflect.Value.IsNil()` проверяет внутренний указатель `val.ptr == nil`.
""",
        "pitfalls": """
- Вызов `reflect.ValueOf(42).IsNil()` приведет к немедленной панике: `panic: reflect: call of reflect.Value.IsNil on int Value`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Для каких `Kind` разрешен вызов `IsNil()` в пакете `reflect`?»
**Ответ:** `Chan`, `Func`, `Interface`, `Map`, `Pointer`, `Slice`, `UnsafePointer`.
"""
    },
    {
        "num": 43,
        "title": "Главная ловушка интерфейсов: возврат nil-указателя ошибки в функции GetError() error",
        "task": "Каверзный случай: nil интерфейс с типом: Создайте структуру MyCustomError. Создайте функцию GetError() error, которая внутри объявляет указатель на вашу структуру var err *MyCustomError = nil и возвращает его. В main проверьте if err != nil. Убедитесь, что программа считает, что ошибка есть.",
        "theory": """
Классический баг на собеседованиях и в production коде.
""",
        "step_by_step": """
1. Создаем структуру `MyCustomError`.
2. Пишем функцию `GetError() error`, возвращающую `var e *MyCustomError = nil`.
3. Демонстрируем ложное срабатывание `if err != nil`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type MyCustomError struct {
	Code int
}

func (e *MyCustomError) Error() string {
	return fmt.Sprintf("код ошибки: %d", e.Code)
}

func BadGetError() error {
	var err *MyCustomError = nil
	// ❌ ОШИБКА: возврат типизированного указателя оборачивает его в интерфейс error:
	return err
}

func GoodGetError() error {
	var err *MyCustomError = nil
	if err != nil {
		return err
	}
	// ✅ ПРАВИЛЬНО: возвращать явный нетипизированный nil:
	return nil
}

func main() {
	errBad := BadGetError()
	if errBad != nil {
		fmt.Println("1. BadGetError: Ошибка ЕСТЬ! (хотя внутри nil!) ❌")
	}

	errGood := GoodGetError()
	if errGood == nil {
		fmt.Println("2. GoodGetError: Ошибки НЕТ! (чистый nil) ✅")
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. BadGetError: Ошибка ЕСТЬ! (хотя внутри nil!) ❌
# 2. GoodGetError: Ошибки НЕТ! (чистый nil) ✅"""
            }
        ],
        "under_the_hood": """
При `return err` рантайм создает `iface{itab: *MyCustomError, data: nil}`, что не равно `0`.
""",
        "pitfalls": """
- Объявление переменной кастомной ошибки `var err *MyError` в начале функции и ее безусловный возврат.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как навсегда защититься от бага `nil pointer in error interface`?»
**Ответ:** Всегда возвращать явный литерал `return nil`, если ошибки нет, либо объявлять переменную ошибки напрямую с интерфейсным типом `var err error`.
"""
    },
    {
        "num": 44,
        "title": "Композиция интерфейсов: объединение встроенных io.Reader и io.Writer в ReadWriter",
        "task": "Сделайте композицию интерфейсов: создайте интерфейс ReadWriter, объединив встроенные io.Reader и io.Writer.",
        "theory": """
Сборка составных контрактов.
""",
        "step_by_step": """
1. Объявляем `type ReadWriter interface { io.Reader; io.Writer }`.
2. Проверяем совместимость.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"bytes"
	"fmt"
	"io"
)

type ReadWriter interface {
	io.Reader
	io.Writer
}

func main() {
	buf := bytes.NewBufferString("Данные")
	var rw ReadWriter = buf

	rw.Write([]byte(" в буфере"))

	out := make([]byte, 64)
	n, _ := rw.Read(out)

	fmt.Println("Результат:", string(out[:n]))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Результат: Данные в буфере"""
            }
        ],
        "under_the_hood": """
Компиляция таблицы виртуальных методов.
""",
        "pitfalls": """
- Неполная реализация одного из встроенных интерфейсов.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли встроить `io.ReadWriter` в другой интерфейс?»
**Ответ:** Да, интерфейсы можно встраивать с любой степенью вложенности.
"""
    },
    {
        "num": 45,
        "title": "Принцип Postel's Law в Go: «Принимай интерфейсы, возвращай структуры» (Accept Interfaces, Return Structs)",
        "task": "Интерфейс как возвращаемый тип (Антипаттерн): Напиши функцию, возвращающую интерфейс, и функцию, возвращающую структуру. Осознай правило Go: Принимай интерфейсы, возвращай структуры (Postel's Law в контексте Go).",
        "theory": """
**Архитектурный закон Go (Accept Interfaces, Return Structs):**
- **Принимай интерфейсы:** функция должна требовать минимально необходимый контракт (`io.Reader`), что делает её максимально гибкой;
- **Возвращай конкретные структуры:** функция должна возвращать конкретный тип `*UserStore` (не интерфейс), чтобы вызывающий код имел доступ ко всем методам и сам решал, в какой интерфейс обернуть объект.
""",
        "step_by_step": """
1. Демонстрируем антипаттерн возврата интерфейса.
2. Демонстрируем идиоматичный возврат структуры `*Service`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Storage interface {
	Save(data string)
}

type MemoryStorage struct {
	items []string
}

func (m *MemoryStorage) Save(data string) {
	m.items = append(m.items, data)
}

// ✅ ИДИОМАТИЧНО: Возвращаем конкретную структуру:
func NewMemoryStorage() *MemoryStorage {
	return &MemoryStorage{}
}

// ✅ ИДИОМАТИЧНО: Принимаем интерфейс:
func SaveReport(s Storage, report string) {
	s.Save(report)
	fmt.Printf("Отчет %q сохранен!\n", report)
}

func main() {
	store := NewMemoryStorage()
	SaveReport(store, "Q3 Financials")
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Отчет "Q3 Financials" сохранен!"""
            }
        ],
        "under_the_hood": """
Возврат структуры избегает лишних аллокаций `iface` и позволяет компилятору инлайнить вызовы.
""",
        "pitfalls": """
- Создание интерфейса `Storage` заранее в том же пакете, где определен `MemoryStorage` (Interface Pollution).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Когда функция ВСЕ-ТАКИ ДОЛЖНА возвращать интерфейс?»
**Ответ:** Только когда реализация скрыта и недоступна вызывающему коду (например, `error` или создание моков в фабриках).
"""
    },
    {
        "num": 46,
        "title": "Интерфейс fmt.Stringer: реализация метода String() для структуры User",
        "task": "Интерфейс fmt.Stringer: Реализуйте метод String() string для вашей структуры User (поля Name, Age). Попробуйте передать объект пользователя напрямую в fmt.Println(user). Убедитесь, что Go автоматически использует ваш метод для красивого вывода.",
        "theory": """
Кастомизация строкового представления пользователя.
""",
        "step_by_step": """
1. Создаем `type User struct { Name string; Age int }`.
2. Реализуем `String() string`.
3. Печатаем через `fmt.Println(u)`.
""",
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

func (u User) String() string {
	return fmt.Sprintf("Пользователь[Имя: %s, Возраст: %d]", u.Name, u.Age)
}

func main() {
	u := User{Name: "Дмитрий", Age: 31}
	fmt.Println(u)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Пользователь[Имя: Дмитрий, Возраст: 31]"""
            }
        ],
        "under_the_hood": """
`fmt.Println` форматирует строку через интерфейс `fmt.Stringer`.
""",
        "pitfalls": """
- Забыть метод `String()`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какой интерфейс имеет наивысший приоритет в `fmt`: `fmt.Stringer` или `fmt.Formatter`?»
**Ответ:** `fmt.Formatter` (если он реализован, `fmt` вызывает его метод `Format()`, игнорируя `String()`).
"""
    },
    {
        "num": 47,
        "title": "Различие типов: кастомный тип type MyInt int и паника при i.(int)",
        "task": "Создай тип MyInt int. Реализуй для него метод String() string. Присвой var i any = MyInt(5). Сделай type assertion i.(int) — получи панику. Объясни, почему MyInt и int — разные типы, хотя underlying type одинаковый.",
        "theory": """
**Строгая типизация Defined Types:**
- `type MyInt int` создает **новый уникальный тип** с базовым типом `int`;
- В интерфейсе сохраняется дескриптор типа `MyInt`, а не `int`;
- Поэтому Type Assertion `i.(int)` выбрасывает панику!
""",
        "step_by_step": """
1. Объявляем `type MyInt int`.
2. Реализуем `(m MyInt) String() string`.
3. Показываем панику при `i.(int)` и правильный `i.(MyInt)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type MyInt int

func (m MyInt) String() string {
	return fmt.Sprintf("MyInt(%d)", int(m))
}

func main() {
	var i any = MyInt(5)

	// 1. Правильный Type Assertion к точному типу MyInt:
	if val, ok := i.(MyInt); ok {
		fmt.Printf("1. Успешное приведение к MyInt: %s\n", val)
	}

	// 2. Попытка приведения к базовому типу int (ok == false):
	if _, ok := i.(int); !ok {
		fmt.Println("2. Приведение i.(int) вернуло false, так как MyInt != int в системе типов Go!")
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Успешное приведение к MyInt: MyInt(5)
# 2. Приведение i.(int) вернуло false, так как MyInt != int в системе типов Go!"""
            }
        ],
        "under_the_hood": """
Дескриптор `_type` для `MyInt` имеет уникальный адрес в памяти `.rodata`.
""",
        "pitfalls": """
- Ожидание, что Type Assertion автоматически приводит к базовому типу (Underlying Type).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем отличие `type MyInt int` (defined type) от `type MyInt = int` (type alias)?»
**Ответ:** Алиас `type MyInt = int` — это просто синоним того же самого типа `int` (Type Assertion `i.(int)` был бы успешен), а `type MyInt int` — совершенно новый самостоятельный тип.
"""
    },
    {
        "num": 48,
        "title": "Каверзный кейс: реализация интерфейса с Pointer Receiver и ошибка передачи значения",
        "task": "[Каверзный кейс]: Реализуй интерфейс с pointer receiver. Попробуй передать значение (а не указатель) структуры в функцию, принимающую интерфейс. Поймай ошибку компиляции.",
        "theory": """
Закрепление проверки Method Set компилятором.
""",
        "step_by_step": """
1. Создаем интерфейс `Resettable` с методом `Reset()`.
2. Реализуем на `*Counter`.
3. Показываем ошибку при передаче `Counter{}`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Resettable interface {
	Reset()
}

type Counter struct {
	val int
}

func (c *Counter) Reset() {
	c.val = 0
}

func DoReset(r Resettable) {
	r.Reset()
}

func main() {
	c := Counter{val: 100}

	// ❌ ОШИБКА: DoReset(c) -> Counter does not implement Resettable
	// ✅ ПРАВИЛЬНО: передавать указатель:
	DoReset(&c)

	fmt.Println("Счетчик после сброса:", c.val)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Счетчик после сброса: 0"""
            }
        ],
        "under_the_hood": """
Компилятор сверяет таблицы методов.
""",
        "pitfalls": """
- Забыть символ `&`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему компилятор не может сам взять адрес `&c` при передаче в функцию `DoReset(c)`?»
**Ответ:** Потому что передача аргумента по значению создает временную копию, и взятие ее адреса изменило бы только копию, что привело бы к скрытому логическому багу.
"""
    },
    {
        "num": 49,
        "title": "Композиция интерфейсов: type ReadWriter interface { io.Reader; io.Writer } и буфер",
        "task": "Композиция интерфейсов: type ReadWriter interface { io.Reader; io.Writer }. Создайте тип, удовлетворяющий этому интерфейсу (например, буфер в памяти).",
        "theory": """
Кастомный потоковый буфер.
""",
        "step_by_step": """
1. Реализуем структуру `RingBuffer`.
2. Реализуем `Read` и `Write`.
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

type ReadWriter interface {
	io.Reader
	io.Writer
}

type SimpleBuffer struct {
	storage []byte
}

func (b *SimpleBuffer) Write(p []byte) (int, error) {
	b.storage = append(b.storage, p...)
	return len(p), nil
}

func (b *SimpleBuffer) Read(p []byte) (int, error) {
	if len(b.storage) == 0 {
		return 0, io.EOF
	}
	n := copy(p, b.storage)
	b.storage = b.storage[n:]
	return n, nil
}

func main() {
	var rw ReadWriter = &SimpleBuffer{}
	rw.Write([]byte("Go Data"))

	out := make([]byte, 10)
	n, _ := rw.Read(out)

	fmt.Printf("Прочитано: %q\n", string(out[:n]))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Прочитано: "Go Data" """
            }
        ],
        "under_the_hood": """
Интерфейсный вызов через `itab`.
""",
        "pitfalls": """
- Срез `b.storage[n:]` оставляет аллокацию в памяти (переиспользование памяти).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова сложность удаления из начала среза `b.storage[n:]`?»
**Ответ:** $O(1)$ по времени, так как просто сдвигается указатель `Data` в `SliceHeader`.
"""
    },
    {
        "num": 50,
        "title": "Реализация интерфейса io.Writer для структуры CountingWriter со счетчиком записанных байт",
        "task": "Реализуйте интерфейс io.Writer для кастомной структуры, которая просто подсчитывает количество записанных в нее байт.",
        "theory": """
**Паттерн метрик потока (Counting Metrics Writer):**
- Подсчитывает объем переданного трафика без сохранения самих данных;
- Идеально для профилирования и сбора метрик Prometheus.
""",
        "step_by_step": """
1. Создаем `type CountingWriter struct { Count int64 }`.
2. Реализуем `(c *CountingWriter) Write(p []byte) (int, error)`.
3. Тестируем с `fmt.Fprintf`.
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

type CountingWriter struct {
	TotalBytes int64
}

func (cw *CountingWriter) Write(p []byte) (int, error) {
	cw.TotalBytes += int64(len(p))
	return len(p), nil
}

func main() {
	counter := &CountingWriter{}
	var w io.Writer = counter

	fmt.Fprintf(w, "Строка номер 1\n")
	fmt.Fprintf(w, "Вторая порция данных для аудита\n")

	fmt.Printf("Всего байт записано через интерфейс io.Writer: %d байт\n", counter.TotalBytes)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Всего байт записано через интерфейс io.Writer: 63 байт"""
            }
        ],
        "under_the_hood": """
`cw.TotalBytes` инкрементируется без аллокаций.
""",
        "pitfalls": """
- Конкурентная запись в `CountingWriter` из нескольких горутин без `atomic.AddInt64`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как сделать `CountingWriter` потокобезопасным без мьютексов?»
**Ответ:** Использовать атомарную операцию `atomic.AddInt64(&cw.TotalBytes, int64(len(p)))`.
"""
    },
    {
        "num": 51,
        "title": "Паттерн Адаптер для функций (Adapter Pattern / HandlerFunc) и реализация интерфейса Handler",
        "task": "Создай тип func(string) string. Сделай так, чтобы он реализовал интерфейс Handler с методом Handle(string) string. Используй method value (adapter pattern).",
        "theory": """
**Паттерн Adapter для функций (в стиле `http.HandlerFunc`):**
- Превращает обычную анонимную функцию в тип, реализующий интерфейс;
- Исключает необходимость объявлять отдельную структуру для каждого обработчика.
""",
        "step_by_step": """
1. Объявляем интерфейс `Handler` с методом `Handle(req string) string`.
2. Объявляем тип функции `type HandlerFunc func(string) string`.
3. Реализуем метод `(f HandlerFunc) Handle(req string) string { return f(req) }`.
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

type Handler interface {
	Handle(req string) string
}

type HandlerFunc func(string) string

func (f HandlerFunc) Handle(req string) string {
	return f(req)
}

func Execute(h Handler, payload string) {
	fmt.Println("Результат обработки:", h.Handle(payload))
}

func main() {
	// Анонимная функция приводится к типу HandlerFunc:
	upperAdapter := HandlerFunc(func(s string) string {
		return strings.ToUpper(s)
	})

	Execute(upperAdapter, "быстрый старт microservices")
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Результат обработки: БЫСТРЫЙ СТАРТ MICROSERVICES"""
            }
        ],
        "under_the_hood": """
Приведение функции к типу `HandlerFunc` позволяет компилятору связать таблицу `itab` интерфейса `Handler`.
""",
        "pitfalls": """
- Забыть вызвать `f(req)` внутри реализации метода.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как устроен `http.HandlerFunc` в стандартном пакете `net/http`?»
**Ответ:** `type HandlerFunc func(ResponseWriter, *Request)` реализует интерфейс `http.Handler` через метод `ServeHTTP(w, r)`, вызывающий `f(w, r)`.
"""
    },
    {
        "num": 52,
        "title": "Ловушка nil-интерфейса: почему returnsError() error возвращает err != nil == true",
        "task": "Каверзный случай: Nil interface vs Nil pointer: Напиши func returnsError() error { var err *MyCustomError = nil; return err }. Вызови её: err := returnsError(). Проверь if err != nil. Она вернет true! Почему? Потому что интерфейс err не пуст (он содержит тип *MyCustomError, значение которого nil).",
        "theory": """
Детальный разбор самого популярного вопроса собеседований по Go.
""",
        "step_by_step": """
1. Создаем структуру `CustomErr`.
2. Пишем функцию `returnsError() error`.
3. Показываем, что `err != nil` дает `true`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type CustomErr struct{}

func (c *CustomErr) Error() string {
	return "сбой кастомной логики"
}

func returnsError() error {
	var err *CustomErr = nil
	// Возвращаем типизированный указатель в интерфейс error:
	return err
}

func main() {
	err := returnsError()

	if err != nil {
		fmt.Printf("❌ ЛОВУШКА: err != nil равен TRUE!\n")
		fmt.Printf("   Тип интерфейса:   %T\n", err)
		fmt.Printf("   Значение данных:  %v\n", err)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# ❌ ЛОВУШКА: err != nil равен TRUE!
#    Тип интерфейса:   *main.CustomErr
#    Значение данных:  <nil>"""
            }
        ],
        "under_the_hood": """
Интерфейс `error` содержит `itab` со ссылкой на метатип `*CustomErr`.
""",
        "pitfalls": """
- Использование вспомогательных функций возврата ошибок с конкретным типом `*MyError`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как исправить функцию `returnsError()`, чтобы проверка `err == nil` работала корректно?»
**Ответ:** Либо объявить переменную как `var err error = nil`, либо делать `if err != nil { return err } return nil`.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 2: {len(exercises)} exercises.")
