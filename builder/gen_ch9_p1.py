# Chapter 9 Part 1: Exercises 1 to 15

exercises = [
    {
        "num": 1,
        "title": "Чтение несуществующего ключа из map и автоматический возврат Zero Value",
        "task": "Чтение несуществующего ключа: Запроси из нормальной мапы ключ, которого там нет. Убедись, что программа не падает, а возвращает zero value (ноль для int).",
        "theory": """
**Поведение `map[K]V` при обращении к отсутствующему ключу:**
- В отличие от Python (`KeyError`) или C++ (`std::map::at` out_of_range), в Go чтение `val := m[key]` **никогда не вызывает панику** и не завершает программу ошибкой;
- Если ключ не найден в хэш-таблице, рантайм Go возвращает **нулевое значение типа `V`** (`0` для чисел, `""` для строк, `false` для `bool`, `nil` для указателей/срезов/мап).
""",
        "step_by_step": """
1. Создаем `scores := map[string]int{"Alice": 95, "Bob": 80}`.
2. Запрашиваем существующий ключ `"Alice"`.
3. Запрашиваем отсутствующий ключ `"Charlie"`.
4. Сравниваем результаты.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	scores := map[string]int{
		"Alice": 95,
		"Bob":   80,
	}

	fmt.Printf("1. Существующий ключ 'Alice':   %d\n", scores["Alice"])
	fmt.Printf("2. Несуществующий ключ 'Charlie': %d (Zero Value типа int)\n", scores["Charlie"])
}""",
                "note": "Чтение несуществующего ключа"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. Существующий ключ 'Alice':   95
# 2. Несуществующий ключ 'Charlie': 0 (Zero Value типа int)""",
                "note": "Возврат нуля без паники"
            }
        ],
        "under_the_hood": """
При промахе хэш-поиска процедура `runtime.mapaccess1` возвращает указатель на глобальную область нулей `runtime.zeroVal`.
""",
        "pitfalls": """
- Предположение, что возвращенный `0` означает, что ключ `"Charlie": 0` реально сохранен в мапе. Для различения отсутствия и реального нуля используют идиому `comma-ok`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему авторы Go решили возвращать Zero Value вместо выброса исключения при чтении из `map`?»
**Ответ:** Это позволяет писать лаконичный код счетчиков вида `counts[word]++` без предварительных проверок наличия ключа (`counts[word]` при первом обращении вернет 0, и `0++` запишет 1).
"""
    },
    {
        "num": 2,
        "title": "Анатомия Nil-мапы (var m map[string]int): безопасное чтение vs фатальная паника при записи",
        "task": "Объяви var m map[string]int (nil map). Прочитай значение по ключу: v := m[\"key\"]. Покажи, что не паникует, возвращает zero value (0). Затем попробуй записать: m[\"key\"] = 1 — получи панику assignment to entry in nil map. Объясни, почему чтение безопасно, а запись — нет.",
        "theory": """
**Nil Map в рантайме Go:**
1. Неинициализированная мапа `var m map[string]int` имеет значение `nil` (внутренний указатель на структуру `hmap` равен `0x0`);
2. **Чтение `m["key"]`:** `runtime.mapaccess1` проверяет `if h == nil { return zeroVal }` $\rightarrow$ абсолютно безопасно;
3. **Запись `m["key"] = 1`:** `runtime.mapassign` не может выделить память под бакеты, так как заголовка `hmap` не существует $\rightarrow$ вызывает немедленную фатальную панику `panic: assignment to entry in nil map`.
""",
        "step_by_step": """
1. Объявляем `var m map[string]int`.
2. Читаем `v := m["test"]` и убеждаемся в отсутствии паники.
3. Перехватываем панику при записи `m["test"] = 100` через `recover()`.
4. Исправляем инициализацией `make(map[string]int)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	var m map[string]int // nil-мапа

	fmt.Printf("1. Состояние: isNil = %t, len = %d\n", m == nil, len(m))

	// Чтение из nil-мапы полностью безопасно:
	val := m["любой_ключ"]
	fmt.Printf("2. Чтение из nil-мапы: val = %d (Zero Value)\n\n", val)

	// Запись в nil-мапу вызывает панику:
	func() {
		defer func() {
			if r := recover(); r != nil {
				fmt.Printf("⚠️ 3. Перехвачена паника при записи: %v\n", r)
			}
		}()
		m["key"] = 1 // ПАНИКА!
	}()

	// Исправление через make:
	m = make(map[string]int)
	m["key"] = 1
	fmt.Printf("\n4. После make: m[\"key\"] = %d (УСПЕШНО!)\n", m["key"])
}""",
                "note": "Nil-мапа: безопасное чтение и паника при записи"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. Состояние: isNil = true, len = 0
# 2. Чтение из nil-мапы: val = 0 (Zero Value)
# 
# ⚠️ 3. Перехвачена паника при записи: assignment to entry in nil map
# 
# 4. После make: m["key"] = 1 (УСПЕШНО!)""",
                "note": "Результаты"
            }
        ],
        "under_the_hood": """
Мапа в Go — это указатель на структуру `runtime.hmap`. Если указатель `0x0`, запись не может аллоцировать память без создания `hmap`.
""",
        "pitfalls": """
- Объявление мапы в структуре `type Service struct { cache map[string]string }` без явной инициализации в конструкторе `NewService()`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему Go не инициализирует `map` автоматически при первой записи, как `append` у срезов?»
**Ответ:** Потому что `map` передается по значению как указатель на `hmap`. Если бы первая запись создавала `hmap` неявно, это изменило бы значение локального указателя, но не обновило бы мапу у вызывающей стороны.
"""
    },
    {
        "num": 3,
        "title": "Инициализация мапы литералом и итерация через for k, v := range",
        "task": "Создай мапу-литерал: map[string]int{\"one\": 1, \"two\": 2, \"three\": 3}. Пройди по ней for k, v := range.",
        "theory": """
**Литерал мапы и итерация:**
- Литерал `map[K]V{k1: v1, k2: v2}` выделяет память и сразу заполняет бакеты;
- Цикл `for k, v := range m` обходит все пары ключ-значение;
- Порядок обхода **намеренно рандомизируется** рантаймом Go на каждом запуске цикла.
""",
        "step_by_step": """
1. Инициализируем `numbers := map[string]int{"one": 1, "two": 2, "three": 3}`.
2. Проходим `for k, v := range numbers`.
3. Печатаем пары ключ-значение.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	numbers := map[string]int{
		"one":   1,
		"two":   2,
		"three": 3,
	}

	fmt.Printf("Размер мапы: %d пар\n", len(numbers))
	for key, val := range numbers {
		fmt.Printf("  Ключ: %-6q -> Значение: %d\n", key, val)
	}
}""",
                "note": "Литерал мапы и обход через range"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Размер мапы: 3 пар
#   Ключ: "one"    -> Значение: 1
#   Ключ: "two"    -> Значение: 2
#   Ключ: "three"  -> Значение: 3""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Литерал преобразуется компилятором в `makemap` с последующей серией вызовов `mapassign`.
""",
        "pitfalls": """
- Надежда на сохранение порядка вставки: мапа в Go принципиально не гарантирует порядок.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли узнать емкость мапы через `cap(m)`?»
**Ответ:** НЕТ! Функция `cap()` запрещена для мап (ошибка компиляции). Мапа динамически расширяется по мере роста коэффициента заполнения (Load Factor $> 6.5$).
"""
    },
    {
        "num": 4,
        "title": "Идиома Comma-ok (val, ok := m[key]): различение нуля и отсутствия ключа",
        "task": "Идиома Comma Ok: Как отличить, в мапе реально лежит ноль, или ключа просто нет? Запроси значение как val, ok := m[\"key\"] и выведи ok.",
        "theory": """
**Двухпараметрический доступ к мапе (Comma-ok idiom):**
- Форма `val, ok := m[key]`:
  - `ok == true` $\rightarrow$ ключ физически существует в мапе (даже если `val == 0`);
  - `ok == false` $\rightarrow$ ключ отсутствует в мапе (и `val` содержит default zero value).
""",
        "step_by_step": """
1. Создаем `balances := map[string]int{"Alice": 0, "Bob": 500}`.
2. Проверяем ключ `"Alice"` (баланс 0, но клиент существует).
3. Проверяем ключ `"Charlie"` (клиент отсутствует).
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	balances := map[string]int{
		"Alice": 0,   // Реально лежит ноль
		"Bob":   500, // Положительный баланс
	}

	// 1. Проверяем Alice:
	valA, okA := balances["Alice"]
	fmt.Printf("Alice:   значение = %d, найден = %-5t (КЛЮЧ ЕСТЬ В МАПЕ!)\n", valA, okA)

	// 2. Проверяем Charlie:
	valC, okC := balances["Charlie"]
	fmt.Printf("Charlie: значение = %d, найден = %-5t (КЛЮЧА НЕТ В МАПЕ!)\n", valC, okC)
}""",
                "note": "Идиома Comma-ok"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Alice:   значение = 0, найден = true  (КЛЮЧ ЕСТЬ В МАПЕ!)
# Charlie: значение = 0, найден = false (КЛЮЧА НЕТ В МАПЕ!)""",
                "note": "Различение 0 и отсутствия"
            }
        ],
        "under_the_hood": """
Компилятор заменяет выражение на вызов `runtime.mapaccess2`, возвращающий `(unsafe.Pointer, bool)`.
""",
        "pitfalls": """
- Проверка наличия через `if m[k] != 0`: если в мапе действительно лежит 0, условие ошибочно решит, что ключа нет.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как проверить только наличие ключа в мапе, не сохраняя само значение?»
**Ответ:** `if _, ok := m[key]; ok { ... }`.
"""
    },
    {
        "num": 5,
        "title": "Функция SafeGet(m, key) для инкапсуляции безопасного чтения из map",
        "task": "Напиши функцию SafeGet(m map[string]int, key string) (int, bool), использующую comma ok идиому: v, ok := m[key]. Верни значение и флаг наличия.",
        "theory": """
Инкапсуляция доступа к данным хэш-таблицы с явным контрактом успешности.
""",
        "step_by_step": """
1. Пишем `SafeGet(m map[string]int, key string) (int, bool)`.
2. Тестируем на существующих и отсутствующих ключах.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func SafeGet(m map[string]int, key string) (int, bool) {
	v, ok := m[key]
	return v, ok
}

func main() {
	inventory := map[string]int{
		"laptop": 15,
		"mouse":  0, // Товар закончился, но позиция есть
	}

	itemsToFind := []string{"laptop", "mouse", "keyboard"}
	for _, item := range itemsToFind {
		qty, found := SafeGet(inventory, item)
		if found {
			fmt.Printf("✔ Товар %-10q найден: количество = %d\n", item, qty)
		} else {
			fmt.Printf("❌ Товар %-10q отсутствует в каталоге\n", item)
		}
	}
}""",
                "note": "Функция SafeGet"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# ✔ Товар "laptop"   найден: количество = 15
# ✔ Товар "mouse"    найден: количество = 0
# ❌ Товар "keyboard" отсутствует в каталоге""",
                "note": "Результаты поиска"
            }
        ],
        "under_the_hood": """
Возврат двух регистров `(RAX, RBX)` без аллокаций памяти.
""",
        "pitfalls": """
- Вызов `SafeGet` на `nil`-мапе: функция отработает штатно и вернет `(0, false)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова амортизированная временная сложность `SafeGet`?»
**Ответ:** В среднем $O(1)$, в худшем случае $O(N)$ при катастрофических коллизиях хэш-функции.
"""
    },
    {
        "num": 6,
        "title": "Безопасное удаление delete(m, key) и отсутствие паник на несуществующих ключах",
        "task": "Безопасное удаление: Используй функцию delete(m, \"key\"). Попробуй удалить ключ, которого нет в мапе (убедись, что это не вызывает ошибок).",
        "theory": """
**Встроенная функция `delete(m, key)`:**
- Удаляет ключ и связанное значение из мапы `m`;
- Если ключ не найден или сама мапа равна `nil`, операция является **no-op (пустой операцией)**: программа не падает и не возвращает ошибок;
- Освобождает слот в бакете для последующей перезаписи.
""",
        "step_by_step": """
1. Создаем `m := map[string]int{"auth": 1, "db": 2}`.
2. Удаляем существующий ключ `"auth"`.
3. Удаляем отсутствующий ключ `"ghost"`.
4. Удаляем из `nil`-мапы.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	services := map[string]int{"auth": 8080, "db": 5432}
	fmt.Printf("1. Исходная мапа: %v\n", services)

	// 1. Удаление существующего ключа:
	delete(services, "auth")
	fmt.Printf("2. После delete('auth'): %v\n", services)

	// 2. Удаление несуществующего ключа (no-op):
	delete(services, "non_existent_key")
	fmt.Printf("3. После delete('non_existent_key'): %v (без ошибок!)\n", services)

	// 3. Удаление из nil-мапы (безопасно!):
	var nilMap map[string]int
	delete(nilMap, "any_key")
	fmt.Println("4. delete из nilMap отработал успешно и без паники!")
}""",
                "note": "Безопасность функции delete"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. Исходная мапа: map[auth:8080 db:5432]
# 2. После delete('auth'): map[db:5432]
# 3. После delete('non_existent_key'): map[db:5432] (без ошибок!)
# 4. delete из nilMap отработал успешно и без паники!""",
                "note": "Штатная работа без паник"
            }
        ],
        "under_the_hood": """
`runtime.mapdelete` проверяет `if h == nil || h.count == 0 { return }`. Внутри бакета слот помечается маркером `emptyOne`.
""",
        "pitfalls": """
- Ожидание, что `delete` вернет булев флаг, был ли элемент удален: `delete` возвращает `void`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Освобождает ли `delete` физическую память бакетов мапы?»
**Ответ:** НЕТ! `delete` освобождает только ячейки для повторного использования. Объем выделенных страниц памяти под мапу не уменьшается.
"""
    },
    {
        "num": 7,
        "title": "Создание мапы map[string]int, добавление 3 пар и форматированный вывод",
        "task": "Создайте мапу map[string]int, добавьте в нее 3 пары ключ-значение и выведите их.",
        "theory": """
Базовые операции инициализации, записи `m[k] = v` и чтения.
""",
        "step_by_step": """
1. Инициализируем `users := make(map[string]int)`.
2. Добавляем 3 пользователя с их ID.
3. Печатаем мапу и ее длину.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	users := make(map[string]int)

	users["admin"] = 1
	users["moderator"] = 2
	users["guest"] = 99

	fmt.Printf("Мапа: %v\n", users)
	fmt.Printf("Число записей len(users): %d\n", len(users))
	fmt.Printf("ID администратора:        %d\n", users["admin"])
}""",
                "note": "Добавление элементов в map"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Мапа: map[admin:1 guest:99 moderator:2]
# Число записей len(users): 3
# ID администратора:        1""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
`make(map[string]int)` аллоцирует структуру `hmap` с 1 начальным бакетом на 8 слотов.
""",
        "pitfalls": """
- Забыть вызов `make()` и писать в `var users map[string]int`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Сколько пар ключ-значение помещается в один бакет `bmap` в рантайме Go?»
**Ответ:** Ровно 8 пар (8 ключей + 8 значений + 8 байт tophash).
"""
    },
    {
        "num": 8,
        "title": "Вложенные мапы map[string]map[string]int и обязательная инициализация внутренних уровней",
        "task": "Вложенные мапы: Создай map[string]map[string]int. Добавь значение. Не забудь, что внутреннюю мапу тоже нужно инициализировать через make, иначе будет паника.",
        "theory": """
**Опасность вложенных мап (Nested Maps):**
- При создании внешней мапы `outer := make(map[string]map[string]int)` все ее значения по умолчанию равны `nil`;
- Попытка записи `outer["user1"]["score"] = 100` вызовет панику `assignment to entry in nil map`, так как `outer["user1"]` равен `nil`;
- Перед записью во внутреннюю мапу **обязательно проверяют и инициализируют ее через `make`**.
""",
        "step_by_step": """
1. Создаем внешнюю мапу `outer := make(map[string]map[string]int)`.
2. Пишем функцию безопасной вставки `SetNestedValue`.
3. Заполняем данные студентов и их оценки.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func SetScore(grades map[string]map[string]int, student, subject string, score int) {
	// Если внутренняя мапа для студента еще не создана:
	if grades[student] == nil {
		grades[student] = make(map[string]int) // Инициализируем внутренний уровень!
	}
	grades[student][subject] = score
}

func main() {
	grades := make(map[string]map[string]int)

	SetScore(grades, "Иван", "Математика", 5)
	SetScore(grades, "Иван", "Физика", 4)
	SetScore(grades, "Анна", "Информатика", 5)

	fmt.Println("Вложенная структура оценок:")
	for student, subjects := range grades {
		fmt.Printf("  Студент: %-6s -> %v\n", student, subjects)
	}
}""",
                "note": "Безопасная работа с вложенными мапами"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Вложенная структура оценок:
#   Студент: Иван   -> map[Математика:5 Физика:4]
#   Студент: Анна   -> map[Информатика:5]""",
                "note": "Вложенные мапы успешно инициализированы"
            }
        ],
        "under_the_hood": """
Каждая внутренняя мапа — это отдельный независимый дескриптор `hmap` в куче.
""",
        "pitfalls": """
- Прямая запись `grades["Анна"]["Физика"] = 5` без предварительного `make` для `"Анна"`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каковы альтернативы глубоко вложенным мапам `map[K1]map[K2]V`?»
**Ответ:** Использование составного ключа-структуры: `type Key struct { Student, Subject string }` и плоской мапы `map[Key]int`. Это требует меньше аллокаций и устраняет проблемы с `nil`.
"""
    },
    {
        "num": 9,
        "title": "Значения по умолчанию для отсутствующих ключей различных типов (string, bool, slice, struct)",
        "task": "Попробуйте обратиться к несуществующему ключу в мапе. Какое значение \"по умолчанию\" вернется?",
        "theory": """
Сводная таблица Zero Values при промахе в map:
- `map[string]string` $\rightarrow `""`
- `map[string]bool` $\rightarrow `false`
- `map[string][]int` $\rightarrow `nil` срез (`len=0`)
- `map[string]Point` $\rightarrow `Point{X: 0, Y: 0}`
""",
        "step_by_step": """
1. Создаем мапы разных типов.
2. Читаем несуществующие ключи.
3. Проверяем возвращенные значения.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type Config struct {
	Timeout int
	Debug   bool
}

func main() {
	mStr := make(map[string]string)
	mBool := make(map[string]bool)
	mSlice := make(map[string][]int)
	mStruct := make(map[string]Config)

	fmt.Printf("1. string: %q\n", mStr["missing"])
	fmt.Printf("2. bool:   %t\n", mBool["missing"])
	fmt.Printf("3. slice:  %v (isNil = %t)\n", mSlice["missing"], mSlice["missing"] == nil)
	fmt.Printf("4. struct: %+v\n", mStruct["missing"])
}""",
                "note": "Zero Values различных типов в map"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. string: ""
# 2. bool:   false
# 3. slice:  [] (isNil = true)
# 4. struct: {Timeout:0 Debug:false}""",
                "note": "Результаты"
            }
        ],
        "under_the_hood": """
Память обнуляется согласно размеру `elemType.Size_`.
""",
        "pitfalls": """
- Предположение, что `mSlice["k"]` вернет аллоцированный срез: возвращается именно `nil`-срез.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли делать `append` к `mSlice["missing"]`?»
**Ответ:** ДА! `mSlice["k"] = append(mSlice["k"], 10)` работает корректно, так как `append(nil, 10)` создает валидный срез `[10]`.
"""
    },
    {
        "num": 10,
        "title": "Структура как ключ мапы: Point{X, Y int} и требования Comparable к типам ключей",
        "task": "Структура как ключ: Создай структуру Point{X, Y int}. Используй её в качестве ключа для мапы. (В Go ключом может быть любой тип, для которого определена операция ==).",
        "theory": """
**Требования к типам ключей в Go:**
1. Ключом в `map[K]V` может быть **любой сравнимый тип (Comparable Type)**;
2. Структура `Point{X, Y int}` сравнима через `==`, так как все ее поля (`int`) сравнимы;
3. Две структуры равны, если равны все их поля;
4. Это позволяет легко использовать координаты, составные ID и пары параметров как ключи.
""",
        "step_by_step": """
1. Объявляем структуру `type Point struct { X, Y int }`.
2. Создаем `grid := make(map[Point]string)`.
3. Добавляем объекты и ищем по координатам.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type Point struct {
	X int
	Y int
}

func main() {
	gameMap := map[Point]string{
		{X: 0, Y: 0}: "База игроков",
		{X: 5, Y: 5}: "Золотой рудник",
		{X: 9, Y: 9}: "Вражеский замок",
	}

	playerPos := Point{X: 5, Y: 5}
	fmt.Printf("Локация в точке %v: %s\n", playerPos, gameMap[playerPos])

	unknownPos := Point{X: 1, Y: 2}
	fmt.Printf("Локация в точке %v: %q (пусто)\n", unknownPos, gameMap[unknownPos])
}""",
                "note": "Структура как ключ map"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Локация в точке {5 5}: Золотой рудник
# Локация в точке {1 2}: "" (пусто)""",
                "note": "Поиск по составному ключу"
            }
        ],
        "under_the_hood": """
Хэш-функция вычисляет хэш от 16 байт структуры `Point` через алгоритм `aeshash128`.
""",
        "pitfalls": """
- Добавление в структуру поля несравнимого типа (например `Tags []string`): структура сразу потеряет свойство `comparable` и вызовет ошибку компиляции `invalid map key type Point`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что произойдет, если в структуре-ключе есть приватные поля?»
**Ответ:** Структура все равно останется comparable и сможет быть ключом мапы, если типы приватных полей сравнимы.
"""
    },
    {
        "num": 11,
        "title": "Хранение срезов в мапе map[string][]int: ловушка потери append и обязательное переприсваивание",
        "task": "Создай мапу map[string][]int (значение — слайс). Добавь элементы: m[\"nums\"] = append(m[\"nums\"], 1). Покажи, что если append вызывает реаллокацию, мапа не увидит новые элементы (потому что слайс в мапе — это struct data, и она не обновляется автоматически). Исправь через переприсваивание.",
        "theory": """
**Механика срезов в значениях мапы:**
- Значением в `map[string][]int` хранится 24-байтная копия дескриптора `SliceHeader`;
- Вызов `append(m["nums"], 1)` создает **новый локальный `SliceHeader`**;
- Если не сделать обратное присваивание `m["nums"] = append(...)`, мапа сохранит старый `SliceHeader` со старой длиной `Len`!
""",
        "step_by_step": """
1. Создаем `m := make(map[string][]int)`.
2. Показываем ошибку, если не переприсвоить результат `append`.
3. Показываем правильный паттерн `m[k] = append(m[k], val)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	m := make(map[string][]int)

	// ПРАВИЛЬНО: результат append ВСЕГДА переприсваивается в мапу
	m["scores"] = append(m["scores"], 10)
	m["scores"] = append(m["scores"], 20)
	m["scores"] = append(m["scores"], 30)

	fmt.Printf("1. Срез в мапе: %v | len = %d, cap = %d\n",
		m["scores"], len(m["scores"]), cap(m["scores"]))

	// Иллюстрация: если извлечь срез в переменную и сделать append без записи в мапу:
	temp := m["scores"]
	temp = append(temp, 40) // temp вырос, но в мапе старый SliceHeader!

	fmt.Printf("2. temp после append: %v (len=%d)\n", temp, len(temp))
	fmt.Printf("3. m[\"scores\"] в мапе: %v (len=%d - НЕ ОБНОВИЛСЯ!)\n",
		m["scores"], len(m["scores"]))
}""",
                "note": "Правильное добавление в срез внутри map"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. Срез в мапе: [10 20 30] | len = 3, cap = 4
# 2. temp после append: [10 20 30 40] (len=4)
# 3. m["scores"] в мапе: [10 20 30] (len=3 - НЕ ОБНОВИЛСЯ!)""",
                "note": "Мапа требует явного переприсваивания"
            }
        ],
        "under_the_hood": """
`m["scores"]` возвращает копию `SliceHeader` по значению. Запись `m["k"] = ...` перезаписывает `SliceHeader` в бакете хэш-таблицы.
""",
        "pitfalls": """
- Вызов функций, делающих `append` к срезу из мапы, без сохранения возвращенного среза обратно в мапу.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как хранить динамический список в мапе без необходимости постоянного переприсваивания `m[k] = append(...)`?»
**Ответ:** Хранить срез указателей `map[string]*[]int` или структуру-обертку с мьютексом.
"""
    },
    {
        "num": 12,
        "title": "Несравнимость мап (Not Comparable): почему m1 == m2 запрещен компилятором",
        "task": "Попробуй сравнить две мапы через == (кроме nil). Получи ошибку компиляции. Объясни, почему мапы не comparable в Go.",
        "theory": """
**Почему мапы в Go НЕ поддерживают оператор `==`?**
1. Мапы являются динамическими ссылочными структурами данных со сложной топологией бакетов;
2. Сравнение мап потребовало бы глубокого обхода $O(N)$ всех пар ключ-значение с поиском в хэш-таблице;
3. В спецификации Go оператор `==` зарезервирован для быстрых, плоских операций сравнения фиксированной памяти;
4. Единственное разрешенное сравнение для мап — это сравнение с `nil`: `m == nil` или `m != nil`.
""",
        "step_by_step": """
1. Создаем `m1` и `m2` с идентичным содержимым.
2. Проверяем сравнение с `nil`.
3. Показываем ошибку компиляции при `m1 == m2`.
4. Сравниваем через пакет `maps.Equal` (Go 1.21+).
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"maps"
)

func main() {
	m1 := map[string]int{"a": 1, "b": 2}
	m2 := map[string]int{"a": 1, "b": 2}

	// 1. Сравнение с nil разрешено:
	fmt.Printf("m1 == nil: %t\n", m1 == nil)

	// 2. Прямое сравнение мап запрещено:
	// _ = m1 == m2 // ОШИБКА КОМПИЛЯЦИИ: invalid operation: m1 == m2 (map can only be compared to nil)

	// 3. Правильное сравнение через пакет maps (Go 1.21+):
	areEqual := maps.Equal(m1, m2)
	fmt.Printf("maps.Equal(m1, m2): %t (УСПЕШНОЕ ГЛУБОКОЕ СРАВНЕНИЕ!)\n", areEqual)
}""",
                "note": "Сравнение мап"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# m1 == nil: false
# maps.Equal(m1, m2): true (УСПЕШНОЕ ГЛУБОКОЕ СРАВНЕНИЕ!)""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Компилятор блокирует `==` на этапе проверки типов. `maps.Equal` проверяет `len(m1) == len(m2)` и обходит ключи `m1`, сравнивая значения в `m2`.
""",
        "pitfalls": """
- Попытка использовать структуру, содержащую `map`, как ключ другой мапы: вызовет ошибку `invalid map key type`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова сложность сравнения двух мап через `maps.Equal`?»
**Ответ:** Линейное время $O(N)$ и $O(1)$ по дополнительной памяти.
"""
    },
    {
        "num": 13,
        "title": "Частотный словарь слов текста map[string]int с разбивкой через strings.Fields",
        "task": "Создай мапу, хранящую частоту слов в строке: map[string]int. Посчитай слова и выведи результат.",
        "theory": """
**Паттерн Word Frequency Counter:**
- `strings.Fields(text)` разбивает строку по любым пробельным символам на `[]string`;
- Идиома `freq[word]++` инкрементирует счетчик за $O(1)$;
- При первом появлении слова `freq[word]` вернет `0`, и `0++` запишет `1`.
""",
        "step_by_step": """
1. Задаем строку с повторениями слов.
2. Разбиваем через `strings.Fields`.
3. Подсчитываем в `map[string]int`.
4. Выводим результаты.
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

func CountWordFrequency(text string) map[string]int {
	freq := make(map[string]int)
	words := strings.Fields(strings.ToLower(text))

	for _, w := range words {
		freq[w]++
	}
	return freq
}

func main() {
	text := "Go is fast and Go is simple and Go is powerful"
	counts := CountWordFrequency(text)

	fmt.Println("Частотный словарь слов:")
	for word, count := range counts {
		fmt.Printf("  • %-10s -> %d раз(а)\n", word, count)
	}
}""",
                "note": "Частотный словарь слов"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Частотный словарь слов:
#   • and        -> 2 раз(а)
#   • simple     -> 1 раз(а)
#   • powerful   -> 1 раз(а)
#   • go         -> 3 раз(а)
#   • is         -> 3 раз(а)
#   • fast       -> 1 раз(а)""",
                "note": "Частоты успешно подсчитаны"
            }
        ],
        "under_the_hood": """
`strings.ToLower` создает нормализованную строку, устраняя дубликаты из-за регистра.
""",
        "pitfalls": """
- Игнорирование знаков препинания при сложном парсинге (решается через `strings.Trim(w, ".,!?:")`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как оптимизировать подсчет частот миллиарда строк в Big Data (MapReduce)?»
**Ответ:** Параллельной фазой Map с локальными мапами в каждой горутине и последующей агрегацией (Reduce) с суммированием счетчиков.
"""
    },
    {
        "num": 14,
        "title": "Хранение объектов в координатной сетке map[Point]string",
        "task": "Создай мапу с ключом-структурой: map[Point]string, где Point struct{ X, Y int }. Покажи, что struct comparable может быть ключом. Добавь точки и ищи по координатам.",
        "theory": """
Закрепление использования структур-значений в качестве ключей хэш-таблицы.
""",
        "step_by_step": """
1. Создаем структуру `type Point struct { X, Y int }`.
2. Создаем `landmarks := make(map[Point]string)`.
3. Добавляем достопримечательности и ищем по ключу.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type Point struct {
	X int
	Y int
}

func main() {
	landmarks := map[Point]string{
		{X: 55, Y: 37}: "Москва (Кремль)",
		{X: 59, Y: 30}: "Санкт-Петербург (Эрмитаж)",
		{X: 55, Y: 49}: "Казань (Кремль)",
	}

	searchCoords := []Point{
		{X: 55, Y: 37},
		{X: 10, Y: 20},
	}

	for _, p := range searchCoords {
		if name, ok := landmarks[p]; ok {
			fmt.Printf("Координата %v: %s\n", p, name)
		} else {
			fmt.Printf("Координата %v: объект не найден\n", p)
		}
	}
}""",
                "note": "Поиск объектов по структуре Point"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Координата {55 37}: Москва (Кремль)
# Координата {10 20}: объект не найден""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Все поля структуры участвуют в вычислении хэш-суммы.
""",
        "pitfalls": """
- Изменение полей структуры: в Go ключи мапы копируются по значению, поэтому их нельзя изменить «снаружи».
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли использовать структуру с полями `[4]byte` как ключ в `map`?»
**Ответ:** ДА! Статические массивы сравнимы, поэтому структуры с массивами (`struct{ IP [4]byte }`) полностью comparable.
"""
    },
    {
        "num": 15,
        "title": "Частотный анализ символов текста map[rune]int с поддержкой Unicode",
        "task": "Постройте частотный словарь: на вход строка, на выход map[rune]int.",
        "theory": """
**Частотный анализ UTF-8 символов:**
- Итерация `for _, r := range text` декодирует UTF-8 поток в кодовые точки `rune` (`int32`);
- Мапа `map[rune]int` корректно подсчитывает частоту латиницы, кириллицы, иероглифов и эмодзи;
- Спецификатор `%c` выводит символ руны.
""",
        "step_by_step": """
1. Пишем функцию `RuneFrequency(text string) map[rune]int`.
2. Тестируем на мультиязычной строке `"Go — это огонь! 🚀"`.
3. Выводим результаты.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func RuneFrequency(text string) map[rune]int {
	freq := make(map[rune]int)
	for _, r := range text {
		freq[r]++
	}
	return freq
}

func main() {
	text := "Привет, мир! 🚀 Go Go Go!"
	counts := RuneFrequency(text)

	fmt.Printf("Исходный текст: %q\n", text)
	fmt.Println("Частота символов (рун):")
	for r, count := range counts {
		if r == ' ' {
			fmt.Printf("  • [ПРОБЕЛ] -> %d\n", count)
		} else {
			fmt.Printf("  • %-8c (код %5d) -> %d\n", r, r, count)
		}
	}
}""",
                "note": "Частотный анализ рун"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Исходный текст: "Привет, мир! 🚀 Go Go Go!"
# Частота символов (рун):
#   • П        (код  1055) -> 1
#   • р        (код  1088) -> 2
#   • и        (код  1080) -> 2
#   • в        (код  1074) -> 1
#   • е        (код  1077) -> 1
#   • т        (код  1090) -> 1
#   • ,        (код    44) -> 1
#   • [ПРОБЕЛ] -> 5
#   • м        (код  1084) -> 1
#   • !        (код    33) -> 4
#   • 🚀       (код 128640) -> 1
#   • G        (код    71) -> 3
#   • o        (код   111) -> 3""",
                "note": "Все Unicode символы подсчитаны"
            }
        ],
        "under_the_hood": """
`range` по строке вызывает декодер `runtime.decoderune`, возвращающий руну и ее длину в байтах.
""",
        "pitfalls": """
- Побайтовый обход `text[i]`, который разобьет русские буквы и эмодзи на некорректные половинки байт.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каков размер типа `rune` в памяти?»
**Ответ:** Тип `rune` является алиасом для `int32` и занимает ровно 4 байта.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 1: {len(exercises)} exercises.")
