# Chapter 13 Part 3: Exercises 49 to 71

exercises = [
    {
        "num": 49,
        "title": "Структура с полем-функцией (Callback) и условный запуск обработчика",
        "task": "Создай структуру с полем-функцией (callback). Напиши метод, который вызывает callback при определённом условии.",
        "theory": """
**Паттерн обратного вызова (Callback Pattern) в структурах:**
- Поле структуры может иметь функциональный тип `OnClick func(string)`;
- Позволяет динамически настраивать реакцию объекта на события в рантайме (паттерн Observer / Event Listener).
""",
        "step_by_step": """
1. Создаем `type Button struct { Label string; OnClick func(label string) }`.
2. Пишем метод `(b *Button) Click()`.
3. Назначаем обработчик и вызываем `Click()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Button struct {
	Label   string
	OnClick func(label string) // Поле-коллбэк
}

func (b *Button) Click() {
	if b.OnClick != nil {
		b.OnClick(b.Label)
	} else {
		fmt.Printf("Кнопка %q нажата, но обработчик не назначен\n", b.Label)
	}
}

func main() {
	submitBtn := &Button{
		Label: "Оплатить заказ",
		OnClick: func(name string) {
			fmt.Printf("⚡ СОБЫТИЕ: Инициирована транзакция для кнопки %q\n", name)
		},
	}

	submitBtn.Click()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# ⚡ СОБЫТИЕ: Инициирована транзакция для кнопки "Оплатить заказ" """
            }
        ],
        "under_the_hood": """
Поле `OnClick` хранит 8-байтный указатель на замыкание.
""",
        "pitfalls": """
- Вызов `b.OnClick()` без предварительной проверки `if b.OnClick != nil` (вызовет панику `nil pointer dereference`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем отличие поля-функции `struct { Handler func() }` от метода структуры `func (s *Struct) Handler()`?»
**Ответ:** Поле-функцию можно динамически подменять в рантайме для каждого конкретного экземпляра, а методы типа статичны и едины для всех экземпляров.
"""
    },
    {
        "num": 50,
        "title": "Сравнение структур User через == и ошибка компиляции при добавлении среза",
        "task": "Сравнение структур: Создай две разные переменные структуры User с одинаковыми данными. Сравни их через ==. Затем добавь в структуру срез []string и посмотри на ошибку компиляции (структуры со ссылочными типами нельзя сравнивать через ==).",
        "theory": """
Повторение и закрепление правил сравнимости структур.
""",
        "step_by_step": """
1. Объявляем структуру `SimpleUser{ID int, Email string}`.
2. Сравниваем два экземпляра через `==`.
3. Анализируем ограничение ссылочных полей.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type SimpleUser struct {
	ID    int
	Email string
}

func main() {
	u1 := SimpleUser{ID: 10, Email: "user@ya.ru"}
	u2 := SimpleUser{ID: 10, Email: "user@ya.ru"}
	u3 := SimpleUser{ID: 20, Email: "admin@ya.ru"}

	fmt.Printf("u1 == u2: %t (все поля равны)\n", u1 == u2)
	fmt.Printf("u1 == u3: %t (ID различаются)\n", u1 == u3)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# u1 == u2: true (все поля равны)
# u1 == u3: false (ID различаются)"""
            }
        ],
        "under_the_hood": """
Побайтовое сравнение полей структуры на стеке.
""",
        "pitfalls": """
- Попытка использовать `==` на структурах с мапами или срезами.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли использовать `SimpleUser` как ключ в `map[SimpleUser]bool`?»
**Ответ:** ДА, поскольку все поля `SimpleUser` сравнимы.
"""
    },
    {
        "num": 51,
        "title": "Строгая десериализация JSON через json.NewDecoder с запретом неизвестных полей (DisallowUnknownFields)",
        "task": "Десериализуйте JSON-строку обратно в структуру (json.Unmarshal), обработав случай, когда JSON содержит лишние поля.",
        "theory": """
**Строгая валидация входящего JSON в API:**
- По умолчанию `json.Unmarshal` просто игнорирует неизвестные поля;
- Для предотвращения ошибок опечаток в DTO используют `decoder.DisallowUnknownFields()`, который возвращает ошибку при наличии лишних ключей.
""",
        "step_by_step": """
1. Создаем структуру `type CreateUserRequest struct { Username, Email string }`.
2. Создаем `json.NewDecoder(strings.NewReader(payload))`.
3. Включаем `dec.DisallowUnknownFields()`.
4. Демонстрируем перехват лишнего поля.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

type CreateUserRequest struct {
	Username string `json:"username"`
	Email    string `json:"email"`
}

func ParseStrictJSON(raw string) (*CreateUserRequest, error) {
	dec := json.NewDecoder(strings.NewReader(raw))
	dec.DisallowUnknownFields() // Запрещаем любые лишние поля!

	var req CreateUserRequest
	if err := dec.Decode(&req); err != nil {
		return nil, err
	}
	return &req, nil
}

func main() {
	validJSON := `{"username":"alex","email":"alex@mail.ru"}`
	invalidJSON := `{"username":"alex","email":"alex@mail.ru","extra_field":"hack"}`

	_, err1 := ParseStrictJSON(validJSON)
	fmt.Printf("1. Валидный JSON:  ошибка = %v\n", err1)

	_, err2 := ParseStrictJSON(invalidJSON)
	fmt.Printf("2. Лишнее поле:   ошибка = %v (ОТКЛОНЕНО!)\n", err2)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Валидный JSON:  ошибка = <nil>
# 2. Лишнее поле:   ошибка = json: unknown field "extra_field" (ОТКЛОНЕНО!)"""
            }
        ],
        "under_the_hood": """
Потоковый декодер сопоставляет токены JSON с набором тегов структуры и возвращает синтаксическую ошибку.
""",
        "pitfalls": """
- Использование стандартного `json.Unmarshal`, пропускающего опечатки в полях DTO.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Зачем включать `DisallowUnknownFields` в микросервисах?»
**Ответ:** Для строгой защиты контрактов API: это мгновенно выявляет опечатки на стороне фронтенда или устаревшие клиенты API.
"""
    },
    {
        "num": 52,
        "title": "Глубокое копирование (Deep Copy) структуры со срезами и указателями vs поверхностное копирование (Shallow)",
        "task": "Напиши функцию ClonePerson(p Person) Person, которая делает deep copy (для простых типов) vs shallow copy (для указателей). Объясни разницу на примере.",
        "theory": """
**Deep Copy vs Shallow Copy:**
- **Shallow Copy (`p2 := p1`):** копирует адреса указателей и дескрипторы срезов. Изменения во вложенных данных отражаются на обеих структурах;
- **Deep Copy:** выделяет новую память для каждого указателя и среза, создавая полностью независимый клон.
""",
        "step_by_step": """
1. Создаем `type Person struct { Name string; Skills []string; Extra *int }`.
2. Пишем метод `(p Person) Clone() Person`.
3. Показываем независимость клона.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"slices"
)

type Person struct {
	Name   string
	Skills []string
	Score  *int
}

func (p Person) DeepClone() Person {
	// 1. Клонируем срез:
	newSkills := slices.Clone(p.Skills)

	// 2. Клонируем значение по указателю:
	var newScore *int
	if p.Score != nil {
		val := *p.Score
		newScore = &val
	}

	return Person{
		Name:   p.Name,
		Skills: newSkills,
		Score:  newScore,
	}
}

func main() {
	initialScore := 100
	p1 := Person{
		Name:   "Иван",
		Skills: []string{"Go", "Docker"},
		Score:  &initialScore,
	}

	p2 := p1.DeepClone()
	p2.Skills[0] = "Python"
	*p2.Score = 500

	fmt.Printf("1. Оригинал p1: Skills=%v | Score=%d\n", p1.Skills, *p1.Score)
	fmt.Printf("2. Клон p2:     Skills=%v | Score=%d (ПОЛНАЯ ИЗОЛЯЦИЯ!)\n", p2.Skills, *p2.Score)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Оригинал p1: Skills=[Go Docker] | Score=100
# 2. Клон p2:     Skills=[Python Docker] | Score=500 (ПОЛНАЯ ИЗОЛЯЦИЯ!)"""
            }
        ],
        "under_the_hood": """
`DeepClone` выделяет новые блоки памяти в куче для среза и числа.
""",
        "pitfalls": """
- Забыть клонировать вложенные мапы или структуры второго уровня вложенности.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как `slices.Clone` (Go 1.21+) упрощает создание глубоких копий?»
**Ответ:** Функция `slices.Clone(s)` делает предвыделение нового массива нужного размера и копирует туда элементы за один быстрый вызов `copy()`.
"""
    },
    {
        "num": 53,
        "title": "Структура с полем типа any (interface{}) и Type Assertion в методах",
        "task": "Создай структуру с полем типа interface{}. Присвой разные значения. Используй type assertion в методе для работы с конкретным типом.",
        "theory": """
Хранение динамических полезных нагрузок (Payload) в структурах.
""",
        "step_by_step": """
1. Создаем `type Container struct { Data any }`.
2. Пишем метод `(c Container) AsString() (string, bool)`.
3. Тестируем Type Assertion.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Container struct {
	Data any
}

func (c Container) PrintDetails() {
	switch v := c.Data.(type) {
	case string:
		fmt.Printf("Строка длиной %d: %q\n", len(v), v)
	case int:
		fmt.Printf("Числовое значение: %d (удвоенное: %d)\n", v, v*2)
	default:
		fmt.Printf("Неизвестный тип данных: %T -> %v\n", v, v)
	}
}

func main() {
	c1 := Container{Data: "Привет, Go!"}
	c2 := Container{Data: 42}
	c3 := Container{Data: true}

	c1.PrintDetails()
	c2.PrintDetails()
	c3.PrintDetails()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Строка длиной 19: "Привет, Go!"
# Числовое значение: 42 (удвоенное: 84)
# Неизвестный тип данных: bool -> true"""
            }
        ],
        "under_the_hood": """
Type Switch над `eface._type` компилируется в эффективную таблицу переходов.
""",
        "pitfalls": """
- Прямое утверждение типа `c.Data.(string)` без проверки `comma-ok` (вызовет панику при несовпадении типов).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Когда вместо `any` в структуре лучше использовать дженерики `type Container[T any] struct { Data T }`?»
**Ответ:** Практически всегда! Дженерики обеспечивают статическую безопасность типов на этапе компиляции и исключают накладные расходы на упаковку в `eface` и type assertion.
"""
    },
    {
        "num": 54,
        "title": "Сравнение структур: равенство сравнимых полей и невозможность сравнения срезов",
        "task": "Сравнение структур: покажите, что две структуры равны, если все поля сравнимы. Что будет, если поле — слайс?",
        "theory": """
Сравнимость структур в условиях композитных данных.
""",
        "step_by_step": """
1. Создаем структуру `Credential{Login, PassHash string}`.
2. Сравниваем `c1 == c2`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Credential struct {
	Login    string
	PassHash string
}

func main() {
	c1 := Credential{Login: "admin", PassHash: "hash_abc"}
	c2 := Credential{Login: "admin", PassHash: "hash_abc"}

	fmt.Printf("c1 == c2: %t\n", c1 == c2)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# c1 == c2: true"""
            }
        ],
        "under_the_hood": """
Поэлементное сравнение строк через `runtime.memequal`.
""",
        "pitfalls": """
- Сравнение через `==` структур с полем `time.Time` (лучше использовать `t1.Equal(t2)` из-за часовых поясов!).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `time.Time` нельзя сравнивать через `==`?»
**Ответ:** Потому что `time.Time` содержит указатель на локацию `loc *Location` и монотонный счетчик, из-за чего два момента одного и того же времени могут быть не равны по `==`. Нужно использовать `t1.Equal(t2)`.
"""
    },
    {
        "num": 55,
        "title": "Инкапсуляция: геттеры и сеттеры с валидацией Age() int и SetAge(int) error",
        "task": "Инкапсуляция (Геттеры и Сеттеры): Помести User в отдельный пакет. Сделай поле age с маленькой буквы (приватным). Напиши публичные методы Age() int (геттер) и SetAge(int) error (сеттер с валидацией).",
        "theory": """
Защита инвариантов бизнес-логики через методы доступа.
""",
        "step_by_step": """
1. Создаем структуру с приватным `age int`.
2. Пишем методы `Age()` и `SetAge(newAge int) error`.
3. Тестируем валидацию.
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

type Employee struct {
	Name string
	age  int // Приватное поле
}

func (e *Employee) Age() int {
	return e.age
}

func (e *Employee) SetAge(newAge int) error {
	if newAge < 18 || newAge > 75 {
		return fmt.Errorf("недопустимый возраст сотрудника: %d (допустимо 18-75)", newAge)
	}
	e.age = newAge
	return nil
}

func main() {
	emp := &Employee{Name: "Станислав"}

	if err := emp.SetAge(16); err != nil {
		fmt.Println("Ошибка:", err)
	}

	if err := emp.SetAge(32); err != nil {
		fmt.Println("Ошибка:", err)
	}

	fmt.Printf("Сотрудник: %s, Возраст: %d\n", emp.Name, emp.Age())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Ошибка: недопустимый возраст сотрудника: 16 (допустимо 18-75)
# Сотрудник: Станислав, Возраст: 32"""
            }
        ],
        "under_the_hood": """
Проверка границ в условии `CMPL`.
""",
        "pitfalls": """
- Игнорирование возвращаемой ошибки сеттера `_ = emp.SetAge(...)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каковы преимущества возврата ошибки из сеттера `SetAge(...) error`?»
**Ответ:** Это делает обработку невалидных данных явной и позволяет вернуть клиенту осмысленный HTTP-статус 400 Bad Request.
"""
    },
    {
        "num": 56,
        "title": "Каверзный кейс: передача структуры по значению (без мутаций) vs по указателю",
        "task": "[Каверзный кейс]: Напиши функцию, которая принимает структуру по значению и пытается изменить её поле. Убедись, что оригинал не изменился. Напиши другую функцию, принимающую указатель.",
        "theory": """
Закрепление различия между передачей структуры по значению и по указателю.
""",
        "step_by_step": """
1. Пишем `ResetTitleVal(b Book)`.
2. Пишем `ResetTitlePtr(b *Book)`.
3. Сравниваем результаты.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Book struct {
	Title string
}

func ResetTitleVal(b Book) {
	b.Title = "Очищено"
}

func ResetTitlePtr(b *Book) {
	if b != nil {
		b.Title = "Очищено"
	}
}

func main() {
	b1 := Book{Title: "Алгоритмы"}
	b2 := Book{Title: "Архитектура"}

	ResetTitleVal(b1)
	fmt.Printf("1. После ResetTitleVal: %s (НЕ ИЗМЕНИЛСЯ!)\n", b1.Title)

	ResetTitlePtr(&b2)
	fmt.Printf("2. После ResetTitlePtr: %s (УСПЕШНО ИЗМЕНЕН!)\n", b2.Title)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. После ResetTitleVal: Алгоритмы (НЕ ИЗМЕНИЛСЯ!)
# 2. После ResetTitlePtr: Очищено (УСПЕШНО ИЗМЕНЕН!)"""
            }
        ],
        "under_the_hood": """
Копирование заголовка строки в стек.
""",
        "pitfalls": """
- Забыть знак `&` при вызове `ResetTitlePtr`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go нет синтаксиса `void Foo(const Struct &s)` как в C++?»
**Ответ:** Потому что структуры до 64 байт дешево передавать по значению (иммутабельно), а для больших структур передают `*Struct` с конвенцией не мутировать поля.
"""
    },
    {
        "num": 57,
        "title": "Паттерн Constructor: фабричная функция NewUser(name, age) (*User, error) с валидацией",
        "task": "Паттерн Constructor: В Go нет конструкторов. Напиши функцию NewUser(name string, age int) (*User, error), которая проверяет, что возраст > 0, и возвращает указатель на структуру или ошибку.",
        "theory": """
Эталонный конструктор доменной модели в Go.
""",
        "step_by_step": """
1. Создаем структуру `User{Name string, Age int}`.
2. Пишем конструктор `NewUser(name string, age int) (*User, error)`.
3. Тестируем успешное создание и валидацию.
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

type User struct {
	Name string
	Age  int
}

func NewUser(name string, age int) (*User, error) {
	if name == "" {
		return nil, errors.New("имя пользователя не может быть пустым")
	}
	if age <= 0 {
		return nil, errors.New("возраст должен быть строго больше 0")
	}

	return &User{Name: name, Age: age}, nil
}

func main() {
	u, err := NewUser("Василий", 24)
	if err != nil {
		panic(err)
	}
	fmt.Printf("Создан пользователь: %+v\n", *u)

	_, errInvalid := NewUser("", -5)
	fmt.Printf("Невалидные данные: ошибка = %v\n", errInvalid)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Создан пользователь: {Name:Василий Age:24}
# Невалидные данные: ошибка = имя пользователя не может быть пустым"""
            }
        ],
        "under_the_hood": """
При ошибке возвращается `(nil, error)` без аллокации структуры.
""",
        "pitfalls": """
- Игнорирование проверки ошибки конструктора.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go не предусмотрены встроенные конструкторы в стиле `User.init()`?»
**Ответ:** Функции `NewUser(...)` более гибкие: они могут возвращать ошибку `error`, интерфейс вместо конкретной структуры и иметь разные имена (`NewUser`, `NewAdminUser`, `NewUserFromJSON`).
"""
    },
    {
        "num": 58,
        "title": "Геометрическая структура Vector2D и иммутабельные методы Add, Subtract, Scale",
        "task": "Реализуйте структуру Vector2D (X, Y float64) с методами Add, Subtract и Scale, возвращающими новые векторы.",
        "theory": """
**Иммутабельные математические структуры (Value Objects):**
- Структура `Vector2D` занимает всего 16 байт;
- Все операции возвращают **новые экземпляры векторов** без изменения исходных;
- Чистый функциональный подход с нулевым риском побочных эффектов.
""",
        "step_by_step": """
1. Объявляем `type Vector2D struct { X, Y float64 }`.
2. Пишем методы `Add`, `Subtract`, `Scale`.
3. Демонстрируем вычисления.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Vector2D struct {
	X, Y float64
}

func (v Vector2D) Add(other Vector2D) Vector2D {
	return Vector2D{X: v.X + other.X, Y: v.Y + other.Y}
}

func (v Vector2D) Subtract(other Vector2D) Vector2D {
	return Vector2D{X: v.X - other.X, Y: v.Y - other.Y}
}

func (v Vector2D) Scale(factor float64) Vector2D {
	return Vector2D{X: v.X * factor, Y: v.Y * factor}
}

func main() {
	v1 := Vector2D{X: 1.0, Y: 2.0}
	v2 := Vector2D{X: 3.0, Y: 4.0}

	sum := v1.Add(v2)
	scaled := sum.Scale(2.0)

	fmt.Printf("v1:     %+v\n", v1)
	fmt.Printf("v2:     %+v\n", v2)
	fmt.Printf("Сумма:  %+v\n", sum)
	fmt.Printf("Scale:  %+v\n", scaled)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# v1:     {X:1 Y:2}
# v2:     {X:3 Y:4}
# Сумма:  {X:4 Y:6}
# Scale:  {X:8 Y:12}"""
            }
        ],
        "under_the_hood": """
Все аргументы и возвращаемые значения передаются в регистрах FPU/SSE (`XMM0`, `XMM1`).
""",
        "pitfalls": """
- Передача `Vector2D` по указателю (создает лишние аллокации в куче).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему для структур размером $\le 16$ байт с плавающей точкой Value Receiver быстрее Pointer Receiver?»
**Ответ:** Потому что компилятор Go передает 16 байт напрямую в двух регистрах процессора без обращений к оперативной памяти и без escape-анализа.
"""
    },
    {
        "num": 59,
        "title": "Пустая структура struct{}: размер 0 байт, массив [1000]struct{} и применение в Set/Chan",
        "task": "Пустая структура struct{}: Создайте переменную empty struct{}. Выведите её размер в байтах с помощью unsafe.Sizeof. Создайте массив из 1000 таких структур [1000]struct{} и проверьте его размер. Где это может быть полезно?",
        "theory": """
**Анатомия пустой структуры `struct{}` (Zero-Size Type):**
- Занимает **ровно 0 байт памяти** (`unsafe.Sizeof(struct{}{}) == 0`);
- Массив любого размера `[1000000]struct{}` занимает **0 байт**;
- **Где применяется:**
  1. Реализация множеств: `map[string]struct{}` (вместо `map[string]bool` для 100% экономии памяти на значениях);
  2. Сигнальные каналы событий: `chan struct{}` (не передает данных, только факт события);
  3. Маркерные интерфейсы и структуры без состояния.
""",
        "step_by_step": """
1. Создаем `empty := struct{}{}`.
2. Создаем массив `var arr [1000]struct{}`.
3. Проверяем размеры через `unsafe.Sizeof`.
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

func main() {
	var empty struct{}
	var arr [1000]struct{}

	fmt.Println("=== ПУСТАЯ СТРУКТУРА struct{} ===")
	fmt.Printf("1. Размер struct{}:           %d байт\n", unsafe.Sizeof(empty))
	fmt.Printf("2. Размер массива [1000]struct{}: %d байт\n", unsafe.Sizeof(arr))

	// Использование в Set:
	set := make(map[string]struct{})
	set["admin"] = struct{}{}
	set["editor"] = struct{}{}

	_, hasAdmin := set["admin"]
	fmt.Printf("3. Множество Set: содержит 'admin' = %t\n", hasAdmin)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# === ПУСТАЯ СТРУКТУРА struct{} ===
# 1. Размер struct{}:           0 байт
# 2. Размер массива [1000]struct{}: 0 байт
# 3. Множество Set: содержит 'admin' = true"""
            }
        ],
        "under_the_hood": """
Все указатели на `struct{}` в куче ссылаются на один специальный глобальный адрес рантайма `runtime.zerobase`.
""",
        "pitfalls": """
- Использование `map[string]bool` вместо `map[string]struct{}` в многомиллионных кэшах.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему для сигнальных каналов используют `chan struct{}`, а не `chan bool`?»
**Ответ:** Потому что `chan struct{}` четко сообщает читателю кода о том, что передается только факт сигнала, и не тратит ни одного байта на хранение значения в буфере.
"""
    },
    {
        "num": 60,
        "title": "Иммутабельная структура (Immutable Struct) и порождающие методы WithName(name) Person",
        "task": "Создай \"immutable\" структуру: поля неэкспортируемые, изменение только через методы, возвращающие новую копию (не меняя оригинал). Напиши WithName(name string) Person (как в Go context).",
        "theory": """
**Паттерн иммутабельных структур (Immutable Builder в стиле `context.Context`):**
- Все поля неэкспортируемые;
- Методы модификации возвращают **новую независимую структуру** `return p`;
- Гарантирует абсолютную потокобезопасность без мьютексов.
""",
        "step_by_step": """
1. Создаем структуру `type ImmutableUser struct { id int; name string }`.
2. Пишем `WithName(name string) ImmutableUser`.
3. Проверяем сохранение старого экземпляра.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type ImmutableUser struct {
	id   int
	name string
}

func NewImmutableUser(id int, name string) ImmutableUser {
	return ImmutableUser{id: id, name: name}
}

func (u ImmutableUser) WithName(newName string) ImmutableUser {
	u.name = newName // Модифицирует копию и возвращает ее
	return u
}

func (u ImmutableUser) Name() string {
	return u.name
}

func main() {
	u1 := NewImmutableUser(1, "Первоначальное имя")
	u2 := u1.WithName("Новое имя")

	fmt.Printf("u1: %s (ОРИГИНАЛ НЕ ИЗМЕНИЛСЯ!)\n", u1.Name())
	fmt.Printf("u2: %s (НОВЫЙ ЭКЗЕМПЛЯР)\n", u2.Name())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# u1: Первоначальное имя (ОРИГИНАЛ НЕ ИЗМЕНИЛСЯ!)
# u2: Новое имя (НОВЫЙ ЭКЗЕМПЛЯР)"""
            }
        ],
        "under_the_hood": """
Копирование по значению на стеке.
""",
        "pitfalls": """
- Случайное использование Pointer Receiver, ломающее концепцию иммутабельности.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в стандартной библиотеке Go реализован пакет `context`?»
**Ответ:** Пакет `context` построен на цепочке иммутабельных структур (`valueCtx`, `timerCtx`, `cancelCtx`), где каждый вызов `context.WithValue` возвращает новую обертку над родительским контекстом.
"""
    },
    {
        "num": 61,
        "title": "Каверзный кейс: ошибка присвоения m['john'].Age = 30 в мапе структур и решение через map[string]*User",
        "task": "Каверзный случай: Мапа структур: Создай map[string]User. Добавь юзера. Попробуй изменить его возраст напрямую: m[\"john\"].Age = 30. Получишь ошибку cannot assign to struct field in map. Замени мапу на map[string]*User и повтори.",
        "theory": """
**Почему `m["key"].Field = ...` запрещено компилятором:**
- Значения в хэш-таблице `map[string]User` **не являются адресуемыми (Not Addressable)**;
- При росте мапы бакеты перемещаются в памяти (эвакуация), и прямой указатель на поле структуры в бакете стал бы невалидным;
- **Решение 1:** Использовать мапу указателей `map[string]*User`;
- **Решение 2:** Извлечь копию структуры во временную переменную, изменить и записать обратно `u := m["key"]; u.Age = 30; m["key"] = u`.
""",
        "step_by_step": """
1. Демонстрируем причину ошибки в `map[string]User`.
2. Создаем `map[string]*User`.
3. Мутируем поле `m["john"].Age = 30`.
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
	// ❌ ОШИБКА:
	// mValue := map[string]User{"john": {Name: "John", Age: 20}}
	// mValue["john"].Age = 30 // cannot assign to struct field in map

	// ✅ СПОСОБ 1: Мапа указателей map[string]*User (РЕКОМЕНДУЕТСЯ):
	mPtr := map[string]*User{
		"john": {Name: "John", Age: 20},
	}
	mPtr["john"].Age = 30 // Успешная мутация через указатель!
	fmt.Printf("1. Через map[string]*User: %+v\n", *mPtr["john"])

	// ✅ СПОСОБ 2: Перезапись копии:
	mVal := map[string]User{"john": {Name: "John", Age: 20}}
	u := mVal["john"]
	u.Age = 35
	mVal["john"] = u
	fmt.Printf("2. Через перезапись копии: %+v\n", mVal["john"])
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Через map[string]*User: {Name:John Age:30}
# 2. Через перезапись копии: {Name:John Age:35}"""
            }
        ],
        "under_the_hood": """
`mPtr["john"]` возвращает указатель, разыменование которого позволяет напрямую писать в память кучи.
""",
        "pitfalls": """
- Попытка взять адрес `&m["key"]` (ошибка компиляции `cannot take the address of m["key"]`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему элементы среза `s[0].Age = 30` можно изменять на месте, а элементы мапы `m["k"].Age = 30` нельзя?»
**Ответ:** Потому что элементы среза непрерывно расположены в памяти и адресуемы (`&s[0]`), а элементы мапы могут менять свое физическое расположение в бакетах при рехэшировании.
"""
    },
    {
        "num": 62,
        "title": "Реализация структуры Stack на срезе: методы Push, Pop (LIFO), Peek и IsEmpty",
        "task": "Создай структуру Stack с полем-слайсом. Напиши методы Push, Pop (LIFO), Peek, IsEmpty. Реализуй через слайс с append и s[:len(s)-1].",
        "theory": """
Реализация классической структуры данных LIFO (Last-In-First-Out).
""",
        "step_by_step": """
1. Создаем `type IntStack struct { elements []int }`.
2. Пишем методы `Push(val int)`, `Pop() (int, bool)`, `Peek() (int, bool)`.
3. Тестируем стек.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type IntStack struct {
	items []int
}

func (s *IntStack) Push(val int) {
	s.items = append(s.items, val)
}

func (s *IntStack) Pop() (int, bool) {
	if s.IsEmpty() {
		return 0, false
	}
	lastIdx := len(s.items) - 1
	val := s.items[lastIdx]
	s.items = s.items[:lastIdx]
	return val, true
}

func (s *IntStack) Peek() (int, bool) {
	if s.IsEmpty() {
		return 0, false
	}
	return s.items[len(s.items)-1], true
}

func (s *IntStack) IsEmpty() bool {
	return len(s.items) == 0
}

func main() {
	stack := &IntStack{}
	stack.Push(10)
	stack.Push(20)
	stack.Push(30)

	top, _ := stack.Peek()
	fmt.Printf("Вершина стека (Peek): %d\n", top)

	fmt.Print("Извлечение элементов (Pop): ")
	for !stack.IsEmpty() {
		val, _ := stack.Pop()
		fmt.Printf("%d ", val)
	}
	fmt.Println()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Вершина стека (Peek): 30
# Извлечение элементов (Pop): 30 20 10"""
            }
        ],
        "under_the_hood": """
`s.items[:lastIdx]` уменьшает поле `Len` без реаллокации базового массива.
""",
        "pitfalls": """
- Вызов `Pop()` на пустом стеке без проверки `IsEmpty()`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как предотвратить утечку памяти в generic-стеке `Stack[T any]` при вызове `Pop()`?»
**Ответ:** Если `T` содержит указатели, перед срезом `s.items[:lastIdx]` необходимо обнулить последний элемент `var zero T; s.items[lastIdx] = zero`, чтобы GC мог освободить память.
"""
    },
    {
        "num": 63,
        "title": "Форматированный вывод структур: глаголы %+v (имена полей) и %#v (синтаксис Go)",
        "task": "Выведи структуру с помощью fmt.Printf(\"%+v\\n\", user) (с именами полей) и %#v (синтаксис Go).",
        "theory": """
Спецификаторы форматирования структур в пакете `fmt`.
""",
        "step_by_step": """
1. Создаем структуру `type ServerInfo struct { Host string; Port int }`.
2. Выводим через `%v`, `%+v` и `%#v`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type ServerInfo struct {
	Host string
	Port int
}

func main() {
	srv := ServerInfo{Host: "localhost", Port: 9090}

	fmt.Printf("1. Обычный %%v:     %v\n", srv)
	fmt.Printf("2. С полями %%+v:   %+v\n", srv)
	fmt.Printf("3. Go-синтаксис %%#v: %#v\n", srv)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Обычный %v:     {localhost 9090}
# 2. С полями %+v:   {Host:localhost Port:9090}
# 3. Go-синтаксис %#v: main.ServerInfo{Host:"localhost", Port:9090}"""
            }
        ],
        "under_the_hood": """
Глагол `%#v` использует `GoString()` или рефлексивно восстанавливает литерал.
""",
        "pitfalls": """
- Использование `%v` при отладке (не видно, какому значению принадлежит какое поле).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какой глагол `fmt` удобнее всего использовать в логах и сообщениях об ошибках в тестах?»
**Ответ:** Глагол `%#v` (он выводит точный Go-синтаксис со всеми типами и именами полей).
"""
    },
    {
        "num": 64,
        "title": "Односвязный список на структуре Node{Value int, Next *Node} и алгоритм обхода",
        "task": "Создайте структуру Node для односвязного списка (Value int, Next *Node) и напишите функцию, которая обходит список и выводит значения.",
        "theory": """
Базовая рекурсивная и итеративная структура связных списков.
""",
        "step_by_step": """
1. Создаем структуру `Node`.
2. Создаем цепочку `10 -> 20 -> 30`.
3. Обходим список.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Node struct {
	Value int
	Next  *Node
}

func PrintLinkedList(head *Node) {
	for curr := head; curr != nil; curr = curr.Next {
		fmt.Printf("%d -> ", curr.Value)
	}
	fmt.Println("nil")
}

func main() {
	head := &Node{
		Value: 100,
		Next: &Node{
			Value: 200,
			Next: &Node{
				Value: 300,
			},
		},
	}

	fmt.Print("Связный список: ")
	PrintLinkedList(head)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Связный список: 100 -> 200 -> 300 -> nil"""
            }
        ],
        "under_the_hood": """
Узлы связываются через 8-байтные указатели `Next`.
""",
        "pitfalls": """
- Попытка объявить `Next Node` по значению (рекурсивный бесконечный размер).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `type Node struct { Next Node }` вызывает ошибку компиляции?»
**Ответ:** Потому что размер структуры вычисляется статически, а прямая рекурсия приводит к бесконечному размеру памяти. Указатель `Next *Node` имеет фиксированный размер 8 байт.
"""
    },
    {
        "num": 65,
        "title": "Методы структуры Circle: Area() (Value Receiver) и Scale(factor) (Pointer Receiver)",
        "task": "Методы с получателем-значением и получателем-указателем: у структуры Circle метод Area() (значение) и Scale(factor) (указатель). Продемонстрируйте вызовы и разницу.",
        "theory": """
Разделение геометрии и трансформаций на структуре круга.
""",
        "step_by_step": """
1. Создаем `type Circle struct { Radius float64 }`.
2. Пишем `(c Circle) Area() float64`.
3. Пишем `(c *Circle) Scale(factor float64)`.
4. Сравниваем результаты.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"math"
)

type Circle struct {
	Radius float64
}

func (c Circle) Area() float64 {
	return math.Pi * c.Radius * c.Radius
}

func (c *Circle) Scale(factor float64) {
	if c != nil && factor > 0 {
		c.Radius *= factor
	}
}

func main() {
	c := Circle{Radius: 10.0}
	fmt.Printf("Исходный круг: R=%.1f | Площадь=%.2f\n", c.Radius, c.Area())

	c.Scale(2.0)
	fmt.Printf("После Scale(2): R=%.1f | Площадь=%.2f\n", c.Radius, c.Area())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Исходный круг: R=10.0 | Площадь=314.16
# После Scale(2): R=20.0 | Площадь=1256.64"""
            }
        ],
        "under_the_hood": """
`Scale` мутирует память `Radius` по адресу `c`.
""",
        "pitfalls": """
- Вызов `Scale` на неадресуемом `Circle{Radius: 5}.Scale(2)` (ошибка компиляции).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что делает компилятор при вызове `c.Scale(2)`?»
**Ответ:** Он автоматически берет адрес `(&c).Scale(2)`.
"""
    },
    {
        "num": 66,
        "title": "Фабричный конструктор NewDatabaseConnection(host, port) (*Connection, error) с валидацией",
        "task": "Конструкторы (Фабричные функции): Напишите функцию NewDatabaseConnection(host string, port int) (*Connection, error). Внутри функции производите валидацию порта (он должен быть от 1 до 65535). Если валидация не пройдена, возвращайте ошибку.",
        "theory": """
Валидация сетевых параметров при инициализации соединений к БД.
""",
        "step_by_step": """
1. Создаем структуру `Connection{Host string, Port int}`.
2. Пишем конструктор с валидацией `1 <= port <= 65535`.
3. Тестируем.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
)

type Connection struct {
	Host string
	Port int
}

func NewDatabaseConnection(host string, port int) (*Connection, error) {
	if host == "" {
		return nil, fmt.Errorf("host не может быть пустым")
	}
	if port < 1 || port > 65535 {
		return nil, fmt.Errorf("недопустимый порт %d (допустимый диапазон 1-65535)", port)
	}

	return &Connection{Host: host, Port: port}, nil
}

func main() {
	conn1, err1 := NewDatabaseConnection("postgres.prod.db", 5432)
	if err1 != nil {
		fmt.Println("Ошибка:", err1)
	} else {
		fmt.Printf("Подключение успешно: %+v\n", *conn1)
	}

	_, err2 := NewDatabaseConnection("postgres.prod.db", 70000)
	if err2 != nil {
		fmt.Printf("Ожидаемая ошибка: %v\n", err2)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Подключение успешно: {Host:postgres.prod.db Port:5432}
# Ожидаемая ошибка: недопустимый порт 70000 (допустимый диапазон 1-65535)"""
            }
        ],
        "under_the_hood": """
Возврат `(nil, error)` при сбое валидации.
""",
        "pitfalls": """
- Создание некорректного соединения через прямой литерал `Connection{Port: 99999}` в обход конструктора.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как запретить пользователям пакета создавать структуру напрямую в обход `NewDatabaseConnection`?»
**Ответ:** Сделать саму структуру или её критические поля неэкспортируемыми (с маленькой буквы) и экспортировать интерфейс.
"""
    },
    {
        "num": 67,
        "title": "Реализация методов односвязного списка: Append(val), Print() и Find(val)",
        "task": "Реализуйте связный список (односвязный) на структурах: добавление в конец, печать, поиск.",
        "theory": """
Полная инкапсуляция логики списка в структуре `LinkedList`.
""",
        "step_by_step": """
1. Создаем структуры `Node` и `LinkedList{head *Node}`.
2. Пишем методы `Append(val int)`, `Print()`, `Find(val int) bool`.
3. Тестируем методы.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Node struct {
	Value int
	Next  *Node
}

type LinkedList struct {
	head *Node
}

func (ll *LinkedList) Append(val int) {
	newNode := &Node{Value: val}
	if ll.head == nil {
		ll.head = newNode
		return
	}
	curr := ll.head
	for curr.Next != nil {
		curr = curr.Next
	}
	curr.Next = newNode
}

func (ll *LinkedList) Find(val int) bool {
	for curr := ll.head; curr != nil; curr = curr.Next {
		if curr.Value == val {
			return true
		}
	}
	return false
}

func (ll *LinkedList) Print() {
	for curr := ll.head; curr != nil; curr = curr.Next {
		fmt.Printf("%d -> ", curr.Value)
	}
	fmt.Println("nil")
}

func main() {
	list := &LinkedList{}
	list.Append(10)
	list.Append(20)
	list.Append(30)

	fmt.Print("Элементы списка: ")
	list.Print()

	fmt.Printf("Поиск 20: %t\n", list.Find(20))
	fmt.Printf("Поиск 99: %t\n", list.Find(99))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Элементы списка: 10 -> 20 -> 30 -> nil
# Поиск 20: true
# Поиск 99: false"""
            }
        ],
        "under_the_hood": """
Связный список в куче.
""",
        "pitfalls": """
- Добавление в конец за $O(N)$ (в продакшене хранят указатель на хвост `tail *Node` для вставки за $O(1)$).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как ускорить добавление в конец связного списка до $O(1)$?»
**Ответ:** Хранить в структуре `LinkedList` указатель на последний узел: `tail *Node`.
"""
    },
    {
        "num": 68,
        "title": "Выравнивание полей в памяти (Padding): StructA (24 байта) против StructB (16 байт) через unsafe.Sizeof",
        "task": "Выравнивание полей в памяти (Padding): Создайте две структуры с одинаковыми полями, но в разном порядке: StructA (поля: a int8, b int64, c int8) и StructB (поля: a int8, c int8, b int64). Выведите размер каждой структуры с помощью unsafe.Sizeof. Разберитесь, как порядок полей влияет на выравнивание и итоговый размер структуры в памяти.",
        "theory": """
**Детальная анатомия байтового выравнивания:**
1. **`StructA` (24 байта):**
   - `a int8`: 1 байт + 7 байт Padding (чтобы `b int64` начался с адреса кратного 8);
   - `b int64`: 8 байт;
   - `c int8`: 1 байт + 7 байт Padding (выравнивание общего размера структуры кратно 8);
   - Итого: $1+7+8+1+7 = 24$ байта.
2. **`StructB` (16 байт):**
   - `a int8`: 1 байт;
   - `c int8`: 1 байт + 6 байт Padding;
   - `b int64`: 8 байт;
   - Итого: $1+1+6+8 = 16$ байт (экономия 33% RAM!).
""",
        "step_by_step": """
1. Объявляем `StructA` и `StructB`.
2. Замеряем `unsafe.Sizeof`.
3. Анализируем байтовую раскладку.
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

type StructA struct {
	a int8  // 1B + 7B pad
	b int64 // 8B
	c int8  // 1B + 7B pad
}

type StructB struct {
	a int8  // 1B
	c int8  // 1B + 6B pad
	b int64 // 8B
}

func main() {
	var a StructA
	var b StructB

	fmt.Printf("Размер StructA: %d байт (нерациональный порядок)\n", unsafe.Sizeof(a))
	fmt.Printf("Размер StructB: %d байт (оптимизированный порядок)\n", unsafe.Sizeof(b))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Размер StructA: 24 байт (нерациональный порядок)
# Размер StructB: 16 байт (оптимизированный порядок)"""
            }
        ],
        "under_the_hood": """
ABI x86-64 требует выравнивания 64-битных целых чисел по 8-байтной границе.
""",
        "pitfalls": """
- Случайное размещение `bool` и `int64` через один.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каков размер пустой структуры `struct{}` в конце другой структуры?»
**Ответ:** Если `struct{}` находится в конце структуры, компилятор добавляет 1 машинное слово (8 байт) Padding, чтобы указатель на поле не указывал за пределы выделенного блока памяти!
"""
    },
    {
        "num": 69,
        "title": "Теги структуры type User struct { Name string `json:'name'` } и валидация схемы",
        "task": "Создай структуру с тегами (struct tags) type User struct { Name string `json:\"name\"` }.",
        "theory": """
Базовое объявление структуры с тегами сериализации.
""",
        "step_by_step": """
1. Создаем структуру с тегами.
2. Маршалим в JSON.
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
	Name string `json:"name"`
}

func main() {
	u := User{Name: "Gopher"}
	data, _ := json.Marshal(u)
	fmt.Printf("JSON: %s\n", string(data))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# JSON: {"name":"Gopher"}"""
            }
        ],
        "under_the_hood": """
Теги в метаданных типа.
""",
        "pitfalls": """
- Опечатки в кавычках.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как объединить несколько тегов в одном поле?»
**Ответ:** Через пробел: `` `json:"name" yaml:"name" db:"name"` ``.
"""
    },
    {
        "num": 70,
        "title": "Двоичное дерево поиска (BST) на структуре TreeNode и симметричный обход (In-Order Traversal)",
        "task": "[Высокая сложность]: Создай структуру TreeNode для бинарного дерева (поля Value int, Left *TreeNode, Right *TreeNode). Напиши метод для обхода дерева (in-order traversal).",
        "theory": """
**Двоичное дерево поиска (Binary Search Tree - BST):**
- У каждого узла `Left.Value < Value < Right.Value`;
- **Симметричный обход (In-Order Traversal):** рекурсивно обходит `Left -> Root -> Right`;
- Гарантирует вывод элементов дерева **в строго отсортированном порядке** за $O(N)$ времени!
""",
        "step_by_step": """
1. Создаем `type TreeNode struct { Value int; Left, Right *TreeNode }`.
2. Пишем метод `Insert(val int)`.
3. Пишем метод `InOrder(visit func(int))`.
4. Демонстрируем сортировку.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type TreeNode struct {
	Value int
	Left  *TreeNode
	Right *TreeNode
}

func (n *TreeNode) Insert(val int) *TreeNode {
	if n == nil {
		return &TreeNode{Value: val}
	}
	if val < n.Value {
		n.Left = n.Left.Insert(val)
	} else if val > n.Value {
		n.Right = n.Right.Insert(val)
	}
	return n
}

func (n *TreeNode) InOrder(visit func(int)) {
	if n == nil {
		return
	}
	n.Left.InOrder(visit)  // 1. Левое поддерево
	visit(n.Value)         // 2. Текущий узел
	n.Right.InOrder(visit) // 3. Правое поддерево
}

func main() {
	var root *TreeNode
	numbers := []int{50, 30, 70, 20, 40, 60, 80}

	for _, num := range numbers {
		root = root.Insert(num)
	}

	fmt.Print("In-Order обход дерева (отсортировано): ")
	root.InOrder(func(val int) {
		fmt.Printf("%d ", val)
	})
	fmt.Println()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# In-Order обход дерева (отсортировано): 20 30 40 50 60 70 80"""
            }
        ],
        "under_the_hood": """
Рекурсивные вызовы используют стек вызовов горутины.
""",
        "pitfalls": """
- Вырождение несбалансированного BST в связный список со сложностью $O(N)$ вместо $O(\log N)$.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каковы три вида обхода бинарных деревьев и где они применяются?»
**Ответ:** 1) In-Order (L-Root-R) — для сортировки; 2) Pre-Order (Root-L-R) — для клонирования/сериализации дерева; 3) Post-Order (L-R-Root) — для удаления дерева и вычисления математических выражений в AST.
"""
    },
    {
        "num": 71,
        "title": "Переопределение методов (Method Overriding) в Child и вызов оригинального метода Parent",
        "task": "Переопределение методов: В структуре Parent напишите метод Greet() string. Встройте её в структуру Child. Напишите метод Greet() для Child. Вызовите метод у объекта Child и продемонстрируйте, как вызывается переопределенный метод, а также как при желании можно вызвать оригинальный метод родителя.",
        "theory": """
**Переопределение (Shadowing / Overriding) методов в Go:**
- Если `Child` определяет собственный метод `Greet()`, он **затеняет** метод `Parent.Greet()`;
- Вызов `child.Greet()` вызывает метод `Child`;
- Вызов `child.Parent.Greet()` вызывает оригинальный метод встроенного родителя.
""",
        "step_by_step": """
1. Создаем `type Parent struct{}` с методом `Greet() string`.
2. Создаем `type Child struct { Parent }` с собственным методом `Greet() string`.
3. Сравниваем вызовы.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Parent struct{}

func (Parent) Greet() string {
	return "Приветствие от Parent структуры"
}

type Child struct {
	Parent // Встраивание
}

// Переопределение метода:
func (Child) Greet() string {
	return "Приветствие от Child структуры (ПЕРЕОПРЕДЕЛЕНО)"
}

func main() {
	c := Child{}

	// 1. Вызов переопределенного метода Child:
	fmt.Printf("1. c.Greet():        %s\n", c.Greet())

	// 2. Явный вызов метода родителя Parent:
	fmt.Printf("2. c.Parent.Greet(): %s\n", c.Parent.Greet())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. c.Greet():        Приветствие от Child структуры (ПЕРЕОПРЕДЕЛЕНО)
# 2. c.Parent.Greet(): Приветствие от Parent структуры"""
            }
        ],
        "under_the_hood": """
Компилятор статически выбирает метод `Child.Greet` с глубиной 0.
""",
        "pitfalls": """
- Иллюзия виртуального полиморфизма (в Go встроенный `Parent` не знает о методах `Child` и не может вызывать переопределенные методы внутри себя).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go встраивание структур не поддерживает полиморфный вызов методов (динамический vtable) как `virtual` в C++?»
**Ответ:** Потому что Go разделяет наследование состояния (композиция структур) и полиморфизм поведения (интерфейсы). Для виртуального полиморфизма в Go используются исключительно интерфейсы.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 3: {len(exercises)} exercises.")
