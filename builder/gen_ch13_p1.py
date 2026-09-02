# Chapter 13 Part 1: Exercises 1 to 24

exercises = [
    {
        "num": 1,
        "title": "Объявление базовой структуры User и способы инициализации (именованный vs позиционный)",
        "task": "Базовая структура: Объяви структуру User с полями Name (строка) и Age (число). Инициализируй её 1) с указанием имен полей, 2) без указания имен полей (строго по порядку).",
        "theory": """
**Структуры (Structs) в Go:**
- Структура — это составной пользовательский тип данных, объединяющий именованные поля;
- **Именованная инициализация (`User{Name: "Иван", Age: 30}`):** промышленный стандарт Go. Порядок полей не важен, неинициализированные поля получают Zero Values, устойчива к добавлению новых полей;
- **Позиционная инициализация (`User{"Иван", 30}`):** требует строгого порядка и указания ВСЕХ полей (хрупкая, ломается при изменении структуры).
""",
        "step_by_step": """
1. Объявляем `type User struct { Name string; Age int }`.
2. Создаем `u1` с именованными полями.
3. Создаем `u2` позиционным литералом.
4. Выводим экземпляры через `fmt.Printf("%+v\n")`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type User struct {
	Name string
	Age  int
}

func main() {
	// 1. Именованная инициализация (рекомендуемый промышленный стандарт):
	u1 := User{
		Name: "Иван",
		Age:  30,
	}

	// 2. Позиционная инициализация (строго по порядку всех полей):
	u2 := User{"Ольга", 25}

	fmt.Printf("u1 (именованный): %+v\n", u1)
	fmt.Printf("u2 (позиционный): %+v\n", u2)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# u1 (именованный): {Name:Иван Age:30}
# u2 (позиционный): {Name:Ольга Age:25}"""
            }
        ],
        "under_the_hood": """
Структура `User` размещается в памяти как непрерывный блок из 24 байт (16 байт строка `Name` + 8 байт число `Age`).
""",
        "pitfalls": """
- Использование позиционной инициализации в публичных библиотеках: добавление любого поля в структуру ломает код всех пользователей библиотеки!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему линтеры (`golangci-lint`, `exhaustive`) запрещают позиционную инициализацию структур в production-коде?»
**Ответ:** Потому что позиционная инициализация хрупка к рефакторингу (добавление поля ломает компиляцию, а перестановка полей одного типа `string, string` приводит к скрытым багам подстановки данных).
"""
    },
    {
        "num": 2,
        "title": "Инкапсуляция неэкспортируемых полей и публичные методы доступа (Getters/Setters)",
        "task": "Создай структуру в отдельном пакете с неэкспортируемыми полями (имена с маленькой буквы). Попробуй обратиться к полям из main — получи ошибку компиляции. Напиши экспортируемые getter/setter методы.",
        "theory": """
**Инкапсуляция и видимость в Go:**
- В Go нет ключевых слов `private/public/protected`;
- Видимость определяется первой буквой идентификатора: заглавная буква (`Name`) — экспортируемое поле (Public), строчная (`age`) — неэкспортируемое (Private для пакета);
- Доступ для чтения и записи с валидацией реализуется через методы `Getter` и `Setter`.
""",
        "step_by_step": """
1. Создаем структуру с приватными полями `name string`, `age int`.
2. Пишем конструктор `NewAccount(name string, age int) *Account`.
3. Пишем методы `Age() int` (геттер) и `SetAge(age int) error` (сеттер с валидацией).
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"errors"
	"fmt"
)

type Account struct {
	name string // Неэкспортируемое поле (private)
	age  int    // Неэкспортируемое поле (private)
}

func NewAccount(name string, age int) (*Account, error) {
	if age < 0 {
		return nil, errors.New("возраст не может быть отрицательным")
	}
	return &Account{name: name, age: age}, nil
}

// Геттер для age (в Go идиоматично называть Age(), а не GetAge()):
func (a *Account) Age() int {
	return a.age
}

// Сеттер с валидацией инвариантов:
func (a *Account) SetAge(age int) error {
	if age < 0 {
		return errors.New("недопустимый возраст")
	}
	a.age = age
	return nil
}

func main() {
	acc, err := NewAccount("Алексей", 28)
	if err != nil {
		panic(err)
	}

	fmt.Printf("Текущий возраст: %d лет\n", acc.Age())

	if err := acc.SetAge(29); err != nil {
		fmt.Println("Ошибка:", err)
	}

	fmt.Printf("Обновленный возраст: %d лет\n", acc.Age())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Текущий возраст: 28 лет
# Обновленный возраст: 29 лет"""
            }
        ],
        "under_the_hood": """
Компилятор проверяет границы пакета на этапе синтаксического анализа (Type Checking) и запрещает доступ к `acc.age` вне определяющего пакета.
""",
        "pitfalls": """
- Именование геттеров в стиле Java `GetAge()`: в Go принято называть геттер просто по имени поля `Age()`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go не рекомендуется писать тривиальные геттеры/сеттеры для всех полей подряд?»
**Ответ:** Если поле не требует валидации и потокобезопасности, в Go принято делать его просто экспортируемым `Age int` (Keep It Simple).
"""
    },
    {
        "num": 3,
        "title": "Анонимные структуры (Anonymous Structs) для локальных DTO и конфигураций",
        "task": "Анонимная структура: Создай структуру прямо в main без объявления типа (cfg := struct{ Host string }{ Host: \"localhost\" }). Отлично подходит для временных данных или тестов.",
        "theory": """
**Анонимные структуры (Anonymous / Inline Structs):**
- Объявляются по месту без создания именованного типа `type ... struct`;
- Идеальны для табличных юнит-тестов (Table-Driven Tests), парсинга разовых JSON-ответов и локальных DTO;
- Не засоряют область видимости пакета.
""",
        "step_by_step": """
1. Создаем анонимную структуру `cfg := struct{ Host string; Port int }{...}`.
2. Выводим поля.
3. Демонстрируем вложенный срез анонимных структур.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	// Анонимная структура конфигурации прямо в теле функции:
	cfg := struct {
		Host string
		Port int
		TLS  bool
	}{
		Host: "api.company.internal",
		Port: 8443,
		TLS:  true,
	}

	fmt.Printf("Конфигурация сервера: %s:%d (TLS=%t)\n", cfg.Host, cfg.Port, cfg.TLS)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Конфигурация сервера: api.company.internal:8443 (TLS=true)"""
            }
        ],
        "under_the_hood": """
Компилятор генерирует анонимный тип с внутренним именем и рассчитывает смещение полей в локальном фрейме.
""",
        "pitfalls": """
- Переиспользование сложных анонимных структур в сигнатурах публичных функций (ухудшает читаемость кода).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли сравнить две переменные анонимных структур через `==`?»
**Ответ:** ДА, если они имеют идентичный набор полей с одинаковыми именами и типами в том же порядке, и все поля являются сравнимыми (comparable).
"""
    },
    {
        "num": 4,
        "title": "Метод с указателем-получателем (Pointer Receiver): func (p *Person) Birthday()",
        "task": "Напиши метод с pointer receiver: func (p *Person) Birthday(). Увеличь возраст на 1. Покажи, что оригинал изменился. Объясни, когда использовать pointer receiver.",
        "theory": """
**Pointer Receiver `(p *Person)`:**
- Получает указатель на оригинальную структуру в памяти;
- **Когда использовать:**
  1. Метод должен модифицировать поля структуры (мутатор);
  2. Структура тяжелая ($> 64$ байт), и нужно избежать копирования;
  3. Структура содержит `sync.Mutex` (мьютексы нельзя копировать!).
""",
        "step_by_step": """
1. Создаем структуру `Person{Name string, Age int}`.
2. Пишем метод `(p *Person) Birthday()`.
3. Вызываем метод и проверяем мутацию.
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

func (p *Person) Birthday() {
	if p != nil {
		p.Age++ // Мутирует оригинальный объект в памяти!
	}
}

func main() {
	dev := Person{Name: "Дмитрий", Age: 25}
	fmt.Printf("До дня рождения:    %+v\n", dev)

	// Вызов метода автоматически берет адрес (&dev).Birthday():
	dev.Birthday()

	fmt.Printf("После дня рождения: %+v (ВОЗРАСТ УВЕЛИЧЕН!)\n", dev)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До дня рождения:    {Name:Дмитрий Age:25}
# После дня рождения: {Name:Дмитрий Age:26} (ВОЗРАСТ УВЕЛИЧЕН!)"""
            }
        ],
        "under_the_hood": """
При вызове `dev.Birthday()` компилятор Go подставляет `(&dev).Birthday()`, передавая 8-байтный адрес в регистр CPU.
""",
        "pitfalls": """
- Смешивание Value Receiver и Pointer Receiver для методов одного типа: идиоматичный Go требует консистентности (если один метод требует `*T`, делайте все методы `*T`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что произойдет, если вызвать метод `dev.Birthday()` на `dev`, которая не является указателем?»
**Ответ:** Компилятор Go автоматически возьмет адрес `&dev`, если переменная адресуема (Addressable).
"""
    },
    {
        "num": 5,
        "title": "Указатели на структуры: создание u := &User{} и автоматическое разыменование полей",
        "task": "Указатели на структуры: Создай указатель u := &User{}. Измени его поле: u.Name = \"Ivan\". (В Go не нужно писать (*u).Name или u->Name, компилятор сам разыменовывает указатель на структуру).",
        "theory": """
**Синтаксический сахар разыменования структур в Go:**
- В C++ для указателей используется стрелочка `u->Name`;
- В Go компилятор определяет, что `u` — это указатель `*User`, и автоматически транслирует `u.Name` в `(*u).Name`.
""",
        "step_by_step": """
1. Создаем `u := &User{Name: "Старт", Age: 18}`.
2. Меняем поле `u.Name = "Ivan"`.
3. Печатаем результат.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type User struct {
	Name string
	Age  int
}

func main() {
	u := &User{
		Name: "Аноним",
		Age:  18,
	}

	// Прямой доступ к полям через точку без оператора ->:
	u.Name = "Ivan"
	u.Age = 22

	fmt.Printf("Обновленный User: %+v (тип: %T, адрес: %p)\n", *u, u, u)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Обновленный User: {Name:Ivan Age:22} (тип: *main.User, адрес: 0xc000010060)"""
            }
        ],
        "under_the_hood": """
Инструкция процессора `MOVQ (u), RAX; MOVQ $str, (RAX)`.
""",
        "pitfalls": """
- Обращение `u.Name`, когда `u == nil` (паника `runtime error: nil pointer dereference`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова стоимость автоматического разыменования `u.Name`?»
**Ответ:** Нулевая на этапе выполнения — смещение поля вычисляется на этапе компиляции.
"""
    },
    {
        "num": 6,
        "title": "Сравнение передачи структуры: AgePerson(p Person) по значению vs AgePersonPtr(p *Person) по указателю",
        "task": "Напиши функцию AgePerson(p Person) (value) и AgePersonPtr(p *Person) (pointer). Вызови обе с одним и тем же Person. Покажи разницу. Объясни \"copy vs reference\" на уровне структур.",
        "theory": """
Сравнение изоляции стека и мутаций по указателю на уровне структур.
""",
        "step_by_step": """
1. Пишем `AgePerson(p Person)`.
2. Пишем `AgePersonPtr(p *Person)`.
3. Сравниваем результаты в `main()`.
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

func AgePerson(p Person) {
	p.Age += 10 // Изменяет локальную копию
}

func AgePersonPtr(p *Person) {
	if p != nil {
		p.Age += 10 // Изменяет оригинал в памяти
	}
}

func main() {
	p := Person{Name: "Максим", Age: 20}

	AgePerson(p)
	fmt.Printf("1. После AgePerson (Value):   %+v (копия, возраст 20)\n", p)

	AgePersonPtr(&p)
	fmt.Printf("2. После AgePersonPtr (Ptr):  %+v (оригинал, возраст 30)\n", p)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. После AgePerson (Value):   {Name:Максим Age:20} (копия, возраст 20)
# 2. После AgePersonPtr (Ptr):  {Name:Максим Age:30} (оригинал, возраст 30)"""
            }
        ],
        "under_the_hood": """
`AgePerson` копирует 24 байта на стек, а `AgePersonPtr` передает 8-байтный адрес в регистре `RAX`.
""",
        "pitfalls": """
- Передача структур с мьютексами по значению в функции.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему копирование структуры с `sync.Mutex` ломает синхронизацию?»
**Ответ:** Потому что копия мьютекса получит независимое состояние блокировки, и горутины будут блокировать разные мьютексы, вызывая Data Race.
"""
    },
    {
        "num": 7,
        "title": "Метод со значением-получателем (Value Receiver): func (u User) Birthday() и потеря мутаций",
        "task": "Метод (Value receiver): Добавь типу User метод func (u User) Birthday(). Внутри увеличь возраст на 1. Вызови метод в main и выведи юзера. Убедись, что возраст не изменился (метод работал с копией).",
        "theory": """
Value Receiver получает полную копию структуры в момент вызова.
""",
        "step_by_step": """
1. Создаем структуру `User{Name string, Age int}`.
2. Пишем метод `(u User) Birthday()`.
3. Убеждаемся в неизменности оригинала.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type User struct {
	Name string
	Age  int
}

func (u User) Birthday() {
	u.Age++
	fmt.Printf("  Внутри метода (копия): %+v\n", u)
}

func main() {
	u := User{Name: "Елена", Age: 30}
	fmt.Printf("До вызова:             %+v\n", u)

	u.Birthday()

	fmt.Printf("После вызова в main:   %+v (НЕ ИЗМЕНИЛСЯ!)\n", u)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До вызова:             {Name:Елена Age:30}
#   Внутри метода (копия): {Name:Елена Age:31}
# После вызова в main:   {Name:Елена Age:30} (НЕ ИЗМЕНИЛСЯ!)"""
            }
        ],
        "under_the_hood": """
Метод транслируется в обычную функцию `User.Birthday(u)`.
""",
        "pitfalls": """
- Ожидание мутации состояния от метода с Value Receiver.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Когда Value Receiver предпочтителен для методов?»
**Ответ:** Для неизменяемых объектов (Value Objects), структур малого размера ($\le 64$ байт), когда требуется гарантия отсутствия побочных эффектов.
"""
    },
    {
        "num": 8,
        "title": "Три способа инициализации структуры Person: позиционная, именованная и new(Person)",
        "task": "Объяви структуру Person с полями Name string, Age int. Создай экземпляр тремя способами: позиционная инициализация, именованные поля, new(Person). Выведи все три.",
        "theory": """
Сравнение всех базовых способов создания экземпляров.
""",
        "step_by_step": """
1. Создаем структуру `Person{Name string, Age int}`.
2. Инициализируем `p1`, `p2`, `p3`.
3. Сравниваем типы и значения.
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

func main() {
	// Способ 1: Позиционная инициализация (значение):
	p1 := Person{"Игорь", 20}

	// Способ 2: Именованная инициализация (значение):
	p2 := Person{Name: "Анна", Age: 22}

	// Способ 3: Через встроенную функцию new() (указатель с Zero Values):
	p3 := new(Person)
	p3.Name = "Виктор"
	p3.Age = 35

	fmt.Printf("1. Позиционный: %+v (%T)\n", p1, p1)
	fmt.Printf("2. Именованный: %+v (%T)\n", p2, p2)
	fmt.Printf("3. new(Person): %+v (%T)\n", *p3, p3)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Позиционный: {Name:Игорь Age:20} (main.Person)
# 2. Именованный: {Name:Анна Age:22} (main.Person)
# 3. new(Person): {Name:Виктор Age:35} (*main.Person)"""
            }
        ],
        "under_the_hood": """
`p1` и `p2` создаются на стеке (если не убегают), `p3` выделяет 24 зануленных байта.
""",
        "pitfalls": """
- Забыть разыменовать `p3` при передаче в функции, ожидающие `Person`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какой способ создания структур является самым распространенным в Go?»
**Ответ:** Литеральное взятие адреса `p := &Person{Name: "..."}`.
"""
    },
    {
        "num": 9,
        "title": "Встраивание структур (Struct Embedding) и автоматическое всплытие полей (Promoted Fields)",
        "task": "Создай структуру Address (City, Street). Встрой (embed) её в Person: type Person struct { Address; Name string }. Покажи, что поля City и Street \"продвигаются\" (promoted): p.City работает напрямую.",
        "theory": """
**Композиция и встраивание вместо наследования в Go:**
- В Go нет классического ООП-наследования (`extends`);
- Вместо этого используется **встраивание (Embedding / Composition)**: в структуру помещается анонимное поле типа `Address`;
- Поля и методы встроенного типа автоматически **«всплывают» (Promoted)** и становятся доступны напрямую через внешнюю структуру (`p.City` $\equiv$ `p.Address.City`).
""",
        "step_by_step": """
1. Создаем структуру `type Address struct { City, Street string }`.
2. Создаем `type Person struct { Address; Name string }`.
3. Инициализируем и проверяем прямой доступ `p.City`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Address struct {
	City   string
	Street string
}

type Person struct {
	Address // Встроенная структура (анонимное поле)
	Name    string
}

func main() {
	p := Person{
		Address: Address{City: "Москва", Street: "Тверская"},
		Name:    "Александр",
	}

	// 1. Прямой доступ к продвинутым полям (Promoted Fields):
	fmt.Printf("Сотрудник: %s, Город: %s, Улица: %s\n", p.Name, p.City, p.Street)

	// 2. Явный доступ через имя типа:
	fmt.Printf("Полный адрес: %s, %s\n", p.Address.City, p.Address.Street)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Сотрудник: Александр, Город: Москва, Улица: Тверская
# Полный адрес: Москва, Тверская"""
            }
        ],
        "under_the_hood": """
Компилятор разрешает селектор `p.City` в `p.Address.City` на этапе компиляции без оверхеда в рантайме.
""",
        "pitfalls": """
- Попытка инициализировать встроенные поля на верхнем уровне литерала `Person{City: "..."}` — ошибка компиляции, в литерале нужно указывать имя типа `Address: Address{...}`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Является ли встраивание структур в Go подлинным наследованием?»
**Ответ:** НЕТ! Это синтаксический сахар над композицией (Has-A, а не Is-A). Встроенная структура не знает о внешней структуре и не имеет полиморфного `vtable`.
"""
    },
    {
        "num": 10,
        "title": "Продвижение методов (Promoted Methods) при встраивании структур и интерфейс Stringer",
        "task": "Добавь метод String() string к Address. Покажи, что он доступен через встроенную структуру: p.String() вызывает метод встроенного поля (promoted method).",
        "theory": """
**Всплытие методов (Method Promotion):**
- Все методы встроенного типа автоматически становятся методами внешней структуры;
- Если `Address` реализует `fmt.Stringer`, то и `Person` автоматически удовлетворяет интерфейсу `fmt.Stringer`!
""",
        "step_by_step": """
1. Добавляем `(a Address) String() string`.
2. Вызываем `p.String()` напрямую через `Person`.
3. Проверяем работу `fmt.Println(p)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Address struct {
	City   string
	Street string
}

func (a Address) String() string {
	return fmt.Sprintf("г. %s, ул. %s", a.City, a.Street)
}

type Person struct {
	Address
	Name string
}

func main() {
	p := Person{
		Address: Address{City: "Санкт-Петербург", Street: "Невский проспект"},
		Name:    "Мария",
	}

	// Метод String() автоматически всплыл из Address:
	fmt.Printf("1. Вызов p.String(): %s\n", p.String())
	fmt.Printf("2. Печать через fmt:  %s\n", p)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Вызов p.String(): г. Санкт-Петербург, ул. Невский проспект
# 2. Печать через fmt:  г. Санкт-Петербург, ул. Невский проспект"""
            }
        ],
        "under_the_hood": """
Таблица методов структуры `Person` расширяется сигнатурами из `Address`.
""",
        "pitfalls": """
- Если `Person` определит свой собственный метод `String()`, он перекроет (Shadow) метод `Address.String()`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как вызвать оригинальный метод встроенной структуры, если он был перекрыт внешним типом?»
**Ответ:** Вызвать явно через имя встроенного типа: `p.Address.String()`.
"""
    },
    {
        "num": 11,
        "title": "Метод с Pointer Receiver: func (u *User) Birthday() и правила модификации состояния",
        "task": "Метод (Pointer receiver): Поменяй сигнатуру на func (u *User) Birthday(). Вызови метод снова и проверь, что оригинал изменился. Правило: хочешь менять состояние — используй указатель.",
        "theory": """
Закрепление золотого правила: **Любая мутация состояния объекта требует Pointer Receiver**.
""",
        "step_by_step": """
1. Объявляем `type User struct { Name string; Age int }`.
2. Пишем `(u *User) Birthday()`.
3. Проверяем сохранение нового возраста.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type User struct {
	Name string
	Age  int
}

func (u *User) Birthday() {
	if u != nil {
		u.Age++
	}
}

func main() {
	u := User{Name: "Кирилл", Age: 19}
	fmt.Printf("До вызова:    %+v\n", u)

	u.Birthday()

	fmt.Printf("После вызова: %+v (СОСТОЯНИЕ УСПЕШНО ИЗМЕНЕНО!)\n", u)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До вызова:    {Name:Кирилл Age:19}
# После вызова: {Name:Кирилл Age:20} (СОСТОЯНИЕ УСПЕШНО ИЗМЕНЕНО!)"""
            }
        ],
        "under_the_hood": """
Прямая запись по смещению поля `Age` в памяти.
""",
        "pitfalls": """
- Вызов метода на неадресуемом значении `User{...}.Birthday()` (ошибка компиляции `cannot call pointer method on literal`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `User{...}.Birthday()` не компилируется?»
**Ответ:** Потому что литерал структуры `User{...}` является временным rvalue-значением и не имеет адреса в памяти.
"""
    },
    {
        "num": 12,
        "title": "Конфликт имен при множественном встраивании (Ambiguous Selector) и явное разрешение",
        "task": "Создай конфликт имён при встраивании: встрой Address и WorkAddress, обе имеют City. Покажи, что p.City вызывает неоднозначность (ambiguous). Исправь через явное указание p.Address.City.",
        "theory": """
**Коллизии имен при композиции (Ambiguity Resolution):**
- Если две встроенные структуры содержат одинаковое поле (например `City`), компилятор Go **не может выбрать автоматически**;
- Попытка доступа `p.City` приводит к ошибке компиляции `ambiguous selector p.City`;
- **Решение:** Явное обращение через тип `p.HomeAddress.City` или `p.WorkAddress.City`.
""",
        "step_by_step": """
1. Создаем `HomeAddress{City string}` и `WorkAddress{City string}`.
2. Встраиваем обе структуры в `Person`.
3. Показываем ошибку неоднозначности и правильное явное обращение.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type HomeAddress struct {
	City string
}

type WorkAddress struct {
	City string
}

type Employee struct {
	HomeAddress
	WorkAddress
	Name string
}

func main() {
	emp := Employee{
		HomeAddress: HomeAddress{City: "Химки"},
		WorkAddress: WorkAddress{City: "Москва"},
		Name:        "Денис",
	}

	// ❌ ОШИБКА: fmt.Println(emp.City) -> ambiguous selector emp.City

	// ✅ ПРАВИЛЬНО: явное указание встроенной структуры:
	fmt.Printf("Сотрудник:     %s\n", emp.Name)
	fmt.Printf("Домашний город: %s\n", emp.HomeAddress.City)
	fmt.Printf("Рабочий город:  %s\n", emp.WorkAddress.City)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Сотрудник:     Денис
# Домашний город: Химки
# Рабочий город:  Москва"""
            }
        ],
        "under_the_hood": """
Компилятор строит таблицу символов с глубиной вложения. При одинаковой глубине двух совпадающих полей генерируется ошибка неоднозначности.
""",
        "pitfalls": """
- Случайное появление коллизий при добавлении новых полей во встроенные сторонние структуры.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что произойдет, если внешняя структура `Employee` добавит собственное поле `City string`?»
**Ответ:** Поле `Employee.City` имеет глубину 0 и автоматически затенит (Shadow) оба встроенных поля с глубиной 1, устранив ошибку неоднозначности!
"""
    },
    {
        "num": 13,
        "title": "Инициализация структуры Book: именованные поля, позиционные аргументы и анонимная структура",
        "task": "Инициализация структур: Создайте структуру Book с полями Title, Author, Pages и IsElectronic. Создайте экземпляр структуры тремя путями: с именованными полями, позиционными аргументами, а также создайте анонимную структуру прямо внутри функции main.",
        "theory": """
Закрепление всех вариантов создания структурных типов.
""",
        "step_by_step": """
1. Объявляем `type Book struct { Title, Author string; Pages int; IsElectronic bool }`.
2. Создаем `b1` (именованный), `b2` (позиционный), `b3` (анонимная структура).
3. Выводим результаты.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Book struct {
	Title        string
	Author       string
	Pages        int
	IsElectronic bool
}

func main() {
	// 1. Именованные поля:
	b1 := Book{
		Title:        "The Go Programming Language",
		Author:       "Alan Donovan",
		Pages:        380,
		IsElectronic: true,
	}

	// 2. Позиционные аргументы:
	b2 := Book{"Concurrency in Go", "Katherine Cox-Buday", 240, false}

	// 3. Анонимная структура прямо в main:
	b3 := struct {
		Title string
		ISBN  string
	}{
		Title: "Designing Data-Intensive Applications",
		ISBN:  "978-1449373320",
	}

	fmt.Printf("1. Именованная: %+v\n", b1)
	fmt.Printf("2. Позиционная: %+v\n", b2)
	fmt.Printf("3. Анонимная:   %+v\n", b3)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Именованная: {Title:The Go Programming Language Author:Alan Donovan Pages:380 IsElectronic:true}
# 2. Позиционная: {Title:Concurrency in Go Author:Katherine Cox-Buday Pages:240 IsElectronic:false}
# 3. Анонимная:   {Title:Designing Data-Intensive Applications ISBN:978-1449373320}"""
            }
        ],
        "under_the_hood": """
Все поля укладываются в непрерывные структуры в стековом кадре.
""",
        "pitfalls": """
- Пропуск одного поля в позиционной инициализации.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каков размер структуры `Book` в памяти на 64-битной архитектуре?»
**Ответ:** 16 (Title) + 16 (Author) + 8 (Pages) + 1 (IsElectronic) + 7 (Padding) = 48 байт.
"""
    },
    {
        "num": 14,
        "title": "Методы для пользовательских типов на базе примитивов: type MyFloat float64 и метод IsPositive()",
        "task": "Методы для примитивов: Создай свой тип type MyFloat float64. Напиши для него метод IsPositive() bool.",
        "theory": """
**Методы на неструктурных типах (Methods on Any Defined Type):**
- В Go методы можно определять на **любых типах**, объявленных в текущем пакете (кроме указателей и интерфейсов);
- Позволяет расширять числа, строки и срезы богатым доменным поведением.
""",
        "step_by_step": """
1. Объявляем `type MyFloat float64`.
2. Пишем `func (f MyFloat) IsPositive() bool`.
3. Тестируем на положительных и отрицательных значениях.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type MyFloat float64

func (f MyFloat) IsPositive() bool {
	return f > 0
}

func (f MyFloat) Abs() MyFloat {
	if f < 0 {
		return -f
	}
	return f
}

func main() {
	var val1 MyFloat = 3.14
	var val2 MyFloat = -10.5

	fmt.Printf("val1 (%.2f): IsPositive = %t\n", val1, val1.IsPositive())
	fmt.Printf("val2 (%.2f): IsPositive = %t | Abs = %.2f\n", val2, val2.IsPositive(), val2.Abs())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# val1 (3.14): IsPositive = true
# val2 (-10.50): IsPositive = false | Abs = 10.50"""
            }
        ],
        "under_the_hood": """
Метод компилируется в обычную функцию `MyFloat.IsPositive(f float64) bool`.
""",
        "pitfalls": """
- Попытка объявить метод для базового типа `func (f float64) IsPositive()` (ошибка компиляции `cannot define new methods on non-local type float64`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли добавить метод к типу `time.Duration` в своем пакете?»
**Ответ:** Напрямую к `time.Duration` нельзя (он определен в пакете `time`), но можно создать свой тип `type MyDuration time.Duration` и добавить метод к нему.
"""
    },
    {
        "num": 15,
        "title": "Паттерн Fluent Interface / Method Chaining с возвратом указателя *Person",
        "task": "Реализуй паттерн Method chaining (fluent interface): person.SetName(\"John\").SetAge(30).String(). Каждый метод возвращает *Person.",
        "theory": """
**Method Chaining (Fluent Builder):**
- Каждый метод-мутатор возвращает указатель на самого себя `return p`;
- Позволяет выстраивать лаконичные цепочки конфигурирования объектов в одну строку.
""",
        "step_by_step": """
1. Создаем структуру `Person{name string, age int}`.
2. Пишем методы `SetName(name string) *Person` и `SetAge(age int) *Person`.
3. Пишем метод `String() string`.
4. Вызываем цепочку методов.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Person struct {
	name string
	age  int
}

func (p *Person) SetName(name string) *Person {
	p.name = name
	return p // Возвращаем указатель для поддержки цепочки
}

func (p *Person) SetAge(age int) *Person {
	p.age = age
	return p // Возвращаем указатель для поддержки цепочки
}

func (p *Person) String() string {
	return fmt.Sprintf("Профиль: %s (%d лет)", p.name, p.age)
}

func main() {
	p := new(Person)

	// Цепочка вызовов (Fluent Interface):
	info := p.SetName("John").SetAge(30).String()

	fmt.Println(info)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Профиль: John (30 лет)"""
            }
        ],
        "under_the_hood": """
Регистр `RAX` с адресом объекта передается из одного вызова метода в следующий.
""",
        "pitfalls": """
- Вызов цепочки на `nil`-указателе без проверки.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В каких популярных Go-библиотеках применяется Fluent Interface?»
**Ответ:** В ORM `GORM` (`db.Where(...).Order(...).Find(...)`), HTTP-клиенте `resty` и логгерах `zerolog`/`zap`.
"""
    },
    {
        "num": 16,
        "title": "Сортировка среза структур []Book по числовому полю через slices.SortFunc",
        "task": "Объявите структуру Book с полями Title, Author, Year. Создайте слайс книг и отсортируйте по году с помощью sort.Slice.",
        "theory": """
Сортировка коллекций структур с использованием современных дженериков `cmp.Compare` и `slices.SortFunc` (Go 1.21+).
""",
        "step_by_step": """
1. Создаем структуру `Book{Title, Author string, Year int}`.
2. Создаем срез `[]Book`.
3. Сортируем с помощью `slices.SortFunc`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"cmp"
	"fmt"
	"slices"
)

type Book struct {
	Title  string
	Author string
	Year   int
}

func main() {
	books := []Book{
		{"The Go Programming Language", "Donovan", 2015},
		{"Clean Code", "Robert Martin", 2008},
		{"Designing Data-Intensive Applications", "Kleppmann", 2017},
	}

	// Современная сортировка Go 1.21+ без рефлексии:
	slices.SortFunc(books, func(a, b Book) int {
		return cmp.Compare(a.Year, b.Year)
	})

	fmt.Println("Книги, отсортированные по году издания:")
	for _, b := range books {
		fmt.Printf("  [%d] %-38s (%s)\n", b.Year, b.Title, b.Author)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Книги, отсортированные по году издания:
#   [2008] Clean Code                             (Robert Martin)
#   [2015] The Go Programming Language            (Donovan)
#   [2017] Designing Data-Intensive Applications  (Kleppmann)"""
            }
        ],
        "under_the_hood": """
`slices.SortFunc` использует быстрый алгоритм Pattern-defeating Quicksort (pdqsort).
""",
        "pitfalls": """
- Использование устаревшего `sort.Slice` с рефлексией в высоконагруженном коде.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `slices.SortFunc` быстрее `sort.Slice`?»
**Ответ:** Потому что `slices.SortFunc` типизирован дженериками и инлайнится компилятором без оверхеда на рефлексию `reflect.Swapper`.
"""
    },
    {
        "num": 17,
        "title": "Локальные анонимные структуры struct{ X, Y int } для временных вычислений",
        "task": "Создай анонимную структуру: p := struct{ X, Y int }{10, 20}. Используй для временной структуры данных внутри функции без объявления типа.",
        "theory": """
Изоляция одноразовых составных данных внутри тела функции.
""",
        "step_by_step": """
1. Создаем точку `p := struct{ X, Y int }{10, 20}`.
2. Вычисляем сумму координат.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	point := struct {
		X, Y int
	}{
		X: 10,
		Y: 20,
	}

	sum := point.X + point.Y
	fmt.Printf("Точка: %+v, Сумма координат: %d\n", point, sum)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Точка: {X:10 Y:20}, Сумма координат: 30"""
            }
        ],
        "under_the_hood": """
16 байт в локальном стековом фрейме.
""",
        "pitfalls": """
- Попытка использовать тип анонимной структуры как тип возврата из экспортированной функции.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Где анонимные структуры являются стандартом индустрии?»
**Ответ:** В табличных юнит-тестах: `tt := []struct{ name string; in int; want int }{...}`.
"""
    },
    {
        "num": 18,
        "title": "Композиция: структура Employee со встроенной структурой Address без имени поля",
        "task": "Композиция (Встраивание): Создай структуру Address (City, Street). Создай Employee, внутри которого встрой структуру Address без имени поля (просто напиши Address).",
        "theory": """
Базовое объявление композиции через безымянные поля.
""",
        "step_by_step": """
1. Объявляем `Address{City, Street string}`.
2. Объявляем `Employee{Address; Position string}`.
3. Инициализируем и выводим.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Address struct {
	City   string
	Street string
}

type Employee struct {
	Address  // Анонимное встраивание
	Position string
}

func main() {
	emp := Employee{
		Address:  Address{City: "Казань", Street: "Баумана"},
		Position: "Senior Go Developer",
	}

	fmt.Printf("Должность: %s | Город: %s\n", emp.Position, emp.City)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Должность: Senior Go Developer | Город: Казань"""
            }
        ],
        "under_the_hood": """
Смещение поля `City` совпадает со смещением `Address` (0 байт).
""",
        "pitfalls": """
- Дублирование имен встроенных структур одного типа.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какое имя имеет анонимное поле внутри структуры?»
**Ответ:** Имя совпадает с именем типа: `emp.Address`.
"""
    },
    {
        "num": 19,
        "title": "Фабричная функция-конструктор NewBook(...) с возвратом указателя *Book",
        "task": "Напишите функцию-конструктор NewBook(...), которая инициализирует поля и возвращает указатель на новую структуру Book.",
        "theory": """
Паттерн фабричного конструктора `NewT(...) *T` в Go.
""",
        "step_by_step": """
1. Пишем `NewBook(title, author string, year int) *Book`.
2. Возвращаем `&Book{...}`.
3. Проверяем в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Book struct {
	Title  string
	Author string
	Year   int
}

func NewBook(title, author string, year int) *Book {
	return &Book{
		Title:  title,
		Author: author,
		Year:   year,
	}
}

func main() {
	book := NewBook("1984", "George Orwell", 1949)
	fmt.Printf("Создана книга: %+v (тип: %T)\n", *book, book)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Создана книга: {Title:1984 Author:George Orwell Year:1949} (тип: *main.Book)"""
            }
        ],
        "under_the_hood": """
Escape-анализ компилятора перемещает созданную структуру в кучу.
""",
        "pitfalls": """
- Игнорирование валидации входных аргументов в конструкторе.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Когда конструктор должен возвращать `(*T, error)`, а когда просто `*T`?»
**Ответ:** Если создание объекта может завершиться ошибкой валидации или подключения к ресурсу — возвращают `(*T, error)`. Если создание гарантированно валидно — просто `*T`.
"""
    },
    {
        "num": 20,
        "title": "Сравнение структур через ==: правила Comparable и запрет срезов/мап в полях",
        "task": "Сравни две структуры через ==. Покажи, что структуры comparable, если все поля comparable. Добавь поле-слайс — получи ошибку компиляции при сравнении.",
        "theory": """
**Правила сравнимости структур (Struct Comparability):**
- Структура является **сравнимой (Comparable)** тогда и только тогда, когда **каждое из её полей сравнимо**;
- Сравнимые типы: примитивы (`int`, `string`, `bool`), массивы `[3]int`, указатели, каналы;
- Несравнимые типы: срезы `[]T`, мапы `map[K]V`, функции `func()`;
- Наличие поля-среза делает всю структуру несравнимой через оператор `==`.
""",
        "step_by_step": """
1. Создаем сравнимую структуру `Point{X, Y int}`.
2. Сравниваем `p1 == p2`.
3. Создаем структуру со срезом `DataHolder{Tags []string}` и показываем, почему `==` запрещен.
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

type NonComparable struct {
	ID   int
	Tags []string // Срез делает структуру несравнимой через ==
}

func main() {
	p1 := Point{X: 10, Y: 20}
	p2 := Point{X: 10, Y: 20}
	p3 := Point{X: 5, Y: 20}

	fmt.Printf("p1 == p2: %t (поля идентичны)\n", p1 == p2)
	fmt.Printf("p1 == p3: %t (поля различаются)\n", p1 == p3)

	nc1 := NonComparable{ID: 1, Tags: []string{"go"}}
	nc2 := NonComparable{ID: 1, Tags: []string{"go"}}
	_ = nc1
	_ = nc2
	// ❌ ОШИБКА КОМПИЛЯЦИИ: fmt.Println(nc1 == nc2)
	// invalid operation: nc1 == nc2 (struct containing []string cannot be compared)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# p1 == p2: true (поля идентичны)
# p1 == p3: false (поля различаются)"""
            }
        ],
        "under_the_hood": """
Для сравнимых структур компилятор генерирует побайтовое сравнение полей через `CMPQ` или `memcmp`.
""",
        "pitfalls": """
- Использование структуры с полем-срезом в качестве ключа мапы `map[NonComparable]int` (ошибка компиляции).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как сравнить две структуры, содержащие срезы или мапы?»
**Ответ:** Использовать `reflect.DeepEqual(s1, s2)` или библиотеку `github.com/google/go-cmp/cmp`.
"""
    },
    {
        "num": 21,
        "title": "Инициализация структуры по именам полей User{ID: 1, Name: 'Alice'}",
        "task": "Инициализируй структуру по именам полей User{ID: 1, Name: \"Alice\"}.",
        "theory": """
Базовое упражнение на именованный литерал.
""",
        "step_by_step": """
1. Объявляем структуру `User{ID int, Name string}`.
2. Создаем экземпляр.
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

func main() {
	u := User{ID: 1, Name: "Alice"}
	fmt.Printf("User: ID=%d, Name=%s\n", u.ID, u.Name)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# User: ID=1, Name=Alice"""
            }
        ],
        "under_the_hood": """
Запись полей в стек.
""",
        "pitfalls": """
- Опечатки в именах полей.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Обязательно ли указывать все поля при именованной инициализации?»
**Ответ:** Нет, пропущенные поля автоматически инициализируются нулевыми значениями (Zero Values).
"""
    },
    {
        "num": 22,
        "title": "Вложенные структуры (Nested Structs) и вложенная литеральная инициализация",
        "task": "Вложенные структуры: Создайте структуру Address (город, улица) и структуру Company (название, адрес). Инициализируйте компанию вместе с её адресом в одном литерале.",
        "theory": """
**Вложенные именованные структуры:**
- Поле `Addr Address` имеет явное имя (не анонимное встраивание);
- Доступ осуществляется строго через имя поля `comp.Addr.City`.
""",
        "step_by_step": """
1. Объявляем `type Address struct { City, Street string }`.
2. Объявляем `type Company struct { Name string; Addr Address }`.
3. Инициализируем вложенным литералом.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Address struct {
	City   string
	Street string
}

type Company struct {
	Name string
	Addr Address // Вложенное именованное поле
}

func main() {
	comp := Company{
		Name: "Яндекс",
		Addr: Address{
			City:   "Москва",
			Street: "Льва Толстого",
		},
	}

	fmt.Printf("Компания: %s | Город: %s, Улица: %s\n",
		comp.Name, comp.Addr.City, comp.Addr.Street)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Компания: Яндекс | Город: Москва, Улица: Льва Толстого"""
            }
        ],
        "under_the_hood": """
Память структуры `Address` встраивается непосредственно в тело структуры `Company`.
""",
        "pitfalls": """
- Попытка вызвать `comp.City` (ошибка компиляции `comp.City undefined`, так как поле `Addr` именованное).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем отличие именованного вложенного поля `Addr Address` от встраивания `Address`?»
**Ответ:** Именованное поле не продвигает поля и методы на верхний уровень, требуя явного обращения `comp.Addr.City`, что предотвращает коллизии имен.
"""
    },
    {
        "num": 23,
        "title": "Продвинутые поля (Promoted Fields): доступ emp.City вместо emp.Address.City",
        "task": "Promoted fields (Продвинутые поля): Доступ к встроенным полям. Попробуй обратиться к городу работника напрямую: emp.City, вместо emp.Address.City. Это магия композиции в Go.",
        "theory": """
Закрепление прямого доступа к полям встроенной структуры.
""",
        "step_by_step": """
1. Создаем структуру с анонимным `Address`.
2. Читаем и меняем `emp.City`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Address struct {
	City string
}

type Employee struct {
	Address
	Name string
}

func main() {
	emp := Employee{
		Address: Address{City: "Новосибирск"},
		Name:    "Роман",
	}

	// Прямой доступ к всплывшему полю:
	fmt.Printf("Сотрудник: %s, Город: %s\n", emp.Name, emp.City)

	// Прямая мутация всплывшего поля:
	emp.City = "Иннополис"
	fmt.Printf("После переезда: Город: %s\n", emp.City)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Сотрудник: Роман, Город: Новосибирск
# После переезда: Город: Иннополис"""
            }
        ],
        "under_the_hood": """
Прямая запись по смещению 0 байт.
""",
        "pitfalls": """
- Конфликт при совпадении имен.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли использовать `emp.Address.City` при наличии всплытия?»
**Ответ:** Да, полная форма записи всегда доступна.
"""
    },
    {
        "num": 24,
        "title": "Вложенные структуры и явное обращение к вложенным полям emp.Address.City",
        "task": "Вложенные структуры: Address внутри Employee. Выведите вложенное поле напрямую (emp.Address.City).",
        "theory": """
Явное обращение через квалифицированное имя.
""",
        "step_by_step": """
1. Инициализируем структуру.
2. Выводим поле через полную цепочку `emp.Address.City`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Address struct {
	City   string
	Street string
}

type Employee struct {
	Address
	Salary int
}

func main() {
	emp := Employee{
		Address: Address{City: "Екатеринбург", Street: "Ленина"},
		Salary:  200000,
	}

	fmt.Printf("Явный доступ: Город=%s, Улица=%s, Зарплата=%d\n",
		emp.Address.City, emp.Address.Street, emp.Salary)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Явный доступ: Город=Екатеринбург, Улица=Ленина, Зарплата=200000"""
            }
        ],
        "under_the_hood": """
Компилятор использует одинаковое смещение.
""",
        "pitfalls": """
- Опечатка в пути селектора.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Различаются ли ассемблерные инструкции для `emp.City` и `emp.Address.City`?»
**Ответ:** НЕТ, генерируется абсолютно одинаковый бинарный код.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 1: {len(exercises)} exercises.")
