# Section 3: Exercises 31 to 45

exercises = [
    {
        "num": 31,
        "title": "Автоматическое форматирование кривого кода через gofmt",
        "task": "Используйте команду go fmt на файле с намеренно плохим форматированием кода и проанализируйте результат.",
        "theory": """
Инструмент `gofmt` (и команда-обертка `go fmt`) трансформирует синтаксическое дерево исходного файла в соответствии со строгими каноническими правилами Go:
- Отступы заменяются на символы табуляции (`\t`);
- Выравниваются знаки присваивания и типы в объявлениях структур;
- Очищаются лишние пустые строки (не более одной пустой строки подряд);
- Нормализуются пробелы вокруг операторов и выражений.
""",
        "step_by_step": """
1. Создаем файл `bad_format.go` с нарушенными отступами, сбитыми пробелами и неаккуратными скобками.
2. Запускаем `gofmt -d bad_format.go` для просмотра различий (diff).
3. Применяем форматирование: `go fmt bad_format.go`.
4. Проверяем идеально отформатированный файл.
""",
        "code_blocks": [
            {
                "filename": "bad_format.go (ДО форматирования)",
                "lang": "go",
                "code": """package    main
import (   "fmt"   )
type   User   struct{
Name string;    Age int; IsAdmin bool
}
func  main(  ){
x:=10;if x>5{
fmt.Println(   "x больше пяти"   )
}
}""",
                "note": "Кривой неформатированный код"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# Применяем форматирование
go fmt bad_format.go

cat bad_format.go""",
                "note": "Команда go fmt"
            },
            {
                "filename": "bad_format.go (ПОСЛЕ форматирования)",
                "lang": "go",
                "code": """package main

import "fmt"

type User struct {
	Name    string
	Age     int
	IsAdmin bool
}

func main() {
	x := 10
	if x > 5 {
		fmt.Println("x больше пяти")
	}
}""",
                "note": "Канонический результат gofmt"
            }
        ],
        "under_the_hood": """
`gofmt` парсит текст в AST (пакет `go/parser`), строит древовидную модель узлов языка и печатает её через `go/printer`. Это гарантирует, что семантика кода остается на 100% неизменной, меняется исключительно визуальное представление.
""",
        "pitfalls": """
- Настройка IDE: обязательно настройте вашу среду разработки (GoLand, VS Code) на запуск `gofmt` (или `goimports`) при каждом сохранении файла (`on save`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go приняты символы табуляции для отступов вместо 2/4 пробелов?»
**Ответ:** Табуляция позволяет каждому разработчику настраивать визуальный размер отступа в своей IDE по своему вкусу (2, 4 или 8 колонок), не изменяя байты исходного файла и не порождая конфликты форматирования в Git.
"""
    },
    {
        "num": 32,
        "title": "Локальная разработка модулей и директива replace в go.mod",
        "task": "Создай модуль calculator с пакетом calc. В другой директории создай модуль app, который импортирует calculator по локальному пути (replace в go.mod). Настрой replace директиву.",
        "theory": """
При разработке микросервисов или собственных библиотек часто возникает ситуация:
Вы пишете сервис `app` и одновременно дорабатываете общую библиотеку `calculator`. Библиотека еще не закоммичена в Git или находится в соседней папке на вашем ноутбуке.

Если просто написать `import "example.com/calculator/calc"`, Go попытается скачать модуль из интернета и выдаст ошибку 404.

Решение: **директива `replace` в файле `go.mod`**.
Она указывает компилятору перенаправить запросы к модулю на локальную директорию в вашей файловой системе:
`replace example.com/calculator => ../calculator`
""",
        "step_by_step": """
1. Создаем папку `calculator/`, инициализируем модуль `example.com/calculator`, создаем пакет `calc` с функцией `Multiply(a, b int) int`.
2. Создаем рядом папку `app/`, инициализируем модуль `example.com/app`.
3. В `app/go.mod` добавляем директиву `replace`.
4. В `app/main.go` импортируем `example.com/calculator/calc` и вызываем функцию.
""",
        "code_blocks": [
            {
                "filename": "calculator/go.mod",
                "lang": "text",
                "code": """module example.com/calculator

go 1.22.5""",
                "note": "Манифест модуля calculator"
            },
            {
                "filename": "calculator/calc/multiply.go",
                "lang": "go",
                "code": """package calc

func Multiply(a, b int) int {
	return a * b
}""",
                "note": "Пакет calc"
            },
            {
                "filename": "app/go.mod",
                "lang": "text",
                "code": """module example.com/app

go 1.22.5

require example.com/calculator v0.0.0

replace example.com/calculator => ../calculator""",
                "note": "Файл app/go.mod с директивой replace"
            },
            {
                "filename": "app/main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"example.com/calculator/calc"
)

func main() {
	res := calc.Multiply(6, 7)
	fmt.Printf("6 * 7 = %d (через локальный replace)\\n", res)
}""",
                "note": "Импорт локального модуля"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """cd app
go run .
# Вывод:
# 6 * 7 = 42 (через локальный replace)""",
                "note": "Успешный запуск без обращения в интернет"
            }
        ],
        "under_the_hood": """
Директива `replace` действует **только в основном (root) модуле** сборки. Если модуль `app` будет опубликован и кто-то импортирует его как зависимость, директивы `replace` из его `go.mod` будут проигнорированы компилятором.
""",
        "pitfalls": """
- Случайный коммит локального `replace` пути (вроде `=> /Users/alex/dev/lib`) в продакшен-ветку сломает CI/CD сборку у других разработчиков.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что появилось в Go 1.18 на замену директиве `replace` для локальной разработки нескольких модулей?»
**Ответ:** Механизм **Go Workspaces (`go.work`)**. Команда `go work init ./app ./calculator` создает файл рабочего пространства `go.work`, позволяя одновременно разрабатывать несколько модулей без модификации файлов `go.mod` и без риска случайно закоммитить временные `replace`.
"""
    },
    {
        "num": 33,
        "title": "Хронология инициализации: calculator.init() и main.init()",
        "task": "Функция инициализации пакета: Напишите функцию init() в пакете calculator, которая выводит текст \"Calculator init\". Напишите аналогичную функцию init() в пакете main. Запустите программу и посмотрите на порядок вывода сообщений.",
        "theory": """
При импорте пакета рантайм Go гарантирует:
1. Пакет `calculator` инициализируется **до того**, как пакет `main` начнет выполнять свой `init()`.
2. Функция `main.main()` стартует только после того, как завершились абсолютно все `init()` всех зависимостей.
""",
        "step_by_step": """
1. Добавляем `func init()` в `calculator/calc.go`.
2. Добавляем `func init()` в `main.go`.
3. Запускаем проект и анализируем порядок вывода строк.
""",
        "code_blocks": [
            {
                "filename": "calculator/calc.go",
                "lang": "go",
                "code": """package calculator

import "fmt"

func init() {
	fmt.Println("--> [1] Calculator init: регистрация математических драйверов")
}

func Add(a, b int) int { return a + b }""",
                "note": "Пакет calculator"
            },
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"hello_mod/calculator"
)

func init() {
	fmt.Println("--> [2] Main init: подготовка контекста приложения")
}

func main() {
	fmt.Println("--> [3] Main func: старт программы!")
	_ = calculator.Add(1, 2)
}""",
                "note": "Файл main.go"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run .
# Вывод:
# --> [1] Calculator init: регистрация математических драйверов
# --> [2] Main init: подготовка контекста приложения
# --> [3] Main func: старт программы!""",
                "note": "Строгая последовательность инициализации"
            }
        ],
        "under_the_hood": """
Функции `init()` каждого пакета исполняются ровно **один раз** за все время работы программы, даже если этот пакет импортируется в 50 разных местах проекта.
""",
        "pitfalls": """
- Попытка явного вызова `init()` из кода (например, `calculator.init()`) вызовет ошибку компиляции: `undefined: calculator.init`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что произойдет, если пакет импортирован в 10 разных файлах: сколько раз вызовется его функция `init()`?»
**Ответ:** Ровно один раз. Рантайм Go отслеживает статус инициализации каждого пакета и повторно `init()` не вызывает.
"""
    },
    {
        "num": 34,
        "title": "Чтение аргументов командной строки через os.Args",
        "task": "Напишите программу, читающую аргументы командной строки через os.Args и выводящую их количество и значения.",
        "theory": """
Пакет `os` предоставляет глобальный срез строк `os.Args` (`[]string`), содержащий аргументы командной строки:
- `os.Args[0]` — путь или имя самого запускаемого бинарного файла;
- `os.Args[1:]` — аргументы, переданные пользователем в терминале;
- `len(os.Args)` — общее количество элементов среза.
""",
        "step_by_step": """
1. Импортируем стандартный пакет `"os"`.
2. Проверяем длину `len(os.Args)`.
3. В цикле `for i, arg := range os.Args` выводим индекс и значение каждого переданного параметра.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"os"
)

func main() {
	fmt.Printf("Всего элементов в os.Args: %d\\n", len(os.Args))
	fmt.Printf("Имя исполняемого файла: %s\\n", os.Args[0])

	if len(os.Args) > 1 {
		fmt.Println("\\nПользовательские аргументы:")
		for i, arg := range os.Args[1:] {
			fmt.Printf("  Аргумент [%d]: %s\\n", i+1, arg)
		}
	} else {
		fmt.Println("\\nДополнительные аргументы не переданы.")
	}
}""",
                "note": "Обработка os.Args"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run . --port=8080 --env=production start
# Вывод:
# Всего элементов в os.Args: 4
# Имя исполняемого файла: /tmp/go-build.../exe/main
# 
# Пользовательские аргументы:
#   Аргумент [1]: --port=8080
#   Аргумент [2]: --env=production
#   Аргумент [3]: start""",
                "note": "Запуск с аргументами"
            }
        ],
        "under_the_hood": """
При старте процесса ядро Linux передает аргументы в стек процесса. Рантайм Go в функции `runtime.sysargs` считывает их и конвертирует C-строки (`char**`) в нативный срез строк Go `[]string`, присваивая его переменной `os.Args`.
""",
        "pitfalls": """
- Прямое обращение по индексу `os.Args[1]` без проверки `if len(os.Args) > 1` приведет к аварийной панике рантайма `panic: runtime error: index out of range [1] with length 1`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему для парсинга флагов (`-port`, `--env`) в продакшене не используют `os.Args` напрямую?»
**Ответ:** `os.Args` — это низкоуровневый срез. Он не валидирует типы, не поддерживает значения по умолчанию, справку `--help` и порядок флагов. Для этого используют стандартный пакет `flag` или промышленную библиотеку `spf13/pflag` / `cobra`.
"""
    },
    {
        "num": 35,
        "title": "Генерация UUID v4 через библиотеку github.com/google/uuid",
        "task": "Внешние зависимости: Найди библиотеку github.com/google/uuid. Скачай её через go get, импортируй и выведи сгенерированный UUID.",
        "theory": """
UUID (Universally Unique Identifier) — 128-битный уникальный идентификатор, стандартизированный RFC 4122.
В распределенных микросервисах UUID v4 генерируется на основе криптографически стойких случайных чисел и используется как:
- Primary Key в базах данных (PostgreSQL, MongoDB);
- Идентификатор запроса (Trace ID / Request ID / Correlation ID).

Официальная и самая популярная библиотека для Go — `github.com/google/uuid`.
""",
        "step_by_step": """
1. Скачиваем библиотеку: `go get github.com/google/uuid`.
2. Импортируем `"github.com/google/uuid"`.
3. Генерируем новый UUID через `uuid.New()`.
4. Преобразуем его в строку и выводим.
""",
        "code_blocks": [
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": "go get github.com/google/uuid",
                "note": "Загрузка google/uuid"
            },
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"github.com/google/uuid"
)

func main() {
	// Генерация нового случайного UUID v4
	id := uuid.New()

	fmt.Printf("Сгенерированный UUID: %s\\n", id.String())
	fmt.Printf("Версия UUID: %d\\n", id.Version())
	fmt.Printf("Размер в байтах: %d байт\\n", len(id))
}""",
                "note": "Использование google/uuid"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run .
# Вывод:
# Сгенерированный UUID: 6ba7b810-9dad-11d1-80b4-00c04fd430c8
# Версия UUID: 4
# Размер в байтах: 16 байт""",
                "note": "Результат генерации"
            }
        ],
        "under_the_hood": """
Тип `uuid.UUID` в `google/uuid` под капотом представляет собой обычный массив байт `[16]byte`. Он не выделяет память в куче при генерации и реализует интерфейсы `encoding.BinaryMarshaler`, `sql.Scanner` и `driver.Valuer`, что позволяет сохранять его в SQL-базу напрямую.
""",
        "pitfalls": """
- Функция `uuid.New()` в случае отказа генератора случайных чисел ОС вызывает `panic`. Если вам нужна безопасная обработка ошибок без паники, используйте `uuid.NewRandom()`, возвращающую `(UUID, error)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в высоконагруженных базах данных (PostgreSQL/MySQL B-Tree индексы) вместо чистого UUID v4 часто предпочитают UUID v7 или ULID?»
**Ответ:** UUID v4 абсолютно случаен, что приводит к сильной фрагментации страниц B-Tree индекса и падению скорости вставок (Write IOPS). UUID v7 и ULID содержат timestamp в старших битах, гарантируя монотонный порядок сортировки (time-ordered).
"""
    },
    {
        "num": 36,
        "title": "Семантическое версионирование и мажорные версии (v1 vs v2)",
        "task": "Создай модуль с несколькими версиями (используй git-теги v1.0.0, v2.0.0). В app импортируй разные версии одного модуля. Объясни, как Go обрабатывает semver.",
        "theory": """
**Semantic Import Versioning (Семантическое версионирование импортов) в Go:**
Спецификация SemVer (`vMAJOR.MINOR.PATCH`):
- `PATCH` (v1.0.1) — исправления багов (обратно совместимо).
- `MINOR` (v1.1.0) — новая функциональность (обратно совместимо).
- `MAJOR` (v2.0.0) — **ломающие изменения API (Breaking Changes)**.

**Фундаментальное правило Go:**
«Если старая и новая программы используют один и тот же путь импорта, новая версия должна быть обратно совместима со старой».

Следовательно:
- Версии `v0` и `v1` импортируются по базовому пути: `github.com/org/calc`.
- Начиная с версии `v2.0.0+`, **путь модуля обязан содержать суффикс `/v2`**:
  `module github.com/org/calc/v2`
- Это позволяет одной программе одновременно использовать и `v1`, и `v2` без конфликтов!
""",
        "step_by_step": """
1. Создаем модуль `v1` с `module example.com/mathlib` и функцией `Add(a, b int) int`.
2. Создаем модуль `v2` с `module example.com/mathlib/v2` и измененным API: `Add(numbers ...int) int`.
3. В приложении `app` импортируем **обе версии одновременно**.
""",
        "code_blocks": [
            {
                "filename": "mathlib/v1 (mathlib/calc.go)",
                "lang": "go",
                "code": """package mathlib

// API v1 принимает строго 2 аргумента
func Add(a, b int) int {
	return a + b
}""",
                "note": "Версия v1 библиотеки"
            },
            {
                "filename": "mathlib/v2 (mathlib/v2/calc.go)",
                "lang": "go",
                "code": """package mathlib

// API v2 принимает переменное число аргументов (breaking change!)
func Add(numbers ...int) int {
	total := 0
	for _, n := range numbers {
		total += n
	}
	return total
}""",
                "note": "Версия v2 библиотеки с суффиксом /v2 в go.mod"
            },
            {
                "filename": "app/main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	mathv1 "example.com/mathlib"
	mathv2 "example.com/mathlib/v2"
)

func main() {
	res1 := mathv1.Add(10, 20)
	res2 := mathv2.Add(10, 20, 30, 40)

	fmt.Printf("Результат через v1: %d\\n", res1)
	fmt.Printf("Результат через v2: %d\\n", res2)
}""",
                "note": "Совместное использование v1 и v2 в одном приложении"
            }
        ],
        "under_the_hood": """
Тулчейн Go рассматривает `example.com/mathlib` и `example.com/mathlib/v2` как **два совершенно разных независимых пакета**. В таблице символов линкера они имеют разные префиксы, что полностью исключает проблему «ада зависимостей» (Dependency Hell) и дублирования символов.
""",
        "pitfalls": """
- Выпуск версии `v2.0.0` в Git-теге без добавления `/v2` в файл `go.mod` — грубейшая ошибка, из-за которой `go get` откажется скачивать модуль или выдаст ошибку `module declares its path as ... but was required as ...`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что такое алгоритм MVS (Minimal Version Selection), используемый Go Modules?»
**Ответ:** Большинство пакетных менеджеров (npm, pip, cargo) по умолчанию выбирают *максимально новую* совместимую версию зависимости. Go выбирает **минимальную версию**, указанную в графе требований всех модулей проекта. Это гарантирует максимальную стабильность и воспроизводимость сборки.
"""
    },
    {
        "num": 37,
        "title": "Инкапсуляция и Go-стиль геттеров (secretCode и SecretCode)",
        "task": "В пакете mathops создай переменную secretCode (с маленькой буквы) и функцию GetSecretCode (с большой). Попробуй обратиться к secretCode из main (поймай ошибку) и получи доступ через функцию.",
        "theory": """
В Go инкапсуляция полей структур и переменных пакета реализуется через функции-аксессоры (геттеры/сеттеры).

**Важное соглашение Effective Go по геттерам:**
В отличие от Java/C# (`getSecretCode()`), в Go в имени геттера **не принято писать префикс `Get`**!
- Переменная/поле: `secretCode` (или `owner`)
- Геттер: `SecretCode()` (или `Owner()`)
- Сеттер: `SetSecretCode(code string)` (или `SetOwner(o string)`)
""",
        "step_by_step": """
1. В `mathops/` объявляем приватную переменную `var secretCode = "SUPER_SECRET_KEY_2026"`.
2. Объявляем экспортируемый геттер `SecretCode() string`.
3. В `main.go` читаем значение через геттер.
""",
        "code_blocks": [
            {
                "filename": "mathops/secret.go",
                "lang": "go",
                "code": """package mathops

// Приватная переменная пакета
var secretCode = "SEC-9988-AUTH-TOKEN"

// SecretCode — идиоматичный Go-геттер (без префикса Get!)
func SecretCode() string {
	return secretCode
}""",
                "note": "Пакет mathops"
            },
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"hello_mod/mathops"
)

func main() {
	// 1. Попытка прямого доступа:
	// fmt.Println(mathops.secretCode) // ОШИБКА: cannot refer to unexported name

	// 2. Доступ через публичный геттер:
	code := mathops.SecretCode()
	fmt.Printf("Секретный ключ успешно получен: %s\\n", code)
}""",
                "note": "main.go"
            }
        ],
        "under_the_hood": """
Компилятор Go инлайнит (function inlining) простые однострочные геттеры вроде `SecretCode()` на этапе оптимизации SSA. На уровне ассемблера вызов функции полностью устраняется и превращается в прямое чтение адреса памяти без накладных расходов на вызов функции (zero-cost abstraction).
""",
        "pitfalls": """
- Использование стиля `GetSecretCode` не является ошибкой компилятора, но сразу выдает разработчика, не знакомого с конвенциями сообщества Go.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Когда в Go все-таки допустим префикс `Get` в именах методов?»
**Ответ:** Префикс `Get` оправдан только тогда, когда метод выполняет нетривиальное действие (сетевой запрос, чтение из БД или парсинг), например `client.GetResource(ctx, id)`. Для простых геттеров полей структуры `Get` опускается.
"""
    },
    {
        "num": 38,
        "title": "Исследование структуры go.mod и роли go.sum",
        "task": "Исследование go.mod: Открой файл go.mod и go.sum. Изучи, как записалась зависимость uuid. Попробуй вручную удалить её из кода и запусти go mod tidy — посмотри, как обновится go.mod.",
        "theory": """
Файл **`go.sum`** — это криптографический реестр контрольных сумм всех используемых модулей.
Каждая строка в `go.sum` содержит:
`<путь_модуля> <версия> h1:<хэш>`

Например:
`github.com/google/uuid v1.6.0 h1:NIvaJDMOLLgnQqtS9L13Si...`

Зачем нужен `go.sum`?
1. **Защита от подмены кода (Supply Chain Attacks):** гарантирует, что автор библиотеки не изменил код версии `v1.6.0` втайне от всех.
2. **Верификация через Go Checksum Database (`sum.golang.org`):** Go проверяет хэш скачанного архива по глобальному публичному неизменяемому логу (Merkle Tree).
""",
        "step_by_step": """
1. Открываем `go.mod` и `go.sum`, находим строки с `google/uuid`.
2. Удаляем вызов и импорт `google/uuid` из `main.go`.
3. Запускаем `go mod tidy`.
4. Наблюдаем, как `go.mod` очищается от ненужной зависимости.
""",
        "code_blocks": [
            {
                "filename": "go.sum (Фрагмент)",
                "lang": "text",
                "code": """github.com/google/uuid v1.6.0 h1:NIvaJDMOLLgnQqtS9L13SiLgXA2zgWUpEvJ8kx4Pzp8=
github.com/google/uuid v1.6.0/go.mod h1:TIyPZe4MgqvFqtWhCDKEIlvZxxxvm618TFiP1UGKOEg=""",
                "note": "Контрольные суммы модуля и его go.mod"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# Удаляем зависимость из кода и очищаем:
go mod tidy

# Проверяем go.mod — require google/uuid исчез!
cat go.mod""",
                "note": "Автоматическая очистка через go mod tidy"
            }
        ],
        "under_the_hood": """
Префикс `h1:` в `go.sum` означает алгоритм хэширования SHA-256 для дерева файлов распакованного zip-архива модуля (Tree Hash).
""",
        "pitfalls": """
- `go.sum` — это **НЕ lockfile** (как `package-lock.json` или `poetry.lock`). Точные версии фиксируются в `go.mod`. `go.sum` нужен исключительно для криптографической валидации целостности.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что делать, если при сборке возникла ошибка `checksum mismatch` в `go.sum`?»
**Ответ:** Это признак серьезного инцидента безопасности: код версии в репозитории был изменен или произошла атака посредника (MitM). Ни в коем случае нельзя слепо удалять `go.sum`. Нужно выяснить причину расхождения хэшей с `sum.golang.org`.
"""
    },
    {
        "num": 39,
        "title": "Углубленный статический анализ проекта через go vet",
        "task": "Запустите статический анализатор кода с помощью go vet на вашем проекте и исправьте найденные предупреждения.",
        "theory": """
`go vet` проверяет логическую корректность конструкций языка, которые синтаксически валидны, но почти наверняка являются багами:
1. Ошибки аргументов `Printf` (`%s` для int).
2. Забытые `time.Sleep` в бесконечных циклах.
3. Копирование структур, содержащих `sync.Mutex` или `sync.WaitGroup`.
4. Использование замыканий с переменной цикла (до Go 1.22 loop variable capture).
5. Недостижимые инструкции после `return`.
""",
        "step_by_step": """
1. Создаем функцию с потенциальными скрытыми дефектами.
2. Запускаем `go vet ./...`.
3. Анализируем вывод и исправляем баги.
""",
        "code_blocks": [
            {
                "filename": "main.go (С багами)",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"sync"
)

type Counter struct {
	mu    sync.Mutex // Mutex НЕЛЬЗЯ передавать по значению (копировать)!
	count int
}

// ОШИБКА: передача структуры с мьютексом по значению вместо указателя (*Counter)
func incrementBad(c Counter) {
	c.mu.Lock()
	c.count++
	c.mu.Unlock()
}

func main() {
	// ОШИБКА: несоответствие типа в Printf
	fmt.Printf("Порт: %d\\n", "8080")
}""",
                "note": "Код со скрытыми ошибками"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go vet ./...
# Вывод go vet:
# ./main.go:13:20: incrementBad passes lock by value: main.Counter contains sync.Mutex
# ./main.go:21:2: fmt.Printf format %d has arg "8080" of wrong type string""",
                "note": "Предупреждения go vet"
            }
        ],
        "under_the_hood": """
Анализатор `copylocks` внутри `go vet` рекурсивно ищет любые типы, реализующие интерфейс `sync.Locker`. Если такой тип передается в функцию по значению, а не по указателю `*Type`, анализатор сигнализирует об ошибке, так как копия мьютекса создает независимый замок и ломает синхронизацию.
""",
        "pitfalls": """
- Забывать запускать `go vet` перед коммитом.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go нельзя копировать `sync.Mutex`?»
**Ответ:** `sync.Mutex` хранит внутреннее состояние блокировки (счетчик ожидающих горутин и бит блокировки). При копировании создается дубликат состояния. Разблокировка копии не разблокирует оригинал, что приводит к состоянию взаимной блокировки (Deadlock) или Data Race.
"""
    },
    {
        "num": 40,
        "title": "Разница между go build, go install, go run и переменная GOBIN",
        "task": "Создай модуль mymod с пакетом api. Сделай go build для получения исполняемого файла. Затем сделай go install. Найди, куда установился бинарник (GOBIN, GOPATH). Объясни разницу между go build, go install, go run.",
        "theory": """
Сравнение трех ключевых команд сборки:

| Команда | Куда сохраняется результат | Назначение |
| :--- | :--- | :--- |
| **`go run`** | Во временный каталог `/tmp/go-build...` (удаляется после завершения) | Быстрая отладка и разработка |
| **`go build`** | В текущую директорию (или путь `-o`) | Сборка артефактов для продакшена и Docker |
| **`go install`** | В `$GOBIN` (по умолчанию `$GOPATH/bin`) | Установка CLI-утилит и генераторов в систему |

Если переменная окружения `GOBIN` задана явно (`go env -w GOBIN=/usr/local/bin`), бинарники устанавливаются туда. Иначе — в `$GOPATH/bin`.
""",
        "step_by_step": """
1. Создаем модуль `mymod` с `package main`.
2. Выполняем `go build .` — проверяем появление `./mymod` в текущей папке.
3. Выполняем `go install .` — проверяем появление бинарника в `$(go env GOPATH)/bin`.
4. Запускаем утилиту из любого места терминала по имени.
""",
        "code_blocks": [
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# 1. go build создает локальный бинарник
go build -o mymod .
ls -l mymod

# 2. go install устанавливает бинарник глобально
go install .

# 3. Проверяем директорию GOPATH/bin
ls -l $(go env GOPATH)/bin/mymod

# 4. Если GOPATH/bin добавлен в PATH, вызываем напрямую:
mymod""",
                "note": "Сравнение go build и go install"
            }
        ],
        "under_the_hood": """
При `go install` для библиотечных пакетов (не `package main`) компилятор кэширует скомпилированные объектные файлы `.a` в кэш сборки `GOCACHE`. Исполняемый бинарник создается только для пакетов `package main`.
""",
        "pitfalls": """
- Запуск `go install` в папке библиотеки (где объявлен `package api`, а не `package main`) не создаст бинарник в `$GOBIN`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как установить конкретную версию утилиты (например, `mockgen`) без засорения `go.mod` текущего проекта?»
**Ответ:** `go install github.com/golang/mock/mockgen@v1.6.0`. Тулчейн Go скачает и соберет утилиту в изолированном контексте, поместит бинарник в `$GOBIN` и не внесет изменений в локальный `go.mod`.
"""
    },
    {
        "num": 41,
        "title": "Управление внешними библиотеками через pkg.go.dev и go get",
        "task": "Подключение внешней зависимости: Инициализируйте новый модуль. Найдите на GitHub или pkg.go.dev популярную библиотеку (например, github.com/google/uuid). Скачайте её с помощью go get github.com/google/uuid. Убедитесь, что в go.mod появилась запись, а также создался файл go.sum.",
        "theory": """
Официальный портал документации и поиска библиотек Go: **[pkg.go.dev](https://pkg.go.dev)**.
Там доступны:
- Полная документация с примерами кода;
- Лицензия пакета (MIT, Apache 2.0, BSD);
- Количество зависимостей и рейтинг безопасности;
- История версий модуля.
""",
        "step_by_step": """
1. Инициализируем модуль: `go mod init test_dep`.
2. Выполняем `go get github.com/google/uuid`.
3. Проверяем появление записей в `go.mod` и `go.sum`.
""",
        "code_blocks": [
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """mkdir -p test_dep && cd test_dep
go mod init test_dep
go get github.com/google/uuid

# Проверяем файлы
cat go.mod
cat go.sum""",
                "note": "Подключение библиотеки"
            }
        ],
        "under_the_hood": """
`go get` обращается к `proxy.golang.org`, который является высоконадежным CDN-прокси от Google, кэширующим исходники всех открытых Go-репозиториев в мире. Даже если автор удалит свой репозиторий на GitHub, ваш проект продолжит собираться благодаря кэшу прокси.
""",
        "pitfalls": """
- Использование непроверенных библиотек без аудита лицензий и активности коммитов.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что делать, если в корпоративной сети компании заблокирован доступ к `proxy.golang.org`?»
**Ответ:** Настроить внутренний корпоративный прокси (например, JFrog Artifactory, Athens или Nexus) и прописать его адрес в переменную окружения `GOPROXY=https://goproxy.company.ru,direct`.
"""
    },
    {
        "num": 42,
        "title": "Множественные init-функции в одном файле и разных файлах пакета",
        "task": "Несколько init-функций: Напишите две разные функции init() в одном файле main.go. Напишите еще одну в файле helper.go (тоже package main). Посмотрите, выполняются ли они все и в каком порядке.",
        "theory": """
В отличие от обычных функций, имя `init` **не является уникальным**!
- В одном файле `.go` разрешено иметь **сколько угодно функций `init()`**.
- Они выполняются строго **сверху вниз** в порядке их объявления в тексте файла.
- Между разными файлами одного пакета функции `init()` выполняются в алфавитном порядке имен файлов.
""",
        "step_by_step": """
1. В `helper.go` объявляем `func init()` (файл на букву 'h').
2. В `main.go` объявляем две функции `func init()` подряд (файл на букву 'm').
3. Запускаем `go run .` и смотрим точный порядок.
""",
        "code_blocks": [
            {
                "filename": "helper.go",
                "lang": "go",
                "code": """package main

import "fmt"

func init() {
	fmt.Println("[1] helper.go -> init(): файл на букву 'h' идет первым по алфавиту")
}""",
                "note": "helper.go"
            },
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func init() {
	fmt.Println("[2] main.go -> init() #1: верхняя функция init в файле main.go")
}

func init() {
	fmt.Println("[3] main.go -> init() #2: нижняя функция init в файле main.go")
}

func main() {
	fmt.Println("[4] main() -> точка входа программы")
}""",
                "note": "main.go с двумя функциями init"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run .
# Вывод:
# [1] helper.go -> init(): файл на букву 'h' идет первым по алфавиту
# [2] main.go -> init() #1: верхняя функция init в файле main.go
# [3] main.go -> init() #2: нижняя функция init в файле main.go
# [4] main() -> точка входа программы""",
                "note": "Порядок вызова"
            }
        ],
        "under_the_hood": """
Компилятор собирает все блоки `init` пакета в единую функцию-цепочку на этапе кодогенерации, объединяя их в список последовательных инструкций `CALL`.
""",
        "pitfalls": """
- Написание более одной `init()` в одном файле усложняет чтение кода. В промышленной разработке рекомендуется иметь не более одной функции `init()` на файл.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли объявить несколько функций `main()` в разных файлах одного пакета `main`?»
**Ответ:** Нет! Функция `main` может быть объявлена ровно один раз на весь пакет. Повторное объявление `func main()` вызовет ошибку `main redeclared in this block`.
"""
    },
    {
        "num": 43,
        "title": "Кросс-компиляция без установки кросс-тулчейнов (GOOS и GOARCH)",
        "task": "Создай модуль, скомпилируй его в бинарник для текущей ОС. Затем скомпилируй кросс-платформенно: для Windows (GOOS=windows GOARCH=amd64), для Linux ARM (GOOS=linux GOARCH=arm64). Проверь бинарники командой file.",
        "theory": """
Кросс-компиляция в C/C++ — это сложнейший процесс, требующий установки кросс-компиляторов (`arm-linux-gnueabihf-gcc`), библиотек и заголовочных файлов.

**В Go кросс-компиляция встроена в ядро языка из коробки!**
Вам достаточно указать две переменные окружения:
- `GOOS` — целевая ОС (`linux`, `windows`, `darwin`, `freebsd`);
- `GOARCH` — целевая архитектура CPU (`amd64`, `arm64`, `arm`, `riscv64`, `386`).

Вы можете собрать бинарник для Linux ARM64 (например, для серверов Graviton в AWS или Raspberry Pi), находясь на Windows или macOS, одной командой!
""",
        "step_by_step": """
1. Компилируем для текущей ОС.
2. Компилируем для Windows x64: `GOOS=windows GOARCH=amd64 go build -o app.exe .`.
3. Компилируем для Linux ARM64: `GOOS=linux GOARCH=arm64 go build -o app-arm64 .`.
4. Проверяем типы собранных бинарников утилитой `file`.
""",
        "code_blocks": [
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# Сборка под Windows (создается PE32+ исполняемый файл)
GOOS=windows GOARCH=amd64 go build -o bin/app.exe .

# Сборка под Linux ARM64 (ELF 64-bit LSB aarch64)
GOOS=linux GOARCH=arm64 go build -o bin/app-arm64 .

# Проверка заголовков файлов
file bin/app.exe
# bin/app.exe: PE32+ executable (console) x86-64, for MS Windows

file bin/app-arm64
# bin/app-arm64: ELF 64-bit LSB executable, ARM aarch64, version 1 (SYSV)""",
                "note": "Кросс-компиляция под разные платформы"
            }
        ],
        "under_the_hood": """
Бэкэнд компилятора Go (`cmd/compile/internal/ssa`) содержит генераторы машинного кода для всех поддерживаемых процессорных архитектур. Поскольку стандартная библиотека Go написана на чистом Go и не зависит от C-библиотек ОС (при `CGO_ENABLED=0`), Go генерирует системные вызовы напрямую к ядру целевой ОС.
""",
        "pitfalls": """
- Если ваш проект использует CGO (интеграция с C-библиотеками через `#include <sqlite3.h>`), простая кросс-компиляция потребует кросс-компилятора C (`CGO_ENABLED=1 CC=aarch64-linux-gnu-gcc`). Поэтому в микросервисах стараются избегать CGO.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Dockerfile для Go-сервисов всегда пишут `CGO_ENABLED=0 GOOS=linux go build`?»
**Ответ:** `CGO_ENABLED=0` отключает линковку с динамической `glibc`. Полученный бинарник является 100% статическим и может запускаться в абсолютно пустом базовом Docker-образе `FROM scratch` размером всего 0 байт, обеспечивая минимальный размер контейнера и идеальную безопасность (нет уязвимостей в ОС).
"""
    },
    {
        "num": 44,
        "title": "Функция init() в main.go и гарантия очередности",
        "task": "Функция init() в main: Напиши функцию func init() в main.go. Выведи в ней сообщение. Убедись, что она вызывается до main().",
        "theory": """
Функция `init()` в пакете `main` идеально подходит для:
- Проверки обязательных переменных окружения перед стартом;
- Инициализации глобальных метрик Prometheus;
- Установки кастомного часового пояса (`time.Local`).
""",
        "step_by_step": """
1. В `main.go` объявляем `func init()`.
2. Проверяем условие или выводим метку инициализации.
3. В `main()` выводим рабочее сообщение.
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

var startTime time.Time

func init() {
	startTime = time.Now()
	fmt.Println("[INIT] Приложение инициализировано в:", startTime.Format(time.RFC3339))
}

func main() {
	fmt.Println("[MAIN] Основной цикл сервиса запущен!")
	fmt.Printf("[MAIN] Время с момента init: %v\\n", time.Since(startTime))
}""",
                "note": "Инициализация времени старта"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": "go run .",
                "note": "Запуск программы"
            }
        ],
        "under_the_hood": """
Рантайм Go инициализирует пакет `main` строго в одном потоке ОС (OS thread `M0`). Это гарантирует, что переменные, установленные в `init()`, будут гарантированно видны функции `main()` с точки зрения модели памяти Go (Memory Model Happens-Before).
""",
        "pitfalls": """
- Долгая синхронная работа в `init()` увеличивает время cold start сервиса в Kubernetes / Serverless.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что произойдет, если в `init()` вызвать `panic()`?»
**Ответ:** Программа немедленно аварийно завершится с дампом стека (stack trace). Функция `main()` даже не начнет выполняться.
"""
    },
    {
        "num": 45,
        "title": "Использование стороннего пакета google/uuid в боевой бизнес-логике",
        "task": "Использование стороннего пакета: Внедрите импорт github.com/google/uuid в ваш код. Сгенерируйте UUID версии 4 и выведите его в консоль.",
        "theory": """
Интеграция UUID в модель сущности бэкенда:
Создадим структуру заказа `Order` с уникальным идентификатором `ID`, суммой `Amount` и статусом.
""",
        "step_by_step": """
1. Создаем структуру `Order`.
2. Реализуем функцию-конструктор `NewOrder(amount float64) *Order`, генерирующую `uuid.NewString()`.
3. Создаем несколько заказов и выводим их данные.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"time"
	"github.com/google/uuid"
)

type Order struct {
	ID        string
	Amount    float64
	CreatedAt time.Time
}

func NewOrder(amount float64) *Order {
	return &Order{
		ID:        uuid.NewString(), // Быстрая генерация строкового представления UUID v4
		Amount:    amount,
		CreatedAt: time.Now(),
	}
}

func main() {
	order1 := NewOrder(1499.90)
	order2 := NewOrder(5200.00)

	fmt.Printf("Заказ #1: ID=%s, Сумма=%.2f руб, Время=%s\\n", 
		order1.ID, order1.Amount, order1.CreatedAt.Format("15:04:05"))
	fmt.Printf("Заказ #2: ID=%s, Сумма=%.2f руб, Время=%s\\n", 
		order2.ID, order2.Amount, order2.CreatedAt.Format("15:04:05"))
}""",
                "note": "Практическое использование UUID в моделях данных"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": "go run .",
                "note": "Запуск"
            }
        ],
        "under_the_hood": """
Метод `uuid.NewString()` аллоцирует строку размером 36 байт (формат `8-4-4-4-12`). Внутри он использует оптимизированное форматирование без тяжелого `fmt.Sprintf`, что минимизирует нагрузку на GC.
""",
        "pitfalls": """
- Генерация строкового UUID `string` занимает 36 байт, а бинарный `[16]byte` — всего 16 байт. В высоконагруженных кэшах и базах данных хранение в бинарном виде экономит гигабайты RAM.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова вероятность коллизии (совпадения) двух UUID v4?»
**Ответ:** Количество возможных комбинаций UUID v4 составляет $2^{122} \approx 5.3 \times 10^{36}$. Чтобы вероятность хотя бы одной коллизии составила $50%$, необходимо генерировать 1 миллиард UUID в секунду на протяжении 85 лет.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Section 3: {len(exercises)} exercises.")
