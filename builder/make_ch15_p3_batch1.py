import json

part3 = []

# Ex 66-76
part3.append({
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
})

part3.append({
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
})

part3.append({
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
})

part3.append({
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
})

part3.append({
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
})

part3.append({
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
})

part3.append({
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
})

part3.append({
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
})

part3.append({
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
})

part3.append({
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
})

part3.append({
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
})

print(f"Batch 1 of Part 3: {len(part3)} exercises.")
with open('builder/gen_ch15_p3_batch1.json', 'w', encoding='utf-8') as f:
    json.dump(part3, f, ensure_ascii=False, indent=2)
