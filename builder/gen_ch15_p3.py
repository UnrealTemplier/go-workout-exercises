exercises = [
  {
    "num": 66,
    "title": "Встраивание Animal в Dog: продвижение метода Breathe() и собственный метод Bark()",
    "task": "Встраивание: Animal (Breathe()), Dog встраивает Animal и добавляет Bark(). Создайте экземпляр Dog и вызовите dog.Breathe() и dog.Bark().",
    "theory": "Композиция поведения: базовая функциональность наследуется через встраивание, а доменная добавляется напрямую.",
    "step_by_step": "1. Создаем Animal с методом Breathe().\n2. Создаем Dog со встраиванием Animal и методом Bark().\n3. Вызываем оба метода.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Animal struct{ Species string }\nfunc (a Animal) Breathe() { fmt.Printf(\"[%s] Дышит кислородом\\n\", a.Species) }\n\ntype Dog struct {\n\tAnimal\n\tBreed string\n}\nfunc (d Dog) Bark() { fmt.Printf(\"[%s] Гав-гав!\\n\", d.Breed) }\n\nfunc main() {\n\td := Dog{Animal: Animal{Species: \"Млекопитающее\"}, Breed: \"Хаски\"}\n\td.Breathe() // Promoted method\n\td.Bark()\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# [Млекопитающее] Дышит кислородом\n# [Хаски] Гав-гав!"
      }
    ],
    "under_the_hood": "Компилятор генерирует прямое обращение d.Animal.Breathe().",
    "pitfalls": "- Думать, что Animal может вызвать Bark().",
    "bigtech_interview": "**Вопрос с собеседования:** «Знает ли встроенная структура о внешней структуре?»\n**Ответ:** Нет, встроенная структура изолирована и ничего не знает о типе, в который она встроена."
  },
  {
    "num": 67,
    "title": "Паттерн Декоратор (Decorator Pattern): TimestampLogger со встраиванием интерфейса Logger",
    "task": "Паттерн «Декоратор»: интерфейс Logger (метод Log(msg string)), базовая реализация StdoutLogger. Декоратор TimestampLogger встраивает Logger и добавляет таймстемп к сообщению перед вызовом базового логера.",
    "theory": "Декоратор динамически расширяет поведение без изменения исходного класса.",
    "step_by_step": "1. Объявляем интерфейс Logger.\n2. Реализуем StdoutLogger.\n3. Создаем TimestampLogger со встраиванием Logger и переопределением Log.\n4. Тестируем.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"time\"\n)\n\ntype Logger interface {\n\tLog(msg string)\n}\n\ntype StdoutLogger struct{}\nfunc (StdoutLogger) Log(msg string) { fmt.Println(msg) }\n\ntype TimestampLogger struct {\n\tLogger // Встраивание интерфейса\n}\n\nfunc (t TimestampLogger) Log(msg string) {\n\tts := time.Now().Format(\"15:04:05\")\n\tt.Logger.Log(fmt.Sprintf(\"[%s] %s\", ts, msg))\n}\n\nfunc main() {\n\tbase := StdoutLogger{}\n\tdecorated := TimestampLogger{Logger: base}\n\tdecorated.Log(\"Сервис успешно запущен\")\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# [15:04:05] Сервис успешно запущен"
      }
    ],
    "under_the_hood": "Декоратор делегирует вызов базовому логеру через интерфейс.",
    "pitfalls": "- Передача nil в поле Logger (приведет к панике nil dereference).",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем преимущество декораторов на интерфейсах?»\n**Ответ:** Возможность компоновать цепочки декораторов (таймстемп + JSON + отправка в Kafka) без изменения исходного кода."
  },
  {
    "num": 68,
    "title": "Method Value vs Pointer Receiver: поведение замыкания f := myGreeter.Greet при изменении объекта",
    "task": "Method value: type Greeter struct { Name string }, метод Greet(). Создай f := myGreeter.Greet, вызови f(). Измени myGreeter.Name. Вызови f() снова. Объясни разницу между value receiver и pointer receiver в этом сценарии.",
    "theory": "Method Value копирует значение объекта при Value Receiver, но сохраняет ссылку при Pointer Receiver.",
    "step_by_step": "1. Создаем GreeterValue и GreeterPtr.\n2. Создаем замыкания fnVal и fnPtr.\n3. Меняем Name и сравниваем повторные вызовы.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype GreeterVal struct{ Name string }\nfunc (g GreeterVal) Greet() { fmt.Println(\"Val:\", g.Name) }\n\ntype GreeterPtr struct{ Name string }\nfunc (g *GreeterPtr) Greet() { fmt.Println(\"Ptr:\", g.Name) }\n\nfunc main() {\n\tgv := GreeterVal{Name: \"Алиса\"}\n\tfnVal := gv.Greet\n\tgv.Name = \"Боб\"\n\tfnVal() // Напечатает 'Алиса' (копия!)\n\n\tgp := &GreeterPtr{Name: \"Алиса\"}\n\tfnPtr := gp.Greet\n\tgp.Name = \"Боб\"\n\tfnPtr() // Напечатает 'Боб' (указатель!)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Val: Алиса\n# Ptr: Боб"
      }
    ],
    "under_the_hood": "При Value Receiver замыкание захватывает копию данных; при Pointer Receiver — адрес памяти.",
    "pitfalls": "- Ожидание актуального состояния от Value Receiver замыкания.",
    "bigtech_interview": "**Вопрос с собеседования:** «Где Method Values применяются на практике?»\n**Ответ:** В роутерах (r.Get(\"/\", s.handleIndex)) и в горутинах (go worker.Run)."
  },
  {
    "num": 69,
    "title": "Паттерн Строитель (Builder Pattern): пошаговая сборка HouseBuilder со fluent интерфейсом",
    "task": "Паттерн «Строитель» (Builder): HouseBuilder с методами WithFloors(n int), WithPool(), Build() House. Соберите дом с бассейном через цепочку вызовов.",
    "theory": "Паттерн Builder изолирует сложную логику конструирования объекта от его представления.",
    "step_by_step": "1. Создаем структуру House.\n2. Создаем HouseBuilder с методами WithFloors, WithPool, Build.\n3. Собираем объект через цепочку.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype House struct {\n\tFloors  int\n\tHasPool bool\n}\n\ntype HouseBuilder struct {\n\thouse House\n}\n\nfunc NewHouseBuilder() *HouseBuilder { return &HouseBuilder{} }\nfunc (b *HouseBuilder) WithFloors(n int) *HouseBuilder { b.house.Floors = n; return b }\nfunc (b *HouseBuilder) WithPool() *HouseBuilder        { b.house.HasPool = true; return b }\nfunc (b *HouseBuilder) Build() House                  { return b.house }\n\nfunc main() {\n\th := NewHouseBuilder().WithFloors(3).WithPool().Build()\n\tfmt.Printf(\"Построен дом: этажей=%d, бассейн=%t\\n\", h.Floors, h.HasPool)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Построен дом: этажей=3, бассейн=true"
      }
    ],
    "under_the_hood": "Строитель мутирует поля в памяти и возвращает собственный указатель.",
    "pitfalls": "- Переиспользование одного и того же билдера без сброса состояния.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие Builder от Functional Options в Go?»\n**Ответ:** Builder создает промежуточный объект-строитель с мутацией состояния, а Functional Options конфигурируют объект через срез замыканий напрямую в конструкторе."
  },
  {
    "num": 70,
    "title": "Паттерн Functional Options: гибкая конфигурация Server через WithPort и WithTimeout",
    "task": "Паттерн Functional Options: структура Server (host, port, timeout, maxConns). Конструктор NewServer(opts ...Option) с дефолтными значениями. Опции WithPort(p int), WithTimeout(d time.Duration). Создайте сервер с кастомным портом и таймаутом.",
    "theory": "Золотой стандарт конфигурации в экосистеме Go (Rob Pike / Dave Cheney).",
    "step_by_step": "1. Создаем Server с приватными полями.\n2. Объявляем type Option func(*Server).\n3. Реализуем WithPort, WithTimeout.\n4. Пишем NewServer с дефолтными значениями.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"time\"\n)\n\ntype Server struct {\n\tHost    string\n\tPort    int\n\tTimeout time.Duration\n}\n\ntype Option func(*Server)\n\nfunc WithPort(port int) Option {\n\treturn func(s *Server) { s.Port = port }\n}\n\nfunc WithTimeout(d time.Duration) Option {\n\treturn func(s *Server) { s.Timeout = d }\n}\n\nfunc NewServer(opts ...Option) *Server {\n\tsrv := &Server{Host: \"0.0.0.0\", Port: 8080, Timeout: 30 * time.Second}\n\tfor _, opt := range opts {\n\t\topt(srv)\n\t}\n\treturn srv\n}\n\nfunc main() {\n\ts := NewServer(WithPort(9090), WithTimeout(5*time.Second))\n\tfmt.Printf(\"Сервер: %s:%d (Таймаут: %v)\\n\", s.Host, s.Port, s.Timeout)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Сервер: 0.0.0.0:9090 (Таймаут: 5s)"
      }
    ],
    "under_the_hood": "Замыкания применяются последовательно к структуре сервера.",
    "pitfalls": "- Передача nil опции в NewServer.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему Functional Options предпочтительнее передачи структуры Config?»\n**Ответ:** Functional Options сохраняют 100% обратную совместимость при добавлении новых опций, не требуют заполнения нулями дефолтных полей и инкапсулируют валидацию параметров."
  },
  {
    "num": 71,
    "title": "Fluent Validator: валидация строк Required и MinLen с накоплением ошибок",
    "task": "Валидация в методах: структура Validator с полем errors []string. Методы Required(val, fieldName), MinLen(val, min, fieldName), IsValid() bool, Errors() []string. Цепочка проверок для формы регистрации.",
    "theory": "Накопление ошибок валидации без прерывания выполнения.",
    "step_by_step": "1. Создаем Validator{ errors []string }.\n2. Реализуем Required, MinLen, IsValid, Errors.\n3. Проверяем регистрационную форму.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n)\n\ntype Validator struct {\n\terrs []string\n}\n\nfunc (v *Validator) Required(val, field string) *Validator {\n\tif strings.TrimSpace(val) == \"\" {\n\t\tv.errs = append(v.errs, fmt.Sprintf(\"Поле %q обязательно\", field))\n\t}\n\treturn v\n}\n\nfunc (v *Validator) MinLen(val string, min int, field string) *Validator {\n\tif len(val) < min {\n\t\tv.errs = append(v.errs, fmt.Sprintf(\"Поле %q должно быть не короче %d символов\", field, min))\n\t}\n\treturn v\n}\n\nfunc (v *Validator) IsValid() bool     { return len(v.errs) == 0 }\nfunc (v *Validator) Errors() []string { return v.errs }\n\nfunc main() {\n\tv := &Validator{}\n\tv.Required(\"\", \"username\").MinLen(\"123\", 6, \"password\")\n\tfmt.Println(\"Форма валидна?\", v.IsValid())\n\tfor _, e := range v.Errors() {\n\t\tfmt.Println(\"❌\", e)\n\t}\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Форма валидна? false\n# ❌ Поле \"username\" обязательно\n# ❌ Поле \"password\" должно быть не короче 6 символов"
      }
    ],
    "under_the_hood": "Ошибки аппендятся в динамический срез errs.",
    "pitfalls": "- Не возвращать *Validator из валидационных методов (сломается цепочка).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как сделать Validator потокобезопасным?»\n**Ответ:** Создавать отдельный экземпляр Validator на каждый HTTP-запрос (локально в стеке горутины) без глобального разделяемого состояния."
  },
  {
    "num": 72,
    "title": "Паттерн Фабричный Метод (Factory Method): полиморфный конструктор NewProcessor",
    "task": "Фабрика структур: интерфейс Processor с методом Process(data string) string. Функция NewProcessor(ptype string) (Processor, error), возвращающая JSONProcessor или XMLProcessor в зависимости от строки.",
    "theory": "Инкапсуляция создания конкретных реализаций за фабричной функцией.",
    "step_by_step": "1. Объявляем Processor{ Process(string) string }.\n2. Реализуем JSONProcessor и XMLProcessor.\n3. Создаем NewProcessor с выбором по типу.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n)\n\ntype Processor interface {\n\tProcess(data string) string\n}\n\ntype JSONProcessor struct{}\nfunc (JSONProcessor) Process(d string) string { return \"[JSON]: {\" + d + \"}\" }\n\ntype XMLProcessor struct{}\nfunc (XMLProcessor) Process(d string) string { return \"[XML]: <data>\" + d + \"</data>\" }\n\nfunc NewProcessor(pType string) (Processor, error) {\n\tswitch pType {\n\tcase \"json\":\n\t\treturn JSONProcessor{}, nil\n\tcase \"xml\":\n\t\treturn XMLProcessor{}, nil\n\tdefault:\n\t\treturn nil, fmt.Errorf(\"неизвестный процессор: %s\", pType)\n\t}\n}\n\nfunc main() {\n\tp, _ := NewProcessor(\"json\")\n\tfmt.Println(p.Process(\"status: 200\"))\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# [JSON]: {status: 200}"
      }
    ],
    "under_the_hood": "Фабрика упаковывает конкретную структуру в интерфейс Processor.",
    "pitfalls": "- Возврат неэкспортированного типа ошибки вместо стандартного error.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда фабричный метод лучше прямого создания структуры?»\n**Ответ:** Когда вызывающий код должен зависеть от абстракции, а не от конкретных деталей создания объектов."
  },
  {
    "num": 73,
    "title": "Ловушка типизированного nil: почему возврат (*MyError)(nil) в error ломает проверку err != nil",
    "task": "Опасность типизированного nil в error: функция возвращает *MyError как error. Создай функцию, которая возвращает nil указатель *MyError, но тип возврата — error. Покажи, что if err != nil срабатывает (потому что интерфейс содержит тип, но nil значение). Исправь баг.",
    "theory": "Интерфейс в Go равен nil ТОЛЬКО если и type == nil, и data == nil. Типизированный nil (*MyError)(nil) имеет type != nil, поэтому if err != nil вернет TRUE!",
    "step_by_step": "1. Создаем MyError{ Msg string }.\n2. Пишем ошибочную функцию GetErrorBad() error, возвращающую *MyError(nil).\n3. Пишем исправленную функцию GetErrorGood() error, возвращающую явный nil.\n4. Сравниваем результаты.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype MyError struct{ Msg string }\nfunc (m *MyError) Error() string { return m.Msg }\n\n// ❌ ОШИБКА: типизированный nil попадает в интерфейс\nfunc GetErrorBad() error {\n\tvar err *MyError = nil\n\treturn err // eface{type: *MyError, data: 0x0} != nil !\n}\n\n// ✅ ИСПРАВЛЕНИЕ: возврат явного nil\nfunc GetErrorGood() error {\n\tvar err *MyError = nil\n\tif err != nil {\n\t\treturn err\n\t}\n\treturn nil // eface{type: 0x0, data: 0x0} == nil\n}\n\nfunc main() {\n\tif err := GetErrorBad(); err != nil {\n\t\tfmt.Println(\"🚨 БАГ: err != nil сработал для nil указателя!\")\n\t}\n\n\tif err := GetErrorGood(); err == nil {\n\t\tfmt.Println(\"✅ ИСПРАВЛЕНО: err == nil сработал корректно\")\n\t}\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# 🚨 БАГ: err != nil сработал для nil указателя!\n# ✅ ИСПРАВЛЕНО: err == nil сработал корректно"
      }
    ],
    "under_the_hood": "Интерфейс (iface/eface) состоит из двух указателей: itab (тип) и data (значение). Если itab != 0, интерфейс НЕ равен nil.",
    "pitfalls": "- Возврат переменной кастомного типа ошибки вместо явного return nil.",
    "bigtech_interview": "**Вопрос с собеседования:** «Топ-1 вопрос на собеседованиях по Go: почему `var p *int = nil; var i any = p; i == nil` возвращает `false`?»\n**Ответ:** Потому что интерфейс `any` хранит тип `*int` и значение `nil`. Интерфейс равен `nil` только тогда, когда и тип, и значение равны `nil`."
  },
  {
    "num": 74,
    "title": "Расширение прав доступа: структура AdminUser со встроенным User и переопределением CanAccess",
    "task": "AdminUser встраивает User, добавляет Permissions []string. Переопределите метод CanAccess(resource string) bool: обычный User имеет доступ только к \"profile\", а AdminUser — к любому ресурсу из Permissions или если он \"admin\".",
    "theory": "Переопределение логики авторизации через встраивание базового пользователя.",
    "step_by_step": "1. Создаем User{Name} с CanAccess(res).\n2. Создаем AdminUser со встраиванием User и Permissions.\n3. Переопределяем CanAccess.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype User struct{ Name string }\nfunc (u User) CanAccess(res string) bool { return res == \"profile\" }\n\ntype AdminUser struct {\n\tUser\n\tPermissions []string\n}\n\nfunc (a AdminUser) CanAccess(res string) bool {\n\tfor _, p := range a.Permissions {\n\t\tif p == res || p == \"*\" {\n\t\t\treturn true\n\t\t}\n\t}\n\treturn a.User.CanAccess(res)\n}\n\nfunc main() {\n\tu := User{\"Иван\"}\n\ta := AdminUser{User: User{\"Ольга\"}, Permissions: []string{\"dashboard\", \"metrics\"}}\n\n\tfmt.Println(\"Иван к dashboard:\", u.CanAccess(\"dashboard\"))\n\tfmt.Println(\"Ольга к dashboard:\", a.CanAccess(\"dashboard\"))\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Иван к dashboard: false\n# Ольга к dashboard: true"
      }
    ],
    "under_the_hood": "AdminUser.CanAccess перекрывает базовый метод User.",
    "pitfalls": "- Забыть проверить базовые права через a.User.CanAccess.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как организовать RBAC в Go микросервисах?»\n**Ответ:** Через контекст запроса context.Context и middleware, проверяющие роли и права в токене JWT."
  },
  {
    "num": 75,
    "title": "Паттерн Одиночка (Singleton Pattern): потокобезопасная инициализация через sync.Once",
    "task": "Паттерн «Одиночка» (Singleton): структура DatabaseConnection (DSN string). Функция GetConnection() *DatabaseConnection с использованием sync.Once гарантирует создание ровно одного экземпляра при конкурентных вызовах.",
    "theory": "sync.Once обеспечивает атомарную ленивую инициализацию без блокировок при последующих чтениях.",
    "step_by_step": "1. Создаем DatabaseConnection{ DSN string }.\n2. Объявляем instance *DatabaseConnection и once sync.Once.\n3. В GetConnection вызываем once.Do(func() { ... }).",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n)\n\ntype DatabaseConnection struct {\n\tDSN string\n}\n\nvar (\n\tinstance *DatabaseConnection\n\tonce     sync.Once\n)\n\nfunc GetConnection() *DatabaseConnection {\n\tonce.Do(func() {\n\t\tfmt.Println(\"[Инициализация соединения с PostgreSQL]\")\n\t\tinstance = &DatabaseConnection{DSN: \"postgres://user:pass@localhost:5432/db\"}\n\t})\n\treturn instance\n}\n\nfunc main() {\n\tvar wg sync.WaitGroup\n\tfor i := 0; i < 5; i++ {\n\t\twg.Add(1)\n\t\tgo func(id int) {\n\t\t\tdefer wg.Done()\n\t\t\tconn := GetConnection()\n\t\t\t_ = conn\n\t\t}(i)\n\t}\n\twg.Wait()\n\tfmt.Println(\"Все горутины получили один и тот же инстанс!\")\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run -race main.go\n# [Инициализация соединения с PostgreSQL]\n# Все горутины получили один и тот же инстанс!"
      }
    ],
    "under_the_hood": "sync.Once использует быстрый atomic.LoadUint32 и медленный Mutex только для первой горутины.",
    "pitfalls": "- Паника внутри once.Do (повторно функция вызвана не будет, инстанс останется nil).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему sync.Once быстрее, чем mutex.Lock() при каждом вызове?»\n**Ответ:** Потому что после первой инициализации `sync.Once` проверяет атомарный флаг с помощью `atomic.LoadUint32`, не заходя в тяжелую системную блокировку мьютекса."
  },
  {
    "num": 76,
    "title": "Паттерн Стратегия для форматирования текста: TextProcessor и интерфейс Formatter",
    "task": "Паттерн Стратегия: TextProcessor принимает Formatter (интерфейс с методом Format(string) string). Реализуйте UpperFormatter (переводит в верхний регистр) и MarkdownFormatter (оборачивает в **жирный**).",
    "theory": "Подстановка стратегии форматирования без изменения текстового процессора.",
    "step_by_step": "1. Объявляем Formatter{ Format(string) string }.\n2. Реализуем UpperFormatter и MarkdownFormatter.\n3. Создаем TextProcessor{ formatter Formatter }.\n4. Тестируем разные стратегии.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n)\n\ntype Formatter interface {\n\tFormat(text string) string\n}\n\ntype UpperFormatter struct{}\nfunc (UpperFormatter) Format(t string) string { return strings.ToUpper(t) }\n\ntype MarkdownBoldFormatter struct{}\nfunc (MarkdownBoldFormatter) Format(t string) string { return \"**\" + t + \"**\" }\n\ntype TextProcessor struct {\n\tfmt Formatter\n}\n\nfunc (tp TextProcessor) Render(s string) string {\n\treturn tp.fmt.Format(s)\n}\n\nfunc main() {\n\tp1 := TextProcessor{fmt: UpperFormatter{}}\n\tp2 := TextProcessor{fmt: MarkdownBoldFormatter{}}\n\n\tfmt.Println(p1.Render(\"golang\"))\n\tfmt.Println(p2.Render(\"golang\"))\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# GOLANG\n# **golang**"
      }
    ],
    "under_the_hood": "Динамический вызов tp.fmt.Format(s) через vtable интерфейса.",
    "pitfalls": "- Передача nil интерфейса в TextProcessor.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие паттерна Strategy от Decorator?»\n**Ответ:** Strategy меняет сам алгоритм работы изнутри (взаимозаменяемые реализации), а Decorator оборачивает объект снаружи, добавляя функциональность поверх существующей."
  },
  {
    "num": 77,
    "title": "Метод-выражение (Method Expression): явная передача получателя f := Greeter.Greet(g)",
    "task": "Метод-выражение (Method Expression): type Greeter struct { Name string }, метод Greet(). Создай f := Greeter.Greet (выражение метода, где тип — func(Greeter)). Вызови f(myGreeter). Объясни, чем method expression отличается от method value.",
    "theory": "Method Expression Greeter.Greet превращает метод в обычную функцию func(Greeter), требующую явной передачи получателя первым аргументом.",
    "step_by_step": "1. Создаем Greeter{Name string}.\n2. Получаем Method Expression fn := Greeter.Greet.\n3. Вызываем fn(Greeter{\"Мария\"}).",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Greeter struct{ Name string }\n\nfunc (g Greeter) Greet(greeting string) {\n\tfmt.Printf(\"%s, %s!\\n\", greeting, g.Name)\n}\n\nfunc main() {\n\t// Method Expression: тип func(Greeter, string)\n\tfn := Greeter.Greet\n\n\tg1 := Greeter{Name: \"Мария\"}\n\tg2 := Greeter{Name: \"Иван\"}\n\n\tfn(g1, \"Привет\")\n\tfn(g2, \"Добрый день\")\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Привет, Мария!\n# Добрый день, Иван!"
      }
    ],
    "under_the_hood": "Компилятор раскрывает синтаксис в вызов функции main.Greeter.Greet(g1, \"Привет\").",
    "pitfalls": "- Путаница между Method Expression (от типа: Type.Method) и Method Value (от экземпляра: instance.Method).",
    "bigtech_interview": "**Вопрос с собеседования:** «Какова сигнатура Method Expression для метода `func (p *Point) Scale(f float64)`?»\n**Ответ:** Сигнатура: `func(*Point, float64)`."
  },
  {
    "num": 78,
    "title": "Инкапсуляция конфигурации пакета config: приватная map и публичные функции Set/Get",
    "task": "Инкапсуляция конфигурации: пакет config с приватной глобальной переменной cfg map[string]string. Публичные функции Set(key, value string), Get(key string) (string, bool), Reset(). Доступ к мапе напрямую из main невозможен.",
    "theory": "Сокрытие глобального состояния пакета за потокобезопасным API.",
    "step_by_step": "1. Создаем приватную map configStore.\n2. Реализуем публичные функции Set, Get, Reset с sync.RWMutex.\n3. Тестируем в main.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n)\n\n// Имитация пакета config:\nvar (\n\tmu  sync.RWMutex\n\tcfg = make(map[string]string)\n)\n\nfunc SetConfig(k, v string) {\n\tmu.Lock()\n\tdefer mu.Unlock()\n\tcfg[k] = v\n}\n\nfunc GetConfig(k string) (string, bool) {\n\tmu.RLock()\n\tdefer mu.RUnlock()\n\tval, ok := cfg[k]\n\treturn val, ok\n}\n\nfunc main() {\n\tSetConfig(\"ENV\", \"production\")\n\tSetConfig(\"PORT\", \"8080\")\n\n\tif val, ok := GetConfig(\"ENV\"); ok {\n\t\tfmt.Println(\"Режим работы:\", val)\n\t}\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Режим работы: production"
      }
    ],
    "under_the_hood": "Карта скрыта в секции данных пакета и защищена мьютексом.",
    "pitfalls": "- Неблокируемый доступ к глобальной мапе в горутинах (вызовет concurrent map read and map write panic).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Go не рекомендуется злоупотреблять глобальным состоянием пакета?»\n**Ответ:** Глобальное состояние затрудняет параллельное тестирование и приводит к скрытой связности компонентов."
  },
  {
    "num": 79,
    "title": "Полиморфная фабрика платежей: функция GetPaymentMethod и интерфейс PaymentMethod",
    "task": "Фабрика с полиморфизмом: GetPaymentMethod(mtype string) (PaymentMethod, error), где PaymentMethod — интерфейс с методом Pay(amount float64) error. Реализации: CardPayment, CryptoPayment. Вызов оплаты через интерфейс.",
    "theory": "Фабрика возвращает интерфейс, скрывая конкретные структуры за полиморфным контрактом.",
    "step_by_step": "1. Создаем интерфейс PaymentMethod{ Pay(float64) error }.\n2. Реализуем CardPayment и CryptoPayment.\n3. Пишем фабрику GetPaymentMethod.\n4. Вызываем оплату.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n)\n\ntype PaymentMethod interface {\n\tPay(amount float64) error\n}\n\ntype CardPayment struct{}\nfunc (CardPayment) Pay(amt float64) error {\n\tfmt.Printf(\"Списание %.2f руб. с банковской карты\\n\", amt)\n\treturn nil\n}\n\ntype CryptoPayment struct{}\nfunc (CryptoPayment) Pay(amt float64) error {\n\tfmt.Printf(\"Транзакция %.2f USDT отправлена в блокчейн\\n\", amt)\n\treturn nil\n}\n\nfunc GetPaymentMethod(mType string) (PaymentMethod, error) {\n\tswitch mType {\n\tcase \"card\":\n\t\treturn CardPayment{}, nil\n\tcase \"crypto\":\n\t\treturn CryptoPayment{}, nil\n\tdefault:\n\t\treturn nil, fmt.Errorf(\"неизвестный метод оплаты: %s\", mType)\n\t}\n}\n\nfunc main() {\n\tmethod, _ := GetPaymentMethod(\"crypto\")\n\t_ = method.Pay(150.0)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Транзакция 150.00 USDT отправлена в блокчейн"
      }
    ],
    "under_the_hood": "Полиморфный вызов без знания конкретного типа.",
    "pitfalls": "- Игнорирование ошибки, возвращаемой фабрикой.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как расширить фабрику без модификации функции switch-case?»\n**Ответ:** Использовать реестр фабрик `var registry = make(map[string]PaymentFactory)` с саморегистрацией в `init()`."
  },
  {
    "num": 80,
    "title": "Методы для срезов чисел: кастомный тип Numbers с методами Sum, Avg, Filter",
    "task": "Методы для среза: type Numbers []int. Реализуй методы Sum() int, Avg() float64, Filter(predicate func(int) bool) Numbers. Сделай цепочку: nums.Filter(isEven).Sum().",
    "theory": "Функциональное расширение срезов методами высшего порядка.",
    "step_by_step": "1. Объявляем type Numbers []int.\n2. Реализуем Sum(), Avg(), Filter().\n3. Собираем цепочку вызовов.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Numbers []int\n\nfunc (n Numbers) Sum() int {\n\tt := 0\n\tfor _, v := range n { t += v }\n\treturn t\n}\n\nfunc (n Numbers) Avg() float64 {\n\tif len(n) == 0 { return 0 }\n\treturn float64(n.Sum()) / float64(len(n))\n}\n\nfunc (n Numbers) Filter(pred func(int) bool) Numbers {\n\tvar res Numbers\n\tfor _, v := range n {\n\t\tif pred(v) { res = append(res, v) }\n\t}\n\treturn res\n}\n\nfunc main() {\n\tnums := Numbers{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}\n\tisEven := func(x int) bool { return x%2 == 0 }\n\n\tsumEven := nums.Filter(isEven).Sum()\n\tfmt.Printf(\"Сумма четных: %d\\n\", sumEven)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Сумма четных: 30"
      }
    ],
    "under_the_hood": "Каждый метод возвращает новый экземпляр среза Numbers.",
    "pitfalls": "- Вызов Avg() на пустом срезе без проверки деления на 0.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в стандартной библиотеке Go нет методов Filter/Map на слайсах?»\n**Ответ:** Go придерживается простоты синтаксиса и максимальной производительности без скрытых аллокаций; с Go 1.21 добавлены дженерик-пакеты `slices` и `maps`."
  },
  {
    "num": 81,
    "title": "Неадресуемость элементов map: почему m[\"a\"].ChangeName() не работает и решение через map[string]*User",
    "task": "Неадресуемость элементов map: создай map[string]User. Попробуй вызвать m[\"a\"].ChangeName(\"Bob\") (где ChangeName — pointer receiver). Получи ошибку компиляции. Объясни, почему элементы map неадресуемы (эвакуация бакетов). Исправь, используя map[string]*User.",
    "theory": "Элементы map не имеют фиксированного адреса в памяти, так как при расширении хэш-таблицы бакеты перемещаются. Решение — хранить в карте указатели map[string]*User.",
    "step_by_step": "1. Создаем User{Name string} с методом (u *User) ChangeName(n string).\n2. Показываем ошибку m[\"a\"].ChangeName(\"Bob\").\n3. Исправляем на map[string]*User.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype User struct{ Name string }\nfunc (u *User) ChangeName(newName string) { u.Name = newName }\n\nfunc main() {\n\t// 1. Ошибка на map со значениями: map[string]User\n\t// m := map[string]User{\"u1\": {\"Алиса\"}}\n\t// m[\"u1\"].ChangeName(\"Боб\") // ❌ cannot call pointer method ChangeName on User\n\n\t// 2. Исправление через map с указателями: map[string]*User\n\tusers := map[string]*User{\n\t\t\"u1\": &User{Name: \"Алиса\"},\n\t}\n\n\tusers[\"u1\"].ChangeName(\"Боб\") // ✅ Успех!\n\tfmt.Println(\"Новое имя пользователя:\", users[\"u1\"].Name)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Новое имя пользователя: Боб"
      }
    ],
    "under_the_hood": "Указатель `*User` указывает на постоянный адрес в куче, не зависящий от реорганизации бакетов мапы `hmap`.",
    "pitfalls": "- Попытка изменить поле структуры в map[string]Struct через прямое присваивание `m[\"key\"].Field = val`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему компилятор Go запрещает брать адрес элемента мапы `&m[\"key\"]`?»\n**Ответ:** Потому что при добавлении новых ключей мапа производит рехэширование (эвакуацию бакетов), и адрес старого слота становится инвалидным, что привело бы к висячим указателям (Dangling Pointers)."
  },
  {
    "num": 82,
    "title": "Паттерн Состояние (State Machine): управление жизненным циклом Order (New -> Paid -> Shipped)",
    "task": "Паттерн Состояние (State Machine): заказ Order с состояниями Created, Paid, Shipped, Cancelled. Методы Pay(), Ship(), Cancel(). Переход возможен только по правилам: Created -> Paid -> Shipped, Created -> Cancelled. Невалидные переходы возвращают ошибку.",
    "theory": "Конечный автомат (FSM) предотвращает недопустимые переходы состояний заказа.",
    "step_by_step": "1. Объявляем тип State int и константы.\n2. Создаем Order{ state State }.\n3. Реализуем Pay(), Ship(), Cancel() с валидацией переходов.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n)\n\ntype OrderState string\n\nconst (\n\tCreated   OrderState = \"CREATED\"\n\tPaid      OrderState = \"PAID\"\n\tShipped   OrderState = \"SHIPPED\"\n\tCancelled OrderState = \"CANCELLED\"\n)\n\ntype Order struct {\n\tID    int\n\tstate OrderState\n}\n\nfunc (o *Order) Pay() error {\n\tif o.state != Created {\n\t\treturn fmt.Errorf(\"нельзя оплатить заказ в статусе %s\", o.state)\n\t}\n\to.state = Paid\n\treturn nil\n}\n\nfunc (o *Order) Ship() error {\n\tif o.state != Paid {\n\t\treturn fmt.Errorf(\"нельзя отправить неоплаченный заказ (%s)\", o.state)\n\t}\n\to.state = Shipped\n\treturn nil\n}\n\nfunc main() {\n\to := &Order{ID: 101, state: Created}\n\t_ = o.Pay()\n\tfmt.Println(\"Статус после оплаты:\", o.state)\n\n\tif err := o.Pay(); err != nil {\n\t\tfmt.Println(\"❌ Ошибка повторной оплаты:\", err)\n\t}\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Статус после оплаты: PAID\n# ❌ Ошибка повторной оплаты: нельзя оплатить заказ в статусе PAID"
      }
    ],
    "under_the_hood": "Проверка текущего состояния перед мутацией поля state.",
    "pitfalls": "- Изменение state в обход методов конечного автомата.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как гарантировать атомарность перехода состояний при высокой конкурентности?»\n**Ответ:** Использовать транзакции БД с `SELECT FOR UPDATE` или оптимистическую блокировку по полю `version`."
  },
  {
    "num": 83,
    "title": "Принцип подстановки Барбары Лисков (LSP): разделение Bird, FlyingBird и структура Ostrich",
    "task": "LSP (Liskov Substitution Principle): покажи нарушение LSP: интерфейс Bird с методами Fly() и Eat(). Создай Ostrich (страус), для которого Fly() возвращает ошибку или паникует. Исправь дизайн: раздели на Bird (Eat()) и FlyingBird (встраивает Bird + Fly()).",
    "theory": "Интерфейсы должны описывать только то поведение, которое истинно для всех их реализаций (ISP & LSP).",
    "step_by_step": "1. Демонстрируем неправильную модель Bird с Fly().\n2. Декомпозируем на Bird{ Eat() } и FlyingBird{ Bird; Fly() }.\n3. Реализуем Sparrow (летает) и Ostrich (не летает).",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\n// Базовый интерфейс для всех птиц:\ntype Bird interface {\n\tEat()\n}\n\n// Интерфейс только для летающих птиц:\ntype FlyingBird interface {\n\tBird\n\tFly()\n}\n\ntype Sparrow struct{}\nfunc (Sparrow) Eat() { fmt.Println(\"Воробей клюет зерно\") }\nfunc (Sparrow) Fly() { fmt.Println(\"Воробей летит в небе\") }\n\ntype Ostrich struct{}\nfunc (Ostrich) Eat() { fmt.Println(\"Страус ест траву\") }\n// Ostrich не реализует Fly, соблюдая LSP!\n\nfunc main() {\n\tbirds := []Bird{Sparrow{}, Ostrich{}}\n\tfor _, b := range birds {\n\t\tb.Eat()\n\t}\n\n\tvar flyer FlyingBird = Sparrow{}\n\tflyer.Fly()\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Воробей клюет зерно\n# Страус ест траву\n# Воробей летит в небе"
      }
    ],
    "under_the_hood": "Интерфейсы строго соответствуют реальным возможностям типов.",
    "pitfalls": "- Возврат panic(\"не поддерживается\") в методах интерфейса.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем суть Liskov Substitution Principle (LSP) в Go?»\n**Ответ:** Любая реализация интерфейса должна полностью и корректно выполнять контракт без неожиданных исключений или паник."
  },
  {
    "num": 84,
    "title": "Глубокое клонирование (Deep Copy): метод Clone() для структур со срезами и указателями",
    "task": "Метод Clone(): структура Profile (Name string, Tags []string, Meta *Metadata). Метод Clone() *Profile создаёт глубокую копию (deep copy) — модификация срезов и указателей в клоне не влияет на оригинал.",
    "theory": "Поверхностное копирование (Shallow Copy) копирует указатели на те же срезы; Deep Copy выделяет независимую память.",
    "step_by_step": "1. Создаем Profile{Name, Tags []string, Meta *Metadata}.\n2. Реализуем Clone() с созданием копий среза и указателя.\n3. Проверяем независимость мутаций.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Metadata struct{ Score int }\n\ntype Profile struct {\n\tName string\n\tTags []string\n\tMeta *Metadata\n}\n\nfunc (p *Profile) Clone() *Profile {\n\tif p == nil { return nil }\n\t\n\t// 1. Копируем срез тегов:\n\ttagsCopy := make([]string, len(p.Tags))\n\tcopy(tagsCopy, p.Tags)\n\n\t// 2. Копируем структуру метаданных:\n\tvar metaCopy *Metadata\n\tif p.Meta != nil {\n\t\tmetaCopy = &Metadata{Score: p.Meta.Score}\n\t}\n\n\treturn &Profile{Name: p.Name, Tags: tagsCopy, Meta: metaCopy}\n}\n\nfunc main() {\n\tp1 := &Profile{Name: \"Илья\", Tags: []string{\"go\", \"k8s\"}, Meta: &Metadata{Score: 100}}\n\tp2 := p1.Clone()\n\n\tp2.Tags[0] = \"python\"\n\tp2.Meta.Score = 50\n\n\tfmt.Println(\"Оригинал p1:\", p1.Tags, p1.Meta.Score)\n\tfmt.Println(\"Клон     p2:\", p2.Tags, p2.Meta.Score)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Оригинал p1: [go k8s] 100\n# Клон     p2: [python k8s] 50"
      }
    ],
    "under_the_hood": "Выделяются новые участки кучи для слайса и подструктуры.",
    "pitfalls": "- Использование обычного присваивания p2 := *p1 (скопирует только указатели).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как быстро сделать Deep Copy сложного графа объектов в Go?»\n**Ответ:** Через `encoding/gob` или кастомный метод `Clone()`. Ручной метод `Clone()` в 10–20 раз быстрее сериализаторов."
  },
  {
    "num": 85,
    "title": "Конструктор пользователя NewUser: строгая валидация email и минимальной длины пароля",
    "task": "Конструктор с валидацией: NewUser(email, password string) (*User, error). Валидация: email содержит '@' и '.', пароль не менее 8 символов. При ошибке возвращается nil и понятная ошибка.",
    "theory": "Гарантия создания только валидных доменных сущностей.",
    "step_by_step": "1. Создаем User{email, pass}.\n2. Реализуем NewUser с проверками.\n3. Проверяем граничные условия.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n\t\"strings\"\n)\n\ntype UserEntity struct {\n\temail    string\n\tpassword string\n}\n\nfunc NewUser(email, pass string) (*UserEntity, error) {\n\tif !strings.Contains(email, \"@\") || !strings.Contains(email, \".\") {\n\t\treturn nil, errors.New(\"некорректный формат email\")\n\t}\n\tif len(pass) < 8 {\n\t\treturn nil, errors.New(\"пароль должен содержать не менее 8 символов\")\n\t}\n\treturn &UserEntity{email: email, password: pass}, nil\n}\n\nfunc main() {\n\tu, err := NewUser(\"teamlead@ozon.ru\", \"secretPass2026\")\n\tif err != nil { panic(err) }\n\tfmt.Println(\"Успешно создан:\", u.email)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Успешно создан: teamlead@ozon.ru"
      }
    ],
    "under_the_hood": "При ошибке аллокация структуры User не происходит.",
    "pitfalls": "- Пропуск проверки на пустые строки.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Go не используют исключения (exceptions) при валидации конструкторов?»\n**Ответ:** В Go ошибки являются обычными значениями (Errors as Values), что делает поток управления предсказуемым и явным."
  },
  {
    "num": 86,
    "title": "Паттерн Middleware на функциях: цепочка промежуточных обработчиков Logging и Auth",
    "task": "Паттерн Middleware: type HandlerFunc func(string) string, type Middleware func(HandlerFunc) HandlerFunc. Напиши middleware LoggingMiddleware и AuthMiddleware. Примени их к базовому хендлеру через цепочку.",
    "theory": "Композиция функций через паттерн Middleware в стиле standard library / chi / echo.",
    "step_by_step": "1. Объявляем HandlerFunc и Middleware.\n2. Реализуем LoggingMiddleware и AuthMiddleware.\n3. Оборачиваем базовый обработчик и вызываем.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n)\n\ntype HandlerFunc func(req string) string\ntype Middleware func(HandlerFunc) HandlerFunc\n\nfunc LoggingMiddleware(next HandlerFunc) HandlerFunc {\n\treturn func(req string) string {\n\t\tfmt.Printf(\"[LOG]: Получен запрос %q\\n\", req)\n\t\treturn next(req)\n\t}\n}\n\nfunc AuthMiddleware(next HandlerFunc) HandlerFunc {\n\treturn func(req string) string {\n\t\tif strings.Contains(req, \"admin\") {\n\t\t\treturn next(req)\n\t\t}\n\t\treturn \"403 Forbidden\"\n\t}\n}\n\nfunc main() {\n\tbaseHandler := func(req string) string { return \"200 OK: \" + req }\n\n\t// Сборка цепочки:\n\tchain := LoggingMiddleware(AuthMiddleware(baseHandler))\n\n\tfmt.Println(\"Ответ 1:\", chain(\"user_action\"))\n\tfmt.Println(\"Ответ 2:\", chain(\"admin_action\"))\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# [LOG]: Получен запрос \"user_action\"\n# Ответ 1: 403 Forbidden\n# [LOG]: Получен запрос \"admin_action\"\n# Ответ 2: 200 OK: admin_action"
      }
    ],
    "under_the_hood": "Замыкания образуют конвейер вызовов (Pipeline).",
    "pitfalls": "- Не передавать вызов next(req) при успешной проверке.",
    "bigtech_interview": "**Вопрос с собеседования:** «В каком порядке выполняются middleware при вызове `M1(M2(Handler))`?»\n**Ответ:** M1 (до next) -> M2 (до next) -> Handler -> M2 (после next) -> M1 (после next) — принцип луковой шелухи (Onion Architecture)."
  },
  {
    "num": 87,
    "title": "Встраивание неэкспортируемой структуры: Car встраивает engine, видимость методов снаружи",
    "task": "Встраивание неэкспортируемой структуры: пакет vehicle содержит приватную структуру engine с публичным методом Start(). Экспортируемая структура Car встраивает engine. Покажи, что метод Start доступен снаружи пакета, хотя сам тип engine невидим.",
    "theory": "Методы встроенного приватного типа всплывают наружу, если они экспортированы (начинаются с заглавной буквы).",
    "step_by_step": "1. Моделируем приватный тип internalEngine с методом Start().\n2. Экспортируем Car со встраиванием internalEngine.\n3. Вызываем car.Start() из main.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\n// Имитация пакета vehicle:\ntype internalEngine struct{}\n\n// Метод Start() экспортируемый (с заглавной буквы)!\nfunc (internalEngine) Start() {\n\tfmt.Println(\"🚀 Двигатель запущен через promoted метод!\")\n}\n\ntype Car struct {\n\tinternalEngine // Приватное встраивание\n\tModel          string\n}\n\nfunc main() {\n\tc := Car{Model: \"Tesla\"}\n\n\t// Снаружи пакета метод Start() доступен напрямую:\n\tc.Start()\n\n\t// Но обратиться к c.internalEngine напрямую нельзя (оно неэкспортировано)!\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# 🚀 Двигатель запущен через promoted метод!"
      }
    ],
    "under_the_hood": "Компилятор экспортирует метод Start в таблице символов структуры Car.",
    "pitfalls": "- Попытка объявить метод неэкспортируемым `start()` в надежде, что он станет публичным.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем встраивать приватные структуры с публичными методами?»\n**Ответ:** Чтобы скрыть внутреннюю реализацию и имя типа, но предоставить готовый интерфейс (например, `sync.Mutex.Lock()`)."
  },
  {
    "num": 88,
    "title": "Потокобезопасная коллекция ThreadSafeMap с инкапсуляцией sync.RWMutex",
    "task": "Потокобезопасная коллекция: структура ThreadSafeMap[K comparable, V any] с приватным sync.RWMutex и приватной map. Методы Set(k, v), Get(k) (v, bool), Delete(k), Len() int.",
    "theory": "RWMutex позволяет множественное параллельное чтение и эксклюзивную запись.",
    "step_by_step": "1. Объявляем дженерик-структуру ThreadSafeMap[K comparable, V any].\n2. Реализуем Set, Get, Delete, Len с RLock/Lock.\n3. Проверяем в конкурентных горутинах.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n)\n\ntype ThreadSafeMap[K comparable, V any] struct {\n\tmu   sync.RWMutex\n\tdata map[K]V\n}\n\nfunc NewThreadSafeMap[K comparable, V any]() *ThreadSafeMap[K, V] {\n\treturn &ThreadSafeMap[K, V]{data: make(map[K]V)}\n}\n\nfunc (m *ThreadSafeMap[K, V]) Set(k K, v V) {\n\tm.mu.Lock()\n\tdefer m.mu.Unlock()\n\tm.data[k] = v\n}\n\nfunc (m *ThreadSafeMap[K, V]) Get(k K) (V, bool) {\n\tm.mu.RLock()\n\tdefer m.mu.RUnlock()\n\tval, ok := m.data[k]\n\treturn val, ok\n}\n\nfunc main() {\n\tsm := NewThreadSafeMap[string, int]()\n\tsm.Set(\"users_online\", 1420)\n\tval, _ := sm.Get(\"users_online\")\n\tfmt.Println(\"Онлайн:\", val)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run -race main.go\n# Онлайн: 1420"
      }
    ],
    "under_the_hood": "RWMutex разделяет горутины чтения без взаимных блокировок.",
    "pitfalls": "- Забыть `defer m.mu.RUnlock()` в Get.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда `sync.Map` из стандартной библиотеки лучше `RWMutex + map`?»\n**Ответ:** Когда ключи пишутся один раз, а читаются миллионы раз, или когда несколько горутин обращаются к непересекающимся наборам ключей."
  },
  {
    "num": 89,
    "title": "Паттерн Цепочка Обязанностей (Chain of Responsibility): последовательная обработка запроса",
    "task": "Паттерн Chain of Responsibility: интерфейс Handler с методами SetNext(Handler) Handler и Handle(req *Request) error. Реализуй цепочку: AuthHandler -> RateLimitHandler -> BusinessHandler.",
    "theory": "Паттерн позволяет передавать запрос по цепочке потенциальных обработчиков.",
    "step_by_step": "1. Объявляем интерфейс Handler.\n2. Реализуем AuthHandler, RateLimitHandler, BusinessHandler.\n3. Связываем через SetNext и запускаем запрос.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Request struct {\n\tUser  string\n\tLimit int\n}\n\ntype Handler interface {\n\tSetNext(Handler) Handler\n\tHandle(*Request) error\n}\n\ntype BaseHandler struct {\n\tnext Handler\n}\n\nfunc (b *BaseHandler) SetNext(h Handler) Handler { b.next = h; return h }\n\ntype AuthHandler struct{ BaseHandler }\nfunc (a *AuthHandler) Handle(r *Request) error {\n\tif r.User == \"\" { return fmt.Errorf(\"ошибка авторизации\") }\n\tfmt.Println(\"✅ Авторизация пройдена\")\n\tif a.next != nil { return a.next.Handle(r) }\n\treturn nil\n}\n\ntype BusinessHandler struct{ BaseHandler }\nfunc (b *BusinessHandler) Handle(r *Request) error {\n\tfmt.Println(\"🚀 Бизнес-логика выполнена для\", r.User)\n\treturn nil\n}\n\nfunc main() {\n\tauth := &AuthHandler{}\n\tbiz := &BusinessHandler{}\n\tauth.SetNext(biz)\n\n\t_ = auth.Handle(&Request{User: \"Дмитрий\"})\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# ✅ Авторизация пройдена\n# 🚀 Бизнес-логика выполнена для Дмитрий"
      }
    ],
    "under_the_hood": "Запросы последовательно обходят связный список обработчиков.",
    "pitfalls": "- Бесконечный цикл при циклической ссылке в SetNext.",
    "bigtech_interview": "**Вопрос с собеседования:** «Где паттерн Chain of Responsibility применяется в веб-серверах?»\n**Ответ:** В цепочках HTTP-фильтров, перехватчиках gRPC Interceptors и конвейерах обработки сообщений."
  },
  {
    "num": 90,
    "title": "Композиция интерфейсов Repository: объединение Reader, Writer и Deleter в единый CRUD-контракт",
    "task": "Композиция интерфейсов: интерфейсы Reader[T], Writer[T], Deleter. Интерфейс Repository[T] встраивает все три. Реализуй InMemoryRepository[T] удовлетворяющий Repository.",
    "theory": "Дженерик-интерфейсы и композиция контрактов для слоя персистентности.",
    "step_by_step": "1. Объявляем Reader, Writer, Deleter и Repository.\n2. Реализуем InMemoryRepo[T].\n3. Проверяем CRUD-операции.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Reader[T any] interface { Get(id int) (T, bool) }\ntype Writer[T any] interface { Save(id int, val T) }\ntype Deleter interface { Delete(id int) }\n\ntype Repository[T any] interface {\n\tReader[T]\n\tWriter[T]\n\tDeleter\n}\n\ntype InMemoryRepo[T any] struct {\n\tstore map[int]T\n}\n\nfunc NewInMemoryRepo[T any]() *InMemoryRepo[T] {\n\treturn &InMemoryRepo[T]{store: make(map[int]T)}\n}\n\nfunc (r *InMemoryRepo[T]) Get(id int) (T, bool) { v, ok := r.store[id]; return v, ok }\nfunc (r *InMemoryRepo[T]) Save(id int, val T)   { r.store[id] = val }\nfunc (r *InMemoryRepo[T]) Delete(id int)        { delete(r.store, id) }\n\nfunc main() {\n\tvar repo Repository[string] = NewInMemoryRepo[string]()\n\trepo.Save(1, \"Запись 1\")\n\tv, _ := repo.Get(1)\n\tfmt.Println(\"Прочитано:\", v)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Прочитано: Запись 1"
      }
    ],
    "under_the_hood": "Таблица методов itab включает все методы составного интерфейса.",
    "pitfalls": "- Избыточная связанность, если сервису нужен только Reader.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в функциях бизнес-логики лучше принимать Reader[T], а не Repository[T]?»\n**Ответ:** Чтобы изолировать бизнес-логику и защитить данные от случайной модификации (Interface Segregation Principle)."
  },
  {
    "num": 91,
    "title": "Паттерн Адаптер (Adapter Pattern): адаптация LegacyPrinter к интерфейсу ModernPrinter",
    "task": "Паттерн «Адаптер» (Adapter): есть устаревший LegacyPrinter (метод PrintOld(text string)). Новый код ожидает интерфейс ModernPrinter (метод PrintFormatted(header, body string)). Напиши адаптер PrinterAdapter.",
    "theory": "Адаптер преобразует интерфейс одного класса в интерфейс, ожидаемый клиентами.",
    "step_by_step": "1. Создаем LegacyPrinter{ PrintOld(string) }.\n2. Объявляем интерфейс ModernPrinter.\n3. Создаем PrinterAdapter со встраиванием LegacyPrinter.\n4. Реализуем PrintFormatted.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype LegacyPrinter struct{}\nfunc (LegacyPrinter) PrintOld(text string) {\n\tfmt.Println(\"=== LEGACY PRINT ===\\n\" + text)\n}\n\ntype ModernPrinter interface {\n\tPrintFormatted(header, body string)\n}\n\ntype PrinterAdapter struct {\n\tlegacy LegacyPrinter\n}\n\nfunc (a PrinterAdapter) PrintFormatted(header, body string) {\n\tformatted := fmt.Sprintf(\"[%s]\n%s\", header, body)\n\ta.legacy.PrintOld(formatted)\n}\n\nfunc main() {\n\tvar p ModernPrinter = PrinterAdapter{legacy: LegacyPrinter{}}\n\tp.PrintFormatted(\"Отчет\", \"Все системы работают стабильно\")\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# === LEGACY PRINT ===\n# [Отчет]\n# Все системы работают стабильно"
      }
    ],
    "under_the_hood": "Адаптер инкапсулирует вызов устаревшего API внутри нового контракта.",
    "pitfalls": "- Прямая модификация устаревшего кода вместо написания адаптера.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда в Go необходим паттерн Адаптер?»\n**Ответ:** При интеграции внешних SDK или при постепенном рефакторинге легаси систем."
  },
  {
    "num": 92,
    "title": "Инициализация вложенных структур: фабричный конструктор NewCar(model, engine)",
    "task": "Инициализация вложенных структур: Car содержит Engine (структура). Напиши конструктор NewCar(model string, hp int) Car, который корректно инициализирует и внешнюю, и внутреннюю структуру.",
    "theory": "Явная инициализация всех уровней композиции в конструкторе.",
    "step_by_step": "1. Создаем Engine{HP int}.\n2. Создаем Car{Model string, Engine Engine}.\n3. Пишем NewCar.\n4. Тестируем.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Engine struct{ HorsePower int }\n\ntype Car struct {\n\tModel  string\n\tEngine Engine\n}\n\nfunc NewCar(model string, hp int) Car {\n\treturn Car{\n\t\tModel:  model,\n\t\tEngine: Engine{HorsePower: hp},\n\t}\n}\n\nfunc main() {\n\tc := NewCar(\"BMW M5\", 600)\n\tfmt.Printf(\"Авто: %s, Мощность: %d л.с.\\n\", c.Model, c.Engine.HorsePower)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Авто: BMW M5, Мощность: 600 л.с."
      }
    ],
    "under_the_hood": "Конструктор собирает структуру в единый непрерывный блок памяти.",
    "pitfalls": "- Оставлять поля Engine неинициализированными (нулевыми).",
    "bigtech_interview": "**Вопрос с собеседования:** «Что возвращать из конструктора: значение `Car` или указатель `*Car`?»\n**Ответ:** Значение `Car`, если структура маленькая и не содержит мьютексов; указатель `*Car`, если структура крупная, содержит мьютексы или требует мутации через методы."
  },
  {
    "num": 93,
    "title": "Защита от создания структуры через литерал: приватный тип и фабрика GetInstance()",
    "task": "Ограничение создания: пакет appinfo. Структура Info не может быть создана через appinfo.Info{} из main (сделай структуру приватной info или запрети создание без конструктора, сделав приватное неэкспортируемое поле). Доступ только через GetInfo().",
    "theory": "Добавление неэкспортируемого поля `_ struct{}` предотвращает прямое создание структуры через литерал без конструктора из других пакетов.",
    "step_by_step": "1. Моделируем структуру с неэкспортируемым маркером.\n2. Экспортируем функцию GetInfo().\n3. Показываем защиту.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype AppInfo struct {\n\tVersion   string\n\tBuildTime string\n\t_         struct{} // Предотвращает литеральную инициализацию без имен полей\n}\n\nfunc GetAppInfo() AppInfo {\n\treturn AppInfo{\n\t\tVersion:   \"v1.22.4\",\n\t\tBuildTime: \"2026-09-02\",\n\t}\n}\n\nfunc main() {\n\tinfo := GetAppInfo()\n\tfmt.Printf(\"Версия: %s (Сборка: %s)\\n\", info.Version, info.BuildTime)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Версия: v1.22.4 (Сборка: 2026-09-02)"
      }
    ],
    "under_the_hood": "Пустая структура `struct{}` имеет нулевой размер (0 байт) и не расходует память.",
    "pitfalls": "- Попытка создать неименованный литерал `AppInfo{\"v1\", \"time\"}` вызовет ошибку компиляции.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем в структуре поле `_ struct{}`?»\n**Ответ:** Чтобы запретить позиционную инициализацию `Type{\"a\", \"b\"}` и заставить разработчиков явно указывать имена полей или использовать конструктор."
  },
  {
    "num": 94,
    "title": "Пакет auth: структуры Token и Session с инкапсуляцией времени жизни и валидации",
    "task": "Пакет auth: структуры Token (значение, expiresAt) и Session (userID, token). Методы IsExpired() bool, IsValid() bool. Инкапсулируй проверку времени жизни токена.",
    "theory": "Инкапсуляция валидации токенов авторизации внутри доменного метода.",
    "step_by_step": "1. Создаем Token{Value, ExpiresAt time.Time}.\n2. Создаем Session{UserID, Token}.\n3. Реализуем IsExpired() и IsValid().",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"time\"\n)\n\ntype Token struct {\n\tValue     string\n\tExpiresAt time.Time\n}\n\nfunc (t Token) IsExpired() bool {\n\treturn time.Now().After(t.ExpiresAt)\n}\n\ntype Session struct {\n\tUserID int\n\tToken  Token\n}\n\nfunc (s Session) IsValid() bool {\n\treturn s.UserID > 0 && !s.Token.IsExpired()\n}\n\nfunc main() {\n\tsess := Session{\n\t\tUserID: 42,\n\t\tToken: Token{\n\t\t\tValue:     \"jwt_secure_token\",\n\t\t\tExpiresAt: time.Now().Add(1 * time.Hour),\n\t\t},\n\t}\n\tfmt.Println(\"Сессия активна?\", sess.IsValid())\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Сессия активна? true"
      }
    ],
    "under_the_hood": "Сравнение времени через time.Now().After().",
    "pitfalls": "- Игнорирование часовых поясов при сравнении времени.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как тестировать методы, зависящие от `time.Now()`?»\n**Ответ:** Инжектировать интерфейс часов `Clock { Now() time.Time }` или передавать текущее время аргументом."
  },
  {
    "num": 95,
    "title": "Паттерн Команда (Command Pattern): абстракция действий с поддержкой Execute и Undo",
    "task": "Паттерн «Команда» (Command): интерфейс Command с методами Execute() error и Undo() error. Реализуйте команды WriteTextCommand и DeleteTextCommand. Структура Button или History хранит и исполняет команды с возможностью отката.",
    "theory": "Инкапсуляция запроса как объекта для поддержки истории и отмены операций (Undo).",
    "step_by_step": "1. Объявляем интерфейс Command.\n2. Создаем Document{ text string }.\n3. Реализуем AppendTextCommand с Execute и Undo.\n4. Тестируем историю выполнения.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Command interface {\n\tExecute()\n\tUndo()\n}\n\ntype Document struct{ Content string }\n\ntype AppendTextCommand struct {\n\tdoc  *Document\n\ttext string\n}\n\nfunc (c *AppendTextCommand) Execute() { c.doc.Content += c.text }\nfunc (c *AppendTextCommand) Undo()    { c.doc.Content = c.doc.Content[:len(c.doc.Content)-len(c.text)] }\n\nfunc main() {\n\tdoc := &Document{}\n\tcmd := &AppendTextCommand{doc: doc, text: \"Привет, Мир!\"}\n\n\tcmd.Execute()\n\tfmt.Println(\"После Execute:\", doc.Content)\n\n\tcmd.Undo()\n\tfmt.Println(\"После Undo:   \", doc.Content)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# После Execute: Привет, Мир!\n# После Undo:    "
      }
    ],
    "under_the_hood": "Команды хранят контекст для восстановления предыдущего состояния.",
    "pitfalls": "- Попытка отката Undo без предварительного Execute.",
    "bigtech_interview": "**Вопрос с собеседования:** «Где паттерн Command применяется в backend-системах?»\n**Ответ:** В CQRS архитектуре, сагах транзакций (Saga Pattern) для компенсирующих транзакций и в очередях фоновых задач."
  },
  {
    "num": 96,
    "title": "Методы с поддержкой context.Context: корректная обработка отмены операции и таймаутов",
    "task": "Методы с context.Context: структура DataFetcher (метод Fetch(ctx context.Context, url string) ([]byte, error)). Метод уважает ctx.Done() и возвращает ошибку при отмене контекста.",
    "theory": "Передача context.Context первым параметром — обязательный стандарт для всех I/O и долгих операций в Go.",
    "step_by_step": "1. Создаем DataFetcher{}.\n2. Реализуем Fetch(ctx context.Context, query string).\n3. Проверяем поведение при time.WithTimeout.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"time\"\n)\n\ntype DataFetcher struct{}\n\nfunc (df DataFetcher) Fetch(ctx context.Context, query string) (string, error) {\n\tselect {\n\tcase <-time.After(100 * time.Millisecond):\n\t\treturn \"Данные по запросу: \" + query, nil\n\tcase <-ctx.Done():\n\t\treturn \"\", ctx.Err()\n\t}\n}\n\nfunc main() {\n\tdf := DataFetcher{}\n\n\t// Таймаут 50мс (операция требует 100мс):\n\tctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)\n\tdefer cancel()\n\n\t_, err := df.Fetch(ctx, \"analytics\")\n\tif err != nil {\n\t\tfmt.Println(\"❌ Запрос отменен по таймауту:\", err)\n\t}\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# ❌ Запрос отменен по таймауту: context deadline exceeded"
      }
    ],
    "under_the_hood": "Канал `ctx.Done()` закрывается при отмене таймера рантайма.",
    "pitfalls": "- Сохранение `context.Context` внутри структуры вместо передачи первым аргументом метода.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему нельзя хранить `context.Context` внутри полей структуры?»\n**Ответ:** Это нарушает официальные правила Go: контекст имеет время жизни одного запроса и должен передаваться явно по стеку вызовов, иначе возникают гонки данных и утечки контекстов."
  }
]
