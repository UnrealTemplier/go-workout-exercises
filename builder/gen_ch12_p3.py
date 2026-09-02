# Chapter 12 Part 3: Exercises 46 to 67

exercises = [
    {
        "num": 46,
        "title": "Передача объектов через интерфейс: упаковка значения vs упаковка указателя",
        "task": "Создай интерфейс Stringer. Передай объект, реализующий интерфейс, в функцию. Имитируй передачу \"по ссылке\" через интерфейс (если под капотом указатель — мутации видны).",
        "theory": """
**Поведение интерфейсов при упаковке (Interface Boxing):**
- Если в интерфейс передан указатель `&User{}`, метод интерфейса оперирует оригинальным объектом в куче;
- Если передано значение `User{}`, интерфейс упаковывает копию.
""",
        "step_by_step": """
1. Создаем интерфейс `type Describable interface { Describe() string }`.
2. Создаем структуру `type Article struct { Title string }`.
3. Реализуем метод `(a *Article) Describe() string`.
4. Демонстрируем вызов через интерфейс.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Describable interface {
	Describe() string
}

type Article struct {
	Title string
}

func (a *Article) Describe() string {
	return "Статья: " + a.Title
}

func PrintDescription(d Describable) {
	fmt.Println(d.Describe())
}

func main() {
	art := &Article{Title: "Модель памяти Go"}
	PrintDescription(art)

	// Модифицируем объект через исходный указатель:
	art.Title = "Высоконагруженный бэкенд на Go"
	PrintDescription(art)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Статья: Модель памяти Go
# Статья: Высоконагруженный бэкенд на Go"""
            }
        ],
        "under_the_hood": """
Интерфейс хранит 8-байтный указатель на структуру `Article` в куче.
""",
        "pitfalls": """
- Попытка передать неадресуемое значение, когда методы объявлены с pointer receiver.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go говорят: 'Не создавайте интерфейсы заранее, пока нет 2+ реализаций'?»
**Ответ:** Преждевременная абстракция интерфейсами ухудшает читаемость и лишает компилятор возможности инлайнинга прямых вызовов функций.
"""
    },
    {
        "num": 47,
        "title": "Отсутствие висячих указателей (Dangling Pointers) в Go благодаря Escape-анализу",
        "task": "Напиши программу с \"dangling pointer\": создай указатель внутри функции на локальную переменную, верни его. Покажи, что Go НЕ допускает dangling pointers (escape analysis выделяет на куче). Затем сымитируй проблему через unsafe.Pointer (только для понимания, не используй в продакшене!).",
        "theory": """
**Безопасность памяти компилятора Go:**
- В C возврат `return &local` приводит к использованию освобожденного стека (Use-After-Free / Dangling Pointer);
- В Go компилятор гарантирует, что любая переменная, чей адрес возвращается, **автоматически перемещается в кучу**;
- Висячие указатели в стандартном безопасном Go невозможны!
""",
        "step_by_step": """
1. Пишем `CreateSafeNumber() *int`.
2. Возвращаем `&val`.
3. Убеждаемся в валидности значения в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func CreateSafeNumber() *int {
	val := 12345
	// В Go это НЕ висячий указатель, так как val переносится в кучу:
	return &val
}

func main() {
	p := CreateSafeNumber()
	fmt.Printf("Значение цело и невредимо: %d (адрес: %p)\n", *p, p)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Значение цело и невредимо: 12345 (адрес: 0xc000018030)"""
            }
        ],
        "under_the_hood": """
Сборщик мусора отслеживает указатель `p` в корневом наборе (Root Set) и не освобождает память.
""",
        "pitfalls": """
- Использование хаков с `uintptr` и `unsafe.Pointer`, нарушающих правила сборщика мусора.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `uintptr` нельзя хранить между вызовами, преобразуя в `unsafe.Pointer`?»
**Ответ:** Потому что `uintptr` — это обычное число, а не указатель. GC не видит ссылку на объект, может переместить или удалить его из кучи, что приведет к реальному Dangling Pointer.
"""
    },
    {
        "num": 48,
        "title": "Передача мапы map[string]int: почему мапа под капотом является указателем *hmap",
        "task": "Отображения (Maps): Передача по значению: Передайте мапу map[string]int в функцию по значению. Внутри функции добавьте новый ключ или измените существующий. Изменилась ли мапа снаружи? (Изучите, почему мапа в Go является указателем на структуру hmap под капотом).",
        "theory": """
Анализ передачи указателя `*hmap` по значению.
""",
        "step_by_step": """
1. Пишем `SetFlag(m map[string]int, key string)`.
2. Передаем мапу.
3. Проверяем в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func SetFlag(m map[string]int, key string) {
	m[key] = 1 // Запись в бакеты разделяемой hmap
}

func main() {
	flags := map[string]int{"debug": 0}
	fmt.Printf("До:    %v\n", flags)

	SetFlag(flags, "feature_x")

	fmt.Printf("После: %v (ФЛАГ ДОБАВЛЕН!)\n", flags)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До:    map[debug:0]
# После: map[debug:0 feature_x:1] (ФЛАГ ДОБАВЛЕН!)"""
            }
        ],
        "under_the_hood": """
Хэш-функция AES/Memhash вычисляет бакет внутри разделяемой структуры `hmap`.
""",
        "pitfalls": """
- Запись в неинициализированную `var m map[string]int` (паника).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что происходит с `hmap` при добавлении элементов?»
**Ответ:** Поле `count` инкрементируется, при Load Factor $> 6.5$ выделяется вдвое больше бакетов и начинается постепенная эвакуация данных.
"""
    },
    {
        "num": 49,
        "title": "Классический Swap(a, b *int) и атомарный обмен в регистрах CPU",
        "task": "Напиши функцию Swap(a, b *int), которая меняет значения двух переменных местами.",
        "theory": """
Обмен значений по указателям.
""",
        "step_by_step": """
1. Пишем `Swap(a, b *int)`.
2. Выполняем `*a, *b = *b, *a`.
3. Проверяем переменные.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Swap(a, b *int) {
	if a != nil && b != nil {
		*a, *b = *b, *a
	}
}

func main() {
	x, y := 10, 99
	fmt.Printf("До Swap:    x=%d, y=%d\n", x, y)

	Swap(&x, &y)

	fmt.Printf("После Swap: x=%d, y=%d\n", x, y)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До Swap:    x=10, y=99
# После Swap: x=99, y=10"""
            }
        ],
        "under_the_hood": """
Инструкции `MOVQ` через регистры CPU.
""",
        "pitfalls": """
- Передача `nil`-указателя.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как поменять два значения без третьей переменной и кортежа?»
**Ответ:** Через побитовое XOR: `*a ^= *b; *b ^= *a; *a ^= *b`.
"""
    },
    {
        "num": 50,
        "title": "Указатель на срез *[]int: гарантированное обновление заголовка SliceHeader даже при реаллокации",
        "task": "Напишите функцию, принимающую *[]int (указатель на слайс). Реализуйте добавление элемента так, чтобы оригинальный слайс гарантированно обновился даже при реаллокации базового массива.",
        "theory": """
**Гарантированное обновление среза через `*[]T`:**
- Синтаксис `*s = append(*s, val)` перезаписывает `SliceHeader` вызывающего стекового кадра;
- Даже если произошла реаллокация и выделился новый базовый массив, вызывающий код гарантированно получит новый указатель `Data`, `Len` и `Cap`.
""",
        "step_by_step": """
1. Пишем `SafeAppend(s *[]int, val int)`.
2. Выполняем `*s = append(*s, val)`.
3. Тестируем со срезом `cap == len`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func SafeAppend(s *[]int, val int) {
	if s == nil {
		return
	}
	*s = append(*s, val) // Гарантированно обновляет SliceHeader в main!
}

func main() {
	data := []int{1, 2} // len=2, cap=2
	fmt.Printf("1. До:    %v | len=%d, cap=%d (адрес массива: %p)\n",
		data, len(data), cap(data), data)

	SafeAppend(&data, 3)

	fmt.Printf("2. После: %v | len=%d, cap=%d (адрес массива: %p - УСПЕХ!)\n",
		data, len(data), cap(data), data)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. До:    [1 2] | len=2, cap=2 (адрес массива: 0xc000018030)
# 2. После: [1 2 3] | len=3, cap=4 (адрес массива: 0xc00001e040 - УСПЕХ!)"""
            }
        ],
        "under_the_hood": """
Функция модифицирует стековый слот `data` в кадре `main`.
""",
        "pitfalls": """
- Передача `SafeAppend(nil, 5)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Когда в промышленном Go оправдано использование `*[]T`?»
**Ответ:** При реализации низкоуровневых байтовых буферов (например `bytes.Buffer`, кодеков и кастомных аллокаторов памяти).
"""
    },
    {
        "num": 51,
        "title": "Копирование больших структур (10 полей): сравнение адресов при передаче по значению и по указателю",
        "task": "Копирование структур: Создайте структуру большого размера (например, с 10 полями). Напишите функцию, принимающую её по значению, и функцию, принимающую её по указателю. Выведите адреса структуры в обоих случаях.",
        "theory": """
Инспекция адресов памяти при передаче структур.
""",
        "step_by_step": """
1. Создаем структуру с 10 полями `HeavyReport`.
2. Пишем `InspectValue(r HeavyReport)` и `InspectPointer(r *HeavyReport)`.
3. Сравниваем адреса с оригиналом.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type HeavyReport struct {
	F1, F2, F3, F4, F5, F6, F7, F8, F9, F10 int
}

func InspectValue(r HeavyReport) {
	fmt.Printf("  Внутри InspectValue:   адрес = %p (НОВЫЙ АДРЕС В СТЕКЕ!)\n", &r)
}

func InspectPointer(r *HeavyReport) {
	fmt.Printf("  Внутри InspectPointer: адрес = %p (ТОТ ЖЕ САМЫЙ АДРЕС!)\n", r)
}

func main() {
	rep := HeavyReport{F1: 1, F10: 10}
	fmt.Printf("1. Адрес rep в main:     адрес = %p\n", &rep)

	InspectValue(rep)
	InspectPointer(&rep)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Адрес rep в main:     адрес = 0xc00006e050
#   Внутри InspectValue:   адрес = 0xc00006e0a0 (НОВЫЙ АДРЕС В СТЕКЕ!)
#   Внутри InspectPointer: адрес = 0xc00006e050 (ТОТ ЖЕ САМЫЙ АДРЕС!)"""
            }
        ],
        "under_the_hood": """
`InspectValue` копирует 80 байт в локальный стек функции.
""",
        "pitfalls": """
- Передача тяжелых структур по значению в цикле.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каков размер структуры `HeavyReport`?»
**Ответ:** $10 \times 8 = 80$ байт.
"""
    },
    {
        "num": 52,
        "title": "Передача головы связного списка Node в функцию и последовательный обход",
        "task": "Создай структуру Node с полем Next *Node. Построй связный список из 3 элементов. Передай голову списка в функцию и пройдись по нему.",
        "theory": """
Передача корневого указателя динамической цепочки узлов.
""",
        "step_by_step": """
1. Создаем структуру `Node{Value int, Next *Node}`.
2. Пишем функцию `Traverse(head *Node)`.
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

func Traverse(head *Node) {
	curr := head
	for curr != nil {
		fmt.Printf("[%d] -> ", curr.Value)
		curr = curr.Next
	}
	fmt.Println("nil")
}

func main() {
	head := &Node{Value: 10, Next: &Node{Value: 20, Next: &Node{Value: 30}}}
	fmt.Print("Связный список: ")
	Traverse(head)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Связный список: [10] -> [20] -> [30] -> nil"""
            }
        ],
        "under_the_hood": """
Обход указателей по адресам в куче.
""",
        "pitfalls": """
- Передача зацикленного списка без проверки шагов.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как удалить узел из середины списка за $O(1)$?»
**Ответ:** Перенаправить указатель: `prev.Next = curr.Next`.
"""
    },
    {
        "num": 53,
        "title": "Инкапсуляция неэкспортируемых полей структуры и доступ через экспортированные методы (Setters)",
        "task": "Создайте структуру с приватными (неэкспортируемыми) полями. Попробуйте передать её по указателю в другой пакет и изменить поля. (Убедитесь, что компилятор выдаст ошибку).",
        "theory": """
**Правила экспорта и инкапсуляции в Go:**
- Поля с маленькой буквы (`balance int`) недоступны за пределами пакета;
- Доступ для мутаций предоставляется исключительно через экспортированные методы (`Deposit`, `Withdraw`).
""",
        "step_by_step": """
1. Создаем структуру с приватным полем `balance int`.
2. Пишем публичный метод `(a *Account) Deposit(amount int)`.
3. Демонстрируем безопасную модификацию.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type BankAccount struct {
	owner   string // Приватное поле
	balance int    // Приватное поле
}

func NewBankAccount(owner string, initialBalance int) *BankAccount {
	return &BankAccount{owner: owner, balance: initialBalance}
}

func (b *BankAccount) Deposit(amount int) {
	if amount > 0 {
		b.balance += amount
	}
}

func (b *BankAccount) Balance() int {
	return b.balance
}

func main() {
	acc := NewBankAccount("Алексей", 1000)
	fmt.Printf("Баланс до:    %d руб.\n", acc.Balance())

	acc.Deposit(500)

	fmt.Printf("Баланс после: %d руб.\n", acc.Balance())
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Баланс до:    1000 руб.
# Баланс после: 1500 руб."""
            }
        ],
        "under_the_hood": """
Компилятор статически проверяет область видимости идентификаторов на этапе компиляции.
""",
        "pitfalls": """
- Попытка доступа `acc.balance` из внешнего пакета (ошибка компиляции `cannot refer to unexported field`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли изменить неэкспортируемое поле из другого пакета?»
**Ответ:** Только через небезопасный пакет `unsafe` (с вычислением смещения поля) или рефлексию (с `reflect.Value`). В продакшене это строжайше запрещено.
"""
    },
    {
        "num": 54,
        "title": "Функция SendToChannel(ch chan int, val int): отправка данных в канал",
        "task": "Напиши функцию, которая принимает канал chan int (каналы тоже передаются по ссылке, то есть указателю на структуру канала). Отправь в него число.",
        "theory": """
Передача каналов в сигнатурах функций.
""",
        "step_by_step": """
1. Пишем `SendToChannel(ch chan<- int, val int)`.
2. Передаем канал и отправляем число.
3. Читаем результат.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func SendToChannel(ch chan<- int, val int) {
	ch <- val // Отправка в разделяемый буфер канала
}

func main() {
	ch := make(chan int, 1)
	SendToChannel(ch, 42)

	received := <-ch
	fmt.Printf("Успешно получено: %d\n", received)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Успешно получено: 42"""
            }
        ],
        "under_the_hood": """
`runtime.chansend` блокирует или помещает элемент в кольцевой буфер `hchan.buf`.
""",
        "pitfalls": """
- Отправка в закрытый канал (паника `send on closed channel`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в аргументах лучше указывать направленные каналы `chan<- T` или `<-chan T`?»
**Ответ:** Это повышает безопасность типов (Type Safety), предотвращая случайное закрытие или чтение из канала там, где разрешена только запись.
"""
    },
    {
        "num": 55,
        "title": "Каверзный кейс срезов: передача по значению и мутация s[0] = 99",
        "task": "Каверзный случай: Срезы (Slices): Создай срез s := []int{1, 2, 3}. Передай его в функцию по значению (без *). Внутри функции измени первый элемент (s[0] = 99). Убедись, что в main элемент *тоже изменился*, хотя срез передавался по значению. (Объяснение: срез сам по себе содержит неявно указатель на базовый массив).",
        "theory": """
Глубокое закрепление дуализма срезов: заголовок по значению, данные по ссылке.
""",
        "step_by_step": """
1. Создаем срез `s := []int{1, 2, 3}`.
2. Пишем `MutateFirst(s []int)`.
3. Проверяем в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func MutateFirst(s []int) {
	if len(s) > 0 {
		s[0] = 99
	}
}

func main() {
	s := []int{1, 2, 3}
	fmt.Printf("До:    %v\n", s)

	MutateFirst(s)

	fmt.Printf("После: %v (s[0] ИЗМЕНИЛСЯ НА 99!)\n", s)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До:    [1 2 3]
# После: [99 2 3] (s[0] ИЗМЕНИЛСЯ НА 99!)"""
            }
        ],
        "under_the_hood": """
Прямая запись по указателю `s.Data`.
""",
        "pitfalls": """
- Неожиданная мутация срезов при передаче в сторонние функции.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как защитить срез от мутаций при передаче в функцию?»
**Ответ:** Передавать клонированную копию через `slices.Clone(s)` или копировать в локальный срез `copy()`.
"""
    },
    {
        "num": 56,
        "title": "Безопасный банковский перевод Transfer(from, to *Account, amount int) error с валидацией баланса",
        "task": "[Высокая сложность]: Напиши структуру Account с полем balance int. Реализуй безопасную функцию перевода денег между двумя счетами, передавая их по указателю, и обработай ситуацию нехватки средств (return error).",
        "theory": """
**Паттерн транзакционной бизнес-логики:**
- Передача счетов по указателю `*Account`;
- Проверка инвариантов: ненулевые указатели, положительная сумма, достаточный баланс;
- Возврат идиоматичной ошибки при нарушении условий.
""",
        "step_by_step": """
1. Создаем структуру `type Account struct { ID string; Balance int }`.
2. Пишем функцию `Transfer(from, to *Account, amount int) error`.
3. Тестируем успешный перевод и ошибку нехватки средств.
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
	ID      string
	Balance int
}

func Transfer(from, to *Account, amount int) error {
	if from == nil || to == nil {
		return errors.New("счет отправителя или получателя равен nil")
	}
	if amount <= 0 {
		return errors.New("сумма перевода должна быть положительной")
	}
	if from.Balance < amount {
		return fmt.Errorf("недостаточно средств: баланс %d, требуется %d", from.Balance, amount)
	}

	from.Balance -= amount
	to.Balance += amount
	return nil
}

func main() {
	accA := &Account{ID: "ACC-101", Balance: 500}
	accB := &Account{ID: "ACC-202", Balance: 100}

	fmt.Printf("До перевода:  A=%d, B=%d\n", accA.Balance, accB.Balance)

	if err := Transfer(accA, accB, 300); err != nil {
		fmt.Printf("Ошибка: %v\n", err)
	} else {
		fmt.Printf("После 300р:   A=%d, B=%d (УСПЕХ!)\n", accA.Balance, accB.Balance)
	}

	if err := Transfer(accA, accB, 9999); err != nil {
		fmt.Printf("После 9999р:  Ошибка перевода -> %v\n", err)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До перевода:  A=500, B=100
# После 300р:   A=200, B=400 (УСПЕХ!)
# После 9999р:  Ошибка перевода -> недостаточно средств: баланс 200, требуется 9999"""
            }
        ],
        "under_the_hood": """
Мутация полей `Balance` напрямую в объектах кучи.
""",
        "pitfalls": """
- В многопоточной среде требуется синхронизация мьютексами (с сортировкой ID счетов для предотвращения Deadlock!).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как предотвратить Deadlock при переводе между двумя аккаунтами с мьютексами `from.mu.Lock()` и `to.mu.Lock()`?»
**Ответ:** Всегда захватывать мьютексы в детерминированном порядке (например, сортируя по ID счета: сначала лочить счет с меньшим ID, затем с большим).
"""
    },
    {
        "num": 57,
        "title": "Функция AppendWithPointer(slice *[]int, val int) и обновление емкости снаружи",
        "task": "Передача среза по указателю: Напишите функцию AppendWithPointer(slice *[]int, val int). Передайте туда срез по указателю и примените append. Убедитесь, что теперь изменения (размер и емкость) отразились снаружи.",
        "theory": """
Мутация среза через разыменование указателя на заголовок.
""",
        "step_by_step": """
1. Пишем `AppendWithPointer(slice *[]int, val int)`.
2. Вызываем `*slice = append(*slice, val)`.
3. Тестируем.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func AppendWithPointer(slice *[]int, val int) {
	if slice != nil {
		*slice = append(*slice, val)
	}
}

func main() {
	var nums []int
	AppendWithPointer(&nums, 100)
	AppendWithPointer(&nums, 200)

	fmt.Printf("nums: %v (len=%d, cap=%d)\n", nums, len(nums), cap(nums))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# nums: [100 200] (len=2, cap=2)"""
            }
        ],
        "under_the_hood": """
Прямая перезапись стекового слота.
""",
        "pitfalls": """
- Передача `nil`-указателя.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем недостаток `AppendWithPointer`?»
**Ответ:** Нарушение принципа чистых функций и менее очевидный поток данных.
"""
    },
    {
        "num": 58,
        "title": "Правильный append через указатель *s = append(*s, 4) в оригинале",
        "task": "Правильный Append через функцию: Чтобы append сработал на оригинале, перепиши функцию из упр. 88, передавая указатель на срез *[]int, и выполни *s = append(*s, 4).",
        "theory": """
Закрепление паттерна `*s = append(*s, ...)`.
""",
        "step_by_step": """
1. Пишем `AppendFour(s *[]int)`.
2. Вызываем с адресом `&slice`.
3. Проверяем в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func AppendFour(s *[]int) {
	if s != nil {
		*s = append(*s, 4)
	}
}

func main() {
	s := []int{1, 2, 3}
	AppendFour(&s)
	fmt.Printf("Результат: %v (len=%d)\n", s, len(s))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Результат: [1 2 3 4] (len=4)"""
            }
        ],
        "under_the_hood": """
Обновление заголовка среза.
""",
        "pitfalls": """
- Забыть знак `*` перед `s`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какой тип имеет `&s`?»
**Ответ:** `*[]int`.
"""
    },
    {
        "num": 59,
        "title": "Мапы: попытка обнуления m = nil или m = make(...) внутри функции и неизменность оригинала",
        "task": "Мапы: Попытка обнуления: Передайте мапу в функцию по значению. Внутри функции присвойте ей nil или создайте новую мапу через make. Изменится ли исходная мапа снаружи?",
        "theory": """
**Почему переприсваивание мапы `m = nil` не влияет на оригинал:**
- Параметр `m` — это **локальная копия указателя на `hmap`**;
- Присвоение `m = nil` или `m = make(...)` меняет только локальную переменную `m`;
- Исходная мапа в `main` продолжает указывать на старую структуру `hmap` в куче!
""",
        "step_by_step": """
1. Пишем функцию `TryToResetMap(m map[string]int)`.
2. Внутри делаем `m = nil` и `m = make(map[string]int)`.
3. Проверяем оригинал в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func TryToResetMap(m map[string]int) {
	m = nil // Перезаписывает только локальную переменную m!
	fmt.Printf("Внутри TryToResetMap: m = %v\n", m)
}

func main() {
	cache := map[string]int{"auth_token": 999}
	fmt.Printf("1. До:    %v\n", cache)

	TryToResetMap(cache)

	fmt.Printf("2. После: %v (ОРИГИНАЛЬНАЯ МАПА НЕ ИЗМЕНИЛАСЬ!)\n", cache)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. До:    map[auth_token:999]
# Внутри TryToResetMap: m = map[]
# 2. После: map[auth_token:999] (ОРИГИНАЛЬНАЯ МАПА НЕ ИЗМЕНИЛАСЬ!)"""
            }
        ],
        "under_the_hood": """
Локальный регистр `RAX` перезаписывается значением `0` (`nil`), не затрагивая переменную `cache`.
""",
        "pitfalls": """
- Попытка очистить мапу через `m = make(...)` внутри функции вместо вызова `clear(m)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как правильно очистить мапу от всех элементов внутри функции?»
**Ответ:** Использовать встроенную функцию `clear(m)` (начиная с Go 1.21) или передавать `*map[K]V`.
"""
    },
    {
        "num": 60,
        "title": "Каналы (Channels) как ссылочный тип: передача дескриптора по значению и чтение данных",
        "task": "Каналы (Channels) как ссылочный тип: Создайте канал. Передайте его в функцию по значению. Запишите данные в канал внутри функции, а прочитайте снаружи. Работает ли передача каналов по значению как передача ссылки?",
        "theory": """
Закрепление ссылочной природы каналов в Go.
""",
        "step_by_step": """
1. Создаем канал `ch := make(chan string, 1)`.
2. Пишем функцию `WriteMessage(ch chan string)`.
3. Читаем сообщение в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func WriteMessage(ch chan string) {
	ch <- "Сообщение успешно доставлено через канал!"
}

func main() {
	ch := make(chan string, 1)

	WriteMessage(ch)

	msg := <-ch
	fmt.Printf("Получено: %s\n", msg)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Получено: Сообщение успешно доставлено через канал!"""
            }
        ],
        "under_the_hood": """
Обе стороны обращаются к одному экземпляру `hchan` в куче.
""",
        "pitfalls": """
- Чтение из неинициализированного `var ch chan int` (вечная блокировка).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какие три встроенных типа в Go обладают ссылочным поведением по умолчанию?»
**Ответ:** Слайсы (частично), мапы (maps) и каналы (channels).
"""
    },
    {
        "num": 61,
        "title": "Массивы [3]int vs Срезы: глубокое копирование всего содержимого массива",
        "task": "Массивы (Arrays) vs Срезы: Создай массив [3]int (важно указать размер). Передай его в функцию по значению. Измени элемент. Убедись, что в массивах (в отличие от срезов) копируется *всё содержимое*, и оригинал не меняется.",
        "theory": """
Закрепление различия между массивом и срезом.
""",
        "step_by_step": """
1. Создаем массив `arr := [3]int{1, 2, 3}`.
2. Пишем `TryToMutateArray(arr [3]int)`.
3. Проверяем неизменность оригинала.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func TryToMutateArray(a [3]int) {
	a[0] = 999
}

func main() {
	arr := [3]int{1, 2, 3}
	fmt.Printf("До:    %v\n", arr)

	TryToMutateArray(arr)

	fmt.Printf("После: %v (ОРИГИНАЛ НЕ ИЗМЕНИЛСЯ!)\n", arr)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До:    [1 2 3]
# После: [1 2 3] (ОРИГИНАЛ НЕ ИЗМЕНИЛСЯ!)"""
            }
        ],
        "under_the_hood": """
Копирование 24 байт массива в стек.
""",
        "pitfalls": """
- Путаница между типом массива `[3]int` и типом среза `[]int`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как проверить, является ли тип массивом или срезом?»
**Ответ:** По наличию размера в скобках: `[3]int` — массив, `[]int` — срез.
"""
    },
    {
        "num": 62,
        "title": "Массивы фиксированной длины [5]int и иммутабельность оригинала при передаче",
        "task": "Массивы (Arrays) фиксированной длины: Создайте массив [5]int{1, 2, 3, 4, 5}. Передайте его в функцию по значению. Измените элемент внутри функции. Изменился ли массив снаружи? (Обратите внимание на ключевое отличие поведения массивов от срезов в Go).",
        "theory": """
Демонстрация полного копирования 40-байтного массива.
""",
        "step_by_step": """
1. Создаем `[5]int{1, 2, 3, 4, 5}`.
2. Пишем функцию `ZeroOutArray(a [5]int)`.
3. Проверяем результат.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func ZeroOutArray(a [5]int) {
	for i := range a {
		a[i] = 0
	}
}

func main() {
	numbers := [5]int{1, 2, 3, 4, 5}
	fmt.Printf("До вызова:    %v\n", numbers)

	ZeroOutArray(numbers)

	fmt.Printf("После вызова: %v (МАССИВ СОХРАНИЛ ВСЕ ЗНАЧЕНИЯ!)\n", numbers)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До вызова:    [1 2 3 4 5]
# После вызова: [1 2 3 4 5] (МАССИВ СОХРАНИЛ ВСЕ ЗНАЧЕНИЯ!)"""
            }
        ],
        "under_the_hood": """
40 байт данных копируются на стековый кадр функции.
""",
        "pitfalls": """
- Предположение, что массив изменится как срез.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go массивы сделаны значениями, а не ссылками как в Java/JS?»
**Ответ:** Для полного контроля над структурой памяти и кэш-локальностью процессора без скрытых аллокаций в куче.
"""
    },
    {
        "num": 63,
        "title": "Передача массива по указателю *[3]int: оптимизация вызовов без копирования",
        "task": "Передача массива по указателю: Передай массив *[3]int в функцию, чтобы избежать полного копирования данных и изменить оригинал.",
        "theory": """
Передача адреса массива `*[N]T`.
""",
        "step_by_step": """
1. Пишем `MutateArrayPtr(a *[3]int)`.
2. Присваиваем `a[0] = 777`.
3. Проверяем в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func MutateArrayPtr(a *[3]int) {
	if a != nil {
		a[0] = 777 // Компилятор Go автоматически разыменовывает (*a)[0]
	}
}

func main() {
	arr := [3]int{10, 20, 30}
	fmt.Printf("До:    %v\n", arr)

	MutateArrayPtr(&arr)

	fmt.Printf("После: %v (МУТАЦИЯ СОХРАНЕНА!)\n", arr)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До:    [10 20 30]
# После: [777 20 30] (МУТАЦИЯ СОХРАНЕНА!)"""
            }
        ],
        "under_the_hood": """
Передается 8-байтный адрес.
""",
        "pitfalls": """
- Попытка передать `*[3]int` туда, где ожидается `[]int`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как преобразовать массив в срез без аллокаций?»
**Ответ:** Слайсингом `s := arr[:]`.
"""
    },
    {
        "num": 64,
        "title": "Структура со срезом внутри Group{Members []string}: мутация разделяемого среза",
        "task": "Структура со срезом внутри: Создайте структуру Group, содержащую поле Members []string. Передайте экземпляр Group в функцию по значению. Измените элемент среза Members[0] = \"New\". Изменился ли этот элемент в исходной структуре снаружи?",
        "theory": """
Закрепление эффекта поверхностного копирования структуры со срезом.
""",
        "step_by_step": """
1. Создаем структуру `type Group struct { Title string; Members []string }`.
2. Пишем функцию `UpdateGroupMember(g Group)`.
3. Меняем `g.Members[0] = "New"`.
4. Анализируем результат в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Group struct {
	Title   string
	Members []string
}

func UpdateGroupMember(g Group) {
	g.Title = "Новое название" // Изменится только локально
	if len(g.Members) > 0 {
		g.Members[0] = "New" // Изменится в общем срезе!
	}
}

func main() {
	grp := Group{
		Title:   "Backend Team",
		Members: []string{"OldMember", "Alice", "Bob"},
	}

	fmt.Printf("1. До:    Title=%-15s | Members=%v\n", grp.Title, grp.Members)

	UpdateGroupMember(grp)

	fmt.Printf("2. После: Title=%-15s | Members=%v (ЭЛЕМЕНТ СРЕЗА СТАЛ New!)\n",
		grp.Title, grp.Members)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. До:    Title=Backend Team    | Members=[OldMember Alice Bob]
# 2. После: Title=Backend Team    | Members=[New Alice Bob] (ЭЛЕМЕНТ СРЕЗА СТАЛ New!)"""
            }
        ],
        "under_the_hood": """
`grp.Members` и `g.Members` ссылаются на один базовый массив строк.
""",
        "pitfalls": """
- Ожидание, что поле `Title` тоже изменится снаружи.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `Title` не изменился, а `Members[0]` изменился?»
**Ответ:** Потому что `Title` — это значение строки, скопированное в поле структуры, а `Members` — это срез с указателем на общий базовый массив.
"""
    },
    {
        "num": 65,
        "title": "Утечка состояния через структуру с указателем Config{Timeout *time.Duration} и Deep Copy",
        "task": "Структура с указателем (Утечка состояния): Создайте структуру Config с полем Timeout *time.Duration. Создайте экземпляр, скопируйте его в другую переменную простым присваиванием cfg2 := cfg1. Измените Timeout в cfg2. Что произошло с Timeout в cfg1? Как это предотвратить (глубокое копирование)?",
        "theory": """
**Опасность поверхностного копирования структур с указателями (Pointer Aliasing Leak):**
- Присваивание `cfg2 := cfg1` копирует указатель `Timeout`;
- Изменение `*cfg2.Timeout = 10s` мутирует память, на которую ссылается и `cfg1`;
- **Решение:** Реализация метода глубокого копирования (Deep Copy / Clone).
""",
        "step_by_step": """
1. Создаем структуру `Config{Timeout *time.Duration}`.
2. Демонстрируем утечку при `cfg2 := cfg1`.
3. Пишем метод `(c Config) Clone() Config`.
4. Показываем полную изоляцию.
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

type Config struct {
	Timeout *time.Duration
}

func (c Config) Clone() Config {
	if c.Timeout == nil {
		return Config{Timeout: nil}
	}
	// Выделяем новую память для указателя (Deep Copy):
	newTimeout := *c.Timeout
	return Config{Timeout: &newTimeout}
}

func main() {
	d1 := 5 * time.Second
	cfg1 := Config{Timeout: &d1}

	// 1. Поверхностное копирование (ОПАСНО!):
	cfgBad := cfg1
	*cfgBad.Timeout = 99 * time.Second
	fmt.Printf("1. После поверхностного копирования: cfg1.Timeout = %v (ИСХОДНЫЙ КОНФИГ ИСПОРЧЕН!)\n", *cfg1.Timeout)

	// 2. Глубокое копирование (Deep Copy):
	d2 := 5 * time.Second
	cfgOrig := Config{Timeout: &d2}
	cfgGood := cfgOrig.Clone()
	*cfgGood.Timeout = 100 * time.Second

	fmt.Printf("2. После Deep Copy Clone():        cfgOrig.Timeout = %v (ИЗОЛЯЦИЯ СОХРАНЕНА!)\n", *cfgOrig.Timeout)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. После поверхностного копирования: cfg1.Timeout = 1m39s (ИСХОДНЫЙ КОНФИГ ИСПОРЧЕН!)
# 2. После Deep Copy Clone():        cfgOrig.Timeout = 5s (ИЗОЛЯЦИЯ СОХРАНЕНА!)"""
            }
        ],
        "under_the_hood": """
`Clone()` аллоцирует новую ячейку в куче, разрывая связь между указателями.
""",
        "pitfalls": """
- Непреднамеренное изменение глобальных настроек микросервиса.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как реализовать Deep Copy для сложных вложенных DTO с десятками полей?»
**Ответ:** 1) Написать рукописный метод `Clone()`; 2) Использовать кодогенерацию (например `deepcopy-gen` из Kubernetes ecosystem); 3) Сериализация/десериализация через `json.Marshal/Unmarshal` (медленно, но надежно).
"""
    },
    {
        "num": 66,
        "title": "Низкоуровневый доступ к полям структуры через unsafe.Pointer и адресное смещение unsafe.Offsetof",
        "task": "Ознакомление с пакетом unsafe: Используя пакет unsafe и unsafe.Pointer, получите указатель на первое поле структуры и, прибавив к адресу смещение, получите доступ ко второму полю без использования его имени. *(Внимание: используйте это только в учебных целях).*",
        "theory": """
**Адресная арифметика в пакете `unsafe`:**
- `unsafe.Pointer` позволяет обходить систему строгой типизации Go;
- Смещение поля вычисляется через `unsafe.Offsetof(s.Field)`;
- Преобразование `unsafe.Pointer(uintptr(p) + offset)` получает прямой адрес поля в памяти.
""",
        "step_by_step": """
1. Создаем структуру `type Header struct { ID int; Flags uint32 }`.
2. Получаем `unsafe.Pointer(&h)`.
3. Прибавляем `unsafe.Offsetof(h.Flags)`.
4. Читаем и меняем поле `Flags`.
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

type PacketHeader struct {
	ID    int    // Смещение: 0 байт (размер: 8 байт)
	Flags uint32 // Смещение: 8 байт (размер: 4 байта)
}

func main() {
	header := PacketHeader{ID: 101, Flags: 0xAA}
	fmt.Printf("1. Исходная структура: %+v\n", header)

	// Получаем указатель на базовый адрес структуры:
	basePtr := unsafe.Pointer(&header)

	// Вычисляем адрес поля Flags через смещение:
	flagsOffset := unsafe.Offsetof(header.Flags)
	flagsPtr := (*uint32)(unsafe.Pointer(uintptr(basePtr) + flagsOffset))

	// Модифицируем поле Flags напрямую по адресу:
	*flagsPtr = 0xFF

	fmt.Printf("2. После unsafe мутации: %+v (Flags успешно изменен на 0xFF!)\n", header)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Исходная структура: {ID:101 Flags:170}
# 2. После unsafe мутации: {ID:101 Flags:255} (Flags успешно изменен на 0xFF!)"""
            }
        ],
        "under_the_hood": """
Прямое вычисление адреса памяти `base + 8`.
""",
        "pitfalls": """
- Сохранение `uintptr` в переменную: сборщик мусора GC не видит `uintptr` как указатель и может переместить структуру.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему правило 3 в документации `unsafe.Pointer` требует вычислять `unsafe.Pointer(uintptr(p) + offset)` в одно неделимое выражение?»
**Ответ:** Чтобы сборщик мусора GC и стековый движок не переместили объект между вычислением промежуточного `uintptr` и его обратным преобразованием в `unsafe.Pointer`.
"""
    },
    {
        "num": 67,
        "title": "Поведение кастомных типов type MyInt int при передаче аргументов и методах",
        "task": "Поведение кастомных типов: Создайте тип-алиас type MyInt int. Напишите методы или функции, принимающие MyInt по значению и по ссылке. Убедитесь, что правила передачи не меняются.",
        "theory": """
**Инвариант правил передачи для кастомных типов:**
- `type MyInt int` создает отдельный именованный тип;
- Правила вызовов идентичны `int`: передача по значению копирует 8 байт, передача по указателю `*MyInt` передает адрес.
""",
        "step_by_step": """
1. Объявляем `type MyInt int`.
2. Пишем метод `(m MyInt) ValueMethod()`.
3. Пишем метод `(m *MyInt) PointerMethod()`.
4. Демонстрируем поведение.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type MyInt int

func (m MyInt) ValueMethod() {
	m += 10 // Изменяет копию
}

func (m *MyInt) PointerMethod() {
	if m != nil {
		*m += 10 // Изменяет оригинал
	}
}

func main() {
	var num MyInt = 100

	num.ValueMethod()
	fmt.Printf("1. После ValueMethod:   %d (не изменился)\n", num)

	num.PointerMethod()
	fmt.Printf("2. После PointerMethod: %d (изменился!)\n", num)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. После ValueMethod:   100 (не изменился)
# 2. После PointerMethod: 110 (изменился!)"""
            }
        ],
        "under_the_hood": """
Трансляция в вызовы `MyInt.ValueMethod(num)` и `(*MyInt).PointerMethod(&num)`.
""",
        "pitfalls": """
- Попытка вызвать pointer method на неадресуемом литерале `MyInt(100).PointerMethod()` (ошибка компиляции `cannot call pointer method on literal`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем отличие `type MyInt int` от `type MyInt = int`?»
**Ответ:** `type MyInt int` — это новый тип (New Defined Type) с собственным набором методов. `type MyInt = int` — это псевдоним (Type Alias), полностью взаимозаменяемый с `int` без явного приведения типов.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 3: {len(exercises)} exercises.")
