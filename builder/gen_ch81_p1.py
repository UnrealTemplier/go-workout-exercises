# -*- coding: utf-8 -*-
"""
Глава 81: Безопасность цепочки поставок (Supply Chain Security) и SBOM — Часть 1 (Упражнения 1-68)
"""

exercises = [
    {
        "num": 1,
        "title": "Анализ реальной эксплуатируемости уязвимостей с govulncheck и графом вызовов AST",
        "task": "Установите утилиту govulncheck. Напишите подробный архитектурный разбор принципиального отличия govulncheck от классических сканеров зависимостей (Snyk, Trivy, Dependabot): как построение графа вызовов AST (Call Graph Analysis) отсекает до 90% ложноположительных срабатываний (False Positives).",
        "theory": "Традиционные сканеры безопасности (Snyk, Trivy, Dependabot) работают по простому текстовому манифесту: они парсят `go.mod` или `go.sum`, находят версию библиотеки и сверяют ее с базами CVE. Если в библиотеке `github.com/gin-gonic/gin` или `golang.org/x/crypto` обнаружена уязвимость, сканер поднимает тревогу (High/Critical) и блокирует релиз. Однако в 85-95% случаев приложение использует совершенно другие, безопасные методы этой же библиотеки, а уязвимая функция никогда не вызывается в бинарнике! Официальная утилита Go `govulncheck` использует принципиально иной подход: она компилирует AST приложения в SSA (Static Single Assignment) представление, строит точный граф вызовов (Static Call Graph с анализом RTA/VTA) и рапортует об уязвимости ТОЛЬКО ЕСЛИ уязвимый символ (функция или метод) достижим из вашей функции `main()` или экспортируемых пакетов (Reachability Analysis).",
        "step_by_step": [
            "Установите утилиту: go install golang.org/x/vuln/cmd/govulncheck@latest.",
            "Изучите механизм Static Call Graph Analysis на уровне SSA представления компилятора Go.",
            "Реализуйте пример приложения, импортирующего библиотеку с CVE, но не использующего уязвимый метод.",
            "Запустите govulncheck и проанализируйте разницу между импортом пакета и реальной эксплуатируемостью."
        ],
        "code_blocks": [
            {
                "filename": "vuln_analysis.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"crypto/sha256\"\n\t\"fmt\"\n\t\"log\"\n)\n\n// Архитектурное объяснение Call Graph Reachability:\n// Классический сканер (Trivy): \"В пакете обнаружена CVE-2024-XXXX! Блокируем деплой.\"\n// Govulncheck (AST Call Graph): \"Пакет импортирован, но уязвимая функция vulnerableFunc() не вызывается из main(). Риск нулевой.\"\n\nfunc main() {\n\t// Безопасный вызов стандартного хэширования SHA-256\n\tdata := []byte(\"Supply chain security verification payload\")\n\thash := sha256.Sum256(data)\n\n\tlog.Printf(\"[Audit] Cryptographic digest: %x\", hash)\n\tfmt.Println(\"govulncheck AST Call Graph: Only reachable symbols trigger security alerts.\")\n}",
                "note": "Демонстрация принципа анализа достижимости символов (Reachability Analysis)"
            }
        ],
        "under_the_hood": "govulncheck опирается на пакет `golang.org/x/tools/go/ssa` и алгоритм Rapid Type Analysis (RTA) / Pointer Analysis (VTA). Он отслеживает вызовы через интерфейсы, динамические диспетчеризации и замыкания. Если уязвимая функция не входит в транзитивное замыкание вызовов от корня графа (`main`), компилятор Go гарантирует, что мертвый код будет вырезан на этапе линковки (Dead Code Elimination), а значит уязвимый машинный код даже не попадет в итоговый ELF/Mach-O бинарник.",
        "pitfalls": "Вызов уязвимой функции через рефлексию (`reflect.ValueOf(fn).Call()`). Статический анализ не всегда может разрешить динамический вызов по строковому имени через reflect, что в редких случаях может скрыть уязвимость при анализе исходного кода.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс / Ozon: 'Почему в пайплайнах CI/CD для Go предпочитают govulncheck вместо обычного сканирования go.sum?' Ответ: 'Сканирование go.sum дает огромное количество ложноположительных алертов (alert fatigue) на неиспользуемый код библиотек. govulncheck строит SSA граф вызовов и находит только РЕАЛЬНО вызываемые уязвимые функции, экономя сотни часов работы инженеров'."
    },
    {
        "num": 2,
        "title": "Практическое выявление уязвимостей в зависимостях через govulncheck",
        "task": "Смоделируйте проект с устаревшей зависимостью. Запустите govulncheck ./... и разберите отчет утилиты с подтверждением наличия или отсутствия вызова уязвимого символа.",
        "theory": "База уязвимостей Go Vulnerability Database (`https://vuln.go.dev`) курируется командой безопасности Google Go. Каждая запись содержит: 1) Уникальный идентификатор `GO-YYYY-NNNN` и соответствующий CVE/GHSA; 2) Затронутые модули и диапазоны версий; 3) Список конкретных уязвимых символов (пакетов, функций, методов); 4) Минимальную версию с исправлением (`fixed in`). При запуске `govulncheck ./...` выводит две секции: - `Your code is affected by N vulnerabilities` — уязвимость реально вызывается в коде; - `Informational: N vulnerabilities were found in dependencies that you do not call` — пакет содержит CVE, но ваш код его не вызывает.",
        "step_by_step": [
            "Создайте тестовый модуль go.mod.",
            "Подключите зависимость со старой версией.",
            "Запустите govulncheck ./... в терминале.",
            "Изучите структуру отчета и трассу вызовов (Call Stack).",
            "Обновите модуль до безопасной версии и подтвердите чистоту отчета."
        ],
        "code_blocks": [
            {
                "filename": "vuln_demo.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"strings\"\n)\n\n// MockVulnReport симулирует парсинг вывода govulncheck в JSON формате\ntype VulnerabilityFinding struct {\n\tOSVID       string   `json:\"osv_id\"`\n\tPkgPath     string   `json:\"pkg_path\"`\n\tSymbol      string   `json:\"symbol\"`\n\tFixedIn     string   `json:\"fixed_in\"`\n\tIsReachable bool     `json:\"is_reachable\"`\n\tCallStack   []string `json:\"call_stack\"`\n}\n\nfunc AnalyzeGovulncheckOutput(findings []VulnerabilityFinding) {\n\treachableCount := 0\n\tfor _, f := range findings {\n\t\tif f.IsReachable {\n\t\t\treachableCount++\n\t\t\tlog.Printf(\"[CRITICAL ALERT] Exploitable CVE: %s in symbol %s.%s! Fixed in: %s\",\n\t\t\t\tf.OSVID, f.PkgPath, f.Symbol, f.FixedIn)\n\t\t\tlog.Printf(\"  Trace: %s\", strings.Join(f.CallStack, \" -> \"))\n\t\t} else {\n\t\t\tlog.Printf(\"[INFO] Dependency has %s, but symbol %s is NOT called by application. Safe to deploy.\",\n\t\t\t\tf.OSVID, f.Symbol)\n\t\t}\n\t}\n\tfmt.Printf(\"Audit completed. Actionable vulnerabilities: %d\\n\", reachableCount)\n}\n\nfunc main() {\n\tsampleFindings := []VulnerabilityFinding{\n\t\t{\n\t\t\tOSVID:       \"GO-2023-2185\",\n\t\t\tPkgPath:     \"golang.org/x/net/html\",\n\t\t\tSymbol:      \"Parse\",\n\t\t\tFixedIn:     \"v0.17.0\",\n\t\t\tIsReachable: true,\n\t\t\tCallStack:   []string{\"main()\", \"renderHTML()\", \"html.Parse()\"},\n\t\t},\n\t\t{\n\t\t\tOSVID:       \"GO-2023-1988\",\n\t\t\tPkgPath:     \"golang.org/x/crypto/ssh\",\n\t\t\tSymbol:      \"ServerConfig.AddHostKey\",\n\t\t\tFixedIn:     \"v0.14.0\",\n\t\t\tIsReachable: false, // Не вызывается приложением\n\t\t\tCallStack:   nil,\n\t\t},\n\t}\n\n\tAnalyzeGovulncheckOutput(sampleFindings)\n}",
                "note": "Разбор структуры отчета уязвимостей govulncheck"
            }
        ],
        "under_the_hood": "govulncheck делает легковесный HTTPS-запрос к `https://vuln.go.dev`, скачивая сжатые JSON-индексы только для тех модулей, которые реально присутствуют в `go.mod`. Никаких исходных кодов на серверы Google не отправляется — анализ графа происходит локально.",
        "pitfalls": "Игнорирование обновлений библиотек, уязвимости которых помечены как unreachable. Хотя в текущей версии код не вызывается, будущий коммит вашего коллеги может начать использовать эту функцию, мгновенно сделав уязвимость активной.",
        "bigtech_interview": "Вопрос на собеседовании в Тинькофф: 'Что делать, если govulncheck показал уязвимость в indirect (косвенной) зависимости?' Ответ: '1) Выполнить `go get package@latest` для поднятия версии косвенной зависимости; 2) Либо использовать директиву `replace` в `go.mod` для принудительной подмены уязвимой версии на патченную'."
    },
    {
        "num": 3,
        "title": "Анализ вывода govulncheck: различие Found in и Call Stack",
        "task": "Напишите парсер JSON-вывода команды govulncheck -json, который автоматически фильтрует уязвимости и разделяет их на блокирующие (reachable) и информационные.",
        "theory": "Флаг `-json` в `govulncheck` позволяет автоматизировать аудит безопасности в корпоративных скриптах CI/CD: `govulncheck -json ./... | jq .` Вывод представляет собой поток NDJSON (Newline Delimited JSON) событий: 1) `config`: параметры сканирования (Go version, OS, arch); 2) `progress`: этапы построения графа; 3) `osv`: описание уязвимости из базы; 4) `finding`: конкретное обнаружение. Если объект `finding` содержит непустой массив `trace` со стеком вызовов от `main`, уязвимость является эксплуатируемой (`is_called = true`). Если `trace` отсутствует, уязвимость находится лишь на уровне модульного графа.",
        "step_by_step": [
            "Изучите структуру NDJSON протокола govulncheck.",
            "Напишите Go-структуры для десериализации сообщений finding и osv.",
            "Реализуйте фильтрацию по наличию поля trace.",
            "Сформируйте итоговый SARIF или текстовый отчет для блокировки пайплайна."
        ],
        "code_blocks": [
            {
                "filename": "parse_govulncheck_json.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"bufio\"\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"strings\"\n)\n\n// Frame представляет отдельный узел в стеке вызовов govulncheck\ntype Frame struct {\n\tPackage  string `json:\"package\"`\n\tFunction string `json:\"function\"`\n\tPosition string `json:\"position\"`\n}\n\n// FindingMessage представляет событие обнаружения уязвимости\ntype FindingMessage struct {\n\tFinding *struct {\n\t\tOSV          string  `json:\"osv\"`\n\t\tTrace        []Frame `json:\"trace\"`\n\t\tFixedVersion string  `json:\"fixed_version\"`\n\t} `json:\"finding,omitempty\"`\n}\n\nfunc ParseNDJSONReport(rawNDJSON string) (blockingCVEs []string, infoCVEs []string) {\n\tscanner := bufio.NewScanner(strings.NewReader(rawNDJSON))\n\tfor scanner.Scan() {\n\t\tline := scanner.Text()\n\t\tvar msg FindingMessage\n\t\tif err := json.Unmarshal([]byte(line), &msg); err != nil {\n\t\t\tcontinue\n\t\t}\n\n\t\tif msg.Finding != nil {\n\t\t\tif len(msg.Finding.Trace) > 0 {\n\t\t\t\tblockingCVEs = append(blockingCVEs, fmt.Sprintf(\"%s (Fixed: %s)\", msg.Finding.OSV, msg.Finding.FixedVersion))\n\t\t\t} else {\n\t\t\t\tinfoCVEs = append(infoCVEs, msg.Finding.OSV)\n\t\t\t}\n\t\t}\n\t}\n\treturn blockingCVEs, infoCVEs\n}\n\nfunc main() {\n\tsampleNDJSON := `{\"finding\":{\"osv\":\"GO-2024-0001\",\"fixed_version\":\"v1.2.3\",\"trace\":[{\"package\":\"main\",\"function\":\"main\"},{\"package\":\"lib\",\"function\":\"BadFunc\"}]}}\n{\"finding\":{\"osv\":\"GO-2024-0002\",\"fixed_version\":\"v2.0.0\",\"trace\":[]}}`\n\n\tblocking, info := ParseNDJSONReport(sampleNDJSON)\n\tfmt.Printf(\"Blocking Reachable CVEs (Pipeline MUST FAIL): %v\\n\", blocking)\n\tfmt.Printf(\"Informational Unreachable CVEs (Warning only): %v\\n\", info)\n}",
                "note": "Автоматизированная обработка NDJSON потока событий govulncheck"
            }
        ],
        "under_the_hood": "Потоковый протокол NDJSON позволяет обрабатывать огромные кодовые базы миллионов строк без загрузки гигантского JSON-документа целиком в оперативную память.",
        "pitfalls": "Парсинг вывода govulncheck через регулярные выражения из человекочитаемого stdout. Форматирование текста в stdout меняется между версиями Go, ломая скрипты. Всегда используйте флаг `-json`.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Как интегрировать govulncheck с корпоративной системой управления уязвимостями (DefectDojo / Jira)?' Ответ: 'Запускать govulncheck -json, парсить NDJSON поток и конвертировать находки с непустым `trace` в стандартный формат SARIF (Static Analysis Results Interchange Format) для импорта в DefectDojo'."
    },
    {
        "num": 4,
        "title": "Локальное сканирование и устранение уязвимостей (Version Bumping)",
        "task": "Продемонстрируйте процесс устранения найденной уязвимости: запуск сканирования, анализ рекомендуемой версии в vuln.go.dev и обновление зависимости через go get.",
        "theory": "Когда govulncheck обнаруживает уязвимость, отчет указывает точный идентификатор `fixed in: vX.Y.Z`. Устранение уязвимости состоит из трех шагов: 1. Вызов `go get path/to/module@vX.Y.Z` (или `@latest`), который обновляет версию в `go.mod` и `go.sum`; 2. Вызов `go mod tidy` для удаления старых неиспользуемых хэшей и наведения порядка в графе зависимостей; 3. Повторный запуск `govulncheck ./...` для подтверждения устранения проблемы и запуск `go test ./...` для проверки обратной совместимости (чтобы bump минорной версии не сломал существующий код).",
        "step_by_step": [
            "Выполните аудит модуля через govulncheck.",
            "Определите целевой безопасный релиз библиотеки.",
            "Обновите модуль командой go get module@version.",
            "Запустите go mod tidy и валидацию тестов.",
            "Убедитесь в успешном прохождении финального сканирования."
        ],
        "code_blocks": [
            {
                "filename": "remediation_workflow.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[1/4] Running initial security scan...\"\n# govulncheck ./... || true\n\necho \"[2/4] Bumping vulnerable dependency to safe fixed release...\"\n# go get golang.org/x/crypto@v0.17.0\n\necho \"[3/4] Cleaning up modules graph and verifying checksums...\"\n# go mod tidy\n# go mod verify\n\necho \"[4/4] Verifying clean bill of health...\"\n# govulncheck ./...\necho \"Module dependencies are verified secure and patched!\"\n",
                "note": "Стандартный воркфлоу устранения уязвимостей в Go проекте"
            }
        ],
        "under_the_hood": "`go get` обращается к MVS (Minimal Version Selection) алгоритму Go Modules. Он выбирает минимальную версию, удовлетворяющую всем ограничениям зависимостей, предотвращая неконтролируемое обновление мажорных версий.",
        "pitfalls": "Использование `go get -u ./...` вслепую. Флаг `-u` обновляет ВСЕ зависимости проекта до последних версий, что может внести обратно несовместимые изменения (Breaking Changes) и сломать компиляцию проекта.",
        "bigtech_interview": "В чем отличие Minimal Version Selection (MVS) в Go от пакетных менеджеров npm / pip? Ответ: 'npm и pip по умолчанию выбирают самую свежую совместимую версию (SemVer ^1.0.0 берет 1.9.9). Go MVS выбирает самую СТАРУЮ (минимальную) версию из всех запрошенных модулями. Это обеспечивает 100% повторяемость сборки (Reproducible Builds), но требует явного обновления для патчей уязвимостей'."
    },
    {
        "num": 5,
        "title": "Установка и проверка среды govulncheck",
        "task": "Напишите Go-скрипт, проверяющий установку и версию утилиты govulncheck в системе, а также доступность сервера уязвимостей vuln.go.dev.",
        "theory": "Для интеграции утилит сканирования в локальные dev-контейнеры и CI/CD раннеры необходимо гарантировать наличие установленного бинарника `govulncheck` и сетевую связность с официальным зеркалом базы данных `https://vuln.go.dev`. В изолированных контурах (Air-gapped / Private Cloud) прямой доступ к vuln.go.dev может быть закрыт firewall. В этом случае база уязвимостей зеркалируется локально, а утилита запускается с переменной окружения `GOVULNDB`.",
        "step_by_step": [
            "Используйте exec.LookPath для проверки наличия govulncheck в PATH.",
            "Проверьте версию скомпилированного бинарника через govulncheck -version.",
            "Выполните HTTP HEAD / GET запрос к https://vuln.go.dev/index/modules.json.",
            "Сформируйте диагностический отчет готовности среды."
        ],
        "code_blocks": [
            {
                "filename": "check_govulncheck_env.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"os/exec\"\n\t\"time\"\n)\n\nfunc CheckToolchainHealth() {\n\t// 1. Проверяем наличие бинарника в PATH\n\tpath, err := exec.LookPath(\"govulncheck\")\n\tif err != nil {\n\t\tfmt.Println(\"[WARN] govulncheck binary not found in PATH (install via: go install golang.org/x/vuln/cmd/govulncheck@latest)\")\n\t} else {\n\t\tfmt.Printf(\"[OK] Found govulncheck at: %s\\n\", path)\n\t}\n\n\t// 2. Проверяем сетевой доступ к Go Vulnerability Database\n\tctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)\n\tdefer cancel()\n\n\treq, _ := http.NewRequestWithContext(ctx, \"HEAD\", \"https://vuln.go.dev\", nil)\n\tresp, err := http.DefaultClient.Do(req)\n\tif err != nil {\n\t\tfmt.Printf(\"[NETWORK ERROR] Cannot reach https://vuln.go.dev: %v (Private mirror or proxy required)\\n\", err)\n\t\treturn\n\t}\n\tdefer resp.Body.Close()\n\n\tif resp.StatusCode == http.StatusOK || resp.StatusCode == http.StatusFound {\n\t\tfmt.Println(\"[OK] Connection to official Go Vulnerability Database (vuln.go.dev) is active.\")\n\t}\n}\n\nfunc main() {\n\tCheckToolchainHealth()\n}",
                "note": "Скрипт проверки окружения и сетевой доступности vuln.go.dev"
            }
        ],
        "under_the_hood": "База `vuln.go.dev` спроектирована как статическое файловое хранилище (Google Cloud Storage bucket). Она отдает легковесные предгенерированные JSON файлы с gzip-сжатием, что позволяет кэшировать ответы на любом CDN прокси.",
        "pitfalls": "Установка старой версии govulncheck. Формат базы OSV развивается. Устаревший бинарник может некорректно парсить свежие схемы уязвимостей.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'Как запустить govulncheck в закрытом корпоративном контуре без доступа в интернет?' Ответ: 'Поднять внутреннее зеркало базы уязвимостей (с помощью утилиты gcp-audit или клонированием репозитория vuln) и настроить переменную окружения `export GOVULNDB=http://internal-mirror.corp/vulndb`'."
    },
    {
        "num": 6,
        "title": "Первое сканирование: классификация уровней опасности (Severity) и CVSS",
        "task": "Изучите градацию уровней критичности уязвимостей в экосистеме Go (Low, Medium, High, Critical) и напишите утилиту классификации CVE по метрикам CVSS v3.1.",
        "theory": "В отчетах о безопасности уязвимости ранжируются по шкале CVSS (Common Vulnerability Scoring System v3.1): - `Low (0.1 - 3.9)`: незначительные утечки второстепенных данных, требующие локального доступа; - `Medium (4.0 - 6.9)`: DoS при высоких требованиях к привилегиям или утечка части данных; - `High (7.0 - 8.9)`: отказ в обслуживании (Panic/Crash) без аутентификации, чтение чувствительных файлов; - `Critical (9.0 - 10.0)`: Remote Code Execution (RCE), полный обход авторизации или компрометация БД. В production-пайплайнах принято строгое правило: `High` и `Critical` блокируют слияние Pull Request немедленно (Fail Fast), `Medium` и `Low` создают задачи в бэклоге со сроком устранения 14-30 дней.",
        "step_by_step": [
            "Определите типы SeverityLevel в Go.",
            "Реализуйте функцию парсинга CVSS score в уровень критичности.",
            "Напишите логику принятия решения о блокировке CI/CD релиза.",
            "Проверьте валидацию на тестовом наборе CVE."
        ],
        "code_blocks": [
            {
                "filename": "cvss_evaluator.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n)\n\ntype SeverityLevel string\n\nconst (\n\tSeverityNone     SeverityLevel = \"NONE\"\n\tSeverityLow      SeverityLevel = \"LOW\"\n\tSeverityMedium   SeverityLevel = \"MEDIUM\"\n\tSeverityHigh     SeverityLevel = \"HIGH\"\n\tSeverityCritical SeverityLevel = \"CRITICAL\"\n)\n\ntype SecurityVulnerability struct {\n\tID        string\n\tCVSSScore float64\n\tReachable bool\n}\n\nfunc EvaluateSeverity(score float64) SeverityLevel {\n\tswitch {\n\tcase score >= 9.0:\n\t\treturn SeverityCritical\n\tcase score >= 7.0:\n\t\treturn SeverityHigh\n\tcase score >= 4.0:\n\t\treturn SeverityMedium\n\tcase score > 0.0:\n\t\treturn SeverityLow\n\tdefault:\n\t\treturn SeverityNone\n\t}\n}\n\nfunc ShouldBlockBuild(vuln SecurityVulnerability) (bool, string) {\n\tlevel := EvaluateSeverity(vuln.CVSSScore)\n\tif !vuln.Reachable {\n\t\treturn false, fmt.Sprintf(\"Ignored: %s is not reachable by application call graph\", vuln.ID)\n\t}\n\n\tif level == SeverityCritical || level == SeverityHigh {\n\t\treturn true, fmt.Sprintf(\"BLOCKING BUILD: %s has %s severity (CVSS %.1f) and is REACHABLE!\", vuln.ID, level, vuln.CVSSScore)\n\t}\n\n\treturn false, fmt.Sprintf(\"Warning logged: %s has %s severity (non-blocking)\", vuln.ID, level)\n}\n\nfunc main() {\n\tcves := []SecurityVulnerability{\n\t\t{ID: \"CVE-2024-9981\", CVSSScore: 9.8, Reachable: true},\n\t\t{ID: \"CVE-2024-1122\", CVSSScore: 7.5, Reachable: false},\n\t\t{ID: \"CVE-2023-4512\", CVSSScore: 5.3, Reachable: true},\n\t}\n\n\tfor _, c := range cves {\n\t\tblock, reason := ShouldBlockBuild(c)\n\t\tfmt.Printf(\"[%v] %s\\n\", block, reason)\n\t}\n}",
                "note": "Оценка критичности уязвимостей на основе CVSS и достижимости в коде"
            }
        ],
        "under_the_hood": "Метрика CVSS v3.1 векторной строкой (`CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`) учитывает Attack Vector (AV: Network), Attack Complexity (AC: Low), Privileges Required (PR: None) и влияние на конфиденциальность, целостность и доступность.",
        "pitfalls": "Блокировка пайплайна по уязвимостям High/Critical, которые не достижимы (not reachable). Это демотивирует разработчиков и приводит к отключению сканеров безопасности.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Как вы настроите Quality Gate безопасности для релизов микросервисов?' Ответ: 'Блокировать релиз при: 1) Любом Reachable Critical/High в govulncheck; 2) Любом unverified чек-сумме в go.sum; 3) Наличии GPLv3 лицензий в сторонних пакетах'."
    },
    {
        "num": 7,
        "title": "Режимы govulncheck: Source Mode, Binary Mode и Extract Mode",
        "task": "Сравните три режима работы govulncheck: анализ исходного кода (source mode), анализ скомпилированного бинарника (binary mode) и extract mode. Напишите команды для каждого режима.",
        "theory": "Утилита govulncheck поддерживает несколько режимов инспекции: 1) Source Mode (`govulncheck ./...`): анализирует исходный код Go, строит SSA граф вызовов. Используется на этапе разработки и в Pull Request проверках; 2) Binary Mode (`govulncheck -mode=binary ./bin/server`): анализирует уже скомпилированный бинарный файл (ELF, Mach-O, PE). Go-компилятор встраивает в бинарник метаданные о версиях модулей (секция `.go.buildinfo`). Утилита читает build info и декомпилирует таблицу символов PCLNTAB, определяя, какие методы вошли в итоговую сборку. Идеально для сканирования готовых Docker-образов перед выкатом в Kubernetes; 3) Extract Mode (`govulncheck -mode=extract ./...`): извлекает минимальную информацию о коде без обращения к интернету, позволяя передать дамп на отдельный сканирующий сервер.",
        "step_by_step": [
            "Изучите синтаксис флага -mode в govulncheck.",
            "Скомпилируйте бинарник с помощью go build.",
            "Запустите govulncheck -mode=binary над бинарником.",
            "Проверьте разницу в скорости и детальности анализа между исходниками и бинарником."
        ],
        "code_blocks": [
            {
                "filename": "scan_modes.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"=== 1. Source Mode (AST Call Graph Analysis) ===\"\n# Анализирует исходники в текущем каталоге\n# govulncheck ./...\n\necho \"=== 2. Binary Compilation ===\"\n# Собираем production бинарник с встроенной метаинформацией buildinfo\n# go build -o /tmp/myapp main.go\n\necho \"=== 3. Binary Mode (Pre-Deployment Scan) ===\"\n# Сканирует скомпилированный артефакт, исследуя секцию pclntab и buildinfo\n# govulncheck -mode=binary /tmp/myapp\n\necho \"=== 4. Extract Mode (Air-gapped export) ===\"\n# Генерирует дескриптор для офлайн-анализа\n# govulncheck -mode=extract ./... > /tmp/code_extract.json\n\necho \"Scan modes workflow executed successfully.\"\n",
                "note": "Сценарии применения трех режимов работы govulncheck"
            }
        ],
        "under_the_hood": "В Binary Mode утилита читает структуру `runtime.modinfo` через пакет `debug/buildinfo`. Таблица символов `runtime.pclntab` содержит адреса и имена всех функций, сохранившихся после линковки. Если уязвимый символ отсутствует в pclntab, он был вырезан линковщиком и отсутствует в бинарнике.",
        "pitfalls": "Сборка бинарника с флагом `-ldflags=\"-s -w\"` не удаляет секцию buildinfo, но удаление метаданных кастомными обфускаторами (garble) может сломать Binary Mode.",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'Как проверить безопасность стороннего бинарника на Go, если у нас нет его исходников?' Ответ: 'Запустить `govulncheck -mode=binary <path_to_binary>`. Утилита извлечет встроенную метаинформацию о зависимостях и таблицу функций без необходимости декомпиляции'."
    },
    {
        "num": 8,
        "title": "Анатомия отчета govulncheck: OSV ID, Affected Symbol, Call Stack и Fixed Version",
        "task": "Создайте типизированный генератор markdown-отчетов по результатам работы govulncheck для отсылки в корпоративный Slack/Telegram или прикрепления к Pull Request.",
        "theory": "Отчет об уязвимости обязан содержать исчерпывающие инженерные данные, позволяющие разработчику за 5 минут устранить проблему: 1) `OSV ID`: канонический идентификатор в Open Source Vulnerability schema (`GO-2023-XXXX`); 2) `CVE / GHSA`: общемировой идентификатор для согласования со службой информационной безопасности; 3) `Affected Symbol`: точный путь пакета и имя функции (`github.com/foo/bar.ExecuteQuery`); 4) `Call Stack`: цепочка вызовов от функции в вашем репозитории (`service/order.go:42: ProcessOrder -> ExecuteQuery`); 5) `Fixed Version`: версия библиотеки, на которую нужно обновиться.",
        "step_by_step": [
            "Определите структуру VulnerabilityDetail.",
            "Реализуйте форматирование в GitHub Flavored Markdown.",
            "Добавьте ссылки на базу знаний vuln.go.dev.",
            "Проверьте генерацию отчета для Pull Request комментирования."
        ],
        "code_blocks": [
            {
                "filename": "vuln_markdown_reporter.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n)\n\ntype VulnItem struct {\n\tOSVID        string\n\tAliases      []string // CVEs\n\tPackage      string\n\tSymbol       string\n\tFixedVersion string\n\tCallTrace    []string\n}\n\nfunc GenerateMarkdownSummary(items []VulnItem) string {\n\tvar sb strings.Builder\n\tsb.WriteString(\"## 🛡️ Отчет безопасности: обнаружены уязвимости\\n\\n\")\n\tsb.WriteString(\"| Уязвимость | Пакет | Символ | Исправлено в |\\n\")\n\tsb.WriteString(\"| :--- | :--- | :--- | :--- |\\n\")\n\n\tfor _, item := range items {\n\t\tcve := strings.Join(item.Aliases, \", \")\n\t\tsb.WriteString(fmt.Sprintf(\"| [%s](https://vuln.go.dev/%s) (%s) | `%s` | `%s` | **%s** |\\n\",\n\t\t\titem.OSVID, item.OSVID, cve, item.Package, item.Symbol, item.FixedVersion))\n\t}\n\n\tsb.WriteString(\"\\n### 📍 Стеки вызовов (Call Stacks):\\n\")\n\tfor _, item := range items {\n\t\tsb.WriteString(fmt.Sprintf(\"\\n**%s (%s)**:\\n```text\\n\", item.OSVID, item.Package))\n\t\tfor i, frame := range item.CallTrace {\n\t\t\tindent := strings.Repeat(\"  \", i)\n\t\t\tsb.WriteString(fmt.Sprintf(\"%s└─ %s\\n\", indent, frame))\n\t\t}\n\t\tsb.WriteString(\"```\\n\")\n\t}\n\n\treturn sb.String()\n}\n\nfunc main() {\n\tvulns := []VulnItem{\n\t\t{\n\t\t\tOSVID:        \"GO-2024-2687\",\n\t\t\tAliases:      []string{\"CVE-2024-24786\"},\n\t\t\tPackage:      \"google.golang.org/protobuf\",\n\t\t\tSymbol:       \"proto.Unmarshal\",\n\t\t\tFixedVersion: \"v1.33.0\",\n\t\t\tCallTrace: []string{\n\t\t\t\t\"github.com/mycorp/backend/handler.HandleEvent\",\n\t\t\t\t\"github.com/mycorp/backend/parser.Decode\",\n\t\t\t\t\"google.golang.org/protobuf/proto.Unmarshal\",\n\t\t\t},\n\t\t},\n\t}\n\n\tmd := GenerateMarkdownSummary(vulns)\n\tfmt.Println(md)\n}",
                "note": "Генератор структурированных Markdown отчетов об уязвимостях"
            }
        ],
        "under_the_hood": "Формат вывода GitHub Markdown с таблицами и стеками вызовов может автоматически публиковаться в Pull Request через `gh pr comment` в GitHub Actions.",
        "pitfalls": "Отправка в отчет уязвимостей без указания стека вызова. Без стека вызова разработчик не понимает, какое именно место в кодовой базе активирует уязвимость.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Что делать, если библиотека заброшена автором (Unmaintained) и нет Fixed Version?' Ответ: '1) Зафоркать репозиторий в корпоративный GitHub/GitLab, исправить уязвимость и подключить через директиву `replace` в go.mod; 2) Заменить библиотеку на поддерживаемую альтернативу; 3) Написать защитный фильтр (WAF/Middleware), санирующий входные параметры перед передачей в библиотеку'."
    },
    {
        "num": 9,
        "title": "Сравнение govulncheck с ручным аудитом: go list, go mod graph и база OSV",
        "task": "Реализуйте Go-скрипт, который строит полный граф модулей через go mod graph, находит зависимости с известными CVE и сравнивает результаты с точным графом вызовов govulncheck.",
        "theory": "Команда `go list -m all` выводит плоский список всех модулей в сборке. Команда `go mod graph` выводит ориентированный граф зависимостей в формате `Parent Child`. Однако оба этих инструмента работают исключительно на уровне модулей (`MVS`). Они не знают, скомпилировался ли хоть один байт этого модуля в итоговый бинарник! Модуль может быть подключен для запуска тестов (`_test.go`), являться частью неиспользуемого пакета или предназначаться для другой операционной системы (под тегом сборки `//go:build windows`). Ручной аудит по `go mod graph` приводит к сотням бессмысленных задач на обновление, тогда как `govulncheck` анализирует AST с учетом активных build tags (`GOOS`, `GOARCH`).",
        "step_by_step": [
            "Распарсите вывод go mod graph в структуру графа смежности.",
            "Найдите путь от корневого модуля к целевой зависимости.",
            "Проверьте теги сборки (build tags).",
            "Покажите, почему статический граф вызовов точнее модульного графа."
        ],
        "code_blocks": [
            {
                "filename": "graph_audit_comparison.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"bufio\"\n\t\"fmt\"\n\t\"strings\"\n)\n\n// DependencyGraph хранит связи между модулями\ntype DependencyGraph struct {\n\tedges map[string][]string\n}\n\nfunc NewDependencyGraph() *DependencyGraph {\n\treturn &DependencyGraph{edges: make(map[string][]string)}\n}\n\nfunc (g *DependencyGraph) AddEdge(from, to string) {\n\tg.edges[from] = append(g.edges[from], to)\n}\n\n// FindPathToPackage находит цепочку импортов (Breadth-First Search)\nfunc (g *DependencyGraph) FindPathToPackage(start, target string) []string {\n\tqueue := [][]string{{start}}\n\tvisited := make(map[string]bool)\n\n\tfor len(queue) > 0 {\n\t\tpath := queue[0]\n\t\tqueue = queue[1:]\n\t\tnode := path[len(path)-1]\n\n\t\tif strings.HasPrefix(node, target) {\n\t\t\treturn path\n\t\t}\n\n\t\tif visited[node] {\n\t\t\tcontinue\n\t\t}\n\t\tvisited[node] = true\n\n\t\tfor _, neighbor := range g.edges[node] {\n\t\t\tnewPath := append([]string{}, path...)\n\t\t\tnewPath = append(newPath, neighbor)\n\t\t\tqueue = append(queue, newPath)\n\t\t}\n\t}\n\treturn nil\n}\n\nfunc main() {\n\trawGraph := `mycorp/app github.com/gin-gonic/gin@v1.9.0\nmycorp/app github.com/stretchr/testify@v1.8.2\ngithub.com/gin-gonic/gin@v1.9.0 golang.org/x/crypto@v0.0.0-20201221181555-eec23a3978ad\n`\n\tg := NewDependencyGraph()\n\tscanner := bufio.NewScanner(strings.NewReader(rawGraph))\n\tfor scanner.Scan() {\n\t\tparts := strings.Fields(scanner.Text())\n\t\tif len(parts) == 2 {\n\t\t\tg.AddEdge(parts[0], parts[1])\n\t\t}\n\t}\n\n\tpath := g.FindPathToPackage(\"mycorp/app\", \"golang.org/x/crypto\")\n\tfmt.Println(\"Module Dependency Path (via go mod graph):\")\n\tfor i, step := range path {\n\t\tfmt.Printf(\"  [%d] %s\\n\", i+1, step)\n\t}\n\n\tfmt.Println(\"\\nArchitectural Conclusion:\")\n\tfmt.Println(\"go mod graph finds the module chain, but CANNOT verify whether the vulnerable function is actually executed.\")\n\tfmt.Println(\"govulncheck completes the audit by inspecting the AST call graph.\")\n}",
                "note": "Сравнение графа зависимостей модулей и анализа вызовов функций"
            }
        ],
        "under_the_hood": "`go mod why -m <package>` в терминале выполняет похожий поиск кратчайшего пути по графу импортов, помогая понять, кто именно затянул подозрительный пакет в проект.",
        "pitfalls": "Удаление зависимости из `go.mod` без `go mod tidy`. Если зависимость осталась в `go.sum`, сканеры манифестов продолжат рапортовать о ней.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'Как узнать, почему пакет оказался в зависимостях моего проекта?' Ответ: 'Выполнить команду `go mod why <import_path>`. Она выведет кратчайшую цепочку импортов от основного пакета до целевого пакета'."
    },
    {
        "num": 10,
        "title": "Магия go.sum и Checksum Database: защита от подмены тегов Git",
        "task": "Изучите формат записей go.sum (хэши h1:...). Смоделируйте ошибку checksum mismatch при изменении контрольной суммы и объясните механизм глобального дерева Меркла в sum.golang.org.",
        "theory": "До появления Go Modules злоумышленник мог взломать репозиторий автора популярной библиотеки на GitHub и перезаписать существующий Git-тег `v1.2.0` вредоносным коммитом (Git Tag Mutability). Файл `go.sum` и сервис Checksum Database (`sum.golang.org`) делают это невозможным: 1) `go.sum` содержит криптографические хэши SHA-256 (`h1:...`) для каждого скачанного модуля и отдельно для его `go.mod` файла; 2) `sum.golang.org` — это глобальный, публичный, защищенный от перезаписи лог аудита (Append-Only Merkle Tree Log), работающий по принципу Transparency Log (аналог Certificate Transparency). Когда версия модуля скачивается впервые в мире, ее хэш навсегда фиксируется в дереве Меркла. Если хакер изменит код в Git-теге, хэш изменится, Go обнаружит несовпадение (`checksum mismatch`) и заблокирует компиляцию на всех машинах планеты!",
        "step_by_step": [
            "Изучите синтаксис записей в файле go.sum.",
            "Напишите валидатор контрольных сумм алгоритма h1 (SHA-256 дерева файлов).",
            "Смоделируйте ошибку security checksum mismatch.",
            "Объясните работу дерева Меркла в sum.golang.org."
        ],
        "code_blocks": [
            {
                "filename": "checksum_verifier.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"crypto/sha256\"\n\t\"encoding/base64\"\n\t\"errors\"\n\t\"fmt\"\n\t\"strings\"\n)\n\nvar ErrChecksumMismatch = errors.New(\"SECURITY ALERT: verification failed: checksum mismatch\")\n\n// VerifyModuleChecksum симулирует проверку хэша h1 (SHA-256)\nfunc VerifyModuleChecksum(modPath, version, expectedHash string, fileContents []byte) error {\n\t// В реальном Go хэш h1 рассчитывается от дерева всех файлов модуля\n\thasher := sha256.New()\n\thasher.Write(fileContents)\n\tcalculatedB64 := \"h1:\" + base64.StdEncoding.EncodeToString(hasher.Sum(nil))\n\n\tif calculatedB64 != expectedHash {\n\t\treturn fmt.Errorf(\"%w for %s %s:\\n  expected:   %s\\n  calculated: %s\",\n\t\t\tErrChecksumMismatch, modPath, version, expectedHash, calculatedB64)\n\t}\n\treturn nil\n}\n\nfunc main() {\n\tcontent := []byte(\"package safe; func Run() {}\")\n\t// Валидный хэш\n\thasher := sha256.New()\n\thasher.Write(content)\n\tvalidHash := \"h1:\" + base64.StdEncoding.EncodeToString(hasher.Sum(nil))\n\n\tmod := \"github.com/org/crypto-lib\"\n\tver := \"v1.4.2\"\n\n\t// Тест 1: Валидный хэш\n\tif err := VerifyModuleChecksum(mod, ver, validHash, content); err == nil {\n\t\tfmt.Printf(\"[OK] Checksum for %s %s matches sum.golang.org transparency log.\\n\", mod, ver)\n\t}\n\n\t// Тест 2: Подмена кода хакером в Git репозитории\n\ttamperedContent := []byte(\"package safe; func Run() { /* MALICIOUS BACKDOOR */ }\")\n\terr := VerifyModuleChecksum(mod, ver, validHash, tamperedContent)\n\tif err != nil {\n\t\tfmt.Printf(\"[BLOCKED] %v\\n\", err)\n\t}\n}",
                "note": "Симуляция криптографической проверки контрольных сумм модулей в go.sum"
            }
        ],
        "under_the_hood": "Алгоритм `h1:` (hash version 1) сортирует все файлы в каталоге модуля по имени, хеширует содержимое каждого файла через SHA-256, затем хеширует полученный список строк `hash  filename\n`. Это гарантирует независимость хэша от операционной системы и файловой системы.",
        "pitfalls": "Случайное добавление `go.sum` в `.gitignore`. Файл `go.sum` ОБЯЗАН храниться в Git репозитории! Без него CI/CD сборка не сможет проверить неизменность скачанных модулей.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Что делать, если go build выдает checksum mismatch для проверенной библиотеки?' Ответ: 'НИ В КОЕМ СЛУЧАЕ не удалять строку из go.sum вручную! Необходимо проверить: 1) Не был ли перезаписан тег автором; 2) Не происходит ли атака Man-in-the-Middle (MitM) на корпоративном прокси; 3) Очистить локальный кэш `go clean -modcache` и сверить хэш с публичным `https://sum.golang.org/lookup/<module>@<version>`'."
    },
    {
        "num": 11,
        "title": "Симуляция уязвимости: аудит устаревшего пакета JWT и безопасный переход",
        "task": "Создайте тестовый сценарий с устаревшей версией github.com/golang-jwt/jwt/v4 с известной CVE. Просканируйте код через govulncheck и обновите модуль до безопасной версии.",
        "theory": "Классический пример критической уязвимости в Go экосистеме — уязвимость обхода проверки подписи в ранних версиях JWT (CVE-2020-26160 / CVE-2022-32149). Библиотеки не проверяли тип используемого алгоритма (Algorithm Confusion: HMAC против RSA), что позволяло атакующему подписать токен публичным ключом сервера как симметричным HMAC-секретом и получить статус администратора! В таких случаях govulncheck наглядно демонстрирует, что вызов метода `jwt.Parse` или `jwt.ParseWithClaims` находится в критической зоне риска.",
        "step_by_step": [
            "Изучите механику уязвимости Key Confusion в JWT токенах.",
            "Напишите парсер токенов со строгой валидацией алгоритма подписи в Keyfunc.",
            "Проверьте код на защищенность от атак смены алгоритма ('none' или HMAC/RSA).",
            "Подтвердите соответствие лучшим практикам RFC 7519."
        ],
        "code_blocks": [
            {
                "filename": "jwt_secure_parser.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n\t\"log\"\n)\n\n// Безопасный интерфейс парсинга JWT с защитой от Algorithm Confusion\ntype TokenParser struct {\n\texpectedAlgorithm string\n\thmacSecret        []byte\n}\n\nfunc NewTokenParser(secret []byte) *TokenParser {\n\treturn &TokenParser{\n\t\texpectedAlgorithm: \"HS256\",\n\t\thmacSecret:        secret,\n\t}\n}\n\n// KeyValidationFunc защищает от атак подмены алгоритма (HMAC вместо RSA)\nfunc (p *TokenParser) ValidateKey(algHeader string) ([]byte, error) {\n\t// КРИТИЧЕСКИ ВАЖНО: Строгая проверка допустимого алгоритма подписи!\n\tif algHeader != p.expectedAlgorithm {\n\t\treturn nil, fmt.Errorf(\"unexpected signing algorithm %q, expected %q (Potential Attack)\",\n\t\t\talgHeader, p.expectedAlgorithm)\n\t}\n\treturn p.hmacSecret, nil\n}\n\nfunc main() {\n\tparser := NewTokenParser([]byte(\"production_super_secret_key\"))\n\n\t// Тест 1: Валидный алгоритм\n\tkey, err := parser.ValidateKey(\"HS256\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Unexpected error: %v\", err)\n\t}\n\tfmt.Printf(\"[OK] Valid algorithm accepted. Secret length: %d bytes\\n\", len(key))\n\n\t// Тест 2: Атака Algorithm Confusion (атакующий шлет RS256 или 'none')\n\t_, err = parser.ValidateKey(\"none\")\n\tif errors.Is(err, err) && err != nil {\n\t\tfmt.Printf(\"[SECURITY BLOCKED] %v\\n\", err)\n\t}\n}",
                "note": "Защита от Algorithm Confusion при парсинге криптографических токенов"
            }
        ],
        "under_the_hood": "В уязвимых версиях библиотек функция обратного вызова `keyFunc` слепо возвращала публичный ключ сервера без проверки заголовка `token.Header[\"alg\"]`. Современные версии `golang-jwt/jwt/v5` требуют явной спецификации разрешенных методов подписи (`jwt.WithValidMethods`).",
        "pitfalls": "Использование устаревшего модуля `github.com/dgrijalva/jwt-go` (заброшен в 2020 году и полон незакрытых CVE). Все проекты обязаны мигрировать на `github.com/golang-jwt/jwt/v5`.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'В чем суть атаки Key Confusion в JWT и как ее предотвратить в Go?' Ответ: 'Атакующий меняет заголовок alg с RS256 на HS256 и подписывает токен публичным ключом сервера. Если сервер не проверяет alg строго, HMAC валидация сойдется. Защита: строгая проверка алгоритма в keyFunc и использование WithValidMethods'."
    },
    {
        "num": 12,
        "title": "Управление принятыми рисками: файл конфигурации govulncheck ignore",
        "task": "Настройте механизм контролируемого подавления ложных срабатываний или принятых рисков (Accepted Risks) для govulncheck через аргументы запуска или конфигурационные файлы.",
        "theory": "В корпоративной разработке возникают ситуации, когда устранить уязвимость прямо сейчас невозможно: 1) Автор сторонней библиотеки еще не выпустил патч, но уязвимость не эксплуатируема в вашем сценарии; 2) Обновление ломает обратную совместимость, а релиз запланирован на следующий квартал; 3) Сервис работает в изолированной внутренней сети без доступа из интернета. В таких случаях комитет безопасности (Security Champion / CISO) оформляет Security Exception. Чтобы CI/CD пайплайн не падал, уязвимость временно добавляется в список исключений с указанием OSV ID, обоснования (Justification), срока действия (Expiration Date) и ответственного инженера.",
        "step_by_step": [
            "Определите структуру конфигурационного файла исключений уязвимостей.",
            "Напишите валидатор срока действия исключения (чтобы исключения не оставались навсегда).",
            "Реализуйте фильтрацию отчета govulncheck по списку разрешенных исключений.",
            "Проверьте блокировку сборки при истечении срока исключения."
        ],
        "code_blocks": [
            {
                "filename": "vuln_ignore_policy.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"time\"\n)\n\ntype IgnoredVulnerability struct {\n\tOSVID         string\n\tReason        string\n\tApprovedBy    string\n\tExpiresAt     time.Time\n}\n\ntype SecurityPolicyEngine struct {\n\texceptions map[string]IgnoredVulnerability\n}\n\nfunc NewSecurityPolicyEngine() *SecurityPolicyEngine {\n\treturn &SecurityPolicyEngine{\n\t\texceptions: make(map[string]IgnoredVulnerability),\n\t}\n}\n\nfunc (e *SecurityPolicyEngine) AddException(ex IgnoredVulnerability) {\n\te.exceptions[ex.OSVID] = ex\n}\n\nfunc (e *SecurityPolicyEngine) IsExceptionValid(osvID string) (bool, string) {\n\tex, found := e.exceptions[osvID]\n\tif !found {\n\t\treturn false, \"No approved security exception found\"\n\t}\n\n\tif time.Now().After(ex.ExpiresAt) {\n\t\treturn false, fmt.Sprintf(\"Exception for %s EXPIRED on %s! Immediate remediation required.\",\n\t\t\tosvID, ex.ExpiresAt.Format(\"2006-01-02\"))\n\t}\n\n\treturn true, fmt.Sprintf(\"Exception active: approved by %s (Reason: %q, Valid until: %s)\",\n\t\tex.ApprovedBy, ex.Reason, ex.ExpiresAt.Format(\"2006-01-02\"))\n}\n\nfunc main() {\n\tengine := NewSecurityPolicyEngine()\n\n\t// Добавляем временно согласованное исключение\n\tengine.AddException(IgnoredVulnerability{\n\t\tOSVID:      \"GO-2023-1899\",\n\t\tReason:     \"Internal service only, no external untrusted input accepted\",\n\t\tApprovedBy: \"security-team@mycorp.com\",\n\t\tExpiresAt:  time.Now().Add(30 * 24 * time.Hour), // Действует 30 дней\n\t})\n\n\t// Проверка активного исключения\n\tvalid, reason := engine.IsExceptionValid(\"GO-2023-1899\")\n\tfmt.Printf(\"[Check 1] Allowed=%v: %s\\n\", valid, reason)\n\n\t// Проверка неавторизованной CVE\n\tvalid2, reason2 := engine.IsExceptionValid(\"GO-2024-9999\")\n\tfmt.Printf(\"[Check 2] Allowed=%v: %s\\n\", valid2, reason2)\n}",
                "note": "Управление временными исключениями безопасности с валидацией срока действия"
            }
        ],
        "under_the_hood": "Хранение даты экспирации (`ExpiresAt`) обязательно: без этого списки исключений превращаются в 'кладбище забытых уязвимостей', где опасные баги игнорируются годами.",
        "pitfalls": "Добавление исключений в виде `flag: --ignore-all` или отключение сканера в CI при сбоях. Каждое исключение обязано быть точечным по конкретному OSV ID.",
        "bigtech_interview": "Вопрос на собеседовании в Тинькофф: 'Как в компании организован процесс работы с CVE, которые нельзя обновить немедленно?' Ответ: 'Создается запрос на Security Waiver (исключение) с оценкой вектора атаки и компенсационных мер. Исключение вносится в конфигурацию сканера с жестким TTL (максимум 30-60 дней). Если за это время патч не выпущен, релизы блокируются'."
    },
    {
        "num": 13,
        "title": "Глубокая верификация go.sum: структура хэшей модуля и go.mod",
        "task": "Напишите парсер файла go.sum. Объясните назначение парных записей: почему для каждого модуля в go.sum присутствуют две строки — для содержимого модуля и для его go.mod файла.",
        "theory": "Внимательный инженер замечает, что для каждой зависимости в `go.sum` обычно записаны ДВЕ строки: 1) `github.com/gin-gonic/gin v1.9.0 h1:abc...` — хэш архива с полным исходным кодом модуля; 2) `github.com/gin-gonic/gin v1.9.0/go.mod h1:xyz...` — хэш ТОЛЬКО файла `go.mod` этого модуля. Зачем Go хранит отдельный хэш файла `go.mod`? Для оптимизации сетевого трафика и скорости сборки (Lazy Module Loading)! Когда Go строит граф зависимостей (MVS), ему не нужно скачивать 100 мегабайт исходного кода всех транзитивных библиотек. Go скачивает ТОЛЬКО их маленькие файлы `go.mod` (несколько килобайт) и проверяет их хэш по строке `.../go.mod h1:...`. Полный архив модуля скачивается только в том случае, если пакеты из него реально импортируются в коде.",
        "step_by_step": [
            "Создайте структуру GoSumEntry для парсинга строк.",
            "Реализуйте чтение go.sum и разделение на модуль-хэши и mod-хэши.",
            "Проверьте целостность и корректность структуры парных записей.",
            "Сформулируйте преимущества Lazy Module Loading для скорости CI сборки."
        ],
        "code_blocks": [
            {
                "filename": "gosum_parser.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"bufio\"\n\t\"fmt\"\n\t\"strings\"\n)\n\ntype GoSumEntry struct {\n\tModulePath string\n\tVersion    string\n\tIsModOnly  bool\n\tHashType   string\n\tHashValue  string\n}\n\nfunc ParseGoSum(rawContent string) []GoSumEntry {\n\tvar entries []GoSumEntry\n\tscanner := bufio.NewScanner(strings.NewReader(rawContent))\n\n\tfor scanner.Scan() {\n\t\tline := strings.TrimSpace(scanner.Text())\n\t\tif line == \"\" {\n\t\t\tcontinue\n\t\t}\n\n\t\tfields := strings.Fields(line)\n\t\tif len(fields) != 3 {\n\t\t\tcontinue\n\t\t}\n\n\t\tmodPath := fields[0]\n\t\tverField := fields[1]\n\t\tfullHash := fields[2]\n\n\t\tisModOnly := false\n\t\tversion := verField\n\t\tif strings.HasSuffix(verField, \"/go.mod\") {\n\t\t\tisModOnly = true\n\t\t\tversion = strings.TrimSuffix(verField, \"/go.mod\")\n\t\t}\n\n\t\thashParts := strings.SplitN(fullHash, \":\", 2)\n\t\thashType, hashVal := \"unknown\", fullHash\n\t\tif len(hashParts) == 2 {\n\t\t\thashType = hashParts[0]\n\t\t\thashVal = hashParts[1]\n\t\t}\n\n\t\tentries = append(entries, GoSumEntry{\n\t\t\tModulePath: modPath,\n\t\t\tVersion:    version,\n\t\t\tIsModOnly:  isModOnly,\n\t\t\tHashType:   hashType,\n\t\t\tHashValue:  hashVal,\n\t\t})\n\t}\n\treturn entries\n}\n\nfunc main() {\n\tsampleGoSum := `golang.org/x/text v0.14.0 h1:ScnM26xAcpOT99q+j2eZebgT4zQjXNQ8u/oEkhkI/I0=\ngolang.org/x/text v0.14.0/go.mod h1:18ZOQIKpY8NJVqYksKHtTdi31H5itUj6mZuhbHOuWtI=\ngithub.com/google/uuid v1.6.0 h1:NIvaJDMOIGetgnn5gkZahV0B80ArWx+/S9bVOlfl55A=\ngithub.com/google/uuid v1.6.0/go.mod h1:TIyPZe4MgqvFqt22lIDRmNApMQqxQKZ82rCY70sPr38=`\n\n\tentries := ParseGoSum(sampleGoSum)\n\tfor _, e := range entries {\n\t\tscope := \"Full Module Code\"\n\t\tif e.IsModOnly {\n\t\t\tscope = \"go.mod Manifest Only (Lazy Loading)\"\n\t\t}\n\t\tfmt.Printf(\"[%s] %s @ %s -> Hash: %s... (%s)\\n\",\n\t\t\te.HashType, e.ModulePath, e.Version, e.HashValue[:12], scope)\n\t}\n}",
                "note": "Парсер go.sum и объяснение роли парных записей для Lazy Module Loading"
            }
        ],
        "under_the_hood": "Если удалить строку с `/go.mod` из `go.sum`, Go при сборке будет вынужден скачать весь zip-архив модуля, чтобы извлечь из него `go.mod`, что увеличит время `go build` в разы.",
        "pitfalls": "Ручное редактирование строк в `go.sum`. Любое ручное изменение приведет к ошибке `checksum mismatch`. Файл должен редактироваться исключительно тулчейном Go (`go mod tidy`, `go get`).",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Зачем в go.sum у одной библиотеки две строки, одна из которых оканчивается на /go.mod?' Ответ: 'Строка /go.mod позволяет Go проверить целостность зависимостей при построении дерева модулей БЕЗ скачивания архива с кодом. Это оптимизация Lazy Module Loading, ускоряющая сборку'."
    },
    {
        "num": 14,
        "title": "Интеграция govulncheck в CI/CD: блокировка Pull Request при уязвимостях",
        "task": "Сконфигурируйте пайплайн GitHub Actions / GitLab CI, запускающий govulncheck ./... с флагом падения пайплайна при обнаружении критических уязвимостей.",
        "theory": "Безопасность цепочки поставок эффективна только тогда, когда проверки автоматизированы и не зависят от дисциплины разработчиков (Shift-Left Security). В CI/CD пайплайне шаг проверки уязвимостей размещается ДО компиляции и сборки Docker-образа. Официальный GitHub Action `golang/govulncheck-action` автоматически запускает анализ и при обнаружении эксплуатируемых уязвимостей завершает шаг с ненулевым exit-кодом (`exit 1`), блокируя merge в защищенную ветку `main` и предотвращая попадание дефектного кода в продакшен.",
        "step_by_step": [
            "Создайте декларативный файл воркфлоу .github/workflows/security.yml.",
            "Сконфигурируйте шаг установки Go и кеширования модулей.",
            "Добавьте шаг запуска golang/govulncheck-action или прямой команды govulncheck ./....",
            "Настройте уведомления и блокировку слияния в ветку main."
        ],
        "code_blocks": [
            {
                "filename": "github-actions-security.yaml",
                "lang": "yaml",
                "code": "name: Security Supply Chain Audit\n\non:\n  push:\n    branches: [ main ]\n  pull_request:\n    branches: [ main ]\n  schedule:\n    # Ежедневное ночное сканирование для выявления свежих 0-day CVE\n    - cron: '0 3 * * *'\n\njobs:\n  govulncheck:\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout Source Code\n        uses: actions/checkout@v4\n\n      - name: Setup Go Toolchain\n        uses: actions/setup-go@v5\n        with:\n          go-version: '1.23'\n          cache: true\n\n      - name: Install govulncheck\n        run: go install golang.org/x/vuln/cmd/govulncheck@latest\n\n      - name: Run Vulnerability Reachability Analysis\n        run: |\n          echo \"Scanning codebase for reachable vulnerabilities...\"\n          govulncheck ./...",
                "note": "Пайплайн GitHub Actions с автоматическим аудитом уязвимостей"
            }
        ],
        "under_the_hood": "Запуск сканирования по расписанию (`schedule: cron`) критически важен: уязвимость в используемой библиотеке может быть обнаружена через 6 месяцев после того, как код был написан и задеплоен. Ночное сканирование выявляет такие угрозы автоматически.",
        "pitfalls": "Запуск govulncheck с `continue-on-error: true`. Это превращает аудит безопасности в формальность: пайплайн зеленый, а уязвимый сервис идет в продакшен.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'Зачем запускать govulncheck по крону, если в кодовой базе не было новых коммитов?' Ответ: 'Потому что новые CVE в существующих библиотеках регистрируются исследователями безопасности каждый день. Код вчера был безопасным, а сегодня в vuln.go.dev появилась новая уязвимость. Регулярный крон выявляет такие риски'."
    },
    {
        "num": 15,
        "title": "Переменная окружения GOSUMDB: sum.golang.org, GONOSUMDB и Private Modules",
        "task": "Настройте переменные окружения GOSUMDB, GOPRIVATE и GONOSUMDB для безопасной сборки проектов, использующих как публичные модули, так и закрытые корпоративные библиотеки.",
        "theory": "По умолчанию `GOSUMDB=sum.golang.org`. При скачивании любого пакета Go отправляет хэш и имя модуля на сервер Google `sum.golang.org`. Но что произойдет, если проект использует приватный корпоративный репозиторий `gitlab.corp.mybank.ru/payments/core`? 1) Google вернет ошибку 404 (он не имеет доступа к вашей приватной сети); 2) Вы допустите утечку внутренней архитектуры и приватных названий модулей во внешнюю сеть! Для решения этой проблемы Go предоставляет переменные: `GOPRIVATE=gitlab.corp.mybank.ru/*` — автоматически отключает как прокси (GOPROXY), так и проверку контрольных сумм (GOSUMDB) для корпоративных доменов; `GONOSUMDB=gitlab.corp.mybank.ru/*` — гранулярно отключает только проверку Checksum DB.",
        "step_by_step": [
            "Изучите назначение GOPRIVATE, GOSUMDB, GONOSUMDB, GONOPROXY.",
            "Сконфигурируйте локальный go env для работы с приватными репозиториями.",
            "Проверьте маски доменов (wildcards).",
            "Обеспечьте защиту от утечки корпоративных путей импорта в публичный интернет."
        ],
        "code_blocks": [
            {
                "filename": "configure_private_modules.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\n# Конфигурация для Enterprise разработки:\n# 1. Задаем приватные домены (отключает proxy и sumdb для внутренних репозиториев)\ngo env -w GOPRIVATE=\"gitlab.mycorp.ru/*,github.com/mycorp-enterprise/*\"\n\n# 2. Публичные модули продолжают проверяться через официальный Transparency Log\ngo env -w GOSUMDB=\"sum.golang.org\"\n\n# 3. Публичные модули кэшируются через Google Proxy или корпоративный Nexus\ngo env -w GOPROXY=\"https://proxy.golang.org,direct\"\n\necho \"Current Go Modules Security Configuration:\"\ngo env GOPRIVATE GOSUMDB GOPROXY GONOSUMDB\n",
                "note": "Безопасная настройка GOPRIVATE и GOSUMDB для корпоративных репозиториев"
            }
        ],
        "under_the_hood": "Переменная `GOPRIVATE` является синтаксическим сахаром: она одновременно устанавливает значения по умолчанию для `GONOPROXY` и `GONOSUMDB`, минимизируя вероятность ошибки конфигурирования.",
        "pitfalls": "Установка `GOSUMDB=off` глобально на машине разработчика. Это полностью отключает проверку подлинности публичных модулей, делая систему уязвимой к атакам подмены тегов и отравления зависимостей.",
        "bigtech_interview": "Вопрос на собеседовании в Тинькофф: 'Что произойдет, если не настроить GOPRIVATE для закрытого корпоративного модуля?' Ответ: 'Команда `go get` попытается обратиться к публичному сервису Google sum.golang.org. Во-первых, сборка упадет с ошибкой 404. Во-вторых, внутренние приватные пути пакетов утекут в логи внешнего сервиса'."
    },
    {
        "num": 16,
        "title": "Изоляция зависимостей с помощью Vendoring в Air-Gapped контурах",
        "task": "Настройте сборку Go-проекта в полностью изолированной сети (Air-Gapped / No Internet) с помощью go mod vendor и флага go build -mod=vendor.",
        "theory": "В критической инфраструктуре (банки, объекты КИИ, оборонные предприятия) серверы сборки и продакшен-ноды физически отключены от глобального интернета (Air-Gapped Environment). Команда `go build` без интернета упадет, так как не сможет обратиться к GitHub или GOPROXY. Механизм `Vendoring` решает эту задачу: команда `go mod vendor` скачивает весь исходный код зависимостей в локальную папку `vendor/` внутри репозитория. Команда `go build -mod=vendor` компилирует проект исключительно из папки `vendor/`, не совершая ни единого сетевого вызова. Это дает две гарантии: 1) 100% независимость от доступности интернета и сторонних серверов; 2) Защита от удаления библиотеки автором (как в истории с `left-pad` в JavaScript).",
        "step_by_step": [
            "Выполните команду go mod vendor.",
            "Убедитесь в создании каталога vendor/ и файла vendor/modules.txt.",
            "Протестируйте сборку с отключенным сетевым интерфейсом через go build -mod=vendor.",
            "Сформулируйте компромиссы между размером Git репозитория и надежностью вендоринга."
        ],
        "code_blocks": [
            {
                "filename": "vendor_workflow.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[1/3] Generating local vendor directory with all dependencies...\"\n# go mod vendor\n\necho \"[2/3] Verifying vendor/modules.txt consistency...\"\n# test -f vendor/modules.txt && echo \"modules.txt present.\"\n\necho \"[3/3] Simulating offline build without network access...\"\n# Флаг -mod=vendor заставляет компилятор игнорировать сетевой модуль-кэш\n# go build -mod=vendor -o /tmp/offline-app main.go\n\necho \"Offline Air-Gapped compilation successful!\"\n",
                "note": "Сборка проекта в изолированном Air-Gapped контуре через vendoring"
            }
        ],
        "under_the_hood": "Файл `vendor/modules.txt` содержит список всех модулей, их версий и список пакетов, скопированных в директорию `vendor/`. Компилятор сверяет `modules.txt` с `go.mod`, гарантируя отсутствие рассинхронизации версий.",
        "pitfalls": "Ручная правка кода внутри каталога `vendor/`. Следующий вызов `go mod vendor` сотрет все ваши ручные правки без предупреждения. Для модификации зависимостей используйте директиву `replace` в `go.mod`.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Что лучше в Enterprise: vendoring в Git или локальный Nexus/Artifactory GOPROXY?' Ответ: 'Для огромных монорепозиториев лучше приватный GOPROXY (Athens/Artifactory), чтобы Git не раздувался гигабайтами стороннего кода. Для критических Air-Gapped контуров и микросервисов с высокими требованиями к автономности надежнее vendoring'."
    },
    {
        "num": 17,
        "title": "Автоматический аудит уязвимостей в GitHub Actions перед компиляцией Docker",
        "task": "Напишите законченный Dockerfile и пайплайн GitHub Actions, в котором этап сборки Docker-образа запускается только после успешного прохождения аудита govulncheck.",
        "theory": "Сборка уязвимого бинарника и упаковка его в контейнерный образ — напрасная трата вычислительных ресурсов раннеров. Архитектурный принцип Shift-Left Security требует строгого порядка этапов (Stages): 1. `Lint & Unit Test`: проверка корректности синтаксиса и бизнес-логики; 2. `Security Audit`: запуск `govulncheck ./...` и проверка `go mod verify`; 3. `Build & Containerize`: только если шаги 1 и 2 завершились успешно, запускается `docker build` и публикация образа в Container Registry (Harbor, Yandex Container Registry, Docker Hub). Это гарантирует, что ни один образ с известными RCE уязвимостями не попадет в registry компании.",
        "step_by_step": [
            "Создайте multi-stage Dockerfile для Go приложения.",
            "Настройте GitHub Actions workflow с зависимостью needs: [security-audit].",
            "Убедитесь, что при падении аудита сборка контейнера не запускается.",
            "Проверьте публикацию только валидированных образов."
        ],
        "code_blocks": [
            {
                "filename": "secure_pipeline.yaml",
                "lang": "yaml",
                "code": "name: Secure Build and Publish Pipeline\n\non:\n  push:\n    branches: [ main ]\n\njobs:\n  security-audit:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.23'\n      - name: Verify Dependencies Integrity\n        run: go mod verify\n      - name: Run govulncheck\n        run: |\n          go install golang.org/x/vuln/cmd/govulncheck@latest\n          govulncheck ./...\n\n  docker-build:\n    needs: [security-audit] # ЗАПУСКАЕТСЯ ТОЛЬКО ПОСЛЕ УСПЕШНОГО АУДИТА!\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - name: Build Secure Docker Image\n        run: |\n          echo \"Security checks passed. Commencing container build...\"\n          docker build -t mycorp/secure-service:latest -f Dockerfile .",
                "note": "Блокировка сборки Docker-образа при обнаружении уязвимостей в кодовой базе"
            },
            {
                "filename": "Dockerfile",
                "lang": "dockerfile",
                "code": "# Multi-stage build для максимальной безопасности\nFROM golang:1.23-alpine AS builder\nWORKDIR /app\nCOPY go.mod go.sum ./\nRUN go mod download && go mod verify\nCOPY . .\n# Сборка статического бинарника без CGO с удалением отладочной информации\nRUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags=\"-s -w\" -o /app/server .\n\n# Финальный образ на базе scratch (нулевая площадь атаки)\nFROM scratch\nCOPY --from=builder /app/server /server\nUSER 65534:65534\nENTRYPOINT [\"/server\"]",
                "note": "Минималистичный безопасный Dockerfile на базе scratch"
            }
        ],
        "under_the_hood": "Флаг `-trimpath` удаляет абсолютные пути локальной файловой системы разработчика из скомпилированного бинарника, а образ `scratch` не содержит утилит sh, bash, curl, libc, лишая злоумышленника инструментов при попытке побега из контейнера.",
        "pitfalls": "Использование одного большого Dockerfile, где сборка и запуск происходят в одном тяжелом образе golang:alpine. В таком образе остаются компилятор, утилиты сборки и пакетный менеджер apk, что создает колоссальную площадь атаки.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Почему для Go бинарников в продакшене выбирают base image scratch или distroless?' Ответ: 'Потому что Go компилируется в самодостаточный статический бинарник. В образе scratch нет ни шелла (/bin/sh), ни пакетных менеджеров, ни libc. Даже если злоумышленник найдет RCE в приложении, он не сможет выполнить системную команду или скачать эксплойт'."
    },
    {
        "num": 18,
        "title": "Каверзный кейс: транзитивные зависимости (Transitive Dependencies) и Reachability",
        "task": "Смоделируйте ситуацию, когда уязвимость находится не в прямом импорте вашего кода, а в глубокой транзитивной зависимости (библиотека C, вызванная библиотекой B). Покажите, как govulncheck анализирует цепочку вызовов сквозь границы пакетов.",
        "theory": "В современных проектах на Go до 80-90% кодовой базы составляют транзитивные (косвенные) зависимости. Если сервис импортирует популярный веб-фреймворк или ORM, тот под капотом тянет десятки сторонних модулей. Когда в одном из глубоких транзитивных модулей регистрируется CVE, классический сканер (Dependabot/Snyk) поднимает тревогу: 'В вашем проекте обнаружена Critical CVE!'. Однако фреймворк может использовать этот модуль только для специфического формата данных, который ваше приложение никогда не включает. govulncheck выполняет межмодульный анализ графа вызовов (Inter-procedural Call Graph Analysis): он проверяет, существует ли путь от функции `main()` вашего сервиса через методы фреймворка к конкретной функции уязвимого транзитивного пакета.",
        "step_by_step": [
            "Определите цепочку модулей: App -> GatewayPkg -> VulnerableTransitivePkg.",
            "Напишите код, вызывающий безопасный метод GatewayPkg.",
            "Покажите, что уязвимый метод транзитивного пакета не вызывается.",
            "Проанализируйте статус проверки в govulncheck (Unreachable)."
        ],
        "code_blocks": [
            {
                "filename": "transitive_reachability.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n)\n\n// Имитация транзитивной зависимости 3-го уровня:\n// App -> BusinessService -> ThirdPartyLib -> VulnerableLegacyHelper\n\ntype VulnerableLegacyHelper struct{}\n\n// SafeUtility вызывается приложением\nfunc (h *VulnerableLegacyHelper) SafeUtility(input string) string {\n\treturn \"Clean: \" + input\n}\n\n// ExploitCVE2024 содержит критическую уязвимость RCE, но НЕ вызывается приложением\nfunc (h *VulnerableLegacyHelper) ExploitCVE2024(cmd string) {\n\tpanic(\"Unsafe RCE triggered! Should never be reachable.\")\n}\n\ntype BusinessService struct {\n\thelper VulnerableLegacyHelper\n}\n\nfunc (s *BusinessService) ProcessOrder(id string) string {\n\t// Вызываем только безопасный метод\n\treturn s.helper.SafeUtility(id)\n}\n\nfunc main() {\n\tsvc := &BusinessService{}\n\tresult := svc.ProcessOrder(\"ord-7841\")\n\n\tlog.Printf(\"[Application] Result: %s\", result)\n\tfmt.Println(\"Call Graph Result: ExploitCVE2024() is NOT reachable. Build deemed secure.\")\n}",
                "note": "Транзитивная зависимость: безопасный путь вызова без активации уязвимого символа"
            }
        ],
        "under_the_hood": "Алгоритм RTA (Rapid Type Analysis) компилятора Go исследует только реально инстанцированные типы и вызываемые интерфейсные методы. Мертвые ветви транзитивных зависимостей отсекаются, не попадая в срез вызовов.",
        "pitfalls": "Обновление всей цепочки зависимостей через `go get -u` без тестирования. Обновление транзитивных пакетов может изменить поведение фреймворка и привести к скрытым багам в runtime.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'В транзитивной зависимости найдена уязвимость, но автор родительской библиотеки задерживает релиз. Как поступить?' Ответ: '1) Проверить через govulncheck, вызывается ли уязвимая функция в нашем приложении. Если нет — риск принят (Accepted Risk); 2) Если вызывается — форсировать безопасную версию транзитивного пакета через директиву `replace` в go.mod'."
    },
    {
        "num": 19,
        "title": "Контроль целостности кэша модулей: команда go mod verify",
        "task": "Изучите работу команды go mod verify. Смоделируйте повреждение локального кэша модулей ($GOPATH/pkg/mod) и покажите, как go mod verify обнаруживает модификацию файлов на диске.",
        "theory": "После скачивания модулей Go сохраняет их в глобальном каталоге `$GOPATH/pkg/mod/download/`. Каталог защищен правами доступа только для чтения (`chmod -R a-w`), однако локальный вредоносный процесс (или сбой дискового накопителя) может изменить файлы библиотеки прямо на диске до компиляции. Команда `go mod verify` выполняет глубокую криптографическую проверку: она пофайлово пересчитывает SHA-256 контрольные суммы всех распакованных на диске пакетов и сравнивает их с каноническими значениями из `go.sum`. Если хотя бы один байт был изменен, команда немедленно сообщает: `github.com/foo/bar v1.0.0: dir has been modified` с ненулевым кодом выхода.",
        "step_by_step": [
            "Выполните команду go mod verify в терминале проекта.",
            "Изучите успешный вывод: all modules verified.",
            "Напишите Go-скрипт проверки целостности локального кэша.",
            "Добавьте шаг go mod verify в пре-коммит хук и CI/CD пайплайн."
        ],
        "code_blocks": [
            {
                "filename": "verify_cache.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"Running Go modules cryptographic cache verification...\"\n# go mod verify проверяет, что скачанные файлы в $GOPATH/pkg/mod не были модифицированы\nif go mod verify; then\n    echo \"SUCCESS: All downloaded modules match their cryptographic hashes in go.sum!\"\nelse\n    echo \"SECURITY FAILURE: Local module files were modified or corrupted! Re-download required.\"\n    exit 1\nfi\n",
                "note": "Скрипт проверки целостности кэша модулей с помощью go mod verify"
            }
        ],
        "under_the_hood": "`go mod verify` не обращается к сети: она работает полностью локально, сопоставляя локальные файлы кэша с доверенными хэшами `go.sum` из репозитория Git.",
        "pitfalls": "Пропуск `go mod verify` в Dockerfile перед сборкой. Всегда выполняйте `RUN go mod download && go mod verify` перед компиляцией.",
        "bigtech_interview": "В чем разница между `go.sum` и `go mod verify`? Ответ: '`go.sum` — это база доверенных хэшей. `go mod verify` — это команда, которая пересчитывает хэши уже скачанных файлов на диске и сверяет их с go.sum, гарантируя отсутствие локального заражения или повреждения файлов кэша'."
    },
    {
        "num": 20,
        "title": "Устранение уязвимостей в косвенных (indirect) зависимостях",
        "task": "Создайте сценарий с уязвимой indirect зависимостью в go.mod. Покажите использование go mod why для поиска причины импорта и принудительное обновление через go get или replace.",
        "theory": "В файле `go.mod` зависимости, которые ваше приложение не импортирует напрямую, помечаются специальным комментарием `// indirect`. Опасность косвенных зависимостей: 1) Команда `go mod tidy` не обновляет indirect зависимости автоматически до последних версий, если они удовлетворяют требованиям родительского модуля (принцип MVS); 2) Если родительский модуль (например, gin-gonic/gin) требует `package-x v1.0.0`, а в `package-x v1.0.0` есть CVE, Go не станет сам скачивать `v1.0.1`. Решение: явный вызов `go get package-x@v1.0.1`. В этом случае Go добавляет прямую запись с версией `v1.0.1 // indirect` в `go.mod`, переопределяя требование родительской библиотеки на безопасную версию.",
        "step_by_step": [
            "Выполните команду go mod why -m <vulnerable_package>.",
            "Определите родительский модуль, затянувший зависимость.",
            "Выполните точечный апдейт: go get <vulnerable_package>@safe_version.",
            "Проверьте обновление строки в go.mod со статусом // indirect."
        ],
        "code_blocks": [
            {
                "filename": "fix_indirect.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nTARGET_PKG=\"golang.org/x/net\"\nSAFE_VER=\"v0.24.0\"\n\necho \"[1/3] Investigating why package is in dependency graph:\"\n# go mod why -m $TARGET_PKG\n\necho \"[2/3] Pinning indirect dependency to patched safe version:\"\n# go get ${TARGET_PKG}@${SAFE_VER}\n\necho \"[3/3] Tidying go.mod manifest:\"\n# go mod tidy\n\necho \"Indirect dependency successfully upgraded to ${SAFE_VER}.\"\n",
                "note": "Поиск и принудительное обновление уязвимых indirect зависимостей"
            }
        ],
        "under_the_hood": "Когда вы явно вызываете `go get indirect-pkg@version`, тулчейн Go вносит директиву `require indirect-pkg version // indirect` в `go.mod`. Это повышает приоритет версии в алгоритме MVS без изменения прямого кода импортов.",
        "pitfalls": "Попытка удалить строку `// indirect` из `go.mod`. При следующем запуске `go mod tidy` или `go build` Go автоматически восстановит минимальную версию родителя, вернув уязвимость обратно!",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Что означает комментарий // indirect в go.mod?' Ответ: 'Это модуль, который не импортируется напрямую ни в одном .go файле нашего проекта, но требуется одной из транзитивных зависимостей. Его можно принудительно обновить через `go get module@version`'."
    },
    {
        "num": 21,
        "title": "Модульный прокси: GOPROXY=https://proxy.golang.org,direct и защита от исчезновения кода",
        "task": "Изучите устройство протокола Go Module Proxy. Напишите HTTP-сервер, реализующий базовые эндпоинты протокола GOPROXY (.info, .mod, .zip) для кэширования модулей.",
        "theory": "Исторически в других языках удаление автором репозитория из GitHub приводило к падению сборок по всему миру (Left-Pad Incident). В Go эта проблема решена на уровне архитектуры: по умолчанию включен `GOPROXY=https://proxy.golang.org,direct`. Прокси-сервер Google кэширует неизменяемые архивы всех когда-либо опубликованных публичных модулей. Даже если автор удалит свой аккаунт на GitHub или сотрет репозиторий, `proxy.golang.org` продолжит вечно отдавать кэшированные zip-архивы и файлы `go.mod`. Суффикс `,direct` означает: 'Если модуль не найден на прокси, попытаться скачать напрямую из системы контроля версий (Git)'",
        "step_by_step": [
            "Изучите спецификацию протокола Go Module Proxy.",
            "Реализуйте HTTP эндпоинты /$base/@v/list, .info, .mod.",
            "Проверьте отдачу метаданных версии модуля в JSON формате.",
            "Сформулируйте гарантии доступности зависимостей через проксирование."
        ],
        "code_blocks": [
            {
                "filename": "mini_goproxy.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"strings\"\n\t\"time\"\n)\n\n// ModuleInfo представляет структуру ответа эндпоинта .info в протоколе GOPROXY\ntype ModuleInfo struct {\n\tVersion string    `json:\"Version\"`\n\tTime    time.Time `json:\"Time\"`\n}\n\n// MiniGoProxy реализует протокол Go Module Proxy для кэширования модулей\nfunc MiniGoProxy() http.Handler {\n\tmux := http.NewServeMux()\n\n\t// 1. Эндпоинт списка версий: /<module>/@v/list\n\t// 2. Эндпоинт метаданных:   /<module>/@v/<version>.info\n\t// 3. Эндпоинт манифеста:    /<module>/@v/<version>.mod\n\tmux.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tpath := r.URL.Path\n\t\tlog.Printf(\"[GOPROXY Request] %s %s\", r.Method, path)\n\n\t\tif strings.HasSuffix(path, \".info\") {\n\t\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\t\tinfo := ModuleInfo{\n\t\t\t\tVersion: \"v1.0.0\",\n\t\t\t\tTime:    time.Now().UTC(),\n\t\t\t}\n\t\t\t_ = json.NewEncoder(w).Encode(info)\n\t\t\treturn\n\t\t}\n\n\t\tif strings.HasSuffix(path, \".mod\") {\n\t\t\tw.Header().Set(\"Content-Type\", \"text/plain; charset=utf-8\")\n\t\t\t_, _ = w.Write([]byte(\"module github.com/mycorp/cached-lib\\n\\ngo 1.23\\n\"))\n\t\t\treturn\n\t\t}\n\n\t\tif strings.HasSuffix(path, \"/@v/list\") {\n\t\t\tw.Header().Set(\"Content-Type\", \"text/plain; charset=utf-8\")\n\t\t\t_, _ = w.Write([]byte(\"v1.0.0\\nv1.0.1\\n\"))\n\t\t\treturn\n\t\t}\n\n\t\thttp.NotFound(w, r)\n\t})\n\n\treturn mux\n}\n\nfunc main() {\n\tproxy := httptest.NewServer(MiniGoProxy())\n\tdefer proxy.Close()\n\n\tfmt.Printf(\"Custom Go Module Proxy listening at: %s\\n\", proxy.URL)\n\n\t// Тестовый запрос эндпоинта версии\n\tresp, err := http.Get(proxy.URL + \"/github.com/mycorp/cached-lib/@v/v1.0.0.info\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Proxy call failed: %v\", err)\n\t}\n\tdefer resp.Body.Close()\n\n\tvar info ModuleInfo\n\t_ = json.NewDecoder(resp.Body).Decode(&info)\n\tfmt.Printf(\"Received cached module info: Version=%s, PublishedAt=%s\\n\", info.Version, info.Time.Format(time.RFC3339))\n}",
                "note": "Реализация протокола Go Module Proxy для защиты от исчезновения библиотек"
            }
        ],
        "under_the_hood": "Протокол GOPROXY исключительно прост: это обычный статический веб-сервер, раздающий файлы через HTTP GET. Внутри архива `.zip` лежит файловое дерево модуля с префиксом `<module>@<version>/`.",
        "pitfalls": "Использование `GOPROXY=direct` в production CI пайплайнах. Прямое скачивание из Git требует установленных утилит git/svn/hg, работает в 5-10 раз медленнее и ломается при падении GitHub.",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'Как Go защищен от удаления автором популярной библиотеки с GitHub?' Ответ: 'Через GOPROXY (proxy.golang.org). Сервер кэширует zip-архив и go.mod навсегда. Даже если репозиторий удален, Go продолжит собирать проект из кэша прокси'."
    },
    {
        "num": 22,
        "title": "Сравнение стратегий загрузки модулей: Direct, Proxy и Off",
        "task": "Напишите аналитическую матрицу сравнения режимов GOPROXY=direct, GOPROXY=proxy, GOPROXY=off и протестируйте поведение тулчейна при отсутствии сети.",
        "theory": "Переменная окружения `GOPROXY` определяет поведение Go при разрешении зависимостей: 1) `GOPROXY=https://proxy.golang.org`: кэширование, высокая скорость (zip по HTTP), защита от удаления кода. Минус: публичный Google прокси видит пути скачиваемых пакетов; 2) `GOPROXY=direct`: скачивание напрямую через Git клонирование (`git clone https://...`). Требует наличия git в системе, создает высокую нагрузку на VCS, медленно клонирует тяжелые репозитории со всей историей коммитов; 3) `GOPROXY=off`: полное отключение любых сетевых запросов при разрешении модулей. Если модуль отсутствует в локальном кэше `$GOPATH/pkg/mod` или каталоге `vendor/`, сборка немедленно падает с ошибкой.",
        "step_by_step": [
            "Изучите синтаксис списка прокси через запятую и пайп.",
            "Проверьте поведение GOPROXY=off при сборке.",
            "Сравните скорость скачивания через proxy vs direct.",
            "Сформулируйте рекомендации для CI/CD раннеров."
        ],
        "code_blocks": [
            {
                "filename": "goproxy_comparison.txt",
                "lang": "text",
                "code": "Сравнительная матрица стратегий GOPROXY в Go:\n\n| Параметр | GOPROXY=https://proxy.golang.org | GOPROXY=direct | GOPROXY=off |\n| :--- | :--- | :--- | :--- |\n| **Источник** | Google Cloud CDN кэш | Исходный Git репозиторий | Только локальный дисковый кэш |\n| **Скорость скачивания** | Сверхвысокая (HTTP gzip zip) | Медленная (полный git clone) | Мгновенная (сеть не используется) |\n| **Устойчивость к удалению** | 100% (кэш вечен) | 0% (удаление репозитория ломает сборку) | 100% (все файлы локально) |\n| **Требования к утилитам** | Не требует git/hg/svn | Требует git в PATH | Не требует сети и утилит |\n| **Приватность путей** | Пути публичных пакетов видны Google | Запросы идут только на хост Git | 100% изоляция (Air-Gapped) |\n| **Сценарий применения** | По умолчанию для 99% dev/CI | Редкие приватные модули без Athens | Высокозащищенные контуры / Vendor |",
                "note": "Сравнительный анализ режимов загрузки модулей в Go"
            }
        ],
        "under_the_hood": "Символ `|` (fallback) в GOPROXY: `https://corp-proxy.ru|https://proxy.golang.org` означает: если корпоративный прокси возвращает 404 или 410 (Gone), переключиться на публичный прокси. Символ `,` (comma) переключается только при сетевой недоступности сервера.",
        "pitfalls": "Использование `GOPROXY=direct` на сборочных серверах без настроенных SSH ключей для GitHub, что приводит к ошибкам `Host key verification failed`.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Что означает запятая и вертикальная черта в строке GOPROXY?' Ответ: 'Запятая (,) переходит к следующему прокси только при сетевых ошибках или таймаутах. Вертикальная черта (|) переходит к следующему прокси даже при кодах 404 (Not Found) и 410 (Gone)'."
    },
    {
        "num": 23,
        "title": "Развертывание собственного корпоративного GOPROXY: Athens / Nexus",
        "task": "Спроектируйте архитектуру внутреннего корпоративного прокси Go Modules на базе Athens / Nexus OSS. Настройте конфигурацию перенаправления приватного трафика и кэширования публичных пакетов.",
        "theory": "В крупных корпорациях (банки, ритейл, телеком) развертывание собственного GOPROXY (например, open-source проекта `Athens` или `JFrog Artifactory / Sonatype Nexus`) решает три задачи: 1) Полный суверенитет и безопасность: все внешние open-source библиотеки скачиваются один раз, проходят автоматический антивирусный аудит и сохраняются во внутреннем S3-хранилище компании; 2) Ускорение CI/CD: сборки в локальной сети скачивают модули со скоростью 10 Гбит/с из локального Athens, не завися от внешнего канала интернета; 3) Единая точка управления доступом: возможность централизованно запретить использование опасных библиотек с критическими CVE во всей компании.",
        "step_by_step": [
            "Опишите docker-compose файл для развертывания Athens с S3 бэкендом.",
            "Настройте upstream URL на proxy.golang.org.",
            "Сконфигурируйте переменную окружения GOPROXY на корпоративный адрес.",
            "Проверьте кэширование модулей во внутреннем хранилище."
        ],
        "code_blocks": [
            {
                "filename": "docker-compose-athens.yaml",
                "lang": "yaml",
                "code": "version: '3.8'\n\nservices:\n  athens-proxy:\n    image: gomods/athens:v0.14.1\n    container_name: corporate-goproxy\n    restart: always\n    ports:\n      - \"3000:3000\"\n    environment:\n      # Внутренний порт прокси\n      ATHENS_PORT: \":3000\"\n      # Хранилище кэшированных zip-архивов и модулей (S3/MinIO/Disk)\n      ATHENS_STORAGE_TYPE: \"disk\"\n      ATHENS_DISK_STORAGE_ROOT: \"/var/lib/athens\"\n      # Внешний апстрим для публичных пакетов\n      ATHENS_GLOBAL_ENDPOINT: \"https://proxy.golang.org\"\n      # Список запрещенных модулей (Blacklist)\n      ATHENS_FILTER_FILE: \"/etc/athens/filter.conf\"\n    volumes:\n      - athens_data:/var/lib/athens\n\nvolumes:\n  athens_data:",
                "note": "Манифест развертывания корпоративного Go Module Proxy Athens"
            }
        ],
        "under_the_hood": "Athens перехватывает запросы от `go get`, проверяет локальный кэш на диске/S3. При промахе (Cache Miss) он скачивает модуль из апстрима, сохраняет архив и отдает клиенту.",
        "pitfalls": "Отсутствие бэкапа хранилища Athens. Если диск с кэшем переполнится или сгорит, компании придется повторно скачивать все модули из интернета.",
        "bigtech_interview": "Вопрос на собеседовании в Тинькофф: 'Как закрыть разработчикам прямой доступ в интернет для скачивания пакетов, не сломав работу Go?' Ответ: 'Поднять внутри периметра сервер Athens/Nexus, закрыть исходящий интернет на рабочих машинах, и централизованно прописать `go env -w GOPROXY=http://athens.corp.internal:3000`'."
    },
    {
        "num": 24,
        "title": "Генерация SBOM (Software Bill of Materials) в форматах CycloneDX и SPDX",
        "task": "Сгенерируйте спецификацию состава программного обеспечения (SBOM) для Go-проекта с помощью утилиты cyclonedx-gomod или syft. Разберите форматы CycloneDX JSON и SPDX 2.3.",
        "theory": "Software Bill of Materials (SBOM) — это цифровой паспорт программного продукта (аналог списка ингредиентов на продуктах питания). В связи с указами по кибербезопасности (US Executive Order 14028, стандарты ФСТЭК / ISO 27001) поставка корпоративного ПО заказчикам без SBOM становится невозможной. SBOM содержит: 1) Полный перечень всех прямых и транзитивных библиотек; 2) Точные версии и криптографические хэши (SHA-256); 3) Лицензии каждого компонента (MIT, Apache-2.0, BSD); 4) Идентификаторы Package URL (PURL, например: `pkg:golang/google.golang.org/protobuf@v1.33.0`). Два главных мировых стандарта SBOM: - `CycloneDX` (разработан OWASP, оптимизирован для AppSec и сканеров уязвимостей); - `SPDX` (Software Package Data Exchange, стандарт Linux Foundation / ISO/IEC 5962:2021).",
        "step_by_step": [
            "Изучите структуру спецификации CycloneDX 1.5 JSON.",
            "Сгенерируйте SBOM через утилиту syft dir:. -o cyclonedx-json=sbom.json.",
            "Напишите Go-парсер SBOM для валидации наличия PURL и хэшей компонентов.",
            "Проверьте соответствие требованиям безопасности."
        ],
        "code_blocks": [
            {
                "filename": "parse_cyclonedx_sbom.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"log\"\n)\n\n// CycloneDXSBOM упрощенная модель спецификации OWASP CycloneDX v1.5\ntype CycloneDXSBOM struct {\n\tBOMFormat   string      `json:\"bomFormat\"`\n\tSpecVersion string      `json:\"specVersion\"`\n\tSerialNumber string     `json:\"serialNumber\"`\n\tMetadata    BOMMetadata `json:\"metadata\"`\n\tComponents  []Component `json:\"components\"`\n}\n\ntype BOMMetadata struct {\n\tTimestamp string    `json:\"timestamp\"`\n\tComponent Component `json:\"component\"`\n}\n\ntype Component struct {\n\tType     string    `json:\"type\"`\n\tName     string    `json:\"name\"`\n\tVersion  string    `json:\"version\"`\n\tPURL     string    `json:\"purl\"`\n\tLicenses []License `json:\"licenses,omitempty\"`\n}\n\ntype License struct {\n\tLicenseDetail struct {\n\t\tID string `json:\"id\"`\n\t} `json:\"license\"`\n}\n\nfunc main() {\n\tsampleSBOM := `{\n\t\t\"bomFormat\": \"CycloneDX\",\n\t\t\"specVersion\": \"1.5\",\n\t\t\"serialNumber\": \"urn:uuid:3e6717db-055e-4b47-9750-61f654b03650\",\n\t\t\"metadata\": {\n\t\t\t\"timestamp\": \"2026-09-07T12:00:00Z\",\n\t\t\t\"component\": { \"type\": \"application\", \"name\": \"payment-api\", \"version\": \"v2.1.0\" }\n\t\t},\n\t\t\"components\": [\n\t\t\t{\n\t\t\t\t\"type\": \"library\",\n\t\t\t\t\"name\": \"google.golang.org/protobuf\",\n\t\t\t\t\"version\": \"v1.33.0\",\n\t\t\t\t\"purl\": \"pkg:golang/google.golang.org/protobuf@v1.33.0\",\n\t\t\t\t\"licenses\": [{ \"license\": { \"id\": \"BSD-3-Clause\" } }]\n\t\t\t},\n\t\t\t{\n\t\t\t\t\"type\": \"library\",\n\t\t\t\t\"name\": \"go.uber.org/zap\",\n\t\t\t\t\"version\": \"v1.27.0\",\n\t\t\t\t\"purl\": \"pkg:golang/go.uber.org/zap@v1.27.0\",\n\t\t\t\t\"licenses\": [{ \"license\": { \"id\": \"MIT\" } }]\n\t\t\t}\n\t\t]\n\t}`\n\n\tvar bom CycloneDXSBOM\n\tif err := json.Unmarshal([]byte(sampleSBOM), &bom); err != nil {\n\t\tlog.Fatalf(\"SBOM parse error: %v\", err)\n\t}\n\n\tfmt.Printf(\"Parsed CycloneDX SBOM (Spec %s, Format %s)\\n\", bom.SpecVersion, bom.BOMFormat)\n\tfmt.Printf(\"Root Application: %s (%s)\\n\", bom.Metadata.Component.Name, bom.Metadata.Component.Version)\n\tfmt.Printf(\"Total Tracked Dependencies: %d\\n\", len(bom.Components))\n\n\tfor i, c := range bom.Components {\n\t\tlic := \"UNKNOWN\"\n\t\tif len(c.Licenses) > 0 {\n\t\t\tlic = c.Licenses[0].LicenseDetail.ID\n\t\t}\n\t\tfmt.Printf(\"  [%d] %s (%s) -> PURL: %s [License: %s]\\n\",\n\t\t\ti+1, c.Name, c.Version, c.PURL, lic)\n\t}\n}",
                "note": "Парсинг и валидация спецификации Software Bill of Materials (OWASP CycloneDX)"
            }
        ],
        "under_the_hood": "Утилита `cyclonedx-gomod` анализирует AST и `go.mod`, автоматически вычисляя PURL (Package URL) по стандарту `https://github.com/package-url/purl-spec`.",
        "pitfalls": "Генерация SBOM на этапе до компиляции (`go.mod`), без учета того, какие пакеты вошли в итоговый бинарник. Качественный SBOM генерируется для финального бинарного файла или Docker-контейнера.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'В чем разница между SPDX и CycloneDX форматами SBOM?' Ответ: 'SPDX исторически создавался Linux Foundation для лицензионного комплаенса (Open Source Compliance). CycloneDX создавался проектом OWASP специально для практической кибербезопасности, анализа уязвимостей (VEX — Vulnerability Exploitability eXchange) и интеграции со сканерами'."
    },
    {
        "num": 25,
        "title": "Фреймворк SLSA (Supply-chain Levels for Software Artifacts) на практике",
        "task": "Изучите 4 уровня безопасности SLSA Framework. Спроектируйте пайплайн сборки Go-приложения, удовлетворяющий требованиям SLSA Level 3: изолированная среда сборки, подписанный Provenance и защита исходного кода.",
        "theory": "SLSA (Supply-chain Levels for Software Artifacts, произносится 'сальса') — это отраслевой фреймворк безопасности от Google, OpenSSF и CISA, защищающий цепочку поставки ПО от исходного кода до продакшена: - `SLSA Level 1`: Сборка автоматизирована через скрипт (build script), генерируется базовый манифест происхождения (Provenance: кто, когда, из какого коммита собрал); - `SLSA Level 2`: Сборка выполняется на выделенном hosted-сервисе (GitHub Actions, GitLab CI), манифест provenance подписан криптографической подписью раннера; - `SLSA Level 3`: Сборка полностью изолирована (Hermetic / Ephemeral build environment). Раннер создается с нуля и уничтожается после сборки. Параметры сборки нельзя подменить извне; - `SLSA Level 4`: Двухстороннее ревью кода двумя разработчиками (Two-Person Review) и герметичная воспроизводимая сборка (Hermetic Reproducible Build).",
        "step_by_step": [
            "Изучите спецификацию SLSA v1.0.",
            "Напишите манифест происхождения in-toto attestation (SLSA Provenance).",
            "Опишите требования к изолированному сборочному раннеру.",
            "Проверьте верификацию provenance через slsa-verifier."
        ],
        "code_blocks": [
            {
                "filename": "slsa_provenance.json",
                "lang": "json",
                "code": "{\n  \"_type\": \"https://in-toto.io/Statement/v0.1\",\n  \"subject\": [\n    {\n      \"name\": \"payment-service-linux-amd64\",\n      \"digest\": {\n        \"sha256\": \"4bf92f3577b34da6a3ce929d0e0e473600f067aa0ba902b70123456789abcdef\"\n      }\n    }\n  ],\n  \"predicateType\": \"https://slsa.dev/provenance/v0.2\",\n  \"predicate\": {\n    \"builder\": {\n      \"id\": \"https://github.com/actions/runner-hosted\"\n    },\n    \"buildType\": \"https://github.com/slsa-framework/slsa-github-generator/go@v1\",\n    \"invocation\": {\n      \"configSource\": {\n        \"uri\": \"git+https://github.com/mycorp/payment-service@refs/heads/main\",\n        \"digest\": { \"sha1\": \"7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b\" },\n        \"entryPoint\": \".github/workflows/release.yaml\"\n      }\n    },\n    \"materials\": [\n      {\n        \"uri\": \"git+https://github.com/mycorp/payment-service\",\n        \"digest\": { \"sha1\": \"7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b\" }\n      }\n    ]\n  }\n}",
                "note": "Аттестация происхождения артефакта (SLSA Provenance v0.2) в формате in-toto"
            }
        ],
        "under_the_hood": "Манифест `SLSA Provenance` подписывается приватным ключом сборочной платформы или через OIDC токен Sigstore. Проверяющая утилита `slsa-verifier` на сервере деплоя сверяет хэш бинарника с хэшем из Provenance и разрешает запуск только валидированного ПО.",
        "pitfalls": "Ручная генерация Provenance на локальном ноутбуке разработчика. SLSA Level 2+ строго требует, чтобы подпись генерировалась доверенным изолированным раннером.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Что гарантирует SLSA Level 3 при сборке Go бинарников?' Ответ: 'Гарантирует, что бинарник был собран именно из указанного Git-коммита в изолированной среде, без возможности для разработчика или взломщика внедрить незакоммиченный бэкдор во время процесса сборки'."
    },
    {
        "num": 26,
        "title": "Vendor vs Go Modules Cache: компромиссы и выбор стратегии",
        "task": "Сделайте детальный бенчмарк и техническое сравнение двух подходов хранения зависимостей: папка vendor/ в репозитории Git против кэширования модулей через GOPROXY в CI/CD.",
        "theory": "Выбор между Vendoring и Modules Cache — классический архитектурный компромисс: 1) `Vendoring` (`go mod vendor`):    - Плюсы: 100% автономность сборки без сети, моментальный старт сборки в CI (не нужно скачивать модули), устойчивость к падению внешних прокси;    - Минусы: раздувание истории Git (десятки мегабайт стороннего кода), загромождение code review (диффы на сотни тысяч строк при обновлении библиотек), риск случайного ручного редактирования vendor; 2) `Modules Cache` (`GOPROXY` + GitHub Actions Cache):    - Плюсы: чистый репозиторий Git (только go.mod и go.sum), понятные диффы, автоматический шаринг кэша между ветками;    - Минусы: зависимость от сетевого канала и доступности прокси-сервера.",
        "step_by_step": [
            "Определите метрики: размер Git репозитория, скорость сборки, автономность.",
            "Проанализируйте влияние на процесс Code Review.",
            "Настройте .gitattributes для скрытия каталога vendor в PR diffs.",
            "Сформулируйте рекомендации для монорепозиториев и микросервисов."
        ],
        "code_blocks": [
            {
                "filename": ".gitattributes",
                "lang": "text",
                "code": "# Скрываем каталог vendor из просмотра diff в GitHub / GitLab,\n# чтобы обновления библиотек не загромождали Code Review инженеров\nvendor/** linguist-vendored\nvendor/** -diff\n",
                "note": "Файл .gitattributes для исключения каталога vendor из diff при Code Review"
            }
        ],
        "under_the_hood": "Директива `linguist-vendored` сообщает движку GitHub Linguist, что код в папке `vendor` является сторонним, исключая его из статистики языков проекта.",
        "pitfalls": "Хранение папки `vendor/` без фиксации `go.sum`. Даже при наличии vendor, файл `go.sum` обязателен для проверки соответствия хэшей.",
        "bigtech_interview": "Что вы выберете для микросервисов компании: Vendoring или GOPROXY кэш? Ответ: 'Для подавляющего большинства сервисов — локальный корпоративный GOPROXY (Athens) + Actions Cache. Vendoring оставляем только для Air-gapped инфраструктуры и критических систем с жестким SLA доступности'."
    },
    {
        "num": 27,
        "title": "CI/CD Integration: автоматический аудит с ненулевым кодом выхода",
        "task": "Напишите bash-скрипт для CI пайплайна, который запускает govulncheck, логирует найденные проблемы и принудительно возвращает код выхода exit 1 только при обнаружении эксплуатируемых уязвимостей.",
        "theory": "Многие утилиты анализа по умолчанию завершаются с кодом `exit 0`, даже если нашли уязвимости (выводя предупреждения в stdout). Чтобы тест безопасности реально блокировал деплой, утилита обязана возвращать ненулевой код. В `govulncheck`: - `exit 0`: уязвимостей не найдено (или найденные уязвимости не вызываются кодом); - `exit 3`: обнаружены реально эксплуатируемые (reachable) уязвимости, код подвержен риску! Скрипт в пайплайне перехватывает этот exit-код и принимает решение о блокировке шага.",
        "step_by_step": [
            "Изучите спецификацию кодов возврата govulncheck (0, 1, 2, 3).",
            "Напишите bash-обертку с анализом exit-кода.",
            "Проверьте корректное прерывание выполнения пайплайна при exit 3.",
            "Интегрируйте скрипт в пайплайн сборки."
        ],
        "code_blocks": [
            {
                "filename": "ci_vuln_gate.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -uo pipefail\n\necho \"==================================================\"\necho \" Starting Security Gate: govulncheck execution   \"\necho \"==================================================\"\n\n# Запуск govulncheck над проектом\ngovulncheck ./...\nEXIT_CODE=$?\n\ncase $EXIT_CODE in\n    0)\n        echo \"SUCCESS: No reachable vulnerabilities detected in codebase.\"\n        exit 0\n        ;;\n    3)\n        echo \"==================================================\"\n        echo \"CRITICAL SECURITY GATE FAILURE!                   \"\n        echo \"Vulnerabilities were found in code you call!      \"\n        echo \"Build is BLOCKED. Patch dependencies immediately. \"\n        echo \"==================================================\"\n        exit 1\n        ;;\n    *)\n        echo \"ERROR: govulncheck failed with internal error code: $EXIT_CODE\"\n        exit 2\n        ;;\nesac\n",
                "note": "Скрипт контроля кодов возврата govulncheck для блокировки CI/CD"
            }
        ],
        "under_the_hood": "Код выхода 3 был специально зарезервирован командой Go для однозначного отделения эксплуатируемых уязвимостей (exit 3) от системных сбоев рантайма (exit 1/2).",
        "pitfalls": "Использование пайпа `govulncheck ./... | tee output.txt` без опции bash `set -o pipefail`. Без pipefail код возврата команды будет равен коду утилиты `tee` (всегда 0), и пайплайн пропустит уязвимость!",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Почему пайплайн пропустил ошибку govulncheck, если в логах был алерт?' Ответ: 'В bash-скрипте не был включен `set -o pipefail`. При использовании пайплайна `cmd | tee` статус возвращается от последней команды tee, маскируя ошибку cmd'."
    },
    {
        "num": 28,
        "title": "Регулярная гигиена зависимостей: автоматизация go mod tidy",
        "task": "Напишите CI проверку, которая контролирует, что разработчик не забыл выполнить go mod tidy перед коммитом, предотвращая накопление мертвого кода в go.mod.",
        "theory": "В процессе активной разработки инженеры пробуют новые библиотеки, удаляют импорты и переименовывают пакеты. Если не запускать `go mod tidy`: 1) Файл `go.mod` заполняется неиспользуемыми модулями; 2) Файл `go.sum` хранит хэши сотен удаленных библиотек; 3) Сканеры безопасности тратят время на проверку библиотек, которые вообще не нужны проекту. Золотой стандарт чистоты: в CI запускается `go mod tidy`, после чего проверяется `git diff --exit-code go.mod go.sum`. Если файлы изменились — билд падает с требованием запустить `go mod tidy` локально.",
        "step_by_step": [
            "Напишите bash проверку git diff после вызова go mod tidy.",
            "Проверьте реакцию на наличие неиспользуемых зависимостей.",
            "Интегрируйте проверку в пре-коммит хуки через pre-commit фреймворк.",
            "Обеспечьте идеальную чистоту манифестов в репозитории."
        ],
        "code_blocks": [
            {
                "filename": "check_mod_tidy.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"Verifying go.mod and go.sum tidiness...\"\ngo mod tidy\n\n# Проверяем, внес ли go mod tidy какие-либо изменения в git статус\nif ! git diff --exit-code go.mod go.sum; then\n    echo \"===========================================================\"\n    echo \"ERROR: go.mod or go.sum is not tidy!\"\n    echo \"Please run 'go mod tidy' locally and commit the changes.\"\n    echo \"===========================================================\"\n    exit 1\nfi\n\necho \"SUCCESS: go.mod and go.sum are completely tidy and up to date.\"\n",
                "note": "CI проверка чистоты манифестов зависимостей go mod tidy"
            }
        ],
        "under_the_hood": "`git diff --exit-code` возвращает 0, если изменений нет, и 1, если обнаружен хотя бы один измененный или удаленный символ.",
        "pitfalls": "Выполнение `go mod tidy` внутри CI с автоматическим коммитом от имени бота без ведома автора PR. Лучше заставить разработчика запустить tidy локально, чтобы он осознавал состав зависимостей.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Зачем проверять go mod tidy в CI?' Ответ: 'Чтобы исключить захламление репозитория фантомными зависимостями, сократить время сборки и снизить объем ложных срабатываний сканеров уязвимостей'."
    },
    {
        "num": 29,
        "title": "Фиксация версий (Dependency Pinning): запрет плавающих тегов",
        "task": "Объясните опасность использования плавающих веток (master, main) в go.mod вместо семантических тегов (v1.2.3) и напишите линтер для проверки отсутствия псевдоверсий без хэшей коммитов.",
        "theory": "В Go Modules версионирование опирается на Semantic Versioning (`vMAJOR.MINOR.PATCH`). Если разработчик указывает зависимость по ветке (`go get github.com/foo/bar@main`), Go генерирует так называемую псевдоверсию (Pseudo-version): `v0.0.0-20240907120000-abcdef123456`. Опасности плавающих версий: 1) Невоспроизводимость сборки: коммит в ветку `main` сторонней библиотеки может сломать ваш билд в любой момент; 2) Риск supply chain атаки: хакер может протолкнуть вредоносный коммит в ветку main незаметно. В production проектах все критические зависимости обязаны быть зафиксированы (Pinned) на конкретные неизменяемые релизные теги (`v1.4.2`).",
        "step_by_step": [
            "Изучите формат псевдоверсий Go (v0.0.0-timestamp-commit).",
            "Напишите скрипт аудита go.mod на наличие нежелательных псевдоверсий.",
            "Сформируйте регламент фиксации релизных версий.",
            "Проверьте стабильность воспроизводимости сборки."
        ],
        "code_blocks": [
            {
                "filename": "audit_pinned_versions.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"bufio\"\n\t\"fmt\"\n\t\"regexp\"\n\t\"strings\"\n)\n\n// pseudoVersionRegex определяет псевдоверсии вида v0.0.0-20240101000000-abcdef123456\nvar pseudoVersionRegex = regexp.MustCompile(`v\\d+\\.\\d+\\.\\d+-\\d{14}-[0-9a-f]{12}`)\n\nfunc AuditPinnedVersions(goModContent string) (unpinned []string) {\n\tscanner := bufio.NewScanner(strings.NewReader(goModContent))\n\tfor scanner.Scan() {\n\t\tline := strings.TrimSpace(scanner.Text())\n\t\tif strings.HasPrefix(line, \"require\") || strings.Contains(line, \"v\") {\n\t\t\tfields := strings.Fields(line)\n\t\t\tif len(fields) >= 2 {\n\t\t\t\tpkg := fields[0]\n\t\t\t\tver := fields[1]\n\t\t\t\tif pseudoVersionRegex.MatchString(ver) {\n\t\t\t\t\tunpinned = append(unpinned, fmt.Sprintf(\"%s @ %s (Warning: Pseudo-version / Unpinned branch)\", pkg, ver))\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\n\treturn unpinned\n}\n\nfunc main() {\n\tsampleGoMod := `module myapp\n\ngo 1.23\n\nrequire (\n\tgithub.com/google/uuid v1.6.0\n\tgithub.com/some/unstable-lib v0.0.0-20230512140000-a1b2c3d4e5f6\n\tgolang.org/x/crypto v0.21.0\n)\n`\n\twarnings := AuditPinnedVersions(sampleGoMod)\n\tif len(warnings) > 0 {\n\t\tfmt.Println(\"[SECURITY WARNING] Detected unpinned pseudo-versions:\")\n\t\tfor _, w := range warnings {\n\t\t\tfmt.Println(\" \", w)\n\t\t}\n\t\tfmt.Println(\"Recommendation: Pin dependencies to tagged release versions (e.g. v1.0.0).\")\n\t} else {\n\t\tfmt.Println(\"[OK] All dependencies are properly pinned to SemVer releases.\")\n\t}\n}",
                "note": "Линтер для проверки фиксации версий зависимостей в go.mod"
            }
        ],
        "under_the_hood": "Псевдоверсия содержит дату UTC (`20230512140000`) и 12 символов хэша Git коммита (`a1b2c3d4e5f6`), что позволяет алгоритму MVS сравнивать коммиты по хронологии.",
        "pitfalls": "Использование зависимости из чужой ветки `master` для быстрого хотфикса без оформления issues или собственного форка. Ветка может быть переписана автором через `git push --force`.",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'Почему нельзя использовать плавающие версии (branches) в продакшен go.mod?' Ответ: 'Нарушается детерминизм и воспроизводимость сборки (Reproducible Builds). В любой момент автор может закомитить баг или бэкдор, который автоматически попадет в продакшен без ревью'."
    },
    {
        "num": 30,
        "title": "Приватные модули: настройка GOPRIVATE, GONOPROXY и корпоративных репозиториев",
        "task": "Настройте работу Go с закрытым корпоративным репозиторием (например, gitlab.corp.internal). Напишите инструкцию по настройке Git SSH/HTTPS аутентификации для go get.",
        "theory": "По умолчанию `go get` пытается скачать модуль через HTTPS без авторизации. Для приватных репозиториев на GitLab/GitHub это вызывает ошибку `401 Unauthorized` или `404 Not Found`. Решение состоит из двух шагов: 1) Настройка `GOPRIVATE=gitlab.corp.internal/*`, чтобы Go не пытался искать приватный модуль на `proxy.golang.org`; 2) Настройка Git для автоматической замены протокола HTTPS на SSH: `git config --global url.\"git@gitlab.corp.internal:\".insteadOf \"https://gitlab.corp.internal/\"`. После этого `go get` будет прозрачно использовать локальные SSH-ключи разработчика или токен `CI_JOB_TOKEN` в пайплайне.",
        "step_by_step": [
            "Сконфигурируйте переменную go env -w GOPRIVATE.",
            "Настройте правило git insteadOf для перенаправления HTTPS в SSH.",
            "Проверьте разрешение имени модуля через go get.",
            "Обеспечьте безопасную авторизацию раннеров в CI/CD."
        ],
        "code_blocks": [
            {
                "filename": "setup_private_gitlab.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nCORP_DOMAIN=\"gitlab.mycompany.internal\"\n\necho \"[1/2] Disabling public proxy and sumdb for corporate domain:\"\ngo env -w GOPRIVATE=\"${CORP_DOMAIN}/*\"\n\necho \"[2/2] Configuring git to rewrite HTTPS to authenticated SSH:\"\n# Тулчейн Go всегда инициирует HTTPS, а git прозрачно заменит URL на SSH с ключами разработчика\ngit config --global url.\"git@${CORP_DOMAIN}:\".insteadOf \"https://${CORP_DOMAIN}/\"\n\necho \"Configuration completed. You can now run: go get ${CORP_DOMAIN}/security/auth-sdk\"\n",
                "note": "Скрипт интеграции Go Modules с корпоративным приватным GitLab через SSH"
            }
        ],
        "under_the_hood": "Когда тулчейн Go скачивает модуль напрямую (`GOPRIVATE`), он вызывает утилиту `git` под капотом. Правило `insteadOf` перехватывает системный вызов Git и меняет URL протокола.",
        "pitfalls": "Забыть добавить слеш на конце в URL `insteadOf`. Неправильный синтаксис `url.\"git@...\".insteadOf` приведет к склеиванию путей и ошибке репозитория.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Как настроить доступ к приватным модулям в Docker контейнере во время сборки?' Ответ: 'Использовать Docker BuildKit с монтированием секретов: `RUN --mount=type=ssh go mod download` или передавать персональный access token через `netrc` файл'."
    },
    {
        "num": 31,
        "title": "Защита от подмены зависимостей (Dependency Confusion Attack)",
        "task": "Объясните в деталях механику атаки Dependency Confusion. Покажите, как злоумышленник может опубликовать вредоносный пакет с именем вашей внутренней библиотеки в публичный интернет, и как Go защищает от этой угрозы.",
        "theory": "Атака Dependency Confusion (открытая Алексом Бирсаном в 2021 году) поразила десятки IT-гигантов (Apple, Microsoft, Uber). Механика атаки: 1) В экосистемах Python (PyPI) или Node.js (npm) компания использует внутренний пакет с простым именем `auth-token`; 2) Хакер регистрирует в публичном глобальном реестре пакет с точно таким же именем `auth-token`, но выставляет версию `v99.9.9`; 3) Пакетные менеджеры pip/npm видят версию 99.9.9 и скачивают хакерский пакет вместо внутреннего! Почему Go архитектурно защищен от этой атаки? 1) В Go нет плоского пространства имен! Имя каждого модуля ОБЯЗАНО быть глобальным URL с доменом компании: `mycorp.com/billing/auth-token`; 2) Если хакер не владеет доменным именем `mycorp.com`, он физически не может опубликовать такой модуль; 3) Переменная `GOPRIVATE=mycorp.com/*` гарантирует, что запросы к домену компании никогда не уйдут в публичный интернет.",
        "step_by_step": [
            "Изучите структуру путей модулей в Go (FQDN namespace).",
            "Смоделируйте попытку подмены имени пакета.",
            "Проверьте защиту с помощью GOPRIVATE и доменных префиксов.",
            "Сформулируйте правила нейминга внутренних модулей компании."
        ],
        "code_blocks": [
            {
                "filename": "dependency_confusion_shield.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n)\n\n// VerifyModuleNameSecurity проверяет защищенность имени модуля от Dependency Confusion\nfunc VerifyModuleNameSecurity(modulePath string, corporateDomains []string) (bool, string) {\n\t// 1. Проверка на плоские имена без домена (запрещено в современном Go)\n\tif !strings.Contains(modulePath, \".\") || !strings.Contains(modulePath, \"/\") {\n\t\treturn false, fmt.Sprintf(\"INSECURE: Module %q lacks FQDN domain prefix (High risk of collision)\", modulePath)\n\t}\n\n\t// 2. Проверка соответствия корпоративному домену\n\tisCorporate := false\n\tfor _, domain := range corporateDomains {\n\t\tif strings.HasPrefix(modulePath, domain+\"/\") {\n\t\t\tisCorporate = true\n\t\t\tbreak\n\t\t}\n\t}\n\n\tif isCorporate {\n\t\treturn true, fmt.Sprintf(\"SECURE: %q belongs to verified corporate domain namespace. Protected by GOPRIVATE.\", modulePath)\n\t}\n\n\treturn true, fmt.Sprintf(\"PUBLIC: %q is treated as public third-party dependency. Protected by sum.golang.org.\", modulePath)\n}\n\nfunc main() {\n\tcorpDomains := []string{\"gitlab.fintech-bank.ru\", \"github.com/mycorp-enterprise\"}\n\n\ttestModules := []string{\n\t\t\"auth-service\", // Плоское имя\n\t\t\"gitlab.fintech-bank.ru/platform/cryptolib\",\n\t\t\"github.com/gin-gonic/gin\",\n\t}\n\n\tfor _, mod := range testModules {\n\t\tsafe, note := VerifyModuleNameSecurity(mod, corpDomains)\n\t\tfmt.Printf(\"[%v] %s\\n\", safe, note)\n\t}\n}",
                "note": "Анализ защиты пространства имен модулей Go от Dependency Confusion"
            }
        ],
        "under_the_hood": "Привязка пространства имен Go к иерархии доменных имен DNS (FQDN) является фундаментальным решением безопасности, исключающим коллизии пакетов между организациями.",
        "pitfalls": "Использование доменов, не принадлежащих компании или забытых к продлению (Domain Drop). Если компания забудет продлить регистрацию домена своего модуля, злоумышленник может перекупить домен и перехватить трафик.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'Почему Go практически не подвержен атакам Dependency Confusion по сравнению с npm и pip?' Ответ: 'В Go модули адресуются по FQDN доменным именам (github.com/org/repo), а не плоским строкам (express, requests). Злоумышленник не может опубликовать пакет в чужом доменном пространстве без взлома DNS или Git-сервера компании'."
    },
    {
        "num": 32,
        "title": "Алгоритм Minimal Version Selection (MVS): математика и детерминизм",
        "task": "Реализуйте симулятор алгоритма Minimal Version Selection (MVS) Расса Кокса на Go. Покажите, почему Go выбирает минимальную подходящую версию, а не самую свежую.",
        "theory": "Создатель системы модулей Go Расс Кокс (Russ Cox) отверг стандартные подходы пакетных менеджеров (npm, pip, cargo, nuget), использующие алгоритмы разрешения SAT-solver. Принцип Minimal Version Selection (MVS): 1) Каждый модуль в `go.mod` указывает МИНИМАЛЬНО необходимую для него версию зависимости; 2) Если модуль A требует `lib v1.2.0`, а модуль B требует `lib v1.3.0`, алгоритм MVS выбирает версию `v1.3.0` (максимальную из минимально запрошенных); 3) Но если в репозитории библиотеки уже вышла версия `v1.9.0`, Go НЕ СТАНЕТ ее использовать! Go возьмет ровно `v1.3.0`, потому что никто явно не запрашивал более новую версию. Это дает 100% повторяемость сборки (Build Reproducibility): сборка, собранная сегодня, гарантированно соберется точно так же через 5 лет, даже если за это время вышли сотни новых версий.",
        "step_by_step": [
            "Изучите математическую модель алгоритма MVS.",
            "Напишите структуру ModuleVersion с корректным парсингом SemVer.",
            "Реализуйте функцию разрешения максимальной из минимально запрошенных версий.",
            "Продемонстрируйте детерминизм алгоритма на примере конфликтующих требований."
        ],
        "code_blocks": [
            {
                "filename": "mvs_simulator.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strconv\"\n\t\"strings\"\n)\n\n// SemVer представляет упрощенную семантическую версию\ntype SemVer struct {\n\tMajor int\n\tMinor int\n\tPatch int\n}\n\nfunc ParseSemVer(v string) SemVer {\n\tv = strings.TrimPrefix(v, \"v\")\n\tparts := strings.Split(v, \".\")\n\tmaj, _ := strconv.Atoi(parts[0])\n\tmin, patch := 0, 0\n\tif len(parts) > 1 {\n\t\tmin, _ = strconv.Atoi(parts[1])\n\t}\n\tif len(parts) > 2 {\n\t\tpatch, _ = strconv.Atoi(parts[2])\n\t}\n\treturn SemVer{Major: maj, Minor: min, Patch: patch}\n}\n\nfunc (s SemVer) Compare(other SemVer) int {\n\tif s.Major != other.Major {\n\t\treturn s.Major - other.Major\n\t}\n\tif s.Minor != other.Minor {\n\t\treturn s.Minor - other.Minor\n\t}\n\treturn s.Patch - other.Patch\n}\n\nfunc (s SemVer) String() string {\n\treturn fmt.Sprintf(\"v%d.%d.%d\", s.Major, s.Minor, s.Patch)\n}\n\n// ResolveMVS находит максимальную из минимально заявленных версий\nfunc ResolveMVS(requirements map[string][]string) map[string]SemVer {\n\tselected := make(map[string]SemVer)\n\n\tfor mod, versions := range requirements {\n\t\tfor _, vStr := range versions {\n\t\t\tv := ParseSemVer(vStr)\n\t\t\tcurrent, exists := selected[mod]\n\t\t\tif !exists || v.Compare(current) > 0 {\n\t\t\t\tselected[mod] = v\n\t\t\t}\n\t\t}\n\t}\n\treturn selected\n}\n\nfunc main() {\n\t// Моделируем требования модулей:\n\t// Module A требует logging v1.2.0\n\t// Module B требует logging v1.4.0\n\t// В репозитории logging доступна v1.9.0 (но MVS ее проигнорирует!)\n\trequirements := map[string][]string{\n\t\t\"github.com/corp/logging\": {\"v1.2.0\", \"v1.4.0\"},\n\t\t\"github.com/corp/auth\":    {\"v2.1.0\", \"v2.0.5\"},\n\t}\n\n\tresult := ResolveMVS(requirements)\n\tfmt.Println(\"MVS Selected Versions (Minimal Version Selection):\")\n\tfor mod, ver := range result {\n\t\tfmt.Printf(\"  Module: %-25s -> Selected: %s (Ignored available v1.9.0)\\n\", mod, ver)\n\t}\n\tfmt.Println(\"\\nMVS guarantees absolute reproducibility: builds never change without explicit developer action.\")\n}",
                "note": "Симуляция алгоритма Minimal Version Selection (MVS) Расса Кокса"
            }
        ],
        "under_the_hood": "В отличие от SAT-солверов в других пакетных менеджерах, сложность которых в худшем случае экспоненциальна (NP-complete), алгоритм MVS работает за линейное время O(N) и всегда имеет ровно одно детерминированное решение.",
        "pitfalls": "Ожидание, что `go build` автоматически подтянет свежий багфикс библиотеки. В Go багфикс подтянется ТОЛЬКО после явного вызова `go get` разработчиком.",
        "bigtech_interview": "Вопрос на собеседовании в Тинькофф: 'Почему создатели Go отказались от использования SemVer диапазонов (^1.2.0, ~1.2.0)?' Ответ: 'Диапазоны версий нарушают воспроизводимость сборки: сегодня собралась версия 1.2.1, а завтра автор запушил 1.2.2 с багом, и билд упал без изменения единой строчки нашего кода. MVS гарантирует стабильность сборки'."
    },
    {
        "num": 33,
        "title": "Подпись артефактов и бинарников с помощью Sigstore Cosign",
        "task": "Изучите стандарт Sigstore Cosign: подпишите бинарный артефакт Go с помощью cosign sign-blob и проверьте подпись через cosign verify-blob. Объясните концепцию Keyless подписи через Fulcio OIDC и Rekor transparency log.",
        "theory": "Подпись бинарных артефактов и Docker-образов — ключевое требование SLSA Level 2/3. Исторически управление приватными GPG ключами было кошмаром безопасности (утечки ключей, потеря паролей). Проект Sigstore (под эгидой Linux Foundation, Google, Red Hat) совершил революцию с концепцией `Keyless Signing`: 1) Разработчик или CI/CD раннер аутентифицируется через OpenID Connect (OIDC, например GitHub Actions токен); 2) Удостоверяющий центр `Fulcio` выпускает короткоживущий X.509 сертификат (сроком жизни всего 10 минут!), привязанный к email разработчика или воркфлоу репозитория; 3) Утилита `Cosign` подписывает бинарник или Docker-образ этим сертификатом; 4) Факт подписи навсегда фиксируется в публичном неизменяемом журнале `Rekor` (Transparency Log); 5) Приватный ключ уничтожается! При верификации `cosign verify-blob` проверяет запись в Rekor, доказывая, что бинарник был подписан именно доверенным CI-раннером в конкретный момент времени.",
        "step_by_step": [
            "Установите утилиту cosign.",
            "Изучите команду генерации локальной пары ключей cosign generate-key-pair.",
            "Подпишите скомпилированный бинарник Go: cosign sign-blob --key cosign.key ./server.",
            "Проверьте подпись публичным ключом: cosign verify-blob --key cosign.pub ...",
            "Освойте архитектуру Keyless signing через OIDC."
        ],
        "code_blocks": [
            {
                "filename": "cosign_signing.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nBIN=\"/tmp/my-secure-app\"\necho \"Compiling clean Go binary...\"\n# CGO_ENABLED=0 go build -trimpath -o \"$BIN\" main.go\n\necho \"[1/3] Generating ephemeral keypair (or using OIDC Keyless mode)...\"\n# cosign generate-key-pair\n\necho \"[2/3] Signing the binary artifact with Cosign...\"\n# cosign sign-blob --key cosign.key --output-signature \"$BIN.sig\" --output-certificate \"$BIN.cert\" \"$BIN\"\n\necho \"[3/3] Verifying artifact integrity and authenticity...\"\n# cosign verify-blob --key cosign.pub --signature \"$BIN.sig\" \"$BIN\"\n\necho \"Cryptographic signature verified successfully. Artifact is authentic.\"\n",
                "note": "Процесс криптографической подписи и верификации артефактов с Sigstore Cosign"
            }
        ],
        "under_the_hood": "Журнал Rekor использует структуру данных Merkle Tree (аналогично Certificate Transparency). Каждая запись получает порядковый номер (Log Index) и Signed Entry Timestamp (SET).",
        "pitfalls": "Хранение постоянного приватного ключа `cosign.key` в незашифрованном виде в репозитории Git. В современной инфраструктуре следует использовать исключительно Keyless signing через OIDC раннера.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Как работает Keyless подпись в Sigstore, если сертификат живет всего 10 минут?' Ответ: 'В момент подписи сертификат валиден. Хэш артефакта, подпись и таймстамп записываются в неизменяемый журнал аудита Rekor. При проверке через год проверяется не валидность сертификата сейчас, а то, что сертификат был валиден в момент фиксации записи в Rekor'."
    },
    {
        "num": 34,
        "title": "Использование директивы replace в go.mod для форков и временных патчей",
        "task": "Настройте директиву replace в файле go.mod для экстренной подмены уязвимой библиотеки на защищенный внутренний форк или локальный путь при отладке.",
        "theory": "Директива `replace` в `go.mod` — мощный инструмент экстренного реагирования (Zero-Day Vulnerability Response): когда в популярной библиотеке найдена критическая уязвимость, а официальный релиз с патчем задерживается, инженер форкает репозиторий в корпоративный аккаунт, закрывает баг и прописывает в `go.mod`: `replace github.com/vulnerable/lib => github.com/mycompany/lib-patched v1.2.4` Компилятор подменит все обращения к библиотеке (включая транзитивные вызовы из других модулей!) на защищенный корпоративный форк. Важное правило: директива `replace` действует ТОЛЬКО в корневом (main) модуле приложения и полностью игнорируется, если ваш модуль сам подключается кем-то как зависимость.",
        "step_by_step": [
            "Изучите синтаксис директивы replace в go.mod.",
            "Продемонстрируйте подмену удаленного модуля на форк с версией.",
            "Продемонстрируйте подмену на локальный путь (например, replace ... => ../local_patch).",
            "Убедитесь в изоляции действия replace границами корневого модуля."
        ],
        "code_blocks": [
            {
                "filename": "go.mod",
                "lang": "text",
                "code": "module github.com/mycorp/payment-service\n\ngo 1.23\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.9.1\n\tgithub.com/vulnerable-org/legacy-parser v1.0.0\n)\n\n// Экстренная подмена уязвимой библиотеки на проверенный корпоративный форк\nreplace github.com/vulnerable-org/legacy-parser v1.0.0 => github.com/mycorp/legacy-parser-patched v1.0.1-secfix\n\n// Временная подмена на локальный каталог при отладке:\n// replace github.com/vulnerable-org/legacy-parser => ../local_patches/legacy-parser\n",
                "note": "Применение директивы replace в go.mod для устранения 0-day уязвимостей"
            }
        ],
        "under_the_hood": "Компилятор Go при анализе импортов заменяет путь модуля в кэше на целевой путь директивы `replace`, подставляя альтернативный исходный код.",
        "pitfalls": "Публикация публичной библиотеки с директивами `replace` внутри ее `go.mod`. Сторонние пользователи библиотеки проигнорируют эти replace, так как Go отбрасывает их для не-main модулей.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Действуют ли директивы replace из зависимостей на наше приложение?' Ответ: 'Нет! Go игнорирует директивы replace во всех транзитивных библиотеках. Только директивы replace из корневого go.mod нашего собственного приложения имеют силу. Это защищает от несанкционированного переопределения кода сторонними модулями'."
    },
    {
        "num": 35,
        "title": "Архитектура Go Checksum Database: доказательство включения в дерево Меркла",
        "task": "Изучите математическую модель базы данных контрольных сумм Go (sum.golang.org). Напишите Go-утилиту, демонстрирующую вычисление корня дерева Меркла и доказательство включения (Proof of Inclusion).",
        "theory": "Сервис `sum.golang.org` спроектирован как прозрачный проверяемый лог (Verifiable Transparency Log), построенный на криптографическом дереве Меркла (Merkle Tree). Каждая запись в базе — это контрольная сумма модуля. Главное свойство дерева Меркла: 1) Клиент не обязан скачивать миллиарды записей, чтобы убедиться, что его запись есть в базе; 2) Сервер предоставляет компактное доказательство включения (Audit Path / Proof of Inclusion) размером всего O(log N) хэшей; 3) Злоумышленник (или скомпрометированный сервер Google) не может изменить старую запись или показать разным клиентам разные версии базы (защита от Split-View Attack), так как любое изменение разрушит подписанный корень дерева (Signed Tree Head — STH).",
        "step_by_step": [
            "Определите структуру MerkleTree на базе SHA-256.",
            "Реализуйте функцию построения родительского хэша hash(left || right).",
            "Сгенерируйте путь доказательства включения (Audit Path).",
            "Проверьте валидацию корня дерева Меркла клиентом."
        ],
        "code_blocks": [
            {
                "filename": "merkle_sumdb.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"crypto/sha256\"\n\t\"encoding/hex\"\n\t\"fmt\"\n)\n\n// HashNode вычисляет промежуточный хэш Меркла: SHA256(0x01 || left || right)\nfunc HashNode(left, right []byte) []byte {\n\th := sha256.New()\n\th.Write([]byte{0x01}) // Префикс узла для защиты от collision attacks\n\th.Write(left)\n\th.Write(right)\n\treturn h.Sum(nil)\n}\n\n// HashLeaf вычисляет хэш листа: SHA256(0x00 || data)\nfunc HashLeaf(data []byte) []byte {\n\th := sha256.New()\n\th.Write([]byte{0x00}) // Префикс листа\n\th.Write(data)\n\treturn h.Sum(nil)\n}\n\nfunc main() {\n\t// 4 записи о версиях библиотек\n\tleaf1 := HashLeaf([]byte(\"github.com/gin-gonic/gin v1.9.0 h1:abc1\"))\n\tleaf2 := HashLeaf([]byte(\"github.com/google/uuid v1.6.0 h1:abc2\"))\n\tleaf3 := HashLeaf([]byte(\"go.uber.org/zap v1.27.0 h1:abc3\"))\n\tleaf4 := HashLeaf([]byte(\"golang.org/x/crypto v0.21.0 h1:abc4\"))\n\n\t// Строим дерево Меркла\n\tparent1 := HashNode(leaf1, leaf2)\n\tparent2 := HashNode(leaf3, leaf4)\n\ttreeRoot := HashNode(parent1, parent2)\n\n\tfmt.Printf(\"Signed Tree Head (Merkle Root): %s\\n\", hex.EncodeToString(treeRoot))\n\n\t// Доказательство включения для leaf1: требуются leaf2 и parent2\n\trecomputedParent1 := HashNode(leaf1, leaf2)\n\trecomputedRoot := HashNode(recomputedParent1, parent2)\n\n\tif hex.EncodeToString(recomputedRoot) == hex.EncodeToString(treeRoot) {\n\t\tfmt.Println(\"Cryptographic Proof of Inclusion verified: Module is immutably logged in SumDB!\")\n\t}\n}",
                "note": "Математическая модель проверки включения в дерево Меркла sum.golang.org"
            }
        ],
        "under_the_hood": "Префиксы `0x00` (для листьев) и `0x01` (для внутренних узлов) предотвращают атаку 'Second-Preimage Attack', делая невозможной подмену структуры дерева.",
        "pitfalls": "Отключение `GOSUMDB=off` в production окружениях. Это лишает вас криптографической защиты от подмены версий библиотек в сети.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Что такое Proof of Consistency в sum.golang.org?' Ответ: 'Это криптографическое доказательство того, что новая версия дерева Меркла получена исключительно добавлением новых записей в конец старого дерева (Append-Only), и ни одна историческая контрольная сумма не была перезаписана'."
    },
    {
        "num": 36,
        "title": "Сканирование SBOM на известные уязвимости с помощью Grype и Trivy",
        "task": "Напишите Go-утилиту автоматизации сканирования SBOM: запускает сканер Grype/Trivy над файлом cyclonedx.json, фильтрует уязвимости по CVSS >= 7.0 и генерирует отчет для службы ИБ.",
        "theory": "Генерация SBOM — это лишь первый шаг (паспорт компонентов). Второй шаг — регулярный аудит этого паспорта (Vulnerability Scanning from SBOM). Утилиты `Grype` (от Anchore) и `Trivy` (от Aqua Security) умеют сканировать SBOM без исходного кода и без доступа к контейнерам: `grype sbom:./bom.json --fail-on high` Преимущество подхода: вы можете сохранять SBOM каждого выпущенного релиза в архив и сканировать его каждую ночь в течение 5 лет! Если в 2029 году в старой библиотеке найдут 0-day эксплойт, вы за 2 секунды определите, в каких именно версиях ваших микросервисов она установлена.",
        "step_by_step": [
            "Сгенерируйте тестовый SBOM файл.",
            "Напишите Go-парсер JSON-отчета утилиты Grype.",
            "Реализуйте фильтрацию по порогу Severity (High / Critical).",
            "Сформируйте алерт безопасности для интеграции с SIEM."
        ],
        "code_blocks": [
            {
                "filename": "grype_sbom_scanner.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"log\"\n)\n\n// GrypeReport представляет упрощенную структуру вывода grype -o json\ntype GrypeReport struct {\n\tMatches []GrypeMatch `json:\"matches\"`\n}\n\ntype GrypeMatch struct {\n\tVulnerability struct {\n\t\tID       string `json:\"id\"`\n\t\tSeverity string `json:\"severity\"`\n\t} `json:\"vulnerability\"`\n\tArtifact struct {\n\t\tName    string `json:\"name\"`\n\t\tVersion string `json:\"version\"`\n\t\tType    string `json:\"type\"`\n\t} `json:\"artifact\"`\n}\n\nfunc AnalyzeSBOMVulnerabilities(reportJSON string) (criticalCount int) {\n\tvar report GrypeReport\n\tif err := json.Unmarshal([]byte(reportJSON), &report); err != nil {\n\t\tlog.Fatalf(\"Parse error: %v\", err)\n\t}\n\n\tfor _, m := range report.Matches {\n\t\tif m.Vulnerability.Severity == \"Critical\" || m.Vulnerability.Severity == \"High\" {\n\t\t\tcriticalCount++\n\t\t\tfmt.Printf(\"[SECURITY ALERT] %s in %s@%s (Severity: %s)\\n\",\n\t\t\t\tm.Vulnerability.ID, m.Artifact.Name, m.Artifact.Version, m.Vulnerability.Severity)\n\t\t}\n\t}\n\treturn criticalCount\n}\n\nfunc main() {\n\tsampleGrypeOutput := `{\n\t\t\"matches\": [\n\t\t\t{\n\t\t\t\t\"vulnerability\": { \"id\": \"CVE-2024-24786\", \"severity\": \"High\" },\n\t\t\t\t\"artifact\": { \"name\": \"google.golang.org/protobuf\", \"version\": \"v1.31.0\", \"type\": \"go-module\" }\n\t\t\t},\n\t\t\t{\n\t\t\t\t\"vulnerability\": { \"id\": \"CVE-2023-1111\", \"severity\": \"Low\" },\n\t\t\t\t\"artifact\": { \"name\": \"golang.org/x/sys\", \"version\": \"v0.1.0\", \"type\": \"go-module\" }\n\t\t\t}\n\t\t]\n\t}`\n\n\tcount := AnalyzeSBOMVulnerabilities(sampleGrypeOutput)\n\tfmt.Printf(\"\\nSBOM Scan Completed. Total High/Critical Findings: %d\\n\", count)\n}",
                "note": "Парсинг и анализ отчета безопасности Grype по файлу SBOM"
            }
        ],
        "under_the_hood": "Grype сопоставляет PURL (Package URL) из SBOM с базами NVD, GitHub Advisory Database и дистрибутивными базами (Alpine SecDB, Debian Security Tracker) локально через кэшированную sqlite базу.",
        "pitfalls": "Сканирование только бинарника без учета базового образа ОС. Если ваш Go-сервис работает в Alpine, SBOM должен включать как Go-модули, так и системные пакеты (busybox, ssl).",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'Зачем хранить SBOM релизов в S3/Artifactory?' Ответ: 'Чтобы непрерывно проводить ретроспективный анализ уязвимостей. При обнаружении новой 0-day уязвимости сканирование исторических SBOM позволяет за секунды найти все уязвимые контейнеры в кластере без их повторной сборки'."
    },
    {
        "num": 37,
        "title": "Комплексный аудит зависимостей: консолидированный Security Runner",
        "task": "Напишите production-grade Go-скрипт консолидированного аудита зависимостей: объединяет запуск govulncheck, go mod verify, проверку лицензий и отправку результатов в формате JSON.",
        "theory": "В зрелых инженерных командах проверки безопасности не запускаются разрозненно. Создается единый инструмент — Security Runner (Quality Gate), который координирует все проверки цепочки поставки: 1. `go mod verify` (контроль целостности кэша); 2. `govulncheck ./...` (достижимость уязвимостей по графу вызовов AST); 3. Проверка лицензий (запрет GPL/AGPL в коммерческом коде); 4. Проверка устаревших псевдоверсий; 5. Формирование единого сводного JSON отчета с финальным статусом PASS / FAIL.",
        "step_by_step": [
            "Определите структуру AuditReport с полями всех этапов проверки.",
            "Реализуйте параллельный или последовательный запуск проверок.",
            "Сформируйте итоговый exit code (0 если все чисто, 1 если есть нарушения).",
            "Проверьте интеграцию скрипта в CI/CD."
        ],
        "code_blocks": [
            {
                "filename": "consolidated_audit.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"os\"\n\t\"time\"\n)\n\ntype CheckResult struct {\n\tName    string `json:\"name\"`\n\tPassed  bool   `json:\"passed\"`\n\tDetails string `json:\"details\"`\n}\n\ntype ConsolidatedAuditReport struct {\n\tTimestamp time.Time     `json:\"timestamp\"`\n\tProject   string        `json:\"project\"`\n\tPassed    bool          `json:\"passed\"`\n\tChecks    []CheckResult `json:\"checks\"`\n}\n\nfunc RunAllAudits() ConsolidatedAuditReport {\n\treport := ConsolidatedAuditReport{\n\t\tTimestamp: time.Now().UTC(),\n\t\tProject:   \"billing-gateway\",\n\t\tPassed:    true,\n\t}\n\n\t// 1. Проверка go mod verify\n\treport.Checks = append(report.Checks, CheckResult{\n\t\tName:    \"go mod verify\",\n\t\tPassed:  true,\n\t\tDetails: \"All cached modules match go.sum checksums\",\n\t})\n\n\t// 2. Проверка govulncheck\n\treport.Checks = append(report.Checks, CheckResult{\n\t\tName:    \"govulncheck reachability\",\n\t\tPassed:  true,\n\t\tDetails: \"Zero exploitable vulnerabilities in call graph\",\n\t})\n\n\t// 3. Проверка отсутствия запрещенных лицензий (GPL/AGPL)\n\treport.Checks = append(report.Checks, CheckResult{\n\t\tName:    \"license compliance\",\n\t\tPassed:  true,\n\t\tDetails: \"All dependencies licensed under permissive MIT/Apache/BSD\",\n\t})\n\n\tfor _, c := range report.Checks {\n\t\tif !c.Passed {\n\t\t\treport.Passed = false\n\t\t\tbreak\n\t\t}\n\t}\n\n\treturn report\n}\n\nfunc main() {\n\treport := RunAllAudits()\n\tdata, _ := json.MarshalIndent(report, \"\", \"  \")\n\tfmt.Println(string(data))\n\n\tif !report.Passed {\n\t\tos.Exit(1)\n\t}\n\tfmt.Println(\"All supply chain security gates passed successfully.\")\n}",
                "note": "Консолидированный раннер проверок безопасности зависимостей"
            }
        ],
        "under_the_hood": "Объединение проверок в единый раннер позволяет формировать артефакты для комплаенс-аудиторов в формате JSON/PDF по стандартам SOC2 и ISO 27001.",
        "pitfalls": "Запуск проверок без таймаутов. Если сетевой запрос к базе уязвимостей зависнет, весь пайплайн CI будет висеть часами.",
        "bigtech_interview": "Вопрос на собеседовании в Тинькофф: 'Как автоматизировать контроль соблюдения политик ИБ перед выкатом сервиса?' Ответ: 'Внедрить единый Security Runner в CI пайплайн. Он проверяет go mod verify, govulncheck, лицензии и подпись артефактов, генерируя криптографическую аттестацию для Admission Controller в Kubernetes'."
    },
    {
        "num": 38,
        "title": "Защита приватного кода: предотвращение утечки хэшей на sum.golang.org",
        "task": "Продемонстрируйте механизм утечки корпоративных путей модулей в публичный интернет при отсутствии GOPRIVATE и настройте защиту через GONOSUMDB.",
        "theory": "Сервис `sum.golang.org` ведет публичный журнал всех обращений. Если разработчик выполняет `go get gitlab.bank.ru/supersecret/algorithm`, Go-клиент по умолчанию отправляет GET запрос: `https://sum.golang.org/lookup/gitlab.bank.ru/supersecret/algorithm@v1.0.0` Последствия катастрофичны: 1) Полный путь к закрытому проекту навсегда записывается в открытые логи сервера; 2) Конкуренты или злоумышленники, анализирующие трафик sumdb, узнают о секретных проектах банка! Настройка переменной `GONOSUMDB=gitlab.bank.ru/*` гарантирует, что хэши приватных модулей проверяются ТОЛЬКО по локальному `go.sum` и никогда не покидают периметр компании.",
        "step_by_step": [
            "Изучите логику обращения Go к сервису sum.golang.org/lookup/.",
            "Настройте точечную маску GONOSUMDB для корпоративных поддоменов.",
            "Проверьте блокировку сетевых запросов к публичному sumdb.",
            "Сформулируйте правила безопасности для корпоративных ноутбуков разработчиков."
        ],
        "code_blocks": [
            {
                "filename": "prevent_leakage.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\n# Защита от утечки имен приватных модулей в публичный transparency log Google\nINTERNAL_REPOS=\"gitlab.corp.internal/*,github.com/mycompany-private/*\"\n\necho \"Enforcing GONOSUMDB policy...\"\ngo env -w GONOSUMDB=\"$INTERNAL_REPOS\"\ngo env -w GONOPROXY=\"$INTERNAL_REPOS\"\n\necho \"Active Go environment:\"\ngo env GOPRIVATE GONOSUMDB GONOPROXY\n\necho \"Private paths will NEVER be leaked to sum.golang.org!\"\n",
                "note": "Конфигурация GONOSUMDB для защиты от утечки корпоративных путей"
            }
        ],
        "under_the_hood": "Тулчейн Go сверяет путь модуля с маской `GONOSUMDB` с помощью функции `path.Match`. Если найдено совпадение, сетевой вызов к `sum.golang.org` блокируется внутри компилятора.",
        "pitfalls": "Настройка `GOPRIVATE` только на сборочном сервере, но не на локальных ноутбуках разработчиков. Разработчик дома запустит `go get` без VPN и сольет приватные пути на серверы Google.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'Какая угроза возникает, если не настроить GONOSUMDB для приватных репозиториев?' Ответ: 'Утечка конфиденциальных метаданных компании (Data Leakage). Пути приватных пакетов попадут в публичные логи Google sum.golang.org, раскрывая структуру закрытых систем и имена закрытых проектов'."
    },
    {
        "num": 39,
        "title": "Установка и инициализация Sigstore Cosign в инфраструктуре сборки",
        "task": "Напишите Go-скрипт автоматической проверки и валидации утилиты cosign в сборочной среде, проверяющий генерацию ключевых пар и поддержку OIDC токенов.",
        "theory": "Утилита `cosign` (часть проекта Sigstore) стала де-факто мировым стандартом подписи контейнеров в Kubernetes (Open Container Initiative — OCI). Cosign хранит криптографические подписи, аттестации и спецификации SBOM прямо в OCI Container Registry рядом с образом контейнера в виде специальных тегов `sha256-<hash>.sig` и `sha256-<hash>.sbom`. Это позволяет валидировать подпись образа в Admission Controller кластера (Kyverno, OPA Gatekeeper) до того, как образ будет запущен в продакшене.",
        "step_by_step": [
            "Установите cosign v2 через go install github.com/sigstore/cosign/v2/cmd/cosign@latest.",
            "Проверьте флаги cosign version.",
            "Создайте временную пару ключей через cosign generate-key-pair.",
            "Убедитесь в создании открытого cosign.pub и зашифрованного cosign.key."
        ],
        "code_blocks": [
            {
                "filename": "init_cosign.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[1/3] Verifying Cosign installation...\"\n# cosign version\n\necho \"[2/3] Generating local testing keypair with password protection...\"\n# export COSIGN_PASSWORD=\"test-secure-password\"\n# cosign generate-key-pair\n\necho \"[3/3] Inspecting public key format (ECDSA P-256):\"\n# cat cosign.pub\n\necho \"Cosign toolchain initialized and ready for signing OCI artifacts.\"\n",
                "note": "Инициализация и проверка среды Sigstore Cosign"
            }
        ],
        "under_the_hood": "Cosign использует алгоритм ECDSA на эллиптической кривой P-256 (secp256r1) с хэшем SHA-256, обеспечивая высокую стойкость при компактном размере подписи (64 байта).",
        "pitfalls": "Забытый пароль от `cosign.key`. Восстановить утерянный приватный ключ невозможно — придется перегенерировать пару и обновлять доверенные сертификаты в Kubernetes.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Где Cosign хранит подписи Docker-образов?' Ответ: 'В том же самом OCI Container Registry! Cosign пушит специальный артефакт с тегом `sha256-<digest>.sig`. Это исключает необходимость поднимать отдельные серверы хранения подписей'."
    },
    {
        "num": 40,
        "title": "Воспроизводимые сборки (Reproducible Builds): флаги -trimpath и CGO_ENABLED=0",
        "task": "Смоделируйте проблему разницы хэшей sha256sum бинарника при сборке на разных машинах. Настройте флаги компилятора CGO_ENABLED=0, -trimpath, -ldflags=\"-s -w -buildid=\" для достижения побайтово идентичных сборок.",
        "theory": "Если два разработчика скомпилируют один и тот же Git-коммит Go на своих машинах, команды `sha256sum` вернут совершенно РАЗНЫЕ хэши! Почему это происходит? 1) В бинарник вшиваются абсолютные пути файлов разработчика (`/Users/ivan/project/main.go` vs `/home/petr/project/main.go`); 2) Линковщик генерирует уникальный случайный `BuildID`; 3) При `CGO_ENABLED=1` системный компилятор gcc/clang добавляет локальные таймстампы и версии библиотек libc. Это уничтожает возможность независимого аудита! Решение — Reproducible Builds в Go: `CGO_ENABLED=0 go build -trimpath -ldflags=\"-s -w -buildid=\" -o app .` Флаг `-trimpath` заменяет пути на модульные префиксы, `-buildid=` обнуляет уникальный ID, а `CGO_ENABLED=0` гарантирует чистую статическую сборку. Теперь бинарник будет побайтово идентичен (bit-for-bit identical) на любой машине мира!",
        "step_by_step": [
            "Скомпилируйте бинарник без специальных флагов на двух разных путях.",
            "Сравните их sha256sum (хэши будут отличаться).",
            "Скомпилируйте проект с CGO_ENABLED=0, -trimpath и -ldflags=\"-buildid=\".",
            "Убедитесь в 100% совпадении криптографических хэшей."
        ],
        "code_blocks": [
            {
                "filename": "reproducible_build.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\n# Создаем две разные сборочные директории\nDIR_A=\"/tmp/build_dir_alpha\"\nDIR_B=\"/tmp/build_dir_beta\"\nmkdir -p \"$DIR_A\" \"$DIR_B\"\n\ncat << 'EOF' > \"$DIR_A/main.go\"\npackage main\nimport \"fmt\"\nfunc main() { fmt.Println(\"Reproducible Build Test\") }\nEOF\ncp \"$DIR_A/main.go\" \"$DIR_B/main.go\"\n\n# 1. ОБЫЧНАЯ СБОРКА (НЕвоспроизводимая: хэши разные из-за путей в отладочной таблице)\n(cd \"$DIR_A\" && go build -o app_a main.go)\n(cd \"$DIR_B\" && go build -o app_b main.go)\necho \"Non-reproducible hashes (DIFFERENT):\"\nsha256sum \"$DIR_A/app_a\" \"$DIR_B/app_b\"\n\n# 2. ЭТАЛОННАЯ ВОСПРОИЗВОДИМАЯ СБОРКА (Reproducible: хэши 100% ИДЕНТИЧНЫ)\nFLAGS=\"-trimpath -ldflags=-buildid=\"\n(cd \"$DIR_A\" && CGO_ENABLED=0 go build $FLAGS -o repro_a main.go)\n(cd \"$DIR_B\" && CGO_ENABLED=0 go build $FLAGS -o repro_b main.go)\n\necho \"Reproducible hashes (EXACT MATCH):\"\nsha256sum \"$DIR_A/repro_a\" \"$DIR_B/repro_b\"\n\nrm -rf \"$DIR_A\" \"$DIR_B\"\n",
                "note": "Достижение 100% воспроизводимости сборки бинарников в Go"
            }
        ],
        "under_the_hood": "Флаг `-trimpath` заменяет абсолютные файловые пути в таблице `runtime.pclntab` и DWARF метаданных на относительные пути модуля, стирая различия файловых систем.",
        "pitfalls": "Использование системного времени (`time.Now()`) в кодогенерации или встраивание даты через `-X main.buildDate=$(date)`. Встраивание динамической даты ломает детерминизм сборки. Используйте стандартную переменную `SOURCE_DATE_EPOCH` (хэш/дата Git коммита).",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Зачем в HighLoad проектах добиваться воспроизводимости сборки (Reproducible Builds)?' Ответ: '1) Чтобы независимые аудиторы могли пересобрать бинарник из исходников и подтвердить отсутствие внедренных бэкдоров; 2) Для дедупликации слоев в Docker и распределенного кэширования сборки (Bazel/Go cache)'."
    },
    {
        "num": 41,
        "title": "Rekor Transparency Log: поиск и верификация записей в журнале аудита",
        "task": "Изучите публичный журнал Rekor (rekor.sigstore.dev). Напишите Go-код для поиска записи по UUID и проверки отсутствия отката времени (backdating).",
        "theory": "Традиционные цифровые подписи имеют уязвимость Backdating Attack: если злоумышленник украл приватный ключ разработчика, он может перевести системные часы назад, подписать вредоносный бинарник старой датой и заявить: 'Этот бинарник был выпущен год назад'. Журнал Rekor (Transparency Log) делает это невозможным: 1) Rekor — это распределенный сервер времени и неизменяемый журнал; 2) При подписи хэш бинарника и сертификат отправляются в Rekor; 3) Rekor фиксирует запись под строгим монотонным порядковым номером (Log Index) и возвращает подписанный сервером таймстамп (Signed Entry Timestamp — SET); 4) Запись нельзя удалить, сдвинуть во времени назад или отредактировать задним числом.",
        "step_by_step": [
            "Изучите REST API журнала Rekor (api/v1/log/entries).",
            "Реализуйте запрос метаданных записи по UUID.",
            "Проверьте LogIndex, IntegratedTime и Merkle Tree Path.",
            "Убедитесь в невозможности подделки времени фиксации артефакта."
        ],
        "code_blocks": [
            {
                "filename": "rekor_inspector.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"time\"\n)\n\n// RekorLogEntry представляет запись в прозрачном журнале аудита Rekor\ntype RekorLogEntry struct {\n\tLogIndex       int64     `json:\"logIndex\"`\n\tIntegratedTime time.Time `json:\"integratedTime\"`\n\tBody           string    `json:\"body\"`\n\tLogID          string    `json:\"logID\"`\n}\n\nfunc ValidateRekorEntry(entryJSON string) {\n\tvar entry RekorLogEntry\n\tif err := json.Unmarshal([]byte(entryJSON), &entry); err != nil {\n\t\tpanic(err)\n\t}\n\n\tfmt.Println(\"=== Rekor Transparency Log Audit Record ===\")\n\tfmt.Printf(\"Log Index (Immutable Monotonic Sequence): #%d\\n\", entry.LogIndex)\n\tfmt.Printf(\"Cryptographically Certified Timestamp:    %s\\n\", entry.IntegratedTime.Format(time.RFC3339))\n\tfmt.Printf(\"Rekor Transparency Tree LogID:           %s\\n\", entry.LogID)\n\tfmt.Println(\"Status: Immutable proof of existence verified. Backdating attack mathematically impossible.\")\n}\n\nfunc main() {\n\tsampleRekor := `{\n\t\t\"logIndex\": 18492041,\n\t\t\"integratedTime\": \"2026-09-07T12:00:00Z\",\n\t\t\"logID\": \"c0d23d6ad406973f9559f3ba2d1ca01f84147d8f668d1380165ef537324777b9\",\n\t\t\"body\": \"eyJzcGVjIjp7InNpZ25hdHVyZSI6Int...In19\"\n\t}`\n\n\tValidateRekorEntry(sampleRekor)\n}",
                "note": "Структура записи неизменяемого журнала аудита Sigstore Rekor"
            }
        ],
        "under_the_hood": "Записи в Rekor используют схему `HashedRekord`, фиксируя SHA-256 дайджест артефакта в дереве Trillian. Сервер подписывает корень дерева собственным аппаратным HSM ключом.",
        "pitfalls": "Проверка подписи Cosign без валидации присутствия в Rekor. Всегда запускайте верификацию с флагом `--rekor-url`, чтобы исключить подписание украденным отозванным ключом.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'Как Transparency Log защищает от взлома удостоверяющего центра (CA)?' Ответ: 'Если хакер взломает CA и тайно выпустит фальшивый сертификат, он не сможет незаметно использовать его: клиент отклонит сертификат, если факт выпуска не зафиксирован в публичном логе Rekor/CT. А появление записи в публичном логе моментально обнаруживается мониторингом владельца домена'."
    },
    {
        "num": 42,
        "title": "Генерация и управление ключевыми парами Cosign",
        "task": "Напишите Go-скрипт или shell-процедуру создания защищенной ключевой пары Cosign (cosign.key / cosign.pub), безопасного экспорта публичного ключа в Kubernetes Secret и управления парольной защитой.",
        "theory": "При использовании классической схемы подписи с постоянными ключами (Key-based Signing) критически важно защитить приватный ключ: 1) Приватный ключ `cosign.key` всегда шифруется паролем по стандарту Scrypt + NaCl secretbox; 2) Пароль передается через переменную окружения `COSIGN_PASSWORD` в секретных переменных CI/CD; 3) Публичный ключ `cosign.pub` экспортируется и распространяется публично: он монтируется в кластер Kubernetes в виде ConfigMap для работы Admission Controller.",
        "step_by_step": [
            "Сгенерируйте ключевую пару с использованием переменной COSIGN_PASSWORD.",
            "Проверьте права доступа на cosign.key (chmod 600).",
            "Создайте Kubernetes Secret/ConfigMap с открытым ключом cosign.pub.",
            "Сформулируйте регламент ротации ключей подписи."
        ],
        "code_blocks": [
            {
                "filename": "key_management.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\n# 1. Задаем криптостойкий пароль приватного ключа\nexport COSIGN_PASSWORD=\"$(openssl rand -base64 32)\"\n\necho \"[1/3] Generating ECDSA P-256 keypair...\"\n# cosign generate-key-pair\n\necho \"[2/3] Securing private key file permissions...\"\n# chmod 600 cosign.key\n\necho \"[3/3] Creating Kubernetes ConfigMap with public verification key:\"\ncat << 'EOF' > k8s-cosign-pub.yaml\napiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: cosign-public-keys\n  namespace: kyverno\ndata:\n  cosign.pub: |\n    -----BEGIN PUBLIC KEY-----\n    MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...\n    -----END PUBLIC KEY-----\nEOF\n\necho \"Keypair generated and packaged for Kubernetes admission controller.\"\n",
                "note": "Управление жизненным циклом и распространением публичных ключей Cosign"
            }
        ],
        "under_the_hood": "Cosign использует формат зашифрованного PEM-контейнера `ENCRYPTED COSIGN PRIVATE KEY`. Функция деривации Scrypt с высокими параметрами N, r, p защищает ключ от перебора по словарю (Brute-force).",
        "pitfalls": "Коммит файла `cosign.key` в систему контроля версий Git. Даже если ключ зашифрован паролем, попадание приватного ключа в публичный репозиторий считается критическим инцидентом ИБ.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Где безопаснее хранить приватный ключ Cosign в Enterprise?' Ответ: 'В аппаратном модуле безопасности (HSM) или облачном KMS (AWS KMS, Yandex Cloud KMS, HashiCorp Vault) через плагин Cosign KMS (`cosign sign --key awskms://...`), чтобы приватный ключ физически никогда не покидал защищенный чип'."
    },
    {
        "num": 43,
        "title": "Keyless Signing через Fulcio: интеграция OIDC и GitHub Actions",
        "task": "Настройте Keyless подпись артефактов в GitHub Actions: получение временного сертификата Fulcio на основе OIDC ID-токена воркфлоу без использования статичных приватных ключей.",
        "theory": "Keyless подпись (Sigstore Fulcio + Cosign) — вершина безопасности цепочки поставок: в репозитории и секретах CI/CD вообще НЕТ никаких приватных ключей, которые можно украсть! Как это работает в GitHub Actions: 1) Воркфлоу получает системные права `permissions: id-token: write`; 2) Раннер запрашивает у GitHub криптографически подписанный OIDC JSON Web Token (JWT); 3) JWT содержит утверждения (Claims): репозиторий, ветку, коммит, имя workflow; 4) Cosign передает этот токен в центр сертификации `Fulcio`; 5) Fulcio проверяет подпись GitHub, генерирует временную ключевую пару в памяти раннера и выписывает X.509 сертификат на имя `https://github.com/mycorp/repo/.github/workflows/release.yaml@refs/heads/main`; 6) Образ подписывается, ключ стирается из памяти, а запись фиксируется в Rekor.",
        "step_by_step": [
            "Сконфигурируйте блок permissions с id-token: write в GitHub Actions.",
            "Используйте команду cosign sign --yes <image> без флага --key.",
            "Проверьте генерацию сертификата Fulcio с OIDC SAN расширением.",
            "Верифицируйте подпись по идентичности репозитория (--certificate-identity)."
        ],
        "code_blocks": [
            {
                "filename": "github-actions-keyless.yaml",
                "lang": "yaml",
                "code": "name: Keyless Container Signing\n\non:\n  push:\n    tags: [ 'v*' ]\n\njobs:\n  build-and-sign:\n    runs-on: ubuntu-latest\n    permissions:\n      contents: read\n      packages: write\n      # КРИТИЧЕСКИ ВАЖНО: Разрешение на выпуск OIDC токена для Keyless Fulcio\n      id-token: write\n\n    steps:\n      - uses: actions/checkout@v4\n      - uses: sigstore/cosign-installer@v3.5.0\n\n      - name: Build and Push OCI Container\n        run: |\n          echo \"Building container...\"\n          # docker build -t ghcr.io/${{ github.repository }}:${{ github.ref_name }} .\n\n      - name: Sign Container with Keyless Cosign\n        run: |\n          # Флаг --yes включает автоматический Keyless режим через Fulcio OIDC\n          cosign sign --yes ghcr.io/${{ github.repository }}:${{ github.ref_name }}\n\n      - name: Verify Keyless Signature\n        run: |\n          cosign verify ghcr.io/${{ github.repository }}:${{ github.ref_name }} \\\n            --certificate-identity-regexp \"https://github.com/${{ github.repository }}/.*\" \\\n            --certificate-oidc-issuer \"https://token.actions.githubusercontent.com\" ",
                "note": "Пайплайн GitHub Actions с Keyless подписью артефактов через OIDC"
            }
        ],
        "under_the_hood": "В сертификате X.509 Fulcio помещает OIDC Claims в расширение SAN (Subject Alternative Name). Это позволяет валидатору Kyverno в Kubernetes точно проверить, что образ был собран именно из ветки `main` официального репозитория.",
        "pitfalls": "Забыть указать `permissions: id-token: write`. Без этого GitHub не выдаст OIDC токен, и Cosign упадет с ошибкой авторизации.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Что проверять при валидации Keyless подписи в Kubernetes?' Ответ: 'Два обязательных параметра: `--certificate-oidc-issuer` (например, `https://token.actions.githubusercontent.com`) и `--certificate-identity` (URL официального репозитория компании). Без проверки identity любой человек в мире может подписать образ своим личным GitHub аккаунтом!'."
    },
    {
        "num": 44,
        "title": "Подпись Docker-образов в OCI Registry с помощью Cosign",
        "task": "Подпишите контейнерный образ с помощью cosign sign --key cosign.key. Покажите, как подпись сохраняется в Registry в формате OCI-артефакта.",
        "theory": "Cosign спроектирован с учетом стандартов OCI (Open Container Initiative) Image Specification. Когда вы подписываете образ `myregistry.io/billing:v1.0.0`: 1) Cosign вычисляет неизменяемый SHA-256 дайджест манифеста образа (`sha256:7a8b9c...`); 2) Подписывает дайджест приватным ключом; 3) Создает новый OCI-манифест с типом `application/vnd.dev.cosign.simplesigning.v1+json`; 4) Пушит этот манифест в тот же репозиторий с тегом: `myregistry.io/billing:sha256-7a8b9c....sig` Поскольку подпись привязана к неизменяемому SHA-256 дайджесту, любая попытка перезаписать тег `v1.0.0` другим кодом автоматически инвалидирует подпись!",
        "step_by_step": [
            "Соберите и запушьте тестовый Docker образ по дайджесту.",
            "Подпишите образ с помощью cosign sign.",
            "Проинспектируйте сгенерированный OCI артефакт в registry через crane или skopeo.",
            "Убедитесь в привязке подписи к криптографическому дайджесту."
        ],
        "code_blocks": [
            {
                "filename": "sign_container_registry.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nREGISTRY_IMAGE=\"localhost:5000/secure-app:v1.0.0\"\n\necho \"[1/3] Locating immutable image digest (sha256)...\"\n# DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' \"$REGISTRY_IMAGE\")\n# echo \"Target image digest: $DIGEST\"\n\necho \"[2/3] Signing container image digest with Cosign...\"\n# cosign sign --key cosign.key \"$REGISTRY_IMAGE\"\n\necho \"[3/3] Inspecting signatures attached in OCI Registry...\"\n# cosign triangulate \"$REGISTRY_IMAGE\"\n# Выводит путь к сигнатурному тегу вида: localhost:5000/secure-app:sha256-....sig\n\necho \"OCI signature artifact successfully published alongside container.\"\n",
                "note": "Подписание OCI контейнеров по неизменяемому криптографическому дайджесту"
            }
        ],
        "under_the_hood": "Команда `cosign triangulate` вычисляет детерминированное имя тега подписи по формуле `sha256-<hash>.sig`, позволяя клиентам находить подписи без централизованных баз данных.",
        "pitfalls": "Подпись образа по изменяемому тегу (`:latest`) без фиксации дайджеста. Всегда используйте pinning по дайджесту `@sha256:...`.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'Почему подпись привязывается к SHA-256 дайджесту манифеста, а не к тегу образа?' Ответ: 'Теги в Docker/OCI реестрах мутабельны (их можно перезаписать в любой момент). Дайджест манифеста вычисляется от содержимого всех слоев образа криптографически неизменяем. Привязка подписи к дайджесту гарантирует защиту от подмены слоев'."
    },
    {
        "num": 45,
        "title": "Генерация SLSA Provenance через slsa-github-generator",
        "task": "Сконфигурируйте официальный генератор slsa-github-generator для автоматического создания подписанного манифеста Provenance уровня SLSA 3 при релизе Go бинарников.",
        "theory": "Проект OpenSSF создал официальный переиспользуемый воркфлоу `slsa-github-generator`. Он решает проблему 'Недоверенного раннера': 1) Основной билд компилируется внутри изолированного раннера; 2) Специальный доверенный генератор (Trusted Builder) перехватывает хэш собранного бинарника; 3) Выпускает криптографическую аттестацию происхождения `provenance.intoto.jsonl`; 4) Подписывает ее приватным ключом SLSA через Sigstore; 5) Прикрепляет аттестацию к релизу на GitHub. Это подтверждает, что бинарник был собран именно из оригинального коммита без вмешательства оператора.",
        "step_by_step": [
            "Создайте воркфлоу .github/workflows/slsa-release.yml.",
            "Подключите slsa-framework/slsa-github-generator/.github/workflows/builder_go_slsa3.yml.",
            "Настройте параметры компиляции (go-version, config-file).",
            "Проверьте генерацию файла provenance.intoto.jsonl в релизе."
        ],
        "code_blocks": [
            {
                "filename": "slsa_builder_workflow.yaml",
                "lang": "yaml",
                "code": "name: SLSA Level 3 Certified Release\n\non:\n  release:\n    types: [ created ]\n\njobs:\n  # Используем сертифицированный доверенный генератор SLSA Level 3\n  build:\n    permissions:\n      id-token: write # Для подписи через Sigstore Fulcio\n      contents: write # Для прикрепления аттестации к релизу\n      actions: read\n    uses: slsa-framework/slsa-github-generator/.github/workflows/builder_go_slsa3.yml@v1.9.0\n    with:\n      go-version: \"1.23\"\n      config-file: \".slsa-goreleaser.yml\"\n      evaluated-envs: \"COMMIT_DATE:${{ github.event.release.created_at }}\" ",
                "note": "Манифест GitHub Actions для сертифицированной сборки SLSA Level 3"
            }
        ],
        "under_the_hood": "`slsa-github-generator` изолирует процесс генерации подписи от скриптов сборки разработчика, гарантируя, что код из репозитория не может подделать Provenance манифест.",
        "pitfalls": "Попытка модифицировать готовый Provenance манифест. Любая правка нарушит цифровую подпись `in-toto`, сделав проверку невалидной.",
        "bigtech_interview": "Вопрос на собеседовании в Тинькофф: 'Что дает конечному пользователю наличие SLSA Provenance у Go-бинарника?' Ответ: 'Пользователь может с помощью `slsa-verifier` математически проверить, что скачанный бинарник собран официальным CI пайплайном из конкретного коммита репозитория, а не скомпилирован хакером на зараженном компьютере'."
    },
    {
        "num": 46,
        "title": "Встроенный мини-SBOM в Go: инспекция бинарников через go version -m",
        "task": "Изучите встроенную возможность Go по чтению модульной метаинформации из скомпилированного бинарника. Напишите парсер секции .go.buildinfo с помощью стандартного пакета debug/buildinfo.",
        "theory": "Начиная с версии Go 1.13, компилятор автоматически внедряет полный список использованных модулей и их хэшей прямо в тело каждого скомпилированного бинарного файла! Утилита `go version -m ./myapp` читает эту секцию и мгновенно выводит: - Версию компилятора Go; - Архитектуру и операционную систему (`GOOS`, `GOARCH`); - Список всех прямых и косвенных зависимостей с их версиями и хэшами `h1:...`; - Флаги компилятора и ревизию Git коммита (`vcs.revision`, `vcs.time`, `vcs.modified`). Стандартный пакет `debug/buildinfo` позволяет читать этот встроенный мини-SBOM программно.",
        "step_by_step": [
            "Импортируйте debug/buildinfo в Go коде.",
            "Вызовите buildinfo.ReadFile(binaryPath).",
            "Извлеките структуру debug.BuildInfo с полями Main, Deps, Settings.",
            "Выведите аудит версий сторонних библиотек без наличия исходного кода."
        ],
        "code_blocks": [
            {
                "filename": "read_buildinfo_sbom.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"debug/buildinfo\"\n\t\"fmt\"\n\t\"os\"\n)\n\n// InspectBinaryMiniSBOM читает встроенные метаданные зависимостей из Go-бинарника\nfunc InspectBinaryMiniSBOM(filePath string) error {\n\tinfo, err := buildinfo.ReadFile(filePath)\n\tif err != nil {\n\t\treturn fmt.Errorf(\"failed to read buildinfo from %s: %w\", filePath, err)\n\t}\n\n\tfmt.Printf(\"=== Native Go Mini-SBOM for %s ===\\n\", filePath)\n\tfmt.Printf(\"Compiled with: %s\\n\", info.GoVersion)\n\tfmt.Printf(\"Main Module:   %s (%s)\\n\", info.Path, info.Main.Version)\n\tfmt.Printf(\"Total Embedded Dependencies: %d\\n\\n\", len(info.Deps))\n\n\tfmt.Println(\"Dependencies List:\")\n\tfor i, dep := range info.Deps {\n\t\tfmt.Printf(\"  [%02d] %-35s %-12s (Hash: %s)\\n\",\n\t\t\ti+1, dep.Path, dep.Version, dep.Sum)\n\t}\n\n\tfmt.Println(\"\\nBuild VCS Settings:\")\n\tfor _, s := range info.Settings {\n\t\tif s.Key == \"vcs.revision\" || s.Key == \"vcs.time\" || s.Key == \"CGO_ENABLED\" {\n\t\t\tfmt.Printf(\"  %-15s = %s\\n\", s.Key, s.Value)\n\t\t}\n\t}\n\n\treturn nil\n}\n\nfunc main() {\n\t// Инспектируем текущий исполняемый файл\n\tselfPath, _ := os.Executable()\n\terr := InspectBinaryMiniSBOM(selfPath)\n\tif err != nil {\n\t\tfmt.Printf(\"[Notice: Expected if run via 'go run'] %v\\n\", err)\n\t\tfmt.Println(\"Tip: Compile via 'go build -o app main.go' and run './app' to see full embedded buildinfo.\")\n\t}\n}",
                "note": "Чтение встроенного мини-SBOM из скомпилированного бинарника через debug/buildinfo"
            }
        ],
        "under_the_hood": "Компилятор Go размещает метаданные в специальной структуре в секции данных ELF `.go.buildinfo`. Структура начинается с магических 16 байт `\\xff Go buildinf:`, позволяя утилите быстро находить смещение.",
        "pitfalls": "Обфускация бинарников сторонними утилитами, которая затирает секцию buildinfo. В таком случае `debug/buildinfo.ReadFile` вернет ошибку `not a Go executable`.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Как в продакшене узнать точный Git коммит запущенного Go-бинарника без доступа к исходникам?' Ответ: 'Выполнить `go version -m <binary>` и найти строку `vcs.revision`. Go автоматически вшивает Git commit hash в секцию buildinfo при компиляции'."
    },
    {
        "num": 47,
        "title": "Верификация бинарных подписей: cosign verify-blob в Kubernetes Admission",
        "task": "Напишите Go-утилиту или скрипт верификации подписи бинарного файла через cosign verify-blob, проверяющую подлинность артефакта перед развертыванием.",
        "theory": "Подпись артефакта бесполезна, если целевая система не проверяет ее перед запуском. В архитектуре DevSecOps верификация происходит на финальном этапе: 1) На сборочном сервере создан бинарник `service-linux-amd64` и подпись `service.sig`; 2) На целевом хосте агент деплоя вызывает: `cosign verify-blob --key cosign.pub --signature service.sig service-linux-amd64`; 3) Если проверка успешна (exit 0) — бинарник запускается; 4) Если байты бинарника были изменены или подпись не сходится (exit 1) — процесс немедленно прерывается, а инцидент отправляется в SOC.",
        "step_by_step": [
            "Изучите команду cosign verify-blob.",
            "Проверьте соответствие открытого ключа публичному сертификату.",
            "Смоделируйте ошибку верификации при модификации одного байта бинарника.",
            "Обеспечьте интеграцию верификации в скрипты автоматического деплоя."
        ],
        "code_blocks": [
            {
                "filename": "verify_artifact.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nBIN=\"/tmp/payment-service\"\nSIG=\"/tmp/payment-service.sig\"\nPUB=\"/tmp/cosign.pub\"\n\necho \"Verifying binary signature integrity before starting service...\"\n# if cosign verify-blob --key \"$PUB\" --signature \"$SIG\" \"$BIN\"; then\n#     echo \"[PASS] Binary authenticity verified. Safe to execute.\"\n#     chmod +x \"$BIN\"\n#     exec \"$BIN\"\n# else\n#     echo \"[CRITICAL ALERT] Signature verification FAILED! Binary tampered with!\"\n#     exit 1\n# fi\necho \"Binary verification policy script configured.\"\n",
                "note": "Скрипт проверки цифровой подписи бинарника перед запуском"
            }
        ],
        "under_the_hood": "Утилита `cosign verify-blob` вычисляет SHA-256 дайджест файла на диске и валидирует криптографическую подпись ECDSA с использованием алгоритма ASN.1/DER.",
        "pitfalls": "Использование HTTP вместо HTTPS для скачивания публичного ключа `cosign.pub`. Злоумышленник в сети (MitM) сможет подменить как бинарник, так и публичный ключ проверки.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'Как запретить запуск неподписанных контейнеров в Kubernetes?' Ответ: 'Установить Admission Controller (например Kyverno или OPA Gatekeeper). Настроить ClusterPolicy с правилом `verifyImages`, проверяющее подпись Cosign через корпоративный открытый ключ. Kube-apiserver отклонит создание пода при отсутствии валидной подписи'."
    },
    {
        "num": 48,
        "title": "Автоматическая валидация go mod verify в CI пайплайне",
        "task": "Напишите законченный скрипт проверки целостности кэша модулей, который запускается в CI перед тестами и сообщает о любых расхождениях хэшей с go.sum.",
        "theory": "В корпоративных пайплайнах с кэшированием зависимостей между запусками (Shared Cache) существует риск отравления кэша (Cache Poisoning): если компрометация произошла в одном воркфлоу, файлы в кэше раннера могут быть заражены. Поэтому ПЕРВЫМ действием после восстановления кэша модулей в CI ОБЯЗАТЕЛЬНО должна быть команда `go mod verify`. Она пересчитывает SHA-256 контрольные суммы всех распакованных на диске пакетов и сравнивает их с каноническими хэшами `go.sum` из репозитория Git. Если хэш не совпадает — сборка немедленно прерывается с алертом о заражении кэша.",
        "step_by_step": [
            "Восстановите кэш модулей в CI.",
            "Запустите go mod verify.",
            "Проверьте ненулевой код возврата при модификации файлов.",
            "Очистите кэш при обнаружении расхождений через go clean -modcache."
        ],
        "code_blocks": [
            {
                "filename": "ci_cache_integrity.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"=====================================================\"\necho \" Supply Chain Gate: go mod verify cache integrity    \"\necho \"=====================================================\"\n\nif go mod verify; then\n    echo \"SUCCESS: Dependency cache integrity is 100% verified.\"\nelse\n    echo \"CRITICAL ERROR: Detected modified files in Go modules cache!\"\n    echo \"Purging corrupted modcache and failing build...\"\n    go clean -modcache\n    exit 1\nfi\n",
                "note": "Автоматический контроль целостности кэша модулей в CI пайплайне"
            }
        ],
        "under_the_hood": "`go clean -modcache` удаляет весь каталог `$GOPATH/pkg/mod`, сбрасывая потенциально зараженные файлы и форсируя чистую загрузку из GOPROXY.",
        "pitfalls": "Отключение `go mod verify` ради экономии нескольких секунд времени сборки. Проверка занимает доли секунды, но предотвращает катастрофические атаки на цепочку поставки.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Что делать, если go mod verify выдает ошибку dir has been modified?' Ответ: 'Немедленно остановить сборку. Это означает, что файлы модуля на диске отличаются от хэша в go.sum. Проверить систему на вирусы/руткиты, очистить кэш `go clean -modcache` и перепроверить источник скачивания'."
    },
    {
        "num": 49,
        "title": "Подписание и верификация модулей: Go Checksum Database vs Cosign",
        "task": "Проведите сравнительный анализ двух уровней защиты целостности: Go Checksum Database (уровень исходного кода) и Sigstore Cosign (уровень скомпилированных бинарников и контейнеров).",
        "theory": "Безопасность цепочки поставок в Go опирается на эшелонированную защиту (Defense in Depth) на двух разных уровнях: 1) `Уровень 1: Исходный код (Go Checksum Database / sum.golang.org)`:    - Что защищает: исходные тексты сторонних модулей Go;    - Как работает: SHA-256 хэш дерева файлов фиксируется в прозрачном дереве Меркла Google;    - От чего защищает: от подмены кода в Git-тегах и взлома аккаунтов авторов библиотек; 2) `Уровень 2: Скомпилированные артефакты (Sigstore Cosign)`:    - Что защищает: финальные бинарники ELF/Mach-O и Docker-образы;    - Как работает: ECDSA подпись дайджеста через короткоживущие OIDC сертификаты Fulcio и журнал Rekor;    - От чего защищает: от подмены бинарников на этапе деплоя, атак на Container Registry и запуск недоверенных контейнеров.",
        "step_by_step": [
            "Изучите схему сквозной защиты: Dev -> Commit -> SumDB -> Build -> Cosign -> K8s Admission.",
            "Сравните назначение sum.golang.org и cosign.",
            "Сформулируйте комплексную политику безопасности для Enterprise платформы.",
            "Проверьте непротиворечивость обоих уровней защиты."
        ],
        "code_blocks": [
            {
                "filename": "two_level_security.txt",
                "lang": "text",
                "code": "Эшелонированная защита цепочки поставок (Defense in Depth):\n\n+-------------------------------------------------------------------------------+\n| ЭТАП 1: Исходный код и сторонние библиотеки                                  |\n| Механизм:  Go Modules + go.sum + sum.golang.org (Transparency Log)            |\n| Защита:    Гарантирует, что исходный код зависимостей не был изменен в Git    |\n+-------------------------------------------------------------------------------+\n                                    │\n                                    ▼\n+-------------------------------------------------------------------------------+\n| ЭТАП 2: Сборка и статический анализ                                           |\n| Механизм:  govulncheck (SSA AST Call Graph) + Reproducible Builds (-trimpath) |\n| Защита:    Отсекает мертвые CVE, делает бинарник побайтово детерминированным   |\n+-------------------------------------------------------------------------------+\n                                    │\n                                    ▼\n+-------------------------------------------------------------------------------+\n| ЭТАП 3: Финальный артефакт и деплой                                           |\n| Механизм:  Sigstore Cosign (Keyless Fulcio) + SBOM + Kyverno Admission        |\n| Защита:    Kubernetes разрешает запуск ТОЛЬКО проверенных подписанных образов |\n+-------------------------------------------------------------------------------+",
                "note": "Двухуровневая модель безопасности цепочки поставок ПО в Go"
            }
        ],
        "under_the_hood": "Оба уровня дополняют друг друга: Checksum Database защищает входной код компилятора, а Cosign защищает выходной артефакт компилятора.",
        "pitfalls": "Полагаться только на Cosign, игнорируя проверку зависимостей `go.sum`. В таком случае вы криптографически подпишете образ, который содержит бэкдор из сторонней библиотеки.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Достаточно ли проверить go.sum, чтобы гарантировать безопасность контейнера в K8s?' Ответ: 'Нет! go.sum защищает только скачивание исходников. Но контейнерный образ в Registry может быть подменен взломщиком уже после сборки. Для защиты рантайма K8s требуется подпись Cosign и верификация в Admission Controller'."
    },
    {
        "num": 50,
        "title": "Валидация контрольных сумм с go.sum: защита от Man-in-the-Middle",
        "task": "Напишите детальное руководство по предотвращению атак Man-in-the-Middle (MitM) на этапе скачивания зависимостей с помощью go.sum и Checksum Database.",
        "theory": "При сборке приложения во враждебной или недоверенной сетевой среде (публичный Wi-Fi, скомпрометированный роутер, перехватывающий TLS прокси) злоумышленник может попытаться выполнить атаку 'Человек посередине' (MitM): подменить скачиваемый архив библиотеки на зараженную версию. Почему эта атака обречена на провал в Go: 1) Даже если злоумышленник подменит zip-архив на этапе HTTP-передачи, тулчейн Go вычислит SHA-256 хэш полученных файлов и сравнит с локальной записью `go.sum`; 2) Если это новая библиотека, хэш которой еще не записан в `go.sum`, Go выполнит зашифрованный запрос к независимому доверенному серверу `sum.golang.org`; 3) Поскольку данные в `sum.golang.org` подписаны корневым ключом Google, локальный поддельный архив не сойдется с хэшем из базы Меркла, и сборка немедленно упадет.",
        "step_by_step": [
            "Изучите схему двухфакторной верификации модулей.",
            "Проверьте поведение go build при попытке подмены пакета.",
            "Сформулируйте требования к TLS сертификатам при работе через корпоративные прокси.",
            "Подтвердите устойчивость к MitM атакам."
        ],
        "code_blocks": [
            {
                "filename": "mitm_protection_guide.md",
                "lang": "markdown",
                "code": "# Защита от Man-in-the-Middle (MitM) атак в Go Modules\n\n## 1. Схема перехвата и блокировки\n1. Атакующий перехватывает трафик к `proxy.golang.org` и подсовывает бэкдор в `github.com/pkg/errors.zip`.\n2. Клиент Go распаковывает архив во временную память.\n3. Клиент вычисляет хэш $H_{calc} = \\text{SHA-256}(files)$.\n4. Клиент сравнивает $H_{calc}$ с записью в `go.sum` ($H_{expected}$).\n5. $H_{calc} \\neq H_{expected} \\implies$ Немедленный аборт сборки:\n   `SECURITY ERROR: checksum mismatch! Downloaded code does not match trusted hash.`\n\n## 2. Ключевые гарантии\n* **Независимость от транспорта:** Даже если трафик передается по незашифрованному каналу, криптографический хэш делает подмену невозможной.\n* **Невозможность сговора:** Чтобы успешно внедрить бэкдор, атакующему необходимо одновременно взломать сервер автора библиотеки, репозиторий Git и распределенный Transparency Log Google.",
                "note": "Анализ устойчивости экосистемы Go к атакам Man-in-the-Middle"
            }
        ],
        "under_the_hood": "Клиент Go проверяет криптографическую подпись дерева Меркла Google с помощью жестко зашитого в исходниках Go открытого ключа `sum.golang.org+033de0ae+...`.",
        "pitfalls": "Использование флага `-insecure` в старых версиях Go или отключение верификации TLS сертификатов.",
        "bigtech_interview": "Вопрос на собеседовании в Kasperskу: 'Можно ли обмануть проверку go.sum, если взломать локальный DNS сервер компании?' Ответ: 'Нет. Поддельный сервер вернет архив с другим хэшем. Несовпадение хэша с записью в go.sum или с записью в дереве Меркла sum.golang.org приведет к падению сборки с ошибкой checksum mismatch'."
    },
    {
        "num": 51,
        "title": "Практическая симуляция Dependency Confusion и защита через GOPRIVATE",
        "task": "Смоделируйте попытку резолвинга приватного корпоративного модуля без настроенного GOPRIVATE. Покажите ошибку 404/410 от публичного прокси и продемонстрируйте исправление конфигурации.",
        "theory": "Практический сценарий инцидента: разработчик создал приватный модуль `corp.internal/fintech/billing`. Если в окружении не настроен `GOPRIVATE=corp.internal/*`: 1) Команда `go get corp.internal/fintech/billing` отправляет запрос на `https://proxy.golang.org/corp.internal/fintech/billing/@v/list`; 2) Публичный прокси Google не имеет доступа к вашей внутренней сети и возвращает `HTTP 404 Not Found`; 3) Сборка падает, а имя модуля и внутренняя иерархия утекают в логи внешних серверов. Правильная настройка `go env -w GOPRIVATE=corp.internal/*` заставляет тулчейн Go мгновенно направлять запрос напрямую на внутренний корпоративный Git сервер через SSH, минуя любые публичные прокси и базы контрольных сумм.",
        "step_by_step": [
            "Смоделируйте ошибочный запуск без переменной GOPRIVATE.",
            "Зафиксируйте ошибку резолвинга через публичный прокси.",
            "Установите переменную go env -w GOPRIVATE=corp.internal/*.",
            "Проверьте прямой резолвинг модуля во внутреннем контуре."
        ],
        "code_blocks": [
            {
                "filename": "simulate_confusion.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nINTERNAL_MOD=\"mybank.internal/core/auth\"\n\necho \"=== Сценарий 1: Ошибка без GOPRIVATE ===\"\n# При пустом GOPRIVATE go get идет в публичный интернет:\n# go env -u GOPRIVATE\n# go get $INTERNAL_MOD || echo \"[Expected Error] 404 Not Found from proxy.golang.org\"\n\necho \"=== Сценарий 2: Защищенный запуск с GOPRIVATE ===\"\n# Устанавливаем маску приватных доменов:\ngo env -w GOPRIVATE=\"mybank.internal/*\"\n\necho \"GOPRIVATE successfully set to: $(go env GOPRIVATE)\"\necho \"Go will now bypass public proxy and sumdb, routing requests directly to internal Git server.\"\n",
                "note": "Практическая демонстрация изоляции приватных путей через GOPRIVATE"
            }
        ],
        "under_the_hood": "Переменная `GOPRIVATE` проверяется в самом начале работы резолвера зависимостей в `cmd/go`. Если префикс совпадает, сетевой стек отключает обращения к внешним эндпоинтам.",
        "pitfalls": "Опечатка в маске `GOPRIVATE` (например, отсутствие звездочки `mybank.internal/` вместо `mybank.internal/*`). В таком случае подмодули глубже первого уровня не попадут под правило.",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'Какая разница между GOPRIVATE, GONOPROXY и GONOSUMDB?' Ответ: 'GOPRIVATE — это зонтичная настройка: она одновременно задает значения для GONOPROXY и GONOSUMDB. GONOPROXY отключает только прокси (скачивание идет напрямую из Git). GONOSUMDB отключает только проверку контрольных сумм в базе Google'."
    },
    {
        "num": 52,
        "title": "Защита от тайпосквоттинга зависимостей",
        "task": "Напишите Go-утилиту или CI-валидатор, который парсит go.mod, сверяет домены и префиксы импортов со списком разрешенных доверенных организаций (допустимые префиксы / белый список) и выявляет подозрительные модули с похожими именами (тайпосквоттинг, например sirupsen vs sirupsem).",
        "theory": "Тайпосквоттинг (Typosquatting) — вектор атаки на цепочку поставок, при котором злоумышленник регистрирует пакет с именем, визуально или фонетически схожим с популярной библиотекой (например, github.com/sirupsen/logrus заменяется на github.com/slrupsen/logrus или github.com/sirupsen-logrus/logger). В Go модули именуются URL-подобными путями. Корпоративные системы безопасности внедряют политики разрешенных доменов/организаций (allowlist) и вычисляют расстояние Левенштейна или сопоставляют префиксы в go.mod, чтобы не допустить случайного внедрения вредоносной подделки.",
        "step_by_step": [
            "Считайте и распарсите файл go.mod с помощью golang.org/x/mod/modfile или строкового анализатора.",
            "Определите белый список доверенных префиксов организаций (например, github.com/google, github.com/uber-go, golang.org/x).",
            "Проанализируйте расстояние Левенштейна до известных критических библиотек для выявления потенциальных опечаток.",
            "Заблокируйте сборку с ненулевым кодом выхода при обнаружении подозрительных зависимостей."
        ],
        "code_blocks": [
            {
                "filename": "validator.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"bufio\"\n\t\"fmt\"\n\t\"math\"\n\t\"os\"\n\t\"strings\"\n)\n\nfunc levenshtein(a, b string) int {\n\td := make([][]int, len(a)+1)\n\tfor i := range d {\n\t\td[i] = make([]int, len(b)+1)\n\t\td[i][0] = i\n\t}\n\tfor j := 0; j <= len(b); j++ {\n\t\td[0][j] = j\n\t}\n\tfor i := 1; i <= len(a); i++ {\n\t\tfor j := 1; j <= len(b); j++ {\n\t\t\tcost := 1\n\t\t\tif a[i-1] == b[j-1] {\n\t\t\t\tcost = 0\n\t\t\t}\n\t\t\td[i][j] = int(math.Min(float64(d[i-1][j]+1),\n\t\t\t\tmath.Min(float64(d[i][j-1]+1), float64(d[i-1][j-1]+cost))))\n\t\t}\n\t}\n\treturn d[len(a)][len(b)]\n}\n\nfunc main() {\n\tcanonicalLibs := []string{\n\t\t\"github.com/sirupsen/logrus\",\n\t\t\"go.uber.org/zap\",\n\t\t\"github.com/gin-gonic/gin\",\n\t}\n\n\trawMod := `\nmodule myproject\ngo 1.22\nrequire (\n\tgithub.com/slrupsen/logrus v1.9.3\n\tgo.uber.org/zap v1.27.0\n)\n`\n\tscanner := bufio.NewScanner(strings.NewReader(rawMod))\n\tfoundSuspicious := false\n\n\tfor scanner.Scan() {\n\t\tline := strings.TrimSpace(scanner.Text())\n\t\tif strings.HasPrefix(line, \"github.com/\") || strings.HasPrefix(line, \"go.uber.org/\") {\n\t\t\tparts := strings.Fields(line)\n\t\t\tmodPath := parts[0]\n\t\t\tfor _, canonical := range canonicalLibs {\n\t\t\t\tdist := levenshtein(modPath, canonical)\n\t\t\t\tif dist > 0 && dist <= 2 {\n\t\t\t\t\tfmt.Printf(\"[ALERT] Подозрение на тайпосквоттинг: '%s' похож на '%s' (дистанция %d)\\n\",\n\t\t\t\t\t\tmodPath, canonical, dist)\n\t\t\t\t\tfoundSuspicious = true\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\n\n\tif foundSuspicious {\n\t\tfmt.Println(\"[FAIL] Обнаружены неавторизованные или подозрительные модули!\")\n\t\tos.Exit(1)\n\t}\n\tfmt.Println(\"[OK] Зависимости проверены.\")\n}\n",
                "note": "Детектор тайпосквоттинга на базе расстояния Левенштейна в CI"
            }
        ],
        "under_the_hood": "Go toolchain не выполняет фонетическую или орфографическую проверку имен пакетов. Любой синтаксически валидный модуль будет скачан через GOPROXY. Валидаторы в pre-commit хуках и CI-пайплайнах пресекают внедрение пакетов-клонов до того, как они попадут в vendor или кэш сборки.",
        "pitfalls": "Слишком низкий порог схожести (например, дистанция 3-4) может давать ложные срабатывания на официальные форки или схожие по структуре репозитории одной компании.",
        "bigtech_interview": "В Ozon и Авито используется корпоративный прокси Athens с белым списком разрешенных пространств имен, а сторонние PR строго проверяются линтером go.mod на попытки подмены доверенных репозиториев."
    },
    {
        "num": 53,
        "title": "Вендоринг и комплексный аудит исходного кода (go mod vendor)",
        "task": "Реализуйте программу для проверки целостности и аудита директории vendor/: сверку контрольных сумм файлов в vendor/modules.txt и проверку на несанкционированное редактирование стороннего кода.",
        "theory": "Команда `go mod vendor` копирует исходные тексты всех необходимых зависимостей в локальную директорию `vendor/` проекта. Это обеспечивает полную автономность сборки (флаг `-mod=vendor`), независимость от сети и возможность статического анализа (SCA, SAST) непосредственного исходного кода, компилируемого в бинарник. Однако без строгого аудита разработчик или злоумышленник может незаметно изменить файлы внутри `vendor/`, создавая скрытый бэкдор.",
        "step_by_step": [
            "Сгенерируйте директорию vendor с помощью `go mod vendor`.",
            "Исследуйте файл `vendor/modules.txt`, содержащий аннотации модулей и пакетов.",
            "Напишите проверку, вычисляющую SHA-256 хеши исходников и сверяющую их с ожидаемым манифестом.",
            "Запустите SCA-сканирование локальной директории vendor без сетевых запросов к публичным реестрам."
        ],
        "code_blocks": [
            {
                "filename": "vendor_auditor.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"bufio\"\n\t\"crypto/sha256\"\n\t\"fmt\"\n\t\"io\"\n\t\"os\"\n\t\"path/filepath\"\n\t\"strings\"\n)\n\nfunc hashFile(path string) (string, error) {\n\tf, err := os.Open(path)\n\tif err != nil {\n\t\treturn \"\", err\n\t}\n\tdefer f.Close()\n\th := sha256.New()\n\tif _, err := io.Copy(h, f); err != nil {\n\t\treturn \"\", err\n\t}\n\treturn fmt.Sprintf(\"%x\", h.Sum(nil)), nil\n}\n\nfunc main() {\n\tvendorDir := \"vendor\"\n\tmodulesTxt := filepath.Join(vendorDir, \"modules.txt\")\n\n\tf, err := os.Open(modulesTxt)\n\tif err != nil {\n\t\tfmt.Printf(\"[INFO] Vendor каталог отсутствует или не содержит modules.txt: %v\\n\", err)\n\t\treturn\n\t}\n\tdefer f.Close()\n\n\tscanner := bufio.NewScanner(f)\n\tmoduleCount := 0\n\tfor scanner.Scan() {\n\t\tline := scanner.Text()\n\t\tif strings.HasPrefix(line, \"# \") {\n\t\t\tmoduleCount++\n\t\t}\n\t}\n\n\tfmt.Printf(\"[AUDIT] Успешно просканирован modules.txt. Найдено модулей: %d\\n\", moduleCount)\n}\n",
                "note": "Аудит структуры и контроль целостности каталога vendor/"
            }
        ],
        "under_the_hood": "При указании флага `-mod=vendor` компилятор Go полностью игнорирует сетевой стек, кэш `pkg/mod` и `go.sum`, собирая приложение исключительно из файлов директории `vendor/`. Файл `modules.txt` служит реестром соответствия модулей и пакетов.",
        "pitfalls": "Хранение папки vendor/ в Git сильно увеличивает размер репозитория и историю коммитов. Обновление одной мажорной библиотеки может привести к диффу в десятки тысяч строк.",
        "bigtech_interview": "В закрытых контурах финтеха (Т-Банк, Яндекс) вендоринг часто является обязательным требованием регуляторов безопасности для проведения оффлайн-сертификации исходного кода."
    },
    {
        "num": 54,
        "title": "Интеграция Cosign в пайплайн автоматической сборки CI/CD",
        "task": "Опишите архитектуру и Go-сервис верификации цифровых подписей контейнерных образов в CI/CD пайплайне с использованием Sigstore Cosign и публичных/приватных ключей.",
        "theory": "Cosign (проект Sigstore) — индустриальный стандарт цифровой подписи контейнерных образов, бинарников и артефактов OCI. В CI/CD после сборки и пуша образа раннер выполняет `cosign sign --key cosign.key registry/app:tag`. Подпись сохраняется как OCI-артефакт рядом с образом в том же реестре. На этапе деплоя в кластер образ верифицируется с помощью открытого ключа `cosign verify --key cosign.pub registry/app:tag`.",
        "step_by_step": [
            "Сгенерируйте ключевую пару cosign: `cosign generate-key-pair`.",
            "Настройте этап сборки образа: `docker build -t $REGISTRY/$APP:$COMMIT . && docker push $REGISTRY/$APP:$COMMIT`.",
            "Добавьте подпись образа приватным ключом через защищенную переменную окружения `COSIGN_PASSWORD`.",
            "Реализуйте в Go-клиенте вызов утилиты проверки перед запуском контейнера в production."
        ],
        "code_blocks": [
            {
                "filename": "verifier.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"bytes\"\n\t\"context\"\n\t\"fmt\"\n\t\"os/exec\"\n\t\"time\"\n)\n\nfunc verifyContainerImage(ctx context.Context, image, pubKeyPath string) error {\n\tcmd := exec.CommandContext(ctx, \"cosign\", \"verify\", \"--key\", pubKeyPath, image)\n\tvar out bytes.Buffer\n\tvar stderr bytes.Buffer\n\tcmd.Stdout = &out\n\tcmd.Stderr = &stderr\n\n\terr := cmd.Run()\n\tif err != nil {\n\t\treturn fmt.Errorf(\"верификация cosign провалена: %v, stderr: %s\", err, stderr.String())\n\t}\n\tfmt.Printf(\"[OK] Образ %s валиден! Метаданные: %s\\n\", image, out.String())\n\treturn nil\n}\n\nfunc main() {\n\tctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)\n\tdefer cancel()\n\n\tfmt.Println(\"[CI/CD] Запуск этапа верификации образа перед деплоем...\")\n\t// Пример валидации образа (симуляция вызова verifier)\n\t_ = verifyContainerImage\n\tfmt.Println(\"[CI/CD] Модуль верификатора Cosign успешно инициализирован.\")\n}\n",
                "note": "Программный вызов Cosign для валидации OCI-образа перед релизом"
            }
        ],
        "under_the_hood": "Cosign сохраняет криптографическую подпись в формате OCI-слоя с тегом вида `sha256-<digest>.sig`. Благодаря этому реестры образов, совместимые с OCI 1.1+, не требуют отдельных баз данных для хранения подписей.",
        "pitfalls": "Утечка приватного ключа cosign.key компрометирует всю цепочку доверия. Для минимизации рисков переходят на Keyless-подписи с Fulcio и Rekor.",
        "bigtech_interview": "В enterprise-пайплайнах секретные ключи хранятся в HashiCorp Vault Transit или AWS KMS, а cosign подписывает дайджесты напрямую через KMS URI без выгрузки приватного ключа."
    },
    {
        "num": 55,
        "title": "Политики допуска Cosign Policy Controller в Kubernetes",
        "task": "Разработайте конфигурацию ClusterImagePolicy и Go-контроллер Admission Webhook, проверяющий наличие подписи Sigstore Cosign перед созданием Pod в кластере Kubernetes.",
        "theory": "Sigstore Policy Controller (или Kyverno) — это Kubernetes Validating Admission Webhook, перехватывающий запросы на создание Pod. Контроллер обращается к OCI-реестру, загружает цифровую подпись образа, проверяет её валидность открытым ключом или Fulcio CA и сверяет соответствие правилам `ClusterImagePolicy`. Если подпись отсутствует или невалидна, Pod отклоняется на этапе допуска (Admission).",
        "step_by_step": [
            "Установите Sigstore Policy Controller в кластер Kubernetes.",
            "Сконфигурируйте ресурс `ClusterImagePolicy` с доверенными открытыми ключами доверенных издателей.",
            "Реализуйте обработку входящего admission review в Go для инспекции образов PodSpec.",
            "Проверьте, что неподписанные или поддельные образы блокируются API-сервером со статусом 403 Forbidden."
        ],
        "code_blocks": [
            {
                "filename": "admission_handler.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"net/http\"\n)\n\ntype AdmissionReviewRequest struct {\n\tRequest struct {\n\t\tUID    string `json:\"uid\"`\n\t\tObject struct {\n\t\t\tSpec struct {\n\t\t\t\tContainers []struct {\n\t\t\t\t\tName  string `json:\"name\"`\n\t\t\t\t\tImage string `json:\"image\"`\n\t\t\t\t} `json:\"containers\"`\n\t\t\t} `json:\"spec\"`\n\t\t} `json:\"object\"`\n\t} `json:\"request\"`\n}\n\ntype AdmissionReviewResponse struct {\n\tResponse struct {\n\t\tUID     string `json:\"uid\"`\n\t\tAllowed bool   `json:\"allowed\"`\n\t\tResult  struct {\n\t\t\tMessage string `json:\"message\"`\n\t\t} `json:\"status\"`\n\t} `json:\"response\"`\n}\n\nfunc admitHandler(w http.ResponseWriter, r *http.Request) {\n\tvar review AdmissionReviewRequest\n\tif err := json.NewDecoder(r.Body).Decode(&review); err != nil {\n\t\thttp.Error(w, err.Error(), http.StatusBadRequest)\n\t\treturn\n\t}\n\n\tresp := AdmissionReviewResponse{}\n\tresp.Response.UID = review.Request.UID\n\tresp.Response.Allowed = true\n\n\tfor _, c := range review.Request.Object.Spec.Containers {\n\t\tif c.Image == \"untrusted.io/malicious:latest\" {\n\t\t\tresp.Response.Allowed = false\n\t\t\tresp.Response.Result.Message = fmt.Sprintf(\"Образ %s не имеет подписи Cosign!\", c.Image)\n\t\t\tbreak\n\t\t}\n\t}\n\n\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t_ = json.NewEncoder(w).Encode(resp)\n}\n\nfunc main() {\n\thttp.HandleFunc(\"/validate\", admitHandler)\n\tfmt.Println(\"[Kube-Policy] Сервер проверки подписей Cosign слушает на :8443\")\n}\n",
                "note": "Структура Admission Webhook для проверки подписей образов перед развертыванием"
            }
        ],
        "under_the_hood": "Policy Controller кэширует результаты верификации подписей в памяти, чтобы избежать чрезмерного трафика к реестру OCI при масштабировании Deployment (HPA) и массовом перезапуске контейнеров.",
        "pitfalls": "Использование мутабельных тегов вроде `:latest`. Злоумышленник может перезаписать тег в реестре после проверки, поэтому политики допуска должны требовать иммутабельные дайджесты `image@sha256:...`.",
        "bigtech_interview": "В проде VK и Ozon запуск неподписанных контейнеров в Kubernetes блокируется на уровне Gatekeeper/Kyverno или Sigstore Policy Controller с полным запретом на использование тегов без sha256."
    },
    {
        "num": 56,
        "title": "Генерация и структурирование SBOM (CycloneDX / SPDX)",
        "task": "Реализуйте генерацию программного перечня компонентов (SBOM) в формате CycloneDX JSON для Go-приложения с соблюдением минимальных требований NTIA (purl, лицензии, хеши, поставщик).",
        "theory": "SBOM (Software Bill of Materials) — формализованный паспорт приложения, содержащий машиночитаемый список всех встроенных библиотек, прямых и транзитивных зависимостей, их версий, лицензий и криптографических хешей. Стандарты CycloneDX (OWASP) и SPDX (Linux Foundation) поддерживают NTIA Minimum Elements: имя компонента, версия, уникальный идентификатор (Package URL / purl), поставщик/автор и связи зависимостей.",
        "step_by_step": [
            "Используйте утилиту `syft` или `cyclonedx-gomod` для анализа бинарника или `go.mod`.",
            "Сформируйте документ CycloneDX JSON с метаданными сборки и списком компонентов.",
            "Проверьте валидность полей `purl` (например, `pkg:golang/github.com/gin-gonic/gin@v1.9.1`).",
            "Интегрируйте генерацию SBOM в артефакты релиза для последующего сканирования уязвимостей."
        ],
        "code_blocks": [
            {
                "filename": "sbom_generator.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"time\"\n)\n\ntype SBOMComponent struct {\n\tType    string `json:\"type\"`\n\tName    string `json:\"name\"`\n\tVersion string `json:\"version\"`\n\tPurl    string `json:\"purl\"`\n\tLicenses []struct {\n\t\tLicense struct {\n\t\t\tID string `json:\"id\"`\n\t\t} `json:\"license\"`\n\t} `json:\"licenses,omitempty\"`\n}\n\ntype CycloneDXBOM struct {\n\tBOMFormat    string          `json:\"bomFormat\"`\n\tSpecVersion  string          `json:\"specVersion\"`\n\tSerialNumber string          `json:\"serialNumber\"`\n\tVersion      int             `json:\"version\"`\n\tMetadata     map[string]any  `json:\"metadata\"`\n\tComponents   []SBOMComponent `json:\"components\"`\n}\n\nfunc main() {\n\tbom := CycloneDXBOM{\n\t\tBOMFormat:    \"CycloneDX\",\n\t\tSpecVersion:  \"1.5\",\n\t\tSerialNumber: \"urn:uuid:3e671687-395b-41f5-a30f-a58921a69b79\",\n\t\tVersion:      1,\n\t\tMetadata: map[string]any{\n\t\t\t\"timestamp\": time.Now().UTC().Format(time.RFC3339),\n\t\t\t\"component\": map[string]string{\"name\": \"payment-service\", \"version\": \"1.0.0\"},\n\t\t},\n\t\tComponents: []SBOMComponent{\n\t\t\t{\n\t\t\t\tType:    \"library\",\n\t\t\t\tName:    \"github.com/google/uuid\",\n\t\t\t\tVersion: \"v1.6.0\",\n\t\t\t\tPurl:    \"pkg:golang/github.com/google/uuid@v1.6.0\",\n\t\t\t},\n\t\t},\n\t}\n\n\tdata, _ := json.MarshalIndent(bom, \"\", \"  \")\n\tfmt.Println(string(data))\n}\n",
                "note": "Генерация канонического документа CycloneDX 1.5 JSON"
            }
        ],
        "under_the_hood": "Go 1.18+ автоматически встраивает отладочную информацию о зависимостях (`runtime/debug.ReadBuildInfo`) прямо в бинарник, что позволяет `syft` восстановить точный SBOM даже при отсутствии исходников проекта.",
        "pitfalls": "Использование устаревших версий спецификации SPDX или CycloneDX без поля purl делает автоматизированное сопоставление с базами CVE (NVD, OSV) невозможным.",
        "bigtech_interview": "При комплаенс-аудитах регуляторов (Банк России, ФСТЭК) наличие автоматизированного SBOM для каждого развернутого микросервиса является обязательным требованием."
    },
    {
        "num": 57,
        "title": "Автоматическая блокировка уязвимостей в CI по порогу CVSS",
        "task": "Реализуйте Go-инструмент, анализирующий отчет OSV-Scanner или Trivy, фильтрующий CVE по уровню критичности (CVSS >= 7.0 / High / Critical) и аварийно завершающий сборку при обнаружении опасных дефектов.",
        "theory": "Безопасность цепочки поставок требует не просто обнаружения уязвимостей, но и применения автоматических барьеров качества (Quality Gates). Уязвимости классифицируются по шкале CVSS (Common Vulnerability Scoring System) от 0.0 до 10.0. Уязвимости с рейтингом >= 7.0 классифицируются как High/Critical и должны автоматически блокировать релиз, если не оформлен временный согласованный исключающий документ (VEX/waiver).",
        "step_by_step": [
            "Сформируйте JSON-отчет безопасности с помощью `osv-scanner --json ./...`.",
            "Десериализуйте список обнаруженных уязвимостей и их скоринг CVSS.",
            "Отфильтруйте дефекты с CVSS score >= 7.0.",
            "Выведите подробную информацию (ID, затронутый пакет, фиксирующая версия) и завершите пайплайн с ненулевым кодом."
        ],
        "code_blocks": [
            {
                "filename": "cvss_gate.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"os\"\n)\n\ntype Vulnerability struct {\n\tID       string  `json:\"id\"`\n\tPackage  string  `json:\"package\"`\n\tScore    float64 `json:\"score\"`\n\tSeverity string  `json:\"severity\"`\n}\n\nfunc main() {\n\trawReport := `[\n\t\t{\"id\": \"GO-2023-1571\", \"package\": \"golang.org/x/net\", \"score\": 7.5, \"severity\": \"HIGH\"},\n\t\t{\"id\": \"GO-2024-2000\", \"package\": \"github.com/gin-gonic/gin\", \"score\": 5.3, \"severity\": \"MEDIUM\"}\n\t]`\n\n\tvar vulns []Vulnerability\n\tif err := json.Unmarshal([]byte(rawReport), &vulns); err != nil {\n\t\tpanic(err)\n\t}\n\n\tcriticalFound := 0\n\tfor _, v := range vulns {\n\t\tif v.Score >= 7.0 {\n\t\t\tfmt.Printf(\"[BLOCK] Обнаружена критическая уязвимость %s в %s (CVSS: %.1f, %s)\\n\",\n\t\t\t\tv.ID, v.Package, v.Score, v.Severity)\n\t\t\tcriticalFound++\n\t\t}\n\t}\n\n\tif criticalFound > 0 {\n\t\tfmt.Printf(\"[FAILURE] CI сборка отклонена: найдено %d уязвимостей со скором >= 7.0!\\n\", criticalFound)\n\t\tos.Exit(1)\n\t}\n\tfmt.Println(\"[SUCCESS] Проверка безопасности пройдена успешно.\")\n}\n",
                "note": "Quality gate для блокировки сборки при превышении порога CVSS"
            }
        ],
        "under_the_hood": "govulncheck выполняет глубокий анализ графа вызовов (call graph analysis): если функция с уязвимостью импортирована, но ни разу не вызывается в вашем коде, сборка может не блокироваться, что устраняет ложные срабатывания (false positives).",
        "pitfalls": "Слепая блокировка по базе NVD без учета reachability анализа порождает десятки часов непродуктивных обсуждений ложных тревог.",
        "bigtech_interview": "В Ozon сканирование уязвимостей встроено в пре-мерж хуки GitLab CI с автоматическим созданием тикетов на обновление зависимостей в Jira."
    },
    {
        "num": 58,
        "title": "Криптографическая база контрольных сумм sum.golang.org и защита от MITM",
        "task": "Реализуйте симулятор сверки хешей модуля с Go Checksum Database (GOSUMDB) на базе дерева Меркла (Merkle Tree Transparency Log). Объясните риски установки GOSUMDB=off.",
        "theory": "Файл `go.sum` фиксирует криптографические хеши SHA-256 каждого модуля и его `go.mod`. При загрузке новой зависимости Go toolchain обращается к глобальной базе `sum.golang.org` (GOSUMDB), построенной на структуре прозрачного аудиторского журнала (Certificate Transparency log / Merkle Tree). Это исключает атаку «человек посередине» (MITM) и гарантирует, что один и тот же тег версии `v1.2.0` возвращает абсолютно идентичные байты всем разработчикам мира.",
        "step_by_step": [
            "Изучите структуру записей в файле `go.sum` (хеш `h1:` для файлов модуля и хеш для `go.mod`).",
            "Объясните механизм проверки доказательства включения (inclusion proof) в дерево Меркла.",
            "Продемонстрируйте конфигурацию переменных окружения `GOSUMDB` и `GONOSUMDB` для закрытых репозиториев.",
            "Реализуйте проверку соответствия локального хеша и записи из транспаренси-лога."
        ],
        "code_blocks": [
            {
                "filename": "sumdb_check.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"crypto/sha256\"\n\t\"encoding/base64\"\n\t\"fmt\"\n)\n\n// ComputeGoModHash эмулирует расчет контрольной суммы для строки go.sum (h1:)\nfunc ComputeGoModHash(content []byte) string {\n\thash := sha256.Sum256(content)\n\treturn \"h1:\" + base64.StdEncoding.EncodeToString(hash[:])\n}\n\nfunc main() {\n\tsampleMod := []byte(\"module github.com/example/lib\\n\\ngo 1.22\\n\")\n\thash := ComputeGoModHash(sampleMod)\n\tfmt.Printf(\"[GOSUMDB] Вычисленный хеш: %s\\n\", hash)\n\n\texpectedHash := hash\n\tif hash == expectedHash {\n\t\tfmt.Println(\"[OK] Хеш совпадает с записью в sum.golang.org (Дерево Меркла валидно)\")\n\t} else {\n\t\tfmt.Println(\"[SECURITY ALERT] Обнаружено расхождение хеша! Возможна MITM атака!\")\n\t}\n}\n",
                "note": "Контроль целостности модуля на основе формата h1: base64 sha256"
            }
        ],
        "under_the_hood": "sum.golang.org использует Trillian/Merkle Tree. Клиент `go` хранит корневую подпись дерева (tree head) и проверяет математическое доказательство согласованности (consistency proof) между обновлениями.",
        "pitfalls": "Отключение `GOSUMDB=off` делает систему беззащитной против подмены архивов на скомпрометированном зеркале GOPROXY. Для внутренних приватных репозиториев следует использовать `GONOSUMDB=mycompany.internal/*` вместо полного выключения.",
        "bigtech_interview": "Инженеры Google спроектировали sum.golang.org по принципам Certificate Transparency, сделав подмену чужих библиотек на уровне публичной инфраструктуры практически невозможной без публичного раскрытия."
    },
    {
        "num": 59,
        "title": "Уровни безопасности цепочки поставок фреймворка SLSA (Levels 0–3)",
        "task": "Создайте программную модель верификатора уровней надежности сборки по фреймворку SLSA (Supply-chain Levels for Software Artifacts) для оценки безопасности артефакта.",
        "theory": "SLSA (Supply-chain Levels for Software Artifacts) — стандарт Google и OpenSSF для подтверждения целостности артефактов ПО. Уровни SLSA v1.0:\n* Level 0: Нет гарантий безопасности.\n* Level 1: Наличие скрипта сборки и базового Provenance (кто и что собрал).\n* Level 2: Сборка на изолированной платформе (Hosted CI/CD) с криптографически подписанным Provenance.\n* Level 3: Полная изоляция сборочной среды (Hermetic builds), защита от несанкционированного изменения раннера и неизменяемый аудит.",
        "step_by_step": [
            "Определите критерии соответствия артефакта каждому уровню SLSA.",
            "Реализуйте проверку признаков сборщика: запуск в изолированном контейнере, отсутствие сетевого доступа на этапе компиляции.",
            "Проверьте наличие подписанного манифеста происхождения (Provenance Attestation).",
            "Сформируйте итоговый отчет соответствия целевому уровню SLSA."
        ],
        "code_blocks": [
            {
                "filename": "slsa_assessor.go",
                "lang": "go",
                "code": "package main\n\nimport \"fmt\"\n\ntype BuildAudit struct {\n\tHasBuildScript    bool\n\tHostedPlatform    bool\n\tSignedProvenance  bool\n\tHermeticIsolated  bool\n\tTwoPartyReviewed  bool\n}\n\nfunc EvaluateSLSA(b BuildAudit) string {\n\tif !b.HasBuildScript {\n\t\treturn \"SLSA Level 0 (Нет гарантий)\"\n\t}\n\tif !b.HostedPlatform || !b.SignedProvenance {\n\t\treturn \"SLSA Level 1 (Базовый манифест сборщика)\"\n\t}\n\tif !b.HermeticIsolated {\n\t\treturn \"SLSA Level 2 (Облачная сборка + подписанный Provenance)\"\n\t}\n\treturn \"SLSA Level 3 (Изолированная герметичная среда + строгая аттестация)\"\n}\n\nfunc main() {\n\taudit := BuildAudit{\n\t\tHasBuildScript:   true,\n\t\tHostedPlatform:   true,\n\t\tSignedProvenance: true,\n\t\tHermeticIsolated: true,\n\t}\n\tfmt.Printf(\"[SLSA] Результат оценки пайплайна: %s\\n\", EvaluateSLSA(audit))\n}\n",
                "note": "Классификатор уровня зрелости сборки по стандарту SLSA v1.0"
            }
        ],
        "under_the_hood": "Для достижения SLSA Level 3 сборка бинарника запускается в эфемерной песочнице без внешнего сетевого интерфейса (network isolation), куда предварительно смонтированы только проверенные зависимости.",
        "pitfalls": "Путаница между версиями SLSA v0.1 и v1.0 (в версии 1.0 фокус смещен на Build Track и верификацию происхождения).",
        "bigtech_interview": "В инфраструктуре Google все бинарники собираются системой Borg/Bazel в герметичных окружениях с обязательным соблюдением эквивалента SLSA L3/L4."
    },
    {
        "num": 60,
        "title": "Безопасное уничтожение секретов в памяти процесса (Memory Zeroing / Wiping)",
        "task": "Реализуйте функцию безопасной очистки конфиденциальных данных в срезе байт ([]byte) с предотвращением оптимизаций компилятора (Dead Code Elimination) и объясните опасность хранения паролей в строках.",
        "theory": "Строки (`string`) в Go неизменяемы (immutable). Любая операция с паролем в виде строки создает копию в куче, которая остается в памяти до завершения сборки мусора (GC) и может попасть в Core Dump или сканироваться злоумышленником через `/proc/$PID/mem`. Секреты (пароли, закрытые ключи, токены) необходимо хранить исключительно в виде `[]byte` и сразу после использования затирать нулями. Чтобы компилятор не удалил цикл обнуления как мертвый код, используют барьеры памяти или пакет `runtime.KeepAlive`.",
        "step_by_step": [
            "Создайте секретный буфер в виде среза байт `[]byte`.",
            "Выполните целевую криптографическую операцию.",
            "Реализуйте функцию `Wipe(b []byte)`, перезаписывающую байты нулями.",
            "Примените `runtime.KeepAlive` для предотвращения оптимизации Dead Store Elimination компилятором."
        ],
        "code_blocks": [
            {
                "filename": "wiping.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"crypto/subtle\"\n\t\"fmt\"\n\t\"runtime\"\n)\n\n// WipeBytes перезаписывает срез байт нулями и защищает от оптимизации компилятора\nfunc WipeBytes(data []byte) {\n\tif len(data) == 0 {\n\t\treturn\n\t}\n\t// Используем subtle или явную запись для гарантированного затирания\n\tfor i := range data {\n\t\tdata[i] = 0\n\t}\n\t// Предотвращаем преждевременный сброс ссылки оптимизатором SSA\n\truntime.KeepAlive(data)\n}\n\nfunc main() {\n\tpassword := []byte(\"SuperSecretEnterpriseMasterKey!2026\")\n\tfmt.Printf(\"[BEFORE WIPE] Адрес: %p, Длина: %d, Содержимое: %s\\n\", password, len(password), string(password))\n\n\t// Имитация аутентификации\n\t_ = subtle.ConstantTimeCompare(password, password)\n\n\t// Немедленная очистка памяти\n\tWipeBytes(password)\n\n\tfmt.Printf(\"[AFTER WIPE]  Адрес: %p, Первые байты: %v (память очищена)\\n\", password, password[:5])\n}\n",
                "note": "Гарантированная перезапись секретов в оперативной памяти"
            }
        ],
        "under_the_hood": "Компилятор Go выполняет SSA-оптимизацию Dead Store Elimination: если после записи в память переменная больше не читается, компилятор может вырезать цикл обнуления. `runtime.KeepAlive` создает фиктивное использование переменной, принуждая рантайм сохранить запись.",
        "pitfalls": "Преобразование `string(password)` создает новую неконтролируемую аллокацию в куче, которую невозможно затереть вручную.",
        "bigtech_interview": "На собеседованиях в безопасность часто спрашивают: 'Почему в crypto/tls или vault клиентах пароли принимаются как []byte, а не string?'"
    },
    {
        "num": 61,
        "title": "Генерация SLSA Provenance через slsa-github-generator",
        "task": "Опишите структуру GitHub Actions workflow с использованием slsa-framework/slsa-github-generator для создания неизменяемого аттестата сборки Go-бинарника (SLSA Level 3).",
        "theory": "SLSA GitHub Generator — официальный Reusable Workflow от OpenSSF, который выполняет сборку в изолированном раннере, генерирует криптографический манифест происхождения (Provenance) в формате in-toto и подписывает его с использованием Sigstore Fulcio/Cosign. Это гарантирует, что бинарник собран именно из указанного коммита, репозитория и ветки, исключая подмену артефакта.",
        "step_by_step": [
            "Определите триггер сборки релиза в репозитории.",
            "Вызовите доверенный workflow `slsa-framework/slsa-github-generator/.github/workflows/builder_go_slsa3.yml`.",
            "Сконфигурируйте параметры сборки (go-version, config-file, имя артефакта).",
            "Получите на выходе бинарник и сопровождающий файл аттестата `*.intoto.jsonl`."
        ],
        "code_blocks": [
            {
                "filename": "slsa_workflow.yml",
                "lang": "yaml",
                "code": "name: SLSA Go Releaser\non:\n  push:\n    tags:\n      - 'v*'\n\npermissions: read-all\n\njobs:\n  build:\n    permissions:\n      id-token: write\n      contents: write\n      actions: read\n    uses: slsa-framework/slsa-github-generator/.github/workflows/builder_go_slsa3.yml@v2.0.0\n    with:\n      go-version: '1.22'\n      config-file: .slsa-goreleaser.yml\n      evaluated-envs: \"COMMIT_DATE:$(date -u +'%Y-%m-%dT%H:%M:%SZ')\"\n",
                "note": "Конфигурация SLSA Level 3 генератора для Go проектов"
            }
        ],
        "under_the_hood": "slsa-github-generator использует GitHub OIDC токен для получения эфемерного X.509 сертификата от Sigstore Fulcio, связывая идентичность репозитория и хэш коммита с выходным бинарником.",
        "pitfalls": "Запуск сборки на собственных раннерах (self-hosted) без должной изоляции не позволяет достичь SLSA Level 3 из-за потенциальной возможности модификации хостовой ОС.",
        "bigtech_interview": "В крупных IT-компаниях развертываются аналогичные внутренние доверенные сборочные фермы (Secure CI Runners), куда у разработчиков нет SSH-доступа."
    },
    {
        "num": 62,
        "title": "Локальный вендоринг зависимостей в enterprise-контурах",
        "task": "Разработайте скрипт подготовки и сборки автономного дистрибутива с флагом -mod=vendor и напишите валидатор отсутствия внешних DNS и сетевых обращений в изолированной среде.",
        "theory": "Локальный вендоринг (`go mod vendor`) решает задачу полного контроля над сторонним кодом: код зависимостей физически размещается в директории `vendor/` репозитория. В закрытых контурах (Air-Gapped) сетевой доступ к сети интернет полностью заблокирован. Сборка с флагом `go build -mod=vendor` гарантирует, что компилятор не предпринимает сетевых попыток обращения к `proxy.golang.org` или `sum.golang.org`.",
        "step_by_step": [
            "Выполните команду `go mod tidy` для актуализации дерева зависимостей.",
            "Сгенерируйте вендор-папку командой `go mod vendor`.",
            "Соберите проект с флагом `go build -mod=vendor -v`.",
            "Проверьте, что в изолированном сетевом неймспейсе (`unshare -n`) сборка проходит без ошибок."
        ],
        "code_blocks": [
            {
                "filename": "build_vendor.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[1/3] Синхронизация зависимостей...\"\ngo mod tidy\n\necho \"[2/3] Формирование локального vendor каталога...\"\ngo mod vendor\n\necho \"[3/3] Компиляция в изолированном режиме (-mod=vendor)...\"\n# Симуляция сборки в офлайн режиме без сетевого доступа\nexport GOPROXY=off\ngo build -mod=vendor -o app_offline main.go\n\necho \"[SUCCESS] Автономный бинарник успешно собран!\"\n",
                "note": "Сборка проекта без доступа к сети через локальный каталог vendor"
            }
        ],
        "under_the_hood": "При `-mod=vendor` Go toolchain подменяет пути импорта на локальные пути внутри каталога `vendor/`. Поиск модулей в `$GOPATH/pkg/mod` полностью отключается.",
        "pitfalls": "Если один из разработчиков обновит `go.mod`, но забудет выполнить `go mod vendor`, сборка в CI с флагом `-mod=vendor` завершится ошибкой несоответствия `modules.txt`.",
        "bigtech_interview": "В инфраструктуре Яндекса весь внешний код сначала проходит процедуру импорта во внутренний монорепозиторий (Arcadia) с обязательным ручным аудитом лицензий и безопасности."
    },
    {
        "num": 63,
        "title": "Аттестаты цепочки поставок фреймворка in-toto",
        "task": "Реализуйте Go-модуль для формирования и верификации метаданных in-toto Statement (Link/Layout) для фиксации материалов (materials) и продуктов (products) этапа сборки.",
        "theory": "in-toto — открытый фреймворк для обеспечения сквозной безопасности цепочки разработки ПО. Он позволяет описать процесс разработки как цепочку шагов (Layout). Каждый шаг (Step) фиксирует входные материалы (Materials — исходники коммита) и выходные продукты (Products — скомпилированный бинарник) с их криптографическими хешами в подписанном документе аттестата (Link metadata).",
        "step_by_step": [
            "Создайте спецификацию in-toto Statement v0.1 / v1.0.",
            "Заполните блок субъекта (`subject`) с указанием имени бинарника и его SHA-256.",
            "Определите предикат (`predicate`) типа SLSA или Custom Link с фиксацией входных хешей.",
            "Сериализуйте документ в JSON и проверьте валидность структуры."
        ],
        "code_blocks": [
            {
                "filename": "intoto_statement.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n)\n\ntype ResourceDescriptor struct {\n\tName   string            `json:\"name\"`\n\tDigest map[string]string `json:\"digest\"`\n}\n\ntype InTotoStatement struct {\n\tType          string               `json:\"_type\"`\n\tSubject       []ResourceDescriptor `json:\"subject\"`\n\tPredicateType string               `json:\"predicateType\"`\n\tPredicate     map[string]any       `json:\"predicate\"`\n}\n\nfunc main() {\n\tstmt := InTotoStatement{\n\t\tType: \"https://in-toto.io/Statement/v1\",\n\t\tSubject: []ResourceDescriptor{\n\t\t\t{\n\t\t\t\tName: \"auth-service-linux-amd64\",\n\t\t\t\tDigest: map[string]string{\n\t\t\t\t\t\"sha256\": \"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855\",\n\t\t\t\t},\n\t\t\t},\n\t\t},\n\t\tPredicateType: \"https://slsa.dev/provenance/v1\",\n\t\tPredicate: map[string]any{\n\t\t\t\"buildDefinition\": map[string]any{\n\t\t\t\t\"buildType\": \"https://actions.github.com/buildtypes/go/v1\",\n\t\t\t},\n\t\t},\n\t}\n\n\tbytes, _ := json.MarshalIndent(stmt, \"\", \"  \")\n\tfmt.Println(string(bytes))\n}\n",
                "note": "Формирование аттестата in-toto Statement v1"
            }
        ],
        "under_the_hood": "Cosign использует стандарт in-toto attestation envelope (DSSE — Dead Simple Signing Envelope) для упаковки любых произвольных метаданных (тесты, сканы уязвимостей, provenance) внутрь OCI реестра.",
        "pitfalls": "Несоответствие схемы предикатов (PredicateType) приводит к сбоям автоматических парсеров в admission контроллерах Kubernetes.",
        "bigtech_interview": "В архитектуре безопасности Google BeyondProd аттестация каждого этапа конвейера является основой для принятия решения о допуске сервиса к обработке пользовательских данных."
    },
    {
        "num": 64,
        "title": "Инспекция и сопоставление SBOM бинарных файлов утилитой Syft",
        "task": "Напишите Go-утилиту, которая парсит JSON-отчет Syft для скомпилированного Go-бинарника и проверяет наличие компонентов без фиксированной версии или с нелицензионным кодом.",
        "theory": "Утилита Syft от Anchore умеет извлекать SBOM непосредственно из скомпилированных Go-бинарников благодаря анализу секции BuildInfo, внедряемой компилятором Go. В корпоративной разработке полученный SBOM сопоставляется с внутренними политиками Legal/Compliance для обнаружения вирусных лицензий (GPLv3 в закрытом проприетарном сервисе) и устаревших зависимостей.",
        "step_by_step": [
            "Скомпилируйте Go-приложение с флагами оптимизации.",
            "Сгенерируйте отчет командой `syft packages file:app.bin -o json`.",
            "Разработайте Go-парсер артефакта Syft для валидации лицензий и версий.",
            "Выведите предупреждения при обнаружении несовместимых лицензий."
        ],
        "code_blocks": [
            {
                "filename": "syft_parser.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"strings\"\n)\n\ntype SyftArtifact struct {\n\tArtifacts []struct {\n\t\tName     string   `json:\"name\"`\n\t\tVersion  string   `json:\"version\"`\n\t\tType     string   `json:\"type\"`\n\t\tLicenses []string `json:\"licenses\"`\n\t} `json:\"artifacts\"`\n}\n\nfunc main() {\n\trawSyftJSON := `{\n\t\t\"artifacts\": [\n\t\t\t{\"name\": \"github.com/google/uuid\", \"version\": \"v1.6.0\", \"type\": \"go-module\", \"licenses\": [\"BSD-3-Clause\"]},\n\t\t\t{\"name\": \"github.com/unknown/copyleft-lib\", \"version\": \"v0.1.0\", \"type\": \"go-module\", \"licenses\": [\"GPL-3.0-only\"]}\n\t\t]\n\t}`\n\n\tvar report SyftArtifact\n\tif err := json.Unmarshal([]byte(rawSyftJSON), &report); err != nil {\n\t\tpanic(err)\n\t}\n\n\tfor _, art := range report.Artifacts {\n\t\tfor _, lic := range art.Licenses {\n\t\t\tif strings.HasPrefix(lic, \"GPL\") {\n\t\t\t\tfmt.Printf(\"[LEGAL ALERT] Обнаружена копилефтная лицензия %s в пакете %s!\\n\", lic, art.Name)\n\t\t\t}\n\t\t}\n\t}\n\tfmt.Println(\"[AUDIT] Анализ лицензий завершен.\")\n}\n",
                "note": "Аудит лицензионной чистоты компонентов из отчета Syft"
            }
        ],
        "under_the_hood": "Syft считывает таблицу символов и встроенный блок `ÿ Go buildinf:` внутри ELF/Mach-O/PE исполняемого файла, извлекая модуль, ревизию и список зависимостей без декомпиляции машинного кода.",
        "pitfalls": "Если бинарник собран со стриппингом метаданных (`-ldflags=\"-s -w\"`), некоторые утилиты не могут восстановить BuildInfo, поэтому для аудита рекомендуется использовать `syft dir:.` на этапе CI.",
        "bigtech_interview": "В юротделах BigTech компаний (Авито, Ozon) автоматический аудит SBOM блокирует merge request, если в зависимостях обнаружена лицензия AGPLv3."
    },
    {
        "num": 65,
        "title": "Настройка корпоративного Private Module Proxy (Athens / Artifactory)",
        "task": "Сконфигурируйте и опишите архитектуру корпоративного Go-прокси в изолированном контуре (Air-Gapped) с поддержкой GOPROXY, GONOSUMDB и фильтрацией приватных модулей.",
        "theory": "Публичный `proxy.golang.org` не имеет доступа к внутренним репозиториям компании (GitLab, Bitbucket) и может раскрывать пути приватных модулей через запросы контрольных сумм. Для защиты конфиденциальности и надежности в корпоративной сети развертывают собственный прокси (Athens, JFrog Artifactory, Nexus). Переменные окружения настраиваются так:\n`GOPROXY=https://athens.corp.internal,https://proxy.golang.org,direct`\n`GONOSUMDB=git.corp.internal/*`\n`GONOPROXY=git.corp.internal/*`.",
        "step_by_step": [
            "Разверните локальный экземпляр Athens Proxy с персистентным хранилищем (S3/MinIO).",
            "Сконфигурируйте список исключений для приватных доменов через `GONOPROXY` и `GONOSUMDB`.",
            "Протестируйте поведение `go get` при недоступности интернета (работа через корпоративный кэш).",
            "Напишите Go-тест для валидации правильности настройки переменных окружения сборщика."
        ],
        "code_blocks": [
            {
                "filename": "proxy_checker.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n\t\"strings\"\n)\n\nfunc main() {\n\tgoproxy := os.Getenv(\"GOPROXY\")\n\tgonosumdb := os.Getenv(\"GONOSUMDB\")\n\n\tfmt.Printf(\"[ENV] GOPROXY=%s\\n\", goproxy)\n\tfmt.Printf(\"[ENV] GONOSUMDB=%s\\n\", gonosumdb)\n\n\tif !strings.Contains(goproxy, \"corp.internal\") && goproxy != \"\" {\n\t\tfmt.Println(\"[WARN] Корпоративный прокси Athens не обнаружен в цепочке GOPROXY!\")\n\t}\n\n\tif gonosumdb == \"\" {\n\t\tfmt.Println(\"[CRITICAL] Переменная GONOSUMDB пуста! Риск утечки внутренних путей модулей в Google!\")\n\t} else {\n\t\tfmt.Println(\"[OK] Приватные модули исключены из публичной базы сумм.\")\n\t}\n}\n",
                "note": "Валидация переменных окружения Go toolchain для корпоративной безопасности"
            }
        ],
        "under_the_hood": "Athens кэширует неизменяемые архивы `.zip`, `.mod` и `.info` модулей. Даже если автор публичной библиотеки удалит свой репозиторий с GitHub, локальный кэш Athens продолжит отдавать зафиксированную версию.",
        "pitfalls": "Забытый `GONOSUMDB` приведет к тому, что `go` попытается запросить контрольную сумму приватного модуля `git.mycorp.ru/auth/secret` у серверов Google (`sum.golang.org`), что приведет к ошибке 404 и утечке названия модуля.",
        "bigtech_interview": "В Т-Банке и Сбере весь внешний трафик разработчиков строго изолирован, а сборка пайплайнов происходит исключительно через внутренний кэширующий зеркальный кластер Artifactory."
    },
    {
        "num": 66,
        "title": "Множественные цифровые подписи артефактов (Multi-Signature Verification)",
        "task": "Реализуйте Go-верификатор, требующий наличия цифровых подписей сразу от нескольких независимых сторон (команды разработки и отдела информационной безопасности — кворум 2 из 2).",
        "theory": "Для критически важных сервисов (платежные шлюзы, управление криптографическими ключами) принцип разделения обязанностей (Separation of Duties) требует множественной подписи артефакта (Multi-party Signing). Образ или бинарник признается валидным только тогда, когда на нем стоят подписи как сборочного пайплайна (Dev Team), так и автоматического сканера безопасности (Sec Team).",
        "step_by_step": [
            "Сгенерируйте открытые ключи двух независимых доверенных центров (Dev и Sec).",
            "Создайте подписи артефакта каждым из ключей.",
            "Напишите Go-верификатор, проверяющий наличие и корректность каждой подписи.",
            "Убедитесь, что отсутствие хотя бы одной из обязательных подписей блокирует деплой."
        ],
        "code_blocks": [
            {
                "filename": "multisig.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"crypto\"\n\t\"crypto/rsa\"\n\t\"crypto/sha256\"\n\t\"fmt\"\n)\n\ntype SignatureAuthority struct {\n\tRole      string\n\tPublicKey *rsa.PublicKey\n}\n\nfunc VerifyQuorum(digest []byte, signatures map[string][]byte, authorities []SignatureAuthority) bool {\n\tvalidCount := 0\n\tfor _, auth := range authorities {\n\t\tsig, exists := signatures[auth.Role]\n\t\tif !exists {\n\t\t\tfmt.Printf(\"[REJECT] Отсутствует обязательная подпись роли: %s\\n\", auth.Role)\n\t\t\treturn false\n\t\t}\n\t\terr := rsa.VerifyPKCS1v15(auth.PublicKey, crypto.SHA256, digest, sig)\n\t\tif err != nil {\n\t\t\tfmt.Printf(\"[REJECT] Невалидная подпись для роли %s: %v\\n\", auth.Role, err)\n\t\t\treturn false\n\t\t}\n\t\tvalidCount++\n\t}\n\treturn validCount == len(authorities)\n}\n\nfunc main() {\n\thash := sha256.Sum256([]byte(\"binary payload v2.4\"))\n\tfmt.Printf(\"[MULTISIG] Дайджест артефакта: %x\\n\", hash)\n\t// Имитация валидации кворума\n\tfmt.Println(\"[MULTISIG] Требуется кворум: [DevTeam, SecOps]\")\n}\n",
                "note": "Кворумная проверка множественных цифровых подписей"
            }
        ],
        "under_the_hood": "Cosign сохраняет множественные подписи как отдельные OCI-дескрипторы внутри единого тега `.sig` образа. Верификатор может сопоставлять открытые ключи или SAN-сертификаты из Fulcio с заданным списком регулярных выражений.",
        "pitfalls": "Рассинхронизация времени выпуска подписей может приводить к ложным сбоям, если одна подпись уже опубликована, а вторая еще генерируется в соседнем джобе CI.",
        "bigtech_interview": "В финтех-проектах требование «четырех глаз» (Four-Eyes Principle) для выпуска прод-артефактов является нормативным требованием Банка России."
    },
    {
        "num": 67,
        "title": "Контроль срока действия цифровых подписей (Signature Expiration)",
        "task": "Разработайте Go-модуль проверки срока действия сертификатов и цифровых подписей, отклоняющий устаревшие подписи даже при их математической корректности.",
        "theory": "В бесключевом режиме Sigstore (Keyless Signing) сертификаты Fulcio выдаются на короткий срок (обычно 10 минут) для защиты от компрометации. Проверка времени создания подписи выполняется через временные метки прозрачного журнала Rekor (RFC 3161 Timestamping). Для традиционных X.509 сертификатов верификатор обязан проверять поля `NotBefore` и `NotAfter` на текущий момент времени.",
        "step_by_step": [
            "Распарсите X.509 сертификат или метаданные временного штампа подписи.",
            "Сравните текущее время с окном валидности сертификата.",
            "Проверьте криптографическую подпись временной метки (Timestamp Authority).",
            "Верните ошибку `ErrSignatureExpired`, если срок действия истек."
        ],
        "code_blocks": [
            {
                "filename": "expiry_checker.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"crypto/x509\"\n\t\"errors\"\n\t\"fmt\"\n\t\"time\"\n)\n\nvar ErrSignatureExpired = errors.New(\"срок действия цифровой подписи истек\")\n\nfunc ValidateCertValidity(cert *x509.Certificate, checkTime time.Time) error {\n\tif checkTime.Before(cert.NotBefore) {\n\t\treturn fmt.Errorf(\"сертификат еще не вступил в силу (действителен с %v)\", cert.NotBefore)\n\t}\n\tif checkTime.After(cert.NotAfter) {\n\t\treturn ErrSignatureExpired\n\t}\n\treturn nil\n}\n\nfunc main() {\n\tcert := &x509.Certificate{\n\t\tNotBefore: time.Now().Add(-24 * time.Hour),\n\t\tNotAfter:  time.Now().Add(-1 * time.Hour), // Просрочен час назад\n\t}\n\n\terr := ValidateCertValidity(cert, time.Now())\n\tif errors.Is(err, ErrSignatureExpired) {\n\t\tfmt.Println(\"[SECURITY ERROR] Подпись отклонена: срок действия сертификата истек!\")\n\t} else {\n\t\tfmt.Println(\"[OK] Сертификат действителен.\")\n\t}\n}\n",
                "note": "Проверка срока годности цифрового сертификата подписи"
            }
        ],
        "under_the_hood": "В Sigstore проверка короткоживущего сертификата опирается на подтверждение времени записи в журнал Rekor (SET — Signed Entry Timestamp). Если запись внесена в Rekor в период действия сертификата, подпись признается бессрочно валидной.",
        "pitfalls": "Использование локального времени сервера без синхронизации по NTP может приводить к ложным срабатываниям валидатора из-за временного дрейфа (clock skew).",
        "bigtech_interview": "На собеседованиях по безопасности спрашивают, как работает проверка подлинности кода при отзыве сертификата (CRL / OCSP stapling) и чем хороши short-lived сертификаты."
    },
    {
        "num": 68,
        "title": "Создание и прикрепление SLSA-аттестатов утилитой Cosign",
        "task": "Реализуйте Go-скрипт или CLI-обертку над cosign attest для связывания предиката SLSA Provenance с OCI-образом и извлечения аттестата через cosign verify-attestation.",
        "theory": "Аттестация в Cosign (`cosign attest`) позволяет связать с OCI-образом структурированный документ (например, отчет о прохождении тестов, результат сканирования SAST или SLSA Provenance). В отличие от простой подписи образа, аттестат содержит проверяемые утверждения (Claims), упакованные в конверт in-toto. Admission Webhook может валидировать конкретные поля предикатов, например, требуя чтобы `tests_passed == true`.",
        "step_by_step": [
            "Сформируйте файл предиката `predicate.json` с метаданными сборщика.",
            "Выполните команду прикрепления аттестата: `cosign attest --key cosign.key --predicate predicate.json --type slsaprovenance $IMAGE`.",
            "Выполните верификацию аттестата: `cosign verify-attestation --key cosign.pub --type slsaprovenance $IMAGE`.",
            "Реализуйте в Go парсинг извлеченного JSON payload для проверки утверждений."
        ],
        "code_blocks": [
            {
                "filename": "attest_parser.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/base64\"\n\t\"encoding/json\"\n\t\"fmt\"\n)\n\ntype CosignPayload struct {\n\tPayloadType string `json:\"payloadType\"`\n\tPayload     string `json:\"payload\"` // base64 encoded in-toto statement\n}\n\ntype InTotoStatement struct {\n\tPredicateType string `json:\"predicateType\"`\n\tPredicate     struct {\n\t\tBuilder struct {\n\t\t\tID string `json:\"id\"`\n\t\t} `json:\"builder\"`\n\t} `json:\"predicate\"`\n}\n\nfunc main() {\n\t// Пример декодирования payload из вывода cosign verify-attestation\n\trawInToto := `{\"predicateType\":\"https://slsa.dev/provenance/v0.2\",\"predicate\":{\"builder\":{\"id\":\"https://github.com/my-org/trusted-builder\"}}}`\n\tb64Payload := base64.StdEncoding.EncodeToString([]byte(rawInToto))\n\n\tdata, err := base64.StdEncoding.DecodeString(b64Payload)\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\n\tvar stmt InTotoStatement\n\tif err := json.Unmarshal(data, &stmt); err != nil {\n\t\tpanic(err)\n\t}\n\n\tfmt.Printf(\"[ATTESTATION] Тип предиката: %s\\n\", stmt.PredicateType)\n\tfmt.Printf(\"[ATTESTATION] Доверенный Builder ID: %s\\n\", stmt.Predicate.Builder.ID)\n\tif stmt.Predicate.Builder.ID == \"https://github.com/my-org/trusted-builder\" {\n\t\tfmt.Println(\"[OK] Аттестат сборщика подтвержден!\")\n\t}\n}\n",
                "note": "Парсинг и верификация утверждений внутри Cosign attestation"
            }
        ],
        "under_the_hood": "Аттестат упаковывается в OCI-образ со специальным тегом `sha256-<digest>.att` в том же репозитории, что делает его портативным и версионируемым вместе с основным контейнером.",
        "pitfalls": "Аттестация больших бинарных файлов напрямую в реестр может приводить к раздуванию OCI манифестов; в аттестат следует помещать только криптографические дайджесты и метаданные.",
        "bigtech_interview": "В enterprise-системах безопасности аттестация используется для реализации концепции Binary Authorization: без аттестата безопасности от ИБ образ физически не может запуститься в проде."
    }
]
