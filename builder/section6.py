# Section 6: Exercises 76 to 91

exercises = [
    {
        "num": 76,
        "title": "Паттерн Driver/Plugin Registry и саморегистрация через init()",
        "task": "Продемонстрируйте функцию init(): пакет автоматически регистрирует себя при импорте (выводит сообщение).",
        "theory": """
**Паттерн Driver Registry (Реестр драйверов/плагинов):**
Это один из важнейших архитектурных паттернов в Go. Он используется в:
- `database/sql` (регистрация драйверов БД: postgres, mysql, sqlite);
- `image` (декодеры png, jpeg, gif);
- `crypto` (алгоритмы хэширования SHA256, MD5).

Как это работает:
1. Базовый пакет `driver` предоставляет функцию `Register(name string, plugin Plugin)`.
2. Конкретные пакеты-реализации (например, `driver/postgres`) в своей функции `init()` вызывают `driver.Register("postgres", &PostgresPlugin{})`.
3. Пользовательское приложение подключает нужный плагин одной строкой blank-импорта:
   `import _ "hello_mod/driver/postgres"`
""",
        "step_by_step": """
1. Создаем пакет `driver/` с интерфейсом `Driver` и реестром `var registry = make(map[string]Driver)`.
2. Создаем подпакет `driver/memory/` с реализацией и саморегистрацией в `init()`.
3. В `main.go` импортируем `_ "hello_mod/driver/memory"` и вызываем драйвер из реестра.
""",
        "code_blocks": [
            {
                "filename": "driver/registry.go",
                "lang": "go",
                "code": """package driver

import (
	"fmt"
	"sync"
)

type Driver interface {
	Connect() string
}

var (
	mu      sync.RWMutex
	drivers = make(map[string]Driver)
)

func Register(name string, d Driver) {
	mu.Lock()
	defer mu.Unlock()
	if d == nil {
		panic("driver: попытка зарегистрировать nil драйвер")
	}
	if _, dup := drivers[name]; dup {
		panic("driver: дубликат регистрации драйвера " + name)
	}
	drivers[name] = d
	fmt.Printf("[РЕЕСТР] Драйвер '%s' успешно зарегистрирован в системе.\\n", name)
}

func Open(name string) (Driver, error) {
	mu.RLock()
	defer mu.RUnlock()
	d, ok := drivers[name]
	if !ok {
		return nil, fmt.Errorf("неизвестный драйвер: %s (забыли blank import?)", name)
	}
	return d, nil
}""",
                "note": "Базовый пакет driver с реестром"
            },
            {
                "filename": "driver/memory/memory.go",
                "lang": "go",
                "code": """package memory

import (
	"hello_mod/driver"
)

type MemoryDriver struct{}

func (m *MemoryDriver) Connect() string {
	return "Подключение к In-Memory хранилищу успешно установлено (RAM Engine)"
}

func init() {
	// Саморегистрация драйвера при импорте
	driver.Register("in-memory", &MemoryDriver{})
}""",
                "note": "Подпакет driver/memory с саморегистрацией в init()"
            },
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"hello_mod/driver"
	_ "hello_mod/driver/memory" // Подключаем драйвер через blank import
)

func main() {
	d, err := driver.Open("in-memory")
	if err != nil {
		panic(err)
	}
	fmt.Println("Статус:", d.Connect())
}""",
                "note": "Файл main.go"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run .
# Вывод:
# [РЕЕСТР] Драйвер 'in-memory' успешно зарегистрирован в системе.
# Статус: Подключение к In-Memory хранилищу успешно установлено (RAM Engine)""",
                "note": "Успешная работа паттерна Driver Registry"
            }
        ],
        "under_the_hood": """
Функция `memory.init()` выполняется на этапе инициализации до старта `main.main`. Она безопасно наполняет потокобезопасную мапу `drivers`, обеспечивая доступ к реализации по строковому ключу.
""",
        "pitfalls": """
- Забыть blank import в `main.go` — `driver.Open` вернет ошибку «неизвестный драйвер».
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в функции `driver.Register` вызывают `panic()`, а не возвращают ошибку `error`?»
**Ответ:** Регистрация драйверов происходит во время фазы `init()`. На этом этапе программа еще не начала работу, а дублирование драйвера или передача `nil` — это грубая ошибка на этапе компиляции/конфигурации разработчика (fail-fast principle), требующая немедленной остановки старта сервиса.
"""
    },
    {
        "num": 77,
        "title": "Профилирование сервиса через net/http/pprof и комбинированные импорты",
        "task": "Импортируйте пакет с алиасом (import f \"fmt\") и только ради побочных эффектов (import _ \"net/http/pprof\").",
        "theory": """
**`net/http/pprof` — секретное оружие Go-инженера в BigTech.**
Это встроенный пакет для сбора профилей производительности (CPU, Heap аллокации памяти, блокировки мьютексов, количество горутин) прямо на работающем боевом сервере!

Когда вы пишете:
`import _ "net/http/pprof"`
Пакет в своей функции `init()` автоматически регистрирует отладочные HTTP-ручки (`/debug/pprof/`, `/debug/pprof/profile`, `/debug/pprof/heap`, `/debug/pprof/goroutine`) на стандартном HTTP-мультиплексоре `http.DefaultServeMux`.
""",
        "step_by_step": """
1. В `main.go` импортируем `f "fmt"`, `_ "net/http/pprof"`, и `"net/http"`.
2. Запускаем фоновый HTTP-сервер на отдельном служебном порту (например, `:6060`).
3. В браузере или терминале открываем `http://localhost:6060/debug/pprof/`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	f "fmt"
	"net/http"
	_ "net/http/pprof" // Автоматическая регистрация ручек профилирования
	"time"
)

func main() {
	f.Println("=== СЕРВИС С ВСТРОЕННЫМ ПРОФАЙЛЕРОМ PPROF ===")

	// Запуск служебного HTTP-сервера для метрик и pprof
	go func() {
		f.Println("Pprof профайлер слушает на http://localhost:6060/debug/pprof/")
		if err := http.ListenAndServe("localhost:6060", nil); err != nil {
			f.Printf("Ошибка pprof сервера: %v\\n", err)
		}
	}()

	// Симуляция фоновой работы сервиса
	for i := 1; i <= 3; i++ {
		f.Printf("Сервис работает... Итерация %d\\n", i)
		time.Sleep(1 * time.Second)
	}
}""",
                "note": "Интеграция pprof профайлера"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# Запуск приложения
go run .

# В отдельном терминале: снятие профиля CPU через официальную утилиту go tool pprof
# go tool pprof http://localhost:6060/debug/pprof/profile?seconds=5""",
                "note": "Снятие профиля нагрузки"
            }
        ],
        "under_the_hood": """
`net/http/pprof` переводит ядро рантайма Go в режим профилирования: каждые 10 мс операционная система посылает процессу сигнал `SIGPROF`, рантайм перехватывает стек вызовов всех активных горутин и упаковывает сэмплы в бинарный protobuf-формат `profile.proto`.
""",
        "pitfalls": """
- Открытие эндпоинта `/debug/pprof/` в публичный интернет без авторизации — критическая уязвимость (утечка памяти и исходного кода). Профайлер всегда выносят на внутренний закрытый порт для служебной сети.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как на продакшен-сервере с помощью pprof найти утечку памяти (Memory Leak)?»
**Ответ:** Снять два последовательных дампа кучи (heap profile) с интервалом в 5 минут и сравнить их командой `go tool pprof -base heap1.pb.gz heap2.pb.gz`. Анализ разницы покажет, в каких функциях непрерывно растут не освобождаемые аллокации.
"""
    },
    {
        "num": 78,
        "title": "Спецификация Go: классификация символов Unicode и правила экспорта",
        "task": "Создайте несколько экспортируемых и неэкспортируемых функций, объясните правило заглавной буквы.",
        "theory": """
В спецификации языка Go экспорт идентификатора определяется строго математически:
«Идентификатор экспортируется, если:
1. Первый символ имени является **заглавной буквой Unicode (Unicode Class Lu / Upper Case Letter)**;
2. Идентификатор объявлен в блоке пакета (package block) или является именем поля/метода».

Это правило применяется ко всему:
- Функциям: `Calculate()` vs `calculate()`
- Структурам: `User` vs `user`
- Полям структур: `User.Email` vs `User.passwordHash`
- Методам: `(u *User) Save()` vs `(u *User) validate()`
- Константам: `MaxRetries` vs `defaultTimeout`
- Переменным: `DefaultClient` vs `activeConnections`
""",
        "step_by_step": """
1. Создаем структуру с комбинацией публичных и приватных полей и методов.
2. Проверяем доступность из внешнего пакета.
""",
        "code_blocks": [
            {
                "filename": "account/account.go",
                "lang": "go",
                "code": """package account

import "errors"

// Account — экспортируемая структура
type Account struct {
	ID      string  // Экспортируемое поле (публичное)
	Owner   string  // Экспортируемое поле (публичное)
	balance float64 // Неэкспортируемое поле (приватное! Защищено от прямой модификации)
}

func New(id, owner string, initialBalance float64) *Account {
	return &Account{
		ID:      id,
		Owner:   owner,
		balance: initialBalance,
	}
}

// Balance — публичный геттер для баланса
func (a *Account) Balance() float64 {
	return a.balance
}

// Deposit — публичный метод с бизнес-валидацией
func (a *Account) Deposit(amount float64) error {
	if amount <= 0 {
		return errors.New("сумма пополнения должна быть положительной")
	}
	a.balance += amount
	return nil
}""",
                "note": "Инкапсуляция полей в Go"
            }
        ],
        "under_the_hood": """
Функция `unicode.IsUpper(r)` в компиляторе сверяет категорию символа в таблицах стандарта Unicode. Это означает, что даже функции на русском языке с заглавной буквы (например, `func Вычислить()`) формально считаются экспортируемыми компилятором Go!
""",
        "pitfalls": """
- Попытка сериализации структуры в JSON через `json.Marshal(acc)`: неэкспортированные поля (как `balance`) **будут проигнорированы сериализатором**, так как рефлексия `reflect` вне пакета не имеет доступа к неэкспортируемым полям!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `json.Unmarshal` не заполняет поля структуры, если они начинаются со строчной буквы?»
**Ответ:** Пакет `encoding/json` — это внешний по отношению к вашему коду пакет. Он инспектирует поля структуры через рефлексию `reflect`. Поскольку неэкспортированные поля недоступны внешним пакетам, рефлексия не имеет права записывать в них данные. Поля под JSON обязаны быть экспортируемыми (`Name string `json:\"name\"``).
"""
    },
    {
        "num": 79,
        "title": "Документирование кода по стандарту GoDoc и локальный pkgsite",
        "task": "Напишите комментарии для пакета и экспортируемой функции в формате godoc, запустите локальный godoc.",
        "theory": """
В Go нет тяжелых XML/Javadoc тегов (`@param`, `@return`, `@throws`).
Документация GoDoc формируется из **обычных понятных комментариев**, оформленных по стандарту:
1. **Комментарий к пакету:** начинается со слова `// Package <имя_пакета> ...` непосредственно перед объявлением `package`.
2. **Комментарий к функции:** начинается с имени функции `// <ИмяФункции> ...` непосредственно перед объявлением `func`.
3. **Форматирование абзацев:** пустая строка комментария разделяет параграфы.
4. **Примеры кода:** блоки с отступом (4 пробела или таб) автоматически рендерятся как подсвеченный моноширинный код.
""",
        "step_by_step": """
1. Пишем каноническую документацию для пакета `hasher`.
2. Запускаем локальный веб-сервер документации `pkgsite` (современный преемник godoc).
3. Просматриваем красивую HTML-документацию в браузере.
""",
        "code_blocks": [
            {
                "filename": "hasher/hasher.go",
                "lang": "go",
                "code": """// Package hasher предоставляет утилиты для безопасного криптографического
// хэширования паролей и токенов пользователей.
//
// Пример использования:
//
//	h := hasher.Sha256Hex("секретная_строка")
//	fmt.Println("Хэш:", h)
package hasher

import (
	"crypto/sha256"
	"encoding/hex"
)

// Sha256Hex принимает произвольную строку данных и возвращает
// её криптографический SHA-256 хэш в виде шестнадцатеричной строки (HEX).
//
// Функция потокобезопасна и не сохраняет внутреннего состояния.
func Sha256Hex(data string) string {
	sum := sha256.Sum256([]byte(data))
	return hex.EncodeToString(sum[:])
}""",
                "note": "Каноническое документирование GoDoc"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# 1. Просмотр документации в терминале
go doc ./hasher

# 2. Просмотр конкретной функции
go doc ./hasher.Sha256Hex

# 3. Установка и запуск локального веб-сервера pkgsite (порт 8080)
# go install golang.org/x/pkgsite/cmd/pkgsite@latest
# pkgsite -http=:8080""",
                "note": "Команды инспекции документации"
            }
        ],
        "under_the_hood": """
Утилита `go doc` парсит AST-дерево и связывает узлы комментариев `ast.CommentGroup` с соответствующими узлами объявлений `ast.FuncDecl` / `ast.TypeDecl`.
""",
        "pitfalls": """
- Написание комментария вида `// Эта функция считает хэш...` вместо канонического `// Sha256Hex считает хэш...` нарушает форматирование GoDoc и выдает предупреждение в линтерах (`revive`, `golint`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что такое Runnable Examples (исполняемые примеры) в тестах Go?»
**Ответ:** Это специальные функции в файлах `_test.go` с префиксом `func ExampleXxx()`, содержащие блок `// Output: ...`. Они не только автоматически тестируются командой `go test`, но и встраиваются в документацию GoDoc на `pkg.go.dev` как интерактивные запускаемые примеры кода!
"""
    },
    {
        "num": 80,
        "title": "Фиксация точной семантической версии зависимости (go get pkg@v1.2.3)",
        "task": "Добавьте зависимость через go get package@v1.2.3, изучите go.mod и go.sum.",
        "theory": """
При добавлении библиотеки вы можете зафиксировать конкретную версию:
- `go get github.com/google/uuid@v1.4.0` — точная фиксация релиза;
- `go get github.com/google/uuid@master` — фиксация последней ревизии ветки master;
- `go get github.com/google/uuid@70ab18` — фиксация по конкретному хэшу коммита.
""",
        "step_by_step": """
1. Устанавливаем конкретную версию `v1.4.0`.
2. Открываем `go.mod` и проверяем строку `github.com/google/uuid v1.4.0`.
3. Сверяем хэши в `go.sum`.
""",
        "code_blocks": [
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go get github.com/google/uuid@v1.4.0
cat go.mod | grep uuid
# require github.com/google/uuid v1.4.0""",
                "note": "Установка точной версии"
            }
        ],
        "under_the_hood": """
Тулчейн Go запрашивает архив конкретного релиза `v1.4.0.zip` с прокси, проверяет чексумму и обновляет файл `go.mod`.
""",
        "pitfalls": """
- Понижение версии (downgrade) может сломать код, если проект уже использовал функции, появившиеся только в более поздних версиях.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в Go откатить (downgrade) версию зависимости на более старую?»
**Ответ:** Выполнить `go get package@vOLD_VERSION` (например, `go get github.com/google/uuid@v1.3.0`) и затем запустить `go mod tidy`. Go автоматически обновит манифест и контрольные суммы.
"""
    },
    {
        "num": 81,
        "title": "Регулярное обслуживание зависимостей: go get -u && go mod tidy",
        "task": "Обновите все зависимости до последних минорных версий (go get -u), затем выполните go mod tidy.",
        "theory": """
Регулярный регламент обновления зависимостей в команде (Dependency Maintenance Routine):
1. `go get -u ./...` — обновляет все используемые модули до последних минорных версий.
2. `go mod tidy` — удаляет устаревшие косвенные зависимости и нормализует `go.sum`.
3. `go test -race ./...` — выполняет регрессионное тестирование всего сервиса с детектором гонок.
4. `govulncheck ./...` — проверяет обновленные библиотеки на безопасность.
""",
        "step_by_step": """
1. Выполняем `go get -u ./...`.
2. Запускаем `go mod tidy`.
3. Прогоняем тесты `go test ./...`.
""",
        "code_blocks": [
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# Полный пайплайн обновления
go get -u ./...
go mod tidy
go test -v -race ./...
git diff go.mod""",
                "note": "Комплексное обновление проекта"
            }
        ],
        "under_the_hood": """
Команда `go get -u ./...` обходит все пакеты текущего проекта, находит максимальные минорные версии для каждого узла графа и пересчитывает MVS-дерево.
""",
        "pitfalls": """
- Обновление зависимостей напрямую на продакшен-сервере без предварительного тестирования в CI/Staging.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в корпоративной разработке автоматизировать регулярное обновление зависимостей?»
**Ответ:** Использованием ботов Dependabot или Renovate. Бот автоматически создает Pull Request с обновленной версией зависимости, CI запускает весь набор тестов, и при успешном прогоне PR вливается в основную ветку.
"""
    },
    {
        "num": 82,
        "title": "Парсинг опций командной строки через стандартный пакет flag",
        "task": "Создайте простое CLI-приложение с использованием стандартного пакета flag (разбор опций).",
        "theory": """
Стандартный пакет `flag` предоставляет базовые возможности парсинга аргументов командной строки:
- Типобезопасные флаги: `flag.String`, `flag.Int`, `flag.Bool`, `flag.Duration`.
- Значения по умолчанию.
- Автоматическая генерация справки при передаче флагов `-h` или `--help`.
- Вызов `flag.Parse()` — обязателен для разбора аргументов!
""",
        "step_by_step": """
1. Объявляем переменные для флагов через `flag.StringVar`, `flag.IntVar`, `flag.DurationVar`.
2. Вызываем `flag.Parse()`.
3. Проверяем оставшиеся неразобранные позиционные аргументы через `flag.Args()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"flag"
	"fmt"
	"time"
)

func main() {
	// Определение флагов
	host := flag.String("host", "127.0.0.1", "Сетевой хост для привязки сервера")
	port := flag.Int("port", 8080, "Порт HTTP-сервера")
	timeout := flag.Duration("timeout", 30*time.Second, "Таймаут ожидания клиентских запросов")
	enableMetrics := flag.Bool("metrics", true, "Включить эндпоинт метрик Prometheus")

	// ОБЯЗАТЕЛЬНЫЙ ВЫЗОВ: парсинг аргументов os.Args
	flag.Parse()

	fmt.Println("=== ПАРАМЕТРЫ СЕРВЕРА ===")
	fmt.Printf("Адрес:           %s:%d\\n", *host, *port)
	fmt.Printf("Таймаут:         %v\\n", *timeout)
	fmt.Printf("Метрики активны: %t\\n", *enableMetrics)

	// Позиционные аргументы (те, что идут после флагов)
	if tail := flag.Args(); len(tail) > 0 {
		fmt.Printf("Дополнительные позиционные параметры: %v\\n", tail)
	}
}""",
                "note": "Стандартный пакет flag"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# 1. Автоматическая справка
go run . -h
# Usage of /tmp/go-build...:
#   -host string
#     	Сетевой хост для привязки сервера (default "127.0.0.1")
#   -metrics
#     	Включить эндпоинт метрик Prometheus (default true)
#   -port int
#     	Порт HTTP-сервера (default 8080)
#   -timeout duration
#     	Таймаут ожидания клиентских запросов (default 30s)

# 2. Запуск с переопределением параметров
go run . -host=0.0.0.0 -port=9000 -timeout=15s -metrics=false workers start""",
                "note": "Вызов с кастомными флагами"
            }
        ],
        "under_the_hood": """
`flag.Parse()` сканирует срез `os.Args[1:]`, сопоставляет имена флагов с зарегистрированной структурой `flag.FlagSet` и преобразует строки в соответствующие типы данных (`strconv.Atoi`, `time.ParseDuration`).
""",
        "pitfalls": """
- Забыть вызвать `flag.Parse()`: значения указателей останутся равными дефолтным, даже если пользователь передал аргументы в консоли!
- Порядок аргументов: стандартный пакет `flag` прекращает поиск флагов при первом встреченном позиционном аргументе.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как поддержать кастомный тип флага (например, срез строк через запятую `[]string`) в стандартном пакете `flag`?»
**Ответ:** Реализовать стандартный интерфейс `flag.Value`, состоящий из двух методов: `String() string` и `Set(string) error`, и зарегистрировать его через `flag.Var(&myCustomType, "name", "usage")`.
"""
    },
    {
        "num": 83,
        "title": "Продвинутый POSIX-совместимый парсинг флагов с spf13/pflag",
        "task": "Установите сторонний пакет github.com/spf13/pflag (или cobra) и реализуйте тот же CLI с ним.",
        "theory": """
Стандартный пакет `flag` не поддерживает:
- Разделение на короткие (`-p`) и длинные (`--port`) флаги;
- Объединение булевых флагов (`-v -d` -> `-vd`);
- Разбор флагов после позиционных аргументов.

Библиотека **`github.com/spf13/pflag`** является 100% совместимой POSIX/GNU-заменой стандартного `flag`.
""",
        "step_by_step": """
1. Скачиваем `go get github.com/spf13/pflag`.
2. Заменяем импорт `flag` на `pflag`.
3. Используем методы с суффиксом `P` для коротких алиасов: `pflag.IntVarP(&port, "port", "p", 8080, "...")`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"time"
	"github.com/spf13/pflag"
)

func main() {
	var (
		host    string
		port    int
		timeout time.Duration
		verbose bool
	)

	// Короткие (-h, -p, -t, -v) и длинные (--host, --port, ...) флаги
	pflag.StringVarP(&host, "host", "h", "127.0.0.1", "Хост сервера")
	pflag.IntVarP(&port, "port", "p", 8080, "Порт сервера")
	pflag.DurationVarP(&timeout, "timeout", "t", 10*time.Second, "Таймаут соединения")
	pflag.BoolVarP(&verbose, "verbose", "v", false, "Подробный вывод логов")

	pflag.Parse()

	fmt.Printf("Подключение к %s:%d (Таймаут: %v, Verbose: %t)\\n", host, port, timeout, verbose)
}""",
                "note": "Использование pflag"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# Короткие флаги в стиле Linux
go run . -p 9090 -v -t 5s
# Подключение к 127.0.0.1:9090 (Таймаут: 5s, Verbose: true)

# Длинные флаги
go run . --host 10.0.0.1 --port 443 --verbose""",
                "note": "Вызов с флагами POSIX"
            }
        ],
        "under_the_hood": """
`pflag` следует стандарту POSIX Utility Syntax Guidelines: одиночное тире для однобуквенных флагов (`-p`), двойное тире для многобуквенных (`--port`).
""",
        "pitfalls": """
- Коллизия однобуквенных флагов: назначение одной и той же буквы `-h` для двух разных флагов вызовет панику при регистрации.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему весь проект Kubernetes использует `pflag` вместо стандартного `flag`?»
**Ответ:** Из-за требований к стандартизации CLI Unix-систем (`kubectl -n default -o yaml -w`). Стандартный пакет `flag` не поддерживает синтаксис `--flag` и `-f` в общепринятой Unix-манере.
"""
    },
    {
        "num": 84,
        "title": "Модульное тестирование в Go: файлы _test.go и раннер go test",
        "task": "Напишите модульный тест для одной из функций (файл _test.go), запустите go test.",
        "theory": """
Принципы тестирования в Go:
1. **Файлы тестов** всегда имеют суффикс `_test.go` (например, `validator_test.go`) и лежат **в той же папке**, что и тестируемый код.
2. **Имя функции** обязано начинаться с `Test`: `func TestValidateEmail(t *testing.T)`.
3. Аргумент `t *testing.T` управляет жизненным циклом теста:
   - `t.Errorf(...)` — сообщает об ошибке, но продолжает выполнение теста.
   - `t.Fatalf(...)` — сообщает об ошибке и **немедленно прерывает** текущий тест.
   - `t.Run(name, fn)` — запускает изолированный подтест (subtest).
""",
        "step_by_step": """
1. Создаем `stringutil.go` с функцией `IsPalindrome(s string) bool`.
2. Создаем `stringutil_test.go`.
3. Пишем табличные тесты (table-driven tests) с проверкой граничных условий (пустая строка, регистр, Unicode).
4. Запускаем `go test -v -cover .`.
""",
        "code_blocks": [
            {
                "filename": "stringutil.go",
                "lang": "go",
                "code": """package main

import "unicode"

// IsPalindrome проверяет, является ли строка палиндромом, игнорируя регистр и пробелы
func IsPalindrome(s string) bool {
	var letters []rune
	for _, r := range s {
		if unicode.IsLetter(r) || unicode.IsDigit(r) {
			letters = append(letters, unicode.ToLower(r))
		}
	}

	for i, j := 0, len(letters)-1; i < j; i, j = i+1, j-1 {
		if letters[i] != letters[j] {
			return false
		}
	}
	return true
}""",
                "note": "Тестируемая функция"
            },
            {
                "filename": "stringutil_test.go",
                "lang": "go",
                "code": """package main

import "testing"

func TestIsPalindrome(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected bool
	}{
		{name: "Простое слово", input: "шалаш", expected: true},
		{name: "С разным регистром и пробелами", input: "А роза упала на лапу Азора", expected: true},
		{name: "Числовой палиндром", input: "12321", expected: true},
		{name: "Не палиндром", input: "разработка на go", expected: false},
		{name: "Пустая строка", input: "   ", expected: true},
		{name: "Один символ", input: "Я", expected: true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := IsPalindrome(tt.input)
			if result != tt.expected {
				t.Errorf("IsPalindrome(%q) = %t; ожидалось: %t", tt.input, result, tt.expected)
			}
		})
	}
}""",
                "note": "Табличный тест stringutil_test.go"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go test -v -cover .
# === RUN   TestIsPalindrome
# === RUN   TestIsPalindrome/Простое_слово
# === RUN   TestIsPalindrome/С_разным_регистром_и_пробелами
# === RUN   TestIsPalindrome/Числовой_палиндром
# === RUN   TestIsPalindrome/Не_палиндром
# === RUN   TestIsPalindrome/Пустая_строка
# === RUN   TestIsPalindrome/Один_символ
# --- PASS: TestIsPalindrome (0.00s)
#     --- PASS: TestIsPalindrome/Простое_слово (0.00s)
#     --- PASS: TestIsPalindrome/С_разным_регистром_и_пробелами (0.00s)
#     --- PASS: TestIsPalindrome/Числовой_палиндром (0.00s)
#     --- PASS: TestIsPalindrome/Не_палиндром (0.00s)
#     --- PASS: TestIsPalindrome/Пустая_строка (0.00s)
#     --- PASS: TestIsPalindrome/Один_символ (0.00s)
# PASS
# coverage: 100.0% of statements
# ok      hello_mod       0.002s""",
                "note": "Результат тестирования с 100% покрытием"
            }
        ],
        "under_the_hood": """
Флаг `-cover` заставляет компилятор Go выполнять **инструментирование кода (Code Instrumentation)**: в каждую ветку базовых блоков AST вставляются счетчики вызовов. По завершении тестов рантайм вычисляет процент выполненных инструкций.
""",
        "pitfalls": """
- Использование `t.Fail()` вместо `t.Errorf()`: `t.Fail()` помечает тест упавшим, но не выводит причину и значения ошибки, что делает отладку невозможной.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем разница между запуском тестов `t.Parallel()` и последовательными тестами?»
**Ответ:** Вызов `t.Parallel()` внутри функции теста сигнализирует тестовому раннеру, что данный тест безопасен для конкурентного выполнения. Раннер запускает параллельные тесты одновременно в нескольких горутинах, используя доступные ядра процессора (`GOMAXPROCS`), что многократно ускоряет прогон тестов на CI.
"""
    },
    {
        "num": 85,
        "title": "Синтез: форматированный цветной вывод и структурированный логер",
        "task": "Используйте добавленный пакет для вывода цветного текста в консоль или для логирования событий.",
        "theory": """
В реальных сервисах форматирование адаптируется под окружение (Environment Adaptive Output):
- Если сервис запущен локально в терминале разработчика: красивый цветной вывод (ANSI Colors);
- Если сервис запущен в контейнере Kubernetes/Docker: чистый структурированный JSON без цветовых кодов.
""",
        "step_by_step": """
1. Создаем фабрику логгера, проверяющую переменную `ENV=production`.
2. В режиме `production` выставляем `JSONFormatter`.
3. В режиме `development` выставляем цветной `TextFormatter`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"os"
	"github.com/sirupsen/logrus"
)

func InitLogger() *logrus.Logger {
	log := logrus.New()

	env := os.Getenv("APP_ENV")
	if env == "production" {
		log.SetFormatter(&logrus.JSONFormatter{})
		log.SetLevel(logrus.InfoLevel)
	} else {
		// Локальный режим разработчика: цветной вывод
		log.SetFormatter(&logrus.TextFormatter{
			FullTimestamp: true,
			ForceColors:   true,
		})
		log.SetLevel(logrus.DebugLevel)
	}
	return log
}

func main() {
	logger := InitLogger()

	logger.WithField("port", 8080).Info("HTTP Сервер успешно запущен")
	logger.WithField("db", "postgres").Debug("Пул соединений прогрет")
	logger.WithField("user_id", 42).Warn("Попытка доступа без двухфакторной аутентификации")
}""",
                "note": "Адаптивный логгер"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# Локальный запуск
go run .

# Запуск в режиме продакшена
APP_ENV=production go run .
# {"level":"info","msg":"HTTP Сервер успешно запущен","port":8080,"time":"2026-09-02T12:30:00Z"}""",
                "note": "Переключение форматов логирования"
            }
        ],
        "under_the_hood": """
`logrus.TextFormatter` проверяет поддержку цветов через вызовы дескриптора терминала `os.Stdout.Fd()`, гарантируя корректное отображение в Unix-терминалах.
""",
        "pitfalls": """
- Отправка цветных ANSI-кодов в системы сбора логов (Kibana/Loki) — логи становятся нечитаемыми из-за экранированных символов вроде `\u001b[31m`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в высоконагруженных бэкендах избегают динамических строковых конкатенаций в логах вида `log.Info(\"User \" + id + \" paid \" + amount)`?»
**Ответ:** Конкатенация строк создает лишние аллокации в памяти на каждый запрос. Структурированное логирование с полями (`log.WithFields`) либо компиляция константных строк снижает нагрузку на Garbage Collector до нуля.
"""
    },
    {
        "num": 86,
        "title": "Бенчмаркинг производительности: testing.B и go test -bench=.",
        "task": "Напишите бенчмарк для функции, запустите go test -bench=..",
        "theory": """
Go — единственный мейнстрим-язык с **встроенным инструментом бенчмаркинга нулевого уровня**.

Правила бенчмарков в Go:
1. Функция находится в `_test.go` и имеет префикс `Benchmark`: `func BenchmarkXxx(b *testing.B)`.
2. Внутри функции обязателен цикл `for i := 0; i < b.N; i++`.
3. Число `b.N` динамически подбирается раннером Go так, чтобы тест выполнялся около 1 секунды для статистической достоверности.
4. Вызов `b.ReportAllocs()` автоматически измеряет количество аллокаций памяти (`allocs/op`) и выделенных байт (`B/op`).
""",
        "step_by_step": """
1. Создаем две реализации конкатенации строк: наивный оператор `+=` и быстрый `strings.Builder`.
2. Пишем два бенчмарка: `BenchmarkConcatPlus` и `BenchmarkConcatBuilder`.
3. Запускаем сравнение производительности: `go test -bench=. -benchmem .`.
""",
        "code_blocks": [
            {
                "filename": "concat.go",
                "lang": "go",
                "code": """package main

import "strings"

// ConcatPlus — наивное сложение строк через оператор +=
func ConcatPlus(parts []string) string {
	res := ""
	for _, p := range parts {
		res += p
	}
	return res
}

// ConcatBuilder — высокопроизводительное объединение через strings.Builder
func ConcatBuilder(parts []string) string {
	var sb strings.Builder
	for _, p := range parts {
		sb.WriteString(p)
	}
	return sb.String()
}""",
                "note": "Сравнение двух алгоритмов"
            },
            {
                "filename": "concat_test.go",
                "lang": "go",
                "code": """package main

import "testing"

var sampleData = []string{
	"Go", "высокопроизводительный", "язык", "для", "бэкенда", 
	"микросервисов", "и", "высоких", "нагрузок", "в", "BigTech",
}

func BenchmarkConcatPlus(b *testing.B) {
	b.ReportAllocs() // Включаем подсчет аллокаций памяти
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = ConcatPlus(sampleData)
	}
}

func BenchmarkConcatBuilder(b *testing.B) {
	b.ReportAllocs()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = ConcatBuilder(sampleData)
	}
}""",
                "note": "Бенчмарки concat_test.go"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go test -bench=. -benchmem .
# BenchmarkConcatPlus-8        2451070        482.3 ns/op     240 B/op     10 allocs/op
# BenchmarkConcatBuilder-8    14205194         82.1 ns/op      96 B/op      3 allocs/op
# PASS
# ok      hello_mod       2.912s""",
                "note": "Результаты бенчмаркинга: Builder в 6 раз быстрее!"
            }
        ],
        "under_the_hood": """
Каждое `+=` со строкой в цикле выделяет новый блок памяти в куче и копирует старые байты ($O(N^2)$ по памяти). `strings.Builder` использует внутренний растущий срез байт `[]byte` с амортизированной сложностью $O(N)$ и преобразует его в `string` без копирования через `unsafe.Pointer`.
""",
        "pitfalls": """
- Компилятор может вырезать вызов функции внутри бенчмарка через Dead Code Elimination, если результат никуда не сохраняется. Принято присваивать результат глобальной переменной пакета.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в BigTech статистически строго сравнивать результаты бенчмарков двух веток Git?»
**Ответ:** Запустить бенчмарк 10 раз (`go test -bench=. -count=10 > old.txt`), переключить ветку (`git checkout feature`), снова запустить 10 раз (`> new.txt`) и сравнить официальной утилитой **`benchstat old.txt new.txt`**. Она рассчитывает p-value и доверительный интервал различий.
"""
    },
    {
        "num": 87,
        "title": "Криптографическая безопасность цепочки поставок: глубокий разбор go.sum",
        "task": "Изучите файл go.sum, поймите его назначение и почему его обязательно нужно коммитить в систему контроля версий.",
        "theory": """
**Supply Chain Security (Безопасность цепочки поставок):**
Один из самых опасных векторов атак в современном мире — подмена кода популярной зависимости на этапе сборки.

Файл `go.sum` решает эту проблему на корню:
1. Он фиксирует SHA-256 хэши **каждого файла исходного кода** каждой версии зависимости.
2. При каждой сборке Go вычисляет хэш скачанных файлов и сверяет его с `go.sum`.
3. Если хотя бы один байт в библиотеке был изменен (например, хакер взломал репозиторий автора на GitHub и внедрил бэкдор), компилятор Go **немедленно аварийно остановит сборку**:
   `SECURITY ERROR: checksum mismatch`.

**Почему `go.sum` ОБЯЗАН быть закоммичен в Git:**
Если не коммитить `go.sum`, сборка на сервере CI/CD заново сгенерирует хэши на основе того, что скачает из сети, полностью обесценив защиту от атак подмены!
""",
        "step_by_step": """
1. Открываем `go.sum` и анализируем записи.
2. Изучаем структуру строк `h1:` и хэшей `go.mod`.
""",
        "code_blocks": [
            {
                "filename": "go.sum (Пример реальных контрольных сумм)",
                "lang": "text",
                "code": """github.com/google/uuid v1.6.0 h1:NIvaJDMOLLgnQqtS9L13SiLgXA2zgWUpEvJ8kx4Pzp8=
github.com/google/uuid v1.6.0/go.mod h1:TIyPZe4MgqvFqtWhCDKEIlvZxxxvm618TFiP1UGKOEg=
github.com/sirupsen/logrus v1.9.3 h1:dueUQMBYksGn6+/YVwcJpqvZsJ1UxF2mOwk2eaja5xU=
github.com/sirupsen/logrus v1.9.3/go.mod h1:naHLInspectionX0sH19dD52vL52...""",
                "note": "Криптографический реестр целостности go.sum"
            }
        ],
        "under_the_hood": """
Go использует публичный прозрачный лог `sum.golang.org`, построенный на структуре данных Merkle Tree (дерево Меркла, аналогично Certificate Transparency). Любое изменение когда-либо опубликованной версии модуля немедленно обнаруживается всем сообществом мира.
""",
        "pitfalls": """
- Добавление `go.sum` в `.gitignore` — опаснейшая ошибка начинающих.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему для каждого модуля в `go.sum` часто присутствуют ДВЕ строки (одна с `/go.mod`, другая без)?»
**Ответ:** Строка с суффиксом `/go.mod` содержит хэш *только файла `go.mod`* этой зависимости. Это позволяет Go вычислять и разрешать граф зависимостей (MVS) быстро, скачивая только легковесные манифесты `go.mod` без необходимости выкачивать гигабайты исходных кодов всех транзитивных библиотек.
"""
    },
    {
        "num": 88,
        "title": "Внедрение метаданных сборки (Git SHA, версия, время) через -ldflags",
        "task": "Соберите программу, внедрив версию и время сборки через -ldflags \"-X main.version=...\".",
        "theory": """
В продакшене бинарник микросервиса должен четко знать:
- Свою точную версию (SemVer);
- Хэш коммита Git SHA, из которого он был собран;
- Точное время сборки и окружение сборщика.

В Go для этого **не нужно создавать файлы конфигурации**!
Флаг линкера **`-X importpath.name=value`** позволяет переопределить значение строковой переменной в коде **на этапе линковки бинарника**!
""",
        "step_by_step": """
1. В `main.go` объявляем строковые переменные `version`, `commit`, `buildTime` со значениями по умолчанию `"dev"`.
2. Компилируем бинарник с флагом `-ldflags`.
3. Запускаем скомпилированный бинарник с флагом `--version`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"flag"
	"fmt"
	"os"
)

// Эти переменные переопределяются линкером при сборке через -ldflags
var (
	version   = "dev-local"
	commit    = "none"
	buildTime = "unknown"
)

func main() {
	showVersion := flag.Bool("version", false, "Показать версию сборки и метаданные")
	flag.Parse()

	if *showVersion {
		fmt.Println("=== СВЕДЕНИЯ О СБОРКЕ СЕРВИСА ===")
		fmt.Printf("Версия релиза:  %s\\n", version)
		fmt.Printf("Git Commit SHA:  %s\\n", commit)
		fmt.Printf("Дата и время:    %s\\n", buildTime)
		os.Exit(0)
	}

	fmt.Printf("Сервис запущен (версия: %s)...\\n", version)
}""",
                "note": "Переменные сборки"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# Сборка с инъекцией метаданных
CURRENT_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "a1b2c3d")

go build -ldflags " \\
  -X main.version=v1.4.2 \\
  -X main.commit=${GIT_COMMIT} \\
  -X main.buildTime=${CURRENT_TIME} \\
  -s -w" -o bin/server .

# Запуск и проверка метаданных
./bin/server --version
# === СВЕДЕНИЯ О СБОРКЕ СЕРВИСА ===
# Версия релиза:  v1.4.2
# Git Commit SHA:  a1b2c3d
# Дата и время:    2026-09-02T12:40:00Z""",
                "note": "Сборка с флагами линкера"
            }
        ],
        "under_the_hood": """
Линкер `go tool link` находит адреса символов `main.version` в сегменте данных `.data` и перезаписывает байты строкового заголовка (`reflect.StringHeader`) на новые строковые константы.
""",
        "pitfalls": """
- Переменные под инъекцию `-X` **обязаны иметь тип `string`** и объявляться через `var`, а не `const`! К константам или числам `int` линкер применить `-X` не сможет.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что появилось в Go 1.18 для автоматического получения информации о сборке без ручных `-ldflags`?»
**Ответ:** Пакет `runtime/debug` и функция `debug.ReadBuildInfo()`. Go автоматически вшивает в бинарник VCS-метаданные (ревизию Git, статус `vcs.modified=true/false`, версию компилятора и флаги сборки), которые можно прочитать прямо из кода в runtime.
"""
    },
    {
        "num": 89,
        "title": "Вендоринг зависимостей: go mod vendor для изолированных закрытых контуров",
        "task": "Воспользуйтесь go mod vendor и соберите проект с вендорингом зависимостей.",
        "theory": """
**Что такое вендоринг (Vendoring)?**
Команда `go mod vendor` копирует исходные коды всех внешних зависимостей проекта в локальную поддиректорию `vendor/` в корне репозитория.

Зачем это нужно в BigTech:
1. **Изолированные закрытые контуры (Air-Gapped Environments):** сборочные сервера оборонных предприятий, банков или закрытых ЦОД не имеют доступа в интернет.
2. **100% независимость от внешних серверов:** сборка гарантированно соберется даже в случае глобального сбоя GitHub или уничтожения аккаунта автора библиотеки.
3. **Быстрая сборка:** `go build -mod=vendor` собирает бинарник моментально без сетевых запросов.
""",
        "step_by_step": """
1. Выполняем команду `go mod vendor`.
2. Изучаем появившуюся папку `vendor/` и файл `vendor/modules.txt`.
3. Собираем проект с флагом вендоринга: `go build -mod=vendor .`.
""",
        "code_blocks": [
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# Копирование всех исходников зависимостей в папку vendor/
go mod vendor

# Просмотр структуры каталога vendor/
ls -l vendor/
# drwxr-xr-x github.com
# drwxr-xr-x golang.org
# -rw-r--r-- modules.txt

# Полностью автономная оффлайн сборка
go build -mod=vendor -o bin/server .""",
                "note": "Вендоринг зависимостей"
            }
        ],
        "under_the_hood": """
Файл `vendor/modules.txt` содержит манифест всех скопированных пакетов с указанием их точных версий и лицензий. При флаге `-mod=vendor` компилятор полностью отключает чтение `$GOPATH/pkg/mod` и берет файлы исключительно из локального каталога `vendor/`.
""",
        "pitfalls": """
- Папка `vendor/` может занимать десятки мегабайт в Git-репозитории. В большинстве открытых проектов её не коммитят, используя обычный кэш модулей, но в enterprise-контурах с жесткими политиками безопасности вендоринг обязателен.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как компилятор Go выбирает между `vendor` и глобальным кэшем модулей?»
**Ответ:** Если папка `vendor/` существует и версия Go в `go.mod` равна 1.14+, `go build` автоматически использует каталог `vendor/`. Принудительно управлять поведением можно флагами `-mod=readonly` (строго по `go.mod`) или `-mod=vendor`.
"""
    },
    {
        "num": 90,
        "title": "Создание автономного локального модуля и связывание через replace",
        "task": "Создайте собственный локальный модуль (отдельная папка с go.mod) и подключите его в ваш основной проект с помощью директивы replace в go.mod.",
        "theory": """
Закрепляем архитектуру связывания независимых сервисов и модулей:
- Модуль ядра `auth-core`;
- Модуль шлюза `api-gateway`;
- Полная изоляция манифестов `go.mod`.
""",
        "step_by_step": """
1. Создаем директорию `core_lib/` с `go mod init gitlab.company.ru/libs/core`.
2. Создаем пакет `security` с функцией `HashPassword(pass string) string`.
3. В основном приложении настраиваем `replace gitlab.company.ru/libs/core => ../core_lib`.
4. Запускаем проект.
""",
        "code_blocks": [
            {
                "filename": "core_lib/go.mod",
                "lang": "text",
                "code": """module gitlab.company.ru/libs/core

go 1.22.5""",
                "note": "Манифест модуля core_lib"
            },
            {
                "filename": "core_lib/security/hash.go",
                "lang": "go",
                "code": """package security

import (
	"crypto/sha256"
	"fmt"
)

func HashPassword(rawPassword string) string {
	sum := sha256.Sum256([]byte(rawPassword))
	return fmt.Sprintf("sha256$%x", sum)
}""",
                "note": "Библиотечный пакет security"
            },
            {
                "filename": "mainapp/go.mod",
                "lang": "text",
                "code": """module gitlab.company.ru/apps/mainapp

go 1.22.5

require gitlab.company.ru/libs/core v0.0.0

replace gitlab.company.ru/libs/core => ../core_lib""",
                "note": "Манифест основного приложения"
            },
            {
                "filename": "mainapp/main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"gitlab.company.ru/libs/core/security"
)

func main() {
	hashed := security.HashPassword("SuperSecret2026!")
	fmt.Printf("Хэш пароля: %s\\n", hashed)
}""",
                "note": "Использование локального модуля"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """cd mainapp
go run .
# Вывод:
# Хэш пароля: sha256$2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824""",
                "note": "Успешный запуск"
            }
        ],
        "under_the_hood": """
Подмена `replace` транслирует файловые дескрипторы компилятора на соседнее дерево директорий, полностью минуя сетевой тулчейн.
""",
        "pitfalls": """
- Забыть создать `go.mod` внутри подключаемой папки: целевой каталог `replace` обязан быть валидным модулем Go с файлом `go.mod` в корне.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как протестировать Pull Request в библиотеке против 20 зависимых микросервисов в CI?»
**Ответ:** Сборочный пайплайн клонирует ветку PR библиотеки в соседнюю директорию и динамически инжектирует строку `replace` во все `go.mod` микросервисов перед запуском их интеграционных тестов.
"""
    },
    {
        "num": 91,
        "title": "Эталонная архитектура микросервиса: Standard Go Project Layout (cmd, internal, pkg)",
        "task": "Постройте проект с многоуровневой структурой пакетов (cmd/server, pkg/database, internal/config), обеспечив корректные пути импорта.",
        "theory": """
**Standard Go Project Layout (Каноническая архитектура проектов на Go):**
В мировом и российском BigTech (Ozon, Yandex, Avito, Tinkoff, WB) де-факто стандартом является следующая структура:

```text
├── cmd/                          # Точки входа (исполняемые бинарники проекта)
│   ├── server/                   # Основной HTTP/gRPC сервис
│   │   └── main.go
│   └── migrator/                 # CLI-утилита применения миграций БД
│       └── main.go
├── internal/                     # Приватная бизнес-логика (защищена компилятором!)
│   ├── app/                      # Сборка контейнера зависимостей (DI)
│   │   └── app.go
│   ├── config/                   # Конфигурация сервиса
│   │   └── config.go
│   ├── domain/                   # Чистые сущности и интерфейсы бизнес-логики
│   │   └── user.go
│   ├── service/                  # Юзкейсы (Use Cases)
│   │   └── user_service.go
│   └── repository/               # Реализации работы с БД (Postgres, Redis)
│       └── user_repo.go
├── pkg/                          # Публичные пакеты (разрешены для импорта внешними сервисами)
│   ├── database/                 # Общий клиент подключения к PostgreSQL
│   │   └── postgres.go
│   └── logger/                   # Обертка над логгером
│       └── logger.go
├── api/                          # Protobuf, OpenAPI/Swagger спецификации
│   └── proto/
│       └── user.proto
├── configs/                      # Конфигурационные файлы (yaml, env)
│   └── config.yaml
├── Makefile                      # Автоматизация сборки
├── Dockerfile                    # Многоэтапный Docker-образ
├── go.mod
└── go.sum
```
""",
        "step_by_step": """
1. Создаем структуру каталогов: `cmd/server/`, `internal/config/`, `pkg/database/`.
2. В `pkg/database/postgres.go` реализуем публичный пул соединений.
3. В `internal/config/config.go` реализуем загрузку настроек сервиса.
4. В `cmd/server/main.go` объединяем компоненты в чистую точку входа.
5. Запускаем команду `go run ./cmd/server`.
""",
        "code_blocks": [
            {
                "filename": "pkg/database/postgres.go",
                "lang": "go",
                "code": """// Package database предоставляет публичный клиент для подключения к PostgreSQL
package database

import (
	"fmt"
	"time"
)

type DB struct {
	DSN string
}

func Connect(dsn string) (*DB, error) {
	fmt.Printf("[PKG/DATABASE] Подключение к пулу PostgreSQL по адресу %s...\\n", dsn)
	time.Sleep(100 * time.Millisecond) // Симуляция сетевого рукопожатия
	fmt.Println("[PKG/DATABASE] Пул соединений PostgreSQL успешно инициализирован.")
	return &DB{DSN: dsn}, nil
}

func (db *DB) Close() {
	fmt.Println("[PKG/DATABASE] Пул соединений PostgreSQL закрыт.")
}""",
                "note": "Публичный пакет pkg/database"
            },
            {
                "filename": "internal/config/config.go",
                "lang": "go",
                "code": """// Package config содержит приватную конфигурацию сервиса
package config

import (
	"os"
)

type Config struct {
	Port  string
	DBDSN string
}

func MustLoad() *Config {
	port := os.Getenv("HTTP_PORT")
	if port == "" {
		port = "8080"
	}

	dsn := os.Getenv("DATABASE_DSN")
	if dsn == "" {
		dsn = "postgres://postgres:secret@localhost:5432/app_db?sslmode=disable"
	}

	return &Config{
		Port:  port,
		DBDSN: dsn,
	}
}""",
                "note": "Приватный пакет internal/config"
            },
            {
                "filename": "cmd/server/main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"hello_mod/internal/config"
	"hello_mod/pkg/database"
)

func main() {
	fmt.Println("==================================================")
	fmt.Println("   ЗАПУСК ENTERPRISE БЭКЕНД-СЕРВИСА НА GO        ")
	fmt.Println("==================================================")

	// 1. Загрузка конфигурации
	cfg := config.MustLoad()
	fmt.Printf("[MAIN] Конфигурация готова. Порт: %s\\n", cfg.Port)

	// 2. Инициализация инфраструктурных клиентов
	db, err := database.Connect(cfg.DBDSN)
	if err != nil {
		panic(err)
	}
	defer db.Close()

	// 3. Запуск сервиса
	fmt.Printf("[MAIN] HTTP-сервер слушает на :%s\\n", cfg.Port)
	fmt.Println("[MAIN] Сервис готов к обработке трафика.")
}""",
                "note": "Чистая точка входа cmd/server/main.go"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run ./cmd/server
# Вывод:
# ==================================================
#    ЗАПУСК ENTERPRISE БЭКЕНД-СЕРВИСА НА GO        
# ==================================================
# [MAIN] Конфигурация готова. Порт: 8080
# [PKG/DATABASE] Подключение к пулу PostgreSQL по адресу postgres://postgres:secret@localhost:5432/app_db?sslmode=disable...
# [PKG/DATABASE] Пул соединений PostgreSQL успешно инициализирован.
# [MAIN] HTTP-сервер слушает на :8080
# [MAIN] Сервис готов к обработке трафика.
# [PKG/DATABASE] Пул соединений PostgreSQL закрыт.""",
                "note": "Идеальная архитектурная сборка микросервиса"
            }
        ],
        "under_the_hood": """
В канонической структуре папка `cmd/` содержит только тонкие точки входа (`main.go`), которые считывают конфигурацию и вызывают конструктор сборщика приложения `app.New(...)`. Вся бизнес-логика инкапсулирована в `internal/`, гарантируя чистоту архитектурных слоев (Clean Architecture / Hexagonal Architecture).
""",
        "pitfalls": """
- Размещение всей логики (роуты, SQL-запросы, парсинг JSON, бизнес-правила) прямо внутри файла `main.go`. Это превращает проект в нетестируемый «спагетти-код».
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в Clean Architecture на Go изолировать слой бизнес-логики (Domain/Usecases) от конкретной базы данных (Postgres/Mongo)?»
**Ответ:** С помощью интерфейсов (Dependency Inversion Principle). Слой бизнес-логики объявляет интерфейс репозитория `type UserRepository interface { GetUser(ctx, id) (*User, error) }`. Слой `repository/postgres` реализует этот интерфейс. Сервис принимает интерфейс через конструктор `NewUserService(repo UserRepository)`, ничего не зная о деталях SQL.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Section 6: {len(exercises)} exercises.")
