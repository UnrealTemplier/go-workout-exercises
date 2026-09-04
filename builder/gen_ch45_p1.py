# -*- coding: utf-8 -*-
exercises = [
  {
    "num": 1,
    "title": "Простой Dockerfile (Single-stage) и анализ избыточного веса образа",
    "task": "**Простой Dockerfile (Single-stage)**: Напишите базовый `Dockerfile` для вашего Go-приложения. Скопируйте туда весь исходный код, установите Go SDK внутри контейнера, выполните `RUN go build` и запустите бинарный файл. Соберите образ и посмотрите на его вес (он должен составить около 800 МБ–1 ГБ). Объясните в комментариях, почему не стоит тащить компилятор Go и исходный код в финальный продакшн-образ.",
    "theory": "Контейнеризация на базе Docker использует пространства имен (Linux namespaces: pid, net, ipc, mnt, uts, user) и контрольные группы (cgroups) для изолированного исполнения процессов на общем ядре хост-системы.\nКлассический одноэтапный `Dockerfile` (Single-stage build) выполняет компиляцию и исполнение внутри одного и того же образа.\n\nКогда для сборки используется официальный базовый образ `golang:1.22` или `golang:1.24` (на базе Debian Linux), итоговый контейнер наследует:\n1. Полный дистрибутив операционной системы (glibc, пакетный менеджер `apt`, утилиты bash, coreutils, curl, git, python и т.д.).\n2. Компилятор Go (`go`, `gofmt`, тулчейн компилятора, ассемблер, линковщик).\n3. Стандартную библиотеку в исходных кодах (`$GOROOT/src`) и промежуточный кэш модулей/пакетов (`$GOPATH/pkg`).\n4. Все исходные `.go` файлы проекта, историю репозитория и тестовые артефакты.\n\nВ результате минимальный сервис «Hello World» весит **от 800 МБ до 1.2 ГБ**. В продакшн-эксплуатации такой образ несет фатальные недостатки:\n- **Огромный Attack Surface (вектор атак):** наличие пакетных менеджеров, отладчиков (`gdb`) и компиляторов позволяет злоумышленнику при RCE (Remote Code Execution) скомпилировать и запустить любой эксплойт или бэкдор прямо в контейнере.\n- **Медленный деплой:** скачивание гигабайтных образов в Kubernetes-кластерах с сотнями нод приводит к сетевому троттлингу, задержкам холодного старта (Cold Start) и переполнению дискового пространства нод (DiskPressure).",
    "step_by_step": "1. Создайте минимальный Go HTTP-сервер в файле `main.go`.\n2. Создайте файл `Dockerfile` с одноэтапной сборкой от базового образа `golang:1.24`.\n3. Соберите Docker-образ командой `docker build -t app-single:v1 .`.\n4. Проверьте размер созданного образа через `docker images app-single:v1`.\n5. Запустите контейнер с пробросом портов: `docker run -d -p 8080:8080 --name single-test app-single:v1`.\n6. Выполните проверку работоспособности через `curl http://localhost:8080` и остановите контейнер.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\thostname, _ := os.Hostname()\n\t\tfmt.Fprintf(w, \"Hello from Single-stage Go Container! Host: %s\\n\", hostname)\n\t})\n\n\thttp.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\tw.Write([]byte(\"OK\"))\n\t})\n\n\tlog.Println(\"Server listening on :8080...\")\n\tif err := http.ListenAndServe(\":8080\", nil); err != nil {\n\t\tlog.Fatalf(\"Server error: %v\", err)\n\t}\n}",
        "note": "Минимальный HTTP-сервер для демонстрации сборки в контейнере"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# Базовый образ Debian с предустановленным Go 1.24\nFROM golang:1.24\n\n# Установка рабочей директории\nWORKDIR /app\n\n# Копирование исходного кода в образ\nCOPY . .\n\n# Скачивание зависимостей и компиляция бинарника\nRUN go mod init example.com/singleapp || true\nRUN go build -o /app/server main.go\n\n# Проброс сетевого порта\nEXPOSE 8080\n\n# Команда запуска процесса в контейнере\nCMD [\"/app/server\"]",
        "note": "Одноэтапный неоптимальный Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка образа\ndocker build -t app-single:v1 .\n\n# Проверка размера образа (видим ~800MB-1GB)\ndocker images app-single:v1 --format \"REPOSITORY: {{.Repository}} | TAG: {{.Tag}} | SIZE: {{.Size}}\"\n\n# Запуск контейнера\ndocker run -d -p 8080:8080 --name test-single app-single:v1\n\n# Тестовый запрос\ncurl -i http://localhost:8080/healthz\n\n# Очистка\ndocker rm -f test-single"
      }
    ],
    "under_the_hood": "С точки зрения файловой системы OverlayFS каждый шаг `RUN` и `COPY` создает отдельный неизменяемый слой (layer). В одноэтапном билде слой с дистрибутивом Go (`/usr/local/go`) фиксируется в нижних слоях (lowerdir). Даже если в конце выполнить `RUN rm -rf /usr/local/go`, размер итогового образа не уменьшится: удаленные файлы лишь помечаются специальными символами скрытия (whiteout files) в верхнем слое (upperdir), оставаясь физически упакованными во всех нижележащих tar-архивах слоев.",
    "pitfalls": "1. Оставление исходников и `.git` папки в продакшн-образе — утечка интеллектуальной собственности и секретов (API-ключи в истории коммитов).\n2. Огромное время pull/push образов в CI/CD пайплайнах.\n3. Уязвимости CVE в предустановленных системных библиотеках Linux, которые не нужны для работы Go-сервиса.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в продакшн запрещено отправлять single-stage Docker-образы для Go-сервисов, даже если они собраны на минимальном дистрибутиве?»\n**Ответ:** Go компилируется в самодостаточный машинный код. В runtime ему не требуются ни компилятор Go, ни заголовочные файлы, ни исходники. Single-stage образ тянет сотни мегабайт лишних файлов и утилит (sh, apt, curl), что катастрофически расширяет поверхность атаки (CVE) и замедляет холодный старт подов в Kubernetes при автомасштабировании."
  },
  {
    "num": 2,
    "title": "Базовый HTTP-сервер, сборка образа и проброс портов (Port Forwarding)",
    "task": "**Базовый Dockerfile**: Напиши простой HTTP-сервер на Go. Создай файл `Dockerfile`. Используй базовый образ `golang:1.22` (или новее). Скопируй исходники (`COPY . .`), скачай зависимости, скомпилируй бинарник внутри контейнера и укажи `CMD` для запуска. Собери образ (`docker build`) и запусти контейнер с пробросом портов (`docker run -p 8080:8080`).",
    "theory": "Сетевая модель Docker изолирует контейнер в собственном сетевом пространстве имен (`Network Namespace`). По умолчанию контейнер подключен к виртуальному мосту `bridge` (`docker0`) и получает приватный IP-адрес вида `172.17.0.x`.\n\nИнструкция `EXPOSE 8080` в `Dockerfile` носит исключительно **декларативный характер**: она документирует порт для других разработчиков и систем оркестрации, но физически не открывает сетевой порт на хосте.\nЧтобы входящий трафик с сетевого интерфейса хоста попал в процесс контейнера, используется проброс портов (`Port Mapping` / `Port Forwarding` флаг `-p <host_port>:<container_port>`).\n\nПри выполнении `docker run -p 8080:8080`:\n1. Демон Docker настраивает в ядре Linux цепочку правил `iptables` / `nftables` в таблице `nat` (цепочка `PREROUTING` и `DOCKER`).\n2. Входящие TCP-пакеты на порт 8080 хостового интерфейса транслируются (DNAT — Destination Network Address Translation) на приватный IP контейнера `172.17.0.2:8080`.\n3. Приложение внутри контейнера обязано слушать адрес `0.0.0.0:8080` (все интерфейсы), а не `127.0.0.1:8080`, иначе трафик с хоста будет отвергнут ядром.",
    "step_by_step": "1. Напишите HTTP-сервер на Go, который слушает `:8080` (эквивалентно `0.0.0.0:8080`).\n2. Опишите `Dockerfile` со сборкой бинарника и декларацией `EXPOSE 8080`.\n3. Соберите образ командой `docker build -t go-web-server:latest .`.\n4. Запустите контейнер: `docker run -d -p 8080:8080 --name web-instance go-web-server:latest`.\n5. Проверьте правила iptables или обратитесь через curl/браузер к `http://localhost:8080`.\n6. Остановите и удалите контейнер.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"log\"\n\t\"net/http\"\n\t\"time\"\n)\n\ntype StatusResponse struct {\n\tStatus    string    `json:\"status\"`\n\tTimestamp time.Time `json:\"timestamp\"`\n\tService   string    `json:\"service\"`\n}\n\nfunc main() {\n\tmux := http.NewServeMux()\n\n\tmux.HandleFunc(\"/api/v1/ping\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\tresp := StatusResponse{\n\t\t\tStatus:    \"pong\",\n\t\t\tTimestamp: time.Now().UTC(),\n\t\t\tService:   \"go-docker-demo\",\n\t\t}\n\t\t_ = json.NewEncoder(w).Encode(resp)\n\t})\n\n\tserver := &http.Server{\n\t\tAddr:         \":8080\", // Важно: слушать 0.0.0.0:8080 внутри контейнера\n\t\tHandler:      mux,\n\t\tReadTimeout:  5 * time.Second,\n\t\tWriteTimeout: 10 * time.Second,\n\t}\n\n\tlog.Println(\"Web server started on :8080\")\n\tif err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {\n\t\tlog.Fatalf(\"Server failed: %v\", err)\n\t}\n}",
        "note": "Production-ready HTTP-сервер с таймаутами и JSON API"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24\n\nWORKDIR /workspace\n\n# Копируем исходный код\nCOPY main.go .\n\n# Собираем оптимизированный бинарник\nRUN CGO_ENABLED=0 go build -ldflags=\"-w -s\" -o webapp main.go\n\n# Документируем порт контейнера\nEXPOSE 8080\n\n# Точка входа в формате exec (JSON-array)\nCMD [\"/workspace/webapp\"]",
        "note": "Dockerfile с компиляцией и EXPOSE"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t go-web-server:latest .\n\n# Запуск в фоновом режиме с привязкой порта 8080 хоста к 8080 контейнера\ndocker run -d -p 8080:8080 --name web-instance go-web-server:latest\n\n# Проверка ответа\ncurl -s http://localhost:8080/api/v1/ping\n\n# Проверка логов контейнера\ndocker logs web-instance\n\n# Остановка контейнера\ndocker rm -f web-instance"
      }
    ],
    "under_the_hood": "Служба `docker-proxy` (userspace proxy) или правила iptables ядра выполняют перенаправление TCP-сессий. Если Go-сервер слушает `127.0.0.1:8080`, он слушает loopback-интерфейс `lo` *внутри* контейнера. Пакеты, пришедшие от docker0 через виртуальный veth-интерфейс `eth0`, имеют адрес назначения `172.17.0.2`, поэтому ядро контейнера сбросит их с флагом RST (Connection Refused). Всегда указывайте `:8080` (`0.0.0.0:8080`).",
    "pitfalls": "1. Запуск сервера на `127.0.0.1:8080` внутри контейнера: запросы снаружи не будут доходить.\n2. Заблуждение, что `EXPOSE` автоматически пробрасывает порт во внешнюю сеть хоста без флага `-p` или `-P`.\n3. Использование `CMD /workspace/webapp` вместо exec-формы `CMD [\"/workspace/webapp\"]`: при запуске через shell процесс не получит сигналы `SIGTERM` для Graceful Shutdown.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем разница между `EXPOSE` в Dockerfile и флагом `-p` при запуске контейнера? Что произойдет, если указать `EXPOSE 8080`, но запустить `docker run -d myimage`?»\n**Ответ:** `EXPOSE` — это метаданные образа (документация), сообщающие, на каком порту приложение ожидает подключения. Без флага `-p` (или флага `-P`, который биндит все exposed-порты на случайные порты хоста) порт на хосте не открывается, и снаружи обратиться к контейнеру по IP хоста невозможно. Доступ к нему останется только у других контейнеров из той же Docker-сети по внутреннему IP."
  },
  {
    "num": 3,
    "title": "Многоэтапный билд (Multi-stage build) на базе Alpine Linux",
    "task": "Напиши **базовый Dockerfile** для Go-приложения: `FROM golang:1.24-alpine AS builder`, `WORKDIR /app`, `COPY go.mod go.sum .`, `RUN go mod download`, `COPY . .`, `RUN CGO_ENABLED=0 GOOS=linux go build -o main ./cmd/app`. Собери: `docker build -t myapp:v1 .`. Запусти: `docker run -p 8080:8080 myapp:v1`.",
    "theory": "Многоэтапная сборка (Multi-stage build), появившаяся в Docker 17.05+, позволяет использовать несколько директив `FROM` в одном файле `Dockerfile`.\n\nКаждая инструкция `FROM` начинает новый этап сборки (stage) с отдельным базовым образом. Предыдущие этапы могут быть поименованы директивой `AS <name>` (например, `FROM golang:1.24-alpine AS builder`).\nКлючевая возможность: селективное копирование артефактов из одного этапа в другой с помощью команды:\n`COPY --from=builder /source/path /destination/path`\n\nВ контексте Go:\n1. **Этап 1 (Builder):** используется образ `golang:1.24-alpine`. Здесь присутствуют все инструменты разработчика: компилятор Go, git для загрузки приватных модулей, заголовочные файлы.\n2. **Флаг `CGO_ENABLED=0`:** критически важен при кросс-компиляции под Alpine (musl libc) или scratch. Он отключает динамическую линковку с libc, формируя 100% автономный ELF-бинарник.\n3. **Этап 2 (Runtime):** используется минимальный образ `alpine:latest` (~5 МБ). В него копируется *только* бинарный файл приложения.\n\nРезультат: размер продакшн-образа снижается с **800+ МБ до 15–20 МБ**!",
    "step_by_step": "1. Создайте структуру проекта: директория `cmd/app/main.go` и `go.mod`.\n2. Напишите `Dockerfile` с этапами `AS builder` и финальным `FROM alpine:3.20`.\n3. Убедитесь в наличии флага `CGO_ENABLED=0 GOOS=linux`.\n4. Соберите образ: `docker build -t myapp:v1 .`.\n5. Запустите: `docker run -d -p 8080:8080 myapp:v1`.\n6. Проверьте размер через `docker images myapp:v1`.",
    "code_blocks": [
      {
        "filename": "cmd/app/main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Hello from Multi-stage Alpine Container!\\n\")\n\t})\n\n\tlog.Println(\"Starting service on port :8080...\")\n\tif err := http.ListenAndServe(\":8080\", nil); err != nil {\n\t\tlog.Fatalf(\"Fatal error: %v\", err)\n\t}\n}",
        "note": "Точка входа Go-приложения"
      },
      {
        "filename": "go.mod",
        "lang": "go",
        "code": "module example.com/multistage\n\ngo 1.24\n",
        "note": "Файл описания модуля Go"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# Stage 1: Сборка бинарника\nFROM golang:1.24-alpine AS builder\n\nWORKDIR /app\n\n# Кэширование загрузки модулей\nCOPY go.mod go.sum* ./\nRUN go mod download\n\n# Копирование исходного кода\nCOPY . .\n\n# Компиляция чистого статического бинарника без CGO\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o main ./cmd/app\n\n# Stage 2: Минимальный рантайм на Alpine\nFROM alpine:3.20\n\nWORKDIR /app\n\n# Копирование только скомпилированного бинарника из builder stage\nCOPY --from=builder /app/main /app/main\n\nEXPOSE 8080\n\nENTRYPOINT [\"/app/main\"]",
        "note": "Многоэтапный Dockerfile со сборкой в Alpine"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка образа myapp:v1\ndocker build -t myapp:v1 .\n\n# Сравнение размера\ndocker images myapp:v1\n\n# Запуск контейнера\ndocker run -d -p 8080:8080 --name app-v1 myapp:v1\n\n# Проверка\ncurl http://localhost:8080\n\n# Удаление\ndocker rm -f app-v1"
      }
    ],
    "under_the_hood": "Сборщик Docker (BuildKit) строит направленный ациклический граф (DAG) этапов сборки. Все слои этапа `builder`, которые не были скопированы через `COPY --from=builder`, полностью отбрасываются из финального тарбола образа. Финальный образ состоит только из базовых слоев `alpine` и единственного слоя, добавляющего бинарник `/app/main`.",
    "pitfalls": "1. Забытый `CGO_ENABLED=0`: если компилировать в Debian-образе с glibc, а запускать в Alpine (musl), приложение упадет с ошибкой `standard_init_linux.go: exec user process caused \"no such file or directory\"`.\n2. Копирование лишних файлов из builder stage (например, `COPY --from=builder /app .`), что снова загрязняет runtime.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему ошибка при запуске Go бинарника в Alpine контейнере часто выглядит как `no such file or directory`, хотя файл точно скопирован и имеет права 0755?»\n**Ответ:** Это происходит, когда бинарник собран с включенным CGO на системе с GNU libc (`/lib/ld-linux-x86-64.so.2`). В Alpine Linux используется другая реализация стандартной библиотеки C — musl libc (`/lib/ld-musl-x86_64.so.1`). Ядро Linux пытается найти динамический загрузчик (ELF interpreter) для бинарника, не находит его и возвращает ошибку `ENOENT` (No such file or directory). Решение: собирать с `CGO_ENABLED=0`."
  },
  {
    "num": 4,
    "title": "Сравнение метрик: Single-stage образ против Multi-stage и аудит размера",
    "task": "Напиши простейший `Dockerfile` для Go-приложения (один этап `FROM golang:1.22`, `go build`, `CMD`). Запусти через `docker run`. Обрати внимание на размер образа (он будет огромным, ~800MB).",
    "theory": "Размер Docker-образа напрямую влияет на жизненный цикл приложения в продакшне:\n1. **Network I/O & Registry Bandwidth:** При раскатке нового релиза на 50 нод Kubernetes передача 800 МБ потребует 40 ГБ сетевого трафика. Для 15 МБ образа — всего 750 МБ (разница более чем в 50 раз!).\n2. **Утилизация диска нод (Disk I/O & Storage):** Контейнерный рантайм (containerd / CRI-O) хранит слои образов в `/var/lib/containerd`. Тяжелые образы быстрее приводят к срабатыванию Garbage Collection образов кублета и eviction подов.\n3. **Безопасность (Vulnerabilities):** Одноэтапный образ `golang:1.22` тянет за собой около 100-200 известных уязвимостей (CVE) в пакетах Debian (systemd, openssl, tar, bash, coreutils). Минимальный образ содержит от 0 до 2 CVE.\n\nКоманда `docker history <image>` позволяет послойно проанализировать вклад каждой директивы в суммарный объем образа.",
    "step_by_step": "1. Создайте файл `Dockerfile.heavy` для одноэтапной сборки.\n2. Создайте файл `Dockerfile.light` для multi-stage сборки.\n3. Соберите оба образа: `myapp:heavy` и `myapp:light`.\n4. Сравните их размер через `docker images | grep myapp`.\n5. Выполните детальный послойный аудит через `docker history myapp:heavy` и `docker history myapp:light`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/ping\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"pong\")\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Минимальный микросервис"
      },
      {
        "filename": "Dockerfile.heavy",
        "lang": "dockerfile",
        "code": "FROM golang:1.24\nWORKDIR /src\nCOPY main.go .\nRUN go build -o /bin/app main.go\nCMD [\"/bin/app\"]",
        "note": "Одноэтапный тяжелый Dockerfile (~850 MB)"
      },
      {
        "filename": "Dockerfile.light",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS build\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -ldflags=\"-w -s\" -o /bin/app main.go\n\nFROM alpine:3.20\nCOPY --from=build /bin/app /bin/app\nCMD [\"/bin/app\"]",
        "note": "Multi-stage легкий Dockerfile (~15 MB)"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка тяжелого образа\ndocker build -f Dockerfile.heavy -t myapp:heavy .\n\n# Сборка легкого образа\ndocker build -f Dockerfile.light -t myapp:light .\n\n# Сравнение размеров\ndocker images myapp:heavy myapp:light --format \"table {{.Repository}}:{{.Tag}}\\t{{.Size}}\"\n\n# Послойный аудит\ndocker history myapp:heavy\ndocker history myapp:light"
      }
    ],
    "under_the_hood": "В `docker history` видно, что базовый слой `golang:1.24` добавляет свыше 700 МБ еще до выполнения каких-либо команд пользователя. Команда `go build` внутри контейнера также генерирует промежуточный кэш компилятора в `$HOME/.cache/go-build`, который в single-stage сборке навсегда остается зафиксированным в слое `RUN`.",
    "pitfalls": "1. Попытка очистить кэш в отдельном `RUN`: `RUN rm -rf /root/.cache` после `RUN go build` создает новый слой с whiteout-записями, не освобождая место в предыдущем слое.\n2. Неиспользование флагов линковщика `-ldflags=\"-w -s\"`, что оставляет в бинарнике отладочную DWARF-информацию (увеличивает размер бинарника на 25-40%).",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы практические последствия использования тяжелых Docker-образов в HighLoad кластере Kubernetes на 500 нод?»\n**Ответ:** 1) Высокая нагрузка на сеть и локальный Registry (Saturation). 2) Длинный Time-To-Ready при Horizontal Pod Autoscaler (HPA), когда поды не успевают подняться во время всплеска трафика (Spike). 3) Быстрое заполнение дисков нод (`DiskPressure`), приводящее к аварийному выселению (Eviction) других критических подов."
  },
  {
    "num": 5,
    "title": "Многоэтапная сборка с переходом на scratch / alpine",
    "task": "Напишите `Dockerfile` для Go-приложения с multi-stage сборкой: первый stage собирает бинарник, второй — минимальный образ на `scratch` или `alpine`.",
    "theory": "Образ `scratch` — это специальный псевдо-базовый образ Docker, который имеет **нулевой размер** (`0 bytes`).\nДиректива `FROM scratch` сообщает Docker, что следующий этап сборки не наследует никакую операционную систему, пакеты или файловую иерархию.\n\nПри сборке в `scratch`:\n- В образе нет ничего: ни `/bin/sh`, ни `/bin/ls`, ни менеджеров пакетов, ни стандартных C-библиотек.\n- Исполняемый файл приложения является единственным файлом в контейнере.\n- Итоговый размер образа равен точно размеру скомпилированного Go-бинарника (обычно 8–15 МБ).\n\nДля успешной работы в `scratch` бинарник обязан быть статически слинкован (`CGO_ENABLED=0`).\nЕсли сервису требуется утилита для отладки или `sh` для выполнения команд health check в Kubernetes/Docker, вместо `scratch` выбирают `alpine` (~5 МБ).",
    "step_by_step": "1. Напишите HTTP-сервер на Go.\n2. Создайте `Dockerfile` с этапом сборки `AS builder` на `golang:1.24-alpine`.\n3. Укажите компиляцию со статическим связыванием `CGO_ENABLED=0`.\n4. Во втором этапе укажите `FROM scratch`.\n5. Скопируйте скомпилированный бинарник через `COPY --from=builder /app/service /service`.\n6. Укажите точку входа `ENTRYPOINT [\"/service\"]` и соберите образ.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Running on pure scratch image!\\n\")\n\t})\n\n\tlog.Println(\"Server running on port 8080...\")\n\tif err := http.ListenAndServe(\":8080\", nil); err != nil {\n\t\tlog.Fatalf(\"Server error: %v\", err)\n\t}\n}",
        "note": "Минималистичный сервис для запуска в scratch"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# Этап 1: Сборка\nFROM golang:1.24-alpine AS builder\n\nWORKDIR /build\n\nCOPY main.go .\n\n# Собираем статический бинарник без CGO с удалением DWARF и таблицы символов\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o service main.go\n\n# Этап 2: Пустой образ scratch\nFROM scratch\n\n# Копируем бинарник из первого этапа\nCOPY --from=builder /build/service /service\n\n# Порт\nEXPOSE 8080\n\n# Запуск напрямую\nENTRYPOINT [\"/service\"]",
        "note": "Dockerfile с целевым образом scratch"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка образа\ndocker build -t app-scratch:latest .\n\n# Проверка размера (размер будет около 6-10 MB!)\ndocker images app-scratch:latest\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-scratch app-scratch:latest\n\n# Проверка ответа\ncurl http://localhost:8080\n\n# Очистка\ndocker rm -f test-scratch"
      }
    ],
    "under_the_hood": "Когда ядро Linux стартует контейнер на базе `scratch`, оно создает корневой каталог (`rootfs`) из единственного слоя, где лежит только `/service`. Процесс стартует напрямую через системный вызов `execve(\"/service\", ...)`. Никаких оболочек bash/sh не вызывается, что дает мгновенный старт контейнера (миллисекунды).",
    "pitfalls": "1. Использование shell-формы `CMD /service`: в scratch нет `/bin/sh`, поэтому контейнер немедленно упадет с ошибкой `exec: \"/bin/sh\": stat /bin/sh: no such file or directory`. Обязательно используйте exec-форму `ENTRYPOINT [\"/service\"]`.\n2. Попытка выполнить `docker exec -it <container> sh` для отладки: в scratch нет командной строки.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в образе `FROM scratch` невозможно запустить скрипт или команду вида `CMD /app`?»\n**Ответ:** Запись `CMD /app` интерпретируется Docker как вызов через шелл: `/bin/sh -c \"/app\"`. В образе `scratch` нет ни одного системного файла и отсутствует `/bin/sh`. Docker вернет ошибку отсутствия файла `/bin/sh`. Запуск возможен только через exec-синтаксис JSON-массива: `ENTRYPOINT [\"/app\"]`."
  },
  {
    "num": 6,
    "title": "Оптимизация размера: builder против Distroless и радикальное сжатие",
    "task": "Оптимизируй Dockerfile через **multi-stage build**: stage 1 — builder (`golang:1.24-alpine`), stage 2 — `FROM scratch` или `gcr.io/distroless/static`. Копируй только бинарник: `COPY --from=builder /app/main /main`. `ENTRYPOINT [\"/main\"]`. Сравни размер: 300MB → 5MB.",
    "theory": "**Distroless** — это семейство контейнерных образов, разработанных компанией Google (`gcr.io/distroless/static-debian12`).\nОни содержат только само приложение и минимально необходимые системные зависимости:\n- Корневые доверенные сертификаты SSL/TLS (`ca-certificates.crt`).\n- Базу временных зон (`/usr/share/zoneinfo`).\n- Минимальный файл `/etc/passwd` с непривилегированным пользователем `nonroot` (UID 65532).\n\nПри этом в Distroless полностью **отсутствуют shell (`/bin/sh`, `/bin/bash`), пакетные менеджеры (`apt`, `apk`) и системные утилиты**.\nСравнение:\n- `golang:1.24` (single-stage): ~850 МБ.\n- `alpine`: ~15–20 МБ.\n- `gcr.io/distroless/static-debian12`: ~8–12 МБ (бинарник + сертификаты).\n\nDistroless считается отраслевым стандартом корпоративной безопасности в Google, RedHat и Cloud Native Security.",
    "step_by_step": "1. Создайте Go-приложение.\n2. Опишите `Dockerfile` с этапом `AS builder` на `golang:1.24-alpine`.\n3. В качестве runtime используйте `gcr.io/distroless/static-debian12`.\n4. Соберите образ и сравните его вес с исходным single-stage.\n5. Продемонстрируйте невозможность взлома через shell: `docker exec -it <container> sh` вернет отказ.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Server time: %s\\n\", time.Now().UTC().Format(time.RFC3339))\n\t})\n\n\tlog.Println(\"Listening on :8080...\")\n\tif err := http.ListenAndServe(\":8080\", nil); err != nil {\n\t\tlog.Fatal(err)\n\t}\n}",
        "note": "Сервис с использованием времени UTC"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# Stage 1: Builder\nFROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /bin/server main.go\n\n# Stage 2: Distroless Static\nFROM gcr.io/distroless/static-debian12:nonroot\nWORKDIR /app\nCOPY --from=builder /bin/server /app/server\n\nEXPOSE 8080\nENTRYPOINT [\"/app/server\"]",
        "note": "Dockerfile с базовым образом Google Distroless"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t app-distroless:latest .\n\n# Проверка размера (около 8 MB)\ndocker images app-distroless:latest\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-distro app-distroless:latest\n\n# Попытка подключиться shell (завершится ошибкой exec: no such file or directory)\ndocker exec -it test-distro sh || echo \"Security confirmed: No shell available!\"\n\n# Очистка\ndocker rm -f test-distro"
      }
    ],
    "under_the_hood": "Google Distroless собирается с помощью Bazel из минимального среза пакетов Debian. В образе присутствует только `/etc/ssl/certs/ca-certificates.crt` и `/etc/passwd` с пользователем `nonroot:nonroot` (UID:GID 65532). Рантайм `runc` запускает процесс в пространстве имен пользователя без root-прав, блокируя вектор атак с повышением привилегий.",
    "pitfalls": "1. Попытка запустить интерактивный шелл для дебага в продакшне — требуется использовать `ephemeral debug containers` в Kubernetes (`kubectl debug`).\n2. Забытый тег `:nonroot`: по умолчанию без суффикса Distroless запускается под root.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Enterprise-инфраструктуре часто предпочитают Google Distroless образу Alpine Linux, хотя разница в размере составляет всего 5–10 МБ?»\n**Ответ:** В Alpine присутствует BusyBox (`/bin/sh`, утилиты сетевого стека) и пакетный менеджер `apk`. В случае RCE-уязвимости в Go-приложении злоумышленник может открыть reverse shell, скачать сторонние бинарники через `wget` или установить эксплойты. В Distroless нет оболочки и утилит: выполнить произвольные команды операционной системы невозможно."
  },
  {
    "num": 7,
    "title": "Разделение на builder и runtime окружение: детальный аудит",
    "task": "**Multi-stage build**: Разделите Dockerfile на `builder` stage (с полным Go) и `runtime` stage (с минимальным базовым образом). Сравните размеры.",
    "theory": "Разделение на `builder` и `runtime` реализует фундаментальный принцип безопасности и надежности: **минимизация привилегий и зависимостей (Least Privilege & Minimal Dependencies)**.\n\nНа этапе сборки (`builder`):\n- Требуются: компилятор Go, Git, SSH-ключи (для загрузки модулей из приватных репозиториев GitLab/GitHub), исходные коды, линтеры и тесты.\n- Окружение работает временно и изолированно на билд-агенте CI/CD.\n\nНа этапе исполнения (`runtime`):\n- Требуются: один единственный бинарный артефакт, конфигурационные файлы по умолчанию и корневые сертификаты TLS.\n- Недопустимо наличие секретов сборки, приватных ключей, исходников или инструментов отладки.\n\nБлагодаря этому архитектурному паттерну обеспечивается изоляция процесса разработки от эксплуатации.",
    "step_by_step": "1. Подготовьте проект с зависимостями.\n2. Сформируйте `Dockerfile`, четко разграничивающий этап сборки и этап рантайма.\n3. Соберите образ и убедитесь, что в итоговом образе отсутствуют файлы `main.go`, `go.mod` и тулчейн Go.\n4. Проверьте содержимое файловой системы запущенного контейнера.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/info\", func(w http.ResponseWriter, r *http.Request) {\n\t\t// Проверяем наличие компилятора go в runtime\n\t\t_, err := os.Stat(\"/usr/local/go/bin/go\")\n\t\thasGo := err == nil\n\n\t\tfmt.Fprintf(w, \"Runtime isolation check. Go compiler present: %v\\n\", hasGo)\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Код для проверки отсутствия компилятора в рантайме"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# === Stage 1: Build Environment ===\nFROM golang:1.24-alpine AS builder\nWORKDIR /workspace\nCOPY main.go .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /workspace/app main.go\n\n# === Stage 2: Runtime Environment ===\nFROM alpine:3.20 AS runtime\nWORKDIR /app\nCOPY --from=builder /workspace/app /app/app\nEXPOSE 8080\nENTRYPOINT [\"/app/app\"]",
        "note": "Разделение builder и runtime"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t app-isolated:latest .\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-iso app-isolated:latest\n\n# Проверка: Go compiler present: false\ncurl http://localhost:8080/info\n\n# Проверка файлов в контейнере (нет исходников!)\ndocker exec test-iso ls -la /app\n\n# Очистка\ndocker rm -f test-iso"
      }
    ],
    "under_the_hood": "В Docker v2 (BuildKit) промежуточные стадии сборки кешируются отдельно. Если в коде поменялся только `main.go`, этап установки базовых пакетов в builder не пересчитывается. На шаге экспорта в OCI image tarball упаковщик сериализует только дельту последнего этапа `runtime`.",
    "pitfalls": "1. Случайное использование одного и того же тега базового образа для обоих этапов без очистки рабочей директории.\n2. Использование директивы `ADD` вместо `COPY`, что может непреднамеренно распаковывать локальные архивы tar в рантайм.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каким образом использование Multi-stage build предотвращает утечку приватных SSH-ключей и токенов доступа при сборке Go-модулей из закрытых репозиториев?»\n**Ответ:** При передаче SSH-ключа или токена на этапе `builder` (например, через `--mount=type=secret` или `ARG`), эти данные используются только на первом этапе для `go mod download`. Финальный этап `runtime` стартует с чистого базового образа, куда копируется только скомпилированный бинарник. Секреты и промежуточные слои builder'а не попадают в граф слоев финального продакшн-образа."
  },
  {
    "num": 8,
    "title": "Безопасность: запуск от непривилегированного пользователя (Non-root user)",
    "task": "Добавь **non-root user**: `RUN adduser -D -u 1000 appuser`, `USER appuser`. Покажи, что root в контейнере — security risk (container escape). Проверь `whoami` внутри контейнера.",
    "theory": "По умолчанию все процессы внутри контейнера Docker исполняются от имени суперпользователя `root` (UID 0).\n\nХотя пространства имен изолируют контейнер, **UID 0 внутри контейнера по умолчанию соответствует UID 0 (root) на хост-машине**!\nЕсли злоумышленник сможет эксплуатировать уязвимость побега из контейнера (Container Escape, например CVE в runc, ядре Linux или ошибочно смонтированный Docker socket `/var/run/docker.sock`), он мгновенно получит полный root-доступ ко всей операционной системе хоста.\n\nСтандарты безопасности CIS Docker Benchmark, PCI DSS и политики безопасности Kubernetes (Pod Security Standards — Restricted) требуют:\n1. Создания выделенного системного пользователя и группы с фиксированным идентификатором (например, UID/GID 10001 или 1000).\n2. Явного указания директивы `USER appuser:appgroup` в `Dockerfile`.\n3. Запрета запуска процессов от UID 0.",
    "step_by_step": "1. В этапе `builder` создайте пользователя `appuser` (UID 10001) в файле `/etc/passwd`.\n2. Скопируйте `/etc/passwd` и `/etc/group` в финальный образ.\n3. Назначьте права на рабочую директорию.\n4. Активируйте пользователя директивой `USER 10001:10001`.\n5. Соберите образ и проверьте команду `id` и `whoami` внутри контейнера.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/whoami\", func(w http.ResponseWriter, r *http.Request) {\n\t\tuid := os.Getuid()\n\t\tgid := os.Getgid()\n\t\tfmt.Fprintf(w, \"Current Process UID: %d, GID: %d\\n\", uid, gid)\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис, сообщающий свой реальный UID и GID"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\n\nWORKDIR /app\nCOPY main.go .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o server main.go\n\n# Создаем непривилегированного пользователя appuser (UID 10001)\nRUN adduser -D -u 10001 -s /bin/sh appuser\n\nFROM alpine:3.20\n\n# Копируем запись пользователя из builder stage\nCOPY --from=builder /etc/passwd /etc/passwd\nCOPY --from=builder /etc/group /etc/group\nCOPY --from=builder /app/server /app/server\n\n# Назначаем владельца\nUSER 10001:10001\n\nEXPOSE 8080\nENTRYPOINT [\"/app/server\"]",
        "note": "Dockerfile с запуском от non-root пользователя 10001"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t app-nonroot:v1 .\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-nonroot app-nonroot:v1\n\n# Проверка UID процесса через HTTP-эндпоинт (вернет UID: 10001)\ncurl http://localhost:8080/whoami\n\n# Проверка через docker exec\ndocker exec test-nonroot id\n\n# Очистка\ndocker rm -f test-nonroot"
      }
    ],
    "under_the_hood": "Директива `USER` меняет атрибуты учетных данных процесса в системном вызове `setuid(10001)` и `setgid(10001)` перед вызовом `execve`. Процесс теряет все capability суперпользователя (в частности `CAP_SYS_ADMIN`, `CAP_NET_ADMIN`, `CAP_DAC_OVERRIDE`), что делает невозможным изменение системных файлов ядра или доступ к чужим файлам хоста.",
    "pitfalls": "1. Попытка биндить привилегированные порты (<1024, например `:80` или `:443`) под non-root пользователем в старых ядрах Linux без `CAP_NET_BIND_SERVICE`. Всегда используйте порты выше 1024 (например, `:8080`).\n2. Назначение прав на запись: если бинарнику нужно писать логи на диск, директория должна принадлежать UID 10001 (`chown -R 10001:10001 /var/log/app`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему строгие политики Kubernetes (PodSecurityPolicy / Pod Security Admission уровня Restricted) блокируют запуск подов с `runAsUser: 0`?»\n**Ответ:** Запуск под root (UID 0) является грубым нарушением эшелонированной обороны (Defense in Depth). В случае уязвимости в приложении или рантайме контейнеров скомпрометированный процесс имеет права суперпользователя и может попытаться осуществить побег из контейнера через уязвимости ядра, модифицировать cgroups или получить доступ к смонтированным чувствительным томам узла."
  },
  {
    "num": 9,
    "title": "Использование golang:alpine вместо golang:latest в builder stage",
    "task": "Используйте `golang:1.22-alpine` вместо `golang:1.22` для builder stage — это уменьшит размер и ускорит сборку.",
    "theory": "Выбор базового образа для этапа `builder` оказывает колоссальное влияние на производительность сборочных конвейеров (CI/CD pipelines).\n\nСравнение базовых builder-образов:\n1. `golang:1.24` (на базе Debian):\n   - Размер: **~850 МБ**.\n   - Пакетный менеджер: `apt` (медленный, требует `apt-get update`).\n   - Используется, когда приложению необходим CGO с GNU libc или сложные системные библиотеки сборки.\n2. `golang:1.24-alpine`:\n   - Размер: **~250 МБ** (в 3.5 раза меньше!).\n   - Пакетный менеджер: `apk` (молниеносная установка пакетов).\n   - Идеален для сборки чистых Go-приложений (`CGO_ENABLED=0`).\n\nВ CI-агентах (GitLab Runner, GitHub Actions) скачивание `golang:alpine` занимает 2–4 секунды вместо 25–40 секунд для полного Debian-образа, что суммарно экономит часы времени команды при десятках сборок в день.",
    "step_by_step": "1. Создайте файл `Dockerfile` с этапом `FROM golang:1.24-alpine AS builder`.\n2. При необходимости установите утилиты сборки через `apk add --no-cache git ca-certificates tzdata`.\n3. Соберите приложение с флагом `CGO_ENABLED=0`.\n4. Сравните скорость pull базового образа и итоговую легковесность сборочного пайплайна.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Built with golang:alpine builder!\\n\")\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Тестовый HTTP сервис"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# Быстрый и легковесный builder на базе Alpine Linux (~250MB)\nFROM golang:1.24-alpine AS builder\n\n# Установка git и корневых сертификатов без сохранения кэша apk\nRUN apk add --no-cache git ca-certificates tzdata\n\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /bin/app main.go\n\n# Финальный runtime\nFROM alpine:3.20\nCOPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo\nCOPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/\nCOPY --from=builder /bin/app /bin/app\n\nEXPOSE 8080\nENTRYPOINT [\"/bin/app\"]",
        "note": "Dockerfile с оптимальным builder'ом на Alpine"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t app-alpine-builder:latest .\n\n# Сравнение базовых образов в локальном кэше\ndocker images \"golang:*\"\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-alp app-alpine-builder:latest\ncurl http://localhost:8080\ndocker rm -f test-alp"
      }
    ],
    "under_the_hood": "Дистрибутив Alpine построен на базе `musl libc` и `busybox`. Он не содержит тяжелых библиотек локализации (`glibc-locale`), документации (`man-pages`) и громоздких утилит. Установка пакетов через `apk --no-cache` не создает временных индексных файлов на диске, уменьшая нагрузку на дисковый ввод-вывод.",
    "pitfalls": "1. Забытый флаг `--no-cache` в `apk add`: индекс пакетов `/var/cache/apk/*` остается в слое builder'а.\n2. Попытка сборки CGO-кода, завязанного на специфические расширения GNU glibc, без предварительной проверки совместимости с musl.",
    "bigtech_interview": "**Вопрос с собеседования:** «В каких случаях нельзя использовать `golang:alpine` для сборки Go-приложений и приходится оставаться на стандартном образе `golang:debian`?»\n**Ответ:** Когда проекту необходим CGO с динамической линковкой под хостовые системы на базе glibc (например, проприетарные драйверы Oracle, специфические криптобиблиотеки, биндинги C++ библиотек с libstdc++, или плагины `go plugin`, требующие строго совпадающих версий компилятора и glibc)."
  },
  {
    "num": 10,
    "title": "Кэширование слоев: порядок инструкций go.mod/go.sum против COPY . .",
    "task": "**Кэширование слоев (Секрет скорости)**: Измени упр. 576. Сначала скопируй **только** `go.mod` и `go.sum`. Затем выполни `RUN go mod download`. И только после этого делай `COPY . .` и `go build`. Попробуй изменить одну строчку в `main.go` и пересобрать образ. Убедись, что скачивание библиотек берется из кэша Docker, экономя уйму времени!",
    "theory": "Docker выполняет сборку послойно сверху вниз. Для каждой директивы он вычисляет контрольную сумму (хэш) входных данных:\n- Для команд `COPY` и `ADD` хэш зависит от контрольной суммы копируемых файлов.\n- Для команд `RUN` хэш зависит от текста самой команды.\n\nЕсли для некоторого шага хэш не изменился, Docker берет готовый промежуточный слой из локального кэша (`CACHED`).\nОднако **при инвалидации кэша на любом шаге ВСЕ последующие шаги обязаны выполняться заново**!\n\nАнтипаттерн:\n```dockerfile\nCOPY . .\nRUN go mod download\nRUN go build ...\n```\nПри малейшем изменении одной строчки в любом `.go` файле шаг `COPY . .` инвалидирует кэш. В результате команда `RUN go mod download` скачивает все десятки сторонних библиотек из интернета заново на каждой сборке!\n\nЗолотой стандарт кэширования:\n```dockerfile\nCOPY go.mod go.sum ./\nRUN go mod download\nCOPY . .\nRUN go build ...\n```\nТеперь `go mod download` выполняется из кэша за 0.1 секунды, пока не изменятся файлы `go.mod` или `go.sum`.",
    "step_by_step": "1. Создайте модуль Go с внешними зависимостями (например, `github.com/google/uuid`).\n2. Опишите правильный порядок инструкций в `Dockerfile`.\n3. Соберите образ первый раз: обратите внимание на загрузку модулей.\n4. Измените строку лога в `main.go` и пересоберите образ.\n5. Убедитесь в выводе терминала: шаг `RUN go mod download` получил статус `CACHED`.",
    "code_blocks": [
      {
        "filename": "go.mod",
        "lang": "go",
        "code": "module example.com/cachelayer\n\ngo 1.24\n\nrequire github.com/google/uuid v1.6.0\n",
        "note": "Файл модулей с внешней зависимостью"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\n\t\"github.com/google/uuid\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/id\", func(w http.ResponseWriter, r *http.Request) {\n\t\tid := uuid.New().String()\n\t\tfmt.Fprintf(w, \"Generated UUID: %s\\n\", id)\n\t})\n\n\tfmt.Println(\"Server running on :8080...\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Приложение, использующее библиотеку uuid"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\n\nWORKDIR /app\n\n# Шаг 1: Копируем ТОЛЬКО файлы описания зависимостей\nCOPY go.mod go.sum ./\n\n# Шаг 2: Скачиваем зависимости (будет закешировано!)\nRUN go mod download\n\n# Шаг 3: Копируем исходный код проекта\nCOPY . .\n\n# Шаг 4: Быстрая компиляция\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /app/server .\n\nFROM alpine:3.20\nCOPY --from=builder /app/server /app/server\nEXPOSE 8080\nENTRYPOINT [\"/app/server\"]",
        "note": "Идеально оптимизированный по кэшированию Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Первая сборка (скачивание модулей)\ndocker build -t test-cache:v1 .\n\n# Вносим изменение в исходный код\necho \"// comment\" >> main.go\n\n# Вторая сборка (обратите внимание на 'CACHED [builder 4/6] RUN go mod download')\ndocker build -t test-cache:v2 .\n\n# Запуск и тест\ndocker run -d -p 8080:8080 --name test-c test-cache:v2\ncurl http://localhost:8080/id\ndocker rm -f test-c"
      }
    ],
    "under_the_hood": "Docker BuildKit проверяет контрольные суммы файлов в контексте сборки по алгоритму blake3/sha256. Если хэши `go.mod` и `go.sum` совпадают с хэшами предыдущей сборки, ссылка на соответствующий snapshot в `/var/lib/docker/overlay2` переиспользуется мгновенно без сетевых обращений.",
    "pitfalls": "1. Забыть сгенерировать `go.sum` перед сборкой (`go mod tidy`), из-за чего сборка в контейнере завершится ошибкой контрольных сумм.\n2. Копирование лишних служебных файлов (README, тесты), вызывающих сброс кэша компиляции.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что происходит с кэшем Docker, если порядок команд в Dockerfile нарушен: сначала `COPY . .`, а затем `RUN go mod download`?»\n**Ответ:** При любом изменении исходного кода (даже пробела в комментарии) шаг `COPY . .` получает новый хэш контекста, что инвалидирует кэш этого шага и всех последующих. В результате команда `RUN go mod download` при каждой сборке заново идет в интернет за зависимостями, увеличивая время сборки с секунд до минут и создавая риск сбоя сборки при сетевых сбоях прокси/GitHub."
  },
  {
    "num": 11,
    "title": "Многоэтапный билд с runner на базе Alpine (~20 MB)",
    "task": "**[Multi-stage build]**: Раздели Dockerfile на 2 этапа: `builder` (где компилируется бинарник) и `runner` (где бинарник запускается, например, `FROM alpine`). Убедись, что размер образа уменьшился до ~20MB.",
    "theory": "Схема `builder -> runner (Alpine)` является общепринятым стандартом для микросервисов, которым требуется минимальная операционная среда.\n\nВ отличие от `scratch`, образ `alpine:3.20`:\n1. Предоставляет утилиту командной строки `sh` (BusyBox) для запуска скриптов миграций, ожидания баз данных (`wait-for-it`) и проверки здоровья (`wget --spider`).\n2. Имеет встроенную структуру каталогов `/etc`, `/tmp`, `/var/run`.\n3. Позволяет установить дополнительные утилиты (`ca-certificates`, `tzdata`, `curl`) при необходимости.\n4. Весит всего **~7 МБ** в распакованном виде, а вместе с оптимизированным Go-бинарником итоговый размер образа составляет около **15–20 МБ**.",
    "step_by_step": "1. Напишите HTTP-сервис на Go с обработчиком graceful shutdown.\n2. Создайте `Dockerfile` с этапами `builder` и `runner`.\n3. В этапе `runner` используйте образ `alpine:3.20`.\n4. Соберите образ и убедитесь, что размер не превышает 20 МБ.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/health\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\tfmt.Fprintln(w, \"healthy\")\n\t})\n\n\tlog.Println(\"Runner started on :8080\")\n\tif err := http.ListenAndServe(\":8080\", nil); err != nil {\n\t\tlog.Fatal(err)\n\t}\n}",
        "note": "Микросервис с эндпоинтом проверки здоровья"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# Stage 1: Builder\nFROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /bin/app main.go\n\n# Stage 2: Runner\nFROM alpine:3.20 AS runner\nWORKDIR /app\nCOPY --from=builder /bin/app /app/app\n\nEXPOSE 8080\nENTRYPOINT [\"/app/app\"]",
        "note": "Двухэтапная сборка: builder + runner на Alpine"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t app-runner:v1 .\n\n# Проверка размера образа (должно быть < 20MB)\ndocker images app-runner:v1 --format \"{{.Repository}}: {{.Size}}\"\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-run app-runner:v1\ncurl http://localhost:8080/health\ndocker rm -f test-run"
      }
    ],
    "under_the_hood": "Финальный тарбол образа состоит всего из двух слоев: нижний слой — это образ Alpine (rootfs с busybox, musl и базовыми конфигами), а верхний слой — единственный файл `/app/app`. Суммарная контрольная сумма манифеста OCI регистрируется в Docker Registry с минимальным сетевым оверхедом.",
    "pitfalls": "1. Забыть скомпилировать бинарник с `CGO_ENABLED=0`: динамически слинкованный бинарник под glibc не запустится на Alpine (musl).\n2. Запуск контейнера под пользователем root без необходимости.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда в качестве runner-образа следует предпочесть `alpine`, а не `scratch`?»\n**Ответ:** `alpine` выбирают, если: 1) Требуется запуск вспомогательных шелл-скриптов перед стартом сервиса (например, ожидание готовности СУБД или генерация конфигураций). 2) Нужен шелл для проведения регламентных работ или отладки в dev/stage окружениях. 3) Сервис использует Health Check через системную утилиту `wget` или `curl`. Если ничего из этого не требуется, выбирают `scratch` или `distroless`."
  },
  {
    "num": 12,
    "title": "Инструкция HEALTHCHECK: автоматический мониторинг здоровья контейнера",
    "task": "Добавь **health check**: `HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1`. Docker автоматически перезапускает unhealthy контейнер.",
    "theory": "Инструкция `HEALTHCHECK` в Dockerfile определяет, как Docker проверяет работоспособность приложения внутри контейнера.\n\nПараметры директивы:\n- `--interval=30s`: частота выполнения проверки (по умолчанию 30 секунд).\n- `--timeout=3s`: максимальное время ожидания ответа на команду проверки.\n- `--start-period=5s`: льготный период для инициализации приложения (неудачи в этот период не переводят контейнер в статус `unhealthy`).\n- `--retries=3`: количество последовательных неудачных проверок, после которого контейнеру присваивается статус `unhealthy`.\n\nКоманда проверки возвращает код выхода (Exit Code):\n- `0`: Success — контейнер здоров (`healthy`).\n- `1`: Unhealthy — контейнер неисправен (`unhealthy`).\n\nDocker демон отслеживает статус и отображает его в выводе `docker ps`. Системы Docker Compose и оркестраторы (Swarm/Kubernetes) используют этот статус для автоматического перезапуска или исключения контейнера из балансировки нагрузки.",
    "step_by_step": "1. Напишите HTTP-сервис с эндпоинтом `/healthz`.\n2. Добавьте в `Dockerfile` инструкцию `HEALTHCHECK` с использованием встроенной в Alpine утилиты `wget`.\n3. Соберите образ и запустите контейнер.\n4. Отследите смену статуса с `health: starting` на `healthy` через `docker ps`.\n5. Изучите историю проверок через `docker inspect --format='{{json .State.Health}}' <container>`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"log\"\n\t\"net/http\"\n\t\"sync/atomic\"\n)\n\nvar isReady int32 = 1\n\nfunc main() {\n\thttp.HandleFunc(\"/health\", func(w http.ResponseWriter, r *http.Request) {\n\t\tif atomic.LoadInt32(&isReady) == 1 {\n\t\t\tw.WriteHeader(http.StatusOK)\n\t\t\tw.Write([]byte(\"OK\"))\n\t\t\treturn\n\t\t}\n\t\thttp.Error(w, \"Service Unavailable\", http.StatusServiceUnavailable)\n\t})\n\n\t// Эндпоинт для искусственной эмуляции сбоя сервиса\n\thttp.HandleFunc(\"/fail\", func(w http.ResponseWriter, r *http.Request) {\n\t\tatomic.StoreInt32(&isReady, 0)\n\t\tw.Write([]byte(\"Service marked as failing\"))\n\t})\n\n\tlog.Println(\"Server running on :8080...\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервер с эндпоинтом /health и ручным триггером сбоя /fail"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /bin/app main.go\n\nFROM alpine:3.20\nWORKDIR /app\nCOPY --from=builder /bin/app /app/app\n\nEXPOSE 8080\n\n# Определение проверки здоровья через wget (входит в busybox в Alpine)\nHEALTHCHECK --interval=5s --timeout=3s --start-period=2s --retries=2 \\\n  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1\n\nENTRYPOINT [\"/app/app\"]",
        "note": "Dockerfile с декларацией HEALTHCHECK"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t app-health:v1 .\n\n# Запуск контейнера\ndocker run -d -p 8080:8080 --name test-health app-health:v1\n\n# Ждем 3-5 секунд и проверяем статус (будет '(healthy)')\ndocker ps --filter \"name=test-health\" --format \"table {{.Names}}\\t{{.Status}}\"\n\n# Эмулируем поломку\ncurl http://localhost:8080/fail\n\n# Ждем 10-12 секунд и снова смотрим статус (перейдет в '(unhealthy)')\ndocker ps --filter \"name=test-health\" --format \"table {{.Names}}\\t{{.Status}}\"\n\n# Очистка\ndocker rm -f test-health"
      }
    ],
    "under_the_hood": "Демон dockerd периодически порождает процесс проверки внутри пространства имен контейнера через системный вызов `execve` рантайма `runc`. Логи последних пяти проверок здоровья и коды выхода сохраняются во внутренней структуре контейнера `ContainerState.Health` и доступны через Docker API.",
    "pitfalls": "1. Забытый флаг `--spider` у `wget`: утилита попытается сохранить файл ответа на диск вместо простой проверки заголовков.\n2. Слишком короткий `--timeout`, из-за чего под нагрузкой контейнер ложно признается `unhealthy`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в образах на базе `scratch` стандартная инструкция `HEALTHCHECK CMD wget ...` не работает и как решить эту задачу без внешних утилит?»\n**Ответ:** В `scratch` нет ни `/bin/sh`, ни `wget`, ни `curl`. Попытка выполнить команду проверки завершится ошибкой отсутствия шелла. Решение: 1) Встроить проверку здоровья прямо в Go-бинарник в виде подкоманды: `HEALTHCHECK CMD [\"/app\", \"healthcheck\"]`, где бинарник сам делает HTTP GET запрос к `127.0.0.1:8080/health` и возвращает `os.Exit(0)` или `os.Exit(1)`. 2) Использовать нативные `livenessProbe` / `readinessProbe` в Kubernetes, которые проверяют сетевой сокет снаружи."
  },
  {
    "num": 13,
    "title": "Полностью статический бинарник: флаги компилятора -ldflags='-w -s' и CGO_ENABLED=0",
    "task": "Соберите полностью статический бинарник: `CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -ldflags=\"-w -s\" -o app`.",
    "theory": "Сборка полностью автономного статического бинарника в Go опирается на две ключевые концепции:\n\n1. **`CGO_ENABLED=0`:**\n   По умолчанию компилятор Go может динамически линковаться с libc хоста при использовании стандартных пакетов `net` (системный DNS резолвер `cgo`) и `os/user`.\n   Переменная `CGO_ENABLED=0` принудительно переключает Go на чистый внутренний Go-резолвер (`netgo`) и внутреннюю реализацию работы с пользователями (`osusergo`). Бинарник становится абсолютно статическим ELF-файлом (`statically linked`).\n\n2. **Флаги линковщика `-ldflags=\"-w -s\"`:**\n   - `-w`: отключает генерацию отладочной DWARF-информации (размер стектрейсов и отладчика `gdb`).\n   - `-s`: удаляет таблицу символов (Symbol Table) из бинарника.\n   Эти флаги сокращают размер скомпилированного файла на **30–50%** без влияния на производительность и вывод имен функций в runtime-паниках Go.\n\nУтилита `file <binary>` в Linux позволяет подтвердить статический статус: вывод `statically linked` гарантирует запуск в любом дистрибутиве и в `scratch`.",
    "step_by_step": "1. Напишите Go-сервис.\n2. Скомпилируйте бинарник стандартной командой `go build` и проверьте его через `file` и `ldd`.\n3. Скомпилируйте бинарник с `CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\"`.\n4. Сравните размеры файлов и убедитесь, что `ldd` возвращает `not a dynamic executable`.\n5. Упакуйте полученный бинарник в контейнер.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"Statically linked Go application running!\")\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Минимальный микросервис"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\n\nWORKDIR /src\nCOPY main.go .\n\n# Сборка полностью статического бинарника со сжатием символов\nRUN CGO_ENABLED=0 GOOS=linux go build \\\n    -a \\\n    -installsuffix cgo \\\n    -ldflags=\"-w -s\" \\\n    -o /bin/app main.go\n\nFROM scratch\nCOPY --from=builder /bin/app /app\nEXPOSE 8080\nENTRYPOINT [\"/app\"]",
        "note": "Статическая сборка для scratch"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Локальная проверка связывания\nCGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o app-static main.go\nfile app-static\n# Вывод: ELF 64-bit LSB executable, ..., statically linked, stripped\n\n# Проверка динамических библиотек (должно вернуть 'not a dynamic executable')\nldd app-static || echo \"Verified: Fully static!\"\n\n# Сборка контейнера\ndocker build -t app-static:latest .\ndocker images app-static:latest"
      }
    ],
    "under_the_hood": "В ELF заголовке файла (`readelf -l app-static`) при статической линковке отсутствует сегмент `INTERP` (путь к динамическому загрузчику `/lib64/ld-linux-x86-64.so.2`). Ядро загружает код сразу в адресное пространство процесса без участия userspace-линковщика, что исключает любые зависимости от библиотек файловой системы контейнера.",
    "pitfalls": "1. Флаг `-s` удаляет таблицу символов, из-за чего профилировщики `pprof` без исходного бинарника не смогут восстановить символические имена функций в сторонних тулах.\n2. При использовании CGO (например, go-sqlite3) `CGO_ENABLED=0` вызовет ошибку компиляции.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что делает флаг `-ldflags=\"-w -s\"` при сборке Go и влияет ли он на способность Go выводить стек вызовов при panic?»\n**Ответ:** Флаг `-w` вырезает DWARF-информацию для внешних отладчиков, а `-s` удаляет стандартную таблицу символов ELF. Однако рантайм Go сохраняет свою внутреннюю таблицу pclntab (program counter line table), поэтому при `panic()` Go по-прежнему выводит полный стек вызовов с именами функций, именами файлов и номерами строк. Производительность приложения также не меняется."
  },
  {
    "num": 14,
    "title": "Настройка .dockerignore: оптимизация build context и безопасность",
    "task": "Настрой **.dockerignore**: исключи `*.md`, `.git/`, `vendor/`, `*_test.go`, `.env`, `docker-compose.yml`. Покажи, что уменьшает build context и ускоряет сборку.",
    "theory": "При выполнении команды `docker build .` клиент Docker упаковывает всю текущую директорию в tar-архив и передает его демону Docker по протоколу HTTP/gRPC. Этот объем данных называется **Build Context** (контекст сборки).\n\nЕсли в проекте нет файла `.dockerignore`:\n1. В контекст сборки попадает папка `.git/` (сотни мегабайт истории, коммитов и веток).\n2. Попадают локальные бинарники, дампы памяти (`core`), логи, папка `vendor/` и временные файлы IDE (`.idea/`, `.vscode/`).\n3. Попадают конфиденциальные файлы окружения: `.env`, приватные ключи `.pem`, `id_rsa`.\n\nФайл `.dockerignore` работает аналогично `.gitignore` и исключает указанные файлы и директории еще на стороне клиента Docker до отправки контекста демону.\n\nПреимущества `.dockerignore`:\n- Ускорение старта сборки (передача контекста за 0.05 сек вместо 15–30 сек).\n- Предотвращение случайной утечки паролей и секретов в слои образа.\n- Эффективное кэширование (изменение локального README не сбрасывает кэш сборки).",
    "step_by_step": "1. Создайте в корне проекта файл `.dockerignore`.\n2. Добавьте в него исключения для `.git`, `.env`, `*.md`, `bin/`, `tmp/`, `docker-compose*.yml`.\n3. Запустите `docker build` и посмотрите на размер отправленного контекста: `Sending build context to Docker daemon ...`.\n4. Убедитесь, что контекст сборки уменьшился до десятков килобайт.",
    "code_blocks": [
      {
        "filename": ".dockerignore",
        "lang": "dockerignore",
        "code": "# Системы контроля версий\n.git\n.gitignore\n\n# Секреты и локальные переменные окружения\n.env*\n*.pem\n*.key\n\n# Локальные бинарники и кэш сборки\nbin/\nbuild/\n*.exe\n*.test\n\n# Тесты и документация\n*_test.go\n*.md\ndocs/\n\n# IDE и редакторы\n.idea/\n.vscode/\n*.swp\n\n# Docker и Compose файлы\ndocker-compose*.yml\nDockerfile*\nMakefile",
        "note": "Production-шаблон .dockerignore для Go-проекта"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY . .\nRUN CGO_ENABLED=0 go build -o /app main.go\n\nFROM scratch\nCOPY --from=builder /app /app\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile, использующий отфильтрованный контекст"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Создадим фиктивный тяжелый файл, который должен игнорироваться\ndd if=/dev/zero of=large_dump.bin bs=1M count=100\n\n# Добавим его в .dockerignore\necho \"large_dump.bin\" >> .dockerignore\n\n# Сборка: обратите внимание на объем контекста сборки (менее 100KB)\ndocker build -t test-ignore:latest .\n\n# Очистка\nrm -f large_dump.bin"
      }
    ],
    "under_the_hood": "CLI-клиент Docker перед отправкой запроса к Docker Daemon парсит `.dockerignore` с помощью синтаксиса filepath.Match. Файлы, удовлетворяющие шаблонам, исключаются из формируемого потока (stream) tar-архива в памяти. Демон даже не узнает о существовании этих файлов на хосте.",
    "pitfalls": "1. Отсутствие `.env` в `.dockerignore`: файл попадает в слой образа при выполнении `COPY . .`, раскрывая пароли от production БД любому, у кого есть доступ к registry.\n2. Не исключен `.git`: образ становится гигантским, а кэш инвалидируется при каждом `git commit`.",
    "bigtech_interview": "**Вопрос с собеседования:** «К каким последствиям приводит отсутствие файла `.dockerignore` в репозитории с активной разработкой при сборках в CI/CD?»\n**Ответ:** 1) Утечка секретов и истории `.git` в продакшн-образы. 2) Резкое замедление сборок из-за передачи сотен мегабайт локального мусора по сети на Docker daemon. 3) Полный сброс кэша слоев на шаге `COPY . .` при изменении любого несущественного файла (например, обновление документации `README.md` или изменение локальной ветки в `.git/HEAD`)."
  },
  {
    "num": 15,
    "title": "Использование FROM scratch в runtime stage: абсолютный минимум",
    "task": "Используйте `FROM scratch` в runtime stage — это пустой образ размером 0 байт, содержащий только ваш бинарник.",
    "theory": "Использование `FROM scratch` в финальном этапе сборки представляет собой верхний уровень оптимизации контейнеров для компилируемых языков (Go, Rust).\n\nПреимущества `FROM scratch`:\n1. **0 байт базового слоя:** образ не содержит ни одного байта стороннего дистрибутива Linux.\n2. **Нулевой риск CVE:** сканеры уязвимостей (Trivy, Clair, Snyk) показывают 0 известных уязвимостей в ОС, так как ОС отсутствует.\n3. **Невозможность исполнения стороннего кода:** отсутствие командного процессора (`sh`/`bash`) делает невозможным выполнение классических скриптовых пейлоадов.\n\nОднако запуск в пустом окружении накладывает жесткие требования:\n- Статическая линковка (`CGO_ENABLED=0`).\n- Корневые сертификаты CA (`/etc/ssl/certs/ca-certificates.crt`), если приложение делает исходящие HTTPS/TLS запросы.\n- Файлы временных зон (`/usr/share/zoneinfo`), если приложению требуется парсить локальные часовые пояса.",
    "step_by_step": "1. Напишите HTTP-сервис.\n2. В первом этапе скомпилируйте статический бинарник.\n3. Во втором этапе объявите `FROM scratch`.\n4. Скопируйте только бинарник.\n5. Запустите контейнер и убедитесь в его минимальном объеме и работоспособности.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"runtime\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Pure scratch runtime! Go: %s, OS: %s/%s\\n\",\n\t\t\truntime.Version(), runtime.GOOS, runtime.GOARCH)\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис, выводящий информацию о рантайме"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS build\nWORKDIR /app\nCOPY main.go .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /app/bin main.go\n\nFROM scratch\nCOPY --from=build /app/bin /bin\nEXPOSE 8080\nENTRYPOINT [\"/bin\"]",
        "note": "Минималистичный образ scratch"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t app-pure-scratch:latest .\n\n# Размер образа (ровно размер бинарника ~6.5MB)\ndocker images app-pure-scratch:latest\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-ps app-pure-scratch:latest\ncurl http://localhost:8080\ndocker rm -f test-ps"
      }
    ],
    "under_the_hood": "Файл манифеста образа содержит конфигурационный JSON и один diff-слой tarball, содержащий единственный файл `/bin`. Контейнерный движок монтирует этот слой в качестве rootfs и запускает процесс с `init` PID=1 внутри изолированного pid namespace.",
    "pitfalls": "1. Попытка совершить исходящий HTTPS-запрос из приложения в scratch без предварительного копирования `ca-certificates.crt`: запрос упадет с ошибкой `x509: certificate signed by unknown authority`.\n2. Использование функции `time.LoadLocation(\"Europe/Moscow\")`: вернет ошибку `unknown time zone`, если не скопирована база zoneinfo.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему при вызове `time.LoadLocation(\"Europe/Moscow\")` внутри контейнера `FROM scratch` приложение возвращает ошибку `unknown time zone`, и как ее исправить без раздувания образа?»\n**Ответ:** В `scratch` отсутствует системная база данных часовых поясов IANA (`/usr/share/zoneinfo`). Для исправления есть два пути: 1) Скопировать `/usr/share/zoneinfo` из этапа builder: `COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo`. 2) В коде Go 1.15+ импортировать анонимный пакет `import _ \"time/tzdata\"`, который компилирует базу часовых поясов прямо внутрь Go-бинарника (добавляет к бинарнику ~450 КБ)."
  },
  {
    "num": 16,
    "title": "Оптимизация размера: scratch + необходимые корневые сертификаты",
    "task": "Оптимизируйте размер образа: используйте `FROM scratch`, копируйте только бинарник и необходимые сертификаты. Проверьте размер через `docker images`.",
    "theory": "При выполнении любого защищенного исходящего сетевого запроса (`http.Get(\"https://api.github.com\")`) криптографическая подсистема Go (`crypto/x509`) валидирует цепочку доверия SSL/TLS сертификата сервера.\nДля этого клиенту необходим локальный пул доверенных корневых сертификатов (Root CA Certificates).\n\nВ обычных дистрибутивах Linux этот пул лежит по пути `/etc/ssl/certs/ca-certificates.crt`.\nВ чистом образе `FROM scratch` этот файл отсутствует. При попытке совершить HTTPS-запрос Go возвращает фатальную ошибку:\n`x509: failed to load system roots and no roots provided`\n\nРешение:\nВ этапе `builder` устанавливается пакет `ca-certificates`, после чего файл сертификатов копируется в runtime-образ:\n`COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/`\nРазмер файла сертификатов составляет всего около **200 КБ**, сохраняя образ ультракомпактным и одновременно полностью готовым к работе с внешними HTTPS API.",
    "step_by_step": "1. Напишите Go-клиент, выполняющий запрос к внешнему HTTPS API.\n2. В этапе builder установите пакет `ca-certificates`.\n3. В этапе runtime (`FROM scratch`) скопируйте файл сертификатов в `/etc/ssl/certs/ca-certificates.crt`.\n4. Соберите образ и убедитесь, что HTTPS-запрос успешно проходит.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n\t\"log\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc main() {\n\tclient := &http.Client{Timeout: 5 * time.Second}\n\n\thttp.HandleFunc(\"/fetch\", func(w http.ResponseWriter, r *http.Request) {\n\t\t// Исходящий HTTPS запрос\n\t\tresp, err := client.Get(\"https://httpbin.org/get\")\n\t\tif err != nil {\n\t\t\thttp.Error(w, fmt.Sprintf(\"TLS Handshake Error: %v\", err), http.StatusInternalServerError)\n\t\t\treturn\n\t\t}\n\t\tdefer resp.Body.Close()\n\n\t\tbody, _ := io.ReadAll(resp.Body)\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\tw.Write(body)\n\t})\n\n\tlog.Println(\"Listening on :8080...\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис с исходящим HTTPS-запросом"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\n\n# Установка актуальных корневых сертификатов\nRUN apk add --no-cache ca-certificates\n\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /bin/app main.go\n\nFROM scratch\n\n# Критически важно для работы HTTPS/TLS в scratch\nCOPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/\n\nCOPY --from=builder /bin/app /bin/app\n\nEXPOSE 8080\nENTRYPOINT [\"/bin/app\"]",
        "note": "Dockerfile с копированием сертификатов в scratch"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t app-scratch-tls:latest .\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-tls app-scratch-tls:latest\n\n# Проверка HTTPS запроса\ncurl -s http://localhost:8080/fetch | grep \"httpbin.org\"\n\n# Очистка\ndocker rm -f test-tls"
      }
    ],
    "under_the_hood": "Пакет `crypto/x509` в Go имеет захардкоженный список стандартных путей для поиска корневых сертификатов в Linux:\n`/etc/ssl/certs/ca-certificates.crt`, `/etc/pki/tls/certs/ca-bundle.crt`, `/etc/ssl/ca-bundle.pem`.\nРазмещение сертификата по пути `/etc/ssl/certs/ca-certificates.crt` обеспечивает автоматическое обнаружение пула сертификатов без явной конфигурации переменных окружения.",
    "pitfalls": "1. Копирование всей папки `/etc/ssl/certs` со всеми симлинками вместо одного файла бандла.\n2. Устаревший файл сертификатов при редких пересборках образа, что может привести к сбою валидации при отзыве промежуточных CA.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему при развертывании Go-микросервиса в контейнере `FROM scratch` запросы к внутренней базе данных PostgreSQL с SSL (`sslmode=verify-full`) падают с ошибкой x509?»\n**Ответ:** Go-драйвер БД использует системный пул сертификатов для проверки сертификата сервера БД. В `scratch` нет файла `/etc/ssl/certs/ca-certificates.crt` и корпоративного Root CA сертификата. Необходимо скопировать публичный корневой сертификат компании в образ или передать его через `tls.Config.RootCAs` в конфигурации подключения."
  },
  {
    "num": 17,
    "title": "BuildKit Cache Mounts: ускорение сборки зависимостей в 10 раз",
    "task": "Напиши **Dockerfile с BuildKit cache mounts**: `RUN --mount=type=cache,target=/go/pkg/mod go mod download`. Кэшируй `go mod download` между сборками даже при изменении кода. Ускорь CI сборку в 10 раз.",
    "theory": "Начиная с Docker 18.09 и сборщика **BuildKit** (включен по умолчанию в современных версиях Docker), появилась поддержка монтирования кэша:\n`RUN --mount=type=cache,target=<path>`\n\nВ Go-разработке есть две ключевые директории кэша:\n1. `/go/pkg/mod`: кэш скачанных исходных кодов Go-модулей (`GOPATH/pkg/mod`).\n2. `/root/.cache/go-build`: кэш скомпилированных пакетов Go (`GOCACHE`).\n\nПроблема классического кэширования слоев:\nЕсли обновилась хотя бы одна библиотека в `go.mod`, весь слой `RUN go mod download` пересчитывается с нуля, скачивая все 100% зависимостей.\n\nПреимущество `type=cache`:\nДиректория монтируется из специального хранилища BuildKit на хосте. Модули, скачанные в предыдущих сборках, **сохраняются на хосте даже при изменении `go.mod` и `main.go`**!\nКомпилятор Go переиспользует уже скомпилированные `.a` архивы из `GOCACHE`, что ускоряет сборку в CI/CD в 5–10 раз.",
    "step_by_step": "1. Включите BuildKit (если не включен по умолчанию): `export DOCKER_BUILDKIT=1`.\n2. Добавьте синтаксическую директиву `# syntax=docker/dockerfile:1` в начало Dockerfile.\n3. Используйте `--mount=type=cache,target=/go/pkg/mod` для шага `go mod download`.\n4. Используйте `--mount=type=cache,target=/root/.cache/go-build` для шага `go build`.\n5. Проверьте скорость повторной сборки при изменении кода.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"BuildKit cache mount demo!\\n\")\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Минимальный микросервис"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# syntax=docker/dockerfile:1\nFROM golang:1.24-alpine AS builder\n\nWORKDIR /src\n\nCOPY go.mod go.sum* ./\n\n# Кэширование загрузки модулей через специальный mount\nRUN --mount=type=cache,target=/go/pkg/mod \\\n    go mod download\n\nCOPY . .\n\n# Кэширование скомпилированных пакетов компилятора Go\nRUN --mount=type=cache,target=/go/pkg/mod \\\n    --mount=type=cache,target=/root/.cache/go-build \\\n    CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /bin/app .\n\nFROM alpine:3.20\nCOPY --from=builder /bin/app /bin/app\nEXPOSE 8080\nENTRYPOINT [\"/bin/app\"]",
        "note": "Dockerfile с использованием BuildKit Cache Mounts"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Включаем BuildKit\nexport DOCKER_BUILDKIT=1\n\n# Сборка с BuildKit\ndocker build -t app-buildkit:v1 .\n\n# Вносим изменение в код\ntouch main.go\n\n# Повторная сборка использует кэш компилятора из /root/.cache/go-build мгновенно!\ndocker build -t app-buildkit:v2 ."
      }
    ],
    "under_the_hood": "BuildKit монтирует локальное файловое хранилище хоста (`/var/lib/docker/buildkit/cache`) в указанную точку монтирования на время исполнения контейнера сборщика. Содержимое этого каталога не записывается в итоговый слой образа (в слое остается только бинарник `/bin/app`), что дает максимальную скорость без раздувания размера образа.",
    "pitfalls": "1. Забыть указать монтирование кэша модулей на шаге `go build`: если `go build` обратится к модулям, а смонтирован только `GOCACHE`, модули не будут найдены в слое.\n2. Недоступность BuildKit на устаревших версиях демона Docker.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем принципиальная разница между кэшированием слоев через `COPY go.mod . && RUN go mod download` и кэшированием через `RUN --mount=type=cache` в BuildKit?»\n**Ответ:** Кэширование слоев инвалидируется целиком при изменении файла `go.mod` (добавлении или обновлении хотя бы одной библиотеки), требуя повторной загрузки всех модулей. Кэш-маунты BuildKit сохраняют директорию кэша на диске хоста независимо от состояния слоев. При изменении `go.mod` скачивается только новая дельта зависимостей, а все старые библиотеки и скомпилированные пакеты мгновенно берутся из кэша хоста."
  },
  {
    "num": 18,
    "title": "Multi-stage сборка: Золотой стандарт продакшн-контейнеризации",
    "task": "**Multi-stage сборка (Золотой стандарт)**: Образ из упр. 576 весит около 800+ МБ (потому что содержит исходники Go, компилятор, ОС Linux). Напиши Dockerfile из двух этапов (stages):\n    * Этап 1 (`builder`): образ `golang`, собираем бинарник.\n    * Этап 2: берем легковесный образ `alpine:latest`. Копируем туда бинарник из `builder`. Убедись, что итоговый образ весит около 15-20 МБ!",
    "theory": "«Золотой стандарт» Dockerfile для Go в продакшне объединяет все лучшие практики оптимизации и безопасности:\n1. **Два этапа сборки (Builder + Minimal Runtime).**\n2. **Селективное кэширование зависимостей (`go.mod` перед кодом).**\n3. **Отключение CGO (`CGO_ENABLED=0`) и флаги компилятора (`-ldflags=\"-w -s\"`).**\n4. **Непривилегированный пользователь (Non-root user).**\n5. **Наличие корневых сертификатов CA и базы таймзон.**\n\nТакой подход гарантирует:\n- Размер образа **15–25 МБ**.\n- Время сборки при изменении кода: **< 2 секунд**.\n- Защиту от атак повышения привилегий.",
    "step_by_step": "1. Опишите законченный production Dockerfile с этапом сборщика и легковесным этапом Alpine.\n2. Создайте non-root пользователя.\n3. Добавьте сертификаты и зону времени.\n4. Проверьте запуск и корректность прав процесса.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Production Grade Go Container!\\n\")\n\t})\n\n\tport := os.Getenv(\"PORT\")\n\tif port == \"\" {\n\t\tport = \"8080\"\n\t}\n\n\tlog.Printf(\"Application running on port :%s\\n\", port)\n\t_ = http.ListenAndServe(\":\"+port, nil)\n}",
        "note": "Production микросервис"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# === Stage 1: Build ===\nFROM golang:1.24-alpine AS builder\n\nRUN apk add --no-cache ca-certificates tzdata\n\nWORKDIR /app\n\n# Кэширование модулей\nCOPY go.mod go.sum* ./\nRUN go mod download\n\n# Копирование исходного кода и сборка\nCOPY . .\nRUN CGO_ENABLED=0 GOOS=linux go build \\\n    -ldflags=\"-w -s\" \\\n    -o /app/server .\n\n# Создание непривилегированного пользователя\nRUN adduser -D -u 10001 -s /sbin/nologin appuser\n\n# === Stage 2: Production Runtime ===\nFROM alpine:3.20\n\nWORKDIR /app\n\n# Сертификаты и таймзоны\nCOPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/\nCOPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo\nCOPY --from=builder /etc/passwd /etc/passwd\nCOPY --from=builder /etc/group /etc/group\n\n# Бинарник\nCOPY --from=builder --chown=10001:10001 /app/server /app/server\n\n# Переключение на non-root\nUSER 10001:10001\n\nEXPOSE 8080\n\nENTRYPOINT [\"/app/server\"]",
        "note": "Золотой стандарт продакшн Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t app-gold-standard:v1 .\n\n# Проверка размера\ndocker images app-gold-standard:v1\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-gold app-gold-standard:v1\ncurl http://localhost:8080\ndocker exec test-gold id\ndocker rm -f test-gold"
      }
    ],
    "under_the_hood": "Флаг `--chown=10001:10001` в команде `COPY` сразу назначает правильного владельца файла в файловой системе слоя без создания дополнительного тяжелого слоя `RUN chown ...`.",
    "pitfalls": "1. Выполнение `RUN chown -R appuser /app` в runtime этапе: это дублирует размер всех файлов в новом слое. Всегда используйте `COPY --chown=...`.\n2. Запуск от пользователя, у которого нет прав на чтение бинарника (права должны быть 0755).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему антипаттерном считается использование команды `RUN chown -R appuser:appgroup /app` после команды `COPY` в Dockerfile?»\n**Ответ:** В архитектуре файловой системы OverlayFS команда `chown` модифицирует метаданные файлов, из-за чего механизм Copy-on-Write полностью копирует все изменяемые файлы из нижнего слоя в новый верхний слой. Если бинарник или статика весили 100 МБ, образ увеличится еще на 100 МБ. Правильное решение — использовать флаг `COPY --chown=UID:GID`."
  },
  {
    "num": 19,
    "title": "Ловушка отсутствия SSL сертификатов в scratch / distroless и ее устранение",
    "task": "**[Scratch / Distroless]**: Используй `FROM scratch` (или `gcr.io/distroless/static-debian12`). Запусти бинарник. Поймай ошибку отсутствия SSL сертификатов (если делаешь HTTPS-запросы) и добавь их через `COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/`.",
    "theory": "При развертывании в минималистичных образах (`scratch` или голом `distroless`) разработчики часто сталкиваются с классической ошибкой:\n`Get \"https://api.stripe.com/v1/...\": x509: certificate signed by unknown authority`\n\nМеханизм возникновения проблемы:\n1. В операционных системах Linux доверенные корневые сертификаты удостоверяющих центров (Let's Encrypt, DigiCert, GlobalSign) поставляются отдельным пакетом `ca-certificates`.\n2. Библиотека Go `crypto/x509` при проверке TLS-соединения пытается загрузить доверенные сертификаты из системных путей файловой системы (`/etc/ssl/certs`).\n3. В пустом образе `scratch` эта директория пуста. Go не может построить цепочку доверия от сертификата сервера до доверенного корня и аварийно завершает сетевой вызов.\n\nРешение:\nЯвное копирование файла сертификатов из этапа сборки:\n`COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt`",
    "step_by_step": "1. Создайте сервис, делающий HTTPS-запрос к внешнему API.\n2. Соберите образ на `scratch` без сертификатов и воспроизведите ошибку `x509: certificate signed by unknown authority`.\n3. Добавьте директиву `COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/`.\n4. Пересоберите образ и убедитесь в успешном выполнении HTTPS-запроса.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc main() {\n\tclient := &http.Client{Timeout: 5 * time.Second}\n\n\thttp.HandleFunc(\"/check-tls\", func(w http.ResponseWriter, r *http.Request) {\n\t\tresp, err := client.Get(\"https://www.cloudflare.com\")\n\t\tif err != nil {\n\t\t\tlog.Printf(\"TLS failure: %v\", err)\n\t\t\thttp.Error(w, fmt.Sprintf(\"TLS Error: %v\", err), http.StatusBadGateway)\n\t\t\treturn\n\t\t}\n\t\tdefer resp.Body.Close()\n\n\t\tfmt.Fprintf(w, \"TLS Handshake OK! Status: %s\\n\", resp.Status)\n\t})\n\n\tlog.Println(\"Server running on :8080...\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис, тестирующий TLS соединение"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\n\n# Устанавливаем сертификаты в builder\nRUN apk add --no-cache ca-certificates\n\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /bin/app main.go\n\nFROM scratch\n\n# Перенос доверенных корневых сертификатов решает ошибку x509\nCOPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/\n\nCOPY --from=builder /bin/app /bin/app\n\nEXPOSE 8080\nENTRYPOINT [\"/bin/app\"]",
        "note": "Dockerfile с исправленной конфигурацией TLS сертификатов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t test-tls-fix:latest .\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-tls-instance test-tls-fix:latest\n\n# Проверка: вернет 'TLS Handshake OK! Status: 200 OK'\ncurl http://localhost:8080/check-tls\n\n# Очистка\ndocker rm -f test-tls-instance"
      }
    ],
    "under_the_hood": "В исходном коде Go (`src/crypto/x509/root_linux.go`) определен срез путей `certFiles`. Функция `systemRootsPool()` последовательно проверяет эти пути. При первом успешном чтении файла он парсится через `AppendCertsFromPEM`. Если ни один файл не найден, возвращается пустой пул сертификатов, что делает любые внешние HTTPS-соединения невозможными.",
    "pitfalls": "1. Забыть установить пакет `ca-certificates` в builder-образе перед копированием файла.\n2. Попытка копировать файл `/etc/ssl/certs/ca-certificates.crt` из хостовой машины вместо воспроизводимого builder-слоя.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в Go-приложении, работающем в контейнере `FROM scratch`, подключиться к внутреннему корпоративному сервису с самоподписанным (self-signed) SSL-сертификатом без отключения `InsecureSkipVerify`?»\n**Ответ:** 1) В Dockerfile скопировать корпоративный Root CA сертификат в образ (`COPY internal-ca.crt /usr/local/share/ca-certificates/`) и выполнить `update-ca-certificates` в builder stage, скопировав объединенный бандл в scratch. 2) Либо в Go-коде загрузить `.crt` файл через `os.ReadFile`, создать кастомный `x509.NewCertPool()`, добавить сертификат через `pool.AppendCertsFromPEM()` и передать его в `tls.Config{RootCAs: pool}` для `http.Client`."
  },
  {
    "num": 20,
    "title": "Многоэтапная сборка: оптимизация с переходом на Alpine и сравнение веса",
    "task": "**Многоэтапная сборка (Multi-stage Dockerfile)**: Оптимизируйте Dockerfile из предыдущей задачи с помощью многоэтапной сборки (Multi-stage):\n    * Этап 1 (`AS builder`): Используйте тяжелый образ `golang:1.26-alpine` для загрузки зависимостей и компиляции бинарника.\n    * Этап 2: Возьмите чистый легковесный образ `alpine:latest`, скопируйте в него *только* скомпилированный на первом этапе бинарный файл и укажите его в `ENTRYPOINT`.\n    Соберите образ и сравните его размер с предыдущим (размер должен упасть до 15–30 МБ).",
    "theory": "Многоэтапная сборка (Multi-stage build) позволяет объединить в одном репозитории тяжелое окружение компиляции и чистое легковесное окружение исполнения.\n\nНа первом этапе (`FROM golang:1.24-alpine AS builder`) используются компилятор Go, заголовочные файлы и кэш пакетов.\nНа втором этапе (`FROM alpine:3.20`) создается чистый образ, куда из builder-этапа переносится исключительно бинарный файл через `COPY --from=builder /app/main /app/main`.\n\nТакое разделение позволяет сократить размер итогового контейнера с 800+ МБ до **15–30 МБ**, сохраняя при этом наличие командной оболочки `sh` и утилит Busybox, необходимых для эксплуатации в ряде систем.",
    "step_by_step": "1. Создайте Go-приложение с веб-сервером.\n2. Напишите `Dockerfile` с этапами `builder` на базе `golang:1.24-alpine` и `alpine:3.20` для рантайма.\n3. Укажите флаги компиляции `CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\"`.\n4. Соберите образ и сравните его размер с тяжелым single-stage образом.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"High-performance Go service in Alpine runtime!\\n\")\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Минимальный веб-сервис"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# Этап 1: Builder\nFROM golang:1.24-alpine AS builder\n\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /bin/app main.go\n\n# Этап 2: Минимальный Runtime\nFROM alpine:3.20\n\nWORKDIR /app\nCOPY --from=builder /bin/app /app/app\n\nEXPOSE 8080\nENTRYPOINT [\"/app/app\"]",
        "note": "Многоэтапный Dockerfile для перехода на Alpine"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка многоэтапного образа\ndocker build -t app-alpine-optimized:v1 .\n\n# Проверка размера (образ весит ~15-20 MB)\ndocker images app-alpine-optimized:v1 --format \"{{.Repository}}: {{.Size}}\"\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-alp-opt app-alpine-optimized:v1\ncurl http://localhost:8080\ndocker rm -f test-alp-opt"
      }
    ],
    "under_the_hood": "Сборщик Docker BuildKit анализирует дерево зависимостей этапов. Он видит, что из этапа `builder` во второй этап запрашивается только файл `/bin/app`. Все остальные временные слои, сгенерированные шагами `RUN go build` и скачиванием компилятора, остаются в builder cache и не включаются в экспортируемый tar-манифест.",
    "pitfalls": "1. Забыть скомпилировать бинарник со статическим связыванием: если CGO включен, бинарник будет требовать динамические библиотеки musl соответствующей версии.\n2. Копирование всей папки `/src` вместо скомпилированного бинарника.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Go многоэтапная сборка дает больший выигрыш в размере и безопасности, чем в языках Python или Node.js?»\n**Ответ:** Go — компилируемый язык со статической типизацией и автономным рантаймом. На этапе исполнения Go не требует виртуальной машины, интерпретатора, исходных кодов (`node_modules`, `site-packages`) и системных динамических библиотек. В образ помещается один скомпилированный машинный код, что позволяет уменьшить размер образа до единиц мегабайт и свести attack surface к нулю."
  },
  {
    "num": 21,
    "title": "Google Distroless: безопасность без шелла и системных утилит",
    "task": "**Distroless**: Используйте `gcr.io/distroless/static-debian12` — минимальный образ от Google с базовыми библиотеками, но без shell (лучше для безопасности).",
    "theory": "**Google Distroless** (`gcr.io/distroless/static-debian12`) — это специализированная линейка базовых образов, содержащих только файлы, критически необходимые для запуска программы.\n\nВ образе Distroless Static присутствуют:\n- Корневой бандл сертификатов SSL/TLS (`/etc/ssl/certs/ca-certificates.crt`).\n- Файл описания системных пользователей `/etc/passwd` с непривилегированным пользователем `nonroot` (UID 65532).\n- База данных временных зон (`/usr/share/zoneinfo`).\n\nЧего в Distroless НЕТ:\n- Нет оболочки (`/bin/sh`, `/bin/bash`).\n- Нет пакетных менеджеров (`apt`, `dpkg`, `apk`).\n- Нет стандартных утилит ядра (`ls`, `cat`, `rm`, `ps`, `curl`, `wget`).\n\nТакая конфигурация делает эксплуатацию большинства классических уязвимостей типа RCE (Remote Code Execution) практически невозможной, так как атакующий не может породить командную строку или скачать эксплойт из сети.",
    "step_by_step": "1. Напишите Go-сервис.\n2. В первом этапе скомпилируйте статический бинарник (`CGO_ENABLED=0`).\n3. Во втором этапе используйте образ `gcr.io/distroless/static-debian12`.\n4. Скопируйте бинарник и запустите контейнер.\n5. Продемонстрируйте, что запуск `docker exec -it <container> sh` невозможен.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Running safely on Google Distroless!\\nTime: %s\\n\", time.Now().UTC())\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Безопасный сервис"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\n\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /bin/app main.go\n\n# Минимальный безопасный образ от Google\nFROM gcr.io/distroless/static-debian12\n\nWORKDIR /app\nCOPY --from=builder /bin/app /app/app\n\n# Запуск от встроенного непривилегированного пользователя nonroot (65532)\nUSER nonroot:nonroot\n\nEXPOSE 8080\nENTRYPOINT [\"/app/app\"]",
        "note": "Dockerfile с базовым образом Distroless"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t app-distroless-safe:v1 .\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-distro-safe app-distroless-safe:v1\ncurl http://localhost:8080\n\n# Попытка взлома/входа в контейнер через shell\ndocker exec -it test-distro-safe /bin/sh\n# Вывод: OCI runtime exec failed: exec: \"/bin/sh\": stat /bin/sh: no such file or directory\n\ndocker rm -f test-distro-safe"
      }
    ],
    "under_the_hood": "При попытке выполнить `docker exec` демон Docker обращается к `containerd`, который через системный вызов `setns` присоединяется к пространствам имен контейнера и пытается вызвать `execve(\"/bin/sh\", ...)`. Поскольку в файловой системе контейнера нет файла `/bin/sh`, ядро возвращает ошибку `ENOENT`, блокируя любую попытку интерактивного доступа.",
    "pitfalls": "1. Использование shell-формы директив `CMD /app/app` или `ENTRYPOINT /app/app`. Без `/bin/sh` запуск упадет сразу.\n2. Необходимость отладки: для исследования падающего контейнера необходимо применять Kubernetes ephemeral debug containers или локальные bind mounts.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как отладить Go-приложение в продакшн-контейнере на базе Distroless, если в нем нет shell и стандартных утилит (`ps`, `netstat`, `curl` )?»\n**Ответ:** В современной инфраструктуре Kubernetes используется механизм эфемерных контейнеров (`kubectl debug pod-name -it --image=nicolaka/netshoot --target=container-name`). Эфемерный контейнер со всеми сетевыми и отладочными утилитами подключается к тем же пространствам имен (Network, PID, IPC), позволяя исследовать трафик, сокеты и процессы без нарушения иммутабельности и безопасности основного рабочего контейнера."
  },
  {
    "num": 22,
    "title": "BuildKit Secrets: безопасная передача токенов и ключей без утечки в слои",
    "task": "Напиши **Dockerfile с secrets**: `RUN --mount=type=secret,id=github_token cat /run/secrets/github_token`. Используй `docker build --secret id=github_token,env=GITHUB_TOKEN`. Покажи, что secrets не попадают в image layers (безопасно).",
    "theory": "При сборке Go-приложений часто требуется загружать приватные модули из закрытых репозиториев (GitLab, GitHub, Bitbucket).\n\nАнтипаттерны передачи секретов:\n1. `ARG GITHUB_TOKEN`: значение аргумента сборки навсегда сохраняется в метаданных образа (в истории `docker history` и OCI манифесте). Любой пользователь, скачавший образ, может легко прочитать токен!\n2. `COPY id_rsa /root/.ssh/ && go mod download && rm /root/.ssh/id_rsa`: приватный ключ навсегда останется в нижнем слое OverlayFS.\n\nРешение: **BuildKit Secrets Mounts** (`--mount=type=secret,id=...`).\nСекрет монтируется во временную файловую систему в оперативной памяти (tmpfs) по пути `/run/secrets/<id>` **исключительно на время выполнения конкретной команды `RUN`**.\nПосле завершения команды tmpfs размонтируется, и секрет **никогда не сохраняется ни в одном слое или метаданных образа**!",
    "step_by_step": "1. Включите сборщик BuildKit: `export DOCKER_BUILDKIT=1`.\n2. Создайте файл с секретом (например, `token.txt` или переменную окружения).\n3. В `Dockerfile` укажите директиву `RUN --mount=type=secret,id=gh_token ...`.\n4. Соберите образ командой `docker build --secret id=gh_token,src=token.txt -t app-secret:v1 .`.\n5. Проверьте через `docker history app-secret:v1`, что секрет отсутствует в метаданных.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Built securely with BuildKit secrets!\\n\")\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Микросервис"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# syntax=docker/dockerfile:1\nFROM golang:1.24-alpine AS builder\n\nWORKDIR /src\n\n# Безопасное монтирование секрета для авторизации в приватном registry\nRUN --mount=type=secret,id=github_token \\\n    TOKEN=$(cat /run/secrets/github_token) && \\\n    echo \"Simulating secure go mod download with token: ${#TOKEN} chars\" && \\\n    true\n\nCOPY main.go .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /bin/app main.go\n\nFROM scratch\nCOPY --from=builder /bin/app /bin/app\nEXPOSE 8080\nENTRYPOINT [\"/bin/app\"]",
        "note": "Dockerfile с BuildKit secret mount"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Создаем секрет в файле на хосте\necho \"ghp_super_secret_production_token_12345\" > /tmp/gh_token.txt\n\n# Сборка с передачей секрета\nDOCKER_BUILDKIT=1 docker build \\\n  --secret id=github_token,src=/tmp/gh_token.txt \\\n  -t app-secret:v1 .\n\n# Проверяем историю образа — токен нигде не зафиксирован!\ndocker history app-secret:v1\n\n# Удаляем файл секрета с хоста\nrm -f /tmp/gh_token.txt"
      }
    ],
    "under_the_hood": "BuildKit создает защищенный gRPC-канал между клиентом Docker CLI и сборочным демоном. Содержимое секрета передается по TLS в поток демона и монтируется через системный вызов `mount(..., \"tmpfs\", ...)` в каталог `/run/secrets`. При формировании snapshot слоя файловая система tmpfs игнорируется OCI-экспортером.",
    "pitfalls": "1. Запись секрета во временный файл в файловой системе образа: `cat /run/secrets/token > /app/token.txt`. Файл `/app/token.txt` попадет в слой образа!\n2. Использование старого синтаксиса `ARG GITHUB_TOKEN`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему аргумент `ARG` в Dockerfile категорически запрещено использовать для передачи паролей от баз данных, API-токенов или SSH-ключей?»\n**Ответ:** Значения всех `ARG` сохраняются в открытом виде в JSON-метаданных конфигурации образа (в секции `history` и `config.Env`), а также отображаются в выводе команды `docker history --no-trunc <image>`. Любой разработчик или система, имеющая доступ на скачивание образа (`docker pull`), может без труда извлечь все аргументы сборки в открытом виде."
  },
  {
    "num": 23,
    "title": "Кросс-платформенная сборка: Multi-arch образы через Docker Buildx",
    "task": "Собери **cross-platform image**: `docker buildx build --platform linux/amd64,linux/arm64 -t myapp:v1 --push`. Используй `buildx` с QEMU эмуляцией или нативными builder'ами. Покажи multi-arch manifest.",
    "theory": "Современная инфраструктура гетерогенна: разработчики часто работают на MacBook с архитектурой Apple Silicon (**ARM64**), а продакшн-серверы в облаках работают на процессорах Intel/AMD (**AMD64**) или ARM-серверах (AWS Graviton, Яндекс Cloud).\n\nЕсли собрать образ локально на Mac без указания платформы, он не сможет запуститься на сервере Linux x86_64 (`exec format error`).\n\nИнструмент **Docker Buildx** (на базе BuildKit) позволяет собирать кросс-платформенные образы (`Multi-arch images`) для нескольких архитектур одновременно:\n`docker buildx build --platform linux/amd64,linux/arm64 -t myapp:v1 --push .`\n\nБлагодаря компилятору Go, у которого встроенная кросс-компиляция (`GOOS=linux GOARCH=arm64` или `GOARCH=amd64`), сборка под разные платформы выполняется нативно, быстро и не требует медленной эмуляции через QEMU.",
    "step_by_step": "1. Убедитесь в наличии билдера buildx: `docker buildx ls`.\n2. Создайте новый экземпляр билдера: `docker buildx create --use --name mybuilder`.\n3. Опишите `Dockerfile`, использующий автоматические аргументы `TARGETOS` и `TARGETARCH`.\n4. Соберите multi-arch манифест под `linux/amd64` и `linux/arm64`.\n5. Проинспектируйте сформированный манифест через `docker buildx imagetools inspect`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"runtime\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Multi-arch Go App running on: %s/%s\\n\", runtime.GOOS, runtime.GOARCH)\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис, сообщающий архитектуру процессора"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# Автоматические аргументы платформы, передаваемые buildx\nFROM --platform=$BUILDPLATFORM golang:1.24-alpine AS builder\n\nARG TARGETOS\nARG TARGETARCH\n\nWORKDIR /src\nCOPY main.go .\n\n# Нативная быстрая кросс-компиляция средствами самого Go без QEMU эмуляции!\nRUN CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH go build \\\n    -ldflags=\"-w -s\" \\\n    -o /bin/app main.go\n\nFROM scratch\nCOPY --from=builder /bin/app /bin/app\nEXPOSE 8080\nENTRYPOINT [\"/bin/app\"]",
        "note": "Кросс-платформенный Dockerfile с поддержкой TARGETARCH"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Создание билдера\ndocker buildx create --use --name multi-arch-builder\n\n# Инициализация\ndocker buildx inspect --bootstrap\n\n# Сборка под amd64 и arm64 (эмуляция или нативный тулчейн Go)\ndocker buildx build --platform linux/amd64,linux/arm64 -t test-multiarch:v1 .\n\n# Проверка поддерживаемых платформ\ndocker buildx ls"
      }
    ],
    "under_the_hood": "В реестре Docker (Registry) multi-arch образ хранится в виде Manifest List (OCI Index). Это JSON-документ со списком дайджестов для конкретных архитектур (`os: linux, architecture: amd64` и `architecture: arm64`). Когда нода Kubernetes выполняет `docker pull`, контейнерный демон считывает архитектуру хостового процессора и скачивает только подходящий бинарный образ.",
    "pitfalls": "1. Сборка CGO-кода под другую архитектуру: требуется кросс-компилятор GCC (`aarch64-linux-gnu-gcc`), иначе сборка завершится сбоем.\n2. Попытка сохранить мультиархитектурный образ локально в Docker daemon через `docker buildx build --load` (Docker daemon не поддерживает одновременное хранение Manifest List нескольких платформ под одним тегом; используйте `--push`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему директива `FROM --platform=$BUILDPLATFORM golang:...` в сочетании с `GOARCH=$TARGETARCH` собирает образы под ARM64/AMD64 в 10 раз быстрее, чем стандартный `docker buildx build`?»\n**Ответ:** Стандартный buildx запускает весь контейнер сборки под эмуляцией QEMU (инструкции x86 эмулируются на ARM программно). Директива `FROM --platform=$BUILDPLATFORM` запускает компилятор Go нативно на архитектуре хоста билдера на полной скорости CPU, а компилятор Go сам создает целевой машинный код под `$TARGETARCH`, так как Go изначально поддерживает кросс-компиляцию из коробки."
  },
  {
    "num": 24,
    "title": "Оптимизация кэша слоев: изоляция go.mod/go.sum от исходного кода",
    "task": "Оптимизируйте кэш Docker-слоёв: скопируйте сначала `go.mod` и `go.sum`, сделайте `go mod download`, затем копируйте остальной код. Теперь изменения в коде не будут вызывать перекачку зависимостей.",
    "theory": "При проектировании эффективного `Dockerfile` критически важно понимать жизненный цикл изменений в кодовой базе:\n- **Исходный код (`*.go`):** меняется разработчиками десятки раз в день (каждый коммит, фикс бага или новая фича).\n- **Внешние зависимости (`go.mod` и `go.sum`):** меняются редко (раз в несколько дней или недель).\n\nЕсли обе группы файлов копируются одновременно:\n`COPY . .`\nто любое редактирование исходников приводит к инвалидации слоя кэша с `COPY`, заставляя Docker повторно выполнять `RUN go mod download`.\n\nПравильная стратегия изоляции слоев:\n1. `COPY go.mod go.sum ./` — копируются только файлы с перечнем зависимостей.\n2. `RUN go mod download` — зависимости скачиваются и фиксируются в отдельном слое кэша.\n3. `COPY . .` — копируется остальной код проекта.\n4. `RUN go build ...` — быстрая компиляция приложения.\n\nБлагодаря этому время пересборки при изменении кода сокращается с минут до **1–3 секунд**!",
    "step_by_step": "1. Создайте проект с модулями и несколькими зависимостями.\n2. Опишите правильный порядок команд в `Dockerfile`.\n3. Соберите образ `app:v1`.\n4. Внесите правку в комментарий `main.go`.\n5. Соберите `app:v2` и обратите внимание на вывод `CACHED` у директивы `RUN go mod download`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"Fast cached layer build!\")\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Исходный код микросервиса"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\n\nWORKDIR /app\n\n# 1. Копируем только файлы манифеста зависимостей\nCOPY go.mod go.sum* ./\n\n# 2. Скачиваем библиотеки в изолированный кэшируемый слой\nRUN go mod download\n\n# 3. Копируем исходники (кэш шага 2 НЕ инвалидируется при изменении кода!)\nCOPY . .\n\n# 4. Компилируем бинарник\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /app/server main.go\n\nFROM alpine:3.20\nCOPY --from=builder /app/server /app/server\nENTRYPOINT [\"/app/server\"]",
        "note": "Эталонная структура кэширования слоев"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Первая сборка (скачивание зависимостей)\ndocker build -t app-cache-demo:v1 .\n\n# Меняем исходный код\necho \"// minor change\" >> main.go\n\n# Вторая сборка — шаг скачивания берется из кэша мгновенно!\ndocker build -t app-cache-demo:v2 ."
      }
    ],
    "under_the_hood": "Послойная файловая система UnionFS/OverlayFS сравнивает хеш-суммы файлов. Шаг 1 зависит исключительно от содержимого `go.mod` и `go.sum`. Пока контрольные суммы sha256 этих файлов идентичны, Docker пропускает выполнение шага 2 и берет готовый снимок файловой системы из кэша слоев.",
    "pitfalls": "1. Использование маски `COPY *.go .` до `go mod download`.\n2. Изменение форматирования в `go.mod`, которое меняет его sha256 и непреднамеренно инвалидирует кэш.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в директиве `COPY go.mod go.sum* ./` рекомендуется ставить звездочку `*` у файла `go.sum`?»\n**Ответ:** Если проект абсолютно новый или не имеет внешних сторонних библиотек, файл `go.sum` может физически отсутствовать в репозитории. Инструкция `COPY go.mod go.sum ./` в таком случае завершится ошибкой сборки `file not found`. Использование glob-паттерна `go.sum*` делает наличие файла опциональным: Docker скопирует его, если он существует, и не упадет с ошибкой, если его нет."
  },
  {
    "num": 25,
    "title": "Статическая линковка и чистый scratch: размер образа равен размеру бинарника",
    "task": "**Статическая линковка и `scratch`**: Alpine Linux — это здорово, но образ `scratch` (абсолютно пустой образ) — еще лучше. В этапе сборки укажи `CGO_ENABLED=0 GOOS=linux go build -o app .`. На втором этапе используй `FROM scratch` и скопируй бинарник. Теперь твой Docker-образ весит ровно столько же, сколько сам бинарный файл (около 10 МБ).",
    "theory": "Образ `scratch` позволяет достичь физического предела минимализма в контейнеризации: **размер Docker-образа становится в точности равен размеру скомпилированного Go-бинарника (около 8–12 МБ)**.\n\nДля этого компилятору Go передаются ключевые параметры:\n1. `CGO_ENABLED=0`: полное отключение CGO и использование встроенных Go-пакетов без внешних зависимостей.\n2. `GOOS=linux`: целевая операционная система Linux.\n3. `-ldflags=\"-w -s\"`: удаление отладочных DWARF таблиц и символов.\n\nПолученный ELF-бинарник запускается непосредственно ядром Linux в изолированном пространстве имен контейнера без каких-либо посредников.",
    "step_by_step": "1. Напишите легковесный веб-сервис на Go.\n2. Создайте `Dockerfile` с этапом сборщика и финальным образом `scratch`.\n3. Скомпилируйте бинарник со всеми оптимизациями статической линковки.\n4. Проверьте размер получившегося Docker-образа через `docker images`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Zero-overhead Go container on pure scratch!\\n\")\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Легковесный сервис"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\n\nWORKDIR /src\nCOPY main.go .\n\n# Полностью статическая сборка со сжатием\nRUN CGO_ENABLED=0 GOOS=linux go build \\\n    -a -installsuffix cgo \\\n    -ldflags=\"-w -s\" \\\n    -o /bin/app main.go\n\n# Финальный образ scratch (0 байт)\nFROM scratch\n\n# Единственный файл в контейнере\nCOPY --from=builder /bin/app /app\n\nEXPOSE 8080\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile с нулевым оверхедом scratch"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t app-ultra-scratch:latest .\n\n# Размер образа (ровно ~6 MB)\ndocker images app-ultra-scratch:latest\n\n# Проверка работоспособности\ndocker run -d -p 8080:8080 --name test-us app-ultra-scratch:latest\ncurl http://localhost:8080\ndocker rm -f test-us"
      }
    ],
    "under_the_hood": "Такой образ содержит ровно 1 слой в файловой системе OverlayFS, в котором записан единственный inode исполняемого файла. Запуск контейнера в Linux cgroups не требует инициализации init-систем и происходит мгновенно.",
    "pitfalls": "1. Попытка использования утилиты `sh` внутри контейнера (например, `docker exec -it <container> sh`) вызовет ошибку, так как в scratch нет никаких шеллов.\n2. Необходимость настройки прав доступа и файлов конфигурации, если приложению требуется доступ к файловой системе.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы преимущества и недостатки полного перехода всех Go-микросервисов компании на `FROM scratch`?»\n**Ответ:** Преимущества: минимальный вес образов (быстрый деплой), минимальное потребление дискового пространства нод, 0 уязвимостей в ОС (CVE), высокая безопасность. Недостатки: отсутствие шелла затрудняет экстренную отладку на stage-стендах, необходимость вручную заботиться о корневых сертификатах TLS (`ca-certificates.crt`) и базе временных зон (`tzdata`), невозможность использования сторонних CLI-утилит внутри контейнера."
  },
  {
    "num": 26,
    "title": "Кэширование модулей Go: секреты оптимизации времени CI/CD сборок",
    "task": "**[Кэширование модулей]**: Оптимизируй Dockerfile: скопируй сначала только `go.mod` и `go.sum`, выполни `go mod download`, и только потом копируй остальной код. Убедись, что при изменении кода этап `download` берется из кэша.",
    "theory": "При частых сборках в конвейерах непрерывной интеграции (GitLab CI, GitHub Actions, Jenkins) время скачивания зависимостей Go может составлять до 80% всего времени билда.\n\nСтратегия максимального ускорения включает:\n1. Раздельное копирование манифеста зависимостей.\n2. Использование переменной `GOPROXY` (например, корпоративный Nexus / Artifactory или публичный `https://proxy.golang.org,direct`).\n3. Использование команды `go mod download -x` для верификации загружаемых архивов.\n\nБлагодаря правильному разделению, билд-агенты CI переиспользуют закэшированные слои Docker Registry, сводя операцию загрузки зависимостей к нулевому времени.",
    "step_by_step": "1. Подготовьте проект с несколькими внешними библиотеками.\n2. Настройте `Dockerfile` с оптимальным кэшированием модулей.\n3. Продемонстрируйте время сборки с кэшем и без кэша.",
    "code_blocks": [
      {
        "filename": "go.mod",
        "lang": "go",
        "code": "module example.com/fastcache\n\ngo 1.24\n\nrequire (\n\tgithub.com/google/uuid v1.6.0\n\tgolang.org/x/sync v0.10.0\n)\n",
        "note": "Файл модулей с зависимостями"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\n\nWORKDIR /workspace\n\n# Переменные проксирования для стабильности загрузки модулей\nENV GOPROXY=https://proxy.golang.org,direct\n\n# Копируем исключительно метаданные модулей\nCOPY go.mod go.sum ./\nRUN go mod download\n\n# Копируем код\nCOPY . .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /bin/service .\n\nFROM alpine:3.20\nCOPY --from=builder /bin/service /service\nENTRYPOINT [\"/service\"]",
        "note": "Dockerfile с оптимизированным кэшированием модулей"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка с замером времени\ntime docker build -t test-mod-cache:v1 .\n\n# Повторная сборка без изменения зависимостей (время < 1 сек)\ntime docker build -t test-mod-cache:v2 ."
      }
    ],
    "under_the_hood": "Команда `go mod download` загружает zip-архивы модулей в каталог `$GOPATH/pkg/mod/cache/download` и проверяет их контрольные суммы по `go.sum`. После завершения этого шага слой фиксируется. Даже если в проекте изменяется логика бизнес-функций в `main.go`, кэшированный каталог `$GOPATH/pkg/mod` сохраняется в локальном графе слоев Docker.",
    "pitfalls": "1. Вызов `RUN go get ./...` вместо `RUN go mod download`: `go get` пытается компилировать пакеты, для чего требуются исходные файлы проекта, которые еще не скопированы.\n2. Несоответствие хэшей в `go.sum` и `go.mod`.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем разница между командами `go mod download` и `go mod vendor` в контексте контейнеризации?»\n**Ответ:** `go mod download` скачивает модули в глобальный кэш `$GOPATH/pkg/mod` в виде сжатых zip-архивов. `go mod vendor` копирует исходные коды всех внешних зависимостей напрямую в локальную директорию `vendor/` проекта. Если проект использует vendor-режим (`go build -mod=vendor`), скачивать зависимости из сети в Dockerfile не требуется вовсе — достаточно скопировать локальную папку `vendor/`, что гарантирует полностью оффлайновую сборку."
  },
  {
    "num": 27,
    "title": "Оптимизация слоев образа: объединение команд RUN и минимизация размера",
    "task": "Оптимизируй **image layers**: минимизируй количество `RUN` команд (но не жертвуй читаемостью). Используй `&&` для объединения. Покажи `docker history myapp:v1` — каждый слой добавляет размер.",
    "theory": "Каждая инструкция `RUN`, `COPY` и `ADD` в `Dockerfile` создает новый физический слой в файловой системе OverlayFS.\n\nАнтипаттерн создания мусорных слоев:\n```dockerfile\nRUN apk update\nRUN apk add curl\nRUN rm -rf /var/cache/apk/*\n```\nВ этой конфигурации создаются **3 отдельных слоя**.\nПакеты, установленные в слое 2, физически останутся в tar-архиве слоя 2! Команда `rm` в слое 3 лишь создаст whiteout-записи, скрывающие файлы, но **не уменьшит размер образа ни на байт**.\n\nПаттерн оптимизации (Layer Flattening):\nКоманды обновления, установки и немедленной очистки кэша объединяются через логический оператор `&&` в рамках одного шага `RUN`:\n```dockerfile\nRUN apk update && \\\n    apk add --no-cache ca-certificates tzdata && \\\n    rm -rf /var/cache/apk/*\n```\nЭто гарантирует, что временные файлы и индексы удаляются ДО фиксации слоя на диске.",
    "step_by_step": "1. Напишите неоптимальный Dockerfile с несколькими командами `RUN`.\n2. Напишите оптимизированный Dockerfile с объединенным `RUN`.\n3. Соберите оба образа и сравните послойную историю через `docker history`.",
    "code_blocks": [
      {
        "filename": "Dockerfile.bad",
        "lang": "dockerfile",
        "code": "FROM alpine:3.20\n# Плохой подход: создает 3 слоя, временные файлы зафиксированы в слое 2\nRUN apk update\nRUN apk add curl\nRUN rm -rf /var/cache/apk/*",
        "note": "Неоптимальный Dockerfile с раздутыми слоями"
      },
      {
        "filename": "Dockerfile.good",
        "lang": "dockerfile",
        "code": "FROM alpine:3.20\n# Хороший подход: все выполняется в одном слое с немедленной очисткой\nRUN apk add --no-cache curl ca-certificates",
        "note": "Оптимизированный Dockerfile с чистым слоем"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка обоих образов\ndocker build -f Dockerfile.bad -t test-layers:bad .\ndocker build -f Dockerfile.good -t test-layers:good .\n\n# Сравнение послойного размера\ndocker history test-layers:bad\ndocker history test-layers:good"
      }
    ],
    "under_the_hood": "OverlayFS фиксирует состояние верхнего каталога `upperdir` только в момент завершения выполнения текущей директивы `RUN`. Если файл был создан и удален в рамках одной bash-сессии, он никогда не будет записан в результирующий diff-архив слоя.",
    "pitfalls": "1. Чрезмерное объединение команд в ущерб читаемости Dockerfile.\n2. Пропуск флага `--no-cache` в пакетном менеджере `apk` (Alpine) или отсутствие очистки `/var/lib/apt/lists/*` в Debian/Ubuntu.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему удаление временных файлов сборщика в отдельной инструкции `RUN rm -rf ...` не уменьшает размер итогового Docker-образа?»\n**Ответ:** Слои в Docker иммутабельны (неизменяемы). Каждый слой хранит только дельту (diff) относительно предыдущего. Если файл был записан в слое N, он физически присутствует в архиве слоя N. Инструкция `RUN rm` в слое N+1 лишь помещает специальную метку whiteout в слой N+1, скрывающую файл при монтировании файловой системы, но общий вес контейнера увеличивается на размер самого слоя N+1."
  },
  {
    "num": 28,
    "title": "Практика .dockerignore: исключение .git, vendor и тестовых файлов",
    "task": "Используйте `.dockerignore` для исключения `.git`, `vendor`, `*.md`, `tests` из контекста сборки.",
    "theory": "Файл `.dockerignore` является первичным рубежом защиты и оптимизации сборок.\n\nЧто необходимо исключать в Go-проектах:\n1. `.git`: предотвращает утечку истории коммитов, веток и авторских метаданных.\n2. `vendor`: если проект использует стандартное скачивание модулей через `go mod download`, локальная папка `vendor/` не должна замусоривать контекст сборки.\n3. `*_test.go` и каталоги тестов `tests/`: тесты выполняются на этапе CI-тестирования, их присутствие в продакшн-образе избыточно.\n4. Документация (`*.md`, `docs/`) и файлы локального окружения (`.env`, `docker-compose.yml`).\n\nЭто гарантирует воспроизводимость сборки независимо от состояния рабочей копии разработчика.",
    "step_by_step": "1. Создайте файл `.dockerignore` в корне проекта.\n2. Добавьте правила исключения для тестов, документации и истории Git.\n3. Запустите сборку и проверьте содержимое контекста сборки.",
    "code_blocks": [
      {
        "filename": ".dockerignore",
        "lang": "dockerignore",
        "code": "# Системы контроля версий\n.git/\n.gitignore\n\n# Документация и диаграммы\n*.md\ndocs/\n\n# Тесты и тестовые моки\n*_test.go\ntests/\nmocks/\n\n# Секреты и конфиги\n.env*\nconfig.local.yaml\n\n# Локальные бинарники и артефакты\nbin/\n*.out\n*.exe\nvendor/",
        "note": "Файл .dockerignore для Go проекта"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /app\nCOPY . .\nRUN CGO_ENABLED=0 go build -o /app/bin main.go\n\nFROM scratch\nCOPY --from=builder /app/bin /app\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Создадим тестовый файл, который должен игнорироваться\ntouch server_test.go README.md\n\n# Сборка\ndocker build -t test-ignore-demo:latest .\n\n# Очистка\nrm -f server_test.go README.md"
      }
    ],
    "under_the_hood": "Парсер клиента Docker фильтрует локальные файлы по glob-шаблонам перед передачей в tar-архиватор. Исключенные файлы даже не считываются с диска файловой системы хоста, сохраняя ресурсы I/O диска.",
    "pitfalls": "1. Случайное добавление в `.dockerignore` файлов, необходимых для сборки (например, файлов шаблонов HTML или SQL-миграций, встроенных через `embed`).\n2. Ошибки в синтаксисе путей (например, `/vendor` вместо `vendor/`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Что произойдет, если в `.dockerignore` случайно добавить шаблоны `*.sql`, а в Go коде используется директива `//go:embed queries/*.sql`?»\n**Ответ:** Команда `COPY . .` не скопирует файлы `*.sql` в образ сборщика. При выполнении `go build` компилятор Go выдаст фатальную ошибку сборки вида `pattern queries/*.sql: no matching files found`, так как файлы были отфильтрованы на этапе формирования контекста сборки."
  },
  {
    "num": 29,
    "title": "Docker Compose: локальное окружение для разработки (Go, Postgres, Redis, Jaeger)",
    "task": "Напиши **docker-compose.yml** для локальной разработки: `app` (Go, hot reload через `air` или `fresh`), `postgres`, `redis`, `jaeger`. Volumes: `./:/app` для live code sync. Networks: `backend`. Покажи `docker-compose up`.\n\n---",
    "theory": "В микросервисной архитектуре Go-сервисы редко работают изолированно. Для полноценной локальной разработки требуется комплексное окружение:\n- **База данных:** PostgreSQL с персистентным хранением данных (Named Volume).\n- **Кэш / Очереди:** Redis.\n- **Распределенная трассировка:** Jaeger All-In-One.\n- **Go-сервис:** с возможностью быстрой компиляции или hot-reload.\n\nИнструмент **Docker Compose** декларативно описывает всю топологию сервисов, их порты, переменные окружения, сетевое взаимодействие и тома в едином файле `docker-compose.yml`.\n\nКонтейнеры внутри одного Compose-проекта автоматически объединяются в общую изолированную сеть `bridge` и могут обращаться друг к другу по именам сервисов (`postgres:5432`, `redis:6379`, `jaeger:4317`) благодаря встроенному DNS-серверу Docker.",
    "step_by_step": "1. Напишите микросервис на Go, подключающийся к PostgreSQL, Redis и отправляющий трейсы в Jaeger.\n2. Создайте `docker-compose.yml`, декларирующий 4 сервиса (`app`, `postgres`, `redis`, `jaeger`).\n3. Настройте монтирование именованного тома `postgres_data` для персистентности данных БД.\n4. Запустите стек командой `docker compose up -d`.\n5. Проверьте логи сервисов через `docker compose logs -f`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\tdbHost := os.Getenv(\"DB_HOST\")\n\tredisHost := os.Getenv(\"REDIS_HOST\")\n\tjaegerHost := os.Getenv(\"JAEGER_HOST\")\n\n\thttp.HandleFunc(\"/status\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Service OK! DB: %s, Redis: %s, Jaeger: %s\\n\", dbHost, redisHost, jaegerHost)\n\t})\n\n\tlog.Println(\"Microservice stack starting on :8080...\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Go микросервис с конфигурацией из ENV"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /app\nCOPY main.go .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /bin/app main.go\n\nFROM alpine:3.20\nWORKDIR /app\nCOPY --from=builder /bin/app /app/app\nEXPOSE 8080\nENTRYPOINT [\"/app/app\"]",
        "note": "Dockerfile сервиса"
      },
      {
        "filename": "docker-compose.yml",
        "lang": "yaml",
        "code": "services:\n  app:\n    build: .\n    container_name: go_workout_app\n    ports:\n      - \"8080:8080\"\n    environment:\n      - DB_HOST=postgres:5432\n      - REDIS_HOST=redis:6379\n      - JAEGER_HOST=jaeger:4318\n    depends_on:\n      - postgres\n      - redis\n    restart: unless-stopped\n\n  postgres:\n    image: postgres:16-alpine\n    container_name: go_workout_pg\n    environment:\n      POSTGRES_USER: devuser\n      POSTGRES_PASSWORD: devpassword\n      POSTGRES_DB: devdb\n    ports:\n      - \"5432:5432\"\n    volumes:\n      - pg_data:/var/lib/postgresql/data\n    restart: unless-stopped\n\n  redis:\n    image: redis:7-alpine\n    container_name: go_workout_redis\n    ports:\n      - \"6379:6379\"\n    restart: unless-stopped\n\n  jaeger:\n    image: jaegertracing/all-in-one:1.57\n    container_name: go_workout_jaeger\n    ports:\n      - \"16686:16686\" # Web UI\n      - \"4318:4318\"   # OTLP HTTP\n    restart: unless-stopped\n\nvolumes:\n  pg_data:",
        "note": "docker-compose.yml для полного стека разработки"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск всех сервисов в фоновом режиме\ndocker compose up -d\n\n# Проверка запущенных контейнеров\ndocker compose ps\n\n# Проверка эндпоинта приложения\ncurl http://localhost:8080/status\n\n# Просмотр логов приложения\ndocker compose logs app\n\n# Остановка стека с сохранением данных в volume\ndocker compose down"
      }
    ],
    "under_the_hood": "Docker Compose создает кастомную сеть bridge (например, `project_default`). Встроенный DNS-сервер Docker (доступный внутри каждого контейнера по адресу `127.0.0.11:53`) автоматически резолвит имя `postgres` в приватный IP-адрес соответствующего контейнера.",
    "pitfalls": "1. Обращение из одного контейнера к другому через `localhost`: внутри контейнера `localhost` указывает на сам контейнер, а не на хост или соседний сервис.\n2. Отсутствие именованных томов (`volumes: pg_data`): при перезапуске контейнера базы данных все таблицы и данные будут стерты.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в микросервисах внутри Docker Compose обращение к PostgreSQL по адресу `localhost:5432` приводит к ошибке `connection refused`?»\n**Ответ:** Каждый контейнер по умолчанию имеет собственное изолированное сетевое пространство имен (Network Namespace) и собственный интерфейс loopback `lo`. Адрес `localhost:5432` указывает внутрь самого контейнера Go-приложения, где сервер PostgreSQL не запущен. Для сетевого взаимодействия между контейнерами необходимо использовать имя сервиса (`postgres:5432`), которое встроенный DNS Docker резолвит в IP-адрес контейнера базы данных."
  },
  {
    "num": 30,
    "title": "Build-time переменные (ARG) и инъекция версии через ldflags",
    "task": "**Build-time variables**: Передавайте Git commit hash и версию через `--build-arg` и `ldflags`: `RUN go build -ldflags=\"-X main.version=${VERSION} -X main.commit=${COMMIT}\"`.",
    "theory": "В продакшн-эксплуатации критически важно точно знать, какая версия кода, коммит и дата сборки исполняются в запущенном контейнере.\n\nМеханизм внедрения метаданных сборки:\n1. В `Dockerfile` объявляются аргументы сборки:\n   `ARG VERSION=dev`\n   `ARG COMMIT=none`\n   `ARG BUILD_TIME=unknown`\n2. Линковщик Go (`go tool link`) поддерживает флаг `-X <package>.<variable>=<value>`, который динамически перезаписывает строковые переменные пакета прямо в бинарном коде во время сборки без изменения исходных файлов.\n3. Команда компиляции:\n   `RUN go build -ldflags=\"-X main.Version=${VERSION} -X main.Commit=${COMMIT} -X main.BuildTime=${BUILD_TIME}\"`\n\nПри запуске `docker build --build-arg VERSION=v1.2.3 --build-arg COMMIT=$(git rev-parse --short HEAD) ...` значения из Git автоматически внедряются в скомпилированный бинарник.",
    "step_by_step": "1. Объявите строковые переменные `Version`, `Commit`, `BuildTime` в пакете `main`.\n2. Создайте эндпоинт `/version`, возвращающий эти данные в формате JSON.\n3. В `Dockerfile` настройте директивы `ARG` и проброс через `-ldflags`.\n4. Соберите образ с передачей параметров `--build-arg`.\n5. Убедитесь, что приложение корректно сообщает свою версию.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"log\"\n\t\"net/http\"\n)\n\n// Переменные, перезаписываемые компилятором через -ldflags -X\nvar (\n\tVersion   = \"dev\"\n\tCommit    = \"none\"\n\tBuildTime = \"unknown\"\n)\n\ntype BuildInfo struct {\n\tVersion   string `json:\"version\"`\n\tCommit    string `json:\"commit\"`\n\tBuildTime string `json:\"build_time\"`\n}\n\nfunc main() {\n\thttp.HandleFunc(\"/version\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\t_ = json.NewEncoder(w).Encode(BuildInfo{\n\t\t\tVersion:   Version,\n\t\t\tCommit:    Commit,\n\t\t\tBuildTime: BuildTime,\n\t\t})\n\t})\n\n\tlog.Printf(\"Starting application version: %s (commit: %s)\\n\", Version, Commit)\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис с динамически внедряемыми метаданными сборки"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\n\n# Аргументы времени сборки\nARG VERSION=dev\nARG COMMIT=none\nARG BUILD_TIME=unknown\n\nWORKDIR /src\nCOPY main.go .\n\n# Инъекция значений аргументов в переменные пакета main\nRUN CGO_ENABLED=0 GOOS=linux go build \\\n    -ldflags=\"-w -s \\\n      -X 'main.Version=${VERSION}' \\\n      -X 'main.Commit=${COMMIT}' \\\n      -X 'main.BuildTime=${BUILD_TIME}'\" \\\n    -o /bin/app main.go\n\nFROM scratch\nCOPY --from=builder /bin/app /bin/app\nEXPOSE 8080\nENTRYPOINT [\"/bin/app\"]",
        "note": "Dockerfile с поддержкой ARG и инъекции ldflags"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка образа с передачей версии и коммита\ndocker build \\\n  --build-arg VERSION=v2.4.1 \\\n  --build-arg COMMIT=a7f83b1 \\\n  --build-arg BUILD_TIME=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \\\n  -t app-versioned:v2.4.1 .\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-ver app-versioned:v2.4.1\n\n# Проверка ответа (вернет JSON с внедренными параметрами)\ncurl -s http://localhost:8080/version\n\n# Очистка\ndocker rm -f test-ver"
      }
    ],
    "under_the_hood": "Линковщик Go на этапе создания таблицы данных инициализации ELF-файла заменяет адреса памяти строковых литералов указанных глобальных переменных на переданные константы. Переменная обязана иметь строковый тип (`string`), иначе линковщик проигнорирует флаг `-X`.",
    "pitfalls": "1. Попытка переопределить нестроковую переменную (например, `int`): линковщик выдаст ошибку `cannot set with -X: not a string variable`.\n2. Опечатка в имени пакета: если переменная находится в пакете `internal/version`, флаг должен быть `-X 'myproject/internal/version.Version=...'`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы ограничения флага `-X` линковщика Go при внедрении метаданных в бинарник?»\n**Ответ:** 1) Флаг `-X` может перезаписывать значения только глобальных переменных строкового типа (`string`). Переменные других типов (`int`, `bool`, структуры) перезаписать нельзя. 2) Переменные должны быть объявлены через `var`, а не как константы `const`. 3) Требуется указывать полный путь к пакету относительно модуля (например, `-X 'example.com/mod/pkg/buildinfo.Version=1.0.0'`)."
  },
  {
    "num": 31,
    "title": "Сетевое взаимодействие: пользовательские Docker-сети и внутренний DNS",
    "task": "Настрой **Docker network**: `docker network create mynet`. Запусти `app` и `postgres` в одной сети. Обращайся по имени контейнера: `postgres:5432`. Покажи DNS resolution в Docker.",
    "theory": "Docker поддерживает несколько драйверов сетей:\n1. `bridge`: виртуальный мост (драйвер по умолчанию).\n2. `host`: отключение сетевой изоляции (контейнер использует сетевой стек хоста).\n3. `none`: полное отключение сети у контейнера.\n4. `overlay`: многохостовая сеть (Swarm/Kubernetes).\n\nКритическое отличие стандартного bridge (`docker0`) от пользовательской сети (`user-defined bridge`):\n- В стандартной сети bridge **внутренний DNS-резолвинг имен контейнеров ОТКЛЮЧЕН** (обращение возможно только по IP-адресам или устаревшим `--link`).\n- В пользовательской сети (`docker network create mynet`) **автоматический DNS-резолвинг включен по умолчанию**. Контейнеры мгновенно находят друг друга по имени контейнера (`container_name`).",
    "step_by_step": "1. Создайте изолированную сеть: `docker network create mynet`.\n2. Запустите контейнер базы данных в этой сети с именем `postgres-db`.\n3. Запустите Go-сервис в той же сети.\n4. Убедитесь, что Go-сервис успешно разрешает имя `postgres-db` через DNS.\n5. Проинспектируйте сеть через `docker network inspect mynet`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\ttargetHost := os.Getenv(\"TARGET_HOST\")\n\tif targetHost == \"\" {\n\t\ttargetHost = \"db-server\"\n\t}\n\n\thttp.HandleFunc(\"/resolve\", func(w http.ResponseWriter, r *http.Request) {\n\t\tips, err := net.LookupIP(targetHost)\n\t\tif err != nil {\n\t\t\thttp.Error(w, fmt.Sprintf(\"DNS Lookup Failed for %s: %v\", targetHost, err), http.StatusInternalServerError)\n\t\t\treturn\n\t\t}\n\n\t\tfmt.Fprintf(w, \"DNS Resolved successfully! Host: %s, IPs: %v\\n\", targetHost, ips)\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис, выполняющий DNS-резолвинг имени соседнего контейнера"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -o /bin/app main.go\n\nFROM alpine:3.20\nCOPY --from=builder /bin/app /app\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Создаем пользовательскую сеть\ndocker network create mynet\n\n# Запускаем фиктивный сервер базы данных с именем 'db-server'\ndocker run -d --name db-server --network mynet alpine:3.20 sleep 3600\n\n# Собираем и запускаем наше Go приложение в сети mynet\ndocker build -t app-net:latest .\ndocker run -d -p 8080:8080 --name test-app --network mynet -e TARGET_HOST=db-server app-net:latest\n\n# Проверяем DNS-резолвинг\ncurl http://localhost:8080/resolve\n\n# Очистка\ndocker rm -f test-app db-server\ndocker network rm mynet"
      }
    ],
    "under_the_hood": "При создании пользовательской сети Docker запускает встроенный DNS-резолвер на виртуальном IP `127.0.0.11`. В контейнере в файле `/etc/resolv.conf` прописывается `nameserver 127.0.0.11`. Любой DNS-запрос перехватывается демоном Docker: если имя совпадает с именем контейнера в сети, возвращается его IP в подсети моста.",
    "pitfalls": "1. Запуск контейнеров в разных сетях: если `app` находится в `net1`, а `db` в `net2`, они не смогут связаться без явного подключения контейнера ко второй сети (`docker network connect`).\n2. Попытка использования имен контейнеров в стандартной сети по умолчанию (`bridge`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в стандартной сети Docker `bridge` (по умолчанию) контейнеры не могут обращаться друг к другу по имени, а в сети `docker network create` — могут?»\n**Ответ:** В сети по умолчанию `bridge` (docker0) для сохранения обратной совместимости со старыми версиями Docker (до 1.10) встроенный embedded DNS-сервер отключен. В ней резолвинг имен работал только через статический файл `/etc/hosts` и устаревший флаг `--link`. Во всех пользовательских сетях (`user-defined networks`) встроенный DNS-сервер `127.0.0.11` активен всегда и динамически обновляет записи при добавлении/удалении контейнеров."
  },
  {
    "num": 32,
    "title": "Непривилегированный пользователь nonroot:nonroot (UID 65532) в Distroless",
    "task": "Запускайте контейнер от непривилегированного пользователя: `USER nonroot:nonroot` (в distroless это пользователь 65532).",
    "theory": "В Google Distroless предусмотрен зарезервированный непривилегированный системный пользователь **`nonroot`** с идентификатором **UID 65532** и группой **GID 65532**.\n\nИспользование директивы:\n`USER nonroot:nonroot` (или `USER 65532:65532`)\nгарантирует:\n1. Процесс исполняется без root-полномочий внутри пространства имен.\n2. Файловая система хоста защищена: даже если бинарник скомпрометирован, он не имеет прав на запись в системные каталоги.\n3. Полное соответствие требованиям Kubernetes Security Context:\n```yaml\nsecurityContext:\n  runAsNonRoot: true\n  runAsUser: 65532\n```",
    "step_by_step": "1. Напишите Go-сервер.\n2. В `Dockerfile` используйте базовый образ `gcr.io/distroless/static-debian12`.\n3. Задайте директиву `USER nonroot:nonroot`.\n4. Соберите и запустите контейнер.\n5. Проверьте реальный UID запущенного процесса.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/user\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Running securely! UID: %d, GID: %d\\n\", os.Getuid(), os.Getgid())\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис для проверки UID"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -ldflags=\"-w -s\" -o /bin/app main.go\n\nFROM gcr.io/distroless/static-debian12\nCOPY --from=builder /bin/app /app\n\n# Стандартный непривилегированный пользователь в Distroless\nUSER nonroot:nonroot\n\nEXPOSE 8080\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile с пользователем nonroot:nonroot"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t app-nonroot-distro:latest .\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-nrd app-nonroot-distro:latest\n\n# Проверка (вернет UID: 65532, GID: 65532)\ncurl http://localhost:8080/user\n\n# Очистка\ndocker rm -f test-nrd"
      }
    ],
    "under_the_hood": "В образе Distroless файл `/etc/passwd` содержит единственную строку:\n`nonroot:x:65532:65532:nonroot:/home/nonroot:/sbin/nologin`.\nКогда OCI runtime вызывает `setuid(65532)`, ядро сбрасывает все маски привилегий `cap_permitted`, `cap_effective` и `cap_inheritable` в 0.",
    "pitfalls": "1. Попытка слушать порт 80 или 443: порты ниже 1024 зарезервированы для root в Linux.\n2. Необходимость записи временных файлов: каталог `/tmp` должен иметь права `chmod 1777`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Kubernetes манифестах рекомендуется указывать числовой ID `runAsUser: 65532`, а не строковое имя `runAsUser: nonroot`?»\n**Ответ:** Kubelet и рантайм контейнеров (containerd) должны иметь возможность валидировать политики безопасности (Pod Security Standards) ДО монтирования и парсинга файловой системы контейнера. Если в манифесте указана строка `nonroot`, рантайм вынужден лезть внутрь rootfs контейнера и читать `/etc/passwd`, что ненадежно и уязвимо к подмене. Числовой UID валидируется ядром Linux нативно и однозначно."
  },
  {
    "num": 33,
    "title": "Каверзный кейс CGO: сборка с SQLite, статическая линковка и конфликт musl/glibc",
    "task": "**[Каверзный кейс — CGO]**: Включи CGO в своем коде (например, используй `github.com/mattn/go-sqlite3`). Попробуй запустить бинарник, собранный в `golang:alpine`, в `FROM scratch`. Поймай ошибку динамического линковера (libc). Исправь, включив `CGO_ENABLED=0` или использовав `alpine` как runner.",
    "theory": "Большинство Go-приложений компилируются с `CGO_ENABLED=0`. Однако при использовании библиотек, содержащих код на C/C++ (например, драйвер базы данных `github.com/mattn/go-sqlite3`), **включение CGO обязательно (`CGO_ENABLED=1`)**.\n\nПодводный камень CGO в контейнерах:\n1. Если собрать бинарник в стандартном образе на базе Debian/Ubuntu (`glibc`), он динамически связывается с `/lib/x86_64-linux-gnu/libc.so.6`.\n2. Если скопировать этот бинарник в минимальный образ на базе Alpine Linux (`musl libc`) или `scratch`, при запуске произойдет сбой:\n   `exec /app: no such file or directory`\n\nРешение для статического CGO:\nИспользование компилятора GCC в Alpine Linux со специальными флагами статического связывания:\n`-ldflags=\"-linkmode external -extldflags '-static'\"`\nЭто принудительно линкует `musl libc` статически внутрь Go-бинарника, позволяя запускать даже CGO-приложения в абсолютно пустом образе `FROM scratch`!",
    "step_by_step": "1. Напишите Go-сервис, использующий SQLite через CGO драйвер.\n2. В этапе builder установите пакеты `gcc` и `musl-dev`.\n3. Укажите параметры сборки: `CGO_ENABLED=1` и `-ldflags=\"-linkmode external -extldflags '-static'\"`.\n4. Скопируйте полученный бинарник в чистый `scratch` или `alpine`.\n5. Убедитесь, что бинарник успешно открывает SQLite БД и выполняет SQL-запросы.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"database/sql\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\n\t_ \"github.com/mattn/go-sqlite3\"\n)\n\nfunc main() {\n\t// Инициализация in-memory SQLite базы данных\n\tdb, err := sql.Open(\"sqlite3\", \":memory:\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Failed to open SQLite: %v\", err)\n\t}\n\tdefer db.Close()\n\n\t_, err = db.Exec(\"CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Migration failed: %v\", err)\n\t}\n\t_, _ = db.Exec(\"INSERT INTO users (name) VALUES ('Alice'), ('Bob');\")\n\n\thttp.HandleFunc(\"/users\", func(w http.ResponseWriter, r *http.Request) {\n\t\trows, err := db.Query(\"SELECT name FROM users\")\n\t\tif err != nil {\n\t\t\thttp.Error(w, err.Error(), 500)\n\t\t\treturn\n\t\t}\n\t\tdefer rows.Close()\n\n\t\tfor rows.Next() {\n\t\t\tvar name string\n\t\t\t_ = rows.Scan(&name)\n\t\t\tfmt.Fprintf(w, \"User: %s\\n\", name)\n\t\t}\n\t})\n\n\tlog.Println(\"SQLite CGO service started on :8080...\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Go сервис с использованием SQLite через CGO"
      },
      {
        "filename": "go.mod",
        "lang": "go",
        "code": "module example.com/sqliteapp\n\ngo 1.24\n\nrequire github.com/mattn/go-sqlite3 v1.14.24\n",
        "note": "go.mod с зависимостью go-sqlite3"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\n\n# Установка GCC и заголовочных файлов musl, необходимых для сборки CGO\nRUN apk add --no-cache gcc musl-dev\n\nWORKDIR /app\n\nCOPY go.mod go.sum* ./\nRUN go mod download\n\nCOPY . .\n\n# Статическая внешняя линковка C-библиотеки в Alpine\nRUN CGO_ENABLED=1 GOOS=linux go build \\\n    -a \\\n    -ldflags=\"-linkmode external -extldflags '-static' -w -s\" \\\n    -o /bin/sqlite-app .\n\n# Запуск в пустом образе scratch!\nFROM scratch\nCOPY --from=builder /bin/sqlite-app /sqlite-app\nEXPOSE 8080\nENTRYPOINT [\"/sqlite-app\"]",
        "note": "Dockerfile со статической линковкой CGO под scratch"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка CGO приложения в scratch\ndocker build -t app-cgo-static:latest .\n\n# Проверка размера (образ весит около 15 MB со встроенным SQLite движком)\ndocker images app-cgo-static:latest\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-cgo app-cgo-static:latest\n\n# Проверка чтения из SQLite\ncurl http://localhost:8080/users\n\n# Очистка\ndocker rm -f test-cgo"
      }
    ],
    "under_the_hood": "Флаг `-linkmode external` заставляет Go передать финальную сборку внешнему линковщику хоста (`gcc` / `ld`). Параметр `-extldflags '-static'` инструктирует gcc связать стандартную библиотеку C (в Alpine это `libc.a` из musl) статически в исполняемый сегмент `.text`. В результате бинарник не содержит динамических ссылок на `.so` библиотеки.",
    "pitfalls": "1. Попытка статической линковки с GNU glibc: glibc крайне плохо поддерживает статическую линковку (`nsswitch` и сетевой резолвер по-прежнему требуют `dlopen`). Для статического CGO всегда используйте Alpine с musl.\n2. Увеличение времени сборки из-за компиляции исходного C-кода SQLite.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему сборка статического бинарника с CGO на базе Debian/Ubuntu часто приводит к предупреждению `Using 'getaddrinfo' in statically linked applications requires at runtime the shared libraries from the glibc version used for linking`?»\n**Ответ:** GNU libc архитектурно разработана с расчетом на динамическую загрузку библиотек через Name Service Switch (`libnss_files.so`, `libnss_dns.so`). При статической компиляции сетевой резолвер glibc в рантайме все равно пытается выполнить `dlopen()` этих библиотек. Если их нет в контейнере, DNS перестает работать. Поэтому для полностью автономных статических CGO-бинарников стандартом является Alpine Linux с библиотекой musl libc, которая не использует динамический NSS."
  },
  {
    "num": 34,
    "title": "Проблема SSL-сертификатов в scratch: диагностика и безопасный импорт",
    "task": "**Проблема SSL-сертификатов в `scratch`**: Добавь в приложение HTTP-запрос к любому HTTPS-сайту (например, `google.com`). Собери в `scratch` и запусти. Получишь ошибку проверки сертификата! В этапе сборки скопируй файл `/etc/ssl/certs/ca-certificates.crt` из `builder` в `scratch`. Проверь, что HTTPS заработал.",
    "theory": "При проектировании микросервисной архитектуры абсолютное большинство сервисов взаимодействуют по HTTPS (вызовы платежных шлюзов, сторонних REST API, OAuth-провайдеров).\n\nЕсли в контейнере `FROM scratch` не настроены корневые сертификаты, любой сетевой вызов завершается ошибкой:\n`x509: certificate signed by unknown authority`\n\nС точки зрения архитектуры безопасности Docker-образов:\n1. Запрещено отключать верификацию сертификатов через `InsecureSkipVerify: true` (это открывает возможность атаки Man-in-the-Middle).\n2. Сертификаты должны быть установлены через официальный пакет `ca-certificates` в этапе сборки.\n3. Бандл `/etc/ssl/certs/ca-certificates.crt` копируется в `scratch`.",
    "step_by_step": "1. Напишите HTTP-клиент, отправляющий запрос на `https://api.github.com`.\n2. Соберите образ без сертификатов и продемонстрируйте сбой.\n3. Добавьте копирование `ca-certificates.crt`.\n4. Проверьте успешное выполнение защищенного соединения.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc main() {\n\tclient := &http.Client{Timeout: 5 * time.Second}\n\n\thttp.HandleFunc(\"/external\", func(w http.ResponseWriter, r *http.Request) {\n\t\tresp, err := client.Get(\"https://api.github.com/zen\")\n\t\tif err != nil {\n\t\t\thttp.Error(w, fmt.Sprintf(\"External TLS Call Failed: %v\", err), http.StatusBadGateway)\n\t\t\treturn\n\t\t}\n\t\tdefer resp.Body.Close()\n\n\t\tw.WriteHeader(resp.StatusCode)\n\t\tfmt.Fprintf(w, \"Success! GitHub Zen API answered with status: %s\\n\", resp.Status)\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис с внешним HTTPS запросом"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\n\nRUN apk add --no-cache ca-certificates\n\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /bin/app main.go\n\nFROM scratch\n\n# Импорт доверенных сертификатов удостоверяющих центров\nCOPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt\n\nCOPY --from=builder /bin/app /bin/app\n\nEXPOSE 8080\nENTRYPOINT [\"/bin/app\"]",
        "note": "Dockerfile с безопасным импортом сертификатов в scratch"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t app-ssl-diag:v1 .\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-ssl app-ssl-diag:v1\n\n# Проверка успешного TLS вызова\ncurl http://localhost:8080/external\n\n# Очистка\ndocker rm -f test-ssl"
      }
    ],
    "under_the_hood": "Go стандартно проверяет цифровую подпись X.509 сертификата удаленного сервера по алгоритмам RSA/ECDSA, сверяя открытый ключ подписи с корневыми открытыми ключами из файла `ca-certificates.crt`. При совпадении хэшей цепочка считается доверенной.",
    "pitfalls": "1. Использование `InsecureSkipVerify: true` в коде в качестве «быстрого решения» — критическая уязвимость в продакшне.\n2. Неверный путь копирования сертификата в scratch.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Go коде категорически запрещено использовать `tls.Config{InsecureSkipVerify: true}` даже во внутреннем контуре Kubernetes кластера?»\n**Ответ:** `InsecureSkipVerify: true` полностью отключает валидацию сертификата удаленного узла (проверку срока действия, SAN/CN и доверия CA). В распределенной среде это делает сервис уязвимым для MITM-атак со стороны любого соседнего скомпрометированного пода, DNS-спуфинга во внутренней сети CoreDNS или подмены трафика при использовании Service Mesh без взаимной проверки mTLS."
  },
  {
    "num": 35,
    "title": "Scratch-образ и HTTPS-сертификаты: автономная интеграция и встроенные бандлы",
    "task": "**Scratch-образ и HTTPS-сертификаты**: Самый минимальный образ в докере — это абсолютно пустой образ `scratch`. Попробуйте собрать ваше приложение на базе `FROM scratch`. Запустите его и сделайте изнутри контейнера HTTPS-запрос к внешнему API. Зафиксируйте ошибку сетевого рукопожатия, связанную с отсутствием корневых сертификатов шифрования (CA). Исправьте Dockerfile: на этапе сборки `builder` скачайте пакет `ca-certificates`, а на втором этапе скопируйте файл сертификатов `ca-certificates.crt` в ваш scratch-контейнер.",
    "theory": "Существует два основных способа решения проблемы сертификатов при работе с минималистичными образами:\n\nСпособ 1: **Внешнее копирование бандла сертификатов**\nВ Dockerfile копируется файл `/etc/ssl/certs/ca-certificates.crt`. Это стандартный способ, сохраняющий возможность обновления сертификатов без изменения исходного кода.\n\nСпособ 2: **Встраивание сертификатов в бинарник через Go `embed`**\nНачиная с Go 1.16, библиотека сертификатов или локальный файл корпоративных CA может быть встроен прямо в исполняемый бинарник директивой `//go:embed`.\nПри старте приложения кастомный `x509.CertPool` инициализируется из встроенных байтов:\n```go\n//go:embed certs/ca.crt\nvar rootCACert []byte\n```\nЭто делает образ 100% автономным: бинарник работает в `scratch` даже без единого файла в `/etc/ssl/certs`!",
    "step_by_step": "1. Напишите код Go с кастомной инициализацией CertPool или копированием бандла.\n2. Опишите `Dockerfile` для сборки автономного бинарника.\n3. Соберите образ и протестируйте исходящее TLS соединение.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"crypto/tls\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc main() {\n\t// Стандартный клиент с таймаутом\n\tclient := &http.Client{\n\t\tTimeout: 5 * time.Second,\n\t\tTransport: &http.Transport{\n\t\t\tTLSClientConfig: &tls.Config{\n\t\t\t\tMinVersion: tls.VersionTLS12,\n\t\t\t},\n\t\t},\n\t}\n\n\thttp.HandleFunc(\"/ping-tls\", func(w http.ResponseWriter, r *http.Request) {\n\t\tresp, err := client.Get(\"https://www.google.com\")\n\t\tif err != nil {\n\t\t\thttp.Error(w, err.Error(), 500)\n\t\t\treturn\n\t\t}\n\t\tdefer resp.Body.Close()\n\t\tfmt.Fprintf(w, \"TLS Handshake Successful! Remote status: %s\\n\", resp.Status)\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Клиент с принудительным TLS 1.2+"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\n\nRUN apk add --no-cache ca-certificates\n\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /bin/app main.go\n\nFROM scratch\nCOPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt\nCOPY --from=builder /bin/app /app\nEXPOSE 8080\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile с копированием сертификатов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t test-ca-bundle:v1 .\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-ca test-ca-bundle:v1\ncurl http://localhost:8080/ping-tls\ndocker rm -f test-ca"
      }
    ],
    "under_the_hood": "Go компилятор линкует криптографические алгоритмы TLS (AES-GCM, ChaCha20-Poly1305, ECDHE) статически. Наличие сертификатов в файловой системе обеспечивает доверенные корневые якоря (Trust Anchors) для валидации цепочки сертификатов X.509.",
    "pitfalls": "1. Копирование сертификатов с правами, запрещающими чтение непривилегированному пользователю (права должны быть 0644).\n2. Забытые промежуточные сертификаты при работе с внутренними корпоративными PKI (Active Directory Certificate Services, HashiCorp Vault).",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы преимущества и недостатки встраивания корневых сертификатов прямо в Go-бинарник через `//go:embed` по сравнению с копированием `/etc/ssl/certs/ca-certificates.crt` в Dockerfile?»\n**Ответ:** Преимущество: бинарник становится абсолютно автономным и гарантированно работает в любых пустых средах без файлов ОС. Недостаток: невозможно обновить истекший или скомпрометированный корневой сертификат средствами администратора ОС или монтированием ConfigMap без полной перекомпиляции Go-кода и выпуска нового релиза приложения."
  },
  {
    "num": 36,
    "title": "Health Check в Dockerfile: реализация через встроенную CLI-подкоманду",
    "task": "Добавьте health check в Dockerfile: `HEALTHCHECK --interval=30s CMD [\"/app\", \"health\"]` (если ваше приложение поддерживает subcommand для health check).",
    "theory": "Классическая инструкция `HEALTHCHECK CMD wget ...` или `curl ...` не работает в образах на базе `FROM scratch` или `distroless`, так как там нет утилит `wget` и `curl`.\n\nЭлегантное и высоконадежное решение: **самопроверка здоровья приложением через CLI-подкоманду (Self-Healthcheck)**.\n\nАрхитектура решения:\n1. Go-бинарник при запуске с аргументом `healthcheck` (`os.Args[1] == \"healthcheck\"`):\n   - Выполняет локальный HTTP-запрос к своему собственному эндпоинту `http://127.0.0.1:8080/healthz`.\n   - Если статус `200 OK`, завершается с кодом выхода `0` (`os.Exit(0)`).\n   - Если произошел таймаут или код ошибки, завершается с кодом выхода `1` (`os.Exit(1)`).\n2. В `Dockerfile` проверка описывается в формате exec-массива:\n   `HEALTHCHECK --interval=10s --timeout=3s CMD [\"/app\", \"healthcheck\"]`\n\nПреимущества:\n- Работает в 100% пустом `FROM scratch` без шелла и внешних утилит.\n- Нулевой оверхед на запуск сторонних интерпретаторов.",
    "step_by_step": "1. Добавьте в `main()` разбор аргумента командной строки `healthcheck`.\n2. Реализуйте функцию локальной проверки с таймаутом в 2 секунды.\n3. В `Dockerfile` пропишите `HEALTHCHECK CMD [\"/app\", \"healthcheck\"]`.\n4. Соберите образ на базе `scratch` и убедитесь, что статус контейнера в `docker ps` успешно переходит в `healthy`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n\t\"time\"\n)\n\nfunc main() {\n\t// Подкоманда самопроверки здоровья для Docker HEALTHCHECK\n\tif len(os.Args) > 1 && os.Args[1] == \"healthcheck\" {\n\t\tclient := http.Client{Timeout: 2 * time.Second}\n\t\tresp, err := client.Get(\"http://127.0.0.1:8080/healthz\")\n\t\tif err != nil || resp.StatusCode != http.StatusOK {\n\t\t\tos.Exit(1) // Неисправен (unhealthy)\n\t\t}\n\t\tos.Exit(0) // Исправен (healthy)\n\t}\n\n\t// Основной рабочий режим веб-сервера\n\thttp.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\tw.Write([]byte(\"OK\"))\n\t})\n\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Service running with self-healthcheck in scratch!\\n\")\n\t})\n\n\tlog.Println(\"Server started on :8080...\")\n\tif err := http.ListenAndServe(\":8080\", nil); err != nil {\n\t\tlog.Fatal(err)\n\t}\n}",
        "note": "Сервер со встроенным режимом healthcheck подкоманды"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\n\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-w -s\" -o /bin/app main.go\n\n# Запуск в абсолютно пустом scratch!\nFROM scratch\n\nCOPY --from=builder /bin/app /app\n\nEXPOSE 8080\n\n# Проверка без curl/wget/sh: вызывается сам Go бинарник!\nHEALTHCHECK --interval=5s --timeout=2s --start-period=1s --retries=2 \\\n  CMD [\"/app\", \"healthcheck\"]\n\nENTRYPOINT [\"/app\"]",
        "note": "Dockerfile с декларацией HEALTHCHECK без шелла"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t app-self-health:latest .\n\n# Запуск\ndocker run -d -p 8080:8080 --name test-sh app-self-health:latest\n\n# Мониторинг статуса (через несколько секунд перейдет в healthy)\ndocker ps --filter \"name=test-sh\" --format \"table {{.Names}}\\t{{.Status}}\"\n\n# Проверка логов healthcheck\ndocker inspect --format='{{json .State.Health}}' test-sh\n\n# Очистка\ndocker rm -f test-sh"
      }
    ],
    "under_the_hood": "Когда `HEALTHCHECK` задан как JSON-массив `CMD [\"/app\", \"healthcheck\"]`, рантайм контейнеров вызывает системный вызов `execve(\"/app\", [\"/app\", \"healthcheck\"], ...)`. Это не требует `/bin/sh` и работает даже в пустой файловой системе `scratch`.",
    "pitfalls": "1. Забыть таймаут у `http.Client` в режиме healthcheck: если сервер завис, проверка тоже зависнет.\n2. Использование длинных путей или внешних зависимостей в режиме healthcheck.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как реализовать проверку `HEALTHCHECK` в Dockerfile для Go-приложения в контейнере `FROM scratch`, если в образе нет утилит `curl`, `wget` и оболочки `/bin/sh`?»\n**Ответ:** Реализовать логику проверки здоровья прямо в Go-бинарнике, добавив обработку CLI-флага или подкоманды: `if os.Args[1] == \"health\" { ... }`. В этой ветке код делает легковесный HTTP GET запрос к локальному эндпоинту `127.0.0.1:8080/healthz` с коротким таймаутом и завершается с `os.Exit(0)` при успехе или `os.Exit(1)` при ошибке. В Dockerfile указать exec-форму: `HEALTHCHECK CMD [\"/app\", \"health\"]`."
  },
  {
    "num": 37,
    "title": "Хранилища данных: Bind Mounts, Named Volumes и tmpfs mounts",
    "task": "Настрой **bind mounts vs volumes**: bind mount `./config:/app/config` для development (live sync). named volume для production data. tmpfs mount `/tmp` для sensitive data (не пишется на диск).",
    "theory": "Контейнеры по умолчанию иммутабельны и эфемерны: при удалении контейнера все данные, записанные в его верхний слой (writable layer), безвозвратно уничтожаются.\n\nВ Docker существует три основных механизма монтирования:\n\n1. **Bind Mounts (`./config:/app/config`):**\n   - Монтирует произвольный файл или каталог хост-машины напрямую в контейнер.\n   - Идеально для локальной разработки (live-sync конфигураций, горячая перезагрузка кода).\n   - Зависит от структуры каталогов конкретной хостовой ОС.\n\n2. **Named Volumes (`docker volume create pgdata` / `pgdata:/var/lib/postgresql/data`):**\n   - Управляются Docker и хранятся в `/var/lib/docker/volumes/`.\n   - Изолированы от структуры хоста, обладают высокой производительностью.\n   - Золотой стандарт для баз данных (PostgreSQL, MySQL, Redis).\n\n3. **tmpfs mounts (`--tmpfs /tmp`):**\n   - Хранятся исключительно в оперативной памяти хоста (RAM), никогда не записываются на диск.\n   - Идеальны для секретов, временных файлов и чувствительных данных.",
    "step_by_step": "1. Создайте локальный файл конфигурации `config.json`.\n2. Создайте именованный том: `docker volume create my_data_vol`.\n3. Запустите Go-контейнер, использующий bind mount для чтения конфигурации и named volume для сохранения состояния.\n4. Продемонстрируйте сохранение данных после перезапуска контейнера.",
    "code_blocks": [
      {
        "filename": "config.json",
        "lang": "json",
        "code": "{\n  \"app_name\": \"StorageDemo\",\n  \"environment\": \"development\"\n}",
        "note": "Файл конфигурации для bind mount"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n\t\"path/filepath\"\n\t\"time\"\n)\n\nfunc main() {\n\t// Чтение конфигурации из bind mount\n\tcfgData, _ := os.ReadFile(\"/app/config/config.json\")\n\n\t// Запись состояния в named volume\n\tdataPath := \"/app/data/counter.txt\"\n\t_ = os.MkdirAll(filepath.Dir(dataPath), 0755)\n\n\thttp.HandleFunc(\"/write\", func(w http.ResponseWriter, r *http.Request) {\n\t\tmsg := fmt.Sprintf(\"Saved at: %s\\n\", time.Now().UTC().Format(time.RFC3339))\n\t\tf, _ := os.OpenFile(dataPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)\n\t\tdefer f.Close()\n\t\t_, _ = f.WriteString(msg)\n\t\tfmt.Fprintf(w, \"Appended to volume: %s\", msg)\n\t})\n\n\thttp.HandleFunc(\"/read\", func(w http.ResponseWriter, r *http.Request) {\n\t\tdata, _ := os.ReadFile(dataPath)\n\t\tfmt.Fprintf(w, \"Config: %s\\nData from Volume:\\n%s\\n\", string(cfgData), string(data))\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}",
        "note": "Сервис, работающий с bind mount и volume"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -o /bin/app main.go\n\nFROM alpine:3.20\nWORKDIR /app\nCOPY --from=builder /bin/app /app/app\nEXPOSE 8080\nENTRYPOINT [\"/app/app\"]",
        "note": "Dockerfile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Создаем именованный том\ndocker volume create storage_data_vol\n\n# Сборка\ndocker build -t app-storage:v1 .\n\n# Запуск с bind mount для конфига и named volume для данных\ndocker run -d -p 8080:8080 --name test-store \\\n  -v $(pwd)/config.json:/app/config/config.json:ro \\\n  -v storage_data_vol:/app/data \\\n  app-storage:v1\n\n# Запись данных в volume\ncurl http://localhost:8080/write\ncurl http://localhost:8080/read\n\n# Удаляем контейнер и создаем новый с тем же volume — данные сохраняются!\ndocker rm -f test-store\ndocker run -d -p 8080:8080 --name test-store-2 \\\n  -v $(pwd)/config.json:/app/config/config.json:ro \\\n  -v storage_data_vol:/app/data \\\n  app-storage:v1\n\ncurl http://localhost:8080/read\n\n# Очистка\ndocker rm -f test-store-2\ndocker volume rm storage_data_vol"
      }
    ],
    "under_the_hood": "Docker использует системный вызов ядра Linux `mount(source, target, \"none\", MS_BIND, NULL)` для bind mount и создает каталог в `/var/lib/docker/volumes/<name>/_data` для named volume. При этом OverlayFS обходит эти точки монтирования, передавая I/O операции напрямую драйверу файловой системы хоста (ext4/xfs), что обеспечивает максимальный IOPS.",
    "pitfalls": "1. Монтирование bind mount без флага `:ro` (read-only): скомпрометированный контейнер может перезаписать критические файлы на хосте.\n2. Проблемы с правами доступа (permission denied): пользователь `appuser` (UID 10001) в контейнере не имеет прав на запись в каталог хоста, принадлежащий root.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем фундаментальные отличия Bind Mount от Named Volume и почему в продакшн-окружениях запрещено использовать Bind Mounts для баз данных?»\n**Ответ:** Bind Mount жестко привязан к конкретному абсолютному пути файловой системы хоста, что нарушает переносимость образов и может вызывать проблемы с правами UID/GID и блокировками файлов (особенно в Docker Desktop на macOS через gRPC-FUSE/VirtioFS). Named Volume изолирован в служебной директории Docker, управляется через Docker API/CSI-драйверы, обеспечивает максимальную скорость дискового ввода-вывода (IOPS) и переносим между нодами кластера."
  },
  {
    "num": 38,
    "title": "ENTRYPOINT против CMD: корректная передача CLI-аргументов и сигналов",
    "task": "Используйте `ENTRYPOINT` вместо `CMD` для бинарника, чтобы аргументы при запуске контейнера добавлялись к основной команде, а не заменяли её.",
    "theory": "Различие между директивами `ENTRYPOINT` и `CMD` часто вызывает путаницу, но является базой проектирования контейнеров:\n\n1. **`ENTRYPOINT` (Исполняемый бинарник):**\n   - Задает неизменяемую команду/бинарник, который будет запущен при старте контейнера.\n   - Все аргументы, переданные в команду `docker run <image> [args...]`, **добавляются к ENTRYPOINT**, а не замещают его.\n\n2. **`CMD` (Аргументы по умолчанию):**\n   - Задает аргументы по умолчанию для `ENTRYPOINT`.\n   - Если пользователь передает аргументы в `docker run`, они **полностью перезаписывают `CMD`**.\n\n3. **Exec-форма против Shell-формы:**\n   - **Exec-форма (JSON array):** `ENTRYPOINT [\"/app\", \"serve\"]` — процесс запускается напрямую как **PID 1**, корректно получая сигналы `SIGTERM` для Graceful Shutdown.\n   - **Shell-форма:** `ENTRYPOINT /app serve` — процесс запускается как дочерний для `/bin/sh -c`. Сигналы ОС не доходят до Go-процесса, и Docker убивает контейнер через 10 секунд по `SIGKILL`!",
    "step_by_step": "1. Напишите Go CLI-приложение с поддержкой флагов и подкоманд (`serve`, `migrate`, `version`).\n2. Опишите `Dockerfile`, где `ENTRYPOINT` указывает на бинарник, а `CMD` задает параметры по умолчанию (`[\"--port\", \"8080\"]`).\n3. Запустите контейнер без аргументов: проверьте запуск с дефолтными параметрами.\n4. Запустите контейнер с кастомными аргументами: `docker run myapp --port 9090`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"flag\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\tport := flag.String(\"port\", \"8080\", \"HTTP server port\")\n\tmode := flag.String(\"mode\", \"production\", \"Application run mode\")\n\tflag.Parse()\n\n\t// Если передана подкоманда\n\tif len(flag.Args()) > 0 && flag.Args()[0] == \"version\" {\n\t\tfmt.Println(\"App Version: v1.0.0\")\n\t\tos.Exit(0)\n\t}\n\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"App running in %s mode on port :%s\\n\", *mode, *port)\n\t})\n\n\tfmt.Printf(\"Starting server on port :%s in %s mode...\\n\", *port, *mode)\n\t_ = http.ListenAndServe(\":\"+*port, nil)\n}",
        "note": "Go CLI сервис с поддержкой флагов командной строки"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY main.go .\nRUN CGO_ENABLED=0 go build -ldflags=\"-w -s\" -o /bin/app main.go\n\nFROM scratch\n\nCOPY --from=builder /bin/app /app\n\nEXPOSE 8080\n\n# ENTRYPOINT задает исполняемый файл\nENTRYPOINT [\"/app\"]\n\n# CMD задает аргументы по умолчанию (могут быть переопределены пользователем)\nCMD [\"--port\", \"8080\", \"--mode\", \"default\"]",
        "note": "Идеальное сочетание ENTRYPOINT и CMD"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка\ndocker build -t app-cli-demo:v1 .\n\n# Запуск по умолчанию (используются аргументы из CMD: --port 8080)\ndocker run -d -p 8080:8080 --name test-def app-cli-demo:v1\ncurl http://localhost:8080\ndocker rm -f test-def\n\n# Запуск с переопределением флагов командной строки\ndocker run -d -p 9090:9090 --name test-custom app-cli-demo:v1 --port 9090 --mode test\ncurl http://localhost:9090\ndocker rm -f test-custom\n\n# Запуск подкоманды\ndocker run --rm app-cli-demo:v1 version"
      }
    ],
    "under_the_hood": "Docker объединяет массивы `Entrypoint` и `Cmd` из метаданных контейнера в единый срез аргументов `args = append(Entrypoint, Cmd...)` и передает его в системный вызов `execve(args[0], args, env)`. При этом процесс Go становится процессом-инициализатором (PID 1) в изолированном пространстве имен PID.",
    "pitfalls": "1. Использование shell-формы `CMD /app`: контейнер не реагирует на `SIGTERM` при `docker stop`.\n2. Путаница между замещением `ENTRYPOINT` (требуется флаг `--entrypoint`) и `CMD` (достаточно дописать аргументы в конце команды `docker run`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Что произойдет при выполнении команды `docker stop <container>`, если в Dockerfile использовалась shell-форма `CMD ./app` вместо exec-формы `CMD [\"./app\"]`?»\n**Ответ:** При shell-форме Docker запускает команду через командный процессор: `/bin/sh -c \"./app\"`. В результате PID 1 получает процесс `sh`, а само Go-приложение становится дочерним процессом. Процесс `/bin/sh` в Linux по умолчанию не пересылает сигналы `SIGTERM` своим дочерним процессам. Go-сервер не получит сигнал, не сможет выполнить Graceful Shutdown и завершить активные транзакции. Через 10 секунд (дефолтный таймаут) Docker принудительно убьет процесс сигналом `SIGKILL`."
  }
]
