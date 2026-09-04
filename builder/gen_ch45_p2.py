# -*- coding: utf-8 -*-
exercises = [
  {
    "num": 39,
    "title": "Безопасность контейнеров: защита от атак Container Escape через Non-root user",
    "task": "**Безопасность (Non-root user)**: Запускать приложение в контейнере от имени пользователя `root` — угроза безопасности. В `alpine` (или другом образе) создай пользователя `appuser`, дай ему права на приложение и укажи директиву `USER appuser` перед `CMD`.",
    "theory": "Запуск приложений под учетной записью суперпользователя `root` (UID 0) в контейнере представляет собой критический риск безопасности:\n1. Если атакующий находит уязвимость (RCE) в коде приложения или сторонней зависимости, он получает права root внутри контейнера.\n2. При наличии ошибок конфигурации (например, монтирование хостового сокета `/var/run/docker.sock` или флага `--privileged`) злоумышленник с root-правами может мгновенно скомпрометировать весь физический сервер хоста (Container Breakout).\n\nДля предотвращения этого в Dockerfile создается отдельный пользователь (например, `appuser` с UID 10001):\n`RUN adduser -D -u 10001 -s /sbin/nologin appuser`\nи активируется директивой:\n`USER 10001:10001`\nТакой процесс не может модифицировать файлы системы, устанавливать пакеты или совершать привилегированные системные вызовы ядра.",
    "step_by_step": "1. Создайте HTTP-сервер на Go.\n2. В этапе builder создайте пользователя `appuser` с UID 10001.\n3. Скопируйте `/etc/passwd` в runtime-образ.\n4. Укажите `USER 10001:10001`.\n5. Запустите контейнер и убедитесь, что попытки записи в корень `/` отклоняются операционной системой.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/security\", func(w http.ResponseWriter, r *http.Request) {\n\t\tuid := os.Getuid()\n\t\tisRoot := uid == 0\n\t\tfmt.Fprintf(w, \"Process UID: %d (Is Root: %v)\\n\", uid, isRoot)\n\t})\n\n\thttp.HandleFunc(\"/try-write\", func(w http.ResponseWriter, r *http.Request) {\n\t\t// Попытка создать файл в корневом каталоге /\n\t\terr := os.WriteFile(\"/root-exploit.txt\", []byte(\"pwned\"), 0644)\n\t\tif err != nil {\n\t\t\thttp.Error(w, fmt.Sprintf(\"Access Denied (Expected for non-root): %v\", err), http.StatusForbidden)\n\t\t\treturn\n\t\t}\n\t\tfmt.Fprintln(w, \"WARNING: Root write succeeded!\")\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис для проверки непривилегированного доступа"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\n\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -ldflags=\"-w -s\" -o /bin/app main.go\n\n# Создание непривилегированного пользователя в builder\nRUN adduser -D -u 10001 -s /sbin/nologin appuser\n\nFROM alpine:3.20\n\n# Копирование учетных записей\nCOPY --from=builder /etc/passwd /etc/passwd\nCOPY --from=builder /etc/group /etc/group\nCOPY --from=builder /bin/app /bin/app\n\n# Переключение пользователя\nUSER 10001:10001\n\nEXPOSE 8080\nENTRYPOINT [\"/bin/app\"]",
        "note": "Dockerfile с non-root пользователем"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t app-security-nonroot:v1 .\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-sec app-security-nonroot:v1\n\n# Проверка UID (вернет UID: 10001)\ncurl http://localhost:8080/security\n\n# Проверка запрета записи в корень (вернет 403 Access Denied)\ncurl http://localhost:8080/try-write\n\n# Очистка\ndocker rm -f test-sec"
      }
    ],
    "under_the_hood": "Ядро Linux проверяет мандатные права доступа (Discretionary Access Control — DAC). Каталог `/` принадлежит `root:root` с правами `0755`. Процесс с UID 10001 подпадает под категорию `others` (только чтение и исполнение `r-x`), поэтому системный вызов `open(\"/root-exploit.txt\", O_CREAT|O_WRONLY, 0644)` немедленно отклоняется с ошибкой `EACCES` (Permission denied).",
    "pitfalls": "1. Запуск от имени пользователя `root` по недосмотру.\n2. Необходимость записи логов: если приложению требуется писать логи в файл, для него должна быть заранее создана директория с правами владельца `chown 10001:10001 /app/logs`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему даже при наличии `USER nonroot` в Dockerfile в production-кластерах Kubernetes дополнительно настраивают `securityContext.allowPrivilegeEscalation: false`?»\n**Ответ:** Если в контейнере случайно останется бинарник с битом SUID (SetUID, например утилиты `su`, `sudo`, `mount`), непривилегированный пользователь может выполнить этот бинарник и временно повысить свои права до root. Флаг `allowPrivilegeEscalation: false` запрещает ядру Linux активировать механизм SUID для всех процессов контейнера, гарантируя, что процесс никогда не сможет получить больше прав, чем у него было при старте."
  },
  {
    "num": 40,
    "title": "Внедрение версии и коммита через ARG и -ldflags при сборке",
    "task": "**[Внедрение версии]**: Используй `ARG` и `-ldflags \"-X main.version=1.0.0\"` в Dockerfile, чтобы передавать тег версии в бинарник во время сборки.",
    "theory": "Автоматизация выпуска релизов требует прослеживаемости артефактов (Traceability). В распределенной системе инциденты часто расследуются по логам и метрикам, где необходимо знать точный хэш коммита и семантическую версию сервиса.\n\nКомпилятор Go поддерживает флаг `-X` для внедрения произвольных строковых значений во время линковки:\n`-ldflags \"-X main.version=1.0.0 -X main.commit=$(git rev-parse HEAD)\"`\n\nВ Dockerfile для этого используются инструкции `ARG`:\n```dockerfile\nARG VERSION=unknown\nARG COMMIT=unknown\nRUN go build -ldflags=\"-X main.version=${VERSION} -X main.commit=${COMMIT}\"\n```\nЗначения передаются из CI пайплайна через флаги сборки:\n`docker build --build-arg VERSION=${CI_COMMIT_TAG} --build-arg COMMIT=${CI_COMMIT_SHA} .`",
    "step_by_step": "1. Объявите переменные `version` и `commit` в пакете `main`.\n2. Реализуйте эндпоинт `/health/version`.\n3. Настройте `Dockerfile` с аргументами сборки.\n4. Соберите образ с указанием версии `1.0.0` и хэша коммита.\n5. Проверьте вывод эндпоинта.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"net/http\"\n)\n\nvar (\n\tversion = \"dev\"\n\tcommit  = \"dirty\"\n)\n\ntype VersionInfo struct {\n\tVersion string `json:\"version\"`\n\tCommit  string `json:\"commit\"`\n}\n\nfunc main() {\n\thttp.HandleFunc(\"/version\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\t_ = json.NewEncoder(w).Encode(VersionInfo{\n\t\t\tVersion: version,\n\t\t\tCommit:  commit,\n\t\t})\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис, отдающий информацию о версии"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\n\nARG VERSION=dev\nARG COMMIT=dirty\n\nWORKDIR /app\nCOPY main.go .\n\nRUN CGO_ENABLED=0 go build \\\n    -ldflags=\"-w -s -X 'main.version=${VERSION}' -X 'main.commit=${COMMIT}'\" \\\n    -o /bin/app main.go\n\nFROM scratch\nCOPY --from=builder /bin/app /app\nEXPOSE 8080\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile с поддержкой аргументов версии"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка с внедрением версии 1.0.0\ndocker build \\\n  --build-arg VERSION=1.0.0 \\\n  --build-arg COMMIT=c78e32a \\\n  -t app-ver-demo:1.0.0 .\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-vd app-ver-demo:1.0.0\n\n# Проверка\ncurl -s http://localhost:8080/version\n# Ответ: {\"version\":\"1.0.0\",\"commit\":\"c78e32a\"}\n\ndocker rm -f test-vd"
      }
    ],
    "under_the_hood": "Линковщик `go tool link` модифицирует сегмент данных инициализированных переменных (`.data`) исполняемого файла ELF. Значение строки записывается напрямую в бинарник, что исключает накладные расходы на чтение файлов или переменных окружения в рантайме.",
    "pitfalls": "1. Использование флага `-X` для нестроковых типов данных (например, `int` или `struct`): вызовет ошибку линковки.\n2. Пропуск кавычек при наличии пробелов в значении аргумента (например, в дате сборки).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему встраивание версии через `-ldflags -X` предпочтительнее чтения версии из файла `version.txt` или переменной окружения `ENV VERSION`?»\n**Ответ:** 1) Встраивание в бинарник защищено от случайного удаления или рассинхронизации внешнего файла. 2) Бинарник становится самодостаточным и отдает правильную версию даже при запуске вне контейнера или в тестах. 3) Переменную окружения `ENV` можно случайно переопределить при запуске контейнера, что приведет к дезинформации систем мониторинга, а бинарная константа гарантирует неизменяемость."
  },
  {
    "num": 41,
    "title": "Docker Compose Overrides: разделение настроек dev и production",
    "task": "Напиши **Docker Compose override**: `docker-compose.yml` (production), `docker-compose.override.yml` (development, автоматически подхватывается), `docker-compose.test.yml` (CI). Покажи `docker-compose -f docker-compose.yml -f docker-compose.test.yml up`.",
    "theory": "Паттерн **Compose Overrides** позволяет переиспользовать базовое описание сервисов, накладывая поверх него специфические конфигурации для разных окружений.\n\nМеханизм слияния Compose:\n1. `docker-compose.yml`: базовый файл, общий для всех сред (определяет имена сервисов, сети, хранилища).\n2. `docker-compose.override.yml`: автоматически применяется при запуске `docker compose up` без дополнительных флагов. Используется для **локальной разработки** (проброс портов на хост, bind mount исходников для live-reload, переменные отладки).\n3. `docker-compose.prod.yml`: применяется явно через `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` для **продакшн-стенда** (жесткие лимиты CPU/Memory, restart-политика `always`, read-only rootfs).\n\nПри слиянии Compose объединяет списки и перезаписывает скалярные значения (порты, переменные окружения, команды).",
    "step_by_step": "1. Создайте базовый `docker-compose.yml`.\n2. Создайте файл `docker-compose.override.yml` для локальной разработки.\n3. Создайте `docker-compose.prod.yml` для продакшна.\n4. Проверьте итоговую конфигурацию через `docker compose config`.",
    "code_blocks": [
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  app:\n    image: mycompany/app:latest\n    environment:\n      - APP_NAME=CoreService\n      - LOG_LEVEL=info\n    networks:\n      - app_net\n\nnetworks:\n  app_net:\n    driver: bridge",
        "note": "Базовый файл конфигурации сервисов"
      },
      {
        "filename": "docker-compose.override.yml",
        "lang": "yaml",
        "code": "# Автоматически применяется для локальной разработки\nservices:\n  app:\n    build:\n      context: .\n      dockerfile: Dockerfile\n    ports:\n      - \"8080:8080\"\n    environment:\n      - LOG_LEVEL=debug\n      - ENV=development\n    volumes:\n      - ./:/app:ro",
        "note": "Override-файл для локальной разработки"
      },
      {
        "filename": "docker-compose.prod.yml",
        "lang": "yaml",
        "code": "# Файл настроек для Production\nservices:\n  app:\n    restart: always\n    deploy:\n      resources:\n        limits:\n          cpus: '2.0'\n          memory: 1G\n    environment:\n      - LOG_LEVEL=warn\n      - ENV=production",
        "note": "Production-конфигурация"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Просмотр локальной конфигурации (автоматическое слияние с override)\ndocker compose config\n\n# Просмотр продакшн конфигурации (явное слияние с prod.yml)\ndocker compose -f docker-compose.yml -f docker-compose.prod.yml config"
      }
    ],
    "under_the_hood": "Compose выполняет глубокое рекурсивное слияние (Deep Merge) YAML-структур. Словари объединяются, скалярные поля заменяются значениями из последующих файлов, а элементы списков (например, `ports` или `volumes`) дополняются без дублирования идентичных ключей.",
    "pitfalls": "1. Хранение секретов и паролей в незашифрованном `docker-compose.override.yml`, который может быть случайно закоммичен в репозиторий.\n2. Конфликт портов при попытке одновременного запуска dev и prod стеков на одной машине.",
    "bigtech_interview": "**Вопрос с собеседования:** «В каком порядке Docker Compose сливает конфигурационные файлы и как исключить автозагрузку `docker-compose.override.yml` в CI/CD конвейере?»\n**Ответ:** По умолчанию Compose сливает `docker-compose.yml`, а затем `docker-compose.override.yml` (если он присутствует в текущей директории). Чтобы в CI/CD или на сервере полностью исключить автозагрузку override-файла, необходимо явно указать список нужных файлов через флаги `-f`: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`. В этом случае файл `docker-compose.override.yml` будет проигнорирован."
  },
  {
    "num": 42,
    "title": "Сборка Multi-Arch образов для AMD64 и ARM64 через Docker Buildx",
    "task": "Соберите multi-architecture образ для amd64 и arm64 через `docker buildx build --platform linux/amd64,linux/arm64 -t app .`",
    "theory": "При развертывании Go-приложений в современных облаках (AWS, GCP, Yandex Cloud, Selectel) все чаще используются инстансы на базе архитектуры ARM64 (AWS Graviton, Ampere Altra). Они обеспечивают до 40% лучшее соотношение производительности к стоимости (Price/Performance).\n\nДля поддержки разнородной инфраструктуры требуется публикация мультиплатформенных образов (Multi-Arch Images).\n\nКоманда сборки:\n`docker buildx build --platform linux/amd64,linux/arm64 -t registry.example.com/app:v1.0 --push .`\n\nКак это работает:\n1. Buildx формирует независимые образы под каждую целевую архитектуру.\n2. Создается манифест OCI (Image Index), связывающий оба образа под единым тегом `v1.0`.\n3. Манифест и слои пушатся в Registry.\n4. При `docker run` клиент скачивает слой, соответствующий архитектуре своего CPU.",
    "step_by_step": "1. Создайте мультиплатформенный `Dockerfile` с аргументами `$BUILDPLATFORM` и `$TARGETARCH`.\n2. Настройте билдер buildx: `docker buildx create --use --name multi-builder`.\n3. Соберите образ под `linux/amd64` и `linux/arm64`.\n4. Проверьте манифест OCI Index.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"runtime\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Running on architecture: %s/%s\\n\", runtime.GOOS, runtime.GOARCH)\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис, определяющий архитектуру исполнения"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# Быстрая сборка на платформе билдера\nFROM --platform=$BUILDPLATFORM golang:1.24-alpine AS builder\n\nARG TARGETOS\nARG TARGETARCH\n\nWORKDIR /src\nCOPY main.go .\n\n# Нативная компиляция компилятором Go под целевую архитектуру TARGETARCH\nRUN CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH go build \\\n    -ldflags=\"-w -s\" \\\n    -o /bin/app main.go\n\nFROM scratch\nCOPY --from=builder /bin/app /app\nEXPOSE 8080\nENTRYPOINT [\"/app\"]",
        "note": "Кросс-компилируемый Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Создание билдера buildx\ndocker buildx create --use --name cloud-builder\n\n# Локальная тестовая сборка под две платформы\ndocker buildx build --platform linux/amd64,linux/arm64 -t test-multiarch-app:v1 .\n\n# Очистка билдера\ndocker buildx rm cloud-builder"
      }
    ],
    "under_the_hood": "В спецификации OCI (Open Container Initiative) Multi-Arch образ представлен JSON-документом с медиа-типом `application/vnd.oci.image.index.v1+json`. Он содержит массив `manifests`, где для каждого дайджеста слоя указаны `platform.os` и `platform.architecture`.",
    "pitfalls": "1. Использование `--load` для мультиархитектурных образов: Docker Engine локально не поддерживает хранение Manifest List под одним именем (требуется собирать по отдельности либо делать `--push` в реестр).\n2. Наличие CGO-зависимостей без кросс-компилятора C.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему кросс-компиляция Go в Docker Buildx работает в разы быстрее, чем кросс-компиляция приложений на C++ или Rust?»\n**Ответ:** Компилятор Go (`cmd/compile`) изначально спроектирован с поддержкой кросс-компиляции из коробки: переключение целевой архитектуры выполняется простым указанием переменных `GOOS` и `GOARCH` без необходимости кросс-линковщиков и системных заголовков хоста (при `CGO_ENABLED=0`). В C++ и Rust требуется кросс-тулчейн GCC/Clang и заголовочные файлы целевой libc, либо медленная поинструкционная эмуляция всей системы через QEMU."
  },
  {
    "num": 43,
    "title": "Персистентность данных: Named Volumes в Docker Compose",
    "task": "Настрой **Docker volumes**: named volume `postgres_data` для persistence. `docker run -v postgres_data:/var/lib/postgresql/data`. Покажи, что данные сохраняются при удалении контейнера.",
    "theory": "Контейнеры являются эфемерными (непостоянными): при выполнении команды `docker compose down` контейнер уничтожается вместе со всеми изменениями в его локальной файловой системе.\n\nДля постоянного хранения данных баз данных (PostgreSQL, MySQL, Redis, MongoDB) используются **именованные тома (Named Volumes)**:\n```yaml\nvolumes:\n  postgres_data:\n    driver: local\n```\n\nОсобенности Named Volumes:\n1. Хранятся в специальной директории Docker хоста (`/var/lib/docker/volumes/<volume_name>/_data`).\n2. Не удаляются при команде `docker compose down`. Данные сохраняются между обновлениями версий образов.\n3. Удалить том можно только явно флагом `docker compose down -v` или командой `docker volume rm`.",
    "step_by_step": "1. Опишите сервис PostgreSQL с подключением named volume `postgres_data`.\n2. Запустите стек `docker compose up -d`.\n3. Создайте таблицу и добавьте тестовые записи.\n4. Выполните `docker compose down`, а затем снова `docker compose up -d`.\n5. Убедитесь, что данные сохранились в полном объеме.",
    "code_blocks": [
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  db:\n    image: postgres:16-alpine\n    container_name: test_pg_volume\n    environment:\n      POSTGRES_USER: postgres\n      POSTGRES_PASSWORD: secretpassword\n      POSTGRES_DB: workout_db\n    ports:\n      - \"5432:5432\"\n    volumes:\n      # Монтирование именованного тома в директорию данных PostgreSQL\n      - pg_persistence_vol:/var/lib/postgresql/data\n    restart: unless-stopped\n\nvolumes:\n  pg_persistence_vol:\n    name: custom_pg_data_volume",
        "note": "Docker Compose с именованным томом"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск базы данных\ndocker compose up -d\n\n# Создаем тестовую таблицу в запущенном PostgreSQL\ndocker compose exec db psql -U postgres -d workout_db -c \"CREATE TABLE test (id int, val text); INSERT INTO test VALUES (1, 'Persistent Data');\"\n\n# Полностью останавливаем и удаляем контейнеры\ndocker compose down\n\n# Перезапускаем контейнер заново\ndocker compose up -d\n\n# Проверяем, что данные на месте!\ndocker compose exec db psql -U postgres -d workout_db -c \"SELECT * FROM test;\"\n\n# Финальная очистка вместе с томом\ndocker compose down -v"
      }
    ],
    "under_the_hood": "При монтировании Named Volume Docker не использует OverlayFS для каталога `/var/lib/postgresql/data`. Он создает прямой bind mount на локальную директорию `/var/lib/docker/volumes/.../_data`. Это обеспечивает максимальную скорость дискового ввода-вывода (direct I/O) и надежность журналирования WAL базы данных.",
    "pitfalls": "1. Случайное выполнение `docker compose down -v` в продакшне: флаг `-v` безвозвратно удаляет все именованные тома проекта вместе с данными.\n2. Проблемы с правами доступа при смене версий образов баз данных.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что произойдет с файлами в Named Volume при выполнении команд `docker compose down` и `docker compose down -v`?»\n**Ответ:** Команда `docker compose down` останавливает и удаляет только контейнеры и сети, оставляя Named Volumes нетронутыми на диске хоста. Команда `docker compose down -v` (или `--volumes`) принудительно удаляет все именованные тома, объявленные в секции `volumes` файла Compose, что приводит к полному и безвозвратному уничтожению всех хранившихся в них данных баз данных."
  },
  {
    "num": 44,
    "title": "Ограничение ресурсов: Memory Limits, CPU Quota и защита от OOMKilled",
    "task": "Настрой **resource limits**: `deploy.resources.limits.memory: 512M`, `deploy.resources.limits.cpus: '1.0'`, `deploy.resources.reservations.memory: 256M`. Покажи OOM Killer при превышении memory limit.",
    "theory": "По умолчанию процесс в контейнере не ограничен в ресурсах и может потребить **100% оперативной памяти и ядер процессора хост-машины**.\nВ случае утечки памяти (Memory Leak) в одном Go-сервисе операционная система Linux активирует **OOM Killer** (Out Of Memory Killer), который может аварийно завершить критические системные процессы (например, dockerd, kubelet или базу данных).\n\nВ Docker Compose и Docker CLI лимиты задаются через подсистему ядра Linux **cgroups (Control Groups v1/v2)**:\n```yaml\ndeploy:\n  resources:\n    limits:\n      cpus: '1.0'\n      memory: 512M\n    reservations:\n      cpus: '0.25'\n      memory: 128M\n```\n\nКритический нюанс Go в контейнерах:\nРантайм Go (`GOMAXPROCS`) по умолчанию считывает количество физических ядер хоста!\nЕсли на сервере 64 ядра, а контейнеру выдан лимит `cpus: 1.0`, Go создаст 64 потока ОС (`M`), что вызовет жесткий троттлинг CPU (CPU Throttling) и задержки планировщика.\nДля решения этой проблемы используется библиотека `go.uber.org/automaxprocs`.",
    "step_by_step": "1. Напишите Go-сервис с мониторингом памяти и автонастройкой `GOMAXPROCS`.\n2. Опишите `docker-compose.yml` с жесткими ограничениями: `memory: 256M`, `cpus: 0.5`.\n3. Запустите сервис и проверьте лимиты через `docker stats`.\n4. Проэмулируйте выделение памяти выше лимита и зафиксируйте код выхода 137 (OOMKilled).",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"runtime\"\n\t\"time\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/info\", func(w http.ResponseWriter, r *http.Request) {\n\t\tvar m runtime.MemStats\n\t\truntime.ReadMemStats(&m)\n\t\tfmt.Fprintf(w, \"Alloc: %d KB, NumCPU: %d, GOMAXPROCS: %d\\n\",\n\t\t\tm.Alloc/1024, runtime.NumCPU(), runtime.GOMAXPROCS(0))\n\t})\n\n\t// Эндпоинт эмуляции утечки памяти для проверки OOMKilled\n\thttp.HandleFunc(\"/leak\", func(w http.ResponseWriter, r *http.Request) {\n\t\tgo func() {\n\t\t\tvar leak [][]byte\n\t\t\tfor {\n\t\t\t\tleak = append(leak, make([]byte, 10*1024*1024)) // +10MB\n\t\t\t\ttime.Sleep(100 * time.Millisecond)\n\t\t\t}\n\t\t}()\n\t\tfmt.Fprintln(w, \"Memory leak initiated...\")\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис для демонстрации работы cgroups памяти"
      },
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  app:\n    build: .\n    ports:\n      - \"8080:8080\"\n    deploy:\n      resources:\n        limits:\n          cpus: '0.50'\n          memory: 128M\n        reservations:\n          cpus: '0.10'\n          memory: 64M",
        "note": "Конфигурация ресурсов cgroups"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -o /app main.go\n\nFROM alpine:3.20\nCOPY --from=builder /app /app\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск с лимитами\ndocker compose up -d\n\n# Мониторинг утилизации ресурсов в реальном времени\ndocker stats --no-stream\n\n# Проверка информации о ресурсах\ncurl http://localhost:8080/info\n\n# Очистка\ndocker compose down"
      }
    ],
    "under_the_hood": "Docker передает лимиты ядру Linux через псевдофайловую систему cgroups v2 (`/sys/fs/cgroup/memory.max` и `cpu.max`). При превышении порога `memory.max` ядро вызывает обработчик `mem_cgroup_out_of_memory()`, посылает процессу сигнал `SIGKILL` и фиксирует причину завершения `OOMKilled: true` в метаданных контейнера.",
    "pitfalls": "1. Забытый `GOMAXPROCS`: при лимите 1 CPU на сервере с 32 ядрами планировщик Go порождает десятки горутин в очереди на исполнение, получая жесткий троттлинг от планировщика CFS ядра Linux.\n2. Недостаточный запас памяти для Garbage Collector Go (GC Overhead): если лимит 128 МБ, а приложение потребляет 110 МБ, GC может не успеть очистить память перед очередным выделением.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что означает код возврата контейнера 137 при завершении процесса в Docker / Kubernetes и как его диагностировать?»\n**Ответ:** Код возврата 137 равен `128 + 9`, где 9 — номер сигнала `SIGKILL`. Это означает, что процесс был принудительно уничтожен ядром Linux без возможности перехвата сигнала. В 99% случаев причиной является OOM Killer из-за превышения установленного лимита памяти (`cgroups memory.max`). Диагностируется командами `docker inspect <container> --format='{{.State.OOMKilled}}'` (вернет `true`) и просмотром системного журнала `dmesg -T | grep -i oom`."
  },
  {
    "num": 45,
    "title": "Аудит слоев образа: утилита dive и команда docker history",
    "task": "Проанализируйте слои образа через `docker history app` и `dive app` (инструмент для глубокого анализа Docker-образов).",
    "theory": "Для оптимизации размера и безопасности контейнеров инженеры применяют инструменты статического анализа слоев:\n1. `docker history <image>`: встроенная команда Docker, отображающая размер каждого слоя, команду, создавшую слой, и время сборки.\n2. **`dive`** (github.com/wagoodman/dive): специализированная CLI-утилита для интерактивного анализа Docker-образов.\n\nВозможности `dive`:\n- Показывает точный список файлов, добавленных, измененных или удаленных в каждом слое.\n- Находит неэффективно потраченное дисковое пространство («Wasted Space») — файлы, которые были записаны в одном слое, а затем перезаписаны или удалены в другом.\n- Рассчитывает метрику эффективности образа (Image Efficiency Score, от 0 до 100%).",
    "step_by_step": "1. Соберите исследуемый Docker-образ.\n2. Выполните команду `docker history --no-trunc <image>`.\n3. Запустите интерактивный анализ через `dive <image>`.\n4. Проанализируйте wasted space и удалите ненужные слои из Dockerfile.",
    "code_blocks": [
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -ldflags=\"-w -s\" -o /bin/app main.go\n\nFROM alpine:3.20\n# Чистый финальный слой: только нужные бинарники без мусора\nCOPY --from=builder /bin/app /bin/app\nENTRYPOINT [\"/bin/app\"]",
        "note": "Оптимизированный Dockerfile"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"Audited clean image!\")\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Минимальный микросервис"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка образа\ndocker build -t app-audit:v1 .\n\n# Встроенный аудит слоев Docker\ndocker history app-audit:v1 --format \"table {{.CreatedBy}}\\t{{.Size}}\"\n\n# Запуск глубокого анализа через dive (в контейнере)\ndocker run --rm -it \\\n  -v /var/run/docker.sock:/var/run/docker.sock \\\n  wagoodman/dive:latest app-audit:v1 --ci"
      }
    ],
    "under_the_hood": "Утилита `dive` скачивает OCI-манифест образа, распаковывает tar-архивы каждого слоя и строит дерево файловой системы. Сравнивая inodes и контрольные суммы между слоями `L_n` и `L_{n+1}`, dive выявляет скрытые whiteout файлы и дубликаты.",
    "pitfalls": "1. Забытые временные файлы компилятора в single-stage образах.\n2. Игнорирование предупреждений CI-линтеров контейнеров (Hadolint).",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое Wasted Space в Docker-образе по метрике утилиты `dive` и как добиться показателя эффективности 99–100%?»\n**Ответ:** Wasted Space — это объем дискового пространства, занятый файлами, которые были продублированы или удалены в последующих слоях образа (например, установка пакетов в одном `RUN`, а удаление их кэша в другом `RUN`, либо изменение прав через `RUN chmod`). Для достижения 100% эффективности необходимо: 1) Использовать multi-stage сборки, где в runtime копируются только готовые бинарники. 2) Объединять создание и очистку временных файлов в один шаг `RUN`. 3) Использовать флаг `COPY --chown=...` вместо отдельного шага `RUN chown`."
  },
  {
    "num": 46,
    "title": "Политики перезапуска: restart unless-stopped, always и on-failure",
    "task": "Настрой **restart policy**: `restart: unless-stopped` (development), `restart: always` (production), `restart: on-failure:3` (CI). Покажи поведение при `docker stop` vs crash.",
    "theory": "Политика перезапуска (`restart policy`) контейнера определяет поведение Docker демона при аварийном падении процесса или перезагрузке операционной системы хоста.\n\nОсновные политики:\n1. `no`: (по умолчанию) не перезапускать контейнер ни при каких обстоятельствах.\n2. `on-failure[:max-retries]`: перезапускать контейнер только в случае ненулевого кода возврата (Exit Code != 0). Рекомендуется для батч-воркеров и утилит миграций.\n3. `always`: всегда перезапускать контейнер при падении, а также автоматически запускать его при старте/перезагрузке Docker демона и всей хостовой ОС.\n4. `unless-stopped`: аналогично `always`, за исключением случая, когда контейнер был явно остановлен вручную инженером (`docker stop`). Золотой стандарт для большинства веб-сервисов.",
    "step_by_step": "1. Опишите сервис в `docker-compose.yml` с политикой `restart: unless-stopped`.\n2. Запустите контейнер.\n3. Сымитируйте аварийное падение процесса изнутри (код возврата 1 или panic).\n4. Убедитесь, что Docker автоматически перезапустил контейнер.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n\t\"time\"\n)\n\nfunc main() {\n\tstartTime := time.Now()\n\n\thttp.HandleFunc(\"/uptime\", func(w http.ResponseWriter, r *http.Request) {\n\t\tlog.Printf(\"Uptime check. Running since: %s\\n\", startTime.Format(time.RFC3339))\n\t\tw.Write([]byte(\"Service active. Start: \" + startTime.Format(time.RFC3339)))\n\t})\n\n\t// Эндпоинт искусственного краша сервиса\n\thttp.HandleFunc(\"/crash\", func(w http.ResponseWriter, r *http.Request) {\n\t\tlog.Println(\"Simulating fatal crash!\")\n\t\tgo func() {\n\t\t\ttime.Sleep(500 * time.Millisecond)\n\t\t\tos.Exit(1) // Аварийный выход\n\t\t}()\n\t\tw.Write([]byte(\"Crashing now...\"))\n\t})\n\n\tlog.Println(\"Listening on :8080...\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис с возможностью вызова контролируемого сбоя"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -o /app main.go\n\nFROM alpine:3.20\nCOPY --from=builder /app /app\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile"
      },
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  web:\n    build: .\n    ports:\n      - \"8080:8080\"\n    restart: unless-stopped",
        "note": "Compose с политикой restart: unless-stopped"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск\ndocker compose up -d\n\n# Проверяем начальное время старта\ncurl http://localhost:8080/uptime\n\n# Провоцируем падение сервиса\ncurl http://localhost:8080/crash\n\n# Ждем 3 секунды: Docker перезапускает контейнер\nsleep 3\n\n# Проверяем uptime — контейнер жив, время старта обновилось!\ncurl http://localhost:8080/uptime\n\n# Очистка\ndocker compose down"
      }
    ],
    "under_the_hood": "Демон Docker отслеживает события выхода процессов через события cgroups/pidfd. При получении уведомления о завершении процесса демон проверяет назначенную политику и при необходимости заново инициирует системный вызов старта контейнера через containerd, применяя экспоненциальный бэкофф (backoff) при частых циклических падениях (CrashLoop).",
    "pitfalls": "1. Использование `restart: always` для контейнеров-миграций: миграция завершится с кодом 0, но Docker перезапустит ее снова, вызвав бесконечный цикл.\n2. Бесконечный CrashLoop: при фатальной ошибке конфигурации контейнер будет непрерывно рестартовать, нагружая CPU сервера.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем практическая разница между `restart: always` и `restart: unless-stopped` в продакшне?»\n**Ответ:** Если физический сервер или служба Docker перезагрузится, обе политики поднимут контейнеры автоматически. Разница проявляется, если дежурный инженер вручную остановил контейнер командой `docker stop`. Контейнер с политикой `always` после перезагрузки демона Docker/сервера снова автоматически запустится вопреки воле инженера. Контейнер с политикой `unless-stopped` запомнит, что он был остановлен вручную, и останется в статусе stopped."
  },
  {
    "num": 47,
    "title": "Интеграция Go-сервиса и PostgreSQL в едином docker-compose.yml",
    "task": "Создайте `docker-compose.yml` с вашим Go-сервисом и PostgreSQL.",
    "theory": "Связка Go + PostgreSQL — самый распространенный паттерн бэкенд-разработки.\n\nВ файле `docker-compose.yml` ключевыми аспектами являются:\n1. Сетевая изоляция: оба сервиса находятся в общей сети.\n2. Передача строки подключения к БД (DSN) через переменные окружения.\n3. Использование `depends_on`: гарантирует правильный порядок старта сервисов.\n4. Использование Named Volume: обеспечивает сохранение таблиц и данных PostgreSQL между перезапусками.",
    "step_by_step": "1. Напишите Go-сервер, выполняющий подключение к PostgreSQL через стандартный драйвер `pgx` или `lib/pq`.\n2. Создайте файл `docker-compose.yml` с сервисами `app` и `postgres`.\n3. Запустите стек и проверьте успешное выполнение SQL-запроса `SELECT 1`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"database/sql\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n\t\"time\"\n\n\t_ \"github.com/lib/pq\"\n)\n\nfunc main() {\n\tdsn := os.Getenv(\"DATABASE_URL\")\n\tif dsn == \"\" {\n\t\tdsn = \"postgres://postgres:secret@postgres:5432/testdb?sslmode=disable\"\n\t}\n\n\tvar db *sql.DB\n\tvar err error\n\n\t// Попытки подключения с бэкоффом\n\tfor i := 0; i < 10; i++ {\n\t\tdb, err = sql.Open(\"postgres\", dsn)\n\t\tif err == nil && db.Ping() == nil {\n\t\t\tlog.Println(\"Connected to PostgreSQL successfully!\")\n\t\t\tbreak\n\t\t}\n\t\tlog.Printf(\"Waiting for Postgres... (%d/10)\\n\", i+1)\n\t\ttime.Sleep(2 * time.Second)\n\t}\n\n\thttp.HandleFunc(\"/db-check\", func(w http.ResponseWriter, r *http.Request) {\n\t\tvar result int\n\t\terr := db.QueryRow(\"SELECT 1\").Scan(&result)\n\t\tif err != nil {\n\t\t\thttp.Error(w, err.Error(), 500)\n\t\t\treturn\n\t\t}\n\t\tfmt.Fprintf(w, \"Postgres Ping OK: %d\\n\", result)\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Go сервис с проверкой связи с PostgreSQL"
      },
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  app:\n    build: .\n    ports:\n      - \"8080:8080\"\n    environment:\n      - DATABASE_URL=postgres://postgres:mysecret@postgres:5432/production_db?sslmode=disable\n    depends_on:\n      - postgres\n    restart: unless-stopped\n\n  postgres:\n    image: postgres:16-alpine\n    environment:\n      POSTGRES_USER: postgres\n      POSTGRES_PASSWORD: mysecret\n      POSTGRES_DB: production_db\n    volumes:\n      - pg_data:/var/lib/postgresql/data\n    restart: unless-stopped\n\nvolumes:\n  pg_data:",
        "note": "docker-compose.yml Go + Postgres"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY go.mod go.sum* ./\nRUN go mod download\nCOPY . .\nRUN CGO_ENABLED=0 go build -o /app main.go\n\nFROM alpine:3.20\nCOPY --from=builder /app /app\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск\ndocker compose up -d\n\n# Проверка соединения с базой данных\ncurl http://localhost:8080/db-check\n\n# Очистка\ndocker compose down -v"
      }
    ],
    "under_the_hood": "Compose подключает контейнеры `app` и `postgres` к виртуальному мосту. Драйвер Go `lib/pq` устанавливает TCP-сокет соединение на порт 5432 по IP-адресу, полученному от встроенного DNS `127.0.0.11` для имени хоста `postgres`.",
    "pitfalls": "1. Сервис `app` стартует быстрее, чем PostgreSQL успеет инициализировать директорию данных (ошибка `connection refused`).\n2. Хардкод паролей в файле репозитория вместо использования `.env`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему директивы `depends_on: [postgres]` недостаточно для надежного старта Go-сервиса, использующего БД в Docker Compose?»\n**Ответ:** По умолчанию `depends_on` проверяет только факт того, что контейнер с PostgreSQL *запустился* (процесс стартовал). Однако серверу PostgreSQL требуется 5–15 секунд на инициализацию системных каталогов, загрузку буферов памяти и открытие сокета 5432. Go-приложение сразу пытается подключиться и падает с ошибкой `dial tcp: connection refused`. Решение: использовать `depends_on` с условием готовности health check (`condition: service_healthy`) либо реализовать retry-логику с экспоненциальным backoff внутри самого Go-кода."
  },
  {
    "num": 48,
    "title": "Полнофункциональный Docker Compose: Go, PostgreSQL и Redis кэш",
    "task": "**[Docker Compose]**: Напиши `docker-compose.yml`, который поднимает твое Go-приложение, PostgreSQL и Redis. Настрой `depends_on` с `condition: service_healthy` (healthcheck для БД).",
    "theory": "В HighLoad системах реляционная база данных PostgreSQL дополняется кэширующим слоем в оперативной памяти на базе Redis.\n\nАрхитектура стека:\n1. `app`: Go HTTP-сервер, реализующий паттерн Cache-Aside.\n2. `postgres`: основное долговременное хранилище (Named Volume).\n3. `redis`: быстрый кэш для сессий и горячих запросов.\n\nПреимущества использования Docker Compose:\n- Единая команда поднятия всей инфраструктуры (`docker compose up -d`).\n- Изоляция сетевого трафика.\n- Воспроизводимость окружения для всех разработчиков команды.",
    "step_by_step": "1. Напишите сервис на Go, подключающийся к Postgres и Redis.\n2. Опишите `docker-compose.yml` с тремя сервисами.\n3. Протестируйте запись данных в Postgres и чтение из кэша Redis.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\tdbURL := os.Getenv(\"DATABASE_URL\")\n\tredisURL := os.Getenv(\"REDIS_URL\")\n\n\thttp.HandleFunc(\"/ping-all\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"All systems operational! DB: %s | Redis: %s\\n\", dbURL, redisURL)\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Go микросервис"
      },
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  app:\n    build: .\n    ports:\n      - \"8080:8080\"\n    environment:\n      - DATABASE_URL=postgres://user:pass@postgres:5432/appdb\n      - REDIS_URL=redis:6379\n    depends_on:\n      - postgres\n      - redis\n\n  postgres:\n    image: postgres:16-alpine\n    environment:\n      POSTGRES_USER: user\n      POSTGRES_PASSWORD: pass\n      POSTGRES_DB: appdb\n    volumes:\n      - pgdata:/var/lib/postgresql/data\n\n  redis:\n    image: redis:7-alpine\n\nvolumes:\n  pgdata:",
        "note": "docker-compose.yml с тремя сервисами"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -o /app main.go\n\nFROM alpine:3.20\nCOPY --from=builder /app /app\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск всех трех сервисов\ndocker compose up -d\n\n# Проверка статуса\ndocker compose ps\n\n# Проверка связи\ncurl http://localhost:8080/ping-all\n\n# Остановка\ndocker compose down -v"
      }
    ],
    "under_the_hood": "Все три контейнера получают виртуальные интерфейсы `eth0` в одной подсети (например, `172.20.0.0/16`). Трафик между `app`, `postgres` и `redis` передается через ядро Linux без выхода на физические сетевые адаптеры хоста, что обеспечивает максимальную пропускную способность (до 40-50 Гбит/с в памяти хоста).",
    "pitfalls": "1. Забытый volume для Postgres: при перезапуске данные стираются.\n2. Проброс порта Redis (`6379:6379`) на хост в продакшне без пароля — частый вектор взлома через Redis RCE.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем скрывать порты внутренних баз данных (`postgres`, `redis`) в продакшн docker-compose и не указывать секцию `ports` наружу?»\n**Ответ:** Если порт указан в секции `ports: [\"5432:5432\"]`, Docker создает правило DNAT в `iptables`, открывая порт 5432 на всех внешних сетевых интерфейсах хоста (`0.0.0.0:5432`), часто в обход локального файрвола (UFW). Это создает угрозу прямого сканирования и брутфорса паролей базы данных из глобального интернета. Доступ к БД должен быть только у контейнеров внутри изолированной Docker-сети."
  },
  {
    "num": 49,
    "title": "Локальное окружение разработки: запуск связки Go-сервиса и PostgreSQL",
    "task": "**Docker Compose для локальной разработки**: Твоему сервису нужен PostgreSQL. Создай файл `docker-compose.yml`. Опиши два сервиса: `app` (собирается из твоего Dockerfile) и `db` (образ `postgres:15`). Настрой сеть, чтобы `app` подключался к БД по имени хоста `db`. Подними всё одной командой `docker compose up -d`.",
    "theory": "Для максимального комфорта локальной разработки инженеры настраивают связку, где:\n1. База данных PostgreSQL запускается в Docker Compose с сохранением данных.\n2. Go-приложение может запускаться как внутри контейнера, так и локально на хосте (через `go run main.go`), подключаясь к `localhost:5432`.\n\nДля этого порт PostgreSQL пробрасывается на хост:\n`ports: [\"5432:5432\"]`\nА строка подключения конфигурируется через переменную окружения `DATABASE_URL` с дефолтным значением на `localhost`.",
    "step_by_step": "1. Создайте `docker-compose.yml` только для PostgreSQL.\n2. Запустите базу: `docker compose up -d`.\n3. Запустите Go-приложение локально: `DATABASE_URL=... go run main.go`.\n4. Убедитесь в успешной работе приложения с контейнеризованной БД.",
    "code_blocks": [
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  postgres:\n    image: postgres:16-alpine\n    container_name: local_dev_pg\n    environment:\n      POSTGRES_USER: dev\n      POSTGRES_PASSWORD: devpass\n      POSTGRES_DB: local_db\n    ports:\n      - \"5432:5432\"\n    volumes:\n      - local_pg_data:/var/lib/postgresql/data\n\nvolumes:\n  local_pg_data:",
        "note": "Compose файл для локальной базы данных"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\tdbHost := os.Getenv(\"DB_HOST\")\n\tif dbHost == \"\" {\n\t\tdbHost = \"localhost\" // Удобно для локального запуска без Docker\n\t}\n\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Connected to DB host: %s\\n\", dbHost)\n\t})\n\n\tlog.Println(\"Server running on :8080...\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис с гибким подключением к базе"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Поднимаем только базу данных\ndocker compose up -d\n\n# Запуск Go сервиса\ngo run main.go &\nPID=$!\n\nsleep 1\ncurl http://localhost:8080/\n\n# Остановка\nkill $PID\ndocker compose down -v"
      }
    ],
    "under_the_hood": "Проброс порта `5432:5432` открывает сокет на хостовой ОС. Приложение Go на хосте подключается к loopback-интерфейсу хоста, после чего демон Docker через iptables/docker-proxy форвардит TCP-пакеты в сетевое пространство имен контейнера PostgreSQL.",
    "pitfalls": "1. Конфликт портов, если на хосте уже работает локально установленный сервис PostgreSQL (`systemctl status postgresql`).\n2. Попытка обратиться к `postgres` по имени сервиса при запуске приложения вне Docker (на хосте имя `postgres` не разрешится без правки `/etc/hosts`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как сделать так, чтобы Go-сервис мог без изменения кода и конфигов работать как внутри контейнера Docker Compose, так и при локальном запуске на ноутбуке разработчика?»\n**Ответ:** Использовать переменные окружения с разумными дефолтами (12-Factor App). Если переменная `DATABASE_HOST` не задана, сервис по умолчанию подключается к `localhost:5432`. В `docker-compose.yml` переменная явно переопределяется на имя контейнера: `DATABASE_HOST=postgres`. Для чтения переменных удобно использовать файл `.env`, который подтягивается локально через `godotenv`, а в Docker Compose монтируется через `env_file`."
  },
  {
    "num": 50,
    "title": "Автоматизация сборки и запуска: Makefile и Taskfile обертка",
    "task": "**[Makefile / Taskfile]**: Напиши `Makefile` с командами `build`, `test`, `docker-build`, `docker-run`, `clean` для автоматизации рутинных задач.",
    "theory": "Запоминание длинных команд Docker (`docker buildx build ...`, `docker compose up -d`, `docker run -v ...`) снижает продуктивность и приводит к ошибкам разработчиков.\n\nИнструменты автоматизации (`Makefile` и современный `Taskfile` на YAML) стандартизируют интерфейс управления проектом:\n- `make build`: компиляция локального бинарника.\n- `make test`: запуск юнит- и интеграционных тестов.\n- `make docker-build`: сборка Docker-образа с правильными тегами и версионированием.\n- `make up` / `make down`: управление Compose-стеком.\n\nСпециальная директива `.PHONY` в Makefile гарантирует, что таски выполнятся, даже если в каталоге существуют файлы с аналогичными именами (`build`, `test`).",
    "step_by_step": "1. Создайте `Makefile` в корне Go-проекта.\n2. Опишите таски сборки, тестирования, сборки образа и запуска Compose.\n3. Протестируйте выполнение команд через `make docker-build` и `make up`.",
    "code_blocks": [
      {
        "filename": "Makefile",
        "lang": "makefile",
        "code": "APP_NAME ?= workout-service\nVERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo \"v1.0.0\")\nCOMMIT ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo \"dirty\")\n\n.PHONY: all build test docker-build up down clean\n\nall: build\n\nbuild:\n\t@echo \"==> Building Go binary...\"\n\tCGO_ENABLED=0 go build -ldflags=\"-w -s -X 'main.version=$(VERSION)'\" -o bin/app main.go\n\ntest:\n\t@echo \"==> Running tests...\"\n\tgo test -v -race ./...\n\ndocker-build:\n\t@echo \"==> Building Docker image $(APP_NAME):$(VERSION)...\"\n\tdocker build \\\n\t\t--build-arg VERSION=$(VERSION) \\\n\t\t--build-arg COMMIT=$(COMMIT) \\\n\t\t-t $(APP_NAME):$(VERSION) \\\n\t\t-t $(APP_NAME):latest .\n\nup:\n\t@echo \"==> Starting local infrastructure...\"\n\tdocker compose up -d\n\ndown:\n\t@echo \"==> Stopping infrastructure...\"\n\tdocker compose down\n\nclean:\n\t@rm -rf bin/",
        "note": "Production Makefile для Go-проекта"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\nvar version = \"dev\"\n\nfunc main() {\n\tfmt.Printf(\"Workout service initialized. Version: %s\\n\", version)\n}",
        "note": "Go сервис"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск компиляции через Make\nmake build\n\n# Проверка бинарника\n./bin/app\n\n# Очистка артефактов\nmake clean"
      }
    ],
    "under_the_hood": "Утилита `make` проверяет временные метки (mtime) файлов зависимостей. Если цель объявлена в `.PHONY`, make пропускает проверку существования одноименного файла на диске и всегда запускает привязанные команды в новом субшелле.",
    "pitfalls": "1. Использование пробелов вместо символа табуляции (`TAB`) в начале строк рецептов в Makefile: make выдаст синтаксическую ошибку `missing separator`.\n2. Забытый `.PHONY`: если случайно создать каталог `test/`, команда `make test` перестанет выполняться с сообщением `test is up to date`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем нужна директива `.PHONY:` в Makefile Go-проекта?»\n**Ответ:** По умолчанию Makefile предполагает, что имена целей (targets) — это файлы, которые должны быть созданы рецептом. Если на диске уже существует файл или папка с именем цели (например, директория `test` или файл `build`), make сочтет, что цель уже актуальна, и не станет выполнять команды. Объявление `.PHONY: build test` сообщает make, что это абстрактные команды, которые необходимо выполнять всегда независимо от состояния файловой системы."
  },
  {
    "num": 51,
    "title": "Безопасность: запуск процессов от непривилегированного пользователя",
    "task": "**Безопасность: запуск от не-root пользователя**: По умолчанию процессы в контейнере запускаются с правами суперпользователя `root`, что является критической уязвимостью в продакшене. Модифицируйте ваш `Dockerfile`: на этапе компиляции создайте системного пользователя `appuser` без домашних директорий, скопируйте файл `/etc/passwd` на финальный этап сборки и добавьте директиву `USER appuser`. Убедитесь, что приложение успешно работает без прав root.",
    "theory": "Запуск контейнеров от root по умолчанию — историческое наследие ранних версий Docker.\nВ современных корпоративных средах действует принцип нулевого доверия (Zero Trust) и модель наименьших привилегий (POLP — Principle of Least Privilege).\n\nПроцесс, исполняющийся под пользователем `appuser` (UID > 1000):\n- Не может изменять системные файлы (`/etc`, `/usr`).\n- Не может устанавливать или модифицировать пакеты ядра.\n- Не имеет capability для перехвата сетевого трафика (`CAP_NET_RAW`, `CAP_NET_ADMIN`).\n- При попытке побега из контейнера на хост злоумышленник сталкивается с ограничениями прав непривилегированного пользователя хоста.",
    "step_by_step": "1. Напишите Go-сервер.\n2. В `Dockerfile` создайте пользователя `appuser` с UID 10001.\n3. Переключитесь на пользователя `USER 10001:10001`.\n4. Проверьте через `docker exec <container> id`, что процесс запущен не под root.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/id\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Current Process UID: %d\\n\", os.Getuid())\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис проверки UID"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -o /app main.go\n\n# Создаем пользователя с фиксированным ID\nRUN adduser -D -u 10001 -s /sbin/nologin nonrootuser\n\nFROM alpine:3.20\nCOPY --from=builder /etc/passwd /etc/passwd\nCOPY --from=builder /app /app\n\nUSER 10001:10001\n\nEXPOSE 8080\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile с non-root пользователем"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t test-nonroot-audit:v1 .\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-nra test-nonroot-audit:v1\ncurl http://localhost:8080/id\ndocker rm -f test-nra"
      }
    ],
    "under_the_hood": "Демон containerd перед запуском процесса читает OCI Spec (`config.json`), где в поле `process.user` установлен `uid: 10001`. Вызывается системный вызов ядра `setresuid(10001, 10001, 10001)`, навсегда сбрасывающий привилегии суперпользователя для процесса и всех его будущих потомков.",
    "pitfalls": "1. Запуск бинарника, которому требуется писать в смонтированный volume, принадлежащий root (решается назначением владельца тома `chown`).\n2. Попытка слушать привилегированный порт 80.",
    "bigtech_interview": "**Вопрос с собеседования:** «Может ли процесс внутри контейнера с UID 10001 читать файлы на хост-машине при использовании Bind Mount?»\n**Ответ:** Только если эти файлы на хосте имеют права на чтение для всех пользователей (флаг `others read`, например `0644` или `0755`), либо если на хосте существует пользователь/группа с тем же числовым идентификатором UID/GID 10001, имеющий доступ к этим файлам. Если файл на хосте принадлежит `root` с правами `0600` или `0700`, процесс с UID 10001 получит ошибку `Permission denied`."
  },
  {
    "num": 52,
    "title": "Паттерн Init Container: выполнение миграций базы данных перед запуском приложения",
    "task": "Напиши **init-контейнер**: `migrations` контейнер запускается перед `app`, выполняет `golang-migrate`, завершается. `app` зависит от `migrations` (`depends_on` + condition). Покажи job pattern в Compose.",
    "theory": "Запуск миграций базы данных прямо из кода основного веб-сервиса — опасный антипаттерн в масштабируемых системах:\n- При горизонтальном масштабировании (HPA) 10 реплик сервиса одновременно попытаются выполнить `db.AutoMigrate()` или применить DDL-скрипты, что приведет к дедлокам в таблицах блокировок (`pg_locks`).\n- Если у сервиса нет прав DDL (создание таблиц, изменение индексов), а есть только DML (`SELECT`, `INSERT`), сервис не сможет стартовать.\n\nАрхитектурный паттерн **Init Container**:\n1. Отдельный легковесный контейнер (например, с утилитой `golang-migrate`) запускается **строго до** старта основного сервиса.\n2. Он применяет миграции и успешно завершается (`exit 0`).\n3. Только после успешного завершения init-контейнера Docker Compose или Kubernetes запускает основной контейнер сервиса.\n\nВ Docker Compose это реализуется через условие:\n```yaml\ndepends_on:\n  migrations:\n    condition: service_completed_successfully\n```",
    "step_by_step": "1. Создайте SQL-файл миграции `000001_init.up.sql`.\n2. Опишите в `docker-compose.yml` сервис `migrations` на базе образа `migrate/migrate`.\n3. Настройте зависимость основного сервиса `app` от `migrations` с условием `service_completed_successfully`.\n4. Запустите стек и проследите порядок исполнения в логах.",
    "code_blocks": [
      {
        "filename": "migrations/000001_create_users_table.up.sql",
        "lang": "sql",
        "code": "CREATE TABLE IF NOT EXISTS users (\n    id SERIAL PRIMARY KEY,\n    email VARCHAR(255) UNIQUE NOT NULL,\n    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP\n);\n\nINSERT INTO users (email) VALUES ('admin@example.com') ON CONFLICT DO NOTHING;",
        "note": "SQL файл начальной миграции"
      },
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  postgres:\n    image: postgres:16-alpine\n    environment:\n      POSTGRES_USER: devuser\n      POSTGRES_PASSWORD: devpass\n      POSTGRES_DB: devdb\n    healthcheck:\n      test: [\"CMD-SHELL\", \"pg_isready -U devuser -d devdb\"]\n      interval: 3s\n      timeout: 2s\n      retries: 5\n\n  # Init-контейнер для наката миграций\n  migrations:\n    image: migrate/migrate:v4.17.0\n    volumes:\n      - ./migrations:/migrations\n    entrypoint:\n      - \"migrate\"\n      - \"-path=/migrations\"\n      - \"-database=postgres://devuser:devpass@postgres:5432/devdb?sslmode=disable\"\n      - \"up\"\n    depends_on:\n      postgres:\n        condition: service_healthy\n\n  # Основной веб-сервер\n  app:\n    image: alpine:3.20\n    command: [\"echo\", \"App started safely after migrations!\"]\n    depends_on:\n      migrations:\n        condition: service_completed_successfully",
        "note": "docker-compose.yml с паттерном Init Container для миграций"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск стека: обратите внимание на последовательность\n# 1. postgres (healthy) -> 2. migrations (completed) -> 3. app\ndocker compose up\n\n# Очистка\ndocker compose down -v"
      }
    ],
    "under_the_hood": "Compose отслеживает состояние жизненного цикла контейнеров. Контейнер `migrations` переходит в статус `exited` с кодом 0. Compose проверяет условие `service_completed_successfully`, после чего инициирует создание и старт контейнера `app`.",
    "pitfalls": "1. Ошибка в SQL-миграции: init-контейнер завершится с кодом 1, и основной сервис никогда не будет запущен (Fail-Fast принцип).\n2. Забытый healthcheck у PostgreSQL: мигратор попытается подключиться к еще не готовой базе данных.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему выполнять автоматические миграции БД внутри функции `init()` или `main()` Go-микросервиса считается антипаттерном в продакшне?»\n**Ответ:** 1) Гонка блокировок (Race Condition): при одновременном старте нескольких реплик сервиса (Rolling Update) они конкурируют за накат миграций, что может приводить к взаимным блокировкам (Deadlock) или повреждению схемы. 2) Нарушение принципа наименьших привилегий: рабочий микросервис должен иметь только права DML (`SELECT`, `INSERT`, `UPDATE`, `DELETE`), тогда как миграции требуют DDL (`CREATE`, `ALTER`, `DROP`). Предоставление DDL-прав приложению увеличивает ущерб при SQL-инъекциях. Миграции должны запускаться изолированно через Init Containers или CI/CD пайплайн."
  },
  {
    "num": 53,
    "title": "Конфигурация через переменные окружения: 12-Factor App в Docker Compose",
    "task": "Реализуйте конфигурацию приложения через переменные окружения, пробрасываемые из `docker-compose` (DB_HOST, REDIS_ADDR).",
    "theory": "Третий фактор методологии **The Twelve-Factor App** гласит: «Храните конфигурацию в среде окружения».\n\nПреимущества конфигурации через переменные окружения (Environment Variables):\n1. Кодовая база абсолютно неизменна между стендами (local, stage, prod).\n2. Секреты и пароли не зашиваются в Docker-образ.\n3. Возможность динамического изменения параметров без перекомпиляции Go-кода.\n\nВ Docker Compose переменные окружения пробрасываются:\n- Через секцию `environment:` в виде списка или словаря.\n- Через директиву `env_file: .env` для централизованного управления.",
    "step_by_step": "1. Напишите Go-сервис, считывающий конфигурацию из `os.Getenv()`.\n2. Создайте файл `.env`.\n3. Опишите `docker-compose.yml`, использующий переменные окружения.\n4. Запустите сервис и убедитесь в корректном применении параметров.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\ntype Config struct {\n\tPort        string\n\tEnvironment string\n\tMaxConns    string\n}\n\nfunc loadConfig() Config {\n\tport := os.Getenv(\"PORT\")\n\tif port == \"\" {\n\t\tport = \"8080\"\n\t}\n\tenv := os.Getenv(\"APP_ENV\")\n\tif env == \"\" {\n\t\tenv = \"development\"\n\t}\n\tmaxConns := os.Getenv(\"MAX_CONNECTIONS\")\n\tif maxConns == \"\" {\n\t\tmaxConns = \"100\"\n\t}\n\n\treturn Config{Port: port, Environment: env, MaxConns: maxConns}\n}\n\nfunc main() {\n\tcfg := loadConfig()\n\n\thttp.HandleFunc(\"/config\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Active Config: Env=%s | MaxConns=%s\\n\", cfg.Environment, cfg.MaxConns)\n\t})\n\n\tfmt.Printf(\"Starting service on port :%s (Env: %s)...\\n\", cfg.Port, cfg.Environment)\n\t_ = http.ListenAndServe(\":\"+cfg.Port, nil)\n}",
        "note": "Go микросервис с чтением ENV"
      },
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  web:\n    build: .\n    ports:\n      - \"8080:8080\"\n    environment:\n      - PORT=8080\n      - APP_ENV=staging\n      - MAX_CONNECTIONS=500",
        "note": "docker-compose.yml с переменными окружения"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -o /app main.go\n\nFROM alpine:3.20\nCOPY --from=builder /app /app\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск\ndocker compose up -d\n\n# Проверка конфигурации\ncurl http://localhost:8080/config\n# Ответ: Active Config: Env=staging | MaxConns=500\n\ndocker compose down"
      }
    ],
    "under_the_hood": "Демон Docker при подготовке вызова `execve` формирует массив строк вида `\"KEY=VALUE\"` в адресном пространстве процесса. В Go рантайм считывает этот блок памяти при старте рантайма и заполняет внутреннюю мапу `syscall.Environ()`.",
    "pitfalls": "1. Забыть установить значения по умолчанию (fallbacks) в коде Go: если переменная не передана, приложение может упасть с `panic` при парсинге пустой строки.\n2. Путаница между переменными сборщика `ARG` и переменными рантайма `ENV`.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие директивы `ARG` от `ENV` в Dockerfile?»\n**Ответ:** `ARG` (Build Argument) существует **только во время сборки образа** (`docker build`) и недоступна в запущенном контейнере (если только значение `ARG` явно не передано в команду `ENV`). `ENV` (Environment Variable) доступна как во время сборки, так и **внутри запущенного контейнера в рантайме** (`docker run`). Значения `ENV` сохраняются в метаданных образа и наследуются всеми дочерними процессами."
  },
  {
    "num": 54,
    "title": "Ротация логов: драйвер json-file, ограничение max-size и max-file",
    "task": "Настрой **log rotation**: `logging.driver: \"json-file\"`, `logging.options.max-size: \"10m\"`, `logging.options.max-file: \"3\"`. Предотвращи заполнение диска логами. Альтернатива: `logging.driver: fluentd` для centralized logging.",
    "theory": "По умолчанию Docker перехватывает все потоки стандартного вывода `stdout` и ошибок `stderr` процессов контейнера и записывает их на диск хоста с помощью драйвера **`json-file`** по пути `/var/lib/docker/containers/<id>/<id>-json.log`.\n\nОпасность отсутствия ротации:\nЕсли приложение активно пишет логи (особенно под высокой нагрузкой или в цикле ошибок), один единственный контейнер может сгенерировать **десятки и сотни гигабайт логов**, полностью заполнив диск хостовой системы (`No space left on device`). Это приводит к остановке Docker демона и падению всех соседних сервисов!\n\nНастройка жесткой ротации:\n```yaml\nlogging:\n  driver: \"json-file\"\n  options:\n    max-size: \"10m\"\n    max-file: \"3\"\n```\nПри превышении размера файла в 10 МБ Docker архивирует его и начинает новый. Хранится максимум 3 файла, гарантируя, что логи сервиса **никогда не займут более 30 МБ диска**.",
    "step_by_step": "1. Создайте Go-сервис, непрерывно генерирующий логи в stdout.\n2. В `docker-compose.yml` настройте секцию `logging` с ограничением `max-size: 1m` и `max-file: 2`.\n3. Запустите контейнер и убедитесь в ограничении дискового пространства логов.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"log\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc main() {\n\tgo func() {\n\t\tfor {\n\t\t\tlog.Println(\"Production event log: processing incoming highload telemetry stream...\")\n\t\t\ttime.Sleep(200 * time.Millisecond)\n\t\t}\n\t}()\n\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.Write([]byte(\"Logging active\"))\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис с активным логированием"
      },
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  logger_app:\n    build: .\n    ports:\n      - \"8080:8080\"\n    logging:\n      driver: \"json-file\"\n      options:\n        max-size: \"1m\"\n        max-file: \"2\"\n    restart: unless-stopped",
        "note": "Compose с ротацией логов"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -o /app main.go\n\nFROM alpine:3.20\nCOPY --from=builder /app /app\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск\ndocker compose up -d\n\n# Проверка настроек логов контейнера\ndocker inspect --format='{{json .HostConfig.LogConfig}}' $(docker compose ps -q logger_app)\n\n# Просмотр последних логов\ndocker compose logs --tail 10 logger_app\n\n# Очистка\ndocker compose down"
      }
    ],
    "under_the_hood": "Демон Docker перенаправляет файловые дескрипторы 1 и 2 (stdout/stderr) контейнера в FIFO pipe. Горутина демона считывает строки, упаковывает их в JSON с меткой времени и пишет в текущий файл лога. При достижении `max-size` файл переименовывается в `.1`, а самый старый файл сверх лимита `max-file` удаляется системным вызовом `unlink`.",
    "pitfalls": "1. Запись логов в локальный файл внутри контейнера (`/app/app.log`): такой файл не виден в `docker logs` и при отсутствии ротации раздувает верхний слой контейнера.\n2. Отсутствие глобальной конфигурации ротации в `/etc/docker/daemon.json` на хост-сервере.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в продакшн-контейнерах категорически запрещено писать логи в локальные файлы на диск контейнера и требуется писать только в `stdout`/`stderr`?»\n**Ответ:** 1) 12-Factor App (Фактор 11 — Потоки событий): контейнер не должен управлять маршрутизацией или хранением своих логов. 2) Запись в файлы внутри контейнера раздувает writable layer OverlayFS, что снижает производительность I/O и переполняет диск без ротации. 3) При выводе в `stdout`/`stderr` инфраструктура (Docker Daemon, Fluentbit, Vector, Promtail) централизованно собирает логи, выполняет ротацию и отправляет их в ElasticSearch / ClickHouse / Grafana Loki."
  },
  {
    "num": 55,
    "title": "Надежный запуск: depends_on с условием condition: service_healthy",
    "task": "Используйте `depends_on` с health check, чтобы Go-сервис стартовал только после готовности БД.",
    "theory": "Классическая директива `depends_on: [db]` лишь гарантирует, что контейнер `db` будет создан и запущен *до* контейнера приложения. Она **не ждет**, пока СУБД внутри контейнера инициализирует таблицы и откроет сетевой порт для приема клиентских соединений.\n\nВ современном стандарте Docker Compose (v2) используется условие **`condition: service_healthy`**:\n```yaml\ndepends_on:\n  postgres:\n    condition: service_healthy\n```\n\nКак это работает:\n1. В сервисе `postgres` объявляется секция `healthcheck` (например, вызов `pg_isready`).\n2. Docker Compose запускает `postgres` и ждет, пока статус здоровья не станет `healthy`.\n3. Только после этого Compose запускает контейнер Go-сервиса `app`.\n4. Сервис гарантированно подключается к уже готовой к приему трафика базе данных!",
    "step_by_step": "1. Опишите в `docker-compose.yml` сервис `postgres` с `healthcheck`.\n2. В сервисе `app` укажите `depends_on` с условием `condition: service_healthy`.\n3. Запустите `docker compose up` и пронаблюдайте ожидание готовности базы в консоли.",
    "code_blocks": [
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  postgres:\n    image: postgres:16-alpine\n    environment:\n      POSTGRES_USER: myuser\n      POSTGRES_PASSWORD: mypassword\n      POSTGRES_DB: appdb\n    healthcheck:\n      test: [\"CMD-SHELL\", \"pg_isready -U myuser -d appdb\"]\n      interval: 2s\n      timeout: 2s\n      retries: 5\n      start_period: 2s\n\n  app:\n    build: .\n    ports:\n      - \"8080:8080\"\n    environment:\n      - DB_ADDR=postgres:5432\n    depends_on:\n      postgres:\n        condition: service_healthy",
        "note": "Compose с зависимостью по healthcheck"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\tdbAddr := os.Getenv(\"DB_ADDR\")\n\tconn, err := net.Dial(\"tcp\", dbAddr)\n\tif err != nil {\n\t\tlog.Fatalf(\"Fatal: Database is not ready: %v\", err)\n\t}\n\tconn.Close()\n\tlog.Println(\"Successfully connected to Database on first attempt!\")\n\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"App running! DB %s is verified healthy!\\n\", dbAddr)\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис, мгновенно подключающийся к БД"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -o /app main.go\n\nFROM alpine:3.20\nCOPY --from=builder /app /app\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск: Compose покажет 'Waiting for postgres to become healthy...'\ndocker compose up -d\n\n# Проверка\ncurl http://localhost:8080/\n\n# Очистка\ndocker compose down -v"
      }
    ],
    "under_the_hood": "Compose подписывается на поток событий Docker Engine (`docker events`). При получении события `health_status: healthy` для контейнера `postgres` внутренний конечный автомат Compose разблокирует переход сервиса `app` в состояние запуска.",
    "pitfalls": "1. Забытый `test` в секции `healthcheck` у базы данных: контейнер никогда не станет `healthy`, и Compose зависнет по таймауту.\n2. Слишком короткий таймаут `start_period`: на медленных машинах база не успеет инициализироваться.",
    "bigtech_interview": "**Вопрос с собеседования:** «Чем `depends_on: { condition: service_healthy }` принципиально лучше скриптов ожидания вроде `wait-for-it.sh` внутри образа приложения?»\n**Ответ:** 1) Чистота образов: приложению не нужно тащить в свой продакшн-образ сторонние bash-скрипты, `nc`, `curl` или `wget` (что особенно важно для `FROM scratch` и `distroless`). 2) Семантическая точность: `wait-for-it.sh` проверяет только открытие TCP-порта, тогда как база данных может слушать порт, но еще не завершить внутреннюю процедуру recovery/migration. Healthcheck проверяет реальную готовность СУБД выполнять SQL-запросы (`pg_isready` или `SELECT 1`)."
  },
  {
    "num": 56,
    "title": "Проблема медленного старта БД: устойчивая retry-логика с экспоненциальным backoff",
    "task": "**Проблема \"Упал до поднятия базы\" (Wait-for-it)**: Если `app` стартует быстрее, чем БД инициализируется, Go-приложение упадет при попытке подключения (упр. 366). Настрой переподключение в самом Go-коде (retry-цикл при старте) ИЛИ используй директиву `depends_on` с условием `condition: service_healthy` в docker-compose.",
    "theory": "В распределенных системах и облачных средах (Kubernetes, AWS ECS) сетевые соединения могут кратковременно обрываться, а базы данных — уходить в перезагрузку (Failover, Maintenance).\n\nЕсли Go-приложение при старте пытается подключиться к БД только один раз:\n```go\ndb, err := sql.Open(...)\nif err != nil || db.Ping() != nil {\n    log.Fatal(\"DB down\") // Падение сервиса!\n}\n```\nто малейшая задержка старта СУБД приведет к падению пода и переходу в статус `CrashLoopBackOff`.\n\nПаттерн устойчивости (**Resilient Startup with Exponential Backoff**):\nСервис не падает сразу, а предпринимает серию повторных попыток подключения с увеличивающимся интервалом и случайным джиттером (Jitter), пока база данных не станет доступной.",
    "step_by_step": "1. Напишите функцию `connectWithRetry` в Go с настраиваемым таймаутом и бэкоффом.\n2. Продемонстрируйте корректную работу приложения при отложенном старте базы данных.\n3. Убедитесь, что при превышении максимального таймаута приложение корректно логирует причину и завершается.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"math/rand\"\n\t\"net\"\n\t\"net/http\"\n\t\"os\"\n\t\"time\"\n)\n\nfunc connectWithRetry(ctx context.Context, target string, maxAttempts int) (net.Conn, error) {\n\tvar conn net.Conn\n\tvar err error\n\tbaseDelay := 500 * time.Millisecond\n\n\tfor attempt := 1; attempt <= maxAttempts; attempt++ {\n\t\tselect {\n\t\tcase <-ctx.Done():\n\t\t\treturn nil, ctx.Err()\n\t\tdefault:\n\t\t}\n\n\t\tconn, err = net.DialTimeout(\"tcp\", target, 2*time.Second)\n\t\tif err == nil {\n\t\t\tlog.Printf(\"Connected successfully to %s on attempt %d!\\n\", target, attempt)\n\t\t\treturn conn, nil\n\t\t}\n\n\t\t// Full Jitter: случайная пауза от 0 до baseDelay * 2^(attempt-1)\n\t\tdelay := time.Duration(rand.Int63n(int64(baseDelay * (1 << attempt))))\n\t\tif delay > 5*time.Second {\n\t\t\tdelay = 5 * time.Second\n\t\t}\n\n\t\tlog.Printf(\"Attempt %d failed (%v). Retrying in %v...\\n\", attempt, err, delay)\n\t\ttime.Sleep(delay)\n\t}\n\n\treturn nil, fmt.Errorf(\"failed to connect after %d attempts: %w\", maxAttempts, err)\n}\n\nfunc main() {\n\tdbAddr := os.Getenv(\"DB_ADDR\")\n\tif dbAddr == \"\" {\n\t\tdbAddr = \"127.0.0.1:5432\"\n\t}\n\n\tctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)\n\tdefer cancel()\n\n\tconn, err := connectWithRetry(ctx, dbAddr, 5)\n\tif err != nil {\n\t\tlog.Printf(\"Could not connect to DB: %v. Continuing in degraded mode...\\n\", err)\n\t} else {\n\t\tconn.Close()\n\t}\n\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"Resilient service is running!\")\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Устойчивая retry-логика подключения к БД"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -o /app main.go\n\nFROM alpine:3.20\nCOPY --from=builder /app /app\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t app-resilient:v1 .\n\n# Запуск сервиса без запущенной базы (продемонстрирует retry с бэкоффом)\ndocker run --rm -e DB_ADDR=127.0.0.1:9999 app-resilient:v1"
      }
    ],
    "under_the_hood": "Использование алгоритма экспоненциального бэкоффа с добавлением случайного шума (Full Jitter) предотвращает проблему «громоподобного стада» (Thundering Herd), когда сотни одновременно стартующих инстансов микросервиса обрушивают только что поднявшуюся базу данных миллионами одновременных попыток соединения.",
    "pitfalls": "1. Бесконечный retry без общего контекста таймаута: под зависает на старте навечно, не давая оркестратору зафиксировать ошибку конфигурации.\n2. Фиксированный интервал ретрая без Jitter: вызывает пиковую нагрузку (spikes) на БД.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое Thundering Herd Problem при рестарте базы данных и как экспоненциальный бэкофф с Jitter решает эту проблему в Go?»\n**Ответ:** Thundering Herd возникает, когда после сбоя или рестарта БД сотни инстансов сервисов одновременно и синхронно пытаются восстановить соединения с одинаковым фиксированным интервалом (например, ровно каждую секунду). Это создает резонансные всплески нагрузки на CPU и сетевой стек БД, снова выводя ее из строя. Добавление случайного разброса (Jitter: `delay = rand(0, 2^attempt * base)`) десинхронизирует запросы клиентов, распределяя нагрузку по времени и обеспечивая плавный ввод базы в строй."
  },
  {
    "num": 57,
    "title": "Усиление безопасности (Hardening): no-new-privileges, cap-drop=ALL и read-only rootfs",
    "task": "Настрой **Docker security**: `--security-opt=no-new-privileges`, `--cap-drop=ALL`, `--cap-add=NET_BIND_SERVICE` (если нужен порт <1024), `--read-only` root filesystem + tmpfs для `/tmp`. Покажи hardened container.",
    "theory": "Комплексное усиление безопасности контейнеров (**Container Hardening**) в соответствии с рекомендациями CIS Benchmarks и NSA/CISA Container Security Guide включает три ключевых барьера:\n\n1. **`--security-opt=no-new-privileges`:**\n   Запрещает процессу и его дочерним процессам получать новые привилегии через вызовы `setuid`/`setgid` программ.\n\n2. **`--cap-drop=ALL` (с селективным добавлением):**\n   Ядро Linux разделяет привилегии root на отдельные возможности (Linux Capabilities, `CAP_*`).\n   Сброс всех capabilities (`cap-drop: ALL`) отбирает у процесса возможность менять системное время (`CAP_SYS_TIME`), управлять сетевыми интерфейсами (`CAP_NET_ADMIN`), перехватывать сокеты (`CAP_NET_RAW`) и отлаживать другие процессы (`CAP_SYS_PTRACE`).\n\n3. **`--read-only` (Read-only Root Filesystem):**\n   Корневая файловая система контейнера монтируется в режиме только для чтения (`ro`). Злоумышленник физически не может изменить ни один бинарный файл, скрипт или конфигурацию в контейнере!\n   Временные файлы, необходимые для работы приложения, монтируются в оперативную память через `tmpfs` (`--tmpfs /tmp`).",
    "step_by_step": "1. Напишите Go-сервер.\n2. Создайте `docker-compose.yml` с максимальными настройками защиты: `read_only: true`, `cap_drop: [ALL]`, `no-new-privileges:true`.\n3. Запустите контейнер.\n4. Продемонстрируйте, что создание файлов в файловой системе контейнера блокируется ядром на уровне файловой системы.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/test-fs\", func(w http.ResponseWriter, r *http.Request) {\n\t\t// Попытка записать файл в корень\n\t\terr := os.WriteFile(\"/hack.sh\", []byte(\"#!/bin/sh\\n\"), 0755)\n\t\tif err != nil {\n\t\t\tfmt.Fprintf(w, \"Security Working: Root FS is READ-ONLY! (%v)\\n\", err)\n\t\t\treturn\n\t\t}\n\t\tfmt.Fprintln(w, \"SECURITY ALERT: Root FS is writable!\")\n\t})\n\n\thttp.HandleFunc(\"/test-tmpfs\", func(w http.ResponseWriter, r *http.Request) {\n\t\t// Запись во временный tmpfs каталог /tmp разрешена\n\t\terr := os.WriteFile(\"/tmp/valid_temp.txt\", []byte(\"in-memory-temp\"), 0644)\n\t\tif err != nil {\n\t\t\thttp.Error(w, err.Error(), 500)\n\t\t\treturn\n\t\t}\n\t\tfmt.Fprintln(w, \"Tmpfs write OK: Temporary files function normally in RAM.\")\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис для тестирования Hardened контейнера"
      },
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  hardened_app:\n    build: .\n    ports:\n      - \"8080:8080\"\n    # 1. Запрет повышения привилегий\n    security_opt:\n      - no-new-privileges:true\n    # 2. Полный сброс всех Capabilities ядра Linux\n    cap_drop:\n      - ALL\n    # 3. Файловая система контейнера только для чтения\n    read_only: true\n    # 4. Монтирование RAM-диска для временных файлов приложения\n    tmpfs:\n      - /tmp:rw,noexec,nosuid,size=64m\n    restart: unless-stopped",
        "note": "Эталонная конфигурация максимальной безопасности в Docker Compose"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -ldflags=\"-w -s\" -o /app main.go\n\nFROM alpine:3.20\nCOPY --from=builder /app /app\nUSER 10001:10001\nEXPOSE 8080\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск защищенного сервиса\ndocker compose up -d\n\n# Проверка режима Read-Only файловой системы (вернет Read-only file system)\ncurl http://localhost:8080/test-fs\n\n# Проверка работы tmpfs памяти (вернет Tmpfs write OK)\ncurl http://localhost:8080/test-tmpfs\n\n# Очистка\ndocker compose down"
      }
    ],
    "under_the_hood": "Флаг `read_only: true` инструктирует `runc` смонтировать корневую файловую систему с флагом `MS_RDONLY`. Любая операция `write()` или `open(..., O_WRONLY)` мгновенно отвергается драйвером файловой системы ядра Linux с кодом ошибки `EROFS` (Read-only file system). В свою очередь `cap_drop: ALL` устанавливает маску capabilities `prctl(PR_CAPBSET_DROP)` для всех битов.",
    "pitfalls": "1. Забыть смонтировать `tmpfs` в `/tmp`: если приложению требуется создать временный файл (например, парсер multipart/form-data при загрузке файлов в Go), запрос упадет с ошибкой `read-only file system`.\n2. Попытка использования библиотек, требующих создания временных файлов в несмонтированных каталогах.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какую защиту обеспечивает комбинация `read_only: true`, `cap_drop: [ALL]` и `no-new-privileges: true` в продакшн-контейнере?»\n**Ответ:** Эта комбинация реализует защиту от подавляющего большинства векторов атак: 1) Атакующий не может модифицировать файлы контейнера или записать вредоносный бинарник/бэкдор на диск (`read_only: true`). 2) Отсутствие Linux capabilities блокирует низкоуровневые атаки на сеть ядра, перехват пакетов и манипуляции с пространством памяти (`cap_drop: ALL`). 3) Запрет `no-new-privileges` гарантирует, что даже при наличии уязвимостей SUID в системных утилитах процесс не сможет повысить привилегии до root хоста."
  },
  {
    "num": 58,
    "title": "Горячая перезагрузка (Hot Reload) в Docker: использование утилиты Air",
    "task": "Настройте hot-reload для разработки: используйте `air` (github.com/air-verse/air) в контейнере с volume mount для исходников.",
    "theory": "При локальной разработке внутри контейнеров необходимость вручную перезапускать `docker compose restart app` после каждого изменения кода замедляет цикл обратной связи (Feedback Loop).\n\nУтилита **Air** (`github.com/air-verse/air`) реализует паттерн горячей перезагрузки (Hot Reload) для языка Go:\n1. Отслеживает изменения файлов проекта (`*.go`, `*.yaml`, `*.html`) через файловые нотификации ядра Linux `inotify`.\n2. Автоматически перекомпилирует бинарник на лету при сохранении файла.\n3. Корректно останавливает старый процесс и запускает новый скомпилированный бинарник за доли секунды.\n\nВ связке с Docker Compose исходные коды монтируются в контейнер через **Bind Mount** (`./:/app`), а кэш компилятора сохраняется в отдельном Named Volume для максимальной скорости пересборки.",
    "step_by_step": "1. Создайте конфигурационный файл `.air.toml`.\n2. Напишите `Dockerfile.dev` с установкой утилиты `air`.\n3. Опишите сервис в `docker-compose.yml` с bind mount исходников.\n4. Запустите контейнер `docker compose up`.\n5. Измените строку в `main.go` и пронаблюдайте автоматическую пересборку в логах Air.",
    "code_blocks": [
      {
        "filename": ".air.toml",
        "lang": "toml",
        "code": "root = \".\"\ntmp_dir = \"tmp\"\n\n[build]\n  cmd = \"go build -o ./tmp/main .\"\n  bin = \"tmp/main\"\n  full_bin = \"\"\n  include_ext = [\"go\", \"tpl\", \"tmpl\", \"html\", \"yaml\", \"yml\"]\n  exclude_dir = [\"assets\", \"tmp\", \"vendor\", \".git\"]\n  include_dir = []\n  exclude_file = []\n  delay = 500 # ms\n  stop_on_error = true\n  log = \"air.log\"\n\n[log]\n  time = true\n\n[color]\n  main = \"magenta\"\n  watcher = \"cyan\"\n  build = \"yellow\"\n  runner = \"green\" ",
        "note": "Файл конфигурации Air"
      },
      {
        "filename": "Dockerfile.dev",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine\n\n# Установка git и утилиты air для live-reload\nRUN go install github.com/air-verse/air@v1.61.5\n\nWORKDIR /app\n\n# Кэширование модулей\nCOPY go.mod go.sum* ./\nRUN go mod download\n\n# Запуск air вместо прямого go run\nCMD [\"air\", \"-c\", \".air.toml\"]",
        "note": "Dockerfile для разработки с Air"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Live reload with Air is working! Version 1.0\\n\")\n\t})\n\n\tlog.Println(\"Server running on :8080 with Air hot-reload...\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Микросервис"
      },
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  app:\n    build:\n      context: .\n      dockerfile: Dockerfile.dev\n    ports:\n      - \"8080:8080\"\n    volumes:\n      - ./:/app\n      - /app/tmp # Изолируем папку tmp от хоста",
        "note": "Compose с bind mount для Air"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск dev-окружения\ndocker compose up -d\n\n# Проверка ответа\ncurl http://localhost:8080/\n\n# Меняем строку в коде\nsed -i 's/Version 1.0/Version 2.0 (HOT RELOADED)/g' main.go\n\n# Ждем 1 секунду и проверяем: ответ изменился без перезапуска контейнера!\ncurl http://localhost:8080/\n\ndocker compose down"
      }
    ],
    "under_the_hood": "Air подписывается на события `IN_MODIFY`, `IN_CREATE` и `IN_DELETE` подсистемы ядра `inotify` для смонтированного каталога. При получении события Air отправляет дочернему процессу сигнал `SIGTERM`, ожидает его завершения и вызывает `fork/execve` нового бинарника из каталога `tmp/`.",
    "pitfalls": "1. Проблемы с inotify на macOS при использовании старых драйверов файловой системы Docker Desktop (требуется включить VirtioFS).\n2. Забытое исключение папки `tmp/` из bind mount, что может приводить к циклическим срабатываниям watcher'а.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему образ с `air` используется исключительно для локальной разработки и категорически запрещен к деплою в production?»\n**Ответ:** 1) Образ содержит полный компилятор Go, исходные коды и тулчейн сборщика (размер 800+ МБ), что резко расширяет attack surface. 2) Процесс компиляции внутри контейнера под нагрузкой может потреблять 100% CPU и памяти. 3) В продакшне действует принцип иммутабельной инфраструктуры: все инстансы должны работать на предварительно скомпилированных, протестированных и проверенных сканерами безопасности бинарниках."
  },
  {
    "num": 59,
    "title": "Сканирование уязвимостей: статический аудит образов через Trivy и Grype",
    "task": "Сканируй **vulnerabilities**: `docker scan myapp:v1` (Snyk) или `trivy image myapp:v1`. Проанализируй отчёт. Обнови base image, удали ненужные пакеты. Покажи CI gate: `CRITICAL` CVE = build failure.\n\n---",
    "theory": "Безопасность цепочки поставок ПО (Software Supply Chain Security) требует обязательного сканирования контейнерных образов на наличие известных уязвимостей (CVE — Common Vulnerabilities and Exposures).\n\nИнструменты аудита:\n1. **Trivy** (от Aqua Security): индустриальный стандарт сканирования контейнеров, репозиториев кода, пакетов Go и манифестов Kubernetes.\n2. **Grype** (от Anchore): быстрый сканер уязвимостей на базе базы уязвимостей vulnerability database.\n\nСканеры анализируют:\n- Пакеты базовой операционной системы (musl, glibc, openssl, busybox).\n- Зависимости Go из файла `go.mod` (сверкой с базами GitHub Advisory Database и NVD).\n- Конфигурационные дефекты (запуск от root, пустые пароли, открытые чувствительные порты).\n\nВ CI/CD пайплайнах сканеры настраиваются на прерывание билда при обнаружении уязвимостей уровня `CRITICAL` или `HIGH` (`--exit-code 1 --severity CRITICAL,HIGH`).",
    "step_by_step": "1. Соберите исследуемый Docker-образ.\n2. Запустите сканирование через Trivy: `trivy image --severity HIGH,CRITICAL <image>`.\n3. Изучите отчет с указанием CVE ID, уязвимого пакета и исправленной версии (Fixed Version).\n4. Настройте флаг прерывания CI пайплайна.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"Secure microservice inspected by Trivy\")\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Микросервис"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -ldflags=\"-w -s\" -o /bin/app main.go\n\n# Использование ультрабезопасного Distroless\nFROM gcr.io/distroless/static-debian12:nonroot\nCOPY --from=builder /bin/app /app\nENTRYPOINT [\"/app\"]",
        "note": "Безопасный Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка образа\ndocker build -t app-scanned:v1 .\n\n# Запуск сканирования через Trivy (в контейнере)\ndocker run --rm -v /var/run/docker.sock:/var/run/docker.sock \\\n  aquasec/trivy:latest image \\\n  --severity HIGH,CRITICAL \\\n  --exit-code 1 \\\n  app-scanned:v1 || echo \"Vulnerabilities detected! Build blocked.\"\n\n# Результат для Distroless покажет 0 vulnerabilities!"
      }
    ],
    "under_the_hood": "Trivy извлекает список файлов и метаданные пакетов (`/lib/apk/db/installed` в Alpine или базу Debian dpkg), вычисляет хэши бинарных зависимостей Go и сверяет их со своей локальной offline-базой данных сигнатур уязвимостей, обновляемой каждые несколько часов.",
    "pitfalls": "1. Сканирование только ОС без анализа зависимостей Go (`go.mod`/`go.sum`).\n2. Игнорирование предупреждений об уязвимостях в базовых образах (необходимость регулярного обновления версий базовых тегов).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как встроить сканирование Docker-образов в DevSecOps пайплайн так, чтобы ложные срабатывания (False Positives) не блокировали релизы критических фиксов?»\n**Ответ:** 1) Использовать флаг `--ignore-unfixed`, чтобы игнорировать CVE, для которых еще нет патча от мейнтейнеров дистрибутива. 2) Вести файл исключений `.trivyignore` в репозитории с обязательным указанием причины (Rationale), ссылки на тикет в Jira и даты пересмотра (Expiration Date). 3) Внедрить Vulnerability Management платформу (DefectDojo / Harbor) для централизованного аппрува исключений службой информационной безопасности."
  },
  {
    "num": 60,
    "title": "Локальное событийно-ориентированное окружение: Redis, Kafka и NATS в Compose",
    "task": "Добавьте Redis, Kafka и NATS в docker-compose для локальной разработки event-driven приложений.",
    "theory": "Event-Driven архитектура (EDA) на Go часто использует специализированные брокеры сообщений под разные задачи:\n1. **Redis:** оперативный кэш, распределенные блокировки (`redsync`) и Pub/Sub для веб-сокетов.\n2. **Apache Kafka (или Redpanda):** долговечный лог событий (Log-centric Event Streaming) с гарантией порядка и партиционированием для аналитики и аудита.\n3. **NATS JetStream:** сверхбыстрый легковесный брокер сообщений для межсервисной коммуникации в реальном времени с низкой задержкой (Sub-millisecond Latency).\n\nПоднятие всех этих компонентов в едином `docker-compose.yml` позволяет разработчику локально воспроизвести весь стек взаимодействия перед отправкой кода в кластер.",
    "step_by_step": "1. Напишите `docker-compose.yml` с сервисами Redis, Kafka (в режиме KRaft без Zookeeper) и NATS JetStream.\n2. Настройте внутреннюю сеть `event_net`.\n3. Запустите стек и проверьте готовность портов всех брокеров.",
    "code_blocks": [
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  # Быстрый кэш и Pub/Sub\n  redis:\n    image: redis:7-alpine\n    ports:\n      - \"6379:6379\"\n    networks:\n      - event_net\n\n  # NATS с поддержкой JetStream\n  nats:\n    image: nats:2.10-alpine\n    command: [\"-js\", \"-m\", \"8222\"]\n    ports:\n      - \"4222:4222\" # Клиентский порт\n      - \"8222:8222\" # HTTP мониторинг\n    networks:\n      - event_net\n\n  # Kafka в современном легковесном режиме KRaft (без Zookeeper)\n  kafka:\n    image: apache/kafka:3.8.0\n    environment:\n      KAFKA_NODE_ID: 1\n      KAFKA_PROCESS_ROLES: broker,controller\n      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093\n      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092\n      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER\n      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT\n      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093\n      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1\n      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1\n      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1\n      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0\n    ports:\n      - \"9092:9092\"\n    networks:\n      - event_net\n\nnetworks:\n  event_net:\n    driver: bridge",
        "note": "docker-compose.yml для полного Event-Driven стека"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc checkPort(addr string) string {\n\tconn, err := net.DialTimeout(\"tcp\", addr, 1*time.Second)\n\tif err != nil {\n\t\treturn fmt.Sprintf(\"DOWN (%v)\", err)\n\t}\n\tconn.Close()\n\treturn \"UP\"\n}\n\nfunc main() {\n\thttp.HandleFunc(\"/brokers\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Redis: %s\\nNATS:  %s\\nKafka: %s\\n\",\n\t\t\tcheckPort(\"redis:6379\"), checkPort(\"nats:4222\"), checkPort(\"kafka:9092\"))\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис проверки доступности брокеров"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск брокеров\ndocker compose up -d\n\n# Проверка статуса контейнеров\ndocker compose ps\n\n# Остановка\ndocker compose down"
      }
    ],
    "under_the_hood": "Apache Kafka в режиме KRaft использует собственный кворум на алгоритме Raft для управления метаданными топиков без отдельного кластера Apache ZooKeeper. NATS JetStream запускается с флагом `-js` и выделяет in-memory буферы для сохранения истории сообщений.",
    "pitfalls": "1. Высокое потребление оперативной памяти JVM внутри Kafka (для локальной разработки часто заменяют на легковесный аналог Redpanda на C++).\n2. Неверная настройка `KAFKA_ADVERTISED_LISTENERS`, из-за чего клиенты снаружи Docker не могут получить метаданные брокера.",
    "bigtech_interview": "**Вопрос с собеседования:** «В каких сценариях распределенной архитектуры на Go целесообразно использовать NATS JetStream вместо Apache Kafka?»\n**Ответ:** NATS JetStream выбирают, когда критически важны: 1) Ультранизкая задержка передачи сообщений (десятки микросекунд против миллисекунд в Kafka). 2) Минимальное потребление ресурсов (один статический бинарник на Go весом 20 МБ, потребляющий 30 МБ RAM против тяжелой JVM Kafka на 1-2 ГБ). 3) Простота развертывания и встроенная поддержка Request-Reply паттерна и Key-Value/Object Store из коробки."
  },
  {
    "num": 61,
    "title": "Управление переменными окружения: директива env_file в Docker Compose",
    "task": "Используйте `.env` файл для переменных окружения в docker-compose (`env_file: .env`).",
    "theory": "Когда количество параметров конфигурации микросервиса превышает 10–15 переменных, перечисление их в блоке `environment:` файла `docker-compose.yml` делает файл нечитаемым и усложняет версионирование.\n\nРешение: **директива `env_file:`**.\n```yaml\nservices:\n  app:\n    env_file:\n      - .env\n      - .env.local\n```\n\nПринципы безопасного управления:\n1. Файл `.env.example` коммитится в Git как образец со всеми ключами и фиктивными значениями.\n2. Файл `.env` с реальными локальными паролями добавляется в `.gitignore` и никогда не попадает в репозиторий.\n3. Compose считывает переменные из указанных файлов и пробрасывает их в контейнер.",
    "step_by_step": "1. Создайте файл `.env.example` с описанием параметров.\n2. Создайте локальный файл `.env`.\n3. Подключите его в `docker-compose.yml` через `env_file: .env`.\n4. Запустите сервис и проверьте успешное считывание переменных в коде Go.",
    "code_blocks": [
      {
        "filename": ".env.example",
        "lang": "bash",
        "code": "# Образец конфигурации окружения\nAPP_PORT=8080\nDATABASE_URL=postgres://user:password@postgres:5432/dbname?sslmode=disable\nREDIS_ADDR=redis:6379\nJWT_SECRET=replace_me_with_random_secret_32_bytes",
        "note": "Файл-шаблон .env.example (коммитится в Git)"
      },
      {
        "filename": ".env",
        "lang": "bash",
        "code": "APP_PORT=8080\nDATABASE_URL=postgres://dev:localpass@postgres:5432/appdb?sslmode=disable\nREDIS_ADDR=redis:6379\nJWT_SECRET=c8f12a349b7e4112e09cda8712345678",
        "note": "Локальный секретный файл .env (в .gitignore)"
      },
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  app:\n    build: .\n    ports:\n      - \"${APP_PORT:-8080}:8080\"\n    env_file:\n      - .env",
        "note": "docker-compose.yml с env_file"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\tport := os.Getenv(\"APP_PORT\")\n\tsecret := os.Getenv(\"JWT_SECRET\")\n\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"App configured via env_file! Port: %s, Secret length: %d\\n\", port, len(secret))\n\t})\n\t_ = http.ListenAndServe(\":\"+port, nil)\n}",
        "note": "Go микросервис"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -o /app main.go\n\nFROM alpine:3.20\nCOPY --from=builder /app /app\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск Compose с автоматическим чтением .env\ndocker compose up -d\n\n# Проверка ответа\ncurl http://localhost:8080/\n\n# Очистка\ndocker compose down"
      }
    ],
    "under_the_hood": "Compose парсит файлы, указанные в `env_file`, удаляет комментарии (`#`) и пробелы, и добавляет переменные в массив `Env` конфигурации контейнера при вызове Docker Engine API. Если переменная одновременно указана в `env_file` и в секции `environment:`, приоритет имеет значение из `environment:`.",
    "pitfalls": "1. Случайный коммит файла `.env` в публичный репозиторий GitHub.\n2. Пробелы вокруг знака равенства (`KEY = VALUE`), что может вызывать ошибки парсинга в старых версиях Compose.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каков порядок приоритета переменных окружения в Docker Compose, если одна и та же переменная определена в `environment:`, `env_file:` и в переменных хостовой системы (shell)?»\n**Ответ:** Порядок приоритета (от наивысшего к наинизшему): 1) Переменные, заданные в секции `environment:` файла `docker-compose.yml`. 2) Переменные командной строки shell хоста (или файла `.env`, интерполируемые в YAML). 3) Переменные из файлов, перечисленных в директиве `env_file:`. 4) Значения `ENV`, жестко прописанные в самом `Dockerfile` базового образа."
  },
  {
    "num": 62,
    "title": "Персистентность Docker Volumes: гарантия сохранности данных при пересоздании",
    "task": "**Docker Volumes (Постоянство данных)**: Убей контейнеры из упр. 582 (`docker compose down`). Подними снова. Убедись, что все данные из базы исчезли. Настрой именованный Volume в `docker-compose.yml` и примонтируй его в `db` (в `/var/lib/postgresql/data`), чтобы данные переживали рестарт контейнеров.",
    "theory": "Ключевое свойство именованных томов (Named Volumes) — независимый от контейнера жизненный цикл.\n\nПри выполнении команд:\n- `docker compose stop`: контейнеры останавливаются, тома остаются нетронутыми.\n- `docker compose down`: контейнеры и сети удаляются, **тома остаются на диске**.\n- `docker compose up -d`: создаются новые контейнеры, к которым монтируются старые тома со всеми ранее записанными данными.\n\nТолько явное указание флага `-v` (`docker compose down -v`) приводит к удалению именованных томов проекта.",
    "step_by_step": "1. Поднимите связку с PostgreSQL и Named Volume.\n2. Запишите в БД запись о заказе пользователя.\n3. Удалите контейнеры командой `docker compose down`.\n4. Снова выполните `docker compose up -d`.\n5. Убедитесь, что запись о заказе присутствует в базе данных.",
    "code_blocks": [
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  db:\n    image: postgres:16-alpine\n    environment:\n      POSTGRES_USER: shopuser\n      POSTGRES_PASSWORD: shoppassword\n      POSTGRES_DB: shopdb\n    volumes:\n      - shop_db_data:/var/lib/postgresql/data\n    ports:\n      - \"5432:5432\"\n\nvolumes:\n  shop_db_data:",
        "note": "Compose с именованным томом"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# 1. Запуск\ndocker compose up -d\n\n# 2. Создание таблицы и вставка строки\ndocker compose exec db psql -U shopuser -d shopdb -c \\\n  \"CREATE TABLE orders (id int, item text); INSERT INTO orders VALUES (101, 'MacBook Pro M3');\"\n\n# 3. Полное удаление контейнеров (БЕЗ флага -v)\ndocker compose down\n\n# 4. Повторный запуск контейнеров с нуля\ndocker compose up -d\n\n# 5. Проверка сохранения данных в томе shop_db_data\ndocker compose exec db psql -U shopuser -d shopdb -c \"SELECT * FROM orders;\"\n\n# 6. Очистка с удалением тома\ndocker compose down -v"
      }
    ],
    "under_the_hood": "Каталог тома хранится вне пула контейнеров в `/var/lib/docker/volumes/shop_db_data/_data`. При удалении контейнера рантайм `runc` просто вызывает системный вызов `umount`. Физические файлы базы данных остаются нетронутыми на файловой системе хоста.",
    "pitfalls": "1. Ошибочный запуск скриптов очистки с флагом `-v` в продакшне.\n2. Бэкапы: сохранение тома не отменяет необходимости регулярного создания логических дампов (`pg_dump`) или физических копий WAL.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как создать резервную копию (backup) данных из Docker Named Volume на хост-машину без остановки сервиса?»\n**Ответ:** Запустить временный служебный контейнер с одновременным монтированием целевого тома и локальной директории хоста: `docker run --rm -v shop_db_data:/data:ro -v $(pwd):/backup alpine tar czf /backup/db_backup.tar.gz -C /data .`. Флаг `:ro` гарантирует, что операция снятия архива не повредит файлы тома во время чтения."
  },
  {
    "num": 63,
    "title": "Hot Reload в Docker: связка Bind Mount исходников и Air для мгновенного отклика",
    "task": "**[Hot Reload в Docker]**: Настрой Docker Compose для локальной разработки с использованием утилиты `air` (горячая перезагрузка кода). Смонтируй локальную папку в контейнер.",
    "theory": "При классической разработке в контейнере изменение одной строки требует выполнения `docker build` (10–30 секунд) и `docker run`. За рабочий день программист теряет до часа времени.\n\nОптимальная архитектура Hot Reload для Go:\n1. Образ `Dockerfile.dev` содержит тулчейн Go и бинарник `air`.\n2. Текущая директория проекта с исходным кодом монтируется в контейнер через **Bind Mount**:\n   `volumes: [\".:/app\"]`\n3. Директории кэша модулей и компилятора изолируются в Named Volumes, чтобы не загрязнять хост и ускорить компиляцию:\n   `volumes: [\"pkg_cache:/go/pkg/mod\", \"build_cache:/root/.cache/go-build\"]`\n4. Время отклика при сохранении файла: **менее 300 миллисекунд**!",
    "step_by_step": "1. Настройте `Dockerfile.dev` с установкой Air.\n2. Опишите сервис в `docker-compose.yml` с монтированием исходников и кэшей.\n3. Запустите стек и протестируйте моментальное обновление эндпоинта.",
    "code_blocks": [
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  dev_server:\n    build:\n      context: .\n      dockerfile: Dockerfile.dev\n    ports:\n      - \"8080:8080\"\n    volumes:\n      - ./:/app:cached\n      - pkg_cache:/go/pkg/mod\n      - build_cache:/root/.cache/go-build\n\nvolumes:\n  pkg_cache:\n  build_cache:",
        "note": "docker-compose.yml для эффективного Hot-Reload"
      },
      {
        "filename": "Dockerfile.dev",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine\n\nRUN go install github.com/air-verse/air@v1.61.5\n\nWORKDIR /app\n\nCOPY go.mod go.sum* ./\nRUN go mod download\n\nCMD [\"air\"]",
        "note": "Dockerfile.dev"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Instant feedback loop with Air and Docker volumes!\\n\")\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Микросервис"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск\ndocker compose up -d\n\n# Проверка\ncurl http://localhost:8080/\n\ndocker compose down"
      }
    ],
    "under_the_hood": "Флаг `:cached` в bind mount оптимизирует производительность файлового ввода-вывода в macOS/Windows Docker Desktop, разрешая временную задержку синхронизации чтения между хостом и виртуальной машиной Linux, что исключает лаги компилятора при чтении сотен файлов Go.",
    "pitfalls": "1. Забыть изолировать директорию `/app/tmp`, из-за чего локальный бинарник Linux может затирать файлы хоста.\n2. Запуск контейнера без проброса портов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему при монтировании bind mount на macOS скорость `go build` внутри контейнера Docker может быть в 10 раз ниже, чем на Linux хосте?»\n**Ответ:** На macOS Docker работает внутри легковесной виртуальной машины Linux. Файлы хоста передаются через виртуальную файловую систему (ранее osxfs, теперь VirtioFS/gRPC-FUSE). Компилятор Go при сборке выполняет десятки тысяч системных вызовов `stat()`, `open()` и `read()`. Каждая операция пересекает границу VM с сетевым оверхедом. Решение: выносить кэши `$GOPATH/pkg` и `$GOCACHE` в нативные Docker Named Volumes, которые физически живут внутри файловой системы ext4 виртуальной машины."
  },
  {
    "num": 64,
    "title": "Тестирование внутри контейнера: выделенный этап сборки (test stage)",
    "task": "Соберите образ и запустите интеграционные тесты внутри контейнера (отдельный stage для тестов).",
    "theory": "Запуск юнит- и интеграционных тестов внутри контейнера гарантирует 100% повторяемость тестового окружения независимо от ОС разработчика (Linux, macOS, Windows).\n\nАрхитектура многоэтапного тестирования в Dockerfile:\n1. `AS builder`: загрузка зависимостей и компиляция.\n2. `AS test`: специальный этап сборки, запускающий `go test -v -race ./...`.\n3. `AS runtime`: финальный продакшн-образ.\n\nЕсли хотя бы один тест падает, сборка Dockerfile завершается с ошибкой на этапе `test`, и продакшн-образ физически **не будет собран**!\nЦелевой этап можно вызвать в CI командой:\n`docker build --target test -t app-test .`",
    "step_by_step": "1. Напишите функцию Go и модульный тест к ней.\n2. В `Dockerfile` выделите отдельный этап `FROM builder AS test`.\n3. Задайте команду запуска тестов с проверкой гонок данных (`-race`).\n4. Соберите этап `test` и убедитесь, что билд прерывается при падении тестов.",
    "code_blocks": [
      {
        "filename": "calc.go",
        "lang": "go",
        "code": "package main\n\nfunc Add(a, b int) int {\n\treturn a + b\n}",
        "note": "Бизнес-логика"
      },
      {
        "filename": "calc_test.go",
        "lang": "go",
        "code": "package main\n\nimport \"testing\"\n\nfunc TestAdd(t *testing.T) {\n\tif Add(2, 3) != 5 {\n\t\tt.Errorf(\"Expected 5, got %d\", Add(2, 3))\n\t}\n}",
        "note": "Модульный тест"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# Базовый этап сборщика\nFROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY . .\n\n# Выделенный этап тестирования\nFROM builder AS test\nRUN CGO_ENABLED=1 apk add --no-cache gcc musl-dev && \\\n    go test -v -race ./...\n\n# Финальный продакшн этап\nFROM builder AS prod-builder\nRUN CGO_ENABLED=0 go build -ldflags=\"-w -s\" -o /bin/app .\n\nFROM scratch AS release\nCOPY --from=prod-builder /bin/app /app\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile с выделенным тестовым этапом"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск только этапа тестов в CI/CD\ndocker build --target test -t myapp-tests .\n\n# Сборка финального релиза (автоматически выполнит тесты при правильной зависимости)\ndocker build --target release -t myapp-release:v1 ."
      }
    ],
    "under_the_hood": "BuildKit строит граф выполнения. При указании флага `--target test` сборщик вычисляет путь в графе только до целевого этапа `test`, пропуская генерацию финального этапа `release`, что экономит время CI пайплайна.",
    "pitfalls": "1. Запуск детекторов гонок (`-race`) при `CGO_ENABLED=0`: Race Detector в Go требует CGO и компилятора GCC.\n2. Пропуск кэша тестов при повторных сборках.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем выделять отдельный этап `AS test` в Dockerfile, если тесты можно запустить на CI-раннере командой `go test ./...` до вызова `docker build`?»\n**Ответ:** 1) Изоляция окружения: запуск внутри Docker гарантирует идентичные версии Go, системных библиотек, glibc/musl и заголовочных файлов, исключая ситуацию «на ноутбуке разработчика работает, а в CI падает». 2) Возможность поднятия в тестовом контейнере необходимых локальных сервисов (например, тестового SQLite или моков). 3) Унификация CI пайплайна: раннеру не требуется установленный тулчейн Go — достаточно только наличия Docker демона."
  },
  {
    "num": 65,
    "title": "Оптимизация кэширования слоев: продвинутые техники BuildKit",
    "task": "**Оптимизация кэширования слоев**: Каждый шаг в `Dockerfile` создает слой, который кэшируется. Напишите команды копирования и сборки в таком порядке, чтобы при изменении файлов с кодом Go вам не приходилось заново скачивать все внешние зависимости из `go.mod`. (Подсказка: сначала копируйте только `go.mod` и `go.sum`, запускайте `RUN go mod download`, а уже потом копируйте остальной код и запускайте компиляцию).",
    "theory": "Максимальная скорость сборки контейнеров достигается глубоким пониманием механики кэширования BuildKit:\n\n1. **Минимизация частоты инвалидации:**\n   Команды, которые меняются реже всего (`RUN apk add`, `COPY go.mod`), размещаются в самом начале `Dockerfile`. Команды, меняющиеся постоянно (`COPY . .`, `RUN go build`), — в самом конце.\n\n2. **Inline кэширование и Remote Cache:**\n   В CI/CD билд-агенты часто создаются с нуля (Stateless Runners). Чтобы не качать зависимости заново, BuildKit умеет сохранять кэш сборки прямо в Docker Registry:\n   `docker buildx build --cache-to type=registry,ref=myreg/app:cache --cache-from type=registry,ref=myreg/app:cache .`\n\n3. **Mounting кэша компилятора:**\n   `--mount=type=cache,target=/root/.cache/go-build` обеспечивает инкрементальную компиляцию Go-кода даже при чистом запуске.",
    "step_by_step": "1. Настройте эталонный порядок директив в `Dockerfile`.\n2. Используйте BuildKit cache mounts.\n3. Продемонстрируйте время инкрементальной сборки при изменении одной функции.",
    "code_blocks": [
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# syntax=docker/dockerfile:1\nFROM golang:1.24-alpine AS builder\n\nWORKDIR /src\n\n# 1. Системные пакеты (кэшируются почти навсегда)\nRUN apk add --no-cache git ca-certificates tzdata\n\n# 2. Модули Go\nCOPY go.mod go.sum* ./\nRUN --mount=type=cache,target=/go/pkg/mod \\\n    go mod download\n\n# 3. Исходный код\nCOPY . .\n\n# 4. Инкрементальная компиляция\nRUN --mount=type=cache,target=/go/pkg/mod \\\n    --mount=type=cache,target=/root/.cache/go-build \\\n    CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /bin/app .\n\nFROM scratch\nCOPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/\nCOPY --from=builder /bin/app /app\nENTRYPOINT [\"/app\"]",
        "note": "Идеально оптимизированный по кэшу Dockerfile"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"Fast cached compile!\")\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Go микросервис"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Включение BuildKit\nexport DOCKER_BUILDKIT=1\n\n# Сборка\ndocker build -t app-cache-opt:latest ."
      }
    ],
    "under_the_hood": "BuildKit строит граф выполнения в виде низкоуровневого формата LLB (Low-Level Builder). Сборщик вычисляет хэши операций параллельно и запускает независимые стадии сборки одновременно в разных потоках CPU.",
    "pitfalls": "1. Использование неявных временных меток в аргументах `ARG TIMESTAMP=$(date)` в начале Dockerfile, что сбрасывает кэш всех последующих слоев при каждом запуске.\n2. Неиспользование `.dockerignore`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему директиву `ARG BUILD_DATE` следует помещать как можно ближе к концу Dockerfile, непосредственно перед финальной компиляцией?»\n**Ответ:** Если объявить `ARG BUILD_DATE` в начале файла, то при передаче текущей даты/времени в каждом CI пайплайне значение аргумента меняется. Это приведет к полной инвалидации кэша Docker на самом первом шаге, заставляя заново скачивать базовые образы, пакеты и все Go-модули. Размещение аргумента в самом конце сохраняет кэш всех предыдущих тяжелых слоев нетронутым."
  },
  {
    "num": 66,
    "title": "Управление профилями сервисов (Compose Profiles): dev, test, metrics",
    "task": "Создайте несколько compose profiles: `docker compose --profile dev up` для разработки, `--profile test` для интеграционных тестов.",
    "theory": "В крупных проектах конфигурация `docker-compose.yml` содержит десятки сервисов: основное приложение, БД, брокеры, Prometheus, Grafana, Jaeger, почтовые заглушки (MailHog), моки внешних API.\nЗапуск всех сервисов одновременно перегружает оперативную память ноутбука разработчика.\n\nМеханизм **Compose Profiles** позволяет группировать сервисы по профилям:\n```yaml\nservices:\n  prometheus:\n    image: prom/prometheus\n    profiles: [\"metrics\", \"monitoring\"]\n\n  mock_payment_gateway:\n    image: wiremock/wiremock\n    profiles: [\"test\"]\n```\n\nПравила работы:\n- Сервисы без профилей запускаются всегда по умолчанию (`docker compose up`).\n- Сервисы с профилями запускаются **только при явном указании профиля**:\n  `docker compose --profile metrics up -d`\n  или через переменную окружения `COMPOSE_PROFILES=metrics,dev`.",
    "step_by_step": "1. Опишите `docker-compose.yml` с базовым сервисом и опциональными сервисами с профилями `metrics` и `tools`.\n2. Запустите стек по умолчанию: убедитесь, что сервисы мониторинга не стартовали.\n3. Запустите стек с профилем `docker compose --profile metrics up -d`.\n4. Проверьте запуск Prometheus.",
    "code_blocks": [
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  # Основной сервис — запускается всегда\n  app:\n    image: alpine:3.20\n    command: [\"sleep\", \"3600\"]\n\n  # Мониторинг — запускается только при --profile metrics\n  prometheus:\n    image: prom/prometheus:v2.52.0\n    profiles:\n      - metrics\n      - monitoring\n    ports:\n      - \"9090:9090\"\n\n  # Инструменты отладки — запускаются только при --profile debug\n  netshoot:\n    image: nicolaka/netshoot\n    profiles:\n      - debug\n    command: [\"sleep\", \"3600\"]",
        "note": "docker-compose.yml с профилями"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Стандартный запуск (запустится только app)\ndocker compose up -d\ndocker compose ps\n\n# Запуск с профилем metrics (дополнительно запустится prometheus)\ndocker compose --profile metrics up -d\ndocker compose ps\n\n# Остановка всего\ndocker compose --profile metrics down"
      }
    ],
    "under_the_hood": "Compose фильтрует граф сервисов перед вызовом Docker API. Сервисы, профили которых не активированы, исключаются из плана развертывания вместе со своими анонимными томами и связями.",
    "pitfalls": "1. Ошибки в именах профилей.\n2. Зависимости между сервисами разных профилей: если базовый сервис зависит через `depends_on` от сервиса с неактивным профилем, Compose выдаст ошибку конфигурации.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем использовать механизм `profiles` в Docker Compose вместо создания нескольких разрозненных compose-файлов?»\n**Ответ:** Профили позволяют хранить всю топологию проекта в одном месте, исключая дублирование определений сетей, именованных томов и общих конфигураций. Это гарантирует, что стек мониторинга или мок-сервисы будут подключены к той же самой сети и volume, что и основное приложение, с минимальной вероятностью рассинхронизации конфигурации."
  },
  {
    "num": 67,
    "title": "Изоляция окружений: Custom Networks для предотвращения сетевых конфликтов",
    "task": "Настройте custom network для изоляции сервисов и избежания конфликтов портов с другими проектами.",
    "theory": "При одновременной работе над несколькими проектами на одной машине или в рамках сложной микросервисной системы дефолтная сеть Docker bridge может приводить к конфликтам портов и нежелательной взаимной видимости сервисов.\n\nНастройка пользовательских сетей (**Custom Networks**) позволяет:\n1. **Изолировать внутренний контур:** база данных и кэш подключаются к `backend_net` без выхода в публичную сеть.\n2. **Ограничить доступ шлюза:** API Gateway подключается одновременно к `frontend_net` и `backend_net`.\n3. Задать фиксированные подсети (Subnet CIDR) и имена мостов хоста.",
    "step_by_step": "1. Опишите две изолированные сети: `frontend_net` и `backend_net`.\n2. Подключите Go веб-сервер к обеим сетям.\n3. Подключите PostgreSQL только к `backend_net`.\n4. Проверьте изоляцию базы данных от внешней сети.",
    "code_blocks": [
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  gateway:\n    image: alpine:3.20\n    command: [\"sleep\", \"3600\"]\n    networks:\n      - frontend_net\n      - backend_net\n\n  database:\n    image: postgres:16-alpine\n    environment:\n      POSTGRES_PASSWORD: secret\n    networks:\n      - backend_net # База изолирована от frontend_net!\n\nnetworks:\n  frontend_net:\n    driver: bridge\n  backend_net:\n    driver: bridge\n    internal: true # Полный запрет доступа во внешний интернет!",
        "note": "Compose с изолированными сетями и флагом internal: true"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск\ndocker compose up -d\n\n# Проверка списка сетей\ndocker network ls | grep workout\n\ndocker compose down"
      }
    ],
    "under_the_hood": "Флаг `internal: true` заставляет Docker настроить правила iptables без маскарадинга (MASQUERADE / SNAT) и без шлюза по умолчанию (default gateway). Контейнеры в этой сети могут общаться только между собой и физически не имеют доступа в интернет.",
    "pitfalls": "1. Попытка установить пакеты (`apk add`) внутри контейнера в сети `internal: true` (запрос упадет по таймауту из-за отсутствия интернета).\n2. Забыть подключить связующий сервис (BFF/Gateway) ко второй сети.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем указывать `internal: true` в определении сети Docker Compose для баз данных?»\n**Ответ:** Флаг `internal: true` запрещает демону Docker настраивать маршрут по умолчанию во внешнюю сеть и правила трансляции сетевых адресов (NAT/MASQUERADE). База данных оказывается в полностью изолированном сетевом сегменте: она может взаимодействовать только с разрешенными сервисами из этой же подсети, исключая утечку трафика в интернет или атаки с эксфильтрацией данных при взломе СУБД."
  },
  {
    "num": 68,
    "title": "Makefile обертка: стандартизация команд сборки, тестов, линтинга и Compose",
    "task": "**Makefile обертка**: Создай `Makefile` в корне проекта. Напиши таски: `make build` (собирает образ), `make up` (поднимает compose), `make down`, `make logs`. Инженеры любят Makefiles за короткие команды.\n\n---",
    "theory": "Инженерная культура BigTech компаний требует, чтобы разработчик мог приступить к работе с репозиторием одной командой:\n`git clone ... && make run`\n\nХорошо спроектированный `Makefile`:\n1. Автоматически извлекает метаданные Git (версия, хэш коммита, статус ветки).\n2. Предоставляет самодокументируемый хелп (`make help`).\n3. Стандартизирует запуск линтеров (`golangci-lint`), тестов, сборки образов и управления Compose-стеком.\n4. Используется одинаково как на локальных машинах разработчиков, так и внутри CI/CD раннеров.",
    "step_by_step": "1. Создайте универсальный `Makefile` с автодокументированием.\n2. Реализуйте таски: `build`, `test`, `lint`, `docker-build`, `up`, `down`.\n3. Проверьте выполнение команды `make help`.",
    "code_blocks": [
      {
        "filename": "Makefile",
        "lang": "makefile",
        "code": "BIN_DIR := bin\nAPP_NAME := workout-app\nVERSION ?= $(shell git describe --tags --always 2>/dev/null || echo \"v0.1.0\")\n\n.PHONY: help build test lint docker-build up down clean\n\nhelp: ## Отобразить список доступных команд\n\t@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = \":.*?## \"}; {printf \"\\033[36m%-16s\\033[0m %s\\n\", $$1, $$2}'\n\nbuild: ## Скомпилировать бинарник Go\n\t@mkdir -p $(BIN_DIR)\n\tCGO_ENABLED=0 go build -ldflags=\"-w -s\" -o $(BIN_DIR)/$(APP_NAME) main.go\n\ntest: ## Запустить все тесты\n\tgo test -v -race -cover ./...\n\nlint: ## Запустить статический анализ кода\n\tgolangci-lint run ./...\n\ndocker-build: ## Собрать оптимизированный Docker-образ\n\tdocker build -t $(APP_NAME):$(VERSION) -t $(APP_NAME):latest .\n\nup: ## Запустить локальный стек сервисов в фоне\n\tdocker compose up -d\n\ndown: ## Остановить локальный стек сервисов\n\tdocker compose down\n\nclean: ## Удалить бинарники и артефакты\n\trm -rf $(BIN_DIR)",
        "note": "Самодокументируемый Production Makefile"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\nfunc main() {\n\tfmt.Println(\"Clean architecture Makefile wrapper demo!\")\n}",
        "note": "Go приложение"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Просмотр справки\nmake help\n\n# Сборка бинарника\nmake build\n\n# Очистка\nmake clean"
      }
    ],
    "under_the_hood": "Скрипт awk в таске `help` парсит комментарии с двойным октоторпом `##` в самом Makefile, автоматически генерируя цветную документацию CLI без необходимости вручную синхронизировать описание команд.",
    "pitfalls": "1. Замена табуляций пробелами.\n2. Неиспользование переменных `?=` (переопределяемых переменных окружения).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Enterprise-командах предпочитают использовать Makefile для оборачивания команд Docker, а не писать bash-скрипты?»\n**Ответ:** Makefile предоставляет единый, проверенный десятилетиями стандарт интерфейса разработки. Разработчику или DevOps-инженеру не нужно изучать кастомные флаги десятков bash-скриптов (`./build.sh`, `./start.sh`, `./deploy-local.sh`). Стандартные цели `make build`, `make test`, `make up` работают одинаково во всех репозиториях компании, а встроенный механизм отслеживания зависимостей целей минимизирует повторные действия."
  },
  {
    "num": 69,
    "title": "Современная синхронизация: docker compose watch для мгновенного обновления кода",
    "task": "Используйте `docker compose watch` (новая фича Docker Compose v2.22+) для автоматической синхронизации кода и rebuild при изменениях.",
    "theory": "Начиная с версии Docker Compose v2.22+, появилась встроенная нативная функциональность **`docker compose watch`**.\n\nОна решает проблему классического bind mount:\n- Не требует установки сторонних утилит hot-reload внутри контейнера (таких как nodemon или air).\n- Позволяет настроить гранулярные правила для разных типов файлов:\n  1. `action: sync` — мгновенная синхронизация статических файлов, конфигураций и шаблонов прямо в работающий контейнер без перезапуска.\n  2. `action: rebuild` — автоматическая пересборка образа и замена контейнера при изменении манифестов зависимостей (`go.mod`, `go.sum`).\n  3. `action: sync+restart` — копирование обновленного файла и перезапуск процесса контейнера.",
    "step_by_step": "1. В `docker-compose.yml` добавьте секцию `develop.watch`.\n2. Настройте правила `sync` для шаблонов и `rebuild` для файлов `go.mod`.\n3. Запустите команду `docker compose watch`.\n4. Измените файл и убедитесь в автоматической фоновой синхронизации.",
    "code_blocks": [
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  web:\n    build: .\n    ports:\n      - \"8080:8080\"\n    # Секция декларации правил автоматического отслеживания изменений\n    develop:\n      watch:\n        # Синхронизация статики и шаблонов без перезапуска\n        - action: sync\n          path: ./static\n          target: /app/static\n\n        # Синхронизация кода и перезапуск контейнера\n        - action: sync+restart\n          path: ./cmd\n          target: /app/cmd\n\n        # Полная пересборка образа при обновлении модулей\n        - action: rebuild\n          path: ./go.mod",
        "note": "docker-compose.yml с секцией develop.watch"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск сервисов в режиме непрерывного отслеживания файлов\ndocker compose watch"
      }
    ],
    "under_the_hood": "CLI Docker Compose запускает локальный файловый watcher на хосте. При фиксации изменения файла Compose вызывает стриминговый tar-эндпоинт Docker Engine API (`PUT /containers/{id}/archive`), копируя измененный файл непосредственно в файловую систему запущенного контейнера на лету.",
    "pitfalls": "1. Требуется версия Docker Compose 2.22.0 или новее.\n2. Неверно указанные целевые пути `target`, приводящие к копированию файлов в неожиданные каталоги.",
    "bigtech_interview": "**Вопрос с собеседования:** «Чем `docker compose watch` лучше стандартного монтирования рабочей директории через `volumes: [\".:/app\"]`?»\n**Ответ:** Стандартный bind mount монтирует всю директорию целиком, включая локальные артефакты хоста (например, бинарники, несовместимые с Linux, локальные логи, мусорные файлы IDE), и может вызывать серьезные просадки дискового ввода-вывода (особенно на macOS). `docker compose watch` синхронизирует только указанные файлы в одну сторону, не блокирует диск постоянным двусторонним монтированием и поддерживает интеллектуальные триггеры (`rebuild` при изменении зависимостей)."
  },
  {
    "num": 70,
    "title": "Production конфигурация: docker-compose.prod.yml с жестким харденингом",
    "task": "Создайте отдельный `docker-compose.prod.yml` с production-настройками и используйте `docker compose -f docker-compose.yml -f docker-compose.prod.yml up` для продакшн-like тестирования.",
    "theory": "Для запуска сервисов на выделенных продакшн-серверах (например, standalone VM или периферийных edge-нодах) создается файл `docker-compose.prod.yml`.\n\nОн реализует максимальные требования промышленной надежности:\n1. `restart: always` — автоматический подъем сервиса при сбоях и перезагрузках ОС.\n2. `read_only: true` — защита от модификации файлов контейнера.\n3. `cap_drop: [ALL]` — отзыв всех привилегий ядра.\n4. `security_opt: [\"no-new-privileges:true\"]` — запрет эскалации прав.\n5. `logging` — ротация логов (не более 3 файлов по 10 МБ).\n6. `deploy.resources.limits` — жесткие квоты cgroups на CPU и память.",
    "step_by_step": "1. Создайте `docker-compose.prod.yml`.\n2. Проверьте слияние конфигурации: `docker compose -f docker-compose.yml -f docker-compose.prod.yml config`.\n3. Убедитесь в отсутствии проброшенных наружу портов БД и наличии лимитов ресурсов.",
    "code_blocks": [
      {
        "filename": "docker-compose.prod.yml",
        "lang": "yaml",
        "code": "services:\n  app:\n    image: myregistry.example.com/shop/app:v1.0.0\n    restart: always\n    read_only: true\n    security_opt:\n      - no-new-privileges:true\n    cap_drop:\n      - ALL\n    tmpfs:\n      - /tmp:rw,noexec,nosuid,size=32m\n    deploy:\n      resources:\n        limits:\n          cpus: '2.00'\n          memory: 512M\n        reservations:\n          cpus: '0.50'\n          memory: 128M\n    logging:\n      driver: \"json-file\"\n      options:\n        max-size: \"10m\"\n        max-file: \"3\"\n    environment:\n      - ENV=production\n      - LOG_LEVEL=warn",
        "note": "Эталонный docker-compose.prod.yml"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Валидация продакшн манифеста\ndocker compose -f docker-compose.prod.yml config --quiet && echo \"Configuration is 100% valid!\" "
      }
    ],
    "under_the_hood": "Спецификация Compose трансформируется в вызовы OCI runtime (runc), накладывая на процесс ограничения Linux namespaces, cgroups v2, seccomp и AppArmor/SELinux профили хостовой системы.",
    "pitfalls": "1. Использование тега `:latest` в продакшне вместо фиксированного семантического тега (например, `:v1.0.0`) или sha256 дайджеста.\n2. Отсутствие мониторинга метрик OOMKilled.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему использование тега `:latest` в продакшн манифестах Docker Compose и Kubernetes считается грубейшей ошибкой?»\n**Ответ:** Тег `:latest` является мутабельным указателем. Он не дает никакой гарантии, какой именно коммит и сборка кода запущены в данный момент. Это делает невозможным воспроизводимый откат (Rollback) на предыдущую версию, приводит к рассинхронизации версий между разными нодами кластера при рестарте подов и ломает аудит безопасности."
  },
  {
    "num": 71,
    "title": "Локальное окружение через Docker Compose: полный стек Go + PostgreSQL",
    "task": "**Локальное окружение через Docker Compose**: Напишите файл `docker-compose.yml`, объединяющий ваше Go-приложение, базу данных PostgreSQL и кэш Redis. Настройте параметры подключения через переменные окружения. Используйте директиву `depends_on` совместно с проверкой здоровья (`healthcheck`) для базы данных, чтобы Go-контейнер начинал запуск только после того, как PostgreSQL полностью готов принимать TCP-соединения.\n\n---",
    "theory": "Законченный стек для локальной разработки объединяет все разобранные лучшие практики:\n1. Автоматический DNS резолвинг между сервисами.\n2. Проверка здоровья (Health Check) базы данных.\n3. Отложенный запуск сервиса через `depends_on: { condition: service_healthy }`.\n4. Персистентность данных через Named Volume.\n5. Проброс только необходимых портов.",
    "step_by_step": "1. Опишите законченный `docker-compose.yml` со связкой Go + PostgreSQL.\n2. Запустите стек и убедитесь в надежном старте сервисов.",
    "code_blocks": [
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  app:\n    build: .\n    ports:\n      - \"8080:8080\"\n    environment:\n      - DATABASE_URL=postgres://appuser:appsecret@postgres:5432/appdb?sslmode=disable\n    depends_on:\n      postgres:\n        condition: service_healthy\n    restart: unless-stopped\n\n  postgres:\n    image: postgres:16-alpine\n    environment:\n      POSTGRES_USER: appuser\n      POSTGRES_PASSWORD: appsecret\n      POSTGRES_DB: appdb\n    volumes:\n      - postgres_dev_data:/var/lib/postgresql/data\n    healthcheck:\n      test: [\"CMD-SHELL\", \"pg_isready -U appuser -d appdb\"]\n      interval: 3s\n      timeout: 2s\n      retries: 5\n    ports:\n      - \"5432:5432\"\n    restart: unless-stopped\n\nvolumes:\n  postgres_dev_data:",
        "note": "Законченный локальный стек"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\tdbURL := os.Getenv(\"DATABASE_URL\")\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Local environment ready! Connected to: %s\\n\", dbURL)\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Go микросервис"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -o /app main.go\n\nFROM alpine:3.20\nCOPY --from=builder /app /app\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск всего стека одной командой\ndocker compose up -d\n\n# Проверка\ncurl http://localhost:8080/\n\n# Остановка с очисткой\ndocker compose down -v"
      }
    ],
    "under_the_hood": "Compose создает мостовую сеть и монтирует том `postgres_dev_data`. До момента, пока `pg_isready` не вернет 0, Compose не посылает команду создания контейнера `app` в Docker Engine.",
    "pitfalls": "1. Забытый healthcheck у СУБД.\n2. Конфликты локального порта 5432.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как быстро проверить здоровье запущенного в Docker Compose сервера PostgreSQL без входа внутрь контейнера?»\n**Ответ:** Командой `docker compose ps` (колонка STATUS покажет `healthy`), либо выполнив команду проверки через exec: `docker compose exec postgres pg_isready -U appuser -d appdb`. Код возврата 0 означает полную готовность базы к обработке запросов."
  },
  {
    "num": 72,
    "title": "CI аудит уязвимостей: сканирование через govulncheck и Trivy",
    "task": "Добавьте в CI этап проверки уязвимостей: `govulncheck` и сканирование Docker-образа (`trivy`).",
    "theory": "Комплексный аудит уязвимостей в CI/CD пайплайне состоит из двух взаимодополняющих уровней:\n\n1. **`govulncheck` (Анализ кода Go на уровне AST):**\n   Официальная утилита команды Go (`golang.org/x/vuln/cmd/govulncheck`).\n   В отличие от простых сканеров, govulncheck выполняет глубокий статический анализ графа вызовов (Call Graph). Если уязвимая функция сторонней библиотеки физически **не вызывается** вашим кодом, govulncheck не создает ложной тревоги!\n\n2. **`trivy` (Анализ Docker-образа и ОС):**\n   Проверяет готовый контейнер на наличие уязвимостей в системных библиотеках (libc, openssl, ca-certificates) и файлах конфигурации.\n\nОбъединение обоих инструментов в CI конвейере гарантирует 100% безопасность исходного кода и рантайма.",
    "step_by_step": "1. Установите `govulncheck`: `go install golang.org/x/vuln/cmd/govulncheck@latest`.\n2. Запустите анализ кода: `govulncheck ./...`.\n3. Соберите Docker-образ.\n4. Выполните сканирование контейнера через Trivy.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"Audited clean codebase!\")\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Микросервис"
      },
      {
        "filename": "ci-audit.sh",
        "lang": "bash",
        "code": "#!/bin/sh\nset -e\n\necho \"==> 1. Running govulncheck on Go source code...\"\ngo install golang.org/x/vuln/cmd/govulncheck@latest\ngovulncheck ./...\n\necho \"==> 2. Building Docker Image...\"\ndocker build -t app-audit-test:latest .\n\necho \"==> 3. Scanning Docker Image with Trivy...\"\ndocker run --rm -v /var/run/docker.sock:/var/run/docker.sock \\\n  aquasec/trivy:latest image --severity CRITICAL --exit-code 1 app-audit-test:latest\n\necho \"==> All security checks passed successfully!\" ",
        "note": "Скрипт проверки безопасности для CI пайплайна"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск проверки\nchmod +x ci-audit.sh\n./ci-audit.sh"
      }
    ],
    "under_the_hood": "`govulncheck` строит SSA (Static Single Assignment) представление Go-кода и ищет пути в графе потока управления от функций `main()` и `init()` к символам, зарегистрированным в базе Go Vulnerability Database (`vuln.go.dev`).",
    "pitfalls": "1. Использование устаревших версий Go, содержащих известные уязвимости в рантайме.\n2. Игнорирование предупреждений govulncheck о стандартной библиотеке.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему `govulncheck` дает значительно меньше ложных срабатываний (False Positives), чем стандартные сканеры зависимостей типа Snyk или Dependabot?»\n**Ответ:** Стандартные сканеры просто анализируют манифест `go.mod` и выдают предупреждение, если в проекте подключена библиотека уязвимой версии. Однако библиотека может содержать уязвимость в редкой вспомогательной функции, которую ваш сервис вообще не использует. `govulncheck` анализирует AST и граф вызовов бинарника и рапортует об уязвимости только в том случае, если уязвимый участок кода действительно вызывается в рантайме вашей программы."
  },
  {
    "num": 73,
    "title": "Использование Init Containers для выполнения миграций БД перед стартом",
    "task": "Используйте `Init Containers` для выполнения миграций БД перед запуском основного приложения.",
    "theory": "Архитектурный паттерн **Init Containers** обеспечивает соблюдение принципа разделения ответственности (Separation of Concerns).\n\nСхема исполнения:\n1. СУБД PostgreSQL инициализируется и сообщает о статусе `healthy`.\n2. Запускается эфемерный init-контейнер мигратора (`migrate/migrate`).\n3. Init-контейнер выполняет проверку версий схемы, накладывает DDL-миграции, фиксирует номер версии в таблице `schema_migrations` и завершает работу с кодом 0.\n4. Основное приложение стартует с гарантией, что все необходимые таблицы, колонки и индексы уже существуют в БД.\n\nЭто исключает падения сервиса из-за ошибок `relation \"users\" does not exist`.",
    "step_by_step": "1. Создайте SQL файлы миграций.\n2. Настройте сервис `init-migrations` в Docker Compose.\n3. Свяжите основной сервис с `init-migrations` через `condition: service_completed_successfully`.\n4. Запустите стек и проверьте логи.",
    "code_blocks": [
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  db:\n    image: postgres:16-alpine\n    environment:\n      POSTGRES_USER: dev\n      POSTGRES_PASSWORD: secret\n      POSTGRES_DB: main_db\n    healthcheck:\n      test: [\"CMD-SHELL\", \"pg_isready -U dev -d main_db\"]\n      interval: 2s\n      timeout: 2s\n      retries: 5\n\n  # Init Container\n  db-migrations:\n    image: migrate/migrate:v4.17.0\n    volumes:\n      - ./migrations:/migrations\n    entrypoint:\n      - \"migrate\"\n      - \"-path=/migrations\"\n      - \"-database=postgres://dev:secret@db:5432/main_db?sslmode=disable\"\n      - \"up\"\n    depends_on:\n      db:\n        condition: service_healthy\n\n  # Рабочий сервис\n  app:\n    image: alpine:3.20\n    command: [\"echo\", \"Database migrations completed successfully! Service is starting...\"]\n    depends_on:\n      db-migrations:\n        condition: service_completed_successfully",
        "note": "Паттерн Init Containers в Docker Compose"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск стека\ndocker compose up\n\n# Очистка\ndocker compose down -v"
      }
    ],
    "under_the_hood": "Compose отслеживает состояние процессов через Docker Socket. Завершение контейнера `db-migrations` с кодом 0 генерирует событие `container:die`, которое переводит триггер зависимости `service_completed_successfully` в активное состояние.",
    "pitfalls": "1. Отсутствие обработки ошибок: если миграция падает, весь деплой должен быть немедленно остановлен.\n2. Неидемпотентные миграции (отсутствие `IF NOT EXISTS`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как обеспечить Zero-Downtime миграцию базы данных при непрерывном деплое новой версии Go-сервиса?»\n**Ответ:** Применять паттерн Expand and Contract (Параллельное изменение). Миграции разбиваются на этапы: 1) Expand (Расширение): добавление новых колонок/таблиц без изменения старых (совместимо со старой и новой версиями сервиса). 2) Развертывание новой версии Go-приложения, пишущего в оба места. 3) Contract (Сужение): удаление старых колонок отдельной отложенной миграцией только после успешного переключения трафика."
  },
  {
    "num": 74,
    "title": "Иммутабельная инфраструктура (Immutable Infrastructure): запрет изменения running containers",
    "task": "**Immutable Infrastructure**: не меняй running containers. Собери новый image, deploy, старый — terminate. Rollback = deploy previous image. Никаких `kubectl exec` для hotfix'ов.",
    "theory": "Принцип **иммутабельной (неизменяемой) инфраструктуры** — фундаментальная основа Cloud Native разработки.\n\nКлючевое правило:\n**Никогда не модифицируйте работающие контейнеры в продакшне!**\nЗапрещены:\n- Подключение по SSH / `docker exec` для редактирования файлов или применения «быстрых хотфиксов».\n- Установка пакетов `apt-get install` или `apk add` в работающем контейнере.\n- Ручная правка конфигурационных файлов на диске контейнера.\n\nЛюбое изменение — это новый коммит в Git, новая автоматическая сборка неизменяемого Docker-образа с уникальным версионным тегом, прохождение тестов и развертывание нового контейнера с плавным выводом старого из эксплуатации (Rolling Update / Blue-Green Deployment).",
    "step_by_step": "1. Продемонстрируйте иммутабельность контейнера с флагом `--read-only`.\n2. Реализуйте выпуск патча через сборку нового образа с тегом `v1.0.1`.\n3. Выполните бесшовное переключение контейнеров.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nconst ReleaseVersion = \"v1.0.1\"\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Immutable release version: %s\\n\", ReleaseVersion)\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Новая версия сервиса"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -ldflags=\"-w -s\" -o /bin/app main.go\n\nFROM scratch\nCOPY --from=builder /bin/app /app\nENTRYPOINT [\"/app\"]",
        "note": "Иммутабельный Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# 1. Сборка нового неизменяемого образа v1.0.1\ndocker build -t app-service:v1.0.1 .\n\n# 2. Запуск нового контейнера\ndocker run -d -p 8081:8080 --name app-v101 --read-only app-service:v1.0.1\n\n# 3. Проверка ответа\ncurl http://localhost:8081/\n\n# 4. Удаление старого контейнера\ndocker rm -f app-v101"
      }
    ],
    "under_the_hood": "Иммутабельность предотвращает дрейф конфигурации (Configuration Drift). Каждый контейнер создается строго из детерминированного неизменяемого слоя OverlayFS, гарантируя 100% совпадение окружения на всех серверах кластера.",
    "pitfalls": "1. Мутации контейнеров в рантайме, приводящие к невозможности воспроизвести окружение при перезапуске ноды.\n2. Отсутствие контроля версий образов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему практика внесения изменений в работающий контейнер через `docker exec` считается недопустимой в HighLoad системах?»\n**Ответ:** 1) Дрейф конфигурации (Configuration Drift): изменения, внесенные вручную, не зафиксированы в коде репозитория и исчезнут при первом же перезапуске или автоскейлинге пода. 2) Нарушение аудита: невозможно отследить, кто, когда и какие изменения внес. 3) Невозможность масштабирования: вновь созданные реплики не будут содержать ручного фикса, что приведет к скрытым багам и падению надежности системы."
  },
  {
    "num": 75,
    "title": "Security by Default: эталонный защищенный контейнер в HighLoad продакшне",
    "task": "**Security by Default**: non-root containers, read-only root FS, minimal base images (distroless/scratch), no secrets in images, mTLS, network policies, RBAC, Pod Security Standards, Falco runtime detection.",
    "theory": "Финальный синтез всех практик контейнеризации в концепции **Security by Default** объединяет:\n1. **Минимальный базовый образ (`gcr.io/distroless/static-debian12:nonroot`).**\n2. **Непривилегированный пользователь (UID 65532).**\n3. **Файловая система только для чтения (`read_only: true`).**\n4. **Сброс всех привилегий ядра Linux (`cap_drop: [ALL]`).**\n5. **Запрет повышения прав (`no-new-privileges: true`).**\n6. **Монтирование оперативной памяти для временных файлов (`tmpfs: /tmp`).**\n7. **Встроенный Healthcheck без внешних утилит.**\n\nТакой контейнер неуязвим для подавляющего большинства векторов атак и готов к развертыванию в финансовых, банковских и высоконагруженных enterprise-системах с наивысшими требованиями регуляторов (PCI DSS, HIPAA, GDPR).",
    "step_by_step": "1. Напишите полноценный Go микросервис со встроенным healthcheck.\n2. Создайте эталонный защищенный `Dockerfile`.\n3. Опишите защищенный `docker-compose.yml`.\n4. Соберите и запустите контейнер, проверив все уровни безопасности.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n\t\"os/signal\"\n\t\"syscall\"\n\t\"time\"\n)\n\nfunc main() {\n\t// Режим проверки здоровья для Docker HEALTHCHECK\n\tif len(os.Args) > 1 && os.Args[1] == \"healthcheck\" {\n\t\tclient := http.Client{Timeout: 2 * time.Second}\n\t\tresp, err := client.Get(\"http://127.0.0.1:8080/healthz\")\n\t\tif err != nil || resp.StatusCode != http.StatusOK {\n\t\t\tos.Exit(1)\n\t\t}\n\t\tos.Exit(0)\n\t}\n\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\tw.Write([]byte(\"OK\"))\n\t})\n\n\tmux.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Enterprise HighLoad Service running under Security by Default standards!\\nUID: %d\\n\", os.Getuid())\n\t})\n\n\tserver := &http.Server{\n\t\tAddr:         \":8080\",\n\t\tHandler:      mux,\n\t\tReadTimeout:  5 * time.Second,\n\t\tWriteTimeout: 10 * time.Second,\n\t}\n\n\t// Graceful Shutdown перехват сигналов SIGTERM и SIGINT\n\tsigChan := make(chan os.Signal, 1)\n\tsignal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)\n\n\tgo func() {\n\t\tlog.Println(\"Server listening on :8080...\")\n\t\tif err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {\n\t\t\tlog.Fatalf(\"Server error: %v\", err)\n\t\t}\n\t}()\n\n\t<-sigChan\n\tlog.Println(\"Shutting down gracefully...\")\n\n\tctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\tdefer cancel()\n\n\tif err := server.Shutdown(ctx); err != nil {\n\t\tlog.Fatalf(\"Forced shutdown: %v\", err)\n\t}\n\tlog.Println(\"Server exited successfully.\")\n}",
        "note": "Production микросервис с самопроверкой и Graceful Shutdown"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# syntax=docker/dockerfile:1\n\n# Stage 1: Build\nFROM golang:1.24-alpine AS builder\n\nWORKDIR /src\n\nCOPY go.mod go.sum* ./\nRUN --mount=type=cache,target=/go/pkg/mod \\\n    go mod download\n\nCOPY . .\n\nRUN --mount=type=cache,target=/go/pkg/mod \\\n    --mount=type=cache,target=/root/.cache/go-build \\\n    CGO_ENABLED=0 GOOS=linux go build \\\n    -ldflags=\"-w -s\" \\\n    -o /bin/server .\n\n# Stage 2: Final Minimal & Hardened Distroless\nFROM gcr.io/distroless/static-debian12:nonroot\n\nWORKDIR /app\nCOPY --from=builder /bin/server /app/server\n\nUSER nonroot:nonroot\n\nEXPOSE 8080\n\nHEALTHCHECK --interval=10s --timeout=2s --start-period=2s --retries=3 \\\n  CMD [\"/app/server\", \"healthcheck\"]\n\nENTRYPOINT [\"/app/server\"]",
        "note": "Эталонный защищенный Dockerfile"
      },
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  production_service:\n    build: .\n    ports:\n      - \"8080:8080\"\n    restart: always\n    read_only: true\n    security_opt:\n      - no-new-privileges:true\n    cap_drop:\n      - ALL\n    tmpfs:\n      - /tmp:rw,noexec,nosuid,size=32m\n    deploy:\n      resources:\n        limits:\n          cpus: '1.5'\n          memory: 256M\n        reservations:\n          cpus: '0.2'\n          memory: 64M\n    logging:\n      driver: \"json-file\"\n      options:\n        max-size: \"10m\"\n        max-file: \"3\" ",
        "note": "Финальная промышленная конфигурация"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка и запуск эталонного защищенного сервиса\ndocker compose up -d\n\n# Проверка работоспособности\ncurl http://localhost:8080/\n\n# Проверка здоровья\ndocker inspect --format='{{json .State.Health.Status}}' $(docker compose ps -q production_service)\n\n# Очистка\ndocker compose down"
      }
    ],
    "under_the_hood": "Данный сервис реализует все требования безопасности OCI Runtime Specification. Рантайм изолирует процесс в пространствах имен `mnt`, `pid`, `net`, `ipc`, `uts`, монтирует rootfs в режиме `ro`, отключает все флаги `capabilities` в дескрипторе процесса и обеспечивает корректную маршрутизацию сигналов остановки `SIGTERM` благодаря тому, что Go-сервер является процессом PID 1.",
    "pitfalls": "1. Попытка записи временных данных мимо смонтированного tmpfs каталога `/tmp`.\n2. Забытый буферизированный канал сигналов `make(chan os.Signal, 1)`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Опишите чеклист из 7 ключевых пунктов для подготовки Go-микросервиса к безопасному промышленному развертыванию в Docker / Kubernetes.»\n**Ответ:** 1) Multi-stage сборка с финальным этапом на базе `FROM scratch` или `distroless` (минимальный вес и 0 CVE). 2) Статическая компиляция `CGO_ENABLED=0 -ldflags=\"-w -s\"`. 3) Запуск строго от непривилегированного пользователя (`USER nonroot` или `USER 10001`). 4) Монтирование корневой файловой системы в режиме только для чтения (`read_only: true`) с памятью `tmpfs` для `/tmp`. 5) Полный сброс привилегий ядра Linux (`cap_drop: [ALL]`) и запрет эскалации (`no-new-privileges: true`). 6) Жесткие ограничения cgroups на память и процессор (Memory limits, CPU quotas) с интеграцией `automaxprocs`. 7) Реализация корректного перехвата `SIGTERM` для Graceful Shutdown и самопроверки здоровья (Healthcheck)."
  }
]
