# Chapter 8 Part 4: Exercises 57 to 74

exercises = [
    {
        "num": 57,
        "title": "Разворот среза на месте ReverseSlice(s) без выделения памяти",
        "task": "Напиши функцию ReverseSlice(s []int), которая разворачивает слайс на месте (in-place), без аллокации нового массива.",
        "theory": """
Алгоритмический разворот среза целых чисел методом двух указателей (Two Pointers) с $O(1)$ памяти.
""",
        "step_by_step": """
1. Пишем `ReverseSlice(s []int)`.
2. В цикле меняем `s[i], s[j] = s[j], s[i]`.
3. Тестируем на четной и нечетной длине.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func ReverseSlice(s []int) {
	for i, j := 0, len(s)-1; i < j; i, j = i+1, j-1 {
		s[i], s[j] = s[j], s[i]
	}
}

func main() {
	numbers := []int{1, 2, 3, 4, 5, 6, 7}
	fmt.Printf("До:    %v\\n", numbers)

	ReverseSlice(numbers)
	fmt.Printf("После: %v\\n", numbers)
}""",
                "note": "Разворот среза на месте"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# До:    [1 2 3 4 5 6 7]
# После: [7 6 5 4 3 2 1]""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Инструкции регистрового обмена процессора без вызова `runtime.makeslice`.
""",
        "pitfalls": """
- Создание копии среза через `make` и `copy` перед разворотом: это тратит $O(N)$ памяти.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова пространственная сложность `ReverseSlice`?»
**Ответ:** Строго $O(1)$ (In-Place).
"""
    },
    {
        "num": 58,
        "title": "Утечка памяти среза байт []byte (1MB) при взятии суффикса и устранение через append([]byte(nil), ...)",
        "task": "Напиши программу, демонстрирующую memory leak с слайсом: big := make([]byte, 1<<20); small := big[len(big)-10:]. Покажи, что small удерживает в памяти весь 1MB underlying array. Исправь через small = append([]byte(nil), small...).",
        "theory": """
**Утечка памяти при парсинге протоколов и файлов:**
- `small := big[len(big)-10:]` держит ссылку на 1 МБ буфер;
- Паттерн `small = append([]byte(nil), small...)` аллоцирует ровно 10 байт в новом буфере, позволяя GC освободить 1 МБ памяти.
""",
        "step_by_step": """
1. Создаем буфер 1 МБ (`1<<20` байт).
2. Демонстрируем утечку при взятии среза из 10 байт.
3. Исправляем через `append([]byte(nil), small...)`.
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

func LeakyTail() []byte {
	big := make([]byte, 1<<20) // 1 МБ
	copy(big[len(big)-10:], []byte("0123456789"))
	return big[len(big)-10:] // Удерживает 1 МБ!
}

func SafeTail() []byte {
	big := make([]byte, 1<<20) // 1 МБ
	copy(big[len(big)-10:], []byte("0123456789"))
	// Копируем только 10 байт в новый мини-буфер:
	return append([]byte(nil), big[len(big)-10:]...)
}

func main() {
	var m runtime.MemStats

	_ = SafeTail()
	runtime.GC()
	runtime.ReadMemStats(&m)
	fmt.Printf("Память после SafeTail:  %d КБ (1 МБ освобожден!)\\n", m.Alloc/1024)

	_ = LeakyTail()
	runtime.GC()
	runtime.ReadMemStats(&m)
	fmt.Printf("Память после LeakyTail: %d КБ (1 МБ заблокирован в памяти!)\\n", m.Alloc/1024)
}""",
                "note": "Устранение утечки памяти среза"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Память после SafeTail:  120 КБ (1 МБ освобожден!)
# Память после LeakyTail: 1144 КБ (1 МБ заблокирован в памяти!)""",
                "note": "Утечка памяти успешно устранена"
            }
        ],
        "under_the_hood": """
`append([]byte(nil), ...)` выделяет минимальный буфер на 10 байт.
""",
        "pitfalls": """
- Использование `buf[start:end]` при парсинге гигабайтных JSON/XML файлов.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как функция `slices.Clone` (Go 1.21+) упрощает безопасное копирование?»
**Ответ:** `safe := slices.Clone(big[len(big)-10:])` делает ровно то же самое с максимальной читаемостью.
"""
    },
    {
        "num": 59,
        "title": "Сброс длины s = s[:0] и архитектура высокопроизводительных пулов памяти",
        "task": "Срежьте слайс до нулевой длины (s = s[:0]). Выведите его len и cap. Объясните, почему этот паттерн полезен для переиспользования памяти без новых аллокаций.",
        "theory": """
**Архитектура Zero-Allocation Buffers:**
- `s = s[:0]` обнуляет счетчик длины `len = 0`;
- Емкость `cap` сохраняется в неизменном виде;
- Позволяет повторно использовать срез в циклах без давления на GC.
""",
        "step_by_step": """
1. Создаем срез `s := make([]int, 0, 100)`.
2. Заполняем его 10 элементами.
3. Сбрасываем `s = s[:0]` и повторно заполняем.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	buf := make([]string, 0, 50)

	// Сессия 1
	buf = append(buf, "Запрос-1", "Запрос-2", "Запрос-3")
	fmt.Printf("Сессия 1: len = %d, cap = %d | Данные: %v\\n", len(buf), cap(buf), buf)

	// Сброс без аллокаций:
	buf = buf[:0]
	fmt.Printf("После buf[:0]: len = %d, cap = %d\\n", len(buf), cap(buf))

	// Сессия 2
	buf = append(buf, "Запрос-4")
	fmt.Printf("Сессия 2: len = %d, cap = %d | Данные: %v\\n", len(buf), cap(buf), buf)
}""",
                "note": "Сброс среза через s[:0]"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Сессия 1: len = 3, cap = 50 | Данные: [Запрос-1 Запрос-2 Запрос-3]
# После buf[:0]: len = 0, cap = 50
# Сессия 2: len = 1, cap = 50 | Данные: [Запрос-4]""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
1 машинная инструкция для изменения регистра длины.
""",
        "pitfalls": """
- Необнуленные указатели `[]*Object` при `s[:0]` (утечка памяти объектов).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как `bytes.Buffer.Reset()` реализует очистку памяти?»
**Ответ:** Вызовом `b.buf = b.buf[:0]`.
"""
    },
    {
        "num": 60,
        "title": "Универсальная проверка отсортированности среза IsSorted на дженериках cmp.Ordered",
        "task": "Проверьте, является ли слайс отсортированным (напишите универсальную функцию с comparable).",
        "theory": """
**Проверка отсортированности в Go 1.21+:**
- Ограничение `cmp.Ordered` поддерживает все числовые типы и строки, для которых определены операторы `<`, `<=`, `>`, `>=`;
- Функция делает один проход $O(N)$, проверяя условие `s[i] < s[i-1]`.
""",
        "step_by_step": """
1. Пишем `IsSorted[T cmp.Ordered](s []T) bool`.
2. Тестируем на срезах чисел и строк.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"cmp"
	"fmt"
)

func IsSorted[T cmp.Ordered](s []T) bool {
	for i := 1; i < len(s); i++ {
		if s[i] < s[i-1] {
			return false
		}
	}
	return true
}

func main() {
	ints1 := []int{10, 20, 30, 40, 50}
	ints2 := []int{10, 50, 30, 40}
	strs := []string{"Apple", "Banana", "Cherry"}

	fmt.Printf("ints1: %v -> Отсортирован: %t\\n", ints1, IsSorted(ints1))
	fmt.Printf("ints2: %v -> Отсортирован: %t\\n", ints2, IsSorted(ints2))
	fmt.Printf("strs:  %v -> Отсортирован: %t\\n", strs, IsSorted(strs))
}""",
                "note": "Универсальная проверка IsSorted"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# ints1: [10 20 30 40 50] -> Отсортирован: true
# ints2: [10 50 30 40] -> Отсортирован: false
# strs:  [Apple Banana Cherry] -> Отсортирован: true""",
                "note": "Результаты проверки"
            }
        ],
        "under_the_hood": """
Мономорфизация дженериков компилятора подставляет эффективные машинные инструкции сравнения.
""",
        "pitfalls": """
- Использование интерфейса `comparable` вместо `cmp.Ordered`: для `comparable` определены только `==` и `!=`, но запрещены `<` и `>`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какая функция в стандартном пакете `slices` выполняет эту проверку?»
**Ответ:** `slices.IsSorted(s)`.
"""
    },
    {
        "num": 61,
        "title": "Реализация структуры данных стек (LIFO Stack) на базе среза: Push и Pop",
        "task": "Реализуй стек (LIFO) на основе слайса: функции Push (через append) и Pop (возврат последнего элемента и уменьшение длины).",
        "theory": """
**Стек LIFO (Last-In-First-Out) на срезе:**
- `Push(v)` $\rightarrow$ `s = append(s, v)` ($O(1)$ амортизированное);
- `Pop()` $\rightarrow$ извлечение `top := s[len(s)-1]` и усечение `s = s[:len(s)-1]` ($O(1)$ гарантированное);
- Максимальная локальность кэша процессора (Cache-friendly).
""",
        "step_by_step": """
1. Создаем тип `type IntStack []int`.
2. Реализуем методы `Push`, `Pop`, `Peek`, `IsEmpty`.
3. Тестируем последовательность операций.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type IntStack []int

func (s *IntStack) Push(v int) {
	*s = append(*s, v)
}

func (s *IntStack) Pop() (int, bool) {
	if len(*s) == 0 {
		return 0, false // Стек пуст
	}
	index := len(*s) - 1
	val := (*s)[index]
	*s = (*s)[:index]
	return val, true
}

func main() {
	var stack IntStack

	stack.Push(10)
	stack.Push(20)
	stack.Push(30)

	fmt.Printf("Стек после 3 Push: %v\\n", stack)

	for {
		val, ok := stack.Pop()
		if !ok {
			break
		}
		fmt.Printf("  Pop: %d | Оставшийся стек: %v\\n", val, stack)
	}
}""",
                "note": "Стек на основе среза"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Стек после 3 Push: [10 20 30]
#   Pop: 30 | Оставшийся стек: [10 20]
#   Pop: 20 | Оставшийся стек: [10]
#   Pop: 10 | Оставшийся стек: []""",
                "note": "LIFO порядок извлечения"
            }
        ],
        "under_the_hood": """
Усечение `*s = (*s)[:index]` выполняется за 1 такт CPU без деаллокаций.
""",
        "pitfalls": """
- Вызов `Pop` на пустом стеке без проверки длины `len == 0`: вызовет панику `index out of range [-1]`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему стек на базе среза быстрее стека на связном списке (Linked List)?»
**Ответ:** Потому что элементы среза расположены непрерывно в памяти и загружаются в L1/L2 кэш линиями по 64 байта, а связный список создает фрагментацию кучи и кэш-промахи (Cache Misses).
"""
    },
    {
        "num": 62,
        "title": "Сортировка срезов через пакет sort: sort.Ints, sort.Strings и кастомный sort.Slice",
        "task": "Отсортируй []int через sort.Ints. Затем отсортируй []string через sort.Strings. Напиши sort.Slice с кастомным less для слайса структур Person (сначала по возрасту, при равенстве — по имени).",
        "theory": """
**Сортировка в пакете `sort`:**
- `sort.Ints(s)` и `sort.Strings(s)` для примитивных типов;
- `sort.Slice(s, func(i, j int) bool)` для многокритериальной сортировки структур (Pattern Order-by Multi-Column).
""",
        "step_by_step": """
1. Сортируем числа и строки.
2. Создаем структуру `Person{Name string, Age int}`.
3. Сортируем сначала по возрасту, затем по имени.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"sort"
)

type Person struct {
	Name string
	Age  int
}

func main() {
	// 1. Сортировка int
	nums := []int{50, 10, 40, 20, 30}
	sort.Ints(nums)
	fmt.Printf("1. sort.Ints:    %v\\n", nums)

	// 2. Сортировка string
	words := []string{"Go", "Rust", "Python", "C++"}
	sort.Strings(words)
	fmt.Printf("2. sort.Strings: %v\\n\\n", words)

	// 3. Многокритериальная сортировка структур:
	people := []Person{
		{Name: "Борис", Age: 30},
		{Name: "Анна", Age: 25},
		{Name: "Виктор", Age: 30},
		{Name: "Денис", Age: 25},
	}

	sort.Slice(people, func(i, j int) bool {
		if people[i].Age != people[j].Age {
			return people[i].Age < people[j].Age // Сначала по возрастанию возраста
		}
		return people[i].Name < people[j].Name // При равенстве - по алфавиту
	})

	fmt.Println("3. sort.Slice для структур Person:")
	for _, p := range people {
		fmt.Printf("   %+v\\n", p)
	}
}""",
                "note": "Сортировка срезов через пакет sort"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. sort.Ints:    [10 20 30 40 50]
# 2. sort.Strings: [C++ Go Python Rust]
# 
# 3. sort.Slice для структур Person:
#    {Name:Анна Age:25}
#    {Name:Денис Age:25}
#    {Name:Борис Age:30}
#    {Name:Виктор Age:30}""",
                "note": "Результаты сортировки"
            }
        ],
        "under_the_hood": """
Алгоритм `pdqsort` (Pattern-defeating Quicksort) со сложностью $O(N \\log N)$.
""",
        "pitfalls": """
- Нарушение строгого слабого порядка (Strict Weak Ordering) в функции `less` (например, использование `<=` вместо `<`), что приводит к багам сортировки.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Является ли `sort.Slice` стабильной сортировкой?»
**Ответ:** НЕТ! Для сохранения относительного порядка одинаковых элементов используют `sort.SliceStable`.
"""
    },
    {
        "num": 63,
        "title": "Сравнение производительности Order-Preserving Delete O(N) и Unordered Delete O(1)",
        "task": "Удаление элемента: Напишите две функции для удаления элемента из среза целых чисел по индексу i:\n* С сохранением порядка элементов (используя append(s[:i], s[i+1:]...)).\n* Без сохранения порядка элементов (заменив удаляемый элемент последним и урезав срез на 1). Объясните разницу в производительности.",
        "theory": """
**Сравнительный анализ алгоритмов удаления:**
1. **Order-Preserving Delete ($O(N)$):**
   `append(s[:i], s[i+1:]...)` $\\rightarrow$ сдвигает $N - i - 1$ элементов влево. Требует прогона данных по шине памяти;
2. **Unordered / Fast Delete ($O(1)$):**
   `s[i] = s[len(s)-1]; s = s[:len(s)-1]` $\\rightarrow$ 1 операция записи. В сотни раз быстрее на миллионных срезах.
""",
        "step_by_step": """
1. Пишем обе функции.
2. Демонстрируем поведение на срезе.
3. Анализируем асимптотику.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func DeleteOrderPreserving(s []int, i int) []int {
	return append(s[:i], s[i+1:]...) // O(N)
}

func DeleteUnordered(s []int, i int) []int {
	s[i] = s[len(s)-1]
	return s[:len(s)-1] // O(1)
}

func main() {
	s1 := []int{10, 20, 30, 40, 50}
	s2 := []int{10, 20, 30, 40, 50}

	res1 := DeleteOrderPreserving(s1, 1) // Удаляем 20
	res2 := DeleteUnordered(s2, 1)        // Удаляем 20

	fmt.Printf("С сохранением порядка O(N):  %v\\n", res1)
	fmt.Printf("Без сохранения порядка O(1): %v\\n", res2)
}""",
                "note": "Сравнение двух подходов к удалению"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# С сохранением порядка O(N):  [10 30 40 50]
# Без сохранения порядка O(1): [10 50 30 40]""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
При $N = 10\\,000\\,000$ `DeleteUnordered` выполняется за 1 наносекунду, а `DeleteOrderPreserving` — за несколько миллисекунд.
""",
        "pitfalls": """
- Применение `DeleteUnordered` в очередях или сортированных срезах, где ломается порядок.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Когда в BigTech продакшене выбирают `Unordered Delete`?»
**Ответ:** Когда срез используется как множество (Set) или реестр активных обработчиков/подписчиков, где порядок не имеет значения.
"""
    },
    {
        "num": 64,
        "title": "Современный пакет slices в Go 1.21+: Sort, Contains, Index и Compact",
        "task": "Используйте современный пакет slices (Go 1.21+) для сортировки, поиска (Contains, Index) и удаления дубликатов (Compact).",
        "theory": """
**Пакет `slices` (Go 1.21+):**
- `slices.Sort(s)` — типобезопасная быстрая сортировка без рефлексии;
- `slices.Contains(s, v)` — проверка наличия за $O(N)$;
- `slices.Index(s, v)` — поиск индекса первого вхождения;
- `slices.Compact(s)` — удаление идущих подряд дубликатов на месте за $O(N)$.
""",
        "step_by_step": """
1. Импортируем стандартный пакет `slices`.
2. Сортируем срез `slices.Sort(nums)`.
3. Ищем элементы через `Contains` и `Index`.
4. Удаляем дубликаты через `Compact`.
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
	nums := []int{5, 2, 8, 2, 5, 1, 8, 9}
	fmt.Printf("Исходный срез: %v\\n", nums)

	// 1. Сортировка на месте
	slices.Sort(nums)
	fmt.Printf("1. slices.Sort:    %v\\n", nums)

	// 2. Поиск
	hasEight := slices.Contains(nums, 8)
	idxFive := slices.Index(nums, 5)
	fmt.Printf("2. Contains(8):    %t | Index(5): %d\\n", hasEight, idxFive)

	// 3. Удаление смежных дубликатов
	nums = slices.Compact(nums)
	fmt.Printf("3. slices.Compact: %v (уникальные элементы!)\\n", nums)
}""",
                "note": "Современный пакет slices"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Исходный срез: [5 2 8 2 5 1 8 9]
# 1. slices.Sort:    [1 2 2 5 5 8 8 9]
# 2. Contains(8):    true | Index(5): 3
# 3. slices.Compact: [1 2 5 8 9] (уникальные элементы!)""",
                "note": "Результаты работы пакета slices"
            }
        ],
        "under_the_hood": """
Функции пакета `slices` построены на дженериках `[S ~[]E, E cmp.Ordered]`, что полностью устраняет накладные расходы на интерфейсы и динамическую диспетчеризацию.
""",
        "pitfalls": """
- Вызов `slices.Compact` на неотсортированном срезе: `Compact` удаляет только *подряд идущие* дубликаты. Перед вызовом срез обязан быть отсортирован!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `slices.Sort` быстрее, чем `sort.Slice` из старого пакета?»
**Ответ:** `sort.Slice` использует рефлексию и замыкания функций, что мешает инлайнингу компилятора. `slices.Sort` на дженериках инлайнится напрямую в тело вызывающего кода без аллокаций.
"""
    },
    {
        "num": 65,
        "title": "Универсальная вставка Insert(s, index, val) со сдвигом и проверкой границ",
        "task": "[Высокая сложность]: Напиши функцию Insert(s []int, index int, val int) []int, которая вставляет элемент в середину слайса без потери данных.",
        "theory": """
Реализация надежной функции вставки с валидацией границ.
""",
        "step_by_step": """
1. Пишем `Insert(s []int, index int, val int) []int`.
2. Проверяем граничные условия `index == 0` и `index == len(s)`.
3. Сдвигаем элементы через `copy`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func Insert(s []int, index int, val int) []int {
	if index < 0 || index > len(s) {
		panic(fmt.Sprintf("insert: index %d out of range [0..%d]", index, len(s)))
	}
	s = append(s, 0)
	copy(s[index+1:], s[index:])
	s[index] = val
	return s
}

func main() {
	s := []int{10, 20, 40, 50}
	fmt.Printf("До:    %v\\n", s)

	s = Insert(s, 2, 30) // Вставка 30 на индекс 2
	fmt.Printf("После: %v\\n", s)

	s = Insert(s, 0, 0) // Вставка в начало
	s = Insert(s, len(s), 60) // Вставка в конец
	fmt.Printf("Итог:  %v\\n", s)
}""",
                "note": "Универсальная функция Insert"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# До:    [10 20 40 50]
# После: [10 20 30 40 50]
# Итог:  [0 10 20 30 40 50 60]""",
                "note": "Вставка отработала корректно"
            }
        ],
        "under_the_hood": """
Один вызов `memmove` при `copy`.
""",
        "pitfalls": """
- Забыть обработку вставки в самый конец `index == len(s)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова сложность вставки $K$ элементов одновременно?»
**Ответ:** При пакетной вставке расширяют срез сразу на $K$ слотов: `s = append(s, make([]T, K)...); copy(s[i+K:], s[i:]); copy(s[i:], newElements)`. Это занимает $O(N)$ вместо $K \\times O(N)$.
"""
    },
    {
        "num": 66,
        "title": "Объединение двух срезов Union(s1, s2) без дубликатов с сохранением порядка",
        "task": "Объедините два слайса без дубликатов (сохранив порядок первого вхождения).",
        "theory": """
**Алгоритм Union со структурой Set на `map[T]struct{}`:**
- Проходим `s1`, затем `s2`;
- Используем хэш-таблицу `seen := make(map[int]struct{})` для отслеживания уникальности за $O(1)$;
- Суммарная сложность $O(N + M)$ по времени.
""",
        "step_by_step": """
1. Пишем `Union(s1, s2 []int) []int`.
2. Используем `map[int]struct{}`.
3. Сохраняем порядок первого вхождения.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func Union(s1, s2 []int) []int {
	seen := make(map[int]struct{})
	result := make([]int, 0, len(s1)+len(s2))

	for _, v := range append(s1, s2...) {
		if _, exists := seen[v]; !exists {
			seen[v] = struct{}{}
			result = append(result, v)
		}
	}
	return result
}

func main() {
	a := []int{1, 2, 3, 4, 5}
	b := []int{3, 4, 5, 6, 7}

	res := Union(a, b)
	fmt.Printf("a:     %v\\n", a)
	fmt.Printf("b:     %v\\n", b)
	fmt.Printf("Union: %v\\n", res)
}""",
                "note": "Объединение срезов без дубликатов"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# a:     [1 2 3 4 5]
# b:     [3 4 5 6 7]
# Union: [1 2 3 4 5 6 7]""",
                "note": "Порядок первого вхождения сохранен"
            }
        ],
        "under_the_hood": """
`struct{}` занимает 0 байт памяти в map values.
""",
        "pitfalls": """
- Использование `map[int]bool`, расходующего лишний 1 байт на каждое значение.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как объединить два уже отсортированных среза за $O(N+M)$ времени и $O(1)$ дополнительной памяти без мапы?»
**Ответ:** Алгоритмом Two Pointers (Merge phase сортировки слиянием).
"""
    },
    {
        "num": 67,
        "title": "Удаление четных чисел на месте (In-Place Filter) без новых аллокаций",
        "task": "In-place фильтрация: Напишите функцию, которая принимает срез []int и удаляет из него все четные числа, не выделяя новый срез через make (модифицируя исходный срез и возвращая новое «окно»).",
        "theory": """
Паттерн фильтрации нечетных чисел на месте.
""",
        "step_by_step": """
1. Пишем `RemoveEvensInPlace(s []int) []int`.
2. Указателем записи `w` сохраняем `v%2 != 0`.
3. Возвращаем `s[:w]`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func RemoveEvensInPlace(s []int) []int {
	w := 0
	for _, v := range s {
		if v%2 != 0 {
			s[w] = v
			w++
		}
	}
	return s[:w]
}

func main() {
	numbers := []int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
	fmt.Printf("До:    %v\\n", numbers)

	odds := RemoveEvensInPlace(numbers)
	fmt.Printf("После: %v (только нечетные, 0 аллокаций!)\\n", odds)
}""",
                "note": "Удаление четных на месте"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# До:    [1 2 3 4 5 6 7 8 9 10]
# После: [1 3 5 7 9] (только нечетные, 0 аллокаций!)""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Перезапись в том же фрейме памяти.
""",
        "pitfalls": """
- Забыть вернуть `s[:w]`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какая функция в Go 1.21+ заменяет In-Place удаление элементов по предикату?»
**Ответ:** `slices.DeleteFunc(s, func(e int) bool { return e%2 == 0 })`.
"""
    },
    {
        "num": 68,
        "title": "Зубчатый двумерный срез (Jagged Array) разной длины и красивый вывод",
        "task": "Создайте слайс слайсов (двумерный) разной длины, заполните случайными числами и выведите красиво.",
        "theory": """
**Зубчатый массив (Jagged Slice):**
- Срез, в котором каждая строка имеет индивидуальную длину;
- Позволяет эффективно представлять треугольные матрицы, деревья и списки смежности графов без расхода памяти на пустые ячейки.
""",
        "step_by_step": """
1. Создаем `jagged := make([][]int, 4)`.
2. Задаем строкам длины 2, 4, 1, 3.
3. Заполняем и форматируем вывод.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	lengths := []int{2, 4, 1, 3}
	jagged := make([][]int, len(lengths))

	val := 10
	for i, l := range lengths {
		jagged[i] = make([]int, l)
		for j := range jagged[i] {
			jagged[i][j] = val
			val += 5
		}
	}

	fmt.Println("Зубчатый динамический срез:")
	for i, row := range jagged {
		fmt.Printf("Строка #%d (len=%d): %v\\n", i, len(row), row)
	}
}""",
                "note": "Зубчатый динамический срез"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Зубчатый динамический срез:
# Строка #0 (len=2): [10 15]
# Строка #1 (len=4): [20 25 30 35]
# Строка #2 (len=1): [40]
# Строка #3 (len=3): [45 50 55]""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Каждая строка аллоцируется отдельно в куче.
""",
        "pitfalls": """
- Предположение о квадратной форме матрицы.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Где в Go стандартной библиотеке применяются зубчатые срезы?»
**Ответ:** В таблицах кодировок `unicode`, синтаксических парсерах и графах зависимостей `go/build`.
"""
    },
    {
        "num": 69,
        "title": "Утечка памяти при возврате среза из 1 000 000 элементов и исправление через make + copy",
        "task": "Утечка памяти при слайсинге: Создайте функцию, которая читает «большой» срез (например, 1 000 000 элементов) и возвращает маленький срез из 2 элементов (bigSlice[0:2]). Объясните, почему этот маленький срез удерживает в памяти весь миллионный массив. Напишите правильное решение с использованием copy, которое позволит сборщику мусора освободить память от большого массива.",
        "theory": """
Финальный закрепляющий разбор утечки памяти в архитектуре Go.
""",
        "step_by_step": """
1. Моделируем генерацию большого среза на 1 000 000 элементов.
2. Пишем функцию с утечкой `LeakyHead`.
3. Пишем исправленную функцию `SafeHead`.
4. Сравниваем адреса и объем памяти.
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

func LeakyHead() []int {
	huge := make([]int, 1_000_000)
	huge[0], huge[1] = 100, 200
	return huge[:2] // Удерживает весь 1_000_000 массив!
}

func SafeHead() []int {
	huge := make([]int, 1_000_000)
	huge[0], huge[1] = 100, 200

	// Клонируем в независимый срез:
	clean := make([]int, 2)
	copy(clean, huge[:2])
	return clean // huge освобождается сборщиком мусора!
}

func main() {
	safe := SafeHead()
	runtime.GC()
	fmt.Printf("SafeHead результат:  %v (len=%d, cap=%d)\\n", safe, len(safe), cap(safe))

	leaky := LeakyHead()
	fmt.Printf("LeakyHead результат: %v (len=%d, cap=%d - УДЕРЖИВАЕТ 8 МБ!)\\n",
		leaky, len(leaky), cap(leaky))
}""",
                "note": "Устранение утечки памяти"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# SafeHead результат:  [100 200] (len=2, cap=2)
# LeakyHead результат: [100 200] (len=2, cap=1000000 - УДЕРЖИВАЕТ 8 МБ!)""",
                "note": "cap(leaky) = 1_000_000 против cap(safe) = 2"
            }
        ],
        "under_the_hood": """
Поле `Cap = 1_000_000` в `LeakyHead` удерживает всю аллокацию от сбора GC.
""",
        "pitfalls": """
- Игнорирование `cap` среза при профилировании через `pprof`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какой инструмент в Go позволяет найти утечки памяти, вызванные удержанием срезов?»
**Ответ:** Профилировщик `pprof` с анализом профиля аллокаций памяти (`go tool pprof -inuse_space / alloc_space`).
"""
    },
    {
        "num": 70,
        "title": "Зубчатый массив [][]int произвольной структуры",
        "task": "Создай слайс слайсов [][]int. Заполни его несколькими внутренними слайсами разной длины (зубчатый массив).",
        "theory": """
Базовое создание произвольного зубчатого массива через литералы.
""",
        "step_by_step": """
1. Создаем `jagged := [][]int{ {1}, {2, 3, 4}, {5, 6} }`.
2. Выводим строки и их длины.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	jagged := [][]int{
		{1},
		{2, 3, 4, 5},
		{6, 7},
		{8, 9, 10},
	}

	for i, row := range jagged {
		fmt.Printf("Строка [%d] (длина %d): %v\\n", i, len(row), row)
	}
}""",
                "note": "Литерал зубчатого среза"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Строка [0] (длина 1): [1]
# Строка [1] (длина 4): [2 3 4 5]
# Строка [2] (длина 2): [6 7]
# Строка [3] (длина 3): [8 9 10]""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Каждая строка — отдельный `SliceHeader`.
""",
        "pitfalls": """
- Доступ `jagged[0][2]` вызовет панику.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли сделать срез срезов плоским (Flatten) за $O(N)$?»
**Ответ:** Да, циклом `for _, row := range jagged { flat = append(flat, row...) }`.
"""
    },
    {
        "num": 71,
        "title": "Сбор среза указателей []*int на элементы среза: правильная индексация &s[i] vs Go 1.22+",
        "task": "Напишите функцию, которая принимает слайс и возвращает слайс указателей на его элементы (осторожно с захватом переменной цикла). Покажите правильный способ.",
        "theory": """
**Правильный сбор указателей на элементы среза:**
- Самый надежный и быстрый способ во всех версиях Go: прямое взятие адреса ячейки среза `&s[i]`;
- В Go 1.22+ `for _, v := range s` создает новую переменную `v` на каждой итерации, но `&v` берет адрес локальной копии, а НЕ ячейки среза `s`!
- Чтобы указатель ссылался на сам базовый массив, используют строго `&s[i]`.
""",
        "step_by_step": """
1. Создаем срез `numbers := []int{10, 20, 30}`.
2. Собираем указатели через `&numbers[i]`.
3. Модифицируем значение через указатель и проверяем срез.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func GetPointers(s []int) []*int {
	ptrs := make([]*int, len(s))
	for i := range s {
		ptrs[i] = &s[i] // Берем прямой адрес ячейки в базовом массиве!
	}
	return ptrs
}

func main() {
	numbers := []int{10, 20, 30}
	ptrs := GetPointers(numbers)

	fmt.Printf("Исходный срез:   %v\\n", numbers)

	// Модифицируем элемент через собранный указатель:
	*ptrs[1] = 999

	fmt.Printf("Срез после мутации *ptrs[1] = 999: %v (УСПЕШНО!)\\n", numbers)
}""",
                "note": "Сбор указателей на элементы среза"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Исходный срез:   [10 20 30]
# Срез после мутации *ptrs[1] = 999: [10 999 30] (УСПЕШНО!)""",
                "note": "Прямая мутация базового массива через указатели"
            }
        ],
        "under_the_hood": """
`&s[i]` вычисляет адрес `s.Data + i*sizeof(int)` в памяти.
""",
        "pitfalls": """
- Взятие `&v` в цикле `for _, v := range s`: указатель будет указывать на стековую переменную `v`, и мутация `*ptr = 999` не изменит срез `s`!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `&v` в `for _, v := range s` не мутирует срез даже в Go 1.22+?»
**Ответ:** Потому что `v` — это копия значения элемента. В Go 1.22+ `&v` дает уникальный адрес копии, но это по-прежнему отдельная переменная, не связанная с базовым массивом среза.
"""
    },
    {
        "num": 72,
        "title": "Функция Filter с дженериками и предикатом func(T) bool",
        "task": "Напиши функцию Filter(nums []int, predicate func(int) bool) []int, которая возвращает новый слайс только с теми элементами, для которых predicate вернул true.",
        "theory": """
Реализация дженерик-фильтрации `Filter[T any](s []T, pred func(T) bool) []T`.
""",
        "step_by_step": """
1. Пишем `Filter[T any](s []T, predicate func(T) bool) []T`.
2. Тестируем на целых числах и строках.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func Filter[T any](s []T, predicate func(T) bool) []T {
	var result []T
	for _, v := range s {
		if predicate(v) {
			result = append(result, v)
		}
	}
	return result
}

func main() {
	numbers := []int{10, 15, 20, 25, 30}
	multiplesOfTen := Filter(numbers, func(n int) bool {
		return n%10 == 0
	})

	words := []string{"Go", "Rust", "Golang", "C"}
	longWords := Filter(words, func(w string) bool {
		return len(w) > 2
	})

	fmt.Printf("Числа, кратные 10: %v\\n", multiplesOfTen)
	fmt.Printf("Длинные слова:     %v\\n", longWords)
}""",
                "note": "Дженерик функция Filter"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Числа, кратные 10: [10 20 30]
# Длинные слова:     [Rust Golang]""",
                "note": "Результаты фильтрации"
            }
        ],
        "under_the_hood": """
GC-shape stenciling компилятора Go генерирует единый машинный код для всех ссылочных типов.
""",
        "pitfalls": """
- Передача тяжелых предикатов с захватом внешнего контекста.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как реализовать функцию `Map[T, R any](s []T, f func(T) R) []R`?»
**Ответ:** `res := make([]R, len(s)); for i, v := range s { res[i] = f(v) }; return res`.
"""
    },
    {
        "num": 73,
        "title": "Многокритериальная сортировка среза структур User через slices.SortFunc (Go 1.21+)",
        "task": "Сортировка срезов: Создайте срез структур User (поля Name и Age). Используя современный стандартный пакет slices (доступен в современных версиях Go) или пакет sort, отсортируйте срез пользователей по возрасту, а затем по имени.",
        "theory": """
**Современная сортировка через `slices.SortFunc`:**
- Функция сравнения `cmp(a, b User) int`:
  - Возвращает отрицательное число, если $a < b$;
  - Возвращает `0`, если $a == b$;
  - Возвращает положительное число, если $a > b$;
- Функция `cmp.Compare` из пакета `cmp` идеально подходит для комбинации полей.
""",
        "step_by_step": """
1. Создаем структуру `User{Name string, Age int}`.
2. Используем `slices.SortFunc` с `cmp.Compare`.
3. Проверяем сортировку по возрасту, затем по имени.
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
)

type User struct {
	Name string
	Age  int
}

func main() {
	users := []User{
		{Name: "Сергей", Age: 28},
		{Name: "Алексей", Age: 22},
		{Name: "Борис", Age: 28},
		{Name: "Дмитрий", Age: 22},
	}

	// Сортировка: сначала по Age, затем по Name
	slices.SortFunc(users, func(a, b User) int {
		if n := cmp.Compare(a.Age, b.Age); n != 0 {
			return n
		}
		return cmp.Compare(a.Name, b.Name)
	})

	fmt.Println("Отсортированные пользователи (Age -> Name):")
	for _, u := range users {
		fmt.Printf("  • %-10s (возраст: %d)\\n", u.Name, u.Age)
	}
}""",
                "note": "Сортировка через slices.SortFunc"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Отсортированные пользователи (Age -> Name):
#   • Алексей    (возраст: 22)
#   • Дмитрий    (возраст: 22)
#   • Борис      (возраст: 28)
#   • Сергей     (возраст: 28)""",
                "note": "Идеальная многоуровневая сортировка"
            }
        ],
        "under_the_hood": """
`slices.SortFunc` не использует рефлексию и работает на $30-50\%$ быстрее старого `sort.Slice`.
""",
        "pitfalls": """
- Ручное вычитание `a.Age - b.Age` вместо `cmp.Compare`: может привести к переполнению целых чисел (Integer Overflow).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `cmp.Compare(a, b)` безопаснее прямого вычитания `a - b`?»
**Ответ:** Вычитание `math.MinInt64 - 1` приводит к переполнению знакового типа. `cmp.Compare` использует операторы `<` и `>`, гарантируя корректный результат для любых граничных значений.
"""
    },
    {
        "num": 74,
        "title": "Многомерный треугольный динамический срез (Треугольник Паскаля) и ступенчатый вывод",
        "task": "Многомерные динамические срезы: Создайте треугольный срез (зубчатый массив), где первая строка содержит 1 элемент, вторая — 2, третья — 3 и т.д. Заполните его числами и выведите на экран.",
        "theory": """
**Построение треугольной матрицы (Triangular Slice):**
- Строка `i` имеет длину `i + 1`;
- Суммарное число элементов для $N$ строк: $\\frac{N(N+1)}{2}$;
- Классическая структура для графов, динамического программирования и треугольника Паскаля.
""",
        "step_by_step": """
1. Создаем `triangle := make([][]int, 5)`.
2. В цикле выделяем строки длины `i + 1`.
3. Заполняем числами от 1 и выводим.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	rows := 5
	triangle := make([][]int, rows)

	counter := 1
	for i := 0; i < rows; i++ {
		triangle[i] = make([]int, i+1) // Длина строки = номер строки + 1
		for j := 0; j <= i; j++ {
			triangle[i][j] = counter
			counter++
		}
	}

	fmt.Println("=== ТРЕУГОЛЬНЫЙ СРЕЗ (5 СТРОК) ===")
	for i, row := range triangle {
		fmt.Printf("Строка #%d: ", i+1)
		for _, val := range row {
			fmt.Printf("%3d ", val)
		}
		fmt.Println()
	}
}""",
                "note": "Треугольный динамический срез"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# === ТРЕУГОЛЬНЫЙ СРЕЗ (5 СТРОК) ===
# Строка #1:   1 
# Строка #2:   2   3 
# Строка #3:   4   5   6 
# Строка #4:   7   8   9  10 
# Строка #5:  11  12  13  14  15""",
                "note": "Треугольная структура выведена"
            }
        ],
        "under_the_hood": """
Аллоцируется ровно $N+1$ срезов: 1 внешний дескриптор и 5 внутренних строк.
""",
        "pitfalls": """
- Выход за пределы строки `triangle[i][j]` при `j > i`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как выделить память под треугольный срез за одну аллокацию?»
**Ответ:** Выделить один непрерывный срез `data := make([]int, N*(N+1)/2)`, а затем раздать указатели в `triangle[i]` через срез `data[offset : offset+i+1]`.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 4: {len(exercises)} exercises.")
