# Chapter 5 Part 3: Exercises 33 to 48

exercises = [
    {
        "num": 33,
        "title": "Имитация тернарного оператора через функцию Max и философия отсутствия ?:",
        "task": "Напиши программу, которая имитирует тернарный оператор через if / else. В Go нет ?: — объясни, почему (философия языка: явность лучше краткости). Напиши функцию Max(a, b int) int без тернарного оператора.",
        "theory": """
**Почему в Go принципиально нет тернарного оператора `cond ? val1 : val2`?**
1. Философия языка: **«Явность лучше неявности, а простота важнее краткости»**;
2. Вложенные тернарные операторы (`a ? b : c ? d : e`) в других языках часто превращаются в нечитаемый спагетти-код;
3. Для нахождения максимума пишется простая, легко оптимизируемая функция `Max(a, b int) int` (начиная с Go 1.21 встроена `max(a, b)`).
""",
        "step_by_step": """
1. Пишем функцию `Max(a, b int) int` через чистый `if`.
2. Пишем функцию `Min(a, b int) int`.
3. Тестируем на различных числах.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

// Каноническая функция Max в Go
func Max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func Min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func main() {
	x, y := 42, 99

	fmt.Printf("Числа: x = %d, y = %d\\n", x, y)
	fmt.Printf("Максимум: %d\\n", Max(x, y))
	fmt.Printf("Минимум:  %d\\n", Min(x, y))
}""",
                "note": "Функции Max и Min вместо тернарного оператора"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Числа: x = 42, y = 99
# Максимум: 99
# Минимум:  42""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Компилятор Go компилирует `if a > b { return a } return b` в условную инструкцию процессора `CMOVGT` (Conditional Move), работающую без ветвления и штрафов за сброс конвейера (Branch Misprediction Penalty).
""",
        "pitfalls": """
- Попытка написать громоздкие однострочные костыли через анонимные функции `func() int { if cond { return a } return b }()` ради «однострочности».
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какая функция появилась в Go 1.21 для нахождения максимума/минимума произвольного количества аргументов?»
**Ответ:** Встроенные дженерик-функции `max(a, b, c...)` и `min(a, b, c...)`, принимающие любое количество упорядоченных типов (`cmp.Ordered`).
"""
    },
    {
        "num": 34,
        "title": "Глубокий анализ цепочки fallthrough при передаче числа 1",
        "task": "Эффект fallthrough: Создайте switch по целому числу от 1 до 3. В ветках case 1 и case 2 добавьте ключевое слово fallthrough. Запустите программу, передав на вход 1, и проанализируйте, почему выполнился код всех последующих веток.",
        "theory": """
При вызове `switch` с `case 1: ... fallthrough; case 2: ... fallthrough; case 3:`:
1. Число совпадает с `case 1`, выполняется код ветки 1;
2. `fallthrough` переносит исполнение на `case 2` (без проверки `val == 2`);
3. `fallthrough` переносит исполнение на `case 3` (без проверки `val == 3`);
4. В итоге отрабатывают **все три ветки подряд**.
""",
        "step_by_step": """
1. Пишем `switch` с каскадным `fallthrough`.
2. Передаем `1` и смотрим трассировку.
3. Передаем `2` и смотрим трассировку со второго шага.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func TraceFallthrough(n int) {
	fmt.Printf("Входное значение: %d\\n", n)
	switch n {
	case 1:
		fmt.Println("  -> Выполнен блок case 1")
		fallthrough
	case 2:
		fmt.Println("  -> Выполнен блок case 2 (по цепочке fallthrough)")
		fallthrough
	case 3:
		fmt.Println("  -> Выполнен блок case 3 (по цепочке fallthrough)")
	default:
		fmt.Println("  -> Блок default")
	}
}

func main() {
	TraceFallthrough(1)
	fmt.Println()
	TraceFallthrough(2)
}""",
                "note": "Трассировка каскада fallthrough"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Входное значение: 1
#   -> Выполнен блок case 1
#   -> Выполнен блок case 2 (по цепочке fallthrough)
#   -> Выполнен блок case 3 (по цепочке fallthrough)
# 
# Входное значение: 2
#   -> Выполнен блок case 2 (по цепочке fallthrough)
#   -> Выполнен блок case 3 (по цепочке fallthrough)""",
                "note": "Результат трассировки"
            }
        ],
        "under_the_hood": """
Инструкции машанного кода располагаются в линейной последовательности, а переход `JMP` на метку `case 2` опускается компилятором.
""",
        "pitfalls": """
- `fallthrough` не может перепрыгнуть через ветку или провалиться в произвольный `case` по имени.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Можно ли использовать `fallthrough` внутри `type switch`?»
**Ответ:** НЕТ! В `type switch` ключевое слово `fallthrough` запрещено спецификацией языка, так как переменная не может одновременно иметь несколько несовместимых статических типов.
"""
    },
    {
        "num": 35,
        "title": "Инспекция динамических типов в рантайме через Type Switch",
        "task": "type switch: создайте несколько переменных разных типов, присвойте их interface{} и внутри switch v := x.(type) выведите название типа.",
        "theory": """
Интерфейс `any` (алиас `interface{}`) может хранить значение любого типа.
`Type Switch` безопасно извлекает и типизирует лежащее внутри значение.
""",
        "step_by_step": """
1. Создаем срез `[]any` с разнотипными объектами (числа, строки, структуры).
2. Обходим в цикле и вызываем `switch v := item.(type)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type CustomPayload struct {
	EventID string
}

func PrintTypeName(x any) {
	switch v := x.(type) {
	case nil:
		fmt.Println("Тип: nil (пустой интерфейс)")
	case int:
		fmt.Printf("Тип: int, значение = %d\\n", v)
	case string:
		fmt.Printf("Тип: string, значение = %q\\n", v)
	case bool:
		fmt.Printf("Тип: bool, значение = %t\\n", v)
	case CustomPayload:
		fmt.Printf("Тип: struct CustomPayload, EventID = %s\\n", v.EventID)
	default:
		fmt.Printf("Тип: %T (нераспознанный)\\n", v)
	}
}

func main() {
	items := []any{nil, 100, "hello", true, CustomPayload{EventID: "EV-999"}, 3.14}
	for _, it := range items {
		PrintTypeName(it)
	}
}""",
                "note": "Инспекция динамических типов"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Тип: nil (пустой интерфейс)
# Тип: int, значение = 100
# Тип: string, значение = "hello"
# Тип: bool, значение = true
# Тип: struct CustomPayload, EventID = EV-999
# Тип: float64 (нераспознанный)""",
                "note": "Результаты"
            }
        ],
        "under_the_hood": """
При боксинге в `any` рантайм создает пару `(тип, значение)`. `Type Switch` сравнивает адрес дескриптора типа в $O(1)$.
""",
        "pitfalls": """
- Пропуск проверки `nil`: если значение интерфейса `nil`, `switch v := x.(type)` корректно попадет в `case nil:`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем разница между `interface{}` и `any` в Go?»
**Ответ:** `any` — это официальный встроенный Type Alias для `interface{}`, представленный в Go 1.18 вместе с дженериками для улучшения читаемости кода.
"""
    },
    {
        "num": 36,
        "title": "Инициализация переменной в заголовке switch (switch num := ...; num)",
        "task": "Switch с инициализацией: По аналогии с if, проинициализируй переменную прямо в конструкции switch (switch num := getNumber(); num { ... }).",
        "theory": """
Синтаксис: `switch init_stmt; value_expr { ... }`
- Переменная `num` создается непосредственно перед оценкой `switch`;
- Доступна во всех `case` и в блоке `default`;
- Не видна за пределами закрывающей фигурной скобки `}`.
""",
        "step_by_step": """
1. Создаем функцию `computeStatusCode() int`.
2. Пишем `switch code := computeStatusCode(); code`.
3. Обрабатываем HTTP статусы 200, 404, 500.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func fetchResponseStatus() int {
	return 404
}

func main() {
	// Инициализация переменной прямо в switch:
	switch status := fetchResponseStatus(); status {
	case 200, 201:
		fmt.Printf("HTTP %d: Успешный запрос (OK)\\n", status)
	case 400:
		fmt.Printf("HTTP %d: Неверный запрос клиента (Bad Request)\\n", status)
	case 404:
		fmt.Printf("HTTP %d: Ресурс не найден (Not Found)\\n", status)
	case 500, 502, 503:
		fmt.Printf("HTTP %d: Внутренняя ошибка сервера (Server Error)\\n", status)
	default:
		fmt.Printf("HTTP %d: Нестандартный код ответа\\n", status)
	}

	// status здесь недоступен
}""",
                "note": "Инициализация в заголовке switch"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# HTTP 404: Ресурс не найден (Not Found)""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Стековый слот выделяется для блока `SwitchStmt` и очищается при выходе.
""",
        "pitfalls": """
- Пропуск точки с запятой `;` при наличии инициализации.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как в одном `switch` инициализировать несколько переменных?»
**Ответ:** Через множественное присваивание: `switch a, b := getA(), getB(); a + b { case 10: ... }`.
"""
    },
    {
        "num": 37,
        "title": "Рефакторинг глубокой вложенности (Pyramid of Doom) через паттерн Guard Clauses",
        "task": "Напиши программу с вложенными if (3 уровня вложенности): проверка доступа к системе (активен ли пользователь, есть ли права админа, не истёк ли срок действия). Затем перепиши через guard clauses (ранние return) — сравни читаемость.",
        "theory": """
**Паттерн Guard Clauses (Защитные условия / Ранний возврат):**
- Инвертирует условия ошибок и возвращает управление немедленно (`if !isActive { return err }`);
- Устраняет антипаттерн «Пирамида вложенности / Arrow Anti-pattern»;
- Основной позитивный сценарий («Happy Path») выполняется на нулевом уровне отступа слева;
- Является главным стандартом чистоты кода в Go.
""",
        "step_by_step": """
1. Создаем структуру `UserSession`.
2. Пишем валидацию с глубокой вложенностью `if`.
3. Переписываем ту же валидацию через `Guard Clauses`.
4. Сравниваем читаемость.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"errors"
	"fmt"
	"time"
)

type UserSession struct {
	IsActive  bool
	IsAdmin   bool
	ExpiresAt time.Time
}

// ❌ Плохой стиль: Глубокая вложенность (Pyramid of Doom)
func ValidateAccessNested(s UserSession) (bool, error) {
	if s.IsActive {
		if s.IsAdmin {
			if time.Now().Before(s.ExpiresAt) {
				return true, nil
			} else {
				return false, errors.New("срок сессии истек")
			}
		} else {
			return false, errors.New("требуются права администратора")
		}
	} else {
		return false, errors.New("пользователь деактивирован")
	}
}

// ✅ Идеальный идиоматичный Go: Guard Clauses (Плоский код)
func ValidateAccessGuard(s UserSession) (bool, error) {
	if !s.IsActive {
		return false, errors.New("пользователь деактивирован")
	}
	if !s.IsAdmin {
		return false, errors.New("требуются права администратора")
	}
	if time.Now().After(s.ExpiresAt) {
		return false, errors.New("срок сессии истек")
	}

	// Happy Path на верхнем уровне:
	return true, nil
}

func main() {
	validSession := UserSession{
		IsActive:  true,
		IsAdmin:   true,
		ExpiresAt: time.Now().Add(1 * time.Hour),
	}

	ok, err := ValidateAccessGuard(validSession)
	fmt.Printf("Доступ разрешен: %t, ошибка: %v\\n", ok, err)
}""",
                "note": "Guard Clauses vs Вложенные if"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Доступ разрешен: true, ошибка: <nil>""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Guard Clauses упрощают граф потока управления (CFG - Control Flow Graph), облегчая компилятору оптимизацию регистров и предсказание ветвлений.
""",
        "pitfalls": """
- Написание длинных веток `else` после `return`: если ветка завершается через `return`, блок `else` писать категорически не следует.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в BigTech код-ревью заставляют убирать `else` после `return`?»
**Ответ:** Это правило `Line of Sight` (Прямая линия видимости): счастливый путь выполнения должен идти прямо по левому краю функции без визуальных ступенек.
"""
    },
    {
        "num": 38,
        "title": "Досрочное прерывание выполнения ветки case с помощью оператора break",
        "task": "Принудительный выход из switch: Напишите switch, проверяющий тип операции (например, строка \"sum\"). Внутри одной из веток case добавьте условие: если дополнительный параметр равен нулю, прервать выполнение этой ветки досрочно с помощью break, не выполняя оставшуюся часть кода в этом case.",
        "theory": """
Оператор `break` внутри `case`:
- Немедленно прерывает выполнение текущей ветки `case`;
- Передает управление за пределы блока `switch`;
- Позволяет защититься от выполнения тяжелой постобработки при особых граничных условиях.
""",
        "step_by_step": """
1. Пишем функцию `ProcessOperation(op string, val int)`.
2. Внутри `case "sum":` проверяем `if val == 0 { break }`.
3. Убеждаемся, что код после `break` пропускается.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func ProcessOperation(op string, val int) {
	fmt.Printf("Операция '%s' с val = %d: ", op, val)

	switch op {
	case "sum":
		if val == 0 {
			fmt.Println("параметр 0 -> досрочный выход через break")
			break // Немедленно выходим из всего switch!
		}
		// Тяжелая операция выполняется только если val != 0:
		fmt.Printf("успешно вычислено sum = %d\\n", val*10)
	case "multiply":
		fmt.Printf("вычислено multiply = %d\\n", val*val)
	}
}

func main() {
	ProcessOperation("sum", 0)
	ProcessOperation("sum", 5)
	ProcessOperation("multiply", 4)
}""",
                "note": "Досрочный выход через break"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Операция 'sum' с val = 0: параметр 0 -> досрочный выход через break
# Операция 'sum' с val = 5: успешно вычислено sum = 50
# Операция 'multiply' с val = 4: вычислено multiply = 16""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Оператор `break` компилируется в безусловный переход `JMP` на метку сразу после закрывающей скобки `switch`.
""",
        "pitfalls": """
- Использование `break` внутри `switch`, находящегося внутри цикла `for`: простой `break` выйдет только из `switch`, но **не выйдет из цикла `for`**! Для выхода из цикла требуется именованная метка (`break Label`).
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как из `switch` выйти из внешнего цикла `for`?»
**Ответ:** Объявить метку перед циклом: `Loop: for { switch { case ...: break Loop } }`.
"""
    },
    {
        "num": 39,
        "title": "Золотой стандарт Go: инверсия условий и плоский стиль Guard Clauses",
        "task": "Паттерн \"Guard Clauses\" (Ранний возврат): Напиши функцию с глубокой вложенностью (if a { if b { if c { return true } } }). Перепиши её в \"плоском\" стиле, инвертируя условия и используя return для раннего выхода (if !a { return false }). Это золотой стандарт чистого кода в Go.",
        "theory": """
Инверсия условий:
- Было: `if condition { do_logic() }`
- Стало: `if !condition { return } do_logic()`
- Делает код линейным и понятным с первого взгляда.
""",
        "step_by_step": """
1. Пишем функцию валидации транзакции.
2. Проверяем баланс, лимиты и статус карты.
3. Оформляем в виде последовательных Guard Clauses.
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

type Account struct {
	Balance   int
	IsBlocked bool
	DailyUsed int
	DailyMax  int
}

func ProcessPayment(acc Account, amount int) error {
	// Guard 1: Проверка блокировки
	if acc.IsBlocked {
		return errors.New("карта заблокирована банком")
	}

	// Guard 2: Проверка суммы
	if amount <= 0 {
		return errors.New("некорректная сумма списания")
	}

	// Guard 3: Проверка баланса
	if acc.Balance < amount {
		return errors.New("недостаточно средств на счете")
	}

	// Guard 4: Проверка суточного лимита
	if acc.DailyUsed+amount > acc.DailyMax {
		return errors.New("превышен суточный лимит операций")
	}

	// Успешное выполнение:
	fmt.Printf("✔ Успешное списание %d руб. Новый баланс: %d руб.\\n",
		amount, acc.Balance-amount)
	return nil
}

func main() {
	acc := Account{Balance: 15000, IsBlocked: false, DailyUsed: 2000, DailyMax: 10000}

	err := ProcessPayment(acc, 5000)
	if err != nil {
		fmt.Println("Ошибка платежа:", err)
	}
}""",
                "note": "Линейная валидация платежа"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# ✔ Успешное списание 5000 руб. Новый баланс: 10000 руб.""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Каждый ранний возврат освобождает регистры и уменьшает время удержания блокировок.
""",
        "pitfalls": """
- Пропуск одного из граничных условий в цепочке.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какое правило форматирования функций пропагандирует официальный гайд Google Go Style Guide?»
**Ответ:** Минимизация отступов (Minimize Nesting) и обязательное выделение ошибок в ранние возвраты (Handle Errors First).
"""
    },
    {
        "num": 40,
        "title": "Диспетчеризация состояний заказа по iota-константам в switch",
        "task": "Напиши программу с switch по константам iota. Создай перечисление StatusPending, StatusProcessing, StatusShipped, StatusDelivered. Функция ProcessOrder(status int) выводит разные сообщения в зависимости от статуса.",
        "theory": """
Использование строго типизированных перечислений на `iota` в `switch` — классический паттерн стейт-машин в Go.
""",
        "step_by_step": """
1. Создаем тип `type OrderStatus int`.
2. Объявляем константы `StatusPending`, `StatusProcessing`, `StatusShipped`, `StatusDelivered`.
3. Реализуем обработчик `ProcessOrder(s OrderStatus)`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

type OrderStatus int

const (
	StatusPending OrderStatus = iota
	StatusProcessing
	StatusShipped
	StatusDelivered
	StatusCancelled
)

func ProcessOrder(status OrderStatus) {
	switch status {
	case StatusPending:
		fmt.Println("⏳ Заказ ожидает подтверждения оплаты")
	case StatusProcessing:
		fmt.Println("📦 Заказ комплектуется на складе")
	case StatusShipped:
		fmt.Println("🚚 Заказ передан курьерской службе")
	case StatusDelivered:
		fmt.Println("✅ Заказ успешно вручен клиенту")
	case StatusCancelled:
		fmt.Println("❌ Заказ аннулирован")
	default:
		fmt.Printf("⚠️ Неизвестный статус заказа: %d\\n", status)
	}
}

func main() {
	ProcessOrder(StatusPending)
	ProcessOrder(StatusShipped)
	ProcessOrder(StatusDelivered)
}""",
                "note": "Обработка iota-статусов"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# ⏳ Заказ ожидает подтверждения оплаты
# 🚚 Заказ передан курьерской службе
# ✅ Заказ успешно вручен клиенту""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Так как значения констант плотные (0, 1, 2, 3, 4), компилятор преобразует `switch` в Jump Table $O(1)$.
""",
        "pitfalls": """
- Использование сырого `int` вместо определенного типа `OrderStatus` в сигнатуре функции.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как компилятор Go защищает от пропуска констант в switch?»
**Ответ:** В связке с линтером `exhaustive` компилятор проверяет, что все константы enum обработаны в `switch`.
"""
    },
    {
        "num": 41,
        "title": "Сложное логическое условие и доказательство эффекта Short-Circuit Evaluation",
        "task": "Напиши программу с сложным логическим условием: проверка допуска на мероприятие. Условие: (возраст >= 18 || есть_сопровождение) && есть_билет && !в_чёрном_списке. Покажи short-circuit evaluation: создай функции-предикаты с fmt.Println внутри и убедись, что при false в левой части && правая часть не вычисляется.",
        "theory": """
**Короткое замыкание (Short-Circuit Evaluation):**
- Для `A && B`: если `A == false`, выражение `B` **никогда не вычисляется** (результат уже гарантированно `false`);
- Для `A || B`: если `A == true`, выражение `B` **никогда не вычисляется** (результат уже гарантированно `true`);
- Это предотвращает лишние тяжелые вызовы к базам данных и защищает от разыменования `nil` (`ptr != nil && ptr.Value > 0`).
""",
        "step_by_step": """
1. Создаем логирующие функции-предикаты `hasTicket()`, `isBlacklisted()`, `checkAge()`.
2. Составляем сложное логическое условие.
3. Анализируем логи консоли, доказывающие пропуск вызовов.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func checkAge(age int) bool {
	fmt.Printf("   [Call] checkAge(%d)\\n", age)
	return age >= 18
}

func hasGuardian(has bool) bool {
	fmt.Printf("   [Call] hasGuardian(%t)\\n", has)
	return has
}

func hasTicket(has bool) bool {
	fmt.Printf("   [Call] hasTicket(%t)\\n", has)
	return has
}

func isBlacklisted(blacklisted bool) bool {
	fmt.Printf("   [Call] isBlacklisted(%t)\\n", blacklisted)
	return blacklisted
}

func main() {
	fmt.Println("--- ТЕСТ 1: Взрослый с билетом не в черном списке ---")
	// Возраст >= 18 -> true (hasGuardian не вызывается!)
	if (checkAge(20) || hasGuardian(false)) && hasTicket(true) && !isBlacklisted(false) {
		fmt.Println("✔ Допуск разрешен!")
	}

	fmt.Println("\\n--- ТЕСТ 2: Ребенок без билета (short-circuit на билете) ---")
	// hasTicket вернет false -> isBlacklisted даже не будет вызван!
	if (checkAge(15) || hasGuardian(true)) && hasTicket(false) && !isBlacklisted(false) {
		fmt.Println("✔ Допуск разрешен!")
	} else {
		fmt.Println("❌ Допуск запрещен (isBlacklisted не вызывался)!")
	}
}""",
                "note": "Доказательство Short-Circuit Evaluation"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# --- ТЕСТ 1: Взрослый с билетом не в черном списке ---
#    [Call] checkAge(20)
#    [Call] hasTicket(true)
#    [Call] isBlacklisted(false)
# ✔ Допуск разрешен!
# 
# --- ТЕСТ 2: Ребенок без билета (short-circuit на билете) ---
#    [Call] checkAge(15)
#    [Call] hasGuardian(true)
#    [Call] hasTicket(false)
# ❌ Допуск запрещен (isBlacklisted не вызывался)!""",
                "note": "Результат трассировки предикатов"
            }
        ],
        "under_the_hood": """
Компилятор транслирует `&&` и `||` в ветвления с переходами `JZ` / `JNZ` сразу к следующей секции или ветке выхода.
""",
        "pitfalls": """
- Помещение функций с побочными эффектами (например `saveToDB()`) в правую часть `&&`: если левая часть `false`, функция записи никогда не выполнится.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему проверка `if user != nil && user.IsActive` безопасна в Go и не вызывает panic?»
**Ответ:** Благодаря Short-circuit evaluation: если `user == nil` истинно (левая часть `false`), правая часть `user.IsActive` не вычисляется, и разыменования `nil` не происходит.
"""
    },
    {
        "num": 42,
        "title": "Функция CheckType(v any) с определением строки, числа и флага",
        "task": "Type switch (переключатель типов): Напиши функцию CheckType(v interface{}). Внутри напиши switch val := v.(type) { ... }, которая проверяет, является ли v строкой, int или bool, и выводит соответствующее сообщение.",
        "theory": """
Стандартный переключатель типов для сериализаторов и универсальных валидаторов.
""",
        "step_by_step": """
1. Реализуем функцию `CheckType(v any)`.
2. Обрабатываем `string`, `int`, `bool` и `default`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func CheckType(v any) {
	switch val := v.(type) {
	case string:
		fmt.Printf("Строковый тип: %q (длина: %d)\\n", val, len(val))
	case int:
		fmt.Printf("Целочисленный тип: %d (квадрат: %d)\\n", val, val*val)
	case bool:
		fmt.Printf("Булев тип: %t\\n", val)
	default:
		fmt.Printf("Неподдерживаемый тип: %T\\n", val)
	}
}

func main() {
	CheckType("Golang")
	CheckType(12)
	CheckType(false)
	CheckType(5.5)
}""",
                "note": "Функция CheckType"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Строковый тип: "Golang" (длина: 6)
# Целочисленный тип: 12 (квадрат: 144)
# Булев тип: false
# Неподдерживаемый тип: float64""",
                "note": "Результаты"
            }
        ],
        "under_the_hood": """
Диспетчеризация типов выполняется через сравнение указателей метаданных типов `runtime.type`.
""",
        "pitfalls": """
- Забыть, что `int` и `int64` — это разные типы для `type switch`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как обработать несколько типов в одном `case` в Type Switch?»
**Ответ:** `case int, int32, int64:`. В этом случае внутри блока переменная будет иметь тип `any`.
"""
    },
    {
        "num": 43,
        "title": "Инициализация переменной внутри switch и проверка недоступности снаружи",
        "task": "Инициализация внутри switch: Объявите и инициализируйте переменную прямо в строке объявления switch (например, switch age := getAge(); { case age < 18: ... }). Убедитесь, что переменная age недоступна за пределами блока switch.",
        "theory": """
Синтаксис `switch var := expr; { ... }`:
- Позволяет изолировать временную переменную;
- Исключает загрязнение внешней области видимости функции.
""",
        "step_by_step": """
1. Создаем функцию `getAge() int`.
2. Пишем `switch age := getAge(); { case age < 18: ... }`.
3. Показываем невозможность обращения к `age` после `switch`.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func getAge() int {
	return 17
}

func main() {
	switch age := getAge(); {
	case age < 18:
		fmt.Printf("Возраст %d: Несовершеннолетний (доступ ограничен)\\n", age)
	default:
		fmt.Printf("Возраст %d: Совершеннолетний\\n", age)
	}

	// fmt.Println(age) // ОШИБКА КОМПИЛЯЦИИ: undefined: age
}""",
                "note": "Инициализация в tagless switch"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Возраст 17: Несовершеннолетний (доступ ограничен)""",
                "note": "Вывод"
            }
        ],
        "under_the_hood": """
Scope закрывается компилятором после обработки `SwitchStmt`.
""",
        "pitfalls": """
- Забыть точку с запятой `;` между инициализацией и телом switch.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «В чем отличие `switch x := f(); x { ... }` от `switch x := f(); { ... }`?»
**Ответ:** В первом случае происходит сопоставление равенства со значением `x` (`case 1:`). Во втором случае это Tagless Switch, где в `case` пишутся булевы условия (`case x < 10:`).
"""
    },
    {
        "num": 44,
        "title": "Классическая задача FizzBuzz: реализация через if/else и через switch",
        "task": "FizzBuzz: Классика. Выведите числа от 1 до 100. Если делится на 3 — \"Fizz\", на 5 — \"Buzz\", на оба — \"FizzBuzz\". Решите через switch и через if/else.",
        "theory": """
**FizzBuzz:**
- Кратность 3 и 5 ($15$) $\rightarrow$ `"FizzBuzz"`
- Кратность 3 $\rightarrow$ `"Fizz"`
- Кратность 5 $\rightarrow$ `"Buzz"`
- Иначе $\rightarrow$ само число
""",
        "step_by_step": """
1. Решаем через `if-else`.
2. Решаем через `switch true`.
3. Сравниваем элегантность решения.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

// Вариант 1: Через switch true (Наиболее чистый и читаемый)
func FizzBuzzSwitch(n int) string {
	switch {
	case n%15 == 0:
		return "FizzBuzz"
	case n%3 == 0:
		return "Fizz"
	case n%5 == 0:
		return "Buzz"
	default:
		return fmt.Sprintf("%d", n)
	}
}

func main() {
	fmt.Println("Первые 16 чисел FizzBuzz:")
	for i := 1; i <= 16; i++ {
		fmt.Printf("%s ", FizzBuzzSwitch(i))
	}
	fmt.Println()
}""",
                "note": "FizzBuzz через switch"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Первые 16 чисел FizzBuzz:
# 1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz 16""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
Проверка `n % 15 == 0` первой исключает ложные срабатывания отдельных условий `n % 3` и `n % 5`.
""",
        "pitfalls": """
- Проверка `n % 3` раньше `n % 15`: число 15 выведет `"Fizz"` вместо `"FizzBuzz"`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как решить FizzBuzz без деления на 15?»
**Ответ:** Конкатенацией строк: формировать буфер, добавляя `"Fizz"` при `n % 3 == 0` и `"Buzz"` при `n % 5 == 0`.
"""
    },
    {
        "num": 45,
        "title": "Цикл for в роли while (for condition) с валидацией пароля",
        "task": "for без постусловия: (как while): запрашивайте у пользователя пароль до тех пор, пока он не введёт \"secret\".",
        "theory": """
**В Go нет ключевого слова `while`:**
Конструкция `for condition { ... }` полностью заменяет классический цикл `while`:
- Тело цикла повторяется, пока условие истинно (`password != "secret"`).
""",
        "step_by_step": """
1. Инициализируем `var pass string`.
2. Запускаем `for pass != "secret" { ... }`.
3. При совпадении выходим из цикла.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import "fmt"

func main() {
	passwords := []string{"123456", "admin", "secret"}
	idx := 0
	var input string

	// for в роли while
	for input != "secret" && idx < len(passwords) {
		input = passwords[idx]
		fmt.Printf("Попытка ввода пароля: %q -> ", input)
		if input == "secret" {
			fmt.Println("✔ Доступ разрешен!")
		} else {
			fmt.Println("❌ Неверный пароль. Повторите ввод.")
		}
		idx++
	}
}""",
                "note": "for в роли while"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Попытка ввода пароля: "123456" -> ❌ Неверный пароль. Повторите ввод.
# Попытка ввода пароля: "admin" -> ❌ Неверный пароль. Повторите ввод.
# Попытка ввода пароля: "secret" -> ✔ Доступ разрешен!""",
                "note": "Результат работы"
            }
        ],
        "under_the_hood": """
Компилятор генерирует цикл с проверкой условия перед итерацией `CMP + JNE`.
""",
        "pitfalls": """
- Риск создания бесконечного цикла, если условие выхода никогда не станет `false`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему создатели Go объединили `for`, `while` и `do-while` в одно ключевое слово `for`?»
**Ответ:** Для ортогональности и минимализма языка: одна языковая конструкция `for` решает все задачи циклов (счетчики, предикаты, бесконечные циклы, итераторы `range`).
"""
    },
    {
        "num": 46,
        "title": "Многоуровневая валидация сложности пароля с помощью Guard Clauses",
        "task": "Напиши программу с guard clause для валидации пароля: функция ValidatePassword(p string) error проверяет длину (≥8), наличие цифры, заглавной буквы и спецсимвола. Каждая проверка — отдельный if с return fmt.Errorf(...). В конце return nil.",
        "theory": """
Эталонная валидация безопасности:
1. Длина $\ge 8$;
2. Наличие цифры `unicode.IsDigit`;
3. Наличие заглавной буквы `unicode.IsUpper`;
4. Наличие спецсимвола `unicode.IsPunct` / `unicode.IsSymbol`.
""",
        "step_by_step": """
1. Пишем вспомогательные сканеры символов.
2. Оформляем `ValidatePassword(p string) error` серией защитных условий.
3. Тестируем различные пароли.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"errors"
	"fmt"
	"unicode"
	"unicode/utf8"
)

func ValidatePassword(p string) error {
	// Guard 1: Минимальная длина
	if utf8.RuneCountInString(p) < 8 {
		return errors.New("пароль должен содержать минимум 8 символов")
	}

	var hasDigit, hasUpper, hasSpecial bool
	for _, r := range p {
		switch {
		case unicode.IsDigit(r):
			hasDigit = true
		case unicode.IsUpper(r):
			hasUpper = true
		case unicode.IsPunct(r) || unicode.IsSymbol(r):
			hasSpecial = true
		}
	}

	// Guard 2: Цифра
	if !hasDigit {
		return errors.New("пароль должен содержать хотя бы одну цифру (0-9)")
	}

	// Guard 3: Заглавная буква
	if !hasUpper {
		return errors.New("пароль должен содержать хотя бы одну заглавную букву (A-Z, А-Я)")
	}

	// Guard 4: Спецсимвол
	if !hasSpecial {
		return errors.New("пароль должен содержать хотя бы один специальный символ (!@#$%^&*)")
	}

	return nil
}

func main() {
	passwords := []string{"short", "nocaps123!", "NOLOWER123!", "ValidPass2026!"}

	for _, pass := range passwords {
		err := ValidatePassword(pass)
		if err != nil {
			fmt.Printf("Пароль '%s': ❌ %v\\n", pass, err)
		} else {
			fmt.Printf("Пароль '%s': ✔ Надежный пароль!\\n", pass)
		}
	}
}""",
                "note": "Валидация пароля через Guard Clauses"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Пароль 'short': ❌ пароль должен содержать минимум 8 символов
# Пароль 'nocaps123!': ❌ пароль должен содержать хотя бы одну заглавную букву (A-Z, А-Я)
# Пароль 'NOLOWER123!': ✔ Надежный пароль!
# Пароль 'ValidPass2026!': ✔ Надежный пароль!""",
                "note": "Результаты валидации"
            }
        ],
        "under_the_hood": """
Пакет `unicode` использует сжатые таблицы диапазонов Unicode для $O(1)$ классификации рун.
""",
        "pitfalls": """
- Использование `len(p)` для проверки длины паролей с нелатинскими символами.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Почему в Enterprise-микросервисах предпочитают `errors.New` вместо создания кастомных типов ошибок для простых текстовых сообщений?»
**Ответ:** Статические ошибки `var ErrTooShort = errors.New(...)` выделяются один раз в памяти и позволяют быстро выполнять проверку через `errors.Is`.
"""
    },
    {
        "num": 47,
        "title": "Поиск экстремумов (Min и Max) в срезе чисел через цикл и if",
        "task": "Поиск максимума и минимума: Пройдитесь по слайсу чисел и найдите самое большое и самое маленькое значение, не используя встроенные функции, а только for и if.",
        "theory": """
Алгоритм линейного поиска экстремумов за $O(N)$:
1. Инициализируем `minVal` и `maxVal` первым элементом среза `slice[0]`;
2. В цикле обновляем значения при `val < minVal` или `val > maxVal`.
""",
        "step_by_step": """
1. Проверяем граничный случай пустого среза.
2. Проходим срез в цикле.
3. Возвращаем минимум и максимум.
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

func FindMinMax(numbers []int) (int, int, error) {
	if len(numbers) == 0 {
		return 0, 0, errors.New("срез пуст")
	}

	minVal := numbers[0]
	maxVal := numbers[0]

	for _, v := range numbers[1:] {
		if v < minVal {
			minVal = v
		}
		if v > maxVal {
			maxVal = v
		}
	}

	return minVal, maxVal, nil
}

func main() {
	nums := []int{24, -5, 108, 0, -42, 87}

	minVal, maxVal, err := FindMinMax(nums)
	if err != nil {
		fmt.Println("Ошибка:", err)
		return
	}

	fmt.Printf("Исходный срез: %v\\n", nums)
	fmt.Printf("Минимум:       %d\\n", minVal)
	fmt.Printf("Максимум:      %d\\n", maxVal)
}""",
                "note": "Поиск Min и Max"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# Исходный срез: [24 -5 108 0 -42 87]
# Минимум:       -42
# Максимум:      108""",
                "note": "Результат"
            }
        ],
        "under_the_hood": """
При итерации компилятор устраняет проверку границ среза (Bounds Check Elimination - BCE), так как диапазон цикла строго ограничен `len(numbers)`.
""",
        "pitfalls": """
- Инициализация `minVal = 0`: если все числа в срезе положительные (например `[10, 20, 30]`), минимум ошибочно останется равным 0. Всегда инициализируйте первым элементом `slice[0]`.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Какова сложность поиска минимума и максимума одновременно и можно ли уменьшить число сравнений?»
**Ответ:** Стандартный алгоритм делает $2N$ сравнений. Алгоритм парного сравнения (Pairwise comparison) делает $\approx 1.5N$ сравнений, сравнивая элементы парами.
"""
    },
    {
        "num": 48,
        "title": "Логирование эффекта Short-Circuit при цепочке из трех булевых предикатов",
        "task": "Сложное условие с булевыми функциями: Напиши 3 функции, возвращающие bool (например, проверяющие строку на длину, на наличие цифр и на наличие заглавных букв). Сделай if, вызывающий их через &&. Добавь в функции вывод логов и посмотри на эффект \"короткого замыкания\" (short-circuit evaluation), когда при false первой функции остальные даже не вызываются.",
        "theory": """
Визуализация оптимизации вычислений:
- Вызовы функций в условиях выполняются строго слева направо;
- При первом `false` выполнение немедленно прерывается.
""",
        "step_by_step": """
1. Пишем функции `checkLen`, `checkDigits`, `checkCaps`.
2. Тестируем строку, проваливающую первую же проверку.
3. Наблюдаем отсутствие логов от последующих функций.
""",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": """package main

import (
	"fmt"
	"strings"
	"unicode/utf8"
)

func checkLength(s string) bool {
	fmt.Println("  [1] Вызов checkLength...")
	return utf8.RuneCountInString(s) >= 8
}

func checkDigits(s string) bool {
	fmt.Println("  [2] Вызов checkDigits...")
	return strings.ContainsAny(s, "0123456789")
}

func checkCaps(s string) bool {
	fmt.Println("  [3] Вызов checkCaps...")
	return strings.ToUpper(s) != strings.ToLower(s)
}

func main() {
	fmt.Println("--- ТЕСТ: Короткая строка 'abc' ---")
	// Длина < 8 (checkDigits и checkCaps НЕ будут вызваны вообще!)
	if checkLength("abc") && checkDigits("abc") && checkCaps("abc") {
		fmt.Println("✔ Все проверки пройдены")
	} else {
		fmt.Println("❌ Валидация прервана на первой ошибке!")
	}
}""",
                "note": "Логирование Short-Circuit"
            },
            {
                "filename": "Терминал",
                "lang": "bash",
                "code": """go run main.go
# --- ТЕСТ: Короткая строка 'abc' ---
#   [1] Вызов checkLength...
# ❌ Валидация прервана на первой ошибке!""",
                "note": "Вызовы [2] и [3] не произошли"
            }
        ],
        "under_the_hood": """
Инструкции вызова функций `CALL` размещаются после условных джампов `TEST + JZ`.
""",
        "pitfalls": """
- Надежда на то, что функции в условиях выполнятся обязательно.
""",
        "bigtech_interview": """
**Вопрос с собеседования:** «Как гарантировать вызов всех трех функций, если их побочные эффекты обязательны?»
**Ответ:** Вычислить их заранее в отдельные переменные: `ok1 := checkLength(s); ok2 := checkDigits(s); ok3 := checkCaps(s); if ok1 && ok2 && ok3 { ... }`.
"""
    }
]

if __name__ == '__main__':
    print(f"Loaded Part 3: {len(exercises)} exercises.")
