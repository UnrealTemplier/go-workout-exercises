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

# Ex 16: Хуки OpenFeature (Hooks) для аудита и телеметрии
code16 = '''package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// HookContext содержит контекст вычисления флага
type HookContext struct {
	FlagKey     string
	FlagType    string
	DefaultVal  any
	EvalContext map[string]any
}

// HookHints содержит дополнительные параметры выполнения
type HookHints map[string]any

// Hook интерфейс OpenFeature для перехвата жизненного цикла вычисления
type Hook interface {
	Before(ctx context.Context, hookCtx HookContext, hints HookHints) (context.Context, error)
	After(ctx context.Context, hookCtx HookContext, evalDetails any, hints HookHints) error
	Error(ctx context.Context, hookCtx HookContext, err error, hints HookHints)
	Finally(ctx context.Context, hookCtx HookContext, hints HookHints)
}

// PrometheusMetricsHook собирает метрики вычислений
type PrometheusMetricsHook struct {
	mu           sync.Mutex
	evalCounters map[string]int64
	latencies    map[string]time.Duration
}

func NewPrometheusMetricsHook() *PrometheusMetricsHook {
	return &PrometheusMetricsHook{
		evalCounters: make(map[string]int64),
		latencies:    make(map[string]time.Duration),
	}
}

type ctxKeyStartTime struct{}

func (h *PrometheusMetricsHook) Before(ctx context.Context, hookCtx HookContext, hints HookHints) (context.Context, error) {
	return context.WithValue(ctx, ctxKeyStartTime{}, time.Now()), nil
}

func (h *PrometheusMetricsHook) After(ctx context.Context, hookCtx HookContext, evalDetails any, hints HookHints) error {
	h.mu.Lock()
	defer h.mu.Unlock()
	key := fmt.Sprintf("flag=%s,variant=%v", hookCtx.FlagKey, evalDetails)
	h.evalCounters[key]++

	if start, ok := ctx.Value(ctxKeyStartTime{}).(time.Time); ok {
		h.latencies[hookCtx.FlagKey] += time.Since(start)
	}
	return nil
}

func (h *PrometheusMetricsHook) Error(ctx context.Context, hookCtx HookContext, err error, hints HookHints) {
	h.mu.Lock()
	defer h.mu.Unlock()
	key := fmt.Sprintf("flag=%s,status=error", hookCtx.FlagKey)
	h.evalCounters[key]++
}

func (h *PrometheusMetricsHook) Finally(ctx context.Context, hookCtx HookContext, hints HookHints) {
	// Очистка ресурсов или финализация контекста
}

func main() {
	hook := NewPrometheusMetricsHook()
	ctx := context.Background()
	hCtx := HookContext{
		FlagKey:     "checkout_v2",
		FlagType:    "boolean",
		DefaultVal:  false,
		EvalContext: map[string]any{"user_id": "usr-123"},
	}

	ctx, _ = hook.Before(ctx, hCtx, nil)
	// Эмуляция вычисления
	time.Sleep(2 * time.Millisecond)
	_ = hook.After(ctx, hCtx, true, nil)
	hook.Finally(ctx, hCtx, nil)

	hook.mu.Lock()
	fmt.Printf("Evaluations: %+v\\n", hook.evalCounters)
	hook.mu.Unlock()
}
'''
validate_go_code(code16, "code16")
exercises.append({
    "num": 16,
    "title": "Хуки OpenFeature (Hooks) для аудита и телеметрии",
    "task": "Реализуйте кастомный перехватчик (Hook) стандарта OpenFeature, имплементирующий методы Before, After, Error и Finally. Настройте автоматический замер латентности оценки и сбор метрик в Prometheus-совместимую структуру с метками flag_name, variant и reason.",
    "theory": "Спецификация OpenFeature стандартизирует жизненный цикл вычисления флагов с помощью концепции Hooks (хуков). По аналогии с middleware в HTTP или интерцепторами в gRPC, хуки позволяют внедрять сквозную функциональность (cross-cutting concerns) без изменения прикладного кода бизнес-логики.\n\nЖизненный цикл вычисления состоит из четырех этапов:\n1. Before: вызывается до обращения к провайдеру. Позволяет обогатить контекст вычисления (EvaluationContext) или зафиксировать таймстемп старта для вычисления латентности.\n2. After: выполняется при успешной оценке провайдером. Получает результирующее значение и причину (Reason: TARGETING_MATCH, DEFAULT, SPLIT и т.д.). Идеален для инкремента счетчиков показов (impressions) и Prometheus-метрик.\n3. Error: срабатывает при ошибке вычисления (например, сетевой таймаут к внешнему сервису флагов, несовместимость типов). Логирует инцидент и отправляет алерты.\n4. Finally: гарантированно вызывается всегда (аналог defer), гарантируя освобождение ресурсов и закрытие спанов OpenTelemetry.",
    "step_by_step": [
        "Определите интерфейс Hook с сигнатурами Before, After, Error и Finally в соответствии со спецификацией OpenFeature.",
        "Реализуйте PrometheusMetricsHook со счетчиками и картой латентности под защитой мьютекса.",
        "В методе Before сохраните метку времени start time в context.Context с использованием изолированного типизированного ключа.",
        "В методе After вычислите дельту time.Since(start) и инкрементируйте счетчик показов с соответствующими метками.",
        "В методе Error зафиксируйте счетчик сбоев вычисления."
    ],
    "code_blocks": [{
        "filename": "openfeature_hook.go",
        "lang": "go",
        "code": code16
    }],
    "under_the_hood": "В OpenFeature хуки могут регистрироваться на трех уровнях: глобально (Global), на уровне клиента (Client), или точечно при конкретном вызове (Invocation). При оценке хуки Before выполняются в порядке регистрации, а хуки After и Finally — в обратном порядке (LIFO), гарантируя вложенную изоляцию контекста выполнения аналогично стеку вызовов defer.",
    "pitfalls": [
        "Блокировка в хуке: вызовы Before/After происходят синхронно в критическом пути клиентского потока. Тяжелые операции (сетевые HTTP-запросы в аналитику) должны отправляться в буферизированный канал воркеров, иначе задержка проверки флага вырастет с микросекунд до десятков миллисекунд.",
        "Утечка горутин и контекстов: ключи контекста должны использовать неэкспортируемые структуры, чтобы избежать коллизий имен."
    ],
    "bigtech_interview": "В HighLoad-сервисах Яндекса и Ozon хуки флагов генерируют миллионы событий в секунду. Прямая отправка логов или HTTP-вызовов на каждый флаг мгновенно положит сеть. Поэтому в хуках применяют поточные атомарные счетчики и кольцевые буферы (ring buffer) для батчинга событий аудита."
})

# Ex 17: Аудит изменений и система одобрения флагов
code17 = '''package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"time"
)

// FlagAuditEvent описывает запись в журнале аудита изменений
type FlagAuditEvent struct {
	EventID   string    `json:"event_id"`
	FlagKey   string    `json:"flag_key"`
	Author    string    `json:"author"`
	OldValue  any       `json:"old_value"`
	NewValue  any       `json:"new_value"`
	Reason    string    `json:"reason"`
	Approved  bool      `json:"approved"`
	Approver  string    `json:"approver"`
	Timestamp time.Time `json:"timestamp"`
}

// AuditDispatcher отправляет уведомления во внешние системы
type AuditDispatcher struct {
	webhookURL string
	client     *http.Client
}

func NewAuditDispatcher(url string) *AuditDispatcher {
	return &AuditDispatcher{
		webhookURL: url,
		client:     &http.Client{Timeout: 3 * time.Second},
	}
}

func (d *AuditDispatcher) RecordChange(ctx context.Context, event FlagAuditEvent) error {
	// Валидация процесса одобрения (Four-Eyes Principle)
	if !event.Approved {
		return fmt.Errorf("изменение флага %s отклонено: отсутствует подтверждение релиз-инженера", event.FlagKey)
	}

	payload, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("ошибка сериализации аудита: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, d.webhookURL, bytes.NewReader(payload))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := d.client.Do(req)
	if err != nil {
		return fmt.Errorf("ошибка отправки вебхука аудита: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		return fmt.Errorf("webhook вернул ошибку: %d", resp.StatusCode)
	}
	return nil
}

func main() {
	// Тестовый сервер вебхука
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var evt FlagAuditEvent
		_ = json.NewDecoder(r.Body).Decode(&evt)
		fmt.Printf("[AUDIT WEBHOOK] Изменен флаг %s пользователем %s (Одобрил: %s): %v -> %v\\n",
			evt.FlagKey, evt.Author, evt.Approver, evt.OldValue, evt.NewValue)
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	dispatcher := NewAuditDispatcher(server.URL)

	changeEvent := FlagAuditEvent{
		EventID:   "evt-9901",
		FlagKey:   "enable_instant_checkout",
		Author:    "lead-dev@company.com",
		OldValue:  false,
		NewValue:  true,
		Reason:    "Релиз функционала для Black Friday",
		Approved:  true,
		Approver:  "tech-lead@company.com",
		Timestamp: time.Now().UTC(),
	}

	if err := dispatcher.RecordChange(context.Background(), changeEvent); err != nil {
		fmt.Printf("Ошибка: %v\\n", err)
	}
}
'''
validate_go_code(code17, "code17")
exercises.append({
    "num": 17,
    "title": "Аудит изменений и система одобрения флагов",
    "task": "Спроектируйте Enterprise-систему аудита изменений конфигурации и фиче-флагов. Реализуйте структуру FlagAuditEvent с метаданными автора, причины и согласующего лица (Four-Eyes Principle). Настройте отправку вебхук-уведомлений с гарантией проверки обязательного согласования изменений.",
    "theory": "В продуктовых системах переключение флага в production равносильно релизу новой версии ПО, но происходит мгновенно без повторного прогона CI/CD пайплайна. Несанкционированное или ошибочное переключение флага способно уронить инфраструктуру за секунды.\n\nПоэтому Enterprise-стандарты (SOC2, ISO 27001, PCI-DSS) требуют строгого соблюдения принципа 'Four-Eyes' (правило двух пар глаз):\n1. Автор изменения создает запрос на переключение флага с указанием причины (Reason) и ссылки на задачу в трекере.\n2. Тимлид или релиз-инженер проверяет readiness сервиса и одобряет изменение.\n3. Изменение фиксируется в неизменяемом журнале аудита (Audit Trail) с отправкой уведомлений в корпоративные каналы (Slack, Telegram, SIEM) и фиксацией в ClickHouse/Elasticsearch.",
    "step_by_step": [
        "Определите структуру FlagAuditEvent, включающую автора, причину, старое/новое значение, статус подтверждения и согласующего.",
        "Реализуйте проверку инварианта одобрения (Approved == true) перед отправкой изменений в прод.",
        "Спроектируйте HTTP-клиент диспетчера аудита с таймаутами для отправки вебхуков в корпоративный мессенджер.",
        "Протестируйте отправку события аудита с использованием httptest.Server."
    ],
    "code_blocks": [{
        "filename": "audit_dispatcher.go",
        "lang": "go",
        "code": code17
    }],
    "under_the_hood": "В распределенных системах записи аудита часто пишутся в транзакционный Outbox в базе данных управления флагами (PostgreSQL), откуда Debezium или CDC-воркер надежно пересылает их в Kafka. Это гарантирует, что даже при падении сети ни одно изменение флага не останется незафиксированным.",
    "pitfalls": [
        "Отсутствие маскирования секретов: если флаг хранит конфиденциальные данные (API-ключи, токены доступа), значения в логе аудита должны маскироваться (hash/redaction).",
        "Синхронная блокировка изменения флага медленным внешним вебхуком: если Slack лежит, переключение флага (особенно аварийного Kill Switch) не должно зависать."
    ],
    "bigtech_interview": "Как защитить систему от несанкционированного изменения Kill Switch во время инцидента? На собеседованиях ожидают ответ: критические рубильники (Break Glass Toggles) имеют режим экстренного применения доверенными On-Call инженерами с обязательным ретроспективным согласованием в течение 1 часа."
})

# Ex 18: Управление техническим долгом: процесс вывода флагов из эксплуатации
code18 = '''package main

import (
	"fmt"
	"time"
)

// FlagMetadata хранит данные жизненного цикла фиче-флага
type FlagMetadata struct {
	Key            string
	Type           string // "release", "experiment", "ops", "permission"
	OwnerEmail     string
	CreatedAt      time.Time
	ExpirationDate time.Time
	Status         string // "active", "stale", "archived"
}

// StaleFlagAuditor анализирует устаревшие флаги
type StaleFlagAuditor struct {
	maxLifespan time.Duration
}

func NewStaleFlagAuditor(maxLifespan time.Duration) *StaleFlagAuditor {
	return &StaleFlagAuditor{maxLifespan: maxLifespan}
}

func (a *StaleFlagAuditor) AuditFlags(flags []FlagMetadata, now time.Time) []FlagMetadata {
	var staleFlags []FlagMetadata
	for _, f := range flags {
		// Ops и Permission флаги могут быть долгоживущими
		if f.Type == "ops" || f.Type == "permission" {
			continue
		}

		age := now.Sub(f.CreatedAt)
		isExpired := !f.ExpirationDate.IsZero() && now.After(f.ExpirationDate)
		isOld := age > a.maxLifespan

		if isExpired || isOld {
			f.Status = "stale"
			staleFlags = append(staleFlags, f)
		}
	}
	return staleFlags
}

func main() {
	now := time.Now()
	flags := []FlagMetadata{
		{
			Key:        "dark_mode_v1",
			Type:       "release",
			OwnerEmail: "alice@company.com",
			CreatedAt:  now.Add(-90 * 24 * time.Hour), // 90 дней назад
		},
		{
			Key:        "kill_switch_recommendations",
			Type:       "ops",
			OwnerEmail: "infra-lead@company.com",
			CreatedAt:  now.Add(-180 * 24 * time.Hour), // Долгоживущий
		},
		{
			Key:            "spring_sale_banner",
			Type:           "experiment",
			OwnerEmail:     "bob@company.com",
			CreatedAt:      now.Add(-30 * 24 * time.Hour),
			ExpirationDate: now.Add(-5 * 24 * time.Hour), // Истек 5 дней назад
		},
	}

	auditor := NewStaleFlagAuditor(60 * 24 * time.Hour) // Порог 60 дней для релизных флагов
	stale := auditor.AuditFlags(flags, now)

	fmt.Printf("Обнаружено %d устаревших флагов (Technical Debt):\\n", len(stale))
	for _, f := range stale {
		fmt.Printf(" - Флаг: %-22s Владелец: %-18s Возраст: %.0f дней\\n",
			f.Key, f.OwnerEmail, now.Sub(f.CreatedAt).Hours()/24)
	}
}
'''
validate_go_code(code18, "code18")
exercises.append({
    "num": 18,
    "title": "Управление техническим долгом: процесс вывода флагов из эксплуатации",
    "task": "Разработайте подсистему аудита жизненного цикла фиче-флагов. Реализуйте структуру FlagMetadata с указанием типа флага, владельца, даты создания и даты истечения. Напишите анализатор StaleFlagAuditor, выявляющий просроченные и устаревшие временные флаги (технический долг) с фильтрацией постоянных флагов (Ops/Permission).",
    "theory": "Каждый добавленный в код фиче-флаг удваивает количество путей выполнения (`2^n` комбинаций состояний). Если не удалять флаги после завершения раскатки, кодовая база превращается в спагетти из устаревших веток `if/else`, затрудняя тестирование, рефакторинг и снижая надежность.\n\nИзвестная катастрофа Knight Capital (2012 год, потеря $440M за 45 минут) произошла именно из-за случайной активации заброшенного флага 8-летней давности, перенаправившего трафик на устаревший мертвый код.\n\nВ зрелых командах вводится строгий SLA на жизнь флагов:\n- Release Toggles: удаление через 14–30 дней после 100% раскатки.\n- Experiment Toggles: удаление сразу после фиксации результатов A/B теста.\n- Ops Toggles и Permission Toggles: бессрочные, но с регулярным аудитом необходимости.",
    "step_by_step": [
        "Создайте структуру FlagMetadata, хранящую тип, контакт владельца и временные границы действия флага.",
        "Реализуйте функцию фильтрации, игнорирующую постоянные флаги (ops, permission).",
        "Проверьте условия устаревания: превышение максимального срока жизни (maxLifespan) или наступление ExpirationDate.",
        "Сформируйте отчет об устаревших флагах с указанием ответственных инженеров."
    ],
    "code_blocks": [{
        "filename": "stale_flags_auditor.go",
        "lang": "go",
        "code": code18
    }],
    "under_the_hood": "В корпоративных CI/CD пайплайнах запуск аудитора устаревших флагов интегрируют в ночные джобы (nightly cron). Если флаг находится в 100% включенном состоянии более 30 дней, бот автоматически создает тикет в Jira на удаление условий из кода и назначает его на автора флага.",
    "pitfalls": [
        "Удаление Ops Toggles: автоматический аудит не должен помечать рубильники аварийного отключения (Kill Switches) как устаревшие только потому, что их не трогали полгода.",
        "Отсутствие поля Owner: если флаг создается анонимно без ответственной команды, через 6 месяцев никто в компании не рискнет его удалить из страха сломать продакшен."
    ],
    "bigtech_interview": "Как Uber и Meta борются с заброшенными флагами? Используются специализированные внутренние инструменты (например, Piranha от Uber), которые автоматически парсят AST, создают Pull Request с удалением флага и мертвой ветки кода, и прогоняют тесты."
})

# Ex 19: Статический анализатор для поиска мертвых фиче-флагов
code19 = '''package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"strings"
)

// FlagUsageLocation хранит местоположение найденного флага
type FlagUsageLocation struct {
	FlagKey  string
	Filename string
	Line     int
	Snippet  string
}

// DeadFlagScanner анализирует AST файлов Go
type DeadFlagScanner struct {
	deadFlags map[string]bool
}

func NewDeadFlagScanner(deadFlags []string) *DeadFlagScanner {
	m := make(map[string]bool)
	for _, f := range deadFlags {
		m[f] = true
	}
	return &DeadFlagScanner{deadFlags: m}
}

func (s *DeadFlagScanner) ScanSource(filename, src string) ([]FlagUsageLocation, error) {
	fset := token.NewFileSet()
	node, err := parser.ParseFile(fset, filename, src, parser.ParseComments)
	if err != nil {
		return nil, err
	}

	var occurrences []FlagUsageLocation

	// Обход синтаксического дерева
	ast.Inspect(node, func(n ast.Node) bool {
		call, ok := n.(*ast.CallExpr)
		if !ok {
			return true
		}

		// Ищем вызовы вида client.BooleanValue(ctx, "flag_name", ...)
		sel, ok := call.Fun.(*ast.SelectorExpr)
		if !ok || sel.Sel.Name != "BooleanValue" {
			return true
		}

		// Ищем аргумент-строку с именем флага (обычно 2-й аргумент: ctx, "flag_key", default)
		for _, arg := range call.Args {
			lit, ok := arg.(*ast.BasicLit)
			if ok && lit.Kind == token.STRING {
				flagName := strings.Trim(lit.Value, "\\\"")
				if s.deadFlags[flagName] {
					pos := fset.Position(call.Pos())
					occurrences = append(occurrences, FlagUsageLocation{
						FlagKey:  flagName,
						Filename: filename,
						Line:     pos.Line,
						Snippet:  lit.Value,
					})
				}
			}
		}
		return true
	})

	return occurrences, nil
}

func main() {
	sampleGoCode := `package service

import "context"

func ProcessOrder(ctx context.Context, client Client) {
	// Старый флаг, который уже 100% включен в проде
	if client.BooleanValue(ctx, "old_checkout_2023", false) {
		runNewFlow()
	} else {
		runLegacyFlow()
	}

	// Активный флаг
	if client.BooleanValue(ctx, "black_friday_promo", false) {
		applyDiscount()
	}
}
`

	deadFlagsList := []string{"old_checkout_2023", "deprecated_search_v1"}
	scanner := NewDeadFlagScanner(deadFlagsList)

	results, err := scanner.ScanSource("order_service.go", sampleGoCode)
	if err != nil {
		panic(err)
	}

	fmt.Printf("Найдено %d вхождений устаревших флагов в AST:\\n", len(results))
	for _, res := range results {
		fmt.Printf(" -> Флаг '%s' в файле %s на строке %d\\n", res.FlagKey, res.Filename, res.Line)
	}
}
'''
validate_go_code(code19, "code19")
exercises.append({
    "num": 19,
    "title": "Статический анализатор для поиска мертвых фиче-флагов",
    "task": "Используя стандартные пакеты go/parser, go/ast и go/token, напишите статический анализатор кода DeadFlagScanner. Анализатор должен обходить синтаксическое дерево исходных файлов Go, обнаруживать вызовы методов client.BooleanValue с устаревшими флагами и возвращать точные номера строк для рефакторинга.",
    "theory": "Ручной поиск заброшенных флагов с помощью `grep` ненадежен: флаг может передаваться как константа, в комментариях или как часть составных строк. Использование абстрактного синтаксического дерева (AST) компилятора Go дает 100% точность идентификации вызовов.\n\nПакет `go/ast` позволяет представить программу в виде древовидной структуры узлов: вызовы функций представляются узлами `*ast.CallExpr`, селекторы методов — `*ast.SelectorExpr`, а строковые литералы аргументов — `*ast.BasicLit`. Обход дерева методом `ast.Inspect` находит точные координаты вызова функции `BooleanValue` и имя переданного флага.",
    "step_by_step": [
        "Инициализируйте набор файлов token.NewFileSet() и распарсите исходный код через parser.ParseFile.",
        "Реализуйте функцию-инспектор для ast.Inspect, проверяющую приведение типов узлов к *ast.CallExpr.",
        "Убедитесь, что вызываемый метод соответствует селектору BooleanValue.",
        "Извлеките строковый литерал из аргументов вызова и сопоставьте со словарем закрытых флагов.",
        "Зафиксируйте координаты позиции вызова в исходном коде через fset.Position()."
    ],
    "code_blocks": [{
        "filename": "dead_flags_ast_scanner.go",
        "lang": "go",
        "code": code19
    }],
    "under_the_hood": "Статический анализатор может не только находить места вызовов, но и модифицировать AST. С помощью пакета `go/printer` можно автоматически заменить блок `if client.BooleanValue(...) { A } else { B }` на безусловное тело `A`, полностью удалив ветку `else` и сам вызов флага без ручного редактирования файла.",
    "pitfalls": [
        "Передача имени флага через переменную: если имя флага передается не строковым литералом `\"my_flag\"`, а переменной или константой (`FlagName`), `*ast.BasicLit` не сработает — потребуется резолвинг идентификаторов через `*ast.Ident` и область видимости `ast.Scope`.",
        "Ложные срабатывания на одноименных методах других интерфейсов: важно проверять тип структуры клиента, если в проекте есть другие типы с методом BooleanValue."
    ],
    "bigtech_interview": "Каковы ограничения чистого AST-анализа по сравнению с анализом типов в Go? Ответ: AST анализирует только синтаксис без учета семантики типов. Для гарантии того, что метод вызывается именно у `openfeature.Client`, в компиляторе используется `go/types` совместно с AST (библиотека `golang.org/x/tools/go/analysis`)."
})

# Ex 20: Динамическая перезагрузка конфигурации (Hot Reload) с fsnotify
code20 = '''package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/fsnotify/fsnotify"
)

// HotConfigManager отслеживает изменения файла конфигурации
type HotConfigManager struct {
	filePath string
	mu       sync.RWMutex
	content  string
}

func NewHotConfigManager(path string) *HotConfigManager {
	return &HotConfigManager{filePath: path}
}

func (m *HotConfigManager) GetContent() string {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.content
}

func (m *HotConfigManager) load() error {
	data, err := os.ReadFile(m.filePath)
	if err != nil {
		return err
	}
	m.mu.Lock()
	m.content = string(data)
	m.mu.Unlock()
	return nil
}

func (m *HotConfigManager) Watch(ctx context.Context) error {
	if err := m.load(); err != nil {
		return err
	}

	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		return err
	}
	defer watcher.Close()

	// В Linux (inotify) при редактировании файлов в Vim/Kubernetes ConfigMap
	// файл часто подменяется через rename/symlink. Надежнее следить за родительской директорией.
	dir := filepath.Dir(m.filePath)
	if err := watcher.Add(dir); err != nil {
		return err
	}

	// Дебаунсинг событий (файловые системы могут генерировать серию WRITE/CHMOD)
	var debounceTimer *time.Timer
	var debounceMu sync.Mutex

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case event, ok := <-watcher.Events:
			if !ok {
				return nil
			}
			if filepath.Clean(event.Name) == filepath.Clean(m.filePath) {
				if event.Has(fsnotify.Write) || event.Has(fsnotify.Create) {
					debounceMu.Lock()
					if debounceTimer != nil {
						debounceTimer.Stop()
					}
					debounceTimer = time.AfterFunc(100*time.Millisecond, func() {
						if err := m.load(); err == nil {
							fmt.Printf("[HOT RELOAD] Конфигурация успешно обновлена: %s\\n", m.GetContent())
						}
					})
					debounceMu.Unlock()
				}
			}
		case err, ok := <-watcher.Errors:
			if !ok {
				return nil
			}
			fmt.Printf("[HOT RELOAD ERROR] %v\\n", err)
		}
	}
}

func main() {
	tmpDir, err := os.MkdirTemp("", "cfg_watch_*")
	if err != nil {
		panic(err)
	}
	defer os.RemoveAll(tmpDir)

	cfgFile := filepath.Join(tmpDir, "config.json")
	_ = os.WriteFile(cfgFile, []byte(`{"rate_limit": 100}`), 0644)

	mgr := NewHotConfigManager(cfgFile)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go func() {
		_ = mgr.Watch(ctx)
	}()

	time.Sleep(50 * time.Millisecond)
	fmt.Printf("Начальный конфиг: %s\\n", mgr.GetContent())

	// Эмулируем изменение файла конфигурации
	_ = os.WriteFile(cfgFile, []byte(`{"rate_limit": 500}`), 0644)
	time.Sleep(200 * time.Millisecond)

	fmt.Printf("Итоговый конфиг в памяти: %s\\n", mgr.GetContent())
}
'''
validate_go_code(code20, "code20")
exercises.append({
    "num": 20,
    "title": "Динамическая перезагрузка конфигурации (Hot Reload) с fsnotify",
    "task": "Используя библиотеку github.com/fsnotify/fsnotify, реализуйте менеджер горячей перезагрузки конфигурации HotConfigManager. Настройте мониторинг файловой директории, устраните дребезг событий (дебаунсинг) и обеспечьте атомарное обновление конфигурации в памяти без перезапуска приложения.",
    "theory": "В классических микросервисах изменение параметра (таймаута, размера пула соединений, лимита RPS) требовало перезапуска пода. Это приводило к инвалидации локальных кэшей, повторному прогреву соединений (cold start) и создавало всплеск задержек.\n\nБиблиотека `fsnotify` предоставляет кроссплатформенный интерфейс к низкоуровневым механизмам нотификаций ядра ОС:\n- Linux: `inotify`\n- macOS: `FSEvents` / `kqueue`\n- Windows: `ReadDirectoryChangesW`\n\nПри изменении файла генерируется системное прерывание, позволяющее приложению мгновенно перечитать файл без поллинга диска с `time.Sleep`.",
    "step_by_step": [
        "Создайте структуру HotConfigManager с защитой состояния через sync.RWMutex.",
        "Инициализируйте наблюдатель fsnotify.NewWatcher() и добавьте директорию с файлом в отслеживание.",
        "Реализуйте цикл select по каналам watcher.Events, watcher.Errors и ctx.Done().",
        "Добавьте дебаунсинг с time.AfterFunc для объединения множественных событий записи в одно обновление.",
        "Обновите состояние в памяти и протестируйте перезагрузку на временном файле."
    ],
    "code_blocks": [{
        "filename": "hot_config_watcher.go",
        "lang": "go",
        "code": code20
    }],
    "under_the_hood": "В Kubernetes ConfigMaps монтируются в контейнер через многоуровневые символические ссылки (`..data -> ..2026_09_08_...`). При обновлении ConfigMap ядро k8s не меняет существующий файл, а атомарно меняет симлинк директории `..data`. Если слушать конкретный файл, `inotify` перестанет получать события. Слушать нужно именно директорию файла!",
    "pitfalls": [
        "Отсутствие дебаунсинга: текстовые редакторы или атомарные утилиты копирования генерируют до 4 событий подряд (`CREATE`, `WRITE`, `CHMOD`, `RENAME`). Без дебаунсинга файл будет прочитан 4 раза подряд, причем в момент `WRITE` он может быть наполовину пустым (broken json).",
        "Утечка дескрипторов: незакрытый `watcher.Close()` оставляет открытые файловые дескрипторы inotify."
    ],
    "bigtech_interview": "Почему в продакшене крупного масштаба не рекомендуется перезагружать конфигурацию с диска на тысячах серверов одновременно? При массовом обновлении ConfigMap все поды одновременно ринутся переподключаться к БД или инвалидировать кэш, вызывая Thundering Herd. Требуется добавление джиттера (рандомизированной задержки) перед применением."
})

# Ex 21: Управление конфигурацией с помощью библиотеки Viper
code21 = '''package main

import (
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/fsnotify/fsnotify"
	"github.com/spf13/viper"
)

type ServerConfig struct {
	Port        int           `mapstructure:"port"`
	Timeout     time.Duration `mapstructure:"timeout"`
	MaxRequests int           `mapstructure:"max_requests"`
}

type ViperConfigHolder struct {
	mu  sync.RWMutex
	cfg ServerConfig
}

func (h *ViperConfigHolder) Get() ServerConfig {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return h.cfg
}

func (h *ViperConfigHolder) update(v *viper.Viper) error {
	var newCfg ServerConfig
	if err := v.Unmarshal(&newCfg); err != nil {
		return fmt.Errorf("ошибка парсинга viper: %w", err)
	}
	h.mu.Lock()
	h.cfg = newCfg
	h.mu.Unlock()
	return nil
}

func main() {
	tmpDir, err := os.MkdirTemp("", "viper_demo_*")
	if err != nil {
		panic(err)
	}
	defer os.RemoveAll(tmpDir)

	cfgFile := filepath.Join(tmpDir, "config.yaml")
	initialYaml := []byte("port: 8080\\ntimeout: 5s\\nmax_requests: 1000\\n")
	_ = os.WriteFile(cfgFile, initialYaml, 0644)

	v := viper.New()
	v.SetConfigFile(cfgFile)
	v.SetConfigType("yaml")

	if err := v.ReadInConfig(); err != nil {
		panic(err)
	}

	holder := &ViperConfigHolder{}
	_ = holder.update(v)

	// Настройка отслеживания изменений Viper
	v.OnConfigChange(func(e fsnotify.Event) {
		fmt.Printf("[VIPER EVENT] Обнаружено изменение файла: %s (op=%v)\\n", e.Name, e.Op)
		if err := holder.update(v); err == nil {
			fmt.Printf("[VIPER RELOAD] Новая конфигурация: %+v\\n", holder.Get())
		}
	})
	v.WatchConfig()

	fmt.Printf("Конфиг при старте: %+v\\n", holder.Get())

	// Изменяем файл
	updatedYaml := []byte("port: 9090\\ntimeout: 10s\\nmax_requests: 5000\\n")
	_ = os.WriteFile(cfgFile, updatedYaml, 0644)

	time.Sleep(300 * time.Millisecond)
	fmt.Printf("Итоговый конфиг: %+v\\n", holder.Get())
}
'''
validate_go_code(code21, "code21")
exercises.append({
    "num": 21,
    "title": "Управление конфигурацией с помощью библиотеки Viper",
    "task": "Изучите популярный стандарт управления конфигурацией spf13/viper. Реализуйте загрузку YAML-конфигурации в строго типизированную структуру Go через Unmarshal, подключите динамическое наблюдение WatchConfig() и безопасную регистрацию коллбэка OnConfigChange.",
    "theory": "`spf13/viper` — де-факто стандарт управления конфигурацией в экосистеме Go и проектах CNCF (Kubernetes, Hugo). Viper умеет агрегировать данные из множества источников (YAML, JSON, TOML, переменные окружения, флаги CLI, Consul, etcd).\n\nФункция `viper.WatchConfig()` внутри использует `fsnotify` в отдельной фоновой горутине, а метод `viper.OnConfigChange(callback)` вызывает пользовательскую функцию при каждом изменении файла на диске.\n\nОднако сам Viper не является полностью потокобезопасным при одновременном чтении и записи через `v.Get*()`. Поэтому в production-коде правильным паттерном является десериализация в неизменяемую структуру через `v.Unmarshal(&cfg)` под защитой мьютекса или атомарного указателя.",
    "step_by_step": [
        "Определите целевую структуру конфигурации с тегами mapstructure.",
        "Инициализируйте экземпляр viper.New() с указанием пути к файлу и типа yaml.",
        "Реализуйте потокобезопасный холдер ViperConfigHolder с методами Get() и update().",
        "Зарегистрируйте коллбэк v.OnConfigChange() и запустите v.WatchConfig().",
        "Проверьте перезагрузку конфигурации при модификации дискового файла."
    ],
    "code_blocks": [{
        "filename": "viper_dynamic_config.go",
        "lang": "go",
        "code": code21
    }],
    "under_the_hood": "Viper автоматически поддерживает преобразование строк в `time.Duration` (например, `5s`, `100ms`), парсинг слайсов и вложенных карт. При вызове `WatchConfig()` Viper запускает внутреннюю горутину, которая транслирует системные события файловой системы в вызов вашего обработчика `OnConfigChange`.",
    "pitfalls": [
        "Гонка данных в viper.Get(): вызовы `viper.GetString(\"key\")` во время перезагрузки через `WatchConfig` могут вызывать data race. Всегда десериализуйте данные в изолированную структуру через `Unmarshal`.",
        "Теги mapstructure: разработчики часто пишут `json:\"port\"` или `yaml:\"port\"`, из-за чего `v.Unmarshal()` оставляет поля со значениями по умолчанию. Viper использует тег `mapstructure`."
    ],
    "bigtech_interview": "В чем недостаток глобального синглтона `viper.Get()`? Использование глобального состояния затрудняет изолированное модульное тестирование и параллельный запуск тестов с `-race`. Рекомендуется всегда создавать изолированные экземпляры `viper.New()` и внедрять их через Dependency Injection."
})

# Ex 22: Валидация динамической конфигурации перед применением
code22 = '''package main

import (
	"errors"
	"fmt"
	"sync"
	"time"
)

// DynamicConfig содержит бизнес-параметры сервиса
type DynamicConfig struct {
	MaxRPS          int           `json:"max_rps"`
	RequestTimeout  time.Duration `json:"request_timeout"`
	MaxPayloadBytes int64         `json:"max_payload_bytes"`
	DBPoolSize      int           `json:"db_pool_size"`
}

// Validate проверяет бизнес-инварианты конфигурации
func (c *DynamicConfig) Validate() error {
	var errs []error

	if c.MaxRPS <= 0 || c.MaxRPS > 100_000 {
		errs = append(errs, fmt.Errorf("max_rps должен быть в диапазоне (0, 100000], получено: %d", c.MaxRPS))
	}
	if c.RequestTimeout <= 0 || c.RequestTimeout > 60*time.Second {
		errs = append(errs, fmt.Errorf("request_timeout должен быть в диапазоне (0, 60s], получено: %v", c.RequestTimeout))
	}
	if c.MaxPayloadBytes < 1024 || c.MaxPayloadBytes > 100*1024*1024 {
		errs = append(errs, fmt.Errorf("max_payload_bytes должен быть от 1KB до 100MB, получено: %d", c.MaxPayloadBytes))
	}
	if c.DBPoolSize < 1 || c.DBPoolSize > 500 {
		errs = append(errs, fmt.Errorf("db_pool_size должен быть в диапазоне [1, 500], получено: %d", c.DBPoolSize))
	}

	return errors.Join(errs...)
}

// SafeConfigManager обеспечивает двухфазное обновление
type SafeConfigManager struct {
	mu     sync.RWMutex
	active DynamicConfig
}

func NewSafeConfigManager(initial DynamicConfig) (*SafeConfigManager, error) {
	if err := initial.Validate(); err != nil {
		return nil, fmt.Errorf("невалидный стартовый конфиг: %w", err)
	}
	return &SafeConfigManager{active: initial}, nil
}

func (m *SafeConfigManager) Get() DynamicConfig {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.active
}

// TryApply реализует двухфазную верификацию перед переключением
func (m *SafeConfigManager) TryApply(candidate DynamicConfig) error {
	// Фаза 1: Валидация кандидата (до захвата эксклюзивной блокировки)
	if err := candidate.Validate(); err != nil {
		return fmt.Errorf("отклонено: новая конфигурация невалидна: %w", err)
	}

	// Фаза 2: Атомарное применение валидной конфигурации
	m.mu.Lock()
	m.active = candidate
	m.mu.Unlock()
	return nil
}

func main() {
	initial := DynamicConfig{
		MaxRPS:          1000,
		RequestTimeout:  2 * time.Second,
		MaxPayloadBytes: 10 * 1024 * 1024,
		DBPoolSize:      50,
	}

	mgr, err := NewSafeConfigManager(initial)
	if err != nil {
		panic(err)
	}

	fmt.Printf("Активная конфигурация: %+v\\n", mgr.Get())

	// Попытка применить ошибочную конфигурацию (таймаут 0 и гигантский RPS)
	badCandidate := DynamicConfig{
		MaxRPS:          -50,
		RequestTimeout:  0,
		MaxPayloadBytes: 1024,
		DBPoolSize:      10,
	}

	err = mgr.TryApply(badCandidate)
	if err != nil {
		fmt.Printf("[RELOAD REJECTED] %v\\n", err)
	}

	// Проверяем, что сервис продолжил работать на стабильном конфиге
	fmt.Printf("Конфигурация осталась стабильной: %+v\\n", mgr.Get())

	// Корректное обновление
	goodCandidate := DynamicConfig{
		MaxRPS:          5000,
		RequestTimeout:  5 * time.Second,
		MaxPayloadBytes: 20 * 1024 * 1024,
		DBPoolSize:      100,
	}
	if err := mgr.TryApply(goodCandidate); err == nil {
		fmt.Printf("[RELOAD SUCCESS] Новая конфигурация: %+v\\n", mgr.Get())
	}
}
'''
validate_go_code(code22, "code22")
exercises.append({
    "num": 22,
    "title": "Валидация динамической конфигурации перед применением",
    "task": "Реализуйте двухфазный механизм обновления конфигурации с обязательной валидацией бизнес-инвариантов. Напишите метод Validate() с использованием errors.Join() для агрегации ошибок. Докажите, что при попытке применить невалидный конфиг сервис отклоняет изменения без паники и продолжает работу на стабильной версии.",
    "theory": "Самый опасный сценарий при использовании Hot Reload конфигурации — человеческая ошибка дежурного инженера: опечатка в значении таймаута (например, `0s` вместо `10s`), указание отрицательного размера пула соединений или лимита памяти `10MB` вместо `10GB`.\n\nЕсли применить такой конфиг 'вслепую', сервис упадет во время выполнения (panic или каскадный отказ соединений). Двухфазная схема обновления (Two-Phase Apply) решает эту проблему:\n1. Фаза 1 (Pre-flight Validation): новый файл парсится во временную структуру `candidate` и валидируется на граничные условия.\n2. Фаза 2 (Commit): если валидация прошла успешно, активный указатель подменяется; если возникла ошибка, кандидат сбрасывается, пишется алерт в мониторинг, а система остается на 100% стабильном предыдущем конфиге.",
    "step_by_step": [
        "Определите структуру DynamicConfig с полями таймаутов, пулов и лимитов нагрузки.",
        "Реализуйте метод Validate() с проверкой граничных диапазонов и агрегацией ошибок через errors.Join().",
        "Создайте SafeConfigManager с проверкой валидности стартового конфига.",
        "В методе TryApply() выполните валидацию до захвата блокировки на запись.",
        "Протестируйте отклонение некорректных параметров и успешное применение корректных."
    ],
    "code_blocks": [{
        "filename": "validated_config_manager.go",
        "lang": "go",
        "code": code22
    }],
    "under_the_hood": "Валидация должна происходить до захвата блокировки `m.mu.Lock()`. Проверка правил может быть относительно медленной (проверка регулярных выражений, DNS-резолвинг адресов брокеров). Валидируя кандидата без блокировки, мы гарантируем нулевое влияние на читающие горутины.",
    "pitfalls": [
        "Паника при валидации: функции валидации должны быть чистыми и не паниковать при nil-указателях или пустых строках.",
        "Частичное применение: ни в коем случае нельзя мутировать поля активного объекта напрямую до завершения валидации всех параметров."
    ],
    "bigtech_interview": "Как в распределенных системах тестируют новые конфиги перед раскаткой? Применяется канареечное применение конфигурации (Canary Config Deployment): конфиг сначала доставляется на 1% подов, где метрики отслеживаются 5 минут, и только при отсутствии всплеска ошибок распространяется на остальной кластер."
})

# Ex 23: Потокобезопасная атомарная подмена конфига через atomic.Pointer
code23 = '''package main

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// ServiceConfig содержит неизменяемую конфигурацию сервиса
type ServiceConfig struct {
	Version      string
	ReadTimeout  time.Duration
	WriteTimeout time.Duration
	MaxWorkers   int
}

// AtomicConfigHolder обеспечивает lock-free чтение конфигурации
type AtomicConfigHolder struct {
	ptr atomic.Pointer[ServiceConfig]
}

func NewAtomicConfigHolder(initial ServiceConfig) *AtomicConfigHolder {
	h := &AtomicConfigHolder{}
	h.ptr.Store(&initial)
	return h
}

// Get выполняет lock-free чтение за доли наносекунды
func (h *AtomicConfigHolder) Get() *ServiceConfig {
	return h.ptr.Load()
}

// Swap атомарно подменяет активную конфигурацию
func (h *AtomicConfigHolder) Swap(newCfg ServiceConfig) {
	h.ptr.Store(&newCfg)
}

func main() {
	holder := NewAtomicConfigHolder(ServiceConfig{
		Version:      "1.0.0",
		ReadTimeout:  100 * time.Millisecond,
		WriteTimeout: 200 * time.Millisecond,
		MaxWorkers:   16,
	})

	var wg sync.WaitGroup
	readersCount := 8
	stopCh := make(chan struct{})

	// Запускаем параллельные горутины, непрерывно читающие конфиг
	for i := 0; i < readersCount; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			var reads int
			for {
				select {
				case <-stopCh:
					return
				default:
					cfg := holder.Get()
					if cfg.MaxWorkers <= 0 {
						panic("недопустимое значение конфига!")
					}
					reads++
				}
			}
		}(i)
	}

	// Атомарно подменяем конфигурацию на лету без блокировок
	time.Sleep(10 * time.Millisecond)
	holder.Swap(ServiceConfig{
		Version:      "1.1.0",
		ReadTimeout:  150 * time.Millisecond,
		WriteTimeout: 300 * time.Millisecond,
		MaxWorkers:   32,
	})
	fmt.Printf("Конфиг атомарно обновлен на версию: %s\\n", holder.Get().Version)

	time.Sleep(10 * time.Millisecond)
	close(stopCh)
	wg.Wait()

	fmt.Println("Все читающие горутины отработали без гонок данных и блокировок.")
}
'''
validate_go_code(code23, "code23")
exercises.append({
    "num": 23,
    "title": "Потокобезопасная атомарная подмена конфига через atomic.Pointer",
    "task": "Используя обобщенный тип atomic.Pointer[T] из стандартной библиотеки Go (Go 1.19+), реализуйте lock-free контейнер конфигурации AtomicConfigHolder. Напишите многопоточный стресс-тест, демонстрирующий отсутствие contention и блокировок между читателями и писателями.",
    "theory": "В приложениях с высокой нагрузкой (сотни тысяч RPS) чтение конфигурации происходит при обработке каждого входящего HTTP/gRPC запроса. Использование даже `sync.RWMutex` в этом месте создает существенные накладные расходы:\n- Блокировка чтения `RLock()` модифицирует внутренний счетчик читателей через атомарную инструкцию шины процессора `LOCK XADD`.\n- На многоядерных машинах (32–128 ядер) десятки горутин начинают конкурировать за одну и ту же кэш-линию процессора (Cache-Line Bouncing), снижая пропускную способность.\n\nПоявившийся в Go 1.19 `atomic.Pointer[T]` решает проблему: метод `ptr.Load()` представляет собой обычное чтение 64-битного указателя на уровне процессора без мутации памяти и без блокировок. Обновление конфигурации через `ptr.Store(&newCfg)` заменяет указатель в один машинный такт. Старый конфиг будет безопасно утилизирован сборщиком мусора (GC), когда все завершившиеся запросы отпустят ссылки.",
    "step_by_step": [
        "Определите структуру конфигурации ServiceConfig.",
        "Создайте AtomicConfigHolder с приватным полем atomic.Pointer[ServiceConfig].",
        "В конструкторе инициализируйте указатель через ptr.Store(&initial).",
        "Реализуйте метод Get(), возвращающий типизированный указатель через ptr.Load().",
        "Реализуйте метод Swap() для мгновенного переключения конфигурации.",
        "Протестируйте конкурентный доступ с параллельными читателями и писателями."
    ],
    "code_blocks": [{
        "filename": "atomic_config_holder.go",
        "lang": "go",
        "code": code23
    }],
    "under_the_hood": "На архитектурах x86-64 и ARM64 вызов `atomic.Pointer.Load()` транслируется в одну процессорную инструкцию `MOV` (с семантикой Acquire). Так как чтение 64-битного слова выровнено по границе 8 байт, процессорная шина гарантирует атомарность без аппаратных мьютексов.",
    "pitfalls": [
        "Мутация полей возвращенного объекта: метод `Get()` возвращает указатель `*ServiceConfig`. Если вызывающий код попытается мутировать `cfg.MaxWorkers = 5`, возникнет гонка данных! Структура за указателем должна быть строго неизменяемой (Immutable Value Object).",
        "Забытая инициализация: если вызвать `Load()` до первого `Store()`, вернется `nil`. Конструктор должен гарантировать ненулевой стартовый указатель."
    ],
    "bigtech_interview": "В чем разница между `atomic.Value` и `atomic.Pointer[T]`? Ответ: `atomic.Value` появился в Go 1.4 и оперирует `any` (interface{}), что влечет аллокацию памяти при боксинге интерфейса и необходимость приведения типов `v.Load().(*Config)`. Дженерик `atomic.Pointer[T]` типобезопасен и исключает аллокации."
})

# Ex 24: Многоуровневая иерархия конфигурации (Config Precedence)
code24 = '''package main

import (
	"fmt"
	"os"
	"strconv"
)

// AppSettings агрегирует финальные настройки
type AppSettings struct {
	Port     int
	Database string
	Debug    bool
}

// ConfigLayer определяет приоритет слоя конфигурации
type ConfigLayer int

const (
	LayerDefault ConfigLayer = iota
	LayerFile
	LayerRemote
	LayerEnv
	LayerCLI
)

// ConfigResolver разрешает параметры с учетом иерархии приоритетов
type ConfigResolver struct {
	defaults map[string]string
	file     map[string]string
	remote   map[string]string
	cli      map[string]string
}

func NewConfigResolver() *ConfigResolver {
	return &ConfigResolver{
		defaults: map[string]string{
			"port":     "8080",
			"database": "postgres://localhost:5432/db",
			"debug":    "false",
		},
		file:   make(map[string]string),
		remote: make(map[string]string),
		cli:    make(map[string]string),
	}
}

// ResolveParam возвращает значение с соблюдением приоритета: CLI > ENV > Remote > File > Default
func (r *ConfigResolver) ResolveParam(key string, envVar string) (string, ConfigLayer) {
	// 1. CLI Flags
	if v, ok := r.cli[key]; ok {
		return v, LayerCLI
	}
	// 2. Environment Variables
	if envVar != "" {
		if v := os.Getenv(envVar); v != "" {
			return v, LayerEnv
		}
	}
	// 3. Remote Config (etcd / Consul)
	if v, ok := r.remote[key]; ok {
		return v, LayerRemote
	}
	// 4. Local File (config.yaml)
	if v, ok := r.file[key]; ok {
		return v, LayerFile
	}
	// 5. Hardcoded Defaults
	return r.defaults[key], LayerDefault
}

func (r *ConfigResolver) BuildSettings() AppSettings {
	portStr, _ := r.ResolveParam("port", "APP_PORT")
	port, _ := strconv.Atoi(portStr)

	dbStr, _ := r.ResolveParam("database", "APP_DATABASE_URL")
	debugStr, _ := r.ResolveParam("debug", "APP_DEBUG")
	debug, _ := strconv.ParseBool(debugStr)

	return AppSettings{
		Port:     port,
		Database: dbStr,
		Debug:    debug,
	}
}

func main() {
	resolver := NewConfigResolver()

	// Слой 4: Файл конфигурации
	resolver.file["port"] = "9000"
	resolver.file["database"] = "postgres://file-host:5432/app"

	// Слой 3: Удаленный сервер конфигурации
	resolver.remote["database"] = "postgres://remote-host:5432/app"

	// Слой 2: Переменные окружения
	_ = os.Setenv("APP_PORT", "9999")
	defer os.Unsetenv("APP_PORT")

	// Слой 1: CLI-флаг
	resolver.cli["debug"] = "true"

	portVal, portLayer := resolver.ResolveParam("port", "APP_PORT")
	dbVal, dbLayer := resolver.ResolveParam("database", "APP_DATABASE_URL")
	debugVal, debugLayer := resolver.ResolveParam("debug", "APP_DEBUG")

	fmt.Printf("Port: %s (из слоя %d: ENV переопределил File)\\n", portVal, portLayer)
	fmt.Printf("Database: %s (из слоя %d: Remote переопределил File)\\n", dbVal, dbLayer)
	fmt.Printf("Debug: %s (из слоя %d: CLI переопределил Default)\\n", debugVal, debugLayer)

	settings := resolver.BuildSettings()
	fmt.Printf("Финальный объект AppSettings: %+v\\n", settings)
}
'''
validate_go_code(code24, "code24")
exercises.append({
    "num": 24,
    "title": "Многоуровневая иерархия конфигурации (Config Precedence)",
    "task": "Реализуйте резолвер конфигурации ConfigResolver, поддерживающий Enterprise-иерархию приоритетов: 1) Флаги CLI -> 2) Переменные окружения (ENV) -> 3) Удаленный конфиг (Remote) -> 4) Локальный файл -> 5) Значения по умолчанию (Defaults). Напишите демонстрацию разрешения конфликтов между слоями.",
    "theory": "В 12-факторных приложениях (The Twelve-Factor App, Factor III: Config) параметры поступают из множества разнородных источников:\n- Разработчик локально запускает сервис с дефолтами.\n- В CI/CD файл `config.yaml` монтируется из репозитория.\n- Администратор переопределяет базу данных через переменную окружения `APP_DATABASE_URL` в Kubernetes Pod Spec.\n- Дежурный инженер точечно передает CLI-флаг `--debug=true`.\n\nЧтобы избежать непредсказуемого поведения, в кодовой базе фиксируется строгая иерархия старшинства (Config Precedence). Значение из более высокого уровня безоговорочно замещает значение из более низкого уровня.",
    "step_by_step": [
        "Определите перечисление слоев конфигурации ConfigLayer от LayerDefault до LayerCLI.",
        "Создайте структуру ConfigResolver, хранящую карты параметров для каждого слоя.",
        "Реализуйте алгоритм поиска ResolveParam: последовательный просмотр от самого приоритетного источника к дефолтам.",
        "Соберите строго типизированную структуру AppSettings с конвертацией типов (string -> int, bool).",
        "Проверьте правильность разрешения конфликтов при одновременном наличии параметра в файле, окружении и CLI."
    ],
    "code_blocks": [{
        "filename": "config_precedence_resolver.go",
        "lang": "go",
        "code": code24
    }],
    "under_the_hood": "Подобная цепочка ответственности (Chain of Responsibility) в библиотеках вроде Viper реализуется через внутреннее дерево `pflag.FlagSet` -> `envProvider` -> `remoteProvider` -> `v.override` -> `v.defaults`. При запросе ключа движок ищет первое непустое совпадение сверху вниз.",
    "pitfalls": [
        "Пустая строка как валидное значение: если переменная окружения установлена как `APP_FEATURE=\"\"`, резолвер должен отличать отсутствие переменной (`os.LookupEnv`) от намеренной установки пустой строки.",
        "Регистрозависимость: переменные окружения в Linux традиционно пишутся в `UPPER_SNAKE_CASE`, тогда как ключи в YAML — в `camelCase` или `kebab-case`. Резолвер должен нормализовать имена."
    ],
    "bigtech_interview": "Почему в 12-factor apps запрещено хранить пароли от продакшен-баз в файлах конфигурации в Git? Ответ: файлы в Git доступны широкому кругу инженеров и сохраняются в истории коммитов. Секреты должны поступать исключительно через переменные окружения, HashiCorp Vault или Kubernetes Secrets."
})

# Ex 25: Тестирование кода с фиче-флагами в Go юнит-тестах
code25 = '''package main

import (
	"context"
	"fmt"
	"sync"
)

// DiscountService рассчитывает скидки на заказ
type DiscountService struct {
	flagClient FeatureFlagClient
}

// FeatureFlagClient интерфейс клиента флагов
type FeatureFlagClient interface {
	BooleanValue(ctx context.Context, flagKey string, defaultValue bool) bool
}

func NewDiscountService(client FeatureFlagClient) *DiscountService {
	return &DiscountService{flagClient: client}
}

func (s *DiscountService) CalculateDiscount(ctx context.Context, amount float64) float64 {
	// Если включен флаг "black_friday_discount", даем 30% скидку, иначе 5%
	if s.flagClient.BooleanValue(ctx, "black_friday_discount", false) {
		return amount * 0.30
	}
	return amount * 0.05
}

// MockFeatureFlagClient потокобезопасный мок для юнит-тестов
type MockFeatureFlagClient struct {
	mu    sync.RWMutex
	flags map[string]bool
}

func NewMockFeatureFlagClient() *MockFeatureFlagClient {
	return &MockFeatureFlagClient{flags: make(map[string]bool)}
}

func (m *MockFeatureFlagClient) SetFlag(key string, val bool) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.flags[key] = val
}

func (m *MockFeatureFlagClient) BooleanValue(ctx context.Context, flagKey string, defaultValue bool) bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	if val, ok := m.flags[flagKey]; ok {
		return val
	}
	return defaultValue
}

func main() {
	// Демонстрация модульного теста обеих веток
	ctx := context.Background()
	mockClient := NewMockFeatureFlagClient()
	service := NewDiscountService(mockClient)

	// Тест 1: Флаг выключен (стандартная скидка 5%)
	mockClient.SetFlag("black_friday_discount", false)
	d1 := service.CalculateDiscount(ctx, 1000)
	fmt.Printf("Тест 1 (Флаг=false): Скидка = %.2f (Ожидалось 50.00)\\n", d1)

	// Тест 2: Флаг включен (Black Friday скидка 30%)
	mockClient.SetFlag("black_friday_discount", true)
	d2 := service.CalculateDiscount(ctx, 1000)
	fmt.Printf("Тест 2 (Флаг=true):  Скидка = %.2f (Ожидалось 300.00)\\n", d2)
}
'''
validate_go_code(code25, "code25")
exercises.append({
    "num": 25,
    "title": "Тестирование кода с фиче-флагами в Go юнит-тестах",
    "task": "Спроектируйте архитектуру тестирования бизнес-логики, зависящей от фиче-флагов. Выделите интерфейс FeatureFlagClient, реализуйте потокобезопасный MockFeatureFlagClient и напишите юнит-тесты, проверяющие обе ветки выполнения алгоритма без внешних зависимостей.",
    "theory": "Код, зависящий от фиче-флагов, требует 100% покрытия обеих ветвей (`flag=true` и `flag=false`). Распространенная анти-практика — тестировать код только с активным флагом, в результате чего при аварийном выключении флага в проде вызывается не протестированный fallback-код, приводящий к сбою.\n\nДля чистого тестирования в Go:\n1. Бизнес-сервис не должен зависеть от глобального синглтона флагов. Он принимает интерфейс `FeatureFlagClient` через конструктор.\n2. В тестах создается изолированный экземпляр `MockFeatureFlagClient`, позволяющий переключать флаги точечно в рамках каждого `t.Run()`.\n3. Мок должен быть потокобезопасным, чтобы поддерживать параллельное выполнение тестов с флагом `t.Parallel()`.",
    "step_by_step": [
        "Объявите минимальный интерфейс FeatureFlagClient с методом BooleanValue.",
        "Реализуйте сервис DiscountService, рассчитывающий скидки в зависимости от состояния флага.",
        "Напишите MockFeatureFlagClient с методом SetFlag() под защитой sync.RWMutex.",
        "Продемонстрируйте тестирование ветки со стандартным поведением (флаг выключен).",
        "Продемонстрируйте тестирование альтернативной ветки (флаг включен)."
    ],
    "code_blocks": [{
        "filename": "feature_flag_testing.go",
        "lang": "go",
        "code": code25
    }],
    "under_the_hood": "При использовании OpenFeature для тестов существует специальный официальный провайдер `inmemory.NewProvider(flagsMap)`. Он позволяет задать начальное состояние флагов для тестов без создания самодельных моков.",
    "pitfalls": [
        "Мутация глобального состояния флагов в тестах: если использовать `openfeature.SetProvider()` внутри юнит-теста, параллельные тесты с `t.Parallel()` начнут перетирать провайдер друг друга, вызывая флакующие тесты (flaky tests).",
        "Тестирование только ветки успеха: если флаг управляет новой платежной системой, обязательно нужно протестировать случай, когда сервер флагов вернул ошибку или дефолт."
    ],
    "bigtech_interview": "Как в CI гарантировать, что разработчики не забыли написать тесты на обе ветки флага? Используется анализ покрытия кода (Code Coverage). Если покрытие ветки `else` падает ниже 80%, мерж-реквест блокируется автоматической проверкой."
})

# Ex 26: Корреляция метрик и флагов в Prometheus / Grafana
code26 = '''package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"time"
)

// GrafanaAnnotationPayload структура аннотации для Grafana HTTP API
type GrafanaAnnotationPayload struct {
	DashboardUID string   `json:"dashboardUID,omitempty"`
	Time         int64    `json:"time"`
	TimeEnd      int64    `json:"timeEnd,omitempty"`
	Tags         []string `json:"tags"`
	Text         string   `json:"text"`
}

// GrafanaAnnotator отправляет маркеры релизов в Grafana
type GrafanaAnnotator struct {
	apiURL     string
	apiKey     string
	httpClient *http.Client
}

func NewGrafanaAnnotator(url, key string) *GrafanaAnnotator {
	return &GrafanaAnnotator{
		apiURL:     url,
		apiKey:     key,
		httpClient: &http.Client{Timeout: 3 * time.Second},
	}
}

func (a *GrafanaAnnotator) AnnotateFlagChange(ctx context.Context, flagKey string, oldVal, newVal any, author string) error {
	nowMs := time.Now().UnixMilli()
	text := fmt.Sprintf("🚩 <b>Feature Flag Changed:</b> <code>%s</code><br/>Значение: <code>%v</code> ➔ <code>%v</code><br/>Автор: %s",
		flagKey, oldVal, newVal, author)

	payload := GrafanaAnnotationPayload{
		Time: nowMs,
		Tags: []string{"feature-flag", flagKey, author},
		Text: text,
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, a.apiURL+"/api/annotations", bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+a.apiKey)

	resp, err := a.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("ошибка запроса к Grafana: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		return fmt.Errorf("grafana вернула статус: %d", resp.StatusCode)
	}
	return nil
}

func main() {
	// Мок сервера Grafana API
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var p GrafanaAnnotationPayload
		_ = json.NewDecoder(r.Body).Decode(&p)
		fmt.Printf("[GRAFANA MOCK] Получена аннотация: Tags=%v, Text=%s\\n", p.Tags, p.Text)
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"id": 42, "message": "Annotation added"}`))
	}))
	defer server.Close()

	annotator := NewGrafanaAnnotator(server.URL, "eyJrZXkiOiJteS10ZXN0LWtleSJ9")

	err := annotator.AnnotateFlagChange(context.Background(), "payment_gateway_v2", false, true, "sre-lead")
	if err != nil {
		panic(err)
	}
	fmt.Println("Аннотация успешно зарегистрирована для наложения на графики задержек и ошибок.")
}
'''
validate_go_code(code26, "code26")
exercises.append({
    "num": 26,
    "title": "Корреляция метрик и флагов в Prometheus / Grafana",
    "task": "Реализуйте интеграцию с Grafana Annotations API. Напишите сервис GrafanaAnnotator, который при каждом переключении фиче-флага отправляет вертикальный маркер события с тегами и HTML-описанием изменения для визуальной корреляции с графиками задержек (p99 latency) и частоты ошибок (5xx error rate).",
    "theory": "Во время инцидента в production SRE-инженеры первым делом смотрят на графики Grafana: внезапный скачок 5xx ошибок или рост задержек p99. Главный вопрос: 'Что изменилось в этот момент? Был деплой или переключение флага?'.\n\nGrafana предоставляет мощный механизм Annotations: на графики метрик накладываются вертикальные пунктирные линии событий. Создавая аннотацию в момент переключения флага (через Grafana HTTP API `POST /api/annotations`), команда мгновенно видит прямую причинно-следственную связь: вертикальная линия 'Включен флаг payment_v2' совпадает с точкой роста ошибок, что позволяет откатить флаг за секунды без гадания в логах.",
    "step_by_step": [
        "Изучите схему полезной нагрузки Grafana Annotations API.",
        "Реализуйте структуру GrafanaAnnotationPayload с метками времени в миллисекундах и массивом тегов.",
        "Создайте сервис GrafanaAnnotator с авторизацией по Bearer Token.",
        "Сформируйте структурированное HTML-сообщение с описанием старого/нового значения и автора.",
        "Протестируйте отправку аннотации на мок-сервере httptest."
    ],
    "code_blocks": [{
        "filename": "grafana_flag_annotator.go",
        "lang": "go",
        "code": code26
    }],
    "under_the_hood": "Помимо прямых HTTP-аннотаций, в мониторинге используется экспорт состояния всех флагов как Prometheus-метрик: `feature_flag_state{flag_name=\"checkout_v2\", state=\"enabled\"} 1`. В запросах PromQL можно использовать операцию умножения векторов (`rate(http_requests_total[5m]) * on(flag_name) group_left feature_flag_state`) для фильтрации метрик по активным флагам.",
    "pitfalls": [
        "Синхронный вызов Grafana в критическом пути: сетевой сбой при обращении к Grafana не должен прерывать или задерживать применение флага. Вызовы должны отправляться асинхронно.",
        "Отсутствие тегов: если не добавлять теги `feature-flag` и конкретное имя флага, аннотации будут отображаться на всех дашбордах подряд, создавая визуальный шум."
    ],
    "bigtech_interview": "Какова разница между метриками (Prometheus) и событиями (Grafana Annotations)? Метрики — это числовые временные ряды, фиксирующие факт деградации. Аннотации событий — это дискретные контекстные маркеры изменений конфигурации, связывающие телеметрию с действиями людей."
})

# Ex 27: Безопасный оффлайн-режим (Graceful Fallback) при сбое сервера флагов
code27 = '''package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"sync"
	"time"
)

// FallbackProvider обеспечивает непрерывную работу при сетевых сбоях
type FallbackProvider struct {
	remoteURL     string
	diskCachePath string
	mu            sync.RWMutex
	cache         map[string]bool
	isOnline      bool
}

func NewFallbackProvider(cachePath string) *FallbackProvider {
	p := &FallbackProvider{
		diskCachePath: cachePath,
		cache:         make(map[string]bool),
		isOnline:      false,
	}
	p.loadFromDisk()
	return p
}

func (p *FallbackProvider) loadFromDisk() {
	data, err := os.ReadFile(p.diskCachePath)
	if err != nil {
		return // Дисковый кэш отсутствует, остаемся на пустом кэше
	}
	var loaded map[string]bool
	if err := json.Unmarshal(data, &loaded); err == nil {
		p.mu.Lock()
		p.cache = loaded
		p.mu.Unlock()
		fmt.Printf("[FALLBACK INIT] Загружено %d флагов из локального дискового снапшота\\n", len(loaded))
	}
}

func (p *FallbackProvider) persistToDisk() {
	p.mu.RLock()
	data, err := json.MarshalIndent(p.cache, "", "  ")
	p.mu.RUnlock()
	if err == nil {
		_ = os.WriteFile(p.diskCachePath, data, 0644)
	}
}

// EvaluateFlag возвращает флаг: 1) из памяти, 2) fallback на defaultValue при полном отсутствии
func (p *FallbackProvider) EvaluateFlag(flagKey string, defaultValue bool) (bool, string) {
	p.mu.RLock()
	defer p.mu.RUnlock()

	val, exists := p.cache[flagKey]
	if exists {
		if p.isOnline {
			return val, "ONLINE_PROVIDER"
		}
		return val, "FALLBACK_CACHED_SNAPSHOT"
	}

	return defaultValue, "DEFAULT_SAFE_FALLBACK"
}

// SimulateRemoteSync эмулирует периодическую синхронизацию
func (p *FallbackProvider) SimulateRemoteSync(remoteSuccess bool, remoteFlags map[string]bool) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if remoteSuccess {
		p.isOnline = true
		for k, v := range remoteFlags {
			p.cache[k] = v
		}
		p.persistToDisk()
		fmt.Println("[SYNC SUCCESS] Флаги успешно обновлены с удаленного сервера.")
	} else {
		p.isOnline = false
		fmt.Println("[SYNC FAILED] Удаленный сервер недоступен! Переход в автономный Fallback-режим.")
	}
}

func main() {
	cacheFile := "/tmp/flags_offline_cache.json"
	defer os.Remove(cacheFile)

	provider := NewFallbackProvider(cacheFile)

	// Шаг 1: Сервер онлайн, синхронизируем данные
	provider.SimulateRemoteSync(true, map[string]bool{
		"new_search_engine": true,
		"enable_ai_chat":    false,
	})

	val, reason := provider.EvaluateFlag("new_search_engine", false)
	fmt.Printf("Поиск v2: %v (Источник: %s)\\n", val, reason)

	// Шаг 2: Сервер флагов упал (сетевая изоляция)
	provider.SimulateRemoteSync(false, nil)

	// Сервис продолжает работу без ошибок, используя сохраненный снапшот
	val, reason = provider.EvaluateFlag("new_search_engine", false)
	fmt.Printf("Поиск v2 во время аварии: %v (Источник: %s)\\n", val, reason)

	// Неизвестный флаг возвращает безопасный дефолт
	valUnknown, reasonUnknown := provider.EvaluateFlag("unregistered_flag", false)
	fmt.Printf("Неизвестный флаг: %v (Источник: %s)\\n", valUnknown, reasonUnknown)
}
'''
validate_go_code(code27, "code27")
exercises.append({
    "num": 27,
    "title": "Безопасный оффлайн-режим (Graceful Fallback) при сбое сервера флагов",
    "task": "Спроектируйте отказоустойчивый провайдер FallbackProvider, поддерживающий трехуровневую стратегию надежности: 1) Оперативная память (In-Memory L1), 2) Резервный дисковый снапшот при рестарте пода во время сетевой аварии, 3) Гарантированный возврат безопасного дефолта (Safe Default).",
    "theory": "Сервер управления фиче-флагами (Flipt, Unleash, LaunchDarkly) — это внешняя сетевая зависимость. Если Go-микросервис будет делать синхронный сетевой RPC-запрос на каждый `client.BooleanValue()`, то при аварии сервера флагов встанет весь бизнес сервиса.\n\nПаттерн Graceful Degradation / Fallback требует:\n1. Локального кэширования: микросервис всегда читает флаги из локальной памяти.\n2. Асинхронной синхронизации: фоновая горутина опрашивает удаленный сервер или слушает gRPC/WebSocket стрим изменений.\n3. Дисковой персистентности: при перезапуске пода в условиях полного отказа сети сервис читает последний известный снапшот с диска.\n4. Безопасного значения по умолчанию (Fail-Safe Default): если флаг не найден вообще, возвращается жестко закодированное безопасное значение.",
    "step_by_step": [
        "Создайте структуру FallbackProvider с локальной картой в памяти и путем к дисковому снапшоту.",
        "Реализуйте метод loadFromDisk() для восстановления состояния при холодном старте без сети.",
        "В методе EvaluateFlag() обеспечьте возврат значения с метаданными источника (ONLINE, CACHED_SNAPSHOT, SAFE_DEFAULT).",
        "Реализуйте эмуляцию падения сети и продемонстрируйте безотказное обслуживание запросов.",
        "Проверьте сохранение последнего валидного снапшота на диск при успешной синхронизации."
    ],
    "code_blocks": [{
        "filename": "graceful_fallback_provider.go",
        "lang": "go",
        "code": code27
    }],
    "under_the_hood": "Такой подход называется Local Evaluation Mode (локальное вычисление). Вместо отправки контекста пользователя на удаленный сервер, клиент скачивает полный набор правил таргетинга в память и вычисляет их локально за 100 наносекунд, обеспечивая абсолютную автономность.",
    "pitfalls": [
        "Блокировка старта сервиса: если в конструкторе `NewProvider()` делать синхронный HTTP-запрос к серверу флагов с таймаутом 30 секунд, под не сможет пройти Kubernetes Startup Probe и попадет в CrashLoopBackOff.",
        "Использование unsafe default: дефолтным значением для флагов платежей или критических операций всегда должно быть консервативное `false` (Fail Closed)."
    ],
    "bigtech_interview": "Что выбрать: Fail-Open или Fail-Closed при сбое флагов безопасности? Для рубильников безопасности (например, блокировки подозрительных IP) обычно выбирают Fail-Open (пропустить трафик), чтобы не заблокировать легитимных клиентов. Для финансовых транзакций — строго Fail-Closed."
})

# Ex 28: Мультитенантные фиче-флаги в B2B SaaS
code28 = '''package main

import (
	"context"
	"fmt"
	"strings"
)

// TenantTier тарифный план клиента
type TenantTier string

const (
	TierFree       TenantTier = "free"
	TierPro        TenantTier = "pro"
	TierEnterprise TenantTier = "enterprise"
)

// TenantContext контекст B2B клиента
type TenantContext struct {
	TenantID string
	Tier     TenantTier
	UserID   string
}

// MultiTenantFlagRule правила флага для SaaS
type MultiTenantFlagRule struct {
	GlobalEnabled bool
	AllowedTiers  map[TenantTier]bool
	TenantOverrides map[string]bool
	UserOverrides   map[string]bool
}

// MultiTenantFlagEngine движок иерархической оценки
type MultiTenantFlagEngine struct {
	rules map[string]MultiTenantFlagRule
}

func NewMultiTenantFlagEngine() *MultiTenantFlagEngine {
	return &MultiTenantFlagEngine{
		rules: make(map[string]MultiTenantFlagRule),
	}
}

func (e *MultiTenantFlagEngine) RegisterRule(flagKey string, rule MultiTenantFlagRule) {
	e.rules[flagKey] = rule
}

// Evaluate разрешает флаг по иерархии: User Override > Tenant Override > Tier Allowed > Global
func (e *MultiTenantFlagEngine) Evaluate(flagKey string, tc TenantContext) (bool, string) {
	rule, ok := e.rules[flagKey]
	if !ok || !rule.GlobalEnabled {
		return false, "GLOBAL_DISABLED"
	}

	// 1. Точечный оверрайд для конкретного пользователя (Pilot User)
	if tc.UserID != "" {
		if val, exists := rule.UserOverrides[tc.UserID]; exists {
			return val, "USER_OVERRIDE"
		}
	}

	// 2. Индивидуальный оверрайд для конкретной компании (Enterprise Beta Tenant)
	if tc.TenantID != "" {
		if val, exists := rule.TenantOverrides[tc.TenantID]; exists {
			return val, "TENANT_OVERRIDE"
		}
	}

	// 3. Доступность по тарифному плану (Tier Gate)
	if rule.AllowedTiers[tc.Tier] {
		return true, "TIER_ENTITLED"
	}

	return false, "TIER_NOT_ENTITLED"
}

func main() {
	engine := NewMultiTenantFlagEngine()

	// Настройка флага "advanced_analytics"
	engine.RegisterRule("advanced_analytics", MultiTenantFlagRule{
		GlobalEnabled: true,
		AllowedTiers: map[TenantTier]bool{
			TierEnterprise: true,
		},
		TenantOverrides: map[string]bool{
			"tenant_beta_corp": true, // Компания на Pro тарифе, участвующая в закрытой бете
		},
		UserOverrides: map[string]bool{
			"usr_special_tester": true, // Точечный пользователь на Free тарифе
		},
	})

	testCases := []struct {
		desc string
		ctx  TenantContext
	}{
		{
			desc: "Обычный пользователь Free",
			ctx:  TenantContext{TenantID: "comp_1", Tier: TierFree, UserID: "u1"},
		},
		{
			desc: "Пользователь Enterprise тарифа",
			ctx:  TenantContext{TenantID: "comp_2", Tier: TierEnterprise, UserID: "u2"},
		},
		{
			desc: "Pro компания из закрытой беты (Tenant Override)",
			ctx:  TenantContext{TenantID: "tenant_beta_corp", Tier: TierPro, UserID: "u3"},
		},
		{
			desc: "Спец-пользователь на Free тарифе (User Override)",
			ctx:  TenantContext{TenantID: "comp_free", Tier: TierFree, UserID: "usr_special_tester"},
		},
	}

	for _, tc := range testCases {
		enabled, reason := engine.Evaluate("advanced_analytics", tc.ctx)
		fmt.Printf("%-50s -> Включен: %-5v (Причина: %s)\\n", tc.desc, enabled, reason)
	}
}
'''
validate_go_code(code28, "code28")
exercises.append({
    "num": 28,
    "title": "Мультитенантные фиче-флаги в B2B SaaS",
    "task": "Спроектируйте многоуровневый движок оценки флагов MultiTenantFlagEngine для корпоративных B2B SaaS систем. Реализуйте строгую иерархию разрешения: 1) Точечный пользователь (User Override) -> 2) Организация (Tenant Override) -> 3) Тарифный план (Tier Entitlement) -> 4) Глобальный рубильник.",
    "theory": "В B2B SaaS архитектуре управление фичами тесно переплетено с монетизацией (Feature Entitlement). Один и тот же функционал (например, SAML SSO, аудит-логи или экспорт данных) доступен не всем пользователям, а зависит от контракта организации.\n\nТребуется иерархическая модель вычисления:\n1. Global Toggle: аварийный флаг, отключающий фичу для всех тенантов при сбое.\n2. Tier Entitlement: доступность фичи в рамках тарифа (`Enterprise`, `Pro`, `Free`).\n3. Tenant Override: возможность выдать доступ конкретной компании-партнеру на тарифе `Pro` в качестве бонуса или пилота.\n4. User Override: точечный доступ для конкретного VIP-пользователя или внутреннего тестировщика внутри тенанта.",
    "step_by_step": [
        "Определите тип TenantTier и структуру контекста запроса TenantContext.",
        "Спроектируйте правила флага MultiTenantFlagRule со словарями тарифов и оверрайдов.",
        "Реализуйте метод Evaluate() с последовательной проверкой от частного к общему.",
        "Продемонстрируйте корректность работы на тестовых пользователях разных тарифов.",
        "Выведите причину оценки (Reason) для аудита и логирования."
    ],
    "code_blocks": [{
        "filename": "multitenant_flag_engine.go",
        "lang": "go",
        "code": code28
    }],
    "under_the_hood": "В крупных облачных платформах (AWS, Stripe) мультитенантные правила компилируются в префиксные бинарные деревья или таблицы маршрутизации, что позволяет выполнять оценку миллионов клиентов за константное время O(1) без обращения к базе данных тенантов.",
    "pitfalls": [
        "Cross-Tenant Data Leak: случайное включение оверрайда для организации `comp_1` не должно влиять на `comp_2`. Ключи тенантов должны быть строго изолированы.",
        "Забытый Global Kill Switch: если в реализации оверрайд пользователя проверяется раньше глобального флага, аварийное отключение не заблокирует пользователей из оверрайда."
    ],
    "bigtech_interview": "В чем разница между Feature Flagging и RBAC (Role-Based Access Control)? RBAC отвечает на вопрос 'Имеет ли пользователь право выполнить операцию?' (авторизация), а Feature Flagging — 'Доступен ли данный функционал в системе прямо сейчас и активен ли этот путь выполнения?'."
})

# Ex 29: Автоматический откат канареечных релизов (Auto-Rollback)
code29 = '''package main

import (
	"context"
	"fmt"
	"math/rand"
	"sync"
	"time"
)

// MetricsClient интерфейс чтения метрик из Prometheus
type MetricsClient interface {
	GetErrorRate(ctx context.Context, service string) (float64, error)
}

// CanarySupervisor осуществляет мониторинг и авто-откат
type CanarySupervisor struct {
	flagKey        string
	thresholdErr   float64
	checkInterval  time.Duration
	metrics        MetricsClient
	flagSetter     func(flagKey string, enabled bool)
	mu             sync.Mutex
	isCanaryActive bool
}

func NewCanarySupervisor(
	flagKey string,
	thresholdErr float64,
	interval time.Duration,
	metrics MetricsClient,
	setter func(flagKey string, enabled bool),
) *CanarySupervisor {
	return &CanarySupervisor{
		flagKey:       flagKey,
		thresholdErr:  thresholdErr,
		checkInterval: interval,
		metrics:       metrics,
		flagSetter:    setter,
	}
}

// StartMonitoring запускает цикл проверки канарейки
func (s *CanarySupervisor) StartMonitoring(ctx context.Context) {
	s.mu.Lock()
	s.isCanaryActive = true
	s.mu.Unlock()

	ticker := time.NewTicker(s.checkInterval)
	defer ticker.Stop()

	fmt.Printf("[SUPERVISOR] Запущен мониторинг канарейки флага %s (Порог ошибок: %.2f%%)\\n",
		s.flagKey, s.thresholdErr*100)

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			rate, err := s.metrics.GetErrorRate(ctx, s.flagKey)
			if err != nil {
				fmt.Printf("[SUPERVISOR WARN] Ошибка получения метрик: %v\\n", err)
				continue
			}

			fmt.Printf("[SUPERVISOR CHECK] Текущий процент ошибок 5xx: %.2f%%\\n", rate*100)

			if rate > s.thresholdErr {
				s.mu.Lock()
				if s.isCanaryActive {
					fmt.Printf("🚨 [AUTO-ROLLBACK] Превышен порог ошибок (%.2f%% > %.2f%%)! Аварийный откат флага %s!\\n",
						rate*100, s.thresholdErr*100, s.flagKey)
					s.flagSetter(s.flagKey, false)
					s.isCanaryActive = false
				}
				s.mu.Unlock()
				return
			}
		}
	}
}

// MockPrometheusClient мокирует ответы Prometheus API
type MockPrometheusClient struct {
	errRates []float64
	idx      int
	mu       sync.Mutex
}

func (m *MockPrometheusClient) GetErrorRate(ctx context.Context, service string) (float64, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	if m.idx < len(m.errRates) {
		r := m.errRates[m.idx]
		m.idx++
		return r, nil
	}
	return 0.001, nil
}

func main() {
	currentFlags := map[string]bool{"canary_order_v2": true}
	var flagMu sync.Mutex

	flagSetter := func(k string, val bool) {
		flagMu.Lock()
		defer flagMu.Unlock()
		currentFlags[k] = val
		fmt.Printf("[FLAG MANAGER] Флаг %s переключен в значение: %v\\n", k, val)
	}

	// Моделируем скачок ошибок на 3-й проверке: 0.1% -> 0.2% -> 1.8% (авария)
	mockPrometheus := &MockPrometheusClient{
		errRates: []float64{0.001, 0.002, 0.018},
	}

	supervisor := NewCanarySupervisor(
		"canary_order_v2",
		0.005, // Порог 0.5% ошибок
		50*time.Millisecond,
		mockPrometheus,
		flagSetter,
	)

	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()

	supervisor.StartMonitoring(ctx)

	flagMu.Lock()
	fmt.Printf("Состояние флага после работы супервизора: %v (должен быть false)\\n", currentFlags["canary_order_v2"])
	flagMu.Unlock()
}
'''
validate_go_code(code29, "code29")
exercises.append({
    "num": 29,
    "title": "Автоматический откат канареечных релизов (Auto-Rollback)",
    "task": "Реализуйте фоновый супервизор канареечных раскаток CanarySupervisor. Супервизор должен периодически опрашивать метрики Prometheus API, и в случае превышения допустимого порога ошибок (например, > 0.5% HTTP 5xx) мгновенно отключать флаг канарейки, предотвращая распространение сбоя на всех пользователей.",
    "theory": "Ручной мониторинг канареечных релизов неэффективен: человеку требуются минуты, чтобы заметить всплеск графиков в Grafana, принять решение и нажать кнопку отката. За эти минуты миллионы пользователей получат ошибку оформления заказа.\n\nAuto-Rollback (автоматический откат) — ключевой компонент современного непрерывного развертывания (Continuous Delivery):\n1. Супервизор запускается параллельно с включением канареечного флага на процент аудитории (1–10%).\n2. Каждые N секунд супервизор выполняет запрос к Prometheus (или Loki / Sentry) для оценки ключевых SLI (Service Level Indicators): частота HTTP 5xx, p99 задержка, процент panic.\n3. Если показатели деградируют выше установленного порога (Error Budget Exceeded), супервизор атомарно выключает флаг и генерирует PagerDuty-инцидент.",
    "step_by_step": [
        "Определите интерфейс MetricsClient с методом GetErrorRate.",
        "Спроектируйте структуру CanarySupervisor с пороговым значением, интервалом проверки и коллбэком переключения флага.",
        "В методе StartMonitoring реализуйте цикл с time.Ticker для регулярного контроля метрик.",
        "При превышении порога выполните атомарный откат флага в false и завершите мониторинг.",
        "Протестируйте реакцию супервизора на эмуляции скачка ошибок."
    ],
    "code_blocks": [{
        "filename": "canary_auto_rollback.go",
        "lang": "go",
        "code": code29
    }],
    "under_the_hood": "В Kubernetes-экосистеме подобную логику реализуют операторы прогрессивной доставки, такие как Argo Rollouts и Flagger. Однако реализация авто-отката на уровне фиче-флагов в Go работает в десятки раз быстрее, так как не требует пересоздания подов и ожидания rolling update пода.",
    "pitfalls": [
        "Ложный откат при недостаточном объеме трафика: если за 10 секунд пришло всего 2 запроса и один вернул ошибку, процент составит 50%. Супервизор должен проверять минимальный объем трафика (Min Requests Volume), например > 100 запросов.",
        "Сетевая ошибка самого Prometheus: если мониторинг временно не отвечает, нельзя сразу откатывать релиз — необходимо учитывать серию последовательных ошибок (Consecutive Failures)."
    ],
    "bigtech_interview": "Что такое 'Burn Rate Alerting' в SRE? Вместо простого порога ошибок оценивается скорость расходования бюджета ошибок (Error Budget). Если при текущей частоте сбоев месячный бюджет SLO сгорит за 1 час, авто-откат срабатывает незамедлительно."
})

# Ex 30: Комплексная платформа Release Engineering и Dynamic Config на Go
code30 = '''package main

import (
	"context"
	"errors"
	"fmt"
	"hash/crc32"
	"sync"
	"sync/atomic"
	"time"
)

// SystemConfig описывает глобальные параметры рантайма
type SystemConfig struct {
	MaxRPS      int           `json:"max_rps"`
	Timeout     time.Duration `json:"timeout"`
	Maintenance bool          `json:"maintenance"`
}

func (c *SystemConfig) Validate() error {
	if c.MaxRPS <= 0 {
		return errors.New("max_rps должен быть > 0")
	}
	if c.Timeout <= 0 || c.Timeout > 30*time.Second {
		return errors.New("timeout вне допустимого диапазона (0, 30s]")
	}
	return nil
}

// EnterpriseFlag описывает флаг раскатки
type EnterpriseFlag struct {
	Key             string
	Percentage      uint32
	AllowBetaUsers  bool
	KillSwitch      bool
	UserOverrides   map[string]bool
}

// EnterpriseReleasePlatform объединяет динамический конфиг и умные флаги
type EnterpriseReleasePlatform struct {
	cfgHolder atomic.Pointer[SystemConfig]

	flagsMu sync.RWMutex
	flags   map[string]EnterpriseFlag

	evalMetrics atomic.Uint64
}

func NewEnterpriseReleasePlatform(initialCfg SystemConfig) (*EnterpriseReleasePlatform, error) {
	if err := initialCfg.Validate(); err != nil {
		return nil, fmt.Errorf("стартовый конфиг невалиден: %w", err)
	}

	p := &EnterpriseReleasePlatform{
		flags: make(map[string]EnterpriseFlag),
	}
	p.cfgHolder.Store(&initialCfg)
	return p, nil
}

// UpdateConfig атомарно и безопасно подменяет конфигурацию
func (p *EnterpriseReleasePlatform) UpdateConfig(newCfg SystemConfig) error {
	if err := newCfg.Validate(); err != nil {
		return fmt.Errorf("обновление отклонено: %w", err)
	}
	p.cfgHolder.Store(&newCfg)
	return nil
}

func (p *EnterpriseReleasePlatform) GetConfig() *SystemConfig {
	return p.cfgHolder.Load()
}

func (p *EnterpriseReleasePlatform) SetFlag(flag EnterpriseFlag) {
	p.flagsMu.Lock()
	defer p.flagsMu.Unlock()
	p.flags[flag.Key] = flag
}

// EvaluateFlag проверяет доступность фичи для пользователя
func (p *EnterpriseReleasePlatform) EvaluateFlag(flagKey string, userID string, isBeta bool) (bool, string) {
	p.evalMetrics.Add(1)

	// Если система в режиме обслуживания, отключаем экспериментальные фичи
	if p.GetConfig().Maintenance {
		return false, "MAINTENANCE_MODE"
	}

	p.flagsMu.RLock()
	flag, exists := p.flags[flagKey]
	p.flagsMu.RUnlock()

	if !exists {
		return false, "FLAG_NOT_FOUND"
	}

	// 1. Аварийный рубильник
	if flag.KillSwitch {
		return false, "KILL_SWITCH_ACTIVE"
	}

	// 2. Индивидуальный оверрайд
	if val, ok := flag.UserOverrides[userID]; ok {
		return val, "USER_OVERRIDE"
	}

	// 3. Бета-тестеры
	if isBeta && flag.AllowBetaUsers {
		return true, "BETA_TESTER_MATCH"
	}

	// 4. Детерминированная процентная раскатка (Canary Rollout)
	if flag.Percentage > 0 {
		hash := crc32.ChecksumIEEE([]byte(flagKey + ":" + userID))
		slot := hash % 100
		if slot < flag.Percentage {
			return true, "PERCENTAGE_ROLLOUT"
		}
	}

	return false, "NOT_IN_SEGMENT"
}

func (p *EnterpriseReleasePlatform) TotalEvaluations() uint64 {
	return p.evalMetrics.Load()
}

func main() {
	initialCfg := SystemConfig{
		MaxRPS:      2500,
		Timeout:     5 * time.Second,
		Maintenance: false,
	}

	platform, err := NewEnterpriseReleasePlatform(initialCfg)
	if err != nil {
		panic(err)
	}

	// Регистрируем флаг новой платежной системы на 25% пользователей
	platform.SetFlag(EnterpriseFlag{
		Key:            "payment_flow_v3",
		Percentage:     25,
		AllowBetaUsers: true,
		KillSwitch:     false,
		UserOverrides: map[string]bool{
			"vip_customer_99": true,
		},
	})

	users := []struct {
		id     string
		isBeta bool
	}{
		{"user_101", false},
		{"user_202", false},
		{"user_303", true}, // Бета-пользователь
		{"vip_customer_99", false}, // Оверрайд
	}

	fmt.Println("=== Фаза 1: Оценка пользователей при штатной работе ===")
	for _, u := range users {
		active, reason := platform.EvaluateFlag("payment_flow_v3", u.id, u.isBeta)
		fmt.Printf("Пользователь %-16s -> Фича: %-5v (Причина: %s)\\n", u.id, active, reason)
	}

	// Включаем аварийный рубильник
	fmt.Println("\\n=== Фаза 2: Активация Kill Switch инженером On-Call ===")
	platform.SetFlag(EnterpriseFlag{
		Key:        "payment_flow_v3",
		KillSwitch: true,
	})

	active, reason := platform.EvaluateFlag("payment_flow_v3", "vip_customer_99", false)
	fmt.Printf("Пользователь vip_customer_99 во время аварии -> Фича: %-5v (Причина: %s)\\n", active, reason)

	fmt.Printf("\\nВсего выполнено вычислений телеметрии: %d\\n", platform.TotalEvaluations())
}
'''
validate_go_code(code30, "code30")
exercises.append({
    "num": 30,
    "title": "Комплексная платформа Release Engineering и Dynamic Config на Go",
    "task": "Разработайте единую корпоративную платформу EnterpriseReleasePlatform, объединяющую динамический конфиг на atomic.Pointer с валидацией, детерминированные процентные раскатки на crc32, поддержку бета-пользователей, аварийный Kill Switch и сбор метрик вычислений.",
    "theory": "В завершающем упражнении мы синтезируем все ключевые концепции главы в законченный модуль уровня Staff Engineer:\n1. Управление конфигурацией: lock-free хранилище на `atomic.Pointer[SystemConfig]` с двухфазной валидацией инвариантов.\n2. Управление релизами: многоуровневая оценка фиче-флагов (Kill Switch -> User Override -> Beta Group -> Hash-based Percentage Rollout).\n3. Высокая производительность: отсутствие аллокаций памяти в горячем пути, масштабируемость на десятки процессорных ядер, потокобезопасность и встроенная телеметрия.\n\nТакая платформа лежит в основе релизных процессов ведущих технологических гигантов, позволяя раскатывать тысячи изменений в день без риска масштабных даунтаймов.",
    "step_by_step": [
        "Спроектируйте структуру SystemConfig с валидацией тайм-аутов и лимитов нагрузки.",
        "Определите EnterpriseFlag с поддержкой процентных раскаток, бета-групп и Kill Switch.",
        "Реализуйте EnterpriseReleasePlatform с хранением конфига через atomic.Pointer.",
        "В методе EvaluateFlag объедините все правила оценки с приоритетом рубильников безопасности.",
        "Добавьте атомарный счетчик обращений для мониторинга активности.",
        "Продемонстрируйте штатную раскатку, обработку оверрайдов и реакцию на включение Kill Switch."
    ],
    "code_blocks": [{
        "filename": "enterprise_release_platform.go",
        "lang": "go",
        "code": code30
    }],
    "under_the_hood": "Использование единой платформы гарантирует консистентность: флаги могут автоматически отключаться не только вручную, но и при переводе системы в режим технического обслуживания (`Maintenance: true`) через динамический конфиг.",
    "pitfalls": [
        "Неконсистентное состояние: если в процессе раскатки изменить процент с 25% на 15%, часть пользователей потеряет доступ к новой фиче. Процентные раскатки должны быть строго монотонными (только на увеличение).",
        "Утечка памяти в мапах оверрайдов: добавление миллионов индивидуальных пользователей в карту флага в памяти забьет кучу Go. Для больших когорт нужно использовать сегменты и фильтры Блума."
    ],
    "bigtech_interview": "Как спроектировать Release Engineering платформу для 50 000 RPS? На интервью Staff Engineer ожидают: децентрализованная архитектура с локальной оценкой в памяти (SDK), распространение правил через Kafka/gRPC стрим с etcd/Redis, и локальное lock-free вычисление без единой внешней блокировки."
})

# Save Part 2
out_path = '/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch94_p2.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Chapter 94 Part 2 generated successfully: {len(exercises)} exercises.")
