# Chapter 3 Part 4: Exercises 46 to 55

exercises = [
    {
        "num": 46,
        "title": "Посимвольное чтение рун Unicode и анализ кодовых точек",
        "task": "Чтение по одному символу: Реализуй посимвольное чтение ввода (рун) и выводи Unicode-код каждого введенного символа.",
        "theory": """
**Руны в Go (`rune` = `int32`):**
В стандарте UTF-8 символы имеют переменную длину от 1 до 4 байт:
- Английские буквы ('A', 'z') — 1 байт;
- Кириллица ('Я', 'ж') — 2 байта;
- Эмодзи ('🚀', '🐹') — 4 байта.

Метод `bufio.Reader.ReadRune()`:
1. Считывает один полный Unicode-символ (кодовую точку);
2. Возвращает руну `r rune`, её размер в байтах `size int` и ошибку `err`.
""",
        "step_by_step": """
1. Инициализируем `reader := bufio.NewReader(os.Stdin)`.
2. В цикле вызываем `r, size, err := reader.ReadRune()`.
3. Печатаем символ, его десятичный код, шестнадцатеричный Unicode (`U+%04X`) и размер в байтах.
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
)

func main() {
	reader := bufio.NewReader(os.Stdin)
	fmt.Print("Введите строку с кириллицей и эмодзи: ")

	for {
		r, size, err := reader.ReadRune()
		if err != nil {
			break
		}

		if r == '\\n' || r == '\\r' {
			break // Конец ввода
		}

		fmt.Printf("Символ: %-3c | Unicode: U+%04X | Dec: %-5d | Байт: %d\\n", r, r, r, size)
	}
}""",
                "note": "Посимвольное чтение рун"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Введите строку с кириллицей и эмодзи: Go 🚀 Да
# Символ: G   | Unicode: U+0047 | Dec: 71    | Байт: 1
# Символ: o   | Unicode: U+006F | Dec: 111   | Байт: 1
# Символ:     | Unicode: U+0020 | Dec: 32    | Байт: 1
# Символ: 🚀  | Unicode: U+1F680| Dec: 128640| Байт: 4
# Символ:     | Unicode: U+0020 | Dec: 32    | Байт: 1
# Символ: Д   | Unicode: U+0414 | Dec: 1044  | Байт: 2
# Символ: а   | Unicode: U+0430 | Dec: 1072  | Байт: 2""",
                "note": "Анализ UTF-8 кодирования"
            }
        ],
        "under_the_hood": """
`ReadRune` считывает первый байт, определяет длину UTF-8 последовательности по старшим битам префикса и дочитывает оставшиеся байты руны из буфера.
""",
        "pitfalls": """
- Итерация по строке через индексы байт `for i := 0; i < len(str); i++ { b := str[i] }` распилит русские буквы пополам. Для обхода символов всегда используют `for _, r := range str` или `[]rune(str)`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему `len("Привет")` возвращает 12, а не 6?»
**Ответ:** Функция `len(s)` в Go возвращает **количество байт** в строке, а не количество символов. Так как каждая кириллическая буква в UTF-8 кодируется 2 байтами, 6 букв занимают 12 байт. Количество символов можно узнать через `utf8.RuneCountInString("Привет")`.
"""
    },
    {
        "num": 47,
        "title": "Сравнение чтения полного имени: bufio.Reader vs fmt.Scanln",
        "task": "Используй bufio.NewReader(os.Stdin) для чтения строки с пробелами. Сравни с fmt.Scanln. Напиши программу, которая читает полное имя пользователя (имя и фамилия через пробел).",
        "theory": """
Сравнительный анализ двух подходов:
- **`fmt.Scanln(&f, &l)`**: требует заранее знать точное количество слов в строке (если пользователь введет отчество — упадет с ошибкой `expected newline`);
- **`bufio.NewReader(os.Stdin).ReadString('\\n')`**: универсален, считывает любое количество слов в строке без ограничений.
""",
        "step_by_step": """
1. Реализуем надежный ввод ФИО через `bufio.Reader`.
2. Разбиваем строку на части через `strings.Fields`.
3. Корректно извлекаем имя, фамилию и опциональное отчество.
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
	fmt.Print("Введите ваше полное имя (например, Александр Сергеевич Пушкин): ")

	input, err := reader.ReadString('\\n')
	if err != nil {
		fmt.Printf("Ошибка: %v\\n", err)
		return
	}

	parts := strings.Fields(strings.TrimSpace(input))
	if len(parts) < 2 {
		fmt.Println("❌ Ошибка: необходимо ввести как минимум Имя и Фамилию!")
		return
	}

	firstName := parts[0]
	lastName := parts[len(parts)-1]

	fmt.Printf("✔ Имя: %s, Фамилия: %s (всего слов: %d)\\n", firstName, lastName, len(parts))
}""",
                "note": "Гибкое чтение имени через bufio.Reader"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Введите ваше полное имя (например, Александр Сергеевич Пушкин): Александр Сергеевич Пушкин
# ✔ Имя: Александр, Фамилия: Пушкин (всего слов: 3)""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
`strings.Fields` за один проход находит границы всех слов и выделяет срез строк, ссылающихся на подстроки исходного текста.
""",
        "pitfalls": """
- Использование жесткого `fmt.Scanln(&first, &last)` сломает пользовательский опыт, если клиент введет второе имя или отчество.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как обработать ввод данных, если пользователь вставил между словами 10 пробелов подряд?»
**Ответ:** `strings.Fields(str)` автоматически объединяет любое количество идущих подряд пробелов, табуляций и переносов строк в один логический разделитель.
"""
    },
    {
        "num": 48,
        "title": "Генерация текстовых шаблонов через функцию с fmt.Sprintf",
        "task": "Используй fmt.Sprintf для формирования строки-шаблона. Создай функцию FormatUser(name string, age int, active bool) string, возвращающую отформатированную строку.",
        "theory": """
Инкапсуляция логики форматирования в чистую функцию:
- Функция `FormatUser` принимает доменные аргументы;
- Возвращает готовую строку с форматированием;
- Не имеет сайд-эффектов ввода-вывода (легко тестируется юнит-тестами).
""",
        "step_by_step": """
1. Объявляем функцию `FormatUser(name string, age int, active bool) string`.
2. Используем `fmt.Sprintf`.
3. Тестируем в функции `main`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func FormatUser(name string, age int, active bool) string {
	status := "НЕАКТИВЕН"
	if active {
		status = "АКТИВЕН"
	}
	return fmt.Sprintf("Пользователь: %-12s | Возраст: %3d | Статус: %s", name, age, status)
}

func main() {
	u1 := FormatUser("Дмитрий", 25, true)
	u2 := FormatUser("Анна", 19, false)
	u3 := FormatUser("Константин", 42, true)

	fmt.Println(u1)
	fmt.Println(u2)
	fmt.Println(u3)
}""",
                "note": "Функция форматирования через Sprintf"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Пользователь: Дмитрий      | Возраст:  25 | Статус: АКТИВЕН
# Пользователь: Анна         | Возраст:  19 | Статус: НЕАКТИВЕН
# Пользователь: Константин   | Возраст:  42 | Статус: АКТИВЕН""",
                "note": "Результат форматирования"
            }
        ],
        "under_the_hood": """
Выравнивание `%-12s` автоматически рассчитывает количество пробелов для дополнения строки до 12 позиций по левому краю.
""",
        "pitfalls": """
- `fmt.Sprintf` рассчитывает ширину `%-12s` по байтам, а не по рунам. Для многобайтовых символов UTF-8 (русские буквы) ширина может незначительно сдвинуться при прямом использовании `%12s`. Для точного выравнивания UTF-8 используют функцию с `utf8.RuneCountInString`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как написать табличный тест для функции `FormatUser`?»
**Ответ:** Использовать срез анонимных структур `[]struct{ name string; age int; active bool; expected string }` и функцию `t.Run` со сравнением результата.
"""
    },
    {
        "num": 49,
        "title": "Прямая низкоуровневая запись в поток os.Stdout через fmt.Fprint",
        "task": "Запиши строку напрямую в os.Stdout с помощью fmt.Fprint.",
        "theory": """
`fmt.Fprint` принимает `io.Writer` в качестве первого аргумента:
`fmt.Fprint(os.Stdout, "Hello")` эквивалентно системной записи в стандартный дескриптор `1`.
""",
        "step_by_step": """
1. Импортируем `fmt` и `os`.
2. Вызываем `fmt.Fprint(os.Stdout, "Сообщение\\n")`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"os"
)

func main() {
	// Прямая запись в дескриптор 1 (Stdout)
	fmt.Fprint(os.Stdout, "Прямой вывод в дескриптор os.Stdout без буферизации.\\n")
}""",
                "note": "Запись в os.Stdout через Fprint"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Прямой вывод в дескриптор os.Stdout без буферизации.""",
                "note": "Результат работы"
            }
        ],
        "under_the_hood": """
`fmt.Print(a...)` в исходном коде Go реализован буквально в одну строчку: `return Fprint(os.Stdout, a...)`.
""",
        "pitfalls": """
- Если закрыть `os.Stdout.Close()`, любые последующие вызовы `fmt.Println` или `fmt.Fprint(os.Stdout)` завершатся ошибкой `os.ErrClosed`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как временно перехватить весь вывод `os.Stdout` в юнит-тесте, чтобы проверить, что функция вывела в консоль?»
**Ответ:** Использовать `os.Pipe()`: подменить `os.Stdout = writePipe`, выполнить тестируемую функцию, закрыть пайп и прочитать перехваченные байты из `readPipe`.
"""
    },
    {
        "num": 50,
        "title": "Интерактивное меню с защитой от некорректного ввода букв",
        "task": "Интерактивное CLI-меню: Создай меню, работающее в цикле (1 - Приветствие, 2 - Показать время, 3 - Очистить экран (вывод пустых строк), 0 - Выход). Обрабатывай некорректный ввод пользователя (буквы вместо цифр).",
        "theory": """
Надежная диспетчеризация CLI-меню:
1. Вывод пунктов меню;
2. Считывание строки целиком через `bufio.Reader`;
3. Преобразование строки в число `choice, err := strconv.Atoi(...)`;
4. Обработка ошибок парсинга и невалидных пунктов без падения программы.
""",
        "step_by_step": """
1. Пишем цикл `for`.
2. Выводим список пунктов 1, 2, 3, 0.
3. Парсим ввод и вызываем соответствующую ветку `switch`.
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
	"strings"
	"time"
)

func main() {
	reader := bufio.NewReader(os.Stdin)

	for {
		fmt.Println("\\n--- МЕНЮ УПРАВЛЕНИЯ ---")
		fmt.Println("1. Приветствие")
		fmt.Println("2. Текущее время сервера")
		fmt.Println("3. Очистить консоль")
		fmt.Println("0. Выход")
		fmt.Print("Выберите пункт (0-3): ")

		input, err := reader.ReadString('\\n')
		if err != nil {
			break
		}

		choice, err := strconv.Atoi(strings.TrimSpace(input))
		if err != nil {
			fmt.Println("❌ Ошибка: введите цифру от 0 до 3, а не текст!")
			continue
		}

		switch choice {
		case 1:
			fmt.Println("👋 Привет, разработчик! Отличного дня.")
		case 2:
			fmt.Printf("⏰ Время на сервере: %s\\n", time.Now().Format("15:04:05 (MST)"))
		case 3:
			fmt.Print("\\033[H\\033[2J") // ANSI код очистки экрана
			fmt.Println("✔ Экран очищен.")
		case 0:
			fmt.Println("🛑 Завершение работы. До свидания!")
			return
		default:
			fmt.Printf("⚠️ Пункт %d отсутствует. Выберите от 0 до 3.\\n", choice)
		}
	}
}""",
                "note": "Защищенное интерактивное меню"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# --- МЕНЮ УПРАВЛЕНИЯ ---
# 1. Приветствие
# 2. Текущее время сервера
# 3. Очистить консоль
# 0. Выход
# Выберите пункт (0-3): abc
# ❌ Ошибка: введите цифру от 0 до 3, а не текст!
# 
# Выберите пункт (0-3): 2
# ⏰ Время на сервере: 14:30:15 (MSK)
# 
# Выберите пункт (0-3): 0
# 🛑 Завершение работы. До свидания!""",
                "note": "Тестирование устойчивости к сбоям"
            }
        ],
        "under_the_hood": """
Последовательность `\\033[H\\033[2J` посылает в VT100/ANSI совместимый эмулятор терминала команду перевода курсора в верхний левый угол (`H`) и очистки всего экрана (`2J`).
""",
        "pitfalls": """
- Использование `fmt.Scan(&choice)`: при вводе `"abc"` программа уйдет в бесконечный цикл, так как символы останутся в `Stdin`. Считывание строки через `bufio.Reader` полностью решает эту проблему.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как сделать консольное меню с поддержкой стрелок на клавиатуре (Interactive TUI)?»
**Ответ:** Использовать библиотеку `charmbracelet/bubbletea` (Elm-архитектура в Go) или `promptui`, которые переводят терминал в сырой режим (Raw Mode) и слушают нажатия стрелок и спецклавиш.
"""
    },
    {
        "num": 51,
        "title": "Реализация интерфейса fmt.Stringer для доменных структур",
        "task": "Реализуй Stringer интерфейс для структуры Book (Title, Author, Year). Переопредели метод String() string. Проверь, что fmt.Println(book) использует твой метод.",
        "theory": """
**Интерфейс `fmt.Stringer`:**
Один из важнейших интерфейсов стандартной библиотеки:
```go
type Stringer interface {
    String() string
}
```
Если структура реализует метод `String() string`, функции `fmt.Println`, `fmt.Printf("%v")` и `fmt.Sprintf` вызывают **именно этот метод** вместо стандартного рефлексивного вывода полей!
""",
        "step_by_step": """
1. Объявляем структуру `Book` с полями `Title`, `Author`, `Year`.
2. Реализуем метод `func (b Book) String() string`.
3. Передаем структуру в `fmt.Println(book)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type Book struct {
	Title  string
	Author string
	Year   int
}

// Реализация интерфейса fmt.Stringer
func (b Book) String() string {
	return fmt.Sprintf("📖 «%s» — %s (%d г.)", b.Title, b.Author, b.Year)
}

func main() {
	book := Book{
		Title:  "Язык программирования Go",
		Author: "Алан Донован, Брайан Керниган",
		Year:   2016,
	}

	// fmt.Println автоматически вызывает метод String()
	fmt.Println(book)

	// fmt.Sprintf также использует String()
	info := fmt.Sprintf("Книга в каталоге: %s", book)
	fmt.Println(info)
}""",
                "note": "Реализация fmt.Stringer"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# 📖 «Язык программирования Go» — Алан Донован, Брайан Керниган (2016 г.)
# Книга в каталоге: 📖 «Язык программирования Go» — Алан Донован, Брайан Керниган (2016 г.)""",
                "note": "Красивый вывод структуры"
            }
        ],
        "under_the_hood": """
При форматировании рантайм Go выполняет проверку утверждения типа (Type Assertion): `if s, ok := p.(Stringer); ok { s.String() }`.
""",
        "pitfalls": """
- **Бесконечная рекурсия:** если внутри метода `String()` вызвать `fmt.Sprintf("%v", b)` (передав ту же структуру `b`), функция вызовет сама себя и упадет с паникой `runtime: goroutine stack exceeds limit`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему метод `String()` рекомендуется реализовывать на value-ресивере `(b Book)`, а не на pointer-ресивере `(b *Book)`?»
**Ответ:** Если метод объявлен на pointer-ресивере `(b *Book) String()`, он сработает только при передаче указателя `fmt.Println(&book)`. При передаче по значению `fmt.Println(book)` интерфейс `fmt.Stringer` не удовлетворится, и Go выведет сырые поля. Метод на value-ресивере работает и для значений, и для указателей.
"""
    },
    {
        "num": 52,
        "title": "Перенаправление потока ошибок Stderr в файл через Shell (2> errors.txt)",
        "task": "Запиши строку напрямую в os.Stderr (ошибки) и перенаправь вывод в файл при запуске go run main.go 2> errors.txt.",
        "theory": """
В командных оболочках (Bash, Zsh, Sh):
- `>` или `1>` — перенаправляет поток `os.Stdout`;
- `2>` — перенаправляет поток ошибок `os.Stderr`;
- `&>` или `2>&1` — объединяет оба потока в один файл.
""",
        "step_by_step": """
1. Пишем сообщения в `os.Stdout` и в `os.Stderr`.
2. Запускаем с перенаправлением `2> errors.txt`.
3. Проверяем содержимое консоли и файла `errors.txt`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"os"
)

func main() {
	fmt.Fprintln(os.Stdout, "[INFO] Сервис успешно запущен.")
	fmt.Fprintln(os.Stderr, "[ERROR] Предупреждение: подключение к Redis нестабильно!")
	fmt.Fprintln(os.Stdout, "[INFO] Обработано 150 запросов.")
	fmt.Fprintln(os.Stderr, "[ERROR] Критическая ошибка: таймаут БД.")
}""",
                "note": "Разделение логов по потокам"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# Перенаправляем только поток ошибок дескриптора 2 в файл:
go run main.go 2> errors.txt
# В терминале отображается только Stdout:
# [INFO] Сервис успешно запущен.
# [INFO] Обработано 150 запросов.

# Проверяем файл errors.txt:
cat errors.txt
# [ERROR] Предупреждение: подключение к Redis нестабильно!
# [ERROR] Критическая ошибка: таймаут БД.""",
                "note": "Проверка перенаправления"
            }
        ],
        "under_the_hood": """
Шелл вызывает системный вызов `dup2(file_fd, 2)`, заменяя дескриптор `os.Stderr` процесса на дескриптор открытого файла.
""",
        "pitfalls": """
- Забыть, что буфер `os.Stderr` в Linux обычно не буферизуется (Unbuffered) или сбрасывается немедленно, в то время как `os.Stdout` при перенаправлении в файл может буферизоваться блоками по 4 КБ.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Что означает конструкция `command > /dev/null 2>&1` в Linux скриптах?»
**Ответ:** Она полностью глушит любой вывод команды: `>` перенаправляет `Stdout` в псевдоустройство `/dev/null` (черную дыру), а `2>&1` перенаправляет поток ошибок `Stderr` (дескриптор 2) в поток `Stdout` (дескриптор 1), который уже направлен в `/dev/null`.
"""
    },
    {
        "num": 53,
        "title": "Интерфейс fmt.GoStringer и спецификатор %#v",
        "task": "Реализуй GoStringer интерфейс (GoString() string) для той же структуры. Проверь разницу между %v и %#v.",
        "theory": """
**Интерфейс `fmt.GoStringer`:**
```go
type GoStringer interface {
    GoString() string
}
```
- Метод `String() string` вызывается при `%v`, `%s` и `fmt.Println`;
- Метод `GoString() string` вызывается **строго при спецификаторе `%#v`**;
- Позволяет генерировать точный Go-код для сериализации объектов или отладки.
""",
        "step_by_step": """
1. Создаем структуру `Money` (сумма и валюта).
2. Реализуем `String() string` (для пользователей) и `GoString() string` (для разработчиков).
3. Сравниваем вывод `%v` и `%#v`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type Money struct {
	AmountCents int64
	Currency    string
}

// Для пользовательского интерфейса (%v, Println)
func (m Money) String() string {
	return fmt.Sprintf("%.2f %s", float64(m.AmountCents)/100.0, m.Currency)
}

// Для отладки и Go-кода (%#v)
func (m Money) GoString() string {
	return fmt.Sprintf("finance.Money{AmountCents: %d, Currency: %q}", m.AmountCents, m.Currency)
}

func main() {
	price := Money{AmountCents: 154990, Currency: "RUB"}

	fmt.Printf("Пользовательский вид (%%v):  %v\\n", price)
	fmt.Printf("Отладочный вид (%%#v):         %#v\\n", price)
}""",
                "note": "Реализация fmt.GoStringer"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Пользовательский вид (%v):  1549.90 RUB
# Отладочный вид (%#v):         finance.Money{AmountCents: 154990, Currency: "RUB"}""",
                "note": "Разделение представлений"
            }
        ],
        "under_the_hood": """
При обработке флага `#` форматировщик сначала проверяет интерфейс `fmt.GoStringer`. Если он реализован, рефлексивный парсер не запускается.
""",
        "pitfalls": """
- Путаница между `String()` и `GoString()`: не помещайте в `String()` внутренние технические детали, а в `GoString()` — пользовательские тексты.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Зачем нужен `fmt.GoStringer`, если есть стандартный `%#v`?»
**Ответ:** Стандартный `%#v` выводит все приватные поля структуры как есть. `GoString()` позволяет скрыть чувствительные данные (хэши, пароли) или преобразовать внутреннее представление (например, миллисекунды в читаемый `time.Duration`) в валидный Go-синтаксис.
"""
    },
    {
        "num": 54,
        "title": "Чтение аргументов командной строки через срез os.Args",
        "task": "Прочитай аргументы командной строки через os.Args. Выведи первый аргумент (имя программы) и все остальные.",
        "theory": """
Срез `os.Args []string`:
1. `os.Args[0]` — путь или имя исполняемого файла;
2. `os.Args[1:]` — срез параметров командной строки, переданных пользователем;
3. `len(os.Args)` — общее количество аргументов (всегда минимум 1).
""",
        "step_by_step": """
1. Импортируем `os`.
2. Выводим `os.Args[0]`.
3. В цикле обходим `os.Args[1:]` и выводим каждый переданный флаг/параметр.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"os"
)

func main() {
	fmt.Printf("Имя бинарника (os.Args[0]): %s\\n", os.Args[0])
	fmt.Printf("Всего передано параметров:  %d\\n\\n", len(os.Args)-1)

	if len(os.Args) > 1 {
		fmt.Println("Список параметров:")
		for i, arg := range os.Args[1:] {
			fmt.Printf("  [%d] %s\\n", i+1, arg)
		}
	} else {
		fmt.Println("Параметры командной строки не переданы.")
	}
}""",
                "note": "Обработка os.Args"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go deploy --env=prod --replicas=5
# Имя бинарника (os.Args[0]): /tmp/go-build.../exe/main
# Всего передано параметров:  3
# 
# Список параметров:
#   [1] deploy
#   [2] --env=prod
#   [3] --replicas=5""",
                "note": "Пример передачи аргументов"
            }
        ],
        "under_the_hood": """
При запуске процесса ядро Linux копирует массив строк `argv` из стека процесса в рантайм Go, где `runtime.args` формирует слайс `os.Args`.
""",
        "pitfalls": """
- Обращение к `os.Args[1]` без проверки `if len(os.Args) > 1` вызовет панику `panic: runtime error: index out of range [1] with length 1`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему при запуске через `go run main.go` имя `os.Args[0]` выглядит как странный путь `/tmp/go-build.../exe/main`?»
**Ответ:** Потому что `go run` компилирует временный бинарник во временную папку операционной системы и запускает его оттуда. При прямой сборке `go build -o myapp` аргумент `os.Args[0]` будет равен `./myapp`.
"""
    },
    {
        "num": 55,
        "title": "Парсинг флагов командной строки через пакет flag (-port=8080)",
        "task": "Используй пакет flag для парсинга флагов консоли (например, -port=8080). Выведи значение порта.",
        "theory": """
Пакет `flag`:
1. `port := flag.Int("port", 8080, "Порт HTTP-сервера")`
2. `flag.Parse()` — запускает разбор параметров командной строки;
3. Возвращает указатель `*int`, значение из которого извлекается через разыменование `*port`.
""",
        "step_by_step": """
1. Регистрируем флаг порта.
2. Вызываем `flag.Parse()`.
3. Валидируем значение порта (1–65535).
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"flag"
	"fmt"
	"os"
)

func main() {
	port := flag.Int("port", 8080, "Порт для запуска HTTP-сервера")
	host := flag.String("host", "0.0.0.0", "Сетевой интерфейс для прослушивания")

	flag.Parse()

	if *port < 1 || *port > 65535 {
		fmt.Fprintf(os.Stderr, "❌ Ошибка: недопустимый порт %d. Допустимо: 1-65535\\n", *port)
		os.Exit(1)
	}

	fmt.Printf("🚀 Сервер успешно настроен на адрес: %s:%d\\n", *host, *port)
}""",
                "note": "Парсинг флагов через package flag"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """# 1. Запуск с дефолтными значениями:
go run main.go
# 🚀 Сервер успешно настроен на адрес: 0.0.0.0:8080

# 2. Запуск с кастомным портом:
go run main.go -port=9090 -host=127.0.0.1
# 🚀 Сервер успешно настроен на адрес: 127.0.0.1:9090

# 3. Вызов встроенной справки:
go run main.go -help
# Usage of /tmp/go-build.../exe/main:
#   -host string
#     	Сетевой интерфейс для прослушивания (default "0.0.0.0")
#   -port int
#     	Порт для запуска HTTP-сервера (default 8080)""",
                "note": "Тестирование флагов"
            }
        ],
        "under_the_hood": """
`flag.Parse` автоматически перехватывает флаги `-help` и `--help`, печатая описание всех зарегистрированных флагов и завершая программу с кодом 0.
""",
        "pitfalls": """
- Попытка прочитать `*port` до вызова `flag.Parse()`: переменная всегда будет содержать дефолтное значение 8080 независимо от флагов терминала.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В каком порядке приоритетов микросервис должен считывать конфигурацию?»
**Ответ:** Золотой стандарт 12-Factor App в BigTech: 1) Флаги командной строки (наивысший приоритет, переопределяют всё); 2) Переменные окружения (Environment Variables); 3) Файлы конфигурации (YAML/JSON/TOML); 4) Дефолтные значения в коде.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 4: {len(exercises)} exercises.")
