# Chapter 5 Part 4: Exercises 49 to 64

exercises = [
    {
        "num": 49,
        "title": "Интерактивное подтверждение (Yes/No) через Multiple Cases в switch",
        "task": "Напиши программу с switch с multiple cases: case \"yes\", \"y\", \"да\", \"Да\": → подтверждение, case \"no\", \"n\", \"нет\", \"Нет\": → отказ. Покажи удобство группировки.",
        "theory": """
**Множественные строковые литералы в `case`:**
Синтаксис: `case "yes", "y", "да", "Да":`
- Позволяет легко обрабатывать синонимы команд и локализацию;
- Гораздо чище длинных цепочек `cmd == "yes" || cmd == "y" || ...`.
""",
        "step_by_step": """
1. Нормализуем ввод пользователя (удаляем пробелы и переводим в нижний регистр).
2. Обрабатываем группы согласия и отказа.
3. Добавляем `default` для неопознанного ответа.
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

func ParseConfirmation(raw string) (bool, bool) {
	cleaned := strings.ToLower(strings.TrimSpace(raw))

	switch cleaned {
	case "yes", "y", "да", "д", "true", "1":
		return true, true
	case "no", "n", "нет", "н", "false", "0":
		return false, true
	default:
		return false, false // Нераспознанный ввод
	}
}

func main() {
	inputs := []string{"  ДА ", "y", "Нет", "unknown"}

	for _, in := range inputs {
		val, ok := ParseConfirmation(in)
		if !ok {
			fmt.Printf("Ввод %-10q -> ⚠️ Нераспознан\\n", in)
		} else if val {
			fmt.Printf("Ввод %-10q -> ✔ Подтверждено (True)\\n", in)
		} else {
			fmt.Printf("Ввод %-10q -> ❌ Отклонено (False)\\n", in)
		}
	}
}""",
                "note": "Парсинг подтверждений через multiple cases"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Ввод "  ДА "     -> ✔ Подтверждено (True)
# Ввод "y"        -> ✔ Подтверждено (True)
# Ввод "Нет"      -> ❌ Отклонено (False)
# Ввод "unknown"  -> ⚠️ Нераспознан""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Компилятор выполняет сравнение через таблицу смещений строк.
""",
        "pitfalls": """
- Пропуск очистки пробелов `strings.TrimSpace` перед передачей в `switch`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как функция `strconv.ParseBool` устроена внутри?»
**Ответ:** Она использует в точности такой же `switch s` по строковым литералам: `case "1", "t", "T", "true", "TRUE", "True": return true, nil`.
"""
    },
    {
        "num": 50,
        "title": "Определение динамического типа интерфейса any через switch v := x.(type)",
        "task": "Проверка типов (Type switch): Создайте переменную типа any (или interface{}). Присвойте ей сначала число, затем строку. Напишите конструкцию switch v := x.(type), которая определяет динамический тип переменной и выводит соответствующее сообщение (например, \"Это целое число\", \"Это строка\").",
        "theory": """
Демонстрация смены динамического типа переменной интерфейсного типа `any`.
""",
        "step_by_step": """
1. Создаем `var data any = 100`.
2. Анализируем через `Type Switch`.
3. Переприсваиваем `data = "Теперь это строка"` и повторно анализируем.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func DescribeDynamicValue(x any) {
	switch v := x.(type) {
	case int:
		fmt.Printf("Это целое число: %d\\n", v)
	case string:
		fmt.Printf("Это строка: %q (байт: %d)\\n", v, len(v))
	default:
		fmt.Printf("Другой тип: %T\\n", v)
	}
}

func main() {
	var data any

	data = 100
	DescribeDynamicValue(data)

	data = "Теперь это строка"
	DescribeDynamicValue(data)
}""",
                "note": "Динамический Type Switch"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Это целое число: 100
# Это строка: "Теперь это строка" (байт: 33)""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
При присвоении `data = 100` интерфейс хранит дескриптор `int`. При `data = "..."` дескриптор перезаписывается на `string`.
""",
        "pitfalls": """
- Излишнее использование `any` в сигнатурах функций там, где можно использовать строгие типы или дженерики `[T any]`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему дженерики в Go 1.18+ предпочтительнее интерфейса `any`?»
**Ответ:** Дженерики мономорфизируются (GC shape stenciling), обеспечивают статическую проверку типов на этапе компиляции и исключают накладные расходы на боксинг и аллокации в куче.
"""
    },
    {
        "num": 51,
        "title": "Идиома Comma-ok для безопасного чтения из map прямо в заголовке if",
        "task": "If с мапой: Создай map[string]int. Используй идиому \"comma ok\" прямо в if, чтобы проверить наличие ключа: if val, ok := myMap[\"key\"]; ok { ... }.",
        "theory": """
**Идиома Comma-ok для мап:**
`if val, ok := m[key]; ok { ... }`
1. `val` получает значение, если ключ найден;
2. `ok` — булев флаг (`true`, если ключ реально существует в мапе);
3. Если ключа нет, `ok == false`, а `val` равен Zero Value;
4. Это позволяет надежно отличать случай, когда ключ отсутствует, от случая, когда по ключу сохранено значение `0`.
""",
        "step_by_step": """
1. Создаем мапу пользователей и их балансов: `map[string]int{"alice": 100, "bob": 0}`.
2. Проверяем наличие ключа `"bob"` (значение 0) и несуществующего ключа `"charlie"`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	balances := map[string]int{
		"alice": 1500,
		"bob":   0, // Баланс 0 руб. (ключ СУЩЕСТВУЕТ!)
	}

	// 1. Проверка существующего ключа с нулевым значением
	if bal, ok := balances["bob"]; ok {
		fmt.Printf("✔ Пользователь 'bob' найден. Баланс: %d руб.\\n", bal)
	} else {
		fmt.Println("❌ Пользователь 'bob' не зарегистрирован")
	}

	// 2. Проверка несуществующего ключа
	if bal, ok := balances["charlie"]; ok {
		fmt.Printf("✔ Пользователь 'charlie' найден: %d руб.\\n", bal)
	} else {
		fmt.Println("❌ Пользователь 'charlie' не зарегистрирован")
	}
}""",
                "note": "Comma-ok идиома для map"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# ✔ Пользователь 'bob' найден. Баланс: 0 руб.
# ❌ Пользователь 'charlie' не зарегистрирован""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Вызов `m[k]` с двумя переменными транслируется в рантайм-функцию `runtime.mapaccess2_faststr`, возвращающую указатель на данные и булев флаг наличия.
""",
        "pitfalls": """
- Проверка наличия ключа через прямое чтение `if m["bob"] != 0`: если у пользователя реальный баланс 0, условие ложно посчитает, что пользователя нет. Всегда используйте `comma-ok`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В каких еще языковых конструкциях Go применяется идиома Comma-ok?»
**Ответ:** 1) Чтение из канала: `v, ok := <-ch` (`ok == false`, если канал закрыт); 2) Type Assertion: `v, ok := x.(T)` (`ok == false`, если тип не совпал).
"""
    },
    {
        "num": 52,
        "title": "Вычисление академического грейда по проценту через switch true",
        "task": "Напиши программу с switch true для вычисления грейда (A, B, C, D, F) по проценту набранных баллов (90–100=A, 80–89=B и т.д.).",
        "theory": """
Канонический академический калькулятор на `switch true`.
""",
        "step_by_step": """
1. Пишем функцию `CalculateGradePercentage(percent float64) string`.
2. Валидируем диапазон $[0.0, 100.0]$.
3. Возвращаем грейд.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func CalculateGradePercentage(pct float64) string {
	switch {
	case pct < 0 || pct > 100:
		return "Invalid Percentage"
	case pct >= 90:
		return "Grade A"
	case pct >= 80:
		return "Grade B"
	case pct >= 70:
		return "Grade C"
	case pct >= 60:
		return "Grade D"
	default:
		return "Grade F (Fail)"
	}
}

func main() {
	tests := []float64{98.5, 82.0, 71.3, 59.9}
	for _, t := range tests {
		fmt.Printf("%5.1f%% -> %s\\n", t, CalculateGradePercentage(t))
	}
}""",
                "note": "Калькулятор грейда на switch true"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
#  98.5% -> Grade A
#  82.0% -> Grade B
#  71.3% -> Grade C
#  59.9% -> Grade F (Fail)""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Сравнение чисел `float64` через инструкции `UCOMISD`.
""",
        "pitfalls": """
- Пропуск точки с запятой при наличии предварительных вычислений.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли использовать выражения с `float64` в ветках `case` обычного `switch val`?»
**Ответ:** Да, но из-за погрешностей IEEE 754 прямое сопоставление `case 0.3:` может не сработать. Для вещественных чисел всегда рекомендуется `switch true` с неравенствами.
"""
    },
    {
        "num": 53,
        "title": "Доказательство пропуска вызова isTrue() в выражении isFalse() && isTrue()",
        "task": "Логическое сокращение (Short-circuit): Напишите функцию isTrue() bool, которая выводит в консоль \"Вызвана isTrue\" и возвращает true, и аналогичную функцию isFalse() bool, возвращающую false. Напишите условие if isFalse() && isTrue(). Посмотрите на вывод в консоли и объясните, почему функция isTrue даже не была вызвана (эффект короткого замыкания логических операторов).",
        "theory": """
Прямой эксперимент, доказывающий оптимизацию Short-Circuit на уровне компилятора:
- `isFalse() && isTrue()`: функция `isFalse()` возвращает `false`;
- Логическое И требует истинности обоих операндов;
- Так как первый операнд уже ложен, весь результат гарантированно `false`, и второй операнд игнорируется.
""",
        "step_by_step": """
1. Пишем `isTrue()` и `isFalse()` с выводом в консоль.
2. Вызываем `if isFalse() && isTrue()`.
3. Убеждаемся, что в консоли напечатано только `"Вызвана isFalse"`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func isTrue() bool {
	fmt.Println(">>> Вызвана функция isTrue()")
	return true
}

func isFalse() bool {
	fmt.Println(">>> Вызвана функция isFalse()")
	return false
}

func main() {
	fmt.Println("--- Начало проверки: if isFalse() && isTrue() ---")

	if isFalse() && isTrue() {
		fmt.Println("Условие выполнено")
	} else {
		fmt.Println("Условие НЕ выполнено")
	}

	fmt.Println("--- Конец проверки ---")
}""",
                "note": "Эксперимент с Short-Circuit"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# --- Начало проверки: if isFalse() && isTrue() ---
# >>> Вызвана функция isFalse()
# Условие НЕ выполнено
# --- Конец проверки ---""",
                "note": "isTrue() не была вызвана"
            }
        ],
        "under_the_hood": """
Инструкция `CALL isTrue` не выполняется, так как `TEST` флага результата `isFalse` выполняет немедленный прыжок на блок `else`.
""",
        "pitfalls": """
- Ожидание, что обе функции выполнятся ради их сайд-эффектов.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В каком порядке следует располагать предикаты в условии `if FastCheck() && SlowDBCheck()`?»
**Ответ:** Всегда помещать самые быстрые проверки в памяти (`FastCheck()`) первыми, а тяжелые вызовы сети или базы данных (`SlowDBCheck()`) последними.
"""
    },
    {
        "num": 54,
        "title": "Сравнение отсутствия проваливания по умолчанию и ключевого слова fallthrough",
        "task": "Напиши программу, которая демонстрирует: в switch в Go не происходит автоматического проваливания (в отличие от C/C++/Java). Создай case без break и покажи, что выполняется только один case. Затем добавь fallthrough и покажи разницу.",
        "theory": """
Финальный сравнительный бенчмарк семантики `switch`.
""",
        "step_by_step": """
1. Запускаем изолированный switch.
2. Запускаем switch с `fallthrough`.
3. Анализируем разницу в поведении.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func DemonstrateNoFallthrough() {
	fmt.Println("1. Go Switch по умолчанию (нет автоматического проваливания):")
	switch 1 {
	case 1:
		fmt.Println("   • Сработал Case 1")
	case 2:
		fmt.Println("   • Сработал Case 2")
	}
}

func DemonstrateWithFallthrough() {
	fmt.Println("2. Go Switch с явным fallthrough:")
	switch 1 {
	case 1:
		fmt.Println("   • Сработал Case 1")
		fallthrough
	case 2:
		fmt.Println("   • Сработал Case 2 (проваливание)")
	}
}

func main() {
	DemonstrateNoFallthrough()
	fmt.Println()
	DemonstrateWithFallthrough()
}""",
                "note": "Сравнение проваливания"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 1. Go Switch по умолчанию (нет автоматического проваливания):
#    • Сработал Case 1
# 
# 2. Go Switch с явным fallthrough:
#    • Сработал Case 1
#    • Сработал Case 2 (проваливание)""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
В Go отсутствие проваливания устраняет необходимость компилятору генерировать предупреждения `-Wimplicit-fallthrough`, как в GCC/Clang.
""",
        "pitfalls": """
- Попытка написать `fallthrough` после ветки `default`, если она последняя.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему создатели языка Go сделали отсутствие `fallthrough` поведением по умолчанию?»
**Ответ:** По статистике анализа кодовых баз C/C++, более 97% веток `switch` завершались оператором `break`. Отсутствие `break` было источником критических багов (забытый break). Поэтому в Go дефолт инвертировали в безопасную сторону.
"""
    },
    {
        "num": 55,
        "title": "Подсчет гласных букв в UTF-8 строке с помощью for range и switch",
        "task": "Подсчет гласных: Напишите программу, которая принимает строку и с помощью switch внутри range-цикла подсчитывает количество гласных букв.",
        "theory": """
Итерация `for _, r := range text` декодирует UTF-8 руны, а `switch unicode.ToLower(r)` подсчитывает русские и латинские гласные.
""",
        "step_by_step": """
1. Итерируемся по рунам строки.
2. В `switch` перечисляем все гласные через запятую.
3. Инкрементируем счетчик.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"unicode"
)

func CountVowels(text string) int {
	vowelsCount := 0

	for _, r := range text {
		switch unicode.ToLower(r) {
		case 'a', 'e', 'i', 'o', 'u', 'y',
			'а', 'е', 'ё', 'и', 'о', 'у', 'ы', 'э', 'ю', 'я':
			vowelsCount++
		}
	}

	return vowelsCount
}

func main() {
	phrase := "Изучаем язык Go и высоконагруженный бэкенд!"
	count := CountVowels(phrase)

	fmt.Printf("Текст: %q\\n", phrase)
	fmt.Printf("Количество гласных букв: %d\\n", count)
}""",
                "note": "Подсчет гласных рун"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Текст: "Изучаем язык Go и высоконагруженный бэкенд!"
# Количество гласных букв: 16""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Все руны в `case` проверяются как 32-битные целые числа.
""",
        "pitfalls": """
- Итерация по байтам `for i := 0; i < len(s); i++`: сломает кириллические буквы, так как они состоят из двух байт. Всегда используйте `for range`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `for _, r := range str` возвращает `rune`, а не `byte`?»
**Ответ:** Потому что оператор `range` над строкой автоматически выполняет потоковое декодирование UTF-8, извлекая полноценные 4-байтные кодовые точки Unicode.
"""
    },
    {
        "num": 56,
        "title": "Двухуровневый вложенный switch для классификации арифметических и логических операций",
        "task": "Напиши программу с вложенным switch: внешний — по типу операции (\"арифметика\", \"логика\"), внутренний — по конкретной операции (+, -, &&, ||). Обработай все ветки.",
        "theory": """
Вложенные конструкции `switch` позволяют строить иерархические парсеры выражений и синтаксические анализаторы языков.
""",
        "step_by_step": """
1. Внешний `switch category` разделяет типы выражений.
2. Внутренний `switch op` выполняет конкретное действие.
3. Обрабатываем `default` на обоих уровнях.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func ExecuteNestedOp(category string, op string, a, b int) {
	fmt.Printf("Категория '%s', оператор '%s': ", category, op)

	switch category {
	case "арифметика":
		switch op {
		case "+":
			fmt.Printf("%d + %d = %d\\n", a, b, a+b)
		case "-":
			fmt.Printf("%d - %d = %d\\n", a, b, a-b)
		case "*":
			fmt.Printf("%d * %d = %d\\n", a, b, a*b)
		default:
			fmt.Println("Неизвестный арифметический оператор")
		}

	case "логика":
		bA := a != 0
		bB := b != 0
		switch op {
		case "&&":
			fmt.Printf("%t && %t = %t\\n", bA, bB, bA && bB)
		case "||":
			fmt.Printf("%t || %t = %t\\n", bA, bB, bA || bB)
		default:
			fmt.Println("Неизвестный логический оператор")
		}

	default:
		fmt.Println("Неизвестная категория операций")
	}
}

func main() {
	ExecuteNestedOp("арифметика", "+", 10, 20)
	ExecuteNestedOp("логика", "&&", 1, 0)
	ExecuteNestedOp("графика", "draw", 0, 0)
}""",
                "note": "Вложенный switch"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Категория 'арифметика', оператор '+': 10 + 20 = 30
# Категория 'логика', оператор '&&': true && false = false
# Категория 'графика', оператор 'draw': Неизвестная категория операций""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Компилятор строит двухуровневое дерево переходов.
""",
        "pitfalls": """
- Чрезмерная вложенность `switch`: при более чем 2 уровнях лучше разделять код на отдельные функции.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как избавиться от глубоко вложенных `switch` в парсерах?»
**Ответ:** Использовать паттерн Registry / Dispatch Map (`map[Category]map[Operator]HandlerFunc`).
"""
    },
    {
        "num": 57,
        "title": "Осмысленное применение goto для выхода из многомерного поиска",
        "task": "goto: напишите алгоритм поиска первого отрицательного числа в срезе с использованием goto (аккуратно и осмысленно).",
        "theory": """
**Оператор `goto` в Go:**
1. Разрешен спецификацией, но строго ограничен: нельзя перепрыгивать в чужие блоки, перепрыгивать через объявления переменных или прыгать между функциями;
2. Легальные кейсы применения в стандартной библиотеке: выход из глубоких вложенных циклов и оптимизация конечных автоматов (Lexer / Parser).
""",
        "step_by_step": """
1. Ищем первое отрицательное число в двумерной матрице.
2. При нахождении делаем `goto Found`.
3. Обрабатываем случай отсутствия.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func FindFirstNegativeMatrix(matrix [][]int) (int, int, int, bool) {
	for rowIdx, row := range matrix {
		for colIdx, val := range row {
			if val < 0 {
				// Осмысленное применение goto: мгновенный выход из двойного цикла
				goto Found
			}
		}
	}

	return 0, 0, 0, false

Found:
	// Метка перехода
	// Для чистоты кода извлекаем координаты первого отрицательного
	for r, row := range matrix {
		for c, v := range row {
			if v < 0 {
				return v, r, c, true
			}
		}
	}
	return 0, 0, 0, false
}

func main() {
	matrix := [][]int{
		{10, 20, 30},
		{40, -7, 60},
		{70, 80, 90},
	}

	if val, r, c, ok := FindFirstNegativeMatrix(matrix); ok {
		fmt.Printf("✔ Найдено отрицательное число %d в позиции [%d][%d]\\n", val, r, c)
	} else {
		fmt.Println("Отрицательных чисел нет")
	}
}""",
                "note": "goto для выхода из многомерного цикла"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# ✔ Найдено отрицательное число -7 в позиции [1][1]""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
`goto` компилируется в прямую инструкцию ассемблера `JMP` на локальный адрес без создания стековых фреймов.
""",
        "pitfalls": """
- Попытка перепрыгнуть через объявление переменной: `goto L; x := 10; L:` вызовет ошибку компиляции `goto L jumps over declaration of x`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова альтернатива `goto` для выхода из вложенного цикла в Go?»
**Ответ:** Использование `break Label` (именованный break) или вынос вложенного цикла в отдельную функцию с прямым `return`.
"""
    },
    {
        "num": 58,
        "title": "Проверка битовых флагов прав доступа к файлу в условии if",
        "task": "Битовые флаги в if: Используйте побитовое И (&) в условии if, чтобы проверить, установлен ли определенный бит (флаг) в целом числе (например, проверка прав доступа к файлу perm & 0400 != 0).",
        "theory": """
**Unix File Permissions в восьмеричной системе (Octal):**
- `0400` (Read by Owner);
- `0200` (Write by Owner);
- `0100` (Execute by Owner);
- Проверка: `if (perm & 0400) != 0 { ... }`.
""",
        "step_by_step": """
1. Задаем битовую маску прав `os.FileMode(0755)`.
2. Проверяем права на чтение, запись и исполнение через `&`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"io/fs"
)

const (
	OwnerRead    fs.FileMode = 0400
	OwnerWrite   fs.FileMode = 0200
	OwnerExecute fs.FileMode = 0100
)

func CheckPermissions(perm fs.FileMode) {
	fmt.Printf("Права файла: %04o (%s)\\n", perm, perm)

	if (perm & OwnerRead) != 0 {
		fmt.Println("✔ Владелец имеет право на ЧТЕНИЕ (0400)")
	}
	if (perm & OwnerWrite) != 0 {
		fmt.Println("✔ Владелец имеет право на ЗАПИСЬ (0200)")
	}
	if (perm & OwnerExecute) != 0 {
		fmt.Println("✔ Владелец имеет право на ИСПОЛНЕНИЕ (0100)")
	}
}

func main() {
	CheckPermissions(0755) // rwxr-xr-x
}""",
                "note": "Битовые флаги прав доступа"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Права файла: 0755 (-rwxr-xr-x)
# ✔ Владелец имеет право на ЧТЕНИЕ (0400)
# ✔ Владелец имеет право на ЗАПИСЬ (0200)
# ✔ Владелец имеет право на ИСПОЛНЕНИЕ (0100)""",
                "note": "Результат проверки"
            }
        ],
        "under_the_hood": """
Инструкция `TEST` накладывает битовую маску за 1 такт процессора.
""",
        "pitfalls": """
- Забыть ведущий ноль `0400`: число `400` в десятичной системе не равно `0400` в восьмеричной (`400 != 256`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему права доступа файлов в Linux и Go традиционно записывают в восьмеричной системе счисления с ведущим нулем `0755`?»
**Ответ:** Потому что каждая восьмеричная цифра (0..7) в точности соответствует 3 битам (`rwx`), что идеально ложится на тройки прав: владелец, группа, остальные.
"""
    },
    {
        "num": 59,
        "title": "Интерактивная проверка високосного года с валидацией ввода",
        "task": "Проверка високосного года: запросите год и выведите результат, используя if-else и логические операторы.",
        "theory": """
Интерактивная консольная версия с валидацией диапазона нашей эры.
""",
        "step_by_step": """
1. Считываем год из консоли.
2. Проверяем високосность.
3. Печатаем результат.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	var year int
	fmt.Print("Введите год для проверки: ")
	if _, err := fmt.Scan(&year); err != nil || year <= 0 {
		fmt.Println("Ошибка: введите корректный положительный год")
		return
	}

	if (year%4 == 0 && year%100 != 0) || (year%400 == 0) {
		fmt.Printf("✔ %d год — ВИСОКОСНЫЙ (в феврале 29 дней)\\n", year)
	} else {
		fmt.Printf("❌ %d год — НЕ високосный (в феврале 28 дней)\\n", year)
	}
}""",
                "note": "Интерактивная проверка года"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Введите год для проверки: 2024
# ✔ 2024 год — ВИСОКОСНЫЙ (в феврале 29 дней)""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Компилятор применяет Constant Division / Multiplication by Magic Numbers для быстрого вычисления остатка от деления на 4, 100 и 400.
""",
        "pitfalls": """
- Ввод отрицательных годов до н.э. без предварительной валидации.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как компилятор Go делит целые числа без использования медленной инструкции `IDIV`?»
**Ответ:** Через умножение на обратное магическое число (Magic Multiplier) со сдвигом вправо (алгоритм Granlund-Montgomery), что работает в 10–20 раз быстрее.
"""
    },
    {
        "num": 60,
        "title": "Консольный калькулятор арифметических операций на switch",
        "task": "switch с bool-выражениями: реализуйте калькулятор: спросите два числа и операцию (+, -, *, /), затем через switch operation выполните вычисление.",
        "theory": """
Калькулятор четырех арифметических действий с перехватом деления на ноль.
""",
        "step_by_step": """
1. Принимаем `a`, `op`, `b`.
2. В `switch op` выполняем сложение, вычитание, умножение, деление.
3. Выводим результат с плавающей точкой.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"errors"
	"fmt"
)

func CalculateCLI(a float64, op string, b float64) (float64, error) {
	switch op {
	case "+":
		return a + b, nil
	case "-":
		return a - b, nil
	case "*":
		return a * b, nil
	case "/":
		if b == 0 {
			return 0, errors.New("ошибка: деление на ноль")
		}
		return a / b, nil
	default:
		return 0, fmt.Errorf("неизвестная операция %q", op)
	}
}

func main() {
	res1, _ := CalculateCLI(10, "+", 5)
	res2, _ := CalculateCLI(20, "/", 4)
	_, err := CalculateCLI(15, "/", 0)

	fmt.Println("10 + 5 =", res1)
	fmt.Println("20 / 4 =", res2)
	fmt.Println("15 / 0 ->", err)
}""",
                "note": "Калькулятор на switch"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 10 + 5 = 15
# 20 / 4 = 5
# 15 / 0 -> ошибка: деление на ноль""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Инструкции `ADDSD`, `SUBSD`, `MULSD`, `DIVSD` выполняются над SSE регистрами `XMM`.
""",
        "pitfalls": """
- Деление `float64` на `0.0`: в Go это возвращает `+Inf` (бесконечность) без ошибки, если не проверить `b == 0` вручную!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему деление целых чисел `10 / 0` вызывает панику рантайма, а вещественных `10.0 / 0.0` — нет?»
**Ответ:** Деление целых на ноль не определено в процессоре и генерирует аппаратное прерывание `SIGFPE` (деление на ноль). Для вещественных чисел стандарт IEEE 754 регламентирует возврат $+\infty$, $-\infty$ или `NaN`.
"""
    },
    {
        "num": 61,
        "title": "Таблица диспетчеризации (Dispatch Table) на map[string]func()",
        "task": "Таблица диспетчеризации (Dispatch Table): Замените огромный switch или цепочку if/else на мапу функций (map[string]func()), где ключ — это строка-команда, а значение — функция, которая должна выполниться.",
        "theory": """
**Паттерн Dispatch Table (Таблица диспетчеризации):**
- Заменяет огромные разрастающиеся `switch` на `map[string]CommandHandler`;
- Реализует принцип Open/Closed (SOLID): новые команды регистрируются без модификации существующего кода;
- Время поиска команды составляет $O(1)$ в хэш-таблице.
""",
        "step_by_step": """
1. Определяем тип обработчика `type CommandHandler func(args []string) error`.
2. Создаем мапу `dispatchTable = make(map[string]CommandHandler)`.
3. Регистрируем обработчики `"ping"`, `"stats"`, `"exit"`.
4. Выполняем диспетчеризацию по строковому ключу.
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

type CommandHandler func(args []string)

func main() {
	// Таблица диспетчеризации команд
	handlers := map[string]CommandHandler{
		"ping": func(args []string) {
			fmt.Println("PONG! Задержка: 1.2 мс")
		},
		"echo": func(args []string) {
			fmt.Printf("ECHO: %s\\n", strings.Join(args, " "))
		},
		"version": func(args []string) {
			fmt.Println("Service Version: v2.4.0 (Go 1.22)")
		},
	}

	// Симуляция вызова команд:
	execute := func(cmd string, args []string) {
		if handler, ok := handlers[cmd]; ok {
			handler(args)
		} else {
			fmt.Printf("❌ Неизвестная команда: %s\\n", cmd)
		}
	}

	execute("ping", nil)
	execute("echo", []string{"Hello", "BigTech", "Workout!"})
	execute("unknown", nil)
}""",
                "note": "Dispatch Table на базе map[string]func()"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# PONG! Задержка: 1.2 мс
# ECHO: Hello BigTech Workout!
# ❌ Неизвестная команда: unknown""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Значения мапы хранят 8-байтные указатели на функции. Вызов `handler()` компилируется в косвенный вызов `CALL (reg)`.
""",
        "pitfalls": """
- Вызов `handlers[cmd]()` без проверки `ok`: если ключа нет, вызов `nil()` вызовет немедленную панику.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем преимущество Dispatch Table перед `switch` при разработке плагинов и модульных систем?»
**Ответ:** Модули могут динамически регистрировать новые обработчики в рантайме (через `RegisterHandler(name, fn)`), не изменяя и не перекомпилируя ядро диспетчера.
"""
    },
    {
        "num": 62,
        "title": "Область видимости переменной из заголовка if внутри ветки else",
        "task": "Инициализация в if и область видимости: if x := getValue(); x > 0 { ... } else { // здесь x тоже видна }, покажите ограниченную область x.",
        "theory": """
**Переменная из заголовка `if` видна во всех ветках `else`:**
- `if x := getValue(); x > 0 { ... } else { fmt.Println(x) }`
- Переменная `x` живет на протяжении **всей условной цепочки**, но исчезает сразу после выхода из блока `else`.
""",
        "step_by_step": """
1. Получаем значение в заголовке `if`.
2. Используем переменную внутри ветки `else`.
3. Показываем ошибку при обращении после `else`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func getTemperature() int {
	return -15
}

func main() {
	// Переменная temp видна и в блоке if, и в блоке else:
	if temp := getTemperature(); temp > 0 {
		fmt.Printf("Плюс на улице: +%d °C\\n", temp)
	} else {
		fmt.Printf("Мороз: %d °C (переменная temp доступна в ветке else!)\\n", temp)
	}

	// temp здесь уже не существует
}""",
                "note": "Доступность переменной в ветке else"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Мороз: -15 °C (переменная temp доступна в ветке else!)""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
С точки зрения AST блок `else` находится внутри той же `ast.IfStmt` области видимости.
""",
        "pitfalls": """
- Повторное объявление `temp := ...` в блоке `else`, которое затенит внешнюю `temp`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Будет ли переменная `x` видна во вложенном `else if`, если она объявлена в первом `if x := ...`?»
**Ответ:** ДА! Переменная видна во всех последующих `else if` и финальном `else` данной цепочки.
"""
    },
    {
        "num": 63,
        "title": "Конечный автомат (State Machine) игрового NPC на базе for и switch",
        "task": "Конечный автомат (State Machine): Реализуйте простую логику NPC в игре (состояния: \"Патруль\", \"Тревога\", \"Атака\"), используя for для тиков времени и switch для перехода между состояниями в зависимости от событий.",
        "theory": """
**Конечный автомат (Finite State Machine / FSM):**
- Состояния: `StatePatrol`, `StateAlert`, `StateAttack`;
- Переходы зависят от событий (дистанция до игрока);
- `switch state` определяет поведение NPC на каждом тике игрового цикла.
""",
        "step_by_step": """
1. Задаем состояния FSM через `iota`.
2. В цикле тиков симулируем изменение дистанции до цели.
3. В `switch state` меняем состояние NPC.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type NPCState int

const (
	StatePatrol NPCState = iota
	StateAlert
	StateAttack
)

func (s NPCState) String() string {
	return [...]string{"Патрулирование", "Тревога", "Атака"}[s]
}

func main() {
	state := StatePatrol
	// Симуляция дистанции до игрока на каждом тике:
	distances := []int{50, 25, 8, 4, 30}

	for tick, dist := range distances {
		fmt.Printf("Тик %d (дистанция %2d м) | Текущее состояние: %-15s -> ",
			tick+1, dist, state)

		switch state {
		case StatePatrol:
			if dist < 30 {
				state = StateAlert
				fmt.Println("Замечен шум! Переход в состояние ТРЕВОГА")
			} else {
				fmt.Println("Спокойный обход периметра")
			}

		case StateAlert:
			if dist < 10 {
				state = StateAttack
				fmt.Println("Враг близко! Переход в состояние АТАКА ⚔️")
			} else if dist >= 30 {
				state = StatePatrol
				fmt.Println("Угроза исчезла. Возврат к ПАТРУЛИРОВАНИЮ")
			} else {
				fmt.Println("Осмотр сектора с оружием наготове")
			}

		case StateAttack:
			if dist >= 10 {
				state = StateAlert
				fmt.Println("Цель отступила. Переход в режим ТРЕВОГИ")
			} else {
				fmt.Println("Нанесение урона цели!")
			}
		}
	}
}""",
                "note": "Конечный автомат (FSM) на for и switch"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Тик 1 (дистанция 50 м) | Текущее состояние: Патрулирование   -> Спокойный обход периметра
# Тик 2 (дистанция 25 м) | Текущее состояние: Патрулирование   -> Замечен шум! Переход в состояние ТРЕВОГА
# Тик 3 (дистанция  8 м) | Текущее состояние: Тревога         -> Враг близко! Переход в состояние АТАКА ⚔️
# Тик 4 (дистанция  4 м) | Текущее состояние: Атака           -> Нанесение урона цели!
# Тик 5 (дистанция 30 м) | Текущее состояние: Атака           -> Цель отступила. Переход в режим ТРЕВОГИ""",
                "note": "Результат работы автомата"
            }
        ],
        "under_the_hood": """
FSM на `switch` не требует динамических аллокаций памяти и работает с максимальной скоростью в игровых движках и сетевых протоколах (TCP State Machine).
""",
        "pitfalls": """
- Забыть обработать обратные переходы из активных состояний при исчезновении триггера.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Где в стандартной библиотеке Go используется паттерн State Machine на `for-switch`?»
**Ответ:** В парсерах HTTP-запросов (`net/http`), парсере JSON-токенов (`encoding/json/scanner.go`) и лексере шаблонов (`text/template/parse/lex.go`).
"""
    },
    {
        "num": 64,
        "title": "Интерактивное консольное меню с бесконечным циклом for и switch",
        "task": "Меню с бесконечным циклом и switch: программа постоянно показывает пункты меню, выполняет действие по вводу и выходит по \"quit\".",
        "theory": """
**Паттерн REPL / CLI Menu:**
- `for { ... }` — бесконечный цикл обработки пользовательских команд;
- `switch choice` — маршрутизация действий;
- Выход из цикла через `return` или именованный `break Loop`.
""",
        "step_by_step": """
1. Запускаем бесконечный цикл `for`.
2. Считываем команду.
3. В `case "quit":` делаем `return` или `break`.
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

func main() {
	// Симуляция потока ввода команд пользователя:
	commandStream := []string{"help", "status", "unknown", "quit"}
	cmdIdx := 0

	fmt.Println("=== ДОБРО ПОЖАЛОВАТЬ В CLI СИСТЕМУ ===")

MainMenuLoop:
	for {
		if cmdIdx >= len(commandStream) {
			break MainMenuLoop
		}
		rawCmd := commandStream[cmdIdx]
		cmdIdx++

		cmd := strings.ToLower(strings.TrimSpace(rawCmd))
		fmt.Printf("\\n[Prompt] > %s\\n", cmd)

		switch cmd {
		case "help":
			fmt.Println("Доступные команды: help, status, restart, quit")
		case "status":
			fmt.Println("Все сервисы работают в штатном режиме: OK")
		case "restart":
			fmt.Println("Перезапуск сервиса...")
		case "quit", "exit":
			fmt.Println("Завершение сеанса. До свидания!")
			break MainMenuLoop // Выход из бесконечного цикла for!
		default:
			fmt.Printf("Неизвестная команда '%s'. Введите 'help' для списка.\\n", cmd)
		}
	}

	fmt.Println("Программа штатно завершена.")
}""",
                "note": "Интерактивное меню с именованным break"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# === ДОБРО ПОЖАЛОВАТЬ В CLI СИСТЕМУ ===
# 
# [Prompt] > help
# Доступные команды: help, status, restart, quit
# 
# [Prompt] > status
# Все сервисы работают в штатном режиме: OK
# 
# [Prompt] > unknown
# Неизвестная команда 'unknown'. Введите 'help' для списка.
# 
# [Prompt] > quit
# Завершение сеанса. До свидания!
# Программа штатно завершена.""",
                "note": "Результат работы CLI меню"
            }
        ],
        "under_the_hood": """
Инструкция `break MainMenuLoop` компилируется в `JMP` за пределы цикла `for`, минуя стандартный выход только из блока `switch`.
""",
        "pitfalls": """
- Использование простого `break` вместо `break Label` внутри `switch`: простой `break` прервет только `switch`, и бесконечный цикл `for` продолжит крутиться.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go для выхода из внешнего цикла изнутри `switch` или `select` требуется labeled break?»
**Ответ:** Потому что в Go оператор `break` без метки по умолчанию привязывается к ближайшей окружающей конструкции (`switch`, `select` или `for`). Чтобы явно указать выход из внешнего цикла `for`, используется именованная метка (Labeled Break).
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 4: {len(exercises)} exercises.")
