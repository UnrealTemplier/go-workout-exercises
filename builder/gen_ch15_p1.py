exercises = [
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  },
  {
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
  }
]
