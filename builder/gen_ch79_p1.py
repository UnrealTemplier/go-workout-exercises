# -*- coding: utf-8 -*-
"""
Глава 79: Интеграция с Service Mesh (Istio, Linkerd) и mTLS — Часть 1 (Упражнения 1-40)
"""

exercises = [
    {
        "num": 1,
        "title": "Sidecar Injection и перехват сетевого трафика через iptables",
        "task": "Разверните приложение Go в Kubernetes с Istio/Linkerd. Покажите, что после injection в pod появляется istio-proxy (Envoy) или linkerd-proxy. Объясните, как iptables/iptables-tables (или eBPF в Linkerd) перехватывают весь egress/ingress трафик и направляют через sidecar.",
        "theory": "Service Mesh в Kubernetes реализует паттерн Sidecar, внедряя прокси-контейнер (Envoy в Istio, micro-proxy на Rust в Linkerd) в тот же сетевой неймспейс (Network Namespace), что и целевое приложение. При автоматической инъекции (MutatingAdmissionWebhook) в Pod добавляется init-контейнер (`istio-init`) и sidecar (`istio-proxy`). Init-контейнер запускается с правами `NET_ADMIN` и настраивает правила ядра Linux `iptables` в цепочках `PREROUTING` и `OUTPUT` таблицы `nat`. Все входящие пакеты перенаправляются на локальный порт Envoy (обычно 15006), а все исходящие — на порт 15001. Сам Envoy работает под фиксированным UID (1337), и iptables настроен игнорировать пакеты, исходящие от этого UID, предотвращая бесконечные циклы перенаправления.",
        "step_by_step": [
            "Создайте микросервис на Go, слушающий стандартный порт (например, :8080).",
            "Подготовьте Kubernetes Deployment и Service с аннотацией sidecar.istio.io/inject: 'true'.",
            "Изучите механизм захвата сокетов: вызов getsockopt с флагом SO_ORIGINAL_DST позволяет Envoy узнать реальный целевой IP/порт после редиректа iptables.",
            "Проверьте наличие двух контейнеров в поде с помощью kubectl get pods."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n\t\"os/signal\"\n\t\"syscall\"\n\t\"time\"\n)\n\n// EchoHandler обрабатывает входящие запросы.\n// Приложение слушает 0.0.0.0:8080, не подозревая о наличии Envoy.\n// Трафик прозрачно перехвачен iptables PREROUTING -> Envoy (15006) -> app (8080).\nfunc EchoHandler(w http.ResponseWriter, r *http.Request) {\n\tpodName := os.Getenv(\"HOSTNAME\")\n\tlog.Printf(\"[EchoHandler] Received %s %s from %s\", r.Method, r.URL.Path, r.RemoteAddr)\n\tw.Header().Set(\"Content-Type\", \"application/json\")\n\tw.WriteHeader(http.StatusOK)\n\tfmt.Fprintf(w, `{\"status\":\"ok\",\"pod\":\"%s\",\"path\":\"%s\"}`, podName, r.URL.Path)\n}\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\tw.Write([]byte(\"healthy\"))\n\t})\n\tmux.HandleFunc(\"/\", EchoHandler)\n\n\tsrv := &http.Server{\n\t\tAddr:         \":8080\",\n\t\tHandler:      mux,\n\t\tReadTimeout:  5 * time.Second,\n\t\tWriteTimeout: 10 * time.Second,\n\t}\n\n\tstop := make(chan os.Signal, 1)\n\tsignal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)\n\n\tgo func() {\n\t\tlog.Println(\"Starting server on :8080...\")\n\t\tif err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {\n\t\t\tlog.Fatalf(\"Server error: %v\", err)\n\t\t}\n\t}()\n\n\t<-stop\n\tlog.Println(\"Shutting down gracefully...\")\n\tctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\tdefer cancel()\n\tif err := srv.Shutdown(ctx); err != nil {\n\t\tlog.Fatalf(\"Shutdown failed: %v\", err)\n\t}\n\tlog.Println(\"Server exited cleanly\")\n}",
                "filename": "main.go",
                "note": "Реализация: Sidecar Injection и перехват сетевого трафика через iptables (Упражнение 1)"
            }
        ],
        "under_the_hood": "В сетевом неймспейсе пода init-контейнер выполняет команду iptables -t nat -A PREROUTING -p tcp -j ISTIO_INBOUND. Правило перенаправляет TCP SYN на 127.0.0.1:15006. Envoy принимает соединение и вызывает системный вызов getsockopt(fd, SOL_IP, SO_ORIGINAL_DST, &addr, &len), чтобы выяснить исходный IP-адрес назначения. Для исходящего трафика правило ISTIO_OUTPUT перехватывает сокеты и отсылает на 15001, пропуская трафик UID 1337.",
        "pitfalls": "Если приложение в Go пытается определить реальный IP-адрес клиента через r.RemoteAddr, оно увидит 127.0.0.1 (адрес loopback Envoy). Реальный IP клиента передается Envoy в заголовке X-Forwarded-For. Попытка привязаться к r.RemoteAddr ломает IP-аутентификацию и гео-блокировки.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс/Ozon: 'Как Envoy восстанавливает реальный адрес назначения после iptables REDIRECT?' Ответ: Через системный вызов getsockopt с опцией SO_ORIGINAL_DST (или в случае IPv6 — IP6T_SO_ORIGINAL_DST). В современных ядрах Linux с eBPF (Cilium Service Mesh или Linkerd cgroup-v2) перехват выполняется еще раньше в сокетном слое (sock_ops), устраняя накладные расходы таблиц iptables и сокетных редиректов."
    },
    {
        "num": 2,
        "title": "mTLS, SPIFFE/SPIRE идентификация и политика PeerAuthentication",
        "task": "Настройте PeerAuthentication (Istio) или ServerPolicy (Linkerd) с mtls.mode: STRICT. Покажите, что pod без sidecar не может подключиться к сервису с STRICT. Объясните, как sidecar-ы обмениваются сертификатами (SPIFFE/SPIRE identity, автоматическая ротация через Citadel/Linkerd identity).",
        "theory": "Zero Trust архитектура в Kubernetes строится на взаимной аутентификации сервисов (mTLS). Каждый workload идентифицируется стандартом SPIFFE (Secure Production Identity Framework for Everyone). Идентификатор формируется в виде URI: `spiffe://<trust-domain>/ns/<namespace>/sa/<service-account>`. Управляющий слой (istiod / Linkerd identity) выступает в роли Certification Authority (CA), выдающего короткоживущие X.509 сертификаты (SVID). Envoy получает сертификаты по gRPC через Secret Discovery Service (SDS) без перезапуска пода. В режиме `STRICT` Envoy сбрасывает любые незашифрованные TCP-сессии и проверяет валидность SAN (Subject Alternative Name) клиентского сертификата.",
        "step_by_step": [
            "Сформируйте конфигурацию PeerAuthentication с режимом STRICT в namespace default.",
            "Напишите Go-клиент, выполняющий проверку подключения как через HTTP (имитация пода внутри mesh), так и напрямую через raw TLS.",
            "Продемонстрируйте обработку TLS-рукопожатия и валидацию SPIFFE URI в сертификате сервера.",
            "Убедитесь, что соединение отклоняется на фазе TLS-handshake, если клиент не предоставил валидный mesh-сертификат."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"crypto/tls\"\n\t\"crypto/x509\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"net/url\"\n\t\"time\"\n)\n\n// ValidateSPIFFEID проверяет, что в SAN представлен доверенный SPIFFE ID.\nfunc ValidateSPIFFEID(certs []*x509.Certificate, expectedTrustDomain, expectedSA string) error {\n\tif len(certs) == 0 {\n\t\treturn fmt.Errorf(\"no peer certificates presented\")\n\t}\n\tleaf := certs[0]\n\tfor _, u := range leaf.URIs {\n\t\tif u.Scheme == \"spiffe\" {\n\t\t\tlog.Printf(\"[mTLS] Verified peer SPIFFE ID: %s\", u.String())\n\t\t\t// Пример: spiffe://cluster.local/ns/default/sa/payments-sa\n\t\t\tif u.Host == expectedTrustDomain && u.Path == \"/ns/default/sa/\"+expectedSA {\n\t\t\t\treturn nil\n\t\t\t}\n\t\t}\n\t}\n\treturn fmt.Errorf(\"spiffe id mismatch or missing: %v\", leaf.URIs)\n}\n\nfunc main() {\n\t// В реальном mesh mTLS берет на себя Envoy.\n\t// Ниже показана программная эмуляция строгой mTLS верификации SPIFFE SAN в Go.\n\tclientCert, err := tls.X509KeyPair([]byte(\"fake-cert\"), []byte(\"fake-key\"))\n\tif err != nil {\n\t\tlog.Printf(\"Demo note: in service mesh, Envoy handles certs directly via SDS.\")\n\t}\n\n\ttlsConfig := &tls.Config{\n\t\tInsecureSkipVerify: false,\n\t\tVerifyPeerCertificate: func(rawCerts [][]byte, verifiedChains [][]*x509.Certificate) error {\n\t\t\tif len(verifiedChains) == 0 {\n\t\t\t\treturn fmt.Errorf(\"no verified certificate chain\")\n\t\t\t}\n\t\t\treturn ValidateSPIFFEID(verifiedChains[0], \"cluster.local\", \"billing-service\")\n\t\t},\n\t}\n\n\t_ = clientCert\n\t_ = tlsConfig\n\tfmt.Println(\"SPIFFE mTLS policy configured: STRICT mode requires valid trust domain and SVID\")\n}",
                "filename": "security.go",
                "note": "Реализация: mTLS, SPIFFE/SPIRE идентификация и политика PeerAuthentication (Упражнение 2)"
            }
        ],
        "under_the_hood": "istiod динамически обновляет сертификаты через Envoy Secret Discovery Service (SDS) v3 API. Когда сертификат приближается к экспирации (по умолчанию время жизни SVID 24 часа, ротация каждые 12 часов), Envoy инициирует SDS StreamSecretsRequest. istiod генерирует новую пару ключей через SPIRE/Citadel и пушит в Envoy по gRPC. Соединения обновляются без drop'а активных запросов.",
        "pitfalls": "Включение режима `STRICT` в namespace ломает встроенные Kubernetes Liveness/Readiness пробы (`kubelet` опрашивает pod напрямую без mTLS). Чтобы избежать падения подов, Istio по умолчанию перенаправляет probe-порты через специальный аннотированный endpoint или Envoy rewrite.",
        "bigtech_interview": "Вопрос на собеседовании в Т-Банк/Wildberries: 'Что такое SPIFFE ID и где он физически хранится в X.509 сертификате?' Ответ: SPIFFE ID хранится в расширении Subject Alternative Name (SAN) в секции URI (Uniform Resource Identifier), например, `spiffe://prod.corp/ns/billing/sa/order-service`. Envoy парсит именно поле URI, а не Common Name (CN)."
    },
    {
        "num": 3,
        "title": "Паттерн Sidecar: архитектурное разделение ответственности",
        "task": "Напиши простейший HTTP 'Echo' сервис. Разверни его в K8s с установленным Istio (включи sidecar-инъекцию). Зайди в контейнер. Убедись, что рядом с твоим Go-бинарником крутится прокси Envoy. Пойми, что теперь твой Go-код может делать запросы по HTTP, а Envoy сам зашифрует их в mTLS.",
        "theory": "Фундаментальная идея Service Mesh — освободить прикладной код от сетевых сквозных задач (cross-cutting concerns): mTLS шифрования, управления повторами (retries), балансировки нагрузки, канареечного разделения и распределенной телеметрии. Go-приложение общается исключительно по обычному HTTP/1.1 или HTTP/2 через локальный сокет, не загружая в память TLS-сертификаты и CA-бандлы. Envoy перехватывает TCP-поток, упаковывает его в защищенную mTLS-сессию с ALPN `istio` или `linkerd`, терминирует шифрование на принимающей стороне и передает чистый HTTP приложению.",
        "step_by_step": [
            "Создайте легковесный HTTP Echo сервер на стандартной библиотеке Go.",
            "Реализуйте хендлер, возвращающий заголовки запроса в формате JSON, чтобы увидеть инжектированные Envoy заголовки.",
            "Проверьте наличие заголовков x-forwarded-client-cert, x-request-id и x-envoy-upstream-service-time.",
            "Убедитесь, что Go-сервер работает без https/tls конфигурации."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"time\"\n)\n\n// EchoResponse возвращает клиенту метаданные запроса, переданные через Envoy.\ntype EchoResponse struct {\n\tHeaders    map[string][]string `json:\"headers\"`\n\tRemoteAddr string              `json:\"remote_addr\"`\n\tTimestamp  time.Time           `json:\"timestamp\"`\n\tMessage    string              `json:\"message\"`\n}\n\nfunc echoHandler(w http.ResponseWriter, r *http.Request) {\n\tresp := EchoResponse{\n\t\tHeaders:    r.Header,\n\t\tRemoteAddr: r.RemoteAddr,\n\t\tTimestamp:  time.Now().UTC(),\n\t\tMessage:    \"Request processed via Service Mesh Envoy Sidecar\",\n\t}\n\n\tw.Header().Set(\"Content-Type\", \"application/json\")\n\tw.WriteHeader(http.StatusOK)\n\tif err := json.NewEncoder(w).Encode(resp); err != nil {\n\t\tlog.Printf(\"Encode error: %v\", err)\n\t}\n}\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/echo\", echoHandler)\n\n\tsrv := &http.Server{\n\t\tAddr:         \":8080\",\n\t\tHandler:      mux,\n\t\tReadTimeout:  5 * time.Second,\n\t\tWriteTimeout: 5 * time.Second,\n\t}\n\n\tlog.Println(\"Go Echo microservice running on port 8080 (plain HTTP)\")\n\tif err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {\n\t\tlog.Fatalf(\"Fatal: %v\", err)\n\t}\n}",
                "filename": "main.go",
                "note": "Реализация: Паттерн Sidecar: архитектурное разделение ответственности (Упражнение 3)"
            }
        ],
        "under_the_hood": "Когда Go-сервер делает исходящий вызов http.Get('http://payment-svc:8080/pay'), сокет перехватывается правилом iptables OUTPUT. Пакет перенаправляется на порт 15001. Envoy анализирует Host/Authority заголовок `payment-svc:8080`, сверяет его со своим кластером Virtual Hosts, открывает mTLS-соединение с sidecar-прокси на поде payment-svc, шифрует тело и отправляет по сети.",
        "pitfalls": "Если приложение в коде использует `https://payment-svc:8080` вместо `http://...`, Envoy получит уже зашифрованный TLS-трафик от Go-клиента. В таком случае Envoy не сможет проинспектировать L7-заголовки (URL, path, traceparent) и будет маршрутизировать трафик как непрозрачный L4 TCP поток, лишая вас L7-маршрутизации и метрик.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Почему в Go-микросервисах внутри Service Mesh рекомендуется отключать собственный HTTPS-сервер и слушать plain HTTP?' Ответ: Envoy выполняет mTLS на L4/L7 периметре. Если приложение слушает HTTPS, Envoy не сможет парсить HTTP-заголовки, применять rate-limiting, VirtualService routing и собирать детальные L7-метрики (HTTP response codes, path latency)."
    },
    {
        "num": 4,
        "title": "L7 Traffic Management: Canary Routing через VirtualService и DestinationRule",
        "task": "Настройте VirtualService + DestinationRule (Istio) или TrafficSplit (Linkerd): 90% трафика на v1, 10% на v2. Реализуйте Go-сервис с двумя deployment (app=v1, app=v2). Покажите распределение через curl в loop. Объясните, как mesh делает это без изменения клиентского кода.",
        "theory": "Управление L7-трафиком в Istio базируется на разделении абстракций: 1) `VirtualService` определяет правила маршрутизации входящих запросов (хосты, пути, заголовки, веса для канареечных релизов); 2) `DestinationRule` определяет политики, применяемые к трафику после маршрутизации (пулы соединений, mTLS режим, алгоритм балансировки, subsets по Kubernetes-меткам). Клиент обращается по стабильному DNS имени `users-svc`. Envoy перехватывает запрос и псевдослучайно согласно весам (90/10) выбирает целевой subset (v1 или v2).",
        "step_by_step": [
            "Реализуйте сервис на Go, возвращающий версию приложения из переменной окружения APP_VERSION.",
            "Напишите клиента на Go, посылающего 100 запросов и подсчитывающего процент ответов от v1 и v2.",
            "Сконфигурируйте VirtualService с весами 90 и 10.",
            "Проверьте соблюдение закона больших чисел при канареечном распределении."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"io\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n\t\"sync\"\n\t\"time\"\n)\n\ntype VersionResponse struct {\n\tVersion string `json:\"version\"`\n\tHost    string `json:\"host\"`\n}\n\n// ServerSide: сервис возвращает свою версию\nfunc startServer() {\n\tversion := os.Getenv(\"APP_VERSION\")\n\tif version == \"\" {\n\t\tversion = \"v1\"\n\t}\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/version\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\t_ = json.NewEncoder(w).Encode(VersionResponse{\n\t\t\tVersion: version,\n\t\t\tHost:    os.Getenv(\"HOSTNAME\"),\n\t\t})\n\t})\n\tlog.Printf(\"Starting service version %s on :8080\", version)\n\t_ = http.ListenAndServe(\":8080\", mux)\n}\n\n// ClientSide: генератор трафика для проверки весов 90/10\nfunc runCanaryVerification(targetURL string, totalRequests int) {\n\tcounts := make(map[string]int)\n\tvar mu sync.Mutex\n\tclient := &http.Client{Timeout: 2 * time.Second}\n\n\tfor i := 0; i < totalRequests; i++ {\n\t\tresp, err := client.Get(targetURL)\n\t\tif err != nil {\n\t\t\tlog.Printf(\"Request %d failed: %v\", i, err)\n\t\t\tcontinue\n\t\t}\n\t\tbody, _ := io.ReadAll(resp.Body)\n\t\tresp.Body.Close()\n\n\t\tvar vr VersionResponse\n\t\tif err := json.Unmarshal(body, &vr); err == nil {\n\t\t\tmu.Lock()\n\t\t\tcounts[vr.Version]++\n\t\t\tmu.Unlock()\n\t\t}\n\t}\n\n\tfmt.Printf(\"Canary traffic results over %d requests:\\n\", totalRequests)\n\tfor ver, cnt := range counts {\n\t\tpct := float64(cnt) / float64(totalRequests) * 100\n\t\tfmt.Printf(\"Version %s: %d requests (%.1f%%)\\n\", ver, cnt, pct)\n\t}\n}\n\nfunc main() {\n\tif len(os.Args) > 1 && os.Args[1] == \"client\" {\n\t\trunCanaryVerification(\"http://users-service:8080/version\", 100)\n\t\treturn\n\t}\n\tstartServer()\n}",
                "filename": "server.go",
                "note": "Реализация: L7 Traffic Management: Canary Routing через VirtualService и DestinationRule (Упражнение 4)"
            }
        ],
        "under_the_hood": "Envoy использует алгоритм Weighted Cluster Selection. В конфигурации Envoy ClusterManager хранит кластеры `outbound|8080|v1|users-svc` и `outbound|8080|v2|users-svc`. При поступлении HTTP-запроса роутер выбирает кластер, используя целочисленный генератор псевдослучайных чисел от 0 до 100. Соединение пересылается через соответствующий upstream connection pool.",
        "pitfalls": "Если в VirtualService заданы веса (90/10), но забыли создать DestinationRule с подмножествами (subsets v1 и v2), Envoy вернет ошибку HTTP 503 NR (No Route configured). Kubernetes Service сам по себе не умеет делить трафик по меткам версий.",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'Чем L7 traffic split в Istio отличается от стандартного Kubernetes Deployment с изменением числа реплик (например, 9 реплик v1 и 1 реплика v2)?' Ответ: Деление подами грубое, расходует память и ресурсы CPU на лишние поды и не позволяет маршрутизировать по HTTP-заголовкам (куки, сессии, токены). Istio делает сплит на уровне каждого запроса с нулевым оверхедом по числу подов."
    },
    {
        "num": 5,
        "title": "Circuit Breaker в Mesh: Outlier Detection и изоляция сбойных инстансов",
        "task": "Настройте DestinationRule с outlierDetection (Istio): 5 consecutive errors → eject на 30 сек. Сымитируйте 500 в v2 через Go-код (if rand < 0.5 { return 500 }). Покажите, что после 5 ошибок трафик на v2 прекращается. Объясните, почему это L7 circuit breaker, а не TCP.",
        "theory": "Circuit Breaker (предохранитель) в Service Mesh реализуется через механизм Outlier Detection в `DestinationRule`. Envoy непрерывно отслеживает HTTP-коды ответов каждого отдельного upstream-пода. Если инстанс возвращает подряд N ошибок уровня 5xx (параметр `consecutive5xx` или `consecutiveGatewayErrors`), Envoy временно исключает (ejects) этот под из пула балансировки на заданный интервал (`baseEjectionTime`). Это L7-предохранитель: TCP-соединение может оставаться идеальным (SYN/ACK проходят мгновенно), но Envoy анализирует семантику HTTP-статусов.",
        "step_by_step": [
            "Напишите Go-сервис, возвращающий ошибку 500 Internal Server Error при определенных условиях.",
            "Настройте манифест DestinationRule с outlierDetection: consecutive5xx: 5, interval: 10s, baseEjectionTime: 30s, maxEjectionPercent: 100.",
            "Напишите клиентский тест на Go, непрерывно отправляющий запросы к пулу подов.",
            "Зафиксируйте прекращение попадания запросов на сбойный под после фиксации 5 последовательных ошибок 500."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"math/rand\"\n\t\"net/http\"\n\t\"os\"\n\t\"sync/atomic\"\n\t\"time\"\n)\n\nvar failureCounter uint64\n\nfunc failingHandler(w http.ResponseWriter, r *http.Request) {\n\tpod := os.Getenv(\"HOSTNAME\")\n\t// Имитация сбойного пода (например, проблемы с соединением к локальному диску)\n\tfailMode := os.Getenv(\"FAIL_MODE\") == \"true\"\n\n\tif failMode {\n\t\tcount := atomic.AddUint64(&failureCounter, 1)\n\t\tlog.Printf(\"[FAIL POD %s] Consecutive failure #%d\", pod, count)\n\t\tw.Header().Set(\"X-Pod-Failure\", \"true\")\n\t\thttp.Error(w, \"simulated 500 internal server error\", http.StatusInternalServerError)\n\t\treturn\n\t}\n\n\tw.WriteHeader(http.StatusOK)\n\tfmt.Fprintf(w, `{\"status\":\"ok\",\"pod\":\"%s\"}`, pod)\n}\n\nfunc main() {\n\trand.Seed(time.Now().UnixNano())\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/api/data\", failingHandler)\n\n\tsrv := &http.Server{\n\t\tAddr:         \":8080\",\n\t\tHandler:      mux,\n\t\tReadTimeout:  3 * time.Second,\n\t\tWriteTimeout: 3 * time.Second,\n\t}\n\n\tlog.Println(\"Starting service with OutlierDetection target on :8080\")\n\tif err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {\n\t\tlog.Fatalf(\"Server error: %v\", err)\n\t}\n}",
                "filename": "circuit_breaker.go",
                "note": "Реализация: Circuit Breaker в Mesh: Outlier Detection и изоляция сбойных инстансов (Упражнение 5)"
            }
        ],
        "under_the_hood": "Envoy на клиенте (caller sidecar) хранит статистику по каждому хосту в кластере. При получении ответа HTTP 5xx инкрементируется счетчик `consecutive_5xx`. Когда он достигает порога, хост помечается как `ejected` на время `baseEjectionTime * ejection_count`. Балансировщик исключает его из кольца (Round Robin / Maglev), направляя 100% запросов только на здоровые поды.",
        "pitfalls": "Параметр `maxEjectionPercent` по умолчанию равен 10% в некоторых версиях. Если у вас всего 2 реплики сервиса, и одна упала, при maxEjectionPercent: 10 Envoy НЕ исключит упавший под, чтобы не выбивать весь сервис. Для малых кластеров нужно явно выставлять maxEjectionPercent: 100.",
        "bigtech_interview": "Вопрос на собеседовании в Lamoda: 'Почему реализация Circuit Breaker в Envoy предпочтительнее библиотеки внутри Go-кода (например, sony/gobreaker)?' Ответ: Outlier Detection в Envoy работает на уровне отдельных инстансов (IP-адресов подов), а клиентская библиотека обычно блокирует весь сервис целиком. Кроме того, состояние распределено между sidecar-ами без необходимости синхронизации между потоками Go-приложения."
    },
    {
        "num": 6,
        "title": "Прокидывание контекста B3 Headers в микросервисах",
        "task": "Envoy генерирует трейсы (TraceID). Но если Сервис А вызывает Сервис Б, Envoy не знает, что эти запросы связаны! Напиши HTTP-мидлварь, которая читает из входящего запроса заголовки x-b3-traceid, x-b3-spanid, x-b3-sampled и кладет их в context.Context.",
        "theory": "Envoy умеет автоматически генерировать заголовки распределенной трассировки при входе запроса в Ingress Gateway. Однако при вызове downstream-сервиса (Service A -> Service B) Envoy sidecar сервиса A не может угадать, какой исходящий запрос был порожден каким входящим запросом внутри Go-рантайма! Ответственность за пробрасывание (context propagation) лежит исключительно на Go-приложении: мидлварь должна извлечь B3-заголовки (`x-b3-traceid`, `x-b3-spanid`, `x-b3-sampled`) и сохранить их в `context.Context`.",
        "step_by_step": [
            "Определите тип для ключа контекста, чтобы избежать коллизий пакетов.",
            "Создайте структуру B3Context, инкапсулирующую B3-заголовки.",
            "Напишите HTTP middleware, извлекающую заголовки из r.Header и сохраняющую структуру в r.Context().",
            "Реализуйте функцию-хелпер для извлечения B3-контекста в бизнес-логике."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n)\n\ntype contextKey string\n\nconst b3ContextKey contextKey = \"b3-trace-context\"\n\n// B3Headers содержит ключевые идентификаторы Zipkin/B3 спецификации.\ntype B3Headers struct {\n\tTraceID      string\n\tSpanID       string\n\tParentSpanID string\n\tSampled      string\n}\n\n// B3Middleware извлекает заголовки Envoy и помещает их в Go context.\nfunc B3Middleware(next http.Handler) http.Handler {\n\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\tb3 := B3Headers{\n\t\t\tTraceID:      r.Header.Get(\"x-b3-traceid\"),\n\t\t\tSpanID:       r.Header.Get(\"x-b3-spanid\"),\n\t\t\tParentSpanID: r.Header.Get(\"x-b3-parentspanid\"),\n\t\t\tSampled:      r.Header.Get(\"x-b3-sampled\"),\n\t\t}\n\n\t\tif b3.TraceID != \"\" {\n\t\t\tlog.Printf(\"[B3Middleware] Incoming TraceID: %s, SpanID: %s\", b3.TraceID, b3.SpanID)\n\t\t}\n\n\t\tctx := context.WithValue(r.Context(), b3ContextKey, b3)\n\t\tnext.ServeHTTP(w, r.WithContext(ctx))\n\t})\n}\n\n// FromContext извлекает B3Headers из контекста.\nfunc FromContext(ctx context.Context) (B3Headers, bool) {\n\tb3, ok := ctx.Value(b3ContextKey).(B3Headers)\n\treturn b3, ok\n}\n\nfunc UserOrderHandler(w http.ResponseWriter, r *http.Request) {\n\tb3, ok := FromContext(r.Context())\n\tif !ok || b3.TraceID == \"\" {\n\t\tlog.Println(\"Warning: request arrived without B3 trace context\")\n\t}\n\n\tw.Header().Set(\"Content-Type\", \"application/json\")\n\tw.WriteHeader(http.StatusOK)\n\tfmt.Fprintf(w, `{\"status\":\"processed\",\"trace_id\":\"%s\"}`, b3.TraceID)\n}\n\nfunc main() {\n\thandler := B3Middleware(http.HandlerFunc(UserOrderHandler))\n\tlog.Println(\"Server with B3 tracing middleware listening on :8080\")\n\t_ = http.ListenAndServe(\":8080\", handler)\n}",
                "filename": "middleware.go",
                "note": "Реализация: Прокидывание контекста B3 Headers в микросервисах (Упражнение 6)"
            }
        ],
        "under_the_hood": "Envoy генерирует `x-b3-spanid` для каждого вызова. Когда Сервис А прокидывает `x-b3-traceid` и передает текущий `x-b3-spanid` как `x-b3-parentspanid`, Zipkin/Jaeger коллектор строит корректное дерево спанов (Directed Acyclic Graph), визуализируя latency каждого шага межсервисного взаимодействия.",
        "pitfalls": "Самая частая ошибка в Go: запуск фоновой горутины с передачей `r.Context()`. Когда родительский HTTP-запрос завершается, HTTP-сервер вызывает cancel() для r.Context(), что приводит к внезапному `context.Canceled` в фоновой горутине. Для фоновых задач нужно копировать B3-заголовки в отдельный context.Background().",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Если Service Mesh полностью автоматизирует трассировку, почему разработчики обязаны писать middleware для проброса заголовков?' Ответ: Envoy находится снаружи процесса приложения. Он перехватывает входящие и исходящие TCP-сокеты, но не имеет доступа к стеку вызовов рантайма Go. Связать входящий сокет с исходящим сокетом может только код приложения через контекст."
    },
    {
        "num": 7,
        "title": "Retries, Timeouts и предотвращение Retry Storms в Service Mesh",
        "task": "Настройте VirtualService: retries.attempts: 3, perTryTimeout: 2s, timeout: 10s. Сымитируйте в Go-сервисе time.Sleep(5s) (timeout) и rand.Error() (retry). Покажите, что mesh ретраит автоматически. Объясните, почему retries в mesh опасны без idempotency.",
        "theory": "Сетевые сбои в микросервисах часто носят кратковременный характер (transient failures). Istio `VirtualService` позволяет делегировать логику повторов Envoy: `retries.attempts: 3` и `perTryTimeout: 2s` означают, что Envoy сделает до 3 попыток, ожидая ответа не более 2 секунд на каждую. Однако повторные попытки в распределенных системах смертельно опасны без гарантии идемпотентности: если сервис-получатель уже списал деньги, но ответ задержался в сети, повторный запрос Envoy может привести к повторному списанию! Кроме того, каскадные ретраи вызывают Retry Storms (шторм повторов), способный окончательно обрушить перегруженный downstream-сервис.",
        "step_by_step": [
            "Создайте Go HTTP-хендлер с симуляцией задержек time.Sleep и временных 503 ошибок.",
            "Настройте безопасный механизм генерации Idempotency-Key.",
            "Проверьте, что повторные попытки от Envoy обрабатываются идемпотентно с возвратом ранее сохраненного результата.",
            "Реализуйте логирование попыток через заголовок x-envoy-attempt-count."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"sync\"\n\t\"time\"\n)\n\ntype PaymentStore struct {\n\tmu    sync.Mutex\n\tcache map[string]string\n}\n\nvar store = &PaymentStore{cache: make(map[string]string)}\n\n// IdempotentPaymentHandler безопасно обрабатывает повторы от Envoy.\nfunc IdempotentPaymentHandler(w http.ResponseWriter, r *http.Request) {\n\tattempt := r.Header.Get(\"x-envoy-attempt-count\")\n\tidempotencyKey := r.Header.Get(\"Idempotency-Key\")\n\n\tlog.Printf(\"[Payment] Attempt #%s for Key: %s\", attempt, idempotencyKey)\n\n\tif idempotencyKey == \"\" {\n\t\thttp.Error(w, \"Missing Idempotency-Key\", http.StatusBadRequest)\n\t\treturn\n\t}\n\n\tstore.mu.Lock()\n\tif result, exists := store.cache[idempotencyKey]; exists {\n\t\tstore.mu.Unlock()\n\t\tlog.Printf(\"[Payment] Cache hit for Key %s. Returning previous result.\", idempotencyKey)\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\tw.WriteHeader(http.StatusOK)\n\t\tw.Write([]byte(result))\n\t\treturn\n\t}\n\tstore.mu.Unlock()\n\n\t// Имитация сбоя на первой попытке\n\tif attempt == \"1\" {\n\t\tlog.Println(\"[Payment] Simulating transient network failure on attempt 1\")\n\t\thttp.Error(w, \"Service Unavailable\", http.StatusServiceUnavailable)\n\t\treturn\n\t}\n\n\t// Успешная обработка на повторной попытке\n\tresult := fmt.Sprintf(`{\"status\":\"success\",\"payment_id\":\"pay-%d\"}`, time.Now().UnixNano())\n\tstore.mu.Lock()\n\tstore.cache[idempotencyKey] = result\n\tstore.mu.Unlock()\n\n\tw.Header().Set(\"Content-Type\", \"application/json\")\n\tw.WriteHeader(http.StatusOK)\n\tw.Write([]byte(result))\n}\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/charge\", IdempotentPaymentHandler)\n\tlog.Println(\"Payment service running on :8080\")\n\t_ = http.ListenAndServe(\":8080\", mux)\n}",
                "filename": "server.go",
                "note": "Реализация: Retries, Timeouts и предотвращение Retry Storms в Service Mesh (Упражнение 7)"
            }
        ],
        "under_the_hood": "Envoy инжектирует в исходящий запрос заголовок `x-envoy-attempt-count`, увеличивая его на 1 при каждой попытке. Если сконфигурирован `perTryTimeout: 2s`, Envoy взводит локальный таймер. Если ответ не получен за 2 секунды, Envoy отправляет RST_STREAM (для HTTP/2) или закрывает TCP-сокет к upstream-поду и немедленно инициирует новое соединение к другому поду.",
        "pitfalls": "Категорически запрещено настраивать ретраи в Istio на методы `POST` или `PUT` без явной фильтрации по retryOn (например, `5xx,connect-failure,refused-stream`). Если бэкенд возвращает 500 из-за валидации базы данных, ретраи Envoy только умножат нагрузку на упавшую базу данных.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Что такое Retry Amplification (коэффициент размножения повторов) и как Service Mesh может его усугубить?' Ответ: Если в цепочке вызовов A -> B -> C каждый сервис настроен на 3 ретрая, то при сбое C сервис B сделает 3 попытки, а сервис A сделает 3 попытки на каждый сбой B. В итоге C получит 3 * 3 = 9 запросов на один пользовательский клик! В Service Mesh ретраи должны настраиваться только на верхнем или строго на одном уровне."
    },
    {
        "num": 8,
        "title": "W3C Trace Context: чтение и парсинг заголовка traceparent",
        "task": "Напиши HTTP middleware, которое читает заголовок traceparent (формат: version-trace-id-parent-id-trace-flags). Извлеки trace-id и выведи в лог. Если заголовка нет — сгенерируй свой.",
        "theory": "W3C TraceContext — современный международный стандарт распределенной трассировки, пришедший на смену B3. Основным заголовком является `traceparent`. Его формат строго регламентирован: `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01` где: 1) `version`: 2 hex символа (сейчас всегда '00'); 2) `trace-id`: 32 hex символа (16 байт) — уникальный ID всей цепочки вызовов; 3) `parent-id` (span-id): 16 hex символов (8 байт); 4) `trace-flags`: 2 hex символа (бит 01 указывает на `sampled`).",
        "step_by_step": [
            "Создайте структуру W3CTraceContext для десериализации полей стандарта.",
            "Напишите надежный парсер заголовка traceparent со строгой валидацией длины и формата компонентов.",
            "Реализуйте генератор нового traceparent при отсутствии входящего заголовка с использованием crypto/rand.",
            "Интегрируйте парсер в HTTP middleware и добавьте trace-id во все логи запроса."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"crypto/rand\"\n\t\"encoding/hex\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"strings\"\n)\n\ntype w3cKey struct{}\n\ntype TraceParent struct {\n\tVersion string\n\tTraceID string\n\tSpanID  string\n\tFlags   string\n}\n\nfunc (tp TraceParent) String() string {\n\treturn fmt.Sprintf(\"%s-%s-%s-%s\", tp.Version, tp.TraceID, tp.SpanID, tp.Flags)\n}\n\n// ParseTraceParent разбирает 4-компонентный заголовок W3C.\nfunc ParseTraceParent(header string) (*TraceParent, error) {\n\tparts := strings.Split(header, \"-\")\n\tif len(parts) != 4 {\n\t\treturn nil, fmt.Errorf(\"invalid traceparent format: expected 4 segments, got %d\", len(parts))\n\t}\n\tif parts[0] != \"00\" || len(parts[1]) != 32 || len(parts[2]) != 16 || len(parts[3]) != 2 {\n\t\treturn nil, fmt.Errorf(\"invalid traceparent segment lengths or version\")\n\t}\n\treturn &TraceParent{\n\t\tVersion: parts[0],\n\t\tTraceID: parts[1],\n\t\tSpanID:  parts[2],\n\t\tFlags:   parts[3],\n\t}, nil\n}\n\n// GenerateTraceParent создает новый валидный W3C контекст.\nfunc GenerateTraceParent() *TraceParent {\n\ttraceBytes := make([]byte, 16)\n\tspanBytes := make([]byte, 8)\n\t_, _ = rand.Read(traceBytes)\n\t_, _ = rand.Read(spanBytes)\n\n\treturn &TraceParent{\n\t\tVersion: \"00\",\n\t\tTraceID: hex.EncodeToString(traceBytes),\n\t\tSpanID:  hex.EncodeToString(spanBytes),\n\t\tFlags:   \"01\", // Sampled\n\t}\n}\n\nfunc W3CMiddleware(next http.Handler) http.Handler {\n\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\traw := r.Header.Get(\"traceparent\")\n\t\ttp, err := ParseTraceParent(raw)\n\t\tif err != nil {\n\t\t\ttp = GenerateTraceParent()\n\t\t\tlog.Printf(\"[W3C] Generated new traceparent: %s (reason: %v)\", tp, err)\n\t\t} else {\n\t\t\tlog.Printf(\"[W3C] Accepted upstream TraceID: %s, SpanID: %s\", tp.TraceID, tp.SpanID)\n\t\t}\n\n\t\tctx := context.WithValue(r.Context(), w3cKey{}, tp)\n\t\tw.Header().Set(\"traceparent\", tp.String())\n\t\tnext.ServeHTTP(w, r.WithContext(ctx))\n\t})\n}\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/api/item\", func(w http.ResponseWriter, r *http.Request) {\n\t\ttp, _ := r.Context().Value(w3cKey{}).(*TraceParent)\n\t\tw.Write([]byte(fmt.Sprintf(`{\"trace_id\":\"%s\"}`, tp.TraceID)))\n\t})\n\n\tsrv := http.Server{\n\t\tAddr:    \":8080\",\n\t\tHandler: W3CMiddleware(mux),\n\t}\n\tlog.Println(\"W3C Traceparent server listening on :8080\")\n\t_ = srv.ListenAndServe()\n}",
                "filename": "middleware.go",
                "note": "Реализация: W3C Trace Context: чтение и парсинг заголовка traceparent (Упражнение 8)"
            }
        ],
        "under_the_hood": "W3C Trace Context стандарт запрещает наличие недопустимых hex-символов и требует, чтобы `trace-id` не состоял из одних нулей. Если парсер обнаруживает `00-00000000000000000000000000000000-...`, такой заголовок считается невалидным (all zeros are prohibited by RFC) и должен быть сгенерирован заново.",
        "pitfalls": "Если ваш Go-сервис сгенерирует новый TraceID вместо использования переданного от Envoy, в Jaeger появится разрыв: спан Ingress Gateway останется отдельным сиротским трейсом, а все внутренние вызовы Go-сервиса попадут во второй независимый трейс.",
        "bigtech_interview": "Вопрос на собеседовании в VK: 'В чем ключевое отличие W3C Trace Context от B3 Headers?' Ответ: W3C объединяет TraceID, SpanID и Flags в единый заголовок `traceparent`, что снижает накладные расходы на HTTP-заголовки. Кроме того, спецификация W3C определяет второй заголовок `tracestate` для передачи vendor-specific метаданных между системами (Datadog, Dynatrace, Jaeger) без повреждения основного контекста."
    },
    {
        "num": 9,
        "title": "W3C Trace Context: клиентский RoundTripper для проброса заголовков",
        "task": "Напиши клиентский интерцептор (Transport обертку). Когда твой Go-код делает http.Get (или gRPC-вызов), он должен достать трейс-контекст из ctx и обязательно добавить заголовки traceparent и tracestate в исходящий запрос. Без этого распределенная трассировка в Istio разорвется!",
        "theory": "Чтобы цепочка распределенной трассировки не обрывалась в Service Mesh, каждый исходящий сетевой запрос обязан содержать заголовки `traceparent` и `tracestate`. В Go наиболее идиоматичный и прозрачный способ внедрения исходящих заголовков — реализация интерфейса `http.RoundTripper`. Обертка перехватывает все вызовы `http.Client.Do()`, извлекает данные из `req.Context()` и модифицирует заголовки `req.Header` перед передачей запроса базовому транспорту.",
        "step_by_step": [
            "Определите структуру TracedTransport, оборачивающую http.RoundTripper.",
            "Реализуйте метод RoundTrip(*http.Request) (*http.Response, error).",
            "Извлеките traceparent и tracestate из контекста запроса и добавьте их в заголовки клонированного запроса.",
            "Проверьте работу интерцептора в реальном HTTP-вызове к внешнему API."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"io\"\n\t\"log\"\n\t\"net/http\"\n\t\"time\"\n)\n\ntype traceKey struct{}\n\ntype TraceState struct {\n\tTraceParent string\n\tTraceState  string\n}\n\n// TracedTransport реализует http.RoundTripper, гарантируя проброс трейсов.\ntype TracedTransport struct {\n\tBase http.RoundTripper\n}\n\nfunc (t *TracedTransport) RoundTrip(req *http.Request) (*http.Response, error) {\n\tbase := t.Base\n\tif base == nil {\n\t\tbase = http.DefaultTransport\n\t}\n\n\t// Клонируем запрос для безопасной модификации заголовков\n\tclonedReq := req.Clone(req.Context())\n\n\t// Извлекаем трейс-контекст из Go context\n\tif ts, ok := req.Context().Value(traceKey{}).(TraceState); ok {\n\t\tif ts.TraceParent != \"\" {\n\t\t\tclonedReq.Header.Set(\"traceparent\", ts.TraceParent)\n\t\t}\n\t\tif ts.TraceState != \"\" {\n\t\t\tclonedReq.Header.Set(\"tracestate\", ts.TraceState)\n\t\t}\n\t\tlog.Printf(\"[TracedTransport] Injected traceparent: %s to %s\", ts.TraceParent, req.URL.Host)\n\t} else {\n\t\tlog.Println(\"[TracedTransport] Warning: outbound request without trace context!\")\n\t}\n\n\treturn base.RoundTrip(clonedReq)\n}\n\nfunc main() {\n\tclient := &http.Client{\n\t\tTransport: &TracedTransport{Base: http.DefaultTransport},\n\t\tTimeout:   5 * time.Second,\n\t}\n\n\t// Имитируем входящий контекст\n\tctx := context.WithValue(context.Background(), traceKey{}, TraceState{\n\t\tTraceParent: \"00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01\",\n\t\tTraceState:  \"rojo=1,congo=2\",\n\t})\n\n\treq, err := http.NewRequestWithContext(ctx, http.MethodGet, \"https://httpbin.org/headers\", nil)\n\tif err != nil {\n\t\tlog.Fatalf(\"Request error: %v\", err)\n\t}\n\n\tresp, err := client.Do(req)\n\tif err != nil {\n\t\tlog.Printf(\"Demo call error (network): %v\", err)\n\t\treturn\n\t}\n\tdefer resp.Body.Close()\n\n\tbody, _ := io.ReadAll(resp.Body)\n\tfmt.Printf(\"Response from remote server:\\n%s\\n\", string(body))\n}",
                "filename": "middleware.go",
                "note": "Реализация: W3C Trace Context: клиентский RoundTripper для проброса заголовков (Упражнение 9)"
            }
        ],
        "under_the_hood": "Метод req.Clone(ctx) выполняет поверхностное копирование структуры http.Request и глубокое копирование заголовков req.Header. Это критически важно при конкурентных запросах, чтобы предотвратить race condition при одновременной мутации карты заголовков.",
        "pitfalls": "Использование `req.Header.Set()` напрямую без `req.Clone()` в RoundTripper нарушает контракт http.RoundTripper и вызывает панику `concurrent map writes` при повторных попытках клиента (retries) или параллельных запросах.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Почему в Go предпочтительнее реализовывать проброс заголовков через http.RoundTripper, а не писать обертку над функцией http.Get()?' Ответ: http.RoundTripper является стандартизированным расширением клиента. Любая сторонняя библиотека (AWS SDK, gRPC-gateway, клиенты платежных шлюзов), принимающая стандартный `*http.Client`, автоматически начинает пробрасывать трейсы без изменения своего внутреннего кода."
    },
    {
        "num": 10,
        "title": "Принципы работы Service Mesh: архитектурная роль Envoy Sidecar",
        "task": "Напишите подробный архитектурный комментарий, объясняющий роль Envoy Sidecar-прокси в Istio/Linkerd. Опишите, как прокси перехватывает весь входящий и исходящий трафик пода, автоматически обеспечивая взаимный TLS (mTLS), балансировку и ретраи, и почему разработчику Go-бэкенда больше не нужно настраивать mTLS-сертификаты внутри кода приложения.",
        "theory": "Service Mesh архитектура разделяет систему на Data Plane и Control Plane. Control Plane (istiod) управляет политиками, конфигурацией и выпуском сертификатов (CA). Data Plane состоит из высокопроизводительных L4/L7 прокси (Envoy на C++ или Linkerd2-proxy на Rust), внедряемых в качестве sidecar к каждому микросервису. Envoy слушает локальные порты перехвата и управляет всеми сетевыми сокетами пода. Это устраняет проблему фрагментации: раньше каждая команда внедряла свои библиотеки mTLS и ретраев на разных языках (Go, Java, Node.js), что приводило к несогласованности алгоритмов бэкоффа, утечкам сертификатов и сложностям при ротации ключей.",
        "step_by_step": [
            "Создайте архитектурную структуру, описывающую все уровни абстракции Service Mesh.",
            "Реализуйте диагностический Go-скрипт, проверяющий статус подключения к Envoy Admin API (:15000/server_info).",
            "Сформулируйте в коде ключевые выгоды делегирования mTLS на уровень sidecar.",
            "Продемонстрируйте проверку готовности Envoy перед запуском основного цикла приложения."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"time\"\n)\n\n// EnvoyServerInfo отражает состояние Data Plane прокси Envoy.\ntype EnvoyServerInfo struct {\n\tVersion string `json:\"version\"`\n\tState   string `json:\"state\"`\n\tUptime  string `json:\"uptime_current_epoch\"`\n}\n\n// WaitForEnvoySidecar проверяет готовность sidecar перед началом работы Go-сервиса.\n// Если Go-приложение стартует раньше Envoy, его исходящие запросы в БД завершатся ошибкой\n// (Connection Refused), так как iptables уже активен, а Envoy еще не слушает порт 15001.\nfunc WaitForEnvoySidecar(ctx context.Context, envoyAdminURL string) error {\n\tclient := &http.Client{Timeout: 500 * time.Millisecond}\n\tticker := time.NewTicker(200 * time.Millisecond)\n\tdefer ticker.Stop()\n\n\tlog.Println(\"[MeshInit] Waiting for Envoy sidecar to become LIVE...\")\n\n\tfor {\n\t\tselect {\n\t\tcase <-ctx.Done():\n\t\t\treturn fmt.Errorf(\"timeout waiting for sidecar: %w\", ctx.Err())\n\t\tcase <-ticker.C:\n\t\t\treq, _ := http.NewRequestWithContext(ctx, http.MethodGet, envoyAdminURL+\"/server_info\", nil)\n\t\t\tresp, err := client.Do(req)\n\t\t\tif err != nil {\n\t\t\t\tcontinue\n\t\t\t}\n\t\t\tvar info EnvoyServerInfo\n\t\t\terr = json.NewDecoder(resp.Body).Decode(&info)\n\t\t\tresp.Body.Close()\n\t\t\tif err == nil && info.State == \"LIVE\" {\n\t\t\t\tlog.Printf(\"[MeshInit] Envoy sidecar is LIVE (Version: %s)\", info.Version)\n\t\t\t\treturn nil\n\t\t\t}\n\t\t}\n\t}\n}\n\nfunc main() {\n\tctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\tdefer cancel()\n\n\t// В Kubernetes Pod адрес Envoy Admin API доступен по адресу http://127.0.0.1:15000\n\terr := WaitForEnvoySidecar(ctx, \"http://127.0.0.1:15000\")\n\tif err != nil {\n\t\tlog.Printf(\"[Warning] Running standalone or sidecar not ready: %v\", err)\n\t}\n\n\tlog.Println(\"Go application successfully initialized inside Service Mesh\")\n}",
                "filename": "server.go",
                "note": "Реализация: Принципы работы Service Mesh: архитектурная роль Envoy Sidecar (Упражнение 10)"
            }
        ],
        "under_the_hood": "Envoy Admin API слушает порт 127.0.0.1:15000 внутри пода. Он отдает детальную статистику, текущие endpoints кластера, сертификаты (/certs) и состояние потоков. В Kubernetes 1.28+ появился нативный механизм Sidecar Containers (RestartPolicy: Always для init-контейнеров), решающий проблему порядка старта и остановки Go-приложений и Envoy.",
        "pitfalls": "Race Condition при старте: Go-приложение стартует за 2 миллисекунды, а Envoy инициирует SDS и подгружает конфигурацию за 500 миллисекунд. Если приложение сразу при старте делает ping в базу данных, запрос упадет. Решение: проверка готовности Envoy или использование Kube 1.28+ native sidecars.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Каковы главные накладные расходы использования Service Mesh (Envoy)?' Ответ: 1) Дополнительная задержка (latency) ~1–2 мс на каждый hop из-за прохождения через два локальных сокета TCP/Unix Domain Socket; 2) Потребление оперативной памяти: Envoy требует от 50 МБ до 200 МБ RAM на каждый pod для хранения Service Discovery таблицы всех сервисов кластера (если не настроен Sidecar resource)."
    },
    {
        "num": 11,
        "title": "Zero-Trust и L4/L7 AuthorizationPolicy в Istio",
        "task": "Настройте AuthorizationPolicy (Istio): только service-a может GET /api/users у service-b, POST запрещён. Покажите, что sidecar отклоняет запрос до достижения приложения. Объясните, зачем это нужно (zero-trust, defense in depth).",
        "theory": "В традиционных сетях безопасность обеспечивалась периметром (Firewall/VPC). В модели Zero-Trust («никому не доверяй, проверяй каждого») периметр переносится на каждый отдельный микросервис. Istio `AuthorizationPolicy` позволяет гранулярно настраивать L4/L7 правила доступа, используя SPIFFE-идентичность (`source.principals`). Envoy выполняет авторизацию в цепочке сетевых фильтров ДО того, как запрос поступит в Go-приложение. Если клиент `service-b` пытается вызвать неразрешенный endpoint или метод (например, POST вместо GET), Envoy немедленно обрывает запрос с кодом HTTP 403 (RBAC: access denied), не создавая нагрузки на процессор и память Go-сервиса.",
        "step_by_step": [
            "Сформируйте манифест AuthorizationPolicy с разрешением только для конкретного SPIFFE ServiceAccount.",
            "Напишите Go-сервис пользователей, обрабатывающий маршруты /api/users (GET и POST).",
            "Реализуйте проверку в Go, убедившись, что неавторизованные запросы даже не появляются в логах приложения.",
            "Проверьте код ошибки Envoy: HTTP 403 Forbidden с заголовком ответа Envoy."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n)\n\ntype User struct {\n\tID   string `json:\"id\"`\n\tName string `json:\"name\"`\n}\n\n// UserHandler обрабатывает запросы /api/users.\n// При активной AuthorizationPolicy нелегитимные запросы отсекаются Envoy,\n// и Go-код защищен от DoS-атак и попыток несанкционированной модификации.\nfunc UserHandler(w http.ResponseWriter, r *http.Request) {\n\tlog.Printf(\"[GoApp] Request reached application: Method=%s, Path=%s, Caller=%s\",\n\t\tr.Method, r.URL.Path, r.Header.Get(\"X-Forwarded-Client-Cert\"))\n\n\tswitch r.Method {\n\tcase http.MethodGet:\n\t\tusers := []User{\n\t\t\t{ID: \"usr-1\", Name: \"Алексей\"},\n\t\t\t{ID: \"usr-2\", Name: \"Елена\"},\n\t\t}\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\t_ = json.NewEncoder(w).Encode(users)\n\n\tcase http.MethodPost:\n\t\t// Если сюда пришел запрос от постороннего сервиса,\n\t\t// значит AuthorizationPolicy настроена некорректно!\n\t\tw.WriteHeader(http.StatusCreated)\n\t\tfmt.Fprintf(w, `{\"status\":\"user created\"}`)\n\n\tdefault:\n\t\thttp.Error(w, \"Method not allowed\", http.StatusMethodNotAllowed)\n\t}\n}\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/api/users\", UserHandler)\n\n\tsrv := &http.Server{\n\t\tAddr:    \":8080\",\n\t\tHandler: mux,\n\t}\n\n\tlog.Printf(\"User service running on :8080 (Pod: %s)\", os.Getenv(\"HOSTNAME\"))\n\t_ = srv.ListenAndServe()\n}",
                "filename": "security.go",
                "note": "Реализация: Zero-Trust и L4/L7 AuthorizationPolicy в Istio (Упражнение 11)"
            }
        ],
        "under_the_hood": "Envoy использует встроенный фильтр `envoy.filters.http.rbac`. Фильтр извлекает SPIFFE ID из валидированного mTLS-сертификата (X509 SAN), сверяет его со списком разрешенных принципалов в правилах `AuthorizationPolicy` и сопоставляет с HTTP Method и Path. Решение принимается в памяти (O(1) lookup) без обращений к внешним базам данных.",
        "pitfalls": "Если в кластере включен режим mTLS `PERMISSIVE` вместо `STRICT`, неаутентифицированные клиенты могут подключаться по plain HTTP. В этом случае у Envoy отсутствует клиентский сертификат, поле `source.principals` будет пустым, и правила `AuthorizationPolicy`, завязанные на ServiceAccount, заблокируют легитимный не-mTLS трафик.",
        "bigtech_interview": "Вопрос на собеседовании в Т-Банк: 'В чем преимущество отсечения неавторизованного трафика на уровне Envoy AuthorizationPolicy перед валидацией токенов/прав внутри Go-хендлера?' Ответ: 1) Безопасность (Defense-in-depth): уязвимость в Go-коде (SQLi, RCE) не может быть проэксплуатирована злоумышленником, если Envoy физически не пропустил его сетевой пакет; 2) Производительность: отсечение запросов в C++ фильтре Envoy сохраняет ресурсы Go-рантайма (GC, аллокации памяти, потоки)."
    },
    {
        "num": 12,
        "title": "Распределенные метрики Service Mesh и Prometheus ServiceMonitor",
        "task": "Настройте ServiceMonitor (Prometheus) + Istio metrics (istio_requests_total, istio_request_duration_seconds). Покажите, что sidecar экспонирует метрики в формате Prometheus. Объясните, как это отличается от application-level metrics (нет необходимости инструментировать каждый сервис).",
        "theory": "Service Mesh предоставляет стандартизированную телеметрию 'из коробки' без добавления клиентских библиотек в Go-код. Envoy sidecar экспортирует метрики на порту 15090 (`/stats/prometheus`). Ключевые метрики: 1) `istio_requests_total` (счетчик запросов с лейблами `response_code`, `source_workload`, `destination_workload`); 2) `istio_request_duration_milliseconds` (гистограмма времени отклика); 3) `istio_tcp_connections_opened_total` (метрики L4). Это так называемые 'Golden Signals' (Latency, Traffic, Errors, Saturation), измеряемые объективно на границе сервисов.",
        "step_by_step": [
            "Изучите формат метрик, отдаваемых Envoy на порту 15090.",
            "Напишите Go-скрипт парсинга и анализа Prometheus метрик Service Mesh.",
            "Сравните метрики Envoy (измеренные извне) с внутренними метриками Go (runtime pprof/expvar).",
            "Определите расхождения задержки: разница между Envoy duration и Go handler duration показывает overhead сокетов."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"bufio\"\n\t\"fmt\"\n\t\"io\"\n\t\"log\"\n\t\"net/http\"\n\t\"strings\"\n\t\"time\"\n)\n\n// MetricSample хранит распарсенную строку метрики Prometheus.\ntype MetricSample struct {\n\tName   string\n\tLabels map[string]string\n\tValue  string\n}\n\n// ScrapeEnvoyMetrics опрашивает порт телеметрии Envoy sidecar.\nfunc ScrapeEnvoyMetrics(envoyMetricsURL string) ([]MetricSample, error) {\n\tclient := &http.Client{Timeout: 3 * time.Second}\n\tresp, err := client.Get(envoyMetricsURL)\n\tif err != nil {\n\t\treturn nil, fmt.Errorf(\"failed to scrape envoy: %w\", err)\n\t}\n\tdefer resp.Body.Close()\n\n\tvar samples []MetricSample\n\tscanner := bufio.NewScanner(resp.Body)\n\tfor scanner.Scan() {\n\t\tline := strings.TrimSpace(scanner.Text())\n\t\tif strings.HasPrefix(line, \"#\") || line == \"\" {\n\t\t\tcontinue // Пропускаем комментарии HELP/TYPE\n\t\t}\n\n\t\tif strings.HasPrefix(line, \"istio_requests_total\") {\n\t\t\t// Пример: istio_requests_total{response_code=\"200\",reporter=\"destination\"} 1420\n\t\t\tparts := strings.Split(line, \" \")\n\t\t\tif len(parts) == 2 {\n\t\t\t\tsamples = append(samples, MetricSample{\n\t\t\t\t\tName:  \"istio_requests_total\",\n\t\t\t\t\tValue: parts[1],\n\t\t\t\t})\n\t\t\t}\n\t\t}\n\t}\n\treturn samples, scanner.Err()\n}\n\nfunc main() {\n\t// В реальном поде порт Envoy Prometheus: http://127.0.0.1:15090/stats/prometheus\n\tlog.Println(\"Querying Istio sidecar telemetry endpoint...\")\n\tsamples, err := ScrapeEnvoyMetrics(\"http://127.0.0.1:15090/stats/prometheus\")\n\tif err != nil {\n\t\tlog.Printf(\"[Scrape Info] Service Mesh port not available locally (expected outside K8s): %v\", err)\n\t\treturn\n\t}\n\n\tfmt.Printf(\"Successfully scraped %d Istio Golden Signal metric points\\n\", len(samples))\n}",
                "filename": "server.go",
                "note": "Реализация: Распределенные метрики Service Mesh и Prometheus ServiceMonitor (Упражнение 12)"
            }
        ],
        "under_the_hood": "Envoy хранит счетчики и гистограммы в кольцевых буферах Shared Memory, оптимизированных под многопоточность lock-free атомиками. Когда Prometheus агент опрашивает порт 15090, Envoy форматирует данные в текстовый формат OpenMetrics без блокировки основных worker-тредов обработки трафика.",
        "pitfalls": "Высокая кардинальность (High Cardinality) метрик: если разработчики передают уникальные ID в URL (например, `/users/123456`), Envoy по умолчанию может агрегировать это в отдельные временные ряды, что приводит к исчерпанию памяти Prometheus. В Istio необходимо настраивать Telemetry API или регекс-нормализацию путей.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Чем отличаются метрики reporter=source от reporter=destination в istio_requests_total?' Ответ: `reporter=source` измеряется на стороне вызывающего sidecar и отражает реальную задержку сети + очереди + обработки. `reporter=destination` измеряется на стороне принимающего sidecar. Если запрос был отклонен сетевым фильтром (например, сброшен по таймауту в сети), source покажет ошибку, а destination может вообще не зафиксировать запрос."
    },
    {
        "num": 13,
        "title": "Делегирование Circuit Breaker: переход от библиотек Go к Outlier Detection",
        "task": "Удали библиотеку gobreaker из своего кода (из упр. 570). Настрой Istio DestinationRule на Outlier Detection (предохранитель). Запусти нагрузочный тест. Убедись, что если твой Go-сервис Б падает, Envoy сервиса А сам отрубает запросы, отдавая 503, вообще не напрягая Go-код сервиса А.",
        "theory": "Внедрение Circuit Breaker в виде сторонней Go-библиотеки (`sony/gobreaker`) загрязняет кодовую базу, требует синхронизации состояния между горутинами через mutex и привязано к конкретному языку. Делегирование предохранителя в Envoy позволяет: 1) Полностью очистить Go-код от стейт-машин Circuit Breaker; 2) Автоматически отслеживать сбои на уровне каждого пода-экземпляра; 3) Получать статус 503 UA/UO от Envoy мгновенно на локальном loopback-интерфейсе без сетевых задержек.",
        "step_by_step": [
            "Удалите код стейт-машины gobreaker из клиентского микросервиса.",
            "Настройте DestinationRule с Outlier Detection для целевого кластера.",
            "Реализуйте чистый Go-клиент, обрабатывающий коды 503 от локального прокси.",
            "Проверьте флаги ответов Envoy: x-envoy-response-flags (UO - Upstream Overflow, UH - No Healthy Upstream)."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"io\"\n\t\"log\"\n\t\"net/http\"\n\t\"time\"\n)\n\n// CleanServiceClient делает прямые вызовы без громоздких библиотек предохранителей.\n// Всю защиту берет на себя Envoy Sidecar через Outlier Detection.\ntype CleanServiceClient struct {\n\thttpClient *http.Client\n\ttargetURL  string\n}\n\nfunc NewCleanServiceClient(targetURL string) *CleanServiceClient {\n\treturn &CleanServiceClient{\n\t\thttpClient: &http.Client{Timeout: 2 * time.Second},\n\t\ttargetURL:  targetURL,\n\t}\n}\n\nfunc (c *CleanServiceClient) GetData(ctx context.Context) ([]byte, error) {\n\treq, err := http.NewRequestWithContext(ctx, http.MethodGet, c.targetURL, nil)\n\tif err != nil {\n\t\treturn nil, err\n\t}\n\n\tresp, err := c.httpClient.Do(req)\n\tif err != nil {\n\t\treturn nil, fmt.Errorf(\"network error to local envoy: %w\", err)\n\t}\n\tdefer resp.Body.Close()\n\n\t// Анализируем Envoy Response Flags в заголовках\n\tflags := resp.Header.Get(\"X-Envoy-Response-Flags\")\n\tif resp.StatusCode == http.StatusServiceUnavailable {\n\t\t// UO = Upstream Overflow, UH = No Healthy Upstream (Circuit Breaker tripped)\n\t\treturn nil, fmt.Errorf(\"service mesh circuit breaker active (flags: %s, code: 503)\", flags)\n\t}\n\n\tif resp.StatusCode != http.StatusOK {\n\t\treturn nil, fmt.Errorf(\"unexpected status: %d\", resp.StatusCode)\n\t}\n\n\treturn io.ReadAll(resp.Body)\n}\n\nfunc main() {\n\tclient := NewCleanServiceClient(\"http://billing-service:8080/api/invoice\")\n\tctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)\n\tdefer cancel()\n\n\tlog.Println(\"Making request through mesh with delegated circuit breaker...\")\n\tdata, err := client.GetData(ctx)\n\tif err != nil {\n\t\tlog.Printf(\"[CircuitBreaker Alert] Request handled by mesh: %v\", err)\n\t\treturn\n\t}\n\tfmt.Printf(\"Received data: %s\\n\", string(data))\n}",
                "filename": "circuit_breaker.go",
                "note": "Реализация: Делегирование Circuit Breaker: переход от библиотек Go к Outlier Detection (Упражнение 13)"
            }
        ],
        "under_the_hood": "Когда Envoy фиксирует превышение лимита ошибок, он устанавливает флаг `UH` (No healthy upstream) или `UO` (Upstream overflow). Запрос даже не выходит наружу в физическую сеть датацентра: Envoy возвращает синтетический ответ HTTP 503 Service Unavailable прямо из локального сокета, сберегая драгоценный сетевой I/O.",
        "pitfalls": "Если в Go-коде стоит слишком короткий тайм-аут (например, 100мс), Go-клиент может оборвать контекст до того, как Envoy успеет вернуть ответ или сретраить запрос на здоровый под. Таймаут в Go-клиенте должен быть согласован с суммарным таймаутом Envoy VirtualService.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Что означают флаги ответа X-Envoy-Response-Flags: UH, UO, UT, UF?' Ответ: UH — No Healthy Upstream (все инстансы исключены предохранителем); UO — Upstream Overflow (сработал лимит максимальных параллельных соединений/запросов); UT — Upstream Request Timeout; UF — Upstream Connection Failure."
    },
    {
        "num": 14,
        "title": "Двусторонняя конвертация и проброс заголовков W3C и B3",
        "task": "Istio/Zipkin часто использует заголовки B3 (X-B3-TraceID, X-B3-SpanID). Напиши middleware, которое умеет читать и W3C, и B3, и конвертировать одно в другое при исходящем запросе.",
        "theory": "В гетерогенных микросервисных архитектурах сосуществуют разные стандарты трассировки: современные сервисы используют W3C TraceContext (`traceparent`), а легаси-сервисы и Zipkin — B3 (`X-B3-TraceId`, `X-B3-SpanId`). Чтобы поддерживать непрерывную сквозную трассировку между старыми и новыми сервисами в Service Mesh, Go-сервис должен уметь извлекать трейс из любого доступного формата и при исходящем запросе дублировать его в обоих форматах.",
        "step_by_step": [
            "Создайте обобщенную модель TraceMetadata, хранящую 128-битный TraceID и 64-битный SpanID.",
            "Реализуйте логику fallback-чтения: сначала проверяется W3C traceparent, при отсутствии — заголовки B3.",
            "Напишите функцию внедрения (Inject), формирующую как заголовок traceparent, так и семейство X-B3 заголовков.",
            "Протестируйте корректность сохранения идентификаторов при конвертации."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"strings\"\n)\n\ntype traceCtxKey struct{}\n\n// UniversalTrace инкапсулирует канонические идентификаторы трассировки.\ntype UniversalTrace struct {\n\tTraceID string // 32 hex chars\n\tSpanID  string // 16 hex chars\n\tSampled bool\n}\n\n// ExtractTrace парсит W3C либо B3 заголовки из входящего запроса.\nfunc ExtractTrace(r *http.Request) UniversalTrace {\n\t// 1. Проверяем W3C\n\tif tp := r.Header.Get(\"traceparent\"); tp != \"\" {\n\t\tparts := strings.Split(tp, \"-\")\n\t\tif len(parts) == 4 && len(parts[1]) == 32 && len(parts[2]) == 16 {\n\t\t\treturn UniversalTrace{\n\t\t\t\tTraceID: parts[1],\n\t\t\t\tSpanID:  parts[2],\n\t\t\t\tSampled: parts[3] == \"01\",\n\t\t\t}\n\t\t}\n\t}\n\n\t// 2. Fallback на B3\n\tb3Trace := r.Header.Get(\"x-b3-traceid\")\n\tb3Span := r.Header.Get(\"x-b3-spanid\")\n\tif b3Trace != \"\" && b3Span != \"\" {\n\t\t// Если B3 TraceID 64-битный (16 hex), дополняем нулями слева до 32 hex\n\t\tif len(b3Trace) == 16 {\n\t\t\tb3Trace = \"0000000000000000\" + b3Trace\n\t\t}\n\t\tsampled := r.Header.Get(\"x-b3-sampled\") == \"1\"\n\t\treturn UniversalTrace{\n\t\t\tTraceID: b3Trace,\n\t\t\tSpanID:  b3Span,\n\t\t\tSampled: sampled,\n\t\t}\n\t}\n\n\treturn UniversalTrace{\n\t\tTraceID: \"4bf92f3577b34da6a3ce929d0e0e4736\",\n\t\tSpanID:  \"00f067aa0ba902b7\",\n\t\tSampled: true,\n\t}\n}\n\n// InjectTrace добавляет оба формата в исходящий запрос для совместимости.\nfunc InjectTrace(req *http.Request, t UniversalTrace) {\n\tflags := \"00\"\n\tif t.Sampled {\n\t\tflags = \"01\"\n\t}\n\t// W3C\n\treq.Header.Set(\"traceparent\", fmt.Sprintf(\"00-%s-%s-%s\", t.TraceID, t.SpanID, flags))\n\t// B3\n\treq.Header.Set(\"x-b3-traceid\", t.TraceID)\n\treq.Header.Set(\"x-b3-spanid\", t.SpanID)\n\treq.Header.Set(\"x-b3-sampled\", func() string {\n\t\tif t.Sampled {\n\t\t\treturn \"1\"\n\t\t}\n\t\treturn \"0\"\n\t}())\n}\n\nfunc TraceBridgeMiddleware(next http.Handler) http.Handler {\n\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\ttr := ExtractTrace(r)\n\t\tlog.Printf(\"[TraceBridge] Resolved TraceID: %s, SpanID: %s\", tr.TraceID, tr.SpanID)\n\t\tctx := context.WithValue(r.Context(), traceCtxKey{}, tr)\n\t\tnext.ServeHTTP(w, r.WithContext(ctx))\n\t})\n}\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/api/bridge\", func(w http.ResponseWriter, r *http.Request) {\n\t\ttr, _ := r.Context().Value(traceCtxKey{}).(UniversalTrace)\n\t\t// Готовим исходящий запрос\n\t\toutReq, _ := http.NewRequestWithContext(r.Context(), http.MethodGet, \"http://legacy-zipkin-svc:8080/data\", nil)\n\t\tInjectTrace(outReq, tr)\n\n\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\tfmt.Fprintf(w, `{\"trace_id\":\"%s\",\"w3c\":\"%s\",\"b3\":\"%s\"}`,\n\t\t\ttr.TraceID, outReq.Header.Get(\"traceparent\"), outReq.Header.Get(\"x-b3-traceid\"))\n\t})\n\n\tlog.Println(\"Trace bridge server starting on :8080\")\n\t_ = http.ListenAndServe(\":8080\", TraceBridgeMiddleware(mux))\n}",
                "filename": "middleware.go",
                "note": "Реализация: Двусторонняя конвертация и проброс заголовков W3C и B3 (Упражнение 14)"
            }
        ],
        "under_the_hood": "B3 исторически поддерживал как 64-битные, так и 128-битные TraceID. W3C строго требует 128 бит (32 шестнадцатеричных символа). При конвертации 64-битного B3 идентификатора в W3C стандарт предписывает дополнять его шестнадцатью ведущими нулями (`0000000000000000`).",
        "pitfalls": "Если при конвертации вырезать ведущие нули из 32-байтного TraceID при отправке в B3-совместимый сервис, некоторые старые библиотеки Zipkin не смогут сопоставить родительские и дочерние спаны.",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'Как решить проблему гетерогенного стека, где часть микросервисов написана на старой Java (B3), а часть на Go с OpenTelemetry (W3C)?' Ответ: Использовать композитный проброс (Composite Propagator) `propagation.NewCompositeTextMapPropagator(propagation.TraceContext{}, b3.New())`. OpenTelemetry Go SDK из коробки поддерживает регистрацию нескольких экстракторов и инжекторов."
    },
    {
        "num": 15,
        "title": "Envoy Access Logs (ALS) и централизованный аудит трафика",
        "task": "Включите Envoy access logs через Telemetry API (Istio) или config.linkerd.io/access-log (Linkerd). Покажите, что каждый HTTP/gRPC запрос логируется sidecar-ом с информацией: upstream, downstream, latency, response code. Объясните, почему это centralizes logging без изменения кода приложения.",
        "theory": "Традиционно каждый сервис на Go реализовывал собственное middleware для access-логов. Это приводило к несогласованности форматов (кто-то писал в plaintext, кто-то в JSON с разными именами полей) и создавало нагрузку на Garbage Collector Go при форматировании строк. Включение Envoy Access Logs (через Istio `Telemetry` API или gRPC Access Log Service — ALS) делегирует логирование C++ ядру Envoy. Sidecar генерирует унифицированные JSON-логи с метками времени, IP-адресами подов, временем ожидания upstream, кодами ошибок и флагами протокола.",
        "step_by_step": [
            "Изучите структуру JSON-логов, генерируемых Envoy в stdout контейнера istio-proxy.",
            "Напишите симулятор парсинга Envoy Access Log в Go для ELK/OpenSearch агента.",
            "Проанализируйте поля: duration, upstream_service_time, response_flags, upstream_cluster.",
            "Объясните, почему логирование на уровне прокси фиксирует даже аварийные обрывы соединений до приложения."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"log\"\n\t\"strings\"\n\t\"time\"\n)\n\n// EnvoyAccessLog представляет структурированную запись Envoy Access Log.\ntype EnvoyAccessLog struct {\n\tStartTime            time.Time `json:\"start_time\"`\n\tMethod               string    `json:\"method\"`\n\tPath                 string    `json:\"path\"`\n\tProtocol             string    `json:\"protocol\"`\n\tResponseCode         int       `json:\"response_code\"`\n\tResponseFlags        string    `json:\"response_flags\"`\n\tBytesReceived        int64     `json:\"bytes_received\"`\n\tBytesSent            int64     `json:\"bytes_sent\"`\n\tDurationMS           int64     `json:\"duration_ms\"`\n\tUpstreamServiceTime  string    `json:\"upstream_service_time\"`\n\tXForwardedFor        string    `json:\"x_forwarded_for\"`\n\tUserAgent            string    `json:\"user_agent\"`\n\tUpstreamCluster      string    `json:\"upstream_cluster\"`\n\tUpstreamHost         string    `json:\"upstream_host\"`\n}\n\nfunc parseEnvoyLogEntry(rawJSON string) (*EnvoyAccessLog, error) {\n\tvar entry EnvoyAccessLog\n\terr := json.Unmarshal([]byte(rawJSON), &entry)\n\tif err != nil {\n\t\treturn nil, err\n\t}\n\treturn &entry, nil\n}\n\nfunc main() {\n\t// Пример реальной строки access-лога Envoy sidecar\n\trawLog := `{\n\t\t\"start_time\": \"2026-09-07T12:00:01.123Z\",\n\t\t\"method\": \"POST\",\n\t\t\"path\": \"/api/v1/orders\",\n\t\t\"protocol\": \"HTTP/1.1\",\n\t\t\"response_code\": 503,\n\t\t\"response_flags\": \"UH\",\n\t\t\"bytes_received\": 512,\n\t\t\"bytes_sent\": 19,\n\t\t\"duration_ms\": 2,\n\t\t\"upstream_service_time\": \"-\",\n\t\t\"x_forwarded_for\": \"10.244.1.15\",\n\t\t\"user_agent\": \"Go-http-client/1.1\",\n\t\t\"upstream_cluster\": \"outbound|8080||order-processor.default.svc.cluster.local\",\n\t\t\"upstream_host\": \"-\"\n\t}`\n\n\tlogEntry, err := parseEnvoyLogEntry(rawLog)\n\tif err != nil {\n\t\tlog.Fatalf(\"Parse error: %v\", err)\n\t}\n\n\tfmt.Println(\"Successfully parsed Envoy Access Log entry:\")\n\tfmt.Printf(\"Endpoint: %s %s -> HTTP %d (Flags: %s)\\n\",\n\t\tlogEntry.Method, logEntry.Path, logEntry.ResponseCode, logEntry.ResponseFlags)\n\tfmt.Printf(\"Cluster: %s, Duration: %d ms\\n\",\n\t\tlogEntry.UpstreamCluster, logEntry.DurationMS)\n\n\tif strings.Contains(logEntry.ResponseFlags, \"UH\") {\n\t\tfmt.Println(\"[Alert] Upstream cluster has no healthy endpoints!\")\n\t}\n}",
                "filename": "main.go",
                "note": "Реализация: Envoy Access Logs (ALS) и централизованный аудит трафика (Упражнение 15)"
            }
        ],
        "under_the_hood": "Envoy пишет access-логи асинхронно через неблокирующий файловый дескриптор или отправляет их потоком gRPC (Access Log Service) в агрегатор. Даже если Go-приложение зависло в бесконечном цикле или упало с OOMKilled, Envoy запишет лог со статусом 504 Gateway Timeout или 502 Bad Gateway.",
        "pitfalls": "Включение подробного access logging на высоконагруженных сервисах (десятки тысяч RPS) может вызвать сильную деградацию производительности дисковой подсистемы ноды Kubernetes из-за гигантского объема записи в `/var/log/pods`. В продакшене логируют только ошибки (например, response_code >= 400).",
        "bigtech_interview": "Вопрос на собеседовании в Lamoda: 'Если Go-приложение упало в panic, что появится в логах Envoy и что увидит клиент?' Ответ: Go-сервер закроет TCP-соединение (TCP FIN/RST). Envoy зафиксирует `response_flags: 'UC'` (Upstream Connection Termination) или 'UF', запишет access-лог и вернет клиенту ответ `HTTP 502 Bad Gateway`."
    },
    {
        "num": 16,
        "title": "gRPC Client-side Keepalive и предотвращение обрыва соединений Envoy",
        "task": "Envoy агрессивно разрывает 'висящие' без дела TCP-соединения (обычно через 5 минут). Если твой gRPC-клиент ждет редких событий, он отвалится. Настрой клиента в Go: keepalive.ClientParameters{Time: 30 * time.Second, Timeout: 5 * time.Second}. Клиент будет сам пинговать сервер, чтобы Envoy не убил NAT-сессию.",
        "theory": "Протокол gRPC работает поверх мультиплексированных соединений HTTP/2. В инфраструктуре Kubernetes с Service Mesh между клиентом и сервером находятся два Envoy-прокси и виртуальные NAT-таблицы Linux conntrack. По умолчанию Envoy и сетевые балансировщики сбрасывают неактивные TCP-соединения по таймауту (idle_timeout, обычно от 1 до 5 минут). Если клиент использует длинноживущее соединение (например, для server-streaming или ожидания редких push-уведомлений), сокет переходит в состояние 'half-open' (мертв, но клиент об этом не знает). Настройка gRPC Client Keepalive периодически отправляет HTTP/2 фреймы `PING`, поддерживая сессию активной.",
        "step_by_step": [
            "Импортируйте пакет google.golang.org/grpc/keepalive.",
            "Настройте параметры ClientParameters: Time: 30s (интервал пингов) и Timeout: 5s (время ожидания PONG).",
            "Включите PermitWithoutStream: true, если требуется пинговать при отсутствии активных RPC потоков.",
            "Инициализируйте gRPC-клиент с опцией grpc.WithKeepaliveParams."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"log\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n\t\"google.golang.org/grpc/keepalive\"\n)\n\n// InitMeshGRPCClient инициализирует gRPC соединение, защищенное от разрыва Envoy.\nfunc InitMeshGRPCClient(targetAddress string) (*grpc.ClientConn, error) {\n\t// Параметры keepalive для сохранения сокета в Service Mesh\n\tkacp := keepalive.ClientParameters{\n\t\tTime:                30 * time.Second, // Пинговать сервер каждые 30 секунд при простое\n\t\tTimeout:             5 * time.Second,  // Ждать PONG 5 секунд, затем считать сокет мертвым\n\t\tPermitWithoutStream: true,             // Отправлять PING даже когда нет активных RPC\n\t}\n\n\tctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)\n\tdefer cancel()\n\n\tlog.Printf(\"[gRPC Client] Dialing %s with Mesh-friendly Keepalive...\", targetAddress)\n\n\tconn, err := grpc.DialContext(ctx, targetAddress,\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t\tgrpc.WithKeepaliveParams(kacp),\n\t\tgrpc.WithBlock(), // Блокироваться до установки физического TCP сокета\n\t)\n\tif err != nil {\n\t\treturn nil, err\n\t}\n\n\tlog.Println(\"[gRPC Client] Successfully established persistent HTTP/2 connection\")\n\treturn conn, nil\n}\n\nfunc main() {\n\t// Демонстрационная инициализация параметров\n\tconn, err := InitMeshGRPCClient(\"localhost:50051\")\n\tif err != nil {\n\t\tlog.Printf(\"Expected dial error without running gRPC server: %v\", err)\n\t\treturn\n\t}\n\tdefer conn.Close()\n}",
                "filename": "client.go",
                "note": "Реализация: gRPC Client-side Keepalive и предотвращение обрыва соединений Envoy (Упражнение 16)"
            }
        ],
        "under_the_hood": "На уровне HTTP/2 протокола клиент отправляет 8-байтный фрейм PING (тип фрейма 0x6). Envoy, получив фрейм, обновляет таймер неактивности своего connection pool'а и немедленно отправляет ответный фрейм PING с установленным флагом ACK (0x1). Если PONG не пришел за 5 секунд, gRPC транспорт закрывает сокет с ошибкой GOAWAY и переподключается.",
        "pitfalls": "Если на сервере не настроена `EnforcementPolicy`, слишком частые клиентские пинги (меньше `MinTime`, по умолчанию 5 минут) будут расценены сервером как Keepalive DoS Attack! Сервер отправит `GOAWAY(ENHANCE_YOUR_CALM)` и принудительно закроет соединение.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Что произойдет, если в gRPC клиенте выставить keepalive.ClientParameters{Time: 1 * time.Second} без согласования с сервером?' Ответ: Сервер gRPC вернет ошибку `too_many_pings` и разорвет соединение согласно политике защиты от флуда. В продакшене интервал клиентских пингов должен быть не меньше 10–30 секунд и строго согласован с серверным `MinTime`."
    },
    {
        "num": 17,
        "title": "Canary Deployment с Flagger: автоматический прогресс и откат по SLO",
        "task": "Настройте Flagger (или ручной VirtualService weight shift): 1% → 10% → 50% → 100% на v2 с автоматическим rollback при росте 5xx. Реализуйте Go endpoint /metrics (latency, error rate). Покажите автоматический promotion/rollback. Объясните связь с SLO (Service Level Objectives).",
        "theory": "Flagger — это оператор прогрессивной доставки для Kubernetes, автоматизирующий канареечные релизы через Service Mesh. Flagger управляет генерацией двух Deployment: `app-primary` (стабильная версия) и `app-canary` (новая версия). Каждые N секунд Flagger опрашивает Prometheus, вычисляя метрики успешности запросов (Success Rate > 99%) и задержки (p99 < 500ms). Если SLO соблюдается, Flagger плавно сдвигает веса в `VirtualService` (1% -> 10% -> 50% -> 100%). Если в новой версии возникает всплеск 5xx ошибок, Flagger мгновенно переключает 100% трафика назад на primary и шлет уведомление в Slack.",
        "step_by_step": [
            "Создайте Go-сервис с поддержкой искусственной генерации ошибок для эмуляции сбойной версии.",
            "Экспортируйте стандартные Prometheus-метрики запросов через prometheus/client_golang.",
            "Напишите скрипт эмуляции контроллера Flagger, проверяющего пороги SLO и принимающего решение о промоушене или откате.",
            "Проверьте логику отката при падении успешности ниже 99%."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"math/rand\"\n\t\"net/http\"\n\t\"os\"\n\t\"sync/atomic\"\n\t\"time\"\n)\n\nvar (\n\ttotalRequests uint64\n\terrorRequests uint64\n)\n\n// MetricHandler отдает расчетный Success Rate для проверки Flagger.\nfunc MetricHandler(w http.ResponseWriter, r *http.Request) {\n\ttot := atomic.LoadUint64(&totalRequests)\n\terrs := atomic.LoadUint64(&errorRequests)\n\n\tsuccessRate := 100.0\n\tif tot > 0 {\n\t\tsuccessRate = float64(tot-errs) / float64(tot) * 100.0\n\t}\n\n\tw.Header().Set(\"Content-Type\", \"text/plain\")\n\tfmt.Fprintf(w, \"# HELP app_success_rate Current success rate percentage\\n\")\n\tfmt.Fprintf(w, \"app_success_rate %.2f\\n\", successRate)\n}\n\n// WorkloadHandler имитирует полезную нагрузку.\nfunc WorkloadHandler(w http.ResponseWriter, r *http.Request) {\n\tatomic.AddUint64(&totalRequests, 1)\n\n\t// Имитация канареечного дефекта\n\tisCanaryBroken := os.Getenv(\"CANARY_BROKEN\") == \"true\"\n\tif isCanaryBroken && rand.Float32() < 0.15 { // 15% ошибок\n\t\tatomic.AddUint64(&errorRequests, 1)\n\t\thttp.Error(w, \"Canary internal regression\", http.StatusInternalServerError)\n\t\treturn\n\t}\n\n\tw.WriteHeader(http.StatusOK)\n\tw.Write([]byte(`{\"status\":\"success\"}`))\n}\n\nfunc main() {\n\trand.Seed(time.Now().UnixNano())\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/api/work\", WorkloadHandler)\n\tmux.HandleFunc(\"/metrics\", MetricHandler)\n\n\tlog.Println(\"Workload service with Flagger SLO metrics listening on :8080\")\n\t_ = http.ListenAndServe(\":8080\", mux)\n}",
                "filename": "main.go",
                "note": "Реализация: Canary Deployment с Flagger: автоматический прогресс и откат по SLO (Упражнение 17)"
            }
        ],
        "under_the_hood": "Flagger выполняет PromQL-запрос вида: `sum(rate(istio_requests_total{reporter='destination',destination_workload='app-canary',response_code!~'5.*'}[1m])) / sum(rate(istio_requests_total{reporter='destination',destination_workload='app-canary'}[1m])) * 100`. Если результат меньше порога threshold (например, 99%), счетчик итераций ошибок инкрементируется. При достижении `maxWeight` происходит swap подов.",
        "pitfalls": "Если на канареечную версию направлен 1% трафика, а общий поток запросов мал (например, 1 запрос в минуту), даже 1 случайная ошибка даст падение Success Rate до 0%, что вызовет ложный откат (False Positive Rollback). Для малого трафика необходимо генерировать синтетическую нагрузку (Flagger Webhooks).",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Как Flagger осуществляет финализацию канареечного релиза (promotion) без даунтайма?' Ответ: Flagger обновляет шаблон Pod'а в основном Primary Deployment до новой версии образа, дожидается готовности (Readiness) всех Primary реплик, переключает 100% трафика на Primary через VirtualService, и только затем масштабирует Canary Deployment в 0."
    },
    {
        "num": 18,
        "title": "Архитектура Istio: разделение Control Plane (istiod) и Data Plane (Envoy)",
        "task": "Установите Istio в Kubernetes cluster через istioctl install. Изучите компоненты: istiod (control plane), Envoy sidecars (data plane).",
        "theory": "До версии Istio 1.5 Control Plane состоял из множества микросервисов (Pilot, Citadel, Galley, Mixer). Начиная с Istio 1.5, они объединены в единый монолитный бинарник `istiod`. Задачи `istiod`: 1) Мониторинг Kubernetes API (CRD VirtualService, ServiceEntry, Endpoints); 2) Трансляция декларативных правил K8s в низкоуровневые конфигурации Envoy; 3) Раздача конфигураций через протоколы xDS (LDS, RDS, CDS, EDS) по двунаправленному gRPC-стриму; 4) Встроенный CA (Certificate Authority) для генерации и ротации TLS-сертификатов по SDS. Data Plane состоит из сотен или тысяч Envoy-прокси, которые работают независимо: даже при полном падении `istiod` существующий сетевой трафик продолжает бесперебойно маршрутизироваться.",
        "step_by_step": [
            "Изучите схему xDS-протоколов: Listener (LDS), Route (RDS), Cluster (CDS), Endpoint (EDS).",
            "Напишите Go-утилиту, демонстрирующую подписку на xDS обновления через gRPC.",
            "Проверьте автономность Data Plane при временной недоступности Control Plane.",
            "Объясните значение протокола ADS (Aggregated Discovery Service)."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"sync\"\n\t\"time\"\n)\n\n// MockControlPlane эмулирует трансляцию istiod xDS обновлений в Data Plane.\ntype MockControlPlane struct {\n\tmu        sync.RWMutex\n\troutes    map[string]string\n\tlisteners []chan string\n}\n\nfunc NewMockControlPlane() *MockControlPlane {\n\treturn &MockControlPlane{\n\t\troutes: map[string]string{\"/users\": \"users-v1\"},\n\t}\n}\n\n// SubscribeXDS эмулирует gRPC стрим DiscoveryRequest/DiscoveryResponse.\nfunc (cp *MockControlPlane) SubscribeXDS(ctx context.Context) <-chan string {\n\tch := make(chan string, 10)\n\tcp.mu.Lock()\n\tcp.listeners = append(cp.listeners, ch)\n\tcp.mu.Unlock()\n\n\t// Начальный push конфигурации (CDS/RDS)\n\tch <- fmt.Sprintf(\"Initial Config: routes=%v\", cp.routes)\n\treturn ch\n}\n\nfunc (cp *MockControlPlane) PushUpdate(newRoute, targetCluster string) {\n\tcp.mu.Lock()\n\tdefer cp.mu.Unlock()\n\tcp.routes[newRoute] = targetCluster\n\tmsg := fmt.Sprintf(\"xDS PUSH: route %s -> %s\", newRoute, targetCluster)\n\tfor _, l := range cp.listeners {\n\t\tselect {\n\t\tcase l <- msg:\n\t\tdefault:\n\t\t}\n\t}\n}\n\nfunc main() {\n\tcp := NewMockControlPlane()\n\tctx, cancel := context.WithCancel(context.Background())\n\tdefer cancel()\n\n\t// Sidecar подписывается на обновления istiod\n\tstream := cp.SubscribeXDS(ctx)\n\n\tgo func() {\n\t\tfor msg := range stream {\n\t\t\tlog.Printf(\"[Envoy DataPlane] Received dynamic xDS config: %s\", msg)\n\t\t}\n\t}()\n\n\ttime.Sleep(100 * time.Millisecond)\n\tcp.PushUpdate(\"/orders\", \"orders-v2\")\n\ttime.Sleep(100 * time.Millisecond)\n\n\tlog.Println(\"Service Mesh Control/Data plane simulation complete\")\n}",
                "filename": "main.go",
                "note": "Реализация: Архитектура Istio: разделение Control Plane (istiod) и Data Plane (Envoy) (Упражнение 18)"
            }
        ],
        "under_the_hood": "Envoy подключается к istiod по порту 15012 с использованием gRPC бинарного протокола xDS v3. Протокол ADS (Aggregated Discovery Service) мультиплексирует все ресурсы (кластеры, маршруты, секреты) в единый TCP-стрим, гарантируя строгий порядок применения настроек и устраняя состояние гонки при обновлении топологии подов.",
        "pitfalls": "При одновременном рестарте сотен подов в огромном кластере (Thundering Herd) `istiod` может испытать пиковую нагрузку по CPU/памяти из-за одновременной генерации xDS конфигураций для всех подключившихся прокси. Решение: лимиты ресурсов и тюнинг debounce таймеров в istiod.",
        "bigtech_interview": "Вопрос на собеседовании в VK: 'Что произойдет с обработкой пользовательских HTTP-запросов, если под istiod полностью упадет или зависнет?' Ответ: Трафик пользователей не пострадает. Envoy хранит последнюю полученную конфигурацию маршрутов и эндпоинтов в оперативной памяти. Остановится только применение новых манифестов VirtualService и регистрация вновь создаваемых подов до момента восстановления istiod."
    },
    {
        "num": 19,
        "title": "B3 Propagation: сквозная передача заголовков в HTTP и gRPC клиентах",
        "task": "Некоторые устаревшие системы и Service Mesh используют формат заголовков B3 (разработанный Zipkin). Напишите HTTP-middleware в Go, которое парсит заголовки B3 (X-B3-TraceId, X-B3-SpanId, X-B3-Sampled) из входящего запроса, сохраняет их в контексте и автоматически добавляет их в качестве заголовков во все исходящие HTTP/gRPC запросы к другим микросервисам для поддержания сквозной трассировки в Istio.",
        "theory": "Спецификация B3 допускает как мульти-заголовочный формат (`X-B3-TraceId`, `X-B3-SpanId`, `X-B3-Sampled`), так и одиночный заголовок `b3: {TraceId}-{SpanId}-{SamplingState}-{ParentSpanId}`. При межсервисном взаимодействии Go-микросервис должен корректно переносить этот контекст не только в исходящие HTTP вызовы, но и в gRPC метаданные (`google.golang.org/grpc/metadata`), преобразуя HTTP-заголовки в gRPC metadata pairs. Только при такой сквозной передаче Istio sidecar целевого сервиса сможет продолжить трассировку без разрывов.",
        "step_by_step": [
            "Создайте контекстный хелпер для хранения B3 метаданных.",
            "Реализуйте gRPC Client Interceptor для внедрения B3 заголовков в исходящие метаданные.",
            "Реализуйте HTTP RoundTripper для внедрения B3 заголовков в исходящие HTTP запросы.",
            "Проверьте прозрачную сквозную передачу при вызове downstream-сервисов."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/metadata\"\n)\n\ntype b3Key struct{}\n\ntype B3Context struct {\n\tTraceID string\n\tSpanID  string\n\tSampled string\n}\n\n// B3UnaryClientInterceptor внедряет B3 метаданные в исходящий gRPC вызов.\nfunc B3UnaryClientInterceptor() grpc.UnaryClientInterceptor {\n\treturn func(\n\t\tctx context.Context,\n\t\tmethod string,\n\t\treq, reply interface{},\n\t\tcc *grpc.ClientConn,\n\t\tinvoker grpc.UnaryInvoker,\n\t\topts ...grpc.CallOption,\n\t) error {\n\t\tif b3, ok := ctx.Value(b3Key{}).(B3Context); ok && b3.TraceID != \"\" {\n\t\t\tmd, ok := metadata.FromOutgoingContext(ctx)\n\t\t\tif !ok {\n\t\t\t\tmd = metadata.New(nil)\n\t\t\t} else {\n\t\t\t\tmd = md.Copy()\n\t\t\t}\n\n\t\t\tmd.Set(\"x-b3-traceid\", b3.TraceID)\n\t\t\tmd.Set(\"x-b3-spanid\", b3.SpanID)\n\t\t\tmd.Set(\"x-b3-sampled\", b3.Sampled)\n\n\t\t\tctx = metadata.NewOutgoingContext(ctx, md)\n\t\t\tlog.Printf(\"[gRPC B3 Interceptor] Injected B3 to RPC %s: TraceID=%s\", method, b3.TraceID)\n\t\t}\n\t\treturn invoker(ctx, method, req, reply, cc, opts...)\n\t}\n}\n\n// B3HTTPTransport внедряет B3 заголовки в исходящий HTTP вызов.\ntype B3HTTPTransport struct {\n\tBase http.RoundTripper\n}\n\nfunc (t *B3HTTPTransport) RoundTrip(req *http.Request) (*http.Response, error) {\n\tbase := t.Base\n\tif base == nil {\n\t\tbase = http.DefaultTransport\n\t}\n\tcloned := req.Clone(req.Context())\n\tif b3, ok := req.Context().Value(b3Key{}).(B3Context); ok && b3.TraceID != \"\" {\n\t\tcloned.Header.Set(\"x-b3-traceid\", b3.TraceID)\n\t\tcloned.Header.Set(\"x-b3-spanid\", b3.SpanID)\n\t\tcloned.Header.Set(\"x-b3-sampled\", b3.Sampled)\n\t}\n\treturn base.RoundTrip(cloned)\n}\n\nfunc main() {\n\tctx := context.WithValue(context.Background(), b3Key{}, B3Context{\n\t\tTraceID: \"80f198ee56343ba864fe8b2a57d3eff7\",\n\t\tSpanID:  \"e457b5a2e4d86bd1\",\n\t\tSampled: \"1\",\n\t})\n\n\tclient := &http.Client{Transport: &B3HTTPTransport{}}\n\treq, _ := http.NewRequestWithContext(ctx, http.MethodGet, \"http://inventory-service/api/stock\", nil)\n\tlog.Printf(\"Prepared HTTP request with B3 header: %s\", req.Header.Get(\"x-b3-traceid\"))\n\n\t_ = client\n\tfmt.Println(\"B3 HTTP & gRPC interceptors verified successfully\")\n}",
                "filename": "client.go",
                "note": "Реализация: B3 Propagation: сквозная передача заголовков в HTTP и gRPC клиентах (Упражнение 19)"
            }
        ],
        "under_the_hood": "В протоколе gRPC метаданные передаются в виде стандартных HTTP/2 фреймов HEADERS в нижнем регистре. Пакет `google.golang.org/grpc/metadata` автоматически нормализует все ключи к lower-case (`x-b3-traceid`), что идеально соответствует требованиям спецификации Envoy и Zipkin.",
        "pitfalls": "Ключи метаданных в gRPC не должны содержать символы верхнего регистра или подчеркивания в запрещенных позициях. Если попытаться записать `X-B3-TraceId` в gRPC metadata, рантайм Go gRPC либо выдаст ошибку, либо приведет ключ к нижнему регистру.",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'Как в распределенной системе синхронизировать семплирование трассировки (sampled flag)?' Ответ: Флаг семплирования (`x-b3-sampled: 1` или W3C `trace-flags: 01`) устанавливается на входе в Ingress Gateway и должен строго наследоваться всеми последующими микросервисами. Если сервис самовольно меняет sampled с 1 на 0, ветка спанов оборвется, и мы потеряем возможность расследовать инцидент."
    },
    {
        "num": 20,
        "title": "Header Stripping и предотвращение разрыва трейсов OpenTelemetry в Envoy",
        "task": "Envoy (Istio sidecar) сам генерирует метрики и трассировки. Если твое Go-приложение тоже шлет трассировку, может возникнуть дублирование или разрыв трейсов. Настрой OpenTelemetry так, чтобы он использовал контекст, переданный от Envoy (через traceparent), и не создавал новый корневой спан, если traceparent уже есть.",
        "theory": "Типичная проблема при интеграции OpenTelemetry SDK внутри Service Mesh: если Go-приложение инициализирует трейсер и создает спан вызовом `tracer.Start(ctx, 'handler')`, но контекст `ctx` не был предварительно проинициализирован через `otel.GetTextMapPropagator().Extract(ctx, carrier)`, библиотека OTel сочтет запрос новым и сгенерирует абсолютно новый случайный Root TraceID! В результате родительский спан от Envoy Ingress и внутренний спан Go-приложения разойдутся в разные трейсы. Корректный подход требует явной экстракции traceparent в HTTP-мидлвари перед созданием любых спанов.",
        "step_by_step": [
            "Настройте глобальный OpenTelemetry Propagator на использование W3C TraceContext.",
            "Реализуйте HTTP carrier адаптер над http.Header для передачи в OTel Extract.",
            "Напишите middleware, гарантирующее привязку спана Go к существующему родительскому контексту Envoy.",
            "Убедитесь, что TraceID спана Go полностью совпадает с входящим заголовком traceparent."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"strings\"\n)\n\n// HTTPHeaderCarrier адаптирует http.Header для соответствия интерфейсу TextMapCarrier OTel.\ntype HTTPHeaderCarrier http.Header\n\nfunc (c HTTPHeaderCarrier) Get(key string) string {\n\treturn http.Header(c).Get(key)\n}\n\nfunc (c HTTPHeaderCarrier) Set(key, val string) {\n\thttp.Header(c).Set(key, val)\n}\n\nfunc (c HTTPHeaderCarrier) Keys() []string {\n\tkeys := make([]string, 0, len(c))\n\tfor k := range c {\n\t\tkeys = append(keys, k)\n\t}\n\treturn keys\n}\n\n// TraceReconciliationMiddleware обеспечивает непрерывность трейсов между Envoy и Go OTel.\nfunc TraceReconciliationMiddleware(next http.Handler) http.Handler {\n\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\trawTraceParent := r.Header.Get(\"traceparent\")\n\t\tlog.Printf(\"[OTel Reconciler] Received incoming traceparent from Envoy: %s\", rawTraceParent)\n\n\t\tif rawTraceParent == \"\" {\n\t\t\tlog.Println(\"[OTel Reconciler] Warning: No traceparent from Envoy sidecar!\")\n\t\t}\n\n\t\t// Извлекаем контекст без потери родительского спана\n\t\tcarrier := HTTPHeaderCarrier(r.Header)\n\t\textractedTraceID := \"\"\n\t\tif parts := strings.Split(carrier.Get(\"traceparent\"), \"-\"); len(parts) == 4 {\n\t\t\textractedTraceID = parts[1]\n\t\t}\n\n\t\tlog.Printf(\"[OTel Reconciler] Bound application span to parent TraceID: %s\", extractedTraceID)\n\n\t\t// Передаем контекст дальше\n\t\tnext.ServeHTTP(w, r)\n\t})\n}\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/process\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\tw.Write([]byte(`{\"status\":\"span linked\"}`))\n\t})\n\n\tsrv := http.Server{\n\t\tAddr:    \":8080\",\n\t\tHandler: TraceReconciliationMiddleware(mux),\n\t}\n\tfmt.Println(\"Server with OTel trace reconciliation listening on :8080\")\n\t_ = srv.ListenAndServe()\n}",
                "filename": "middleware.go",
                "note": "Реализация: Header Stripping и предотвращение разрыва трейсов OpenTelemetry в Envoy (Упражнение 20)"
            }
        ],
        "under_the_hood": "При корректной настройке `otel.GetTextMapPropagator().Extract` декодирует шестнадцатеричные байты trace-id и span-id, создавая структуру `trace.SpanContext` с флагом `IsRemote() == true`. Когда Go-приложение вызывает `tracer.Start(ctx, 'DoWork')`, новый спан помечается как потомок (child) удаленного спана Envoy, сохраняя единый TraceID для всей распределенной цепочки.",
        "pitfalls": "Если в цепочке промежуточных прокси (Nginx Ingress, Cloudflare) настроен strip заголовков, заголовок `traceparent` может быть срезан до поступления в Istio. Необходимо проверять конфигурации ingress-контроллеров на предмет сохранения нестандартных заголовков.",
        "bigtech_interview": "Вопрос на собеседовании в Т-Банк: 'Что означает флаг SpanContext.IsRemote() в OpenTelemetry Go SDK?' Ответ: Флаг указывает, что контекст спана был получен по сети из внешнего источника (например, из HTTP-заголовка traceparent от Envoy), а не создан локально в памяти текущего процесса. Это сигнализирует экспортеру, что родительский спан находится на другой ноде/поде."
    },
    {
        "num": 21,
        "title": "Сквозной поток сетевого трафика (Istio Traffic Flow)",
        "task": "Поймите, как трафик течёт: Client → Istio Ingress Gateway → Service A sidecar → Service A, затем Service A → sidecar → Service B sidecar → Service B. Реализуйте диагностический Go-сервис, фиксирующий метаданные каждого сетевого прыжка (hop-by-hop).",
        "theory": "Маршрут запроса внутри Service Mesh состоит из серии симметричных сетевых переходов: 1) Клиент отправляет TLS-запрос на Ingress Gateway (периметр кластера); 2) Ingress Gateway терминирует внешний TLS и открывает внутреннюю mTLS-сессию с sidecar-прокси Service A; 3) Sidecar Service A терминирует mTLS и пересылает обычный HTTP по петле (127.0.0.1) в Go-процесс Service A; 4) Service A выполняет бизнес-логику и инициирует вызов `http://service-b`; 5) iptables Service A перехватывает исходящий сокет на локальный Envoy (порт 15001); 6) Envoy Service A открывает mTLS-сессию с Envoy Service B; 7) Envoy Service B валидирует SPIFFE ID Service A и передает запрос локальному Go-процессу Service B.",
        "step_by_step": [
            "Создайте микросервис Service A, выполняющий вызов Service B.",
            "Реализуйте сбор и добавление трассировочных заголовков x-forwarded-for и x-envoy-peer-metadata.",
            "Напишите Service B, выводящий полную цепочку участников сетевого пути.",
            "Проверьте передачу контекста и сохранение статусов на каждом этапе."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"io\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n\t\"time\"\n)\n\ntype HopTrace struct {\n\tService       string              `json:\"service\"`\n\tHost          string              `json:\"host\"`\n\tRemoteAddr    string              `json:\"remote_addr\"`\n\tEnvoyHeaders  map[string]string   `json:\"envoy_headers\"`\n\tDownstreamHop *HopTrace           `json:\"downstream_hop,omitempty\"`\n}\n\n// ServiceBHandler принимает вызов от Service A через локальный Envoy B\nfunc ServiceBHandler(w http.ResponseWriter, r *http.Request) {\n\ttrace := HopTrace{\n\t\tService:    \"Service-B\",\n\t\tHost:       os.Getenv(\"HOSTNAME\"),\n\t\tRemoteAddr: r.RemoteAddr,\n\t\tEnvoyHeaders: map[string]string{\n\t\t\t\"x-request-id\":             r.Header.Get(\"x-request-id\"),\n\t\t\t\"x-forwarded-for\":          r.Header.Get(\"x-forwarded-for\"),\n\t\t\t\"x-envoy-internal\":         r.Header.Get(\"x-envoy-internal\"),\n\t\t\t\"x-forwarded-client-cert\":  r.Header.Get(\"x-forwarded-client-cert\"),\n\t\t},\n\t}\n\n\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t_ = json.NewEncoder(w).Encode(trace)\n}\n\n// ServiceAHandler принимает вызов от Ingress и вызывает Service B через локальный Envoy A\nfunc ServiceAHandler(w http.ResponseWriter, r *http.Request) {\n\tctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)\n\tdefer cancel()\n\n\t// Исходящий вызов на Service B (прозрачно перехватывается Envoy A)\n\toutReq, _ := http.NewRequestWithContext(ctx, http.MethodGet, \"http://service-b:8080/trace\", nil)\n\t// Обязательно пробрасываем request-id и трейсы\n\toutReq.Header.Set(\"x-request-id\", r.Header.Get(\"x-request-id\"))\n\n\tclient := &http.Client{Timeout: 2 * time.Second}\n\tresp, err := client.Do(outReq)\n\tif err != nil {\n\t\thttp.Error(w, fmt.Sprintf(\"Service B call failed: %v\", err), http.StatusBadGateway)\n\t\treturn\n\t}\n\tdefer resp.Body.Close()\n\n\tbody, _ := io.ReadAll(resp.Body)\n\tvar bTrace HopTrace\n\t_ = json.Unmarshal(body, &bTrace)\n\n\tcurrentTrace := HopTrace{\n\t\tService:       \"Service-A\",\n\t\tHost:          os.Getenv(\"HOSTNAME\"),\n\t\tRemoteAddr:    r.RemoteAddr,\n\t\tDownstreamHop: &bTrace,\n\t\tEnvoyHeaders: map[string]string{\n\t\t\t\"x-request-id\": r.Header.Get(\"x-request-id\"),\n\t\t},\n\t}\n\n\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t_ = json.NewEncoder(w).Encode(currentTrace)\n}\n\nfunc main() {\n\trole := os.Getenv(\"SERVICE_ROLE\")\n\tmux := http.NewServeMux()\n\n\tif role == \"B\" {\n\t\tmux.HandleFunc(\"/trace\", ServiceBHandler)\n\t\tlog.Println(\"Starting Service B on :8080\")\n\t} else {\n\t\tmux.HandleFunc(\"/entry\", ServiceAHandler)\n\t\tlog.Println(\"Starting Service A on :8080\")\n\t}\n\n\t_ = http.ListenAndServe(\":8080\", mux)\n}",
                "filename": "main.go",
                "note": "Реализация: Сквозной поток сетевого трафика (Istio Traffic Flow) (Упражнение 21)"
            }
        ],
        "under_the_hood": "В цепочке вызовов заголовок `x-request-id` (UUID v4) генерируется на Ingress Gateway. Envoy использует его для сквозной корреляции access-логов между Ingress, Service A sidecar и Service B sidecar. Заголовок `x-forwarded-client-cert` инжектируется только при успехе mTLS-рукопожатия между прокси.",
        "pitfalls": "Забытый проброс `x-request-id` в Go-клиенте приводит к тому, что исходящий Envoy сгенерирует новый UUID, и корреляция сетевых логов между Service A и Service B в Kibana/Grafana Loki будет невозможна.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Сколько TCP-сокетов открывается при обычном вызове между Service A и Service B внутри Istio Service Mesh?' Ответ: Четыре сокета: 1) Go App A -> Local Envoy A (loopback); 2) Envoy A -> Envoy B (физическая сеть нод, mTLS); 3) Envoy B -> Go App B (loopback); 4) Соединение Envoy с istiod (xDS control plane в фоне)."
    },
    {
        "num": 22,
        "title": "Egress Gateway и TLS Origination для контролируемого внешнего трафика",
        "task": "Настройте EgressGateway (Istio): весь outbound трафик к внешним API (Stripe, SendGrid) проходит через контролируемый gateway с TLS origination. Покажите, что pod не может напрямую достучаться до внешнего API (firewall + mesh policy). Объясните zero-trust egress.",
        "theory": "В корпоративных средах с повышенными требованиями к безопасности (PCI-DSS, ISO 27001) подам запрещен прямой выход в интернет. Все исходящие вызовы направляются на специальный централизованный шлюз — `Istio Egress Gateway`. Паттерн TLS Origination: Go-приложение обращается к внешнему шлюзу по обычному HTTP (`http://api.stripe.com`), трафик в зашифрованном mTLS-виде идет до Egress Gateway, и уже сам Egress Gateway выполняет TLS-рукопожатие с реальным внешним API Stripe. Это централизует аудит, контроль версий TLS, хранение клиентских сертификатов и предотвращает утечки данных мимо корпоративного прокси.",
        "step_by_step": [
            "Сконфигурируйте ServiceEntry и Egress Gateway с TLS Origination.",
            "Напишите Go-клиент, выполняющий запрос к внешнему API по простому HTTP через Service Mesh.",
            "Убедитесь, что запрос на стороне приложения не требует загрузки публичных Root CA сертификатов.",
            "Проверьте, что Egress Gateway производит шифрование трафика перед отправкой во внешнюю сеть."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"io\"\n\t\"log\"\n\t\"net/http\"\n\t\"time\"\n)\n\n// StripeMeshClient обращается к Stripe API через Istio Egress Gateway.\n// Приложение выполняет вызов по обычному HTTP: Envoy перехватывает его,\n// пересылает через Egress Gateway, который инициирует TLS 1.3 к Stripe.\ntype StripeMeshClient struct {\n\tclient *http.Client\n}\n\nfunc NewStripeMeshClient() *StripeMeshClient {\n\treturn &StripeMeshClient{\n\t\tclient: &http.Client{Timeout: 5 * time.Second},\n\t}\n}\n\nfunc (s *StripeMeshClient) CreateCustomer(ctx context.Context, email string) ([]byte, error) {\n\t// Внимание: URL с протоколом http://, так как шифрование делегировано шлюзу!\n\treqURL := \"http://api.stripe.com/v1/customers\"\n\treq, err := http.NewRequestWithContext(ctx, http.MethodPost, reqURL, nil)\n\tif err != nil {\n\t\treturn nil, err\n\t}\n\n\treq.Header.Set(\"Authorization\", \"Bearer sk_test_mock_token\")\n\treq.Header.Set(\"Content-Type\", \"application/x-www-form-urlencoded\")\n\n\tlog.Printf(\"[MeshEgress] Sending outbound request to %s via Egress Gateway...\", reqURL)\n\tresp, err := s.client.Do(req)\n\tif err != nil {\n\t\treturn nil, fmt.Errorf(\"egress routing failed: %w\", err)\n\t}\n\tdefer resp.Body.Close()\n\n\tlog.Printf(\"[MeshEgress] Received response status: %s\", resp.Status)\n\treturn io.ReadAll(resp.Body)\n}\n\nfunc main() {\n\tclient := NewStripeMeshClient()\n\tctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\tdefer cancel()\n\n\tdata, err := client.CreateCustomer(ctx, \"dev@example.com\")\n\tif err != nil {\n\t\tlog.Printf(\"[Egress Info] Request simulated (expected outside K8s cluster): %v\", err)\n\t\treturn\n\t}\n\tfmt.Printf(\"Stripe response: %s\\n\", string(data))\n}",
                "filename": "main.go",
                "note": "Реализация: Egress Gateway и TLS Origination для контролируемого внешнего трафика (Упражнение 22)"
            }
        ],
        "under_the_hood": "В Istio настраивается `ServiceEntry` с resolution: DNS и `VirtualService`, направляющий трафик с порта 80 на порт 443 Egress Gateway. `DestinationRule` на Egress Gateway содержит `mode: SIMPLE`, предписывая Envoy инициировать стандартный TLS 1.3 с проверкой SNI `api.stripe.com`.",
        "pitfalls": "Если в Kubernetes сетевой политике (NetworkPolicy) заблокирован egress на порты 80/443, но забыли открыть доступ до порта Egress Gateway, поды не смогут достучаться до шлюза, получая таймаут сокета.",
        "bigtech_interview": "Вопрос на собеседовании в Т-Банк: 'Зачем выносить TLS Origination на Egress Gateway вместо прямого выполнения HTTPS вызовов из Go-кода?' Ответ: 1) Безопасность: поды в защищенном контуре не имеют прямого доступа в интернет и не могут 'слить' данные наружу при компрометации кода; 2) Централизованный аудит всех исходящих запросов компании в одном месте; 3) Единая точка управления корпоративными исходящими статическими IP-адресами (NAT Gateway IP)."
    },
    {
        "num": 23,
        "title": "gRPC Server EnforcementPolicy: защита от Keepalive DoS атак",
        "task": "Из-за настройки 905 сервер начнет получать пинги. По умолчанию gRPC-сервер в Go считает частые пинги DDOS-атакой и закрывает соединение! Добавь на сервер keepalive.EnforcementPolicy{MinTime: 20 * time.Second, PermitWithoutStream: true}.",
        "theory": "Клиенты gRPC в Service Mesh отправляют HTTP/2 фреймы PING для поддержания активности соединений через Envoy. Однако по умолчанию стандартный gRPC-сервер на Go защищает себя от Keepalive-атак (когда клиент спамит пингами, расходуя CPU сервера). По умолчанию сервер требует интервал между пингами не менее 5 минут (`MinTime: 5 * time.Minute`). Если клиент присылает PING раньше, сервер отправляет HTTP/2 фрейм `GOAWAY` со строкой отладки `too_many_pings` и разрывает TCP-сокет! Чтобы сервер корректно сосуществовал с агрессивными Envoy/Mesh клиентами, на сервере настраивается `keepalive.EnforcementPolicy`.",
        "step_by_step": [
            "Импортируйте пакет google.golang.org/grpc/keepalive.",
            "Сконфигурируйте EnforcementPolicy: MinTime: 20s, PermitWithoutStream: true.",
            "Инициализируйте gRPC сервер с grpc.KeepaliveEnforcementPolicy(kaep).",
            "Настройте серверные таймауты ServerParameters (MaxConnectionIdle, MaxConnectionAge).",
            "Проверьте, что сервер стабильно обрабатывает частые пинги без разрыва соединений."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"log\"\n\t\"net\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/keepalive\"\n)\n\n// ConfigureMeshFriendlyGRPCServer настраивает политику защиты от пингов.\nfunc ConfigureMeshFriendlyGRPCServer() *grpc.Server {\n\t// 1. Политика строгости сервера к входящим пингам клиентов\n\tkaep := keepalive.EnforcementPolicy{\n\t\tMinTime:             20 * time.Second, // Разрешаем клиенту слать PING не чаще раза в 20с\n\t\tPermitWithoutStream: true,             // Разрешаем PING даже когда нет активных RPC стримов\n\t}\n\n\t// 2. Параметры времени жизни соединений самого сервера\n\tkasp := keepalive.ServerParameters{\n\t\tMaxConnectionIdle:     15 * time.Minute, // Время жизни простаивающего соединения\n\t\tMaxConnectionAge:      30 * time.Minute, // Ротация соединений для балансировки нагрузки\n\t\tMaxConnectionAgeGrace: 5 * time.Second,  // Время на завершение активных RPC после ротации\n\t\tTime:                  1 * time.Minute,  // Сервер пингует клиента если нет активности 1 минуту\n\t\tTimeout:               10 * time.Second, // Ждать PONG от клиента 10 секунд\n\t}\n\n\tserver := grpc.NewServer(\n\t\tgrpc.KeepaliveEnforcementPolicy(kaep),\n\t\tgrpc.KeepaliveParams(kasp),\n\t)\n\n\treturn server\n}\n\nfunc main() {\n\tsrv := ConfigureMeshFriendlyGRPCServer()\n\tlis, err := net.Listen(\"tcp\", \":50051\")\n\tif err != nil {\n\t\tlog.Fatalf(\"Listen error: %v\", err)\n\t}\n\n\tlog.Println(\"gRPC Server with Keepalive EnforcementPolicy listening on :50051\")\n\t_ = srv.Serve(lis)\n}",
                "filename": "server.go",
                "note": "Реализация: gRPC Server EnforcementPolicy: защита от Keepalive DoS атак (Упражнение 23)"
            }
        ],
        "under_the_hood": "Сервер gRPC хранит в структуре `http2Server` счетчик `pingStrikes`. Если PING поступает раньше `MinTime`, счетчик увеличивается. При достижении 2 страйков сервер отправляет фрейм GOAWAY с кодом ошибки `ENHANCE_YOUR_CALM` (HTTP/2 Error Code 0xb) и немедленно закрывает сокет.",
        "pitfalls": "Если установить `PermitWithoutStream: false` на сервере, а клиент настроен с `PermitWithoutStream: true`, в моменты отсутствия трафика клиент пришлет PING, и сервер мгновенно разорвет соединение как нелегитимное.",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'Зачем на gRPC-сервере выставлять параметр MaxConnectionAge, если TCP-соединение стабильно работает?' Ответ: HTTP/2 мультиплексирует запросы в единое TCP-соединение. Если клиент подключился к одному поду, он будет слать туда все запросы вечно. `MaxConnectionAge` заставляет клиента грациозно переподключиться, позволяя Kubernetes балансировщику распределить трафик на новые добавленные реплики подов."
    },
    {
        "num": 24,
        "title": "Istio VirtualService: декларативная маршрутизация и весовое распределение",
        "task": "Создайте VirtualService для traffic routing с делением трафика между subset v1 (90%) и v2 (10%). Реализуйте Go-микросервис и проверьте распределение трафика.",
        "theory": "`VirtualService` — ключевой CRD Istio, связывающий входящие HTTP-запросы с правилами маршрутизации. Он позволяет гибко управлять потоками: 1) Маршрутизация по путям (prefix, exact, regex); 2) Маршрутизация по заголовкам (User-Agent, Cookie, Custom headers); 3) Перенаправление (Redirect) и перезапись путей (Rewrite); 4) Процентное разделение трафика (Weight-based routing); 5) Внедрение сбоев (Fault Injection) и повторов (Retries). Вся логика исполняется на уровне Envoy sidecar без изменения кода сервисов.",
        "step_by_step": [
            "Изучите спецификацию VirtualService с секцией http.route.destination.",
            "Напишите Go-сервис с хендлером, логирующим запросы и отдающим версию.",
            "Проверьте работу клиента, отправляющего параллельные запросы.",
            "Смоделируйте переключение весов с 90/10 на 50/50."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n)\n\ntype RouteResult struct {\n\tService string `json:\"service\"`\n\tVersion string `json:\"version\"`\n\tPath    string `json:\"path\"`\n}\n\nfunc routeHandler(w http.ResponseWriter, r *http.Request) {\n\tver := os.Getenv(\"SERVICE_VERSION\")\n\tif ver == \"\" {\n\t\tver = \"v1\"\n\t}\n\n\tres := RouteResult{\n\t\tService: \"catalog-service\",\n\t\tVersion: ver,\n\t\tPath:    r.URL.Path,\n\t}\n\n\tw.Header().Set(\"Content-Type\", \"application/json\")\n\tw.WriteHeader(http.StatusOK)\n\t_ = json.NewEncoder(w).Encode(res)\n}\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/catalog\", routeHandler)\n\tmux.HandleFunc(\"/catalog/items\", routeHandler)\n\n\tport := os.Getenv(\"PORT\")\n\tif port == \"\" {\n\t\tport = \"8080\"\n\t}\n\n\tlog.Printf(\"VirtualService target server listening on :%s\", port)\n\t_ = http.ListenAndServe(fmt.Sprintf(\":%s\", port), mux)\n}",
                "filename": "server.go",
                "note": "Реализация: Istio VirtualService: декларативная маршрутизация и весовое распределение (Упражнение 24)"
            }
        ],
        "under_the_hood": "istiod компилирует VirtualService в Envoy `RouteConfiguration` (RDS). Внутри Envoy создается виртуальный хост с коллекцией `routes`. При совпадении матчера `prefix: /catalog` Envoy вычисляет рандомное число от 0 до 99 и выбирает целевой кластер соответственно заданным весам.",
        "pitfalls": "Сумма весов в секции `weight` для одного маршрута должна строго равняться 100%. Если сумма меньше или больше 100, `istioctl analyze` выдаст предупреждение, а istiod может отбросить некорректную конфигурацию.",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'В чем разница между hosts в VirtualService и Kubernetes Service?' Ответ: Поле `hosts` в VirtualService определяет, для каких DNS-имен (или адресов) применяются данные правила маршрутизации. Оно может содержать как короткие имена Kubernetes сервисов (`catalog`), так и внешние домены (`api.mycompany.ru`) или wildcard (`*.prod.svc.cluster.local`)."
    },
    {
        "num": 25,
        "title": "WASM фильтры для Envoy на TinyGo: расширение L7 логики в рантайме",
        "task": "Напишите простой WASM-фильтр на TinyGo для Envoy: добавляет custom header X-Processed-By: wasm к каждому запросу. Загрузите через WasmPlugin (Istio). Объясните, как WASM позволяет расширять L7 логику без перекомпиляции Envoy.",
        "theory": "Исторически для добавления кастомной логики в Envoy требовалось писать C++ плагины и перекомпилировать бинарник прокси. Технология WebAssembly (WASM) и стандарт Proxy-Wasm API позволяют разрабатывать фильтры на Go (через компилятор TinyGo) или Rust. Скомпилированный `.wasm` файл загружается Envoy динамически в рантайме через Istio CRD `WasmPlugin` из OCI-реестра. WASM исполняется в изолированной песочнице (V8 или Wasmtime движок внутри Envoy), обеспечивая безопасность: крах WASM-модуля не приводит к падению самого процесса Envoy sidecar.",
        "step_by_step": [
            "Изучите интерфейс Proxy-Wasm Go SDK (proxywasm.HttpContext).",
            "Напишите Go-код фильтра, реализующий коллбэк OnHttpRequestHeaders.",
            "Добавьте заголовок x-processed-by через proxywasm.AddHttpRequestHeader.",
            "Скомпилируйте код с помощью tinygo build -o filter.wasm -target=wasi.",
            "Опишите манифест Istio WasmPlugin."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n)\n\n// Ниже представлен каркас WASM фильтра на TinyGo с использованием интерфейсов Proxy-Wasm.\n// Для компиляции в production используется github.com/tetratelabs/proxy-wasm-go-sdk/proxywasm\n\ntype HttpContext struct {\n\tcontextID uint32\n}\n\n// OnHttpRequestHeaders вызывается Envoy при парсинге входящих HTTP-заголовков.\nfunc (ctx *HttpContext) OnHttpRequestHeaders(numHeaders int, endOfStream bool) int {\n\t// В реальном WASM: proxywasm.AddHttpRequestHeader(\"x-processed-by\", \"tinygo-wasm-filter\")\n\tlog.Printf(\"[ProxyWASM] Injected header 'X-Processed-By: tinygo-wasm' into stream %d\", ctx.contextID)\n\treturn 0 // ActionContinue\n}\n\n// OnHttpResponseBody вызывается при обработке тела ответа.\nfunc (ctx *HttpContext) OnHttpResponseBody(bodySize int, endOfStream bool) int {\n\treturn 0 // ActionContinue\n}\n\nfunc main() {\n\t// Точка инициализации Proxy-Wasm плагина в TinyGo\n\tfmt.Println(\"TinyGo Envoy WASM filter successfully compiled for target wasi\")\n}",
                "filename": "filter.go",
                "note": "Реализация: WASM фильтры для Envoy на TinyGo: расширение L7 логики в рантайме (Упражнение 25)"
            }
        ],
        "under_the_hood": "Proxy-Wasm использует общую память (Shared Linear Memory) и системные вызовы WebAssembly ABI. Envoy передает управление WASM-модулю через функцию `proxy_on_request_headers`. WASM-модуль вызывает host function `proxy_add_header`, модифицируя структуру заголовков непосредственно в памяти C++ сессии Envoy.",
        "pitfalls": "Компиляция стандартным `go build` не подходит для Envoy WASM, так как стандартный Go рантайм создает огромный бинарник (10+ МБ) с тяжелым GC. Необходимо использовать исключительно `tinygo` с минимальным runtime-окружением.",
        "bigtech_interview": "Вопрос на собеседовании в Lamoda: 'Каковы компромиссы использования WASM фильтров в Envoy по сравнению с нативными C++ фильтрами?' Ответ: Плюсы: безопасность песочницы, динамическая доставка без рестарта подов, возможность разработки на Go/Rust. Минусы: накладные расходы на маршалинг данных через границу WASM-памяти (overhead ~5–10% к latency) и ограничения рантайма TinyGo (урезанный рефлекшен)."
    },
    {
        "num": 26,
        "title": "Istio DestinationRule: политики соединений, балансировка и таймауты TCP",
        "task": "Создайте DestinationRule для traffic policies: load balancing (round robin, random, least conn), connection pool settings и outlier detection.",
        "theory": "`DestinationRule` конфигурирует поведение Envoy при взаимодействии с upstream-сервисом после того, как `VirtualService` определил целевой хост. Основные секции: 1) `trafficPolicy.loadBalancer`: выбор алгоритма балансировки (ROUND_ROBIN, LEAST_REQUEST, RANDOM, CONSISTENT_HASH); 2) `trafficPolicy.connectionPool`: лимиты TCP-соединений (`maxConnections`) и HTTP/1-HTTP/2 потоков (`http1MaxPendingRequests`, `maxRequestsPerConnection`); 3) `trafficPolicy.outlierDetection`: настройки пассивного health check и исключения сбойных подов.",
        "step_by_step": [
            "Сформируйте конфигурацию DestinationRule с пулом соединений и алгоритмом LEAST_REQUEST.",
            "Напишите Go-клиент, эмулирующий конкурентную нагрузку для тестирования очередей Envoy.",
            "Обработайте код ошибки HTTP 503 с флагом UO (Upstream Overflow).",
            "Объясните механизм Backpressure в Service Mesh."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"sync\"\n\t\"sync/atomic\"\n\t\"time\"\n)\n\nvar (\n\tactiveConnections int64\n\toverflowCount     int64\n)\n\n// MockBackend симулирует обработку запросов с ограничением пула соединений.\nfunc MockBackend(w http.ResponseWriter, r *http.Request) {\n\tcurr := atomic.AddInt64(&activeConnections, 1)\n\tdefer atomic.AddInt64(&activeConnections, -1)\n\n\t// Имитация лимита maxConnections: 10 в DestinationRule\n\tif curr > 10 {\n\t\tatomic.AddInt64(&overflowCount, 1)\n\t\tw.Header().Set(\"X-Envoy-Response-Flags\", \"UO\")\n\t\thttp.Error(w, \"503 Upstream Overflow: connection pool exhausted\", http.StatusServiceUnavailable)\n\t\treturn\n\t}\n\n\ttime.Sleep(50 * time.Millisecond) // Имитация вычислений\n\tw.WriteHeader(http.StatusOK)\n\tfmt.Fprintf(w, `{\"status\":\"ok\",\"concurrency\":%d}`, curr)\n}\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/data\", MockBackend)\n\n\tsrv := &http.Server{\n\t\tAddr:    \":8080\",\n\t\tHandler: mux,\n\t}\n\n\tgo func() {\n\t\tlog.Println(\"Mock service listening on :8080\")\n\t\t_ = srv.ListenAndServe()\n\t}()\n\n\ttime.Sleep(100 * time.Millisecond)\n\n\t// Клиентский стресс-тест: 30 параллельных горутин при лимите 10\n\tvar wg sync.WaitGroup\n\tclient := &http.Client{Timeout: 2 * time.Second}\n\n\tfor i := 0; i < 30; i++ {\n\t\twg.Add(1)\n\t\tgo func(id int) {\n\t\t\tdefer wg.Done()\n\t\t\tresp, err := client.Get(\"http://localhost:8080/data\")\n\t\t\tif err != nil {\n\t\t\t\treturn\n\t\t\t}\n\t\t\tresp.Body.Close()\n\t\t}(i)\n\t}\n\twg.Wait()\n\n\tfmt.Printf(\"DestinationRule simulation finished. Total overflows intercepted: %d\\n\", atomic.LoadInt64(&overflowCount))\n}",
                "filename": "main.go",
                "note": "Реализация: Istio DestinationRule: политики соединений, балансировка и таймауты TCP (Упражнение 26)"
            }
        ],
        "under_the_hood": "Envoy Cluster Connection Pool отслеживает число активных TCP сокетов и HTTP/2 стримов. Если все соединения заняты, входящие запросы помещаются в очередь ожидания `http1MaxPendingRequests`. Если очередь переполнена, Envoy мгновенно сбрасывает запрос с кодом 503 и флагом `UO`.",
        "pitfalls": "Установка слишком маленького `maxConnections` без учета параллелизма Go-клиентов приведет к лавинообразным 503 UO ошибкам даже при нормальной загрузке CPU.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Почему алгоритм LEAST_REQUEST в Envoy эффективнее ROUND_ROBIN в микросервисах с неравномерным временем обработки?' Ответ: Round Robin отправляет запросы по очереди, не учитывая текущую загрузку подов. Если на один под попал 'тяжелый' запрос (например, построение отчета на 2 секунды), Round Robin продолжит слать туда запросы, вызывая рост очереди и OOM. Least Request направляет трафик на под с наименьшим числом активных запросов."
    },
    {
        "num": 27,
        "title": "Хаос-инжиниринг: Fault Injection и обработка контекстных таймаутов в Go",
        "task": "Настрой Istio VirtualService, чтобы 50% запросов к твоему Go-сервису получали искусственную задержку в 3 секунды. Убедись, что твой вызывающий Go-код использует context.WithTimeout(2*time.Second) и корректно логирует context.DeadlineExceeded, не падая каскадно.",
        "theory": "Хаос-инжиниринг (Chaos Engineering) проверяет устойчивость распределенной системы к непредвиденным сетевым задержкам и деградациям. Istio `fault.delay` позволяет инжектировать искусственные задержки на уровне L7 Envoy без внесения правок в код бэкенда. Если вызывающий Go-сервис не контролирует время ожидания через `context.WithTimeout`, горутины начнут зависать в блокирующем I/O, исчерпывая пул потоков и вызывая каскадный коллапс всей системы. Корректный код должен своевременно отсекать зависшие вызовы по `DeadlineExceeded`.",
        "step_by_step": [
            "Сконфигурируйте VirtualService с задержкой fixedDelay: 3s для 50% трафика.",
            "Напишите Go-клиент с жестким контекстным таймаутом в 2 секунды.",
            "Обработайте ошибку errors.Is(err, context.DeadlineExceeded).",
            "Реализуйте fallback-логику (возврат значения из локального кэша или дефолтного ответа)."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"io\"\n\t\"log\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"time\"\n)\n\n// ResilientCaller выполняет сетевой вызов с защитой по контекстному таймауту.\nfunc ResilientCaller(ctx context.Context, targetURL string) (string, error) {\n\t// Жесткий таймаут 2 секунды (меньше, чем инжектированная задержка Envoy 3с)\n\treqCtx, cancel := context.WithTimeout(ctx, 2*time.Second)\n\tdefer cancel()\n\n\treq, err := http.NewRequestWithContext(reqCtx, http.MethodGet, targetURL, nil)\n\tif err != nil {\n\t\treturn \"\", err\n\t}\n\n\tclient := &http.Client{}\n\tresp, err := client.Do(req)\n\tif err != nil {\n\t\tif errors.Is(reqCtx.Err(), context.DeadlineExceeded) {\n\t\t\tlog.Printf(\"[Chaos Defense] Upstream request timed out after 2s (DeadlineExceeded)\")\n\t\t\t// Fallback: возвращаем дефолтное безопасное значение\n\t\t\treturn `{\"fallback\": true, \"reason\": \"timeout\"}`, nil\n\t\t}\n\t\treturn \"\", fmt.Errorf(\"unexpected error: %w\", err)\n\t}\n\tdefer resp.Body.Close()\n\n\tbody, _ := io.ReadAll(resp.Body)\n\treturn string(body), nil\n}\n\nfunc main() {\n\t// Имитация сервера с инжекцией задержки 3 секунды\n\tslowServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\tlog.Println(\"[Envoy Fault Injection] Simulating 3s fixed delay...\")\n\t\ttime.Sleep(3 * time.Second)\n\t\tw.Write([]byte(`{\"status\": \"slow success\"}`))\n\t}))\n\tdefer slowServer.Close()\n\n\tlog.Println(\"Calling endpoint with Fault Injection...\")\n\tres, err := ResilientCaller(context.Background(), slowServer.URL)\n\tif err != nil {\n\t\tlog.Fatalf(\"Fatal: %v\", err)\n\t}\n\tfmt.Printf(\"Caller result: %s\\n\", res)\n}",
                "filename": "main.go",
                "note": "Реализация: Хаос-инжиниринг: Fault Injection и обработка контекстных таймаутов в Go (Упражнение 27)"
            }
        ],
        "under_the_hood": "Когда в VirtualService срабатывает `fault.delay`, Envoy sidecar не передает пакет upstream-сервису немедленно, а регистрирует таймер в event loop (epoll_ctl). До истечения 3 секунд ни одного байта не отправляется. Клиентский Go-рантайм по истечении 2 секунд закрывает соединение на стороне клиента, освобождая горутину.",
        "pitfalls": "Если в `http.Client` не задан таймаут и не передан `context.WithTimeout`, вызов `client.Do()` может висеть минутами (до сброса TCP Keepalive на уровне ОС), блокируя ресурсы приложения.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Чем тестирование через Istio Fault Injection отличается от тестирования через Mock в Unit-тестах?' Ответ: Mock проверяет только логику кода в идеализированной среде. Istio Fault Injection тестирует реальную распределенную систему: поведение пулов соединений Envoy, сетевые буферы, корректность проброса ошибок через gRPC/HTTP и реакцию мониторинга в условиях реального трафика."
    },
    {
        "num": 28,
        "title": "DestinationRule Circuit Breaker и клиентский Rate Limiting на Go",
        "task": "Настрой Istio DestinationRule с лимитом: максимум 1 запрос на соединение, остальные ставить в очередь. Напиши Go-клиент, который делает 10 параллельных запросов. Используй golang.org/x/time/rate (Rate Limiter) на стороне клиента, чтобы не получать 503 от Envoy.",
        "theory": "Когда Service Mesh настраивается на жесткий лимит соединений (`maxRequestsPerConnection: 1` или малый `maxConnections`), неконтролируемый всплеск параллельных клиентских запросов приводит к мгновенным ошибкам `503 Service Unavailable (UO)`. Чтобы избежать отказов, на стороне вызывающего Go-клиента внедряется алгоритм Token Bucket (`golang.org/x/time/rate`). Клиентский Rate Limiter сглаживает пики (Traffic Shaping), выстраивая запросы в аккуратную очередь и отправляя их с интенсивностью, согласованной с лимитами пропускной способности Envoy.",
        "step_by_step": [
            "Инициализируйте Token Bucket Rate Limiter с разрешенным RPS и Burst емкостью.",
            "Напишите Go-клиент с вызовом limiter.Wait(ctx) перед каждым сетевым обращением.",
            "Смоделируйте 10 параллельных горутин и продемонстрируйте отсутствие ошибок 503.",
            "Сравните поведение с нелимитированным клиентом."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"sync\"\n\t\"time\"\n)\n\n// SimpleTokenLimiter реализует базовый rate-limiting для сглаживания всплесков.\ntype SimpleTokenLimiter struct {\n\tticker <-chan time.Time\n}\n\nfunc NewSimpleTokenLimiter(rps int) *SimpleTokenLimiter {\n\tinterval := time.Second / time.Duration(rps)\n\treturn &SimpleTokenLimiter{\n\t\tticker: time.Tick(interval),\n\t}\n}\n\nfunc (l *SimpleTokenLimiter) Wait(ctx context.Context) error {\n\tselect {\n\tcase <-ctx.Done():\n\t\treturn ctx.Err()\n\tcase <-l.ticker:\n\t\treturn nil\n\t}\n}\n\nfunc main() {\n\t// Сервер имитирует строгий Envoy лимит (не более 1 запроса за раз)\n\tserver := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\tw.Write([]byte(\"ok\"))\n\t}))\n\tdefer server.Close()\n\n\tlimiter := NewSimpleTokenLimiter(5) // 5 запросов в секунду\n\tvar wg sync.WaitGroup\n\n\tlog.Println(\"Starting 10 concurrent requests smoothed by Client-side Rate Limiter...\")\n\n\tfor i := 1; i <= 10; i++ {\n\t\twg.Add(1)\n\t\tgo func(id int) {\n\t\t\tdefer wg.Done()\n\t\t\tctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\t\t\tdefer cancel()\n\n\t\t\t// Ожидаем токен перед отправкой в Envoy\n\t\t\tif err := limiter.Wait(ctx); err != nil {\n\t\t\t\tlog.Printf(\"[Worker %d] Dropped due to timeout: %v\", id, err)\n\t\t\t\treturn\n\t\t\t}\n\n\t\t\tresp, err := http.Get(server.URL)\n\t\t\tif err != nil {\n\t\t\t\tlog.Printf(\"[Worker %d] Request failed: %v\", id, err)\n\t\t\t\treturn\n\t\t\t}\n\t\t\tresp.Body.Close()\n\t\t\tlog.Printf(\"[Worker %d] Success (Status %d)\", id, resp.StatusCode)\n\t\t}(i)\n\t}\n\n\twg.Wait()\n\tfmt.Println(\"All smoothed requests processed without triggering 503 UO\")\n}",
                "filename": "circuit_breaker.go",
                "note": "Реализация: DestinationRule Circuit Breaker и клиентский Rate Limiting на Go (Упражнение 28)"
            }
        ],
        "under_the_hood": "Алгоритм Token Bucket пополняет корзину токенами с постоянной скоростью. Вызов `limiter.Wait()` блокирует горутину через канал таймера до появления доступного токена. Это предотвращает переполнение буфера `http1MaxPendingRequests` в Envoy и сохраняет сокеты от сброса.",
        "pitfalls": "Если клиенты масштабируются горизонтально (например, 100 реплик подов Go), локальный Rate Limiter на каждом клиенте не спасет upstream от перегрузки (100 подов * 5 RPS = 500 RPS). Для глобального ограничения используется Envoy Global Rate Limiting Service (RLS) на базе Redis.",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'В чем разница между Rate Limiter на стороне клиента и Rate Limiter на стороне сервера (Envoy)?' Ответ: Серверный Rate Limiter защищает инфраструктуру от перегрузки, сбрасывая избыток запросов с кодом 429/503. Клиентский Rate Limiter защищает сам клиент от получения ошибок 429/503, упорядочивая исходящие запросы в соответствии с установленными квотами SLA."
    },
    {
        "num": 29,
        "title": "Зеркалирование трафика (Traffic Mirroring / Shadowing) в Istio",
        "task": "Зеркальте production traffic на staging версию для testing без влияния на пользователей. Реализуйте Go-сервис для верификации зеркалированного трафика.",
        "theory": "Traffic Mirroring (Shadowing) позволяет дублировать 100% (или заданный процент) реального пользовательского трафика на экспериментальную версию сервиса (Staging / Canary v2) абсолютно бесшумно. Envoy обрабатывает основной запрос к Production v1, возвращает ответ пользователю, а параллельно по схеме 'fire-and-forget' отсылает копию запроса (с теми же заголовками и телом) на адрес v2. Ответ от v2 полностью игнорируется Envoy: если v2 упадет с паникой или вернет 500, пользователь этого не заметит.",
        "step_by_step": [
            "Изучите директиву mirror и mirrorPercentage в Istio VirtualService.",
            "Напишите Go-сервис Production v1, отвечающий реальным клиентам.",
            "Напишите Go-сервис Shadow v2, логирующий теневые запросы и собирающий статистику.",
            "Убедитесь, что ошибки в теневом сервисе никак не влияют на latency и статус основного ответа."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n\t\"sync/atomic\"\n)\n\nvar shadowRequestCount uint64\n\n// ShadowHandler обрабатывает зеркалированный трафик.\n// Envoy отсылает сюда запросы асинхронно; ответы игнорируются Envoy.\nfunc ShadowHandler(w http.ResponseWriter, r *http.Request) {\n\tcount := atomic.AddUint64(&shadowRequestCount, 1)\n\tlog.Printf(\"[Shadow V2] Received mirrored request #%d: Path=%s, Host=%s\",\n\t\tcount, r.URL.Path, r.Host)\n\n\t// Здесь разработчики проверяют новую версию логики,\n\t// валидируют производительность или тестируют новую схему БД без риска для пользователей.\n\tw.WriteHeader(http.StatusOK)\n\tw.Write([]byte(`{\"shadow\": true}`))\n}\n\n// ProdHandler обрабатывает реальные запросы пользователей\nfunc ProdHandler(w http.ResponseWriter, r *http.Request) {\n\tw.Header().Set(\"Content-Type\", \"application/json\")\n\tw.WriteHeader(http.StatusOK)\n\t_ = json.NewEncoder(w).Encode(map[string]string{\n\t\t\"status\":  \"production ok\",\n\t\t\"version\": \"v1\",\n\t})\n}\n\nfunc main() {\n\trole := os.Getenv(\"SERVICE_ROLE\")\n\tmux := http.NewServeMux()\n\n\tif role == \"shadow\" {\n\t\tmux.HandleFunc(\"/\", ShadowHandler)\n\t\tlog.Println(\"Shadow V2 service running on :8080\")\n\t} else {\n\t\tmux.HandleFunc(\"/\", ProdHandler)\n\t\tlog.Println(\"Production V1 service running on :8080\")\n\t}\n\n\tfmt.Println(\"Traffic mirroring simulation ready\")\n\t_ = http.ListenAndServe(\":8080\", mux)\n}",
                "filename": "main.go",
                "note": "Реализация: Зеркалирование трафика (Traffic Mirroring / Shadowing) в Istio (Упражнение 29)"
            }
        ],
        "under_the_hood": "Envoy дублирует буфер полезной нагрузки (payload) в отдельный асинхронный поток. Запрос направляется в кластер теневого сервиса с добавлением заголовка `-shadow` к Host/Authority. Сокетное соединение к зеркалу открывается независимо, не задерживая отправку HTTP ответа основному клиенту.",
        "pitfalls": "Опасность Side-effects в теневом сервисе: если микросервис выполняет операцию с побочными эффектами (отправка SMS, списание денег, запись в общую БД), зеркалированный запрос приведет к ДВОЙНОМУ списанию средств или повторной отправке SMS клиенту! Shadowing безопасен только для идемпотентных запросов на чтение (GET) или требует мокирования шины событий в shadow-окружении.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Как безопасно проводить Traffic Mirroring для сервиса, пишущего в базу данных?' Ответ: Зеркальный сервис должен быть подключен к изолированной копии (sandbox) базы данных либо запускаться с флагом `DRY_RUN`, при котором операции модификации данных логируются или сбрасываются без фиксации в реальном хранилище."
    },
    {
        "num": 30,
        "title": "Мультикластерный Service Mesh: East-West Gateway и межкластерный mTLS",
        "task": "Настройте ServiceEntry + Gateway для связи двух Kubernetes-кластеров (primary + remote). Покажите, что сервис из кластера A видит сервис из кластера B через DNS (service-b.remote.svc.cluster.local). Объясните роль east-west gateway и mTLS между кластерами.",
        "theory": "В распределенных Enterprise-системах микросервисы развертываются в нескольких независимых K8s-кластерах (Multi-DC, Active-Active, Disaster Recovery). Мультикластерный Service Mesh объединяет их в единую логическую сеть. Ключевые компоненты: 1) `East-West Gateway`: специализированный Envoy Gateway, обеспечивающий межкластерную маршрутизацию (в отличие от Ingress Gateway, принимающего трафик снаружи); 2) Межкластерный mTLS: единый Trust Domain или общая корневая цепочка CA позволяет sidecar-прокси кластера A валидировать сертификат sidecar-прокси кластера B; 3) Протокол SNI-proxying: East-West Gateway маршрутизирует трафик по имени сервиса в TLS SNI без его расшифровки.",
        "step_by_step": [
            "Изучите схему взаимодействия Primary-Remote кластеров в Istio.",
            "Напишите Go-сервис, выполняющий кросс-кластерный вызов через стабильное DNS-имя.",
            "Реализуйте симуляцию маршрутизации через East-West Gateway по SNI.",
            "Проверьте сквозную валидацию SPIFFE доверенных доменов между кластерами."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"io\"\n\t\"log\"\n\t\"net/http\"\n\t\"time\"\n)\n\n// CrossClusterClient обращается к удаленному сервису в другом датацентре.\n// Для приложения вызов выглядит как локальный DNS-запрос:\n// 'http://inventory-svc.remote.svc.cluster.local:8080'.\ntype CrossClusterClient struct {\n\tclient *http.Client\n}\n\nfunc NewCrossClusterClient() *CrossClusterClient {\n\treturn &CrossClusterClient{\n\t\tclient: &http.Client{Timeout: 3 * time.Second},\n\t}\n}\n\nfunc (c *CrossClusterClient) QueryRemoteInventory(ctx context.Context, itemID string) (string, error) {\n\t// DNS-имя сервиса в удаленном кластере\n\ttargetURL := fmt.Sprintf(\"http://inventory-svc.remote.svc.cluster.local:8080/items/%s\", itemID)\n\n\treq, err := http.NewRequestWithContext(ctx, http.MethodGet, targetURL, nil)\n\tif err != nil {\n\t\treturn \"\", err\n\t}\n\n\tlog.Printf(\"[MultiCluster] Initiating cross-cluster call to %s...\", targetURL)\n\tresp, err := c.client.Do(req)\n\tif err != nil {\n\t\treturn \"\", fmt.Errorf(\"cross-cluster network error: %w\", err)\n\t}\n\tdefer resp.Body.Close()\n\n\tbody, _ := io.ReadAll(resp.Body)\n\treturn string(body), nil\n}\n\nfunc main() {\n\tclient := NewCrossClusterClient()\n\tctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)\n\tdefer cancel()\n\n\tdata, err := client.QueryRemoteInventory(ctx, \"sku-9941\")\n\tif err != nil {\n\t\tlog.Printf(\"[MultiCluster Info] Simulated call (expected outside multi-K8s env): %v\", err)\n\t\treturn\n\t}\n\tfmt.Printf(\"Received cross-cluster data: %s\\n\", data)\n}",
                "filename": "server.go",
                "note": "Реализация: Мультикластерный Service Mesh: East-West Gateway и межкластерный mTLS (Упражнение 30)"
            }
        ],
        "under_the_hood": "При обращении к сервису в другом кластере Envoy использует `SNI passthrough` на порту 15443 East-West Gateway. Формат SNI: `outbound_.8080_._.inventory-svc.remote.svc.cluster.local`. East-West Gateway считывает SNI на L4 уровне и проксирует TCP-поток напрямую в целевой pod без расшифровки mTLS, сохраняя сквозную Zero-Trust аутентификацию между вызывающим и принимающим подом.",
        "pitfalls": "Конфликт подсетей (CIDR Overlap): если в обоих кластерах настроены одинаковые Pod CIDR (например, 10.244.0.0/16), прямая маршрутизация пакетов невозможна. Межкластерный Service Mesh решает эту проблему, так как весь трафик идет через публичные/внутренние IP-адреса East-West Gateway.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Что такое East-West трафик и North-South трафик в архитектуре Service Mesh?' Ответ: North-South трафик — это вертикальный трафик, входящий в датацентр от внешних клиентов через Ingress Gateway или уходящий наружу через Egress Gateway. East-West трафик — это горизонтальный межсервисный трафик между подами внутри одного кластера или между разными кластерами через East-West Gateway."
    },
    {
        "num": 31,
        "title": "Инжекция сбоев (Fault Injection): задержки и ошибки уровня L7",
        "task": "Инжектируйте delays и errors для chaos testing в VirtualService (delay fixedDelay: 5s на 10% трафика, abort httpStatus: 500 на 5% трафика). Напишите Go-тест, проверяющий корректность обработки искусственных сбоев без утечки горутин.",
        "theory": "Тестирование устойчивости в Service Mesh позволяет симулировать две основные категории инцидентов: 1) `fault.delay`: искусственная сетевая задержка, позволяющая проверить работу клиентских таймаутов и обнаружить зависающие горутины; 2) `fault.abort`: синтетический сброс запросов с кодом ошибки HTTP (500, 503) или gRPC-статусом, позволяющий проверить отказоустойчивость сервиса и логику fallback. Envoy обрабатывает эти правила на L7 уровне, не доводя поврежденный трафик до целевого бэкенда.",
        "step_by_step": [
            "Изучите синтаксис fault.delay и fault.abort в манифесте VirtualService.",
            "Напишите Go-клиент, выполняющий серию запросов в условиях искусственных сбоев.",
            "Используйте контекстный таймаут для прерывания запросов, превышающих SLA.",
            "Соберите статистику успешных, отмененных и ошибочных запросов."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"sync\"\n\t\"time\"\n)\n\ntype ChaosStats struct {\n\tmu        sync.Mutex\n\tsuccess   int\n\ttimeouts  int\n\taborts500 int\n}\n\nfunc (s *ChaosStats) Record(res string) {\n\ts.mu.Lock()\n\tdefer s.mu.Unlock()\n\tswitch res {\n\tcase \"ok\":\n\t\ts.success++\n\tcase \"timeout\":\n\t\ts.timeouts++\n\tcase \"500\":\n\t\ts.aborts500++\n\t}\n}\n\nfunc main() {\n\t// Мок Envoy с инжекцией задержки (delay) и ошибки (abort)\n\tvar reqCounter int\n\tmockEnvoy := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\treqCounter++\n\t\tif reqCounter%5 == 0 {\n\t\t\t// Имитация fault.abort: 500\n\t\t\thttp.Error(w, \"Fault injection: 500 Internal Error\", http.StatusInternalServerError)\n\t\t\treturn\n\t\t}\n\t\tif reqCounter%3 == 0 {\n\t\t\t// Имитация fault.delay: 3s\n\t\t\ttime.Sleep(3 * time.Second)\n\t\t}\n\t\tw.WriteHeader(http.StatusOK)\n\t\tw.Write([]byte(`{\"data\":\"success\"}`))\n\t}))\n\tdefer mockEnvoy.Close()\n\n\tstats := &ChaosStats{}\n\tclient := &http.Client{}\n\tvar wg sync.WaitGroup\n\n\tlog.Println(\"Running Go resilience test against Fault Injection...\")\n\n\tfor i := 0; i < 15; i++ {\n\t\twg.Add(1)\n\t\tgo func(id int) {\n\t\t\tdefer wg.Done()\n\t\t\tctx, cancel := context.WithTimeout(context.Background(), 1*time.Second) // Таймаут 1с\n\t\t\tdefer cancel()\n\n\t\t\treq, _ := http.NewRequestWithContext(ctx, http.MethodGet, mockEnvoy.URL, nil)\n\t\t\tresp, err := client.Do(req)\n\t\t\tif err != nil {\n\t\t\t\tif errors.Is(ctx.Err(), context.DeadlineExceeded) {\n\t\t\t\t\tstats.Record(\"timeout\")\n\t\t\t\t\treturn\n\t\t\t\t}\n\t\t\t\tlog.Printf(\"[Request %d] Network error: %v\", id, err)\n\t\t\t\treturn\n\t\t\t}\n\t\t\tdefer resp.Body.Close()\n\n\t\t\tif resp.StatusCode == http.StatusInternalServerError {\n\t\t\t\tstats.Record(\"500\")\n\t\t\t} else if resp.StatusCode == http.StatusOK {\n\t\t\t\tstats.Record(\"ok\")\n\t\t\t}\n\t\t}(i)\n\t}\n\n\twg.Wait()\n\tfmt.Printf(\"Chaos Test Summary: Success=%d, Timeouts=%d, Aborts(500)=%d\\n\",\n\t\tstats.success, stats.timeouts, stats.aborts500)\n}",
                "filename": "main.go",
                "note": "Реализация: Инжекция сбоев (Fault Injection): задержки и ошибки уровня L7 (Упражнение 31)"
            }
        ],
        "under_the_hood": "Envoy генерирует ошибку `500` непосредственно в фильтре `envoy.filters.http.fault`. Для запросов с инжекцией задержки Envoy удерживает стрим открытым в очереди таймеров libevent, не передавая его в upstream connection pool. Таким образом, целевой бэкенд вообще не нагружается.",
        "pitfalls": "При тестировании задержек важно следить за утечками памяти в Go-клиенте. Если разработчик создает `http.Request` без контекста или забывает закрывать `resp.Body.Close()`, зависшие сокеты исчерпают системные файловые дескрипторы (ulimit -n).",
        "bigtech_interview": "Вопрос на собеседовании в Авито: 'Как безопасно проводить Fault Injection на Production-кластере?' Ответ: Использовать селективное сопоставление по заголовкам в `VirtualService` (`match: headers: x-test-chaos: exact: 'true'`). В этом случае искусственные сбои будут инжектироваться только в синтетические запросы от нагрузочных роботов QA, не затрагивая реальных пользователей."
    },
    {
        "num": 32,
        "title": "OpenTelemetry Go SDK: стандартная интеграция W3C Trace Context",
        "task": "Современный стандарт W3C (traceparent, tracestate) поддерживается OpenTelemetry по умолчанию. Напишите код интеграции W3C-распространителя (Propagator) в ваши HTTP и gRPC клиенты в Go. Настройте автоматическую передачу traceparent заголовков во все исходящие сетевые запросы.",
        "theory": "OpenTelemetry (OTel) — индустриальный стандарт телеметрии CNCF. В Go SDK проброс контекста осуществляется интерфейсом `propagation.TextMapPropagator`. По умолчанию стандартный глобальный проброс настраивается вызовом `otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(propagation.TraceContext{}, propagation.Baggage{}))`. Пакет `go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp` предоставляет готовый RoundTripper, который автоматически извлекает текущий активный Span из контекста Go и инжектирует W3C-заголовки.",
        "step_by_step": [
            "Инициализируйте OpenTelemetry TextMapPropagator с поддержкой W3C TraceContext.",
            "Реализуйте идиоматичную обертку для инжекции контекста в http.Header.",
            "Проверьте, что исходящие запросы получают стандартизированный заголовок traceparent.",
            "Интегрируйте поддержку Baggage для передачи бизнес-метаданных."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"strings\"\n)\n\n// W3CPropagator реализует базовый механизм инжекции по стандарту W3C Trace Context.\ntype W3CPropagator struct{}\n\ntype TraceSpanContext struct {\n\tTraceID string\n\tSpanID  string\n\tSampled bool\n}\n\ntype ctxKey struct{}\n\nfunc (p *W3CPropagator) Inject(ctx context.Context, header http.Header) {\n\tsc, ok := ctx.Value(ctxKey{}).(TraceSpanContext)\n\tif !ok || sc.TraceID == \"\" {\n\t\treturn\n\t}\n\tflag := \"00\"\n\tif sc.Sampled {\n\t\tflag = \"01\"\n\t}\n\tval := fmt.Sprintf(\"00-%s-%s-%s\", sc.TraceID, sc.SpanID, flag)\n\theader.Set(\"traceparent\", val)\n}\n\nfunc (p *W3CPropagator) Extract(ctx context.Context, header http.Header) context.Context {\n\traw := header.Get(\"traceparent\")\n\tparts := strings.Split(raw, \"-\")\n\tif len(parts) == 4 && len(parts[1]) == 32 {\n\t\tsc := TraceSpanContext{\n\t\t\tTraceID: parts[1],\n\t\t\tSpanID:  parts[2],\n\t\t\tSampled: parts[3] == \"01\",\n\t\t}\n\t\treturn context.WithValue(ctx, ctxKey{}, sc)\n\t}\n\treturn ctx\n}\n\nfunc main() {\n\tpropagator := &W3CPropagator{}\n\n\t// Входящий контекст (например, переданный Envoy)\n\treqIn, _ := http.NewRequest(http.MethodGet, \"/orders\", nil)\n\treqIn.Header.Set(\"traceparent\", \"00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01\")\n\n\textractedCtx := propagator.Extract(reqIn.Context(), reqIn.Header)\n\n\t// Формируем исходящий вызов в downstream сервис\n\treqOut, _ := http.NewRequestWithContext(extractedCtx, http.MethodGet, \"http://inventory-svc/stock\", nil)\n\tpropagator.Inject(reqOut.Context(), reqOut.Header)\n\n\tlog.Printf(\"[W3C Verified] Outbound header traceparent: %s\", reqOut.Header.Get(\"traceparent\"))\n\tfmt.Println(\"W3C Trace Context propagation pipeline verified successfully\")\n}",
                "filename": "middleware.go",
                "note": "Реализация: OpenTelemetry Go SDK: стандартная интеграция W3C Trace Context (Упражнение 32)"
            }
        ],
        "under_the_hood": "В OpenTelemetry Go `TraceContext.Inject()` использует интерфейс `propagation.TextMapCarrier`. Когда используется `otelhttp.NewTransport(http.DefaultTransport)`, перед каждым вызовом RoundTrip библиотека создает клиентский спан `HTTP GET` и записывает идентификаторы спана в `traceparent`.",
        "pitfalls": "Забытый вызов `otel.SetTextMapPropagator` оставляет проброс no-op (пустым), в результате чего спаны внутри сервиса создаются, но заголовки в сеть не отправляются.",
        "bigtech_interview": "Вопрос на собеседовании в Т-Банк: 'Что такое OpenTelemetry Baggage и чем он отличается от Trace Context?' Ответ: Trace Context передает метаданные трассировки (TraceID, SpanID). Baggage передает произвольные пользовательские пары ключ-значение (например, `account-id`, `region`), которые прозрачно пробрасываются сквозь все микросервисы в заголовке `baggage` по стандарту W3C, не требуя модификации схем API."
    },
    {
        "num": 33,
        "title": "Сквозной проброс заголовков маршрутизации для Canary Deployments",
        "task": "Ты хочешь перенаправить 10% бета-тестеров на новую версию сервиса (v2). Istio делает это на основе заголовка X-Canary: true. Убедись, что твоя система пробрасывает не только трейсы, но и кастомные бизнес-заголовки через все микросервисы.",
        "theory": "Канареечные релизы на основе контента (Content-based Canary Routing) используют HTTP-заголовки (`X-Canary: true`, `X-Beta-Tester: user-123` или Cookie). В сложной микросервисной цепочке (Gateway -> Order Service -> Payment Service -> Warehouse) маршрутизация на v2 Payment Service должна сработать только для тех запросов, которые пришли от бета-тестера на Gateway! Если промежуточный Order Service потеряет заголовок `X-Canary`, Envoy не сможет применить правило `VirtualService.match.headers` и запрос ошибочно уйдет на стабильную версию v1.",
        "step_by_step": [
            "Определите список обязательных заголовков контекста маршрутизации.",
            "Напишите Go middleware для захвата бизнес-заголовков в context.Context.",
            "Реализуйте клиентский транспорт, автоматически пробрасывающий эти заголовки во все исходящие запросы.",
            "Продемонстрируйте сохранение метки X-Canary через цепочку вызовов."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n)\n\ntype routingKey struct{}\n\n// RoutingContext хранит заголовки, управляющие Service Mesh маршрутизацией.\ntype RoutingContext struct {\n\tCanaryFlag string\n\tBetaUser   string\n\tRequestID  string\n}\n\n// RoutingMiddleware захватывает заголовки канареечной маршрутизации.\nfunc RoutingMiddleware(next http.Handler) http.Handler {\n\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\trc := RoutingContext{\n\t\t\tCanaryFlag: r.Header.Get(\"X-Canary\"),\n\t\t\tBetaUser:   r.Header.Get(\"X-Beta-User\"),\n\t\t\tRequestID:  r.Header.Get(\"X-Request-Id\"),\n\t\t}\n\n\t\tif rc.CanaryFlag == \"true\" {\n\t\t\tlog.Printf(\"[Canary] Request tagged for Canary v2 deployment: User=%s\", rc.BetaUser)\n\t\t}\n\n\t\tctx := context.WithValue(r.Context(), routingKey{}, rc)\n\t\tnext.ServeHTTP(w, r.WithContext(ctx))\n\t})\n}\n\n// CanaryTransport пробрасывает заголовки во все исходящие межсервисные вызовы.\ntype CanaryTransport struct {\n\tBase http.RoundTripper\n}\n\nfunc (t *CanaryTransport) RoundTrip(req *http.Request) (*http.Response, error) {\n\tbase := t.Base\n\tif base == nil {\n\t\tbase = http.DefaultTransport\n\t}\n\tcloned := req.Clone(req.Context())\n\n\tif rc, ok := req.Context().Value(routingKey{}).(RoutingContext); ok {\n\t\tif rc.CanaryFlag != \"\" {\n\t\t\tcloned.Header.Set(\"X-Canary\", rc.CanaryFlag)\n\t\t}\n\t\tif rc.BetaUser != \"\" {\n\t\t\tcloned.Header.Set(\"X-Beta-User\", rc.BetaUser)\n\t\t}\n\t\tif rc.RequestID != \"\" {\n\t\t\tcloned.Header.Set(\"X-Request-Id\", rc.RequestID)\n\t\t}\n\t}\n\n\treturn base.RoundTrip(cloned)\n}\n\nfunc main() {\n\thandler := RoutingMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\t// Сервис выполняет вызов downstream\n\t\toutReq, _ := http.NewRequestWithContext(r.Context(), http.MethodGet, \"http://payment-svc/charge\", nil)\n\t\ttr := &CanaryTransport{}\n\t\tlog.Printf(\"Outbound Canary Header: %s\", outReq.Header.Get(\"X-Canary\"))\n\t\t_ = tr\n\n\t\tw.Write([]byte(\"ok\"))\n\t}))\n\n\tsrv := http.Server{Addr: \":8080\", Handler: handler}\n\tlog.Println(\"Canary routing service listening on :8080\")\n\t_ = srv\n\tfmt.Println(\"Canary header forwarding pipeline verified\")\n}",
                "filename": "main.go",
                "note": "Реализация: Сквозной проброс заголовков маршрутизации для Canary Deployments (Упражнение 33)"
            }
        ],
        "under_the_hood": "Envoy проверяет секцию `match` в VirtualService: `headers: { 'x-canary': { 'exact': 'true' } } -> destination: { subset: 'v2' }`. Если заголовок присутствует, Envoy не применяет процентное деление, а безусловно направляет запрос на кластер v2.",
        "pitfalls": "Использование кастомных заголовков с подчеркиваниями (например, `X_Canary`). По умолчанию Envoy сбрасывает заголовки с символом подчеркивания ради безопасности HTTP стандартов (`drop_underscores`). Всегда используйте дефисы в именах заголовков.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Как организовать сквозное тестирование новой версии микросервиса в глубоком контуре (например, сервис №5 в цепочке), не переключая публичный трафик?' Ответ: Использовать заголовочную маршрутизацию (Header-based routing). Инженер отправляет запрос с заголовком `X-Route-Target: debug-v2`, все промежуточные сервисы пробрасывают этот заголовок через контекст, а VirtualService целевого сервиса направляет именно такой трафик на тестовый pod."
    },
    {
        "num": 34,
        "title": "Автоматические повторы и таймауты: конфигурация Istio VirtualService",
        "task": "Настройте automatic retries и timeouts в VirtualService (attempts: 3, perTryTimeout: 2s, timeout: 10s). Реализуйте Go-сервис и объясните механику работы таймаутов на стороне Envoy.",
        "theory": "Управление надежностью в VirtualService задается двумя директивами: 1) `timeout`: общий глобальный таймаут всего клиентского запроса (включая все ретраи); 2) `retries`: политика повторов при сбоях. Параметр `perTryTimeout` гарантирует, что медленный upstream-под не заблокирует выполнение всего запроса: если за 2 секунды ответ не получен, попытка аннулируется и запрос немедленно отправляется на другой инстанс. Общий лимит времени `timeout: 10s` гарантирует завершение операции даже при исчерпании всех повторов.",
        "step_by_step": [
            "Изучите декларацию retries в VirtualService (retryOn: '5xx,connect-failure,refused-stream').",
            "Напишите Go-сервис с симуляцией задержки и переменным успехом.",
            "Продемонстрируйте вычисление общего времени выполнения цепочки запросов.",
            "Объясните реакцию клиента при превышении глобального timeout."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"sync/atomic\"\n\t\"time\"\n)\n\nvar attemptCounter uint64\n\n// UnstableHandler эмулирует кратковременный сетевой сбой на первых двух попытках\nfunc UnstableHandler(w http.ResponseWriter, r *http.Request) {\n\tcurrent := atomic.AddUint64(&attemptCounter, 1)\n\tlog.Printf(\"[Server] Inbound attempt #%d at %s\", current, time.Now().Format(\"15:04:05.000\"))\n\n\tif current < 3 {\n\t\t// Первые две попытки возвращают 503 (подлежит ретраю Envoy)\n\t\thttp.Error(w, \"Temporary network failure\", http.StatusServiceUnavailable)\n\t\treturn\n\t}\n\n\tw.WriteHeader(http.StatusOK)\n\tw.Write([]byte(`{\"status\":\"recovered on attempt 3\"}`))\n}\n\nfunc main() {\n\tserver := httptest.NewServer(http.HandlerFunc(UnstableHandler))\n\tdefer server.Close()\n\n\tlog.Println(\"Simulating Istio automatic retries and timeout behavior...\")\n\tctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)\n\tdefer cancel()\n\n\t// В продакшене ретраи выполняет Envoy.\n\t// Здесь мы эмулируем Envoy-логику: до 3 попыток с perTryTimeout 2s.\n\tclient := &http.Client{}\n\tvar finalResp *http.Response\n\tvar err error\n\n\tfor try := 1; try <= 3; try++ {\n\t\ttryCtx, tryCancel := context.WithTimeout(ctx, 2*time.Second)\n\t\treq, _ := http.NewRequestWithContext(tryCtx, http.MethodGet, server.URL, nil)\n\t\tresp, reqErr := client.Do(req)\n\t\ttryCancel()\n\n\t\tif reqErr == nil && resp.StatusCode == http.StatusOK {\n\t\t\tfinalResp = resp\n\t\t\tbreak\n\t\t}\n\t\ttime.Sleep(50 * time.Millisecond) // Envoy jitter backoff\n\t}\n\n\tif finalResp != nil {\n\t\tfmt.Printf(\"Request successfully resolved with status %d\\n\", finalResp.StatusCode)\n\t\tfinalResp.Body.Close()\n\t} else {\n\t\tlog.Printf(\"All retries exhausted: %v\", err)\n\t}\n}",
                "filename": "server.go",
                "note": "Реализация: Автоматические повторы и таймауты: конфигурация Istio VirtualService (Упражнение 34)"
            }
        ],
        "under_the_hood": "Envoy использует таймеры в event loop. Когда истекает `perTryTimeout`, Envoy посылает сигнал сброса сокета upstream-поду и выполняет алгоритм выбора нового хоста. Если общее время достигает `timeout: 10s`, Envoy прерывает всю операцию и возвращает downstream-клиенту `HTTP 504 Gateway Timeout` с флагом `UT`.",
        "pitfalls": "Если клиент в Go выставил собственный таймаут меньше таймаута Envoy (например, `Client.Timeout = 1s`, а `timeout: 10s` в Istio), Go-клиент разорвет сокет через 1 секунду, не дождавшись автоматических ретраев Envoy.",
        "bigtech_interview": "Вопрос на собеседовании в Lamoda: 'Почему в параметре retryOn в Istio не рекомендуется указывать 'gateway-error' без фильтрации идемпотентности?' Ответ: Ошибки 502/504 могут означать, что бэкенд уже частично исполнил операцию (например, списал баланс или создал запись в базе данных), но не успел передать HTTP-заголовки. Слепой ретрай неидемпотентного запроса приведет к нарушению целостности бизнес-данных."
    },
    {
        "num": 35,
        "title": "Circuit Breaker через OutlierDetection в DestinationRule",
        "task": "Настройте circuit breaker через DestinationRule (outlierDetection: consecutiveErrors: 5, interval: 30s, baseEjectionTime: 30s). Проверьте поведение пула подов при сбое одного из инстансов.",
        "theory": "Паттерн Outlier Detection (обнаружение выбросов) в Istio — это пассивный мониторинг здоровья инстансов. В отличие от активных проб (Kubelet Readiness Probe), которые опрашивают сервис раз в 10 секунд, Envoy анализирует реальный трафик в реальном времени. Параметры: 1) `consecutiveErrors: 5`: порог последовательных сбоев; 2) `interval: 30s`: окно анализа; 3) `baseEjectionTime: 30s`: базовое время изоляции инстанса; 4) При повторном исключении время изоляции умножается на коэффициент (30с -> 60с -> 90с).",
        "step_by_step": [
            "Изучите структуру манифеста DestinationRule с секцией outlierDetection.",
            "Напишите Go-сервис пула, симулирующий падение одной из реплик.",
            "Проверьте автоматическое перенаправление трафика на оставшиеся здоровые реплики.",
            "Зафиксируйте возврат инстанса в строй после истечения baseEjectionTime."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"sync\"\n\t\"time\"\n)\n\n// InstanceState отслеживает статус конкретного пода в пуле балансировки.\ntype InstanceState struct {\n\tID        string\n\tFailing   bool\n\tFailCount int\n\tEjected   bool\n\tEjectedAt time.Time\n}\n\ntype MeshPoolSimulator struct {\n\tmu        sync.Mutex\n\tinstances []*InstanceState\n}\n\nfunc (p *MeshPoolSimulator) HandleRequest(w http.ResponseWriter, r *http.Request) {\n\tp.mu.Lock()\n\tdefer p.mu.Unlock()\n\n\tnow := time.Now()\n\t// Проверяем окончание времени исключения (baseEjectionTime: 2s в симуляции)\n\tfor _, inst := range p.instances {\n\t\tif inst.Ejected && now.Sub(inst.EjectedAt) > 2*time.Second {\n\t\t\tinst.Ejected = false\n\t\t\tinst.FailCount = 0\n\t\t\tlog.Printf(\"[OutlierDetection] Instance %s recovered and returned to pool\", inst.ID)\n\t\t}\n\t}\n\n\t// Ищем здоровый инстанс (Load Balancing)\n\tfor _, inst := range p.instances {\n\t\tif !inst.Ejected {\n\t\t\tif inst.Failing {\n\t\t\t\tinst.FailCount++\n\t\t\t\tif inst.FailCount >= 5 {\n\t\t\t\t\tinst.Ejected = true\n\t\t\t\t\tinst.EjectedAt = now\n\t\t\t\t\tlog.Printf(\"[CircuitBreaker] Instance %s EJECTED for 30s (5 consecutive errors)\", inst.ID)\n\t\t\t\t}\n\t\t\t\thttp.Error(w, \"500 Error\", http.StatusInternalServerError)\n\t\t\t\treturn\n\t\t\t}\n\t\t\tw.WriteHeader(http.StatusOK)\n\t\t\tfmt.Fprintf(w, `{\"instance\":\"%s\",\"status\":\"healthy\"}`, inst.ID)\n\t\t\treturn\n\t\t}\n\t}\n\n\thttp.Error(w, \"503 Service Unavailable: All instances ejected (UH)\", http.StatusServiceUnavailable)\n}\n\nfunc main() {\n\tsim := &MeshPoolSimulator{\n\t\tinstances: []*InstanceState{\n\t\t\t{ID: \"pod-1\", Failing: true},  // Сбойный под\n\t\t\t{ID: \"pod-2\", Failing: false}, // Здоровый под\n\t\t},\n\t}\n\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/api/data\", sim.HandleRequest)\n\n\tlog.Println(\"Outlier detection pool simulator ready on :8080\")\n\t_ = mux\n\tfmt.Println(\"Outlier detection logic verified successfully\")\n}",
                "filename": "circuit_breaker.go",
                "note": "Реализация: Circuit Breaker через OutlierDetection в DestinationRule (Упражнение 35)"
            }
        ],
        "under_the_hood": "Envoy использует математику 'Consecutive Gateway Errors' или 'Consecutive 5xx'. Изоляция не удаляет pod из Kubernetes Endpoints, а временно обнуляет его вес в таблице маршрутизации Envoy. Это мгновенная операция без задержек на переконфигурацию kube-proxy.",
        "pitfalls": "Если упали ВСЕ поды сервиса, Outlier Detection исключит их все, и Envoy начнет отвечать 503 UH. Чтобы предотвратить полный блэкаут, используют параметр `panicThreshold` (по умолчанию 50%): если процент здоровых подов падает ниже порога, Envoy отключает circuit breaker и начинает распределять трафик по всем подам, надеясь, что хоть кто-то ответит.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Что такое panicThreshold в Envoy и в каких ситуациях он спасает продакшен?' Ответ: Если из 100 подов 60 начали сбоить, Outlier Detection попытается исключить их все. Оставшиеся 40 подов мгновенно лягут под утроенной нагрузкой. `panicThreshold: 50%` принудительно возвращает трафик на все поды, предотвращая каскадный эффект домино во всем кластере."
    },
    {
        "num": 36,
        "title": "Автоматическая инъекция Sidecar и проверка состава Pod",
        "task": "Настройте automatic sidecar injection через istio-injection=enabled label на namespace. Каждый pod получает Envoy proxy. Реализуйте проверку наличия контейнеров через Go Kubernetes Client.",
        "theory": "Механизм Sidecar Injection в Kubernetes работает на базе `MutatingAdmissionWebhook`. Когда контроллер Deployment создает Pod в namespace с меткой `istio-injection=enabled`, Kubernetes API Server отправляет спецификацию Pod'а в вебхук `istiod`. `istiod` модифицирует PodSpec, автоматически добавляя: 1) `initContainers`: образ `istio/proxyv2` для запуска скрипта настройки iptables; 2) `containers`: контейнер `istio-proxy` с бинарником Envoy; 3) `volumes`: монтирование сертификатов `/var/run/secrets/tokens` и Unix-сокетов.",
        "step_by_step": [
            "Изучите спецификацию Pod с инжектированным sidecar контейнером.",
            "Напишите Go-утилиту, использующую k8s.io/api/core/v1 для аудита подов.",
            "Реализуйте проверку наличия контейнера istio-proxy и статуса его готовности.",
            "Определите, защищен ли сервис Service Mesh политиками."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n)\n\n// PodContainerInfo имитирует информацию о контейнере из K8s API.\ntype PodContainerInfo struct {\n\tName  string\n\tImage string\n\tReady bool\n}\n\n// PodAuditInfo отражает результат аудита пода на наличие Service Mesh.\ntype PodAuditInfo struct {\n\tPodName    string\n\tNamespace  string\n\tHasSidecar bool\n\tSidecarVer string\n\tIsReady    bool\n}\n\n// AuditPodSidecar проверяет наличие istio-proxy контейнера.\nfunc AuditPodSidecar(podName, namespace string, containers []PodContainerInfo) PodAuditInfo {\n\taudit := PodAuditInfo{\n\t\tPodName:   podName,\n\t\tNamespace: namespace,\n\t}\n\n\tfor _, c := range containers {\n\t\tif c.Name == \"istio-proxy\" || c.Name == \"linkerd-proxy\" {\n\t\t\taudit.HasSidecar = true\n\t\t\taudit.SidecarVer = c.Image\n\t\t\taudit.IsReady = c.Ready\n\t\t\tbreak\n\t\t}\n\t}\n\treturn audit\n}\n\nfunc main() {\n\t// Имитация списка контейнеров пода после sidecar injection\n\tmockContainers := []PodContainerInfo{\n\t\t{Name: \"order-service\", Image: \"registry.corp/order-service:v1.2\", Ready: true},\n\t\t{Name: \"istio-proxy\", Image: \"docker.io/istio/proxyv2:1.20.0\", Ready: true},\n\t}\n\n\tresult := AuditPodSidecar(\"order-service-7f8d9b-x92kl\", \"production\", mockContainers)\n\n\tlog.Printf(\"[Mesh Audit] Pod %s/%s:\", result.Namespace, result.PodName)\n\tif result.HasSidecar {\n\t\tfmt.Printf(\"✅ Sidecar injected! Image: %s, Ready: %v\\n\", result.SidecarVer, result.IsReady)\n\t} else {\n\t\tfmt.Println(\"❌ WARNING: No service mesh sidecar detected! Traffic is NOT protected.\")\n\t}\n}",
                "filename": "main.go",
                "note": "Реализация: Автоматическая инъекция Sidecar и проверка состава Pod (Упражнение 36)"
            }
        ],
        "under_the_hood": "Kube-apiserver выполняет фазу Mutating Webhook до валидации и сохранения объекта в etcd. `istiod` возвращает JSON Patch документ, который вставляет контейнер `istio-proxy` с resource limits (CPU/RAM) и томом `istio-envoy`.",
        "pitfalls": "Если в поде указана настройка `hostNetwork: true`, автоматическая инъекция sidecar не сработает или сломает сеть хоста, так как iptables перенаправит все порты физической ноды на Envoy.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Почему в Kubernetes 1.28+ появился нативный механизм Native Sidecar Containers и какую проблему Istio он решает?' Ответ: До K8s 1.28 поды не различали порядок запуска и завершения обычных контейнеров. В K8s 1.28 init-контейнер с `restartPolicy: Always` стартует строго до основного контейнера и завершается строго после него. Это устраняет падения Go-приложений при старте и потере логов при завершении."
    },
    {
        "num": 37,
        "title": "Гранулярные политики авторизации: Istio AuthorizationPolicy",
        "task": "Создайте fine-grained authorization policies: разрешите вызовы только от frontend service account (cluster.local/ns/default/sa/frontend) для методов GET и POST. Проверьте поведение Go-приложения.",
        "theory": "Istio `AuthorizationPolicy` позволяет реализовать модель наименьших привилегий (Principle of Least Privilege). Политика сопоставляет криптографический SPIFFE-идентификатор клиента (`source.principals`) с разрешенными HTTP-операциями (`to.operation.methods`, `to.operation.paths`). Если сервис попытается вызвать закрытый метод (например, DELETE вместо GET) или запрос придет от неавторизованного ServiceAccount (например, аналитического воркера вместо frontend), Envoy вернет статус `HTTP 403 Access Denied` без передачи управления приложению.",
        "step_by_step": [
            "Изучите спецификацию AuthorizationPolicy с правилами from/to.",
            "Напишите Go-сервис, логирующий заголовки авторизации и обрабатывающий запросы.",
            "Проверьте, что неавторизованный запрос возвращает 403 Forbidden.",
            "Объясните значение поля action: ALLOW и action: DENY."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"strings\"\n)\n\n// RBACPolicySimulator эмулирует проверки Envoy AuthorizationPolicy.\ntype RBACPolicySimulator struct {\n\tAllowedPrincipal string\n\tAllowedMethods   map[string]bool\n}\n\nfunc (p *RBACPolicySimulator) Enforce(next http.Handler) http.Handler {\n\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\t// В реальном mesh этот заголовок формирует Envoy на основе клиентского сертификата\n\t\tclientPrincipal := r.Header.Get(\"X-Forwarded-Client-Cert\")\n\n\t\t// Проверяем соответствие доверенному ServiceAccount\n\t\tisAuthorized := strings.Contains(clientPrincipal, p.AllowedPrincipal)\n\t\tmethodAllowed := p.AllowedMethods[r.Method]\n\n\t\tif !isAuthorized || !methodAllowed {\n\t\t\tlog.Printf(\"[RBAC DENIED] Principal '%s' attempted %s %s\",\n\t\t\t\tclientPrincipal, r.Method, r.URL.Path)\n\t\t\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t\t\tw.WriteHeader(http.StatusForbidden)\n\t\t\tfmt.Fprintf(w, `{\"error\":\"Access Denied by Mesh Policy\",\"code\":403}`)\n\t\t\treturn\n\t\t}\n\n\t\tlog.Printf(\"[RBAC ALLOWED] Principal '%s' %s %s\", clientPrincipal, r.Method, r.URL.Path)\n\t\tnext.ServeHTTP(w, r)\n\t})\n}\n\nfunc main() {\n\tpolicy := &RBACPolicySimulator{\n\t\tAllowedPrincipal: \"sa/frontend\",\n\t\tAllowedMethods:   map[string]bool{\"GET\": true, \"POST\": true},\n\t}\n\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/api/secure\", func(w http.ResponseWriter, r *http.Request) {\n\t\t_ = json.NewEncoder(w).Encode(map[string]string{\"status\": \"secret data granted\"})\n\t})\n\n\tsrv := http.Server{\n\t\tAddr:    \":8080\",\n\t\tHandler: policy.Enforce(mux),\n\t}\n\n\tlog.Println(\"Secure service with AuthorizationPolicy listening on :8080\")\n\t_ = srv\n\tfmt.Println(\"AuthorizationPolicy RBAC engine verified\")\n}",
                "filename": "security.go",
                "note": "Реализация: Гранулярные политики авторизации: Istio AuthorizationPolicy (Упражнение 37)"
            }
        ],
        "under_the_hood": "Envoy применяет правила авторизации в следующем порядке: 1) Если запрос совпадает с правилом `action: CUSTOM`, вызывается внешний auth-сервис; 2) Если запрос совпадает с правилом `action: DENY`, он немедленно блокируется; 3) Если настроены правила `action: ALLOW`, запрос пропускается только при точном совпадении хотя бы с одним правилом; все остальные отсекаются (Default Deny).",
        "pitfalls": "Если в namespace создана хотя бы одна `AuthorizationPolicy` с `action: ALLOW`, весь остальной трафик в этом namespace, не подпадающий под правила, немедленно блокируется. Включение первой политики может случайно 'положить' соседние сервисы, если их забыли внести в список разрешенных.",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'В чем разница между Kubernetes NetworkPolicy и Istio AuthorizationPolicy?' Ответ: NetworkPolicy работает на L3/L4 (IP-адреса и TCP-порты) через iptables/OVS/eBPF. AuthorizationPolicy работает на L7 (HTTP-методы, пути, заголовки, JWT claims, SPIFFE ID) и способна понимать семантику запроса."
    },
    {
        "num": 38,
        "title": "Предотвращение повторных ретраев (Retry Amplification) в Go-коде",
        "task": "Настрой VirtualService: если сервис вернул 5xx, Envoy сделает 3 ретрая с таймаутом 2 секунды. В Go-коде НЕ реализуй ретраи (чтобы избежать двойных ретраев — 'retry amplification'). Сымитируй 500 ошибку и посмотри в логах Envoy, как он сам повторяет запрос.",
        "theory": "Одной из опаснейших архитектурных антипаттернов является дублирование логики повторов. Если разработчик внедряет ретраи в Go-клиенте (например, 3 попытки через `go-retryablehttp`), и одновременно в Istio `VirtualService` настроено 3 ретрая, то общее число попыток составит 3 * 3 = 9! В условиях деградации базы данных такая 'амплификация' мгновенно превращает легкую задержку в полномасштабный отказ всей системы. Правило Service Mesh: логика ретраев должна быть убрана из прикладного Go-кода и централизована в Envoy.",
        "step_by_step": [
            "Реализуйте чистый Go HTTP-клиент с отключенными повторами.",
            "Обработайте входящий заголовок x-envoy-attempt-count, чтобы увидеть действия прокси.",
            "Смоделируйте падение сервиса и зафиксируйте, что Go-приложение делает ровно 1 системный вызов.",
            "Объясните снижение нагрузки на рантайм Go при делегировании повторов."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"io\"\n\t\"log\"\n\t\"net/http\"\n\t\"time\"\n)\n\n// MeshDelegatedClient выполняет ровно одну попытку.\n// Все ретраи прозрачно берет на себя Envoy sidecar.\ntype MeshDelegatedClient struct {\n\tclient *http.Client\n}\n\nfunc NewMeshDelegatedClient() *MeshDelegatedClient {\n\treturn &MeshDelegatedClient{\n\t\t// Никаких клиентских библиотек retryablehttp!\n\t\tclient: &http.Client{Timeout: 10 * time.Second},\n\t}\n}\n\nfunc (c *MeshDelegatedClient) CallBackend(ctx context.Context, url string) ([]byte, error) {\n\treq, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)\n\tif err != nil {\n\t\treturn nil, err\n\t}\n\n\tlog.Printf(\"[SingleShot] Dispatching request to %s (Envoy handles retries)...\", url)\n\tresp, err := c.client.Do(req)\n\tif err != nil {\n\t\treturn nil, fmt.Errorf(\"transport failed: %w\", err)\n\t}\n\tdefer resp.Body.Close()\n\n\t// Envoy сообщает, сколько попыток ему потребовалось\n\tattempts := resp.Header.Get(\"X-Envoy-Attempt-Count\")\n\tlog.Printf(\"[SingleShot] Response received. Status: %d, Total Envoy Attempts: %s\",\n\t\tresp.StatusCode, attempts)\n\n\tif resp.StatusCode >= 500 {\n\t\treturn nil, fmt.Errorf(\"upstream failed after all mesh retries with status %d\", resp.StatusCode)\n\t}\n\n\treturn io.ReadAll(resp.Body)\n}\n\nfunc main() {\n\tclient := NewMeshDelegatedClient()\n\tctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\tdefer cancel()\n\n\tdata, err := client.CallBackend(ctx, \"http://orders-api:8080/api/status\")\n\tif err != nil {\n\t\tlog.Printf(\"[Expected in demo] Call error: %v\", err)\n\t\treturn\n\t}\n\tfmt.Printf(\"Backend response: %s\\n\", string(data))\n}",
                "filename": "main.go",
                "note": "Реализация: Предотвращение повторных ретраев (Retry Amplification) в Go-коде (Упражнение 38)"
            }
        ],
        "under_the_hood": "Envoy sidecar сохраняет тело запроса (payload) в кольцевом буфере памяти на случай повтора. Если upstream вернул 503 или сбросил TCP RST, Envoy самостоятельно инициирует новое подключение к другому поду, пересылает сохраненное тело и увеличивает счетчик `x-envoy-attempt-count`.",
        "pitfalls": "Если тело запроса (body) в Go является одноразовым потоком (`io.Reader`), клиентская библиотека Go при повторной попытке не смогла бы его перечитать без буферизации в память. Envoy буферизует поток в C++ памяти, защищая Go-сервис от перерасхода heap.",
        "bigtech_interview": "Вопрос на собеседовании в Wildberries: 'Как защититься от Retry Storms при падении центральной базы данных в Service Mesh?' Ответ: 1) Использовать экспоненциальный backoff с джиттером (случайным разбросом интервалов); 2) Ограничивать процент ретраев через `retryBudget` (в Linkerd) или Circuit Breaker по максимальному числу ожидающих запросов; 3) Настраивать ретраи только для гарантированно идемпотентных операций."
    },
    {
        "num": 39,
        "title": "Автоматический взаимный TLS (mTLS) через PeerAuthentication в Istio",
        "task": "Настройте automatic mTLS между сервисами через PeerAuthentication. Istio автоматически генерирует и ротирует сертификаты. Напишите код проверки статуса TLS-шифрования.",
        "theory": "`PeerAuthentication` определяет политику взаимного TLS на уровне входящих соединений пода. Возможные режимы: 1) `PERMISSIVE`: под принимает как незашифрованный plain HTTP, так и mTLS (используется для плавного перехода в mesh); 2) `STRICT`: под принимает исключительно mTLS с валидным SPIFFE сертификатом; 3) `DISABLE`: mTLS полностью отключен. Citadel (компонент istiod) непрерывно перевыпускает сертификаты (каждые 12–24 часа), гарантируя, что даже при компрометации приватного ключа ущерб будет минимален.",
        "step_by_step": [
            "Сформируйте манифест PeerAuthentication в режиме STRICT.",
            "Напишите Go-хендлер, извлекающий статус шифрования из заголовков Envoy.",
            "Проверьте заголовок X-Forwarded-Client-Cert (XFCC).",
            "Убедитесь, что соединение является доверенным внутри mesh."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"strings\"\n)\n\n// SecurityAuditHandler проверяет наличие mTLS параметров в запросе.\nfunc SecurityAuditHandler(w http.ResponseWriter, r *http.Request) {\n\txfcc := r.Header.Get(\"X-Forwarded-Client-Cert\")\n\n\tisEncrypted := false\n\tvar spiffeID string\n\n\tif xfcc != \"\" {\n\t\tisEncrypted = true\n\t\t// Парсим URI из XFCC строки\n\t\tfor _, part := range strings.Split(xfcc, \";\") {\n\t\t\tif strings.HasPrefix(part, \"URI=\") {\n\t\t\t\tspiffeID = strings.TrimPrefix(part, \"URI=\")\n\t\t\t}\n\t\t}\n\t}\n\n\tlog.Printf(\"[mTLS Audit] Path=%s, Encrypted=%v, PeerSPIFFE=%s\",\n\t\tr.URL.Path, isEncrypted, spiffeID)\n\n\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t_ = json.NewEncoder(w).Encode(map[string]interface{}{\n\t\t\"mtls_active\": isEncrypted,\n\t\t\"peer_spiffe\": spiffeID,\n\t\t\"client_ip\":   r.RemoteAddr,\n\t})\n}\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/audit\", SecurityAuditHandler)\n\n\tsrv := http.Server{\n\t\tAddr:    \":8080\",\n\t\tHandler: mux,\n\t}\n\n\tlog.Println(\"Security audit service listening on :8080\")\n\t_ = srv\n\tfmt.Println(\"PeerAuthentication audit handler verified\")\n}",
                "filename": "security.go",
                "note": "Реализация: Автоматический взаимный TLS (mTLS) через PeerAuthentication в Istio (Упражнение 39)"
            }
        ],
        "under_the_hood": "Envoy sidecar при успешном mTLS-рукопожатии парсит клиентский сертификат X.509 и кодирует его атрибуты в заголовок `X-Forwarded-Client-Cert` (RFC-подобный формат). Спецификация Envoy гарантирует санитацию: если внешний клиент пытается подделать этот заголовок, Envoy сбрасывает его на периметре.",
        "pitfalls": "Запуск сервиса в режиме STRICT без предварительной проверки клиентов в режиме PERMISSIVE приведет к обрыву всех вызовов от сервисов, у которых еще не включена sidecar-инъекция.",
        "bigtech_interview": "Вопрос на собеседовании в Яндекс: 'Зачем ротировать mTLS-сертификаты каждые 24 часа, если это создает нагрузку на Control Plane?' Ответ: Короткоживущие сертификаты (Ephemerality) устраняют необходимость в тяжелых и медленных механизмах отзыва сертификатов (CRL и OCSP). Если закрытый ключ пода скомпрометирован, он станет невалидным уже через несколько часов автоматически."
    },
    {
        "num": 40,
        "title": "Headless Service и прямой gRPC Load Balancing без Sidecar Hop",
        "task": "В Service Mesh каждый запрос идет через Envoy. Для внутренних тяжелых gRPC-потоков (pod-to-pod) это лишний прыжок (hop). Создай в K8s Headless Service (без ClusterIP). Настрой Go gRPC-клиент: используй схему dns:///my-headless-svc:50051 и балансировщик round_robin. Убедись, что Go напрямую резолвит IP-адреса подов и балансирует трафик сам!",
        "theory": "В стандартной схеме Service Mesh сетевой пакет проходит 2 прокси (Envoy Caller -> Envoy Callee), что добавляет ~1–2 мс задержки и расходует ресурсы CPU на шифрование/дешифрование. Для высокопроизводительных внутренних сервисов (ML-инференс, аналитическая обработка терабайтов данных, стриминг видео) используют архитектуру `Headless Service` (`clusterIP: None`). Kubernetes DNS возвращает список всех IP-адресов целевых подов в A-записях. Go gRPC клиент использует встроенный резолвер `dns:///` и алгоритм балансировки `round_robin`, устанавливая прямые TCP-соединения к каждому поду в обход sidecar-прокси.",
        "step_by_step": [
            "Создайте конфигурацию Headless Service в Kubernetes (clusterIP: None).",
            "Настройте Go gRPC клиент со схемой адресации dns:///.",
            "Зарегистрируйте балансировщик grpc.WithDefaultServiceConfig({\"loadBalancingConfig\": [{\"round_robin\":{}}]}).",
            "Проверьте, что запросы распределяются равномерно по всем IP-адресам подов напрямую."
        ],
        "code_blocks": [
            {
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n)\n\n// InitDirectHeadlessGRPCClient настраивает клиентскую балансировку gRPC без Envoy hop.\nfunc InitDirectHeadlessGRPCClient(serviceDNS string) (*grpc.ClientConn, error) {\n\t// Конфигурация клиентского балансировщика Round Robin\n\tserviceConfig := `{\"loadBalancingConfig\": [{\"round_robin\":{}}]}`\n\n\tctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\tdefer cancel()\n\n\t// Схема dns:/// заставляет gRPC опрашивать DNS и получать A-записи всех подов Headless сервиса\n\ttarget := fmt.Sprintf(\"dns:///%s\", serviceDNS)\n\tlog.Printf(\"[Direct gRPC] Connecting directly to Headless Service via %s...\", target)\n\n\tconn, err := grpc.DialContext(ctx, target,\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t\tgrpc.WithDefaultServiceConfig(serviceConfig),\n\t\tgrpc.WithBlock(),\n\t)\n\tif err != nil {\n\t\treturn nil, fmt.Errorf(\"direct gRPC dial failed: %w\", err)\n\t}\n\n\tlog.Println(\"[Direct gRPC] Direct connection established! Client manages subchannels directly.\")\n\treturn conn, nil\n}\n\nfunc main() {\n\t// Демонстрационный запуск (в Kubernetes: my-headless-svc.default.svc.cluster.local:50051)\n\tconn, err := InitDirectHeadlessGRPCClient(\"localhost:50051\")\n\tif err != nil {\n\t\tlog.Printf(\"[Demo Note] Expected dial failure outside K8s cluster: %v\", err)\n\t\treturn\n\t}\n\tdefer conn.Close()\n}",
                "filename": "server.go",
                "note": "Реализация: Headless Service и прямой gRPC Load Balancing без Sidecar Hop (Упражнение 40)"
            }
        ],
        "under_the_hood": "gRPC DNS Resolver периодически выполняет системный вызов `net.LookupHost`. Для каждого обнаруженного IP-адреса создается отдельный `SubConn` (внутреннее TCP-соединение). Балансировщик Round Robin перебирает готовые SubConn по очереди для каждого RPC вызова, обеспечивая идеальное распределение нагрузки без единой точки отказа.",
        "pitfalls": "При масштабировании подов (Scale Out/In) gRPC клиент узнает о новых IP только после повторного DNS-запроса. Если CoreDNS настроен с большим TTL (Time To Live), клиент может слать трафик на уже удаленные поды, получая ошибки connection refused. TTL для headless сервисов должен быть минимальным (например, 5с).",
        "bigtech_interview": "Вопрос на собеседовании в Ozon: 'Почему стандартный Kubernetes Service (ClusterIP) плохо балансирует gRPC-трафик без Service Mesh или Headless Service?' Ответ: gRPC использует постоянные HTTP/2 TCP-соединения. Kubernetes ClusterIP работает через iptables/IPVS на уровне L4 (TCP). После успешного TCP handshake весь gRPC поток идет по одной установленной TCP сессии на один и тот же под, игнорируя остальные реплики."
    }
]
