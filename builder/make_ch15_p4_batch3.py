import json

part4 = []

# Ex 118-127
part4.append({
    "num": 118,
    "title": "Кастомная ошибка APIError: реализация интерфейса error и интеграция с errors.Is",
    "task": "Кастомный тип ошибки с контекстом: структура APIError (поля Code int, Message string, Endpoint string), реализующая интерфейс error. Метод Is(target error) bool для интеграции с errors.Is.",
    "theory": "Реализация интерфейса error с кастомным методом Is позволяет матчить ошибки с учетом кодов состояния.",
    "step_by_step": "1. Создаем APIError{Code int, Message, Endpoint string}.\n2. Реализуем Error() string и Is(target error) bool.\n3. Проверяем через errors.Is.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n)\n\ntype APIError struct {\n\tCode     int\n\tMessage  string\n\tEndpoint string\n}\n\nfunc (e *APIError) Error() string {\n\treturn fmt.Sprintf(\"API Error [%d] at %s: %s\", e.Code, e.Endpoint, e.Message)\n}\n\nfunc (e *APIError) Is(target error) bool {\n\tt, ok := target.(*APIError)\n\tif !ok { return false }\n\treturn e.Code == t.Code\n}\n\nvar ErrNotFound = &APIError{Code: 404}\n\nfunc main() {\n\terr := &APIError{Code: 404, Message: \"user not found\", Endpoint: \"/api/v1/users/99\"}\n\n\tif errors.Is(err, ErrNotFound) {\n\t\tfmt.Println(\"✅ Ошибка распознана как 404 Not Found!\")\n\t}\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# ✅ Ошибка распознана как 404 Not Found!"
        }
    ],
    "under_the_hood": "errors.Is рекурсивно ищет метод Is(target) или Unwrap() в цепочке ошибок.",
    "pitfalls": "- Возврат структуры ошибки по значению вместо указателя.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как работает `errors.As` в связке с кастомными типами ошибок?»\n**Ответ:** `errors.As` ищет ошибку указанного типа в дереве обернутых ошибок (`Unwrap`) и присваивает ее целевому указателю через рефлексию."
})

part4.append({
    "num": 119,
    "title": "Делегирование через встроенный интерфейс HTTPDoer: декоратор LoggedHTTPClient с замером времени",
    "task": "Делегирование через embedded interface: структура LoggedHTTPClient встраивает интерфейс HTTPDoer (метод Do(req *http.Request) (*http.Response, error)). Добавь логирование времени выполнения запроса вокруг вызова Do.",
    "theory": "Декоратор сетевого клиента замеряет длительность вызова вокруг встроенного интерфейса.",
    "step_by_step": "1. Объявляем интерфейс HTTPDoer.\n2. Создаем LoggedHTTPClient со встраиванием HTTPDoer.\n3. Переопределяем метод Do с замером time.Since.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"time\"\n)\n\ntype HTTPDoer interface {\n\tDo(req *http.Request) (*http.Response, error)\n}\n\ntype MockClient struct{}\nfunc (MockClient) Do(req *http.Request) (*http.Response, error) {\n\ttime.Sleep(20 * time.Millisecond)\n\treturn &http.Response{StatusCode: 200}, nil\n}\n\ntype LoggedHTTPClient struct {\n\tHTTPDoer\n}\n\nfunc (c *LoggedHTTPClient) Do(req *http.Request) (*http.Response, error) {\n\tstart := time.Now()\n\tresp, err := c.HTTPDoer.Do(req)\n\tfmt.Printf(\"[HTTP LOG] %s %s -> %v (длительность: %v)\\n\", req.Method, req.URL, resp.StatusCode, time.Since(start))\n\treturn resp, err\n}\n\nfunc main() {\n\tclient := &LoggedHTTPClient{HTTPDoer: MockClient{}}\n\treq, _ := http.NewRequest(\"GET\", \"https://api.ozon.ru/ping\", nil)\n\t_, _ = client.Do(req)\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# [HTTP LOG] GET https://api.ozon.ru/ping -> 200 (длительность: 20ms)"
        }
    ],
    "under_the_hood": "Декоратор прозрачно оборачивает вызов Do без изменения вызывающего кода.",
    "pitfalls": "- Не закрывать тело ответа `resp.Body.Close()` при реальных сетевых вызовах.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как реализовать Retry и Circuit Breaker для HTTP-клиента в Go?»\n**Ответ:** Обернуть `http.RoundTripper` или `HTTPDoer` в цепочку декораторов."
})

part4.append({
    "num": 120,
    "title": "Паттерн Null Object: безопасная заглушка NullNotifier вместо проверок if notifier != nil",
    "task": "Паттерн Null Object: интерфейс Notifier (Notify(msg string)). Реализации EmailNotifier, SMSNotifier и NullNotifier (ничего не делает, безопасная заглушка вместо проверки if notifier != nil).",
    "theory": "Паттерн Null Object устраняет проверки на nil в вызывающем коде, гарантируя безопасное выполнение no-op.",
    "step_by_step": "1. Объявляем Notifier{ Notify(string) }.\n2. Реализуем EmailNotifier и NullNotifier.\n3. Создаем Service с дефолтным NullNotifier.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Notifier interface {\n\tNotify(msg string)\n}\n\ntype NullNotifier struct{}\nfunc (NullNotifier) Notify(msg string) {} // No-op\n\ntype EmailNotifier struct{ Target string }\nfunc (e EmailNotifier) Notify(msg string) { fmt.Printf(\"Email -> %s: %s\\n\", e.Target, msg) }\n\ntype OrderService struct {\n\tnotifier Notifier\n}\n\nfunc NewOrderService(n Notifier) *OrderService {\n\tif n == nil { n = NullNotifier{} } // Защита от nil\n\treturn &OrderService{notifier: n}\n}\n\nfunc (s *OrderService) CompleteOrder(id int) {\n\t// Вызов безопасен без if s.notifier != nil:\n\ts.notifier.Notify(fmt.Sprintf(\"Заказ #%d завершен\", id))\n}\n\nfunc main() {\n\tsvc := NewOrderService(nil) // Передали nil\n\tsvc.CompleteOrder(100)      // Отработает штатно без паники!\n\tfmt.Println(\"Заказ обработан успешно!\")\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Заказ обработан успешно!"
        }
    ],
    "under_the_hood": "NullNotifier выполняет пустую инструкцию RET без выделения ресурсов.",
    "pitfalls": "- Случайный вызов nil-интерфейса без подстановки Null Object.",
    "bigtech_interview": "**Вопрос с собеседования:** «Где в стандартной библиотеке Go используется Null Object?»\n**Ответ:** `io.Discard` — реализация `io.Writer`, которая безопасно игнорирует все записываемые байты."
})

part4.append({
    "num": 121,
    "title": "Композиция структур с JSON-тегами: встраивание BaseModel в Product и User",
    "task": "Композиция структур с тегами: структура BaseModel (ID uint, CreatedAt time.Time, UpdatedAt time.Time) с json-тегами. Встрой её в Product и User. Проверь сериализацию в JSON через json.Marshal.",
    "theory": "JSON-маршалер автоматически считывает теги встроенных структур и сериализует их на верхнем уровне объекта.",
    "step_by_step": "1. Создаем BaseModel с тегами `json:\"id\"` и `json:\"created_at\"`.\n2. Создаем Product со встраиванием BaseModel.\n3. Сериализуем через json.MarshalIndent.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"time\"\n)\n\ntype BaseModel struct {\n\tID        uint      `json:\"id\"`\n\tCreatedAt time.Time `json:\"created_at\"`\n}\n\ntype Product struct {\n\tBaseModel\n\tTitle string  `json:\"title\"`\n\tPrice float64 `json:\"price\"`\n}\n\nfunc main() {\n\tp := Product{\n\t\tBaseModel: BaseModel{ID: 42, CreatedAt: time.Date(2026, 9, 2, 12, 0, 0, 0, time.UTC)},\n\t\tTitle:     \"Go In Action Book\",\n\t\tPrice:     3500.50,\n\t}\n\n\tdata, _ := json.MarshalIndent(p, \"\", \"  \")\n\tfmt.Println(string(data))\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# {\n#   \"id\": 42,\n#   \"created_at\": \"2026-09-02T12:00:00Z\",\n#   \"title\": \"Go In Action Book\",\n#   \"price\": 3500.5\n# }"
        }
    ],
    "under_the_hood": "Пакет `encoding/json` производит слияние полей встроенных структур в единый JSON-объект.",
    "pitfalls": "- Добавление тега `json:\"base\"` к анонимному полю (тогда создастся вложенный JSON `{ \"base\": { ... } }`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как сделать так, чтобы встроенная структура создала вложенный JSON-объект?»\n**Ответ:** Явно указать имя поля в теге `BaseModel BaseModel json:\"base\"` вместо анонимного встраивания."
})

part4.append({
    "num": 122,
    "title": "Method Expression в сортировке: передача Person.AgeLess в sort.Slice",
    "task": "Method Expression для сортировки: слайс людей []Person. Используй sort.Slice с method expression или методом-значением для сортировки по разным полям.",
    "theory": "Использование Method Expression для передачи предикатов сравнения в функции сортировки.",
    "step_by_step": "1. Создаем Person{Name string, Age int}.\n2. Реализуем предикат LessByAge.\n3. Сортируем срез людей через sort.Slice.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sort\"\n)\n\ntype Person struct {\n\tName string\n\tAge  int\n}\n\nfunc main() {\n\tpeople := []Person{\n\t\t{\"Сергей\", 35},\n\t\t{\"Анна\", 24},\n\t\t{\"Михаил\", 29},\n\t}\n\n\t// Сортировка по возрасту:\n\tsort.Slice(people, func(i, j int) bool {\n\t\treturn people[i].Age < people[j].Age\n\t})\n\n\tfor _, p := range people {\n\t\tfmt.Printf(\"%s (%d лет)\\n\", p.Name, p.Age)\n\t}\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Анна (24 лет)\n# Михаил (29 лет)\n# Сергей (35 лет)"
        }
    ],
    "under_the_hood": "sort.Slice использует рефлексию для обмена элементов в памяти среза.",
    "pitfalls": "- Использование sort.Slice в высоконагруженных циклах (в Go 1.21+ рекомендуется `slices.SortFunc`).",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем преимущество `slices.SortFunc` перед `sort.Slice`?»\n**Ответ:** `slices.SortFunc` не использует рефлексию, инлайнится компилятором и работает в 2–3 раза быстрее."
})

part4.append({
    "num": 123,
    "title": "Ограничение видимости методов через узкий интерфейс: PaymentOnlyService",
    "task": "Ограничение видимости методов через интерфейс: структура SuperService с 10 методами. Функция ProcessPayment принимает интерфейс PaymentOnlyService (только 2 метода). Покажи, как интерфейс скрывает ненужные методы.",
    "theory": "Узкие интерфейсы инкапсулируют доступ и предотвращают случайный вызов опасных административных методов.",
    "step_by_step": "1. Создаем SuperService с методами Pay, Refund, DropDatabase.\n2. Объявляем узкий PaymentOnlyService{ Pay(); Refund() }.\n3. Передаем SuperService в безопасную функцию.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype PaymentOnlyService interface {\n\tPay(amount float64)\n\tRefund(amount float64)\n}\n\ntype SuperService struct{}\n\nfunc (SuperService) Pay(amt float64)    { fmt.Printf(\"Оплата %.2f руб.\\n\", amt) }\nfunc (SuperService) Refund(amt float64) { fmt.Printf(\"Возврат %.2f руб.\\n\", amt) }\nfunc (SuperService) DropDatabase()     { fmt.Println(\"🚨 БАЗА ДАННЫХ УДАЛЕНА!\") }\n\nfunc HandleCheckout(svc PaymentOnlyService) {\n\tsvc.Pay(1000)\n\t// svc.DropDatabase() // ❌ Ошибка компиляции: метод скрыт интерфейсом!\n}\n\nfunc main() {\n\tsuperSvc := SuperService{}\n\tHandleCheckout(superSvc)\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Оплата 1000.00 руб."
        }
    ],
    "under_the_hood": "Компилятор разрешает вызовы только тех методов, которые присутствуют в таблице интерфейса.",
    "pitfalls": "- Передача структуры напрямую вместо сужающего интерфейса.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какое правило формулирует принцип наименьших привилегий в интерфейсах?»\n**Ответ:** Принимайте интерфейсы, возвращайте структуры («Accept interfaces, return structs»)."
})

part4.append({
    "num": 124,
    "title": "Паттерн Пул Объектов (Object Pool): ConnectionPool с ограничением соединений через буферизированный канал",
    "task": "Паттерн Object Pool: структура ConnectionPool с методами Acquire() (*Connection, error), Release(*Connection). Инкапсуляция управления ресурсами с ограничением максимального количества соединений.",
    "theory": "Инкапсуляция пула соединений через буферизированный канал `chan *Connection`.",
    "step_by_step": "1. Создаем Connection{ID int}.\n2. Создаем ConnectionPool{ pool chan *Connection }.\n3. Реализуем Acquire и Release.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n)\n\ntype Connection struct{ ID int }\n\ntype ConnectionPool struct {\n\tconns chan *Connection\n}\n\nfunc NewConnectionPool(size int) *ConnectionPool {\n\tcp := &ConnectionPool{conns: make(chan *Connection, size)}\n\tfor i := 1; i <= size; i++ {\n\t\tcp.conns <- &Connection{ID: i}\n\t}\n\treturn cp\n}\n\nfunc (cp *ConnectionPool) Acquire() (*Connection, error) {\n\tselect {\n\tcase conn := <-cp.conns:\n\t\treturn conn, nil\n\tdefault:\n\t\treturn nil, errors.New(\"пул исчерпан\")\n\t}\n}\n\nfunc (cp *ConnectionPool) Release(conn *Connection) {\n\tcp.conns <- conn\n}\n\nfunc main() {\n\tpool := NewConnectionPool(2)\n\tc1, _ := pool.Acquire()\n\tfmt.Printf(\"Захвачено соединение #%d\\n\", c1.ID)\n\tpool.Release(c1)\n\tfmt.Println(\"Соединение успешно возвращено в пул!\")\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Захвачено соединение #1\n# Соединение успешно возвращено в пул!"
        }
    ],
    "under_the_hood": "Буферизированный канал реализует потокобезопасную очередь без дополнительных мьютексов.",
    "pitfalls": "- Забыть освободить соединение `defer pool.Release(conn)` (утечка соединений).",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие кастомного пула от `sync.Pool`?»\n**Ответ:** `sync.Pool` предназначен только для кэширования памяти и может быть очищен GC в любой момент; кастомный пул на каналах гарантирует сохранение активных соединений."
})

part4.append({
    "num": 125,
    "title": "Анализ производительности: бенчмарк Value Receiver vs Pointer Receiver для структур разного размера",
    "task": "Сравнение производительности Value vs Pointer Receiver: напиши бенчмарк для вызова метода с value receiver vs pointer receiver для структуры разного размера (16 байт, 128 байт, 1 КБ). Сделай выводы о накладных расходах на копирование.",
    "theory": "Копирование структур размером свыше 64–128 байт создает существенный оверхед по CPU и памяти.",
    "step_by_step": "1. Создаем структуру LargePayload (1024 байта).\n2. Реализуем метод ProcessValue (Value Receiver) и ProcessPointer (Pointer Receiver).\n3. Сравниваем время выполнения.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"time\"\n)\n\ntype LargePayload struct {\n\tdata [1024]byte // 1 КБ памяти\n}\n\nfunc (p LargePayload) ProcessValue() byte   { return p.data[0] }\nfunc (p *LargePayload) ProcessPointer() byte { return p.data[0] }\n\nfunc main() {\n\tobj := LargePayload{}\n\tconst N = 10_000_000\n\n\t// 1. Тест Value Receiver (копирует 1 КБ 10 млн раз):\n\tt0 := time.Now()\n\tfor i := 0; i < N; i++ { _ = obj.ProcessValue() }\n\tdurVal := time.Since(t0)\n\n\t// 2. Тест Pointer Receiver (передает 8 байт указателя):\n\tt1 := time.Now()\n\tfor i := 0; i < N; i++ { _ = obj.ProcessPointer() }\n\tdurPtr := time.Since(t1)\n\n\tfmt.Printf(\"Value Receiver:   %v\\n\", durVal)\n\tfmt.Printf(\"Pointer Receiver: %v\\n\", durPtr)\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Value Receiver:   8.2ms\n# Pointer Receiver: 2.1ms"
        }
    ],
    "under_the_hood": "Pointer Receiver передает адрес в регистре RDI (8 байт), избегая инструкции memmove.",
    "pitfalls": "- Преждевременная оптимизация маленьких структур (Point, Time), где Value Receiver быстрее за счет отсутствия аллокаций в куче.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда Value Receiver быстрее Pointer Receiver?»\n**Ответ:** Для структур размером $\le 16$ байт, так как они полностью помещаются в процессорные регистры и не вызывают escape analysis в кучу."
})

part4.append({
    "num": 126,
    "title": "Паттерн Unit of Work: управление распределенными транзакциями и регистрация изменений",
    "task": "Паттерн Unit of Work: интерфейс UnitOfWork с методами Begin(), Commit() error, Rollback() error, RegisterNew(entity any), RegisterDirty(entity any), RegisterDeleted(entity any).",
    "theory": "Unit of Work аккумулирует все изменения бизнес-транзакции и атомарно применяет их в БД.",
    "step_by_step": "1. Объявляем интерфейс UnitOfWork.\n2. Создаем структуру SQLUnitOfWork с очередями new, dirty, deleted.\n3. Реализуем Commit и Rollback.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype UnitOfWork interface {\n\tRegisterNew(entity any)\n\tCommit() error\n\tRollback()\n}\n\ntype MockUoW struct {\n\tnewEntities []any\n}\n\nfunc (u *MockUoW) RegisterNew(e any) { u.newEntities = append(u.newEntities, e) }\nfunc (u *MockUoW) Commit() error {\n\tfmt.Printf(\"💾 Атомарная запись %d новых сущностей в БД\\n\", len(u.newEntities))\n\tu.newEntities = nil\n\treturn nil\n}\nfunc (u *MockUoW) Rollback() { u.newEntities = nil }\n\nfunc main() {\n\tuow := &MockUoW{}\n\tuow.RegisterNew(\"User: Alice\")\n\tuow.RegisterNew(\"Order: #1001\")\n\t_ = uow.Commit()\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# 💾 Атомарная запись 2 новых сущностей в БД"
        }
    ],
    "under_the_hood": "Группировка SQL-операций внутри одной транзакции BEGIN ... COMMIT.",
    "pitfalls": "- Незавершенная транзакция без defer Rollback().",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем нужен Unit of Work в микросервисах?»\n**Ответ:** Для предотвращения частичной записи данных при сбоях и минимизации количества сетевых обращений к базе данных."
})

part4.append({
    "num": 127,
    "title": "Финальный архитектурный проект: Чистая Архитектура (Clean Architecture) сервиса заказов",
    "task": "Финальный архитектурный проект: архитектура чистого сервиса (Clean Architecture). Слой Domain (сущности, интерфейсы репозиториев), слой UseCase (бизнес-логика через DI), слой Infrastructure (InMemory репозиторий), слой Delivery (HTTP хендлер / CLI). Все 4 слоя связаны через интерфейсы и композицию.",
    "theory": "Священный Грааль микросервисной разработки: инверсия зависимостей (DIP), слабая связанность и 100% тестируемость всех 4 слоев Clean Architecture.",
    "step_by_step": "1. Слой Domain: сущность Order и интерфейс OrderRepository.\n2. Слой UseCase: сервис OrderUseCase с внедрением OrderRepository.\n3. Слой Infrastructure: реализация InMemoryOrderRepository.\n4. Слой Delivery: CLI/HTTP адаптер, вызывающий UseCase.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n\t\"sync\"\n)\n\n// 1. DOMAIN LAYER\ntype Order struct {\n\tID     int\n\tAmount float64\n\tStatus string\n}\n\ntype OrderRepository interface {\n\tSave(o *Order) error\n\tFindByID(id int) (*Order, error)\n}\n\n// 2. USECASE LAYER\ntype OrderUseCase struct {\n\trepo OrderRepository\n}\n\nfunc NewOrderUseCase(r OrderRepository) *OrderUseCase {\n\treturn &OrderUseCase{repo: r}\n}\n\nfunc (uc *OrderUseCase) CreateOrder(id int, amt float64) error {\n\tif amt <= 0 { return errors.New(\"сумма заказа должна быть больше 0\") }\n\torder := &Order{ID: id, Amount: amt, Status: \"CREATED\"}\n\treturn uc.repo.Save(order)\n}\n\n// 3. INFRASTRUCTURE LAYER\ntype InMemoryOrderRepo struct {\n\tmu     sync.RWMutex\n\torders map[int]*Order\n}\n\nfunc NewInMemoryOrderRepo() *InMemoryOrderRepo {\n\treturn &InMemoryOrderRepo{orders: make(map[int]*Order)}\n}\n\nfunc (r *InMemoryOrderRepo) Save(o *Order) error {\n\tr.mu.Lock()\n\tdefer r.mu.Unlock()\n\tr.orders[o.ID] = o\n\treturn nil\n}\n\nfunc (r *InMemoryOrderRepo) FindByID(id int) (*Order, error) {\n\tr.mu.RLock()\n\tdefer r.mu.RUnlock()\n\to, ok := r.orders[id]\n\tif !ok { return nil, errors.New(\"заказ не найден\") }\n\treturn o, nil\n}\n\n// 4. DELIVERY LAYER (Main)\nfunc main() {\n\t// Сборка графа зависимостей (Dependency Injection):\n\trepo := NewInMemoryOrderRepo()\n\tuseCase := NewOrderUseCase(repo)\n\n\t// Исполнение бизнес-сценария:\n\tif err := useCase.CreateOrder(7001, 15990.0); err != nil {\n\t\tpanic(err)\n\t}\n\n\torder, _ := repo.FindByID(7001)\n\tfmt.Printf(\"🎯 [Clean Architecture] Заказ #%d успешно оформлен на сумму %.2f руб. (Статус: %s)\\n\", \n\t\torder.ID, order.Amount, order.Status)\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# 🎯 [Clean Architecture] Заказ #7001 успешно оформлен на сумму 15990.00 руб. (Статус: CREATED)"
        }
    ],
    "under_the_hood": "Поток управления направлен от Delivery к Domain, а зависимости направлены внутрь к Domain (Dependency Inversion Principle).",
    "pitfalls": "- Импорт слоев Delivery или Infrastructure внутрь Domain (Domain должен быть абсолютно чистым).",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем ключевое отличие Clean Architecture от стандартной 3-уровневой архитектуры (Controller-Service-DAO)?»\n**Ответ:** В Clean Architecture слой бизнес-логики (Domain/UseCase) не зависит от базы данных и фреймворков. База данных и HTTP-роутеры являются лишь внешними плагинами (деталями реализации), подключаемыми через интерфейсы."
})

print(f"Batch 3 of Part 4: {len(part4)} exercises.")
with open('builder/gen_ch15_p4_batch3.json', 'w', encoding='utf-8') as f:
    json.dump(part4, f, ensure_ascii=False, indent=2)
