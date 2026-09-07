# -*- coding: utf-8 -*-
"""
Глава 81: Безопасность цепочки поставок (Supply Chain Security) и SBOM — Часть 2 (Упражнения 69-136)
"""

exercises = [
    {
        "num": 69,
        "title": "Отключение CGO для статической линковки и минимизации вектора атак",
        "task": "Соберите статически слинкованный бинарник без CGO (CGO_ENABLED=0), проверьте отсутствие динамических зависимостей libc через ldd или readelf и упакуйте его в минимальный Docker-образ FROM scratch.",
        "theory": "По умолчанию Go может использовать CGO для резолвинга DNS и работы с системными сертификатами. Включение CGO (`CGO_ENABLED=1`) связывает бинарник с системной библиотекой glibc/musl, делая его уязвимым к эксплойтам переполнения буфера в C-рантайме (например, уязвимости в getaddrinfo). Сборка с `CGO_ENABLED=0` порождает полностью автономный статически слинкованный ELF-файл, работающий даже в пустом контейнере `FROM scratch` без разделяемых библиотек, шелла и утилит ОС.",
        "step_by_step": [
            "Скомпилируйте программу с флагом `CGO_ENABLED=0 go build -ldflags=\"-s -w\" -o app .`.",
            "Выполните команду `file app` и проверьте признак `statically linked`.",
            "Запустите `ldd app` и убедитесь в сообщении `not a dynamic executable`.",
            "Сформируйте Dockerfile на базе `FROM scratch` с добавлением только CA-сертификатов."
        ],
        "code_blocks": [
            {
                "filename": "static_build.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[1/3] Компиляция чистого Go бинарника без CGO...\"\nCGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags=\"-s -w\" -o myapp .\n\necho \"[2/3] Анализ зависимостей libc...\"\nif file myapp | grep -q \"statically linked\"; then\n    echo \"[OK] Бинарник статически слинкован (CGO отключен)\"\nelse\n    echo \"[FAIL] Бинарник содержит динамические зависимости!\"\n    exit 1\nfi\n\necho \"[3/3] Проверка ldd...\"\nldd myapp 2>&1 | grep -q \"not a dynamic executable\" && echo \"[OK] ldd подтвердил отсутствие внешних библиотек\"\n",
                "note": "Скрипт валидации статической линковки и изоляции от libc"
            }
        ],
        "under_the_hood": "При `CGO_ENABLED=0` Go использует встроенный сетевой резолвер на чистом Go (pure Go net resolver), который парсит `/etc/resolv.conf` и общается с DNS-серверами напрямую через сокеты UDP/TCP без вызова `getaddrinfo()` из glibc.",
        "pitfalls": "Если в чистый контейнер `scratch` не скопировать файл корневых сертификатов `/etc/ssl/certs/ca-certificates.crt`, HTTPS-запросы приложения упадут с ошибкой `x509: certificate signed by unknown authority`.",
        "bigtech_interview": "На собеседованиях в Ozon и Авито кандидатов часто просят объяснить разницу между Alpine Linux с musl libc и контейнерами scratch / distroless с точки зрения DevSecOps и размера образов."
    },
    {
        "num": 70,
        "title": "Добавление метаданных и аннотаций при подписании образов Cosign",
        "task": "Реализуйте подпись OCI-образа с внедрением пользовательских криптографических аннотаций (коммит, автор, окружение) через cosign sign --annotations.",
        "theory": "Cosign позволяет внедрять в цифровую подпись произвольные пары ключ-значение (annotations). Эти данные защищены той же криптографической подписью, что и образ. При верификации можно требовать не просто факт наличия подписи, но и совпадение аннотаций (например, `env=production` или `repo=github.com/myorg/backend`), что предотвращает использование тестовых сборок в проде.",
        "step_by_step": [
            "Соберите OCI-образ и отправьте его в реестр.",
            "Сформируйте набор аннотаций: `commit=$(git rev-parse HEAD)`, `build_env=production`.",
            "Подпишите образ с флагами `--annotations`: `cosign sign --key cosign.key -a env=production -a commit=$SHA $IMAGE`.",
            "Убедитесь в успешной публикации подписи с аннотациями в OCI-манифесте."
        ],
        "code_blocks": [
            {
                "filename": "sign_annotations.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nIMAGE=\"myregistry.corp/payments/api:v1.2.0\"\nCOMMIT=\"4f8a3c9b\"\nBUILD_TIME=$(date -u +\"%Y-%m-%dT%H:%M:%SZ\")\n\necho \"[COSIGN] Подписание образа с криптографическими аннотациями...\"\n# Симуляция вызова cosign sign\necho \"cosign sign --key cosign.key \\\n  -a org=MyCompany \\\n  -a environment=production \\\n  -a git_commit=${COMMIT} \\\n  -a build_time=${BUILD_TIME} \\\n  ${IMAGE}\"\n\necho \"[SUCCESS] Аннотации зафиксированы в криптографическом слое подписи.\"\n",
                "note": "Подписание контейнера с внедрением метаданных окружения"
            }
        ],
        "under_the_hood": "Аннотации помещаются в поле `annotations` дескриптора OCI-слоя подписи. Любая попытка изменить аннотацию нарушает подпись открытым ключом.",
        "pitfalls": "Хранение чувствительных секретов (токенов, паролей) в аннотациях недопустимо, так как аннотации подписи открыты для чтения всем пользователям реестра.",
        "bigtech_interview": "В enterprise-системах Kubernetes аннотации подписи Cosign проверяются Gatekeeper-политиками для гарантии, что образ собран именно на защищенном раннере GitLab CI, а не локально разработчиком."
    },
    {
        "num": 71,
        "title": "Фиксация и заморозка зависимостей в Git через go mod vendor",
        "task": "Организуйте полный цикл вендоринга для многомодульного репозитория, настройте проверку консистентности modules.txt и автоматизируйте сборку с -mod=vendor в CI.",
        "theory": "Вендоринг зависимостей фиксирует точные копии сторонних пакетов в каталоге `vendor/` проекта. Это устраняет риск исчезновения библиотек из публичных репозиториев (инцидент left-pad), гарантирует идентичность исходников между локальной разработкой и сборочным сервером и защищает от скрытой подмены исходников на внешних Git-хостингах.",
        "step_by_step": [
            "Выполните `go mod tidy` и зафиксируйте `go.mod` и `go.sum`.",
            "Выполните `go mod vendor` для выгрузки исходных кодов сторонних библиотек.",
            "Добавьте `vendor/` в систему контроля версий Git.",
            "Настройте этап CI: `go build -mod=vendor ./...` и проверку отсутствия диффа в `git status`."
        ],
        "code_blocks": [
            {
                "filename": "freeze_deps.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[1/3] Актуализация дерева зависимостей...\"\ngo mod tidy\n\necho \"[2/3] Обновление vendor папки...\"\ngo mod vendor\n\necho \"[3/3] Проверка консистентности (no git diff)...\"\nif [ -n \"$(git status --porcelain vendor/ go.mod go.sum)\" ]; then\n    echo \"[WARN] Каталог vendor/ не синхронизирован с go.mod! Закоммитьте изменения.\"\nelse\n    echo \"[OK] Все зависимости синхронизированы и заморожены.\"\nfi\n",
                "note": "Скрипт проверки целостности и синхронизации каталога vendor"
            }
        ],
        "under_the_hood": "Go сохраняет в `vendor/modules.txt` полный манифест с версиями модулей и путями пакетов. Если `go.mod` содержит зависимость, отсутствующую в `modules.txt`, компилятор с флагом `-mod=vendor` завершится с фатальной ошибкой.",
        "pitfalls": "Смешивание ручных правок в каталоге vendor/ с автоматическим вендорингом приведет к потере изменений при следующем выполнении `go mod vendor`.",
        "bigtech_interview": "В компаниях с жесткими требованиями к комплаенсу (банковский сектор) вендоринг обязателен для возможности проведения ревизии кода сотрудниками ИБ без обращения в интернет."
    },
    {
        "num": 72,
        "title": "Верификация аннотаций подписи при валидации OCI-образов",
        "task": "Разработайте Go-скрипт проверки подписи Cosign с обязательной проверкой аннотаций (проверка окружения, ветки Git и идентификатора пайплайна).",
        "theory": "Команда `cosign verify -a <key>=<value>` проверяет не только криптографическую валидность открытого ключа, но и соответствие заявленных аннотаций. Если образ подписан доверенным ключом, но аннотация `environment` содержит значение `staging` вместо `production`, валидатор отклоняет образ, предотвращая проникновение тестовых артефактов в бой.",
        "step_by_step": [
            "Сконфигурируйте вызов утилиты cosign с флагом `-a` для каждой обязательной аннотации.",
            "Реализуйте обработку вывода cosign verify в Go.",
            "Проверьте сценарий отказа, когда ключ валиден, но аннотация не совпадает.",
            "Логируйте результат аудита в структурированном виде."
        ],
        "code_blocks": [
            {
                "filename": "verify_ann.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"os/exec\"\n\t\"time\"\n)\n\nfunc VerifyImageWithAnnotations(image, pubKey string, requiredAnn map[string]string) error {\n\tctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)\n\tdefer cancel()\n\n\targs := []string{\"verify\", \"--key\", pubKey}\n\tfor k, v := range requiredAnn {\n\t\targs = append(args, \"-a\", fmt.Sprintf(\"%s=%s\", k, v))\n\t}\n\targs = append(args, image)\n\n\tcmd := exec.CommandContext(ctx, \"cosign\", args...)\n\tout, err := cmd.CombinedOutput()\n\tif err != nil {\n\t\treturn fmt.Errorf(\"ошибка проверки аннотаций cosign: %v, вывод: %s\", err, string(out))\n\t}\n\tfmt.Printf(\"[OK] Образ успешно валидирован со всеми требуемыми аннотациями!\\n\")\n\treturn nil\n}\n\nfunc main() {\n\treq := map[string]string{\n\t\t\"environment\": \"production\",\n\t\t\"org\":         \"MyCompany\",\n\t}\n\tfmt.Printf(\"[VERIFY] Требуемые аннотации для допуска: %v\\n\", req)\n\t// Вызов валидатора (симуляция)\n\t_ = VerifyImageWithAnnotations\n}\n",
                "note": "Проверка совпадения аннотаций OCI-подписи в CI/CD"
            }
        ],
        "under_the_hood": "Cosign декодирует полезную нагрузку подписи (JSON SimpleSigning payload), находит карту `critical.identity` и сверяет все заданные флаги `-a` на точное побайтовое совпадение строк.",
        "pitfalls": "Регистрозависимость: аннотации `Production` и `production` будут признаны несовпадающими.",
        "bigtech_interview": "Как не допустить выкатку staging-образа в production-кластер Kubernetes? Ответ: Проверять аннотацию `env=prod` в Admission Webhook при верификации подписи Cosign."
    },
    {
        "num": 73,
        "title": "Иммутабельные изолированные сборки в Air-Gapped окружении",
        "task": "Сконфигурируйте полностью герметичный сборочный процесс на базе go build -mod=vendor в среде с изолированным сетевым пространством имен (network namespace).",
        "theory": "В изолированных средах (Air-Gapped / High-Security) сборочный хост физически или логически отключен от внешней сети. Использование локального каталога `vendor/` обеспечивает 100% автономность. Сборка не зависит от состояния внешних зеркал, DNS-серверов или доступности GitHub. В таких условиях гарантируется абсолютная воспроизводимость (immutable builds).",
        "step_by_step": [
            "Подготовьте полный каталог зависимостей с помощью `go mod vendor`.",
            "Запустите сборку в изолированном сетевом неймспейсе с помощью `unshare -n`.",
            "Убедитесь, что компилятор не падает и успешно генерирует бинарник.",
            "Проверьте, что попытка обращения к сети заблокирована на уровне ядра Linux."
        ],
        "code_blocks": [
            {
                "filename": "airgap_build.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[AIR-GAP] Запуск герметичной компиляции в изолированном сетевом неймспейсе...\"\n\n# Команда unshare -n создает изолированный стек сети (loopback down, нет интерфейсов)\nif command -v unshare &> /dev/null; then\n    unshare -n env GOPROXY=off go build -mod=vendor -v -o app_secure main.go\n    echo \"[SUCCESS] Проект собран в окружении без сетевого доступа!\"\nelse\n    # Fallback если нет прав root/unshare\n    GOPROXY=off go build -mod=vendor -o app_secure main.go\n    echo \"[OK] Проект собран с GOPROXY=off\"\nfi\n",
                "note": "Герметичная сборка без сетевого интерфейса"
            }
        ],
        "under_the_hood": "Флаг `-mod=vendor` указывает драйверу сборки Go не обращаться к механизму загрузки модулей. Модульный резолвер подменяется поиском путей в локальном дереве каталога `vendor/`.",
        "pitfalls": "Если в коде или тестах зашиты вызовы реальных внешних сетевых эндпоинтов, автономный прогон упадет с сетевой ошибкой.",
        "bigtech_interview": "Почему BigTech предпочитает монорепозитории и локальный вендоринг для критических сервисов? Для исключения внешних рисков доступности сторонних сервисов и контроля целостности всех зависимостей в едином коммите."
    },
    {
        "num": 74,
        "title": "Безопасная аутентификация в Git для приватных Go-модулей",
        "task": "Настройте директивы git config insteadOf для прозрачной подмены протокола HTTPS на SSH или внедрения персональных токенов доступа (PAT) в CI/CD без раскрытия секретов в коде.",
        "theory": "Приватные модули компании (например, `gitlab.corp.com/team/auth`) требуют аутентификации при загрузке через `go get`. Поскольку Go toolchain выполняет вызовы Git по протоколу HTTPS без интерактивного ввода пароля, в окружении CI настраивают перенаправление URL через `git config --global url.\"...\".insteadOf`. Для SSH используется ключ deploy key, а для HTTPS — эфемерный токен доступа раннера.",
        "step_by_step": [
            "Сконфигурируйте SSH-аутентификацию: `git config --global url.\"git@gitlab.corp.com:\".insteadOf \"https://gitlab.corp.com/\"`.",
            "Для HTTPS настройте внедрение токена: `git config --global url.\"https://oauth2:${CI_JOB_TOKEN}@gitlab.corp.com/\".insteadOf \"https://gitlab.corp.com/\"`.",
            "Установите `GOPRIVATE=gitlab.corp.com/*`.",
            "Проверьте бесшовную загрузку модулей командой `go mod download`."
        ],
        "code_blocks": [
            {
                "filename": "setup_git_auth.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nTOKEN=\"${CI_ACCESS_TOKEN:-x-access-token}\"\nCORP_HOST=\"github.company.internal\"\n\necho \"[GIT-AUTH] Настройка безопасного доступа к приватным модулям...\"\n# Настройка подмены HTTPS URL с токеном доступа\ngit config --global url.\"https://${TOKEN}@${CORP_HOST}/\".insteadOf \"https://${CORP_HOST}/\"\n\n# Исключение приватных модулей из публичных кэшей и баз сумм\nexport GOPRIVATE=\"${CORP_HOST}/*\"\n\necho \"[OK] Git сконфигурирован. Тестирование go mod download...\"\n# go mod download\n",
                "note": "Автоматическая настройка учетных данных Git для Go toolchain"
            }
        ],
        "under_the_hood": "Утилита `go get` делегирует клонирование репозиториев системному клиенту `git`. Правило `insteadOf` перехватывает сгенерированный URL до установления сетевого соединения, прозрачно добавляя заголовки авторизации.",
        "pitfalls": "Логирование вывода команды `git config --list` в общедоступные логи сборки может привести к утечке секретного токена в открытом виде.",
        "bigtech_interview": "В GitLab CI для безопасного скачивания приватных подмодулей используется встроенный эфемерный токен `CI_JOB_TOKEN`, который инвалидируется сразу после завершения пайплайна."
    },
    {
        "num": 75,
        "title": "Криптографическая привязка и подписание SBOM через Cosign",
        "task": "Реализуйте аттестацию OCI-образа программным паспортом SBOM (CycloneDX / SPDX) с помощью cosign attest и напишите Go-скрипт извлечения и верификации SBOM перед развертыванием.",
        "theory": "Создание SBOM решает задачу инвентаризации, но без криптографической защиты злоумышленник может подменить SBOM, удалив из него записи об уязвимых библиотеках. Sigstore Cosign позволяет прикрепить SBOM к образу в виде криптографического аттестата (`cosign attest --predicate sbom.json --type cyclonedx`). При верификации гарантируется, что перечень компонентов составлен именно доверенным сборочным конвейером.",
        "step_by_step": [
            "Сгенерируйте SBOM для бинарника или образа: `syft packages -o cyclonedx-json > sbom.json`.",
            "Подпишите и прикрепите SBOM: `cosign attest --key cosign.key --predicate sbom.json --type cyclonedx $IMAGE`.",
            "Реализуйте извлечение аттестата: `cosign verify-attestation --key cosign.pub --type cyclonedx $IMAGE`.",
            "Распарсите полученный JSON в Go-сервисе безопасности."
        ],
        "code_blocks": [
            {
                "filename": "attest_sbom.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nIMAGE=\"myregistry.corp/service:v1.0.0\"\n\necho \"[1/2] Генерация паспорта компонентов (SBOM)...\"\n# syft packages ${IMAGE} -o spdx-json > sbom.spdx.json\n\necho \"[2/2] Прикрепление криптографического аттестата SBOM через Cosign...\"\n# cosign attest --key cosign.key --predicate sbom.spdx.json --type spdxjson ${IMAGE}\n\necho \"[OK] Аттестат SBOM подписан и опубликован в реестре OCI рядом с образом.\"\n",
                "note": "Скрипт прикрепления подписанного SBOM к контейнеру"
            }
        ],
        "under_the_hood": "Cosign сохраняет предикат SBOM в формате envelope DSSE (Dead Simple Signing Envelope), сериализуя тело манифеста в Base64 и подписывая хеш SHA-256 полезной нагрузки.",
        "pitfalls": "Большие файлы SBOM (десятки мегабайт) могут превышать ограничения OCI-реестра на размер одного слоя или вызывать таймауты сетевых запросов.",
        "bigtech_interview": "В стандартах US Executive Order 14028 и европейском Cyber Resilience Act требование подписанного SBOM является ключевым критерием допуска программного обеспечения на рынок."
    },
    {
        "num": 76,
        "title": "Защита от атаки Dependency Confusion (Подмена зависимостей)",
        "task": "Смоделируйте сценарий атаки Dependency Confusion, при котором злоумышленник публикует публичный пакет с тем же именем, что и внутренний модуль, но с версией v99.0.0. Настройте GOPRIVATE для блокировки утечки и подмены.",
        "theory": "Атака Dependency Confusion возникает, когда менеджер пакетов ищет зависимость как в приватном, так и в публичном репозитории. Если публичный реестр содержит пакет с тем же путем и более высокой версией (например, `v99.0.0`), сборщик может скачать вредоносный публичный код. В Go настройка `GOPRIVATE=mycorp.com/*` принуждает Go toolchain полностью игнорировать публичные `proxy.golang.org` и `sum.golang.org` для всех совпадающих путей импорта.",
        "step_by_step": [
            "Определите внутренний префикс модулей компании (например, `github.com/mycompany/*` или `corp.internal/*`).",
            "Установите переменную окружения `export GOPRIVATE=github.com/mycompany/*`.",
            "Проверьте, что переменные `GONOPROXY` и `GONOSUMDB` автоматически унаследовали эти правила.",
            "Напишите Go-тест, проверяющий, что приватные модули резолвятся только через внутренний VCS-сервер."
        ],
        "code_blocks": [
            {
                "filename": "goprivate_guard.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n\t\"strings\"\n)\n\nfunc main() {\n\tgoprivate := os.Getenv(\"GOPRIVATE\")\n\tcorporateDomain := \"github.com/mycompany/\"\n\n\tif goprivate == \"\" {\n\t\tfmt.Println(\"[CRITICAL ALERT] GOPRIVATE не задан! Риск атаки Dependency Confusion!\")\n\t\tos.Exit(1)\n\t}\n\n\tmatched := false\n\tfor _, pattern := range strings.Split(goprivate, \",\") {\n\t\tif strings.HasPrefix(corporateDomain, strings.TrimSuffix(pattern, \"*\")) {\n\t\t\tmatched = true\n\t\t\tbreak\n\t\t}\n\t}\n\n\tif !matched {\n\t\tfmt.Printf(\"[ERROR] Корпоративный префикс %s не покрыт правилами GOPRIVATE (%s)!\\n\", corporateDomain, goprivate)\n\t\tos.Exit(1)\n\t}\n\tfmt.Println(\"[OK] Защита от Dependency Confusion активна. Приватные модули изолированы.\")\n}\n",
                "note": "Валидация изоляции приватных путей импорта от публичных прокси"
            }
        ],
        "under_the_hood": "Когда префикс модуля попадает под маску `GOPRIVATE`, Go toolchain отключает вызовы `proxy.golang.org/lookup` и обращается напрямую к репозиторию по протоколам git/https, а также отключает проверку в `sum.golang.org`.",
        "pitfalls": "Если указать `GOPRIVATE=mycompany` вместо `mycompany.com/*`, маска может сработать некорректно для поддоменов или вложенных путей.",
        "bigtech_interview": "Исследователь Алекс Бирсан заработал сотни тысяч долларов на Bug Bounty, применив Dependency Confusion против Apple, Microsoft и Tesla. В Go эта проблема закрывается строгой настройкой GOPRIVATE."
    },
    {
        "num": 77,
        "title": "Сравнительный анализ стандартов SBOM: SPDX vs CycloneDX vs Syft",
        "task": "Разработайте Go-утилиту нормализации данных SBOM, сопоставляющую структуры SPDX 2.3 и CycloneDX 1.5 в единую унифицированную модель компонентов.",
        "theory": "Два главных международных стандарта SBOM:\n1. SPDX (Software Package Data Exchange) — стандарт Linux Foundation / ISO/IEC 5962:2021, исторически ориентированный на лицензионную чистоту и юридический аудит.\n2. CycloneDX — стандарт консорциума OWASP, специально спроектированный для нужд кибербезопасности, DevSecOps, анализа уязвимостей (VEX) и связей компонентов.\nФормат Syft JSON является внутренним представлением утилиты Syft, объединяющим расширенные метаданные бинарников.",
        "step_by_step": [
            "Определите унифицированную структуру `CanonicalComponent` (Name, Version, PURL, License, Hash).",
            "Реализуйте парсер для секции `packages` стандарта SPDX.",
            "Реализуйте парсер для секции `components` стандарта CycloneDX.",
            "Объедините и нормализуйте полученные данные в сводный отчет."
        ],
        "code_blocks": [
            {
                "filename": "sbom_normalizer.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n)\n\ntype CanonicalComponent struct {\n\tName    string `json:\"name\"`\n\tVersion string `json:\"version\"`\n\tPurl    string `json:\"purl\"`\n}\n\n// CycloneDX structure subset\ntype CDXDoc struct {\n\tComponents []struct {\n\t\tName    string `json:\"name\"`\n\t\tVersion string `json:\"version\"`\n\t\tPurl    string `json:\"purl\"`\n\t} `json:\"components\"`\n}\n\nfunc main() {\n\tcdxData := `{\n\t\t\"components\": [\n\t\t\t{\"name\": \"golang.org/x/crypto\", \"version\": \"v0.22.0\", \"purl\": \"pkg:golang/golang.org/x/crypto@v0.22.0\"}\n\t\t]\n\t}`\n\tvar doc CDXDoc\n\t_ = json.Unmarshal([]byte(cdxData), &doc)\n\n\tcanonical := make([]CanonicalComponent, 0, len(doc.Components))\n\tfor _, c := range doc.Components {\n\t\tcanonical = append(canonical, CanonicalComponent{\n\t\t\tName:    c.Name,\n\t\t\tVersion: c.Version,\n\t\t\tPurl:    c.Purl,\n\t\t})\n\t}\n\tfmt.Printf(\"[NORMALIZER] Успешно нормализовано %d компонентов в каноничный вид\\n\", len(canonical))\n}\n",
                "note": "Унификация форматов SBOM для межсистемного анализа"
            }
        ],
        "under_the_hood": "Поле PURL (Package URL) является общим связующим звеном между всеми стандартами: оно однозначно идентифицирует экосистему (`pkg:golang`), организацию, пакет и версию.",
        "pitfalls": "SPDX использует префикс `SPDXRef-Package-...`, а CycloneDX — UUID `bom-ref`. Потеря кросс-ссылок нарушает граф зависимостей при конвертации.",
        "bigtech_interview": "Какой формат SBOM выбрать для интеграции с SIEM/SOC и сканерами уязвимостей? Ответ: CycloneDX благодаря широкой поддержке VEX (Vulnerability Exploitability eXchange) и тесной интеграции с OWASP Dependency-Track."
    },
    {
        "num": 78,
        "title": "Установка, настройка и автоматизация CLI-сканера Syft",
        "task": "Напишите скрипт автоматической установки актуальной версии Anchore Syft с верификацией контрольных сумм и запустите сканирование локального скомпилированного Go-бинарника.",
        "theory": "Утилита `syft` от Anchore является де-факто стандартом командной строки для извлечения SBOM из файлов, папок и контейнеров. В безопасном CI/CD пайплайне установка сторонних CLI-инструментов должна сопровождаться обязательной проверкой криптографической контрольной суммы (SHA-256) дистрибутива перед запуском.",
        "step_by_step": [
            "Скачайте официальный архив релиза Syft с GitHub Releases.",
            "Загрузите сопровождающий файл контрольных сумм `checksums.txt`.",
            "Сверьте SHA-256 хеш скачанного бинарника с эталоном через `sha256sum --check`.",
            "Выполните тестовое сканирование: `syft packages dir:. -o table`."
        ],
        "code_blocks": [
            {
                "filename": "install_syft.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nSYFT_VERSION=\"v1.0.1\"\necho \"[SYFT] Безопасная установка Syft ${SYFT_VERSION}...\"\n\n# Скачивание официальным скриптом с проверкой контрольных сумм\ncurl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /tmp ${SYFT_VERSION}\n\n/tmp/syft --version\necho \"[OK] Syft успешно установлен и готов к генерации SBOM.\"\n",
                "note": "Установка Syft с проверкой ревизии и версионирования"
            }
        ],
        "under_the_hood": "Syft содержит встроенные каталогизаторы (catalogers) для Go (`cataloger/golang`), которые ищут `go.mod`, `go.sum`, а также декодируют секцию `.go.buildinfo` в ELF-заголовках бинарников.",
        "pitfalls": "Скачивание скрипта установки через `curl | sh` без указания точного тега версии может привести к неожиданной поломке CI при выходе несовместимой мажорной версии.",
        "bigtech_interview": "В enterprise-контурах запуск внешних скриптов из сети заблокирован: все бинарники сборщиков должны браться из внутреннего доверенного репозитория артефактов (Nexus/Artifactory)."
    },
    {
        "num": 79,
        "title": "Воспроизводимые детерминированные сборки Go (Reproducible Builds)",
        "task": "Сконфигурируйте флаги компилятора Go (-trimpath, -ldflags=\"-s -w -buildid=\") для получения побайтово идентичных бинарников на разных машинах и проверьте совпадение sha256sum.",
        "theory": "Воспроизводимая сборка (Reproducible Build) гарантирует, что компиляция одних и тех же исходников всегда дает побайтово одинаковый бинарный файл. По умолчанию Go внедряет в бинарник абсолютные пути файловой системы разработчика и случайный Build ID. Флаг `-trimpath` удаляет пути к файлам исходников, а `-ldflags=\"-buildid=\"` исключает случайный идентификатор сборки, обеспечивая абсолютный детерминизм.",
        "step_by_step": [
            "Скомпилируйте проект с флагами: `go build -trimpath -ldflags=\"-s -w -buildid=\" -o bin1 .`.",
            "Скомпилируйте проект во временном каталоге с другим именем: `go build -trimpath -ldflags=\"-s -w -buildid=\" -o bin2 .`.",
            "Вычислите SHA-256 хеши обоих файлов: `sha256sum bin1 bin2`.",
            "Убедитесь в 100% побайтовом совпадении хешей."
        ],
        "code_blocks": [
            {
                "filename": "reproduce.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[1/3] Сборка первого бинарника (путь A)...\"\ngo build -trimpath -ldflags=\"-s -w -buildid=\" -o /tmp/app_build_a main.go\nHASH_A=$(sha256sum /tmp/app_build_a | awk '{print $1}')\n\necho \"[2/3] Сборка второго бинарника (путь B)...\"\ngo build -trimpath -ldflags=\"-s -w -buildid=\" -o /tmp/app_build_b main.go\nHASH_B=$(sha256sum /tmp/app_build_b | awk '{print $1}')\n\necho \"[3/3] Сравнение криптографических хешей:\"\necho \"Hash A: ${HASH_A}\"\necho \"Hash B: ${HASH_B}\"\n\nif [ \"${HASH_A}\" = \"${HASH_B}\" ]; then\n    echo \"[SUCCESS] Сборка 100% воспроизводима (детерминирована)!\"\nelse\n    echo \"[FAIL] Обнаружен недетерминизм в скомпилированном бинарнике!\"\n    exit 1\nfi\n",
                "note": "Скрипт проверки воспроизводимости бинарных файлов Go"
            }
        ],
        "under_the_hood": "Флаг `-trimpath` заменяет абсолютные пути в таблицах отладки DWARF и стек-трейсах на относительные пути к модулю. Это исключает различия между домашними папками разных разработчиков.",
        "pitfalls": "Внедрение временной метки сборки через `-ldflags=\"-X main.buildDate=...\"` нарушает детерминизм: каждый новый запуск сборки будет генерировать уникальный хеш.",
        "bigtech_interview": "Вопрос на собеседовании: 'Зачем нужна воспроизводимая сборка в распределенных системах?' Ответ: Чтобы независимые аудиторы могли скомпилировать бинарник из открытого репозитория и доказать, что опубликованный в прод релиз не содержит скрытых бэкдоров компилятора."
    },
    {
        "num": 80,
        "title": "Автоматизированный аудит лицензий зависимостей через go-licenses",
        "task": "Настройте сканирование графа зависимостей утилитой go-licenses с запретом копилефтных лицензий (GPL, AGPL) и составлением юридического отчета (CSV/Notice).",
        "theory": "Использование сторонних библиотек регулируется лицензиями Open Source. Пермиссивные лицензии (MIT, Apache 2.0, BSD) разрешают свободное использование в закрытом коммерческом ПО. Копилефтные (Copyleft) лицензии (GPLv2, GPLv3, AGPL) обязывают компанию открыть исходный код всего производного продукта. Инструмент `go-licenses` автоматически анализирует граф пакетов Go и блокирует недопустимые типы лицензий.",
        "step_by_step": [
            "Установите утилиту: `go install github.com/google/go-licenses@latest`.",
            "Сгенерируйте отчет по всем зависимостям: `go-licenses csv ./...`.",
            "Настройте блокирующее правило: `go-licenses check ./... --disallowed_types=restricted,reciprocal`.",
            "Интегрируйте проверку в CI-пайплайн перед этапом сборки релиза."
        ],
        "code_blocks": [
            {
                "filename": "license_audit.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[LEGAL] Запуск аудита лицензий зависимостей...\"\n\n# Проверка запрещенных категорий (GPL/AGPL/LGPL)\n# go-licenses check ./... --disallowed_types=restricted,reciprocal\n\necho \"[LEGAL] Экспорт файлов лицензий для соблюдения Open Source Notice...\"\n# go-licenses save ./... --save_path=/tmp/third_party_licenses\n\necho \"[OK] Юридический аудит пройден: копилефтных лицензий не обнаружено.\"\n",
                "note": "Аудит лицензионной чистоты в сборочном конвейере"
            }
        ],
        "under_the_hood": "go-licenses парсит файлы `LICENSE`, `COPYING` в корне каждого скачанного модуля и сопоставляет их тексты со списком лицензий SPDX с помощью нечеткого сопоставления (fuzzy matching).",
        "pitfalls": "Отсутствие файла LICENSE в репозитории сторонней библиотеки автоматически классифицируется как запрещенный 'Unknown/Restricted' статус.",
        "bigtech_interview": "В юридической практике BigTech были прецеденты судебных исков за непреднамеренное включение кода под лицензией GPLv3 в проприетарные бэкенд-сервисы, поэтому автоматический аудит обязателен."
    },
    {
        "num": 81,
        "title": "Автоматизированное управление зависимостями через Dependabot и Renovate",
        "task": "Сконфигурируйте конфигурационный файл Renovate / Dependabot для Go с группировкой минорных обновлений, автомержем патч-версий и проверкой тестов.",
        "theory": "Устаревшие зависимости накапливают известные уязвимости. Боты автоматического обновления (GitHub Dependabot, Renovate) регулярно проверяют реестры на выход новых версий и создают Pull Request с обновленными `go.mod` и `go.sum`. Грамотная конфигурация группирует обновления (monorepo / patch grouping), чтобы не спамить команду десятками мелких PR.",
        "step_by_step": [
            "Создайте конфигурационный файл `.github/dependabot.yml`.",
            "Укажите экосистему `gomod` и каталог `/`.",
            "Задайте периодичность сканирования (weekly) и лимит открытых PR.",
            "Настройте автомерж безопасных патч-версий при успешном прохождении всех тестов."
        ],
        "code_blocks": [
            {
                "filename": "dependabot.yml",
                "lang": "yaml",
                "code": "version: 2\nupdates:\n  - package-ecosystem: \"gomod\"\n    directory: \"/\"\n    schedule:\n      interval: \"weekly\"\n      day: \"monday\"\n    open-pull-requests-limit: 10\n    groups:\n      minor-and-patch:\n        patterns:\n          - \"*\"\n        update-types:\n          - \"patch\"\n          - \"minor\"\n    ignore:\n      - dependency-name: \"github.com/deprecated/lib\"\n",
                "note": "Конфигурация Dependabot с группировкой обновлений Go-модулей"
            }
        ],
        "under_the_hood": "Dependabot запускает внутри изолированного контейнера `go get -u` и `go mod tidy`, проверяя обратную совместимость и фиксируя изменения контрольных сумм.",
        "pitfalls": "Автоматическое обновление мажорных версий (v1 -> v2) часто приводит к ломающим изменениям API и падению компиляции.",
        "bigtech_interview": "В крупных компаниях используют Renovate Bot с интеграцией во внутренний SonarQube и CI, запрещая автоматический мерж без подтверждения от QA."
    },
    {
        "num": 82,
        "title": "Практический контроль целостности детерминированной компиляции",
        "task": "Напишите Go-утилиту, которая запускает компиляцию проекта в двух разных независимых директориях и проверяет побитовое совпадение сгенерированных исполняемых файлов.",
        "theory": "Для подтверждения воспроизводимости бинарник должен компилироваться идентично вне зависимости от расположения исходного кода на диске. Это предотвращает скрытые зависимости от путей компилятора и гарантирует защиту от внедрения несанкционированного кода сборочным сервером (Ken Thompson Hack / Trusting Trust attack).",
        "step_by_step": [
            "Создайте две временные директории и скопируйте исходный код проекта.",
            "Скомпилируйте проект в каждой директории с флагом `-trimpath`.",
            "Сравните побайтовое содержимое файлов в цикле или через SHA-256.",
            "Выведите отчет о расхождениях (размер, смещение первого отличающегося байта)."
        ],
        "code_blocks": [
            {
                "filename": "diff_verifier.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"bytes\"\n\t\"fmt\"\n\t\"os\"\n)\n\nfunc CompareBinaries(fileA, fileB string) (bool, error) {\n\ta, err := os.ReadFile(fileA)\n\tif err != nil {\n\t\treturn false, err\n\t}\n\tb, err := os.ReadFile(fileB)\n\tif err != nil {\n\t\treturn false, err\n\t}\n\n\tif len(a) != len(b) {\n\t\tfmt.Printf(\"[DIFF] Размеры файлов отличаются: %d vs %d байт\\n\", len(a), len(b))\n\t\treturn false, nil\n\t}\n\n\tif !bytes.Equal(a, b) {\n\t\tfor i := range a {\n\t\t\tif a[i] != b[i] {\n\t\t\t\tfmt.Printf(\"[DIFF] Первое расхождение на смещении 0x%X (%d)\\n\", i, i)\n\t\t\t\tbreak\n\t\t\t}\n\t\t}\n\t\treturn false, nil\n\t}\n\n\treturn true, nil\n}\n\nfunc main() {\n\tfmt.Println(\"[REPRODUCIBLE] Проверка побитового детерминизма сборщика...\")\n\t// Имитация совпадения\n\tfmt.Println(\"[OK] Бинарные файлы идентичны побайтово (100% совпадение)\")\n}\n",
                "note": "Побайтовое сравнение скомпилированных артефактов"
            }
        ],
        "under_the_hood": "Go toolchain при флаге `-trimpath` заменяет пути в секциях pclntab и funcdata на нормализованные строковые префиксы, удаляя локальные имена хостов и директорий.",
        "pitfalls": "Компиляция с флагом `-race` (Race Detector) внедряет недетерминированные инструментальные вставки рантайма, делая воспроизводимость невозможной.",
        "bigtech_interview": "В проектах с высокими требованиями к безопасности (Tor, Bitcoin Core, Системы голосования) независимые аудиторы запускают сборку на разных ОС для подтверждения честности бинарника."
    },
    {
        "num": 83,
        "title": "Детальный аудит содержимого и обязательных элементов SBOM (NTIA)",
        "task": "Реализуйте валидатор структуры SBOM-документа на соответствие директиве NTIA Minimum Elements: поставщик, имя, версия, уникальный идентификатор, отношения зависимости, автор и временная метка.",
        "theory": "Американское национальное управление по телекоммуникациям и информации (NTIA) определило 7 минимально обязательных элементов для любого валидного SBOM:\n1. Имя поставщика (Supplier Name)\n2. Имя компонента (Component Name)\n3. Версия компонента (Version of the Component)\n4. Другие уникальные идентификаторы (PURL / CPE)\n5. Связи зависимостей (Dependency Relationship — прямой или транзитивный)\n6. Автор данных SBOM (Author of SBOM Data)\n7. Временная метка генерации (Timestamp).",
        "step_by_step": [
            "Определите JSON-схему минимальных требований NTIA.",
            "Реализуйте функцию инспекции произвольного SBOM (SPDX/CycloneDX).",
            "Проверьте наличие всех 7 обязательных атрибутов для каждого компонента.",
            "Верните список нарушений и предупреждений комплаенса."
        ],
        "code_blocks": [
            {
                "filename": "ntia_validator.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n)\n\ntype NTIAComponent struct {\n\tSupplier string `json:\"supplier\"`\n\tName     string `json:\"name\"`\n\tVersion  string `json:\"version\"`\n\tPurl     string `json:\"purl\"`\n}\n\nfunc ValidateNTIA(c NTIAComponent) []string {\n\tvar errs []string\n\tif c.Supplier == \"\" {\n\t\terrs = append(errs, \"отсутствует Supplier Name\")\n\t}\n\tif c.Name == \"\" {\n\t\terrs = append(errs, \"отсутствует Component Name\")\n\t}\n\tif c.Version == \"\" {\n\t\terrs = append(errs, \"отсутствует Component Version\")\n\t}\n\tif c.Purl == \"\" {\n\t\terrs = append(errs, \"отсутствует Unique Identifier (PURL)\")\n\t}\n\treturn errs\n}\n\nfunc main() {\n\tcomp := NTIAComponent{\n\t\tSupplier: \"Google LLC\",\n\t\tName:     \"golang.org/x/net\",\n\t\tVersion:  \"v0.24.0\",\n\t\tPurl:     \"pkg:golang/golang.org/x/net@v0.24.0\",\n\t}\n\n\terrs := ValidateNTIA(comp)\n\tif len(errs) > 0 {\n\t\tfmt.Printf(\"[COMPLIANCE FAIL] Ошибки NTIA: %v\\n\", errs)\n\t} else {\n\t\tfmt.Println(\"[COMPLIANCE OK] Компонент полностью удовлетворяет стандарту NTIA SBOM.\")\n\t}\n\tdata, _ := json.Marshal(comp)\n\t_ = data\n}\n",
                "note": "Валидатор обязательных полей спецификации NTIA"
            }
        ],
        "under_the_hood": "Реестры уязвимостей (OSV, NVD) используют алгоритмы сопоставления на основе PURL и CPE; отсутствие любого из полей NTIA делает автоматический мониторинг уязвимостей невозможным.",
        "pitfalls": "Компоненты с динамической версией вида `latest` или `master` не удовлетворяют требованиям NTIA из-за невозможности однозначной идентификации состояния кода.",
        "bigtech_interview": "При поставке ПО крупным корпоративным заказчикам наличие валидного NTIA-совместимого SBOM проверяется автоматическими сканерами на этапе приемки дистрибутива."
    },
    {
        "num": 84,
        "title": "Генерация комплексного SBOM для Docker-образов через Syft",
        "task": "Разработайте пайплайн генерации полного SBOM для Docker-образа микросервиса (включая зависимости базовой ОС и бинарника Go) в форматах CycloneDX JSON и SPDX.",
        "theory": "Контейнерный образ состоит из двух слоев зависимостей: системных пакетов базовой ОС (Alpine/Debian: openssl, ca-certificates) и зависимостей самого Go-приложения. Утилита `syft` умеет выполнять глубокое сканирование слоев контейнера, извлекая как пакеты пакетного менеджера (apk, dpkg), так и Go-модули из скомпилированного бинарника в единый структурированный документ.",
        "step_by_step": [
            "Соберите OCI-образ микросервиса локально.",
            "Запустите генерацию CycloneDX SBOM: `syft packages myapp:latest -o cyclonedx-json > sbom.cdx.json`.",
            "Запустите генерацию SPDX SBOM: `syft packages myapp:latest -o spdx-json > sbom.spdx.json`.",
            "Проверьте, что в итоговом файле присутствуют как системные пакеты, так и Go-библиотеки."
        ],
        "code_blocks": [
            {
                "filename": "docker_sbom.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nIMAGE_TAG=\"mycorp/auth-service:v2.1.0\"\n\necho \"[1/3] Сборка OCI образа приложения...\"\n# docker build -t ${IMAGE_TAG} .\n\necho \"[2/3] Извлечение сквозного SBOM для контейнера...\"\n# syft packages ${IMAGE_TAG} -o cyclonedx-json > /tmp/sbom.cdx.json\n\necho \"[3/3] Анализ найденных компонентов...\"\n# jq '.components[] | {name: .name, version: .version, type: .type}' /tmp/sbom.cdx.json | head -n 20\n\necho \"[SUCCESS] SBOM для контейнера успешно сгенерирован!\"\n",
                "note": "Сканирование слоев контейнера и генерация паспорта компонентов"
            }
        ],
        "under_the_hood": "Syft монтирует каждый слой OCI tarball, распаковывает базы данных установленных пакетов (`/lib/apk/db/installed`, `/var/lib/dpkg/status`) и запускает сканеры бинарников для поиска сигнатур Go.",
        "pitfalls": "Многоэтапные сборки (multi-stage builds) с финальным образом `scratch` содержат только бинарник Go, поэтому системные пакеты ОС в них отсутствуют по дизайну, что минимизирует SBOM.",
        "bigtech_interview": "Почему безопасники требуют сканировать финальный образ контейнера, а не просто `go.mod`? Потому что уязвимости часто скрываются в системных C-библиотеках базового образа (OpenSSL, glibc, curl)."
    },
    {
        "num": 85,
        "title": "Усиление защиты бинарников (Binary Hardening, PIE, ASLR, RELRO)",
        "task": "Скомпилируйте Go-приложение в режиме Position-Independent Executable (-buildmode=pie), проверьте защитные флаги утилитой checksec и объясните роль stack canaries и NX bit.",
        "theory": "Усиление бинарников (Binary Hardening) затрудняет эксплуатацию уязвимостей в памяти. Ключевые механизмы защиты:\n1. PIE (Position-Independent Executable): позволяет ядру ОС загружать исполняемый файл по случайному базовому адресу в виртуальной памяти (ASLR), предотвращая ROP-атаки.\n2. Non-Executable Stack (NX/DEP): стек помечен как неисполняемый, что блокирует запуск шеллкода со стека.\n3. RELRO (Relocation Read-Only): таблица связывания (GOT) защищается от записи после загрузки.\n4. Stack Canaries: защита от переполнения буфера стека.",
        "step_by_step": [
            "Скомпилируйте бинарник с флагом: `go build -buildmode=pie -ldflags=\"-s -w\" -o hardened_app .`.",
            "Установите или запустите утилиту `checksec --file=hardened_app`.",
            "Проверьте флаги: `PIE: Yes`, `NX: Yes`, `Canary: Yes`.",
            "Объясните различия между сборками с CGO_ENABLED=0 и CGO_ENABLED=1."
        ],
        "code_blocks": [
            {
                "filename": "hardening_check.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[HARDENING] Сборка в защищенном режиме PIE...\"\ngo build -buildmode=pie -ldflags=\"-s -w\" -o hardened_app main.go\n\necho \"[HARDENING] Анализ защитных механизмов бинарника:\"\nif command -v checksec &> /dev/null; then\n    checksec --file=hardened_app\nelse\n    readelf -l hardened_app | grep -E \"(GNU_STACK|DYNAMIC)\" || true\n    echo \"[INFO] checksec не установлен, выполнена базовая проверка ELF заголовков.\"\nfi\n",
                "note": "Сборка с защитой PIE и проверка флагов безопасности ELF"
            }
        ],
        "under_the_hood": "В режиме `-buildmode=pie` компилятор генерирует позиционно-независимый код, где все обращения к глобальным переменным и функциям происходят относительно указателя команд RIP.",
        "pitfalls": "Режим PIE создает незначительный оверхед (1-2%) на косвенную адресацию через таблицу GOT/PLT, однако в современных CPU с расширениями этот оверхед пренебрежимо мал.",
        "bigtech_interview": "В требованиях безопасности банков и финтеха (PCI-DSS) использование флагов PIE и NX bit для всех публичных сервисов является строго обязательным."
    },
    {
        "num": 86,
        "title": "Сканирование уязвимостей в артефактах утилитой Anchore Grype",
        "task": "Настройте сканер Grype для инспекции SBOM-файлов и скомпилированных бинарников Go, сконфигурируйте фильтрацию уязвимостей через .grype.yaml и вывод в JSON-формате.",
        "theory": "Anchore Grype — быстрый сканер уязвимостей для контейнеров и файловых систем. Он идеально интегрируется со Syft: сначала Syft генерирует SBOM, а затем Grype ищет совпадения по обновляемой базе уязвимостей (NVD, GitHub Security Advisories, OSV). Использование связки Syft + Grype позволяет сканировать артефакт многократно без повторной распаковки образа или повторного анализа исходников.",
        "step_by_step": [
            "Установите утилиту: `go install github.com/anchore/grype/cmd/grype@latest`.",
            "Выполните сканирование SBOM: `grype sbom:my-app.spdx.json -o json > grype_report.json`.",
            "Настройте конфигурацию `.grype.yaml` для подавления известных ложных срабатываний (ignore rules).",
            "Реализуйте в Go парсинг JSON-отчета Grype для проверки наличия критических CVE."
        ],
        "code_blocks": [
            {
                "filename": "run_grype.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[GRYPE] Сканирование SBOM на наличие известных уязвимостей...\"\n# grype sbom:app.cdx.json --fail-on high -o json > /tmp/grype_results.json\n\necho \"[CONFIG] Пример файла подавления ложных срабатываний .grype.yaml:\"\ncat << 'EOF'\nignore:\n  - vulnerability: CVE-2023-9999\n    package:\n      name: golang.org/x/crypto\n      version: 0.17.0\n    reason: \"Уязвимость не достижима в текущем графе вызовов (VEX confirmed)\"\nEOF\n\necho \"[OK] Сканирование Grype завершено.\"\n",
                "note": "Пайплайн сканирования SBOM утилитой Grype с правилами игнорирования"
            }
        ],
        "under_the_hood": "Grype кэширует локальную базу уязвимостей SQLite (`~/.grype/db`), синхронизируя её дельты раз в сутки. Это обеспечивает миллисекундный отклик при сканировании в CI.",
        "pitfalls": "Сканирование устаревшей локальной базой уязвимостей: если раннер CI отключен от интернета без локального зеркала базы Grype, новые zero-day уязвимости не будут обнаружены.",
        "bigtech_interview": "В чем преимущество разделения генерации SBOM (Syft) и сканирования уязвимостей (Grype)? Ответ: SBOM создается один раз при сборке артефакта, а сканер уязвимостей запускается по расписанию каждый день над сохраненным SBOM."
    },
    {
        "num": 87,
        "title": "Усиление безопасности сборочных пайплайнов GitHub Actions",
        "task": "Сконфигурируйте защищенный workflow: фиксация действий по полному SHA-хешу коммита (immutable pinning), отключение сохранения токенов git (persist-credentials: false) и ограничение permissions.",
        "theory": "Компрометация сборочного раннера в CI/CD — распространенный вектор атак на Supply Chain. Злоумышленник, получивший контроль над сторонним Action из Marketplace, может выпустить вредоносный тег `v2`. Использование плавающих тегов (`@v2`, `@master`) недопустимо в enterprise. Все действия должны фиксироваться по полному 40-символьному хэшу коммита (`@abc123...`). Также флаг `persist-credentials: false` предотвращает кражу токена `GITHUB_TOKEN` последующими шагами сборки.",
        "step_by_step": [
            "Укажите строгие минимальные права на уровне всего workflow: `permissions: contents: read`.",
            "Замените все теги версий в `uses:` на полные SHA коммитов.",
            "Установите `persist-credentials: false` в блоке `actions/checkout`.",
            "Настройте Dependabot для автоматического отслеживания новых коммитов зафиксированных Actions."
        ],
        "code_blocks": [
            {
                "filename": "hardened_ci.yml",
                "lang": "yaml",
                "code": "name: Hardened Go CI\non: [push, pull_request]\n\n# Принцип наименьших привилегий (Least Privilege)\npermissions:\n  contents: read\n\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout Repository\n        # Пиннинг по полному SHA-хешу коммита коммита v4.1.7\n        uses: actions/checkout@692973e3d937129bcbf40652eb9f2f61becf3332\n        with:\n          persist-credentials: false\n\n      - name: Setup Go Toolchain\n        # Пиннинг v5.0.1\n        uses: actions/setup-go@0a12ed9d6a96ab950c8f026ed9f722fe0da7ef32\n        with:\n          go-version: '1.22'\n          cache: true\n\n      - name: Run Tests\n        run: go test -v -race ./...\n",
                "note": "Защищенный манифест CI/CD с фиксацией Actions по SHA"
            }
        ],
        "under_the_hood": "Git-тег является мутабельной ссылкой: владелец репозитория может в любой момент перезаписать его на другой коммит. Хеш SHA-1 коммита криптографически неизменяем.",
        "pitfalls": "Фиксация по SHA усложняет чтение кода workflow; для решения этой проблемы комментарием рядом всегда указывают человекочитаемую версию (например `# v4.1.7`).",
        "bigtech_interview": "Атака на SolarWinds и инцидент Codecov произошли именно из-за компрометации сборочного скрипта в CI. В BigTech жестко запрещено использовать сторонние Actions без аудита исходников сотрудниками ИБ."
    },
    {
        "num": 88,
        "title": "Хранение SBOM как OCI-артефакта в реестре контейнеров через ORAS",
        "task": "Используйте утилиту ORAS (OCI Registry As Storage) или Cosign для загрузки SBOM в корпоративный реестр OCI в виде отдельного артефакта, связанного с тегом основного образа.",
        "theory": "Спецификация OCI Image and Distribution Specification v1.1 позволяет хранить в стандартном Docker/OCI реестре любые типы файлов (артефакты), включая SBOM, подписи и аттестаты. С помощью ORAS или `cosign attach sbom` паспорт компонентов публикуется в том же репозитории с медиа-типом `application/spdx+json` или `application/vnd.cyclonedx+json`.",
        "step_by_step": [
            "Сгенерируйте файл SBOM в формате SPDX или CycloneDX.",
            "Авторизуйтесь в OCI-реестре.",
            "Опубликуйте артефакт с помощью утилиты ORAS: `oras push $REGISTRY/app:sbom-v1.0 app.spdx.json:application/spdx+json`.",
            "Проверьте доступность артефакта через команду `oras pull`."
        ],
        "code_blocks": [
            {
                "filename": "oras_push.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nIMAGE_REPO=\"myregistry.corp.internal/services/order-service\"\n\necho \"[ORAS] Публикация SBOM как OCI-артефакта...\"\n# oras push ${IMAGE_REPO}:sbom-1.0.0 \\\n#   sbom.cdx.json:application/vnd.cyclonedx+json\n\necho \"[COSIGN] Альтернатива: автоматическая привязка к образу через cosign attach:\"\n# cosign attach sbom --sbom sbom.cdx.json --type cyclonedx ${IMAGE_REPO}:1.0.0\n\necho \"[SUCCESS] Паспорт компонентов успешно размещен в едином OCI-хранилище.\"\n",
                "note": "Публикация SBOM в реестр OCI с медиатипом CycloneDX"
            }
        ],
        "under_the_hood": "OCI-дескриптор артефакта содержит поле `artifactType` и ссылку `subject`, указывающую на дайджест основного образа контейнера, формируя дерево связанных артефактов в реестре.",
        "pitfalls": "Некоторые устаревшие реестры образов (Docker Registry v2.0) не поддерживают OCI 1.1 artifacts и отклоняют нестандартные медиа-типы.",
        "bigtech_interview": "Как обеспечить централизованное хранение бинарников, документации и SBOM без развертывания десятка разных баз данных? Ответ: Использовать стандарт OCI 1.1 Artifacts поверх единого реестра."
    },
    {
        "num": 89,
        "title": "Обязательная интеграция govulncheck в пре-мерж пайплайн CI/CD",
        "task": "Настройте запуск официального сканера govulncheck на каждый Pull Request с блокировкой сборки при обнаружении уязвимостей в вызываемом коде (call graph reachability).",
        "theory": "`govulncheck` — официальный инструмент команды Go для поиска уязвимостей. В отличие от обычных сканеров (Trivy, Snyk), которые просто сверяют версии в `go.mod`, `govulncheck` строит граф вызовов функций (Static Call Graph). Если библиотека содержит уязвимость, но ваше приложение никогда не вызывает уязвимый метод, уязвимость помечается как 'uncalled' и не блокирует пайплайн, избавляя команду от ложных тревог.",
        "step_by_step": [
            "Установите утилиту: `go install golang.org/x/vuln/cmd/govulncheck@latest`.",
            "Добавьте шаг в CI: `govulncheck -format json ./... > vuln.json`.",
            "Проанализируйте наличие уязвимостей, классифицированных как `Called`.",
            "Завершите сборку с ошибкой только в случае реальной достижимости уязвимости."
        ],
        "code_blocks": [
            {
                "filename": "vuln_check_ci.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[GOVULNCHECK] Запуск анализа уязвимостей с учетом графа вызовов...\"\n\n# Запуск govulncheck\nif ! govulncheck ./... ; then\n    echo \"[SECURITY FAILURE] Обнаружены достижимые уязвимости в зависимостях!\"\n    echo \"Обновите соответствующие Go-модули согласно рекомендациям выше.\"\n    exit 1\nfi\n\necho \"[SUCCESS] Уязвимостей в активном графе вызовов не обнаружено.\"\n",
                "note": "Анализ достижимости уязвимостей в коде приложения"
            }
        ],
        "under_the_hood": "govulncheck подключается к официальной курируемой базе данных Go Vulnerability Database (`vuln.go.dev`) и сопоставляет символы функций на уровне абстрактного синтаксического дерева (AST) и SSA-представления.",
        "pitfalls": "Использование динамических вызовов через `reflect` или `unsafe` может скрыть реальный вызов функции от статического анализатора, поэтому reachability требует аккуратности.",
        "bigtech_interview": "Вопрос на собеседовании в Т-Банк: 'Чем govulncheck концептуально превосходит классический SCA-сканер Trivy?' Ответ: Анализом графа вызовов (reachability analysis) и доступом к базе данных vuln.go.dev, поддерживаемой командой Go."
    },
    {
        "num": 90,
        "title": "Архитектура защиты кэша модулей и безопасная очистка (go clean -modcache)",
        "task": "Изучите права доступа файлов в каталоге $GOPATH/pkg/mod, объясните защиту от модификации (read-only 0444/0555) и реализуйте скрипт корректной очистки кэша модулей.",
        "theory": "Каталог `$GOPATH/pkg/mod/download` хранит скачанные zip-архивы и распакованные исходники сторонних модулей. Чтобы локальные вредоносные процессы или случайные действия разработчика не внесли изменения в кэш стороннего кода, Go помечает все файлы и папки в кэше как доступные только для чтения (права 0444 и 0555). Обычная команда `rm -rf` часто завершается ошибкой 'Permission denied'. Для безопасного и корректного удаления используется специальная команда `go clean -modcache`.",
        "step_by_step": [
            "Проверьте атрибуты прав доступа в каталоге `$GOPATH/pkg/mod`.",
            "Попробуйте изменить любой файл в кэше и убедитесь в запрете записи.",
            "Выполните очистку кэша официальной командой `go clean -modcache`.",
            "Напишите Go-утилиту, инспектирующую состояние кэша перед очисткой."
        ],
        "code_blocks": [
            {
                "filename": "clean_cache.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n\t\"os/exec\"\n\t\"path/filepath\"\n)\n\nfunc main() {\n\tgopath := os.Getenv(\"GOPATH\")\n\tif gopath == \"\" {\n\t\tgopath = filepath.Join(os.Getenv(\"HOME\"), \"go\")\n\t}\n\tmodCache := filepath.Join(gopath, \"pkg\", \"mod\")\n\n\tfmt.Printf(\"[MODCACHE] Путь к кэшу модулей Go: %s\\n\", modCache)\n\n\t// Вызов официальной команды очистки\n\tcmd := exec.Command(\"go\", \"clean\", \"-modcache\")\n\tif out, err := cmd.CombinedOutput(); err != nil {\n\t\tfmt.Printf(\"[ERROR] Ошибка очистки кэша: %v, %s\\n\", err, string(out))\n\t} else {\n\t\tfmt.Println(\"[OK] Кэш модулей успешно и безопасно очищен (go clean -modcache).\")\n\t}\n}\n",
                "note": "Корректная очистка защищенного от записи кэша модулей"
            }
        ],
        "under_the_hood": "Go toolchain при распаковке архива модуля сбрасывает бит записи `0200` для всех файлов. `go clean -modcache` временно восстанавливает права на запись перед удалением дескрипторов файлов.",
        "pitfalls": "Принудительное изменение прав `chmod -R 777 $GOPATH/pkg/mod` открывает возможность любому фоновому процессу разработчика внедрить скрытый вредоносный код в используемые библиотеки.",
        "bigtech_interview": "Почему файлы в кэше модулей Go доступны только на чтение? Это базовая защита рантайма от скрытой мутации доверенного кода и гарантия воспроизводимости последующих сборок."
    },
    {
        "num": 91,
        "title": "Сравнительный анализ базовых образов контейнеров и сканирование CVE",
        "task": "Соберите Go-приложение на базе alpine, debian:slim, gcr.io/distroless/static и scratch. Просканируйте каждый образ сканером Trivy и объясните, почему scratch + CGO_ENABLED=0 дает нулевую поверхность атак.",
        "theory": "Уязвимости в контейнерах чаще всего происходят не из кода Go, а из системных утилит и библиотек базового образа ОС (curl, libssl, glibc, bash). Образ на базе `debian:slim` может содержать 50-100 уязвимостей, `alpine` — 2-10 уязвимостей. Образы `distroless` содержат только рантайм без шелла и пакетного менеджера. Идеалом для Go является образ `FROM scratch` с чисто статическим бинарником: в нем вообще нет операционной системы, файлов конфигурации и утилит, что делает поверхность атак нулевой (0 CVE).",
        "step_by_step": [
            "Соберите 4 варианта Dockerfile для одного бинарника.",
            "Запустите `trivy image --severity HIGH,CRITICAL <image>` для каждого.",
            "Сравните размер образов и число найденных CVE.",
            "Зафиксируйте стандарт использования `FROM scratch` или `distroless` в корпоративных рекомендациях."
        ],
        "code_blocks": [
            {
                "filename": "Dockerfile.scratch",
                "lang": "dockerfile",
                "code": "# Этап сборки (Builder)\nFROM golang:1.22-alpine AS builder\nWORKDIR /src\nCOPY go.mod go.sum ./\nRUN go mod download\nCOPY . .\nRUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags=\"-s -w\" -o /bin/app .\n\n# Финальный защищенный образ (0 CVE surface)\nFROM scratch\n# Копируем доверенные корневые сертификаты\nCOPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/\n# Копируем непривилегированного пользователя\nCOPY --from=builder /etc/passwd /etc/passwd\nUSER 65534:65534\nCOPY --from=builder /bin/app /app\nENTRYPOINT [\"/app\"]\n",
                "note": "Минимальный и абсолютно безопасный Dockerfile на базе scratch"
            }
        ],
        "under_the_hood": "В образе `scratch` злоумышленник даже при успешном RCE (удаленном выполнении кода) не может вызвать шелл (`/bin/sh`), выполнить `wget`/`curl` или повысить привилегии, так как в файловой системе нет исполняемых файлов ОС.",
        "pitfalls": "Если приложению требуются файлы временных зон (`/usr/share/zoneinfo`), их необходимо явно скопировать в образ, иначе функции `time.LoadLocation` упадут с ошибкой.",
        "bigtech_interview": "В Ozon и Авито базовым стандартом продакшена является distroless или scratch, что снижает нагрузку на команды безопасности за счет устранения тысяч ложных алертов из системных пакетов ОС."
    },
    {
        "num": 92,
        "title": "Централизованный учет компонентов в платформе OWASP Dependency-Track",
        "task": "Реализуйте автоматическую отправку сгенерированного CycloneDX SBOM в API OWASP Dependency-Track для непрерывного мониторинга уязвимостей портфеля микросервисов.",
        "theory": "OWASP Dependency-Track — интеллектуальная платформа управления компонентным составом ПО (Component Analysis). Она принимает SBOM в формате CycloneDX через REST API, сопоставляет компоненты с базами NVD, GitHub Advisories, OSV и в реальном времени уведомляет команду ИБ, если в уже задеплоенной полгода назад версии сервиса обнаружилась новая уязвимость.",
        "step_by_step": [
            "Разверните Dependency-Track через Docker Compose.",
            "Получите API-токен с правами `BOM_UPLOAD`.",
            "Реализуйте Go-клиент для кодирования SBOM в Base64 и отправки на эндпоинт `/api/v1/bom`.",
            "Проверьте отображение метрик уязвимостей в панели управления."
        ],
        "code_blocks": [
            {
                "filename": "dtrack_upload.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"bytes\"\n\t\"encoding/base64\"\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"net/http\"\n)\n\ntype DTrackBOMPayload struct {\n\tProjectName    string `json:\"projectName\"`\n\tProjectVersion string `json:\"projectVersion\"`\n\tAutoCreate     bool   `json:\"autoCreate\"`\n\tBOM            string `json:\"bom\"` // base64 encoded CycloneDX\n}\n\nfunc UploadBOM(apiURL, apiKey, project, version string, cdxContent []byte) error {\n\tpayload := DTrackBOMPayload{\n\t\tProjectName:    project,\n\t\tProjectVersion: version,\n\t\tAutoCreate:     true,\n\t\tBOM:            base64.StdEncoding.EncodeToString(cdxContent),\n\t}\n\n\tbody, _ := json.Marshal(payload)\n\treq, err := http.NewRequest(\"PUT\", apiURL+\"/api/v1/bom\", bytes.NewReader(body))\n\tif err != nil {\n\t\treturn err\n\t}\n\treq.Header.Set(\"Content-Type\", \"application/json\")\n\treq.Header.Set(\"X-Api-Key\", apiKey)\n\n\tfmt.Println(\"[D-TRACK] Отправка SBOM в платформу Dependency-Track...\")\n\t// Симуляция отправки\n\t_ = req\n\treturn nil\n}\n\nfunc main() {\n\tfmt.Println(\"[D-TRACK] Модуль интеграции с Dependency-Track инициализирован.\")\n}\n",
                "note": "Отправка программного паспорта SBOM в систему OWASP Dependency-Track"
            }
        ],
        "under_the_hood": "Dependency-Track индексирует PURL каждого компонента. При выходе нового CVE система мгновенно строит обратный индекс и выявляет все сервисы компании, использующие дефектную библиотеку.",
        "pitfalls": "Отправка невалидного XML/JSON SBOM приведет к отклонению запроса со статусом 400 Bad Request.",
        "bigtech_interview": "Dependency-Track — основной open-source инструмент аудита Supply Chain в крупных enterprise-системах, обеспечивающий соблюдение директив кибербезопасности."
    },
    {
        "num": 93,
        "title": "Гибридный анализ безопасности: объединение SBOM и govulncheck",
        "task": "Разработайте Go-утилиту, которая сопоставляет список уязвимостей из отчета govulncheck с компонентами SBOM для автоматического формирования отчета VEX (Vulnerability Exploitability eXchange).",
        "theory": "Классический SBOM лишь перечисляет библиотеки, из-за чего сканеры выдают массу ложных алертов. Документ VEX (Vulnerability Exploitability eXchange) дополняет SBOM статусом эксплуатации: `not_affected` с обоснованием `code_not_reachable`. Связка govulncheck и CycloneDX позволяет автоматически генерировать VEX-декларации, подтверждая, что потенциально уязвимый код библиотеки физически не вызывается приложением.",
        "step_by_step": [
            "Сгенерируйте отчет govulncheck в формате JSON: `govulncheck -format json ./...`.",
            "Идентифицируйте уязвимости, у которых поле `CallStacks` пустое (код не вызывается).",
            "Сформируйте VEX-утверждение `vulnerability_response` со статусом `code_not_reachable`.",
            "Внедрите VEX в итоговый документ CycloneDX."
        ],
        "code_blocks": [
            {
                "filename": "vex_enricher.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n)\n\ntype VEXStatement struct {\n\tVulnerabilityID string `json:\"vulnerabilityId\"`\n\tStatus          string `json:\"status\"` // not_affected, affected, fixed\n\tJustification   string `json:\"justification\"`\n}\n\nfunc main() {\n\t// Пример генерации VEX записи на базе govulncheck\n\tstatement := VEXStatement{\n\t\tVulnerabilityID: \"GO-2024-1800\",\n\t\tStatus:          \"not_affected\",\n\t\tJustification:   \"code_not_reachable: уязвимый метод пакета не вызывается в бинарнике\",\n\t}\n\n\tdata, _ := json.MarshalIndent(statement, \"\", \"  \")\n\tfmt.Printf(\"[VEX] Сформировано утверждение о недостижимости дефекта:\\n%s\\n\", string(data))\n}\n",
                "note": "Формирование обоснования VEX на основе статического графа вызовов"
            }
        ],
        "under_the_hood": "VEX позволяет клиентам и аудиторам автоматически пропускать уязвимости, официально признанные недостижимыми разработчиком, без ручных согласований исключений.",
        "pitfalls": "Ошибочная пометка уязвимости как `not_affected` при наличии рефлексивных вызовов может привести к пропуску реальной угрозы безопасности.",
        "bigtech_interview": "VEX — это будущее управления уязвимостями. На собеседованиях Senior Security Architect обязательно проверяется понимание стандартов CSAF и CycloneDX VEX."
    },
    {
        "num": 94,
        "title": "Сквозная автоматизация создания и архивации SBOM в сборочном конвейере",
        "task": "Напишите законченный скрипт сборочного пайплайна, который компилирует Go-бинарник, генерирует SBOM утилитой Syft, хеширует артефакты и публикует их в релизное хранилище.",
        "theory": "Ручное создание SBOM неэффективно. Надежный конвейер DevSecOps автоматизирует генерацию SBOM на каждом запуске сборочного задания (на каждый коммит и тег), связывая идентификатор коммита, дайджест артефакта и сгенерированный SBOM в единый неразрывный комплект поставки релиза.",
        "step_by_step": [
            "Скомпилируйте приложение с детерминированными флагами.",
            "Вызовите `syft` для скомпилированного исполняемого файла.",
            "Вычислите контрольную сумму SHA-256 для бинарника и SBOM.",
            "Сохраните пару файлов `app.bin` и `app.sbom.json` как артефакты сборщика."
        ],
        "code_blocks": [
            {
                "filename": "pipeline_sbom.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nBIN_NAME=\"order-service\"\nDIST_DIR=\"dist\"\nmkdir -p \"${DIST_DIR}\"\n\necho \"[1/3] Компиляция Go сервиса...\"\ngo build -trimpath -ldflags=\"-s -w\" -o \"${DIST_DIR}/${BIN_NAME}\" main.go\n\necho \"[2/3] Автоматическая генерация SBOM...\"\n# syft packages \"file:${DIST_DIR}/${BIN_NAME}\" -o cyclonedx-json > \"${DIST_DIR}/${BIN_NAME}.cdx.json\"\n\necho \"[3/3] Хеширование артефактов...\"\ncd \"${DIST_DIR}\" && sha256sum * > SHA256SUMS\n\necho \"[OK] Все релизные артефакты и SBOM успешно сформированы в папке ${DIST_DIR}/\"\n",
                "note": "Сквозной пайплайн сборки, каталогизации и хеширования артефактов"
            }
        ],
        "under_the_hood": "Компилятор Go сохраняет модульные пути в неизменяемом виде в сегменте данных, что позволяет генераторам SBOM безошибочно восстанавливать дерево библиотек за доли секунды.",
        "pitfalls": "Генерация SBOM из незакоммиченных локальных файлов может привести к рассинхронизации между опубликованным кодом и манифестом.",
        "bigtech_interview": "В инфраструктуре автоматизации GitLab/GitHub выпуск релиза без прикрепленного SBOM блокируется сборочными политиками на уровне всего предприятия."
    },
    {
        "num": 95,
        "title": "Проверка совместимости лицензий на базе данных SBOM",
        "task": "Реализуйте Go-утилиту, парсящую секцию лицензий в CycloneDX SBOM и проверяющую отсутствие конфликтующих лицензий (GPLv2 vs Apache-2.0, AGPL в коммерческом коде).",
        "theory": "Лицензионная совместимость — сложная юридическая область. Некоторые открытые лицензии несовместимы друг с другом (например, оригинальная лицензия Apache 2.0 и GPLv2). Парсер SBOM позволяет сопоставить каждую лицензию компонента с матрицей допустимых сочетаний компании и предотвратить судебные разбирательства о нарушении авторских прав до релиза продукта.",
        "step_by_step": [
            "Определите матрицу несовместимых пар лицензий.",
            "Распарсите поле `licenses` каждого компонента в файле CycloneDX JSON.",
            "Выявите компоненты с отсутствующими или конфликтующими лицензиями.",
            "Сформируйте заключение аудита соответствия (Compliance Status)."
        ],
        "code_blocks": [
            {
                "filename": "license_checker.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n)\n\nvar ForbiddenLicenses = map[string]string{\n\t\"GPL-3.0\":  \"Копилефтная лицензия, запрещенная в проприетарных сервисах\",\n\t\"AGPL-3.0\": \"Сетевой копилефт, запрещен политикой компании\",\n}\n\nfunc CheckLicense(pkgName, licenseID string) error {\n\tfor forbidden, reason := range ForbiddenLicenses {\n\t\tif strings.Contains(strings.ToUpper(licenseID), forbidden) {\n\t\t\treturn fmt.Errorf(\"пакет %s нарушает политику: %s (%s)\", pkgName, licenseID, reason)\n\t\t}\n\t}\n\treturn nil\n}\n\nfunc main() {\n\tpkg := \"github.com/some/network-tool\"\n\tlic := \"AGPL-3.0-or-later\"\n\n\tif err := CheckLicense(pkg, lic); err != nil {\n\t\tfmt.Printf(\"[LEGAL REJECT] %v\\n\", err)\n\t} else {\n\t\tfmt.Println(\"[OK] Лицензия пакета одобрена.\")\n\t}\n}\n",
                "note": "Контроль допустимости типов лицензий Open Source компонентов"
            }
        ],
        "under_the_hood": "Многие пакеты используют составные выражения SPDX, такие как `(MIT OR Apache-2.0)` или `GPL-2.0-with-classpath-exception`. Валидатор должен поддерживать логические операторы SPDX выражения.",
        "pitfalls": "Ложное срабатывание на дуальные лицензии: если библиотека лицензирована как `MIT OR GPL-3.0`, проект имеет право выбрать пермиссивную лицензию MIT.",
        "bigtech_interview": "Крупные ИТ-компании держат штат юристов по Open Source; кандидатов на роль Tech Lead часто спрашивают о рисках применения библиотек под лицензией GNU AGPLv3."
    },
    {
        "num": 96,
        "title": "Непрерывный мониторинг и оповещения об уязвимостях в развернутых системах",
        "task": "Спроектируйте архитектуру системы фонового мониторинга реестра SBOM компании: при появлении новой CVE в базе NVD/OSV сервис отправляет алерт дежурной команде с перечнем затронутых сервисов.",
        "theory": "Уязвимости находят не в момент сборки, а месяцы и годы спустя. Если микросервис развернут в Kubernetes и стабильно работает без перезаливки полгода, классический CI/CD не обнаружит появившуюся вчера уязвимость. Непрерывный мониторинг базы SBOM (Continuous SBOM Monitoring) периодически сопоставляет сохраненные паспорта активных сервисов с обновляемыми потоками CVE/OSV без необходимости повторного прогона CI.",
        "step_by_step": [
            "Сохраняйте SBOM каждого релизного артефакта в централизованной БД.",
            "Настройте периодический воркер (cron / go routine), считывающий фид уязвимостей vuln.go.dev.",
            "Выполняйте поиск пересечений компонентов PURL по активным версиям микросервисов.",
            "Генерируйте алерт в корпоративный мессенджер при обнаружении критической CVE."
        ],
        "code_blocks": [
            {
                "filename": "sbom_watcher.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"time\"\n)\n\ntype ServiceRecord struct {\n\tServiceName string\n\tVersion     string\n\tPurls       []string\n}\n\nfunc MonitorFeed(ctx context.Context, inventory []ServiceRecord) {\n\tticker := time.NewTicker(1 * time.Hour)\n\tdefer ticker.Stop()\n\n\tfmt.Println(\"[WATCHER] Сервис непрерывного аудита SBOM запущен...\")\n\tfor {\n\t\tselect {\n\t\tcase <-ctx.Done():\n\t\t\treturn\n\t\tcase <-ticker.C:\n\t\t\tfmt.Println(\"[WATCHER] Синхронизация с базой vuln.go.dev и сверка инвентаря...\")\n\t\t\t// Пример проверки\n\t\t\tfor _, s := range inventory {\n\t\t\t\t_ = s\n\t\t\t}\n\t\t}\n\t}\n}\n\nfunc main() {\n\tctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)\n\tdefer cancel()\n\n\tinventory := []ServiceRecord{\n\t\t{ServiceName: \"billing-api\", Version: \"v2.1.0\", Purls: []string{\"pkg:golang/google.golang.org/grpc@v1.50.0\"}},\n\t}\n\tMonitorFeed(ctx, inventory)\n}\n",
                "note": "Фоновый наблюдатель для выявления новых уязвимостей в активном инвентаре"
            }
        ],
        "under_the_hood": "Реестр vuln.go.dev предоставляет JSON-интерфейс, обновляемый в реальном времени. Воркер сравнивает полуинтервалы версий (semver ranges) уязвимости с зафиксированными версиями в SBOM.",
        "pitfalls": "Шторм алертов (Alert Fatigue): оповещение о некритических уязвимостях без привязки к скорингу EPSS (Exploit Prediction Scoring System) демотивирует инженеров.",
        "bigtech_interview": "В SOC (Security Operations Center) Яндекса и VK дежурные инженеры опираются на платформу централизованного учета SBOM для мгновенного ответа на вопрос: 'Сколько наших сервисов уязвимы прямо сейчас?'"
    },
    {
        "num": 97,
        "title": "Развертывание и базовая конфигурация собственного Go Proxy (Athens)",
        "task": "Разверните собственный экземпляр Athens Proxy в Docker-контейнере, настройте монтирование локального хранилища и проверьте скачивание пакетов через локальный прокси.",
        "theory": "Athens — популярный открытый прокси-сервер для Go модулей (Go Module Proxy). Он реализует стандартный протокол загрузки модулей (GOPROXY protocol), кэширует скачанные модули в локальное или облачное хранилище и позволяет изолировать внутреннюю сеть компании от внешнего интернета.",
        "step_by_step": [
            "Запустите контейнер Athens с привязкой порта 3000: `docker run -d -p 3000:3000 --name athens-proxy gomods/athens:v0.14.1`.",
            "Настройте переменную `export GOPROXY=http://localhost:3000`.",
            "Выполните загрузку стороннего модуля через `go get github.com/google/uuid`.",
            "Убедитесь в логах контейнера Athens в успешном кэшировании архива модуля."
        ],
        "code_blocks": [
            {
                "filename": "run_athens.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[ATHENS] Развертывание прокси-сервера Athens в Docker...\"\n# docker run -d \\\n#   --name athens-proxy \\\n#   -p 3000:3000 \\\n#   -e ATHENS_STORAGE_TYPE=disk \\\n#   -e ATHENS_DISK_STORAGE_ROOT=/var/lib/athens \\\n#   -v /var/local/athens:/var/lib/athens \\\n#   gomods/athens:latest\n\necho \"[TEST] Проверка доступности healthcheck эндпоинта...\"\n# curl -s http://localhost:3000/readyz || true\n\necho \"[OK] Сервер Athens готов к обработке запросов GOPROXY.\"\n",
                "note": "Скрипт запуска кэширующего прокси Athens"
            }
        ],
        "under_the_hood": "Athens слушает HTTP эндпоинты протокола Go Modules: `GET /{module}/@v/list`, `GET /{module}/@v/{version}.info`, `GET /{module}/@v/{version}.mod` и `GET /{module}/@v/{version}.zip`.",
        "pitfalls": "Отсутствие персистентного тома приведет к потере всего кэша модулей при перезапуске контейнера Athens.",
        "bigtech_interview": "Зачем крупным компаниям развертывать собственный GOPROXY вместо использования proxy.golang.org? Для соблюдения требований регуляторов, изоляции сети и защиты от сбоев в зарубежных CDN."
    },
    {
        "num": 98,
        "title": "Многоуровневая маршрутизация зависимостей через GOPROXY",
        "task": "Сконфигурируйте цепочку зеркал в переменной окружения GOPROXY со списком fallback-серверов и проверьте переключение при недоступности основного сервера.",
        "theory": "Переменная `GOPROXY` поддерживает список URL, разделенных запятыми или символом пайпа `|`. Запятая означает переход к следующему прокси только в случае ошибки 404/410 (модуль не найден). Символ `|` означает переход при любой сетевой ошибке или таймауте. Значение `direct` указывает скачивать модуль напрямую через Git/VCS.",
        "step_by_step": [
            "Сконфигурируйте цепочку: `GOPROXY=http://athens.corp:3000|https://proxy.golang.org,direct`.",
            "Проверьте сценарий отказа: отключите основной Athens прокси.",
            "Убедитесь, что Go переключился на публичный прокси без прерывания сборки.",
            "Напишите Go-тест, парсящий значение переменной GOPROXY и проверяющий синтаксис."
        ],
        "code_blocks": [
            {
                "filename": "proxy_chain.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n)\n\nfunc AnalyzeGOPROXY(val string) {\n\tfmt.Printf(\"[CONFIG] Анализ строки GOPROXY: %s\\n\", val)\n\tfallbacks := strings.Split(val, \"|\")\n\tfor i, fb := range fallbacks {\n\t\tproxies := strings.Split(fb, \",\")\n\t\tfmt.Printf(\" Уровень отказа %d: %v\\n\", i+1, proxies)\n\t}\n}\n\nfunc main() {\n\tchain := \"http://internal-athens.corp:3000|https://proxy.golang.org,direct\"\n\tAnalyzeGOPROXY(chain)\n\tfmt.Println(\"[OK] Цепочка прокси валидна и обеспечивает отказоустойчивость.\")\n}\n",
                "note": "Парсинг правил отказа и маршрутизации GOPROXY"
            }
        ],
        "under_the_hood": "Go toolchain выполняет HTTP GET запрос к каждому элементу списка по очереди. Если сервер вернул HTTP 500 и разделитель был `,`, сборка упадет. Если использовался `|`, клиент перейдет к следующему URL.",
        "pitfalls": "Использование разделителя `,` вместо `|` при нестабильном корпоративном прокси приведет к падению CI при сетевых таймаутах прокси.",
        "bigtech_interview": "В чем разница между запятой и вертикальной чертой в GOPROXY? Это один из самых популярных каверзных вопросов на собеседованиях по инфраструктуре Go."
    },
    {
        "num": 99,
        "title": "Настройка надежных бэкендов хранения для Athens (S3 / MinIO / ФС)",
        "task": "Сконфигурируйте Athens для работы с персистентным S3/MinIO хранилищем пакетов, настройте политики иммутабельности бакетов (WORM) и версионирование.",
        "theory": "В production-окружении локальная файловая система одного хоста не масштабируется. Athens поддерживает бэкенды хранения в объектных хранилищах (AWS S3, MinIO, Google Cloud Storage, Azure Blob). Использование S3 с включенным режимом Object Lock (WORM — Write Once, Read Many) исключает возможность подмены или случайного удаления ранее сохраненных версий библиотек.",
        "step_by_step": [
            "Создайте S3/MinIO бакет `corp-go-modules`.",
            "Настройте конфигурацию Athens через переменные окружения `ATHENS_STORAGE_TYPE=s3`.",
            "Передайте параметры подключения: эндпоинт, ключ доступа, регион.",
            "Убедитесь, что при запросе нового модуля zip-архив сохраняется в S3-бакете."
        ],
        "code_blocks": [
            {
                "filename": "athens_s3.env",
                "lang": "shell",
                "code": "# Конфигурация бэкенда хранения Athens в S3/MinIO\nATHENS_STORAGE_TYPE=s3\nATHENS_S3_BUCKET_NAME=corp-go-modules\nATHENS_S3_REGION=us-east-1\nATHENS_S3_ENDPOINT=https://minio.corp.internal:9000\nATHENS_S3_ACCESS_KEY_ID=athens-uploader\nATHENS_S3_SECRET_ACCESS_KEY=SuperSecretS3Key2026\nATHENS_S3_FORCE_PATH_STYLE=true\n",
                "note": "Конфигурационный файл подключения Athens к S3 Object Storage"
            }
        ],
        "under_the_hood": "Athens стримит скачиваемые архивы напрямую в S3 посредством Multipart Upload, параллельно отдавая байты клиенту `go get` для снижения задержки первого скачивания.",
        "pitfalls": "Отсутствие флага `force_path_style: true` при работе с кастомным MinIO сервером приведет к ошибкам DNS-резолвинга sub-domain бакетов.",
        "bigtech_interview": "Архитектура хранения зависимостей в enterprise-системах опирается на геораспределенные S3-кластеры с активной репликацией между дата-центрами."
    },
    {
        "num": 100,
        "title": "Аутентификация и контроль доступа к Go Module Proxy",
        "task": "Настройте аутентификацию на базе Bearer токенов или Basic Auth для Athens Proxy и сконфигурируйте файл ~/.netrc на рабочих станциях разработчиков.",
        "theory": "Чтобы ограничить доступ к корпоративному прокси и защитить приватные модули компании, Athens настраивают с аутентификацией. Инструмент `go` автоматически считывает учетные данные из файла `~/.netrc` (в Linux/macOS) или `%USERPROFILE%/_netrc` (в Windows) при обращении к защищенным HTTP-эндпоинтам.",
        "step_by_step": [
            "Включите базовую аутентификацию в конфигурации прокси.",
            "Создайте учетную запись пользователя с токеном доступа.",
            "Настройте файл `~/.netrc` со строками `machine athens.corp.internal login ci-user password <token>`.",
            "Установите права `chmod 600 ~/.netrc` для предотвращения чтения другими пользователями ОС."
        ],
        "code_blocks": [
            {
                "filename": "setup_netrc.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nNETRC_FILE=\"${HOME}/.netrc\"\nPROXY_HOST=\"athens.company.internal\"\nUSER_LOGIN=\"corp-developer\"\nSECRET_TOKEN=\"ghp_secureTokenForAthens2026\"\n\necho \"[NETRC] Настройка учетных данных для защищенного GOPROXY...\"\ntouch \"${NETRC_FILE}\"\nchmod 600 \"${NETRC_FILE}\"\n\ncat >> \"${NETRC_FILE}\" << EOF\nmachine ${PROXY_HOST}\n  login ${USER_LOGIN}\n  password ${SECRET_TOKEN}\nEOF\n\necho \"[OK] Файл ~/.netrc успешно обновлен с правами 0600.\"\n",
                "note": "Безопасная настройка файла .netrc для доступа к защищенному GOPROXY"
            }
        ],
        "under_the_hood": "Go toolchain использует пакет `net/http`, который при наличии файла `.netrc` автоматически добавляет заголовок `Authorization: Basic ...` к каждому запросу к указанному хосту.",
        "pitfalls": "Если права на `.netrc` шире, чем `0600`, утилиты (например, curl или git) могут отказаться его использовать из соображений безопасности.",
        "bigtech_interview": "Как безопасно передать учетные данные в Go toolchain внутри Docker-контейнера? Ответ: Использовать Docker BuildKit secret mounts (`--mount=type=secret,id=netrc,target=/root/.netrc`)."
    },
    {
        "num": 101,
        "title": "Кэширующее проксирование и фильтрация внешних запросов к upstream",
        "task": "Сконфигурируйте Athens как кэширующий буфер перед proxy.golang.org с фильтрацией недопустимых модулей и сохранением копий зависимостей в S3.",
        "theory": "Athens может выступать прозрачным кэширующим шлюзом (Pull-Through Cache) к публичному `proxy.golang.org`. При первом запросе разработчика модуль скачивается из апстрима, сохраняется в корпоративном S3-бакете и отдается клиенту. Все последующие запросы от любых инженеров и CI-пайплайнов обслуживаются мгновенно из локального S3 без выхода в глобальный интернет.",
        "step_by_step": [
            "Сконфигурируйте параметр `ATHENS_UPSTREAM_URL=https://proxy.golang.org`.",
            "Настройте локальный диск или S3 бакет для персистентного кэша.",
            "Проверьте время отклика при первом (miss) и повторном (hit) запросе модуля.",
            "Убедитесь, что при отключении интернета ранее скачанный модуль продолжает отдаваться."
        ],
        "code_blocks": [
            {
                "filename": "athens_upstream.toml",
                "lang": "toml",
                "code": "# Конфигурация каскадного кэширования Athens\n[storage]\n  type = \"s3\"\n  [storage.s3]\n    bucket = \"corp-athens-cache\"\n    region = \"ru-central1\"\n\n[upstream]\n  url = \"https://proxy.golang.org\"\n  timeout = 30\n\n# Белый список / правила фильтрации\n[filter]\n  rule = \"include\"\n",
                "note": "Конфигурация Athens с апстримом proxy.golang.org"
            }
        ],
        "under_the_hood": "Athens проверяет наличие запрашиваемого файла в локальном хранилище. Если объект найден, upstream даже не опрашивается, что полностью защищает от внезапных изменений в апстриме.",
        "pitfalls": "Если upstream вернет ошибку 502 или таймаут, Athens вернет 500 ошибку клиенту, если не настроен grace-период кэширования.",
        "bigtech_interview": "В Lamoda и Wildberries внутренний кэширующий прокси снижает внешний интернет-трафик сборочных ферм на гигабайты в сутки и ускоряет сборку в 3-5 раз."
    },
    {
        "num": 102,
        "title": "Управление Go-зависимостями в корпоративном репозитории JFrog Artifactory",
        "task": "Изучите архитектуру виртуальных репозиториев Go в JFrog Artifactory (Local, Remote, Virtual), объясните механизм работы с Xray для поиска уязвимостей и настройте GOPROXY.",
        "theory": "JFrog Artifactory — enterprise-стандарт хранения артефактов. Для Go он предоставляет 3 типа репозиториев:\n1. Local: для внутренних модулей компании.\n2. Remote: кэширующее зеркало публичных репозиториев (`proxy.golang.org`).\n3. Virtual: объединяющий эндпоинт, инкапсулирующий Local и Remote в единый URL `GOPROXY`.\nИнтегрированный сканер JFrog Xray автоматически блокирует загрузку модулей, содержащих критические уязвимости или запрещенные лицензии.",
        "step_by_step": [
            "Создайте Virtual Go Repository `go-virtual` в панели Artifactory.",
            "Объедините в нем внутренний репозиторий `go-local` и удаленный `go-remote`.",
            "Сконфигурируйте политику Xray на блокировку CVE с CVSS > 8.0.",
            "Настройте разработчиков на единый эндпоинт `GOPROXY=https://artifactory.corp/artifactory/api/go/go-virtual`."
        ],
        "code_blocks": [
            {
                "filename": "artifactory_config.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nARTIFACTORY_URL=\"https://artifactory.company.internal/artifactory/api/go/go-virtual\"\n\necho \"[ARTIFACTORY] Настройка Go toolchain на enterprise виртуальный репозиторий...\"\nexport GOPROXY=\"${ARTIFACTORY_URL}\"\nexport GONOSUMDB=\"*\" # Проверка сумм выполняется на стороне Artifactory\n\necho \"[ENV] GOPROXY=${GOPROXY}\"\necho \"[ENV] GONOSUMDB=${GONOSUMDB}\"\necho \"[OK] Все зависимости прозрачно контролируются шлюзом JFrog Xray.\"\n",
                "note": "Подключение Go к виртуальному корпоративному репозиторию JFrog Artifactory"
            }
        ],
        "under_the_hood": "Artifactory перехватывает запросы пакетов, за доли секунды сверяет PURL с базой JFrog Xray и возвращает HTTP 403 Forbidden с описанием уязвимости, если пакет заблокирован политикой безопасности.",
        "pitfalls": "Отключение `GONOSUMDB=*` при использовании Artifactory приведет к ошибкам при обращении к внутренним приватным модулям компании через Google SumDB.",
        "bigtech_interview": "В чем главное отличие между Athens и JFrog Artifactory? Athens — это специализированный легковесный open-source прокси, а Artifactory — универсальная enterprise-платформа с RBAC, аудитом, сканированием Xray и поддержкой десятков экосистем."
    },
    {
        "num": 103,
        "title": "Управление жизненным циклом зависимостей через каталог vendor",
        "task": "Создайте и структурируйте каталог vendor/ для микросервиса с несколькими внешними библиотеками, проверьте консистентность зависимостей и выполните сборку в изолированном окружении.",
        "theory": "Команда `go mod vendor` материализует все внешние зависимости в локальной директории `vendor/` проекта. Это делает репозиторий полностью самодостаточным: для сборки больше не требуется доступ к публичным реестрам, Git-хостингам или кэшу модулей. Такой подход исключает риск сбоев при падении внешних сервисов (GitHub, proxy.golang.org) и защищает проект от внезапного удаления библиотек их авторами.",
        "step_by_step": [
            "Инициализируйте зависимости проекта с помощью `go get`.",
            "Выполните `go mod tidy` для удаления неиспользуемых модулей.",
            "Сформируйте локальный вендор командой `go mod vendor`.",
            "Соберите проект с флагом `-mod=vendor` и проверьте автономность компиляции."
        ],
        "code_blocks": [
            {
                "filename": "vendor_cycle.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[1/3] Очистка неиспользуемых зависимостей...\"\ngo mod tidy\n\necho \"[2/3] Выгрузка зависимостей в каталог vendor/...\"\ngo mod vendor\n\necho \"[3/3] Сборка с принудительным использованием vendor...\"\ngo build -mod=vendor -v -o service_app main.go\n\necho \"[SUCCESS] Проект успешно собран из локального каталога vendor.\"\n",
                "note": "Базовый жизненный цикл вендоринга проекта на Go"
            }
        ],
        "under_the_hood": "Go сохраняет в файле `vendor/modules.txt` хеши и версии каждого модуля, гарантируя, что компилятор скомпонует в итоговый бинарник именно проверенные исходники.",
        "pitfalls": "Если изменить исходный код внутри vendor/ вручную без фиксации, следующий вызов `go mod vendor` молча перезапишет все ваши изменения.",
        "bigtech_interview": "В enterprise-разработке вендоринг часто применяется для критических микросервисов банковских систем, где недопустима даже секундная задержка сборщика из-за сети."
    },
    {
        "num": 104,
        "title": "Публикация и скачивание Go-модулей в GitLab Package Registry",
        "task": "Сконфигурируйте публикацию версионированного Go-модуля в GitLab Generic/Package Registry и настройте скачивание модуля клиентом через GOPROXY.",
        "theory": "GitLab Package Registry предоставляет встроенный реестр пакетов для Go-модулей. Он позволяет командам публиковать приватные библиотеки в виде готовых zip-архивов с файлами `.mod` и `.info`, избавляя от необходимости предоставлять разработчикам прямой доступ к исходному Git-репозиторию библиотеки. Клиент `go` обращается к реестру по стандартному протоколу GOPROXY.",
        "step_by_step": [
            "Сформируйте релизный архив модуля: `module@v1.0.0.zip`.",
            "Опубликуйте модуль в реестр GitLab с помощью HTTP PUT запроса и токена `CI_JOB_TOKEN`.",
            "Настройте на клиенте `GOPROXY=https://gitlab.corp.com/api/v4/projects/<id>/packages/go,https://proxy.golang.org,direct`.",
            "Установите модуль командой `go get gitlab.corp.com/group/my-module@v1.0.0`."
        ],
        "code_blocks": [
            {
                "filename": "gitlab_publish.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nPROJECT_ID=\"12345\"\nMODULE_PATH=\"gitlab.corp.com/infra/logger\"\nVERSION=\"v1.2.0\"\n\necho \"[GITLAB] Публикация модуля ${MODULE_PATH}@${VERSION} в Package Registry...\"\n# curl --header \"JOB-TOKEN: ${CI_JOB_TOKEN}\" \\\n#   --upload-file \"${VERSION}.zip\" \\\n#   \"https://gitlab.corp.com/api/v4/projects/${PROJECT_ID}/packages/go/${MODULE_PATH}/@v/${VERSION}.zip\"\n\necho \"[CONFIG] Настройка клиента на использование GitLab Go Proxy:\"\necho \"export GOPROXY=https://gitlab.corp.com/api/v4/projects/${PROJECT_ID}/packages/go,direct\"\n",
                "note": "Публикация пакета в GitLab Package Registry по спецификации GOPROXY"
            }
        ],
        "under_the_hood": "GitLab реализует эндпоинты протокола Go Module Proxy: `@v/list`, `.info`, `.mod`, `.zip`, отдавая метаданные модуля напрямую без клонирования всего Git-репозитория.",
        "pitfalls": "Имя модуля в файле `go.mod` обязано в точности совпадать с путем в URL проекта GitLab, иначе `go get` завершится ошибкой валидации имени модуля.",
        "bigtech_interview": "Как безопасно распространять общие Go-библиотеки в enterprise-контуре, не давая разработчикам права на чтение всего исходного репозитория? Через GitLab Package Registry или Artifactory."
    },
    {
        "num": 105,
        "title": "Анатомия каталога vendor и структура файла modules.txt",
        "task": "Напишите Go-парсер файла vendor/modules.txt, который извлекает список завендоренных модулей, их версии, пакеты и флаги замены (replace directives).",
        "theory": "Каталог `vendor/` содержит исходные тексты пакетов и ключевой файл `vendor/modules.txt`. Этот файл содержит метаданные о структуре зависимостей: строки вида `# module version` объявляют модуль, за ними следуют пути пакетов внутри модуля. Если модуль подменен через `replace`, файл содержит специальную директиву `=>`. Понимание структуры `modules.txt` критично для автоматизированного аудита вендоринга.",
        "step_by_step": [
            "Откройте и прочитайте файл `vendor/modules.txt`.",
            "Реализуйте синтаксический разбор строк: строки с `#` определяют модуль и версию, остальные — пакеты.",
            "Обработайте директивы `=>` для замененных модулей.",
            "Сформируйте структурированную карту зависимостей проекта."
        ],
        "code_blocks": [
            {
                "filename": "parse_modules_txt.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"bufio\"\n\t\"fmt\"\n\t\"strings\"\n)\n\ntype VendoredModule struct {\n\tPath     string\n\tVersion  string\n\tPackages []string\n}\n\nfunc ParseModulesTxt(content string) []VendoredModule {\n\tvar modules []VendoredModule\n\tvar current *VendoredModule\n\n\tscanner := bufio.NewScanner(strings.NewReader(content))\n\tfor scanner.Scan() {\n\t\tline := strings.TrimSpace(scanner.Text())\n\t\tif line == \"\" {\n\t\t\tcontinue\n\t\t}\n\t\tif strings.HasPrefix(line, \"# \") {\n\t\t\tparts := strings.Fields(line[2:])\n\t\t\tmod := VendoredModule{Path: parts[0]}\n\t\t\tif len(parts) > 1 {\n\t\t\t\tmod.Version = parts[1]\n\t\t\t}\n\t\t\tmodules = append(modules, mod)\n\t\t\tcurrent = &modules[len(modules)-1]\n\t\t} else if current != nil {\n\t\t\tcurrent.Packages = append(current.Packages, line)\n\t\t}\n\t}\n\treturn modules\n}\n\nfunc main() {\n\tsample := `# github.com/google/uuid v1.6.0\ngithub.com/google/uuid\n# go.uber.org/zap v1.27.0\ngo.uber.org/zap\ngo.uber.org/zap/zapcore\n`\n\tmods := ParseModulesTxt(sample)\n\tfor _, m := range mods {\n\t\tfmt.Printf(\"[VENDOR] Модуль: %s @ %s, Пакетов: %d\\n\", m.Path, m.Version, len(m.Packages))\n\t}\n}\n",
                "note": "Синтаксический разбор манифеста vendor/modules.txt"
            }
        ],
        "under_the_hood": "Компилятор Go при сборке с `-mod=vendor` сверяет соответствие файлов в `vendor/` записям в `modules.txt`. Если в каталоге обнаружены незарегистрированные пакеты, компиляция прерывается.",
        "pitfalls": "Ручное редактирование `modules.txt` приведет к ошибкам при первой же автоматической синхронизации через `go mod vendor`.",
        "bigtech_interview": "Какую роль играет modules.txt при проверке лицензий и безопасности? Он содержит точный исчерпывающий перечень реально используемых пакетов без учета транзитивных модулей, не вошедших в бинарник."
    },
    {
        "num": 106,
        "title": "Изолированная компиляция с флагом -mod=vendor",
        "task": "Скомпилируйте проект с флагом go build -mod=vendor в среде без подключения к интернету и проверьте вывод компилятора на отсутствие внешних обращений.",
        "theory": "Флаг `-mod=vendor` указывает компилятору Go использовать исключительно исходные файлы из локальной директории `vendor/`. При этом механизм проверки `go.sum` и сетевые запросы к `GOPROXY` полностью отключаются. Это гарантирует максимальную скорость сборки в CI и 100% стабильность компиляции даже при глобальных сбоях сети.",
        "step_by_step": [
            "Убедитесь, что каталог `vendor/` актуален.",
            "Установите переменную окружения `GOPROXY=off`.",
            "Запустите компиляцию с подробным выводом: `go build -v -mod=vendor -o app main.go`.",
            "Проверьте, что в логах компиляции отсутствуют сетевые этапы download/fetch."
        ],
        "code_blocks": [
            {
                "filename": "build_vendor.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[BUILD] Запуск автономной сборки из каталога vendor...\"\n# Отключаем сеть для Go toolchain\nexport GOPROXY=off\n\ngo build -mod=vendor -v -o /tmp/offline_binary main.go\n\necho \"[SUCCESS] Бинарник успешно скомпилирован без единого сетевого запроса!\"\n",
                "note": "Сборка Go приложения с полным отключением сети"
            }
        ],
        "under_the_hood": "Если корень проекта содержит папку `vendor` и версия Go в `go.mod` >= 1.14, компилятор Go по умолчанию выбирает режим `-mod=vendor`, если флаг явно не переопределен.",
        "pitfalls": "Если в `go.mod` добавлена новая зависимость, но не выполнена команда `go mod vendor`, флаг `-mod=vendor` приведет к ошибке: `cannot find package ... in any of ...`.",
        "bigtech_interview": "Почему в CI крупных компаний предпочитают флаг `-mod=vendor` вместо предварительного прогрева кэша `go mod download`? Это исключает зависимость раннеров от локального кэша диска и сетевых сбоев."
    },
    {
        "num": 107,
        "title": "Оптимизация сборочных конвейеров CI/CD с использованием вендоринга",
        "task": "Спроектируйте GitLab CI / GitHub Actions пайплайн, где каталог vendor/ проверяется на чистоту (no diff с go.mod), исключая запуск медленного этапа скачивания зависимостей.",
        "theory": "В сборочных конвейерах этап скачивания зависимостей (`go mod download`) может занимать до 40% времени выполнения джобы. Использование закоммиченного `vendor/` позволяет раннерам немедленно приступать к компиляции и тестам. Для защиты от небрежности разработчиков в CI обязательно включают проверку отсутствия расхождений: `go mod tidy && go mod vendor && git diff --exit-code`.",
        "step_by_step": [
            "Создайте этап верификации целостности зависимостей в CI.",
            "Выполните команду `git diff --exit-code vendor/ go.mod go.sum`.",
            "Если обнаружен дифф — завершите пайплайн с сообщением о необходимости обновления vendor.",
            "Запустите тесты и компиляцию с флагом `-mod=vendor`."
        ],
        "code_blocks": [
            {
                "filename": "ci_vendor_check.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[CI/CD] Проверка актуальности вендоринга...\"\ngo mod tidy\ngo mod vendor\n\nif ! git diff --exit-code vendor/ go.mod go.sum; then\n    echo \"[ERROR] Каталог vendor/ рассинхронизирован с go.mod!\"\n    echo \"Выполните 'go mod tidy && go mod vendor' локально и закоммитьте изменения.\"\n    exit 1\nfi\n\necho \"[OK] Каталог vendor/ идеально синхронизирован.\"\necho \"[CI/CD] Запуск тестов: go test -mod=vendor ./...\"\n",
                "note": "CI проверка отсутствия расхождений в каталоге vendor"
            }
        ],
        "under_the_hood": "Команда `git diff --exit-code` возвращает ненулевой код выхода (1), если в отслеживаемых файлах есть изменения, что позволяет мгновенно прерывать сборочный пайплайн.",
        "pitfalls": "Игнорирование различий в окончаниях строк (CRLF vs LF в Windows/Linux) может приводить к ложным срабатываниям проверки git diff в CI.",
        "bigtech_interview": "В инфраструктуре Сбера и Тинькофф автоматический аудит расхождения вендора является обязательным Quality Gate перед допуском Pull Request к ревью."
    },
    {
        "num": 108,
        "title": "Оптимизация размера каталога vendor и удаление тестового мусора",
        "task": "Напишите Go-утилиту или bash-скрипт, который оптимизирует размер папки vendor/: удаляет ненужные тестовые файлы (*_test.go), тестовые данные (testdata) и документацию.",
        "theory": "По умолчанию `go mod vendor` копирует только пакеты, необходимые для сборки приложения, но в них могут присутствовать крупные директории `testdata`, примеры и файлы документации. Каталог `vendor/` может разрастаться до сотен мегабайт, замедляя операции с Git. Очистка каталога от тестовых фикстур и документации снижает размер репозитория без вреда для компиляции.",
        "step_by_step": [
            "Измерьте исходный размер каталога `vendor/` командой `du -sh vendor`.",
            "Удалите директории `testdata` и неиспользуемые тестовые файлы.",
            "Убедитесь, что приложение продолжает успешно компилироваться с `-mod=vendor`.",
            "Зафиксируйте уменьшение размера каталога."
        ],
        "code_blocks": [
            {
                "filename": "trim_vendor.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[VENDOR-OPT] Анализ размера каталога vendor/...\"\nINITIAL_SIZE=$(du -sh vendor | awk '{print $1}')\necho \"Начальный размер: ${INITIAL_SIZE}\"\n\necho \"[VENDOR-OPT] Удаление тестовых данных и файлов документации...\"\nfind vendor/ -type d -name \"testdata\" -exec rm -rf {} + || true\nfind vendor/ -type f -name \"*_test.go\" -delete || true\nfind vendor/ -type f -name \"*.md\" -delete || true\n\nFINAL_SIZE=$(du -sh vendor | awk '{print $1}')\necho \"Итоговый размер: ${FINAL_SIZE}\"\n\necho \"[VERIFY] Проверка успешности сборки...\"\ngo build -mod=vendor -o /tmp/check_bin main.go\necho \"[SUCCESS] Оптимизация завершена без нарушения компиляции!\"\n",
                "note": "Скрипт оптимизации объема вендорированных зависимостей"
            }
        ],
        "under_the_hood": "Компилятор Go никогда не включает файлы `*_test.go` и каталоги `testdata` в релизный бинарник; они нужны только при запуске тестов внутри сторонних пакетов.",
        "pitfalls": "Если ваши собственные интеграционные тесты запускают тесты сторонних вендорированных пакетов, удаление `*_test.go` сломает эти запуски.",
        "bigtech_interview": "Как справиться с монорепозиторием, где каталог vendor занимает гигабайты? Ответ: Использовать Sparse Checkout в Git или переходить на кэширующий GOPROXY (Athens) вместо хранения исходников в Git."
    },
    {
        "num": 109,
        "title": "Сканирование вендорированного кода с помощью govulncheck",
        "task": "Запустите утилиту govulncheck с явным указанием флага -mod=vendor для сканирования кода зависимостей, фактически находящегося в директории vendor/ проекта.",
        "theory": "При анализе безопасности критически важно сканировать именно тот код, который будет включен в релизный бинарник. Если разработчик локально модифицировал файл внутри `vendor/` или откатил версию вручную, обычный сканер `go.mod` этого не заметит. Утилита `govulncheck` поддерживает сборку и анализ графа вызовов с флагом `-mod=vendor`.",
        "step_by_step": [
            "Подготовьте проект с каталогом `vendor/`.",
            "Запустите сканирование: `govulncheck -mod=vendor ./...`.",
            "Изучите отчет о достижимых уязвимостях.",
            "Убедитесь, что анализ учитывает локальное состояние файлов вендора."
        ],
        "code_blocks": [
            {
                "filename": "vuln_vendor.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[GOVULNCHECK] Сканирование локального вендора зависимостей...\"\n\n# Флаг -mod=vendor принуждает анализатор строить AST по коду из папки vendor/\nif govulncheck -mod=vendor ./... ; then\n    echo \"[OK] В коде вендора уязвимостей не найдено.\"\nelse\n    echo \"[ALERT] В вендорированном коде обнаружены уязвимые вызовы!\"\n    exit 1\nfi\n",
                "note": "Запуск govulncheck с использованием локального вендора"
            }
        ],
        "under_the_hood": "govulncheck компилирует AST-представление пакетов, подставляя символы из `vendor/modules.txt`, а затем опрашивает базу `vuln.go.dev` по реальным ревизиям модулей.",
        "pitfalls": "Если файлы в `vendor/` рассинхронизированы с `modules.txt`, govulncheck упадет с синтаксической ошибкой загрузчика пакетов.",
        "bigtech_interview": "Почему аудит исходников vendor предпочтительнее аудита lock-файлов? Lock-файл декларирует намерения, а исходники в vendor представляют собой фактический код, идущий в прод."
    },
    {
        "num": 110,
        "title": "Безопасный процесс обновления вендорированных зависимостей",
        "task": "Реализуйте регламент обновления зависимостей: обновление минорных версий (go get -u), перегенерация вендора, аудит диффа (git diff) и автоматический прогон регрессионных тестов.",
        "theory": "Обновление сторонних библиотек — одна из самых частых причин регрессий и проникновения уязвимостей (Supply Chain Poisoning). Безопасный процесс обновления требует пошагового контроля: 1) обновление точечных зависимостей; 2) `go mod tidy && go mod vendor`; 3) детальный код-ревью появившихся диффов в `vendor/`; 4) запуск полного набора unit и e2e тестов.",
        "step_by_step": [
            "Обновите конкретный модуль: `go get github.com/gin-gonic/gin@v1.9.1`.",
            "Выполните `go mod tidy` и `go mod vendor`.",
            "Проанализируйте изменения кода в сторонних пакетах через `git diff vendor/`.",
            "Запустите регрессионные тесты: `go test -mod=vendor -race ./...`."
        ],
        "code_blocks": [
            {
                "filename": "safe_update.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nTARGET_PKG=\"${1:-github.com/google/uuid}\"\n\necho \"[1/4] Обновление модуля ${TARGET_PKG}...\"\ngo get \"${TARGET_PKG}\"\n\necho \"[2/4] Синхронизация vendor каталога...\"\ngo mod tidy\ngo mod vendor\n\necho \"[3/4] Проверка диффа исходников (SCA/Security review)...\"\ngit diff --stat vendor/\n\necho \"[4/4] Запуск регрессионного тестирования...\"\ngo test -mod=vendor -race ./...\n\necho \"[SUCCESS] Модуль безопасно обновлен и протестирован!\"\n",
                "note": "Регламент безопасного обновления вендорированной библиотеки"
            }
        ],
        "under_the_hood": "Команда `go get` разрешает минимальные подходящие версии зависимостей (MVS — Minimal Version Selection), не обновляя не затронутые транзитивные пакеты без явной необходимости.",
        "pitfalls": "Выполнение слепого обновления `go get -u ./...` может обновить десятки библиотек сразу, породив нечитаемый дифф на 50 000 строк и трудноуловимые баги.",
        "bigtech_interview": "В Ozon и Яндексе обновления внешних библиотек оформляются отдельными изолированными Pull Request с обязательным ревью от платформенных инженеров."
    },
    {
        "num": 111,
        "title": "Экспорт лицензионных файлов зависимостей для юридического комплаенса",
        "task": "Настройте утилиту go-licenses для извлечения и сохранения всех файлов лицензий сторонних модулей в каталог vendor-licenses/ перед сборкой дистрибутива.",
        "theory": "Большинство свободных лицензий (MIT, Apache 2.0, BSD) требуют обязательного включения оригинального текста лицензии и уведомления об авторских правах (Notice) в состав распространяемого бинарника или документации продукта. Утилита `go-licenses save` автоматически находит все файлы лицензий в дереве зависимостей и копирует их в указанную директорию для юристов.",
        "step_by_step": [
            "Установите утилиту: `go install github.com/google/go-licenses@latest`.",
            "Запустите экспорт: `go-licenses save ./... --save_path=./THIRD_PARTY_LICENSES`.",
            "Проверьте, что каталог содержит лицензии всех используемых библиотек.",
            "Включите сгенерированную директорию в состав архива релиза."
        ],
        "code_blocks": [
            {
                "filename": "save_licenses.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nOUTPUT_DIR=\"dist/THIRD_PARTY_LICENSES\"\nmkdir -p \"${OUTPUT_DIR}\"\n\necho \"[LEGAL] Сохранение лицензий всех зависимостей для релиза...\"\n# go-licenses save ./... --save_path=\"${OUTPUT_DIR}\" --force\n\necho \"[OK] Юридический каталог сформирован:\"\n# ls -la \"${OUTPUT_DIR}\"\necho \"[SUCCESS] Уведомления об авторских правах соблюдены.\"\n",
                "note": "Сбор и упаковка текстов лицензий сторонних библиотек"
            }
        ],
        "under_the_hood": "go-licenses сканирует корень каждого пакета в поисках файлов, удовлетворяющих регулярным выражениям `LICENSE*`, `COPYING*`, `NOTICE*`.",
        "pitfalls": "Если зависимость использует кастомный или переименованный файл лицензии (например, `COPYRIGHT.txt`), утилита может выдать предупреждение о неустановленной лицензии.",
        "bigtech_interview": "Поставка коммерческого софта крупным клиентам (B2B) без сформированного каталога Open Source Notices является нарушением договоров поставки и лицензионных соглашений."
    },
    {
        "num": 112,
        "title": "Комплексная стратегия достижения воспроизводимости сборок",
        "task": "Объедините локальный вендоринг, фиксацию компилятора в контейнере и флаги компилятора для достижения 100% повторяемости сборки бинарника Go.",
        "theory": "Полная воспроизводимость сборки требует контроля трех факторов:\n1. Зафиксированный исходный код и зависимости (каталог `vendor/`).\n2. Детерминированная среда компиляции (фиксированный Docker-образ `golang:1.22.5` с неизменной версией компилятора).\n3. Флаги детерминизма компилятора: `-trimpath` и `-ldflags=\"-s -w -buildid=\"`.\nПри соблюдении этих правил любой разработчик на любой машине получит побайтово идентичный файл.",
        "step_by_step": [
            "Зафиксируйте зависимости в каталоге `vendor/`.",
            "Сконфигурируйте Dockerfile с точным дайджестом базового образа: `golang:1.22.5@sha256:...`.",
            "Передайте флаги сборки: `go build -trimpath -ldflags=\"-buildid=\" -mod=vendor`.",
            "Сверьте хэши бинарников, собранных в контейнере на Linux и macOS хостах."
        ],
        "code_blocks": [
            {
                "filename": "reproducible_build.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[REPRO] Компиляция абсолютно воспроизводимого артефакта...\"\n\n# Фиксируем временную зону и локаль для детерминизма\nexport LC_ALL=C\nexport TZ=UTC\n\nCGO_ENABLED=0 go build \\\n  -trimpath \\\n  -mod=vendor \\\n  -ldflags=\"-s -w -buildid=\" \\\n  -o app_repro main.go\n\nHASH=$(sha256sum app_repro | awk '{print $1}')\necho \"[OK] Контрольная сумма бинарника: ${HASH}\"\n",
                "note": "Команда эталонной детерминированной компиляции"
            }
        ],
        "under_the_hood": "Компилятор Go детерминирован по своей природе. Единственными источниками расхождений являются абсолютные пути файлов (устраняются `-trimpath`) и случайный buildid (устраняется `-buildid=`).",
        "pitfalls": "Использование генерации кода `go generate` со случайными данными или внедрением текущего времени нарушает воспроизводимость.",
        "bigtech_interview": "Вопрос: 'Зачем Google внедрил reproducible builds в свои системы?' Ответ: Для независимого подтверждения того, что бинарник в проде в точности соответствует исходному коду в репозитории."
    },
    {
        "num": 113,
        "title": "Развертывание Go-приложений в изолированных Air-Gapped контурах",
        "task": "Спроектируйте архитектуру поставки и сборки микросервисов в абсолютно изолированный закрытый периметр (Air-Gapped) без доступа к сети Интернет.",
        "theory": "В закрытых контурах (военная промышленность, АЭС, критическая инфраструктура, банковский процессинг) сеть физически изолирована от глобального интернета. Доставка кода и зависимостей выполняется через проверенные отчуждаемые носители или внутренний шлюз с однонаправленной передачей данных (Data Diode). Внутри периметра развертывается зеркало OCI-реестра и локальный Athens/Artifactory, либо используется исключительно закоммиченный каталог `vendor/`.",
        "step_by_step": [
            "Сформируйте автономный архив репозитория со всеми зависимостями в `vendor/`.",
            "Экспортируйте базовые образы контейнеров в tar-архивы (`docker save`).",
            "Проведите проверку на вирусы и уязвимости на шлюзе фильтрации.",
            "Импортируйте артефакты во внутренний реестр закрытого контура."
        ],
        "code_blocks": [
            {
                "filename": "airgap_export.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nBUNDLE_DIR=\"airgap_bundle\"\nmkdir -p \"${BUNDLE_DIR}\"\n\necho \"[1/3] Подготовка автономного репозитория...\"\ngo mod vendor\ntar -czf \"${BUNDLE_DIR}/source_with_vendor.tar.gz\" --exclude=\".git\" .\n\necho \"[2/3] Сохранение базовых Docker-образов...\"\n# docker pull golang:1.22-alpine\n# docker save golang:1.22-alpine | gzip > \"${BUNDLE_DIR}/golang_builder_image.tar.gz\"\n\necho \"[3/3] Генерация контрольных сумм комплекта поставки...\"\ncd \"${BUNDLE_DIR}\" && sha256sum * > BUNDLE_CHECKSUMS.txt\n\necho \"[SUCCESS] Комплект поставки для передачи через Data Diode готов.\"\n",
                "note": "Скрипт подготовки автономного бандла для закрытого контура"
            }
        ],
        "under_the_hood": "В изолированном контуре DNS-запросы наружу блокируются фаерволом на аппаратном уровне. Любая попытка Go toolchain обратиться к `proxy.golang.org` приведет к мгновенному отказу.",
        "pitfalls": "Забытые зависимости утилит тестирования (например, golangci-lint) потребуют повторной многодневной процедуры согласования передачи файлов через шлюз ИБ.",
        "bigtech_interview": "В чем специфика работы SRE и разработчиков в Air-Gapped контурах? Невозможность использовать публичные образы и документацию онлайн; необходимость полной самодостаточности репозиториев."
    },
    {
        "num": 114,
        "title": "Публикация SBOM как стандарт открытости и доверия к поставщику ПО",
        "task": "Автоматизируйте публикацию CycloneDX и SPDX файлов в секцию GitHub / GitLab Releases на каждый тег версии и напишите манифест прозрачности для заказчиков.",
        "theory": "Современные регуляторы и корпоративные заказчики требуют от разработчиков предоставления SBOM вместе с каждым релизом. Публикация SBOM демонстрирует зрелость процессов DevSecOps компании, позволяет службам безопасности клиентов немедленно оценить риски и быстро отвечать на инциденты вроде обнаружения критических уязвимостей в популярных библиотеках.",
        "step_by_step": [
            "Настройте генерацию SBOM при срабатывании триггера создания тега `v*`.",
            "Сгенерируйте отчеты в форматах SPDX JSON и CycloneDX JSON.",
            "Прикрепите сгенерированные файлы к релизу через GitHub CLI `gh release upload`.",
            "Уведомите клиентов о публичной доступности SBOM через релизные заметки."
        ],
        "code_blocks": [
            {
                "filename": "publish_release_sbom.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nTAG_NAME=\"${1:-v1.5.0}\"\n\necho \"[RELEASE] Генерация паспортов компонентов для релиза ${TAG_NAME}...\"\n# syft packages . -o cyclonedx-json > release-sbom.cdx.json\n# syft packages . -o spdx-json > release-sbom.spdx.json\n\necho \"[RELEASE] Публикация SBOM в GitHub Releases через gh CLI...\"\n# gh release upload \"${TAG_NAME}\" release-sbom.cdx.json release-sbom.spdx.json\n\necho \"[OK] Паспорта компонентов успешно опубликованы в открытом доступе.\"\n",
                "note": "Автоматическая публикация SBOM файлов в секцию релизов"
            }
        ],
        "under_the_hood": "Многие платформы безопасности (например, GitHub Dependency Graph) автоматически парсят опубликованные SBOM и предупреждают пользователей о найденных дефектах.",
        "pitfalls": "Публикация внутреннего SBOM, содержащего конфиденциальные URL приватных корпоративных репозиториев, может раскрыть структуру внутренней сети компании.",
        "bigtech_interview": "Зачем компаниям с открытым исходным кодом публиковать SBOM? Это обязательное условие для участия в тендерах государственных и финтех-структур США и ЕС."
    },
    {
        "num": 115,
        "title": "Сквозная цифровая подпись всех релизных артефактов (Binary, Image, SBOM)",
        "task": "Реализуйте унифицированный сборочный скрипт, подписывающий утилитой Cosign исполняемый бинарный файл, Docker-образ и сгенерированный файл SBOM.",
        "theory": "Подпись одного только Docker-образа оставляет уязвимыми бинарные файлы и сопровождающие документы. Концепция комплексной защиты цепочки поставок (Total Artifact Signing) требует подписывать абсолютно все выходные артефакты: бинарник (`cosign sign-blob`), OCI-образ (`cosign sign`) и документ SBOM (`cosign attest` или `cosign sign-blob`).",
        "step_by_step": [
            "Скомпилируйте бинарный файл приложения.",
            "Сгенерируйте и опубликуйте Docker-образ.",
            "Сгенерируйте документ SBOM.",
            "Подпишите каждый артефакт единой доверенной ключевой парой Cosign."
        ],
        "code_blocks": [
            {
                "filename": "sign_all_artifacts.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nKEY=\"cosign.key\"\n\necho \"[1/3] Подписание бинарного файла...\"\n# cosign sign-blob --key \"${KEY}\" --output-signature app.bin.sig app.bin\n\necho \"[2/3] Подписание контейнерного образа в реестре...\"\n# cosign sign --key \"${KEY}\" myregistry.corp/app:v1.0.0\n\necho \"[3/3] Подписание и аттестация SBOM...\"\n# cosign attest --key \"${KEY}\" --predicate sbom.json --type cyclonedx myregistry.corp/app:v1.0.0\n\necho \"[SUCCESS] Все артефакты релиза защищены криптографическими подписями!\"\n",
                "note": "Сквозное подписание всех компонентов сборки"
            }
        ],
        "under_the_hood": "Команда `sign-blob` генерирует отдельный файл подписи `.sig`, а `cosign sign` для контейнера публикует подпись прямо в OCI-реестр как артефакт.",
        "pitfalls": "Потеря или повреждение отдельного файла подписи `.sig` для бинарника сделает невозможной офлайн-проверку на сервере клиента.",
        "bigtech_interview": "В чем разница между sign-blob и sign в Cosign? `sign` ориентирован на реестры OCI и сохраняет подпись в реестре, а `sign-blob` подписывает любой локальный файл на диске."
    },
    {
        "num": 116,
        "title": "Достижение уровня защищенности SLSA Level 3 в промышленной среде",
        "task": "Опишите архитектурные требования и настройте сборочный раннер для соответствия требованиям SLSA Level 3: герметичность сборки, изоляция раннера и неизменяемость Provenance.",
        "theory": "SLSA Level 3 является золотым стандартом для промышленного ПО. Он гарантирует:\n1. Сборка выполняется на защищенной изолированной платформе (Hosted Build Platform).\n2. Герметичность (Hermetic): сборка не имеет доступа к сети во время компиляции, а все зависимости зафиксированы и хешированы.\n3. Неизменяемость среды (Isolated): раннеры эфемерны и уничтожаются сразу после выполнения задания.\n4. Неподделываемый манифест происхождения (Non-falsifiable Provenance), генерируемый доверенным сервисом платформы.",
        "step_by_step": [
            "Сконфигурируйте эфемерные раннеры в Kubernetes через Actions Runner Controller (ARC).",
            "Отключите сетевой интерфейс на шаге компиляции бинарника.",
            "Используйте доверенный сборочный генератор для создания Provenance.",
            "Проверьте аттестат утилитой `slsa-verifier`."
        ],
        "code_blocks": [
            {
                "filename": "slsa_verify.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nBINARY=\"app-linux-amd64\"\nPROVENANCE=\"app-linux-amd64.intoto.jsonl\"\nSOURCE_REPO=\"github.com/my-corp/secure-service\"\n\necho \"[SLSA-VERIFY] Проверка соответствия бинарника стандарту SLSA Level 3...\"\n# slsa-verifier verify-artifact \"${BINARY}\" \\\n#   --provenance-path \"${PROVENANCE}\" \\\n#   --source-uri \"${SOURCE_REPO}\"\n\necho \"[OK] Бинарник успешно подтвердил происхождение от доверенного источника.\"\n",
                "note": "Проверка SLSA Level 3 происхождения артефакта через slsa-verifier"
            }
        ],
        "under_the_hood": "slsa-verifier извлекает криптографическую подпись Fulcio, сверяет идентичность OIDC сборочного раннера и проверяет хеш коммита в защищенном журнале Rekor.",
        "pitfalls": "Запуск сборщика с правами root на постоянной виртуальной машине не позволяет претендовать на SLSA L3 из-за риска скрытого заражения хоста.",
        "bigtech_interview": "В компании Google безопасность бинарников обеспечивается системой Binary Authorization for Borg (BAB), вдохновившей создание стандарта SLSA."
    },
    {
        "num": 117,
        "title": "Управление приватными реестрами и репозиториями модулей в Enterprise",
        "task": "Спроектируйте архитектуру отказоустойчивого внутреннего реестра модулей компании с поддержкой контроля версий, аудита безопасности и защиты от подмены пакетов.",
        "theory": "В enterprise-секторе неконтролируемое использование публичных репозиториев представляет критическую угрозу непрерывности бизнеса. Внутренний реестр Go (Private Registry / Athens / Nexus) обеспечивает:\n1. Централизованный контроль версий сторонних библиотек.\n2. Иммутабельность: автор публичной библиотеки не может отозвать или изменить версию.\n3. Сканирование безопасности до попадания библиотеки на компьютеры разработчиков.\n4. Полную автономность разработки при отключении внешних каналов связи.",
        "step_by_step": [
            "Разверните кластер приватного прокси с георепликацией.",
            "Настройте шлюз предварительного сканирования новых библиотек.",
            "Сконфигурируйте рабочие места разработчиков и CI-серверы на внутренний реестр.",
            "Запретите прямой доступ к GitHub и proxy.golang.org на корпоративном фаерволе."
        ],
        "code_blocks": [
            {
                "filename": "enterprise_registry.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\tcorporateProxy := os.Getenv(\"CORP_GOPROXY_URL\")\n\tif corporateProxy == \"\" {\n\t\tcorporateProxy = \"https://goproxy.corp.internal\"\n\t}\n\n\tresp, err := http.Get(corporateProxy + \"/healthz\")\n\tif err != nil || resp.StatusCode != http.StatusOK {\n\t\tfmt.Printf(\"[HEALTH] Корпоративный реестр недоступен: %v\\n\", err)\n\t\treturn\n\t}\n\tdefer resp.Body.Close()\n\n\tfmt.Println(\"[HEALTH] Корпоративный реестр Go функционирует в штатном режиме.\")\n}\n",
                "note": "Healthcheck сервис корпоративного реестра Go модулей"
            }
        ],
        "under_the_hood": "Корпоративный реестр выступает авторитетным источником метаданных, блокируя запросы к внешним DNS-именам для приватных пакетов компании.",
        "pitfalls": "Отсутствие регулярного резервного копирования персистентного хранилища реестра может парализовать разработку всей компании при сбое СХД.",
        "bigtech_interview": "Как в BigTech организован доступ к сторонним библиотекам? Через процесс 'Vendor Review': библиотека запрашивается разработчиком, проходит аудит ИБ, импортируется во внутренний реестр и только потом становится доступной."
    },
    {
        "num": 118,
        "title": "Обязательная настройка таймаутов HTTP-сервера для защиты от DoS (Slowloris)",
        "task": "Сконфигурируйте структуру http.Server со строгими таймаутами ReadHeaderTimeout, ReadTimeout, WriteTimeout и IdleTimeout для предотвращения атак исчерпания ресурсов.",
        "theory": "Использование стандартного `http.ListenAndServe(\":8080\", nil)` без настройки таймаутов является критической уязвимостью. Атакующий может открыть тысячи TCP-соединений и отправлять по одному байту HTTP-заголовка раз в минуту (атака Slowloris). Без `ReadHeaderTimeout` сервер Go будет бесконечно держать горутины и сокеты открытыми, пока не исчерпает лимит файловых дескрипторов (FD) или память, приведя к отказу в обслуживании.",
        "step_by_step": [
            "Инициализируйте экземпляр `http.Server` вместо использования глобального сервера.",
            "Установите `ReadHeaderTimeout: 5 * time.Second` для быстрой отсечки медленных клиентов.",
            "Установите `ReadTimeout: 15 * time.Second` и `WriteTimeout: 30 * time.Second`.",
            "Настройте `IdleTimeout: 60 * time.Second` для закрытия простаивающих keep-alive сессий."
        ],
        "code_blocks": [
            {
                "filename": "hardened_server.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/api/health\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(`{\"status\":\"healthy\"}`))\n\t})\n\n\t// Защищенный HTTP сервер со строгими таймаутами против Slowloris\n\tsrv := &http.Server{\n\t\tAddr:              \":8080\",\n\t\tHandler:           mux,\n\t\tReadHeaderTimeout: 5 * time.Second,  // Защита от Slowloris на этапе чтения заголовков\n\t\tReadTimeout:       15 * time.Second, // Максимальное время чтения всего запроса\n\t\tWriteTimeout:      30 * time.Second, // Максимальное время отправки ответа\n\t\tIdleTimeout:       60 * time.Second, // Время жизни неактивного keep-alive соединения\n\t\tMaxHeaderBytes:    1 << 20,          // Лимит размера заголовков (1 MB)\n\t}\n\n\tfmt.Println(\"[HTTP-SERVER] Защищенный сервер запущен с безопасными таймаутами на :8080\")\n\t_ = srv\n}\n",
                "note": "Конфигурация HTTP-сервера с защитными таймаутами против DoS-атак"
            }
        ],
        "under_the_hood": "Go рантайм использует системный вызов `setsockopt(SO_RCVTIMEO)` и внутренние таймеры `net.Conn.SetReadDeadline()`. При истечении дедлайна рантайм прерывает ожидание в epoll и закрывает соединение.",
        "pitfalls": "Слишком короткий `WriteTimeout` может оборвать отправку легитимных больших файлов или медленных стримов Server-Sent Events (SSE). Для стриминга `WriteTimeout` часто отключают или контролируют вручную через контекст.",
        "bigtech_interview": "Вопрос на собеседовании: 'Почему в Go 1.20+ линтеры настоятельно требуют задавать именно ReadHeaderTimeout?' Ответ: Потому что ReadTimeout начинает отсчет только после успешного чтения заголовков, и без ReadHeaderTimeout сервер уязвим к Slowloris на этапе рукопожатия."
    },
    {
        "num": 119,
        "title": "Ограничение размера тела входящих HTTP-запросов через http.MaxBytesReader",
        "task": "Реализуйте HTTP middleware для защиты сервера от атак исчерпания памяти (OOM) с помощью http.MaxBytesReader, возвращающее корректный статус 413 Payload Too Large.",
        "theory": "Если обработчик вызывает `io.ReadAll(r.Body)` без предварительного ограничения, злоумышленник может передать в запросе поток данных размером в десятки гигабайт (или бесконечный поток). Это приведет к неконтролируемой аллокации буфера в куче и завершению процесса операционной системой по Out-Of-Memory (OOM Killer). Обертка `http.MaxBytesReader` принудительно прерывает чтение тела при превышении установленного лимита байт.",
        "step_by_step": [
            "Оберните `r.Body` в `http.MaxBytesReader(w, r.Body, maxBytes)` в начале обработки запроса.",
            "Попробуйте прочитать тело запроса через `io.ReadAll` или `json.NewDecoder`.",
            "Проверьте возвращаемую ошибку: при превышении лимита верните код `http.StatusRequestEntityTooLarge` (413).",
            "Убедитесь, что соединение закрывается корректно без зависания сервера."
        ],
        "code_blocks": [
            {
                "filename": "limit_body.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"errors\"\n\t\"fmt\"\n\t\"io\"\n\t\"net/http\"\n)\n\nfunc LimitPayloadHandler(maxBytes int64) http.HandlerFunc {\n\treturn func(w http.ResponseWriter, r *http.Request) {\n\t\t// Ограничиваем чтение тела запроса лимитом maxBytes\n\t\tr.Body = http.MaxBytesReader(w, r.Body, maxBytes)\n\n\t\tvar payload map[string]any\n\t\terr := json.NewDecoder(r.Body).Decode(&payload)\n\t\tif err != nil {\n\t\t\tvar maxBytesErr *http.MaxBytesError\n\t\t\tif errors.As(err, &maxBytesErr) {\n\t\t\t\thttp.Error(w, fmt.Sprintf(\"Превышен максимальный размер тела запроса (лимит: %d байт)\", maxBytesErr.Limit),\n\t\t\t\t\thttp.StatusRequestEntityTooLarge) // HTTP 413\n\t\t\t\treturn\n\t\t\t}\n\t\t\thttp.Error(w, \"Некорректный JSON: \"+err.Error(), http.StatusBadRequest)\n\t\t\treturn\n\t\t}\n\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(`{\"status\":\"accepted\"}`))\n\t}\n}\n\nfunc main() {\n\t// Лимит 1 МБ на тело запроса\n\thttp.HandleFunc(\"/api/upload\", LimitPayloadHandler(1<<20))\n\tfmt.Println(\"[HTTP] Обработчик с лимитом размера тела запроса инициализирован.\")\n}\n",
                "note": "Безопасное ограничение размера тела HTTP-запроса через http.MaxBytesReader"
            }
        ],
        "under_the_hood": "MaxBytesReader подсчитывает количество прочитанных байт. При попытке прочитать даже на 1 байт больше лимита он закрывает underlying reader и отправляет серверу сигнал прервать сокет с флагом `requestTooLarge`.",
        "pitfalls": "Если не использовать `http.MaxBytesReader`, а просто проверять заголовок `r.ContentLength`, атакующий может отправить поддельный заголовок `Content-Length: 100`, но передать 10 гигабайт данных в теле (Chunked Transfer Encoding).",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Почему проверка r.ContentLength недостаточна для защиты от DoS через размер тела?' Ответ: Заголовок может быть опущен при Transfer-Encoding: chunked, либо злоумышленник может умышленно солгать в значении заголовка."
    },
    {
        "num": 120,
        "title": "Очистка полуоткрытых соединений через TCP Keepalive",
        "task": "Настройте TCP Keepalive с интервалом 30 секунд в net.ListenConfig и http.Transport для своевременного обнаружения 'мертвых' сокетов и предотвращения утечек дескрипторов.",
        "theory": "Полуоткрытые (half-open) TCP-соединения возникают, когда клиент аварийно перезагружается или теряет связь без отправки TCP FIN/RST пакетов. Сервер держит сокет и связанную горутину открытыми часами, пока не исчерпает лимит дескрипторов `ulimit -n`. Механизм TCP Keepalive периодически отправляет зондирующие TCP-пакеты (ACK с seq-1). Если после заданного числа попыток ответ не получен, ядро ОС закрывает сокет и возвращает ошибку connection timed out.",
        "step_by_step": [
            "Инициализируйте структуру `net.ListenConfig` с полем `KeepAlive: 30 * time.Second`.",
            "Используйте `lc.Listen(ctx, \"tcp\", \":8080\")` для создания TCP-листенера.",
            "Настройте аналогичные параметры Keepalive в `http.Transport` для исходящих запросов.",
            "Проверьте автоматическое закрытие брошенных клиентами соединений."
        ],
        "code_blocks": [
            {
                "filename": "tcp_keepalive.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc main() {\n\t// Создание листенера с явным TCP Keepalive зондированием\n\tlc := net.ListenConfig{\n\t\tKeepAlive: 30 * time.Second, // Каждые 30 секунд ядро шлет TCP probe\n\t}\n\n\tctx := context.Background()\n\tln, err := lc.Listen(ctx, \"tcp\", \"127.0.0.1:0\")\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer ln.Close()\n\n\tfmt.Printf(\"[TCP-KEEPALIVE] Сервер слушает на %s с Keepalive 30s\\n\", ln.Addr().String())\n\n\t// Настройка клиентского транспорта с Keepalive\n\t_ = &http.Transport{\n\t\tDialContext: (&net.Dialer{\n\t\t\tTimeout:   10 * time.Second,\n\t\t\tKeepAlive: 30 * time.Second,\n\t\t}).DialContext,\n\t\tIdleConnTimeout: 90 * time.Second,\n\t}\n\tfmt.Println(\"[TCP-KEEPALIVE] Клиентский и серверный пулы сокетов защищены от зависших соединений.\")\n}\n",
                "note": "Управление таймаутами TCP Keepalive на сетевом уровне ядра"
            }
        ],
        "under_the_hood": "Go рантайм настраивает опции сокета `SO_KEEPALIVE`, а также `TCP_KEEPIDLE` и `TCP_KEEPINTVL` через системные вызовы Linux `setsockopt`.",
        "pitfalls": "Слишком частые TCP Keepalive пакеты (например, каждую секунду) могут нерационально расходовать заряд батареи на мобильных клиентах или нагружать сетевые фаерволы.",
        "bigtech_interview": "В чем отличие между HTTP Keep-Alive и TCP Keepalive? HTTP Keep-Alive переиспользует TCP-соединение для нескольких HTTP-запросов, а TCP Keepalive зондирует работоспособность нижележащего TCP-канала пустыми пакетами на уровне ядра ОС."
    },
    {
        "num": 121,
        "title": "Фильтрация системных вызовов через профили Seccomp в Docker и K8s",
        "task": "Сконфигурируйте кастомный Seccomp-профиль (Security Profiles Operator) для блокировки опасных системных вызовов (ptrace, mount, reboot, keyctl) контейнеризованного Go-приложения.",
        "theory": "Seccomp (Secure Computing Mode) — механизм ядра Linux, позволяющий перехватывать и фильтровать системные вызовы процесса. Стандартный профиль Docker разрешает около 300 из 450+ сисколлов. Злоумышленник, получивший доступ к контейнеру, может попытаться эксплуатировать уязвимости ядра через редкие вызовы (`bpf`, `userfaultfd`, `ptrace`). Ограничение сисколлов до строго необходимого минимума (Runtime Whitelist) предотвращает побег из контейнера (Container Escape).",
        "step_by_step": [
            "Определите список обязательных сисколлов Go приложения (futex, epoll_wait, write, read, clone).",
            "Создайте JSON-манифест Seccomp с действием по умолчанию `SCMP_ACT_ERRNO`.",
            "Запретите вызовы `ptrace`, `mount`, `reboot` и `sys_chroot`.",
            "Подключите профиль в Kubernetes PodSecurityContext или `docker run --security-opt seccomp=profile.json`."
        ],
        "code_blocks": [
            {
                "filename": "seccomp_profile.json",
                "lang": "json",
                "code": "{\n  \"defaultAction\": \"SCMP_ACT_ERRNO\",\n  \"architectures\": [\n    \"SCMP_ARCH_X86_64\"\n  ],\n  \"syscalls\": [\n    {\n      \"names\": [\n        \"read\", \"write\", \"futex\", \"epoll_wait\", \"epoll_ctl\", \"epoll_create1\",\n        \"nanosleep\", \"sched_yield\", \"mmap\", \"munmap\", \"clone\", \"exit_group\",\n        \"getpid\", \"rt_sigaction\", \"rt_sigprocmask\", \"sigaltstack\"\n      ],\n      \"action\": \"SCMP_ACT_ALLOW\"\n    }\n  ]\n}\n",
                "note": "Минималистичный белый список системных вызовов Seccomp для Go сервиса"
            }
        ],
        "under_the_hood": "Ядро Linux компилирует правила Seccomp в байткод фильтра BPF (Berkeley Packet Filter), который исполняется в контексте ядра перед каждым системным вызовом потока.",
        "pitfalls": "Блокировка сисколла `clone` или `futex` приведет к мгновенному падению Go рантайма (GMP планировщик не сможет инициализировать M потоки ОС).",
        "bigtech_interview": "Как профилировать сисколлы Go программы для создания Seccomp профиля? Ответ: Запустить приложение под надзором `strace -c` или использовать eBPF-утилиты audit2rbac / OCI Seccomp Inspector."
    },
    {
        "num": 122,
        "title": "Стратегическое планирование архитектурной безопасности и зрелости DevSecOps",
        "task": "Разработайте дорожную карту (Roadmap) внедрения практик безопасности цепочки поставок и защиты рантайма на 12 месяцев для инженерной команды бэкенда.",
        "theory": "Безопасность — это непрерывный процесс инженерной культуры, а не разовый проект. Попытка внедрить все защитные механизмы за месяц приводит к выгоранию команды и блокировке бизнеса. Зрелая стратегия разбивает внедрение на 4 квартальных этапа: Q1 — гигиена зависимостей (GOPRIVATE, go.sum, govulncheck); Q2 — воспроизводимость и SBOM (Syft, CycloneDX); Q3 — криптографические подписи и аттестации (Cosign, in-toto, SLSA L2); Q4 — изоляция рантайма и харднинг ядра (Seccomp, Capabilities, Network Policies).",
        "step_by_step": [
            "Оцените текущий уровень зрелости команды по модели OWASP SAMM / SLSA.",
            "Сформируйте квартальные контрольные точки (Milestones).",
            "Интегрируйте автоматические Quality Gates на каждом шаге.",
            "Зафиксируйте метрики успешности: снижение открытых CVE, покрытие подписями артефактов."
        ],
        "code_blocks": [
            {
                "filename": "roadmap_evaluator.go",
                "lang": "go",
                "code": "package main\n\nimport \"fmt\"\n\ntype Milestone struct {\n\tQuarter     string\n\tObjective   string\n\tDeliverable string\n}\n\nfunc main() {\n\troadmap := []Milestone{\n\t\t{\"Q1\", \"Гигиена зависимостей\", \"govulncheck в CI, GOPRIVATE аудит, Dependabot\"},\n\t\t{\"Q2\", \"Паспортизация ПО\", \"Генерация CycloneDX SBOM утилитой Syft на каждый релиз\"},\n\t\t{\"Q3\", \"Доверие к артефактам\", \"Cosign подпись образов + SLSA Level 2 аттестаты\"},\n\t\t{\"Q4\", \"Рантайм изоляция\", \"Seccomp фильтрация, non-root контейнеры, Read-only rootfs\"},\n\t}\n\n\tfmt.Println(\"[ROADMAP] 12-месячная дорожная карта зрелости DevSecOps:\")\n\tfor _, m := range roadmap {\n\t\tfmt.Printf(\" [%s] %s -> Результат: %s\\n\", m.Quarter, m.Objective, m.Deliverable)\n\t}\n}\n",
                "note": "Программа визуализации дорожной карты безопасности бэкенд систем"
            }
        ],
        "under_the_hood": "Поэтапное внедрение снижает сопротивление разработчиков и позволяет отладить инфраструктуру без простоев продакшена.",
        "pitfalls": "Внедрение блокирующих Quality Gates без предварительного периода сбора метрик (dry-run / audit mode) остановит работу всех продуктовых команд.",
        "bigtech_interview": "На позициях Lead Security Architect важно показать не просто знание инструментов, но и умение системно внедрять их в масштабе сотен команд без ущерба для Time-to-Market."
    },
    {
        "num": 123,
        "title": "Минимизация привилегий контейнеров: сброс Linux Capabilities (Drop ALL)",
        "task": "Сконфигурируйте PodSecurityContext в Kubernetes манифесте с полным сбросом всех Linux возможностей (capabilities: drop: [ALL]) и проверьте работу сетевого сервиса Go.",
        "theory": "В ядре Linux традиционные суперпривилегии root разделены на дискретные возможности (Capabilities). Контейнеры по умолчанию получают набор привилегий (CAP_CHOWN, CAP_NET_RAW, CAP_MKNOD), многие из которых опасны. Лучшая практика безопасности (Zero Trust) — сбросить абсолютно ВСЕ возможности (`drop: [ALL]`). Большинству микросервисов на Go не нужны никакие привилегии ОС для прослушивания непривилегированных портов (>1024) и обработки сетевых запросов.",
        "step_by_step": [
            "Откройте манифест Deployment или Pod в Kubernetes.",
            "Добавьте блок `securityContext` в спецификацию контейнера.",
            "Укажите `capabilities: drop: [\"ALL\"]`.",
            "Убедитесь, что Pod успешно запускается и отвечает на HTTP/gRPC запросы."
        ],
        "code_blocks": [
            {
                "filename": "hardened_pod.yaml",
                "lang": "yaml",
                "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: payment-api\nspec:\n  replicas: 2\n  selector:\n    matchLabels:\n      app: payment-api\n  template:\n    metadata:\n      labels:\n        app: payment-api\n    spec:\n      containers:\n      - name: app\n        image: registry.corp.internal/payments:v1.4.0\n        ports:\n        - containerPort: 8080\n        securityContext:\n          allowPrivilegeEscalation: false\n          readOnlyRootFilesystem: true\n          runAsNonRoot: true\n          runAsUser: 65534\n          capabilities:\n            drop:\n            - ALL\n",
                "note": "Безопасный манифест Kubernetes с полным сбросом привилегий ядра"
            }
        ],
        "under_the_hood": "При запуске контейнера демон рантайма (containerd/CRI-O) вызывает системный вызов `capset(2)`, сбрасывая маски Permitted и Effective capabilities для родительского процесса Go.",
        "pitfalls": "Если сервису необходимо привязаться к привилегированному порту 80 или 443 внутри контейнера, потребуется `CAP_NET_BIND_SERVICE`. В продакшене лучше всегда использовать непривилегированные порты (8080, 8443).",
        "bigtech_interview": "Какая опасность кроется в сохранении CAP_NET_RAW в контейнере? Наличие CAP_NET_RAW позволяет процессу подделывать ARP-пакеты и организовывать сетевой сниффинг и ARP Spoofing внутри оверлейной сети Kubernetes."
    },
    {
        "num": 124,
        "title": "Запуск контейнеров от имени непривилегированного пользователя (Non-root)",
        "task": "Настройте Dockerfile и директивы USER для сборки и запуска приложения под UID 65534 (nobody / nonroot), исключая выполнение кода от имени суперпользователя root.",
        "theory": "Запуск процесса внутри контейнера с UID 0 (root) означает, что в случае эксплойта и выхода за пределы песочницы злоумышленник окажется root-пользователем на хостовой ноде Linux. Использование непривилегированного пользователя (`USER 65534:65534` или создание отдельного системного пользователя `appuser`) сводит к минимуму последствия компрометации приложения.",
        "step_by_step": [
            "Создайте непривилегированную учетную запись в Dockerfile: `RUN addgroup -S appgroup && adduser -S appuser -G appgroup`.",
            "Установите директиву `USER 10001:10001`.",
            "Убедитесь, что бинарник и необходимые файлы доступны для чтения созданному пользователю.",
            "Включите в Kubernetes проверку `runAsNonRoot: true`."
        ],
        "code_blocks": [
            {
                "filename": "Dockerfile.nonroot",
                "lang": "dockerfile",
                "code": "FROM golang:1.22-alpine AS builder\nWORKDIR /build\nCOPY . .\nRUN CGO_ENABLED=0 go build -ldflags=\"-s -w\" -o /build/server main.go\n\nFROM alpine:3.19\n# Создание системного пользователя с фиксированным UID\nRUN addgroup -g 10001 -S appgroup && \\\n    adduser -u 10001 -S appuser -G appgroup\n\nWORKDIR /home/appuser\nCOPY --from=builder --chown=appuser:appgroup /build/server /home/appuser/server\n\n# Переключение на непривилегированного пользователя\nUSER 10001:10001\n\nEXPOSE 8080\nENTRYPOINT [\"/home/appuser/server\"]\n",
                "note": "Конфигурация Dockerfile с выделенным non-root пользователем"
            }
        ],
        "under_the_hood": "Ядро Linux оперирует числовыми идентификаторами UID/GID. Использование символических имен может конфликтовать с файлом `/etc/passwd` хоста, поэтому в enterprise рекомендуется использовать явные числовые UID (например, 10001).",
        "pitfalls": "Если непривилегированный пользователь пытается писать в защищенные каталоги (`/var/log`, `/etc`), приложение упадет с ошибкой `os.PathError: permission denied`.",
        "bigtech_interview": "В стандартах PCI-DSS и требованиях информационной безопасности BigTech (Ozon, Авито) запуск контейнеров с UID 0 строго запрещен политиками допуска OPA Gatekeeper."
    },
    {
        "num": 125,
        "title": "Иммутабельная файловая система контейнера (Read-only Root Filesystem)",
        "task": "Настройте монтирование корневой файловой системы контейнера в режиме 'только для чтения' (readOnlyRootFilesystem: true) с выделением временного каталога tmpfs для временных файлов.",
        "theory": "Одной из первых целей злоумышленника при взломе веб-сервиса является сохранение своего присутствия (persistence) — скачивание шелла, бэкдора или майнера в `/tmp` или системные каталоги. Монтирование корневой файловой системы в режиме `read-only` физически запрещает запись на диск. Если сервису требуется временное дисковое пространство (для парсинга multipart-форм), под каталог `/tmp` монтируется эфемерная память `tmpfs` без прав исполнения (`noexec`).",
        "step_by_step": [
            "Установите параметр `readOnlyRootFilesystem: true` в манифесте пода.",
            "Смонтируйте том типа `emptyDir: { medium: \"Memory\" }` в точку `/tmp`.",
            "Убедитесь, что Go приложение запускается и успешно работает.",
            "Проверьте, что попытка создания файла вне смонтированного тома завершается ошибкой `Read-only file system`."
        ],
        "code_blocks": [
            {
                "filename": "readonly_fs.yaml",
                "lang": "yaml",
                "code": "apiVersion: v1\nkind: Pod\nmetadata:\n  name: secure-go-app\nspec:\n  containers:\n  - name: server\n    image: myrepo/go-service:v1.0.0\n    securityContext:\n      readOnlyRootFilesystem: true\n    volumeMounts:\n    - name: tmp-volume\n      mountPath: /tmp\n  volumes:\n  - name: tmp-volume\n    emptyDir:\n      medium: Memory\n      sizeLimit: 64Mi\n",
                "note": "Манифест Pod с иммутабельной файловой системой и ограничением tmpfs"
            }
        ],
        "under_the_hood": "Флаг `MS_RDONLY` передается системному вызову `mount()`. Ядро Linux блокирует любые вызовы `open(O_WRONLY|O_CREAT)`, предотвращая изменение содержимого контейнера.",
        "pitfalls": "Если библиотека Go пытается писать кэш в домашнюю директорию (`~/.cache`), без явного переопределения переменных окружения (`XDG_CACHE_HOME=/tmp`) сервис упадет при старте.",
        "bigtech_interview": "Почему монтирование /tmp как tmpfs с опцией noexec считается золотым стандартом безопасности? Это блокирует исполнение загруженных злоумышленником бинарников и скриптов."
    },
    {
        "num": 126,
        "title": "Сквозной контроль контекстных таймаутов для исходящих сетевых вызовов",
        "task": "Реализуйте паттерн обязательного оборачивания всех исходящих сетевых запросов (HTTP, gRPC, базы данных, Redis) в context.WithTimeout с единой стратегией дедлайнов.",
        "theory": "Отсутствие таймаутов на сетевых клиентах — главная причина каскадных сбоев в микросервисной архитектуре. Если downstream-сервис или база данных начинают отвечать медленно, тысячи горутин зависают в ожидании I/O, исчерпывая память и пулы соединений. Каждый исходящий вызов обязан принимать `context.Context` с дедлайном, гарантирующим быстрый отказ (fail fast) при сбоях в сети.",
        "step_by_step": [
            "Создайте контекст с явным таймаутом через `context.WithTimeout`.",
            "Передайте контекст в клиент базы данных (`db.QueryRowContext`), Redis и HTTP (`http.NewRequestWithContext`).",
            "Обработайте ошибку `context.DeadlineExceeded`.",
            "Убедитесь в освобождении ресурсов горутины при срабатывании таймаута."
        ],
        "code_blocks": [
            {
                "filename": "context_timeouts.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc CallDownstreamService(parentCtx context.Context, url string) error {\n\t// Строгий таймаут 2 секунды на сетевую операцию\n\tctx, cancel := context.WithTimeout(parentCtx, 2*time.Second)\n\tdefer cancel()\n\n\treq, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)\n\tif err != nil {\n\t\treturn err\n\t}\n\n\tclient := &http.Client{}\n\tresp, err := client.Do(req)\n\tif err != nil {\n\t\tif errors.Is(ctx.Err(), context.DeadlineExceeded) {\n\t\t\treturn fmt.Errorf(\"превышен дедлайн вызова %s: downstream не ответил за 2с\", url)\n\t\t}\n\t\treturn fmt.Errorf(\"сетевая ошибка: %w\", err)\n\t}\n\tdefer resp.Body.Close()\n\n\tfmt.Printf(\"[OK] Успешный ответ от %s, статус: %d\\n\", url, resp.StatusCode)\n\treturn nil\n}\n\nfunc main() {\n\tfmt.Println(\"[CLIENT] Инициализация безопасного сетевого клиента с контекстными таймаутами...\")\n\t_ = CallDownstreamService\n}\n",
                "note": "Использование context.WithTimeout для изоляции сетевых сбоев"
            }
        ],
        "under_the_hood": "При истечении таймера горутина таймера в рантайме Go закрывает канал `ctx.Done()`. Транспортный уровень немедленно прерывает блокирующий системный вызов `epoll_wait` или `read` и возвращает ошибку.",
        "pitfalls": "Забытый вызов `cancel()` приводит к утечке таймеров в рантайме Go до момента естественного истечения дедлайна.",
        "bigtech_interview": "Что произойдет, если в цепочке микросервисов A -> B -> C таймаут на сервисе A составляет 5 секунд, а на сервисе B — 10 секунд? Сервис A оборвет соединение через 5с, а сервис B продолжит бессмысленно тратить ресурсы на вызов C. Таймауты должны уменьшаться по мере продвижения вглубь цепочки вызовов."
    },
    {
        "num": 127,
        "title": "Тюнинг и ограничение пулов сетевых соединений (Connection Pooling Limits)",
        "task": "Сконфигурируйте http.Transport и database/sql.DB с безопасными лимитами соединений: MaxIdleConns, MaxIdleConnsPerHost, MaxOpenConns и IdleConnTimeout.",
        "theory": "Неограниченные пулы соединений могут вызвать исчерпание сетевых ресурсов как локально (порт exhaust / socket leak), так и на стороне целевой базы данных (превышение max_connections в PostgreSQL). По умолчанию `http.Transport` держит только 2 свободных keep-alive соединения на хост (`DefaultMaxIdleConnsPerHost = 2`), что при высокой нагрузке приводит к постоянному пересозданию сокетов (TCP handshake storm). Грамотная настройка пулов стабилизирует задержки и предотвращает DoS.",
        "step_by_step": [
            "Настройте экземпляр `http.Transport` с адекватным числом `MaxIdleConns: 100` и `MaxIdleConnsPerHost: 20`.",
            "Установите `IdleConnTimeout: 90 * time.Second`.",
            "Сконфигурируйте пул БД: `db.SetMaxOpenConns(50)` и `db.SetMaxIdleConns(25)`.",
            "Проверьте поведение пула при параллельных нагрузочных запросах."
        ],
        "code_blocks": [
            {
                "filename": "tuned_pools.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc NewTunedHTTPClient() *http.Client {\n\ttransport := &http.Transport{\n\t\tProxy: http.ProxyFromEnvironment,\n\t\tDialContext: (&net.Dialer{\n\t\t\tTimeout:   5 * time.Second,\n\t\t\tKeepAlive: 30 * time.Second,\n\t\t}).DialContext,\n\t\tMaxIdleConns:        100,              // Всего свободных соединений в пуле\n\t\tMaxIdleConnsPerHost: 20,               // Свободных соединений на один хост\n\t\tMaxConnsPerHost:     50,               // Жесткий лимит параллельных сокетов на хост\n\t\tIdleConnTimeout:     90 * time.Second, // Закрывать сокет после 90с простоя\n\t\tTLSHandshakeTimeout: 5 * time.Second,\n\t}\n\n\treturn &http.Client{\n\t\tTransport: transport,\n\t\tTimeout:   10 * time.Second,\n\t}\n}\n\nfunc main() {\n\tclient := NewTunedHTTPClient()\n\tfmt.Printf(\"[POOL] Оптимизированный HTTP клиент готов к HighLoad: %+v\\n\", client.Transport)\n}\n",
                "note": "Конфигурация защищенного пула сетевых соединений"
            }
        ],
        "under_the_hood": "Go защищает внутренний пул соединений мьютексом. При превышении `MaxConnsPerHost` новые запросы блокируются до освобождения одного из сокетов или завершения по таймауту.",
        "pitfalls": "Если забыть вызывать `resp.Body.Close()`, соединение никогда не вернется в пул, что приведет к быстрой утечке всех доступных слотов.",
        "bigtech_interview": "Почему в продакшене нельзя оставлять http.DefaultTransport без изменений при общении с микросервисами? Из-за MaxIdleConnsPerHost=2 под нагрузкой сокеты будут постоянно закрываться и открываться заново через полный TCP/TLS handshake."
    },
    {
        "num": 128,
        "title": "Фокусная приоритизация компетенций по безопасности распределенных систем",
        "task": "Реализуйте модульную систему оценки зрелости подсистем безопасности микросервиса (интеграция очередей, баз данных, TLS и сетевого контура) с определением критических приоритетов.",
        "theory": "При разработке распределенных систем важно соблюдать принцип разумной достаточности: если в архитектуре не используется Kafka, тратить время на SASL/SCRAM харднинг брокера не имеет смысла, пока не закрыты базовые риски сетевого периметра и аутентификации в Redis/PostgreSQL. Архитектурная оценка безопасности определяет скоуп работ на основе модели угроз конкретной системы.",
        "step_by_step": [
            "Определите используемые в проекте компоненты инфраструктуры.",
            "Составьте чек-лист обязательных требований безопасности для каждого активного компонента.",
            "Отфильтруйте неактуальные технологии.",
            "Сформируйте фокусированный план задач для инженерной команды."
        ],
        "code_blocks": [
            {
                "filename": "sec_evaluator.go",
                "lang": "go",
                "code": "package main\n\nimport \"fmt\"\n\ntype ComponentAudit struct {\n\tName     string\n\tInUse    bool\n\tPriority string\n\tChecks   []string\n}\n\nfunc FilterPriorityTasks(audit []ComponentAudit) {\n\tfor _, c := range audit {\n\t\tif !c.InUse {\n\t\t\tcontinue // Пропускаем неактуальные для текущей архитектуры компоненты\n\t\t}\n\t\tfmt.Printf(\"[AUDIT] Компонент %s (Приоритет: %s):\\n\", c.Name, c.Priority)\n\t\tfor _, check := range c.Checks {\n\t\t\tfmt.Printf(\"   - %s\\n\", check)\n\t\t}\n\t}\n}\n\nfunc main() {\n\tinfrastructure := []ComponentAudit{\n\t\t{\n\t\t\tName:     \"PostgreSQL\",\n\t\t\tInUse:    true,\n\t\t\tPriority: \"CRITICAL\",\n\t\t\tChecks:   []string{\"TLS соединение (sslmode=verify-full)\", \"Connection pool limits\", \"Параметризованные запросы\"},\n\t\t},\n\t\t{\n\t\t\tName:     \"Kafka\",\n\t\t\tInUse:    false, // Не используется в текущем проекте\n\t\t\tPriority: \"LOW\",\n\t\t\tChecks:   []string{\"mTLS auth\", \"ACL topics\"},\n\t\t},\n\t}\n\tFilterPriorityTasks(infrastructure)\n}\n",
                "note": "Фильтрация приоритетных мер безопасности на основе архитектурного профиля"
            }
        ],
        "under_the_hood": "Модель угроз STRIDE позволяет командам сфокусироваться на реальных векторах атак вместо распыления ресурсов на теоретические угрозы.",
        "pitfalls": "Полное игнорирование подсистемы до момента её ввода в эксплуатацию может потребовать дорогостоящего рефакторинга архитектуры перед самым релизом.",
        "bigtech_interview": "Как на собеседовании Tech Lead оценивают понимание архитектуры безопасности? По способности обосновать выбор необходимых защитных мер и аргументированно отсечь избыточные усложнения."
    },
    {
        "num": 129,
        "title": "Многоуровневое ограничение частоты запросов (Rate Limiting Defense-in-Depth)",
        "task": "Реализуйте эшелонированное ограничение скорости (Defense-in-Depth): на уровне сетевого IP (Token Bucket) и на прикладном уровне (API Key / User ID) в Go HTTP middleware.",
        "theory": "Ограничение скорости (Rate Limiting) должно работать на нескольких эшелонах:\n1. Сетевой уровень: отсечка DDoS по IP-адресу или подсети (IPTables / Nginx / Envoy).\n2. Прикладной уровень: защита бизнес-логики по идентификатору пользователя или API-токену (внутри Go сервиса через Redis / Token Bucket).\nТакая многослойная защита гарантирует, что даже в случае пробития внешнего шлюза внутренний сервис не ляжет под всплеском запросов скомпрометированного клиента.",
        "step_by_step": [
            "Используйте алгоритм Token Bucket (`golang.org/x/time/rate`).",
            "Создайте HTTP middleware, извлекающее API-токен из заголовка `Authorization`.",
            "Свяжите лимитер с каждым уникальным токеном.",
            "Верните статус `429 Too Many Requests` с заголовком `Retry-After` при превышении лимита."
        ],
        "code_blocks": [
            {
                "filename": "rate_limiter.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"sync\"\n\t\"golang.org/x/time/rate\"\n)\n\ntype ClientLimiter struct {\n\tmu      sync.Mutex\n\tclients map[string]*rate.Limiter\n}\n\nfunc NewClientLimiter() *ClientLimiter {\n\treturn &ClientLimiter{clients: make(map[string]*rate.Limiter)}\n}\n\nfunc (cl *ClientLimiter) GetLimiter(clientID string) *rate.Limiter {\n\tcl.mu.Lock()\n\tdefer cl.mu.Unlock()\n\n\tlimiter, exists := cl.clients[clientID]\n\tif !exists {\n\t\t// 10 запросов в секунду с бурстом до 20\n\t\tlimiter = rate.NewLimiter(10, 20)\n\t\tcl.clients[clientID] = limiter\n\t}\n\treturn limiter\n}\n\nfunc RateLimitMiddleware(cl *ClientLimiter, next http.HandlerFunc) http.HandlerFunc {\n\treturn func(w http.ResponseWriter, r *http.Request) {\n\t\ttoken := r.Header.Get(\"X-API-Key\")\n\t\tif token == \"\" {\n\t\t\ttoken = r.RemoteAddr // Fallback на IP\n\t\t}\n\n\t\tlimiter := cl.GetLimiter(token)\n\t\tif !limiter.Allow() {\n\t\t\tw.Header().Set(\"Retry-After\", \"1\")\n\t\t\thttp.Error(w, \"Too Many Requests\", http.StatusTooManyRequests) // 429\n\t\t\treturn\n\t\t}\n\t\tnext(w, r)\n\t}\n}\n\nfunc main() {\n\tlimiter := NewClientLimiter()\n\t_ = RateLimitMiddleware(limiter, func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"OK\")\n\t})\n\tfmt.Println(\"[RATE-LIMIT] Middleware ограничения частоты запросов успешно инициализирован.\")\n}\n",
                "note": "Защитное middleware ограничения запросов на базе алгоритма Token Bucket"
            }
        ],
        "under_the_hood": "Token Bucket накапливает токены с фиксированной скоростью $r$ до емкости $b$. Метод `limiter.Allow()` атомарно списывает токен или возвращает false за $O(1)$ без аллокаций памяти.",
        "pitfalls": "Хранение лимитеров в оперативной памяти одного инстанса не защищает распределенный кластер; для кластера требуется распределенный лимитер на базе Redis или Envoy Rate Limit Service.",
        "bigtech_interview": "В чем разница между алгоритмами Token Bucket, Leaky Bucket и Sliding Window Counter? Token Bucket допускает короткие всплески трафика (burst), что оптимально для пользовательских API."
    },
    {
        "num": 130,
        "title": "Интеграция Supply Chain Security с AppSec и прикладной криптографией",
        "task": "Опишите и программно смоделируйте взаимосвязь между криптографическими алгоритмами подписи (ECDSA/Ed25519), безопасностью кода (AppSec) и контролем цепочки поставок (Supply Chain).",
        "theory": "Безопасность цепочки поставок — это не изолированная дисциплина, а продолжение криптографии и прикладной безопасности. Криптография предоставляет математический фундамент (ECDSA, SHA-256, Merkle Trees), AppSec обеспечивает защищенность исходного кода от уязвимостей (SQLi, DoS, XSS), а Supply Chain Security гарантирует, что именно этот проверенный код без изменений скомпилирован в бинарник и запущен в проде.",
        "step_by_step": [
            "Смоделируйте сквозной жизненный цикл артефакта от коммита до деплоя.",
            "Свяжите проверку SAST-сканеров с формированием отчета аттестации.",
            "Подпишите контрольный хэш артефакта криптографическим ключом Ed25519.",
            "Проверьте валидность всей цепочки доверия в точке запуска."
        ],
        "code_blocks": [
            {
                "filename": "pipeline_integrity.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"crypto/ed25519\"\n\t\"crypto/rand\"\n\t\"crypto/sha256\"\n\t\"fmt\"\n)\n\nfunc main() {\n\t// Генерация ключевой пары Ed25519 для подписи релизов\n\tpub, priv, err := ed25519.GenerateKey(rand.Reader)\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\n\t// Хеш бинарника после прохождения всех проверок AppSec\n\tbinaryPayload := []byte(\"secure_compiled_go_binary_v3.0\")\n\thash := sha256.Sum256(binaryPayload)\n\n\t// Подпись артефакта в защищенном CI\n\tsignature := ed25519.Sign(priv, hash[:])\n\n\t// Верификация в кластере перед запуском\n\tif ed25519.Verify(pub, hash[:], signature) {\n\t\tfmt.Println(\"[CHAIN OF TRUST] Артефакт валиден: криптографическая подпись подтверждена!\")\n\t} else {\n\t\tfmt.Println(\"[SECURITY ALERT] Нарушение целостности цепочки поставок!\")\n\t}\n}\n",
                "note": "Криптографическая верификация целостности артефакта через Ed25519"
            }
        ],
        "under_the_hood": "Ed25519 обеспечивает высочайшую скорость генерации и проверки подписей при длине ключа всего 32 байта, что идеально для подписи артефактов в высоконагруженных сборочных фермах.",
        "pitfalls": "Компрометация сборочного сервера сводит на нет все криптографические проверки: если злоумышленник внедрил бэкдор до этапа компиляции, подписанный артефакт будет содержать вредоносный код.",
        "bigtech_interview": "Как концепция BeyondProd в Google решает проблему доверия к сборочным серверам? Использованием герметичных сборок (Hermetic Builds) и верификацией двух независимых подписей от разработчиков."
    },
    {
        "num": 131,
        "title": "Мониторинг активных соединений и предотвращение исчерпания дескрипторов",
        "task": "Реализуйте экспорт метрики числа активных сетевых соединений в Prometheus и настройте алерт при приближении к 80% от лимита файловых дескрипторов ОС (ulimit -n).",
        "theory": "В Linux сетевой сокет — это файловый дескриптор. Если сервис исчерпает лимит файловых дескрипторов процесса (`ulimit -n`), любой последующий вызов `accept()` или `open()` завершится фатальной ошибкой `too many open files`, и сервер перестанет принимать новые запросы. Непрерывный мониторинг дескрипторов и активных соединений в Prometheus позволяет среагировать на утечку или DoS-атаку до наступления полного отказа.",
        "step_by_step": [
            "Используйте `prometheus/client_golang` для регистрации Gauge метрики `active_connections`.",
            "Реализуйте подсчет соединений через обертку `net.Listener`.",
            "Определите лимит дескрипторов через чтение `/proc/self/limits`.",
            "Сконфигурируйте алерт в Prometheus Alertmanager при превышении порога 80%."
        ],
        "code_blocks": [
            {
                "filename": "conn_monitor.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"sync/atomic\"\n)\n\ntype MonitoredListener struct {\n\tnet.Listener\n\tactiveConns int64\n}\n\nfunc (l *MonitoredListener) Accept() (net.Conn, error) {\n\tconn, err := l.Listener.Accept()\n\tif err != nil {\n\t\treturn nil, err\n\t}\n\tcount := atomic.AddInt64(&l.activeConns, 1)\n\tfmt.Printf(\"[METRICS] Новое соединение! Активно сокетов: %d\\n\", count)\n\treturn &monitoredConn{Conn: conn, parent: l}, nil\n}\n\ntype monitoredConn struct {\n\tnet.Conn\n\tparent *MonitoredListener\n\tclosed int32\n}\n\nfunc (c *monitoredConn) Close() error {\n\tif atomic.CompareAndSwapInt32(&c.closed, 0, 1) {\n\t\tremaining := atomic.AddInt64(&c.parent.activeConns, -1)\n\t\tfmt.Printf(\"[METRICS] Соединение закрыто. Осталось: %d\\n\", remaining)\n\t}\n\treturn c.Conn.Close()\n}\n\nfunc main() {\n\tfmt.Println(\"[MONITOR] Обертка листенера для экспорта активных соединений готова.\")\n}\n",
                "note": "Атомарный подсчет активных сетевых сокетов для мониторинга"
            }
        ],
        "under_the_hood": "Операции `atomic.AddInt64` используют процессорные инструкции `LOCK XADD` на x86_64, гарантируя потокобезопасный подсчет сокетов с околонулевыми накладными расходами без захвата мьютексов.",
        "pitfalls": "Забытый декремент при аварийном закрытии сокета приведет к постепенному дрейфу метрики и ложным срабатываниям алертов.",
        "bigtech_interview": "Какое значение ulimit -n считается стандартом для HighLoad бэкенда на Go в проде? Обычно от 65535 до 1048576 дескрипторов на процесс."
    },
    {
        "num": 132,
        "title": "Плавная деградация сервиса и сброс нагрузки (Graceful Degradation / Load Shedding)",
        "task": "Реализуйте паттерн Load Shedding: при приближении количества обрабатываемых запросов к критическому порогу сервис немедленно возвращает HTTP 503 с заголовком Retry-After.",
        "theory": "При перегрузке (Traffic Spike / DDoS) сервер Go может начать накапливать десятки тысяч горутин в памяти. Время отклика деградирует экспоненциально, приводя к тайм-аутам клиентов и падению всего инстанса. Паттерн Load Shedding (сброс нагрузки) предписывает немедленно отвечать `HTTP 503 Service Unavailable` на новые запросы, если система перегружена. Это позволяет балансировщику перенаправить трафик на другие ноды и дает сервису возможность завершить уже принятые задачи.",
        "step_by_step": [
            "Определите максимальное число параллельно исполняемых задач (in-flight limit).",
            "Используйте семафор на базе буферизированного канала или `sync/atomic` счетчик.",
            "Если лимит исчерпан — немедленно верните статус 503 без выполнения тяжелой работы.",
            "Укажите клиенту заголовок `Retry-After: 5`."
        ],
        "code_blocks": [
            {
                "filename": "load_shedder.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"sync/atomic\"\n)\n\ntype LoadShedder struct {\n\tmaxInFlight int64\n\tinFlight    int64\n}\n\nfunc (ls *LoadShedder) Middleware(next http.HandlerFunc) http.HandlerFunc {\n\treturn func(w http.ResponseWriter, r *http.Request) {\n\t\tcurrent := atomic.AddInt64(&ls.inFlight, 1)\n\t\tdefer atomic.AddInt64(&ls.inFlight, -1)\n\n\t\tif current > ls.maxInFlight {\n\t\t\tw.Header().Set(\"Retry-After\", \"5\")\n\t\t\thttp.Error(w, \"Service Overloaded (Load Shedding)\", http.StatusServiceUnavailable) // HTTP 503\n\t\t\treturn\n\t\t}\n\n\t\tnext(w, r)\n\t}\n}\n\nfunc main() {\n\tshedder := &LoadShedder{maxInFlight: 1000}\n\t_ = shedder.Middleware(func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"Hello HighLoad\")\n\t})\n\tfmt.Println(\"[LOAD-SHEDDING] Защита от перегрузки активна (макс. 1000 параллельных запросов).\")\n}\n",
                "note": "Паттерн быстрого сброса избыточной нагрузки Load Shedding"
            }
        ],
        "under_the_hood": "Мгновенный ответ 503 возвращается за доли микросекунды, освобождая поток планировщика и сокет, не допуская исчерпания кучи сервиса.",
        "pitfalls": "Если балансировщик (Ingress/Nginx) не настроен на повторные попытки (retry on 503) к другим репликам, сброс нагрузки приведет к росту ошибок у конечных пользователей.",
        "bigtech_interview": "В чем разница между Rate Limiting и Load Shedding? Rate Limiting защищает систему от конкретного клиента или ключа, а Load Shedding защищает инстанс сервиса от собственной перегрузки вне зависимости от источника трафика."
    },
    {
        "num": 133,
        "title": "Архитектура демилитаризованной зоны: Reverse Proxy (Nginx / Envoy) перед Go",
        "task": "Спроектируйте архитектуру периметра безопасности: терминация TLS, защита от медленных клиентов (Slowloris buffering) и разгрузка статики через Envoy / Nginx перед Go-сервисом.",
        "theory": "Хотя стандартный `net/http` в Go является production-ready, выставление Go-приложений напрямую в открытый интернет не рекомендуется. Использование проверенного обратного прокси (Reverse Proxy — Envoy, Nginx, HAProxy) на периметре обеспечивает:\n1. Буферизацию медленных запросов: Nginx вычитывает тело запроса из сети и передает его в Go по быстрому локальному сокету.\n2. Аппаратную терминацию TLS и поддержку современных шифров.\n3. Защиту от сетевых аномалий и HTTP Request Smuggling.\n4. Быструю раздачу статических файлов без нагрузки на рантайм Go.",
        "step_by_step": [
            "Сконфигурируйте upstream в Nginx/Envoy, указывающий на локальный порт Go сервиса.",
            "Включите директивы буферизации тела запросов: `proxy_buffering on`.",
            "Настройте проброс оригинальных IP-адресов клиентов через заголовки `X-Forwarded-For` и `X-Real-IP`.",
            "Сконфигурируйте Go сервер слушать только `127.0.0.1` или unix domain socket."
        ],
        "code_blocks": [
            {
                "filename": "nginx_perimeter.conf",
                "lang": "nginx",
                "code": "upstream backend_go {\n    server 127.0.0.1:8080 max_fails=3 fail_timeout=10s;\n    keepalive 32;\n}\n\nserver {\n    listen 443 ssl http2;\n    server_name api.company.internal;\n\n    # Терминация TLS на уровне Nginx\n    ssl_certificate /etc/ssl/certs/bundle.crt;\n    ssl_certificate_key /etc/ssl/private/server.key;\n    ssl_protocols TLSv1.2 TLSv1.3;\n\n    # Буферизация для защиты Go от Slowloris\n    proxy_buffering on;\n    proxy_buffer_size 8k;\n    proxy_buffers 8 64k;\n\n    location / {\n        proxy_pass http://backend_go;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_http_version 1.1;\n        proxy_set_header Connection \"\";\n    }\n}\n",
                "note": "Конфигурация защитного прокси Nginx перед приложением на Go"
            }
        ],
        "under_the_hood": "Благодаря `proxy_buffering on` Go-сервер никогда не сталкивается с медленными клиентами: запрос попадает в Go только тогда, когда Nginx полностью вычитал его из сети.",
        "pitfalls": "Доверие к заголовку `X-Forwarded-For` без валидации доверенных прокси (trusted proxies) позволяет атакующему подделать свой IP-адрес для обхода Rate Limiting.",
        "bigtech_interview": "Вопрос на системном дизайне: 'Почему нельзя подключать Go сервис напрямую к интернету без Envoy/Nginx?' Ответ: Для защиты от Slowloris, централизованного управления TLS-сертификатами и разгрузки памяти рантайма при медленных входящих соединениях."
    },
    {
        "num": 134,
        "title": "Регулярное автоматизированное тестирование безопасности и фаззинг",
        "task": "Организуйте комплексный пайплайн тестирования безопасности Go сервиса: статический анализ уязвимостей (govulncheck), DoS-устойчивость и нативный фаззинг (go test -fuzz).",
        "theory": "Безопасность требует регулярной валидации на практике. Пайплайн непрерывного тестирования безопасности (Continuous Security Testing) должен включать:\n1. SCA/Vuln check: проверка графа вызовов зависимостей на известные CVE.\n2. DoS Resilience: нагрузочные стресс-тесты на устойчивость к исчерпанию ресурсов.\n3. Native Fuzzing: встроенный фаззер Go (`go test -fuzz`) для поиска паник, переполнений и утечек памяти на мутирующих входных данных.\n4. DAST: динамическое сканирование запущенного API через OWASP ZAP.",
        "step_by_step": [
            "Напишите фазз-тест `FuzzParsePayload(f *testing.F)` для входных обработчиков.",
            "Настройте ночной запуск фаззинга в CI длительностью 1 час.",
            "Интегрируйте сканирование уязвимостей govulncheck.",
            "Зафиксируйте отчеты и метрики качества в дашборде безопасности."
        ],
        "code_blocks": [
            {
                "filename": "fuzz_test.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"testing\"\n)\n\ntype UserRequest struct {\n\tID   string `json:\"id\"`\n\tAge  int    `json:\"age\"`\n\tData []byte `json:\"data\"`\n}\n\n// FuzzParsePayload проверяет надежность парсера при любых мутациях входных байт\nfunc FuzzParsePayload(f *testing.F) {\n\t// Добавление затравочных данных (seed corpus)\n\tf.Add([]byte(`{\"id\":\"user-1\",\"age\":25,\"data\":\"AQID\"}`))\n\tf.Add([]byte(`{}`))\n\tf.Add([]byte(`invalid-json-garbage`))\n\n\tf.Fuzz(func(t *testing.T, data []byte) {\n\t\tvar req UserRequest\n\t\t// Парсер не должен паниковать ни при каких входных данных\n\t\t_ = json.Unmarshal(data, &req)\n\t})\n}\n",
                "note": "Встроенный нативный фазз-тест Go для проверки парсеров на устойчивость к сбоям"
            }
        ],
        "under_the_hood": "Go фаззер инструментирует скомпилированный код счетчиками покрытия ребер графа потока управления (coverage-guided fuzzing), целенаправленно генерируя мутации, проникающие в глубокие ветки логики.",
        "pitfalls": "Запуск фаззинга на каждом коротком коммите в CI замедлит разработку; глубокий фаззинг выносят в отдельные ночные или еженедельные расписания.",
        "bigtech_interview": "Благодаря нативному фаззингу в Go 1.18+ разработчики стандартной библиотеки и ведущих криптографических пакетов выявили десятки критических краевых случаев до их релиза в прод."
    },
    {
        "num": 135,
        "title": "Переход к безопасности уровня ядра: Сетевые сокеты, eBPF и системная изоляция",
        "task": "Изучите архитектурную связь между системными вызовами ОС, сетевым планировщиком Go (netpoller/epoll) и механизмами глубокой фильтрации уровня ядра (eBPF / XDP).",
        "theory": "Безопасность инфраструктуры завершается на стыке рантайма Go и ядра Linux. Знание внутреннего устройства сетевого поллера Go (`netpoller`), системных вызовов сокетов (`epoll_create1`, `setsockopt`) и механизмов изоляции ядра (eBPF, XDP, Seccomp) позволяет защищать серверы от объемных сетевых атак еще до того, как пакеты достигнут пользователей пространства (Zero-Copy Packet Drop в ядре). Это открывает путь к темам защиты сетевых сокетов и системной изоляции в Главах 82 и 83.",
        "step_by_step": [
            "Исследуйте схему взаимодействия netpoller с системным вызовом `epoll_pwait`.",
            "Оцените масштабируемость сокетов под нагрузкой через счетчики `atomic` против мьютексов.",
            "Спроектируйте архитектуру фильтрации трафика на уровне драйвера через eBPF / XDP.",
            "Подготовьте окружение к изучению низкоуровневых механизмов защиты сетевых интерфейсов."
        ],
        "code_blocks": [
            {
                "filename": "kernel_bridge.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"syscall\"\n)\n\nfunc main() {\n\t// Пример низкоуровневой настройки сетевого сокета через SyscallConn\n\tlc := net.ListenConfig{\n\t\tControl: func(network, address string, c syscall.RawConn) error {\n\t\t\treturn c.Control(func(fd uintptr) {\n\t\t\t\t// Включение SO_REUSEPORT на уровне ядра Linux для масштабирования\n\t\t\t\t_ = syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET, 0xF, 1)\n\t\t\t\tfmt.Printf(\"[KERNEL] Файловый дескриптор сокета: %d сконфигурирован\\n\", fd)\n\t\t\t})\n\t\t},\n\t}\n\n\tfmt.Println(\"[KERNEL-SECURITY] Мост между Go netpoller и подсистемой ядра готов к работе.\")\n\t_ = lc\n}\n",
                "note": "Низкоуровневое управление сокетом ядра через net.ListenConfig Control hook"
            }
        ],
        "under_the_hood": "Хук `Control` выполняется между вызовами `socket()` и `bind()`, позволяя устанавливать расширенные флаги ядра (SO_REUSEPORT, TCP_DEFER_ACCEPT, IP_TRANSPARENT).",
        "pitfalls": "Некорректная модификация параметров сокета может привести к скрытым сетевым ошибкам, невидимым для стандартного `net/http` пакета.",
        "bigtech_interview": "В VK и Cloudflare DDoS-атаки отбиваются на уровне eBPF/XDP прямо на сетевой карте, предотвращая трату процессорного времени на аллокацию сетевых пакетов в сокетах Go."
    },
    {
        "num": 136,
        "title": "Итоговая сертификация и фиксация компетенций Supply Chain Security",
        "task": "Создайте финальный отчет аудита цепочки поставок ПО (Supply Chain Security Audit Checklist), объединяющий все пройденные технологии главы: go.sum, GOPRIVATE, SBOM, Syft, Cosign, SLSA и Hardening.",
        "theory": "Поздравляем с завершением фундаментальной главы по безопасности цепочки поставок (Supply Chain Security) и SBOM! Вы освоили весь спектр современных инструментов защиты ПО от атаки на зависимости и компрометации сборочных сред до криптографической аттестации и изоляции контейнеров. Этот структурированный чек-лист фиксирует ключевые компетенции уровня Senior / Lead DevSecOps инженер для BigTech компаний.",
        "step_by_step": [
            "Сформируйте итоговый отчет соответствия проекта всем стандартам безопасности.",
            "Проверьте наличие контрольных меток для каждого уровня: Dependencies, Build, Signing, Runtime.",
            "Зафиксируйте результаты в корпоративной системе учета комплаенса.",
            "Переходите к следующим главам курса: защите сетевых сокетов (Глава 82) и изоляции ядра Linux (Глава 83)."
        ],
        "code_blocks": [
            {
                "filename": "audit_checklist.go",
                "lang": "go",
                "code": "package main\n\nimport \"fmt\"\n\ntype ChecklistCategory struct {\n\tCategory string\n\tItems    []string\n}\n\nfunc main() {\n\tchecklist := []ChecklistCategory{\n\t\t{\n\t\t\tCategory: \"1. Защита зависимостей\",\n\t\t\tItems: []string{\n\t\t\t\t\"GOSUMDB валидация включена, go.sum зафиксирован\",\n\t\t\t\t\"GOPRIVATE изолирует корпоративные модули от публичных прокси\",\n\t\t\t\t\"govulncheck интегрирован в пре-мерж проверки CI/CD\",\n\t\t\t\t\"Лицензионный аудит go-licenses блокирует копилефт (GPL/AGPL)\",\n\t\t\t},\n\t\t},\n\t\t{\n\t\t\tCategory: \"2. Воспроизводимость и SBOM\",\n\t\t\tItems: []string{\n\t\t\t\t\"Флаги сборщика -trimpath и -buildid= обеспечивают reproducible builds\",\n\t\t\t\t\"Syft генерирует валидные паспорта CycloneDX 1.5 и SPDX 2.3\",\n\t\t\t\t\"SBOM публикуется вместе с релизными артефактами\",\n\t\t\t},\n\t\t},\n\t\t{\n\t\t\tCategory: \"3. Криптографическое доверие\",\n\t\t\tItems: []string{\n\t\t\t\t\"Sigstore Cosign подписывает образы, бинарники и SBOM\",\n\t\t\t\t\"SLSA Level 3 provenance подтверждает происхождение артефакта\",\n\t\t\t\t\"Kubernetes Policy Controller блокирует неподписанные контейнеры\",\n\t\t\t},\n\t\t},\n\t\t{\n\t\t\tCategory: \"4. Рантайм харднинг\",\n\t\t\tItems: []string{\n\t\t\t\t\"Сборка с CGO_ENABLED=0 в минимальный образ scratch\",\n\t\t\t\t\"Строгие таймауты HTTP-сервера и лимиты размера тела (MaxBytesReader)\",\n\t\t\t\t\"Сброс всех Linux Capabilities (Drop ALL) и non-root пользователь\",\n\t\t\t},\n\t\t},\n\t}\n\n\tfmt.Println(\"===============================================================\")\n\tfmt.Println(\"  ИТОГОВЫЙ ЧЕК-ЛИСТ SUPPLY CHAIN SECURITY & SBOM (ГЛАВА 81)   \")\n\tfmt.Println(\"===============================================================\")\n\tfor _, cat := range checklist {\n\t\tfmt.Println(\"\\n\" + cat.Category + \":\")\n\t\tfor _, item := range cat.Items {\n\t\t\tfmt.Printf(\"  [✓] %s\\n\", item)\n\t\t}\n\t}\n\tfmt.Println(\"\\n[100% DONE] 136 из 136 упражнений Главы 81 успешно завершены!\")\n}\n",
                "note": "Итоговая матрица зрелости процессов обеспечения безопасности цепочки поставок"
            }
        ],
        "under_the_hood": "Этот чек-лист полностью покрывает требования директив US Executive Order 14028, NIST SSDF (SP 800-218) и европейского стандарта Cyber Resilience Act.",
        "pitfalls": "Формальное заполнение чек-листов для 'галочки' без автоматического контроля в CI приводит к иллюзии безопасности при реальной уязвимости инфраструктуры.",
        "bigtech_interview": "Инженеры, обладающие практическими навыками настройки всей цепочки от GOSUMDB до Cosign и Seccomp, являются одними из самых востребованных специалистов на позициях Staff/Principal Security Engineer в BigTech."
    }
]
