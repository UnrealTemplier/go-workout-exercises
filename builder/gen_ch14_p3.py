# Chapter 14 Part 3: Exercises 53 to 77

exercises = [
    {
        "num": 53,
        "title": "Статическая проверка реализации интерфейса на этапе компиляции: var _ io.Writer = (*MyStruct)(nil)",
        "task": "Проверка реализации на этапе компиляции: Напишите специальную строчку кода (используя пустой идентификатор), которая заставит компилятор выдать ошибку прямо при сборке, если структура MyStruct вдруг перестанет реализовывать интерфейс io.Writer.",
        "theory": """
**Паттерн Compile-Time Interface Check:**
- Синтаксис: `var _ InterfaceName = (*ConcreteType)(nil)`;
- Выделяет 0 байт памяти и не выполняется в рантайме;
- Гарантирует падение компиляции с понятной ошибкой при рефакторинге, если структура перестанет удовлетворять интерфейсу.
""",
        "step_by_step": """
1. Создаем структуру `AuditLogger`.
2. Добавляем статическую проверку `var _ io.Writer = (*AuditLogger)(nil)`.
3. Реализуем метод `Write(p []byte) (int, error)`.
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

type AuditLogger struct{}

func (a *AuditLogger) Write(p []byte) (int, error) {
	fmt.Printf("[AUDIT]: %s", string(p))
	return len(p), nil
}

// 🛡️ СТАТИЧЕСКАЯ ПРОВЕРКА НА ЭТАПЕ КОМПИЛЯЦИИ:
// Если метод Write будет удален или сигнатура изменится, компилятор немедленно упадет при сборке!
var _ io.Writer = (*AuditLogger)(nil)

func main() {
	logger := &AuditLogger{}
	fmt.Fprintln(logger, "Событие авторизации пользователя")
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# [AUDIT]: Событие авторизации пользователя"""
            }
        ],
        "under_the_hood": """
Компилятор проверяет типы на фазе Typecheck и оптимизирует `var _` в 0 байт ассемблера.
""",
        "pitfalls": """
- Написание проверки без разыменования `var _ io.Writer = AuditLogger{}` для типов с Pointer Receiver.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Зачем нужна строка `var _ Interface = (*Type)(nil)` в библиотеках?»
**Ответ:** Для мгновенного обнаружения несовместимости типов в IDE и CI до запуска тестов и деплоя.
"""
    },
    {
        "num": 54,
        "title": "Интерфейс All (io.Reader + io.Writer + fmt.Stringer) и реализация структуры MegaBuffer",
        "task": "Создай интерфейс All, встраивающий io.Reader, io.Writer, fmt.Stringer. Покажи, что структура, реализующая All, автоматически удовлетворяет каждому встроенному интерфейсу.",
        "theory": """
Широкие композитные интерфейсы и автоматическая совместимость с подмножествами.
""",
        "step_by_step": """
1. Объявляем `type All interface { io.Reader; io.Writer; fmt.Stringer }`.
2. Создаем структуру `MegaBuffer`.
3. Присваиваем каждому из встроенных интерфейсов.
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

type All interface {
	io.Reader
	io.Writer
	fmt.Stringer
}

type MegaBuffer struct {
	buf bytes.Buffer
}

func (m *MegaBuffer) Read(p []byte) (int, error)  { return m.buf.Read(p) }
func (m *MegaBuffer) Write(p []byte) (int, error) { return m.buf.Write(p) }
func (m *MegaBuffer) String() string              { return m.buf.String() }

func main() {
	mb := &MegaBuffer{}
	var all All = mb

	// Автоматическая совместимость со всеми подмножествами интерфейса:
	var r io.Reader = all
	var w io.Writer = all
	var s fmt.Stringer = all

	fmt.Fprintf(w, "MegaBuffer инициализирован!")
	fmt.Printf("Stringer: %s\n", s.String())

	out := make([]byte, 10)
	n, _ := r.Read(out)
	fmt.Printf("Reader:   %q\n", string(out[:n]))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Stringer: MegaBuffer инициализирован!
# Reader:   "MegaBuffer" """
            }
        ],
        "under_the_hood": """
Преобразование `All` в `io.Reader` происходит через извлечение соответствующего `itab`.
""",
        "pitfalls": """
- Создание слишком широких интерфейсов в публичных API.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли переменную типа `All` передать в функцию, принимающую `io.Writer`?»
**Ответ:** ДА, поскольку набор методов `All` полностью содержит все методы `io.Writer`.
"""
    },
    {
        "num": 55,
        "title": "Функция пакетного вывода среза интерфейсов []fmt.Stringer",
        "task": "Напишите функцию, которая принимает слайс интерфейсов fmt.Stringer и выводит их строковое представление.",
        "theory": """
Пакетная полиморфная обработка.
""",
        "step_by_step": """
1. Пишем `PrintAllStringers(items []fmt.Stringer)`.
2. Передаем разнородные структуры, реализующие `String()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type City struct{ Name string }
func (c City) String() string { return "г. " + c.Name }

type Temperature float64
func (t Temperature) String() string { return fmt.Sprintf("%.1f°C", float64(t)) }

func PrintAllStringers(items []fmt.Stringer) {
	fmt.Println("Список строковых представлений:")
	for idx, item := range items {
		fmt.Printf("  #%d: %s\n", idx+1, item.String())
	}
}

func main() {
	stringers := []fmt.Stringer{
		City{Name: "Новосибирск"},
		Temperature(-15.5),
		City{Name: "Владивосток"},
	}

	PrintAllStringers(stringers)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Список строковых представлений:
#   #1: г. Новосибирск
#   #2: -15.5°C
#   #3: г. Владивосток"""
            }
        ],
        "under_the_hood": """
Срез хранит массив дескрипторов `iface`.
""",
        "pitfalls": """
- Попытка передать `[]City` напрямую в `[]fmt.Stringer`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как преобразовать `[]City` в `[]fmt.Stringer`?»
**Ответ:** Создать срез `res := make([]fmt.Stringer, len(cities))` и в цикле скопировать элементы.
"""
    },
    {
        "num": 56,
        "title": "Method Set для T и *T: асимметрия Value Receiver и Pointer Receiver в интерфейсах",
        "task": "Создай структуру T с методом Value() string (value receiver). Покажи, что var x T удовлетворяет интерфейсу Valuer. А var p *T тоже удовлетворяет (методы value receiver доступны и для pointer). Затем создай метод PointerMethod() только для *T. Покажи, что T не удовлетворяет интерфейсу с PointerMethod, а *T — удовлетворяет.",
        "theory": """
**Полная матрица Method Set в Go:**
| Тип | Доступные методы в Method Set |
| :--- | :--- |
| **`T`** (значение) | Только методы с **Value Receiver `(t T)`** |
| **`*T`** (указатель) | И методы **`(t T)`**, И методы **`(t *T)`** |
""",
        "step_by_step": """
1. Создаем интерфейсы `Valuer` и `Mutator`.
2. Создаем структуру `Item` с методами `(i Item) Value()` и `(i *Item) Mutate()`.
3. Проверяем совместимость.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Valuer interface {
	Value() string
}

type Mutator interface {
	Mutate()
}

type Item struct {
	text string
}

func (i Item) Value() string { return i.text }
func (i *Item) Mutate()       { i.text += "_mutated" }

func main() {
	var val Item = Item{text: "data"}
	var ptr *Item = &Item{text: "data"}

	// 1. Valuer удовлетворяют И значение, И указатель:
	var v1 Valuer = val // ✅ Успех
	var v2 Valuer = ptr // ✅ Успех
	fmt.Printf("v1: %s | v2: %s\n", v1.Value(), v2.Value())

	// 2. Mutator удовлетворяет ТОЛЬКО указатель:
	// var m1 Mutator = val // ❌ ОШИБКА КОМПИЛЯЦИИ: Item does not implement Mutator
	var m2 Mutator = ptr // ✅ Успех
	m2.Mutate()
	fmt.Printf("После Mutate: %s\n", ptr.text)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# v1: data | v2: data
# После Mutate: data_mutated"""
            }
        ],
        "under_the_hood": """
Компилятор автоматически генерирует враппер для вызова value-метода через указатель `(*T).Value`.
""",
        "pitfalls": """
- Передача значения в интерфейс, содержащий хотя бы один pointer-метод.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go нет автоматического авто-разыменования при передаче значения в интерфейс с pointer-методами?»
**Ответ:** Потому что интерфейс копирует значение при упаковке; вызов pointer-метода изменил бы временную копию внутри интерфейса, а не исходную переменную, что нарушило бы целостность данных.
"""
    },
    {
        "num": 57,
        "title": "Тестирование и Mocking: интерфейс DB с методом Save() и тестовая заглушка MockDB",
        "task": "Mocking (Заглушки для тестов): Создай интерфейс DB с методом Save(). Напиши функцию ProcessData(db DB). В main передай реальную базу, а для \"теста\" напиши структуру MockDB, которая просто пишет в консоль, и передай её.",
        "theory": """
**Паттерн Mocking в Go:**
- Интерфейсы позволяют легко изолировать бизнес-логику от внешних инфраструктурных сервисов (БД, сетевые API, очереди Kafka);
- В юнит-тестах вместо реальной базы передается легкий Mock-объект.
""",
        "step_by_step": """
1. Объявляем интерфейс `Database` с методом `Save(id int, data string) error`.
2. Создаем `MockDB` для тестов.
3. Пишем тестируемую функцию `RegisterUser(db Database, id int, name string)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Database interface {
	Save(id int, data string) error
}

// Тестовая заглушка (Mock):
type MockDB struct {
	SavedItems map[int]string
}

func (m *MockDB) Save(id int, data string) error {
	m.SavedItems[id] = data
	fmt.Printf("[MOCK DB]: Успешно сохранен ID=%d (%s)\n", id, data)
	return nil
}

func RegisterUser(db Database, id int, name string) error {
	return db.Save(id, name)
}

func main() {
	mock := &MockDB{SavedItems: make(map[int]string)}

	// Тестируем логику без подключения к реальной СУБД:
	err := RegisterUser(mock, 101, "Константин")
	if err != nil {
		panic(err)
	}

	fmt.Printf("Проверка состояния Mock: %+v\n", mock.SavedItems)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# [MOCK DB]: Успешно сохранен ID=101 (Константин)
# Проверка состояния Mock: map[101:Константин]"""
            }
        ],
        "under_the_hood": """
Интерфейсный вызов перенаправляется на `MockDB.Save`.
""",
        "pitfalls": """
- Использование тяжелых глобальных синглтонов базы данных вместо передачи интерфейса через параметры.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какие инструменты для автоматической генерации моков популярны в BigTech?»
**Ответ:** `mockery` и `uber-go/mock` (бывший `golang/mock`), генерирующие потокобезопасные моки по интерфейсам.
"""
    },
    {
        "num": 58,
        "title": "Демонстрация правил Method Set: почему T не получает методы *T автоматически",
        "task": "Напиши программу, демонстрирующую: *T получает все методы T (value receiver), но T не получает методы *T (pointer receiver) автоматически. Объясни правила method set.",
        "theory": """
Закрепление теоретических основ спецификации Go по Method Sets.
""",
        "step_by_step": """
1. Демонстрируем правила.
2. Проверяем вызовы.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Reader interface{ Read() string }
type Writer interface{ Write(string) }

type Document struct{ text string }

func (d Document) Read() string   { return d.text }
func (d *Document) Write(s string) { d.text = s }

func main() {
	doc := Document{text: "Hello"}
	ptr := &doc

	// *Document реализует И Reader, И Writer:
	var r1 Reader = ptr // ✅ Успех
	var w1 Writer = ptr // ✅ Успех
	_ = r1
	_ = w1

	// Document реализует ТОЛЬКО Reader:
	var r2 Reader = doc // ✅ Успех
	_ = r2
	// var w2 Writer = doc // ❌ Ошибка компиляции

	fmt.Println("Method Set правила подтверждены!")
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Method Set правила подтверждены!"""
            }
        ],
        "under_the_hood": """
Спецификация языка Go (Раздел Method Sets).
""",
        "pitfalls": """
- Смешивание получателей без понимания Method Set.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какой method set имеет интерфейсный тип?»
**Ответ:** Method set интерфейса — это в точности список методов, объявленных в этом интерфейсе.
"""
    },
    {
        "num": 59,
        "title": "Внедрение зависимостей (Dependency Injection): структура Service со встроенным DB интерфейсом",
        "task": "Внедрение зависимостей (DI): Добавь DB как поле в структуру Service. Создай NewService(db DB).",
        "theory": """
**Dependency Injection (DI) через конструктор:**
- Сервис зависит от интерфейса `Database`, а не конкретной реализации;
- Позволяет легко подменять Postgres на MySQL или Mock в тестах.
""",
        "step_by_step": """
1. Создаем `type Service struct { db Database }`.
2. Пишем конструктор `NewService(db Database) *Service`.
3. Реализуем метод `(s *Service) ProcessOrder(id int)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Database interface {
	Save(id int, data string) error
}

type OrderService struct {
	db Database // Зависимость в виде интерфейса
}

func NewOrderService(db Database) *OrderService {
	return &OrderService{db: db}
}

func (s *OrderService) CreateOrder(id int, item string) error {
	fmt.Println("Бизнес-логика: оформление заказа...")
	return s.db.Save(id, item)
}

type PostgresDB struct{}
func (p *PostgresDB) Save(id int, data string) error {
	fmt.Printf("[PostgreSQL]: Запись заказа %d: %q\n", id, data)
	return nil
}

func main() {
	pg := &PostgresDB{}
	service := NewOrderService(pg)

	_ = service.CreateOrder(5001, "MacBook Pro M3")
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Бизнес-логика: оформление заказа...
# [PostgreSQL]: Запись заказа 5001: "MacBook Pro M3" """
            }
        ],
        "under_the_hood": """
Поле `s.db` хранит 16-байтный дескриптор интерфейса.
""",
        "pitfalls": """
- Передача `nil` в конструктор `NewOrderService(nil)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go предпочитают явный DI через конструкторы вместо DI-фреймворков со скрытой магией?»
**Ответ:** Явный DI прост, прозрачен, статически проверяется компилятором и не требует магии рефлексии.
"""
    },
    {
        "num": 60,
        "title": "Каверзный кейс: nil interface против интерфейса с nil-указателем структуры и защитная проверка",
        "task": "[Каверзный кейс]: \"Nil interface\": объяви переменную типа интерфейс var s Shape. Сравни её с nil (должно быть true). Присвой ей указатель на структуру, который равен nil. Сравни снова (теперь false! Интерфейс внутри содержит тип, хотя указатель nil). Обработай эту ситуацию.",
        "theory": """
Закрепление обработки nil-указателей внутри интерфейсов.
""",
        "step_by_step": """
1. Создаем `var s Shape = nil`.
2. Создаем `var c *Circle = nil; s = c`.
3. Показываем смену статуса `s == nil`.
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

type Circle struct {
	R float64
}

func (c *Circle) Area() float64 {
	if c == nil {
		return 0 // Защитная проверка на nil receiver!
	}
	return 3.14 * c.R * c.R
}

func main() {
	var s Shape = nil
	fmt.Printf("1. Исходный интерфейс:  s == nil -> %t\n", s == nil)

	var c *Circle = nil
	s = c
	fmt.Printf("2. После s = (*Circle)(nil): s == nil -> %t (НЕ NIL!)\n", s == nil)

	// Благодаря защитной проверке if c == nil внутри метода, вызов безопасен:
	fmt.Printf("3. Вызов метода s.Area(): %.2f (без паники!)\n", s.Area())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Исходный интерфейс:  s == nil -> true
# 2. После s = (*Circle)(nil): s == nil -> false (НЕ NIL!)
# 3. Вызов метода s.Area(): 0.00 (без паники!)"""
            }
        ],
        "under_the_hood": """
При вызове `s.Area()` рантайм передает `data == nil` в качестве первого аргумента метода.
""",
        "pitfalls": """
- Отсутствие проверки `if c == nil` внутри метода при обращении к `c.R` (приведет к панике).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Может ли метод в Go безопасно вызываться на `nil`-указателе?»
**Ответ:** ДА! В Go `nil` является валидным получателем метода (Receiver), если тело метода не обращается к полям структуры без проверки `if recv == nil`.
"""
    },
    {
        "num": 61,
        "title": "Сравнение интерфейсов с nil: разница между чистым nil-интерфейсом и типизированным nil",
        "task": "Сравнение интерфейсов с nil: покажите разницу между nil-интерфейсом и интерфейсом, хранящим nil-указатель на конкретный тип.",
        "theory": """
Сравнение поведения интерфейсов.
""",
        "step_by_step": """
1. Иллюстрируем два состояния интерфейса.
2. Печатаем `%v` и `%T`.
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

type Dev struct{}
func (d *Dev) Work() {}

func main() {
	var w1 Worker = nil
	var dev *Dev = nil
	var w2 Worker = dev

	fmt.Printf("w1: значение=%v, тип=%T, w1 == nil -> %t\n", w1, w1, w1 == nil)
	fmt.Printf("w2: значение=%v, тип=%T, w2 == nil -> %t\n", w2, w2, w2 == nil)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# w1: значение=<nil>, тип=<nil>, w1 == nil -> true
# w2: значение=<nil>, тип=*main.Dev, w2 == nil -> false"""
            }
        ],
        "under_the_hood": """
`w1` — `(nil, nil)`, `w2` — `(*main.Dev, nil)`.
""",
        "pitfalls": """
- Ложные предположения о равенстве.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как называть интерфейс `w2`?»
**Ответ:** «Typed nil» (типизированный nil).
"""
    },
    {
        "num": 62,
        "title": "Гибкость потоков с io.Reader: подсчет пробелов CountSpaces(r io.Reader) (int, error)",
        "task": "Гибкость с io.Reader: Напишите функцию CountSpaces(r io.Reader) (int, error), которая подсчитывает количество пробелов в потоке данных. Продемонстрируйте её работу, передав туда сначала строку (обернутую в strings.NewReader), а затем открытый файл os.File.",
        "theory": """
Потоковая обработка любых объемов данных без загрузки всего файла в память.
""",
        "step_by_step": """
1. Пишем `CountSpaces(r io.Reader) (int, error)`.
2. Читаем буфером 64 байта в цикле.
3. Тестируем со `strings.NewReader` и `bytes.NewReader`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"io"
	"strings"
)

func CountSpaces(r io.Reader) (int, error) {
	buf := make([]byte, 64)
	spaces := 0

	for {
		n, err := r.Read(buf)
		if n > 0 {
			for _, b := range buf[:n] {
				if b == ' ' {
					spaces++
				}
			}
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			return spaces, err
		}
	}
	return spaces, nil
}

func main() {
	text := "Go — это выразительный, лаконичный, чистый и эффективный язык."
	count, _ := CountSpaces(strings.NewReader(text))

	fmt.Printf("Строка: %q\nКоличество пробелов: %d\n", text, count)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Строка: "Go — это выразительный, лаконичный, чистый и эффективный язык."
# Количество пробелов: 8"""
            }
        ],
        "under_the_hood": """
Потоковое чтение с фиксированным буфером памяти $O(1)$.
""",
        "pitfalls": """
- Выделение буфера размером со весь файл.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как обработать 100-гигабайтный файл логов с минимальным потреблением памяти?»
**Ответ:** Использовать потоковое чтение через `bufio.Scanner` или `io.Reader` с небольшим фиксированным буфером ($4..64$ КБ).
"""
    },
    {
        "num": 63,
        "title": "Type Assertion между интерфейсами: преобразование io.Writer к io.ReadWriter",
        "task": "Напиши программу с type assertion на interface: var w io.Writer = os.Stdout. Сделай w.(io.ReadWriter) — проверь, удастся ли. Объясни: os.Stdout — *os.File, который реализует io.Writer, но не io.ReadWriter (нет метода Read для stdout). Попробуй с файлом на чтение+запись.",
        "theory": """
**Динамическое приведение интерфейсов (Interface-to-Interface Assertion):**
- Синтаксис `rw, ok := w.(io.ReadWriter)` проверяет, реализует ли динамический объект, лежащий внутри `w`, расширенный интерфейс;
- `*os.File` реализует оба метода (`Read` и `Write`), поэтому проверка успешна.
""",
        "step_by_step": """
1. Инициализируем `var w io.Writer = os.Stdout`.
2. Проверяем `w.(io.ReadWriter)`.
3. Анализируем результат.
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
	var w io.Writer = os.Stdout

	// Проверяем, реализует ли лежащий внутри *os.File интерфейс io.ReadWriter:
	if rw, ok := w.(io.ReadWriter); ok {
		fmt.Printf("✅ Успех: %T реализует интерфейс io.ReadWriter!\n", rw)
	} else {
		fmt.Println("❌ Не реализует io.ReadWriter")
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# ✅ Успех: *os.File реализует интерфейс io.ReadWriter!"""
            }
        ],
        "under_the_hood": """
Рантайм строит новый `itab` для целевого интерфейса `io.ReadWriter`.
""",
        "pitfalls": """
- Одинарное приведение без `ok` в случае несовпадения интерфейсов (паника).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова стоимость приведения одного интерфейса к другому интерфейсу `i1.(Interface2)`?»
**Ответ:** Рантайм ищет методы в таблице `itab` и кэширует результат в глобальной хэш-таблице `itabTable` за $O(1)$ при повторных вызовах.
"""
    },
    {
        "num": 64,
        "title": "Генератор случайных букв на базе бесконечного ридера RandomLetterReader (io.Reader)",
        "task": "Стандартный io.Reader: Напиши свой тип, который удовлетворяет интерфейсу io.Reader и генерирует бесконечный поток случайных букв при чтении.",
        "theory": """
Генерация бесконечных потоков данных через `io.Reader`.
""",
        "step_by_step": """
1. Создаем структуру `RandomLetterReader`.
2. Реализуем метод `Read(p []byte) (int, error)`.
3. Ограничиваем чтение через `io.LimitReader`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"io"
	"math/rand"
)

type RandomLetterReader struct{}

func (RandomLetterReader) Read(p []byte) (n int, err error) {
	letters := "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
	for i := range p {
		p[i] = letters[rand.Intn(len(letters))]
	}
	return len(p), nil
}

func main() {
	randReader := RandomLetterReader{}

	// Читаем ровно 32 случайных символа с помощью io.LimitReader:
	limited := io.LimitReader(randReader, 32)

	result, err := io.ReadAll(limited)
	if err != nil {
		panic(err)
	}

	fmt.Printf("Случайный токен (32 байта): %s\n", string(result))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Случайный токен (32 байта): WvBskrKqLpMxzTyUqZaBcDeFgHiJkLmN"""
            }
        ],
        "under_the_hood": """
`io.LimitReader` оборачивает бесконечный ридер и возвращает `io.EOF` по достижении лимита.
""",
        "pitfalls": """
- Вызов `io.ReadAll` на бесконечном ридере без `LimitReader` (вызовет OOM-панику).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в стандартной библиотеке устроен генератор криптографических ключей `crypto/rand.Reader`?»
**Ответ:** Он реализован как глобальный `io.Reader`, считывающий псевдослучайные байты из `/dev/urandom` или системного вызова `getrandom(2)`.
"""
    },
    {
        "num": 65,
        "title": "Type Switch по нескольким интерфейсам: определение io.ReadWriter, io.Reader, io.Writer",
        "task": "Напиши программу с type switch на нескольких интерфейсах: определи, является ли значение io.Reader, io.Writer, io.Closer или комбинацией. Используй case io.ReadWriter:.",
        "theory": """
Инспекция интерфейсных возможностей объекта.
""",
        "step_by_step": """
1. Пишем `InspectStream(x any)`.
2. Используем `switch x.(type)` с интерфейсными кейсами.
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

func InspectStream(x any) {
	switch v := x.(type) {
	case io.ReadWriter:
		fmt.Printf("1. %T: Полнодуплексный поток (io.ReadWriter)\n", v)
	case io.Reader:
		fmt.Printf("2. %T: Поток только для чтения (io.Reader)\n", v)
	case io.Writer:
		fmt.Printf("3. %T: Поток только для записи (io.Writer)\n", v)
	default:
		fmt.Printf("4. %T: Не является потоковым объектом\n", v)
	}
}

func main() {
	InspectStream(bytes.NewBuffer(nil))
	InspectStream(strings.NewReader("тест"))
	InspectStream(42)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. *bytes.Buffer: Полнодуплексный поток (io.ReadWriter)
# 2. *strings.Reader: Поток только для чтения (io.Reader)
# 4. int: Не является потоковым объектом"""
            }
        ],
        "under_the_hood": """
Порядок `case` важен: более специфичные интерфейсы (`io.ReadWriter`) должны идти раньше общих (`io.Reader`).
""",
        "pitfalls": """
- Помещение `case io.Reader` перед `case io.ReadWriter` (перехватит `*bytes.Buffer` до проверки на запись).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Влияет ли порядок `case` в `type switch` над интерфейсами на результат?»
**Ответ:** ДА! Если тип удовлетворяет нескольким интерфейсам, выполнится первый подходящий по порядку `case`.
"""
    },
    {
        "num": 66,
        "title": "Интерфейс Validator с методом Validate() error и пакетная валидация ValidateAll",
        "task": "Создай интерфейс Validator с методом Validate() error. Реализуй для User и Order. Напиши функцию ValidateAll(items ...Validator) []error, которая валидирует всё и возвращает слайс ошибок.",
        "theory": """
**Паттерн композитной валидации (Composite Validation):**
- Единый контракт `Validator` для всех доменных моделей;
- Функция `ValidateAll` агрегирует ошибки всех сущностей.
""",
        "step_by_step": """
1. Создаем `type Validator interface { Validate() error }`.
2. Реализуем `User` и `Order`.
3. Пишем `ValidateAll(items ...Validator) []error`.
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

type Validator interface {
	Validate() error
}

type User struct {
	Email string
}

func (u User) Validate() error {
	if u.Email == "" {
		return errors.New("email пользователя не может быть пустым")
	}
	return nil
}

type Order struct {
	Amount float64
}

func (o Order) Validate() error {
	if o.Amount <= 0 {
		return errors.New("сумма заказа должна быть строго больше 0")
	}
	return nil
}

func ValidateAll(items ...Validator) []error {
	var errs []error
	for _, item := range items {
		if err := item.Validate(); err != nil {
			errs = append(errs, err)
		}
	}
	return errs
}

func main() {
	u1 := User{Email: ""}
	u2 := User{Email: "dev@avito.ru"}
	o1 := Order{Amount: -100}

	errorsList := ValidateAll(u1, u2, o1)

	fmt.Printf("Обнаружено %d ошибок валидации:\n", len(errorsList))
	for _, err := range errorsList {
		fmt.Printf("  • %v\n", err)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Обнаружено 2 ошибок валидации:
#   • email пользователя не может быть пустым
#   • сумма заказа должна быть строго больше 0"""
            }
        ],
        "under_the_hood": """
Полиморфный вызов методов `Validate()`.
""",
        "pitfalls": """
- Прерывание проверки на первой ошибке, когда требуется вернуть все ошибки формы.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как объединить срез ошибок `[]error` в одну ошибку в Go 1.20+?»
**Ответ:** С помощью функции `errors.Join(errs...)`.
"""
    },
    {
        "num": 67,
        "title": "Сортировка среза структур по предикату через slices.SortFunc (Go 1.21+)",
        "task": "Используй sort.Slice для сортировки среза структур по определенному полю (передав замыкание, реализующее логику less(i, j int) bool).",
        "theory": """
Современная сортировка без рефлексии.
""",
        "step_by_step": """
1. Создаем структуру `Product{Name string, Price float64}`.
2. Сортируем срез с помощью `slices.SortFunc`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"cmp"
	"fmt"
	"slices"
)

type Product struct {
	Name  string
	Price float64
}

func main() {
	products := []Product{
		{"Клавиатура", 4500},
		{"Монитор", 28000},
		{"Мышь", 2100},
	}

	// Сортировка по возрастанию цены:
	slices.SortFunc(products, func(a, b Product) int {
		return cmp.Compare(a.Price, b.Price)
	})

	fmt.Println("Товары по возрастанию цены:")
	for _, p := range products {
		fmt.Printf("  • %-12s: %.0f руб.\n", p.Name, p.Price)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Товары по возрастанию цены:
#   • Мышь        : 2100 руб.
#   • Клавиатура  : 4500 руб.
#   • Монитор     : 28000 руб."""
            }
        ],
        "under_the_hood": """
`slices.SortFunc` использует быстрый алгоритм pdqsort.
""",
        "pitfalls": """
- Использование медленного `sort.Slice` в горячих циклах.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `slices.SortFunc` эффективнее `sort.Slice`?»
**Ответ:** Потому что `sort.Slice` использует рефлексию `reflect.Swapper`, а `slices.SortFunc` типизирован дженериками и компилируется в прямой машинный код.
"""
    },
    {
        "num": 68,
        "title": "Цепочка Middleware для интерфейса Handler: LoggingMiddleware и AuthMiddleware",
        "task": "Создай middleware chain для своего интерфейса Handler (метод Handle(req string) string). Напиши LoggingMiddleware, AuthMiddleware, которые оборачивают Handler и возвращают новый Handler. Покажи композицию.",
        "theory": """
**Паттерн Middleware Chain (Декоратор):**
- Оборачивает базовый обработчик в цепочку слоев (логирование, аутентификация, метрики);
- Каждый слой реализует интерфейс `Handler` и делегирует вызов следующему обработчику.
""",
        "step_by_step": """
1. Создаем интерфейс `Handler`.
2. Пишем базовый `CoreHandler`.
3. Пишем декораторы `LoggingMiddleware` и `AuthMiddleware`.
4. Собираем цепочку и выполняем запрос.
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

type CoreHandler struct{}

func (CoreHandler) Handle(req string) string {
	return "Обработано: " + strings.ToUpper(req)
}

// Logging Middleware:
type LoggingMiddleware struct {
	next Handler
}

func (l LoggingMiddleware) Handle(req string) string {
	fmt.Printf("➡️ [LOG] Входящий запрос: %q\n", req)
	resp := l.next.Handle(req)
	fmt.Printf("⬅️ [LOG] Исходящий ответ: %q\n", resp)
	return resp
}

// Auth Middleware:
type AuthMiddleware struct {
	next Handler
}

func (a AuthMiddleware) Handle(req string) string {
	if strings.Contains(req, "anonymous") {
		return "403 Forbidden: Доступ запрещен"
	}
	return a.next.Handle(req)
}

func main() {
	var pipeline Handler = CoreHandler{}
	pipeline = LoggingMiddleware{next: pipeline}
	pipeline = AuthMiddleware{next: pipeline}

	fmt.Println("1. Запрос авторизованного пользователя:")
	_ = pipeline.Handle("order_id=123")

	fmt.Println("\n2. Запрос анонима:")
	resp := pipeline.Handle("anonymous_user")
	fmt.Println(resp)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Запрос авторизованного пользователя:
# ➡️ [LOG] Входящий запрос: "order_id=123"
# ⬅️ [LOG] Исходящий ответ: "Обработано: ORDER_ID=123"
# 
# 2. Запрос анонима:
# 403 Forbidden: Доступ запрещен"""
            }
        ],
        "under_the_hood": """
Стек вызовов формируется цепочкой вызовов методов `next.Handle`.
""",
        "pitfalls": """
- Нарушение порядка middleware (например, логирование после аутентификации не залогирует отфильтрованные запросы).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как строится HTTP Middleware в веб-фреймворках (Gin, Chi, Echo)?»
**Ответ:** По паттерну цепочки обязанностей (Chain of Responsibility / Decorator) над интерфейсом `http.Handler` или срезом `[]HandlerFunc`.
"""
    },
    {
        "num": 69,
        "title": "Полиморфное поведение срезов: почему []Developer нельзя привести к []Worker напрямую",
        "task": "Полиморфное поведение слайсов: Создайте интерфейс Worker с методом Work(). Создайте несколько структур-профессий. Напишите функцию, которая принимает []Worker и запускает их работу. Попробуйте передать туда срез конкретных структур []Developer напрямую и разберитесь, почему Go запрещает приведение срезов конкретных типов к срезам интерфейсов напрямую.",
        "theory": """
**Почему `[]ConcreteType` не приводится к `[]Interface`:**
- Срез `[]Developer` хранит элементы по 8 или 24 байта каждый;
- Срез `[]Worker` обязан хранить элементы по 16 байт (`itab + data`);
- Прямое приведение нарушило бы адресацию памяти. Требуется явное создание нового среза и конвертация за $O(N)$.
""",
        "step_by_step": """
1. Создаем интерфейс `Worker` и структуру `Developer`.
2. Пишем функцию `RunAll(workers []Worker)`.
3. Демонстрируем явную конвертацию.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Worker interface {
	Work() string
}

type Developer struct {
	Name string
}

func (d Developer) Work() string {
	return d.Name + " разрабатывает микросервисы"
}

func RunAll(workers []Worker) {
	for _, w := range workers {
		fmt.Println("  •", w.Work())
	}
}

func main() {
	devs := []Developer{
		{Name: "Иван"},
		{Name: "Мария"},
	}

	// ❌ ОШИБКА: RunAll(devs)
	// cannot use devs (variable of type []Developer) as []Worker value in argument to RunAll

	// ✅ ПРАВИЛЬНО: явная конвертация:
	workers := make([]Worker, len(devs))
	for i, d := range devs {
		workers[i] = d
	}

	fmt.Println("Запуск рабочей смены:")
	RunAll(workers)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Запуск рабочей смены:
#   • Иван разрабатывает микросервисы
#   • Мария разрабатывает микросервисы"""
            }
        ],
        "under_the_hood": """
При упаковке каждого элемента `workers[i] = d` рантайм создает 16-байтный дескриптор `iface`.
""",
        "pitfalls": """
- Попытка использовать `unsafe.Pointer` для каста срезов (приведет к повреждению памяти и панике).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go не предусмотрено автоматическое неявное преобразование `[]T` в `[]any`?»
**Ответ:** Чтобы не скрывать скрытую аллокацию памяти и цикл $O(N)$ за невинным вызовом функции. В Go все дорогостоящие операции должны быть явными.
"""
    },
    {
        "num": 70,
        "title": "Декоратор потока UpperWriter (io.Writer): перехват и трансформация в верхний регистр",
        "task": "Стандартный io.Writer: Напиши структуру UpperWriter, которая оборачивает os.Stdout, перехватывает записываемые байты, переводит их в верхний регистр (пакет bytes) и только потом пишет в консоль. Вызови fmt.Fprintln с твоим райтером.",
        "theory": """
Паттерн фильтрации и трансформации потока вывода на лету.
""",
        "step_by_step": """
1. Создаем структуру `UpperWriter{out io.Writer}`.
2. Реализуем `(u *UpperWriter) Write(p []byte) (int, error)`.
3. Используем `bytes.ToUpper(p)`.
4. Передаем в `fmt.Fprintln`.
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

type UpperWriter struct {
	target io.Writer
}

func NewUpperWriter(w io.Writer) *UpperWriter {
	return &UpperWriter{target: w}
}

func (u *UpperWriter) Write(p []byte) (int, error) {
	upperData := bytes.ToUpper(p)
	return u.target.Write(upperData)
}

func main() {
	writer := NewUpperWriter(os.Stdout)

	fmt.Fprintln(writer, "высоконагруженные сервисы на go")
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# ВЫСОКОНАГРУЖЕННЫЕ СЕРВИСЫ НА GO"""
            }
        ],
        "under_the_hood": """
`bytes.ToUpper` трансформирует срез байт в памяти до записи в дескриптор 1 (stdout).
""",
        "pitfalls": """
- Мутация входящего среза `p` на месте (входящий срез может принадлежать вызывающему коду).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как реализован `gzip.Writer` в стандартной библиотеке?»
**Ответ:** Он реализован как декоратор `io.Writer`, сжимающий байты алгоритмом DEFLATE перед передачей в нижележащий целевой `w io.Writer`.
"""
    },
    {
        "num": 71,
        "title": "Инспекция динамического типа Describe(i any) с выводом полей структуры через reflect",
        "task": "Напишите функцию Describe(i interface{}), которая печатает динамический тип и значение, а также, если возможно, использует reflect для вывода полей структуры.",
        "theory": """
Рефлексивный аудит произвольных типов.
""",
        "step_by_step": """
1. Пишем `Describe(i any)`.
2. Извлекаем `reflect.TypeOf` и `reflect.ValueOf`.
3. Если структура — выводим все поля.
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

type SessionInfo struct {
	UserID int
	Token  string
}

func Describe(i any) {
	if i == nil {
		fmt.Println("Объект равен nil")
		return
	}

	t := reflect.TypeOf(i)
	v := reflect.ValueOf(i)

	fmt.Printf("Тип: %s | Kind: %s\n", t.String(), t.Kind())

	if t.Kind() == reflect.Struct {
		fmt.Println("Поля структуры:")
		for idx := 0; idx < t.NumField(); idx++ {
			field := t.Field(idx)
			val := v.Field(idx)
			fmt.Printf("  • %-10s = %v (%s)\n", field.Name, val.Interface(), field.Type)
		}
	}
}

func main() {
	s := SessionInfo{UserID: 777, Token: "jwt_secret_token"}
	Describe(s)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Тип: main.SessionInfo | Kind: struct
# Поля структуры:
#   • UserID     = 777 (int)
#   • Token      = jwt_secret_token (string)"""
            }
        ],
        "under_the_hood": """
Рефлексия считывает смещения полей из метаданных рантайма.
""",
        "pitfalls": """
- Вызов `t.NumField()` на типах, не являющихся структурами (приведет к панике).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каковы риски использования рефлексии в критическом пути высоконагруженных систем?»
**Ответ:** Рефлексия отключает оптимизации компилятора (инлайнинг, escape-анализ), порождает лишние аллокации в куче и работает в 10–50 раз медленнее прямого машинного кода.
"""
    },
    {
        "num": 72,
        "title": "Глубокое сравнение reflect.DeepEqual: сравнение срезов, мап и сложных структур",
        "task": "Напиши функцию DeepEqual(a, b interface{}) bool, используя reflect.DeepEqual. Покажи, когда она полезна (сравнение слайсов, мап, структур с неэкспортируемыми полями).",
        "theory": """
**Функция `reflect.DeepEqual`:**
- Рекурсивно сравнивает вложенные структуры данных (срезы, мапы, указатели);
- Незаменима в юнит-тестах для верификации сложных DTO.
""",
        "step_by_step": """
1. Создаем структуры с неэкспортируемыми полями и срезами.
2. Сравниваем через `reflect.DeepEqual`.
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

type Config struct {
	Name  string
	Ports []int
}

func main() {
	c1 := Config{Name: "App", Ports: []int{80, 443}}
	c2 := Config{Name: "App", Ports: []int{80, 443}}
	c3 := Config{Name: "App", Ports: []int{80, 8080}}

	// Оператор c1 == c2 запрещен компилятором из-за среза Ports!
	fmt.Printf("DeepEqual(c1, c2): %t (полная идентичность)\n", reflect.DeepEqual(c1, c2))
	fmt.Printf("DeepEqual(c1, c3): %t (порты различаются)\n", reflect.DeepEqual(c1, c3))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# DeepEqual(c1, c2): true (полная идентичность)
# DeepEqual(c1, c3): false (порты различаются)"""
            }
        ],
        "under_the_hood": """
Рекурсивный обход графа объектов в памяти.
""",
        "pitfalls": """
- `reflect.DeepEqual(nilSlice, emptySlice)` вернет `false`, так как `nil != []`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что используют в BigTech вместо `reflect.DeepEqual` в тестах?»
**Ответ:** Библиотеку `github.com/google/go-cmp/cmp`, которая выводит понятный diff различий при падении теста.
"""
    },
    {
        "num": 73,
        "title": "Антипаттерн Interface Pollution: почему не нужно объявлять интерфейсы заранее",
        "task": "Напиши программу с interface pollution антипаттерном: создай интерфейс заранее, \"на всякий случай\". Перепиши правильно: accept interfaces, return structs — создай интерфейс там, где он используется (в функции-параметре), а не в определении типа.",
        "theory": """
**Антипаттерн Interface Pollution:**
- Создание интерфейса с 15 методами для единственной структуры «на всякий случай» или по привычке из Java/C#;
- **Идиоматичный подход Go:** Пишите конкретные структуры. Создавайте интерфейс только там, где реально появляется несколько реализаций или потребность в моках для тестов.
""",
        "step_by_step": """
1. Показываем антипаттерн `UserServiceInterface`.
2. Переписываем правильно: конкретная структура `UserService` и точечный интерфейс потребителя.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

// ❌ АНТИПАТТЕРН: Гигантский интерфейс заранее для единственной структуры:
// type UserServiceInterface interface { GetUser(); UpdateUser(); DeleteUser() ... }

// ✅ ИДИОМАТИЧНЫЙ GO: Конкретная структура:
type UserService struct{}

func (UserService) FetchUser(id int) string {
	return fmt.Sprintf("User#%d", id)
}

// ✅ Потребитель объявляет минимально необходимый интерфейс:
type UserFetcher interface {
	FetchUser(id int) string
}

func RenderUserProfile(f UserFetcher, id int) {
	fmt.Println("Профиль:", f.FetchUser(id))
}

func main() {
	svc := UserService{}
	RenderUserProfile(svc, 42)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Профиль: User#42"""
            }
        ],
        "under_the_hood": """
Меньше интерфейсных таблиц `itab` в бинарном файле.
""",
        "pitfalls": """
- Создание пары `MyService` и `IMyService` для каждого файла проекта.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go не используют префиксы `I` в именах интерфейсов (`IReader`, `IWriter`)?»
**Ответ:** Интерфейсы в Go описывают поведение и суффиксируются действием (`Reader`, `Writer`, `Formatter`, `Closer`).
"""
    },
    {
        "num": 74,
        "title": "Интерфейс сортировки sort.Interface (Len, Less, Swap) для среза BookSlice",
        "task": "Интерфейс сортировки: Создайте срез структур Book (название, год). Чтобы отсортировать этот срез с помощью стандартного метода sort.Sort, реализуйте для вашего типа (например, type BookSlice []Book) три метода интерфейса sort.Interface: Len(), Less(i, j int) bool и Swap(i, j int).",
        "theory": """
Реализация классического контракта `sort.Interface`.
""",
        "step_by_step": """
1. Создаем `Book{Title string, Year int}`.
2. Создаем `type BookSlice []Book`.
3. Реализуем `Len`, `Less`, `Swap`.
4. Сортируем через `sort.Sort`.
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

type Book struct {
	Title string
	Year  int
}

type BookSlice []Book

func (b BookSlice) Len() int           { return len(b) }
func (b BookSlice) Less(i, j int) bool { return b[i].Year < b[j].Year }
func (b BookSlice) Swap(i, j int)      { b[i], b[j] = b[j], b[i] }

func main() {
	books := BookSlice{
		{"The Go Programming Language", 2015},
		{"Concurrency in Go", 2017},
		{"Go in Action", 2015},
	}

	sort.Sort(books)

	fmt.Println("Книги отсортированы:")
	for _, book := range books {
		fmt.Printf("  [%d] %s\n", book.Year, book.Title)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Книги отсортированы:
#   [2015] The Go Programming Language
#   [2015] Go in Action
#   [2017] Concurrency in Go"""
            }
        ],
        "under_the_hood": """
Сортировка на месте без аллокаций.
""",
        "pitfalls": """
- Неправильный знак `<` в `Less` (приведет к обратной сортировке).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Является ли `sort.Sort` стабильной сортировкой?»
**Ответ:** НЕТ, `sort.Sort` не гарантирует сохранение порядка равных элементов. Для стабильной сортировки используют `sort.Stable`.
"""
    },
    {
        "num": 75,
        "title": "Паттерн Стратегия (Strategy Pattern) на базе интерфейса Sorter",
        "task": "Создайте и используйте интерфейс Sorter с методом Sort(data []int), реализуйте его с разными алгоритмами (пузырёк, выбор) и выберите стратегию во время выполнения.",
        "theory": """
**Паттерн Strategy через интерфейсы:**
- Позволяет динамически подменять алгоритмы в рантайме без изменения клиентского кода.
""",
        "step_by_step": """
1. Создаем интерфейс `Sorter` с методом `Sort(data []int)`.
2. Реализуем `BubbleSorter` и `SelectionSorter`.
3. Применяем стратегии.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Sorter interface {
	Sort(data []int)
}

type BubbleSorter struct{}

func (BubbleSorter) Sort(data []int) {
	n := len(data)
	for i := 0; i < n-1; i++ {
		for j := 0; j < n-i-1; j++ {
			if data[j] > data[j+1] {
				data[j], data[j+1] = data[j+1], data[j]
			}
		}
	}
}

type SelectionSorter struct{}

func (SelectionSorter) Sort(data []int) {
	n := len(data)
	for i := 0; i < n-1; i++ {
		minIdx := i
		for j := i + 1; j < n; j++ {
			if data[j] < data[minIdx] {
				minIdx = j
			}
		}
		data[i], data[minIdx] = data[minIdx], data[i]
	}
}

func ExecuteSort(s Sorter, arr []int) {
	s.Sort(arr)
	fmt.Printf("Отсортировано (%T): %v\n", s, arr)
}

func main() {
	arr1 := []int{5, 2, 9, 1}
	arr2 := []int{8, 3, 7, 4}

	ExecuteSort(BubbleSorter{}, arr1)
	ExecuteSort(SelectionSorter{}, arr2)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Отсортировано (main.BubbleSorter): [1 2 5 9]
# Отсортировано (main.SelectionSorter): [3 4 7 8]"""
            }
        ],
        "under_the_hood": """
Полиморфный вызов выбранного алгоритма.
""",
        "pitfalls": """
- Мутация исходного среза, если вызывающий код ожидал неизменяемости.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Где в Go чаще всего применяется паттерн Strategy?»
**Ответ:** В роутинге HTTP, балансировщиках нагрузки (Round-Robin vs Least Connections) и сериализаторах (JSON vs Protobuf).
"""
    },
    {
        "num": 76,
        "title": "Сравнение Generics Max[T cmp.Ordered] против пустых интерфейсов MaxInterface(a, b any)",
        "task": "Создай generic-функцию Max[T constraints.Ordered](a, b T) T и сравни с интерфейсным подходом MaxInterface(a, b interface{}) (interface{}, error). Покажи преимущества generics над пустыми интерфейсами.",
        "theory": """
**Преимущества Generics над `any` / `interface{}`:**
1. **Безопасность типов во время компиляции:** исключает ошибки времени выполнения;
2. **Нулевой оверхед (Zero Boxing Overhead):** данные передаются в регистрах CPU без упаковки в `eface` и аллокаций в куче;
3. **Прямой возврат точного типа `T`:** не требует Type Assertion со стороны вызывающего кода.
""",
        "step_by_step": """
1. Пишем `MaxGeneric[T cmp.Ordered](a, b T) T`.
2. Пишем `MaxInterface(a, b any) (any, error)`.
3. Сравниваем удобство и производительность.
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

// 1. Современный generic-подход (Go 1.21+):
func MaxGeneric[T cmp.Ordered](a, b T) T {
	if a > b {
		return a
	}
	return b
}

// 2. Устаревший интерфейсный подход (до Go 1.18):
func MaxInterface(a, b any) (any, error) {
	switch va := a.(type) {
	case int:
		if vb, ok := b.(int); ok {
			if va > vb {
				return va, nil
			}
			return vb, nil
		}
	}
	return nil, fmt.Errorf("несовместимые типы")
}

func main() {
	// Generic: строгая типизация и возврат int без кастов:
	maxInt := MaxGeneric(10, 25)
	maxStr := MaxGeneric("apple", "banana")

	fmt.Printf("Generic Max Int: %d\n", maxInt)
	fmt.Printf("Generic Max Str: %s\n", maxStr)

	// Interface: требуется проверка ошибки и Type Assertion:
	res, _ := MaxInterface(10, 25)
	val := res.(int)
	fmt.Printf("Interface Max:   %d\n", val)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Generic Max Int: 25
# Generic Max Str: banana
# Interface Max:   25"""
            }
        ],
        "under_the_hood": """
Generics используют механизм мономорфизации компилятора (GCShape Stenciling) для генерации быстрого кода.
""",
        "pitfalls": """
- Использование `any` для математических функций при наличии дженериков.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Когда следует использовать Generics, а когда интерфейсы?»
**Ответ:** Generics используют, когда алгоритм одинаков для разных типов и важна сохранность типа (контейнеры, слайсы, алгоритмы). Интерфейсы используют, когда у разных типов различается поведение (полиморфизм).
"""
    },
    {
        "num": 77,
        "title": "Неявное удовлетворение интерфейсов через Embedding: структура со встроенным bytes.Buffer",
        "task": "Напиши программу, которая демонстрирует implicit satisfaction через embedding: структура встраивает bytes.Buffer, поэтому автоматически удовлетворяет io.Reader, io.Writer, io.ByteReader и т.д.",
        "theory": """
**Встраивание структур для реализации интерфейсов:**
- Встраивание типа, реализующего методы интерфейса, автоматически передает эту реализацию внешней структуре;
- Позволяет за 1 строку кода удовлетворить десятку стандартных интерфейсов Go!
""",
        "step_by_step": """
1. Создаем `type CustomStream struct { bytes.Buffer; ID string }`.
2. Демонстрируем, что `CustomStream` автоматически удовлетворяет `io.Reader`, `io.Writer`, `io.ByteReader`, `fmt.Stringer`.
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

type CustomStream struct {
	bytes.Buffer // Встраивает десятки методов
	ID           string
}

func main() {
	stream := &CustomStream{ID: "session_001"}

	// CustomStream автоматически реализует io.Writer:
	var w io.Writer = stream
	fmt.Fprintf(w, "Данные для сессии %s", stream.ID)

	// CustomStream автоматически реализует io.Reader:
	var r io.Reader = stream
	data, _ := io.ReadAll(r)

	fmt.Printf("Прочитано из stream: %q\n", string(data))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Прочитано из stream: "Данные для сессии session_001" """
            }
        ],
        "under_the_hood": """
Методы `bytes.Buffer` экспортируются в `itab` структуры `CustomStream`.
""",
        "pitfalls": """
- Случайное затирание встроенных методов собственными функциями с несовпадающими сигнатурами.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Сколько интерфейсов стандартной библиотеки реализует `*bytes.Buffer`?»
**Ответ:** Более 6 интерфейсов: `io.Reader`, `io.Writer`, `io.ByteReader`, `io.ByteScanner`, `io.RuneReader`, `io.RuneScanner`, `io.WriterTo`, `io.ReaderFrom`, `fmt.Stringer`.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 3: {len(exercises)} exercises.")
