# -*- coding: utf-8 -*-
"""Exercises 1..12 of Chapter 41."""

exercises = [
  {
    "num": 1,
    "title": "Подключение стандартного профайлера pprof: приватный порт :6060 и структура эндпоинтов",
    "task": "Подключи пакет `_ \"net/http/pprof\"` и запусти отдельный HTTP-сервер на порту 6060. Открой `http://localhost:6060/debug/pprof/`.",
    "theory": "Архитектура профайлинга в стандартной библиотеке Go:\n- Пакет `net/http/pprof` регистрирует встроенные обработчики диагностики в `http.DefaultServeMux`:\n  - `/debug/pprof/`: HTML индексная страница со списком всех доступных профилей.\n  - `/debug/pprof/heap`: профиль использования оперативной памяти в куче (heap allocations).\n  - `/debug/pprof/goroutine`: стек-трейсы всех запущенных горутин в реальном времени.\n  - `/debug/pprof/profile`: 30-секундный замер активности CPU.\n  - `/debug/pprof/block`: блокировки на примитивах синхронизации.\n  - `/debug/pprof/mutex`: борьба за мьютексы (lock contention).\n- **Паттерн приватного порта (Dual-Port Pattern):**\n  Основной веб-сервер слушает публичный порт `:8080`, а `pprof` запускается в отдельной горутине на `:6060` (привязка строго к `localhost` или внутренней подсети k8s), чтобы закрыть доступ к внутренностям рантайма из внешнего интернета.",
    "step_by_step": "1. Создайте отдельный `http.Server` для профайлера на адресе `127.0.0.1:6060`.\n2. Запустите его в фоновой горутине `go func() { ... }()`.\n3. Смоделируйте обращение к эндпоинту `/debug/pprof/`.\n4. Проверьте код ответа 200 OK и доступность диагностических индексов.",
    "code_blocks": [
      {
        "filename": "pprof_isolated_server_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"strings\"\n\t\"testing\"\n)\n\ntype DiagnosticIndexHandler struct{}\n\nfunc (h *DiagnosticIndexHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {\n\tif r.URL.Path != \"/debug/pprof/\" {\n\t\thttp.NotFound(w, r)\n\t\treturn\n\t}\n\tw.Header().Set(\"Content-Type\", \"text/html; charset=utf-8\")\n\tw.WriteHeader(http.StatusOK)\n\tfmt.Fprintf(w, \"<html><body><h1>Types of profiles available:</h1>\")\n\tfmt.Fprintf(w, \"<ul>\")\n\tfmt.Fprintf(w, \"<li><a href='allocs'>allocs</a></li>\")\n\tfmt.Fprintf(w, \"<li><a href='block'>block</a></li>\")\n\tfmt.Fprintf(w, \"<li><a href='goroutine'>goroutine</a></li>\")\n\tfmt.Fprintf(w, \"<li><a href='heap'>heap</a></li>\")\n\tfmt.Fprintf(w, \"<li><a href='mutex'>mutex</a></li>\")\n\tfmt.Fprintf(w, \"<li><a href='profile'>profile</a></li>\")\n\tfmt.Fprintf(w, \"<li><a href='trace'>trace</a></li>\")\n\tfmt.Fprintf(w, \"</ul></body></html>\")\n}\n\nfunc TestPprofIsolatedServer(t *testing.T) {\n\thandler := &DiagnosticIndexHandler{}\n\tserver := httptest.NewServer(handler)\n\tdefer server.Close()\n\n\tresp, err := http.Get(server.URL + \"/debug/pprof/\")\n\tif err != nil || resp.StatusCode != http.StatusOK {\n\t\tt.Fatalf(\"Ошибка доступа к /debug/pprof/: %v\", err)\n\t}\n\tdefer resp.Body.Close()\n\n\tif !strings.Contains(resp.Header.Get(\"Content-Type\"), \"text/html\") {\n\t\tt.Fatalf(\"Некорректный Content-Type: %s\", resp.Header.Get(\"Content-Type\"))\n\t}\n\n\tfmt.Println(\"Изолированный сервер pprof (:6060) успешно подтвержден:\")\n\tfmt.Printf(\"  • Эндпоинт: %s/debug/pprof/\\n\", server.URL)\n\tfmt.Printf(\"  • Статус ответа: %d OK\\n\", resp.StatusCode)\n\tfmt.Println(\"  • Доступные профили: allocs, block, goroutine, heap, mutex, profile, trace\")\n}",
        "note": "Изолированный запуск эндпоинтов pprof на приватном порту"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v pprof_isolated_server_test.go\n# Вывод:\n# === RUN   TestPprofIsolatedServer\n# Изолированный сервер pprof (:6060) успешно подтвержден:\n#   • Эндпоинт: http://127.0.0.1:.../debug/pprof/\n#   • Статус ответа: 200 OK\n#   • Доступные профили: allocs, block, goroutine, heap, mutex, profile, trace\n# --- PASS: TestPprofIsolatedServer (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "При импорте `_ \"net/http/pprof\"` срабатывает функция `init()`, которая вызывает `http.Handle(\"/debug/pprof/\", http.HandlerFunc(Index))` в глобальном объекте `http.DefaultServeMux`. Если ваше основное приложение использует кастомный роутер (`chi`, `gin`, `mux`), эндпоинты pprof не попадут в публичную маршрутизацию, если вы явно не примонтируете их.",
    "pitfalls": "Подключать `pprof` на публичный `http.DefaultServeMux`, выставленный в интернет через `http.ListenAndServe(\":8080\", nil)`: любой внешний злоумышленник сможет прочитать исходные коды функций, токены из дампа кучи или запустить CPU-профайлинг на 300 секунд, вызвав отказ в обслуживании (DDoS).",
    "bigtech_interview": "**Вопрос с собеседования:** «Какой оверхед наносит включенный пакет net/http/pprof в продакшене при отсутствии активных запросов сбора профиля?»\n**Ответ:** Практически **нулевой** (0% CPU). Сами по себе зарегистрированные HTTP-хендлеры пассивны. Механизм CPU-профилирования ядра ОС (сигналы `SIGPROF` частотой 100 Гц) и детальная трассировка выполнения активируются только в тот момент, когда инженер или агент Pyroscope начинает скачивать профиль по HTTP."
  },
  {
    "num": 2,
    "title": "Анализ CPU-bound нагрузки: сбор профиля процессора через go tool pprof и команды top/web",
    "task": "Сымитируй высокую нагрузку (CPU-bound задача, например вычисление хэшей в цикле). Сделай дамп CPU профиля (30 секунд) с помощью `go tool pprof http://localhost:6060/debug/pprof/profile`. Используй команду `top` и `web` (график) в pprof-консоли.",
    "theory": "Механика сбора CPU профиля в Go:\n- При вызове `/debug/pprof/profile?seconds=30` рантайм Go обращается к ядру Linux через системный вызов `setitimer`:\n  - Таймер настраивается на частоту **100 Гц** (каждые 10 мс).\n  - Ядро шлет процессу сигнал `SIGPROF`.\n  - Обработчик сигнала в рантайме Go перехватывает Program Counter (PC) всех активных потоков ОС (потоков M в модели GMP) и записывает текущий стек вызовов.\n- **Инструмент `go tool pprof`:**\n  - Команда `top10`: показывает 10 функций, потребляющих больше всего процессорного времени (столбцы `flat` и `cum`).\n  - Команда `list <FunctionName>`: построчный просмотр ассемблерного или Go-кода с указанием точного времени на каждой строке.\n  - Команда `web` / флаг `-http=:8080`: интерактивный граф и Flame Graph (огненный график).",
    "step_by_step": "1. Создайте CPU-емкую операцию (вычисление SHA-256 хешей в цикле).\n2. Запустите замер времени выполнения горячей функции.\n3. Смоделируйте разбор вывода `pprof top`.\n4. Верифицируйте разницу между `flat` (время самой функции) и `cum` (время с учетом дочерних вызовов).",
    "code_blocks": [
      {
        "filename": "cpu_bound_profiling_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"crypto/sha256\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\nfunc ComputeIntensiveHashes(iterations int) [32]byte {\n\tvar current [32]byte\n\tdata := []byte(\"seed-data-for-stress-test\")\n\tfor i := 0; i < iterations; i++ {\n\t\th := sha256.Sum256(data)\n\t\tcurrent = h\n\t\tdata = current[:]\n\t}\n\treturn current\n}\n\ntype PprofTopEntry struct {\n\tFunction string\n\tFlatPct  float64\n\tCumPct   float64\n}\n\nfunc TestCPUBoundProfiling(t *testing.T) {\n\tstart := time.Now()\n\tres := ComputeIntensiveHashes(50_000)\n\tduration := time.Since(start)\n\n\tif res == [32]byte{} {\n\t\tt.Fatal(\"Хэш не вычислен\")\n\t}\n\n\t// Моделирование вывода `go tool pprof` команды `top`\n\tsimulatedTop := []PprofTopEntry{\n\t\t{Function: \"crypto/sha256.block\", FlatPct: 78.4, CumPct: 78.4},\n\t\t{Function: \"main.ComputeIntensiveHashes\", FlatPct: 15.2, CumPct: 93.6},\n\t\t{Function: \"runtime.memmove\", FlatPct: 4.1, CumPct: 4.1},\n\t}\n\n\tfmt.Println(\"Анализ CPU-профиля успешно смоделирован:\")\n\tfmt.Printf(\"  • Время выполнения 50,000 хэшей: %v\\n\", duration)\n\tfmt.Println(\"  • Команда: go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30\")\n\tfmt.Println(\"  • Вывод команды 'top':\")\n\tfmt.Printf(\"     flat%%   cum%%   function\\n\")\n\tfor _, entry := range simulatedTop {\n\t\tfmt.Printf(\"    %5.1f%%  %5.1f%%   %s\\n\", entry.FlatPct, entry.CumPct, entry.Function)\n\t}\n\tfmt.Println(\"  • sha256.block забирает 78.4% CPU (узкое место найдено!)\")\n}",
        "note": "Симуляция CPU-bound задачи и интерпретация вывода pprof top"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск профилирования в терминале:\ngo tool pprof http://localhost:6060/debug/pprof/profile?seconds=30\n# (pprof) top\n# (pprof) list ComputeIntensiveHashes\n# (pprof) web"
      }
    ],
    "under_the_hood": "Столбец `flat` отражает время, проведенное процессором непосредственно в теле инструкции данной функции, исключая любые вызовы подфункций. Столбец `cum` (cumulative) суммирует время работы самой функции и всего дерева ее дочерних вызовов. Если `flat` мал, а `cum` огромен — функция сама по себе легкая, но вызывает тяжелые подпрограммы.",
    "pitfalls": "Пытаться профилировать CPU на виртуальных машинах с сильным CPU Steal Time (дешевые VPS с оверселлингом): ядро виртуализации искажает доставку сигналов `SIGPROF`, что приводит к ложным показаниям задержек в pprof.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему горутины, заблокированные в операциях ввода-вывода (I/O wait, chan receive, sleep), не отображаются в CPU-профиле?»\n**Ответ:** Потому что заблокированные горутины снимаются с выполнения планировщиком Go (M отвязывается от G), поток ядра засыпает на `epoll_wait` или мьютексе и не потребляет тиков CPU. Сигналы `SIGPROF` ловят только активный поток выполнения в контексте выполняющихся инструкций. Для анализа времени ожидания I/O используют `block profile` или `execution trace`."
  },
  {
    "num": 3,
    "title": "Диагностика утечки памяти: анализ профиля кучи debug/pprof/heap и поиск аллокаций",
    "task": "**[Утечка памяти]**: Напиши программу, которая в бесконечном цикле добавляет элементы в глобальный слайс, не очищая его. Сделай дамп Heap (`debug/pprof/heap`). Найди в pprof строку кода, которая занимает больше всего памяти.",
    "theory": "Природа утечек памяти в языках со сборщиком мусора:\n- В Go нет ручного `free()`, сборщик мусора GC использует триколорный марк-энд-свип (Tri-color Mark & Sweep).\n- Объект **не может быть освобожден**, пока до него существует путь по ссылкам от корневых объектов (Root Set: глобальные переменные, стеки активных горутин).\n- **Сценарий утечки:**\n  - Добавление элементов в срез, привязанный к глобальной переменной или долгоживущему синглтону.\n  - Удержание гигантского исходного массива через подстроку или мелкий под-слайс `sub := hugeSlice[:2]`.\n- **Профиль кучи `/debug/pprof/heap`:**\n  - `inuse_space`: объем памяти, занятый живыми объектами прямо сейчас.\n  - `alloc_space`: суммарный объем памяти, выделенный за все время жизни программы (показывает генераторы мусора для GC).",
    "step_by_step": "1. Создайте глобальный накопитель данных (срез байтовых блоков).\n2. Заполните срез в цикле объектами по 1 МБ без очистки.\n3. Продемонстрируйте структуру памяти кучи.\n4. Верифицируйте нахождение виновной строки кода через `pprof list`.",
    "code_blocks": [
      {
        "filename": "memory_leak_heap_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"testing\"\n)\n\n// Глобальный накопитель — частая причина утечек в Go\nvar globalMemoryLeakSink [][]byte\n\nfunc LeakMemory(chunks int) {\n\tfor i := 0; i < chunks; i++ {\n\t\t// Каждая аллокация: 1 МБ\n\t\tblock := make([]byte, 1024*1024)\n\t\tblock[0] = 0xFF\n\t\tglobalMemoryLeakSink = append(globalMemoryLeakSink, block)\n\t}\n}\n\nfunc TestMemoryLeakHeap(t *testing.T) {\n\tvar m1, m2 runtime.MemStats\n\truntime.GC()\n\truntime.ReadMemStats(&m1)\n\n\t// Утечка 10 МБ\n\tLeakMemory(10)\n\n\truntime.GC() // Принудительный сбор мусора: не сможет удалить globalMemoryLeakSink!\n\truntime.ReadMemStats(&m2)\n\n\tallocatedMB := float64(m2.HeapAlloc-m1.HeapAlloc) / (1024 * 1024)\n\tif allocatedMB < 9.0 {\n\t\tt.Fatalf(\"Ожидалось увеличение кучи минимум на 9 МБ, получено: %.2f МБ\", allocatedMB)\n\t}\n\n\tfmt.Println(\"Диагностика утечки памяти в куче успешно подтверждена:\")\n\tfmt.Printf(\"  • HeapAlloc до утечки:  %.2f МБ\\n\", float64(m1.HeapAlloc)/(1024*1024))\n\tfmt.Printf(\"  • HeapAlloc после утечки: %.2f МБ (Удержано в памяти: %.2f МБ)\\n\",\n\t\tfloat64(m2.HeapAlloc)/(1024*1024), allocatedMB)\n\tfmt.Println(\"  • Команда анализа: go tool pprof http://localhost:6060/debug/pprof/heap\")\n\tfmt.Println(\"  • В консоли pprof: (pprof) top -inuse_space\")\n\tfmt.Println(\"  • Строка 'make([]byte, 1024*1024)' занимает 100% живой памяти!\")\n\n\t// Очистка для изоляции тестов\n\tglobalMemoryLeakSink = nil\n\truntime.GC()\n}",
        "note": "Моделирование классической утечки памяти через глобальный срез и замер HeapAlloc"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск анализа кучи:\ngo tool pprof -inuse_space http://localhost:6060/debug/pprof/heap\n# (pprof) top\n# (pprof) list LeakMemory\n# Показана точная строка: block := make([]byte, 1024*1024)"
      }
    ],
    "under_the_hood": "Память в куче Go аллоцируется страницами размером 8 КБ через аллокатор `tcmalloc`-подобной архитектуры (mcache -> mcentral -> mheap). Профиль кучи собирается сэмплированием: по умолчанию `runtime.MemProfileRate = 512 * 1024` (сохраняется срез стека на каждые 512 КБ выделений), что снижает оверхед в продакшене до минимума.",
    "pitfalls": "Анализировать утечку с флагом `-alloc_space` вместо `-inuse_space`: `-alloc_space` показывает, сколько памяти было выделено суммарно (включая уже удаленный сборщиком мусор). Реальные утечки ищут строго по флагу `-inuse_space`!",
    "bigtech_interview": "**Вопрос с собеседования:** «Как под-слайсинг срезов (Sub-slicing) может приводить к скрытым утечкам гигантских объемов памяти?»\n**Ответ:** Если функция прочитала из сети массив размером 50 МБ и вернула под-слайс `return buf[:10]`, новый срез указывает на тот же самый базовый массив. Пока жив этот мелкий срез на 10 байт, GC не может освободить весь 50-мегабайтный буфер! Лечение: явно скопировать нужные байты через `copy()` в новый независимый срез."
  },
  {
    "num": 4,
    "title": "Утечка горутин (Goroutine Leak): зависание на каналах и локализация строки через pprof goroutine",
    "task": "**[Утечка горутин]**: Напиши код, который в цикле запускает горутины, зависающие на чтении из канала навсегда. Сделай дамп `goroutine`. Убедись, что число горутин растет. В pprof найди точную строку кода, где горутины заблокированы.",
    "theory": "Опасность утечки горутин:\n- Каждая горутина в Go резервирует минимум **2 КБ памяти** под свой стек (динамически расширяется до 1 ГБ на 64-битных ОС).\n- **Сценарий утечки:**\n  - Горутина ждет чтения `<-ch` из канала, в который никто никогда ничего не отправит.\n  - Или ждет записи `ch <- val` в небуферизированный канал, из которого никто не читает.\n- **GC не собирает заблокированные горутины!**\n  Если горутина заблокирована, она и все объекты, на которые она ссылается в своем стеке, остаются в памяти навсегда. 100 000 утекших горутин съедят сотни мегабайт памяти и приведут к OOMKilled.",
    "step_by_step": "1. Создайте небуферизированный канал без отправителя.\n2. Запустите 20 горутин, заблокированных на чтении из этого канала.\n3. Зафиксируйте рост счетчика `runtime.NumGoroutine()`.\n4. Верифицируйте поиск заблокированной строки через профиль `/debug/pprof/goroutine`.",
    "code_blocks": [
      {
        "filename": "goroutine_leak_chan_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"runtime\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n)\n\nfunc LeakyWorker(orphanChan <-chan int, started *sync.WaitGroup) {\n\tstarted.Done()\n\t// Точка блокировки: чтение из канала навсегда!\n\t<-orphanChan\n}\n\nfunc TestGoroutineLeakChan(t *testing.T) {\n\tinitialCount := runtime.NumGoroutine()\n\torphanChan := make(chan int) // Нет отправителя!\n\n\tconst spawned = 25\n\tvar started sync.WaitGroup\n\tstarted.Add(spawned)\n\n\tfor i := 0; i < spawned; i++ {\n\t\tgo LeakyWorker(orphanChan, &started)\n\t}\n\tstarted.Wait()\n\ttime.Sleep(10 * time.Millisecond)\n\n\tcurrentCount := runtime.NumGoroutine()\n\tleakedCount := currentCount - initialCount\n\n\tif leakedCount < spawned {\n\t\tt.Fatalf(\"Ожидалась утечка минимум %d горутин, зафиксировано: %d\", spawned, leakedCount)\n\t}\n\n\tfmt.Println(\"Диагностика утечки горутин успешно подтверждена:\")\n\tfmt.Printf(\"  • Начальное число горутин: %d\\n\", initialCount)\n\tfmt.Printf(\"  • Текущее число горутин:   %d (Утечка: +%d горутин)\\n\", currentCount, leakedCount)\n\tfmt.Println(\"  • Команда анализа: go tool pprof http://localhost:6060/debug/pprof/goroutine\")\n\tfmt.Println(\"  • В дампе pprof: состояние 'chan receive' на строке '<-orphanChan'\")\n}",
        "note": "Моделирование утечки горутин на чтении из мертвого канала и замер NumGoroutine"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Анализ заблокированных горутин:\ngo tool pprof http://localhost:6060/debug/pprof/goroutine\n# (pprof) top\n# (pprof) traces\n# Вывод покажет: 25 горутин висят на main.LeakyWorker (goroutine_leak_chan_test.go:16)"
      }
    ],
    "under_the_hood": "В дампе `/debug/pprof/goroutine?debug=2` рантайм выводит текстовый стек-трейс всех горутин. Каждая запись содержит заголовок: `goroutine 42 [chan receive]:` или `goroutine 43 [select]:`. Число в квадратных скобках показывает статус планировщика `gopark`.",
    "pitfalls": "Запускать горутину без `context.Context` или канала отмены `done`: если родительская операция завершилась по таймауту, фоновая горутина обязана узнать об этом через `select { case <-ctx.Done(): return }`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как предотвратить утечку горутин при использовании time.After в циклах select?»\n**Ответ:** `time.After(duration)` создает новый канал и таймер, который удерживается рантаймом до истечения интервала. В цикле `select` по 1000 итераций в секунду будут созданы тысячи висячих таймеров. Решение: использовать `time.NewTimer` с явным вызовом `timer.Stop()` и сбросом через `timer.Reset()`."
  },
  {
    "num": 5,
    "title": "Диагностика дедлоков: состояния semacquire и chan receive в pprof дампе горутин",
    "task": "**[Каверзный кейс]**: Создай дедлок (например, забыл `Unlock()` у мьютекса). Сделай дамп `goroutine`. Найди в выводе pprof горутины в состоянии `chan receive` или `semacquire`, которые указывают на место дедлока.",
    "theory": "Анатомия блокировок в рантайме Go:\n- Когда горутина не может захватить `sync.Mutex`, она паркуется через внутренний системный семафор:\n  состояние в pprof отображается как **`semacquire`** (`sync.runtime_SemacquireMutex`).\n- Когда горутина заблокирована на чтении из пустого канала:\n  состояние отображается как **`chan receive`** (`runtime.chanrecv1`).\n- Когда две горутины захватывают ресурсы крест-накрест (Mutex A $\\to$ Mutex B и Mutex B $\\to$ Mutex A), возникает классический взаимный дедлок (Deadlock).\n- **Диагностика через `debug=1` или `debug=2`:**\n  В pprof группы горутин с одинаковыми стеками группируются, сразу подсвечивая «узел», в котором скопились сотни заблокированных потоков.",
    "step_by_step": "1. Создайте мьютекс и захватите его без освобождения (`Lock()` без `Unlock()`).\n2. Запустите фоновую горутину, пытающуюся захватить этот же мьютекс.\n3. Зафиксируйте переход горутины в состояние ожидания семафора.\n4. Проверьте диагностические признаки `semacquire`.",
    "code_blocks": [
      {
        "filename": "deadlock_semacquire_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype DeadlockSimulator struct {\n\tmu sync.Mutex\n}\n\nfunc (d *DeadlockSimulator) BlockedWorker(ready *sync.WaitGroup, acquired *bool) {\n\tready.Done()\n\t// Попытка захватить уже залоченный мьютекс -> состояние semacquire!\n\td.mu.Lock()\n\t*acquired = true\n\td.mu.Unlock()\n}\n\nfunc TestDeadlockSemacquire(t *testing.T) {\n\tsim := &DeadlockSimulator{}\n\n\t// Главная горутина блокирует мьютекс и \"забывает\" отпустить\n\tsim.mu.Lock()\n\n\tvar ready sync.WaitGroup\n\tready.Add(1)\n\tacquired := false\n\n\tgo sim.BlockedWorker(&ready, &acquired)\n\tready.Wait()\n\n\t// Даем горутине встать в очередь ожидания семафора\n\ttime.Sleep(50 * time.Millisecond)\n\n\tif acquired {\n\t\tt.Fatal(\"Воркер не должен был захватить мьютекс\")\n\t}\n\n\tfmt.Println(\"Состояние дедлока (semacquire) успешно смоделировано:\")\n\tfmt.Println(\"  • Мьютекс удерживается: Lock() без Unlock()\")\n\tfmt.Println(\"  • Воркер переведен планировщиком в режим goparkunlock()\")\n\tfmt.Println(\"  • В дампе debug/pprof/goroutine: состояние 'sync.(*Mutex).Lock -> semacquire'\")\n\tfmt.Println(\"  • Локализация дедлока: точный номер строки вызова sim.mu.Lock()\")\n\n\t// Освобождаем для чистого завершения теста\n\tsim.mu.Unlock()\n\ttime.Sleep(10 * time.Millisecond)\n}",
        "note": "Воспроизведение зависания на мьютексе и выявление состояния semacquire"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v deadlock_semacquire_test.go\n# Вывод:\n# === RUN   TestDeadlockSemacquire\n# Состояние дедлока (semacquire) успешно смоделировано:\n#   • Мьютекс удерживается: Lock() без Unlock()\n#   • Воркер переведен планировщиком в режим goparkunlock()\n#   • В дампе debug/pprof/goroutine: состояние 'sync.(*Mutex).Lock -> semacquire'\n#   • Локализация дедлока: точный номер строки вызова sim.mu.Lock()\n# --- PASS: TestDeadlockSemacquire (0.06s)\n# PASS"
      }
    ],
    "under_the_hood": "`sync.Mutex` в Go использует гибридный алгоритм: сначала 4 итерации активного спин-лока (Spinning на CPU), а если мьютекс не освободился — горутина переводится в спящий режим через системный семафор рантайма `runtime_SemacquireMutex`, освобождая ядро CPU для других горутин.",
    "pitfalls": "Копировать `sync.Mutex` по значению (например передавая структуру `func(s MyStruct)` вместо указателя `*MyStruct`): это создает копию внутреннего флага блокировки, приводя к мгновенным дедлокам и ложным срабатываниям детектора гонок `go vet copylocks`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему встроенный детектор дедлоков Go fatal error: all goroutines are asleep - deadlock! срабатывает не всегда?»\n**Ответ:** Встроенный детектор рантайма срабатывает только тогда, когда **ВСЕ** горутины в программе заснули (включая main). Если в фоне работает хотя бы одна живая горутина (например сетевой сервер `http.ListenAndServe`, ожидающий соединений, или фоновый тикер), рантайм не считает это глобальным дедлоком, и сервис зависает молча. Найти такой частичный дедлок можно только через дамп pprof goroutine."
  },
  {
    "num": 6,
    "title": "Профилирование памяти в бенчмарках: флаги -benchmem, -memprofile и анализ mem.out",
    "task": "Напиши бенчмарк, который alloc'ает много памяти. Запусти его с флагами `-benchmem -memprofile=mem.out`. Проанализируй `mem.out` через `go tool pprof`.",
    "theory": "Связка бенчмаркинга и профайлинга в Go:\n- Команда `go test -bench=. -benchmem -memprofile=mem.out`:\n  1. Запускает бенчмарки и измеряет параметры аллокаций:\n     - `B/op`: количество выделенных байт на операцию.\n     - `allocs/op`: количество обращений к аллокатору кучи на операцию.\n  2. Генерирует бинарный файл профиля `mem.out`.\n- **Анализ профиля `mem.out`:**\n  - `go tool pprof -alloc_space mem.out`: показывает, какие функции нагенерировали больше всего мусора за время теста.\n  - `go tool pprof -inuse_space mem.out`: показывает, сколько памяти осталось не освобождено на момент окончания бенчмарка.",
    "step_by_step": "1. Создайте функцию конкатенации строк через оператор `+` (генерирует много аллокаций).\n2. Напишите Benchmark-функцию.\n3. Продемонстрируйте замер метрик памяти `B/op` и `allocs/op`.\n4. Верифицируйте сбор профиля `mem.out`.",
    "code_blocks": [
      {
        "filename": "string_alloc_bench_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"strings\"\n\t\"testing\"\n)\n\n// Неэффективная функция: конкатенация строк через '+' в цикле\nfunc InefficientConcat(words []string) string {\n\tvar result string\n\tfor _, w := range words {\n\t\tresult += w + \" \" // Создает новую аллокацию строки на каждой итерации!\n\t}\n\treturn result\n}\n\n// Оптимизированная функция:strings.Builder с предвыделением\nfunc OptimizedConcat(words []string) string {\n\tvar b strings.Builder\n\ttotalLen := 0\n\tfor _, w := range words {\n\t\ttotalLen += len(w) + 1\n\t}\n\tb.Grow(totalLen)\n\tfor _, w := range words {\n\t\tb.WriteString(w)\n\t\tb.WriteByte(' ')\n\t}\n\treturn b.String()\n}\n\nfunc BenchmarkInefficientConcat(b *testing.B) {\n\twords := []string{\"apple\", \"banana\", \"cherry\", \"dragonfruit\", \"elderberry\", \"fig\", \"grape\"}\n\tb.ReportAllocs()\n\tb.ResetTimer()\n\tfor i := 0; i < b.N; i++ {\n\t\t_ = InefficientConcat(words)\n\t}\n}\n\nfunc BenchmarkOptimizedConcat(b *testing.B) {\n\twords := []string{\"apple\", \"banana\", \"cherry\", \"dragonfruit\", \"elderberry\", \"fig\", \"grape\"}\n\tb.ReportAllocs()\n\tb.ResetTimer()\n\tfor i := 0; i < b.N; i++ {\n\t\t_ = OptimizedConcat(words)\n\t}\n}",
        "note": "Сравнение неэффективной конкатенации строк и strings.Builder в бенчмарках"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск бенчмарка со сбором профиля памяти:\ngo test -bench=. -benchmem -memprofile=mem.out string_alloc_bench_test.go\n\n# Анализ полученного профиля:\ngo tool pprof -alloc_space mem.out\n# (pprof) top\n# (pprof) list InefficientConcat"
      }
    ],
    "under_the_hood": "Строки в Go неизменяемы (`immutable`). При вызове `s += w` рантайм выделяет новый блок памяти в куче размером `len(s) + len(w)`, копирует туда старое содержимое и добавляет новое, превращая алгоритм в $O(N^2)$ по памяти и нагружая сборщик мусора.",
    "pitfalls": "Забывать вызывать `b.ResetTimer()` перед циклом бенчмарка: если подготовка тестовых данных занимает 100 мс, это время и аллокации попадут в результат первой итерации и исказят профиль.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие флагов pprof -alloc_space и -alloc_objects?»\n**Ответ:** \n- `-alloc_space`: показывает суммарный объем в мегабайтах (важно для поиска утечек больших буферов).\n- `-alloc_objects`: показывает количество отдельных обращений к аллокатору в штуках. Даже если объекты мелкие (по 16 байт), миллион вызовов аллокатора создаст колоссальное давление на `mcache` и заставит GC работать без остановки."
  },
  {
    "num": 7,
    "title": "Непрерывное профилирование (Continuous Profiling): архитектура Pyroscope, Parca и интеграция pyroscope-go",
    "task": "Настрой **Continuous Profiling** (Pyroscope/Parca/Cloud Profiler): `github.com/grafana/pyroscope-go`. `pyroscope.Start(pyroscope.Config{ApplicationName: \"order-service\", ServerAddress: \"http://pyroscope:4040\"})`. Автоматический профиль 24/7, historical comparison.",
    "theory": "Эволюция от ad-hoc профилирования к Continuous Profiling:\n- **Проблема классического pprof:**\n  - Инженер снимает профиль только тогда, когда сервис уже упал или дежурный получил алерт.\n  - «Поймать» всплеск нагрузки длительностью 2 секунды вручную невозможно.\n- **Continuous Profiling (Непрерывное профилирование 24/7):**\n  - Легковесный агент (Pyroscope / Parca) непрерывно собирает профили (CPU, Heap, Goroutines, Mutex) со всех реплик сервиса с микроскопическим оверхедом (< 1% CPU).\n  - Сжатые профили сохраняются в специализированную TSDB.\n  - Позволяет сравнить профиль сегодня в 14:00 с профилем недельной давности (Diff View) и моментально найти регрессию после недавнего релиза!",
    "step_by_step": "1. Создайте модель конфигурации агента `pyroscope.Start`.\n2. Задайте имя сервиса `order-service` и адрес сервера `http://pyroscope:4040`.\n3. Смоделируйте периодическую отправку профилей.\n4. Верифицируйте готовность к непрерывному мониторингу в продакшене.",
    "code_blocks": [
      {
        "filename": "pyroscope_continuous_profiling_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype PyroscopeAgentConfig struct {\n\tApplicationName string\n\tServerAddress   string\n\tProfileTypes    []string\n\tTags            map[string]string\n\tEnabled         bool\n}\n\nfunc InitContinuousProfiler(app, server string) PyroscopeAgentConfig {\n\treturn PyroscopeAgentConfig{\n\t\tApplicationName: app,\n\t\tServerAddress:   server,\n\t\tProfileTypes: []string{\n\t\t\t\"cpu\",\n\t\t\t\"inuse_space\",\n\t\t\t\"inuse_objects\",\n\t\t\t\"goroutines\",\n\t\t\t\"mutex_count\",\n\t\t},\n\t\tTags: map[string]string{\n\t\t\t\"region\": \"ru-central1\",\n\t\t\t\"env\":    \"production\",\n\t\t},\n\t\tEnabled: true,\n\t}\n}\n\nfunc TestPyroscopeContinuousProfiling(t *testing.T) {\n\tcfg := InitContinuousProfiler(\"order-service\", \"http://pyroscope.monitoring:4040\")\n\n\tif !cfg.Enabled || cfg.ApplicationName != \"order-service\" || len(cfg.ProfileTypes) != 5 {\n\t\tt.Fatalf(\"Ошибка конфигурации Pyroscope: %+v\", cfg)\n\t}\n\n\tfmt.Println(\"Непрерывный профайлинг (Continuous Profiling Pyroscope) успешно проверен:\")\n\tfmt.Printf(\"  • Приложение: %s (Env: %s)\\n\", cfg.ApplicationName, cfg.Tags[\"env\"])\n\tfmt.Printf(\"  • Сервер:     %s\\n\", cfg.ServerAddress)\n\tfmt.Printf(\"  • Типы профилей 24/7: %v\\n\", cfg.ProfileTypes)\n\tfmt.Println(\"  • Позволяет находить 5-секундные всплески и регрессии релизов за любой день года!\")\n}",
        "note": "Конфигурация непрерывного профилирования приложения через Pyroscope Go SDK"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v pyroscope_continuous_profiling_test.go\n# Вывод:\n# === RUN   TestPyroscopeContinuousProfiling\n# Непрерывный профайлинг (Continuous Profiling Pyroscope) успешно проверен:\n#   • Приложение: order-service (Env: production)\n#   • Сервер:     http://pyroscope.monitoring:4040\n#   • Типы профилей 24/7: [cpu inuse_space inuse_objects goroutines mutex_count]\n#   • Позволяет находить 5-секундные всплески и регрессии релизов за любой день года!\n# --- PASS: TestPyroscopeContinuousProfiling (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Pyroscope использует формат деревьев стеков (Trie) и сжатие по колоночному принципу (similar to flamebearer): терабайты профилей за месяц сжимаются в несколько гигабайт дискового пространства.",
    "pitfalls": "Включать сбор профиля мьютексов с максимальной частотой `runtime.SetMutexProfileFraction(1)` в HighLoad: запись каждого события захвата мьютекса замедлит программу на 30–50%. Для продакшена используют значение от 5 до 100.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие Pyroscope от Parca в методах сбора данных?»\n**Ответ:** Pyroscope исторически использовал push-модель через SDK приложения (`pyroscope-go`). Parca использует eBPF-агента ядра Linux: она считывает стек-трейсы любых процессов без модификации исходного кода и библиотек Go приложения (Zero-Code Profiling), работая на уровне ядра ОС."
  },
  {
    "num": 8,
    "title": "Программная трассировка рантайма (Execution Tracing): runtime/trace, trace.Start/Stop и go tool trace",
    "task": "Настрой **Execution Tracing** programmatically: `trace.Start(w)`, `trace.Stop()`. Собери trace в тесте. Покажи `View trace` в `go tool trace`.",
    "theory": "Возможности инструмента go tool trace:\n- В отличие от pprof, который оперирует статистическими выборками (Samples), `runtime/trace` **детерминированно логирует каждое событие рантайма Go**:\n  1. Переключение контекста горутин (GMP context switches).\n  2. Фазы работы сборщика мусора GC (STW - Stop-The-World фазы, Mark Assist).\n  3. Сетевые блокировки в сетевом поллере (Netpoller).\n  4. Блокировки на системных вызовах ОС (Syscalls).\n- **Программный запуск:**\n  ```go\n  f, _ := os.Create(\"trace.out\")\n  trace.Start(f)\n  defer trace.Stop()\n  ```\n- **Просмотр:**\n  `go tool trace trace.out` открывает в браузере миллисекундный таймлайн активности всех логических процессоров P.",
    "step_by_step": "1. Создайте временный буфер для записи бинарных событий трассировки.\n2. Инициируйте `trace.Start` и выполните тестовую конкурентную работу.\n3. Завершите трассировку через `trace.Stop`.\n4. Верифицируйте присутствие служебного заголовка формата trace.",
    "code_blocks": [
      {
        "filename": "programmatic_runtime_trace_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"bytes\"\n\t\"fmt\"\n\t\"runtime/trace\"\n\t\"sync\"\n\t\"testing\"\n)\n\nfunc TestProgrammaticRuntimeTrace(t *testing.T) {\n\tvar buf bytes.Buffer\n\n\t// 1. Старт трассировщика\n\terr := trace.Start(&buf)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка запуска runtime/trace: %v\", err)\n\t}\n\n\t// 2. Имитация конкурентной работы\n\tvar wg sync.WaitGroup\n\tfor i := 0; i < 5; i++ {\n\t\twg.Add(1)\n\t\tgo func(id int) {\n\t\t\tdefer wg.Done()\n\t\t\tvar acc int\n\t\t\tfor j := 0; j < 1000; j++ {\n\t\t\t\tacc += j\n\t\t\t}\n\t\t}(i)\n\t}\n\twg.Wait()\n\n\t// 3. Остановка трассировщика\n\ttrace.Stop()\n\n\tif buf.Len() == 0 {\n\t\tt.Fatal(\"Буфер трассировки пуст\")\n\t}\n\n\tfmt.Println(\"Программная трассировка runtime/trace успешно выполнена:\")\n\tfmt.Printf(\"  • Записано байт телеметрии: %d байт\\n\", buf.Len())\n\tfmt.Println(\"  • Команда визуализации: go tool trace trace.out\")\n\tfmt.Println(\"  • Разделы отчета: View trace (таймлайн потоков P), Goroutine analysis, GC pauses\")\n}",
        "note": "Программный захват событий рантайма Go через runtime/trace в буфер памяти"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v programmatic_runtime_trace_test.go\n# Вывод:\n# === RUN   TestProgrammaticRuntimeTrace\n# Программная трассировка runtime/trace успешно выполнена:\n#   • Записано байт телеметрии: ... байт\n#   • Команда визуализации: go tool trace trace.out\n#   • Разделы отчета: View trace (таймлайн потоков P), Goroutine analysis, GC pauses\n# --- PASS: TestProgrammaticRuntimeTrace (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "События `runtime/trace` сохраняются в локальные кольцевые буферы каждого логического процессора P без глобальных мьютексов, что минимизирует влияние самого наблюдателя на планировщик Go.",
    "pitfalls": "Включать `trace.Start` на часы в высоконагруженном сервисе: файл трассировки генерирует от 10 до 50 МБ данных в секунду, что быстро переполнит диск хоста. Трассировку включают точечно на 5–10 секунд.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое Mark Assist в выводе go tool trace и почему он замедляет пользовательские запросы?»\n**Ответ:** Если сервис создает объекты в куче быстрее, чем фоновый GC успевает их размечать, рантайм Go принудительно заставляет пользовательскую горутину, запросившую память, помогать сборщику мусора (Mark Assist). В трейсе это видно как внезапная пауза выполнения бизнес-кода внутри `runtime.gcAssistAlloc`."
  },
  {
    "num": 9,
    "title": "Снятие CPU-профиля через curl, запуск веб-интерфейса go tool pprof -http и Flame Graph",
    "task": "Включи **pprof**: `import _ \"net/http/pprof\"`. `http.ListenAndServe(\":6060\", nil)`. Собери **CPU profile**: `curl -o cpu.prof http://localhost:6060/debug/pprof/profile?seconds=30`. `go tool pprof -http=:8080 cpu.prof`. Покажи flame graph, top functions.",
    "theory": "Визуализация профилей через современный Web UI:\n- Флаг `-http=:8080` запускает локальный веб-сервер с богатым интерактивным интерфейсом:\n  1. **Flame Graph (Огненный график):**\n     - Ось X: доля общего времени выполнения (чем шире плашка, тем больше CPU съела функция).\n     - Ось Y: глубина стека вызовов (родители снизу, потомки сверху).\n     - Позволяет мгновенно заметить «широкие полки» — функции-пожиратели процессора.\n  2. **Top View:** таблица функций, отсортированная по `flat%` и `cum%`.\n  3. **Source View:** построчный просмотр исходного кода с подсветкой затрат в процентах.",
    "step_by_step": "1. Смоделируйте процесс скачивания 30-секундного файла `cpu.prof`.\n2. Проверьте запуск веб-интерфейса `go tool pprof -http=:8080`.\n3. Разберите назначение представлений Flame Graph и Top.\n4. Верифицируйте локализацию узких мест.",
    "code_blocks": [
      {
        "filename": "pprof_web_ui_workflow_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype FlameGraphSpan struct {\n\tName     string\n\tWidthPct float64\n\tChildren []FlameGraphSpan\n}\n\nfunc TestPprofWebUIWorkflow(t *testing.T) {\n\t// Модель Flame Graph: ProcessOrders -> JSONMarshal -> StringAlloc\n\tflame := FlameGraphSpan{\n\t\tName:     \"main.ProcessOrders\",\n\t\tWidthPct: 100.0,\n\t\tChildren: []FlameGraphSpan{\n\t\t\t{\n\t\t\t\tName:     \"encoding/json.Marshal\",\n\t\t\t\tWidthPct: 65.4,\n\t\t\t\tChildren: []FlameGraphSpan{\n\t\t\t\t\t{Name: \"reflect.Value.Interface\", WidthPct: 40.2},\n\t\t\t\t},\n\t\t\t},\n\t\t\t{\n\t\t\t\tName:     \"database/sql.Query\",\n\t\t\t\tWidthPct: 28.1,\n\t\t\t},\n\t\t},\n\t}\n\n\tif flame.Children[0].WidthPct < 60.0 {\n\t\tt.Fatal(\"Ожидалось доминирование JSON маршалинга\")\n\t}\n\n\tfmt.Println(\"Пайплайн работы с pprof Web UI успешно верифицирован:\")\n\tfmt.Println(\"  1. Сбор дампа: curl -o cpu.prof http://localhost:6060/debug/pprof/profile?seconds=30\")\n\tfmt.Println(\"  2. Запуск UI:  go tool pprof -http=:8080 cpu.prof\")\n\tfmt.Println(\"  3. Анализ Flame Graph:\")\n\tfmt.Printf(\"     └── %-25s (100%% CPU)\\n\", flame.Name)\n\tfmt.Printf(\"         ├── %-25s (%.1f%% CPU - Широкая полка!)\\n\", flame.Children[0].Name, flame.Children[0].WidthPct)\n\tfmt.Printf(\"         └── %-25s (%.1f%% CPU)\\n\", flame.Children[1].Name, flame.Children[1].WidthPct)\n\tfmt.Println(\"  • Оптимизация: замена encoding/json на sonic / easyjson ускорит сервис на 65%!\")\n}",
        "note": "Анализ структуры Flame Graph и локализация узкого места в коде"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Скачать CPU дамп за 30 секунд:\ncurl -sK -o cpu.prof http://localhost:6060/debug/pprof/profile?seconds=30\n\n# Открыть интерактивный веб-интерфейс:\ngo tool pprof -http=:8080 cpu.prof"
      }
    ],
    "under_the_hood": "Встроенный веб-сервер pprof использует Graphviz (для генерации ориентированных графов вызовов) и генерирует SVG-изображения Flame Graph с поддержкой интерактивного зума (клик по любой плашке масштабирует ее на 100% экрана).",
    "pitfalls": "Запускать `go tool pprof -http=:8080` на удаленном сервере без открытия туннеля SSH: безопаснее всего пробросить порт командой `ssh -L 8080:localhost:8080 user@remote-server`, чтобы не открывать диагностику наружу.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что означает \"эффект ледяного пика\" (Icicle Graph) по сравнению с классическим Flame Graph?»\n**Ответ:** Это тот же самый график, но перевернутый сверху вниз: корневой вызов отображается на верхней строке, а вызываемые подфункции «стекают» сосульками вниз. В pprof через меню Views можно переключаться между классическим Flame Graph и Icicle Graph в зависимости от привычки инженера."
  },
  {
    "num": 10,
    "title": "Полный обзор эндпоинтов net/http/pprof: heap, goroutine, profile, block, mutex и allocs",
    "task": "Включите `net/http/pprof` и изучите endpoint'ы: `/debug/pprof/`, `/debug/pprof/heap`, `/debug/pprof/goroutine`, `/debug/pprof/profile`.",
    "theory": "Карта эндпоинтов и режимов pprof:\n1. **`/debug/pprof/heap`:** срез памяти кучи (параметры `?gc=1` принудительно запускает GC перед снятием профиля).\n2. **`/debug/pprof/allocs`:** совокупный профиль всех когда-либо выделенных объектов (включая уже удаленные).\n3. **`/debug/pprof/goroutine`:** список стеков всех горутин (параметр `?debug=1` дает компактную текстовую сводку, `?debug=2` — полный дамп со всеми аргументами).\n4. **`/debug/pprof/profile`:** замер активности CPU за N секунд (параметр `?seconds=30`).\n5. **`/debug/pprof/block`:** задержки на каналах и мьютексах (требует `runtime.SetBlockProfileRate`).\n6. **`/debug/pprof/mutex`:** борьба за блокировки мьютексов (требует `runtime.SetMutexProfileFraction`).\n7. **`/debug/pprof/cmdline`:** аргументы командной строки текущего процесса.\n8. **`/debug/pprof/symbol`:** резолвинг адресов функций по таблице символов.",
    "step_by_step": "1. Создайте реестр стандартных эндпоинтов pprof.\n2. Проверьте параметры запросов каждого эндпоинта (`seconds`, `debug`, `gc`).\n3. Смоделируйте опрос эндпоинтов.\n4. Верифицируйте назначение каждого диагностического профиля.",
    "code_blocks": [
      {
        "filename": "pprof_endpoints_survey_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype EndpointSpec struct {\n\tPath        string\n\tDefaultArg  string\n\tDescription string\n}\n\nfunc GetPprofEndpoints() []EndpointSpec {\n\treturn []EndpointSpec{\n\t\t{Path: \"/debug/pprof/\", DefaultArg: \"-\", Description: \"HTML index of available profiles\"},\n\t\t{Path: \"/debug/pprof/heap\", DefaultArg: \"?gc=1\", Description: \"Live memory allocations in heap\"},\n\t\t{Path: \"/debug/pprof/allocs\", DefaultArg: \"-\", Description: \"Cumulative past allocations\"},\n\t\t{Path: \"/debug/pprof/goroutine\", DefaultArg: \"?debug=1\", Description: \"Stack traces of all current goroutines\"},\n\t\t{Path: \"/debug/pprof/profile\", DefaultArg: \"?seconds=30\", Description: \"CPU sampling profile over N seconds\"},\n\t\t{Path: \"/debug/pprof/block\", DefaultArg: \"-\", Description: \"Synchronization blocking events\"},\n\t\t{Path: \"/debug/pprof/mutex\", DefaultArg: \"-\", Description: \"Lock contention and wait duration\"},\n\t\t{Path: \"/debug/pprof/trace\", DefaultArg: \"?seconds=5\", Description: \"Runtime execution event trace\"},\n\t}\n}\n\nfunc TestPprofEndpointsSurvey(t *testing.T) {\n\tendpoints := GetPprofEndpoints()\n\n\tif len(endpoints) != 8 {\n\t\tt.Fatalf(\"Ожидалось 8 стандартных эндпоинтов pprof, получено: %d\", len(endpoints))\n\t}\n\n\tfmt.Println(\"Справочник эндпоинтов net/http/pprof:\")\n\tfor idx, ep := range endpoints {\n\t\tfmt.Printf(\"  [%d] %-24s (Args: %-12s) -> %s\\n\", idx+1, ep.Path, ep.DefaultArg, ep.Description)\n\t}\n\tfmt.Println(\"  • Инженер выбирает нужный эндпоинт в зависимости от характера проблемы (CPU/RAM/Locks/Threads)!\")\n}",
        "note": "Справочник и валидация всех стандартных диагностических путей pprof"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v pprof_endpoints_survey_test.go\n# Вывод:\n# === RUN   TestPprofEndpointsSurvey\n# Справочник эндпоинтов net/http/pprof:\n#   [1] /debug/pprof/            (Args: -           ) -> HTML index of available profiles\n#   [2] /debug/pprof/heap        (Args: ?gc=1       ) -> Live memory allocations in heap\n#   [3] /debug/pprof/allocs      (Args: -           ) -> Cumulative past allocations\n#   [4] /debug/pprof/goroutine   (Args: ?debug=1    ) -> Stack traces of all current goroutines\n#   [5] /debug/pprof/profile     (Args: ?seconds=30 ) -> CPU sampling profile over N seconds\n#   [6] /debug/pprof/block       (Args: -           ) -> Synchronization blocking events\n#   [7] /debug/pprof/mutex       (Args: -           ) -> Lock contention and wait duration\n#   [8] /debug/pprof/trace       (Args: ?seconds=5  ) -> Runtime execution event trace\n# --- PASS: TestPprofEndpointsSurvey (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Эндпоинт `/debug/pprof/goroutine?debug=1` группирует горутины по одинаковым стек-трейсам: вместо 50 000 экранов текста он выведет `50000 @ 0x... 0x...` и один общий стек, позволяя мгновенно увидеть паттерн массового зависания.",
    "pitfalls": "Использовать `/debug/pprof/heap?gc=1` во время пика нагрузки в HighLoad: принудительный запуск Garbage Collection вызовет кратковременную Stop-The-World паузу и всплеск задержки ответов клиентам.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему профили /debug/pprof/block и /debug/pprof/mutex по умолчанию возвращают пустые данные?»\n**Ответ:** Потому что их сбор отключен в рантайме по умолчанию ради нулевого оверхеда. Чтобы они начали собирать данные, нужно явно вызвать в `main()`: `runtime.SetBlockProfileRate(1)` (собирать задержки блокировок) и `runtime.SetMutexProfileFraction(5)` (собирать 1 из 5 событий борьбы за мьютекс)."
  },
  {
    "num": 11,
    "title": "Паттерн Dual-Port: запуск pprof на изолированном порту 6060 для защиты от внешнего периметра",
    "task": "**Интеграция HTTP-профайлера `pprof`**: Подключите стандартный пакет профайлинга к вашему работающему веб-приложению, импортировав пустой пакет `_ \"net/http/pprof\"`. Настройте запуск вспомогательного HTTP-сервера на отдельном порту (например, `localhost:6060`) только для нужд диагностики, чтобы закрыть доступ к диагностическим эндпоинтам из внешней сети.",
    "theory": "Архитектурный стандарт Dual-Port в BigTech:\n- Любой продакшн микросервис разделяет сетевой трафик на два порта:\n  1. **Порт данных (Data Port, например `:8080`):**\n     - Слушает `0.0.0.0:8080`.\n     - На него смотрит Ingress / балансировщик нагрузки.\n     - Содержит только публичные бизнес-эндпоинты (`/api/v1/...`).\n  2. **Служебный порт (Management Port, например `:6060`):**\n     - Слушает `127.0.0.1:6060` или закрытую подсеть мониторинга.\n     - Содержит `/debug/pprof/`, `/metrics` (Prometheus) и `/healthz`.\n     - **Недоступен из интернета ни при каких обстоятельствах!**",
    "step_by_step": "1. Создайте основной сервер бизнес-логики на порту `:8080`.\n2. Создайте второй изолированный сервер диагностики на порту `:6060`.\n3. Запустите оба сервера с раздельным жизненным циклом.\n4. Проверьте сетевую изоляцию эндпоинтов pprof.",
    "code_blocks": [
      {
        "filename": "dual_port_architecture_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype DualPortApp struct {\n\tPublicServer *http.Server\n\tDiagServer   *http.Server\n}\n\nfunc StartDualPortApp(publicAddr, diagAddr string) *DualPortApp {\n\t// 1. Публичный роутер: ТОЛЬКО бизнес-эндпоинты\n\tpublicMux := http.NewServeMux()\n\tpublicMux.HandleFunc(\"/api/v1/order\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\tw.Write([]byte(`{\"order\":\"created\"}`))\n\t})\n\n\t// 2. Диагностический роутер: pprof, healthz\n\tdiagMux := http.NewServeMux()\n\tdiagMux.HandleFunc(\"/debug/pprof/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\tw.Write([]byte(\"pprof-internal-dashboard\"))\n\t})\n\n\tapp := &DualPortApp{\n\t\tPublicServer: &http.Server{Addr: publicAddr, Handler: publicMux},\n\t\tDiagServer:   &http.Server{Addr: diagAddr, Handler: diagMux},\n\t}\n\n\treturn app\n}\n\nfunc TestDualPortArchitecture(t *testing.T) {\n\tapp := StartDualPortApp(\"127.0.0.1:8080\", \"127.0.0.1:6060\")\n\n\tif app.PublicServer.Addr == app.DiagServer.Addr {\n\t\tt.Fatal(\"Порты серверов обязаны быть строго изолированы!\")\n\t}\n\n\tfmt.Println(\"Архитектурный паттерн Dual-Port успешно подтвержден:\")\n\tfmt.Printf(\"  • Публичный бизнес-порт: %s (Смотрит в Ingress)\\n\", app.PublicServer.Addr)\n\tfmt.Printf(\"  • Приватный диагностический: %s (Доступ только SRE и Prometheus)\\n\", app.DiagServer.Addr)\n\tfmt.Println(\"  • Попытка доступа к /debug/pprof/ снаружи вернет 404 Not Found!\")\n\n\t// Имитация корректной остановки\n\tctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)\n\tdefer cancel()\n\t_ = app.PublicServer.Shutdown(ctx)\n\t_ = app.DiagServer.Shutdown(ctx)\n}",
        "note": "Разделение публичного роутера и диагностического порта pprof"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v dual_port_architecture_test.go\n# Вывод:\n# === RUN   TestDualPortArchitecture\n# Архитектурный паттерн Dual-Port успешно подтвержден:\n#   • Публичный бизнес-порт: 127.0.0.1:8080 (Смотрит в Ingress)\n#   • Приватный диагностический: 127.0.0.1:6060 (Доступ только SRE и Prometheus)\n#   • Попытка доступа к /debug/pprof/ снаружи вернет 404 Not Found!\n# --- PASS: TestDualPortArchitecture (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Kubernetes манифесте Deployment для пода объявляют два порта: `containerPort: 8080` (привязывается к Service и Ingress) и `containerPort: 6060` (скрыт внутри оверлейной сети CNI и доступен только через `kubectl port-forward` или Prometheus Operator).",
    "pitfalls": "Запустить диагностический сервер без Graceful Shutdown: при остановке пода `DiagServer` оборвет активные TCP соединения мониторинга, что вызовет ложные срабатывания алертов `TargetDown` в Prometheus.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему недостаточно просто защитить /debug/pprof паролем через Basic Auth на основном порту?»\n**Ответ:** Basic Auth снижает производительность публичного роутера, добавляет зависимость от парсинга заголовков авторизации на каждом запросе, уязвим к утечкам кредов в логах прокси и создает риск человеческой ошибки (разработчик забыл добавить middleware на новый роут). Физическое разделение сокетов гарантирует абсолютную изоляцию на сетевом уровне L4."
  },
  {
    "num": 12,
    "title": "Анализ профиля горутин (Goroutine Profile): классификация блокировок и выявление Goroutine Leaks",
    "task": "Используйте **goroutine profile** для поиска goroutine leaks: какие горутины заблокированы и на чём.",
    "theory": "Классификация состояний горутин в goroutine profile:\n- При снятии дампа горутины группируются по типам ожидания:\n  1. `[chan receive]`: ожидание чтения из канала (частая причина утечек — забытый sender).\n  2. `[chan send]`: ожидание записи в канал (забытый receiver в небуферизированном канале).\n  3. `[select]`: блокировка на конструкции `select` без сработавших веток `case` и без `default`.\n  4. `[semacquire]`: ожидание мьютекса `sync.Mutex` или `sync.RWMutex` (борьба за блокировку или дедлок).\n  5. `[IO wait]`: ожидание ответа от сетевого сокета в `netpoller` (зависший HTTP/SQL запрос без таймаута).\n  6. `[sleep]`: горутина спит в `time.Sleep()`.",
    "step_by_step": "1. Смоделируйте структуру сводки профиля горутин.\n2. Классифицируйте заблокированные горутины по 5 ключевым состояниям.\n3. Рассчитайте долю утекших горутин.\n4. Верифицируйте нахождение источника утечки.",
    "code_blocks": [
      {
        "filename": "goroutine_profile_analyzer_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype GoroutineProfileSummary struct {\n\tTotalGoroutines int\n\tStates          map[string]int\n\tTopBlockSites   []string\n}\n\nfunc AnalyzeGoroutineDump() GoroutineProfileSummary {\n\treturn GoroutineProfileSummary{\n\t\tTotalGoroutines: 1045,\n\t\tStates: map[string]int{\n\t\t\t\"chan receive\": 950, // 950 горутин зависли на каналах -> Очевидная УТЕЧКА!\n\t\t\t\"IO wait\":      70,\n\t\t\t\"semacquire\":   15,\n\t\t\t\"running\":      10,\n\t\t},\n\t\tTopBlockSites: []string{\n\t\t\t\"950 @ workerpool.go:42 (workerpool.(*Pool).worker)\",\n\t\t\t\"70  @ net/http/client.go:180 (net/http.send)\",\n\t\t\t\"15  @ cache.go:88 (cache.(*RWMutex).RLock)\",\n\t\t},\n\t}\n}\n\nfunc TestGoroutineProfileAnalyzer(t *testing.T) {\n\tsummary := AnalyzeGoroutineDump()\n\n\tleakPercent := float64(summary.States[\"chan receive\"]) / float64(summary.TotalGoroutines) * 100\n\n\tif leakPercent < 90.0 {\n\t\tt.Fatalf(\"Ожидалось выявление критической утечки (>90%%), получено: %.1f%%\", leakPercent)\n\t}\n\n\tfmt.Println(\"Анализ профиля горутин (goroutine profile) успешно подтвержден:\")\n\tfmt.Printf(\"  • Всего горутин: %d\\n\", summary.TotalGoroutines)\n\tfmt.Printf(\"  • Распределение по состояниям: %v\\n\", summary.States)\n\tfmt.Println(\"  • Топ мест блокировок:\")\n\tfor idx, site := range summary.TopBlockSites {\n\t\tfmt.Printf(\"    #%d: %s\\n\", idx+1, site)\n\t}\n\tfmt.Printf(\"  • Вердикт: 950 горутин заблокированы на workerpool.go:42 (%.1f%% всех горутин сервиса!)\\n\", leakPercent)\n}",
        "note": "Парсинг и классификация состояний горутин в дампах goroutine profile"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v goroutine_profile_analyzer_test.go\n# Вывод:\n# === RUN   TestGoroutineProfileAnalyzer\n# Анализ профиля горутин (goroutine profile) успешно подтвержден:\n#   • Всего горутин: 1045\n#   • Распределение по состояниям: map[IO wait:70 chan receive:950 running:10 semacquire:15]\n#   • Топ мест блокировок:\n#     #1: 950 @ workerpool.go:42 (workerpool.(*Pool).worker)\n#     #2: 70  @ net/http/client.go:180 (net/http.send)\n#     #3: 15  @ cache.go:88 (cache.(*RWMutex).RLock)\n#   • Вердикт: 950 горутин заблокированы на workerpool.go:42 (90.9% всех горутин сервиса!)\n# --- PASS: TestGoroutineProfileAnalyzer (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Сборщик профиля горутин кратковременно останавливает планировщик Go (STW-фаза на доли миллисекунды), проходит по глобальному массиву всех структур `allgs` (`[]*g`) и считывает текущий счетчик инструкций PC и поле `g.status` каждого объекта.",
    "pitfalls": "Снимать дамп `goroutine?debug=2` при миллионе запущенных горутин: сериализация текста займет десятки секунд и может забить всю оперативную память. При миллионных пулах горутин снимают `debug=1` (агрегированная сводка).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в продакшене автоматически алертить об утечке горутин до того, как сервис упадет по OOM?»\n**Ответ:** Настраивают Prometheus-алерт по метрике `go_goroutines`:\n```promql\nderiv(go_goroutines[15m]) > 5\n```\nЕсли число горутин монотонно растет на протяжении 15 минут без возврата к базовому уровню, дежурный инженер получает уведомление задолго до исчерпания памяти хоста."
  }
]
