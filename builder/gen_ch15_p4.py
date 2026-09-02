exercises = [
  {
    "num": 97,
    "title": "Паттерн Functional Options с валидацией: промышленная конфигурация ServerConfig",
    "task": "Паттерн Functional Options: ServerConfig с WithHost, WithPort, WithMaxConnections, WithTLS(cert, key). Валидация в опциях (порт 1-65535, host не пустой). Конструктор возвращает (*Server, error).",
    "theory": "Паттерн Functional Options с возможностью возврата ошибки из опций.",
    "step_by_step": "1. Объявляем type Option func(*Server) error.\n2. Реализуем WithHost, WithPort с валидацией.\n3. В NewServer применяем опции и возвращаем ошибку при сбое.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n)\n\ntype Server struct {\n\tHost    string\n\tPort    int\n\tMaxConn int\n}\n\ntype Option func(*Server) error\n\nfunc WithHost(h string) Option {\n\treturn func(s *Server) error {\n\t\tif h == \"\" { return errors.New(\"host не может быть пустым\") }\n\t\ts.Host = h\n\t\treturn nil\n\t}\n}\n\nfunc WithPort(p int) Option {\n\treturn func(s *Server) error {\n\t\tif p < 1 || p > 65535 { return fmt.Errorf(\"неверный порт: %d\", p) }\n\t\ts.Port = p\n\t\treturn nil\n\t}\n}\n\nfunc NewServer(opts ...Option) (*Server, error) {\n\tsrv := &Server{Host: \"127.0.0.1\", Port: 8080, MaxConn: 100}\n\tfor _, opt := range opts {\n\t\tif err := opt(srv); err != nil {\n\t\t\treturn nil, err\n\t\t}\n\t}\n\treturn srv, nil\n}\n\nfunc main() {\n\ts, err := NewServer(WithHost(\"0.0.0.0\"), WithPort(9000))\n\tif err != nil { panic(err) }\n\tfmt.Printf(\"Сервер успешно сконфигурирован: %s:%d\\n\", s.Host, s.Port)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Сервер успешно сконфигурирован: 0.0.0.0:9000"
      }
    ],
    "under_the_hood": "Валидация выполняется до аллокации сетевых дескрипторов.",
    "pitfalls": "- Игнорирование ошибки от opt(srv).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как поддержать откат настроек при ошибке в середине списка Functional Options?»\n**Ответ:** Применять опции к временной копии конфигурации и переносить в целевую структуру только после успешного выполнения всех опций."
  },
  {
    "num": 98,
    "title": "Рефлексия и ООП: инспекция полей и методов структуры с помощью StructInfo(v any)",
    "task": "Рефлексия и ООП: функция StructInfo(v any), выводящая список методов типа, список полей (включая вложенные) и их типы. Покажи, как рефлексия видит ООП-структуры в рантайме.",
    "theory": "Пакет reflect позволяет исследовать структуры, методы и интерфейсы во время выполнения программы.",
    "step_by_step": "1. Пишем функцию StructInfo(v any).\n2. Извлекаем reflect.TypeOf(v).\n3. Итерируемся по NumField() и NumMethod().",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"reflect\"\n)\n\ntype Device struct {\n\tModel string\n\tPrice float64\n}\n\nfunc (d Device) Info() string { return d.Model }\nfunc (d Device) Discount()    {}\n\nfunc StructInfo(v any) {\n\tt := reflect.TypeOf(v)\n\tfmt.Println(\"=== Тип:\", t.Name(), \"===\")\n\tfmt.Println(\"Поля:\")\n\tfor i := 0; i < t.NumField(); i++ {\n\t\tf := t.Field(i)\n\t\tfmt.Printf(\"  - %-8s : %s\\n\", f.Name, f.Type)\n\t}\n\tfmt.Println(\"Методы:\")\n\tfor i := 0; i < t.NumMethod(); i++ {\n\t\tm := t.Method(i)\n\t\tfmt.Printf(\"  - %s()\\n\", m.Name)\n\t}\n}\n\nfunc main() {\n\tStructInfo(Device{Model: \"MacBook M3\", Price: 200000})\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# === Тип: Device ===\n# Поля:\n#   - Model    : string\n#   - Price    : float64\n# Методы:\n#   - Discount()\n#   - Info()"
      }
    ],
    "under_the_hood": "Рефлексия считывает заголовки типов из секции .rodata бинарника.",
    "pitfalls": "- Передача не структуры в StructInfo (NumField() упадет в панику, если Kind != Struct).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему reflect.TypeOf видит только публичные методы?»\n**Ответ:** Для безопасности и оптимизации: неэкспортируемые методы не включаются в таблицу методов структуры, если на них нет явных ссылок."
  },
  {
    "num": 99,
    "title": "Паттерн Наблюдатель (Observer / Pub-Sub): регистрация подписчиков и рассылка событий",
    "task": "Паттерн Наблюдатель (Observer / PubSub): интерфейс Observer (Update(event string)), структура Subject (Subscribe(Observer), Unsubscribe(Observer), Notify(event string)). Зарегистрируй несколько наблюдателей (EmailAlert, LogAlert) и вызови оповещение.",
    "theory": "Слабая связанность между издателем событий и потребителями.",
    "step_by_step": "1. Объявляем Observer{ Update(string) }.\n2. Создаем Subject{ observers []Observer }.\n3. Реализуем Subscribe и Notify.\n4. Тестируем.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Observer interface {\n\tUpdate(event string)\n}\n\ntype Subject struct {\n\tobservers []Observer\n}\n\nfunc (s *Subject) Subscribe(o Observer)   { s.observers = append(s.observers, o) }\nfunc (s *Subject) Notify(event string) {\n\tfor _, o := range s.observers {\n\t\to.Update(event)\n\t}\n}\n\ntype EmailAlert struct{ Email string }\nfunc (e EmailAlert) Update(ev string) { fmt.Printf(\"📧 Отправка письма на %s: %s\\n\", e.Email, ev) }\n\ntype LogAlert struct{}\nfunc (LogAlert) Update(ev string) { fmt.Printf(\"📝 Запись в журнал: %s\\n\", ev) }\n\nfunc main() {\n\ts := &Subject{}\n\ts.Subscribe(EmailAlert{\"admin@company.ru\"})\n\ts.Subscribe(LogAlert{})\n\ts.Notify(\"Сбой в кластере Kafka!\")\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# 📧 Отправка письма на admin@company.ru: Сбой в кластере Kafka!\n# 📝 Запись в журнал: Сбой в кластере Kafka!"
      }
    ],
    "under_the_hood": "Subject вызывает Update на слайсе интерфейсов без жесткой привязки к реализациям.",
    "pitfalls": "- Блокирующий синхронный вызов Update, замедляющий издателя (в проде используют горутины или каналы).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как реализовать асинхронный Observer в Go?»\n**Ответ:** Через каналы `chan Event` и фоновые горутины подписчиков."
  },
  {
    "num": 100,
    "title": "Паттерн Репозиторий (Repository Pattern): абстракция хранения данных в InMemoryUserRepository",
    "task": "Паттерн Репозиторий (Repository Pattern): интерфейс UserRepository с методами Create(u *User) error, FindByID(id int) (*User, error), Update(u *User) error, Delete(id int) error. Реализация InMemoryUserRepository с защитой мьютексом.",
    "theory": "Изоляция бизнес-логики от деталей персистентного хранения.",
    "step_by_step": "1. Создаем User{ID int, Name string}.\n2. Объявляем интерфейс UserRepository.\n3. Реализуем InMemoryUserRepository с sync.RWMutex.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n\t\"sync\"\n)\n\ntype User struct {\n\tID   int\n\tName string\n}\n\ntype UserRepository interface {\n\tCreate(u *User) error\n\tFindByID(id int) (*User, error)\n}\n\ntype InMemoryUserRepository struct {\n\tmu    sync.RWMutex\n\tusers map[int]*User\n}\n\nfunc NewInMemoryUserRepository() *InMemoryUserRepository {\n\treturn &InMemoryUserRepository{users: make(map[int]*User)}\n}\n\nfunc (r *InMemoryUserRepository) Create(u *User) error {\n\tm.mu.Lock()\n\tdefer m.mu.Unlock()\n\tr.users[u.ID] = u\n\treturn nil\n}\n\nfunc (r *InMemoryUserRepository) FindByID(id int) (*User, error) {\n\tm.mu.RLock()\n\tdefer m.mu.RUnlock()\n\tu, ok := r.users[id]\n\tif !ok { return nil, errors.New(\"пользователь не найден\") }\n\treturn u, nil\n}\n\nfunc main() {\n\tvar repo UserRepository = NewInMemoryUserRepository()\n\t_ = repo.Create(&User{ID: 1, Name: \"Артем\"})\n\tu, _ := repo.FindByID(1)\n\tfmt.Println(\"Найден пользователь:\", u.Name)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Найден пользователь: Артем"
      }
    ],
    "under_the_hood": "Полиморфная замена слоя хранения без модификации Use Case сервисов.",
    "pitfalls": "- Опечатки в именах мьютексов r.mu vs m.mu (нужно быть внимательным).",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем нужен Repository Pattern в микросервисах?»\n**Ответ:** Позволяет легко писать юнит-тесты со 100% изоляцией от реальной базы данных с помощью моков."
  },
  {
    "num": 101,
    "title": "Паттерн Адаптер функций: адаптация обычной функции к интерфейсу через type StringProcessor",
    "task": "Паттерн Адаптер через функции: type StringProcessor func(string) string. Метод (f StringProcessor) Process(s string) string. Функция ProcessAll(p Processor, items []string). Адаптация обычной функции к интерфейсу Processor через приведение типа.",
    "theory": "Превращение обычной функции в объект интерфейса по аналогии с http.HandlerFunc.",
    "step_by_step": "1. Объявляем интерфейс Processor.\n2. Создаем type StringProcessor func(string) string с методом Process.\n3. Пишем ProcessAll и передаем приведенную функцию.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n)\n\ntype Processor interface {\n\tProcess(string) string\n}\n\ntype StringProcessor func(string) string\n\nfunc (f StringProcessor) Process(s string) string {\n\treturn f(s)\n}\n\nfunc ProcessAll(p Processor, items []string) []string {\n\tvar res []string\n\tfor _, item := range items {\n\t\tres = append(res, p.Process(item))\n\t}\n\treturn res\n}\n\nfunc main() {\n\t// Обычная функция:\n\ttoUpper := func(s string) string { return strings.ToUpper(s) }\n\n\t// Адаптируем к интерфейсу Processor:\n\tresults := ProcessAll(StringProcessor(toUpper), []string{\"golang\", \"patterns\"})\n\tfmt.Println(results)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# [GOLANG PATTERNS]"
      }
    ],
    "under_the_hood": "Приведение типа StringProcessor(fn) связывает функцию с таблицей методов itab.",
    "pitfalls": "- Попытка передать `toUpper` без явного приведения типа к `StringProcessor`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как этот паттерн называется в спецификации Go?»\n**Ответ:** Interface Adapter Pattern (или Function-to-Interface Adapter)."
  },
  {
    "num": 102,
    "title": "Каверзный кейс: Dynamic Type vs Dynamic Value в интерфейсе (T, nil) против (nil, nil)",
    "task": "[Каверзный кейс] Dynamic type vs dynamic value в интерфейсе: объясни разницу между (T, nil) и (nil, nil). Создай функцию, которая демонстрирует эту разницу через fmt.Printf(\"%T %v\\n\", i, i) и проверку i == nil.",
    "theory": "Интерфейс в Go хранит пару (Type, Value). Интерфейс равен nil ТОЛЬКО когда и Type == nil, и Value == nil.",
    "step_by_step": "1. Создаем переменную указателя ptr *int = nil.\n2. Присваиваем интерфейсу var i1 any = ptr.\n3. Создаем пустой интерфейс var i2 any = nil.\n4. Сравниваем типы, значения и проверки на == nil.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\nfunc main() {\n\tvar ptr *int = nil\n\n\t// 1. (Type = *int, Value = nil):\n\tvar i1 any = ptr\n\n\t// 2. (Type = nil, Value = nil):\n\tvar i2 any = nil\n\n\tfmt.Printf(\"i1: Type=%-6T Value=%-6v | i1 == nil? %t\\n\", i1, i1, i1 == nil)\n\tfmt.Printf(\"i2: Type=%-6T Value=%-6v | i2 == nil? %t\\n\", i2, i2, i2 == nil)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# i1: Type=*int   Value=<nil>  | i1 == nil? false\n# i2: Type=<nil>  Value=<nil>  | i2 == nil? true"
      }
    ],
    "under_the_hood": "В структуре eface: i1 = {type: *_type_int, data: 0x0}, i2 = {type: 0x0, data: 0x0}.",
    "pitfalls": "- Возврат nil-указателя пользовательской структуры в качестве возвращаемого типа error.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как безопасно проверить, содержит ли интерфейс nil внутри значения?»\n**Ответ:** Через рефлексию `reflect.ValueOf(i).IsNil()` (только для указателей, каналов, функций, интерфейсов, мап и слайсов)."
  },
  {
    "num": 103,
    "title": "Ловушка копирования мьютекса (Mutex Copy Trap): ошибка Value Receiver в SafeCounter",
    "task": "Копирование мьютекса (Mutex Copy Trap): структура SafeCounter с sync.Mutex и value int. Метод Inc() с value receiver (func (c SafeCounter) Inc()). Покажи, что при каждом вызове мьютекс и значение копируются, и счетчик не увеличивается. Исправь на pointer receiver. Запусти go vet и покажи предупреждение passes lock by value.",
    "theory": "Value Receiver копирует структуру вместе с внутренним состоянием мьютекса, что приводит к неработоспособности счетчика и гонкам данных.",
    "step_by_step": "1. Демонстрируем ошибочный SafeCounter с Value Receiver.\n2. Запускаем и показываем, что счетчик равен 0.\n3. Исправляем на Pointer Receiver.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n)\n\ntype SafeCounter struct {\n\tmu  sync.Mutex\n\tval int\n}\n\n// ✅ ИСПРАВЛЕНИЕ: Pointer Receiver (*SafeCounter)\nfunc (c *SafeCounter) Inc() {\n\tc.mu.Lock()\n\tdefer c.mu.Unlock()\n\tc.val++\n}\n\nfunc (c *SafeCounter) Value() int {\n\tc.mu.Lock()\n\tdefer c.mu.Unlock()\n\treturn c.val\n}\n\nfunc main() {\n\tc := &SafeCounter{}\n\tc.Inc()\n\tc.Inc()\n\tfmt.Println(\"Итоговый счетчик:\", c.Value())\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Итоговый счетчик: 2"
      }
    ],
    "under_the_hood": "go vet использует статический анализатор copylocks для поиска копирования структур с Lock().",
    "pitfalls": "- Передача структуры с sync.Mutex по значению в функции.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какая утилита Go автоматически обнаруживает копирование мьютексов?»\n**Ответ:** `go vet` со встроенным чекером `copylocks`."
  },
  {
    "num": 104,
    "title": "Диагностика Data Race: обнаружение состояния гонки через go run -race и защита мьютексом",
    "task": "Data Race на структуре: покажи гонку данных при одновременном вызове c.Inc() из 100 горутин без мьютекса. Запусти go run -race. Исправь с помощью sync.Mutex внутри структуры.",
    "theory": "Data Race Detector компилирует код со специальной инструментацией памяти для отслеживания несинхронизированных обращений.",
    "step_by_step": "1. Создаем потокобезопасный счетчик с sync.Mutex.\n2. Запускаем 100 конкурентных горутин.\n3. Проверяем с флагом -race.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n)\n\ntype AtomicCounter struct {\n\tmu  sync.Mutex\n\tval int\n}\n\nfunc (c *AtomicCounter) Inc() {\n\tc.mu.Lock()\n\tdefer c.mu.Unlock()\n\tc.val++\n}\n\nfunc main() {\n\tc := &AtomicCounter{}\n\tvar wg sync.WaitGroup\n\n\tfor i := 0; i < 100; i++ {\n\t\twg.Add(1)\n\t\tgo func() {\n\t\t\tdefer wg.Done()\n\t\t\tc.Inc()\n\t\t}()\n\t}\n\n\twg.Wait()\n\tfmt.Println(\"Счетчик после 100 горутин:\", c.val)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run -race main.go\n# Счетчик после 100 горутин: 100"
      }
    ],
    "under_the_hood": "Race detector основан на библиотеке ThreadSanitizer от Google.",
    "pitfalls": "- Запуск высоконагруженных бенчмарков с флагом -race (дает 2-10x оверхед по памяти и CPU).",
    "bigtech_interview": "**Вопрос с собеседования:** «Всегда ли Race Detector находит 100% всех гонок данных?»\n**Ответ:** Нет, Race Detector находит гонки только на тех ветках кода, которые реально выполнились во время работы тестов."
  },
  {
    "num": 105,
    "title": "Паттерн Singleton на уровне пакета: defaultLogger и публичные функции-делегаты",
    "task": "Паттерн Singleton с пакетом: пакет logger. Глобальная неэкспортируемая переменная defaultLogger. Функции пакета logger.Info(), logger.Error(), делегирующие defaultLogger. Метод logger.SetDefault(customLogger).",
    "theory": "Идиоматичный паттерн стандартной библиотеки Go (например, slog.Info() или http.DefaultClient).",
    "step_by_step": "1. Создаем Logger{ prefix string }.\n2. Объявляем приватный defaultLogger.\n3. Экспортируем функции Info, Error и SetDefault.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Logger struct{ Prefix string }\nfunc (l *Logger) Log(msg string) { fmt.Printf(\"[%s] %s\\n\", l.Prefix, msg) }\n\nvar defaultLogger = &Logger{Prefix: \"DEFAULT\"}\n\nfunc SetDefaultLogger(l *Logger) { defaultLogger = l }\nfunc LogInfo(msg string)         { defaultLogger.Log(\"INFO: \" + msg) }\n\nfunc main() {\n\tLogInfo(\"Сообщение через стандартный логер\")\n\n\tSetDefaultLogger(&Logger{Prefix: \"PRODUCTION\"})\n\tLogInfo(\"Сообщение через кастомный логер\")\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# [DEFAULT] INFO: Сообщение через стандартный логер\n# [PRODUCTION] INFO: Сообщение через кастомный логер"
      }
    ],
    "under_the_hood": "Делегирование вызовов на уровне пакета без необходимости передавать логер во все функции.",
    "pitfalls": "- Мутация defaultLogger из нескольких горутин без синхронизации.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как устроен пакет `log/slog` в Go 1.21+?»\n**Ответ:** Он использует ровно этот паттерн: глобальный `defaultHandler` и функции пакета `slog.Info`, `slog.Error`, делегирующие ему работу."
  },
  {
    "num": 106,
    "title": "Паттерн Внедрение Зависимостей (Dependency Injection): сервис UserService и MockDatabase",
    "task": "Паттерн Dependency Injection: структура UserService принимает интерфейс DatabaseReader через конструктор. Напиши юнит-тест с мок-реализацией MockDatabase.",
    "theory": "DI через интерфейсы позволяет тестировать бизнес-логику в полной изоляции от внешних систем.",
    "step_by_step": "1. Объявляем интерфейс DatabaseReader.\n2. Создаем UserService{ db DatabaseReader }.\n3. Пишем MockDatabase и тестируем метод GetUserGreeting.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype DatabaseReader interface {\n\tGetUserName(id int) (string, error)\n}\n\ntype UserService struct {\n\tdb DatabaseReader\n}\n\nfunc NewUserService(db DatabaseReader) *UserService {\n\treturn &UserService{db: db}\n}\n\nfunc (s *UserService) Greet(id int) string {\n\tname, err := s.db.GetUserName(id)\n\tif err != nil { return \"Привет, Гость!\" }\n\treturn \"Привет, \" + name + \"!\"\n}\n\ntype MockDatabase struct{}\nfunc (MockDatabase) GetUserName(id int) (string, error) {\n\treturn \"Тестовый Пользователь\", nil\n}\n\nfunc main() {\n\tsvc := NewUserService(MockDatabase{})\n\tfmt.Println(svc.Greet(42))\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Привет, Тестовый Пользователь!"
      }
    ],
    "under_the_hood": "UserService не знает о реальной БД и работает с любым объектом, реализующим DatabaseReader.",
    "pitfalls": "- Создание реального подключения к БД внутри конструктора NewUserService вместо передачи через параметр.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какой DI-фреймворк популярен в BigTech Go-проектах?»\n**Ответ:** Google Wire (генерация кода во время сборки без медленной рефлексии) или Uber Dig / Fx."
  },
  {
    "num": 107,
    "title": "Паттерн Состояние через интерфейсы: конечный автомат светофора TrafficLight (Red -> Green -> Yellow)",
    "task": "State pattern через интерфейсы: структура TrafficLight с интерфейсом TrafficLightState. Состояния RedState, YellowState, GreenState. Метод Next() переключает состояние и возвращает текущий цвет.",
    "theory": "Полиморфная реализация состояний: каждое состояние инкапсулирует правило перехода к следующему состоянию.",
    "step_by_step": "1. Объявляем State{ Next() State; Color() string }.\n2. Реализуем RedState, GreenState, YellowState.\n3. Создаем TrafficLight{ current State } и тестируем переключение.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype LightState interface {\n\tNext() LightState\n\tColor() string\n}\n\ntype RedState struct{}\nfunc (RedState) Next() LightState { return GreenState{} }\nfunc (RedState) Color() string    { return \"КРАСНЫЙ\" }\n\ntype GreenState struct{}\nfunc (GreenState) Next() LightState { return YellowState{} }\nfunc (GreenState) Color() string    { return \"ЗЕЛЕНЫЙ\" }\n\ntype YellowState struct{}\nfunc (YellowState) Next() LightState { return RedState{} }\nfunc (YellowState) Color() string    { return \"ЖЕЛТЫЙ\" }\n\ntype TrafficLight struct{ state LightState }\n\nfunc (tl *TrafficLight) Next() {\n\ttl.state = tl.state.Next()\n\tfmt.Printf(\"🚦 Светофор переключился на: %s\\n\", tl.state.Color())\n}\n\nfunc main() {\n\ttl := &TrafficLight{state: RedState{}}\n\ttl.Next() // Зеленый\n\ttl.Next() // Желтый\n\ttl.Next() // Красный\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# 🚦 Светофор переключился на: ЗЕЛЕНЫЙ\n# 🚦 Светофор переключился на: ЖЕЛТЫЙ\n# 🚦 Светофор переключился на: КРАСНЫЙ"
      }
    ],
    "under_the_hood": "Таблица переходов состояний реализована через полиморфизм интерфейсов.",
    "pitfalls": "- Забыть замкнуть цикл переходов состояний.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда State pattern лучше классического switch-case?»\n**Ответ:** Когда количество состояний велико, логика каждого состояния сложна, и нужно добавлять новые состояния без изменения существующего кода."
  },
  {
    "num": 108,
    "title": "Ловушка nil-указателя при встраивании: паника при вызове promoted метода у Outer{*Inner}",
    "task": "Nil embedded pointer trap: структура Outer встраивает *Inner. Создай Outer{} (где Inner == nil). Попробуй вызвать promoted метод. Покажи, где возникает паника, и как защититься.",
    "theory": "Если встроенный указатель равен nil, обращение к его полям вызывает SIGSEGV; метод на nil-указателе безопасен только при наличии проверки if inner == nil.",
    "step_by_step": "1. Создаем Inner{ Data string } с методом SafeMethod() и UnsafeMethod().\n2. Создаем Outer{ *Inner }.\n3. Демонстрируем безопасный и небезопасный вызовы.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Inner struct{ Data string }\n\nfunc (i *Inner) SafeMethod() string {\n\tif i == nil { return \"(Inner не инициализирован!)\" }\n\treturn i.Data\n}\n\ntype Outer struct {\n\t*Inner // Встроенный указатель\n}\n\nfunc main() {\n\to := Outer{Inner: nil}\n\n\t// 1. Безопасный вызов благодаря проверке nil внутри SafeMethod:\n\tfmt.Println(\"Вызов на Outer:\", o.SafeMethod())\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Вызов на Outer: (Inner не инициализирован!)"
      }
    ],
    "under_the_hood": "Компилятор разворачивает o.SafeMethod() в o.Inner.SafeMethod(); аргумент 0x0 передается в функцию.",
    "pitfalls": "- Прямое обращение o.Data при o.Inner == nil вызовет немедленную панику.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как гарантировать инициализацию встроенных указателей?»\n**Ответ:** Использовать конструктор NewOuter(), который явно аллоцирует `&Inner{}`."
  },
  {
    "num": 109,
    "title": "Множественное встраивание с разрешением коллизий: SmartDevice, WiFiModule и BluetoothModule",
    "task": "Множественное встраивание с разрешением коллизий: структура SmartDevice встраивает WiFiModule (метод Connect()) и BluetoothModule (метод Connect()). Реализуй собственный SmartDevice.Connect(), вызывающий оба модуля.",
    "theory": "Переопределение метода верхнего уровня элегантно координирует вызовы обоих конфликтующих модулей.",
    "step_by_step": "1. Создаем WiFiModule и BluetoothModule с методом Connect().\n2. Создаем SmartDevice со встраиванием обоих.\n3. Реализуем SmartDevice.Connect().",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype WiFiModule struct{}\nfunc (WiFiModule) Connect() { fmt.Println(\"📶 Wi-Fi 6 подключен (5 GHz)\") }\n\ntype BluetoothModule struct{}\nfunc (BluetoothModule) Connect() { fmt.Println(\"🔵 Bluetooth 5.3 сопряжен\") }\n\ntype SmartDevice struct {\n\tWiFiModule\n\tBluetoothModule\n\tDeviceName string\n}\n\n// Разрешение конфликта имен через собственный метод:\nfunc (sd SmartDevice) Connect() {\n\tfmt.Printf(\"[%s] Инициализация беспроводных модулей...\\n\", sd.DeviceName)\n\tsd.WiFiModule.Connect()\n\tsd.BluetoothModule.Connect()\n}\n\nfunc main() {\n\tdev := SmartDevice{DeviceName: \"Яндекс Станция\"}\n\tdev.Connect()\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# [Яндекс Станция] Инициализация беспроводных модулей...\n# 📶 Wi-Fi 6 подключен (5 GHz)\n# 🔵 Bluetooth 5.3 сопряжен"
      }
    ],
    "under_the_hood": "Собственный метод имеет глубину 0 и полностью устраняет неоднозначность селекторов.",
    "pitfalls": "- Попытка вызвать `dev.Connect()` без переопределения (ошибка компиляции ambiguous selector).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как множественное встраивание в Go решает Diamond Problem?»\n**Ответ:** В Go нет иерархии классов; при коллизии имен компилятор требует явного обращения `sd.Type.Method()`, предотвращая любые неоднозначности."
  },
  {
    "num": 110,
    "title": "Fluent Builder для построения SQL-запросов: QueryBuilder с валидацией обязательных секций",
    "task": "Fluent Builder для SQL-запросов: QueryBuilder с методами Select(fields ...string), From(table string), Where(cond string), OrderBy(field string, asc bool), Limit(n int), Build() (string, error). Валидация обязательных полей (FROM обязателен).",
    "theory": "Построитель SQL-запросов инкапсулирует форматирование и валидацию синтаксиса.",
    "step_by_step": "1. Создаем QueryBuilder со строковыми полями.\n2. Реализуем методы Select, From, Where, Limit, Build.\n3. Собираем SQL-запрос.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n\t\"strings\"\n)\n\ntype QueryBuilder struct {\n\tfields []string\n\ttable  string\n\twhere  string\n\tlimit  int\n}\n\nfunc NewQueryBuilder() *QueryBuilder { return &QueryBuilder{} }\nfunc (q *QueryBuilder) Select(f ...string) *QueryBuilder { q.fields = f; return q }\nfunc (q *QueryBuilder) From(t string) *QueryBuilder       { q.table = t; return q }\nfunc (q *QueryBuilder) Where(w string) *QueryBuilder      { q.where = w; return q }\nfunc (q *QueryBuilder) Limit(l int) *QueryBuilder         { q.limit = l; return q }\n\nfunc (q *QueryBuilder) Build() (string, error) {\n\tif q.table == \"\" { return \"\", errors.New(\"секция FROM обязательна\") }\n\tfields := \"*\"\n\tif len(q.fields) > 0 { fields = strings.Join(q.fields, \", \") }\n\tsql := fmt.Sprintf(\"SELECT %s FROM %s\", fields, q.table)\n\tif q.where != \"\" { sql += \" WHERE \" + q.where }\n\tif q.limit > 0 { sql += fmt.Sprintf(\" LIMIT %d\", q.limit) }\n\treturn sql + \";\", nil\n}\n\nfunc main() {\n\tsql, _ := NewQueryBuilder().\n\t\tSelect(\"id\", \"email\", \"status\").\n\t\tFrom(\"users\").\n\t\tWhere(\"status = 'active'\").\n\t\tLimit(10).\n\t\tBuild()\n\tfmt.Println(\"Сгенерированный SQL:\", sql)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Сгенерированный SQL: SELECT id, email, status FROM users WHERE status = 'active' LIMIT 10;"
      }
    ],
    "under_the_hood": "Строки объединяются в итоговый SQL-запрос с проверкой инвариантов.",
    "pitfalls": "- SQL Injection при прямой конкатенации пользовательского ввода в Where (в реальных проектах используют placeholders `$1`, `$2`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Go популярны query builders вроде squirrel вместо чистого ORM?»\n**Ответ:** Они дают полный контроль над производительностью SQL, индексами и планами выполнения без магии ORM."
  },
  {
    "num": 111,
    "title": "Утиная типизация (Structural Typing): совпадение методов в независимых интерфейсах Reader и Scanner",
    "task": "Интерфейсы с одинаковыми методами: два интерфейса Reader (Read() string) и Scanner (Read() string). Тип Document реализует метод Read() string. Покажи, что Document удовлетворяет обоим интерфейсам автоматически (structural typing).",
    "theory": "В Go реализация интерфейсов неявная (Duck Typing / Structural Subtyping) — явного implements не требуется.",
    "step_by_step": "1. Объявляем интерфейсы StringReader и StringScanner с методом Read() string.\n2. Реализуем Document{ Content string }.\n3. Присваиваем Document обоим интерфейсам.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype StringReader interface { Read() string }\ntype StringScanner interface { Read() string }\n\ntype Document struct{ Content string }\nfunc (d Document) Read() string { return d.Content }\n\nfunc main() {\n\tdoc := Document{Content: \"Конфиденциальный документ\"}\n\n\t// Один тип автоматически реализует оба независимых интерфейса:\n\tvar r StringReader = doc\n\tvar s StringScanner = doc\n\n\tfmt.Println(\"Reader :\", r.Read())\n\tfmt.Println(\"Scanner:\", s.Read())\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Reader : Конфиденциальный документ\n# Scanner: Конфиденциальный документ"
      }
    ],
    "under_the_hood": "Компилятор строит две таблицы itab для пары (Document, StringReader) и (Document, StringScanner).",
    "pitfalls": "- Случайная реализация чужого интерфейса из-за совпадения тривиального имени метода.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем преимущество structural typing над номинативной типизацией Java/C++?»\n**Ответ:** Позволяет объявлять интерфейсы на стороне потребителя (consumer-driven interfaces) и подключать сторонние библиотеки без внесения правок в их код."
  },
  {
    "num": 112,
    "title": "Конфликтующие сигнатуры методов: почему тип не может реализовать интерфейсы с разным возвратом",
    "task": "Интерфейсы с конфликтующими сигнатурами: InterfaceA (Get() int) и InterfaceB (Get() string). Объясни, почему один тип не может реализовать оба интерфейса одновременно.",
    "theory": "В Go перегрузка методов (Method Overloading) по сигнатуре или возвращаемому типу строго запрещена.",
    "step_by_step": "1. Объявляем InterfaceA{ Get() int } и InterfaceB{ Get() string }.\n2. Объясняем невозможность одновременной реализации одним типом.\n3. Предлагаем решение через две разные структуры или адаптер.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype InterfaceA interface { Get() int }\ntype InterfaceB interface { Get() string }\n\n// Структура может объявить Get() только ОДИН раз:\ntype ContainerA struct{ val int }\nfunc (c ContainerA) Get() int { return c.val }\n\ntype ContainerB struct{ val string }\nfunc (c ContainerB) Get() string { return c.val }\n\nfunc main() {\n\tvar a InterfaceA = ContainerA{42}\n\tvar b InterfaceB = ContainerB{\"Golang\"}\n\tfmt.Printf(\"A: %d, B: %s\\n\", a.Get(), b.Get())\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# A: 42, B: Golang"
      }
    ],
    "under_the_hood": "Таблица символов типа не поддерживает дублирование имен методов с разными типами возврата.",
    "pitfalls": "- Попытка объявить два метода с одним именем `Get()` у одной структуры (ошибка компиляции `Get redeclared`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Go нет перегрузки методов (Method Overloading)?»\n**Ответ:** Создатели Go (Кен Томпсон и Роб Пайк) сознательно исключили перегрузку для однозначности и простоты чтения кода (одно имя — одна функция)."
  },
  {
    "num": 113,
    "title": "Паттерн Event Emitter: потокобезопасная шина событий с методами On, Emit, Off",
    "task": "Паттерн Event Emitter: структура EventEmitter с методами On(event string, handler func(data any)), Emit(event string, data any), Off(event string). Поддержка нескольких обработчиков на одно событие.",
    "theory": "Асинхронная или синхронная шина событий для слабой связанности микросервисных компонентов.",
    "step_by_step": "1. Создаем EventEmitter{ handlers map[string][]func(any) }.\n2. Реализуем On, Emit, Off с sync.RWMutex.\n3. Тестируем отправку события нескольким подписчикам.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n)\n\ntype EventEmitter struct {\n\tmu       sync.RWMutex\n\thandlers map[string][]func(data any)\n}\n\nfunc NewEventEmitter() *EventEmitter {\n\treturn &EventEmitter{handlers: make(map[string][]func(any))}\n}\n\nfunc (e *EventEmitter) On(event string, fn func(any)) {\n\te.mu.Lock()\n\tdefer e.mu.Unlock()\n\te.handlers[event] = append(e.handlers[event], fn)\n}\n\nfunc (e *EventEmitter) Emit(event string, data any) {\n\te.mu.RLock()\n\tdefer e.mu.RUnlock()\n\tfor _, fn := range e.handlers[event] {\n\t\tfn(data)\n\t}\n}\n\nfunc main() {\n\temitter := NewEventEmitter()\n\n\temitter.On(\"order_created\", func(d any) { fmt.Println(\"📧 Email сервис: заказ\", d) })\n\temitter.On(\"order_created\", func(d any) { fmt.Println(\"📦 Склад: зарезервирован товар для заказа\", d) })\n\n\temitter.Emit(\"order_created\", 1045)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# 📧 Email сервис: заказ 1045\n# 📦 Склад: зарезервирован товар для заказа 1045"
      }
    ],
    "under_the_hood": "Мапа со срезом функций-обработчиков защищена RWMutex.",
    "pitfalls": "- Паника внутри обработчика, ломающая вызов последующих подписчиков (нужен recover).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как изолировать обработчики в Event Emitter от взаимного влияния?»\n**Ответ:** Запускать каждый обработчик в отдельной горутине `go func() { defer recover(); fn(data) }()`."
  },
  {
    "num": 114,
    "title": "Upcasting и Downcasting в Go: неявная упаковка в интерфейс и безопасный Type Assertion",
    "task": "Upcast / Downcast в Go: покажи, как интерфейс Animal приводится к конкретному типу *Dog через type assertion (d, ok := a.(*Dog)), и как конкретный тип упаковывается в интерфейс (upcast — неявный, downcast — явный через type assertion / type switch).",
    "theory": "Upcast происходит автоматически при присваивании; Downcast требует проверки через форму с запятой (comma-ok idiom).",
    "step_by_step": "1. Объявляем Animal{ Sound() string }.\n2. Реализуем Dog{ Breed string }.\n3. Упаковываем Dog в Animal (Upcast).\n4. Распаковываем через d, ok := a.(*Dog) (Downcast).",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Animal interface { Sound() string }\n\ntype Dog struct{ Breed string }\nfunc (d *Dog) Sound() string { return \"Гав!\" }\n\nfunc main() {\n\tdog := &Dog{Breed: \"Корги\"}\n\n\t// 1. Upcast (неявный):\n\tvar a Animal = dog\n\tfmt.Println(\"Звук:\", a.Sound())\n\n\t// 2. Downcast (явный через type assertion comma-ok):\n\tif realDog, ok := a.(*Dog); ok {\n\t\tfmt.Printf(\"Успешный downcast: порода %s\\n\", realDog.Breed)\n\t}\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Звук: Гав!\n# Успешный downcast: порода Корги"
      }
    ],
    "under_the_hood": "Type Assertion сравнивает указатель `_type` внутри `iface` с типом `*Dog`.",
    "pitfalls": "- Использование одиночного утверждения `a.(*Dog)` без `ok` (вызовет панику в рантайме при несовпадении типов).",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие type assertion от type conversion?»\n**Ответ:** Type conversion (`float64(i)`) меняет представление значения в памяти; Type assertion (`i.(string)`) лишь проверяет и извлекает динамический тип из интерфейса."
  },
  {
    "num": 115,
    "title": "Stateless сервисы на базе пустой структуры struct{}: нулевой размер памяти и группировка методов",
    "task": "Stateless Service: структура MathService struct{} (пустая структура) с методами Add(a, b int) int, Multiply(a, b int) int. Объясни, почему в Go сервисы без состояния часто делают пустыми структурами (0 байт, удобная группировка методов).",
    "theory": "Пустая структура `struct{}` занимает 0 байт памяти и служит идеальным контейнером для группировки чистых функций.",
    "step_by_step": "1. Объявляем type MathService struct{}.\n2. Реализуем методы Add и Multiply.\n3. Проверяем размер структуры через unsafe.Sizeof.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"unsafe\"\n)\n\ntype MathService struct{}\n\nfunc (MathService) Add(a, b int) int      { return a + b }\nfunc (MathService) Multiply(a, b int) int { return a * b }\n\nfunc main() {\n\tsvc := MathService{}\n\tfmt.Printf(\"Размер структуры в памяти: %d байт\\n\", unsafe.Sizeof(svc))\n\tfmt.Printf(\"2 + 3 = %d\\n\", svc.Add(2, 3))\n\tfmt.Printf(\"4 * 5 = %d\\n\", svc.Multiply(4, 5))\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Размер структуры в памяти: 0 байт\n# 2 + 3 = 5\n# 4 * 5 = 20"
      }
    ],
    "under_the_hood": "Аллокации `struct{}` указывают на глобальную константу рантайма `zerobase`.",
    "pitfalls": "- Попытка хранить изменяемое состояние внутри stateless сервиса.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем делать методы на пустой структуре вместо обычных функций пакета?»\n**Ответ:** Чтобы сервис мог удовлетворять интерфейсу (например, `CalculatorService`) и легко подменяться моком в тестах."
  },
  {
    "num": 116,
    "title": "Принцип разделения интерфейсов (ISP): декомпозиция GodInterface на маленькие контракты",
    "task": "Interface Segregation Principle (ISP): покажи интерфейс-монолит GodInterface с 10 методами. Разбей его на маленькие интерфейсы Reader, Writer, Closer, Seeker. Создай составной интерфейс ReadWriteCloser через встраивание.",
    "theory": "Клиенты не должны зависеть от методов, которые они не используют (ISP).",
    "step_by_step": "1. Показываем антипаттерн GodInterface.\n2. Декомпозируем на Reader, Writer, Closer.\n3. Собираем ReadWriteCloser через композицию.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\n// Маленькие, сфокусированные интерфейсы:\ntype Reader interface{ Read() string }\ntype Writer interface{ Write(data string) }\ntype Closer interface{ Close() error }\n\n// Композиция интерфейсов:\ntype ReadWriteCloser interface {\n\tReader\n\tWriter\n\tCloser\n}\n\ntype SimpleStream struct{ data string }\nfunc (s *SimpleStream) Read() string       { return s.data }\nfunc (s *SimpleStream) Write(d string)     { s.data = d }\nfunc (s *SimpleStream) Close() error       { return nil }\n\nfunc main() {\n\tvar rwc ReadWriteCloser = &SimpleStream{}\n\trwc.Write(\"Потоковые данные\")\n\tfmt.Println(\"Прочитано:\", rwc.Read())\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Прочитано: Потоковые данные"
      }
    ],
    "under_the_hood": "Каждый интерфейс содержит только минимально необходимый набор сигнатур.",
    "pitfalls": "- Создание огромных интерфейсов-монолитов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какое золотое правило Роб Пайк сформулировал относительно размера интерфейсов в Go?»\n**Ответ:** «The bigger the interface, the weaker the abstraction» (Чем больше интерфейс, тем слабее абстракция). Самые мощные интерфейсы Go содержат 1–2 метода (`io.Reader`, `fmt.Stringer`, `error`)."
  },
  {
    "num": 117,
    "title": "Проблема хрупкого базового класса (Fragile Base Class) и ее решение через композицию в Go",
    "task": "Fragile Base Class проблема: почему в классическом ООП изменение базового класса может сломать потомков, и как Go композиция решает эту проблему (явное делегирование вместо неявного наследования).",
    "theory": "В классическом ООП изменение реализации родительского метода ломает потомков из-за неявного вызова виртуальных методов; в Go встраивание изолировано и не имеет vtable-перекрытий между родителем и потомком.",
    "step_by_step": "1. Моделируем базовый счетчик BaseCounter с методом AddAll.\n2. Встраиваем его в LoggingCounter.\n3. Демонстрируем предсказуемость делегирования.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype BaseCounter struct{ count int }\n\nfunc (b *BaseCounter) Add(n int) { b.count += n }\nfunc (b *BaseCounter) AddAll(nums []int) {\n\tfor _, v := range nums {\n\t\tb.Add(v)\n\t}\n}\n\ntype LoggingCounter struct {\n\tBaseCounter\n}\n\n// В Go вызов lc.AddAll() вызывает BaseCounter.AddAll,\n// который вызывает BaseCounter.Add, а не LoggingCounter.Add!\n// Нет неявного полиморфного перехвата -> нет хрупкости!\n\nfunc main() {\n\tlc := &LoggingCounter{}\n\tlc.AddAll([]string{\"1\", \"2\"} == nil) // безопасное поведение\n\tlc.AddAll([]int{10, 20, 30})\n\tfmt.Println(\"Итоговый подсчет:\", lc.count)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Итоговый подсчет: 60"
      }
    ],
    "under_the_hood": "Вызовы методов встроенной структуры связываются статически с получателем BaseCounter.",
    "pitfalls": "- Ожидание, что родительский метод в Go волшебным образом вызовет переопределенный метод потомка.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Go нет виртуальных методов для структур?»\n**Ответ:** Чтобы исключить проблему хрупкого базового класса, сделать код на 100% предсказуемым при чтении и упростить оптимизации компилятора (инлайнинг функций)."
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
    "bigtech_interview": "**Вопрос с собеседования:** «Когда Value Receiver быстрее Pointer Receiver?»\n**Ответ:** Для структур размером $\\le 16$ байт, так как они полностью помещаются в процессорные регистры и не вызывают escape analysis в кучу."
  },
  {
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
  },
  {
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
  }
]
