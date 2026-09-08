# -*- coding: utf-8 -*-
import json
import subprocess
import tempfile
import os

exercises = []

# Ex 1
exercises.append({
    "num": 1,
    "title": "Концепция Kubernetes Operator и контрольного цикла (Reconcile Loop)",
    "task": "Изучите философию Kubernetes: переход от императивного управления к декларативному. Объясните назначение паттерна Operator: расширение возможностей ядра Kubernetes для автоматизации сложных приложений (СУБД, кэши, очереди). Нарисуйте схему работы контрольного цикла (Reconciliation Loop): Наблюдение (Observe) -> Анализ различий (Analyze) -> Приведение к желаемому состоянию (Act).",
    "theory": r"""Философия ядра Kubernetes построена на декларативном подходе к управлению инфраструктурой:
1. **Декларативное описание:** Пользователь описывает **желаемое состояние (Desired State)** в виде YAML-манифеста ресурса, а не последовательность императивных команд.
2. **Паттерн Контроллер (Controller):** Фоновый управляющий процесс непрерывно исполняет бесконечный цикл согласования (**Reconciliation Loop**):
   - **Observe (Наблюдение):** Опрос фактического состояния системы через Informers/Listers.
   - **Analyze (Анализ различий):** Вычисление разницы (`Diff`) между текущим состоянием (**Current/Observed State**) и желаемым состоянием (**Desired State**, описанным в `Spec`).
   - **Act (Действие):** Вызов API Kubernetes или внешних систем для устранения расхождения (создание Pod, масштабирование StatefulSet, настройка репликации).

Паттерн **Operator** (введенный компанией CoreOS в 2016 г.):
Это специализированный контроллер, объединяющий пользовательский ресурс (**Custom Resource Definition, CRD**) и операционную экспертизу человека (Site Reliability Engineer) в коде на Go. Оператор автоматизирует жизненный цикл сложных систем с сохранением состояния (Stateful Workloads: PostgreSQL, Kafka, Redis, Elasticsearch): резервное копирование, автоматический failover мастера, ротацию TLS-сертификатов и обновление версий без простоя.""",
    "step_by_step": [
        "Опишите структуры желаемого (`DesiredClusterState`) и текущего (`ObservedClusterState`) состояния.",
        "Реализуйте контрольный цикл `ReconcileLoop`, выполняющий этапы Observe, Analyze и Act.",
        "Запрограммируйте логику масштабирования узлов при обнаружении дрифта спецификации.",
        "Продемонстрируйте работу контроллера при изменении желаемого числа реплик."
    ],
    "code_blocks": [
        {
            "filename": "reconcile_loop_concept.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
	"time"
)

type DesiredClusterState struct {
	ClusterName string
	Replicas    int
	Version     string
}

type ObservedClusterState struct {
	ActivePods []string
	Version    string
}

type OperatorController struct {
	desired  DesiredClusterState
	observed ObservedClusterState
}

func (c *OperatorController) Observe(ctx context.Context) ObservedClusterState {
	return c.observed
}

func (c *OperatorController) Analyze(desired DesiredClusterState, observed ObservedClusterState) int {
	diff := desired.Replicas - len(observed.ActivePods)
	return diff
}

func (c *OperatorController) Act(ctx context.Context, diff int) error {
	if diff > 0 {
		for i := 0; i < diff; i++ {
			podName := fmt.Sprintf("%s-pod-%d", c.desired.ClusterName, len(c.observed.ActivePods)+1)
			c.observed.ActivePods = append(c.observed.ActivePods, podName)
			fmt.Printf("[ACT] Provisioned new stateful pod: %s\n", podName)
		}
	} else if diff < 0 {
		removeCount := -diff
		for i := 0; i < removeCount; i++ {
			lastIdx := len(c.observed.ActivePods) - 1
			removed := c.observed.ActivePods[lastIdx]
			c.observed.ActivePods = c.observed.ActivePods[:lastIdx]
			fmt.Printf("[ACT] Gracefully terminated stateful pod: %s\n", removed)
		}
	} else {
		fmt.Println("[ACT] Cluster is in steady desired state. No actions needed.")
	}
	return nil
}

func (c *OperatorController) Reconcile(ctx context.Context) error {
	fmt.Println("\n--- START RECONCILIATION LOOP ---")
	observed := c.Observe(ctx)
	fmt.Printf("[OBSERVE] Desired Replicas: %d, Observed Active Pods: %d (%v)\n",
		c.desired.Replicas, len(observed.ActivePods), observed.ActivePods)

	diff := c.Analyze(c.desired, observed)
	fmt.Printf("[ANALYZE] Detected discrepancy diff: %+d pods\n", diff)

	return c.Act(ctx, diff)
}

func main() {
	ctrl := &OperatorController{
		desired: DesiredClusterState{
			ClusterName: "postgres-prod",
			Replicas:    3,
			Version:     "v16.1",
		},
		observed: ObservedClusterState{
			ActivePods: []string{"postgres-prod-pod-1"},
			Version:    "v16.1",
		},
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	_ = ctrl.Reconcile(ctx)
	_ = ctrl.Reconcile(ctx)
}
"""
        }
    ],
    "under_the_hood": "В архитектуре Kubernetes контроллеры не хранят локального состояния между циклами. Метод `Reconcile` является чисто идемпотентной функцией от текущего снимка мира: при любом сбое процесс оператора можно убить и перезапустить, и следующий вызов Reconcile восстановит согласованность без повреждения данных.",
    "pitfalls": [
        "Попытка хранить изменяемое состояние внутри полей структуры контроллера: при рестарте оператора или смене лидера в Leader Election несохраненное локальное состояние теряется.",
        "Игнорирование контекста `ctx.Done()` при долгих сетевых операциях, приводящее к зависанию Reconcile воркеров."
    ],
    "bigtech_interview": "В чем отличие паттерна Operator от обычного Deployment контроллера в Kubernetes? Deployment контроллер оперирует stateless-приложениями: ему безразличен порядок запуска и завершения подов, сетевая идентичность и состояние дисков. Operator содержит предметную экспертизу (Domain Knowledge) о конкретном stateful-приложении: знает, какой узел является Primary, как безопасно передать лидерство (Failover), когда запускать `pg_dump` или перестроить Raft-кворум."
})

# Ex 2
exercises.append({
    "num": 2,
    "title": "Проектирование Custom Resource Definition (CRD): Spec vs Status",
    "task": "Спроектируйте кастомный ресурс для базы данных: `DatabaseCluster`. Разделите ресурс на две ключевые секции: `spec` (желаемое состояние, задаваемое пользователем: версия СУБД, количество реплик, лимиты памяти) и `status` (фактическое наблюдаемое состояние кластера: число активных реплик, текущий лидер, список ошибок).",
    "theory": r"""Архитектурный стандарт API Kubernetes требует строгого разделения ресурса на две ключевые подсхемы:
1. **`.spec` (Спецификация / Desired State):**
   - Заполняется пользователем или вышестоящими системами автоматизации (GitOps, ArgoCD).
   - Описывает **что** должно работать: количество реплик, лимиты CPU/Memory, версия СУБД, параметры дискового тома (StorageClass, размер).
   - **Оператор НИКОГДА не должен модифицировать `.spec`** (за исключением редких сценариев мутационных вебхуков или подстановки значений по умолчанию).
2. **`.status` (Статус / Observed State):**
   - Заполняется **исключительно контроллером оператора**.
   - Описывает **фактическое текущее состояние**: текущее число готовых реплик (`readyReplicas`), IP-адрес мастера (`primaryEndpoint`), список аварийных условий (`conditions`).
   - Пользователь не должен вручную редактировать `.status`.

Это разделение поддерживается на уровне ядра Kubernetes через механизм подресурса **`/status` subresource**.""",
    "step_by_step": [
        "Определите Go-структуру `DatabaseClusterSpec` с параметрами конфигурации кластера.",
        "Определите Go-структуру `DatabaseClusterStatus` с полями фактического состояния.",
        "Объедините их в корневую структуру `DatabaseCluster` с метаданными Kubernetes.",
        "Реализуйте сериализацию манифеста в формат JSON/YAML."
    ],
    "code_blocks": [
        {
            "filename": "crd_spec_status_design.go",
            "lang": "go",
            "code": r"""package main

import (
	"encoding/json"
	"fmt"
	"time"
)

type ResourceRequirements struct {
	CPURequest    string `json:"cpu_request"`
	MemoryRequest string `json:"memory_request"`
	StorageSize   string `json:"storage_size"`
}

type DatabaseClusterSpec struct {
	Engine        string               `json:"engine"`
	Version       string               `json:"version"`
	Replicas      int32                `json:"replicas"`
	Resources     ResourceRequirements `json:"resources"`
	BackupEnabled bool                 `json:"backup_enabled"`
}

type ClusterPhase string

const (
	PhasePending     ClusterPhase = "Pending"
	PhaseProvisioning ClusterPhase = "Provisioning"
	PhaseRunning     ClusterPhase = "Running"
	PhaseDegraded    ClusterPhase = "Degraded"
)

type DatabaseClusterStatus struct {
	Phase          ClusterPhase `json:"phase"`
	ReadyReplicas  int32        `json:"ready_replicas"`
	PrimaryNode    string       `json:"primary_node"`
	LastBackupTime *time.Time   `json:"last_backup_time,omitempty"`
	Message        string       `json:"message"`
}

type DatabaseCluster struct {
	APIVersion string                `json:"apiVersion"`
	Kind       string                `json:"kind"`
	Metadata   map[string]string     `json:"metadata"`
	Spec       DatabaseClusterSpec   `json:"spec"`
	Status     DatabaseClusterStatus `json:"status"`
}

func main() {
	cluster := DatabaseCluster{
		APIVersion: "storage.mycompany.com/v1alpha1",
		Kind:       "DatabaseCluster",
		Metadata: map[string]string{
			"name":      "pg-analytics",
			"namespace": "databases",
		},
		Spec: DatabaseClusterSpec{
			Engine:   "PostgreSQL",
			Version:  "16.2",
			Replicas: 3,
			Resources: ResourceRequirements{
				CPURequest:    "2000m",
				MemoryRequest: "8Gi",
				StorageSize:   "100Gi",
			},
			BackupEnabled: true,
		},
		Status: DatabaseClusterStatus{
			Phase:         PhaseRunning,
			ReadyReplicas: 3,
			PrimaryNode:   "pg-analytics-0",
			Message:       "Cluster is healthy and replicating synchronously",
		},
	}

	manifest, err := json.MarshalIndent(cluster, "", "  ")
	if err != nil {
		panic(err)
	}

	fmt.Println("=== DATABASE CLUSTER RESOURCE MANIFEST ===")
	fmt.Println(string(manifest))
}
"""
        }
    ],
    "under_the_hood": "В etcd Kubernetes разделяет доступ к ресурсу: эндпоинт `PUT /apis/group/version/namespaces/ns/databaseclusters/name` обновляет только Spec и Metadata. Для обновления статуса используется специализированный подресурс `PUT .../status`. Это позволяет настраивать раздельные RBAC права (разработчики могут менять spec, но не status) и избегать конфликтов версий при параллельных изменениях.",
    "pitfalls": [
        "Изменение `spec` внутри Reconcile-цикла контроллера: это приводит к мгновенной инвалидации кэша и провоцирует бесконечные рекурсивные вызовы Reconcile (Reconciliation Storm).",
        "Хранение конфиденциальных данных (паролей СУБД) открытым текстом внутри `spec`: пароли должны храниться в `corev1.Secret`, а в `spec` передаваться только `SecretKeySelector`."
    ],
    "bigtech_interview": "Почему в API Kubernetes статус обязательно реализуется как отдельный subresource (/status)? Подресурс `/status` изолирует права доступа: пользователю дается право `update` на основной ресурс для изменения конфигурации, а ServiceAccount оператора наделяется правом `update` на подресурс `status`. Кроме того, при обновлении `/status` API-сервер игнорирует изменения в блоке `.spec`, предотвращая непреднамеренный оверрайд желаемого состояния."
})

# Ex 3
exercises.append({
    "num": 3,
    "title": "Инициализация проекта оператора с помощью Kubebuilder",
    "task": "Установите утилиту `kubebuilder` и инструменты кодогенерации `kustomize`, `controller-gen`. Инициализируйте проект оператора: `kubebuilder init --domain mycompany.com --repo mycompany.com/db-operator`. Изучите структуру сгенерированного проекта: файлы `main.go`, `PROJECT`, папки `api/`, `controllers/`, `config/`.",
    "theory": r"""**Kubebuilder** — официальный SDK сообщества Kubernetes (SIG API Machinery) для разработки операторов на Go с использованием библиотек `controller-runtime` и `client-go`.

Архитектура типового проекта Kubebuilder:
- **`PROJECT`:** Метаданные проекта (домен, плагины, используемые версии API).
- **`cmd/main.go` (или `main.go`):** Точка входа. Создает `ctrl.Manager`, настраивает флаги командной строки, метрики Prometheus, Leader Election и регистрирует контроллеры.
- **`api/v1alpha1/`:** Схемы типов кастомных ресурсов (`*_types.go`), Go-структуры Spec и Status, аннотации генератора маркеров.
- **`internal/controller/`:** Бизнес-логика примирения (`*_controller.go`).
- **`config/`:** Манифесты Kustomize:
  - `crd/`: Сгенерированные YAML-схемы CRD.
  - `rbac/`: Роли и привязки ClusterRole с минимально необходимыми правами.
  - `manager/`: Манифест Deployment для запуска оператора в кластере.""",
    "step_by_step": [
        "Смоделируйте структуру каталогов и файлов проекта Kubebuilder на Go.",
        "Реализуйте парсер конфигурационного файла проекта `PROJECT`.",
        "Создайте структуру проверки валидности файлового дерева проекта.",
        "Продемонстрируйте валидацию обязательных файлов проекта оператора."
    ],
    "code_blocks": [
        {
            "filename": "kubebuilder_project_structure.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"strings"
)

type KubebuilderProjectConfig struct {
	Domain      string
	Layout      string
	ProjectName string
	Repo        string
	Version     string
}

func ValidateProjectTree(files []string) (bool, []string) {
	required := []string{
		"PROJECT",
		"cmd/main.go",
		"config/crd/kustomization.yaml",
		"config/rbac/role.yaml",
		"config/manager/manager.yaml",
	}

	existing := make(map[string]bool)
	for _, f := range files {
		existing[f] = true
	}

	var missing []string
	for _, req := range required {
		if !existing[req] {
			missing = append(missing, req)
		}
	}
	return len(missing) == 0, missing
}

func main() {
	cfg := KubebuilderProjectConfig{
		Domain:      "mycompany.com",
		Layout:      "go.kubebuilder.io/v4",
		ProjectName: "db-operator",
		Repo:        "github.com/mycompany/db-operator",
		Version:     "3",
	}

	simulatedFiles := []string{
		"PROJECT",
		"cmd/main.go",
		"go.mod",
		"config/crd/kustomization.yaml",
		"config/rbac/role.yaml",
		"config/manager/manager.yaml",
	}

	valid, missing := ValidateProjectTree(simulatedFiles)

	fmt.Println("=== KUBEBUILDER PROJECT INITIALIZATION ===")
	fmt.Printf("Domain:  %s\nRepo:    %s\nLayout:  %s\n", cfg.Domain, cfg.Repo, cfg.Layout)
	fmt.Printf("Project structure valid: %v (Missing: %s)\n", valid, strings.Join(missing, ", "))
}
"""
        }
    ],
    "under_the_hood": "Команда `kubebuilder init` использует шаблонизатор Go (`text/template`) для генерации скаффолдинга. Она создает файл `PROJECT`, фиксирующий плагины кодогенерации (например `go.kubebuilder.io/v4`), что позволяет последующим командам `kubebuilder create api` точно знать целевые директории и структуру пакетов.",
    "pitfalls": [
        "Несовпадение имени Go-модуля в `go.mod` и аргумента `--repo`: приводит к ошибкам импорта пакетов контроллеров при сборке.",
        "Ручная модификация манифестов в папке `config/crd/bases/`: эти файлы генерируются автоматически командой `make manifests`, любые ручные правки затираются."
    ],
    "bigtech_interview": "В чем разница между Kubebuilder и Operator SDK от Red Hat? Исторически Operator SDK поддерживал Ansible и Helm операторы в дополнение к Go. Начиная с версии Operator SDK v1.0, для Go-операторов под капотом используется именно Kubebuilder в виде подключаемого плагина. Сегодня Kubebuilder является признанным отраслевым стандартом архитектуры контроллеров на Go."
})

# Ex 4
exercises.append({
    "num": 4,
    "title": "Создание API кастомного ресурса с помощью Kubebuilder CLI",
    "task": "Выполните команду `kubebuilder create api --group storage --version v1alpha1 --kind DatabaseCluster`. Разберите структуру сгенерированных Go-файлов в папке `api/v1alpha1/`: `databasecluster_types.go`. Поймите роль встроенных структур `metav1.TypeMeta` и `metav1.ObjectMeta`.",
    "theory": r"""Команда `kubebuilder create api` регистрирует новую GroupVersionKind (GVK) схему:
1. **Group:** Логическая группировка API (например `storage.mycompany.com`).
2. **Version:** Стадия зрелости контракта (`v1alpha1` -> `v1beta1` -> `v1`).
3. **Kind:** Название сущности в верхнем регистре CamelCase (`DatabaseCluster`).

Анатомия корневого объекта кастомного ресурса:
- **`metav1.TypeMeta`:** Содержит строковые поля `Kind` и `APIVersion`. Необходима сериализатору Kubernetes для определения схемы десериализации объекта из JSON/YAML.
- **`metav1.ObjectMeta`:** Стандартные метаданные платформы:
  - `Name` и `Namespace`: уникальный составной ключ объекта.
  - `UID`: глобальный UUID, генерируемый etcd.
  - `ResourceVersion`: монотонно возрастающая версия для оптимистической блокировки.
  - `Generation`: числовой счетчик изменений спецификации (`Spec`).
  - `Labels` и `Annotations`: метки селекторов и метаданные.
  - `OwnerReferences`: связи владения для Garbage Collector.
  - `Finalizers`: блокираторы удаления объекта.""",
    "step_by_step": [
        "Определите типы `TypeMeta` и `ObjectMeta`, эмулирующие стандартные метаданные Kubernetes.",
        "Создайте структуру `DatabaseCluster` с встраиванием метаданных.",
        "Реализуйте метод проверки равенства GroupVersionKind.",
        "Продемонстрируйте инициализацию кастомного ресурса с заполнением метаданных."
    ],
    "code_blocks": [
        {
            "filename": "crd_types_gvk.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
)

type TypeMeta struct {
	Kind       string `json:"kind"`
	APIVersion string `json:"apiVersion"`
}

type ObjectMeta struct {
	Name            string            `json:"name"`
	Namespace       string            `json:"namespace"`
	UID             string            `json:"uid"`
	ResourceVersion string            `json:"resourceVersion"`
	Generation      int64             `json:"generation"`
	Labels          map[string]string `json:"labels,omitempty"`
	Finalizers      []string          `json:"finalizers,omitempty"`
}

type DatabaseCluster struct {
	TypeMeta   `json:",inline"`
	ObjectMeta `json:"metadata,omitempty"`

	Spec   map[string]any `json:"spec,omitempty"`
	Status map[string]any `json:"status,omitempty"`
}

func (c *DatabaseCluster) GroupVersionKind() string {
	return fmt.Sprintf("%s, Kind=%s", c.APIVersion, c.Kind)
}

func main() {
	cluster := &DatabaseCluster{
		TypeMeta: TypeMeta{
			APIVersion: "storage.mycompany.com/v1alpha1",
			Kind:       "DatabaseCluster",
		},
		ObjectMeta: ObjectMeta{
			Name:            "redis-cache",
			Namespace:       "production",
			UID:             "d9b1c7a8-1234-5678-9abc-def012345678",
			ResourceVersion: "100452",
			Generation:      1,
			Labels: map[string]string{
				"app.kubernetes.io/managed-by": "db-operator",
			},
			Finalizers: []string{"storage.mycompany.com/cleanup-snapshots"},
		},
	}

	fmt.Println("=== KUBERNETES CUSTOM RESOURCE GVK ===")
	fmt.Printf("GVK:        %s\n", cluster.GroupVersionKind())
	fmt.Printf("Namespace:  %s\n", cluster.Namespace)
	fmt.Printf("Name:       %s\n", cluster.Name)
	fmt.Printf("Generation: %d\n", cluster.Generation)
}
"""
        }
    ],
    "under_the_hood": "В Go директива `json:\",inline\"` указывает кодеку слияние полей `TypeMeta` на верхний уровень JSON-документа. При регистрации в схеме рантайма (`scheme.Builder.Register`) типы привязываются к объекту `schema.GroupVersionKind`, позволяя `controller-runtime` полиморфно восстанавливать точный тип структуры Go по содержимому HTTP-запроса.",
    "pitfalls": [
        "Забытое встраивание `metav1.TypeMeta` или `metav1.ObjectMeta`: делает структуру несовместимой с интерфейсом `client.Object`, из-за чего контроллер не сможет компилироваться.",
        "Именование полей структуры с маленькой буквы (неэкспортируемые поля): такие поля не сериализуются и не попадут в сгенерированный CRD манифест."
    ],
    "bigtech_interview": "В чем разница между полями ResourceVersion и Generation в ObjectMeta? `ResourceVersion` — это внутренняя монотонная версия записи в etcd; она изменяется при абсолютно любых модификациях объекта (включая служебные обновления `.status`, annotations и labels). `Generation` увеличивается API-сервером ТОЛЬКО при изменениях желаемой спецификации (`.spec`). Контроллеры используют проверку изменения Generation, чтобы не тратить ресурсы на повторное примирение при обновлении статуса."
})

# Ex 5
exercises.append({
    "num": 5,
    "title": "Разметка Go-структур маркерами генератора (Kubebuilder Markers)",
    "task": "Добавьте аннотации генератора ко всем полям структуры: `// +kubebuilder:validation:Minimum=1`, `// +kubebuilder:validation:Maximum=9`, `// +kubebuilder:subresource:status`, `// +kubebuilder:printcolumn:name=\"Replicas\",type=\"integer\",JSONPath=\".spec.replicas\"`. Сгенерируйте YAML-манифест CRD с помощью команды `make manifests`.",
    "theory": r"""Генератор манифестов **`controller-gen`** анализирует комментарии к структурам Go со специальным префиксом `// +kubebuilder:`.

Ключевые категории маркеров:
1. **CRD Метаданные и подресурсы:**
   - `// +kubebuilder:subresource:status` — активирует выделенный подресурс `/status`.
   - `// +kubebuilder:subresource:scale:specpath=.spec.replicas,statuspath=.status.replicas` — включает поддержку команды `kubectl scale`.
2. **Отображение в `kubectl get`:**
   - `// +kubebuilder:printcolumn:name="Replicas",type="integer",JSONPath=".spec.replicas"` — добавляет кастомные колонки в вывод консоли.
3. **OpenAPI v3 Валидация:**
   - `// +kubebuilder:validation:Minimum=1` — ограничение минимального числового значения.
   - `// +kubebuilder:validation:Pattern="^[a-z0-9-]+$"` — регулярное выражение для строк.
   - `// +kubebuilder:validation:Enum=PostgreSQL;MySQL;Redis` — перечисление допустимых значений.
   - `// +kubebuilder:default=3` — значение по умолчанию при отсутствии поля.""",
    "step_by_step": [
        "Опишите структуру с маркерами валидации Kubebuilder в комментариях.",
        "Реализуйте парсер маркерных комментариев для извлечения правил валидации.",
        "Сгенерируйте фрагмент спецификации OpenAPI v3 Validation Schema на основе маркеров.",
        "Продемонстрируйте валидацию переданных значений согласно сгенерированным правилам."
    ],
    "code_blocks": [
        {
            "filename": "kubebuilder_markers_generator.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
)

type FieldValidationRule struct {
	FieldName string
	Min       int
	Max       int
	Required  bool
}

func ValidateClusterReplicas(replicas int, rule FieldValidationRule) error {
	if rule.Required && replicas == 0 {
		return fmt.Errorf("field '%s' is required", rule.FieldName)
	}
	if replicas < rule.Min {
		return fmt.Errorf("field '%s' value %d violates minimum constraint (%d)", rule.FieldName, replicas, rule.Min)
	}
	if replicas > rule.Max {
		return fmt.Errorf("field '%s' value %d violates maximum constraint (%d)", rule.FieldName, replicas, rule.Max)
	}
	return nil
}

func main() {
	rule := FieldValidationRule{
		FieldName: "replicas",
		Min:       1,
		Max:       9,
		Required:  true,
	}

	fmt.Println("=== TESTING KUBEBUILDER VALIDATION RULES ===")
	err := ValidateClusterReplicas(3, rule)
	fmt.Printf("Replicas: 3 -> Valid: %v (err: %v)\n", err == nil, err)

	err = ValidateClusterReplicas(12, rule)
	fmt.Printf("Replicas: 12 -> Valid: %v (err: %v)\n", err == nil, err)

	err = ValidateClusterReplicas(0, rule)
	fmt.Printf("Replicas: 0 -> Valid: %v (err: %v)\n", err == nil, err)
}
"""
        }
    ],
    "under_the_hood": "Утилита `controller-gen` использует пакет `go/parser` для синтаксического анализа AST-дерева Go файлов. Она считывает комментарии перед полями структур, транслирует их в структуры валидации OpenAPI v3 (`apiextensionsv1.CustomResourceValidation`) и сохраняет в итоговый YAML-манифест в `config/crd/bases/`.",
    "pitfalls": [
        "Случайный пробел между `//` и `+kubebuilder:`: комментарий `//  +kubebuilder:` будет проигнорирован генератором, и правило валидации не попадет в CRD.",
        "Использование маркера валидации для опционального поля без указания указателя: в Go число `int32` по умолчанию равно 0. Если поле не является указателем `*int32`, но имеет правило `Minimum=1`, пустой запрос пользователя всегда будет завершаться ошибкой валидации."
    ],
    "bigtech_interview": "Почему валидация через маркеры OpenAPI v3 предпочтительнее Validating Admission Webhook везде, где это возможно? Схема OpenAPI v3 исполняется непосредственно внутри API-сервера без сетевых вызовов. Это дает минимальную задержку (субмиллисекунды), защищает кластер от сбоев вебхуков при сетевых разделениях и не создает дополнительной нагрузки на рантайм оператора."
})

# Ex 6
exercises.append({
    "num": 6,
    "title": "Генерация методов DeepCopy (zz_generated.deepcopy.go)",
    "task": "Объясните, почему рантайм Kubernetes требует, чтобы каждый объект схемы реализовывал интерфейс `runtime.Object` с методом `DeepCopyObject()`. Запустите генерацию методов глубокого копирования через `controller-gen object paths=\"./...\"` и изучите сгенерированный код.",
    "theory": r"""В ядре Kubernetes и библиотеке `client-go` каждый ресурс обязан реализовывать интерфейс `runtime.Object`:
```go
type Object interface {
    GetObjectKind() schema.ObjectKind
    DeepCopyObject() Object
}
```

Зачем необходимо глубокое копирование (**DeepCopy**)?
1. **Кэш Информера (Informer Cache):** Клиент `controller-runtime` возвращает указатели на объекты, хранящиеся в разделяемом in-memory кэше.
2. **Предотвращение гонок данных (Data Races):** Если контроллер начнет напрямую модифицировать поля возвращенного указателя, он повредит общий кэш и вызовет race condition с другими потоками или воркерами.
3. **Безопасная мутация:** Перед любой модификацией объекта или передачей в функцию примирения вызывается `instance.DeepCopy()`, создающий полную изолированную копию всех срезов, мап и указателей в куче.""",
    "step_by_step": [
        "Определите интерфейс `DeepCopyable` с методом глубокого клонирования.",
        "Реализуйте ручной метод `DeepCopyInto` для структуры кастомного ресурса с копированием срезов.",
        "Продемонстрируйте, что модификация копии не затрагивает исходный объект в кэше.",
        "Объясните назначение сгенерированного файла `zz_generated.deepcopy.go`."
    ],
    "code_blocks": [
        {
            "filename": "deepcopy_implementation.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
)

type DatabaseClusterSpec struct {
	Replicas int
	Tags     []string
	Settings map[string]string
}

type DatabaseCluster struct {
	Name string
	Spec DatabaseClusterSpec
}

func (in *DatabaseCluster) DeepCopyInto(out *DatabaseCluster) {
	*out = *in
	if in.Spec.Tags != nil {
		in, out := &in.Spec.Tags, &out.Spec.Tags
		*out = make([]string, len(*in))
		copy(*out, *in)
	}
	if in.Spec.Settings != nil {
		in, out := &in.Spec.Settings, &out.Spec.Settings
		*out = make(map[string]string, len(*in))
		for key, val := range *in {
			(*out)[key] = val
		}
	}
}

func (in *DatabaseCluster) DeepCopy() *DatabaseCluster {
	if in == nil {
		return nil
	}
	out := new(DatabaseCluster)
	in.DeepCopyInto(out)
	return out
}

func main() {
	original := &DatabaseCluster{
		Name: "redis-master",
		Spec: DatabaseClusterSpec{
			Replicas: 3,
			Tags:     []string{"cache", "in-memory"},
			Settings: map[string]string{"maxmemory": "4gb"},
		},
	}

	clone := original.DeepCopy()

	// Мутируем клон
	clone.Spec.Replicas = 5
	clone.Spec.Tags[0] = "MUTATED"
	clone.Spec.Settings["maxmemory"] = "16gb"

	fmt.Println("=== DEEP COPY ISOLATION TEST ===")
	fmt.Printf("Original: Replicas=%d, Tag[0]=%s, maxmemory=%s\n",
		original.Spec.Replicas, original.Spec.Tags[0], original.Spec.Settings["maxmemory"])
	fmt.Printf("Clone:    Replicas=%d, Tag[0]=%s, maxmemory=%s\n",
		clone.Spec.Replicas, clone.Spec.Tags[0], clone.Spec.Settings["maxmemory"])
}
"""
        }
    ],
    "under_the_hood": "Генератор `controller-gen object` создает файл `zz_generated.deepcopy.go`. Он генерирует оптимизированный ассемблерно-подобный код на чистом Go без рефлексии (`reflect`), выполняя побайтовое копирование примитивов и рекурсивный `make + copy` для слайсов и мап, что работает на порядок быстрее `encoding/json` сериализации.",
    "pitfalls": [
        "Поверхностное копирование (Shallow Copy `*out = *in`) без глубокого клонирования слайсов и мап: ссылки на лежащие в куче массивы остаются общими, провоцируя скрытые гонки данных при параллельной работе контроллера.",
        "Ручное удаление файла `zz_generated.deepcopy.go`: компиляция немедленно завершится ошибкой отсутствия метода `DeepCopyObject()`."
    ],
    "bigtech_interview": "Почему в client-go запрещено напрямую мутировать объекты, полученные через lister.Get()? `lister.Get()` возвращает прямой указатель на объект из локального in-memory кэша информера (Informer Cache). Прямая мутация этого объекта изменяет данные в общем кэше в обход API-сервера etcd, нарушает целостность данных для всех остальных контроллеров процесса и порождает Data Race."
})

# Ex 7
exercises.append({
    "num": 7,
    "title": "Анатомия метода Reconcile в Controller-Runtime",
    "task": "Разберите сигнатуру метода: `Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error)`. Объясните, почему входящий запрос `req` содержит только пространство имен (`Namespace`) и имя ресурса (`Name`), а не сам объект: контроллер обязан самостоятельно запросить актуальное состояние из кэша API-сервера.",
    "theory": r"""Сигнатура метода Reconcile в `sigs.k8s.io/controller-runtime`:
```go
func (r *Reconciler) Reconcile(ctx context.Context, req reconcile.Request) (reconcile.Result, error)
```

Почему `reconcile.Request` содержит только `types.NamespacedName` (Namespace и Name), а не само тело объекта?
1. **Защита от устаревших событий (Stale Events):** Между моментом генерации события в API-сервере и его извлечением воркером из очереди может пройти время (очередь перегружена, сетевая задержка). Если бы передавался сам объект, контроллер работал бы с устаревшим снимком.
2. **Схлопывание событий (Event Coalescing):** Если объект изменился 100 раз подряд, очередь `workqueue` сохраняет только один ключ `namespace/name`. Воркер просыпается один раз и запрашивает **самое свежее состояние на текущую миллисекунду** из кэша.
3. **Обработка удаления:** Если ресурс был удален, в etcd его уже нет. Контроллер вызывает `client.Get`, получает ошибку `NotFound` и корректно завершает примирение.""",
    "step_by_step": [
        "Определите типы `Request` и `Result`, моделирующие API `controller-runtime`.",
        "Создайте имитатор локального кэша объектов `MockClient`.",
        "Реализуйте контроллер с методом `Reconcile`, извлекающим актуальный объект по ключу `NamespacedName`.",
        "Продемонстрируйте обработку найденного объекта и ветвление при отсутствии ресурса."
    ],
    "code_blocks": [
        {
            "filename": "reconcile_anatomy.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
	"time"
)

type NamespacedName struct {
	Namespace string
	Name      string
}

type Request struct {
	NamespacedName NamespacedName
}

type Result struct {
	Requeue      bool
	RequeueAfter time.Duration
}

type DatabaseCluster struct {
	Name      string
	Namespace string
	Replicas  int
}

type MockClient struct {
	storage map[string]*DatabaseCluster
}

func (c *MockClient) Get(key NamespacedName) (*DatabaseCluster, error) {
	k := fmt.Sprintf("%s/%s", key.Namespace, key.Name)
	if obj, ok := c.storage[k]; ok {
		return obj, nil
	}
	return nil, fmt.Errorf("resource not found")
}

type ClusterReconciler struct {
	client *MockClient
}

func (r *ClusterReconciler) Reconcile(ctx context.Context, req Request) (Result, error) {
	fmt.Printf("[RECONCILE] Triggered for key: %s/%s\n", req.NamespacedName.Namespace, req.NamespacedName.Name)

	instance, err := r.client.Get(req.NamespacedName)
	if err != nil {
		fmt.Printf("[RECONCILE] Object %s/%s not found (deleted). Terminating reconcile.\n",
			req.NamespacedName.Namespace, req.NamespacedName.Name)
		return Result{}, nil
	}

	fmt.Printf("[RECONCILE] Successfully fetched fresh state: Name=%s, Replicas=%d\n",
		instance.Name, instance.Replicas)
	return Result{RequeueAfter: 60 * time.Second}, nil
}

func main() {
	client := &MockClient{
		storage: map[string]*DatabaseCluster{
			"prod/redis-cluster": {Name: "redis-cluster", Namespace: "prod", Replicas: 6},
		},
	}

	reconciler := &ClusterReconciler{client: client}

	// 1. Примирение существующего объекта
	res, err := reconciler.Reconcile(context.Background(), Request{
		NamespacedName: NamespacedName{Namespace: "prod", Name: "redis-cluster"},
	})
	fmt.Printf("Result 1: RequeueAfter=%v, Err=%v\n\n", res.RequeueAfter, err)

	// 2. Примирение удаленного объекта
	res, err = reconciler.Reconcile(context.Background(), Request{
		NamespacedName: NamespacedName{Namespace: "prod", Name: "deleted-cluster"},
	})
	fmt.Printf("Result 2: RequeueAfter=%v, Err=%v\n", res.RequeueAfter, err)
}
"""
        }
    ],
    "under_the_hood": "В `controller-runtime` очередь `workqueue` является дедуплицированной очередью с задержкой (RateLimitingQueue). При добавлении нескольких событий для одного ключа `foo/bar`, если ключ уже находится в очереди на обработку, он не дублируется. Это обеспечивает феноменальную устойчивость операторов к лавинообразным всплескам нагрузки.",
    "pitfalls": [
        "Возврат ошибки `return ctrl.Result{}, err`, когда ресурс не найден (`apierrors.IsNotFound(err)`): это приведет к бесконечным повторам Reconcile с экспоненциальным backoff для уже удаленного объекта.",
        "Попытка сериализовать тело объекта в очередь вместо `NamespacedName`: это резко увеличивает потребление памяти и приводит к обработке неактуальных версий состояния."
    ],
    "bigtech_interview": "Почему очередь событий в контроллере Kubernetes оперирует только ключами NamespacedName, а не самими объектами ресурсов? 1) Экономия памяти очереди; 2) Дедупликация (Coalescing): если ресурс модифицируется 100 раз в секунду, контроллер выполнит Reconcile всего один раз для самого последнего снимка; 3) Защита от Stale Data: воркер всегда читает актуальное состояние из кэша в момент начала обработки, а не состояние на момент генерации события."
})

# Ex 8
exercises.append({
    "num": 8,
    "title": "Идемпотентность контроллера: ключевое требование надежности",
    "task": "Сформулируйте требование идемпотентности: контроллер может быть вызван многократно для одного и того же состояния (в том числе при сетевых сбоях или ложных срабатываниях). Напишите код примирения дочернего Deployment: если Deployment уже существует и его спецификация совпадает с желаемой, никаких действий не предпринимается.",
    "theory": r"""**Идемпотентность** — фундаментальный закон распределенных систем управления:
> Функция $f(x)$ идемпотентна, если повторный вызов $f(f(x))$ дает в точности тот же результат, что и однократный $f(x)$, без побочных эффектов.

В Kubernetes оператор может быть перезапущен в любой произвольный момент времени:
- Из-за сбоя ноды кластера или OOM-Kill.
- Из-за смены лидера в Leader Election.
- Из-за ложного срабатывания периодического таймера ресинхронизации (Resync Period).

Контроллер обязан проектироваться так, чтобы при запуске Reconcile:
1. Проверять существование дочернего ресурса (`client.Get`).
2. Если ресурс отсутствует — создавать его (`client.Create`).
3. Если ресурс существует — сравнивать желаемые и фактические поля (`Diff`).
4. Если различий нет — **завершать работу без вызовов API на запись**.""",
    "step_by_step": [
        "Определите модель дочернего объекта `Deployment` с полями Replicas и Image.",
        "Реализуйте функцию вычисления расхождения `HasDeploymentDrift`.",
        "Запрограммируйте идемпотентный метод `ReconcileDeployment` с защитой от лишних вызовов Update.",
        "Продемонстрируйте сценарии: создание нового, пропуск идентичного и обновление изменившегося ресурса."
    ],
    "code_blocks": [
        {
            "filename": "idempotent_reconcile.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
)

type Deployment struct {
	Name     string
	Replicas int
	Image    string
}

type ReconcileAction string

const (
	ActionCreate ReconcileAction = "CREATE"
	ActionUpdate ReconcileAction = "UPDATE"
	ActionNoop   ReconcileAction = "NOOP"
)

func ReconcileDeployment(desired Deployment, current *Deployment) (ReconcileAction, *Deployment) {
	if current == nil {
		created := desired
		return ActionCreate, &created
	}

	// Проверка на дрифт конфигурации
	drift := false
	if current.Replicas != desired.Replicas {
		current.Replicas = desired.Replicas
		drift = true
	}
	if current.Image != desired.Image {
		current.Image = desired.Image
		drift = true
	}

	if drift {
		return ActionUpdate, current
	}
	return ActionNoop, current
}

func main() {
	desired := Deployment{Name: "postgres-pooler", Replicas: 3, Image: "pgbouncer:1.22"}

	fmt.Println("=== IDEMPOTENT RECONCILIATION TEST ===")

	// 1. Первый проход: объект не существует -> CREATE
	action, current := ReconcileDeployment(desired, nil)
	fmt.Printf("Step 1: Action=%s, State=%+v\n", action, *current)

	// 2. Второй проход: объект уже в нужном состоянии -> NOOP (идемпотентность!)
	action, current = ReconcileDeployment(desired, current)
	fmt.Printf("Step 2: Action=%s, State=%+v\n", action, *current)

	// 3. Третий проход: пользователь изменил желаемый образ -> UPDATE
	desired.Image = "pgbouncer:1.23"
	action, current = ReconcileDeployment(desired, current)
	fmt.Printf("Step 3: Action=%s, State=%+v\n", action, *current)
}
"""
        }
    ],
    "under_the_hood": "Если контроллер выполняет `client.Update()` для объекта, поля которого не изменились, API-сервер Kubernetes все равно генерирует событие изменения `ResourceVersion`. Это событие снова попадает в очередь информера и вызывает повторный Reconcile, замыкая бесконечный паразитный цикл (Hot Loop), перегружающий etcd.",
    "pitfalls": [
        "Слепой вызов `client.Create()` без предварительной проверки существования ресурса: вызовет ошибку `AlreadyExists` и приведет к сбою цикла.",
        "Сравнение объектов целиком через `reflect.DeepEqual(current, desired)`: Kubernetes API-сервер автоматически добавляет системные поля (defaulting, статусы, служебные аннотации), поэтому `DeepEqual` всегда будет возвращать `false`."
    ],
    "bigtech_interview": "Как избежать бесконечного цикла Reconcile (Hot Loop), когда оператор постоянно обновляет дочерний ресурс? 1) Сравнивать только те поля, которыми управляет оператор (например, `spec.template`), игнорируя служебные метаданные; 2) Использовать предикаты `predicate.GenerationChangedPredicate`, отсекающие события без изменения `.spec`; 3) Переходить на современный механизм Server-Side Apply (SSA), где API-сервер сам рассчитывает владение полями и диффы."
})

# Ex 9
exercises.append({
    "num": 9,
    "title": "Чтение ресурсов через Controller-Runtime Client (Get & List)",
    "task": "Используйте `r.Client.Get(ctx, req.NamespacedName, instance)` для извлечения кастомного ресурса. Корректно обработайте ошибку отсутствия ресурса: `if apierrors.IsNotFound(err) { return ctrl.Result{}, nil }` (объект был удален из кластера, примирение завершается успешно).",
    "theory": r"""Интерфейс `client.Client` в библиотеке `controller-runtime` объединяет методы чтения и записи:
- **`Get(ctx, key, obj)`:** Считывает один объект по `types.NamespacedName`.
- **`List(ctx, list, opts...)`:** Считывает список объектов с фильтрацией по Namespace, Labels (`client.MatchingLabels`) или полям (`client.MatchingFields`).

Критически важный паттерн обработки ошибки удаления:
Когда ресурс удаляется из кластера, контроллер получает событие удаления и вызывает `r.Get()`. API-сервер возвращает ошибку `StatusReasonNotFound`.
```go
if err := r.Get(ctx, req.NamespacedName, cluster); err != nil {
    if apierrors.IsNotFound(err) {
        // Ресурс удален! Примирение завершается штатно.
        return ctrl.Result{}, nil
    }
    // Реальная сетевая ошибка: возвращаем err для повтора
    return ctrl.Result{}, err
}
```
Если в блоке `IsNotFound` вернуть `err`, контроллер будет бесконечно пытаться повторить примирение несуществующего ресурса.""",
    "step_by_step": [
        "Определите интерфейс клиента с методами `Get` и `List`.",
        "Реализуйте обработчик с проверкой ошибки `IsNotFound`.",
        "Запрограммируйте выборку дочерних подов через селектор меток `MatchingLabels`.",
        "Продемонстрируйте штатный выход при удалении ресурса."
    ],
    "code_blocks": [
        {
            "filename": "client_get_list_patterns.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
)

var ErrNotFound = errors.New("NotFound")

type MockK8sClient struct {
	data map[string]string
}

func (c *MockK8sClient) Get(ctx context.Context, key string) (string, error) {
	if val, ok := c.data[key]; ok {
		return val, nil
	}
	return "", ErrNotFound
}

func IsNotFound(err error) bool {
	return errors.Is(err, ErrNotFound)
}

func ReconcileResource(ctx context.Context, client *MockK8sClient, key string) (string, error) {
	val, err := client.Get(ctx, key)
	if err != nil {
		if IsNotFound(err) {
			return "SUCCESS_DELETED_CLEANUP", nil
		}
		return "ERROR_RETRY", err
	}
	return fmt.Sprintf("SUCCESS_PROCESSED: %s", val), nil
}

func main() {
	client := &MockK8sClient{
		data: map[string]string{
			"databases/postgres-prod": "SPEC_REPLICAS_3",
		},
	}

	ctx := context.Background()

	// 1. Чтение существующего ресурса
	res, err := ReconcileResource(ctx, client, "databases/postgres-prod")
	fmt.Printf("Existing:  Result=%s, Err=%v\n", res, err)

	// 2. Чтение удаленного ресурса (IsNotFound)
	res, err = ReconcileResource(ctx, client, "databases/deleted-cluster")
	fmt.Printf("Deleted:   Result=%s, Err=%v\n", res, err)
}
"""
        }
    ],
    "under_the_hood": "По умолчанию вызовы `r.Client.Get` и `r.Client.List` обращаются не к реальному etcd, а к локальному in-memory кэшу на базе `client-go` Informer. Чтение выполняется за наносекунды из оперативной памяти процесса без выполнения сетевых HTTP-запросов к API-серверу.",
    "pitfalls": [
        "Паника при передаче непроинициализированного указателя в `r.Get(ctx, key, obj)`: объект `obj` обязан быть выделен через `new(MyType)` или `&MyType{}` до передачи в метод.",
        "Использование прямого чтения `client.Reader` без крайней необходимости: обход кэша создает колоссальную нагрузку на API-сервер и etcd при масштабировании оператора."
    ],
    "bigtech_interview": "Почему в контроллерах Kubernetes вызовы Get и List по умолчанию читают данные из кэша, а не напрямую из API-сервера? В крупном кластере работают сотни контроллеров, обрабатывающих миллионы событий в секунду. Если бы каждый Reconcile выполнял прямой сетевой запрос в etcd, API-сервер исчерпал бы сокеты и упал под DoS-нагрузкой. Кэш информеров синхронизируется через единое долгоживущее HTTP/2 Watch-соединение, а чтение обслуживается локально из памяти."
})

# Ex 10
exercises.append({
    "num": 10,
    "title": "Кэширование, Informers и Listers в Controller-Runtime",
    "task": "Объясните, как устроен клиент `controller-runtime`: вызовы `Get` и `List` по умолчанию читают данные из локального in-memory кэша (Informer cache), поддерживаемого через Watch-соединение с API-сервером. Почему прямые запросы к API-серверу запрещены при высокой нагрузке на кластер?",
    "theory": r"""Архитектура кэширования **Informer** в Kubernetes:
1. **Reflector:** Компонент, поддерживающий актуальность данных. На старте он выполняет один `List` запрос для наполнения кэша, а затем держит постоянное HTTP/2 `Watch` соединение с API-сервером для получения стрима изменений (`Added`, `Modified`, `Deleted`).
2. **Delta FIFO:** Очередь, упорядочивающая входящие события от Reflector.
3. **Indexer (In-Memory Cache):** Локальное потокобезопасное хранилище объектов в оперативной памяти Go-процесса оператора.
4. **Lister:** Предоставляет read-only доступ к Indexer без сетевых задержек.

**Проблема Read-After-Write Consistency (Несогласованность после записи):**
Поскольку кэш информера обновляется асинхронно через Watch-канал, возникает сетевой лаг (обычно 1–10 мс).
Если контроллер выполнит запись `r.Create(pod)`, а на следующей строке вызовет кэшированный `r.Get(pod)`, он может получить ошибку `NotFound`, так как событие Watch еще не долетело до локального информера!""",
    "step_by_step": [
        "Смоделируйте архитектуру кэша Informer с потокобезопасным хранилищем `Indexer`.",
        "Реализуйте симуляцию лага обновления кэша при операциях записи.",
        "Покажите разницу между чтением из кэша и прямым чтением (Direct Reader).",
        "Продемонстрируйте влияние лага Watch-канала на повторный Reconcile."
    ],
    "code_blocks": [
        {
            "filename": "informer_cache_architecture.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"sync"
	"time"
)

type InformerCache struct {
	mu    sync.RWMutex
	store map[string]string
}

func NewInformerCache() *InformerCache {
	return &InformerCache{store: make(map[string]string)}
}

func (c *InformerCache) Get(key string) (string, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	val, ok := c.store[key]
	return val, ok
}

func (c *InformerCache) OnWatchEvent(key, val string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.store[key] = val
}

func main() {
	cache := NewInformerCache()

	// 1. Попытка чтения до получения события Watch
	_, found := cache.Get("default/my-db")
	fmt.Printf("[Cache Read 1] Before Watch event: found=%v\n", found)

	// 2. Имитация задержки сетевого Watch канала
	go func() {
		time.Sleep(20 * time.Millisecond)
		cache.OnWatchEvent("default/my-db", "READY")
	}()

	time.Sleep(50 * time.Millisecond)

	// 3. Чтение после обновления кэша информером
	val, found := cache.Get("default/my-db")
	fmt.Printf("[Cache Read 2] After Watch sync:   found=%v, val=%s\n", found, val)
}
"""
        }
    ],
    "under_the_hood": "В `controller-runtime` клиент `mgr.GetClient()` является составным (**DelegatingClient**): все операции `Get` и `List` он автоматически направляет в Informer Cache, а все мутирующие операции (`Create`, `Update`, `Patch`, `Delete`) отправляет напрямую в API-сервер по HTTP/2.",
    "pitfalls": [
        "Попытка немедленного повторного чтения только что созданного объекта через `r.Get`: из-за асинхронного лага кэша объект может еще не появиться в кэше. Всегда используйте объект, возвращенный операцией `Create`/`Update`, либо полагайтесь на следующий цикл Reconcile.",
        "Переполнение оперативной памяти (OOM) оператора из-за кэширования тяжелых объектов: по умолчанию информер кэширует все поля всех объектов отслеживаемого типа в кластере."
    ],
    "bigtech_interview": "Что такое проблема Read-After-Write lag в controller-runtime и как с ней бороться? При вызове `r.Create(pod)` объект записывается в etcd, но локальный кэш информера обновляется асинхронно через Watch-стрим с задержкой в несколько миллисекунд. Если контроллер сразу же вызывает кэшированный `r.Get(pod)`, он может получить NotFound. Борьба: 1) Не читать объект сразу после создания; 2) Завершать Reconcile и доверять тому, что событие создания само инициирует следующий Reconcile, когда дойдет до информера."
})

print("Writing Chapter 91 Part 1 (exercises 1-10 processed)")

# Ex 11
exercises.append({
    "num": 11,
    "title": "Фильтрация событий примирения (Event Predicates)",
    "task": "По умолчанию контроллер перезапускает `Reconcile` при любом изменении объекта, включая обновление служебных полей статуса. Подключите предикат `predicate.GenerationChangedPredicate{}` в билдер контроллера: примирение будет запускаться ТОЛЬКО при изменении спецификации (`metadata.generation`), предотвращая бесконечные циклы.",
    "theory": r"""В Kubernetes каждое изменение любого поля объекта генерирует событие `UpdateEvent`.
Если оператор обновляет поле `.status`, API-сервер увеличивает `metadata.resourceVersion` и рассылает событие информерам.
Если контроллер не настроит фильтрацию событий, он попадет в бесконечный цикл:
`Reconcile -> r.Status().Update() -> Event -> Reconcile -> r.Status().Update() -> ...`

Решение: **Предикаты событий (Event Predicates)**
Предикаты (`predicate.Predicate`) фильтруют события ДО их добавления в очередь `workqueue`:
- **`GenerationChangedPredicate`:** Пропускает событие `Update`, только если `oldObject.GetGeneration() != newObject.GetGeneration()`. Поле `Generation` увеличивается только при изменении блока `.spec`. Обновления `.status`, annotations и labels отсекаются на уровне кэша!
- **Кастомные предикаты (`predicate.Funcs`):** Позволяют фильтровать события по конкретным меткам (`labels`), пространству имен или статусу готовности подов.""",
    "step_by_step": [
        "Определите интерфейс предиката `EventPredicate` с методами фильтрации Create, Update, Delete.",
        "Реализуйте структуру `GenerationChangedPredicate`, сравнивающую поколения объектов.",
        "Создайте имитатор очереди событий, отсекающий события с неизменным Generation.",
        "Продемонстрируйте пропуск обновления статуса и срабатывание примирения при изменении спецификации."
    ],
    "code_blocks": [
        {
            "filename": "predicate_generation_filter.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
)

type ObjectMetadata struct {
	Name            string
	ResourceVersion int
	Generation      int64
}

type UpdateEvent struct {
	OldMeta ObjectMetadata
	NewMeta ObjectMetadata
}

type GenerationChangedPredicate struct{}

func (p GenerationChangedPredicate) Update(e UpdateEvent) bool {
	if e.OldMeta.Generation != e.NewMeta.Generation {
		return true
	}
	return false
}

func main() {
	predicate := GenerationChangedPredicate{}

	fmt.Println("=== KUBERNETES EVENT PREDICATE TEST ===")

	// Сценарий 1: Обновление только статуса (Generation не изменился)
	statusUpdate := UpdateEvent{
		OldMeta: ObjectMetadata{Name: "postgres-cluster", ResourceVersion: 100, Generation: 1},
		NewMeta: ObjectMetadata{Name: "postgres-cluster", ResourceVersion: 101, Generation: 1},
	}
	shouldReconcile1 := predicate.Update(statusUpdate)
	fmt.Printf("Status update (RV 100 -> 101, Gen=1): Enqueue Reconcile? -> %v (Filtered!)\n", shouldReconcile1)

	// Сценарий 2: Пользователь изменил Spec (Generation увеличился)
	specUpdate := UpdateEvent{
		OldMeta: ObjectMetadata{Name: "postgres-cluster", ResourceVersion: 101, Generation: 1},
		NewMeta: ObjectMetadata{Name: "postgres-cluster", ResourceVersion: 102, Generation: 2},
	}
	shouldReconcile2 := predicate.Update(specUpdate)
	fmt.Printf("Spec update   (RV 101 -> 102, Gen 1 -> 2): Enqueue Reconcile? -> %v (Allowed!)\n", shouldReconcile2)
}
"""
        }
    ],
    "under_the_hood": "Механизм предикатов в `controller-runtime` выполняется непосредственно в горутине обработчика событий информера (`ResourceEventHandler`). Если предикат возвращает `false`, ключ объекта даже не попадает в очередь `workqueue`, что экономит такты процессора и память под очереди.",
    "pitfalls": [
        "Использование `GenerationChangedPredicate` на дочерних ресурсах (например Pod или Service): у стандартных подов поле `Generation` не поддерживается API-сервером (всегда равно 0). Для дочерних ресурсов необходимо использовать кастомные предикаты проверки фазы или готовности.",
        "Случайная фильтрация событий удаления (`DeleteFunc`): если предикат отклонит событие удаления, контроллер не сможет запустить процедуру очистки."
    ],
    "bigtech_interview": "Почему использование GenerationChangedPredicate критично для предотвращения Hot Loops в операторах? При обновлении статуса кастомного ресурса контроллер вызывает API, что генерирует событие Update. Без фильтрации по Generation это событие снова попадет в очередь, снова вызовет Reconcile, который снова обновит статус. `GenerationChangedPredicate` прерывает этот бесконечный цикл, так как API-сервер увеличивает Generation только при изменении желаемой спецификации `.spec`."
})

# Ex 12
exercises.append({
    "num": 12,
    "title": "Связывание ресурсов через OwnerReferences (Сборка мусора K8s)",
    "task": "При создании дочерних ресурсов (StatefulSet, Service, ConfigMap) привяжите их к родительскому объекту с помощью функции `ctrl.SetControllerReference(instance, childObj, r.Scheme)`. Докажите, что при удалении родительского ресурса `DatabaseCluster` Kubernetes автоматически удалит все дочерние поды и сервисы по механизму каскадной сборки мусора (Garbage Collection).",
    "theory": r"""Когда оператор создает дочерние ресурсы (ConfigMap, Secret, Service, StatefulSet), возникает критический вопрос управления их жизненным циклом:
Что произойдет с этими ресурсами, если пользователь выполнит команду `kubectl delete databasecluster my-cluster`?
Без специальной настройки дочерние ресурсы останутся «висеть» в кластере в виде зомби (ресурсная утечка).

Решение: **Механизм OwnerReferences и Garbage Collector (GC)**
Каждый дочерний объект в секции `metadata.ownerReferences` содержит ссылку на родительский ресурс:
```yaml
ownerReferences:
  - apiVersion: storage.mycompany.com/v1alpha1
    kind: DatabaseCluster
    name: pg-analytics
    uid: 4a2b3c4d-...
    controller: true
    blockOwnerDeletion: true
```
Функция `controllerutil.SetControllerReference(owner, controlled, scheme)`:
1. Заполняет поля GVK, Name и UID владельца.
2. Устанавливает флаг `controller: true` (у объекта может быть много owners, но ровно один controller-owner).
3. При удалении владельца фоновый сборщик мусора Kubernetes (**Kube-Garbage-Collector**) автоматически выполняет каскадное удаление всех зависимых дочерних объектов.""",
    "step_by_step": [
        "Определите структуру `OwnerReference` с полями APIVersion, Kind, Name, UID и флагом Controller.",
        "Реализуйте функцию `SetControllerReference` с проверкой конфликта контроллеров.",
        "Смоделируйте каскадную сборку мусора дочерних ресурсов при удалении родительского объекта.",
        "Продемонстрируйте защиту от перезаписи существующего контроллера-владельца."
    ],
    "code_blocks": [
        {
            "filename": "owner_references_gc.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
)

type OwnerReference struct {
	APIVersion         string
	Kind               string
	Name               string
	UID                string
	Controller         bool
	BlockOwnerDeletion bool
}

type K8sResource struct {
	Name            string
	Namespace       string
	UID             string
	OwnerReferences []OwnerReference
}

func SetControllerReference(owner, child *K8sResource, apiVersion, kind string) error {
	for _, ref := range child.OwnerReferences {
		if ref.Controller {
			return fmt.Errorf("child resource %s already has a controller owner: %s", child.Name, ref.Name)
		}
	}

	child.OwnerReferences = append(child.OwnerReferences, OwnerReference{
		APIVersion:         apiVersion,
		Kind:               kind,
		Name:               owner.Name,
		UID:                owner.UID,
		Controller:         true,
		BlockOwnerDeletion: true,
	})
	return nil
}

func main() {
	parentCluster := &K8sResource{
		Name:      "postgres-primary",
		Namespace: "databases",
		UID:       "uid-parent-9988-aabb",
	}

	childService := &K8sResource{
		Name:      "postgres-primary-svc",
		Namespace: "databases",
		UID:       "uid-child-1122-ccdd",
	}

	err := SetControllerReference(parentCluster, childService, "storage.mycompany.com/v1alpha1", "DatabaseCluster")
	if err != nil {
		panic(err)
	}

	fmt.Println("=== KUBERNETES OWNER REFERENCES GC TEST ===")
	fmt.Printf("Child: %s\n", childService.Name)
	for i, ref := range childService.OwnerReferences {
		fmt.Printf(" OwnerRef [%d]: Kind=%s, Name=%s, UID=%s, Controller=%v\n",
			i+1, ref.Kind, ref.Name, ref.UID, ref.Controller)
	}

	// Попытка привязать второго контроллера вызовет ошибку
	anotherParent := &K8sResource{Name: "rogue-parent", UID: "uid-rogue"}
	err = SetControllerReference(anotherParent, childService, "storage.mycompany.com/v1alpha1", "DatabaseCluster")
	fmt.Printf("Second controller reference attempt error: %v\n", err)
}
"""
        }
    ],
    "under_the_hood": "Сборщик мусора Kubernetes работает в двух режимах: **Foreground Deletion** (родитель переводится в состояние удаления с финализатором `foregroundDeletion`, пока все дочерние объекты не будут удалены) и **Background Deletion** (родитель удаляется мгновенно, а дочерние ресурсы удаляются асинхронно в фоне).",
    "pitfalls": [
        "Попытка установить `OwnerReference` между объектами из разных пространств имен (Cross-Namespace Owner): Kubernetes запрещает межпространственные ссылки владельцев для изоляции безопасности (за исключением ресурсов уровня кластера).",
        "Создание дочерних ресурсов без `OwnerReference`: при удалении кастомного ресурса в кластере останутся «осиротевшие» поды и сервисы (Orphaned Resources)."
    ],
    "bigtech_interview": "Что такое флаг blockOwnerDeletion в OwnerReference и зачем он нужен? Флаг `blockOwnerDeletion: true` сообщает сборщику мусора Kubernetes, что родительский ресурс не должен физически удаляться из etcd до тех пор, пока данный дочерний ресурс не будет гарантированно завершен и удален. Это защищает от ситуаций, когда кастомный ресурс исчез, а его база данных продолжает писать на диск в полуудаленном состоянии."
})

# Ex 13
exercises.append({
    "num": 13,
    "title": "Паттерн Status Conditions для отображения состояния",
    "task": "Реализуйте стандартное отображение статуса через срез условий `metav1.Condition`: типы условий `Available`, `Progressing`, `Degraded`. Используйте вспомогательный пакет `k8s.io/apimachinery/pkg/api/meta` и функцию `meta.SetStatusCondition(&instance.Status.Conditions, newCondition)` для безопасного обновления статусов.",
    "theory": r"""Исторически разные контроллеры Kubernetes изобретали собственные форматы статусов (`Phase: string`, числовые флаги, списки ошибок), что делало невозможным построение унифицированных дашбордов и мониторинга.

Современный стандарт Kubernetes API (KEP-1623): **`metav1.Condition`**
Каждое условие описывает текущее состояние определенного аспекта системы:
```go
type Condition struct {
    Type               string          // Название аспекта: "Ready", "Progressing", "Degraded"
    Status             ConditionStatus // "True", "False", "Unknown"
    ObservedGeneration int64           // Поколение спецификации, для которого вычислено условие
    LastTransitionTime metav1.Time     // Время последнего изменения Status
    Reason             string          // Машинно-читаемая причина в UpperCamelCase: "QuorumLost"
    Message            string          // Человеко-читаемое подробное описание
}
```
Функция `meta.SetStatusCondition`:
- Добавляет условие, если его не было.
- Если условие существует и его `Status` не изменился — сохраняет исходный `LastTransitionTime`!
- Если `Status` изменился — атомарно обновляет время перехода `LastTransitionTime` на `time.Now()`.""",
    "step_by_step": [
        "Определите тип `Condition` и статусы `ConditionTrue`, `ConditionFalse`.",
        "Реализуйте идиоматичную функцию `SetStatusCondition` с сохранением `LastTransitionTime` при неизменном статусе.",
        "Создайте структуру `Status` со срезом условий.",
        "Продемонстрируйте обновление условий при сбое репликации и восстановлении здоровья."
    ],
    "code_blocks": [
        {
            "filename": "status_conditions_pattern.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"time"
)

type ConditionStatus string

const (
	ConditionTrue    ConditionStatus = "True"
	ConditionFalse   ConditionStatus = "False"
	ConditionUnknown ConditionStatus = "Unknown"
)

type Condition struct {
	Type               string
	Status             ConditionStatus
	ObservedGeneration int64
	LastTransitionTime time.Time
	Reason             string
	Message            string
}

func SetStatusCondition(conditions *[]Condition, newCond Condition) {
	if conditions == nil {
		return
	}

	for i, existing := range *conditions {
		if existing.Type == newCond.Type {
			if existing.Status != newCond.Status {
				existing.Status = newCond.Status
				existing.LastTransitionTime = newCond.LastTransitionTime
			}
			existing.Reason = newCond.Reason
			existing.Message = newCond.Message
			existing.ObservedGeneration = newCond.ObservedGeneration
			(*conditions)[i] = existing
			return
		}
	}

	*conditions = append(*conditions, newCond)
}

func main() {
	var conditions []Condition
	now := time.Now().UTC()

	// 1. Установка условия Ready=False (старт развертывания)
	SetStatusCondition(&conditions, Condition{
		Type:               "Ready",
		Status:             ConditionFalse,
		ObservedGeneration: 1,
		LastTransitionTime: now,
		Reason:             "ProvisioningPods",
		Message:            "Waiting for replica pods to report healthy status",
	})

	fmt.Println("=== KUBERNETES STATUS CONDITIONS ===")
	fmt.Printf("Condition 1: Type=%s, Status=%s, Reason=%s, Time=%s\n",
		conditions[0].Type, conditions[0].Status, conditions[0].Reason, conditions[0].LastTransitionTime.Format(time.Kitchen))

	// 2. Повторная установка с тем же статусом (время LastTransitionTime НЕ должно измениться!)
	later := now.Add(2 * time.Minute)
	SetStatusCondition(&conditions, Condition{
		Type:               "Ready",
		Status:             ConditionFalse,
		ObservedGeneration: 1,
		LastTransitionTime: later,
		Reason:             "StillProvisioning",
		Message:            "2 of 3 replicas ready",
	})
	fmt.Printf("Condition 2: Type=%s, Status=%s, Reason=%s, Time=%s (Unchanged transition!)\n",
		conditions[0].Type, conditions[0].Status, conditions[0].Reason, conditions[0].LastTransitionTime.Format(time.Kitchen))

	// 3. Кластер готов: Ready=True (время LastTransitionTime обязано обновиться!)
	readyTime := now.Add(5 * time.Minute)
	SetStatusCondition(&conditions, Condition{
		Type:               "Ready",
		Status:             ConditionTrue,
		ObservedGeneration: 1,
		LastTransitionTime: readyTime,
		Reason:             "AllReplicasSynchronized",
		Message:            "Database cluster is fully available",
	})
	fmt.Printf("Condition 3: Type=%s, Status=%s, Reason=%s, Time=%s (Transition updated!)\n",
		conditions[0].Type, conditions[0].Status, conditions[0].Reason, conditions[0].LastTransitionTime.Format(time.Kitchen))
}
"""
        }
    ],
    "under_the_hood": "Поле `ObservedGeneration` в `Condition` критично для GitOps и CLI утилит (например `kubectl wait`). Утилита `kubectl wait --for=condition=Ready databasecluster/pg` проверяет не только `Status == True`, но и `ObservedGeneration == metadata.generation`, гарантируя, что статус относится именно к текущей примененной спецификации, а не к предыдущей версии до реконфигурации.",
    "pitfalls": [
        "Обновление `LastTransitionTime` на каждый Reconcile, даже если `Status` не изменился: это ломает мониторинг длительности нахождения ресурса в определенном состоянии.",
        "Использование свободных нестандартизированных названий типов условий: рекомендуется использовать общепринятые `Ready`, `Progressing`, `Degraded`, `Reconciling`."
    ],
    "bigtech_interview": "Зачем в структуре Condition присутствует поле ObservedGeneration? Когда пользователь обновляет `.spec` (Generation увеличивается с 1 до 2), контроллер может начать примирение с задержкой в несколько секунд. Если внешняя система проверит статус до завершения Reconcile, она увидит `Ready=True`, относящийся к Generation 1! Поле `ObservedGeneration: 1` показывает, что условие рассчитано для старой версии спецификации и еще не актуализировано для версии 2."
})

# Ex 14
exercises.append({
    "num": 14,
    "title": "Атомарное обновление статуса через Subresource Status",
    "task": "Для обновления секции `status` используйте специальный интерфейс клиента: `r.Status().Update(ctx, instance)` или `r.Status().Patch(ctx, instance, client.MergeFrom(oldInstance))`. Объясните, почему обновление через `r.Update()` является антипаттерном и может перезаписать параллельные правки спецификации пользователем.",
    "theory": r"""Почему в Kubernetes категорически запрещено обновлять статус через стандартный `r.Client.Update(ctx, instance)`?
1. **Гонка спецификации (Spec Overwrite Race Condition):**
   - Контроллер считывает ресурс со `spec.replicas = 3`.
   - В процессе работы Reconcile пользователь выполняет `kubectl edit` и меняет `spec.replicas = 5`.
   - В конце цикла контроллер вызывает `r.Update(ctx, instance)`, отправляя весь объект целиком.
   - **Катастрофа:** правка пользователя затирается старым значением `replicas = 3`!
2. **Ограничение прав RBAC:**
   - В production-окружениях ServiceAccount оператора наделяется правами на запись только в подресурс `databaseclusters/status`. Вызов `r.Update()` завершится ошибкой `403 Forbidden`.

Решение: **`r.Status().Update()` или `r.Status().Patch()`**
API-сервер при обращении к эндпоинту `/status` обновляет **только блок `.status`**, полностью игнорируя любые изменения в блоках `.spec` и `.metadata`.""",
    "step_by_step": [
        "Определите интерфейс клиента с раздельными методами `Update` и `Status().Update`.",
        "Реализуйте симулятор API-сервера, защищающий блок `spec` при обновлении через `/status`.",
        "Смоделируйте параллельное изменение спецификации пользователем во время работы контроллера.",
        "Докажите, что `r.Status().Update` сохраняет изменения пользователя в целостности."
    ],
    "code_blocks": [
        {
            "filename": "status_subresource_update.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
)

type Resource struct {
	Name     string
	Replicas int    // Spec
	Phase    string // Status
}

type APIServerSimulator struct {
	stored Resource
}

func (s *APIServerSimulator) UnsafeFullUpdate(in Resource) {
	// Антипаттерн: перезаписывает и Spec, и Status
	s.stored = in
}

func (s *APIServerSimulator) SafeStatusUpdate(in Resource) {
	// Идиоматичный K8s Subresource: обновляет только Status!
	s.stored.Phase = in.Phase
}

func main() {
	server := &APIServerSimulator{
		stored: Resource{Name: "redis", Replicas: 3, Phase: "Pending"},
	}

	// Контроллер прочитал состояние: Replicas=3, Phase=Pending
	controllerSnapshot := server.stored

	// 1. В этот момент ПОЛЬЗОВАТЕЛЬ параллельно масштабирует кластер: Replicas=10
	server.stored.Replicas = 10
	fmt.Printf("[User Action] Scaled cluster to %d replicas\n", server.stored.Replicas)

	// 2. Контроллер завершил проверки и обновляет статус на "Running"
	controllerSnapshot.Phase = "Running"

	// Тест безопасного обновления через Subresource
	server.SafeStatusUpdate(controllerSnapshot)
	fmt.Println("=== SAFE STATUS SUBRESOURCE UPDATE ===")
	fmt.Printf("Resulting State: Replicas=%d (User changes PRESERVED!), Phase=%s\n",
		server.stored.Replicas, server.stored.Phase)
}
"""
        }
    ],
    "under_the_hood": "При использовании `r.Status().Patch(ctx, instance, client.MergeFrom(oldInstance))` контроллер генерирует минимальный JSON Merge Patch (например `{\"status\":{\"phase\":\"Running\"}}`), что снижает сетевой трафик и минимизирует вероятность конфликтов версий в etcd.",
    "pitfalls": [
        "Забытый маркер `// +kubebuilder:subresource:status` в файле типов: без этого маркера API-сервер не создает эндпоинт `/status`, и вызов `r.Status().Update()` завершится ошибкой 404 NotFound.",
        "Мутация спецификации перед вызовом `r.Status().Update()` в надежде применить ее: изменения в `.spec` будут молча проигнорированы сервером."
    ],
    "bigtech_interview": "В чем фундаментальная разница между client.Update и client.Patch при обновлении ресурсов в Kubernetes? `client.Update` отправляет весь объект целиком (HTTP PUT) и требует точного совпадения `ResourceVersion`. При малейшем несовпадении возвращается `409 Conflict`. `client.Patch` отправляет только дельту изменений (HTTP PATCH), что предотвращает затирание параллельных изменений других контроллеров и существенно повышает надежность системы при конкурентном доступе."
})

# Ex 15
exercises.append({
    "num": 15,
    "title": "Использование Финализаторов (Finalizers) для очистки внешних ресурсов",
    "task": "Если перед удалением базы данных необходимо создать финальный снапшот в облачном хранилище S3 или освободить внешний DNS-адрес, Kubernetes не должен удалять объект немедленно. Добавьте финализатор `database.mycompany.com/finalizer` через `controllerutil.AddFinalizer`. Реализуйте перехват удаления (`!instance.DeletionTimestamp.IsZero()`), выполнение очистки и снятие финализатора.",
    "theory": r"""По умолчанию удаление объекта в Kubernetes (`kubectl delete`) приводит к его немедленному стиранию из etcd.
Однако если ресурс управляет **внешней инфраструктурой** (бакеты S3, записи AWS Route53, тома EBS, внешние балансировщики), контроллер не успеет их удалить и ресурсы продолжат тарифицироваться в облаке.

Механизм **Finalizers (Финализаторы)**:
1. **Регистрация:** При первом создании ресурса контроллер добавляет строковый ключ в срез `metadata.finalizers` (например `storage.mycompany.com/finalizer`) через `controllerutil.AddFinalizer`.
2. **Блокировка удаления:** Когда пользователь вызывает `kubectl delete`:
   - API-сервер **НЕ удаляет** объект из etcd.
   - API-сервер выставляет поле `metadata.deletionTimestamp` (объект переходит в состояние `Terminating`).
3. **Перехват контроллером:**
   - В Reconcile проверяется условие: `if !instance.GetDeletionTimestamp().IsZero()`.
   - Контроллер выполняет процедуру очистки внешней инфраструктуры (создание финального бэкапа, удаление LUN на СХД).
4. **Снятие блокировки:**
   - Контроллер вызывает `controllerutil.RemoveFinalizer` и сохраняет объект.
   - Список `finalizers` становится пустым, и Kubernetes мгновенно стирает объект из etcd.""",
    "step_by_step": [
        "Определите структуру `K8sObject` с полями `Finalizers` и `DeletionTimestamp`.",
        "Реализуйте методы добавления и снятия финализатора.",
        "Запрограммируйте логику жизненного цикла: регистрация при создании, перехват при удалении, вызов внешней очистки.",
        "Продемонстрируйте безопасное удаление внешних ресурсов до стирания объекта."
    ],
    "code_blocks": [
        {
            "filename": "finalizers_external_cleanup.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"time"
)

const ClusterFinalizer = "storage.mycompany.com/backup-and-cleanup"

type ManagedCluster struct {
	Name              string
	Finalizers        []string
	DeletionTimestamp *time.Time
}

func (c *ManagedCluster) HasFinalizer(finalizer string) bool {
	for _, f := range c.Finalizers {
		if f == finalizer {
			return true
		}
	}
	return false
}

func (c *ManagedCluster) AddFinalizer(finalizer string) {
	if !c.HasFinalizer(finalizer) {
		c.Finalizers = append(c.Finalizers, finalizer)
	}
}

func (c *ManagedCluster) RemoveFinalizer(finalizer string) {
	var result []string
	for _, f := range c.Finalizers {
		if f != finalizer {
			result = append(result, f)
		}
	}
	c.Finalizers = result
}

func ExternalStorageCleanup(clusterName string) error {
	fmt.Printf("[EXTERNAL S3] Creating final backup snapshot for '%s'...\n", clusterName)
	fmt.Printf("[EXTERNAL DNS] Releasing public IP and DNS routes for '%s'...\n", clusterName)
	return nil
}

func ReconcileCluster(cluster *ManagedCluster) {
	// 1. Проверяем, находится ли объект в процессе удаления
	if cluster.DeletionTimestamp != nil {
		if cluster.HasFinalizer(ClusterFinalizer) {
			fmt.Println("[FINALIZER] Intercepted deletion! Performing external teardown...")
			_ = ExternalStorageCleanup(cluster.Name)

			// Снимаем финализатор
			cluster.RemoveFinalizer(ClusterFinalizer)
			fmt.Println("[FINALIZER] Cleanup completed. Finalizer removed. Object is now deleted from etcd.")
		}
		return
	}

	// 2. Обычный запуск: гарантируем наличие финализатора
	if !cluster.HasFinalizer(ClusterFinalizer) {
		cluster.AddFinalizer(ClusterFinalizer)
		fmt.Printf("[FINALIZER] Registered finalizer '%s' on resource '%s'\n", ClusterFinalizer, cluster.Name)
	}
}

func main() {
	cluster := &ManagedCluster{Name: "production-pg"}

	fmt.Println("=== KUBERNETES FINALIZERS LIFECYCLE TEST ===")

	// Шаг 1: Создание ресурса
	ReconcileCluster(cluster)
	fmt.Printf("State after create: Finalizers=%v\n\n", cluster.Finalizers)

	// Шаг 2: Пользователь удаляет ресурс (K8s выставляет DeletionTimestamp)
	now := time.Now()
	cluster.DeletionTimestamp = &now

	// Шаг 3: Контроллер обрабатывает удаление
	ReconcileCluster(cluster)
	fmt.Printf("State after cleanup: Finalizers=%v (Object safely erased!)\n", cluster.Finalizers)
}
"""
        }
    ],
    "under_the_hood": "Если внешний сервис (например AWS S3 API) временно недоступен во время очистки финализатора, метод Reconcile возвращает ошибку `return ctrl.Result{}, err`. Kubernetes не снимет финализатор, ресурс останется в статусе `Terminating`, а контроллер будет повторять попытки очистки, гарантируя нулевую потерю данных и отсутствие оставленных ресурсов.",
    "pitfalls": [
        "Зависание объекта в статусе `Terminating` навсегда: если контроллер содержит баг и паникует в блоке очистки финализатора, объект невозможно удалить даже с флагом `--force` без ручного редактирования `finalizers: []` через `kubectl edit`.",
        "Вызов `RemoveFinalizer` до успешного завершения очистки: при падении оператора в середине операции внешние ресурсы останутся недоудаленными."
    ],
    "bigtech_interview": "Что происходит на уровне etcd, когда пользователь выполняет kubectl delete над объектом с финализатором? API-сервер не стирает ключ из etcd. Вместо этого он производит атомарную операцию обновления: выставляет поле `metadata.deletionTimestamp = time.Now()`, опционально устанавливает `metadata.deletionGracePeriodSeconds` и сохраняет объект. Физическое удаление ключа из etcd происходит только тогда, когда срез `metadata.finalizers` станет пустым `[]`."
})

# Ex 16
exercises.append({
    "num": 16,
    "title": "Стратегии возврата из Reconcile Loop",
    "task": "Изучите сценарии управления повтором: `return ctrl.Result{}, nil` (успех, ждать следующих изменений); `return ctrl.Result{Requeue: true}, nil` (немедленный повтор цикла); `return ctrl.Result{RequeueAfter: 30 * time.Second}, nil` (периодический опрос здоровья ресурса); `return ctrl.Result{}, err` (ошибка с экспоненциальным backoff рантайма).",
    "theory": r"""Возвращаемые значения метода `Reconcile` управляют планировщиком очереди `workqueue`:

1. **`return ctrl.Result{}, nil` (Успех):**
   - Состояние системы полностью синхронизировано.
   - Ключ удаляется из очереди.
   - Следующий вызов произойдет только при возникновении внешнего события (изменение Spec, падение Pod) или по истечении глобального интервала ресинхронизации (Resync Period).
2. **`return ctrl.Result{Requeue: true}, nil` (Немедленный повтор):**
   - Контроллер выполнил промежуточный шаг (например, создал Secret) и хочет немедленно продолжить следующий этап без ожидания события информера.
3. **`return ctrl.Result{RequeueAfter: 30 * time.Second}, nil` (Периодический опрос / Polling):**
   - Используется для мониторинга внешних систем (проверка статуса репликации в БД, опрос готовности облачного снапшота, ротация сертификатов раз в сутки).
4. **`return ctrl.Result{}, err` (Ошибка с Exponential Backoff):**
   - Системный сбой (сеть, недоступность API-сервера).
   - Очередь `workqueue` автоматически применяет экспоненциальную задержку повторов (например 5ms -> 10ms -> 20ms ... до 1000s) для предотвращения лавинообразной перегрузки.""",
    "step_by_step": [
        "Определите типы управляющих сигналов возврата из Reconcile.",
        "Реализуйте контроллер конечного автомата (State Machine) кластера.",
        "Смоделируйте переход состояний: Инициализация -> Ожидание готовности подов (`RequeueAfter`) -> Готовность.",
        "Продемонстрируйте разницу в поведении очереди при ошибках и плановых повторах."
    ],
    "code_blocks": [
        {
            "filename": "reconcile_return_strategies.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"time"
)

type Result struct {
	Requeue      bool
	RequeueAfter time.Duration
}

type ClusterState string

const (
	StateInit         ClusterState = "INIT"
	StateWaitingPods  ClusterState = "WAITING_PODS"
	StateRunning      ClusterState = "RUNNING"
	StateNetworkError ClusterState = "NETWORK_ERROR"
)

func StepReconcile(state ClusterState) (Result, error) {
	switch state {
	case StateInit:
		fmt.Println("[Reconcile] Creating child service and config... Need immediate next step.")
		return Result{Requeue: true}, nil

	case StateWaitingPods:
		fmt.Println("[Reconcile] Pods are starting up. Polling status in 10 seconds...")
		return Result{RequeueAfter: 10 * time.Second}, nil

	case StateRunning:
		fmt.Println("[Reconcile] Cluster is healthy and stable. Going to sleep.")
		return Result{}, nil

	case StateNetworkError:
		fmt.Println("[Reconcile] API Server timeout! Triggering exponential backoff.")
		return Result{}, fmt.Errorf("connection refused by kube-apiserver")

	default:
		return Result{}, nil
	}
}

func main() {
	fmt.Println("=== KUBERNETES RECONCILE RETURN STRATEGIES ===")

	r1, err1 := StepReconcile(StateInit)
	fmt.Printf("StateInit:         Requeue=%v, RequeueAfter=%v, Err=%v\n\n", r1.Requeue, r1.RequeueAfter, err1)

	r2, err2 := StepReconcile(StateWaitingPods)
	fmt.Printf("StateWaitingPods:  Requeue=%v, RequeueAfter=%v, Err=%v\n\n", r2.Requeue, r2.RequeueAfter, err2)

	r3, err3 := StepReconcile(StateRunning)
	fmt.Printf("StateRunning:      Requeue=%v, RequeueAfter=%v, Err=%v\n\n", r3.Requeue, r3.RequeueAfter, err3)

	r4, err4 := StepReconcile(StateNetworkError)
	fmt.Printf("StateNetworkError: Requeue=%v, RequeueAfter=%v, Err=%v\n", r4.Requeue, r4.RequeueAfter, err4)
}
"""
        }
    ],
    "under_the_hood": "Внутри `controller-runtime` возвращение одновременно ненулевого `RequeueAfter` и ошибки `err != nil` является логической ошибкой: если возвращен `err`, контроллер полностью игнорирует значение `RequeueAfter` и применяет стандартный `RateLimiter` очереди с экспоненциальным backoff.",
    "pitfalls": [
        "Использование `return ctrl.Result{Requeue: true}, err`: избыточно, так как любая возвращенная ошибка `err != nil` уже неявно инициирует повтор очереди.",
        "Слишком частый опрос через `RequeueAfter: 100 * time.Millisecond`: приводит к перегрузке CPU оператора и росту логов."
    ],
    "bigtech_interview": "Почему возвращение Result{Requeue: true} следует использовать с осторожностью? `Requeue: true` возвращает ключ в начало очереди без экспоненциальной задержки. Если внешнее условие (например ожидание готовности диска) не изменилось, контроллер войдет в режим активного ожидания (Busy Loop), сжигая 100% CPU ядра ноды. Для периодических проверок внешних условий всегда следует использовать `RequeueAfter` с разумным интервалом (от 5 до 30 секунд)."
})

# Ex 17
exercises.append({
    "num": 17,
    "title": "Управление параллелизмом контроллера (Concurrent Reconciles)",
    "task": "По умолчанию контроллер обрабатывает события строго последовательно в один поток. Настройте пул параллельных воркеров в `controller.Options{MaxConcurrentReconciles: 5}`. Убедитесь, что логика примирения не содержит гонок данных и корректно работает при параллельной обработке событий разных ресурсов.",
    "theory": r"""По умолчанию контроллер в Kubebuilder запускает ровно **один воркер** (`MaxConcurrentReconciles: 1`).
Если в кластере создано 1000 пользовательских баз данных, а примирение одной базы занимает 2 секунды (проверка бэкапов, сетевые вызовы), обработка очереди займет более 30 минут!

Параллелизация обработки (**Concurrent Reconciles**):
В настройках контроллера задается параметр:
```go
controller.Options{
    MaxConcurrentReconciles: 10,
}
```
Гарантии очереди `workqueue` при параллельной обработке:
1. **Строгая изоляция одного ресурса:** Очередь гарантирует, что события для **одного и того же ключа `Namespace/Name` НИКОГДА не будут обрабатываться параллельно двумя воркерами**. Если воркер #1 обрабатывает `default/db-1`, а для `default/db-1` пришло новое событие, оно ожидает завершения воркера #1.
2. **Параллелизм разных ресурсов:** События для `default/db-1` и `prod/db-2` обрабатываются полностью параллельно в независимых горутинах.
3. **Требование к коду:** Структура контроллера не должна иметь несинхронизированного общего состояния (shared state) между вызовами Reconcile.""",
    "step_by_step": [
        "Смоделируйте очередь с блокировкой ключей (Key-Level In-Flight Lock).",
        "Создайте пул воркеров с лимитом параллелизма `MaxConcurrentReconciles`.",
        "Продемонстрируйте параллельное выполнение примирения для разных ресурсов.",
        "Докажите, что один и тот же ресурс никогда не примиряется двумя воркерами одновременно."
    ],
    "code_blocks": [
        {
            "filename": "concurrent_reconciles_pool.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

type WorkQueue struct {
	mu         sync.Mutex
	inFlight   map[string]bool
	items      []string
	cond       *sync.Cond
	activeJobs int32
}

func NewWorkQueue() *WorkQueue {
	q := &WorkQueue{
		inFlight: make(map[string]bool),
	}
	q.cond = sync.NewCond(&q.mu)
	return q
}

func (q *WorkQueue) Add(key string) {
	q.mu.Lock()
	defer q.mu.Unlock()
	q.items = append(q.items, key)
	q.cond.Signal()
}

func (q *WorkQueue) Get() string {
	q.mu.Lock()
	defer q.mu.Unlock()

	for {
		for i, item := range q.items {
			if !q.inFlight[item] {
				q.inFlight[item] = true
				q.items = append(q.items[:i], q.items[i+1:]...)
				atomic.AddInt32(&q.activeJobs, 1)
				return item
			}
		}
		q.cond.Wait()
	}
}

func (q *WorkQueue) Done(key string) {
	q.mu.Lock()
	defer q.mu.Unlock()
	delete(q.inFlight, key)
	atomic.AddInt32(&q.activeJobs, -1)
	q.cond.Broadcast()
}

func main() {
	queue := NewWorkQueue()
	maxWorkers := 3
	var wg sync.WaitGroup

	fmt.Println("=== CONCURRENT RECONCILES SIMULATOR ===")

	// Запуск пула воркеров
	for w := 1; w <= maxWorkers; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for i := 0; i < 2; i++ {
				key := queue.Get()
				fmt.Printf("[Worker %d] START Reconcile for: %s (Active Jobs: %d)\n",
					workerID, key, atomic.LoadInt32(&queue.activeJobs))
				time.Sleep(50 * time.Millisecond)
				fmt.Printf("[Worker %d] DONE  Reconcile for: %s\n", workerID, key)
				queue.Done(key)
			}
		}(w)
	}

	// Добавляем задачи: 4 разных ресурса и 2 дубликата
	queue.Add("prod/pg-cluster-1")
	queue.Add("prod/pg-cluster-2")
	queue.Add("prod/pg-cluster-3")
	queue.Add("prod/pg-cluster-1") // Дубликат: должен ждать завершения первого!
	queue.Add("stage/redis-1")
	queue.Add("stage/redis-2")

	wg.Wait()
	fmt.Println("All concurrent reconcile jobs completed safely.")
}
"""
        }
    ],
    "under_the_hood": "Внутренняя реализация очереди `client-go/util/workqueue` отслеживает множество `processing: map[any]empty`. Если ключ извлекается методом `Get()`, он помечается как занятый. Любые последующие поступления этого ключа складываются в очередь `dirty: map[any]empty` и выдаются воркерам ТОЛЬКО после вызова `Done(key)` предыдущим воркером, исключая гонки данных на уровне ресурса.",
    "pitfalls": [
        "Использование глобальных несинхронизированных переменных или не-thread-safe кэшей внутри структуры контроллера при `MaxConcurrentReconciles > 1`.",
        "Выставление слишком высокого числа воркеров (например 100): приводит к исчерпанию пула HTTP/2 соединений к API-серверу и CPU Throttling в Kubernetes."
    ],
    "bigtech_interview": "Могут ли два воркера контроллера в Kubernetes параллельно выполнять Reconcile для одного и того же объекта кастомного ресурса? Нет! Очередь `workqueue` в client-go гарантирует атомарную изоляцию ключа: пока один воркер обрабатывает `Namespace/Name`, этот ключ заблокирован в наборе `processing`. Новые события для этого же ресурса аккумулируются и будут переданы на обработку только после того, как первый воркер вызовет `Done()`. Параллельно обрабатываются только события РАЗНЫХ ресурсов."
})

# Ex 18
exercises.append({
    "num": 18,
    "title": "Валидационные вебхуки (Validating Admission Webhooks)",
    "task": "Некоторые правила невозможно выразить стандартной схемой OpenAPI (например, проверка: «число реплик должно быть нечетным числом для кворума»). Сгенерируйте вебхук с помощью `kubebuilder create webhook --group storage --version v1alpha1 --kind DatabaseCluster --defaulting --programmatic-validation`. Реализуйте интерфейс `webhook.CustomValidator` и метод `ValidateCreate`.",
    "theory": r"""Хотя валидация OpenAPI v3 покрывает большинство базовых ограничений (диапазоны чисел, регулярные выражения строк), сложные бизнес-правила требуют программной проверки на Go:
- Проверка кворума: число узлов должно быть нечетным (1, 3, 5).
- Запрет уменьшения размера постоянного дискового тома (`Volume缩小` запрещено в облачных провайдерах).
- Проверка доступности указанной версии СУБД в корпоративном реестре образов.

**Validating Admission Webhook:**
1. При выполнении `kubectl apply` запрос попадает в API-сервер.
2. API-сервер отправляет HTTPS POST запрос `AdmissionReview` на вебхук оператора.
3. Метод `ValidateCreate` или `ValidateUpdate` анализирует объект.
4. Если правило нарушено — вебхук возвращает `admission.Denied("reason")`.
5. API-сервер **отклоняет запрос пользователя**, и невалидный объект даже не сохраняется в etcd!""",
    "step_by_step": [
        "Определите интерфейс валидатора `CustomValidator` с методами `ValidateCreate` и `ValidateUpdate`.",
        "Реализуйте валидацию инварианта: число реплик распределенной СУБД должно быть строго нечетным.",
        "Реализуйте валидацию неизменяемости поля: запрет изменения типа движка СУБД при обновлении.",
        "Продемонстрируйте отклонение невалидных запросов с возвратом человекочитаемой ошибки."
    ],
    "code_blocks": [
        {
            "filename": "validating_admission_webhook.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
)

type DatabaseCluster struct {
	Name     string
	Engine   string
	Replicas int
}

type DatabaseClusterValidator struct{}

func (v *DatabaseClusterValidator) ValidateCreate(ctx context.Context, obj *DatabaseCluster) error {
	// Правило 1: Кворум требует нечетного числа узлов
	if obj.Replicas%2 == 0 {
		return fmt.Errorf("quorum requirement violated: replicas must be an odd number (got %d, expected 1, 3, 5, 7)", obj.Replicas)
	}
	return nil
}

func (v *DatabaseClusterValidator) ValidateUpdate(ctx context.Context, oldObj, newObj *DatabaseCluster) error {
	// Правило 2: Движок СУБД неизменяем после создания
	if oldObj.Engine != newObj.Engine {
		return fmt.Errorf("field 'engine' is immutable: cannot change from '%s' to '%s'", oldObj.Engine, newObj.Engine)
	}

	return v.ValidateCreate(ctx, newObj)
}

func main() {
	validator := &DatabaseClusterValidator{}
	ctx := context.Background()

	fmt.Println("=== VALIDATING ADMISSION WEBHOOK TEST ===")

	// Тест 1: Валидное создание (3 реплики)
	valid := &DatabaseCluster{Name: "raft-db", Engine: "etcd", Replicas: 3}
	err := validator.ValidateCreate(ctx, valid)
	fmt.Printf("Create 3 replicas: Allowed? %v (err: %v)\n", err == nil, err)

	// Тест 2: Отклонение четного числа реплик (4 реплики)
	invalid := &DatabaseCluster{Name: "raft-db", Engine: "etcd", Replicas: 4}
	err = validator.ValidateCreate(ctx, invalid)
	fmt.Printf("Create 4 replicas: Allowed? %v (Reason: %v)\n", err == nil, err)

	// Тест 3: Отклонение смены неизменяемого поля Engine
	updated := &DatabaseCluster{Name: "raft-db", Engine: "consul", Replicas: 3}
	err = validator.ValidateUpdate(ctx, valid, updated)
	fmt.Printf("Update Engine:     Allowed? %v (Reason: %v)\n", err == nil, err)
}
"""
        }
    ],
    "under_the_hood": "Kubernetes API-сервер выполняет вызовы Validating Webhooks параллельно с таймаутом по умолчанию 10 секунд. Если вебхук не отвечает вовремя, поведение определяется параметром `failurePolicy`: при `failurePolicy: Fail` запрос пользователя отклоняется, при `failurePolicy: Ignore` запрос пропускается.",
    "pitfalls": [
        "Использование `failurePolicy: Fail` без высокодоступного развертывания вебхука (минимум 2–3 реплики оператора): при падении пода оператора пользователи не смогут создавать или обновлять ресурсы кластера.",
        "Выполнение медленных синхронных внешних вызовов внутри вебхука: при превышении таймаута вебхука все `kubectl apply` запросы начнут завершаться ошибкой `Webhook timeout`."
    ],
    "bigtech_interview": "В чем разница между фазами Mutating Admission и Validating Admission в пайплайне API-сервера? Фаза Mutating Admission выполняется СТРОГО ПЕРЕД фазой Validating. Мутационные вебхуки могут изменять тело объекта (подставлять дефолтные значения, инжектировать sidecar-контейнеры). Валидационные вебхуки запускаются после того, как все мутации применены, и могут только одобрить (Allow) или отклонить (Deny) итоговый запрос без возможности его модификации."
})

# Ex 19
exercises.append({
    "num": 19,
    "title": "Мутационные вебхуки (Mutating Admission Webhooks)",
    "task": "Реализуйте подстановку значений по умолчанию на этапе Admission Review: метод `Default()`. Если пользователь не указал версию образа базы данных или лимиты памяти, мутационный вебхук прозрачно подставляет рекомендуемые продакшен-значения перед сохранением объекта в etcd.",
    "theory": r"""Часто пользователям не требуется задавать десятки вспомогательных параметров конфигурации (размеры буферов, версии вспомогательных образов, таймауты подключения).

**Мутационный вебхук (Mutating Admission Webhook / Defaulting Webhook):**
1. Пользователь отправляет минимальный манифест:
   ```yaml
   apiVersion: storage.mycompany.com/v1alpha1
   kind: DatabaseCluster
   metadata:
     name: simple-db
   spec:
     replicas: 3
   ```
2. API-сервер вызывает мутационный вебхук оператора `Default()`.
3. Код вебхука анализирует пустые поля:
   - Если `spec.version == ""` -> подставляет `"16.2"`.
   - Если `spec.resources.memory == ""` -> подставляет `"4Gi"`.
   - Если `spec.storageClass == ""` -> подставляет `"fast-nvme"`.
4. Вебхук формирует JSON Patch и возвращает его в API-сервер.
5. В etcd сохраняется уже полностью укомплектованный объект.""",
    "step_by_step": [
        "Определите интерфейс дефолтера `CustomDefaulter` с методом `Default`.",
        "Реализуйте логику подстановки безопасных продакшен-значений по умолчанию.",
        "Продемонстрируйте модификацию разреженного пользовательского манифеста.",
        "Убедитесь, что явно заданные пользователем параметры не перезаписываются."
    ],
    "code_blocks": [
        {
            "filename": "mutating_admission_defaulting.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
)

type ClusterSpec struct {
	Version      string
	Replicas     int
	MemoryLimit  string
	StorageClass string
}

type DatabaseCluster struct {
	Name string
	Spec ClusterSpec
}

type DatabaseClusterDefaulter struct {
	DefaultVersion      string
	DefaultMemory       string
	DefaultStorageClass string
}

func (d *DatabaseClusterDefaulter) Default(ctx context.Context, obj *DatabaseCluster) {
	if obj.Spec.Version == "" {
		obj.Spec.Version = d.DefaultVersion
	}
	if obj.Spec.Replicas == 0 {
		obj.Spec.Replicas = 3
	}
	if obj.Spec.MemoryLimit == "" {
		obj.Spec.MemoryLimit = d.DefaultMemory
	}
	if obj.Spec.StorageClass == "" {
		obj.Spec.StorageClass = d.DefaultStorageClass
	}
}

func main() {
	defaulter := &DatabaseClusterDefaulter{
		DefaultVersion:      "postgres:16.2-alpine",
		DefaultMemory:       "4Gi",
		DefaultStorageClass: "ceph-nvme-replicated",
	}

	// Разреженный объект: пользователь указал только имя и переопределил память
	userCluster := &DatabaseCluster{
		Name: "dev-cluster",
		Spec: ClusterSpec{
			MemoryLimit: "16Gi", // Пользовательское значение должно сохраниться!
		},
	}

	fmt.Println("=== MUTATING ADMISSION (DEFAULTING) TEST ===")
	fmt.Printf("Before Defaulting:\n Version='%s', Replicas=%d, Memory='%s', StorageClass='%s'\n\n",
		userCluster.Spec.Version, userCluster.Spec.Replicas, userCluster.Spec.MemoryLimit, userCluster.Spec.StorageClass)

	defaulter.Default(context.Background(), userCluster)

	fmt.Printf("After Defaulting:\n Version='%s', Replicas=%d, Memory='%s', StorageClass='%s'\n",
		userCluster.Spec.Version, userCluster.Spec.Replicas, userCluster.Spec.MemoryLimit, userCluster.Spec.StorageClass)
}
"""
        }
    ],
    "under_the_hood": "Мутационный вебхук возвращает API-серверу не сам объект, а массив операций в формате **JSON Patch (RFC 6902)**: `[{\"op\": \"add\", \"path\": \"/spec/version\", \"value\": \"postgres:16.2-alpine\"}]`. API-сервер применяет эти операции к JSON-документу в памяти перед отправкой в валидационные вебхуки.",
    "pitfalls": [
        "Неидемпотентная мутация: если повторный вызов мутационного вебхука изменяет уже мутированный объект (например, добавляет суффикс к строке), API-сервер может зациклиться, вызывая вебхуки до исчерпания лимита рекурсии (Reinvocation Limit).",
        "Перезапись значений, явно переданных пользователем: всегда проверяйте `if field == \"\"` перед подстановкой дефолта."
    ],
    "bigtech_interview": "Почему подстановка значений по умолчанию в Mutating Webhook предпочтительнее реализации defaulting логики внутри метода Reconcile контроллера? Если значения по умолчанию подставляются в Reconcile через `client.Update()`, в etcd сначала сохраняется «неполный» объект, генерируется дополнительное событие Watch, увеличивается `metadata.generation`, и пользователь в `kubectl get` видит пустое поле до первого прохода Reconcile. Мутационный вебхук гарантирует, что объект сохраняется в etcd уже полностью заполненным атомарно."
})

# Ex 20
exercises.append({
    "num": 20,
    "title": "Безопасность вебхуков: генерация TLS-сертификатов с cert-manager",
    "task": "Kubernetes API-сервер взаимодействует с Admission Webhooks строго по протоколу HTTPS. Настройте манифесты cert-manager: создание `Issuer` и `Certificate` для автоматического выпуска и ротации TLS-сертификатов вебхука и инъекции CA-бандла (`cert-manager.io/inject-ca-from`).",
    "theory": r"""Для защиты от подделки запросов (Man-in-the-Middle) Kubernetes API-сервер предъявляет жесткие требования к Admission Webhooks:
1. Вызовы осуществляются **строго по протоколу HTTPS**.
2. В конфигурации вебхука (`MutatingWebhookConfiguration` / `ValidatingWebhookConfiguration`) в поле `clientConfig.caBundle` должен быть указан публичный корневой сертификат Certificate Authority (CA) в Base64.

Ручной выпуск сертификатов через OpenSSL и управление секретами в продакшене ненадежны из-за риска истечения срока действия ключей.
Индустриальный стандарт: **интеграция с `cert-manager`**
- Создается самоподписанный `Issuer` (SelfSigned) или корпоративный Vault Issuer.
- Ресурс `Certificate` автоматически генерирует `corev1.Secret` с `tls.crt` и `tls.key` для пода оператора.
- Аннотация `cert-manager.io/inject-ca-from: databases/webhook-server-cert` на манифесте WebhookConfiguration указывает cert-manager автоматически инжектировать актуальный `caBundle` прямо в конфигурацию API-сервера.""",
    "step_by_step": [
        "Определите структуру конфигурации TLS сертификатов вебхука.",
        "Реализуйте валидацию наличия валидного CA-бандла и совпадения Subject Alternative Names (SANs).",
        "Смоделируйте проверку SAN адреса сервиса `my-operator-webhook-service.databases.svc`.",
        "Продемонстрируйте механизм ротации сертификатов без простоя оператора."
    ],
    "code_blocks": [
        {
            "filename": "webhook_tls_certmanager.go",
            "lang": "go",
            "code": r"""package main

import (
	"crypto/x509"
	"encoding/pem"
	"fmt"
	"strings"
)

type WebhookTLSConfig struct {
	ServiceName string
	Namespace   string
	CABundle    string
	CertSANs    []string
}

func ValidateWebhookTLS(cfg WebhookTLSConfig) error {
	expectedDNS := fmt.Sprintf("%s.%s.svc", cfg.ServiceName, cfg.Namespace)
	expectedFullDNS := fmt.Sprintf("%s.%s.svc.cluster.local", cfg.ServiceName, cfg.Namespace)

	found := false
	for _, san := range cfg.CertSANs {
		if san == expectedDNS || san == expectedFullDNS {
			found = true
			break
		}
	}

	if !found {
		return fmt.Errorf("TLS certificate SANs %v do not contain required webhook DNS: '%s'",
			cfg.CertSANs, expectedDNS)
	}

	if strings.TrimSpace(cfg.CABundle) == "" {
		return fmt.Errorf("caBundle is empty! API Server will reject webhook connection")
	}

	return nil
}

func main() {
	cfg := WebhookTLSConfig{
		ServiceName: "db-operator-webhook-service",
		Namespace:   "databases",
		CABundle:    "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCg==",
		CertSANs: []string{
			"db-operator-webhook-service.databases.svc",
			"db-operator-webhook-service.databases.svc.cluster.local",
		},
	}

	err := ValidateWebhookTLS(cfg)
	fmt.Println("=== KUBERNETES WEBHOOK TLS CONFIG VALIDATION ===")
	fmt.Printf("Service DNS: %s.%s.svc\n", cfg.ServiceName, cfg.Namespace)
	fmt.Printf("TLS Config Valid: %v (err: %v)\n", err == nil, err)

	_ = pem.Block{}
	_ = x509.Certificate{}
}
"""
        }
    ],
    "under_the_hood": "Контроллер `cainjector` из состава `cert-manager` отслеживает аннотации на объектах `ValidatingWebhookConfiguration`. При обновлении или ротации сертификата `cainjector` считывает публичный ключ из `corev1.Secret`, кодирует в Base64 и атомарно патчит поле `clientConfig.caBundle` вебхука, исключая сетевые сбои.",
    "pitfalls": [
        "Несовпадение имени сервиса и пространства имен в Subject Alternative Name (SAN) сертификата: API-сервер отклонит TLS рукопожатие с ошибкой `x509: certificate is valid for X, not Y`.",
        "Истечение срока действия сертификата вебхука: приводит к полной блокировке всех операций создания и изменения ресурсов в кластере при `failurePolicy: Fail`."
    ],
    "bigtech_interview": "Почему для Admission Webhooks обязательно указывать SAN в формате <service-name>.<namespace>.svc? Kubernetes API-сервер разрешает доменное имя вебхука через CoreDNS кластера и инициирует TLS-соединение по внутреннему DNS-имени Сервиса. Клиент TLS в API-сервере сверяет имя хоста с расширением Subject Alternative Names (SAN) сертификата. Если имя сервиса отсутствует в сертификате, TLS handshake завершится фатальной ошибкой безопасности."
})

# Ex 21
exercises.append({
    "num": 21,
    "title": "Наблюдение за дочерними ресурсами (Watches & Owns)",
    "task": "Что произойдет, если администратор вручную удалит Pod или Service, созданный вашим оператором? Настройте связывание в билдере: `ctrl.NewControllerManagedBy(mgr).For(&storagev1.DatabaseCluster{}).Owns(&corev1.Service{}).Complete(r)`. Убедитесь, что при падении или изменении дочернего сервиса оператор немедленно запускает Reconcile и восстанавливает его.",
    "theory": r"""Оператор отвечает за поддержание желаемого состояния не только в ответ на действия пользователя над родительским CRD, но и при внешних возмущениях в кластере (дрифт инфраструктуры):
- Администратор случайно выполнил `kubectl delete service pg-primary`.
- Воркер нода упала, и Pod перешел в статус `Failed`.
- Другой контроллер случайно изменил конфигурацию ConfigMap.

Директива **`.Owns(&corev1.Service{})`** в билдере контроллера:
1. Контроллер подписывается на события Watch дочернего ресурса `Service`.
2. Когда сервис изменяется или удаляется, `controller-runtime` заглядывает в его `metadata.ownerReferences`.
3. По ссылке `OwnerReference` извлекается имя родительского объекта `DatabaseCluster`.
4. В очередь `workqueue` помещается запрос на примирение **родительского объекта**!
5. Запускается метод `Reconcile` родителя, который обнаруживает отсутствие дочернего ресурса и мгновенно воссоздает его (Self-Healing).""",
    "step_by_step": [
        "Определите карту связей владения `OwnerMap`.",
        "Реализуйте обработчик событий дочерних объектов `EnqueueRequestForOwner`.",
        "Смоделируйте удаление дочернего сетевого сервиса администратором.",
        "Продемонстрируйте автоматическую постановку родительского ресурса в очередь Reconcile для самоисцеления."
    ],
    "code_blocks": [
        {
            "filename": "watches_owns_self_healing.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
)

type ReconcileRequest struct {
	Namespace string
	Name      string
}

type EnqueueRequestForOwnerHandler struct {
	ownerKind string
}

func (h *EnqueueRequestForOwnerHandler) OnChildEvent(childName, ownerKind, ownerName, namespace string) *ReconcileRequest {
	if ownerKind != h.ownerKind || ownerName == "" {
		return nil
	}

	fmt.Printf("[WATCH EVENT] Child '%s' changed! Enqueueing parent %s '%s/%s'\n",
		childName, ownerKind, namespace, ownerName)

	return &ReconcileRequest{
		Namespace: namespace,
		Name:      ownerName,
	}
}

func main() {
	handler := &EnqueueRequestForOwnerHandler{ownerKind: "DatabaseCluster"}

	fmt.Println("=== KUBERNETES WATCHES & OWNS SELF-HEALING ===")

	// Симуляция: администратор удалил сервис pg-primary-service
	req := handler.OnChildEvent(
		"pg-primary-service",
		"DatabaseCluster",
		"production-db",
		"databases",
	)

	if req != nil {
		fmt.Printf("Reconciliation scheduled for PARENT: %s/%s -> Self-healing will recreate child service!\n",
			req.Namespace, req.Name)
	}
}
"""
        }
    ],
    "under_the_hood": "Под капотом директива `.Owns(&T{})` создает `handler.EnqueueRequestForOwner` с указанием типа владельца и схемы типов `Scheme`. Обработчик использует Indexer кэша информера для мгновенного резолвинга родительского объекта по UID владельца без выполнения дополнительных запросов к API-серверу.",
    "pitfalls": [
        "Забытый вызов `ctrl.SetControllerReference` при создании дочернего ресурса: без `OwnerReference` метод `Owns()` не сможет определить родителя, и при удалении дочернего объекта самоисцеление (Self-Healing) не сработает!",
        "Наблюдение за слишком широким классом ресурсов (например `Owns(&corev1.Pod{})` в кластере с 100 000 подов) без фильтрации предикатами: создаст огромный поток событий в информер."
    ],
    "bigtech_interview": "Как контроллер понимает, какой именно родительский ресурс нужно примирить при падении дочернего пода, за которым настроен Watch через Owns? Когда в информер поступает событие изменения дочернего пода, обработчик `handler.EnqueueRequestForOwner` считывает срез `metadata.ownerReferences` пода. Он ищет запись, где `controller: true` и `kind` совпадает с целевым типом родительского CRD, извлекает `namespace` и `name` родителя и ставит в очередь `workqueue` задачу на Reconcile родителя."
})

# Ex 22
exercises.append({
    "num": 22,
    "title": "Реакция на внешние события через source.Channel",
    "task": "Оператор должен реагировать не только на события Kubernetes, но и на внешние триггеры (например, вебхук о готовности бэкапа в облаке или сообщение из топика Kafka). Настройте источник событий `source.Channel`: передача кастомных событий в очередь контроллера через канал Go `chan event.GenericEvent`.",
    "theory": r"""Классический контроллер слушает только события из etcd через информеры.
Однако в сложных системах триггеры изменения состояния часто приходят из **внешних систем**:
- Внешняя система резервного копирования (S3/GCS webhook) уведомила, что ночной бэкап завершен.
- Брокер сообщений Apache Kafka прислал сообщение о смене топологии дата-центра.
- Внешний мониторинг Prometheus Alertmanager уведомил оператор об аварии диска на физической ноде.

Механизм **`source.Channel`** в `controller-runtime`:
1. Создается небуферизованный или буферизованный канал Go:
   `events := make(chan event.GenericEvent, 100)`
2. Канал подключается в билдер контроллера:
   `WatchesRawSource(source.Channel(events, &handler.EnqueueRequestForObject{}))`
3. Фоновая горутина (HTTP webhook listener, Kafka consumer) пишет в канал события `event.GenericEvent{Object: cluster}`.
4. `controller-runtime` считывает событие из канала и автоматически ставит ресурс в очередь `Reconcile`!""",
    "step_by_step": [
        "Определите структуру `GenericEvent` с ссылкой на целевой объект.",
        "Реализуйте мост передачи событий из Go-канала в очередь контроллера `source.Channel`.",
        "Смоделируйте фоновый HTTP-приемник внешних вебхуков от облачного хранилища бэкапов.",
        "Продемонстрируйте запуск примирения по сигналу из внешнего канала."
    ],
    "code_blocks": [
        {
            "filename": "external_source_channel.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"time"
)

type NamespacedName struct {
	Namespace string
	Name      string
}

type GenericEvent struct {
	Resource NamespacedName
	Message  string
}

func ExternalWebhookListener(ch chan<- GenericEvent) {
	// Симуляция внешнего вебхука от облачного провайдера S3 через 50 мс
	time.Sleep(50 * time.Millisecond)
	ch <- GenericEvent{
		Resource: NamespacedName{Namespace: "databases", Name: "pg-analytics"},
		Message:  "S3_BACKUP_COMPLETED_SUCCESSFULLY",
	}
}

func ControllerEventSourceBridge(events <-chan GenericEvent, reconcileQueue chan<- NamespacedName) {
	for evt := range events {
		fmt.Printf("[SOURCE.CHANNEL] Received external event for %s/%s: %s\n",
			evt.Resource.Namespace, evt.Resource.Name, evt.Message)
		reconcileQueue <- evt.Resource
	}
}

func main() {
	eventsChan := make(chan GenericEvent, 10)
	reconcileQueue := make(chan NamespacedName, 10)

	fmt.Println("=== KUBERNETES SOURCE.CHANNEL EXTERNAL EVENTS ===")

	go ExternalWebhookListener(eventsChan)
	go func() {
		ControllerEventSourceBridge(eventsChan, reconcileQueue)
	}()

	// Ожидание поступления задачи в очередь Reconcile
	triggered := <-reconcileQueue
	fmt.Printf("[RECONCILE TRIGGERED] Processing external event for cluster: %s/%s\n",
		triggered.Namespace, triggered.Name)
}
"""
        }
    ],
    "under_the_hood": "Внутри `controller-runtime` компонент `source.Channel` запускает долгоживущую горутину, которая читает из предоставленного Go-канала в цикле `select` с учетом контекста `ctx.Done()`. Каждое сообщение передается в переданный `handler.EventHandler`, преобразующий его в ключ `reconcile.Request` очереди воркеров.",
    "pitfalls": [
        "Переполнение буфера канала `chan event.GenericEvent`: если канал заполнен, а контроллер не успевает вычитывать события, пишущая горутина заблокируется. Используйте неблокирующую отправку `select { case ch <- evt: default: // log dropped event }` или адекватный размер буфера.",
        "Забытое закрытие канала при завершении работы менеджера оператора, приводящее к утечкам горутин."
    ],
    "bigtech_interview": "Как в архитектуре Kubernetes операторов организовать реакцию на сообщения из очереди Kafka или RabbitMQ? Создается долгоживущий Consumer (Runnable в терминах controller-runtime), который регистрируется в менеджере `mgr.Add(myKafkaConsumer)`. При получении сообщения Consumer формирует объект `event.GenericEvent{Object: targetCRD}` и отправляет его в канал `chan event.GenericEvent`, подключенный к контроллеру через `builder.WatchesRawSource(source.Channel(events, ...))`. Это обеспечивает бесшовную интеграцию внешних очередей с циклом Reconcile."
})

# Verify gofmt
print(f"Total exercises in part 1: {len(exercises)}")
for ex in exercises:
    num = ex["num"]
    for cb in ex["code_blocks"]:
        code = cb["code"]
        with tempfile.NamedTemporaryFile("w", suffix=".go", delete=False) as tf:
            tf.write(code)
            tf_path = tf.name
        try:
            res = subprocess.run(["gofmt", "-e", tf_path], capture_output=True, text=True)
            if res.returncode != 0:
                print(f"gofmt error in ex {num}:", res.stderr)
                raise RuntimeError(f"Syntax error in exercise {num}")
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

out_path = "/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch91_p1.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Wrote {out_path} successfully with {len(exercises)} exercises!")
