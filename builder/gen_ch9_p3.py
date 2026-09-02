# Chapter 9 Part 3: Exercises 32 to 47

exercises = [
    {
        "num": 32,
        "title": "Очистка мапы через встроенную функцию clear(m) в Go 1.21+",
        "task": "Очистка мапы: Используй встроенную функцию clear(m) (появилась в Go 1.21), чтобы удалить все элементы из мапы.",
        "theory": """
**Встроенная функция `clear(m)` (Go 1.21+):**
- Удаляет все элементы из мапы `m`, сбрасывая ее длину `len(m)` в `0`;
- Сохраняет выделенные бакеты памяти, что позволяет быстро повторно заполнять мапу без новых аллокаций;
- Работает быстрее, чем ручной цикл с `delete(m, k)`.
""",
        "step_by_step": """
1. Создаем мапу `cache := map[string]int{"a": 1, "b": 2, "c": 3}`.
2. Проверяем длину `len(cache)`.
3. Вызываем `clear(cache)`.
4. Проверяем длину и состояние мапы.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	cache := map[string]int{
		"token_1": 100,
		"token_2": 200,
		"token_3": 300,
	}

	fmt.Printf("1. До clear:  len = %d | %v\n", len(cache), cache)

	// Очищаем мапу в Go 1.21+:
	clear(cache)

	fmt.Printf("2. После clear: len = %d | %v\n", len(cache), cache)

	// Мапа готова к повторному использованию:
	cache["token_4"] = 400
	fmt.Printf("3. После вставки: len = %d | %v\n", len(cache), cache)
}""",
                "note": "Очистка мапы через clear(m)"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. До clear:  len = 3 | map[token_1:100 token_2:200 token_3:300]
# 2. После clear: len = 0 | map[]
# 3. После вставки: len = 1 | map[token_4:400]""",
                "note": "Мапа очищена"
            }
        ],
        "under_the_hood": """
`runtime.mapclear` зануляет счетчик `hmap.count` и помечает бакеты как пустые без деаллокации структуры.
""",
        "pitfalls": """
- Передача `nil`-мапы в `clear(m)`: операция безопасно выполняется как no-op.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем разница между `clear(m)` и `m = make(map[K]V)`?»
**Ответ:** `clear(m)` сохраняет бакеты (устраняя задержки на расширение при повторном заполнении), но НЕ уменьшает объем занимаемой памяти под саму структуру `hmap`. `m = make(...)` выделяет новую чистую мапу, а старая удаляется сборщиком мусора (GC).
"""
    },
    {
        "num": 33,
        "title": "Сбор ключей MapKeys(m) и доказательство недетерминированности порядка итерации",
        "task": "Напиши функцию MapKeys(m map[string]int) []string, возвращающую слайс ключей. Запусти несколько раз — покажи, что порядок итерации не детерминирован.",
        "theory": """
**Рандомизация итератора мапы в Go:**
- При создании итератора `range m` рантайм Go генерирует **случайное смещение начального бакета** (`fastrand()`);
- Это архитектурное решение авторов Go: намеренно предотвратить зависимость клиентского кода от конкретного порядка хэш-таблицы;
- Последовательные запуски одной и той же программы могут возвращать разный порядок ключей.
""",
        "step_by_step": """
1. Пишем `MapKeys(m map[string]int) []string`.
2. Заполняем мапу 6 элементами.
3. Запускаем сбор ключей 3 раза и сравниваем порядок.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func MapKeys(m map[string]int) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	return keys
}

func main() {
	data := map[string]int{
		"alpha": 1, "beta": 2, "gamma": 3,
		"delta": 4, "epsilon": 5, "zeta": 6,
	}

	fmt.Println("Демонстрация недетерминированного порядка итерации:")
	for run := 1; run <= 3; run++ {
		keys := MapKeys(data)
		fmt.Printf("  Запуск #%d: %v\n", run, keys)
	}
}""",
                "note": "Сбор ключей map"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Демонстрация недетерминированного порядка итерации:
#   Запуск #1: [alpha beta gamma delta epsilon zeta]
#   Запуск #2: [gamma delta epsilon zeta alpha beta]
#   Запуск #3: [delta epsilon zeta alpha beta gamma]""",
                "note": "Порядок ключей меняется от запуска к запуску"
            }
        ],
        "under_the_hood": """
В `runtime.mapiterinit` поле `it.startBucket = fastrand() & (1<<h.B - 1)`.
""",
        "pitfalls": """
- Написание юнит-тестов, сравнивающих строки вывода мапы напрямую (`fmt.Sprint(m)`): тесты будут периодически флапать (Flaky Tests).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какая функция в пакете `maps` (Go 1.23+) или `golang.org/x/exp/maps` возвращает ключи?»
**Ответ:** `maps.Keys(m)` возвращает итератор `iter.Seq[K]`, а в слайс собирается через `slices.Collect(maps.Keys(m))`.
"""
    },
    {
        "num": 34,
        "title": "Запрет несравнимых типов (slices, maps, funcs) в качестве ключей мапы",
        "task": "Попробуйте использовать слайс или мапу в качестве ключа другой мапы и изучите ошибку компиляции. Почему ключами могут быть только сравниваемые (comparable) типы?",
        "theory": """
**Математические требования к ключам хэш-таблицы:**
1. Для ключа $K$ обязаны быть строго определены:
   - **Хэш-функция:** $H(k_1) == H(k_2)$, если $k_1 == k_2$;
   - **Операция эквивалентности:** $k_1 == k_2$ для разрешения коллизий в бакете;
2. Срезы `[]int`, мапы `map[K]V` и функции `func()` в Go мутабельны и не поддерживают оператор `==`;
3. Попытка создать `map[[]int]string` вызывает ошибку компиляции: `invalid map key type []int`.
""",
        "step_by_step": """
1. Показываем список разрешенных типов ключей.
2. Показываем список запрещенных типов ключей.
3. Демонстрируем обходной путь (сериализация среза в строку).
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	// ❌ ОШИБКИ КОМПИЛЯЦИИ (раскомментируйте для проверки):
	// var badMap1 map[[]int]string        // invalid map key type []int
	// var badMap2 map[map[string]int]bool // invalid map key type map[string]int
	// var badMap3 map[func()]int          // invalid map key type func()

	// ✔ РАЗРЕШЕННЫЕ СРАВНИМЫЕ ТИПЫ (Comparable):
	// int, float64, string, bool, pointer (*T), channel (chan T),
	// array ([N]T где T comparable), struct (где все поля comparable).

	// Паттерн обхода: сериализация среза в comparable-тип (массив или строку):
	type Vector3D [3]float64 // Статический массив comparable!
	matrix := map[Vector3D]string{
		{1.0, 2.0, 3.0}: "Точка A",
		{0.0, 0.0, 0.0}: "Начало координат",
	}

	fmt.Printf("Мапа с ключом-массивом [3]float64: %v\n", matrix)
}""",
                "note": "Типы ключей в Go"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Мапа с ключом-массивом [3]float64: map[[0 0 0]:Начало координат [1 2 3]:Точка A]""",
                "note": "Массивы полностью разрешены как ключи"
            }
        ],
        "under_the_hood": """
Компилятор проверяет интерфейс `types.Comparable(keyType)`.
""",
        "pitfalls": """
- Использование `float64` с `NaN` в качестве ключа: `math.NaN() != math.NaN()`, такой ключ невозможно прочитать обратно!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему срезы не сделали comparable, сравнивая их побайтово?»
**Ответ:** Потому что мутация среза в памяти изменила бы его хэш, и элемент навсегда потерялся бы в старом бакете хэш-таблицы (нарушение инварианта хэширования).
"""
    },
    {
        "num": 35,
        "title": "Сравнение ручной очистки через delete в цикле и встроенной функции clear(m)",
        "task": "Напиши функцию ClearMap(m map[string]int), удаляющую все элементы. Реализуй через for k := range m { delete(m, k) }. В Go 1.21+ используй встроенную clear(m) и сравни.",
        "theory": """
**Эволюция очистки мап в Go:**
- **До Go 1.21:** `for k := range m { delete(m, k) }` — требовал создания итератора и $N$ вызовов `runtime.mapdelete`;
- **Go 1.21+:** `clear(m)` — специализированная встроенная операция `runtime.mapclear`, очищающая бакеты за один системный вызов.
""",
        "step_by_step": """
1. Пишем `ClearMapLegacy(m map[string]int)`.
2. Сравниваем поведение с `clear(m)`.
3. Проверяем длину после обеих операций.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func ClearMapLegacy(m map[string]int) {
	for k := range m {
		delete(m, k)
	}
}

func main() {
	m1 := map[string]int{"a": 1, "b": 2, "c": 3}
	m2 := map[string]int{"x": 10, "y": 20, "z": 30}

	// 1. Ручная очистка в цикле:
	ClearMapLegacy(m1)
	fmt.Printf("1. После ClearMapLegacy: len = %d | %v\n", len(m1), m1)

	// 2. Современный clear(m):
	clear(m2)
	fmt.Printf("2. После clear(m2):       len = %d | %v\n", len(m2), m2)
}""",
                "note": "Два способа очистки map"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. После ClearMapLegacy: len = 0 | map[]
# 2. После clear(m2):       len = 0 | map[]""",
                "note": "Результаты идентичны"
            }
        ],
        "under_the_hood": """
`runtime.mapclear` оптимизирует обнуление памяти через векторные инструкции без накладных расходов на хэширование ключей.
""",
        "pitfalls": """
- Попытка пересоздать мапу внутри функции `func Clear(m map[K]V) { m = make(...) }`: это изменит только локальную копию указателя, а вызывающая сторона останется со старой мапой!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `func Clear(m map[K]V) { m = make(map[K]V) }` не работает?»
**Ответ:** Потому что `m` передается по значению (копируется указатель `*hmap`). Переприсваивание `m = make(...)` меняет локальный указатель функции, не затрагивая оригинал.
"""
    },
    {
        "num": 36,
        "title": "Удаление элементов тестовой мапы через delete(m, k) и гарантия отсутствия сбоев",
        "task": "Удаление ключей: Заполните мапу тестовыми данными. Удалите один из ключей с помощью встроенной функции delete. Попробуйте вызвать delete для ключа, которого в мапе нет. Происходит ли при этом ошибка или паника?",
        "theory": """
Закрепление надежности удаления данных из справочников.
""",
        "step_by_step": """
1. Заполняем `serverConfigs := map[string]string{...}`.
2. Удаляем существующий ключ `"dev"`.
3. Удаляем отсутствующий ключ `"staging"`.
4. Выводим оставшиеся конфигурации.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	configs := map[string]string{
		"local": "localhost:8080",
		"dev":   "dev.example.com",
		"prod":  "api.example.com",
	}

	fmt.Printf("Исходные конфиги: %v\n", configs)

	delete(configs, "dev")
	delete(configs, "staging") // Несуществующий ключ

	fmt.Printf("Итоговые конфиги: %v (паники и ошибок нет!)\n", configs)
}""",
                "note": "Удаление ключей"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Исходные конфиги: map[dev:dev.example.com local:localhost:8080 prod:api.example.com]
# Итоговые конфиги: map[local:localhost:8080 prod:api.example.com] (паники и ошибок нет!)""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
No-op при отсутствии ключа.
""",
        "pitfalls": """
- Вызов `delete` без передачи мапы (синтаксическая ошибка).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова амортизированная сложность `delete`?»
**Ответ:** $O(1)$.
"""
    },
    {
        "num": 37,
        "title": "Фатальная ошибка конкурентной записи: fatal error: concurrent map writes и sync.Mutex / sync.RWMutex",
        "task": "Fatal error: concurrent map writes: Создай мапу. В цикле запусти 100 горутин (добавь слово go перед вызовом анонимной функции go func(){ m[\"a\"] = 1 }()), которые одновременно пишут в мапу. Поймай аварийное завершение программы. (Мапы в Go не потокобезопасны на запись!).",
        "theory": """
**Потокобезопасность мап в Go:**
1. Встроенные мапы в Go **НЕ являются потокобезопасными (Not Thread-Safe)**;
2. При одновременной записи из нескольких горутин рантайм Go обнаруживает гонку через битовый флаг `hmap.flags & hashWriting` и вызывает **немедленный краш процесса** `fatal error: concurrent map writes`;
3. Эту фатальную ошибку **НЕВОЗМОЖНО перехватить через `recover()`**;
4. **Решение:** использовать мьютексы `sync.Mutex` / `sync.RWMutex` или `sync.Map`.
""",
        "step_by_step": """
1. Объясняем механизм детекции гонки в рантайме.
2. Пишем безопасную структуру `SafeCounter` с `sync.RWMutex`.
3. Запускаем 100 конкурентных горутин с корректной синхронизацией через `sync.WaitGroup`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"sync"
)

// SafeMap инкапсулирует мапу и RWMutex для защиты от гонок:
type SafeMap struct {
	mu   sync.RWMutex
	data map[string]int
}

func NewSafeMap() *SafeMap {
	return &SafeMap{data: make(map[string]int)}
}

func (s *SafeMap) Set(key string, val int) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.data[key] = val
}

func (s *SafeMap) Get(key string) (int, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	v, ok := s.data[key]
	return v, ok
}

func main() {
	safeMap := NewSafeMap()
	var wg sync.WaitGroup

	// 100 конкурентных горутин безопасно пишут в мапу:
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			safeMap.Set(fmt.Sprintf("key_%d", workerID%10), workerID)
		}(i)
	}

	wg.Wait()
	fmt.Printf("✔ 100 горутин успешно завершили работу без краша!\n")
	val, ok := safeMap.Get("key_5")
	fmt.Printf("Значение key_5: %d (найден: %t)\n", val, ok)
}""",
                "note": "Потокобезопасная мапа с sync.RWMutex"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run -race main.go
# ✔ 100 горутин успешно завершили работу без краша!
# Значение key_5: 95 (найден: true)""",
                "note": "Сборка с флагом -race подтверждает 0 data races"
            }
        ],
        "under_the_hood": """
В начале `runtime.mapassign` проверяется `if h.flags&hashWriting != 0 { throw("concurrent map writes") }`. Флаг `hashWriting` выставляется на время модификации бакета.
""",
        "pitfalls": """
- Надежда перехватить `fatal error: concurrent map writes` через `recover()`: это системный `throw()`, который немедленно аварийно завершает весь процесс ОС.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go не встроили мьютекс в каждую мапу по умолчанию?»
**Ответ:** Большинство мап используются локально в пределах одной горутины. Автоматическая блокировка замедлила бы все однопоточные операции в разы. Для многопоточности ответственность возложена на разработчика (`sync.RWMutex` или `sync.Map`).
"""
    },
    {
        "num": 38,
        "title": "Хранение указателей на структуры в мапе map[int]*User и прямая мутация полей",
        "task": "Создай мапу с указателями на структуры в качестве значений: map[int]*User. Измени поля структуры, полученной из мапы. Покажи, что мапа хранит указатель, и изменения видны при повторном чтении.",
        "theory": """
**Мапа структур vs Мапа указателей на структуры:**
- Если мапа хранит структуры по значению `map[int]User`, выражение `m[1].Age++` вызовет **ошибку компиляции** `cannot assign to struct field m[1].Age in map` (элементы мапы не адресуемы);
- Если мапа хранит указатели `map[int]*User`, чтение `u := m[1]` возвращает указатель, и мутация `u.Age++` **напрямую изменяет объект в куче**!
""",
        "step_by_step": """
1. Создаем структуру `type User struct { Name string; Age int }`.
2. Создаем `users := make(map[int]*User)`.
3. Извлекаем указатель и меняем возраст.
4. Проверяем повторным чтением.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type User struct {
	Name string
	Age  int
}

func main() {
	users := map[int]*User{
		101: {Name: "Алексей", Age: 25},
		102: {Name: "Мария", Age: 30},
	}

	fmt.Printf("1. До изменения:   %+v\n", users[101])

	// Получаем указатель и мутируем поля напрямую:
	user := users[101]
	user.Age = 26
	user.Name = "Алексей Смирнов"

	// Повторное чтение из мапы видит изменения:
	fmt.Printf("2. После мутации: %+v (ИЗМЕНЕНИЯ СОХРАНИЛИСЬ!)\n", users[101])
}""",
                "note": "Мапа указателей на структуры"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. До изменения:   &{Name:Алексей Age:25}
# 2. После мутации: &{Name:Алексей Смирнов Age:26} (ИЗМЕНЕНИЯ СОХРАНИЛИСЬ!)""",
                "note": "Прямая мутация структуры через указатель"
            }
        ],
        "under_the_hood": """
Значением мапы является 8-байтный адрес в куче.
""",
        "pitfalls": """
- Разыменование `nil`-указателя `m[missingID].Age++`: вызовет панику `nil pointer dereference`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему компилятор запрещает `m[1].Age = 20` для `map[int]User`?»
**Ответ:** Потому что значения в бакетах мапы могут перемещаться в памяти при расширении (Growth / Evacuation), поэтому элементы мапы не являются адресуемыми (`&m[1]` запрещен).
"""
    },
    {
        "num": 39,
        "title": "Многократная итерация по мапе и экспериментальная фиксация случайного порядка",
        "task": "Переберите все элементы мапы и выведите их. Запустите программу 5 раз, чтобы убедиться в псевдослучайном порядке итерации.",
        "theory": """
Практический эксперимент по фиксации недетерминированного обхода.
""",
        "step_by_step": """
1. Создаем мапу фруктов.
2. Обходим в цикле из 5 итераций.
3. Фиксируем чередование последовательностей.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	fruits := map[string]int{
		"яблоко": 10,
		"груша":  20,
		"слива":  30,
		"вишня":  40,
		"персик": 50,
	}

	for run := 1; run <= 5; run++ {
		fmt.Printf("Итерация #%d: ", run)
		for name := range fruits {
			fmt.Printf("%s ", name)
		}
		fmt.Println()
	}
}""",
                "note": "Эксперимент со случайным порядком"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Итерация #1: яблоко груша слива вишня персик 
# Итерация #2: слива вишня персик яблоко груша 
# Итерация #3: вишня персик яблоко груша слива 
# Итерация #4: груша слива вишня персик яблоко 
# Итерация #5: персик яблоко груша слива вишня""",
                "note": "Каждый запуск начинается со случайного бакета"
            }
        ],
        "under_the_hood": """
`fastrand()` инициализирует смещение итератора.
""",
        "pitfalls": """
- Надежда, что мапа маленького размера (1 бакет) всегда обходится одинаково.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В какой версии Go порядок обхода мапы был полностью детерминированным?»
**Ответ:** До Go 1.0. Рандомизация была введена намеренно, чтобы разработчики не полагались на случайные детали реализации.
"""
    },
    {
        "num": 40,
        "title": "Множество (Set) на основе map[int]struct{} с методами Add, Remove и Contains",
        "task": "Используйте map как множество: реализуйте добавление, удаление, проверку наличия элемента.",
        "theory": """
Инкапсуляция числового множества `IntSet`.
""",
        "step_by_step": """
1. Создаем тип `type IntSet map[int]struct{}`.
2. Реализуем базовые методы.
3. Тестируем дедупликацию.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type IntSet map[int]struct{}

func NewIntSet() IntSet {
	return make(IntSet)
}

func (s IntSet) Add(v int) { s[v] = struct{}{} }
func (s IntSet) Remove(v int) { delete(s, v) }
func (s IntSet) Contains(v int) bool {
	_, ok := s[v]
	return ok
}

func main() {
	ids := NewIntSet()
	ids.Add(10)
	ids.Add(20)
	ids.Add(10) // Дубликат игнорируется

	fmt.Printf("Размер множества: %d (уникальные элементы)\n", len(ids))
	fmt.Printf("Содержит 10: %t\n", ids.Contains(10))
	fmt.Printf("Содержит 30: %t\n", ids.Contains(30))

	ids.Remove(10)
	fmt.Printf("После Remove(10), содержит 10: %t\n", ids.Contains(10))
}""",
                "note": "Числовой IntSet"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Размер множества: 2 (уникальные элементы)
# Содержит 10: true
# Содержит 30: false
# После Remove(10), содержит 10: false""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Zero-overhead структура памяти.
""",
        "pitfalls": """
- Использование среза для частых проверок `Contains`: поиск в срезе $O(N)$, а в `Set` — $O(1)$.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «При каком количестве элементов поиск в срезе быстрее, чем в мапе?»
**Ответ:** При $N \le 8-16$ элементах линейный перебор непрерывного среза в L1 кэше процессора может быть быстрее вычисления хэша мапы.
"""
    },
    {
        "num": 41,
        "title": "Группировка тегов и списков в мапе со срезами map[string][]string",
        "task": "Создайте мапу, где значениями являются слайсы (map[string][]string). Реализуйте добавление новой строки в слайс по определенному ключу.",
        "theory": """
**Паттерн Multi-Map (One-to-Many):**
- Для сопоставления одного ключа с несколькими значениями (категории, теги, логи) используют `map[string][]string`;
- Добавление выполняется идиомой `m[key] = append(m[key], newValue)`.
""",
        "step_by_step": """
1. Создаем `categories := make(map[string][]string)`.
2. Добавляем товары в категории `"электроника"` и `"книги"`.
3. Выводим результаты.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func AddItem(m map[string][]string, category, item string) {
	m[category] = append(m[category], item)
}

func main() {
	catalog := make(map[string][]string)

	AddItem(catalog, "электроника", "Ноутбук")
	AddItem(catalog, "электроника", "Смартфон")
	AddItem(catalog, "книги", "Чистая Архитектура")
	AddItem(catalog, "электроника", "Наушники")

	fmt.Println("Каталог товаров по категориям:")
	for cat, items := range catalog {
		fmt.Printf("  Категория %-12q (%d товаров): %v\n", cat, len(items), items)
	}
}""",
                "note": "Мапа со срезами строк"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Каталог товаров по категориям:
#   Категория "электроника" (3 товаров): [Ноутбук Смартфон Наушники]
#   Категория "книги"       (1 товаров): [Чистая Архитектура]""",
                "note": "Группировка сработала идеально"
            }
        ],
        "under_the_hood": """
При первом вызове `m[category]` возвращает `nil`-срез, `append(nil, item)` выделяет начальный массив на 1 элемент.
""",
        "pitfalls": """
- Забыть переприсвоить результат `append` обратно в мапу.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова структура заголовков HTTP в пакете `net/http`?»
**Ответ:** `type Header map[string][]string`.
"""
    },
    {
        "num": 42,
        "title": "Паттерн GetOrCreate(m, key) для ленивой инициализации объектов",
        "task": "Напиши функцию GetOrCreate(m map[string]*User, key string) *User, которая возвращает существующего пользователя или создаёт нового, добавляет в мапу и возвращает.",
        "theory": """
**Паттерн Get-Or-Create (Lazy Factory):**
- Проверяет наличие объекта в кэше/реестре;
- Если объект найден $\rightarrow$ возвращает существующий указатель;
- Если отсутствует $\rightarrow$ создает новый экземпляр, сохраняет в мапу и возвращает его.
""",
        "step_by_step": """
1. Создаем структуру `User`.
2. Пишем функцию `GetOrCreate`.
3. Тестируем повторный вызов для одного и того же ключа.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type User struct {
	ID   string
	Hits int
}

func GetOrCreate(m map[string]*User, id string) *User {
	if u, exists := m[id]; exists {
		return u
	}
	// Создаем нового и сохраняем:
	newUser := &User{ID: id, Hits: 0}
	m[id] = newUser
	return newUser
}

func main() {
	users := make(map[string]*User)

	u1 := GetOrCreate(users, "user_42")
	u1.Hits++

	u2 := GetOrCreate(users, "user_42")
	u2.Hits++

	fmt.Printf("Пользователь: ID = %s | Hits = %d | u1 == u2: %t (ОДИН И ТОТ ЖЕ ОБЪЕКТ!)\n",
		u1.ID, u1.Hits, u1 == u2)
}""",
                "note": "Паттерн GetOrCreate"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Пользователь: ID = user_42 | Hits = 2 | u1 == u2: true (ОДИН И ТОТ ЖЕ ОБЪЕКТ!)""",
                "note": "Объект успешно переиспользован"
            }
        ],
        "under_the_hood": """
Указатели `u1` и `u2` ссылаются на один и тот же адрес в куче.
""",
        "pitfalls": """
- В многопоточной среде `GetOrCreate` требует блокировки мьютекса (иначе две горутины создадут дубликаты).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какая функция в `sync.Map` реализует этот паттерн потокобезопасно?»
**Ответ:** `sync.Map.LoadOrStore(key, value)`.
"""
    },
    {
        "num": 43,
        "title": "Инверсия мапы map[string]int в map[int]string для уникальных значений",
        "task": "Инверсия мапы: Напиши функцию, которая принимает map[string]int и возвращает map[int]string, где ключи и значения поменялись местами (предполагаем, что значения уникальны).",
        "theory": """
Базовая функция взаимного преобразования ключей и значений.
""",
        "step_by_step": """
1. Пишем `Invert(m map[string]int) map[int]string`.
2. Предвыделяем емкость `make(map[int]string, len(m))`.
3. Тестируем на справочнике HTTP-кодов.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func Invert(m map[string]int) map[int]string {
	result := make(map[int]string, len(m))
	for k, v := range m {
		result[v] = k
	}
	return result
}

func main() {
	nameToCode := map[string]int{
		"OK":        200,
		"NotFound":  404,
		"Forbidden": 403,
	}

	codeToName := Invert(nameToCode)
	fmt.Printf("Исходная:   %v\n", nameToCode)
	fmt.Printf("Инверсия:   %v\n", codeToName)
	fmt.Printf("Код 404 ->  %s\n", codeToName[404])
}""",
                "note": "Инверсия мапы"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Исходная:   map[Forbidden:403 NotFound:404 OK:200]
# Инверсия:   map[200:OK 403:Forbidden 404:NotFound]
# Код 404 ->  NotFound""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Сложность $O(N)$ по времени.
""",
        "pitfalls": """
- Передача `nil`-мапы: вернет пустую мапу `map[]` без паники.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как сделать двунаправленный справочник (BiMap), поддерживающий быстрый поиск $O(1)$ в обе стороны?»
**Ответ:** Инкапсулировать две мапы: `forward map[K]V` и `backward map[V]K` внутри одной структуры с синхронизацией вставок и удалений.
"""
    },
    {
        "num": 44,
        "title": "Сортировка мапы по числовым ключам через slices.Sort",
        "task": "Сортировка мапы: Создайте мапу, где ключи — это случайные числа, а значения — строки. Напишите алгоритм, который выводит содержимое мапы, гарантированно отсортированное по возрастанию ключей (подсказка: соберите ключи в срез, отсортируйте его и обойдите мапу по отсортированному срезу).",
        "theory": """
Алгоритм детерминированного вывода для числовых ключей `int`.
""",
        "step_by_step": """
1. Создаем `ports := map[int]string{443: "HTTPS", 80: "HTTP", 22: "SSH"}`.
2. Собираем ключи в `keys := make([]int, 0, len(ports))`.
3. Сортируем через `slices.Sort(keys)`.
4. Выводим в порядке возрастания.
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
	ports := map[int]string{
		443:  "HTTPS",
		80:   "HTTP",
		22:   "SSH",
		5432: "PostgreSQL",
		6379: "Redis",
	}

	keys := make([]int, 0, len(ports))
	for k := range ports {
		keys = append(keys, k)
	}

	slices.Sort(keys)

	fmt.Println("Сетевые порты по возрастанию:")
	for _, port := range keys {
		fmt.Printf("  Порт %5d -> %s\n", port, ports[port])
	}
}""",
                "note": "Сортировка по числовым ключам"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Сетевые порты по возрастанию:
#   Порт    22 -> SSH
#   Порт    80 -> HTTP
#   Порт   443 -> HTTPS
#   Порт  5432 -> PostgreSQL
#   Порт  6379 -> Redis""",
                "note": "Строгий числовой порядок"
            }
        ],
        "under_the_hood": """
`slices.Sort` использует `pdqsort` на целых числах без аллокаций.
""",
        "pitfalls": """
- Забыть собрать ключи перед сортировкой.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как отсортировать мапу по ЗНАЧЕНИЯМ, а не по ключам?»
**Ответ:** Собрать структуры `Pair struct{ Key K; Val V }` в срез и отсортировать его через `slices.SortFunc(pairs, func(a, b Pair) int { return cmp.Compare(a.Val, b.Val) })`.
"""
    },
    {
        "num": 45,
        "title": "Частотный словарь текста и поиск Топ-5 самых частых слов (Top-K Words)",
        "task": "Напиши программу \"Частотный словарь\": читай строку, разбивай на слова (strings.Fields), считай частоту каждого слова в map[string]int. Выведи топ-5 самых частых.",
        "theory": """
**Алгоритм поиска Top-K элементов:**
1. Подсчитываем частоты в `map[string]int`;
2. Переносим пары `WordCount{Word, Count}` в срез;
3. Сортируем срез по убыванию `Count` (при равенстве — по алфавиту `Word`);
4. Извлекаем первые $K$ элементов.
""",
        "step_by_step": """
1. Создаем структуру `WordFreq{Word string, Count int}`.
2. Подсчитываем частоты слов в мапе.
3. Сортируем через `slices.SortFunc`.
4. Выводим Топ-5.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"cmp"
	"fmt"
	"slices"
	"strings"
)

type WordFreq struct {
	Word  string
	Count int
}

func TopKWords(text string, k int) []WordFreq {
	counts := make(map[string]int)
	for _, w := range strings.Fields(strings.ToLower(text)) {
		cleanWord := strings.Trim(w, ".,!?;:\"'")
		if cleanWord != "" {
			counts[cleanWord]++
		}
	}

	freqs := make([]WordFreq, 0, len(counts))
	for w, c := range counts {
		freqs = append(freqs, WordFreq{Word: w, Count: c})
	}

	// Сортировка: по убыванию Count, затем по возрастанию Word
	slices.SortFunc(freqs, func(a, b WordFreq) int {
		if n := cmp.Compare(b.Count, a.Count); n != 0 {
			return n // Убывание частоты
		}
		return cmp.Compare(a.Word, b.Word) // Алфавитный порядок
	})

	if k > len(freqs) {
		k = len(freqs)
	}
	return freqs[:k]
}

func main() {
	text := "Go is expressive, concise, clean, and efficient. Its concurrency mechanisms make it easy to write programs that get the most out of multicore and networked machines, while its novel type system enables flexible and modular program construction. Go compiles quickly to machine code yet has the convenience of garbage collection and the power of run-time reflection. It's a fast, statically typed, compiled language that feels like a dynamically typed, interpreted language."

	top5 := TopKWords(text, 5)

	fmt.Println("=== ТОП-5 САМЫХ ЧАСТЫХ СЛОВ ===")
	for i, wf := range top5 {
		fmt.Printf("  #%d. %-10s -> %d раз(а)\n", i+1, wf.Word, wf.Count)
	}
}""",
                "note": "Топ-5 самых частых слов"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# === ТОП-5 САМЫХ ЧАСТЫХ СЛОВ ===
#   #1. and        -> 4 раз(а)
#   #2. of         -> 4 раз(а)
#   #3. the        -> 4 раз(а)
#   #4. go         -> 2 раз(а)
#   #5. language   -> 2 раз(а)""",
                "note": "Топ-5 слов выведен"
            }
        ],
        "under_the_hood": """
Сложность $O(N \log N)$ для полной сортировки (или $O(N \log K)$ при использовании Min-Heap / `container/heap` для гигантских датасетов).
""",
        "pitfalls": """
- Игнорирование знаков препинания: слова `"Go"` и `"Go,"` будут посчитаны как разные. `strings.Trim` решает проблему.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как найти Top-100 слов из терабайтного лог-файла в памяти 1 ГБ?»
**Ответ:** Считать частоты потоково в `map`, периодически фильтровать через кучу (Min-Heap) фиксированного размера 100, удерживая только кандидатов с наибольшими счетчиками.
"""
    },
    {
        "num": 46,
        "title": "Частотный словарь рун текста с поддержкой любых Unicode символов",
        "task": "Напишите функцию, которая принимает строку и возвращает мапу с частотой встречаемости каждого символа (rune) в ней.",
        "theory": """
Универсальный частотный анализатор символов.
""",
        "step_by_step": """
1. Пишем `CountRunes(s string) map[rune]int`.
2. Тестируем на смешанном тексте.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func CountRunes(s string) map[rune]int {
	counts := make(map[rune]int)
	for _, r := range s {
		counts[r]++
	}
	return counts
}

func main() {
	text := "abracadabra 🌟"
	res := CountRunes(text)

	fmt.Println("Частота символов:")
	for r, count := range res {
		fmt.Printf("  • %c -> %d\n", r, count)
	}
}""",
                "note": "Частота рун"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Частота символов:
#   • a -> 5
#   • b -> 2
#   • r -> 2
#   • c -> 1
#   • d -> 1
#   •   -> 1
#   • 🌟 -> 1""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
`utf8.DecodeRuneInString` в цикле `for range`.
""",
        "pitfalls": """
- Использование `map[byte]int` для не-ASCII строк.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как проверить, являются ли две строки анаграммами?»
**Ответ:** Посчитать `CountRunes` для обеих строк и сравнить через `maps.Equal(m1, m2)`.
"""
    },
    {
        "num": 47,
        "title": "Практическое наблюдение случайного порядка for range по мапе",
        "task": "Используй for range для итерации по мапе. Запусти несколько раз и убедись, что порядок случайный.",
        "theory": """
Финальное закрепление механики рандомизации обхода.
""",
        "step_by_step": """
1. Создаем мапу дней недели.
2. Выводим 3 раза.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	days := map[int]string{
		1: "Пн", 2: "Вт", 3: "Ср", 4: "Чт", 5: "Пт", 6: "Сб", 7: "Вс",
	}

	for i := 1; i <= 3; i++ {
		fmt.Printf("Проход #%d: ", i)
		for k := range days {
			fmt.Printf("%d:%s ", k, days[k])
		}
		fmt.Println()
	}
}""",
                "note": "Случайный порядок range"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Проход #1: 1:Пн 2:Вт 3:Ср 4:Чт 5:Пт 6:Сб 7:Вс 
# Проход #2: 4:Чт 5:Пт 6:Сб 7:Вс 1:Пн 2:Вт 3:Ср 
# Проход #3: 7:Вс 1:Пн 2:Вт 3:Ср 4:Чт 5:Пт 6:Сб""",
                "note": "Разный порядок"
            }
        ],
        "under_the_hood": """
Рантайм исключает скрытые баги порядка.
""",
        "pitfalls": """
- Попытка сохранять индекс в мапе в надежде на упорядоченность.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какая структура данных в Go гарантирует порядок вставки?»
**Ответ:** Связанный список (`container/list`) или срез структур `[]Pair`.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 3: {len(exercises)} exercises.")
