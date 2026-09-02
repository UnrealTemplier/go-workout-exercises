import json

part3 = []

# Ex 77-86
part3.append({
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
})

part3.append({
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
})

part3.append({
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
})

part3.append({
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
})

part3.append({
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
})

part3.append({
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
})

part3.append({
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
})

part3.append({
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
})

part3.append({
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
})

part3.append({
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
})

print(f"Batch 2 of Part 3: {len(part3)} exercises.")
with open('builder/gen_ch15_p3_batch2.json', 'w', encoding='utf-8') as f:
    json.dump(part3, f, ensure_ascii=False, indent=2)
