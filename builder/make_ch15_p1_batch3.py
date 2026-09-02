import json

part3 = []

# Ex 23-33
part3.append({
    "num": 23,
    "title": "Методы на кастомных срезах: type IntSlice []int и безопасное суммирование nil-среза",
    "task": "Реализуй метод на nil slice: type IntSlice []int, метод (s IntSlice) Sum() int. Вызови (IntSlice(nil)).Sum() — покажи, что nil slice ведёт себя как пустой слайс внутри метода.",
    "theory": "Срез nil имеет len=0 и cap=0, обход через for range выполняется 0 раз без паники.",
    "step_by_step": "1. Объявляем type IntSlice []int.\n2. Реализуем метод Sum() int.\n3. Вызываем на IntSlice(nil).",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype IntSlice []int\n\nfunc (s IntSlice) Sum() int {\n\ttotal := 0\n\tfor _, v := range s {\n\t\ttotal += v\n\t}\n\treturn total\n}\n\nfunc main() {\n\tvar s IntSlice = nil\n\tfmt.Printf(\"Сумма nil slice: %d\\n\", s.Sum())\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Сумма nil slice: 0"
        }
    ],
    "under_the_hood": "Дескриптор среза {Data: 0, Len: 0, Cap: 0} передается в функцию.",
    "pitfalls": "- Прямое обращение s[0] на nil слайсе.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему len(nil) равен 0?»\n**Ответ:** Поле Len заголовка nil-слайса равно 0."
})

part3.append({
    "num": 24,
    "title": "Автоматическое разыменование: вызов Value Receiver метода у указателя на структуру",
    "task": "Изучите обратный случай: можно ли вызвать метод с value receiver у указателя на структуру? Проверьте на практике.",
    "theory": "Вызов ptr.ValueMethod() компилируется в (*ptr).ValueMethod().",
    "step_by_step": "1. Создаем Config{Host string, Port int}.\n2. Реализуем Address() string с Value Receiver.\n3. Вызываем на указателе &Config{}.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Config struct {\n\tHost string\n\tPort int\n}\n\nfunc (c Config) Address() string {\n\treturn fmt.Sprintf(\"%s:%d\", c.Host, c.Port)\n}\n\nfunc main() {\n\tptr := &Config{Host: \"127.0.0.1\", Port: 8080}\n\tfmt.Printf(\"Адрес: %s\\n\", ptr.Address())\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Адрес: 127.0.0.1:8080"
        }
    ],
    "under_the_hood": "Компилятор вставляет инструкцию загрузки структуры из памяти.",
    "pitfalls": "- Вызов на nil-указателе приведет к панике при разыменовании.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему вызов value-метода на nil-указателе падает?»\n**Ответ:** Для создания копии значения рантайм обязан разыменовать указатель *ptr."
})

part3.append({
    "num": 25,
    "title": "Раздельная реализация String() для T и *T: выбор метода в интерфейсе fmt.Stringer",
    "task": "Объяви метод String() string для типа T и отдельно для *T с разной реализацией. Создай переменные var t T и var p *T, присвой интерфейсу fmt.Stringer. Покажи, какой метод выбирается в каждом случае и почему.",
    "theory": "Method set для T содержит только value методы, а для *T — и value, и pointer методы.",
    "step_by_step": "1. Создаем ItemValue и ItemPointer.\n2. Присваиваем интерфейсу fmt.Stringer.\n3. Анализируем вывод.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype ItemValue struct{ Name string }\nfunc (i ItemValue) String() string { return \"[Value]: \" + i.Name }\n\ntype ItemPointer struct{ Name string }\nfunc (i *ItemPointer) String() string { return \"[Pointer]: \" + i.Name }\n\nfunc main() {\n\tv := ItemValue{\"А\"}\n\tp := &ItemPointer{\"Б\"}\n\tvar s1 fmt.Stringer = v\n\tvar s2 fmt.Stringer = p\n\tfmt.Println(s1.String())\n\tfmt.Println(s2.String())\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# [Value]: А\n# [Pointer]: Б"
        }
    ],
    "under_the_hood": "Таблица itab строится на точном совпадении типов получателей.",
    "pitfalls": "- Передача значения структуры с Pointer Stringer в fmt.Println.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему fmt.Printf(\"%s\", val) не всегда вызывает String()?»\n**Ответ:** Если метод объявлен на *T, а передано значение T, Stringer не найден в method set."
})

part3.append({
    "num": 26,
    "title": "Множественное встраивание интерфейсов: композиция io.Reader и io.Writer в кастомном буфере",
    "task": "Множественное встраивание: структура ReadWriter встраивает io.Reader и io.Writer. Реализуйте для своего типа (например, буфер), удовлетворяющего обоим интерфейсам.",
    "theory": "Композиция стандартных потоковых контрактов.",
    "step_by_step": "1. Создаем CustomReadWriter с bytes.Buffer.\n2. Реализуем Read и Write.\n3. Проверяем совместимость с io.ReadWriter.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport (\n\t\"bytes\"\n\t\"fmt\"\n\t\"io\"\n)\n\ntype CustomReadWriter struct {\n\tbuf bytes.Buffer\n}\n\nfunc (c *CustomReadWriter) Read(p []byte) (int, error)  { return c.buf.Read(p) }\nfunc (c *CustomReadWriter) Write(p []byte) (int, error) { return c.buf.Write(p) }\n\nfunc main() {\n\tvar rw io.ReadWriter = &CustomReadWriter{}\n\tfmt.Fprintf(rw, \"Привет, Поток!\")\n\tout, _ := io.ReadAll(rw)\n\tfmt.Printf(\"Прочитано: %q\\n\", string(out))\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Прочитано: \"Привет, Поток!\""
        }
    ],
    "under_the_hood": "Композитный интерфейс объединяет таблицы методов io.Reader и io.Writer.",
    "pitfalls": "- Не возвращать io.EOF в конце потока чтения.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как устроен io.ReadWriter?»\n**Ответ:** Как встраивание интерфейсов type ReadWriter interface { Reader; Writer }."
})

part3.append({
    "num": 27,
    "title": "Паттерн Fluent Interface: каскадная конфигурация точки p.WithX(10).WithY(20).String()",
    "task": "Реализуй method chaining (fluent interface): type Point struct { x, y float64 }, методы WithX(x float64) *Point, WithY(y float64) *Point, String() string. Каждый метод возвращает *Point для цепочки: p.WithX(10).WithY(20).String().",
    "theory": "Fluent Interface с возвратом указателя *Point.",
    "step_by_step": "1. Создаем Point.\n2. Реализуем WithX, WithY, String.\n3. Собираем цепочку вызовов.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Point struct{ x, y float64 }\n\nfunc (p *Point) WithX(x float64) *Point { p.x = x; return p }\nfunc (p *Point) WithY(y float64) *Point { p.y = y; return p }\nfunc (p *Point) String() string          { return fmt.Sprintf(\"Point(%.1f, %.1f)\", p.x, p.y) }\n\nfunc main() {\n\tp := &Point{}\n\tfmt.Println(p.WithX(10).WithY(20).String())\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Point(10.0, 20.0)"
        }
    ],
    "under_the_hood": "Адрес объекта передается через регистры CPU.",
    "pitfalls": "- Вызов цепочки на значении без указателя.",
    "bigtech_interview": "**Вопрос с собеседования:** «Где в Go чаще всего применяется Fluent Interface?»\n**Ответ:** В построителях SQL-запросов и HTTP-клиентах."
})

part3.append({
    "num": 28,
    "title": "Фабричный метод-конструктор NewRectangle(w, h float64) с валидацией геометрических размеров",
    "task": "Создайте фабричный метод (конструктор) NewRectangle(w, h float64) *Rectangle, который валидирует входные данные (ширина и высота > 0) и возвращает error, если они невалидны.",
    "theory": "Конструктор с проверкой инвариантов и возвратом error.",
    "step_by_step": "1. Создаем Rectangle.\n2. Пишем NewRectangle(w, h) (*Rectangle, error).\n3. Проверяем валидные и невалидные параметры.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n)\n\ntype Rectangle struct{ w, h float64 }\n\nfunc NewRectangle(w, h float64) (*Rectangle, error) {\n\tif w <= 0 || h <= 0 {\n\t\treturn nil, errors.New(\"размеры должны быть больше 0\")\n\t}\n\treturn &Rectangle{w: w, h: h}, nil\n}\n\nfunc main() {\n\tr, err := NewRectangle(10, 5)\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tfmt.Printf(\"Прямоугольник: %.1f x %.1f\\n\", r.w, r.h)\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Прямоугольник: 10.0 x 5.0"
        }
    ],
    "under_the_hood": "При ошибке возвращается nil-указатель.",
    "pitfalls": "- Возврат неинициализированной структуры вместо nil.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как именовать конструкторы в Go?»\n**Ответ:** New() если пакет узкоспециализирован, или NewTypeName()."
})

part3.append({
    "num": 29,
    "title": "Ad-hoc Interface (Анонимный интерфейс по месту использования) для функции MakeSound",
    "task": "Объяви два типа Dog и Cat с одинаковым методом Speak() string. Напиши функцию MakeSound(speaker interface{ Speak() string }), принимающую любой тип с методом Speak. Покажи ad-hoc interface (неявный интерфейс) в действии.",
    "theory": "Анонимные интерфейсы прямо в параметрах функций.",
    "step_by_step": "1. Создаем Dog и Cat с методом Speak().\n2. Пишем MakeSound(speaker interface{ Speak() string }).\n3. Передаем обе структуры.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Dog struct{}\nfunc (Dog) Speak() string { return \"Гав!\" }\n\ntype Cat struct{}\nfunc (Cat) Speak() string { return \"Мяу!\" }\n\nfunc MakeSound(speaker interface{ Speak() string }) {\n\tfmt.Println(speaker.Speak())\n}\n\nfunc main() {\n\tMakeSound(Dog{})\n\tMakeSound(Cat{})\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Гав!\n# Мяу!"
        }
    ],
    "under_the_hood": "Компилятор строит анонимный тип интерфейса и таблицу itab.",
    "pitfalls": "- Дублирование одинаковых ad-hoc интерфейсов во многих функциях.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда использовать ad-hoc интерфейс?»\n**Ответ:** Для локальных утилит с одним методом без необходимости экспорта."
})

part3.append({
    "num": 30,
    "title": "Безопасная печать связного списка: метод PrintValue() на nil-указателе структуры Node",
    "task": "Nil-ресиверы: Создай структуру Node (элемент связного списка). Напиши метод func (n *Node) PrintValue(). Внутри метода в самом начале напиши if n == nil { fmt.Println(\"nil\"); return }. В main объяви var n *Node = nil и вызови n.PrintValue(). Убедись, что паники нет! (В Go методы можно безопасно вызывать у nil-указателей, если внутри есть проверка).",
    "theory": "Nil-получатели защищают методы от крашей.",
    "step_by_step": "1. Создаем Node{val int}.\n2. Реализуем (n *Node) PrintValue() с проверкой nil.\n3. Вызываем на nil.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Node struct{ val int }\n\nfunc (n *Node) PrintValue() {\n\tif n == nil {\n\t\tfmt.Println(\"nil\")\n\t\treturn\n\t}\n\tfmt.Println(\"Value:\", n.val)\n}\n\nfunc main() {\n\tvar n *Node = nil\n\tn.PrintValue()\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# nil"
        }
    ],
    "under_the_hood": "Рантайм передает адрес 0x0 в качестве первого аргумента.",
    "pitfalls": "- Разыменование полей до проверки на nil.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Go не падает вызов nil.Method()?»\n**Ответ:** Потому что вызовы методов статические, а не через vtable объекта."
})

part3.append({
    "num": 31,
    "title": "Композиция вместо наследования: анонимное встраивание структуры Engine в структуру Car",
    "task": "Композиция вместо наследования: Создайте структуру Engine с методом Start(). Создайте структуру Car, встроив в неё Engine анонимно. Продемонстрируйте вызов метода car.Start(). Объясните, как композиция заменяет наследование классов.",
    "theory": "Встраивание структур (Embedding) обеспечивает всплытие методов (Method Promotion).",
    "step_by_step": "1. Создаем Engine{HP int} с методом Start().\n2. Создаем Car со встраиванием Engine.\n3. Вызываем car.Start().",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Engine struct{ HP int }\nfunc (e Engine) Start() { fmt.Printf(\"Двигатель %d л.с. запущен!\\n\", e.HP) }\n\ntype Car struct {\n\tEngine\n\tModel string\n}\n\nfunc main() {\n\tc := Car{Engine: Engine{HP: 200}, Model: \"Sedan\"}\n\tc.Start() // Method Promotion\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Двигатель 200 л.с. запущен!"
        }
    ],
    "under_the_hood": "Вызов c.Start() преобразуется в c.Engine.Start().",
    "pitfalls": "- Ожидание полиморфизма наследования.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Go нет наследования классов?»\n**Ответ:** Композиция безопаснее, исключает жесткую связанность и проблему хрупкого базового класса."
})

part3.append({
    "num": 32,
    "title": "Инкапсуляция банковского счета bank.Account с контролем отрицательного баланса",
    "task": "Реализуйте инкапсуляцию: создайте пакет bank со структурой Account. Сделайте поле balance приватным. Добавьте методы Deposit() и Withdraw(), которые не дают балансу уйти в минус (возвращая ошибку при нехватке средств).",
    "theory": "Инкапсуляция защищает баланс от овердрафта.",
    "step_by_step": "1. Создаем Account с приватным balance.\n2. Реализуем методы с проверками.\n3. Тестируем.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n)\n\ntype Account struct{ balance int }\n\nfunc (a *Account) Deposit(amt int) error {\n\tif amt <= 0 { return errors.New(\"неверная сумма\") }\n\ta.balance += amt\n\treturn nil\n}\n\nfunc (a *Account) Withdraw(amt int) error {\n\tif amt > a.balance { return errors.New(\"недостаточно средств\") }\n\ta.balance -= amt\n\treturn nil\n}\n\nfunc main() {\n\tacc := &Account{balance: 1000}\n\t_ = acc.Deposit(500)\n\t_ = acc.Withdraw(300)\n\tfmt.Println(\"Баланс:\", acc.balance)\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Баланс: 1200"
        }
    ],
    "under_the_hood": "Баланс модифицируется только через проверенные методы.",
    "pitfalls": "- Использование float без округления для денег.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как сделать счет потокобезопасным?»\n**Ответ:** Добавить sync.Mutex внутри Account."
})

part3.append({
    "num": 33,
    "title": "Методы на функциональных типах: type Handler func(string) string и реализация интерфейсов",
    "task": "Объяви тип Handler func(string) string. Создай метод (h Handler) Process(s string) string. Покажи, что функциональные типы тоже могут иметь методы, и Handler удовлетворяет интерфейсу с методом Process.",
    "theory": "Паттерн Function Adapter: методы на функциональных типах.",
    "step_by_step": "1. Объявляем интерфейс Processor{ Process(string) string }.\n2. Объявляем type Handler func(string) string.\n3. Реализуем метод Process.\n4. Адаптируем функцию к интерфейсу.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n)\n\ntype Processor interface {\n\tProcess(string) string\n}\n\ntype Handler func(string) string\n\nfunc (h Handler) Process(s string) string {\n\treturn h(s)\n}\n\nfunc main() {\n\tfn := Handler(func(s string) string { return strings.ToUpper(s) })\n\tvar p Processor = fn\n\tfmt.Println(p.Process(\"golang oop\"))\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# GOLANG OOP"
        }
    ],
    "under_the_hood": "Функция упаковывается в интерфейс iface с таблицей методов Handler.",
    "pitfalls": "- Забыть вызвать h(s) внутри Process.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как работает http.HandlerFunc?»\n**Ответ:** Это тип func(ResponseWriter, *Request), реализующий метод ServeHTTP."
})

print(f"Loaded batch 3: {len(part3)} exercises.")
with open('builder/gen_ch15_p1_batch3.json', 'w', encoding='utf-8') as f:
    json.dump(part3, f, ensure_ascii=False, indent=2)
