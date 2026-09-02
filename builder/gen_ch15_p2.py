exercises = [
  {
    "num": 34,
    "title": "Полиморфизм: интерфейс Describer с методом Describe() для Circle и Rectangle",
    "task": "Полиморфизм: интерфейс Describer с методом Describe() string. Реализуйте для Circle и Rectangle. Функция PrintAll(desc []Describer) выводит описание каждого.",
    "theory": "Полиморфизм подтипов на основе общего интерфейса.",
    "step_by_step": "1. Объявляем Describer.\n2. Реализуем Describe() для Circle и Rectangle.\n3. Пишем PrintAll(desc []Describer).",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Describer interface {\n\tDescribe() string\n}\n\ntype Circle struct{ R float64 }\nfunc (c Circle) Describe() string { return fmt.Sprintf(\"Круг радиусом %.1f\", c.R) }\n\ntype Rectangle struct{ W, H float64 }\nfunc (r Rectangle) Describe() string { return fmt.Sprintf(\"Прямоугольник %.1fx%.1f\", r.W, r.H) }\n\nfunc PrintAll(items []Describer) {\n\tfor _, item := range items {\n\t\tfmt.Println(\"•\", item.Describe())\n\t}\n}\n\nfunc main() {\n\tshapes := []Describer{Circle{5}, Rectangle{4, 6}}\n\tPrintAll(shapes)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# • Круг радиусом 5.0\n# • Прямоугольник 4.0x6.0"
      }
    ],
    "under_the_hood": "Вызовы методов диспетчеризуются через iface.itab.",
    "pitfalls": "- Попытка передать []Circle в []Describer напрямую без конвертации.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как устроен динамический полиморфизм в Go?»\n**Ответ:** Через интерфейсные таблицы itab, хранящие указатели на конкретные методы структуры."
  },
  {
    "num": 35,
    "title": "Встраивание bytes.Buffer в CustomReader и автоматическое всплытие потоковых методов",
    "task": "Создай структуру CustomReader, встроив в неё bytes.Buffer. Покажи, что методы Buffer (Write, WriteString, Bytes и т.д.) продвигаются (promoted) и доступны напрямую на CustomReader.",
    "theory": "Встраивание стандартных типов передает все их методы внешней структуре.",
    "step_by_step": "1. Создаем CustomReader{ bytes.Buffer, ID string }.\n2. Вызываем WriteString и Bytes напрямую на CustomReader.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"bytes\"\n\t\"fmt\"\n)\n\ntype CustomReader struct {\n\tbytes.Buffer // Встраивание\n\tID           string\n}\n\nfunc main() {\n\tcr := &CustomReader{ID: \"stream_1\"}\n\tcr.WriteString(\"Данные потока\") // Promoted method\n\tfmt.Printf(\"[%s] Прочитано: %s\\n\", cr.ID, cr.String())\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# [stream_1] Прочитано: Данные потока"
      }
    ],
    "under_the_hood": "Компилятор генерирует прокси-вызовы к встроенному полю Buffer.",
    "pitfalls": "- Копирование структуры со встроенным Buffer (bytes.Buffer нельзя копировать после использования!).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему bytes.Buffer нельзя передавать по значению?»\n**Ответ:** Buffer содержит внутренний срез и массив-буфер; копирование приведет к повреждению памяти при росте буфера."
  },
  {
    "num": 36,
    "title": "Приватные методы: вызов неэкспортируемого метода из публичного API структуры",
    "task": "Создайте приватный метод (начинается с маленькой буквы) внутри структуры и вызовите его из публичного метода этой же структуры.",
    "theory": "Вспомогательные методы инкапсулируют внутреннюю логику.",
    "step_by_step": "1. Создаем OrderProcessor.\n2. Реализуем приватный метод validate() bool.\n3. Вызываем его из публичного Process().",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype OrderProcessor struct {\n\tOrderID int\n\tAmount  float64\n}\n\nfunc (op *OrderProcessor) validate() bool {\n\treturn op.OrderID > 0 && op.Amount > 0\n}\n\nfunc (op *OrderProcessor) Process() error {\n\tif !op.validate() {\n\t\treturn fmt.Errorf(\"заказ %d не прошел валидацию\", op.OrderID)\n\t}\n\tfmt.Printf(\"Заказ #%d на сумму %.2f успешно обработан!\\n\", op.OrderID, op.Amount)\n\treturn nil\n}\n\nfunc main() {\n\top := &OrderProcessor{OrderID: 101, Amount: 4500}\n\t_ = op.Process()\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Заказ #101 на сумму 4500.00 успешно обработан!"
      }
    ],
    "under_the_hood": "Приватный метод не экспортируется в заголовки пакета.",
    "pitfalls": "- Дублирование валидации в нескольких публичных методах вместо выноса в приватный.",
    "bigtech_interview": "**Вопрос с собеседования:** «Доступны ли приватные методы структуры в тестах?»\n**Ответ:** Да, если тест находится в том же пакете."
  },
  {
    "num": 37,
    "title": "Анонимное встраивание Engine в Car и прямой вызов car.Start()",
    "task": "Создай структуру Engine с методом Start(). Создай структуру Car, которая анонимно встраивает Engine. Вызови car.Start() напрямую у структуры Car (встраивание полей и методов).",
    "theory": "Всплытие методов через композицию.",
    "step_by_step": "1. Создаем Engine с методом Start().\n2. Создаем Car со встраиванием Engine.\n3. Вызываем car.Start().",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Engine struct{ Type string }\nfunc (e Engine) Start() { fmt.Printf(\"Двигатель %s запущен!\\n\", e.Type) }\n\ntype Car struct {\n\tEngine\n\tBrand string\n}\n\nfunc main() {\n\tc := Car{Engine: Engine{\"V8 Turbo\"}, Brand: \"Porsche\"}\n\tc.Start()\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Двигатель V8 Turbo запущен!"
      }
    ],
    "under_the_hood": "Синтаксис c.Start() преобразуется в c.Engine.Start().",
    "pitfalls": "- Ожидание, что Engine знает о структуре Car.",
    "bigtech_interview": "**Вопрос с собеседования:** «Можно ли переопределить метод Start в Car?»\n**Ответ:** Да, тогда вызовется Car.Start, а к Engine.Start можно обратиться явно через c.Engine.Start()."
  },
  {
    "num": 38,
    "title": "Потокобезопасная структура SafeCounter со встроенным *sync.Mutex",
    "task": "Создай структуру SafeCounter, встроив *sync.Mutex. Покажи, что методы Lock/Unlock продвигаются. Напиши метод Inc() с защитой мьютекса. Объясни, почему встраивается именно *sync.Mutex, а не sync.Mutex.",
    "theory": "Встраивание указателя *sync.Mutex предотвращает случайное фатальное копирование мьютекса при передаче структуры.",
    "step_by_step": "1. Создаем SafeCounter{ *sync.Mutex, val int }.\n2. Реализуем Inc() и Value().\n3. Запускаем конкурентный инкремент.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n)\n\ntype SafeCounter struct {\n\t*sync.Mutex // Указатель на мьютекс\n\tval         int\n}\n\nfunc NewSafeCounter() *SafeCounter {\n\treturn &SafeCounter{Mutex: &sync.Mutex{}}\n}\n\nfunc (c *SafeCounter) Inc() {\n\tc.Lock() // Promoted Lock\n\tdefer c.Unlock()\n\tc.val++\n}\n\nfunc main() {\n\tc := NewSafeCounter()\n\tvar wg sync.WaitGroup\n\tfor i := 0; i < 1000; i++ {\n\t\twg.Add(1)\n\t\tgo func() {\n\t\t\tdefer wg.Done()\n\t\t\tc.Inc()\n\t\t}()\n\t}\n\twg.Wait()\n\tfmt.Println(\"Счетчик:\", c.val)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run -race main.go\n# Счетчик: 1000"
      }
    ],
    "under_the_hood": "Мьютекс разделяется между всеми копиями ссылки на структуру.",
    "pitfalls": "- Встраивание значения sync.Mutex и случайное копирование структуры по значению (приведет к Data Race).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Go запрещено копировать sync.Mutex?»\n**Ответ:** Копирование мьютекса копирует его внутреннее битовое состояние блокировки, что приводит к дедлокам и гонкам данных (go vet выдает предупреждение)."
  },
  {
    "num": 39,
    "title": "Разрешение конфликтов имен (Ambiguous Selectors) при встраивании GPS и MobilePhone в SmartCar",
    "task": "Конфликты имен при композиции: Создайте две структуры: GPS (с методом GetCoordinates()) и MobilePhone (с методом GetCoordinates()). Создайте структуру SmartCar, встроив в неё обе эти структуры. Попробуйте вызвать smartCar.GetCoordinates(). Разберитесь в ошибке компиляции (ambiguous selector) и решите её, вызвав методы явно через имена встроенных типов.",
    "theory": "Коллизия имен при множественном встраивании устраняется явной квалификацией имени встроенного типа.",
    "step_by_step": "1. Создаем GPS и MobilePhone с методом GetCoordinates().\n2. Создаем SmartCar со встраиванием обеих структур.\n3. Показываем ошибку ambiguous selector и исправляем через smartCar.GPS.GetCoordinates().",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype GPS struct{}\nfunc (GPS) GetCoordinates() string { return \"55.7558° N, 37.6173° E (GPS)\" }\n\ntype MobilePhone struct{}\nfunc (MobilePhone) GetCoordinates() string { return \"55.7512° N, 37.6184° E (GSM)\" }\n\ntype SmartCar struct {\n\tGPS\n\tMobilePhone\n}\n\nfunc main() {\n\tcar := SmartCar{}\n\n\t// ❌ ОШИБКА: car.GetCoordinates() -> ambiguous selector car.GetCoordinates\n\n\t// ✅ Явное разрешение конфликта:\n\tfmt.Println(\"Координаты GPS:\", car.GPS.GetCoordinates())\n\tfmt.Println(\"Координаты GSM:\", car.MobilePhone.GetCoordinates())\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Координаты GPS: 55.7558° N, 37.6173° E (GPS)\n# Координаты GSM: 55.7512° N, 37.6184° E (GSM)"
      }
    ],
    "under_the_hood": "Компилятор видит два кандидата на одном уровне глубины в дереве селекторов и останавливает сборку.",
    "pitfalls": "- Попытка вызвать неоднозначный метод напрямую.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как компилятор Go разрешает совпадение имен при встраивании на разной глубине?»\n**Ответ:** Метод с меньшей глубиной вложенности затеняет (shadows) метод с большей глубиной. Ошибка возникает только при совпадении на одинаковой глубине."
  },
  {
    "num": 40,
    "title": "Кредитный аккаунт CreditAccount: расширение базовой структуры Account и поле CreditLimit",
    "task": "\"Наследование\" через композицию (Embedding): Создай структуру CreditAccount. Встрой в неё структуру account анонимным полем. Добавь поле CreditLimit float64.",
    "theory": "Расширение модели данных путем добавления новых полей к встроенной структуре.",
    "step_by_step": "1. Создаем базовый Account.\n2. Создаем CreditAccount со встраиванием Account и CreditLimit.\n3. Тестируем.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Account struct{ Balance float64 }\n\ntype CreditAccount struct {\n\tAccount\n\tCreditLimit float64\n}\n\nfunc (c *CreditAccount) AvailableFunds() float64 {\n\treturn c.Balance + c.CreditLimit\n}\n\nfunc main() {\n\tca := CreditAccount{Account: Account{Balance: 1000}, CreditLimit: 5000}\n\tfmt.Printf(\"Доступно средств: %.2f руб.\\n\", ca.AvailableFunds())\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Доступно средств: 6000.00 руб."
      }
    ],
    "under_the_hood": "Поле Balance лежит внутри подструктуры Account в непрерывной памяти.",
    "pitfalls": "- Забыть проинициализировать встроенную структуру.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как получить доступ к встроенной структуре целиком?»\n**Ответ:** Через имя встроенного типа ca.Account."
  },
  {
    "num": 41,
    "title": "Безопасное хэширование паролей: сеттер SetPassword(raw string) с crypto/sha256",
    "task": "Создайте структуру User с полями Email и PasswordHash. Сделайте сеттер SetPassword(raw string), который внутри хэширует пароль (используйте crypto/sha256) перед сохранением, чтобы сырой пароль никогда не хранился в памяти.",
    "theory": "Инкапсуляция криптографической обработки внутри сеттера.",
    "step_by_step": "1. Создаем User{Email, passwordHash}.\n2. Реализуем SetPassword с sha256.Sum256.\n3. Реализуем CheckPassword.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"crypto/sha256\"\n\t\"encoding/hex\"\n\t\"fmt\"\n)\n\ntype User struct {\n\tEmail        string\n\tpasswordHash string\n}\n\nfunc (u *User) SetPassword(raw string) {\n\thash := sha256.Sum256([]byte(raw))\n\tu.passwordHash = hex.EncodeToString(hash[:])\n}\n\nfunc (u *User) CheckPassword(raw string) bool {\n\thash := sha256.Sum256([]byte(raw))\n\treturn u.passwordHash == hex.EncodeToString(hash[:])\n}\n\nfunc main() {\n\tu := &User{Email: \"dev@yandex.ru\"}\n\tu.SetPassword(\"super_secret_123\")\n\tfmt.Println(\"Пароль верен?\", u.CheckPassword(\"super_secret_123\"))\n\tfmt.Println(\"Пароль неверен?\", u.CheckPassword(\"wrong_pass\"))\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Пароль верен? true\n# Пароль неверен? false"
      }
    ],
    "under_the_hood": "Сырой пароль удаляется сборщиком мусора, в структуре хранится только хэш.",
    "pitfalls": "- Хранение сырого пароля в публичном поле.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что используют для хэширования паролей в продакшене?»\n**Ответ:** bcrypt или argon2id с солью (salt) для защиты от радужных таблиц."
  },
  {
    "num": 42,
    "title": "Конфликт одинаковых полей Name при множественном встраивании: s.TypeA.Name vs s.TypeB.Name",
    "task": "Создай структуру, встраивающую два типа с одинаковым полем Name. Попробуй обратиться к .Name — получи ошибку ambiguous selector. Исправь через явное указание: s.TypeA.Name vs s.TypeB.Name.",
    "theory": "Явное указание пути к полю устраняет неоднозначность.",
    "step_by_step": "1. Создаем TypeA{Name} и TypeB{Name}.\n2. Создаем Composite{TypeA, TypeB}.\n3. Обращаемся через c.TypeA.Name и c.TypeB.Name.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Author struct{ Name string }\ntype Publisher struct{ Name string }\n\ntype BookRelease struct {\n\tAuthor\n\tPublisher\n}\n\nfunc main() {\n\trelease := BookRelease{\n\t\tAuthor:    Author{Name: \"Дональд Кнут\"},\n\t\tPublisher: Publisher{Name: \"Addison-Wesley\"},\n\t}\n\tfmt.Println(\"Автор:       \", release.Author.Name)\n\tfmt.Println(\"Издательство:\", release.Publisher.Name)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Автор:        Дональд Кнут\n# Издательство: Addison-Wesley"
      }
    ],
    "under_the_hood": "Компилятор вычисляет смещение каждого поля в байтах.",
    "pitfalls": "- Попытка прямого обращения release.Name.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как работает ambiguous selector на этапе компиляции?»\n**Ответ:** Компилятор генерирует ошибку во время проверки типов при обнаружении более одного пути одинаковой длины."
  },
  {
    "num": 43,
    "title": "Реализация sort.Interface для среза Student: сортировка по убыванию успеваемости",
    "task": "Интерфейс sort.Interface: реализуйте его для слайса структур Student (поля Name, Grade), чтобы сортировать по убыванию успеваемости. Используйте sort.Sort.",
    "theory": "Классическая сортировка через Len, Less, Swap.",
    "step_by_step": "1. Создаем Student{Name, Grade}.\n2. Объявляем type ByGrade []Student.\n3. Реализуем Len, Less, Swap.\n4. Сортируем через sort.Sort.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sort\"\n)\n\ntype Student struct {\n\tName  string\n\tGrade float64\n}\n\ntype ByGrade []Student\n\nfunc (b ByGrade) Len() int           { return len(b) }\nfunc (b ByGrade) Less(i, j int) bool { return b[i].Grade > b[j].Grade } // Убывание\nfunc (b ByGrade) Swap(i, j int)      { b[i], b[j] = b[j], b[i] }\n\nfunc main() {\n\tstudents := ByGrade{\n\t\t{\"Анна\", 4.5},\n\t\t{\"Борис\", 4.9},\n\t\t{\"Виктор\", 3.8},\n\t}\n\tsort.Sort(students)\n\tfor _, s := range students {\n\t\tfmt.Printf(\"• %-8s: %.1f\\n\", s.Name, s.Grade)\n\t}\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# • Борис   : 4.9\n# • Анна    : 4.5\n# • Виктор  : 3.8"
      }
    ],
    "under_the_hood": "Алгоритм QuickSort/Pattern-defeating Quicksort работает на срезе без аллокаций.",
    "pitfalls": "- Неправильный знак в Less для сортировки по убыванию.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что быстрее: sort.Sort или slices.SortFunc?»\n**Ответ:** slices.SortFunc быстрее за счет дженериков и отсутствия интерфейсного оверхеда."
  },
  {
    "num": 44,
    "title": "Встраивание интерфейса io.Reader в структуру MyProcessor и делегирование чтения",
    "task": "Встрой интерфейс io.Reader в структуру MyProcessor. Покажи, что MyProcessor автоматически удовлетворяет io.Reader, если встроенное поле инициализировано типом, реализующим io.Reader.",
    "theory": "Встраивание интерфейса в структуру автоматически делегирует все методы интерфейса вложенному полю.",
    "step_by_step": "1. Создаем MyProcessor{ io.Reader, Name string }.\n2. Передаем MyProcessor в io.ReadAll.\n3. Проверяем чтение.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n\t\"strings\"\n)\n\ntype MyProcessor struct {\n\tio.Reader // Встраивание интерфейса\n\tName      string\n}\n\nfunc main() {\n\tp := MyProcessor{\n\t\tReader: strings.NewReader(\"Привет от встроенного интерфейса!\"),\n\t\tName:   \"MainProcessor\",\n\t}\n\tdata, _ := io.ReadAll(p) // p реализует io.Reader!\n\tfmt.Println(string(data))\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Привет от встроенного интерфейса!"
      }
    ],
    "under_the_hood": "Вызов p.Read делегируется вызову метода внутри поля Reader.",
    "pitfalls": "- Вызов Read при Reader == nil приведет к панике nil pointer dereference.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем встраивать интерфейсы в структуры?»\n**Ответ:** Для переопределения части методов (декораторы) без ручной реализации всех остальных методов интерфейса."
  },
  {
    "num": 45,
    "title": "Изоляция методов при объявлении типов type MyInt int и безопасность примитивов",
    "task": "Изучите \"Aliasing\" типов. Создайте тип type MyInt int и добавьте к нему метод. Попробуйте вызвать этот метод у обычной переменной типа int. Убедитесь, что так нельзя, и поймите, почему это защищает от случайного изменения поведения встроенных типов.",
    "theory": "Создание нового типа type MyInt int изолирует его Method Set от базового int.",
    "step_by_step": "1. Объявляем type MyInt int.\n2. Реализуем метод Square() int.\n3. Показываем, что x := 5; x.Square() не компилируется.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype MyInt int\n\nfunc (m MyInt) Square() int {\n\treturn int(m * m)\n}\n\nfunc main() {\n\tvar custom MyInt = 7\n\tfmt.Printf(\"Квадрат %d: %d\\n\", custom, custom.Square())\n\n\t// ❌ ОШИБКА: raw := 7; raw.Square()\n\t// raw.Square undefined (type int has no field or method Square)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Квадрат 7: 49"
      }
    ],
    "under_the_hood": "Компилятор Go осуществляет строгий статический контроль типов.",
    "pitfalls": "- Путаница между Defined Type (type New int) и Type Alias (type Alias = int).",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем в Go запретили методы для примитивов?»\n**Ответ:** Для чистоты системы типов и предотвращения взаимного влияния сторонних библиотек."
  },
  {
    "num": 46,
    "title": "Затенение и переопределение методов: Car.Start() с вызовом c.Engine.Start()",
    "task": "[Теневание (Shadowing)]: В структуре Car из предыдущего задания добавь свой собственный метод Start(), который выводит \"Car starting...\", а затем вызывает встроенный метод c.Engine.Start(). (Переопределение методов).",
    "theory": "Переопределение позволяет добавить поведение перед или после вызова встроенного метода.",
    "step_by_step": "1. Создаем Engine{HP int}.\n2. Создаем Car со встраиванием Engine и собственным методом Start().\n3. Вызываем c.Engine.Start() внутри Car.Start().",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Engine struct{ HP int }\nfunc (e Engine) Start() { fmt.Printf(\"Двигатель (%d л.с.) урчит!\\n\", e.HP) }\n\ntype Car struct {\n\tEngine\n\tModel string\n}\n\nfunc (c Car) Start() {\n\tfmt.Printf(\"[%s] Инициализация систем зажигания...\\n\", c.Model)\n\tc.Engine.Start() // Явный вызов встроенного метода\n}\n\nfunc main() {\n\tc := Car{Engine: Engine{HP: 300}, Model: \"Audi RS\"}\n\tc.Start()\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# [Audi RS] Инициализация систем зажигания...\n# Двигатель (300 л.с.) урчит!"
      }
    ],
    "under_the_hood": "Вызовы методов компилируются в прямые статические вызовы функций.",
    "pitfalls": "- Рекурсивный вызов c.Start() вместо c.Engine.Start() (stack overflow).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в Go реализовать аналог super.Method() из Java?»\n**Ответ:** Через явное обращение к встроенному типу: c.EmbeddedType.Method()."
  },
  {
    "num": 47,
    "title": "Встроенный указатель *Item в структуре: nil-паника при доступе к полям против безопасности методов",
    "task": "Создай структуру с встроенным указателем *Item. Покажи, что если Item == nil, доступ к promoted полям вызывает панику. А вызов promoted метода — панику только если метод разыменовывает получателя без проверки.",
    "theory": "Встраивание указателей экономит память, но требует осторожности при неинициализированном nil-указателе.",
    "step_by_step": "1. Создаем Item{Title string} с безопасным методом GetTitle().\n2. Создаем Box со встроенным *Item.\n3. Демонстрируем безопасный вызов b.GetTitle() и панику b.Title при nil.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Item struct{ Title string }\n\nfunc (i *Item) GetTitle() string {\n\tif i == nil {\n\t\treturn \"(нет товара)\"\n\t}\n\treturn i.Title\n}\n\ntype Box struct {\n\t*Item // Встроенный указатель\n\tBoxID int\n}\n\nfunc main() {\n\tbox := Box{Item: nil, BoxID: 404}\n\n\t// 1. Метод вызывается безопасно благодаря nil-check:\n\tfmt.Printf(\"Товар в коробке #%d: %s\\n\", box.BoxID, box.GetTitle())\n\n\t// 2. Прямой доступ к promoted полю box.Title вызвал бы panic (nil dereference)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Товар в коробке #404: (нет товара)"
      }
    ],
    "under_the_hood": "Доступ к box.Title компилируется как box.Item.Title; если Item == 0x0, происходит SIGSEGV.",
    "pitfalls": "- Прямое обращение к полям встроенного указателя без проверки на nil.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем опасность встраивания указателей *T в структуры?»\n**Ответ:** Неинициализированное поле *T равно nil, и обращение к его полям вызывает панику в рантайме."
  },
  {
    "num": 48,
    "title": "Многоуровневая цепочка встраивания A -> B -> C и глубокое всплытие методов (Deep Promotion)",
    "task": "Создай цепочку встраивания: A встраивает B, B встраивает C. C имеет метод Hello(). Покажи, что Hello доступен напрямую на A (deep promotion).",
    "theory": "Go рекурсивно продвигает методы по всей цепочке встраивания любой глубины.",
    "step_by_step": "1. Создаем C{ Msg string } с методом Hello().\n2. Создаем B{ C } и A{ B }.\n3. Вызываем a.Hello().",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype C struct{ Msg string }\nfunc (c C) Hello() string { return \"Привет от C: \" + c.Msg }\n\ntype B struct{ C }\ntype A struct{ B }\n\nfunc main() {\n\ta := A{B: B{C: C{Msg: \"Deep Promotion работает!\"}}}\n\tfmt.Println(a.Hello()) // a -> b -> c -> Hello()\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Привет от C: Deep Promotion работает!"
      }
    ],
    "under_the_hood": "Компилятор производит поиск в ширину (BFS) по графу встраивания.",
    "pitfalls": "- Слишком глубокие цепочки встраивания ухудшают читаемость кода.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какова максимальная глубина встраивания в Go?»\n**Ответ:** Язык не ограничивает глубину, но на практике глубже 2 уровней встраивание не рекомендуется."
  },
  {
    "num": 49,
    "title": "Расширение типа time.Time: кастомный тип type MyTime time.Time и метод IsWeekend()",
    "task": "Создайте тип type MyTime time.Time и добавьте к нему метод IsWeekend() bool.",
    "theory": "Добавление доменных методов к типам стандартной библиотеки.",
    "step_by_step": "1. Объявляем type MyTime time.Time.\n2. Реализуем метод IsWeekend() bool.\n3. Тестируем на субботе и понедельнике.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"time\"\n)\n\ntype MyTime time.Time\n\nfunc (t MyTime) IsWeekend() bool {\n\tw := time.Time(t).Weekday()\n\treturn w == time.Saturday || w == time.Sunday\n}\n\nfunc main() {\n\tsaturday := MyTime(time.Date(2026, 9, 5, 12, 0, 0, 0, time.UTC))\n\tmonday := MyTime(time.Date(2026, 9, 7, 12, 0, 0, 0, time.UTC))\n\n\tfmt.Println(\"Суббота выходной? \", saturday.IsWeekend())\n\tfmt.Println(\"Понедельник выходной?\", monday.IsWeekend())\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Суббота выходной?  true\n# Понедельник выходной? false"
      }
    ],
    "under_the_hood": "Каст time.Time(t) имеет нулевую стоимость в рантайме.",
    "pitfalls": "- Потеря методов time.Time на MyTime (их нужно вызывать через приведение к time.Time(t)).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему MyTime не наследует методы time.Time?»\n**Ответ:** Defined type не наследует methods базового типа. Чтобы сохранить методы, используют встраивание struct { time.Time }."
  },
  {
    "num": 50,
    "title": "Автоматическое приведение получателя: авто-взятие адреса и разыменование в Point",
    "task": "Автоматическое приведение получателя: Создайте структуру Point с методом-указателем MoveX(dx int) и методом-значением GetX() int.\n* Создайте значение переменной p := Point{X: 1} и вызовите p.MoveX(5).\n* Создайте указатель pPtr := &Point{X: 1} и вызовите pPtr.GetX().\nОбъясните, как компилятор Go автоматически подставляет взятие адреса (&) или разыменование (*) для удобного вызова методов.",
    "theory": "Синтаксический сахар компилятора Go устраняет необходимость вручную писать (*ptr) и (&val).",
    "step_by_step": "1. Создаем Point{X int}.\n2. Реализуем (p *Point) MoveX(dx int).\n3. Реализуем (p Point) GetX() int.\n4. Тестируем авто-взятие адреса и авто-разыменование.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Point struct{ X int }\n\nfunc (p *Point) MoveX(dx int) { p.X += dx }\nfunc (p Point) GetX() int     { return p.X }\n\nfunc main() {\n\t// 1. Авто-взятие адреса (&p).MoveX(5):\n\tp := Point{X: 1}\n\tp.MoveX(5)\n\tfmt.Println(\"После MoveX:\", p.GetX())\n\n\t// 2. Авто-разыменование (*pPtr).GetX():\n\tpPtr := &Point{X: 100}\n\tfmt.Println(\"GetX через указатель:\", pPtr.GetX())\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# После MoveX: 6\n# GetX через указатель: 100"
      }
    ],
    "under_the_hood": "Компилятор анализирует тип переменной и сигнатуру метода в AST.",
    "pitfalls": "- Думать, что вызов GetX на указателе меняет копию.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда автоматическое взятие адреса невозможно?»\n**Ответ:** Для неадресуемых выражений (литералы, возвращаемые значения функций, значения мап)."
  },
  {
    "num": 51,
    "title": "Переопределение методов (Shadowing): кастомная логика Withdraw в CreditAccount с кредитным лимитом",
    "task": "Переопределение методов (Shadowing): Для CreditAccount напиши свой метод Withdraw(amount float64) error, который позволяет уходить в минус до уровня CreditLimit, вызывая оригинальный метод (например, через прямое изменение баланса или вызов c.account.Withdraw, если бы поле было доступно).",
    "theory": "Переопределение метода с изменением бизнес-правил расхода средств.",
    "step_by_step": "1. Создаем базовый Account.\n2. Создаем CreditAccount со встраиванием Account и полем CreditLimit.\n3. Переопределяем Withdraw.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n)\n\ntype Account struct{ Balance float64 }\n\nfunc (a *Account) Withdraw(amt float64) error {\n\tif amt > a.Balance { return errors.New(\"недостаточно средств\") }\n\ta.Balance -= amt\n\treturn nil\n}\n\ntype CreditAccount struct {\n\tAccount\n\tCreditLimit float64\n}\n\nfunc (c *CreditAccount) Withdraw(amt float64) error {\n\tif amt > c.Balance+c.CreditLimit {\n\t\treturn fmt.Errorf(\"превышен кредитный лимит (доступно %.2f)\", c.Balance+c.CreditLimit)\n\t}\n\tc.Balance -= amt\n\treturn nil\n}\n\nfunc main() {\n\tca := &CreditAccount{Account: Account{Balance: 100}, CreditLimit: 500}\n\t_ = ca.Withdraw(400)\n\tfmt.Printf(\"Баланс после овердрафта: %.2f руб.\\n\", ca.Balance)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Баланс после овердрафта: -300.00 руб."
      }
    ],
    "under_the_hood": "ca.Withdraw вызывает метод верхнего уровня CreditAccount.",
    "pitfalls": "- Забыть проверить общий доступный лимит (Balance + CreditLimit).",
    "bigtech_interview": "**Вопрос с собеседования:** «Можно ли вызвать оригинальный метод Account.Withdraw из CreditAccount?»\n**Ответ:** Да, через явное обращение ca.Account.Withdraw(amt)."
  },
  {
    "num": 52,
    "title": "Композиция интерфейсов: объединение io.Reader, io.Writer и io.Closer в ReadWriteCloser",
    "task": "Композиция интерфейсов: определите ReadWriteCloser, объединяющий io.Reader, io.Writer, io.Closer. Реализуйте в своей обёртке над файлом.",
    "theory": "Интерфейсная композиция формирует богатые абстракции из маленьких контрактов.",
    "step_by_step": "1. Объявляем интерфейс ReadWriteCloser.\n2. Создаем MockFileSession.\n3. Реализуем Read, Write, Close.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n)\n\ntype ReadWriteCloser interface {\n\tio.Reader\n\tio.Writer\n\tio.Closer\n}\n\ntype MockFileSession struct {\n\tclosed bool\n}\n\nfunc (m *MockFileSession) Read(p []byte) (int, error)  { return 0, io.EOF }\nfunc (m *MockFileSession) Write(p []byte) (int, error) { return len(p), nil }\nfunc (m *MockFileSession) Close() error                 { m.closed = true; return nil }\n\nfunc main() {\n\tvar rwc ReadWriteCloser = &MockFileSession{}\n\t_, _ = rwc.Write([]byte(\"лог\"))\n\t_ = rwc.Close()\n\tfmt.Println(\"Сессия закрыта успешно!\")\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Сессия закрыта успешно!"
      }
    ],
    "under_the_hood": "Таблица itab связывает 3 метода с конкретной структурой.",
    "pitfalls": "- Забыть реализовать хотя бы один метод композитного интерфейса.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем польза композиции маленьких интерфейсов?»\n**Ответ:** Соблюдение Interface Segregation Principle (ISP) — клиенты зависят только от тех методов, которые им реально нужны."
  },
  {
    "num": 53,
    "title": "Приоритет собственных методов над promoted: переопределение метода Read в обертке io.Reader",
    "task": "Создай структуру, встраивающую io.Reader. Переопредели метод Read на внешней структуре (например, добавь логирование). Покажи, что собственный метод имеет приоритет над promoted.",
    "theory": "Собственные методы структуры имеют наивысший приоритет (глубина 0).",
    "step_by_step": "1. Создаем LoggingReader со встраиванием io.Reader.\n2. Реализуем метод Read с логированием.\n3. Тестируем чтение.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n\t\"strings\"\n)\n\ntype LoggingReader struct {\n\tio.Reader // Встроенный Reader\n}\n\nfunc (l *LoggingReader) Read(p []byte) (int, error) {\n\tn, err := l.Reader.Read(p)\n\tfmt.Printf(\"[LOG]: Прочитано %d байт\\n\", n)\n\treturn n, err\n}\n\nfunc main() {\n\tsrc := strings.NewReader(\"Go OOP Exercises\")\n\tlr := &LoggingReader{Reader: src}\n\tout := make([]byte, 8)\n\t_, _ = lr.Read(out)\n\tfmt.Printf(\"Данные: %q\\n\", string(out))\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# [LOG]: Прочитано 8 байт\n# Данные: \"Go OOP E\""
      }
    ],
    "under_the_hood": "Компилятор связывает вызов с LoggingReader.Read, минуя автоматическое делегирование.",
    "pitfalls": "- Не передавать вызов l.Reader.Read, что сломает поток данных.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как называется этот архитектурный паттерн?»\n**Ответ:** Паттерн Декоратор (Decorator) на базе встраивания интерфейса."
  },
  {
    "num": 54,
    "title": "Реализация интерфейса fmt.Stringer для структуры User с форматированием User: <Email>",
    "task": "Напишите метод String() (реализация интерфейса fmt.Stringer), который форматирует структуру User в красивый вид вида User: <Email>.",
    "theory": "fmt.Stringer переопределяет стандартное представление объекта в fmt.Print.",
    "step_by_step": "1. Создаем User{Email string, Role string}.\n2. Реализуем метод String() string.\n3. Выводим через fmt.Println.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype User struct {\n\tEmail string\n\tRole  string\n}\n\nfunc (u User) String() string {\n\treturn fmt.Sprintf(\"User: <%s> [%s]\", u.Email, u.Role)\n}\n\nfunc main() {\n\tu := User{Email: \"architect@ozon.ru\", Role: \"Admin\"}\n\tfmt.Println(u)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# User: <architect@ozon.ru> [Admin]"
      }
    ],
    "under_the_hood": "Пакет fmt через рефлексию или type assertion проверяет v.(fmt.Stringer).",
    "pitfalls": "- Вызов fmt.Sprintf(\"%s\", u) внутри String() (приведет к бесконечной рекурсии и панике).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в методе String() нельзя писать `return fmt.Sprintf(\"%v\", u)`?»\n**Ответ:** Спецификатор `%v` или `%s` для `u` снова вызовет метод `u.String()`, что приведет к бесконечной взаимной рекурсии и падению по stack overflow."
  },
  {
    "num": 55,
    "title": "Сравнение Embedding vs Explicit Composition: анонимное встраивание против явного поля",
    "task": "Сравни embedding и explicit composition: создай два варианта Logger (один с embed io.Writer, другой с полем writer io.Writer). Покажи разницу в доступе к методам, полям и удовлетворении интерфейсов.",
    "theory": "Embedding открывает методы наружу (IS-A), а явное поле скрывает их внутри структуры (HAS-A).",
    "step_by_step": "1. Создаем EmbeddedLogger{ io.Writer }.\n2. Создаем ExplicitLogger{ w io.Writer }.\n3. Сравниваем удовлетворение интерфейса io.Writer.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"bytes\"\n\t\"fmt\"\n\t\"io\"\n)\n\n// 1. Embedding (IS-A / Promoted):\ntype EmbeddedLogger struct{ io.Writer }\n\n// 2. Explicit Composition (HAS-A / Encapsulated):\ntype ExplicitLogger struct{ w io.Writer }\n\nfunc main() {\n\tbuf := &bytes.Buffer{}\n\tel := EmbeddedLogger{Writer: buf}\n\txl := ExplicitLogger{w: buf}\n\n\t// el автоматически является io.Writer:\n\tvar w io.Writer = el\n\tfmt.Fprintf(w, \"Запись через EmbeddedLogger\\n\")\n\n\t// xl НЕ является io.Writer (нет всплытия метода Write):\n\t// var bad io.Writer = xl // ❌ Ошибка компиляции\n\t_ = xl\n\n\tfmt.Print(buf.String())\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Запись через EmbeddedLogger"
      }
    ],
    "under_the_hood": "Embedding генерирует прокси-таблицу методов в itab структуры.",
    "pitfalls": "- Использование Embedding, когда методы внутреннего типа не должны быть частью публичного API.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда предпочесть явное поле вместо встраивания?»\n**Ответ:** Когда нужно скрыть детали реализации (инкапсуляция) и контролировать доступ к вложенному объекту."
  },
  {
    "num": 56,
    "title": "Каверзный кейс: перекрытие одинаковых полей Name в структуре B со встроенной A",
    "task": "[Каверзный кейс]: Создай структуру A с полем Name string и структуру B, встраивающую A. У B тоже есть поле Name. Создай экземпляр B. Выведи b.Name и b.A.Name (покажи, как работает разрешение конфликтов имен при встраивании).",
    "theory": "Собственное поле структуры b.Name затеняет встроенное поле b.A.Name.",
    "step_by_step": "1. Создаем A{Name string}.\n2. Создаем B{A, Name string}.\n3. Инициализируем и выводим b.Name и b.A.Name.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype A struct{ Name string }\ntype B struct {\n\tA\n\tName string\n}\n\nfunc main() {\n\tb := B{\n\t\tA:    A{Name: \"Родительское Имя\"},\n\t\tName: \"Собственное Имя\",\n\t}\n\tfmt.Println(\"b.Name:   \", b.Name)\n\tfmt.Println(\"b.A.Name: \", b.A.Name)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# b.Name:    Собственное Имя\n# b.A.Name:  Родительское Имя"
      }
    ],
    "under_the_hood": "Компилятор находит поле Name на глубине 0 и останавливает поиск.",
    "pitfalls": "- Думать, что b.Name перезаписывает b.A.Name (это два разных участка памяти).",
    "bigtech_interview": "**Вопрос с собеседования:** «Сколько байт занимает структура B?»\n**Ответ:** 32 байта (два string по 16 байт каждый: b.A.Name и b.Name)."
  },
  {
    "num": 57,
    "title": "Инспекция встраивания через reflect.TypeOf: флаг field.Anonymous == true",
    "task": "Используй reflect.TypeOf на структуре с embedded полем. Покажи, что embedded struct видно как отдельное поле с именем типа, у которого Anonymous = true.",
    "theory": "Рефлексия различает явные поля и анонимно встроенные структуры с помощью флага Anonymous.",
    "step_by_step": "1. Создаем Base и Container со встраиванием Base.\n2. Обходим поля через reflect.TypeOf(c).Field(i).\n3. Выводим field.Name и field.Anonymous.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"reflect\"\n)\n\ntype Base struct{ ID int }\ntype Container struct {\n\tBase   // Anonymous embedded\n\tTitle  string\n}\n\nfunc main() {\n\tc := Container{Base: Base{101}, Title: \"Тест\"}\n\tt := reflect.TypeOf(c)\n\tfor i := 0; i < t.NumField(); i++ {\n\t\tf := t.Field(i)\n\t\tfmt.Printf(\"Поле #%d: %-8s (Тип: %-12s, Anonymous: %t)\\n\", i, f.Name, f.Type, f.Anonymous)\n\t}\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Поле #0: Base     (Тип: main.Base   , Anonymous: true)\n# Поле #1: Title    (Тип: string      , Anonymous: false)"
      }
    ],
    "under_the_hood": "В метаданных рантайма поле имеет флаг StructField.Anonymous.",
    "pitfalls": "- Попытка искать promoted поля через t.Field(i) на первом уровне (они находятся внутри вложенного t.Field(0).Type).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как сериализаторы JSON находят promoted поля?»\n**Ответ:** Рекурсивным обходом рефлексии по полям с флагом Anonymous == true."
  },
  {
    "num": 58,
    "title": "Управление состоянием файла: структура File с методами Open, Read, Close (Pointer Receiver)",
    "task": "Создайте структуру File и добавьте к ней методы Open(), Read(), Close(). Используйте pointer receiver для всех методов, изменяющих состояние (например, флаг isOpen).",
    "theory": "Pointer Receiver для синхронизации и изменения внутреннего флага состояния.",
    "step_by_step": "1. Создаем File{name string, isOpen bool}.\n2. Реализуем Open(), Read(), Close().\n3. Проверяем переходы состояний.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n)\n\ntype VirtualFile struct {\n\tname   string\n\tisOpen bool\n}\n\nfunc (f *VirtualFile) Open() error {\n\tif f.isOpen { return errors.New(\"файл уже открыт\") }\n\tf.isOpen = true\n\tfmt.Printf(\"Файл %q открыт\\n\", f.name)\n\treturn nil\n}\n\nfunc (f *VirtualFile) Close() error {\n\tif !f.isOpen { return errors.New(\"файл уже закрыт\") }\n\tf.isOpen = false\n\tfmt.Printf(\"Файл %q закрыт\\n\", f.name)\n\treturn nil\n}\n\nfunc main() {\n\tf := &VirtualFile{name: \"app.log\"}\n\t_ = f.Open()\n\t_ = f.Close()\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Файл \"app.log\" открыт\n# Файл \"app.log\" закрыт"
      }
    ],
    "under_the_hood": "Мутация флага isOpen происходит напрямую по адресу структуры.",
    "pitfalls": "- Использование Value Receiver, из-за чего флаг isOpen останется неизменным.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в io.Closer метод Close() обычно требует Pointer Receiver?»\n**Ответ:** Потому что закрытие ресурса изменяет внутреннее состояние структуры и освобождает системный дескриптор."
  },
  {
    "num": 59,
    "title": "Паттерн Стратегия (Strategy Pattern): интерфейс PaymentStrategy и функция Checkout",
    "task": "Паттерн «Стратегия»: интерфейс PaymentStrategy с методом Pay(amount float64). Реализуйте стратегии CreditCard и PayPal. Функция Checkout(amount float64, strategy PaymentStrategy) вызывает оплату.",
    "theory": "Паттерн Strategy позволяет динамически подменять алгоритмы оплаты в рантайме.",
    "step_by_step": "1. Объявляем PaymentStrategy{ Pay(float64) }.\n2. Реализуем CreditCard и PayPal.\n3. Пишем функцию Checkout.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype PaymentStrategy interface {\n\tPay(amount float64)\n}\n\ntype CreditCard struct{ Number string }\nfunc (c CreditCard) Pay(amt float64) {\n\tfmt.Printf(\"Оплата %.2f руб. картой %s\\n\", amt, c.Number)\n}\n\ntype SBP struct{ Phone string }\nfunc (s SBP) Pay(amt float64) {\n\tfmt.Printf(\"Оплата %.2f руб. через СБП (%s)\\n\", amt, s.Phone)\n}\n\nfunc Checkout(amount float64, strategy PaymentStrategy) {\n\tstrategy.Pay(amount)\n}\n\nfunc main() {\n\tCheckout(2500, CreditCard{Number: \"*4412\"})\n\tCheckout(1200, SBP{Phone: \"+7-999-***-00\"})\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Оплата 2500.00 руб. картой *4412\n# Оплата 1200.00 руб. через СБП (+7-999-***-00)"
      }
    ],
    "under_the_hood": "Полиморфный вызов через интерфейс без switch/case.",
    "pitfalls": "- Жесткая привязка Checkout к конкретной платежной системе.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем преимущество паттерна Strategy в микросервисах?»\n**Ответ:** Позволяет легко подключать новые платежные шлюзы без изменения клиентского кода оформления заказов (Open-Closed Principle)."
  },
  {
    "num": 60,
    "title": "Инкапсулированные конструкторы: приватная структура member и строгая валидация NewMember",
    "task": "Инкапсулированные конструкторы: В пакете user создайте приватную структуру member. Напишите экспортируемую функцию-конструктор NewMember(email string) (*member, error), которая проверяет email на наличие символа @. Если валидация не пройдена, возвращайте ошибку. Попробуйте создать экземпляр member в обход конструктора из пакета main.",
    "theory": "Приватная структура гарантирует создание объектов исключительно через валидирующий конструктор.",
    "step_by_step": "1. Моделируем приватную структуру member.\n2. Реализуем NewMember с проверкой strings.Contains(email, \"@\").\n3. Проверяем валидные и невалидные случаи.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n\t\"strings\"\n)\n\ntype member struct {\n\temail string\n}\n\nfunc NewMember(email string) (*member, error) {\n\tif !strings.Contains(email, \"@\") {\n\t\treturn nil, errors.New(\"некорректный email: отсутствует символ @\")\n\t}\n\treturn &member{email: email}, nil\n}\n\nfunc (m *member) Email() string { return m.email }\n\nfunc main() {\n\tm, err := NewMember(\"senior@avito.ru\")\n\tif err != nil { panic(err) }\n\tfmt.Println(\"Успешно создан участник:\", m.Email())\n\n\t_, errInvalid := NewMember(\"bad_email\")\n\tif errInvalid != nil {\n\t\tfmt.Println(\"❌ Валидация отклонила:\", errInvalid)\n\t}\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Успешно создан участник: senior@avito.ru\n# ❌ Валидация отклонила: некорректный email: отсутствует символ @"
      }
    ],
    "under_the_hood": "Неэкспортируемый тип member невозможно инстанцировать из другого пакета через литерал member{}.",
    "pitfalls": "- Экспорт структуры member с маленькой буквы, но публичными полями.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем делать саму структуру неэкспортируемой?»\n**Ответ:** Чтобы принудительно заставить пользователей создавать объекты только через фабричную функцию New, соблюдая 100% инварианты."
  },
  {
    "num": 61,
    "title": "Паттерн Mixin в Go: композиция поведения LoggerMixin и MetricsMixin в структуре Service",
    "task": "Реализуй \"mixin\" паттерн: создай несколько маленьких структур (LoggerMixin с методом Log, MetricsMixin с методом Record) и встрой их в большую структуру Service. Покажи, как Service получает все методы миксинов.",
    "theory": "Паттерн Mixin позволяет собирать сложные сервисы из независимых строительных блоков поведения.",
    "step_by_step": "1. Создаем LoggerMixin{Log(string)}.\n2. Создаем MetricsMixin{Record(string)}.\n3. Создаем Service со встраиванием обоих миксинов.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype LoggerMixin struct{}\nfunc (LoggerMixin) Log(msg string) { fmt.Println(\"[LOG]:\", msg) }\n\ntype MetricsMixin struct{}\nfunc (MetricsMixin) Record(metric string) { fmt.Println(\"[METRIC]:\", metric, \"+1\") }\n\ntype OrderService struct {\n\tLoggerMixin\n\tMetricsMixin\n}\n\nfunc (s *OrderService) CreateOrder(id int) {\n\ts.Log(fmt.Sprintf(\"Создание заказа #%d\", id))\n\ts.Record(\"orders_created_total\")\n}\n\nfunc main() {\n\tsvc := &OrderService{}\n\tsvc.CreateOrder(777)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# [LOG]: Создание заказа #777\n# [METRIC]: orders_created_total +1"
      }
    ],
    "under_the_hood": "Методы миксинов автоматически всплывают в пространстве имен OrderService.",
    "pitfalls": "- Коллизия имен методов между несколькими миксинами.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие миксинов в Go от трейтов в Rust или миксинов в Python?»\n**Ответ:** В Go миксины — это обычное структурное встраивание (композиция), без специального синтаксиса трейтов."
  },
  {
    "num": 62,
    "title": "Границы пакетов и безопасность памяти: почему взлом приватных полей через unsafe является антипаттерном",
    "task": "Попробуйте изменить приватное поле структуры из другого пакета с помощью пакета unsafe и пакета reflect. Поймите, почему это антипаттерн и как Go защищает границы пакетов на этапе компиляции.",
    "theory": "Пакет unsafe позволяет обойти проверки компилятора через адресную арифметику, но ломает гарантии безопасности памяти и обратной совместимости.",
    "step_by_step": "1. Создаем структуру с приватным полем secret int.\n2. Читаем и модифицируем через unsafe.Pointer.\n3. Объясняем риски для продакшена.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"unsafe\"\n)\n\ntype SecureContainer struct {\n\tPublicInfo string\n\tsecretCode int // Приватное поле\n}\n\nfunc NewContainer() SecureContainer {\n\treturn SecureContainer{PublicInfo: \"Открыто\", secretCode: 1234}\n}\n\nfunc main() {\n\tc := NewContainer()\n\tfmt.Printf(\"До взлома: PublicInfo=%s\\n\", c.PublicInfo)\n\n\t// Взлом приватного поля secretCode через unsafe:\n\tptr := (*int)(unsafe.Pointer(uintptr(unsafe.Pointer(&c)) + unsafe.Offsetof(c.secretCode)))\n\t*ptr = 9999 // Принудительная перезапись приватного поля\n\n\tfmt.Printf(\"После unsafe модификации secretCode=%d\\n\", *ptr)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# До взлома: PublicInfo=Открыто\n# После unsafe модификации secretCode=9999"
      }
    ],
    "under_the_hood": "unsafe.Pointer отключает статический typechecker компилятора.",
    "pitfalls": "- Использование unsafe в бизнес-логике (приведет к падениям при изменении выравнивания полей компилятором).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему использование unsafe для приватных полей запрещено в BigTech CI/CD?»\n**Ответ:** Потому что это нарушает инкапсуляцию, приводит к UB (неопределенному поведению) при обновлении версий Go и ломает оптимизации компилятора."
  },
  {
    "num": 63,
    "title": "Полная инкапсуляция сущности: неэкспортируемая структура person.person с фабрикой и геттерами",
    "task": "Создай пакет person со неэкспортируемой структурой person с неэкспортируемыми полями. Напиши экспортируемый конструктор NewPerson(name string, age int) *person и экспортируемые getter/setter методы.",
    "theory": "100% инкапсуляция скрывает структуру и все ее поля за публичным интерфейсом методов.",
    "step_by_step": "1. Моделируем person с приватными name и age.\n2. Реализуем NewPerson, Name(), SetName(), Age(), SetAge().\n3. Тестируем в main.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype personEntity struct {\n\tname string\n\tage  int\n}\n\nfunc NewPerson(name string, age int) *personEntity {\n\treturn &personEntity{name: name, age: age}\n}\n\nfunc (p *personEntity) Name() string     { return p.name }\nfunc (p *personEntity) Age() int        { return p.age }\nfunc (p *personEntity) SetAge(a int)    { if a > 0 { p.age = a } }\n\nfunc main() {\n\tp := NewPerson(\"Екатерина\", 26)\n\tp.SetAge(27)\n\tfmt.Printf(\"%s: %d лет\\n\", p.Name(), p.Age())\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Екатерина: 27 лет"
      }
    ],
    "under_the_hood": "Все манипуляции производятся строго через вызовы методов.",
    "pitfalls": "- Отсутствие проверки в сеттерах.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда стоит скрывать саму структуру?»\n**Ответ:** В библиотеках и SDK, когда структура должна оставаться непрозрачной (Opaque Struct) для сохранения обратной совместимости."
  },
  {
    "num": 64,
    "title": "Инкапсуляция банковского счета BankAccount с целочисленным балансом и проверкой валидности",
    "task": "Инкапсуляция: Создай структуру BankAccount с приватным полем balance int. Напиши конструктор NewBankAccount(initial int) *BankAccount и методы Deposit, Withdraw (с проверкой баланса) и GetBalance.",
    "theory": "Контроль целочисленного баланса в копейках.",
    "step_by_step": "1. Создаем BankAccount{balance int}.\n2. Реализуем NewBankAccount, Deposit, Withdraw, GetBalance.\n3. Проверяем валидность операций.",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n)\n\ntype BankAccount struct{ balance int }\n\nfunc NewBankAccount(init int) *BankAccount {\n\tif init < 0 { init = 0 }\n\treturn &BankAccount{balance: init}\n}\n\nfunc (b *BankAccount) GetBalance() int { return b.balance }\n\nfunc (b *BankAccount) Deposit(amt int) error {\n\tif amt <= 0 { return errors.New(\"неверная сумма\") }\n\tb.balance += amt\n\treturn nil\n}\n\nfunc (b *BankAccount) Withdraw(amt int) error {\n\tif amt > b.balance { return errors.New(\"недостаточно средств\") }\n\tb.balance -= amt\n\treturn nil\n}\n\nfunc main() {\n\tb := NewBankAccount(5000)\n\t_ = b.Deposit(2000)\n\t_ = b.Withdraw(1500)\n\tfmt.Println(\"Баланс:\", b.GetBalance(), \"копеек\")\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Баланс: 5500 копеек"
      }
    ],
    "under_the_hood": "Атомарные изменения целочисленного значения.",
    "pitfalls": "- Пропуск проверки amt <= 0.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему для балансов не используют uint64?»\n**Ответ:** Потому что вычитание большего из меньшего в unsigned типах приводит к переполнению (Underflow) в огромное положительное число."
  },
  {
    "num": 65,
    "title": "Иммутабельные структуры данных (Value Object): Counter с возвратом новой копии WithValue",
    "task": "Реализуй immutable структуру Counter: поля неэкспортируемые, методы WithValue(v int) Counter возвращают новую копию, не меняя оригинал. Покажи, что оригинал остаётся неизменным.",
    "theory": "Паттерн Value Object: любые модификации порождают новый неизменяемый объект.",
    "step_by_step": "1. Создаем Counter{val int}.\n2. Реализуем метод (c Counter) WithValue(v int) Counter.\n3. Показываем неизменность оригинала c1 после вызова c2 := c1.WithValue(20).",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype ImmutableCounter struct {\n\tval int\n}\n\nfunc NewImmutableCounter(v int) ImmutableCounter {\n\treturn ImmutableCounter{val: v}\n}\n\nfunc (c ImmutableCounter) Value() int {\n\treturn c.val\n}\n\n// WithValue возвращает НОВЫЙ экземпляр, оригинал не меняется:\nfunc (c ImmutableCounter) WithValue(v int) ImmutableCounter {\n\treturn ImmutableCounter{val: v}\n}\n\nfunc main() {\n\tc1 := NewImmutableCounter(10)\n\tc2 := c1.WithValue(50)\n\n\tfmt.Printf(\"Оригинал c1: %d\\n\", c1.Value())\n\tfmt.Printf(\"Новый c2:     %d\\n\", c2.Value())\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run main.go\n# Оригинал c1: 10\n# Новый c2:     50"
      }
    ],
    "under_the_hood": "Структура копируется по значению в регистрах процессора.",
    "pitfalls": "- Случайное использование pointer receiver, разрушающее иммутабельность.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем преимущество иммутабельных структур в конкурентном Go-коде?»\n**Ответ:** Иммутабельные структуры на 100% потокобезопасны без мьютексов, так как горутины только читают неизменяемые данные."
  }
]
