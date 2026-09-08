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

# Ex 1: Роль статического анализа в поддержании архитектуры Monorepo
code1 = r'''package main

import (
	"fmt"
)

// ArchitectureRule описывает правило архитектурного контроля
type ArchitectureRule struct {
	Name        string
	Severity    string
	Description string
}

// MonorepoGovernancePolicy формулирует манифест автоматического контроля
func GetArchitectureRules() []ArchitectureRule {
	return []ArchitectureRule{
		{
			Name:        "LayerIsolation",
			Severity:    "BLOCKING",
			Description: "Пакет domain/* не имеет права импортировать infrastructure/* или database/*.",
		},
		{
			Name:        "ContextPropagation",
			Severity:    "BLOCKING",
			Description: "Запрещен context.Background() внутри бизнес-логики; контекст передается 1-м аргументом.",
		},
		{
			Name:        "SQLSanitization",
			Severity:    "BLOCKING",
			Description: "Запрещена конкатенация строк в SQL-запросах; разрешены только позиционные плейсхолдеры.",
		},
		{
			Name:        "ResourceCleanup",
			Severity:    "BLOCKING",
			Description: "defer resp.Body.Close() обязан вызываться строго ПОСЛЕ проверки if err != nil.",
		},
	}
}

func main() {
	fmt.Println("=== Автоматический архитектурный контроль в Monorepo ===")
	rules := GetArchitectureRules()
	for i, r := range rules {
		fmt.Printf("%d. [%s] %s: %s\n", i+1, r.Severity, r.Name, r.Description)
	}
	fmt.Println("\nВывод: Ручное Code Review пропускает 30% скрытых архитектурных нарушений.")
	fmt.Println("Пользовательские линтеры на go/analysis блокируют антипаттерны еще до коммита.")
}
'''

validate_go_code(code1, "code1")
exercises.append({
    "num": 1,
    "title": "Роль статического анализа в поддержании архитектуры Monorepo",
    "task": "Изучите, почему ручное ревью кода (Code Review) неизбежно дает сбои в масштабе компании с сотнями разработчиков и микросервисов. Сформулируйте задачи автоматического архитектурного надзора: предотвращение эрозии архитектурных слоев (Layer Inversion), обнаружение утечек горутин и контекстов, блокировка SQL-инъекций и принудительное следование соглашениям компании на уровне CI.",
    "theory": "В быстрорастущих технологических компаниях кодовая база исчисляется миллионами строк кода в Monorepo или сотнях репозиториев.\n\nПроблема 'архитектурной эрозии' (Architectural Decay): когда дедлайны горят, разработчики склонны срезать углы — импортировать слой базы данных напрямую в доменную модель, использовать `context.Background()` вместо проброса контекста или забывать освобождать ресурсы.\n\nНадежда на ручное Code Review не оправдывается: 1) Человеческая усталость (reviewer fatigue); 2) Разный уровень опыта инженеров; 3) Субъективность споров в комментариях к PR.\n\nЕдинственное надежное решение — **программный архитектурный надзор (Policy as Code)** через кастомные статические анализаторы. Линтер проверяет синтаксические деревья (AST) за секунды и блокирует слияние pull request при малейшем нарушении контрактов.",
    "step_by_step": [
        "Классифицировать категории критических дефектов (архитектурные, надежность, безопасность).",
        "Сформулировать инварианты изоляции слоев Clean Architecture.",
        "Определить место статического анализа в конвейере разработки (Pre-commit -> IDE -> CI/CD Gate).",
        "Спроектировать манифест корпоративных правил кодогенерации и проверки."
    ],
    "code_blocks": [
        {
            "filename": "monorepo_governance.go",
            "lang": "go",
            "code": code1
        }
    ],
    "under_the_hood": "Статический анализ Go опирается на то, что язык Go имеет строгую грамматику и компилятор с открытым исходным кодом. Официальный тулинг `golang.org/x/tools/go/analysis` позволяет инспектировать типы и AST с той же точностью, с какой их видит компилятор `gc`.",
    "pitfalls": [
        "Попытка писать архитектурные проверки на регулярных выражениях regex (grep) вместо синтаксического анализа AST (регулярки ломаются от комментариев и форматирования).",
        "Слишком жесткие неблокирующие предупреждения (Warning), которые разработчики быстро начинают игнорировать.",
        "Отсутствие автоматических исправлений (SuggestedFixes) для распространенных нарушений."
    ],
    "bigtech_interview": "Как в Uber и Google обеспечивают соблюдение архитектурных стандартов тысячами инженеров? Ответ: Через создание собственных линтеров на базе go/analysis, интегрированных в CI. Если код нарушает правило (например, обращается к внутренней структуре чужого пакета без интерфейса), PR автоматически блокируется ботом с точной ссылкой на документацию и готовым Suggested Fix."
})

# Ex 2: Архитектура фреймворка golang.org/x/tools/go/analysis
code2 = r'''package main

import (
	"fmt"
	"go/token"
)

// DummyDiagnostic имитирует структуру analysis.Diagnostic
type DummyDiagnostic struct {
	Pos     token.Pos
	Message string
}

// DummyAnalyzer описывает контракт анализатора
type DummyAnalyzer struct {
	Name string
	Doc  string
	Run  func() []DummyDiagnostic
}

func main() {
	fmt.Println("=== Архитектура фреймворка golang.org/x/tools/go/analysis ===")
	fmt.Println()
	fmt.Println("Ключевые сущности фреймворка:")
	fmt.Println("1. analysis.Analyzer — манифест линтера (Name, Doc, Run, Requires, FactTypes).")
	fmt.Println("2. analysis.Pass — контекст запуска для конкретного пакета Go:")
	fmt.Println("   - pass.Fset: token.FileSet (позиции файлов, строк и колонок)")
	fmt.Println("   - pass.Files: []*ast.File (синтаксические деревья)")
	fmt.Println("   - pass.Pkg: *types.Package (информация о компилируемом пакете)")
	fmt.Println("   - pass.TypesInfo: *types.Info (карты семантики типов: Defs, Uses, Types)")
	fmt.Println("   - pass.Reportf(): регистрация ошибок и предупреждений с точной позицией в коде")
	fmt.Println("3. analysis.Fact — механизм передачи информации между пакетами в дереве сборки.")
}
'''

validate_go_code(code2, "code2")
exercises.append({
    "num": 2,
    "title": "Архитектура фреймворка golang.org/x/tools/go/analysis",
    "task": "Изучите внутреннее устройство стандартного фреймворка статического анализа Go (golang.org/x/tools/go/analysis): манифест analysis.Analyzer, контекст прохода analysis.Pass, сообщения об ошибках analysis.Diagnostic, зависимости анализаторов (Requires) и межпакетные факты analysis.Fact.",
    "theory": "Фреймворк `golang.org/x/tools/go/analysis` — это официальный модульный стандарт разработки линтеров в экосистеме Go, созданный авторами языка (на нем работают `go vet`, `staticcheck` и `golangci-lint`).\n\nАрхитектура построена вокруг двух понятий:\n1) **`analysis.Analyzer`**: неизменяемый дескриптор инструмента. Он задает уникальное имя (`Name`), документацию (`Doc`), функцию запуска (`Run`), список предварительно требуемых анализаторов (`Requires`) и типы экспортируемых фактов (`FactTypes`);\n2) **`analysis.Pass`**: контекст выполнения для одного конкретного пакета Go. Через `pass` анализатор получает доступ к синтаксическим деревьям файлов (`pass.Files`), таблицам типов компилятора (`pass.TypesInfo`), набору файлов (`pass.Fset`) и методам сообщения об ошибках (`pass.Reportf`).\n\nФреймворк берет на себя распараллеливание анализа по ядрам CPU, кэширование результатов и управление зависимостями.",
    "step_by_step": [
        "Изучить сигнатуру функции `Run: func(*analysis.Pass) (interface{}, error)`.",
        "Понять роль `token.FileSet` для перевода смещений байт в номера строк.",
        "Разобрать граф зависимостей между анализаторами через поле `Requires`.",
        "Сформулировать требования к модульности и идемпотентности анализатора."
    ],
    "code_blocks": [
        {
            "filename": "analysis_framework.go",
            "lang": "go",
            "code": code2
        }
    ],
    "under_the_hood": "Драйвер анализа (например, `singlechecker` или `multichecker`) строит направленный ациклический граф (DAG) пакетов проекта. Пакеты анализируются в топологическом порядке: сначала зависимости, затем зависимые модули. Это позволяет передавать факты о типах от нижних уровней к верхним.",
    "pitfalls": [
        "Использование глобального изменяемого состояния внутри структуры Analyzer (приведет к гонкам данных при параллельном анализе пакетов).",
        "Вызов `panic()` внутри функции `Run` при синтаксических ошибках в анализируемом коде.",
        "Игнорирование поля `Requires`: если анализатору нужны типы, но не указан inspect/types, `pass.TypesInfo` может быть неполным."
    ],
    "bigtech_interview": "В чем преимущество `go/analysis` перед написанием собственных скриптов разбора AST? Ответ: Унификация. Линтер, написанный по стандарту `go/analysis`, может запускаться как самостоятельная консольная утилита (`singlechecker`), как часть общего монолитного чекера (`multichecker`), встраиваться в `go vet` или компилироваться в плагин `golangci-lint` без изменения единой строчки кода."
})

# Ex 3: Анатомия абстрактного синтаксического дерева (go/ast)
code3 = r'''package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
)

// PrintASTStructure демонстрирует иерархию синтаксического дерева Go
func PrintASTStructure() {
	src := `
package sample

func Calculate(x int) int {
	if x > 0 {
		return x * 2
	}
	return 0
}
`
	fset := token.NewFileSet()
	node, err := parser.ParseFile(fset, "sample.go", src, parser.AllErrors)
	if err != nil {
		fmt.Println("Parse error:", err)
		return
	}

	fmt.Println("Имя пакета:", node.Name.Name)
	for _, decl := range node.Decls {
		if fn, ok := decl.(*ast.FuncDecl); ok {
			fmt.Printf("Объявление функции: %s\n", fn.Name.Name)
			fmt.Printf("  -> Параметров: %d\n", len(fn.Type.Params.List))
			fmt.Printf("  -> Операторов в теле: %d\n", len(fn.Body.List))
			for i, stmt := range fn.Body.List {
				switch s := stmt.(type) {
				case *ast.IfStmt:
					fmt.Printf("    [%d] Оператор условия: if ...\n", i)
				case *ast.ReturnStmt:
					fmt.Printf("    [%d] Оператор возврата: return ...\n", i)
				default:
					fmt.Printf("    [%d] Оператор типа: %T\n", i, s)
				}
			}
		}
	}
}

func main() {
	fmt.Println("=== Анатомия абстрактного синтаксического дерева (go/ast) ===")
	PrintASTStructure()
}
'''

validate_go_code(code3, "code3")
exercises.append({
    "num": 3,
    "title": "Анатомия абстрактного синтаксического дерева (go/ast)",
    "task": "Изучите базовые типы и иерархию пакета go/ast: корень дерева ast.File, интерфейс узла ast.Node, объявления ast.Decl (FuncDecl, GenDecl), операторы ast.Stmt (IfStmt, ReturnStmt, AssignStmt) и выражения ast.Expr (CallExpr, BinaryExpr, Ident). Напишите утилиту инспекции структуры функции Calculate.",
    "theory": "Пакет `go/ast` объявляет типы данных для представления абстрактных синтаксических деревьев программ на Go.\n\nКаждый элемент программы является реализацией интерфейса `ast.Node`:\n```go\ntype Node interface {\n    Pos() token.Pos // Начальная позиция узла\n    End() token.Pos // Конечная позиция узла\n}\n```\nВсе узлы делятся на три основные группы:\n1) **`ast.Decl` (Declarations)**: объявления верхнего уровня (`*ast.FuncDecl` — функции и методы, `*ast.GenDecl` — импорты, константы, переменные и типы);\n2) **`ast.Stmt` (Statements)**: императивные инструкции внутри тел функций (`*ast.IfStmt`, `*ast.ForStmt`, `*ast.ReturnStmt`, `*ast.AssignStmt`);\n3) **`ast.Expr` (Expressions)**: выражения, вычисляющие значение (`*ast.CallExpr` — вызов функции, `*ast.BinaryExpr` — бинарная операция `x > 0`, `*ast.Ident` — идентификатор имени переменной).",
    "step_by_step": [
        "Использовать `parser.ParseFile` для разбора исходного текста программы в дерево AST.",
        "Итерироваться по слайсу объявлений `file.Decls`.",
        "Выполнить приведение типа к `*ast.FuncDecl` для получения сигнатуры и тела функции.",
        "Разобрать операторы блока `fn.Body.List` через switch по типам `ast.Stmt`."
    ],
    "code_blocks": [
        {
            "filename": "ast_anatomy.go",
            "lang": "go",
            "code": code3
        }
    ],
    "under_the_hood": "Парсер Go строит точное синтаксическое дерево без потерь: каждый узел хранит token.Pos, указывающий на байтовое смещение в исходном файле. Это позволяет сопоставлять синтаксические конструкции с комментариями (`ast.CommentGroup`) и сохранять форматирование.",
    "pitfalls": [
        "Путаница между выражениями (`ast.Expr`) и операторами (`ast.Stmt`): например, вызов функции в строке `fn()` является оператором `*ast.ExprStmt`, внутри которого лежит выражение `*ast.CallExpr`.",
        "Разыменование nil-полей (например, `fn.Body` у объявления функции интерфейса или внешней сборки cgo равен `nil`).",
        "Игнорирование скобок `*ast.ParenExpr` при анализе сложных выражений."
    ],
    "bigtech_interview": "Почему в AST Go вызов метода `user.Save()` представлен как `*ast.CallExpr` с полем `Fun` типа `*ast.SelectorExpr`? Ответ: Потому что синтаксически `user.Save` — это выборка поля/метода через селектор точку. `X` селектора — это идентификатор `user`, а `Sel` — идентификатор `Save`. `CallExpr` оборачивает этот селектор со списком переданных аргументов `Args`."
})

# Ex 4: Информация о типах (go/types): переход от синтаксиса к семантике
code4 = r'''package main

import (
	"fmt"
	"go/ast"
	"go/importer"
	"go/parser"
	"go/token"
	"go/types"
)

// SemanticTypeAnalyzer демонстрирует извлечение типов компилятора через go/types
func SemanticTypeAnalyzer() {
	src := `
package main

import "io"

func CloseResource(r io.Closer) error {
	return r.Close()
}
`
	fset := token.NewFileSet()
	file, _ := parser.ParseFile(fset, "main.go", src, parser.AllErrors)

	// Настройка type checker
	conf := types.Config{Importer: importer.Default()}
	info := &types.Info{
		Types: make(map[ast.Expr]types.TypeAndValue),
		Defs:  make(map[*ast.Ident]types.Object),
		Uses:  make(map[*ast.Ident]types.Object),
	}

	pkg, err := conf.Check("main", fset, []*ast.File{file}, info)
	if err != nil {
		fmt.Println("Typecheck error:", err)
		return
	}

	fmt.Printf("Пакет успешно типизирован: %s\n", pkg.Path())
	fmt.Printf("Количество разрешенных выражений в Types: %d\n", len(info.Types))
	fmt.Printf("Количество определенных объектов в Defs: %d\n", len(info.Defs))
	fmt.Printf("Количество используемых объектов в Uses: %d\n", len(info.Uses))
}

func main() {
	fmt.Println("=== Семантический анализ типов с go/types ===")
	SemanticTypeAnalyzer()
}
'''

validate_go_code(code4, "code4")
exercises.append({
    "num": 4,
    "title": "Информация о типах (go/types): переход от синтаксиса к семантике",
    "task": "Синтаксический анализ AST видит только имена идентификаторов, но слеп к их реальным типам. Изучите структуру types.Info пакета go/types: карты Types (типы и константные значения выражений), Defs (объявления идентификаторов) и Uses (использование идентификаторов). Покажите, как types.Info связывает узел AST с типами компилятора.",
    "theory": "Синтаксическое дерево (AST) знает только то, что написано в коде: например, `x.Close()`. Но является ли `x` структурой `*os.File`, сетевым сокетом `net.Conn` или кастомным типом пользователя? Имеет ли метод `Close()` сигнатуру `Close() error` или не возвращает ничего?\n\nБез информации о типах ответить на эти вопросы невозможно.\n\nПакет `go/types` выполняет полную проверку типов (Type Checking) по правилам языка Go и заполняет структуру `types.Info`:\n1) **`Types map[ast.Expr]TypeAndValue`**: отображает любое синтаксическое выражение (например, `x + 1`) на его статический тип `types.Type` и значение (если вычисляется во время компиляции);\n2) **`Defs map[*ast.Ident]Object`**: отображает идентификатор в месте его ОБЪЯВЛЕНИЯ на объект символа (переменная, константа, имя функции);\n3) **`Uses map[*ast.Ident]Object`**: отображает идентификатор в месте его ИСПОЛЬЗОВАНИЯ на объект, где он был объявлен;\n4) **`types.Implements(T, Iface)`**: позволяет программно проверить, реализует ли тип интерфейс `error` или `io.Closer`.",
    "step_by_step": [
        "Изучить назначение структуры `types.Info` и ее основных карт Defs, Uses, Types.",
        "Инициализировать `types.Config` и выполнить `conf.Check` для AST-файлов.",
        "Проверить связывание идентификатора вызова метода с его семантическим объектом `types.Func`.",
        "Определить разницу между интерфейсным типом и конкретной структурой."
    ],
    "code_blocks": [
        {
            "filename": "types_semantics.go",
            "lang": "go",
            "code": code4
        }
    ],
    "under_the_hood": "Внутри `go/types` объекты типов представлены интерфейсом `types.Type` и его конкретными реализациями: `*types.Basic` (int, string), `*types.Named` (пользовательские типы), `*types.Pointer`, `*types.Struct`, `*types.Interface`, `*types.Signature` (функции). Это позволяет линтеру с идеальной точностью анализировать структуры данных.",
    "pitfalls": [
        "Обращение к `pass.TypesInfo.Types[expr]` для выражений, не вычисляющих значение (например, метка перехода label: вернет отсутствие ключа).",
        "Попытка сравнения типов через оператор `==` вместо `types.Identical(t1, t2)` (для именованных типов прямое сравнение может дать сбой из-за разных экземпляров пакетов).",
        "Необработанный `nil` при вызове `pass.TypesInfo.TypeOf(expr)`."
    ],
    "bigtech_interview": "Как в анализаторе проверить, возвращает ли функция тип `error`? Ответ: 1) Получить сигнатуру функции `sig := obj.Type().(*types.Signature)`; 2) Проверить результаты `results := sig.Results()`; 3) Если `results.Len() > 0`, взять тип последнего параметра `lastType := results.At(results.Len()-1).Type()`; 4) Проверить совпадение с встроенным типом ошибки через `types.Identical(lastType, types.Universe.Lookup(\"error\").Type())`."
})

# Ex 5: Создание первого статического анализатора на Go
code5 = r'''package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
)

// DummyReport сообщение линтера
type DummyReport struct {
	Pos     token.Pos
	Message string
}

// CheckEmptyFunctions обходит AST и находит пустые функции
func CheckEmptyFunctions(fset *token.FileSet, file *ast.File) []DummyReport {
	var reports []DummyReport

	for _, decl := range file.Decls {
		fn, ok := decl.(*ast.FuncDecl)
		if !ok || fn.Body == nil {
			continue
		}

		// Если список операторов в теле функции пуст
		if len(fn.Body.List) == 0 {
			reports = append(reports, DummyReport{
				Pos:     fn.Pos(),
				Message: fmt.Sprintf("функция '%s' имеет пустое тело", fn.Name.Name),
			})
		}
	}

	return reports
}

func main() {
	fmt.Println("=== Создание первого статического анализатора (noempty) ===")
	src := `
package testpkg

func ValidFunction() {
	println("doing work")
}

func SuspiciousEmpty() {}
`
	fset := token.NewFileSet()
	file, _ := parser.ParseFile(fset, "test.go", src, 0)

	findings := CheckEmptyFunctions(fset, file)
	for _, f := range findings {
		pos := fset.Position(f.Pos)
		fmt.Printf("⚠️  [%s:%d] %s\n", pos.Filename, pos.Line, f.Message)
	}
}
'''

validate_go_code(code5, "code5")
exercises.append({
    "num": 5,
    "title": "Создание первого статического анализатора на Go",
    "task": "Напишите свой первый статический анализатор noempty: анализатор сканирует объявления функций *ast.FuncDecl, проверяет количество операторов в блоке fn.Body.List и формирует диагностическое предупреждение, если тело функции пусто (len(fn.Body.List) == 0).",
    "theory": "Создание собственного линтера начинается с формулирования простого синтаксического инварианта.\n\nВ Go функция с пустым телом `func DoSomething() {}` часто является забытой заглушкой (TODO stub), ошибочно оставленной разработчиком в коде перед релизом.\n\nКаноничная структура анализатора в терминах `go/analysis`:\n```go\nvar Analyzer = &analysis.Analyzer{\n    Name: \"noempty\",\n    Doc:  \"находит функции с пустым телом\",\n    Run:  run,\n}\n\nfunc run(pass *analysis.Pass) (interface{}, error) {\n    for _, file := range pass.Files {\n        // Обход AST\n    }\n    return nil, nil\n}\n```\nФункция `run` итерируется по всем файлам пакета `pass.Files`, фильтрует объявления `*ast.FuncDecl` и сообщает об ошибках вызовом `pass.Reportf(fn.Pos(), \"сообщение\")`.",
    "step_by_step": [
        "Объявить глобальную переменную дескриптора `analysis.Analyzer`.",
        "Реализовать функцию `run(pass *analysis.Pass)`.",
        "Отфильтровать узлы `*ast.FuncDecl`, исключая прототипы интерфейсов без тела (`fn.Body == nil`).",
        "Проверить условие `len(fn.Body.List) == 0` и зарегистрировать диагностику."
    ],
    "code_blocks": [
        {
            "filename": "noempty_analyzer.go",
            "lang": "go",
            "code": code5
        }
    ],
    "under_the_hood": "Когда вызывается `pass.Reportf(pos, ...)`, фреймворк `go/analysis` автоматически использует внутренний `pass.Fset` для преобразования целочисленного `token.Pos` в файл, строку и столбец. Это гарантирует точную интеграцию с редакторами кода VS Code / GoLand / Cursor.",
    "pitfalls": [
        "Паника разыменования nil-указателя на внешних объявлениях функций без тела (например, в ассемблерных функциях или CGO: `func Syscall()` имеет `fn.Body == nil`).",
        "Срабатывание на функции, содержащие только комментарии (комментарии не входят в `fn.Body.List`, поэтому тело формально пусто).",
        "Регистрация ошибки на методах-заглушках, реализующих интерфейс с явным комментарием `// no-op`."
    ],
    "bigtech_interview": "Как отличить забытую пустую функцию от осознанной заглушки `// no-op`? Ответ: В AST к файлу привязан список комментариев `file.Comments`. Анализатор может проверить, попадает ли позиция комментария внутрь диапазона `[fn.Body.Lbrace, fn.Body.Rbrace]`. Если внутри скобок есть комментарий, содержащий маркер `no-op` или `stub`, анализатор игнорирует функцию."
})

# Ex 6: Обход AST с помощью ast.Inspect
code6 = r'''package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
)

// RunInspectDemo демонстрирует рекурсивный обход AST функцией ast.Inspect
func RunInspectDemo() {
	src := `
package main

func Outer() {
	println("outer")
	fn := func() {
		println("inner closure")
	}
	fn()
}
`
	fset := token.NewFileSet()
	file, _ := parser.ParseFile(fset, "main.go", src, 0)

	totalNodes := 0
	callCount := 0

	// ast.Inspect рекурсивно обходит дерево в глубину (Depth-First Search)
	ast.Inspect(file, func(n ast.Node) bool {
		if n == nil {
			return false // Вызывается при выходе из узла
		}
		totalNodes++

		// Если встретили вызов функции
		if call, ok := n.(*ast.CallExpr); ok {
			callCount++
			pos := fset.Position(call.Pos())
			fmt.Printf("Найден вызов функции в строке %d\n", pos.Line)
		}

		// Возврат true означает: продолжать спускаться вглубь дочерних узлов
		// Возврат false остановил бы обход текущей подветки дерева!
		return true
	})

	fmt.Printf("Всего обойдено узлов AST: %d, вызовов функций: %d\n", totalNodes, callCount)
}

func main() {
	fmt.Println("=== Рекурсивный обход AST с помощью ast.Inspect ===")
	RunInspectDemo()
}
'''

validate_go_code(code6, "code6")
exercises.append({
    "num": 6,
    "title": "Обход AST с помощью ast.Inspect",
    "task": "Изучите стандартную функцию рекурсивного обхода дерева ast.Inspect(node ast.Node, f func(ast.Node) bool): покажите, как остановить спуск в ненужные поддеревья возвратом false (например, пропуск инспекции внутренних тел анонимных функций или структур) и как обрабатывать выход из узла при n == nil.",
    "theory": "Вместо ручного написания рекурсивных функций обхода десятков типов узлов `go/ast` предоставляет стандартную функцию высшего порядка `ast.Inspect`.\n\nСигнатура:\n`ast.Inspect(node ast.Node, f func(ast.Node) bool)`\n\nМеханика работы:\n1) Функция `f` вызывается для каждого узла дерева в порядке обхода в глубину (DFS — Depth-First Search);\n2) Если `f` возвращает **`true`**, `ast.Inspect` продолжает спуск во всех потомков текущего узла;\n3) Если `f` возвращает **`false`**, обход дочерних элементов этого узла прекращается (pruning subtrees). Это критически важно для производительности;\n4) После того как все дети узла обойдены, функция `f` вызывается повторно со значением `n == nil`, что позволяет реализовать логику выхода из контекста (exit hook, аналог закрывающей скобки).",
    "step_by_step": [
        "Изучить сигнатуру и контракт функции `ast.Inspect`.",
        "Реализовать фильтрацию по типу узла через type-assertion `n.(*ast.CallExpr)`.",
        "Продемонстрировать отсечение поддерева возвратом `false`.",
        "Использовать условие `n == nil` для очистки состояния стека обхода."
    ],
    "code_blocks": [
        {
            "filename": "ast_inspect.go",
            "lang": "go",
            "code": code6
        }
    ],
    "under_the_hood": "Под капотом `ast.Inspect` вызывает `ast.Walk`. В `ast.Walk` реализован колоссальный оператор `switch` по всем 50+ типам AST-узлов языка Go, вызывающий `Walk` для всех непустых полей структуры. Возврат `false` предотвращает вызовы для вложенных узлов, экономя такты CPU.",
    "pitfalls": [
        "Забытая проверка `if n == nil { return false }`: попытка разыменовать `n.Pos()` при выходе из узла вызовет панику `nil pointer dereference`.",
        "Случайный возврат `false` на корневом узле `*ast.File` (обход завершится немедленно, не проверив ни одной строчки кода).",
        "Чрезмерная глубина стека вызовов при обработке гигантских сгенерированных файлов."
    ],
    "bigtech_interview": "Как в `ast.Inspect` запретить линтеру заходить внутрь тел тестовых функций `TestXxx(t *testing.T)`? Ответ: При встрече узла `*ast.FuncDecl` проверить, начинается ли его имя с `Test` и лежит ли файл в `_test.go`. Если да — вернуть `false`. Это исключит все дерево тела тестовой функции из инспекции."
})

# Ex 7: Регистрация предупреждений и позиционирование в коде
code7 = r'''package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
)

// SourceCodeReporter демонстрирует точное позиционирование диагностик
type SourceCodeReporter struct {
	fset *token.FileSet
}

func (r *SourceCodeReporter) Report(pos token.Pos, format string, args ...interface{}) {
	position := r.fset.Position(pos)
	msg := fmt.Sprintf(format, args...)
	// Формат, стандартизированный для компиляторов и линтеров: filename:line:column: message
	fmt.Printf("%s:%d:%d: %s\n", position.Filename, position.Line, position.Column, msg)
}

func main() {
	fmt.Println("=== Позиционирование в коде с token.FileSet и Reportf ===")
	src := `package main

func main() {
	var unusedVariable = 42
}
`
	fset := token.NewFileSet()
	file, _ := parser.ParseFile(fset, "app/main.go", src, 0)
	reporter := &SourceCodeReporter{fset: fset}

	// Найдем неиспользуемую переменную
	ast.Inspect(file, func(n ast.Node) bool {
		if valSpec, ok := n.(*ast.ValueSpec); ok {
			for _, id := range valSpec.Names {
				if id.Name == "unusedVariable" {
					reporter.Report(id.Pos(), "переменная '%s' объявлена, но не используется", id.Name)
				}
			}
		}
		return true
	})
}
'''

validate_go_code(code7, "code7")
exercises.append({
    "num": 7,
    "title": "Регистрация предупреждений и позиционирование в коде",
    "task": "Изучите механику перевода абстрактных смещений token.Pos в точные координаты исходного кода (имя файла, номер строки и колонки) через token.FileSet. Реализуйте метод логирования предупреждений в каноничном формате компилятора Go filename:line:column: message.",
    "theory": "Для эффективности представления памяти компилятор Go не хранит строки и имена файлов в каждом синтаксическом узле AST. Вместо этого используется глобальная непрерывная числовая ось смещений — тип `token.Pos` (по сути, обычный `int`).\n\nСтруктура `token.FileSet` управляет этой осью:\n1) Каждый распарсенный файл занимает определенный диапазон смещений `[base, base + size]`;\n2) Для любого `node.Pos()` метод `fset.Position(pos)` выполняет бинарный поиск по файлам и вычисляет:\n   - `Filename string`: относительный или абсолютный путь к файлу;\n   - `Line int`: точный номер строки (1-based);\n   - `Column int`: номер символа в строке (1-based).\n\nВ `go/analysis` метод `pass.Reportf(node.Pos(), format, args...)` автоматически производит это преобразование и формирует диагностику `analysis.Diagnostic`.",
    "step_by_step": [
        "Изучить природу компактного числового типа `token.Pos`.",
        "Использовать `pass.Fset.Position(pos)` для получения структуры `token.Position`.",
        "Сформировать вывод в каноничном формате компилятора UNIX.",
        "Убедиться, что позиция указывает на начало идентификатора ошибки, а не на весь блок."
    ],
    "code_blocks": [
        {
            "filename": "source_reporter.go",
            "lang": "go",
            "code": code7
        }
    ],
    "under_the_hood": "Хранение одного 32/64-битного `token.Pos` вместо структуры `{File, Line, Col}` в каждом из миллионов узлов AST экономит до 70% оперативной памяти при разборе больших проектов.",
    "pitfalls": [
        "Передача `node.End()` вместо `node.Pos()`: предупреждение подсветит конец функции или файла вместо проблемного места.",
        "Использование чужого `token.FileSet`, не связанного с текущим сеансом парсинга (вернет мусорные или отрицательные номера строк).",
        "Некорректная обработка сгенерированных файлов с директивами `//line`."
    ],
    "bigtech_interview": "Почему `pass.ReportRangef` лучше, чем обычный `pass.Reportf`? Ответ: `pass.ReportRangef(node, ...)` принимает узел целиком (с Pos() и End()), что позволяет современным IDE (VS Code, GoLand) подсветить волнистой линией точный диапазон проблемного выражения целиком, а не только первый символ."
})

# Ex 8: Фреймворк тестирования анализаторов: analysistest
code8 = r'''package main

import (
	"fmt"
)

// ExplainAnalysisTest иллюстрирует методологию тестирования линтеров Go
func ExplainAnalysisTest() {
	fmt.Println("=== Фреймворк тестирования analysistest в Go ===")
	fmt.Println()
	fmt.Println("Стандартный подход к тестированию линтеров на базе go/analysis:")
	fmt.Println("1. Структура тестовых каталогов:")
	fmt.Println("   myanalyzer/")
	fmt.Println("   ├── analyzer.go")
	fmt.Println("   ├── analyzer_test.go")
	fmt.Println("   └── testdata/src/a/")
	fmt.Println("       └── sample.go")
	fmt.Println()
	fmt.Println("2. Содержимое testdata/src/a/sample.go с маркерными комментариями:")
	fmt.Println("   package a")
	fmt.Println("   func BadFunction() {} // want \"функция имеет пустое тело\"")
	fmt.Println("   func GoodFunction() { println(\"ok\") }")
	fmt.Println()
	fmt.Println("3. Тестовый файл analyzer_test.go:")
	fmt.Println("   func TestAnalyzer(t *testing.T) {")
	fmt.Println("       testdata := analysistest.TestData()")
	fmt.Println("       analysistest.Run(t, testdata, myanalyzer.Analyzer, \"a\")")
	fmt.Println("   }")
	fmt.Println()
	fmt.Println("Механика: analysistest.Run компилирует тестовый пакет 'a', запускает анализатор")
	fmt.Println("и сверяет текст и номера строк сообщений с комментариями // want.")
}

func main() {
	ExplainAnalysisTest()
}
'''

validate_go_code(code8, "code8")
exercises.append({
    "num": 8,
    "title": "Фреймворк тестирования анализаторов: analysistest",
    "task": "Изучите специализированный фреймворк тестирования статических анализаторов golang.org/x/tools/go/analysis/analysistest. Разберите структуру каталогов testdata/src/, использование специальных маркерных комментариев // want 'regexp' и написание юнит-тестов с помощью analysistest.Run.",
    "theory": "Тестирование статических анализаторов требует проверки двух вещей: 1) Линтер находит ошибку именно там, где она есть (True Positive); 2) Линтер молчит там, где код написан корректно (True Negative / No False Positives).\n\nПакет `analysistest` автоматизирует этот процесс через декларативные тесты:\n1) Создается директория `testdata/src/<pkgname>/`;\n2) Внутри пишутся реальные `.go` файлы с правильным и ошибочным кодом;\n3) На строках, где анализатор ДОЛЖЕН выдать предупреждение, добавляется специальный комментарий:\n`// want \"текст ошибки или регулярное выражение\"`\n4) В юнит-тесте вызывается:\n```go\nfunc TestMyAnalyzer(t *testing.T) {\n    testdata := analysistest.TestData()\n    analysistest.Run(t, testdata, myanalyzer.Analyzer, \"pkgname\")\n}\n```\nЕсли анализатор выдаст ошибку не на той строке, выдаст лишнюю ошибку или текст не совпадет с `// want`, тест упадет с подробным diff.",
    "step_by_step": [
        "Создать структуру каталога `testdata/src/a` в репозитории линтера.",
        "Написать тестовые кейсы с валидными и невалидными конструкциями Go.",
        "Разместить маркеры `// want \"...\"` на целевых строках.",
        "Запустить тест через стандартный `go test ./...` и убедиться в 100% покрытии правил."
    ],
    "code_blocks": [
        {
            "filename": "analysistest_guide.go",
            "lang": "go",
            "code": code8
        }
    ],
    "under_the_hood": "`analysistest` создает виртуальное окружение GOPATH/Go Modules в папке `testdata`, парсит комментарии специальным лексером и сопоставляет позиции `pass.Reportf` с позициями комментариев `want`.",
    "pitfalls": [
        "Неправильный синтаксис комментария (например, `//want` без пробела или опечатка в кавычках).",
        "Пропуск тестирования валидных случаев (тест должен доказывать отсутствие ложных срабатываний).",
        "Различия в путях на Windows и Linux при работе с `analysistest.TestData()`."
    ],
    "bigtech_interview": "Почему маркерный подход `// want` лучше ручной проверки слайса диагностик `assert.Equal(t, reports)`? Ответ: Потому что тест становится самодокументируемым примером кода: разработчик видит исходный Go-код и прямо напротив проблемной строки видит ожидаемое сообщение линтера, что делает поддержку сотен тест-кейсов тривиальной."
})

# Ex 9: Линтер 1: Запрет context.Background() вне main() и тестов
code9 = r'''package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"strings"
)

// CheckNoBackground находит вызовы context.Background() в бизнес-коде
func CheckNoBackground(fset *token.FileSet, file *ast.File, filename string) []string {
	var issues []string

	// Исключаем тесты
	if strings.HasSuffix(filename, "_test.go") {
		return nil
	}

	ast.Inspect(file, func(n ast.Node) bool {
		// Исключаем функцию main()
		if fn, ok := n.(*ast.FuncDecl); ok && fn.Name.Name == "main" {
			return false // Не заходим внутрь main()
		}

		call, ok := n.(*ast.CallExpr)
		if !ok {
			return true
		}

		// Проверяем селектор: context.Background() или context.TODO()
		if sel, ok := call.Fun.(*ast.SelectorExpr); ok {
			if ident, ok := sel.X.(*ast.Ident); ok && ident.Name == "context" {
				if sel.Sel.Name == "Background" || sel.Sel.Name == "TODO" {
					pos := fset.Position(call.Pos())
					issues = append(issues, fmt.Sprintf("%s:%d: запрещен вызов context.%s() в бизнес-логике; передавайте входящий ctx первым аргументом",
						pos.Filename, pos.Line, sel.Sel.Name))
				}
			}
		}
		return true
	})

	return issues
}

func main() {
	fmt.Println("=== Линтер nobackground: Запрет context.Background() ===")
	src := `package service

import "context"

func ProcessOrder() {
	ctx := context.Background() // Ошибка!
	_ = ctx
}

func main() {
	ctx := context.Background() // Разрешено в main
	_ = ctx
}
`
	fset := token.NewFileSet()
	file, _ := parser.ParseFile(fset, "service/order.go", src, 0)

	findings := CheckNoBackground(fset, file, "service/order.go")
	for _, f := range findings {
		fmt.Println("🚨", f)
	}
}
'''

validate_go_code(code9, "code9")
exercises.append({
    "num": 9,
    "title": "Линтер 1: Запрет context.Background() вне main() и тестов",
    "task": "В микросервисной архитектуре создание нового context.Background() или context.TODO() внутри бизнес-слоя разрывает цепочку контекстов: теряются таймауты, отмены и trace ID OpenTelemetry. Разработайте анализатор nobackground: запретите вызовы context.Background() и context.TODO() везде, кроме функций main() и тестовых файлов *_test.go.",
    "theory": "Контекст (`context.Context`) в Go предназначен для сквозной передачи сигналов отмены, дедлайнов и метаданных трассировки через все уровни приложения.\n\nКогда разработчик внутри сервисного метода вызывает `ctx := context.Background()` вместо того, чтобы принять `ctx context.Context` первым параметром функции:\n1) Разрывается распределенная трассировка (Distributed Tracing): Jaeger/OpenTelemetry Spans теряют связь с родительским трейсом;\n2) Игнорируется отмена клиентского HTTP/gRPC запроса (сервер продолжает молотить тяжелый SQL-запрос, хотя клиент уже закрыл вкладку браузера);\n3) Перестают работать глобальные таймауты деградации.\n\nЛинтер `nobackground` обходит AST и пресекает создание контекстов на корню во всех бизнес-пакетах компании.",
    "step_by_step": [
        "Исключить из проверки тестовые файлы с суффиксом `_test.go`.",
        "Исключить из проверки функцию верхнего уровня `func main()`.",
        "Обнаружить вызовы `*ast.CallExpr`, где функция является `*ast.SelectorExpr` с `X == \"context\"`.",
        "Заблокировать методы `Background` и `TODO` с требованием проброса контекста через параметры."
    ],
    "code_blocks": [
        {
            "filename": "nobackground_analyzer.go",
            "lang": "go",
            "code": code9
        }
    ],
    "under_the_hood": "Для 100% надежности анализатор должен проверять не просто строковое имя `\"context\"`, а семантический пакет через `pass.TypesInfo.Uses[ident]`. Это предотвратит ложные срабатывания, если разработчик создал локальную переменную с именем `context`.",
    "pitfalls": [
        "Блокировка легитимных вызовов в фоновых worker-демонах (для фоновых задач должен использоваться контролируемый корневой контекст приложения `appCtx`).",
        "Пропуск алиасов импорта (например, `import ctxpkg \"context\"`).",
        "Блокировка контекста в тестах."
    ],
    "bigtech_interview": "Почему в Google запрещено использовать `context.TODO()` в коде master-ветки? Ответ: `context.TODO()` задумывался как временная заглушка в процессе рефакторинга. Оставленный на проде, он означает, что разработчик не знал, откуда взять контекст, и проигнорировал таймауты. Линтер в CI Google блокирует коммиты с `context.TODO()`, заставляя инженера явно прокинуть контекст."
})

# Ex 10: Линтер 2: Запрет хранения context.Context в структурах
code10 = r'''package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
)

// CheckStructContext проверяет, чтобы context.Context не хранился в полях структур
func CheckStructContext(fset *token.FileSet, file *ast.File) []string {
	var issues []string

	ast.Inspect(file, func(n ast.Node) bool {
		structType, ok := n.(*ast.StructType)
		if !ok || structType.Fields == nil {
			return true
		}

		for _, field := range structType.Fields.List {
			// Проверяем тип поля: context.Context
			if sel, ok := field.Type.(*ast.SelectorExpr); ok {
				if ident, ok := sel.X.(*ast.Ident); ok && ident.Name == "context" && sel.Sel.Name == "Context" {
					pos := fset.Position(field.Pos())
					fieldName := "(anonymous)"
					if len(field.Names) > 0 {
						fieldName = field.Names[0].Name
					}
					issues = append(issues, fmt.Sprintf("%s:%d: поле '%s' имеет запрещенный тип context.Context; передавайте context аргументом в методы",
						pos.Filename, pos.Line, fieldName))
				}
			}
		}
		return true
	})

	return issues
}

func main() {
	fmt.Println("=== Линтер structcontext: Запрет context в структурах ===")
	src := `package repository

import "context"

type BadRepository struct {
	ctx context.Context // Запрещено официальным Go Code Review Comments!
	db  string
}

type GoodRepository struct {
	db string
}
`
	fset := token.NewFileSet()
	file, _ := parser.ParseFile(fset, "repo.go", src, 0)

	findings := CheckStructContext(fset, file)
	for _, f := range findings {
		fmt.Println("🚨", f)
	}
}
'''

validate_go_code(code10, "code10")
exercises.append({
    "num": 10,
    "title": "Линтер 2: Запрет хранения context.Context в структурах",
    "task": "Официальный гайдлайн Go Code Review Comments гласит: «Do not store Contexts inside a struct type; instead, pass a Context explicitly to each function that needs it». Разработайте линтер structcontext: анализатор инспектирует ast.StructType и сообщает об ошибке, если поле структуры имеет тип context.Context.",
    "theory": "Хранение `context.Context` внутри полей структуры — один из самых коварных антипаттернов в Go.\n\nПочему это опасно:\n1) **Жизненный цикл**: Структура (например, сервис `UserService` или репозиторий `OrderRepo`) создается один раз при старте приложения (Singleton) и живет часами/днями. Контекст же привязан к конкретному HTTP-запросу и живет 50 миллисекунд. Сохранение контекста запроса в сервис приводит к сохранению мертвого отмененного контекста для всех последующих пользователей;\n2) **Гонки данных (Data Races)**: Если структура используется параллельно десятками горутин, замена контекста в поле структуры приведет к немедленной гонке данных;\n3) **Утечки памяти**: Контекст хранит ссылки на горутины и значения, препятствуя их очистке Garbage Collector.\n\nЕдинственное исключение — структуры DTO сообщений или команд, но не сервисы.",
    "step_by_step": [
        "Обнаружить синтаксические узлы объявления структур `*ast.StructType`.",
        "Пройти по полям структуры `structType.Fields.List`.",
        "Проверить тип поля на селектор `context.Context`.",
        "Вывести предупреждение с рекомендацией передавать контекст первым параметром методов."
    ],
    "code_blocks": [
        {
            "filename": "structcontext_analyzer.go",
            "lang": "go",
            "code": code10
        }
    ],
    "under_the_hood": "Правило 'Contexts should not be stored in structs' проверяется также стандартным линтером `containedctx`. Наш кастомный анализатор расширяет его, позволяя настраивать белый список структур (например, разрешать контекст в типах `http.Request`).",
    "pitfalls": [
        "Блокировка `http.Request`: стандартная структура библиотеки Go содержит поле `ctx context.Context` (нужно добавить исключение).",
        "Пропуск встроенных (embedded) анонимных полей `context.Context`.",
        "Пропуск алиасов контекста через typedef."
    ],
    "bigtech_interview": "Почему в стандартной структуре `http.Request` есть поле `ctx context.Context`, если гайдлайны Go это запрещают? Ответ: Это исторический компромисс обратной совместимости. Пакет `context` был добавлен в стандартную библиотеку только в Go 1.7, когда сигнатура `http.Handler.ServeHTTP(ResponseWriter, *Request)` уже была зафиксирована обещанием Go 1 Compatibility Promise. Чтобы не ломать миллиарды строк существующего кода, контекст встроили прямо в `*http.Request` через методы `Context()` и `WithContext()`."
})

# Ex 11: Линтер 3: Детекция пропущенных проверок ошибок (unhandled errors)
code11 = r'''package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
)

// CheckUnhandledErrors находит игнорирование возвращаемых ошибок
func CheckUnhandledErrors(fset *token.FileSet, file *ast.File) []string {
	var issues []string

	ast.Inspect(file, func(n ast.Node) bool {
		// 1. Случай вызова функции как отдельного оператора: fn()
		if exprStmt, ok := n.(*ast.ExprStmt); ok {
			if call, ok := exprStmt.X.(*ast.CallExpr); ok {
				pos := fset.Position(call.Pos())
				issues = append(issues, fmt.Sprintf("%s:%d: результат вызова функции игнорируется (возможна потеря error)",
					pos.Filename, pos.Line))
			}
		}

		// 2. Случай явного сброса в blank identifier: _ = fn()
		if assign, ok := n.(*ast.AssignStmt); ok {
			if len(assign.Lhs) == 1 {
				if ident, ok := assign.Lhs[0].(*ast.Ident); ok && ident.Name == "_" {
					pos := fset.Position(assign.Pos())
					issues = append(issues, fmt.Sprintf("%s:%d: явный сброс результата в '_' запрещен правилами надежности",
						pos.Filename, pos.Line))
				}
			}
		}

		return true
	})

	return issues
}

func main() {
	fmt.Println("=== Линтер checkerr: Детекция пропущенных ошибок ===")
	src := `package main

import "os"

func BadWorker() {
	os.Remove("/tmp/file") // Ошибка игнорируется!

	_ = os.Chmod("/tmp/file", 0777) // Ошибка сброшена в blank identifier!
}
`
	fset := token.NewFileSet()
	file, _ := parser.ParseFile(fset, "worker.go", src, 0)

	findings := CheckUnhandledErrors(fset, file)
	for _, f := range findings {
		fmt.Println("🚨", f)
	}
}
'''

validate_go_code(code11, "code11")
exercises.append({
    "num": 11,
    "title": "Линтер 3: Детекция пропущенных проверок ошибок (unhandled errors)",
    "task": "Игнорирование ошибок — первопричина 'тихого падения' сервисов под нагрузкой. Разработайте анализатор checkerr: находит вызовы функций, возвращающих тип error, результат которых либо полностью игнорируется fn(), либо явно сбрасывается в пустой идентификатор _ = fn().",
    "theory": "В Go ошибки являются обычными значениями, возвращаемыми функциями. Язык намеренно не имеет механизма исключений (try/catch), требуя явной обработки.\n\nОднако разработчики иногда забывают обработать ошибку или сознательно пишут `_ = file.Close()`, надеясь, что 'здесь ошибки быть не может'. На практике игнорирование ошибок при закрытии файлов приводит к потере недозаписанных на диск буферов, а игнорирование ошибок сетевых вызовов порождает скрытое повреждение данных (Silent Corruption).\n\nЛинтер `checkerr` (аналог популярного `errcheck`) использует комбинацию AST и `go/types`:\n1) Находит все операторы-вызовы `*ast.ExprStmt` и присваивания `*ast.AssignStmt` с `_`;\n2) Через `pass.TypesInfo.Types[call]` проверяет сигнатуру возвращаемого типа;\n3) Если среди возвращаемых значений есть тип `error`, регистрирует блокирующую ошибку.",
    "step_by_step": [
        "Обнаружить одиночные вызовы функций в виде операторов `ast.ExprStmt`.",
        "Обнаружить присваивания в пустой идентификатор `_` в `ast.AssignStmt`.",
        "Использовать информацию о типах `types.Info` для фильтрации функций, действительно возвращающих `error`.",
        "Реализовать исключения для безопасных функций стандартной библиотеки (например, `fmt.Println`)."
    ],
    "code_blocks": [
        {
            "filename": "checkerr_analyzer.go",
            "lang": "go",
            "code": code11
        }
    ],
    "under_the_hood": "Проверка типа ошибки выполняется вызовом компилятора: `types.Implements(returnType, errorInterface)`. Если возвращается множественный кортеж `(int, error)`, анализатор инспектирует последний элемент кортежа `types.Tuple`.",
    "pitfalls": [
        "Предупреждения на вызовы `fmt.Printf` или `fmt.Fprintln`, которые формально возвращают error, но в 99.9% случаев не требуют обработки в консоли (требуется белый список исключений).",
        "Пропуск обработки ошибок внутри операторов `go fn()` и `defer fn()`.",
        "Ложные срабатывания на функциях, возвращающих статус `bool`, а не `error`."
    ],
    "bigtech_interview": "Почему игнорирование ошибки `defer file.Close()` в Go может привести к потере данных? Ответ: Операционная система сбрасывает данные из буфера файлового кэша на физический диск в момент закрытия дескриптора. Если на диске закончилось место (No space left on device) или произошел сбой сети в NFS, системный вызов close() вернет ошибку записи. Если Go-код проигнорировал ошибку Close(), приложение считает файл успешно сохраненным, тогда как данные были потеряны."
})

# Ex 12: Линтер 4: Контроль слоев Clean Architecture (Layer Imports)
code12 = r'''package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"strings"
)

// CleanArchRule задает правила изоляции слоев
type CleanArchRule struct {
	ForbiddenImportPrefix string
	Reason                string
}

// CheckCleanArchLayers проверяет соблюдение правила зависимостей
func CheckCleanArchLayers(fset *token.FileSet, file *ast.File, filePath string) []string {
	var issues []string

	// Проверяем, находится ли файл в доменном слое
	if !strings.Contains(filePath, "/domain/") {
		return nil
	}

	// Запрещенные импорты для доменного слоя
	forbidden := []CleanArchRule{
		{ForbiddenImportPrefix: "mycompany/pkg/infrastructure", Reason: "Доменный слой не должен зависеть от инфраструктуры"},
		{ForbiddenImportPrefix: "mycompany/pkg/database", Reason: "Доменный слой не должен зависеть от базы данных"},
		{ForbiddenImportPrefix: "database/sql", Reason: "Доменный слой не должен зависеть от драйверов SQL"},
	}

	for _, imp := range file.Imports {
		importPath := strings.Trim(imp.Path.Value, `"`)
		for _, rule := range forbidden {
			if strings.HasPrefix(importPath, rule.ForbiddenImportPrefix) {
				pos := fset.Position(imp.Pos())
				issues = append(issues, fmt.Sprintf("%s:%d: нарушение Чистой Архитектуры: импорт '%s' запрещен в домене (%s)",
					pos.Filename, pos.Line, importPath, rule.Reason))
			}
		}
	}

	return issues
}

func main() {
	fmt.Println("=== Архитектурный линтер: Контроль слоев Clean Architecture ===")
	src := `package domain

import (
	"context"
	"database/sql" // Нарушение!
)

type User struct {
	ID string
}
`
	fset := token.NewFileSet()
	file, _ := parser.ParseFile(fset, "internal/domain/user.go", src, 0)

	findings := CheckCleanArchLayers(fset, file, "internal/domain/user.go")
	for _, f := range findings {
		fmt.Println("🚨", f)
	}
}
'''

validate_go_code(code12, "code12")
exercises.append({
    "num": 12,
    "title": "Линтер 4: Контроль слоев Clean Architecture (Layer Imports)",
    "task": "Архитектурное правило гласит: внутренние слои Чистой Архитектуры (Domain, Entities, Use Cases) ничего не знают о внешних слоях (Database, HTTP, Infrastructure). Разработайте линтер cleanarch: анализатор проверяет директивы импорта файлов в пакетах /domain/ и запрещает импорт пакетов infrastructure, database или database/sql.",
    "theory": "Чистая Архитектура (Clean Architecture / Onion / Hexagonal) держится на **Принципе Инверсии Зависимостей (Dependency Inversion Principle)**:\nСтрелки зависимостей в кодовой базе должны быть направлены СТРОГО СНАРУЖИ ВНУТРЬ. Доменный слой ядра бизнеса (`domain`) должен зависеть только от чистого языка Go и не иметь никаких внешних зависимостей.\n\nНа практике разработчики часто срезают углы: импортируют драйвер PostgreSQL (`database/sql`), Redis или клиент Kafka прямо в доменные структуры. В результате доменное ядро оказывается жестко привязано к конкретным технологиям, а модульное тестирование бизнес-логики без поднятия баз данных становится невозможным.\n\nАрхитектурный линтер анализирует `ast.ImportSpec` и физический путь к файлу: если файл находится в `/domain/`, любые импорты инфраструктурных пакетов немедленно прерывают билд.",
    "step_by_step": [
        "Определить принадлежность анализируемого файла к доменному слою по его пути.",
        "Итерироваться по списку директив импорта `file.Imports`.",
        "Сопоставить очищенный путь импорта `imp.Path.Value` с черным списком инфраструктурных модулей.",
        "Вывести строгое сообщение об ошибке с пояснением принципа инверсии зависимостей."
    ],
    "code_blocks": [
        {
            "filename": "cleanarch_linter.go",
            "lang": "go",
            "code": code12
        }
    ],
    "under_the_hood": "В крупных корпоративных системах (например, uber-go/nilaway или bazel visibility) контроль границ пакетов реализуется декларативными правилами package boundary rules, запрещающими циклические и обратные зависимости на уровне графа сборки.",
    "pitfalls": [
        "Проверка только локальных путей без учета полного имени модуля из `go.mod`.",
        "Использование относительных путей `../infrastructure` (в Go запрещено, но должно валидироваться).",
        "Отсутствие исключений для чисто служебных пакетов общего назначения (`time`, `errors`, `math`)."
    ],
    "bigtech_interview": "Как в Clean Architecture доменный слой взаимодействует с базой данных, если ему запрещено импортировать пакет базы данных? Ответ: Через интерфейсы (Ports and Adapters). Доменный слой объявляет интерфейс `type UserRepository interface { Save(u User) error }`. Внешний инфраструктурный пакет базы данных импортирует домен и РЕАЛИЗУЕТ этот интерфейс. В рантайме зависимость внедряется через Dependency Injection, удовлетворяя архитектурный контракт."
})

# Ex 13: Инспекция директив импорта (ast.ImportSpec)
code13 = r'''package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"strings"
)

// ImportPolicyValidator проверяет список разрешенных стандартных библиотек
type ImportPolicyValidator struct {
	allowedStdLib map[string]struct{}
}

func NewImportValidator() *ImportPolicyValidator {
	return &ImportPolicyValidator{
		allowedStdLib: map[string]struct{}{
			"context": {},
			"errors":  {},
			"fmt":     {},
			"time":    {},
			"strings": {},
		},
	}
}

func (v *ImportPolicyValidator) ValidateImports(fset *token.FileSet, file *ast.File) []string {
	var issues []string

	for _, imp := range file.Imports {
		path := strings.Trim(imp.Path.Value, `"`)

		// Если это сторонняя библиотека (содержит точку в первом сегменте домена)
		if strings.Contains(strings.Split(path, "/")[0], ".") {
			pos := fset.Position(imp.Pos())
			issues = append(issues, fmt.Sprintf("%s:%d: сторонняя библиотека '%s' запрещена в Core-пакете",
				pos.Filename, pos.Line, path))
			continue
		}

		// Проверка стандартной библиотеки по белому списку
		if _, ok := v.allowedStdLib[path]; !ok {
			pos := fset.Position(imp.Pos())
			issues = append(issues, fmt.Sprintf("%s:%d: пакет стандартной библиотеки '%s' не входит в разрешенный whitelist",
				pos.Filename, pos.Line, path))
		}
	}

	return issues
}

func main() {
	fmt.Println("=== Инспекция директив импорта (ast.ImportSpec) ===")
	src := `package core

import (
	"context"
	"net/http" // Запрещен whitelist'ом
	"github.com/google/uuid" // Сторонняя зависимость
)
`
	fset := token.NewFileSet()
	file, _ := parser.ParseFile(fset, "core/entity.go", src, 0)

	validator := NewImportValidator()
	findings := validator.ValidateImports(fset, file)
	for _, f := range findings {
		fmt.Println("🚨", f)
	}
}
'''

validate_go_code(code13, "code13")
exercises.append({
    "num": 13,
    "title": "Инспекция директив импорта (ast.ImportSpec)",
    "task": "Реализуйте глубокий анализ директив импорта ast.ImportSpec: различие стандартной библиотеки Go и внешних сторонних зависимостей, разбор путей импортов и фильтрацию по белому списку разрешенных пакетов (Whitelist) для критических модулей ядра.",
    "theory": "Узел `ast.ImportSpec` представляет единичную строку импорта внутри блока `import (...)`.\n\nСтруктура `ast.ImportSpec`:\n- `Path *ast.BasicLit`: строковый литерал пути (всегда содержит окружающие кавычки `\"net/http\"`, которые необходимо снимать через `strings.Trim(imp.Path.Value, \"\\\"\")` или `strconv.Unquote`);\n- `Name *ast.Ident`: опциональное локальное переименование импорта (alias), точка `.` для прямого импорта или подчеркивание `_` для сайд-эффект импорта;\n- `Doc *ast.CommentGroup`: комментарии над строкой импорта.\n\nПроверка структуры импортов позволяет отслеживать раздувание зависимостей (Dependency Bloat) и предотвращать попадание тяжелых фреймворков в легковесные библиотеки компании.",
    "step_by_step": [
        "Итерироваться по срезу `file.Imports`.",
        "Корректно извлечь путь через `strconv.Unquote`.",
        "Классифицировать путь: стандартная библиотека (без точки в первом сегменте) vs внешний репозиторий.",
        "Сопоставить путь с корпоративным белым списком разрешенных пакетов."
    ],
    "code_blocks": [
        {
            "filename": "import_inspector.go",
            "lang": "go",
            "code": code13
        }
    ],
    "under_the_hood": "В компиляторе Go стандартная библиотека определяется отсутствием точки `.` в первой компоненте пути (например, `math/rand` vs `github.com/pkg/errors`). Пакет `golang.org/x/tools/go/packages` использует это же правило для разделения stdlib и внешних модулей.",
    "pitfalls": [
        "Забытое удаление кавычек из `imp.Path.Value` (сравнение `\"fmt\"` со строкой `fmt` всегда вернет `false`).",
        "Игнорирование анонимных импортов `_ \"net/http/pprof\"` (сайд-эффект импорты несут особые риски безопасности).",
        "Обработка алиасов: если файл содержит `import h \"net/http\"`, `imp.Name.Name` будет `h`."
    ],
    "bigtech_interview": "Почему в production монорепозиториях часто запрещают точечные импорты `import . \"mypkg\"`? Ответ: Точечный импорт вываливает все экспортируемые идентификаторы чужого пакета в текущее пространство имен файла. Это делает чтение кода запутанным (непонятно, откуда взялась функция), порождает конфликты имен при обновлении библиотек и ломает рефакторинг в IDE."
})

# Ex 14: Линтер 5: Детекция неконтролируемых горутин (Unguarded Goroutines)
code14 = r'''package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
)

// CheckUnguardedGoroutines находит 'дикие' запуски горутин без надзора
func CheckUnguardedGoroutines(fset *token.FileSet, file *ast.File) []string {
	var issues []string

	ast.Inspect(file, func(n ast.Node) bool {
		goStmt, ok := n.(*ast.GoStmt)
		if !ok {
			return true
		}

		pos := fset.Position(goStmt.Pos())
		// Проверяем, что именно запускается: анонимная функция go func() или обычная функция
		switch callTarget := goStmt.Call.Fun.(type) {
		case *ast.FuncLit:
			issues = append(issues, fmt.Sprintf("%s:%d: обнаружена неконтролируемая анонимная горутина 'go func()'; используйте WorkerPool или sync.WaitGroup",
				pos.Filename, pos.Line))
		case *ast.Ident:
			issues = append(issues, fmt.Sprintf("%s:%d: запуск горутины 'go %s()'; убедитесь в наличии graceful shutdown и recover",
				pos.Filename, pos.Line, callTarget.Name))
		default:
			issues = append(issues, fmt.Sprintf("%s:%d: неконтролируемый запуск горутины", pos.Filename, pos.Line))
		}

		return true
	})

	return issues
}

func main() {
	fmt.Println("=== Линтер safego: Детекция неконтролируемых горутин ===")
	src := `package handler

func HandleRequest() {
	// Опасный запуск без WaitGroup и отслеживания контекста!
	go func() {
		println("async work")
	}()
}
`
	fset := token.NewFileSet()
	file, _ := parser.ParseFile(fset, "handler.go", src, 0)

	findings := CheckUnguardedGoroutines(fset, file)
	for _, f := range findings {
		fmt.Println("🚨", f)
	}
}
'''

validate_go_code(code14, "code14")
exercises.append({
    "num": 14,
    "title": "Линтер 5: Детекция неконтролируемых горутин (Unguarded Goroutines)",
    "task": "Запуск горутин через ключевое слово go func() без привязки к WaitGroup, Worker Pool или ErrGroup — частая причина утечек памяти и аварийного завершения сервиса при панике. Разработайте анализатор safego: находит все операторы ast.GoStmt и требует использования утвержденных корпоративных примитивов конкурентности.",
    "theory": "Горутины в Go дешевы (около 2 КБ стека), что провоцирует разработчиков запускать их бесконтрольно: `go sendEmail()`, `go updateMetrics()`.\n\nТри смертельных риска 'диких' горутин (Unguarded Goroutines):\n1) **Необработанная паника**: Если внутри горутины произойдет `panic` (например, nil pointer dereference), аварийно завершится ВЕСЬ Go-процесс, положив весь сервис в Kubernetes;\n2) **Утечка памяти и процессора (Goroutine Leak)**: Если горутина зависнет на вечном чтении небуферизованного канала или блокирующем сетевом сокете без таймаута, она останется в памяти навсегда;\n3) **Нарушение Graceful Shutdown**: При остановке пода Kubernetes неконтролируемые горутины будут грубо убиты операционной системой на середине записи в базу данных.\n\nЛинтер `safego` запрещает прямое использование ключевого слова `go`, принуждая инженеров использовать безопасные обертки (например, `pool.Go()`, `errgroup.Group` или корпоративный `safego.Go(func())` с встроенным `recover()`).",
    "step_by_step": [
        "Обнаружить узел запуска горутины `*ast.GoStmt`.",
        "Проверить вызываемое выражение `goStmt.Call`.",
        "Идентифицировать запуск анонимной функции `*ast.FuncLit`.",
        "Зарегистрировать предупреждение о нарушении корпоративного стандарта безопасной многопоточности."
    ],
    "code_blocks": [
        {
            "filename": "safego_analyzer.go",
            "lang": "go",
            "code": code14
        }
    ],
    "under_the_hood": "В рантайме Go паника в любой горутине, не перехваченная локальным `recover()`, поднимается до вершины стека горутины и вызывает `runtime.fatalpanic`, приводящий к мгновенному падению процесса (Exit Code 2). Защитить чужую горутину внешним `recover` невозможно, поэтому изоляция обязана быть внутри тела горутины.",
    "pitfalls": [
        "Ложные срабатывания на легитимном создании пула воркеров в функции `main()` или `init()`.",
        "Пропуск запусков через методы объектов `go s.worker()`.",
        "Отсутствие белого списка для одобренных библиотек конкурентности."
    ],
    "bigtech_interview": "Как в Ozon и Wildberries защищают серверы от падения при фоновых асинхронных задачах? Ответ: Запрещают сырое ключевое слово `go` линтером и обязывают использовать утилиту вида `safego.Go(ctx, func(ctx context.Context))`. Внутри этой функции автоматически делается `defer recover()` с отправкой стек-трейса в Sentry, логов в Elastic и инкрементом счетчика паник в Prometheus."
})

# Ex 15: Линтер 6: Запрет глобальных мутабельных переменных
code15 = r'''package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
)

// CheckGlobalMutableState проверяет объявления глобальных переменных на уровне пакета
func CheckGlobalMutableState(fset *token.FileSet, file *ast.File) []string {
	var issues []string

	for _, decl := range file.Decls {
		genDecl, ok := decl.(*ast.GenDecl)
		// Нас интересуют только объявления 'var' на уровне пакета
		if !ok || genDecl.Tok != token.VAR {
			continue
		}

		for _, spec := range genDecl.Specs {
			valSpec, ok := spec.(*ast.ValueSpec)
			if !ok {
				continue
			}

			for _, name := range valSpec.Names {
				// Разрешаем известные безопасные паттерны (например, var ErrNotFound = ...)
				if len(name.Name) >= 3 && name.Name[:3] == "Err" {
					continue
				}

				pos := fset.Position(name.Pos())
				issues = append(issues, fmt.Sprintf("%s:%d: обнаружена глобальная мутабельная переменная 'var %s'; используйте инкапсуляцию в структуру или const",
					pos.Filename, pos.Line, name.Name))
			}
		}
	}

	return issues
}

func main() {
	fmt.Println("=== Линтер noglobalstate: Запрет глобальных переменных ===")
	src := `package cache

import "errors"

// Разрешенная неизменяемая ошибка
var ErrCacheMiss = errors.New("miss")

// Опасное глобальное состояние! Гонка данных при многопоточности!
var GlobalCache = make(map[string]string)
var RequestCount int
`
	fset := token.NewFileSet()
	file, _ := parser.ParseFile(fset, "cache.go", src, 0)

	findings := CheckGlobalMutableState(fset, file)
	for _, f := range findings {
		fmt.Println("🚨", f)
	}
}
'''

validate_go_code(code15, "code15")
exercises.append({
    "num": 15,
    "title": "Линтер 6: Запрет глобальных мутабельных переменных",
    "task": "Глобальное изменяемое состояние (Global State) разрушает изоляцию тестов, делает невозможным конкурентное исполнение и провоцирует Data Race. Разработайте анализатор noglobalstate: сканирует объявления ast.GenDecl с token.VAR на уровне пакета, запрещая глобальные переменные (за исключением константных ошибок var ErrXxx = errors.New()).",
    "theory": "В Go переменные, объявленные на уровне пакета через ключевое слово `var`, доступны всем горутинам и функциям этого пакета.\n\nПочему глобальное состояние опасно:\n1) **Гонки данных (Data Races)**: Если две горутины одновременно читают и пишут в `var GlobalConfig` или `var cache map[...]`, происходит повреждение памяти и аварийная остановка рантайма;\n2) **Скрытые связи (Tight Coupling)**: Функции становятся нечистыми (Non-pure functions), их результат зависит от скрытого состояния, а не от переданных аргументов;\n3) **Сложность тестирования**: Тесты, запущенные параллельно (`t.Parallel()`), начинают перезаписывать глобальные переменные друг друга, порождая плавающие падения (Flaky Tests).\n\nКачественный линтер разрешает на уровне пакета только неизменяемые константы (`const`), статические ошибки (`var ErrNotFound = errors.New(...)`) и потокобезопасные синглтоны, запрещая изменяемые счетчики, мапы и срезы.",
    "step_by_step": [
        "Отфильтровать объявления верхнего уровня `*ast.GenDecl` с маркером `token.VAR`.",
        "Итерироваться по спецификациям значений `*ast.ValueSpec`.",
        "Реализовать фильтрацию разрешенных паттернов: префикс `Err` для статических ошибок sentinel errors.",
        "Зарегистрировать предупреждение с требованием передачи зависимостей через структуру конструктора."
    ],
    "code_blocks": [
        {
            "filename": "noglobalstate_analyzer.go",
            "lang": "go",
            "code": code15
        }
    ],
    "under_the_hood": "В популярном линтере `gochecknoglobals` проверка семантики типов углубляется: разрешаются типы, реализующие потокобезопасные интерфейсы (`sync.Locker`, `atomic.Pointer`), но строго запрещаются примитивные скалярные типы и сырые коллекции.",
    "pitfalls": [
        "Блокировка легитимных регулярок `var re = regexp.MustCompile(...)` (их компиляция в рантайме тяжелая, и глобальное хранение оправдано).",
        "Блокировка зарегистрированных ошибок `var ErrExpired = ...`.",
        "Ложные срабатывания на флагах Cobra CLI в файлах команд."
    ],
    "bigtech_interview": "Почему `var myRegex = regexp.MustCompile(...)` разрешают делать глобальной переменной, а `var myMap = make(map[string]string)` запрещают? Ответ: `*regexp.Regexp` после компиляции является потокобезопасным объектом только для чтения (Read-Only), и его методы поиска могут безопасно вызываться тысячами параллельных горутин. Напротив, встроенная `map` в Go не защищена от гонок и мгновенно роняет приложение с фатальной ошибкой `fatal error: concurrent map writes` при параллельной модификации."
})

output_path = '/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch98_p1.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Chapter 98 Part 1 generated successfully: {len(exercises)} exercises.")
