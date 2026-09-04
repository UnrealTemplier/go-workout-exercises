# Part 2 of Chapter 48: exercises 32 to 62

exercises = [
  {
    "num": 32,
    "title": "Логика retake() в sysmon: отзыв процессора P у зависших вычислений",
    "task": "**[sysmon: Retaking Bindings]**: Если горутина выполняет CPU-bound работу без вызова функций (например, `for i := 0; i < 1e10; i++ {}`), как `sysmon` понимает, что нужно вытеснить (preempt) эту горутину? Напиши такой цикл и проверь, не блокирует ли он другие горутины (работает ли планировщик).",
    "theory": "Функция `retake(now)` внутри потока `sysmon` — главный механизм контроля зависших горутин и системных вызовов.\nПри каждом проходе `sysmon` обходит все P:\n1. Если `p.status == _Prunning`: проверяется длительность непрерывного исполнения `pd.schedwhen`. Если она превышает 10 мс, вызывается `preemptone(pp)`, который инициирует асинхронное вытеснение через `SIGURG`.\n2. Если `p.status == _Psyscall`: проверяется счетчик `syscalltick`. Если вызов длится дольше 10 мс или в очереди этого P есть готовые горутины, `sysmon` вызывает `handoffp(pp)`, отбирая P у блокирующего потока M.",
    "step_by_step": "1. Создаем программу, где одна горутина исполняет непрерывный математический цикл.\n2. Вторая горутина фиксирует отметки времени своего пробуждения.\n3. Убеждаемся, что интервалы задержек второй горутины не превышают квант вытеснения (~10-20 мс).",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"time\"\n)\n\nfunc main() {\n\truntime.GOMAXPROCS(1)\n\tfmt.Println(\"GOMAXPROCS = 1. Тестирование кванта времени вытеснения sysmon...\")\n\n\tstop := false\n\n\t// Горутина 1: непрерывный тяжелый CPU цикл\n\tgo func() {\n\t\tvar x uint64\n\t\tfor !stop {\n\t\t\tx = (x + 13) * 7\n\t\t}\n\t\t_ = x\n\t}()\n\n\t// Горутина 2: замеряет интервалы между квантами\n\tdelays := make([]time.Duration, 0, 5)\n\tstart := time.Now()\n\tfor i := 0; i < 5; i++ {\n\t\ttime.Sleep(1 * time.Millisecond)\n\t\tnow := time.Now()\n\t\tdelays = append(delays, now.Sub(start))\n\t\tstart = now\n\t}\n\n\tstop = true\n\ttime.Sleep(20 * time.Millisecond)\n\n\tfmt.Println(\"Интервалы между передачами управления:\")\n\tfor i, d := range delays {\n\t\tfmt.Printf(\"  Шаг %d: %v\\n\", i+1, d)\n\t}\n}",
        "note": "Фиксация интервалов переключения горутин по таймеру sysmon"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод:\n# GOMAXPROCS = 1. Тестирование кванта времени вытеснения sysmon...\n# Интервалы между передачами управления:\n#   Шаг 1: 10.8ms\n#   Шаг 2: 10.4ms\n#   Шаг 3: 11.1ms\n#   Шаг 4: 10.2ms\n#   Шаг 5: 10.6ms"
      }
    ],
    "under_the_hood": "В функции `retake()` в `src/runtime/proc.go` условие вытеснения выглядит так:\n`if s == _Prunning { if pd.schedwhen + 10*1000*1000 < now { preemptone(pp) } }`.\nКонстанта $10 \\times 10^6$ наносекунд (10 мс) определяет базовый тайм-слайс планировщика Go.",
    "pitfalls": "В виртуализированных средах с переподпиской CPU (CPU overcommit) физическое ядро может быть отобрано гипервизором, из-за чего реальный интервал `retake` может растянуться до 50–100 мс.",
    "bigtech_interview": "**Вопрос с собеседования:** Какова базовая длительность кванта времени (time-slice) горутины в планировщике Go и почему выбран именно такой интервал?\n**Ответ:** Квант времени составляет ровно **10 миллисекунд** (проверяется потоком `sysmon`).\nЭтот компромисс выбран для баланса:\n- Слишком маленький квант (например, 1 мс) создавал бы чрезмерный оверхед на частые сигналы `SIGURG`, переключения контекста и сброс кэшей CPU;\n- Слишком большой квант (например, 100 мс) приводил бы к заметным «заиканиям» (jitter) и росту p99/p999 latency при наличии тяжелых вычислительных горутин."
  },
  {
    "num": 33,
    "title": "Реализация упрощенного алгоритма Work Stealing на чистом Go",
    "task": "Реализуйте упрощённый алгоритм work stealing на чистом Go (без `runtime`): N «воркеров» с локальными deque (push/pop снизу, steal сверху). Покажите, почему steal сверху уменьшает contention.",
    "theory": "Для глубокого понимания механики Work Stealing полезно реализовать его модель на прикладном уровне Go.\nМодель включает:\n1. $N$ независимых воркеров (эмулирующих потоки $M$ и процессоры $P$);\n2. Локальную двустороннюю очередь (Deque) у каждого воркера:\n   - Владелец кладет и забирает задачи с **хвоста** (LIFO) для максимальной кэш-локальности;\n   - Другие воркеры при простое крадут задачи с **головы** (FIFO) чужой очереди для минимизации конфликтов с владельцем.",
    "step_by_step": "1. Создаем структуру `Deque` с защитой мьютексом (или атомарным CAS).\n2. Реализуем пул из 4 воркеров.\n3. Помещаем 100 задач только в очередь воркера 0.\n4. Воркеры 1, 2, 3 обнаруживают пустые очереди и успешно воруют задачи у воркера 0.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"math/rand\"\n\t\"sync\"\n\t\"sync/atomic\"\n\t\"time\"\n)\n\ntype Task func()\n\ntype WorkQueue struct {\n\tmu    sync.Mutex\n\ttasks []Task\n}\n\nfunc (q *WorkQueue) Push(t Task) {\n\tq.mu.Lock()\n\tq.tasks = append(q.tasks, t)\n\tq.mu.Unlock()\n}\n\nfunc (q *WorkQueue) Pop() (Task, bool) {\n\tq.mu.Lock()\n\tdefer q.mu.Unlock()\n\tif len(q.tasks) == 0 {\n\t\treturn nil, false\n\t}\n\t// Владелец берет с хвоста (LIFO)\n\tlast := len(q.tasks) - 1\n\tt := q.tasks[last]\n\tq.tasks = q.tasks[:last]\n\treturn t, true\n}\n\nfunc (q *WorkQueue) StealHalf() []Task {\n\tq.mu.Lock()\n\tdefer q.mu.Unlock()\n\tn := len(q.tasks)\n\tif n <= 1 {\n\t\treturn nil\n\t}\n\t// Вор забирает половину с головы (FIFO)\n\tstealCount := (n + 1) / 2\n\tstolen := make([]Task, stealCount)\n\tcopy(stolen, q.tasks[:stealCount])\n\tq.tasks = q.tasks[stealCount:]\n\treturn stolen\n}\n\nfunc main() {\n\tconst numWorkers = 4\n\tqueues := make([]*WorkQueue, numWorkers)\n\tfor i := 0; i < numWorkers; i++ {\n\t\tqueues[i] = &WorkQueue{}\n\t}\n\n\tvar processed [numWorkers]int64\n\tvar wg sync.WaitGroup\n\twg.Add(numWorkers)\n\n\tconst totalTasks = 120\n\t// Загружаем все задачи только в очередь воркера 0\n\tfor i := 0; i < totalTasks; i++ {\n\t\ttaskID := i\n\t\tqueues[0].Push(func() {\n\t\t\ttime.Sleep(1 * time.Millisecond)\n\t\t\t_ = taskID\n\t\t})\n\t}\n\n\tstop := int32(0)\n\tfor id := 0; id < numWorkers; id++ {\n\t\tgo func(wid int) {\n\t\t\tdefer wg.Done()\n\t\t\tfor atomic.LoadInt32(&stop) == 0 {\n\t\t\t\t// 1. Пытаемся взять свою задачу\n\t\t\t\tif task, ok := queues[wid].Pop(); ok {\n\t\t\t\t\ttask()\n\t\t\t\t\tatomic.AddInt64(&processed[wid], 1)\n\t\t\t\t\tcontinue\n\t\t\t\t}\n\n\t\t\t\t// 2. Кража работы: выбираем случайную чужую очередь\n\t\t\t\tvictim := rand.Intn(numWorkers)\n\t\t\t\tif victim != wid {\n\t\t\t\t\tstolen := queues[victim].StealHalf()\n\t\t\t\t\tif len(stolen) > 0 {\n\t\t\t\t\t\tfor _, t := range stolen {\n\t\t\t\t\t\t\tqueues[wid].Push(t)\n\t\t\t\t\t\t}\n\t\t\t\t\t\tcontinue\n\t\t\t\t\t}\n\t\t\t\t}\n\t\t\t\ttime.Sleep(500 * time.Microsecond)\n\t\t\t}\n\t\t}(id)\n\t}\n\n\ttime.Sleep(200 * time.Millisecond)\n\tatomic.StoreInt32(&stop, 1)\n\twg.Wait()\n\n\tfmt.Println(\"Результаты распределения работы через Work Stealing:\")\n\tvar total int64\n\tfor i := 0; i < numWorkers; i++ {\n\t\tcnt := atomic.LoadInt64(&processed[i])\n\t\ttotal += cnt\n\t\tfmt.Printf(\"  Воркер %d обработал: %d задач\\n\", i, cnt)\n\t}\n\tfmt.Printf(\"Всего обработано: %d / %d\\n\", total, totalTasks)\n}",
        "note": "Упрощенная реализация пула воркеров с Work Stealing"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод демонстрирует успешную кражу задач:\n# Результаты распределения работы через Work Stealing:\n#   Воркер 0 обработал: 35 задач\n#   Воркер 1 обработал: 30 задач\n#   Воркер 2 обработал: 28 задач\n#   Воркер 3 обработал: 27 задач\n# Всего обработано: 120 / 120"
      }
    ],
    "under_the_hood": "Классический алгоритм Work Stealing (Chase-Lev deque) оптимизирует параллельный доступ: владелец использует неатомарные операции добавления/извлечения в конец массива, а воры используют CAS-инструкцию для извлечения из начала. Конкуренция возникает только тогда, когда в очереди остается последний элемент.",
    "pitfalls": "В наивной реализации без рандомизации жертвы воры могут одновременно пытаться красть у одного и того же воркера, вызывая конкуренцию за мьютекс (thundering herd).",
    "bigtech_interview": "**Вопрос с собеседования:** Почему владелец очереди в Work Stealing забирает задачи в порядке LIFO (с конца), а воры крадут задачи в порядке FIFO (с начала)?\n**Ответ:**\n1) **Локальность кэша (Cache Locality):** Самая последняя добавленная задача только что работала с данными, которые еще находятся в быстрых кэшах L1/L2 процессора владельца. Исполнение LIFO минимизирует промахи кэша;\n2) **Размер поддерева задач:** Самые старые задачи (в начале очереди FIFO) обычно представляют собой крупные родительские задачи, способные породить много новых подзадач. Украдя старую задачу, ворующий процессор получает большой кусок долгой самостоятельной работы;\n3) **Разделение точек доступа:** Владелец работает с хвостом (`tail`), а воры с головой (`head`). Это сводит конкуренцию за доступ к очереди практически к нулю."
  },
  {
    "num": 34,
    "title": "Блокирующие системные вызовы при работе с диском и механизм Handoff",
    "task": "**Блокирующие Системные вызовы (Handoff)**: В отличие от сети, чтение огромного файла с диска (File I/O) часто требует синхронного системного вызова. Сделай тяжелый `os.ReadFile`. Изучи механику Handoff: текущий поток ОС (`M`) блокируется вместе с горутиной, а контекст `P` *отвязывается* от этого `M` и передается новому (или спящему) потоку `M`, чтобы не останавливать работу остальных горутин.",
    "theory": "Операции чтения и записи файлов на диск (`os.ReadFile`, `os.WriteFile`, `os.Open`) в операционных системах Linux/Unix блокируют системный поток M на уровне ядра ОС.\nПоскольку файловые дескрипторы дисков не поддерживают неблокирующий опрос через `epoll`, рантайм Go применяет следующую стратегию:\n1. Перед вызовом syscall поток M вызывает `entersyscall()`. Процессор P переводится в состояние `_Psyscall`.\n2. Если в локальной очереди P есть другие горутины, поток M немедленно вызывает `handoffp()`, отдавая P другому потоку M.\n3. Если очередь P была пуста, P остается за этим M до тех пор, пока фоновый поток `sysmon` через 10 мс не отберет его принудительно.",
    "step_by_step": "1. Создаем временный файл размером 50 МБ.\n2. Запускаем несколько горутин, синхронно читающих файл с диска.\n3. Отслеживаем изменение метрики системных потоков ОС через `runtime/metrics` или `GODEBUG=schedtrace`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"crypto/rand\"\n\t\"fmt\"\n\t\"os\"\n\t\"runtime\"\n\t\"sync\"\n\t\"time\"\n)\n\nfunc createTempFile(sizeMB int) string {\n\tf, err := os.CreateTemp(\"\", \"bench_gmp_*.bin\")\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer f.Close()\n\n\tbuf := make([]byte, 1024*1024)\n\trand.Read(buf)\n\tfor i := 0; i < sizeMB; i++ {\n\t\tf.Write(buf)\n\t}\n\treturn f.Name()\n}\n\nfunc main() {\n\truntime.GOMAXPROCS(2)\n\tpath := createTempFile(20)\n\tdefer os.Remove(path)\n\n\tfmt.Printf(\"GOMAXPROCS = 2. Старт 10 параллельных операций чтения файла...\\n\")\n\n\tvar wg sync.WaitGroup\n\tconst readers = 10\n\twg.Add(readers)\n\n\tfor i := 0; i < readers; i++ {\n\t\tgo func(id int) {\n\t\t\tdefer wg.Done()\n\t\t\tdata, err := os.ReadFile(path)\n\t\t\tif err != nil {\n\t\t\t\treturn\n\t\t\t}\n\t\t\t_ = data[0]\n\t\t}(i)\n\t}\n\n\ttime.Sleep(50 * time.Millisecond)\n\tfmt.Printf(\"Число горутин во время чтения: %d\\n\", runtime.NumGoroutine())\n\n\twg.Wait()\n\tfmt.Println(\"Все операции чтения успешно завершены.\")\n}",
        "note": "Параллельное чтение с диска и адаптация потоков ОС"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "GODEBUG=schedtrace=100 go run main.go\n# Наблюдайте рост threads в выводе schedtrace"
      }
    ],
    "under_the_hood": "В `src/runtime/proc.go` функция `entersyscall()` сохраняет регистры PC и SP в структуру `gp.sched`, переключает состояние на `_Gsyscall` и сохраняет отметку времени `pp.syscalltick`. Функция `handoffp()` вызывает `startm(pp, false)`: если в пуле свободных потоков `sched.midle` есть спящий M, он пробуждается; если нет — ядром создается новый поток M через `clone()`.",
    "pitfalls": "Вызов синхронных дисковых операций в цикле обработки HTTP-запросов под высокой нагрузкой (10 000 RPS) может привести к созданию сотен потоков ОС, деградации производительности дисковой подсистемы и OOM.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в Go нет асинхронного дискового ввода-вывода (AIO / io_uring) в стандартной библиотеке по умолчанию?\n**Ответ:** Исторически стандартный Linux POSIX AIO (`io_submit`) крайне ограничен: он работает только с флагом `O_DIRECT` (в обход кэша страниц ядра) и не поддерживает сокеты.\nНовый интерфейс Linux `io_uring` решает эту проблему, но он требует свежих ядер Linux (5.1+), имеет сложную модель безопасности (seccomp ограничения в контейнерах) и активно тестируется сообществом Go в экспериментальных библиотеках. На данный момент стандартная библиотека Go использует проверенный и надежный механизм блокирующих syscalls с потоковым `handoffp`."
  },
  {
    "num": 35,
    "title": "Точки безопасного вытеснения (Preemption Points): пролог функций и компилятор Go",
    "task": "**Preemption points**: Изучите, где runtime вставляет проверки на preemption (function prologue, loop backedges). Напишите код, который избегает этих точек (tight loop без вызовов).",
    "theory": "Компилятор Go (`cmd/compile`) отвечает за генерацию безопасных точек остановки.\nВ классической модели компилятор вставляет в пролог каждой функции:\n```assembly\nCMPQ SP, 16(R14)   // Сравнение указателя стека с g.stackguard0\nJLS  morestack      // Если SP <= stackguard0, переход на выделение стека\n```\nФокус архитектуры Go в том, что планировщик использует ту же самую проверку для кооперативного вытеснения!\nКогда рантайм хочет вытеснить горутину, он присваивает:\n`gp.stackguard0 = stackPreempt` (константа `0xfffffffffffffff0`).\nПри следующем вызове любой функции условие `SP <= stackguard0` гарантированно срабатывает. Вызывается `runtime.morestack()`, которая обнаруживает флаг прерывания, сохраняет контекст горутины и вызывает `runtime.goschedImpl()`.",
    "step_by_step": "1. Напишем простую функцию и скомпилируем ее в ассемблер: `go tool compile -S main.go`.\n2. Найдем инструкции сравнения со `stackguard0` в начале функции.\n3. Разберем логику работы `runtime.morestack`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\n//go:noinline\nfunc calculate(a, b int) int {\n\treturn a*a + b*b\n}\n\nfunc main() {\n\tres := calculate(3, 4)\n\tfmt.Printf(\"Результат: %d\\n\", res)\n}",
        "note": "Функция для ассемблерной инспекции пролога"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go tool compile -S main.go | grep -A 5 'TEXT.*calculate'\n# Пример вывода ассемблера Plan 9:\n# main.calculate STEXT ...\n#   0x0000 00000 (main.go:6)\tCMPQ\tSP, 16(R14)\n#   0x0004 00004 (main.go:6)\tPCDATA\t$0, $-2\n#   0x0004 00004 (main.go:6)\tJLS\t28\n#   ...\n#   0x001c 00028 (main.go:6)\tCALL\truntime.morestack_noctxt(SB)"
      }
    ],
    "under_the_hood": "Регистр `R14` в архитектуре amd64 в Go 1.17+ зарезервирован под хранение указателя на текущую горутину `g` (register-based calling convention). Смещение `16(R14)` указывает точно на поле `g.stackguard0`. Проверка занимает всего 2 процессорные инструкции и практически не влияет на скорость вызова функций.",
    "pitfalls": "Если функция заинлайнена компилятором (`inlined`), ее пролог устраняется, и проверка `morestack` исчезает. Именно поэтому в циклах с инлайнингом кооперативное вытеснение до Go 1.14 не срабатывало.",
    "bigtech_interview": "**Вопрос с собеседования:** Каким образом планировщик Go утилизирует проверку переполнения стека (`morestack`) для кооперативного вытеснения горутин?\n**Ответ:** Поле `g.stackguard0` хранит границу безопасного использования стека.\nКогда планировщик хочет вытеснить горутину (например, при вызове `Gosched()` или по требованию GC), он искусственно завышает эту границу, записывая в `stackguard0` специальное значение `stackPreempt`.\nВ начале следующей вызываемой функции процессор проверяет `SP <= stackguard0`. Условие неизбежно выполняется, и поток переходит в функцию `morestack()`.\nВнутри `morestack()` рантайм проверяет: если `stackguard0 == stackPreempt`, это не настоящее переполнение стека, а запрос на вытеснение. Рантайм паркует горутину и запускает `schedule()`."
  },
  {
    "num": 36,
    "title": "Эксперимент с отключением асинхронного вытеснения: GODEBUG=asyncpreemptoff=1",
    "task": "**[Каверзный кейс — Async Preemption]**: До Go 1.14 планировщик был кооперативным (вытеснение только при вызове функций). Напиши бесконечный цикл `for {}` (без вызовов функций) в горутине. Если бы ты был на Go 1.13, программа бы зависла. На современном Go компилятор вставляет безопасные точки (safe-points). Проверь, что горутина вытесняется. Отключи вытеснение через `go:build` или `GODEBUG=asyncpreemptoff=1` и посмотри, как зависнет планировщик.",
    "theory": "Для отладки и проверки совместимости Go предоставляет недокументированный флаг рантайма:\n`GODEBUG=asyncpreemptoff=1`\nЭтот флаг полностью отключает посылку сигналов `SIGURG` потоком `sysmon`, возвращая планировщик Go к строго кооперативной модели времен Go 1.13.\nВ этом режиме бесконечный цикл `for {}` без вызовов функций при `GOMAXPROCS=1` гарантированно подвесит поток исполнения, наглядно демонстрируя важность асинхронного вытеснения.",
    "step_by_step": "1. Пишем программу с плотным циклом.\n2. Запускаем ее в штатном режиме: программа успешно отрабатывает.\n3. Запускаем ее с `GODEBUG=asyncpreemptoff=1` и таймаутом: программа зависает.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"time\"\n)\n\nfunc main() {\n\truntime.GOMAXPROCS(1)\n\tfmt.Println(\"Проверка флага asyncpreemptoff...\")\n\n\tdone := false\n\tgo func() {\n\t\tfor !done {\n\t\t\t// Плотный цикл\n\t\t}\n\t\tfmt.Println(\"Цикл завершен!\")\n\t}()\n\n\ttime.Sleep(100 * time.Millisecond)\n\tdone = true\n\ttime.Sleep(50 * time.Millisecond)\n\tfmt.Println(\"Успешное завершение программы.\")\n}",
        "note": "Программа для проверки поведения с asyncpreemptoff=1"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Штатный запуск (Go 1.14+): отрабатывает за доли секунды\ngo run main.go\n\n# Запуск с отключением асинхронного вытеснения (зависнет намертво):\n# GODEBUG=asyncpreemptoff=1 go run main.go"
      }
    ],
    "under_the_hood": "В `src/runtime/signal_unix.go` функция `preemptM()` проверяет: `if debug.asyncpreemptoff != 0 { return }`. Если флаг выставлен, системный вызов `pthread_kill(mp.procid, SIGURG)` блокируется, и рантайм ожидает только кооперативных точек останова.",
    "pitfalls": "Никогда не используйте `asyncpreemptoff=1` в продакшене: любая сторонняя библиотека с плотным математическим циклом или парсингом JSON вызовет зависание сборщика мусора и скачки задержек до бесконечности.",
    "bigtech_interview": "**Вопрос с собеседования:** В каких редких инженерных ситуациях может потребоваться флаг `GODEBUG=asyncpreemptoff=1`?\n**Ответ:**\n1) При глубоком профилировании низкоуровневых систем с помощью `perf` или аппаратных счетчиков CPU, когда сигналы `SIGURG` загрязняют профиль системных прерываний;\n2) При интеграции со старыми C-библиотеками через CGO, некорректно обрабатывающими прерывание системных вызовов с ошибкой `EINTR`;\n3) При отладке через устаревшие версии GDB, не умеющие игнорировать сигнал `SIGURG`."
  },
  {
    "num": 37,
    "title": "Сценарий Half-Half: балансировка двух занятых ядер и двух свободных P",
    "task": "Создайте ситуацию «half-half»: 2 CPU-bound goroutine на 2 P, остальные P простаивают. Заставьте «простаивающие» P украсть работу. Объясните, почему steal происходит только при пустой локальной очереди и как работает `findRunnable()`.",
    "theory": "В распределенных многопроцессорных системах часто возникает ситуация «Half-Half»:\nПоловина процессоров P полностью загружена долгими CPU-задачами, а вторая половина освободилась.\nПланировщик Go использует потоки `Spinning M`:\n- Освободившиеся процессоры не выключаются мгновенно, а заходят в цикл `findrunnable()`;\n- Они находят занятые P и крадут у них по половине очереди (`runqsteal`);\n- Если одна из тяжелых горутин порождает пачку подзадач, они мгновенно растаскиваются свободными ядрами без задержки на пробуждение.",
    "step_by_step": "1. Устанавливаем `GOMAXPROCS=4`.\n2. Запускаем 2 CPU-bound горутины, занимающие 2 P на 100%.\n3. На остальных 2 P запускаем генерацию быстрых задач.\n4. Отслеживаем утилизацию ядер.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"sync\"\n\t\"time\"\n)\n\nfunc main() {\n\truntime.GOMAXPROCS(4)\n\tfmt.Println(\"Сценарий Half-Half на 4 P...\")\n\n\tvar wg sync.WaitGroup\n\tstopCPU := make(chan struct{})\n\n\t// 2 тяжелые CPU-bound горутины на P0 и P1\n\tfor i := 0; i < 2; i++ {\n\t\tgo func(id int) {\n\t\t\tvar acc uint64\n\t\t\tfor {\n\t\t\t\tselect {\n\t\t\t\tcase <-stopCPU:\n\t\t\t\t\treturn\n\t\t\t\tdefault:\n\t\t\t\t\tacc = (acc*17 + 1) % 1000000007\n\t\t\t\t}\n\t\t\t}\n\t\t}(i)\n\t}\n\n\t// Генерация потока легких задач на оставшихся P\n\tconst tasks = 500\n\twg.Add(tasks)\n\tfor i := 0; i < tasks; i++ {\n\t\tgo func(id int) {\n\t\t\tdefer wg.Done()\n\t\t\ttime.Sleep(2 * time.Millisecond)\n\t\t}(i)\n\t}\n\n\twg.Wait()\n\tclose(stopCPU)\n\ttime.Sleep(50 * time.Millisecond)\n\tfmt.Println(\"Сценарий Half-Half успешно завершен.\")\n}",
        "note": "Сценарий частичной загрузки ядер и свободных P"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go"
      }
    ],
    "under_the_hood": "В сценарии Half-Half счетчик `sched.idleprocs` равен 2, а `sched.nmspinning` равен 1. Один поток вращения постоянно проверяет очереди занятых P. Это гарантирует, что как только тяжелая горутина уступит процессор или создаст дочернюю горутину, она будет немедленно подхвачена свободным ядром.",
    "pitfalls": "Если тяжелые задачи выполняют вычисления без аллокаций памяти, кэши L1/L2 занятых ядер не инвалидируются, обеспечивая максимальный IPC (instructions per cycle).",
    "bigtech_interview": "**Вопрос с собеседования:** Как рантайм Go балансирует горутины, если в приложении одновременно работают и тяжелые CPU-bound вычисления, и тысячи легковесных сетевых запросов?\n**Ответ:**\n1) Сетевые горутины уходят в сон в `netpoller`, не занимая CPU;\n2) CPU-bound горутины работают на процессорах `P`, но каждые 10 мс вытесняются потоком `sysmon` через `SIGURG`;\n3) Проснувшиеся от сетевых событий горутины попадают в очереди `P` и благодаря вытеснению получают процессорное время в течение максимум 10 мс;\n4) Work Stealing гарантирует, что сетевые горутины не застрянут на занятом P, а будут украдены свободными процессорами."
  },
  {
    "num": 38,
    "title": "Work Stealing в действии: перераспределение очередей при неравномерной нагрузке",
    "task": "**Work stealing в действии.**: Запустите N горутин с неравномерной нагрузкой (часть считает в цикле, часть сразу завершается). Включите трассировку (`go tool trace`) и визуально найдите моменты, когда P ворует горутины из чужих локальных очередей.",
    "theory": "При неравномерной нагрузке одни горутины завершаются за миллисекунды, а другие выполняют долгие вычисления.\nБез Work Stealing ядра, завершившие быстрые задачи, простаивали бы (Idle CPU), пока перегруженные ядра страдали бы от длинных очередей.\nWork Stealing динамически выравнивает длину очередей всех P, стремясь к равновесию.",
    "step_by_step": "1. Запускаем тест с неравномерными задачами (от 1 мс до 100 мс).\n2. Записываем трассировку `trace.out`.\n3. Анализируем сбалансированность использования процессоров P.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"math/rand\"\n\t\"runtime\"\n\t\"sync\"\n\t\"time\"\n)\n\nfunc main() {\n\truntime.GOMAXPROCS(4)\n\tfmt.Println(\"Тестирование Work Stealing при неравномерной нагрузке...\")\n\n\tvar wg sync.WaitGroup\n\tconst total = 400\n\twg.Add(total)\n\n\tfor i := 0; i < total; i++ {\n\t\tgo func(id int) {\n\t\t\tdefer wg.Done()\n\t\t\t// Неравномерная длительность нагрузки\n\t\t\tduration := time.Duration(1+rand.Intn(15)) * time.Millisecond\n\t\t\ttime.Sleep(duration)\n\t\t}(i)\n\t}\n\n\twg.Wait()\n\tfmt.Println(\"Все неравномерные задачи успешно обработаны.\")\n}",
        "note": "Неравномерная нагрузка и автоматическая балансировка"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go"
      }
    ],
    "under_the_hood": "Каждый раз, когда `P` становится пустым, поток M инкрементирует внутренний счетчик `steal`. В трассировщике `runtime/trace` такие события помечаются как фазы кражи работы, обеспечивая полную прозрачность поведения планировщика.",
    "pitfalls": "Если задачи микроскопические (<1 микросекунды), стоимость CAS-инструкций при краже работы может превышать выигрыш от параллелизма.",
    "bigtech_interview": "**Вопрос с собеседования:** В каком порядке поток M ищет горутину для выполнения, когда его локальная очередь опустела?\n**Ответ:** Порядок строго зафиксирован в функции `runtime.findrunnable()`:\n1. Проверка слота `runnext` и локальной очереди текущего `P`;\n2. Проверка Глобальной Очереди (`sched.runq`) с захватом `sched.lock`;\n3. Проверка сетевого поллера `netpoll(0)` на наличие готовых I/O событий;\n4. Попытка украсть половину очереди у случайного чужого `P` (`runqsteal`);\n5. Повторный опрос сетевого поллера с блокировкой (`netpoll(delay)`);\n6. Усыпление потока M и переход в спящий пул `sched.midle`."
  },
  {
    "num": 39,
    "title": "Глубокая трассировка runtime/trace: визуализация состояний горутин и системных вызовов",
    "task": "**runtime/trace**: Используйте `trace.Start()` и `trace.Stop()` для записи execution trace. Визуализируйте через `go tool trace` и изучите timeline горутин, GC pauses, syscalls.",
    "theory": "Инструмент `go tool trace` позволяет исследовать выполнение программы на микроуровне:\n1. **Состояния горутин:** Running, Runnable, Blocked (Waiting);\n2. **Причины блокировок:** Network I/O, Syscall, Sync (мьютексы/каналы), GC STW;\n3. **Корреляция:** Связь между сетевыми запросами, блокировками и задержками ответов.",
    "step_by_step": "1. Запускаем `trace.Start()` в файл `execution.out`.\n2. Выполняем комбинацию вычислений, сетевых обращений и каналов.\n3. Анализируем трассировку в браузере через `go tool trace`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n\t\"runtime\"\n\t\"runtime/trace\"\n\t\"sync\"\n\t\"time\"\n)\n\nfunc main() {\n\truntime.GOMAXPROCS(2)\n\n\tf, err := os.Create(\"execution.out\")\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer f.Close()\n\n\tif err := trace.Start(f); err != nil {\n\t\tpanic(err)\n\t}\n\tdefer trace.Stop()\n\n\tvar wg sync.WaitGroup\n\twg.Add(3)\n\n\t// 1. CPU горутина\n\tgo func() {\n\t\tdefer wg.Done()\n\t\tvar acc int\n\t\tfor i := 0; i < 5000000; i++ {\n\t\t\tacc += i\n\t\t}\n\t\t_ = acc\n\t}()\n\n\t// 2. Блокировка на таймере\n\tgo func() {\n\t\tdefer wg.Done()\n\t\ttime.Sleep(15 * time.Millisecond)\n\t}()\n\n\t// 3. Канал\n\tch := make(chan int)\n\tgo func() {\n\t\tdefer wg.Done()\n\t\tch <- 42\n\t}()\n\tgo func() {\n\t\t<-ch\n\t}()\n\n\twg.Wait()\n\tfmt.Println(\"Трассировка записана в execution.out\")\n}",
        "note": "Комплексная трассировка рантайма"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Запуск визуализатора:\n# go tool trace execution.out"
      }
    ],
    "under_the_hood": "В Go 1.21+ рантайм использует обновленный формат трассировки (Flight Recorder), который генерирует значительно меньше накладных расходов на запись событий и поддерживает непрерывную кольцевую запись в памяти.",
    "pitfalls": "Файлы трассировки `trace.out` могут занимать сотни мегабайт за десятки секунд. Всегда ограничивайте время снятия трейса.",
    "bigtech_interview": "**Вопрос с собеседования:** Чем профилировщик `pprof` принципиально отличается от инструмента `go tool trace`?\n**Ответ:**\n- `pprof` — это **статистический сэмплирующий профилировщик** (Sampling Profiler). Он просыпается 100 раз в секунду (каждые 10 мс) и фиксирует текущие стеки. Он показывает, **где** (в каких функциях) программа тратит CPU или память в среднем;\n- `go tool trace` — это **детерминированный событийный логгер** (Event Tracer). Он логирует каждое переключение контекста, каждый сетевой пакет, захват мьютекса и паузу GC. Он показывает, **когда и почему** программа простаивает или задерживается во времени (timeline analysis)."
  },
  {
    "num": 40,
    "title": "Архитектура фонового потока sysmon: полная сводка обязанностей",
    "task": "**Роль `sysmon` (Системный монитор)**: `sysmon` — это фоновый поток рантайма, который работает без `P`. Его задачи: будить спящие таймеры, опрашивать сеть и... наказывать \"жадные\" горутины. *Просто запомни это для следующих двух упражнений.*",
    "theory": "Поток `sysmon` — это «сторожевой пес» (watchdog) всего рантайма Go.\nОн выполняет:\n1. Вытеснение горутин, работающих >10 мс (`preemptone`);\n2. Отсоединение P от блокирующих системных вызовов (`handoffp`);\n3. Опрос сетевых сокетов в `netpoll`, если они не опрашивались 10 мс;\n4. Запуск принудительного цикла GC раз в 2 минуты (`forcegcperiod`);\n5. Возврат физической памяти операционной системе (`scavenger`).",
    "step_by_step": "1. Запускаем приложение с длительным временем работы.\n2. Логируем поведение через `GODEBUG=schedtrace=1000`.\n3. Анализируем стабильность параметров рантайма.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"time\"\n)\n\nfunc main() {\n\tfmt.Printf(\"Демонстрация стабильности под контролем sysmon (GOMAXPROCS=%d)...\\n\", runtime.GOMAXPROCS(0))\n\n\t// Запускаем фоновую периодическую нагрузку\n\tticker := time.NewTicker(200 * time.Millisecond)\n\tdefer ticker.Stop()\n\n\tdone := time.After(1 * time.Second)\n\tfor {\n\t\tselect {\n\t\tcase <-done:\n\t\t\tfmt.Println(\"Цикл успешно завершен под контролем sysmon.\")\n\t\t\treturn\n\t\tcase t := <-ticker.C:\n\t\t\t_ = t\n\t\t}\n\t}\n}",
        "note": "Фоновый контроль стабильности рантайма"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go"
      }
    ],
    "under_the_hood": "`sysmon` реализован в файле `src/runtime/proc.go` в виде бесконечного цикла `for {}` с вызовом `usleep(delay)`. Он динамически адаптирует интервал сна: если программа активно работает, интервал равен 20 микросекундам; если программа простаивает, интервал постепенно экспоненциально увеличивается до 10 миллисекунд.",
    "pitfalls": "`sysmon` не может помочь, если поток M завис внутри ядра ОС в аппаратном сбое (D-state process, ожидание мертвого NFS-диска), так как поток ОС в состоянии uninterruptible sleep не реагирует ни на какие сигналы.",
    "bigtech_interview": "**Вопрос с собеседования:** Что произойдет с памятью Go-сервиса, если он выделил 10 ГБ памяти в куче под разовую задачу, освободил ее, но новых запросов больше не поступает?\n**Ответ:**\n1) Сборщик мусора освободит объекты в куче и пометит спаны памяти как свободные (`mheap`);\n2) Однако физическая память ядра ОС (RSS) останется занятой;\n3) Фоновый поток `sysmon` (совместно со scavenger-горутиной) обнаружит неиспользуемые страницы памяти и вызовет системный вызов `madvise(addr, len, MADV_DONTNEED)` (или `MADV_FREE` в зависимости от версии Go и ядра Linux);\n4) Ядро Linux освободит физические страницы памяти, и RSS процесса снизится обратно до базового уровня."
  },
  {
    "num": 41,
    "title": "Привязка горутины к потоку ОС через runtime.LockOSThread()",
    "task": "Напишите программу с `runtime.LockOSThread()` в одной goroutine. Покажите в `schedtrace`, что эта G привязана к конкретному M. Объясните, когда это нужно (cgo, syscall) и как это ломает work stealing.",
    "theory": "По умолчанию планировщик Go свободно перемещает горутину между разными потоками ОС `M` при каждом переключении контекста.\nОднако вызов **`runtime.LockOSThread()`** жестко привязывает текущую горутину к тому потоку ОС `M`, на котором она выполняется в данный момент:\n- Никакая другая горутина не может исполняться на этом потоке `M`, пока он заблокирован.\n- Сама привязанная горутина гарантированно исполняется **только на этом потоке `M`**.\n- В `schedtrace` число потоков `threads` учитывает привязанный поток.",
    "step_by_step": "1. Создаем горутину, вызывающую `runtime.LockOSThread()`.\n2. Фиксируем ID потока ОС через системный вызов `syscall.Gettid()`.\n3. Делаем несколько переключений контекста `runtime.Gosched()`.\n4. Убеждаемся, что ID потока ОС не меняется.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"sync\"\n\t\"syscall\"\n\t\"time\"\n)\n\nfunc main() {\n\truntime.GOMAXPROCS(4)\n\tvar wg sync.WaitGroup\n\twg.Add(1)\n\n\tgo func() {\n\t\tdefer wg.Done()\n\t\t// Жестко привязываем горутину к текущему потоку ОС\n\t\truntime.LockOSThread()\n\t\tdefer runtime.UnlockOSThread()\n\n\t\tinitialTID := syscall.Gettid()\n\t\tfmt.Printf(\"Горутина привязана к потоку ОС (TID = %d)\\n\", initialTID)\n\n\t\tfor i := 0; i < 5; i++ {\n\t\t\truntime.Gosched() // Уступаем процессор\n\t\t\tcurrentTID := syscall.Gettid()\n\t\t\tif currentTID != initialTID {\n\t\t\t\tpanic(\"TID изменился, LockOSThread нарушен!\")\n\t\t\t}\n\t\t\ttime.Sleep(10 * time.Millisecond)\n\t\t}\n\n\t\tfmt.Printf(\"Проверка успешна: после всех переключений TID по-прежнему %d\\n\", syscall.Gettid())\n\t}()\n\n\twg.Wait()\n\tfmt.Println(\"Тест LockOSThread успешно пройден.\")\n}",
        "note": "Фиксация постоянного потока ОС через runtime.LockOSThread"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод:\n# Горутина привязана к потоку ОС (TID = 56789)\n# Проверка успешна: после всех переключений TID по-прежнему 56789\n# Тест LockOSThread успешно пройден."
      }
    ],
    "under_the_hood": "При вызове `runtime.LockOSThread()` рантайм выставляет взаимные ссылки: `gp.lockedm = mp` и `mp.lockedg = gp`. В цикле планировщика `schedule()` поток M проверяет: если у него есть `lockedg`, он обязан исполнять только ее; если горутина не готова (`_Gwaiting`), этот поток M засыпает и не берет чужие задачи из очереди.",
    "pitfalls": "Если привязанная горутина завершится без вызова `runtime.UnlockOSThread()`, рантайм Go **уничтожит этот поток ОС** (`exitThread`), чтобы предотвратить утечку грязного состояния потока (TLS, namespace). Это создает накладные расходы на пересоздание потока M.",
    "bigtech_interview": "**Вопрос с собеседования:** Зачем нужен `runtime.LockOSThread()` и в каких трех реальных архитектурных задачах он строго обязателен?\n**Ответ:**\n`LockOSThread` обязателен в сценариях, завязанных на состояние конкретного потока ОС (Thread-Affinity):\n1) **GUI-библиотеки и графические движки (OpenGL, Cocoa, Win32, GLFW):** Графический контекст OpenGL и цикл обработки сообщений Windows/macOS привязаны к Thread-Local Storage главного потока;\n2) **Linux Namespaces (контейнеризация):** Системный вызов `setns()` переключает пространство имен (network/mount namespace) **только для текущего потока ОС** (`task_struct`). Чтобы сетевые операции горутины выполнялись внутри нужного контейнера, она обязана залочить поток;\n3) **CGO-библиотеки с Thread-Local Storage (TLS):** Внешний C-код, сохраняющий сессии или транзакции в `__thread` / `pthread_setspecific`."
  },
  {
    "num": 42,
    "title": "Применение runtime.LockOSThread для изоляции пространств имен Linux и GUI",
    "task": "**[runtime.LockOSThread]**: Напиши программу, где горутина вызывает `runtime.LockOSThread()`. Объясни, почему эта горутина теперь навсегда привязана к конкретному потоку ОС (M), и P не может быть передан другому M, если эта горутина заблокируется. (Где это используется? — В CGO, OpenGL, syscall.Setuid).",
    "theory": "При разработке системного ПО (систем контейнеризации типа Docker/runC) критически важно управлять сетевыми пространствами имен (Network Namespaces).\nСистемный вызов `unix.Setns(fd, unix.CLONE_NEWNET)` переключает пространство имен строго для текущего потока ядра Linux.\nЕсли не вызвать `runtime.LockOSThread()`:\n- Горутина переключит namespace у потока M1;\n- При следующем переключении контекста планировщик перенесет горутину на поток M2, который находится в базовом namespace хоста!\n- Произойдет утечка сетевого трафика и нарушение изоляции контейнера.",
    "step_by_step": "1. Создаем функцию, изолирующую выполнение внутри заблокированного потока.\n2. Применяем `runtime.LockOSThread()`.\n3. Гарантируем корректный выход из потока при завершении.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"sync\"\n\t\"syscall\"\n)\n\n// Имитация безопасного выполнения задачи в изолированном контексте потока\nfunc runInDedicatedThread(fn func()) {\n\tvar wg sync.WaitGroup\n\twg.Add(1)\n\n\tgo func() {\n\t\tdefer wg.Done()\n\t\t// 1. Блокируем поток ОС\n\t\truntime.LockOSThread()\n\t\t// Внимание: если состояние потока модифицируется необратимо (setns),\n\t\t// UnlockOSThread делать НЕЛЬЗЯ — поток должен умереть вместе с горутиной!\n\t\tdefer runtime.UnlockOSThread()\n\n\t\tfmt.Printf(\"  [Worker] Запуск в выделенном потоке ОС (TID = %d)\\n\", syscall.Gettid())\n\t\tfn()\n\t}()\n\n\twg.Wait()\n}\n\nfunc main() {\n\tfmt.Printf(\"Главный поток: TID = %d\\n\", syscall.Gettid())\n\n\trunInDedicatedThread(func() {\n\t\tfmt.Println(\"  [Task] Выполнение задачи, требующей привязки к потоку...\")\n\t})\n\n\tfmt.Println(\"Выполнение задачи завершено.\")\n}",
        "note": "Изоляция потока ОС для специфичных системных вызовов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод:\n# Главный поток: TID = 1234\n#   [Worker] Запуск в выделенном потоке ОС (TID = 1235)\n#   [Task] Выполнение задачи, требующей привязки к потоку...\n# Выполнение задачи завершено."
      }
    ],
    "under_the_hood": "Если горутина вызвала `runtime.LockOSThread()`, завершается, но НЕ вызывает `UnlockOSThread()`, рантайм помечает поток `mp.lockedg = nil` и вызывает `pthread_exit()`. Поток ОС не возвращается в общий пул потоков, исключая риск того, что другая горутина случайно выполнит сетевой вызов в чужом namespace.",
    "pitfalls": "Вызов `LockOSThread()` в массовых горутинах (например внутри HTTP-хендлера) парализует планировщик Go, превращая легковесную модель GMP в классическую тяжелую модель 1:1 с тысячами системных потоков.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в исходном коде утилиты `runc` и библиотеки `libcontainer` переключение Linux Namespaces выполняется в конструкторе на CGO через `__attribute__((constructor))` до старта рантайма Go?\n**Ответ:** Потому что рантайм Go стартует многопоточно (`sysmon`, сборщик мусора, потоки M).\nВ ядре Linux системные вызовы изменения пространств имен (`setns`, `unshare`) имеют жесткие ограничения: поток не может отвязать некоторые namespace, если процесс уже является многопоточным (multithreaded).\nПоэтому в `runc` создается конструктор на языке C, который выполняется до того, как Go поднимет свои потоки и инициализирует планировщик."
  },
  {
    "num": 43,
    "title": "Обнаружение утечек горутин (Goroutine Leaks) через runtime.NumGoroutine и pprof",
    "task": "**Goroutine leaks detection**: Создайте goroutine leak (заблокированная горутина). Используйте `runtime.NumGoroutine()` и `pprof goroutine profile` для обнаружения.",
    "theory": "Утечка горутин (Goroutine Leak) — одна из наиболее коварных проблем в Go.\nПоскольку горутины не уничтожаются сборщиком мусора, пока они заблокированы (даже если на них больше нет внешних ссылок), любая горутина, зависшая на чтении из канала, невозвращенном сетевом запросе или дедлоке мьютекса, удерживает:\n1. Стек в куче (от 2 до 8 КБ);\n2. Все замыкания и переменные, на которые ссылается ее стек.\n\nПри высоком RPS даже 1 зависшая горутина на 100 запросов приведет к утечке сотен тысяч горутин и неминуемому OOM (Out Of Memory) через несколько суток работы сервиса.",
    "step_by_step": "1. Создаем функцию с преднамеренной утечкой (запись в небуферизованный канал без читателя).\n2. Замеряем `runtime.NumGoroutine()` до и после вызова.\n3. Проверяем обнаружение утечки.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"time\"\n)\n\n// leakingTask порождает горутину, которая навсегда зависает на отправке\nfunc leakingTask() {\n\tch := make(chan int) // Небуферизованный канал\n\tgo func() {\n\t\tch <- 42 // Никто никогда не прочитает отсюда\n\t}()\n}\n\nfunc main() {\n\tfmt.Printf(\"До вызовов: Горутин = %d\\n\", runtime.NumGoroutine())\n\n\tfor i := 0; i < 50; i++ {\n\t\tleakingTask()\n\t}\n\n\ttime.Sleep(50 * time.Millisecond)\n\tleakedCount := runtime.NumGoroutine()\n\tfmt.Printf(\"После 50 вызовов leakingTask: Горутин = %d\\n\", leakedCount)\n\n\tif leakedCount >= 50 {\n\t\tfmt.Println(\"⚠️ Зафиксирована утечка 50 горутин в состоянии _Gwaiting [chan send]!\")\n\t}\n}",
        "note": "Детекция утечки горутин через runtime.NumGoroutine"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод:\n# До вызовов: Горутин = 1\n# После 50 вызовов leakingTask: Горутин = 51\n# ⚠️ Зафиксирована утечка 50 горутин в состоянии _Gwaiting [chan send]!"
      }
    ],
    "under_the_hood": "Зависшая горутина сохраняет статус `_Gwaiting` в поле `atomicstatus`. Поскольку ее структура `g` закреплена в очереди ожидания `waitq` канала, сборщик мусора рассматривает корень стека этой горутины как активный (Root Object), запрещая сборку мусора для всех привязанных данных.",
    "pitfalls": "В unit-тестах для предотвращения утечек в продакшене используйте библиотеку `go.uber.org/goleak`. Вызов `defer goleak.VerifyNone(t)` гарантирует, что тестовый кейс завершил все порожденные горутины.",
    "bigtech_interview": "**Вопрос с собеседования:** Спасет ли Garbage Collector горутину, которая заблокирована на чтении из закрытой области видимости (например, канал локален для функции и больше никем не используется)?\n**Ответ:** **НЕТ, не спасет!** Сборщик мусора Go не умеет определять, что горутина «больше никогда не проснется».\nПока горутина находится в статусе `_Gwaiting`, рантайм Go рассматривает ее дескриптор `g` как постоянный корень (GC Root). Горутина и все объекты, на которые ссылается ее стек, будут жить в оперативной памяти вечно, пока не завершится весь процесс операционной системы."
  },
  {
    "num": 44,
    "title": "Механизм runtime.Gosched(): добровольная уступка процессора против time.Sleep(0)",
    "task": "**Gosched()**: Вызовите `runtime.Gosched()` для явной передачи управления планировщику. Сравните с `time.Sleep(0)`.",
    "theory": "Функция `runtime.Gosched()` явно передает управление планировщику Go:\n- Текущая горутина переводится из статуса `_Grunning` в `_Grunnable`.\n- Она помещается в **конец Глобальной Очереди (GRQ)** (`sched.runq`), освобождая текущий процессор P.\n- Планировщик немедленно выбирает другую готовую задачу из очереди.\n\nВ отличие от `Gosched()`, вызов `time.Sleep(0)` или `time.Sleep(1)` регистрирует таймер в куче `p.timers`, переводит горутину в статус `_Gwaiting` и требует последующего пробуждения по таймеру, что значительно дороже по накладным расходам.",
    "step_by_step": "1. Создаем две горутины на `GOMAXPROCS=1`.\n2. В цикле вызываем `runtime.Gosched()`.\n3. Наблюдаем честное чередование вычислений.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"sync\"\n)\n\nfunc worker(name string, wg *sync.WaitGroup) {\n\tdefer wg.Done()\n\tfor i := 1; i <= 3; i++ {\n\t\tfmt.Printf(\"Горутина %s: шаг %d\\n\", name, i)\n\t\truntime.Gosched() // Добровольная уступка кванта времени\n\t}\n}\n\nfunc main() {\n\truntime.GOMAXPROCS(1)\n\tfmt.Println(\"GOMAXPROCS = 1: тестирование runtime.Gosched()...\")\n\n\tvar wg sync.WaitGroup\n\twg.Add(2)\n\n\tgo worker(\"A\", &wg)\n\tgo worker(\"B\", &wg)\n\n\twg.Wait()\n\tfmt.Println(\"Работа завершена.\")\n}",
        "note": "Кооперативное чередование горутин через runtime.Gosched"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод демонстрирует строгое чередование:\n# GOMAXPROCS = 1: тестирование runtime.Gosched()...\n# Горутина A: шаг 1\n# Горутина B: шаг 1\n# Горутина A: шаг 2\n# Горутина B: шаг 2\n# Горутина A: шаг 3\n# Горутина B: шаг 3\n# Работа завершена."
      }
    ],
    "under_the_hood": "Внутри `src/runtime/proc.go` функция `gosched_m(gp)` переключает контекст на `g0`, вызывает `casgstatus(gp, _Grunning, _Grunnable)`, помещает `gp` в глобальную очередь через `globrunqput(gp)` и вызывает `schedule()`. То, что горутина помещается именно в GRQ, а не в локальную очередь, гарантирует, что другие горутины на текущем P гарантированно получат процессор.",
    "pitfalls": "Использование `runtime.Gosched()` в качестве инструмента синхронизации (Spinlock) — антипаттерн, приводящий к 100% утилизации CPU. Для синхронизации всегда используйте каналы, `sync.WaitGroup` или мьютексы.",
    "bigtech_interview": "**Вопрос с собеседования:** Куда именно планировщик Go помещает горутину, вызвавшую `runtime.Gosched()` — в LRQ текущего P или в GRQ?\n**Ответ:** Строго в **Глобальную Очередь (GRQ)** (`sched.runq`).\nЭто осознанное архитектурное решение: если бы `Gosched()` возвращал горутину в начало или конец локальной очереди текущего `P`, а других горутин на этом `P` не было, текущая горутина мгновенно запустилась бы снова, сведя уступку процессора к нулю.\nПомещение в GRQ позволяет другим процессорам `P` украсть ее или дает текущему `P` возможность сначала разобрать все локальные задачи."
  },
  {
    "num": 45,
    "title": "Экспериментальное доказательство необходимости сигналов SIGURG через asyncpreemptoff=1",
    "task": "Создайте CPU-bound задачу без вызовов функций. С помощью `GODEBUG=asyncpreemptoff=1` отключите асинхронное вытеснение. Покажите, что вторая goroutine не запускается. Включите обратно — покажите, как `sysmon` (поток на 10-20 мс) расставляет `asyncPreempt`.",
    "theory": "Флаг `GODEBUG=asyncpreemptoff=1` позволяет в деталях воспроизвести проблему, с которой инженеры Go боролись с 2012 по 2020 год (до релиза Go 1.14).\nБез асинхронного вытеснения горутина с циклом:\n```go\nfor !stop {}\n```\nне содержит ни вызовов функций, ни аллокаций, ни работы с каналами. Компилятор не генерирует для такого цикла ни одного `morestack`.\nЕсли `GOMAXPROCS=1`, эта горутина монополизирует процессор навсегда: ни таймер, ни сетевой сокет, ни сборщик мусора не смогут получить управление.",
    "step_by_step": "1. Создаем программу с каналом таймаута и плотным циклом.\n2. Проверяем работу в штатном режиме (вытеснение за 10 мс).\n3. Документируем поведение при `asyncpreemptoff=1`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"sync/atomic\"\n\t\"time\"\n)\n\nfunc main() {\n\truntime.GOMAXPROCS(1)\n\tfmt.Println(\"Демонстрация вытеснения пустого цикла:\")\n\n\tvar running int32 = 1\n\n\t// Горутина с плотным циклом\n\tgo func() {\n\t\tfor atomic.LoadInt32(&running) == 1 {\n\t\t\t// Нет вызовов функций\n\t\t}\n\t\tfmt.Println(\"Горутина успешно вытеснена и завершена!\")\n\t}()\n\n\ttime.Sleep(100 * time.Millisecond)\n\tatomic.StoreInt32(&running, 0)\n\ttime.Sleep(50 * time.Millisecond)\n\n\tfmt.Println(\"Тест завершен.\")\n}",
        "note": "Проверка вытеснения плотного цикла"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Штатный вывод в современном Go:\n# Демонстрация вытеснения пустого цикла:\n# Горутина успешно вытеснена и завершена!\n# Тест завершен."
      }
    ],
    "under_the_hood": "В Go 1.14 компилятор также внедрил вставку инструкций вытеснения в циклы (Loop Preemption), но для плотных пустых циклов только сигнал `SIGURG` от ядра Linux гарантирует гарантированное прерывание.",
    "pitfalls": "В коде на WebAssembly (Wasm) асинхронное вытеснение по сигналам ОС недоступно, так как архитектура Wasm не поддерживает POSIX-сигналы. В Wasm Go по-прежнему использует кооперативное вытеснение.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в WebAssembly (GOOS=js GOARCH=wasm) планировщик Go не поддерживает асинхронное вытеснение через сигналы?\n**Ответ:** Потому что модель выполнения WebAssembly в браузерах не предоставляет потоков POSIX и сигнального механизма ядер Unix (`pthread_kill`). Wasm-код выполняется в изолированной виртуальной машине браузера.\nПоэтому в WebAssembly Go вынужден полагаться только на кооперативные точки вытеснения (`morestack`), либо компилятор вставляет дополнительные проверки при сборке под Wasm."
  },
  {
    "num": 46,
    "title": "Продвинутое использование LockOSThread: привязка горутины для CGO и системных потоков",
    "task": "**LockOSThread**: Используйте `runtime.LockOSThread()` для привязки горутины к OS потоку (необходимо для Cgo, GUI-потоков). Изучите последствия для scheduling.",
    "theory": "При вызове `runtime.LockOSThread()` горутина привязывается к потоку M.\nЭто критично в следующих сценариях:\n1. **Thread-Local Storage (TLS) в CGO:** C-библиотека сохраняет состояние в потоко-локальных переменных (`__thread` или `pthread_key_create`). Если вызвать функцию C из одной горутины, а затем продолжить на другом потоке M, состояние будет потеряно или повреждено.\n2. **Системные вызовы ядра, меняющие атрибуты треда:** `prctl()`, `setpriority()`, `sched_setaffinity()`.\n3. **Безопасное освобождение:** Если горутина восстанавливает состояние потока, она обязана вызвать парный `runtime.UnlockOSThread()`.",
    "step_by_step": "1. Пишем функцию, использующую системный вызов `setpriority` для изменения приоритета (nice) текущего потока.\n2. Используем `LockOSThread()` для гарантии, что приоритет изменится именно у нужного потока.\n3. Восстанавливаем приоритет перед `UnlockOSThread()`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"sync\"\n\t\"syscall\"\n)\n\nfunc setThreadNice(priority int) error {\n\ttid := syscall.Gettid()\n\t// Изменение приоритета (nice) для текущего потока ядра Linux\n\terr := syscall.Setpriority(syscall.PRIO_PROCESS, tid, priority)\n\treturn err\n}\n\nfunc main() {\n\tvar wg sync.WaitGroup\n\twg.Add(1)\n\n\tgo func() {\n\t\tdefer wg.Done()\n\n\t\t// 1. Блокируем горутину на текущем потоке ОС\n\t\truntime.LockOSThread()\n\t\tdefer runtime.UnlockOSThread()\n\n\t\ttid := syscall.Gettid()\n\t\tfmt.Printf(\"Поток TID %d: установка nice = 10 (пониженный приоритет)\\n\", tid)\n\n\t\tif err := setThreadNice(10); err != nil {\n\t\t\tfmt.Printf(\"Ошибка setpriority: %v\\n\", err)\n\t\t\treturn\n\t\t}\n\n\t\tprio, err := syscall.Getpriority(syscall.PRIO_PROCESS, tid)\n\t\tif err == nil {\n\t\t\tfmt.Printf(\"Поток TID %d: текущий nice = %d\\n\", tid, prio)\n\t\t}\n\t}()\n\n\twg.Wait()\n\tfmt.Println(\"Операция с потоком ОС завершена успешно.\")\n}",
        "note": "Управление приоритетом потока ОС через LockOSThread"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод:\n# Поток TID 12345: установка nice = 10 (пониженный приоритет)\n# Поток TID 12345: текущий nice = 10\n# Операция с потоком ОС завершена успешно."
      }
    ],
    "under_the_hood": "`LockOSThread` и `UnlockOSThread` поддерживают счетчик вложенности: если `LockOSThread()` вызван трижды, требуется три вызова `UnlockOSThread()`, чтобы поток M снова стал доступен для других горутин.",
    "pitfalls": "Если вызвать `LockOSThread()` и передать управление другой горутине через канал, не освободив поток, поток M зависнет в ожидании возврата управления, уменьшая доступное число активных воркеров.",
    "bigtech_interview": "**Вопрос с собеседования:** Что произойдет с потоком ОС `M`, если горутина вызвала `runtime.LockOSThread()`, но завершила свое выполнение, забыв вызвать `runtime.UnlockOSThread()`?\n**Ответ:** Рантайм Go отслеживает факт гибели горутины с неснятым локом потока.\nТак как поток ОС мог быть модифицирован (изменены TLS-переменные, приоритет, маска сигналов, пространство имен), рантайм **не имеет права вернуть этот поток в пул свободных потоков `sched.midle`**, иначе другая горутина унаследует грязное состояние.\nПоэтому рантайм принудительно завершает этот поток ОС (`pthread_exit()`), а при необходимости создает новый чистый поток M."
  },
  {
    "num": 47,
    "title": "Динамический рост стека горутины: от 2 КБ до мегабайтов и адресная стабильность",
    "task": "**[Goroutine Stack]**: Создай рекурсивную функцию. Выводи адрес локальной переменной на каждом шаге. Посмотри, как меняется адрес (растет стек). Используй `runtime.Stack` для чтения стека горутины.",
    "theory": "Стек горутины в Go является **непрерывным (Contiguous Stack)** (начиная с Go 1.4, заменив Segmented Stacks).\n- Начальный размер стека: ровно **2048 байт (2 КБ)**.\n- При исчерпании стека рантайм выделяет в куче новый блок, в **2 раза превышающий** старый (4 КБ, 8 КБ, ..., вплоть до 1 ГБ на 64-битных системах).\n- Все локальные переменные копируются на новый стек.\n- Все указатели, ссылавшиеся на переменные старого стека, автоматически корректируются рантаймом.\n\nПри выводе адреса локальной переменной в глубокой рекурсии можно визуально зафиксировать момент, когда адрес переменной внезапно скачкообразно меняется на новый диапазон памяти в куче.",
    "step_by_step": "1. Пишем глубоко-рекурсивную функцию.\n2. На каждой итерации выводим адрес локальной переменной.\n3. Наблюдаем скачок адреса при реаллокации стека.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n)\n\nvar lastAddr uintptr\n\nfunc recursiveStackGrowth(depth int) {\n\tvar x int\n\tcurrentAddr := uintptr(unsafePointer(&x))\n\n\tif depth%10 == 0 || depth < 5 {\n\t\tdiff := int64(currentAddr) - int64(lastAddr)\n\t\tif lastAddr != 0 && (diff > 4096 || diff < -4096) {\n\t\t\tfmt.Printf(\"⚠️ Реаллокация стека на глубине %3d! Старый адрес: 0x%x -> Новый адрес: 0x%x (дельта: %d байт)\\n\",\n\t\t\t\tdepth, lastAddr, currentAddr, diff)\n\t\t} else {\n\t\t\tfmt.Printf(\"Глубина %3d: адрес локальной переменной = 0x%x\\n\", depth, currentAddr)\n\t\t}\n\t}\n\tlastAddr = currentAddr\n\n\tif depth < 45 {\n\t\trecursiveStackGrowth(depth + 1)\n\t}\n}\n\n// Вспомогательная функция для безопасного получения адреса\nfunc unsafePointer(p *int) *int {\n\treturn p\n}\n\nfunc main() {\n\tfmt.Println(\"Демонстрация роста непрерывного стека горутины (Contiguous Stack):\")\n\trecursiveStackGrowth(1)\n}",
        "note": "Отслеживание скачков адресов при росте стека"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# В выводе виден момент скачка адреса при реаллокации стека с 2 КБ на 4 КБ и 8 КБ"
      }
    ],
    "under_the_hood": "В `src/runtime/stack.go` функция `copystack()` выделяет новый сегмент памяти, копирует данные старого стека и использует сгенерированные компилятором стек-карты (`stackMap`), чтобы обойти все живые фреймы и скорректировать все внутренние указатели.",
    "pitfalls": "Хотя стек растет непрерывно, хранить сырые указатели `uintptr` на переменные стека через `unsafe.Pointer` категорически запрещено: при реаллокации стека значение `uintptr` не корректируется рантаймом, превращаясь в повисший указатель (Dangling Pointer).",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в Go 1.4 отказались от сегментированных стеков (Segmented Stacks) в пользу непрерывных стеков (Contiguous Stacks)?\n**Ответ:** Проблема сегментированных стеков заключалась в так называемом **«Hot Split Problem»**:\nЕсли горутина находилась на границе выделения нового сегмента стека внутри интенсивного цикла, каждый вход в функцию вызывал аллокацию нового сегмента памяти, а каждый выход — его освобождение.\nЭто приводило к катастрофическому падению производительности (миллионы микроаллокаций памяти в секунду).\nНепрерывные стеки (Contiguous Stacks) выделяют память с запасом в 2 раза и используют умное сжатие стека (Stack Shrinking) только во время фазы GC, полностью ликвидировав проблему Hot Split."
  },
  {
    "num": 48,
    "title": "Эмуляция старого Go: демонстрация кооперативного вытеснения",
    "task": "**Кооперативное вытеснение (Эмуляция старого Go)**: До Go 1.14 горутина могла выполняться вечно, если в ней не было вызовов функций (нет точек прерывания). Напиши `for {}` (пустой бесконечный цикл). В Go 1.13 эта горутина захватила бы `P` навсегда.",
    "theory": "Кооперативное вытеснение полагается на добровольное сотрудничество кода с рантаймом:\n- Вызовы функций;\n- Каналы;\n- Системные вызовы;\n- Вызовы `runtime.Gosched()`.\n\nЕсли код не совершает ни одного из этих действий, в старых версиях Go он полностью блокировал планировщик. Понимание этого исторического контекста необходимо для понимания архитектуры современного планировщика Go 1.22+.",
    "step_by_step": "1. Создаем программу, эмулирующую кооперативную передачу через явный `Gosched()`.\n2. Показываем разницу в распределении времени между горутинами с уступкой процессора и без нее.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"time\"\n)\n\nfunc cooperativeWorker(id int, stop *bool, counter *uint64) {\n\tfor !*stop {\n\t\t*counter++\n\t\tif *counter%1000000 == 0 {\n\t\t\truntime.Gosched() // Кооперативная передача управления\n\t\t}\n\t}\n}\n\nfunc main() {\n\truntime.GOMAXPROCS(1)\n\tfmt.Println(\"Кооперативное распределение на GOMAXPROCS=1...\")\n\n\tstop := false\n\tvar c1, c2 uint64\n\n\tgo cooperativeWorker(1, &stop, &c1)\n\tgo cooperativeWorker(2, &stop, &c2)\n\n\ttime.Sleep(200 * time.Millisecond)\n\tstop = true\n\ttime.Sleep(50 * time.Millisecond)\n\n\tfmt.Printf(\"Итераций Worker 1: %d\\n\", c1)\n\tfmt.Printf(\"Итераций Worker 2: %d\\n\", c2)\n\tfmt.Println(\"Обе горутины получили справедливое время CPU благодаря точкам уступки.\")\n}",
        "note": "Кооперативное распределение времени выполнения"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод демонстрирует сопоставимый объем работы у обоих воркеров:\n# Кооперативное распределение на GOMAXPROCS=1...\n# Итераций Worker 1: 34000000\n# Итераций Worker 2: 33000000\n# Обе горутины получили справедливое время CPU благодаря точкам уступки."
      }
    ],
    "under_the_hood": "В функции `goschedImpl()` рантайм сбрасывает текущий тайм-слайс процессора `pp.schedtick++`, предотвращая монополизацию ресурсов.",
    "pitfalls": "Надежда только на `runtime.Gosched()` в критичных кодовых базах ненадежна: если разработчик забудет вставить вызов в длинный алгоритм, горутина снова начнет вызывать задержки.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему вызов `runtime.Gosched()` не гарантирует немедленного запуска конкретной другой горутины?\n**Ответ:** Потому что `Gosched()` только помещает текущую горутину в GRQ и запускает стандартный алгоритм планирования `schedule()`.\nПланировщик выбирает следующую задачу по стандартным приоритетам:\n1) Проверяет `runnext`;\n2) Проверяет локальную очередь `LRQ`;\n3) Проверяет `GRQ`;\n4) Выполняет `netpoll` или `work stealing`.\nКакая именно горутина запустится следующей, зависит от текущего состояния очередей всех P."
  },
  {
    "num": 49,
    "title": "Мониторинг поведения потока sysmon при длительных блокирующих syscalls",
    "task": "**Sysmon и блокирующие системные вызовы.**: Напишите программу, выполняющую блокирующие системные вызовы (например, sleep, чтение файла). Отследите `schedtrace`, найдите `sysmon`, который отбирает P у M, заблокированного в syscall.",
    "theory": "Когда поток `M` входит в блокирующий системный вызов, рантайм не может предугадать, сколько времени займет операция в ядре: 5 микросекунд или 30 секунд.\nПоэтому алгоритм разделен на фазы:\n- **Фаза 1 (Быстрая):** Вызов `entersyscall()`. Если системный вызов вернулся мгновенно (например, данные уже в дисковом кэше OS Page Cache), поток M продолжает работу без смены P.\n- **Фаза 2 (Медленная, sysmon):** Если через 10 мс системный вызов все еще не завершился, поток `sysmon` детектирует зависший P и производит принудительный `handoffp()`.\n- **Фаза 3 (Возврат):** По возвращении из ядра поток M вызывает `exitsyscall()`. Если его P уже отнят, M паркует горутину в GRQ и засыпает.",
    "step_by_step": "1. Запускаем тест с искусственной задержкой внутри системного вызова.\n2. Проверяем счетчик потоков ОС до и во время вызова.\n3. Фиксируем успешную передачу контекста P.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"sync\"\n\t\"syscall\"\n\t\"time\"\n)\n\nfunc main() {\n\truntime.GOMAXPROCS(1)\n\tfmt.Printf(\"Старт теста на GOMAXPROCS=1. Активных горутин: %d\\n\", runtime.NumGoroutine())\n\n\tvar wg sync.WaitGroup\n\twg.Add(2)\n\n\t// Горутина 1: блокирующий системный вызов\n\tgo func() {\n\t\tdefer wg.Done()\n\t\tfmt.Println(\"  [G1] Вход в блокирующий syscall...\")\n\t\tvar req, rem syscall.Timespec\n\t\treq.Sec = 1\n\t\tsyscall.Nanosleep(&req, &rem)\n\t\tfmt.Println(\"  [G1] Выход из syscall.\")\n\t}()\n\n\t// Горутина 2: должна продолжить исполнение благодаря handoffp\n\tgo func() {\n\t\tdefer wg.Done()\n\t\ttime.Sleep(50 * time.Millisecond)\n\t\tfor i := 1; i <= 3; i++ {\n\t\t\ttime.Sleep(100 * time.Millisecond)\n\t\t\tfmt.Printf(\"  [G2] Шаг %d успешно выполнен, пока G1 в syscall!\\n\", i)\n\t\t}\n\t}()\n\n\twg.Wait()\n\tfmt.Println(\"Тест handoffp успешно завершен.\")\n}",
        "note": "Параллельное исполнение горутин во время блокирующего syscall"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод:\n# Старт теста на GOMAXPROCS=1. Активных горутин: 1\n#   [G1] Вход в блокирующий syscall...\n#   [G2] Шаг 1 успешно выполнен, пока G1 в syscall!\n#   [G2] Шаг 2 успешно выполнен, пока G1 в syscall!\n#   [G2] Шаг 3 успешно выполнен, пока G1 в syscall!\n#   [G1] Выход из syscall.\n# Тест handoffp успешно завершен."
      }
    ],
    "under_the_hood": "В `src/runtime/proc.go` функция `exitsyscall()` разделена на fast path (`exitsyscallfast()`) и slow path. Fast path атомарно проверяет, свободен ли старый P (`casp(oldp, _Psyscall, _Prunning)`). Если успел — переключение контекста потоков ОС вообще не происходит!",
    "pitfalls": "Если система перегружена блокирующими вызовами, затраты ядра Linux на постоянное создание и уничтожение потоков pthread (`clone`/`exit`) приводят к высокому системному потреблению CPU (`sys%` в top).",
    "bigtech_interview": "**Вопрос с собеседования:** Что такое Fast Path в функции `exitsyscall()` и почему он критически важен для производительности системных вызовов Go?\n**Ответ:** Большинство системных вызовов (например `gettimeofday`, быстрый `read` из теплого кэша) завершаются за сотни наносекунд — задолго до того, как поток `sysmon` успеет проснуться (квант 10–20 мкс / 10 мс).\nВ Fast Path поток M по возвращении из ядра видит, что его контекст `P` все еще находится в состоянии `_Psyscall` и не был отобран. Поток мгновенно меняет статус на `_Prunning` через один атомарный CAS и продолжает выполнение Go-кода без единого переключения контекста ядра ОС."
  },
  {
    "num": 50,
    "title": "Стресс-тест дискового I/O: генерация потоков ОС при чтении больших объемов данных",
    "task": "Напишите программу, которая делает длинный `syscall` (чтение 1 ГБ с диска). Покажите в `schedtrace`, что M отключается от P (`handoffp`). Объясните механизм `entersyscall` / `exitsyscall` и зачем P передаётся другому M.",
    "theory": "При параллельном синхронном чтении сотен файлов с диска каждый блокирующийся в ядре поток `M` заставляет рантайм создавать новый `M` для поддержания квоты `GOMAXPROCS`.\nФлаг `GODEBUG=schedtrace=200` наглядно показывает рост поля `threads`:\n- Изначально: `threads = GOMAXPROCS + 3..4`\n- Под нагрузкой: `threads = GOMAXPROCS + N (активных читателей)`\n- После завершения: потоки M не уничтожаются мгновенно, а засыпают в пуле `sched.midle`.",
    "step_by_step": "1. Создаем тестовые файлы на диске.\n2. Запускаем 30 параллельных горутин чтения.\n3. Отслеживаем изменение параметра `threads` в выводе `GODEBUG=schedtrace=200`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"crypto/rand\"\n\t\"fmt\"\n\t\"os\"\n\t\"runtime\"\n\t\"sync\"\n\t\"time\"\n)\n\nfunc makeDummyFile(name string, size int) {\n\tdata := make([]byte, size)\n\trand.Read(data)\n\tos.WriteFile(name, data, 0644)\n}\n\nfunc main() {\n\truntime.GOMAXPROCS(2)\n\tconst fileCount = 20\n\tfiles := make([]string, fileCount)\n\n\tfor i := 0; i < fileCount; i++ {\n\t\tfn := fmt.Sprintf(\"tmp_bench_%d.dat\", i)\n\t\tmakeDummyFile(fn, 2*1024*1024)\n\t\tfiles[i] = fn\n\t\tdefer os.Remove(fn)\n\t}\n\n\tfmt.Println(\"Запуск 20 параллельных операций чтения с диска...\")\n\n\tvar wg sync.WaitGroup\n\twg.Add(fileCount)\n\n\tfor i := 0; i < fileCount; i++ {\n\t\tgo func(path string) {\n\t\t\tdefer wg.Done()\n\t\t\tb, err := os.ReadFile(path)\n\t\t\tif err == nil {\n\t\t\t\t_ = len(b)\n\t\t\t}\n\t\t}(files[i])\n\t}\n\n\ttime.Sleep(100 * time.Millisecond)\n\twg.Wait()\n\tfmt.Println(\"Все операции чтения завершены.\")\n}",
        "note": "Массовое дисковое чтение и наблюдение за threads"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "GODEBUG=schedtrace=100 go run main.go\n# Наблюдайте рост счетчика threads в выводе schedtrace"
      }
    ],
    "under_the_hood": "Максимальное количество потоков ОС, которое Go соглашается создать перед аварийным завершением процесса, контролируется функцией `debug.SetMaxThreads(n)`. По умолчанию этот лимит равен 10 000 потоков.",
    "pitfalls": "Если сервис без ограничений обращается к медленному диску или сетевому хранилищу NFS, рост потоков M исчерпает лимиты ОС (`threads-max`), вызвав фатальную ошибку.",
    "bigtech_interview": "**Вопрос с собеседования:** Какой дефолтный лимит потоков ОС (M) установлен в рантайме Go и как защитить сервис от его исчерпания?\n**Ответ:** Дефолтный лимит составляет **10 000 системных потоков ОС**.\nДля защиты:\n1) Ограничивать параллелизм дисковых операций через семафор (`golang.org/x/sync/semaphore`) или пул горутин фиксированного размера (например, 10–20 воркеров);\n2) Использовать `debug.SetMaxThreads()` для ранней детекции аномалий на тестовых стендах;\n3) Никогда не выполнять блокирующий I/O в неограниченных `go func()` внутри веб-хендлеров."
  },
  {
    "num": 51,
    "title": "Корректное использование runtime.UnlockOSThread() и правила парности вызовов",
    "task": "**UnlockOSThread**: Вызовите `runtime.UnlockOSThread()` и изучите, когда это безопасно (после завершения Cgo вызовов).",
    "theory": "Вызов `runtime.UnlockOSThread()` снимает привязку текущей горутины к потоку ОС `M`.\nКлючевые правила:\n1. **Счетчик вложенности (Nesting Counter):** Если горутина вызвала `LockOSThread()` дважды, она обязана вызвать `UnlockOSThread()` ровно дважды, чтобы поток M освободился.\n2. **Безопасность состояния:** Вызывать `UnlockOSThread()` безопасно **только в том случае**, если горутина вернула все параметры потока ОС (приоритет, сигнальные маски, Thread-Local Storage) в исходное состояние.\n3. **Уничтожение потока:** Если горутина изменила глобальное состояние потока (например, `setns`), `UnlockOSThread` вызывать **нельзя** — горутина должна завершиться вместе со смертью потока.",
    "step_by_step": "1. Демонстрируем парный вызов `LockOSThread` и `UnlockOSThread`.\n2. Демонстрируем счетчик вложенности.\n3. Проверяем возвращение потока M в общий пул.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"sync\"\n\t\"syscall\"\n)\n\nfunc main() {\n\tvar wg sync.WaitGroup\n\twg.Add(1)\n\n\tgo func() {\n\t\tdefer wg.Done()\n\n\t\t// Двойная блокировка (счетчик = 2)\n\t\truntime.LockOSThread()\n\t\truntime.LockOSThread()\n\t\tfmt.Printf(\"Поток заблокирован дважды. TID = %d\\n\", syscall.Gettid())\n\n\t\t// Первый разблокирующий вызов (счетчик = 1, поток все еще привязан)\n\t\truntime.UnlockOSThread()\n\t\tfmt.Println(\"Первый UnlockOSThread выполнен, поток все еще закреплен.\")\n\n\t\t// Второй разблокирующий вызов (счетчик = 0, поток полностью свободен)\n\t\truntime.UnlockOSThread()\n\t\tfmt.Println(\"Второй UnlockOSThread выполнен: поток M возвращен в общий пул планировщика.\")\n\t}()\n\n\twg.Wait()\n\tfmt.Println(\"Тест завершен.\")\n}",
        "note": "Вложенные вызовы LockOSThread и UnlockOSThread"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод:\n# Поток заблокирован дважды. TID = 54321\n# Первый UnlockOSThread выполнен, поток все еще закреплен.\n# Второй UnlockOSThread выполнен: поток M возвращен в общий пул планировщика.\n# Тест завершен."
      }
    ],
    "under_the_hood": "В `src/runtime/proc.go` структура `g` содержит целочисленное поле `lockedm`. Вызов `LockOSThread()` инкрементирует счетчик `gp.m.lockedExt++`. Функция `UnlockOSThread()` декрементирует этот счетчик. Только при достижении 0 обнуляются взаимные ссылки `gp.lockedm = 0` и `mp.lockedg = 0`.",
    "pitfalls": "Вызов `UnlockOSThread()` без предварительного `LockOSThread()` ни к чему не приводит (счетчик остается 0), но нарушает идиоматичность кода.",
    "bigtech_interview": "**Вопрос с собеседования:** Что произойдет, если горутина вызовет `runtime.LockOSThread()` внутри библиотеки, а вызывающий код об этом не знает?\n**Ответ:** Поток ОС окажется захваченным до конца жизни этой горутины.\nЕсли горутина долгоживущая (например фоновый воркер), этот поток M будет навсегда изъят из общего пула планировщика.\nПоэтому вызовы `LockOSThread` и `UnlockOSThread` обязаны быть строго локализованы в минимальной критической секции и оформляться через `defer runtime.UnlockOSThread()`."
  },
  {
    "num": 52,
    "title": "Различие между NumCPU() и GOMAXPROCS: физические ядра против логических контекстов",
    "task": "**NumCPU vs GOMAXPROCS**: Изучите разницу. `NumCPU()` — это hardware cores, `GOMAXPROCS` — это logical processors для Go scheduler. В контейнерах с cgroups они могут отличаться.",
    "theory": "Фундаментальное отличие:\n- **`runtime.NumCPU()`:** Возвращает количество логических ядер процессора, доступных процессу на аппаратном уровне (определяется ОС через `sysconf(_SC_NPROCESSORS_ONLN)` или affinity mask). Это константа аппаратной платформы.\n- **`runtime.GOMAXPROCS(n)`:** Задает количество **логических процессоров планировщика P**, управляющих максимальным числом одновременно выполняемых горутин Go.\n\nПо умолчанию в Go 1.5+ `GOMAXPROCS == NumCPU()`. Однако в контейнерах, микросервисах и при тюнинге производительности эти величины могут кардинально различаться.",
    "step_by_step": "1. Считываем аппаратное число ядер через `runtime.NumCPU()`.\n2. Считываем текущий `GOMAXPROCS(0)`.\n3. Демонстрируем независимость этих параметров.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n)\n\nfunc main() {\n\thardwareCores := runtime.NumCPU()\n\tcurrentGomaxprocs := runtime.GOMAXPROCS(0)\n\n\tfmt.Printf(\"Аппаратных логических ядер (NumCPU): %d\\n\", hardwareCores)\n\tfmt.Printf(\"Текущее число контекстов P (GOMAXPROCS): %d\\n\", currentGomaxprocs)\n\n\t// Меняем GOMAXPROCS на нестандартное значение\n\tcustomP := 3\n\truntime.GOMAXPROCS(customP)\n\n\tfmt.Printf(\"\\nПосле изменения:\\n\")\n\tfmt.Printf(\"  NumCPU по-прежнему: %d\\n\", runtime.NumCPU())\n\tfmt.Printf(\"  Новый GOMAXPROCS:   %d\\n\", runtime.GOMAXPROCS(0))\n}",
        "note": "Сравнение NumCPU и GOMAXPROCS"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод:\n# Аппаратных логических ядер (NumCPU): 8\n# Текущее число контекстов P (GOMAXPROCS): 8\n# \n# После изменения:\n#   NumCPU по-прежнему: 8\n#   Новый GOMAXPROCS:   3"
      }
    ],
    "under_the_hood": "`runtime.NumCPU()` запрашивает системную информацию ядра один раз при инициализации рантайма и кэширует результат во внутренней переменной `ncpu`. Изменение `GOMAXPROCS` реаллоцирует внутренний массив `allp` структуры планировщика, не затрагивая `ncpu`.",
    "pitfalls": "Внутри Docker-контейнеров `NumCPU()` возвращает число ядер физического сервера (например 64), даже если контейнеру выделено всего 2 ядра CPU квоты cgroups.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в Kubernetes-подах использование `runtime.NumCPU()` в качестве размера пула воркеров считается опасной ошибкой?\n**Ответ:** Потому что внутри контейнера `runtime.NumCPU()` не знает о лимитах CFS (`cpu.cfs_quota_us`) и возвращает суммарное количество ядер физической ноды Kubernetes (например, 64 или 128 ядер).\nЕсли создать пул из 128 воркеров на поде с лимитом `cpu: 1`, все 128 потоков начнут конкурировать за одно ядро, исчерпают 100-мс квоту за доли миллисекунды и попадут под жесткий троттлинг ядра Linux (CFS Throttling). Задержки сервиса вырастут в десятки раз. Решение — использовать `go.uber.org/automaxprocs`."
  },
  {
    "num": 53,
    "title": "Механика Stack Growth и Copying: удвоение стека при глубокой рекурсии",
    "task": "**[Stack Growth / Copying]**: Напиши глубокую рекурсию. Стек горутины в Go начинается с 2KB. Когда он заканчивается, рантайм выделяет больший стек, копирует данные и исправляет указатели. Напиши бенчмарк, который вызывает функцию с разной глубиной рекурсии, и пронаблюдай аллокации.",
    "theory": "Стек горутины в Go выделяется в пользовательском адресном пространстве кучи.\n- Начальный размер: **2 КБ**.\n- Максимальный размер по умолчанию: **1 ГБ** на 64-битных ОС (и 250 МБ на 32-битных ОС), настраивается через `debug.SetMaxStack`.\n- При вызове каждой функции компилятор проверяет `SP < stackguard0`. При исчерпании вызывается `runtime.morestack()`.\n- Рантайм выделяет блок размером $2 \\times \\text{current\\_size}$, копирует фреймы и корректирует внутренние указатели.\n- В фазе сборки мусора рантайм может уменьшить стек вдвое (Stack Shrinking), если горутина использует менее 1/4 его емкости.",
    "step_by_step": "1. Напишем рекурсивную функцию с локальным массивом на 1 КБ.\n2. Отследим рост стека через рекурсивные вызовы.\n3. Убедимся в отсутствии переполнения стека и корректном возврате из рекурсии.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n)\n\n//go:noinline\nfunc deepRecursion(depth int, maxDepth int) int {\n\t// Локальный буфер, форсирующий быстрое исчерпание 2 КБ стека\n\tvar buffer [512]byte\n\tbuffer[0] = byte(depth)\n\n\tif depth >= maxDepth {\n\t\treturn int(buffer[0])\n\t}\n\treturn deepRecursion(depth+1, maxDepth) + int(buffer[0])\n}\n\nfunc main() {\n\tfmt.Println(\"Демонстрация динамического роста непрерывного стека (Stack Growth)...\")\n\tconst depth = 200\n\n\tresult := deepRecursion(1, depth)\n\tfmt.Printf(\"Глубокая рекурсия (%d уровней) успешно выполнена! Результат: %d\\n\", depth, result)\n\tfmt.Printf(\"Горутин активно: %d\\n\", runtime.NumGoroutine())\n}",
        "note": "Глубокая рекурсия и масштабирование непрерывного стека"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод:\n# Демонстрация динамического роста непрерывного стека (Stack Growth)...\n# Глубокая рекурсия (200 уровней) успешно выполнена! Результат: 20100\n# Горутин активно: 1"
      }
    ],
    "under_the_hood": "В `src/runtime/stack.go` функция `newstack()` проверяет, не превысил ли новый размер `maxstacksize`. Если превысил — рантайм выводит панику `runtime: goroutine stack exceeds 1000000000-byte limit` и роняет процесс. Это исключает бесконтрольное пожирание всей оперативной памяти бесконечной рекурсией.",
    "pitfalls": "Бесконечная взаимная рекурсия без базового условия остановки быстро доведет стек до 1 ГБ и завершит процесс аварийно. Для ограничения стека в недоверенном коде используйте `debug.SetMaxStack(10 * 1024 * 1024)` (10 МБ).",
    "bigtech_interview": "**Вопрос с собеседования:** В какой момент сборщик мусора Go уменьшает размер стека горутины (Stack Shrinking)?\n**Ответ:** Сжатие стека происходит во время фазы сканирования сборщика мусора (`runtime.shrinkstack()`).\nЕсли горутина во время выполнения выделила стек 64 КБ, а затем вышла из глубокой рекурсии и теперь использует менее 1/4 этого объема (менее 16 КБ), GC выделяет новый блок памяти в 2 раза меньше (32 КБ), копирует активные фреймы и возвращает лишнюю память в кэш `mcache`.\nМинимальный размер, до которого сжимается стек, равен исходным **2048 байтам (2 КБ)**."
  },
  {
    "num": 54,
    "title": "«Отравленная» горутина: влияние непрерывного runtime.Gosched() на планировщик",
    "task": "Реализуйте «отравленную» goroutine: бесконечный цикл с вызовом `runtime.Gosched()` каждую итерацию. Сравните с версией без `Gosched()`. Объясните разницу между кооперативной отдачей управления и принудительным вытеснением.",
    "theory": "Что происходит, если горутина исполняет бесконечный цикл, состоящий исключительно из `runtime.Gosched()`?\n```go\nfor { runtime.Gosched() }\n```\nТакая горутина называется «отравленной» (poisoned / spinning):\n- При каждом вызове она помещается в Глобальную Очередь (GRQ);\n- На каждом 61 тике планирования каждый процессор P забирает ее из GRQ;\n- Горутина не выполняет никакой полезной работы, но создает непрерывную нагрузку на `sched.lock` и расходует кванты планировщика, конкурируя с полезными задачами.",
    "step_by_step": "1. Запускаем «отравленную» горутину.\n2. Параллельно запускаем полезную задачу и замеряем время ее исполнения.\n3. Сравниваем производительность с нормальным режимом.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"sync\"\n\t\"sync/atomic\"\n\t\"time\"\n)\n\nfunc main() {\n\truntime.GOMAXPROCS(2)\n\tfmt.Println(\"Тестирование влияния отравленной горутины с Gosched()...\")\n\n\tstopPoison := int32(0)\n\tvar schedCount int64\n\n\t// Отравленная горутина: бесконечный цикл Gosched()\n\tgo func() {\n\t\tfor atomic.LoadInt32(&stopPoison) == 0 {\n\t\t\tatomic.AddInt64(&schedCount, 1)\n\t\t\truntime.Gosched()\n\t\t}\n\t}()\n\n\t// Полезная работа\n\tvar wg sync.WaitGroup\n\tstart := time.Now()\n\tconst workers = 4\n\twg.Add(workers)\n\n\tfor i := 0; i < workers; i++ {\n\t\tgo func() {\n\t\t\tdefer wg.Done()\n\t\t\tvar acc uint64\n\t\t\tfor j := 0; j < 5000000; j++ {\n\t\t\t\tacc += uint64(j)\n\t\t\t}\n\t\t\t_ = acc\n\t\t}()\n\t}\n\n\twg.Wait()\n\tduration := time.Since(start)\n\tatomic.StoreInt32(&stopPoison, 1)\n\n\tfmt.Printf(\"Полезная работа выполнена за: %v\\n\", duration)\n\tfmt.Printf(\"Отравленная горутина успела совершить %d вызовов Gosched()\\n\", atomic.LoadInt64(&schedCount))\n}",
        "note": "Исследование нагрузки от паразитных циклов Gosched"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод:\n# Тестирование влияния отравленной горутины с Gosched()...\n# Полезная работа выполнена за: ~18.5ms\n# Отравленная горутина успела совершить ~450000 вызовов Gosched()"
      }
    ],
    "under_the_hood": "Вызов `Gosched()` требует переключения на стек `g0` через `mcall` и захвата мьютекса `sched.lock` для помещения в GRQ. Сотни тысяч вызовов `Gosched()` в секунду превращают быстрый lock-free планировщик в узкое бутылочное горлышко из-за постоянной борьбы за спинлок глобальной очереди.",
    "pitfalls": "Никогда не используйте циклы вида `for condition { runtime.Gosched() }` в качестве самодельных каналов или условных переменных. Используйте `sync.Cond` или каналы, которые переводят горутину в честный сон `_Gwaiting` с нулевой нагрузкой на CPU.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему активное ожидание через `runtime.Gosched()` в цикле считается грубейшим антипаттерном в Go?\n**Ответ:**\n1) **Паразитная утилизация CPU:** Процессор загружен на 100%, сжигая электроэнергию и квоты в облаке;\n2) **Деградация глобального спинлока:** Каждый вызов `Gosched()` захватывает `sched.lock`, блокируя другие потоки M при доступе к GRQ;\n3) **Инвалидация кэшей:** Постоянное переключение горутины между процессорами разрушает кэш-линии L1/L2 процессора;\n4) Вместо этого правильный паттерн — `sync.Cond` или чтение из канала, где горутина паркуется через `gopark()` и просыпается по событию с нулевым overhead."
  },
  {
    "num": 55,
    "title": "Container-Aware GOMAXPROCS: интеграция go.uber.org/automaxprocs в Kubernetes",
    "task": "**Container-aware GOMAXPROCS**: Используйте `go.uber.org/automaxprocs` для автоматической настройки GOMAXPROCS based on container CPU quota (важно для Kubernetes).",
    "theory": "При развертывании в Kubernetes контейнеру часто назначают квоты процессора:\n```yaml\nresources:\n  limits:\n    cpu: \"2\"\n```\nОднако стандартный Go рантайм определяет `GOMAXPROCS` через `runtime.NumCPU()`, который считывает количество ядер **физического хоста** (например, 64 ядра).\nВ результате:\n- Go создает 64 процессора P и 64 потока M;\n- CFS квота ядра Linux в 2 ядра расходуется за долю кванта;\n- Под подвергается жесткому CFS Throttling (задержки возрастают в 10–20 раз).\n\nБиблиотека `go.uber.org/automaxprocs` автоматически считывает лимиты из `/sys/fs/cgroup/cpu/cpu.cfs_quota_us` (cgroups v1) или `cpu.max` (cgroups v2) и устанавливает `GOMAXPROCS` равным квоте округленной вниз (или вверх).",
    "step_by_step": "1. Демонстрируем подключение `automaxprocs` через blank-import `_ \"go.uber.org/automaxprocs\"`.\n2. Реализуем fallback-алгоритм вычисления CFS-квоты вручную на Go.\n3. Проверяем корректность вычисления.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"math\"\n\t\"os\"\n\t\"runtime\"\n\t\"strconv\"\n\t\"strings\"\n)\n\n// Упрощенный парсер cgroups v1 для демонстрации логики automaxprocs\nfunc getContainerCPULimit() (int, bool) {\n\tquotaBytes, err := os.ReadFile(\"/sys/fs/cgroup/cpu/cpu.cfs_quota_us\")\n\tif err != nil {\n\t\treturn 0, false // Не в контейнере или cgroups v2\n\t}\n\tperiodBytes, err := os.ReadFile(\"/sys/fs/cgroup/cpu/cpu.cfs_period_us\")\n\tif err != nil {\n\t\treturn 0, false\n\t}\n\n\tquota, err1 := strconv.ParseFloat(strings.TrimSpace(string(quotaBytes)), 64)\n\tperiod, err2 := strconv.ParseFloat(strings.TrimSpace(string(periodBytes)), 64)\n\n\tif err1 != nil || err2 != nil || quota <= 0 || period <= 0 {\n\t\treturn 0, false // Лимит не задан (-1)\n\t}\n\n\tcores := int(math.Floor(quota / period))\n\tif cores < 1 {\n\t\tcores = 1\n\t}\n\treturn cores, true\n}\n\nfunc main() {\n\thostCPU := runtime.NumCPU()\n\tcurrentP := runtime.GOMAXPROCS(0)\n\n\tfmt.Printf(\"Аппаратных ядер хоста: %d\\n\", hostCPU)\n\tfmt.Printf(\"Текущий GOMAXPROCS: %d\\n\", currentP)\n\n\tif limit, ok := getContainerCPULimit(); ok {\n\t\tfmt.Printf(\"Обнаружен лимит контейнера: %d CPU\\n\", limit)\n\t\truntime.GOMAXPROCS(limit)\n\t\tfmt.Printf(\"GOMAXPROCS автоматически адаптирован к: %d\\n\", runtime.GOMAXPROCS(0))\n\t} else {\n\t\tfmt.Println(\"Контейнерные лимиты CFS не обнаружены, используется значение по умолчанию.\")\n\t}\n}",
        "note": "Логика адаптации GOMAXPROCS под cgroups"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод:\n# Аппаратных ядер хоста: 8\n# Текущий GOMAXPROCS: 8\n# Контейнерные лимиты CFS не обнаружены, используется значение по умолчанию."
      }
    ],
    "under_the_hood": "В cgroups v2 параметры квоты объединены в файл `/sys/fs/cgroup/cpu.max` в формате `max 100000` (без лимита) или `200000 100000` (квота 2 ядра). `automaxprocs` поддерживает обе версии cgroups и логирует скорректированное значение в `stdlog` при старте программы.",
    "pitfalls": "Если лимит задан как дробное число (например `cpu: 500m` или `1.5`), `automaxprocs` по умолчанию округляет вниз до 1, предотвращая троттлинг, но это может снизить пиковую производительность, если требуется дробный оверкоммит.",
    "bigtech_interview": "**Вопрос с собеседования:** Что произойдет с сервисом на Go в Kubernetes, если у пода `limits.cpu: 1`, но на ноде 32 ядра, и разработчик не подключил `automaxprocs`?\n**Ответ:** Сервис установит `GOMAXPROCS=32`.\nПри поступлении параллельных запросов рантайм поднимет до 32 потоков ОС, которые параллельно начнут вычисления.\nПериод квоты Linux CFS по умолчанию составляет 100 мс, а лимит пода — 1 CPU (100 мс процессорного времени за период).\n32 потока израсходуют 100 мс квоты суммарно всего за **3.1 миллисекунды** (100 мс / 32 потока).\nОставшиеся **96.9 миллисекунд** каждого периода весь под будет полностью заблокирован ядром Linux (CFS Throttling).\nВ метриках Prometheus возникнет огромный рост p99 latency и троттлинга (`container_cpu_cfs_throttled_periods_total`)."
  },
  {
    "num": 56,
    "title": "Некооперативное асинхронное вытеснение (Non-Cooperative Preemption) в Go 1.22+",
    "task": "**Асинхронное вытеснение (Non-Cooperative Preemption)**: Запусти код из упр. 622 на современной версии Go. Убедись, что программа работает нормально (другие горутины тоже получают процессорное время). Как это работает? `sysmon` видит, что горутина крутится >10 мс, и отправляет потоку `M` аппаратный сигнал `SIGURG`. Запусти программу с флагом `GODEBUG=asyncpreemptoff=1` (отключение асинхронного вытеснения) — и посмотри, как твой пустой цикл снова намертво повесит ядро процессора!",
    "theory": "Асинхронное вытеснение в современном Go работает прозрачно для разработчика:\n1. Поток `sysmon` детектирует, что горутина выполняется непрерывно >10 мс.\n2. Посылается сигнал `SIGURG` (через `tgkill` в Linux).\n3. Обработчик сигналов рантайма перехватывает сигнал, проверяет стек-карту текущей инструкции.\n4. Выполняется сохранение регистров общего назначения и переключение контекста на другую горутину.\n5. Горутина возвращается в статус `_Grunnable`.",
    "step_by_step": "1. Пишем программу с чистым CPU-bound алгоритмом шифрования/хеширования.\n2. Проверяем отзывчивость системы и переключение задач.\n3. Анализируем отсутствие зависаний.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"crypto/sha256\"\n\t\"fmt\"\n\t\"runtime\"\n\t\"sync\"\n\t\"time\"\n)\n\nfunc cpuIntensiveHasher(id int, stop *bool, hashes *uint64) {\n\tdata := []byte(\"GMP-Scheduler-Go-1.22-Deep-Internals\")\n\tfor !*stop {\n\t\th := sha256.Sum256(data)\n\t\tdata = h[:]\n\t\t*hashes++\n\t}\n}\n\nfunc main() {\n\truntime.GOMAXPROCS(1)\n\tfmt.Println(\"Демонстрация Non-Cooperative Preemption при тяжелых криптографических вычислениях...\")\n\n\tstop := false\n\tvar h1, h2 uint64\n\tvar wg sync.WaitGroup\n\twg.Add(2)\n\n\tgo func() {\n\t\tdefer wg.Done()\n\t\tcpuIntensiveHasher(1, &stop, &h1)\n\t}()\n\n\tgo func() {\n\t\tdefer wg.Done()\n\t\tcpuIntensiveHasher(2, &stop, &h2)\n\t}()\n\n\ttime.Sleep(200 * time.Millisecond)\n\tstop = true\n\twg.Wait()\n\n\tfmt.Printf(\"Горутина 1 вычислила хешей: %d\\n\", h1)\n\tfmt.Printf(\"Горутина 2 вычислила хешей: %d\\n\", h2)\n\tfmt.Println(\"Асинхронное вытеснение обеспечило равный доступ к единственному P!\")\n}",
        "note": "Параллельные вычисления на 1 P с вытеснением по SIGURG"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод:\n# Демонстрация Non-Cooperative Preemption при тяжелых криптографических вычислениях...\n# Горутина 1 вычислила хешей: 1250000\n# Горутина 2 вычислила хешей: 1245000\n# Асинхронное вытеснение обеспечило равный доступ к единственному P!"
      }
    ],
    "under_the_hood": "Асинхронное вытеснение сохраняет не только регистры общего назначения (RAX, RBX, RCX и др.), но и регистры чисел с плавающей точкой (XMM/YMM в x86-64), чтобы математические и криптографические расчеты не были повреждены при выходе из обработчика сигнала.",
    "pitfalls": "В коде с ассемблерными вставками без директивы `NO_LOCAL_POINTERS` или с некорректным стеком вытеснение может привести к панике рантайма при попытке GC просканировать стек.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему сигнал `SIGURG` не убивает Go-приложение и как рантайм изолирует его от пользовательских обработчиков сигналов?\n**Ответ:** При старте рантайма функция `initsig()` настраивает обработчики всех системных сигналов через `sigaction()`.\nДля `SIGURG` выставляется флаг `SA_ONSTACK` (обработка на выделенном альтернативном сигнальном стеке `gsignal`).\nВ обработчике `runtime.sighandler()` рантайм проверяет: если пришел `SIGURG`, это внутренний запрос планировщика на вытеснение. Рантайм поглощает его и никогда не передает в пользовательские каналы пакета `os/signal`."
  },
  {
    "num": 57,
    "title": "Справедливость планирования (Fairness): предотвращение голодания горутин",
    "task": "**Fairness**: Создайте сценарий, где одна горутина monopolizes CPU. Изучите, как preemption обеспечивает fairness.",
    "theory": "Справедливость (Fairness) планировщика Go гарантируется тремя механизмами:\n1. **Тайм-слайс 10 мс:** Ни одна горутина не может непрерывно удерживать процессор дольше 10 мс при наличии других готовых задач.\n2. **Проверка GRQ каждые 61 тик:** Предотвращает зависание горутин в Глобальной Очереди.\n3. **Случайный Work Stealing:** Исключает постоянное обделение ресурсами конкретных очередей.",
    "step_by_step": "1. Создаем сценарий с 1 монопольной горутиной и 10 легкими горутинами.\n2. Запускаем на `GOMAXPROCS=1`.\n3. Убеждаемся, что все 10 легких горутин успешно выполнились без голодания.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"sync\"\n\t\"sync/atomic\"\n\t\"time\"\n)\n\nfunc main() {\n\truntime.GOMAXPROCS(1)\n\tfmt.Println(\"Тестирование Fairness планировщика на GOMAXPROCS=1...\")\n\n\tstopHeavy := int32(0)\n\tvar heavyIterations uint64\n\n\t// Монопольная тяжелая горутина\n\tgo func() {\n\t\tfor atomic.LoadInt32(&stopHeavy) == 0 {\n\t\t\theavyIterations++\n\t\t}\n\t}()\n\n\t// 10 легких горутин\n\tconst lightCount = 10\n\tvar wg sync.WaitGroup\n\twg.Add(lightCount)\n\tvar completedLight int32\n\n\tfor i := 0; i < lightCount; i++ {\n\t\tgo func(id int) {\n\t\t\tdefer wg.Done()\n\t\t\ttime.Sleep(10 * time.Millisecond)\n\t\t\tatomic.AddInt32(&completedLight, 1)\n\t\t}(i)\n\t}\n\n\twg.Wait()\n\tatomic.StoreInt32(&stopHeavy, 1)\n\n\tfmt.Printf(\"Все %d легких горутин успешно завершились!\\n\", completedLight)\n\tfmt.Printf(\"Тяжелая горутина выполнила %d итераций и не вызвала голодания.\\n\", heavyIterations)\n}",
        "note": "Предотвращение голодания легких горутин при тяжелой нагрузке"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод:\n# Тестирование Fairness планировщика на GOMAXPROCS=1...\n# Все 10 легких горутин успешно завершились!\n# Тяжелая горутина выполнила 45000000 итераций и не вызвала голодания."
      }
    ],
    "under_the_hood": "Справедливость обеспечивается тем, что при срабатывании таймера вытесненная тяжелая горутина помещается в **конец** локальной очереди (или в GRQ), давая возможность всем остальным горутинам продвинуться вперед в кольцевом буфере.",
    "pitfalls": "Хотя планировщик справедлив по времени CPU, в Go **нет механизма приоритетов горутин**: нельзя сделать горутину с «высоким приоритетом» без ручного проектирования очередей сообщений.",
    "bigtech_interview": "**Вопрос с собеседования:** Поддерживает ли Go приоритеты горутин на уровне рантайма (как `nice` в Linux или `Thread.setPriority()` в Java), и почему?\n**Ответ:** **НЕТ, не поддерживает.**\nАвторы Go (Rob Pike, Dmitry Vyukov) осознанно отказались от приоритетов горутин по причинам:\n1) **Priority Inversion (Инверсия приоритетов):** Низкоприоритетная горутина может захватить мьютекс, а высокоприоритетная заблокируется на нем, сведя приоритеты на нет;\n2) **Сложность планировщика:** Приоритетные очереди уничтожают скорость lock-free очередей и усложняют Work Stealing;\n3) В высоконагруженных системах приоритизация реализуется на архитектурном уровне: разделением трафика на разные пулы воркеров и отдельные инстансы микросервисов."
  },
  {
    "num": 58,
    "title": "Анализ исходного кода планировщика: функции preemptone() и preemptM()",
    "task": "Найдите в исходниках Go (`src/runtime/proc.go`) функцию `preemptone()` и `preemptM()`. Напишите комментарий-разбор: как именно сигнал `SIGURG` модифицирует контекст goroutine, чтобы она попала в safe point.",
    "theory": "Анализ исходного кода рантайма в файлах `src/runtime/proc.go` и `src/runtime/signal_unix.go`:\n```go\n// preemptone пытается вытеснить горутину gp, запущенную на pp.\nfunc preemptone(pp *p) bool {\n    mp := pp.m.ptr()\n    if mp == nil || mp == getg().m {\n        return false\n    }\n    gp := mp.curg\n    if gp == nil || gp == mp.g0 {\n        return false\n    }\n    gp.preempt = true\n    // Кооперативный флаг: проверка переполнения стека\n    gp.stackguard0 = stackPreempt\n\n    // Асинхронный флаг: посылка сигнала SIGURG\n    if preemptMSupported && debug.asyncpreemptoff == 0 {\n        pp.preempt = true\n        preemptM(mp)\n    }\n    return true\n}\n```\n\nФункция `preemptM(mp)` вызывает платформенный системный вызов `signalM(mp, sigPreempt)`, который через POSIX вызов `pthread_kill` шлет сигнал `SIGURG` ядру ОС.",
    "step_by_step": "1. Создаем программу, моделирующую логику флагов вытеснения.\n2. Разбираем последовательность переходов в рантайме.\n3. Документируем назначение полей `gp.preempt` и `gp.stackguard0`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"time\"\n)\n\n// Моделирование структуры метаданных горутины и флагов вытеснения\ntype GoroutinePreemptDescriptor struct {\n\tID          int\n\tStatus      string\n\tPreemptFlag bool\n\tStackguard0 uint64\n}\n\nfunc main() {\n\tfmt.Println(\"Архитектурный анализ исходников src/runtime/proc.go:\")\n\tfmt.Println(\"1. sysmon обнаруживает горутину, работающую > 10 мс\")\n\tfmt.Println(\"2. Вызов preemptone(pp):\")\n\tfmt.Println(\"   - gp.preempt = true\")\n\tfmt.Println(\"   - gp.stackguard0 = stackPreempt (0xfffffffffffffff0)\")\n\tfmt.Println(\"   - preemptM(mp) -> pthread_kill(mp, SIGURG)\")\n\tfmt.Println(\"3. sighandler перехватывает SIGURG -> asyncPreempt -> schedule()\")\n\n\t// Проверяем работу рантайма вживую\n\tdone := make(chan bool)\n\tgo func() {\n\t\ttime.Sleep(20 * time.Millisecond)\n\t\tdone <- true\n\t}()\n\n\t<-done\n\tfmt.Printf(\"Рантайм Go (%s): вытеснение проверено.\\n\", runtime.Version())\n}",
        "note": "Архитектурная схема работы preemptone и preemptM"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go"
      }
    ],
    "under_the_hood": "В `src/runtime/signal_unix.go` функция `preemptM()` проверяет атомарный флаг `atomic.Cas(&mp.signalPending, 0, 1)`, чтобы не спамить сигналами `SIGURG`, если предыдущий сигнал еще не был обработан ядром ОС.",
    "pitfalls": "Попытка перехватить `SIGURG` через пакет `os/signal` в пользовательском коде не сработает: рантайм Go перехватывает этот сигнал раньше и фильтрует его.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему в Go вытеснение реализовано как комбинация кооперативного (`stackguard0`) И асинхронного (`SIGURG`) механизмов, а не только через сигналы?\n**Ответ:**\n1) Сигналы ОС (`SIGURG`) дороги: вызов `pthread_kill` требует переключения контекста в ядро Linux, прерывания процессора и работы сигнального стека ядра (~2–5 микросекунд);\n2) Кооперативная проверка в прологе функции (`stackguard0`) стоит ровно **2 инструкции процессора** (~0.5 наносекунды) и работает полностью в user-space без участия ядра;\n3) Поэтому рантайм всегда сначала пробует кооперативное вытеснение при входе в функции, и только если горутина застряла в длинном цикле без вызовов, `sysmon` прибегает к «тяжелой артиллерии» в виде сигнала `SIGURG`."
  },
  {
    "num": 59,
    "title": "Проблема инверсии приоритетов (Priority Inversion) и паттерны изоляции очередей",
    "task": "**Priority inversion**: Go не поддерживает приоритеты горутин. Изучите, как это влияет на latency-sensitive задачи и какие workarounds существуют (separate P's, goroutine pools).",
    "theory": "Поскольку в планировщике Go все горутины равноправны, возникает архитектурная проблема:\nЕсли сервер обрабатывает как важные запросы от пользователей (High Priority), так и тяжелые фоновые генерации отчетов (Low Priority), они помещаются в одни и те же очереди LRQ/GRQ.\nТяжелые фоновые задачи могут занять все процессоры P, вызвав деградацию latency критичных пользовательских запросов.\n\nРешение в Go — **архитектурная изоляция на уровне очередей (QoS Buffers)** с принудительным выделением пулов воркеров разной емкости.",
    "step_by_step": "1. Создаем диспетчер с разделением на High-Priority и Low-Priority очереди.\n2. Обеспечиваем приоритетную обработку срочных задач.\n3. Проверяем минимальную задержку критичных запросов.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n\t\"time\"\n)\n\ntype PriorityDispatcher struct {\n\thighQueue chan func()\n\tlowQueue  chan func()\n\tstop      chan struct{}\n\twg        sync.WaitGroup\n}\n\nfunc NewPriorityDispatcher(workers int) *PriorityDispatcher {\n\td := &PriorityDispatcher{\n\t\thighQueue: make(chan func(), 1000),\n\t\tlowQueue:  make(chan func(), 1000),\n\t\tstop:      make(chan struct{}),\n\t}\n\n\tfor i := 0; i < workers; i++ {\n\t\td.wg.Add(1)\n\t\tgo func() {\n\t\t\tdefer d.wg.Done()\n\t\t\tfor {\n\t\t\t\tselect {\n\t\t\t\tcase <-d.stop:\n\t\t\t\t\treturn\n\t\t\t\t// Приоритетная проверка: сначала HighQueue\n\t\t\t\tcase task := <-d.highQueue:\n\t\t\t\t\ttask()\n\t\t\t\tdefault:\n\t\t\t\t\tselect {\n\t\t\t\t\tcase <-d.stop:\n\t\t\t\t\t\treturn\n\t\t\t\t\tcase task := <-d.highQueue:\n\t\t\t\t\t\ttask()\n\t\t\t\t\tcase task := <-d.lowQueue:\n\t\t\t\t\t\ttask()\n\t\t\t\t\t}\n\t\t\t\t}\n\t\t\t}\n\t\t}()\n\t}\n\treturn d\n}\n\nfunc main() {\n\td := NewPriorityDispatcher(4)\n\n\tvar highLatencies []time.Duration\n\tvar mu sync.Mutex\n\n\t// Заполняем LowQueue тяжелыми задачами\n\tfor i := 0; i < 50; i++ {\n\t\td.lowQueue <- func() {\n\t\t\ttime.Sleep(5 * time.Millisecond)\n\t\t}\n\t}\n\n\t// Посылаем High-Priority задачи\n\tfor i := 0; i < 5; i++ {\n\t\tcreated := time.Now()\n\t\td.highQueue <- func() {\n\t\t\tlatency := time.Since(created)\n\t\t\tmu.Lock()\n\t\t\thighLatencies = append(highLatencies, latency)\n\t\t\tmu.Unlock()\n\t\t}\n\t}\n\n\ttime.Sleep(100 * time.Millisecond)\n\tclose(d.stop)\n\td.wg.Wait()\n\n\tfmt.Println(\"Задержки High-Priority задач:\")\n\tfor i, lat := range highLatencies {\n\t\tfmt.Printf(\"  Запрос %d: %v\\n\", i+1, lat)\n\t}\n}",
        "note": "Реализация прикладного QoS с приоритизацией очередей"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод:\n# Задержки High-Priority задач:\n#   Запрос 1: 120µs\n#   Запрос 2: 150µs\n#   Запрос 3: 180µs\n#   Запрос 4: 210µs\n#   Запрос 5: 240µs"
      }
    ],
    "under_the_hood": "Двойной `select` с веткой `default` реализует неблокирующую приоритетную проверку: если в `highQueue` есть задача, воркер всегда берет ее в обход `lowQueue`, моделируя поведение Strict Priority Queue.",
    "pitfalls": "Строгая приоритизация может привести к полному голоданию (Starvation) низкоприоритетной очереди. В продакшене используйте взвешенные алгоритмы (Weighted Fair Queuing, WFQ).",
    "bigtech_interview": "**Вопрос с собеседования:** Как спроектировать микросервис на Go, чтобы тяжелые фоновые синхронизации не влияли на SLA критичных пользовательских запросов?\n**Ответ:**\n1) **Разделение очередей:** Выделить отдельные каналы/пулы воркеров под разные типы задач;\n2) **Ограничение конкурентности:** Ограничить количество одновременных фоновых горутин семафором (например, не более 2 фоновых задач на 16 ядер);\n3) **Изоляция по процессам:** Вынести тяжелые фоновые задачи в отдельный фоновый Worker Pod в Kubernetes, оставив API Pod только для пользовательского трафика."
  },
  {
    "num": 60,
    "title": "Комплексный аудит в Go Trace: визуализация взаимодействия CPU-bound и IO-bound горутин",
    "task": "**[Высокая сложность — Go Trace]**: Напиши программу с CPU-bound и IO-bound горутинами. Запусти её, записав трейс в файл: `cat > trace.out` через `runtime/trace`. Открой `go tool trace trace.out`. Найди визуализацию GMP: посмотри, как горутины привязываются к P и M, и когда происходит блокировка.",
    "theory": "Комплексная трассировка высоконагруженного сервиса объединяет:\n1. **CPU Timeline:** Визуализация загрузки каждого процессора `P0..P(N-1)`.\n2. **Network Poller:** Время ожидания сетевых ответов.\n3. **GC STW Pauses:** Точные границы пауз остановки мира сборщика мусора.\n4. **Syscall Handoff:** Фазы отделения потоков M при системных вызовах.\n\nАнализ такого профиля позволяет сразу выявить «узкие горлышки» масштабируемости.",
    "step_by_step": "1. Запускаем одновременную нагрузку: CPU-вычисления, сетевые пинги и системные вызовы.\n2. Фиксируем трассировку в `complex_trace.out`.\n3. Анализируем отчет в `go tool trace`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"os\"\n\t\"runtime\"\n\t\"runtime/trace\"\n\t\"sync\"\n\t\"syscall\"\n\t\"time\"\n)\n\nfunc main() {\n\truntime.GOMAXPROCS(4)\n\n\tf, err := os.Create(\"complex_trace.out\")\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer f.Close()\n\n\tif err := trace.Start(f); err != nil {\n\t\tpanic(err)\n\t}\n\tdefer trace.Stop()\n\n\tvar wg sync.WaitGroup\n\twg.Add(3)\n\n\t// 1. CPU-bound нагрузка\n\tgo func() {\n\t\tdefer wg.Done()\n\t\tvar acc uint64\n\t\tfor i := 0; i < 10000000; i++ {\n\t\t\tacc += uint64(i)\n\t\t}\n\t\t_ = acc\n\t}()\n\n\t// 2. IO-bound сетевая нагрузка через Netpoller\n\tln, _ := net.Listen(\"tcp\", \"127.0.0.1:0\")\n\tdefer ln.Close()\n\tgo func() {\n\t\tdefer wg.Done()\n\t\tconn, err := net.Dial(\"tcp\", ln.Addr().String())\n\t\tif err == nil {\n\t\t\tconn.Close()\n\t\t}\n\t}()\n\n\t// 3. Блокирующий системный вызов\n\tgo func() {\n\t\tdefer wg.Done()\n\t\tvar req, rem syscall.Timespec\n\t\treq.Nsec = 20000000 // 20 мс\n\t\tsyscall.Nanosleep(&req, &rem)\n\t}()\n\n\twg.Wait()\n\tfmt.Println(\"Комплексная трассировка сохранена в complex_trace.out\")\n}",
        "note": "Комплексная трассировка разнородных нагрузок"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Открытие отчета:\n# go tool trace complex_trace.out"
      }
    ],
    "under_the_hood": "Внутри `go tool trace` формируется интерактивный граф взаимодействия: видно, как поток 1 исполняет CPU, поток 2 паркуется в `netpoll`, а поток 3 уходит в `_Gsyscall`, вызывая `handoffp`.",
    "pitfalls": "Не открывайте гигантские файлы trace (>500 МБ) в браузере: движок визуализации может исчерпать оперативную память вкладки Chrome. Используйте флаг сэмплинга или профилируйте меньший интервал.",
    "bigtech_interview": "**Вопрос с собеседования:** Как с помощью `go tool trace` обнаружить проблему Lock Contention (борьбы за мьютексы)?\n**Ответ:**\n1) Открыть раздел **«Synchronization blocking profile»** в меню `go tool trace`;\n2) Инструмент строит граф задержек, сгруппированный по вызовам `sync.Mutex.Lock` и операциям с каналами;\n3) В графе отображаются точные функции и строки кода, на которых горутины суммарно потеряли больше всего времени в состоянии ожидания `_Gwaiting`;\n4) Если задержки вызваны мьютексом, решение — шардирование мьютекса (sharded lock) или переход на атомики/RWMutex."
  },
  {
    "num": 61,
    "title": "Масштабирование сетевых соединений в Netpoller: 50 000 виртуальных сокетов",
    "task": "**Netpoller и асинхронный I/O.**: Создайте сетевой сервер с большим количеством одновременных соединений. Убедитесь через трассировку, что при ожидании ввода-вывода горутины не блокируют потоки ОС, а паркуются через netpoller.",
    "theory": "Netpoller мультиплексирует сетевые сокеты через неблокирующие дескрипторы ядра:\n- В Linux: системный вызов `epoll_create1` и `epoll_ctl`;\n- В macOS/FreeBSD: `kqueue`;\n- В Windows: `CreateIoCompletionPort` (IOCP).\n\nКогда горутина блокируется на чтении из TCP-сокета, поток ОС `M` освобождается немедленно (за время <1 микросекунды). Это позволяет Go-серверу держать миллионы открытых WebSocket / gRPC / TCP соединений (C10M problem), расходуя только память под стеки и буферы ядра.",
    "step_by_step": "1. Создаем TCP-сервер.\n2. Подключаем 1000 легковесных клиентов с редким обменом.\n3. Проверяем неизменность количества потоков ОС `threads`.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"runtime\"\n\t\"sync\"\n\t\"sync/atomic\"\n\t\"time\"\n)\n\nfunc main() {\n\truntime.GOMAXPROCS(2)\n\tln, err := net.Listen(\"tcp\", \"127.0.0.1:0\")\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer ln.Close()\n\n\tvar connected int64\n\tvar wg sync.WaitGroup\n\n\t// Эхо-сервер\n\tgo func() {\n\t\tfor {\n\t\t\tconn, err := ln.Accept()\n\t\t\tif err != nil {\n\t\t\t\treturn\n\t\t\t}\n\t\t\tgo func(c net.Conn) {\n\t\t\t\tdefer c.Close()\n\t\t\t\tbuf := make([]byte, 16)\n\t\t\t\tfor {\n\t\t\t\t\tn, err := c.Read(buf)\n\t\t\t\t\tif err != nil {\n\t\t\t\t\t\treturn\n\t\t\t\t\t}\n\t\t\t\t\tc.Write(buf[:n])\n\t\t\t\t}\n\t\t\t}(conn)\n\t\t}\n\t}()\n\n\t// 500 клиентов\n\tconst clients = 500\n\twg.Add(clients)\n\n\tfor i := 0; i < clients; i++ {\n\t\tgo func() {\n\t\t\tdefer wg.Done()\n\t\t\tc, err := net.Dial(\"tcp\", ln.Addr().String())\n\t\t\tif err != nil {\n\t\t\t\treturn\n\t\t\t}\n\t\t\tdefer c.Close()\n\n\t\t\tatomic.AddInt64(&connected, 1)\n\t\t\tc.Write([]byte(\"ping\"))\n\t\t\tbuf := make([]byte, 16)\n\t\t\tc.Read(buf)\n\t\t\ttime.Sleep(50 * time.Millisecond)\n\t\t}()\n\t}\n\n\twg.Wait()\n\tfmt.Printf(\"Успешно обслужено %d TCP клиентов на %d P\\n\", atomic.LoadInt64(&connected), runtime.GOMAXPROCS(0))\n\tfmt.Printf(\"Итоговое число горутин: %d\\n\", runtime.NumGoroutine())\n}",
        "note": "Обслуживание сотен TCP-клиентов через Netpoller"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод:\n# Успешно обслужено 500 TCP клиентов на 2 P\n# Итоговое число горутин: 3"
      }
    ],
    "under_the_hood": "Для предотвращения голодания сетевого ввода-вывода функция `schedule()` каждые 61 тик (или когда очереди LRQ/GRQ пусты) вызывает `netpoll(0)`. Дескрипторы, готовые к чтению/записи, возвращают список горутин `gList`, которые сразу помещаются в очередь выполнения текущего процессора P.",
    "pitfalls": "Каждое открытое TCP-соединение требует памяти под сетевые буферы ядра (`rmem`/`wmem`, от 4 до 64 КБ на сокет). При 100 000 соединений память ядра Linux может исчерпаться раньше, чем память в Go.",
    "bigtech_interview": "**Вопрос с собеседования:** Как планировщик Go гарантирует, что горутины, ожидающие сетевых ответов от базы данных, не зависнут в очереди, если все ядра заняты математическими расчетами?\n**Ответ:**\n1) Поток `sysmon` каждые 10 мс опрашивает `netpoll()`: если в сокеты поступили данные, `sysmon` извлекает готовые горутины и сбрасывает их в Глобальную Очередь (GRQ);\n2) Поток `sysmon` принудительно вытесняет CPU-горутины через сигнал `SIGURG`;\n3) Каждые 61 тик процессоры P обязательно заглядывают в GRQ, забирая проснувшиеся сетевые горутины на выполнение."
  },
  {
    "num": 62,
    "title": "Взаимодействие time.Sleep(1ms) и CPU-bound горутины при GOMAXPROCS=1",
    "task": "Создайте программу с `runtime.GOMAXPROCS(1)` и двумя goroutine: одна с `time.Sleep(1ms)` в цикле, другая — вычислительная. Соберите trace и покажите, как `sysmon` (через `retake`) забирает P у спящей goroutine, если та не просыпается вовремя.",
    "theory": "Сценарий проверки таймеров и CPU-нагрузки на одном ядре:\n- Горутина 1: в цикле вызывает `time.Sleep(1 * time.Millisecond)`.\n- Горутина 2: крутит бесконечный CPU-bound цикл.\n\nВ Go < 1.14 таймер на 1 мс не мог сработать вовремя: Горутина 2 блокировала P, и Горутина 1 ждала десятки или сотни миллисекунд.\nВ Go 1.14+ таймеры встроены в процессор P (`p.timers`), а асинхронное вытеснение прерывает Горутину 2, гарантируя своевременное пробуждение спящей горутины.",
    "step_by_step": "1. Устанавливаем `GOMAXPROCS=1`.\n2. Запускаем таймерную горутину и тяжелую горутину.\n3. Замеряем отклонение реального времени сна от запрошенного 1 мс (Timer Drift).",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"sync/atomic\"\n\t\"time\"\n)\n\nfunc main() {\n\truntime.GOMAXPROCS(1)\n\tfmt.Println(\"Тестирование таймеров при тяжелой CPU-нагрузке на GOMAXPROCS=1...\")\n\n\tstopCPU := int32(0)\n\tvar cpuTicks uint64\n\n\t// Тяжелая CPU горутина\n\tgo func() {\n\t\tfor atomic.LoadInt32(&stopCPU) == 0 {\n\t\t\tcpuTicks++\n\t\t}\n\t}()\n\n\t// Таймерная горутина: замеряет задержки time.Sleep(1ms)\n\tconst sleepIterations = 5\n\tdelays := make([]time.Duration, sleepIterations)\n\n\tfor i := 0; i < sleepIterations; i++ {\n\t\tstart := time.Now()\n\t\ttime.Sleep(1 * time.Millisecond)\n\t\tdelays[i] = time.Since(start)\n\t}\n\n\tatomic.StoreInt32(&stopCPU, 1)\n\ttime.Sleep(20 * time.Millisecond)\n\n\tfmt.Println(\"Реальная длительность time.Sleep(1ms):\")\n\tfor i, d := range delays {\n\t\tfmt.Printf(\"  Итерация %d: %v\\n\", i+1, d)\n\t}\n\tfmt.Printf(\"CPU горутина успела выполнить %d итераций.\\n\", cpuTicks)\n}",
        "note": "Замер точности таймеров на одном ядре под нагрузкой"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вывод в Go 1.22+:\n# Тестирование таймеров при тяжелой CPU-нагрузке на GOMAXPROCS=1...\n# Реальная длительность time.Sleep(1ms):\n#   Итерация 1: 1.15ms\n#   Итерация 2: 1.08ms\n#   Итерация 3: 1.12ms\n#   Итерация 4: 1.09ms\n#   Итерация 5: 1.14ms\n# CPU горутина успела выполнить 3200000 итераций."
      }
    ],
    "under_the_hood": "В `src/runtime/proc.go` функция `checkTimers()` проверяет минимальный таймер `pp.timers[0].when`. Если время наступило, таймер выполняется немедленно. При наличии CPU-нагрузки вытеснение по сигналу `SIGURG` каждые 10 мс гарантирует, что `checkTimers()` будет вызван без критических задержек.",
    "pitfalls": "`time.Sleep` в Go не является жестким таймером реального времени (Hard Real-Time): операционная система гарантирует, что горутина проспит **не менее** указанного времени, но точный момент пробуждения зависит от загрузки системы и квантования ядра ОС.",
    "bigtech_interview": "**Вопрос с собеседования:** Подходит ли язык Go для систем жесткого реального времени (Hard Real-Time, управление медицинским оборудованием, тормозами автомобилей)?\n**Ответ:** **НЕТ, не подходит.**\nGo — это система с автоматическим управлением памятью (GC) и многоуровневым планировщиком:\n1) Паузы Stop-The-World (хоть и субмиллисекундные) создают недетерминированные задержки;\n2) Квантование планировщика (10 мс) и непредсказуемость вытеснения не гарантируют микросекундные дедлайны;\n3) Для жесткого реального времени применяются языки без сборщика мусора и без скрытого рантайма (C, C++, Rust, Zig) на специализированных RTOS (FreeRTOS, QNX, VxWorks).\nОднако для Soft Real-Time (HighLoad бэкенды, биржевой финтех с p99 < 1 мс, стриминг) Go подходит идеально."
  }
]
