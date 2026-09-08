import json
import subprocess
import os

def validate_go(code):
    p = subprocess.run(['gofmt', '-e'], input=code.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise ValueError(f"Go syntax error: {p.stderr.decode('utf-8')}\nCode:\n{code}")

exercises = []

# Ex 1
ex1_code = """package main

import (
	"fmt"
)

// ReleasePrinciple демонстрирует концептуальное различие между развертыванием и релизом.
type ReleasePrinciple struct {
	Concept    string
	Definition string
	Tooling    string
	Risk       string
}

func GetReleaseEngineeringPrinciples() []ReleasePrinciple {
	return []ReleasePrinciple{
		{
			Concept:    "Deployment (Деплой)",
			Definition: "Физическая доставка скомпилированного бинарного артефакта на серверы или поды Kubernetes",
			Tooling:    "CI/CD пайплайны, Docker, Helm, ArgoCD, Kubernetes Deployments",
			Risk:       "Низкий: код уже на сервере, но неактивен и недоступен пользователям (Dark Launch)",
		},
		{
			Concept:    "Release (Релиз)",
			Definition: "Открытие функционала реальным пользователям (бизнес-момент запуска)",
			Tooling:    "Feature Flags (OpenFeature, LaunchDarkly, Flipt), Canary Routing, A/B тесты",
			Risk:       "Управляемый: плавное включение для 1% -> 10% -> 100% с возможностью отката за 50 мс",
		},
	}
}

func main() {
	fmt.Println("Фундаментальный принцип Enterprise Release Engineering: Deploy != Release")
	for _, p := range GetReleaseEngineeringPrinciples() {
		fmt.Printf("--> [%s]\\n    Определение: %s\\n    Инструменты: %s\\n    Риски:       %s\\n",
			p.Concept, p.Definition, p.Tooling, p.Risk)
	}
	fmt.Println("\\nПреимущество: Trunk-Based Development устраняет долгоживущие ветки и исключает Merge Hell!")
}
"""
validate_go(ex1_code)

exercises.append({
    "num": 1,
    "title": "Философия Feature Flags: разделение деплоя и релиза",
    "task": "Изучите фундаментальный принцип современной Enterprise-разработки: Deploy != Release. Спроектируйте сравнительную модель Deployment vs Release, объясните преимущества Trunk-Based Development и устранение проблемы 'интеграционного ада' (Merge Hell).",
    "theory": "В классическом GitFlow разработчики создавали долгоживущие фиче-ветки (Feature Branches), которые разрабатывались неделями. Слияние такой ветки в main приводило к десяткам конфликтов (Merge Hell) и огромному стрессу при релизе. Современный стандарт Enterprise-инженерии — Trunk-Based Development и принцип Deploy != Release:\\n1. Deployment (деплой) — техническое действие. Код сливается в main ежедневно малыми порциями и автоматически выкатывается на прод. Незавершенный функционал закрывается фиче-флагом (Feature Flag). Для пользователей ничего не меняется.\\n2. Release (релиз) — бизнес-действие. Включение функционала происходит динамически через панель управления флагами без повторной сборки и без повторного деплоя бинарника. Если релиз вызвал сбои, флаг выключается за 50 мс без ожидания 20-минутного CI/CD пайплайна отката.",
    "step_by_step": "1. Спроектируйте структуру ReleasePrinciple с полями Concept, Definition, Tooling, Risk.\\n2. Реализуйте функцию GetReleaseEngineeringPrinciples со сравнительными метриками.\\n3. Опишите влияние на культуру Trunk-Based Development.\\n4. Протестируйте вывод концептуального отчета.",
    "code_blocks": [{"filename": "deploy_vs_release.go", "lang": "go", "code": ex1_code}],
    "under_the_hood": "Фиче-флаги переносят решения о доступности функционала из фазы компиляции (Compile-time) в фазу выполнения программы (Runtime Evaluation).",
    "pitfalls": "Опасность превращения кода в лабиринт неиспользуемых флагов (Flag Debt): каждый флаг должен иметь четкий срок жизни и удаляться из кодовой базы после завершения 100% раскатки.",
    "bigtech_interview": "Почему BigTech компании (Google, Meta, Яндекс) практически полностью перешли на Trunk-Based Development и фиче-флаги, отказавшись от GitFlow?"
})

# Ex 2
ex2_code = """package main

import (
	"fmt"
	"time"
)

// FlagCategory классифицирует типы флагов по классификации Мартина Фаулера.
type FlagCategory struct {
	Name        string
	Lifespan    string
	Dynamism    string
	Description string
	Example     string
}

func GetFowlerFlagCategories() []FlagCategory {
	return []FlagCategory{
		{
			Name:        "Release Toggles",
			Lifespan:    "Дни - 2 недели (временные)",
			Dynamism:    "Статические или квази-динамические",
			Description: "Скрывают незавершенный код в ветке main до момента полного релиза фичи",
			Example:     "feature_new_checkout_flow: false",
		},
		{
			Name:        "Experiment Toggles",
			Lifespan:    "Недели - месяцы (временные)",
			Dynamism:    "Высокодинамичные per request",
			Description: "Используются для A/B тестирования и многовариантных экспериментов конверсии",
			Example:     "ab_test_button_color: 'blue' vs 'green'",
		},
		{
			Name:        "Ops Toggles (Kill Switches)",
			Lifespan:    "Годы / Навсегда (постоянные)",
			Dynamism:    "Динамические рубильники",
			Description: "Аварийные выключатели тяжелых подсистем при резких пиках нагрузки и DoS",
			Example:     "enable_heavy_ml_recommendations: true/false",
		},
		{
			Name:        "Permission Toggles",
			Lifespan:    "Постоянные (бизнес-правила)",
			Dynamism:    "Динамические per user/tenant",
			Description: "Управление доступом к премиум-функциям по тарифным планам (B2B SaaS)",
			Example:     "tier_enterprise_audit_log_export: true",
		},
	}
}

func main() {
	fmt.Println("Классификация Feature Toggles по Мартину Фаулеру:")
	for i, cat := range GetFowlerFlagCategories() {
		fmt.Printf("%d. [%s]\\n   Срок жизни:  %s\\n   Динамичность: %s\\n   Назначение:   %s\\n   Пример:       %s\\n\\n",
			i+1, cat.Name, cat.Lifespan, cat.Dynamism, cat.Description, cat.Example)
	}
}
"""
validate_go(ex2_code)

exercises.append({
    "num": 2,
    "title": "Классификация флагов по Мартину Фаулеру",
    "task": "Изучите 4 типа фиче-флагов по классификации Мартина Фаулера (Release, Experiment, Ops, Permission Toggles). Спроектируйте информационную модель FlagCategory с анализом их жизненного цикла (Lifespan), динамичности вычисления (Dynamism) и областей применения в архитектуре.",
    "theory": "Мартин Фаулер выделил 4 фундаментальные категории Feature Toggles:\\n1. Release Toggles (флаги релизов): скрывают разрабатываемый функционал от конечных пользователей. Живут от нескольких дней до пары недель, удаляются сразу после 100% стабильного релиза.\\n2. Experiment Toggles (эксперименты / A/B): делят пользователей на контрольную и экспериментальную группы для замера метрик бизнеса (CTR, GMV). Живут до достижения статистической значимости теста (2-4 недели).\\n3. Ops Toggles (рубильники безопасности / Kill Switches): постоянные флаги, позволяющие дежурным инженерам мгновенно отключить ресурсоемкие некритичные сервисы (рекомендации, расчет персональных скидок) при авариях и пиках распродаж (Черная Пятница).\\n4. Permission Toggles (авторизационные): определяют доступность платных возможностей в зависимости от роли или плана подписки (B2B SaaS Enterprise vs Basic).",
    "step_by_step": "1. Спроектируйте структуру FlagCategory с полями классификации.\\n2. Реализуйте GetFowlerFlagCategories с детальным описанием 4 категорий.\\n3. Проанализируйте различия между временными (Release/Experiment) и постоянными (Ops/Permission) флагами.\\n4. Выведите форматированный отчет.",
    "code_blocks": [{"filename": "fowler_flags.go", "lang": "go", "code": ex2_code}],
    "under_the_hood": "Понимание типа флага определяет архитектуру хранения: Release-флаги можно кэшировать в памяти, Ops-флаги требуют синхронизации за секунды, а Permission-флаги зависят от контекста авторизации пользователя в JWT.",
    "pitfalls": "Смешивание типов флагов: когда временный Release-флаг забывают удалить и начинают использовать его как Permission-флаг, это приводит к путанице в кодовой базе и непреднамеренным утечкам фич.",
    "bigtech_interview": "Почему Ops Toggles (Kill Switches) должны проектироваться как 'отказоустойчивые по умолчанию' (Fail-Safe Defaults) и что должен возвращать флаг при падении сервера флагов?"
})

# Ex 3
ex3_code = """package main

import (
	"fmt"
	"sync"
)

// FlagManager — потокобезопасный менеджер фиче-флагов в оперативной памяти.
type FlagManager struct {
	mu    sync.RWMutex
	flags map[string]bool
}

func NewFlagManager() *FlagManager {
	return &FlagManager{
		flags: make(map[string]bool),
	}
}

// Set устанавливает значение флага.
func (m *FlagManager) Set(name string, enabled bool) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.flags[name] = enabled
}

// IsEnabled проверяет состояние флага (lock-free чтение при RLock).
func (m *FlagManager) IsEnabled(name string) bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.flags[name]
}

func main() {
	mgr := NewFlagManager()
	mgr.Set("new_payment_flow", true)
	mgr.Set("maintenance_mode", false)

	var wg sync.WaitGroup

	// Конкурентное чтение и запись для проверки потокобезопасности
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			if id%3 == 0 {
				mgr.Set("dynamic_promo", id%2 == 0)
			} else {
				_ = mgr.IsEnabled("new_payment_flow")
			}
		}(i)
	}
	wg.Wait()

	fmt.Printf("new_payment_flow: %v\\n", mgr.IsEnabled("new_payment_flow"))
	fmt.Printf("maintenance_mode: %v\\n", mgr.IsEnabled("maintenance_mode"))
	fmt.Println("Потокобезопасный FlagManager успешно протестирован без race conditions.")
}
"""
validate_go(ex3_code)

exercises.append({
    "num": 3,
    "title": "Базовый потокобезопасный менеджер флагов в памяти",
    "task": "Создайте базовый потокобезопасный менеджер флагов FlagManager в памяти на чистом Go. Реализуйте методы Set и IsEnabled с защитой структуры sync.RWMutex и обеспечьте корректную работу в многопоточной среде без data races.",
    "theory": "Самый простой способ реализации фиче-флагов — локальная хэш-таблица в оперативной памяти процесса. Поскольку чтение флагов происходит при каждом входящем HTTP-запросе миллионы раз в секунду, а запись (смена состояния флага) — крайне редко (раз в день или час), идеальным примитивом синхронизации является sync.RWMutex. Вызов RLock() позволяет параллельно читать флаги сотням горутин без взаимной блокировки, в то время как Lock() обеспечивает эксклюзивную запись при обновлении.",
    "step_by_step": "1. Спроектируйте структуру FlagManager с map[string]bool и sync.RWMutex.\\n2. Реализуйте метод Set с блокировкой m.mu.Lock().\\n3. Реализуйте метод IsEnabled с разделяемой блокировкой m.mu.RLock().\\n4. Напишите многопоточный сценарий с одновременным чтением и записью.\\n5. Проверьте отсутствие гонок данных.",
    "code_blocks": [{"filename": "inmemory_flags.go", "lang": "go", "code": ex3_code}],
    "under_the_hood": "При обращении к несуществующему ключу map в Go возвращается нулевое значение типа bool (false), что обеспечивает безопасное поведение по умолчанию.",
    "pitfalls": "Если в многопоточной среде забыть мьютекс и сделать одновременную запись и чтение в стандартную map Go, рантайм вызовет фатальный неперехватываемый крах процесса: fatal error: concurrent map read and map write.",
    "bigtech_interview": "Почему для сверхвысоких нагрузок (100k+ RPS) даже sync.RWMutex может вызывать contention за кэш-линии процессора и как атомарная замена указателя atomic.Pointer[map[string]bool] решает эту проблему?"
})

# Ex 4
ex4_code = """package main

import (
	"fmt"
)

// OpenFeatureConcept описывает основные компоненты открытого стандарта OpenFeature.
type OpenFeatureConcept struct {
	Component   string
	Role        string
	Interface   string
	Description string
}

func GetOpenFeatureConcepts() []OpenFeatureConcept {
	return []OpenFeatureConcept{
		{
			Component:   "Provider (Провайдер)",
			Role:        "Транспорт / Движок оценки",
			Interface:   "FeatureProvider",
			Description: "Реализует адаптер к конкретному бэкенду (Flipt, LaunchDarkly, Redis, In-Memory, Consul)",
		},
		{
			Component:   "Client (Клиент)",
			Role:        "API для разработчика приложения",
			Interface:   "Client",
			Description: "Предоставляет методы: BooleanValue, StringValue, FloatValue, IntValue, ObjectValue",
		},
		{
			Component:   "EvaluationContext",
			Role:        "Контекст таргетинга",
			Interface:   "EvaluationContext",
			Description: "Содержит уникальный targetingKey (userID) и динамические атрибуты пользователя/запроса",
		},
		{
			Component:   "Hooks (Перехватчики)",
			Role:        "Жизненный цикл вычисления",
			Interface:   "Hook (Before, After, Error, Finally)",
			Description: "Обеспечивают сквозной аудит, валидацию и экспорт телеметрии/метрик в Prometheus/OTel",
		},
	}
}

func main() {
	fmt.Println("Архитектурный стандарт OpenFeature (CNCF):")
	for _, c := range GetOpenFeatureConcepts() {
		fmt.Printf("--> [%s] (%s)\\n    Интерфейс: %s\\n    Описание:  %s\\n\\n",
			c.Component, c.Role, c.Interface, c.Description)
	}
	fmt.Println("OpenFeature исключает vendor-lock-in: провайдер флагов меняется в 1 строчке кода!")
}
"""
validate_go(ex4_code)

exercises.append({
    "num": 4,
    "title": "Открытый стандарт OpenFeature и экосистема Go SDK",
    "task": "Изучите открытый отраслевой стандарт OpenFeature (проект CNCF Incubating). Спроектируйте архитектурную модель четырех фундаментальных концепций стандарта: Provider, Client, EvaluationContext и Hook, объяснив, как стандарт устраняет привязку к поставщику (Vendor Lock-in).",
    "theory": "Исторически каждый вендор систем управления флагами (LaunchDarkly, Split, Unleash, Flagsmith) создавал собственный проприетарный SDK. Это приводило к сильнейшему vendor lock-in: при переходе на собственный open-source движок (например, Flipt) приходилось переписывать тысячи вызовов во всех микросервисах компании. OpenFeature (стандарт CNCF) унифицировал эту область, подобно тому как OpenTelemetry унифицировал трассировку и метрики:\\n1. Provider: адаптер к конкретному источнику данных (Flipt, Redis, JSON file). Меняется один раз при старте main().\\n2. Client: единый интерфейс вычисления флагов (BooleanValue, StringValue и т.д.), который используют разработчики микросервисов.\\n3. EvaluationContext: контекст пользователя (targetingKey, регион, версия ОС) для вычисления персонализированных правил.\\n4. Hooks: механизм внедрения сквозной логики (логирование, Prometheus метрики).",
    "step_by_step": "1. Спроектируйте структуру OpenFeatureConcept.\\n2. Опишите роли Provider, Client, EvaluationContext и Hooks.\\n3. Проанализируйте преимущества стандартизации для Enterprise-архитектуры.\\n4. Выведите сводный инженерный обзор стандарта.",
    "code_blocks": [{"filename": "openfeature_spec.go", "lang": "go", "code": ex4_code}],
    "under_the_hood": "Благодаря OpenFeature бизнес-код микросервиса зависит только от абстрактного интерфейса, а конкретный поставщик (SaaS или локальный Redis) подключается как плагин в функции инициализации.",
    "pitfalls": "Не передавайте чувствительные данные (пароли, номера кредитных карт) в EvaluationContext: провайдеры могут пересылать эти атрибуты на внешние серверы аудита.",
    "bigtech_interview": "Почему OpenFeature и OpenTelemetry стали ключевыми стандартами CNCF для Cloud-Native платформ? Как абстракция провайдера защищает корпоративную платформу от ценовых изменений коммерческих SaaS вендоров?"
})

# Ex 5
ex5_code = """package main

import (
	"context"
	"fmt"
)

// MockEvaluationContext эмулирует контекст пользователя в OpenFeature.
type MockEvaluationContext struct {
	TargetingKey string
	Attributes   map[string]interface{}
}

// MockOpenFeatureClient эмулирует официальный OpenFeature Go SDK.
type MockOpenFeatureClient struct {
	inMemoryFlags map[string]bool
}

func NewMockOpenFeatureClient() *MockOpenFeatureClient {
	return &MockOpenFeatureClient{
		inMemoryFlags: map[string]bool{
			"new_checkout_flow": true,
			"ai_summary_banner": false,
		},
	}
}

func (c *MockOpenFeatureClient) BooleanValue(
	ctx context.Context,
	flagKey string,
	defaultValue bool,
	evalCtx MockEvaluationContext,
) (bool, error) {
	val, ok := c.inMemoryFlags[flagKey]
	if !ok {
		// При отсутствии флага возвращается безопасное дефолтное значение
		return defaultValue, nil
	}
	return val, nil
}

func main() {
	ctx := context.Background()
	client := NewMockOpenFeatureClient()

	userCtx := MockEvaluationContext{
		TargetingKey: "user_10928",
		Attributes: map[string]interface{}{
			"country": "RU",
			"group":   "beta-testers",
		},
	}

	// Вычисление булевого флага
	isNewCheckout, err := client.BooleanValue(ctx, "new_checkout_flow", false, userCtx)
	if err != nil {
		panic(err)
	}

	isBannerEnabled, _ := client.BooleanValue(ctx, "ai_summary_banner", false, userCtx)
	isUnknown, _ := client.BooleanValue(ctx, "non_existent_flag", true, userCtx)

	fmt.Printf("new_checkout_flow: %v\\n", isNewCheckout)
	fmt.Printf("ai_summary_banner: %v\\n", isBannerEnabled)
	fmt.Printf("non_existent_flag (fallback to default): %v\\n", isUnknown)
}
"""
validate_go(ex5_code)

exercises.append({
    "num": 5,
    "title": "Подключение официального Go SDK open-feature/go-sdk",
    "task": "Изучите сигнатуру и поведение официального OpenFeature Go SDK. Реализуйте модель клиента MockOpenFeatureClient с поддержкой метода BooleanValue(ctx, flagKey, defaultValue, evalCtx) и гарантированным возвратом безопасного defaultValue при отсутствии флага.",
    "theory": "В официальном OpenFeature Go SDK (github.com/open-feature/go-sdk) вычисление значений флагов строго типизировано. Существуют методы: BooleanValue, StringValue, FloatValue, IntValue, ObjectValue. Сигнатура:\\nclient.BooleanValue(ctx context.Context, flag string, defaultValue bool, evalCtx EvaluationContext) (bool, error)\\nКлючевой контракт надежности: если флаг не найден, бэкенд провайдера недоступен или произошла ошибка валидации, метод ОБЯЗАН вернуть defaultValue. Благодаря этому при любых авариях внешней инфраструктуры флагов бизнес-логика приложения не падает, а продолжает работать в безопасном штатном режиме.",
    "step_by_step": "1. Спроектируйте структуру MockEvaluationContext с TargetingKey и картой атрибутов.\\n2. Реализуйте MockOpenFeatureClient с методом BooleanValue.\\n3. Обеспечьте возврат defaultValue при отсутствии ключа.\\n4. Проверьте вычисление существующих и неизвестных флагов.",
    "code_blocks": [{"filename": "openfeature_sdk.go", "lang": "go", "code": ex5_code}],
    "under_the_hood": "OpenFeature также поддерживает детальную оценку через BooleanValueDetails: возвращается не просто bool, но и причина выбора (Reason: TARGETING_MATCH, DEFAULT, CACHED) и вариант (Variant).",
    "pitfalls": "Передача defaultValue = true для рискованных экспериментальных фич: значение по умолчанию всегда должно соответствовать самому надежному и проверенному поведению системы (Fail-Safe).",
    "bigtech_interview": "Почему сигнатура вычисления фиче-флага всегда требует явной передачи defaultValue? Как это соотносится с паттерном Graceful Degradation?"
})

# Ex 6
ex6_code = """package main

import (
	"fmt"
	"strings"
)

// TargetEvaluationContext описывает параметры текущего запроса/пользователя.
type TargetEvaluationContext struct {
	UserID    string
	UserGroup string
	Country   string
	AppVersion string
}

// EvaluateBetaTargeting вычисляет доступность фичи на основе атрибутов контекста.
func EvaluateBetaTargeting(flagKey string, ctx TargetEvaluationContext) (bool, string) {
	if flagKey != "redesign_v2" {
		return false, "FLAG_NOT_FOUND"
	}

	// Правило: включено, если пользователь в группе beta-testers ИЛИ страна RU
	if strings.EqualFold(ctx.UserGroup, "beta-testers") {
		return true, "TARGETING_MATCH_GROUP"
	}

	if strings.EqualFold(ctx.Country, "RU") {
		return true, "TARGETING_MATCH_COUNTRY"
	}

	return false, "DEFAULT_FALLTHROUGH"
}

func main() {
	users := []TargetEvaluationContext{
		{UserID: "usr_1", UserGroup: "beta-testers", Country: "DE", AppVersion: "3.1.0"},
		{UserID: "usr_2", UserGroup: "standard", Country: "RU", AppVersion: "2.0.0"},
		{UserID: "usr_3", UserGroup: "standard", Country: "US", AppVersion: "3.1.0"},
	}

	fmt.Println("Оценка таргетинга флага redesign_v2:")
	for _, u := range users {
		enabled, reason := EvaluateBetaTargeting("redesign_v2", u)
		fmt.Printf("User: %s (Group=%s, Country=%s) -> Включен: %-5v (Причина: %s)\\n",
			u.UserID, u.UserGroup, u.Country, enabled, reason)
	}
}
"""
validate_go(ex6_code)

exercises.append({
    "num": 6,
    "title": "Контекст вычисления (Evaluation Context) и таргетинг",
    "task": "Реализуйте контекст вычисления TargetEvaluationContext и логику таргетинга. Напишите функцию EvaluateBetaTargeting, которая включает флаг redesign_v2, если пользователь входит в группу 'beta-testers' ИЛИ находится в стране 'RU', с возвратом причины срабатывания (Reason).",
    "theory": "Статические флаги (on/off для всех) редко применяются для сложных фич. В реальности требуется контекстный таргетинг (Contextual Targeting): показ функционала конкретной когорте пользователей. Evaluation Context передает параметры запроса в движок правил. Стандартные атрибуты контекста:\\n- TargetingKey: уникальный идентификатор субъекта (ID пользователя, ID организации, Device ID).\\n- Атрибуты окружения: страна (GeoIP), версия мобильного клиента, платформа (iOS/Android/Web), роль сотрудника (is_internal_employee).\\nДвижок сопоставляет контекст с правилами: UserGroup == 'beta-testers' OR Country == 'RU'. Возврат причины (Reason) критичен для отладки: инженер видит, почему конкретный пользователь получил тот или иной вариант.",
    "step_by_step": "1. Спроектируйте структуру TargetEvaluationContext с полями UserID, UserGroup, Country, AppVersion.\\n2. Реализуйте функцию EvaluateBetaTargeting с проверкой логических условий.\\n3. Верните флаг и строковую причину (Reason).\\n4. Протестируйте поведение на разных профилях пользователей.",
    "code_blocks": [{"filename": "targeting_context.go", "lang": "go", "code": ex6_code}],
    "under_the_hood": "EvaluationContext создается на уровне HTTP/gRPC middleware для каждого запроса и оборачивается в context.Context, делая атрибуты доступными на всех слоях бизнес-логики без явного проброса через параметры функций.",
    "pitfalls": "Регистрозависимость строковых проверок: пользователь может прислать country: 'ru' или 'RU'. Всегда используйте strings.EqualFold для нормализации строковых атрибутов.",
    "bigtech_interview": "Как в распределенных B2B системах организуют иерархический контекст таргетинга (Global Context -> Tenant Context -> User Context)?"
})

# Ex 7
ex7_code = """package main

import (
	"fmt"
	"hash/crc32"
)

// PercentageRolloutEvaluator выполняет детерминированное процентное включение функционала.
type PercentageRolloutEvaluator struct {
	Percentage uint32 // от 0 до 100
}

func NewPercentageRollout(percentage uint32) *PercentageRolloutEvaluator {
	if percentage > 100 {
		percentage = 100
	}
	return &PercentageRolloutEvaluator{Percentage: percentage}
}

// IsEnabledForUser вычисляет стабильное попадание пользователя в процентную когорту.
func (r *PercentageRolloutEvaluator) IsEnabledForUser(flagName, userID string) (bool, uint32) {
	if r.Percentage == 0 {
		return false, 0
	}
	if r.Percentage == 100 {
		return true, 100
	}

	// Составляем уникальную соль: флаг + пользователь
	key := fmt.Sprintf("%s:%s", flagName, userID)

	// Вычисляем контрольную сумму CRC32 IEEE
	hashVal := crc32.ChecksumIEEE([]byte(key))

	// Получаем бакет от 0 до 99
	bucket := hashVal % 100

	return bucket < r.Percentage, bucket
}

func main() {
	// Раскатка на 20% аудитории
	rollout := NewPercentageRollout(20)
	flag := "new_search_engine"

	fmt.Printf("Тестирование 20%% процентной раскатки для флага %s:\\n", flag)
	users := []string{"alice", "bob", "charlie", "dave", "eve", "frank", "grace"}

	for _, user := range users {
		enabled1, bucket1 := rollout.IsEnabledForUser(flag, user)
		// Проверяем детерминированность повторным вызовом
		enabled2, bucket2 := rollout.IsEnabledForUser(flag, user)

		if enabled1 != enabled2 || bucket1 != bucket2 {
			panic("Нарушение детерминизма хэширования!")
		}

		fmt.Printf("Пользователь: %-8s -> Бакет: %2d/100 -> Включено: %v\\n", user, bucket1, enabled1)
	}
}
"""
validate_go(ex7_code)

exercises.append({
    "num": 7,
    "title": "Процентные раскатки (Percentage Rollouts) и детерминированное хэширование",
    "task": "Реализуйте алгоритм плавной процентной раскатки (Percentage Rollout) на базе хэширования CRC32 IEEE: hash(flagName + \":\" + userID) % 100. Докажите математическую детерминированность: конкретный пользователь всегда попадает в один и тот же бакет при неизменном проценте раскатки.",
    "theory": "При релизе нового сервиса на миллионную аудиторию включение сразу на 100% смертельно опасно. Применяется постепенная процентная раскатка (Canary Rollout): 1% -> 5% -> 25% -> 50% -> 100%. Ключевые требования:\\n1. Детерминированность (Sticky Evaluation): если пользователь зашел на сайт утром и попал в 5% участников, при обновлении страницы вечером он обязан остаться в этой группе. Никаких случайных rand.Float64()!\\n2. Независимость флагов: попадание пользователя в 10% для флага А не должно означать автоматическое попадание в 10% для флага Б. Для этого к ключу хэширования подмешивается имя флага: flagName + ':' + userID.\\n3. Алгоритм: вычисляется 32-битный хэш (CRC32, MurmurHash3, SHA256), берется остаток от деления на 100. Если bucket < targetPercentage — фича активна.",
    "step_by_step": "1. Спроектируйте PercentageRolloutEvaluator с полем Percentage.\\n2. Сформируйте ключ с солью: flagName + \":\" + userID.\\n3. Вычислите crc32.ChecksumIEEE и возьмите остаток % 100.\\n4. Сравните полученный бакет с пороговым процентом.\\n5. Докажите идентичность результатов при повторных вычислениях.",
    "code_blocks": [{"filename": "percentage_rollout.go", "lang": "go", "code": ex7_code}],
    "under_the_hood": "CRC32 вычисляется процессором аппаратно за 1–2 такта с использованием инструкций SSE4.2 (CRC32), обеспечивая скорость вычисления свыше 50 миллионов оценок в секунду на одном ядре CPU.",
    "pitfalls": "Хэширование только по userID (без имени флага): приведет к тому, что одни и те же пользователи будут подопытными кроликами во всех тестах компании, а другие никогда не увидят новых фич.",
    "bigtech_interview": "Почему алгоритм консистентного хэширования в процентных раскатках гарантирует монотонность (Monotonicity): при увеличении процента с 10% до 20% ни один пользователь из первых 10% не потеряет доступ к фиче?"
})

# Ex 8
ex8_code = """package main

import (
	"fmt"
)

// SegmentCondition описывает критерии принадлежности пользователя к сегменту.
type SegmentCondition struct {
	MinSpendCents int64
	IsVIP         bool
	Platform      string
}

// UserProfile хранит характеристики клиента.
type UserProfile struct {
	ID            string
	SpendCents    int64
	VIPStatus     bool
	DeviceOS      string
}

// SegmentEngine проверяет соответствие пользователя сегментам.
type SegmentEngine struct{}

func (e *SegmentEngine) IsInSegment(user UserProfile, segment string) bool {
	switch segment {
	case "high_value_customers":
		return user.SpendCents >= 1000000 || user.VIPStatus // 10 000 руб или VIP
	case "mobile_ios_users":
		return user.DeviceOS == "iOS"
	default:
		return false
	}
}

func main() {
	engine := &SegmentEngine{}

	users := []UserProfile{
		{ID: "usr_alice", SpendCents: 1500000, VIPStatus: false, DeviceOS: "Android"},
		{ID: "usr_bob", SpendCents: 20000, VIPStatus: false, DeviceOS: "iOS"},
		{ID: "usr_charlie", SpendCents: 5000, VIPStatus: true, DeviceOS: "Web"},
	}

	for _, u := range users {
		isHighValue := engine.IsInSegment(u, "high_value_customers")
		isIOS := engine.IsInSegment(u, "mobile_ios_users")
		fmt.Printf("User: %-12s -> HighValue: %-5v, iOS: %-5v\\n", u.ID, isHighValue, isIOS)
	}
}
"""
validate_go(ex8_code)

exercises.append({
    "num": 8,
    "title": "Сегментация пользователей (User Segmentation)",
    "task": "Спроектируйте движок сегментации пользователей SegmentEngine. Реализуйте проверку принадлежности профиля UserProfile к сегментам 'high_value_customers' (сумма покупок >= 10 000 руб или статус VIP) и 'mobile_ios_users'.",
    "theory": "Сегментация пользователей (User Segmentation) позволяет таргетировать фичи на определенные группы клиентов без ручного перечисления тысяч идентификаторов. Сегмент — это динамическое именованное правило. Вместо того чтобы настраивать условия в каждом флаге заново, флаг привязывается к сегменту: 'Enable feature X for segment high_value_customers'. Сегменты могут быть статическими (список VIP-пользователей) или динамическими (на основе вычисляемых атрибутов: сумма трат за 30 дней, геолокация, тип устройства).",
    "step_by_step": "1. Спроектируйте структуру UserProfile с параметрами клиента.\\n2. Создайте структуру SegmentEngine с методом IsInSegment.\\n3. Реализуйте логику проверки пороговых условий для сегментов.\\n4. Протестируйте сопоставление различных профилей клиентов.",
    "code_blocks": [{"filename": "user_segmentation.go", "lang": "go", "code": ex8_code}],
    "under_the_hood": "В крупных e-commerce системах расчет тяжелых сегментов (RFM-анализ, LTV) выполняется аналитическими пайплайнами в ClickHouse/Spark раз в сутки, а агрегированные метрики кэшируются в профиле пользователя в Redis.",
    "pitfalls": "Сложные вычисления сегментов внутри горячего сетевого пути HTTP-запроса могут замедлить работу шлюза. Используйте только предварительно вычисленные атрибуты пользователя.",
    "bigtech_interview": "Как организовать передачу динамических сегментов пользователя через JWT-токены без раздувания размера HTTP-заголовков?"
})

# Ex 9
ex9_code = """package main

import (
	"fmt"
	"strconv"
	"strings"
)

// CompareSemVer сравнивает две семантические версии вида "major.minor.patch".
// Возвращает 1 если v1 > v2, -1 если v1 < v2, 0 если равны.
func CompareSemVer(v1, v2 string) int {
	parts1 := strings.Split(v1, ".")
	parts2 := strings.Split(v2, ".")

	for i := 0; i < 3; i++ {
		var n1, n2 int
		if i < len(parts1) {
			n1, _ = strconv.Atoi(parts1[i])
		}
		if i < len(parts2) {
			n2, _ = strconv.Atoi(parts2[i])
		}

		if n1 > n2 {
			return 1
		}
		if n1 < n2 {
			return -1
		}
	}
	return 0
}

// RuleEvaluator проверяет сложные логические условия над версиями и списками.
type RuleEvaluator struct{}

func (e *RuleEvaluator) IsAppVersionSupported(clientVer, minRequiredVer string) bool {
	return CompareSemVer(clientVer, minRequiredVer) >= 0
}

func (e *RuleEvaluator) IsCountryInList(country string, allowedCountries []string) bool {
	for _, c := range allowedCountries {
		if strings.EqualFold(country, c) {
			return true
		}
	}
	return false
}

func main() {
	eval := &RuleEvaluator{}

	clientVer := "2.4.1"
	minVer := "2.4.0"
	fmt.Printf("Проверка версии: %s >= %s -> %v\\n", clientVer, minVer, eval.IsAppVersionSupported(clientVer, minVer))

	clientCountry := "KZ"
	allowed := []string{"RU", "BY", "KZ"}
	fmt.Printf("Проверка страны: %s IN %v -> %v\\n", clientCountry, allowed, eval.IsCountryInList(clientCountry, allowed))
}
"""
validate_go(ex9_code)

exercises.append({
    "num": 9,
    "title": "Сложные логические правила таргетинга (Rule Engine)",
    "task": "Разработайте интерпретатор правил таргетинга RuleEvaluator. Реализуйте функцию семантического сравнения версий CompareSemVer (SemVer: major.minor.patch) для условия version >= minVersion и проверку вхождения страны в список разрешенных значений (оператор IN).",
    "theory": "Продвинутые системы управления флагами поддерживают декларативный язык правил (Domain-Specific Language или JSON Rules):\\n1. Операторы сравнения чисел и версий: >, <, >=, <=, ==. Обычное лексикографическое сравнение строк для версий некорректно ('2.10.0' лексикографически меньше '2.4.0', хотя 2.10 новее!). Требуется разбор компонентов SemVer (Major, Minor, Patch).\\n2. Операторы множеств: IN, NOT IN. Проверка вхождения атрибута в список разрешенных регионов, тенантов или групп.\\n3. Логические связки: композиция условий через AND, OR, NOT. Это позволяет формулировать правила вида: 'Включить биометрию для iOS с версией >= 4.5.0 И находящихся в РФ'.",
    "step_by_step": "1. Реализуйте алгоритм CompareSemVer с разбиением по точкам и покомпонентным сравнением чисел.\\n2. Создайте структуру RuleEvaluator с методами проверки версий и списков.\\n3. Протестируйте сравнение версий 2.4.1 и 2.4.0.\\n4. Протестируйте проверку вхождения страны в белый список.",
    "code_blocks": [{"filename": "rule_engine.go", "lang": "go", "code": ex9_code}],
    "under_the_hood": "В продакшене для описания таких правил используют CEL (Common Expression Language от Google), компилирующий правила в байткод для субмикросекундного исполнения в Go.",
    "pitfalls": "Ошибки парсинга префиксов версий (например, 'v2.4.0' с ведущей 'v'). Обязательно вызывайте strings.TrimPrefix(v, 'v') перед парсингом цифр.",
    "bigtech_interview": "Почему для мобильных клиентов критически важен таргетинг по версиям приложения (App Version Targeting) при раскатке новых API эндпоинтов бэкенда?"
})

# Ex 10
ex10_code = """package main

import (
	"fmt"
	"sync/atomic"
	"time"
)

// EmergencyKillSwitch предоставляет операционный рубильник безопасности (Ops Toggle).
type EmergencyKillSwitch struct {
	isKilled atomic.Bool
}

func NewEmergencyKillSwitch() *EmergencyKillSwitch {
	return &EmergencyKillSwitch{}
}

func (s *EmergencyKillSwitch) Trip() {
	s.isKilled.Store(true)
	fmt.Println("--> [ALARM]: Аварийный рубильник СРАБОТАЛ! Тяжелая подсистема отключена.")
}

func (s *EmergencyKillSwitch) Restore() {
	s.isKilled.Store(false)
	fmt.Println("--> [RESTORE]: Работа подсистемы восстановлена.")
}

func (s *EmergencyKillSwitch) IsActive() bool {
	return s.isKilled.Load()
}

// RecommendationService эмулирует сервис с защитой через Kill Switch.
type RecommendationService struct {
	killSwitch *EmergencyKillSwitch
}

func (r *RecommendationService) GetRecommendations(userID string) []string {
	// Если аварийный рубильник включен — мгновенно отдаем статическую заглушку (0% нагрузки на ML кластер)
	if r.killSwitch.IsActive() {
		return []string{"Популярные товары (заглушка)", "Новинки сезона (заглушка)"}
	}

	// Имитация тяжелого запроса к ML модели
	return []string{
		fmt.Sprintf("Персональная рекомендация 1 для %s", userID),
		fmt.Sprintf("Персональная рекомендация 2 для %s", userID),
	}
}

func main() {
	sw := NewEmergencyKillSwitch()
	svc := &RecommendationService{killSwitch: sw}

	// 1. Штатный режим работы
	fmt.Println("Штатный режим:", svc.GetRecommendations("user_101"))

	// 2. Дежурный инженер активирует аварийный рубильник (DDoS или отказ ML кластера)
	sw.Trip()

	// 3. Быстрый ответ без вызова ML
	fmt.Println("Аварийный режим:", svc.GetRecommendations("user_101"))
}
"""
validate_go(ex10_code)

exercises.append({
    "num": 10,
    "title": "Аварийные рубильники (Kill Switches) для высоконагруженных систем",
    "task": "Реализуйте операционный аварийный рубильник EmergencyKillSwitch на базе atomic.Bool. Смоделируйте сценарий перегрузки сервиса рекомендаций RecommendationService, когда срабатывание рубильника мгновенно переводит сервис на отдачу статической заглушки с нулевой нагрузкой на тяжелые внешние бэкенды.",
    "theory": "Аварийный рубильник (Kill Switch / Ops Toggle) — критический элемент архитектуры устойчивости (SRE Resilience). Когда в дни пиковых распродаж (Black Friday, 11.11) трафик возрастает в 10 раз, или когда сторонний провайдер ML-рекомендаций начинает отвечать с задержкой 5 секунд, сервис рискует упасть целиком. Дежурный SRE активирует Kill Switch. Сервис рекомендаций перестает обращаться к ML-кластеру и мгновенно возвращает статический закешированный список популярных товаров. Время ответа падает с 5000 мс до 0.1 мс, нагрузка на базы снижается, а пользователи продолжают совершать покупки.",
    "step_by_step": "1. Спроектируйте EmergencyKillSwitch со счетчиком atomic.Bool.\\n2. Реализуйте методы Trip, Restore и IsActive.\\n3. Внедрите проверку рубильника в RecommendationService.\\n4. Смоделируйте переключение между тяжелыми вызовами и статической заглушкой.",
    "code_blocks": [{"filename": "kill_switch.go", "lang": "go", "code": ex10_code}],
    "under_the_hood": "Чтение atomic.Bool.Load() компилируется в одну инструкцию процессора MOV без барьеров памяти на x86, занимая менее 1 наносекунды на вызов.",
    "pitfalls": "Рубильник должен управляться через независимый канал: если панель управления флагами находится за тем же упавшим API Gateway, дежурный инженер физически не сможет нажать кнопку выключения.",
    "bigtech_interview": "Как в Netflix и Ozon используют градацию уровней деградации (Graceful Degradation Levels: Level 1 - отключить рекомендации, Level 2 - отключить отзывы, Level 3 - только оформление заказа) при авариях?"
})

# Ex 11
ex11_code = """package main

import (
	"context"
	"fmt"
)

// FliptFlagResult описывает ответ от сервера Flipt.
type FliptFlagResult struct {
	Key     string
	Enabled bool
	Variant string
	Reason  string
}

// MockFliptGRPCClient эмулирует клиент к открытому серверу управления флагами Flipt.
type MockFliptGRPCClient struct {
	serverEndpoint string
}

func NewMockFliptGRPCClient(endpoint string) *MockFliptGRPCClient {
	return &MockFliptGRPCClient{serverEndpoint: endpoint}
}

func (c *MockFliptGRPCClient) Evaluate(ctx context.Context, flagKey, entityID string) (FliptFlagResult, error) {
	// В реальном приложении здесь RPC вызов к flipt.NewEvaluationServiceClient(conn)
	if flagKey == "enable_crypto_payments" {
		return FliptFlagResult{
			Key:     flagKey,
			Enabled: true,
			Variant: "bitcoin_lightning",
			Reason:  "MATCH_EVALUATION",
		}, nil
	}
	return FliptFlagResult{Key: flagKey, Enabled: false, Reason: "FLAG_NOT_FOUND"}, nil
}

func main() {
	ctx := context.Background()
	client := NewMockFliptGRPCClient("localhost:9000")

	res, err := client.Evaluate(ctx, "enable_crypto_payments", "user_554")
	if err != nil {
		panic(err)
	}

	fmt.Printf("Ответ Flipt Evaluation Server:\\nФлаг: %s, Включен: %v, Вариант: %s (Причина: %s)\\n",
		res.Key, res.Enabled, res.Variant, res.Reason)
	fmt.Println("Flipt предоставляет веб-интерфейс, GitOps-синхронизацию и аудит изменений из коробки.")
}
"""
validate_go(ex11_code)

exercises.append({
    "num": 11,
    "title": "Интеграция с открытыми серверами управления флагами (Flipt)",
    "task": "Изучите архитектуру открытого сервера управления фиче-флагами Flipt (написанного на Go). Смоделируйте gRPC-клиент MockFliptGRPCClient для вычисления флагов и вариантов (Variants) и разберите преимущества self-hosted решений перед коммерческими SaaS.",
    "theory": "Flipt (flipt.io) — ведущий открытый сервер управления флагами, написанный на Go. Ключевые преимущества для Enterprise:\\n1. Self-hosted: данные о пользователях и флагах не покидают защищенный периметр компании (соответствие 152-ФЗ / GDPR).\\n2. Высокая скорость: поддержка gRPC и REST API, хранение правил в PostgreSQL / SQLite / Redis.\\n3. GitOps совместимость: правила флагов могут храниться в репозитории Git в виде YAML-манифестов и синхронизироваться через CI/CD.\\n4. Официальный провайдер OpenFeature: библиотека flipt-openfeature-provider-go подключается к OpenFeature в одну строчку кода.",
    "step_by_step": "1. Спроектируйте структуру FliptFlagResult с полями Key, Enabled, Variant, Reason.\\n2. Реализуйте MockFliptGRPCClient с методом Evaluate.\\n3. Смоделируйте оценку таргетинга с возвратом варианта bitcoin_lightning.\\n4. Протестируйте вызов метода с контекстом.",
    "code_blocks": [{"filename": "flipt_client.go", "lang": "go", "code": ex11_code}],
    "under_the_hood": "Для минимизации задержек клиент Flipt поддерживает режим локальной синхронизации (Local Evaluation / Offline Sync): клиент выкачивает снимок всех правил в память процесса и оценивает флаги локально за 100 наносекунд без RPC-вызовов по сети.",
    "pitfalls": "Постоянные сетевые вызовы к удаленному Flipt на каждый HTTP-запрос создают точку отказа и добавляют 2–5 мс сетевой задержки. Всегда используйте клиентский кэш или Local Evaluation.",
    "bigtech_interview": "В чем разница между Client-Side Evaluation (оценка правил на стороне микросервиса) и Server-Side Evaluation (оценка на сервере флагов)? Почему для высоконагруженного бэкенда выбирают Client-Side?"
})

# Ex 12
ex12_code = """package main

import (
	"fmt"
	"sync"
)

// L1CacheFlags хранит локальную копию флагов в памяти процесса.
type L1CacheFlags struct {
	mu    sync.RWMutex
	cache map[string]bool
}

func NewL1CacheFlags() *L1CacheFlags {
	return &L1CacheFlags{cache: make(map[string]bool)}
}

func (c *L1CacheFlags) Get(key string) bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.cache[key]
}

func (c *L1CacheFlags) Update(key string, val bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.cache[key] = val
}

// RedisPubSubSimulator эмулирует распределенную рассылку изменений флагов через шину Pub/Sub.
type RedisPubSubSimulator struct {
	subscribers []*L1CacheFlags
}

func (ps *RedisPubSubSimulator) Subscribe(cache *L1CacheFlags) {
	ps.subscribers = append(ps.subscribers, cache)
}

func (ps *RedisPubSubSimulator) PublishUpdate(key string, val bool) {
	fmt.Printf("--> [Redis Pub/Sub]: Опубликовано обновление флага %s = %v\\n", key, val)
	for _, sub := range ps.subscribers {
		sub.Update(key, val)
	}
}

func main() {
	bus := &RedisPubSubSimulator{}

	// Имитация 3 подов микросервиса в Kubernetes, каждый со своим L1 кэшем в памяти
	pod1 := NewL1CacheFlags()
	pod2 := NewL1CacheFlags()
	pod3 := NewL1CacheFlags()

	bus.Subscribe(pod1)
	bus.Subscribe(pod2)
	bus.Subscribe(pod3)

	// Администратор изменил флаг
	bus.PublishUpdate("promo_black_friday", true)

	fmt.Printf("Значение в Pod 1: %v\\n", pod1.Get("promo_black_friday"))
	fmt.Printf("Значение в Pod 2: %v\\n", pod2.Get("promo_black_friday"))
	fmt.Printf("Значение в Pod 3: %v\\n", pod3.Get("promo_black_friday"))
}
"""
validate_go(ex12_code)

exercises.append({
    "num": 12,
    "title": "Хранение и распространение флагов через Redis Pub/Sub",
    "task": "Реализуйте двухуровневую архитектуру распространения флагов с локальным кэшем L1 в памяти процесса и шиной инвалидации Redis Pub/Sub. Обеспечьте мгновенную (менее 10 мс) синхронизацию изменений между всеми подами кластера без периодического опроса (polling).",
    "theory": "Архитектурная дилемма управления флагами: чтение флага должно занимать единицы наносекунд (из локальной памяти процесса Go), но обновление должно мгновенно распространяться на сотни реплик сервиса в Kubernetes. Решение — паттерн Cache Invalidation via Pub/Sub:\\n1. Каждый под хранит копию всех активных флагов в локальной map с sync.RWMutex (L1 Cache).\\n2. При изменении флага в панели управления бэкенд записывает новое значение в Redis и публикует событие в канал Pub/Sub: PUBLISH flags:updates '{\"key\":\"feature_x\",\"val\":true}'.\\n3. Все поды слушают канал в фоновой горутине. При получении сообщения под обновляет свою локальную память.\\nВ результате чтение происходит с нулевой задержкой из оперативной памяти, а консистентность достигается за время прохождения сетевого пакета (< 5 мс).",
    "step_by_step": "1. Спроектируйте L1CacheFlags с потокобезопасной хэш-таблицей.\\n2. Создайте модель брокера RedisPubSubSimulator.\\n3. Реализуйте методы Subscribe и PublishUpdate.\\n4. Протестируйте синхронное обновление состояния во всех подписчиках.",
    "code_blocks": [{"filename": "pubsub_flags.go", "lang": "go", "code": ex12_code}],
    "under_the_hood": "Redis Pub/Sub не гарантирует доставку при обрыве соединения (at-most-once delivery). Для надежности при реконнекте сокета под должен выполнить полную вычитку всех ключей (Snapshot Sync) через HGETALL flags:active.",
    "pitfalls": "Если под завис во время сборки мусора (Stop-The-World пауза GC), буфер сокета Pub/Sub в ядре может переполниться, вызвав сброс соединения клиентом Redis.",
    "bigtech_interview": "Почему для синхронизации фиче-флагов между микросервисами предпочитают Pub/Sub в Redis или NATS вместо периодического опроса базы данных раз в секунду?"
})

# Ex 13
ex13_code = """package main

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
)

// CanaryRouter управляет выбором бэкенда на основе фиче-флага.
type CanaryRouter struct {
	isCanaryActive func(ctx context.Context, userID string) bool
}

func (r *CanaryRouter) RouteRequest(ctx context.Context, userID string) string {
	if r.isCanaryActive(ctx, userID) {
		return "http://backend-v2-canary.internal:8080"
	}
	return "http://backend-v1-stable.internal:8080"
}

func main() {
	// Флаг активен только для пользователей с четным ID
	router := &CanaryRouter{
		isCanaryActive: func(ctx context.Context, userID string) bool {
			return userID == "user_200" || userID == "user_400"
		},
	}

	ctx := context.Background()
	users := []string{"user_100", "user_200", "user_300", "user_400"}

	fmt.Println("Маршрутизация трафика между v1 и v2 по фиче-флагу:")
	for _, u := range users {
		target := router.RouteRequest(ctx, u)
		fmt.Printf("Запрос от %s -> Направлен на: %s\\n", u, target)
	}
}
"""
validate_go(ex13_code)

exercises.append({
    "num": 13,
    "title": "Канареечные релизы (Canary Releases) с канареечной маршрутизацией",
    "task": "Спроектируйте архитектуру канареечной маршрутизации CanaryRouter на базе фиче-флагов. Напишите метод RouteRequest, динамически выбирающий целевой кластер (v1 Stable vs v2 Canary) на основе оценки флага пользователя.",
    "theory": "Традиционная канареечная раскатка в Kubernetes (Canary Deployment через Service) делит трафик на L4 уровне случайным образом (например, 9 подов v1 и 1 под v2 = 10% трафика). Недостаток: один и тот же пользователь при кликах по сайту постоянно переключается между старой и новой версией, получая разорванный пользовательский опыт. Канареечная маршрутизация на базе фиче-флагов (L7 Canary Routing) обеспечивает интеллектуальное деление: флаг вычисляется по UserID. Если пользователь попал в когорту Canary, ВСЕ его последующие запросы строго направляются на v2 кластер. Если обнаружен баг, флаг выключается мгновенно для конкретного пользователя или сегмента.",
    "step_by_step": "1. Спроектируйте CanaryRouter с функцией оценки флага isCanaryActive.\\n2. Реализуйте метод RouteRequest с возвратом адреса бэкенда v1 или v2.\\n3. Протестируйте стабильность маршрутизации для набора пользователей.",
    "code_blocks": [{"filename": "canary_routing.go", "lang": "go", "code": ex13_code}],
    "under_the_hood": "Шлюз вычисляет флаг и устанавливает внутренний HTTP-заголовок (например, X-Upstream-Version: v2). Kubernetes Ingress (Ingress-Nginx canary-by-header) или Envoy перенаправляет запрос на соответствующий Service.",
    "pitfalls": "Несоответствие контрактов баз данных: если версия v2 выполнила ломающую миграцию структуры БД, пользователи на версии v1 получат ошибки. Всегда используйте паттерн Expand/Contract для схем данных.",
    "bigtech_interview": "В чем преимущества Canary Routing на уровне приложения по сравнению со случайной балансировкой подов на уровне Kubernetes Service?"
})

# Ex 14
ex14_code = """package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
)

// CanaryMiddleware инжектирует заголовок X-Upstream-Service на основе фиче-флага.
func CanaryMiddleware(isCanaryUser func(userID string) bool, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		userID := r.Header.Get("X-User-ID")

		targetService := "orders-service-v1"
		if userID != "" && isCanaryUser(userID) {
			targetService = "orders-service-v2-canary"
		}

		// Инжектируем заголовок для downstream-прокси или Service Mesh
		r.Header.Set("X-Upstream-Service", targetService)
		w.Header().Set("X-Served-By", targetService)

		next.ServeHTTP(w, r)
	})
}

func main() {
	canaryRule := func(userID string) bool {
		return userID == "beta_tester_01"
	}

	handler := CanaryMiddleware(canaryRule, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = fmt.Fprintf(w, "Запрос отправлен на: %s", r.Header.Get("X-Upstream-Service"))
	}))

	// Тест 1: обычный пользователь
	rec1 := httptest.NewRecorder()
	req1 := httptest.NewRequest(http.MethodGet, "/orders", nil)
	req1.Header.Set("X-User-ID", "standard_user")
	handler.ServeHTTP(rec1, req1)
	fmt.Printf("Пользователь 1: %s (Served-By: %s)\\n", rec1.Body.String(), rec1.Header().Get("X-Served-By"))

	// Тест 2: участник бета-теста
	rec2 := httptest.NewRecorder()
	req2 := httptest.NewRequest(http.MethodGet, "/orders", nil)
	req2.Header.Set("X-User-ID", "beta_tester_01")
	handler.ServeHTTP(rec2, req2)
	fmt.Printf("Пользователь 2: %s (Served-By: %s)\\n", rec2.Body.String(), rec2.Header().Get("X-Served-By"))
}
"""
validate_go(ex14_code)

exercises.append({
    "num": 14,
    "title": "Канареечная маршрутизация на уровне HTTP Middleware",
    "task": "Реализуйте HTTP Middleware CanaryMiddleware для канареечной маршрутизации. Напишите код извлечения X-User-ID, вычисления признака участия в канарейке и инъекции заголовка X-Upstream-Service для маршрутизации трафика в Kubernetes Service Mesh.",
    "theory": "В архитектуре microservices маршрутизация запросов к разным версиям сервисов часто делегируется Service Mesh (Istio, Linkerd) или API-шлюзу. Middleware в Go перехватывает входящий запрос, извлекает идентификатор клиента (из сессионной куки или заголовка X-User-ID) и оценивает фиче-флаг. По результатам оценки middleware устанавливает специальный заголовок маршрутизации: X-Upstream-Service: orders-service-v2-canary. Внутренний прокси Envoy считывает этот заголовок и направляет TCP-пакет на соответствующий VirtualService, обеспечивая полную прозрачность для вызывающего кода.",
    "step_by_step": "1. Спроектируйте функцию CanaryMiddleware, принимающую предикат isCanaryUser.\\n2. Извлеките идентификатор пользователя из заголовка X-User-ID.\\n3. Определите целевой сервис v1 или v2.\\n4. Установите заголовки запроса и ответа.\\n5. Протестируйте прохождение запросов через middleware.",
    "code_blocks": [{"filename": "canary_middleware.go", "lang": "go", "code": ex14_code}],
    "under_the_hood": "Добавление заголовка в объект r.Header перед вызовом next.ServeHTTP(w, r) делает этот заголовок доступным для всех последующих middleware и обратного прокси httputil.ReverseProxy.",
    "pitfalls": "Никогда не доверяйте заголовку X-Upstream-Service, если он пришел от внешнего публичного клиента из интернета. Всегда перезаписывайте его значение на шлюзе.",
    "bigtech_interview": "Как в Istio настраивают VirtualService для маршрутизации по заголовку (exact / prefix match) и как это сочетается с Go API Gateway?"
})

# Ex 15
ex15_code = """package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// ABExperimentEvent описывает событие взаимодействия пользователя с вариантом фичи.
type ABExperimentEvent struct {
	ExperimentID string
	UserID       string
	Variant      string
	Action       string // "impression", "click", "conversion"
	Timestamp    time.Time
}

// AnalyticsLogger эмулирует сбор событий экспериментов для ClickHouse / Kafka.
type AnalyticsLogger struct {
	mu     sync.Mutex
	events []ABExperimentEvent
}

func (l *AnalyticsLogger) LogImpression(expID, userID, variant string) {
	l.mu.Lock()
	defer l.mu.Unlock()
	l.events = append(l.events, ABExperimentEvent{
		ExperimentID: expID,
		UserID:       userID,
		Variant:      variant,
		Action:       "impression",
		Timestamp:    time.Now(),
	})
	fmt.Printf("[Analytics]: Зафиксирован показ пользователю %s варианта %s в тесте %s\\n",
		userID, variant, expID)
}

func main() {
	analytics := &AnalyticsLogger{}
	_ = context.Background()

	// Имитация вызова OpenFeature StringValue для A/B тестирования цвета кнопки
	buttonVariants := []string{"blue_control", "green_experiment"}

	// Пользователь 1 видит вариант A
	analytics.LogImpression("exp_checkout_button_v1", "usr_101", buttonVariants[0])

	// Пользователь 2 видит вариант B
	analytics.LogImpression("exp_checkout_button_v1", "usr_102", buttonVariants[1])
}
"""
validate_go(ex15_code)

exercises.append({
    "num": 15,
    "title": "Организация A/B тестирования и сбор событий взаимодействия",
    "task": "Спроектируйте архитектуру A/B тестирования на базе фиче-флагов со сбором телеметрии показов (Impression Logging). Реализуйте структуру ABExperimentEvent и логгер событий AnalyticsLogger для последующей отправки в ClickHouse/Kafka с целью расчета статистической значимости конверсий.",
    "theory": "A/B тестирование (Multivariate Experimentation) — научный метод проверки продуктовых гипотез. Фиче-флаг возвращает строковый вариант (например, 'control' vs 'variant_a' vs 'variant_b'). Ключевое правило корректности A/B теста: факт показа варианта (Impression Event) должен быть немедленно залогирован в аналитическую систему (Kafka -> ClickHouse). Если просто показать пользователю вариант, но не зафиксировать событие показа, аналитики не смогут рассчитать размер выборки и конверсию (Conversion Rate), а результаты A/B теста будут статистически невалидными (Sample Ratio Mismatch).",
    "step_by_step": "1. Спроектируйте структуру ABExperimentEvent с полями ExperimentID, UserID, Variant, Action, Timestamp.\\n2. Реализуйте потокобезопасный логгер AnalyticsLogger с методом LogImpression.\\n3. Смоделируйте генерацию событий показа для контрольной и экспериментальной групп.\\n4. Протестируйте фиксацию событий.",
    "code_blocks": [{"filename": "ab_testing.go", "lang": "go", "code": ex15_code}],
    "under_the_hood": "Для минимизации задержек логгер не пишет в сеть синхронно: события собираются в кольцевой буфер в памяти и отправляются батчами по 500 штук в фоновом воркере.",
    "pitfalls": "Логирование показа ДО реального рендеринга кнопки на экране: если сервис сгенерировал вариант 'green', но пользователь закрыл страницу до загрузки, учет показа исказит статистику конверсий.",
    "bigtech_interview": "Что такое Sample Ratio Mismatch (SRM) в A/B тестировании и как рассинхронизация логирования событий приводит к ложным результатам экспериментов?"
})

output_path = "/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch94_p1.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Chapter 94 Part 1 generated successfully: {len(exercises)} exercises.")
