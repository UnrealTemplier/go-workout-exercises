import json

part1 = []

# Ex 1-10
part1.append({
    "num": 1,
    "title": "Методы для кастомных типов на базе примитивов: type MyDuration int и правило локальности пакета",
    "task": "Создайте кастомный тип на базе встроенного: type MyDuration int. Напишите для него метод ToMinutes() float64 и ToSeconds() int. Проверьте вызов методов на переменной этого типа. Объясните, почему нельзя объявлять методы для базовых типов (например, напрямую для int) или для типов из чужих пакетов.",
    "theory": "**Методы на пользовательских типах (Defined Types) и Receiver в Go:**\n- В Go методы можно объявлять для любого именованного типа, объявленного в том же пакете, кроме базовых встроенных примитивов (int, string, float64) и указателей *T;\n- Синтаксис type MyDuration int создает совершенно новый определенный тип (Defined Type), сохраняющий базовое представление памяти int, но изолирующий набор методов (Method Set);\n- **Правило локальности пакета (Package Locality Rule):** Запрещено добавлять методы к типам, объявленным в других пакетах (например, time.Duration или http.Request). Это предотвращает коллизии методов (Orphan Rule) и обеспечивает модульность.",
    "step_by_step": "1. Объявляем тип type MyDuration int (время в миллисекундах).\n2. Реализуем метод (d MyDuration) ToSeconds() int с получателем-значением (Value Receiver).\n3. Реализуем метод (d MyDuration) ToMinutes() float64.\n4. В main создаем переменную d := MyDuration(150000) и вызываем методы.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype MyDuration int\n\nfunc (d MyDuration) ToSeconds() int {\n\treturn int(d) / 1000\n}\n\nfunc (d MyDuration) ToMinutes() float64 {\n\treturn float64(d) / 60000.0\n}\n\nfunc main() {\n\td := MyDuration(150000)\n\tfmt.Printf(\"Длительность: %d мс\\n\", d)\n\tfmt.Printf(\"В секундах:   %d с\\n\", d.ToSeconds())\n\tfmt.Printf(\"В минутах:    %.2f мин\\n\", d.ToMinutes())\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Длительность: 150000 мс\n# В секундах:   150 с\n# В минутах:    2.50 мин"
        }
    ],
    "under_the_hood": "На уровне ассемблера метод func (d MyDuration) ToSeconds() int компилируется в обычную функцию main.MyDuration.ToSeconds(d MyDuration) int, где получатель (receiver) передается как первый скрытый параметр.",
    "pitfalls": "- Попытка вызвать метод кастомного типа на литерале базового типа без явного приведения: (150000).ToSeconds() вызовет ошибку cannot call pointer method or field on untyped int.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Go запрещено определять методы для типов из импортированных пакетов (например, func (t time.Time) CustomFormat())?»\n**Ответ:** Это фундаментальное архитектурное решение (Package Locality). Если бы два независимых пакета добавили метод с одинаковым именем CustomFormat() к time.Time, возник бы неразрешимый конфликт при линковке в третьем пакете."
})

part1.append({
    "num": 2,
    "title": "Вычисление расстояния Distance(other Point) и автоматическое разыменование получателя",
    "task": "Объяви тип Point с методом Distance(other Point) float64 (value receiver). Вычисли расстояние между двумя точками. Покажи, что метод можно вызвать и на значении, и на указателе (Go автоматически разыменовывает/берёт адрес).",
    "theory": "**Value Receiver и автоматическое разыменование (Automatic Dereferencing):**\n- Метод с Value Receiver (p Point) получает полную копию структуры в момент вызова;\n- Если метод вызывается на указателе ptr := &Point{}, компилятор Go автоматически преобразует вызов ptr.Distance(p2) в (*ptr).Distance(p2).",
    "step_by_step": "1. Создаем структуру Point с полями X, Y float64.\n2. Реализуем метод (p Point) Distance(other Point) float64 с формулой Евклидова расстояния.\n3. Создаем значение p1 и указатель pPtr := &p1.\n4. Демонстрируем эквивалентность вызовов.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"math\"\n)\n\ntype Point struct {\n\tX, Y float64\n}\n\nfunc (p Point) Distance(other Point) float64 {\n\tdx := p.X - other.X\n\tdy := p.Y - other.Y\n\treturn math.Sqrt(dx*dx + dy*dy)\n}\n\nfunc main() {\n\tp1 := Point{X: 0, Y: 0}\n\tp2 := Point{X: 3, Y: 4}\n\n\td1 := p1.Distance(p2)\n\tfmt.Printf(\"Расстояние (вызов на значении):   %.2f\\n\", d1)\n\n\tpPtr := &p1\n\td2 := pPtr.Distance(p2)\n\tfmt.Printf(\"Расстояние (вызов на указателе): %.2f\\n\", d2)\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Расстояние (вызов на значении):   5.00\n# Расстояние (вызов на указателе): 5.00"
        }
    ],
    "under_the_hood": "Компилятор анализирует AST и вставляет инструкцию загрузки значения из памяти перед вызовом.",
    "pitfalls": "- Использование Value Receiver для структур большого размера (>128 байт), что приводит к лишним аллокациям и копированию памяти при каждом вызове.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда следует выбирать Value Receiver, а когда Pointer Receiver?»\n**Ответ:** Value Receiver выбирают для маленьких иммутабельных типов (примитивы, маленькие структуры <= 16 байт). Pointer Receiver обязателен, если метод мутирует состояние или структура содержит мьютексы (sync.Mutex)."
})

part1.append({
    "num": 3,
    "title": "Инкапсуляция данных: приватная структура bank.account и публичный конструктор NewAccount",
    "task": "Инкапсуляция (Private/Public): Создай пакет bank. В нём структуру account (с маленькой буквы) с приватным полем balance float64. Напиши публичную функцию NewAccount(initialBalance float64) *account, которая выступает конструктором.",
    "theory": "**Инкапсуляция на уровне пакетов в Go:**\n- Видимость определяется регистром первой буквы идентификатора (строчная — приватный для пакета, заглавная — публичный экспортируемый);\n- Создание приватной структуры с публичным конструктором гарантирует невозможность создания невалидного объекта в обход правил валидации.",
    "step_by_step": "1. Моделируем структуру с неэкспортируемым балансом.\n2. Экспортируем конструктор NewAccount.\n3. Добавляем методы доступа Balance() и Deposit().",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"math\"\n)\n\ntype internalAccount struct {\n\tbalance float64\n}\n\nfunc NewInternalAccount(init float64) *internalAccount {\n\tif init < 0 {\n\t\tinit = 0\n\t}\n\treturn &internalAccount{balance: init}\n}\n\nfunc (a *internalAccount) Balance() float64 { return a.balance }\nfunc (a *internalAccount) Deposit(amount float64) {\n\tif amount > 0 {\n\t\ta.balance += amount\n\t}\n}\n\nfunc main() {\n\tacc := NewInternalAccount(1000.50)\n\tacc.Deposit(500.25)\n\tfmt.Printf(\"Текущий баланс счета: %.2f руб.\\n\", math.Round(acc.Balance()*100)/100)\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Текущий баланс счета: 1500.75 руб."
        }
    ],
    "under_the_hood": "Компилятор блокирует доступ к неэкспортируемым полям на этапе построения AST.",
    "pitfalls": "- Попытка инкапсулировать состояние между структурами внутри одного и того же пакета.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие инкапсуляции в Go от C++/Java?»\n**Ответ:** В Go инкапсуляция действует на уровне пакетов, а не отдельных классов/структур."
})

part1.append({
    "num": 4,
    "title": "Цепочка вызовов (Method Chaining / Fluent Interface) для кастомного типа Counter",
    "task": "Создайте тип Counter на основе int. Реализуйте методы Inc(), Dec(), Value() int с получателем-указателем. Сделайте цепочку вызовов: c.Inc().Inc().Dec().",
    "theory": "**Method Chaining в Go:**\n- Чтобы связать вызовы в цепочку, метод обязан возвращать указатель на получателя *Counter.",
    "step_by_step": "1. Объявляем type Counter int.\n2. Реализуем Inc() *Counter и Dec() *Counter.\n3. Реализуем Value() int.\n4. Собираем цепочку c.Inc().Inc().Dec().",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Counter int\n\nfunc (c *Counter) Inc() *Counter {\n\t*c++\n\treturn c\n}\n\nfunc (c *Counter) Dec() *Counter {\n\t*c--\n\treturn c\n}\n\nfunc (c *Counter) Value() int {\n\treturn int(*c)\n}\n\nfunc main() {\n\tvar c Counter = 10\n\tc.Inc().Inc().Inc().Dec()\n\tfmt.Printf(\"Итоговое значение счетчика: %d\\n\", c.Value())\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Итоговое значение счетчика: 12"
        }
    ],
    "under_the_hood": "Адрес получателя возвращается в регистре RAX для следующего вызова.",
    "pitfalls": "- Возврат значения Counter вместо указателя при попытке мутации.",
    "bigtech_interview": "**Вопрос с собеседования:** «Где в Go применяется Method Chaining?»\n**Ответ:** В Query Builder (GORM), HTTP-маршрутизаторах (Chi) и валидаторах."
})

part1.append({
    "num": 5,
    "title": "Изоляция состояния структуры Counter с приватным полем value int в отдельном пакете",
    "task": "Создайте структуру Counter с приватным полем value int (вынесите её в отдельный пакет counter, чтобы поле было действительно приватным для main).",
    "theory": "Инкапсуляция внутреннего поля структуры и доступ через экспортируемые методы.",
    "step_by_step": "1. Объявляем структуру с полем value int.\n2. Добавляем конструктор и методы Get/Add.\n3. Проверяем работу.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype SafeCounter struct {\n\tvalue int\n}\n\nfunc NewSafeCounter(start int) *SafeCounter {\n\treturn &SafeCounter{value: start}\n}\n\nfunc (c *SafeCounter) Add(delta int) { c.value += delta }\nfunc (c *SafeCounter) Get() int       { return c.value }\n\nfunc main() {\n\tcnt := NewSafeCounter(100)\n\tcnt.Add(25)\n\tcnt.Add(-10)\n\tfmt.Printf(\"Состояние счетчика: %d\\n\", cnt.Get())\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Состояние счетчика: 115"
        }
    ],
    "under_the_hood": "Приватное поле имеет смещение 0, но защищено компилятором.",
    "pitfalls": "- Экспорт поля с заглавной буквы при необходимости строгого контроля инварианта.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как сделать структуру потокобезопасной?»\n**Ответ:** Использовать sync.Mutex или атомики atomic.Int64."
})

part1.append({
    "num": 6,
    "title": "Автоматическое взятие адреса при вызове Pointer Receiver метода на значении",
    "task": "Объяви тип Counter с методом Increment() (pointer receiver). Создай переменную var c Counter (не указатель), вызови c.Increment(). Покажи, что Go автоматически передаёт адрес для pointer receiver. Убедись, что оригинал изменился.",
    "theory": "Компилятор автоматически преобразует c.Increment() в (&c).Increment(), если c адресуемо.",
    "step_by_step": "1. Объявляем структуру Counter{val int}.\n2. Реализуем (c *Counter) Increment().\n3. Вызываем метод на переменной-значении.\n4. Проверяем изменение оригинала.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Counter struct {\n\tval int\n}\n\nfunc (c *Counter) Increment() {\n\tc.val++\n}\n\nfunc main() {\n\tvar c Counter\n\tc.val = 10\n\tc.Increment()\n\tc.Increment()\n\tfmt.Printf(\"Оригинал изменился: %d (ожидалось 12)\\n\", c.val)\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Оригинал изменился: 12 (ожидалось 12)"
        }
    ],
    "under_the_hood": "Компилятор генерирует взятие адреса переменной в стеке.",
    "pitfalls": "- Попытка вызвать pointer-метод на неадресуемом литерале Counter{val: 10}.Increment().",
    "bigtech_interview": "**Вопрос с собеседования:** «Какие значения в Go неадресуемы?»\n**Ответ:** Литералы структур, возвращаемые значения функций, значения из map и константы."
})

part1.append({
    "num": 7,
    "title": "Методы Increment() и Decrement() с Pointer Receiver для управления состоянием структуры",
    "task": "Добавьте к Counter методы Increment() и Decrement() с pointer receiver (*Counter), чтобы они могли изменять состояние структуры.",
    "theory": "Pointer Receiver для методов, изменяющих внутреннее состояние.",
    "step_by_step": "1. Объявляем структуру Counter{count int}.\n2. Реализуем методы Increment и Decrement с *Counter получателем.\n3. Проверяем вызовы.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Counter struct {\n\tcount int\n}\n\nfunc (c *Counter) Increment() { c.count++ }\nfunc (c *Counter) Decrement() { c.count-- }\n\nfunc main() {\n\tc := &Counter{count: 0}\n\tc.Increment()\n\tc.Increment()\n\tc.Decrement()\n\tfmt.Printf(\"Текущее значение: %d\\n\", c.count)\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Текущее значение: 1"
        }
    ],
    "under_the_hood": "Мутация полей выполняется напрямую по адресу памяти.",
    "pitfalls": "- Пропуск звездочки * в получателе, из-за чего изменится временная копия.",
    "bigtech_interview": "**Вопрос с собеседования:** «Можно ли смешивать value receiver и pointer receiver у одной структуры?»\n**Ответ:** Технически можно, но рекомендуется придерживаться единообразия (Pointer Receiver для всех методов, если хотя бы один метод мутирует состояние)."
})

part1.append({
    "num": 8,
    "title": "Method Set для T и *T: сравнение Area() (Value) и Scale() (Pointer) у структуры Rectangle",
    "task": "Объяви тип Rectangle с методами Area() float64 (value receiver) и Scale(factor float64) (pointer receiver). Покажи, что Area работает на value и pointer, а Scale требует addressable value или указатель. Объясни method set T vs *T.",
    "theory": "**Спецификация Method Sets:**\n- Type T содержит только методы с получателем (t T);\n- Type *T содержит методы с получателем (t T) И (t *T).",
    "step_by_step": "1. Создаем структуру Rectangle.\n2. Реализуем Area() с Value Receiver.\n3. Реализуем Scale() с Pointer Receiver.\n4. Демонстрируем вызовы на значении и указателе.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Rectangle struct {\n\tWidth, Height float64\n}\n\nfunc (r Rectangle) Area() float64 {\n\treturn r.Width * r.Height\n}\n\nfunc (r *Rectangle) Scale(factor float64) {\n\tr.Width *= factor\n\tr.Height *= factor\n}\n\nfunc main() {\n\tr1 := Rectangle{Width: 10, Height: 5}\n\tfmt.Printf(\"Area на значении: %.1f\\n\", r1.Area())\n\tr1.Scale(2.0)\n\tfmt.Printf(\"После Scale: Width=%.1f, Height=%.1f\\n\", r1.Width, r1.Height)\n\n\tr2 := &Rectangle{Width: 4, Height: 3}\n\tfmt.Printf(\"Area на указателе: %.1f\\n\", r2.Area())\n\tr2.Scale(3.0)\n\tfmt.Printf(\"После Scale r2: Width=%.1f, Height=%.1f\\n\", r2.Width, r2.Height)\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Area на значении: 50.0\n# После Scale: Width=20.0, Height=10.0\n# Area на указателе: 12.0\n# После Scale r2: Width=12.0, Height=9.0"
        }
    ],
    "under_the_hood": "Method set определяет совместимость с интерфейсами.",
    "pitfalls": "- Попытка передать Rectangle в интерфейс с методом Scale.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему Rectangle{10, 20}.Scale(2) запрещен?»\n**Ответ:** Литерал структуры неадресуем; взятие адреса временного значения бессмысленно."
})

part1.append({
    "num": 9,
    "title": "Реализация метода Area() с Value Receiver для структуры Rectangle",
    "task": "Создай структуру Rectangle с полями Width, Height float64. Напиши для нее метод Area() с value receiver. Вызови метод.",
    "theory": "Вычисление площади через метод со значением-получателем.",
    "step_by_step": "1. Объявляем структуру Rectangle.\n2. Реализуем метод Area().\n3. Вызываем в main.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Rectangle struct {\n\tWidth, Height float64\n}\n\nfunc (r Rectangle) Area() float64 {\n\treturn r.Width * r.Height\n}\n\nfunc main() {\n\trect := Rectangle{Width: 12.5, Height: 4.0}\n\tfmt.Printf(\"Площадь прямоугольника: %.2f кв. ед.\\n\", rect.Area())\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Площадь прямоугольника: 50.00 кв. ед."
        }
    ],
    "under_the_hood": "Структура передается в регистры как пара float64.",
    "pitfalls": "- Попытка мутировать поля внутри метода с Value Receiver.",
    "bigtech_interview": "**Вопрос с собеседования:** «Является ли вызов метода rect.Area() сахаром над функцией?»\n**Ответ:** Да, это эквивалентно Rectangle.Area(rect)."
})

part1.append({
    "num": 10,
    "title": "Инкапсуляция возраста: структура Person, валидация в SetAge(age int) error и геттер GetAge()",
    "task": "Структура Person с приватным полем age (неэкспортируемое). Экспортируемые методы SetAge(age int) error (с проверкой >0) и GetAge() int. Продемонстрируйте инкапсуляцию.",
    "theory": "Геттеры и сеттеры с валидацией инвариантов возраста.",
    "step_by_step": "1. Создаем Person с приватным age int.\n2. Реализуем SetAge(age int) error.\n3. Реализуем GetAge() int.\n4. Тестируем валидацию.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n)\n\ntype Person struct {\n\tName string\n\tage  int\n}\n\nfunc (p *Person) SetAge(age int) error {\n\tif age <= 0 || age > 150 {\n\t\treturn errors.New(\"некорректный возраст\")\n\t}\n\tp.age = age\n\treturn nil\n}\n\nfunc (p *Person) GetAge() int {\n\treturn p.age\n}\n\nfunc main() {\n\tp := &Person{Name: \"Алексей\"}\n\t_ = p.SetAge(28)\n\tfmt.Printf(\"Пользователь: %s, Возраст: %d\\n\", p.Name, p.GetAge())\n\n\tif err := p.SetAge(-5); err != nil {\n\t\tfmt.Println(\"❌ Ошибка валидации:\", err)\n\t}\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Пользователь: Алексей, Возраст: 28\n# ❌ Ошибка валидации: некорректный возраст"
        }
    ],
    "under_the_hood": "Приватность проверяется компилятором на этапе typecheck.",
    "pitfalls": "- Игнорирование ошибки от сеттера.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Go геттеры называют без префикса Get?»\n**Ответ:** По соглашению Effective Go геттеры называют именем свойства (Age()), а префикс Get используют только для ресурсоемких операций."
})

print(f"Loaded batch 1: {len(part1)} exercises.")
with open('builder/gen_ch15_p1_batch1.json', 'w', encoding='utf-8') as f:
    json.dump(part1, f, ensure_ascii=False, indent=2)
