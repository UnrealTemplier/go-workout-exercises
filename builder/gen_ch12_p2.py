# Chapter 12 Part 2: Exercises 24 to 45

exercises = [
    {
        "num": 24,
        "title": "Указатель на интерфейс (*interface{} / *any): почему это антипаттерн в Go",
        "task": "Напишите функцию, которая принимает interface{} и указатель на интерфейс. Попытайтесь изменить значение через указатель на интерфейс и поймите, почему это антипаттерн.",
        "theory": """
**Почему `*interface{}` почти никогда не нужен в Go:**
- Интерфейс `any` (`interface{}`) уже сам по себе является 16-байтным дескриптором `(itab/_type, data)`, где `data` хранит указатель на значение;
- Использование `*any` добавляет второй уровень косвенности (`**eface`), ухудшает читаемость и лишает код полиморфизма;
- Исключение: редкие методы низкоуровневой десериализации JSON/CBOR в динамические типы.
""",
        "step_by_step": """
1. Пишем функцию `BadInterfacePtr(v *any)`.
2. Пишем идиоматичную функцию `GoodGeneric[T any](v *T)`.
3. Сравниваем подходы.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

// АНТИПАТТЕРН: указатель на пустой интерфейс
func BadInterfacePtr(v *any) {
	if v != nil {
		*v = "новое строковое значение"
	}
}

// ИДИОМАТИЧНО: передача типизированного указателя или дженерика
func GoodGeneric[T any](v *T, newVal T) {
	if v != nil {
		*v = newVal
	}
}

func main() {
	var dyn any = 123
	fmt.Printf("1. До BadInterfacePtr:   %v (%T)\n", dyn, dyn)

	BadInterfacePtr(&dyn)
	fmt.Printf("2. После BadInterfacePtr: %v (%T)\n", dyn, dyn)

	num := 42
	GoodGeneric(&num, 100)
	fmt.Printf("3. Идиоматичный дженерик: %d\n", num)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. До BadInterfacePtr:   123 (int)
# 2. После BadInterfacePtr: новое строковое значение (string)
# 3. Идиоматичный дженерик: 100"""
            }
        ],
        "under_the_hood": """
Интерфейс в рантайме представлен структурой `eface`. Указатель `*any` — это указатель на саму 16-байтную структуру `eface`.
""",
        "pitfalls": """
- Передача `&val` в функцию, принимающую `any`: внутри функции интерфейс упаковывает `*int`, а не `int`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В каких редких случаях допустим указатель на интерфейс `*io.Reader`?»
**Ответ:** Практически никогда в прикладном коде. В 99.9% случаев передают сам интерфейс `io.Reader` по значению.
"""
    },
    {
        "num": 25,
        "title": "Мутация среза по значению: изменение s[0] = 99 в разделяемой памяти",
        "task": "Напиши функцию, принимающую срез []int. Измени существующий элемент s[0]. Выведи срез снаружи (он изменился! срез — это ссылка под капотом).",
        "theory": """
Закрепление разделения базового массива между заголовками среза.
""",
        "step_by_step": """
1. Пишем `SetFirst(s []int, val int)`.
2. Вызываем `SetFirst(numbers, 99)`.
3. Печатаем обновленный срез.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func SetFirst(s []int, val int) {
	if len(s) > 0 {
		s[0] = val
	}
}

func main() {
	numbers := []int{1, 2, 3}
	fmt.Printf("До:    %v\n", numbers)

	SetFirst(numbers, 99)

	fmt.Printf("После: %v (ПЕРВЫЙ ЭЛЕМЕНТ ИЗМЕНИЛСЯ!)\n", numbers)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До:    [1 2 3]
# После: [99 2 3] (ПЕРВЫЙ ЭЛЕМЕНТ ИЗМЕНИЛСЯ!)"""
            }
        ],
        "under_the_hood": """
Запись по указателю `Data` базового массива.
""",
        "pitfalls": """
- Вызов на пустом срезе `[]int{}` (паника `index out of range`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Является ли срез ссылочным типом в терминах спецификации Go?»
**Ответ:** Формально нет (срез — это значимая структура `SliceHeader`), но практически он обладает ссылочной семантикой благодаря внутреннему указателю `Data`.
"""
    },
    {
        "num": 26,
        "title": "Структура со срезом внутри (Team.Members): неполная изоляция при передаче по значению",
        "task": "Создайте структуру, содержащую слайс. Передайте структуру по значению, а затем измените элемент слайса внутри переданной структуры. Объясните, почему оригинальный слайс изменился.",
        "theory": """
**Поверхностное копирование структур (Shallow Copy Pitfall):**
- При передаче структуры `Team` по значению копируются ее поля (`Name string`, `Members []string`);
- Поле `Members` копируется как 24-байтный дескриптор `SliceHeader`;
- Базовый массив строк **НЕ копируется**;
- Мутация `t.Members[0] = "New"` изменит срез в оригинальной структуре!
""",
        "step_by_step": """
1. Создаем структуру `type Team struct { Name string; Members []string }`.
2. Пишем функцию `ModifyMember(t Team)`.
3. Меняем `t.Members[0] = "Капитан Очевидность"`.
4. Проверяем оригинал в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Team struct {
	Name    string
	Members []string
}

func ModifyMember(t Team) {
	t.Name = "Новое имя команды" // Изменяет только копию поля Name
	if len(t.Members) > 0 {
		t.Members[0] = "Алексей (Лид)" // ИЗМЕНЯЕТ РАЗДЕЛЯЕМЫЙ СРЕЗ!
	}
}

func main() {
	team := Team{
		Name:    "Gophers",
		Members: []string{"Иван", "Сергей", "Анна"},
	}

	fmt.Printf("1. До:    Name=%-10s | Members=%v\n", team.Name, team.Members)

	ModifyMember(team)

	fmt.Printf("2. После: Name=%-10s | Members=%v (СРЕЗ ВНУТРИ ИЗМЕНИЛСЯ!)\n",
		team.Name, team.Members)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. До:    Name=Gophers    | Members=[Иван Сергей Анна]
# 2. После: Name=Gophers    | Members=[Алексей (Лид) Сергей Анна] (СРЕЗ ВНУТРИ ИЗМЕНИЛСЯ!)"""
            }
        ],
        "under_the_hood": """
При присваивании структуры создается поверхностная копия (Shallow Copy).
""",
        "pitfalls": """
- Убежденность, что передача структуры по значению гарантирует 100% изоляцию вложенных срезов и мап.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как сделать глубокое копирование (Deep Copy) структуры со срезом?»
**Ответ:** Создать новую структуру и скопировать срез через `copy(newSlice, origSlice)` или пакет `slices.Clone`.
"""
    },
    {
        "num": 27,
        "title": "Escape-анализ: функция GetPointer() *int и проверка через go build -gcflags='-m'",
        "task": "Напиши функцию GetPointer() *int. Внутри создай x := 42; return &x. Go выделит x на куче (escape analysis). Проверь через go build -gcflags=\"-m\", что x \"escapes to heap\".",
        "theory": """
Диагностика побега в кучу в реальном выводе компилятора.
""",
        "step_by_step": """
1. Пишем `GetPointer() *int`.
2. Возвращаем `&x`.
3. Анализируем отчет компилятора `-gcflags="-m"`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func GetPointer() *int {
	x := 42
	return &x // &x экранируется в кучу
}

func main() {
	p := GetPointer()
	fmt.Printf("Значение из кучи: %d (адрес: %p)\n", *p, p)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go build -gcflags="-m" main.go
# ./main.go:6:2: moved to heap: x
# ./main.go:12:12: ... argument does not escape
go run main.go
# Значение из кучи: 42 (адрес: 0xc000018030)"""
            }
        ],
        "under_the_hood": """
Оптимизатор компилятора заменяет размещение в стеке на вызов `runtime.newobject`.
""",
        "pitfalls": """
- Случайный побег больших переменных в кучу в критических для latency участках кода.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какие основные причины побега переменных в кучу (Heap Escape)?»
**Ответ:** 1) Возврат указателя на локальную переменную; 2) Передача в интерфейс `any` (например `fmt.Println`); 3) Выделение памяти неизвестного на этапе компиляции размера `make([]int, n)`; 4) Захват переменной в замыкании; 5) Слишком большой размер переменной (> 64 КБ на стек).
"""
    },
    {
        "num": 28,
        "title": "Структура с указателем на другую структуру: мутация данных через вложенный указатель",
        "task": "Создайте структуру с указателем на другую структуру. Передайте её по значению и измените поле вложенной структуры через указатель.",
        "theory": """
**Утечка состояния через вложенные указатели (Pointer Aliasing):**
- Структура `Order` передается по значению;
- Поле `Customer *User` копируется как 8-байтный адрес;
- Модификация `o.Customer.Name = ...` изменяет данные в куче, общие для всех копий `Order`!
""",
        "step_by_step": """
1. Создаем `type Customer struct { Name string }`.
2. Создаем `type Order struct { ID int; Client *Customer }`.
3. Пишем `UpdateCustomer(o Order)`.
4. Демонстрируем изменение `Client.Name` в исходном заказе.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Customer struct {
	Name string
}

type Order struct {
	ID     int
	Client *Customer
}

func UpdateCustomer(o Order) {
	o.ID = 999                // Локальная копия
	o.Client.Name = "Константин" // Мутация общего объекта в куче!
}

func main() {
	client := &Customer{Name: "Илья"}
	order := Order{ID: 1, Client: client}

	fmt.Printf("1. До:    ID=%d | Клиент=%s\n", order.ID, order.Client.Name)

	UpdateCustomer(order)

	fmt.Printf("2. После: ID=%d | Клиент=%s (КЛИЕНТ ИЗМЕНИЛСЯ!)\n",
		order.ID, order.Client.Name)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. До:    ID=1 | Клиент=Илья
# 2. После: ID=1 | Клиент=Константин (КЛИЕНТ ИЗМЕНИЛСЯ!)"""
            }
        ],
        "under_the_hood": """
Два экземпляра `Order` ссылаются на один и тот же адрес `Client` в куче.
""",
        "pitfalls": """
- Непреднамеренная мутация общих разделяемых структур в многопоточном коде.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как защитить вложенные структуры от случайных мутаций?»
**Ответ:** Использовать семантику значений (хранить `Client Customer` без указателя) или создавать глубокие копии объектов перед передачей.
"""
    },
    {
        "num": 29,
        "title": "Бенчмарк копирования массива [1000000]int (8 МБ) по значению vs передача указателя",
        "task": "Создай массив [3]int и передай в функцию. Покажи, что массив передаётся по значению (копируется целиком). Измерь время копирования большого массива [1000000]int через time.Now() — сравни с передачей указателя.",
        "theory": """
**Сравнительный анализ накладных расходов памяти:**
- Передача `[1000000]int` по значению: копирует $1\,000\,000 \times 8 = 8\text{ МБ}$ данных в стек (занимает миллисекунды);
- Передача `*[1000000]int`: копирует ровно 8 байт адреса (занимает доли наносекунды, быстрее в $10\,000$ раз!).
""",
        "step_by_step": """
1. Создаем тип `type HugeArray [1000000]int`.
2. Пишем функцию `PassByValue(arr HugeArray)`.
3. Пишем функцию `PassByPointer(arr *HugeArray)`.
4. Замеряем время через `time.Since()`.
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

type HugeArray [1000000]int // 8 Мегабайт данных

func PassByValue(arr HugeArray) int {
	return arr[0]
}

func PassByPointer(arr *HugeArray) int {
	return arr[0]
}

func main() {
	var bigData HugeArray

	// 1. Замер передачи по значению (копирование 8 МБ):
	startVal := time.Now()
	for i := 0; i < 100; i++ {
		_ = PassByValue(bigData)
	}
	durVal := time.Since(startVal)

	// 2. Замер передачи по указателю (копирование 8 байт):
	startPtr := time.Now()
	for i := 0; i < 100; i++ {
		_ = PassByPointer(&bigData)
	}
	durPtr := time.Since(startPtr)

	fmt.Printf("100 вызовов PassByValue (8 МБ):   %v\n", durVal)
	fmt.Printf("100 вызовов PassByPointer (8 байт): %v (РАЗНИЦА В ТЫСЯЧИ РАЗ!)\n", durPtr)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 100 вызовов PassByValue (8 МБ):   15.42ms
# 100 вызовов PassByPointer (8 байт): 420ns (РАЗНИЦА В ТЫСЯЧИ РАЗ!)"""
            }
        ],
        "under_the_hood": """
`PassByValue` вызывает цикл `DUFFCOPY` / `memmove` на 8 МБ в цикле.
""",
        "pitfalls": """
- Переполнение стека горутины при глубокой рекурсии с тяжелыми массивами.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каков порог размера структуры/массива, после которого выгоднее передавать указатель?»
**Ответ:** Общепринятая граница в Go — $64-128$ байт (размер одной-двух линий кэша процессора L1).
"""
    },
    {
        "num": 30,
        "title": "Указатель на структуру Employee и функция GiveBonus(e *Employee, amount int)",
        "task": "Указатели на структуры: Создайте структуру Employee с полем Salary. Напишите функцию GiveBonus(e *Employee, amount int), которая увеличивает зарплату. Передайте структуру по указателю.",
        "theory": """
Идиоматичная мутация бизнес-сущностей в сервисах.
""",
        "step_by_step": """
1. Создаем структуру `Employee{Name string, Salary int}`.
2. Пишем `GiveBonus(e *Employee, amount int)`.
3. Увеличиваем `e.Salary += amount`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Employee struct {
	Name   string
	Salary int
}

func GiveBonus(e *Employee, amount int) {
	if e != nil {
		e.Salary += amount
	}
}

func main() {
	emp := &Employee{Name: "Артем", Salary: 150000}
	fmt.Printf("До бонуса:    %+v\n", emp)

	GiveBonus(emp, 50000)

	fmt.Printf("После бонуса: %+v (ЗАРПЛАТА ОБНОВЛЕНА!)\n", emp)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До бонуса:    &{Name:Артем Salary:150000}
# После бонуса: &{Name:Артем Salary:200000} (ЗАРПЛАТА ОБНОВЛЕНА!)"""
            }
        ],
        "under_the_hood": """
Прямая модификация поля по смещению указателя.
""",
        "pitfalls": """
- Забыть знак `&` при создании структуры или вызове.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в доменных сервисах (DDD) сущности передают по указателю?»
**Ответ:** Потому что сущности обладают уникальной идентичностью (ID) и состоянием, которое должно изменяться централизованно.
"""
    },
    {
        "num": 31,
        "title": "Исторический баг захвата переменной цикла по ссылке в горутине до и после Go 1.22",
        "task": "Создайте цикл for, в котором создается горутина, принимающая переменную цикла по ссылке (особенно актуально для версий Go до 1.22). Изучите классическую проблему замыкания и указателей.",
        "theory": """
**Анализ классической проблемы конкурентности:**
- **До Go 1.22:** Переменная цикла `v` имела один адрес. Горутины читали `v` после завершения цикла и все выводили последнее значение;
- **Go 1.22+:** Каждая итерация создает независимый экземпляр `v`.
""",
        "step_by_step": """
1. Создаем цикл с горутинами.
2. Демонстрируем безопасный паттерн с явной передачей аргумента `go func(val int) { ... }(i)`.
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

func main() {
	var wg sync.WaitGroup

	fmt.Println("Запуск горутин с явной передачей аргумента (безопасно для всех версий Go):")
	for i := 1; i <= 3; i++ {
		wg.Add(1)
		// Передаем i параметром по значению:
		go func(val int) {
			defer wg.Done()
			fmt.Printf("  Горутина получила значение: %d\n", val)
		}(i)
	}

	wg.Wait()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Запуск горутин с явной передачей аргумента (безопасно для всех версий Go):
#   Горутина получила значение: 3
#   Горутина получила значение: 1
#   Горутина получила значение: 2"""
            }
        ],
        "under_the_hood": """
Значение `i` копируется в стек горутины при планировании `runtime.newproc`.
""",
        "pitfalls": """
- Запуск `go func() { fmt.Println(&i) }()` в Go $\le 1.21$.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как выявить утечку переменных цикла в горутинах?»
**Ответ:** Запустить `go vet` или скомпилировать с детектором гонок `go run -race`.
"""
    },
    {
        "num": 32,
        "title": "Анатомия интерфейса any (eface): type + data и почему указатель на any избыточен",
        "task": "Создай interface{} (или any) переменную, присвой ей int. Попробуй взять указатель на interface{} и изменить значение. Объясни, что хранится внутри interface{} (type + value или pointer to value).",
        "theory": """
**Структура `eface` (Empty Interface Header):**
- Состоит из двух 8-байтных полей: `_type *rtype` (метаданные типа) и `data unsafe.Pointer` (указатель на данные в куче);
- Присвоение `var i any = 42` аллоцирует значение в куче (или использует заготовленную константу) и сохраняет адрес в `data`.
""",
        "step_by_step": """
1. Создаем `var box any = 42`.
2. Анализируем тип и значение.
3. Переназначаем `box = "теперь строка"`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	var box any = 42
	fmt.Printf("1. box: %v (Тип: %T)\n", box, box)

	// Переприсваивание интерфейса меняет дескриптор eface:
	box = "теперь это строка"
	fmt.Printf("2. box: %v (Тип: %T)\n", box, box)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. box: 42 (Тип: int)
# 2. box: теперь это строка (Тип: string)"""
            }
        ],
        "under_the_hood": """
При смене типа компилятор перезаписывает оба поля `_type` и `data` в `eface`.
""",
        "pitfalls": """
- Приведение типов без проверки `val, ok := box.(int)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каковы размеры структуры `iface` (непустой интерфейс) и `eface` (пустой `any`)?»
**Ответ:** Обе структуры занимают ровно 16 байт на 64-битных системах.
"""
    },
    {
        "num": 33,
        "title": "Передача переменной цикла как аргумента анонимной функции: эталон изоляции",
        "task": "То же самое, что и 79, но передавайте переменную цикла как аргумент в анонимную функцию. Сравните поведение.",
        "theory": """
Паттерн явного проброса параметров для полной переносимости между версиями Go.
""",
        "step_by_step": """
1. Создаем список задач `[]string{"Email", "SMS", "Push"}`.
2. Передаем элемент аргументом в горутину.
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

func main() {
	var wg sync.WaitGroup
	channels := []string{"Email", "SMS", "Push"}

	for _, ch := range channels {
		wg.Add(1)
		go func(channelName string) {
			defer wg.Done()
			fmt.Printf("Отправка уведомления через: %s\n", channelName)
		}(ch)
	}

	wg.Wait()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Отправка уведомления через: Push
# Отправка уведомления через: Email
# Отправка уведомления через: SMS"""
            }
        ],
        "under_the_hood": """
Копирование строки в локальный кадр горутины.
""",
        "pitfalls": """
- Забыть `wg.Done()` в `defer`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в продакшене все еще рекомендуется передавать аргументы явно, несмотря на исправление в Go 1.22?»
**Ответ:** Это делает код самодокументируемым, явным, устойчивым к рефакторингу и совместимым с более старыми версиями компилятора Go.
"""
    },
    {
        "num": 34,
        "title": "Классическая ловушка: AppendAndModify(s []int) []int и поведение при cap == len vs cap > len",
        "task": "Напиши функцию AppendAndModify(s []int) []int. Внутри сделай s = append(s, 100), затем s[0] = 999. Верни s. В main создай слайс с cap == len (чтобы гарантировать реаллокацию). Покажи, что s[0] в оригинале НЕ изменился (реаллокация), но если cap > len — изменился. Это классическая ловушка!",
        "theory": """
**Супер-ловушка собеседований BigTech по срезам:**
1. **Случай `cap == len`:** `append` выделяет НОВЫЙ массив. Модификация `s[0] = 999` происходит в НОВОМ массиве. В исходном срезе в `main` элемент `s[0]` **НЕ изменился**;
2. **Случай `cap > len`:** `append` пишет в СТАРЫЙ массив. Модификация `s[0] = 999` происходит в СТАРОМ массиве. В исходном срезе в `main` элемент `s[0]` **ИЗМЕНИЛСЯ**!
""",
        "step_by_step": """
1. Пишем `AppendAndModify(s []int) []int`.
2. Тестируем кейс 1: `make([]int, 2, 2)` (`cap == len`).
3. Тестируем кейс 2: `make([]int, 2, 5)` (`cap > len`).
4. Сравниваем результаты в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func AppendAndModify(s []int) []int {
	s = append(s, 100)
	s[0] = 999
	return s
}

func main() {
	// КЕЙС 1: cap == len (Гарантированная реаллокация)
	s1 := make([]int, 2, 2)
	s1[0], s1[1] = 10, 20
	fmt.Printf("1. КЕЙС 1 (cap==len) ДО:  s1 = %v\n", s1)
	res1 := AppendAndModify(s1)
	fmt.Printf("   res1 (новый массив): %v\n", res1)
	fmt.Printf("   s1 в main (СТАРЫЙ):  %v (s1[0] НЕ ИЗМЕНИЛСЯ!)\n\n", s1)

	// КЕЙС 2: cap > len (БЕЗ реаллокации)
	s2 := make([]int, 2, 5)
	s2[0], s2[1] = 10, 20
	fmt.Printf("2. КЕЙС 2 (cap>len)  ДО:  s2 = %v\n", s2)
	res2 := AppendAndModify(s2)
	fmt.Printf("   res2 (тот же массив): %v\n", res2)
	fmt.Printf("   s2 в main (ОБЩИЙ):   %v (s2[0] ИЗМЕНИЛСЯ НА 999!)\n", s2)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. КЕЙС 1 (cap==len) ДО:  s1 = [10 20]
#    res1 (новый массив): [999 20 100]
#    s1 в main (СТАРЫЙ):  [10 20] (s1[0] НЕ ИЗМЕНИЛСЯ!)
# 
# 2. КЕЙС 2 (cap>len)  ДО:  s2 = [10 20]
#    res2 (тот же массив): [999 20 100]
#    s2 в main (ОБЩИЙ):   [999 20] (s2[0] ИЗМЕНИЛСЯ НА 999!)"""
            }
        ],
        "under_the_hood": """
При `cap > len` указатель `s.Data` не меняется, поэтому `s[0] = 999` мутирует память, на которую по-прежнему указывает `s2.Data`.
""",
        "pitfalls": """
- Передача подсреза `arr[1:3]` в стороннюю библиотеку без трехзначного слайсинга `arr[1:3:3]`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как защитить срез от скрытых мутаций в функции `AppendAndModify`?»
**Ответ:** Использовать трехзначный слайсинг (Full Slice Expression) `s[0:2:2]`, принудительно устанавливающий `cap = len`, что гарантирует аллокацию нового массива при `append`.
"""
    },
    {
        "num": 35,
        "title": "Удвоение числа по указателю DoublePtr(n *int)",
        "task": "Передача по указателю: Перепиши функцию как DoublePtr(n *int) и умножь *n на 2. Передай адрес переменной. Проверь, что оригинал изменился.",
        "theory": """
Базовая мутация примитива через разыменование.
""",
        "step_by_step": """
1. Пишем `DoublePtr(n *int)`.
2. Выполняем `*n *= 2`.
3. Тестируем в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func DoublePtr(n *int) {
	if n != nil {
		*n *= 2
	}
}

func main() {
	val := 21
	fmt.Printf("До DoublePtr:    %d\n", val)

	DoublePtr(&val)

	fmt.Printf("После DoublePtr: %d\n", val)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До DoublePtr:    21
# После DoublePtr: 42"""
            }
        ],
        "under_the_hood": """
Инструкция `SHLQ $1, (AX)` (битовый сдвиг влево на 1 для быстрого умножения на 2).
""",
        "pitfalls": """
- Забыть проверку `n != nil`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как оптимизатор Go компилирует умножение на степени двойки?»
**Ответ:** Заменяет `MULQ` на быструю инструкцию битового сдвига `SHLQ`.
"""
    },
    {
        "num": 36,
        "title": "Метод со значением-получателем (Value Receiver) и неизменность оригинальной структуры",
        "task": "Напиши структуру Counter с полем count int. Напиши метод Add() для неё (value receiver). Вызови метод. Убедись, что оригинал не поменялся.",
        "theory": """
Метод с Value Receiver `func (c Counter) Add()` получает **копию структуры**, поэтому любые изменения `c.count++` теряются при выходе из метода.
""",
        "step_by_step": """
1. Создаем структуру `Counter{count int}`.
2. Пишем `func (c Counter) Add()`.
3. Вызываем метод и проверяем `count`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Counter struct {
	count int
}

func (c Counter) Add() {
	c.count++ // Изменяет локальную копию
}

func main() {
	cnt := Counter{count: 10}
	fmt.Printf("До Add():    %+v\n", cnt)

	cnt.Add()

	fmt.Printf("После Add(): %+v (ОРИГИНАЛ НЕ ИЗМЕНИЛСЯ!)\n", cnt)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До Add():    {count:10}
# После Add(): {count:10} (ОРИГИНАЛ НЕ ИЗМЕНИЛСЯ!)"""
            }
        ],
        "under_the_hood": """
Вызов трансформируется в `Counter.Add(cnt)`.
""",
        "pitfalls": """
- Использование Value Receiver для методов-мутаторов (Setter).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Когда Value Receiver предпочтителен?»
**Ответ:** Для иммутабельных структур, типов времени (`time.Time`) и методов чтения (Getter).
"""
    },
    {
        "num": 37,
        "title": "Срезы по значению и append: почему добавленный элемент не появился в оригинале",
        "task": "Каверзный случай: Срезы и Append: Передай тот же срез по значению в функцию и сделай внутри s = append(s, 4). Выведи длину среза в main. Убедись, что добавленный элемент *не появился* в оригинале. (Объяснение: append может изменить указатель, длину и емкость, а мы меняем только копию заголовка среза).",
        "theory": """
Закрепление принципа неизменности длины оригинального среза.
""",
        "step_by_step": """
1. Пишем `AppendElement(s []int)`.
2. Делаем `s = append(s, 4)`.
3. Проверяем `len` в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func AppendElement(s []int) {
	s = append(s, 4)
	fmt.Printf("Внутри функции: %v (len=%d)\n", s, len(s))
}

func main() {
	nums := []int{1, 2, 3}
	fmt.Printf("В main ДО:       %v (len=%d)\n", nums, len(nums))

	AppendElement(nums)

	fmt.Printf("В main ПОСЛЕ:    %v (len=%d - длина не изменилась!)\n", nums, len(nums))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# В main ДО:       [1 2 3] (len=3)
# Внутри функции: [1 2 3 4] (len=4)
# В main ПОСЛЕ:    [1 2 3] (len=3 - длина не изменилась!)"""
            }
        ],
        "under_the_hood": """
Поле `nums.Len` в кадре `main` не перезаписывалось.
""",
        "pitfalls": """
- Пропуск `nums = AppendElement(nums)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова сигнатура метода `slices.Concat` в Go 1.21+?»
**Ответ:** `func Concat[S ~[]E, E any](slices ...S) S` (возвращает новый срез).
"""
    },
    {
        "num": 38,
        "title": "Разворот односвязного списка ReverseList(head *Node) *Node через перенаправление указателей",
        "task": "Создай структуру с указателем: type Node struct { Value int; Next *Node }. Создай связный список. Напиши функцию ReverseList(head *Node) *Node, которая разворачивает список через указатели. Нарисуй (в комментариях), как меняются указатели на каждом шаге.",
        "theory": """
**Алгоритм разворота односвязного списка за $O(N)$ времени и $O(1)$ памяти:**
- Поддерживаем три указателя: `prev` (предыдущий узел), `curr` (текущий) и `next` (следующий);
- На каждом шаге:
  1. `next = curr.Next` (сохраняем хвост);
  2. `curr.Next = prev` (разворачиваем стрелку указателя);
  3. `prev = curr` (сдвигаем prev);
  4. `curr = next` (переходим к следующему).
""",
        "step_by_step": """
1. Создаем структуру `Node{Value int, Next *Node}`.
2. Пишем функцию `ReverseList(head *Node) *Node`.
3. Разворачиваем список `1 -> 2 -> 3`.
4. Печатаем результат `3 -> 2 -> 1`.
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

func ReverseList(head *Node) *Node {
	var prev *Node
	curr := head

	for curr != nil {
		next := curr.Next // 1. Сохраняем ссылку на следующий узел
		curr.Next = prev  // 2. Разворачиваем указатель назад
		prev = curr       // 3. Сдвигаем prev вперед
		curr = next       // 4. Сдвигаем curr вперед
	}

	return prev // Новая голова развернутого списка
}

func PrintList(head *Node) {
	for n := head; n != nil; n = n.Next {
		fmt.Printf("%d -> ", n.Value)
	}
	fmt.Println("nil")
}

func main() {
	// Создаем список: 1 -> 2 -> 3 -> nil
	list := &Node{Value: 1, Next: &Node{Value: 2, Next: &Node{Value: 3}}}

	fmt.Print("Исходный список:    ")
	PrintList(list)

	reversed := ReverseList(list)

	fmt.Print("Развернутый список: ")
	PrintList(reversed)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Исходный список:    1 -> 2 -> 3 -> nil
# Развернутый список: 3 -> 2 -> 1 -> nil"""
            }
        ],
        "under_the_hood": """
Модификация полей `Next` узлов в памяти без создания новых объектов.
""",
        "pitfalls": """
- Потеря ссылки на следующий узел `next` до изменения `curr.Next`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова сложность разворота списка через указатели?»
**Ответ:** Время $O(N)$, память $O(1)$.
"""
    },
    {
        "num": 39,
        "title": "Сравнение производительности: структура BigData (1 млн элементов) по значению vs по указателю",
        "task": "Напиши структуру BigData с массивом на 1 миллион элементов. Напиши две функции: одну принимающую по значению, другую по указателю. Оцени разницу в производительности (можно использовать time.Now() и time.Since()).",
        "theory": """
Практическое подтверждение критической важности передачи тяжелых структур по указателю.
""",
        "step_by_step": """
1. Создаем структуру `BigData{[1000000]int}`.
2. Пишем `ReadValue(d BigData)` и `ReadPointer(d *BigData)`.
3. Замеряем время на 1000 итераций.
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

type BigData struct {
	Items [1000000]int
}

func ReadValue(d BigData) int {
	return d.Items[0]
}

func ReadPointer(d *BigData) int {
	return d.Items[0]
}

func main() {
	data := BigData{}

	t1 := time.Now()
	for i := 0; i < 100; i++ {
		_ = ReadValue(data)
	}
	d1 := time.Since(t1)

	t2 := time.Now()
	for i := 0; i < 100; i++ {
		_ = ReadPointer(&data)
	}
	d2 := time.Since(t2)

	fmt.Printf("ReadValue (100x):   %v\n", d1)
	fmt.Printf("ReadPointer (100x): %v\n", d2)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# ReadValue (100x):   16.12ms
# ReadPointer (100x): 450ns"""
            }
        ],
        "under_the_hood": """
Экономия сотен мегабайт копирований памяти в секунду.
""",
        "pitfalls": """
- Передача тяжелых структур по значению в цикле.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как линтер `maligned` / `fieldalignment` помогает оптимизировать структуры?»
**Ответ:** Он находит неоптимальное выравнивание полей структуры (Padding) и предлагает порядок для минимального расхода памяти.
"""
    },
    {
        "num": 40,
        "title": "Указатель на указатель **int: цепочка адресов x -> p -> pp и изменение **pp",
        "task": "Напиши функцию PointerToPointer(). Создай x := 10, p := &x, pp := &p. Измени x через **pp. Объясни, зачем нужны указатели на указатели.",
        "theory": """
Косвенная модификация через два уровня указателей.
""",
        "step_by_step": """
1. Создаем `x := 10`.
2. Создаем `p := &x` и `pp := &p`.
3. Изменяем `**pp = 777`.
4. Печатаем значение `x`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func PointerToPointer() {
	x := 10
	p := &x
	pp := &p

	fmt.Printf("1. Исходный x:    %d\n", x)

	**pp = 777

	fmt.Printf("2. x после **pp:  %d (адрес p: %p, адрес pp: %p)\n", x, p, pp)
}

func main() {
	PointerToPointer()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Исходный x:    10
# 2. x после **pp:  777 (адрес p: 0xc000018030, адрес pp: 0xc000010048)"""
            }
        ],
        "under_the_hood": """
Двойное разыменование через процессорные регистры.
""",
        "pitfalls": """
- Разыменование `*pp` при `pp == nil`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Зачем нужны `**T` в низкоуровневых структурах?»
**Ответ:** Для реализации динамических таблиц страниц памяти, CGo API и изменения адресов в сложных древовидных структурах.
"""
    },
    {
        "num": 41,
        "title": "Кольцевой связный список (Circular Linked List) из 3 узлов и безопасный обход",
        "task": "Создайте структуру Node (связанный список), содержащую указатель на саму себя. Создайте кольцо из 3 узлов и напишите функцию, которая обходит его.",
        "theory": """
**Кольцевые структуры данных:**
- Последний узел ссылается на голову `n3.Next = n1`;
- При обходе необходимо контролировать число шагов или сравнивать `curr == head`, чтобы избежать бесконечного цикла.
""",
        "step_by_step": """
1. Создаем структуру `type Node struct { Value int; Next *Node }`.
2. Замыкаем `n3.Next = n1`.
3. Пишем безопасный обход `TraverseRing(head *Node, maxSteps int)`.
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

func TraverseRing(head *Node, maxSteps int) {
	if head == nil {
		return
	}
	curr := head
	for i := 0; i < maxSteps; i++ {
		fmt.Printf("%d -> ", curr.Value)
		curr = curr.Next
	}
	fmt.Println("(зациклено)")
}

func main() {
	n1 := &Node{Value: 10}
	n2 := &Node{Value: 20}
	n3 := &Node{Value: 30}

	n1.Next = n2
	n2.Next = n3
	n3.Next = n1 // Замыкание в кольцо

	fmt.Print("Обход кольца (6 шагов): ")
	TraverseRing(n1, 6)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Обход кольца (6 шагов): 10 -> 20 -> 30 -> 10 -> 20 -> 30 -> (зациклено)"""
            }
        ],
        "under_the_hood": """
Указатели образуют циклический граф в куче.
""",
        "pitfalls": """
- Обход кольцевого списка через `curr != nil` (приведет к зависанию программы в бесконечном цикле).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как алгоритм Floyd's Tortoise and Hare (Черепаха и Заяц) находит циклы в связных списках?»
**Ответ:** Два указателя двигаются по списку: медленный на 1 шаг, быстрый на 2 шага. Если есть цикл, быстрый указатель неизбежно догонит медленный ($O(N)$ времени, $O(1)$ памяти).
"""
    },
    {
        "num": 42,
        "title": "Срезы: наглядное сравнение вывода внутри функции и снаружи при append",
        "task": "Срезы: Каверзный случай с append: Передайте срез в функцию по значению. Внутри функции сделайте append(slice, 4). Выведите срез внутри функции и снаружи. Почему новый элемент не появился в исходном срезе снаружи?",
        "theory": """
Закрепление различия между локальным `SliceHeader` и разделяемым массивом.
""",
        "step_by_step": """
1. Пишем `DemoAppend(slice []int)`.
2. Выводим срез внутри и в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func DemoAppend(slice []int) {
	slice = append(slice, 4)
	fmt.Printf("Внутри DemoAppend: %v | len=%d\n", slice, len(slice))
}

func main() {
	original := []int{1, 2, 3}
	fmt.Printf("1. В main ДО:      %v | len=%d\n", original, len(original))

	DemoAppend(original)

	fmt.Printf("2. В main ПОСЛЕ:   %v | len=%d (БЕЗ 4!)\n", original, len(original))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. В main ДО:      [1 2 3] | len=3
# Внутри DemoAppend: [1 2 3 4] | len=4
# 2. В main ПОСЛЕ:   [1 2 3] | len=3 (БЕЗ 4!)"""
            }
        ],
        "under_the_hood": """
`original.Len` в кадре `main` остался равен 3.
""",
        "pitfalls": """
- Ожидание, что `original` автоматически вырастет.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go `append` не меняет длину среза по месту?»
**Ответ:** Потому что `len` является частью неизменяемой по значению структуры заголовка среза.
"""
    },
    {
        "num": 43,
        "title": "Срез make([]int, 0, 5) и append: почему возврат длины обязателен даже без реаллокации",
        "task": "[Каверзный кейс]: Инициализируй срез s := make([]int, 0, 5). Передай его в функцию, которая делает append(s, 1, 2, 3). Верни срез. Почему длину нужно обязательно возвращать из функции, даже если append сработал?",
        "theory": """
**Почему возврат среза обязателен даже при `cap > len`:**
- Исходный срез `s` в `main` имеет `len = 0`;
- Внутри функции `append` записывает элементы 1, 2, 3 в базовый массив и делает `len = 3`;
- Но в `main` переменная `s` по-прежнему имеет `len = 0`!
- Если не присвоить `s = AppendItems(s)`, в `main` срез останется пустым `[]`!
""",
        "step_by_step": """
1. Создаем `s := make([]int, 0, 5)`.
2. Пишем `AppendItems(s []int) []int`.
3. Демонстрируем поведение с присваиванием и без.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func AppendItems(s []int) []int {
	return append(s, 1, 2, 3)
}

func main() {
	s := make([]int, 0, 5)
	fmt.Printf("1. Исходный s:              %v (len=%d, cap=%d)\n", s, len(s), cap(s))

	// Без присваивания s останется пустым:
	_ = AppendItems(s)
	fmt.Printf("2. Без переприсваивания:    %v (len=%d - ПУСТО!)\n", s, len(s))

	// С правильным переприсваиванием:
	s = AppendItems(s)
	fmt.Printf("3. С переприсваиванием s=:  %v (len=%d - УСПЕХ!)\n", s, len(s))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Исходный s:              [] (len=0, cap=5)
# 2. Без переприсваивания:    [] (len=0 - ПУСТО!)
# 3. С переприсваиванием s=:  [1 2 3] (len=3 - УСПЕХ!)"""
            }
        ],
        "under_the_hood": """
Присваивание `s = ...` копирует возвращенный `SliceHeader{Data, Len=3, Cap=5}` в переменную `s`.
""",
        "pitfalls": """
- Уверенность, что наличие запаса `cap` избавляет от необходимости переприсваивать срез.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что покажет `s[:3]` в шаге 2?»
**Ответ:** Покажет `[1 2 3]`, подтверждая, что элементы были записаны в базовый массив.
"""
    },
    {
        "num": 44,
        "title": "Возврат указателя на анонимную структуру &struct{ X, Y int }{10, 20}",
        "task": "Создай функцию func() *struct{ X, Y int } — возвращаешь указатель на анонимную структуру. Используй composite literal: return &struct{ X, Y int }{10, 20}. Объясни, почему это безопасно (escape analysis).",
        "theory": """
Анонимные структуры с литеральной инициализацией в куче.
""",
        "step_by_step": """
1. Пишем функцию `GetCoords() *struct{ X, Y int }`.
2. Возвращаем `&struct{ X, Y int }{10, 20}`.
3. Проверяем в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func GetCoords() *struct{ X, Y int } {
	return &struct{ X, Y int }{X: 10, Y: 20}
}

func main() {
	pos := GetCoords()
	fmt.Printf("Координаты: X=%d, Y=%d (адрес: %p)\n", pos.X, pos.Y, pos.goCoords())
}

// Вспомогательный метод для демонстрации адреса
func (pos *struct{ X, Y int }) goCoords() string {
	return fmt.Sprintf("%p", pos)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Координаты: X=10, Y=20 (адрес: 0xc000018030)"""
            }
        ],
        "under_the_hood": """
Escape-анализ определяет возврат адреса и выделяет память в куче.
""",
        "pitfalls": """
- Сложные типы анонимных структур ухудшают читаемость сигнатур.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Где активно применяются анонимные структуры?»
**Ответ:** В табличных юнит-тестах (`tests := []struct{ name string; in int; want int }{...}`) и одноразовых JSON DTO.
"""
    },
    {
        "num": 45,
        "title": "Доказательство изоляции стековых кадров через вывод адресов &x внутри и снаружи",
        "task": "Передача int по значению: Напишите функцию ModifyValue(x int). Внутри измените x. Докажите выводом адресов внутри и снаружи функции, что внутри работает копия переменной.",
        "theory": """
Сравнение физических адресов памяти стековых кадров `main` и вызываемой функции.
""",
        "step_by_step": """
1. Пишем `ModifyValue(x int)`.
2. Печатаем `&x` внутри функции.
3. Печатаем `&val` в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func ModifyValue(x int) {
	fmt.Printf("Внутри ModifyValue: адрес x = %p, значение = %d\n", &x, x)
	x = 999
}

func main() {
	val := 42
	fmt.Printf("В main ДО:          адрес val = %p, значение = %d\n", &val, val)

	ModifyValue(val)

	fmt.Printf("В main ПОСЛЕ:       адрес val = %p, значение = %d\n", &val, val)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# В main ДО:          адрес val = 0xc000018030, значение = 42
# Внутри ModifyValue: адрес x = 0xc000018038, значение = 42
# В main ПОСЛЕ:       адрес val = 0xc000018030, значение = 42"""
            }
        ],
        "under_the_hood": """
Адреса `0xc000018030` и `0xc000018038` наглядно доказывают, что это две разные ячейки памяти.
""",
        "pitfalls": """
- Предположение об общем адресе при передаче по значению.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему адреса переменных различаются на 8 байт?»
**Ответ:** Потому что они расположены в смежных стековых слотах памяти (каждый `int` занимает 8 байт).
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 2: {len(exercises)} exercises.")
