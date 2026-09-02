# Section 5: Exercises 61 to 75

exercises = [
    {
        "num": 61,
        "title": "Удаление пакета и верификация чистоты go.mod",
        "task": "Выполни команду go mod tidy после удаления импорта color из кода. Проверь, что зависимость исчезла из go.mod.",
        "theory": """
В других языках удаление библиотеки часто оставляет «мертвые» записи в файле зависимостей, раздувая манифесты (`package.json`, `requirements.txt`).
В Go команда `go mod tidy` выполняет строгую сборку мусора на уровне зависимостей, приводя `go.mod` в 100% соответствие реальному коду.
""",
        "step_by_step": """
1. Удаляем все вызовы и импорты библиотеки `color` из кода.
2. Запускаем `go mod tidy`.
3. Проверяем `git status` и `git diff go.mod` — модуль `github.com/fatih/color` полностью удален из `go.mod` и `go.sum`.
""",
        "code_blocks": [
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go mod tidy
git diff go.mod
# -require github.com/fatih/color v1.17.0
# -require github.com/mattn/go-colorable v0.1.13 // indirect""",
                "note": "Удаление неиспользуемых зависимостей"
            }
        ],
        "under_the_hood": """
`go mod tidy` строит срез всех файлов пакета, парсит блок `import` в каждом файле, строит множество используемых путей и удаляет из графа требований модули, не входящие в это множество.
""",
        "pitfalls": """
- Если зависимость используется хотя бы в одном не закоммиченном файле или тестовом файле `_test.go`, `go mod tidy` сохранит её в `go.mod`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Зачем запускать `go mod tidy` с флагом `-diff` в Go 1.21+?»
**Ответ:** Флаг `go mod tidy -diff` не изменяет файлы на диске, а выводит diff изменений и завершается с кодом ошибки, если требуются правки. Это идеально для быстрых проверок в CI-пайплайнах.
"""
    },
    {
        "num": 62,
        "title": "Полный справочник директив go.mod: module, go, require, replace, exclude",
        "task": "Изучи go.mod после добавления зависимостей. Объясни назначение каждой секции: module, go, require, replace, exclude. Попробуй использовать exclude для блокировки конкретной версии пакета.",
        "theory": """
В файле `go.mod` поддерживаются **ровно 5 ключевых директив**:

1. **`module <path>`:** Декларирует уникальное имя текущего модуля и базовый путь импорта.
2. **`go <version>`:** Указывает минимальную версию языка Go и тулчейна (например, `go 1.22`).
3. **`require <path> <version>`:** Фиксирует зависимости проекта и их минимально допустимые версии.
4. **`replace <old_path> [old_version] => <new_path> [new_version]`:** Перенаправляет путь импорта на локальную папку или форк репозитория.
5. **`exclude <path> <version>`:** Запрещает компилятору использовать конкретную сломанную или уязвимую версию зависимости (например, если в версии `v1.2.3` нашли критический баг).
""",
        "step_by_step": """
1. Открываем `go.mod`.
2. Добавляем директиву `exclude github.com/google/uuid v1.5.0`.
3. Запускаем `go build .` — компилятор проигнорирует версию v1.5.0 и выберет следующую подходящую версию (v1.6.0).
""",
        "code_blocks": [
            {
                "filename": "go.mod (Комплексный пример)",
                "lang": "text",
                "code": """module gitlab.company.ru/backend/payment-gate

go 1.22.5

// Прямые зависимости
require (
	github.com/google/uuid v1.6.0
	github.com/sirupsen/logrus v1.9.3
)

// Запрет использования сломанной версии
exclude github.com/google/uuid v1.5.0

// Подмена на локальный форк библиотеки
replace github.com/sirupsen/logrus => ../custom-logrus""",
                "note": "Все директивы манифеста go.mod"
            }
        ],
        "under_the_hood": """
При вычислении графа зависимостей (MVS) алгоритм компилятора отфильтровывает все версии из списка `exclude` и строит минимальный путь без их участия.
""",
        "pitfalls": """
- Директивы `replace` и `exclude` действуют **только в корневом модуле**. Если вы публикуете библиотеку, пользователи вашей библиотеки не унаследуют ваши `replace` и `exclude`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В каких случаях в BigTech используют директиву `exclude`?»
**Ответ:** Когда в популярной библиотеке обнаруживается критическая уязвимость 0-day (CVE) или критическая утечка памяти (memory leak) в конкретном релизе, в корневом `go.mod` монорепозитория прописывают `exclude`, предотвращая случайное использование этой версии кем-либо из сотен разработчиков компании.
"""
    },
    {
        "num": 63,
        "title": "Устройство кэша модулей: $GOPATH/pkg/mod",
        "task": "Просмотри все скачанные зависимости в кэше с помощью go env GOPATH и перехода в папку pkg/mod.",
        "theory": """
Все внешние библиотеки, скачанные тулчейном Go, сохраняются в единое глобальное хранилище на диске:
`$GOPATH/pkg/mod` (или `$(go env GOMODCACHE)`).

Особенности кэша модулей Go:
1. **Дедупликация:** если 20 разных проектов на вашем компьютере используют `github.com/gin-gonic/gin v1.9.1`, библиотека скачивается на диск **ровно один раз**.
2. **Read-Only права (Только для чтения):** все файлы внутри `$GOPATH/pkg/mod` помечаются правами `chmod 0444` (read-only). Ни вы, ни сторонняя программа не можете случайно изменить код зависимости в кэше.
""",
        "step_by_step": """
1. Узнаем путь к кэшу через `go env GOMODCACHE`.
2. Просматриваем скачанные библиотеки через `ls -la $(go env GOMODCACHE)/cache/download`.
3. При необходимости очистки кэша используем команду `go clean -modcache`.
""",
        "code_blocks": [
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# Путь к кэшу модулей
go env GOMODCACHE
# /home/ut/go/pkg/mod

# Просмотр скачанных исходников
ls -l $(go env GOMODCACHE)/github.com/google/

# Очистка кэша модулей (если нужно освободить диск)
# go clean -modcache""",
                "note": "Инспекция кэша зависимостей"
            }
        ],
        "under_the_hood": """
Каталог `$GOPATH/pkg/mod/cache/download` хранит оригинальные `.zip` архивы и `.mod` файлы с серверов прокси. При сборке Go распаковывает нужную версию в соответствующий подкаталог и проверяет хэш через `go.sum`.
""",
        "pitfalls": """
- Попытка отредактировать файл внутри `$GOPATH/pkg/mod` напрямую завершится ошибкой файловой системы `Permission denied` (Read-only file system). Для модификации внешних библиотек используйте директиву `replace`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в Dockerfile эффективно кэшировать зависимости Go, чтобы `docker build` не скачивал их заново при каждом изменении кода?»
**Ответ:** Разделением слоев в Dockerfile:
```dockerfile
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o server .
```
Слой `RUN go mod download` закэшируется Docker-демоном и будет пересобираться только при реальном изменении `go.mod` или `go.sum`.
"""
    },
    {
        "num": 64,
        "title": "Анализ графа зависимостей: go mod graph и go mod why",
        "task": "Выполни go mod graph и проанализируй граф зависимостей. Найди транзитивные зависимости. Выполни go mod why для одной из зависимостей.",
        "theory": """
В крупных сервисах проект может косвенно зависеть от сотен пакетов.
Для аудита дерева зависимостей тулчейн Go предоставляет мощные утилиты:

1. **`go mod graph`** — выводит полный список ребер направленного графа зависимостей в формате `<модуль-источник> <модуль-зависимость>`.
2. **`go mod why <package>`** — объясняет кратчайшую цепочку импортов от вашего пакета `main` до указанного пакета (отвечает на вопрос «Зачем эта библиотека вообще есть в моем проекте?»).
""",
        "step_by_step": """
1. Запускаем `go mod graph` и изучаем вывод.
2. Запускаем `go mod why golang.org/x/sys` — изучаем цепочку вызовов.
""",
        "code_blocks": [
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# 1. Просмотр графа
go mod graph | head -n 10
# hello_mod github.com/sirupsen/logrus@v1.9.3
# github.com/sirupsen/logrus@v1.9.3 golang.org/x/sys@v0.0.0-20220715151400-c0bba94af5f8

# 2. Выяснение причины присутствия пакета
go mod why golang.org/x/sys
# # golang.org/x/sys
# hello_mod
# github.com/sirupsen/logrus
# golang.org/x/sys/unix""",
                "note": "Анализ зависимостей через graph и why"
            }
        ],
        "under_the_hood": """
`go mod why` выполняет поиск в ширину (BFS) по графу импортов пакетов, находя минимальный путь от корневого пакета `main` до целевого пакета.
""",
        "pitfalls": """
- Если `go mod why -m <module>` выводит `(main module does not need package ...)`, значит этот модуль не участвует в сборке бинарника и может быть удален через `go mod tidy`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как визуализировать граф зависимостей Go в виде интерактивной схемы или SVG-картинки?»
**Ответ:** Скомбинировать `go mod graph` с утилитой Graphviz:
`go mod graph | modgraphviz | dot -Tpng -o graph.png`
"""
    },
    {
        "num": 65,
        "title": "Локальный модуль myutils и оркестрация через replace",
        "task": "Создай локальный модуль myutils. В основном модуле mainapp добавь зависимость через replace в go.mod, указав путь к myutils на файловой системе.",
        "theory": """
Сценарий: корпоративный монорепозиторий или локальная разработка независимых библиотек.
Структура проекта:
```text
workspace/
├── mainapp/
│   ├── go.mod
│   └── main.go
└── myutils/
    ├── go.mod
    └── validator/
        └── email.go
```
""",
        "step_by_step": """
1. Создаем папку `myutils/`, инициализируем `go mod init company.com/myutils`.
2. В `myutils/validator/email.go` пишем функцию проверки email: `Validate(email string) bool`.
3. Создаем папку `mainapp/`, инициализируем `go mod init company.com/mainapp`.
4. В `mainapp/go.mod` прописываем `replace company.com/myutils => ../myutils`.
5. В `mainapp/main.go` вызываем `validator.Validate("dev@yandex.ru")`.
""",
        "code_blocks": [
            {
                "filename": "myutils/validator/email.go",
                "lang": "go",
                "code": """package validator

import "strings"

func Validate(email string) bool {
	return strings.Contains(email, "@") && strings.Contains(email, ".")
}""",
                "note": "Локальный модуль myutils"
            },
            {
                "filename": "mainapp/go.mod",
                "lang": "text",
                "code": """module company.com/mainapp

go 1.22.5

require company.com/myutils v0.0.0

replace company.com/myutils => ../myutils""",
                "note": "Файл mainapp/go.mod"
            },
            {
                "filename": "mainapp/main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"company.com/myutils/validator"
)

func main() {
	email := "alex@company.ru"
	isValid := validator.Validate(email)
	fmt.Printf("Email '%s' валиден: %t\\n", email, isValid)
}""",
                "note": "Импорт локального модуля"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """cd mainapp
go run .
# Вывод:
# Email 'alex@company.ru' валиден: true""",
                "note": "Запуск приложения"
            }
        ],
        "under_the_hood": """
При резолвинге пути `company.com/myutils/validator` компилятор сверяет таблицу подстановок `replace` и читает файлы напрямую из каталога `../myutils/validator`, минуя кэш модулей и сетевые прокси.
""",
        "pitfalls": """
- Использование абсолютных локальных путей вроде `/home/alex/myutils` в `replace` сделает проект неработоспособным на машинах коллег. Всегда используйте относительные пути (`../myutils`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что такое мультимодульный монорепозиторий (Monorepo) в Go и как в нем управлять версиями?»
**Ответ:** В монорепозитории в одном Git-репозитории живут десятки микросервисов и общих библиотек. Для локальной разработки без постоянных правок `replace` используют `go.work` (Go Workspaces), а в CI собирают бинарники в рамках единого коммита Git SHA.
"""
    },
    {
        "num": 66,
        "title": "Поиск уязвимостей в зависимостях через govulncheck",
        "task": "Создай модуль с уязвимой зависимостью. Запусти govulncheck (или go list -m -json all | nancy sleuth). Проанализируй результат.",
        "theory": """
Безопасность сторонних библиотек — ключевое требование к бэкенду.
Официальный инструмент от команды Go: **`govulncheck`** ([vuln.go.dev](https://vuln.go.dev)).

**Почему `govulncheck` на голову превосходит обычные сканеры вроде npm audit или trivy?**
Обычные сканеры просто сравнивают версию в манифесте: если у вас установлена библиотека `v1.0.0` с уязвимостью, они выдают тревогу (false positive), даже если вы используете только одну безопасную функцию из ста.

`govulncheck` строит **статический граф вызовов (Static Call Graph)** вашей программы! Он сообщает об уязвимости только в том случае, если скомпилированный код **реально вызывает уязвимую функцию**!
""",
        "step_by_step": """
1. Устанавливаем официальную утилиту: `go install golang.org/x/vuln/cmd/govulncheck@latest`.
2. Запускаем сканирование текущего проекта: `govulncheck ./...`.
3. Анализируем отчет (ID уязвимости GO-202X-XXXX, стек вызовов, исправленная версия).
""",
        "code_blocks": [
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# Установка утилиты аудита безопасности
go install golang.org/x/vuln/cmd/govulncheck@latest

# Запуск сканирования проекта
govulncheck ./...
# === Govulncheck ===
# No vulnerabilities found.
# Your code is safe!""",
                "note": "Сканирование проекта на уязвимости"
            }
        ],
        "under_the_hood": """
`govulncheck` запрашивает официальную базу данных `vuln.go.dev` через HTTP. Для каждого модуля строится SSA-представление функций и выполняется поиск путей достижимости (Reachability Analysis) от функции `main.main` до уязвимого символа.
""",
        "pitfalls": """
- Игнорирование аудита уязвимостей перед деплоем в прод. В BigTech запуск `govulncheck` встроен в блокирующий этап CI-пайплайна.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что такое Call Graph Reachability Analysis в `govulncheck`?»
**Ответ:** Это алгоритм статического анализа, который проверяет, может ли поток управления программы когда-либо дойти до конкретной уязвимой функции. Если уязвимый код никогда не вызывается в бинарнике, уязвимость классифицируется как невлияющая (unaffected), что исключает ложные срабатывания.
"""
    },
    {
        "num": 67,
        "title": "Предзагрузка исходных кодов через go mod download",
        "task": "Скачай исходники любого стороннего пакета (например, github.com/stretchr/testify) с помощью go mod download.",
        "theory": """
Команда `go mod download` скачивает модули, указанные в `go.mod`, в локальный кэш `$GOPATH/pkg/mod`, **не выполняя сборку или компиляцию кода**.

Зачем это нужно:
1. **Оптимизация Docker-образов (Layer Caching):** предварительное скачивание модулей до копирования исходного кода.
2. **Оффлайн-разработка:** скачивание всех зависимостей перед поездкой или работой без интернета.
""",
        "step_by_step": """
1. Выполняем `go mod download github.com/stretchr/testify`.
2. Проверяем, что исходники успешно сохранены в кэше.
""",
        "code_blocks": [
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# Предзагрузка всех зависимостей проекта
go mod download

# Предзагрузка конкретного пакета
go mod download github.com/stretchr/testify@v1.9.0""",
                "note": "Загрузка зависимостей в кэш"
            }
        ],
        "under_the_hood": """
`go mod download` параллельно скачивает `.mod` и `.zip` файлы зависимостей по протоколу GOPROXY и распаковывает их во временный каталог перед атомарным перемещением в `$GOPATH/pkg/mod`.
""",
        "pitfalls": """
- `go mod download` не проверяет, импортирован ли пакет в коде проекта — он просто сохраняет его в кэш.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем отличие `go mod download` от `go get`?»
**Ответ:** `go get` модифицирует `go.mod` (добавляет/обновляет зависимость). `go mod download` только скачивает файлы на диск на основе уже существующего `go.mod`, не меняя файл манифеста.
"""
    },
    {
        "num": 68,
        "title": "Приватные корпоративные репозитории: GOPRIVATE, GONOPROXY, GONOSUMDB",
        "task": "Создай приватный модуль (локально или на приватном репозитории). Настрой GOPRIVATE и GONOSUMDB. Импортируй его в другой проект.",
        "theory": """
В корпоративной разработке (Yandex, Ozon, Avito, VK, Tinkoff) исходный код закрыт и хранится на приватных серверах GitLab/GitHub Enterprise:
`gitlab.ozon.ru/payments/sdk`

Что произойдет, если запустить `go get gitlab.ozon.ru/payments/sdk` по умолчанию?
1. Go попытается отправить запрос на публичный сервер `proxy.golang.org`.
2. Публичный сервер вернет ошибку 404, а закрытый адрес вашего сервиса утечет на серверы Google!
3. Go попытается сверить хэш в публичной базе `sum.golang.org` и выдаст ошибку.

**Настройка приватных модулей в Go:**
Переменная **`GOPRIVATE`** указывает маску приватных репозиториев компании:
`go env -w GOPRIVATE="gitlab.ozon.ru/*,github.com/mycompany/*"`

Она автоматически отключает и прокси (`GONOPROXY`), и базу контрольных сумм (`GONOSUMDB`) для указанных доменов, заставляя Go обращаться к репозиторию напрямую через SSH/Git.
""",
        "step_by_step": """
1. Устанавливаем маску приватных пакетов: `go env -w GOPRIVATE=gitlab.company.ru/*`.
2. Настраиваем Git на авторизацию по SSH: `git config --global url."git@gitlab.company.ru:".insteadOf "https://gitlab.company.ru/"`.
3. Теперь `go get gitlab.company.ru/common/auth` скачивается безопасно и напрямую!
""",
        "code_blocks": [
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# Настройка приватного домена компании
go env -w GOPRIVATE="gitlab.company.ru/*"

# Проверка настроек
go env GOPRIVATE
# gitlab.company.ru/*

go env GONOPROXY
# gitlab.company.ru/* (наследуется от GOPRIVATE)

go env GONOSUMDB
# gitlab.company.ru/* (наследуется от GOPRIVATE)""",
                "note": "Конфигурация корпоративного окружения"
            }
        ],
        "under_the_hood": """
При совпадении префикса модуля с маской `GOPRIVATE` тулчейн Go обходит сетевой стек `GOPROXY` и вызывает системный бинарник `git clone` или `git ls-remote` напрямую к серверу, используя локальные SSH-ключи или `.netrc`.
""",
        "pitfalls": """
- Отсутствие настройки `GOPRIVATE` в CI/CD пайплайнах приводит к сбою сборки закрытых микросервисов.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Зачем нужна переменная `GONOSUMDB` отдельно от `GOPRIVATE`?»
**Ответ:** Если в компании развернут внутренний защищенный прокси-сервер (внутренний Athens/Artifactory), то `GONOPROXY` может быть пустым (скачиваем через внутренний прокси), но `GONOSUMDB` должен быть настроен на домены компании, чтобы не отправлять запросы в публичный `sum.golang.org`.
"""
    },
    {
        "num": 69,
        "title": "Инспекция доступных релизов пакета через go list -m -versions",
        "task": "Проверь, какие версии стороннего пакета доступны, используя go list -m -versions github.com/fatih/color.",
        "theory": """
Команда `go list -m -versions <module>` опрашивает прокси-сервер и выводит список всех официально опубликованных семантических версий и тегов библиотеки.
""",
        "step_by_step": """
1. Выполняем `go list -m -versions github.com/fatih/color`.
2. Анализируем список доступных релизов (от ранних `v1.0.0` до современных `v1.17.0`).
""",
        "code_blocks": [
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go list -m -versions github.com/fatih/color
# Вывод:
# github.com/fatih/color v0.1.0 v1.5.0 v1.6.0 v1.7.0 v1.8.0 v1.9.0 v1.10.0 v1.12.0 v1.13.0 v1.14.1 v1.15.0 v1.16.0 v1.17.0""",
                "note": "Просмотр версий модуля"
            }
        ],
        "under_the_hood": """
`go list` обращается к эндпоинту `https://proxy.golang.org/<module>/@v/list`, возвращающему список текстовых строк с версиями, прошедшими валидацию SemVer.
""",
        "pitfalls": """
- Если автор репозитория создал git-тег без префикса `v` (например, `1.2.0` вместо `v1.2.0`), Go проигнорирует такой тег, так как спецификация требует префикс `v`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что такое псевдоверсии (pseudo-versions) в Go (например, `v0.0.0-20230512181234-abcd1234ef56`)?»
**Ответ:** Псевдоверсия генерируется Go, когда вы подключаете модуль по хэшу коммита или ветке (не по тегу). Она состоит из базовой версии, UTC-таймстампа коммита и 12 символов SHA1-хэша коммита, гарантируя строгий порядок в MVS.
"""
    },
    {
        "num": 70,
        "title": "Механизм internal-пакетов: аппаратная инкапсуляция компилятора",
        "task": "Создай пакет internal/secret. Попробуй импортировать его из другого модуля (должна быть ошибка), а затем из того же модуля (должно работать).",
        "theory": """
В Go существует специальное зарезервированное имя директории — **`internal/`**.

**Закон пакетов `internal` (Internal Package Rule):**
Пакет, расположенный внутри директории `.../internal/...`, может быть импортирован **ТОЛЬКО кодом, находящимся в родительском дереве директорий по отношению к `internal`**.

Если сторонний модуль попытается импортировать ваш `internal`-пакет:
Компилятор Go **заблокирует сборку с фатальной ошибкой**:
`use of internal package not allowed`.

Это ключевой инструмент создания безопасных библиотек и монорепозиториев в BigTech: вы можете свободно менять код в `internal/`, гарантируя, что внешние пользователи не завяжутся на приватные кишки вашего сервиса.
""",
        "step_by_step": """
1. В текущем модуле создаем структуру `internal/secret/token.go`.
2. Объявляем функцию `GetAdminToken() string`.
3. В `main.go` (в том же модуле) импортируем `hello_mod/internal/secret` — компилируется успешно!
4. В соседнем внешнем модуле пробуем импортировать тот же пакет — компилятор выдает ошибку доступа.
""",
        "code_blocks": [
            {
                "filename": "internal/secret/token.go",
                "lang": "go",
                "code": """package secret

// GetAdminToken доступен только внутри текущего модуля hello_mod
func GetAdminToken() string {
	return "SEC-INTERNAL-SUPER-SECRET-TOKEN-999"
}""",
                "note": "Пакет внутри internal/"
            },
            {
                "filename": "main.go (Внутри того же модуля)",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"hello_mod/internal/secret"
)

func main() {
	tok := secret.GetAdminToken()
	fmt.Printf("Токен успешно получен внутри модуля: %s\\n", tok)
}""",
                "note": "Успешный импорт из разрешенного родительского дерева"
            },
            {
                "filename": "Внешний модуль external_app/main.go (Попытка импорта)",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"hello_mod/internal/secret" // ПОПЫТКА ИМПОРТА ИЗВНЕ!
)

func main() {
	fmt.Println(secret.GetAdminToken())
}""",
                "note": "Попытка несанкционированного импорта"
            },
            {
                "filename": "Вывод компилятора для external_app",
                "lang": "text",
                "code": """./main.go:5:2: use of internal package hello_mod/internal/secret not allowed""",
                "note": "Жесткая блокировка компилятором Go"
            }
        ],
        "under_the_hood": """
Компилятор Go (`cmd/compile`) при проверке каждого импорта проверяет вхождение подстроки `/internal/` в путь импорта. Если она присутствует, компилятор находит общего родителя (common ancestor) в путях файловой системы. Если вызывающий пакет находится вне поддерева каталога, в котором объявлен `internal`, сборка прерывается.
""",
        "pitfalls": """
- Попытка использовать `internal` для кода, который вы планируете экспортировать как публичную библиотеку для сторонних клиентов.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем разница между `pkg/` и `internal/` в стандартном макете Go-проекта (Standard Go Project Layout)?»
**Ответ:** Код в `pkg/` разрешен для импорта любыми внешними сервисами и модулями (публичные контракты, DTO, клиенты SDK). Код в `internal/` аппаратно защищен компилятором от импорта извне и содержит приватную бизнес-логику текущего сервиса.
"""
    },
    {
        "num": 71,
        "title": "Конфигурация 12-Factor App: переменные окружения и .env",
        "task": "Создай программу, которая читает переменные окружения (os.Getenv, os.LookupEnv). Реализуй конфигурацию через .env файл (можно использовать github.com/joho/godotenv или парсить самостоятельно).",
        "theory": """
Методология **The Twelve-Factor App (III. Конфигурация)**:
Конфигурация сервиса (порты, пароли к БД, секретные ключи, уровень логирования) должна строго отделяться от кода и передаваться через переменные окружения (Environment Variables).

В Go есть две основные функции для чтения окружения:
1. `os.Getenv(key)` — возвращает значение переменной или пустую строку `""`, если переменная не задана.
2. `os.LookupEnv(key)` — возвращает `(string, bool)`. Булевый флаг позволяет **отличить случай, когда переменная не задана вовсе, от случая, когда она задана равной пустой строке** (`FOO=""`)!

Для локальной разработки используется библиотека `github.com/joho/godotenv`, которая парсит `.env` файл и помещает переменные в окружение процесса.
""",
        "step_by_step": """
1. Скачиваем библиотеку: `go get github.com/joho/godotenv`.
2. Создаем файл конфигурации `.env`.
3. Пишем парсер конфигурации с валидацией обязательных полей и значениями по умолчанию.
""",
        "code_blocks": [
            {
                "filename": ".env",
                "lang": "text",
                "code": """APP_PORT=8080
DATABASE_URL=postgres://user:pass@localhost:5432/mydb?sslmode=disable
LOG_LEVEL=debug
APP_DEBUG=true""",
                "note": "Файл переменных окружения .env"
            },
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"os"
	"strconv"
	"github.com/joho/godotenv"
)

type Config struct {
	Port     int
	DBUrl    string
	LogLevel string
	IsDebug  bool
}

func LoadConfig() (*Config, error) {
	// Загружаем .env, если он существует (в продакшене переменные передаются оркестратором K8s)
	_ = godotenv.Load()

	// 1. Чтение порта со значением по умолчанию
	portStr := os.Getenv("APP_PORT")
	port := 8080
	if portStr != "" {
		if p, err := strconv.Atoi(portStr); err == nil {
			port = p
		}
	}

	// 2. Чтение критической переменной через LookupEnv
	dbURL, ok := os.LookupEnv("DATABASE_URL")
	if !ok || dbURL == "" {
		return nil, fmt.Errorf("обязательная переменная окружения DATABASE_URL не задана")
	}

	logLevel := os.Getenv("LOG_LEVEL")
	if logLevel == "" {
		logLevel = "info"
	}

	isDebug, _ := strconv.ParseBool(os.Getenv("APP_DEBUG"))

	return &Config{
		Port:     port,
		DBUrl:    dbURL,
		LogLevel: logLevel,
		IsDebug:  isDebug,
	}, nil
}

func main() {
	cfg, err := LoadConfig()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Ошибка конфигурации: %v\\n", err)
		os.Exit(1)
	}

	fmt.Println("=== КОНФИГУРАЦИЯ СЕРВИСА ЗАГРУЖЕНА ===")
	fmt.Printf("Порт:         %d\\n", cfg.Port)
	fmt.Printf("Database URL: %s\\n", cfg.DBUrl)
	fmt.Printf("Log Level:    %s\\n", cfg.LogLevel)
	fmt.Printf("Debug Mode:   %t\\n", cfg.IsDebug)
}""",
                "note": "Надежная загрузка конфигурации"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run .
# Вывод:
# === КОНФИГУРАЦИЯ СЕРВИСА ЗАГРУЖЕНА ===
# Порт:         8080
# Database URL: postgres://user:pass@localhost:5432/mydb?sslmode=disable
# Log Level:    debug
# Debug Mode:   true""",
                "note": "Результат запуска"
            }
        ],
        "under_the_hood": """
`godotenv` считывает файл `.env` построчно, разбирает кавычки, экранирование и комментарии `#`, после чего вызывает системный вызов `os.Setenv()`, добавляя пары ключ-значение в окружение процесса.
""",
        "pitfalls": """
- Коммит файла `.env` с реальными паролями и токенами в Git — грубейшее нарушение информационной безопасности. Файл `.env` обязательно добавляется в `.gitignore`, а в репозиторий коммитится шаблон `.env.example`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем принципиальная разница между `os.Getenv(\"DEBUG\")` и `os.LookupEnv(\"DEBUG\")`?»
**Ответ:** Если переменная окружения задана в shell как `export DEBUG=""`, `os.Getenv` вернет пустую строку `""`. При этом невозможно понять, существует ли переменная. `os.LookupEnv` вернет `("", true)`, сигнализируя, что переменная объявлена.
"""
    },
    {
        "num": 72,
        "title": "Управление внешними зависимостями в продакшен-микросервисах",
        "task": "Найдите популярный сторонний пакет (например, github.com/fatih/color или github.com/sirupsen/logrus), добавьте его в ваш проект с помощью go get.",
        "theory": """
Чек-лист выбора сторонней библиотеки в BigTech:
1. **Зрелость и поддержка:** регулярные коммиты, закрытые Issue, поддержка последних версий Go.
2. **Лицензия:** допустимы MIT, Apache 2.0, BSD. Запрещены строгие copyleft-лицензии (GPL v3, AGPL), так как они требуют раскрытия исходного кода всего проприетарного бэкенда компании.
3. **Количество зависимостей:** минимальное транзитивное дерево (принцип «A little copying is better than a little dependency»).
4. **Аллокации и производительность:** отсутствие утечек памяти в высоконагруженных циклах.
""",
        "step_by_step": """
1. Выполняем `go get github.com/sirupsen/logrus`.
2. Проверяем лицензию и граф зависимостей.
""",
        "code_blocks": [
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": "go get github.com/sirupsen/logrus@v1.9.3",
                "note": "Подключение проверенной библиотеки"
            }
        ],
        "under_the_hood": """
Go скачивает модуль с SHA256 верификацией и помещает распакованный исходный код в кэш `$GOPATH/pkg/mod/github.com/sirupsen/logrus@v1.9.3`.
""",
        "pitfalls": """
- Подключение «библиотек-однодневок» с 1 звездой на GitHub ради одной функции из 10 строк.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что гласит пословица Go Proverbs: `A little copying is better than a little dependency`?»
**Ответ:** Лучше скопировать 5-10 строк проверенной функции в свой проект, чем тащить тяжелую стороннюю библиотеку с десятками транзитивных зависимостей, рисками уязвимостей безопасности и усложнением обновлений.
"""
    },
    {
        "num": 73,
        "title": "Обновление минорных версий пакетов через go get -u",
        "task": "Обновите версию стороннего пакета до последней минорной версии с помощью go get -u и проверьте, не сломался ли ваш код.",
        "theory": """
Флаг `-u` (update) указывает тулчейну Go обновить указанный пакет (и его зависимости) до **самой последней доступной минорной/патч-версии** в рамках текущей мажорной версии:
- `go get -u github.com/fatih/color` — обновит `color` до последней версии (например, `v1.17.0`);
- `go get -u ./...` — обновит **все** зависимости проекта до последних версий.
""",
        "step_by_step": """
1. Запускаем `go get -u github.com/fatih/color`.
2. Запускаем тесты `go test ./...` для проверки обратной совместимости.
3. Запускаем `go mod tidy` для фиксации хэшей.
""",
        "code_blocks": [
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# Обновление пакета до свежего релиза
go get -u github.com/fatih/color

# Прогон всех тестов после апгрейда
go test -v ./...

# Очистка
go mod tidy""",
                "note": "Обновление зависимостей и прогон тестов"
            }
        ],
        "under_the_hood": """
`go get -u` запрашивает актуальный список версий с прокси, находит наибольший SemVer тег без ломающих изменений и обновляет записи в `go.mod`.
""",
        "pitfalls": """
- Слепое выполнение `go get -u ./...` на огромном проекте без достаточного покрытия интеграционными тестами может привести к регрессионным ошибкам.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем разница между `go get package@latest` и `go get -u package`?»
**Ответ:** `go get package@latest` обновляет только сам указанный пакет до последней версии, оставляя его транзитивные зависимости на минимально требуемых версиях. Флаг `-u` рекурсивно обновляет как сам целевой пакет, так и **все его транзитивные зависимости**.
"""
    },
    {
        "num": 74,
        "title": "Модуль с пакетами main и greeter: архитектурное разделение",
        "task": "Создайте модуль с двумя пакетами: main и greeter. Импортируйте greeter и вызовите его публичную функцию.",
        "theory": """
Классический паттерн разделения приложения:
- Пакет `greeter` — чистый доменный слой, не знающий ничего о консоли, HTTP или базах данных;
- Пакет `main` — точка входа, связывающая слои.
""",
        "step_by_step": """
1. Создаем папку `greeter/` и файл `greeter/greet.go`.
2. Объявляем структуру `Greeter` и метод `Greet(name string) string`.
3. В `main.go` создаем экземпляр `greeter.New()` и выводим приветствие.
""",
        "code_blocks": [
            {
                "filename": "greeter/greet.go",
                "lang": "go",
                "code": """package greeter

import "fmt"

type Service struct {
	Prefix string
}

func New(prefix string) *Service {
	return &Service{Prefix: prefix}
}

func (s *Service) Greet(name string) string {
	return fmt.Sprintf("%s, %s! Рады видеть вас в системе.", s.Prefix, name)
}""",
                "note": "Пакет greeter"
            },
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"hello_mod/greeter"
)

func main() {
	svc := greeter.New("Приветствуем")
	msg := svc.Greet("Константин")
	fmt.Println(msg)
}""",
                "note": "Файл main.go"
            }
        ],
        "under_the_hood": """
Вызов метода структуры `svc.Greet` в Go компилируется в прямой вызов функции `greeter.(*Service).Greet(svc, name)` с передачей указателя на получатель (receiver) в качестве первого скрытого аргумента.
""",
        "pitfalls": """
- Попытка передавать изменяемое состояние сервиса без указателя (`func (s Service)`), что приводит к копированию всей структуры при каждом вызове.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Когда в Go следует использовать pointer receiver (`*Service`), а когда value receiver (`Service`)?»
**Ответ:** Pointer receiver (`*T`) обязателен, если: 1. Метод должен мутировать состояние структуры; 2. Структура содержит большие поля или мьютексы `sync.Mutex` (их нельзя копировать); 3. Для консистентности API (если у одного метода pointer receiver, у всех остальных методов типа тоже делают pointer receiver).
"""
    },
    {
        "num": 75,
        "title": "Защита внутренней бизнес-логики через каталог internal/",
        "task": "Создайте пакет с внутренней реализацией в каталоге internal и убедитесь, что код извне модуля не может его импортировать.",
        "theory": """
Реализуем эталонную архитектуру микросервиса:
```text
my_service/
├── cmd/
│   └── server/
│       └── main.go        (Точка входа)
├── internal/
│   ├── auth/              (Приватная авторизация)
│   └── database/          (Приватные репозитории)
└── go.mod
```

Ни один внешний проект не сможет импортировать `my_service/internal/auth`!
""",
        "step_by_step": """
1. Создаем структуру каталогов `internal/auth/`.
2. Создаем файл `internal/auth/jwt.go` с функцией `GenerateInternalToken(userID int64) string`.
3. В `cmd/server/main.go` вызываем функцию и проверяем корректность сборки.
""",
        "code_blocks": [
            {
                "filename": "internal/auth/jwt.go",
                "lang": "go",
                "code": """package auth

import "fmt"

func GenerateInternalToken(userID int64) string {
	return fmt.Sprintf("JWT.HEADER.USER_%d.SIGNATURE_SECRET", userID)
}""",
                "note": "Защищенный внутренний пакет internal/auth"
            },
            {
                "filename": "cmd/server/main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"hello_mod/internal/auth"
)

func main() {
	token := auth.GenerateInternalToken(9941)
	fmt.Printf("Сгенерирован внутренний токен: %s\\n", token)
}""",
                "note": "Точка входа cmd/server/main.go"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run ./cmd/server
# Вывод:
# Сгенерирован внутренний токен: JWT.HEADER.USER_9941.SIGNATURE_SECRET""",
                "note": "Успешный запуск команды из каталога cmd/server"
            }
        ],
        "under_the_hood": """
Правило `internal` проверяется компилятором на основе пути к пакету в AST. Если путь содержит токен `/internal/`, компилятор сверяет родительский префикс импортируемого и импортирующего пакетов.
""",
        "pitfalls": """
- Размещение в `internal` кода, который должен быть повторно использован другими сервисами компании. Для общего кода создают отдельные библиотеки-репозитории или выносят в `pkg/`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли разместить директорию `internal/` внутри подкаталога (например, `pkg/api/internal/parser`)?»
**Ответ:** Да! Правило `internal` работает на любом уровне вложенности. В этом случае пакет `parser` будет доступен только коду внутри `pkg/api/...`, но недоступен даже другим пакетам того же модуля (например, `pkg/database`).
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Section 5: {len(exercises)} exercises.")
