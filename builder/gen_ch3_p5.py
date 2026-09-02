# Chapter 3 Part 5: Exercises 56 to 65

exercises = [
    {
        "num": 56,
        "title": "Сравнительный анализ и тестирование функций Scan, Scanln и Scanf",
        "task": "Напиши программу, которая читает строку с консоли (fmt.Scan, fmt.Scanln, fmt.Scanf). Сравни поведение трёх функций: введи строку с пробелами, числа, смешанные данные.",
        "theory": """
Итоговое сопоставление семейства функций `fmt.Scan*`:
1. **`fmt.Scan`**: игнорирует переносы строк, читает токены до первого пробельного разделителя, ждет ввода недостающих аргументов на следующих строках;
2. **`fmt.Scanln`**: читает аргументы только с текущей строки, строго завершается по `\\n`;
3. **`fmt.Scanf`**: сопоставляет вход строго с шаблоном форматирования, включая литеральные разделители.
""",
        "step_by_step": """
1. Пишем демонстрационную программу с переключением режима сканирования.
2. Проводим сравнительные тесты с пробелами и числами.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
)

func demoSscan() {
	input := "Go 2024 99.5"

	// 1. fmt.Sscan
	var lang string
	var year int
	var score float64
	fmt.Sscan(input, &lang, &year, &score)
	fmt.Printf("1. Sscan:  lang=%s, year=%d, score=%.1f\\n", lang, year, score)

	// 2. fmt.Sscanln
	var l2 string
	var y2 int
	var s2 float64
	fmt.Sscanln(input, &l2, &y2, &s2)
	fmt.Printf("2. Sscanln: lang=%s, year=%d, score=%.1f\\n", l2, y2, s2)

	// 3. fmt.Sscanf
	var l3 string
	var y3 int
	var s3 float64
	fmt.Sscanf(input, "%s %d %f", &l3, &y3, &s3)
	fmt.Printf("3. Sscanf:  lang=%s, year=%d, score=%.1f\\n", l3, y3, s3)
}

func main() {
	fmt.Println("=== Сравнение Scan-функций ===")
	demoSscan()
}""",
                "note": "Сравнение семейств Scan-функций"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# === Сравнение Scan-функций ===
# 1. Sscan:  lang=Go, year=2024, score=99.5
# 2. Sscanln: lang=Go, year=2024, score=99.5
# 3. Sscanf:  lang=Go, year=2024, score=99.5""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Все три функции внутри вызывают единый сканер `fmt.ss`, но передают разные флаги парсера: `nlIsSpace = true` для `Scan`, `nlIsEnd = true` для `Scanln`, и `format != ""` для `Scanf`.
""",
        "pitfalls": """
- Использование `fmt.Scan` для парсинга конфигурационных файлов: `Scan` не видит разницы между переводом строки и пробелом, что может привести к слипанию разных строк конфига.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В каком случае `fmt.Sscan` работает быстрее `fmt.Sscanf`?»
**Ответ:** `fmt.Sscan` работает быстрее, так как не компилирует и не сопоставляет строку формата `%s %d`, а сразу читает токен за токеном.
"""
    },
    {
        "num": 57,
        "title": "Потоковый Unicode-сканер через bufio.Reader.ReadRune",
        "task": "Считай ввод пользователя по одному символу с помощью bufio.Reader (метод ReadRune).",
        "theory": """
Метод `ReadRune()`:
- Автоматически декодирует UTF-8 поток;
- При ошибке декодирования (битый байт) возвращает руну `utf8.RuneError` (`\\uFFFD`) и размер 1 байт.
""",
        "step_by_step": """
1. Создаем ридер над `os.Stdin`.
2. В цикле считываем руны до переноса строки.
3. Проверяем валидность UTF-8 кодирования.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"bufio"
	"fmt"
	"os"
	"unicode/utf8"
)

func main() {
	reader := bufio.NewReader(os.Stdin)
	fmt.Print("Введите текст: ")

	for {
		r, size, err := reader.ReadRune()
		if err != nil {
			break
		}
		if r == '\\n' {
			break
		}

		if r == utf8.RuneError && size == 1 {
			fmt.Println("⚠️ Обнаружен поврежденный байт UTF-8!")
			continue
		}

		fmt.Printf("Руна: %c (код: %d)\\n", r, r)
	}
}""",
                "note": "Посимвольный Unicode-ридер"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Введите текст: Мир 🌍
# Руна: М (код: 1052)
# Руна: и (код: 1080)
# Руна: р (код: 1088)
# Руна:   (код: 32)
# Руна: 🌍 (код: 127757)""",
                "note": "Результат посимвольного разбора"
            }
        ],
        "under_the_hood": """
`ReadRune` проверяет до 4 байт из буфера, используя функцию `utf8.DecodeRune`.
""",
        "pitfalls": """
- Забыть обработать случай `utf8.RuneError`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Сколько байт может занимать одна руна в оперативной памяти и в файле UTF-8?»
**Ответ:** В памяти тип `rune` — это `int32`, поэтому он ВСЕГДА занимает ровно 4 байта. В сериализованном UTF-8 потоке (в файле или сокете) символ занимает от 1 до 4 байт.
"""
    },
    {
        "num": 58,
        "title": "Интерактивное консольное меню с fmt.Scanln",
        "task": "Создай интерактивное меню в консоли: выводи список опций (1. Приветствие, 2. Текущее время, 3. Выход), читай выбор пользователя (fmt.Scanln) и выполняй действие. Обработай неверный ввод.",
        "theory": """
Интерактивное меню на `fmt.Scanln`:
- Очистка потока ввода при ошибках парсинга;
- Использование оператора `switch` для вызова действий.
""",
        "step_by_step": """
1. Создаем бесконечный цикл `for`.
2. Выводим опции 1, 2, 3.
3. Считываем выбор через `fmt.Scanln(&choice)`.
4. Обрабатываем некорректный ввод.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"bufio"
	"fmt"
	"os"
	"time"
)

func main() {
	for {
		fmt.Println("\\n=== ОПЕРАЦИОННОЕ МЕНЮ ===")
		fmt.Println("1. Приветствие")
		fmt.Println("2. Системное время")
		fmt.Println("3. Выход")
		fmt.Print("Ваш выбор: ")

		var choice int
		_, err := fmt.Scanln(&choice)
		if err != nil {
			fmt.Println("❌ Ошибка ввода: введите число 1, 2 или 3.")
			// Сбрасываем буфер ввода
			bufio.NewReader(os.Stdin).ReadString('\\n')
			continue
		}

		switch choice {
		case 1:
			fmt.Println("✨ Привет! Рады видеть вас в системе.")
		case 2:
			fmt.Printf("⏰ Текущее время: %s\\n", time.Now().Format("15:04:05"))
		case 3:
			fmt.Println("👋 Завершение программы. До встречи!")
			return
		default:
			fmt.Printf("⚠️ Опция %d не найдена. Доступны: 1, 2, 3\\n", choice)
		}
	}
}""",
                "note": "Меню на Scanln"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# === ОПЕРАЦИОННОЕ МЕНЮ ===
# 1. Приветствие
# 2. Системное время
# 3. Выход
# Ваш выбор: 1
# ✨ Привет! Рады видеть вас в системе.
# 
# Ваш выбор: 3
# 👋 Завершение программы. До встречи!""",
                "note": "Сессия"
            }
        ],
        "under_the_hood": """
При ошибке `Scanln` не вычитывает символы до конца строки, поэтому ручной сброс через `ReadString('\\n')` обязателен.
""",
        "pitfalls": """
- Если не сбросить буфер при вводе строки `"hello"`, программа зациклится.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как реализовать меню с перехватом сигналов остановки сервиса?»
**Ответ:** Запустить меню в главной горутине, а в параллельной горутине слушать `signal.Notify(chan, syscall.SIGINT, syscall.SIGTERM)`.
"""
    },
    {
        "num": 59,
        "title": "Табличный вывод с левым и правым выравниванием (%10s и %-10s)",
        "task": "Выведи таблицу (имя, возраст, город) выровненную по колонкам с помощью глаголов форматирования %10s и %-10s.",
        "theory": """
Флаги позиционирования строк:
- `%-16s` — выравнивание текста **по левому краю** (подходит для имен, заголовков);
- `%7d` / `%10s` — выравнивание текста **по правому краю** (подходит для чисел, цен, дат);
- `%4d` — выравнивание чисел по правому краю.
""",
        "step_by_step": """
1. Создаем список пользователей.
2. Печатаем форматированную шапку таблицы.
3. В цикле выводим каждую строку с фиксированной шириной полей.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type UserInfo struct {
	Name string
	Age  int
	City string
}

func main() {
	users := []UserInfo{
		{Name: "Александр", Age: 29, City: "Москва"},
		{Name: "Екатерина", Age: 22, City: "Санкт-Петербург"},
		{Name: "Илья", Age: 35, City: "Новосибирск"},
		{Name: "Ольга", Age: 19, City: "Казань"},
	}

	fmt.Println("+------------------+---------+------------------+")
	fmt.Printf("| %-16s | %-7s | %-16s |\\n", "Имя", "Возраст", "Город")
	fmt.Println("+------------------+---------+------------------+")

	for _, u := range users {
		fmt.Printf("| %-16s | %7d | %-16s |\\n", u.Name, u.Age, u.City)
	}

	fmt.Println("+------------------+---------+------------------+")
}""",
                "note": "Выравнивание колонок таблицы"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# +------------------+---------+------------------+
# | Имя              | Возраст | Город            |
# +------------------+---------+------------------+
# | Александр        |      29 | Москва           |
# | Екатерина        |      22 | Санкт-Петербург  |
# | Илья             |      35 | Новосибирск      |
# | Ольга            |      19 | Казань           |
# +------------------+---------+------------------+""",
                "note": "Выровненный табличный отчет"
            }
        ],
        "under_the_hood": """
Форматировщик вычисляет разницу между заданной шириной и длиной строки, дополняя буфер нужным числом пробелов `0x20`.
""",
        "pitfalls": """
- Длина кириллических строк в байтах вдвое больше количества символов. В пакете `fmt` ширина `%16s` считает байты. Если в выводе важна абсолютная точность Unicode-символов, используют библиотеку `olekukonko/tablewriter`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какую библиотеку стандартно используют в Go для красивого вывода таблиц в CLI?»
**Ответ:** `olekukonko/tablewriter` или встроенный в стандартную библиотеку `text/tabwriter`.
"""
    },
    {
        "num": 60,
        "title": "Однострочный CLI-калькулятор через fmt.Scanf (\"%f %s %f\")",
        "task": "Напиши программу-калькулятор в одну строку: читай выражение вида 5 + 3 через fmt.Scanf(\"%d %s %d\"), вычисляй результат. Обработай ошибки ввода.",
        "theory": """
Парсинг математического выражения:
1. Шаблон `"%f %s %f\\n"` разбирает левый операнд, математический знак (`+`, `-`, `*`, `/`) и правый операнд;
2. Обработка деления на ноль (`b == 0`);
3. Валидация поддерживаемых операторов.
""",
        "step_by_step": """
1. Запрашиваем выражение.
2. Считываем через `fmt.Scanf`.
3. В `switch` вычисляем результат.
4. Проверяем граничные случаи.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	var (
		a, b float64
		op   string
	)

	fmt.Print("Введите математическое выражение (например, 10.5 * 2): ")
	n, err := fmt.Scanf("%f %s %f\\n", &a, &op, &b)

	if err != nil || n != 3 {
		fmt.Printf("❌ Ошибка разбора выражения: %v\\n", err)
		return
	}

	var result float64

	switch op {
	case "+":
		result = a + b
	case "-":
		result = a - b
	case "*":
		result = a * b
	case "/":
		if b == 0 {
			fmt.Println("❌ Ошибка: деление на ноль невозможно!")
			return
		}
		result = a / b
	default:
		fmt.Printf("❌ Неизвестный оператор '%s'. Поддерживаются: +, -, *, /\\n", op)
		return
	}

	fmt.Printf("✔ Результат: %.2f %s %.2f = %.2f\\n", a, op, b, result)
}""",
                "note": "Однострочный калькулятор на Scanf"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Введите математическое выражение (например, 10.5 * 2): 42 / 2
# ✔ Результат: 42.00 / 2.00 = 21.00""",
                "note": "Вычисление выражения"
            }
        ],
        "under_the_hood": """
`fmt.Scanf` последовательно преобразует токены через `strconv.ParseFloat`.
""",
        "pitfalls": """
- Ввод оператора слитным текстом (`5+3` вместо `5 + 3`): `Scanf` со спецификатором `%s` не сможет разделить число и знак без пробелов.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как распарсить сложное математическое выражение со скобками `(5 + 3) * 2` в Go?»
**Ответ:** С помощью алгоритма сортировочной станции Дейкстры (Shunting-yard algorithm) для перевода выражения в обратную польскую нотацию (RPN) или через стандартный пакет `go/parser` с `go/token`.
"""
    },
    {
        "num": 61,
        "title": "Мини-интерпретатор командной строки (REPL) высокой сложности",
        "task": "[Высокая сложность]: Напиши свой мини-интерпретатор: в бесконечном цикле считывай команду из консоли (например, \"exit\", \"help\", \"print <text>\") и реагируй на неё, пока не введут \"exit\".",
        "theory": """
Архитектура консольного REPL:
1. Лексер: считывание строки через `bufio.Reader` и разделение на команду и аргументы (`strings.SplitN`);
2. Роутер команд: мапа или `switch` обработчиков;
3. Исполнение и вывод результата.
""",
        "step_by_step": """
1. Инициализируем словарь переменных интерпретатора `store := make(map[string]string)`.
2. Реализуем команды: `set <key> <val>`, `get <key>`, `print <text>`, `help`, `exit`.
3. Запускаем интерактивный цикл.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

func main() {
	reader := bufio.NewReader(os.Stdin)
	store := make(map[string]string)

	fmt.Println("🚀 Go REPL Shell v1.0 (введите 'help' для справки)")

	for {
		fmt.Print("repl> ")
		line, err := reader.ReadString('\\n')
		if err != nil {
			break
		}

		input := strings.TrimSpace(line)
		if input == "" {
			continue
		}

		parts := strings.SplitN(input, " ", 3)
		command := strings.ToLower(parts[0])

		switch command {
		case "exit", "quit":
			fmt.Println("👋 Завершение сессии REPL.")
			return
		case "help":
			fmt.Println("Доступные команды:")
			fmt.Println("  set <ключ> <значение> - сохранить значение")
			fmt.Println("  get <ключ>            - получить значение")
			fmt.Println("  print <текст>         - напечатать строку")
			fmt.Println("  keys                  - список всех ключей")
			fmt.Println("  exit                  - выйти")
		case "set":
			if len(parts) < 3 {
				fmt.Println("❌ Ошибка синтаксиса: используйте 'set <ключ> <значение>'")
				continue
			}
			store[parts[1]] = parts[2]
			fmt.Printf("✔ Ключ '%s' успешно сохранен.\\n", parts[1])
		case "get":
			if len(parts) < 2 {
				fmt.Println("❌ Ошибка: укажите ключ 'get <ключ>'")
				continue
			}
			if val, ok := store[parts[1]]; ok {
				fmt.Printf("=> %s\\n", val)
			} else {
				fmt.Printf("⚠️ Ключ '%s' не найден.\\n", parts[1])
			}
		case "print":
			if len(parts) < 2 {
				fmt.Println()
				continue
			}
			text := strings.TrimPrefix(input, parts[0]+" ")
			fmt.Println(text)
		case "keys":
			fmt.Printf("Всего ключей в памяти: %d\\n", len(store))
			for k, v := range store {
				fmt.Printf("  • %s = %s\\n", k, v)
			}
		default:
			fmt.Printf("❌ Неизвестная команда '%s'. Введите 'help'.\\n", command)
		}
	}
}""",
                "note": "Полнофункциональный REPL-интерпретатор"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 🚀 Go REPL Shell v1.0 (введите 'help' для справки)
# repl> set database postgresql://master:5432
# ✔ Ключ 'database' успешно сохранен.
# repl> get database
# => postgresql://master:5432
# repl> print Привет, мир!
# Привет, мир!
# repl> exit
# 👋 Завершение сессии REPL.""",
                "note": "Интерактивная сессия"
            }
        ],
        "under_the_hood": """
`strings.SplitN(input, " ", 3)` делит строку максимум на 3 части, благодаря чему аргумент `<значение>` может содержать пробелы внутри себя.
""",
        "pitfalls": """
- Использование `strings.Split` вместо `strings.SplitN`: разобьет строку с пробелами на десятки элементов, сломав аргументы команд.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как устроен клиент Redis `redis-cli`?»
**Ответ:** Это классический REPL-интерпретатор: парсит команду пользователя из терминала, кодирует в бинарный протокол RESP (REdis Serialization Protocol), отправляет по TCP-сокету и форматирует ответ в `os.Stdout`.
"""
    },
    {
        "num": 62,
        "title": "Потоковое суммирование чисел из Stdin до EOF через ScanWords",
        "task": "Напиши программу, которая читает числа из stdin до EOF (Ctrl+D / Ctrl+Z). Суммируй все числа и выведи результат. Используй bufio.Scanner с разбиением по словам.",
        "theory": """
**Кастомный сплиттер `scanner.Split(bufio.ScanWords)`:**
По умолчанию `bufio.Scanner` читает строки (`ScanLines`).
Если переключить сплиттер на `bufio.ScanWords`:
1. Сканер будет возвращать слова/числа, разделенные любыми пробелами или переводами строк;
2. Это позволяет читать поток из тысяч чисел независимо от того, как они отформатированы.
""",
        "step_by_step": """
1. Создаем `scanner := bufio.NewScanner(os.Stdin)`.
2. Устанавливаем `scanner.Split(bufio.ScanWords)`.
3. В цикле суммируем числа через `strconv.ParseFloat`.
4. При `EOF` выводим сумму, количество и среднее.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
)

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	// Переключаем сканер в режим чтения слов
	scanner.Split(bufio.ScanWords)

	fmt.Println("Введите поток чисел через пробел или Enter (завершение — Ctrl+D):")

	var total float64
	count := 0

	for scanner.Scan() {
		token := scanner.Text()
		val, err := strconv.ParseFloat(token, 64)
		if err != nil {
			fmt.Printf("⚠️ Пропуск нечислового токена: '%s'\\n", token)
			continue
		}

		total += val
		count++
	}

	if err := scanner.Err(); err != nil {
		fmt.Printf("Ошибка сканера: %v\\n", err)
		return
	}

	fmt.Println("\\n========================================")
	fmt.Printf("Обработано чисел: %d\\n", count)
	fmt.Printf("Сумма:            %.2f\\n", total)
	if count > 0 {
		fmt.Printf("Среднее:          %.2f\\n", total/float64(count))
	}
	fmt.Println("========================================")
}""",
                "note": "Суммирование потока через ScanWords"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# Запуск в конвейере через echo:
echo "10 20.5 30 40 50.5" | go run main.go
# Введите поток чисел через пробел или Enter (завершение — Ctrl+D):
# 
# ========================================
# Обработано чисел: 5
# Сумма:            151.00
# Среднее:          30.20
# ========================================""",
                "note": "Тест с конвейером"
            }
        ],
        "under_the_hood": """
`bufio.ScanWords` пропускает ведущие пробелы и находит конец слова, возвращая срез байт токена без промежуточных строковых аллокаций.
""",
        "pitfalls": """
- Игнорирование ошибки `strconv.ParseFloat`: при вводе случайного текста программа может прибавить 0 или упасть.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как написать свой собственный `bufio.SplitFunc` для парсинга CSV-файлов с разделителем точка с запятой `;`?»
**Ответ:** Реализовать функцию с сигнатурой `func(data []byte, atEOF bool) (advance int, token []byte, err error)`, находящую индекс байта `';'`.
"""
    },
    {
        "num": 63,
        "title": "Таблица умножения 10×10 с идеальным позиционированием (%4d)",
        "task": "Создай программу, которая выводит таблицу умножения 10×10 с выравниванием по правому краю (используй ширину поля в fmt.Printf, например %4d).",
        "theory": """
Двумерное форматирование сетки:
- Внешний цикл по строкам от 1 до 10;
- Внутренний цикл по столбцам от 1 до 10;
- Спецификатор `%4d` обеспечивает строгую сетку из колонок шириной 4 символа.
""",
        "step_by_step": """
1. Печатаем верхнюю строчку с номерами колонок.
2. В двойном цикле вычисляем `i * j` и печатаем через `%4d`.
3. В конце каждой строки делаем `fmt.Println()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	fmt.Println("       ТАБЛИЦА УМНОЖЕНИЯ 10 × 10")
	fmt.Println("--------------------------------------------")

	// Шапка колонок
	fmt.Printf("    ")
	for j := 1; j <= 10; j++ {
		fmt.Printf("%4d", j)
	}
	fmt.Println("\\n    ----------------------------------------")

	// Тело таблицы
	for i := 1; i <= 10; i++ {
		fmt.Printf("%2d |", i)
		for j := 1; j <= 10; j++ {
			fmt.Printf("%4d", i*j)
		}
		fmt.Println()
	}
}""",
                "note": "Сетка таблицы умножения"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
#        ТАБЛИЦА УМНОЖЕНИЯ 10 × 10
# --------------------------------------------
#        1   2   3   4   5   6   7   8   9  10
#     ----------------------------------------
#  1 |   1   2   3   4   5   6   7   8   9  10
#  2 |   2   4   6   8  10  12  14  16  18  20
#  3 |   3   6   9  12  15  18  21  24  27  30
#  4 |   4   8  12  16  20  24  28  32  36  40
#  5 |   5  10  15  20  25  30  35  40  45  50
#  6 |   6  12  18  24  30  36  42  48  54  60
#  7 |   7  14  21  28  35  42  49  56  63  70
#  8 |   8  16  24  32  40  48  56  64  72  80
#  9 |   9  18  27  36  45  54  63  72  81  90
# 10 |  10  20  30  40  50  60  70  80  90 100""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Буфер `fmt.Printf` накапливает байты и сбрасывает их в дескриптор терминала.
""",
        "pitfalls": """
- Забыть выровнять номер строки слева (`%2d |`), из-за чего строка 10 сдвинет всю сетку вправо.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как оптимизировать вывод огромных ASCII-сеток в терминал?»
**Ответ:** Обернуть `os.Stdout` в `bufio.NewWriter(os.Stdout)` и вызвать `writer.Flush()` один раз в конце вывода.
"""
    },
    {
        "num": 64,
        "title": "Динамический консольный прогресс-бар через возврат каретки (\\r)",
        "task": "Напиши программу, которая выводит прогресс-бар в консоль (например, [####------] 40%). Используй \\r для возврата каретки и обновления строки.",
        "theory": """
Механика динамического Progress Bar:
1. Символ `\\r` (Carriage Return) возвращает курсор в начало строки;
2. Общая длина шкалы фиксирована (например, 20 символов);
3. Количество заполненных символов `#` пропорционально проценту выполнения;
4. Оставшиеся ячейки заполняются дефисами `-`.
""",
        "step_by_step": """
1. В цикле от 0 до 100% рассчитываем доли заполнения.
2. Формируем строку `[#####-----] 50%`.
3. Печатаем через `fmt.Printf("\\r...")` с задержкой `time.Sleep`.
4. В конце выводим `fmt.Println()`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"strings"
	"time"
)

func renderProgressBar(percent int, width int) {
	filled := (percent * width) / 100
	empty := width - filled

	bar := strings.Repeat("█", filled) + strings.Repeat("░", empty)
	fmt.Printf("\\r🚀 Загрузка: [%s] %3d%%", bar, percent)
}

func main() {
	totalSteps := 100
	barWidth := 25

	fmt.Println("Старт процесса деплоя артефакта...")

	for i := 0; i <= totalSteps; i++ {
		renderProgressBar(i, barWidth)
		time.Sleep(30 * time.Millisecond)
	}

	fmt.Println("\\n✔ Деплой успешно завершен на 100%!")
}""",
                "note": "Динамический прогресс-бар"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Старт процесса деплоя артефакта...
# 🚀 Загрузка: [█████████████████████████] 100%
# ✔ Деплой успешно завершен на 100%!""",
                "note": "Анимация в реальном времени"
            }
        ],
        "under_the_hood": """
Эмулятор терминала обрабатывает байт `0x0D` (`\\r`), устанавливая внутренний указатель позиции курсора в колонку 0 без изменения текущей строки.
""",
        "pitfalls": """
- Добавление `\\n` в конце строки прогресс-бара приведет к созданию 100 новых строк вместо плавной перезаписи одной строки.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как реализовать многопоточный мульти-прогресс-бар (скачивание 5 файлов одновременно)?»
**Ответ:** Использовать библиотеку `schollz/progressbar` или ANSI escape-команды управления курсором `\\033[A` (курсор вверх на N строк).
"""
    },
    {
        "num": 65,
        "title": "Цветной и стилизованный консольный вывод через ANSI Escape Codes",
        "task": "Создай цветной вывод в консоль без внешних пакетов, используя ANSI escape-коды (\\033[31m — красный, \\033[0m — сброс). Напиши функции Red(), Green(), Yellow() для обёртки строк.",
        "theory": """
**ANSI Escape Sequences (Управляющие коды терминала):**
Формат: `\\033[<КОД>m` (где `\\033` или `\\x1b` — символ ESC):
- `\\033[0m` — полный сброс стилей (Reset);
- `\\033[1m` — жирный шрифт (Bold);
- `\\033[31m` — красный текст (Red);
- `\\033[32m` — зеленый текст (Green);
- `\\033[33m` — желтый текст (Yellow);
- `\\033[36m` — цвет Go Cyan;
- `\\033[41m` — красный фон (Background).
""",
        "step_by_step": """
1. Задаем константы ANSI-кодов.
2. Создаем хелперы `Red(s)`, `Green(s)`, `Yellow(s)`, `Cyan(s)`.
3. Выводим цветные структурированные логи.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

const (
	ColorReset  = "\\033[0m"
	ColorRed    = "\\033[31m"
	ColorGreen  = "\\033[32m"
	ColorYellow = "\\033[33m"
	ColorCyan   = "\\033[36m"
	ColorBold   = "\\033[1m"
)

func Red(s string) string    { return ColorRed + s + ColorReset }
func Green(s string) string  { return ColorGreen + s + ColorReset }
func Yellow(s string) string { return ColorYellow + s + ColorReset }
func Cyan(s string) string   { return ColorCyan + s + ColorReset }
func Bold(s string) string   { return ColorBold + s + ColorReset }

func main() {
	fmt.Println(Bold("=== СИСТЕМА МОНИТОРИНГА KUBERNETES ==="))

	fmt.Printf("[%s] %s: Все поды запущены (%s)\\n", Green("SUCCESS"), Cyan("auth-service"), Green("Ready: 3/3"))
	fmt.Printf("[%s] %s: Превышен порог памяти (%s)\\n", Yellow("WARNING"), Cyan("payment-gate"), Yellow("88% RAM"))
	fmt.Printf("[%s] %s: База данных недоступна! (%s)\\n", Red("CRITICAL"), Cyan("billing-api"), Red("Connection Refused"))
}""",
                "note": "Нативный цветной вывод в консоль"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# === СИСТЕМА МОНИТОРИНГА KUBERNETES ===
# [SUCCESS] auth-service: Все поды запущены (Ready: 3/3)
# [WARNING] payment-gate: Превышен порог памяти (88% RAM)
# [CRITICAL] billing-api: База данных недоступна! (Connection Refused)""",
                "note": "Красочный цветной лог в терминале"
            }
        ],
        "under_the_hood": """
Терминальный драйвер tty перехватывает байты `0x1B '['` и переключает состояние графического рендерера GPU терминала.
""",
        "pitfalls": """
- Забыть вызвать `ColorReset` (`\\033[0m`) в конце строки: весь последующий текст терминала (включая команды пользователя) останется окрашенным в этот цвет!
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в продакшн логгерах (Loki, Elasticsearch, CloudWatch) отключают ANSI-цвета?»
**Ответ:** Системы агрегации логов сохраняют ANSI-последовательности как сырой мусор `\\u001b[31m`, что раздувает размер индексов БД и ломает полнотекстовый поиск. Цветной вывод включают только для локального терминала разработчика при `isatty(stdout)`.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 5: {len(exercises)} exercises.")
