exercises = [
  {
    "num": 1,
    "title": "Базовый workflow GitHub Actions: триггеры, Checkout, Setup-Go и тестирование с детектором гонок",
    "task": "Создай **базовый workflow**: `.github/workflows/ci.yml`. Triggers: `on: [push, pull_request]`. Jobs: `test` (checkout, setup Go, `go test -race -cover`), `build` (depends on test, `go build`). Покажи green check на PR.",
    "theory": "Автоматизация непрерывной интеграции (CI — Continuous Integration) гарантирует, что каждый коммит и Pull Request проверяются независимым билд-агентом на ошибки компиляции, дефекты линтинга и падение тестов.\n\nВ экосистеме **GitHub Actions**:\n1. Конфигурация хранится в каталоге `.github/workflows/*.ya?ml`.\n2. Блок `on:` задает триггеры событий: `push` (отправка в ветки) и `pull_request` (создание или обновление PR).\n3. `jobs:` определяет параллельные задачи, выполняемые на изолированных виртуальных машинах (`runs-on: ubuntu-latest`).\n4. Шаг `actions/checkout@v4` клонирует репозиторий.\n5. Шаг `actions/setup-go@v5` настраивает тулчейн Go заданной версии и автоматически подключает кэширование модулей.\n6. Вызов `go test -v -race -timeout 30s ./...` запускает тесты с **детектором гонок данных (Race Detector)**, выявляющим несинхронизированный доступ к разделяемой памяти между горутинами.",
    "step_by_step": "1. Создайте структуру каталогов `.github/workflows/`.\n2. Создайте файл `ci.yml` с триггерами на `push` и `pull_request`.\n3. Добавьте шаги `actions/checkout@v4` и `actions/setup-go@v5` с версией `1.24`.\n4. Настройте запуск тестов с флагами `-v -race -timeout 60s`.\n5. Напишите тестируемый Go-код и модульный тест.",
    "code_blocks": [
      {
        "filename": ".github/workflows/ci.yml",
        "lang": "yaml",
        "code": "name: Continuous Integration\n\non:\n  push:\n    branches: [ main, develop ]\n  pull_request:\n    branches: [ main ]\n\njobs:\n  test:\n    name: Run Unit Tests & Race Detector\n    runs-on: ubuntu-latest\n\n    steps:\n      - name: Checkout Source Code\n        uses: actions/checkout@v4\n\n      - name: Set up Go 1.24\n        uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n          cache: true\n\n      - name: Verify Dependencies\n        run: go mod verify\n\n      - name: Execute Tests with Race Detector\n        run: go test -v -race -timeout 60s ./...",
        "note": "Базовый GitHub Actions CI workflow"
      },
      {
        "filename": "service.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"sync\"\n)\n\n// ThreadSafeCounter обеспечивает потокобезопасный инкремент\ntype ThreadSafeCounter struct {\n\tmu    sync.Mutex\n\tvalue int\n}\n\nfunc (c *ThreadSafeCounter) Inc() {\n\tc.mu.Lock()\n\tdefer c.mu.Unlock()\n\tc.value++\n}\n\nfunc (c *ThreadSafeCounter) Value() int {\n\tc.mu.Lock()\n\tdefer c.mu.Unlock()\n\treturn c.value\n}\n\nfunc main() {\n\t// Точка входа сервиса\n}",
        "note": "Потокобезопасный компонент для проверки детектором гонок"
      },
      {
        "filename": "service_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"sync\"\n\t\"testing\"\n)\n\nfunc TestThreadSafeCounter(t *testing.T) {\n\tc := &ThreadSafeCounter{}\n\tvar wg sync.WaitGroup\n\n\titerations := 100\n\twg.Add(iterations)\n\tfor i := 0; i < iterations; i++ {\n\t\tgo func() {\n\t\t\tdefer wg.Done()\n\t\t\tc.Inc()\n\t\t}()\n\t}\n\twg.Wait()\n\n\tif c.Value() != iterations {\n\t\tt.Fatalf(\"Expected %d, got %d\", iterations, c.Value())\n\t}\n}",
        "note": "Параллельный тест для детектора гонок"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Локальная эмуляция шагов CI пайплайна\ngo mod verify\ngo test -v -race -timeout 60s ./..."
      }
    ],
    "under_the_hood": "Флаг `-race` перекомпилирует код с помощью ThreadSanitizer (TSan). Компилятор внедряет инструментирующий код вокруг каждой операции чтения и записи в память (8-байтные shadow memory адреса). Если две горутины обращаются к одной ячейке памяти без синхронизации (мьютексы, каналы, atomic), рантайм мгновенно падает с ненулевым кодом выхода и подробным стектрейсом, что переводит задачу CI в статус failed.",
    "pitfalls": "1. Запуск тестов без флага `-race`: Data Race может не проявляться на 1 ядре локального компьютера, но обрушить production под нагрузкой.\n2. Отсутствие `-timeout`: зависший тест (дедлок в канале) заблокирует раннер GitHub Actions на максимальный таймаут по умолчанию (360 минут / 6 часов).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в CI-пайплайне критически важно запускать тесты с флагом `-race`, и почему этот флаг не используют при компиляции продакшн-образов?»\n**Ответ:** Флаг `-race` включает ThreadSanitizer, который отслеживает все операции с памятью в рантайме и гарантированно выявляет гонки данных (Data Races) между горутинами. Однако в продакшне его использовать нельзя, так как инструментирование памяти увеличивает потребление CPU в 2–10 раз, а потребление RAM — в 5–20 раз. В продакшн компилируют с `go build -ldflags=\"-w -s\"`, а `-race` держат обязательным шагом на этапе CI."
  },
  {
    "num": 2,
    "title": "Матричные сборки (Matrix Strategy): тестирование на нескольких версиях Go и разных ОС",
    "task": "Добавь **matrix strategy**: `strategy: matrix: go-version: ['1.22', '1.23', '1.24'], os: [ubuntu-latest, windows-latest]`. Покажи параллельный запуск на всех комбинациях.",
    "theory": "При разработке библиотек общего назначения (Open Source SDK, драйверы, утилиты) критически важно гарантировать совместимость с несколькими версиями Go и различными операционными системами (Linux, Windows, macOS).\n\nДиректива **`strategy: matrix:`** в GitHub Actions:\n- Позволяет задать многомерную матрицу параметров (`go-version`, `os`).\n- Автоматически создает декартово произведение (Cartesian Product) всех комбинаций.\n- Запускает каждую комбинацию параллельно в изолированном контейнере/раннере.\n\nОпция `fail-fast: false` гарантирует, что если билд упадет на одной версии (например, Windows + Go 1.22), остальные ветки матрицы продолжат выполнение до конца, предоставив полный отчет об ошибках.",
    "step_by_step": "1. В `ci.yml` объявите блок `strategy: matrix:`.\n2. Задайте список версий Go: `['1.22', '1.23', '1.24']`.\n3. Задайте список операционных систем: `[ubuntu-latest, windows-latest]`.\n4. Настройте `actions/setup-go` с параметром `go-version: ${{ matrix.go-version }}`.\n5. Проверьте запуск 6 параллельных задач в интерфейсе GitHub Actions.",
    "code_blocks": [
      {
        "filename": ".github/workflows/matrix-ci.yml",
        "lang": "yaml",
        "code": "name: Cross-Platform Matrix CI\n\non:\n  push:\n    branches: [ main ]\n  pull_request:\n    branches: [ main ]\n\njobs:\n  matrix-test:\n    name: Test (Go ${{ matrix.go-version }} on ${{ matrix.os }})\n    runs-on: ${{ matrix.os }}\n    strategy:\n      fail-fast: false\n      matrix:\n        go-version: ['1.22', '1.23', '1.24']\n        os: [ubuntu-latest, windows-latest]\n\n    steps:\n      - name: Checkout Code\n        uses: actions/checkout@v4\n\n      - name: Set up Go ${{ matrix.go-version }}\n        uses: actions/setup-go@v5\n        with:\n          go-version: ${{ matrix.go-version }}\n          cache: true\n\n      - name: Run Tests\n        run: go test -v ./...",
        "note": "Матричный workflow GitHub Actions"
      },
      {
        "filename": "cross_platform.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"path/filepath\"\n\t\"runtime\"\n)\n\n// GetAppPath возвращает нормализованный путь с учетом разделителей ОС (\\ для Windows, / для Linux)\nfunc GetAppPath(dir, filename string) string {\n\treturn filepath.Join(dir, filename)\n}\n\nfunc main() {\n\tfmt.Printf(\"OS: %s, Arch: %s, GoVersion: %s\\n\",\n\t\truntime.GOOS, runtime.GOARCH, runtime.Version())\n}",
        "note": "Код, учитывающий особенности файловых путей разных ОС"
      },
      {
        "filename": "cross_platform_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"path/filepath\"\n\t\"testing\"\n)\n\nfunc TestGetAppPath(t *testing.T) {\n\tresult := GetAppPath(\"configs\", \"app.yaml\")\n\texpected := filepath.Join(\"configs\", \"app.yaml\")\n\tif result != expected {\n\t\tt.Fatalf(\"Expected %q, got %q\", expected, result)\n\t}\n}",
        "note": "Кросс-платформенный тест"
      }
    ],
    "under_the_hood": "Движок GitHub Actions компилирует матрицу в независимые виртуальные машины. Для Windows выделяется инстанс Windows Server с PowerShell в качестве шелла по умолчанию, а для Linux — Ubuntu с Bash. Это позволяет вскрыть специфичные баги Go, связанные с разделителями путей (`filepath.Separator`), переносами строк (`\\r\\n` против `\\n`) и регистронезависимостью файловых систем.",
    "pitfalls": "1. Забытый `filepath.FromSlash` / `filepath.Join`: хардкод слешей `/` в тестах приведет к падению на `windows-latest`.\n2. Высокий расход бесплатных минут GitHub Actions (раннеры Windows и macOS расходуют квоту в 2–10 раз быстрее Linux).",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем нужна директива `fail-fast: false` в матричной стратегии CI?»\n**Ответ:** По умолчанию в GitHub Actions включен режим `fail-fast: true`: если любая одна задача из матрицы завершается с ошибкой, GitHub автоматически отменяет все остальные параллельно выполняющиеся задачи матрицы. Режим `fail-fast: false` отключает этот механизм, позволяя всем комбинациям ОС и версий Go дойти до конца. Это дает инженеру полную картину (например, понять, что баг специфичен только для Go 1.22 на Windows, а не ломает весь проект целиком)."
  },
  {
    "num": 3,
    "title": "Пайплайн по пушу в main: автоматический запуск тестов и сборки артефакта",
    "task": "**[GitHub Actions / GitLab CI]**: Напиши пайплайн, который срабатывает при пуше в ветку `main`. Пайплайн должен запускать `go test ./...` и `golangci-lint run`.",
    "theory": "Ветка `main` (или `master`) в современной разработке рассматривается как защищенный релизный транк (Trunk-Based Development). Любой коммит в `main` обязан быть протестирован, проверен и собран в готовый бинарный артефакт.\n\nТиповой конвейер по пушу в `main`:\n1. Триггер: `on.push.branches: [main]`.\n2. Job 1 (`test`): скачивание зависимостей, прогон unit-тестов с флагом `-race`.\n3. Job 2 (`build`): сборка продакшн-бинарника с флагами оптимизации (`CGO_ENABLED=0 go build -ldflags=\"-w -s\"`).\n4. Загрузка собранного бинарника в хранилище артефактов GitHub Actions через `actions/upload-artifact@v4` для последующего деплоя.",
    "step_by_step": "1. Создайте `.github/workflows/main.yml`.\n2. Ограничьте триггер только веткой `main`.\n3. Настройте зависимость задач через `needs: [test]`.\n4. Соберите статический бинарник и выгрузите его как артефакт.",
    "code_blocks": [
      {
        "filename": ".github/workflows/main.yml",
        "lang": "yaml",
        "code": "name: Main Branch Pipeline\n\non:\n  push:\n    branches:\n      - main\n\njobs:\n  test:\n    name: Run Unit Tests\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n          cache: true\n      - name: Run Tests\n        run: go test -v -race ./...\n\n  build:\n    name: Compile Release Binary\n    needs: test\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n          cache: true\n\n      - name: Build Binary\n        run: |\n          mkdir -p dist\n          CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags=\"-w -s\" -o dist/app-linux-amd64 .\n\n      - name: Upload Artifact\n        uses: actions/upload-artifact@v4\n        with:\n          name: release-binary\n          path: dist/app-linux-amd64\n          retention-days: 7",
        "note": "Workflow со связанными задачами test -> build"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"Main branch build ready for deployment!\")\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Основной код сервиса"
      }
    ],
    "under_the_hood": "Директива `needs: test` строит направленный граф (DAG) выполнения. GitHub Actions не выделяет раннер для задачи `build`, пока `test` не завершится с кодом 0. Выгруженные через `upload-artifact` файлы передаются через защищенное S3-хранилище GitHub и доступны для скачивания или использования на этапе deploy.",
    "pitfalls": "1. Забытый `needs`: задачи `test` и `build` запустятся параллельно, и бинарник будет собран даже при падении тестов!\n2. Слишком длинный срок хранения артефактов (`retention-days`), исчерпывающий дисковую квоту репозитория.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем разделять пайплайн на две отдельные job (`test` и `build`) с директивой `needs`, а не выполнить всё в одной job последовательными шагами `run`?»\n**Ответ:** 1) Принцип Fail-Fast: разделение изолирует логику и позволяет не тратить ресурсы раннера на сборку артефактов при падении тестов. 2) Параллелизм и независимость окружений: тесты могут требовать CGO и GCC, а билд компилируется в статическом чистом контейнере. 3) Четкая визуализация в UI: инженер мгновенно видит на графе, на каком именно этапе произошел сбой (тесты или компиляция)."
  },
  {
    "num": 4,
    "title": "Статический анализ: настройка golangci-lint и конфигурация .golangci.yml",
    "task": "Добавь **lint**: `golangci-lint` через `golangci/golangci-lint-action@v6`. Конфиг `.golangci.yml`: `linters: [errcheck, gosimple, govet, ineffassign, staticcheck, typecheck, unused]`. Gate: lint failure = build failure.",
    "theory": "Статический анализ кода выявляет баги, утечки ресурсов, пропущенные проверки ошибок и нарушения кодстайла еще до этапа компиляции и тестирования.\n\n**`golangci-lint`** — быстрый агрегатор линтеров Go, запускающий десятки анализаторов параллельно над общим AST-деревом парсера.\n\nКлючевые обязательные линтеры:\n- `errcheck`: гарантирует, что ни одна возвращаемая ошибка не проигнорирована.\n- `govet`: официальный анализатор Go (проверка теневых переменных, копирования мьютексов).\n- `gosimple`: упрощение избыточных конструкций языка.\n- `ineffassign`: поиск неэффективных присваиваний и перезаписи переменных.\n- `gosec`: поиск потенциальных уязвимостей (SQL-инъекции, слабые генераторы случайных чисел).\n\nВ GitHub Actions используется официальный экшен `golangci/golangci-lint-action@v6` с автоматическим кэшированием результатов.",
    "step_by_step": "1. Создайте файл конфигурации `.golangci.yml` в корне репозитория.\n2. Включите обязательные линтеры: `errcheck`, `gosimple`, `govet`, `ineffassign`, `staticcheck`.\n3. Добавьте шаг линтинга в `.github/workflows/lint.yml`.\n4. Протестируйте локальный запуск линтера командой `golangci-lint run`.",
    "code_blocks": [
      {
        "filename": ".golangci.yml",
        "lang": "yaml",
        "code": "run:\n  timeout: 5m\n  tests: true\n\nlinters:\n  disable-all: true\n  enable:\n    - errcheck     # Проверка обработки всех ошибок\n    - gosimple     # Упрощение конструкций кода\n    - govet        # Официальные проверки go vet\n    - ineffassign  # Детекция бесполезных присваиваний\n    - staticcheck  # Глубокий статический анализ\n    - unused       # Поиск неиспользуемых функций и констант\n\nlinters-settings:\n  errcheck:\n    check-type-assertions: true\n    check-blank: true\n\nissues:\n  exclude-use-default: false\n  max-issues-per-linter: 0\n  max-same-issues: 0",
        "note": "Файл конфигурации .golangci.yml"
      },
      {
        "filename": ".github/workflows/lint.yml",
        "lang": "yaml",
        "code": "name: Code Quality & Lint\n\non:\n  push:\n    branches: [ main ]\n  pull_request:\n\njobs:\n  golangci:\n    name: Run golangci-lint\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n          cache: false # Экшен golangci-lint сам управляет своим кэшем\n\n      - name: Run golangci-lint\n        uses: golangci/golangci-lint-action@v6\n        with:\n          version: v1.64\n          args: --config=.golangci.yml --timeout=5m",
        "note": "Workflow для проверки качества кода"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n)\n\nfunc run() error {\n\t// Корректная обработка ошибки без игнорирования\n\tf, err := os.Open(\"config.json\")\n\tif err != nil {\n\t\treturn fmt.Errorf(\"open file error: %w\", err)\n\t}\n\tdefer f.Close()\n\treturn nil\n}\n\nfunc main() {\n\tif err := run(); err != nil {\n\t\tfmt.Fprintf(os.Stderr, \"Error: %v\\n\", err)\n\t}\n}",
        "note": "Чистый код, проходящий проверки линтера"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Локальная установка и запуск golangci-lint\ngolangci-lint run ./..."
      }
    ],
    "under_the_hood": "`golangci-lint` парсит все исходники один раз, преобразуя их в структуры `go/ast` и `go/types`. Затем все включенные линтеры запускаются конкурентно как горутины над разделяемым представлением AST, что работает в 3–5 раз быстрее поочередного запуска утилит.",
    "pitfalls": "1. Игнорирование проверки типа `val := x.(MyType)` без `ok`, что при несовпадении типов приводит к рантайм-панике.\n2. Слишком мягкие настройки линтера (отключение `errcheck`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Enterprise-командах запрещено использовать пустые идентификаторы ошибок вида `_ = json.Unmarshal(...)` или вызывать функции без проверки ошибки в Go?»\n**Ответ:** Необработанная ошибка приводит к распространению невалидного или нулевого состояния (nil pointer dereference) вглубь системы, из-за чего сервис падает с паникой далеко от реального места возникновения сбоя. Линтер `errcheck` с параметром `check-blank: true` отлавливает попытки замалчивания ошибок через `_ = ...`, заставляя инженера явно обрабатывать или возвращать ошибку вверх по стеку."
  },
  {
    "num": 5,
    "title": "Безопасность в CI: статический анализ уязвимостей через gosec, nancy и Trivy",
    "task": "Добавь **security scan**: `gosec` (SAST), `nancy` (dependency vulnerabilities), `trivy` (container scan). Gate: `HIGH`/`CRITICAL` = failure. Покажи security-first pipeline.",
    "theory": "Концепция **DevSecOps (Shift-Left Security)** требует переноса проверок информационной безопасности на самые ранние этапы разработки.\n\nКомплексный сканирующий пайплайн объединяет три уровня защиты:\n1. **SAST (Static Application Security Testing) — `gosec`:**\n   Анализирует исходный Go-код на известные паттерны уязвимостей (CWE): жестко зашитые пароли, небезопасные вызовы `os/exec`, использование слабых хэш-функций (MD5, SHA1), SQL-инъекции, незащищенный парсинг TLS.\n2. **SCA (Software Composition Analysis) — `nancy` / `govulncheck`:**\n   Проверяет дерево зависимостей (`go.mod`, `go.sum`) по базе известных уязвимостей.\n3. **Container Image Scan — `trivy`:**\n   Сканирует собранный Docker-образ на уязвимости системных пакетов ОС.\n\nSecurity Gate: при обнаружении уязвимостей уровня `HIGH` или `CRITICAL` пайплайн автоматически падает с ошибкой (`exit code 1`), блокируя слияние кода.",
    "step_by_step": "1. Создайте `.github/workflows/security.yml`.\n2. Настройте запуск `gosec` с порогом строгости `-severity high`.\n3. Добавьте шаг проверки зависимостей через `govulncheck`.\n4. Настройте генерацию отчетов в формате SARIF для интеграции с вкладкой Security в GitHub.",
    "code_blocks": [
      {
        "filename": ".github/workflows/security.yml",
        "lang": "yaml",
        "code": "name: Security Audit & SAST\n\non:\n  push:\n    branches: [ main ]\n  pull_request:\n\njobs:\n  security-audit:\n    name: Run SAST & Dependency Scans\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n          cache: true\n\n      # 1. Запуск gosec (SAST)\n      - name: Run Gosec Security Scanner\n        uses: securego/gosec@master\n        with:\n          args: '-severity high -confidence high -fmt sarif -out results.sarif ./'\n\n      # 2. Проверка зависимостей через официальный govulncheck\n      - name: Run Govulncheck\n        run: |\n          go install golang.org/x/vuln/cmd/govulncheck@latest\n          govulncheck ./...",
        "note": "Workflow статического анализа безопасности"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"crypto/rand\"\n\t\"fmt\"\n\t\"math/big\"\n)\n\n// Безопасная генерация криптографически стойкого случайного токена\nfunc generateSecureToken() (int64, error) {\n\tnBig, err := rand.Int(rand.Reader, big.NewInt(1000000))\n\tif err != nil {\n\t\treturn 0, err\n\t}\n\treturn nBig.Int64(), nil\n}\n\nfunc main() {\n\ttoken, _ := generateSecureToken()\n\tfmt.Printf(\"Cryptographically secure token: %d\\n\", token)\n}",
        "note": "Безопасный код без использования уязвимого math/rand"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Локальная проверка уязвимостей\ngo install github.com/securego/gosec/v2/cmd/gosec@latest\ngosec -severity high ./..."
      }
    ],
    "under_the_hood": "`gosec` анализирует AST-дерево программы по набору правил CWE (Common Weakness Enumeration). Например, правило `G404` отлавливает использование `math/rand` вместо `crypto/rand` в контекстах генерации токенов, а правило `G201` находит строковую конкатенацию в SQL-запросах вместо параметризованных placeholders (`$1`, `?`).",
    "pitfalls": "1. Использование `math/rand` для генерации паролей или session ID.\n2. Подавление предупреждений безопасности директивами `// #nosec` без письменного согласования с отделом ИБ.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие SAST сканирования (gosec) от анализа зависимостей SCA (govulncheck/nancy)?»\n**Ответ:** SAST анализирует код, написанный разработчиками вашей компании: он ищет дефекты безопасности в реализации логики (небезопасный парсинг путей к файлам, конкатенация SQL, слабые шифры, захардкоженные API-ключи). SCA (Software Composition Analysis) не анализирует вашу бизнес-логику, а проверяет внешние Open Source библиотеки из `go.mod` на наличие уже известных опубликованных уязвимостей (CVE) в мировых базах данных."
  },
  {
    "num": 6,
    "title": "Отчетность о покрытии кода тестами (Code Coverage) и экспорт в HTML",
    "task": "Добавь **coverage reporting**: `go test -coverprofile=coverage.out -covermode=atomic`. `go tool cover -html=coverage.out -o coverage.html`. Upload to Codecov/Coveralls. Gate: coverage < 80% = failure (или warning).",
    "theory": "Метрика **Code Coverage** (покрытие кода тестами) отражает процент строк и ветвлений логики, выполненных во время прогона тестового набора.\n\nКоманды Go для работы с покрытием:\n1. `go test -coverprofile=coverage.out -covermode=atomic ./...`:\n   - Генерирует файл профиля покрытия.\n   - Режим `-covermode=atomic` критически важен для параллельных тестов, так как использует атомарные операции для счетчиков выполнения строк, предотвращая гонки данных в самих тестах.\n2. `go tool cover -func=coverage.out`:\n   - Выводит суммарный процент покрытия по каждому пакету и функции в консоль.\n3. `go tool cover -html=coverage.out -o coverage.html`:\n   - Генерирует интерактивный HTML-отчет, где зеленым подсвечены выполненные строки, а красным — не покрытые тестами.\n\nВ CI пайплайне этот HTML-файл сохраняется как артефакт, позволяя разработчикам исследовать пробелы в тестировании прямо в браузере.",
    "step_by_step": "1. Напишите код с условиями ветвления и тесты к нему.\n2. Запустите генерацию профиля покрытия с флагом `-covermode=atomic`.\n3. Сформируйте HTML-отчет.\n4. В `.github/workflows/coverage.yml` настройте публикацию артефакта покрытия.",
    "code_blocks": [
      {
        "filename": "discount.go",
        "lang": "go",
        "code": "package main\n\n// CalculateDiscount вычисляет скидку клиента в процентах\nfunc CalculateDiscount(isVIP bool, totalAmount float64) int {\n\tif isVIP {\n\t\tif totalAmount > 1000 {\n\t\t\treturn 25\n\t\t}\n\t\treturn 15\n\t}\n\n\tif totalAmount > 500 {\n\t\treturn 10\n\t}\n\treturn 0\n}",
        "note": "Бизнес-логика с несколькими ветвлениями"
      },
      {
        "filename": "discount_test.go",
        "lang": "go",
        "code": "package main\n\nimport \"testing\"\n\nfunc TestCalculateDiscount(t *testing.T) {\n\ttests := []struct {\n\t\tname     string\n\t\tisVIP    bool\n\t\tamount   float64\n\t\texpected int\n\t}{\n\t\t{\"VIP large amount\", true, 1200, 25},\n\t\t{\"VIP small amount\", true, 500, 15},\n\t\t{\"Regular customer discount\", false, 600, 10},\n\t\t{\"Regular no discount\", false, 200, 0},\n\t}\n\n\tfor _, tt := range tests {\n\t\tt.Run(tt.name, func(t *testing.T) {\n\t\t\tgot := CalculateDiscount(tt.isVIP, tt.amount)\n\t\t\tif got != tt.expected {\n\t\t\t\tt.Fatalf(\"Expected %d, got %d\", tt.expected, got)\n\t\t\t}\n\t\t})\n\t}\n}",
        "note": "Табличные тесты для 100% покрытия всех веток"
      },
      {
        "filename": ".github/workflows/coverage.yml",
        "lang": "yaml",
        "code": "name: Test Coverage Report\n\non: [push, pull_request]\n\njobs:\n  coverage:\n    name: Generate Code Coverage\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n          cache: true\n\n      - name: Run Tests with Atomic Coverage Profile\n        run: go test -v -race -coverprofile=coverage.out -covermode=atomic ./...\n\n      - name: Generate HTML Report\n        run: go tool cover -html=coverage.out -o coverage.html\n\n      - name: Output Summary to Console\n        run: go tool cover -func=coverage.out\n\n      - name: Upload HTML Coverage Artifact\n        uses: actions/upload-artifact@v4\n        with:\n          name: html-coverage-report\n          path: coverage.html\n          retention-days: 14",
        "note": "Workflow генерации артефактов покрытия"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Локальная генерация и проверка покрытия\ngo test -coverprofile=coverage.out -covermode=atomic ./...\ngo tool cover -func=coverage.out\n# Вывод: total: (statements) 100.0%"
      }
    ],
    "under_the_hood": "Компилятор Go при флаге `-covermode=atomic` оборачивает каждый блок базового кода (Basic Block) в вызов функции `sync/atomic.AddUint32(&counter, 1)`. При завершении программы буфер счетчиков записывается в текстовый файл с указанием координат строк `file:startLine.col,endLine.col numStatements count`.",
    "pitfalls": "1. Использование `-covermode=set` или `count` при параллельном запуске тестов (`-race`): возникнет Data Race на счетчиках покрытия. Всегда используйте `-covermode=atomic`.\n2. Ложное чувство безопасности при высоком проценте покрытия: 100% Line Coverage не гарантирует отсутствия багов при граничных значениях аргументов (Edge Cases).",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем разница между режимами `covermode` в Go: `set`, `count` и `atomic`?»\n**Ответ:** 1) `set` (по умолчанию без race) — булев флаг, фиксирует только факт «была ли выполнена строка хотя бы один раз». 2) `count` — числовой счетчик, фиксирует точное количество раз выполнения каждого блока кода (непотокобезопасен). 3) `atomic` — потокобезопасный атомарный счетчик (`atomic.AddInt32`). Режим `atomic` обязателен при конкурентном тестировании и запуске совместно с флагом `-race`."
  },
  {
    "num": 7,
    "title": "GitHub Actions: запуск проверок на каждый Pull Request для защиты ветки main",
    "task": "Создайте GitHub Actions workflow, который запускает `go test ./...` на каждый PR.",
    "theory": "Запуск тестов на событие `pull_request` — ключевой механизм контроля качества перед слиянием (Pre-merge Validation).\n\nПри наступлении события `pull_request`:\n- GitHub Actions автоматически создает **фиктивный merge-коммит** (`refs/pull/PR_NUMBER/merge`), объединяющий целевую ветку `main` и ветку автора PR.\n- Тесты запускаются не на изолированной ветке разработчика, а **на результате слияния**.\n- Если за время работы над PR в `main` были влиты изменения, конфликтующие логически, CI упадет ДО попадания кода в production.\n\nСтатус проверки отображается в Pull Request как зеленый маркер (Check Passed), без которого кнопка «Merge» блокируется политиками защиты веток (Branch Protection).",
    "step_by_step": "1. Создайте `.github/workflows/pr-check.yml`.\n2. Настройте триггер: `on.pull_request.types: [opened, synchronize, reopened]`.\n3. Добавьте запуск тестов и проверку форматирования кода `gofmt -l`.\n4. Убедитесь в корректном отображении статуса проверки в PR.",
    "code_blocks": [
      {
        "filename": ".github/workflows/pr-check.yml",
        "lang": "yaml",
        "code": "name: Pull Request Verification\n\non:\n  pull_request:\n    branches: [ main ]\n    types: [ opened, synchronize, reopened ]\n\njobs:\n  pr-validation:\n    name: Verify PR\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n          cache: true\n\n      - name: Check Code Formatting\n        run: |\n          UNFORMATTED=$(gofmt -l .)\n          if [ -n \"$UNFORMATTED\" ]; then\n            echo \"Error: Unformatted Go code detected:\"\n            echo \"$UNFORMATTED\"\n            exit 1\n          fi\n\n      - name: Run Tests\n        run: go test -v -race ./...",
        "note": "Workflow верификации PR"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\nfunc main() {\n\tfmt.Println(\"PR validation check passed cleanly!\")\n}",
        "note": "Форматированный Go код"
      }
    ],
    "under_the_hood": "Событие `synchronize` срабатывает каждый раз, когда разработчик делает новый `git push` в ветку открытого Pull Request, гарантируя повторную проверку всего тестового набора на свежих изменениях.",
    "pitfalls": "1. Настройка триггера только на `on: [push]`: при открытии PR из форка или ветки без прямого пуша в защищенную ветку проверки не запустятся.\n2. Пропуск шага проверки форматирования `gofmt`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в триггере `pull_request` GitHub Actions запускает тесты на ветке `refs/pull/N/merge`, а не на ветке `refs/pull/N/head`?»\n**Ответ:** Запуск на `head` тестирует только код разработчика в изоляции. Запуск на `merge` эмулирует реальное слияние ветки с текущим состоянием целевой ветки `main`. Если коллега только что смерджил в `main` изменение сигнатуры интерфейса, тесты на `head` прошли бы успешно, но проект сломался бы сразу после мерджа. Тестирование на `merge` предотвращает семантические конфликты слияния."
  },
  {
    "num": 8,
    "title": "Первый Pipeline: создание каталога .github/workflows и базовый CI",
    "task": "**Первый Pipeline**: Создай папку `.github/workflows/` и файл `ci.yml`. Настрой триггер: срабатывать при `push` в ветку `main`. Добавь шаг, который делает `actions/checkout` (скачивает код) и `actions/setup-go` (устанавливает нужную версию Go). Добавь команду `go test ./...`. Сделай пуш и проверь зеленую галочку в GitHub.",
    "theory": "Каждый CI/CD процесс в GitHub начинается с создания служебной директории `.github/workflows` в корне Git-репозитория.\n\nФайлы внутри этой директории парсятся движком GitHub Actions:\n- Имя файла может быть любым с расширением `.yml` или `.yaml`.\n- Поле `name:` задает отображаемое имя пайплайна в веб-интерфейсе GitHub.\n- Минимальный жизненный цикл пайплайна включает:\n  1. Выделение раннера (`runs-on`).\n  2. Загрузка исходников (`actions/checkout`).\n  3. Инициализация тулчейна Go (`actions/setup-go`).\n  4. Выполнение bash-команд тестирования и сборки (`run:`).",
    "step_by_step": "1. Создайте каталог `.github/workflows/`.\n2. Создайте файл `ci.yml`.\n3. Опишите задачу запуска тестов при пуше в `main`.\n4. Сделайте коммит и отправьте изменения в репозиторий.",
    "code_blocks": [
      {
        "filename": ".github/workflows/ci.yml",
        "lang": "yaml",
        "code": "name: First CI Pipeline\n\non:\n  push:\n    branches:\n      - main\n\njobs:\n  test-job:\n    name: Execute Go Tests\n    runs-on: ubuntu-latest\n    steps:\n      - name: Check out repository\n        uses: actions/checkout@v4\n\n      - name: Install Go\n        uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n\n      - name: Run Go Unit Tests\n        run: go test -v ./...",
        "note": "Первый рабочий пайплайн в репозитории"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\nfunc Greet(name string) string {\n\treturn fmt.Sprintf(\"Hello, %s!\", name)\n}\n\nfunc main() {\n\tfmt.Println(Greet(\"Gopher\"))\n}",
        "note": "Тестируемая функция"
      },
      {
        "filename": "main_test.go",
        "lang": "go",
        "code": "package main\n\nimport \"testing\"\n\nfunc TestGreet(t *testing.T) {\n\texpected := \"Hello, Gopher!\"\n\tif got := Greet(\"Gopher\"); got != expected {\n\t\tt.Errorf(\"Expected %s, got %s\", expected, got)\n\t}\n}",
        "note": "Модульный тест"
      }
    ],
    "under_the_hood": "GitHub получает webhook от git-сервера при пуше в ветку `main`, парсит YAML, валидирует синтаксис по схеме JSON Schema и помещает задачу в глобальную очередь задач билд-агентов.",
    "pitfalls": "1. Ошибки в отступах YAML (использование табуляций вместо 2 пробелов).\n2. Размещение папки `.github` не в корне репозитория.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какова минимальная структура файлов для запуска автоматического CI в репозитории GitHub?»\n**Ответ:** Достаточно создать один YAML-файл по пути `.github/workflows/<name>.yml`, содержащий валидное описание секций `on:` (триггер события), `jobs:` (перечень задач), `runs-on:` (операционная система раннера) и `steps:` (шаги выполнения с экшенами или командами `run`)."
  },
  {
    "num": 9,
    "title": "Кэширование в CI: ускорение скачивания модулей через кэш директории /go/pkg/mod",
    "task": "**[Кэширование в CI]**: Настрой кэширование папки `/go/pkg/mod` в CI-пайплайне, чтобы ускорить прохождение тестов.",
    "theory": "Каждый запуск задачи в GitHub Actions происходит на «чистой» виртуальной машине, где папка `$GOPATH/pkg/mod` изначально пуста. Если проект использует десятки внешних библиотек (gRPC, AWS SDK, Prometheus), их скачивание занимает 30–60 секунд на каждом билде.\n\nПаттерн кэширования:\nДиректория `$GOPATH/pkg/mod` сохраняется в облачном хранилище кэша GitHub после успешного билда.\nПри следующем запуске кэш скачивается и восстанавливается за **1–2 секунды**.\n\nВ современном экшене `actions/setup-go@v5` кэширование зависимостей включено по умолчанию через параметр `cache: true`, который автоматически вычисляет хэш от всех файлов `go.sum` в репозитории.",
    "step_by_step": "1. Включите параметр `cache: true` в шаге `actions/setup-go@v5`.\n2. Запустите пайплайн первый раз: модули скачаются и кэш запишется в хранилище.\n3. Запустите пайплайн повторно: в логах шага `setup-go` отобразится `Restored from cache`.",
    "code_blocks": [
      {
        "filename": ".github/workflows/cached-ci.yml",
        "lang": "yaml",
        "code": "name: Cached CI Pipeline\n\non: [push]\n\njobs:\n  build-and-test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      # Автоматическое кэширование go modules в setup-go v5\n      - name: Setup Go with Cache\n        uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n          cache: true\n          cache-dependency-path: go.sum\n\n      - name: Run Tests (Instant without downloading!)\n        run: go test -v ./...",
        "note": "Workflow с автоматическим кэшированием модулей"
      },
      {
        "filename": "go.mod",
        "lang": "text",
        "code": "module example.com/cachedapp\n\ngo 1.24\n\nrequire github.com/google/uuid v1.6.0\n",
        "note": "Файл манифеста модулей"
      }
    ],
    "under_the_hood": "`actions/setup-go` при флаге `cache: true` определяет путь `$GOPATH/pkg/mod` и формирует ключ вида `setup-go-Linux-x64-go-<version>-<hash(go.sum)>`. Если хэш `go.sum` совпадает, тарбол кэша распаковывается в файловую систему раннера до вызова `go test`.",
    "pitfalls": "1. Отсутствие файла `go.sum` в репозитории, из-за чего хэш ключа кэша не может быть рассчитан.\n2. Ручная очистка кэша: GitHub автоматически удаляет неиспользуемый кэш через 7 дней.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как работает ключ кэширования `hashFiles('go.sum')` в GitHub Actions и когда происходит инвалидация кэша?»\n**Ответ:** Функция `hashFiles('go.sum')` вычисляет криптографический хэш SHA-256 от содержимого файла `go.sum`. Пока список зависимостей и их точные версии не меняются, хэш остается неизменным, и раннер мгновенно переиспользует готовый кэш. Как только разработчик добавляет или обновляет библиотеку (`go get`), хэш `go.sum` изменяется, старый кэш инвалидируется, скачиваются новые модули и формируется новый снимок кэша."
  },
  {
    "num": 10,
    "title": "Продвинутое кэширование: actions/cache@v4 для go/pkg/mod и ~/.cache/go-build",
    "task": "Добавь **cache**: `actions/cache@v4` для `~/go/pkg/mod` и `~/.cache/go-build`. Ключ: `go-mod-${{ hashFiles('go.sum') }}`. Покажи ускорение CI с 5 минут до 1 минуты.",
    "theory": "Для максимального ускорения сборки тяжелых Go-приложений кэширования одних только модулей недостаточно.\n\nВ Go существуют два независимых кэша:\n1. **Module Cache (`~/go/pkg/mod`):** исходные коды скачанных сторонних библиотек.\n2. **Build Cache (`~/.cache/go-build` в Linux):** скомпилированные объектные архивы (`.a` файлы) стандартной библиотеки и пакетов приложения.\n\nЕсли кэшировать **оба каталога** с помощью универсального экшена `actions/cache@v4`:\n- Не нужно заново скачивать библиотеки по сети.\n- Не нужно заново компилировать неизмененные пакеты (Go переиспользует объектные файлы из `GOCACHE`).\nВремя полного цикла CI сокращается **с 45 секунд до 4–6 секунд**!",
    "step_by_step": "1. Опишите шаг `actions/cache@v4` с путями `~/go/pkg/mod` и `~/.cache/go-build`.\n2. Задайте составной ключ на основе ОС и хэша `go.sum`.\n3. Добавьте префиксы восстановления `restore-keys` для частичного переиспользования кэша при обновлении зависимостей.",
    "code_blocks": [
      {
        "filename": ".github/workflows/advanced-cache.yml",
        "lang": "yaml",
        "code": "name: Advanced Go Caching\n\non: [push, pull_request]\n\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n          cache: false # Отключаем базовый кэш, настраиваем глубокий кастомный\n\n      - name: Cache Go Modules and Build Cache\n        uses: actions/cache@v4\n        with:\n          path: |\n            ~/go/pkg/mod\n            ~/.cache/go-build\n          key: ${{ runner.os }}-go-cache-${{ hashFiles('**/go.sum') }}-${{ hashFiles('**/*.go') }}\n          restore-keys: |\n            ${{ runner.os }}-go-cache-${{ hashFiles('**/go.sum') }}-\n            ${{ runner.os }}-go-cache-\n\n      - name: Run Tests with Warm Cache\n        run: go test -v -race ./...",
        "note": "Двухуровневое кэширование модулей и GOCACHE"
      }
    ],
    "under_the_hood": "Благодаря параметру `restore-keys`, если точного совпадения по ключу не найдено (например, изменился один `.go` файл), GitHub Actions скачивает самый свежий предыдущий кэш по префиксу. Компилятор Go считывает заголовки из `~/.cache/go-build` и компилирует только дельту измененного кода.",
    "pitfalls": "1. Превышение общего лимита кэша репозитория (10 ГБ на репозиторий в GitHub Actions).\n2. Кэширование папки `bin/` или временных файлов тестов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем кэшировать директорию `~/.cache/go-build` в CI, если уже настроен кэш `~/go/pkg/mod`?»\n**Ответ:** Кэш `pkg/mod` содержит только исходный код зависимостей. При запуске `go test` компилятор Go все равно вынужден компилировать эти исходники в машинный код. Директория `~/.cache/go-build` хранит уже скомпилированные бинарные пакеты. Кэширование обеих папок исключает и сетевую загрузку, и этап повторной компиляции сторонних библиотек, ускоряя CI в разы."
  },
  {
    "num": 11,
    "title": "Матричное тестирование версий Go: проверка совместимости 1.22, 1.23 и 1.24",
    "task": "Настройте матрицу версий Go (1.21, 1.22, 1.23) для проверки совместимости.",
    "theory": "При выпуске корпоративных библиотек и микросервисов необходимо проверять обратную совместимость с предыдущими стабильными версиями языка.\n\nСогласно политике поддержки команды Go (Go Release Policy), одновременно поддерживаются **две последние мажорные версии** (например, 1.23 и 1.24).\n\nМатричное тестирование версий в CI:\n- Гарантирует, что в код случайно не попали фичи из более нового Go (например, изменения в цикле `for` с переменными в 1.22 или новые методы стандартной библиотеки 1.24), которые сломают сборку у клиентов на предыдущей версии.\n- Позволяет заранее тестировать код на предварительных версиях (Release Candidates / Beta).",
    "step_by_step": "1. Создайте `.github/workflows/versions-matrix.yml`.\n2. Настройте матрицу `go-version: ['1.22.x', '1.23.x', '1.24.x']`.\n3. Запустите тестирование и убедитесь в параллельном исполнении.",
    "code_blocks": [
      {
        "filename": ".github/workflows/versions-matrix.yml",
        "lang": "yaml",
        "code": "name: Go Versions Compatibility Matrix\n\non:\n  push:\n    branches: [ main ]\n  pull_request:\n\njobs:\n  test-compatibility:\n    name: Compatibility Go ${{ matrix.go-version }}\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        go-version: ['1.22.x', '1.23.x', '1.24.x']\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-go@v5\n        with:\n          go-version: ${{ matrix.go-version }}\n          cache: true\n      - name: Run Tests\n        run: go test -v ./...",
        "note": "Матрица версий Go"
      },
      {
        "filename": "compat.go",
        "lang": "go",
        "code": "package main\n\n// Multiply выполняет умножение\nfunc Multiply(a, b int) int {\n\treturn a * b\n}",
        "note": "Совместимый код"
      },
      {
        "filename": "compat_test.go",
        "lang": "go",
        "code": "package main\n\nimport \"testing\"\n\nfunc TestMultiply(t *testing.T) {\n\tif got := Multiply(4, 5); got != 20 {\n\t\tt.Fatalf(\"Expected 20, got %d\", got)\n\t}\n}",
        "note": "Тест"
      }
    ],
    "under_the_hood": "Спецификатор `1.23.x` инструктирует `setup-go` автоматически скачивать самый последний минорный релиз безопасности (например, `1.23.6`) из официального реестра релизов Go, гарантируя тестирование на стабильных патчах.",
    "pitfalls": "1. Использование директивы `go 1.24` в файле `go.mod`: если проект требует Go 1.24, компилятор Go 1.22 откажется собирать проект с ошибкой `requires go >= 1.24`. Для обратной совместимости в `go.mod` указывается минимальная поддерживаемая версия.\n2. Неоправданно широкая матрица старых неподдерживаемых версий.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какова официальная политика поддержки версий языка Go компанией Google и сообществом?»\n**Ответ:** Официально поддерживаются две последние мажорные версии (N и N-1, например 1.24 и 1.23). При обнаружении критических уязвимостей безопасности или багов патчи (минорные версии N.x) выпускаются только для этих двух версий. Поддержка более старых версий (1.21 и ниже) прекращается. Поэтому матричное тестирование в CI Enterprise-библиотек обычно ограничивают версиями `[N-1, N]`."
  },
  {
    "num": 12,
    "title": "Семантическое версионирование (Semantic Versioning) и автоматический релиз",
    "task": "Добавь **semantic versioning**: `semantic-release` или `go-semantic-release`. Автоматический `git tag` + GitHub Release на merge в `main`. Docker tag: `v1.2.3`, `v1.2`, `v1`. Покажи automated changelog.",
    "theory": "Семантическое версионирование (**SemVer — Semantic Versioning 2.0.0**) кодирует изменения в формате:\n`vMAJOR.MINOR.PATCH`\n- `MAJOR`: несовместимые изменения API (Breaking Changes).\n- `MINOR`: обратимо совместимая новая функциональность.\n- `PATCH`: обратимо совместимые исправления ошибок (Bug Fixes).\n\nСпецификация **Conventional Commits**:\n- `fix: fix database timeout` -> увеличивает `PATCH` (1.0.1).\n- `feat: add redis cache layer` -> увеличивает `MINOR` (1.1.0).\n- `feat!: change auth payload` (или `BREAKING CHANGE:`) -> увеличивает `MAJOR` (2.0.0).\n\nУтилиты автоматизации (`semantic-release`, `go-semantic-release`) парсят историю коммитов при слиянии в `main`, вычисляют следующий номер версии, ставят Git-тег, генерируют `CHANGELOG.md` и создают официальный GitHub Release.",
    "step_by_step": "1. Настройте workflow `.github/workflows/release.yml` с триггером на пуш в `main`.\n2. Подключите экшен `go-semantic-release/action@v1`.\n3. Передайте секретный токен `GITHUB_TOKEN` с правами на запись контента (`permissions: contents: write`).\n4. Протестируйте автоматическое создание релиза при коммите с префиксом `feat:`.",
    "code_blocks": [
      {
        "filename": ".github/workflows/release.yml",
        "lang": "yaml",
        "code": "name: Automated Semantic Release\n\non:\n  push:\n    branches:\n      - main\n\npermissions:\n  contents: write\n  issues: write\n  pull-requests: write\n\njobs:\n  release:\n    name: Semantic Release\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout Code\n        uses: actions/checkout@v4\n        with:\n          fetch-depth: 0 # Полная история для анализа коммитов\n\n      - name: Run Semantic Release\n        uses: go-semantic-release/action@v1\n        with:\n          github-token: ${{ secrets.GITHUB_TOKEN }}\n          changelog-generator: default",
        "note": "Workflow автоматического SemVer релиза"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Пример коммита по стандарту Conventional Commits\ngit commit -m \"feat(auth): add JWT token refresh endpoint\"\ngit push origin main\n# CI автоматически проанализирует коммит, создаст тег v1.1.0 и опубликует релиз!"
      }
    ],
    "under_the_hood": "Экшен анализирует коммиты от последнего существующего тега до текущего `HEAD`. Парсер сопоставляет префиксы регулярными выражениями. Затем через GitHub REST API (`POST /repos/{owner}/{repo}/releases`) создается релиз с отрендеренным markdown-списком изменений.",
    "pitfalls": "1. Использование `fetch-depth: 1` (по умолчанию в checkout): экшен не увидит историю предыдущих коммитов и тегов. Обязательно указывать `fetch-depth: 0`.\n2. Недостаточные права токена: требуется `permissions: contents: write`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в модульной системе Go (Go Modules) мажорная версия `v2+` требует изменения пути импорта модуля (Semantic Import Versioning)?»\n**Ответ:** Согласно правилу Semantic Import Versioning в Go, если модуль меняет мажорную версию (`v2.0.0`), он считается принципиально другим пакетом с несовместимым API. Чтобы предотвратить поломку зависимых проектов, Go требует добавить суффикс версии в `go.mod` и все пути импорта: `module github.com/user/repo/v2`. Это позволяет двум разным библиотекам в одном проекте бесконфликтно использовать одновременно версии `v1` и `v2` одной и той же зависимости."
  },
  {
    "num": 13,
    "title": "Контроль целостности модулей: go mod verify и go mod tidy -diff в CI",
    "task": "Добавьте `go mod verify` и `go mod tidy -diff` для проверки, что go.mod консистентен.",
    "theory": "Безопасность и чистота зависимостей — ключевой аспект CI/CD пайплайна Go:\n\n1. **`go mod verify`:**\n   Проверяет, что локально скачанные модули в `$GOPATH/pkg/mod` не были скомпрометированы или повреждены. Утилита сравнивает хэш-суммы всех файлов каждого модуля с криптографическими контрольными суммами, зафиксированными в файле `go.sum`. Защищает от атак подмены пакетов (Supply Chain Attacks).\n\n2. **`go mod tidy -diff` (доступно в Go 1.23+):**\n   Проверяет, что файлы `go.mod` и `go.sum` являются абсолютно актуальными и чистыми:\n   - Нет забытых неиспользуемых библиотек.\n   - Нет отсутствующих зависимостей.\n   Флаг `-diff` возвращает ненулевой код выхода, если `go.mod` требует форматирования или очистки, не изменяя файлы на диске.",
    "step_by_step": "1. Создайте `.github/workflows/modules-check.yml`.\n2. Добавьте шаг проверки целостности хэшей `go mod verify`.\n3. Добавьте шаг проверки чистоты зависимостей `go mod tidy -diff` (или проверку `git diff --exit-code`).\n4. Убедитесь, что пайплайн блокирует коммиты с неактуальным `go.mod`.",
    "code_blocks": [
      {
        "filename": ".github/workflows/modules-check.yml",
        "lang": "yaml",
        "code": "name: Go Modules Integrity Check\n\non: [push, pull_request]\n\njobs:\n  verify-modules:\n    name: Verify go.mod & go.sum\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n          cache: true\n\n      - name: Verify module cache integrity\n        run: go mod verify\n\n      - name: Ensure go.mod and go.sum are tidy\n        run: |\n          go mod tidy\n          git diff --exit-code go.mod go.sum || (echo \"Error: go.mod or go.sum is not tidy. Run 'go mod tidy' locally!\" && exit 1)",
        "note": "Workflow строгой проверки зависимостей"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\nfunc main() {\n\tfmt.Println(\"Modules integrity guaranteed!\")\n}",
        "note": "Минимальный микросервис"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Локальная проверка целостности\ngo mod tidy\ngo mod verify\n# Вывод: all modules verified"
      }
    ],
    "under_the_hood": "Файл `go.sum` содержит строки вида `<module> <version> h1:<hash>`. Префикс `h1:` обозначает алгоритм хэширования Hash1 (SHA-256 по всем файлам модуля в алфавитном порядке). `go mod verify` пересчитывает SHA-256 каждого распакованного каталога и сверяет с контрольной записью.",
    "pitfalls": "1. Ручное редактирование файла `go.sum`.\n2. Коммит изменений кода без предварительного выполнения `go mod tidy`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем нужна проверка `git diff --exit-code go.mod go.sum` после выполнения `go mod tidy` в CI?»\n**Ответ:** Если разработчик удалил вызов внешней библиотеки из кода, но забыл выполнить `go mod tidy` перед коммитом, неиспользуемая библиотека останется в `go.mod`. В результате Dockerfile и CI продолжат скачивать ненужную библиотеку, раздувая контекст и создавая лишние ложные срабатывания сканеров уязвимостей (CVE). Проверка `git diff --exit-code` падает с ошибкой, если на диске появились незакоммиченные изменения после `tidy`, заставляя разработчика поддерживать идеальную чистоту файла зависимостей."
  },
  {
    "num": 14,
    "title": "Оптимизация времени CI: раздельное кэширование ~/go/pkg/mod и ~/.cache/go-build",
    "task": "**Кэширование в CI**: Скачивание модулей (`go mod download`) при каждом запуске пайплайна тратит время. Добавь шаг кэширования директорий `~/.cache/go-build` и `~/go/pkg/mod` (в GitHub Actions у `setup-go` есть встроенный флаг `cache: true`). Замерь, на сколько секунд ускорилась сборка.",
    "theory": "При проектировании высокопроизводительных пайплайнов в больших монорепозиториях время прохождения проверок напрямую влияет на скорость релиза (DORA метрика Time to Restore / Lead Time for Changes).\n\nСкачивание модулей (`go mod download`) и компиляция занимают значительную часть времени.\nИспользование связки двух каталогов кэша:\n- `~/go/pkg/mod`\n- `~/.cache/go-build`\n\nс раздельными ключами кэширования:\n1. Кэш модулей привязывается строго к хэшу файла `go.sum`:\n   `key: ${{ runner.os }}-go-mod-${{ hashFiles('**/go.sum') }}`\n2. Кэш компиляции привязывается к хэшу `go.sum` и коммиту Git, с fallback на предыдущий кэш:\n   `restore-keys: ${{ runner.os }}-go-build-`\n\nЭто позволяет добиться максимального коэффициента попадания в кэш (Cache Hit Ratio > 95%).",
    "step_by_step": "1. Опишите независимые шаги кэширования для модулей и для build cache.\n2. Проверьте время первого «холодного» запуска.\n3. Проверьте время повторного «горячего» запуска пайплайна.",
    "code_blocks": [
      {
        "filename": ".github/workflows/optimized-cache.yml",
        "lang": "yaml",
        "code": "name: Production Optimized Cache\n\non: [push, pull_request]\n\njobs:\n  fast-ci:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n          cache: false\n\n      # 1. Кэш Go Modules (инвалидируется ТОЛЬКО при изменении go.sum)\n      - name: Cache Go Modules\n        uses: actions/cache@v4\n        with:\n          path: ~/go/pkg/mod\n          key: ${{ runner.os }}-gomod-${{ hashFiles('**/go.sum') }}\n          restore-keys: |\n            ${{ runner.os }}-gomod-\n\n      # 2. Кэш компилятора Go Build Cache\n      - name: Cache Go Build\n        uses: actions/cache@v4\n        with:\n          path: ~/.cache/go-build\n          key: ${{ runner.os }}-gobuild-${{ github.sha }}\n          restore-keys: |\n            ${{ runner.os }}-gobuild-\n\n      - name: Fast Test Run\n        run: go test -v ./...",
        "note": "Раздельное высокоэффективное кэширование"
      }
    ],
    "under_the_hood": "Разделение кэшей изолирует сетевой кэш от компиляционного. Если изменился один `.go` файл, кэш `gomod` совпадает на 100% (мгновенное попадание), а кэш `gobuild` восстанавливается по префиксу `restore-keys`, перекомпилируя только дельту измененного пакета.",
    "pitfalls": "1. Кэширование всей директории `~/.cache` целиком, что может захватить нерелевантные временные файлы ОС.\n2. Неверный путь к кэшу компилятора на macOS (`~/Library/Caches/go-build`) или Windows (`%LocalAppData%\\go-build`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Где физически располагаются директории `GOPATH` и `GOCACHE` на операционных системах Linux, macOS и Windows по умолчанию?»\n**Ответ:** По умолчанию:\n- `GOPATH`: `~/go` на Linux и macOS; `%USERPROFILE%\\go` на Windows. Модули лежат в `$GOPATH/pkg/mod`.\n- `GOCACHE`: `~/.cache/go-build` на Linux; `~/Library/Caches/go-build` на macOS; `%LocalAppData%\\go-build` на Windows. Точный путь в любой ОС можно узнать командой `go env GOCACHE`."
  },
  {
    "num": 15,
    "title": "Сборка и публикация Docker-образа в Docker Hub через Secrets",
    "task": "**[Сборка и пуш образа]**: Добавь шаг в пайплайн: логин в Docker Hub (через secrets), сборка образа с тегом текущего коммита (SHA) и пуш в registry.",
    "theory": "Публикация контейнерных образов в публичный или приватный реестр (Docker Hub, GHCR, Harbor) — стандартный этап сборки артефактов в Continuous Integration. \n\nДля аутентификации в Docker Hub категорически запрещено использовать пароль учетной записи. Вместо этого генерируется Personal Access Token (PAT) с ограниченными правами (Read/Write) и сохраняется в зашифрованных секретах репозитория (`DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`).\n\nОфициальный набор экшенов Docker (`docker/login-action`, `docker/setup-buildx-action`, `docker/build-push-action`) опирается на BuildKit, предоставляя аппаратную изоляцию, эффективное кэширование слоев и поддержку параллельной сборки. Тегирование образов по SHA коммита (`${{ github.sha }}`) обеспечивает полную воспроизводимость и неизменяемость (immutability) продакшн-образов.",
    "step_by_step": "1. Создайте Personal Access Token в настройках профиля Docker Hub (Account Settings -> Security -> New Access Token).\n2. Добавьте секреты в GitHub: Settings -> Secrets and variables -> Actions -> Repository secrets: `DOCKERHUB_USERNAME` и `DOCKERHUB_TOKEN`.\n3. Создайте workflow `.github/workflows/docker-publish.yml`, настроив триггер на `push` в ветку `main`.\n4. Сконфигурируйте шаги: Checkout, Login to Docker Hub, Setup Buildx, Build and Push.\n5. Запустите pipeline и убедитесь в успешной публикации образа в реестр.",
    "code_blocks": [
      {
        "filename": ".github/workflows/docker-publish.yml",
        "lang": "yaml",
        "code": "name: Docker Build & Push\n\non:\n  push:\n    branches: [ main ]\n\njobs:\n  docker:\n    name: Build and Push Docker Image\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout repository\n        uses: actions/checkout@v4\n\n      - name: Set up Docker Buildx\n        uses: docker/setup-buildx-action@v3\n\n      - name: Log in to Docker Hub\n        uses: docker/login-action@v3\n        with:\n          username: ${{ secrets.DOCKERHUB_USERNAME }}\n          password: ${{ secrets.DOCKERHUB_TOKEN }}\n\n      - name: Build and push image\n        uses: docker/build-push-action@v5\n        with:\n          context: .\n          file: ./Dockerfile\n          push: true\n          tags: |\n            ${{ secrets.DOCKERHUB_USERNAME }}/microservice:latest\n            ${{ secrets.DOCKERHUB_USERNAME }}/microservice:${{ github.sha }}"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\tport := os.Getenv(\"PORT\")\n\tif port == \"\" {\n\t\tport = \"8080\"\n\t}\n\n\thttp.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"OK\"))\n\t})\n\n\tfmt.Printf(\"Сервис запущен на порту %s\\n\", port)\n\tif err := http.ListenAndServe(\":\"+port, nil); err != nil {\n\t\tfmt.Printf(\"Ошибка сервера: %v\\n\", err)\n\t}\n}"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# syntax=docker/dockerfile:1\nFROM golang:1.24-alpine AS builder\nWORKDIR /app\nCOPY go.mod go.sum* ./\nRUN go mod download\nCOPY . .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-s -w\" -o /service .\n\nFROM alpine:3.21\nRUN apk --no-cache add ca-certificates tzdata\nUSER 65534:65534\nCOPY --from=builder /service /service\nEXPOSE 8080\nENTRYPOINT [\"/service\"]"
      }
    ],
    "under_the_hood": "При вызове `docker/login-action` экшен создает временную конфигурацию `~/.docker/config.json`, в которой сохраняется закодированный базовый токен аутентификации для домена `https://index.docker.io/v1/`. В конце джобы (post-action step) этот временный конфиг автоматически очищается, предотвращая утечку учетных данных на раннере.\n\nBuildKit взаимодействует с Docker Registry API v2: перед отправкой слоев демон запрашивает манифест целевого тега и отправляет только отсутствующие блобы (layer diffs). Использование хеша коммита исключает проблемы с перезаписью тега `latest` (tag drifting).",
    "pitfalls": "1. Использование пароля учетной записи вместо Personal Access Token: компрометация секрета приведет к захвату всего аккаунта Docker Hub.\n2. Отправка образов только с тегом `:latest`: делает невозможным откат (rollback) на предыдущую версию в Kubernetes при сбое нового релиза.\n3. Хранение секретов в открытом виде в аргументах сборки `ARG`: они попадают в историю слоев образа (`docker history`).",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в production Kubernetes-манифестах запрещено использовать тег `:latest`, и как CI/CD должен формировать теги образов?\n**Ответ:** Тег `:latest` мутабелен: под одним и тем же тегом в реестре сегодня лежит версия A, а завтра — версия B. Это нарушает принцип детерминизма и воспроизводимости деплоя. Kubernetes при `imagePullPolicy: IfNotPresent` вообще не скачает новый образ, если на ноде уже есть старый `:latest`. В CI/CD правильным подходом является тегирование по неизменяемому SHA коммита Git (`sha-XXXXX`) или семантическому тегу релиза (`v1.2.3`), что гарантирует однозначное соответствие запущенного в проде контейнера исходному коду."
  },
  {
    "num": 16,
    "title": "Многоконтурный деплой: dev, staging, production с ручным аппрувом",
    "task": "Добавь **multi-environment deployment**: `dev` (auto on PR merge), `staging` (auto on tag `v*-rc*`), `production` (manual approval). GitHub Environments + protection rules. Покажи promotion pipeline.",
    "theory": "Концепция многоконтурного развертывания (Multi-Environment Deployment) разграничивает риски при доставке кода в production:\n1. **Dev (Development):** Автоматический деплой при слиянии Pull Request в ветку `develop` или `main`. Служит для интеграционного тестирования разработчиками.\n2. **Staging:** Автоматический деплой при создании релиз-кандидата (тег `v*-rc*`). Окружение, идентичное production (pre-prod), где проводятся нагрузочные, E2E и регрессионные тесты.\n3. **Production:** Развертывание только стабильных релизов (теги `v[0-9]+.[0-9]+.[0-9]+`). В enterprise-системах требует обязательного прохождения Approval Gate (ручного подтверждения техлидом или релиз-инженером) через GitHub Environments Protection Rules.\n\nВ GitHub Actions механизм Environments позволяет настраивать Required Reviewers, тайм-ауты ожидания (wait timers) и изолированные секреты, специфичные для каждого окружения.",
    "step_by_step": "1. В репозитории GitHub откройте Settings -> Environments и создайте окружения `dev`, `staging` и `production`.\n2. Для `production` настройте `Required reviewers`, выбрав ответственных инженеров.\n3. Создайте файл `.github/workflows/deploy.yml`.\n4. Сконфигурируйте джобу `deploy-dev` с условием `github.ref == 'refs/heads/main'`.\n5. Сконфигурируйте джобу `deploy-staging` с условием `startsWith(github.ref, 'refs/tags/v') && contains(github.ref, '-rc')`.\n6. Сконфигурируйте джобу `deploy-prod` с привязкой `environment: production` и условием `startsWith(github.ref, 'refs/tags/v') && !contains(github.ref, '-rc')`.",
    "code_blocks": [
      {
        "filename": ".github/workflows/deploy.yml",
        "lang": "yaml",
        "code": "name: Multi-Environment Deployment\n\non:\n  push:\n    branches: [ main ]\n    tags:\n      - 'v*.*.*'\n\njobs:\n  build:\n    name: Build and Artifact\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - name: Setup Go\n        uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n      - name: Build Binary\n        run: CGO_ENABLED=0 go build -ldflags=\"-s -w\" -o service .\n      - name: Upload Binary\n        uses: actions/upload-artifact@v4\n        with:\n          name: service-binary\n          path: service\n\n  deploy-dev:\n    name: Deploy to Dev\n    needs: build\n    if: github.ref == 'refs/heads/main'\n    runs-on: ubuntu-latest\n    environment: dev\n    steps:\n      - uses: actions/download-artifact@v4\n        with:\n          name: service-binary\n      - run: echo \"Deploying commit ${{ github.sha }} to DEV environment\"\n\n  deploy-staging:\n    name: Deploy to Staging\n    needs: build\n    if: startsWith(github.ref, 'refs/tags/v') && contains(github.ref, '-rc')\n    runs-on: ubuntu-latest\n    environment: staging\n    steps:\n      - uses: actions/download-artifact@v4\n        with:\n          name: service-binary\n      - run: echo \"Deploying release candidate ${{ github.ref_name }} to STAGING\"\n\n  deploy-prod:\n    name: Deploy to Production\n    needs: build\n    if: startsWith(github.ref, 'refs/tags/v') && !contains(github.ref, '-rc')\n    runs-on: ubuntu-latest\n    environment:\n      name: production\n      url: https://api.prod.example.com\n    steps:\n      - uses: actions/download-artifact@v4\n        with:\n          name: service-binary\n      - run: echo \"Deploying official release ${{ github.ref_name }} to PRODUCTION\" "
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n)\n\nvar version = \"dev\"\n\nfunc main() {\n\tenv := os.Getenv(\"APP_ENV\")\n\tif env == \"\" {\n\t\tenv = \"local\"\n\t}\n\tfmt.Printf(\"Запуск сервиса [Версия: %s, Контур: %s]\\n\", version, env)\n}"
      }
    ],
    "under_the_hood": "Когда джоба привязана к `environment: production`, GitHub Actions приостанавливает выполнение пайплайна в статусе `Waiting`. На почту и в UI репозитория отправляется нотификация ревьюерам. \n\nПри одобрении раннер получает доступ к секретам, привязанным исключительно к `production` (например, боевые ключи доступа к Kubernetes или Cloud KMS). Если ревьюер отклоняет запуск или истекает таймаут ожидания, джоба переходит в статус `Failed`, а боевой контур остается нетронутым.",
    "pitfalls": "1. Использование одинаковых секретов базы данных для dev, staging и prod: ошибка в скрипте миграций на dev затрет боевые данные.\n2. Отсутствие валидации зависимостей `needs: [build]`: деплой запускается параллельно со сборкой или тестами до подтверждения их успешности.\n3. Отсутствие защиты ветки `main`: разработчик может запушить коммит напрямую в обход PR и запустить автоматический деплой.",
    "bigtech_interview": "**Вопрос с собеседования:** Как предотвратить ситуацию, когда сборка с тегом v1.2.0 попадает в Production без предварительного тестирования на Staging?\n**Ответ:** Существует два паттерна:\n1. **Паттерн GitFlow/Release-branches:** Релиз-кандидат `v1.2.0-rc1` сначала собирается и деплоится на Staging. Только после успешных QA-тестов ветка релиза мерджится в `main`, где формируется финальный тег `v1.2.0`.\n2. **GitOps / Metadata Promotion:** CI собирает неизменяемый Docker-образ один раз. Деплой на Staging обновляет манифест в GitOps-репозитории в ветке `staging`. После валидации CI-пайплайн или бот копирует SHA образа в манифест `prod`, создавая Pull Request на релиз-инженера."
  },
  {
    "num": 17,
    "title": "Интеграция golangci-lint-action со строгим контролем линтеров",
    "task": "Используйте `golangci-lint-action` для запуска всех линтеров (staticcheck, errcheck, gosec, revive, etc.) с одной командой.",
    "theory": "Статический анализ — первая линия обороны качества кода в Go. Официальный `golangci-lint-action` интегрирует мета-линтер `golangci-lint` непосредственно в GitHub Actions, автоматически кэшируя кэши линтеров и бинарные деревья модулей.\n\nДля поддержания enterprise-стандартов в файле `.golangci.yml` активируются критические линтеры:\n- `staticcheck`: глубокий семантический анализ логики и устаревших API.\n- `errcheck`: проверка необработанных возвращаемых ошибок.\n- `gosec`: поиск уязвимостей безопасности (SQL injection, слабые алгоритмы криптографии, SSRF).\n- `revive`: быстрый расширяемый линтер стилистики Go.\n- `ineffassign`: детекция неэффективных или перезаписываемых присваиваний.\n\nФлаг `--issues-exit-code=1` гарантирует падение пайплайна при наличии малейших предупреждений, предотвращая мердж «грязного» кода.",
    "step_by_step": "1. Создайте в корне репозитория конфигурацию `.golangci.yml`.\n2. Включите необходимые линтеры в секции `linters.enable`.\n3. Создайте `.github/workflows/lint.yml` с использованием `golangci/golangci-lint-action@v6`.\n4. Задайте аргумент `args: --timeout=5m --issues-exit-code=1`.\n5. Протестируйте работу на коде с намеренной ошибкой (например, неиспользованное возвращаемое значение `error`).",
    "code_blocks": [
      {
        "filename": ".golangci.yml",
        "lang": "yaml",
        "code": "run:\n  timeout: 5m\n  issues-exit-code: 1\n  tests: true\n\nlinters:\n  disable-all: true\n  enable:\n    - errcheck\n    - gosimple\n    - govet\n    - ineffassign\n    - staticcheck\n    - typecheck\n    - unused\n    - gosec\n    - revive\n\nlinters-settings:\n  errcheck:\n    check-type-assertions: true\n    check-blank: true\n  gosec:\n    severity: medium\n    confidence: medium\n\nissues:\n  max-issues-per-linter: 0\n  max-same-issues: 0"
      },
      {
        "filename": ".github/workflows/lint.yml",
        "lang": "yaml",
        "code": "name: Static Code Analysis\n\non:\n  push:\n    branches: [ main ]\n  pull_request:\n    branches: [ main ]\n\njobs:\n  golangci:\n    name: Lint Go Code\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - name: Setup Go\n        uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n          cache: false\n\n      - name: Run golangci-lint\n        uses: golangci/golangci-lint-action@v6\n        with:\n          version: v1.64.5\n          args: --timeout=5m --issues-exit-code=1"
      },
      {
        "filename": "calc.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n)\n\n// Divide делит a на b, возвращая ошибку при делении на ноль.\nfunc Divide(a, b float64) (float64, error) {\n\tif b == 0 {\n\t\treturn 0, errors.New(\"деление на ноль недопустимо\")\n\t}\n\treturn a / b, nil\n}\n\nfunc main() {\n\tres, err := Divide(10, 2)\n\tif err != nil {\n\t\tfmt.Printf(\"Ошибка: %v\\n\", err)\n\t\treturn\n\t}\n\tfmt.Printf(\"Результат: %.2f\\n\", res)\n}"
      }
    ],
    "under_the_hood": "`golangci-lint-action` сохраняет кэш в GitHub Actions Cache (`~/.cache/golangci-lint`). Он кэширует:\n1. Результаты парсинга AST (Abstract Syntax Tree) пакетов.\n2. Type-checking информацию, сгенерированную `go/types`.\n3. Анализ SSA (Static Single Assignment) графов.\n\nБлагодаря этому инкрементальный запуск линтера на PR занимает 3-5 секунд вместо 1-2 минут при холодном старте. Ключ кэша строится на базе версии Go, версии `golangci-lint` и хеша файла `go.sum`.",
    "pitfalls": "1. Дублирование кэширования: если включить `cache: true` в `actions/setup-go` и одновременно кэширование в `golangci-lint-action`, возможны конфликты путей и замедление работы.\n2. Использование плавающего тега `@latest` для `golangci-lint-action`: минорный релиз линтера с новыми правилами может неожиданно сломать пайплайн во всех ветках команды.\n3. Игнорирование проверки `check-type-assertions`: паника при приведении `val.(string)` в runtime.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему на уровне CI важно разделять шаги линтинга (`golangci-lint`) и запуска тестов (`go test -race`), а не запускать их одной строкой `make test-all`?\n**Ответ:** Разделение на независимые джобы в пайплайне дает три преимущества:\n1. **Параллелизм:** Линтинг и юнит-тесты выполняются параллельно на разных раннерах, сокращая суммарный Feedback Loop для инженера до минимума.\n2. **Локализация ошибок:** На PR в UI GitHub сразу видно, упала ли бизнес-логика (тесты) или стиль/безопасность (линтер).\n3. **Fail-Fast политика:** Линтер часто отрабатывает быстрее тестов. При грубой ошибке (синтаксис, неошибочное присваивание) PR реджектится без лишней траты времени раннеров на тяжелые интеграционные тесты."
  },
  {
    "num": 18,
    "title": "Публикация в GitHub Container Registry (GHCR) с тегом SHA",
    "task": "Добавь **Docker build and push**: `docker/login-action` → `docker/build-push-action`. Tag: `ghcr.io/${{ github.repository }}:${{ github.sha }}`, `ghcr.io/${{ github.repository }}:latest`. Push to GitHub Container Registry.",
    "theory": "GitHub Container Registry (GHCR) — встроенное в инфраструктуру GitHub объектное хранилище OCI-образов (`ghcr.io`). \n\nПреимущества использования GHCR по сравнению со сторонними реестрами:\n- Бесшовная аутентификация через встроенный одноразовый токен `${{ secrets.GITHUB_TOKEN }}` без необходимости генерировать и обновлять внешние пароли.\n- Высокая пропускная способность при скачивании раннерами GitHub Actions (внутри единого датацентра Azure/AWS).\n- Привязка доступа к правам репозитория или организации через `permissions: packages: write`.\n\nДля надежного отслеживания образ тегируется двумя значениями:\n1. `ghcr.io/owner/repo:latest` (для быстрого локального запуска).\n2. `ghcr.io/owner/repo:${{ github.sha }}` (детерминированный OCI-образ для развертывания).",
    "step_by_step": "1. В workflow предоставьте джобе права на запись пакетов: `permissions: packages: write, contents: read`.\n2. Добавьте шаг авторизации в реестре `ghcr.io` с логином `${{ github.actor }}` и паролем `${{ secrets.GITHUB_TOKEN }}`.\n3. Используйте экшен `docker/metadata-action` для автоматической генерации семантических тегов и лейблов OCI.\n4. Вызовите `docker/build-push-action`, указав сгенерированные теги и целевую платформу `linux/amd64`.",
    "code_blocks": [
      {
        "filename": ".github/workflows/ghcr-publish.yml",
        "lang": "yaml",
        "code": "name: Publish OCI Image to GHCR\n\non:\n  push:\n    branches: [ main ]\n\npermissions:\n  contents: read\n  packages: write\n\njobs:\n  build-and-push:\n    name: Build & Push to GHCR\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout source\n        uses: actions/checkout@v4\n\n      - name: Set up Docker Buildx\n        uses: docker/setup-buildx-action@v3\n\n      - name: Log in to GHCR\n        uses: docker/login-action@v3\n        with:\n          registry: ghcr.io\n          username: ${{ github.actor }}\n          password: ${{ secrets.GITHUB_TOKEN }}\n\n      - name: Extract metadata (tags, labels)\n        id: meta\n        uses: docker/metadata-action@v5\n        with:\n          images: ghcr.io/${{ github.repository }}\n          tags: |\n            type=raw,value=latest\n            type=sha,format=long\n\n      - name: Build and push\n        uses: docker/build-push-action@v5\n        with:\n          context: .\n          push: true\n          tags: ${{ steps.meta.outputs.tags }}\n          labels: ${{ steps.meta.outputs.labels }}"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/version\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\t_, _ = w.Write([]byte(`{\"service\":\"gateway\",\"status\":\"ready\"}`))\n\t})\n\n\tfmt.Println(\"API шлюз запущен на :8080\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "При включении `packages: write` GitHub выдает временный JWT-токен в переменную `GITHUB_TOKEN`. Экшен `docker/login-action` обращается к `https://ghcr.io/v2/token`, отправляя Basic Auth. В ответ GHCR возвращает bearer token для авторизации push-запросов.\n\nСтандарт OCI Image Index позволяет связывать метаданные (`org.opencontainers.image.revision`, `org.opencontainers.image.source`) с манифестом образа. Это позволяет из инспектора Kubernetes сразу перейти по ссылке к точному коммиту, из которого был собран под.",
    "pitfalls": "1. Забытые permissions: по умолчанию в современных репозиториях `GITHUB_TOKEN` имеет режим `read-only`, без `packages: write` сборка упадет с `403 Forbidden`.\n2. Регистр имени репозитория: `ghcr.io` строго требует нижний регистр пути (`ghcr.io/org/repo`). Если имя организации содержит заглавные буквы, экшен `metadata-action` автоматически приводит их к lower-case.\n3. Отсутствие очистки старых untagged образов в реестре, приводящее к исчерпанию дисковых квот организации.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем ключевое отличие `GITHUB_TOKEN` от Personal Access Token (PAT) при авторизации в реестрах контейнеров?\n**Ответ:** `GITHUB_TOKEN` генерируется динамически для каждого конкретного прогона workflow, действует строго во время выполнения джобы и имеет минимально необходимые права, ограниченные текущим репозиторием. PAT привязан к учетной записи конкретного человека, имеет длительный срок жизни и глобальный охват. Использование `GITHUB_TOKEN` исключает утечку персистентных ключей и устраняет проблему увольнения сотрудника, на чьем PAT держался весь CI/CD."
  },
  {
    "num": 19,
    "title": "Валидация Infrastructure as Code: terraform validate и kubeconform",
    "task": "Добавь **infrastructure as code validation**: `terraform validate`, `terraform plan` (comment on PR). `kubeval` / `kubeconform` для Kubernetes manifests. Gate: invalid config = build failure.\n\n---",
    "theory": "С развитием GitOps и Platform Engineering инфраструктура описывается кодом (IaC — Terraform/OpenTofu, Kubernetes Manifests, Helm, Kustomize). Ошибки в манифестах или опечатки в типах ресурсов, дошедшие до продакшна, приводят к авариям масштаба всего кластера.\n\nПайплайн валидации IaC обязан проверять:\n1. **Синтаксис и схему манифестов Kubernetes (`kubeconform`):** Быстрый инструмент на Go, валидирующий YAML-манифесты по официальным JSON-схемам Kubernetes OpenAPI целевой версии (например, `1.31.0`), выявляя устаревшие или несуществующие поля.\n2. **Синтаксис Terraform (`terraform validate` / `tflint`):** Проверка структуры HCL, типов входных переменных и обязательных аргументов провайдеров без обращения к удаленному состоянию (state).\n3. **Безопасность (`checkov` или `tfsec`):** Поиск открытых портов (0.0.0.0/0), отсутствия шифрования дисков и дефолтных паролей.",
    "step_by_step": "1. Создайте `.github/workflows/iac-check.yml`, срабатывающий на Pull Request при изменении файлов `*.tf` или `k8s/**.yaml`.\n2. Настройте шаг валидации Terraform: `terraform fmt -check` и `terraform validate`.\n3. Установите `kubeconform` и запустите проверку каталога с манифестами: `kubeconform -strict -kubernetes-version 1.31.0 k8s/`.\n4. Заблокируйте PR при обнаружении синтаксических ошибок или невалидных полей.",
    "code_blocks": [
      {
        "filename": ".github/workflows/iac-check.yml",
        "lang": "yaml",
        "code": "name: IaC and Kubernetes Validation\n\non:\n  pull_request:\n    paths:\n      - 'deploy/**'\n      - 'terraform/**'\n\njobs:\n  kubeconform:\n    name: Validate K8s Manifests\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - name: Install Kubeconform\n        run: |\n          curl -sL https://github.com/yannh/kubeconform/releases/download/v0.6.7/kubeconform-linux-amd64.tar.gz | tar xz\n          sudo mv kubeconform /usr/local/bin/\n\n      - name: Validate Manifests\n        run: |\n          kubeconform -strict -summary -kubernetes-version 1.31.0 deploy/k8s/\n\n  terraform:\n    name: Validate Terraform\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - name: Setup Terraform\n        uses: hashicorp/setup-terraform@v3\n        with:\n          terraform_version: 1.9.0\n\n      - name: Terraform Init & Validate\n        run: |\n          cd terraform\n          terraform init -backend=false\n          terraform fmt -check\n          terraform validate"
      },
      {
        "filename": "deploy/k8s/deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: billing-service\n  labels:\n    app.kubernetes.io/name: billing\nspec:\n  replicas: 3\n  selector:\n    matchLabels:\n      app.kubernetes.io/name: billing\n  template:\n    metadata:\n      labels:\n        app.kubernetes.io/name: billing\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/billing:v1.0.0\n          resources:\n            limits:\n              cpu: \"500m\"\n              memory: \"256Mi\"\n            requests:\n              cpu: \"100m\"\n              memory: \"64Mi\"\n          ports:\n            - containerPort: 8080"
      }
    ],
    "under_the_hood": "`kubeconform` не требует подключения к живому API-серверу кластера. Он парсит YAML в структуру памяти и сопоставляет каждое поле с JSON Schema, скачиваемой из реестра `https://raw.githubusercontent.com/yannh/kubernetes-json-schema`. Флаг `-strict` запрещает наличие неопределенных (лишних) полей, что предотвращает ошибки опечаток в названиях ключей.\n\n`terraform validate` строит граф зависимостей локальных модулей, валидирует внутреннюю совместимость ссылок на атрибуты и блоки ресурсов.",
    "pitfalls": "1. Использование команды `kubectl apply --dry-run=client` в CI: она имеет ограниченные проверки и требует громоздкой настройки kubectl с валидным kubeconfig.\n2. Пропуск флага `-backend=false` при `terraform init` в CI: попытка подключиться к S3 бэкенду без прод-секретов приведет к падению сборки на публичных PR.\n3. Игнорирование валидации Custom Resource Definitions (CRD) операторов (PrometheusRule, VirtualService): необходимо передавать флаг `-schema-location default -schema-location 'https://...'`.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между инструментами `conftest` (OPA), `kubeconform` и `polaris` при проверке манифестов Kubernetes в CI?\n**Ответ:** \n- **`kubeconform`** проверяет **структурную валидность** схемы: соответствие полей спецификации K8s OpenAPI (типы, обязательные атрибуты).\n- **`conftest` (Open Policy Agent / Rego)** проверяет **бизнес-политики и безопасность**: например, «запретить запуск под root», «обязательно наличие лейбла `owner`», «запретить image:latest».\n- **`polaris`** специализируется на **best practices** аудита надежности и эффективности использования ресурсов (наличие probes, resources limits/requests). В зрелом CI они дополняют друг друга."
  },
  {
    "num": 20,
    "title": "Пайплайн в GitLab CI: stages, кэширование go pkg/mod и артефакты",
    "task": "Перепиши pipeline на **GitLab CI**: `.gitlab-ci.yml`. Stages: `test`, `build`, `deploy`. `image: golang:1.24`. Cache: `key: \"$CI_COMMIT_REF_SLUG\"`, paths: `/go/pkg/mod`. Покажи similarity/difference с GitHub Actions.",
    "theory": "GitLab CI/CD — промышленный стандарт для self-hosted инсталляций в крупных enterprise-компаниях (банки, финтех, телеком). Конфигурация описывается в декларативном файле `.gitlab-ci.yml`.\n\nКлючевые сущности GitLab CI:\n- **`stages`:** Последовательные фазы выполнения конвейера (например, `test` -> `build` -> `deploy`). Джобы одного stage запускаются параллельно.\n- **`cache`:** Механизм сохранения промежуточных файлов между запусками на одном раннере для ускорения сборки (для Go кэшируются `GOCACHE` и `GOPATH/pkg/mod`).\n- **`artifacts`:** Неизменяемые результаты сборки (бинарники, coverage-отчеты), которые передаются между stages и сохраняются в GitLab на заданный срок (`expire_in`).\n\nПравильное управление кэшем через ключ `key: files: [go.sum]` позволяет инвалидировать зависимости только при изменении дерева модулей.",
    "step_by_step": "1. Создайте в корне проекта файл `.gitlab-ci.yml`.\n2. Объявите базовый Docker-образ `image: golang:1.24-alpine`.\n3. Задайте переменные окружения `GOCACHE` и `GOPATH` внутри рабочей директории проекта.\n4. Настройте секцию `cache` по ключу файла `go.sum`.\n5. Создайте джобы: `unit_tests`, `linter` в стадии `test`, джобу `compile` в стадии `build` с передачей бинарника через `artifacts`.",
    "code_blocks": [
      {
        "filename": ".gitlab-ci.yml",
        "lang": "yaml",
        "code": "image: golang:1.24-alpine\n\nvariables:\n  GOPATH: \"$CI_PROJECT_DIR/.go\"\n  GOCACHE: \"$CI_PROJECT_DIR/.cache/go-build\"\n  CGO_ENABLED: \"0\"\n\nstages:\n  - test\n  - build\n\ncache:\n  key:\n    files:\n      - go.sum\n  paths:\n    - .go/pkg/mod/\n    - .cache/go-build/\n\nbefore_script:\n  - apk add --no-cache git make\n\ntest:unit:\n  stage: test\n  script:\n    - go test -v -race=false -coverprofile=coverage.txt ./...\n  artifacts:\n    expire_in: 7 days\n    reports:\n      coverage_report:\n        coverage_format: cobertura\n        path: coverage.txt\n\nbuild:app:\n  stage: build\n  script:\n    - go build -ldflags=\"-s -w\" -o bin/server .\n  artifacts:\n    paths:\n      - bin/server\n    expire_in: 30 days"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc Greet(name string) string {\n\tif name == \"\" {\n\t\treturn \"Hello, Guest!\"\n\t}\n\treturn fmt.Sprintf(\"Hello, %s!\", name)\n}\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tname := r.URL.Query().Get(\"name\")\n\t\t_, _ = w.Write([]byte(Greet(name)))\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      },
      {
        "filename": "main_test.go",
        "lang": "go",
        "code": "package main\n\nimport \"testing\"\n\nfunc TestGreet(t *testing.T) {\n\ttests := []struct {\n\t\tinput string\n\t\twant  string\n\t}{\n\t\t{\"\", \"Hello, Guest!\"},\n\t\t{\"Alice\", \"Hello, Alice!\"},\n\t}\n\n\tfor _, tt := range tests {\n\t\tif got := Greet(tt.input); got != tt.want {\n\t\t\tt.Errorf(\"Greet(%q) = %q; want %q\", tt.input, got, tt.want)\n\t\t}\n\t}\n}"
      }
    ],
    "under_the_hood": "GitLab Runner выполняет джобу в изолированном Docker-контейнере. По умолчанию раннер монтирует директорию `$CI_PROJECT_DIR`. Если переменные `GOPATH` и `GOCACHE` не переопределены, Go сохраняет кэш в системные папки `/root/go` и `/root/.cache`, которые уничтожаются вместе с контейнером при завершении джобы.\n\nПереопределение путей внутрь `$CI_PROJECT_DIR` позволяет механизму `cache` архивировать эти директории в zip/tar и выгружать в MinIO/S3 (GitLab Distributed Cache) для последующих запусков.",
    "pitfalls": "1. Путаница между `cache` и `artifacts`: `cache` не гарантирован (может быть сброшен при смене раннера), его нельзя использовать для передачи бинарных файлов в стадию деплоя. Для передачи артефактов сборки обязательна директива `artifacts`.\n2. Запуск `go test -race` на Alpine без установки `gcc` и `musl-dev`: CGO флаг падает с ошибкой линковщика.\n3. Отсутствие директивы `expire_in` у артефактов: гигабайты собранных бинарников быстро переполняют хранилище GitLab.",
    "bigtech_interview": "**Вопрос с собеседования:** Как в GitLab CI оптимизировать время прохождения конвейера с 15 минут до 2 минут для микросервиса на Go?\n**Ответ:**\n1. **DAG (Directed Acyclic Graph) через `needs`:** Устранить линейное ожидание стадий; джоба сборки образа может запускаться сразу после завершения линтинга конкретного сервиса, не дожидаясь долгих интеграционных тестов других сервисов.\n2. **Distributed Cache:** Настроить общий S3/MinIO кэш для Go-модулей и кэша компилятора (`GOCACHE`).\n3. **Кастомный базовый образ (Custom CI Image):** Собрать свой образ раннера с предустановленными `golangci-lint`, `go-junit-report`, `git`, исключив `apk add` / `apt-get install` на каждом шаге.\n4. **Параллелизация тестов:** Использовать флаг `parallel:` для запуска тестов по подпакетам на нескольких раннерах."
  },
  {
    "num": 21,
    "title": "Сбор метрик тестового покрытия и интеграция с Codecov",
    "task": "Добавьте проверку code coverage: `go test -coverprofile=coverage.out` и загрузка отчёта в Codecov.",
    "theory": "Тестовое покрытие (Code Coverage) показывает процент строк, блоков и ветвей бизнес-логики, исполняемых при прогоне тест-сьюта.\n\nВ Go встроен мощный генератор профиля покрытия:\n- `go test -coverprofile=coverage.out -covermode=atomic ./...` — ключ `-covermode=atomic` необходим при параллельном тестировании горутин, чтобы исключить Data Race на счетчиках покрытия.\n- Утилита `go tool cover -func=coverage.out` выводит суммарный процент покрытия в терминал.\n- Утилита `go tool cover -html=coverage.out -o coverage.html` формирует интерактивный HTML-отчет с подсветкой непокрытых ветвей (красный цвет).\n\nСервис Codecov позволяет встраивать Quality Gate: автоматически реджектить PR, если суммарный процент покрытия падает более чем на заданный порог (например, 1%), а также комментировать измененные строки прямо в pull request.",
    "step_by_step": "1. Запустите тесты с генерацией профиля покрытия: `go test -coverprofile=coverage.out -covermode=atomic ./...`.\n2. Преобразуйте или выведите процент покрытия через `go tool cover -func=coverage.out`.\n3. Настройте шаг выгрузки отчета через `codecov/codecov-action@v4` в GitHub Actions.\n4. Добавьте файл конфигурации `codecov.yml`, установив целевой порог (target) 80% и допустимый спад (threshold) 0.5%.",
    "code_blocks": [
      {
        "filename": ".github/workflows/coverage.yml",
        "lang": "yaml",
        "code": "name: Test Coverage\n\non:\n  push:\n    branches: [ main ]\n  pull_request:\n    branches: [ main ]\n\njobs:\n  test-coverage:\n    name: Run Unit Tests & Measure Coverage\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - name: Setup Go\n        uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n\n      - name: Run Tests with Atomic Coverage\n        run: |\n          go test -v -race -coverprofile=coverage.out -covermode=atomic ./...\n\n      - name: Verify Coverage Threshold in Terminal\n        run: |\n          go tool cover -func=coverage.out\n\n      - name: Upload to Codecov\n        uses: codecov/codecov-action@v4\n        with:\n          file: ./coverage.out\n          flags: unittests\n          fail_ci_if_error: true\n        env:\n          CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}"
      },
      {
        "filename": "codecov.yml",
        "lang": "yaml",
        "code": "coverage:\n  status:\n    project:\n      default:\n        target: 80%\n        threshold: 0.5%\n    patch:\n      default:\n        target: 85%\ncomment:\n  layout: \"reach,diff,flags,files\"\n  behavior: default"
      },
      {
        "filename": "auth/auth.go",
        "lang": "go",
        "code": "package auth\n\nimport \"errors\"\n\nvar ErrEmptyCredentials = errors.New(\"логин или пароль не могут быть пустыми\")\n\n// ValidateUser проверяет валидность логина и пароля пользователя.\nfunc ValidateUser(username, password string) error {\n\tif username == \"\" || password == \"\" {\n\t\treturn ErrEmptyCredentials\n\t}\n\tif len(password) < 8 {\n\t\treturn errors.New(\"пароль должен содержать минимум 8 символов\")\n\t}\n\treturn nil\n}"
      },
      {
        "filename": "auth/auth_test.go",
        "lang": "go",
        "code": "package auth\n\nimport \"testing\"\n\nfunc TestValidateUser(t *testing.T) {\n\ttests := []struct {\n\t\tname     string\n\t\tuser     string\n\t\tpass     string\n\t\twantErr  bool\n\t}{\n\t\t{\"Valid User\", \"admin\", \"secret123\", false},\n\t\t{\"Empty User\", \"\", \"secret123\", true},\n\t\t{\"Short Password\", \"admin\", \"123\", true},\n\t}\n\n\tfor _, tt := range tests {\n\t\tt.Run(tt.name, func(t *testing.T) {\n\t\t\terr := ValidateUser(tt.user, tt.pass)\n\t\t\tif (err != nil) != tt.wantErr {\n\t\t\t\tt.Fatalf(\"ValidateUser() error = %v, wantErr %v\", err, tt.wantErr)\n\t\t\t}\n\t\t})\n\t}\n}"
      }
    ],
    "under_the_hood": "Флаг `-covermode=atomic` указывает компилятору `go test` инструментировать исходный код: перед каждым базовым блоком кода вставляется атомарный инкремент счетчика `sync/atomic.AddUint32(&counter, 1)`. \n\nЕсли использовать режим по умолчанию `set` при параллельном тестировании горутин (`-race`), запись в счетчик вызовет ложное срабатывание Race Detector. Сгенерированный файл `coverage.out` содержит кортежи: `файл:строка_старта.колонка,строка_конца.колонка кол-во_инструкций число_вызовов`.",
    "pitfalls": "1. Гонка данных в счетчиках покрытия: использование `-covermode=set` вместе с флагом `-race` приводит к падению тестов из-за data race в самом коде инструментации.\n2. Погоня за 100% покрытием: разработчики начинают писать бесполезные тесты для геттеров, сеттеров и сгенерированного protobuf-кода, что увеличивает время сборки и хрупкость тестов.\n3. Отсутствие флага `-coverpkg=./...`: если юнит-тест пакета `handlers` тестирует также пакет `service`, покрытие сервиса не будет учтено без флага `-coverpkg`.",
    "bigtech_interview": "**Вопрос с собеседования:** Что такое «Patch Coverage» в Codecov и почему в BigTech командах отслеживают именно его, а не общий «Project Coverage»?\n**Ответ:** Patch Coverage измеряет процент покрытия **только тех строк кода, которые добавлены или изменены в текущем Pull Request**. Общий Project Coverage в легаси-монолите может составлять 40%, и поднять его моментально невозможно. Однако строгое правило «Patch Coverage >= 85%» гарантирует, что любой новый функционал покрыт тестами на высоком уровне, и суммарный техдолг системы с каждым релизом непрерывно снижается."
  },
  {
    "num": 22,
    "title": "CI линтинг на страже: тонкая настройка .golangci.yml и локальный кэш",
    "task": "**CI: Линтер на страже**: Никогда не мерджи грязный код! Добавь шаг с использованием `golangci-lint` (есть готовый GitHub Action `golangci/golangci-lint-action`). Намеренно закоммить код с неиспользуемой переменной. Убедись, что пайплайн **падает** и не дает коду пройти дальше.",
    "theory": "Качественный линтинг в CI не должен раздражать разработчиков ложными срабатываниями (false positives) или падать по 10 минут. Для этого требуется тонкая настройка исключений и параметров в `.golangci.yml`.\n\nКлючевые практики enterprise-конфигурации:\n1. **Исключение тестовых файлов из строгих правил:** Например, в тестах допустимо игнорировать ошибки закрытия `defer resp.Body.Close()`. Это настраивается через `issues.exclude-rules`.\n2. **Параллельное исполнение:** `run.concurrency: 4` позволяет утилизировать многоядерность CI-раннера.\n3. **Строгий контроль импортов (`gci` / `goimports`):** Автоматическая группировка импортов (стандартная библиотека, сторонние пакеты, внутренние модули компании).\n4. **Контроль сложности кода (`gocyclo` / `cyclop`):** Ограничение цикломатической сложности функций (обычно не более 15), стимулирующее рефакторинг.",
    "step_by_step": "1. Настройте секцию `linters-settings` для `gci` с явным разделением на `standard`, `default`, `prefix(my-module)`.\n2. Добавьте линтер `gocyclo` с порогом `min-complexity: 15`.\n3. Добавьте в `issues.exclude-rules` исключение ошибок `errcheck` для файлов `*_test.go`.\n4. Включите шаг запуска `golangci-lint run --new-from-rev=origin/main` для быстрой проверки только изменений в PR.",
    "code_blocks": [
      {
        "filename": ".golangci.yml",
        "lang": "yaml",
        "code": "run:\n  timeout: 5m\n  concurrency: 4\n  issues-exit-code: 1\n\nlinters:\n  disable-all: true\n  enable:\n    - errcheck\n    - gosimple\n    - govet\n    - ineffassign\n    - staticcheck\n    - unused\n    - gocyclo\n    - gci\n\nlinters-settings:\n  gocyclo:\n    min-complexity: 15\n  gci:\n    sections:\n      - standard\n      - default\n      - prefix(example.com/project)\n\nissues:\n  exclude-rules:\n    - path: _test\\.go\n      linters:\n        - errcheck\n        - gocyclo"
      },
      {
        "filename": ".github/workflows/fast-lint.yml",
        "lang": "yaml",
        "code": "name: Fast PR Linter\n\non:\n  pull_request:\n    branches: [ main ]\n\njobs:\n  lint:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n        with:\n          fetch-depth: 0\n\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n\n      - name: Install golangci-lint\n        run: go install github.com/golangci/golangci-lint/cmd/golangci-lint@v1.64.5\n\n      - name: Run Linter on Changed Code Only\n        run: |\n          golangci-lint run --new-from-rev=origin/main --timeout=3m"
      },
      {
        "filename": "order.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n)\n\n// ProcessOrder проверяет статус заказа и сумму.\nfunc ProcessOrder(status string, amount float64) error {\n\tif amount <= 0 {\n\t\treturn errors.New(\"некорректная сумма заказа\")\n\t}\n\n\tif status != \"PENDING\" {\n\t\treturn fmt.Errorf(\"недопустимый статус заказа: %s\", status)\n\t}\n\n\treturn nil\n}"
      }
    ],
    "under_the_hood": "Флаг `--new-from-rev=origin/main` выполняет `git diff` между веткой PR и базовой веткой `main`. `golangci-lint` запускает полный статический анализ всего проекта для построения точной таблицы типов и связей, но в итоговый отчет выводит **исключительно те ошибки, которые локализованы в измененных строках**. \n\nДля работы этой команды в `actions/checkout` обязательно требуется `fetch-depth: 0`, иначе shallow-клон репозитория не будет содержать историю коммитов базовой ветки.",
    "pitfalls": "1. Shallow checkout: при `fetch-depth: 1` команда `git merge-base` не может найти общего предка, и флаг `--new-from-rev` падает с фатальной ошибкой git.\n2. Устаревание версии линтера: использование локальной версии `golangci-lint` на машине разработчика 1.55, а в CI — 1.64, что приводит к «у меня локально все работает, а CI красный». Версии должны быть строго зафиксированы через Makefile или toolchain.\n3. Отсутствие линтера `gci` / `gofumpt`: разработчики тратят время на споры о форматировании импортов во время Code Review.",
    "bigtech_interview": "**Вопрос с собеседования:** Как решить проблему «Legacy Codebase», когда при включении нового линтера в `.golangci.yml` падает 5 000 старых предупреждений во всем репозитории?\n**Ответ:**\n1. Использовать флаг `--new-from-rev=origin/main` в CI, чтобы блокировать появление предупреждений **только в новом и изменяемом коде**.\n2. Использовать генерацию базовой линии (baseline/todo list): исключить старые предупреждения через секцию `issues.exclude` или сгенерированный список исключений.\n3. Внедрить в команду правило «Boy Scout Rule» (оставь место чище, чем нашел): если инженер прикасается к файлу с легаси-кодом, он исправляет линтер-ошибки в рамках отдельного рефакторинг-коммита."
  },
  {
    "num": 23,
    "title": "Многоплатформенная сборка (Multi-arch) образов с Docker Buildx и QEMU",
    "task": "**[Multi-arch сборка]**: Используй `docker buildx` в CI для сборки образов под архитектуры `linux/amd64` и `linux/arm64` (чтобы твой образ работал и на Intel-серверах, и на Apple Silicon / ARM-инстансах AWS).",
    "theory": "Современная облачная инфраструктура все чаще переходит на ARM-процессоры (AWS Graviton, Apple Silicon M-series, Ampere Altra в GCP/Yandex Cloud) из-за лучшего соотношения производительности на ватт и снижения стоимости аренды виртуальных машин на 20–40%.\n\nЕсли собрать образ только под `linux/amd64`, попытка запустить его на ARM-ноде Kubernetes завершится ошибкой ядра `exec format error`.\n\nРешение — сборка мульти-архитектурного OCI Image Index с поддержкой платформ `linux/amd64` и `linux/arm64`:\n- **QEMU (`docker/setup-qemu-action`):** Эмулирует чужую архитектуру процессора в пространстве пользователя (`binfmt_misc`).\n- **Buildx (`docker/setup-buildx-action`):** Расширение Docker CLI на базе BuildKit, собирающее слои под несколько платформ и склеивающее их в единый манифест-манифестов (Manifest List).",
    "step_by_step": "1. Настройте эмуляцию QEMU через `docker/setup-qemu-action@v3`.\n2. Создайте и инициализируйте Buildx builder через `docker/setup-buildx-action@v3`.\n3. В джобе `docker/build-push-action` укажите параметр `platforms: linux/amd64,linux/arm64`.\n4. Соберите и опубликуйте образ.\n5. Проверьте манифест с помощью команды `docker buildx imagetools inspect`.",
    "code_blocks": [
      {
        "filename": ".github/workflows/multi-arch.yml",
        "lang": "yaml",
        "code": "name: Multi-Arch Image Build\n\non:\n  push:\n    tags:\n      - 'v*.*.*'\n\njobs:\n  buildx:\n    name: Build Multi-Arch Docker Image\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout\n        uses: actions/checkout@v4\n\n      - name: Set up QEMU\n        uses: docker/setup-qemu-action@v3\n\n      - name: Set up Docker Buildx\n        uses: docker/setup-buildx-action@v3\n\n      - name: Log in to Docker Hub\n        uses: docker/login-action@v3\n        with:\n          username: ${{ secrets.DOCKERHUB_USERNAME }}\n          password: ${{ secrets.DOCKERHUB_TOKEN }}\n\n      - name: Build and Push Multi-Arch Image\n        uses: docker/build-push-action@v5\n        with:\n          context: .\n          platforms: linux/amd64,linux/arm64\n          push: true\n          tags: ${{ secrets.DOCKERHUB_USERNAME }}/gateway:${{ github.ref_name }}"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# syntax=docker/dockerfile:1\nFROM --platform=$BUILDPLATFORM golang:1.24-alpine AS builder\nARG TARGETOS\nARG TARGETARCH\nWORKDIR /app\nCOPY go.mod go.sum* ./\nRUN go mod download\nCOPY . .\nRUN CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH go build -ldflags=\"-s -w\" -o /app/server .\n\nFROM alpine:3.21\nWORKDIR /\nCOPY --from=builder /app/server /server\nUSER 65534:65534\nENTRYPOINT [\"/server\"]"
      },
      {
        "filename": "inspect.sh",
        "lang": "bash",
        "code": "# Проверка OCI Manifest List в удаленном реестре:\ndocker buildx imagetools inspect docker.io/username/gateway:v1.0.0"
      }
    ],
    "under_the_hood": "Сборка нативного Go-кода через эмуляцию QEMU может работать в 10 раз медленнее из-за трансляции инструкций x86 -> ARM. \n\nПромышленный трюк заключается в использовании аргументов BuildKit:\n`FROM --platform=$BUILDPLATFORM golang:...`\nКомпилятор Go запускается нативно на платформе хоста раннера (`amd64`), а кросс-компиляция под `arm64` выполняется моментально силами самого Go (`GOOS=$TARGETOS GOARCH=$TARGETARCH go build`) без задействования тяжелой эмуляции QEMU!",
    "pitfalls": "1. Запуск CGO-сборки под `arm64` без кросс-компилятора `gcc-aarch64-linux-gnu`: CGO требует нативных заголовочных файлов целевой платформы. Рекомендуется отключать `CGO_ENABLED=0`.\n2. Забытый флаг `--platform=$BUILDPLATFORM`: если его опустить, сам компилятор Go будет выполняться внутри эмулятора QEMU, и сборка затянется на 20 минут.\n3. Локальный просмотр `docker images` после сборки нескольких платформ: Buildx не может загрузить мульти-архитектурный образ в локальный Docker Daemon без экспортера OCI tarball, поэтому флаг `push: true` обязателен.",
    "bigtech_interview": "**Вопрос с собеседования:** Как устроен OCI Image Index (Manifest List) и каким образом Kubernetes понимает, какой слой скачать на конкретную ноду?\n**Ответ:** OCI Image Index — это JSON-документ медиатипа `application/vnd.oci.image.index.v1+json`. Он содержит массив дескрипторов `manifests[]`, где каждый элемент ссылается на дайджест конкретного образа и указывает платформу (`platform.architecture: amd64` или `arm64`, `platform.os: linux`). Kubelet при обращении к реестру передает параметры своей архитектуры (`GOARCH/GOOS`), и контейнерный рантайм (containerd/CRI-O) скачивает строго тот дочерний образ, который соответствует архитектуре процессора данной ноды."
  },
  {
    "num": 24,
    "title": "Управление GitLab CI Runners: Shared против Specific и тегирование",
    "task": "Настрой **GitLab CI with runners**: shared runners vs specific runners (tagged `docker`, `k8s`). Self-hosted runner on Kubernetes (`gitlab-runner` Helm chart). Покажи scaling runners.",
    "theory": "В инфраструктуре GitLab CI исполнители задач (GitLab Runners) делятся на два типа:\n1. **Shared Runners:** Общий пул раннеров, доступный всем проектам организации. Подходит для простых проверок, но имеет очереди и разделяемые ресурсы.\n2. **Specific (Project/Group) Runners:** Выделенные виртуальные машины или поды Kubernetes, зарегистрированные для конкретного проекта или департамента. Необходимы для:\n   - Доступа к закрытым контурам сети (VPN, базы данных в VPC, внутренние OCI-реестры).\n   - Специфического оборудования (GPU для ML, ARM bare-metal, SSD NVMe).\n   - Изоляции чувствительных сборок со строгими требованиями безопасности.\n\nСвязывание джобы с раннером осуществляется через **теги (`tags`)**. Если у раннера указаны теги `[docker, k8s, high-cpu]`, джоба с директивой `tags: [docker, high-cpu]` будет направлена строго на него.",
    "step_by_step": "1. Зарегистрируйте раннер на выделенном сервере или в Kubernetes кластере с тегами `go-builder`, `k8s-infra`.\n2. В файле `.gitlab-ci.yml` добавьте секцию `tags` в каждую джобу.\n3. Для тяжелых сборок укажите теги высокопроизводительных раннеров.\n4. Настройте `executor = \"kubernetes\"` в файле `config.toml` раннера для динамического создания подов под каждую джобу.",
    "code_blocks": [
      {
        "filename": ".gitlab-ci.yml",
        "lang": "yaml",
        "code": "stages:\n  - lint\n  - test\n  - deploy\n\njob:linter:\n  stage: lint\n  image: golangci/golangci-lint:v1.64.5-alpine\n  tags:\n    - shared-docker\n  script:\n    - golangci-lint run --timeout=5m\n\njob:integration_tests:\n  stage: test\n  image: golang:1.24\n  tags:\n    - high-perf\n    - bare-metal\n  script:\n    - go test -v -race -timeout=15m ./internal/integration/...\n\njob:deploy_k8s:\n  stage: deploy\n  tags:\n    - k8s-prod-access\n  script:\n    - kubectl rollout status deployment/auth-service -n production"
      },
      {
        "filename": "config.toml",
        "lang": "toml",
        "code": "concurrent = 8\ncheck_interval = 0\n\n[session_server]\n  session_timeout = 1800\n\n[[runners]]\n  name = \"k8s-cluster-runner\"\n  url = \"https://gitlab.example.com\"\n  id = 42\n  token = \"glrt-t1_runner_registration_token\"\n  token_obtained_at = 2026-01-01T00:00:00Z\n  token_expires_at = 0001-01-01T00:00:00Z\n  executor = \"kubernetes\"\n  [runners.kubernetes]\n    host = \"\"\n    bearer_token_overwrite_allowed = false\n    image = \"alpine:3.21\"\n    namespace = \"gitlab-runners\"\n    privileged = false\n    cpu_limit = \"4\"\n    memory_limit = \"8Gi\"\n    cpu_request = \"1\"\n    memory_request = \"2Gi\" "
      }
    ],
    "under_the_hood": "GitLab Runner периодически опрашивает GitLab API (`POST /api/v4/jobs/request`). В теле запроса раннер передает свои теги. \n\nGitLab CI Scheduler сравнивает теги свободной джобы с тегами запросившего раннера. Джоба назначается только при строгом совпадении подмножества тегов. \n\nВ Kubernetes Executor раннер создает Pod с несколькими контейнерами: `build` (выполняет скрипт), `helper` (клонирует git, загружает/скачивает кэш и артефакты) и sidecar-контейнеры сервисов (базы данных, Redis).",
    "pitfalls": "1. Зависание джобы в статусе `Pending` (Stuck job): если в `.gitlab-ci.yml` указать несуществующий тег, например `tags: [gpu]`, а такого раннера нет в проекте, пайплайн будет висеть бесконечно.\n2. Включение `privileged = true` на shared-раннерах: компрометация одной сборки позволяет злоумышленнику вырваться из Docker-контейнера на хостовую ноду кластера.\n3. Использование одного runner token на сотне серверов: затрудняет аудит и аннулирование доступа при компрометации отдельного хоста.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в production-кластерах запрещено использовать Docker-in-Docker (`dind`) с привилегированным режимом (`privileged = true`) на GitLab раннерах, и чем его заменяют?\n**Ответ:** Флаг `privileged = true` отключает изоляцию ядра Linux (AppArmor, seccomp, сбрасывает ограничения cgroups), давая контейнеру полные права суперпользователя на ноде K8s. Любой разработчик через скрипт сборки может смонтировать диск ноды `/dev/sda1` и украсть секреты всех соседних подов. \nВместо DinD в enterprise используют **беспривилегированные сборщики**:\n1. **Kaniko** от Google: собирает Docker-образы в пространстве пользователя без демона Docker.\n2. **Buildah / Podman**: сборка без root-прав через user namespaces.\n3. **BuildKit daemonless** в режиме `rootless`."
  },
  {
    "num": 25,
    "title": "Декларативный пайплайн в Jenkins (Jenkinsfile): stages, junit и parallel",
    "task": "Настрой **Jenkins pipeline** (declarative): `Jenkinsfile`. Stages: `Checkout`, `Test`, `Build`, `Deploy`. Agents: `docker` agent `golang:1.24`. Shared library for common steps. Покажи enterprise CI.",
    "theory": "Несмотря на популярность GitHub Actions и GitLab CI, Jenkins остается основой CI/CD во многих Enterprise-корпорациях благодаря десяткам тысяч плагинов и зрелой системе управления доступом (RBAC).\n\nСовременный стандарт Jenkins — **Declarative Pipeline** (`Jenkinsfile`), пришедший на смену хрупким Scripted Groovy пайплайнам:\n- Жесткая декларативная структура блоков: `pipeline`, `agent`, `stages`, `steps`, `post`.\n- `agent { docker { ... } }`: выполнение каждого этапа внутри чистого контейнера без засорения ОС агента.\n- Секция `post { ... }`: гарантированное выполнение блоков `always`, `success`, `failure`, `cleanup` (например, отправка алертов и сбор JUnit XML отчетов).\n- Блок `parallel`: одновременный запуск независимых проверок (юнит-тесты и статический анализ).",
    "step_by_step": "1. Создайте в корне репозитория файл `Jenkinsfile`.\n2. Объявите агента с базовым образом `golang:1.24`.\n3. Добавьте утилиту `go-junit-report` для конвертации вывода `go test` в стандартный XML-формат JUnit.\n4. В секции `stages` организуйте параллельное выполнение тестов и линтера через блок `parallel`.\n5. В секции `post.always` добавьте шаг `junit 'reports/**/*.xml'` для отображения графиков тестов в веб-интерфейсе Jenkins.",
    "code_blocks": [
      {
        "filename": "Jenkinsfile",
        "lang": "groovy",
        "code": "pipeline {\n    agent {\n        docker {\n            image 'golang:1.24-alpine'\n            args '-v /var/cache/go:/go/pkg/mod'\n        }\n    }\n    options {\n        timeout(time: 30, unit: 'MINUTES')\n        buildDiscarder(logRotator(numToKeepStr: '20'))\n    }\n    environment {\n        CGO_ENABLED = '0'\n        GOPATH = '/go'\n    }\n    stages {\n        stage('Prepare') {\n            steps {\n                sh 'apk add --no-cache git make'\n                sh 'go install github.com/jstemmer/go-junit-report/v2@latest'\n                sh 'mkdir -p reports'\n            }\n        }\n        stage('Quality Checks') {\n            parallel {\n                stage('Unit Tests') {\n                    steps {\n                        sh 'go test -v -coverprofile=reports/coverage.out ./... 2>&1 | go-junit-report -set-exit-code > reports/junit.xml'\n                    }\n                }\n                stage('Compile Binary') {\n                    steps {\n                        sh 'go build -ldflags=\"-s -w\" -o bin/app .'\n                    }\n                }\n            }\n        }\n    }\n    post {\n        always {\n            junit testResults: 'reports/junit.xml', allowEmptyResults: true\n            archiveArtifacts artifacts: 'bin/app', fingerprint: true, allowEmptyArchive: true\n        }\n        failure {\n            echo 'Пайплайн завершился ошибкой! Уведомляем команду...'\n        }\n    }\n}"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc HealthCheck() string {\n\treturn \"healthy\"\n}\n\nfunc main() {\n\thttp.HandleFunc(\"/health\", func(w http.ResponseWriter, r *http.Request) {\n\t\t_, _ = w.Write([]byte(HealthCheck()))\n\t})\n\tfmt.Println(\"Сервис запущен...\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      },
      {
        "filename": "main_test.go",
        "lang": "go",
        "code": "package main\n\nimport \"testing\"\n\nfunc TestHealthCheck(t *testing.T) {\n\tif got := HealthCheck(); got != \"healthy\" {\n\t\tt.Fatalf(\"HealthCheck() = %s; want healthy\", got)\n\t}\n}"
      }
    ],
    "under_the_hood": "Когда Jenkins выполняет директиву `agent { docker { ... } }`, мастер-нода отправляет на агент команду:\n`docker run -d -u 1000:1000 -v /workspace:/workspace golang:1.24-alpine cat`\nКонтейнер удерживается в запущенном состоянии командой `cat`. Каждый последующий блок `sh '...'` исполняется внутри контейнера через `docker exec`. \n\nПлагин JUnit парсит результирующий XML и записывает статистику в SQL/H2 базу данных Jenkins, формируя графики динамики тестов (Test Result Trend).",
    "pitfalls": "1. Забытый флаг `-set-exit-code` в `go-junit-report`: без него утилита считывает `FAIL` от `go test`, генерирует XML, но завершается с кодом `0`, и Jenkins считает шаг успешным.\n2. Проблема прав доступа к смонтированным папкам: контейнер по умолчанию работает под тем же UID, что и демон Jenkins на хосте; несовпадение UID приводит к ошибкам `Permission denied`.\n3. Смешивание Scripted и Declarative синтаксиса без блока `script { ... }` внутри шагов `steps`.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем преимущества и недостатки перехода с Jenkins на современные облачные CI-решения (GitHub Actions / GitLab CI / Tekton)?\n**Ответ:** \n- **Преимущества перехода:** Отсутствие необходимости администрировать собственный мастер-сервер Jenkins (патчи уязвимостей, падения плагинов, утечки памяти JVM), конфигурация как код (Pipeline as Code) хранится рядом с приложением в репозитории, простота масштабирования ephemeral-агентов.\n- **Недостатки перехода:** Сложность миграции тысяч кастомных Groovy-скриптов и корпоративных плагинов, в банках часто требуется строгая изоляция в закрытом контуре без выхода в интернет, где Jenkins с локальными агентами разворачивается проще всего."
  },
  {
    "num": 26,
    "title": "Кэширование слоев Docker Buildx через GitHub Actions Cache (gha)",
    "task": "Используйте `docker/build-push-action` с layer caching через GitHub Actions cache.",
    "theory": "При обычной сборке Docker-образа в облачном CI каждый запуск происходит на чистой виртуальной машине. Это означает, что слои `RUN go mod download` и компиляция Go собираются «с нуля», занимая по 3–5 минут на каждый PR.\n\nBuildKit поддерживает внешние бэкэнды кэша (External Cache Storage). Для GitHub Actions разработан нативный бэкенд **GitHub Actions Cache (`type=gha`)**:\n- `cache-from: type=gha` — указывает BuildKit искать существующие слои в хранилище кэша GitHub.\n- `cache-to: type=gha,mode=max` — выгружает в кэш не только финальный слой образа, но и промежуточные слои всех этапов сборки (`multi-stage`).\n\nБлагодаря этому при изменении только одного Go-файла этап `go mod download` мгновенно берется из кэша (CACHED), а повторная сборка занимает менее 10 секунд.",
    "step_by_step": "1. Включите Buildx через `docker/setup-buildx-action@v3`.\n2. В параметрах `docker/build-push-action@v5` добавьте секции `cache-from: type=gha` и `cache-to: type=gha,mode=max`.\n3. Убедитесь, что в Dockerfile инструкции `COPY go.mod go.sum` и `RUN go mod download` вынесены перед `COPY . .`.\n4. Запустите сборку дважды и проверьте в логах наличие пометки `CACHED` напротив скачивания модулей.",
    "code_blocks": [
      {
        "filename": ".github/workflows/docker-cache.yml",
        "lang": "yaml",
        "code": "name: Docker Layer Caching with GHA\n\non:\n  push:\n    branches: [ main ]\n  pull_request:\n    branches: [ main ]\n\njobs:\n  build:\n    name: Build with GHA Layer Cache\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout\n        uses: actions/checkout@v4\n\n      - name: Set up Docker Buildx\n        uses: docker/setup-buildx-action@v3\n\n      - name: Build Docker Image with GHA Cache\n        uses: docker/build-push-action@v5\n        with:\n          context: .\n          push: false\n          tags: myapp:local-test\n          cache-from: type=gha\n          cache-to: type=gha,mode=max"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# syntax=docker/dockerfile:1\nFROM golang:1.24-alpine AS builder\nWORKDIR /src\n\n# Кэширование зависимостей: слой не пересобирается, пока не изменится go.sum\nCOPY go.mod go.sum* ./\nRUN go mod download\n\n# Копирование исходного кода и компиляция\nCOPY . .\nRUN CGO_ENABLED=0 go build -ldflags=\"-s -w\" -o /bin/service .\n\nFROM alpine:3.21\nCOPY --from=builder /bin/service /service\nUSER 65534:65534\nENTRYPOINT [\"/service\"]"
      }
    ],
    "under_the_hood": "Бэкенд `type=gha` обращается напрямую к GitHub Actions Cache Service API по протоколу gRPC/REST. BuildKit разбивает слои на OCI-дескрипторы и сохраняет их в blob store GitHub Actions (с лимитом 10 ГБ на репозиторий).\n\nПараметр `mode=max` критичен: по умолчанию (`mode=min`) BuildKit кэширует только слои, попавшие в итоговый stage образа. Промежуточный этап `builder` со скачанными модулями и `.a` архивами компилятора Go будет проигнорирован. Режим `mode=max` принудительно сохраняет артефакты всех промежуточных стадий.",
    "pitfalls": "1. Использование `mode=min` вместо `mode=max`: разработчик удивляется, почему этап `RUN go mod download` не кэшируется при последующих запусках.\n2. Неправильный порядок инструкций в Dockerfile: если поставить `COPY . .` перед `RUN go mod download`, изменение любого README.md сбросит кэш всех последующих слоев.\n3. Исчерпание квоты в 10 ГБ: GitHub удаляет самые старые кэши по политике LRU (Least Recently Used), поэтому рекомендуется собирать компактные слои без лишних временных файлов.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между `cache-to: type=gha` и `cache-to: type=registry,ref=myregistry/cache`? Когда следует предпочесть реестр?\n**Ответ:** \n- `type=gha` привязан к инфраструктуре GitHub Actions. Он идеален для открытых или небольших проектов, но ограничен квотой 10 ГБ на репозиторий и недоступен за пределами GitHub.\n- `type=registry` выгружает кэш-слои напрямую в OCI-реестр (например, Harbor, AWS ECR, GCP Artifact Registry). Этот подход предпочтителен в крупных компаниях: кэш не ограничен по размеру, к нему имеют доступ любые локальные машины инженеров (`docker buildx --cache-from`), а также внешние раннеры (GitLab CI, Jenkins, Argo Workflows)."
  },
  {
    "num": 27,
    "title": "GitOps с ArgoCD: настройка манифеста Application CRD и автосинхронизация",
    "task": "Настрой **ArgoCD** (GitOps): `Application` CRD. Source: Git repo with K8s manifests. Destination: `https://kubernetes.default.svc`, namespace `production`. Sync policy: `automated` (prune, self-heal). Покажи declarative continuous delivery.",
    "theory": "GitOps — методология непрерывной доставки для облачных приложений, где Git-репозиторий является «единственным источником правды» (Single Source of Truth) о желаемом состоянии кластера.\n\n**ArgoCD** — ведущий GitOps-контроллер для Kubernetes, реализованный на Go:\n- Непрерывно сравнивает декларированное в Git состояние манифестов (Desired State) с реальным состоянием ресурсов в кластере (Live State).\n- При обнаружении расхождений (OutOfSync) уведомляет или автоматически устраняет расхождение (Self-Heal / Automated Sync).\n- Основной ресурс — Custom Resource Definition **`Application`**: связывает Git-репозиторий, каталог с манифестами и целевой кластер с namespace.",
    "step_by_step": "1. Создайте манифест `argocd-application.yaml` с `kind: Application`.\n2. Укажите `spec.source`: URL git-репозитория, целевую ветку `targetRevision` и путь к каталогу с K8s-манифестами `path`.\n3. Укажите `spec.destination`: URL сервера Kubernetes (`https://kubernetes.default.svc`) и целевой `namespace`.\n4. Включите политику автоматической синхронизации `syncPolicy.automated: {prune: true, selfHeal: true}`.\n5. Примените манифест: `kubectl apply -f argocd-application.yaml -n argocd`.",
    "code_blocks": [
      {
        "filename": "argocd-application.yaml",
        "lang": "yaml",
        "code": "apiVersion: argoproj.io/v1alpha1\nkind: Application\nmetadata:\n  name: payment-service\n  namespace: argocd\n  finalizers:\n    - resources-finalizer.argocd.argoproj.io\nspec:\n  project: default\n  source:\n    repoURL: 'https://github.com/company/k8s-manifests.git'\n    targetRevision: HEAD\n    path: apps/payment-service/overlays/production\n  destination:\n    server: 'https://kubernetes.default.svc'\n    namespace: payments\n  syncPolicy:\n    automated:\n      prune: true\n      selfHeal: true\n    syncOptions:\n      - CreateNamespace=true\n      - PruneLast=true"
      },
      {
        "filename": "apps/payment-service/overlays/production/deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: payment-api\n  namespace: payments\nspec:\n  replicas: 3\n  selector:\n    matchLabels:\n      app: payment-api\n  template:\n    metadata:\n      labels:\n        app: payment-api\n    spec:\n      containers:\n        - name: server\n          image: ghcr.io/company/payment-api:v1.4.2\n          ports:\n            - containerPort: 8080"
      }
    ],
    "under_the_hood": "ArgoCD Application Controller каждые 3 минуты (или мгновенно по входящему Webhook от GitHub) запускает цикл сверки (Reconciliation Loop). \n\nКонтроллер выполняет `git clone / git fetch`, рендерит манифесты (с помощью Kustomize или Helm) и обращается к K8s API Discovery. С помощью алгоритма 3-way merge контроллер сопоставляет Git, API и Live-объекты.\n\nЕсли включен `selfHeal: true`, любая ручная попытка инженера изменить манифест в кластере через `kubectl edit` будет перезаписана состоянием из Git в течение нескольких секунд.",
    "pitfalls": "1. Отсутствие `prune: true`: при удалении YAML-файла из Git ресурс останется «висеть» в кластере как сирота-зомби.\n2. Хранение исходного Go-кода приложения и GitOps-манифестов в одном репозитории: каждый коммит в код приложения будет вызывать лишний цикл перегенерации ArgoCD. Лучшая практика — разделение на App Repo и Config/Infra Repo.\n3. Отсутствие `finalizers`: при удалении ресурса `Application` ресурсы сервиса в кластере могут остаться неуправляемыми.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем фундаментальное преимущество Pull-модели (ArgoCD / Flux) перед Push-моделью (деплой через `kubectl apply` прямо из джобы GitHub Actions)?\n**Ответ:** \n1. **Безопасность (No Cluster Credentials in CI):** В Push-модели раннер CI обязан иметь kubeconfig с правами администратора кластера. Компрометация CI дает злоумышленнику полный доступ к кластеру. В Pull-модели агент ArgoCD сидит внутри кластера и тянет изменения сам — кластер закрыт извне, kubeconfig наружу не отдается.\n2. **Защита от дрифта (Drift Detection):** Push-пайплайн запускается только при коммите. Если кто-то ночью изменил под руками через `kubectl`, Push-пайплайн об этом не узнает. ArgoCD непрерывно мониторит дрифт и автоматически возвращает кластер к состоянию из Git."
  },
  {
    "num": 28,
    "title": "CI: Сканирование уязвимостей в зависимостях Go с помощью govulncheck",
    "task": "**CI: Сканирование уязвимостей**: Установи официальный инструмент сканирования уязвимостей в Go: `govulncheck`. Добавь его запуск в пайплайн. Он проверит, нет ли в твоем `go.mod` пакетов с известными CVE (уязвимостями).",
    "theory": "Ошибки безопасности в сторонних библиотеках (supply chain vulnerabilities) представляют серьезную угрозу. Официальная команда Go разработала специализированный инструмент **`govulncheck`**, опирающийся на базу данных уязвимостей Go Vulnerability Database (`https://vuln.go.dev`).\n\nВ отличие от тривиальных сканеров (Trivy, Snyk), которые просто сверяют версии в `go.mod` и выдают сотни ложных тревог, `govulncheck` проводит **статический анализ графа вызовов (Call Graph Analysis)**:\n- Он определяет, вызывается ли уязвимая функция/метод из библиотеки вашим собственным кодом.\n- Если уязвимый метод физически не используется, `govulncheck` помечает уязвимость как «неаффектирующую исполнение» (uncalled vulnerability).\n- Это снижает процент ложных срабатываний до минимума и позволяет блокировать CI только при реальной угрозе.",
    "step_by_step": "1. Установите `govulncheck`: `go install golang.org/x/vuln/cmd/govulncheck@latest`.\n2. Добавьте в GitHub Actions отдельную джобу `security-scan`.\n3. Запустите анализ исходного кода: `govulncheck ./...`.\n4. Настройте блокировку пайплайна при наличии вызываемых уязвимостей.",
    "code_blocks": [
      {
        "filename": ".github/workflows/govulncheck.yml",
        "lang": "yaml",
        "code": "name: Security Vulnerability Scan\n\non:\n  push:\n    branches: [ main ]\n  pull_request:\n    branches: [ main ]\n  schedule:\n    # Еженедельное сканирование зависимостей по понедельникам в 03:00 UTC\n    - cron: '0 3 * * 1'\n\njobs:\n  govulncheck:\n    name: Run Govulncheck\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - name: Setup Go\n        uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n\n      - name: Install and Run govulncheck\n        run: |\n          go install golang.org/x/vuln/cmd/govulncheck@latest\n          govulncheck ./..."
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\t_, _ = w.Write([]byte(\"Безопасный сервис без уязвимых зависимостей\"))\n\t})\n\n\tfmt.Println(\"Сервис запущен на :8080\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "`govulncheck` работает в три этапа:\n1. Загрузка минимальных метаданных об уязвимостях по протоколу HTTP из `vuln.go.dev` (кэшируются локально).\n2. Построение SSA (Static Single Assignment) представления кода программы с помощью пакета `golang.org/x/tools/go/ssa`.\n3. Анализ достижимости (Reachability Analysis) в графе вызовов программы от точки входа `main()` до уязвимых пакетов. Если путь в графе существует, выводится трассировка вызовов с указанием конкретной функции и рекомендации по обновлению версии.",
    "pitfalls": "1. Запуск сканирования только на Pull Request: новые уязвимости (0-day) в используемых библиотеках могут быть обнаружены через месяц после релиза. Поэтому обязателен еженедельный запуск по расписанию (`schedule: cron`).\n2. Игнорирование уязвимостей в стандартной библиотеке Go: `govulncheck` проверяет также версию компилятора Go; если версия рантайма устарела, он потребует обновить Go в CI.\n3. Паника разработчиков из-за непроверенных CVE в `go.mod`: использование обычных regex-сканеров приводит к частым ложным тревогам, тогда как `govulncheck` отсекает их на уровне графа вызовов.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему `govulncheck` точнее и эффективнее для Go-проектов, чем традиционные анализаторы уязвимостей вроде Trivy или Snyk?\n**Ответ:** Традиционные сканеры оперируют только манифестами зависимостей (`go.mod`/`go.sum`). Если библиотека содержит CVE в функции экспорта PDF, а проект использует из этой же библиотеки только утилиту парсинга дат, традиционный сканер заблокирует сборку (False Positive). \n`govulncheck` использует компиляторный анализ графа вызовов Go (SSA Reachability Analysis). Он знает реальный поток исполнения программы и бьет тревогу только в том случае, если байткод уязвимой функции может быть физически исполнен при работе приложения."
  }
]
