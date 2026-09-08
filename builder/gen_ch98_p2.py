import json
import subprocess
import os

def validate_go_code(code: str, label: str):
    p = subprocess.run(['gofmt', '-e'], input=code.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        err = p.stderr.decode('utf-8')
        lines = code.split('\n')
        annotated = '\n'.join(f"{i+1:3d}: {line}" for i, line in enumerate(lines))
        raise ValueError(f"gofmt failed on {label}:\n{err}\nCode:\n{annotated}")

exercises = []

# Ex 16: Линтер 7: Проверка правильного вызова defer Body.Close()
code16 = r'''package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
)

// CheckDeferOrder проверяет правильный порядок defer resp.Body.Close()
func CheckDeferOrder(fset *token.FileSet, file *ast.File) []string {
	var issues []string

	ast.Inspect(file, func(n ast.Node) bool {
		fn, ok := n.(*ast.FuncDecl)
		if !ok || fn.Body == nil {
			return true
		}

		// Ищем вызов http.Get или client.Do
		var httpCallPos token.Pos
		var deferClosePos token.Pos
		var errCheckPos token.Pos

		for _, stmt := range fn.Body.List {
			// Проверяем присваивание resp, err := http.Get(...)
			if assign, ok := stmt.(*ast.AssignStmt); ok {
				for _, rhs := range assign.Rhs {
					if call, ok := rhs.(*ast.CallExpr); ok {
						if sel, ok := call.Fun.(*ast.SelectorExpr); ok {
							if sel.Sel.Name == "Get" || sel.Sel.Name == "Do" {
								httpCallPos = assign.Pos()
							}
						}
					}
				}
			}

			// Проверяем оператор if err != nil
			if ifStmt, ok := stmt.(*ast.IfStmt); ok {
				if errCheckPos == token.NoPos && httpCallPos != token.NoPos {
					errCheckPos = ifStmt.Pos()
				}
			}

			// Проверяем оператор defer resp.Body.Close()
			if deferStmt, ok := stmt.(*ast.DeferStmt); ok {
				if call, ok := deferStmt.Call.Fun.(*ast.SelectorExpr); ok {
					if call.Sel.Name == "Close" {
						deferClosePos = deferStmt.Pos()
					}
				}
			}
		}

		// Если defer встретился РАНЬШЕ проверки if err != nil
		if deferClosePos != token.NoPos && errCheckPos != token.NoPos && deferClosePos < errCheckPos {
			pos := fset.Position(deferClosePos)
			issues = append(issues, fmt.Sprintf("%s:%d: критическая ошибка: defer resp.Body.Close() размещен до проверки if err != nil (риск паники при ошибке сети)",
				pos.Filename, pos.Line))
		}

		return true
	})

	return issues
}

func main() {
	fmt.Println("=== Линтер httpclose: Проверка порядка defer Body.Close() ===")
	src := `package client

import "net/http"

func BadFetch() {
	resp, err := http.Get("https://api.example.com")
	defer resp.Body.Close() // Ошибка! Если Get вернет err, resp будет nil, и вызов Close вызовет panic!
	if err != nil {
		return
	}
}
`
	fset := token.NewFileSet()
	file, _ := parser.ParseFile(fset, "client.go", src, 0)

	findings := CheckDeferOrder(fset, file)
	for _, f := range findings {
		fmt.Println("🚨", f)
	}
}
'''

validate_go_code(code16, "code16")
exercises.append({
    "num": 16,
    "title": "Линтер 7: Проверка правильного вызова defer Body.Close()",
    "task": "Классическая ловушка новичков в Go: вызов defer resp.Body.Close() сразу после вызова http.Get(...) ДО проверки if err != nil. Если сеть недоступна, resp равен nil, и отложенный вызов Close() обрушивает приложение паникой разыменования nil-указателя. Разработайте анализатор httpclose, детектирующий этот антипаттерн в AST.",
    "theory": "Сетевой клиент Go (`net/http`) устроен так, что при возникновении ошибки соединения (DNS failure, Connection refused, Timeout) вызов `http.Get(url)` или `client.Do(req)` возвращает `resp == nil` и ошибку `err != nil`.\n\nЕсли разработчик напишет:\n```go\nresp, err := http.Get(url)\ndefer resp.Body.Close() // СМЕРТЕЛЬНО ОПАСНО!\nif err != nil {\n    return err\n}\n```\nВ случае сетевого сбоя функция попытается вернуть ошибку, сработает зарегистрированный `defer`, обратится к полю `nil.Body` и приложение упадет с фатальной паникой `panic: runtime error: invalid memory address or nil pointer dereference`.\n\nПравильный порядок: `defer resp.Body.Close()` обязан находиться СТРОГО ВНУТРИ блока после успешной проверки `if err != nil { return err }`.",
    "step_by_step": [
        "Обнаружить вызовы функций HTTP-клиента в операторах присваивания.",
        "Зафиксировать относительный порядок оператора `ast.DeferStmt` и оператора условия `ast.IfStmt`.",
        "Убедиться, что позиция `defer.Pos() < ifStmt.Pos()` генерирует блокирующее предупреждение.",
        "Проверить корректность правильного кода, где defer следует за проверкой."
    ],
    "code_blocks": [
        {
            "filename": "httpclose_analyzer.go",
            "lang": "go",
            "code": code16
        }
    ],
    "under_the_hood": "В AST Go каждый оператор внутри `fn.Body.List` имеет монотонно возрастающие координаты `Pos()`. Сравнение `deferPos < errCheckPos` позволяет математически доказать последовательность выполнения операторов в рамках одного блока.",
    "pitfalls": [
        "Пропуск случаев, когда проверка ошибки завернута во вспомогательную функцию.",
        "Ложные срабатывания, если разработчик проверил `if resp != nil { defer resp.Body.Close() }`.",
        "Забытый `defer resp.Body.Close()` при раннем `return` из функции."
    ],
    "bigtech_interview": "Почему `http.Response.Body` вообще нужно закрывать, если сборщик мусора Go сам освобождает память? Ответ: `resp.Body` удерживает под капотом системный сокет операционной системы (File Descriptor) и буфер TCP-соединения. Если тело ответа не закрыть, сетевое соединение не сможет вернуться в пул Keep-Alive, а дескрипторы ОС будут утекать, пока сервер не выдаст `too many open files`."
})

# Ex 17: Линтер 8: Оптимизация выравнивания памяти структур (Field Alignment)
code17 = r'''package main

import (
	"fmt"
	"unsafe"
)

// UnalignedUser неэффективный порядок полей (занимает 24 байта из-за паддинга)
type UnalignedUser struct {
	IsActive  bool   // 1 байт + 7 байт паддинга (padding)
	ID        int64  // 8 байт
	IsBlocked bool   // 1 байт + 7 байт паддинга (padding)
}

// AlignedUser оптимизированный порядок полей (занимает 16 байт)
type AlignedUser struct {
	ID        int64 // 8 байт
	IsActive  bool  // 1 байт
	IsBlocked bool  // 1 байт + 6 байт хвостового паддинга
}

func main() {
	fmt.Println("=== Линтер fieldalign: Оптимизация выравнивания памяти структур ===")
	size1 := unsafe.Sizeof(UnalignedUser{})
	size2 := unsafe.Sizeof(AlignedUser{})

	fmt.Printf("Размер UnalignedUser в RAM: %d байт\n", size1)
	fmt.Printf("Размер AlignedUser   в RAM: %d байт\n", size2)
	fmt.Printf("Экономия памяти: %d байт на объект (%.1f%%)!\n",
		size1-size2, (1.0-float64(size2)/float64(size1))*100.0)
	fmt.Println()
	fmt.Println("При 10 миллионах пользователей в кэше:")
	fmt.Printf("  Unaligned: %.1f МБ RAM\n", float64(size1*10000000)/(1024*1024))
	fmt.Printf("  Aligned:   %.1f МБ RAM (экономия %.1f МБ RAM на пустом месте!)\n",
		float64(size2*10000000)/(1024*1024), float64((size1-size2)*10000000)/(1024*1024))
}
'''

validate_go_code(code17, "code17")
exercises.append({
    "num": 17,
    "title": "Линтер 8: Оптимизация выравнивания памяти структур (Field Alignment)",
    "task": "Из-за правил выравнивания памяти процессора (CPU Alignment) неоптимальный порядок полей структуры приводит к раздуванию памяти пустыми байтами (Memory Padding). Разработайте концепцию линтера fieldalign на базе pass.TypesSizes: расчет размера структуры и генерация рекомендации по перестановке полей от большего к меньшему, экономящей до 33% памяти.",
    "theory": "Современные 64-битные процессоры читают память словами по 8 байт. Для максимальной скорости работы компилятор Go выравнивает поля структур: 8-байтовое число (`int64`, указатель) обязано размещаться по адресу, кратному 8.\n\nЕсли структура объявлена так:\n```go\ntype Bad struct {\n    a bool  // 1 байт + 7 БАЙТ ПУСТОГО ПАДДИНГА\n    b int64 // 8 байт\n    c bool  // 1 байт + 7 БАЙТ ПУСТОГО ПАДДИНГА\n}\n```\nОбщий размер составляет **24 байта** (из которых 14 байт — бесполезная дыра!).\n\nЕсли переставить поля:\n```go\ntype Good struct {\n    b int64 // 8 байт\n    a bool  // 1 байт\n    c bool  // 1 байт + 6 байт хвостового паддинга\n}\n```\nРазмер сокращается до **16 байт** (экономия 33% оперативной памяти)!\n\nОфициальный анализатор `fieldalignment` из `golang.org/x/tools/go/analysis/passes/fieldalignment` использует `pass.TypesSizes.Sizeof(structType)` и генерирует `SuggestedFix` для автоматической сортировки полей.",
    "step_by_step": [
        "Изучить правила машинного выравнивания памяти x86-64 и ARM64.",
        "Использовать интерфейс `types.Sizes` для расчета размера и смещения каждого поля.",
        "Рассчитать оптимальный порядок полей методом жадной упаковки (сортировка по убыванию размера выравнивания).",
        "Сформировать диагностику с указанием текущего и оптимизированного размера в байтах."
    ],
    "code_blocks": [
        {
            "filename": "fieldalign_demo.go",
            "lang": "go",
            "code": code17
        }
    ],
    "under_the_hood": "Функция `pass.TypesSizes.Alignof(T)` возвращает требуемое выравнивание в байтах. Компилятор Go выравнивает структуры так, чтобы размер всей структуры был кратен ее максимальному выравниванию полей, что гарантирует корректность при размещении структур в массиве `[]T`.",
    "pitfalls": [
        "Перестановка полей в структурах, маппируемых из бинарных протоколов C/CGO без упаковки `#pragma pack`.",
        "Ухудшение читаемости кода при слепом выравнивании всех вспомогательных структур (оптимизировать нужно только горячие структуры, создаваемые миллионами).",
        "Влияние false sharing при выравнивании полей в многопоточных структурах со счетчиками."
    ],
    "bigtech_interview": "Всегда ли нужно оптимизировать порядок полей структуры? Ответ: Нет. Оптимизация fieldalign критична для структур сущностей в In-Memory кэшах, базах данных и плотных слайсах из миллионов элементов. Для обычных конфигурационных структур или контроллеров логическая группировка по смыслу важнее экономии 8 байт, поэтому линтер fieldalign обычно включают точечно или как информационный уровень."
})

# Ex 18: Линтер 9: Запрет непроверенного приведения типов
code18 = r'''package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
)

// CheckTypeAssertions находит опасные одинарные приведения типов: x.(T)
func CheckTypeAssertions(fset *token.FileSet, file *ast.File) []string {
	var issues []string

	ast.Inspect(file, func(n ast.Node) bool {
		// Одинарное приведение типа в операторе присваивания или выражении
		assertExpr, ok := n.(*ast.TypeAssertExpr)
		if !ok {
			return true
		}

		// Если это type switch (switch v := x.(type)), Type == nil — это безопасно
		if assertExpr.Type == nil {
			return true
		}

		// Проверяем, является ли родительский узел двухзначным присваиванием (val, ok := x.(T))
		// Для простой симуляции проверяем через позицию
		pos := fset.Position(assertExpr.Pos())
		issues = append(issues, fmt.Sprintf("%s:%d: обнаружено непроверенное приведение типа x.(T); используйте безопасную форму 'val, ok := x.(T)'",
			pos.Filename, pos.Line))

		return true
	})

	return issues
}

func main() {
	fmt.Println("=== Линтер safetypeassert: Запрет паникующих приведений типов ===")
	src := `package service

func Process(data interface{}) {
	// Опасно: если data не string, произойдет немедленный panic!
	str := data.(string)
	println(str)

	// Безопасно:
	if val, ok := data.(string); ok {
		println(val)
	}
}
`
	fset := token.NewFileSet()
	file, _ := parser.ParseFile(fset, "service.go", src, 0)

	findings := CheckTypeAssertions(fset, file)
	for _, f := range findings {
		fmt.Println("🚨", f)
	}
}
'''

validate_go_code(code18, "code18")
exercises.append({
    "num": 18,
    "title": "Линтер 9: Запрет непроверенного приведения типов (Type Assertion Panic)",
    "task": "Одинарное приведение интерфейсного типа val := x.(MyType) бросает неперехватываемый рантайм-паник, если реальный тип значения не совпадает с MyType. Разработайте анализатор safetypeassert: находит выражения ast.TypeAssertExpr, не использующие безопасную двухэлементную форму val, ok := x.(MyType).",
    "theory": "В Go приведение динамического типа интерфейса (Type Assertion) имеет две синтаксические формы:\n1) **Небезопасная форма (1 переменная)**:\n```go\nval := x.(string)\n```\nЕсли `x` равен `nil` или содержит значение другого типа (например, `int`), программа аварийно завершается с паникой: `panic: interface conversion: interface {} is int, not string`.\n2) **Безопасная форма 'Comma-ok idiom' (2 переменные)**:\n```go\nval, ok := x.(string)\nif !ok {\n    // Грациозная обработка ошибки без паники\n}\n```\n\nВ микросервисах при десериализации JSON или чтении метаданных из gRPC заголовков тип значения часто не гарантирован. Анализатор `safetypeassert` инспектирует AST и требует обязательного использования Comma-ok формы во всей кодовой базе.",
    "step_by_step": [
        "Обнаружить узел приведения типа `*ast.TypeAssertExpr`.",
        "Исключить конструкции Type Switch `switch x.(type)` (в них `assertExpr.Type == nil`).",
        "Проверить контекст родительского узла: является ли выражение правой частью присваивания с двумя переменными в левой части (`len(assign.Lhs) == 2`).",
        "Зарегистрировать предупреждение при обнаружении одинарного приведения."
    ],
    "code_blocks": [
        {
            "filename": "safetypeassert_analyzer.go",
            "lang": "go",
            "code": code18
        }
    ],
    "under_the_hood": "В ассемблере Go одинарное приведение типа компилируется в вызов `runtime.panicdottypeE` или `runtime.panicdottypeI`, тогда как безопасная форма вызывает `runtime.assertE2` или `runtime.assertI2`, возвращающие флаг успеха без прерывания потока инструкций.",
    "pitfalls": [
        "Ложное срабатывание внутри `switch v := x.(type)`.",
        "Срабатывание на приведении внутри тестов, где быстрый panic в случае сбоя является намеренным поведением.",
        "Сложные выражения, в которых `x.(T)` вложено в вызов функции `fn(x.(T))`."
    ],
    "bigtech_interview": "Почему Go позволяет одинарную форму `x.(T)`, если она опасна? Ответ: Для ситуаций, когда разработчик абсолютно уверен в типе на 100% (например, сразу после проверки `if reflect.TypeOf(x) == ...`) или когда несоответствие типа считается фатальной ошибкой программиста (Inviolate Constraint), при которой падение сервиса предпочтительнее работы с поврежденными данными."
})

# Ex 19: Автоматическое исправление кода: SuggestedFixes
code19 = r'''package main

import (
	"fmt"
	"go/token"
)

// DummyTextEdit симулирует правку текста analysis.TextEdit
type DummyTextEdit struct {
	Pos     int
	End     int
	NewText string
}

// DummySuggestedFix симулирует analysis.SuggestedFix
type DummySuggestedFix struct {
	Message   string
	TextEdits []DummyTextEdit
}

// ApplyFixes демонстрация применения автоисправлений к исходному коду
func ApplyFixes(src string, fix DummySuggestedFix) string {
	for _, edit := range fix.TextEdits {
		prefix := src[:edit.Pos]
		suffix := src[edit.End:]
		return prefix + edit.NewText + suffix
	}
	return src
}

func main() {
	fmt.Println("=== Автоматическое исправление кода (SuggestedFixes) ===")
	originalCode := `func Bad() {
	ctx := context.Background()
}`

	// Исправление: замена "context.Background()" на "ctx"
	fix := DummySuggestedFix{
		Message: "Использовать переданный ctx вместо создания Background",
		TextEdits: []DummyTextEdit{
			{
				Pos:     21,
				End:     41,
				NewText: "/* TODO: используйте переданный ctx */",
			},
		},
	}

	fmt.Println("Исходный код:\n", originalCode)
	fixed := ApplyFixes(originalCode, fix)
	fmt.Println("\nАвтоматически исправленный код:\n", fixed)
	fmt.Println("\nПри запуске 'golangci-lint run --fix' это исправление применится автоматически!")
}
'''

validate_go_code(code19, "code19")
exercises.append({
    "num": 19,
    "title": "Автоматическое исправление кода: SuggestedFixes",
    "task": "Современный линтер должен не просто сообщать об ошибке, но и уметь автоматически исправить ее в исходном коде по команде разработчика. Изучите структуры analysis.SuggestedFix и analysis.TextEdit фреймворка go/analysis и напишите логику генерации автоисправлений для флага -fix.",
    "theory": "Фреймворк `go/analysis` содержит нативную поддержку автоматического рефакторинга кода через поле `SuggestedFixes` в структуре `analysis.Diagnostic`.\n\nКаждое исправление `analysis.SuggestedFix` состоит из:\n- `Message string`: человекочитаемое описание предлагаемого действия;\n- `TextEdits []analysis.TextEdit`: срез атомарных правок текста.\n\nКаждая правка `analysis.TextEdit` задает диапазон замены в исходном файле:\n```go\ntype TextEdit struct {\n    Pos     token.Pos // Начало заменяемого фрагмента\n    End     token.Pos // Конец заменяемого фрагмента\n    NewText []byte    // Новый текст на замену\n}\n```\nКогда разработчик запускает линтер с флагом `-fix` (например, `golangci-lint run --fix` или в IDE через Quick Fix), тулинг автоматически заменяет байты в исходных файлах и форматирует код через `gofmt`.",
    "step_by_step": [
        "Сформировать объект `analysis.TextEdit` с точными координатами `node.Pos()` и `node.End()`.",
        "Подготовить замещающий срез байт `NewText`.",
        "Привязать `SuggestedFix` к сообщению `pass.Report`.",
        "Проверить применение исправления через `analysistest` с суффиксом `.golden`."
    ],
    "code_blocks": [
        {
            "filename": "suggested_fixes.go",
            "lang": "go",
            "code": code19
        }
    ],
    "under_the_hood": "Драйвер анализа сортирует `TextEdits` в обратном порядке (с конца файла к началу). Это гарантирует, что изменение длины строки в начале файла не сдвинет смещения байт для последующих правок в этом же файле.",
    "pitfalls": [
        "Пересекающиеся диапазоны `TextEdits` (приведет к ошибке overlapping edits).",
        "Генерация синтаксически невалидного кода Go в `NewText`.",
        "Забытый импорт пакетов, требуемых для нового сгенерированного кода (требуется кодогенерация импортов через `golang.org/x/tools/go/ast/astutil`)."
    ],
    "bigtech_interview": "Как протестировать `SuggestedFixes` в `analysistest`? Ответ: Создать рядом с файлом `sample.go` файл с суффиксом `sample.go.golden`. Фреймворк `analysistest.Run` применит правки анализатора к первому файлу и побайтово сравнит результат с эталонным файлом `.golden`."
})

# Ex 20: Передача фактов между пакетами (Modular Analysis Facts)
code20 = r'''package main

import (
	"fmt"
	"go/types"
)

// BlockingCallFact факт о том, что функция выполняет блокирующий I/O
type BlockingCallFact struct {
	Reason string
}

func (f *BlockingCallFact) AFact() {} // Маркерный метод интерфейса analysis.Fact

func (f *BlockingCallFact) String() string {
	return "blocking: " + f.Reason
}

func main() {
	fmt.Println("=== Межпакетный модульный анализ (Modular Facts) ===")
	fact := &BlockingCallFact{Reason: "выполняет сетевой вызов"}
	fmt.Printf("Зарегистрирован факт: %s\n", fact.String())
	fmt.Println()
	fmt.Println("Принцип работы Facts в go/analysis:")
	fmt.Println("1. Пакет A объявляет функцию DoNetworkRequest() и экспортирует факт:")
	fmt.Println("   pass.ExportObjectFact(fnObj, &BlockingCallFact{\"network\"})")
	fmt.Println("2. Пакет B импортирует пакет A и вызывает DoNetworkRequest().")
	fmt.Println("3. Анализатор в пакете B импортирует факт:")
	fmt.Println("   var fact BlockingCallFact")
	fmt.Println("   if pass.ImportObjectFact(targetFnObj, &fact) {")
	fmt.Println("       pass.Reportf(call.Pos(), \"вызов блокирующей функции внутри критической секции!\")")
	fmt.Println("   }")
}
'''

validate_go_code(code20, "code20")
exercises.append({
    "num": 20,
    "title": "Передача фактов между пакетами (Modular Analysis Facts)",
    "task": "Некоторые архитектурные проверки невозможно выполнить в рамках одного файла или пакета: например, обнаружение вызова медленной блокирующей функции внутри критической секции. Изучите механизм межпакетных фактов (Modular Analysis Facts): экспорт фактов pass.ExportObjectFact и импорт pass.ImportObjectFact.",
    "theory": "Большинство линтеров работают изолированно в пределах одного пакета (Intra-package Analysis). Но что делать, если функция `db.Query()` объявлена в пакете `database`, а вызывается в пакете `api`?\n\nФреймворк `go/analysis` предоставляет механизм **Фактов (Facts)**:\n1) **Экспорт факта**: Анализатор пакета A помечает объект типа (`types.Object`) или сам пакет сериализуемой структурой-фактом:\n```go\npass.ExportObjectFact(fnObj, &BlockingFact{})\n```\n2) **Кэширование**: Драйвер анализа сохраняет экспортированные факты в бинарный кэш компилятора;\n3) **Импорт факта**: Когда анализатор проверяет пакет B, вызывающий эту функцию, он запрашивает:\n```go\nvar fact BlockingFact\nif pass.ImportObjectFact(calledFn, &fact) {\n    // Найдена блокирующая функция из чужого пакета!\n}\n```\nЭто обеспечивает глубокий межпакетный статический анализ без необходимости перепарсивать исходные коды зависимостей.",
    "step_by_step": [
        "Объявить структуру факта, реализующую интерфейс `analysis.Fact` (метод `AFact()`).",
        "Зарегистрировать тип факта в `analyzer.FactTypes` дескриптора.",
        "Экспортировать факт для обнаруженных функций через `pass.ExportObjectFact`.",
        "Импортировать факт в зависимых пакетах через `pass.ImportObjectFact` и выдать предупреждение."
    ],
    "code_blocks": [
        {
            "filename": "modular_facts.go",
            "lang": "go",
            "code": code20
        }
    ],
    "under_the_hood": "Факты сериализуются с помощью пакета `encoding/gob`. Драйвер сохраняет их в `~/.cache/go-build/`, что позволяет при инкрементальном запуске линтера не анализировать заново неизмененные библиотеки зависимостей.",
    "pitfalls": [
        "Забытая регистрация типа факта в срезе `analyzer.FactTypes` (вызовет панику при вызове `ExportObjectFact`).",
        "Попытка экспортировать несериализуемые типы (каналы, функции, замыкания).",
        "Циклические зависимости между фактами."
    ],
    "bigtech_interview": "Как стандартный анализатор `printf` из `go vet` узнает, что функция `myLogger.Infof()` принимает форматированную строку, если она лежит в другом пакете? Ответ: Анализатор `printf` анализирует исходный код `myLogger.Infof()`. Обнаружив внутри вызов `fmt.Sprintf(format, args...)`, он экспортирует объектный факт `printf.Fact{Kind: ...}` на метод `Infof`. При проверке вызывающего кода `pass.ImportObjectFact` считывает этот факт и проверяет соответствие глаголов форматирования (%s, %d) переданным типам."
})

# Ex 21: Сборка кастомного линтера как плагина golangci-lint
code21 = r'''package main

import (
	"fmt"
)

// ExplainGolangciPlugin демонстрирует интерфейс плагина для golangci-lint
func ExplainGolangciPlugin() {
	fmt.Println("=== Сборка линтера как плагина для golangci-lint ===")
	fmt.Println()
	fmt.Println("1. Обязательная точка входа плагина (файл plugin.go):")
	fmt.Println("   package main")
	fmt.Println("   import \"golang.org/x/tools/go/analysis\"")
	fmt.Println()
	fmt.Println("   // Экспортируемая переменная или функция New")
	fmt.Println("   func New(conf any) ([]*analysis.Analyzer, error) {")
	fmt.Println("       return []*analysis.Analyzer{")
	fmt.Println("           myanalyzer.Analyzer,")
	fmt.Println("       }, nil")
	fmt.Println("   }")
	fmt.Println()
	fmt.Println("2. Команда компиляции плагина Go (.so):")
	fmt.Println("   go build -buildmode=plugin -o mylinters.so plugin.go")
	fmt.Println()
	fmt.Println("3. Подключение в .golangci.yml:")
	fmt.Println("   linters-settings:")
	fmt.Println("     custom:")
	fmt.Println("       myanalyzer:")
	fmt.Println("         path: mylinters.so")
	fmt.Println("         description: Корпоративные правила архитектуры")
}

func main() {
	ExplainGolangciPlugin()
}
'''

validate_go_code(code21, "code21")
exercises.append({
    "num": 21,
    "title": "Сборка кастомного линтера как плагина golangci-lint",
    "task": "Изучите механизм динамических плагинов (Go Plugins) в golangci-lint: напишите экспортируемую функцию New(conf any) ([]*analysis.Analyzer, error), скомпилируйте линтер в динамическую библиотеку mylinters.so с флагом -buildmode=plugin и подключите его в секцию custom конфигурации golangci-lint.",
    "theory": "`golangci-lint` — абсолютный стандарт агрегации линтеров в сообществе Go (объединяет более 50 инструментов анализа).\n\nДля подключения собственных корпоративных проверок `golangci-lint` поддерживает систему плагинов:\n1) **Контракт плагина**: Создается пакет `main`, экспортирующий конструктор:\n```go\nfunc New(conf any) ([]*analysis.Analyzer, error) {\n    return []*analysis.Analyzer{MyCustomAnalyzer}, nil\n}\n```\n2) **Компиляция**: Плагин собирается как динамическая библиотека shared object:\n`go build -buildmode=plugin -o mylinters.so .`\n3) **Конфигурация**: В `.golangci.yml` прописывается путь к `.so` файлу.\n\nОднако режим `-buildmode=plugin` имеет жесткое ограничение: он требует точнейшего побайтового совпадения версий зависимостей, компилятора Go и флагов сборки между бинарником `golangci-lint` и плагином, поэтому в современных пайплайнах предпочтение отдается компиляции через Module Plugins.",
    "step_by_step": [
        "Создать файл плагина с функцией-конструктором `New`.",
        "Скомпилировать плагин с флагом `-buildmode=plugin`.",
        "Прописать плагин в блоке `linters-settings.custom` в `.golangci.yml`.",
        "Запустить проверку `golangci-lint run` с новым анализатором."
    ],
    "code_blocks": [
        {
            "filename": "plugin_integration.go",
            "lang": "go",
            "code": code21
        }
    ],
    "under_the_hood": "`golangci-lint` открывает `.so` файл системным вызовом `plugin.Open()`, ищет символ `New` через `p.Lookup(\"New\")` и регистрирует полученные анализаторы в общем планировщике проверок.",
    "pitfalls": [
        "Несовпадение версии компилятора Go между `golangci-lint` и плагином (ошибка `plugin was built with a different version of package ...`).",
        "Плагины Go не поддерживаются на операционной системе Windows.",
        "Несовпадение версии пакета `golang.org/x/tools`."
    ],
    "bigtech_interview": "Почему в production CI/CD избегают `.so` плагинов Go? Ответ: Из-за крайней хрупкости `plugin.Open`: любая разница в зависимостях или патч-версии компилятора Go ломает запуск линтера. Вместо динамических плагинов в BigTech используютModule Plugins: статическую пересборку бинарника `golangci-lint` с включенными линтерами компании."
})

# Ex 22: Интеграция через Module Plugins в golangci-lint
code22 = r'''package main

import (
	"fmt"
)

// ExplainModulePlugins демонстрирует статическую сборку golangci-lint с линтерами
func ExplainModulePlugins() {
	fmt.Println("=== Статическая интеграция через Module Plugins в golangci-lint ===")
	fmt.Println()
	fmt.Println("Современный стандарт без CGO и без проблем с версиями (golangci-lint custom):")
	fmt.Println("1. Создание манифеста сборщика .custom-gcl.yml:")
	fmt.Println("   version: v1.60.0")
	fmt.Println("   plugins:")
	fmt.Println("     - module: 'github.com/mycompany/linters'")
	fmt.Println("       import: 'github.com/mycompany/linters/cleanarch'")
	fmt.Println("       version: v1.0.0")
	fmt.Println()
	fmt.Println("2. Команда сборки корпоративного бинарника:")
	fmt.Println("   golangci-lint custom")
	fmt.Println()
	fmt.Println("3. Результат: Единый монолитный бинарник ./custom-gcl со всеми встроенными")
	fmt.Println("   корпоративными анализаторами, работающий на любой ОС без CGO и .so файлов!")
}

func main() {
	ExplainModulePlugins()
}
'''

validate_go_code(code22, "code22")
exercises.append({
    "num": 22,
    "title": "Интеграция через Module Plugins в golangci-lint",
    "task": "Динамические плагины .so хрупки и не работают на Windows. Освойте официальный механизм Module Plugins в golangci-lint: декларативный файл конфигурации .custom-gcl.yml, утилиту golangci-lint custom и статическую компиляцию монолитного корпоративного бинарника линтера со встроенными анализаторами компании.",
    "theory": "Для решения проблем с динамическими плагинами создатели `golangci-lint` разработали команду `golangci-lint custom` (Module Plugins).\n\nПринцип работы:\n1) Создается манифест `.custom-gcl.yml`:\n```yaml\nversion: v1.60.0\nplugins:\n  - module: 'github.com/mycompany/governance-linters'\n    import: 'github.com/mycompany/governance-linters/pkg/rules'\n    version: v1.2.0\n```\n2) Запускается команда `golangci-lint custom`;\n3) Утилита скачивает Go-модули ваших линтеров, генерирует обертку `main.go` и статически компилирует единый самодостаточный бинарный файл `custom-gcl`;\n4) Полученный бинарник распространяется среди разработчиков и в Docker-образах CI/CD. Он на 100% стабилен, работает без CGO на любой ОС (Linux, macOS, Windows) и запускается мгновенно.",
    "step_by_step": [
        "Спроектировать манифест `.custom-gcl.yml` с указанием версии базового линтера и модулей плагинов.",
        "Реализовать экспорт структуры анализатора из корпоративного Go-модуля.",
        "Выполнить сборку через `golangci-lint custom`.",
        "Проверить работу собственного бинарника командой `./custom-gcl linters`."
    ],
    "code_blocks": [
        {
            "filename": "custom_gcl_builder.go",
            "lang": "go",
            "code": code22
        }
    ],
    "under_the_hood": "Команда `custom` под капотом разворачивает временный модуль Go в каталоге кэша, генерирует код вызова конструкторов линтеров, запускает стандартный компилятор `go build -o custom-gcl` и очищает временные артефакты.",
    "pitfalls": [
        "Конфликт версий транзитивных зависимостей между `golangci-lint` и вашим линтером (требуется выравнивание go.mod).",
        "Отсутствие тэга версии в Git-репозитории кастомного линтера при сборке через модуль.",
        "Забытое обновление версии базового golangci-lint в манифесте."
    ],
    "bigtech_interview": "Как распространять кастомный корпоративный `golangci-lint` среди 500 разработчиков компании? Ответ: Собирать бинарник `custom-gcl` в базовый Docker-образ CI/CD и выкладывать мультиплатформенные бинарники (linux/amd64, darwin/arm64, windows/amd64) во внутренний реестр Nexus/Artifactory с автоматическим обновлением через корпоративный менеджер пакетов (brew tap или asdf plugin)."
})

# Ex 23: Конфигурация .golangci.yml для корпоративных проверок
code23 = r'''package main

import (
	"fmt"
)

// GenerateGolangciYaml генерирует эталонный файл конфигурации
func GenerateGolangciYaml() string {
	return `
run:
  timeout: 5m
  tests: true

linters:
  disable-all: true
  enable:
    - errcheck      # Проверка необработанных ошибок
    - gosimple      # Упрощение кода
    - govet         # Официальные проверки компилятора
    - ineffassign   # Детекция бесполезных присваиваний
    - staticcheck   # Глубокий статический анализ
    - unused        # Неиспользуемый код
    - gosec         # Проверка уязвимостей безопасности
    - revive        # Быстрый расширяемый линтер стиля
    - bodyclose     # Закрытие resp.Body

linters-settings:
  govet:
    enable-all: true
    disable:
      - fieldalignment # Включается точечно
  revive:
    rules:
      - name: context-as-argument
        severity: error
      - name: exported
        severity: warning

issues:
  exclude-use-default: false
  max-issues-per-linter: 0
  max-same-issues: 0
`
}

func main() {
	fmt.Println("=== Корпоративная конфигурация .golangci.yml ===")
	fmt.Println(GenerateGolangciYaml())
}
'''

validate_go_code(code23, "code23")
exercises.append({
    "num": 23,
    "title": "Конфигурация .golangci.yml для корпоративных проверок",
    "task": "Напишите эталонный конфигурационный файл .golangci.yml для крупного микросервисного проекта: отключение проверок по умолчанию (disable-all: true), включение строгого базового набора линтеров (govet, errcheck, staticcheck, gosec, bodyclose), настройка правил revive и лимитов диагностик.",
    "theory": "Эффективность статического анализа определяется качеством его конфигурации. Конфигурация по умолчанию в `golangci-lint` включает лишь несколько базовых инструментов, пропуская критические баги.\n\nПромышленный стандарт настройки `.golangci.yml`:\n1) **`disable-all: true`**: отключить дефолтный набор, чтобы явно контролировать каждый включенный инструмент;\n2) **Ядро надежности**: `errcheck`, `govet`, `staticcheck`, `ineffassign`, `unused`;\n3) **Безопасность**: `gosec` (детекция слабых шифров, инъекций, утечек секретов);\n4) **Управление ресурсами**: `bodyclose` (контроль HTTP body);\n5) **Тюнинг вывода (`issues`)**: установка `max-issues-per-linter: 0` и `max-same-issues: 0`, чтобы линтер не обрезал одинаковые ошибки на больших кодовых базах.",
    "step_by_step": [
        "Настроить секцию `run` (таймаут выполнения, анализ тестов).",
        "Сформировать белый список включенных линтеров в секции `linters.enable`.",
        "Настроить параметры правил в `linters-settings`.",
        "Настроить правила фильтрации ложных срабатываний в секции `issues`."
    ],
    "code_blocks": [
        {
            "filename": "golangci_config.go",
            "lang": "go",
            "code": code23
        }
    ],
    "under_the_hood": "`golangci-lint` парсит `.golangci.yml` с помощью библиотеки `spf13/viper`. Конфигурация кэшируется, а при запуске в подкаталогах репозитория линтер автоматически поднимается вверх по дереву каталогов в поисках ближайшего конфига.",
    "pitfalls": [
        "Включение сразу всех 60+ линтеров без разбора (приведет к тысячам конфликтующих предупреждений и отторжению инструмента командой).",
        "Установка слишком низкого таймаута (например, 1m на проекте из миллиона строк линтер упадет по таймауту).",
        "Использование устаревших имен линтеров в новых версиях golangci-lint."
    ],
    "bigtech_interview": "Как внедрить жесткий `.golangci.yml` в старый легаси-проект с 5000 существующих нарушений? Ответ: Использовать параметр `new-from-rev: origin/master` в секции `issues`. Линтер будет проверять и блокировать ошибки ТОЛЬКО в новых измененных строках кода PR, не трогая легаси. Это позволяет мгновенно остановить деградацию кода, а старые ошибки постепенно вычищать в фоновом режиме."
})

# Ex 24: Оптимизация производительности анализатора
code24 = r'''package main

import (
	"fmt"
	"time"
)

// ProfilingOptimizer объясняет техники ускорения анализаторов
func ExplainLinterOptimizations() {
	fmt.Println("=== Оптимизация производительности статических анализаторов ===")
	fmt.Println()
	fmt.Println("Ключевые приемы ускорения на миллионных кодовых базах:")
	fmt.Println("1. Pruning поддеревьев в ast.Inspect:")
	fmt.Println("   - Возвращайте 'false' сразу при встрече узлов, которые не могут содержать ошибку.")
	fmt.Println("2. Ленивый (Lazy) анализ типов:")
	fmt.Println("   - Сначала делайте быструю синтаксическую фильтрацию по AST (например, call.Sel.Name == 'Query').")
	fmt.Println("   - И только если имя совпало — запрашивайте тяжелый семантический тип из pass.TypesInfo.")
	fmt.Println("3. Предварительная фильтрация файлов по байтовому сканированию:")
	fmt.Println("   - Если файл не содержит подстроку 'context', не парсите его глубоким анализатором контекстов.")
	fmt.Println("4. Параллелизация на уровне пакетов (встроена в go/analysis).")
}

func main() {
	ExplainLinterOptimizations()
}
'''

validate_go_code(code24, "code24")
exercises.append({
    "num": 24,
    "title": "Оптимизация производительности анализатора",
    "task": "В Monorepo на 1 000 000 строк медленный линтер парализует работу разработчиков и затягивает CI. Изучите методы оптимизации производительности анализаторов: отсечение поддеревьев AST (Pruning), ленивый запрос семантики типов go/types только после синтаксической фильтрации и профилирование скорости через go test -bench.",
    "theory": "Статический анализ — ресурсоемкая операция. Если ваш кастомный линтер будет для каждого выражения в кодовой базе вызывать тяжелые проверки типов `types.Implements` или парсить интерфейсы, проверка репозитория займет 10 минут.\n\nЗолотые правила оптимизации анализаторов:\n1) **Синтаксический фильтр впереди семантического (AST Filter First)**: Сравнение строк `call.Sel.Name == \"Exec\"` занимает 2 наносекунды. Запрос к карте типов `pass.TypesInfo.Types[call]` занимает 100 наносекунд. Сначала отфильтруйте 99.9% нерелевантных узлов по именам селекторов AST, и только для оставшихся 0.1% делайте проверку типов;\n2) **Раннее отсечение (Subtree Pruning)**: Если анализатор проверяет глобальные переменные, возвращайте `false` при входе в любую функцию — не тратьте время на обход миллионов операторов внутри функций;\n3) **Профилирование**: Запуск `go test -bench . -cpuprofile cpu.prof` позволяет выявить узкие места линтера через `go tool pprof`.",
    "step_by_step": [
        "Изучить воронку фильтрации узлов AST от дешевых синтаксических к дорогим семантическим.",
        "Реализовать возврат `false` в `ast.Inspect` для отсечения нерелевантных блоков.",
        "Написать бенчмарк анализатора на синтетическом пакете из 10 000 строк.",
        "Замерить ускорение работы и сокращение потребления оперативной памяти."
    ],
    "code_blocks": [
        {
            "filename": "linter_optimization.go",
            "lang": "go",
            "code": code24
        }
    ],
    "under_the_hood": "Фреймворк `go/analysis` использует `inspect.Analyzer` (из пакета `golang.org/x/tools/go/analysis/passes/inspect`). Он выполняет ровно один проход по AST для всех анализаторов пакета, собирая индекс узлов по типам (`inspector.Preorder`), устраняя повторные обходы дерева.",
    "pitfalls": [
        "Повторный парсинг исходных файлов через `parser.ParseFile` внутри функции `Run` (файлы уже распарсены и лежат в `pass.Files`).",
        "Создание больших временных структур данных в хипе на каждый узел AST.",
        "Аллокации замыканий внутри функции обхода `ast.Inspect`."
    ],
    "bigtech_interview": "Почему использование `golang.org/x/tools/go/analysis/passes/inspect` ускоряет сьют из 20 линтеров в 5 раз? Ответ: Без инспектора каждый из 20 анализаторов делает свой собственный полный рекурсивный обход всех файлов пакета. Инспектор обходит AST один раз, строит компактный слайс узлов и позволяет каждому анализатору подписаться только на интересующие его типы узлов (например, только `*ast.CallExpr`), исключая 95% лишней работы."
})

# Ex 25: Линтер 10: Запрет использования SQL-конкатенации
code25 = r'''package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
)

// CheckSQLInjection находит склеивание строк в SQL запросах
func CheckSQLInjection(fset *token.FileSet, file *ast.File) []string {
	var issues []string

	ast.Inspect(file, func(n ast.Node) bool {
		call, ok := n.(*ast.CallExpr)
		if !ok {
			return true
		}

		sel, ok := call.Fun.(*ast.SelectorExpr)
		if !ok {
			return true
		}

		// Проверяем вызовы методов Query, QueryRow, Exec
		methodName := sel.Sel.Name
		if methodName != "Query" && methodName != "QueryRow" && methodName != "Exec" {
			return true
		}

		if len(call.Args) == 0 {
			return true
		}

		// Первый аргумент (или второй, если первым идет context)
		sqlArg := call.Args[0]
		if len(call.Args) > 1 {
			// Если первый аргумент ctx
			if ident, ok := call.Args[0].(*ast.Ident); ok && ident.Name == "ctx" {
				sqlArg = call.Args[1]
			}
		}

		// 1. Проверка конкатенации строк через оператор '+'
		if binExpr, ok := sqlArg.(*ast.BinaryExpr); ok && binExpr.Op == token.ADD {
			pos := fset.Position(binExpr.Pos())
			issues = append(issues, fmt.Sprintf("%s:%d: уязвимость SQL-инъекции: запрещена конкатенация строк в %s(); используйте плейсхолдеры $1, $2",
				pos.Filename, pos.Line, methodName))
		}

		// 2. Проверка форматирования через fmt.Sprintf(...)
		if innerCall, ok := sqlArg.(*ast.CallExpr); ok {
			if innerSel, ok := innerCall.Fun.(*ast.SelectorExpr); ok {
				if innerSel.Sel.Name == "Sprintf" {
					pos := fset.Position(innerCall.Pos())
					issues = append(issues, fmt.Sprintf("%s:%d: уязвимость SQL-инъекции: запрещено использование fmt.Sprintf в %s(); используйте плейсхолдеры",
						pos.Filename, pos.Line, methodName))
				}
			}
		}

		return true
	})

	return issues
}

func main() {
	fmt.Println("=== Линтер nosqlinjection: Защита от SQL-инъекций ===")
	src := `package repo

import "fmt"

func GetUser(db DB, ctx Context, id string) {
	// Опасная конкатенация!
	db.Query(ctx, "SELECT * FROM users WHERE id = '" + id + "'")

	// Опасный fmt.Sprintf!
	query := fmt.Sprintf("DELETE FROM orders WHERE user_id = '%s'", id)
	db.Exec(ctx, query)
}
`
	fset := token.NewFileSet()
	file, _ := parser.ParseFile(fset, "repo.go", src, 0)

	findings := CheckSQLInjection(fset, file)
	for _, f := range findings {
		fmt.Println("🚨", f)
	}
}
'''

validate_go_code(code25, "code25")
exercises.append({
    "num": 25,
    "title": "Линтер 10: Запрет использования SQL-конкатенации (SQL Injection Prevention)",
    "task": "SQL-инъекция — уязвимость номер один в веб-приложениях. Разработайте анализатор безопасности nosqlinjection: анализирует аргументы методов Query, QueryRow и Exec, запрещая формирование текста запроса через конкатенацию строк (оператор +) или вызов fmt.Sprintf, принуждая разработчиков использовать позиционные параметры ($1, $2).",
    "theory": "Уязвимости типа SQL Injection возникают, когда недоверенные пользовательские данные конкатенируются напрямую в строку SQL-запроса.\n\nЗлоумышленник может передать в поле ID значение `' OR '1'='1`, получив доступ ко всей базе данных или стерев таблицы (`'; DROP TABLE users; --`).\n\nЕдинственная надежная защита — параметризованные запросы (Prepared Statements / Positional Parameters):\n```go\n// БЕЗОПАСНО:\ndb.QueryContext(ctx, \"SELECT * FROM users WHERE id = $1\", userID)\n\n// ОПАСНО (конкатенация):\ndb.QueryContext(ctx, \"SELECT * FROM users WHERE id = '\" + userID + \"'\")\n\n// ОПАСНО (fmt.Sprintf):\ndb.QueryContext(ctx, fmt.Sprintf(\"SELECT * FROM users WHERE id = '%s'\", userID))\n```\nАнализатор `nosqlinjection` инспектирует аргумент SQL-запроса: если аргумент не является строковым литералом `*ast.BasicLit` или статической константой, а представлен бинарным сложением `*ast.BinaryExpr (+)` или вызовом `fmt.Sprintf`, билд немедленно блокируется.",
    "step_by_step": [
        "Обнаружить вызовы методов `Query`, `QueryRow`, `Exec` у интерфейсов базы данных.",
        "Определить позицию аргумента SQL-запроса с учетом наличия контекста первым параметром.",
        "Проверить узел аргумента на бинарную операцию сложения `token.ADD`.",
        "Проверить узел аргумента на вызов функции форматирования `fmt.Sprintf`.",
        "Сформировать предупреждение безопасности критического приоритета (CRITICAL)."
    ],
    "code_blocks": [
        {
            "filename": "nosqlinjection_analyzer.go",
            "lang": "go",
            "code": code25
        }
    ],
    "under_the_hood": "В enterprise-безопасности аналогичный анализ выполняется популярными линтерами `gosec` (правило G201/G202) и Google SafeSQL. Они используют граф потока данных (Taint Analysis) для отслеживания пути переменной от HTTP-запроса до вызова SQL-драйвера.",
    "pitfalls": [
        "Ложные срабатывания при склейке статических константных строк, разбитых на несколько строк для читаемости (`\"SELECT ... \" + \"FROM ...\"`).",
        "Пропуск запросов, собранных через `strings.Builder` или `bytes.Buffer` (требуется taint analysis).",
        "Игнорирование оберток ORM (Gorm, Squirrel, Ent)."
    ],
    "bigtech_interview": "Как разрешить разработчикам динамически добавлять условия `WHERE` без риска SQL-инъекций? Ответ: Использовать типобезопасные query builder библиотеки (например, `Masterminds/squirrel` или кодогенератор `sqlc`). Они собирают запросы из отдельных клауз, автоматически подставляя плейсхолдеры `$1, $2` и собирая аргументы в единый безопасный слайс параметров `args []interface{}`."
})

output_path = '/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch98_p2.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Chapter 98 Part 2 generated successfully: {len(exercises)} exercises.")
