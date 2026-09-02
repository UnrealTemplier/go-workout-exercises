# Chapter 12 Part 1: Exercises 1 to 23

exercises = [
    {
        "num": 1,
        "title": "Передача примитива int по значению (Pass by Value) и изоляция локального стека",
        "task": "Передайте int в функцию, измените его внутри — покажите, что исходная переменная не изменилась.",
        "theory": """
**Фундаментальная модель передачи параметров в Go:**
- В языке Go **абсолютно все аргументы передаются по значению (Pass by Value)**;
- При вызове функции `Modify(x int)` значение аргумента побайтово копируется в локальный стековый фрейм или регистр CPU вызываемой функции;
- Любые изменения внутри функции затрагивают исключительно изолированную локальную копию.
""",
        "step_by_step": """
1. Объявляем функцию `ModifyInt(val int)`.
2. Внутри присваиваем `val = 999`.
3. Проверяем значение оригинальной переменной до и после вызова.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func ModifyInt(val int) {
	val = 999
	fmt.Printf("Внутри функции ModifyInt: val = %d (адрес: %p)\n", val, &val)
}

func main() {
	original := 42
	fmt.Printf("1. До вызова функции:      original = %d (адрес: %p)\n", original, &original)

	ModifyInt(original)

	fmt.Printf("2. После вызова функции:   original = %d (адрес: %p - НЕ ИЗМЕНИЛСЯ!)\n", original, &original)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. До вызова функции:      original = 42 (адрес: 0xc000018030)
# Внутри функции ModifyInt: val = 999 (адрес: 0xc000018038)
# 2. После вызова функции:   original = 42 (адрес: 0xc000018030 - НЕ ИЗМЕНИЛСЯ!)"""
            }
        ],
        "under_the_hood": """
В конвенции вызовов ABIInternal компилятор передает значение `42` в регистре процессора `RAX`, не затрагивая ячейку памяти `original`.
""",
        "pitfalls": """
- Ожидание, что функция изменит исходную переменную без передачи явного указателя `*int`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Существует ли в Go передача по ссылке (Pass by Reference) на уровне языка, как в C++ (`int &ref`)?»
**Ответ:** НЕТ! В спецификации Go нет ссылок в стиле C++. Все передается строго по значению. Когда мы передаем указатель `*T`, мы передаем **по значению сам 8-байтный адрес**.
"""
    },
    {
        "num": 2,
        "title": "Сравнение передачи массива и среза: глубокая копия данных vs копия заголовка SliceHeader",
        "task": "Сравните передачу массива и среза: массив копируется, срез — заголовок (изменение элементов влияет на оригинал).",
        "theory": """
**Ключевое различие между Arrays и Slices при вызовах:**
- **Массив `[3]int`:** является монолитным значимым типом. При передаче копируются **все элементы массива целиком** ($O(N)$ по памяти);
- **Срез `[]int`:** является 24-байтной структурой `SliceHeader (Data uintptr, Len int, Cap int)`. Копируется только 24-байтный заголовок, а указатель `Data` продолжает ссылаться на тот же базовый массив в памяти.
""",
        "step_by_step": """
1. Пишем `MutateArray(arr [3]int)`.
2. Пишем `MutateSlice(s []int)`.
3. Сравниваем поведение оригиналов в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func MutateArray(arr [3]int) {
	arr[0] = 777 // Изменяет локальную копию массива
}

func MutateSlice(s []int) {
	s[0] = 777 // Изменяет элемент в разделяемом базовом массиве!
}

func main() {
	origArray := [3]int{1, 2, 3}
	origSlice := []int{1, 2, 3}

	MutateArray(origArray)
	fmt.Printf("1. Массив после MutateArray: %v (НЕ ИЗМЕНИЛСЯ!)\n", origArray)

	MutateSlice(origSlice)
	fmt.Printf("2. Срез после MutateSlice:    %v (ИЗМЕНИЛСЯ НА МЕСТЕ!)\n", origSlice)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Массив после MutateArray: [1 2 3] (НЕ ИЗМЕНИЛСЯ!)
# 2. Срез после MutateSlice:    [777 2 3] (ИЗМЕНИЛСЯ НА МЕСТЕ!)"""
            }
        ],
        "under_the_hood": """
Для массива компилятор генерирует `memmove` на стек. Для среза — копирует 3 машинных слова (Data, Len, Cap) в регистры.
""",
        "pitfalls": """
- Передача гигантских массивов `[100000]int` по значению: приводит к копированию мегабайт памяти на каждый вызов.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему говорят, что срез передается по значению, если изменения элементов видны снаружи?»
**Ответ:** Потому что сам дескриптор `SliceHeader` копируется по значению, но одно из его полей — это указатель `Data` на базовый массив.
"""
    },
    {
        "num": 3,
        "title": "Передача структуры по значению User vs по указателю *User: влияние на поля",
        "task": "Передайте структуру по значению и по указателю; сравните результат изменения полей.",
        "theory": """
**Семантика структур (Struct Semantics):**
- Передача структуры по значению `func Update(u User)` создает независимую копию всех полей структуры;
- Передача по указателю `func Update(u *User)` передает адрес памяти, позволяя мутировать исходный объект.
""",
        "step_by_step": """
1. Создаем структуру `type User struct { Name string; Age int }`.
2. Пишем `UpdateValue(u User)` и `UpdatePointer(u *User)`.
3. Сравниваем результаты в `main()`.
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

func UpdateValue(u User) {
	u.Age += 10
}

func UpdatePointer(u *User) {
	if u != nil {
		u.Age += 10
	}
}

func main() {
	user1 := User{Name: "Иван", Age: 20}
	user2 := User{Name: "Ольга", Age: 20}

	UpdateValue(user1)
	fmt.Printf("1. user1 после UpdateValue:   %+v (копия, возраст 20)\n", user1)

	UpdatePointer(&user2)
	fmt.Printf("2. user2 после UpdatePointer: %+v (мутация, возраст 30)\n", user2)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. user1 после UpdateValue:   {Name:Иван Age:20} (копия, возраст 20)
# 2. user2 после UpdatePointer: {Name:Ольга Age:30} (мутация, возраст 30)"""
            }
        ],
        "under_the_hood": """
При вызове `UpdatePointer` передается только 8-байтный указатель, а поля модифицируются по прямому смещению в куче или стеке.
""",
        "pitfalls": """
- Вызов `UpdatePointer(nil)` без проверки `if u != nil` вызовет панику.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В каких случаях структуру ОБЯЗАТЕЛЬНО передавать по указателю?»
**Ответ:** 1) Когда требуется модификация полей; 2) Когда структура содержит мьютекс `sync.Mutex` (мьютексы нельзя копировать!); 3) Когда структура тяжелая ($> 64$ байт), чтобы избежать оверхеда на копирование.
"""
    },
    {
        "num": 4,
        "title": "Передача мапы map в функцию: ссылочная семантика указателя на заголовок hmap",
        "task": "Передайте мапу (map) в функцию, добавьте новую пару ключ-значение и проверьте оригинал. Объясните, почему мапы ведут себя как ссылочные типы.",
        "theory": """
**Внутреннее устройство `map` в Go:**
- Тип `map[K]V` в Go — это синтаксический сахар над указателем `*runtime.hmap`;
- При передаче мапы в функцию копируется **сам указатель на заголовок `hmap`**;
- Любая вставка `m[key] = val` или удаление `delete(m, key)` внутри функции модифицирует ту же самую хэш-таблицу в памяти!
""",
        "step_by_step": """
1. Пишем `InsertMetric(m map[string]int, key string, val int)`.
2. Создаем мапу `metrics := make(map[string]int)`.
3. Добавляем элементы через функцию.
4. Проверяем оригинал в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func InsertMetric(m map[string]int, key string, val int) {
	m[key] = val // Модифицирует оригинальную хэш-таблицу!
}

func main() {
	metrics := make(map[string]int)
	metrics["cpu_usage"] = 45

	fmt.Printf("1. До вызова:    %v\n", metrics)

	InsertMetric(metrics, "ram_usage", 78)
	InsertMetric(metrics, "disk_io", 120)

	fmt.Printf("2. После вызова: %v (НОВЫЕ КЛЮЧИ ПОЯВИЛИСЬ СНАРУЖИ!)\n", metrics)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. До вызова:    map[cpu_usage:45]
# 2. После вызова: map[cpu_usage:45 disk_io:120 ram_usage:78] (НОВЫЕ КЛЮЧИ ПОЯВИЛИСЬ СНАРУЖИ!)"""
            }
        ],
        "under_the_hood": """
Переменная `metrics` хранит указатель на структуру `hmap`. Функция получает копию этого указателя, ссылающегося на те же бакеты `bmap`.
""",
        "pitfalls": """
- Передача `nil`-мапы: чтение из нее сработает, но попытка вставки `m[k] = v` внутри функции вызовет панику `assignment to entry in nil map`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go нет синтаксиса `*map[string]int` в аргументах функций?»
**Ответ:** Потому что `map` уже является указателем под капотом. Указатель на мапу `*map` нужен только если функция должна заменить саму мапу на другой экземпляр (`*m = make(...)`).
"""
    },
    {
        "num": 5,
        "title": "Изоляция полей структуры при передаче по значению и защита от побочных эффектов",
        "task": "Напишите функцию, принимающую структуру по значению, и измените её поле. Убедитесь, что оригинал не изменился.",
        "theory": """
Закрепление принципа иммутабельности при передаче значимых структур.
""",
        "step_by_step": """
1. Создаем структуру `Product{Title string, Price float64}`.
2. Пишем функцию `ApplyDiscount(p Product, discount float64)`.
3. Убеждаемся в неизменности исходного объекта.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Product struct {
	Title string
	Price float64
}

func ApplyDiscount(p Product, discount float64) {
	p.Price -= discount
	fmt.Printf("Внутри ApplyDiscount: %+v\n", p)
}

func main() {
	item := Product{Title: "Клавиатура", Price: 5000.0}
	fmt.Printf("До вызова:            %+v\n", item)

	ApplyDiscount(item, 1000.0)

	fmt.Printf("После вызова:         %+v (ЦЕНА ОРИГИНАЛА НЕ ИЗМЕНИЛАСЬ!)\n", item)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До вызова:            {Title:Клавиатура Price:5000}
# Внутри ApplyDiscount: {Title:Клавиатура Price:4000}
# После вызова:         {Title:Клавиатура Price:5000} (ЦЕНА ОРИГИНАЛА НЕ ИЗМЕНИЛАСЬ!)"""
            }
        ],
        "under_the_hood": """
Структура копируется в локальный стек вызываемой функции.
""",
        "pitfalls": """
- Случайная передача по значению структуры, содержащей срезы (элементы среза изменятся, а примитивные поля — нет).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как сделать функцию `ApplyDiscount` чистой (Pure Function) и вернуть обновленную структуру?»
**Ответ:** Возвращать измененную копию: `func ApplyDiscount(p Product, discount float64) Product { p.Price -= discount; return p }`.
"""
    },
    {
        "num": 6,
        "title": "Инкремент Increment(x int): доказательство передачи примитивов по значению",
        "task": "Напиши функцию Increment(x int), которая пытается увеличить x на 1. Убедись, что оригинал не меняется (передача по значению).",
        "theory": """
Базовое доказательство отсутствия скрытых ссылок у числовых типов.
""",
        "step_by_step": """
1. Пишем `Increment(x int)`.
2. Вызываем с переменной `counter`.
3. Анализируем результат.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Increment(x int) {
	x++
}

func main() {
	counter := 10
	Increment(counter)
	fmt.Printf("Значение counter: %d (НЕ ИЗМЕНИЛОСЬ!)\n", counter)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Значение counter: 10 (НЕ ИЗМЕНИЛОСЬ!)"""
            }
        ],
        "under_the_hood": """
Инструкция `INCQ` выполняется над регистром, в который был скопирован аргумент.
""",
        "pitfalls": """
- Непонимание почему `counter` не стал 11.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как исправить функцию `Increment`, чтобы она изменила `counter`?»
**Ответ:** Передать указатель `func Increment(x *int) { *x++ }` и вызвать `Increment(&counter)`.
"""
    },
    {
        "num": 7,
        "title": "Ловушка append внутри функции: почему срез в main не видит добавленные элементы",
        "task": "Передайте слайс в функцию, добавьте туда элемент с помощью append и проверьте, изменился ли оригинальный слайс. Объясните результат.",
        "theory": """
**Анатомия ловушки передачи срезов (Slice Header Trap):**
- Срез передается как копия дескриптора `SliceHeader{Data, Len, Cap}`;
- Функция `append` увеличивает поле `Len` в **локальной копии дескриптора**;
- В вызывающей функции `main` поле `Len` у исходного `SliceHeader` остается прежним;
- Поэтому `fmt.Println(origSlice)` выводит только элементы до старой длины `Len`!
""",
        "step_by_step": """
1. Пишем `TryAppend(s []int, val int)`.
2. Передаем срез `data := []int{1, 2}`.
3. Объясняем, почему `len(data)` в `main` остался равен 2.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func TryAppend(s []int, val int) {
	s = append(s, val)
	fmt.Printf("Внутри TryAppend:   %v | len=%d, cap=%d\n", s, len(s), cap(s))
}

func main() {
	data := []int{1, 2}
	fmt.Printf("1. Исходный срез:   %v | len=%d, cap=%d\n", data, len(data), cap(data))

	TryAppend(data, 3)

	fmt.Printf("2. Срез в main:     %v | len=%d, cap=%d (ЭЛЕМЕНТ 3 НЕ ПОЯВИЛСЯ!)\n",
		data, len(data), cap(data))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Исходный срез:   [1 2] | len=2, cap=2
# Внутри TryAppend:   [1 2 3] | len=3, cap=4
# 2. Срез в main:     [1 2] | len=2, cap=2 (ЭЛЕМЕНТ 3 НЕ ПОЯВИЛСЯ!)"""
            }
        ],
        "under_the_hood": """
При вызове `append` локальная переменная `s` получила новый `SliceHeader` с `Len=3, Cap=4`, а переменная `data` в стеке `main` осталась с `Len=2, Cap=2`.
""",
        "pitfalls": """
- Попытка модифицировать длину среза без возврата обновленного среза `data = TryAppend(data, 3)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Где физически оказался элемент 3, если у исходного среза был запас `cap = 10`?»
**Ответ:** Элемент 3 был физически записан в 3-й слот базового массива в памяти, но `main()` не может его прочитать, так как его собственный дескриптор `Len` по-прежнему равен 2 (но его можно увидеть через срез `data[:3]`).
"""
    },
    {
        "num": 8,
        "title": "Передача массива по указателю *[5]int: экономия памяти и сохранение мутаций",
        "task": "Массивы по указателю: Напишите функцию, принимающую указатель на массив *[5]int. Измените элементы и убедитесь, что изменения сохранились.",
        "theory": """
Передача `*[N]T` исключает копирование элементов и позволяет мутировать массив на месте.
""",
        "step_by_step": """
1. Пишем `FillArray(arr *[5]int)`.
2. Заполняем массив значениями.
3. Проверяем в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func FillArray(arr *[5]int) {
	if arr == nil {
		return
	}
	for i := range arr {
		arr[i] = (i + 1) * 10
	}
}

func main() {
	var numbers [5]int
	fmt.Printf("До заполнения:    %v\n", numbers)

	FillArray(&numbers)

	fmt.Printf("После заполнения: %v (МУТАЦИЯ СОХРАНЕНА!)\n", numbers)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До заполнения:    [0 0 0 0 0]
# После заполнения: [10 20 30 40 50] (МУТАЦИЯ СОХРАНЕНА!)"""
            }
        ],
        "under_the_hood": """
Функция получает 8-байтный указатель на начало непрерывного 40-байтного блока памяти.
""",
        "pitfalls": """
- Жесткая привязка к фиксированному размеру массива `[5]int` (для гибкости используют срезы `[]int`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему сигнатура `func Foo(arr *[5]int)` менее гибка, чем `func Foo(s []int)`?»
**Ответ:** Потому что размер массива `[5]int` является частью типа. В такую функцию нельзя передать массив `[6]int` или срез.
"""
    },
    {
        "num": 9,
        "title": "Мутация существующего элемента среза по индексу s[0] = val и общий базовый массив",
        "task": "Передайте слайс в функцию и измените существующий элемент по индексу. Объясните разницу с предыдущим пунктом.",
        "theory": """
**Разница между изменением элемента и append:**
- Изменение существующего элемента `s[0] = 999` **НЕ меняет заголовок среза** (длина и емкость прежние);
- Оно перезаписывает байты напрямую в базовом массиве по указателю `Data`;
- Поэтому вызывающий код немедленно видит обновление элемента.
""",
        "step_by_step": """
1. Пишем `UpdateFirstElement(s []int, newVal int)`.
2. Передаем `scores := []int{10, 20, 30}`.
3. Проверяем обновление `scores[0]`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func UpdateFirstElement(s []int, newVal int) {
	if len(s) > 0 {
		s[0] = newVal // Прямая запись в общий базовый массив!
	}
}

func main() {
	scores := []int{10, 20, 30}
	fmt.Printf("До вызова:    %v\n", scores)

	UpdateFirstElement(scores, 999)

	fmt.Printf("После вызова: %v (ЭЛЕМЕНТ s[0] ОБНОВИЛСЯ!)\n", scores)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До вызова:    [10 20 30]
# После вызова: [999 20 30] (ЭЛЕМЕНТ s[0] ОБНОВИЛСЯ!)"""
            }
        ],
        "under_the_hood": """
Инструкция процессора `MOVQ $999, (Data)`.
""",
        "pitfalls": """
- Вызов `s[0] = ...` для пустого среза `len == 0` (паника `index out of range`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Является ли операция `s[i] = v` потокобезопасной при передаче среза в несколько горутин?»
**Ответ:** НЕТ! Параллельная запись в один и тот же индекс среза без синхронизации (`sync.Mutex`) приводит к Data Race.
"""
    },
    {
        "num": 10,
        "title": "Передача интерфейса с Value Receiver vs Pointer Receiver и сохранение мутаций",
        "task": "Передайте интерфейс, содержащий указатель-получатель и значение-получатель, и убедитесь в разнице при изменении.",
        "theory": """
**Интерфейсы и семантика получателей:**
- Если интерфейс упаковывает значение по значению (`User`), методы с value receiver модифицируют копию внутри интерфейса;
- Если интерфейс упаковывает указатель (`*User`), методы с pointer receiver модифицируют оригинальный объект в куче.
""",
        "step_by_step": """
1. Создаем интерфейс `type Resetter interface { Reset() }`.
2. Реализуем метод на структуре `Counter` с pointer receiver.
3. Передаем интерфейс в функцию.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Resetter interface {
	Reset()
}

type Counter struct {
	Value int
}

func (c *Counter) Reset() {
	c.Value = 0 // Мутирует оригинальный объект через указатель
}

func DoReset(r Resetter) {
	r.Reset()
}

func main() {
	cnt := &Counter{Value: 100}
	fmt.Printf("До DoReset:    %+v\n", cnt)

	DoReset(cnt)

	fmt.Printf("После DoReset: %+v (ОБНУЛЕН ЧЕРЕЗ ИНТЕРФЕЙС!)\n", cnt)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До DoReset:    &{Value:100}
# После DoReset: &{Value:0} (ОБНУЛЕН ЧЕРЕЗ ИНТЕРФЕЙС!)"""
            }
        ],
        "under_the_hood": """
Интерфейс хранит `itab` (таблицу методов) и `data` (указатель на экземпляр `*Counter`).
""",
        "pitfalls": """
- Попытка передать `Counter{}` по значению в интерфейс, где методы объявлены на `*Counter` (ошибка компиляции `does not implement Resetter`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему структура `Counter` не реализует интерфейс, если метод объявлен как `func (c *Counter) Reset()`?»
**Ответ:** Потому что метод принадлежит набору методов (Method Set) указателя `*Counter`, а не значения `Counter`.
"""
    },
    {
        "num": 11,
        "title": "Каверзный кейс: ChangeName(u User) vs ChangeNamePtr(u *User)",
        "task": "[Каверзный кейс]: Создай структуру (struct) User{Name string}. Напиши функцию ChangeName(u User), меняющую имя (передача по значению). И функцию ChangeNamePtr(u *User). Проверь разницу.",
        "theory": """
Сравнение мутаций строковых полей в структурах.
""",
        "step_by_step": """
1. Создаем структуру `User{Name string}`.
2. Пишем `ChangeName(u User, name string)` и `ChangeNamePtr(u *User, name string)`.
3. Сравниваем результаты.
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

func ChangeName(u User, newName string) {
	u.Name = newName // Изменяет локальную копию
}

func ChangeNamePtr(u *User, newName string) {
	if u != nil {
		u.Name = newName // Изменяет оригинал
	}
}

func main() {
	u1 := User{Name: "Иван"}
	u2 := User{Name: "Олег"}

	ChangeName(u1, "Петр")
	fmt.Printf("1. ChangeName:    %s (оригинал не изменился)\n", u1.Name)

	ChangeNamePtr(&u2, "Петр")
	fmt.Printf("2. ChangeNamePtr: %s (оригинал успешно обновлен!)\n", u2.Name)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. ChangeName:    Иван (оригинал не изменился)
# 2. ChangeNamePtr: Петр (оригинал успешно обновлен!)"""
            }
        ],
        "under_the_hood": """
Строковое поле `Name` (16 байт) копируется при вызове `ChangeName` и модифицируется по указателю в `ChangeNamePtr`.
""",
        "pitfalls": """
- Передача по значению больших DTO при обработке HTTP-запросов.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каков размер заголовка структуры `User{Name string}` в памяти?»
**Ответ:** 16 байт (размер `StringHeader: Data uintptr, Len int`).
"""
    },
    {
        "num": 12,
        "title": "Неизменяемость строк (String Immutability) в Go и безопасный возврат новой строки",
        "task": "Передайте строку в функцию, \"измените\" её (создайте новую) и верните. Объясните неизменяемость (immutability) строк в Go.",
        "theory": """
**Строгая иммутабельность строк в Go:**
- В Go байты строки, на которые ссылается `StringHeader.Data`, защищены от записи (Read-Only Memory);
- Любая модификация (например, `strings.ToUpper` или замена символов) создает **новую строку** и возвращает новый заголовок;
- Строки можно безопасно передавать в сотни горутин без риска гонок данных!
""",
        "step_by_step": """
1. Пишем `AddPrefix(s, prefix string) string`.
2. Возвращаем новую строку `prefix + s`.
3. Показываем неизменность исходной строки.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func AddPrefix(s string, prefix string) string {
	// Строки в Go иммутабельны. Создается новая строка:
	return prefix + ": " + s
}

func main() {
	original := "сервис авторизации"
	fmt.Printf("1. Исходная строка: %q\n", original)

	result := AddPrefix(original, "[AUDIT]")

	fmt.Printf("2. Новая строка:     %q\n", result)
	fmt.Printf("3. Исходная строка: %q (НЕ ИЗМЕНИЛАСЬ!)\n", original)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Исходная строка: "сервис авторизации"
# 2. Новая строка:     "[AUDIT]: сервис авторизации"
# 3. Исходная строка: "сервис авторизации" (НЕ ИЗМЕНИЛАСЬ!)"""
            }
        ],
        "under_the_hood": """
Конкатенация строк вызывает `runtime.concatstrings`, который выделяет новый буфер памяти.
""",
        "pitfalls": """
- Попытка изменить байт строки `s[0] = 'A'` (ошибка компиляции `cannot assign to s[0]`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему строки в Go сделаны иммутабельными?»
**Ответ:** Для безопасности памяти, потокобезопасности без блокировок мьютексов и возможности безопасного слайсинга подстрок `sub := s[1:5]` за $O(1)$ без копирования байт.
"""
    },
    {
        "num": 13,
        "title": "Сброс длины среза ResetSlice(s []int) через s[:0] и сохранение оригинального среза в main",
        "task": "Напиши функцию ResetSlice(s []int), которая делает s = s[:0]. Покажи, что оригинальный слайс в main НЕ изменился (длина осталась прежней). Объясни почему (слайс — это struct с указателем, len, cap; передача по значению копирует эту struct).",
        "theory": """
**Копирование дескриптора среза при вызове `s = s[:0]`:**
- Локальная переменная `s` получает `Len = 0`;
- Переменная `data` в `main()` сохраняет свое оригинальное поле `Len`;
- Чтобы обнулить длину в `main`, нужно либо вернуть `s[:0]`, либо передать указатель `*[]int`.
""",
        "step_by_step": """
1. Пишем `ResetSlice(s []int)`.
2. Выполняем `s = s[:0]`.
3. Проверяем срез в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func ResetSlice(s []int) {
	s = s[:0] // Изменяет Len только в локальной копии SliceHeader!
	fmt.Printf("Внутри ResetSlice:  len=%d, cap=%d\n", len(s), cap(s))
}

func main() {
	numbers := []int{10, 20, 30, 40}
	fmt.Printf("1. До вызова:        %v | len=%d, cap=%d\n", numbers, len(numbers), cap(numbers))

	ResetSlice(numbers)

	fmt.Printf("2. После вызова:     %v | len=%d, cap=%d (ДЛИНА В MAIN НЕ ИЗМЕНИЛАСЬ!)\n",
		numbers, len(numbers), cap(numbers))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. До вызова:        [10 20 30 40] | len=4, cap=4
# Внутри ResetSlice:  len=0, cap=4
# 2. После вызова:     [10 20 30 40] | len=4, cap=4 (ДЛИНА В MAIN НЕ ИЗМЕНИЛАСЬ!)"""
            }
        ],
        "under_the_hood": """
Операция `s[:0]` перезаписывает регистр `RBX` (Len), оставляя стековый слот `numbers` нетронутым.
""",
        "pitfalls": """
- Заблуждение, что `s[:0]` освобождает память базового массива (емкость `cap` сохраняется).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как правильно написать функцию сброса среза?»
**Ответ:** Использовать возврат: `func ResetSlice(s []int) []int { return s[:0] }` и вызывать `s = ResetSlice(s)`.
"""
    },
    {
        "num": 14,
        "title": "Идиоматичный возврат обновленного среза после append: func AddItem(s []T, val T) []T",
        "task": "Покажите ошибку: передали срез, внутри функции append, снаружи не видно новых элементов без возврата; исправьте, используя возврат обновлённого среза.",
        "theory": """
Золотой стандарт работы со срезами в Go: **всегда возвращать результат `append` из функции**.
""",
        "step_by_step": """
1. Пишем `AddItem(s []string, item string) []string`.
2. Возвращаем `append(s, item)`.
3. Переприсваиваем результат в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func AddItem(s []string, item string) []string {
	return append(s, item) // Идиоматичный возврат обновленного среза
}

func main() {
	tasks := []string{"Написать код", "Запустить тесты"}
	fmt.Printf("1. До:    %v (len=%d)\n", tasks, len(tasks))

	// Правильный паттерн: переприсваивание результата
	tasks = AddItem(tasks, "Собрать Docker образ")

	fmt.Printf("2. После: %v (len=%d - УСПЕШНО ДОБАВЛЕНО!)\n", tasks, len(tasks))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. До:    [Написать код Запустить тесты] (len=2)
# 2. После: [Написать код Запустить тесты Собрать Docker образ] (len=3 - УСПЕШНО ДОБАВЛЕНО!)"""
            }
        ],
        "under_the_hood": """
Возвращается обновленный 24-байтный заголовок `SliceHeader`.
""",
        "pitfalls": """
- Игнорирование возвращаемого значения `AddItem(tasks, "item")` (линтер `errcheck`/`govet`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему стандартные функции вроде `append` требуют переприсваивания `s = append(s, v)`?»
**Ответ:** Потому что при переполнении `cap` функция аллоцирует новый массив в куче, и старая переменная `s` должна быть обновлена новым указателем.
"""
    },
    {
        "num": 15,
        "title": "Защитная проверка указателей на nil внутри функций (Defensive Nil-Check)",
        "task": "Создай функцию, которая принимает указатель, но аргумент может быть nil. Обработай эту ситуацию внутри функции (if ptr == nil).",
        "theory": """
**Паттерн защитного программирования (Defensive Programming):**
- Любая публичная функция или метод, принимающий указатель `*T`, обязана проверять `if ptr == nil`;
- Защищает сервис от падений при некорректных входных параметрах.
""",
        "step_by_step": """
1. Пишем `PrintScore(score *int)`.
2. Добавляем проверку `if score == nil`.
3. Тестируем на валидном значении и `nil`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func PrintScore(score *int) {
	if score == nil {
		fmt.Println("⚠️ Оценка отсутствует (nil указатель)")
		return
	}
	fmt.Printf("Оценка студента: %d баллов\n", *score)
}

func main() {
	val := 95
	PrintScore(&val)
	PrintScore(nil) // Безопасный вызов!
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Оценка студента: 95 баллов
# ⚠️ Оценка отсутствует (nil указатель)"""
            }
        ],
        "under_the_hood": """
Инструкция условного перехода `CMPQ (ptr), $0; JE nil_block`.
""",
        "pitfalls": """
- Прямое обращение `*score` без `if score == nil`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как писать надежные методы для `nil`-получателей?»
**Ответ:** Проверять `if r == nil` в первой строке метода и возвращать дефолтные значения или ошибку.
"""
    },
    {
        "num": 16,
        "title": "Пользовательский тип type Score int: передача по значению vs по указателю",
        "task": "Создайте кастомный тип на основе int. Передайте его в функцию по значению и по ссылке, изучите разницу.",
        "theory": """
Пользовательские типы (Type Definitions) наследуют семантику передачи базового типа.
""",
        "step_by_step": """
1. Объявляем `type Score int`.
2. Пишем `AddScoreVal(s Score)` и `AddScorePtr(s *Score)`.
3. Сравниваем результаты.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Score int

func AddScoreVal(s Score) {
	s += 10
}

func AddScorePtr(s *Score) {
	if s != nil {
		*s += 10
	}
}

func main() {
	var s1 Score = 50
	var s2 Score = 50

	AddScoreVal(s1)
	fmt.Printf("1. s1 после AddScoreVal: %d (не изменился)\n", s1)

	AddScorePtr(&s2)
	fmt.Printf("2. s2 после AddScorePtr: %d (изменился!)\n", s2)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. s1 после AddScoreVal: 50 (не изменился)
# 2. s2 после AddScorePtr: 60 (изменился!)"""
            }
        ],
        "under_the_hood": """
`Score` имеет одинаковое машинное представление с `int` (8 байт).
""",
        "pitfalls": """
- Заблуждение, будто кастомный тип приобретает ссылочные свойства.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Отличается ли производительность передачи `type MyInt int` от стандартного `int`?»
**Ответ:** НЕТ, они полностью идентичны на уровне ассемблерного кода.
"""
    },
    {
        "num": 17,
        "title": "Передача строк в функции: 16-байтный заголовок StringHeader и Read-Only безопасность",
        "task": "Изучите поведение строк при передаче: строка неизменяема, попытка изменения через unsafe запрещена (просто поймите, что строка — копия заголовка).",
        "theory": """
**Устройство строки при передаче в функцию:**
- Структура строки: `(Data uintptr, Len int)` — ровно 16 байт;
- Передача строки в функцию не копирует сами символы, а лишь копирует 16-байтный заголовок;
- Передача огромной строки на 1 ГБ в функцию выполняется мгновенно за 0 нс без аллокаций памяти!
""",
        "step_by_step": """
1. Пишем `InspectString(s string)`.
2. Выводим длину и проверяем неизменность данных.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func InspectString(s string) {
	fmt.Printf("Внутри функции: длина = %d байт\n", len(s))
}

func main() {
	hugeText := "Высоконагруженный сервис на Go с миллионами RPS"
	fmt.Printf("Оригинальная строка: %q\n", hugeText)

	// Передача выполняется мгновенно (копируется 16 байт):
	InspectString(hugeText)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Оригинальная строка: "Высоконагруженный сервис на Go с миллионами RPS"
# Внутри функции: длина = 88 байт"""
            }
        ],
        "under_the_hood": """
Строка размещается в сегменте `.rodata` или куче, дескриптор передается в регистрах `RAX, RBX`.
""",
        "pitfalls": """
- Передача `*string` (создает лишнее разыменование и аллокацию указателя).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Нужно ли передавать строки по указателю `*string` для оптимизации производительности?»
**Ответ:** НЕТ! Передача `string` по значению (16 байт) оптимальна, так как байты строки никогда не копируются при передаче.
"""
    },
    {
        "num": 18,
        "title": "Передача функций (Callbacks) по значению: передача 8-байтного указателя на код",
        "task": "Напишите функцию, которая принимает функцию (callback) по значению и вызывает её. Является ли функция ссылочным типом?",
        "theory": """
**Тип функции как функциональное значение:**
- В Go переменная типа `func()` физически хранит указатель на машинный код (или структуру замыкания);
- Передача функции в качестве аргумента передает 8-байтный указатель по значению.
""",
        "step_by_step": """
1. Пишем `ExecuteCallback(cb func(string))`.
2. Передаем анонимную функцию.
3. Анализируем вызов.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func ExecuteCallback(action func(msg string)) {
	if action != nil {
		action("Коллбэк успешно вызван!")
	}
}

func main() {
	handler := func(msg string) {
		fmt.Println("LOG:", msg)
	}

	ExecuteCallback(handler)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# LOG: Коллбэк успешно вызван!"""
            }
        ],
        "under_the_hood": """
Инструкция процессора `CALL (RAX)`.
""",
        "pitfalls": """
- Вызов `nil`-функции `var f func(); f()` приведет к панике.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каков размер переменной типа функции в Go?»
**Ответ:** 8 байт (указатель на функцию).
"""
    },
    {
        "num": 19,
        "title": "Функция ModifyMap(m map[string]int) и ссылочное поведение хэш-таблиц",
        "task": "Напиши функцию ModifyMap(m map[string]int), которая добавляет элемент в мапу. Покажи, что оригинальная мапа изменилась (мапа — ссылочный тип, передаётся по значению struct, но внутри указатель). Объясни.",
        "theory": """
Демонстрация модификации хэш-таблицы внутри изолированной функции.
""",
        "step_by_step": """
1. Пишем `ModifyMap(m map[string]int)`.
2. Добавляем ключ `"status" = 200`.
3. Проверяем в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func ModifyMap(m map[string]int) {
	m["status"] = 200
	m["retries"] = 3
}

func main() {
	config := map[string]int{"timeout": 5}
	fmt.Printf("1. До вызова:    %v\n", config)

	ModifyMap(config)

	fmt.Printf("2. После вызова: %v (МУТАЦИЯ МАПЫ СОХРАНЕНА!)\n", config)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. До вызова:    map[timeout:5]
# 2. После вызова: map[retries:3 status:200 timeout:5] (МУТАЦИЯ МАПЫ СОХРАНЕНА!)"""
            }
        ],
        "under_the_hood": """
Мапа передается как копия указателя `*hmap`.
""",
        "pitfalls": """
- Конкурентная модификация мапы из разных горутин без мьютекса (fatal error: concurrent map writes).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему мапы в Go не требуют явной передачи по указателю `*map`?»
**Ответ:** Потому что тип `map` уже является указателем на структуру `hmap` в рантайме.
"""
    },
    {
        "num": 20,
        "title": "Канал chan int как ссылочный тип: передача дескриптора *hchan в функцию-воркер",
        "task": "Создайте канал (chan int), передайте его в функцию и отправьте туда данные. Проверьте получение в главной горутине.",
        "theory": """
**Анатомия каналов (Channels) в Go:**
- Тип `chan T` под капотом является указателем на структуру `*runtime.hchan`;
- Передача канала в функцию копирует только 8-байтный указатель;
- Обе горутины работают с одной и той же кольцевой очередью буфера канала.
""",
        "step_by_step": """
1. Пишем функцию `ProduceData(ch chan<- int)`.
2. Создаем `ch := make(chan int, 3)`.
3. Отправляем и читаем данные.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func ProduceData(ch chan<- int) {
	ch <- 100
	ch <- 200
	close(ch)
}

func main() {
	ch := make(chan int, 2)

	go ProduceData(ch)

	for val := range ch {
		fmt.Printf("Получено из канала: %d\n", val)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Получено из канала: 100
# Получено из канала: 200"""
            }
        ],
        "under_the_hood": """
Структура `hchan` хранит мьютекс `lock`, буфер `buf`, очереди ожидания горутин `recvq` и `sendq`.
""",
        "pitfalls": """
- Отправка в `nil`-канал: блокирует горутину навсегда (Deadlock).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каков размер переменной `ch chan int` в памяти?»
**Ответ:** Ровно 8 байт (указатель на структуру `hchan`).
"""
    },
    {
        "num": 21,
        "title": "Передача указателя на указатель **int и мутация целевого адреса",
        "task": "Изучи, как передать указатель на указатель (**int). Напиши функцию, меняющую значение, на которое указывает внутренний указатель.",
        "theory": """
Закрепление работы с двойными указателями в сигнатурах функций.
""",
        "step_by_step": """
1. Пишем `UpdateTarget(pp **int, newVal int)`.
2. Модифицируем значение `**pp = newVal`.
3. Проверяем в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func UpdateTarget(pp **int, newVal int) {
	if pp != nil && *pp != nil {
		**pp = newVal
	}
}

func main() {
	x := 55
	p := &x

	fmt.Printf("До:    x = %d\n", x)

	UpdateTarget(&p, 777)

	fmt.Printf("После: x = %d\n", x)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До:    x = 55
# После: x = 777"""
            }
        ],
        "under_the_hood": """
Косвенная запись через двойное смещение.
""",
        "pitfalls": """
- Забыть проверку `*pp != nil`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем отличие `*a, *b = *b, *a` от манипуляций с `**int`?»
**Ответ:** Swap меняет значения в существующих ячейках, а `**int` позволяет перенаправить указатель на совершенно другую область памяти.
"""
    },
    {
        "num": 22,
        "title": "Каверзный кейс срезов: s := make([]int, 3, 10), мутация s[0] и невидимость append без реаллокации",
        "task": "Создай слайс s := make([]int, 3, 10). Заполни значениями. Передай в функцию, которая меняет s[0]. Покажи, что оригинал изменился (потому что слайс содержит указатель на массив). Затем в той же функции сделай append — покажи, что оригинал не увидел новые элементы (если не было реаллокации) или увидел (если была реаллокация и ты вернул результат). Это каверзный случай!",
        "theory": """
**Глубокий разбор скрытой модификации базового массива:**
- При `cap(s) = 10` и `len(s) = 3` вызов `append(s, 999)` **НЕ вызывает реаллокацию**;
- Элемент `999` записывается в 4-й слот разделяемого базового массива в памяти;
- Но в `main` длина `len(s)` осталась равной 3, поэтому `s` не отображает 4-й элемент, хотя он физически там записан!
- Доказательство: в `main` срез `s[:4]` отобразит записанный элемент!
""",
        "step_by_step": """
1. Создаем `s := make([]int, 3, 10)`.
2. Пишем функцию `TrickySliceDemo(s []int)`.
3. Внутри меняем `s[0] = 777` и делаем `s = append(s, 999)`.
4. В `main` печатаем `s` и подсрез `s[:4]`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func TrickySliceDemo(s []int) {
	s[0] = 777         // 1. Мутация элемента (ВИДНА В MAIN!)
	s = append(s, 999) // 2. Запись в 4-й слот базового массива без реаллокации (cap=10)
	fmt.Printf("Внутри функции: s = %v | len=%d, cap=%d\n", s, len(s), cap(s))
}

func main() {
	s := make([]int, 3, 10)
	s[0], s[1], s[2] = 1, 2, 3

	fmt.Printf("1. Исходный срез:           %v | len=%d, cap=%d\n", s, len(s), cap(s))

	TrickySliceDemo(s)

	fmt.Printf("2. Срез в main:             %v | len=%d, cap=%d (s[0] изменился!)\n",
		s, len(s), cap(s))

	// ⚠️ СЕКРЕТ: Раскрываем 4-й элемент среза через ре-слайсинг:
	fmt.Printf("3. Доступ через s[:4]:      %v (ЭЛЕМЕНТ 999 ФИЗИЧЕСКИ ТАМ ЕСТЬ!)\n", s[:4])
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Исходный срез:           [1 2 3] | len=3, cap=10
# Внутри функции: s = [777 2 3 999] | len=4, cap=10
# 2. Срез в main:             [777 2 3] | len=3, cap=10 (s[0] изменился!)
# 3. Доступ через s[:4]:      [777 2 3 999] (ЭЛЕМЕНТ 999 ФИЗИЧЕСКИ ТАМ ЕСТЬ!)"""
            }
        ],
        "under_the_hood": """
Оба дескриптора среза ссылаются на один и тот же адрес `Data`, но имеют разные поля `Len` (3 в `main` и 4 в функции).
""",
        "pitfalls": """
- Неожиданная перезапись данных в общем базовом массиве другими функциями.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему этот случай называют 'невидимой мутацией памяти'?»
**Ответ:** Потому что элемент физически записывается в разделяемый массив памяти, но вызывающая сторона не видит его через стандартный `len`, пока не сделает ре-слайсинг.
"""
    },
    {
        "num": 23,
        "title": "Реаллокация базового массива при append (cap == len) и полное расщепление связей срезов",
        "task": "Создайте слайс, передайте его в функцию, сделайте append, который вызовет реаллокацию базового массива. Убедитесь, что оригинальный слайс в main не увидел новых элементов.",
        "theory": """
**Полное расщепление памяти (Memory Decoupling):**
- Если `len == cap`, вызов `append` выделяет **новый массив в куче**;
- Новые элементы и последующие мутации `s[0] = ...` внутри функции пишутся в **новый массив**;
- Исходный срез в `main` остается указывать на **старый массив** и больше не видит никаких изменений!
""",
        "step_by_step": """
1. Создаем срез `s := []int{1, 2}` (`len=2, cap=2`).
2. Пишем `DecoupleDemo(s []int)`.
3. Внутри делаем `s = append(s, 3); s[0] = 999`.
4. Демонстрируем, что в `main` даже `s[0]` остался `1`!
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func DecoupleDemo(s []int) {
	// append превышает cap=2 -> выделяется НОВЫЙ массив в куче!
	s = append(s, 3)
	s[0] = 999 // Изменяет НОВЫЙ массив, старый массив не тронут!

	fmt.Printf("Внутри DecoupleDemo: s = %v (новый массив)\n", s)
}

func main() {
	s := []int{1, 2} // len=2, cap=2
	fmt.Printf("1. Исходный срез: %v (адрес базового массива: %p)\n", s, s)

	DecoupleDemo(s)

	fmt.Printf("2. Срез в main:   %v (адрес: %p - ПОЛНАЯ ИЗОЛЯЦИЯ!)\n", s, s)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Исходный срез: [1 2] (адрес базового массива: 0xc000018030)
# Внутри DecoupleDemo: s = [999 2 3] (новый массив)
# 2. Срез в main:   [1 2] (адрес: 0xc000018030 - ПОЛНАЯ ИЗОЛЯЦИЯ!)"""
            }
        ],
        "under_the_hood": """
`runtime.growslice` выделяет новый блок памяти и копирует туда элементы, меняя указатель `Data`.
""",
        "pitfalls": """
- Распространенная ошибка на собеседованиях: предполагать, что `s[0] = 999` после `append` изменит оригинал при `len == cap`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «При каких условиях модификация `s[0] = 999` после `append` изменит исходный срез в `main`?»
**Ответ:** ТОЛЬКО если у исходного среза был достаточный запас емкости (`cap > len`) на момент вызова `append`. Если емкости не хватило, происходит реаллокация и связь полностью теряется.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 1: {len(exercises)} exercises.")
