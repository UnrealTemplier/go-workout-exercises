import json

part2 = []

# Ex 11-22
part2.append({
    "num": 11,
    "title": "Метод Value() с Value Receiver для безопасного чтения состояния объекта",
    "task": "Добавьте метод Value() с value receiver для безопасного чтения текущего состояния.",
    "theory": "Безопасное чтение гарантирует иммутабельность вызывающего объекта.",
    "step_by_step": "1. Создаем структуру Score.\n2. Реализуем метод (s Score) Value() int.\n3. Вызываем в main.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Score struct {\n\tpoints int\n}\n\nfunc (s Score) Value() int {\n\treturn s.points\n}\n\nfunc main() {\n\ts := Score{points: 95}\n\tfmt.Printf(\"Текущие баллы: %d\\n\", s.Value())\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Текущие баллы: 95"
        }
    ],
    "under_the_hood": "Чтение без захвата указателя.",
    "pitfalls": "- Использование Value Receiver для структур со срезами (мутация слайса затронет оригинал!).",
    "bigtech_interview": "**Вопрос с собеседования:** «Защищает ли Value Receiver от всех мутаций?»\n**Ответ:** Нет, если структура содержит указатели, срезы или мапы, их внутреннее состояние может быть изменено."
})

part2.append({
    "num": 12,
    "title": "Масштабирование прямоугольника: метод Scale(factor float64) с Pointer Receiver",
    "task": "Создай метод Scale(factor float64) для Rectangle с pointer receiver, который умножает ширину и высоту на factor. Проверь, что оригинал изменился.",
    "theory": "Мутация полей через указатель.",
    "step_by_step": "1. Создаем структуру Rectangle.\n2. Реализуем метод Scale(factor float64).\n3. Вызываем на прямоугольнике.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Rectangle struct {\n\tWidth, Height float64\n}\n\nfunc (r *Rectangle) Scale(factor float64) {\n\tif r == nil || factor <= 0 {\n\t\treturn\n\t}\n\tr.Width *= factor\n\tr.Height *= factor\n}\n\nfunc main() {\n\trect := Rectangle{Width: 10, Height: 20}\n\trect.Scale(2.5)\n\tfmt.Printf(\"После масштабирования: %.1f x %.1f\\n\", rect.Width, rect.Height)\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# После масштабирования: 25.0 x 50.0"
        }
    ],
    "under_the_hood": "Прямая мутация полей по адресу памяти.",
    "pitfalls": "- Вызов Scale(0) без проверки.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что будет при вызове Scale на nil-указателе?»\n**Ответ:** С проверкой if r == nil вызов безопасен, без проверки произойдет nil pointer dereference."
})

part2.append({
    "num": 13,
    "title": "Приемники и nil-получатели: безопасный вызов метода GetValue() на nil-указателе *Node",
    "task": "Приемники (Receivers) и nil-получатели: Напишите структуру Node с полем Value int и методом GetValue() int. Настройте метод так, чтобы получатель (receiver) был указателем (n *Node). Добавьте проверку if n == nil { return 0 }. Создайте переменную var n *Node (она равна nil) и попробуйте вызвать n.GetValue(). Убедитесь, что в Go вызов метода на nil-указателе возможен и не всегда приводит к панике (в отличие от других языков).",
    "theory": "В Go вызов метода на nil-указателе не падает, если метод проверяет nil receiver.",
    "step_by_step": "1. Объявляем Node{Value int}.\n2. Реализуем (n *Node) GetValue() int с проверкой if n == nil.\n3. Вызываем на var n *Node = nil.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Node struct {\n\tValue int\n}\n\nfunc (n *Node) GetValue() int {\n\tif n == nil {\n\t\treturn 0\n\t}\n\treturn n.Value\n}\n\nfunc main() {\n\tvar n *Node = nil\n\tval := n.GetValue()\n\tfmt.Printf(\"Результат вызова на nil-указателе: %d\\n\", val)\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Результат вызова на nil-указателе: 0"
        }
    ],
    "under_the_hood": "Адрес метода разрешается статически, рантайм передает 0x0 в качестве аргумента.",
    "pitfalls": "- Обращение к полям структуры до проверки на nil.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Go разрешен вызов методов на nil-указателях?»\n**Ответ:** Потому что методы в Go — это обычные функции с первым скрытым аргументом получателя, а 0x0 — валидный аргумент."
})

part2.append({
    "num": 14,
    "title": "Управление банковским счетом: геттер Balance(), методы Deposit() и Withdraw() с защитой от овердрафта",
    "task": "Геттеры и действия: Добавь к account методы Balance() float64 (геттер), Deposit(amount float64) и Withdraw(amount float64) error. Убедись, что снять денег больше, чем есть на балансе, нельзя.",
    "theory": "Инкапсуляция бизнес-правил внутри структуры.",
    "step_by_step": "1. Объявляем Account.\n2. Реализуем Balance, Deposit, Withdraw.\n3. Проверяем овердрафт.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n)\n\ntype Account struct {\n\tbalance float64\n}\n\nfunc (a *Account) Balance() float64 { return a.balance }\n\nfunc (a *Account) Deposit(amount float64) error {\n\tif amount <= 0 {\n\t\treturn errors.New(\"сумма пополнения должна быть больше 0\")\n\t}\n\ta.balance += amount\n\treturn nil\n}\n\nfunc (a *Account) Withdraw(amount float64) error {\n\tif amount > a.balance {\n\t\treturn errors.New(\"недостаточно средств\")\n\t}\n\ta.balance -= amount\n\treturn nil\n}\n\nfunc main() {\n\tacc := &Account{balance: 500}\n\t_ = acc.Deposit(200)\n\tfmt.Printf(\"Баланс: %.2f руб.\\n\", acc.Balance())\n\n\tif err := acc.Withdraw(1000); err != nil {\n\t\tfmt.Println(\"❌ Ошибка:\", err)\n\t}\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Баланс: 700.00 руб.\n# ❌ Ошибка: недостаточно средств"
        }
    ],
    "under_the_hood": "Все операции проверяют инвариант до записи в память.",
    "pitfalls": "- Работа с деньгами через float64 без округления.",
    "bigtech_interview": "**Вопрос с собеседования:** «В каком типе хранить деньги в Go?»\n**Ответ:** В int64 в минимальных единицах валюты (копейках, центах)."
})

part2.append({
    "num": 15,
    "title": "Method Values (Значения методов): захват получателя в замыкание p.Distance",
    "task": "Создай method value: p := Point{3, 4}; distanceFromP := p.Distance. Вызови distanceFromP(otherPoint). Объясни, что method value захватывает получателя (p копируется в замыкание).",
    "theory": "Method Values захватывают объект получателя и возвращают функцию с привязанным состоянием.",
    "step_by_step": "1. Создаем структуру Point.\n2. Присваиваем fn := origin.Distance.\n3. Вызываем функцию fn(p).",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"math\"\n)\n\ntype Point struct {\n\tX, Y float64\n}\n\nfunc (p Point) Distance(other Point) float64 {\n\tdx := p.X - other.X\n\tdy := p.Y - other.Y\n\treturn math.Sqrt(dx*dx + dy*dy)\n}\n\nfunc main() {\n\torigin := Point{0, 0}\n\tdistanceFromOrigin := origin.Distance\n\n\tp1 := Point{3, 4}\n\tfmt.Printf(\"Расстояние: %.2f\\n\", distanceFromOrigin(p1))\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Расстояние: 5.00"
        }
    ],
    "under_the_hood": "Компилятор создает замыкание, сохраняющее копию origin.",
    "pitfalls": "- Ожидание, что изменение origin повлияет на уже созданный Method Value с Value Receiver.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие Method Value от Method Expression?»\n**Ответ:** Method Value (p.Distance) имеет получателя внутри замыкания, а Method Expression (Point.Distance) требует передать получателя первым параметром."
})

part2.append({
    "num": 16,
    "title": "Встраивание структур: переопределение методов (Method Shadowing) у Employee и Person",
    "task": "Встраивание: Employee встраивает Person. Вызовите метод GetAge напрямую у Employee. Добавьте в Employee свой метод GetAge (переопределение) и покажите разницу.",
    "theory": "Затенение встроенных методов при объявлении метода с тем же именем.",
    "step_by_step": "1. Создаем Person с GetAge().\n2. Создаем Employee со встраиванием Person и собственным GetAge().\n3. Сравниваем вызовы emp.GetAge() и emp.Person.GetAge().",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Person struct {\n\tAge int\n}\n\nfunc (p Person) GetAge() int {\n\treturn p.Age\n}\n\ntype Employee struct {\n\tPerson\n\tPosition string\n}\n\nfunc (e Employee) GetAge() int {\n\treturn e.Age + 100 // Затенение\n}\n\nfunc main() {\n\temp := Employee{Person: Person{Age: 30}, Position: \"Dev\"}\n\tfmt.Printf(\"emp.GetAge():        %d\\n\", emp.GetAge())\n\tfmt.Printf(\"emp.Person.GetAge(): %d\\n\", emp.Person.GetAge())\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# emp.GetAge():        130\n# emp.Person.GetAge(): 30"
        }
    ],
    "under_the_hood": "Компилятор разрешает имена методов с минимальной глубиной вложенности.",
    "pitfalls": "- Думать, что в Go работает динамический полиморфизм наследования классов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Является ли встраивание структур наследованием?»\n**Ответ:** Нет, это композиция с синтаксическим сахаром делегирования."
})

part2.append({
    "num": 17,
    "title": "Рекурсивное дерево Tree с методом Sum() на nil pointer receiver",
    "task": "Реализуй метод на nil pointer receiver: type Tree struct { Value int; Left, Right *Tree }, метод (t *Tree) Sum() int. Вызови (nil).Sum() — покажи, что если метод проверяет if t == nil { return 0 }, это безопасно. Объясни, почему в Go это возможно (nil — валидный receiver, если не разыменовывается).",
    "theory": "Безопасные рекурсивные алгоритмы на базе nil receiver.",
    "step_by_step": "1. Создаем структуру Tree.\n2. Реализуем (t *Tree) Sum() int с базовым случаем if t == nil { return 0 }.\n3. Проверяем вызов на nil и на дереве.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Tree struct {\n\tValue int\n\tLeft, Right *Tree\n}\n\nfunc (t *Tree) Sum() int {\n\tif t == nil {\n\t\treturn 0\n\t}\n\treturn t.Value + t.Left.Sum() + t.Right.Sum()\n}\n\nfunc main() {\n\tvar empty *Tree = nil\n\tfmt.Printf(\"Сумма nil дерева: %d\\n\", empty.Sum())\n\n\troot := &Tree{Value: 10, Left: &Tree{Value: 5}, Right: &Tree{Value: 15}}\n\tfmt.Printf(\"Сумма дерева:     %d\\n\", root.Sum())\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Сумма nil дерева: 0\n# Сумма дерева:     30"
        }
    ],
    "under_the_hood": "Рекурсия завершается на nil-листьях без создания лишних проверок в вызывающем коде.",
    "pitfalls": "- Обращение к t.Left до проверки if t == nil.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем писать методы на nil receiver?»\n**Ответ:** Это делает рекурсивный код компактным, элегантным и избавляет от громоздких внешних проверок."
})

part2.append({
    "num": 18,
    "title": "Авто-взятие адреса компилятором при вызове pointer-метода на переменной r Rectangle",
    "task": "Изучите авто-взятие адреса: создайте переменную r Rectangle (не указатель) и попробуйте вызвать r.Area(), если метод требует *Rectangle. Объясните, как компилятор делает это за вас.",
    "theory": "Автоматическое взятие адреса (&r).Method() при вызове на адресуемой переменной.",
    "step_by_step": "1. Создаем Rectangle.\n2. Реализуем (r *Rectangle) Area() float64.\n3. Вызываем на значении r Rectangle.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Rectangle struct {\n\tWidth, Height float64\n}\n\nfunc (r *Rectangle) Area() float64 {\n\treturn r.Width * r.Height\n}\n\nfunc main() {\n\tr := Rectangle{5, 4}\n\tres := r.Area() // Компилятор подставляет (&r).Area()\n\tfmt.Printf(\"Площадь: %.1f\\n\", res)\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Площадь: 20.0"
        }
    ],
    "under_the_hood": "Фаза компилятора трансформирует AST узел в взятие адреса.",
    "pitfalls": "- Вызов на неадресуемом литерале Rectangle{5, 4}.Area().",
    "bigtech_interview": "**Вопрос с собеседования:** «Работает ли авто-взятие адреса при присваивании интерфейсу?»\n**Ответ:** Нет, интерфейс требует точного соответствия method set."
})

part2.append({
    "num": 19,
    "title": "Определенный тип type MyString string и метод проверки палиндрома IsPalindrome()",
    "task": "Создай defined type type MyString string. Объяви метод (s MyString) IsPalindrome() bool. Покажи, что методы можно объявлять только на типы, определённые в том же пакете. Попробуй добавить метод к int — получи ошибку компиляции.",
    "theory": "Defined types над базовыми примитивами и изоляция набора методов.",
    "step_by_step": "1. Объявляем type MyString string.\n2. Реализуем IsPalindrome() bool с учетом рун.\n3. Проверяем слова.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype MyString string\n\nfunc (s MyString) IsPalindrome() bool {\n\trunes := []rune(string(s))\n\tn := len(runes)\n\tfor i := 0; i < n/2; i++ {\n\t\tif runes[i] != runes[n-1-i] {\n\t\t\treturn false\n\t\t}\n\t}\n\treturn true\n}\n\nfunc main() {\n\ts := MyString(\"топот\")\n\tfmt.Printf(\"%q палиндром? %t\\n\", s, s.IsPalindrome())\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# \"топот\" палиндром? true"
        }
    ],
    "under_the_hood": "Приведение типов имеет нулевой оверхед по памяти.",
    "pitfalls": "- Побайтовое сравнение UTF-8 строк.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие defined type от type alias?»\n**Ответ:** Defined type создает новый тип с собственным method set, а alias — лишь синоним."
})

part2.append({
    "num": 20,
    "title": "Каверзный кейс: почему значение Rectangle не удовлетворяет интерфейсу с Pointer-методом Scale",
    "task": "[Каверзный кейс]: Создай интерфейс Geometry с методом Area(). Попробуй присвоить переменной типа Geometry значение Rectangle (а не указатель). Пойми, почему метод Scale не входит в интерфейс для значения (Method Sets: *T включает методы T и *T, а T включает только методы T).",
    "theory": "Method sets определяют возможность удовлетворения интерфейсов.",
    "step_by_step": "1. Создаем интерфейс Transformer{ Scale(float64) }.\n2. Создаем Rectangle с (r *Rectangle) Scale.\n3. Демонстрируем ошибку при присвоении значения.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype Transformer interface {\n\tScale(factor float64)\n}\n\ntype Rectangle struct {\n\tWidth, Height float64\n}\n\nfunc (r *Rectangle) Scale(factor float64) {\n\tr.Width *= factor\n\tr.Height *= factor\n}\n\nfunc main() {\n\tvar t Transformer = &Rectangle{10, 5} // ✅ Успех\n\tt.Scale(2.0)\n\tfmt.Println(\"Трансформация выполнена успешно!\")\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Трансформация выполнена успешно!"
        }
    ],
    "under_the_hood": "Рантайм проверяет соответствие таблицы itab на этапе присваивания.",
    "pitfalls": "- Попытка упаковать значение T в интерфейс с pointer receiver методами.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему T не включает методы *T в свой method set?»\n**Ответ:** Чтобы избежать скрытой мутации копий данных внутри интерфейсов."
})

part2.append({
    "num": 21,
    "title": "Инкапсуляция и сокрытие данных: защита поля balance от прямого доступа из внешних пакетов",
    "task": "Инкапсуляция (Скрытие данных): Создайте пакет bank. Внутри пакета объявите структуру Account с приватным (неэкспортируемым) полем balance float64. Напишите публичные методы Deposit(amount float64) и Withdraw(amount float64) error для изменения баланса с валидацией, а также метод-геттер Balance() float64. Попробуйте получить доступ к полю balance напрямую из пакета main и зафиксируйте ошибку компиляции.",
    "theory": "Инкапсуляция защищает инварианты сущностей от некорректного вмешательства извне.",
    "step_by_step": "1. Создаем BankAccount с приватным balance.\n2. Реализуем публичные методы доступа.\n3. Тестируем.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n)\n\ntype BankAccount struct {\n\tbalance float64\n}\n\nfunc NewBankAccount(init float64) *BankAccount { return &BankAccount{balance: init} }\nfunc (b *BankAccount) Balance() float64        { return b.balance }\nfunc (b *BankAccount) Withdraw(amt float64) error {\n\tif amt > b.balance {\n\t\treturn errors.New(\"недостаточно средств\")\n\t}\n\tb.balance -= amt\n\treturn nil\n}\n\nfunc main() {\n\tacc := NewBankAccount(500)\n\t_ = acc.Withdraw(150)\n\tfmt.Printf(\"Баланс: %.2f руб.\\n\", acc.Balance())\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Баланс: 350.00 руб."
        }
    ],
    "under_the_hood": "Проверка прав доступа к неэкспортируемым идентификаторам компилятором.",
    "pitfalls": "- Случайный экспорт поля с большой буквы.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как протестировать приватные методы пакета?»\n**Ответ:** Поместить юнит-тесты в тот же пакет (package bank)."
})

part2.append({
    "num": 22,
    "title": "Значения против указателей: неявный переход (&acc).Modify() при вызове на значении",
    "task": "Значения vs Указатели (Сюрпризы): Напиши для структуры метод с value receiver (func (a account) Print()) и метод с pointer receiver (func (a *account) Modify()). В main создай значение acc := bank.NewAccount(...) (допустим, он возвращает значение, а не указатель). Вызови acc.Modify(). Осознай, что Go \"под капотом\" сам берет указатель (&acc).Modify().",
    "theory": "Go автоматически берет адрес адресуемого значения при вызове pointer receiver метода.",
    "step_by_step": "1. Создаем структуру SimpleAccount.\n2. Реализуем Print (value) и Modify (pointer).\n3. Вызываем оба метода на значении.",
    "code_blocks": [
        {
            "filename": "main.go",
            "lang": "go",
            "code": "package main\n\nimport \"fmt\"\n\ntype SimpleAccount struct {\n\tOwner string\n}\n\nfunc (a SimpleAccount) Print() {\n\tfmt.Println(\"Владелец:\", a.Owner)\n}\n\nfunc (a *SimpleAccount) Modify(name string) {\n\ta.Owner = name\n}\n\nfunc main() {\n\tacc := SimpleAccount{Owner: \"Иван\"}\n\tacc.Print()\n\tacc.Modify(\"Константин\") // (&acc).Modify(...)\n\tacc.Print()\n}"
        },
        {
            "filename": "Терминал",
            "lang": "bash",
            "code": "go run main.go\n# Владелец: Иван\n# Владелец: Константин"
        }
    ],
    "under_the_hood": "Компилятор генерирует передачу адреса переменной.",
    "pitfalls": "- Непонимание того, что оригинал действительно изменился.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда авто-взятие адреса не работает?»\n**Ответ:** На элементах map (m[\"key\"].Modify()), так как они неадресуемы."
})

print(f"Loaded batch 2: {len(part2)} exercises.")
with open('builder/gen_ch15_p1_batch2.json', 'w', encoding='utf-8') as f:
    json.dump(part2, f, ensure_ascii=False, indent=2)
