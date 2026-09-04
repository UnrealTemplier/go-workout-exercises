exercises = [
  {
    "num": 29,
    "title": "Сканирование OCI-образов на уязвимости с помощью Trivy в CI",
    "task": "Добавьте security scan образа через `trivy` (Aqua Security) или `snyk` в CI pipeline.",
    "theory": "Безопасность контейнеров не ограничивается зависимостями языка Go: уязвимости часто содержатся в системных библиотеках базового образа ОС (glibc, openssl, busybox). \n\n**Trivy (Aqua Security)** — один из самых популярных и быстрых сканеров безопасности с открытым исходным кодом:\n- Сканирует файловую систему образов, пакеты ОС (Alpine, Debian, RHEL) и зависимости приложений.\n- Поддерживает интеграцию в CI через `aquasecurity/trivy-action`.\n- Позволяет настраивать уровни критичности (`CRITICAL,HIGH`) и блокировать пайплайн (`exit-code: 1`) при наличии известных эксплойтов.\n- Поддерживает вывод результатов в формате SARIF (Static Analysis Results Interchange Format) для отображения предупреждений прямо на вкладке Security в GitHub.",
    "step_by_step": "1. Соберите локальный Docker-образ без публикации в реестр.\n2. Добавьте шаг запуска `aquasecurity/trivy-action@master`.\n3. Укажите имя целевого образа `image-ref`.\n4. Настройте `format: 'table'` и `exit-code: '1'` для критических уязвимостей (`severity: 'CRITICAL,HIGH'`).\n5. Добавьте второй запуск для генерации файла `trivy-results.sarif` и загрузки его через `github/codeql-action/upload-sarif`.",
    "code_blocks": [
      {
        "filename": ".github/workflows/trivy-scan.yml",
        "lang": "yaml",
        "code": "name: Container Security Scan\n\non:\n  push:\n    branches: [ main ]\n  pull_request:\n    branches: [ main ]\n\njobs:\n  trivy:\n    name: Build & Scan Container\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout repository\n        uses: actions/checkout@v4\n\n      - name: Build local Docker image\n        run: docker build -t local/service:${{ github.sha }} .\n\n      - name: Run Trivy Vulnerability Scanner\n        uses: aquasecurity/trivy-action@master\n        with:\n          image-ref: 'local/service:${{ github.sha }}'\n          format: 'table'\n          exit-code: '1'\n          ignore-unfixed: true\n          vuln-type: 'os,library'\n          severity: 'CRITICAL,HIGH'"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# syntax=docker/dockerfile:1\nFROM golang:1.24-alpine AS builder\nWORKDIR /app\nCOPY go.mod go.sum* ./\nRUN go mod download\nCOPY . .\nRUN CGO_ENABLED=0 go build -ldflags=\"-s -w\" -o /service .\n\n# Минимальный базовый образ с актуальными патчами безопасности\nFROM alpine:3.21\nRUN apk --no-cache upgrade && apk --no-cache add ca-certificates\nUSER 65534:65534\nCOPY --from=builder /service /service\nEXPOSE 8080\nENTRYPOINT [\"/service\"]"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/health\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"Healthy\"))\n\t})\n\tfmt.Println(\"Server running on :8080\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "Trivy распаковывает слои OCI-образа в локальный кэш и извлекает базы установленных пакетов (`/lib/apk/db/installed` в Alpine, `/var/lib/dpkg/status` в Debian). \n\nЗатем Trivy сопоставляет версии пакетов с локальной базой CVE, которая скачивается из GitHub Releases (`trivy-db`). Параметр `ignore-unfixed: true` отфильтровывает уязвимости, для которых авторы апстрим-дистрибутива еще не выпустили исправленный пакет, предотвращая блокировку CI по нерешаемым причинам.",
    "pitfalls": "1. Отсутствие `ignore-unfixed: true`: пайплайн падает из-за древней уязвимости low/medium в libc, для которой нет исправления, парализуя релизы команды.\n2. Сканирование тяжелых дистрибутивов вроде Ubuntu:latest: содержит сотни системных пакетов и уязвимостей. Переход на `scratch`, `distroless` или минимальный `alpine` сокращает число CVE до нуля.\n3. Отсутствие кэширования базы данных Trivy в CI, что увеличивает время выполнения джобы на 40-60 секунд при каждом прогоне.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему сканирование Dockerfile (`hadolint`) не заменяет сканирование скомпилированного OCI-образа (`trivy`), и в чем разница?\n**Ответ:** `hadolint` выполняет статический анализ текста Dockerfile (проверяет best practices: наличие non-root пользователя, отсутствие `apt-get upgrade`, пиннинг версий). Однако он ничего не знает о том, какие именно бинарники и пакеты скачались из сети во время сборки. Trivy инспектирует реальную бинарную файловую систему готового образа, сверяя хэши и версии установленных библиотек с базами NVD/CVE. В зрелом DevSecOps пайплайне применяются оба инструмента."
  },
  {
    "num": 30,
    "title": "Матричное тестирование на разных версиях Go и операционных системах",
    "task": "**[Матричное тестирование]**: Настрой матричный билд в CI: прогон тестов одновременно на Go 1.21, 1.22 и 1.23.",
    "theory": "При разработке библиотек, CLI-утилит и фундаментальных сервисов критически важно гарантировать работоспособность на разных версиях языка Go (поддержка N и N-1 по официальной политике Go) и различных операционных системах (Linux, macOS, Windows).\n\nМатричная стратегия (`strategy: matrix`):\n- Автоматически порождает декартово произведение параметров: 4 версии Go × 2 ОС = 8 параллельных джобов.\n- `fail-fast: false`: падение одной комбинации не прерывает тестирование остальных, позволяя инженеру увидеть полный спектр несовместимостей.\n- `max-parallel: 4`: позволяет ограничить число одновременно выполняемых джобов, чтобы не исчерпать лимиты раннеров организации.",
    "step_by_step": "1. Создайте `.github/workflows/matrix-test.yml`.\n2. В секции `strategy.matrix` укажите массив версий `go-version: ['1.21', '1.22', '1.23', '1.24']` и платформ `os: [ubuntu-latest, macos-latest]`.\n3. Задайте `fail-fast: false`.\n4. Настройте запуск тестов с флагом гонок: `go test -v -race ./...`.\n5. Проверьте запуск 8 параллельных задач в интерфейсе GitHub Actions.",
    "code_blocks": [
      {
        "filename": ".github/workflows/matrix-test.yml",
        "lang": "yaml",
        "code": "name: Cross-Platform Matrix Test\n\non:\n  push:\n    branches: [ main ]\n  pull_request:\n    branches: [ main ]\n\njobs:\n  test:\n    name: Go ${{ matrix.go-version }} on ${{ matrix.os }}\n    runs-on: ${{ matrix.os }}\n    strategy:\n      fail-fast: false\n      matrix:\n        go-version: ['1.21', '1.22', '1.23', '1.24']\n        os: [ubuntu-latest, macos-latest]\n\n    steps:\n      - name: Checkout Code\n        uses: actions/checkout@v4\n\n      - name: Setup Go\n        uses: actions/setup-go@v5\n        with:\n          go-version: ${{ matrix.go-version }}\n\n      - name: Verify Go Version\n        run: go version\n\n      - name: Run Tests with Race Detector\n        run: go test -v -race ./..."
      },
      {
        "filename": "sysinfo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n)\n\n// GetSystemInfo возвращает текущую ОС и архитектуру.\nfunc GetSystemInfo() string {\n\treturn fmt.Sprintf(\"OS: %s, Arch: %s, Go: %s\", runtime.GOOS, runtime.GOARCH, runtime.Version())\n}\n\nfunc main() {\n\tfmt.Println(GetSystemInfo())\n}"
      },
      {
        "filename": "sysinfo_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"runtime\"\n\t\"strings\"\n\t\"testing\"\n)\n\nfunc TestGetSystemInfo(t *testing.T) {\n\tinfo := GetSystemInfo()\n\tif !strings.Contains(info, runtime.GOOS) {\n\t\tt.Fatalf(\"Ожидалось упоминание ОС %s, получено: %s\", runtime.GOOS, info)\n\t}\n}"
      }
    ],
    "under_the_hood": "Раннер GitHub Actions преобразует матрицу в JSON-массив контекстов. Каждая джоба получает свой собственный изолированный runner environment.\n\nПри компиляции с флагом `-race` на macOS и Linux используется LLVM ThreadSanitizer. На архитектурах x86-64 и ARM64 флаг `-race` доступен из коробки, однако на 32-битных ОС или Windows ARM он может не поддерживаться, поэтому матрица позволяет изолировать ОС-специфичные тесты через `include` / `exclude` блоки.",
    "pitfalls": "1. Запуск флага `-race` на неподдерживаемых платформах (например, 32-битный x86): падение сборки с ошибкой `race detector not supported`.\n2. Забытый `fail-fast: false`: если одна джоба на Go 1.21 падает, все остальные 7 джобов моментально прерываются, не давая понять, работает ли код на Go 1.24.\n3. Исчерпание минут бесплатного GitHub Actions: матрица 5x5 на каждый коммит съедает квоту аккаунта за несколько дней.",
    "bigtech_interview": "**Вопрос с собеседования:** Что изменилось в семантике цикла `for ... := range` в Go 1.22, и почему матричное тестирование на версиях 1.21 и 1.22+ критично для открытых библиотек?\n**Ответ:** В Go 1.22 была исправлена историческая проблема разделения переменной цикла (Loop Variable Scoping): теперь на каждой итерации цикла создается новая переменная, а не переиспользуется один и тот же адрес памяти. \nЕсли библиотека запускает горутины внутри `for val := range items`, в Go 1.21 без передачи `val` аргументом возникнет data race / замыкание на последнее значение, а в Go 1.22+ тот же код выполнится корректно. Матричный тест моментально вскрывает этот скрытый баг на Go 1.21."
  },
  {
    "num": 31,
    "title": "Паттерн ArgoCD App of Apps: управление множеством окружений и сервисов",
    "task": "Настрой **ArgoCD App of Apps**: root `Application` manages other `Application`s. `apps/dev/`, `apps/staging/`, `apps/prod/`. Покажи managing multiple environments from single repo.",
    "theory": "Когда число микросервисов в компании переваливает за сотни, ручное добавление каждого манифеста `Application` в ArgoCD становится неуправляемым. \n\nПаттерн **«App of Apps» (Приложение приложений)** решает эту проблему декларативно:\n- Создается единый корневой манифест `Application` (Root App).\n- Root App указывает на Git-каталог, содержащий декларации дочерних `Application` CRD.\n- Каждый дочерний `Application` указывает на манифесты конкретного сервиса (например, `apps/dev/payment`, `apps/staging/auth`, `apps/prod/catalog`).\n- При добавлении нового микросервиса инженер просто коммитит один YAML в репозиторий, и ArgoCD автоматически подхватывает и разворачивает его.",
    "step_by_step": "1. Создайте структуру репозитория: `bootstrap/root.yaml`, `apps/dev/*.yaml`, `apps/prod/*.yaml`.\n2. Опишите `root.yaml`, направленный на каталог `apps/environments`.\n3. В дочерних манифестах укажите конкретные overlay-папки Kustomize или Helm-чарты.\n4. Примените корневой манифест в кластер: `kubectl apply -f bootstrap/root.yaml -n argocd`.\n5. Убедитесь в веб-интерфейсе ArgoCD, что появилось дерево зависимостей приложений.",
    "code_blocks": [
      {
        "filename": "bootstrap/root-app.yaml",
        "lang": "yaml",
        "code": "apiVersion: argoproj.io/v1alpha1\nkind: Application\nmetadata:\n  name: root-apps\n  namespace: argocd\n  finalizers:\n    - resources-finalizer.argocd.argoproj.io\nspec:\n  project: default\n  source:\n    repoURL: 'https://github.com/company/gitops-infra.git'\n    targetRevision: HEAD\n    path: apps/environments/production\n  destination:\n    server: 'https://kubernetes.default.svc'\n    namespace: argocd\n  syncPolicy:\n    automated:\n      prune: true\n      selfHeal: true"
      },
      {
        "filename": "apps/environments/production/billing-app.yaml",
        "lang": "yaml",
        "code": "apiVersion: argoproj.io/v1alpha1\nkind: Application\nmetadata:\n  name: prod-billing-service\n  namespace: argocd\nspec:\n  project: default\n  source:\n    repoURL: 'https://github.com/company/billing-service.git'\n    targetRevision: v2.1.0\n    path: deploy/k8s/overlays/production\n  destination:\n    server: 'https://kubernetes.default.svc'\n    namespace: billing\n  syncPolicy:\n    automated:\n      prune: true\n      selfHeal: true\n    syncOptions:\n      - CreateNamespace=true"
      }
    ],
    "under_the_hood": "ArgoCD рекурсивно обрабатывает ресурсы: при синхронизации Root App контроллер применяет дочерние манифесты `Application` в пространство имен `argocd`. \n\nКаждый дочерний CRD регистрируется в Etcd кластера, что запускает отдельные экземпляры `ApplicationController` для дочерних микросервисов. В интерфейсе ArgoCD формируется визуальное дерево топологии, где от корня отходят ветви сервисов, а от них — поды, сервисы, ингрессы и конфигмапы.",
    "pitfalls": "1. Циклические зависимости или бесконечная рекурсия, если Root App случайно указывает на папку, содержащую сам `root-app.yaml`.\n2. Случайное удаление корневого приложения с `finalizers`: приведет к каскадному удалению вообще всех микросервисов компании в кластере.\n3. Отсутствие разграничения проектов (`AppProject`): все дочерние сервисы получают права default-проекта, что нарушает принцип наименьших привилегий.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между паттерном «App of Apps» и генератором приложений «ApplicationSet» в ArgoCD?\n**Ответ:** \n- **App of Apps** базируется на стандартных статических манифестах `Application` в Git. Это простой и прозрачный подход, но требует ручного создания файла `app.yaml` на каждый новый микросервис.\n- **ApplicationSet** — это контроллер-генератор шаблонов. Он использует генераторы (Git directory, List, Matrix, Cluster generator) и автоматически штампует сотни `Application` по единому шаблону при появлении новой папки в Git или нового кластера в инвентаре, устраняя boilerplate-код."
  },
  {
    "num": 32,
    "title": "Генерация SBOM через Syft и подпись OCI-образов с помощью Cosign (Sigstore)",
    "task": "Настройте автоматическую генерацию SBOM (Software Bill of Materials) через `syft` и подписывайте образ через `cosign`.",
    "theory": "Защита цепочки поставок ПО (Software Supply Chain Security) — один из главных приоритетов ИБ. \n\nКлючевые компоненты безопасного пайплайна:\n1. **SBOM (Software Bill of Materials):** Полная инвентаризационная опись всех зависимостей, компонентов ОС, хэшей и лицензий, содержащихся в контейнере. Инструмент **Syft (Anchore)** генерирует SBOM в стандартных форматах SPDX или CycloneDX.\n2. **Cosign (проект Sigstore):** Инструмент для криптографической подписи контейнерных образов. В современном облачном подходе используется режим **Keyless Signing**: подпись генерируется с использованием OIDC-токена GitHub Actions и публичного сертификационного центра Fulcio, а хэш подписи фиксируется в прозрачном неизменяемом логе Rekor.",
    "step_by_step": "1. Установите Cosign и Syft в GitHub Actions пайплайне.\n2. Соберите и опубликуйте OCI-образ в реестр (например, GHCR).\n3. Сгенерируйте SBOM: `syft <image> -o spdx-json=sbom.spdx.json`.\n4. Прикрепите SBOM к образу: `cosign attest --predicate sbom.spdx.json --type spdx <image>`.\n5. Подпишите образ в keyless-режиме: `cosign sign --yes <image>`.\n6. Проверьте подпись: `cosign verify <image>`.",
    "code_blocks": [
      {
        "filename": ".github/workflows/cosign-sbom.yml",
        "lang": "yaml",
        "code": "name: Secure Build & Sign\n\non:\n  push:\n    tags: [ 'v*.*.*' ]\n\npermissions:\n  contents: read\n  packages: write\n  id-token: write # Необходимо для OIDC keyless signing в Cosign\n\njobs:\n  sign-image:\n    name: Build, SBOM and Sign with Cosign\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - name: Install Cosign\n        uses: sigstore/cosign-installer@v3.8.0\n\n      - name: Install Syft\n        uses: anchore/sbom-action/download-syft@v0.17.9\n\n      - name: Log in to GHCR\n        uses: docker/login-action@v3\n        with:\n          registry: ghcr.io\n          username: ${{ github.actor }}\n          password: ${{ secrets.GITHUB_TOKEN }}\n\n      - name: Build and Push Docker Image\n        id: docker_build\n        uses: docker/build-push-action@v5\n        with:\n          context: .\n          push: true\n          tags: ghcr.io/${{ github.repository }}:${{ github.ref_name }}\n\n      - name: Generate and Attest SBOM\n        run: |\n          syft ghcr.io/${{ github.repository }}:${{ github.ref_name }} -o spdx-json=sbom.spdx.json\n          cosign attest --yes --predicate sbom.spdx.json --type spdx ghcr.io/${{ github.repository }}:${{ github.ref_name }}\n\n      - name: Sign OCI Image (Keyless)\n        run: |\n          cosign sign --yes ghcr.io/${{ github.repository }}:${{ github.ref_name }}"
      },
      {
        "filename": "verify.sh",
        "lang": "bash",
        "code": "# Проверка валидности подписи в кластере перед запуском:\ncosign verify ghcr.io/company/repo:v1.0.0 \\\n  --certificate-identity \"https://github.com/company/repo/.github/workflows/cosign-sbom.yml@refs/tags/v1.0.0\" \\\n  --certificate-oidc-issuer \"https://token.actions.githubusercontent.com\" "
      }
    ],
    "under_the_hood": "При Keyless Signing Cosign запрашивает OIDC ID-токен у GitHub Actions API (благодаря `id-token: write`). Этот токен удостоверяет личность пайплайна (URL репозитория, ветку, коммит). \n\nCosign отправляет токен в CA Fulcio, который генерирует краткосрочный x509-сертификат (живет 10 минут). Образ подписывается сгенерированным сертификатом, а запись о транзакции отправляется в неизменяемый журнал Rekor (Append-only Merkle Tree). Подпись выгружается в OCI-реестр как отдельный артефакт с расширением `.sig`.",
    "pitfalls": "1. Забытое разрешение `id-token: write`: Cosign не сможет получить OIDC-токен и упадет с ошибкой аутентификации.\n2. Подпись образа по плавающему тегу (`:latest`) вместо SHA-дайджеста: образ может быть перезаписан, и подпись потеряет криптографическую силу.\n3. Отсутствие Admission Webhook (Kyverno / OPA Gatekeeper) в кластере Kubernetes: подписание образов теряет смысл, если кластер позволяет запускать неподписанные контейнеры.",
    "bigtech_interview": "**Вопрос с собеседования:** Что защищает цепочка Cosign + Kyverno/Gatekeeper в production Kubernetes кластере?\n**Ответ:** Она исключает класс атак Man-in-the-Middle и компрометацию реестра образов. Даже если злоумышленник взломает реестр контейнеров или учетную запись разработчика и подменит OCI-образ вредоносным кодом, Admission Controller кластера (Kyverno) откажет в запуске пода, так как подмененный образ не будет содержать криптографическую подпись и аттестацию от доверенного CI-пайплайна организации."
  },
  {
    "num": 33,
    "title": "Канареечные релизы с Argo Rollouts и анализ метрик Prometheus",
    "task": "Настрой **Argo Rollouts**: `Rollout` CRD (replacement for `Deployment`). Strategies: `Canary` (1% → 10% → 50% → 100%), `BlueGreen` (active/preview). Analysis: `prometheus` query for auto-promotion/rollback. Покажи progressive delivery.",
    "theory": "Традиционный RollingUpdate в Kubernetes заменяет старые реплики на новые постепенно, но не позволяет управлять процентом трафика и не анализирует ошибки приложения в реальном времени.\n\n**Argo Rollouts** — контроллер прогрессивной доставки (Progressive Delivery):\n- Заменяет стандартный ресурс `Deployment` на CRD **`Rollout`**.\n- Поддерживает стратегию **Canary**: плавное переключение пользовательского трафика (1% → 10% → 50% → 100%) на канареечную версию с помощью Service Mesh (Istio) или Ingress (ALB/Nginx).\n- **`AnalysisTemplate`**: автоматическая проверка метрик из Prometheus (например, `http_error_rate < 0.01` и `p99_latency < 200ms`) между шагами канарейки.\n- При скачке 5xx-ошибок контроллер автоматически прерывает деплой и мгновенно откатывает трафик на стабильную версию (Auto-Rollback).",
    "step_by_step": "1. Опишите манифест `rollout.yaml` с `kind: Rollout`.\n2. Настройте шаги `strategy.canary.steps`: шаг 5%, пауза 10m, шаг 20%, пауза 30m, шаг 50%, пауза 1h.\n3. Создайте `AnalysisTemplate`, запрашивающий у Prometheus процент ошибок HTTP за последние 5 минут.\n4. Свяжите `analysis` с шагами канареечного релиза.\n5. Примените манифест и симулируйте деплой новой версии сервиса.",
    "code_blocks": [
      {
        "filename": "rollout.yaml",
        "lang": "yaml",
        "code": "apiVersion: argoproj.io/v1alpha1\nkind: Rollout\nmetadata:\n  name: order-service\n  namespace: orders\nspec:\n  replicas: 5\n  strategy:\n    canary:\n      analysis:\n        templates:\n          - templateName: success-rate\n        args:\n          - name: service-name\n            value: order-service\n      steps:\n        - setWeight: 5\n        - pause: { duration: 5m }\n        - setWeight: 20\n        - pause: { duration: 15m }\n        - setWeight: 50\n        - pause: { duration: 30m }\n  selector:\n    matchLabels:\n      app: order-service\n  template:\n    metadata:\n      labels:\n        app: order-service\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/order-service:v2.0.0\n          ports:\n            - containerPort: 8080"
      },
      {
        "filename": "analysis-template.yaml",
        "lang": "yaml",
        "code": "apiVersion: argoproj.io/v1alpha1\nkind: AnalysisTemplate\nmetadata:\n  name: success-rate\n  namespace: orders\nspec:\n  args:\n    - name: service-name\n  metrics:\n    - name: success-rate\n      interval: 1m\n      successCondition: result[0] >= 0.99\n      failureLimit: 3\n      provider:\n        prometheus:\n          address: http://prometheus.monitoring.svc:9090\n          query: |\n            sum(rate(http_requests_total{service=\"{{args.service-name}}\",status!~\"5.*\"}[2m]))\n            /\n            sum(rate(http_requests_total{service=\"{{args.service-name}}\"}[2m]))"
      }
    ],
    "under_the_hood": "Argo Rollouts Controller создает две ReplicaSet: Stable (текущая стабильная версия) и Canary (новая версия). \n\nЕсли используется интеграция с Ingress-контроллером или Service Mesh (Envoy/Istio), Argo Rollouts динамически обновляет веса маршрутизации трафика (Traffic Routing). \n\nAnalysis Run запускается в фоновом режиме: контроллер шлет PromQL-запросы к Prometheus. Если значение `result[0]` падает ниже порога 0.99 более 3 раз подряд (`failureLimit: 3`), Rollout переходит в статус `Degraded`, вес канарейки немедленно сбрасывается в 0%, а трафик возвращается на 100% Stable RS.",
    "pitfalls": "1. Недостаточный объем трафика на первом шаге (1-5%): метрики Prometheus не успевают набрать статистическую значимость, и тест успешности может дать ложный результат.\n2. Несовместимые миграции БД при откате (Destructive DB Migrations): если новая версия сервиса удалила колонку в БД, то автоматический откат канарейки на старую версию сломает старую версию.\n3. Отсутствие таймаутов на шагах паузы без ручного подтверждения (`pause: {}` без `duration`).",
    "bigtech_interview": "**Вопрос с собеседования:** Чем Canary-деплой с анализом метрик превосходит Blue-Green деплой в HighLoad микросервисах?\n**Ответ:** Blue-Green требует двукратного перерасхода инфраструктурных ресурсов (100% idle-нод для Green-контура) и переключает весь 100% поток пользователей одномоментно. Если в новой версии есть скрытый баг, проявляющийся под нагрузкой (например, утечка горутин или дедлок), все 100% пользователей столкнутся со сбоем. \nCanary-деплой с Argo Rollouts направляет на новую версию лишь 1–5% пользователей. Если система деградирует, страдают доли процента клиентов, а автоматика закрывает канарейку за считанные секунды без участия дежурного инженера."
  },
  {
    "num": 34,
    "title": "Автоматизация релизов GoReleaser: кросс-компиляция и создание GitHub Release",
    "task": "Создайте release workflow, который при создании Git tag собирает бинарники для всех OS/arch через `goreleaser`.",
    "theory": "Сборка бинарных релизов Go под десятки платформ вручную — трудоемкий процесс. **GoReleaser** — промышленный стандарт автоматизации релизов для Go-проектов:\n- Выполняет кросс-компиляцию под все комбинации ОС и архитектур (`linux/amd64`, `darwin/arm64`, `windows/amd64`).\n- Генерирует архивы (`.tar.gz`, `.zip`), контрольные суммы (`checksums.txt`) и SBOM.\n- Формирует описание релиза (Release Notes / Changelog) на базе коммитов.\n- Создает официальный GitHub/GitLab Release и прикрепляет все артефакты.\n- Собирает и публикует сопутствующие Docker-образы.",
    "step_by_step": "1. Создайте файл конфигурации `.goreleaser.yaml`.\n2. Задайте параметры `builds`: флаги линковщика `-ldflags`, целевые `goos` и `goarch`.\n3. Создайте workflow `.github/workflows/release.yml`, срабатывающий на пуш тега `v*.*.*`.\n4. Запустите экшен `goreleaser/goreleaser-action@v5` с передачей токена `GITHUB_TOKEN`.\n5. Создайте Git-тег и проверьте сгенерированный релиз на странице репозитория.",
    "code_blocks": [
      {
        "filename": ".goreleaser.yaml",
        "lang": "yaml",
        "code": "version: 2\n\nproject_name: cloud-cli\n\nbefore:\n  hooks:\n    - go mod tidy\n\nbuilds:\n  - env:\n      - CGO_ENABLED=0\n    goos:\n      - linux\n      - darwin\n      - windows\n    goarch:\n      - amd64\n      - arm64\n    ldflags:\n      - -s -w\n      - -X main.version={{.Version}}\n      - -X main.commit={{.Commit}}\n      - -X main.date={{.Date}}\n\narchives:\n  - format: tar.gz\n    name_template: >-\n      {{ .ProjectName }}_{{ .Version }}_{{ .Os }}_{{ .Arch }}\n    format_overrides:\n      - goos: windows\n        format: zip\n\nchecksum:\n  name_template: 'checksums.txt'\n\nchangelog:\n  sort: asc\n  filters:\n    exclude:\n      - '^docs:'\n      - '^test:'"
      },
      {
        "filename": ".github/workflows/release.yml",
        "lang": "yaml",
        "code": "name: Release Management\n\non:\n  push:\n    tags:\n      - 'v*.*.*'\n\npermissions:\n  contents: write\n\njobs:\n  goreleaser:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n        with:\n          fetch-depth: 0\n\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n\n      - name: Run GoReleaser\n        uses: goreleaser/goreleaser-action@v5\n        with:\n          distribution: goreleaser\n          version: latest\n          args: release --clean\n        env:\n          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\nvar (\n\tversion = \"dev\"\n\tcommit  = \"none\"\n\tdate    = \"unknown\"\n)\n\nfunc main() {\n\tfmt.Printf(\"CLI Tool: %s (Commit: %s, Built at: %s)\\n\", version, commit, date)\n}"
      }
    ],
    "under_the_hood": "GoReleaser запускает компиляцию параллельно на всех ядрах раннера. Переменные `version`, `commit`, `date` динамически внедряются в бинарник через опции `-X main.var=value` линковщика `go tool link`.\n\nБлагодаря параметру `fetch-depth: 0` GoReleaser анализирует `git log` от предыдущего тега до текущего, группируя коммиты по типам (feat, fix, refactor) согласно спецификации Conventional Commits для построения красивого релизного списка.",
    "pitfalls": "1. Забытый `fetch-depth: 0`: Git-история коммитов будет усечена до одного коммита, и GoReleaser не сможет сгенерировать changelog или определить предыдущий тег.\n2. Отсутствие прав `permissions: contents: write`: джоба завершится ошибкой `403 Resource not accessible by integration` при попытке загрузить бинарники в GitHub Releases.\n3. Оставленные отладочные символы: отсутствие флагов `-s -w` раздувает размер бинарников в 2-3 раза.",
    "bigtech_interview": "**Вопрос с собеседования:** Как флаги линковщика `-s -w` влияют на размер бинарника Go и стек-трейсы при панике (Panic Stack Trace)?\n**Ответ:** \n- Флаг `-s` отключает генерацию таблицы символов (symbol table).\n- Флаг `-w` отключает генерацию отладочной информации DWARF (используется для отладчиков вроде GDB или Delve). \nИх комбинация уменьшает размер итогового бинарника на 30–50%. При этом **стек-трейсы при панике продолжают работать корректно**, поскольку информация об именах функций и номерах строк кода вшивается рантаймом Go в отдельную секцию `pclntab` (program counter line table), которую флаги `-s -w` не удаляют."
  },
  {
    "num": 35,
    "title": "Генерация отчета о покрытии тестами в HTML и загрузка артефакта в CI",
    "task": "**CI: Test Coverage Artifacts**: Добавь генерацию отчета о покрытии кода тестами (`go test -coverprofile=coverage.out`). Настрой пайплайн так, чтобы он сохранял этот файл как Artifact (артефакт сборки), который можно скачать после завершения пайплайна.",
    "theory": "Хотя консольный процент покрытия (`go tool cover -func`) полезен для гейтов, инженерам часто требуется детально видеть, какие именно строки, граничные условия и ветки ошибок не были покрыты тестами.\n\nУтилита стандартной поставки `go tool cover -html=coverage.out -o coverage.html`:\n- Генерирует автономный HTML-файл с CSS и JS.\n- Подсвечивает исходный код цветами: зеленый (блок кода выполнен), красный (блок не был вызван), серый (декларации/комментарии).\n- Встроенный выпадающий список позволяет переключаться между всеми файлами и пакетами репозитория.\n\nВ GitHub Actions экшен `actions/upload-artifact` сохраняет сформированный HTML-отчет в виде загружаемого ZIP-архива, доступного для скачивания разработчиками прямо из интерфейса сборки.",
    "step_by_step": "1. Запустите тесты с генерацией профиля: `go test -coverprofile=coverage.out ./...`.\n2. Преобразуйте профиль в HTML: `go tool cover -html=coverage.out -o coverage.html`.\n3. Добавьте шаг `actions/upload-artifact@v4` для загрузки `coverage.html`.\n4. Настройте срок жизни артефакта `retention-days: 14`.",
    "code_blocks": [
      {
        "filename": ".github/workflows/coverage-artifact.yml",
        "lang": "yaml",
        "code": "name: Coverage HTML Artifact\n\non:\n  pull_request:\n    branches: [ main ]\n\njobs:\n  coverage:\n    name: Generate HTML Coverage\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - name: Setup Go\n        uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n\n      - name: Run Tests and Generate Profile\n        run: |\n          go test -race -coverprofile=coverage.out ./...\n\n      - name: Convert Profile to HTML Report\n        run: |\n          go tool cover -html=coverage.out -o coverage.html\n\n      - name: Upload HTML Coverage Report\n        uses: actions/upload-artifact@v4\n        with:\n          name: html-coverage-report\n          path: coverage.html\n          retention-days: 14"
      },
      {
        "filename": "validator.go",
        "lang": "go",
        "code": "package main\n\nimport \"errors\"\n\nfunc CheckAge(age int) error {\n\tif age < 0 {\n\t\treturn errors.New(\"возраст не может быть отрицательным\")\n\t}\n\tif age > 150 {\n\t\treturn errors.New(\"нереалистичный возраст\")\n\t}\n\treturn nil\n}"
      },
      {
        "filename": "validator_test.go",
        "lang": "go",
        "code": "package main\n\nimport \"testing\"\n\nfunc TestCheckAge(t *testing.T) {\n\tif err := CheckAge(25); err != nil {\n\t\tt.Fatalf(\"CheckAge(25) вернул ошибку: %v\", err)\n\t}\n}"
      }
    ],
    "under_the_hood": "`go tool cover` парсит AST каждого Go-файла и считывает диапазоны из `coverage.out`. \n\nПри рендеринге HTML утилита кодирует исходные файлы Go в escape-последовательности и оборачивает каждый блок в теги `<span class=\"cov8\">...</span>` или `<span class=\"cov0\">...</span>`, где цифра соответствует частоте выполнения блока (от 0 до 10). Результирующий файл является полностью самодостаточным (inlined styles) и открывается в любом браузере локально без веб-сервера.",
    "pitfalls": "1. Отсутствие параметра `retention-days`: тяжелые артефакты быстро забьют дисковую квоту организации.\n2. Попытка открыть `coverage.html` на машине, где нет исходного кода: если HTML сгенерирован встроенной утилитой, исходный код уже зашит внутрь HTML, но если использовать сторонние генераторы, они могут ссылаться на внешние пути.\n3. Генерация coverage без флага `-covermode=atomic` при многопоточном коде приводит к фатальным падениям тестов.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем ограничение метрики «Line Coverage» (покрытие строк) и почему «Branch Coverage» (покрытие ветвей) надежнее?\n**Ответ:** Покрытие строк просто фиксирует, выполнилась ли строка кода. В конструкции вида `if a && b { doSomething() }`, если тест проверяет только случай `a=true, b=true`, строка `if` будет помечена как 100% покрытая. \nОднако ветка `b=false` протестирована не была, и логическая ошибка останется незамеченной. Branch Coverage требует протестировать все возможные исходы каждого булева условия (`true` и `false`), гарантируя отсутствие слепых зон в критической логике."
  },
  {
    "num": 36,
    "title": "Релизный пайплайн по Git-тегам: сборка и выгрузка ассетов в GitHub Release",
    "task": "**[Релизный пайплайн (Tags)]**: Настрой триггер на создание Git-тега (например, `v1.0.0`). Пайплайн должен собрать бинарники под разные ОС (linux, windows, darwin), заархивировать их и создать Release в GitHub.",
    "theory": "Формирование официального релиза в Git — ключевой момент поставки артефактов пользователям и downstream-системам.\n\nРелизный пайплайн обязан:\n1. Срабатывать строго при создании аннотированного Git-тега (`git tag -a v1.0.0 -m \"Release 1.0.0\"`).\n2. Выполнять строгую компиляцию без отладочных данных с инъекцией версии.\n3. Создавать запись GitHub Release через API (`softprops/action-gh-release`).\n4. Автоматически генерировать контрольные суммы (SHA-256) для предотвращения подмены бинарников.\n5. Прикреплять архив и хэши в релизные ассеты.",
    "step_by_step": "1. Настройте триггер workflow на событие `push.tags: ['v*.*.*']`.\n2. Настройте компиляцию утилиты под целевую ОС (Linux amd64).\n3. Сгенерируйте контрольную сумму: `sha256sum binary > binary.sha256`.\n4. Используйте экшен `softprops/action-gh-release@v2` для публикации релиза и загрузки файлов.\n5. Проверьте права токена `permissions: contents: write`.",
    "code_blocks": [
      {
        "filename": ".github/workflows/tag-release.yml",
        "lang": "yaml",
        "code": "name: Publish Tagged Release\n\non:\n  push:\n    tags:\n      - 'v*.*.*'\n\npermissions:\n  contents: write\n\njobs:\n  build-and-release:\n    name: Build & Attach Release Assets\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout Code\n        uses: actions/checkout@v4\n\n      - name: Setup Go\n        uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n\n      - name: Build Binary\n        run: |\n          mkdir -p dist\n          CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags=\"-s -w -X main.version=${{ github.ref_name }}\" -o dist/mycli-linux-amd64 .\n          cd dist\n          sha256sum mycli-linux-amd64 > mycli-linux-amd64.sha256\n\n      - name: Create GitHub Release\n        uses: softprops/action-gh-release@v2\n        with:\n          files: |\n            dist/mycli-linux-amd64\n            dist/mycli-linux-amd64.sha256\n          draft: false\n          prerelease: false\n          generate_release_notes: true"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n)\n\nvar version = \"dev\"\n\nfunc main() {\n\tif len(os.Args) > 1 && os.Args[1] == \"--version\" {\n\t\tfmt.Printf(\"MyCLI version %s\\n\", version)\n\t\treturn\n\t}\n\tfmt.Println(\"CLI инструмент готов к выполнению команд.\")\n}"
      }
    ],
    "under_the_hood": "Экшен `softprops/action-gh-release` взаимодействует с GitHub REST API:\n`POST /repos/{owner}/{repo}/releases`\nПараметр `generate_release_notes: true` задействует встроенный движок генерации описания релизов GitHub, который парсит заголовки объединенных PR со времени предыдущего релиза и формирует аккуратный Markdown-список изменений с указанием авторов коммитов.",
    "pitfalls": "1. Забытый `permissions: contents: write`: джоба завершится с `403 Forbidden` при попытке создать релиз.\n2. Создание релиза без файла SHA-256: безопасность цепочки поставок нарушается, пользователи не могут проверить целостность скачанного исполняемого файла.\n3. Использование `draft: false` для непротестированных тегов: если тег запушен по ошибке, релиз моментально станет доступен пользователям.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между легковесным тегом (`lightweight tag`) и аннотированным тегом (`annotated tag`) в Git, и какой из них следует использовать в CI/CD?\n**Ответ:** Легковесный тег — это просто указатель на конкретный коммит (подобно ветке, которая не двигается). Аннотированный тег (`git tag -a`) сохраняется в базе Git как полноценный объект: он содержит имя автора тега, email, дату создания, сообщение релиза и опционально криптографическую GPG-подпись. В релизных пайплайнах CI/CD следует использовать **только аннотированные подписанные теги**, поскольку они гарантируют подлинность автора релиза."
  },
  {
    "num": 37,
    "title": "GitOps с Flux CD: GitRepository, Kustomization и автоматизация обновления образов",
    "task": "Настрой **Flux CD** (alternative to ArgoCD): `GitRepository` + `Kustomization` + `ImagePolicy` + `ImageUpdateAutomation`. Автоматическое обновление image tag в Git при новом Docker image. Покажи GitOps with Flux.",
    "theory": "**Flux CD** — флагманский GitOps-инструментарий проекта CNCF, построенный на микросервисной архитектуре контроллеров:\n- **`source-controller`:** Следит за Git-репозиториями (`GitRepository`), OCI-артефактами и Helm-репозиториями.\n- **`kustomize-controller`:** Применяет Kustomize-манифесты (`Kustomization`) в кластер, обеспечивая непрерывную сверку (reconciliation).\n- **`image-reflector-controller`:** Сканирует реестр контейнеров и ищет новые теги образов (`ImageRepository`).\n- **`image-automation-controller`:** При появлении нового OCI-образа автоматически коммитит измененный тег обратно в Git-репозиторий (`ImageUpdateAutomation`).\n\nЭтот цикл полностью автоматизирует Continuous Deployment: CI пушит образ в реестр → Flux обнаруживает тег → Flux обновляет Git → кластер синхронизируется.",
    "step_by_step": "1. Создайте CRD `GitRepository`, указав адрес git-репозитория инфраструктуры.\n2. Создайте CRD `Kustomization` для развертывания каталога `deploy/production`.\n3. Настройте `ImageRepository` для отслеживания тегов в реестре.\n4. Настройте `ImagePolicy` с фильтром по SemVer (`>=1.0.0 <2.0.0`).\n5. Настройте `ImageUpdateAutomation` для коммита новых версий в Git.",
    "code_blocks": [
      {
        "filename": "flux-git-sync.yaml",
        "lang": "yaml",
        "code": "apiVersion: source.toolkit.fluxcd.io/v1\nkind: GitRepository\nmetadata:\n  name: fleet-infra\n  namespace: flux-system\nspec:\n  interval: 1m\n  url: https://github.com/company/fleet-infra.git\n  ref:\n    branch: main\n---\napiVersion: kustomize.toolkit.fluxcd.io/v1\nkind: Kustomization\nmetadata:\n  name: payment-service\n  namespace: flux-system\nspec:\n  interval: 5m\n  path: \"./apps/production/payment\"\n  prune: true\n  sourceRef:\n    kind: GitRepository\n    name: fleet-infra\n  validation: client"
      },
      {
        "filename": "flux-image-automation.yaml",
        "lang": "yaml",
        "code": "apiVersion: image.toolkit.fluxcd.io/v1beta2\nkind: ImageRepository\nmetadata:\n  name: payment-image\n  namespace: flux-system\nspec:\n  image: ghcr.io/company/payment\n  interval: 1m\n---\napiVersion: image.toolkit.fluxcd.io/v1beta2\nkind: ImagePolicy\nmetadata:\n  name: payment-policy\n  namespace: flux-system\nspec:\n  imageRepositoryRef:\n    name: payment-image\n  policy:\n    semver:\n      range: '^1.0.0'\n---\napiVersion: image.toolkit.fluxcd.io/v1beta1\nkind: ImageUpdateAutomation\nmetadata:\n  name: payment-auto-commit\n  namespace: flux-system\nspec:\n  interval: 1m\n  sourceRef:\n    kind: GitRepository\n    name: fleet-infra\n  git:\n    checkout:\n      ref:\n        branch: main\n    commit:\n      author:\n        name: fluxcdbot\n        email: fluxcdbot@users.noreply.github.com\n      messageTemplate: 'chore(cd): update payment image to {{range .Updated.Images}}{{println .}}{{end}}'\n    push:\n      branch: main\n  update:\n    path: ./apps/production/payment\n    strategy: Setters"
      }
    ],
    "under_the_hood": "В манифестах Kustomize целевой тег помечается специальным комментарием: `image: ghcr.io/company/payment:v1.0.0 # {\"$imagepolicy\": \"flux-system:payment-policy\"}`. \n\n`ImageAutomationController` парсит AST YAML-файлов, находит маркер `$imagepolicy` и заменяет значение тега на наивысшую версию, удовлетворяющую SemVer. Затем контроллер выполняет `git commit` и `git push` по SSH-ключу или GitHub App токену.",
    "pitfalls": "1. Конфликты слияния (Merge Conflicts): если разработчики коммитят в ту же ветку `main`, куда пишет бот Flux, пуш упадет с ошибкой non-fast-forward.\n2. Бесконечный цикл перегенерации коммитов при некорректном синтаксисе комментариев-сеттеров.\n3. Отсутствие валидации прав доступа к Git-репозиторию: бот падает при попытке push в защищенную ветку.",
    "bigtech_interview": "**Вопрос с собеседования:** Сравните архитектурные подходы ArgoCD и Flux CD. В каких сценариях Flux предпочтительнее?\n**Ответ:** \n- **ArgoCD** — монолитное приложение с мощным визуальным UI, встроенным SSO и RBAC. Отлично подходит для больших команд разработки, которым нужен красивый дашборд для наблюдения за состоянием сервисов.\n- **Flux CD** построен по строгой Unix-философии K8s-native контроллеров без обязательного UI. Он потребляет значительно меньше ресурсов, идеально масштабируется для управления тысячами edge-кластеров (Fleet Management) и обладает нативной встроенной автоматизацией обратного коммита тегов в Git (`ImageUpdateAutomation`)."
  },
  {
    "num": 38,
    "title": "Продвинутая мультиплатформенная сборка Docker-образов через QEMU и Buildx",
    "task": "Настройте multi-arch Docker образы через `docker/setup-qemu-action` и `docker/setup-buildx-action`.",
    "theory": "При промышленной сборке мульти-архитектурных образов (`amd64` и `arm64`) критично оптимизировать время работы CI. Эмуляция инструкций ARM через QEMU медленнее нативной компиляции в 5–10 раз.\n\nПродвинутый подход совмещает:\n1. **`binfmt` эмуляцию:** Регистрация эмуляторов QEMU в ядре раннера через `docker/setup-qemu-action`.\n2. **BuildKit Multi-Platform Cross-Compilation:** Использование нативных возможностей Go кросс-компиляции (`GOOS=linux GOARCH=arm64`), исключая запуск самого компилятора Go внутри QEMU.\n3. **Общий экспорт манифеста:** Создание единого мульти-архитектурного OCI-дескриптора.",
    "step_by_step": "1. Добавьте шаги `setup-qemu-action` и `setup-buildx-action`.\n2. В Dockerfile организуйте stage сборки с флагом `--platform=$BUILDPLATFORM`.\n3. Используйте аргументы `TARGETPLATFORM`, `TARGETOS`, `TARGETARCH`.\n4. В GitHub Actions укажите `platforms: linux/amd64,linux/arm64`.\n5. Протестируйте итоговый образ на обеих архитектурах.",
    "code_blocks": [
      {
        "filename": ".github/workflows/advanced-multiarch.yml",
        "lang": "yaml",
        "code": "name: Advanced Multi-Arch CI\n\non:\n  push:\n    branches: [ main ]\n\njobs:\n  multiarch:\n    name: Build & Push AMD64/ARM64\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - name: Set up QEMU\n        uses: docker/setup-qemu-action@v3\n        with:\n          platforms: all\n\n      - name: Set up Docker Buildx\n        uses: docker/setup-buildx-action@v3\n\n      - name: Log in to GHCR\n        uses: docker/login-action@v3\n        with:\n          registry: ghcr.io\n          username: ${{ github.actor }}\n          password: ${{ secrets.GITHUB_TOKEN }}\n\n      - name: Build & Push Image\n        uses: docker/build-push-action@v5\n        with:\n          context: .\n          platforms: linux/amd64,linux/arm64\n          push: true\n          tags: ghcr.io/${{ github.repository }}:latest"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# syntax=docker/dockerfile:1\nFROM --platform=$BUILDPLATFORM golang:1.24-alpine AS builder\nARG TARGETOS\nARG TARGETARCH\n\nWORKDIR /src\nCOPY go.mod go.sum* ./\nRUN go mod download\n\nCOPY . .\n# Нативная кросс-компиляция компилятором хоста:\nRUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} \\\n    go build -ldflags=\"-s -w\" -o /out/app .\n\nFROM alpine:3.21\nWORKDIR /app\nCOPY --from=builder /out/app /app/server\nUSER 65534:65534\nENTRYPOINT [\"/app/server\"]"
      }
    ],
    "under_the_hood": "Модуль ядра Linux `binfmt_misc` перехватывает системный вызов `execve`. Когда ОС пытается запустить бинарник ARM64 на процессоре x86_64, ядро определяет сигнатуру ELF-заголовка и автоматически передает исполнение эмулятору `/usr/bin/qemu-aarch64-static`. \n\nБлагодаря флагу `--platform=$BUILDPLATFORM` BuildKit скачивает компилятор Go родной архитектуры хоста (x86_64), поэтому Go компилирует ARM64-код на полной скорости процессора хоста без единого вызова QEMU!",
    "pitfalls": "1. Ошибочный запуск тестов `go test` на этапе сборки контейнера под чужую архитектуру: тесты будут исполняться внутри QEMU, что замедлит сборку в разы. Тесты следует прогонять в отдельной нативной джобе CI до сборки контейнера.\n2. Пропуск аргументов `ARG TARGETOS` и `ARG TARGETARCH`: Go скомпилирует бинарник под платформу билдера (`amd64`), и образ упадет на ARM-ноде.\n3. Проблемы с CGO: при кросс-компиляции CGO отключен по умолчанию, попытка включить его без кросс-тулчейнов C приведет к ошибкам компилятора.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему запуск юнит-тестов Go внутри эмулируемого через QEMU контейнера считается антипаттерном в CI?\n**Ответ:** QEMU транслирует инструкции гостевой архитектуры в команды хоста на лету. Это приводит к колоссальному падению производительности CPU (в 5–10 раз) и искажению таймингов синхронизации (гонки данных и дедлоки могут либо маскироваться, либо проявляться ложно). \nПравильный подход — прогонять все тесты и линтеры на нативных раннерах x86_64, а компиляцию под ARM64 выполнять кросс-компилятором Go, тестируя бинарник на настоящих ARM-нодах только на этапе E2E/Smoke."
  },
  {
    "num": 39,
    "title": "Cloud-Native CI/CD с Tekton: Task, Pipeline и декларативные PipelineRun",
    "task": "Настрой **Tekton** (cloud-native CI/CD): `Task`, `TaskRun`, `Pipeline`, `PipelineRun`. Reusable tasks: `git-clone`, `buildah`, `kubectl-deploy`. Покажи Kubernetes-native CI/CD.\n\n---",
    "theory": "**Tekton** — облачный движок непрерывной интеграции и доставки (CI/CD), разработанный под эгидой Continuous Delivery Foundation (CDF):\n- Полностью K8s-native: нет центрального CI-сервера; каждый шаг пайплайна исполняется как отдельный контейнер внутри Kubernetes Pod.\n- Основные строительные блоки:\n  - **`Task`:** Набор последовательных шагов (`steps`), выполняемых внутри одного Pod на одной ноде (шаги разделяют общее дисковое пространство через `workspace`).\n  - **`Pipeline`:** Граф задач (DAG из `Task`), определяющий порядок и зависимости выполнения.\n  - **`PipelineRun`:** Экземпляр запуска пайплайна с конкретными параметрами, ветками Git и хранилищем.",
    "step_by_step": "1. Создайте CRD `Task` для сборки Go-приложения (`go test` и `go build`).\n2. Опишите `Pipeline`, объединяющий задачу клонирования репозитория и задачу сборки.\n3. Настройте общий `workspace` на базе PersistentVolumeClaim.\n4. Создайте `PipelineRun` для запуска конвейера.\n5. Отслеживайте выполнение через Tekton CLI: `tkn pipelinerun logs -f`.",
    "code_blocks": [
      {
        "filename": "tekton-task.yaml",
        "lang": "yaml",
        "code": "apiVersion: tekton.dev/v1beta1\nkind: Task\nmetadata:\n  name: golang-build\n  namespace: ci\nspec:\n  workspaces:\n    - name: source\n  steps:\n    - name: test\n      image: golang:1.24-alpine\n      workingDir: $(workspaces.source.path)\n      script: |\n        go test -v ./...\n\n    - name: compile\n      image: golang:1.24-alpine\n      workingDir: $(workspaces.source.path)\n      script: |\n        CGO_ENABLED=0 go build -ldflags=\"-s -w\" -o bin/server ."
      },
      {
        "filename": "tekton-pipeline.yaml",
        "lang": "yaml",
        "code": "apiVersion: tekton.dev/v1beta1\nkind: Pipeline\nmetadata:\n  name: app-ci-pipeline\n  namespace: ci\nspec:\n  workspaces:\n    - name: shared-workspace\n  tasks:\n    - name: fetch-repo\n      taskRef:\n        name: git-clone\n      workspaces:\n        - name: output\n          workspace: shared-workspace\n      params:\n        - name: url\n          value: \"https://github.com/company/app.git\"\n        - name: revision\n          value: \"main\"\n\n    - name: build-app\n      taskRef:\n        name: golang-build\n      runAfter:\n        - fetch-repo\n      workspaces:\n        - name: source\n          workspace: shared-workspace"
      },
      {
        "filename": "tekton-run.yaml",
        "lang": "yaml",
        "code": "apiVersion: tekton.dev/v1beta1\nkind: PipelineRun\nmetadata:\n  generateName: app-run-\n  namespace: ci\nspec:\n  pipelineRef:\n    name: app-ci-pipeline\n  workspaces:\n    - name: shared-workspace\n      volumeClaimTemplate:\n        spec:\n          accessModes:\n            - ReadWriteOnce\n          resources:\n            requests:\n              storage: 2Gi"
      }
    ],
    "under_the_hood": "При создании ресурса `PipelineRun` Tekton Controller анализирует граф зависимостей `runAfter`. Для каждого Task создается Kubernetes Pod. \n\nВсе контейнеры шагов (`steps`) внутри этого пода монтируются к общей директории `emptyDir` или `PersistentVolumeClaim` (workspace). Порядок выполнения шагов строго гарантируется контроллером через инициализационные контейнеры и точки синхронизации файловой блокировки.",
    "pitfalls": "1. Использование нескольких Task с workspace типа `ReadWriteOnce` (RWO) на разных нодах кластера: K8s не может смонтировать один RWO-том на два пода на разных физических серверах одновременно.\n2. Отсутствие сборщика мусора (Tekton Pruner): завершенные объекты `PipelineRun` и `TaskRun` накапливаются в Etcd, вызывая деградацию K8s API.\n3. Долгий cold-start: каждый шаг скачивает свои образы контейнеров, если они не закешированы на ноде.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем ключевое различие между Tekton и традиционными системами CI/CD вроде GitHub Actions или GitLab CI?\n**Ответ:** GitHub Actions и GitLab CI — это монолитные SaaS/готовые платформы со своими агентами и серверами координации. \nTekton — это **низкоуровневый K8s-фреймворк/спецификация**. Он не предназначен для конечного разработчика напрямую, а служит строительным фундаментом для Platform Engineering команд, строящих внутренние порталы разработки (IDP) в enterprise-компаниях. Многие платформы (OpenShift Pipelines, Jenkins X) работают на базе Tekton."
  },
  {
    "num": 40,
    "title": "Автоматическая очистка устаревших Issue и PR с помощью actions/stale",
    "task": "Добавьте `stale` workflow для автоматического закрытия неактивных issues и PR.",
    "theory": "В крупных проектах с открытым исходным кодом или монорепозиториях компании накапливаются сотни заброшенных Pull Request и тикетов (Issue), на запросы дополнительной информации по которым авторы не отвечают месяцами.\n\nЭкшен **`actions/stale`**:\n- Запускается по расписанию (cron).\n- Автоматически помечает тикеты и PR лейблом `stale` после заданного периода неактивности (например, 60 дней).\n- Отправляет вежливое уведомление автору с просьбой подтвердить актуальность.\n- Если в течение следующих 7 дней активности нет, тикет/PR автоматически закрывается.\n- Любой новый комментарий пользователя автоматически снимает лейбл `stale`.",
    "step_by_step": "1. Создайте `.github/workflows/stale.yml`.\n2. Настройте триггер `schedule` на запуск раз в сутки (например, в полночь).\n3. Используйте экшен `actions/stale@v9`.\n4. Задайте `days-before-stale: 60` и `days-before-close: 7`.\n5. Настройте исключение тикетов с лейблом `pinned` или `security`.",
    "code_blocks": [
      {
        "filename": ".github/workflows/stale.yml",
        "lang": "yaml",
        "code": "name: Mark Stale Issues and PRs\n\non:\n  schedule:\n    - cron: '0 0 * * *'\n  workflow_dispatch:\n\npermissions:\n  issues: write\n  pull-requests: write\n\njobs:\n  stale:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/stale@v9\n        with:\n          repo-token: ${{ secrets.GITHUB_TOKEN }}\n          stale-issue-message: 'Этот тикет помечен как устаревший из-за отсутствия активности в течение 60 дней. Он будет закрыт через 7 дней, если не поступит новых комментариев.'\n          stale-pr-message: 'Этот Pull Request помечен как устаревший из-за неактивности. Он будет автоматически закрыт через 7 дней.'\n          stale-issue-label: 'stale'\n          stale-pr-label: 'stale'\n          days-before-stale: 60\n          days-before-close: 7\n          exempt-issue-labels: 'pinned,security,roadmap'\n          exempt-pr-labels: 'work-in-progress,blocked'"
      }
    ],
    "under_the_hood": "Экшен опрашивает GitHub Issues API:\n`GET /repos/{owner}/{repo}/issues?state=open&sort=updated&direction=asc`\nЭкшен фильтрует записи по полю `updated_at`. Если время последнего обновления превышает `days-before-stale`, экшен выполняет `POST` запрос на добавление лейбла и комментария. \n\nПри следующем запуске, если дата комментария с пометкой stale превышает `days-before-close`, экшен отправляет `PATCH /issues/{id}` со статусом `state: closed`.",
    "pitfalls": "1. Слишком агрессивные тайминги (например, 7 дней до stale): раздражает контрибьюторов, которые ушли в отпуск.\n2. Отсутствие исключений (`exempt-issue-labels`): бот закрывает важные долгосрочные задачи из дорожной карты (roadmap).\n3. Забытые права `permissions: issues: write, pull-requests: write`: падение с ошибкой прав доступа.",
    "bigtech_interview": "**Вопрос с собеседования:** Какую роль играет автоматизация жизненного цикла Issues/PR в поддержании гигиены репозиториев (Repo Hygiene) в BigTech?\n**Ответ:** Открытые заброшенные PR создают иллюзию незавершенной работы, засоряют поиск, создают конфликты слияния и требуют регулярного внимания мейнтейнеров. \nАвтоматизация закрытия неактивных тикетов высвобождает время ведущих инженеров, стимулирует авторов доводить код до конца и поддерживает актуальность бэклога без ручной рутины."
  },
  {
    "num": 41,
    "title": "Оптимизация графа стадий в GitLab CI через Directed Acyclic Graph (DAG)",
    "task": "**GitLab CI аналог**: Создайте `.gitlab-ci.yml` с stages: `lint`, `test`, `build`, `deploy`. Используйте `kaniko` для build Docker-образа без Docker daemon.",
    "theory": "По умолчанию в GitLab CI стадии (`stages`) выполняются строго последовательно: все джобы стадии `test` обязаны завершиться, прежде чем стартует хотя бы одна джоба стадии `build`.\n\nЕсли в стадии `test` есть долгий тест (15 минут), а параллельно выполняется быстрый линтер (1 минута), джоба сборки контейнера будет простаивать 14 минут!\n\nДиректива **`needs: [...]`** внедряет модель **Directed Acyclic Graph (DAG)**:\n- Разрывает жесткую линейную зависимость стадий.\n- Джоба стартует **немедленно**, как только завершатся строго указанные в `needs` предшественники, игнорируя незавершенные джобы текущей или предыдущих стадий.\n- Это сокращает общее время прохождения конвейера (Pipeline Wall-Clock Time) в разы.",
    "step_by_step": "1. Создайте `.gitlab-ci.yml` с четырьмя стадиями: `lint`, `test`, `build`, `deploy`.\n2. В джобе сборки Docker-образа укажите `needs: [\"job:linter\"]`, чтобы она не ждала долгих тестов.\n3. В джобе деплоя укажите зависимость от сборки образа и интеграционных тестов: `needs: [\"job:docker_build\", \"job:integration_tests\"]`.\n4. Сравните время выполнения линейного пайплайна и DAG-графа.",
    "code_blocks": [
      {
        "filename": ".gitlab-ci.yml",
        "lang": "yaml",
        "code": "stages:\n  - lint\n  - test\n  - build\n  - deploy\n\njob:linter:\n  stage: lint\n  image: golangci/golangci-lint:v1.64.5-alpine\n  script:\n    - golangci-lint run --timeout=2m\n\njob:unit_tests:\n  stage: test\n  image: golang:1.24-alpine\n  script:\n    - go test -v -short ./...\n\njob:integration_tests:\n  stage: test\n  image: golang:1.24-alpine\n  script:\n    - sleep 60 # Симуляция долгих тестов с базой данных\n    - go test -v ./internal/database/...\n\njob:docker_build:\n  stage: build\n  # Джоба стартует сразу после линтера, не дожидаясь долгих интеграционных тестов!\n  needs:\n    - job:linter\n  image: docker:27-cli\n  services:\n    - docker:27-dind\n  script:\n    - docker build -t myapp:$CI_COMMIT_SHA .\n\njob:deploy_staging:\n  stage: deploy\n  needs:\n    - job:docker_build\n    - job:integration_tests\n  script:\n    - echo \"Deploying to Staging after both Docker Build and Integration Tests finish!\" "
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /app\nCOPY . .\nRUN CGO_ENABLED=0 go build -o /app/server .\n\nFROM alpine:3.21\nCOPY --from=builder /app/server /server\nENTRYPOINT [\"/server\"]"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\nfunc main() {\n\tfmt.Println(\"DAG Pipeline Demo Service\")\n}"
      }
    ],
    "under_the_hood": "GitLab CI планировщик строит топологический граф (DAG). Каждому узлу графа соответствует джоба, а ребрам — связи `needs`. \n\nКак только входящие ребра узла переходят в состояние `Success`, планировщик мгновенно отправляет джобу в очередь выполнения раннеров. По умолчанию `needs` также передает артефакты только указанных джобов, что снижает нагрузку на сеть при скачивании промежуточных файлов.",
    "pitfalls": "1. Циклические зависимости (`A needs B`, а `B needs A`): GitLab отклонит `.gitlab-ci.yml` с ошибкой валидации схемы.\n2. Непреднамеренная потеря артефактов: если джоба использует `needs`, она больше не скачивает артефакты всех предыдущих стадий по умолчанию — нужно явно перечислить источники артефактов.\n3. Преждевременный деплой: если забыть связать `deploy` с `test` через `needs`, сервис задеплоится даже при упавших тестах!",
    "bigtech_interview": "**Вопрос с собеседования:** В каких случаях использование `needs` (DAG) в GitLab CI может привести к инциденту на продакшне при невнимательной настройке?\n**Ответ:** Если в пайплайне джоба `deploy` настроена с `needs: [docker_build]`, но инженер забыл добавить в `needs` джобу `security_audit` или `integration_tests`. В такой конфигурации деплой запустится и успешно завершится, как только соберется Docker-образ, даже если интеграционные тесты параллельно упали с ошибкой. В джобе деплоя обязаны быть перечислены все критические барьеры качества."
  },
  {
    "num": 42,
    "title": "Continuous Delivery: защищенная публикация Docker-образа по Git SHA",
    "task": "**CD: Сборка и Push образа**: Создай секрет в настройках GitHub (токен от DockerHub или GitHub Container Registry). Напиши новую джобу (Job) в пайплайне: если тесты прошли успешно, собирай Docker-образ и делай `docker push` с тегом, равным хэшу коммита (`${{ github.sha }}`).",
    "theory": "В концепции Continuous Delivery каждый успешный коммит в ветку `main` потенциально готов к релизу. Образ приложения компилируется, тестируется и публикуется в доверенный реестр контейнеров.\n\nПринципы безопасного CD:\n1. **Строгая изоляция секретов:** Использование зашифрованных GitHub Secrets с минимальными правами доступа.\n2. **Неизменяемость (Immutability):** Образ тегируется SHA коммита (`${{ github.sha }}`) и датой сборки. Тег `:latest` используется исключительно как псевдоним для ручных тестов.\n3. **Защита от запуска на форках:** Секреты сборщика никогда не должны быть доступны в Pull Request из сторонних форков репозитория.",
    "step_by_step": "1. Добавьте секреты `DOCKERHUB_USER` и `DOCKERHUB_TOKEN` в настройки репозитория.\n2. Настройте условие `if: github.ref == 'refs/heads/main'` для исключения публикации образов из веток разработки.\n3. Сгенерируйте детерминированные теги OCI.\n4. Выполните сборку и публикацию через `docker/build-push-action`.\n5. Проверьте опубликованный манифест в реестре.",
    "code_blocks": [
      {
        "filename": ".github/workflows/cd-publish.yml",
        "lang": "yaml",
        "code": "name: CD Production Image Publish\n\non:\n  push:\n    branches: [ main ]\n\njobs:\n  publish:\n    name: Build & Push Production Image\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout Source Code\n        uses: actions/checkout@v4\n\n      - name: Set up Docker Buildx\n        uses: docker/setup-buildx-action@v3\n\n      - name: Login to DockerHub\n        uses: docker/login-action@v3\n        with:\n          username: ${{ secrets.DOCKERHUB_USER }}\n          password: ${{ secrets.DOCKERHUB_TOKEN }}\n\n      - name: Build and Push\n        uses: docker/build-push-action@v5\n        with:\n          context: .\n          push: true\n          tags: |\n            ${{ secrets.DOCKERHUB_USER }}/api-service:${{ github.sha }}\n            ${{ secrets.DOCKERHUB_USER }}/api-service:latest"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /app\nCOPY go.mod go.sum* ./\nRUN go mod download\nCOPY . .\nRUN CGO_ENABLED=0 go build -ldflags=\"-s -w\" -o /app/api .\n\nFROM alpine:3.21\nUSER 65534:65534\nCOPY --from=builder /app/api /api\nENTRYPOINT [\"/api\"]"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/api/v1/status\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\t_, _ = w.Write([]byte(`{\"status\":\"online\"}`))\n\t})\n\tfmt.Println(\"API server ready\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "Когда коммит мерджится в `main`, GitHub Actions инициирует событие `push`. BuildKit отправляет слои в Docker Registry v2 API. \n\nСначала передаются блобы слоев (`POST /v2/<name>/blobs/uploads/`), затем отправляется манифест образа. При наличии двух тегов (`${{ github.sha }}` и `latest`) BuildKit загружает блобы слоев данных ровно один раз, создавая лишь два указателя-манифеста в реестре, ссылающихся на единый корневой config hash.",
    "pitfalls": "1. Запуск джобы сборки с `push: true` на событие `pull_request`: публикация непроверенного кода в прод-реестр.\n2. Утечка токена в логах сборки: вывод переменных окружения командой `env` или `set -x`.\n3. Отсутствие healthcheck или тестов перед этапом сборки контейнера.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в Continuous Delivery пайплайнах запрещено пересобирать Docker-образ при продвижении (promotion) со Staging в Production?\n**Ответ:** Повторная сборка (`docker build`) нарушает принцип детерминизма артефактов (Artifact Immutability). Даже разница в 5 минут может привести к скачиванию обновленного минорного системного пакета из `apk/apt` или изменению временных меток. Образ должен быть собран **строго один раз** на этапе CI. Для продвижения в Production используется тот же самый OCI-образ (по SHA256-дайджесту), который прошел все тесты на Staging."
  },
  {
    "num": 43,
    "title": "Автоматизация SemVer версионирования и генерация Changelog с git-chglog",
    "task": "**[SemVer и Changelog]**: Автоматизируй генерацию changelog при релизе (например, с помощью `release-please` или интеграции с Jira/Issues).",
    "theory": "Семантическое версионирование (**Semantic Versioning — SemVer 2.0.0**) кодирует изменения формата `MAJOR.MINOR.PATCH`:\n- `PATCH`: исправление ошибок без нарушения обратной совместимости.\n- `MINOR`: добавление новой функциональности с сохранением обратной совместимости.\n- `MAJOR`: несовместимые изменения API (Breaking Changes).\n\nВместо ручного ведения файла `CHANGELOG.md` применяются утилиты вроде **`git-chglog`** или **`release-drafter`**, парсящие коммиты по стандарту Conventional Commits:\n- `feat:` -> Minor инкремент\n- `fix:` -> Patch инкремент\n- `feat!:` или `BREAKING CHANGE:` -> Major инкремент.",
    "step_by_step": "1. Создайте шаблон форматирования `.chglog/config.yml`.\n2. Настройте экшен генерации changelog в GitHub Actions при создании релиза.\n3. Установите `git-chglog` и выполните генерацию истории изменений: `git-chglog -o CHANGELOG.md`.\n4. Автоматически закомиттье обновленный `CHANGELOG.md` или прикрепите его текст к GitHub Release.",
    "code_blocks": [
      {
        "filename": ".chglog/config.yml",
        "lang": "yaml",
        "code": "style: github\ntemplate: CHANGELOG.tpl.md\ninfo:\n  title: CHANGELOG\n  repository_url: https://github.com/company/project\noptions:\n  commits:\n    filters:\n      Type:\n        - feat\n        - fix\n        - perf\n        - refactor\n  commit_groups:\n    title_maps:\n      feat: Features\n      fix: Bug Fixes\n      perf: Performance Improvements\n      refactor: Code Refactoring"
      },
      {
        "filename": ".github/workflows/changelog.yml",
        "lang": "yaml",
        "code": "name: Generate Changelog\n\non:\n  push:\n    tags:\n      - 'v*.*.*'\n\npermissions:\n  contents: write\n\njobs:\n  changelog:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n        with:\n          fetch-depth: 0\n\n      - name: Install git-chglog\n        run: |\n          curl -sL https://github.com/git-chglog/git-chglog/releases/download/v0.15.4/git-chglog_0.15.4_linux_amd64.tar.gz | tar xz\n          sudo mv git-chglog /usr/local/bin/\n\n      - name: Generate Changelog\n        run: |\n          git-chglog -o CHANGELOG.md\n          git-chglog $(git describe --tags --abbrev=0) > RELEASE_NOTES.md\n\n      - name: Update GitHub Release Notes\n        uses: softprops/action-gh-release@v2\n        with:\n          body_path: RELEASE_NOTES.md"
      },
      {
        "filename": "version.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\nconst CurrentVersion = \"1.3.0\"\n\nfunc PrintVersion() {\n\tfmt.Printf(\"Сервис Версия: %s\\n\", CurrentVersion)\n}"
      }
    ],
    "under_the_hood": "`git-chglog` обращается к Git CLI: парсит граф коммитов между смежными тегами (`git log <prev-tag>..<current-tag>`), извлекая хеш коммита, имя автора и тему сообщения. \n\nЗатем утилита прогоняет структурированные данные через Go Template (`CHANGELOG.tpl.md`), группируя коммиты по секциям и связывая хеши гиперссылками на коммиты в веб-интерфейсе GitHub.",
    "pitfalls": "1. Несоблюдение командой формата Conventional Commits: коммиты с сообщениями вроде «fix», «update», «work» не попадают в сгенерированный лог.\n2. Shallow clone (`fetch-depth: 1`): утилита видит только один коммит и не может определить предыдущие теги.\n3. Зацикливание CI: если экшен коммитит `CHANGELOG.md` обратно в ветку `main`, это может вызвать повторный триггер workflow, если не настроить фильтры `[skip ci]`.",
    "bigtech_interview": "**Вопрос с собеседования:** Как автоматизировать выбор следующей версии SemVer (0.1.0 -> 0.2.0 или 1.0.0) в CI без ручного участия разработчика?\n**Ответ:** Используются утилиты семантического релиза (**Semantic Release** / **GoReleaser** / **svu**). Они анализируют сообщения коммитов со времени последнего Git-тега:\n- Если есть `BREAKING CHANGE:` или восклицательный знак (`feat!:`), инкрементируется `MAJOR`.\n- Если максимальный уровень — `feat:`, инкрементируется `MINOR`.\n- Если только `fix:` или `perf:`, инкрементируется `PATCH`.\nCI-пайплайн автоматически генерирует следующий тег (например, `v1.4.0`) и пушит его в Git, запуская релизную сборку."
  },
  {
    "num": 44,
    "title": "GitLab Container Registry и автоматический деплой в Kubernetes",
    "task": "Настройте GitLab Container Registry и automatic deploy на Kubernetes через GitLab CI/CD.",
    "theory": "GitLab предлагает нативную интеграцию между встроенным реестром контейнеров (GitLab Container Registry) и кластером Kubernetes через GitLab Agent for Kubernetes или переменные окружения CI/CD:\n- Авторизация во встроенном реестре выполняется автоматически через предопределенные переменные `$CI_REGISTRY_USER` и `$CI_REGISTRY_PASSWORD`.\n- Публикация образа происходит по адресу `$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA`.\n- Деплой в Kubernetes осуществляется с использованием инструмента `kubectl` или `helm` в контексте кластера.\n\nПеременные окружения `$KUBECONFIG` или подключение раннера в том же кластере позволяют исключить передачу паролей вручную.",
    "step_by_step": "1. Включите Container Registry в настройках проекта GitLab.\n2. В файле `.gitlab-ci.yml` создайте стадию `publish` для сборки и пуша OCI-образа через Kaniko (без root-прав).\n3. Создайте стадию `deploy` с образом `bitnami/kubectl:latest`.\n4. Обновите образ в Deployment кластера: `kubectl set image deployment/app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA`.\n5. Проконтролируйте статус развертывания через `kubectl rollout status`.",
    "code_blocks": [
      {
        "filename": ".gitlab-ci.yml",
        "lang": "yaml",
        "code": "stages:\n  - publish\n  - deploy\n\nbuild_image:\n  stage: publish\n  image:\n    name: gcr.io/kaniko-project/executor:v1.23.2-debug\n    entrypoint: [\"\"]\n  script:\n    - /kaniko/executor\n      --context \"${CI_PROJECT_DIR}\"\n      --dockerfile \"${CI_PROJECT_DIR}/Dockerfile\"\n      --destination \"${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}\"\n      --destination \"${CI_REGISTRY_IMAGE}:latest\"\n\ndeploy_k8s:\n  stage: deploy\n  image: bitnami/kubectl:1.31\n  script:\n    - kubectl set image deployment/api-server api-server=${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA} -n staging\n    - kubectl rollout status deployment/api-server -n staging --timeout=120s\n  only:\n    - main"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /app\nCOPY . .\nRUN CGO_ENABLED=0 go build -ldflags=\"-s -w\" -o /app/server .\n\nFROM alpine:3.21\nCOPY --from=builder /app/server /server\nENTRYPOINT [\"/server\"]"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\t_, _ = w.Write([]byte(\"OK\"))\n\t})\n\tfmt.Println(\"K8s microservice ready\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "Kaniko запускается в пространстве пользователя (rootless) без демона Docker. Он парсит Dockerfile, распаковывает базовую файловую систему в память/диск, компилирует Go-код и делает снапшоты изменений каждого слоя. \n\nЗатем Kaniko формирует OCI tarball и отправляет его в GitLab Container Registry по адресу `registry.gitlab.com`. При деплое `kubectl` отправляет PATCH-запрос в K8s API сервер, который обновляет `spec.template.spec.containers[0].image`, и Kubelet начинает rolling update.",
    "pitfalls": "1. Использование Docker-in-Docker на Kubernetes раннере без настроенного TLS/Certificates: ошибки соединения демона.\n2. Отсутствие таймаута на `kubectl rollout status`: при ImagePullBackOff джоба CI будет висеть до глобального таймаута GitLab (1 час).\n3. Отсутствие `imagePullSecrets`: приватный реестр GitLab Container Registry требует K8s Secret типа `docker-registry` в целевом namespace.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в enterprise Kubernetes средах предпочтительнее использовать GitOps (ArgoCD/Flux), а не прямую команду `kubectl set image` из GitLab CI?\n**Ответ:** Команда `kubectl set image` изменяет состояние кластера напрямую в рантайме, минуя Git. В результате возникает рассинхронизация (Configuration Drift): манифест в Git-репозитории по-прежнему содержит старый тег, а в кластере работает новый. Если под упадет или нода перезапустится с восстановлением из Git, K8s откатится назад. GitOps гарантирует, что любое изменение версии фиксируется коммитом в Git перед применением в кластере."
  },
  {
    "num": 45,
    "title": "GitOps триггер: автоматическое обновление манифестов в конфигурационном репозитории",
    "task": "**[GitOps trigger]**: После успешного пуша образа в registry, пайплайн должен клонировать отдельный репозиторий с Kubernetes-манифестами (Infrastructure Repo), заменить в нем тег образа на новый, сделать коммит и запушить. (Это триггер для ArgoCD).",
    "theory": "В зрелой архитектуре микросервисов репозитории разделены на два типа:\n1. **Application Repository (App Repo):** Содержит исходный код Go, юнит-тесты и Dockerfile.\n2. **Configuration Repository (GitOps/Infra Repo):** Содержит манифесты K8s, Helm-чарты или Kustomize overlays для всех окружений (`dev`, `stage`, `prod`).\n\nПайплайн в App Repo при успешной публикации OCI-образа:\n- Клонирует GitOps-репозиторий по SSH-ключу или GitHub App токену.\n- Использует утилиту `kustomize edit set image` или `yq` для обновления тега образа.\n- Создает коммит `chore: update image to sha-XXXXX` и пушит в GitOps-репозиторий.\n- ArgoCD/Flux замечает коммит в GitOps-репозитории и синхронизирует кластер.",
    "step_by_step": "1. Создайте deploy key или Personal Access Token с правами записи в GitOps-репозиторий.\n2. В пайплайне App Repo после сборки добавьте шаг клонирования `config-repo`.\n3. Установите `kustomize`.\n4. Обновите тег образа: `kustomize edit set image api-service=ghcr.io/org/app:${{ github.sha }}`.\n5. Закоммитьте и запушите изменение от имени бота `ci-bot`.",
    "code_blocks": [
      {
        "filename": ".github/workflows/gitops-trigger.yml",
        "lang": "yaml",
        "code": "name: Update GitOps Repository\n\non:\n  push:\n    branches: [ main ]\n\njobs:\n  publish-and-notify-gitops:\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout Source Code\n        uses: actions/checkout@v4\n\n      - name: Build and Push Docker Image\n        run: |\n          echo \"Building and pushing ghcr.io/company/auth-service:${{ github.sha }}...\"\n\n      - name: Checkout GitOps Infrastructure Repo\n        uses: actions/checkout@v4\n        with:\n          repository: company/gitops-manifests\n          token: ${{ secrets.GITOPS_REPO_PAT }}\n          path: gitops-manifests\n\n      - name: Update Image Tag via Kustomize\n        run: |\n          cd gitops-manifests/apps/auth-service/overlays/production\n          curl -s \"https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh\" | bash\n          ./kustomize edit set image auth-service=ghcr.io/company/auth-service:${{ github.sha }}\n\n      - name: Commit and Push Changes to GitOps\n        run: |\n          cd gitops-manifests\n          git config user.name \"gitops-bot\"\n          git config user.email \"gitops-bot@company.com\"\n          git add .\n          git commit -m \"chore(release): update auth-service to commit ${{ github.sha }}\"\n          git push origin main"
      },
      {
        "filename": "kustomization.yaml",
        "lang": "yaml",
        "code": "apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\nresources:\n  - ../../base\nimages:\n  - name: auth-service\n    newName: ghcr.io/company/auth-service\n    newTag: a1b2c3d4e5"
      }
    ],
    "under_the_hood": "`kustomize edit set image` не просто перезаписывает строку regex-заменой, а безопасно парсит AST YAML-файла `kustomization.yaml` и обновляет поля `newName` и `newTag`. \n\nЭто исключает повреждение структуры файла или форматирования комментариев. При пуше коммита в GitOps-репозиторий ArgoCD считывает обновленный тег через вебхук и запускает накатку изменений в Kubernetes.",
    "pitfalls": "1. Использование команды `sed -i` для правки YAML: случайное изменение других полей или повреждение отступов ломает манифест. Всегда используйте `kustomize` или `yq`.\n2. Конфликты одновременных коммитов: если 5 микросервисов параллельно обновляют один GitOps-репозиторий, `git push` упадет с конфликтом. Требуется `git pull --rebase` перед коммитом или разнесение сервисов по разным репозиториям.\n3. Отсутствие защиты от коммитов с упавшими сборками: шаг обновления GitOps должен строго зависеть от успешного завершения всех тестов.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему монорепозиторий конфигураций для GitOps часто разделяют по веткам или каталогам для разных сред (Dev/Stage/Prod)?\n**Ответ:** Разделение по веткам (`branch-per-environment`) считается антипаттерном в GitOps из-за конфликтов слияния при мердже веток между средами. \nЛучшая мировая практика — **разграничение по каталогам (Directory/Overlay-per-environment)** в рамках единой ветки `main`: `apps/auth/overlays/dev`, `apps/auth/overlays/prod`. Это позволяет использовать Kustomize для наследования базовых манифестов и изолированно управлять конфигурациями контуров без риска случайного перезатирания настроек при Git Merge."
  },
  {
    "num": 46,
    "title": "Интеграционное тестирование с базой данных через Service Containers в GitHub Actions",
    "task": "**Интеграционные тесты в CI (Service Containers)**: Твои тесты требуют реального Redis. В GitHub Actions настрой *Service Container* с Redis. Пайплайн должен поднять контейнер с редисом, выполнить твои интеграционные `go test`, а затем убить контейнер.",
    "theory": "Мокирование баз данных (sqlmock, miniredis) полезно для юнит-тестов, но не способно проверить реальное поведение сложных SQL-запросов, транзакций, блокировок, Lua-скриптов и индексов.\n\nGitHub Actions поддерживает **Service Containers (`services:`)**:\n- Дополнительные контейнеры (PostgreSQL, Redis, Kafka), запускаемые параллельно с основной джобой на том же хосте.\n- Доступны по локальной сети (`localhost:<port>`).\n- Оснащены механизмом **Healthcheck (`options: --health-cmd ...`)**, гарантирующим, что тесты Go не стартуют раньше, чем СУБД будет готова принимать соединения.",
    "step_by_step": "1. В workflow добавьте блок `services.redis` с образом `redis:7-alpine`.\n2. Настройте healthcheck через `redis-cli ping`.\n3. Задайте проброс портов `ports: - 6379:6379`.\n4. В коде Go инициализируйте клиент Redis по адресу `localhost:6379`.\n5. Запустите тесты `go test -v ./...` и убедитесь в успешной записи и чтении ключей.",
    "code_blocks": [
      {
        "filename": ".github/workflows/integration.yml",
        "lang": "yaml",
        "code": "name: Integration Tests with Real Services\n\non:\n  push:\n    branches: [ main ]\n  pull_request:\n    branches: [ main ]\n\njobs:\n  integration-tests:\n    name: Redis Integration Tests\n    runs-on: ubuntu-latest\n\n    services:\n      redis:\n        image: redis:7-alpine\n        ports:\n          - 6379:6379\n        options: >-\n          --health-cmd \"redis-cli ping\"\n          --health-interval 5s\n          --health-timeout 2s\n          --health-retries 5\n\n    steps:\n      - name: Checkout Code\n        uses: actions/checkout@v4\n\n      - name: Setup Go\n        uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n\n      - name: Run Integration Tests\n        env:\n          REDIS_ADDR: localhost:6379\n        run: go test -v -race ./..."
      },
      {
        "filename": "cache.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"strings\"\n\t\"time\"\n)\n\n// SimpleRedisClient реализует базовый обмен по протоколу RESP.\ntype SimpleRedisClient struct {\n\taddr string\n}\n\nfunc NewSimpleRedisClient(addr string) *SimpleRedisClient {\n\treturn &SimpleRedisClient{addr: addr}\n}\n\n// Ping проверяет доступность Redis сервера.\nfunc (c *SimpleRedisClient) Ping(ctx context.Context) (string, error) {\n\tvar d net.Dialer\n\tconn, err := d.DialContext(ctx, \"tcp\", c.addr)\n\tif err != nil {\n\t\treturn \"\", fmt.Errorf(\"ошибка подключения к redis: %w\", err)\n\t}\n\tdefer conn.Close()\n\n\t_, err = conn.Write([]byte(\"*1\\r\\n$4\\r\\nPING\\r\\n\"))\n\tif err != nil {\n\t\treturn \"\", err\n\t}\n\n\tbuf := make([]byte, 128)\n\tn, err := conn.Read(buf)\n\tif err != nil {\n\t\treturn \"\", err\n\t}\n\n\tres := strings.TrimSpace(string(buf[:n]))\n\treturn res, nil\n}\n\nfunc main() {\n\tclient := NewSimpleRedisClient(\"localhost:6379\")\n\tctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)\n\tdefer cancel()\n\n\tpong, err := client.Ping(ctx)\n\tif err != nil {\n\t\tfmt.Printf(\"Ошибка Redis: %v\\n\", err)\n\t\treturn\n\t}\n\tfmt.Printf(\"Ответ Redis: %s\\n\", pong)\n}"
      },
      {
        "filename": "cache_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"os\"\n\t\"testing\"\n\t\"time\"\n)\n\nfunc TestRedisConnection(t *testing.T) {\n\taddr := os.Getenv(\"REDIS_ADDR\")\n\tif addr == \"\" {\n\t\taddr = \"localhost:6379\"\n\t}\n\n\tclient := NewSimpleRedisClient(addr)\n\tctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)\n\tdefer cancel()\n\n\tpong, err := client.Ping(ctx)\n\tif err != nil {\n\t\tt.Fatalf(\"Ping failed: %v\", err)\n\t}\n\n\tif pong != \"+PONG\" {\n\t\tt.Fatalf(\"Expected +PONG, got %q\", pong)\n\t}\n}"
      }
    ],
    "under_the_hood": "GitHub Actions запускает сервисные контейнеры через команду `docker run` в общей Docker-сети. Раннер периодически выполняет команду проверки здоровья `--health-cmd`. \n\nОсновная джоба раннера ожидает, пока контейнер сервиса перейдет в статус `healthy`. Если контейнер не успел подняться за отведенное время (`health-retries * health-interval`), джоба аварийно завершается до запуска Go-тестов, предотвращая ложные падения.",
    "pitfalls": "1. Забытый healthcheck: тесты стартуют через 200 мс после создания контейнера, когда СУБД еще инициализирует свои внутренние файлы, и падают с `connection refused`.\n2. Жестко зашитый порт или адрес: если тесты запускаются внутри контейнера раннера (container-based job), обращаться нужно не к `localhost`, а к имени сервиса `redis:6379`.\n3. Утечки соединений в тестах без закрытия `defer conn.Close()`: исчерпание пула сокетов раннера.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между запуском баз данных через `services:` в GitHub Actions и использованием библиотеки `testcontainers-go` в коде тестов?\n**Ответ:** \n- **`services:`** конфигурируется на уровне YAML. База поднимается один раз на весь прогон джобы. Это быстро, но требует ручной очистки данных между тестами и привязывает код к конкретной CI-системе.\n- **`testcontainers-go`** поднимает Docker-контейнеры программно прямо из кода Go (`testing.M` или `TestMain`). Это обеспечивает 100% идентичность локального запуска на ноутбуке разработчика и в любой CI (GitLab, GitHub, Jenkins), а также изолированное окружение для каждого отдельного тест-сьюта."
  },
  {
    "num": 47,
    "title": "Автоматические релизы с GoReleaser: генерация бинарников, контрольных сумм и GitHub Release",
    "task": "**Автоматические релизы (GoReleaser)**: Установи утилиту `GoReleaser`. Создай файл `.goreleaser.yaml`. Настрой GitHub Action, который срабатывает только при пуше Git-тега (например, `v1.0.0`). GoReleaser автоматически скомпилирует бинарники под Windows, Linux, macOS, запакует их в архивы и прикрепит к релизу на GitHub.",
    "theory": "Повторение и закрепление практики автоматизации сборки релизов с помощью **GoReleaser**:\n- Инструмент автоматизирует компиляцию под популярные платформы (Linux x86/ARM, macOS Intel/Apple Silicon, Windows).\n- Генерирует криптографический файл контрольных сумм `checksums.txt` (алгоритм SHA-256).\n- Генерирует файл описания релиза на базе истории Git (`Conventional Commits`).\n- Прикрепляет все скомпилированные архивы к странице релиза в GitHub.\n\nДля работы требуется настроить файл `.goreleaser.yaml` в корне репозитория и передать токен `GITHUB_TOKEN` с правами записи.",
    "step_by_step": "1. Установите GoReleaser локально: `go install github.com/goreleaser/goreleaser/v2@latest`.\n2. Создайте файл `.goreleaser.yaml` с помощью команды `goreleaser init`.\n3. Настройте конфигурацию компиляции `builds` и архивов `archives`.\n4. Создайте GitHub Actions workflow `.github/workflows/goreleaser.yml`, срабатывающий на теги `v*`.\n5. Протестируйте локальный запуск без публикации: `goreleaser release --snapshot --clean`.",
    "code_blocks": [
      {
        "filename": ".goreleaser.yaml",
        "lang": "yaml",
        "code": "version: 2\n\nproject_name: go-worker\n\nbefore:\n  hooks:\n    - go mod tidy\n\nbuilds:\n  - id: worker\n    binary: go-worker\n    env:\n      - CGO_ENABLED=0\n    goos:\n      - linux\n      - darwin\n      - windows\n    goarch:\n      - amd64\n      - arm64\n    ldflags:\n      - -s -w -X main.version={{.Version}}\n\narchives:\n  - format: tar.gz\n    name_template: \"{{ .ProjectName }}_{{ .Version }}_{{ .Os }}_{{ .Arch }}\"\n    format_overrides:\n      - goos: windows\n        format: zip\n\nchecksum:\n  name_template: \"checksums.txt\"\n  algorithm: sha256\n\nchangelog:\n  sort: asc\n  use: github"
      },
      {
        "filename": ".github/workflows/goreleaser.yml",
        "lang": "yaml",
        "code": "name: Automated Releases with GoReleaser\n\non:\n  push:\n    tags:\n      - 'v*.*.*'\n\npermissions:\n  contents: write\n\njobs:\n  release:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n        with:\n          fetch-depth: 0\n\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n\n      - name: Run GoReleaser\n        uses: goreleaser/goreleaser-action@v5\n        with:\n          distribution: goreleaser\n          version: latest\n          args: release --clean\n        env:\n          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\nvar version = \"dev\"\n\nfunc main() {\n\tfmt.Printf(\"Worker daemon version: %s\\n\", version)\n}"
      }
    ],
    "under_the_hood": "GoReleaser запускает процесс компиляции для матрицы целевых архитектур. Для каждой пары `GOOS/GOARCH` вызывается компилятор Go. \n\nЗатем создаются gzip-архивы и вычисляются дайджесты SHA-256 каждого файла. GoReleaser вызывает GitHub Releases API (`POST /repos/:owner/:repo/releases`), создает драфт релиза, выгружает каждый бинарник через Multipart Upload и публикует релиз.",
    "pitfalls": "1. Забытый флаг `--clean`: если каталог `dist` уже существует от предыдущей сборки, GoReleaser завершится с ошибкой.\n2. Неполная история коммитов: отсутствие `fetch-depth: 0` приводит к невозможности генерации списка изменений.\n3. Отсутствие обработки CGO: если CGO включен, кросс-компиляция завершится ошибкой компилятора GCC.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему контрольные суммы `checksums.txt` должны проверяться пользователем перед запуском бинарников?\n**Ответ:** Это защищает от атак Man-in-the-Middle и повреждения файлов при скачивании. Сверив вычисленный локально хэш файла (`sha256sum -c checksums.txt`) со значением в релизе, пользователь гарантирует, что скачанный файл в точности совпадает с артефактом, скомпилированным в доверенном CI-конвейере."
  },
  {
    "num": 48,
    "title": "Учебный деплой по SSH: автоматизация запуска через docker compose на удаленном сервере",
    "task": "**Simple CD (Deploy via SSH)**: *Учебный деплой.* Добавь шаг, который с помощью SSH-ключа логинится на твой удаленный сервер (VPS), делает `docker pull` нового образа, останавливает старый контейнер и запускает новый.",
    "theory": "Для простых учебных проектов, пет-проектов и небольших сервисов развертывание полноценного кластера Kubernetes часто избыточно. В таких сценариях применяется классический деплой по SSH на выделенный VPS/VDS сервер.\n\nБезопасная архитектура деплоя по SSH:\n1. Выделенный приватный SSH-ключ (`SSH_PRIVATE_KEY`) добавляется в GitHub Secrets.\n2. На сервере создается отдельный непривилегированный пользователь `deployer`, входящий в группу `docker`.\n3. В CI-пайплайне запускается SSH-агент (`webfactory/ssh-agent` или нативная команда `ssh`).\n4. По SSH на сервер передается обновленный файл `docker-compose.yml`, после чего выполняется команда:\n   `docker compose pull && docker compose up -d --remove-orphans`.",
    "step_by_step": "1. Сгенерируйте пару SSH-ключей: `ssh-keygen -t ed25519 -C \"ci-deploy\"`.\n2. Добавьте публичный ключ на сервер в `~/.ssh/authorized_keys`, а приватный — в GitHub Secrets `SSH_KEY`.\n3. Добавьте адрес сервера в секрет `SERVER_HOST` и пользователя в `SERVER_USER`.\n4. Настройте workflow с шагами: настройка SSH, копирование конфига через `scp`, выполнение `docker compose up -d` через `ssh`.\n5. Проверьте запуск контейнера на удаленном сервере.",
    "code_blocks": [
      {
        "filename": ".github/workflows/ssh-deploy.yml",
        "lang": "yaml",
        "code": "name: Simple SSH Deploy\n\non:\n  push:\n    branches: [ main ]\n\njobs:\n  deploy:\n    name: Deploy to Remote VPS\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - name: Setup SSH Agent\n        uses: webfactory/ssh-agent@v0.9.0\n        with:\n          ssh-private-key: ${{ secrets.SSH_KEY }}\n\n      - name: Add Known Hosts\n        run: |\n          mkdir -p ~/.ssh\n          ssh-keyscan -H ${{ secrets.SERVER_HOST }} >> ~/.ssh/known_hosts\n\n      - name: Copy Compose Config to Server\n        run: |\n          scp docker-compose.prod.yml ${{ secrets.SERVER_USER }}@${{ secrets.SERVER_HOST }}:/opt/app/docker-compose.yml\n\n      - name: Pull and Restart Application\n        run: |\n          ssh ${{ secrets.SERVER_USER }}@${{ secrets.SERVER_HOST }} \"cd /opt/app && docker compose pull && docker compose up -d --remove-orphans\" "
      },
      {
        "filename": "docker-compose.prod.yml",
        "lang": "yaml",
        "code": "services:\n  web:\n    image: ghcr.io/company/web-app:latest\n    restart: always\n    ports:\n      - \"80:8080\"\n    environment:\n      - APP_ENV=production"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\t_, _ = w.Write([]byte(\"Привет из продакшна, развернутого по SSH!\"))\n\t})\n\n\tport := os.Getenv(\"PORT\")\n\tif port == \"\" {\n\t\tport = \"8080\"\n\t}\n\tfmt.Printf(\"Сервер запущен на :%s\\n\", port)\n\t_ = http.ListenAndServe(\":\"+port, nil)\n}"
      }
    ],
    "under_the_hood": "Экшен `webfactory/ssh-agent` запускает процесс `ssh-agent` в памяти раннера и регистрирует приватный ключ через `ssh-add`. \n\nКоманда `ssh-keyscan` опрашивает открытый публичный ключ хоста сервера и заносит его отпечаток (fingerprint) в `~/.ssh/known_hosts`, предотвращая блокировку SSH-клиента диалоговым запросом `Are you sure you want to continue connecting (yes/no)?`.",
    "pitfalls": "1. Использование root-пользователя для SSH-деплоя: уязвимость в скрипте CI может привести к полному удалению ОС сервера (`rm -rf /`).\n2. Отсутствие `known_hosts`: использование флага `-o StrictHostKeyChecking=no` делает пайплайн уязвимым для MITM-перехвата SSH-сессии.\n3. Простой приложения (Downtime) при перезапуске `docker compose up -d`: без обратного прокси (Nginx/Traefik) происходит кратковременный сброс соединений.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в production BigTech инфраструктуре категорически запрещен деплой по прямому SSH из CI-пайплайна?\n**Ответ:** \n1. **Пробивание сетевого периметра:** Прямой SSH требует открытия 22 порта наружу в публичный интернет или создания туннелей, что запрещено политиками информационной безопасности (Zero Trust).\n2. **Отсутствие аудита и масштабируемости:** SSH не масштабируется на парк из 10 000 серверов; сбой на одном хосте оставляет систему в неконсистентном состоянии.\n3. **Хранение долгоживущих SSH-ключей в CI:** Утечка ключа дает злоумышленнику доступ к интерактивной shell-сессии на сервере. Вместо SSH используются декларативные контроллеры (K8s/Nomad/GitOps)."
  },
  {
    "num": 49,
    "title": "Настройка Branch Protection Rules: обязательные Status Checks и код-ревью",
    "task": "**Branch Protection**: Настрой репозиторий (в UI GitHub/GitLab). Запрети прямой пуш в ветку `main`. Обяжи делать Pull Requests, и поставь галочку: \"Слить код можно только если CI-пайплайн (линтер и тесты) пройден успешно\".\n\n---",
    "theory": "Защита главной ветки (`main`/`master`) — фундаментальное правило разработки в любой IT-компании. Прямой коммит или push в `main` («Push to master») категорически блокируется на уровне настроек репозитория.\n\nКлючевые политики **Branch Protection Rules (GitHub / GitLab)**:\n1. **Require a pull request before merging:** Весь код поступает в `main` исключительно через Pull Request / Merge Request.\n2. **Require approvals:** Обязательное подтверждение PR минимум одним или двумя коллегами (Peer Code Review).\n3. **Require status checks to pass before merging:** Слияние заблокировано, пока не завершатся зеленым все критические джобы CI:\n   - `test` (юнит-тесты и детектор гонок),\n   - `golangci-lint` (статический анализ),\n   - `security-scan` (поиск уязвимостей).\n4. **Require branches to be up to date before merging:** Гарантирует, что PR протестирован на актуальной версии ветки `main`.",
    "step_by_step": "1. В репозитории GitHub перейдите в Settings -> Branches -> Add branch protection rule.\n2. В поле Branch name pattern укажите `main`.\n3. Отметьте чекбокс `Require a pull request before merging` (минимум 1 approval).\n4. Отметьте `Require status checks to pass before merging`.\n5. В строке поиска найдите точные имена джобов вашего workflow (например, `test`, `lint`).\n6. Включите `Do not allow bypassing the above settings` (применять правила даже к администраторам).",
    "code_blocks": [
      {
        "filename": ".github/workflows/mandatory-checks.yml",
        "lang": "yaml",
        "code": "name: Mandatory Branch Protection Checks\n\non:\n  pull_request:\n    branches: [ main ]\n\njobs:\n  lint:\n    name: Mandatory Linter\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n      - name: Run golangci-lint\n        uses: golangci/golangci-lint-action@v6\n        with:\n          version: v1.64.5\n\n  test:\n    name: Mandatory Unit Tests\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n      - name: Run Tests with Race Detector\n        run: go test -v -race -cover ./..."
      },
      {
        "filename": "service.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n)\n\n// CalculateDiscount вычисляет размер скидки для клиента.\nfunc CalculateDiscount(total float64, isVIP bool) (float64, error) {\n\tif total < 0 {\n\t\treturn 0, errors.New(\"сумма не может быть отрицательной\")\n\t}\n\tif isVIP {\n\t\treturn total * 0.20, nil\n\t}\n\treturn total * 0.05, nil\n}\n\nfunc main() {\n\tdiscount, _ := CalculateDiscount(1000, true)\n\tfmt.Printf(\"Размер скидки: %.2f руб.\\n\", discount)\n}"
      },
      {
        "filename": "service_test.go",
        "lang": "go",
        "code": "package main\n\nimport \"testing\"\n\nfunc TestCalculateDiscount(t *testing.T) {\n\td, err := CalculateDiscount(100, true)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка: %v\", err)\n\t}\n\tif d != 20.0 {\n\t\tt.Fatalf(\"Ожидалось 20.0, получено %.2f\", d)\n\t}\n}"
      }
    ],
    "under_the_hood": "Когда PR создается, GitHub связывает коммит PR с объектом Commit Status API (`POST /repos/:owner/:repo/statuses/:sha`). \n\nКаждая джоба GitHub Actions отправляет обновления статуса: `state: pending`, затем `state: success` или `state: failure`. \n\nКнопка «Merge pull request» в веб-интерфейсе GitHub программно заблокирована на уровне API, пока все контексты статусов, зарегистрированные в правилах Branch Protection, не перейдут в статус `success`.",
    "pitfalls": "1. Несовпадение имен статусов: если переименовать `name:` у джобы в YAML-файле, GitHub будет бесконечно ждать статуса со старым именем, блокируя слияние PR.\n2. Исключение администраторов из правил: лид команды в спешке может случайно запушить ломающий коммит напрямую в `main`.\n3. Отсутствие `Dismiss stale pull request approvals when new commits are pushed`: если автор запушит новые изменения после получения аппрува, они попадут в `main` без повторного ревью.",
    "bigtech_interview": "**Вопрос с собеседования:** Что такое «Merge Queue» (Очередь слияния) в GitHub и какую проблему она решает в высоконагруженных монорепозиториях?\n**Ответ:** Когда сотни разработчиков одновременно мерджат PR в `main`, возникает проблема: PR A и PR B по отдельности проходят все тесты на своей ветке, но при одновременном слиянии их изменения конфликтуют на уровне бизнес-логики, ломая `main`. \nMerge Queue автоматически выстраивает одобренные PR в очередь, применяет их последовательно на временной ветке, прогоняет тесты для каждого объединенного состояния и только при успехе сливает в `main`. Если чей-то PR ломает билд, он автоматически выбрасывается из очереди без остановки работы остальных коллег."
  },
  {
    "num": 50,
    "title": "Автоматический линтинг в CI: проверка go vet и golangci-lint",
    "task": "**Автоматический линтинг в CI**: Напишите пайплайн сборки для GitHub Actions в файле `.github/workflows/ci.yml`. Настройте первый шаг: при каждом пуше кода в репозиторий автоматически должен запускаться строгий линтер `golangci-lint` с использованием официального готового экшена `golangci/golangci-lint-action` [470].",
    "theory": "Линтинг в CI должен быть быстрым, всеобъемлющим и предотвращать появление ошибок еще до этапа компиляции тяжелых бинарников.\n\nКомбинация инструментов:\n1. **`go vet`:** Официальный статический анализатор компилятора Go. Проверяет критические ошибки: некорректные строки форматирования `Printf`, подозрительные булевы выражения, блокировки мьютексов.\n2. **`golangci-lint`:** Мета-линтер, объединяющий десятки статических анализаторов. Выполняет углубленный анализ типов, неиспользуемых переменных и стилистики.\n\nВключение линтинга в пайплайн GitHub Actions с автоматическим падением при малейших замечаниях гарантирует высокое качество кодовой базы.",
    "step_by_step": "1. Создайте `.github/workflows/lint.yml`.\n2. Настройте запуск на `push` и `pull_request`.\n3. Добавьте шаг выполнения `go vet ./...`.\n4. Добавьте шаг выполнения `golangci/golangci-lint-action@v6`.\n5. Убедитесь, что ошибки форматирования или статического анализа приводят к падению джобы.",
    "code_blocks": [
      {
        "filename": ".github/workflows/lint.yml",
        "lang": "yaml",
        "code": "name: Automated Linting Pipeline\n\non:\n  push:\n    branches: [ main ]\n  pull_request:\n    branches: [ main ]\n\njobs:\n  lint:\n    name: Run Linters\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout Code\n        uses: actions/checkout@v4\n\n      - name: Setup Go\n        uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n\n      - name: Run Go Vet\n        run: go vet ./...\n\n      - name: Run golangci-lint\n        uses: golangci/golangci-lint-action@v6\n        with:\n          version: v1.64.5\n          args: --timeout=5m"
      },
      {
        "filename": "math_helper.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\n// Multiply перемножает два целых числа.\nfunc Multiply(a, b int) int {\n\treturn a * b\n}\n\nfunc main() {\n\tresult := Multiply(6, 7)\n\tfmt.Printf(\"Результат умножения: %d\\n\", result)\n}"
      }
    ],
    "under_the_hood": "`go vet` использует встроенный компиляторный фреймворк `golang.org/x/tools/go/analysis`. Анализатор строит абстрактное синтаксическое дерево (AST) и инспектирует факты (Analysis Facts). \n\n`golangci-lint` запускает этот анализ в параллельных потоках горутин, переиспользуя единый загруженный кэш пакетов `go/packages`, что делает его работу в несколько раз быстрее поочередного вызова отдельных утилит.",
    "pitfalls": "1. Запуск линтера без скачивания зависимостей: линтер упадет с ошибкой `cannot find package`. Экшен `setup-go` или `golangci-lint-action` берут заботу об этом на себя.\n2. Игнорирование кода возврата: использование конструкций вроде `golangci-lint run || true` маскирует ошибки и обессмысливает CI.\n3. Слишком короткий таймаут: в больших монорепозиториях дефолтного таймаута в 1 минуту может не хватить на холодный прогон.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между синтаксическими ошибками (Syntax Errors) и семантическими ошибками, выявляемыми `go vet`?\n**Ответ:** \n- Синтаксические ошибки не позволяют компилятору собрать исходный код в AST (например, пропущенная закрывающая фигурная скобка или опечатка в ключевом слове `func`). \n- Семантические ошибки синтаксически абсолютно валидны, но содержат логический баг или антипаттерн (например, передача `fmt.Printf(\"%d\", \"строка\")` — программа скомпилируется, но упадет или выведет `%!d(string=...)` в runtime). `go vet` находит именно такие скрытые дефекты."
  },
  {
    "num": 51,
    "title": "Тестирование и эффективное кэширование Go-зависимостей в CI",
    "task": "**Тестирование и кэширование зависимостей**: Добавьте в ваш пайплайн CI шаг автоматического запуска тестов `go test -v ./...` [471]. Чтобы не скачивать заново все внешние библиотеки при каждом запуске CI (что сильно замедляет сборку), настройте кэширование папок `~/.cache/go-build` и `~/go/pkg/mod` в вашем CI-пайплайне [471].",
    "theory": "Запуск тестов — центральный этап проверки бизнес-логики. Для ускорения времени выполнения пайплайна критично кэшировать скачанные модули Go.\n\nЭволюция кэширования в GitHub Actions:\n- Ранее использовался экшен `actions/cache` с ручным указанием путей `~/go/pkg/mod` и ключей хешей `go.sum`.\n- В современном `actions/setup-go@v5` кэширование встроено из коробки: параметр `cache: true` (включен по умолчанию) автоматически кэширует как зависимости (`go mod`), так и кэш сборщика Go (`go build cache`).\n\nТестирование с флагами `-race` и `-cover` обеспечивает одновременный контроль корректности многопоточности и полноты покрытия кодовой базы.",
    "step_by_step": "1. Включите автоматический кэш в `actions/setup-go@v5` через `cache: true`.\n2. Настройте команду запуска тестов: `go test -v -race -cover ./...`.\n3. Убедитесь, что при повторном запуске пайплайна в логах появляется сообщение `Cache restored successfully`.\n4. Сравните время выполнения холодного и теплого прогона.",
    "code_blocks": [
      {
        "filename": ".github/workflows/test-cache.yml",
        "lang": "yaml",
        "code": "name: Tests with Caching\n\non:\n  push:\n    branches: [ main ]\n  pull_request:\n    branches: [ main ]\n\njobs:\n  test:\n    name: Run Unit Tests\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout Code\n        uses: actions/checkout@v4\n\n      - name: Setup Go with Built-in Cache\n        uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n          cache: true\n          cache-dependency-path: go.sum\n\n      - name: Run Tests\n        run: go test -v -race -cover ./..."
      },
      {
        "filename": "string_utils.go",
        "lang": "go",
        "code": "package main\n\nimport \"strings\"\n\n// Reverse переворачивает строку с учетом Unicode рун.\nfunc Reverse(s string) string {\n\trunes := []rune(s)\n\tfor i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {\n\t\trunes[i], runes[j] = runes[j], runes[i]\n\t}\n\treturn string(runes)\n}\n\nfunc main() {\n\tprintln(Reverse(\"Привет, Go!\"))\n}"
      },
      {
        "filename": "string_utils_test.go",
        "lang": "go",
        "code": "package main\n\nimport \"testing\"\n\nfunc TestReverse(t *testing.T) {\n\tcases := []struct {\n\t\tin, want string\n\t}{\n\t\t{\"Hello\", \"olleH\"},\n\t\t{\"Мир\", \"риМ\"},\n\t\t{\"\", \"\"},\n\t}\n\tfor _, c := range cases {\n\t\tgot := Reverse(c.in)\n\t\tif got != c.want {\n\t\t\tt.Errorf(\"Reverse(%q) == %q, want %q\", c.in, got, c.want)\n\t\t}\n\t}\n}"
      }
    ],
    "under_the_hood": "`actions/setup-go` при завершении джобы вычисляет SHA-256 хеш от файла `go.sum` и упаковывает директории:\n- `~/go/pkg/mod` (исходные тексты скачанных зависимостей)\n- `~/.cache/go-build` (скомпилированные объектные `.a` архивы пакетов)\nв архив tar.zst и выгружает в GitHub Cache Storage. При следующем запуске с тем же `go.sum` этот архив восстанавливается за 1-2 секунды, исключая сетевые запросы к `proxy.golang.org`.",
    "pitfalls": "1. Забытый файл `go.sum`: если `go.sum` не закоммичен в репозиторий, ключ кэша не может быть детерминирован, и кэш будет пересоздаваться на каждый коммит.\n2. Ручное удаление модулей в пайплайне: выполнение команд вроде `go clean -modcache` сводит на нет работу кэша.\n3. Кэширование папки `vendor`: если проект использует vendoring (`go mod vendor`), кэшировать `~/go/pkg/mod` не имеет смысла, так как зависимости уже лежат в Git.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между `GOCACHE` (кэш сборщика) и `GOPATH/pkg/mod` (кэш модулей) в Go?\n**Ответ:** \n- **`GOPATH/pkg/mod`** содержит скачанные из интернета неизменяемые архивы и исходные коды сторонних библиотек.\n- **`GOCACHE`** содержит скомпилированные машинные объектные файлы (`.a`), результаты работы компилятора и линковщика, а также кэшированные результаты успешных тестов (`go test` выводит `(cached)`). \nКэширование обоих каталогов в CI дает максимальный прирост скорости."
  },
  {
    "num": 52,
    "title": "Полный сквозной CI/CD конвейер: от коммита до Production с ручным подтверждением",
    "task": "Создайте полный CI/CD пайплайн: push в main → сборка образа → деплой в staging-кластер → acceptance-тесты → promotion в production (ручное подтверждение).",
    "theory": "Промышленный эталонный пайплайн CI/CD связывает воедино все стадии жизненного цикла ПО:\n1. **Lint & Test:** Параллельная проверка качества кода, линтеров и юнит-тестов.\n2. **Build OCI Image:** Сборка неизменяемого контейнера с тегированием по SHA.\n3. **Deploy to Staging:** Автоматическое развертывание в тестовый кластер.\n4. **Acceptance / E2E Tests:** Запуск сквозных функциональных тестов против развернутого Staging-окружения.\n5. **Approval Gate:** Ожидание подтверждения релиз-инженером через GitHub Environment Protection Rules.\n6. **Deploy to Production:** Развертывание проверенного образа в боевой кластер с канареечной валидацией.",
    "step_by_step": "1. Создайте `.github/workflows/full-pipeline.yml`.\n2. Опишите цепочку зависимостей через `needs: [...]`.\n3. Настройте джобы: `verify` -> `build-image` -> `deploy-staging` -> `e2e-tests` -> `deploy-production`.\n4. Для `deploy-production` укажите `environment: production`.\n5. Протестируйте прохождение конвейера со симуляцией всех этапов.",
    "code_blocks": [
      {
        "filename": ".github/workflows/full-pipeline.yml",
        "lang": "yaml",
        "code": "name: End-to-End Enterprise CI/CD\n\non:\n  push:\n    branches: [ main ]\n\njobs:\n  verify:\n    name: Quality Gate (Lint & Tests)\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n          cache: true\n      - run: go vet ./...\n      - run: go test -v -race -cover ./...\n\n  build-image:\n    name: Build & Push Image\n    needs: verify\n    runs-on: ubuntu-latest\n    outputs:\n      image_tag: ${{ steps.meta.outputs.tag }}\n    steps:\n      - uses: actions/checkout@v4\n      - id: meta\n        run: echo \"tag=ghcr.io/${{ github.repository }}:${{ github.sha }}\" >> $GITHUB_OUTPUT\n      - run: echo \"Building container with tag ${{ steps.meta.outputs.tag }}...\"\n\n  deploy-staging:\n    name: Deploy to Staging\n    needs: build-image\n    runs-on: ubuntu-latest\n    environment: staging\n    steps:\n      - run: echo \"Deploying image ${{ needs.build-image.outputs.image_tag }} to Staging K8s cluster...\"\n\n  acceptance-tests:\n    name: Run E2E Acceptance Tests\n    needs: deploy-staging\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo \"Running Newman / Cypress / Go integration tests against Staging API...\"\n\n  deploy-production:\n    name: Deploy to Production (Approval Gate)\n    needs: acceptance-tests\n    runs-on: ubuntu-latest\n    environment:\n      name: production\n      url: https://api.production.company.com\n    steps:\n      - run: echo \"Deploying verified image ${{ needs.build-image.outputs.image_tag }} to Production cluster!\" "
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/api/v1/health\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\t_, _ = w.Write([]byte(`{\"status\":\"UP\",\"version\":\"2.4.0\"}`))\n\t})\n\tfmt.Println(\"Production API Server starting...\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "Граф выполнения GitHub Actions связывает джобы через `needs`. Выходные переменные (`outputs`) передаются между джобами через контекст `${{ needs.<job_id>.outputs.<name> }}`. \n\nНа шаге `deploy-production` рантайм GitHub ставит джобу на паузу до тех пор, пока назначенные в настройках окружения ревьюеры не подтвердят запуск через веб-интерфейс или мобильное приложение GitHub.",
    "pitfalls": "1. Запуск E2E тестов параллельно с деплоем на Staging вместо использования `needs: [deploy-staging]`: тесты начнут стучаться в еще не обновившийся сервис.\n2. Пересборка контейнера перед деплоем в Production: в прод должен идти строго тот же тег образа, который прошел Staging и E2E тесты.\n3. Отсутствие мониторинга метрик после деплоя в Production.",
    "bigtech_interview": "**Вопрос с собеседования:** Что такое «Rollback Strategy» и как организовать моментальный откат продакшна при сбое в рамках сквозного CI/CD конвейера?\n**Ответ:** \n1. **На уровне GitOps:** Откат выполняется простым коммитом `git revert <commit_hash>` в репозиторий манифестов; ArgoCD мгновенно возвращает предыдущую версию образа.\n2. **На уровне Kubernetes:** Вызов `kubectl rollout undo deployment/<name>`.\n3. **На уровне Argo Rollouts:** Автоматический откат на основе `AnalysisTemplate` при превышении процента ошибок в Prometheus. \nГлавное правило: никогда не чинить production «вперед» новым спешным коммитом с коленки (Hotfix), а сначала мгновенно откатить трафик на гарантированно рабочую предыдущую версию."
  },
  {
    "num": 53,
    "title": "Сборка и публикация образа в реестр: GHCR и Docker Hub с семантическими тегами",
    "task": "**Сборка и публикация образа в реестр (Registry)**: Напишите шаг CI, который при успешном прохождении тестов собирает Docker-образ вашего приложения с помощью вашего многоэтапного `Dockerfile`. Настройте авторизацию пайплайна в реестре (например, GitHub Container Registry — GHCR или Docker Hub) и опубликуйте собранный образ, автоматически выставив ему тег, равный SHA-хэшу текущего коммита Git [472].",
    "theory": "Публикация контейнерных артефактов в промышленный реестр (Registry) требует соблюдения строгих практик тегирования:\n- **`latest`:** Тег для локальных экспериментов разработчиков.\n- **Git SHA (`sha-xxxxxxx`):** Уникальный идентификатор коммита, обеспечивающий 100% повторяемость.\n- **SemVer теги (`1.2.3`, `1.2`, `1`):** Официальные стабильные версии, генерируемые экшеном `docker/metadata-action`.\n\nЭкшен `docker/build-push-action` обеспечивает безопасную сборку без сохранения промежуточных паролей на диске раннера.",
    "step_by_step": "1. Предоставьте права `permissions: packages: write, contents: read`.\n2. Авторизуйтесь в реестре через `docker/login-action`.\n3. Используйте `docker/metadata-action` для автоматической генерации набора тегов.\n4. Выполните сборку и публикацию через `docker/build-push-action`.\n5. Проверьте опубликованные теги в веб-интерфейсе реестра.",
    "code_blocks": [
      {
        "filename": ".github/workflows/publish-registry.yml",
        "lang": "yaml",
        "code": "name: Publish OCI Artifacts\n\non:\n  push:\n    branches: [ main ]\n    tags: [ 'v*.*.*' ]\n\npermissions:\n  contents: read\n  packages: write\n\njobs:\n  build-and-push:\n    name: Build & Push OCI Image\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout\n        uses: actions/checkout@v4\n\n      - name: Setup Buildx\n        uses: docker/setup-buildx-action@v3\n\n      - name: Login to GitHub Container Registry\n        uses: docker/login-action@v3\n        with:\n          registry: ghcr.io\n          username: ${{ github.actor }}\n          password: ${{ secrets.GITHUB_TOKEN }}\n\n      - name: Generate Smart Docker Metadata\n        id: meta\n        uses: docker/metadata-action@v5\n        with:\n          images: ghcr.io/${{ github.repository }}\n          tags: |\n            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}\n            type=sha,format=short,prefix=sha-\n            type=semver,pattern={{version}}\n            type=semver,pattern={{major}}.{{minor}}\n\n      - name: Build & Push\n        uses: docker/build-push-action@v5\n        with:\n          context: .\n          push: true\n          tags: ${{ steps.meta.outputs.tags }}\n          labels: ${{ steps.meta.outputs.labels }}"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "FROM golang:1.24-alpine AS builder\nWORKDIR /src\nCOPY . .\nRUN CGO_ENABLED=0 go build -ldflags=\"-s -w\" -o /bin/app .\n\nFROM alpine:3.21\nCOPY --from=builder /bin/app /app\nENTRYPOINT [\"/app\"]"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\nfunc main() {\n\tfmt.Println(\"Registry Publisher Service v1.0.0\")\n}"
      }
    ],
    "under_the_hood": "`docker/metadata-action` анализирует событие Git. Если событием был пуш тега `v1.2.3`, он генерирует сразу три тега: `1.2.3`, `1.2` и `1`. \n\nКогда `docker/build-push-action` пушит эти теги, BuildKit отправляет слои данных один раз, связывая три OCI-манифеста с одним и тем же набором слоев.",
    "pitfalls": "1. Использование верхнего регистра в названии репозитория: `ghcr.io/MyOrg/App` приведет к ошибке реестра `invalid reference format`.\n2. Запуск сборки с `push: true` на Pull Request из внешнего форка.\n3. Отсутствие файла `.dockerignore`: попадание папки `.git`, локальных бинарников и временных файлов в контекст сборки Docker.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в production реестрах контейнеров рекомендуется включать функцию «Immutable Tags» (Неизменяемые теги)?\n**Ответ:** По умолчанию любой OCI-тег можно перезаписать новым пушем. Если разработчик или злоумышленник случайно пересоберет и перезапишет образ `v1.2.3`, все новые поды в кластере скачают новый непротестированный код, что разрушит воспроизводимость сборок и аудит безопасности. \nФункция Immutable Tags на уровне реестра (Harbor, AWS ECR, GCP Artifact Registry) запрещает перезапись существующих тегов, гарантируя целостность выпущенных релизов."
  },
  {
    "num": 54,
    "title": "Мультиархитектурная кросс-компиляция образов с Buildx для Intel x86 и Apple Silicon",
    "task": "**Мультиархитектурные сборки (Buildx)**: Если ваши сервера работают на x86 архитектуре (Intel/AMD), а локальные компьютеры разработчиков или часть серверов — на ARM (например, Apple Silicon M1/M2), образ должен быть собран под обе архитектуры. Настройте пайплайн на использование инструмента `docker/setup-buildx-action` для сборки мультиархитектурного образа под платформы `linux/amd64` и `linux/arm64` одновременно [473].",
    "theory": "Разработчики современных IT-компаний часто работают на ноутбуках MacBook с чипами Apple Silicon (ARM64), тогда как серверные мощности и ноды Kubernetes в облаке традиционно работают на архитектуре Intel/AMD (x86_64).\n\nБез мультиархитектурной сборки возникают проблемы:\n- Образ, собранный разработчиком локально на Mac, падает в кластере с `exec format error`.\n- Образ, собранный на x86 сервере CI, не запускается локально у разработчика без медленной эмуляции.\n\nРешение: использование `docker buildx` для сборки мультиархитектурных OCI-манифестов с поддержкой платформ `linux/amd64` и `linux/arm64`.",
    "step_by_step": "1. Настройте эмуляцию QEMU через `docker/setup-qemu-action@v3`.\n2. Создайте инстанс Buildx builder через `docker/setup-buildx-action@v3`.\n3. В параметрах `docker/build-push-action` укажите платформы: `platforms: linux/amd64,linux/arm64`.\n4. Соберите и опубликуйте образ.\n5. Проинспектируйте результат через `docker buildx imagetools inspect`.",
    "code_blocks": [
      {
        "filename": ".github/workflows/buildx-matrix.yml",
        "lang": "yaml",
        "code": "name: Multi-Arch Buildx CI\n\non:\n  push:\n    branches: [ main ]\n\njobs:\n  build:\n    name: Build Multi-Arch Image\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - name: Set up QEMU\n        uses: docker/setup-qemu-action@v3\n\n      - name: Set up Docker Buildx\n        uses: docker/setup-buildx-action@v3\n\n      - name: Login to DockerHub\n        uses: docker/login-action@v3\n        with:\n          username: ${{ secrets.DOCKERHUB_USERNAME }}\n          password: ${{ secrets.DOCKERHUB_TOKEN }}\n\n      - name: Build and Push Multi-Arch\n        uses: docker/build-push-action@v5\n        with:\n          context: .\n          platforms: linux/amd64,linux/arm64\n          push: true\n          tags: ${{ secrets.DOCKERHUB_USERNAME }}/universal-app:latest"
      },
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# syntax=docker/dockerfile:1\nFROM --platform=$BUILDPLATFORM golang:1.24-alpine AS builder\nARG TARGETOS\nARG TARGETARCH\n\nWORKDIR /workspace\nCOPY go.mod ./\nCOPY . .\nRUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} go build -ldflags=\"-s -w\" -o /out/app .\n\nFROM alpine:3.21\nCOPY --from=builder /out/app /bin/app\nENTRYPOINT [\"/bin/app\"]"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n)\n\nfunc main() {\n\tfmt.Printf(\"Сервис успешно запущен! Архитектура: %s, ОС: %s\\n\", runtime.GOARCH, runtime.GOOS)\n}"
      }
    ],
    "under_the_hood": "BuildKit параллельно запускает два изолированных контейнера сборки: один с переменными `TARGETARCH=amd64`, второй — с `TARGETARCH=arm64`. \n\nПосле завершения компиляции BuildKit загружает в реестр оба независимых образа и формирует корневой `application/vnd.oci.image.index.v1+json` документ, содержащий ссылки на дайджесты обеих архитектур.",
    "pitfalls": "1. Сборка CGO-зависимостей без настройки кросс-компиляторов C: завершается ошибкой сборщика.\n2. Пропуск `platforms` при вызове `build-push-action`: соберется образ только под архитектуру раннера (обычно amd64).\n3. Попытка выполнить `docker run` локально на мультиархитектурном образе без флага `push: true`: Buildx не может загрузить мульти-индекс в локальный Docker Daemon.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему кросс-компиляция в Go (`GOOS/GOARCH`) на порядок быстрее сборки образов на C++ или Rust под несколько архитектур в CI?\n**Ответ:** Компилятор Go с самого начала проектировался как встроенный кросс-компилятор: бэкенд кодогенерации компилятора Go (`gc`) умеет компилировать код под любую поддерживаемую архитектуру (x86, ARM, MIPS, RISC-V) из одной и той же бинарной сборки без необходимости устанавливать отдельные пакеты кросс-тулчейнов и внешние библиотеки (при условии `CGO_ENABLED=0`). В C++/Rust требуется сложная настройка sysroot и отдельных тулчейнов `gcc-cross`."
  },
  {
    "num": 55,
    "title": "Безопасное управление секретами в CI/CD: маскирование, Vault и GitHub Secrets",
    "task": "**Управление секретами в CI/CD**: Представьте, что для прохождения интеграционных тестов в CI вашему приложению нужен токен доступа к стороннему сервису. Настройте передачу этого токена: добавьте его в секреты репозитория (GitHub Secrets) [474], а в пайплайне пробросьте его в тест через переменную окружения `env` [474]. Напишите комментарий о том, почему категорически запрещено коммитить реальные пароли и токены в Git-репозиторий.",
    "theory": "Утечка учетных данных (API-ключей, токенов БД, приватных ключей SSH) через логи CI/CD — одна из наиболее распространенных причин инцидентов ИБ в корпорациях.\n\nПринципы безопасного управления секретами:\n1. **GitHub Secrets:** Шифруются асимметричным ключом (libsodium sealed box) перед сохранением в базе GitHub.\n2. **Автоматическое маскирование (Secret Masking):** Значения секретов автоматически заменяются на `***` в консольных логах.\n3. **Команда `::add-mask::`:** Позволяет динамически маскировать секреты, сгенерированные или полученные в рантайме.\n4. **Внешние хранилища секретов (HashiCorp Vault):** В enterprise-системах долгоживущие секреты не хранятся в GitHub, а запрашиваются динамически через Vault OIDC JWT аутентификацию.",
    "step_by_step": "1. Добавьте секрет `DATABASE_PASSWORD` в Settings -> Secrets and variables -> Actions.\n2. В файле workflow передайте секрет в джобу через секцию `env:`.\n3. Для динамически генерируемых секретов используйте директиву `echo \"::add-mask::$DYNAMIC_SECRET\"`.\n4. Запустите тесты с чтением секрета из переменной окружения.\n5. Убедитесь, что при попытке вывода в консоль значение маскируется звездочками `***`.",
    "code_blocks": [
      {
        "filename": ".github/workflows/secrets.yml",
        "lang": "yaml",
        "code": "name: Secure Secrets Handling\n\non:\n  push:\n    branches: [ main ]\n\njobs:\n  secure-job:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - name: Setup Go\n        uses: actions/setup-go@v5\n        with:\n          go-version: '1.24'\n\n      - name: Demonstrate Dynamic Masking\n        run: |\n          TOKEN=$(openssl rand -hex 16)\n          # Регистрация динамического секрета в системе маскирования GitHub Actions:\n          echo \"::add-mask::$TOKEN\"\n          echo \"DYNAMIC_API_TOKEN=$TOKEN\" >> $GITHUB_ENV\n          echo \"Секрет сгенерирован и защищен: $TOKEN\"\n\n      - name: Run Tests with Encrypted Secrets\n        env:\n          DB_PASS: ${{ secrets.DATABASE_PASSWORD }}\n        run: |\n          go test -v ./..."
      },
      {
        "filename": "db.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n\t\"os\"\n)\n\n// ConnectDB имитирует защищенное подключение к базе данных.\nfunc ConnectDB() error {\n\tpass := os.Getenv(\"DB_PASS\")\n\tif pass == \"\" {\n\t\treturn errors.New(\"пароль базы данных не передан через окружение\")\n\t}\n\tfmt.Printf(\"Подключение к базе данных успешно установлено [Длина секрета: %d символов]\\n\", len(pass))\n\treturn nil\n}\n\nfunc main() {\n\tif err := ConnectDB(); err != nil {\n\t\tfmt.Printf(\"Ошибка: %v\\n\", err)\n\t\tos.Exit(1)\n\t}\n}"
      },
      {
        "filename": "db_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"os\"\n\t\"testing\"\n)\n\nfunc TestConnectDB(t *testing.T) {\n\t_ = os.Setenv(\"DB_PASS\", \"super_secret_ci_password_123\")\n\tdefer os.Unsetenv(\"DB_PASS\")\n\n\tif err := ConnectDB(); err != nil {\n\t\tt.Fatalf(\"ConnectDB failed: %v\", err)\n\t}\n}"
      }
    ],
    "under_the_hood": "Раннер GitHub Actions перехватывает весь поток stdout/stderr всех запускаемых команд. Движок раннера содержит таблицу зарегистрированных секретов. \n\nПеред отправкой строки лога на сервер GitHub демон раннера прогоняет текст через алгоритм поиска подстрок (Aho-Corasick) и заменяет любые точные совпадения со значениями секретов на `***`.",
    "pitfalls": "1. Вывод секретов в формате Base64 или URL-encoded: если зашифровать пароль в base64 (`echo $SECRET | base64`), раннер не распознает закодированную строку и выведет ее в открытый лог!\n2. Использование `set -x` в bash: трассировка bash может раскрыть секреты при подстановке аргументов команд.\n3. Доступность секретов в PR из форков: по умолчанию GitHub Actions не передает секреты в PR из форков репозитория для защиты от вредоносных скриптов контрибьюторов.",
    "bigtech_interview": "**Вопрос с собеседования:** Как устроен механизм OpenID Connect (OIDC) для аутентификации GitHub Actions в HashiCorp Vault или AWS/GCP без использования статических паролей?\n**Ответ:** Раннер GitHub Actions запрашивает у провайдера GitHub криптографически подписанный JSON Web Token (JWT), подтверждающий контекст сборки (репозиторий, ветку, коммит). \nЗатем раннер отправляет этот JWT в Vault или AWS STS. Облачный сервис проверяет подпись открытым ключом GitHub (`https://token.actions.githubusercontent.com`), валидирует правила доступа (например, «только ветка main репозитория company/payments») и выдает временные краткосрочные учетные данные (срок жизни 15 минут). Это полностью устраняет статические долгоживущие секреты."
  },
  {
    "num": 56,
    "title": "Platform Engineering: Self-Service портал разработчика (IDP) и автоматизация через PR",
    "task": "**Platform Engineering**: internal developer platform (IDP). Self-service: `kubectl apply` → Git PR → automated pipeline. Golden paths, paved roads. Developers focus on code, platform team on infrastructure.",
    "theory": "С ростом штата инженеров традиционная модель взаимодействия «Разработчик ставит тикет в Jira системным администраторам/DevOps на создание базы данных или развертывание сервиса» становится главным узким местом компании.\n\n**Platform Engineering** создает внутреннюю платформу разработки (**Internal Developer Platform — IDP**, например Spotify Backstage):\n- **Self-Service:** Разработчик через веб-портал или шаблонный репозиторий за 2 клика заказывает новый микросервис со всем окружением.\n- **GitOps Automation:** Платформа автоматически создает Git-репозиторий с кодом на Go, генерирует Helm-чарты, пайплайны CI/CD и создает Pull Request в репозиторий инфраструктуры.\n- **Golden Paths (Золотые пути):** Стандартизированные шаблоны сервисов со встроенным логированием, трейсингом, метриками и безопасностью.",
    "step_by_step": "1. Разработайте шаблон микросервиса на Go с преднастроенными Dockerfile, Makefile и CI-пайплайнами.\n2. Создайте GitHub Action или скрипт автоматизации, генерирующий манифесты инфраструктуры при создании нового сервиса.\n3. Настройте генерацию K8s Namespace, ResourceQuota и Deployment.\n4. Создайте автоматический Pull Request в GitOps-репозиторий кластера.\n5. Продемонстрируйте сценарий Self-Service создания сервиса.",
    "code_blocks": [
      {
        "filename": "template/scaffold.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"bytes\"\n\t\"fmt\"\n\t\"text/template\"\n)\n\ntype ServiceMetadata struct {\n\tServiceName string\n\tOwnerTeam   string\n\tPort        int\n}\n\nconst k8sTemplate = `apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: {{ .ServiceName }}\n  labels:\n    app.kubernetes.io/name: {{ .ServiceName }}\n    team: {{ .OwnerTeam }}\nspec:\n  replicas: 2\n  selector:\n    matchLabels:\n      app: {{ .ServiceName }}\n  template:\n    metadata:\n      labels:\n        app: {{ .ServiceName }}\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/{{ .ServiceName }}:latest\n          ports:\n            - containerPort: {{ .Port }}\n`\n\nfunc GenerateManifest(meta ServiceMetadata) (string, error) {\n\ttmpl, err := template.New(\"manifest\").Parse(k8sTemplate)\n\tif err != nil {\n\t\treturn \"\", err\n\t}\n\tvar buf bytes.Buffer\n\tif err := tmpl.Execute(&buf, meta); err != nil {\n\t\treturn \"\", err\n\t}\n\treturn buf.String(), nil\n}\n\nfunc main() {\n\tmeta := ServiceMetadata{\n\t\tServiceName: \"loyalty-api\",\n\t\tOwnerTeam:   \"marketing-tech\",\n\t\tPort:        8080,\n\t}\n\tmanifest, err := GenerateManifest(meta)\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tfmt.Println(\"Сгенерированный платформенный манифест:\")\n\tfmt.Println(manifest)\n}"
      },
      {
        "filename": ".github/workflows/idp-scaffold.yml",
        "lang": "yaml",
        "code": "name: Platform Self-Service Provisioner\n\non:\n  workflow_dispatch:\n    inputs:\n      service_name:\n        description: 'Имя нового микросервиса'\n        required: true\n        default: 'order-processor'\n      team:\n        description: 'Команда владелец'\n        required: true\n        default: 'core-backend'\n\njobs:\n  scaffold:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - name: Scaffold Platform Manifests\n        run: |\n          echo \"Создание инфраструктурных манифестов для ${{ github.event.inputs.service_name }}...\"\n          mkdir -p output/${{ github.event.inputs.service_name }}\n\n      - name: Create Pull Request to Infrastructure Repo\n        uses: peter-evans/create-pull-request@v6\n        with:\n          token: ${{ secrets.INFRA_REPO_PAT }}\n          commit-message: \"feat(idp): scaffold new service ${{ github.event.inputs.service_name }}\"\n          title: \"IDP: New Service Onboarding - ${{ github.event.inputs.service_name }}\"\n          body: \"Автоматически сгенерированный PR платформенной командой для регистрации сервиса ${{ github.event.inputs.service_name }}.\"\n          branch: \"idp/${{ github.event.inputs.service_name }}\" "
      }
    ],
    "under_the_hood": "В концепции Platform as a Product портал разработки (Backstage) отправляет webhook или вызывает GitHub Actions API (`POST /repos/:owner/:repo/actions/workflows/:id/dispatches`). \n\nПлатформенный пайплайн генерирует стандартизированные манифесты Kubernetes, регистрирует DNS-записи во внутреннем Route53/CoreDNS, настраивает дашборд Grafana и заводит проект в Sentry без единого обращения к живым администраторам.",
    "pitfalls": "1. Навязывание жестких ограничений («золотой наручник» вместо «золотого пути»): если платформа запрещает любые нестандартные параметры, разработчики будут обходить ее стороной.\n2. Отсутствие контроля удаления ресурсов (Day 2 Operations): создание сервисов автоматизировано, но заброшенные тестовые сервисы годами тратят ресурсы облака.\n3. Недостаточная документация API платформы для разработчиков.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем принципиальная разница между классической ролью DevOps-инженера и современным Platform Engineer?\n**Ответ:** \n- Классический **DevOps-инженер** часто работал в проектной команде («DevOps в каждой команде») и занимался ручной настройкой пайплайнов, написанием Dockerfile и деплоем конкретных приложений.\n- **Platform Engineer** относится к платформе как к **внутреннему продукту (Platform as a Product)**, клиентами которого являются сотни продуктовых разработчиков компании. Он создает инструменты самообслуживания (IDP, CLI, фреймворки, API), позволяющие продуктовым инженерам самостоятельно развертывать, мониторить и масштабировать сервисы за считанные минуты без тикетов и очередей."
  },
  {
    "num": 57,
    "title": "Непрерывное развертывание (Continuous Deployment) в Kubernetes при слиянии в ветку main",
    "task": "**Непрерывное развертывание (CD)**: Добавьте финальный шаг в ваш пайплайн. При слиянии кода в ветку `main`, после сборки и публикации нового образа в реестр, пайплайн должен автоматически обновлять деплоймент в Kubernetes. Напишите вызов команды `kubectl set image deployment/my-app my-container=my-registry/my-app:sha-tag` [475] (или опишите концепцию GitOps развертывания через ArgoCD, где пайплайн просто коммитит новый тег образа в специальный вспомогательный репозиторий манифестов).",
    "theory": "Завершающий этап зрелого CI/CD конвейера — истинное **Continuous Deployment (CD)**:\n- При одобрении и слиянии Pull Request в ветку `main` пайплайн автоматически проводит все проверки, собирает контейнерный образ и инициирует доставку в целевой кластер без участия человека.\n- Для обеспечения нулевого времени простоя (Zero Downtime Deployment) в Kubernetes используются параметры `maxSurge: 25%` и `maxUnavailable: 0`.\n- Обязательно наличие проб готовности (`readinessProbe`) и живучести (`livenessProbe`), гарантирующих, что старые реплики сервиса не будут остановлены до того, как новые поды полностью инициализируют сетевые слушатели и пул подключений к БД.",
    "step_by_step": "1. Включите триггер на событие `push` в ветку `main`.\n2. Соберите OCI-образ приложения и опубликуйте в реестр с тегом SHA.\n3. Настройте шаг развертывания через `kubectl apply -f ...` или обновление через GitOps.\n4. Настройте команду ожидания успешного завершения развертывания: `kubectl rollout status deployment/web-gateway --timeout=180s`.\n5. Проверьте поведение кластера при обновлении реплик.",
    "code_blocks": [
      {
        "filename": ".github/workflows/cd-deploy.yml",
        "lang": "yaml",
        "code": "name: Continuous Deployment to K8s\n\non:\n  push:\n    branches: [ main ]\n\njobs:\n  ci-cd:\n    name: Build, Publish and Deploy\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout Code\n        uses: actions/checkout@v4\n\n      - name: Set up Docker Buildx\n        uses: docker/setup-buildx-action@v3\n\n      - name: Login to Container Registry\n        uses: docker/login-action@v3\n        with:\n          registry: ghcr.io\n          username: ${{ github.actor }}\n          password: ${{ secrets.GITHUB_TOKEN }}\n\n      - name: Build & Publish Image\n        uses: docker/build-push-action@v5\n        with:\n          context: .\n          push: true\n          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}\n\n      - name: Set Kubeconfig\n        uses: azure/k8s-set-context@v4\n        with:\n          method: kubeconfig\n          kubeconfig: ${{ secrets.KUBE_CONFIG }}\n\n      - name: Deploy to Kubernetes Cluster\n        run: |\n          kubectl set image deployment/web-gateway web-gateway=ghcr.io/${{ github.repository }}:${{ github.sha }} -n production\n          kubectl rollout status deployment/web-gateway -n production --timeout=180s"
      },
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: web-gateway\n  namespace: production\nspec:\n  replicas: 3\n  strategy:\n    type: RollingUpdate\n    rollingUpdate:\n      maxSurge: 1\n      maxUnavailable: 0\n  selector:\n    matchLabels:\n      app: web-gateway\n  template:\n    metadata:\n      labels:\n        app: web-gateway\n    spec:\n      containers:\n        - name: web-gateway\n          image: ghcr.io/company/web-gateway:latest\n          ports:\n            - containerPort: 8080\n          readinessProbe:\n            httpGet:\n              path: /ready\n              port: 8080\n            initialDelaySeconds: 3\n            periodSeconds: 5\n          livenessProbe:\n            httpGet:\n              path: /live\n              port: 8080\n            initialDelaySeconds: 5\n            periodSeconds: 10"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n\t\"os/signal\"\n\t\"syscall\"\n\t\"time\"\n)\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/live\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"ALIVE\"))\n\t})\n\tmux.HandleFunc(\"/ready\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"READY\"))\n\t})\n\tmux.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\t_, _ = w.Write([]byte(\"Production Gateway v1.0.0\"))\n\t})\n\n\tserver := &http.Server{\n\t\tAddr:    \":8080\",\n\t\tHandler: mux,\n\t}\n\n\tgo func() {\n\t\tfmt.Println(\"Сервер слушает на порту :8080\")\n\t\tif err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {\n\t\t\tfmt.Printf(\"Ошибка сервера: %v\\n\", err)\n\t\t}\n\t}()\n\n\tstop := make(chan os.Signal, 1)\n\tsignal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)\n\t<-stop\n\n\tfmt.Println(\"Получен сигнал завершения. Graceful shutdown...\")\n\tctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)\n\tdefer cancel()\n\n\tif err := server.Shutdown(ctx); err != nil {\n\t\tfmt.Printf(\"Ошибка при остановке сервера: %v\\n\", err)\n\t}\n\tfmt.Println(\"Сервер успешно остановлен.\")\n}"
      }
    ],
    "under_the_hood": "При выполнении `RollingUpdate` с параметром `maxUnavailable: 0` Kubelet сначала создает новый Pod и ждет прохождения `readinessProbe`. \n\nТолько после того, как эндпоинт `/ready` вернет статус 200 OK, Kubernetes Service переключает сетевые правила iptables/IPVS на новый под и отправляет сигнал `SIGTERM` старому поду. Благодаря встроенному Graceful Shutdown на Go сервер завершает текущие HTTP-запросы без обрыва соединений клиентов.",
    "pitfalls": "1. Отсутствие обработки `SIGTERM` в Go: контейнер мгновенно завершается, обрывая тысячи активных пользовательских соединений.\n2. `readinessProbe` проверяет внешние зависимости (например, падение стороннего сервиса делает локальный сервис «не готовым», и K8s выводит из балансировки все поды кластера одновременно).\n3. Параметр `maxUnavailable: 1` при 1 реплике сервиса: приводит к гарантированному простою (downtime) во время обновления.",
    "bigtech_interview": "**Вопрос с собеседования:** Каковы три фундаментальных условия для обеспечения True Zero-Downtime Deployment микросервиса на Go в Kubernetes?\n**Ответ:** \n1. **Корректные K8s Probes:** Наличие `readinessProbe` (чтобы трафик не поступал до инициализации роутеров и пулов БД) и `livenessProbe`.\n2. **Graceful Shutdown в коде Go:** Перехват `SIGTERM`, вызов `server.Shutdown(ctx)` с достаточным таймаутом для обработки текущих In-flight запросов.\n3. **Задержка перед остановкой (preStop Hook):** Обновление правил iptables/kube-proxy на всех нодах кластера занимает 1–3 секунды. Чтобы запросы, находящиеся в полете, не попали на уже умирающий сокет, в манифест контейнера добавляется `lifecycle.preStop.exec.command: [\"sleep\", \"5\"]`, давая kube-proxy время обновить таблицы маршрутизации."
  }
]
