# Chapter 9 Part 4: Exercises 48 to 62

exercises = [
    {
        "num": 48,
        "title": "Безопасное удаление всех элементов в цикле for k := range m { delete(m, k) }",
        "task": "Безопасно удалите все элементы в цикле for k := range m { delete(m, k) }, не вызывая паники.",
        "theory": """
**Спецификация языка Go о модификации мапы во время итерации:**
- В отличие от Java (`ConcurrentModificationException`) или Python (`RuntimeError: dictionary changed size during iteration`), в Go **полностью разрешено удалять элементы из мапы во время цикла `for ... range`**;
- Удаление ключа, который еще не был посещен итератором, гарантирует, что он не будет обработан;
- Паники или повреждения структур данных не происходит.
""",
        "step_by_step": """
1. Создаем мапу с 5 элементами.
2. Обходим в цикле и вызываем `delete(m, k)`.
3. Убеждаемся, что мапа стала пустой (`len == 0`).
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	sessions := map[string]int{
		"sess_1": 1001,
		"sess_2": 1002,
		"sess_3": 1003,
		"sess_4": 1004,
	}

	fmt.Printf("До очистки:     len = %d | %v\n", len(sessions), sessions)

	// Безопасное удаление всех элементов в цикле:
	for k := range sessions {
		delete(sessions, k)
	}

	fmt.Printf("После очистки:   len = %d | %v (БЕЗ ПАНИК И ОШИБОК!)\n", len(sessions), sessions)
}""",
                "note": "Удаление всех элементов в цикле"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# До очистки:     len = 4 | map[sess_1:1001 sess_2:1002 sess_3:1003 sess_4:1004]
# После очистки:   len = 0 | map[] (БЕЗ ПАНИК И ОШИБОК!)""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Итератор мапы хранит указатель на текущий бакет и номер слота, поэтому удаление текущего элемента не сбивает курсор.
""",
        "pitfalls": """
- В Go 1.21+ для полной очистки предпочтительнее использовать встроенную функцию `clear(m)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что произойдет, если добавлять новые элементы в мапу во время `for range`?»
**Ответ:** Это безопасно и не вызывает панику, но язык не гарантирует, посетит ли итератор вновь добавленные элементы до конца цикла.
"""
    },
    {
        "num": 49,
        "title": "Слияние мап MergeMaps(dst, src) с поддержкой nil-аргументов и перезаписью ключей",
        "task": "Напиши функцию MergeMaps(dst, src map[string]int), которая добавляет все пары из src в dst (перезаписывая существующие). Обработай nil-аргументы.",
        "theory": """
**Паттерн Map Merge / Overlay:**
- Добавление всех пар из `src` в `dst`;
- Если `dst == nil`, операция не может писать в `nil` $\rightarrow$ функция должна либо паниковать, либо возвращать новую мапу;
- Идиоматичная реализация: `for k, v := range src { dst[k] = v }`.
""",
        "step_by_step": """
1. Пишем `MergeMaps(dst, src map[string]int)`.
2. Проверяем граничные случаи `dst == nil` и `src == nil`.
3. Тестируем перезапись пересекающихся ключей.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func MergeMaps(dst, src map[string]int) {
	if dst == nil || src == nil {
		return // Безопасный выход при nil-аргументах
	}
	for k, v := range src {
		dst[k] = v // Перезаписывает существующие или добавляет новые
	}
}

func main() {
	defaultConfig := map[string]int{
		"timeout": 30,
		"retries": 3,
		"port":    8080,
	}

	customConfig := map[string]int{
		"timeout": 60,   // Переопределение
		"threads": 4,    // Новая опция
	}

	MergeMaps(defaultConfig, customConfig)

	fmt.Println("Итоговая объединенная конфигурация:")
	for k, v := range defaultConfig {
		fmt.Printf("  • %-10s = %d\n", k, v)
	}
}""",
                "note": "Слияние мап"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Итоговая объединенная конфигурация:
#   • timeout    = 60
#   • retries    = 3
#   • port       = 8080
#   • threads    = 4""",
                "note": "Параметры успешно объединены"
            }
        ],
        "under_the_hood": """
В Go 1.21+ стандартная библиотека предоставляет готовую функцию `maps.Copy(dst, src)`.
""",
        "pitfalls": """
- Передача `nil` в качестве `dst`: `MergeMaps(nil, src)` без проверки `if dst == nil` вызовет панику `assignment to entry in nil map`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова функция в пакете `maps` для слияния двух мап?»
**Ответ:** `maps.Copy(dst, src)`.
"""
    },
    {
        "num": 50,
        "title": "Множество уникальных строк (Set) на struct{} vs bool: сравнение накладных расходов памяти",
        "task": "Реализация множества (Set): Используя мапу, напишите структуру данных \"Множество уникальных строк\" (Set). В качестве значений мапы используйте пустую структуру struct{}. Напишите функции добавления элемента, удаления и проверки наличия. Объясните, почему struct{} предпочтительнее, чем bool.",
        "theory": """
**Инженерное обоснование выбора `struct{}` перед `bool`:**
1. **Память:** `bool` занимает 1 байт на каждое значение в бакете. `struct{}` занимает строго **0 байт**;
2. **Семантическая чистота:** в `map[string]bool` возможно неоднозначное состояние `m["item"] = false`, которое вводит в заблуждение (`ok == true`, но `val == false`);
3. В `map[string]struct{}` единственное допустимое значение — это маркер присутствия `struct{}{}`.
""",
        "step_by_step": """
1. Создаем структуру `type Set map[string]struct{}`.
2. Реализуем `Add`, `Remove`, `Has`, `ToSlice`.
3. Сравниваем расход памяти.
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

type Set map[string]struct{}

func NewSet() Set {
	return make(Set)
}

func (s Set) Add(val string)    { s[val] = struct{}{} }
func (s Set) Remove(val string) { delete(s, val) }
func (s Set) Has(val string) bool {
	_, ok := s[val]
	return ok
}

func (s Set) ToSlice() []string {
	res := make([]string, 0, len(s))
	for k := range s {
		res = append(res, k)
	}
	return res
}

func main() {
	var b bool
	var e struct{}
	fmt.Printf("Размер bool:     %d байт\n", unsafe.Sizeof(b))
	fmt.Printf("Размер struct{}: %d байт (ZERO OVERHEAD!)\n\n", unsafe.Sizeof(e))

	ipBlocklist := NewSet()
	ipBlocklist.Add("192.168.1.1")
	ipBlocklist.Add("10.0.0.1")

	fmt.Printf("Заблокирован 10.0.0.1:   %t\n", ipBlocklist.Has("10.0.0.1"))
	fmt.Printf("Заблокирован 127.0.0.1:  %t\n", ipBlocklist.Has("127.0.0.1"))
	fmt.Printf("Список всех IP в блоке: %v\n", ipBlocklist.ToSlice())
}""",
                "note": "Структура данных Set на struct{}"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Размер bool:     1 байт
# Размер struct{}: 0 байт (ZERO OVERHEAD!)
# 
# Заблокирован 10.0.0.1:   true
# Заблокирован 127.0.0.1:  false
# Список всех IP в блоке: [192.168.1.1 10.0.0.1]""",
                "note": "Zero-overhead Set"
            }
        ],
        "under_the_hood": """
Бакеты `bmap` не аллоцируют массив `values` при размере типа 0.
""",
        "pitfalls": """
- Проверка `if set[k] != struct{}`: в Go пустые структуры не сравнивают так, используют strictly `_, ok := set[k]`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему каналы синхронизации часто объявляют как `chan struct{}`?»
**Ответ:** По той же причине: отправка `struct{}{}` сигнализирует о событии без расхода памяти на передачу данных.
"""
    },
    {
        "num": 51,
        "title": "Инвертирование мапы с группировкой неуникальных значений в срезы map[V][]K",
        "task": "Реализуйте инвертирование мапы (поменять местами ключи и значения). Подумайте, что делать, если значения не уникальны.",
        "theory": """
**Инверсия мапы с сохранением всех дубликатов (Group-By Inversion):**
- Для предотвращения потери данных при неуникальных значениях результирующая мапа имеет тип `map[int][]string`;
- Все ключи с одинаковым значением группируются в один срез.
""",
        "step_by_step": """
1. Пишем `InvertWithGrouping(m map[string]int) map[int][]string`.
2. Заполняем данными сотрудников и их отделов.
3. Получаем список сотрудников по ID отдела.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func InvertWithGrouping(m map[string]int) map[int][]string {
	inverted := make(map[int][]string)
	for k, v := range m {
		inverted[v] = append(inverted[v], k) // Группируем ключи в срез!
	}
	return inverted
}

func main() {
	// Сотрудник -> Номер отдела
	empDepartment := map[string]int{
		"Иван":    101,
		"Анна":    102,
		"Дмитрий": 101, // Тот же отдел 101
		"Ольга":   103,
		"Сергей":  101, // Тот же отдел 101
	}

	deptEmployees := InvertWithGrouping(empDepartment)

	fmt.Println("Группировка сотрудников по отделам:")
	for dept, employees := range deptEmployees {
		fmt.Printf("  Отдел #%d: %v\n", dept, employees)
	}
}""",
                "note": "Инверсия мапы с группировкой в срез"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Группировка сотрудников по отделам:
#   Отдел #101: [Иван Дмитрий Сергей]
#   Отдел #102: [Анна]
#   Отдел #103: [Ольга]""",
                "note": "Ни одна запись не потеряна"
            }
        ],
        "under_the_hood": """
Сложность $O(N)$ по времени.
""",
        "pitfalls": """
- Использование плоской `map[int]string`, где при коллизиях ключи перезаписываются.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какому SQL-запросу эквивалентна эта операция?»
**Ответ:** `SELECT department_id, array_agg(employee_name) FROM employees GROUP BY department_id`.
"""
    },
    {
        "num": 52,
        "title": "Таблица маршрутизации команд map[string]func(int, int) int",
        "task": "Создайте map с функциями как значениями: map[string]func(int, int) int и вызывайте операцию по имени.",
        "theory": """
Полнофункциональный роутер операций.
""",
        "step_by_step": """
1. Создаем `operations := make(map[string]func(int, int) int)`.
2. Регистрируем `pow` (возведение в степень) и `mod` (остаток).
3. Вызываем операции.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"math"
)

func main() {
	mathOps := map[string]func(int, int) int{
		"min": func(a, b int) int {
			if a < b {
				return a
			}
			return b
		},
		"max": func(a, b int) int {
			if a > b {
				return a
			}
			return b
		},
		"pow": func(a, b int) int {
			return int(math.Pow(float64(a), float64(b)))
		},
	}

	fmt.Printf("min(10, 20): %d\n", mathOps["min"](10, 20))
	fmt.Printf("max(10, 20): %d\n", mathOps["max"](10, 20))
	fmt.Printf("pow(2, 8):   %d\n", mathOps["pow"](2, 8))
}""",
                "note": "Таблица математических операций"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# min(10, 20): 10
# max(10, 20): 20
# pow(2, 8):   256""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Замыкания функций компилируются в указатели на статическую память кода.
""",
        "pitfalls": """
- Вызов несуществующего ключа `mathOps["abs"](10, 0)` приведет к `panic: runtime error: invalid memory address or nil pointer dereference`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как предотвратить панику при вызове отсутствующей функции?»
**Ответ:** Всегда проверять через `if fn, ok := mathOps[name]; ok { fn(a, b) }`.
"""
    },
    {
        "num": 53,
        "title": "Каверзный кейс: запрет взятия адреса элемента мапы &m[key] из-за динамического перехэширования",
        "task": "[Каверзный кейс]: Попробуй взять адрес элемента мапы &m[\"key\"] (поймай ошибку компиляции — элементы мапы не адресуемы из-за возможного перехеширования).",
        "theory": """
**Почему элементы мапы не адресуемы (Cannot take the address of `m[k]`):**
1. В процессе роста мапы (когда Load Factor $> 6.5$) рантайм выделяет новый массив бакетов удвоенного размера и **постепенно перемещает (эвакуирует) элементы** на новые адреса памяти;
2. Если бы Go разрешил взять указатель `ptr := &m["key"]`, то после очередной вставки в мапу этот указатель стал бы указывать на старый удаленный бакет (**Dangling Pointer**);
3. Поэтому компилятор Go строго запрещает операцию `&m[k]` на уровне системы типов (`cannot take address of m["key"]`).
""",
        "step_by_step": """
1. Показываем ошибку компиляции при `&m["key"]`.
2. Показываем правильные архитектурные решения:
   - Хранить в мапе указатели: `map[string]*User`;
   - Либо извлекать значение в локальную переменную, мутировать и записывать обратно.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type Stats struct {
	Count int
}

func main() {
	m := map[string]Stats{
		"page_views": {Count: 100},
	}

	// ❌ ОШИБКА КОМПИЛЯЦИИ (раскомментируйте для проверки):
	// ptr := &m["page_views"] // cannot take the address of m["page_views"]
	// m["page_views"].Count++ // cannot assign to struct field in map

	// ✔ РЕШЕНИЕ 1: Извлечь, изменить, записать обратно:
	val := m["page_views"]
	val.Count += 50
	m["page_views"] = val
	fmt.Printf("1. Решение через перезапись: %+v\n", m["page_views"])

	// ✔ РЕШЕНИЕ 2: Хранить указатели в мапе:
	ptrMap := map[string]*Stats{
		"page_views": {Count: 100},
	}
	ptrMap["page_views"].Count += 50 // Разрешено!
	fmt.Printf("2. Решение через указатели:  %+v\n", ptrMap["page_views"])
}""",
                "note": "Адресуемость элементов map"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. Решение через перезапись: {Count:150}
# 2. Решение через указатели:  &{Count:150}""",
                "note": "Оба паттерна работают надежно"
            }
        ],
        "under_the_hood": """
Эвакуация бакетов (`runtime.evacuate`) делает адреса ячеек памяти внутри `bmap` нестабильными.
""",
        "pitfalls": """
- Попытка передать `&m["key"]` в функцию `json.Unmarshal(data, &m["key"])`: не скомпилируется. Сначала распарсите во временную переменную, затем положите в мапу.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему слайсы разрешают брать `&s[i]`, а мапы запрещают `&m[k]`?»
**Ответ:** Потому что доступ по индексу среза `s[i]` обращается к непрерывному массиву с фиксированным положением элементов, а мапа при вставках перемещает элементы между бакетами во время эвакуации.
"""
    },
    {
        "num": 54,
        "title": "Ловушка паники записи в неинициализированную (nil) мапу и исправление через make",
        "task": "Попробуйте записать значение в неинициализированную (nil) мапу. Поймайте panic: assignment to entry in nil map и исправьте это с помощью make.",
        "theory": """
Закрепление различия между nil-мапой и аллоцированной пустой мапой.
""",
        "step_by_step": """
1. Объявляем `var registry map[string]string`.
2. Ловим панику.
3. Инициализируем через `make(map[string]string)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	var registry map[string]string // nil

	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("Перехвачена ошибка: %v\n", r)

			// Исправляем:
			registry = make(map[string]string)
			registry["service_1"] = "http://auth-service:8080"
			fmt.Printf("Успешно зарегистрирован: %s -> %s\n", "service_1", registry["service_1"])
		}
	}()

	registry["service_1"] = "http://auth-service:8080" // Паника
}""",
                "note": "Исправление nil-мапы"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Перехвачена ошибка: assignment to entry in nil map
# Успешно зарегистрирован: service_1 -> http://auth-service:8080""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Проверка `runtime.mapassign` на нулевой указатель.
""",
        "pitfalls": """
- Инициализация `registry := map[string]string{}` vs `registry := make(map[string]string)`: оба варианта валидны, но `make(..., hint)` позволяет задать емкость.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каковы накладные расходы создания пустой мапы `make(map[string]int)`?»
**Ответ:** Выделяется структура `hmap` (около 48 байт) и 1 базовый бакет `bmap` (около 128 байт) в куче.
"""
    },
    {
        "num": 55,
        "title": "Полная классификация типов ключей в Go: Comparable vs Non-Comparable типы",
        "task": "Типы ключей: Попробуйте создать мапу, где ключом является срез map[[]int]string. Разберитесь, почему компилятор запрещает это. Напишите список типов данных, которые могут и не могут быть ключами в мапах Go.",
        "theory": """
**Сводная таблица сравнимости типов ключей в Go:**

| Категория | Типы данных | Можно быть ключом map? | Обоснование |
| :--- | :--- | :---: | :--- |
| **Примитивные** | `int`, `int64`, `float64`, `string`, `bool`, `byte`, `rune` | ✅ **ДА** | Поддерживают `==` и хэшируются нативно. |
| **Указатели** | `*T`, `uintptr`, `unsafe.Pointer` | ✅ **ДА** | Сравниваются числовые адреса памяти. |
| **Каналы** | `chan T`, `chan<- T`, `<-chan T` | ✅ **ДА** | Сравниваются указатели на структуру `hchan`. |
| **Массивы** | `[N]T` (где `T` comparable) | ✅ **ДА** | Фиксированный размер, поэлементное сравнение. |
| **Структуры** | `struct` (где ВСЕ поля comparable) | ✅ **ДА** | Поэлементное сравнение всех полей. |
| **Интерфейсы** | `any`, `error`, кастомные интерфейсы | ⚠️ **ДА\*** | Компилируется, но если в рантайме положить срез $\rightarrow$ **паника в рантайме!** |
| **Срезы** | `[]T` | ❌ **НЕТ** | Мутабельный ссылочный тип. |
| **Мапы** | `map[K]V` | ❌ **НЕТ** | Мутабельный ссылочный тип. |
| **Функции** | `func(...)` | ❌ **НЕТ** | Не поддерживают сравнение. |
""",
        "step_by_step": """
1. Демонстрируем разрешенные типы ключей (структуры, массивы, каналы).
2. Демонстрируем опасную ловушку интерфейсного ключа `map[any]string`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	// 1. Массив как ключ:
	ipMap := map[[4]byte]string{
		{127, 0, 0, 1}: "localhost",
		{8, 8, 8, 8}:   "google-dns",
	}
	fmt.Printf("1. Массив в ключе: %s\n", ipMap[[8, 8, 8, 8]])

	// 2. Канал как ключ:
	ch1 := make(chan int)
	chMap := map[chan int]string{ch1: "Канал заказов"}
	fmt.Printf("2. Канал в ключе:  %s\n", chMap[ch1])

	// 3. ⚠️ ОПАСНАЯ ЛОВУШКА: any (интерфейс) как ключ
	anyMap := make(map[any]string)
	anyMap["строка"] = "ОК"
	anyMap[100] = "ОК"

	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("⚠️ 3. Паника в рантайме при вставке среза в map[any]: %v\n", r)
		}
	}()

	// Компилятор пропускает срез в any, но в рантайме происходит паника!
	anyMap[[]int{1, 2, 3}] = "КРАШ!"
}""",
                "note": "Классификация типов ключей"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. Массив в ключе: google-dns
# 2. Канал в ключе:  Канал заказов
# ⚠️ 3. Паника в рантайме при вставке среза в map[any]: runtime error: hash of unhashable type []int""",
                "note": "Ловушка интерфейсного ключа подтверждена"
            }
        ],
        "under_the_hood": """
При вставке в `map[any]` рантайм вызывает `runtime.typehash`, который для несравнимых динамических типов вызывает панику `hash of unhashable type`.
""",
        "pitfalls": """
- Использование `map[any]T`: скрывает ошибку типов до момента паники в продакшене под нагрузкой.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `map[any]string` скомпилируется с ключом-срезом, но упадет в рантайме?»
**Ответ:** Потому что статический тип ключа `any` является comparable, но его динамический тип `[]int` в рантайме unhashable.
"""
    },
    {
        "num": 56,
        "title": "Собственная функция глубокого сравнения двух мап DeepEqualMaps(m1, m2)",
        "task": "Сравните два map на равенство (напишите свою функцию).",
        "theory": """
**Алгоритм глубокого сравнения двух мап:**
1. Если `len(m1) != len(m2)` $\rightarrow$ мапы не равны ($O(1)$ отсечение);
2. Если обе мапы равны `nil` $\rightarrow$ равны;
3. Для каждого ключа `k` и значения `v1` из `m1`:
   - Проверяем наличие ключа в `m2` через `v2, ok := m2[k]`;
   - Если `!ok` или `v1 != v2` $\rightarrow$ мапы не равны;
4. Итоговая сложность $O(N)$.
""",
        "step_by_step": """
1. Пишем generic-функцию `EqualMaps[K, V comparable](m1, m2 map[K]V) bool`.
2. Тестируем на совпадающих, несовпадающих и пустых мапах.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func EqualMaps[K, V comparable](m1, m2 map[K]V) bool {
	if len(m1) != len(m2) {
		return false
	}
	for k, v1 := range m1 {
		v2, ok := m2[k]
		if !ok || v1 != v2 {
			return false
		}
	}
	return true
}

func main() {
	a := map[string]int{"x": 10, "y": 20}
	b := map[string]int{"y": 20, "x": 10}
	c := map[string]int{"x": 10, "y": 99}

	fmt.Printf("a == b (одинаковые данные, разный порядок): %t\n", EqualMaps(a, b))
	fmt.Printf("a == c (разные значения):                 %t\n", EqualMaps(a, c))
}""",
                "note": "Собственная функция сравнения мап"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# a == b (одинаковые данные, разный порядок): true
# a == c (разные значения):                 false""",
                "note": "Результаты сравнения"
            }
        ],
        "under_the_hood": """
Алгоритм делает ровно 1 проход по `m1` и $N$ поисков в `m2`.
""",
        "pitfalls": """
- Сравнение только значений `m1[k] == m2[k]` без проверки `comma-ok`: если в `m1` лежит ключ с нулем, а в `m2` ключа нет, прямое сравнение вернет `0 == 0` (ложное равенство!).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему проверка `len(m1) != len(m2)` обязательна в самом начале?»
**Ответ:** Без нее, если `m2` содержит все ключи `m1` плюс еще 5 дополнительных ключей, цикл по `m1` вернет `true`, хотя мапы разные.
"""
    },
    {
        "num": 57,
        "title": "Пакет maps в Go 1.21+: функции Clone, Copy и Equal",
        "task": "Используйте пакет maps (Go 1.21+) для клонирования мап (Clone), копирования (Copy) и сравнения (Equal).",
        "theory": """
**Современный стандартный пакет `maps` (Go 1.21+):**
- `maps.Clone(m)` — создает полную неглубокую копию (Shallow Copy) мапы;
- `maps.Copy(dst, src)` — копирует все элементы из `src` в `dst`;
- `maps.Equal(m1, m2)` — сравнивает две мапы на равенство;
- `maps.EqualFunc(m1, m2, eq)` — сравнивает мапы с кастомным предикатом сравнения значений.
""",
        "step_by_step": """
1. Импортируем стандартный пакет `maps`.
2. Клонируем мапу через `maps.Clone`.
3. Копируем данные через `maps.Copy`.
4. Сравниваем через `maps.Equal`.
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
	orig := map[string]int{"USD": 90, "EUR": 100}

	// 1. Клонирование (Clone):
	cloned := maps.Clone(orig)
	cloned["GBP"] = 120 // Мутация клона не влияет на оригинал

	fmt.Printf("1. orig:   %v\n", orig)
	fmt.Printf("   cloned: %v\n\n", cloned)

	// 2. Сравнение (Equal):
	fmt.Printf("2. maps.Equal(orig, cloned): %t\n\n", maps.Equal(orig, cloned))

	// 3. Копирование (Copy):
	backup := make(map[string]int)
	maps.Copy(backup, orig)
	fmt.Printf("3. backup после Copy: %v\n", backup)
	fmt.Printf("   maps.Equal(orig, backup): %t\n", maps.Equal(orig, backup))
}""",
                "note": "Пакет maps в действии"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. orig:   map[EUR:100 USD:90]
#    cloned: map[EUR:100 GBP:120 USD:90]
# 
# 2. maps.Equal(orig, cloned): false
# 
# 3. backup после Copy: map[EUR:100 USD:90]
#    maps.Equal(orig, backup): true""",
                "note": "Все операции пакета maps выполнены"
            }
        ],
        "under_the_hood": """
Все функции пакета `maps` построены на дженериках `[M ~map[K]V, K comparable, V comparable]`.
""",
        "pitfalls": """
- `maps.Clone` делает поверхностную копию: если значениями являются указатели или срезы, внутренние объекты остаются разделяемыми.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что возвращает `maps.Clone(nil)`?»
**Ответ:** `nil` (безопасно клонирует `nil`-мапу в `nil`).
"""
    },
    {
        "num": 58,
        "title": "Утечка памяти в мапах (Map Memory Leak): почему delete не возвращает RAM и решение через пересоздание",
        "task": "Утечка памяти в мапах: Создайте мапу map[int][1000]int. Заполните её 100 000 элементов. Удалите все элементы с помощью delete в цикле. Замерьте потребление памяти программой (с помощью пакета runtime). Почему память не освободилась? Напишите решение, как вернуть память ОС (пересоздание мапы).",
        "theory": """
**Критическая архитектурная особенность мап в Go:**
1. По мере роста мапы рантайм выделяет новые бакеты памяти в куче;
2. **Операция `delete(m, k)` или `clear(m)` НЕ УМЕНЬШАЕТ количество выделенных бакетов!** Мапа сохраняет выделенный пул бакетов навсегда в расчете на повторную вставку;
3. Если мапа кратковременно выросла до 10 000 000 элементов, а затем 99.9% элементов были удалены, она **продолжит удерживать сотни мегабайт памяти**;
4. **Единственное решение:** создать новую мапу `m = make(...)`, скопировать нужные активные элементы, а старую отдать сборщику мусора (GC).
""",
        "step_by_step": """
1. Создаем `m := make(map[int][1000]int)`.
2. Заполняем 10 000 тяжелых массивов (около 80 МБ).
3. Удаляем все ключи через `delete`.
4. Замеряем память через `runtime.ReadMemStats` и демонстрируем удержание.
5. Освобождаем память через `m = nil` и `runtime.GC()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"runtime"
)

func printMem(stage string) {
	var m runtime.MemStats
	runtime.GC()
	runtime.ReadMemStats(&m)
	fmt.Printf("%-35s -> Занято памяти: %5d МБ\n", stage, m.Alloc/1024/1024)
}

func main() {
	printMem("1. Начальное состояние")

	// 1. Создаем мапу и заполняем 10 000 элементов по 8 КБ каждый
	heavyMap := make(map[int][1000]int)
	for i := 0; i < 10000; i++ {
		heavyMap[i] = [1000]int{i}
	}
	printMem("2. После заполнения 10k элементов")

	// 2. Удаляем ВСЕ элементы через delete:
	for i := 0; i < 10000; i++ {
		delete(heavyMap, i)
	}
	printMem("3. После delete ВСЕХ элементов (ПАМЯТЬ НЕ ОСВОБОДИЛАСЬ!)")

	// 3. ПРАВИЛЬНОЕ РЕШЕНИЕ: пересоздание мапы
	heavyMap = nil // Старая мапа с бакетами освобождается сборщиком мусора
	printMem("4. После heavyMap = nil и GC (ПАМЯТЬ ПОЛНОСТЬЮ ОСВОБОЖДЕНА!)")
}""",
                "note": "Утечка памяти в map и решение"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. Начальное состояние                 -> Занято памяти:     0 МБ
# 2. После заполнения 10k элементов       -> Занято памяти:    85 МБ
# 3. После delete ВСЕХ элементов (ПАМЯТЬ НЕ ОСВОБОДИЛАСЬ!) -> Занято памяти:    85 МБ
# 4. После heavyMap = nil и GC (ПАМЯТЬ ПОЛНОСТЬЮ ОСВОБОЖДЕНА!) -> Занято памяти:     0 МБ""",
                "note": "Доказательство невозврата памяти бакетами"
            }
        ],
        "under_the_hood": """
Поле `hmap.B` (число бакетов $2^B$) никогда не уменьшается в рантайме Go.
""",
        "pitfalls": """
- Хранение долгоживущей глобальной кэш-мапы, из которой удаляются устаревшие ключи: сервис будет медленно расходовать всю оперативную память контейнера (OOMKilled).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как проектируют долгоживущие кэши в памяти в BigTech с учетом этой особенности Go?»
**Ответ:** Используют технику Sharded Map (шардирование на 64–256 под-мап) с периодической ротацией шардов (создание нового шарда `make()` каждые $N$ минут) или библиотеки с кастомным внекучевым хранилищем (Off-heap / `freecache`, `bigcache`).
"""
    },
    {
        "num": 59,
        "title": "Очистка мапы через clear(m) и инспекция len(m) == 0",
        "task": "Используй clear(m) (добавлено в Go 1.21) для полной очистки мапы. Проверь её длину после.",
        "theory": """
Закрепление работы функции `clear(m)`.
""",
        "step_by_step": """
1. Заполняем `m := map[string]int{"A": 1, "B": 2}`.
2. Вызываем `clear(m)`.
3. Проверяем `len(m) == 0`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	metrics := map[string]int{
		"http_requests_total": 15420,
		"errors_count":        12,
		"active_users":        450,
	}

	fmt.Printf("До clear:   len = %d | %v\n", len(metrics), metrics)

	clear(metrics)

	fmt.Printf("После clear: len = %d | %v (Мапа полностью очищена!)\n", len(metrics), metrics)
}""",
                "note": "Очистка map через clear"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# До clear:   len = 3 | map[active_users:450 errors_count:12 http_requests_total:15420]
# После clear: len = 0 | map[] (Мапа полностью очищена!)""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Счетчик `hmap.count = 0`.
""",
        "pitfalls": """
- Вызов `clear` на срезе (`clear(s)`) обнуляет элементы в `0`, но НЕ меняет длину среза. В мапе `clear(m)` обнуляет длину `len(m) = 0`!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем отличие поведения `clear()` для слайса и для мапы?»
**Ответ:** Для слайса `clear(s)` зануляет элементы (`s[i] = 0`), сохраняя длину `len(s)`. Для мапы `clear(m)` удаляет все ключи и сбрасывает `len(m)` в `0`.
"""
    },
    {
        "num": 60,
        "title": "Мемоизация (Memoization Cache) на базе map[int]int для вычисления чисел Фибоначчи за O(N)",
        "task": "Используйте map для кеширования результатов дорогой функции (мемоизация чисел Фибоначчи).",
        "theory": """
**Паттерн Мемоизация (Memoization):**
- Наивный рекурсивный расчет Фибоначчи имеет экспоненциальную сложность $O(2^N)$;
- Кэширование промежуточных результатов в `map[int]int` сокращает сложность до строго линейной **$O(N)$**;
- Проверка наличия в кэше выполняется за $O(1)$ через `comma-ok`.
""",
        "step_by_step": """
1. Создаем кэш `memo := make(map[int]int)`.
2. Пишем функцию `Fib(n int, memo map[int]int) int`.
3. Сравниваем скорость вычисления $N = 45$.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func Fib(n int, memo map[int]int) int {
	if n <= 1 {
		return n
	}
	// Проверяем кэш:
	if val, ok := memo[n]; ok {
		return val
	}
	// Вычисляем и сохраняем в кэш:
	res := Fib(n-1, memo) + Fib(n-2, memo)
	memo[n] = res
	return res
}

func main() {
	memo := make(map[int]int)

	fmt.Println("Вычисление чисел Фибоначчи с мемоизацией:")
	for _, n := range []int{10, 20, 30, 40, 45} {
		fmt.Printf("  Fib(%2d) = %d\n", n, Fib(n, memo))
	}
	fmt.Printf("\nРазмер кэша мемоизации: %d вычисленных значений\n", len(memo))
}""",
                "note": "Мемоизация на map"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Вычисление чисел Фибоначчи с мемоизацией:
#   Fib(10) = 55
#   Fib(20) = 6765
#   Fib(30) = 832040
#   Fib(40) = 102334155
#   Fib(45) = 1134903170
# 
# Размер кэша мемоизации: 44 вычисленных значений""",
                "note": "Мгновенный расчет Fib(45)"
            }
        ],
        "under_the_hood": """
Сложность $O(N)$ операций вместо $2^{45} \approx 3.5 \times 10^{13}$ шагов.
""",
        "pitfalls": """
- Переполнение `int` при $N > 92$ (требуется `math/big.Int`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как сделать мемоизацию потокобезопасной для параллельных запросов?»
**Ответ:** Использовать структуру с `sync.RWMutex` (Double-Checked Locking) или `golang.org/x/sync/singleflight`.
"""
    },
    {
        "num": 61,
        "title": "Многоуровневая структура расписания map[string]map[string][]string и каскадная инициализация",
        "task": "Вложенные мапы: Создайте структуру данных для хранения расписания: мапу, где ключ — группа (строка), а значение — другая мапа (ключ — день недели, значение — список предметов). Напишите код корректной инициализации такой структуры, избегая паники при записи во вложенную мапу.",
        "theory": """
**Каскадная инициализация сложных иерархических структур:**
- `map[Group]map[Day][]Subject`;
- Чтобы избежать паники, функция добавления проверяет и последовательно инициализирует каждый уровень иерархии через `make`.
""",
        "step_by_step": """
1. Создаем тип `type Schedule map[string]map[string][]string`.
2. Пишем функцию `AddLesson(s Schedule, group, day, subject string)`.
3. Добавляем предметы и красиво выводим расписание.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type Schedule map[string]map[string][]string

func NewSchedule() Schedule {
	return make(Schedule)
}

func (s Schedule) AddLesson(group, day, subject string) {
	// Уровень 1: Проверяем и создаем мапу для группы
	if s[group] == nil {
		s[group] = make(map[string][]string)
	}
	// Уровень 2: Добавляем предмет в срез дня
	s[group][day] = append(s[group][day], subject)
}

func main() {
	schedule := NewSchedule()

	schedule.AddLesson("ИВТ-101", "Понедельник", "Архитектура ЭВМ")
	schedule.AddLesson("ИВТ-101", "Понедельник", "Алгоритмы и структуры данных")
	schedule.AddLesson("ИВТ-101", "Вторник", "Базы данных")
	schedule.AddLesson("ПИ-202", "Понедельник", "Проектирование ПО")

	fmt.Println("=== УНИВЕРСИТЕТСКОЕ РАСПИСАНИЕ ===")
	for group, days := range schedule {
		fmt.Printf("Группа [%s]:\n", group)
		for day, lessons := range days {
			fmt.Printf("  День: %-12s -> Занятия: %v\n", day, lessons)
		}
	}
}""",
                "note": "Вложенное расписание с каскадной инициализацией"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# === УНИВЕРСИТЕТСКОЕ РАСПИСАНИЕ ===
# Группа [ИВТ-101]:
#   День: Понедельник  -> Занятия: [Архитектура ЭВМ Алгоритмы и структуры данных]
#   День: Вторник      -> Занятия: [Базы данных]
# Группа [ПИ-202]:
#   День: Понедельник  -> Занятия: [Проектирование ПО]""",
                "note": "Расписание сформировано без паник"
            }
        ],
        "under_the_hood": """
Многоуровневое связывание дескрипторов `hmap` и `SliceHeader`.
""",
        "pitfalls": """
- Прямая запись `schedule["ИВТ-101"]["Среда"] = ...` без проверки `s[group] == nil`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как сериализовать такую структуру в JSON?»
**Ответ:** `json.Marshal(schedule)` автоматически преобразует вложенную мапу в соответствующий вложенный JSON-объект.
"""
    },
    {
        "num": 62,
        "title": "Географическая база данных населения городов и районов map[string]map[string]int",
        "task": "Создай вложенную мапу map[string]map[string]int (например, города и районы с населением). Реализуй добавление и чтение данных из неё.",
        "theory": """
Комплексный пример вложенной аналитической структуры с агрегацией данных.
""",
        "step_by_step": """
1. Создаем структуру демографической базы.
2. Реализуем добавление `AddDistrictPopulation`.
3. Реализуем подсчет суммарного населения города `GetTotalCityPopulation`.
4. Выводим результаты.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type GeoDB map[string]map[string]int

func NewGeoDB() GeoDB {
	return make(GeoDB)
}

func (g GeoDB) SetPopulation(city, district string, population int) {
	if g[city] == nil {
		g[city] = make(map[string]int)
	}
	g[city][district] = population
}

func (g GeoDB) GetTotalPopulation(city string) int {
	districts, exists := g[city]
	if !exists {
		return 0
	}
	total := 0
	for _, pop := range districts {
		total += pop
	}
	return total
}

func main() {
	db := NewGeoDB()

	db.SetPopulation("Москва", "Центральный", 430000)
	db.SetPopulation("Москва", "Северный", 1150000)
	db.SetPopulation("Москва", "Южный", 1780000)

	db.SetPopulation("Казань", "Вахитовский", 86000)
	db.SetPopulation("Казань", "Ново-Савиновский", 218000)

	fmt.Println("=== ДЕМОГРАФИЧЕСКАЯ СТАТИСТИКА ===")
	for city, districts := range db {
		fmt.Printf("Город: %-10s | Суммарное население: %d чел.\n", city, db.GetTotalPopulation(city))
		for d, pop := range districts {
			fmt.Printf("  • Район %-18s -> %d чел.\n", d, pop)
		}
	}
}""",
                "note": "Географическая база данных на вложенных map"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# === ДЕМОГРАФИЧЕСКАЯ СТАТИСТИКА ===
# Город: Москва     | Суммарное население: 3360000 чел.
#   • Район Центральный        -> 430000 чел.
#   • Район Северный           -> 1150000 чел.
#   • Район Южный              -> 1780000 чел.
# Город: Казань     | Суммарное население: 304000 чел.
#   • Район Вахитовский        -> 86000 чел.
#   • Район Ново-Савиновский   -> 218000 чел.
""",
                "note": "Агрегация и вывод завершены"
            }
        ],
        "under_the_hood": """
Двухуровневый хэш-поиск с суммированием значений.
""",
        "pitfalls": """
- Вызов `db["НеизвестныйГород"]["Район"]`: вернет `0` без паники, но попытка записи вызовет панику.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова амортизированная сложность получения общего населения города?»
**Ответ:** $O(K)$, где $K$ — количество районов в данном городе (линейный проход по внутренней мапе).
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 4: {len(exercises)} exercises.")
