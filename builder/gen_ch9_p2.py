# Chapter 9 Part 2: Exercises 16 to 31

exercises = [
    {
        "num": 16,
        "title": "Указатель как ключ мапы map[*Point]string: сравнение адресов памяти vs значений полей",
        "task": "Указатель как ключ: Измени тип ключа на *Point. Создай две разные переменные с одинаковыми координатами X и Y. Запиши значение по первому указателю, а попытайся прочитать по второму. Изучи, почему вернется 0 (адреса-то разные!).",
        "theory": """
**Специфика указателей как ключей мапы:**
- При использовании указателя `*Point` в качестве ключа хэшируется и сравнивается **сам числовой адрес ячейки памяти**, а НЕ поля структуры;
- Две разные переменные `p1 := &Point{1, 2}` и `p2 := &Point{1, 2}` имеют разные адреса (`p1 != p2`), поэтому `m[p2]` вернет пустую строку, даже если их координаты идентичны.
""",
        "step_by_step": """
1. Создаем структуру `Point{X, Y int}`.
2. Создаем `m := make(map[*Point]string)`.
3. Создаем два разных указателя с одинаковыми `X=10, Y=20`.
4. Записываем по `p1`, читаем по `p2`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type Point struct {
	X, Y int
}

func main() {
	m := make(map[*Point]string)

	p1 := &Point{X: 10, Y: 20}
	p2 := &Point{X: 10, Y: 20} // Те же координаты, но другой адрес!

	m[p1] = "База альянса"

	fmt.Printf("Адрес p1: %p | Адрес p2: %p\n", p1, p2)
	fmt.Printf("Поиск по p1: %q\n", m[p1])
	fmt.Printf("Поиск по p2: %q (НЕ НАЙДЕН, так как p1 != p2!)\n", m[p2])
}""",
                "note": "Указатели как ключи map"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Адрес p1: 0xc000014070 | Адрес p2: 0xc000014080
# Поиск по p1: "База альянса"
# Поиск по p2: "" (НЕ НАЙДЕН, так как p1 != p2!)""",
                "note": "Разные адреса дают разные ключи"
            }
        ],
        "under_the_hood": """
Хэшируется 8-байтный указатель `uintptr(unsafe.Pointer(p))` вместо содержимого структуры.
""",
        "pitfalls": """
- Использование `*SessionID` или `*UUID` в качестве ключей мап: два экземпляра с одинаковым строковым/байтовым значением не найдут друг друга.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Когда указатели в качестве ключей мапы оправданы?»
**Ответ:** Когда требуется идентифицировать конкретный живой экземпляр объекта в памяти (Identity Map, отслеживание активных соединений `*net.Conn` или подписчиков `*Client`).
"""
    },
    {
        "num": 17,
        "title": "Реализация структуры данных Множество (Set) на базе map[string]struct{} с операциями Union и Intersection",
        "task": "Реализуй множество (Set) через map[string]struct{}. Покажи, что struct{} занимает 0 байт. Реализуй методы: Add, Remove, Contains, Union, Intersection.",
        "theory": """
**Идиоматичный Set в Go:**
- Тип `struct{}` (пустая структура) имеет размер строго **0 байт** (`unsafe.Sizeof(struct{}{}) == 0`);
- В отличие от `map[T]bool`, который тратит 1 байт на значение в каждом бакете, `map[T]struct{}` не расходует память на значения;
- Все операции поиска, добавления и удаления выполняются за $O(1)$.
""",
        "step_by_step": """
1. Создаем тип `type StringSet map[string]struct{}`.
2. Реализуем методы `Add`, `Remove`, `Contains`, `Union`, `Intersection`.
3. Тестируем операции над множествами.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"unsafe"
)

type StringSet map[string]struct{}

func NewStringSet() StringSet {
	return make(StringSet)
}

func (s StringSet) Add(item string) {
	s[item] = struct{}{}
}

func (s StringSet) Remove(item string) {
	delete(s, item)
}

func (s StringSet) Contains(item string) bool {
	_, ok := s[item]
	return ok
}

func (s StringSet) Union(other StringSet) StringSet {
	res := NewStringSet()
	for k := range s {
		res.Add(k)
	}
	for k := range other {
		res.Add(k)
	}
	return res
}

func (s StringSet) Intersection(other StringSet) StringSet {
	res := NewStringSet()
	for k := range s {
		if other.Contains(k) {
			res.Add(k)
		}
	}
	return res
}

func main() {
	var empty struct{}
	fmt.Printf("Размер struct{}: %d байт (ZERO OVERHEAD!)\n\n", unsafe.Sizeof(empty))

	setA := NewStringSet()
	setA.Add("Go")
	setA.Add("Docker")
	setA.Add("Kubernetes")

	setB := NewStringSet()
	setB.Add("Go")
	setB.Add("Python")
	setB.Add("Rust")

	fmt.Printf("Set A: %v\n", setA)
	fmt.Printf("Set B: %v\n", setB)
	fmt.Printf("A ∩ B (Intersection): %v\n", setA.Intersection(setB))
	fmt.Printf("A ∪ B (Union):        %v\n", setA.Union(setB))
}""",
                "note": "Структура данных Set"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Размер struct{}: 0 байт (ZERO OVERHEAD!)
# 
# Set A: map[Docker:{} Go:{} Kubernetes:{}]
# Set B: map[Go:{} Python:{} Rust:{}]
# A ∩ B (Intersection): map[Go:{}]
# A ∪ B (Union):        map[Docker:{} Go:{} Kubernetes:{} Python:{} Rust:{}]""",
                "note": "Операции над множествами"
            }
        ],
        "under_the_hood": """
Рантайм оптимизирует бакеты: если размер `elemSize == 0`, массив значений вообще не аллоцируется.
""",
        "pitfalls": """
- Использование `map[string]bool` в высоконагруженных кэшах: при 100 млн записей это потратит лишние 100+ МБ памяти.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `struct{}{}` занимает 0 байт?»
**Ответ:** Потому что пустая структура не содержит полей и служит чисто синтаксическим маркером присутствия.
"""
    },
    {
        "num": 18,
        "title": "Удаление ключей через delete(m, key) и обработка несуществующих записей",
        "task": "Удалите элемент из мапы с помощью delete. Что произойдет (упадет ли программа), если попытаться удалить несуществующий ключ?",
        "theory": """
Закрепление контракта встроенной функции `delete`:
- Попытка удаления несуществующего ключа **гарантированно безопасна** и не приводит к панике;
- Длина мапы `len(m)` не изменяется.
""",
        "step_by_step": """
1. Создаем мапу `currencies := map[string]string{"USD": "Доллар", "EUR": "Евро"}`.
2. Удаляем `"USD"`.
3. Пытаемся удалить `"GBP"`.
4. Проверяем длину.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	currencies := map[string]string{
		"USD": "Доллар США",
		"EUR": "Евро",
	}

	fmt.Printf("До удаления:     len = %d | %v\n", len(currencies), currencies)

	// 1. Удаляем существующий ключ
	delete(currencies, "USD")
	fmt.Printf("После 'USD':     len = %d | %v\n", len(currencies), currencies)

	// 2. Удаляем отсутствующий ключ
	delete(currencies, "GBP")
	fmt.Printf("После 'GBP':     len = %d | %v (без ошибок!)\n", len(currencies), currencies)
}""",
                "note": "Поведение функции delete"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# До удаления:     len = 2 | map[EUR:Евро USD:Доллар США]
# После 'USD':     len = 1 | map[EUR:Евро]
# После 'GBP':     len = 1 | map[EUR:Евро] (без ошибок!)""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
При отсутствии совпадения `tophash` функция `mapdelete` завершается без мутаций.
""",
        "pitfalls": """
- Проверка `if _, ok := m[k]; ok { delete(m, k) }`: эта проверка избыточна, достаточно просто вызвать `delete(m, k)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Безопасен ли вызов `delete(m, k)` внутри цикла `for k := range m`?»
**Ответ:** ДА! Спецификация языка Go прямо гарантирует безопасность удаления текущего или любых других ключей во время итерации `range`.
"""
    },
    {
        "num": 19,
        "title": "Идемпотентность операции delete(m, key)",
        "task": "Удали элемент через delete(m, \"key\"). Покажи, что удаление несуществующего ключа не паникует и не возвращает ошибку.",
        "theory": """
Концепция идемпотентности в Go: повторные вызовы `delete` для одного и того же ключа приводят к идентичному результату без побочных эффектов.
""",
        "step_by_step": """
1. Создаем `m := map[string]int{"status": 200}`.
2. Вызываем `delete(m, "status")` 3 раза подряд.
3. Убеждаемся в стабильности работы.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	m := map[string]int{"status": 200}

	delete(m, "status")
	delete(m, "status") // Повторный вызов
	delete(m, "status") // Третий вызов

	fmt.Printf("Мапа после 3 вызовов delete: %v (len=%d)\n", m, len(m))
}""",
                "note": "Идемпотентность delete"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Мапа после 3 вызовов delete: map[] (len=0)""",
                "note": "Стабильная работа"
            }
        ],
        "under_the_hood": """
Никаких аллокаций или исключений.
""",
        "pitfalls": """
- Ожидание возвращаемого значения от `delete`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `delete` сделали процедурой (не возвращающей значения)?»
**Ответ:** Для исключения накладных расходов на проверки статуса в высокопроизводительном коде.
"""
    },
    {
        "num": 20,
        "title": "Паттерн Command Dispatcher на базе map[string]func(int, int) int",
        "task": "Мапа с функциями (Command Dispatcher): Создай map[string]func(int, int) int. Положи туда ключи \"add\", \"sub\", \"mul\" и соответствующие анонимные функции. Вызови нужную функцию по строковому ключу.",
        "theory": """
**Паттерн Command Dispatcher / Strategy:**
- Мапа функций первого класса `map[string]func(A, B) C` заменяет громоздкие каскады `switch/case` или цепочки `if/else`;
- Позволяет регистрировать новые команды и обработчики динамически во время работы сервиса (Plugin Architecture).
""",
        "step_by_step": """
1. Создаем `dispatcher := make(map[string]func(int, int) int)`.
2. Регистрируем `"add"`, `"sub"`, `"mul"`.
3. Пишем безопасную функцию выполнения `Execute`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type BinaryOp func(a, b int) int

func main() {
	dispatcher := map[string]BinaryOp{
		"add": func(a, b int) int { return a + b },
		"sub": func(a, b int) int { return a - b },
		"mul": func(a, b int) int { return a * b },
	}

	commands := []struct {
		op   string
		a, b int
	}{
		{"add", 10, 5},
		{"sub", 20, 7},
		{"mul", 6, 8},
		{"div", 100, 2}, // Неизвестная команда
	}

	for _, cmd := range commands {
		if fn, ok := dispatcher[cmd.op]; ok {
			fmt.Printf("Команда %-4s(%d, %d) -> Результат: %d\n", cmd.op, cmd.a, cmd.b, fn(cmd.a, cmd.b))
		} else {
			fmt.Printf("⚠️ Команда %-4s неизвестна диспетчеру\n", cmd.op)
		}
	}
}""",
                "note": "Command Dispatcher на map"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Команда add (10, 5) -> Результат: 15
# Команда sub (20, 7) -> Результат: 13
# Команда mul (6, 8) -> Результат: 48
# ⚠️ Команда div  неизвестна диспетчеру""",
                "note": "Динамический вызов функций"
            }
        ],
        "under_the_hood": """
Значением мапы является 8-байтный указатель на дескриптор функции. Вызов `fn()` происходит через косвенный переход `CALL RAX`.
""",
        "pitfalls": """
- Вызов `dispatcher[cmd](a, b)` без проверки `comma-ok`: если ключ отсутствует, вернется `nil`, и вызов `nil(a, b)` вызовет панику `nil pointer dereference`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Где в стандартной библиотеке Go используется мапа функций?»
**Ответ:** В роутере `http.ServeMux` (для сопоставления URL-путей с `http.HandlerFunc`) и в пакете `rpc`.
"""
    },
    {
        "num": 21,
        "title": "Интерактивный CLI-калькулятор на базе таблицы операций map[string]func",
        "task": "Создай мапу функций: map[string]func(int, int) int. Заполни операциями add, sub, mul, div. Используй как калькулятор: пользователь вводит операцию, программа вызывает соответствующую функцию.",
        "theory": """
Расширение Command Dispatcher с валидацией деления на ноль.
""",
        "step_by_step": """
1. Реализуем безопасные функции операций.
2. Обрабатываем деление на ноль.
3. Тестируем калькулятор.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	calc := map[string]func(int, int) (int, error){
		"add": func(a, b int) (int, error) { return a + b, nil },
		"sub": func(a, b int) (int, error) { return a - b, nil },
		"mul": func(a, b int) (int, error) { return a * b, nil },
		"div": func(a, b int) (int, error) {
			if b == 0 {
				return 0, fmt.Errorf("деление на ноль запрещено")
			}
			return a / b, nil
		},
	}

	tests := []struct {
		op   string
		a, b int
	}{
		{"add", 100, 50},
		{"div", 100, 4},
		{"div", 100, 0},
	}

	for _, t := range tests {
		fn, ok := calc[t.op]
		if !ok {
			fmt.Printf("Операция %s не поддерживается\n", t.op)
			continue
		}
		res, err := fn(t.a, t.b)
		if err != nil {
			fmt.Printf("Ошибка при %s(%d, %d): %v\n", t.op, t.a, t.b, err)
		} else {
			fmt.Printf("Успех: %s(%d, %d) = %d\n", t.op, t.a, t.b, res)
		}
	}
}""",
                "note": "Калькулятор на map функций"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Успех: add(100, 50) = 150
# Успех: div(100, 4) = 25
# Ошибка при div(100, 0): деление на ноль запрещено""",
                "note": "Результаты вычислений"
            }
        ],
        "under_the_hood": """
Компилятор оптимизирует сигнатуру функций через единый интерфейсный тип.
""",
        "pitfalls": """
- Игнорирование проверки деления на ноль внутри анонимных функций.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каковы преимущества таблицы диспетчеризации перед `switch-case` при добавлении 50 новых операций?»
**Ответ:** Соответствие принципу Open/Closed (SOLID): добавление новых операций не требует модификации основного кода выполнения, операции можно регистрировать из внешних модулей через `RegisterOp(name, fn)`.
"""
    },
    {
        "num": 22,
        "title": "Инициализация через make(map[K]V) и исправление паники записи в nil",
        "task": "Паника при инициализации: Объявите мапу var m map[string]int без инициализации. Попробуйте прочитать ключ — что вернет Go? Теперь попробуйте записать значение m[\"key\"] = 1. Зафиксируйте панику. Инициализируйте мапу с помощью make и исправьте ошибку.",
        "theory": """
Комплексный разбор жизненного цикла `hmap`.
""",
        "step_by_step": """
1. Объявляем `var m map[string]int`.
2. Читаем `m["test"]` (возвращает 0).
3. Перехватываем панику записи.
4. Исправляем через `make(map[string]int)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	var m map[string]int

	// 1. Чтение безопасно
	fmt.Printf("1. Чтение из nil-мапы: m[\"a\"] = %d\n", m["a"])

	// 2. Ловим панику записи
	func() {
		defer func() {
			if r := recover(); r != nil {
				fmt.Printf("2. Перехвачена паника: %v\n", r)
			}
		}()
		m["key"] = 1
	}()

	// 3. Исправление через make
	m = make(map[string]int)
	m["key"] = 1
	fmt.Printf("3. Успешная запись после make: m[\"key\"] = %d\n", m["key"])
}""",
                "note": "Исправление неинициализированной map"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. Чтение из nil-мапы: m["a"] = 0
# 2. Перехвачена паника: assignment to entry in nil map
# 3. Успешная запись после make: m["key"] = 1""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
`makemap` создает корневой дескриптор `hmap` и выделяет массив бакетов.
""",
        "pitfalls": """
- Объявление `var m map[K]V` вместо `m := make(map[K]V)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли указать начальную емкость мапы в `make`?»
**Ответ:** ДА! `make(map[K]V, hint)` выделяет достаточное количество бакетов под `hint` элементов, предотвращая дорогостоящие реаллокации (Evacuation) при заполнении.
"""
    },
    {
        "num": 23,
        "title": "Инвертирование мапы map[string]int в map[int]string с детекцией коллизий",
        "task": "Инвертируйте map [string]int в [int]string, проверьте на коллизии.",
        "theory": """
**Инверсия мапы (Key-Value Inversion):**
- Исходная мапа сопоставляет `string -> int`;
- Инвертированная мапа сопоставляет `int -> string`;
- **Проблема коллизий:** если двум разным ключам соответствовало одно значение (например `"admin": 1` и `"root": 1`), в инвертированной мапе один ключ затрет другой!
""",
        "step_by_step": """
1. Пишем `InvertWithCollisionCheck(m map[string]int) (map[int]string, error)`.
2. Тестируем на мапе без коллизий.
3. Тестируем на мапе с дубликатами значений.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func InvertWithCollisionCheck(m map[string]int) (map[int]string, error) {
	inverted := make(map[int]string, len(m))
	for k, v := range m {
		if oldKey, exists := inverted[v]; exists {
			return nil, fmt.Errorf("коллизия для значения %d: ключи %q и %q", v, oldKey, k)
		}
		inverted[v] = k
	}
	return inverted, nil
}

func main() {
	uniqueMap := map[string]int{"one": 1, "two": 2, "three": 3}
	inv1, err1 := InvertWithCollisionCheck(uniqueMap)
	fmt.Printf("1. Уникальная инверсия: %v (err: %v)\n", inv1, err1)

	duplicateMap := map[string]int{"admin": 1, "root": 1, "guest": 2}
	inv2, err2 := InvertWithCollisionCheck(duplicateMap)
	fmt.Printf("2. Инверсия с дубликатами: %v (err: %v)\n", inv2, err2)
}""",
                "note": "Инверсия мапы с проверкой коллизий"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. Уникальная инверсия: map[1:one 2:two 3:three] (err: <nil>)
# 2. Инверсия с дубликатами: map[] (err: коллизия для значения 1: ключи "admin" и "root")""",
                "note": "Детекция коллизий сработала"
            }
        ],
        "under_the_hood": """
Сложность $O(N)$ времени и $O(N)$ памяти.
""",
        "pitfalls": """
- Неконтролируемая перезапись дубликатов значений без логирования или возврата ошибки.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как инвертировать мапу с сохранением ВСЕХ коллизий без потерь?»
**Ответ:** Изменить тип возвращаемой мапы на `map[int][]string` (группировка всех ключей в срез).
"""
    },
    {
        "num": 24,
        "title": "Каверзный кейс: паника записи в nil-мапу и правильная инициализация",
        "task": "[Каверзный кейс]: Объяви var m map[string]int. Попробуй сделать m[\"a\"] = 1 (поймай панику записи в nil-мапу). Исправь с помощью make.",
        "theory": """
Закрепление паттерна безопасного создания хэш-таблицы.
""",
        "step_by_step": """
1. Иллюстрируем типичный баг на собеседовании.
2. Исправляем на `m := make(map[string]int)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	// Каверзный кейс:
	var m map[string]int

	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("Поймана ожидаемая паника: %v\n", r)

			// Исправленный вариант:
			fixedMap := make(map[string]int)
			fixedMap["a"] = 1
			fmt.Printf("Исправлено через make: fixedMap[\"a\"] = %d\n", fixedMap["a"])
		}
	}()

	m["a"] = 1 // Вызов паники
}""",
                "note": "Перехват и исправление nil-мапы"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Поймана ожидаемая паника: assignment to entry in nil map
# Исправлено через make: fixedMap["a"] = 1""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Встроенная инструкция компилятора `assertNotNilMap`.
""",
        "pitfalls": """
- Объявление `var m map[string]int` внутри структур без инициализации.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go `var s []int` можно использовать с `append`, а `var m map[K]V` нельзя использовать для записи?»
**Ответ:** Потому что `append` возвращает новый дескриптор `SliceHeader`, обновляя переменную вызывающего кода, а запись `m[k] = v` не возвращает значения и требует уже существующего корневого объекта `hmap`.
"""
    },
    {
        "num": 25,
        "title": "Идиома Comma-ok для безопасной проверки наличия ключа перед вычислениями",
        "task": "Используйте идиому value, ok := myMap[key] для безопасной проверки наличия ключа перед его использованием.",
        "theory": """
Применение идиомы `value, ok := m[key]` в Guard Clauses.
""",
        "step_by_step": """
1. Создаем мапу пользователей и их балансов.
2. Проверяем наличие счета перед переводом.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func ProcessPayment(accounts map[string]int, user string, amount int) {
	balance, ok := accounts[user]
	if !ok {
		fmt.Printf("❌ Ошибка: пользователь %q не зарегистрирован в системе\n", user)
		return
	}

	if balance < amount {
		fmt.Printf("⚠️ Недостаточно средств для %q: баланс %d, требуется %d\n", user, balance, amount)
		return
	}

	accounts[user] -= amount
	fmt.Printf("✔ Списание %d со счета %q прошло успешно! Новый баланс: %d\n", amount, user, accounts[user])
}

func main() {
	bank := map[string]int{
		"Alice": 500,
		"Bob":   50,
	}

	ProcessPayment(bank, "Charlie", 100)
	ProcessPayment(bank, "Bob", 100)
	ProcessPayment(bank, "Alice", 100)
}""",
                "note": "Проверка наличия счета через comma-ok"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# ❌ Ошибка: пользователь "Charlie" не зарегистрирован в системе
# ⚠️ Недостаточно средств для "Bob": баланс 50, требуется 100
# ✔ Списание 100 со счета "Alice" прошло успешно! Новый баланс: 400""",
                "note": "Все ветки обработаны корректно"
            }
        ],
        "under_the_hood": """
`runtime.mapaccess2` проверяет наличие ключа без аллокаций.
""",
        "pitfalls": """
- Прямое чтение `accounts[user]` без проверки: создаст риск ложного нулевого баланса.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова идиома проверки отсутствия ключа?»
**Ответ:** `if _, ok := m[key]; !ok { /* ключ отсутствует */ }`.
"""
    },
    {
        "num": 26,
        "title": "Функция InvertMap(m) со стратегией перезаписи Last-Write-Wins",
        "task": "Напиши функцию InvertMap(m map[string]int) map[int]string, которая меняет ключи и значения местами. Обработай коллизии: если несколько ключей имели одно значение — пусть побеждает последний (или возвращай ошибку).",
        "theory": """
Реализация стратегии Last-Write-Wins при инверсии мапы.
""",
        "step_by_step": """
1. Пишем `InvertMap(m map[string]int) map[int]string`.
2. Перебираем пары и сохраняем `inv[v] = k`.
3. Анализируем результат при дубликатах.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func InvertMap(m map[string]int) map[int]string {
	inverted := make(map[int]string, len(m))
	for k, v := range m {
		inverted[v] = k // При совпадении v побеждает последний k
	}
	return inverted
}

func main() {
	original := map[string]int{
		"HTTP": 80,
		"HTTPS": 443,
		"SSH": 22,
	}

	inverted := InvertMap(original)
	fmt.Printf("Оригинал:  %v\n", original)
	fmt.Printf("Инверсия:  %v\n", inverted)
	fmt.Printf("Порт 443 -> Протокол: %s\n", inverted[443])
}""",
                "note": "Функция InvertMap"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Оригинал:  map[HTTP:80 HTTPS:443 SSH:22]
# Инверсия:  map[22:SSH 80:HTTP 443:HTTPS]
# Порт 443 -> Протокол: HTTPS""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Предвыделение `make(map[int]string, len(m))` исключает расширение бакетов.
""",
        "pitfalls": """
- Так как обход мапы в Go недетерминирован, при коллизиях победителем может стать случайный ключ на разных запусках!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему при коллизиях `InvertMap` недетерминирован?»
**Ответ:** Потому что порядок итерации `for k, v := range m` случаен, и порядок перезаписи дублирующихся значений `inverted[v] = k` непредсказуем.
"""
    },
    {
        "num": 27,
        "title": "Подсчет частоты слов текста с предварительной токенизацией strings.Fields",
        "task": "Подсчет частоты слов: Напиши функцию, которая принимает строку текста (с пробелами), разбивает её на слова (пакет strings) и с помощью мапы подсчитывает, сколько раз встретилось каждое слово.",
        "theory": """
Изолированная функция подсчета частот слов.
""",
        "step_by_step": """
1. Пишем `CountWords(text string) map[string]int`.
2. Используем `strings.Fields`.
3. Тестируем на фразе.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"strings"
)

func CountWords(text string) map[string]int {
	counts := make(map[string]int)
	for _, word := range strings.Fields(text) {
		counts[word]++
	}
	return counts
}

func main() {
	text := "яблоко банан яблоко груша банан яблоко"
	res := CountWords(text)

	fmt.Printf("Текст: %q\n", text)
	fmt.Println("Результаты подсчета:")
	for k, v := range res {
		fmt.Printf("  • %-10s: %d\n", k, v)
	}
}""",
                "note": "Подсчет частот слов"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Текст: "яблоко банан яблоко груша банан яблоко"
# Результаты подсчета:
#   • яблоко    : 3
#   • банан     : 2
#   • груша     : 1""",
                "note": "Результаты"
            }
        ],
        "under_the_hood": """
Идиома `counts[word]++` компилируется в эффективную инструкцию рантайма.
""",
        "pitfalls": """
- Передача пустой строки: `strings.Fields("")` вернет пустой срез, функция безопасно вернет пустую мапу.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова временная сложность `CountWords` от длины строки $L$?»
**Ответ:** $O(L)$ линейное время (разбивка на токены + вставка в хэш-таблицу).
"""
    },
    {
        "num": 28,
        "title": "Ловушка мутации переменной цикла v++ в range по мапе и правильная модификация m[k]++",
        "task": "Пройди range по мапе и попробуй изменить значение через переменную цикла: for k, v := range m { v++ }. Покажи, что мапа не изменилась. Сделай правильно: for k := range m { m[k]++ }.",
        "theory": """
**Ловушка копирования в цикле по мапе:**
- В `for k, v := range m` переменная `v` — это **локальная копия значения** из бакета;
- Выражение `v++` инкрементирует только локальную переменную на стеке;
- Для реальной мутации данных в мапе необходимо выполнять запись по ключу: `m[k]++`.
""",
        "step_by_step": """
1. Создаем `m := map[string]int{"A": 10, "B": 20}`.
2. Пробуем наивный цикл `for _, v := range m { v += 100 }`.
3. Показываем, что мапа не изменилась.
4. Выполняем правильный цикл `for k := range m { m[k] += 100 }`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	m := map[string]int{"A": 10, "B": 20}
	fmt.Printf("1. Исходная мапа: %v\n", m)

	// НЕПРАВИЛЬНО: мутация локальной копии v
	for _, v := range m {
		v += 100 // Изменяет только копию на стеке!
	}
	fmt.Printf("2. После for _, v (НЕ ИЗМЕНИЛАСЬ!): %v\n", m)

	// ПРАВИЛЬНО: явная запись по ключу в мапу
	for k := range m {
		m[k] += 100 // Мутирует саму хэш-таблицу!
	}
	fmt.Printf("3. После for k := range m: %v (УСПЕШНО!)\n", m)
}""",
                "note": "Правильная мутация элементов map в цикле"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. Исходная мапа: map[A:10 B:20]
# 2. После for _, v (НЕ ИЗМЕНИЛАСЬ!): map[A:10 B:20]
# 3. После for k := range m: map[A:110 B:120] (УСПЕШНО!)""",
                "note": "Только m[k] мутирует мапу"
            }
        ],
        "under_the_hood": """
При `for _, v` значение `v` копируется в стековый регистр. `m[k] = ...` вызывает `runtime.mapassign`.
""",
        "pitfalls": """
- Модификация полей структур `for _, user := range users { user.Age++ }`: возраст в мапе не изменится.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли добавлять новые ключи в мапу внутри цикла `for k := range m`?»
**Ответ:** Да, язык это разрешает, но гарантии того, попадет ли новый добавленный ключ в текущую итерацию цикла, нет (рантайм может посетить его или пропустить).
"""
    },
    {
        "num": 29,
        "title": "Мапа столиц стран и демонстрация различий между Zero Value и Comma-ok",
        "task": "Запятая-ок (Comma-ok idiom): Создайте мапу соответствия стран и их столиц. Напишите код, который проверяет наличие города в мапе. Продемонстрируйте разницу между получением дефолтного значения для несуществующего ключа и реальной проверкой через val, ok := m[key].",
        "theory": """
Практическая демонстрация идиомы `comma-ok` на справочнике столиц.
""",
        "step_by_step": """
1. Создаем справочник `capitals := map[string]string{ "Россия": "Москва", "Германия": "Берлин" }`.
2. Ищем существующую страну.
3. Ищем отсутствующую страну.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func FindCapital(capitals map[string]string, country string) {
	// Способ 1: Прямое чтение (дефолтное значение)
	val := capitals[country]
	fmt.Printf("Прямое чтение для %-10s -> %q\n", country, val)

	// Способ 2: Идиома comma-ok (надежная проверка)
	if capital, ok := capitals[country]; ok {
		fmt.Printf("  ✔ Найдено: Столица %s — это %s\n", country, capital)
	} else {
		fmt.Printf("  ❌ Внимание: Страна %s отсутствует в базе данных!\n", country)
	}
}

func main() {
	capitals := map[string]string{
		"Россия":   "Москва",
		"Франция":  "Париж",
		"Германия": "Берлин",
	}

	FindCapital(capitals, "Россия")
	FindCapital(capitals, "Бразилия")
}""",
                "note": "Сравнение прямого чтения и comma-ok"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Прямое чтение для Россия     -> "Москва"
#   ✔ Найдено: Столица Россия — это Москва
# Прямое чтение для Бразилия   -> ""
#   ❌ Внимание: Страна Бразилия отсутствует в базе данных!""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
При отсутствии ключа рантайм возвращает пустую строку `""` (длина 0, указатель nil).
""",
        "pitfalls": """
- Проверка `if capitals[country] != ""` вместо `comma-ok`: если столица пустая строка `""` (город-государство без столицы), проверка выдаст ложный результат.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем преимущество `comma-ok` перед возвратом ошибки `error` в методах чтения?»
**Ответ:** Нулевые накладные расходы по аллокациям памяти, лаконичный синтаксис `if val, ok := m[k]; ok` и инлайнинг рантайма.
"""
    },
    {
        "num": 30,
        "title": "Чтение несуществующего ключа в числовых и строковых мапах",
        "task": "Попробуй прочитать значение по несуществующему ключу. Выведи результат (должен быть нулевым значением типа).",
        "theory": """
Базовая проверка возврата Zero Value.
""",
        "step_by_step": """
1. Создаем числовую мапу `ages := map[string]int{"Bob": 25}`.
2. Читаем `"Alice"`.
3. Печатаем нулевое значение.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	ages := map[string]int{"Bob": 25}

	missingAge := ages["Alice"]
	fmt.Printf("Значение для отсутствующего ключа 'Alice': %d (Zero Value типа int)\n", missingAge)
}""",
                "note": "Zero Value отсутствующего ключа"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Значение для отсутствующего ключа 'Alice': 0 (Zero Value типа int)""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
`zeroVal` в `runtime.mapaccess1`.
""",
        "pitfalls": """
- Путать `0` (возраст не найден) с реальным возрастом младенца (`0` лет).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как безопасно вернуть указатель `*int` на значение из мапы?»
**Ответ:** `map[string]*int`: при отсутствии ключа вернется `nil`, что однозначно указывает на отсутствие значения.
"""
    },
    {
        "num": 31,
        "title": "Детерминированный вывод мапы: сбор и сортировка среза ключей",
        "task": "Отсортируйте ключи map и выведите значения в отсортированном порядке.",
        "theory": """
**Паттерн сортировки мапы (Sorted Map Traversal):**
1. Мапы в Go не упорядочены;
2. Для гарантированного детерминированного вывода:
   - Собирают все ключи в срез `keys := make([]K, 0, len(m))`;
   - Сортируют срез ключей (`slices.Sort(keys)` или `sort.Strings/Ints`);
   - Обходят отсортированный срез ключей и читают значения из мапы `m[k]`.
""",
        "step_by_step": """
1. Создаем неупорядоченную мапу `scores := map[string]int{"Dan": 90, "Ann": 95, "Ben": 85}`.
2. Собираем ключи в срез `keys`.
3. Сортируем срез `slices.Sort(keys)`.
4. Выводим данные в строгом алфавитном порядке.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"slices"
)

func main() {
	scores := map[string]int{
		"Dan": 90,
		"Ann": 95,
		"Ben": 85,
		"Cal": 92,
	}

	// 1. Собираем ключи с предварительным выделением емкости
	keys := make([]string, 0, len(scores))
	for k := range scores {
		keys = append(keys, k)
	}

	// 2. Сортируем срез ключей (Go 1.21+)
	slices.Sort(keys)

	// 3. Детерминированный вывод:
	fmt.Println("Отсортированный вывод мапы:")
	for _, k := range keys {
		fmt.Printf("  • %-5s -> %d баллов\n", k, scores[k])
	}
}""",
                "note": "Сортировка ключей map"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Отсортированный вывод мапы:
#   • Ann   -> 95 баллов
#   • Ben   -> 85 баллов
#   • Cal   -> 92 баллов
#   • Dan   -> 90 баллов""",
                "note": "Гарантированный порядок вывода"
            }
        ],
        "under_the_hood": """
`slices.Sort` выполняет $O(N \log N)$ сортировку ключей, после чего каждый поиск `scores[k]` занимает $O(1)$.
""",
        "pitfalls": """
- Выделение среза через `make([]string, len(scores))` и последующий `append`: создаст срез двойной длины с пустыми строками в начале. Используйте `make([]string, 0, len(scores))`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова асимптотика детерминированного обхода мапы?»
**Ответ:** $O(N \log N)$ по времени (доминирует сортировка ключей) и $O(N)$ по памяти под срез ключей.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 2: {len(exercises)} exercises.")
