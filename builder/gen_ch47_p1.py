exercises = [
  {
    "num": 1,
    "title": "Оптимизация Dockerfile для Kubernetes: кэширование зависимостей и минимальный OCI-образ",
    "task": "Закрепите версии зависимостей в `go.sum`, используйте кэширование слоёв (сначала копируйте `go.mod` и `go.sum`, затем `go mod download`, потом исходники).",
    "theory": "Перед развертыванием приложения в кластере Kubernetes необходимо сформировать контейнерный OCI-образ, удовлетворяющий промышленным стандартам:\n1. **Детерминизм и воспроизводимость:** Версии всех модулей Go фиксируются в файле `go.sum` с криптографическими контрольными суммами.\n2. **Эффективное послойное кэширование (Docker Layer Caching):** Инструкции `COPY go.mod go.sum` и `RUN go mod download` выносятся перед копированием исходного кода. Это исключает повторную загрузку гигабайтов зависимостей при изменении строчки кода.\n3. **Многоэтапная сборка (Multi-stage build):** Компиляция выполняется в тяжелом образе `golang:1.24-alpine`, а итоговый бинарник копируется в минимальный образ `alpine:3.21` или `scratch`, сокращая размер пода с 800 МБ до 15 МБ.",
    "step_by_step": "1. Создайте файл `Dockerfile` с многоэтапной сборкой.\n2. Скопируйте файлы манифеста зависимостей: `COPY go.mod go.sum ./`.\n3. Запустите загрузку модулей: `RUN go mod download`.\n4. Скопируйте исходный код и выполните сборку со статической линковкой: `CGO_ENABLED=0 go build -ldflags=\"-s -w\" -o /service .`.\n5. Скопируйте скомпилированный бинарник в чистый образ `alpine:3.21` под непривилегированным пользователем.",
    "code_blocks": [
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# syntax=docker/dockerfile:1\nFROM golang:1.24-alpine AS builder\n\nWORKDIR /app\n\n# Кэширование слоя модулей: выполняется только при изменении go.mod или go.sum\nCOPY go.mod go.sum* ./\nRUN go mod download\n\n# Копирование исходного кода и статическая сборка\nCOPY . .\nRUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-s -w\" -o /bin/k8s-app .\n\n# Финальный runtime-образ\nFROM alpine:3.21\nRUN apk --no-cache add ca-certificates tzdata\nUSER 65534:65534\nCOPY --from=builder /bin/k8s-app /k8s-app\nEXPOSE 8080\nENTRYPOINT [\"/k8s-app\"]"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\tport := os.Getenv(\"PORT\")\n\tif port == \"\" {\n\t\tport = \"8080\"\n\t}\n\n\thttp.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"OK\"))\n\t})\n\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\t_, _ = w.Write([]byte(\"Go microservice is running in Kubernetes!\"))\n\t})\n\n\tfmt.Printf(\"Сервис запущен на :%s\\n\", port)\n\tif err := http.ListenAndServe(\":\"+port, nil); err != nil {\n\t\tfmt.Printf(\"Ошибка сервера: %v\\n\", err)\n\t}\n}"
      }
    ],
    "under_the_hood": "Демон сборки вычисляет контрольный хэш содержимого файлов `go.mod` и `go.sum`. Если хэши совпадают с предыдущей сборкой, шаг `RUN go mod download` не запускается, а используется закэшированный снимок файловой системы (Layer snapshot).\n\nСкомпилированный бинарник с флагом `CGO_ENABLED=0` не имеет внешних динамических зависимостей от `libc` (ld-linux.so), что позволяет ему нативно выполняться в минимальном окружении Alpine или Scratch внутри контейнера Kubernetes.",
    "pitfalls": "1. Копирование `COPY . .` до `RUN go mod download`: любое изменение комментария в коде приводит к повторному скачиванию всех модулей из сети.\n2. Забытый `CGO_ENABLED=0`: бинарник, скомпилированный на хосте с glibc, упадет в Alpine контейнере с ошибкой `standard_init_linux.go: exec user process caused: no such file or directory`.\n3. Запуск от пользователя root (UID 0): грубое нарушение стандартов безопасности Kubernetes Pod Security Standards.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему размер OCI-образа критически влияет на стабильность кластера Kubernetes при горизонтальном автомасштабировании (HPA)?\n**Ответ:** При резком скачке нагрузки HPA создает десятки новых подов. Если образ весит 800 МБ, нодам кластера требуется скачать десятки гигабайт по сети (Image Pull Latency), что приводит к долгой задержке старта (Cold Start в 2-5 минут), исчерпанию дисковых квот нод и падению сервиса под входящим трафиком. Минимальный образ весом 15 МБ скачивается за 1-2 секунды, обеспечивая моментальную реакцию на всплески нагрузки."
  },
  {
    "num": 2,
    "title": "Унификация жизненного цикла сборки и деплоя с помощью Makefile",
    "task": "Напишите `Makefile` с командами `build`, `test`, `lint`, `docker-build`, `docker-run`.",
    "theory": "`Makefile` — стандарт декларативного описания задач сборки, тестирования и запуска в профессиональных инженерных командах. \n\nОн абстрагирует разработчика и CI/CD раннеры от громоздких флагов компилятора:\n- `make test`: запуск юнит-тестов с детектором гонок.\n- `make lint`: проверка кода статическим анализатором `golangci-lint`.\n- `make docker-build`: сборка OCI-образа с динамической подстановкой Git SHA и версии.\n- `make docker-run`: локальный запуск с пробросом портов и переменных окружения.\n\nИспользование директивы `.PHONY` гарантирует корректное выполнение команд даже при наличии одноименных файлов или папок на диске.",
    "step_by_step": "1. Создайте в корне проекта файл `Makefile`.\n2. Объявите переменные сборки: `APP_NAME`, `GIT_SHA`, `IMAGE_TAG`.\n3. Опишите цели: `build`, `test`, `lint`, `docker-build`, `docker-run`.\n4. Добавьте флаги `-race`, `-cover` для тестирования и `-ldflags=\"-s -w\"` для компиляции.\n5. Протестируйте выполнение команд в терминале.",
    "code_blocks": [
      {
        "filename": "Makefile",
        "lang": "makefile",
        "code": "APP_NAME ?= k8s-service\nREGISTRY ?= ghcr.io/company\nGIT_SHA  ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo \"dev\")\nIMAGE    ?= $(REGISTRY)/$(APP_NAME):$(GIT_SHA)\n\n.PHONY: all build test lint docker-build docker-run clean\n\nall: lint test build\n\nbuild:\n\t@echo \"==> Компиляция Go бинарника...\"\n\tCGO_ENABLED=0 go build -ldflags=\"-s -w -X main.version=$(GIT_SHA)\" -o bin/$(APP_NAME) .\n\ntest:\n\t@echo \"==> Запуск тестов с детектором гонок...\"\n\tgo test -v -race -coverprofile=coverage.out ./...\n\nlint:\n\t@echo \"==> Проверка кода линтером...\"\n\tgolangci-lint run --timeout=5m\n\ndocker-build:\n\t@echo \"==> Сборка Docker-образа $(IMAGE)...\"\n\tdocker build -t $(IMAGE) -t $(REGISTRY)/$(APP_NAME):latest .\n\ndocker-run:\n\t@echo \"==> Локальный запуск контейнера...\"\n\tdocker run --rm -p 8080:8080 -e PORT=8080 $(IMAGE)\n\nclean:\n\t@rm -rf bin/ coverage.out"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nvar version = \"dev\"\n\nfunc main() {\n\thttp.HandleFunc(\"/version\", func(w http.ResponseWriter, r *http.Request) {\n\t\t_, _ = w.Write([]byte(fmt.Sprintf(\"Version: %s\\n\", version)))\n\t})\n\tfmt.Printf(\"Сервис версии %s запущен на :8080\\n\", version)\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "GNU Make парсит зависимости между целями и запускает каждую строку рецепта в отдельном подоболочке `/bin/sh`. \n\nСимвол `@` в начале строки отключает эхо-вывод самой команды в терминал. Директива `.PHONY: build test` предотвращает коллизию: если в каталоге появится папка с именем `build`, Make не будет считать цель выполненной, а принудительно исполнит рецепт.",
    "pitfalls": "1. Использование пробелов вместо табуляций (`Tab`): синтаксический анализатор Make требует строго символ табуляции в начале строк рецептов.\n2. Отсутствие `.PHONY`: если случайно создать каталог `test`, вызов `make test` выдаст `make: 'test' is up to date` и ничего не выполнит.\n3. Жестко зашитые теги образов (`latest`): сборка затирает предыдущие версии без возможности отката.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в enterprise Go-репозиториях для автоматизации локальных задач предпочитают `Makefile` или `Taskfile` вместо bash-скриптов `build.sh`?\n**Ответ:** \n1. **Декларативный граф зависимостей:** Make умеет проверять временные метки файлов (mtime) и пересобирать только измененные артефакты.\n2. **Единый стандартизированный интерфейс:** Новому разработчику в команде не нужно читать документацию по десяткам скриптов: вызов `make all` или `make test` одинаково работает в 100 разных сервисах компании.\n3. **Бесшовная интеграция с CI:** Пайплайн в GitHub Actions или GitLab CI просто вызывает те же самые таргеты `make test`, гарантируя 100% идентичность проверок локально и на сервере сборки."
  },
  {
    "num": 3,
    "title": "Интеграция CI конвейера с контролем качества и публикацией в Docker Hub",
    "task": "Настройте GitHub Actions (или GitLab CI): пайплайн запускает линтер (`golangci-lint`), тесты с race detector, сборку образа и пуш в Docker Hub при пуше в main.",
    "theory": "Автоматизация Continuous Integration (CI) гарантирует, что каждый коммит в репозиторий проходит строгий аудит качества перед доставкой в кластер Kubernetes.\n\nКлючевые этапы пайплайна:\n1. **Static Analysis:** Проверка стиля, ошибок и уязвимостей через `golangci-lint`.\n2. **Race Detection & Testing:** Исполнение юнит-тестов с флагом `-race` для детекции гонок данных в горутинах.\n3. **Container Build & Publish:** Сборка OCI-образа через Docker Buildx и безопасная аутентификация в Docker Hub по токенам репозитория (`DOCKER_USER`, `DOCKER_PAT`).",
    "step_by_step": "1. Создайте workflow `.github/workflows/ci.yml`.\n2. Настройте триггер на событие `push` в ветку `main`.\n3. Настройте джобы `lint-and-test` и `build-and-push`.\n4. Сконфигурируйте авторизацию в Docker Hub через секреты репозитория.\n5. Проверьте зеленый статус выполнения пайплайна.",
    "code_blocks": [
      {
        "filename": ".github/workflows/ci.yml",
        "lang": "yaml",
        "code": "name: K8s Service CI\n\non:\n  push:\n    branches: [ main ]\n\njobs:\n  lint-and-test:\n    name: Code Quality Gate\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n          cache: true\n      - name: Run Linter\n        uses: golangci/golangci-lint-action@v6\n        with:\n          version: v1.64.5\n      - name: Run Tests with Race Detector\n        run: go test -v -race -cover ./...\n\n  docker:\n    name: Build & Push Image\n    needs: lint-and-test\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: docker/setup-buildx-action@v3\n      - name: Login to Docker Hub\n        uses: docker/login-action@v3\n        with:\n          username: ${{ secrets.DOCKERHUB_USERNAME }}\n          password: ${{ secrets.DOCKERHUB_TOKEN }}\n      - name: Build and Push\n        uses: docker/build-push-action@v5\n        with:\n          context: .\n          push: true\n          tags: |\n            ${{ secrets.DOCKERHUB_USERNAME }}/k8s-service:${{ github.sha }}\n            ${{ secrets.DOCKERHUB_USERNAME }}/k8s-service:latest"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc Add(a, b int) int {\n\treturn a + b\n}\n\nfunc main() {\n\thttp.HandleFunc(\"/add\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Result: %d\\n\", Add(2, 3))\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      },
      {
        "filename": "main_test.go",
        "lang": "go",
        "code": "package main\n\nimport \"testing\"\n\nfunc TestAdd(t *testing.T) {\n\tif got := Add(2, 3); got != 5 {\n\t\tt.Fatalf(\"Add(2, 3) = %d; want 5\", got)\n\t}\n}"
      }
    ],
    "under_the_hood": "Связка `needs: [lint-and-test]` гарантирует, что джоба сборки контейнера не стартует при наличии ошибок в тестах или коде. \n\nПри вызове `docker/build-push-action` экшен передает дайджест коммита в переменные тегов. В реестре формируется OCI-манифест, на который K8s ссылается в спецификации `Deployment`.",
    "pitfalls": "1. Запуск сборки контейнера параллельно с тестами: тратит ресурсы раннеров на публикацию заведомо нерабочего образа.\n2. Хранение паролей в открытом коде репозитория вместо GitHub Secrets.\n3. Отсутствие флага `-race` в тестах CI: скрытые многопоточные гонки пройдут в production.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в production Kubernetes-манифестах нельзя использовать тег `:latest`, сформированный CI?\n**Ответ:** Тег `:latest` мутабелен. Если кластер выполняет пересоздание пода на новой ноде, Kubelet при `imagePullPolicy: IfNotPresent` может запустить старую версию с локального кэша ноды, а соседняя нода скачает новую версию. В результате в одном кластере одновременно работают разные версии сервиса. Использование детерминированного тега по Git SHA исключает расхождение версий."
  },
  {
    "num": 4,
    "title": "Базовые манифесты Kubernetes: Deployment и Service (ClusterIP)",
    "task": "**Deployment и Service манифесты**: Напишите K8s-манифест `deployment.yaml` для запуска вашего Go-приложения, указав количество реплик равным 3. Напишите манифест `service.yaml` типа `ClusterIP` (или `NodePort`), который будет балансировать входящий трафик между вашими тремя подами (Pods).",
    "theory": "Кластер Kubernetes управляет контейнерами декларативно через базовые ресурсы:\n1. **`Deployment`:** Контроллер верхнего уровня, управляющий жизненным циклом подов (Pods) через дочерний `ReplicaSet`. Обеспечивает самоисцеление (Self-healing), масштабирование до 3 реплик и плавное обновление (RollingUpdate).\n2. **`Service` типа `ClusterIP`:** Внутренний балансировщик нагрузки с постоянным виртуальным IP-адресом. Поды эфемерны и регулярно меняют свои динамические IP при перезапусках. `Service` абстрагирует поды, направляя трафик на готовые реплики по совпадению селекторов (`selector.matchLabels`).",
    "step_by_step": "1. Создайте манифест `deployment.yaml` с `replicas: 3` и селектором `app: k8s-demo`.\n2. Создайте манифест `service.yaml` с типом `ClusterIP`, связав `port: 80` с `targetPort: 8080`.\n3. Примените манифесты: `kubectl apply -f deployment.yaml -f service.yaml`.\n4. Проверьте запуск 3 подов через `kubectl get pods -l app=k8s-demo`.\n5. Проверьте создание сервиса через `kubectl get svc k8s-demo`.",
    "code_blocks": [
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: k8s-demo\n  labels:\n    app: k8s-demo\nspec:\n  replicas: 3\n  selector:\n    matchLabels:\n      app: k8s-demo\n  template:\n    metadata:\n      labels:\n        app: k8s-demo\n    spec:\n      containers:\n        - name: web\n          image: ghcr.io/company/k8s-demo:v1.0.0\n          ports:\n            - containerPort: 8080"
      },
      {
        "filename": "service.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Service\nmetadata:\n  name: k8s-demo-svc\nspec:\n  type: ClusterIP\n  selector:\n    app: k8s-demo\n  ports:\n    - name: http\n      protocol: TCP\n      port: 80\n      targetPort: 8080"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\thostname, _ := os.Hostname()\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Ответ от пода: %s\\n\", hostname)\n\t})\n\n\tfmt.Println(\"HTTP сервер слушает на :8080\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "`Deployment` создает объект `ReplicaSet`. `ReplicaSetController` следит за тем, чтобы число живых подов соответствовало `spec.replicas=3`. \n\nКогда создается `Service`, контроллер K8s создает одноименный объект `Endpoints` (или `EndpointSlice`), заполняемый IP-адресами активных подов. Демон `kube-proxy` на каждой ноде кластера транслирует виртуальный ClusterIP в правила ядра Linux (iptables или IPVS), выполняя случайную или round-robin балансировку трафика.",
    "pitfalls": "1. Несовпадение селектора: если в `Service.spec.selector` указать `app: demo`, а в `Deployment.spec.template.metadata.labels` — `app: k8s-demo`, `Endpoints` будет пустым, и сервис вернет ошибку соединения.\n2. Путаница между `port` и `targetPort`: `port` — это порт, который слушает сам Service, а `targetPort` — порт внутри контейнера приложения.\n3. Попытка деплоить `Pod` напрямую без `Deployment`: при падении или перезагрузке ноды одиночный под никогда не будет пересоздан.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между `iptables` и `IPVS` режимами работы `kube-proxy` в крупных кластерах Kubernetes?\n**Ответ:** \n- Режим **`iptables`** использует последовательную цепочку правил пакетного фильтра Netfilter (сложность поиска $O(N)$). При росте числа сервисов в кластере до десятков тысяч добавление одного правила вызывает задержки ядра и резкую деградацию производительности сети.\n- Режим **`IPVS` (IP Virtual Server)** реализован на базе хэш-таблиц ядра Linux (сложность поиска $O(1)$). Он потребляет в разы меньше памяти, поддерживает сложные алгоритмы балансировки (least connection, weighted response) и рассчитан на огромные HighLoad-кластеры с сотнями тысяч эндпоинтов."
  },
  {
    "num": 5,
    "title": "Конфигурация через ConfigMap и Secret: внешняя настройка и переменные окружения",
    "task": "**Конфигурация через ConfigMap и Secrets**: Не храните пароли и адреса БД в кодовой базе. Напишите манифесты `ConfigMap` (для хранения адреса СУБД) и `Secret` (для хранения пароля к базе в зашифрованном Base64 виде). Настройте манифест `deployment.yaml` так, чтобы эти данные автоматически пробрасывались в контейнер с Go в виде переменных окружения.",
    "theory": "Принцип 12-Factor App требует строгого разделения конфигурации и исходного кода приложения. В Kubernetes для этого используются:\n1. **`ConfigMap`:** Хранилище неконфиденциальных параметров (URL внешних сервисов, уровень логирования, порт).\n2. **`Secret`:** Хранилище чувствительных данных (пароли к БД, API-токены, TLS-сертификаты). Данные кодируются в Base64 (тип `Opaque`) или задаются открытым текстом в поле `stringData`.\n\nВ манифесте `Deployment` переменные пробрасываются в контейнер:\n- Через `env` и `valueFrom: configMapKeyRef / secretKeyRef` для выборочных ключей.\n- Через `envFrom: [configMapRef, secretRef]` для массового импорта всех пар ключ-значение.",
    "step_by_step": "1. Создайте `configmap.yaml` с параметрами `DATABASE_HOST` и `LOG_LEVEL`.\n2. Создайте `secret.yaml` с паролем `DATABASE_PASSWORD` через `stringData`.\n3. В `deployment.yaml` подключите их через `envFrom` или `valueFrom`.\n4. В коде Go прочитайте переменные через `os.Getenv()`.\n5. Примените манифесты и убедитесь в логах пода, что конфигурация прочитана успешно.",
    "code_blocks": [
      {
        "filename": "configmap.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: app-config\ndata:\n  DB_HOST: \"postgres.production.svc.cluster.local\"\n  DB_PORT: \"5432\"\n  LOG_LEVEL: \"info\" "
      },
      {
        "filename": "secret.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Secret\nmetadata:\n  name: app-secret\ntype: Opaque\nstringData:\n  DB_USER: \"postgres_user\"\n  DB_PASSWORD: \"SuperSecurePassword2026!\" "
      },
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: backend-app\nspec:\n  replicas: 2\n  selector:\n    matchLabels:\n      app: backend-app\n  template:\n    metadata:\n      labels:\n        app: backend-app\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/backend:v1.0.0\n          envFrom:\n            - configMapRef:\n                name: app-config\n            - secretRef:\n                name: app-secret"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\tdbHost := os.Getenv(\"DB_HOST\")\n\tdbPort := os.Getenv(\"DB_PORT\")\n\tdbUser := os.Getenv(\"DB_USER\")\n\tdbPass := os.Getenv(\"DB_PASSWORD\")\n\tlogLevel := os.Getenv(\"LOG_LEVEL\")\n\n\tfmt.Printf(\"Инициализация сервиса: Host=%s:%s, User=%s, LogLevel=%s\\n\", dbHost, dbPort, dbUser, logLevel)\n\tif dbPass == \"\" {\n\t\tfmt.Println(\"ВНИМАНИЕ: Пароль БД отсутствует!\")\n\t} else {\n\t\tfmt.Println(\"Секретный пароль успешно загружен из Secret.\")\n\t}\n\n\thttp.HandleFunc(\"/health\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"OK\"))\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "При старте пода Kubelet обращается к API-серверу K8s, запрашивает объекты `ConfigMap` и `Secret` и передает их в виде массива `env[]` в CRI (Container Runtime Interface — containerd). \n\n`containerd` запускает процесс с этими переменными окружения в его виртуальном пространстве процесса `/proc/$PID/environ`.",
    "pitfalls": "1. Иллюзия безопасности Base64: стандартный `Secret` в Kubernetes не зашифрован, Base64 — это лишь метод кодирования бинарных данных в строку. В etcd секреты должны шифроваться через KMS (Encryption at Rest).\n2. Обновление переменных: если изменить ConfigMap в кластере, значения переменных окружения в уже запущенных подах **не обновятся** без перезапуска подов (`kubectl rollout restart`).\n3. Забытый namespace: ConfigMap и Secret должны находиться в том же namespace, что и Deployment.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в enterprise Kubernetes-инфраструктуре запрещено хранить боевые пароли в стандартных K8s Secret, и как организуют интеграцию с HashiCorp Vault?\n**Ответ:** Стандартные K8s Secret хранятся в Etcd и часто случайно утекают в git-манифесты или логи. В BigTech используют оператор **External Secrets Operator (ESO)** или **Vault Secrets Operator (VSO)**. \nПриложение декларирует ресурс `ExternalSecret`, контроллер которого по безопасной mTLS/OIDC аутентификации запрашивает секреты напрямую из защищенного хранилища HashiCorp Vault или Cloud KMS, создавая синхронизированные временные K8s Secret в памяти ноды с автоматической ротацией ключей."
  },
  {
    "num": 6,
    "title": "Автоматизация релизов под Kubernetes через GoReleaser и Git-теги",
    "task": "Автоматизируйте версионирование: при пуше тега `v*` запускайте goreleaser для сборки бинарников под разные платформы и создания GitHub Release.",
    "theory": "При подготовке бинарников и контейнерных образов для Kubernetes релизный процесс должен быть полностью автоматизирован.\n\n**GoReleaser** в связке с Git-тегами (`v*`):\n- Выполняет чистую кросс-компиляцию под Linux (amd64, arm64).\n- Внедряет переменные версии коммита через `-ldflags`.\n- Генерирует контрольные суммы SHA-256 (`checksums.txt`).\n- Автоматически собирает и пушит OCI-образы в реестр (Docker Hub / GHCR).\n- Формирует описание релиза на GitHub Releases.",
    "step_by_step": "1. Создайте файл `.goreleaser.yaml`.\n2. Настройте компиляцию бинарника под `linux/amd64` с `CGO_ENABLED=0`.\n3. Создайте `.github/workflows/release.yml`, срабатывающий на пуш тега `v*.*.*`.\n4. Добавьте права `permissions: contents: write, packages: write`.\n5. Создайте Git-тег и проверьте созданный релиз.",
    "code_blocks": [
      {
        "filename": ".goreleaser.yaml",
        "lang": "yaml",
        "code": "version: 2\n\nproject_name: k8s-service\n\nbefore:\n  hooks:\n    - go mod tidy\n\nbuilds:\n  - env:\n      - CGO_ENABLED=0\n    goos:\n      - linux\n    goarch:\n      - amd64\n      - arm64\n    ldflags:\n      - -s -w\n      - -X main.version={{.Version}}\n      - -X main.commit={{.Commit}}\n\ndockers:\n  - image_templates:\n      - \"ghcr.io/company/k8s-service:{{ .Version }}\"\n      - \"ghcr.io/company/k8s-service:latest\"\n    dockerfile: Dockerfile\n    build_flag_templates:\n      - \"--platform=linux/amd64\"\n\narchives:\n  - format: tar.gz\n    name_template: \"{{ .ProjectName }}_{{ .Version }}_{{ .Os }}_{{ .Arch }}\"\n\nchecksum:\n  name_template: \"checksums.txt\" "
      },
      {
        "filename": ".github/workflows/release.yml",
        "lang": "yaml",
        "code": "name: Release\n\non:\n  push:\n    tags:\n      - 'v*.*.*'\n\npermissions:\n  contents: write\n  packages: write\n\njobs:\n  goreleaser:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n        with:\n          fetch-depth: 0\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n      - name: Log in to GHCR\n        uses: docker/login-action@v3\n        with:\n          registry: ghcr.io\n          username: ${{ github.actor }}\n          password: ${{ secrets.GITHUB_TOKEN }}\n      - uses: goreleaser/goreleaser-action@v5\n        with:\n          distribution: goreleaser\n          version: latest\n          args: release --clean\n        env:\n          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nvar (\n\tversion = \"dev\"\n\tcommit  = \"none\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/version\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Version: %s, Commit: %s\\n\", version, commit)\n\t})\n\tfmt.Printf(\"K8s Service v%s (%s) running...\\n\", version, commit)\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "GoReleaser через вызовы `git describe --tags --exact-match` считывает текущий тег. \n\nОн компилирует бинарники и затем использует `docker buildx` для формирования OCI-образа, передавая скомпилированный бинарник внутрь контекста сборки. Это исключает необходимость запуска компилятора Go внутри самого Dockerfile.",
    "pitfalls": "1. Забытый `fetch-depth: 0`: Git-клон будет неполным, и GoReleaser не сможет сопоставить тег.\n2. Неверные права `GITHUB_TOKEN`: сборка завершится с ошибкой 403 при выгрузке пакетов в GHCR.\n3. Отсутствие `.dockerignore`: случайная загрузка гигабайтов локальных файлов в контекст Docker.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем преимущество сборки Docker-образов через GoReleaser по сравнению со сборкой внутри multi-stage Dockerfile в CI?\n**Ответ:** При сборке через GoReleaser компиляция бинарников Go выполняется один раз на мощном хосте раннера CI с нативным параллелизмом и кэшем. Затем готовые бинарники просто копируются в минимальные контейнеры (`scratch` / `alpine`). В multi-stage Dockerfile компиляция повторяется внутри контейнера для каждого образа, что тратит в 2-3 раза больше времени и ресурсов CPU."
  },
  {
    "num": 7,
    "title": "Анатомия манифеста Deployment: селекторы, шаблоны подов и применение",
    "task": "Напиши **Deployment manifest**: `apiVersion: apps/v1`, `kind: Deployment`. `replicas: 3`, `selector: matchLabels: app: myapp`. `template: spec: containers: - name: app, image: myapp:v1, ports: - containerPort: 8080`. Примени: `kubectl apply -f deployment.yml`.",
    "theory": "Манифест `Deployment` (`apiVersion: apps/v1`) — основа запуска масштабируемых stateless-сервисов в Kubernetes:\n- `spec.replicas`: целевое количество экземпляров (подов).\n- `spec.selector.matchLabels`: селектор, по которому контроллер определяет, какие поды принадлежат данному Deployment.\n- `spec.template`: шаблон (Pod Template), по которому создаются новые поды при масштабировании или обновлении.\n- `spec.template.metadata.labels`: метки, которые обязаны строго совпадать с селектором `matchLabels`.\n- `spec.template.spec.containers`: спецификация контейнеров, их образов, портов и переменных.",
    "step_by_step": "1. Создайте манифест `deployment.yaml`.\n2. Задайте `replicas: 3` и селектор `matchLabels: app: myapp`.\n3. Опишите контейнер `myapp:v1` с портом 8080.\n4. Примените манифест: `kubectl apply -f deployment.yaml`.\n5. Проверьте запуск подов: `kubectl get pods -o wide`.",
    "code_blocks": [
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp-deployment\n  labels:\n    app: myapp\nspec:\n  replicas: 3\n  selector:\n    matchLabels:\n      app: myapp\n  template:\n    metadata:\n      labels:\n        app: myapp\n    spec:\n      containers:\n        - name: app\n          image: myapp:v1\n          ports:\n            - containerPort: 8080"
      },
      {
        "filename": "commands.sh",
        "lang": "bash",
        "code": "# Применение манифеста\nkubectl apply -f deployment.yaml\n\n# Проверка созданных ресурсов\nkubectl get deployments\nkubectl get replicasets\nkubectl get pods -l app=myapp"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\t_, _ = w.Write([]byte(\"Hello from myapp:v1 Pod!\"))\n\t})\n\tfmt.Println(\"Сервер слушает на :8080\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "Когда `kubectl apply` отправляет YAML в API Server, `DeploymentController` создает объект `ReplicaSet` с хэшем шаблона пода в имени (например, `myapp-deployment-7569b9b5f5`). \n\nЗатем `ReplicaSetController` видит, что `desired=3`, а `current=0`, и отправляет 3 запроса на создание `Pod` в API Server. Планировщик `kube-scheduler` находит подходящие рабочие ноды с достаточным количеством ресурсов и связывает поды с нодами (`Binding`). Демон `kubelet` на каждой ноде скачивает образ и запускает контейнеры.",
    "pitfalls": "1. Изменение `matchLabels` в существующем Deployment: поле `selector` неизменяемо (immutable) после создания, попытка его изменить вызовет ошибку валидации K8s API.\n2. Несовпадение `template.metadata.labels` и `selector.matchLabels`: K8s API отклонит манифест с ошибкой `selector does not match template labels`.\n3. Отсутствие ограничений ресурсов: один сбойный под может занять 100% памяти ноды и вызвать падение соседних системных компонентов.",
    "bigtech_interview": "**Вопрос с собеседования:** Чем Deployment отличается от ReplicaSet и почему разработчики почти никогда не создают ReplicaSet напрямую?\n**Ответ:** `ReplicaSet` умеет только одно: поддерживать заданное количество одинаковых подов. Он не умеет выполнять плавное обновление (Rolling Update) с нулевым простоем, откат к предыдущим версиям (Rollback) и канареечный деплой. \n`Deployment` — это контроллер высшего порядка: при обновлении версии образа он создает **новый ReplicaSet**, постепенно увеличивая число его реплик от 0 до 3 и одновременно уменьшая число реплик старого ReplicaSet от 3 до 0. Вся история ревизий версий управляется именно Deployment."
  },
  {
    "num": 8,
    "title": "Внутренняя балансировка нагрузки через Service (ClusterIP)",
    "task": "Напиши **Service manifest**: `kind: Service`, `type: ClusterIP`, `selector: app: myapp`, `ports: - port: 80, targetPort: 8080`. Покажи internal load balancing между pods.",
    "theory": "Каждый Pod в Kubernetes имеет собственный IP-адрес. Однако этот IP эфемерный: при падении пода, рестарте ноды или деплое новой версии создаются новые поды с совершенно новыми IP.\n\nРесурс **`Service` типа `ClusterIP`**:\n- Выделяет стабильный внутренний IP-адрес (`ClusterIP`) и DNS-имя в пространстве `cluster.local`.\n- Непрерывно отслеживает поды с помощью селектора `app: myapp`.\n- Выполняет внутреннюю балансировку нагрузки между подами на транспортном уровне (L4 TCP/UDP).\n- Другие микросервисы в кластере обращаются к сервису по стабильному DNS-имени: `http://myapp-service:80`.",
    "step_by_step": "1. Создайте манифест `service.yaml` с `type: ClusterIP`.\n2. Направьте входящий трафик с `port: 80` на `targetPort: 8080`.\n3. Примените манифест: `kubectl apply -f service.yaml`.\n4. Проверьте созданный объект Endpoints: `kubectl get endpoints myapp-service`.\n5. Выполните запрос из временного контейнера: `kubectl run test --rm -it --image=alpine -- wget -qO- http://myapp-service`.",
    "code_blocks": [
      {
        "filename": "service.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Service\nmetadata:\n  name: myapp-service\n  labels:\n    app: myapp\nspec:\n  type: ClusterIP\n  selector:\n    app: myapp\n  ports:\n    - name: http\n      protocol: TCP\n      port: 80\n      targetPort: 8080"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\tpodName, _ := os.Hostname()\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Запрос обработан репликой: %s\\n\", podName)\n\t})\n\n\tfmt.Println(\"Микросервис ожидает запросы на :8080\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      },
      {
        "filename": "test-lb.sh",
        "lang": "bash",
        "code": "# Проверка балансировки: запросы распределяются между разными репликами\nfor i in $(seq 1 5); do\n  curl -s http://myapp-service\ndone"
      }
    ],
    "under_the_hood": "Virtual IP (`ClusterIP`) физически не существует на сетевых интерфейсах хоста. CoreDNS кластера сопоставляет имя `myapp-service.default.svc.cluster.local` с этим виртуальным IP. \n\nКогда пакет отправляется на ClusterIP, сетевой стек ядра хоста перехватывает его через правила DNAT (Destination NAT), сгенерированные `kube-proxy` в таблице `iptables` (цепочка `KUBE-SERVICES` -> `KUBE-SVC-XXX` -> `KUBE-SEP-XXX`). Ядро случайным образом подменяет ClusterIP на реальный IP одного из подов.",
    "pitfalls": "1. Сервис балансирует только на уровне TCP-соединений (L4): при постоянном HTTP/2 или gRPC соединении все запросы пойдут в один и тот же под. Для балансировки gRPC требуется Service Mesh или L7 Ingress.\n2. Трафик идет на не готовые поды: если не настроена `readinessProbe`, трафик начнет поступать на под до инициализации приложения.\n3. Опечатка в `targetPort`: сервис вернет ошибку таймаута или сброс соединения.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему gRPC трафик плохо балансируется стандартным Kubernetes Service (ClusterIP) и как решается эта проблема?\n**Ответ:** gRPC работает поверх протокола HTTP/2, который мультиплексирует сотни RPC-запросов внутри **одного долгоживущего TCP-соединения**. Kube-proxy балансирует на уровне L4 (TCP сокетов): он открывает одно соединение к одному поду, и все последующие тысячи gRPC-запросов уходят в этот единственный под, перегружая его. \nРешения:\n1. **Client-side load balancing:** Использование Headless Service (`clusterIP: None`) и резолвера DNS в Go gRPC клиенте (`grpc.Dial(\"dns:///service:50051\")`).\n2. **L7 Проксирование:** Использование Service Mesh (Envoy/Istio) или Envoy Ingress, балансирующего каждый отдельный gRPC-вызов (L7 stream)."
  },
  {
    "num": 9,
    "title": "Экстернализация конфигурации через ConfigMap и envFrom",
    "task": "Напиши **ConfigMap**: `kind: ConfigMap`, `data: DATABASE_URL: postgres://...`, `LOG_LEVEL: info`. Подключи в pod: `envFrom: - configMapRef: name: app-config`. Покажи externalized configuration.",
    "theory": "Хардкод конфигураций (адреса брокеров, уровни логов, таймауты) в бинарнике нарушает гибкость эксплуатации. Контейнер должен оставаться одинаковым для dev, staging и production, меняться должна только конфигурация.\n\n`ConfigMap`:\n- Хранит пары ключ-значение в поле `data`.\n- Директива `envFrom: - configMapRef: name: app-config` автоматически преобразует каждую запись `data` в переменную окружения контейнера с тем же именем.\n- В коде Go параметры считываются через `os.Getenv` с возможностью задания значений по умолчанию.",
    "step_by_step": "1. Создайте манифест `configmap.yaml` с параметрами `DATABASE_URL` и `LOG_LEVEL`.\n2. Опишите `deployment.yaml` с `envFrom: - configMapRef: name: app-config`.\n3. В коде Go напишите функцию чтения конфигурации с дефолтными значениями.\n4. Примените манифесты: `kubectl apply -f configmap.yaml -f deployment.yaml`.\n5. Проверьте логи пода: `kubectl logs -l app=config-demo`.",
    "code_blocks": [
      {
        "filename": "configmap.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: app-config\ndata:\n  DATABASE_URL: \"postgres://user:pass@pg-cluster.database.svc:5432/orders?sslmode=disable\"\n  LOG_LEVEL: \"info\"\n  MAX_CONNECTIONS: \"50\" "
      },
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: config-demo\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: config-demo\n  template:\n    metadata:\n      labels:\n        app: config-demo\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/config-demo:v1.0.0\n          envFrom:\n            - configMapRef:\n                name: app-config"
      },
      {
        "filename": "config.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n)\n\ntype Config struct {\n\tDatabaseURL string\n\tLogLevel    string\n\tMaxConns    string\n}\n\nfunc LoadConfig() Config {\n\treturn Config{\n\t\tDatabaseURL: getEnv(\"DATABASE_URL\", \"postgres://localhost:5432/dev\"),\n\t\tLogLevel:    getEnv(\"LOG_LEVEL\", \"debug\"),\n\t\tMaxConns:    getEnv(\"MAX_CONNECTIONS\", \"10\"),\n\t}\n}\n\nfunc getEnv(key, defaultVal string) string {\n\tif val := os.Getenv(key); val != \"\" {\n\t\treturn val\n\t}\n\treturn defaultVal\n}\n\nfunc main() {\n\tcfg := LoadConfig()\n\tfmt.Printf(\"Конфигурация успешно загружена:\\n- DB: %s\\n- LogLevel: %s\\n- MaxConns: %s\\n\",\n\t\tcfg.DatabaseURL, cfg.LogLevel, cfg.MaxConns)\n}"
      }
    ],
    "under_the_hood": "При планировании пода Kubelet валидирует наличие указанного `ConfigMap` в namespace. Если ConfigMap не существует, под зависает в статусе `CreateContainerConfigError`. \n\nПосле успешной валидации Kubelet парсит словарь `data` и передает его в системную структуру создания контейнера. Имена ключей должны строго соответствовать формату C-идентификаторов (`[-._a-zA-Z][-._a-zA-Z0-9]*`).",
    "pitfalls": "1. Опечатка в имени ConfigMap: под упадет в `CreateContainerConfigError` и не запустится.\n2. Недопустимые символы в ключах (например, слэш `/`): переменная окружения с некорректным именем будет отброшена операционной системой Linux.\n3. Отсутствие fallback (значений по умолчанию) в коде Go: сервис падает с nil pointer или паникой, если переменная не задана в dev-окружении.",
    "bigtech_interview": "**Вопрос с собеседования:** В каких случаях передача параметров через переменные окружения (`envFrom`) хуже, чем монтирование ConfigMap в виде файла (`volumeMounts`)?\n**Ответ:** \n1. **Динамическое обновление (Hot Reload):** Изменение ConfigMap, смонтированного как файл в том (volume), обновляется на файловой системе пода демоном Kubelet автоматически в течение 1 минуты. Переменные окружения процесса обновлены быть не могут (требуется полный рестарт пода).\n2. **Сложные и структурированные конфигурации:** Большие конфигурационные файлы (JSON, YAML, Nginx config) неудобно и небезопасно передавать через переменные окружения из-за ограничений оболочки на размер командной строки и спецсимволы."
  },
  {
    "num": 10,
    "title": "Минимальный Pod манифест для Go-приложения",
    "task": "Создайте минимальный **Pod** манифест для вашего Go-приложения. Запустите через `kubectl apply`.",
    "theory": "`Pod` (Под) — наименьшая развертываемая вычислительная единица в Kubernetes.\n\nПод представляет собой группу из одного или нескольких контейнеров, разделяющих:\n- Общее сетевое пространство имен (Network Namespace) — контейнеры имеют один IP-адрес и могут общаться между собой через `localhost`.\n- Общее хранилище (Shared Volumes).\n- Общее пространство межпроцессного взаимодействия (IPC).\n\nХотя в продакшне поды запускаются через `Deployment`, понимание манифеста одиночного `Pod` (`apiVersion: v1`) критично для отладки и глубокого понимания модели K8s.",
    "step_by_step": "1. Создайте файл манифеста `pod.yaml` с `kind: Pod`.\n2. Задайте имя пода и спецификацию контейнера с образом Go-приложения.\n3. Примените манифест: `kubectl apply -f pod.yaml`.\n4. Проверьте статус пода: `kubectl get pods`.\n5. Посмотрите логи запущенного пода: `kubectl logs my-go-pod`.",
    "code_blocks": [
      {
        "filename": "pod.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Pod\nmetadata:\n  name: my-go-pod\n  labels:\n    app: demo\nspec:\n  restartPolicy: Always\n  containers:\n    - name: web-server\n      image: alpine:3.21\n      command: [\"/bin/sh\", \"-c\"]\n      args:\n        - |\n          echo \"Минимальный под на Go запущен!\"\n          while true; do sleep 3600; done\n      ports:\n        - containerPort: 8080"
      },
      {
        "filename": "commands.sh",
        "lang": "bash",
        "code": "# Создание пода\nkubectl apply -f pod.yaml\n\n# Просмотр детальной информации о поде\nkubectl describe pod my-go-pod\n\n# Просмотр логов контейнера\nkubectl logs my-go-pod\n\n# Удаление пода\nkubectl delete pod my-go-pod"
      }
    ],
    "under_the_hood": "При создании пода рантайм контейнеров (containerd) первым делом запускает специальный скрытый контейнер — **Pause Container** (`k8s.gcr.io/pause`). \n\nPause Container удерживает открытыми сетевые неймспейсы ядра Linux (`netns`). Все остальные пользовательские контейнеры этого пода присоединяются к неймспейсу Pause-контейнера через флаг ядра `--net=container:<pause_id>`. Это обеспечивает единый IP-адрес для всех контейнеров пода.",
    "pitfalls": "1. Запуск подов напрямую в продакшне: если нода с одиночным подом перезагрузится или упадет, под не будет восстановлен.\n2. Конфликт портов: два контейнера внутри одного пода не могут слушать один и тот же порт (например, оба слушают 8080), так как они делят один сетевой стек `localhost`.\n3. `restartPolicy: Always` для одноразовых задач: завершившийся контейнер будет перезапускаться бесконечно (CrashLoopBackOff).",
    "bigtech_interview": "**Вопрос с собеседования:** Какую роль выполняет `pause` контейнер внутри Kubernetes Pod?\n**Ответ:** Pause контейнер выполняет две ключевые функции:\n1. **Удержание пространств имен (Namespaces Anchor):** Он инициализирует сетевой стек (IP-адрес, сетевые интерфейсы, таблицы маршрутизации) и IPC-пространство пода. Если пользовательские контейнеры перезапускаются или падают, сетевой интерфейс и IP пода не теряются, потому что Pause контейнер продолжает жить.\n2. **Роль PID 1 (Zombie Reaper):** В Linux процесс с PID 1 обязан собирать дочерние зомби-процессы (`wait()`). Если включено разделение PID namespace между контейнерами, pause-контейнер предотвращает утечки таблицы процессов ядра."
  },
  {
    "num": 11,
    "title": "Управление секретами: Opaque Secret, stringData и secretKeyRef",
    "task": "Напиши **Secret**: `kind: Secret`, `type: Opaque`, `stringData: DB_PASSWORD: secret123`. Base64 encoding автоматический. Подключи: `env: - name: DB_PASSWORD, valueFrom: secretKeyRef: name: app-secrets, key: DB_PASSWORD`. Покажи secrets management (но не для production — use external secrets operator).",
    "theory": "Манифест `Secret` (`apiVersion: v1`, `type: Opaque`) предназначен для хранения конфиденциальных данных.\n\nСпособы описания секретов:\n- `data`: значения обязаны быть предварительно закодированы в формат Base64.\n- `stringData`: позволяет задавать значения открытым текстом в YAML. При отправке в K8s API сервер автоматически преобразует их в Base64.\n\nПодключение секрета в контейнер:\nДиректива `valueFrom.secretKeyRef` позволяет связать конкретную переменную окружения контейнера с определенным ключом секрета. Для продакшн-окружений рекомендуется применять внешние операторы секретов (External Secrets Operator / Vault).",
    "step_by_step": "1. Создайте манифест `secret.yaml` с полем `stringData`.\n2. Добавьте секрет `DB_PASSWORD: secret123`.\n3. В `pod.yaml` подключите переменную окружения через `secretKeyRef`.\n4. В коде Go прочитайте переменную `os.Getenv(\"DB_PASSWORD\")`.\n5. Примените манифесты и проверьте успешный доступ к секрету.",
    "code_blocks": [
      {
        "filename": "secret.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Secret\nmetadata:\n  name: app-secrets\ntype: Opaque\nstringData:\n  DB_PASSWORD: \"SuperSecretPassword2026!\"\n  API_KEY: \"prod_live_abcdef123456\" "
      },
      {
        "filename": "pod-secret.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Pod\nmetadata:\n  name: secure-app\nspec:\n  containers:\n    - name: app\n      image: alpine:3.21\n      command: [\"/bin/sh\", \"-c\"]\n      args:\n        - |\n          echo \"Под запущен. Длина пароля: ${#DB_PASSWORD} символов.\"\n          sleep 3600\n      env:\n        - name: DB_PASSWORD\n          valueFrom:\n            secretKeyRef:\n              name: app-secrets\n              key: DB_PASSWORD"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n)\n\nfunc main() {\n\tpass := os.Getenv(\"DB_PASSWORD\")\n\tif pass == \"\" {\n\t\tpanic(\"DB_PASSWORD не обнаружен в переменных окружения\")\n\t}\n\tfmt.Printf(\"Успешно получен секрет БД (длина: %d симв.)\\n\", len(pass))\n}"
      }
    ],
    "under_the_hood": "Когда K8s API Server принимает манифест со `stringData`, он кодирует каждое строковое значение в Base64 и сохраняет результат в поле `data` объекта etcd. \n\nПри создании пода Kubelet монтирует секрет в оперативную память (RAM `tmpfs`) ноды или передает его в переменные процесса контейнера, исключая запись секретов на физический жесткий диск ноды.",
    "pitfalls": "1. Коммит `secret.yaml` со `stringData` в публичный Git-репозиторий: компрометация паролей.\n2. Путаница между шифрованием и Base64: любой пользователь с правами чтения `kubectl get secret app-secrets -o yaml` может декодировать пароль командой `base64 -d`.\n3. Опечатка в поле `key`: под упадет в статус `CreateContainerConfigError`.",
    "bigtech_interview": "**Вопрос с собеседования:** Как включить настоящее шифрование секретов в покое (Encryption at Rest) для etcd в Kubernetes?\n**Ответ:** По умолчанию etcd хранит данные в открытом виде. Для шифрования создается файл конфигурации `EncryptionConfiguration`, в котором объявляется провайдер шифрования (например, `aescbc` или `kms` с интеграцией с AWS KMS / Vault / Google Cloud KMS). \nЭтот конфиг передается флагу K8s API Server `--encryption-provider-config`. После этого все объекты `Secret` шифруются симметричным ключом перед записью на диск etcd."
  },
  {
    "num": 12,
    "title": "Самоисцеление (Self-Healing) и декларативное состояние в Deployment",
    "task": "Создайте **Deployment** с 3 репликами. Изучите, как K8s поддерживает желаемое состояние.",
    "theory": "Центральная концепция Kubernetes — **Reconciliation Loop (Цикл сверки)**:\n- Система непрерывно сравнивает **Желаемое состояние (Desired State)**, описанное в манифесте (`replicas: 3`), с **Текущим состоянием (Current / Live State)** в кластере.\n- Если разработчик вручную удалит под (`kubectl delete pod ...`) или физическая нода выйдет из строя, `ReplicaSetController` мгновенно обнаружит, что текущее число подов стало равным 2 вместо 3, и автоматически создаст новый под на исправной ноде.\n- Это гарантирует отказоустойчивость (Self-healing) и доступность сервиса без участия дежурных инженеров.",
    "step_by_step": "1. Создайте `deployment.yaml` с 3 репликами.\n2. Примените манифест и убедитесь в наличии 3 работающих подов.\n3. Симулируйте аварию: принудительно удалите один из подов через `kubectl delete pod <name>`.\n4. Наблюдайте в реальном времени, как контроллер создает новый под взамен удаленного.\n5. Проверьте события через `kubectl get events --sort-by=.metadata.creationTimestamp`.",
    "code_blocks": [
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: resilient-service\n  labels:\n    app: resilient\nspec:\n  replicas: 3\n  selector:\n    matchLabels:\n      app: resilient\n  template:\n    metadata:\n      labels:\n        app: resilient\n    spec:\n      containers:\n        - name: app\n          image: alpine:3.21\n          command: [\"/bin/sh\", \"-c\", \"sleep 3600\"]"
      },
      {
        "filename": "demo-self-heal.sh",
        "lang": "bash",
        "code": "# 1. Запуск деплоймента\nkubectl apply -f deployment.yaml\n\n# 2. Получение списка подов\nkubectl get pods -l app=resilient\n\n# 3. Принудительное удаление одного пода\nPOD_TO_KILL=$(kubectl get pods -l app=resilient -o jsonpath='{.items[0].metadata.name}')\necho \"Удаляем под: $POD_TO_KILL\"\nkubectl delete pod $POD_TO_KILL\n\n# 4. Проверка: K8s моментально создал новый под взамен!\nkubectl get pods -l app=resilient"
      }
    ],
    "under_the_hood": "`ReplicaSetController` слушает события API-сервера через механизм HTTP/2 Watch API. \n\nПри получении события `DELETED` для пода, входящего в селектор контроллера, функция `syncReplicaSet()` вычисляет разницу:\n`diff = desiredReplicas - currentReplicas`\nЕсли `diff > 0`, контроллер немедленно отправляет вызов `POST /api/v1/namespaces/default/pods`, инициируя создание нового пода.",
    "pitfalls": "1. Попытка восстановить упавший под вручную: не требуется, контроллер сделает это автоматически быстрее человека.\n2. Нехватка ресурсов на нодах (Pending pod): контроллер создаст под в etcd, но планировщик `kube-scheduler` не сможет назначить его на ноду из-за нехватки CPU/памяти.\n3. Ошибки в `restartPolicy`: для контроллеров `Deployment` допустима только политика `restartPolicy: Always`.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между `Edge-triggered` и `Level-triggered` моделями управления в распределенных системах, и почему Kubernetes построен на Level-triggered подходе?\n**Ответ:** \n- **Edge-triggered:** Реакция происходит строго на факт изменения (дельта-событие: «под удален»). Если в сети произошел сбой или брокер сообщений потерял пакет события, система навсегда останется в рассинхронизированном состоянии.\n- **Level-triggered:** Контроллер оперирует абсолютным текущим состоянием (уровень: «в системе сейчас 2 пода, а нужно 3»). Даже если сотни событий были потеряны при сбое сети, на следующем цикле сверки контроллер сравнит желаемое число с реальным и устранит разрыв. Это делает Kubernetes предельно устойчивым к сетевым сбоям."
  },
  {
    "num": 13,
    "title": "Связка Deployment, Service и ConfigMap с ограничением ресурсов (Requests/Limits)",
    "task": "Создайте Kubernetes манифесты: `Deployment`, `Service`, `ConfigMap` для вашего приложения. Настройте количество реплик и ресурсы (requests/limits).",
    "theory": "Комплексный манифест микросервиса объединяет вычисления (`Deployment`), сетевую балансировку (`Service`) и конфигурацию (`ConfigMap`), дополненные обязательными спецификациями ресурсов:\n- **`requests`:** Гарантированный минимум ресурсов CPU и памяти, резервируемый планировщиком `kube-scheduler` на ноде при размещении пода.\n- **`limits`:** Жесткий потолок потребления ресурсов:\n  - При превышении Memory limit ядро Linux уничтожает контейнер по **OOMKilled** (Out of Memory, Exit code 137).\n  - При превышении CPU limit контейнер не убивается, а подвергается **троттлингу** (CPU Throttling) через CFS-квоты ядра.",
    "step_by_step": "1. Создайте манифест `all-in-one.yaml`, объединяющий `ConfigMap`, `Deployment` и `Service`.\n2. Задайте `resources.requests: cpu: 100m, memory: 128Mi`.\n3. Задайте `resources.limits: cpu: 500m, memory: 256Mi`.\n4. Примените манифест: `kubectl apply -f all-in-one.yaml`.\n5. Проверьте выделенные ресурсы: `kubectl describe pod -l app=microservice`.",
    "code_blocks": [
      {
        "filename": "all-in-one.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: microservice-cfg\ndata:\n  APP_ENV: \"staging\"\n  PORT: \"8080\"\n---\napiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: microservice-dep\nspec:\n  replicas: 2\n  selector:\n    matchLabels:\n      app: microservice\n  template:\n    metadata:\n      labels:\n        app: microservice\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/microservice:v1.0.0\n          envFrom:\n            - configMapRef:\n                name: microservice-cfg\n          resources:\n            requests:\n              cpu: \"100m\"\n              memory: \"128Mi\"\n            limits:\n              cpu: \"500m\"\n              memory: \"256Mi\"\n          ports:\n            - containerPort: 8080\n---\napiVersion: v1\nkind: Service\nmetadata:\n  name: microservice-svc\nspec:\n  type: ClusterIP\n  selector:\n    app: microservice\n  ports:\n    - port: 80\n      targetPort: 8080"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\tport := os.Getenv(\"PORT\")\n\tif port == \"\" {\n\t\tport = \"8080\"\n\t}\n\tenv := os.Getenv(\"APP_ENV\")\n\n\thttp.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"OK\"))\n\t})\n\n\tfmt.Printf(\"Микросервис запущен в среде [%s] на порту :%s\\n\", env, port)\n\t_ = http.ListenAndServe(\":\"+port, nil)\n}"
      }
    ],
    "under_the_hood": "`kube-scheduler` суммирует `requests` всех подов на ноде. Если на сервере свободно 200m CPU, а под запрашивает 250m, под не будет туда запланирован. \n\nЗначения `limits` транслируются в cgroups v2:\n- Memory limit -> `memory.max`\n- CPU limit -> `cpu.max` (например, `50000 100000` означает максимум 50 мс процессорного времени за 100 мс период CFS).",
    "pitfalls": "1. Запуск без `requests`: Kubelet помещает под в класс качества `BestEffort`. При нехватке памяти на ноде такие поды выселяются (evicted) в первую очередь.\n2. Недостаточный лимит памяти: приложение упадет с OOMKilled при кратковременном всплеске аллокаций в Go.\n3. Использование суффикса `M` вместо `Mi`: `128M` = $128 \\times 10^6$ байт, `128Mi` = $128 \\times 2^{20}$ байт.",
    "bigtech_interview": "**Вопрос с собеседования:** Что такое классы QoS (Quality of Service) в Kubernetes и как они определяются?\n**Ответ:** K8s автоматически присваивает поду один из трех классов QoS на основе requests и limits:\n1. **Guaranteed:** У каждого контейнера `requests == limits` для CPU и памяти. Наивысший приоритет, выселяются последними при деградации ноды.\n2. **Burstable:** `requests < limits` или заданы только requests. Могут временно потреблять больше минимума, выселяются во вторую очередь.\n3. **BestEffort:** `requests` и `limits` не заданы вообще. Низший приоритет, ядро Linux убивает их первыми при давлении на память (Node Memory Pressure)."
  },
  {
    "num": 14,
    "title": "Настройка диагностических проб: Liveness и Readiness Probes в веб-сервере Go",
    "task": "**Настройка Liveness и Readiness Probes**: Интегрируйте в веб-сервер Go два диагностических эндпоинта:\n    * `/live` (Liveness) — возвращает статус `200 OK`, если приложение просто запущено и не зависло мертвой блокировкой.\n    * `/ready` (Readiness) — возвращает `200 OK` только тогда, когда приложение успешно установило соединение с БД и готово обрабатывать трафик пользователей.\n    Пропишите опрос этих эндпоинтов в K8s-манифесте пода в секциях `livenessProbe` и `readinessProbe`.",
    "theory": "Пробы (Probes) — механизм контроля жизнедеятельности подов со стороны Kubelet:\n1. **`livenessProbe` (Проба живучести):** Проверяет, что процесс приложения жив и не заблокирован взаимной блокировкой (deadlock). Если эндпоинт `/live` не отвечает или возвращает статус $\\ge 400$, Kubelet **перезапускает контейнер**.\n2. **`readinessProbe` (Проба готовности):** Проверяет, готово ли приложение обрабатывать трафик (успешно ли подключение к БД, прогрет ли кэш). Если эндпоинт `/ready` возвращает ошибку, под **не перезапускается**, но временно **удаляется из балансировщика Service (Endpoints)**, предотвращая ошибки у клиентов.",
    "step_by_step": "1. Реализуйте в коде Go эндпоинты `/live` и `/ready`.\n2. В эндпоинте `/ready` добавьте проверку доступности базы данных (ping).\n3. В манифесте `deployment.yaml` сконфигурируйте секции `livenessProbe` и `readinessProbe`.\n4. Задайте параметры: `initialDelaySeconds: 5`, `periodSeconds: 10`, `timeoutSeconds: 2`.\n5. Примените манифест и проверьте пробы через `kubectl describe pod`.",
    "code_blocks": [
      {
        "filename": "probes-deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: probe-service\nspec:\n  replicas: 2\n  selector:\n    matchLabels:\n      app: probe-service\n  template:\n    metadata:\n      labels:\n        app: probe-service\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/probe-service:v1.0.0\n          ports:\n            - containerPort: 8080\n          livenessProbe:\n            httpGet:\n              path: /live\n              port: 8080\n            initialDelaySeconds: 5\n            periodSeconds: 10\n            timeoutSeconds: 2\n            failureThreshold: 3\n          readinessProbe:\n            httpGet:\n              path: /ready\n              port: 8080\n            initialDelaySeconds: 2\n            periodSeconds: 5\n            timeoutSeconds: 2\n            failureThreshold: 2"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"sync/atomic\"\n)\n\nvar isDBConnected atomic.Bool\n\nfunc main() {\n\t// Симуляция успешного подключения к БД через 3 секунды после старта\n\tgo func() {\n\t\tisDBConnected.Store(true)\n\t}()\n\n\t// Liveness: проверяет только то, что HTTP-сервер отвечает\n\thttp.HandleFunc(\"/live\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"ALIVE\"))\n\t})\n\n\t// Readiness: проверяет готовность обслуживать трафик (доступность БД)\n\thttp.HandleFunc(\"/ready\", func(w http.ResponseWriter, r *http.Request) {\n\t\tif !isDBConnected.Load() {\n\t\t\tw.WriteHeader(http.StatusServiceUnavailable)\n\t\t\t_, _ = w.Write([]byte(\"DB_DISCONNECTED\"))\n\t\t\treturn\n\t\t}\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"READY\"))\n\t})\n\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\t_, _ = w.Write([]byte(\"Бизнес-логика микросервиса\"))\n\t})\n\n\tfmt.Println(\"Сервер с диагностическими пробами слушает на :8080\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "Демон `kubelet` периодически отправляет HTTP GET-запросы на указанный порт пода. \n\nЕсли `livenessProbe` возвращает ошибку более `failureThreshold` раз подряд, Kubelet шлет процессу сигнал `SIGTERM`, ждет `terminationGracePeriodSeconds` (30 с по умолчанию) и, если процесс не завершился, убивает его через `SIGKILL`. \n\nЕсли `readinessProbe` возвращает статус `503`, контроллер EndpointSlice мгновенно вычеркивает IP пода из списка адресов балансировки `Service`.",
    "pitfalls": "1. Проверка внешних зависимостей (БД, сторонний API) в `livenessProbe`: если БД кратковременно упадет под нагрузкой, Kubelet начнет циклически убивать и перезапускать **все поды сервиса одновременно**, превращая мелкий сбой в катастрофу (Каскадный сбой / Cascading Failure). Проверка БД допустима **только в readinessProbe**!\n2. Слишком короткий `timeoutSeconds: 1` при тяжелой нагрузке: Kubelet считает пробу проваленной из-за занятости CPU приложения.\n3. Отсутствие `initialDelaySeconds`: Kubelet опрашивает под до завершения инициализации рантайма Go, вызывая ложные перезапуски.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему проверка соединения с PostgreSQL в `livenessProbe` считается критическим антипаттерном в архитектуре Kubernetes?\n**Ответ:** Цель `livenessProbe` — ответить на вопрос: «Жив ли сам процесс Go? Поможет ли ему перезапуск контейнера?». Если СУБД PostgreSQL упала или перегружена, перезапуск контейнера Go проблему с БД не решит, но создаст лавину повторных подключений к БД (Thundering Herd) и положит весь кластер. \nВнешние зависимости проверяются **исключительно в `readinessProbe`**: под помечается как «не готовый» и снимается с балансировки, но процесс спокойно ждет восстановления БД без бессмысленных панических рестартов."
  },
  {
    "num": 15,
    "title": "Поведение контейнеров при превышении Resource Requests и Limits: OOMKilled против Throttling",
    "task": "Добавьте **Resource requests и limits** для CPU и memory. Что произойдёт при превышении limits? (OOMKilled для memory, throttling для CPU).",
    "theory": "Разница в механике превышения процессорных и оперативных лимитов обусловлена природой ресурсов:\n1. **Память (Compressible vs Incompressible):** Память нельзя сжать во времени. Если контейнер превышает `limits.memory`, ядро Linux не может временно «замедлить» выделение ОЗУ и вызывает механизм Out-Of-Memory Killer (**OOM Killer**). Процесс немедленно уничтожается сигналом `SIGKILL` (код возврата **137**, статус **OOMKilled**).\n2. **Процессор (Compressible Resource):** Процессорное время сжимаемо. При превышении `limits.cpu` контейнер **никогда не убивается**. Планировщик Completely Fair Scheduler (CFS) ядра Linux временно отбирает у потоков контейнера кванты времени процессора до наступления следующего периода (100 мс). Это называется **CPU Throttling** — приложение начинает резко тормозить, а latency запросов взлетает в 10 раз.",
    "step_by_step": "1. Создайте код на Go, симулирующий постепенную утечку памяти.\n2. В манифесте `Deployment` задайте жесткий лимит памяти `limits.memory: 64Mi`.\n3. Запустите контейнер в кластере.\n4. Дождитесь аварийного падения и проверьте статус: `kubectl get pods`.\n5. Изучите причину завершения через `kubectl describe pod` (найдите запись `OOMKilled: true, Exit Code: 137`).",
    "code_blocks": [
      {
        "filename": "oom-deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: oom-test\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: oom-test\n  template:\n    metadata:\n      labels:\n        app: oom-test\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/oom-test:v1.0.0\n          resources:\n            requests:\n              memory: \"32Mi\"\n              cpu: \"100m\"\n            limits:\n              memory: \"64Mi\"\n              cpu: \"200m\" "
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"time\"\n)\n\nfunc main() {\n\tfmt.Println(\"Запуск симулятора утечки памяти...\")\n\tvar leak [][]byte\n\n\tfor {\n\t\t// Аллокация 10 МБ каждые 500 миллисекунд\n\t\tchunk := make([]byte, 10*1024*1024)\n\t\tfor i := range chunk {\n\t\t\tchunk[i] = 1 // Принудительное касание страниц памяти (RSS)\n\t\t}\n\t\tleak = append(leak, chunk)\n\n\t\tvar m runtime.MemStats\n\t\truntime.ReadMemStats(&m)\n\t\tfmt.Printf(\"Выделено памяти: %d МБ\\n\", m.Alloc/1024/1024)\n\t\ttime.Sleep(500 * time.Millisecond)\n\t}\n}"
      },
      {
        "filename": "check-oom.sh",
        "lang": "bash",
        "code": "# Просмотр статуса завершения контейнера\nkubectl get pod -l app=oom-test\n\n# Детальный вывод причины падения\nkubectl describe pod -l app=oom-test | grep -E \"Terminated|Exit Code|Reason\"\n# Вывод:\n#   Last State:     Terminated\n#     Reason:       OOMKilled\n#     Exit Code:    137"
      }
    ],
    "under_the_hood": "Ядро Linux отслеживает потребление Resident Set Size (RSS) в подсистеме cgroups (`memory.current`). Когда значение достигает `memory.max` (лимита 64Mi), ядро пытается очистить page cache. \n\nЕсли свободной памяти не остается, ядро выбирает процесс с наибольшим `oom_score` внутри контрольной группы и шлет ему системный сигнал `SIGKILL` (сигнал номер 9; в Linux код завершения по сигналу равен $128 + 9 = 137$). Перехватить или обработать `SIGKILL` в Go-коде невозможно.",
    "pitfalls": "1. Задание слишком тесных memory limits: сборщик мусора Go (GC) запускается при удвоении кучи (`GOGC=100`). Если лимит 64 МБ, а сервис на пике потребляет 35 МБ, GC не успеет сработать, и под упадет по OOMKilled. Запас лимита памяти должен быть не менее 30-50%.\n2. Путаница между CPU throttling и OOM: когда сервис тормозит, часто ошибочно думают на плохую сеть, хотя причиной является агрессивный CPU limit.\n3. Отсутствие мониторинга метрики `container_cpu_cfs_throttled_periods_total` в Prometheus.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему многие HighLoad компании (включая команды инженеров Uber и Google) рекомендуют полностью отключать CPU Limits (`limits.cpu`) в production Kubernetes, оставляя только `requests.cpu`?\n**Ответ:** CFS Quota в ядре Linux работает дискретными периодами по 100 мс. Если контейнеру выделен лимит в 1 CPU, это значит, что ему разрешено суммарно работать 100 мс за период. Если многопоточный сервис на Go запустил 8 горутин, они параллельно исчерпают эти 100 мс процессорного времени всего за 12.5 миллисекунд! \nОставшиеся 87.5 мс периода контейнер будет полностью заморожен ядром (CPU Throttling), что приводит к резким скачкам p99 latency и срыву SLA, даже если на самой физической ноде 90% процессорных мощностей простаивает."
  },
  {
    "num": 16,
    "title": "Однократные задачи в Kubernetes: манифест Job для миграций базы данных",
    "task": "Напиши **Job**: `kind: Job`, `template: spec: restartPolicy: OnFailure`, `containers: - command: [\"./migrate\", \"up\"]`. Запускается один раз, до completion. Покажи database migrations as K8s Job.",
    "theory": "В отличие от `Deployment`, поды которого обязаны работать непрерывно, задачи вроде миграций БД, генерации отчетов или бэкапов должны выполниться ровно один раз и завершиться с кодом 0.\n\nРесурс **`Job` (`apiVersion: batch/v1`)**:\n- Создает один или несколько подов и следит за их успешным завершением (`Completed`).\n- При падении (`Exit code != 0`) контроллер автоматически перезапускает под в соответствии с политикой `restartPolicy: OnFailure` или `Never`.\n- `backoffLimit`: максимальное количество попыток перезапуска перед тем, как Job будет помечена как проваленная (`Failed`).\n- Идеально подходит для применения миграций схемы БД (Liquibase, Goose, golang-migrate) перед стартом веб-серверов.",
    "step_by_step": "1. Создайте код утилиты миграций на Go.\n2. Опишите манифест `migration-job.yaml` с `kind: Job`.\n3. Укажите `restartPolicy: OnFailure` и `backoffLimit: 3`.\n4. Примените манифест: `kubectl apply -f migration-job.yaml`.\n5. Дождитесь статуса `Completed`: `kubectl wait --for=condition=complete job/db-migration --timeout=60s`.",
    "code_blocks": [
      {
        "filename": "migration-job.yaml",
        "lang": "yaml",
        "code": "apiVersion: batch/v1\nkind: Job\nmetadata:\n  name: db-migration\nspec:\n  backoffLimit: 3\n  ttlSecondsAfterFinished: 300 # Автоматическое удаление через 5 минут после завершения\n  template:\n    spec:\n      restartPolicy: OnFailure\n      containers:\n        - name: migrate\n          image: ghcr.io/company/db-migrator:v1.0.0\n          command: [\"/bin/migrator\", \"up\"]\n          env:\n            - name: DATABASE_URL\n              valueFrom:\n                secretKeyRef:\n                  name: db-secrets\n                  key: DSN"
      },
      {
        "filename": "migrator.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n\t\"time\"\n)\n\nfunc main() {\n\tdsn := os.Getenv(\"DATABASE_URL\")\n\tif dsn == \"\" {\n\t\tfmt.Println(\"ОШИБКА: Переменная DATABASE_URL не задана\")\n\t\tos.Exit(1)\n\t}\n\n\tfmt.Println(\"Начало применения миграций базы данных...\")\n\ttime.Sleep(2 * time.Second) // Имитация применения SQL DDL скриптов\n\n\tfmt.Println(\"Миграции схемы БД успешно применены!\")\n\tos.Exit(0)\n}"
      },
      {
        "filename": "check-job.sh",
        "lang": "bash",
        "code": "# Запуск задачи\nkubectl apply -f migration-job.yaml\n\n# Просмотр статуса Job\nkubectl get jobs\n\n# Просмотр логов пода миграций\nkubectl logs job/db-migration"
      }
    ],
    "under_the_hood": "`JobController` создает Pod. Когда процесс в контейнере завершается с кодом 0 (`Exit Code 0`), Kubelet переводит статус пода в `Succeeded`. \n\n`JobController` фиксирует условие `Complete: True`. Опция `ttlSecondsAfterFinished: 300` задействует контроллер TTL-after-finished, который через 5 минут автоматически удаляет объект Job и его завершенные поды из etcd, предотвращая засорение кластера старыми записями.",
    "pitfalls": "1. Забытый `restartPolicy: OnFailure`: по умолчанию поды используют политику `Always`, что недопустимо для Job (K8s API отклонит манифест).\n2. Запуск нескольких миграций параллельно: одновременный запуск двух реплик мигратора может заблокировать таблицы БД в дедлоке. Для Job требуется `completions: 1` и `parallelism: 1`.\n3. Отсутствие `ttlSecondsAfterFinished`: тысячи завершенных подов накапливаются в etcd, перегружая память K8s master-нод.",
    "bigtech_interview": "**Вопрос с собеседования:** Как связать выполнение K8s Job миграций с развертыванием нового релиза в Helm-чарте или GitOps?\n**Ответ:** Используются **Helm Hooks** (`helm.sh/hook: pre-install,pre-upgrade`, `helm.sh/hook-delete-policy: hook-succeeded`). \nHelm сначала применяет манифест Job миграции и ждет его успешного завершения (`Completed`). Только после успешного применения DDL-схемы Helm запускает обновление Deployment с новыми подами веб-сервера. Если миграция упала с ошибкой, Helm прерывает релиз и не обновляет рабочие поды, исключая поломку продакшна."
  },
  {
    "num": 17,
    "title": "Практическая настройка Liveness Probe через эндпоинт /healthz",
    "task": "Настройте **Liveness probe** через HTTP GET `/healthz`. K8s будет перезапускать поды, которые не отвечают.",
    "theory": "Зависание приложения из-за дедлока мьютексов (`sync.Mutex`), утечки файловых дескрипторов или зацикливания бесконечного цикла невозможно выявить стандартными средствами операционной системы: с точки зрения ядра Linux процесс жив и потребляет процессор.\n\n**`livenessProbe` через HTTP GET `/healthz`**:\n- Kubelet отправляет HTTP-запрос на порт 8080 каждые N секунд.\n- Если сервис завис в дедлоке, горутина HTTP-сервера не сможет обработать запрос и завершится по таймауту (`timeoutSeconds`).\n- После превышения лимита ошибок (`failureThreshold: 3`) Kubelet инициирует принудительный перезапуск контейнера, восстанавливая работоспособность пода.",
    "step_by_step": "1. Зарегистрируйте легковесный обработчик `/healthz` в Go.\n2. В `deployment.yaml` добавьте блок `livenessProbe`.\n3. Установите `periodSeconds: 5` и `timeoutSeconds: 2`.\n4. Разверните сервис в кластере.\n5. Протестируйте реакцию K8s на искусственный дедлок обработчика.",
    "code_blocks": [
      {
        "filename": "liveness-deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: liveness-demo\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: liveness-demo\n  template:\n    metadata:\n      labels:\n        app: liveness-demo\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/liveness-demo:v1.0.0\n          ports:\n            - containerPort: 8080\n          livenessProbe:\n            httpGet:\n              path: /healthz\n              port: 8080\n            initialDelaySeconds: 3\n            periodSeconds: 5\n            timeoutSeconds: 2\n            failureThreshold: 3"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"sync\"\n\t\"time\"\n)\n\nvar (\n\tmu      sync.Mutex\n\tblocked bool\n)\n\nfunc main() {\n\t// Обычный эндпоинт проверки жизнеспособности\n\thttp.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tmu.Lock()\n\t\tdefer mu.Unlock()\n\n\t\tif blocked {\n\t\t\t// Симуляция зависания процесса\n\t\t\ttime.Sleep(10 * time.Second)\n\t\t}\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"HEALTHY\"))\n\t})\n\n\t// Эндпоинт для намеренного вызова дедлока при тестировании\n\thttp.HandleFunc(\"/trigger-deadlock\", func(w http.ResponseWriter, r *http.Request) {\n\t\tmu.Lock()\n\t\tblocked = true\n\t\tmu.Unlock()\n\t\t_, _ = w.Write([]byte(\"Deadlock активирован. Ожидаем рестарт Kubelet...\"))\n\t})\n\n\tfmt.Println(\"Сервер слушает на :8080\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "Kubelet создает фонового исполнителя (prober worker). На каждом тике таймера (`periodSeconds`) воркер открывает TCP-сокет к IP пода, формирует HTTP-запрос `GET /healthz HTTP/1.1` и ждет ответа не более `timeoutSeconds`. \n\nЕсли HTTP-код ответа находится в диапазоне $200 \\le \\text{code} < 400$, проба считается успешной. Если происходит ошибка или ответ не пришел вовремя, внутренний счетчик ошибок инкрементируется. При `failures >= failureThreshold` вызывается функция `killContainer()` рантайма CRI.",
    "pitfalls": "1. Тяжелые вычисления в эндпоинте `/healthz`: проверка не должна обращаться к диску или тяжелым парсерам, иначе проба сама по себе перегрузит CPU.\n2. Слишком агрессивный таймаут (`timeoutSeconds: 1`): малейший Stop-the-World сборщика мусора Go (GC pause) приведет к ложному падению пробы.\n3. Отсутствие мониторинга рестартов: если сервис рестартится каждые 10 минут, это симптом критического бага в коде.",
    "bigtech_interview": "**Вопрос с собеседования:** Чем опасен бесконечный перезапуск пода Kubelet по Liveness пробе и как K8s защищает кластер от перегрузки?\n**Ответ:** Если приложение падает или зависает сразу после старта, непрерывный мгновенный рестарт вызовет 100% утилизацию CPU и переполнение логов на ноде. \nKubernetes реализует механизм экспоненциальной задержки перезапуска — **CrashLoopBackOff**: время между попытками рестарта удваивается (10s, 20s, 40s, 80s ... вплоть до максимума в 300 секунд / 5 минут), давая ноде передышку и сохраняя стабильность кластера."
  },
  {
    "num": 18,
    "title": "Практическое применение Deployment.yaml и инспекция состояния через kubectl",
    "task": "Напиши `Deployment.yaml` для своего Go-приложения (replicas: 3). Примени `kubectl apply -f`. Проверь статус подов.",
    "theory": "Уверенное владение утилитой командной строки `kubectl` — ключевой навык инженера при эксплуатации приложений в кластере Kubernetes:\n- `kubectl apply -f <file>`: декларативное применение манифеста (алгоритм 3-way merge).\n- `kubectl get pods -l <label>`: просмотр статуса, числа перезапусков (Restarts) и времени жизни (Age).\n- `kubectl describe pod <name>`: детальный аудит состояний контейнеров, событий планировщика (Events) и диагностических проб.\n- `kubectl logs -f <name>`: потоковый просмотр stdout/stderr логов контейнера.\n- `kubectl exec -it <name> -- /bin/sh`: интерактивное подключение внутрь контейнера.",
    "step_by_step": "1. Создайте манифест `deployment.yaml` с 3 репликами.\n2. Примените манифест командой `kubectl apply -f deployment.yaml`.\n3. Запросите статус развертывания: `kubectl rollout status deployment/web-demo`.\n4. Выведите список запущенных подов с расширенной информацией: `kubectl get pods -o wide`.\n5. Изучите вывод секции `Events` в `kubectl describe pod <name>`.",
    "code_blocks": [
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: web-demo\n  labels:\n    tier: frontend\nspec:\n  replicas: 3\n  selector:\n    matchLabels:\n      tier: frontend\n  template:\n    metadata:\n      labels:\n        tier: frontend\n    spec:\n      containers:\n        - name: app\n          image: alpine:3.21\n          command: [\"/bin/sh\", \"-c\", \"echo 'Web demo ready'; sleep 3600\"]\n          ports:\n            - containerPort: 8080"
      },
      {
        "filename": "inspect.sh",
        "lang": "bash",
        "code": "# 1. Применение манифеста\nkubectl apply -f deployment.yaml\n\n# 2. Ожидание завершения развертывания\nkubectl rollout status deployment/web-demo --timeout=60s\n\n# 3. Получение списка подов с IP адресами и именами нод\nkubectl get pods -l tier=frontend -o wide\n\n# 4. Просмотр логов всех реплик деплоймента одновременно\nkubectl logs -l tier=frontend --tail=20"
      }
    ],
    "under_the_hood": "Команда `kubectl apply` рассчитывает разницу (diff) между локальным YAML, текущей конфигурацией в etcd и последней примененной конфигурацией, записанной в системной аннотации `kubectl.kubernetes.io/last-applied-configuration`. \n\nЭто гарантирует, что поля, добавленные сторонними контроллерами (например, HPA или Istio sidecar injector), не будут стерты при повторном применении локального файла.",
    "pitfalls": "1. Использование `kubectl create` вместо `kubectl apply`: команда `create` падает с ошибкой, если ресурс уже существует в кластере.\n2. Игнорирование секции `Events` при статусе `Pending`: разработчик часто гадает, почему под не стартует, хотя в событиях четко написано `0/5 nodes available: insufficient cpu`.\n3. Ручная правка манифестов через `kubectl edit`: приводит к рассинхронизации кластера с кодовой базой Git (Configuration Drift).",
    "bigtech_interview": "**Вопрос с собеседования:** Что происходит под капотом K8s при выполнении команды `kubectl exec -it <pod> -- /bin/sh`?\n**Ответ:** \n1. `kubectl` отправляет HTTP POST-запрос с заголовком `Upgrade: SPDY / WebSocket` на K8s API Server.\n2. API Server проверяет права RBAC пользователя.\n3. API Server открывает стриминговое соединение с агентом `kubelet` целевой ноды.\n4. `kubelet` через интерфейс CRI вызывает метод `Exec()` демона `containerd`.\n5. `containerd` порождает процесс `/bin/sh` внутри Linux cgroups/namespaces целевого контейнера и связывает его дескрипторы pty (stdin/stdout/stderr) со стримом пользователя."
  },
  {
    "num": 19,
    "title": "Планировщик периодических задач: CronJob для бэкапов и фоновой обработки",
    "task": "Напиши **CronJob**: `kind: CronJob`, `schedule: \"0 2 * * *\"` (daily at 2 AM). `jobTemplate` для backup, cleanup, report generation. Покажи scheduled tasks in Kubernetes.",
    "theory": "Для выполнения регламентных задач по расписанию (ежедневная очистка устаревших сессий, создание резервных копий БД в 02:00 ночи, генерация аналитических отчетов) в Kubernetes используется ресурс **`CronJob` (`apiVersion: batch/v1`)**:\n- Синтаксис расписания аналогичен стандартному Linux Cron: `schedule: \"0 2 * * *\"` (минута, час, день месяца, месяц, день недели).\n- `concurrencyPolicy`: определяет поведение при наложении запусков:\n  - `Allow` (по умолчанию): задачи могут запускаться параллельно.\n  - `Forbid`: если предыдущая задача еще не завершилась, новый запуск пропускается.\n  - `Replace`: если старая задача еще работает, она отменяется, а вместо нее запускается новая.\n- `successfulJobsHistoryLimit` и `failedJobsHistoryLimit`: лимиты хранения завершенных подов.",
    "step_by_step": "1. Создайте код фоновой задачи на Go.\n2. Опишите манифест `cronjob.yaml` с расписанием `schedule: \"0 2 * * *\"`.\n3. Установите политику параллелизма `concurrencyPolicy: Forbid`.\n4. Задайте лимиты истории: `successfulJobsHistoryLimit: 3`.\n5. Примените манифест и протестируйте внеплановый запуск через `kubectl create job --from=cronjob/daily-backup test-run`.",
    "code_blocks": [
      {
        "filename": "cronjob.yaml",
        "lang": "yaml",
        "code": "apiVersion: batch/v1\nkind: CronJob\nmetadata:\n  name: daily-backup\nspec:\n  schedule: \"0 2 * * *\" # Ежедневно в 02:00 ночи UTC\n  concurrencyPolicy: Forbid\n  successfulJobsHistoryLimit: 3\n  failedJobsHistoryLimit: 1\n  jobTemplate:\n    spec:\n      template:\n        spec:\n          restartPolicy: OnFailure\n          containers:\n            - name: backup-worker\n              image: ghcr.io/company/backup-tool:v1.0.0\n              command: [\"/bin/backup\", \"--target=s3\"]\n              env:\n                - name: S3_BUCKET\n                  value: \"production-backups-archive\" "
      },
      {
        "filename": "backup.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n\t\"time\"\n)\n\nfunc main() {\n\tbucket := os.Getenv(\"S3_BUCKET\")\n\tfmt.Printf(\"[%s] Старт создания резервной копии в бакет %s...\\n\", time.Now().Format(time.RFC3339), bucket)\n\n\t// Имитация создания дампа\n\ttime.Sleep(3 * time.Second)\n\n\tfmt.Println(\"Дамп базы данных успешно загружен в S3. Задача завершена.\")\n}"
      },
      {
        "filename": "test-cron.sh",
        "lang": "bash",
        "code": "# Применение CronJob\nkubectl apply -f cronjob.yaml\n\n# Ручной запуск Job из шаблона CronJob (без ожидания 02:00 ночи)\nkubectl create job --from=cronjob/daily-backup manual-test-run\n\n# Просмотр статуса выполнения\nkubectl get jobs\nkubectl logs job/manual-test-run"
      }
    ],
    "under_the_hood": "`CronJobController` внутри `kube-controller-manager` каждые 10 секунд опрашивает зарегистрированные объекты `CronJob`. Он вычисляет время следующего запуска по локальному времени контроллера. \n\nПри наступлении назначенного времени контроллер создает дочерний объект `Job`, который в свою очередь порождает рабочий `Pod`. Политика `concurrencyPolicy: Forbid` проверяет список активных подов: если статус предыдущего пода не равен `Complete`, контроллер логирует пропуск итерации.",
    "pitfalls": "1. Неправильный часовой пояс (Timezone): исторически расписание CronJob исполнялось строго по времени мастер-нод (UTC). Начиная с K8s 1.27 доступно поле `timeZone: \"Europe/Moscow\"`.\n2. Политика `Allow` при долгих бэкапах: если бэкап завис и работает 25 часов, каждую ночь будет запускаться еще один экземпляр, что приведет к исчерпанию ресурсов ноды и базы данных.\n3. Отсутствие лимитов истории: тысячи записей завершенных задач засоряют etcd.",
    "bigtech_interview": "**Вопрос с собеседования:** Что произойдет, если нода с CronJobController перезагружалась во время планового времени срабатывания CronJob?\n**Ответ:** Поле `startingDeadlineSeconds` определяет временное окно: если контроллер был недоступен, но поднялся в пределах заданного таймаута (например, `startingDeadlineSeconds: 300` — 5 минут), он догонит расписание и немедленно запустит пропущенную задачу. Если параметр не задан, а было пропущено более 100 интервалов запуска, K8s регистрирует ошибку и больше не запускает CronJob до ручного вмешательства."
  },
  {
    "num": 20,
    "title": "Настройка Readiness Probe через эндпоинт /readyz для защиты от сбоев БД",
    "task": "Настройте **Readiness probe** через `/readyz`. K8s перестанет отправлять трафик на поды, которые не готовы (например, при недоступности БД).",
    "theory": "Главная задача **`readinessProbe`** — гарантировать, что трафик реальных пользователей направляется **только на те поды, которые прямо сейчас способны успешно его обработать**.\n\nСценарии использования эндпоинта `/readyz`:\n- **Старт сервиса:** Приложение запустило HTTP-сервер, но еще не прогрело локальный LRU-кэш или не подключилось к пулу соединений PostgreSQL. Под не должен получать трафик до статуса 200 OK.\n- **Временная недоступность внешних сервисов:** Если БД перезагружается или исчерпала лимит коннектов, эндпоинт `/readyz` возвращает статус `503 Service Unavailable`. K8s немедленно исключает под из балансировки `Service`, клиенты не получают ошибок 500, а запросы перенаправляются на другие исправные реплики.",
    "step_by_step": "1. Создайте в коде Go эндпоинт `/readyz` с реальной проверкой пинга БД (`db.PingContext`).\n2. В `deployment.yaml` настройте блок `readinessProbe`.\n3. Установите `periodSeconds: 5`, `failureThreshold: 2`.\n4. Протестируйте поведение сервиса при разрыве соединения с БД.\n5. Убедитесь, что IP пода исчезает из вывода `kubectl get endpoints`.",
    "code_blocks": [
      {
        "filename": "readiness-deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: order-service\nspec:\n  replicas: 2\n  selector:\n    matchLabels:\n      app: order-service\n  template:\n    metadata:\n      labels:\n        app: order-service\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/order-service:v1.0.0\n          ports:\n            - containerPort: 8080\n          readinessProbe:\n            httpGet:\n              path: /readyz\n              port: 8080\n            initialDelaySeconds: 2\n            periodSeconds: 5\n            timeoutSeconds: 2\n            failureThreshold: 2\n            successThreshold: 1"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"sync/atomic\"\n\t\"time\"\n)\n\ntype DatabaseMock struct {\n\thealthy atomic.Bool\n}\n\nfunc (db *DatabaseMock) Ping(ctx context.Context) error {\n\tif !db.healthy.Load() {\n\t\treturn fmt.Errorf(\"соединение с базой данных потеряно\")\n\t}\n\treturn nil\n}\n\nfunc main() {\n\tdb := &DatabaseMock{}\n\tdb.healthy.Store(true)\n\n\t// Readiness эндпоинт: проверяет возможность обработать SQL транзакции\n\thttp.HandleFunc(\"/readyz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tctx, cancel := context.WithTimeout(r.Context(), 1*time.Second)\n\t\tdefer cancel()\n\n\t\tif err := db.Ping(ctx); err != nil {\n\t\t\tw.WriteHeader(http.StatusServiceUnavailable)\n\t\t\t_, _ = w.Write([]byte(\"NOT_READY: \" + err.Error()))\n\t\t\treturn\n\t\t}\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"READY\"))\n\t})\n\n\t// Эндпоинт симуляции сбоя СУБД\n\thttp.HandleFunc(\"/simulate-db-down\", func(w http.ResponseWriter, r *http.Request) {\n\t\tdb.healthy.Store(false)\n\t\t_, _ = w.Write([]byte(\"Состояние БД изменено на UNHEALTHY\"))\n\t})\n\n\tfmt.Println(\"Сервис заказов слушает на :8080\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "Когда `kubelet` фиксирует отказ `readinessProbe` (код 503), он отправляет событие изменения статуса пода `PodReady: False` в API-сервер. \n\nКонтроллер `EndpointSlice` немедленно удаляет IP-адрес этого пода из списка активных эндпоинтов сервиса. Демон `kube-proxy` на всех нодах пересчитывает правила iptables/IPVS. В результате новые сетевые пакеты перестают маршрутизироваться на деградировавший под.",
    "pitfalls": "1. Забытый `timeoutSeconds`: если БД зависает без ответа, HTTP-запрос пробы висит бесконечно, блокируя горутины сервера. Всегда используйте `context.WithTimeout`.\n2. Использование одинаковой логики в `liveness` и `readiness`: если упала внешняя БД, liveness-проба начнет циклически перезапускать поды, а readiness-проба корректно снимет под с балансировки.\n3. Отсутствие `successThreshold: 1`: после восстановления БД под должен моментально вернуться в балансировку.",
    "bigtech_interview": "**Вопрос с собеседования:** Что произойдет с входящими HTTP-запросами, если во всем кластере у всех 10 реплик сервиса одновременно откажет `readinessProbe`?\n**Ответ:** Объект `Endpoints` сервиса станет полностью пустым (0 активных IP). \nВ зависимости от конфигурации:\n1. Внутренний Kube-proxy сбросит соединение с ошибкой `Connection refused` (нет доступных бэкендов).\n2. Внешний Ingress-контроллер (Nginx / ALB / Envoy) вернет клиентам статус **503 Service Unavailable** или **502 Bad Gateway**.\n3. При этом **поды не будут перезапущены**, а останутся работать в ожидании восстановления зависимостей, предотвращая каскадный шторм рестартов."
  },
  {
    "num": 21,
    "title": "Сравнение механизмов Liveness и Readiness проб: рестарт пода против снятия с балансировки",
    "task": "Напиши **Liveness и Readiness пробы**: `livenessProbe: httpGet: path: /healthz, port: 8080, initialDelaySeconds: 10, periodSeconds: 5`. `readinessProbe: httpGet: path: /ready, port: 8080`. Покажи разницу: liveness = restart pod, readiness = remove from service endpoints.",
    "theory": "Принципиальное различие между Liveness и Readiness пробами заключается в действии, предпринимаемом Kubelet при сбое:\n- **`livenessProbe` (Действие: Перезапуск):** Если процесс завис в дедлоке или попал в некорректное состояние памяти, Kubelet принудительно убивает контейнер и запускает новый. Это «хирургическое вмешательство».\n- **`readinessProbe` (Действие: Маршрутизация трафика):** Если под перегружен, исчерпал пул коннектов к БД или прогревает кэш, Kubelet **не трогает контейнер**, а лишь убирает его IP из объекта `Endpoints` сервиса. Трафик не поступает на под, давая ему восстановиться, после чего Kubelet автоматически возвращает его в балансировку.",
    "step_by_step": "1. Создайте в Go обработчики `/healthz` (liveness) и `/ready` (readiness).\n2. Опишите обе пробы в `deployment.yaml`.\n3. Установите `initialDelaySeconds: 10` для liveness и `initialDelaySeconds: 2` для readiness.\n4. Разверните сервис и симулируйте временную перегрузку.\n5. Убедитесь, что статус пода остается `Running`, но поле `READY` меняется с `1/1` на `0/1`.",
    "code_blocks": [
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: dual-probe-app\nspec:\n  replicas: 2\n  selector:\n    matchLabels:\n      app: dual-probe\n  template:\n    metadata:\n      labels:\n        app: dual-probe\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/dual-probe:v1.0.0\n          ports:\n            - containerPort: 8080\n          livenessProbe:\n            httpGet:\n              path: /healthz\n              port: 8080\n            initialDelaySeconds: 10\n            periodSeconds: 5\n          readinessProbe:\n            httpGet:\n              path: /ready\n              port: 8080\n            initialDelaySeconds: 2\n            periodSeconds: 3"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"sync/atomic\"\n)\n\nvar isReady atomic.Bool\n\nfunc main() {\n\tisReady.Store(true)\n\n\thttp.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"OK\"))\n\t})\n\n\thttp.HandleFunc(\"/ready\", func(w http.ResponseWriter, r *http.Request) {\n\t\tif !isReady.Load() {\n\t\t\tw.WriteHeader(http.StatusServiceUnavailable)\n\t\t\t_, _ = w.Write([]byte(\"BUSY\"))\n\t\t\treturn\n\t\t}\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"READY\"))\n\t})\n\n\t// Эмуляция временной перегрузки: снять с балансировки на 10 сек\n\thttp.HandleFunc(\"/overload\", func(w http.ResponseWriter, r *http.Request) {\n\t\tisReady.Store(false)\n\t\t_, _ = w.Write([]byte(\"Временная перегрузка активирована\"))\n\t})\n\n\tfmt.Println(\"Dual-probe сервис запущен на :8080\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "Пробы выполняются независимыми воркерами в Kubelet. Если статус readiness меняется на `Unready`, Kubelet отправляет update-запрос в API Server, обновляя `status.conditions` пода (`Ready: False`). \n\nКонтроллер Endpoints отслеживает эти условия и генерирует событие в etcd, после чего kube-proxy на всех нодах мгновенно исключает IP из таблицы iptables.",
    "pitfalls": "1. Задание одинаковых путей `/healthz` для обеих проб без разделения логики.\n2. Проверка внешних зависимостей в livenessProbe: приводит к каскадному рестарту всех подов при сбое внешней БД.\n3. Отсутствие `initialDelaySeconds`: Kubelet убивает контейнер до завершения старта рантайма Go.",
    "bigtech_interview": "**Вопрос с собеседования:** Что происходит с активными HTTP-запросами (in-flight requests), когда под становится Unready по `readinessProbe`?\n**Ответ:** Статус Unready влияет **только на новые подключения**: сервис исключает под из Endpoints, и новые запросы на него не поступают. Все уже установленные TCP-соединения и текущие обрабатываемые запросы продолжают обслуживаться процессом без прерывания до их нормального завершения."
  },
  {
    "num": 22,
    "title": "Защита медленно стартующих приложений с помощью Startup Probe",
    "task": "Используйте **Startup probe** для медленно стартующих приложений (долгие миграции, прогрев кэша).",
    "theory": "Некоторые приложения требуют длительного времени на запуск (прогрев тяжелых ML-моделей, загрузка многогигабайтных справочников в память, проверка целостности БД).\n\nЕсли использовать только `livenessProbe` с большим `initialDelaySeconds: 300`:\n- Если приложение зависнет в рантайме после старта, Kubelet будет ждать те же 300 секунд перед первой проверкой.\n\nРешение — **`startupProbe`**:\n- Действует исключительно на этапе старта контейнера.\n- **Полностью отключает** выполнение Liveness и Readiness проб до тех пор, пока сама не завершится успехом (`200 OK`).\n- Позволяет выделить приложению до 5–10 минут на инициализацию без риска быть убитым Kubelet.",
    "step_by_step": "1. Реализуйте в Go эндпоинт `/startup` с проверкой прогрева кэша.\n2. В `deployment.yaml` настройте `startupProbe: failureThreshold: 30, periodSeconds: 10` (максимум $30 \\times 10 = 300$ секунд).\n3. Настройте строгую `livenessProbe: periodSeconds: 5, failureThreshold: 2`.\n4. Разверните сервис и убедитесь, что Kubelet не перезапускает контейнер во время долгой инициализации.",
    "code_blocks": [
      {
        "filename": "startup-deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: slow-startup-app\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: slow-app\n  template:\n    metadata:\n      labels:\n        app: slow-app\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/slow-app:v1.0.0\n          ports:\n            - containerPort: 8080\n          # Выделяем до 300 секунд (30 * 10с) на холодный старт\n          startupProbe:\n            httpGet:\n              path: /startup\n              port: 8080\n            failureThreshold: 30\n            periodSeconds: 10\n          # После успеха startupProbe включается строгая liveness-проверка\n          livenessProbe:\n            httpGet:\n              path: /live\n              port: 8080\n            periodSeconds: 5\n            failureThreshold: 2"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"sync/atomic\"\n\t\"time\"\n)\n\nvar isWarmedUp atomic.Bool\n\nfunc main() {\n\t// Симуляция тяжелого прогрева кэша (45 секунд)\n\tgo func() {\n\t\tfmt.Println(\"Начало прогрева локального кэша и загрузки справочников...\")\n\t\ttime.Sleep(45 * time.Second)\n\t\tisWarmedUp.Store(true)\n\t\tfmt.Println(\"Прогрев завершен! Приложение готово к работе.\")\n\t}()\n\n\thttp.HandleFunc(\"/startup\", func(w http.ResponseWriter, r *http.Request) {\n\t\tif !isWarmedUp.Load() {\n\t\t\tw.WriteHeader(http.StatusServiceUnavailable)\n\t\t\t_, _ = w.Write([]byte(\"WARMING_UP\"))\n\t\t\treturn\n\t\t}\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"STARTED\"))\n\t})\n\n\thttp.HandleFunc(\"/live\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"ALIVE\"))\n\t})\n\n\tfmt.Println(\"Сервер слушает на :8080...\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "Kubelet держит флаг `startupComplete = false`. Пока этот флаг ложен, вызовы liveness и readiness проб блокируются. \n\nКак только эндпоинт `/startup` возвращает первый успешный ответ `200 OK`, Kubelet навсегда переводит `startupComplete = true` для данного контейнера и переключается на стандартный цикл liveness/readiness проб.",
    "pitfalls": "1. Заниженный `failureThreshold`: если прогрев занял 46 секунд, а лимит был рассчитан на 40 секунд, Kubelet убьет контейнер прямо перед финишем инициализации.\n2. Проверка базы данных в `startupProbe`: если упадет БД, под вообще никогда не выйдет из стадии старта и упадет.\n3. Отсутствие таймаутов на HTTP клиентах при обращении к внешним ресурсам во время прогрева.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем ключевое архитектурное преимущество связки `startupProbe + livenessProbe` перед использованием одного только `livenessProbe` с большим `initialDelaySeconds`?\n**Ответ:** Если использовать только `livenessProbe` с `initialDelaySeconds: 300s`, то в случае зависания (deadlock) приложения на 30-й секунде Kubelet не заметит проблему еще 270 секунд. \nСвязка со `startupProbe` решает обе задачи: она дает контейнеру до 300 секунд на старт, но как только контейнер запустился (например, за 15 секунд), startupProbe завершается и **моментально активирует быстрый liveness-мониторинг** (каждые 5 секунд), обеспечивая реакцию на аварии за считанные секунды."
  },
  {
    "num": 23,
    "title": "Комплексная интеграция эндпоинтов /health/live и /health/ready в Deployment",
    "task": "Добавьте `readinessProbe` и `livenessProbe` в Deployment: проверяйте HTTP-эндпоинты `/health/ready` и `/health/live`.",
    "theory": "Стандартизация диагностических эндпоинтов в enterprise-архитектуре микросервисов:\n- `/health/live`: минималистичная проверка живости HTTP-рантайма Go.\n- `/health/ready`: комплексная проверка готовности сервиса (пул БД, соединение с брокером сообщений, доступность кэша).\n\nВ манифесте `Deployment` пробы настраиваются с разделением частоты опроса: readiness опрашивается чаще (`periodSeconds: 3`), так как своевременное снятие с балансировки критично для минимизации клиентских ошибок, а liveness опрашивается реже (`periodSeconds: 10`).",
    "step_by_step": "1. Настройте мультиплексор `http.ServeMux` с маршрутами `/health/live` и `/health/ready`.\n2. В `deployment.yaml` сконфигурируйте секции `readinessProbe` и `livenessProbe`.\n3. Укажите параметры `timeoutSeconds: 2`, `failureThreshold: 3`.\n4. Разверните сервис в тестовом кластере.\n5. Проинспектируйте выполнение проб через `kubectl describe pod`.",
    "code_blocks": [
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: api-gateway\nspec:\n  replicas: 2\n  selector:\n    matchLabels:\n      app: api-gateway\n  template:\n    metadata:\n      labels:\n        app: api-gateway\n    spec:\n      containers:\n        - name: gateway\n          image: ghcr.io/company/gateway:v1.0.0\n          ports:\n            - containerPort: 8080\n          livenessProbe:\n            httpGet:\n              path: /health/live\n              port: 8080\n            initialDelaySeconds: 5\n            periodSeconds: 10\n            timeoutSeconds: 2\n          readinessProbe:\n            httpGet:\n              path: /health/ready\n              port: 8080\n            initialDelaySeconds: 2\n            periodSeconds: 3\n            timeoutSeconds: 1"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\tmux := http.NewServeMux()\n\n\tmux.HandleFunc(\"/health/live\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(`{\"status\":\"UP\"}`))\n\t})\n\n\tmux.HandleFunc(\"/health/ready\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(`{\"status\":\"READY\",\"database\":\"connected\"}`))\n\t})\n\n\tmux.HandleFunc(\"/api/v1/data\", func(w http.ResponseWriter, r *http.Request) {\n\t\t_, _ = w.Write([]byte(`{\"message\":\"Enterprise API Data\"}`))\n\t})\n\n\tfmt.Println(\"API Gateway слушает порт :8080\")\n\t_ = http.ListenAndServe(\":8080\", mux)\n}"
      }
    ],
    "under_the_hood": "Kubelet использует свой внутренний пул горутин для параллельного опроса сотен подов на ноде. \n\nПри получении ответа от `/health/ready` Kubelet анализирует статус-код. Значение 200 OK переводит под в состояние `EndpointsReady`. Изменения сериализуются в Protobuf и передаются в K8s API Server через gRPC-соединение Kubelet.",
    "pitfalls": "1. Логирование каждого вызова пробы в общий лог сервиса: при 100 подах опрос каждые 3 секунды генерирует миллионы бесполезных строк логов в Elasticsearch/Loki. Запросы проб следует исключать из логов доступа.\n2. Блокирующий вызов без таймаута внутри handler readiness: зависание горутины при падении БД.\n3. Отсутствие заголовка `Content-Type` или закрытия `r.Body`.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в логах доступа (Access Logs) сервиса в K8s рекомендуется фильтровать запросы от `User-Agent: kube-probe/...`?\n**Ответ:** Запросы диагностических проб Kubelet (`kube-probe/1.31`) выполняются непрерывно (каждые несколько секунд на каждую реплику). Если записывать их в общие access-логи, они составляют до 80–90% от общего объема логов сервиса. Это приводит к раздуванию индексов в ElasticSearch/ClickHouse/Loki, росту затрат на хранение и затрудняет поиск реальных клиентских запросов инженерами при расследовании инцидентов."
  },
  {
    "num": 24,
    "title": "Экспонирование Deployment внутри кластера через Service (ClusterIP)",
    "task": "Напиши `Service.yaml` (ClusterIP), чтобы暴露 (expose) деплоймент внутри кластера.",
    "theory": "Для организации взаимодействия между микросервисами (Service-to-Service Communication) используется абстракция `Service` типа `ClusterIP`.\n\nАрхитектура внутреннего взаимодействия:\n- Микросервис `billing-service` обращается к сервису `auth-service`.\n- Встроенный CoreDNS кластера автоматически преобразует имя сервиса в виртуальный ClusterIP.\n- Виртуальный IP сопоставляется с активными репликами через Endpoints.\n- Трафик балансируется прозрачно для вызывающего Go-клиента.",
    "step_by_step": "1. Создайте `deployment.yaml` для сервиса авторизации.\n2. Создайте `service.yaml` с `type: ClusterIP`.\n3. Задайте `port: 80` и `targetPort: 8080`.\n4. Примените манифесты.\n5. Протестируйте сетевое подключение по DNS-имени сервиса.",
    "code_blocks": [
      {
        "filename": "auth-service.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: auth-deployment\nspec:\n  replicas: 2\n  selector:\n    matchLabels:\n      app: auth-server\n  template:\n    metadata:\n      labels:\n        app: auth-server\n    spec:\n      containers:\n        - name: auth\n          image: ghcr.io/company/auth:v1.0.0\n          ports:\n            - containerPort: 8080\n---\napiVersion: v1\nkind: Service\nmetadata:\n  name: auth-service\nspec:\n  type: ClusterIP\n  selector:\n    app: auth-server\n  ports:\n    - name: http\n      port: 80\n      targetPort: 8080"
      },
      {
        "filename": "client.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc main() {\n\tclient := &http.Client{Timeout: 3 * time.Second}\n\n\t// Обращение по внутреннему DNS-имени K8s Service:\n\tresp, err := client.Get(\"http://auth-service/verify\")\n\tif err != nil {\n\t\tfmt.Printf(\"Ошибка обращения к сервису авторизации: %v\\n\", err)\n\t\treturn\n\t}\n\tdefer resp.Body.Close()\n\n\tbody, _ := io.ReadAll(resp.Body)\n\tfmt.Printf(\"Ответ от auth-service: %s\\n\", string(body))\n}"
      }
    ],
    "under_the_hood": "Kubernetes создает запись типа A в CoreDNS: `auth-service.default.svc.cluster.local -> 10.96.12.34`. \n\nКогда Go-клиент выполняет `client.Get(\"http://auth-service/...\")`, библиотека net в Go запрашивает `/etc/resolv.conf`, где указан DNS-сервер K8s (`10.96.0.10`) и суффиксы поиска (`search default.svc.cluster.local svc.cluster.local cluster.local`). CoreDNS возвращает IP сервиса за доли миллисекунды.",
    "pitfalls": "1. Попытка обратиться к поду по его IP-адресу вместо DNS сервиса: при перезапуске пода адрес изменится, и клиент начнет получать сетевые ошибки.\n2. Большое количество суффиксов в `resolv.conf`: приводит к 3-4 избыточным DNS-запросам на каждый внешний хост.\n3. Отсутствие таймаута в `http.Client`: зависание горутин при сетевых задержках в кластере.",
    "bigtech_interview": "**Вопрос с собеседования:** Что такое `ndots:5` в `/etc/resolv.conf` подов Kubernetes и почему это создает огромную нагрузку на CoreDNS?\n**Ответ:** Директива `ndots:5` означает: если доменное имя содержит меньше 5 точек (например, `api.stripe.com` содержит 2 точки), resolver обязан сначала попытаться найти это имя по очереди во всех внутренних суффиксах поиска (`api.stripe.com.default.svc...`, `api.stripe.com.svc...` и т.д.). \nТолько получив 3-4 ошибки NXDOMAIN, резолвер делает запрос во внешний интернет. В крупных кластерах это генерирует миллиарды бесполезных DNS-запросов. Решение: использование точки на конце внешних адресов (`api.stripe.com.`) или тюнинг `dnsConfig.options: ndots: 2`."
  },
  {
    "num": 25,
    "title": "Настройка Startup Probe с увеличенным временем ожидания для тяжелых сервисов",
    "task": "Напиши **Startup probe**: `startupProbe: httpGet: path: /healthz, port: 8080, failureThreshold: 30, periodSeconds: 10` (5 минут на старт). Отключает liveness/readiness до success. Покажи для slow-starting applications.",
    "theory": "Для сервисов с экстремально долгим циклом прогрева (аналитические базы данных, ML inference, сервисы с компиляцией шейдеров или полной перестройкой индекса) требуется тонкая настройка параметров:\n- `failureThreshold: 30`\n- `periodSeconds: 10`\nСуммарно это дает $30 \\times 10 = 300$ секунд (5 минут) гарантированного времени на старт.\n\nВо время работы `startupProbe`:\n- Liveness-проба отключена (контейнер не будет убит).\n- Readiness-проба отключена (трафик не будет поступать).\n- Приложение спокойно выполняет CPU-интенсивную инициализацию.",
    "step_by_step": "1. Создайте эндпоинт `/healthz` в Go, возвращающий 200 OK только после полной загрузки данных.\n2. В манифесте опишите `startupProbe` с интервалом 10с и порогом 30.\n3. Настройте livenessProbe с быстрым интервалом 5с.\n4. Разверните сервис и убедитесь по событиям `kubectl get events`, что проба ожидает готовности.",
    "code_blocks": [
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: heavy-ml-service\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: heavy-ml\n  template:\n    metadata:\n      labels:\n        app: heavy-ml\n    spec:\n      containers:\n        - name: model-server\n          image: ghcr.io/company/heavy-ml:v1.0.0\n          ports:\n            - containerPort: 8080\n          # Выделяем до 5 минут на загрузку весов моделей\n          startupProbe:\n            httpGet:\n              path: /healthz\n              port: 8080\n            failureThreshold: 30\n            periodSeconds: 10\n          livenessProbe:\n            httpGet:\n              path: /healthz\n              port: 8080\n            periodSeconds: 5\n            failureThreshold: 3"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"sync/atomic\"\n\t\"time\"\n)\n\nvar modelLoaded atomic.Bool\n\nfunc main() {\n\tgo func() {\n\t\tfmt.Println(\"Загрузка моделей в память (займет 30 секунд)...\")\n\t\ttime.Sleep(30 * time.Second)\n\t\tmodelLoaded.Store(true)\n\t\tfmt.Println(\"Модели загружены успешно!\")\n\t}()\n\n\thttp.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tif !modelLoaded.Load() {\n\t\t\tw.WriteHeader(http.StatusServiceUnavailable)\n\t\t\t_, _ = w.Write([]byte(\"LOADING\"))\n\t\t\treturn\n\t\t}\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"READY\"))\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "Kubelet инкрементирует внутренний счетчик неудач `startupProbe`. Если число неудач достигает `failureThreshold`, Kubelet генерирует событие `Unhealthy: Startup probe failed` и отправляет контейнеру `SIGKILL`. \n\nЕсли же ответ 200 получен до исчерпания лимита, счетчик сбрасывается, `startupProbe` деактивируется до конца жизни контейнера, и управление переходит к livenessProbe.",
    "pitfalls": "1. Забытый `startupProbe` при долгом старте: Kubelet убьет под через 30 секунд по Liveness пробе, отправив его в вечный CrashLoopBackOff.\n2. Пропуск `timeoutSeconds`: если обработчик зависает, Kubelet блокирует выполнение последующих проверок.\n3. Опрос пробы слишком часто (`periodSeconds: 1`): создает лишнюю нагрузку на CPU во время и без того тяжелой инициализации.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между `Init Containers` и `Startup Probe` для инициализации приложения?\n**Ответ:** \n- **`Init Containers`** запускаются строго **до старта основного контейнера приложения** и выполняются последовательно до полного завершения. Они идеальны для задач, которые можно вынести в отдельный процесс (скачивание файлов конфигурации, запуск SQL миграций схемы).\n- **`Startup Probe`** работает **внутри основного контейнера приложения** во время выполнения его процесса `main()`. Она необходима, когда инициализация неотделима от основного бинарника (прогрев памяти, инициализация пулов соединений, компиляция внутренних кэшей)."
  },
  {
    "num": 26,
    "title": "Создание и проверка Service (ClusterIP) для маршрутизации к Deployment",
    "task": "Создайте **Service** типа ClusterIP для внутреннего доступа к вашему Deployment.",
    "theory": "Закрепление ключевой роли `Service` типа `ClusterIP`:\n- Предоставляет единую стабильную входную точку для группы подов.\n- Автоматически синхронизирует список IP-адресов подов через `Endpoints`.\n- Обеспечивает прозрачное горизонтальное масштабирование: при увеличении числа реплик с 2 до 10 конфигурация клиентов не меняется.",
    "step_by_step": "1. Создайте `deployment.yaml` с 3 репликами.\n2. Создайте `service.yaml` типа `ClusterIP`.\n3. Примените конфигурацию: `kubectl apply -f .`.\n4. Проверьте сопоставление IP-адресов: `kubectl get endpoints <service-name>`.\n5. Масштабируйте Deployment (`kubectl scale deployment ... --replicas=5`) и убедитесь, что список Endpoints автоматически пополнился новыми IP.",
    "code_blocks": [
      {
        "filename": "service.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Service\nmetadata:\n  name: user-service\n  labels:\n    app: user-service\nspec:\n  type: ClusterIP\n  selector:\n    app: user-service\n  ports:\n    - name: http\n      port: 8080\n      targetPort: 8080"
      },
      {
        "filename": "verify-lb.sh",
        "lang": "bash",
        "code": "# 1. Просмотр ClusterIP и портов\nkubectl get svc user-service\n\n# 2. Просмотр реальных IP подов за сервисом\nkubectl get endpoints user-service\n\n# 3. Масштабирование сервиса\nkubectl scale deployment user-service --replicas=4\n\n# 4. Проверка автоматического обновления Endpoints\nkubectl get endpoints user-service"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\tpod, _ := os.Hostname()\n\thttp.HandleFunc(\"/user\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"User API: ответ сформирован репликой %s\\n\", pod)\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "`EndpointSliceController` подписан на изменения объектов `Pod`. \n\nКогда новый под переходит в статус `Running` и успешно проходит `readinessProbe`, контроллер генерирует объект `EndpointSlice` (современная масштабируемая замена монолитного `Endpoints`). Kubelet и kube-proxy считывают обновление по протоколу Watch и добавляют новый IP в таблицу IPVS/iptables.",
    "pitfalls": "1. Несовпадение селектора: сервис создан, но `Endpoints: <none>`.\n2. Попытка подключиться к ClusterIP извне кластера (с домашнего ноутбука): ClusterIP маршрутизируется только внутри приватной SDN сети кластера.\n3. Отсутствие обработки keep-alive соединений в HTTP клиентах.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в Kubernetes 1.21+ объект `EndpointSlice` заменил классический ресурс `Endpoints`?\n**Ответ:** Классический ресурс `Endpoints` содержал полный список всех IP-адресов подов сервиса в одном едином объекте. При наличии 5 000 подов у одного сервиса любое падение или пересоздание одного пода приводило к передаче всего огромного JSON-объекта (размером в мегабайты) по сети на тысячи нод кластера, перегружая etcd и сеть. \n`EndpointSlice` разбивает список адресов на небольшие чанки (по 100 эндпоинтов в каждом), что снизило сетевой трафик и нагрузку на etcd при обновлениях в сотни раз."
  },
  {
    "num": 27,
    "title": "Конфликт планировщика Go с лимитами CPU (GOMAXPROCS) и интеграция automaxprocs",
    "task": "**Конфликт планировщика Go с лимитами CPU (GOMAXPROCS)**: * Объясните в комментариях проблему: если в K8s выставить лимит по процессору `resources.limits.cpu: \"2\"`, рантайм Go по-прежнему будет видеть общее количество ядер физического сервера (например, 64 ядра) и установит `GOMAXPROCS` равным 64. Это приведет к сильному троттлингу (замедлению) контейнера планировщиком CFS ядра Linux.\n    * Решите эту проблему: импортируйте популярную библиотеку `go.uber.org/automaxprocs` в ваш файл `main.go` [465]. Запустите контейнер в K8s и убедитесь по логам, что Go автоматически скорректировал количество потоков под реальные лимиты контейнера [465].",
    "theory": "Одна из самых коварных проблем производительности Go в Kubernetes:\n- Рантайм Go при старте определяет количество потоков ОС планировщика (`GOMAXPROCS`) через системный вызов `runtime.NumCPU()`.\n- Системный вызов возвращает **общее количество физических ядер хост-машины** (например, 64 или 128 ядер), полностью игнорируя лимиты cgroups контейнера (`limits.cpu: \"2\"`).\n- В результате Go запускает 64 системных потока (`M` в модели GMP), которые начинают параллельно исполнять горутины.\n- Планировщик Linux CFS исчерпывает 200 мс квоты (лимит 2 CPU) за считанные миллисекунды и жестко замораживает все потоки контейнера (**CPU Throttling**).\n- Задержка ответов (latency) сервиса взлетает с 5 мс до 800 мс!\n\nРешение — библиотека от инженеров Uber: **`go.uber.org/automaxprocs`**. Она считывает реальные квоты CFS из `/sys/fs/cgroup` и автоматически выставляет `GOMAXPROCS` равным реальному лимиту контейнера.",
    "step_by_step": "1. Добавьте библиотеку `go get go.uber.org/automaxprocs`.\n2. Импортируйте пакет через анонимный импорт `_ \"go.uber.org/automaxprocs\"` в начале файла `main.go`.\n3. Задайте в манифесте `resources.limits.cpu: \"2\"`.\n4. Запустите контейнер в Kubernetes.\n5. Убедитесь по логам старта, что `GOMAXPROCS` автоматически скорректирован с 64 до 2.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"runtime\"\n\n\t// Автоматическая настройка GOMAXPROCS под cgroups лимиты K8s\n\t_ \"go.uber.org/automaxprocs\"\n)\n\nfunc main() {\n\tfmt.Printf(\"Сервис запущен. Реальное значение GOMAXPROCS = %d (Ядер на хосте: %d)\\n\",\n\t\truntime.GOMAXPROCS(0), runtime.NumCPU())\n\n\thttp.HandleFunc(\"/compute\", func(w http.ResponseWriter, r *http.Request) {\n\t\t// Имитация вычислений\n\t\ttotal := 0\n\t\tfor i := 0; i < 1_000_000; i++ {\n\t\t\ttotal += i\n\t\t}\n\t\tfmt.Fprintf(w, \"GOMAXPROCS=%d, Result=%d\\n\", runtime.GOMAXPROCS(0), total)\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      },
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: automaxprocs-demo\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: automaxprocs-demo\n  template:\n    metadata:\n      labels:\n        app: automaxprocs-demo\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/automaxprocs-demo:v1.0.0\n          resources:\n            requests:\n              cpu: \"1\"\n              memory: \"128Mi\"\n            limits:\n              cpu: \"2\" # Лимит 2 ядра на 64-ядерном сервере\n              memory: \"256Mi\" "
      }
    ],
    "under_the_hood": "В функции `init()` пакет `automaxprocs` инспектирует виртуальную файловую систему cgroups v1 (`/sys/fs/cgroup/cpu/cpu.cfs_quota_us`) или cgroups v2 (`/sys/fs/cgroup/cpu.max`). \n\nОн делит квоту на период (`quota / period`). Например, для лимита 2 CPU: $200000 / 100000 = 2.0$. Пакет округляет дробное значение вниз (floor) и вызывает стандартную функцию `runtime.GOMAXPROCS(2)`. Логи выводятся в формате: `maxprocs: Updating GOMAXPROCS=2: using cgroups quota`.",
    "pitfalls": "1. Дробные лимиты CPU (`limits.cpu: \"500m\"`): округление дает `GOMAXPROCS=1`, что является безопасным минимумом.\n2. Отсутствие `automaxprocs` в микросервисах с пулом горутин: приводит к колоссальному падению throughput и деградации p99 latency под нагрузкой.\n3. Ручная жесткая установка `runtime.GOMAXPROCS(N)` в коде: лишает контейнер гибкости при изменении манифестов K8s.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в Kubernetes при `limits.cpu: \"2\"` на 64-ядерном сервере приложение без `automaxprocs` испытывает сильный CFS Throttling, даже если CPU утилизация составляет всего 50%?\n**Ответ:** Планировщик Go видит 64 ядра и создает 64 системных потока ОС (`M`). Когда поступает пачка запросов, планировщик Go одновременно будит все 64 потока на разных ядрах. \nЗа каждую миллисекунду реального времени 64 ядра суммарно сжигают 64 мс квоты. Выделенный лимит в 2 ядра (200 мс на период 100 мс) исчерпывается всего за **3.125 миллисекунды**! Оставшиеся 96.8 миллисекунд контейнер находится в состоянии глубокого троттлинга ядра Linux, а клиенты ждут ответов."
  },
  {
    "num": 28,
    "title": "Классы качества обслуживания (QoS): Guaranteed, Burstable и BestEffort",
    "task": "Настрой **resource requests/limits**: `resources: requests: memory: \"256Mi\", cpu: \"250m\"`, `limits: memory: \"512Mi\", cpu: \"500m\"`. Покажи QoS classes: `Guaranteed` (requests=limits), `Burstable` (requests<limits), `BestEffort` (none).",
    "theory": "Kubernetes управляет распределением ресурсов через механизм **QoS (Quality of Service)**:\n1. **`Guaranteed`:** У всех контейнеров пода заданы `requests` и `limits`, и они **строго равны** между собой как по CPU, так и по памяти (`requests.cpu == limits.cpu` и `requests.mem == limits.mem`). Наивысший приоритет, никогда не выселяются при дефиците памяти ноды.\n2. **`Burstable`:** Заданы requests и limits, но `requests < limits`, либо заданы только requests. Могут временно утилизировать свободные мощности ноды («burst»).\n3. **`BestEffort`:** Ни requests, ни limits не указаны. Низший приоритет, первыми уничтожаются OOM Killer при малейшей нехватке памяти на ноде.",
    "step_by_step": "1. Создайте манифест с Guaranteed QoS: укажите одинаковые значения в `requests` и `limits`.\n2. Создайте манифест с Burstable QoS: `requests.cpu: 250m, limits.cpu: 500m`.\n3. Примените оба манифеста.\n4. Проверьте присвоенный класс через `kubectl get pod <name> -o jsonpath='{.status.qosClass}'`.\n5. Изучите приоритеты выселения подов при аварии.",
    "code_blocks": [
      {
        "filename": "qos-deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: guaranteed-service\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: guaranteed\n  template:\n    metadata:\n      labels:\n        app: guaranteed\n    spec:\n      containers:\n        - name: app\n          image: alpine:3.21\n          command: [\"sleep\", \"3600\"]\n          resources:\n            requests:\n              cpu: \"500m\"\n              memory: \"512Mi\"\n            limits:\n              cpu: \"500m\" # Равно requests -> Guaranteed QoS\n              memory: \"512Mi\" # Равно requests -> Guaranteed QoS\n---\napiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: burstable-service\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: burstable\n  template:\n    metadata:\n      labels:\n        app: burstable\n    spec:\n      containers:\n        - name: app\n          image: alpine:3.21\n          command: [\"sleep\", \"3600\"]\n          resources:\n            requests:\n              cpu: \"250m\"\n              memory: \"256Mi\"\n            limits:\n              cpu: \"500m\" # Больше requests -> Burstable QoS\n              memory: \"512Mi\" "
      },
      {
        "filename": "check-qos.sh",
        "lang": "bash",
        "code": "# Проверка QoS класса первого пода:\nkubectl get pod -l app=guaranteed -o jsonpath='{.items[0].status.qosClass}'\n# Вывод: Guaranteed\n\n# Проверка QoS класса второго пода:\nkubectl get pod -l app=burstable -o jsonpath='{.items[0].status.qosClass}'\n# Вывод: Burstable"
      }
    ],
    "under_the_hood": "Kubelet рассчитывает значение `oom_score_adj` для каждого контейнера в зависимости от QoS:\n- Для **Guaranteed** подов: `oom_score_adj = -997` (ядро Linux защищает процесс от OOM Killer почти как системные демоны).\n- Для **BestEffort** подов: `oom_score_adj = 1000` (максимальная вероятность быть убитым ядром).\n- Для **Burstable** подов: динамический балл от 2 до 999 в зависимости от отношения потребления памяти к запрошенному request.",
    "pitfalls": "1. Использование BestEffort в production: любой случайный фоновый процесс на ноде может привести к немедленному уничтожению вашего пода.\n2. Несоответствие requests и limits в одном из контейнеров мультиконтейнерного пода: весь под потеряет статус Guaranteed и станет Burstable.\n3. Завышение requests для Guaranteed подов: ноды будут казаться заполненными на 100%, хотя реальное потребление ресурсов может быть низким (Over-provisioning).",
    "bigtech_interview": "**Вопрос с собеседования:** В каком порядке Kubelet выселяет (evicts) поды при наступлении события `NodeMemoryPressure` (дефицит памяти на ноде)?\n**Ответ:** Kubelet выселяет поды строго по иерархии:\n1. **BestEffort поды:** уничтожаются первыми, так как они не задекларировали никаких гарантий ресурсов.\n2. **Burstable поды, превысившие свои `requests`:** выселяются следующими, при этом первыми идут те, у которых наибольшее превышение requests относительно лимита.\n3. **Burstable поды в пределах `requests`:** выселяются только при продолжающемся дефиците.\n4. **Guaranteed поды:** выселяются в самую последнюю очередь, только если на ноде исчерпаны все остальные поды и под угрозой стабильность системных компонентов Kubelet/OS."
  },
  {
    "num": 29,
    "title": "Горизонтальное автомасштабирование подов (HPA v2) по утилизации CPU",
    "task": "Настрой **HorizontalPodAutoscaler (HPA)**: `apiVersion: autoscaling/v2`, `metrics: - type: Resource, resource: name: cpu, target: type: Utilization, averageUtilization: 70`. Scale 3 → 10 pods. Покажи autoscaling.",
    "theory": "**HorizontalPodAutoscaler (HPA)** — контроллер автоматического масштабирования количества реплик пода в зависимости от нагрузки.\n\nВ спецификации `autoscaling/v2`:\n- Поддерживается масштабирование по ресурсам (CPU, Memory) и кастомным/внешним метрикам (Prometheus, очереди RabbitMQ, Kafka lag).\n- Алгоритм расчета целевого числа реплик:\n  $$\\text{DesiredReplicas} = \\lceil \\text{CurrentReplicas} \\times \\frac{\\text{CurrentMetricValue}}{\\text{TargetMetricValue}} \\rceil$$\n- При значении `averageUtilization: 70` по CPU: если средняя загрузка по всем подам достигает 70% от `requests.cpu`, HPA плавно увеличивает число реплик от 3 до 10.",
    "step_by_step": "1. Убедитесь, что в кластере установлен `metrics-server`.\n2. Убедитесь, что в манифесте `Deployment` заданы `resources.requests.cpu`.\n3. Создайте манифест `hpa.yaml` с диапазоном реплик 3..10 и целевым порогом CPU 70%.\n4. Примените манифест: `kubectl apply -f hpa.yaml`.\n5. Проверьте статус автомасштабирования: `kubectl get hpa`.",
    "code_blocks": [
      {
        "filename": "hpa.yaml",
        "lang": "yaml",
        "code": "apiVersion: autoscaling/v2\nkind: HorizontalPodAutoscaler\nmetadata:\n  name: api-autoscaler\nspec:\n  scaleTargetRef:\n    apiVersion: apps/v1\n    kind: Deployment\n    name: api-service\n  minReplicas: 3\n  maxReplicas: 10\n  metrics:\n    - type: Resource\n      resource:\n        name: cpu\n        target:\n          type: Utilization\n          averageUtilization: 70\n  behavior:\n    scaleDown:\n      stabilizationWindowSeconds: 300 # Предотвращение флаппинга при спаде нагрузки\n      policies:\n        - type: Percent\n          value: 20\n          periodSeconds: 60"
      },
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: api-service\nspec:\n  replicas: 3\n  selector:\n    matchLabels:\n      app: api-service\n  template:\n    metadata:\n      labels:\n        app: api-service\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/api:v1.0.0\n          resources:\n            requests:\n              cpu: \"200m\" # HPA считает процент именно от этого значения\n              memory: \"128Mi\"\n            limits:\n              cpu: \"500m\"\n              memory: \"256Mi\" "
      }
    ],
    "under_the_hood": "`HPAController` внутри `kube-controller-manager` каждые 15 секунд опрашивает `Metrics API` (`metrics.k8s.io`). \n\nКонтроллер получает текущую загрузку CPU от `metrics-server`, который собирает метрики со всех нод через cAdvisor. Если текущее значение составляет 140m при request 200m ($70\\%$), система находится в балансе. \n\nЕсли загрузка возрастает до 180m ($90\\%$), HPA рассчитывает: $3 \\times (90 / 70) = 3.85 \\rightarrow 4$ реплики, и отправляет вызов `Scale` в `Deployment`.",
    "pitfalls": "1. Отсутствие `resources.requests.cpu`: HPA не сможет рассчитать процент утилизации и перейдет в статус `<unknown>`, масштабирование работать не будет.\n2. Флаппинг (Flapping / Thrashed Scaling): резкое скачкообразное масштабирование вверх-вниз при импульсной нагрузке. Требуется настройка `behavior.scaleDown.stabilizationWindowSeconds: 300`.\n3. Конфликт с ручным `kubectl scale`: HPA автоматически перезапишет ручные изменения числа реплик.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему автомасштабирование по утилизации памяти (Memory Utilization) в Go сервисах работает значительно хуже, чем по CPU?\n**Ответ:** В Go рантайм использует сборщик мусора (GC) и собственный аллокатор памяти (tcmalloc-like mcache/mcentral/mheap). \nКогда сервис освобождает объекты в куче, рантайм Go не возвращает страницы памяти операционной системе немедленно (`scavenger` возвращает память медленно через `madvise(MADV_DONTNEED)`). В результате RSS процесса в cgroups остается высоким даже после спада трафика, и HPA не может своевременно отмасштабировать поды вниз (Scale Down). Поэтому в BigTech масштабируют по **CPU, RPS или лагу очередей**."
  },
  {
    "num": 30,
    "title": "Публичный доступ к сервису через Service типа LoadBalancer в облачной инфраструктуре",
    "task": "Создайте **Service** типа LoadBalancer для production (в облаке создаст внешний LB).",
    "theory": "Для предоставления прямого сетевого доступа к сервису из публичного интернета без Ingress-контроллера используется **`Service` типа `LoadBalancer`**:\n- Автоматически инициирует создание физического внешнего балансировщика в облачном провайдере (AWS Network Load Balancer, Google Cloud Network LB, Yandex Cloud NLB).\n- Облачный балансировщик получает публичный статический IP-адрес (`External-IP`).\n- Трафик перенаправляется с публичного IP через `NodePort` на ноды кластера, а затем через Kube-proxy — на поды приложения.",
    "step_by_step": "1. Создайте манифест `service-lb.yaml` с `type: LoadBalancer`.\n2. Добавьте аннотации облачного провайдера (например, для AWS NLB).\n3. Примените манифест: `kubectl apply -f service-lb.yaml`.\n4. Дождитесь выделения публичного адреса: `kubectl get svc web-lb -w`.\n5. Выполните запрос к сервису по внешнему IP-адресу через браузер или curl.",
    "code_blocks": [
      {
        "filename": "service-lb.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Service\nmetadata:\n  name: web-lb\n  annotations:\n    # Пример аннотации для создания Network Load Balancer в AWS:\n    service.beta.kubernetes.io/aws-load-balancer-type: \"external\"\n    service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: \"ip\"\nspec:\n  type: LoadBalancer\n  selector:\n    app: web-app\n  ports:\n    - name: http\n      protocol: TCP\n      port: 80\n      targetPort: 8080"
      },
      {
        "filename": "check-lb.sh",
        "lang": "bash",
        "code": "# Ожидание выделения внешнего адреса облачным провайдером\nkubectl get svc web-lb\n\n# Пример вывода:\n# NAME     TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)        AGE\n# web-lb   LoadBalancer   10.96.120.45    51.250.10.89    80:31234/TCP   45s\n\n# Проверка ответа через публичный IP\ncurl http://51.250.10.89"
      }
    ],
    "under_the_hood": "Cloud Controller Manager (CCM) отслеживает события создания сервисов с типом `LoadBalancer`. \n\nCCM обращается к API облачного провайдера (через IAM-роль), заказывает создание балансировщика нагрузки, настраивает Target Group и health-check. После создания CCM записывает полученный публичный IP-адрес или DNS-имя в поле `status.loadBalancer.ingress` объекта Service.",
    "pitfalls": "1. Высокая стоимость: создание отдельного `Service LoadBalancer` на каждый из 100 микросервисов создаст 100 облачных балансировщиков, что приведет к огромным счетам за инфраструктуру. Вместо этого создают **один Ingress-контроллер** за одним LoadBalancer.\n2. Потеря исходного IP клиента (Client IP Spoofing): при прохождении через NodePort происходит SNAT. Для сохранения реального IP требуется опция `externalTrafficPolicy: Local`.\n3. Зависание в статусе `<pending>` на локальном Minikube/Kind без запуска `minikube tunnel`.",
    "bigtech_interview": "**Вопрос с собеседования:** Что делает опция `spec.externalTrafficPolicy: Local` в Kubernetes Service и какую скрытую проблему она несет?\n**Ответ:** \n- **Плюсы:** `externalTrafficPolicy: Local` отключает второй сетевой прыжок (SNAT) между нодами кластера. Нода принимает входящий пакет и отправляет его **строго на под, запущенный на этой же физической ноде**. Это сохраняет реальный исходный IP-адрес клиента (`X-Forwarded-For` не нужен) и снижает задержку сети.\n- **Минусы:** Возникает неравномерная балансировка нагрузки: если на Ноде А запущен 1 под, а на Ноде Б — 3 пода, внешний облачный балансировщик будет делить трафик 50/50 между двумя нодами. В результате под на Ноде А получит в 3 раза больше нагрузки, чем поды на Ноде Б!"
  },
  {
    "num": 31,
    "title": "Управление раздельной конфигурацией: ConfigMap для параметров и Secret для DSN",
    "task": "**[ConfigMap & Secret]**: Вынеси конфигурацию (порт, лог-уровень) в `ConfigMap`. Чувствительные данные (DSN БД) помести в `Secret`. Подключи их в Pod через `envFrom` или `valueFrom`.",
    "theory": "Разделение ответственности между открытыми и конфиденциальными параметрами конфигурации:\n1. **`ConfigMap`:** Хранит открытые параметры (`HTTP_PORT: \"8080\"`, `LOG_LEVEL: \"info\"`, `CACHE_TTL: \"15m\"`).\n2. **`Secret`:** Хранит строку подключения к базе данных (`DATABASE_DSN`) с паролем учетной записи.\n\nИспользование выборочной привязки через `valueFrom` делает контракт зависимостей контейнера явным и проверяемым на этапе код-ревью.",
    "step_by_step": "1. Создайте `configmap.yaml` с параметрами приложения.\n2. Создайте `secret.yaml` со строкой подключения к БД.\n3. В `deployment.yaml` свяжите переменные через `configMapKeyRef` и `secretKeyRef`.\n4. В Go-сервисе инициализируйте подключение к БД и HTTP-сервер.\n5. Протестируйте работу приложения в кластере.",
    "code_blocks": [
      {
        "filename": "manifests.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: app-settings\ndata:\n  HTTP_PORT: \"8080\"\n  LOG_LEVEL: \"warn\"\n---\napiVersion: v1\nkind: Secret\nmetadata:\n  name: app-credentials\ntype: Opaque\nstringData:\n  DATABASE_DSN: \"postgres://app_user:StrongPass2026@pg.db.svc:5432/app_db?sslmode=require\"\n---\napiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: catalog-service\nspec:\n  replicas: 2\n  selector:\n    matchLabels:\n      app: catalog\n  template:\n    metadata:\n      labels:\n        app: catalog\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/catalog:v1.0.0\n          env:\n            - name: PORT\n              valueFrom:\n                configMapKeyRef:\n                  name: app-settings\n                  key: HTTP_PORT\n            - name: LOG_LEVEL\n              valueFrom:\n                configMapKeyRef:\n                  name: app-settings\n                  key: LOG_LEVEL\n            - name: DB_DSN\n              valueFrom:\n                secretKeyRef:\n                  name: app-credentials\n                  key: DATABASE_DSN"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\tport := os.Getenv(\"PORT\")\n\tlogLevel := os.Getenv(\"LOG_LEVEL\")\n\tdsn := os.Getenv(\"DB_DSN\")\n\n\tif dsn == \"\" {\n\t\tpanic(\"Критическая ошибка: DB_DSN не передан!\")\n\t}\n\n\tfmt.Printf(\"Каталог-сервис инициализирован: Port=%s, LogLevel=%s\\n\", port, logLevel)\n\tfmt.Println(\"Подключение к БД по DSN из Secret успешно сконфигурировано.\")\n\n\thttp.HandleFunc(\"/health\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"OK\"))\n\t})\n\n\t_ = http.ListenAndServe(\":\"+port, nil)\n}"
      }
    ],
    "under_the_hood": "Kubelet связывает дескрипторы переменных окружения перед вызовом системного вызова `clone` (создание контейнера). \n\nЗначение секрета читается из `tmpfs` памяти ноды. Использование явного связывания через `valueFrom` защищает от случайного перезатирания переменных, которое может произойти при использовании общего `envFrom` при наличии пересекающихся ключей.",
    "pitfalls": "1. Хранение DSN со специальными символами в URL без экранирования (URL encoding пароля).\n2. Случайное логирование переменной `DB_DSN` в stdout сервиса: пароль попадает в централизованное хранилище логов.\n3. Опечатка в имени ключа `secretKeyRef`: под зависает в `CreateContainerConfigError`.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем опасность хранения паролей в переменных окружения процесса (`env`), и почему монтирование секрета как файла в Volume безопаснее?\n**Ответ:** \n1. **Утечки в логи и дампы:** Переменные окружения процесса видны в `/proc/$PID/environ`. При сбое (crash/panic) многие библиотеки отправляют переменные окружения в Sentry/Datadog вместе со стек-трейсом, компрометируя пароли.\n2. **Безопасность дочерних процессов:** Любой дочерний процесс (`exec.Command`) по умолчанию наследует все переменные родителя.\n3. Монтирование секрета как файла в виртуальную память (`tmpfs`) изолирует доступ строго правами файловой системы (chmod 0400), исключая непреднамеренную утечку."
  },
  {
    "num": 32,
    "title": "Вертикальное автомасштабирование (VPA): режимы Auto и Recommendation Only",
    "task": "Настрой **VerticalPodAutoscaler (VPA)**: `updateMode: \"Auto\"` или `\"Off\"` (recommendation only). Автоматически adjusts requests/limits based on actual usage. Покажи difference с HPA (scale up pod vs scale out pods).",
    "theory": "В то время как HPA масштабирует сервис **горизонтально** (увеличивает число подов), **VerticalPodAutoscaler (VPA)** масштабирует его **вертикально** — автоматически подбирает оптимальные значения `requests` и `limits` по CPU и памяти для каждого пода на основе реального исторического потребления.\n\nРежимы работы VPA (`updateMode`):\n1. **`Off` (Recommendation Only):** Безопасный режим аудита. VPA только рассчитывает и показывает рекомендации в статусе CRD, но ничего не меняет.\n2. **`Initial`:** VPA назначает рекомендованные ресурсы только новым подам в момент их создания.\n3. **`Auto` / `Recreate`:** VPA принудительно перезапускает работающие поды (eviction), чтобы применить новые лимиты ресурсов.",
    "step_by_step": "1. Убедитесь, что в кластере установлен VPA Controller.\n2. Создайте манифест `vpa.yaml` с `updateMode: \"Off\"`.\n3. Примените манифест: `kubectl apply -f vpa.yaml`.\n4. Дайте сервису поработать под нагрузкой несколько минут.\n5. Запросите рекомендации VPA: `kubectl describe vpa my-service-vpa`.",
    "code_blocks": [
      {
        "filename": "vpa.yaml",
        "lang": "yaml",
        "code": "apiVersion: autoscaling.k8s.io/v1\nkind: VerticalPodAutoscaler\nmetadata:\n  name: my-service-vpa\nspec:\n  targetRef:\n    apiVersion: apps/v1\n    kind: Deployment\n    name: billing-api\n  updatePolicy:\n    updateMode: \"Off\" # Режим рекомендаций без опасного перезапуска подов\n  resourcePolicy:\n    containerPolicies:\n      - containerName: '*'\n        minAllowed:\n          cpu: 100m\n          memory: 128Mi\n        maxAllowed:\n          cpu: 2000m\n          memory: 4Gi\n        controlledResources: [\"cpu\", \"memory\"]"
      },
      {
        "filename": "check-vpa.sh",
        "lang": "bash",
        "code": "# Просмотр рекомендаций VPA\nkubectl describe vpa my-service-vpa\n\n# Пример секции Recommendation в выводе:\n# Recommendation:\n#   Container Recommendations:\n#     Container Name:  app\n#     Lower Bound:\n#       Cpu:     150m\n#       Memory:  200Mi\n#     Target:\n#       Cpu:     250m\n#       Memory:  350Mi\n#     Upper Bound:\n#       Cpu:     1000m\n#       Memory:  1Gi"
      }
    ],
    "under_the_hood": "VPA состоит из трех компонентов:\n1. **Recommender:** Анализирует историю потребления из Prometheus / Metrics Server и рассчитывает 4 значения (LowerBound, Target, UncappedTarget, UpperBound).\n2. **Updater:** В режиме `Auto` находит поды, чьи текущие ресурсы сильно расходятся с `Target`, и вызывает их выселение (`Eviction`).\n3. **Admission Plugin:** Мутирующий вебхук перехватывает создание нового пода и подставляет вычисленные значения `requests/limits` в спецификацию пода.",
    "pitfalls": "1. Одновременное включение HPA и VPA по одной и той же метрике (CPU): приводит к разрушительному резонансу (HPA плодит поды, а VPA уменьшает их размер, или наоборот).\n2. Использование `updateMode: \"Auto\"` без настроенного `PodDisruptionBudget`: VPA может одновременно прибить все поды сервиса для обновления ресурсов.\n3. Отсутствие `minAllowed` и `maxAllowed`: риск сжатия ресурсов до нуля или захвата всей ноды.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему одновременное использование HPA и VPA на одном Deployment считается опасным антипаттерном, и как их безопасно совмещать?\n**Ответ:** Если HPA и VPA настроены на одну метрику (CPU), возникает конфликт контроллеров: при росте нагрузки HPA добавляет новые поды, а VPA параллельно увеличивает CPU limit каждого пода. При спаде нагрузки оба контроллера одновременно уменьшают ресурсы и число подов, вызывая резкую нестабильность. \nСовмещение допустимо только в двух сценариях:\n1. VPA работает строго в режиме рекомендаций (`updateMode: \"Off\"`).\n2. HPA масштабирует по **бизнес-метрикам** (RPS, задержка HTTP, длина очереди Kafka), а VPA управляет **памятью** (Memory)."
  },
  {
    "num": 33,
    "title": "Нагрузочное тестирование автомасштабирования (HPA) по CPU и памяти",
    "task": "Настройте `HorizontalPodAutoscaler` по CPU и памяти, проверьте масштабирование нагрузочным тестом.",
    "theory": "Проверка работоспособности HPA перед выкаткой в продакшн обязательна:\n- Нагрузочный генератор (`hey` или `k6`) генерирует непрерывный поток параллельных HTTP-запросов.\n- Вычислительная нагрузка в Go-сервисе утилизирует CPU.\n- Метрики `container_cpu_usage_seconds_total` растут.\n- HPA фиксирует превышение целевого порога (например, 70%) и выполняет горизонтальное масштабирование реплик от 2 до 8.\n- После прекращения нагрузки контроллер выдерживает стабилизационное окно (cooldown) и плавно сворачивает лишние реплики.",
    "step_by_step": "1. Разверните сервис с установленным `requests.cpu: 100m`.\n2. Создайте HPA с порогом 50% CPU.\n3. Запустите генератор нагрузки `kubectl run load-generator --image=busybox -- sh -c \"while true; do wget -q -O- http://my-service; done\"`.\n4. Наблюдайте за ростом нагрузки: `kubectl get hpa -w`.\n5. Убедитесь, что число подов масштабируется с 2 до 6.",
    "code_blocks": [
      {
        "filename": "hpa-test.yaml",
        "lang": "yaml",
        "code": "apiVersion: autoscaling/v2\nkind: HorizontalPodAutoscaler\nmetadata:\n  name: load-test-hpa\nspec:\n  scaleTargetRef:\n    apiVersion: apps/v1\n    kind: Deployment\n    name: load-service\n  minReplicas: 2\n  maxReplicas: 8\n  metrics:\n    - type: Resource\n      resource:\n        name: cpu\n        target:\n          type: Utilization\n          averageUtilization: 50"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"math\"\n\t\"net/http\"\n)\n\nfunc cpuHeavyHandler(w http.ResponseWriter, r *http.Request) {\n\t// Интенсивная нагрузка на CPU\n\tvar x float64 = 0.0001\n\tfor i := 0; i < 500000; i++ {\n\t\tx += math.Sqrt(x)\n\t}\n\tfmt.Fprintf(w, \"OK: %f\\n\", x)\n}\n\nfunc main() {\n\thttp.HandleFunc(\"/\", cpuHeavyHandler)\n\tfmt.Println(\"Нагрузочный сервис слушает на :8080\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      },
      {
        "filename": "run-load.sh",
        "lang": "bash",
        "code": "# Мониторинг масштабирования в реальном времени\nkubectl get hpa load-test-hpa -w\n\n# В отдельном терминале: запуск 5 параллельных генераторов нагрузки\nfor i in $(seq 1 5); do\n  kubectl run \"generator-$i\" --rm -i --tty --image=busybox -- /bin/sh -c \"while true; do wget -q -O- http://load-service; done\" &\ndone"
      }
    ],
    "under_the_hood": "Metrics-server с интервалом в 15–30 секунд опрашивает cAdvisor на каждой ноде. \n\nHPA Controller вычисляет скользящее среднее утилизации. При скачке до 120% он отправляет PATCH-запрос в subresource `/scale` Deployment, обновляя поле `spec.replicas`. Новый ReplicaSet запускает поды, а Kubelet скачивает образ и стартует контейнеры.",
    "pitfalls": "1. Отсутствие установленного `metrics-server`: самая частая причина неработающего HPA в локальных кластерах.\n2. Недостаток нод в кластере: поды переходят в статус `Pending`, так как ноды физически заполнены. Для автоматического добавления серверов требуется **Cluster Autoscaler** или **Karpenter**.\n3. Слишком низкий порог (например, 20%): приводит к постоянному дерганию подов.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между HPA на уровне подов и Cluster Autoscaler / Karpenter на уровне инфраструктуры?\n**Ответ:** \n- **HPA (Horizontal Pod Autoscaler)** работает **внутри кластера на уровне подов**: он увеличивает количество реплик Deployment, когда растет нагрузка.\n- **Cluster Autoscaler / Karpenter** работает **на уровне облачной инфраструктуры**: когда новые поды от HPA не могут запуститься и зависают в статусе `Pending` из-за нехватки CPU на имеющихся серверах, Cluster Autoscaler заказывает у облачного провайдера (AWS/GCP/VK Cloud) новые виртуальные машины (Worker Nodes), расширяя физический размер кластера."
  },
  {
    "num": 34,
    "title": "Оркестрация Stateful-приложений: StatefulSet и Headless Service",
    "task": "Настрой **StatefulSet**: `kind: StatefulSet`, `serviceName: postgres`, `replicas: 3`, `volumeClaimTemplates: - metadata: name: data, spec: accessModes: [ReadWriteOnce], resources: requests: storage: 10Gi`. Stable network identity: `postgres-0`, `postgres-1`, `postgres-2`. Покажи для databases.",
    "theory": "В отличие от stateless веб-серверов, базы данных (PostgreSQL, Redis, Kafka, Cassandra) требуют:\n- Стабильных сетевых имен хостов (Stable Network Identity).\n- Порядкового создания и удаления (Ordinal Index: 0, 1, 2).\n- Выделенного персистентного диска для каждой реплики, который не теряется при перезапуске пода.\n\nРесурс **`StatefulSet` (`apiVersion: apps/v1`)**:\n- Поды именуются строго детерминированно: `postgres-0`, `postgres-1`, `postgres-2`.\n- Требует обязательного **Headless Service** (`clusterIP: None`) для DNS-маршрутизации к конкретным подам напрямую (`postgres-0.postgres-svc`).\n- Секция **`volumeClaimTemplates`**: автоматически генерирует индивидуальный PersistentVolumeClaim (PVC) для каждого порядкового номера пода.",
    "step_by_step": "1. Создайте манифест Headless Service с `clusterIP: None`.\n2. Опишите манифест `StatefulSet` с `serviceName`, связывающим его с Headless Service.\n3. Добавьте блок `volumeClaimTemplates` с запросом 10Gi диска.\n4. Примените манифесты: `kubectl apply -f statefulset.yaml`.\n5. Убедитесь, что поды создаются строго по очереди (сначала 0, затем 1, затем 2).",
    "code_blocks": [
      {
        "filename": "statefulset.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Service\nmetadata:\n  name: postgres-headless\n  labels:\n    app: postgres\nspec:\n  clusterIP: None # Headless Service\n  selector:\n    app: postgres\n  ports:\n    - port: 5432\n      name: postgresql\n---\napiVersion: apps/v1\nkind: StatefulSet\nmetadata:\n  name: postgres\nspec:\n  serviceName: \"postgres-headless\"\n  replicas: 3\n  selector:\n    matchLabels:\n      app: postgres\n  template:\n    metadata:\n      labels:\n        app: postgres\n    spec:\n      containers:\n        - name: postgres\n          image: postgres:16-alpine\n          ports:\n            - containerPort: 5432\n          env:\n            - name: POSTGRES_PASSWORD\n              value: \"secret\"\n          volumeMounts:\n            - name: pgdata\n              mountPath: /var/lib/postgresql/data\n  volumeClaimTemplates:\n    - metadata:\n        name: pgdata\n      spec:\n        accessModes: [ \"ReadWriteOnce\" ]\n        resources:\n          requests:\n            storage: 10Gi"
      },
      {
        "filename": "inspect-stateful.sh",
        "lang": "bash",
        "code": "# Просмотр созданных подов StatefulSet\nkubectl get pods -l app=postgres\n\n# Просмотр автоматически созданных томов (PVC)\nkubectl get pvc -l app=postgres\n# Вывод:\n# pgdata-postgres-0   Bound\n# pgdata-postgres-1   Bound\n# pgdata-postgres-2   Bound"
      }
    ],
    "under_the_hood": "`StatefulSetController` соблюдает строгий порядок: под `postgres-1` не начнет создаваться, пока под `postgres-0` не перейдет в статус `Running` и `Ready`. \n\nПри масштабировании вниз удаление происходит в обратном порядке (сначала 2, затем 1). При удалении пода связанный с ним том `PersistentVolumeClaim` **никогда не удаляется автоматически**, защищая данные базы от случайной потери.",
    "pitfalls": "1. Использование обычного ClusterIP вместо Headless: CoreDNS не создаст индивидуальные DNS-записи для каждого пода (`postgres-0.postgres-headless`), что нарушит репликацию Master-Replica.\n2. Ручное удаление PVC: может привести к необратимой потере данных.\n3. Развертывание StatefulSet на нодах в разных зонах доступности (Multi-AZ) без настройки топологии томов (CSI volume binding mode: WaitForFirstConsumer).",
    "bigtech_interview": "**Вопрос с собеседования:** В чем ключевые различия между `Deployment` и `StatefulSet` в Kubernetes?\n**Ответ:** \n1. **Идентичность подов:** В Deployment поды взаимозаменяемы и имеют случайные имена (`app-6b8c-x9z`); в StatefulSet каждый под имеет уникальный постоянный индекс (`db-0`, `db-1`) и стабильное DNS-имя.\n2. **Порядок развертывания:** Deployment создает поды параллельно; StatefulSet — строго последовательно по возрастанию индекса.\n3. **Хранилище данных:** В Deployment поды либо не имеют дисков, либо делят общий ReadWriteMany том; в StatefulSet через `volumeClaimTemplates` каждый под получает собственный выделенный диск, который повторно монтируется к тому же поду даже после его переноса на другую ноду."
  },
  {
    "num": 35,
    "title": "Обеспечение доступности при обслуживании кластера: PodDisruptionBudget (PDB)",
    "task": "Настрой **PodDisruptionBudget (PDB)**: `minAvailable: 2` или `maxUnavailable: 1`. Защита от voluntary disruptions: node drain, cluster upgrade. Покажи, что ensures availability during maintenance.",
    "theory": "В процессе эксплуатации кластера регулярно происходят добровольные прерывания (**Voluntary Disruptions**):\n- Обновление версии Kubernetes на нодах (`kubeadm upgrade`).\n- Перезагрузка нод для установки патчей ядра Linux.\n- Вывод ноды из эксплуатации инженером командой `kubectl drain <node>`.\n- Сжатие кластера (Scale Down) облачным автоскейлером.\n\nБез защитных механизмов `kubectl drain` может одномоментно остановить все поды сервиса на ноде, вызвав недоступность (Downtime).\n\n**PodDisruptionBudget (PDB) (`apiVersion: policy/v1`)**:\n- Гарантирует минимальное количество подов, обязанных оставаться доступными во время обслуживания.\n- Параметры: `minAvailable: 2` или `maxUnavailable: 1`.",
    "step_by_step": "1. Создайте манифест `pdb.yaml` с селектором вашего сервиса.\n2. Задайте `minAvailable: 2` (для сервиса из 3 реплик).\n3. Примените манифест: `kubectl apply -f pdb.yaml`.\n4. Проверьте текущий статус бюджета: `kubectl get pdb`.\n5. Попробуйте выполнить drain ноды и убедитесь, что K8s не выселяет поды сверх лимита.",
    "code_blocks": [
      {
        "filename": "pdb.yaml",
        "lang": "yaml",
        "code": "apiVersion: policy/v1\nkind: PodDisruptionBudget\nmetadata:\n  name: payment-service-pdb\nspec:\n  minAvailable: 2 # Минимум 2 реплики обязаны работать в любой момент времени\n  selector:\n    matchLabels:\n      app: payment-service"
      },
      {
        "filename": "test-drain.sh",
        "lang": "bash",
        "code": "# Просмотр статуса PDB\nkubectl get pdb payment-service-pdb\n# Вывод:\n# NAME                  MIN AVAILABLE   MAX UNAVAILABLE   ALLOWED DISRUPTIONS   AGE\n# payment-service-pdb   2               N/A               1                     5m\n\n# Попытка вывода ноды из эксплуатации:\n# K8s выселит 1 под, дождется старта новой реплики на другой ноде,\n# и только потом разрешит выселить следующий под!\nkubectl drain node-1 --ignore-daemonsets --delete-emptydir-data"
      }
    ],
    "under_the_hood": "Когда инженер выполняет `kubectl drain`, утилита вызывает API выселения: `POST /api/v1/namespaces/default/pods/<name>/eviction`. \n\nAPI Server обращается к контроллеру PDB. Контроллер проверяет:\n$\\text{CurrentHealthyPods} - 1 \\ge \\text{minAvailable}$\nЕсли условие истинно, выселение разрешается. Если условие ложно, API Server возвращает ошибку `429 Too Many Requests (Cannot evict pod as it would violate the pod's disruption budget)`, и команда drain ожидает появления новых готовых подов.",
    "pitfalls": "1. Задание `minAvailable: 100%` или `maxUnavailable: 0`: ноду с такими подами невозможно будет заэвакуировать через `kubectl drain`, команда зависнет навсегда.\n2. PDB не защищает от **Involuntary Disruptions** (аварии железа, внезапное отключение питания сервера, kernel panic): бюджет действует только на плановые действия через Eviction API.\n3. Забытый PDB для одиночных подов (`replicas: 1`): drain приведет к гарантированному даунтайму.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между Voluntary и Involuntary Disruptions в Kubernetes и что защищает сервис от каждого из них?\n**Ответ:** \n- **Voluntary Disruptions (Плановые прерывания):** Инициируются администратором или автоматикой (`kubectl drain`, обновление нод, Cluster Autoscaler, выселение VPA). От них сервис **защищает `PodDisruptionBudget` (PDB)**, блокируя выселение сверх бюджета.\n- **Involuntary Disruptions (Внеплановые аварии):** Аппаратный сбой сервера, падение гипервизора, сбой питания, потеря сети. PDB от них спасти не может. Защитой служит **высокий фактор репликации (`replicas >= 3`)** и распределение подов по разным зонам доступности через **`podAntiAffinity`**."
  },
  {
    "num": 36,
    "title": "Два способа монтирования ConfigMap: переменные окружения против файлов в Volume",
    "task": "Создайте **ConfigMap** для конфигурации приложения. Смонтируйте его как env vars и как файлы.",
    "theory": "ConfigMap можно подключить в под двумя способами, каждый из которых имеет свои особенности:\n1. **Переменные окружения (`envFrom` / `valueFrom`):**\n   - Простота доступа в коде (`os.Getenv`).\n   - Значения передаются процессу один раз при старте.\n   - **Не обновляются динамически:** изменение ConfigMap не изменит переменные в работающем процессе без рестарта пода.\n2. **Монтирование в том (`volumes` + `volumeMounts`):**\n   - ConfigMap монтируется как директория, где каждый ключ становится отдельным файлом, а значение — содержимым файла.\n   - **Динамическое обновление (Hot Reload):** Kubelet автоматически синхронизирует изменения файла в течение 1 минуты без перезапуска пода.",
    "step_by_step": "1. Создайте `configmap.yaml` с файлом конфигурации `app.json`.\n2. В `deployment.yaml` настройте том `configMap` и `volumeMounts: mountPath: /etc/config`.\n3. В коде Go прочитайте конфигурационный файл из пути `/etc/config/app.json`.\n4. Измените ConfigMap командой `kubectl edit configmap`.\n5. Убедитесь через `cat /etc/config/app.json` внутри пода, что файл обновился автоматически.",
    "code_blocks": [
      {
        "filename": "config-volume.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: dynamic-config\ndata:\n  app.json: |\n    {\n      \"rate_limit\": 500,\n      \"feature_flags\": {\n        \"new_checkout\": true\n      }\n    }\n---\napiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: hot-reload-app\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: hot-reload\n  template:\n    metadata:\n      labels:\n        app: hot-reload\n    spec:\n      volumes:\n        - name: config-volume\n          configMap:\n            name: dynamic-config\n      containers:\n        - name: app\n          image: alpine:3.21\n          command: [\"/bin/sh\", \"-c\"]\n          args:\n            - |\n              while true; do\n                echo \"--- Текущий конфиг ---\"\n                cat /etc/config/app.json\n                sleep 10\n              done\n          volumeMounts:\n            - name: config-volume\n              mountPath: /etc/config\n              readOnly: true"
      },
      {
        "filename": "watcher.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n\t\"time\"\n)\n\n// ReadConfig читает конфигурационный файл с диска\nfunc ReadConfig(path string) (string, error) {\n\tdata, err := os.ReadFile(path)\n\tif err != nil {\n\t\treturn \"\", err\n\t}\n\treturn string(data), nil\n}\n\nfunc main() {\n\tpath := \"/etc/config/app.json\"\n\tfor {\n\t\tcfg, err := ReadConfig(path)\n\t\tif err != nil {\n\t\t\tfmt.Printf(\"Ошибка чтения: %v\\n\", err)\n\t\t} else {\n\t\t\tfmt.Printf(\"[%s] Прочитан конфиг: %s\\n\", time.Now().Format(\"15:04:05\"), cfg)\n\t\t}\n\t\ttime.Sleep(10 * time.Second)\n\t}\n}"
      }
    ],
    "under_the_hood": "Kubelet монтирует том ConfigMap через символические ссылки (symlinks):\n`/etc/config/app.json -> ..data/app.json -> ..2026_09_04_10_00_00/app.json`\nПри изменении ConfigMap Kubelet скачивает новую версию в скрытую директорию с новым временным штампом и атомарно переключает симлинк `..data`. \n\nБиблиотеки на Go (например, `fsnotify`) могут слушать события изменения директории и мгновенно перезагружать конфигурацию без остановки обслуживания трафика.",
    "pitfalls": "1. Использование `subPath`: если смонтировать файл через `volumeMounts.subPath`, динамическое обновление **отключается** из-за особенностей механизмов bind mount в ядре Linux.\n2. Задержка синхронизации: обновление файла занимает от 10 до 60 секунд (период синхронизации Kubelet cache).\n3. Попытка записи в смонтированный том: том доступен только для чтения (`readOnly: true`).",
    "bigtech_interview": "**Вопрос с собеседования:** Почему при монтировании ConfigMap через `subPath` hot-reload не работает, и как правильно организовать Hot Reload конфигурации в Go?\n**Ответ:** При использовании `subPath` файл монтируется напрямую через системный вызов `mount --bind` на уровне inode конкретного файла. Когда Kubelet обновляет ConfigMap, он создает новый файл с новым inode и переключает симлинк директории. Но bind-mount жестко привязан к старому inode, поэтому файл внутри контейнера остается старым навсегда. \nПравильное решение для Hot Reload:\n1. Монтировать всю директорию целиком (без `subPath`).\n2. В Go использовать библиотеку `fsnotify` для отслеживания изменений симлинка `..data` в директории и атомарно перечитывать конфиг в память (`atomic.Pointer[Config]`)."
  },
  {
    "num": 37,
    "title": "Базовая подготовка Pod манифеста и инспекция логов через kubectl",
    "task": "**Подготовка (Pod)**: Напиши файл `pod.yaml`. Опиши в нем сущность `Pod`, укажи свой Docker-образ (из упр. 591). Запусти через `kubectl apply -f pod.yaml`. Проверь статус через `kubectl get pods`. Посмотри логи через `kubectl logs my-pod`.",
    "theory": "Практическое закрепление базовых операций с подами:\n- Описание манифеста `pod.yaml` с образом приложения.\n- Развертывание в кластере через `kubectl apply -f pod.yaml`.\n- Инспекция фаз жизненного цикла пода (`Pending`, `ContainerCreating`, `Running`, `Completed`, `Failed`).\n- Чтение стандартных потоков вывода через `kubectl logs`.",
    "step_by_step": "1. Создайте файл `pod.yaml`.\n2. Задайте имя `my-pod` и контейнер с образом `k8s-demo`.\n3. Примените манифест: `kubectl apply -f pod.yaml`.\n4. Проверьте запуск пода: `kubectl get pods my-pod`.\n5. Посмотрите логи: `kubectl logs my-pod`.",
    "code_blocks": [
      {
        "filename": "pod.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Pod\nmetadata:\n  name: my-pod\n  labels:\n    app: training-demo\nspec:\n  containers:\n    - name: app\n      image: alpine:3.21\n      command: [\"/bin/sh\", \"-c\"]\n      args:\n        - |\n          echo \"Инициализация учебного пода...\"\n          echo \"Сервис успешно стартовал в пространстве K8s!\"\n          sleep 3600"
      },
      {
        "filename": "commands.sh",
        "lang": "bash",
        "code": "# 1. Применение манифеста пода\nkubectl apply -f pod.yaml\n\n# 2. Проверка статуса\nkubectl get pod my-pod -o wide\n\n# 3. Чтение логов контейнера\nkubectl logs my-pod\n\n# 4. Удаление пода\nkubectl delete pod my-pod"
      }
    ],
    "under_the_hood": "Когда контейнер пишет в stdout или stderr, рантайм `containerd` перенаправляет эти потоки в JSON/CRI-логи на диске ноды:\n`/var/log/pods/<namespace>_<pod_name>_<pod_id>/<container_name>/0.log`\nКоманда `kubectl logs` делает HTTP GET запрос на API Server, который открывает стрим к демону `kubelet` ноды, а Kubelet считывает файл лога с диска.",
    "pitfalls": "1. Запись логов в локальные файлы внутри контейнера вместо stdout: логи теряются при удалении пода и недоступны через `kubectl logs`.\n2. Переполнение диска ноды: отсутствие ротации логов в настройках Kubelet/containerd.\n3. Падение пода при запуске фоновых демонов без процесса на переднем плане (PID 1 завершается, и контейнер останавливается).",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в Kubernetes категорически рекомендуется писать логи в stdout/stderr процесса, а не в файлы внутри контейнера?\n**Ответ:** Следование принципу 12-Factor App (Logs as Event Streams). \nКонтейнер должен быть stateless: у него нет гарантий сохранения локального диска при перезапуске. Запись в stdout позволяет K8s-инфраструктуре единообразно перехватывать логи на уровне рантайма (containerd), ротировать их на ноде и автоматически собирать агентными сборщиками (Fluentbit, Vector, Promtail) в централизованные хранилища (Elasticsearch, Loki, ClickHouse) без необходимости монтировать тома или настраивать пути внутри каждого сервиса."
  },
  {
    "num": 38,
    "title": "Маршрутизация внешнего HTTP-трафика с NGINX Ingress Controller",
    "task": "**[Ingress]**: Настрой `Ingress` (с использованием NGINX Ingress Controller), чтобы маршрутизировать HTTP-трафик с локального хоста на твой `Service`.",
    "theory": "В то время как `Service` балансирует трафик на транспортном уровне (L4 TCP), **`Ingress`** управляет входящим трафиком на прикладном уровне (L7 HTTP/HTTPS):\n- Маршрутизация по доменным именам (Virtual Hosting: `api.example.com` vs `auth.example.com`).\n- Маршрутизация по путям URL (`/orders`, `/users`).\n- Терминация SSL/TLS сертификатов в единой точке.\n- Интеграция с Ingress-контроллером (NGINX Ingress Controller, Traefik, HAProxy), который динамически обновляет конфигурацию обратного прокси.",
    "step_by_step": "1. Убедитесь, что в кластере запущен NGINX Ingress Controller.\n2. Создайте `ingress.yaml` с `ingressClassName: nginx`.\n3. Опишите правило маршрутизации хоста `api.local` на сервис `backend-service:80`.\n4. Примените манифест: `kubectl apply -f ingress.yaml`.\n5. Выполните запрос с заголовком Host: `curl -H \"Host: api.local\" http://<ingress-ip>`.",
    "code_blocks": [
      {
        "filename": "ingress.yaml",
        "lang": "yaml",
        "code": "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: app-ingress\n  annotations:\n    nginx.ingress.kubernetes.io/rewrite-target: /\n    nginx.ingress.kubernetes.io/proxy-read-timeout: \"60\"\nspec:\n  ingressClassName: nginx\n  rules:\n    - host: api.local\n      http:\n        paths:\n          - path: /\n            pathType: Prefix\n            backend:\n              service:\n                name: backend-service\n                port:\n                  number: 80"
      },
      {
        "filename": "service-backend.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Service\nmetadata:\n  name: backend-service\nspec:\n  type: ClusterIP\n  selector:\n    app: backend\n  ports:\n    - port: 80\n      targetPort: 8080"
      },
      {
        "filename": "test-ingress.sh",
        "lang": "bash",
        "code": "# Просмотр адреса Ingress\nkubectl get ingress app-ingress\n\n# Тестовый вызов с эмуляцией DNS хоста api.local\ncurl -v -H \"Host: api.local\" http://localhost/"
      }
    ],
    "under_the_hood": "NGINX Ingress Controller работает как Pod в кластере. Контроллер слушает изменения ресурсов `Ingress` через K8s API. \n\nПри появлении манифеста контроллер рендерит конфигурационный файл `/etc/nginx/nginx.conf` и выполняет команду `nginx -s reload` (или динамически обновляет апстримы через Lua-модуль без сброса соединений). Входящий трафик от клиентов направляется напрямую на IP-адреса подов, минуя kube-proxy.",
    "pitfalls": "1. Забытый `ingressClassName: nginx`: в современных версиях K8s без явного класса Ingress будет проигнорирован контроллером.\n2. Ошибки с `rewrite-target`: регулярные выражения в путях могут привести к неожиданной перезаписи URL запросов к бэкенду.\n3. Отсутствие Ingress-контроллера в кластере: сам по себе манифест `Ingress` является лишь декларацией; без запущенного контроллера трафик маршрутизироваться не будет.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем эволюционная разница между классическим `Ingress` и современным стандартом `Gateway API` в Kubernetes?\n**Ответ:** Классический `Ingress` — монолитный ресурс, смешивающий в одном YAML ответственность сетевого администратора (домены, TLS, провайдеры) и продуктового разработчика (пути маршрутизации). Кроме того, расширенные настройки (rate limiting, header rewrite) требовали вендор-специфичных аннотаций (`nginx.ingress...`), несовместимых между контроллерами. \n**Gateway API** разделяет роли через независимые ресурсы:\n- `GatewayClass` (инфраструктурная платформа),\n- `Gateway` (сетевые инженеры: слушатели, TLS, IP),\n- `HTTPRoute` / `GRPCRoute` (разработчики сервисов: маршрутизация путей и канареечные веса), обеспечивая строгий ролевой доступ (RBAC) и нативную переносимость между любыми провайдерами."
  },
  {
    "num": 39,
    "title": "Управление размещением подов: Affinity, Anti-Affinity и распределение по нодам",
    "task": "Настрой **Affinity/Anti-affinity**: `podAntiAffinity: preferredDuringSchedulingIgnoredDuringExecution` — распредели pods across nodes. `podAffinity` — co-locate related pods. `nodeAffinity` — run on specific nodes (GPU, SSD). Покажи topology spread.",
    "theory": "По умолчанию планировщик K8s размещает поды на любых свободных нодах. В HighLoad системах требуется точное управление топологией:\n1. **`podAntiAffinity` (Разнесение подов):** Запрещает или не рекомендует размещать реплики одного и того же сервиса на одном физическом сервере (`topologyKey: kubernetes.io/hostname`) или в одной зоне доступности (AZ). При падении одной ноды сервис гарантированно сохраняет 100% работоспособность.\n2. **`podAffinity` (Сближение подов):** Размещает тесно взаимодействующие микросервисы (например, API и кэш) на одной ноде для минимизации задержек сети.\n3. **`nodeAffinity`:** Привязывает поды к нодам со специфическими метками (ноды с SSD, GPU или мощным CPU).",
    "step_by_step": "1. Опишите в `deployment.yaml` секцию `affinity.podAntiAffinity`.\n2. Используйте мягкое правило `preferredDuringSchedulingIgnoredDuringExecution` с весом 100.\n3. Задайте `topologyKey: \"kubernetes.io/hostname\"`.\n4. Разверните 3 реплики сервиса на кластере из нескольких нод.\n5. Убедитесь через `kubectl get pods -o wide`, что поды распределились по разным нодам.",
    "code_blocks": [
      {
        "filename": "anti-affinity-deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: ha-service\nspec:\n  replicas: 3\n  selector:\n    matchLabels:\n      app: ha-service\n  template:\n    metadata:\n      labels:\n        app: ha-service\n    spec:\n      affinity:\n        podAntiAffinity:\n          # Мягкое правило: K8s постарается разнести поды по разным серверам,\n          # но если серверов меньше 3, поды все равно запустятся!\n          preferredDuringSchedulingIgnoredDuringExecution:\n            - weight: 100\n              podAffinityTerm:\n                labelSelector:\n                  matchExpressions:\n                    - key: app\n                      operator: In\n                      values:\n                        - ha-service\n                topologyKey: \"kubernetes.io/hostname\"\n      containers:\n        - name: app\n          image: alpine:3.21\n          command: [\"sleep\", \"3600\"]"
      },
      {
        "filename": "verify-spread.sh",
        "lang": "bash",
        "code": "# Просмотр распределения подов по физическим нодам:\nkubectl get pods -l app=ha-service -o wide\n\n# Пример вывода (каждый под на своей ноде):\n# NAME                          READY   STATUS    NODE\n# ha-service-5899fcb6cb-2k9x4   1/1     Running   node-worker-1\n# ha-service-5899fcb6cb-78v2m   1/1     Running   node-worker-2\n# ha-service-5899fcb6cb-w9p4j   1/1     Running   node-worker-3"
      }
    ],
    "under_the_hood": "`kube-scheduler` вычисляет топологию в две фазы:\n1. **Filtering (Фильтрация):** Отсеивание нод, не удовлетворяющих жестким требованиям (`requiredDuringScheduling...`).\n2. **Scoring (Оценка):** Присвоение баллов оставшимся нодам. Для каждого правила `preferred...` планировщик добавляет `weight` (от 1 до 100) нодам, на которых еще нет подов с меткой `app: ha-service`. Под назначается на ноду с наибольшим суммарным баллом.",
    "pitfalls": "1. Использование жесткого правила `requiredDuringScheduling...` при малом числе нод: если в кластере 2 ноды, а реплик 3, третья реплика навсегда зависнет в статусе `Pending`.\n2. Высокая вычислительная сложность Scoring при сотнях тысяч подов в кластере: тяжелые правила Affinity могут замедлить работу планировщика.\n3. Опечатка в `topologyKey`.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между `preferredDuringSchedulingIgnoredDuringExecution` и `requiredDuringSchedulingIgnoredDuringExecution`?\n**Ответ:** \n- **`required...` (Hard affinity):** Обязательное строгое требование. Если в кластере нет подходящей ноды (или на всех нодах уже есть такой под), планировщик **откажется запускать под**, оставив его в статусе `Pending`.\n- **`preferred...` (Soft affinity):** Желательное мягкое предпочтение. Планировщик постарается выбрать наилучшую ноду в соответствии с правилом, но если свободных нод нет, он **все равно разместит под** на любой доступной ноде, отдавая приоритет доступности сервиса."
  },
  {
    "num": 40,
    "title": "Управление конфиденциальными данными через Secret со stringData",
    "task": "Создайте **Secret** для sensitive данных (DB password, API keys). Используйте `stringData` для удобного задания в plain text.",
    "theory": "Закрепление работы с конфиденциальными параметрами (API-ключи, токены, пароли):\n- Поле `stringData` упрощает составление манифестов инженерами: значения записываются открытым текстом в YAML, а K8s API сервер при сохранении в базу etcd автоматически преобразует их в кодировку Base64.\n- Подключение в под осуществляется через `valueFrom.secretKeyRef` или монтирование тома `secret`.",
    "step_by_step": "1. Создайте манифест `secret.yaml` с `stringData`.\n2. Добавьте API-токены и ключи доступа.\n3. В `pod.yaml` подключите секреты.\n4. В коде Go прочитайте значения и убедитесь в их корректности.\n5. Примените манифесты и проверьте безопасность окружения.",
    "code_blocks": [
      {
        "filename": "secret.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Secret\nmetadata:\n  name: payment-credentials\ntype: Opaque\nstringData:\n  STRIPE_SECRET_KEY: \"sk_live_51MzXYZ1234567890abcdef\"\n  WEBHOOK_SIGNING_SECRET: \"whsec_abcdef1234567890\" "
      },
      {
        "filename": "pod.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Pod\nmetadata:\n  name: payment-processor\nspec:\n  containers:\n    - name: processor\n      image: alpine:3.21\n      command: [\"/bin/sh\", \"-c\", \"echo 'Credentials loaded'; sleep 3600\"]\n      env:\n        - name: STRIPE_KEY\n          valueFrom:\n            secretKeyRef:\n              name: payment-credentials\n              key: STRIPE_SECRET_KEY"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n)\n\nfunc main() {\n\tstripeKey := os.Getenv(\"STRIPE_KEY\")\n\tif stripeKey == \"\" {\n\t\tpanic(\"STRIPE_KEY отсутствует в окружении!\")\n\t}\n\tfmt.Printf(\"Платежный модуль инициализирован. Длина ключа: %d байт\\n\", len(stripeKey))\n}"
      }
    ],
    "under_the_hood": "API-сервер K8s при получении объекта Secret с полем `stringData` выполняет итерацию по словарю, конвертирует строковые значения в байты, применяет стандартное кодирование `base64.StdEncoding.EncodeToString()` и сохраняет их в словарь `data`. \n\nПоле `stringData` используется только для записи; при обратном чтении (`kubectl get secret -o yaml`) всегда возвращается Base64-поле `data`.",
    "pitfalls": "1. Сохранение файла со `stringData` в репозиторий Git: случайное раскрытие боевых секретов.\n2. Спецсимволы новой строки в `stringData`: случайный перенос строки в конце токена может сломать проверку цифровой подписи в Go API клиенте.\n3. Отсутствие прав RBAC на просмотр секретов: разработчики должны иметь доступ только к тем секретам, которые требуются их сервису.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему команда `kubectl get secret` доступна разработчикам только в dev-кластерах, но строго закрыта в production?\n**Ответ:** Стандартные K8s Secret хранятся в Base64. Команда `kubectl get secret <name> -o yaml` позволяет любому пользователю с правами чтения мгновенно декодировать боевые пароли к БД и приватные ключи API (`base64 -d`), что нарушает требования стандартов безопасности (PCI DSS, ISO 27001, SOC 2). В проде права на чтение Secret выдаются только системным сервис-аккаунтам контроллеров, а инженеры получают доступ по схеме Zero Standing Privileges (ZSP) через временные токены."
  },
  {
    "num": 41,
    "title": "Изоляция рабочих нагрузок: механизмы Taints и Tolerations",
    "task": "Настрой **Taints и Tolerations**: `node taint: dedicated=gpu:NoSchedule`. Pod с `toleration: key: dedicated, operator: Equal, value: gpu, effect: NoSchedule` может запланироваться на GPU node. Покажи dedicated node pools.",
    "theory": "Механизм **Taints (Окрашивания)** и **Tolerations (Терпимости)** позволяет нодам кластера «отталкивать» определенный набор подов:\n- Нода помечается окрашиванием (Taint): `kubectl taint nodes gpu-node dedicated=gpu:NoSchedule`. Это означает: «Ни один под не может быть запланирован на эту ноду, если у него нет соответствующей терпимости (Toleration)».\n- Под объявляет терпимость (`tolerations`): `key: dedicated, value: gpu, effect: NoSchedule`.\n\nСценарии применения в BigTech:\n1. **Выделенные нод-пулы с GPU/TPU:** Защита дорогостоящих серверов с видеокартами от случайного запуска обычных легковесных микросервисов.\n2. **Dedicated Infrastructure:** Изоляция чувствительных баз данных или финансовых платежных сервисов на отдельных физических серверах (Bare-metal нодах).\n3. **Реакция на сбои нод:** Автоматические системные taints (`node.kubernetes.io/not-ready:NoExecute`).",
    "step_by_step": "1. Окрасьте целевую ноду: `kubectl taint nodes node-gpu-1 dedicated=gpu:NoSchedule`.\n2. В манифесте `deployment.yaml` опишите секцию `spec.template.spec.tolerations`.\n3. Укажите оператор `Equal`, ключ `dedicated`, значение `gpu` и эффект `NoSchedule`.\n4. Разверните сервис и убедитесь через `kubectl get pods -o wide`, что под запланирован на GPU-ноду.\n5. Убедитесь, что поды без `tolerations` не попадают на эту ноду.",
    "code_blocks": [
      {
        "filename": "gpu-deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: ml-inference\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: ml-inference\n  template:\n    metadata:\n      labels:\n        app: ml-inference\n    spec:\n      tolerations:\n        - key: \"dedicated\"\n          operator: \"Equal\"\n          value: \"gpu\"\n          effect: \"NoSchedule\"\n      # В дополнение к toleration используем nodeSelector для точной посадки на GPU:\n      nodeSelector:\n        accelerator: \"nvidia-tesla-v100\"\n      containers:\n        - name: inference\n          image: ghcr.io/company/ml-model:v1.0.0\n          resources:\n            limits:\n              nvidia.com/gpu: 1"
      },
      {
        "filename": "taint-commands.sh",
        "lang": "bash",
        "code": "# 1. Окрашивание ноды: запретить планирование обычных подов\nkubectl taint nodes worker-gpu-1 dedicated=gpu:NoSchedule\n\n# 2. Добавление метки ноды для nodeSelector\nkubectl label nodes worker-gpu-1 accelerator=nvidia-tesla-v100\n\n# 3. Проверка существующих taints на ноде\nkubectl describe node worker-gpu-1 | grep Taints"
      }
    ],
    "under_the_hood": "`kube-scheduler` на этапе фильтрации (Node Filtering) инспектирует список `node.spec.taints`. Для каждого taint ноды планировщик ищет соответствующую запись в `pod.spec.tolerations`. \n\nЭффекты taints:\n- `NoSchedule`: Новые поды без toleration не могут быть запланированы на ноду, но уже работающие поды не трогаются.\n- `PreferNoSchedule`: Планировщик старается избегать ноды, но назначит под при отсутствии альтернатив.\n- `NoExecute`: Поды без toleration не только не назначаются, но и **немедленно выселяются (evicted)** с ноды!",
    "pitfalls": "1. Заблуждение о привязке: `toleration` **не заставляет** под идти на эту конкретную ноду, он лишь **разрешает** ему там запуститься! Чтобы под пошел строго на GPU ноду, необходимо комбинировать `tolerations` с `nodeSelector` или `nodeAffinity`.\n2. Опечатка в ключе или регистре (case-sensitive): под зависнет в статусе `Pending`.\n3. Забытое снятие тайнта при выводе ноды из карантина: `kubectl taint nodes node-1 key:NoSchedule-`.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между эффектами тайнта `NoSchedule` и `NoExecute`?\n**Ответ:** \n- **`NoSchedule`** действует только на **новые поды** в момент работы планировщика. Поды, которые уже работают на ноде, продолжают работать.\n- **`NoExecute`** действует на **все поды**: если нода получает таинт `NoExecute`, Kubelet немедленно выселяет (убивает) все работающие поды, не имеющие соответствующей терпимости (`toleration`). Это используется для автоматической эвакуации подов с умирающих нод (`node.kubernetes.io/unreachable:NoExecute` с параметром `tolerationSeconds: 300`)."
  },
  {
    "num": 42,
    "title": "Сравнение механизмов доставки конфигурации: Env Vars против Mounted Volumes",
    "task": "Изучите разницу между env vars и mounted volumes для ConfigMap/Secret (первый не обновляется без restart, второй — обновляется).",
    "theory": "Критическое архитектурное сравнение двух подходов монтирования ConfigMap и Secret:\n1. **Переменные окружения (`env` / `envFrom`):**\n   - **Плюсы:** Мгновенный и нативный доступ в Go через `os.Getenv()`, отсутствие операций с диском.\n   - **Минусы:** **Статичность**. При изменении ConfigMap в кластере переменные окружения запущенного процесса Linux обновиться не могут. Требуется полный перезапуск подов (`kubectl rollout restart`).\n2. **Монтирование в том (`volumes` + `volumeMounts`):**\n   - **Плюсы:** **Динамичность**. Kubelet автоматически обновляет файлы в директории пода в течение 60 секунд после правки ConfigMap в кластере без рестарта процесса.\n   - **Минусы:** Требуется логика чтения файла или подписка на файловые события (`fsnotify`) в коде Go.",
    "step_by_step": "1. Создайте ConfigMap с параметром `FEATURE_ENABLED: \"false\"`.\n2. Создайте второй ключ с файлом конфигурации `features.json`.\n3. Подключите первый ключ через `env`, а второй — через `volumeMounts: mountPath: /app/config`.\n4. Измените оба значения в кластере через `kubectl edit configmap`.\n5. Сравните вывод: переменная окружения осталась старой, а смонтированный файл обновился!",
    "code_blocks": [
      {
        "filename": "comparison-pod.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Pod\nmetadata:\n  name: config-compare\nspec:\n  volumes:\n    - name: config-vol\n      configMap:\n        name: test-cfg\n  containers:\n    - name: app\n      image: alpine:3.21\n      command: [\"/bin/sh\", \"-c\"]\n      args:\n        - |\n          while true; do\n            echo \"ENV VAR: $MY_ENV_FLAG\"\n            echo \"VOLUME FILE: $(cat /app/config/features.json 2>/dev/null)\"\n            sleep 15\n          done\n      env:\n        - name: MY_ENV_FLAG\n          valueFrom:\n            configMapKeyRef:\n              name: test-cfg\n              key: FEATURE_FLAG\n      volumeMounts:\n        - name: config-vol\n          mountPath: /app/config"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n\t\"time\"\n)\n\nfunc main() {\n\tenvVal := os.Getenv(\"MY_ENV_FLAG\")\n\tfilePath := \"/app/config/features.json\"\n\n\tfor {\n\t\tfileContent, err := os.ReadFile(filePath)\n\t\tif err != nil {\n\t\t\tfileContent = []byte(\"ошибка чтения\")\n\t\t}\n\t\tfmt.Printf(\"[%s] Env: %s | File: %s\\n\",\n\t\t\ttime.Now().Format(\"15:04:05\"), envVal, string(fileContent))\n\t\ttime.Sleep(15 * time.Second)\n\t}\n}"
      }
    ],
    "under_the_hood": "Переменные окружения процесса в Linux записываются в область стека процесса при вызове `execve` и не могут быть модифицированы извне ядром без ведома процесса. \n\nДля файлов в томе Kubelet периодически синхронизирует локальное состояние ConfigMap, создавая новую директорию и атомарно переключая символическую ссылку через `rename()`. Это делает чтение файла всегда консистентным.",
    "pitfalls": "1. Ожидание, что `os.Getenv` волшебным образом обновится при изменении ConfigMap в K8s: одна из самых частых ошибок начинающих Go-разработчиков.\n2. Использование `subPath`: при монтировании конкретного файла через `subPath` механизм симлинков отключается, и файл на диске также перестает обновляться!\n3. Кэширование файла в коде: если вы прочитали файл один раз в функции `init()`, динамическое обновление на диске никак не повлияет на переменную в памяти Go.",
    "bigtech_interview": "**Вопрос с собеседования:** Если монтирование тома ConfigMap поддерживает автоматическое обновление файлов, почему многие команды все равно предпочитают переменные окружения и `kubectl rollout restart`?\n**Ответ:** \n1. **Детерминизм и версионирование:** При `rollout restart` обновление происходит плавно по стратегии RollingUpdate с контролем готовности подов и возможностью мгновенного отката (`rollout undo`).\n2. **Проблема рассинхронизации (In-flight Drift):** При обновлении файла на лету Kubelet обновляет ноды асинхронно с задержкой до 1 минуты. В этот период разные реплики сервиса работают с разными версиями конфигурации, что может приводить к трудноуловимым багам в распределенной бизнес-логике."
  },
  {
    "num": 43,
    "title": "Плавное завершение (Graceful Shutdown): рассинхронизация SIGTERM и сетевых маршрутов",
    "task": "**Плавное завершение (Graceful Shutdown) в Kubernetes**: При удалении пода K8s отправляет сигнал `SIGTERM` и одновременно удаляет его адрес из Service. Однако эти процессы происходят асинхронно! Напишите код в Go: при получении сигнала `SIGTERM` программа должна подождать 5–10 секунд (продолжая обрабатывать входящие запросы, пока K8s обновляет сетевые маршруты) и только после этого закрыть активные соединения и завершить процесс. Это позволит избежать ошибок 502 (Bad Gateway) у клиентов при деплое новых версий.",
    "theory": "При удалении пода (деплой новой версии, масштабирование вниз) в Kubernetes происходят **два параллельных асинхронных процесса**:\n1. **Процесс остановки пода:** Kubelet отправляет контейнеру сигнал `SIGTERM` и запускает таймер `terminationGracePeriodSeconds` (30 с).\n2. **Процесс обновления сети:** Контроллер EndpointSlice исключает IP пода из списка, API Server уведомляет все ноды, и `kube-proxy` на каждой ноде перестраивает правила iptables/IPVS.\n\n**Критическая проблема рассинхронизации:**\nПроцесс обновления правил iptables на всех нодах занимает от 1 до 5 секунд. Если Go-сервер при получении `SIGTERM` немедленно закроет слушающий сокет (`server.Close()`), то клиенты, чьи запросы придут через еще не обновившиеся правила сети в течение этих 2-3 секунд, получат сетевую ошибку **`502 Bad Gateway`** или `Connection Refused`!\n\n**Решение:**\nПри получении `SIGTERM` процесс Go обязан **выждать паузу в 5–10 секунд** (продолжая принимать новые входящие запросы, пока K8s убирает маршруты), и только затем вызвать `server.Shutdown(ctx)` для завершения текущих соединений.",
    "step_by_step": "1. Перехватите сигналы `os.Interrupt`, `syscall.SIGTERM` через буферизированный канал `chan os.Signal, 1`.\n2. При получении сигнала выполните задержку `time.Sleep(5 * time.Second)`.\n3. Создайте контекст с таймаутом `context.WithTimeout(context.Background(), 20*time.Second)`.\n4. Вызовите метод `server.Shutdown(ctx)` для корректного завершения активных соединений.\n5. Задайте в манифесте `terminationGracePeriodSeconds: 45`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n\t\"os/signal\"\n\t\"syscall\"\n\t\"time\"\n)\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/api/work\", func(w http.ResponseWriter, r *http.Request) {\n\t\ttime.Sleep(500 * time.Millisecond) // Имитация обработки запроса\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"SUCCESS\"))\n\t})\n\n\tserver := &http.Server{\n\t\tAddr:         \":8080\",\n\t\tHandler:      mux,\n\t\tReadTimeout:  10 * time.Second,\n\t\tWriteTimeout: 10 * time.Second,\n\t}\n\n\tgo func() {\n\t\tfmt.Println(\"Сервер слушает на :8080\")\n\t\tif err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {\n\t\t\tfmt.Printf(\"Ошибка сервера: %v\\n\", err)\n\t\t}\n\t}()\n\n\t// Буферизированный канал сигналов ОС\n\tstop := make(chan os.Signal, 1)\n\tsignal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)\n\n\tsig := <-stop\n\tfmt.Printf(\"Получен сигнал [%v]. Начинаем фазу ожидания обновления сетевых маршрутов...\\n\", sig)\n\n\t// Шаг 1: Пауза для того, чтобы kube-proxy и Ingress успели исключить IP пода из Endpoints\n\ttime.Sleep(6 * time.Second)\n\n\tfmt.Println(\"Сетевые маршруты K8s сброшены. Выполняем graceful shutdown соединений...\")\n\n\t// Шаг 2: Завершение текущих активных клиентских запросов\n\tctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)\n\tdefer cancel()\n\n\tif err := server.Shutdown(ctx); err != nil {\n\t\tfmt.Printf(\"Ошибка при Shutdown: %v\\n\", err)\n\t}\n\n\tfmt.Println(\"Сервер успешно и безопасно остановлен без потери клиентских запросов.\")\n}"
      },
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: zero-downtime-app\nspec:\n  replicas: 3\n  template:\n    spec:\n      # Время ожидания перед отправкой SIGKILL должно превышать суммарную задержку в Go:\n      # 6с (sleep) + 20с (Shutdown timeout) = 26с < 40с\n      terminationGracePeriodSeconds: 40\n      containers:\n        - name: app\n          image: ghcr.io/company/zero-downtime:v1.0.0\n          ports:\n            - containerPort: 8080"
      }
    ],
    "under_the_hood": "Событие `PodDeleted` от API Server должно дойти по сети до демона `kube-proxy` на каждой из 500 нод кластера. \n\nПока эти демоны пересчитывают цепочки iptables, Ingress-контроллер продолжает направлять часть запросов на старый IP. Пауза в 5-6 секунд (или использование `lifecycle.preStop.exec.command: [\"sleep\", \"5\"]`) дает сетевому слою K8s время гарантированно вывести под из балансировки, прежде чем Go закроет TCP-слушатель.",
    "pitfalls": "1. Использование небуферизированного канала `make(chan os.Signal)`: риск потери сигнала.\n2. `terminationGracePeriodSeconds` меньше, чем время работы `time.Sleep + server.Shutdown`: Kubelet принудительно убьет процесс сигналом `SIGKILL` до завершения обработки запросов.\n3. Вызов `server.Close()` вместо `server.Shutdown(ctx)`: `Close()` жестко обрывает все активные клиентские сокеты.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между задержкой в коде Go (`time.Sleep`) и хуком жизненного цикла `preStop` в манифесте Kubernetes?\n**Ответ:** \n- **`lifecycle.preStop` хук** выполняется Kubelet **до** отправки сигнала `SIGTERM` контейнеру (`preStop: exec: command: [\"sleep\", \"5\"]`). Это чисто декларативный инфраструктурный способ, не требующий изменений в кодовой базе Go.\n- Задержка в коде Go выполняется после получения `SIGTERM`. \nОба подхода решают одну проблему, однако в BigTech часто комбинируют их или предпочитают `preStop` хук, чтобы код микросервиса оставался чистым и не содержал платформо-зависимых задержек сна."
  },
  {
    "num": 44,
    "title": "Сетевая сегментация Zero-Trust: манифест NetworkPolicy для защиты базы данных",
    "task": "Настрой **NetworkPolicy**: `kind: NetworkPolicy`, `podSelector: matchLabels: app: database`, `policyTypes: [Ingress]`, `ingress: - from: - podSelector: matchLabels: app: backend`, `ports: - protocol: TCP, port: 5432`. Покажи zero-trust network segmentation.",
    "theory": "По умолчанию в Kubernetes действует открытая модель сети (Flat Network Model): любой под в любом namespace может свободно отправлять TCP-пакеты на любой другой под или сервис.\n\nПринципы безопасности Zero-Trust требуют строгой изоляции:\nРесурс **`NetworkPolicy` (`apiVersion: networking.k8s.io/v1`)**:\n- Действует как распределенный программный межсетевой экран (Firewall).\n- Селектор `podSelector.matchLabels: app: database` выбирает целевые поды.\n- Секция `ingress.from` разрешает входящие TCP-соединения на порт 5432 **строго от подов с меткой `app: backend`**.\n- Любые другие попытки подключения (например, от взломанного frontend-пода или чужого сервиса) блокируются ядром на корню.",
    "step_by_step": "1. Убедитесь, что в кластере установлен CNI-плагин с поддержкой NetworkPolicy (Cilium, Calico).\n2. Создайте манифест `db-network-policy.yaml`.\n3. Опишите правило: входящий трафик на порт 5432 разрешен только от `app: backend`.\n4. Примените манифест: `kubectl apply -f db-network-policy.yaml`.\n5. Протестируйте подключение: от frontend-пода соединение должно отваливаться по таймауту, а от backend — успешно проходить.",
    "code_blocks": [
      {
        "filename": "db-network-policy.yaml",
        "lang": "yaml",
        "code": "apiVersion: networking.k8s.io/v1\nkind: NetworkPolicy\nmetadata:\n  name: secure-database-access\n  namespace: production\nspec:\n  podSelector:\n    matchLabels:\n      app: database\n  policyTypes:\n    - Ingress\n  ingress:\n    - from:\n        - podSelector:\n            matchLabels:\n              app: backend\n      ports:\n        - protocol: TCP\n          port: 5432"
      },
      {
        "filename": "test-isolation.sh",
        "lang": "bash",
        "code": "# 1. Проверка от пода backend (доступ РАЗРЕШЕН):\nkubectl run test-backend --rm -it --labels=\"app=backend\" --image=postgres:16-alpine -- \\\n  pg_isready -h database -p 5432\n\n# 2. Проверка от постороннего пода frontend (доступ ЗАБЛОКИРОВАН):\nkubectl run test-frontend --rm -it --labels=\"app=frontend\" --image=postgres:16-alpine -- \\\n  pg_isready -h database -p 5432 --timeout=3"
      }
    ],
    "under_the_hood": "Сетевой агент CNI (например, eBPF-программы Cilium или iptables-цепочки Calico `felix`) перехватывает сетевые интерфейсы `veth`. \n\nКак только на поды вешается `NetworkPolicy`, CNI переводит целевой под в режим изоляции (Default Deny для входящего трафика) и генерирует правила BPF/iptables, пропускающие пакеты строго от исходных IP-адресов, помеченных меткой `app: backend`.",
    "pitfalls": "1. Использование стандартного CNI Flannel: Flannel не поддерживает NetworkPolicy, манифест применится без ошибок, но фильтрация работать **не будет**.\n2. Блокировка DNS-трафика: если включить `policyTypes: [Egress]` без разрешения исходящего UDP 53 порта к CoreDNS, поды не смогут резолвить доменные имена.\n3. Селектор по namespace: если backend и база находятся в разных пространствах имен, требуется добавить `namespaceSelector`.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в enterprise кластерах в каждом namespace создают правило «Default Deny All NetworkPolicy»?\n**Ответ:** По умолчанию сеть в K8s полностью открыта. Если злоумышленник через RCE (Remote Code Execution) взломает публичный микросервис на периметре, он сможет сканировать всю внутреннюю сеть кластера (Lateral Movement), подключаться к базам данных, Redis и внутренним Kafka брокерам. \nПолитика «Default Deny All» блокирует весь входящий и исходящий трафик в namespace по умолчанию. Разработчик обязан явно задекларировать белый список разрешенных сетевых связей для каждого сервиса."
  },
  {
    "num": 45,
    "title": "Управление правами доступа: ServiceAccount и принцип наименьших привилегий",
    "task": "Настройте **ServiceAccount** с минимальными правами для вашего приложения (principle of least privilege).",
    "theory": "Когда контейнеру внутри пода требуется взаимодействовать с Kubernetes API (например, микросервис читает список подов или контроллер создает ConfigMap), он аутентифицируется через **`ServiceAccount`**.\n\nПринцип наименьших привилегий (Principle of Least Privilege):\n- По умолчанию поды используют аккаунт `default`, к которому часто привязаны избыточные права.\n- Настоятельно рекомендуется создавать выделенный `ServiceAccount` для каждого приложения.\n- Если приложению **не нужен** доступ к K8s API, обязательно отключать автомонтирование токена:\n  `automountServiceAccountToken: false` — это защищает кластер от захвата при компрометации контейнера.",
    "step_by_step": "1. Создайте манифест `service-account.yaml`.\n2. Установите `automountServiceAccountToken: false` для изоляции.\n3. В `deployment.yaml` привяжите аккаунт через `serviceAccountName: backend-sa`.\n4. Примените манифесты.\n5. Проверьте отсутствие смонтированного JWT-токена в директории `/var/run/secrets/kubernetes.io/serviceaccount`.",
    "code_blocks": [
      {
        "filename": "service-account.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: ServiceAccount\nmetadata:\n  name: backend-sa\n  namespace: default\nautomountServiceAccountToken: false # Запрет монтирования API токена для безопасности"
      },
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: secure-service\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: secure-service\n  template:\n    metadata:\n      labels:\n        app: secure-service\n    spec:\n      serviceAccountName: backend-sa\n      containers:\n        - name: app\n          image: alpine:3.21\n          command: [\"/bin/sh\", \"-c\"]\n          args:\n            - |\n              if [ -f /var/run/secrets/kubernetes.io/serviceaccount/token ]; then\n                echo \"ВНИМАНИЕ: Токен K8s API смонтирован!\"\n              else\n                echo \"БЕЗОПАСНО: Доступ к токенам API кластера заблокирован.\"\n              fi\n              sleep 3600"
      }
    ],
    "under_the_hood": "По умолчанию Kubelet монтирует том типа `projected` в каждый контейнер по пути `/var/run/secrets/kubernetes.io/serviceaccount`. Том содержит три файла:\n1. `token`: подписанный JWT-токен сервисного аккаунта.\n2. `ca.crt`: публичный корневой сертификат K8s API Server.\n3. `namespace`: текущее пространство имен.\nДиректива `automountServiceAccountToken: false` предотвращает монтирование этого тома.",
    "pitfalls": "1. Использование аккаунта `default` со связанной ролью `cluster-admin`: взлом одного пода дает злоумышленнику полный контроль над всем датацентром.\n2. Хранение долгоживущих токенов ServiceAccount в секретах: начиная с K8s 1.24, секреты для ServiceAccount больше не генерируются автоматически (используется механизм TokenRequest API с коротким сроком жизни).\n3. Опечатка в `serviceAccountName`.",
    "bigtech_interview": "**Вопрос с собеседования:** Что может сделать злоумышленник, если он получил доступ к токену ServiceAccount внутри скомпрометированного пода?\n**Ответ:** Имея JWT-токен из `/var/run/secrets/kubernetes.io/serviceaccount/token`, злоумышленник может слать прямые запросы к K8s API Server (`https://kubernetes.default.svc`) от имени этого аккаунта через `curl`. \nЕсли аккаунт имеет права на создание подов или чтение секретов, злоумышленник может прочитать пароли других сервисов кластера, запустить криптомайнеры или совершить побег из контейнера (Container Escape) на хостовую ноду."
  },
  {
    "num": 46,
    "title": "Каверзный кейс: настройка GOMEMLIMIT для предотвращения OOMKilled в Go",
    "task": "**[Каверзный кейс — GOMEMLIMIT]**: Установи в контейнере лимит памяти `resources.limits.memory: 128Mi`. В коде Go сделай аллокацию большого слайса. Поймай `OOMKilled` (Out of Memory). Установи переменную окружения `GOMEMLIMIT=120MiB`, чтобы GC Go понимал лимиты cgroup и работал эффективнее.",
    "theory": "До версии Go 1.19 сборщик мусора (GC) не знал о лимитах памяти контейнера в cgroups. Он ориентировался только на переменную `GOGC` (запуск GC при удвоении размера кучи). \n\nЕсли контейнеру выделен лимит `limits.memory: 128Mi`, а сервис быстро аллоцировал 70 МБ, GC планировал следующий запуск при достижении $70 \\times 2 = 140$ МБ. Но при 128 МБ ядро Linux немедленно убивало контейнер по **OOMKilled** до того, как GC успевал освободить память!\n\nВ Go 1.19+ появилась переменная окружения **`GOMEMLIMIT`**:\n- Жесткий ориентир (Soft Memory Limit) для рантайма Go.\n- Рантайм Go начинает агрессивно запускать сборщик мусора, когда потребление приближается к `GOMEMLIMIT`, предотвращая падение по OOM.\n- **Золотое правило:** `GOMEMLIMIT` выставляется на **85–90% от `resources.limits.memory`** (например, `115MiB` при лимите `128Mi`). Оставшиеся 10–15% резервируются под стек, память рантайма и внекучевые аллокации CGO.",
    "step_by_step": "1. Задайте в манифесте `resources.limits.memory: 128Mi`.\n2. Добавьте переменную окружения `GOMEMLIMIT: \"115MiB\"`.\n3. Оставьте стандартный `GOGC: \"100\"`.\n4. Запустите стресс-тест памяти в Go.\n5. Убедитесь, что сервис не падает по OOM, а сборщик мусора своевременно счищает память.",
    "code_blocks": [
      {
        "filename": "gomemlimit-deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: memory-safe-app\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: mem-safe\n  template:\n    metadata:\n      labels:\n        app: mem-safe\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/mem-safe:v1.0.0\n          env:\n            # 90% от лимита контейнера 128Mi:\n            - name: GOMEMLIMIT\n              value: \"115MiB\"\n            - name: GOGC\n              value: \"100\"\n          resources:\n            requests:\n              memory: \"64Mi\"\n              cpu: \"100m\"\n            limits:\n              memory: \"128Mi\"\n              cpu: \"500m\" "
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"runtime\"\n\t\"runtime/debug\"\n)\n\nfunc main() {\n\tfmt.Printf(\"GOMEMLIMIT настроен: %d байт\\n\", debug.SetMemoryLimit(-1))\n\n\thttp.HandleFunc(\"/allocate\", func(w http.ResponseWriter, r *http.Request) {\n\t\t// Создание временного всплеска нагрузки на кучу\n\t\tdata := make([][]byte, 1000)\n\t\tfor i := range data {\n\t\t\tdata[i] = make([]byte, 100*1024) // 100 КБ каждый\n\t\t}\n\n\t\tvar m runtime.MemStats\n\t\truntime.ReadMemStats(&m)\n\t\tfmt.Fprintf(w, \"Alloc: %d КБ, NumGC: %d\\n\", m.Alloc/1024, m.NumGC)\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "Рантайм Go непрерывно отслеживает размер кучи и память, выделенную под системные структуры. \n\nКогда `HeapSys + StackSys` приближается к отметке `GOMEMLIMIT`, триггер GC смещается: сборщик мусора запускается непрерывно и пропорционально давлению памяти. Чтобы избежать бесконечного зацикливания (GC CPU Thrashing), рантайм Go ограничивает максимальное время работы GC не более 50% от суммарного процессорного времени.",
    "pitfalls": "1. Установка `GOMEMLIMIT` равным 100% от лимита cgroups (`128MiB` при лимите `128Mi`): контейнер все равно упадет по OOMKilled из-за памяти, потребляемой бинарником, кодом CGO, тредами ОС и сокетами ядра.\n2. Полное отключение GC (`GOGC=off`) без настройки `GOMEMLIMIT`.\n3. Использование суффикса `MB` вместо `MiB`: в Go синтаксис `MiB` означает $1024 \\times 1024$ байт, а `MB` — $1000 \\times 1000$ байт.",
    "bigtech_interview": "**Вопрос с собеседования:** Что такое «GC CPU Thrashing» при неправильной настройке `GOMEMLIMIT` и как Go 1.19+ защищает сервис от этой проблемы?\n**Ответ:** Если потребление памяти сервиса упирается в `GOMEMLIMIT`, сборщик мусора начинает запускаться непрерывно после каждой новой аллокации. В старых версиях это приводило к тому, что 100% времени процессора сжигалось на сборку мусора, а приложение полностью переставало отвечать на запросы (Livelock). \nВ Go 1.19+ встроен **GC CPU Limiter**: если затраты времени на GC превышают **50% от одного процессорного окна**, рантайм временно блокирует запуск GC и дает приложению работать, предпочитая риск получить OOMKilled полной остановке сервиса."
  },
  {
    "num": 47,
    "title": "Смертность одиночных подов и обеспечение надежности через Deployment",
    "task": "**Развертывание (Deployment)**: Поды смертны. Если под удалят, он не воскреснет. Удали под. Напиши `deployment.yaml`. Опиши `Deployment`, который управляет 3 репликами (копиями) твоего приложения. Примени его. `kubectl get pods` должен показать 3 работающих пода.",
    "theory": "Одиночный Pod в Kubernetes — временная сущность (Cattle, not Pets):\n- Если одиночный под падает из-за аппаратного сбоя ноды, Kubelet не восстанавливает его.\n- Если администратор случайно удалит под (`kubectl delete pod`), под исчезает навсегда.\n\nКонтроллер **`Deployment`** решает эту проблему:\n- Создает спецификацию через `ReplicaSet`.\n- Непрерывно сверяет количество живых экземпляров.\n- Автоматически создает новый под при любых авариях или удалениях.",
    "step_by_step": "1. Создайте одиночный под и удалите его: убедитесь, что он не восстановился.\n2. Создайте манифест `deployment.yaml`.\n3. Примените Deployment.\n4. Удалите под деплоймента командой `kubectl delete pod`.\n5. Убедитесь, что Deployment немедленно поднял новый под с новым именем.",
    "code_blocks": [
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: indestructible-service\nspec:\n  replicas: 2\n  selector:\n    matchLabels:\n      app: indestructible\n  template:\n    metadata:\n      labels:\n        app: indestructible\n    spec:\n      containers:\n        - name: app\n          image: alpine:3.21\n          command: [\"sleep\", \"3600\"]"
      },
      {
        "filename": "demo-kill.sh",
        "lang": "bash",
        "code": "# Просмотр подов\nkubectl get pods -l app=indestructible\n\n# Удаление пода\nPOD_NAME=$(kubectl get pods -l app=indestructible -o jsonpath='{.items[0].metadata.name}')\necho \"Уничтожаем под: $POD_NAME\"\nkubectl delete pod $POD_NAME\n\n# Проверка: контроллер моментально запустил замену!\nkubectl get pods -l app=indestructible"
      }
    ],
    "under_the_hood": "`ReplicaSetController` слушает очередь событий API Server. \n\nУдаление пода генерирует событие `DELETE`. Функция контроллера `manageReplicas()` сопоставляет активные поды с числом `spec.replicas`. Заметив недостачу, контроллер немедленно формирует транзакцию создания нового пода.",
    "pitfalls": "1. Деплой подов напрямую манифестом `kind: Pod` в продуктовых средах.\n2. Изменение селекторов работающего Deployment.\n3. Отсутствие мониторинга доступности реплик.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в Kubernetes архитектуре принято называть поды «Cattle, not Pets» (Скот, а не домашние питомцы)?\n**Ответ:** Исторически серверы администрировались как домашние питомцы («Pets»): им давали уникальные имена, лечили при сбоях и берегли каждый хост. \nВ облачной парадигме поды являются расходным материалом («Cattle»): они взаимозаменяемы, безлики, имеют случайные хэш-имена и могут уничтожаться или пересоздаваться сотнями в минуту без какого-либо урона для системы."
  },
  {
    "num": 48,
    "title": "Управление доступом на основе ролей (RBAC): ServiceAccount, Role и RoleBinding",
    "task": "Настрой **ServiceAccount + RBAC**: `kind: ServiceAccount`, `kind: Role` (permissions in namespace), `kind: RoleBinding` (bind SA to Role). Покажи principle of least privilege for pods.",
    "theory": "Модель **RBAC (Role-Based Access Control)** управляет правами доступа процессов и пользователей к API кластера Kubernetes:\n1. **`ServiceAccount`:** Учетная запись, от имени которой действует Pod.\n2. **`Role`:** Набор разрешений в рамках конкретного namespace (правила: `apiGroups`, `resources`, `verbs`).\n3. **`RoleBinding`:** Связывает ServiceAccount с Role, наделяя его правами.\n\nПример: микросервису требуется считывать список подов в своем namespace, но запрещено удалять поды или читать секреты.",
    "step_by_step": "1. Создайте `ServiceAccount` с именем `pod-reader-sa`.\n2. Создайте манифест `Role`, разрешающий действия `get`, `list`, `watch` для ресурса `pods`.\n3. Создайте `RoleBinding`, связывающий аккаунт с ролью.\n4. Привяжите `serviceAccountName: pod-reader-sa` в `deployment.yaml`.\n5. Протестируйте права через команду `kubectl auth can-i`.",
    "code_blocks": [
      {
        "filename": "rbac.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: ServiceAccount\nmetadata:\n  name: pod-reader-sa\n  namespace: default\n---\napiVersion: rbac.authorization.k8s.io/v1\nkind: Role\nmetadata:\n  name: pod-reader-role\n  namespace: default\nrules:\n  - apiGroups: [\"\"] # Core API Group\n    resources: [\"pods\"]\n    verbs: [\"get\", \"list\", \"watch\"]\n---\napiVersion: rbac.authorization.k8s.io/v1\nkind: RoleBinding\nmetadata:\n  name: read-pods-binding\n  namespace: default\nsubjects:\n  - kind: ServiceAccount\n    name: pod-reader-sa\n    namespace: default\nroleRef:\n  kind: Role\n  name: pod-reader-role\n  apiGroup: rbac.authorization.k8s.io"
      },
      {
        "filename": "check-rbac.sh",
        "lang": "bash",
        "code": "# Проверка прав: может ли ServiceAccount читать поды? (Ответ: yes)\nkubectl auth can-i list pods --as=system:serviceaccount:default:pod-reader-sa\n\n# Проверка прав: может ли ServiceAccount удалять поды? (Ответ: no)\nkubectl auth can-i delete pods --as=system:serviceaccount:default:pod-reader-sa\n\n# Проверка прав: может ли ServiceAccount читать секреты? (Ответ: no)\nkubectl auth can-i get secrets --as=system:serviceaccount:default:pod-reader-sa"
      }
    ],
    "under_the_hood": "Когда приложение обращается к API-серверу (`GET /api/v1/namespaces/default/pods`), модуль авторизации RBAC перехватывает запрос. \n\nОн парсит субъект из токена JWT, находит все объекты `RoleBinding` в данном namespace, сопоставляет запрошенный URI (`resource: pods`, `verb: list`) с правилами `rules[]`. Если совпадение найдено, запрос пропускается, иначе возвращается статус `403 Forbidden`.",
    "pitfalls": "1. Использование `ClusterRole` и `ClusterRoleBinding` вместо `Role` и `RoleBinding`: выдача прав на весь кластер вместо одного namespace.\n2. Использование подстановочного знака `verbs: [\"*\"]` и `resources: [\"*\"]`: нарушение принципа наименьших привилегий.\n3. Отсутствие прав на `watch` при использовании client-go Informer cache.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между `RoleBinding` и `ClusterRoleBinding`?\n**Ответ:** \n- **`RoleBinding`** действует строго в пределах **одного конкретного namespace**. Даже если связать его с глобальной `ClusterRole`, права будут ограничены только ресурсами данного пространства имен.\n- **`ClusterRoleBinding`** действует **глобально на весь кластер**, давая права во всех существующих и будущих пространствах имен (например, права на просмотр нод `nodes` или чтение подов во всех namespace одновременно). Использование `ClusterRoleBinding` в приложениях требует строгого согласования с отделом ИБ."
  },
  {
    "num": 49,
    "title": "Headless Service: прямое обнаружение подов по DNS и интеграция со StatefulSet",
    "task": "Настрой **Headless Service**: `clusterIP: None`. DNS: `postgres-0.postgres.default.svc.cluster.local`. Используй для StatefulSet peer discovery. Покажи, как pods находят друг друга.",
    "theory": "Обычный сервис направляет трафик на виртуальный ClusterIP, выполняя балансировку случайным образом.\n\n**`Headless Service` (`clusterIP: None`)**:\n- Не выделяет виртуальный IP-адрес и не использует kube-proxy.\n- CoreDNS возвращает список реальных IP-адресов **всех готовых подов** в виде нескольких A-записей.\n- При связке со `StatefulSet` CoreDNS генерирует индивидуальные DNS-записи для каждого пода:\n  `<pod-name>.<service-name>.<namespace>.svc.cluster.local` (например, `postgres-0.postgres.default.svc.cluster.local`).\n- Это критично для баз данных с репликацией (Master-Slave), где клиенты должны подключаться напрямую к конкретной ноде.",
    "step_by_step": "1. Создайте `headless-service.yaml` с `clusterIP: None`.\n2. Задайте селектор `app: db`.\n3. Примените манифест.\n4. Выполните DNS-запрос через `nslookup` из временного контейнера.\n5. Убедитесь, что DNS возвращает прямые IP всех подов.",
    "code_blocks": [
      {
        "filename": "headless-service.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Service\nmetadata:\n  name: db-headless\nspec:\n  clusterIP: None # Ключевой параметр Headless Service\n  selector:\n    app: db\n  ports:\n    - port: 5432\n      name: postgresql"
      },
      {
        "filename": "dns-test.sh",
        "lang": "bash",
        "code": "# Проверка DNS резолвинга Headless Service:\nkubectl run dnsutils --rm -it --image=tianon/speedtest -- nslookup db-headless\n\n# Пример ответа: возвращаются прямые IP-адреса всех подов:\n# Name:   db-headless.default.svc.cluster.local\n# Address: 10.244.1.15\n# Address: 10.244.2.28\n# Address: 10.244.3.42"
      }
    ],
    "under_the_hood": "Плагин `kubernetes` в CoreDNS подключен к API Server через Watch. \n\nПри запросе обычного сервиса CoreDNS возвращает единственную запись ClusterIP. При запросе Headless Service CoreDNS считывает связанный объект `Endpoints`/`EndpointSlice` и возвращает массив записей `A` со всеми IP адресами готовых подов.",
    "pitfalls": "1. Опечатка в `clusterIP: None` (например, пустая строка): K8s автоматически выделит обычный ClusterIP.\n2. Кэширование DNS на стороне Go-клиента: если стандартный DNS-клиент закэширует IP, он продолжит слать запросы на упавший под.\n3. Попытка настроить Headless Service без селектора.",
    "bigtech_interview": "**Вопрос с собеседования:** Как Go gRPC клиент использует Headless Service для клиентской балансировки (Client-Side Load Balancing)?\n**Ответ:** Go gRPC клиент использует встроенный DNS-резолвер:\n`conn, err := grpc.Dial(\"dns:///my-headless-service:50051\", grpc.WithDefaultServiceConfig(`{\"loadBalancingConfig\": [{\"round_robin\":{}}]}`))`\nРезолвер периодически опрашивает Headless Service, получает список IP всех подов и распределяет каждый отдельный RPC-вызов по кругу (Round-Robin) между TCP-соединениями к разным подам, решая проблему балансировки долгоживущих HTTP/2 соединений без внешних прокси."
  },
  {
    "num": 50,
    "title": "Настройка Ingress с NGINX Ingress Controller для доменного роутинга",
    "task": "Создайте **Ingress** с Nginx Ingress Controller для роутинга HTTP-трафика на ваш сервис по доменному имени.",
    "theory": "Практическое закрепление создания L7 маршрутизации:\n- Внешний трафик поступает на единый IP балансировщика Ingress Controller.\n- На основе HTTP заголовка `Host: api.company.com` и пути `/` запрос перенаправляется на нужный внутренний `Service`.\n- Обеспечивается централизованное управление SSL/TLS сертификатами через K8s Secret типа `kubernetes.io/tls`.",
    "step_by_step": "1. Создайте `ingress.yaml` с правилом для домена `api.company.com`.\n2. Укажите `ingressClassName: nginx`.\n3. Свяжите правило с сервисом `api-service` на порту 80.\n4. Примените манифест: `kubectl apply -f ingress.yaml`.\n5. Протестируйте запрос через `curl -H \"Host: api.company.com\"`.",
    "code_blocks": [
      {
        "filename": "ingress.yaml",
        "lang": "yaml",
        "code": "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: domain-ingress\n  annotations:\n    nginx.ingress.kubernetes.io/ssl-redirect: \"false\"\nspec:\n  ingressClassName: nginx\n  rules:\n    - host: api.company.com\n      http:\n        paths:\n          - path: /\n            pathType: Prefix\n            backend:\n              service:\n                name: api-service\n                port:\n                  number: 80"
      },
      {
        "filename": "test-host.sh",
        "lang": "bash",
        "code": "# Проверка правила маршрутизации по домену\ncurl -v -H \"Host: api.company.com\" http://localhost/"
      }
    ],
    "under_the_hood": "Контроллер NGINX парсит поле `spec.rules[].host` и генерирует блок `server { server_name api.company.com; ... }` в конфигурации Nginx. \n\nДиректива `pathType: Prefix` сопоставляет префикс URL с локацией `location /`. Входящие запросы без соответствующего заголовка Host попадают в default backend.",
    "pitfalls": "1. Неверный `pathType`: использование `Exact` вместо `Prefix` приведет к тому, что запросы к `/api/users` вернут 404.\n2. Конфликт правил в разных Ingress-манифестах с одинаковым хостом.\n3. Отсутствие аннотации для SSL редиректа при наличии TLS.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между `pathType: Prefix` и `pathType: Exact` в спецификации Kubernetes Ingress?\n**Ответ:** \n- **`Exact`:** Строгое точное совпадение URL. Правило с `path: /orders` совпадет только с запросом `/orders`. Запрос `/orders/123` не совпадет и вернет ошибку 404.\n- **`Prefix`:** Совпадение по сегментам пути, разделенным слэшами. Правило с `path: /orders` совпадет с `/orders`, `/orders/` и `/orders/123/items`, что является стандартом для API-маршрутизации."
  },
  {
    "num": 51,
    "title": "Тонкая настройка Ingress правил: спецификация хостов, путей и бэкендов",
    "task": "Настрой **Ingress**: `kind: Ingress`, `spec: rules: - host: api.example.com, http: paths: - path: /, pathType: Prefix, backend: service: name: myapp, port: number: 80`. TLS: `spec: tls: - hosts: [api.example.com], secretName: api-tls`. Покажи external access.",
    "theory": "Манифест `Ingress` позволяет объединять несколько доменов и префиксов путей в едином файле конфигурации:\n- Маршрутизация на основе путей (Path-Based Routing):\n  - `api.example.com/v1/auth` -> `auth-service`\n  - `api.example.com/v1/billing` -> `billing-service`\n- Маршрутизация на основе поддоменов:\n  - `admin.example.com` -> `backoffice-service`",
    "step_by_step": "1. Опишите манифест `multi-ingress.yaml`.\n2. Задайте два правила в секции `rules` для хостов `api.example.com` и `admin.example.com`.\n3. Настройте перенаправление на соответствующие сервисы.\n4. Примените манифест.\n5. Протестируйте оба маршрута через curl.",
    "code_blocks": [
      {
        "filename": "multi-ingress.yaml",
        "lang": "yaml",
        "code": "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: core-ingress\nspec:\n  ingressClassName: nginx\n  rules:\n    - host: api.example.com\n      http:\n        paths:\n          - path: /v1/auth\n            pathType: Prefix\n            backend:\n              service:\n                name: auth-service\n                port:\n                  number: 80\n          - path: /v1/billing\n            pathType: Prefix\n            backend:\n              service:\n                name: billing-service\n                port:\n                  number: 80\n    - host: admin.example.com\n      http:\n        paths:\n          - path: /\n            pathType: Prefix\n            backend:\n              service:\n                name: backoffice-service\n                port:\n                  number: 80"
      },
      {
        "filename": "verify.sh",
        "lang": "bash",
        "code": "# Проверка маршрута 1\ncurl -H \"Host: api.example.com\" http://localhost/v1/auth/login\n\n# Проверка маршрута 2\ncurl -H \"Host: admin.example.com\" http://localhost/"
      }
    ],
    "under_the_hood": "NGINX Ingress сортирует пути по длине префикса (longest prefix match). \n\nЗапрос к `/v1/auth/token` сопоставляется с локацией `/v1/auth`, а не с более общим `/`. Заголовок `Host` проверяется в первую очередь через виртуальные хосты Nginx.",
    "pitfalls": "1. Дублирование путей в разных сервисах.\n2. Проблема trailing slash: запросы к `/v1/auth` и `/v1/auth/` могут интерпретироваться по-разному при отсутствии rewrite-аннотаций.\n3. Отсутствие healthcheck на бэкенд-сервисах.",
    "bigtech_interview": "**Вопрос с собеседования:** Как NGINX Ingress Controller избегает сброса активных соединений (Zero-Downtime Reload) при частом изменении конфигураций Ingress в кластере?\n**Ответ:** Традиционная команда `nginx -s reload` запускает новый мастер-процесс Nginx и постепенно закрывает старые воркеры. При тысячах обновлений в секунду в динамическом кластере это приводило к утечкам памяти и сбросу соединений. \nСовременный NGINX Ingress Controller использует **Lua-модуль (OpenResty) и динамическую память shm (Shared Memory)**: список IP адресов подов (upstreams) хранится в разделяемой памяти и обновляется на лету через внутренний REST API без выполнения перезагрузки Nginx."
  },
  {
    "num": 52,
    "title": "Практика самовосстановления (Self-Healing) подов в Deployment",
    "task": "**Самовосстановление (Self-healing)**: Намеренно удали один из подов Deployment'а (`kubectl delete pod <имя>`). Быстро сделай `kubectl get pods`. Увидь, как Kubernetes мгновенно создает новый под на замену убитому, чтобы поддержать требуемое число реплик = 3.",
    "theory": "Демонстрация фундаментального принципа надежности Kubernetes:\n- Поды смертны, но Deployment вечен.\n- При удалении пода через `kubectl delete pod` контроллер `ReplicaSet` мгновенно замечает разницу между желаемым числом реплик и текущим.\n- Создается новый под с новым уникальным именем и IP-адресом.\n- Балансировщик Service обновляет Endpoints без простоя трафика.",
    "step_by_step": "1. Запустите Deployment с 3 репликами.\n2. Запустите непрерывный пинг сервиса в фоновом режиме: `while true; do curl http://service; sleep 0.2; done`.\n3. В другом окне принудительно удалите один из подов: `kubectl delete pod <name>`.\n4. Наблюдайте, как непрерывный поток запросов не прерывается ни на секунду.",
    "code_blocks": [
      {
        "filename": "self-heal-test.sh",
        "lang": "bash",
        "code": "# 1. Просмотр подов\nkubectl get pods -l app=resilient\n\n# 2. Удаление одного пода\nPOD_ID=$(kubectl get pods -l app=resilient -o jsonpath='{.items[0].metadata.name}')\necho \"Удаление пода $POD_ID...\"\nkubectl delete pod $POD_ID\n\n# 3. Моментальная проверка: K8s уже создал новый под!\nkubectl get pods -l app=resilient"
      }
    ],
    "under_the_hood": "Цикл сверки (Reconciliation Loop) выполняется контроллером каждые несколько миллисекунд по событиям etcd Watch. \n\nВремя восстановления пода в среднем составляет менее 1 секунды при условии, что OCI-образ уже закэширован на ноде.",
    "pitfalls": "1. Зависание пода в `Terminating`: если приложение игнорирует `SIGTERM`, удаление продлится полные 30 секунд.\n2. Недостаток свободных нод при падении физического сервера.\n3. Отсутствие репликации (`replicas: 1`): удаление единственного пода гарантирует простой.",
    "bigtech_interview": "**Вопрос с собеседования:** Что происходит с точки зрения etcd и Kube-scheduler при удалении пода командой `kubectl delete pod`?\n**Ответ:** \n1. `kubectl` отправляет `DELETE /api/v1/namespaces/default/pods/<name>`.\n2. API Server не удаляет объект из etcd моментально, а выставляет поле `metadata.deletionTimestamp` (статус `Terminating`).\n3. Kubelet видит временную метку и шлет процессу `SIGTERM`.\n4. Одновременно ReplicaSetController видит, что активных подов стало $N-1$, и отправляет `POST` на создание нового пода.\n5. Scheduler назначает новый под на свободную ноду, и он поднимается параллельно с угасанием старого пода."
  },
  {
    "num": 53,
    "title": "Инициализационные контейнеры (Init Containers): ожидание готовности PostgreSQL",
    "task": "**[Init Containers]**: Напиши Pod с `initContainer`, который ждет, пока PostgreSQL поднимется (использует `pg_isready` или `nc -z`). Только после успеха должен стартовать основной контейнер с твоим приложением.",
    "theory": "При старте пода основной сервис часто зависит от внешних ресурсов (база данных должна подняться и применить миграции). Если запустить сервис раньше БД, он упадет с ошибкой подключения.\n\n**`Init Containers` (`spec.initContainers`)**:\n- Запускаются **до старта основных контейнеров приложения**.\n- Выполняются строго последовательно до успешного завершения с кодом 0 (`Completed`).\n- Если init-контейнер падает, Kubelet перезапускает его в соответствии с `restartPolicy`.\n- Идеальны для проверки готовности зависимостей (например, опрос утилитой `pg_isready` или `nc -z`).",
    "step_by_step": "1. В манифесте `deployment.yaml` добавьте секцию `spec.template.spec.initContainers`.\n2. Настройте легковесный образ `postgres:16-alpine`.\n3. Добавьте команду цикла ожидания: `until pg_isready -h db-service -p 5432; do sleep 2; done`.\n4. Разверните сервис.\n5. Убедитесь по статусу пода `Init:0/1`, что K8s ожидает базу данных перед запуском Go-контейнера.",
    "code_blocks": [
      {
        "filename": "init-deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: app-with-init\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: app-with-init\n  template:\n    metadata:\n      labels:\n        app: app-with-init\n    spec:\n      initContainers:\n        - name: wait-for-postgres\n          image: postgres:16-alpine\n          command:\n            - /bin/sh\n            - -c\n            - |\n              echo \"Ожидание готовности PostgreSQL...\"\n              until pg_isready -h postgres-service -p 5432 -U postgres; do\n                echo \"База данных недоступна, повтор через 2 секунды...\"\n                sleep 2\n              done\n              echo \"PostgreSQL готов к приему соединений!\"\n      containers:\n        - name: backend\n          image: ghcr.io/company/backend:v1.0.0\n          ports:\n            - containerPort: 8080"
      },
      {
        "filename": "check-init.sh",
        "lang": "bash",
        "code": "# Просмотр статуса пода на этапе инициализации:\nkubectl get pods -l app=app-with-init\n# Вывод:\n# NAME                             READY   STATUS     RESTARTS   AGE\n# app-with-init-658f96489-7k8m2   0/1     Init:0/1   0          5s\n\n# Просмотр логов init-контейнера:\nkubectl logs pod/app-with-init-658f96489-7k8m2 -c wait-for-postgres"
      }
    ],
    "under_the_hood": "Kubelet последовательно итерирует массив `spec.initContainers`. Для каждого элемента создается контейнер. \n\nKubelet ждет события завершения процесса. Только когда статус контейнера переходит в `Terminated` с `ExitCode: 0`, Kubelet переходит к следующему init-контейнеру. Основные контейнеры приложения (`spec.containers`) вообще не создаются рантаймом до завершения всех initContainers.",
    "pitfalls": "1. Бесконечный цикл в initContainer без таймаута: если БД упала навсегда, под зависнет в `Init:0/1` навсегда.\n2. Использование тяжелых образов для init-контейнера: замедляет холодный старт пода.\n3. Пропуск флага `-c <name>` в `kubectl logs`: по умолчанию logs пытается прочитать логи основного контейнера, который еще даже не запущен.",
    "bigtech_interview": "**Вопрос с собеседования:** Могут ли `Init Containers` разделять данные с основными контейнерами приложения, и как это устроено?\n**Ответ:** Да! Все контейнеры одного пода (включая initContainers и обычные контейнеры) имеют доступ к общим томам пода (`spec.volumes`). \nКлассический паттерн: Init-контейнер монтирует том `emptyDir`, клонирует туда Git-репозиторий со статикой или скачивает конфигурационный файл с Vault/S3, а затем основной веб-сервер монтирует этот же том `emptyDir` в режиме read-only и раздает файлы."
  },
  {
    "num": 54,
    "title": "Установка и настройка Ingress Controller через Helm",
    "task": "Настрой **Ingress Controller** (nginx/traefik): Helm install. `LoadBalancer` service (cloud) or `NodePort` (bare metal). Cert-manager for automatic TLS (Let's Encrypt). Покажи complete ingress stack.",
    "theory": "Манифест `Ingress` не выполняет никакой маршрутизации сам по себе — это просто декларация конфигурации в базе данных etcd. Для ее воплощения в жизнь в кластере обязан быть запущен **Ingress Controller**.\n\nУстановка промышленного NGINX Ingress Controller через пакетный менеджер **Helm**:\n- Helm разворачивает набор подов Nginx, сервис балансировщика (`LoadBalancer` или `NodePort`), ServiceAccount, RBAC роли и Custom Resource Definitions.\n- Контроллер получает внешний IP адрес от облачного провайдера и начинает слушать порты 80 и 443.",
    "step_by_step": "1. Добавьте официальный Helm-репозиторий `ingress-nginx`.\n2. Обновите список чартов: `helm repo update`.\n3. Установите чарт командой `helm install ingress-nginx ingress-nginx/ingress-nginx`.\n4. Дождитесь выделения внешнего IP: `kubectl get svc ingress-nginx-controller -n default -w`.\n5. Проверьте обработку тестовых запросов.",
    "code_blocks": [
      {
        "filename": "install-ingress.sh",
        "lang": "bash",
        "code": "# 1. Добавление репозитория ingress-nginx\nhelm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx\nhelm repo update\n\n# 2. Установка контроллера в выделенный namespace\nhelm install ingress-nginx ingress-nginx/ingress-nginx \\\n  --namespace ingress-system \\\n  --create-namespace \\\n  --set controller.replicaCount=2 \\\n  --set controller.resources.requests.cpu=100m \\\n  --set controller.resources.requests.memory=128Mi\n\n# 3. Проверка статуса внешнего балансировщика\nkubectl get svc -n ingress-system"
      }
    ],
    "under_the_hood": "Helm создает Deployment контроллера, который запускает связку: бинарник на Go (`nginx-ingress-controller`) и оптимизированный веб-сервер Nginx. \n\nКонтроллер на Go подключается к K8s API по Informer/Watch API и отслеживает изменения `Ingress`, `Endpoints` и `Secret`. При изменениях он на лету обновляет таблицы апстримов в памяти Nginx.",
    "pitfalls": "1. Установка нескольких Ingress-контроллеров без указания `ingressClassName`: контроллеры будут конфликтовать и перезаписывать правила друг друга.\n2. Недостаток ресурсов CPU у Ingress-контроллера: при росте трафика весь входящий поток кластера начнет тормозить.\n3. Отсутствие репликации контроллера (`replicaCount: 1`): падение пода контроллера парализует доступ ко всем сервисам компании.",
    "bigtech_interview": "**Вопрос с собеседования:** Чем отличается Ingress-контроллер от обычного Kube-proxy?\n**Ответ:** \n- **`kube-proxy`** работает на уровне **L4 (TCP/UDP)** на каждой ноде кластера. Он не анализирует содержимое пакетов, не умеет читать HTTP-заголовки, cookies, пути URL и не умеет расшифровывать TLS.\n- **`Ingress Controller`** работает на прикладном уровне **L7 (HTTP/HTTPS)**. Он терминает SSL-сертификаты, парсит URL, выполняет rate-limiting, сжатие gzip/brotli, проверку авторизационных токенов и маршрутизирует трафик на основе доменных имен и путей."
  },
  {
    "num": 55,
    "title": "Использование аннотаций Ingress для Rate Limiting, CORS и перезаписи путей",
    "task": "Используйте **Ingress annotations** для rate limiting, CORS, rewrite target.",
    "theory": "Стандартный ресурс `Ingress` описывает только хосты и пути. Тонкая настройка веб-сервера осуществляется через аннотации (`metadata.annotations`):\n1. **Rewrite Target:** Перезапись URL (`nginx.ingress.kubernetes.io/rewrite-target: /$2`), позволяющая клиентам обращаться к `/api/v1/(.*)`, передавая на бэкенд чистый путь `/$2`.\n2. **Rate Limiting:** Защита от DDoS-атак и перегрузок:\n   - `limit-rps: \"10\"`: ограничение числа запросов в секунду с одного IP.\n   - `limit-connections: \"5\"`: лимит параллельных TCP-соединений.\n3. **CORS:** Автоматическая установка заголовков `Access-Control-Allow-Origin: \"*\"` для веб-клиентов.",
    "step_by_step": "1. Создайте манифест `ingress-annotations.yaml`.\n2. Добавьте аннотации rewrite-target, rate-limit и CORS.\n3. Примените манифест.\n4. Проверьте работу rate limiting серией быстрых запросов (ожидайте статус 429 или 503).\n5. Проверьте наличие CORS-заголовков в ответе curl.",
    "code_blocks": [
      {
        "filename": "ingress-annotations.yaml",
        "lang": "yaml",
        "code": "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: advanced-ingress\n  annotations:\n    nginx.ingress.kubernetes.io/use-regex: \"true\"\n    nginx.ingress.kubernetes.io/rewrite-target: /$2\n    # Ограничение частоты запросов (Rate Limiting)\n    nginx.ingress.kubernetes.io/limit-rps: \"5\"\n    nginx.ingress.kubernetes.io/limit-burst-multiplier: \"2\"\n    # Настройка CORS для Single Page Applications\n    nginx.ingress.kubernetes.io/enable-cors: \"true\"\n    nginx.ingress.kubernetes.io/cors-allow-methods: \"GET, POST, OPTIONS\"\n    nginx.ingress.kubernetes.io/cors-allow-origin: \"https://app.company.com\"\nspec:\n  ingressClassName: nginx\n  rules:\n    - host: api.company.com\n      http:\n        paths:\n          - path: /services/billing(/|$)(.*)\n            pathType: ImplementationSpecific\n            backend:\n              service:\n                name: billing-service\n                port:\n                  number: 80"
      },
      {
        "filename": "test-ratelimit.sh",
        "lang": "bash",
        "code": "# Быстрая отправка 20 запросов: после 10-го запроса Nginx вернет 503 Service Temporarily Unavailable\nfor i in $(seq 1 20); do\n  curl -s -o /dev/null -w \"%{http_code}\\n\" -H \"Host: api.company.com\" http://localhost/services/billing/status\ndone"
      }
    ],
    "under_the_hood": "Аннотации транслируются контроллером в нативные директивы конфигурации Nginx:\n- `limit_req_zone $binary_remote_addr zone=... rate=5r/s;`\n- `more_set_headers 'Access-Control-Allow-Origin: https://app.company.com';`\n- `rewrite ^/services/billing(/|$)(.*) /$2 break;`\nОбработка происходит в памяти воркера Nginx до того, как пакет уйдет на под приложения.",
    "pitfalls": "1. Ошибки в регулярных выражениях rewrite-target: срезка первого символа пути или поломка статических файлов.\n2. Rate Limiting за CloudFlare или внешним CDN: если не настроен заголовок `X-Forwarded-For` через `use-forwarded-headers: \"true\"`, Nginx будет считать все запросы пришедшими с одного IP адреса CDN и заблокирует всех пользователей сразу!\n3. Избыточный размер буфера заголовков клиента.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему при использовании Ingress Rate Limiting за обратным прокси (CDN / Cloudflare) критично настраивать директивы `real-ip`?\n**Ответ:** Если не настроить `real-ip`, Nginx видит в сокете IP-адрес пограничного сервера CDN (например, 104.16.x.x), а не реального клиента. \nПри лимите в 10 запросов в секунду первые 10 запросов от любого пользователя мира исчерпают лимит, и весь последующий глобальный трафик компании будет заблокирован с ошибкой 429/503. Настройка `enable-real-ip: \"true\"` заставляет Nginx извлекать настоящий IP клиента из заголовка `X-Forwarded-For`."
  },
  {
    "num": 56,
    "title": "Расширение API Kubernetes: создание Custom Resource Definition (CRD)",
    "task": "Настрой **Custom Resource Definition (CRD)**: `kind: CustomResourceDefinition`, `spec: group: example.com, versions: - name: v1, served: true, storage: true, schema: ...`. Напиши **Operator** на Go (`controller-runtime`): watches CR, reconciles state. Покажи Kubernetes-native automation.",
    "theory": "Kubernetes изначально спроектирован как расширяемая платформа. **Custom Resource Definition (CRD)** (`apiVersion: apiextensions.k8s.io/v1`) позволяет регистрировать собственные типы ресурсов в K8s API Server (например, `Database`, `BackupPolicy`, `KafkaTopic`):\n- Ресурс регистрируется глобально в кластере.\n- Определяется схема валидации полей через OpenAPI v3 JSON Schema.\n- После применения CRD разработчики могут управлять вашими кастомными объектами стандартной утилитой `kubectl` (`kubectl get database`, `kubectl apply -f my-db.yaml`), а логику их обработки реализует кастомный **Kubernetes Operator** на Go.",
    "step_by_step": "1. Создайте манифест `database-crd.yaml`.\n2. Задайте группу `group: example.com` и версию `v1alpha1`.\n3. Опишите OpenAPI v3 схему с полями `engine`, `version`, `replicas`.\n4. Примените CRD в кластер: `kubectl apply -f database-crd.yaml`.\n5. Создайте экземпляр кастомного ресурса `my-database.yaml` и проверьте через `kubectl get databases`.",
    "code_blocks": [
      {
        "filename": "database-crd.yaml",
        "lang": "yaml",
        "code": "apiVersion: apiextensions.k8s.io/v1\nkind: CustomResourceDefinition\nmetadata:\n  name: databases.example.com\nspec:\n  group: example.com\n  names:\n    kind: Database\n    plural: databases\n    singular: database\n    shortNames:\n      - db\n  scope: Namespaced\n  versions:\n    - name: v1alpha1\n      served: true\n      storage: true\n      schema:\n        openAPIV3Schema:\n          type: object\n          properties:\n            spec:\n              type: object\n              required: [\"engine\", \"replicas\"]\n              properties:\n                engine:\n                  type: string\n                  enum: [\"postgres\", \"mysql\", \"redis\"]\n                replicas:\n                  type: integer\n                  minimum: 1\n                  maximum: 5\n                storageSize:\n                  type: string\n                  default: \"10Gi\" "
      },
      {
        "filename": "my-database.yaml",
        "lang": "yaml",
        "code": "apiVersion: example.com/v1alpha1\nkind: Database\nmetadata:\n  name: orders-database\nspec:\n  engine: postgres\n  replicas: 3\n  storageSize: \"20Gi\" "
      },
      {
        "filename": "test-crd.sh",
        "lang": "bash",
        "code": "# 1. Регистрация нового типа ресурса в API K8s\nkubectl apply -f database-crd.yaml\n\n# 2. Создание экземпляра кастомного ресурса\nkubectl apply -f my-database.yaml\n\n# 3. Получение списка через kubectl (работает как с нативными подами!)\nkubectl get databases\nkubectl get db orders-database -o yaml"
      }
    ],
    "under_the_hood": "API Server K8s динамически регистрирует новые HTTP эндпоинты в своем REST-маршрутизаторе:\n`/apis/example.com/v1alpha1/namespaces/{namespace}/databases`\nПри создании объекта API Server валидирует входящий JSON по OpenAPI v3 схеме. Валидные данные сериализуются и сохраняются в базу etcd по ключу `/registry/example.com/databases/default/orders-database`.",
    "pitfalls": "1. Опечатка в имени `metadata.name`: имя CRD обязано строго подчиняться шаблону `<plural>.<group>` (например, `databases.example.com`), иначе K8s отклонит регистрацию.\n2. Изменение схемы в продакшне без написания конверсионных вебхуков (Conversion Webhooks).\n3. Поле `storage: true` обязано быть выставлено ровно для одной версии схемы.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между CRD (Custom Resource Definition) и Kubernetes Operator?\n**Ответ:** \n- **CRD** — это **только декларация схемы данных** (структура в etcd, как таблица в реляционной БД). Сам по себе CRD ничего не делает, это просто пассивная запись.\n- **Kubernetes Operator** — это **активный контроллер (бинарник на Go)**, который слушает события изменения CRD по Watch API и реализует бизнес-логику управления (создает StatefulSet, настраивает репликацию базы данных, делает бэкапы, выполняет Failover). CRD — это контракт, а Оператор — мозг системы."
  },
  {
    "num": 57,
    "title": "Горизонтальное автомасштабирование по утилизации CPU (HPA): практическая конфигурация",
    "task": "Создайте **Horizontal Pod Autoscaler (HPA)** на основе CPU utilization.",
    "theory": "Практическое закрепление создания HPA для производственных микросервисов:\n- Декларация масштабирования целевого деплоймента.\n- Привязка к порогу утилизации CPU (например, 75%).\n- Использование стабилизационных окон для защиты от качания подов.\n- Автоматическая балансировка ресурсов в часы пик и экономия денег компании ночью.",
    "step_by_step": "1. Создайте `hpa-cpu.yaml` с минимальным числом реплик 2 и максимальным 10.\n2. Привяжите `scaleTargetRef` к имени Deployment.\n3. Задайте `averageUtilization: 75`.\n4. Примените манифест.\n5. Проконтролируйте текущие значения утилизации через `kubectl get hpa`.",
    "code_blocks": [
      {
        "filename": "hpa-cpu.yaml",
        "lang": "yaml",
        "code": "apiVersion: autoscaling/v2\nkind: HorizontalPodAutoscaler\nmetadata:\n  name: payment-hpa\nspec:\n  scaleTargetRef:\n    apiVersion: apps/v1\n    kind: Deployment\n    name: payment-api\n  minReplicas: 2\n  maxReplicas: 10\n  metrics:\n    - type: Resource\n      resource:\n        name: cpu\n        target:\n          type: Utilization\n          averageUtilization: 75"
      },
      {
        "filename": "verify.sh",
        "lang": "bash",
        "code": "# Просмотр статуса HPA\nkubectl get hpa payment-hpa\n\n# Вывод детальной информации и событий автомасштабирования\nkubectl describe hpa payment-hpa"
      }
    ],
    "under_the_hood": "HPA Controller вычисляет процент утилизации:\n$$\\text{Utilization} = \\frac{\\sum \\text{Usage(Pods)}}{\\sum \\text{Requests(Pods)}} \\times 100\\%$$\nЕсли полученное значение отличается от целевого (75%) более чем на коэффициент допуска (tolerance 10%), контроллер выполняет масштабирование.",
    "pitfalls": "1. Завышение `minReplicas`: избыточные траты инфраструктурных ресурсов.\n2. `maxReplicas` превышает лимиты емкости кластера: поды зависнут в статусе `Pending`.\n3. Отсутствие мониторинга событий масштабирования в Grafana.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в production сервисах с HPA параметр `minReplicas` никогда не ставят равным 1?\n**Ответ:** Если `minReplicas: 1`, то в периоды затишья работает всего один под. Это полностью лишает систему высокой доступности (High Availability): \n1. При плановой эвакуации ноды (`kubectl drain`) сервис уходит в даунтайм.\n2. При падении ноды пользователи получают ошибки, пока под создается заново (от 30 секунд до 2 минут).\n3. При резком наплыве трафика один под мгновенно перегружается и падает до того, как HPA успеет отреагировать. \nМинимально допустимое число реплик в HighLoad — **не менее 2–3 подов**."
  },
  {
    "num": 58,
    "title": "Логирование по стандарту Twelve-Factor App в контейнерах и централизованный сбор",
    "task": "**Спецификация Twelve-Factor App по логированию**: Объясните, почему в контейнеризированных средах и Kubernetes приложение на Go должно писать логи исключительно в стандартные потоки вывода `os.Stdout` и `os.Stderr`, а не в файлы внутри контейнера. Настройте ваш структурированный логгер `slog` на вывод в `Stdout` и объясните, как внешние сборщики логов (например, FluentBit или Loki) собирают эти данные из K8s.",
    "theory": "Одиннадцатый фактор методологии **The Twelve-Factor App** гласит:\n> *«Приложение никогда не должно заботиться о маршрутизации или хранении своего потока вывода. Оно не должно пытаться писать в log-файлы или управлять ими. Каждый запущенный процесс пишет свой поток событий без буферизации в `stdout` и `stderr`».*\n\nВ Kubernetes:\n- Контейнеры пишут структурированный JSON в `stdout`.\n- Рантайм `containerd` упаковывает строки в стандартные файлы `/var/log/pods/`.\n- DaemonSet-агенты (Vector, Fluentbit, Grafana Alloy) читают файлы с диска хоста и отправляют в Elasticsearch, ClickHouse или Loki.\n- Это полностью снимает с Go-приложения накладные расходы на сетевую отправку логов и гарантирует сохранность записей при панике процесса.",
    "step_by_step": "1. Настройте структурированный логгер `slog` в Go.\n2. Выводите все логи строго в `os.Stdout`.\n3. Не создавайте локальных файлов логов на диске.\n4. Разверните сервис в K8s.\n5. Убедитесь, что логи собираются централизованно через `kubectl logs`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"log/slog\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\t// Инициализация стандартного JSON логгера Go 1.21+ в stdout\n\tlogger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{\n\t\tLevel: slog.LevelInfo,\n\t}))\n\tslog.SetDefault(logger)\n\n\tslog.Info(\"Сервис запущен в соответствии со стандартами 12-Factor App\",\n\t\t\"component\", \"http-server\",\n\t\t\"port\", 8080)\n\n\thttp.HandleFunc(\"/order\", func(w http.ResponseWriter, r *http.Request) {\n\t\torderID := r.URL.Query().Get(\"id\")\n\t\tslog.Info(\"Обработка заказа\",\n\t\t\t\"order_id\", orderID,\n\t\t\t\"remote_addr\", r.RemoteAddr,\n\t\t\t\"method\", r.Method)\n\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"Order processed\"))\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      },
      {
        "filename": "pod-logs.sh",
        "lang": "bash",
        "code": "# Просмотр структурированных JSON логов пода\nkubectl logs -l app=order-service --tail=10"
      }
    ],
    "under_the_hood": "Ядро Linux перехватывает файловый дескриптор 1 (`stdout`) процесса контейнера. Демон `containerd` через сокет `conmon` или FIFO пайпы мультиплексирует вывод, оборачивает каждую строку временной меткой в формате RFC3339Nano и флагом потока (`stdout`/`stderr`) и сбрасывает на диск ноды.",
    "pitfalls": "1. Запись логов в текстовые файлы внутри контейнера: при пересоздании пода диск стирается, и логи пропадают навсегда.\n2. Отправка логов по сети напрямую из приложения (HTTP-запросы к ElasticSearch): сетевая задержка или падение лог-сервера замедляет или полностью блокирует бизнес-логику Go-сервиса!\n3. Неструктурированный текст (`fmt.Println`): затрудняет поиск и парсинг в Grafana/Kibana.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему отправка логов по сети напрямую из кода Go в централизованное хранилище (Logstash/Loki) считается грубым антипаттерном в HighLoad микросервисах?\n**Ответ:** \n1. **Блокировки и деградация throughput:** Если лог-сервер кратковременно испытывает проблемы с диском или сетью, внутренний буфер логгера переполняется. Приложение либо начинает дропать логи, либо блокирует горутины, останавливая всю обработку клиентских запросов.\n2. **Потеря логов при аварии (Crash/Panic):** Если процесс Go падает по панике или OOM, буфер в памяти процесса стирается, и критический лог с причиной аварии не успевает уйти по сети.\n3. Запись в локальный `stdout` гарантирует запись в файловый кэш ОС за доли микросекунды, а фоновую доставку безопасно берет на себя DaemonSet-агент (Vector)."
  },
  {
    "num": 59,
    "title": "Локальное тестирование в Minikube/Kind и проброс портов через kubectl port-forward",
    "task": "Разверните приложение в локальном Kubernetes (minikube/kind) и проверьте доступ через `kubectl port-forward`.",
    "theory": "При локальной разработке микросервисов разработчики используют легковесные дистрибутивы Kubernetes:\n- **`Minikube`:** Разворачивает одноузловой кластер внутри виртуальной машины или Docker-контейнера.\n- **`Kind` (Kubernetes in Docker):** Запускает ноды кластера как контейнеры Docker (быстрый старт, идеально для CI).\n\nКоманда **`kubectl port-forward`**:\n- Создает двунаправленный защищенный TCP-туннель между локальным портом вашего ноутбука (`localhost:8080`) и внутренним портом пода или сервиса в кластере.\n- Не требует настройки Ingress, Service LoadBalancer или внешних DNS.\n- Идеальный инструмент для отладки приватных баз данных, Redis или gRPC сервисов.",
    "step_by_step": "1. Разверните сервис `db-service` в локальном кластере.\n2. Выполните команду проброса портов: `kubectl port-forward svc/db-service 5432:5432`.\n3. Подключитесь к базе данных с локального клиента Go по адресу `localhost:5432`.\n4. Убедитесь в успешной передаче трафика по туннелю.\n5. Завершите сессию туннелирования сочетанием клавиш `Ctrl+C`.",
    "code_blocks": [
      {
        "filename": "port-forward.sh",
        "lang": "bash",
        "code": "# Проброс порта локального ноутбука на Service в кластере\nkubectl port-forward svc/internal-api 8080:80\n\n# Пример вывода:\n# Forwarding from 127.0.0.1:8080 -> 8080\n# Forwarding from [::1]:8080 -> 8080\n# Handling connection for 8080\n\n# В другом терминале: локальный вызов внутреннего сервиса\ncurl http://localhost:8080/health"
      },
      {
        "filename": "client.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n\t\"net/http\"\n)\n\nfunc main() {\n\t// Подключение через порт, проброшенный утилитой port-forward:\n\tresp, err := http.Get(\"http://localhost:8080/health\")\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer resp.Body.Close()\n\n\tbody, _ := io.ReadAll(resp.Body)\n\tfmt.Printf(\"Успешный ответ из кластера через туннель: %s\\n\", string(body))\n}"
      }
    ],
    "under_the_hood": "`kubectl port-forward` открывает локальный слушающий TCP-сокет на машине разработчика. При входящем подключении утилита шлет POST запрос `Upgrade: SPDY / WebSocket` на K8s API Server. \n\nAPI Server связывается с демоном `kubelet` ноды через CRI стриминг. Kubelet открывает TCP-сокет к сетевому пространству имен целевого пода и мультиплексирует поток байтов.",
    "pitfalls": "1. Использование `port-forward` в продакшне: туннель не рассчитан на высокие нагрузки и падает при обрыве связи с API-сервером.\n2. Занятый локальный порт: ошибка `bind: address already in use`.\n3. Разрыв соединения при перезапуске пода: port-forward привязан к конкретному поду или его текущему IP.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему `kubectl port-forward` не масштабируется для production-трафика и чем он отличается от Ingress?\n**Ответ:** `port-forward` — это инструмент отладки. Трафик идет через управляющий уровень кластера (Control Plane): каждый пакет проходит через K8s API Server и Kubelet, создавая высокую нагрузку на мастер-ноды кластера и их etcd-связи. \nIngress и Service работают на уровне данных (Data Plane): трафик идет напрямую с балансировщика нагрузки на рабочие ноды через оптимизированные драйверы ядра Linux, обеспечивая миллионы запросов в секунду."
  },
  {
    "num": 60,
    "title": "Автомасштабирование по кастомным метрикам: масштабирование по длине очереди Kafka через KEDA",
    "task": "Настройте HPA на основе **custom metrics** (например, длина Kafka очереди через Prometheus Adapter).",
    "theory": "Стандартный HPA по CPU и памяти не способен эффективно масштабировать консьюмеры очередей (Kafka, RabbitMQ, SQS):\n- Если в топик Kafka поступило 1 000 000 сообщений, консьюмеры могут работать с низким CPU (например, ожидая I/O базы данных). HPA не увеличит число реплик, и время отставания (Consumer Lag) вырастет до критических масштабов.\n\nРешение: **KEDA (Kubernetes Event-driven Autoscaling)**:\n- Расширяет K8s нативными Custom Resources (`ScaledObject`).\n- Умеет подключаться к брокерам (Kafka, RabbitMQ, Redis, Prometheus).\n- Измеряет длину очереди или лаг консьюмер-группы.\n- Масштабирует поды от 0 до N реплик (Scale-to-Zero) при появлении сообщений.",
    "step_by_step": "1. Установите KEDA в кластер через Helm.\n2. Создайте манифест `ScaledObject` для сервиса обработки заказов.\n3. Укажите триггер `type: kafka` с целевым лагом `lagThreshold: \"100\"`.\n4. Задайте диапазон реплик: `minReplicaCount: 1`, `maxReplicaCount: 20`.\n5. Отправьте тестовую пачку сообщений в Kafka и наблюдайте масштабирование подов консьюмеров.",
    "code_blocks": [
      {
        "filename": "scaled-object.yaml",
        "lang": "yaml",
        "code": "apiVersion: keda.sh/v1alpha1\nkind: ScaledObject\nmetadata:\n  name: kafka-consumer-scaler\n  namespace: default\nspec:\n  scaleTargetRef:\n    apiVersion: apps/v1\n    kind: Deployment\n    name: order-consumer\n  pollingInterval: 15\n  cooldownPeriod: 300\n  minReplicaCount: 1\n  maxReplicaCount: 15\n  triggers:\n    - type: kafka\n      metadata:\n        bootstrapServers: kafka-cluster.kafka.svc:9092\n        consumerGroup: order-processing-group\n        topic: incoming-orders\n        lagThreshold: \"50\" # Добавлять реплику на каждые 50 сообщений лага"
      },
      {
        "filename": "consumer.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n\t\"time\"\n)\n\nfunc main() {\n\tpodName, _ := os.Hostname()\n\tfmt.Printf(\"[%s] Консьюмер Kafka запущен. Чтение топика incoming-orders...\\n\", podName)\n\n\t// Имитация вычитки сообщений из очереди\n\tfor {\n\t\ttime.Sleep(100 * time.Millisecond)\n\t}\n}"
      },
      {
        "filename": "check-keda.sh",
        "lang": "bash",
        "code": "# Просмотр статуса ScaledObject\nkubectl get scaledobject kafka-consumer-scaler\n\n# KEDA автоматически создает стандартный HPA ресурс:\nkubectl get hpa keda-hpa-kafka-consumer-scaler"
      }
    ],
    "under_the_hood": "KEDA Operator периодически (каждые `pollingInterval` секунд) опрашивает брокер Kafka через протокол AdminClient API, запрашивая `OffsetFetch` и `ListConsumerGroupOffsets`. \n\nKEDA вычисляет суммарный лаг по всем партициям. Она передает вычисленную метрику во внутренний Custom Metrics API Server. Стандартный HPA контроллер Kubernetes считывает это значение и плавно меняет число реплик Deployment.",
    "pitfalls": "1. Превышение количества реплик над числом партиций Kafka: в Kafka одна партиция может читаться строго одним консьюмером внутри группы! Если в топике 8 партиций, запуск 15 реплик бессмысленен — 7 реплик будут простаивать в idle. `maxReplicaCount` не должен превышать число партиций!\n2. Слишком частый опрос (`pollingInterval: 1`): перегрузка контроллера Kafka Admin API.\n3. Отсутствие аутентификации (TriggerAuthentication) для защищенных SASL/SCRAM кластеров Kafka.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему при масштабировании консьюмеров Kafka через HPA/KEDA максимальное число реплик жестко ограничено количеством партиций топика?\n**Ответ:** Фундаментальная модель конкурентности Apache Kafka гарантирует строгий порядок сообщений внутри партиции. \nПравило Kafka: **каждая партиция внутри одной консьюмер-группы может обрабатываться строго одним потоком/процессом**. Если в топике создано 10 партиций, а KEDA отмасштабирует Deployment до 15 реплик, ровно 10 подов возьмут по одной партиции, а оставшиеся 5 подов не получат ни одной партиции и будут на 100% простаивать, напрасно сжигая память и CPU компании."
  }
]
