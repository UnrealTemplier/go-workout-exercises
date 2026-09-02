# Chapter 11 Part 2: Exercises 26 to 49

exercises = [
    {
        "num": 26,
        "title": "Функция AppendWithPointer(s *[]int, val int) с сохранением нового заголовка среза",
        "task": "Реализуйте функцию, принимающую *[]int и делающую append, чтобы изменение слайса (длины и ёмкости) стало видно снаружи.",
        "theory": """
**Указатель на структуру SliceHeader `*[]T`:**
- При реаллокации среза функция `append` создает новый массив и возвращает новый `SliceHeader`;
- Передача указателя `*[]int` позволяет функции перезаписать заголовок среза вызывающей стороны `*s = append(*s, val)`.
""",
        "step_by_step": """
1. Пишем `AppendWithPointer(s *[]int, val int)`.
2. Проверяем `s != nil`.
3. Вызываем `*s = append(*s, val)`.
4. Тестируем в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func AppendWithPointer(s *[]int, val int) {
	if s == nil {
		return
	}
	*s = append(*s, val)
}

func main() {
	var nums []int // nil-срез
	fmt.Printf("1. До:    %v | len=%d, cap=%d\n", nums, len(nums), cap(nums))

	AppendWithPointer(&nums, 10)
	AppendWithPointer(&nums, 20)
	AppendWithPointer(&nums, 30)

	fmt.Printf("2. После: %v | len=%d, cap=%d (МУТАЦИЯ СОХРАНЕНА!)\n",
		nums, len(nums), cap(nums))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. До:    [] | len=0, cap=0
# 2. После: [10 20 30] | len=3, cap=4 (МУТАЦИЯ СОХРАНЕНА!)"""
            }
        ],
        "under_the_hood": """
Функция модифицирует поля `Data`, `Len`, `Cap` в вызывающем стековом кадре.
""",
        "pitfalls": """
- Вызов `AppendWithPointer(nil, 10)` без проверки на `nil`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в 99% случаев лучше возвращать срез `func Foo(s []T) []T`, а не принимать `*[]T`?»
**Ответ:** Возврат значения обеспечивает прозрачный поток данных (Value Semantics), облегчает композицию вызовов и снижает риск гонок данных в многопоточном коде.
"""
    },
    {
        "num": 27,
        "title": "Обмен числовых значений SwapValues(a, b *int) через разыменование указателей",
        "task": "Напишите функцию, которая принимает два указателя на числа и меняет местами значения, на которые они указывают.",
        "theory": """
Закрепление безопасного обмена значений по указателям.
""",
        "step_by_step": """
1. Пишем `SwapValues(a, b *int)`.
2. Меняем значения `*a, *b = *b, *a`.
3. Тестируем.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func SwapValues(a, b *int) {
	if a == nil || b == nil {
		return
	}
	*a, *b = *b, *a
}

func main() {
	first, second := 50, 90
	fmt.Printf("До:    first = %d, second = %d\n", first, second)

	SwapValues(&first, &second)

	fmt.Printf("После: first = %d, second = %d\n", first, second)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До:    first = 50, second = 90
# После: first = 90, second = 50"""
            }
        ],
        "under_the_hood": """
Ассемблерные инструкции `MOVQ (AX), CX; MOVQ (BX), DX; MOVQ DX, (AX); MOVQ CX, (BX)`.
""",
        "pitfalls": """
- Передача `nil`-указателей.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что произойдет, если передать один и тот же указатель `SwapValues(&x, &x)`?»
**Ответ:** Значение переменной останется неизменным.
"""
    },
    {
        "num": 28,
        "title": "Модификация значения переменной x через разыменование указателя *p = 100",
        "task": "Разыменование: Создайте указатель на переменную x. Через этот указатель измените значение x на 100. Выведите x и проверьте, что оно изменилось.",
        "theory": """
Прямой доступ к памяти через оператор `*`.
""",
        "step_by_step": """
1. Создаем `x := 10`.
2. `p := &x`.
3. `*p = 100`.
4. Печатаем `x`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	x := 10
	p := &x

	fmt.Printf("Исходный x:         %d\n", x)

	*p = 100 // Запись 100 по адресу в указателе p

	fmt.Printf("Обновленный x:      %d (УСПЕШНО ИЗМЕНЕН!)\n", x)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Исходный x:         10
# Обновленный x:      100 (УСПЕШНО ИЗМЕНЕН!)"""
            }
        ],
        "under_the_hood": """
Запись 8 байт по адресу `p`.
""",
        "pitfalls": """
- Присвоение `p = 100` (ошибка компиляции `cannot use 100 as *int`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем отличие `p` от `*p`?»
**Ответ:** `p` — это сам указатель (адрес в памяти), а `*p` — это значение, расположенное по этому адресу.
"""
    },
    {
        "num": 29,
        "title": "Взятие адреса отдельного элемента массива &arr[0] и мутация через указатель",
        "task": "Получи указатель на элемент массива (или среза) &arr[0]. Измени элемент через указатель.",
        "theory": """
**Указатель на элемент коллекции `&arr[i]`:**
- Позволяет получить прямой доступ к конкретному элементу массива или среза;
- Изменение `*ptr = val` обновляет элемент в коллекции.
""",
        "step_by_step": """
1. Создаем массив `arr := [3]string{"Go", "Python", "Java"}`.
2. Берем `pFirst := &arr[0]`.
3. Присваиваем `*pFirst = "Golang Highload"`.
4. Печатаем массив.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	arr := [3]string{"Go", "Python", "Java"}
	fmt.Printf("До изменения:    %v\n", arr)

	pFirst := &arr[0] // Указатель на первый элемент
	*pFirst = "Golang Highload"

	fmt.Printf("После изменения: %v\n", arr)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До изменения:    [Go Python Java]
# После изменения: [Golang Highload Python Java]"""
            }
        ],
        "under_the_hood": """
Указатель ссылается на смещение `arr + 0`.
""",
        "pitfalls": """
- Сохранение `&s[0]` для среза, который впоследствии растет через `append`: срез переедет в новый буфер, а указатель останется указывать на старый массив!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему опасно сохранять указатель на элемент среза `&s[i]` при динамическом добавлении элементов?»
**Ответ:** При реаллокации среза базовый массив копируется в новую область памяти, и сохраненный указатель перестает указывать на актуальный элемент среза.
"""
    },
    {
        "num": 30,
        "title": "Сравнение указателей с помощью оператора равенства == (Identity vs Equality)",
        "task": "Сравни два указателя на один и тот же адрес с помощью ==.",
        "theory": """
**Семантика сравнения указателей `p1 == p2`:**
- Два указателя равны (`true`), если они указывают на **один и тот же адрес памяти** либо оба равны `nil`;
- Сравнение самих значений выполняется через `*p1 == *p2`.
""",
        "step_by_step": """
1. Создаем `a := 42`, `b := 42`.
2. Создаем `p1 := &a`, `p2 := &a`, `p3 := &b`.
3. Сравниваем указатели.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	a, b := 42, 42

	p1 := &a
	p2 := &a
	p3 := &b

	fmt.Printf("p1 == p2 (один адрес): %t (адрес: %p)\n", p1 == p2, p1)
	fmt.Printf("p1 == p3 (разные адреса): %t (p1: %p, p3: %p)\n", p1 == p3, p1, p3)
	fmt.Printf("*p1 == *p3 (значения равны): %t\n", *p1 == *p3)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# p1 == p2 (один адрес): true (адрес: 0xc000018030)
# p1 == p3 (разные адреса): false (p1: 0xc000018030, p3: 0xc000018038)
# *p1 == *p3 (значения равны): true"""
            }
        ],
        "under_the_hood": """
Сравнение 64-битных адресов инструкцией `CMPQ`.
""",
        "pitfalls": """
- Сравнение `p1 == p3` в надежде сравнить содержимое данных.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Когда `&struct{}` вернет одинаковый адрес для двух разных переменных?»
**Ответ:** Для пустых структур `struct{}` компилятор может вернуть один и тот же глобальный адрес `zerobase` (`0x...`).
"""
    },
    {
        "num": 31,
        "title": "Выделение памяти под целое число функцией new(int) и вывод адреса",
        "task": "Функция new(): Выделите память под переменную типа int с помощью встроенной функции new(). Присвойте ей значение и выведите её адрес и значение.",
        "theory": """
Базовое использование встроенной функции `new()`.
""",
        "step_by_step": """
1. Создаем `ptr := new(int)`.
2. Присваиваем `*ptr = 1024`.
3. Печатаем адрес и значение.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	ptr := new(int)
	*ptr = 1024

	fmt.Printf("Выделенный адрес: %p\n", ptr)
	fmt.Printf("Значение в памяти: %d\n", *ptr)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Выделенный адрес: 0xc000018030
# Значение в памяти: 1024"""
            }
        ],
        "under_the_hood": """
Вызов рантайма для выделения 8 байт.
""",
        "pitfalls": """
- Забыть разыменовать указатель при чтении.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Освобождается ли память, выделенная через `new`, вручную как `free()` в C?»
**Ответ:** НЕТ! Память автоматически управляется сборщиком мусора (Garbage Collector) на основе алгоритма Tracing Tri-color Mark-and-Sweep.
"""
    },
    {
        "num": 32,
        "title": "Функция AppendToSlice(s, val) []int и правила переприсваивания срезов",
        "task": "Напиши функцию AppendToSlice(s []int, val int) []int, которая возвращает новый слайс. Покажи, что нужно присваивать результат: s = AppendToSlice(s, 5). Объясни, когда происходит реаллокация.",
        "theory": """
Идиоматичный возврат среза из функции.
""",
        "step_by_step": """
1. Пишем `AppendToSlice(s []int, val int) []int`.
2. Возвращаем `append(s, val)`.
3. Демонстрируем обязательное переприсваивание `s = AppendToSlice(s, ...)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func AppendToSlice(s []int, val int) []int {
	return append(s, val)
}

func main() {
	s := []int{1, 2}
	fmt.Printf("1. Исходный срез: %v (cap=%d)\n", s, cap(s))

	// ОБЯЗАТЕЛЬНО переприсваиваем результат:
	s = AppendToSlice(s, 3)
	fmt.Printf("2. После append:  %v (cap=%d)\n", s, cap(s))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Исходный срез: [1 2] (cap=2)
# 2. После append:  [1 2 3] (cap=4)"""
            }
        ],
        "under_the_hood": """
При исчерпании `cap` функция `growslice` удваивает емкость и копирует элементы.
""",
        "pitfalls": """
- Вызов `AppendToSlice(s, 5)` без присваивания результата `s = ...`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `append` возвращает срез, а не изменяет его на месте?»
**Ответ:** Потому что при нехватке емкости `append` выделяет совершенно новый массив в памяти и возвращает обновленный `SliceHeader` с новым указателем `Data`.
"""
    },
    {
        "num": 33,
        "title": "Сравнение способов выделения: p1 := new(int) vs var x int; p2 := &x",
        "task": "Сравнение способов выделения: Сравните создание указателя через p1 := new(int) и var x int; p2 := &x. Будут ли они вести себя одинаково при работе с памятью?",
        "theory": """
**Сравнение `new(T)` и `&x`:**
- Оба варианта создают зануленную переменную типа `T` и возвращают указатель `*T`;
- С точки зрения оптимизатора компилятора оба выражения абсолютно эквивалентны;
- `var x int; p2 := &x` дает переменной имя `x` в текущем скоупе, а `new(int)` создает анонимное значение.
""",
        "step_by_step": """
1. Создаем `p1 := new(int)`.
2. Создаем `var x int; p2 := &x`.
3. Сравниваем поведение.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	// Вариант 1: new()
	p1 := new(int)
	*p1 = 10

	// Вариант 2: &x
	var x int
	p2 := &x
	*p2 = 10

	fmt.Printf("p1: %p -> %d\n", p1, *p1)
	fmt.Printf("p2: %p -> %d\n", p2, *p2)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# p1: 0xc000018030 -> 10
# p2: 0xc000018038 -> 10"""
            }
        ],
        "under_the_hood": """
Идентичный ассемблерный код в SSA бэкенде компилятора.
""",
        "pitfalls": """
- Заблуждение, будто `new()` ВСЕГДА аллоцирует в куче (если переменная не убегает, компилятор разместит ее на стеке!).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Обязан ли `new(T)` аллоцировать память в куче (Heap)?»
**Ответ:** НЕТ! Компилятор Go проводит Escape-анализ: если значение не покидает стек функции, `new(T)` размещается на стеке без оверхеда на GC.
"""
    },
    {
        "num": 34,
        "title": "Мутация значения переменной любого типа через reflect.ValueOf(ptr).Elem()",
        "task": "Напишите функцию, меняющую значение переменной любого типа через interface{} и * с использованием reflect (дополнительно).",
        "theory": """
**Рефлексия и мутация через указатели (`reflect.Value.Elem()`):**
- Для изменения переменной через `reflect` необходимо передать **указатель**;
- Метод `reflect.ValueOf(ptr).Elem()` получает разыменованное изменяемое значение (`CanSet() == true`).
""",
        "step_by_step": """
1. Пишем `SetReflect(ptr any, newVal any)`.
2. Проверяем `v.Kind() == reflect.Pointer`.
3. Записываем `elem.Set(reflect.ValueOf(newVal))`.
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

func SetReflect(ptr any, newVal any) {
	val := reflect.ValueOf(ptr)
	if val.Kind() != reflect.Pointer || val.IsNil() {
		return
	}

	elem := val.Elem()
	if elem.CanSet() {
		elem.Set(reflect.ValueOf(newVal))
	}
}

func main() {
	count := 10
	name := "Golang"

	SetReflect(&count, 99)
	SetReflect(&name, "Go Workout")

	fmt.Printf("count: %d\n", count)
	fmt.Printf("name:  %s\n", name)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# count: 99
# name:  Go Workout"""
            }
        ],
        "under_the_hood": """
Рефлексия проверяет флаги settability в структуре `reflect.Value`.
""",
        "pitfalls": """
- Передача значения без указателя `SetReflect(count, 99)`: вызовет панику или `CanSet() == false`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `json.Unmarshal(data, &v)` требует обязательной передачи указателя?»
**Ответ:** Потому что рефлексия может записать десериализованные данные в структуру только тогда, когда передан указатель (`CanSet() == true`).
"""
    },
    {
        "num": 35,
        "title": "Передача примитива по значению IncrementByValue(x int) и изоляция стекового кадра",
        "task": "Напиши функцию IncrementByValue(x int), которая увеличивает x на 1. Вызови из main и покажи, что оригинальная переменная не изменилась. Объясни почему.",
        "theory": """
Строгая изоляция стековых кадров функций.
""",
        "step_by_step": """
1. Пишем `IncrementByValue(x int)`.
2. Делаем `x++`.
3. Демонстрируем неизменность исходной переменной.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func IncrementByValue(x int) {
	x++
	fmt.Printf("Внутри IncrementByValue: x = %d\n", x)
}

func main() {
	val := 5
	fmt.Printf("До вызова:               val = %d\n", val)

	IncrementByValue(val)

	fmt.Printf("После вызова:            val = %d (ОРИГИНАЛ НЕ ИЗМЕНИЛСЯ!)\n", val)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До вызова:               val = 5
# Внутри IncrementByValue: x = 6
# После вызова:            val = 5 (ОРИГИНАЛ НЕ ИЗМЕНИЛСЯ!)"""
            }
        ],
        "under_the_hood": """
Параметр `x` размещается в локальном регистре или стеке вызываемой функции.
""",
        "pitfalls": """
- Ожидание мутации оригинальной переменной без передачи `*int`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова базовая модель передачи параметров в Go?»
**Ответ:** В Go ВСЕ параметры передаются исключительно по значению (Pass by Value).
"""
    },
    {
        "num": 36,
        "title": "Каверза со ссылкой на переменную цикла в отложенных горутинах/замыканиях",
        "task": "Объясните и исправьте ситуацию: в цикле for, переменная используется в замыкании, запускаемом позже (каверза со ссылкой).",
        "theory": """
Сравнение паттернов передачи аргументов в горутины.
""",
        "step_by_step": """
1. Демонстрируем безопасную передачу аргумента в горутину `go func(v int) { ... }(val)`.
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
	items := []string{"A", "B", "C"}

	for _, item := range items {
		wg.Add(1)
		// ЭТАЛОННЫЙ ПАТТЕРН: передаем item аргументом функции:
		go func(val string) {
			defer wg.Done()
			fmt.Printf("Обработан элемент: %s\n", val)
		}(item)
	}

	wg.Wait()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Обработан элемент: C
# Обработан элемент: A
# Обработан элемент: B"""
            }
        ],
        "under_the_hood": """
Значение `item` копируется в стек горутины при запуске.
""",
        "pitfalls": """
- Прямой захват внешней переменной в горутине в старых версиях Go до 1.22.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какой линтер находит гонки данных при захвате переменных цикла?»
**Ответ:** Встроенный детектор гонок `go run -race` и анализатор `go vet` (проверка `loopclosure`).
"""
    },
    {
        "num": 37,
        "title": "Escape-анализ: функция GetLocalPointer() *int и диагностика компилятора -gcflags='-m'",
        "task": "Escape-анализ (Возврат указателя): Напишите функцию GetLocalPointer() *int, которая создает локальную переменную внутри себя, присваивает ей значение и возвращает её адрес. Безопасно ли это в Go? (Изучите, почему компилятор Go переносит такую переменную в кучу — Escape Analysis, запустив сборку с флагом go build -gcflags=\"-m\").",
        "theory": """
**Подробный разбор Escape Analysis:**
- Компилятор строит граф направленной достижимости (Escape Graph);
- Если адрес локальной переменной возвращается наружу, компилятор генерирует вызов `runtime.newobject`;
- Проверить это можно командой `go build -gcflags="-m"`.
""",
        "step_by_step": """
1. Пишем `GetLocalPointer() *int`.
2. Возвращаем `&val`.
3. Анализируем вывод компилятора.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func GetLocalPointer() *int {
	val := 777 // moved to heap: val
	return &val
}

func main() {
	p := GetLocalPointer()
	fmt.Printf("Указатель на значение из кучи: %p -> %d\n", p, *p)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go build -gcflags="-m" main.go
# ./main.go:6:2: moved to heap: val
# ./main.go:12:12: ... argument does not escape
go run main.go
# Указатель на значение из кучи: 0xc000018030 -> 777"""
            }
        ],
        "under_the_hood": """
Экранирование переменной из стека в кучу.
""",
        "pitfalls": """
- Иллюзия, что возврат указателей всегда «быстрее»: аллокация в куче создает работу сборщику мусора.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что дороже: скопировать структуру 32 байта или вернуть указатель на нее?»
**Ответ:** Скопировать 32 байта на стеке в 10 раз быстрее, чем аллоцировать структуру в куче через `new` с последующей сборкой мусора.
"""
    },
    {
        "num": 38,
        "title": "Обнуление значения по указателю Zeroify(val *int)",
        "task": "Модификация в функции: Напишите функцию Zeroify(val *int), которая устанавливает значение по указателю в 0. Проверьте её работу на локальной переменной.",
        "theory": """
Сброс значения через разыменование.
""",
        "step_by_step": """
1. Пишем `Zeroify(val *int)`.
2. Присваиваем `*val = 0`.
3. Тестируем в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func Zeroify(val *int) {
	if val != nil {
		*val = 0
	}
}

func main() {
	score := 500
	fmt.Printf("До Zeroify:    %d\n", score)

	Zeroify(&score)

	fmt.Printf("После Zeroify: %d\n", score)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До Zeroify:    500
# После Zeroify: 0"""
            }
        ],
        "under_the_hood": """
Инструкция `MOVQ $0, (AX)`.
""",
        "pitfalls": """
- Вызов на `nil`-указателе без проверки.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как обнулить массив `[1000]int` за одну инструкцию?»
**Ответ:** `*arr = [1000]int{}` (компилятор оптимизирует это в быстрый `memclr`).
"""
    },
    {
        "num": 39,
        "title": "Опасность записи в nil-мапу NilMap(m map[string]int) и правильная инициализация",
        "task": "Напиши функцию NilMap(m map[string]int) и попробуй записать в неё. Что произойдёт с nil мапой? Объясни панику и как её избежать.",
        "theory": """
**Nil Map Mechanics:**
- Чтение из nil-мапы безопасно (возвращает Zero Value);
- Запись в nil-мапу `m["key"] = 1` вызывает фатальную панику `panic: assignment to entry in nil map`;
- Для записи мапа обязана быть инициализирована через `make(map[K]V)`.
""",
        "step_by_step": """
1. Демонстрируем панику записи в nil-мапу.
2. Перехватываем через `recover()`.
3. Показываем исправление через `make`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func NilMapDemo(m map[string]int) {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("⚠️ Перехвачена паника: %v\n", r)
		}
	}()

	m["key"] = 100 // ПАНИКА!
}

func main() {
	var m map[string]int // nil-мапа
	NilMapDemo(m)

	// Исправленный вариант:
	validMap := make(map[string]int)
	validMap["key"] = 100
	fmt.Printf("После make: validMap['key'] = %d\n", validMap["key"])
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# ⚠️ Перехвачена паника: assignment to entry in nil map
# После make: validMap['key'] = 100"""
            }
        ],
        "under_the_hood": """
`runtime.mapassign` проверяет заголовок `hmap`: если `h == nil`, вызывается `panic("assignment to entry in nil map")`.
""",
        "pitfalls": """
- Объявление `var m map[string]int` с последующей записью без вызова `make`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему чтение из nil-мапы разрешено, а запись запрещена?»
**Ответ:** Чтение не требует создания структуры `hmap` и бакетов, а запись требует инициализации хэш-таблицы в куче.
"""
    },
    {
        "num": 40,
        "title": "Разыменование указателя *p и чтение значения из памяти",
        "task": "Разыменование (Dereferencing): Имея указатель из упр. 76, получи значение по этому адресу, используя оператор *, и выведи его.",
        "theory": """
Закрепление синтаксиса разыменования.
""",
        "step_by_step": """
1. Создаем переменную `target := 888`.
2. Получаем указатель `p := &target`.
3. Разыменовываем `*p`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	target := 888
	p := &target

	fmt.Printf("Разыменованное значение: %d\n", *p)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Разыменованное значение: 888"""
            }
        ],
        "under_the_hood": """
Чтение из памяти по адресу.
""",
        "pitfalls": """
- Опечатки в синтаксисе.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каков приоритет унарного оператора `*`?»
**Ответ:** Такой же, как у унарного `&` и `!`.
"""
    },
    {
        "num": 41,
        "title": "Неинициализированный указатель var p *int и фиксация паники nil pointer dereference",
        "task": "Nil-указатель: Создайте указатель типа *int без инициализации. Попробуйте вывести его значение (оно должно быть nil). Попробуйте разыменовать его (*p = 5) и зафиксируйте панику (nil pointer dereference).",
        "theory": """
Демонстрация нулевого состояния указателя.
""",
        "step_by_step": """
1. Создаем `var p *int`.
2. Разыменовываем `*p = 5` в защитном блоке.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	var p *int
	fmt.Printf("1. Значение p: %v (isNil: %t)\n", p, p == nil)

	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("2. Зафиксирована паника: %v\n", r)
		}
	}()

	*p = 5 // Паника
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. Значение p: <nil> (isNil: true)
# 2. Зафиксирована паника: runtime error: invalid memory address or nil pointer dereference"""
            }
        ],
        "under_the_hood": """
Обработка аппаратного прерывания `SIGSEGV`.
""",
        "pitfalls": """
- Запись по адресу `nil`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Является ли `nil` ключевым словом в Go?»
**Ответ:** НЕТ! `nil` — это предопределенный идентификатор (Predeclared Identifier), представляющий нулевое значение указателей, интерфейсов, слайсов, мап, каналов и функций.
"""
    },
    {
        "num": 42,
        "title": "Попытка перетереть локальный указатель TryToReassign(p *int) и неизменность внешнего адреса",
        "task": "Попытка перетереть сам указатель: Напишите функцию TryToReassign(p *int). Внутри функции попробуйте присвоить самому указателю новый адрес p = new(int). Изменится ли оригинальный указатель, который передавали извне?",
        "theory": """
**Копирование указателя при передаче параметров:**
- Параметр `p` внутри `TryToReassign(p *int)` — это **локальная копия адреса**;
- Переприсваивание `p = new(int)` меняет только локальную переменную `p`;
- Исходный указатель в `main()` **продолжает указывать на старую переменную**.
""",
        "step_by_step": """
1. Пишем `TryToReassign(p *int)`.
2. Выполняем `p = new(int); *p = 999`.
3. Проверяем оригинальный указатель в `main()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func TryToReassign(p *int) {
	p = new(int) // Перезаписывает ЛОКАЛЬНУЮ копию указателя!
	*p = 999
	fmt.Printf("Внутри TryToReassign: p = %p, *p = %d\n", p, *p)
}

func main() {
	x := 42
	ptr := &x

	fmt.Printf("1. До вызова:         ptr = %p, *ptr = %d\n", ptr, *ptr)

	TryToReassign(ptr)

	fmt.Printf("2. После вызова:      ptr = %p, *ptr = %d (НЕ ИЗМЕНИЛСЯ!)\n", ptr, *ptr)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. До вызова:         ptr = 0xc000018030, *ptr = 42
# Внутри TryToReassign: p = 0xc000018038, *p = 999
# 2. После вызова:      ptr = 0xc000018030, *ptr = 42 (НЕ ИЗМЕНИЛСЯ!)"""
            }
        ],
        "under_the_hood": """
Локальный регистр `AX` перезаписывается новым адресом из `newobject`.
""",
        "pitfalls": """
- Ожидание, что `p = ...` изменит внешний указатель (для этого нужен `**int`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как заставить функцию изменить внешний указатель `ptr`?»
**Ответ:** Принять двойной указатель `func Reassign(p **int)` и выполнить `*p = new(int)`.
"""
    },
    {
        "num": 43,
        "title": "Массив указателей [3]*int и пакетная модификация связанных переменных в цикле",
        "task": "Массив указателей: Создайте массив из 3 указателей на int. Присвойте каждому элементу адрес разных переменных. В цикле измените значения всех переменных через массив указателей.",
        "theory": """
**Массив указателей `[N]*T`:**
- Хранит $N$ адресов памяти;
- Позволяет модифицировать группу разрозненных переменных в едином цикле.
""",
        "step_by_step": """
1. Создаем переменные `a, b, c := 10, 20, 30`.
2. Создаем массив `ptrs := [3]*int{&a, &b, &c}`.
3. В цикле умножаем каждое значение на 10.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	a, b, c := 10, 20, 30
	ptrs := [3]*int{&a, &b, &c}

	fmt.Printf("До цикла:    a=%d, b=%d, c=%d\n", a, b, c)

	for _, p := range ptrs {
		*p *= 10 // Умножаем значение по каждому адресу
	}

	fmt.Printf("После цикла: a=%d, b=%d, c=%d\n", a, b, c)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# До цикла:    a=10, b=20, c=30
# После цикла: a=100, b=200, c=300"""
            }
        ],
        "under_the_hood": """
Последовательный обход 8-байтных указателей в массиве.
""",
        "pitfalls": """
- Наличие `nil` в одном из элементов массива (необходима проверка `if p != nil`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каков размер массива `[3]*int` в памяти?»
**Ответ:** $3 \times 8 = 24$ байта на 64-битной архитектуре.
"""
    },
    {
        "num": 44,
        "title": "Реализация односвязного списка (Singly Linked List) на структуре Node с полем Next *Node",
        "task": "Указатели внутри структур: Создайте структуру Node, у которой есть поле Value int и поле Next *Node. Соедините три такие структуры в цепочку (связный список) и обойдите его с помощью цикла for, выводя значения.",
        "theory": """
**Самоссылающиеся структуры (Self-Referential Structs):**
- Структура `Node` не может содержать поле `Next Node` по значению (рекурсивный бесконечный размер);
- Поле `Next *Node` хранит 8-байтный указатель на следующий узел;
- Конец списка обозначается `Next == nil`.
""",
        "step_by_step": """
1. Создаем структуру `type Node struct { Value int; Next *Node }`.
2. Создаем цепочку `n1 -> n2 -> n3`.
3. Обходим список циклом `for curr := head; curr != nil; curr = curr.Next`.
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

func main() {
	// Создаем цепочку: 10 -> 20 -> 30 -> nil
	n3 := &Node{Value: 30, Next: nil}
	n2 := &Node{Value: 20, Next: n3}
	n1 := &Node{Value: 10, Next: n2}

	fmt.Print("Обход связного списка: ")
	curr := n1
	for curr != nil {
		fmt.Printf("%d -> ", curr.Value)
		curr = curr.Next
	}
	fmt.Println("nil")
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Обход связного списка: 10 -> 20 -> 30 -> nil"""
            }
        ],
        "under_the_hood": """
Узлы связного списка распределены по куче (Linked Nodes).
""",
        "pitfalls": """
- Попытка объявить `type Node struct { Next Node }` (ошибка компиляции `invalid recursive type Node`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему связный список `Node` уступает срезу `[]int` по скорости последовательного обхода?»
**Ответ:** Потому что элементы среза лежат непрерывно в памяти и загружаются в быстрый кэш процессора (L1/L2 Cache Lines), а узлы связного списка разбросаны по куче, вызывая частые промахи кэша (Cache Misses).
"""
    },
    {
        "num": 45,
        "title": "Опциональные поля структуры через указатели Profile { Name string, Age *int }",
        "task": "Опциональные поля через указатели: Создайте структуру Profile с полями Name string и Age *int. Напишите логику: если Age равен nil, выводить \"Возраст не указан\", иначе выводить реальное значение. Инициализируйте два профиля (с указанием возраста и без).",
        "theory": """
**Паттерн опциональных полей (Optional Fields / Nullable):**
- В Go примитивный `int` всегда имеет `0`, поэтому нельзя отличить «возраст равен 0» от «возраст не указан»;
- Поле `Age *int` позволяет точно различить `nil` (поле отсутствует) и `&0` (поле равно 0);
- Стандарт де-факто для JSON REST API (`omitempty`).
""",
        "step_by_step": """
1. Создаем структуру `Profile{Name string, Age *int}`.
2. Создаем `p1` (без возраста, `Age: nil`).
3. Создаем `p2` (с возрастом `Age: &age`).
4. Форматируем вывод.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

type Profile struct {
	Name string
	Age  *int // Опциональное поле (nil = не указано)
}

func (p Profile) PrintInfo() {
	if p.Age == nil {
		fmt.Printf("Профиль %-10s | Возраст: не указан\n", p.Name)
	} else {
		fmt.Printf("Профиль %-10s | Возраст: %d лет\n", p.Name, *p.Age)
	}
}

func main() {
	ageVal := 25

	p1 := Profile{Name: "Аноним", Age: nil}
	p2 := Profile{Name: "Сергей", Age: &ageVal}

	p1.PrintInfo()
	p2.PrintInfo()
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Профиль Аноним     | Возраст: не указан
# Профиль Сергей     | Возраст: 25 лет"""
            }
        ],
        "under_the_hood": """
Сериализатор `encoding/json` сериализует `nil` как JSON `null`.
""",
        "pitfalls": """
- Разыменование `*p.Age` без предварительной проверки `if p.Age != nil`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в Go сериализовать JSON с опциональными полями без отправки `0` или `""`?»
**Ответ:** Объявить поля как указатели `*int`, `*string` с тегом `json:"age,omitempty"`.
"""
    },
    {
        "num": 46,
        "title": "Безопасное разыменование: паттерн Guard Clause if p != nil",
        "task": "Безопасное разыменование: Защити код проверки указателя проверкой if p != nil перед разыменованием.",
        "theory": """
Шаблон защитных условий (Guard Clauses) для исключения паник в бизнес-логике.
""",
        "step_by_step": """
1. Пишем функцию `SafePrint(p *int)`.
2. Добавляем проверку `if p == nil { fmt.Println("указатель nil"); return }`.
3. Печатаем значение.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func SafePrint(p *int) {
	if p == nil {
		fmt.Println("⚠️ Значение недоступно (указатель nil)")
		return
	}
	fmt.Printf("Значение: %d\n", *p)
}

func main() {
	var nilPtr *int
	val := 42

	SafePrint(nilPtr)
	SafePrint(&val)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# ⚠️ Значение недоступно (указатель nil)
# Значение: 42"""
            }
        ],
        "under_the_hood": """
Быстрая проверка `TESTQ AX, AX`.
""",
        "pitfalls": """
- Пропуск проверки в высоконагруженных методах.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какой оверхед дает проверка `if p == nil`?»
**Ответ:** 1 такт процессора (благодаря предсказателю переходов Branch Predictor проверка выполняется почти бесплатно).
"""
    },
    {
        "num": 47,
        "title": "Сравнение указателей: Identity адресов (&a == &b) против Equality значений (*p1 == *p2)",
        "task": "Сравнение указателей: Создай две разные переменные с одинаковым значением (например, 10). Сравни их адреса (&a == &b). Пойми, почему результат false. Затем присвой два указателя на одну и ту же переменную и убедись, что они равны.",
        "theory": """
**Различие идентичности (Identity) и равенства (Equality):**
- `&a == &b`: сравнивает физические адреса в оперативной памяти (два разных объекта в памяти всегда имеют разные адреса);
- `*p1 == *p2`: сравнивает логические значения по этим адресам.
""",
        "step_by_step": """
1. Создаем `a, b := 10, 10`.
2. Сравниваем `&a == &b` (false).
3. Создаем `p1 := &a`, `p2 := &a`.
4. Сравниваем `p1 == p2` (true).
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	a := 10
	b := 10

	// 1. Две разные переменные имеют РАЗНЫЕ адреса памяти:
	fmt.Printf("1. &a == &b: %t (адрес a: %p, адрес b: %p)\n", &a == &b, &a, &b)
	fmt.Printf("2. *(&a) == *(&b): %t (значения одинаковы: 10 == 10)\n", *(&a) == *(&b))

	// 2. Два указателя на одну и ту же переменную:
	p1 := &a
	p2 := &a
	fmt.Printf("3. p1 == p2: %t (указывают на один и тот же адрес: %p)\n", p1 == p2, p1)
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# 1. &a == &b: false (адрес a: 0xc000018030, адрес b: 0xc000018038)
# 2. *(&a) == *(&b): true (значения одинаковы: 10 == 10)
# 3. p1 == p2: true (указывают на один и тот же адрес: 0xc000018030)"""
            }
        ],
        "under_the_hood": """
Сравнение регистров с адресами памяти.
""",
        "pitfalls": """
- Использование `==` над указателями при проверке равенства структур.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как сравнивать структуры по значению, если у нас есть два указателя `u1, u2 *User`?»
**Ответ:** Разыменовать оба указателя: `*u1 == *u2`.
"""
    },
    {
        "num": 48,
        "title": "Инициализация массива указателей [3]*int адресами трех независимых переменных",
        "task": "Массив указателей: Создай массив [3]*int. Проинициализируй его адресами трех разных переменных.",
        "theory": """
Закрепление синтаксиса массива указателей.
""",
        "step_by_step": """
1. Создаем `x, y, z := 1, 2, 3`.
2. Создаем `arr := [3]*int{&x, &y, &z}`.
3. Печатаем адреса и значения.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import "fmt"

func main() {
	x, y, z := 100, 200, 300
	var ptrArr [3]*int

	ptrArr[0] = &x
	ptrArr[1] = &y
	ptrArr[2] = &z

	for i, ptr := range ptrArr {
		fmt.Printf("Элемент #%d -> Адрес: %p, Значение: %d\n", i, ptr, *ptr)
	}
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# Элемент #0 -> Адрес: 0xc000018030, Значение: 100
# Элемент #1 -> Адрес: 0xc000018038, Значение: 200
# Элемент #2 -> Адрес: 0xc000018040, Значение: 300"""
            }
        ],
        "under_the_hood": """
Массив из 3 ячеек по 8 байт.
""",
        "pitfalls": """
- Забыть инициализировать один из элементов (останется `nil`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем отличие `[3]*int` от `*[3]int`?»
**Ответ:** `[3]*int` — это массив из трех указателей на целые числа. `*[3]int` — это один указатель на массив из трех целых чисел.
"""
    },
    {
        "num": 49,
        "title": "Исследование размеров типов через unsafe.Sizeof: инвариант 8-байтных указателей",
        "task": "Размер типов: Импортируй unsafe. Узнай с помощью unsafe.Sizeof размер переменной int64 и размер указателя *int64. Убедись, что размер указателя не зависит от того, на какой тип он указывает.",
        "theory": """
**Инвариант размеров указателей в архитектуре компьютера:**
- На 64-битной архитектуре (amd64, arm64) **ЛЮБОЙ указатель занимает ровно 8 байт**;
- Размер указателя не зависит от размера типа, на который он ссылается (`*bool` — 8 байт, `*byte` — 8 байт, `*[1000000]int` — 8 байт);
- Функция `unsafe.Sizeof` вычисляет размер типа на этапе компиляции с нулевыми накладными расходами.
""",
        "step_by_step": """
1. Импортируем `unsafe`.
2. Замеряем `unsafe.Sizeof` для различных типов и указателей на них.
3. Анализируем результаты.
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

type BigStruct struct {
	Buffer [1024]byte
}

func main() {
	var (
		b   bool
		i64 int64
		big BigStruct

		pBool   *bool
		pInt64  *int64
		pBig    *BigStruct
	)

	fmt.Println("=== РАЗМЕРЫ ТИПОВ В ПАМЯТИ (unsafe.Sizeof) ===")
	fmt.Printf("1. bool:               %4d байт  | *bool:       %4d байт\n",
		unsafe.Sizeof(b), unsafe.Sizeof(pBool))
	fmt.Printf("2. int64:              %4d байт  | *int64:      %4d байт\n",
		unsafe.Sizeof(i64), unsafe.Sizeof(pInt64))
	fmt.Printf("3. BigStruct (1024B):  %4d байт  | *BigStruct:  %4d байт\n",
		unsafe.Sizeof(big), unsafe.Sizeof(pBig))
}"""
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": r"""go run main.go
# === РАЗМЕРЫ ТИПОВ В ПАМЯТИ (unsafe.Sizeof) ===
# 1. bool:                  1 байт  | *bool:          8 байт
# 2. int64:                 8 байт  | *int64:         8 байт
# 3. BigStruct (1024B):  1024 байт  | *BigStruct:     8 байт"""
            }
        ],
        "under_the_hood": """
`unsafe.Sizeof` возвращает константу компилятора на основе структуры ABI целевой платформы.
""",
        "pitfalls": """
- Передача `*bool` вместо `bool` для «экономии памяти»: указатель `*bool` занимает 8 байт против 1 байта у самого `bool`!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему передача `*bool` или `*byte` в функцию неэффективна по памяти?»
**Ответ:** Потому что сам `bool` занимает 1 байт, а указатель на него — 8 байт (в 8 раз больше), плюс создает аллокацию в куче и дополнительное косвенное чтение из памяти.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 2: {len(exercises)} exercises.")
