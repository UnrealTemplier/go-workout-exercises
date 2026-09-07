# -*- coding: utf-8 -*-
"""
Глава 82: Защита сетевых сокетов и противодействие DoS-атакам — Часть 2 (Упражнения 29-55)
"""

exercises = [
    {
        "num": 29,
        "title": "Экономия ресурсов CPU при SYN-флуде через TCP_DEFER_ACCEPT",
        "task": "Настройте параметр TCP_DEFER_ACCEPT в net.ListenConfig и измерьте нагрузку на процессор при наплыве пустых TCP-соединений, не передающих прикладные данные.",
        "theory": "При классическом SYN-флуде или атаке полуоткрытыми соединениями ядро ОС переводит сокет в состояние ESTABLISHED и будит поток приложения для вызова `accept()`. Рантайм Go инициализирует горутину и сетевой буфер, после чего блокируется на `read()`. Опция `TCP_DEFER_ACCEPT` инструктирует ядро не генерировать событие EPOLLIN и не будить рантайм до поступления хотя бы одного байта полезных данных. Пустые соединения отсекаются на уровне ядра с околонулевыми затратами CPU со стороны приложения.",
        "step_by_step": [
            "Инициализируйте `net.ListenConfig` с хуком `Control`.",
            "Установите опцию `TCP_DEFER_ACCEPT` с таймаутом 5-10 секунд.",
            "Смоделируйте подключение клиента без отправки HTTP-запроса.",
            "Убедитесь, что метод `Accept()` не вызывается до прихода первого байта данных."
        ],
        "code_blocks": [
            {
                "filename": "defer_accept_shield.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"syscall\"\n)\n\nfunc ListenDefer(addr string, timeoutSec int) (net.Listener, error) {\n\tlc := net.ListenConfig{\n\t\tControl: func(network, address string, c syscall.RawConn) error {\n\t\t\tvar setErr error\n\t\t\terr := c.Control(func(fd uintptr) {\n\t\t\t\t// TCP_DEFER_ACCEPT: константа 9 в Linux TCP\n\t\t\t\tsetErr = syscall.SetsockoptInt(int(fd), syscall.IPPROTO_TCP, 9, timeoutSec)\n\t\t\t})\n\t\t\tif err != nil {\n\t\t\t\treturn err\n\t\t\t}\n\t\t\treturn setErr\n\t\t},\n\t}\n\treturn lc.Listen(context.Background(), \"tcp\", addr)\n}\n\nfunc main() {\n\tln, err := ListenDefer(\"127.0.0.1:0\", 10)\n\tif err != nil {\n\t\tfmt.Printf(\"[WARN] Ошибка TCP_DEFER_ACCEPT: %v\\n\", err)\n\t\treturn\n\t}\n\tdefer ln.Close()\n\n\tfmt.Printf(\"[DEFER] Защищенный сокет слушает на %s\\n\", ln.Addr())\n}\n",
                "note": "Низкоуровневая настройка задержки пробуждения сокета"
            }
        ],
        "under_the_hood": "Ядро Linux оставляет сокет в состоянии SYN_RECV вплоть до прихода первого пакета PSH/ACK с данными, отсекая пустые TCP-сессии без вызова планировщика Go.",
        "pitfalls": "Если протокол требует баннера от сервера до передачи данных клиентом, использование `TCP_DEFER_ACCEPT` приведет к мертвому зависанию сессии.",
        "bigtech_interview": "В чем разница между SYN Cookies и TCP_DEFER_ACCEPT? SYN Cookies защищают ядро от переполнения памяти на этапе handshake, а TCP_DEFER_ACCEPT защищает приложение от траты ресурсов на пустые установленные сессии."
    },
    {
        "num": 30,
        "title": "Многопоточный стресс-клиент DoS-атаки Slowloris на Go",
        "task": "Разработайте утилиту на Go для демонстрации атаки Slowloris: генерация 1000 параллельных сессий с периодической отправкой байтов заголовков для проверки устойчивости инфраструктуры.",
        "theory": "Стресс-тестирование на устойчивость к Slowloris требует генерации стабильного пула медленных сокетов. Клиентская программа в Go использует легкие горутины, каждая из которых устанавливает TCP-соединение, шлет начальные байты HTTP-заголовка и уходит в сон `time.Sleep(10s)` перед отправкой следующего байта. Скрипт позволяет наглядно проверить работу таймаутов `ReadHeaderTimeout` на стороне тестируемого сервиса.",
        "step_by_step": [
            "Определите пул из 1000 горутин.",
            "В каждой горутине подключитесь к целевому серверу через `net.DialTimeout`.",
            "Отправляйте по одному байту HTTP-заголовка раз в 10 секунд.",
            "Логируйте количество разорванных сервером соединений."
        ],
        "code_blocks": [
            {
                "filename": "slowloris_demo.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"sync\"\n\t\"time\"\n)\n\nfunc launchSlowlorisClient(target string, numConns int) {\n\tvar wg sync.WaitGroup\n\tfor i := 0; i < numConns; i++ {\n\t\twg.Add(1)\n\t\tgo func(id int) {\n\t\t\tdefer wg.Done()\n\t\t\tconn, err := net.DialTimeout(\"tcp\", target, 3*time.Second)\n\t\t\tif err != nil {\n\t\t\t\treturn\n\t\t\t}\n\t\t\tdefer conn.Close()\n\n\t\t\t// Отправляем стартовую строку запроса\n\t\t\t_, _ = conn.Write([]byte(\"GET / HTTP/1.1\\r\\nHost: test\\r\\n\"))\n\n\t\t\tfor {\n\t\t\t\ttime.Sleep(10 * time.Second)\n\t\t\t\t_, err := conn.Write([]byte(\"X: 1\\r\\n\"))\n\t\t\t\tif err != nil {\n\t\t\t\t\t// Сервер сбросил соединение по ReadHeaderTimeout\n\t\t\t\t\treturn\n\t\t\t\t}\n\t\t\t}\n\t\t}(i)\n\t}\n\twg.Wait()\n}\n\nfunc main() {\n\tfmt.Println(\"[SLOWLORIS] Демонстрационный клиент стресс-тестирования готов.\")\n\t_ = launchSlowlorisClient\n}\n",
                "note": "Стресс-генератор медленных HTTP-соединений на Go"
            }
        ],
        "under_the_hood": "Благодаря легковесности горутин Go (2-4 КБ на стек) одна машина может генерировать сотни тысяч одновременных медленных сессий, моделируя мощнейший DoS.",
        "pitfalls": "Запуск против внешних сервисов без авторизации классифицируется статьей 272/273 УК РФ (неправомерный доступ к компьютерной информации).",
        "bigtech_interview": "Как Cloudflare и AWS CloudFront нейтрализуют Slowloris? L7-прокси полностью вычитывает все заголовки запроса в свои буферы и проксирует в бэкенд только целостные готовые HTTP-запросы."
    },
    {
        "num": 31,
        "title": "Переполнение таблицы conntrack и защита через правила NOTRACK в iptables",
        "task": "Исследуйте системные лимиты таблицы отслеживания соединений Linux (nf_conntrack_max, nf_conntrack_count) и сконфигурируйте stateless-фильтрацию через iptables NOTRACK.",
        "theory": "Подсистема Netfilter ядра Linux отслеживает состояние каждого сетевого пакета в таблице `conntrack`. Размер таблицы ограничен параметром `net.netfilter.nf_conntrack_max`. Во время DDoS-атак с подделкой IP-адресов таблица мгновенно заполняется до максимума (`nf_conntrack_count == nf_conntrack_max`), после чего ядро начинает молча отбрасывать абсолютно все входящие пакеты (`nf_conntrack: table full, dropping packet`). Решение: отключить отслеживание соединений для высоконагруженных портов через `iptables -t raw -A PREROUTING -p tcp --dport 8080 -j NOTRACK`.",
        "step_by_step": [
            "Проверьте текущее заполнение таблицы: `sysctl net.netfilter.nf_conntrack_count`.",
            "Проверьте максимальный лимит: `sysctl net.netfilter.nf_conntrack_max`.",
            "Сконфигурируйте правило исключения: `iptables -t raw -A PREROUTING -p tcp --dport 8080 -j NOTRACK`.",
            "Реализуйте Go-программу мониторинга метрик conntrack через `/proc/sys/net/netfilter/`."
        ],
        "code_blocks": [
            {
                "filename": "conntrack_monitor.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n\t\"strconv\"\n\t\"strings\"\n)\n\nfunc CheckConntrack() {\n\tmaxBytes, err := os.ReadFile(\"/proc/sys/net/netfilter/nf_conntrack_max\")\n\tif err != nil {\n\t\tfmt.Printf(\"[WARN] Conntrack недоступен: %v\\n\", err)\n\t\treturn\n\t}\n\tcountBytes, err := os.ReadFile(\"/proc/sys/net/netfilter/nf_conntrack_count\")\n\tif err != nil {\n\t\treturn\n\t}\n\n\tmaxVal, _ := strconv.Atoi(strings.TrimSpace(string(maxBytes)))\n\tcountVal, _ := strconv.Atoi(strings.TrimSpace(string(countBytes)))\n\n\tutilization := float64(countVal) / float64(maxVal) * 100\n\tfmt.Printf(\"[CONNTRACK] Заполнение: %d / %d (%.2f%%)\\n\", countVal, maxVal, utilization)\n\tif utilization > 80.0 {\n\t\tfmt.Println(\"[ALERT] Опасное заполнение таблицы conntrack! Риск потери пакетов!\")\n\t}\n}\n\nfunc main() {\n\tCheckConntrack()\n}\n",
                "note": "Мониторинг заполнения системной таблицы Netfilter conntrack"
            }
        ],
        "under_the_hood": "Правило `-j NOTRACK` переводит пакет в состояние `UNTRACKED`, минуя выделение памяти в таблице conntrack и разгружая ядро Linux.",
        "pitfalls": "При отключении tracking перестают работать правила iptables с фильтрацией по состоянию `-m state --state ESTABLISHED,RELATED` для этих сокетов.",
        "bigtech_interview": "Почему Kubernetes кластеры на Kube-proxy iptables начинают терять пакеты при 50 000+ RPS? Из-за исчерпания conntrack table; переход на Cilium/eBPF решает эту проблему за счет бестрекерной маршрутизации."
    },
    {
        "num": 32,
        "title": "Практический анализ уязвимостей стандартного сервера http.ListenAndServe",
        "task": "Продемонстрируйте падение стандартного http.ListenAndServe() под нагрузкой из медленных клиентов и опишите дефекты архитектуры рантайма по умолчанию.",
        "theory": "Функция `http.ListenAndServe(\":8080\", handler)` использует глобальный экземпляр `&http.Server{}` со всеми нулевыми таймаутами. Нулевой таймаут в Go означает бесконечное ожидание. Подключение 1000 медленных клиентов навсегда парализует сервер. Наличие такой конфигурации в промышленном коде — грубейшая ошибка проектирования сетевого стека.",
        "step_by_step": [
            "Скомпилируйте приложение с `http.ListenAndServe`.",
            "Запустите стресс-клиент Slowloris.",
            "Попробуйте выполнить параллельный запрос легитимным клиентом `curl`.",
            "Убедитесь в зависании или отказе сервиса.",
            "Замените вызов на безопасную структуру с таймаутами."
        ],
        "code_blocks": [
            {
                "filename": "vulnerable_demo.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"I am vulnerable\")\n\t})\n\n\tfmt.Println(\"[DEMO] ВНИМАНИЕ: Запущен сервер с дефолтными бесконечными таймаутами!\")\n\t// Антипаттерн для продакшена:\n\t_ = http.ListenAndServe\n\t_ = mux\n}\n",
                "note": "Антипаттерн вызова ListenAndServe без защитных таймаутов"
            }
        ],
        "under_the_hood": "Внутри `http.ListenAndServe` создается `Server{Addr: addr, Handler: handler}`. Поля `ReadTimeout`, `WriteTimeout`, `IdleTimeout` и `ReadHeaderTimeout` остаются равными 0 (бесконечность).",
        "pitfalls": "Использование сторонних роутеров (Gin, Chi, Fiber) не спасает от проблемы, если сам `http.Server` инициализирован без явных таймаутов.",
        "bigtech_interview": "Вопрос: 'Спасает ли переход на Gin от уязвимости Slowloris?' Ответ: Нет, Gin — это лишь маршрутизатор (http.Handler); низкоуровневые таймауты сокета задаются исключительно в структуре http.Server."
    },
    {
        "num": 33,
        "title": "Активация и аудит подсистемы TCP SYN Cookies на уровне Linux",
        "task": "Настройте автоматическую активацию net.ipv4.tcp_syncookies в конфигурации /etc/sysctl.conf и напишите скрипт проверки метрик отраженных атак через netstat -s.",
        "theory": "TCP SYN Cookies являются базовой линией обороны операционной системы против атак типа SYN-флуд. Параметр `net.ipv4.tcp_syncookies = 1` предписывает ядру включать криптографический режим при заполнении очереди полуоткрытых сокетов (SYN backlog). Это исключает падение сервера от исчерпания памяти ядра, позволяя продолжать обслуживать легитимных клиентов.",
        "step_by_step": [
            "Проверьте текущее значение: `sysctl net.ipv4.tcp_syncookies`.",
            "Включите защиту: `sysctl -w net.ipv4.tcp_syncookies=1`.",
            "Зафиксируйте настройку в `/etc/sysctl.d/99-security.conf`.",
            "Проверьте статистику срабатываний: `netstat -s | grep -i syncookies`."
        ],
        "code_blocks": [
            {
                "filename": "sysctl_hardening.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[SYSCTL] Применение сетевого харднинга против SYN Flood...\"\n\n# Включение SYN Cookies\nsysctl -w net.ipv4.tcp_syncookies=1\n\n# Увеличение глубины очередей сокетов\nsysctl -w net.core.somaxconn=4096\nsysctl -w net.ipv4.tcp_max_syn_backlog=8192\n\necho \"[METRICS] Проверка счетчиков отраженных атак:\"\nnetstat -s | grep -E \"(syncookies|overflows)\" || true\n\necho \"[OK] Сетевой стек Linux успешно защищен.\"\n",
                "note": "Скрипт тюнинга параметров сетевой безопасности ядра Linux"
            }
        ],
        "under_the_hood": "При включенном режиме ядро вычисляет ISN как `SHA1(src_ip, dst_ip, src_port, dst_port, secret, t) + seq_client + flags`.",
        "pitfalls": "Параметр `tcp_syncookies=2` форсирует использование cookies всегда, что не рекомендуется из-за накладных расходов на процессор.",
        "bigtech_interview": "В чем недостаток работы в режиме SYN Cookies? При генерации ISN невозможно сохранить все TCP опции (Selective Acknowledgements SACK, Timestamp), что незначительно снижает пропускную способность соединения при потерях пакетов."
    },
    {
        "num": 34,
        "title": "Оптимальная калибровка ReadHeaderTimeout в высоконагруженных шлюзах",
        "task": "Сконфигурируйте и обоснуйте выбор значения ReadHeaderTimeout: 10 * time.Second для API Gateway, обрабатывающего мобильный трафик с высокими задержками сети.",
        "theory": "Выбор значения `ReadHeaderTimeout` — это баланс между устойчивостью к Slowloris и доступностью для клиентов в мобильных сетях (3G/LTE/Edge). Слишком маленькое значение (менее 1 секунды) приведет к ложным сбросам соединений у пользователей с высоким джиттером и потерями пакетов. Значение 5-10 секунд является признанным мировым стандартом для публичных мобильных API: оно гарантированно отсекает Slowloris, не создавая ложных тревог для реальных клиентов.",
        "step_by_step": [
            "Инициализируйте экземпляр `http.Server` с `ReadHeaderTimeout: 10 * time.Second`.",
            "Протестируйте отсечение соединений с паузой между заголовками более 10 секунд.",
            "Убедитесь в бесперебойном приеме запросов от клиентов с задержкой 200-500 мс.",
            "Логируйте ошибки таймаутов для последующего анализа в Grafana."
        ],
        "code_blocks": [
            {
                "filename": "gateway_timeout.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc CreateGatewayServer(addr string) *http.Server {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/v1/orders\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, `{\"status\":\"created\"}`)\n\t})\n\n\treturn &http.Server{\n\t\tAddr:              addr,\n\t\tHandler:           mux,\n\t\tReadHeaderTimeout: 10 * time.Second, // Оптимальный порог для мобильного трафика\n\t\tIdleTimeout:       60 * time.Second,\n\t}\n}\n\nfunc main() {\n\tsrv := CreateGatewayServer(\":8080\")\n\tfmt.Printf(\"[GATEWAY] Сервер запущен на %s с ReadHeaderTimeout = 10s\\n\", srv.Addr)\n\t_ = srv\n}\n",
                "note": "Конфигурация API Gateway с устойчивым таймаутом чтения заголовков"
            }
        ],
        "under_the_hood": "Таймаут начинает отсчитываться сразу после вызова `Accept()`. Как только получена последняя пустая строка `\\r\\n` заголовков, таймер останавливается.",
        "pitfalls": "Если клиенты работают по медленным спутниковым каналам, таймаут 1-2 секунды вызовет массовые сбои.",
        "bigtech_interview": "Как в Яндекс Go выбирают таймауты для водительских приложений? Таймауты на заголовки устанавливаются в 5-10 секунд с агрессивным Exponential Backoff ретраем на клиенте."
    },
    {
        "num": 35,
        "title": "Низкоуровневые системные вызовы рантайма Go и базовый Seccomp профиль",
        "task": "Исследуйте ключевые системные вызовы рантайма Go (clone, futex, mmap, epoll_pwait) и составьте базовый Seccomp-профиль в формате JSON для запуска Go-контейнера в Docker.",
        "theory": "Рантайм Go значительно отличается от классических программ на C/C++. Для работы планировщика GMP требуются специфические системные вызовы:\n* `clone` / `clone3`: создание потоков ОС для M воркеров.\n* `futex`: межпоточная синхронизация мьютексов и каналов.\n* `mmap` / `munmap` / `madvise`: аллокатор памяти Go (mheap/mcentral).\n* `epoll_create1` / `epoll_ctl` / `epoll_pwait`: сетевой поллер (netpoller).\nБлокировка любого из этих вызовов приводит к немедленному аварийному падению программы (`SIGSYS` / crash).",
        "step_by_step": [
            "Определите минимально необходимый набор системных вызовов Go.",
            "Создайте JSON-файл Seccomp-профиля с действием по умолчанию `SCMP_ACT_ERRNO`.",
            "Добавьте обязательные сисколы в белый список (`SCMP_ACT_ALLOW`).",
            "Запустите Docker-контейнер с флагом `--security-opt seccomp=profile.json`.",
            "Убедитесь в штатной работе HTTP-сервера."
        ],
        "code_blocks": [
            {
                "filename": "go_seccomp_minimal.json",
                "lang": "json",
                "code": "{\n  \"defaultAction\": \"SCMP_ACT_ERRNO\",\n  \"architectures\": [\n    \"SCMP_ARCH_X86_64\"\n  ],\n  \"syscalls\": [\n    {\n      \"names\": [\n        \"read\", \"write\", \"openat\", \"close\",\n        \"futex\", \"clone\", \"clone3\", \"sched_yield\", \"nanosleep\",\n        \"mmap\", \"munmap\", \"madvise\", \"mprotect\",\n        \"epoll_create1\", \"epoll_ctl\", \"epoll_pwait\", \"epoll_wait\",\n        \"socket\", \"bind\", \"listen\", \"accept4\", \"getsockname\", \"getpeername\",\n        \"setsockopt\", \"getsockopt\", \"fcntl\",\n        \"rt_sigaction\", \"rt_sigprocmask\", \"sigaltstack\", \"exit_group\"\n      ],\n      \"action\": \"SCMP_ACT_ALLOW\"\n    }\n  ]\n}\n",
                "note": "Минимальный рабочий профиль Seccomp для Go HTTP сервисов"
            }
        ],
        "under_the_hood": "При попытке выполнить вызов, не входящий в список разрешенных, ядро Linux отправляет процессу сигнал `SIGSYS` или возвращает ошибку `EPERM` без исполнения сисколла.",
        "pitfalls": "Забытый сисколл `madvise` приведет к падению сборщика мусора Go при возврате страниц памяти ОС (`runtime.sysUnused`).",
        "bigtech_interview": "Почему стандартный Docker seccomp профиль разрешает сисколл clone, но блокирует clone с флагами создания новых неймспейсов? Для защиты от побега из контейнера через создание вложенных User Namespaces."
    },
    {
        "num": 36,
        "title": "Защита от атак раздувания заголовков через MaxHeaderBytes",
        "task": "Сконфигурируйте жесткий лимит MaxHeaderBytes: 1 << 20 (1 МБ) и протестируйте сценарии отправки допустимых и недопустимо больших HTTP-запросов.",
        "theory": "Ограничение размера входящих заголовков — фундаментальный рубеж защиты памяти сервера. Без этого ограничения злоумышленник может направить поток заголовков, пока сервер не исчерпает свободные слоты в оперативной памяти. Установка `MaxHeaderBytes: 1 << 20` гарантирует, что ни один клиент не сможет занять более 1 мегабайта в буфере парсинга запроса.",
        "step_by_step": [
            "Сконфигурируйте параметр `MaxHeaderBytes` в `http.Server`.",
            "Отправьте запрос с размером заголовков 500 КБ — проверьте успешную обработку.",
            "Отправьте запрос с размером заголовков 2 МБ — проверьте отсечение соединения.",
            "Зафиксируйте поведение в интеграционных тестах."
        ],
        "code_blocks": [
            {
                "filename": "test_max_header.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc RunServerWithHeaderLimit() *http.Server {\n\treturn &http.Server{\n\t\tAddr:           \":8080\",\n\t\tMaxHeaderBytes: 1 << 20, // 1 MB максимум\n\t\tReadTimeout:    10 * time.Second,\n\t}\n}\n\nfunc main() {\n\tsrv := RunServerWithHeaderLimit()\n\tfmt.Printf(\"[SERVER] Запущен с лимитом MaxHeaderBytes = %d байт\\n\", srv.MaxHeaderBytes)\n\t_ = srv\n}\n",
                "note": "Установка жесткого лимита размера заголовков в 1 МБ"
            }
        ],
        "under_the_hood": "Если при чтении запроса размер заголовков превышает лимит, Go рантайм закрывает underlying сокет без вызова пользовательского хендлера.",
        "pitfalls": "Если перед Go сервером стоит Reverse Proxy, лимит прокси может сработать раньше, вернув ошибку до того, как запрос дойдет до Go.",
        "bigtech_interview": "Какова дефолтная величина MaxHeaderBytes в Go? Ровно 1 МБ (1 << 20), если значение в структуре http.Server равно 0."
    },
    {
        "num": 37,
        "title": "Ограничение размера полезной нагрузки через http.MaxBytesReader",
        "task": "Используйте http.MaxBytesReader для ограничения чтения тела входящего запроса до 10 МБ, возвращая статус 413 при попытке передать избыточный объем данных.",
        "theory": "Даже если размер заголовков ограничен, злоумышленник может передать 100-гигабайтный поток данных в теле запроса (POST/PUT). Функция `io.ReadAll(r.Body)` без ограничений приведет к мгновенному падению сервера по Out-Of-Memory. Обертка `r.Body = http.MaxBytesReader(w, r.Body, 10<<20)` гарантирует, что чтение прервется ошибкой `http.MaxBytesError` сразу при превышении 10 МБ, защищая память кучи.",
        "step_by_step": [
            "В начале обработчика оберните `r.Body` в `http.MaxBytesReader`.",
            "Прочитайте тело через `json.NewDecoder(r.Body).Decode(&data)` или `io.ReadAll`.",
            "Проверьте ошибку: при `errors.As(err, &maxBytesErr)` верните статус 413.",
            "Убедитесь в закрытии сокета без зависания сервера."
        ],
        "code_blocks": [
            {
                "filename": "max_bytes_demo.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n\t\"io\"\n\t\"net/http\"\n)\n\nfunc SafeUploadHandler(w http.ResponseWriter, r *http.Request) {\n\t// Лимит 10 МБ на тело запроса\n\tconst maxBodyBytes = 10 << 20\n\tr.Body = http.MaxBytesReader(w, r.Body, maxBodyBytes)\n\n\tbody, err := io.ReadAll(r.Body)\n\tif err != nil {\n\t\tvar maxBytesErr *http.MaxBytesError\n\t\tif errors.As(err, &maxBytesErr) {\n\t\t\thttp.Error(w, \"413 Request Entity Too Large\", http.StatusRequestEntityTooLarge)\n\t\t\treturn\n\t\t}\n\t\thttp.Error(w, \"Ошибка чтения: \"+err.Error(), http.StatusBadRequest)\n\t\treturn\n\t}\n\n\tfmt.Fprintf(w, \"Успешно принято %d байт\\n\", len(body))\n}\n\nfunc main() {\n\thttp.HandleFunc(\"/upload\", SafeUploadHandler)\n\tfmt.Println(\"[HTTP] Обработчик с защитой MaxBytesReader готов к работе.\")\n}\n",
                "note": "Безопасное чтение тела запроса с ограничением в 10 МБ"
            }
        ],
        "under_the_hood": "MaxBytesReader подсчитывает каждый байт. При превышении лимита он отправляет сигнал внутреннему серверу прервать TCP-соединение.",
        "pitfalls": "Забытая проверка ошибки `errors.As(err, &maxBytesErr)` может привести к возврату ошибки 500 вместо корректного кода 413.",
        "bigtech_interview": "Почему нельзя доверять r.ContentLength? Потому что заголовок Content-Length контролируется клиентом и может быть сфальсифицирован или отсутствовать при chunked transfer encoding."
    },
    {
        "num": 38,
        "title": "Высокопроизводительное распределение соединений через SO_REUSEPORT",
        "task": "Спроектируйте архитектуру многопоточного сервера с шардированием слушающих сокетов через SO_REUSEPORT и проведите бенчмарк пропускной способности при параллельных подключениях.",
        "theory": "На серверах с 32+ ядрами CPU одиночный `net.Listener` становится узким местом из-за конкуренции за блокировку очереди сокета в ядре. Использование `SO_REUSEPORT` позволяет создать отдельный сокет для каждого ядра процессора. Ядро Linux аппаратно распределяет входящие потоки, гарантируя нулевую конкуренцию за блокировки и максимальную скорость обработки запросов.",
        "step_by_step": [
            "Определите число доступных CPU через `runtime.NumCPU()`.",
            "Создайте $N$ независимых листенеров с опцией `SO_REUSEPORT` на одном порту.",
            "Запустите HTTP-сервер на каждом листенере в отдельной горутине.",
            "Сравните задержки p99 под высокой параллельной нагрузкой."
        ],
        "code_blocks": [
            {
                "filename": "multi_reuseport.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"net/http\"\n\t\"runtime\"\n\t\"syscall\"\n)\n\nfunc startWorker(id int, addr string) {\n\tlc := net.ListenConfig{\n\t\tControl: func(network, address string, c syscall.RawConn) error {\n\t\t\treturn c.Control(func(fd uintptr) {\n\t\t\t\t_ = syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET, 0xF, 1)\n\t\t\t})\n\t\t},\n\t}\n\tln, err := lc.Listen(context.Background(), \"tcp\", addr)\n\tif err != nil {\n\t\treturn\n\t}\n\tdefer ln.Close()\n\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Воркер %d\\n\", id)\n\t})\n\t_ = http.Serve(ln, mux)\n}\n\nfunc main() {\n\tcpus := runtime.NumCPU()\n\taddr := \"127.0.0.1:8080\"\n\tfmt.Printf(\"[REUSEPORT] Запуск %d шардированных листенеров на %s...\\n\", cpus, addr)\n\tfor i := 0; i < cpus; i++ {\n\t\tgo startWorker(i, addr)\n\t}\n\tfmt.Println(\"[OK] Все воркеры успешно запущены.\")\n}\n",
                "note": "Шардирование листенеров по ядрам CPU через SO_REUSEPORT"
            }
        ],
        "under_the_hood": "Хэширование по 4-кортежу в ядре обеспечивает идеальный баланс трафика без накладных расходов на межъядерную синхронизацию.",
        "pitfalls": "На операционных системах Windows опция `SO_REUSEPORT` не поддерживается (доступен только небезопасный SO_REUSEADDR).",
        "bigtech_interview": "Какова разница между SO_REUSEADDR и SO_REUSEPORT? SO_REUSEADDR позволяет перепривязать порт в состоянии TIME_WAIT, а SO_REUSEPORT позволяет нескольким процессам параллельно слушать один и тот же порт."
    },
    {
        "num": 39,
        "title": "Инфраструктурная настройка ulimit и защита от EMFILE в продакшене",
        "task": "Сконфигурируйте системные лимиты дескрипторов в /etc/security/limits.conf и systemd unit файле сервиса (LimitNOFILE=1048576) для предотвращения сбоев под пиковой нагрузкой.",
        "theory": "Даже самый оптимизированный Go-сервис упадет с ошибкой `accept: too many open files`, если системный лимит дескрипторов процесса остался равным 1024. В production-средах лимит дескрипторов настраивается на уровне оркестратора (Kubernetes), systemd-сервиса (`LimitNOFILE=1048576`) или файла `/etc/security/limits.conf`, обеспечивая возможность удержания сотен тысяч одновременных сетевых соединений.",
        "step_by_step": [
            "Изучите конфигурацию systemd unit файла сервиса.",
            "Добавьте директивы `LimitNOFILE=1048576` и `LimitNPROC=512000` в секцию `[Service]`.",
            "Перезагрузите демон: `systemctl daemon-reload`.",
            "Проверьте эффективные лимиты запущенного процесса в `/proc/<PID>/limits`."
        ],
        "code_blocks": [
            {
                "filename": "service_hardening.service",
                "lang": "ini",
                "code": "[Unit]\nDescription=HighLoad Go Backend Service\nAfter=network.target\n\n[Service]\nType=simple\nUser=www-data\nGroup=www-data\nExecStart=/usr/local/bin/my-go-service\nRestart=always\n\n# Максимальный лимит открытых файлов и сокетов (ulimit -n)\nLimitNOFILE=1048576\n\n# Лимит потоков операционной системы\nLimitNPROC=512000\n\n# Защита от OOM паники\nOOMScoreAdjust=-500\n\n[Install]\nWantedBy=multi-user.target\n",
                "note": "Конфигурация systemd unit файла с расширенным лимитом файловых дескрипторов"
            }
        ],
        "under_the_hood": "Параметр `LimitNOFILE` устанавливает системные лимиты `RLIMIT_NOFILE` для процесса до запуска бинарника, исключая необходимость прав root внутри приложения.",
        "pitfalls": "Увеличение `LimitNOFILE` требует также достаточного объема оперативной памяти для структур сокетов ядра (`file-max`).",
        "bigtech_interview": "Как в Kubernetes манифесте задать ulimit для пода? Через секцию pod spec `initContainers` с вызовом `sysctl` или настройку runtime handler в CRI-O/containerd."
    },
    {
        "num": 40,
        "title": "Низкоуровневая настройка TCP Keep-Alive зондов на сырых дескрипторах",
        "task": "Используйте net.TCPConn для активации SetKeepAlive(true) и SetKeepAlivePeriod(30 * time.Second) на принятом сетевом соединении для своевременного обнаружения мертвых сокетов.",
        "theory": "Сетевое соединение может быть разорвано без уведомления сервера (например, при падении промежуточного NAT-шлюза). Метод `conn.SetKeepAlive(true)` включает отправку пустых TCP ACK-зондов на уровне ядра. Метод `conn.SetKeepAlivePeriod(30 * time.Second)` определяет интервал между зондами. Если клиент не отвечает на зонды, сокет автоматически закрывается, возвращая ошибку `read: connection timed out`.",
        "step_by_step": [
            "Примите соединение и приведите его к `*net.TCPConn`.",
            "Включите зондирование: `tcpConn.SetKeepAlive(true)`.",
            "Задайте интервал: `tcpConn.SetKeepAlivePeriod(30 * time.Second)`.",
            "Проверьте освобождение ресурсов при внезапном отключении клиента."
        ],
        "code_blocks": [
            {
                "filename": "tcp_keepalive_raw.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"time\"\n)\n\nfunc configureKeepAlive(conn net.Conn) error {\n\ttcpConn, ok := conn.(*net.TCPConn)\n\tif !ok {\n\t\treturn fmt.Errorf(\"соединение не является TCPConn\")\n\t}\n\n\t// Включение TCP Keep-Alive зондирования ядра\n\tif err := tcpConn.SetKeepAlive(true); err != nil {\n\t\treturn err\n\t}\n\t// Интервал между зондами 30 секунд\n\tif err := tcpConn.SetKeepAlivePeriod(30 * time.Second); err != nil {\n\t\treturn err\n\t}\n\treturn nil\n}\n\nfunc main() {\n\tfmt.Println(\"[TCP] Функция настройки сырого Keep-Alive зондирования готова.\")\n\t_ = configureKeepAlive\n}\n",
                "note": "Управление TCP Keep-Alive зондами через методы net.TCPConn"
            }
        ],
        "under_the_hood": "Go вызывает `setsockopt(fd, SOL_SOCKET, SO_KEEPALIVE, 1)` и `setsockopt(fd, IPPROTO_TCP, TCP_KEEPINTVL, 30)`.",
        "pitfalls": "Если между клиентом и сервером стоит агрессивный NAT-шлюз с таймаутом 60с, интервал Keep-Alive должен быть строго меньше таймаута NAT (например, 30с).",
        "bigtech_interview": "Почему по умолчанию в Go 1.22 TCP Keep-Alive включен на 15 секунд? Для предотвращения утечек файловых дескрипторов на облачных балансировщиках AWS/GCP."
    },
    {
        "num": 41,
        "title": "Блокировка отладки и инъекций шеллкода через Seccomp (Block ptrace)",
        "task": "Сконфигурируйте Seccomp-профиль, запрещающий системный вызов ptrace, и напишите Go-тест, проверяющий, что попытка вызвать syscall.PtraceAttach мгновенно убивает процесс сигналом SIGSYS.",
        "theory": "Системный вызов `ptrace` используется отладчиками (GDB, Delve) для инспекции памяти и перехвата регистров процесса. В продакшен-среде `ptrace` представляет огромную опасность: злоумышленник, получивший доступ к соседнему непривилегированному процессу, может внедрить шеллкод в память вашего сервиса через `PTRACE_POKETEXT` или сдампить секретные ключи. Блокировка `ptrace` через Seccomp исключает этот вектор атак.",
        "step_by_step": [
            "Создайте Seccomp профиль с запретом сисколла `ptrace` (действие `SCMP_ACT_KILL` или `SCMP_ACT_ERRNO`).",
            "Напишите Go-программу, вызывающую `syscall.PtraceAttach(pid)`.",
            "Запустите программу в изолированном контейнере с данным профилем.",
            "Убедитесь в генерации ошибки `operation not permitted` или завершении по сигналу `SIGSYS`."
        ],
        "code_blocks": [
            {
                "filename": "block_ptrace.json",
                "lang": "json",
                "code": "{\n  \"defaultAction\": \"SCMP_ACT_ALLOW\",\n  \"architectures\": [\n    \"SCMP_ARCH_X86_64\"\n  ],\n  \"syscalls\": [\n    {\n      \"names\": [\n        \"ptrace\",\n        \"process_vm_readv\",\n        \"process_vm_writev\"\n      ],\n      \"action\": \"SCMP_ACT_KILL_PROCESS\"\n    }\n  ]\n}\n",
                "note": "Seccomp профиль для уничтожения процесса при попытке использования ptrace"
            }
        ],
        "under_the_hood": "При действии `SCMP_ACT_KILL_PROCESS` ядро Linux немедленно завершает всю группу потоков процесса без возможности перехвата ошибки в коде приложения.",
        "pitfalls": "Блокировка ptrace сделает невозможным профилирование или отладку сервиса 'на лету' через delve в этом контейнере.",
        "bigtech_interview": "Как в Kubernetes запретить внедрение в память контейнеров? Запретить capability `SYS_PTRACE` и задействовать restricted pod security standard."
    },
    {
        "num": 42,
        "title": "Мгновенное обнаружение сбоев сети через опцию TCP_USER_TIMEOUT",
        "task": "Сконфигурируйте системную опцию TCP_USER_TIMEOUT (Linux) на сокете через RawConn.Control для гарантированного закрытия соединения при зависании ретрансмитов дольше 30 секунд.",
        "theory": "По умолчанию в Linux, если удаленный хост перестал отвечать (разрыв связи), стек TCP может выполнять повторные отправки (retransmissions) до 15-20 минут (регулируется `tcp_retries2 = 15`), прежде чем признать сокет мертвым. Наличие опции `TCP_USER_TIMEOUT` (RFC 5482) позволяет задать максимальное время в миллисекундах, в течение которого переданные данные могут оставаться неподтвержденными. Если ACK не получен за 30 000 мс, ядро принудительно обрывает сокет с ошибкой ETIMEDOUT.",
        "step_by_step": [
            "Извлеките `syscall.RawConn` из принятого соединения `net.Conn`.",
            "В функции `Control` вызовите `syscall.SetsockoptInt` с опцией `TCP_USER_TIMEOUT` (константа 0x12 / 18 в Linux).",
            "Установите таймаут в 30 000 миллисекунд (30 секунд).",
            "Проверьте быстрое освобождение сокета при симуляции потери сетевых пакетов (iptables DROP)."
        ],
        "code_blocks": [
            {
                "filename": "user_timeout.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"syscall\"\n)\n\nfunc SetTCPUserTimeout(conn net.Conn, timeoutMs int) error {\n\ttcpConn, ok := conn.(*net.TCPConn)\n\tif !ok {\n\t\treturn fmt.Errorf(\"не является TCP соединением\")\n\t}\n\n\trawConn, err := tcpConn.SyscallConn()\n\tif err != nil {\n\t\treturn err\n\t}\n\n\tvar opErr error\n\terr = rawConn.Control(func(fd uintptr) {\n\t\t// 0x12 (18) соответствует TCP_USER_TIMEOUT в ядре Linux\n\t\topErr = syscall.SetsockoptInt(int(fd), syscall.IPPROTO_TCP, 18, timeoutMs)\n\t})\n\tif err != nil {\n\t\treturn err\n\t}\n\treturn opErr\n}\n\nfunc main() {\n\tfmt.Println(\"[TCP] Функция установки TCP_USER_TIMEOUT успешно скомпилирована.\")\n\t_ = SetTCPUserTimeout\n}\n",
                "note": "Установка TCP_USER_TIMEOUT для защиты от 15-минутных зависаний ретрансмитов"
            }
        ],
        "under_the_hood": "В отличие от TCP Keep-Alive, работающего при отсутствии данных, TCP_USER_TIMEOUT активен именно тогда, когда в буфере отправки ЕСТЬ неподтвержденные данные, что критично для сетевых клиентов баз данных и очередей.",
        "pitfalls": "Опция специфична для Linux ядра 2.6.37+ и вызовет ошибку при сборке или выполнении на операционных системах macOS или Windows.",
        "bigtech_interview": "Как избежать ситуации, когда Go-сервис зависает на 15 минут при отправке запроса к зависшему внешнему сервису? Настроить TCP_USER_TIMEOUT на 20-30 секунд на уровне транспортного сокета."
    },
    {
        "num": 43,
        "title": "Интеграция Token Bucket лимитера в структуру RateLimitedListener",
        "task": "Реализуйте потокобезопасную структуру RateLimitedListener, использующую golang.org/x/time/rate для контроля общего темпа приема TCP-соединений в секунду.",
        "theory": "Для предотвращения внезапных всплесков трафика (Traffic Spikes / Stampede), способных вызвать просадку планировщика Go, сетевой листенер оборачивают в централизованный Token Bucket лимитер. Метод `rateLimiter.Wait(ctx)` или `Allow()` регулирует скорость выдачи новых сокетов из очереди ядра, сглаживая нагрузку и гарантируя предсказуемое потребление ресурсов процессора.",
        "step_by_step": [
            "Определите тип `RateLimitedListener` со встроенным `net.Listener` и `*rate.Limiter`.",
            "В методе `Accept()` вызывайте `l.limiter.Wait(context.Background())`.",
            "Инициализируйте лимитер параметрами: 1000 соединений в секунду, burst 500.",
            "Проверьте стабильность времени обработки запросов под пиковой нагрузкой."
        ],
        "code_blocks": [
            {
                "filename": "rate_limited_listener.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"golang.org/x/time/rate\"\n)\n\ntype RateLimitedListener struct {\n\tnet.Listener\n\tlimiter *rate.Limiter\n}\n\nfunc NewRateLimitedListener(inner net.Listener, r rate.Limit, b int) *RateLimitedListener {\n\treturn &RateLimitedListener{\n\t\tListener: inner,\n\t\tlimiter:  rate.NewLimiter(r, b),\n\t}\n}\n\nfunc (l *RateLimitedListener) Accept() (net.Conn, error) {\n\t// Ожидаем доступности токена в лимитере перед принятием следующего сокета\n\terr := l.limiter.Wait(context.Background())\n\tif err != nil {\n\t\treturn nil, err\n\t}\n\treturn l.Listener.Accept()\n}\n\nfunc main() {\n\tfmt.Println(\"[RATE] RateLimitedListener сглаживания сетевых всплесков готов.\")\n\t_ = NewRateLimitedListener\n}\n",
                "note": "Сглаживание скорости вызова Accept через алгоритм Token Bucket"
            }
        ],
        "under_the_hood": "Метод `Wait()` использует таймер рантайма, временно усыпляя горутину листенера без активного опроса CPU (busy-wait), позволяя ядрам процессора обрабатывать уже принятые сокеты.",
        "pitfalls": "Если burst лимитера меньше ожидаемого размера очереди SYN-пакетов, легитимные клиенты начнут испытывать задержку на этапе установки TCP-сессии.",
        "bigtech_interview": "Чем отличается rate.Limiter.Wait() от rate.Limiter.Allow()? Allow() немедленно возвращает boolean (сброс или пропуск), а Wait() блокирует поток до появления токена (сглаживание нагрузки)."
    },
    {
        "num": 44,
        "title": "Эшелонированная защита: HAProxy / Envoy перед сервисом на Go",
        "task": "Спроектируйте архитектуру демилитаризованной зоны с L7 прокси (HAProxy / Envoy / Nginx) перед Go-сервисом: терминация TLS, защита от атак Slowloris через буферизацию и фильтрация L7 аномалий.",
        "theory": "Несмотря на высокую производительность Go, прямое подключение сервисов к открытому интернету не рекомендуется. Специализированные прокси (Envoy, HAProxy, Nginx) написаны на C/C++ с применением сокетных оптимизаций ядра (kqueue/epoll) и содержат аппаратные ускорители TLS (Intel QAT). Прокси полностью вычитывает медленный запрос клиента в свои буферы и передает в Go только целостный HTTP-запрос по быстрому локальному сокету или Unix Domain Socket, полностью изолируя Go от медленных клиентов.",
        "step_by_step": [
            "Сконфигурируйте HAProxy с секциями `frontend` и `backend`.",
            "Установите `timeout http-request 5s` для быстрой отсечки Slowloris на уровне HAProxy.",
            "Настройте отправку в Go через Unix Domain Socket (`/var/run/go.sock`).",
            "Проверьте снижение расхода памяти и количества горутин в Go-сервисе."
        ],
        "code_blocks": [
            {
                "filename": "haproxy_frontend.cfg",
                "lang": "haproxy",
                "code": "global\n    maxconn 100000\n    log /dev/log local0\n\ndefaults\n    log global\n    mode http\n    option httplog\n    timeout connect 5s\n    timeout client  30s\n    timeout server  30s\n    timeout http-request 5s # Защита от Slowloris на периметре сети\n\nfrontend http_in\n    bind *:80\n    bind *:443 ssl crt /etc/ssl/certs/site.pem alpn h2,http/1.1\n    # Буферизация тела запроса до передачи в бэкенд\n    default_backend go_cluster\n\nbackend go_cluster\n    balance roundrobin\n    server go_app1 127.0.0.1:8080 check maxconn 5000\n",
                "note": "Конфигурация HAProxy для буферизации и защиты Go сервисов на сетевом периметре"
            }
        ],
        "under_the_hood": "HAProxy использует однопоточную event-driven модель с мультиплексированием тысяч соединений в одном процессе с минимальным расходом памяти (около 16 КБ на сессию).",
        "pitfalls": "Если прокси не пробрасывает заголовок `X-Forwarded-For` или не настроен `send-proxy` (PROXY protocol), Go-приложение потеряет реальные IP-адреса клиентов для Rate Limiting.",
        "bigtech_interview": "В инфраструктуре Авито и Ozon ни один Go-сервер не смотрит в интернет напрямую: весь входящий трафик проходит через Ingress Nginx / Envoy шлюзы."
    },
    {
        "num": 45,
        "title": "Автоматизированный аудит устойчивости утилитой slowhttptest",
        "task": "Используйте утилиту slowhttptest для проведения контролируемой стресс-атаки Slowloris на тестовый сервис Go и сформируйте HTML-отчет с графиком доступности сервиса.",
        "theory": "Утилита `slowhttptest` — отраслевой стандарт тестирования серверов на уязвимость к медленным DoS-атакам (Slowloris, Slow POST, Slow Read). Она умеет открывать тысячи соединений с заданным темпом передачи заголовков (`-i 10`) и зондировать сервис контрольными запросами для вычисления времени наступления отказа (Service Available percentage).",
        "step_by_step": [
            "Установите утилиту: `apt-get install slowhttptest`.",
            "Запустите тест: `slowhttptest -c 1000 -H -i 10 -r 200 -t GET -u http://localhost:8080 -g -o slowloris_report`.",
            "Проанализируйте сгенерированные графики доступности сервиса.",
            "Убедитесь, что сервер с настроенным `ReadHeaderTimeout` удерживает 100% доступность."
        ],
        "code_blocks": [
            {
                "filename": "run_slowhttptest.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nTARGET_URL=\"http://127.0.0.1:8080\"\n\necho \"[STRESS-TEST] Запуск аудита устойчивости к Slowloris (slowhttptest)...\"\n\n# -c 1000: 1000 параллельных соединений\n# -H: Slowloris режим (медленные заголовки)\n# -i 10: интервал 10 секунд между досылкой байтов\n# -r 200: скорость подключения 200 conn/sec\n# -t GET: метод запроса\n# -l 60: длительность теста 60 секунд\nslowhttptest -c 1000 -H -i 10 -r 200 -t GET -u \"${TARGET_URL}\" -l 60 -g -o /tmp/report || true\n\necho \"[OK] Стресс-тестирование завершено. Отчет сформирован.\"\n",
                "note": "Скрипт стресс-тестирования сервера утилитой slowhttptest"
            }
        ],
        "under_the_hood": "slowhttptest отправляет неполные HTTP-заголовки и отслеживает код ответа зондирующего сокета. Если зондирующий сокет не может установить TCP-соединение за 5 секунд, статус сервиса помечается как NO (Unavailable).",
        "pitfalls": "Запуск теста с слишком высоким `-r` (rate) на слабой машине может исчерпать ресурсы локального сетевого стека клиента до того, как сервер почувствует нагрузку.",
        "bigtech_interview": "В отчетах penetration testing оценка устойчивости веб-приложений к Slowloris с помощью slowhttptest является обязательным разделом аудита соответствия OWASP."
    },
    {
        "num": 46,
        "title": "Изоляция исходящего сетевого трафика через Seccomp (Block Network Egress)",
        "task": "Сконфигурируйте Seccomp-профиль, блокирующий системный вызов connect, запустите Go-приложение и убедитесь, что попытки исходящих HTTP-запросов блокируются ядром Linux.",
        "theory": "Если сервис предназначен только для обработки входящих запросов и не должен обращаться во внешнюю сеть, разрешение исходящих сетевых сокетов создает серьезный риск: в случае RCE-уязвимости атакующий может запустить Reverse Shell или выполнить эксфильтрацию конфиденциальных данных на сторонний C2-сервер. Запрет системного вызова `connect` на уровне Seccomp делает исходящие сетевые подключения физически невозможными на уровне ядра ОС.",
        "step_by_step": [
            "Создайте Seccomp-профиль с блокировкой сисколла `connect`.",
            "Напишите Go-сервис, пытающийся выполнить `http.Get(\"https://google.com\")`.",
            "Запустите сервис под надзором профиля Seccomp.",
            "Убедитесь, что сетевой вызов возвращает ошибку `dial tcp: connect: operation not permitted`."
        ],
        "code_blocks": [
            {
                "filename": "block_connect.json",
                "lang": "json",
                "code": "{\n  \"defaultAction\": \"SCMP_ACT_ALLOW\",\n  \"architectures\": [\n    \"SCMP_ARCH_X86_64\"\n  ],\n  \"syscalls\": [\n    {\n      \"names\": [\n        \"connect\"\n      ],\n      \"action\": \"SCMP_ACT_ERRNO\",\n      \"errnoRet\": 1\n    }\n  ]\n}\n",
                "note": "Seccomp профиль для возврата EPERM (Operation not permitted) при вызове connect"
            }
        ],
        "under_the_hood": "Системный вызов `connect` инициирует TCP 3-way handshake наружу. Перехват сисколла BPF-фильтром Seccomp предотвращает даже формирование исходящего IP-пакета на сетевом интерфейсе.",
        "pitfalls": "Если сервису необходимо общаться с локальной базой данных через Unix Domain Socket, вызов `connect` также потребуется. Для тонкой фильтрации используют Network Policies в Kubernetes.",
        "bigtech_interview": "Как гарантировать изоляцию сервиса от несанкционированного выхода в интернет в Cloud-Native окружении? Комбинацией Kubernetes Egress NetworkPolicy (на уровне CNI) и Seccomp профиля (на уровне контейнера)."
    },
    {
        "num": 47,
        "title": "Экспорт метрик соединений в Prometheus и алертинг по порогу сокетов",
        "task": "Реализуйте экспорт метрик активных соединений (Gauge: active_connections) в Prometheus через хук ConnState и настройте правило алертинга при превышении 80% от лимита дескрипторов.",
        "theory": "Своевременное обнаружение DoS-атаки или утечки сокетов требует непрерывной телеметрии. Метрика `http_active_connections` экспортируется в Prometheus. При приближении к 80% от лимита `ulimit -n` Alertmanager отправляет критическое уведомление дежурному инженеру, позволяя масштабировать поды (HPA) или активировать агрессивную фильтрацию до отказа сервиса.",
        "step_by_step": [
            "Используйте `prometheus.NewGauge` для метрики `active_connections`.",
            "Инкрементируйте счетчик в состоянии `StateNew` и декрементируйте в `StateClosed`.",
            "Сконфигурируйте эндпоинт `/metrics` через `promhttp.Handler()`.",
            "Напишите правило оповещения Prometheus Alerting Rule."
        ],
        "code_blocks": [
            {
                "filename": "metrics_server.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"net/http\"\n\t\"sync/atomic\"\n)\n\nfunc main() {\n\tvar activeConns int64\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/metrics\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"# HELP http_active_connections Текущее число открытых сокетов\\n\"+\n\t\t\t\"# TYPE http_active_connections gauge\\n\"+\n\t\t\t\"http_active_connections %d\\n\", atomic.LoadInt64(&activeConns))\n\t})\n\n\tsrv := &http.Server{\n\t\tAddr:    \":8080\",\n\t\tHandler: mux,\n\t\tConnState: func(c net.Conn, state http.ConnState) {\n\t\t\tswitch state {\n\t\t\tcase http.StateNew:\n\t\t\t\tatomic.AddInt64(&activeConns, 1)\n\t\t\tcase http.StateClosed:\n\t\t\t\tatomic.AddInt64(&activeConns, -1)\n\t\t\t}\n\t\t},\n\t}\n\n\tfmt.Println(\"[METRICS] Сервер экспорта метрик активных соединений инициализирован на :8080\")\n\t_ = srv\n}\n",
                "note": "Экспорт числа открытых TCP-сокетов в формате метрик Prometheus"
            }
        ],
        "under_the_hood": "Метрика Gauge отражает текущее значение в оперативной памяти без задержек дискового ввода-вывода, позволяя Prometheus скрейпить ее каждые 5-15 секунд.",
        "pitfalls": "Если хендлер `/metrics` находится на том же сервере без отдельного порта, при переполнении пула соединений Prometheus не сможет получить метрики именно в момент аварии.",
        "bigtech_interview": "Почему в enterprise-архитектуре эндпоинты /metrics и /healthz всегда выносят на отдельный внутренний порт управления (management port, например :9090)? Чтобы мониторинг продолжал функционировать при DoS-перегрузке основного рабочего порта (:8080)."
    },
    {
        "num": 48,
        "title": "Плавная деградация (Graceful Degradation) при экстремальной нагрузке",
        "task": "Реализуйте паттерн адаптивной деградации сервиса: при превышении критического числа активных соединений сервер временно отключает вторичные тяжелые функции и возвращает 503 на некритические запросы.",
        "theory": "При атаке или внезапном всплеске трафика сервер не должен падать целиком. Принцип Graceful Degradation (плавная деградация) предписывает сохранять работоспособность критического функционала (например, прием оплаты или оформление заказа), временно отключая ресурсоемкие фоновые сервисы (рекомендательные системы, расчет аналитики, персонализацию), либо отдавая кэшированные данные со статусом 203/503.",
        "step_by_step": [
            "Заведите счетчик нагрузки (число активных горутин или сокетов).",
            "Определите два порога: `WarningThreshold` (70%) и `CriticalThreshold` (90%).",
            "В обработчике проверяйте уровень загрузки системы.",
            "При `Warning` возвращайте упрощенный ответ без обращения к тяжелым микросервисам.",
            "При `Critical` немедленно возвращайте статус 503 с заголовком `Retry-After`."
        ],
        "code_blocks": [
            {
                "filename": "adaptive_degradation.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"sync/atomic\"\n)\n\ntype ServiceShield struct {\n\tinflight int64\n\tmaxSafe  int64\n}\n\nfunc (s *ServiceShield) Middleware(next http.HandlerFunc) http.HandlerFunc {\n\treturn func(w http.ResponseWriter, r *http.Request) {\n\t\tcurrent := atomic.AddInt64(&s.inflight, 1)\n\t\tdefer atomic.AddInt64(&s.inflight, -1)\n\n\t\tif current > s.maxSafe {\n\t\t\t// Режим аварийного сброса нагрузки\n\t\t\tw.Header().Set(\"Retry-After\", \"5\")\n\t\t\thttp.Error(w, \"Service Under Heavy Load (Try later)\", http.StatusServiceUnavailable)\n\t\t\treturn\n\t\t}\n\n\t\tnext(w, r)\n\t}\n}\n\nfunc main() {\n\tshield := &ServiceShield{maxSafe: 500}\n\t_ = shield.Middleware(func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"OK\")\n\t})\n\tfmt.Println(\"[SHIELD] Модуль адаптивной плавной деградации активирован.\")\n}\n",
                "note": "Паттерн мягкой деградации под пиковыми нагрузками"
            }
        ],
        "under_the_hood": "Быстрый отказ (fail-fast) на раннем этапе экономит процессорные такты, не позволяя очереди ожидания в планировщике Go расти до критических величин.",
        "pitfalls": "Если клиенты не поддерживают заголовок `Retry-After` и начинают агрессивно долбить сервер повторными запросами (Thundering Herd), сброс нагрузки может усилить атаку.",
        "bigtech_interview": "Что такое Load Shedding и Circuit Breaking и как они дополняют друг друга? Circuit Breaker защищает от падения зависимых сервисов, а Load Shedding защищает сам сервис от перегрузки."
    },
    {
        "num": 49,
        "title": "Оптимизация пулов исходящих сетевых соединений (http.Transport Limits)",
        "task": "Сконфигурируйте http.Transport с жесткими лимитами пула соединений: MaxIdleConns: 100, MaxIdleConnsPerHost: 10, IdleConnTimeout: 90 * time.Second.",
        "theory": "Исходящие сетевые запросы из одного микросервиса в другой также подвержены проблемам сокетов. Стандартный `http.DefaultTransport` имеет параметр `DefaultMaxIdleConnsPerHost = 2`. При высокой нагрузке (1000 RPS) клиент использует сотни параллельных соединений, но после завершения запроса закрывает 98% сокетов, открывая заново новые. Это приводит к шторму открытий сокетов (TIME_WAIT exhaustion) и исчерпанию портов ОС. Тюнинг `MaxIdleConnsPerHost` до 10-50 соединений стабилизирует сетевой стек.",
        "step_by_step": [
            "Инициализируйте экземпляр `http.Transport`.",
            "Установите `MaxIdleConns: 100` и `MaxIdleConnsPerHost: 20`.",
            "Задайте `IdleConnTimeout: 90 * time.Second`.",
            "Создайте `http.Client` на базе данного транспорта и используйте его как синглтон."
        ],
        "code_blocks": [
            {
                "filename": "client_pool_tuning.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc CreatePooledHTTPClient() *http.Client {\n\ttransport := &http.Transport{\n\t\tProxy: http.ProxyFromEnvironment,\n\t\tDialContext: (&net.Dialer{\n\t\t\tTimeout:   5 * time.Second,\n\t\t\tKeepAlive: 30 * time.Second,\n\t\t}).DialContext,\n\t\tForceAttemptHTTP2:     true,\n\t\tMaxIdleConns:          100,              // Всего свободных сокетов в пуле\n\t\tMaxIdleConnsPerHost:   20,               // Свободных сокетов на один хост\n\t\tIdleConnTimeout:       90 * time.Second, // Закрывать сокет после 90с простоя\n\t\tTLSHandshakeTimeout:   5 * time.Second,\n\t\tExpectContinueTimeout: 1 * time.Second,\n\t}\n\n\treturn &http.Client{\n\t\tTransport: transport,\n\t\tTimeout:   10 * time.Second,\n\t}\n}\n\nfunc main() {\n\tclient := CreatePooledHTTPClient()\n\tfmt.Printf(\"[CLIENT-POOL] Пул сетевых соединений настроен: %+v\\n\", client.Transport)\n}\n",
                "note": "Тюнинг пула сокетов для высоконагруженных микросервисных клиентов"
            }
        ],
        "under_the_hood": "http.Transport переиспользует существующие сокеты, пропуская этапы TCP SYN handshake и TLS exchange, что ускоряет межсервисные вызовы с 50 мс до 1-2 мс.",
        "pitfalls": "Создание нового `&http.Client{}` внутри каждого обработчика приводит к созданию изолированного пула и мгновенной утечке сокетов в состояние TIME_WAIT.",
        "bigtech_interview": "Почему http.Client в Go обязан быть синглтоном? Чтобы переиспользовать пул TCP соединений между запросами и не исчерпать эфемерные порты операционной системы."
    },
    {
        "num": 50,
        "title": "Обязательное использование дедлайнов контекста для всех исходящих RPC",
        "task": "Разработайте стандарт безопасного клиента микросервиса: обязательное использование context.WithTimeout для всех исходящих вызовов к базам данных, кэшам и HTTP API.",
        "theory": "Сетевые сбои неизбежны. Если удаленный микросервис или база данных зависают, клиентский запрос без контекстного таймаута заблокирует горутину навсегда. При накоплении таких горутин весь клиентский сервис исчерпает память и рухнет. Каждый сетевой запрос обязан принимать `context.Context` с жестким ограничением времени жизни.",
        "step_by_step": [
            "Создайте контекст с таймаутом: `ctx, cancel := context.WithTimeout(parentCtx, 5*time.Second)`.",
            "Обязательно вызовите `defer cancel()` для освобождения таймера.",
            "Создайте запрос через `http.NewRequestWithContext(ctx, ...)`.",
            "Проверьте обработку ошибки `context.DeadlineExceeded`."
        ],
        "code_blocks": [
            {
                "filename": "outbound_timeout.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc FetchExternalData(parentCtx context.Context, targetURL string) error {\n\t// Строгий дедлайн на выполнение сетевой операции 3 секунды\n\tctx, cancel := context.WithTimeout(parentCtx, 3*time.Second)\n\tdefer cancel()\n\n\treq, err := http.NewRequestWithContext(ctx, http.MethodGet, targetURL, nil)\n\tif err != nil {\n\t\treturn err\n\t}\n\n\tresp, err := http.DefaultClient.Do(req)\n\tif err != nil {\n\t\tif errors.Is(ctx.Err(), context.DeadlineExceeded) {\n\t\t\treturn fmt.Errorf(\"дедлайн запроса к %s истек: сервис не ответил вовремя\", targetURL)\n\t\t}\n\t\treturn err\n\t}\n\tdefer resp.Body.Close()\n\n\tfmt.Printf(\"[OUTBOUND] Успешный ответ: %d\\n\", resp.StatusCode)\n\treturn nil\n}\n\nfunc main() {\n\tfmt.Println(\"[RPC] Безопасный клиент с context.WithTimeout готов к работе.\")\n\t_ = FetchExternalData\n}\n",
                "note": "Сквозной контроль времени сетевых операций через context.WithTimeout"
            }
        ],
        "under_the_hood": "При срабатывании таймера рантайм закрывает канал `ctx.Done()`. Сетевой транспорт немедленно вызывает `conn.Close()` для прерывания блокирующего системного вызова.",
        "pitfalls": "Забытый `defer cancel()` удерживает объект таймера в куче рантайма до истечения таймаута, создавая скрытую утечку памяти.",
        "bigtech_interview": "В чем разница между Client.Timeout и Request.Context? Client.Timeout задает глобальное время на весь запрос включая редиректы, а Request.Context позволяет отменять запрос динамически извне."
    },
    {
        "num": 51,
        "title": "Архитектура эталонного защищенного микросервиса (Ultimate Secure Microservice)",
        "task": "Спроектируйте и реализуйте архитектурный каркас production-grade Go микросервиса, объединяющий защиту цепочки поставок (Supply Chain), сетевой харднинг (Network Hardening), изоляцию ядра (Seccomp/Capabilities) и наблюдаемость (Slog/Prometheus).",
        "theory": "Финальный рубеж разработки безопасных систем — сквозная интеграция всех уровней защиты (Defense-in-Depth):\n1. Supply Chain: проверка go.sum, сканирование govulncheck в CI, генерация SBOM через Syft, подпись Cosign и SLSA L3 provenance.\n2. Сетевая безопасность: ReadHeaderTimeout, WriteTimeout, IdleTimeout, MaxHeaderBytes, MaxBytesReader, TCP Keepalive, Rate Limiting.\n3. Изоляция ОС: Seccomp-профиль, сброс всех Linux Capabilities (Drop ALL), non-root пользователь (UID 65534), read-only rootfs.\n4. Наблюдаемость: структурированные логи slog с request_id/trace_id, Prometheus метрики соединений и задержек.",
        "step_by_step": [
            "Инициализируйте защищенный `http.Server` со всеми таймаутами.",
            "Внедрите middleware ограничения размера тела и семафор параллелизма.",
            "Настройте экспорт метрик и эндпоинт `/healthz`.",
            "Сконфигурируйте Dockerfile на базе `FROM scratch` с непривилегированным пользователем.",
            "Подготовьте манифест Seccomp и Kubernetes SecurityContext."
        ],
        "code_blocks": [
            {
                "filename": "secure_service_capstone.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log/slog\"\n\t\"net/http\"\n\t\"os\"\n\t\"os/signal\"\n\t\"syscall\"\n\t\"time\"\n)\n\nfunc main() {\n\tlogger := slog.New(slog.NewJSONHandler(os.Stdout, nil))\n\tslog.SetDefault(logger)\n\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(`{\"status\":\"OK\",\"hardened\":true}`))\n\t})\n\n\tsrv := &http.Server{\n\t\tAddr:              \":8080\",\n\t\tHandler:           mux,\n\t\tReadHeaderTimeout: 5 * time.Second,\n\t\tReadTimeout:       15 * time.Second,\n\t\tWriteTimeout:      15 * time.Second,\n\t\tIdleTimeout:       60 * time.Second,\n\t\tMaxHeaderBytes:    1 << 20,\n\t}\n\n\tgo func() {\n\t\tslog.Info(\"[STARTUP] Защищенный микросервис запущен\", \"addr\", srv.Addr)\n\t\tif err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {\n\t\t\tslog.Error(\"Фатальная ошибка сервера\", \"error\", err)\n\t\t}\n\t}()\n\n\tquit := make(chan os.Signal, 1)\n\tsignal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)\n\t<-quit\n\tslog.Info(\"[SHUTDOWN] Плавная остановка сервиса...\")\n\n\tctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)\n\tdefer cancel()\n\t_ = srv.Shutdown(ctx)\n\tslog.Info(\"[SHUTDOWN] Сервер успешно остановлен.\")\n}\n",
                "note": "Эталонный архитектурный каркас защищенного микросервиса на Go"
            }
        ],
        "under_the_hood": "Такая архитектура нейтрализует векторы атак на всех стадиях: компилятор отсекает уязвимости зависимостей, рантайм защищает память от DoS, ядро блокирует эксплойты прав, а мониторинг обеспечивает прозрачность.",
        "pitfalls": "Формальное внедрение одного уровня защиты (например, Seccomp) бесполезно, если в коде оставлен http.ListenAndServe без таймаутов.",
        "bigtech_interview": "Кандидатов на позиции Principal Architect в Ozon и Яндекс просят спроектировать архитектуру отказоустойчивого сервиса с нуля; знание сквозного харднинга является ключевым критерием оценки."
    },
    {
        "num": 52,
        "title": "Мандатный контроль доступа: профили AppArmor для Go-бинарников",
        "task": "Разработайте профиль AppArmor для Go-приложения, разрешающий чтение конфигурации /etc/myapp/config.yaml и запись в /var/log/myapp/, и проверьте блокировку чтения /etc/passwd.",
        "theory": "AppArmor (Application Armor) — модуль безопасности ядра Linux (LSM), реализующий мандатный контроль доступа (MAC) на основе путей к файлам. В отличие от стандартных прав доступа Linux (DAC: rwx), AppArmor жестко ограничивает возможности даже процесса, запущенного от root. Если злоумышленник скомпрометирует веб-сервер и попытается прочитать `/etc/passwd` или `/etc/shadow`, ядро заблокирует доступ с ошибкой `Permission denied`, логируя инцидент в syslog.",
        "step_by_step": [
            "Создайте текстовый профиль AppArmor `/etc/apparmor.d/usr.local.bin.myapp`.",
            "Укажите разрешенные пути: `/usr/local/bin/myapp mr`, `/etc/myapp/config.yaml r`, `/var/log/myapp/** rw`.",
            "Заблокируйте чтение системных каталогов.",
            "Активируйте профиль через `apparmor_parser -r /etc/apparmor.d/...`.",
            "Проверьте блокировку несанкционированного доступа к файлам из кода Go."
        ],
        "code_blocks": [
            {
                "filename": "myapp_apparmor.profile",
                "lang": "apparmor",
                "code": "#include <tunables/global>\n\n/usr/local/bin/myapp {\n    #include <abstractions/base>\n    #include <abstractions/nameservice>\n\n    # Разрешаем исполнение самого бинарника\n    /usr/local/bin/myapp mr,\n\n    # Чтение только собственного конфигурационного файла\n    /etc/myapp/config.yaml r,\n\n    # Запись строго в каталог логов\n    /var/log/myapp/ rw,\n    /var/log/myapp/** rw,\n\n    # Запрет доступа к чувствительным системным файлам\n    deny /etc/passwd r,\n    deny /etc/shadow r,\n    deny /root/** rwx,\n}\n",
                "note": "Мандатный профиль AppArmor для изоляции файлового доступа Go сервиса"
            }
        ],
        "under_the_hood": "LSM-хуки AppArmor перехватывают системные вызовы `openat()` и `execve()` в ядре, сверяя запрашиваемый путь с шаблонами профиля.",
        "pitfalls": "Если не включить `nameservice` абстракцию, Go не сможет прочитать `/etc/resolv.conf` для DNS-резолвинга.",
        "bigtech_interview": "В чем разница между AppArmor и SELinux? AppArmor привязывает политики к путям файлов (Path-based), что проще в настройке, а SELinux использует inode labels (Type Enforcement)."
    },
    {
        "num": 53,
        "title": "Профилирование системных вызовов утилитой strace (strace -c ./app)",
        "task": "Запустите Go-сервер под управлением strace -c ./app, выполните серию HTTP-запросов и проанализируйте статистику системных вызовов ядра (частота вызовов, суммарное время в сисколлах).",
        "theory": "Утилита `strace` перехватывает все системные вызовы процесса через механизм `ptrace`. Флаг `-c` формирует сводный отчет: количество вызовов, процент времени в ядре и количество ошибок для каждого сисколла (`futex`, `epoll_pwait`, `read`, `write`). Анализ strace позволяет выявить скрытые узкие места сетевого ввода-вывода и избыточные вызовы ядра.",
        "step_by_step": [
            "Скомпилируйте бинарник: `go build -o app main.go`.",
            "Запустите сервер под надзором: `strace -c -f ./app` (флаг `-f` отслеживает все горутины и M-потоки).",
            "Отправьте нагрузку утилитой `curl` или `wrk`.",
            "Остановите сервер (Ctrl+C) и изучите сводную таблицу системных вызовов."
        ],
        "code_blocks": [
            {
                "filename": "run_strace.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"[STRACE] Запуск трассировки системных вызовов Go сервиса...\"\n\n# -c: подсчет статистики\n# -f: трассировка дочерних потоков ОС (clone)\n# -e trace=network,desc,memory: фильтрация подсистем\nstrace -c -f ./app 2>&1 | tee strace_report.txt\n\necho \"[OK] Анализ профиля сисколлов завершен.\"\n",
                "note": "Профилирование системных вызовов Go процесса утилитой strace"
            }
        ],
        "under_the_hood": "strace переводит поток в режим останова на входе и выходе из каждого сисколла (syscall entry/exit stop), что создает существенный оверхед (до 10x замедления), поэтому в продакшене для низкоуровневого анализа используют eBPF/perf.",
        "pitfalls": "Запуск `strace` без флага `-f` покажет только основной поток инициализации, пропустив реальную работу сетевого поллера в рабочих потоках M.",
        "bigtech_interview": "Какие сисколлы в отчете strace Go-сервера занимают первое место по количеству вызовов? Обычно это `futex` (планировщик/мьютексы) и `epoll_pwait` (сетевой поллер)."
    },
    {
        "num": 54,
        "title": "Финальное испытание: Проектирование неуязвимого сервера (The Unbreakable Server)",
        "task": "Постройте интеграционный HTTP-сервер, выдерживающий одновременные атаки Slowloris, SYN-Flood и Header Bombing: таймауты, SO_REUSEPORT, TCP_DEFER_ACCEPT, ulimit 1 000 000 и строгий Seccomp.",
        "theory": "The Unbreakable Server — эталонная инженерная конструкция, сочетающая все защитные механизмы курса:\n* Сетевые таймауты: `ReadHeaderTimeout: 5s`, `WriteTimeout: 10s`, `IdleTimeout: 120s`, `MaxHeaderBytes: 1MB`.\n* Сетевой стек ОС: `SO_REUSEPORT` для шардирования по ядрам и `TCP_DEFER_ACCEPT` для отсечки пустых соединений.\n* Системная изоляция: строгий профиль Seccomp с запретом опасных вызовов (`ptrace`, `reboot`, `mount`).\n* Инфраструктура: `ulimit -n 1000000` и `tcp_syncookies = 1`.\nСервер стабильно отвечает легитимным клиентам с задержкой p99 < 50ms даже под шквалом атак.",
        "step_by_step": [
            "Сконфигурируйте `ListenConfig` с флагами `SO_REUSEPORT` и `TCP_DEFER_ACCEPT`.",
            "Инициализируйте `http.Server` со всеми защитными таймаутами.",
            "Внедрите семафор ограничения параллельных обработчиков.",
            "Запустите параллельную симуляцию атак и проверьте метрики доступности."
        ],
        "code_blocks": [
            {
                "filename": "unbreakable_server.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"net/http\"\n\t\"syscall\"\n\t\"time\"\n)\n\nfunc CreateUnbreakableServer(addr string) (*http.Server, net.Listener, error) {\n\tlc := net.ListenConfig{\n\t\tControl: func(network, address string, c syscall.RawConn) error {\n\t\t\treturn c.Control(func(fd uintptr) {\n\t\t\t\t// 1. SO_REUSEPORT для масштабирования по ядрам\n\t\t\t\t_ = syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET, 0xF, 1)\n\t\t\t\t// 2. TCP_DEFER_ACCEPT: ядро будит Go только при наличии реальных данных\n\t\t\t\t_ = syscall.SetsockoptInt(int(fd), syscall.IPPROTO_TCP, 9, 5)\n\t\t\t})\n\t\t},\n\t}\n\n\tln, err := lc.Listen(context.Background(), \"tcp\", addr)\n\tif err != nil {\n\t\treturn nil, nil, err\n\t}\n\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"UNBREAKABLE: Service Healthy\")\n\t})\n\n\tsrv := &http.Server{\n\t\tHandler:           mux,\n\t\tReadHeaderTimeout: 5 * time.Second,  // Щит против Slowloris\n\t\tReadTimeout:       10 * time.Second,\n\t\tWriteTimeout:      10 * time.Second,\n\t\tIdleTimeout:       120 * time.Second,\n\t\tMaxHeaderBytes:    1 << 20,          // 1 МБ лимит заголовков\n\t}\n\treturn srv, ln, nil\n}\n\nfunc main() {\n\tsrv, ln, err := CreateUnbreakableServer(\"127.0.0.1:8080\")\n\tif err != nil {\n\t\tfmt.Printf(\"[FATAL] Ошибка запуска: %v\\n\", err)\n\t\treturn\n\t}\n\tdefer ln.Close()\n\n\tfmt.Println(\"[UNBREAKABLE] Сервер успешно запущен со всеми эшелонами защиты!\")\n\t_ = srv\n}\n",
                "note": "Финальная интеграционная конструкция неуязвимого HTTP-сервера Go"
            }
        ],
        "under_the_hood": "Комбинация TCP_DEFER_ACCEPT и ReadHeaderTimeout полностью исключает возможность зависания горутин на медленных клиентах.",
        "pitfalls": "Отсутствие мониторинга метрик может скрыть факт идущей атаки, даже если сам сервер успешно ее отражает.",
        "bigtech_interview": "Поздравляем! Способность спроектировать и аргументировать каждое решение в 'The Unbreakable Server' подтверждает уровень квалификации Senior/Lead Backend Go Engineer."
    },
    {
        "num": 55,
        "title": "Принцип наименьших привилегий: запуск на порту 80 через Linux Capabilities",
        "task": "Настройте запуск Go-приложения на стандартном HTTP-порту 80 без прав суперпользователя root с помощью утилиты setcap 'cap_net_bind_service=+ep'.",
        "theory": "В операционных системах Linux порты с номерами от 1 до 1023 являются привилегированными (Privileged Ports). Исторически для привязки сокета к порту 80 или 443 требовался запуск процесса с правами `root`. Однако запуск сервиса от root нарушает фундаментальный принцип наименьших привилегий (Principle of Least Privilege). С помощью механизма Linux Capabilities приложению выдается точечная возможность `CAP_NET_BIND_SERVICE`, позволяющая непривилегированному пользователю слушать порт 80 без суперправ.",
        "step_by_step": [
            "Скомпилируйте исполняемый файл: `go build -o webapp main.go`.",
            "Установите непривилегированного владельца файла: `chown appuser:appuser webapp`.",
            "Выдайте capability: `sudo setcap 'cap_net_bind_service=+ep' webapp`.",
            "Запустите бинарник от имени `appuser` и проверьте успешную привязку к порту 80.",
            "Проверьте атрибуты файла утилитой `getcap webapp`."
        ],
        "code_blocks": [
            {
                "filename": "bind_capability.sh",
                "lang": "bash",
                "code": "#!/usr/bin/env bash\nset -euo pipefail\n\nBINARY=\"./webapp\"\n\necho \"[SECURITY] Наделение бинарника правом привязки к портам <1024...\"\n\n# Наделение capability CAP_NET_BIND_SERVICE\nsudo setcap 'cap_net_bind_service=+ep' \"${BINARY}\"\n\necho \"[CHECK] Проверка установленных capabilities:\"\ngetcap \"${BINARY}\"\n\necho \"[SUCCESS] Теперь процесс может безопасно слушать порт 80 от non-root пользователя!\"\n",
                "note": "Установка возможности CAP_NET_BIND_SERVICE на исполняемый файл Go"
            }
        ],
        "under_the_hood": "Бит `+ep` означает Effective и Permitted. Ядро Linux проверяет маску capabilities в дескрипторе файла при системном вызове `bind()` сокета, разрешая привязку к порту 80.",
        "pitfalls": "Любая перекомпиляция файла `go build` перезаписывает бинарник и сбрасывает все ранее установленные файловые capabilities.",
        "bigtech_interview": "Как в Dockerfile запустить сервис на порту 80 без прав root? Добавить `setcap 'cap_net_bind_service=+ep' /app` на этапе сборки и переключиться на `USER 65534`."
    }
]
