# Section 4: Exercises 46 to 60

exercises = [
    {
        "num": 46,
        "title": "Проектирование чистого API пакета mathops",
        "task": "Создай модуль calculator. Внутри создай пакет mathops. Напиши там функции Add и Subtract (с большой буквы!).",
        "theory": """
Качественный дизайн пакета в Go строится вокруг следующих принципов:
1. **Простота API:** экспортируйте только то, что действительно нужно пользователю пакета.
2. **Отсутствие избыточных абстракций:** не создавайте интерфейсы заранее, если у типа только одна конкретная реализация.
3. **Строгая типизация:** используйте явные числовые типы (`int`, `float64`, `int64`).
""",
        "step_by_step": """
1. Инициализируем модуль: `go mod init calculator`.
2. Создаем директорию `mathops/` и файл `mathops/operations.go`.
3. Реализуем экспортируемые функции `Add(a, b int) int` и `Subtract(a, b int) int`.
""",
        "code_blocks": [
            {
                "filename": "mathops/operations.go",
                "lang": "go",
                "code": """package mathops

// Add возвращает сумму двух целых чисел
func Add(a, b int) int {
	return a + b
}

// Subtract возвращает разность двух целых чисел
func Subtract(a, b int) int {
	return a - b
}""",
                "note": "Пакет mathops"
            }
        ],
        "under_the_hood": """
При компиляции пакета генерируется файл описания экспорта (export data), содержащий сигнатуры функций `Add` и `Subtract`. Другие пакеты при компиляции считывают только этот компактный заголовок, не тратя время на повторный парсинг тела функций.
""",
        "pitfalls": """
- Написание комментариев к публичным функциям, не начинающихся с имени самой функции. В GoDoc принято, чтобы комментарий начинался с имени документируемого идентификатора: `// Add возвращает...`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go не приветствуется создание пакета с именем `models` или `types`?»
**Ответ:** Пакет `models` быстро превращается в монолитную свалку разнородных структур всего проекта (User, Order, Payment, Metrics), порождая проблемы с циклическими зависимостями. В Go структуры разносят по контекстным доменным пакетам (`user`, `order`, `billing`).
"""
    },
    {
        "num": 47,
        "title": "Автоматизация сборки и запуска через Makefile",
        "task": "Создай Makefile (или скрипт) с целями: build, run, test, clean, install. Автоматизируй сборку и запуск.",
        "theory": """
В профессиональной бэкенд-разработке `Makefile` — это стандартный интерфейс команд для любого проекта:
- Новый разработчик в команде или агент CI/CD не должны помнить длинные флаги сборки;
- Достаточно выполнить `make build` или `make test`.

Ключевые директивы:
- `.PHONY` — указывает утилите `make`, что цели не являются именами файлов на диске;
- Переменные для флагов сборки и версионирования.
""",
        "step_by_step": """
1. Создаем в корне проекта файл `Makefile`.
2. Определяем переменные: `APP_NAME`, `BIN_DIR`.
3. Добавляем цели: `build`, `run`, `test`, `clean`, `install`, `lint`.
4. Тестируем вызовы `make build` и `make clean`.
""",
        "code_blocks": [
            {
                "filename": "Makefile",
                "lang": "makefile",
                "code": """.PHONY: all build run test lint clean install

APP_NAME := server
BIN_DIR := ./bin
SRC_DIR := .

all: test build

## build: Собрать оптимизированный бинарник
build:
	@echo "==> Сборка бинарника $(APP_NAME)..."
	@mkdir -p $(BIN_DIR)
	CGO_ENABLED=0 go build -ldflags="-s -w" -o $(BIN_DIR)/$(APP_NAME) $(SRC_DIR)

## run: Собрать и запустить приложение локально
run:
	@go run $(SRC_DIR)

## test: Запустить все юнит-тесты с детектором гонок
test:
	@echo "==> Запуск тестов..."
	@go test -v -race -cover ./...

## lint: Проверить проект через go vet
lint:
	@echo "==> Статический анализ..."
	@go vet ./...

## install: Установить бинарник в GOBIN
install:
	@go install $(SRC_DIR)

## clean: Удалить скомпилированные артефакты
clean:
	@echo "==> Очистка артефактов..."
	@rm -rf $(BIN_DIR)
	@go clean -cache""",
                "note": "Промышленный Makefile для Go-проекта"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """make build
# ==> Сборка бинарника server...

make clean
# ==> Очистка артефактов...""",
                "note": "Использование команд make"
            }
        ],
        "under_the_hood": """
В `Makefile` строки команд внутри целей **обязаны начинаться с символа табуляции (`\t`)**, а не пробелов. Использование пробелов приведет к ошибке утилиты Make: `missing separator`.
""",
        "pitfalls": """
- Забыть объявить `.PHONY` для целей: если на диске случайно появится файл или папка с именем `build`, команда `make build` решит, что цель уже собрана, и ничего не сделает!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Зачем во флаге `-ldflags` передают `\"-s -w\"`?»
**Ответ:** Флаг `-s` отключает генерацию таблицы символов (Symbol Table), а `-w` отключает отладочную информацию DWARF. Это уменьшает размер итогового Go-бинарника на 30–40% без потери производительности в runtime.
"""
    },
    {
        "num": 48,
        "title": "Импорт и интеграция пакета mathops в main",
        "task": "В пакете main импортируй свой пакет mathops и используй его функции.",
        "theory": """
Интеграция локального пакета в точку входа приложения демонстрирует слаженную работу модульной системы Go:
- Корневой модуль `calculator`;
- Импорт `"calculator/mathops"`;
- Вызов публичных функций через квалификатор `mathops.Add(...)`.
""",
        "step_by_step": """
1. В корневом `main.go` импортируем `"calculator/mathops"`.
2. Вычисляем сумму и разность.
3. Запускаем проект через `go run .`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"calculator/mathops"
)

func main() {
	a, b := 50, 18
	fmt.Printf("%d + %d = %d\\n", a, b, mathops.Add(a, b))
	fmt.Printf("%d - %d = %d\\n", a, b, mathops.Subtract(a, b))
}""",
                "note": "Файл main.go"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run .
# Вывод:
# 50 + 18 = 68
# 50 - 18 = 32""",
                "note": "Запуск приложения"
            }
        ],
        "under_the_hood": """
При импорте пакета тулчейн Go резолвит путь `calculator/mathops`, сопоставляя префикс `calculator` с корнем текущего модуля (где лежит `go.mod`), и находит подкаталог `mathops` на диске.
""",
        "pitfalls": """
- Попытка использовать `import "./mathops"` вместо `import "calculator/mathops"`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что произойдет, если в пакете `mathops` изменить код функции, не трогая сигнатуру: нужно ли перекомпилировать весь проект?»
**Ответ:** Компилятор Go благодаря инкрементальному кэшированию перекомпилирует только измененный пакет `mathops` и выполнит перелинковку `main`. Все остальные неизмененные пакеты берутся из `GOCACHE`.
"""
    },
    {
        "num": 49,
        "title": "Автоматическая нормализация зависимостей через go mod tidy",
        "task": "Очистка зависимостей: Удалите из кода main.go использование библиотеки uuid, но оставьте её в импортах. Выполните команду go mod tidy. Посмотрите, как изменились файлы go.mod и go.sum.",
        "theory": """
Если в коде остается строка `import "github.com/google/uuid"`, но сам идентификатор `uuid` нигде не вызывается:
1. Компилятор Go **запретит сборку** с ошибкой: `imported and not used: "github.com/google/uuid"`.
2. Команда `go mod tidy` анализирует AST-дерево. Если импорт не используется ни в одном файле пакета (или если удалить саму строку импорта), `go mod tidy` полностью удалит запись `require github.com/google/uuid` из `go.mod` и очистит неактуальные хэши в `go.sum`.
""",
        "step_by_step": """
1. Оставляем неиспользуемый импорт — проверяем ошибку `go build`.
2. Удаляем строку импорта из кода.
3. Выполняем `go mod tidy`.
4. Сверяем `git diff go.mod`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	// "github.com/google/uuid" — удален за ненадобностью
)

func main() {
	fmt.Println("Программа работает без внешних зависимостей!")
}""",
                "note": "Код без лишних импортов"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go mod tidy
# go.mod автоматически обновляется, удаляя лишний require

git diff go.mod
# -require github.com/google/uuid v1.6.0""",
                "note": "Очистка go.mod"
            }
        ],
        "under_the_hood": """
`go mod tidy` выполняет полный обход графа импортов для всех комбинаций операционных систем и билд-тегов (`GOOS`/`GOARCH`). Если библиотека используется только на Windows (в файле `app_windows.go`), `go mod tidy` не удалит её, даже если вы запускаете команду на Linux!
""",
        "pitfalls": """
- Ручное удаление строк из `go.mod` через текстовый редактор может привести к повреждению структуры манифеста. Всегда используйте `go mod tidy`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Удаляет ли `go mod tidy` зависимости, используемые исключительно в тестовых файлах `_test.go`?»
**Ответ:** Нет! `go mod tidy` учитывает зависимости, используемые как в основном коде, так и в тестах `_test.go`.
"""
    },
    {
        "num": 50,
        "title": "Хронология: mathutils.init() против main.init()",
        "task": "Порядок инициализации пакетов: Добавь init() в свой пакет mathutils. Импортируй его в main. Проследи, чей init() выполняется раньше (пакета или main).",
        "theory": """
Фундаментальный закон инициализации в Go:
**Инициализация зависимостей всегда предшествует инициализации зависимого пакета.**

Поскольку `main` зависит от `mathutils`, то `mathutils.init()` гарантированно завершится до того, как начнет выполняться `main.init()`.
""",
        "step_by_step": """
1. В `mathutils/mathutils.go` объявляем `func init()`.
2. В `main.go` объявляем `func init()` и `func main()`.
3. Запускаем программу и верифицируем вывод.
""",
        "code_blocks": [
            {
                "filename": "mathutils/mathutils.go",
                "lang": "go",
                "code": """package mathutils

import "fmt"

func init() {
	fmt.Println(">>> [ИНИЦИАЛИЗАЦИЯ] mathutils.init(): подготовка математических таблиц")
}

func Add(a, b int) int { return a + b }""",
                "note": "Пакет mathutils"
            },
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"calculator/mathutils"
)

func init() {
	fmt.Println(">>> [ИНИЦИАЛИЗАЦИЯ] main.init(): пакет main готов к запуску")
}

func main() {
	fmt.Println(">>> [РАБОТА] main.main(): старт вычислений")
	res := mathutils.Add(10, 20)
	fmt.Printf("Результат: %d\\n", res)
}""",
                "note": "main.go"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run .
# Вывод:
# >>> [ИНИЦИАЛИЗАЦИЯ] mathutils.init(): подготовка математических таблиц
# >>> [ИНИЦИАЛИЗАЦИЯ] main.init(): пакет main готов к запуску
# >>> [РАБОТА] main.main(): старт вычислений
# Результат: 30""",
                "note": "Порядок вывода строк"
            }
        ],
        "under_the_hood": """
Рантайм Go реализует детерминированный порядок: `Runtime Init -> Dependencies Init -> Main Package Init -> Main Function`.
""",
        "pitfalls": """
- Попытка положиться на то, что `main.init()` выполнится раньше зависимостей. В Go это архитектурно невозможно.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что будет, если в пакете `A` функция `init()` создает глобальную горутину, модифицирующую общую переменную, а пакет `B` читает ее в своем `init()`?»
**Ответ:** Это состояние гонки (Data Race) и недетерминированное поведение. До завершения всей фазы инициализации программы запуск горутин в `init()` с доступом к общему состоянию считается грубейшим антипаттерном.
"""
    },
    {
        "num": 51,
        "title": "Красивый табличный вывод в консоль через tablewriter",
        "task": "Используя github.com/olekukonko/tablewriter, создай красивую таблицу с данными (имя, возраст, город) минимум 5 строк.",
        "theory": """
При разработке консольных утилит (CLI) и системных инструментов бэкенда (управление кластером, миграции, просмотр метрик) табличное форматирование делает вывод структурированным и удобным для чтения.
Популярная библиотека — `github.com/olekukonko/tablewriter`.
""",
        "step_by_step": """
1. Скачиваем библиотеку: `go get github.com/olekukonko/tablewriter`.
2. В коде инициализируем `tablewriter.NewWriter(os.Stdout)`.
3. Задаем заголовки колонок через `table.SetHeader(...)`.
4. Добавляем строки данных и вызываем `table.Render()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"os"
	"strconv"
	"github.com/olekukonko/tablewriter"
)

type Employee struct {
	Name string
	Age  int
	City string
	Role string
}

func main() {
	employees := []Employee{
		{Name: "Александр Смирнов", Age: 29, City: "Москва", Role: "Senior Go Developer"},
		{Name: "Елена Васильева", Age: 25, City: "Санкт-Петербург", Role: "Backend Engineer"},
		{Name: "Дмитрий Кузнецов", Age: 34, City: "Новосибирск", Role: "Tech Lead"},
		{Name: "Ольга Попова", Age: 27, City: "Екатеринбург", Role: "DevOps Engineer"},
		{Name: "Иван Соколов", Age: 22, City: "Казань", Role: "Junior Go Developer"},
	}

	table := tablewriter.NewWriter(os.Stdout)
	table.SetHeader([]string{"ФИО Сотрудника", "Возраст", "Город", "Должность"})
	table.SetBorder(true)
	table.SetAutoWrapText(true)
	table.SetHeaderColor(
		tablewriter.Colors{tablewriter.Bold, tablewriter.FgCyanColor},
		tablewriter.Colors{tablewriter.Bold, tablewriter.FgYellowColor},
		tablewriter.Colors{tablewriter.Bold, tablewriter.FgGreenColor},
		tablewriter.Colors{tablewriter.Bold, tablewriter.FgMagentaColor},
	)

	for _, emp := range employees {
		table.Append([]string{
			emp.Name,
			strconv.Itoa(emp.Age),
			emp.City,
			emp.Role,
		})
	}

	table.Render()
}""",
                "note": "Генерация таблицы сотрудников"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run .
# +---------------------+---------+-----------------+---------------------+
# |   ФИО СОТРУДНИКА    | ВОЗРАСТ |      ГОРОД      |      ДОЛЖНОСТЬ      |
# +---------------------+---------+-----------------+---------------------+
# | Александр Смирнов   |      29 | Москва          | Senior Go Developer |
# | Елена Васильева     |      25 | Санкт-Петербург | Backend Engineer    |
# | Дмитрий Кузнецов    |      34 | Новосибирск     | Tech Lead           |
# | Ольга Попова        |      27 | Екатеринбург    | DevOps Engineer     |
# | Иван Соколов        |      22 | Казань          | Junior Go Developer |
# +---------------------+---------+-----------------+---------------------+""",
                "note": "Табличный вывод в консоль"
            }
        ],
        "under_the_hood": """
`tablewriter` производит предварительный расчет ширины колонок в символах (учитывая UTF-8 символы переменной длины) и выравнивает текст добавлением пробелов перед отправкой в поток `io.Writer`.
""",
        "pitfalls": """
- Использование `string(emp.Age)` для конвертации числа в строку! В Go `string(65)` вернет символ Unicode с кодом 65 (`'A'`), а не `"65"`. Для чисел всегда используйте `strconv.Itoa()` или `fmt.Sprint()`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `tablewriter.NewWriter` принимает интерфейс `io.Writer`, а не жесткий тип `*os.File`?»
**Ответ:** Это классический пример принципа открытости/закрытости (OCP) и гибкости Go. Принятие интерфейса `io.Writer` позволяет отрисовывать таблицу куда угодно: в stdout (`os.Stdout`), в файл (`os.File`), в память (`bytes.Buffer`) или напрямую в тело HTTP-ответа (`http.ResponseWriter`).
"""
    },
    {
        "num": 52,
        "title": "Псевдонимы пакетов при импорте (import calc \"hello_mod/calculator\")",
        "task": "Псевдонимы (алиасы) пакетов: Импортируйте ваш пакет calculator под другим именем (например, calc). Используйте новый алиас для вызова функций пакета: calc.Add(...).",
        "theory": """
Алиасы импорта позволяют переопределить локальное имя пакета в конкретном исходном файле:
`import calc "hello_mod/calculator"`

Теперь в коде все обращения к функциям производятся через `calc.Add()`.
""",
        "step_by_step": """
1. В `main.go` импортируем `hello_mod/calculator` с псевдонимом `calc`.
2. Вызываем `calc.Add(10, 20)`.
3. Запускаем программу.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	calc "hello_mod/calculator" // Задаем краткий алиас calc
)

func main() {
	sum := calc.Add(100, 200)
	fmt.Printf("Вычисление через алиас calc: %d\\n", sum)
}""",
                "note": "Импорт с алиасом calc"
            }
        ],
        "under_the_hood": """
Алиас попадает в локальную таблицу символов файла AST. Компилятор преобразует селектор `calc.Add` в вызов полного символа `hello_mod/calculator.Add`.
""",
        "pitfalls": """
- Попытка использовать исходное имя пакета `calculator.Add` после объявления алиаса `calc` вызовет ошибку: `undefined: calculator`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в Go импортировать две разные библиотеки с одинаковым именем пакета (например, `github.com/alice/logger` и `github.com/bob/logger`)?»
**Ответ:** Через алиасы импорта:
```go
import (
    alicelog "github.com/alice/logger"
    boblog "github.com/bob/logger"
)
```
"""
    },
    {
        "num": 53,
        "title": "Анонимный импорт (Blank Import) и выполнение побочных эффектов",
        "task": "Анонимный импорт (blank import): Импортируй пакет mathutils через _ \"путь/к/mathutils\". Убедись, что вызывается только его init(), а компилятор не ругается на неиспользуемый пакет.",
        "theory": """
В Go строжайше запрещены неиспользуемые импорты (ошибка компиляции `imported and not used`).

Что делать, если нам нужно **только выполнить функцию `init()` пакета** (например, зарегистрировать драйвер базы данных), но мы не вызываем ни одной функции из него напрямую?

Решение: **Blank Import (пустой идентификатор `_`)**:
`import _ "hello_mod/mathutils"`

Компилятор Go:
1. Включит пакет `mathutils` в сборку бинарника.
2. Выполнит его функцию `init()` до запуска `main()`.
3. Не выдаст ошибку о неиспользуемом пакете.
""",
        "step_by_step": """
1. В `main.go` пишем `import _ "hello_mod/mathutils"`.
2. В теле `main()` не пишем никаких вызовов `mathutils`.
3. Запускаем проект и видим, что `mathutils.init()` сработал!
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	_ "hello_mod/mathutils" // Blank import: импорт ТОЛЬКО ради выполнения init()
)

func main() {
	fmt.Println("Функция main() выполняется. Пакет mathutils не вызывался напрямую!")
}""",
                "note": "Blank import в main.go"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run .
# Вывод:
# >>> [ИНИЦИАЛИЗАЦИЯ] mathutils.init(): подготовка математических таблиц
# Функция main() выполняется. Пакет mathutils не вызывался напрямую!""",
                "note": "Выполнение init() при blank import"
            }
        ],
        "under_the_hood": """
При пустом импорте компилятор не связывает имя пакета ни с какой локальной переменной пространства имен, поэтому обращение по имени пакета невозможно, но линкер включает сегмент инициализации пакета в цепочку `inittasks`.
""",
        "pitfalls": """
- Злоупотребление blank-импортами для обычной бизнес-логики размывает зависимости проекта. Используйте `_` только для саморегистрации плагинов и драйверов.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему драйвер PostgreSQL `github.com/lib/pq` или `github.com/jackc/pgx/v5/stdlib` импортируют через `_`?»
**Ответ:** Пакет драйвера в своей функции `init()` вызывает стандартную функцию `sql.Register("postgres", &Driver{})`. Пользовательский код работает со стандартным пакетом `database/sql`, не вызывая методы драйвера напрямую.
"""
    },
    {
        "num": 54,
        "title": "Промышленный CLI на базе библиотеки github.com/spf13/cobra",
        "task": "Импортируй github.com/spf13/cobra и создай CLI-приложение с двумя командами: hello (приветствие) и time (текущее время). Добавь флаг --name для команды hello.",
        "theory": """
Библиотека **Cobra** — это общепризнанный мировой стандарт для создания CLI-приложений на Go.
На Cobra построены такие гиганты, как:
- `kubectl` (Kubernetes CLI);
- `docker` (Docker CLI);
- `gh` (GitHub CLI);
- `hugo` (генератор статических сайтов).

Архитектура Cobra:
- Команды представляют собой действия (`server start`, `config set`).
- Аргументы представляют сущности (`app deploy staging`).
- Флаги модифицируют поведение (`--port 8080`, `--verbose`).
""",
        "step_by_step": """
1. Скачиваем Cobra: `go get github.com/spf13/cobra`.
2. Создаем корневую команду `rootCmd`.
3. Создаем дочерние команды `helloCmd` и `timeCmd`.
4. Регистрируем флаг `--name` (`-n`) для `helloCmd`.
5. Вызываем `rootCmd.Execute()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"os"
	"time"
	"github.com/spf13/cobra"
)

var nameFlag string

func main() {
	// 1. Корневая команда
	rootCmd := &cobra.Command{
		Use:   "mycli",
		Short: "Учебная CLI-утилита для бэкенд-инженера",
		Long:  "Полноценный CLI инструмент с поддержкой вложенных команд и флагов на Go.",
	}

	// 2. Команда hello
	helloCmd := &cobra.Command{
		Use:   "hello",
		Short: "Вывести приветствие пользователю",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Printf("👋 Привет, %s! Успешной разработки на Go!\\n", nameFlag)
		},
	}
	// Привязка строкового флага --name (-n) со значением по умолчанию "Инженер"
	helloCmd.Flags().StringVarP(&nameFlag, "name", "n", "Инженер", "Имя для приветствия")

	// 3. Команда time
	timeCmd := &cobra.Command{
		Use:   "time",
		Short: "Показать текущее серверное время",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Printf("🕒 Текущее время (UTC): %s\\n", time.Now().UTC().Format(time.RFC3339))
			fmt.Printf("🕒 Локальное время:     %s\\n", time.Now().Format("2006-01-02 15:04:05"))
		},
	}

	// Регистрация команд в корневой
	rootCmd.AddCommand(helloCmd)
	rootCmd.AddCommand(timeCmd)

	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Ошибка выполнения: %v\\n", err)
		os.Exit(1)
	}
}""",
                "note": "Полноценный CLI на Cobra"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# 1. Автоматическая генерация справки
go run . --help

# 2. Вызов команды hello с флагом
go run . hello --name="Алексей"
# 👋 Привет, Алексей! Успешной разработки на Go!

# 3. Вызов команды time
go run . time
# 🕒 Текущее время (UTC): 2026-09-02T08:15:00Z
# 🕒 Локальное время:     2026-09-02 12:15:00""",
                "note": "Тестирование CLI-утилиты"
            }
        ],
        "under_the_hood": """
Cobra использует библиотеку `pflag` (POSIX-совместимый форк пакета `flag`). Она строит дерево команд и разбирает параметры командной строки с поддержкой флагов любого типа (`StringVarP`, `IntVarP`, `DurationVarP`), валидацией аргументов и генерацией автодополнения для bash/zsh/fish.
""",
        "pitfalls": """
- Забыть вызвать `rootCmd.AddCommand(...)` — команда не появится в списке доступных действий.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в Cobra организовать структуру файлов для большого микросервиса с десятками команд?»
**Ответ:** Создается пакет `cmd/` (`cmd/root.go`, `cmd/server.go`, `cmd/migrate.go`), где каждая команда объявляется в отдельном файле, а функция `Execute()` экспортируется и вызывается из тонкого `main.go`.
"""
    },
    {
        "num": 55,
        "title": "Пакеты models/user и models/order: имя папки как имя пакета",
        "task": "Создай пакеты models/user и models/order. Используй их в main. Обрати внимание на то, как Go трактует имя последней папки как имя пакета.",
        "theory": """
В Go имя пакета в коде (`package user`) **должно совпадать с именем последней директории в пути импорта** (`models/user`).

Сравните:
- Путь импорта: `"hello_mod/models/user"`
- Имя пакета: `package user`
- Использование в коде: `user.Entity` (а не `models_user.Entity`).
""",
        "step_by_step": """
1. Создаем папки `models/user/` и `models/order/`.
2. В `models/user/user.go` объявляем структуру `User` и конструктор `New(id int, name string) User`.
3. В `models/order/order.go` объявляем структуру `Order`.
4. В `main.go` импортируем оба пакета.
""",
        "code_blocks": [
            {
                "filename": "models/user/user.go",
                "lang": "go",
                "code": """package user

type User struct {
	ID   int
	Name string
}

func New(id int, name string) User {
	return User{ID: id, Name: name}
}""",
                "note": "Пакет models/user"
            },
            {
                "filename": "models/order/order.go",
                "lang": "go",
                "code": """package order

type Order struct {
	ID     string
	UserID int
	Total  float64
}

func New(id string, userID int, total float64) Order {
	return Order{ID: id, UserID: userID, Total: total}
}""",
                "note": "Пакет models/order"
            },
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"hello_mod/models/order"
	"hello_mod/models/user"
)

func main() {
	u := user.New(101, "Иван Петров")
	o := order.New("ORD-9901", u.ID, 4500.50)

	fmt.Printf("Пользователь: ID=%d, Имя=%s\\n", u.ID, u.Name)
	fmt.Printf("Заказ: ID=%s, UserID=%d, Сумма=%.2f руб\\n", o.ID, o.UserID, o.Total)
}""",
                "note": "main.go"
            }
        ],
        "under_the_hood": """
При компиляции тулчейн Go присваивает пакетам внутренние пути `hello_mod/models/user` и `hello_mod/models/order`. Однако идентификаторами селектора в коде остаются короткие имена `user` и `order`.
""",
        "pitfalls": """
- Если объявить `package models` внутри папки `models/user`, то при импорте возникнет коллизия имен: и `models/user`, и `models/order` будут претендовать на имя `models`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go функция создания структуры называется просто `New()`, а не `NewUser()`?»
**Ответ:** При импорте пакет уже квалифицирует имя: `user.New()` читается идеально лаконично и понятно. Название `user.NewUser()` содержало бы избыточное дублирование (stuttering).
"""
    },
    {
        "num": 56,
        "title": "Импорт ради побочных эффектов: _ \"hello_mod/calculator\"",
        "task": "Импорт ради побочных эффектов: Импортируйте пакет calculator с использованием пустого идентификатора _ \"hello_mod/calculator\". Убедитесь, что функция init() из него вызывается, даже если вы не используете функции пакета напрямую.",
        "theory": """
Паттерн «Импорт побочного эффекта» (Side-effect import) лежит в основе расширяемости Go:
- Регистрация драйверов баз данных (`database/sql`);
- Регистрация графических декодеров (`image/png`, `image/jpeg`);
- Регистрация HTTP эндпоинтов профилирования (`net/http/pprof`).
""",
        "step_by_step": """
1. Добавляем в `calculator` функцию `init()`, регистрирующую сообщение.
2. В `main.go` импортируем `_ "hello_mod/calculator"`.
3. Запускаем проект и наблюдаем срабатывание `init()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	_ "hello_mod/calculator"
)

func main() {
	fmt.Println("Основной процесс завершил работу.")
}""",
                "note": "main.go"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run .
# Вывод:
# --> [1] Calculator init: регистрация математических драйверов
# Основной процесс завершил работу.""",
                "note": "Срабатывание побочного эффекта"
            }
        ],
        "under_the_hood": """
Линкер Go включает все объектные файлы пакета, импортированного через `_`, в секцию инициализации и компонует его глобальные переменные.
""",
        "pitfalls": """
- Если пакет не содержит функции `init()` и глобальных переменных, blank import не произведет никакого видимого эффекта, но увеличит размер бинарника.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в Go устроен механизм `image.Decode` и зачем там нужен `import _ \"image/png\"`?»
**Ответ:** Пакет `image/png` в своей функции `init()` вызывает `image.RegisterFormat(\"png\", ...)`. При вызове `image.Decode(reader)` пакет `image` считывает первые байты (magic bytes) и находит зарегистрированный декодер для формата PNG.
"""
    },
    {
        "num": 57,
        "title": "Структурированное логирование с sirupsen/logrus и MultiWriter",
        "task": "Используя github.com/sirupsen/logrus, настрой логгер с разными уровнями (Debug, Info, Warn, Error). Запиши логи в файл и в консоль одновременно (multi-writer).",
        "theory": """
В современных бэкенд-сервисах обычный `fmt.Println` не подходит для логирования:
- Логи должны быть **структурированными** (JSON-формат для отправки в Elasticsearch/Kibana/ClickHouse);
- Должны поддерживаться **уровни логирования** (Debug, Info, Warn, Error, Fatal);
- Должен поддерживаться вывод одновременно в терминал разработчика и в файл логов через `io.MultiWriter`.
""",
        "step_by_step": """
1. Скачиваем logrus: `go get github.com/sirupsen/logrus`.
2. Создаем файл логов на диске `os.OpenFile("app.log", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)`.
3. Объединяем stdout и файл через `io.MultiWriter(os.Stdout, file)`.
4. Настраиваем `logrus.SetFormatter(&logrus.JSONFormatter{})`.
5. Пишем логи разных уровней с полями (`WithFields`).
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"io"
	"os"
	"github.com/sirupsen/logrus"
)

func main() {
	// Создаем/открываем файл логов
	logFile, err := os.OpenFile("app.log", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		logrus.Fatalf("Не удалось открыть файл логов: %v", err)
	}
	defer logFile.Close()

	// MultiWriter отправляет байты одновременно в консоль и в файл
	multiWriter := io.MultiWriter(os.Stdout, logFile)
	logrus.SetOutput(multiWriter)

	// Включаем вывод в формате JSON (стандарт для Kubernetes/ELK)
	logrus.SetFormatter(&logrus.JSONFormatter{
		TimestampFormat: "2006-01-02 15:04:05.000",
	})

	// Устанавливаем минимальный уровень логирования
	logrus.SetLevel(logrus.DebugLevel)

	// Логирование с метаданными (полями контекста)
	logrus.WithFields(logrus.Fields{
		"service": "billing-api",
		"env":     "production",
	}).Info("Сервис успешно запущен")

	logrus.WithFields(logrus.Fields{
		"user_id": 4821,
		"ip":      "192.168.1.55",
	}).Debug("Пользователь выполнил аутентификацию")

	logrus.WithFields(logrus.Fields{
		"latency_ms": 340,
		"threshold":  200,
	}).Warn("Высокое время ответа от платежного шлюза")

	logrus.WithFields(logrus.Fields{
		"error_code": "ERR_DB_TIMEOUT",
		"query":      "SELECT * FROM accounts",
	}).Error("Таймаут соединения с базой данных PostgreSQL")
}""",
                "note": "Структурированный JSON-логгер с MultiWriter"
            },
            {
                "filename": "Терминал (Вывод JSON-логов)",
                "lang": "bash",
                "code": """go run .
# {"env":"production","level":"info","msg":"Сервис успешно запущен","service":"billing-api","time":"2026-09-02 12:20:00.120"}
# {"ip":"192.168.1.55","level":"debug","msg":"Пользователь выполнил аутентификацию","time":"2026-09-02 12:20:00.122","user_id":4821}
# {"latency_ms":340,"level":"warning","msg":"Высокое время ответа от платежного шлюза","threshold":200,"time":"2026-09-02 12:20:00.123"}
# {"error_code":"ERR_DB_TIMEOUT","level":"error","msg":"Таймаут соединения с базой данных PostgreSQL","query":"SELECT * FROM accounts","time":"2026-09-02 12:20:00.124"}""",
                "note": "JSON-логи"
            }
        ],
        "under_the_hood": """
`io.MultiWriter` принимает срез `[]io.Writer` и в цикле вызывает метод `Write(p)` для каждого писателя. Если запись в один из дескрипторов завершится ошибкой, запись прерывается.
""",
        "pitfalls": """
- В сверхвысоконагруженных системах (HighLoad) `logrus` уступает по производительности современным zero-allocation логгерам: `go.uber.org/zap` или стандартному `log/slog` (начиная с Go 1.21).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем преимущество нового пакета `log/slog`, появившегося в Go 1.21?»
**Ответ:** `log/slog` — это официальный высокопроизводительный структурированный логгер прямо в стандартной библиотеке Go. Он предоставляет интерфейс `slog.Handler`, поддерживает JSON, текст и минимизирует аллокации в куче благодаря `slog.Attr`.
"""
    },
    {
        "num": 58,
        "title": "Экспериментальные пакеты golang.org/x/exp и Дженерики (Generic Min/Max)",
        "task": "Импортируй golang.org/x/exp/constraints и создай generic-функцию Min и Max для числовых типов. Объясни, почему этот пакет в x/exp, а не в стандартной библиотеке.",
        "theory": """
**Что такое репозитории `golang.org/x/...`?**
Помимо стандартной библиотеки, команда Go поддерживает официальные подрепозитории (Sub-repositories):
- `golang.org/x/crypto` — современные криптоалгоритмы (Argon2, Bcrypt, ChaCha20);
- `golang.org/x/net` — HTTP/2, WebSocket, парсинг HTML;
- `golang.org/x/sync` — расширенная синхронизация (`errgroup`, `semaphore`);
- `golang.org/x/exp` — **экспериментальные API (Experimental)**, которые находятся на этапе тестирования и обкатки сообществом.

Когда в Go 1.18 появились дженерики, констрейнт `constraints.Ordered` разместили в `x/exp`. В Go 1.21 его стабилизировали и перенесли в стандартную библиотеку как **`cmp.Ordered`** и функции `min()` / `max()`.
""",
        "step_by_step": """
1. Скачиваем `go get golang.org/x/exp/constraints`.
2. Пишем обобщенную (generic) функцию `Min[T constraints.Ordered](a, b T) T`.
3. Тестируем её с `int`, `float64` и `string`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"golang.org/x/exp/constraints"
)

// Min работает с любым сравнимым упорядоченным типом: числа, строки
func Min[T constraints.Ordered](a, b T) T {
	if a < b {
		return a
	}
	return b
}

// Max возвращает максимальное из двух значений
func Max[T constraints.Ordered](a, b T) T {
	if a > b {
		return a
	}
	return b
}

func main() {
	// Целые числа
	fmt.Printf("Min(10, 42) = %d\\n", Min(10, 42))

	// Дробные числа float64
	fmt.Printf("Max(3.14, 2.71) = %.2f\\n", Max(3.14, 2.71))

	// Строки (лексикографическое сравнение)
	fmt.Printf("Min('apple', 'banana') = %s\\n", Min("apple", "banana"))
}""",
                "note": "Generic Min и Max на Go"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run .
# Вывод:
# Min(10, 42) = 10
# Max(3.14, 2.71) = 3.14
# Min('apple', 'banana') = apple""",
                "note": "Результат вызова обобщенных функций"
            }
        ],
        "under_the_hood": """
Компилятор Go реализует дженерики методом **GCShape Stenciling (мономорфизация на основе формы типов)**. Для всех типов указателей генерируется один общий бинарный код (так как все указатели имеют одинаковый размер 8 байт), а для базовых типов значений (`int`, `float64`) компилятор генерирует специализированные машинные инструкции. Это предотвращает раздувание размера бинарника (code bloat).
""",
        "pitfalls": """
- Пакеты внутри `golang.org/x/exp` не защищены гарантией Go 1 Compatibility Promise и могут меняться или удаляться в будущих версиях.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем разница между ограничением `any` и `comparable` в дженериках Go?»
**Ответ:** `any` (псевдоним для `interface{}`) разрешает передачу абсолютно любого типа, но для него нельзя использовать операторы `==` и `!=`. Ограничение `comparable` разрешает передачу только тех типов, которые поддерживают сравнение на равенство `==` и могут быть ключами в `map`.
"""
    },
    {
        "num": 59,
        "title": "Анатомия go.mod: версия Go и requirements",
        "task": "Открой файл go.mod и изучи его содержимое. Найди версию Go и requirement.",
        "theory": """
Разберем каждую строчку стандартного `go.mod`:
```text
module github.com/myorg/myservice // 1. Имя модуля

go 1.22.5 // 2. Минимальная версия языка/тулчейна

require ( // 3. Блок зависимостей
    github.com/google/uuid v1.6.0 // Прямая зависимость
    github.com/stretchr/testify v1.9.0 // Прямая зависимость
    golang.org/x/sys v0.25.0 // indirect — транзитивная зависимость
)
```
""",
        "step_by_step": """
1. Открываем файл `go.mod`.
2. Анализируем блок `require`.
3. Обращаем внимание на маркеры `// indirect`.
""",
        "code_blocks": [
            {
                "filename": "go.mod",
                "lang": "text",
                "code": """module github.com/myorg/myservice

go 1.22.5

require (
	github.com/google/uuid v1.6.0
	github.com/sirupsen/logrus v1.9.3
	github.com/spf13/cobra v1.8.1
)

require (
	github.com/inconshreveable/mousetrap v1.1.0 // indirect
	github.com/spf13/pflag v1.0.5 // indirect
	golang.org/x/sys v0.25.0 // indirect
)""",
                "note": "Структура go.mod"
            }
        ],
        "under_the_hood": """
Если зависимость не используется непосредственно в ваших `.go` файлах, но требуется для компиляции одной из используемых библиотек, тулчейн Go автоматически группирует её в отдельный блок `require (...) // indirect`.
""",
        "pitfalls": """
- Удаление `// indirect` зависимостей вручную приведет к тому, что при следующей сборке Go снова добавит их обратно через `go mod tidy`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему некоторые зависимости попадают в блок `// indirect`, даже если мы их не импортировали?»
**Ответ:** Потому что модуль, который мы импортировали напрямую (например, `cobra`), зависит от `pflag`. Чтобы сборка была детерминированной и фиксировала точные хэши всех звеньев дерева зависимостей, они явно фиксируются в `go.mod`.
"""
    },
    {
        "num": 60,
        "title": "Тестовые зависимости github.com/stretchr/testify и go test",
        "task": "Создай модуль, добавь зависимость github.com/stretchr/testify (только для тестов). Убедись, что она попадает в go.mod с директивой // indirect. Затем напиши тест с assert.Equal и запусти go test.",
        "theory": """
Тестирование — неотъемлемая часть культуры Go.
Встроенный раннер тестов `go test` ищет все файлы с суффиксом `_test.go`.

Библиотека `github.com/stretchr/testify` — самый популярный фреймворк утверждений (assertions) и моков для Go, позволяющий писать выразительные тесты:
`assert.Equal(t, expected, actual)`
`assert.NoError(t, err)`
""",
        "step_by_step": """
1. Создаем функцию `Sum(numbers ...int) int` в `calc.go`.
2. Создаем файл тестов `calc_test.go`.
3. Импортируем `"github.com/stretchr/testify/assert"`.
4. Пишем тестовую функцию `TestSum(t *testing.T)`.
5. Запускаем `go test -v ./...`.
""",
        "code_blocks": [
            {
                "filename": "calc.go",
                "lang": "go",
                "code": """package main

// Sum суммирует произвольное количество чисел
func Sum(numbers ...int) int {
	total := 0
	for _, n := range numbers {
		total += n
	}
	return total
}""",
                "note": "Тестируемая функция"
            },
            {
                "filename": "calc_test.go",
                "lang": "go",
                "code": """package main

import (
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestSum(t *testing.T) {
	// Arrange (Подготовка)
	cases := []struct {
		name     string
		input    []int
		expected int
	}{
		{name: "Положительные числа", input: []int{1, 2, 3, 4}, expected: 10},
		{name: "Пустой срез", input: []int{}, expected: 0},
		{name: "Отрицательные числа", input: []int{-5, 5, -10}, expected: -10},
	}

	// Act & Assert (Тестирование)
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			actual := Sum(tc.input...)
			assert.Equal(t, tc.expected, actual, "Сумма чисел должна совпадать с ожидаемой")
		})
	}
}""",
                "note": "Табличный юнит-тест (Table-driven test)"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go test -v ./...
# === RUN   TestSum
# === RUN   TestSum/Положительные_числа
# === RUN   TestSum/Пустой_срез
# === RUN   TestSum/Отрицательные_числа
# --- PASS: TestSum (0.00s)
#     --- PASS: TestSum/Положительные_числа (0.00s)
#     --- PASS: TestSum/Пустой_срез (0.00s)
#     --- PASS: TestSum/Отрицательные_числа (0.00s)
# PASS
# ok      hello_mod       0.003s""",
                "note": "Успешный прогон тестов"
            }
        ],
        "under_the_hood": """
Команда `go test` компилирует специальный исполняемый файл `main`, включающий тестовый harness, запускает его в отдельном процессе, парсит вывод и возвращает код 0 (успех) или 1 (сбой теста). Исходный код тестов `_test.go` никогда не попадает в продакшен-бинарник, собранный через `go build`.
""",
        "pitfalls": """
- Тестовая функция обязана начинаться с префикса `Test` с заглавной буквы и принимать аргумент `(t *testing.T)`. Функция `testSum()` будет проигнорирована раннером.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что такое Table-Driven Tests (табличные тесты) в Go и почему они считаются золотым стандартом в BigTech?»
**Ответ:** Табличные тесты структурируют входные данные и ожидаемые результаты в виде среза анонимных структур (`[]struct{...}`). Это позволяет легко добавлять десятки граничных случаев (corner cases) без дублирования тестового кода и запускать их изолированно через `t.Run(tc.name, ...)`.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Section 4: {len(exercises)} exercises.")
