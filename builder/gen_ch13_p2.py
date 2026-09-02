# Chapter 13 Part 2: Exercises 25 to 48

exercises = [
    {
        "num": 25,
        "title": "Теги структур struct tags: опция omitempty в json и сериализация нулевых значений",
        "task": "Используй теги структур: json:\"name,omitempty\". Сериализуй структуру в JSON через encoding/json. Покажи, как omitempty пропускает zero value.",
        "theory": """
**Теги структур (Struct Tags) и `omitempty`:**
- Теги — это строковые метаданные, прикрепленные к полям структуры в обратных кавычках: `` `json:"key,omitempty"` ``;
- Опция `omitempty` указывает кодировщику `encoding/json` **пропускать поле в JSON**, если оно имеет Zero Value (`0`, `""`, `false`, `nil`);
- Исключение: для примитивов `int` значение `0` тоже считается нулевым и опускается (чтобы отправить `0`, используют указатель `*int`).
""",
        "step_by_step": """
1. Создаем структуру `UserProfile` с тегами `json:"..."`.
2. Создаем экземпляр с заполненными и нулевыми полями.
3. Сериализуем через `json.MarshalIndent`.
4. Анализируем сгенерированный JSON.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"encoding/json"
	"fmt"
)

type UserProfile struct {
	ID        int      `json:"id"`
	Nickname  string   `json:"nickname"`
	Bio       string   `json:"bio,omitempty"`       // Пропускается, если ""
	Followers int      `json:"followers,omitempty"` // Пропускается, если 0
	Interests []string `json:"interests,omitempty"` // Пропускается, если nil или []
}

func main() {
	u := UserProfile{
		ID:       101,
		Nickname: "gopher_master",
		Bio:      "", // Zero value -> будет исключено из JSON благодаря omitempty
	}

	jsonData, err := json.MarshalIndent(u, "", "  ")
	if err != nil {
		panic(err)
	}

	fmt.Println(string(jsonData))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# {
#   "id": 101,
#   "nickname": "gopher_master"
# }"""
            }
        ],
        "under_the_hood": """
Пакет `encoding/json` парсит теги через `reflect.StructTag.Get("json")` при инициализации энкодера.
""",
        "pitfalls": """
- Написание тега с пробелами `` `json: "name"` `` — синтаксическая ошибка формата тегов! Пробелы внутри тегов запрещены.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как с помощью тегов принудительно исключить приватное или секретное поле из JSON?»
**Ответ:** Использовать тег `` `json:"-"` ``.
"""
    },
    {
        "num": 26,
        "title": "Множественные теги структур (json, db, yaml) и чтение через reflect.StructTag",
        "task": "Создай структуру с тегами для нескольких кодировок: json:\"user_name\" db:\"username\". Прочитай теги через reflect.TypeOf().Field().Tag и выведи.",
        "theory": """
**Спецификация мульти-тегов в Go:**
- Теги могут содержать несколько пар `ключ:"значение"`, разделенных пробелом: `` `json:"user_id" db:"id" validate:"required"` ``;
- Метод `tag.Get("db")` возвращает значение для конкретного ключа.
""",
        "step_by_step": """
1. Создаем структуру `AccountEntity` с тегами `json`, `db`, `validate`.
2. Получаем тип через `reflect.TypeOf(AccountEntity{})`.
3. Итерируемся по полям и считываем теги.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"reflect"
)

type AccountEntity struct {
	ID       int64  `json:"id" db:"account_id" validate:"required"`
	Username string `json:"user_name" db:"username" validate:"min=3"`
}

func main() {
	t := reflect.TypeOf(AccountEntity{})

	fmt.Printf("Инспекция метаданных структуры %s:\n", t.Name())
	for i := 0; i < t.NumField(); i++ {
		field := t.Field(i)
		jsonTag := field.Tag.Get("json")
		dbTag := field.Tag.Get("db")
		valTag := field.Tag.Get("validate")

		fmt.Printf("  Поле %-10s | json: %-12s | db: %-12s | val: %s\n",
			field.Name, jsonTag, dbTag, valTag)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Инспекция метаданных структуры AccountEntity:
#   Поле ID         | json: id           | db: account_id   | val: required
#   Поле Username   | json: user_name    | db: username     | val: min=3"""
            }
        ],
        "under_the_hood": """
Теги хранятся в бинарном мета-описании типов сегмента `.rodata`.
""",
        "pitfalls": """
- Использование метода `tag.Lookup("key")`, когда требуется отличить отсутствие тега от пустого значения.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как работают популярные валидаторы структур вроде `go-playground/validator`?»
**Ответ:** Они парсят теги `` `validate:"..."` `` через рефлексию при старте приложения, кэшируют правила валидации и проверяют значения полей структур в рантайме.
"""
    },
    {
        "num": 27,
        "title": "Создание и заполнение анонимной структуры прямо в main",
        "task": "Создай анонимную структуру прямо внутри функции main, запиши в неё данные и выведи.",
        "theory": """
Быстрое создание локальных контейнеров данных.
""",
        "step_by_step": """
1. Создаем переменную с анонимным структурным типом.
2. Заполняем поля `Metric`, `Value`, `Timestamp`.
3. Печатаем.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"time"
)

func main() {
	telemetry := struct {
		Metric    string
		Value     float64
		Timestamp time.Time
	}{
		Metric:    "cpu_temp_celsius",
		Value:     48.5,
		Timestamp: time.Now(),
	}

	fmt.Printf("Метрика: %s = %.1f°C (зафиксировано в %s)\n",
		telemetry.Metric, telemetry.Value, telemetry.Timestamp.Format("15:04:05"))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Метрика: cpu_temp_celsius = 48.5°C (зафиксировано в 15:04:05)"""
            }
        ],
        "under_the_hood": """
Локальный стек функции `main`.
""",
        "pitfalls": """
- Попытка создать метод для анонимной структуры (методы разрешены только для именованных типов).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли объявить анонимную структуру с методами?»
**Ответ:** НЕТ, в Go методы объявляются только для именованных типов (`type ...`). Но анонимная структура может содержать поля-функции `struct { Action func() }`.
"""
    },
    {
        "num": 28,
        "title": "Затенение полей (Field Shadowing): приоритет собственного поля структуры над встроенным",
        "task": "Затенение полей: Добавь в Employee поле City. Какое поле выведет emp.City — из работника или из его адреса? Проверь на практике.",
        "theory": """
**Правило затенения (Shadowing Rule) в иерархии композиции:**
- Поле с меньшей глубиной вложенности (глубина 0) **всегда затеняет** поле с большей глубиной (глубина 1);
- Выражение `emp.City` обращается к `Employee.City` (глубина 0);
- Доступ к встроенному полю сохраняется через явное квалифицированное имя `emp.Address.City` (глубина 1).
""",
        "step_by_step": """
1. Создаем `Address{City string}`.
2. Создаем `Employee{Address; City string; Name string}`.
3. Сравниваем `emp.City` и `emp.Address.City`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Address struct {
	City string // Глубина 1
}

type Employee struct {
	Address        // Встроенная структура
	City    string // Глубина 0 (ЗАТЕНЯЕТ Address.City!)
	Name    string
}

func main() {
	emp := Employee{
		Address: Address{City: "Санкт-Петербург (Адрес прописки)"},
		City:    "Москва (Фактический офис)",
		Name:    "Виктор",
	}

	// 1. Прямой доступ вернет поле нулевой глубины (Employee.City):
	fmt.Printf("1. emp.City:         %s\n", emp.City)

	// 2. Доступ к затененному полю:
	fmt.Printf("2. emp.Address.City: %s\n", emp.Address.City)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. emp.City:         Москва (Фактический офис)
# 2. emp.Address.City: Санкт-Петербург (Адрес прописки)"""
            }
        ],
        "under_the_hood": """
Компилятор ищет селектор в таблице символов сверху вниз по уровням вложенности.
""",
        "pitfalls": """
- Неожиданная перезапись встроенного поля при добавлении одноименного поля во внешнюю структуру.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что произойдет, если внешняя структура затенит метод встроенного типа?»
**Ответ:** Метод внешней структуры будет вызван по умолчанию при `obj.Method()`, а метод встроенного типа останется доступен через `obj.EmbeddedType.Method()`.
"""
    },
    {
        "num": 29,
        "title": "Фабричный конструктор NewPerson(name, age) *Person: зачем возвращать указатель",
        "task": "Напиши конструктор NewPerson(name string, age int) *Person. Объясни, зачем возвращать указатель (чтобы избежать копирования и позволить методам с pointer receiver).",
        "theory": """
**Преимущества возврата `*T` из конструкторов:**
1. **Исключение копирования:** передача объекта другим функциям занимает всего 8 байт (адрес);
2. **Поддержка Pointer Receivers:** экземпляр сразу готов к вызову методов-мутаторов;
3. **Единый источник истины (Single Source of Truth):** все компоненты ссылаются на один и тот же объект в памяти.
""",
        "step_by_step": """
1. Пишем `NewPerson(name string, age int) *Person`.
2. Возвращаем `&Person{name: name, age: age}`.
3. Проверяем работу.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Person struct {
	Name string
	Age  int
}

func NewPerson(name string, age int) *Person {
	return &Person{
		Name: name,
		Age:  age,
	}
}

func main() {
	p := NewPerson("Тимофей", 30)
	fmt.Printf("Создан объект: %+v (адрес: %p)\n", *p, p)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Создан объект: {Name:Тимофей Age:30} (адрес: 0xc000018030)"""
            }
        ],
        "under_the_hood": """
`runtime.newobject` аллоцирует структуру в куче.
""",
        "pitfalls": """
- Создание конструктора для крошечных неизменяемых структур (например `Point{X, Y int}`), где возврат по значению `Point` быстрее и эффективнее для GC.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В каких случаях конструктор должен возвращать значение `T`, а не указатель `*T`?»
**Ответ:** Для маленьких неизменяемых структур-значений (Value Objects), таких как `time.Date(...) time.Time` или `image.Point`.
"""
    },
    {
        "num": 30,
        "title": "Встраивание структур: композиция Person в Driver и всплытие полей (Field Promotion)",
        "task": "Встраивание структур (Embedding): Создайте структуру Person с полями Name и Age. Создайте структуру Driver, встроив в неё Person анонимно (без указания имени поля), и добавив поле LicenseCategory. Продемонстрируйте прямой доступ к полю Name через экземпляр Driver (эффект \"всплытия\" полей / field promotion).",
        "theory": """
Моделирование ролевой модели через композицию типов.
""",
        "step_by_step": """
1. Создаем `type Person struct { Name string; Age int }`.
2. Создаем `type Driver struct { Person; LicenseCategory string }`.
3. Демонстрируем `driver.Name` и `driver.LicenseCategory`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Person struct {
	Name string
	Age  int
}

type Driver struct {
	Person          // Встраивание (Field Promotion)
	LicenseCategory string
}

func main() {
	d := Driver{
		Person:          Person{Name: "Владимир", Age: 40},
		LicenseCategory: "B, C",
	}

	// Прямой доступ к всплывшим полям Person:
	fmt.Printf("Водитель: %s (%d лет) | Категория прав: %s\n",
		d.Name, d.Age, d.LicenseCategory)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Водитель: Владимир (40 лет) | Категория прав: B, C"""
            }
        ],
        "under_the_hood": """
Поля `Name` и `Age` лежат в начале структуры `Driver`.
""",
        "pitfalls": """
- Попытка приведения типов `var p Person = d` (ошибка компиляции — `Driver` НЕ является подтипом `Person`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли передать `Driver` в функцию, принимающую `Person`?»
**Ответ:** НЕТ! В Go нет полиморфизма подтипов для структур. Нужно либо передавать `d.Person`, либо использовать интерфейсы.
"""
    },
    {
        "num": 31,
        "title": "Универсальная инспекция структуры PrintStructFields(v any) через рефлексию (reflect.Type)",
        "task": "Напиши функцию PrintStructFields(v interface{}), которая через рефлексию (reflect.Type) отображает все поля структуры: имя, тип, теги, экспортированность.",
        "theory": """
**Рефлексивный анализ структур (`reflect.Type`):**
- Метод `t.NumField()` возвращает количество полей;
- Метод `t.Field(i)` возвращает дескриптор `reflect.StructField` (`Name`, `Type`, `Tag`, `PkgPath`, `IsExported()`).
""",
        "step_by_step": """
1. Пишем `PrintStructFields(v any)`.
2. Извлекаем `reflect.TypeOf(v)`.
3. Итерируемся по полям и форматируем отчет.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"reflect"
)

type ServerConfig struct {
	Host      string `json:"host"`
	Port      int    `json:"port"`
	secretKey string // Приватное поле
}

func PrintStructFields(v any) {
	t := reflect.TypeOf(v)
	if t.Kind() == reflect.Pointer {
		t = t.Elem()
	}
	if t.Kind() != reflect.Struct {
		fmt.Println("Ошибка: ожидалась структура")
		return
	}

	fmt.Printf("Структура: %s (%d полей)\n", t.Name(), t.NumField())
	for i := 0; i < t.NumField(); i++ {
		f := t.Field(i)
		fmt.Printf("  #%d: Имя=%-12s | Тип=%-8s | Экспорт=%-5t | Тег=%q\n",
			i+1, f.Name, f.Type.String(), f.IsExported(), f.Tag)
	}
}

func main() {
	cfg := ServerConfig{Host: "0.0.0.0", Port: 8080, secretKey: "jwt-token"}
	PrintStructFields(cfg)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Структура: ServerConfig (3 полей)
#   #1: Имя=Host         | Тип=string   | Экспорт=true  | Тег="json:\"host\""
#   #2: Имя=Port         | Тип=int      | Экспорт=true  | Тег="json:\"port\""
#   #3: Имя=secretKey    | Тип=string   | Экспорт=false | Тег="" """
            }
        ],
        "under_the_hood": """
Метаданные типов считываются из таблиц runtime type info.
""",
        "pitfalls": """
- Вызов `t.Field(i)` без проверки `t.Kind() == reflect.Struct` (приведет к панике).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как определить, является ли поле структуры экспортируемым (Public) через рефлексию?»
**Ответ:** Через метод `f.IsExported()` (начиная с Go 1.17) или проверку `f.PkgPath == ""`.
"""
    },
    {
        "num": 32,
        "title": "Продвижение методов: структура Car с анонимным полем Engine и прямой вызов car.Start()",
        "task": "Анонимные поля: структура Car с анонимным полем Engine. Покажите продвижение методов.",
        "theory": """
Автоматическое всплытие методов встроенных структур.
""",
        "step_by_step": """
1. Создаем `type Engine struct { Horsepower int }`.
2. Пишем метод `(e Engine) Start()`.
3. Создаем `type Car struct { Engine; Model string }`.
4. Вызываем `car.Start()` напрямую.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Engine struct {
	Horsepower int
}

func (e Engine) Start() {
	fmt.Printf("  Двигатель запущен! Мощность: %d л.с.\n", e.Horsepower)
}

type Car struct {
	Engine
	Model string
}

func main() {
	c := Car{
		Engine: Engine{Horsepower: 249},
		Model:  "Audi A6",
	}

	fmt.Printf("Автомобиль: %s\n", c.Model)

	// Метод Start() всплыл из встроенной структуры Engine:
	c.Start()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Автомобиль: Audi A6
#   Двигатель запущен! Мощность: 249 л.с."""
            }
        ],
        "under_the_hood": """
Связывание метода происходит статически во время компиляции.
""",
        "pitfalls": """
- Предположение, будто метод `Start()` знает о модели `Car` (встроенный метод видит только свой собственный `Engine`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Может ли метод встроенного `Engine` обратиться к полю `Car.Model`?»
**Ответ:** НЕТ! Встроенная структура полностью автономна и не имеет ссылки на внешнюю структуру-обертку.
"""
    },
    {
        "num": 33,
        "title": "Прямой вызов методов встроенного объекта Engine через объект Car",
        "task": "Создайте структуру Car, которая содержит встроенную (embedded) структуру Engine. Вызовите методы Engine напрямую через объект Car.",
        "theory": """
Закрепление синтаксиса вызова методов через композицию.
""",
        "step_by_step": """
1. Добавляем методы `Start()` и `Stop()`.
2. Вызываем оба метода через экземпляр `Car`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Engine struct {
	RPM int
}

func (e *Engine) Accelerate() {
	e.RPM += 1000
	fmt.Printf("Обороты двигателя: %d RPM\n", e.RPM)
}

type Car struct {
	Engine
	Brand string
}

func main() {
	car := Car{Brand: "BMW"}
	car.Accelerate()
	car.Accelerate()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Обороты двигателя: 1000 RPM
# Обороты двигателя: 2000 RPM"""
            }
        ],
        "under_the_hood": """
Метод с pointer receiver мутирует встроенное поле `RPM`.
""",
        "pitfalls": """
- Вызов метода на неадресуемой структуре.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как работает неявное взятие адреса при `car.Accelerate()`?»
**Ответ:** Компилятор подставляет `(&car.Engine).Accelerate()`.
"""
    },
    {
        "num": 34,
        "title": "Каверзный кейс: срез указателей []*Point и пакетная мутация координат в цикле",
        "task": "[Каверзный кейс]: Создай структуру Point с полями X, Y int. В цикле создай срез указателей на структуры []*Point. Изменяй поля через указатели.",
        "theory": """
**Коллекции указателей на структуры `[]*T`:**
- Каждый элемент среза — это 8-байтный указатель на отдельную структуру в куче;
- Позволяет изменять состояние объектов без их копирования и синхронизировать изменения между несколькими коллекциями.
""",
        "step_by_step": """
1. Создаем `type Point struct { X, Y int }`.
2. Создаем срез `[]*Point`.
3. В цикле модифицируем координаты `pt.X += 10`.
4. Печатаем результаты.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Point struct {
	X, Y int
}

func main() {
	var points []*Point

	// Инициализируем срез указателей:
	for i := 1; i <= 3; i++ {
		points = append(points, &Point{X: i * 10, Y: i * 20})
	}

	fmt.Println("До модификации:")
	for idx, pt := range points {
		fmt.Printf("  points[%d] = %+v (адрес: %p)\n", idx, *pt, pt)
	}

	// Модифицируем поля через указатели:
	for _, pt := range points {
		pt.X += 5
		pt.Y += 5
	}

	fmt.Println("После модификации:")
	for idx, pt := range points {
		fmt.Printf("  points[%d] = %+v\n", idx, *pt)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До модификации:
#   points[0] = {X:10 Y:20} (адрес: 0xc000018030)
#   points[1] = {X:20 Y:40} (адрес: 0xc000018038)
#   points[2] = {X:30 Y:60} (адрес: 0xc000018040)
# После модификации:
#   points[0] = {X:15 Y:25}
#   points[1] = {X:25 Y:45}
#   points[2] = {X:35 Y:65}"""
            }
        ],
        "under_the_hood": """
Срез хранит массив 8-байтных указателей.
""",
        "pitfalls": """
- Наличие `nil` среди элементов среза при разыменовании `pt.X`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем плюс `[]Point` перед `[]*Point` для сборщика мусора?»
**Ответ:** `[]Point` хранит все данные в одном непрерывном блоке памяти (1 аллокация, 0 указателей для сканирования GC). `[]*Point` создает $N+1$ аллокаций и нагружает GC сканированием каждого указателя.
"""
    },
    {
        "num": 35,
        "title": "Выравнивание полей в памяти (Memory Padding & Alignment) и оптимизация размера структур",
        "task": "Оптимизируй структуру по памяти: расположи поля от большего к меньшему (int64, int32, bool, byte). Измерь unsafe.Sizeof до и после. Покажи эффект padding/alignment.",
        "theory": """
**Механика Memory Alignment и Padding в Go:**
- Процессор быстрее читает данные, выровненные по границе их собственного размера (8-байтные типы выравниваются по адресу кратному 8, 4-байтные — кратному 4);
- Компилятор вставляет пустые байты (**Padding**), чтобы выровнять поля;
- **Правило оптимизации:** Сортировка полей от большего к меньшему размеру (`8B -> 4B -> 2B -> 1B`) минимизирует паддинг и экономит до 50% оперативной памяти!
""",
        "step_by_step": """
1. Создаем `BadStruct` с чередующимися типами.
2. Создаем `GoodStruct` с полями от большего к меньшему.
3. Сравниваем `unsafe.Sizeof`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"unsafe"
)

// Неоптимальный порядок полей (много пустого Padding):
type BadStruct struct {
	A bool   // 1 байт + 7 байт Padding
	B int64  // 8 байт
	C bool   // 1 байт + 7 байт Padding
}

// Оптимальный порядок полей (Padding сгруппирован):
type GoodStruct struct {
	B int64  // 8 байт
	A bool   // 1 байт
	C bool   // 1 байт + 6 байт Padding
}

func main() {
	var bad BadStruct
	var good GoodStruct

	fmt.Println("=== СРАВНЕНИЕ ВЫРАВНИВАНИЯ ПАМЯТИ (unsafe.Sizeof) ===")
	fmt.Printf("1. BadStruct (неупорядоченная): %2d байт\n", unsafe.Sizeof(bad))
	fmt.Printf("2. GoodStruct (оптимизированная): %2d байт (ЭКОНОМИЯ 33%%!)\n", unsafe.Sizeof(good))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# === СРАВНЕНИЕ ВЫРАВНИВАНИЯ ПАМЯТИ (unsafe.Sizeof) ===
# 1. BadStruct (неупорядоченная): 24 байт
# 2. GoodStruct (оптимизированная): 16 байт (ЭКОНОМИЯ 33%!)"""
            }
        ],
        "under_the_hood": """
`BadStruct` содержит 14 байт неиспользуемого пустого заполнителя (Padding) из 24 байт.
""",
        "pitfalls": """
- Хаотичное расположение полей в структурах, которые хранятся в миллионных срезах (приводит к перерасходу гигабайт RAM).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какой линтер автоматически проверяет и оптимизирует порядок полей в структурах Go?»
**Ответ:** `govet` с анализатором `fieldalignment` (`golangci-lint run --enable fieldalignment`).
"""
    },
    {
        "num": 36,
        "title": "Теги структур и сериализация в JSON (json.Marshal): игнорирование приватных полей",
        "task": "Теги структур и JSON (Marshal): Добавь к полям User теги `json:\"name\"` и `json:\"age,omitempty\"`. Используй json.Marshal из пакета encoding/json, чтобы получить JSON. Обрати внимание, что приватные поля (с маленькой буквы) в JSON не попадут.",
        "theory": """
**Правило видимости для сериализаторов:**
- `encoding/json` сериализует **ТОЛЬКО экспортируемые поля** (с заглавной буквы);
- Приватные неэкспортируемые поля игнорируются автоматически, даже если к ним приписан тег!
""",
        "step_by_step": """
1. Создаем `type User struct { Name string; Age int; secretToken string }`.
2. Сериализуем в JSON.
3. Убеждаемся в отсутствии `secretToken` в выводе.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"encoding/json"
	"fmt"
)

type User struct {
	Name        string `json:"name"`
	Age         int    `json:"age,omitempty"`
	secretToken string `json:"token"` // Приватное поле -> ИГНОРИРУЕТСЯ энкодером!
}

func main() {
	u := User{
		Name:        "Кирилл",
		Age:         28,
		secretToken: "secret_12345",
	}

	data, err := json.Marshal(u)
	if err != nil {
		panic(err)
	}

	fmt.Printf("JSON: %s\n", string(data))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# JSON: {"name":"Кирилл","age":28}"""
            }
        ],
        "under_the_hood": """
Рефлексия проверяет `f.PkgPath == ""` перед маршалингом поля.
""",
        "pitfalls": """
- Удивление, почему поле `json:"token"` не попадает в JSON (потому что имя поля `token` написано со строчной буквы).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как отправить приватное поле в JSON без его экспорта наружу?»
**Ответ:** Реализовать кастомный интерфейс `json.Marshaler` (`func (u User) MarshalJSON() ([]byte, error)`).
"""
    },
    {
        "num": 37,
        "title": "Потокобезопасный счетчик со встроенным sync.Mutex и всплытием методов Lock/Unlock",
        "task": "Создай структуру с встроенным sync.Mutex. Покажи, что методы Lock()/Unlock() \"продвигаются\" и доступны напрямую. Используй для потокобезопасного инкремента счётчика.",
        "theory": """
**Паттерн потокобезопасной структуры со встроенным Mutex:**
- Встраивание `sync.Mutex` в структуру продвигает методы `c.Lock()` и `c.Unlock()` на верхний уровень;
- **Важно:** Структуры со встроенным мьютексом **ОБЯЗАНЫ передаваться исключительно по указателю `*Counter`**, чтобы избежать копирования мьютекса!
""",
        "step_by_step": """
1. Создаем `type SafeCounter struct { sync.Mutex; value int }`.
2. Пишем методы `Inc()` и `Value() int`.
3. Запускаем 100 конкурентных горутин.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
)

type SafeCounter struct {
	sync.Mutex // Встроенный мьютекс
	value      int
}

func (c *SafeCounter) Inc() {
	c.Lock() // Прямой вызов продвинутого метода
	defer c.Unlock()
	c.value++
}

func (c *SafeCounter) Value() int {
	c.Lock()
	defer c.Unlock()
	return c.value
}

func main() {
	counter := &SafeCounter{}
	var wg sync.WaitGroup

	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			counter.Inc()
		}()
	}

	wg.Wait()
	fmt.Printf("Итоговое значение счетчика: %d (ПОЛНАЯ ПОТОКОБЕЗОПАСНОСТЬ!)\n", counter.Value())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run -race main.go
# Итоговое значение счетчика: 100 (ПОЛНАЯ ПОТОКОБЕЗОПАСНОСТЬ!)"""
            }
        ],
        "under_the_hood": """
Атомарная блокировка через `runtime/internal/atomic` в методе `sync.Mutex.Lock()`.
""",
        "pitfalls": """
- Вызов `counter := SafeCounter{}` с передачей по значению (копирование заблокированного мьютекса приведет к крашу или дедлоку).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Google Style Guide иногда рекомендуют именовать мьютекс `mu sync.Mutex` вместо анонимного встраивания?»
**Ответ:** Чтобы не раскрывать методы `Lock()` и `Unlock()` наружу в публичный API структуры (инкапсуляция механизма синхронизации внутри методов).
"""
    },
    {
        "num": 38,
        "title": "Двусторонняя сериализация/десериализация структуры User (json.Marshal и json.Unmarshal)",
        "task": "Теги структур и JSON: Создайте структуру User с тегами для JSON (например, json:\"user_id\"). Напишите код, который сериализует структуру в JSON-строку с помощью json.Marshal, и код, который десериализует JSON-строку обратно в структуру.",
        "theory": """
Полный цикл преобразования Go Struct $\leftrightarrow$ JSON Payload.
""",
        "step_by_step": """
1. Создаем структуру `type UserDTO struct { UserID int, Email string }`.
2. Сериализуем объект в строку JSON.
3. Десериализуем строку обратно в новый экземпляр `&parsedUser`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"encoding/json"
	"fmt"
)

type UserDTO struct {
	UserID int    `json:"user_id"`
	Email  string `json:"email"`
}

func main() {
	original := UserDTO{UserID: 777, Email: "dev@ozon.ru"}

	// 1. Сериализация (Marshal):
	bytes, err := json.Marshal(original)
	if err != nil {
		panic(err)
	}
	fmt.Printf("1. JSON строка:    %s\n", string(bytes))

	// 2. Десериализация (Unmarshal):
	var restored UserDTO
	if err := json.Unmarshal(bytes, &restored); err != nil {
		panic(err)
	}
	fmt.Printf("2. Восстановлено:  %+v\n", restored)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. JSON строка:    {"user_id":777,"email":"dev@ozon.ru"}
# 2. Восстановлено:  {UserID:777 Email:dev@ozon.ru}"""
            }
        ],
        "under_the_hood": """
`json.Unmarshal` использует рефлексию для поиска полей с соответствующими тегами и заполняет их по указателю.
""",
        "pitfalls": """
- Передача значения вместо указателя `json.Unmarshal(bytes, restored)` (ошибка `json: Unmarshal(non-pointer)`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `json.Unmarshal` требует передачи указателя `&restored`?»
**Ответ:** Потому что функции в Go не могут изменить значение переменной вызывающего кода без указателя на нее.
"""
    },
    {
        "num": 39,
        "title": "Методы PrintInfo() (Value Receiver) и UpdateYear() (Pointer Receiver): почему мутация требует указатель",
        "task": "Добавьте к структуре метод PrintInfo() с получателем по значению (value receiver) и метод UpdateYear() с получателем по указателю (pointer receiver). Объясните, почему для изменения состояния нужен указатель.",
        "theory": """
Разделение методов чтения (Read-Only) и методов записи (Mutators).
""",
        "step_by_step": """
1. Создаем `type Car struct { Model string; Year int }`.
2. Пишем `(c Car) PrintInfo()`.
3. Пишем `(c *Car) UpdateYear(year int)`.
4. Демонстрируем работу.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Car struct {
	Model string
	Year  int
}

// Value Receiver для чтения:
func (c Car) PrintInfo() {
	fmt.Printf("Автомобиль: %s (%d г.в.)\n", c.Model, c.Year)
}

// Pointer Receiver для мутации:
func (c *Car) UpdateYear(newYear int) {
	if c != nil {
		c.Year = newYear
	}
}

func main() {
	car := Car{Model: "Lada Vesta", Year: 2020}
	car.PrintInfo()

	car.UpdateYear(2024)
	car.PrintInfo()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Автомобиль: Lada Vesta (2020 г.в.)
# Автомобиль: Lada Vesta (2024 г.в.)"""
            }
        ],
        "under_the_hood": """
`PrintInfo` копирует 24 байта, `UpdateYear` получает адрес памяти.
""",
        "pitfalls": """
- Попытка мутировать `c.Year` в `PrintInfo`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какое практическое правило выбора между Value и Pointer Receiver?»
**Ответ:** Если хотя бы один метод изменяет состояние или структура содержит мьютекс — используйте Pointer Receiver для ВСЕХ методов типа.
"""
    },
    {
        "num": 40,
        "title": "Анонимное встраивание User в Employee и прямой доступ к emp.Name",
        "task": "Создай структуру Employee, которая анонимно встраивает (embedding) User. Обрати внимание, что поля User доступны напрямую (например, emp.Name).",
        "theory": """
Закрепление синтаксиса встраивания пользователей в доменные модели.
""",
        "step_by_step": """
1. Объявляем `User{ID int, Name string}`.
2. Объявляем `Employee{User; Department string}`.
3. Проверяем прямой доступ.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type User struct {
	ID   int
	Name string
}

type Employee struct {
	User
	Department string
}

func main() {
	emp := Employee{
		User:       User{ID: 101, Name: "Татьяна"},
		Department: "Platform Engineering",
	}

	fmt.Printf("Сотрудник: %s (ID: %d) | Отдел: %s\n", emp.Name, emp.ID, emp.Department)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Сотрудник: Татьяна (ID: 101) | Отдел: Platform Engineering"""
            }
        ],
        "under_the_hood": """
Смещение `emp.Name` рассчитывается как `emp + 8`.
""",
        "pitfalls": """
- Забыть структуру `User` в литерале инициализации.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как сериализуется встроенная структура в JSON по умолчанию?»
**Ответ:** Поля встроенной структуры сериализуются на верхний уровень JSON-объекта (Flatted JSON).
"""
    },
    {
        "num": 41,
        "title": "Десериализация json.Unmarshal: обязательная передача структуры по указателю &user",
        "task": "JSON Unmarshal: Создай строку с JSON. Используй json.Unmarshal, чтобы распарсить её в структуру User. Не забудь передать структуру по указателю!",
        "theory": """
Парсинг внешних JSON-ответов в типизированные структуры.
""",
        "step_by_step": """
1. Создаем строку с сырыми JSON-данными.
2. Парсим через `json.Unmarshal([]byte(raw), &user)`.
3. Обрабатываем ошибку парсинга.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"encoding/json"
	"fmt"
)

type User struct {
	Name   string `json:"name"`
	Role   string `json:"role"`
	Active bool   `json:"active"`
}

func main() {
	rawJSON := `{"name":"Михаил","role":"Admin","active":true}`

	var user User
	err := json.Unmarshal([]byte(rawJSON), &user)
	if err != nil {
		fmt.Println("Ошибка парсинга JSON:", err)
		return
	}

	fmt.Printf("Успешно распарсено: %+v\n", user)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Успешно распарсено: {Name:Михаил Role:Admin Active:true}"""
            }
        ],
        "under_the_hood": """
Токенизатор JSON сопоставляет ключи и заполняет поля структуры через `reflect.Value.Set`.
""",
        "pitfalls": """
- Передача `json.Unmarshal(data, user)` без `&` (возвращает `json.InvalidUnmarshalError`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что произойдет, если в JSON придет поле с несовместимым типом (например число вместо строки)?»
**Ответ:** `json.Unmarshal` вернет ошибку `*json.UnmarshalTypeError`, заполнив остальные корректные поля.
"""
    },
    {
        "num": 42,
        "title": "Встраивание интерфейса io.Reader в структуру: реализация через делегирование",
        "task": "Создай структуру, которая встраивает интерфейс io.Reader. Объясни, что это значит: структура реализует интерфейс через делегирование встроенному полю.",
        "theory": """
**Встраивание интерфейсов в структуры (Interface Embedding):**
- Структура может встраивать интерфейс `io.Reader` как анонимное поле;
- Это означает, что структура автоматически **удовлетворяет интерфейсу `io.Reader`**;
- Любой вызов `Read()` делегируется объекту, сохраненному во встроенном поле интерфейса;
- Мощный паттерн для создания декораторов потоков данных (Middleware / Wrappers).
""",
        "step_by_step": """
1. Создаем структуру `type CountingReader struct { io.Reader; TotalBytes int64 }`.
2. Переопределяем метод `Read(p []byte) (n int, err error)`.
3. Подсчитываем прочитанные байты.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"io"
	"strings"
)

type CountingReader struct {
	io.Reader // Встроенный интерфейс
	BytesRead int
}

func (cr *CountingReader) Read(p []byte) (int, error) {
	n, err := cr.Reader.Read(p) // Делегирование вызова
	cr.BytesRead += n
	return n, err
}

func main() {
	source := strings.NewReader("Привет, высоконагруженный мир Go!")
	counter := &CountingReader{Reader: source}

	buf := make([]byte, 16)
	for {
		n, err := counter.Read(buf)
		if n > 0 {
			fmt.Printf("Прочитано %d байт: %q\n", n, string(buf[:n]))
		}
		if err == io.EOF {
			break
		}
	}

	fmt.Printf("Всего прочитано байт: %d\n", counter.BytesRead)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Прочитано 16 байт: "Привет, вы"
# Прочитано 16 байт: "соконагруж"
# Прочитано 16 байт: "енный мир "
# Прочитано 11 байт: "Go!"
# Всего прочитано байт: 59"""
            }
        ],
        "under_the_hood": """
Структура хранит 16-байтный интерфейсный дескриптор `itab/data`.
""",
        "pitfalls": """
- Вызов `Read()` на структуре с `nil`-интерфейсом внутри (паника `nil pointer dereference`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Зачем встраивать интерфейсы в тестовые мок-структуры?»
**Ответ:** Чтобы удовлетворить гигантскому интерфейсу с 20 методами, переопределив только 1-2 нужных в тесте метода (остальные вызовы упадут с nil-паникой при обращении).
"""
    },
    {
        "num": 43,
        "title": "Теги полей json:'title,omitempty' и сериализация структур в JSON",
        "task": "Добавьте к структуре теги полей (например, json:\"title,omitempty\") и сериализуйте структуру в JSON с помощью json.Marshal.",
        "theory": """
Закрепление сериализации структур с тегами.
""",
        "step_by_step": """
1. Создаем структуру `Task{Title string, Done bool}`.
2. Сериализуем через `json.Marshal`.
3. Печатаем JSON.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"encoding/json"
	"fmt"
)

type Task struct {
	Title string `json:"title,omitempty"`
	Done  bool   `json:"is_completed"`
}

func main() {
	t1 := Task{Title: "Пройти модуль 13", Done: true}
	t2 := Task{Title: "", Done: false}

	b1, _ := json.Marshal(t1)
	b2, _ := json.Marshal(t2)

	fmt.Printf("t1: %s\n", string(b1))
	fmt.Printf("t2: %s (title опущен!)\n", string(b2))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# t1: {"title":"Пройти модуль 13","is_completed":true}
# t2: {"is_completed":false} (title опущен!)"""
            }
        ],
        "under_the_hood": """
Быстрая сериализация на основе AST тегов.
""",
        "pitfalls": """
- Опечатка `json:is_completed` (без кавычек).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как сделать так, чтобы число `ID int` сериализовалось в JSON как строка `"123"`?»
**Ответ:** Использовать тег `` `json:"id,string"` ``.
"""
    },
    {
        "num": 44,
        "title": "Паттерн Functional Options для гибкого конфигурирования серверов NewServer(opts ...Option)",
        "task": "Реализуй паттерн Functional Options: type Option func(*Server). Напиши WithHost(string), WithPort(int). Конструктор NewServer(opts ...Option) *Server.",
        "theory": """
**Паттерн Functional Options (Золотой стандарт конфигураций в Go):**
- Решает проблему перегрузки конструкторов (в Go нет перегрузки методов);
- Позволяет задавать дефолтные значения и гибко переопределять любые опции;
- Чистый, расширяемый и обратно-совместимый API.
""",
        "step_by_step": """
1. Создаем структуру `Server{host string, port int, timeout time.Duration}`.
2. Объявляем `type Option func(*Server)`.
3. Пишем опции `WithHost(h string)`, `WithPort(p int)`.
4. Пишем конструктор `NewServer(opts ...Option) *Server`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"time"
)

type Server struct {
	host    string
	port    int
	timeout time.Duration
}

type Option func(*Server)

func WithHost(host string) Option {
	return func(s *Server) {
		s.host = host
	}
}

func WithPort(port int) Option {
	return func(s *Server) {
		s.port = port
	}
}

func WithTimeout(timeout time.Duration) Option {
	return func(s *Server) {
		s.timeout = timeout
	}
}

func NewServer(opts ...Option) *Server {
	// Дефолтная конфигурация:
	srv := &Server{
		host:    "127.0.0.1",
		port:    8080,
		timeout: 30 * time.Second,
	}

	// Применяем пользовательские опции:
	for _, opt := range opts {
		opt(srv)
	}

	return srv
}

func main() {
	// Сервер с дефолтными настройками:
	s1 := NewServer()
	fmt.Printf("1. Дефолтный сервер: %s:%d (таймаут %v)\n", s1.host, s1.port, s1.timeout)

	// Сервер с кастомными опциями:
	s2 := NewServer(
		WithHost("api.production.ru"),
		WithPort(443),
		WithTimeout(5*time.Second),
	)
	fmt.Printf("2. Кастомный сервер: %s:%d (таймаут %v)\n", s2.host, s2.port, s2.timeout)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Дефолтный сервер: 127.0.0.1:8080 (таймаут 30s)
# 2. Кастомный сервер: api.production.ru:443 (таймаут 5s)"""
            }
        ],
        "under_the_hood": """
Замыкания опций передаются как срез функциональных указателей и последовательно мутируют структуру в куче.
""",
        "pitfalls": """
- Применение `nil`-опции в цикле (всегда проверяйте `if opt != nil`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему паттерн Functional Options предпочтительнее передачи структуры `Config`?»
**Ответ:** Он защищает от передачи неполных структур со случайными Zero Values, позволяет валидировать каждый параметр индивидуально и обеспечивает 100% обратную совместимость при добавлении новых опций.
"""
    },
    {
        "num": 45,
        "title": "Получатели методов: IncrementValue() (значение) vs IncrementPointer() (указатель) для Counter",
        "task": "Получатели методов: Для структуры Counter (поле value int) напишите два метода: IncrementValue() с получателем-значением ((c Counter)) и IncrementPointer() с получателем-указателем ((c *Counter)). Вызовите оба метода и проверьте, какой из них действительно увеличивает счетчик в исходном объекте.",
        "theory": """
Практическое сравнение поведения счетчиков при разных получателях.
""",
        "step_by_step": """
1. Создаем структуру `Counter{value int}`.
2. Пишем `(c Counter) IncrementValue()`.
3. Пишем `(c *Counter) IncrementPointer()`.
4. Сравниваем результаты.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Counter struct {
	value int
}

func (c Counter) IncrementValue() {
	c.value++ // Изменяет копию
}

func (c *Counter) IncrementPointer() {
	c.value++ // Изменяет оригинал
}

func main() {
	cnt := Counter{value: 10}

	cnt.IncrementValue()
	fmt.Printf("1. После IncrementValue:   %d (не изменился)\n", cnt.value)

	cnt.IncrementPointer()
	fmt.Printf("2. После IncrementPointer: %d (УВЕЛИЧЕН!)\n", cnt.value)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. После IncrementValue:   10 (не изменился)
# 2. После IncrementPointer: 11 (УВЕЛИЧЕН!)"""
            }
        ],
        "under_the_hood": """
`IncrementPointer` изменяет ячейку памяти напрямую по адресу.
""",
        "pitfalls": """
- Вызов метода на копии.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Может ли линтер найти ошибочный Value Receiver для мутатора?»
**Ответ:** Да, линтер `govet` (проверка `copylocks` и `lostcancel`) и `staticcheck` предупреждают о бесполезных присваиваниях в Value Receiver.
"""
    },
    {
        "num": 46,
        "title": "Сравнение структур Point{X, Y} через == и запрет сравнения при добавлении среза Meta []string",
        "task": "Сравнение структур: Создайте структуру Point с полями X, Y int. Сравните два экземпляра через ==. Теперь добавьте в структуру поле Meta []string (срез). Попробуйте снова сравнить структуры. Объясните поведение компилятора.",
        "theory": """
Детальный анализ статической проверки сравнимости типов (Type Comparability Checking).
""",
        "step_by_step": """
1. Создаем `Point{X, Y int}`.
2. Сравниваем `p1 == p2`.
3. Создаем `ExtendedPoint{X, Y int; Meta []string}`.
4. Показываем невозможность `==` и решение через `reflect.DeepEqual`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"reflect"
)

type Point struct {
	X, Y int
}

type ExtendedPoint struct {
	X, Y int
	Meta []string
}

func main() {
	p1 := Point{1, 2}
	p2 := Point{1, 2}
	fmt.Printf("Point: p1 == p2 -> %t\n", p1 == p2)

	ep1 := ExtendedPoint{X: 1, Y: 2, Meta: []string{"A", "B"}}
	ep2 := ExtendedPoint{X: 1, Y: 2, Meta: []string{"A", "B"}}

	// Сравнение через reflect.DeepEqual:
	equal := reflect.DeepEqual(ep1, ep2)
	fmt.Printf("ExtendedPoint: reflect.DeepEqual -> %t\n", equal)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Point: p1 == p2 -> true
# ExtendedPoint: reflect.DeepEqual -> true"""
            }
        ],
        "under_the_hood": """
Срезы содержат указатели на динамическую память, поэтому компилятор запрещает оператор `==` на этапе семантического анализа AST.
""",
        "pitfalls": """
- Использование `==` для структур с вложенными мапами или срезами.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go запретили оператор `==` для срезов и структур со срезами?»
**Ответ:** Потому что семантика равенства срезов неоднозначна (сравнивать физические указатели или поэлементные значения?), и глубокое поэлементное сравнение $O(N)$ скрыло бы тяжелые вычисления под простым оператором `==`.
"""
    },
    {
        "num": 47,
        "title": "Метод Greet() для структуры User со значением-получателем (Value Receiver)",
        "task": "Добавь метод Greet() для структуры User (value receiver).",
        "theory": """
Базовый метод чтения приветствия.
""",
        "step_by_step": """
1. Создаем структуру `User{Name string}`.
2. Пишем метод `(u User) Greet() string`.
3. Выводим строку приветствия.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type User struct {
	Name string
}

func (u User) Greet() string {
	return fmt.Sprintf("Здравствуйте, %s! Добро пожаловать в систему.", u.Name)
}

func main() {
	user := User{Name: "Екатерина"}
	fmt.Println(user.Greet())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Здравствуйте, Екатерина! Добро пожаловать в систему."""
            }
        ],
        "under_the_hood": """
Копирование строки в стек метода.
""",
        "pitfalls": """
- Опечатки в имени метода.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какой Method Set у типа `User`?»
**Ответ:** В Method Set значения `User` входят все методы с Value Receiver `(u User)`.
"""
    },
    {
        "num": 48,
        "title": "Структура, встраивающая несколько интерфейсов (io.Reader + io.Closer = io.ReadCloser)",
        "task": "Создай структуру, встраивающую несколько интерфейсов. Покажи, что она удовлетворяет всем встроенным интерфейсам автоматически, если реализует все необходимые методы.",
        "theory": """
**Множественное встраивание интерфейсов:**
- Встраивание `io.Reader` и `io.Closer` автоматически делает структуру совместимой с `io.ReadCloser`;
- Позволяет собирать композитные интерфейсные контракты.
""",
        "step_by_step": """
1. Создаем `type SessionStream struct { io.Reader; io.Closer }`.
2. Передаем экземпляр в функцию, ожидающую `io.ReadCloser`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"io"
	"strings"
)

type DummyCloser struct{}

func (DummyCloser) Close() error {
	fmt.Println("Поток успешно закрыт")
	return nil
}

type StreamWrapper struct {
	io.Reader
	io.Closer
}

func ProcessStream(rc io.ReadCloser) {
	defer rc.Close()
	buf := make([]byte, 32)
	n, _ := rc.Read(buf)
	fmt.Printf("Прочитано: %q\n", string(buf[:n]))
}

func main() {
	stream := StreamWrapper{
		Reader: strings.NewReader("Бинарные данные сессии"),
		Closer: DummyCloser{},
	}

	// StreamWrapper автоматически реализует io.ReadCloser:
	ProcessStream(stream)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Прочитано: "Бинарные данные сессии"
# Поток успешно закрыт"""
            }
        ],
        "under_the_hood": """
Компилятор генерирует интерфейсную таблицу `itab` для `io.ReadCloser`.
""",
        "pitfalls": """
- Передача структуры с незаполненными интерфейсными полями.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в стандартной библиотеке `net/http` реализован `http.Response.Body`?»
**Ответ:** Поле `Body` имеет тип `io.ReadCloser`, что требует от сетевого драйвера реализации методов `Read` и `Close`.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 2: {len(exercises)} exercises.")
