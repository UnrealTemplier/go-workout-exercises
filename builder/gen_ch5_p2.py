# Chapter 5 Part 2: Exercises 17 to 32

exercises = [
    {
        "num": 17,
        "title": "Классический switch по числовому значению дня недели (1–7)",
        "task": "Классический switch: напишите switch для дня недели (1–7) и выведите название дня.",
        "theory": """
**Оператор `switch` в Go:**
1. Не требует ключевого слова `break` в конце каждой ветки (автоматический выход после выполнения `case`);
2. Ветви `case` вычисляются сверху вниз до первого совпадения;
3. Ветку `default` можно располагать в любом месте блока `switch`, но по соглашению её помещают в самый конец.
""",
        "step_by_step": """
1. Передаем номер дня от 1 до 7.
2. В `switch day` сопоставляем числа с названиями дней.
3. Печатаем результат.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func PrintDayName(day int) {
	switch day {
	case 1:
		fmt.Println("Понедельник")
	case 2:
		fmt.Println("Вторник")
	case 3:
		fmt.Println("Среда")
	case 4:
		fmt.Println("Четверг")
	case 5:
		fmt.Println("Пятница")
	case 6:
		fmt.Println("Суббота")
	case 7:
		fmt.Println("Воскресенье")
	default:
		fmt.Println("Некорректный день недели")
	}
}

func main() {
	PrintDayName(1)
	PrintDayName(5)
	PrintDayName(8)
}""",
                "note": "Классический switch по значению"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Понедельник
# Пятница
# Некорректный день недели""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Для последовательных целых чисел компилятор Go генерирует Jump Table (таблицу косвенных переходов по индексу), которая отрабатывает за константное время $O(1)$.
""",
        "pitfalls": """
- Написание `break` в конце каждого `case` по привычке из C++/Java: в Go это избыточный мертвый код.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Чем поведение `switch` в Go принципиально отличается от C/C++/Java/JS?»
**Ответ:** В Go по умолчанию отсутствует проваливание (No Fallthrough by default). Выполняется строго один выбранный `case`, после чего управление немедленно передается за пределы `switch`.
"""
    },
    {
        "num": 18,
        "title": "Базовый switch по значению с обязательной обработкой ветки default",
        "task": "Базовый switch по значению: Напишите программу, которая принимает число от 1 до 7 (день недели) и с помощью конструкции switch выводит название этого дня (например, 1 — \"Понедельник\"). Добавьте ветку default для обработки некорректных чисел.",
        "theory": """
Ветка `default`:
- Срабатывает, когда ни один из предшествующих `case` не совпал;
- Необходима для защитного программирования (Defensive Programming), чтобы отлавливать невалидные входные данные.
""",
        "step_by_step": """
1. Пишем функцию `GetDayTitle(day int) string`.
2. Добавляем `default: return "Ошибка: день должен быть от 1 до 7"`.
3. Тестируем граничные и невалидные значения.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func GetDayTitle(day int) string {
	switch day {
	case 1:
		return "Понедельник"
	case 2:
		return "Вторник"
	case 3:
		return "Среда"
	case 4:
		return "Четверг"
	case 5:
		return "Пятница"
	case 6:
		return "Суббота"
	case 7:
		return "Воскресенье"
	default:
		return fmt.Sprintf("Ошибка: некорректный день %d (ожидалось 1..7)", day)
	}
}

func main() {
	days := []int{3, 7, 0, 10}
	for _, d := range days {
		fmt.Println(GetDayTitle(d))
	}
}""",
                "note": "Обработка default в switch"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Среда
# Воскресенье
# Ошибка: некорректный день 0 (ожидалось 1..7)
# Ошибка: некорректный день 10 (ожидалось 1..7)""",
                "note": "Результаты"
            }
        ],
        "under_the_hood": """
Если ни один `case` не совпал, процессор совершает безусловный джамп `JMP` на метку блока `default`.
""",
        "pitfalls": """
- Отсутствие `default` в функциях, возвращающих значение без дефолтного `return` в конце.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Обязана ли ветка `default` быть последней в блоке `switch`?»
**Ответ:** Синтаксически нет — `default` может стоять даже первой или посередине `switch`. Однако по стандарту Go Code Style её всегда размещают в самом конце для удобства чтения.
"""
    },
    {
        "num": 19,
        "title": "Диспетчеризация строковых команд CLI через switch по строке",
        "task": "Напиши программу с switch по строке: принимает команду (\"start\", \"stop\", \"restart\", \"status\") и выполняет соответствующее действие (просто выводит сообщение). Добавь default для неизвестной команды.",
        "theory": """
**Строковый `switch` в Go:**
- В отличие от многих языков, где `switch` работает только с числами, в Go `switch` нативно поддерживает строки `string`;
- Сравнение строк выполняется через бинарное сопоставление заголовков и байт памяти.
""",
        "step_by_step": """
1. Получаем текстовую команду службы.
2. В `switch cmd` обрабатываем `"start"`, `"stop"`, `"restart"`, `"status"`.
3. В `default` выводим предупреждение о неизвестной команде.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func ExecuteServiceCommand(cmd string) {
	switch cmd {
	case "start":
		fmt.Println("🚀 Инициализация и запуск демона службы...")
	case "stop":
		fmt.Println("🛑 Остановка рабочих воркеров и сброс буферов...")
	case "restart":
		fmt.Println("🔄 Перезагрузка сервиса (Graceful Restart)...")
	case "status":
		fmt.Println("📊 Статус: Active (running), PID: 4092, Uptime: 48h")
	default:
		fmt.Printf("⚠️ Неизвестная команда '%s'. Доступны: start, stop, restart, status\\n", cmd)
	}
}

func main() {
	commands := []string{"start", "status", "reload"}
	for _, c := range commands {
		ExecuteServiceCommand(c)
	}
}""",
                "note": "Строковый switch для команд"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 🚀 Инициализация и запуск демона службы...
# 📊 Статус: Active (running), PID: 4092, Uptime: 48h
# ⚠️ Неизвестная команда 'reload'. Доступны: start, stop, restart, status""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Для строковых `case` компилятор строит оптимизированное бинарное дерево поиска (Binary Search) по хэшам строк или длинам строк, избегая побайтового сравнения несовпадающих длин.
""",
        "pitfalls": """
- Чувствительность к регистру (`"Start"` не совпадет со `"start"`). Перед `switch` рекомендуется применять `strings.ToLower(strings.TrimSpace(cmd))`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как компилятор Go оптимизирует строковый `switch` с большим количеством веток (например, 50 case)?»
**Ответ:** Компилятор сортирует строковые литералы по значению хэша и длине, генерируя бинарный поиск с логарифмической сложностью $O(\log N)$ вместо наивного линейного перебора $O(N)$.
"""
    },
    {
        "num": 20,
        "title": "Интерактивный ввод и диспетчеризация дней недели через switch",
        "task": "Базовый switch: Запроси у пользователя номер дня недели (1-7) и выведи его название через switch. Обработай default случай (если введено другое число).",
        "theory": """
Интерактивная консольная программа с безопасным чтением через `fmt.Scan` и диспетчеризацией через `switch`.
""",
        "step_by_step": """
1. Запрашиваем ввод у пользователя.
2. Проверяем ошибку парсинга.
3. Передаем число в `switch`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	var day int
	fmt.Print("Введите день недели (1-7): ")
	if _, err := fmt.Scan(&day); err != nil {
		fmt.Println("Ошибка: требуется ввести число")
		return
	}

	switch day {
	case 1:
		fmt.Println("Понедельник — День планирования спринта")
	case 2:
		fmt.Println("Вторник — Активная разработка")
	case 3:
		fmt.Println("Среда — Экватор недели и код-ревью")
	case 4:
		fmt.Println("Четверг — Нагрузочное тестирование")
	case 5:
		fmt.Println("Пятница — Деплой в стейджинг (No Prod Deploy)")
	case 6:
		fmt.Println("Суббота — Выходной день")
	case 7:
		fmt.Println("Воскресенье — Подготовка к новой неделе")
	default:
		fmt.Printf("Неверный номер дня %d. Введите число от 1 до 7.\\n", day)
	}
}""",
                "note": "Интерактивный switch с обработкой ввода"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Введите день недели (1-7): 5
# Пятница — Деплой в стейджинг (No Prod Deploy)""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Все строковые литералы описаний помещаются в сегмент памяти `.rodata`.
""",
        "pitfalls": """
- Игнорирование ошибки ввода `fmt.Scan`: если пользователь введет `"abc"`, переменная `day` останется `0` и попадет в `default`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go принято выносить логику из `main()` в чистые функции для юнит-тестирования?»
**Ответ:** Потому что интерактивные функции с `fmt.Scan` сложно тестировать автоматически, а чистую функцию `GetDaySchedule(day int) string` можно покрыть табличными тестами (Table-Driven Tests) за миллисекунды.
"""
    },
    {
        "num": 21,
        "title": "Трансформация switch со значением в True Switch (switch без выражения)",
        "task": "switch без выражения: превратите предыдущий пример в switch { case day == 1: ... } (true switch).",
        "theory": """
**Конструкция `switch { case expr: }` (True Switch):**
- После слова `switch` нет переменной;
- В каждом `case` пишется полноценное булево выражение (`day == 1`, `day == 2`);
- Позволяет сочетать проверки равенства с диапазонами и сложными предикатами в одном блоке.
""",
        "step_by_step": """
1. Переписываем `switch day` в `switch`.
2. Заменяем `case 1:` на `case day == 1:`.
3. Проверяем идентичность поведения.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func DescribeDayTrueSwitch(day int) string {
	switch {
	case day == 1:
		return "Понедельник"
	case day == 2:
		return "Вторник"
	case day == 3:
		return "Среда"
	case day == 4:
		return "Четверг"
	case day == 5:
		return "Пятница"
	case day == 6:
		return "Суббота"
	case day == 7:
		return "Воскресенье"
	default:
		return "Некорректный день"
	}
}

func main() {
	fmt.Println("День 4:", DescribeDayTrueSwitch(4))
	fmt.Println("День 9:", DescribeDayTrueSwitch(9))
}""",
                "note": "True switch без выражения"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# День 4: Четверг
# День 9: Некорректный день""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
При `switch` без тега компилятор подставляет неявную константу `true` и проверяет равенство результата каждого выражения с `true`.
""",
        "pitfalls": """
- Использование `true switch` для тривиальных равенств `day == 1` менее лаконично, чем обычный `switch day { case 1: }`. True switch раскрывает мощь при сложных диапазонах.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли в одном `case` внутри true switch объединять несколько условий через запятую?»
**Ответ:** ДА! Запись `case day == 6, day == 7:` работает как логическое ИЛИ (`||`) между выражениями.
"""
    },
    {
        "num": 22,
        "title": "Классификация диапазонов возраста через Tagless Switch",
        "task": "Напиши программу с tagless switch (switch true): проверяет диапазон возраста и выводит категорию (\"ребёнок\", \"подросток\", \"взрослый\", \"пенсионер\"). Используй сравнения в case.",
        "theory": """
Tagless Switch идеально подходит для проверки диапазонов чисел:
- `case age < 13:`
- `case age < 18:`
- `case age < 60:`
- `default:`
""",
        "step_by_step": """
1. Задаем возраст `age`.
2. Используем `switch { case age < 13: ... }`.
3. Проверяем порядок условий.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func ClassifyAge(age int) string {
	switch {
	case age < 0:
		return "недопустимый возраст"
	case age <= 12:
		return "ребёнок"
	case age <= 17:
		return "подросток"
	case age <= 59:
		return "взрослый"
	default:
		return "пенсионер"
	}
}

func main() {
	testAges := []int{8, 16, 30, 65, -1}
	for _, a := range testAges {
		fmt.Printf("Возраст %3d: %s\\n", a, ClassifyAge(a))
	}
}""",
                "note": "Классификация диапазонов через tagless switch"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Возраст   8: ребёнок
# Возраст  16: подросток
# Возраст  30: взрослый
# Возраст  65: пенсионер
# Возраст  -1: недопустимый возраст""",
                "note": "Результаты"
            }
        ],
        "under_the_hood": """
SSA-оптимизатор генерирует последовательность сравнений без создания лишних переменных на стеке.
""",
        "pitfalls": """
- Если перепутать порядок (например, поставить `case age <= 59` первым), условие перехватит и детей, и подростков.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Каковы преимущества Tagless Switch перед цепочкой `if - else if`?»
**Ответ:** 1) Отсутствие лесенки фигурных скобок `{}`; 2) Четкая колоночная структура кода; 3) Возможность использования `fallthrough` при необходимости.
"""
    },
    {
        "num": 23,
        "title": "Множественные значения через запятую в одном case (Будни vs Выходные)",
        "task": "Множественный case: Перепиши упр. 117 так, чтобы на дни 1,2,3,4,5 программа выводила \"Будний день\", а на 6,7 — \"Выходной\", объединив значения через запятую в одном case.",
        "theory": """
**Группировка в `case` через запятую:**
Синтаксис: `case 1, 2, 3, 4, 5:`
- Эквивалентно логическому ИЛИ (`day == 1 || day == 2 || ...`);
- Исключает дублирование исполняемого кода и избавляет от необходимости писать `fallthrough`.
""",
        "step_by_step": """
1. Передаем номер дня.
2. В первом `case 1, 2, 3, 4, 5` выводим `"Будний день"`.
3. Во втором `case 6, 7` выводим `"Выходной"`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func CheckWorkday(day int) string {
	switch day {
	case 1, 2, 3, 4, 5:
		return "Будний день (рабочее время)"
	case 6, 7:
		return "Выходной день (отдых)"
	default:
		return "Некорректный день"
	}
}

func main() {
	fmt.Println("Понедельник (1):", CheckWorkday(1))
	fmt.Println("Пятница (5):    ", CheckWorkday(5))
	fmt.Println("Суббота (6):    ", CheckWorkday(6))
	fmt.Println("Воскресенье (7):", CheckWorkday(7))
}""",
                "note": "Группировка значений в case через запятую"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Понедельник (1): Будний день (рабочее время)
# Пятница (5):     Будний день (рабочее время)
# Суббота (6):     Выходной день (отдых)
# Воскресенье (7): Выходной день (отдых)""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Компилятор проверяет вхождение числа в диапазон $[1, 5]$ одной инструкцией сравнения границ `CMP + JBE`.
""",
        "pitfalls": """
- Использование оператора `||` внутри `case 1 || 2:`: в Go синтаксис требует именно **запятую** (`case 1, 2:`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Сколько значений можно перечислить через запятую в одном `case`?»
**Ответ:** Ограничений в спецификации Go нет — можно перечислить любое разумное количество литералов.
"""
    },
    {
        "num": 24,
        "title": "Определение сезонов года: группировка case vs накопление через fallthrough",
        "task": "Напиши программу с switch и fallthrough: по номеру месяца определяет сезон. Используй fallthrough для группировки месяцев в сезоны (например, декабрь → зима, но fallthrough в январь? Нет, сгруппируй case'ы: case 12, 1, 2:). Затем сделай версию с fallthrough, где каждый case \"проваливается\" в следующий для накопления описания.",
        "theory": """
**Ключевое слово `fallthrough`:**
1. Принудительно передает управление на **первую строку следующего `case`**, игнорируя проверку его условия;
2. Должно быть **последней инструкцией** в блоке `case`;
3. Запрещено в финальном `case` или `default` (некуда проваливаться);
4. Запрещено внутри `type switch`.
""",
        "step_by_step": """
1. Реализуем определение сезона через чистую группировку `case 12, 1, 2:`.
2. Реализуем накопительный статус прав пользователя через `fallthrough`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

// 1. Идиоматичная группировка месяцев в сезоны
func GetSeason(month int) string {
	switch month {
	case 12, 1, 2:
		return "Зима ❄️"
	case 3, 4, 5:
		return "Весна 🌸"
	case 6, 7, 8:
		return "Лето ☀️"
	case 9, 10, 11:
		return "Осень 🍁"
	default:
		return "Некорректный месяц"
	}
}

// 2. Накопление прав доступа через fallthrough
func PrintPermissionsCascade(level int) {
	fmt.Printf("Права для уровня %d: ", level)
	switch level {
	case 3:
		fmt.Print("[ADMIN: Полный доступ] ")
		fallthrough
	case 2:
		fmt.Print("[OPERATOR: Запись данных] ")
		fallthrough
	case 1:
		fmt.Print("[GUEST: Чтение] ")
	default:
		fmt.Print("[Нет базовых прав]")
	}
	fmt.Println()
}

func main() {
	fmt.Println("Январь (1):", GetSeason(1))
	fmt.Println("Июль (7):  ", GetSeason(7))
	fmt.Println()

	PrintPermissionsCascade(3)
	PrintPermissionsCascade(1)
}""",
                "note": "Сезоны и накопление через fallthrough"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Январь (1): Зима ❄️
# Июль (7):   Лето ☀️
# 
# Права для уровня 3: [ADMIN: Полный доступ] [OPERATOR: Запись данных] [GUEST: Чтение] 
# Права для уровня 1: [GUEST: Чтение] """,
                "note": "Результат работы"
            }
        ],
        "under_the_hood": """
При `fallthrough` компилятор просто не вставляет инструкцию `JMP` на выход из `switch`, позволяя процессору исполнять следующие инструкции последовательно.
""",
        "pitfalls": """
- Случайное использование `fallthrough` в середине ветки вместо самого конца блока.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `fallthrough` в Go встречается крайне редко в production-коде?»
**Ответ:** Потому что он нарушает принцип независимости веток и часто приводит к трудноуловимым логическим ошибкам. В 99% случаев группировка `case A, B:` чище и безопаснее.
"""
    },
    {
        "num": 25,
        "title": "Категоризация рабочих и выходных дней через группированный switch",
        "task": "Множественные значения в case: Перепишите предыдущую программу с днями недели так, чтобы switch группировал дни: в одном case перечислялись будни (1, 2, 3, 4, 5) и выводилось \"Будний день\", а в другом — выходные (6, 7) с выводом \"Выходной\".",
        "theory": """
Закрепление синтаксиса группировки дней.
""",
        "step_by_step": """
1. Создаем функцию классификации.
2. Проверяем граничные условия.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func DayType(day int) string {
	switch day {
	case 1, 2, 3, 4, 5:
		return "Будний день"
	case 6, 7:
		return "Выходной"
	default:
		return "Неизвестный день"
	}
}

func main() {
	for d := 1; d <= 7; d++ {
		fmt.Printf("День %d: %s\\n", d, DayType(d))
	}
}""",
                "note": "Группировка будней и выходных"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# День 1: Будний день
# День 2: Будний день
# День 3: Будний день
# День 4: Будний день
# День 5: Будний день
# День 6: Выходной
# День 7: Выходной""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Компилятор оптимизирует проверку через битовую маску или диапазон.
""",
        "pitfalls": """
- Забыть ветку `default`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как проверить день недели с помощью пакета `time`?»
**Ответ:** `now := time.Now(); switch now.Weekday() { case time.Saturday, time.Sunday: ... }`.
"""
    },
    {
        "num": 26,
        "title": "Определение выходного дня через case 6, 7:",
        "task": "Несколько значений в case: определите выходной или будний день через case 6, 7:.",
        "theory": """
Компактная проверка выходных дней.
""",
        "step_by_step": """
1. Передаем номер дня.
2. В `case 6, 7:` возвращаем `true`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func IsWeekend(day int) bool {
	switch day {
	case 6, 7:
		return true
	default:
		return false
	}
}

func main() {
	fmt.Println("Среда (3) — выходной?", IsWeekend(3))
	fmt.Println("Суббота (6) — выходной?", IsWeekend(6))
}""",
                "note": "Проверка выходного через switch"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Среда (3) — выходной? false
# Суббота (6) — выходной? true""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Функция компилируется в проверку `(day == 6) || (day == 7)`.
""",
        "pitfalls": """
- Предположение, что 0 — это воскресенье (в зависимости от формата календаря).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какой тип возвращает метод `time.Now().Weekday()`?»
**Ответ:** Пользовательский тип `time.Weekday`, базовым типом которого является `int` (где `Sunday = 0`, `Monday = 1` ... `Saturday = 6`).
"""
    },
    {
        "num": 27,
        "title": "Переключатель типов Type Switch над интерфейсом any (interface{})",
        "task": "Напиши программу с type switch: функция принимает interface{} (или any) и определяет тип значения (int, string, bool, float64). Для каждого типа выводит сообщение с форматированным значением. Добавь default.",
        "theory": """
**Type Switch (`switch v := x.(type)`):**
1. Специальная форма `switch`, работающая только с интерфейсными типами (`any` / `interface{}`);
2. Конструкция `.(type)` разрешена **только внутри заголовка switch**;
3. Внутри каждого блока `case T:` переменная `v` автоматически получает точный статический тип `T`!
""",
        "step_by_step": """
1. Пишем функцию `InspectType(val any)`.
2. Используем `switch v := val.(type)`.
3. Обрабатываем `int`, `string`, `bool`, `float64` и `default`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func InspectType(val any) {
	switch v := val.(type) {
	case int:
		fmt.Printf("Целое число (int): %d | Удвоенное: %d\\n", v, v*2)
	case string:
		fmt.Printf("Строка (string):    %q | Длина: %d\\n", v, len(v))
	case bool:
		fmt.Printf("Флаг (bool):        %t | Инверсия: %t\\n", v, !v)
	case float64:
		fmt.Printf("Дробное (float64):  %.2f | Квадрат: %.2f\\n", v, v*v)
	default:
		fmt.Printf("Неизвестный тип:    %T (значение: %v)\\n", v, v)
	}
}

func main() {
	InspectType(42)
	InspectType("Golang")
	InspectType(true)
	InspectType(3.14)
	InspectType([]int{1, 2, 3})
}""",
                "note": "Type Switch над any"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Целое число (int): 42 | Удвоенное: 84
# Строка (string):    "Golang" | Длина: 6
# Флаг (bool):        true | Инверсия: false
# Дробное (float64):  3.14 | Квадрат: 9.86
# Неизвестный тип:    []int (значение: [1 2 3])""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Рантайм считывает метаданные типа `runtime._type` из интерфейсного заголовка `eface` и выполняет быстрое сопоставление по указателям дескрипторов типов.
""",
        "pitfalls": """
- Попытка использовать `val.(type)` вне оператора `switch`: вызовет ошибку компиляции `use of .(type) outside type switch`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем отличие Type Switch от Type Assertion `v, ok := x.(T)`?»
**Ответ:** Type Assertion проверяет один конкретный тип `T`. Type Switch проверяет множество типов за одну конструкцию и делает это эффективнее за счет единой таблицы типов компилятора.
"""
    },
    {
        "num": 28,
        "title": "Switch без выражения как элегантная замена каскадному if",
        "task": "Switch без выражения (аналог каскадного if): Перепиши упр. 113 (возрастные категории), используя конструкцию switch { case age < 13: ... } (без передачи переменной после слова switch).",
        "theory": """
Tagless Switch структурирует логику и исключает визуальный шум от множественных `else if`.
""",
        "step_by_step": """
1. Пишем функцию через `switch { case age < 13: ... }`.
2. Тестируем категории.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func AgeCategoryTagless(age int) string {
	switch {
	case age < 13:
		return "Ребенок"
	case age < 18:
		return "Подросток"
	case age < 60:
		return "Взрослый"
	default:
		return "Пенсионер"
	}
}

func main() {
	fmt.Println("10 лет:", AgeCategoryTagless(10))
	fmt.Println("15 лет:", AgeCategoryTagless(15))
	fmt.Println("35 лет:", AgeCategoryTagless(35))
	fmt.Println("70 лет:", AgeCategoryTagless(70))
}""",
                "note": "Tagless switch для категорий"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 10 лет: Ребенок
# 15 лет: Подросток
# 35 лет: Взрослый
# 70 лет: Пенсионер""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Все ветки проверяются строго сверху вниз до первого `true`.
""",
        "pitfalls": """
- Неправильная последовательность условий.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем разница в производительности между `if-else if` и `switch true`?»
**Ответ:** Разницы в производительности нет — компилятор Go генерирует для них абсолютно идентичный машинный код. Выбор между ними определяется только читаемостью кода.
"""
    },
    {
        "num": 29,
        "title": "Tagless Switch для академической шкалы оценок по баллам",
        "task": "switch без выражения (Tagless switch): Напишите аналог цепочки if-else из задачи на определение оценки по баллам, используя switch без указания переменной после ключевого слова (когда условия пишутся прямо в ветках case, например, case score >= 90:).",
        "theory": """
Оценка по баллам через `switch { case score >= 90: ... }`.
""",
        "step_by_step": """
1. Пишем функцию `GradeTagless(score int) string`.
2. Реализуем ветки `score >= 90`, `>= 80`, `>= 70`, `>= 50`, `default`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func GradeTagless(score int) string {
	switch {
	case score < 0 || score > 100:
		return "Ошибка: недопустимый балл"
	case score >= 90:
		return "A (Превосходно)"
	case score >= 80:
		return "B (Хорошо)"
	case score >= 70:
		return "C (Удовлетворительно)"
	case score >= 50:
		return "D (Минимальный проходной)"
	default:
		return "F (Не сдал)"
	}
}

func main() {
	fmt.Println("95 баллов:", GradeTagless(95))
	fmt.Println("82 балла: ", GradeTagless(82))
	fmt.Println("45 баллов:", GradeTagless(45))
}""",
                "note": "Грейд через tagless switch"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 95 баллов: A (Превосходно)
# 82 балла:  B (Хорошо)
# 45 баллов: F (Не сдал)""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Ветви сопоставляются последовательно с ранним выходом.
""",
        "pitfalls": """
- Забыть проверку верхнего диапазона `score > 100`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли объявить переменную прямо в заголовке `switch` без тега?»
**Ответ:** ДА! Например: `switch score := getScore(); { case score >= 90: ... }`. Точка с запятой после инициализации обязательна.
"""
    },
    {
        "num": 30,
        "title": "Механика передачи управления следующему case через fallthrough",
        "task": "fallthrough: продемонстрируйте, как fallthrough передаёт управление следующему case, и объясните, зачем это нужно.",
        "theory": """
`fallthrough`:
- Принудительный безусловный переход к телу следующего `case`;
- Условие следующего `case` **НЕ проверяется**;
- Используется в алгоритмах ступенчатого выполнения и эмуляторах инструкций виртуальных машин / байткода.
""",
        "step_by_step": """
1. Создаем `switch step` со значениями 1, 2, 3.
2. Вставляем `fallthrough` в `case 1` и `case 2`.
3. Анализируем каскадный вывод.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func ExecutePipelines(startStep int) {
	fmt.Printf("--- Запуск пайплайна с шага %d ---\\n", startStep)
	switch startStep {
	case 1:
		fmt.Println("1. Сборка артефактов и линтинг")
		fallthrough
	case 2:
		fmt.Println("2. Запуск интеграционных тестов")
		fallthrough
	case 3:
		fmt.Println("3. Развертывание в Kubernetes кластер")
	default:
		fmt.Println("Пайплайн завершен.")
	}
}

func main() {
	ExecutePipelines(1)
	fmt.Println()
	ExecutePipelines(2)
}""",
                "note": "Каскадный конвейер на fallthrough"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# --- Запуск пайплайна с шага 1 ---
# 1. Сборка артефактов и линтинг
# 2. Запуск интеграционных тестов
# 3. Развертывание в Kubernetes кластер
# 
# --- Запуск пайплайна с шага 2 ---
# 2. Запуск интеграционных тестов
# 3. Развертывание в Kubernetes кластер""",
                "note": "Результат работы fallthrough"
            }
        ],
        "under_the_hood": """
Компилятор опускает генерацию инструкции перехода `JMP` на метку выхода `end_switch`.
""",
        "pitfalls": """
- Ошибочное предположение, что при `fallthrough` проверяется условие следующего `case`: следующая ветка выполнится в 100% случаев, даже если её условие ложно!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли сделать `fallthrough` из ветки `default`?»
**Ответ:** Только если `default` не является последней веткой в блоке `switch`. Если `default` стоит в самом конце, `fallthrough` вызовет ошибку компиляции `cannot fallthrough final case in switch`.
"""
    },
    {
        "num": 31,
        "title": "Локальное связывание типов в Type Switch (case int: v * 2)",
        "task": "Напиши программу с type switch, где в каждом case извлекается значение с тем же именем переменной: case int: fmt.Println(v * 2). Покажи, что переменная v в каждом case имеет тип конкретного case'а.",
        "theory": """
**Type Narrowing (Сужение типа):**
В конструкции `switch v := item.(type)`:
- Внутри `case int:` переменная `v` имеет тип `int` (к ней применимы операции `v * 2`, `v + 1`);
- Внутри `case string:` переменная `v` имеет тип `string` (применимы `strings.ToUpper(v)`, `len(v)`);
- Внутри `case []byte:` переменная `v` имеет тип `[]byte`.
""",
        "step_by_step": """
1. Пишем функцию `ProcessItem(item any)`.
2. В каждом `case` выполняем операции, специфичные для конкретного типа.
3. Проверяем компиляцию без ручного приведения типов.
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

func ProcessItem(item any) {
	switch v := item.(type) {
	case int:
		// v здесь строго int:
		fmt.Printf("Число: %d -> Удвоенное: %d\\n", v, v*2)
	case string:
		// v здесь строго string:
		fmt.Printf("Строка: %q -> В верхнем регистре: %s\\n", v, strings.ToUpper(v))
	case []int:
		// v здесь строго []int:
		fmt.Printf("Срез: %v -> Длина среза: %d\\n", v, len(v))
	default:
		fmt.Printf("Другой тип %T: %v\\n", v, v)
	}
}

func main() {
	ProcessItem(50)
	ProcessItem("gopher")
	ProcessItem([]int{10, 20, 30})
}""",
                "note": "Type Narrowing в Type Switch"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Число: 50 -> Удвоенное: 100
# Строка: "gopher" -> В верхнем регистре: GOPHER
# Срез: [10 20 30] -> Длина среза: 3""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Компилятор создает теневые локальные переменные в каждом `case`, автоматически распаковывая поле `data` интерфейса в соответствующий тип.
""",
        "pitfalls": """
- Если в `case` перечислено несколько типов (`case int, int64:`), переменная `v` сохраняет исходный интерфейсный тип `any`, так как точный тип неоднозначен.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какой тип будет иметь переменная `v` в ветке `case int, string:`?»
**Ответ:** Она будет иметь исходный интерфейсный тип `any` (или `interface{}`), потому что компилятор не может статически гарантировать один конкретный тип для нескольких вариантов.
"""
    },
    {
        "num": 32,
        "title": "Сравнение семантики switch в Go (без break) и принудительный fallthrough",
        "task": "Провал проваливания (fallthrough): В Go, в отличие от C/Java/JS, switch не требует break — он выходит автоматически. Попробуй использовать ключевое слово fallthrough в конце одного из case, чтобы заставить программу выполнить следующий case независимо от его условия.",
        "theory": """
Финальное закрепление:
- Обычный `case` изолирован и завершается сам;
- `fallthrough` принудительно пробивает изоляцию и передает управление вниз.
""",
        "step_by_step": """
1. Демонстрируем поведение без `fallthrough` (выполняется только 1 ветка).
2. Демонстрируем поведение с `fallthrough` (выполняются обе ветки).
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func StandardSwitch(val int) {
	fmt.Println("--- 1. Стандартный switch Go (без fallthrough): ---")
	switch val {
	case 1:
		fmt.Println("Ветка 1 выполнена")
	case 2:
		fmt.Println("Ветка 2 выполнена")
	}
}

func FallthroughSwitch(val int) {
	fmt.Println("--- 2. Switch с fallthrough: ---")
	switch val {
	case 1:
		fmt.Println("Ветка 1 выполнена")
		fallthrough // Проваливаемся в ветку 2!
	case 2:
		fmt.Println("Ветка 2 выполнена (хотя val != 2!)")
	}
}

func main() {
	StandardSwitch(1)
	fmt.Println()
	FallthroughSwitch(1)
}""",
                "note": "Сравнение стандартного switch и fallthrough"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# --- 1. Стандартный switch Go (без fallthrough): ---
# Ветка 1 выполнена
# 
# --- 2. Switch с fallthrough: ---
# Ветка 1 выполнена
# Ветка 2 выполнена (хотя val != 2!)""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Разница на уровне ассемблера: наличие инструкции `JMP` в конце базового блока первого `case`.
""",
        "pitfalls": """
- Использование `fallthrough` в расчете на повторную проверку условий следующего `case`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Go ключевое слово `break` все-таки существует внутри `switch`?»
**Ответ:** Чтобы иметь возможность досрочно прервать выполнение длинного блока `case` (например, внутри вложенного `if` условия) и сразу выйти из всего `switch`.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 2: {len(exercises)} exercises.")
