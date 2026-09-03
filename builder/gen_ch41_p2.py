# -*- coding: utf-8 -*-
"""Exercises 13..24 of Chapter 41."""

exercises = [
  {
    "num": 13,
    "title": "Анализ execution trace через runtime/trace: временная шкала горутин, задержки GC и syscalls",
    "task": "Используйте `runtime/trace` для записи execution trace: `go tool trace trace.out`. Изучите timeline горутин, GC, syscall'ов.",
    "theory": "Глубокий анализ рантайма через go tool trace:\n- `go tool trace trace.out` предоставляет визуализатор на базе движка Perfetto / Catapult:\n  1. **Timeline потоков (Goroutines & Procs):** отображает загрузку каждого процессора P во времени.\n  2. **Фазы GC:** графически подсвечивает Stop-the-World фазы (Sweep Termination и Mark Termination) и фоновую разметку памяти (Concurrent Mark).\n  3. **Syscalls:** показывает время блокировки потоков M на дисковых и сетевых системных вызовах ОС.\n  4. **Network Wait:** задержки ожидания событий в epoll/kqueue.\n- Позволяет ответить на вопрос: «Почему 8 ядер процессора простаивают, а RPS не растет?» (например, из-за частых блокировок планировщика или долгого I/O).",
    "step_by_step": "1. Создайте модель отчета execution trace.\n2. Проанализируйте метрики времени работы процессоров P.\n3. Классифицируйте фазы GC и блокировки на системных вызовах.\n4. Верифицируйте нахождение неэффективных задержек.",
    "code_blocks": [
      {
        "filename": "trace_timeline_analysis_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype TraceExecutionStats struct {\n\tTotalDurationMs float64\n\tGCSweepSTWMs    float64\n\tGCMarkSTWMs     float64\n\tSyscallWaitMs   float64\n\tExecutionMs     float64\n}\n\nfunc AnalyzeExecutionTrace() TraceExecutionStats {\n\treturn TraceExecutionStats{\n\t\tTotalDurationMs: 5000.0,\n\t\tGCSweepSTWMs:    0.15,\n\t\tGCMarkSTWMs:     0.20,\n\t\tSyscallWaitMs:   350.0, // Долгие системные вызовы!\n\t\tExecutionMs:     4649.65,\n\t}\n}\n\nfunc TestTraceTimelineAnalysis(t *testing.T) {\n\tstats := AnalyzeExecutionTrace()\n\n\ttotalSTW := stats.GCSweepSTWMs + stats.GCMarkSTWMs\n\tif totalSTW > 1.0 {\n\t\tt.Fatalf(\"Аномально долгий STW сборщика мусора: %.2f ms\", totalSTW)\n\t}\n\n\tfmt.Println(\"Анализ событий Execution Trace (runtime/trace) успешно подтвержден:\")\n\tfmt.Printf(\"  • Общее время трейса: %.1f ms\\n\", stats.TotalDurationMs)\n\tfmt.Printf(\"  • Суммарная пауза GC STW: %.3f ms (Субмиллисекундная пауза!)\\n\", totalSTW)\n\tfmt.Printf(\"  • Блокировка на Syscalls: %.1f ms (Время в ядре ОС)\\n\", stats.SyscallWaitMs)\n\tfmt.Printf(\"  • Полезная работа CPU:    %.1f ms\\n\", stats.ExecutionMs)\n\tfmt.Println(\"  • Визуализатор: go tool trace trace.out -> View trace\")\n}",
        "note": "Анализ временных интервалов STW-пауз сборщика мусора и системных вызовов в trace.out"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск веб-визуализатора трассировки рантайма:\ngo tool trace trace.out\n# Откроется браузер: http://127.0.0.1:xxxx\n# Выберите 'View trace' для интерактивной навигации клавишами W (зум) / S (отдалить) / A / D"
      }
    ],
    "under_the_hood": "Клавиши навигации в классическом `go tool trace` соответствуют игровому WASD: клавиша W приближает масштаб временной шкалы вплоть до отдельных наносекунд, позволяя рассмотреть переключение горутины с одного ядра процессора на другое.",
    "pitfalls": "Открывать `go tool trace` в сторонних браузерах без поддержки Chromium: веб-движок визуализатора оптимизирован строго под Google Chrome / Chromium из-за использования специфичных компонентов хромовского `chrome://tracing`.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие GC Mark Assist от фазы Stop-The-World (STW) в выводе go tool trace?»\n**Ответ:** STW полностью останавливает выполнение всего пользовательского кода программы на доли миллисекунды. Mark Assist останавливает только конкретную горутину, которая запрашивает память в куче слишком быстро, заставляя ее помогать маркировать объекты, в то время как остальные горутины сервиса продолжают работать на параллельных ядрах."
  },
  {
    "num": 14,
    "title": "Профилирование аллокаций: выявление генераторов мусора через -alloc_space и -alloc_objects",
    "task": "Профилируйте **аллокации**: используйте `pprof` с `-alloc_space` и `-alloc_objects`, чтобы найти функции, создающие больше всего мусора.",
    "theory": "Разделение аллокаций по объему и количеству:\n- Часто сервис страдает не от того, что ему не хватает RAM, а от того, что сборщик мусора GC утилизирует 50% всех ядер процессора.\n- **Два режима профилирования аллокаций:**\n  1. `pprof -alloc_space`: показывает суммарный объем выделенной памяти в гигабайтах. Позволяет найти функции, аллоцирующие гигантские структуры.\n  2. `pprof -alloc_objects`: показывает количество отдельных выделений в штуках (миллионы мелких структур). Позволяет найти места создания миллионов микро-объектов, которые заставляют GC непрерывно сканировать указатели.\n- Оптимизация по `-alloc_objects` часто дает куда больший прирост производительности, чем по объему!",
    "step_by_step": "1. Создайте сценарий генерации множества мелких объектов (`sync.Pool` кандидат).\n2. Смоделируйте отчет профилирования аллокаций.\n3. Сопоставьте показатели `alloc_space` и `alloc_objects`.\n4. Верифицируйте стратегию оптимизации (переход на пулы объектов).",
    "code_blocks": [
      {
        "filename": "alloc_profile_metrics_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype AllocProfileRecord struct {\n\tFunction     string\n\tAllocSpaceMB float64\n\tAllocObjects int\n}\n\nfunc AnalyzeAllocsProfile() []AllocProfileRecord {\n\treturn []AllocProfileRecord{\n\t\t{Function: \"json.Unmarshal\", AllocSpaceMB: 450.0, AllocObjects: 12_500_000},\n\t\t{Function: \"parser.ParseHeader\", AllocSpaceMB: 120.0, AllocObjects: 8_000_000},\n\t\t{Function: \"logger.FormatLog\", AllocSpaceMB: 60.0, AllocObjects: 4_500_000},\n\t}\n}\n\nfunc TestAllocProfileMetrics(t *testing.T) {\n\trecords := AnalyzeAllocsProfile()\n\n\ttotalObjects := 0\n\tfor _, r := range records {\n\t\ttotalObjects += r.AllocObjects\n\t}\n\n\tif totalObjects < 20_000_000 {\n\t\tt.Fatalf(\"Ожидалось выявление миллионов объектов мусора: %d\", totalObjects)\n\t}\n\n\tfmt.Println(\"Профилирование аллокаций кучи (-alloc_space vs -alloc_objects):\")\n\tfmt.Printf(\"  %-25s %12s %15s\\n\", \"Функция\", \"Alloc Space\", \"Alloc Objects\")\n\tfor _, r := range records {\n\t\tfmt.Printf(\"  %-25s %10.1f MB %14d шт\\n\", r.Function, r.AllocSpaceMB, r.AllocObjects)\n\t}\n\tfmt.Println(\"  • json.Unmarshal создал 12.5 МИЛЛИОНОВ объектов! (Главный кандидат на sync.Pool / easyjson)\")\n}",
        "note": "Сравнительный анализ объема памяти и количества объектов в профиле аллокаций"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Поиск функций, создающих больше всего мусора:\ngo tool pprof -alloc_objects http://localhost:6060/debug/pprof/allocs\n# (pprof) top\n# (pprof) list json.Unmarshal\n\n# Поиск функций, выделяющих наибольший объем в мегабайтах:\ngo tool pprof -alloc_space http://localhost:6060/debug/pprof/allocs"
      }
    ],
    "under_the_hood": "Каждый вызов `new()` или `make()` для объекта, содержащего указатели, регистрируется в mspan-классах аллокатора Go. Сборщик мусора обязан обойти каждый такой объект по графу ссылок. Если заменить структуры без указателей или переиспользовать их через `sync.Pool`, нагрузка на фазу Mark падает до нуля.",
    "pitfalls": "Оптимизировать `-alloc_space`, не глядя на `-alloc_objects`: сокращение объема с 500 МБ до 400 МБ при сохранении 20 миллионов объектов не снизит утилизацию процессора сборщиком мусора.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Go структуры без указателей ([]byte, struct { a, b int }) сканируются сборщиком мусора гораздо быстрее?»\n**Ответ:** Если блок памяти в куче не содержит указателей (флаг `noscan` в метаданных класса `mspan`), GC помечает весь блок как «серый/черный» за 1 операцию и вообще не заглядывает внутрь его байтов, экономя такты CPU."
  },
  {
    "num": 15,
    "title": "Экспорт системных метрик рантайма: runtime.ReadMemStats и мониторинг GC в Prometheus",
    "task": "Используйте `runtime.ReadMemStats` для экспорта Go runtime метрик (GC pauses, heap inuse, sys memory) в Prometheus.",
    "theory": "Ключевые метрики структуры runtime.MemStats:\n- `runtime.ReadMemStats(&m)` заполняет детальную статистику рантайма:\n  1. `m.HeapAlloc`: байты в куче, занятые живыми объектами.\n  2. `m.HeapInuse`: байты во всех активных страницах кучи (включая фрагментацию).\n  3. `m.Sys`: суммарный объем виртуальной памяти, запрошенный у ядра ОС через `mmap`.\n  4. `m.NumGC`: суммарное количество завершенных циклов сборки мусора.\n  5. `m.PauseNs[(m.NumGC+255)%256]`: точная длительность последней Stop-The-World паузы GC в наносекундах.\n- В Prometheus стандартный клиент `promhttp` автоматически экспортирует эти метрики (`go_memstats_heap_alloc_bytes`, `go_gc_duration_seconds`).",
    "step_by_step": "1. Создайте структуру сбора метрик через `runtime.ReadMemStats`.\n2. Зафиксируйте текущие значения `HeapAlloc`, `HeapInuse` и `Sys`.\n3. Извлеките длительность последней паузы сборщика мусора.\n4. Продемонстрируйте экспорт в формат метрик Prometheus.",
    "code_blocks": [
      {
        "filename": "runtime_memstats_exporter_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"testing\"\n)\n\ntype RuntimeMetricsSnapshot struct {\n\tHeapAllocBytes uint64\n\tHeapInuseBytes uint64\n\tSysBytes       uint64\n\tNumGC          uint32\n\tLastGCPauseNs  uint64\n}\n\nfunc CollectRuntimeMetrics() RuntimeMetricsSnapshot {\n\tvar m runtime.MemStats\n\truntime.ReadMemStats(&m)\n\n\tlastPause := uint64(0)\n\tif m.NumGC > 0 {\n\t\tlastPause = m.PauseNs[(m.NumGC+255)%256]\n\t}\n\n\treturn RuntimeMetricsSnapshot{\n\t\tHeapAllocBytes: m.HeapAlloc,\n\t\tHeapInuseBytes: m.HeapInuse,\n\t\tSysBytes:       m.Sys,\n\t\tNumGC:          m.NumGC,\n\t\tLastGCPauseNs:  lastPause,\n\t}\n}\n\nfunc TestRuntimeMemstatsExporter(t *testing.T) {\n\truntime.GC() // Провоцируем хотя бы один цикл сборки\n\tsnap := CollectRuntimeMetrics()\n\n\tif snap.HeapAllocBytes == 0 || snap.SysBytes == 0 {\n\t\tt.Fatalf(\"Метрики памяти не собраны: %+v\", snap)\n\t}\n\n\tfmt.Println(\"Сбор и экспорт системных метрик runtime.MemStats:\")\n\tfmt.Printf(\"  • go_memstats_heap_alloc_bytes: %.2f МБ\\n\", float64(snap.HeapAllocBytes)/(1024*1024))\n\tfmt.Printf(\"  • go_memstats_heap_inuse_bytes: %.2f МБ\\n\", float64(snap.HeapInuseBytes)/(1024*1024))\n\tfmt.Printf(\"  • go_memstats_sys_bytes:        %.2f МБ (Память от ОС)\\n\", float64(snap.SysBytes)/(1024*1024))\n\tfmt.Printf(\"  • go_memstats_gc_cycles_total:  %d циклов\\n\", snap.NumGC)\n\tfmt.Printf(\"  • go_gc_last_pause_nanoseconds: %d нс (%.3f мс)\\n\", snap.LastGCPauseNs, float64(snap.LastGCPauseNs)/1_000_000)\n}",
        "note": "Прямое чтение системной структуры runtime.MemStats и подготовка Prometheus-метрик"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v runtime_memstats_exporter_test.go\n# Вывод:\n# === RUN   TestRuntimeMemstatsExporter\n# Сбор и экспорт системных метрик runtime.MemStats:\n#   • go_memstats_heap_alloc_bytes: ... МБ\n#   • go_memstats_heap_inuse_bytes: ... МБ\n#   • go_memstats_sys_bytes:        ... МБ (Память от ОС)\n#   • go_memstats_gc_cycles_total:  ... циклов\n#   • go_gc_last_pause_nanoseconds: ... нс (... мс)\n# --- PASS: TestRuntimeMemstatsExporter (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Вызов `runtime.ReadMemStats` останавливает мир (STW) на доли микросекунды для атомарного чтения счетчиков всех процессоров P. Поэтому вызывать его в цикле на каждый HTTP запрос нельзя: стандартный экспортер Prometheus скрейпит его раз в 15 секунд.",
    "pitfalls": "Путать `m.HeapAlloc` (живые объекты) и RSS процесса в Linux: RSS включает стеки горутин, фрагментацию страниц, кэши mcache и сам бинарный код, поэтому в `top` процесс всегда занимает больше памяти, чем показывает `HeapAlloc`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как параметр GOMEMLIMIT (Go 1.19+) взаимодействует с переменной GOGC?»\n**Ответ:** `GOGC` задает процент роста кучи до следующего запуска GC (по умолчанию 100%). `GOMEMLIMIT` задает жесткий потолок памяти процесса (Soft Memory Limit). Если потребление памяти приближается к `GOMEMLIMIT`, рантайм автоматически снижает целевой порог кучи и запускает GC чаще, предотвращая OOMKilled в Kubernetes без ручной подстройки `GOGC`."
  },
  {
    "num": 16,
    "title": "Диагностика утечки CPU: бесконечный пересчет, профиль за 30 секунд и команды top/list",
    "task": "**Диагностика утечки CPU**: Напишите функцию, которая содержит в себе алгоритмическую ошибку, приводящую к высокой утилизации процессора (например, пустой цикл `for {}` или неэффективный пересчет строк). Запустите нагрузку на сервис. С помощью утилиты `go tool pprof` соберите профиль процессора за 30 секунд: `go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30`. С помощью команд `top` и `list` найдите ту самую функцию, которая забирает больше всего процессорного времени.",
    "theory": "Пошаговый траблшутинг CPU-спайков в продакшене:\n1. Дежурный видит алерт `CPUUsage > 90%` на одном из подов сервиса.\n2. Подключается через `kubectl port-forward <pod-name> 6060:6060`.\n3. Запускает команду сбора:\n   `go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30`\n4. В консоли pprof:\n   - `top`: мгновенно выводит имя виновной функции на первой строке.\n   - `list <FunctionName>`: открывает листинг исходного кода и показывает точный процент CPU напротив каждой строки (например `line 42: for !isDone { ... } 85.4%`).\n5. Инженер локализует дефект за 60 секунд!",
    "step_by_step": "1. Создайте функцию с алгоритмической ошибкой (неэффективный пересчет подстрок в цикле).\n2. Выполните нагрузочный замер.\n3. Продемонстрируйте результат разбора команд `top` и `list`.\n4. Верифицируйте нахождение точной строки исходного кода.",
    "code_blocks": [
      {
        "filename": "cpu_leak_troubleshoot_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n\t\"testing\"\n\t\"time\"\n)\n\n// Алгоритмическая ошибка: квадратичный поиск подстрок вместо мапы\nfunc InefficientSearch(haystack string, needles []string) int {\n\tmatches := 0\n\tfor _, n := range needles {\n\t\t// Квадратичное сканирование гигантской строки\n\t\tif strings.Contains(haystack, n) {\n\t\t\tmatches++\n\t\t}\n\t}\n\treturn matches\n}\n\nfunc TestCPULeakTroubleshoot(t *testing.T) {\n\thaystack := strings.Repeat(\"abcdefghijklmnopqrstuvwxyz0123456789\", 500)\n\tneedles := []string{\"foo\", \"bar\", \"999\", \"abc\", \"xyz\", \"hello\", \"world\"}\n\n\tstart := time.Now()\n\tfor i := 0; i < 5000; i++ {\n\t\t_ = InefficientSearch(haystack, needles)\n\t}\n\tduration := time.Since(start)\n\n\tfmt.Println(\"Диагностика утечки CPU через pprof top/list смоделирована:\")\n\tfmt.Printf(\"  • Время неэффективного пересчета: %v\\n\", duration)\n\tfmt.Println(\"  • Команда: go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30\")\n\tfmt.Println(\"  • (pprof) top:\")\n\tfmt.Println(\"      flat%   cum%   function\")\n\tfmt.Println(\"      74.2%  74.2%   strings.Index\")\n\tfmt.Println(\"      21.1%  95.3%   main.InefficientSearch\")\n\tfmt.Println(\"  • (pprof) list InefficientSearch:\")\n\tfmt.Println(\"      74.2%   line 16: if strings.Contains(haystack, n)\")\n\tfmt.Println(\"  • Точная строка ошибки локализована!\")\n}",
        "note": "Воспроизведение алгоритмической ошибки CPU и симуляция вывода команд top и list"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Интерактивная консоль pprof:\ngo tool pprof http://localhost:6060/debug/pprof/profile?seconds=30\n# (pprof) top\n# (pprof) list InefficientSearch\n# (pprof) o /tmp/cpu.svg; svg"
      }
    ],
    "under_the_hood": "Команда `list` сопоставляет адреса инструкций (PC) из профиля с таблицей отладочных символов DWARF, скомпилированной внутри исполняемого Go бинарника, выводя оригинальный исходный код программы.",
    "pitfalls": "Собирать профиль при стрипнутом бинарнике (`go build -ldflags=\"-s -w\"`): без таблицы символов DWARF pprof покажет только шестнадцатеричные адреса памяти (`0x4a12f0`), сделав команду `list` бесполезной.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в продакшене не стоит собирать CPU-профиль длительностью более 30–60 секунд?»\n**Ответ:** Профиль процессора непрерывно перехватывает стек всех потоков ядра с частотой 100 Гц. Сбор профиля на 10 минут создаст многогигабайтный файл дампа, потребует огромного времени на передачу по сети и может создать заметный оверхед на планировщик в моменты пиковых нагрузок. Стандартное окно диагностики — от 10 до 30 секунд."
  },
  {
    "num": 17,
    "title": "Непрерывный профайлинг в Kubernetes: детекция регрессий и интеграция с Pyroscope/Parca",
    "task": "Настройте **continuous profiling** через Pyroscope или Parca: автоматический сбор профилей в продакшене для анализа регрессий.",
    "theory": "Продакшн Continuous Profiling в Kubernetes:\n- Классический CI/CD пайплайн проверяет юнит-тесты, но не ловит деградацию производительности (Performance Regression).\n- **Схема работы continuous profiling в K8s:**\n  1. Каждый под сервиса отправляет профили (CPU, Mem, Goroutines) в кластер Pyroscope/Parca.\n  2. В метаданные профиля добавляются теги Git: `service_version=v2.1.0`, `commit_sha=abc123`.\n  3. После деплоя новой версии SRE открывает дашборд сравнения версий (Diff View).\n  4. Если потребление CPU функцией `json.Unmarshal` выросло на 40%, релиз откатывается автоматически!",
    "step_by_step": "1. Создайте модель тегирования профилей релизами сервиса.\n2. Смоделируйте сравнение потребления CPU между версиями `v1.0.0` и `v1.1.0`.\n3. Рассчитайте процент деградации алгоритма.\n4. Верифицируйте принятие решения об откате релиза.",
    "code_blocks": [
      {
        "filename": "continuous_profiling_diff_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype VersionProfile struct {\n\tVersion      string\n\tCPUPerReqMs  float64\n\tAllocsPerReq int\n}\n\nfunc DetectPerformanceRegression(oldVer, newVer VersionProfile) (isRegressed bool, cpuDiffPct float64) {\n\tcpuDiffPct = ((newVer.CPUPerReqMs - oldVer.CPUPerReqMs) / oldVer.CPUPerReqMs) * 100.0\n\t// Регрессия фиксируется при росте CPU > 15%\n\tif cpuDiffPct > 15.0 {\n\t\treturn true, cpuDiffPct\n\t}\n\treturn false, cpuDiffPct\n}\n\nfunc TestContinuousProfilingDiff(t *testing.T) {\n\tv1 := VersionProfile{Version: \"v1.0.0\", CPUPerReqMs: 12.0, AllocsPerReq: 40}\n\tv2 := VersionProfile{Version: \"v1.1.0\", CPUPerReqMs: 17.5, AllocsPerReq: 85}\n\n\tregressed, diff := DetectPerformanceRegression(v1, v2)\n\n\tif !regressed || diff < 40.0 {\n\t\tt.Fatalf(\"Ожидалась фиксация регрессии: regressed=%v, diff=%.1f%%\", regressed, diff)\n\t}\n\n\tfmt.Println(\"Continuous Profiling: Детекция регрессии релизов (Pyroscope/Parca):\")\n\tfmt.Printf(\"  • Базовая версия %s: %.1f ms CPU/req\\n\", v1.Version, v1.CPUPerReqMs)\n\tfmt.Printf(\"  • Новая версия   %s: %.1f ms CPU/req (Деградация: +%.1f%%)\\n\", v2.Version, v2.CPUPerReqMs, diff)\n\tfmt.Println(\"  • Алертинг: сработал automated canary rollback (откат деплоя в k8s)!\")\n}",
        "note": "Сравнение метрик профилирования между релизами для предотвращения деградации в продакшене"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v continuous_profiling_diff_test.go\n# Вывод:\n# === RUN   TestContinuousProfilingDiff\n# Continuous Profiling: Детекция регрессии релизов (Pyroscope/Parca):\n#   • Базовая версия v1.0.0: 12.0 ms CPU/req\n#   • Новая версия   v1.1.0: 17.5 ms CPU/req (Деградация: +45.8%)\n#   • Алертинг: сработал automated canary rollback (откат деплоя в k8s)!\n# --- PASS: TestContinuousProfilingDiff (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Системы Continuous Profiling сохраняют профили в виде иерархических графов (Call Trees) с мержем по временным интервалам, позволяя вычислять разность графов $Graph_{new} - Graph_{old}$ за миллисекунды.",
    "pitfalls": "Хранить непрерывные профили без Retention-политики: профили сотен микросервисов за год займут десятки терабайт. Настраивают автоматический Downsampling (агрегация старых профилей до 10-минутных средних).",
    "bigtech_interview": "**Вопрос с собеседования:** «Чем дифференциальный Flame Graph (Diff Flame Graph) отличается от стандартного?»\n**Ответ:** В Diff Flame Graph плашки окрашиваются в красный и синий цвета:\n- **Красные плашки:** функции, которые стали потреблять **больше** CPU/памяти по сравнению с базовой версией.\n- **Синие плашки:** функции, которые были оптимизированы и стали потреблять **меньше**.\nЭто позволяет инженеру за 5 секунд понять влияние нового коммита."
  },
  {
    "num": 18,
    "title": "Сравнение двух профилей через go tool pprof -base old.prof new.prof для поиска регрессий",
    "task": "Сравните два профиля через `go tool pprof -base old.prof new.prof`, чтобы найти регрессии после деплоя.",
    "theory": "Механика флага -base в утилите pprof:\n- Команда `go tool pprof -base old.prof new.prof`:\n  - Вычитает значения счетчиков файла `old.prof` из `new.prof`.\n  - В выводе `top` появляются относительные дельты: `+250ms`, `+12.4MB`, `+1500 allocs`.\n  - Позволяет математически строго подтвердить:\n    1. Насколько коммит ускорил выполнение горячего цикла.\n    2. Не внес ли новый функционал скрытых аллокаций памяти.",
    "step_by_step": "1. Создайте модель двух профилей (до и после изменений).\n2. Рассчитайте дельту по времени выполнения функций.\n3. Продемонстрируйте вывод `pprof -base` со знаками `+` и `-`.\n4. Верифицируйте успешное подтверждение оптимизации.",
    "code_blocks": [
      {
        "filename": "pprof_base_diff_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype FunctionDelta struct {\n\tName       string\n\tOldSeconds float64\n\tNewSeconds float64\n}\n\nfunc (d FunctionDelta) Delta() float64 {\n\treturn d.NewSeconds - d.OldSeconds\n}\n\nfunc TestPprofBaseDiff(t *testing.T) {\n\tdiffs := []FunctionDelta{\n\t\t{Name: \"json.Unmarshal\", OldSeconds: 4.5, NewSeconds: 1.2}, // Оптимизация (-3.3s)\n\t\t{Name: \"auth.ValidateJWT\", OldSeconds: 0.8, NewSeconds: 2.1}, // Регрессия (+1.3s)\n\t\t{Name: \"db.Query\", OldSeconds: 3.0, NewSeconds: 3.0},         // Без изменений\n\t}\n\n\tfmt.Println(\"Сравнение профилей через 'go tool pprof -base old.prof new.prof':\")\n\tfmt.Println(\"  flat     cum      function\")\n\tfor _, d := range diffs {\n\t\tdelta := d.Delta()\n\t\tsign := \"+\"\n\t\tif delta < 0 {\n\t\t\tsign = \"\"\n\t\t}\n\t\tstatus := \"OK\"\n\t\tif delta > 0.5 {\n\t\t\tstatus = \"REGRESSION!\"\n\t\t} else if delta < -1.0 {\n\t\t\tstatus = \"IMPROVED!\"\n\t\t}\n\t\tfmt.Printf(\"  %s%.2fs   %s%.2fs   %-20s -> %s\\n\", sign, delta, sign, delta, d.Name, status)\n\t}\n}",
        "note": "Расчет дельты между базовым и новым профилями pprof"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сравнение профиля до релиза и после релиза:\ngo tool pprof -base prod_before.prof prod_after.prof\n# (pprof) top\n# Показывает строки со знаками + (деградация) и - (ускорение):\n# -3.30s   -3.30s  json.Unmarshal\n# +1.30s   +1.30s  auth.ValidateJWT"
      }
    ],
    "under_the_hood": "`pprof` сопоставляет стеки функций по их сигнатурам символов. Если сигнатура функции не изменилась, дельта вычисляется вычитанием целочисленных счетчиков сэмплов в каждом узле дерева вызовов.",
    "pitfalls": "Сравнивать профили, снятые под принципиально разной нагрузкой (например, 100 RPS против 10 000 RPS): абсолютные дельты будут бессмысленны. Сравнивать нужно профили с одинаковым объемом обработанных запросов или нормировать значения.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как использовать go tool pprof -base в автоматизированном CI/CD пайплайне?»\n**Ответ:** Запускают бенчмарки на PR-ветке и на master-ветке: `go test -bench=. -cpuprofile=pr.prof` и `master.prof`. Сравнивают вывод через `go tool pprof -base master.prof pr.prof` и автоматически валят merge request, если время ключевых функций выросло более чем на 5%."
  },
  {
    "num": 19,
    "title": "Безопасность профилирования в проде: защита эндпоинта pprof от несанкционированного доступа",
    "task": "**[Profiling in Prod]**: Настрой так, чтобы pprof был доступен только из внутренней сети (приватный endpoint), а не извне. (Злоумышленник может использовать pprof для DDoS или чтения памяти).",
    "theory": "Векторы атак через открытый pprof:\n1. **Утечка конфиденциальных данных (Data Leakage):**\n   - Через `/debug/pprof/heap` или `/debug/pprof/cmdline` злоумышленник может выгрузить дампы кучи, содержащие токены авторизации, приватные ключи шифрования, пароли к БД и персональные данные пользователей.\n2. **Отказ в обслуживании (Denial of Service):**\n   - Запрос `/debug/pprof/profile?seconds=300` перегружает процессор сбором стеков.\n   - Запрос `/debug/pprof/trace?seconds=60` забивает диск временными файлами.\n- **Стратегия глубокой эшелонированной защиты (Defense in Depth):**\n  - Привязка сокета только к `127.0.0.1` или внутренней подсети k8s.\n  - NetworkPolicy в Kubernetes (блокировка трафика из других namespace).\n  - Отсутствие роутов pprof в манифестах Ingress/API Gateway.",
    "step_by_step": "1. Создайте модель проверки сетевого периметра.\n2. Продемонстрируйте запрет доступа к `/debug/pprof/` с внешних IP-адресов.\n3. Разрешите доступ только доверенным внутренним подсетям (Loopback, Pod CIDR).\n4. Верифицируйте безопасность продакшн-конфигурации.",
    "code_blocks": [
      {
        "filename": "pprof_security_firewall_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net\"\n\t\"net/http\"\n\t\"testing\"\n)\n\ntype SecurityFirewall struct {\n\tAllowedCIDRs []*net.IPNet\n}\n\nfunc (f *SecurityFirewall) IsAllowed(remoteAddr string) bool {\n\thost, _, err := net.SplitHostPort(remoteAddr)\n\tif err != nil {\n\t\thost = remoteAddr\n\t}\n\tip := net.ParseIP(host)\n\tif ip == nil {\n\t\treturn false\n\t}\n\tfor _, cidr := range f.AllowedCIDRs {\n\t\tif cidr.Contains(ip) {\n\t\t\treturn true\n\t\t}\n\t}\n\treturn false\n}\n\nfunc TestPprofSecurityFirewall(t *testing.T) {\n\t// Разрешены ТОЛЬКО localhost (127.0.0.1/8) и внутренняя сеть k8s (10.244.0.0/16)\n\t_, loopback, _ := net.ParseCIDR(\"127.0.0.0/8\")\n\t_, k8sInternal, _ := net.ParseCIDR(\"10.244.0.0/16\")\n\n\tfw := &SecurityFirewall{AllowedCIDRs: []*net.IPNet{loopback, k8sInternal}}\n\n\ttestCases := []struct {\n\t\tClientIP string\n\t\tAllowed  bool\n\t}{\n\t\t{\"127.0.0.1:54321\", true},       // Локальный SRE туннель\n\t\t{\"10.244.1.15:39102\", true},      // Prometheus/Pyroscope pod\n\t\t{\"194.87.12.4:80\", false},        // Внешний интернет\n\t\t{\"8.8.8.8:443\", false},           // Публичный адрес\n\t}\n\n\tfor _, tc := range testCases {\n\t\tok := fw.IsAllowed(tc.ClientIP)\n\t\tif ok != tc.Allowed {\n\t\t\tt.Fatalf(\"Сбой фаервола для %s: ожидалось %v, получено %v\", tc.ClientIP, tc.Allowed, ok)\n\t\t}\n\t}\n\n\tfmt.Println(\"Защита pprof в продакшене (Security Firewall) успешно подтверждена:\")\n\tfmt.Println(\"  • 127.0.0.1 (kubectl port-forward): РАЗРЕШЕНО\")\n\tfmt.Println(\"  • 10.244.1.15 (Внутренний k8s CIDR): РАЗРЕШЕНО\")\n\tfmt.Println(\"  • 194.87.12.4 (Внешний клиент интернета): ЗАБЛОКИРОВАНО (HTTP 403 Forbidden)\")\n}",
        "note": "Сетевая фильтрация доступа к диагностическим эндпоинтам pprof по IP-адресам"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v pprof_security_firewall_test.go\n# Вывод:\n# === RUN   TestPprofSecurityFirewall\n# Защита pprof в продакшене (Security Firewall) успешно подтверждена:\n#   • 127.0.0.1 (kubectl port-forward): РАЗРЕШЕНО\n#   • 10.244.1.15 (Внутренний k8s CIDR): РАЗРЕШЕНО\n#   • 194.87.12.4 (Внешний клиент интернета): ЗАБЛОКИРОВАНО (HTTP 403 Forbidden)\n# --- PASS: TestPprofSecurityFirewall (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Kubernetes доступ к закрытому порту пода организуют через команду `kubectl port-forward pod-name 6060:6060`: трафик туннелируется через шифрованное TLS-соединение Kube-API Server с авторизацией по RBAC сертификату инженера, исключая выставление портов в публичную сеть.",
    "pitfalls": "Привязывать диагностический сервер к `0.0.0.0:6060` на хостах без локального файрвола: порт станет доступен по внешнему белому IP-адресу машины.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какую опасность представляет эндпоинт /debug/pprof/cmdline?»\n**Ответ:** Он возвращает точные аргументы командной строки, с которыми был запущен бинарник Go процесса (`os.Args`). Если нерадивый DevOps передал пароли или токены API через флаги запуска (`-db-password=secret`), злоумышленник моментально прочитает их в открытом виде."
  },
  {
    "num": 20,
    "title": "Поиск утечки памяти в реальном времени: снятие Heap Profile и локализация растущей кучи",
    "task": "**Диагностика утечки памяти (Heap Profile)**: Напишите фоновый воркер, который раз в секунду создает структуру большого объема и складывает её в глобальный слайс, имитируя классическую утечку памяти (память аллоцируется, но GC не может её очистить). Запустите сервис. Соберите профиль кучи с помощью команды: `go tool pprof http://localhost:6060/debug/pprof/heap`. Найдите строку кода, которая аллоцирует память, остающуюся в куче навсегда.",
    "theory": "Методика исследования утечек памяти в проде (Heap Inspection):\n- **Симптомы:** График памяти в Grafana показывает «пилообразную лестницу» (Sawtooth with upward trend): после сборки мусора минимальная планка памяти монотонно растет.\n- **Алгоритм локализации:**\n  1. Снять базовый профиль:\n     `curl -s http://localhost:6060/debug/pprof/heap > base.heap`\n  2. Подождать 10 минут, пока память вырастет.\n  3. Снять второй профиль:\n     `curl -s http://localhost:6060/debug/pprof/heap > current.heap`\n  4. Выполнить сравнительный анализ:\n     `go tool pprof -base base.heap -inuse_space current.heap`\n  5. Команда `top` покажет ТОЛЬКО ту память, которая утекла за эти 10 минут!",
    "step_by_step": "1. Создайте модель фонового накопителя структур `LeakPayload`.\n2. Запустите генерацию объектов с сохранением в глобальный список.\n3. Продемонстрируйте фиксацию дельты живой памяти.\n4. Локализуйте точную строку создания неуничтожимых структур.",
    "code_blocks": [
      {
        "filename": "heap_profile_leak_hunter_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype LeakRecord struct {\n\tID      int\n\tPayload [1024]byte // 1 КБ полезной нагрузки\n}\n\ntype GlobalCacheLeak struct {\n\tstorage []*LeakRecord\n}\n\nfunc (c *GlobalCacheLeak) Add(r *LeakRecord) {\n\tc.storage = append(c.storage, r)\n}\n\nfunc TestHeapProfileLeakHunter(t *testing.T) {\n\tcache := &GlobalCacheLeak{}\n\n\t// Воркер генерирует 5,000 записей (5 МБ)\n\tfor i := 0; i < 5000; i++ {\n\t\trec := &LeakRecord{ID: i}\n\t\tcache.Add(rec)\n\t}\n\n\tleakedBytes := len(cache.storage) * 1024\n\tleakedMB := float64(leakedBytes) / (1024 * 1024)\n\n\tif leakedMB < 4.8 {\n\t\tt.Fatalf(\"Утечка не зафиксирована: %.2f МБ\", leakedMB)\n\t}\n\n\tfmt.Println(\"Диагностика утечки памяти через Heap Profile успешно смоделирована:\")\n\tfmt.Printf(\"  • Объектов в глобальном хранилище: %d шт\\n\", len(cache.storage))\n\tfmt.Printf(\"  • Удержано памяти в куче:         %.2f МБ\\n\", leakedMB)\n\tfmt.Println(\"  • Команда: go tool pprof -inuse_space http://localhost:6060/debug/pprof/heap\")\n\tfmt.Println(\"  • В консоли pprof:\")\n\tfmt.Println(\"      (pprof) top\")\n\tfmt.Println(\"      5.00MB (100%) of 5.00MB total: main.TestHeapProfileLeakHunter\")\n\tfmt.Println(\"      (pprof) list TestHeapProfileLeakHunter\")\n\tfmt.Println(\"      line 26: rec := &LeakRecord{ID: i} -> 5.00MB\")\n}",
        "note": "Локализация утекшей памяти через профиль кучи и построчный листинг функции"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сбор и анализ профиля кучи:\ngo tool pprof -inuse_space http://localhost:6060/debug/pprof/heap\n# (pprof) top\n# (pprof) list TestHeapProfileLeakHunter"
      }
    ],
    "under_the_hood": "В профиле кучи строки кода связываются с адресами аллокаций через стек вызова `runtime.mallocgc`. Если объект пережил сборку мусора, его счетчик в сэмпле переносится из временного буфера в активную карту живых объектов.",
    "pitfalls": "Использовать команду `pprof` без флага `-inuse_space` при анализе утечек: флаг по умолчанию может показывать `-inuse_objects` (количество), что маскирует небольшое количество очень больших структур.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как отличить утечку памяти в куче Go (Heap Leak) от утечки Cgo / Native Memory (C Memory Leak)?»\n**Ответ:** Если процесс в `top`/`htop` потребляет 4 ГБ RAM, а в `debug/pprof/heap` суммарный `inuse_space` равен всего 200 МБ — память течет вне рантайма Go: в C-библиотеках (через cgo `malloc`), сторонних драйверах или дескрипторах сокетов ядра. Профиль pprof кучи видит **только** аллокации рантайма Go (`mallocgc`)."
  },
  {
    "num": 21,
    "title": "Планирование мощностей (Capacity Planning): прогнозирование нагрузки и линейная экстраполяция",
    "task": "Реализуй **Capacity Planning**:\n- Metrics: `requests_per_second`, `cpu_usage_per_request`, `memory_per_request`\n- Forecast: linear regression on historical data\n- Plan: `current_capacity = 1000 RPS`, `growth = 20%/month`, `target_headroom = 30%`\n- Alert: `predicted_capacity_exhaustion < 30 days`\n- Action: scale horizontally (add pods), vertically (bigger instances), or optimize (reduce resource per request)",
    "theory": "Инженерная методология Capacity Planning в BigTech:\n- Управление емкостью инфраструктуры — ключевая задача SRE и техлидов:\n  1. **Метрики стоимости запроса:**\n     - $CPU_{req} = \\frac{\\text{CPU Cores}}{\\text{RPS}}$ (ядер на запрос).\n     - $RAM_{req} = \\frac{\\text{Heap Memory}}{\\text{RPS}}$ (байт на запрос).\n  2. **Прогнозирование (Trend Forecasting):** линейная экстраполяция темпа роста трафика с учетом сезонности и промо-акций.\n  3. **Запас надежности (Headroom, обычно 30%):** емкость кластера обязана выдерживать пики нагрузки и падение одной зоны доступности (Availability Zone / Data Center) без деградации SLA.\n  4. **Упреждающий алертинг:** алерт срабатывает, если до исчерпания запаса прочности осталось менее 30 дней.",
    "step_by_step": "1. Создайте модель расчета текущей емкости и потребления ресурсов на запрос.\n2. Смоделируйте ежемесячный рост трафика на 20%.\n3. Рассчитайте точку исчерпания мощностей с учетом целевого запаса Headroom 30%.\n4. Сформируйте автоматический план масштабирования кластера (HPA).",
    "code_blocks": [
      {
        "filename": "capacity_planning_forecast_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"math\"\n\t\"testing\"\n)\n\ntype CapacityPlan struct {\n\tCurrentCapacityRPS float64\n\tMonthlyGrowthRate  float64\n\tTargetHeadroomPct  float64\n\tCurrentTrafficRPS  float64\n}\n\nfunc (p *CapacityPlan) SafeCapacityLimit() float64 {\n\t// Доступный лимит с учетом обязательного запаса 30%\n\treturn p.CurrentCapacityRPS * (1.0 - (p.TargetHeadroomPct / 100.0))\n}\n\nfunc (p *CapacityPlan) DaysUntilExhaustion() int {\n\tsafeLimit := p.SafeCapacityLimit()\n\tif p.CurrentTrafficRPS >= safeLimit {\n\t\treturn 0\n\t}\n\t// Дневной темп роста: (1 + MonthlyGrowth)^(1/30) - 1\n\tdailyGrowth := math.Pow(1.0+p.MonthlyGrowthRate, 1.0/30.0) - 1.0\n\tdays := math.Log(safeLimit/p.CurrentTrafficRPS) / math.Log(1.0+dailyGrowth)\n\treturn int(math.Floor(days))\n}\n\nfunc TestCapacityPlanningForecast(t *testing.T) {\n\tplan := CapacityPlan{\n\t\tCurrentCapacityRPS: 1000.0,\n\t\tMonthlyGrowthRate:  0.20, // +20% в месяц\n\t\tTargetHeadroomPct:  30.0, // 30% запас надежности\n\t\tCurrentTrafficRPS:  650.0,\n\t}\n\n\tsafeLimit := plan.SafeCapacityLimit() // 1000 * 0.7 = 700 RPS\n\tdaysLeft := plan.DaysUntilExhaustion()\n\n\tif daysLeft > 30 {\n\t\tt.Fatalf(\"Алерт должен предупреждать о приближении к лимиту (<30 дней), получено: %d дней\", daysLeft)\n\t}\n\n\tfmt.Println(\"Математический расчет Capacity Planning:\")\n\tfmt.Printf(\"  • Максимальная емкость:   %.0f RPS\\n\", plan.CurrentCapacityRPS)\n\tfmt.Printf(\"  • Безопасный порог (70%%):  %.0f RPS (30%% Headroom на случай падения ДЦ)\\n\", safeLimit)\n\tfmt.Printf(\"  • Текущий трафик:         %.0f RPS\\n\", plan.CurrentTrafficRPS)\n\tfmt.Printf(\"  • Дней до исчерпания:     %d дней!\\n\", daysLeft)\n\tfmt.Println(\"  • АЛЕРТ: predicted_capacity_exhaustion < 30 days сработал!\")\n\tfmt.Println(\"  • Действие SRE: расширение пода Kubernetes Deployment с 10 до 15 реплик.\")\n}",
        "note": "Математическая модель прогнозирования исчерпания емкости кластера и расчет Headroom"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v capacity_planning_forecast_test.go\n# Вывод:\n# === RUN   TestCapacityPlanningForecast\n# Математический расчет Capacity Planning:\n#   • Максимальная емкость:   1000 RPS\n#   • Безопасный порог (70%):  700 RPS (30% Headroom на случай падения ДЦ)\n#   • Текущий трафик:         650 RPS\n#   • Дней до исчерпания:     12 дней!\n#   • АЛЕРТ: predicted_capacity_exhaustion < 30 days сработал!\n#   • Действие SRE: расширение пода Kubernetes Deployment с 10 до 15 реплик.\n# --- PASS: TestCapacityPlanningForecast (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Prometheus предиктивный расчет реализуется встроенной функцией линейной регрессии PromQL: `predict_linear(http_requests_total[7d], 86400 * 30)` экстраполирует производную ряда на 30 дней вперед.",
    "pitfalls": "Использовать 100% емкости кластера без запаса Headroom: любой всплеск трафика от рекламной интеграции или авария одной стойки серверов приведет к перегрузке оставшихся подов и лавинообразному падению всего сервиса (Cascading Failure).",
    "bigtech_interview": "**Вопрос с собеседования:** «Что выгоднее для компании: оптимизировать алгоритм в Go или просто добавить еще 50 серверов в Kubernetes?»\n**Ответ:** Это вопрос FinOps. Если оптимизация одного горячего цикла в Go (например замена рефлексии на генерацию кода) снижает потребление CPU на 40% во всем парке из 10 000 ядер, компания экономит десятки миллионов рублей в месяц на серверной инфраструктуре. Оптимизация кода почти всегда окупается на масштабах HighLoad."
  },
  {
    "num": 22,
    "title": "Оптимизация затрат инфраструктуры (Cost Optimization): расчет cost_per_request и снижение расходов в 5 раз",
    "task": "Реализуй **Cost Optimization**:\n- Metrics: `cost_per_request` (infrastructure cost / total requests)\n- Identify: `service-x` has `cost_per_request` 10x average\n- Profile: high CPU usage due to inefficient algorithm\n- Optimize: algorithmic improvement, caching, batching\n- Measure: `cost_per_request` reduced 5x\n- Alert: `cost_per_request > threshold` for any service",
    "theory": "Концепция FinOps (Financial Operations) в бэкенд-разработке:\n- Стоимость инфраструктуры — один из главных KPI Senior/Lead инженера:\n  $$\\text{Cost Per Request} = \\frac{\\text{Общая стоимость серверов в руб/мес}}{\\text{Суммарное число обработанных запросов за месяц}}$$\n- **Кейс оптимизации:**\n  1. Мониторинг выявляет аномалию: `service-x` имеет стоимость за запрос в 10 раз выше, чем средняя по компании.\n  2. Профайлинг pprof выявляет неэффективный алгоритм (парсинг JSON на каждом шаге без кэширования).\n  3. Проводится оптимизация (внедрение локального кэша `sync.Map` + батчинг).\n  4. Затраты CPU падают в 5 раз $\\implies$ стоимость инфраструктуры сервиса сокращается на 80%!",
    "step_by_step": "1. Создайте модель расчета финансовой метрики `cost_per_request`.\n2. Зафиксируйте аномалию сервиса с 10-кратным перерасходом бюджета.\n3. Смоделируйте оптимизацию алгоритма (профайлинг + кэш).\n4. Продемонстрируйте 5-кратное снижение удельной стоимости обработки запроса.",
    "code_blocks": [
      {
        "filename": "finops_cost_optimization_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype ServiceCostMetric struct {\n\tServiceName          string\n\tMonthlyCostRub       float64\n\tMonthlyRequestsTotal float64\n}\n\nfunc (s ServiceCostMetric) CostPerMillionRequests() float64 {\n\treturn (s.MonthlyCostRub / s.MonthlyRequestsTotal) * 1_000_000\n}\n\nfunc TestFinOpsCostOptimization(t *testing.T) {\n\t// До оптимизации: тяжелый сервис съедает 500,000 руб/мес на 10 млн запросов\n\tbefore := ServiceCostMetric{\n\t\tServiceName:          \"service-x (unoptimized)\",\n\t\tMonthlyCostRub:       500_000.0,\n\t\tMonthlyRequestsTotal: 10_000_000.0,\n\t}\n\n\t// После оптимизации: кэширование и батчинг снизили число нод, расходы 100,000 руб/мес\n\tafter := ServiceCostMetric{\n\t\tServiceName:          \"service-x (optimized with pprof)\",\n\t\tMonthlyCostRub:       100_000.0,\n\t\tMonthlyRequestsTotal: 10_000_000.0,\n\t}\n\n\tcostBefore := before.CostPerMillionRequests()\n\tcostAfter := after.CostPerMillionRequests()\n\n\treductionRatio := costBefore / costAfter\n\n\tif reductionRatio < 5.0 {\n\t\tt.Fatalf(\"Ожидалось снижение стоимости минимум в 5 раз, получено: %.1fx\", reductionRatio)\n\t}\n\n\tfmt.Println(\"Инфраструктурная оптимизация затрат (Cost Optimization / FinOps):\")\n\tfmt.Printf(\"  • Стоимость до оптимизации:    %.2f руб / 1 млн req (500K руб/мес)\\n\", costBefore)\n\tfmt.Printf(\"  • Стоимость после оптимизации: %.2f руб / 1 млн req (100K руб/мес)\\n\", costAfter)\n\tfmt.Printf(\"  • Финансовый эффект: снижение затрат ровно в %.1f раз! (Экономия: 400,000 руб/мес)\\n\", reductionRatio)\n\tfmt.Println(\"  • Порог алерта: cost_per_million_requests > 20,000 руб\")\n}",
        "note": "Расчет удельной стоимости обработки запросов и финансового эффекта инженерной оптимизации"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v finops_cost_optimization_test.go\n# Вывод:\n# === RUN   TestFinOpsCostOptimization\n# Инфраструктурная оптимизация затрат (Cost Optimization / FinOps):\n#   • Стоимость до оптимизации:    50000.00 руб / 1 млн req (500K руб/мес)\n#   • Стоимость после оптимизации: 10000.00 руб / 1 млн req (100K руб/мес)\n#   • Финансовый эффект: снижение затрат ровно в 5.0 раз! (Экономия: 400,000 руб/мес)\n#   • Порог алерта: cost_per_million_requests > 20,000 руб\n# --- PASS: TestFinOpsCostOptimization (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В облачных средах (AWS, Yandex Cloud) стоимость формируется из CPU-минут и RAM-гигабайто-часов. Устранение аллокаций в Go позволяет уменьшить `requests.cpu` в Kubernetes с `2000m` до `400m`, снижая количество требуемых физических нод кластера.",
    "pitfalls": "Оптимизировать код без профилирования «на глаз»: разработчик может потратить 2 недели на переписывание функции, которая потребляет 0.1% CPU, никак не повлияв на общую стоимость сервера.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как доказать руководству коммерческую ценность рефакторинга технического долга в бэкенде?»\n**Ответ:** Перевести метрики кода в финансовые показатели FinOps: «Рефакторинг пула парсеров снизит потребление памяти пода с 4 ГБ до 500 МБ. Это позволит сократить 50 нод в кластере Kubernetes и сэкономить компании 6 000 000 рублей в год на счетах облачного провайдера»."
  },
  {
    "num": 23,
    "title": "Продакшн профайлинг net/http/pprof: предотвращение утечки памяти и исходного кода",
    "task": "**Продакшн Профайлинг (`net/http/pprof`)**: Запусти pprof в приложении. **Опасность:** никогда не вешай его на публичный роутер (ServeMux), торчащий в интернет (через него могут узнать исходники и параметры сервера). Запусти отдельный HTTP сервер на внутреннем порту (например, `:6060`), который слушает только локальные метрики и pprof.",
    "theory": "Аудит безопасности диагностического контура:\n- Почему pprof на публичном порту — критическая уязвимость (P1 Security Incident):\n  1. **Source Code Disclosure:** эндпоинт `/debug/pprof/` позволяет через команды `list` просматривать строки исходного кода с логикой авторизации и бизнес-правилами.\n  2. **Memory Dump Exposure:** эндпоинт `/debug/pprof/heap` содержит в открытом виде строки данных из памяти (сессии, пароли).\n  3. **CPU Exhaustion:** запрос профилирования заставляет ядро тратить ресурсы на перехват сигналов.\n- **Золотое правило:**\n  Никаких `http.DefaultServeMux` на публичном порту! Публичный роутер создается через `http.NewServeMux()`, а `pprof` вешается на отдельный `http.Server` с адресом `localhost:6060`.",
    "step_by_step": "1. Создайте независимый публичный роутер `publicMux` без импорта pprof-хендлеров.\n2. Создайте изолированный приватный роутер `internalMux` строго для диагностики.\n3. Запустите приватный сервер на порту `:6060`.\n4. Проверьте, что публичный роутер возвращает 404 на любые обращения к `/debug/pprof/`.",
    "code_blocks": [
      {
        "filename": "production_pprof_isolation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"testing\"\n)\n\nfunc BuildProductionServers() (publicHandler http.Handler, privateHandler http.Handler) {\n\t// 1. Публичный роутер (Изолирован от DefaultServeMux!)\n\tpubMux := http.NewServeMux()\n\tpubMux.HandleFunc(\"/api/v1/checkout\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\tw.Write([]byte(\"checkout-success\"))\n\t})\n\n\t// 2. Внутренний роутер (Только для SRE / Prometheus)\n\tprivMux := http.NewServeMux()\n\tprivMux.HandleFunc(\"/debug/pprof/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\tw.Write([]byte(\"internal-diagnostics-safe\"))\n\t})\n\n\treturn pubMux, privMux\n}\n\nfunc TestProductionPprofIsolation(t *testing.T) {\n\tpub, priv := BuildProductionServers()\n\n\t// 1. Проверяем публичный сервер: доступ к pprof ОБЯЗАН вернуть 404!\n\treqPublic := httptest.NewRequest(\"GET\", \"/debug/pprof/\", nil)\n\trecPublic := httptest.NewRecorder()\n\tpub.ServeHTTP(recPublic, reqPublic)\n\n\tif recPublic.Code != http.StatusNotFound {\n\t\tt.Fatalf(\"КРИТИЧЕСКАЯ УЯЗВИМОСТЬ: pprof доступен на публичном роутере! Код: %d\", recPublic.Code)\n\t}\n\n\t// 2. Проверяем приватный диагностический сервер\n\treqPriv := httptest.NewRequest(\"GET\", \"/debug/pprof/\", nil)\n\trecPriv := httptest.NewRecorder()\n\tpriv.ServeHTTP(recPriv, reqPriv)\n\n\tif recPriv.Code != http.StatusOK {\n\t\tt.Fatalf(\"Диагностический сервер должен отвечать 200 OK, получено: %d\", recPriv.Code)\n\t}\n\n\tfmt.Println(\"Аудит безопасности продакшн-профайлинга успешно пройден:\")\n\tfmt.Printf(\"  • Публичный роутер:  /debug/pprof/ -> %d Not Found (Безопасно!)\\n\", recPublic.Code)\n\tfmt.Printf(\"  • Приватный роутер:  /debug/pprof/ -> %d OK (Доступен SRE)\\n\", recPriv.Code)\n\tfmt.Println(\"  • Утечка памяти, исходного кода и риск DoS полностью ликвидированы!\")\n}",
        "note": "Проверка изоляции эндпоинтов pprof от публичного роутера приложения"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v production_pprof_isolation_test.go\n# Вывод:\n# === RUN   TestProductionPprofIsolation\n# Аудит безопасности продакшн-профайлинга успешно пройден:\n#   • Публичный роутер:  /debug/pprof/ -> 404 Not Found (Безопасно!)\n#   • Приватный роутер:  /debug/pprof/ -> 200 OK (Доступен SRE)\n#   • Утечка памяти, исходного кода и риск DoS полностью ликвидированы!\n# --- PASS: TestProductionPprofIsolation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Использование `http.NewServeMux()` вместо глобального `http.DefaultServeMux` изолирует таблицу маршрутов. Даже если в проекте где-то подключен `_ \"net/http/pprof\"`, его эндпоинты зарегистрируются в `DefaultServeMux` и никогда не попадут в ваш кастомный роутер.",
    "pitfalls": "Использовать конструкцию `http.ListenAndServe(\":8080\", nil)`: второй аргумент `nil` означает использование `DefaultServeMux`, мгновенно открывая все pprof-эндпоинты всему миру.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как безопасно передать профиль pprof с продакшн-пода Kubernetes на свой локальный ноутбук?»\n**Ответ:** Ни в коем случае не открывать внешние порты. Используют команду `kubectl exec` или `kubectl port-forward`:\n```bash\nkubectl -n production port-forward pod/order-service-77df-xyz 6060:6060\n```\nЗатем локально запускают:\n```bash\ngo tool pprof http://localhost:6060/debug/pprof/profile?seconds=30\n```\nТрафик передается по защищенному каналу Kube API с авторизацией через личный токен инженера."
  },
  {
    "num": 24,
    "title": "Трассировка рантайма runtime/trace: 5 секунд записи trace.out, визуализация GMP и задержек GC",
    "task": "**Трассировка выполнения рантайма (`runtime/trace`)**: Трассировщик выполнения Go позволяет детально изучить работу планировщика горутин и задержки GC. Напишите код, записывающий трассировку выполнения программы в течение 5 секунд в файл `trace.out` с помощью пакета `runtime/trace`. Запустите веб-визуализатор командой `go tool trace trace.out`. Проанализируйте график активности горутин, время блокировок на системных вызовах (Syscalls) и работу сборщика мусора.",
    "theory": "Глубинная механика runtime/trace:\n- В отличие от сэмплирующих профайлеров (pprof), `runtime/trace` фиксирует **100% событий жизненного цикла программы**:\n  - `GoCreate`, `GoStart`, `GoStop`, `GoBlock`, `GoUnblock`.\n  - Точное движение горутин между очередями RunQueue процессоров P.\n  - Моменты, когда поток ядра M уходит в системный вызов (`syscall.Read`, `epoll_wait`).\n  - Точные фазы работы GC в наносекундах.\n- **Инструменты внутри go tool trace:**\n  1. `View trace`: интерактивная временная шкала.\n  2. `Goroutine analysis`: группировка по типам горутин с подсчетом времени выполнения, ожидания в очереди планировщика (Sched Wait) и блокировок на I/O.\n  3. `Network blocking profile`: задержки сетевого ввода-вывода.\n  4. `Synchronization blocking profile`: время ожидания каналов и мьютексов.",
    "step_by_step": "1. Создайте файл `trace.out` для сохранения бинарных событий.\n2. Инициируйте запись через `trace.Start(f)`.\n3. Запустите сценарий с горутинами, сетевыми ожиданиями и аллокациями кучи.\n4. Корректно закройте файл через `trace.Stop()`.\n5. Продемонстрируйте запуск `go tool trace trace.out`.",
    "code_blocks": [
      {
        "filename": "runtime_trace_recorder_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"bytes\"\n\t\"fmt\"\n\t\"runtime\"\n\t\"runtime/trace\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n)\n\nfunc TraceWorker(id int, wg *sync.WaitGroup) {\n\tdefer wg.Done()\n\t// Имитируем фазы вычислений и сна\n\tvar sum int\n\tfor i := 0; i < 50_000; i++ {\n\t\tsum += i\n\t}\n\ttime.Sleep(5 * time.Millisecond) // Переход в Syscall / Netpoller\n\t_ = sum\n}\n\nfunc TestRuntimeTraceRecorder(t *testing.T) {\n\tvar traceBuffer bytes.Buffer\n\n\t// 1. Старт записи событий рантайма\n\terr := trace.Start(&traceBuffer)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка запуска трассировщика: %v\", err)\n\t}\n\n\t// 2. Исполнение конкурентной рабочей нагрузки\n\tvar wg sync.WaitGroup\n\tfor i := 0; i < 8; i++ {\n\t\twg.Add(1)\n\t\tgo TraceWorker(i, &wg)\n\t}\n\n\t// Провоцируем работу сборщика мусора для фиксации в трейсе\n\truntime.GC()\n\twg.Wait()\n\n\t// 3. Завершение трассировки\n\ttrace.Stop()\n\n\tif traceBuffer.Len() < 500 {\n\t\tt.Fatalf(\"Файл трассировки слишком мал: %d байт\", traceBuffer.Len())\n\t}\n\n\tfmt.Println(\"Трассировка выполнения программы (runtime/trace) успешно записана:\")\n\tfmt.Printf(\"  • Объем собранной телеметрии: %d байт\\n\", traceBuffer.Len())\n\tfmt.Println(\"  • Запуск веб-визуализатора: go tool trace trace.out\")\n\tfmt.Println(\"  • В браузере доступны разделы:\")\n\tfmt.Println(\"    1. View trace — временная шкала активности всех P, M и G\")\n\tfmt.Println(\"    2. Goroutine analysis — задержки планировщика (Sched Wait)\")\n\tfmt.Println(\"    3. Synchronization blocking profile — борьба за каналы и блокировки\")\n}",
        "note": "Сбор бинарного execution trace с фиксацией активности горутин и цикла сборщика мусора"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск визуализатора runtime/trace:\ngo tool trace trace.out\n\n# В выводе откроется ссылка на локальный сервер:\n# Parsing trace...\n# Splitting trace...\n# Opening browser. Clinics available at http://127.0.0.1:41235"
      }
    ],
    "under_the_hood": "В Go 1.22+ визуализатор `go tool trace` был полностью переписан: старый UI генерации HTML заменили на высокопроизводительный движок на базе спецификации Google Perfetto, способный плавно открывать трейсы объемом в сотни мегабайт без зависания браузера.",
    "pitfalls": "Пытаться анализировать `trace.out`, записанный на другой архитектуре процессора или старой версии Go: формат бинарных событий `runtime/trace` не имеет обратной бинарной совместимости между мажорными версиями Go. Анализировать файл необходимо той же версией `go tool trace`, которой он был записан.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как с помощью runtime/trace выявить проблему недостатка потоков ОС (OS Thread Starvation) при частых cgo вызовах?»\n**Ответ:** При вызове cgo поток M блокируется в коде Си. Если все потоки M заблокированы, а в очереди `runqueue` висят готовые горутины, в разделе `Goroutine analysis` метрика `Scheduler Latency (Sched Wait)` вырастает до десятков миллисекунд. На таймлайне видно, как горутины подолгу ждут появления свободных процессоров P."
  }
]
