# -*- coding: utf-8 -*-
import json
import subprocess
import tempfile
import os

exercises = []

# Ex 23
exercises.append({
    "num": 23,
    "title": "Оптимистические конфликты версий (Conflict Retry)",
    "task": "При одновременной модификации одного ресурса несколькими процессами API-сервер возвращает ошибку `OperationCannotBeFulfilled` (ResourceVersion mismatch). Оберните операции модификации в стандартную функцию повторов `k8s.io/client-go/util/retry.RetryOnConflict(retry.DefaultBackoff, func() error { ... })`.",
    "theory": r"""Kubernetes API-сервер использует механизм **оптимистической блокировки (Optimistic Concurrency Control)** на базе поля `metadata.resourceVersion`.
Если процесс A и процесс B одновременно прочитали ресурс с `resourceVersion: 100`, а затем процесс A сохранил обновление (`resourceVersion` стал 101), то попытка процесса B сохранить свои изменения будет отклонена API-сервером с HTTP ошибкой:
`409 Conflict: Operation cannot be fulfilled on databaseclusters.storage: the object has been modified; please apply your changes to the latest version and try again`.

Стандартное решение: **`retry.RetryOnConflict`**
Пакет `k8s.io/client-go/util/retry` предоставляет функцию `RetryOnConflict`:
```go
err := retry.RetryOnConflict(retry.DefaultBackoff, func() error {
    // 1. Повторно считываем самый свежий объект из API
    if err := r.Get(ctx, req.NamespacedName, cluster); err != nil {
        return err
    }
    // 2. Применяем мутацию
    cluster.Status.ReadyReplicas = 3
    // 3. Пытаемся обновить
    return r.Status().Update(ctx, cluster)
})
```
Функция автоматически повторяет операцию с экспоненциальной задержкой и джиттером при ошибке конфликта версий.""",
    "step_by_step": [
        "Определите ошибку `ErrConflict` и структуру ресурса с версией.",
        "Реализуйте симулятор функции `RetryOnConflict` с повторным чтением актуального состояния.",
        "Смоделируйте гонку версий между двумя конкурентными процессами.",
        "Продемонстрируйте успешное обновление ресурса после устранения конфликта версий."
    ],
    "code_blocks": [
        {
            "filename": "retry_on_conflict_pattern.go",
            "lang": "go",
            "code": r"""package main

import (
	"errors"
	"fmt"
	"sync"
	"time"
)

var ErrConflict = errors.New("409 Conflict: resourceVersion mismatch")

type DatabaseCluster struct {
	Name            string
	ResourceVersion int
	ActiveReplicas  int
}

type APIServer struct {
	mu      sync.Mutex
	cluster DatabaseCluster
}

func (s *APIServer) Get() DatabaseCluster {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.cluster
}

func (s *APIServer) Update(obj DatabaseCluster) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if obj.ResourceVersion != s.cluster.ResourceVersion {
		return ErrConflict
	}

	obj.ResourceVersion++
	s.cluster = obj
	return nil
}

func RetryOnConflict(attempts int, op func() error) error {
	var err error
	for i := 0; i < attempts; i++ {
		err = op()
		if err == nil {
			return nil
		}
		if errors.Is(err, ErrConflict) {
			time.Sleep(10 * time.Millisecond)
			continue
		}
		return err
	}
	return fmt.Errorf("retry limit exceeded: %w", err)
}

func main() {
	server := &APIServer{
		cluster: DatabaseCluster{Name: "postgres", ResourceVersion: 10, ActiveReplicas: 1},
	}

	// Симулируем параллельное изменение версии другим процессом
	go func() {
		time.Sleep(5 * time.Millisecond)
		_ = server.Update(DatabaseCluster{Name: "postgres", ResourceVersion: 10, ActiveReplicas: 2})
	}()

	// Наш процесс пытается обновить статус с использованием RetryOnConflict
	err := RetryOnConflict(5, func() error {
		latest := server.Get()
		fmt.Printf("[RetryOnConflict] Read latest ResourceVersion: %d\n", latest.ResourceVersion)
		latest.ActiveReplicas = 3
		return server.Update(latest)
	})

	fmt.Println("=== KUBERNETES CONFLICT RETRY TEST ===")
	fmt.Printf("Update completed with error: %v\n", err)
	finalState := server.Get()
	fmt.Printf("Final Cluster State: ResourceVersion=%d, ActiveReplicas=%d\n",
		finalState.ResourceVersion, finalState.ActiveReplicas)
}
"""
        }
    ],
    "under_the_hood": "Алгоритм `retry.DefaultBackoff` использует 5 попыток с начальной задержкой 10 мс, фактором роста 1.0 и 10% джиттером (`Steps: 5, Duration: 10ms, Factor: 1.0, Jitter: 0.1`). Джиттер предотвращает явление Thundering Herd, когда сотни параллельных воркеров синхронно бомбардируют API-сервер повторными запросами.",
    "pitfalls": [
        "Мутация устаревшего экземпляра структуры внутри цикла `RetryOnConflict`: если не вызвать `r.Get()` в начале каждой итерации, вы будете бесконечно отправлять устаревший `ResourceVersion`.",
        "Оборачивание в `RetryOnConflict` неидемпотентных операций (например отправка HTTP-запроса платежному шлюзу): повторы должны применяться исключительно к транзакциям обновления в etcd."
    ],
    "bigtech_interview": "Почему в контроллерах Kubernetes не используется пессимистическая блокировка (например SELECT FOR UPDATE в SQL)? Kubernetes спроектирован как высокомасштабируемая распределенная система. Пессимистические блокировки требуют поддержания открытых транзакций в распределенном хранилище etcd, снижают пропускную способность кластера и приводят к дедлокам при сетевых сбоях контроллеров. Оптимистическая блокировка на базе ResourceVersion полностью децентрализована и не блокирует чтение."
})

# Ex 24
exercises.append({
    "num": 24,
    "title": "Интеграционное тестирование с envtest",
    "task": "Настройте окружение `envtest`: запуск локального реального бинарника `kube-apiserver` и `etcd` прямо из юнит-тестов Go без необходимости разворачивать Minikube или Docker-in-Docker. Напишите тест, создающий ресурс `DatabaseCluster` и проверяющий генерацию дочерних объектов через клиент.",
    "theory": r"""Традиционное тестирование операторов в реальных кластерах (Minikube, Kind, k3s) страдает от медленного старта (минуты) и тяжеловесности. Мокирование интерфейсов (`fake.NewClientBuilder`) часто скрывает реальные ошибки валидации OpenAPI и гонки версий.

Индустриальный стандарт: **пакет `sigs.k8s.io/controller-runtime/pkg/envtest`**
1. `envtest` запускает локальные бинарники реального `kube-apiserver` и `etcd` прямо из юнит-теста на машине разработчика за 1–2 секунды!
2. В `envtest` **отсутствуют** контроллер-менеджер (`kube-controller-manager`) и планировщик (`kube-scheduler`). Это идеальная изолированная среда для проверки логики вашего оператора.
3. Тесты проверяют реальную регистрацию CRD схем, валидацию полей, подресурсы `/status` и работу информеров без сетевых накладных расходов.""",
    "step_by_step": [
        "Определите модель тестового окружения `EnvTestEnvironment`.",
        "Реализуйте жизненный цикл: инициализация схемы, старт виртуального сервера, регистрация CRD.",
        "Напишите тест создания пользовательского ресурса с проверкой сохранения в хранилище.",
        "Обеспечьте корректный останов тестового окружения через `defer env.Stop()`."
    ],
    "code_blocks": [
        {
            "filename": "envtest_integration_harness.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
	"sync"
)

type CustomResource struct {
	Namespace string
	Name      string
	Replicas  int
}

type EnvTestServer struct {
	mu      sync.RWMutex
	storage map[string]CustomResource
	running bool
}

func (s *EnvTestServer) Start() error {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.storage = make(map[string]CustomResource)
	s.running = true
	fmt.Println("[envtest] Local kube-apiserver & etcd started on in-memory transport")
	return nil
}

func (s *EnvTestServer) Stop() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.running = false
	fmt.Println("[envtest] Local test environment stopped cleanly")
}

func (s *EnvTestServer) Create(ctx context.Context, obj CustomResource) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if !s.running {
		return fmt.Errorf("apiserver is not running")
	}
	key := fmt.Sprintf("%s/%s", obj.Namespace, obj.Name)
	if _, exists := s.storage[key]; exists {
		return fmt.Errorf("already exists: %s", key)
	}
	s.storage[key] = obj
	return nil
}

func main() {
	env := &EnvTestServer{}
	if err := env.Start(); err != nil {
		panic(err)
	}
	defer env.Stop()

	// Выполнение интеграционного теста
	testCluster := CustomResource{
		Namespace: "default",
		Name:      "test-postgres",
		Replicas:  3,
	}

	err := env.Create(context.Background(), testCluster)
	fmt.Println("=== KUBERNETES ENVTEST INTEGRATION TEST ===")
	fmt.Printf("Create resource '%s/%s' -> Result: %v\n",
		testCluster.Namespace, testCluster.Name, err == nil)
}
"""
        }
    ],
    "under_the_hood": "Утилита `setup-envtest` скачивает скомпилированные бинарники `kube-apiserver` и `etcd` для архитектуры хоста (linux/darwin, amd64/arm64). Пакет `envtest.Environment` стартует эти процессы в фоновом режиме на случайных свободных TCP-портах и возвращает готовый `rest.Config` для инициализации клиента.",
    "pitfalls": [
        "Ожидание, что в `envtest` запустятся поды: в envtest нет `kubelet` и `kube-scheduler`, поэтому созданные Deployment и Pod не перейдут в статус Running без ручного обновления статуса мок-контроллером.",
        "Забытый вызов `testEnv.Stop()` в функции завершения тестов (`AfterSuite`), приводящий к зависанию осиротевших процессов etcd и утечке памяти в CI."
    ],
    "bigtech_interview": "В чем главное преимущество тестирования операторов через envtest по сравнению со связкой fake client (fake.NewClientBuilder)? Fake client реализует лишь примитивную Go-мапу объектов в памяти: он не валидирует типы по OpenAPI схеме, игнорирует subresource /status, не генерирует ResourceVersion и не эмулирует оптимистические конфликты 409. `envtest` запускает настоящий бинарник kube-apiserver, гарантируя 100% паритет поведения с реальным продакшен-кластером."
})

# Ex 25
exercises.append({
    "num": 25,
    "title": "Тестирование с использованием Ginkgo и Gomega",
    "task": "Изучите BDD-фреймворк тестирования, принятый в экосистеме Kubernetes (Ginkgo/Gomega). Напишите сценарий тестирования контроллера: блоки `Describe`, `Context`, `It`, асинхронные проверки условий `Eventually(func() bool { ... }, timeout, interval).Should(BeTrue())`.",
    "theory": r"""Поскольку контроллеры Kubernetes работают **асинхронно** (между созданием кастомного ресурса и генерацией дочерних подов проходит время), классические синхронные ассерты (`assert.Equal`) в юнит-тестах завершаются ложными падениями (Flaky Tests).

Индустриальный стандарт экосистемы Kubernetes: **BDD фреймворк Ginkgo + Gomega**
- **Структура сценария:**
  - `Describe("DatabaseCluster Controller")` — тестируемый компонент.
  - `Context("When creating a new cluster")` — начальные условия.
  - `It("Should provision the primary statefulset")` — ожидаемое поведение.
- **Асинхронные ассерты `Eventually`:**
  - Функция `Eventually` циклически опрашивает условие с заданным интервалом до наступления таймаута:
    ```go
    Eventually(func() bool {
        err := k8sClient.Get(ctx, key, &statefulSet)
        return err == nil && statefulSet.Status.ReadyReplicas == 3
    }, timeout, interval).Should(BeTrue())
    ```
- **`Consistently`:** Проверяет, что условие сохраняется стабильным в течение определенного времени (защита от флапающих состояний).""",
    "step_by_step": [
        "Смоделируйте BDD ассерты `Eventually` на чистом Go с таймаутом и интервалом опроса.",
        "Реализуйте асинхронный симулятор создания дочерних ресурсов контроллером.",
        "Напишите тестовый блок проверки появления дочернего сервиса в течение таймаута.",
        "Продемонстрируйте падение теста при превышении таймаута ожидания условия."
    ],
    "code_blocks": [
        {
            "filename": "ginkgo_gomega_bdd_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"time"
)

func Eventually(condition func() bool, timeout, interval time.Duration) bool {
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		if condition() {
			return true
		}
		time.Sleep(interval)
	}
	return condition()
}

type StatefulSetSimulator struct {
	ReadyReplicas int
}

func main() {
	sts := &StatefulSetSimulator{ReadyReplicas: 0}

	// Имитация фоновой работы оператора: реплики станут готовы через 60 мс
	go func() {
		time.Sleep(60 * time.Millisecond)
		sts.ReadyReplicas = 3
	}()

	fmt.Println("=== GINKGO / GOMEGA ASYNC EVENTUALLY TEST ===")

	// Тест 1: Успешное ожидание готовности кластера
	success := Eventually(func() bool {
		fmt.Printf("[Eventually Poll] Current ReadyReplicas: %d\n", sts.ReadyReplicas)
		return sts.ReadyReplicas == 3
	}, 150*time.Millisecond, 25*time.Millisecond)

	fmt.Printf("Test Result: Eventually(ReadyReplicas == 3) -> Passed: %v\n\n", success)

	// Тест 2: Превышение таймаута при недостижимом условии
	failed := Eventually(func() bool {
		return sts.ReadyReplicas == 10 // Никогда не наступит
	}, 50*time.Millisecond, 20*time.Millisecond)

	fmt.Printf("Test Result: Eventually(ReadyReplicas == 10) -> Timed out as expected: %v\n", !failed)
}
"""
        }
    ],
    "under_the_hood": "Gomega использует рефлексию и интерфейсы `types.GomegaMatcher` для вычисления условий. В отличие от наивного цикла `for`, `Eventually` форматирует подробный отчет об ошибке с дампом последнего полученного состояния и временем истечения дедлайна.",
    "pitfalls": [
        "Использование `time.Sleep()` с фиксированной задержкой вместо `Eventually`: на медленных серверах CI тесты начинают непредсказуемо падать (Flakiness), а на быстрых машинах тесты идут неоправданно долго.",
        "Слишком короткий таймаут `Eventually` (например 50 мс): под нагрузкой в CI рантайм Go может приостановить горутину из-за GC, вызвав ложный таймаут."
    ],
    "bigtech_interview": "В чем разница между ассертами Eventually и Consistently в библиотеке Gomega? `Eventually` проверяет, что условие станет истинным ХОТЯ БЫ ОДИН РАЗ до истечения таймаута (идеально для асинхронного ожидания завершения развертывания). `Consistently` проверяет, что условие остается истинным НЕПРЕРЫВНО на протяжении всего отведенного интервала времени (необходимо для доказательства того, что контроллер не совершает ложных перезапусков или флапаний)."
})

print("Writing Chapter 91 Part 2 (exercises 23-25 processed)")

# Ex 26
exercises.append({
    "num": 26,
    "title": "RBAC-манифесты и принцип наименьших привилегий",
    "task": "Оператор должен иметь доступ только к тем ресурсам, которыми управляет. Разметьте методы контроллера марoverride-маркерами: `// +kubebuilder:rbac:groups=storage.mycompany.com,resources=databaseclusters,verbs=get;list;watch;create;update;patch;delete`. Сгенерируйте `ClusterRole` и проверьте отсутствие избыточных прав (например, запрет прав администратора кластера).",
    "theory": r"""Принцип наименьших привилегий (**Principle of Least Privilege**) — краеугольный камень безопасности платформы Kubernetes.
Если оператор развертывается с правами `cluster-admin`, компрометация контейнера оператора (RCE уязвимость) дает злоумышленнику полный контроль над всеми секретами и нодами кластера.

Управление RBAC в Kubebuilder:
Маркеры генерации прав размещаются непосредственно над методом `Reconcile`:
```go
// +kubebuilder:rbac:groups=storage.mycompany.com,resources=databaseclusters,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=storage.mycompany.com,resources=databaseclusters/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=storage.mycompany.com,resources=databaseclusters/finalizers,verbs=update
// +kubebuilder:rbac:groups=apps,resources=statefulsets,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=core,resources=services;configmaps;secrets,verbs=get;list;watch;create;update;patch
```
Команда `make manifests` транслирует эти комментарии в файл `config/rbac/role.yaml` (`ClusterRole`). Права на ресурсы, не задействованные в Reconcile, должны быть строго исключены.""",
    "step_by_step": [
        "Определите модель правила RBAC `PolicyRule` с группами, ресурсами и глаголами (verbs).",
        "Создайте структуру валидации RBAC прав оператора на предмет избыточных привилегий.",
        "Запрограммируйте проверку отсутствия опасных wildcard '*' прав.",
        "Сгенерируйте итоговый манифест роли с минимально достаточными правами."
    ],
    "code_blocks": [
        {
            "filename": "rbac_least_privilege.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"strings"
)

type PolicyRule struct {
	APIGroups []string
	Resources []string
	Verbs     []string
}

func AuditRBACSecurity(rules []PolicyRule) []string {
	var warnings []string
	for _, rule := range rules {
		for _, verb := range rule.Verbs {
			if verb == "*" {
				warnings = append(warnings, fmt.Sprintf("CRITICAL: Wildcard verb '*' found in rule for resources: %v", rule.Resources))
			}
		}
		for _, res := range rule.Resources {
			if res == "*" {
				warnings = append(warnings, "CRITICAL: Wildcard resource '*' found!")
			}
			if res == "secrets" {
				for _, v := range rule.Verbs {
					if v == "delete" || v == "deletecollection" {
						warnings = append(warnings, "WARNING: Sensitive 'secrets' resource has destructive delete permissions")
					}
				}
			}
		}
	}
	return warnings
}

func main() {
	operatorRole := []PolicyRule{
		{
			APIGroups: []string{"storage.mycompany.com"},
			Resources: []string{"databaseclusters", "databaseclusters/status"},
			Verbs:     []string{"get", "list", "watch", "create", "update", "patch", "delete"},
		},
		{
			APIGroups: []string{"apps"},
			Resources: []string{"statefulsets"},
			Verbs:     []string{"get", "list", "watch", "create", "update", "patch"},
		},
		{
			APIGroups: []string{""},
			Resources: []string{"services", "configmaps"},
			Verbs:     []string{"get", "list", "watch", "create", "update"},
		},
	}

	warnings := AuditRBACSecurity(operatorRole)

	fmt.Println("=== KUBERNETES RBAC LEAST PRIVILEGE AUDIT ===")
	fmt.Printf("Total Rules Configured: %d\n", len(operatorRole))
	if len(warnings) == 0 {
		fmt.Println("RBAC Audit PASSED: Zero wildcard violations. Least privilege enforced!")
	} else {
		for _, w := range warnings {
			fmt.Println(" -", w)
		}
	}
	_ = strings.Join(warnings, "")
}
"""
        }
    ],
    "under_the_hood": "Kubernetes API-сервер проверяет права с помощью авторизатора RBAC (`rbac.authorization.k8s.io`). Каждый запрос валидируется по триплету: `(User/ServiceAccount, Namespace, Verb, Resource, Subresource)`. Отсутствие права на подресурс `/status` приводит к отклонению запросов обновления статуса со статусом 403.",
    "pitfalls": [
        "Использование `verbs: [\"*\"]` или `resources: [\"*\"]` для 'быстрого прохождения тестов': это грубейшее нарушение требований информационной безопасности (SecOps/Compliance).",
        "Забытые права на эндпоинт `/finalizers`: оператор не сможет снять финализатор и зависнет при попытке удаления ресурса."
    ],
    "bigtech_interview": "В чем разница между RoleBinding и ClusterRoleBinding для ServiceAccount оператора? `ClusterRoleBinding` наделяет оператор правами во ВСЕХ пространствах имен кластера (Cluster-Scoped Operator). Если оператор предназначен для работы только в одном tenant-пространстве (Namespace-Scoped Operator), используется `RoleBinding`, ограничивающий доступ ServiceAccount оператора строго границами целевого Namespace."
})

# Ex 27
exercises.append({
    "num": 27,
    "title": "Экспорт метрик контроллера в Prometheus",
    "task": "Подключите сбор метрик: `metrics.Registry.MustRegister(reconcileDurationMetric, clusterCountMetric)`. Экспортируйте кастомные бизнес-метрики состояния управляемых баз данных: количество реплик в статусе Ready, лаг репликации и число аварийных переключений мастера (failovers).",
    "theory": r"""Библиотека `controller-runtime` по умолчанию экспортирует стандартные системные метрики контроллера на порту `:8080` (`/metrics`):
- `controller_runtime_reconcile_total`: общее число запусков Reconcile с метками `result="success|error"`.
- `controller_runtime_reconcile_time_seconds`: гистограмма длительности выполнения примирения.
- `workqueue_depth`: текущий размер очереди задач.

Регистрация пользовательских бизнес-метрик:
Для добавления предметных метрик оператора используется глобальный реестр `sigs.k8s.io/controller-runtime/pkg/metrics`:
```go
import "sigs.k8s.io/controller-runtime/pkg/metrics"

var (
    ClusterReplicasGauge = prometheus.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "db_operator_cluster_ready_replicas",
            Help: "Current number of healthy database replicas",
        },
        []string{"namespace", "cluster_name"},
    )
)

func init() {
    metrics.Registry.MustRegister(ClusterReplicasGauge)
}
```
Внутри `Reconcile` контроллер обновляет значение метрики вызовом `ClusterReplicasGauge.WithLabelValues(ns, name).Set(float64(readyCount))`.""",
    "step_by_step": [
        "Определите структуры метрик Gauge и Counter с поддержкой меток.",
        "Создайте потокобезопасный реестр метрик `CustomMetricRegistry`.",
        "Реализуйте регистрацию и обновление бизнес-метрик: `ready_replicas` и `failovers_total`.",
        "Продемонстрируйте сбор метрик кластера в цикле примирения."
    ],
    "code_blocks": [
        {
            "filename": "prometheus_operator_metrics.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"sync"
)

type MetricKey struct {
	Namespace string
	Cluster   string
}

type OperatorMetrics struct {
	mu            sync.RWMutex
	readyReplicas map[MetricKey]float64
	failoverTotal map[MetricKey]int64
}

func NewOperatorMetrics() *OperatorMetrics {
	return &OperatorMetrics{
		readyReplicas: make(map[MetricKey]float64),
		failoverTotal: make(map[MetricKey]int64),
	}
}

func (m *OperatorMetrics) SetReadyReplicas(ns, cluster string, count float64) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.readyReplicas[MetricKey{Namespace: ns, Cluster: cluster}] = count
}

func (m *OperatorMetrics) IncFailover(ns, cluster string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.failoverTotal[MetricKey{Namespace: ns, Cluster: cluster}]++
}

func main() {
	metrics := NewOperatorMetrics()

	// Имитация цикла примирения
	ns := "databases"
	cluster := "postgres-prod"

	metrics.SetReadyReplicas(ns, cluster, 3)
	metrics.IncFailover(ns, cluster)

	fmt.Println("=== KUBERNETES OPERATOR PROMETHEUS METRICS ===")
	metrics.mu.RLock()
	defer m.mu.RUnlock()

	for k, v := range metrics.readyReplicas {
		fmt.Printf("metric: db_operator_cluster_ready_replicas{namespace=\"%s\",cluster=\"%s\"} %.1f\n",
			k.Namespace, k.Cluster, v)
	}
	for k, v := range metrics.failoverTotal {
		fmt.Printf("metric: db_operator_failover_total{namespace=\"%s\",cluster=\"%s\"} %d\n",
			k.Namespace, k.Cluster, v)
	}
}
"""
        }
    ],
    "under_the_hood": "Метрики Prometheus собираются пулом скрейпинга (Prometheus Scrape Loop). При удалении кастомного ресурса из кластера контроллер обязан удалить соответствующую серию метрик вызовом `GaugeVec.DeleteLabelValues(ns, name)`, иначе старые метрики удаленного ресурса продолжат вечно экспортироваться в Prometheus (утечка памяти time-series).",
    "pitfalls": [
        "Использование Prometheus default registry (`prometheus.MustRegister`) вместо `controller-runtime` registry: приведет к коллизиям и отсутствию метрик в общем эндпоинте оператора.",
        "Забытое удаление меток (`DeleteLabelValues`) при уничтожении кластера: провоцирует утечку памяти в мониторинге."
    ],
    "bigtech_interview": "По каким ключевым SLI/SLO метрикам оценивается здоровье самого Kubernetes оператора в production? 1) Latency примирения (`controller_runtime_reconcile_time_seconds` p99 < 500ms); 2) Очередь задач (`workqueue_depth` = 0 в штатном режиме, отсутствие роста); 3) Доля ошибок примирения (`rate(controller_runtime_reconcile_total{result=\"error\"}[5m])` / total < 0.1%); 4) Время задержки в очереди (`workqueue_queue_duration_seconds`)."
})

# Ex 28
exercises.append({
    "num": 28,
    "title": "Выборы лидера (Leader Election) для высокой доступности (HA)",
    "task": "В продакшене оператор развертывается в 2–3 репликах для отказоустойчивости, однако цикл примирения должен исполняться ровно одним активным процессом во избежание конфликтов. Включите механизм Leader Election в `manager.Options{LeaderElection: true, LeaderElectionID: \"db-operator-lock\"}` на базе Kubernetes Lease-ресурсов.",
    "theory": r"""Развертывание оператора в единственной реплике недопустимо в production (Single Point of Failure):
- При обновлении ноды оператор перезапускается.
- На время перезапуска кластер остается без контроля самоисцеления.

Решение: **Active-Passive HA с Leader Election**
Оператор развертывается в виде `Deployment` с `replicas: 3`.
Механизм выбора лидера на базе **Kubernetes Leases (`coordination.k8s.io/v1`)**:
1. Все 3 реплики соревнуются за обладание ресурсом `Lease` с именем `db-operator-lock` в namespace оператора.
2. Процесс, первым создавший или продливший Lease, становится **Лидером (Active Leader)**:
   - Запускает контроллеры, информеры и цикл Reconcile.
   - Периодически (раз в 2–5 секунд) обновляет метку времени продления аренды (`renewTime`).
3. Остальные реплики остаются **Пассивными (Standby)**:
   - Слушают Lease и ждут освобождения.
4. Если Лидер упал (Node Crash / OOM), через время `leaseDuration` (обычно 15 секунд) пассивная реплика перехватывает аренду и немедленно становится новым Лидером.""",
    "step_by_step": [
        "Определите структуру ресурса аренды `LeaseLock` с владельцем и временем истечения.",
        "Реализуйте симулятор конкурентной борьбы за лидерство между тремя репликами оператора.",
        "Смоделируйте аварийное падение активного лидера.",
        "Продемонстрируйте автоматический перехват управления резервной репликой (Failover)."
    ],
    "code_blocks": [
        {
            "filename": "leader_election_lease.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"sync"
	"time"
)

type LeaseLock struct {
	mu           sync.Mutex
	Holder       string
	LeaseExpires time.Time
}

func (l *LeaseLock) TryAcquireOrRenew(candidate string, duration time.Duration) bool {
	l.mu.Lock()
	defer l.mu.Unlock()

	now := time.Now()
	// Если аренда свободна или истекла, либо кандидат уже является лидером (продление)
	if l.Holder == "" || now.After(l.LeaseExpires) || l.Holder == candidate {
		l.Holder = candidate
		l.LeaseExpires = now.Add(duration)
		return true
	}
	return false
}

func main() {
	lease := &LeaseLock{}
	leaseDuration := 100 * time.Millisecond

	fmt.Println("=== KUBERNETES LEADER ELECTION SIMULATOR ===")

	// 1. Старт 3 реплик оператора
	replicas := []string{"operator-pod-1", "operator-pod-2", "operator-pod-3"}
	var activeLeader string

	for _, rep := range replicas {
		if lease.TryAcquireOrRenew(rep, leaseDuration) {
			activeLeader = rep
			fmt.Printf("[%s] Successfully acquired LEASE! Becoming ACTIVE LEADER.\n", rep)
			break
		} else {
			fmt.Printf("[%s] Failed to acquire lease. Running in STANDBY mode.\n", rep)
		}
	}

	// 2. Лидер продлевает аренду
	fmt.Printf("\n[Heartbeat] Leader %s renews lease...\n", activeLeader)
	lease.TryAcquireOrRenew(activeLeader, leaseDuration)

	// 3. Авария лидера: лидер упал и больше не продлевает аренду
	fmt.Printf("[CRASH] Leader %s suddenly terminated!\n", activeLeader)
	time.Sleep(150 * time.Millisecond) // Ждем истечения срока аренды

	// 4. Резервная реплика перехватывает лидерство
	standbyCandidate := "operator-pod-2"
	if lease.TryAcquireOrRenew(standbyCandidate, leaseDuration) {
		fmt.Printf("[FAILOVER] %s detected expired lease! Acquired leadership successfully.\n", standbyCandidate)
	}
}
"""
        }
    ],
    "under_the_hood": "Реализация Leader Election в `client-go/tools/leaderelection` использует оптимистическую блокировку на ресурсе `coordination.k8s.io/Lease`. При продлении аренды лидер выполняет `Update` Lease-объекта с инкрементом `acquireTime` и `renewTime`. Если сетевая задержка превышает `RenewDeadline`, лидер добровольно отказывается от лидерства (Step Down), предотвращая Split-Brain.",
    "pitfalls": [
        "Недостаточные права RBAC на ресурс `leases` в группе `coordination.k8s.io`: оператор не сможет создать замок и упадет с паникой на старте.",
        "Слишком агрессивные таймауты аренды (например 1 секунда): при кратковременном сетевом джиттере или GC STW паузе в Go лидер потеряет замок и кластер начнет непрерывно флапать лидерство."
    ],
    "bigtech_interview": "Как предотвратить феномен Split-Brain, если старый лидер оператора испытал долгую GC-паузу и очнулся, когда новая реплика уже перехватила лидерство? Механизм `client-go` Leader Election гарантирует, что если лидер не смог продлить аренду до дедлайна `RenewDeadline`, он немедленно отменяет контекст исполнения `ctx.Done()`. Все фоновые горутины старого лидера обязаны мгновенно прервать операции записи. Кроме того, оптимистическая блокировка `ResourceVersion` в etcd отклонит любые попытки старого лидера сохранить изменения."
})

# Ex 29
exercises.append({
    "num": 29,
    "title": "Сборка легковесного контейнера на базе Google Distroless",
    "task": "Напишите многоэтапный `Dockerfile` (Multi-stage build) для сборки бинарника оператора: этап сборки на базе `golang:1.22-alpine` (с флагами `CGO_ENABLED=0 -ldflags=\"-s -w\"`) и финальный минимальный рантайм-образ на базе `gcr.io/distroless/static:nonroot`. Запустите оператор от непривилегированного пользователя.",
    "theory": r"""Развертывание операторов с правами суперпользователя (`root`) или на базе полновесных ОС-образов (Ubuntu, Debian, полный Alpine) категорически запрещено в защищенных Enterprise-контурах:
- Наличие пакетных менеджеров (`apk`, `apt`), утилит `curl`, `sh`, `bash` дает злоумышленнику готовый инструментарий при компрометации пода.
- Большой размер контейнера (>500 МБ) замедляет скачивание образов нодами при автоскейлинге.

**Золотой стандарт Cloud-Native безопасности:**
1. **Multi-stage сборка:**
   - Этап 1 (`builder`): компиляция статического Go-бинарника с `CGO_ENABLED=0`.
   - Флаги линковщика `-ldflags="-s -w"` вырезают отладочную информацию (DWARF) и таблицу символов, уменьшая размер бинарника на 30–40%.
2. **Финальный образ `gcr.io/distroless/static:nonroot`:**
   - Не содержит ни командных оболочек, ни утилит, ни libc.
   - Содержит только корневые CA-сертификаты (`/etc/ssl/certs/ca-certificates.crt`), tzdata и запись в `/etc/passwd` для пользователя `nonroot:nonroot` (UID 65532).
   - Размер итогового Docker-образа составляет всего **15–25 МБ**!""",
    "step_by_step": [
        "Смоделируйте валидацию Dockerfile манифеста на соответствие лучшим практикам SecOps.",
        "Проверьте наличие директивы `USER 65532:65532` (nonroot).",
        "Проверьте флаги статической компиляции `CGO_ENABLED=0` и `-ldflags=\"-s -w\"`.",
        "Продемонстрируйте структуру минимального контейнера оператора."
    ],
    "code_blocks": [
        {
            "filename": "distroless_dockerfile_validation.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"strings"
)

const TargetDockerfile = `
# Build stage
FROM golang:1.22-alpine AS builder
WORKDIR /workspace
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o manager cmd/main.go

# Production runtime stage
FROM gcr.io/distroless/static:nonroot
WORKDIR /
COPY --from=builder /workspace/manager .
USER 65532:65532

ENTRYPOINT ["/manager"]
`

func AuditDockerfile(content string) (bool, []string) {
	var issues []string

	if !strings.Contains(content, "CGO_ENABLED=0") {
		issues = append(issues, "Missing CGO_ENABLED=0: binary may depend on host glibc")
	}
	if !strings.Contains(content, "-ldflags=\"-s -w\"") {
		issues = append(issues, "Missing stripping flags '-s -w': binary size is not optimal")
	}
	if !strings.Contains(content, "FROM gcr.io/distroless/static:nonroot") {
		issues = append(issues, "Base image is not distroless: potential attack surface")
	}
	if !strings.Contains(content, "USER 65532:65532") {
		issues = append(issues, "Container runs as ROOT! Nonroot user required for security compliance")
	}

	return len(issues) == 0, issues
}

func main() {
	valid, issues := AuditDockerfile(TargetDockerfile)

	fmt.Println("=== DOCKERFILE DISTROLESS SECURITY AUDIT ===")
	fmt.Printf("Audit Passed: %v\n", valid)
	if len(issues) == 0 {
		fmt.Println("Dockerfile 100% compliant with Cloud-Native Enterprise Security standards!")
	} else {
		for _, issue := range issues {
			fmt.Println(" - FAIL:", issue)
		}
	}
}
"""
        }
    ],
    "under_the_hood": "Образ `distroless/static:nonroot` использует UID 65532. В манифесте `PodSecurityContext` для пода оператора обязательно задаются атрибуты: `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false` и `capabilities: drop: [\"ALL\"]`, что гарантирует высший уровень защиты (Restricted Pod Security Standard).",
    "pitfalls": [
        "Сборка с `CGO_ENABLED=1`: бинарник потребует разделяемую библиотеку `glibc`, которая полностью отсутствует в образе `distroless/static`, и контейнер упадет при запуске с ошибкой `no such file or directory`.",
        "Попытка войти в запущенный distroless контейнер через `kubectl exec -it pod -- sh`: в контейнере нет командного процессора `sh`, вход завершится ошибкой. Для отладки используются Ephemeral Debug Containers (`kubectl debug`)."
    ],
    "bigtech_interview": "Почему в production операторах предпочитают Google Distroless, а не минимальный Alpine Linux? В Alpine содержится BusyBox (оболочка /bin/sh, утилиты wget, nc, vi, find) и менеджер пакетов apk. Если злоумышленник найдет способ выполнить команду через баг в коде оператора, он сможет скачать и скомпилировать эксплойт прямо внутри контейнера. В Distroless нет шелла и утилит: любая попытка инъекции команд ОС завершается ошибкой отсутствия исполняемого файла."
})

# Ex 30
exercises.append({
    "num": 30,
    "title": "Сквозная разработка PostgreSQL Operator на Go",
    "task": "Создайте полноценный рабочий оператор базы данных PostgreSQL на Go: описание CRD с параметрами репликации и версий, контроллер, создающий StatefulSet и Service, мониторинг статуса реплик через `pg_stat_replication`, автоматический failover лидера при сбое и graceful-очистка через Finalizers при удалении кластера.",
    "theory": r"""Комплексная архитектура промышленного оператора базы данных:
1. **CRD `PostgresCluster`:** Пользователь задает версию СУБД, число реплик и размер дискового хранилища.
2. **Дочерние ресурсы:**
   - `corev1.ConfigMap` с тюнингованным `postgresql.conf` (shared_buffers, wal_level=replica).
   - `corev1.Secret` со сгенерированными криптографическими паролями репликации.
   - `corev1.Service` (Headless Service для сетевой адресации узлов + ClusterIP для балансировки чтения на реплики).
   - `apps/v1.StatefulSet` для управления стабильной идентичностью подов (`pg-0`, `pg-1`, `pg-2`).
3. **Контрольный цикл (Reconciliation):**
   - Проверка наличия финализатора бэкапов.
   - Синхронизация дочерних ресурсов (StatefulSet, Service).
   - Мониторинг здоровья мастера и выбор новой Primary-ноды при падении.
   - Атомарное обновление подресурса `/status` с условиями `Ready` и `FailoverInProgress`.""",
    "step_by_step": [
        "Определите контракт CRD `PostgresClusterSpec` и `PostgresClusterStatus`.",
        "Реализуйте контроллер `PostgresClusterReconciler` со всеми этапами жизненного цикла.",
        "Запрограммируйте создание дочерних ресурсов с привязкой `OwnerReference`.",
        "Продемонстрируйте примирение нового кластера, обновление статуса и подготовку к failover."
    ],
    "code_blocks": [
        {
            "filename": "postgres_operator_complete.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
	"time"
)

type PostgresClusterSpec struct {
	Version  string
	Replicas int
	Storage  string
}

type PostgresClusterStatus struct {
	ReadyReplicas int
	Primary       string
	Phase         string
}

type PostgresCluster struct {
	Name      string
	Namespace string
	Spec      PostgresClusterSpec
	Status    PostgresClusterStatus
}

type PostgresReconciler struct{}

func (r *PostgresReconciler) Reconcile(ctx context.Context, cluster *PostgresCluster) error {
	fmt.Printf("\n=== [PostgresReconciler] Reconciling cluster '%s/%s' ===\n",
		cluster.Namespace, cluster.Name)

	// 1. Проверка дочернего Headless Service
	fmt.Printf("[Reconcile] Ensuring Headless Service '%s-headless' exists with OwnerRef\n", cluster.Name)

	// 2. Проверка дочернего StatefulSet
	fmt.Printf("[Reconcile] Ensuring StatefulSet '%s-sts' with %d replicas (image: postgres:%s, storage: %s)\n",
		cluster.Name, cluster.Spec.Replicas, cluster.Spec.Version, cluster.Spec.Storage)

	// 3. Вычисление фактического состояния кластера
	observedReady := cluster.Spec.Replicas
	primaryNode := fmt.Sprintf("%s-sts-0", cluster.Name)

	// 4. Обновление статуса
	cluster.Status.ReadyReplicas = observedReady
	cluster.Status.Primary = primaryNode
	cluster.Status.Phase = "Running"

	fmt.Printf("[Reconcile] Status updated: Phase=%s, Primary=%s, ReadyReplicas=%d/%d\n",
		cluster.Status.Phase, cluster.Status.Primary, cluster.Status.ReadyReplicas, cluster.Spec.Replicas)
	return nil
}

func main() {
	cluster := &PostgresCluster{
		Name:      "ha-postgres",
		Namespace: "databases",
		Spec: PostgresClusterSpec{
			Version:  "16.2",
			Replicas: 3,
			Storage:  "50Gi",
		},
		Status: PostgresClusterStatus{Phase: "Pending"},
	}

	reconciler := &PostgresReconciler{}
	err := reconciler.Reconcile(context.Background(), cluster)
	if err != nil {
		panic(err)
	}

	fmt.Println("\nCluster reconciliation finished with success!")
	_ = time.Second
}
"""
        }
    ],
    "under_the_hood": "В промышленных операторах СУБД (Zalando Postgres Operator, CloudNativePG) внутри каждого пода БД запускается специализированный агент-менеджер (например Patroni или собственный Go-демон), который взаимодействует с etcd или Kubernetes API для распределенного консенсуса, гарантируя автоматический failover мастера менее чем за 10 секунд без потери транзакций.",
    "pitfalls": [
        "Использование Deployment вместо StatefulSet для базы данных: поды Deployment имеют случайные имена и не гарантируют сохранение сетевого идентификатора и постоянных томов PersistentVolumeClaim при перезапусках.",
        "Ручной failover без проверки кворума: может привести к Split-Brain, когда два узла считают себя мастером и параллельно принимают транзакции на запись."
    ],
    "bigtech_interview": "Как Cloud-Native PostgreSQL оператор организует процедуру безаварийного обновления минорной версии СУБД (Zero-Downtime Rolling Update)? 1) Оператор последовательно обновляет поды реплик (Read Replicas), дожидаясь синхронизации WAL-логов; 2) Когда все реплики переведены на новую версию, оператор инициирует контролируемый Switchover: принудительно переключает мастер на обновленную реплику; 3) Старый мастер понижается до реплики, обновляется и подключается к новому кластеру. Приложение испытывает кратковременную задержку переключения соединений не более 1–2 секунд."
})

# Ex 31
exercises.append({
    "num": 31,
    "title": "Conversion Webhooks: Плавная миграция схем CRD (v1alpha1 -> v1beta1 -> v1)",
    "task": "Реализуйте конверсионный вебхук на Go для обеспечения обратной совместимости при изменении схемы CRD. Примените архитектуру Hub & Spoke: назначьте версию `v1beta1` в качестве хаба с реализацией интерфейса `conversion.Hub`, а для `v1alpha1` реализуйте интерфейс `conversion.Convertible` с методами `ConvertTo` и `ConvertFrom`. Покажите, как API-сервер прозрачно конвертирует старые манифесты на лету.",
    "theory": r"""С развитием оператора структура CRD неизбежно меняется (переименование полей, объединение структур).
Как обновить схему без остановки кластера и без принуждения всех команд компании одновременно переписывать тысячи YAML файлов?

Архитектура **Conversion Webhooks (Конверсионные вебхуки)**:
В Kubernetes применяется паттерн **Hub and Spoke**:
1. **Hub Version (Хаб-версия):** Выбирается центральная стабильная версия API (например `v1beta1`). Она реализует маркерный интерфейс:
   `func (*DatabaseCluster) Hub() {}`
2. **Spoke Versions (Версии-спицы):** Все остальные версии (`v1alpha1`, `v1`) реализуют интерфейс `conversion.Convertible`:
   - `ConvertTo(hub conversion.Hub) error` — конвертация старой версии в центральный Hub.
   - `ConvertFrom(hub conversion.Hub) error` — конвертация из центрального Hub в старую версию.
3. **Прозрачная работа:** Когда клиент запрашивает старую версию `v1alpha1`, API-сервер на лету вызывает конверсионный вебхук оператора, возвращая объект в запрошенном формате!""",
    "step_by_step": [
        "Определите старую версию структуры `V1Alpha1Cluster` со старыми именами полей.",
        "Определите целевую версию Hub `V1Beta1Cluster` с оптимизированной схемой.",
        "Реализуйте методы `ConvertTo` и `ConvertFrom` для двунаправленной трансформации данных.",
        "Продемонстрируйте успешную сквозную конвертацию данных с сохранением семантики."
    ],
    "code_blocks": [
        {
            "filename": "conversion_webhook_hub_spoke.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
)

// V1Beta1Cluster выступает в качестве Hub версии
type V1Beta1Cluster struct {
	Name        string
	NodeCount   int    // Новое унифицированное поле
	StorageSize string // Новое имя
}

func (h *V1Beta1Cluster) Hub() {}

// V1Alpha1Cluster выступает в роли Spoke версии
type V1Alpha1Cluster struct {
	Name            string
	Replicas        int    // Старое имя поля
	DiskCapacity    string // Старое имя поля
}

func (src *V1Alpha1Cluster) ConvertTo(dst *V1Beta1Cluster) error {
	dst.Name = src.Name
	dst.NodeCount = src.Replicas
	dst.StorageSize = src.DiskCapacity
	return nil
}

func (dst *V1Alpha1Cluster) ConvertFrom(src *V1Beta1Cluster) error {
	dst.Name = src.Name
	dst.Replicas = src.NodeCount
	dst.DiskCapacity = src.StorageSize
	return nil
}

func main() {
	// Симуляция: пользователь прислал старый манифест v1alpha1
	oldManifest := V1Alpha1Cluster{
		Name:         "legacy-postgres",
		Replicas:     3,
		DiskCapacity: "100Gi",
	}

	// 1. Конвертация v1alpha1 -> v1beta1 (Hub)
	hub := &V1Beta1Cluster{}
	if err := oldManifest.ConvertTo(hub); err != nil {
		panic(err)
	}

	fmt.Println("=== KUBERNETES CONVERSION WEBHOOK (HUB & SPOKE) ===")
	fmt.Printf("Converted to Hub (v1beta1): Name=%s, NodeCount=%d, StorageSize=%s\n",
		hub.Name, hub.NodeCount, hub.StorageSize)

	// 2. Конвертация обратно v1beta1 -> v1alpha1 для старого клиента
	restored := &V1Alpha1Cluster{}
	if err := restored.ConvertFrom(hub); err != nil {
		panic(err)
	}

	fmt.Printf("Restored Spoke  (v1alpha1): Name=%s, Replicas=%d, DiskCapacity=%s\n",
		restored.Name, restored.Replicas, restored.DiskCapacity)
}
"""
        }
    ],
    "under_the_hood": "В etcd объект всегда сохраняется СТРОГО в версии Hub (версия, помеченная как `storage: true` в CRD). При выполнении `kubectl get databaseclusters.v1alpha1` API-сервер считывает Hub-версию из etcd, вызывает конверсионный вебхук по HTTPS и отдает клиенту ответ в схеме v1alpha1.",
    "pitfalls": [
        "Потеря данных (Lossy Conversion): если в старой версии `v1alpha1` были поля, отсутствующие в схеме `v1beta1`, при обратной конвертации эти поля будут утеряны. Для сохранения используется аннотация `conversion.kubernetes.io/preserved-unknown-fields`.",
        "Паника при кастинге интерфейса `conversion.Hub`: всегда безопасно проверяйте приведение типов `dst, ok := hub.(*V1Beta1Cluster)`."
    ],
    "bigtech_interview": "Почему паттерн Hub and Spoke эффективнее прямого маппинга 'каждый с каждым' (Point-to-Point) при конвертации N версий CRD? При direct-маппинге для $N$ версий требуется написать $N \\times (N - 1)$ конвертеров ($O(N^2)$ сложность). При использовании Hub & Spoke любая версия конвертируется только в/из центрального Hub, что требует всего $2 \\times (N - 1)$ методов ($O(N)$ сложность) и радикально снижает вероятность багов при миграции схем."
})

# Ex 32
exercises.append({
    "num": 32,
    "title": "Server-Side Apply (SSA) вместо Read-Modify-Write",
    "task": "Откажитесь от устаревшего и подверженного гонкам паттерна `Get -> Mutate -> Update` в пользу Server-Side Apply. Используйте `client.Patch` с типом `client.Apply` и типизированными конфигураторами (`applyconfigurations`). Докажите, как механизм Field Management в API-сервере предотвращает конфликты версий и защищает поля, управляемые другими контроллерами (например, HPA или внешними аннотаторами).",
    "theory": r"""Традиционный паттерн обновления ресурсов в Kubernetes:
`r.Get(ctx, key, obj)` -> `obj.Spec.Replicas = 3` -> `r.Update(ctx, obj)`.

Проблемы классического подхода:
1. **Гонки версий (Optimistic Locking Conflicts):** Требует сотен вызовов `RetryOnConflict`.
2. **Затирание чужих полей:** Если Horizontal Pod Autoscaler (HPA) управляет `spec.replicas`, а внешний Service Mesh контроллер инжектирует аннотации, классический `r.Update()` затирает чужие изменения!

Решение: **Server-Side Apply (SSA)** (стандарт Kubernetes 1.22+):
1. **Field Ownership (Владение полями):** API-сервер отслеживает, какой контроллер (Field Manager) владеет каждым конкретным полем ресурса (`metadata.managedFields`).
2. **Декларативное наложение:** Оператор отправляет только те поля, за которые он отвечает, с указанием имени менеджера:
   `r.Patch(ctx, obj, client.Apply, client.FieldOwner("db-operator"), client.ForceOwnership)`
3. **Разрешение конфликтов:** Если два контроллера пытаются одновременно управлять одним полем, API-сервер возвращает явный конфликт владения, защищая целостность системы.""",
    "step_by_step": [
        "Определите модель структуры управления полями `ManagedField`.",
        "Реализуйте симулятор механизма Server-Side Apply с разрешением владения полями.",
        "Смоделируйте независимое управление: оператор управляет образом СУБД, а HPA управляет числом реплик.",
        "Докажите, что SSA предотвращает взаимное затирание полей контроллерами."
    ],
    "code_blocks": [
        {
            "filename": "server_side_apply_ssa.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
)

type FieldManagerRecord struct {
	Manager string
	Fields  map[string]any
}

type SSAObject struct {
	Name          string
	ManagedFields map[string]FieldManagerRecord
}

func (o *SSAObject) Apply(manager string, patch map[string]any, force bool) error {
	for fieldName, newVal := range patch {
		for existingMgr, record := range o.ManagedFields {
			if existingMgr != manager {
				if _, exists := record.Fields[fieldName]; exists && !force {
					return fmt.Errorf("conflict: field '%s' is owned by manager '%s'", fieldName, existingMgr)
				}
			}
		}
	}

	rec, exists := o.ManagedFields[manager]
	if !exists {
		rec = FieldManagerRecord{Manager: manager, Fields: make(map[string]any)}
	}
	for k, v := range patch {
		rec.Fields[k] = v
	}
	o.ManagedFields[manager] = rec
	return nil
}

func main() {
	obj := &SSAObject{
		Name:          "postgres-cluster",
		ManagedFields: make(map[string]FieldManagerRecord),
	}

	fmt.Println("=== SERVER-SIDE APPLY (SSA) FIELD MANAGEMENT ===")

	// 1. Оператор применяет желаемый образ и настройки
	operatorPatch := map[string]any{
		"spec.image": "postgres:16.2",
	}
	_ = obj.Apply("db-operator", operatorPatch, false)
	fmt.Printf("[SSA] 'db-operator' applied spec.image\n")

	// 2. Внешний автоскейлер HPA управляет количеством реплик
	hpaPatch := map[string]any{
		"spec.replicas": 5,
	}
	_ = obj.Apply("kube-hpa-controller", hpaPatch, false)
	fmt.Printf("[SSA] 'kube-hpa-controller' applied spec.replicas\n")

	// 3. Попытка оператора изменить поле, принадлежащее HPA (без флага force) вызовет конфликт
	conflictingPatch := map[string]any{
		"spec.replicas": 3,
	}
	err := obj.Apply("db-operator", conflictingPatch, false)
	fmt.Printf("[SSA Conflict] Operator modifying HPA-owned field -> Error: %v\n", err)

	fmt.Println("\nAll fields safely co-managed without overwriting!")
}
"""
        }
    ],
    "under_the_hood": "В `client-go` генератор создает типизированные структуры конфигураций (**ApplyConfigurations**, пакет `applyconfigurations`). Контроллер пишет: `sts := appsv1ac.StatefulSet(name, ns).WithSpec(appsv1ac.StatefulSetSpec().WithReplicas(3))`, что обеспечивает полную типобезопасность на этапе компиляции без использования строковых карт `map[string]any`.",
    "pitfalls": [
        "Случайная смена имени `FieldOwner`: если оператор в разных версиях передает разные имена менеджера (например `db-operator` и `database-operator`), API-сервер сочтет их двумя разными контроллерами и выбросит ошибку конфликта.",
        "Использование классического `r.Update()` поверх ресурса, управляемого через SSA: обычный Update перезаписывает блок `managedFields`, разрушая карту владения полями."
    ],
    "bigtech_interview": "В чем архитектурное преимущество Server-Side Apply над Client-Side Apply (kubectl apply с аннотацией last-applied-configuration)? Client-Side Apply вычисляет трехсторонний diff (Three-Way Merge) на клиенте и хранит гигантский JSON-снимок в аннотации `kubectl.kubernetes.io/last-applied-configuration`. Это ограничено лимитом размера аннотаций (256 КБ) и не поддерживает концепцию совместного владения полями несколькими контроллерами. Server-Side Apply вычисляет слияние на сервере etcd с точным отслеживанием менеджера каждого поля."
})

# Ex 33
exercises.append({
    "num": 33,
    "title": "Плавный перезапуск StatefulSet с сохранением кворума (Quorum-Aware Rolling Update)",
    "task": "Реализуйте контроллер, управляющий распределенной базой данных с кворумом (Raft / etcd / CockroachDB). Вместо стандартного механизма обновлений Kubernetes, оператор перехватывает управление ротацией подов: последовательно переводит поды в режим обслуживания, проверяет синхронизацию данных и кворума кластера перед перезапуском каждого следующего узла.",
    "theory": r"""Стандартный механизм обновления StatefulSet в Kubernetes (`RollingUpdateStrategy`):
- Перезапускает поды строго по одному в порядке убывания индексов (`pod-2` -> `pod-1` -> `pod-0`).
- Проверяет только факт `PodReady` (прохождение readinessProbe контейнера).

Почему этого категорически недостаточно для распределенных кластеров с консенсусом (Raft, etcd, Kafka, ClickHouse)?
1. **Проблема несинхронизированного кворума:** Под может пройти проверку `readinessProbe` (процесс запустился), но еще не успеть среплицировать терабайты данных или догнать журнал Raft. Если Kubernetes немедленно погасит следующий узел, кластер потеряет кворум и наступит отказ в обслуживании (Outage)!
2. **Переключение лидерства:** Перед перезапуском узла-лидера (Primary) оператор должен сначала мягко передать лидерство другому узлу (Step Down / Demote), чтобы избежать разрыва клиентских сессий.

Решение: **Оператор переводит StatefulSet в `updateStrategy.type: OnDelete`** и берет управление перезапуском подов полностью на себя.""",
    "step_by_step": [
        "Определите модель узла кластера `RaftNode` с флагами готовности, синхронизации и статусом мастера.",
        "Реализуйте валидатор наличия кворума `HasQuorum(nodes)`.",
        "Запрограммируйте алгоритм поочередного перезапуска: мягкий перенос лидерства, ожидание полной синхронизации WAL.",
        "Продемонстрируйте безопасный перезапуск 3-узлового кластера без потери кворума."
    ],
    "code_blocks": [
        {
            "filename": "quorum_aware_rolling_update.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"time"
)

type RaftNode struct {
	ID        string
	IsLeader  bool
	IsSynced  bool
	IsHealthy bool
}

func HasQuorum(nodes []RaftNode) bool {
	healthyCount := 0
	for _, n := range nodes {
		if n.IsHealthy && n.IsSynced {
			healthyCount++
		}
	}
	return healthyCount >= (len(nodes)/2 + 1)
}

func PerformQuorumRollingUpdate(nodes []RaftNode) error {
	fmt.Println("=== STARTING QUORUM-AWARE ROLLING UPDATE ===")

	for i := range nodes {
		fmt.Printf("\n[Step %d/3] Preparing to update node: %s\n", i+1, nodes[i].ID)

		// 1. Проверяем кворум кластера
		if !HasQuorum(nodes) {
			return fmt.Errorf("ABORT: Quorum lost! Refusing to restart node %s", nodes[i].ID)
		}

		// 2. Если узел является лидером, выполняем мягкий transfer leadership
		if nodes[i].IsLeader {
			fmt.Printf("[Failover] Node %s is LEADER! Gracefully stepping down...\n", nodes[i].ID)
			nodes[i].IsLeader = false
			// Передаем лидерство следующему здоровому узлу
			nextIdx := (i + 1) % len(nodes)
			nodes[nextIdx].IsLeader = true
			fmt.Printf("[Failover] New leader elected: %s\n", nodes[nextIdx].ID)
		}

		// 3. Перезапуск узла
		fmt.Printf("[Restart] Terminating and upgrading node %s...\n", nodes[i].ID)
		nodes[i].IsHealthy = false
		nodes[i].IsSynced = false
		time.Sleep(30 * time.Millisecond) // Имитация перезапуска

		nodes[i].IsHealthy = true
		fmt.Printf("[Health] Node %s process started. Waiting for Raft log catch-up...\n", nodes[i].ID)

		time.Sleep(30 * time.Millisecond) // Имитация репликации данных
		nodes[i].IsSynced = true
		fmt.Printf("[Synchronized] Node %s fully caught up! Safe to proceed to next node.\n", nodes[i].ID)
	}

	return nil
}

func main() {
	cluster := []RaftNode{
		{ID: "raft-node-0", IsLeader: true, IsSynced: true, IsHealthy: true},
		{ID: "raft-node-1", IsLeader: false, IsSynced: true, IsHealthy: true},
		{ID: "raft-node-2", IsLeader: false, IsSynced: true, IsHealthy: true},
	}

	err := PerformQuorumRollingUpdate(cluster)
	fmt.Printf("\nRolling update result: Success=%v, Error=%v\n", err == nil, err)
}
"""
        }
    ],
    "under_the_hood": "При использовании стратегии `OnDelete` контроллер StatefulSet в Kubernetes не трогает существующие поды при изменении шаблона `spec.template`. Оператор сам выбирает, какой под удалить (`client.Delete(pod)`). После удаления Kubernetes воссоздает под с новым шаблоном, а оператор ждет восстановления консенсуса перед удалением следующего.",
    "pitfalls": [
        "Полагание на стандартный `readinessProbe` контейнера: probe проверяет HTTP/TCP порт, но ничего не знает о лаге репликации или наличии кворума в распределенном протоколе.",
        "Одновременный перезапуск двух узлов при сетевом сбое: мгновенно уничтожает кворум и переводит кластер в Read-Only режим."
    ],
    "bigtech_interview": "Как в распределенных базах данных гарантировать отсутствие Split-Brain во время передачи лидерства при плановом перезапуске? Используется двухфазная процедура Step-Down: 1) Лидер прекращает прием новых запросов на запись; 2) Отправляет RPC команду передачи лидерства наиболее синхронизированной реплике (`Raft Leadership Transfer`); 3) Ждет подтверждения, что новая реплика увеличила Term и получила кворум голосов; 4) Только после этого старый узел безопасно перезапускается."
})

# Ex 34
exercises.append({
    "num": 34,
    "title": "Управление Rate Limiting и очередью Reconcile (Custom RateLimiter)",
    "task": "Настройте кастомные параметры контроллерной очереди `workqueue` в Kubebuilder: сконфигурируйте `workqueue.NewMaxOfRateLimiter` с использованием `ItemExponentialFailureRateLimiter` (базовая задержка 5 мс, максимум 1000 с) и `BucketRateLimiter` (защита от перегрузки API-сервера). Протестируйте поведение контроллера при массовых сетевых отказах управляемых ресурсов.",
    "theory": r"""Когда управляемая инфраструктура переживает аварию (например 500 баз данных одновременно потеряли связь с хранилищем), наивный контроллер начинает бомбардировать API-сервер повторными запросами Reconcile, вызывая каскадный отказ контрольной плоскости.

**Композитный Rate Limiter очереди `workqueue`:**
Библиотека `client-go` использует связку **`workqueue.NewMaxOfRateLimiter`**, объединяющую два независимых алгоритма:
1. **`ItemExponentialFailureRateLimiter` (Поэлементный экспоненциальный лимитер):**
   - Отслеживает число неудач для каждого конкретного ресурса.
   - Базовая задержка: 5 мс, множитель: 2.
   - Попытка 1: 5ms, попытка 2: 10ms, попытка 3: 20ms ... до 1000s.
   - Защищает от частого перезапуска одного сбойного объекта.
2. **`BucketRateLimiter` (Глобальный Token Bucket лимитер):**
   - Ограничивает общий глобальный RPS всех повторов (например максимум 100 повторов в секунду).
   - Защищает API-сервер Kubernetes от лавинообразной перегрузки (Thundering Herd).
`NewMaxOfRateLimiter` выбирает максимальную задержку из двух лимитеров, обеспечивая абсолютную стабильность.""",
    "step_by_step": [
        "Определите структуры поэлементного экспоненциального и глобального bucket лимитеров.",
        "Реализуйте композитный `MaxOfRateLimiter`.",
        "Смоделируйте серию повторных сбоев для одного ресурса и замерьте экспоненциальный рост задержки.",
        "Продемонстрируйте сброс счетчика сбоев при успешном завершении примирения."
    ],
    "code_blocks": [
        {
            "filename": "workqueue_custom_ratelimiter.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"math"
	"time"
)

type ItemExponentialFailureRateLimiter struct {
	baseDelay time.Duration
	maxDelay  time.Duration
	failures  map[string]int
}

func NewExponentialLimiter(base, max time.Duration) *ItemExponentialFailureRateLimiter {
	return &ItemExponentialFailureRateLimiter{
		baseDelay: base,
		maxDelay:  max,
		failures:  make(map[string]int),
	}
}

func (l *ItemExponentialFailureRateLimiter) When(item string) time.Duration {
	exp := l.failures[item]
	l.failures[item]++

	// 2^exp
	factor := math.Pow(2, float64(exp))
	backoff := time.Duration(float64(l.baseDelay) * factor)

	if backoff > l.maxDelay || backoff < 0 {
		return l.maxDelay
	}
	return backoff
}

func (l *ItemExponentialFailureRateLimiter) Forget(item string) {
	delete(l.failures, item)
}

func main() {
	limiter := NewExponentialLimiter(5*time.Millisecond, 1000*time.Millisecond)
	targetCluster := "databases/postgres-faulty"

	fmt.Println("=== WORKQUEUE EXPONENTIAL RATE LIMITER TEST ===")
	for attempt := 1; attempt <= 6; attempt++ {
		delay := limiter.When(targetCluster)
		fmt.Printf("Failure #%d -> Calculated Requeue Delay: %v\n", attempt, delay)
	}

	// Успешное примирение: сброс счетчика ошибок
	limiter.Forget(targetCluster)
	fmt.Printf("\nResource recovered! After Forget(): Requeue Delay: %v\n", limiter.When(targetCluster))
}
"""
        }
    ],
    "under_the_hood": "Метод `Forget(item)` удаляет ключ из мапы неудач. Если разработчик забудет вызвать `q.Forget(item)` при успешном завершении Reconcile, то при следующем случайном сбое через месяц задержка сразу начнется с максимального значения (1000s), что недопустимо.",
    "pitfalls": [
        "Отсутствие верхнего предела задержки `maxDelay`: при длительном сбое задержка экспоненциально превысит недели или вызовет переполнение целого числа `time.Duration`.",
        "Забытый вызов `q.Forget(item)` при успешном Reconcile: история ошибок сохраняется вечно, искажая планирование повторов."
    ],
    "bigtech_interview": "Почему стандартный RateLimiter очереди в client-go сочетает BucketRateLimiter и ExponentialFailureRateLimiter? Если в кластере произойдет массовый сетевой отказ тысячи баз данных, ExponentialFailureRateLimiter на первой попытке назначит всем задержку 5 мс. В результате через 5 мс тысячи подов одновременно ломанутся в API-сервер (Thundering Herd). Глобальный BucketRateLimiter сдерживает общий суммарный поток повторов безопасным лимитом, предотвращая DoS-атаку на kube-apiserver."
})

# Ex 35
exercises.append({
    "num": 35,
    "title": "Сборка и публикация Operator Lifecycle Manager (OLM) Bundle",
    "task": "Упакуйте разработанный оператор в промышленный формат каталога Kubernetes / OpenShift: сгенерируйте манифесты `ClusterServiceVersion` (CSV) с описанием прав RBAC, примеров CRD и поддерживаемых режимов установки (`AllNamespaces`, `OwnNamespace`). Проведите валидацию метаданных бандла с помощью утилиты `operator-sdk bundle validate`.",
    "theory": r"""Для распространения операторов в корпоративных каталогах (OperatorHub.io, Red Hat OpenShift, платформы Kubernetes) используется стандарт **Operator Lifecycle Manager (OLM)**.

Структура **OLM Bundle**:
- **`manifests/`:**
  - `storage.mycompany.com_databaseclusters.yaml` — схемы CRD.
  - `db-operator.clusterserviceversion.yaml` (**CSV**) — ключевой манифест каталога:
    - Метаданные: название, версия SemVer, иконка в Base64, контакты мейнтейнеров.
    - Описание прав RBAC и ServiceAccount.
    - `installModes`: поддерживаемые режимы видимости (`OwnNamespace`, `SingleNamespace`, `MultiNamespace`, `AllNamespaces`).
    - `customresourcedefinitions`: ссылки на CRD с примерами манифестов (`alm-examples`).
- **`metadata/annotations.yaml`:** Метаданные бандла для сборки OCI-контейнера.
Бандл упаковывается в стандартный Docker/OCI образ и публикуется в реестр артефактов.""",
    "step_by_step": [
        "Определите модель манифеста `ClusterServiceVersion` с метаданными и режимами установки.",
        "Реализуйте валидатор структуры OLM бандла на наличие обязательных полей CSV.",
        "Проверьте корректность SemVer версии оператора и указания прав доступа.",
        "Продемонстрируйте прохождение валидации бандла для публикации в OperatorHub."
    ],
    "code_blocks": [
        {
            "filename": "olm_bundle_validation.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"strings"
)

type InstallModeType string

const (
	InstallModeOwnNamespace   InstallModeType = "OwnNamespace"
	InstallModeAllNamespaces  InstallModeType = "AllNamespaces"
)

type ClusterServiceVersion struct {
	Name         string
	Version      string
	DisplayName  string
	Description  string
	InstallModes map[InstallModeType]bool
	CRDNames     []string
}

func ValidateOLMBundle(csv ClusterServiceVersion) (bool, []string) {
	var errs []string
	if csv.Name == "" {
		errs = append(errs, "CSV 'name' is required")
	}
	if csv.Version == "" || !strings.HasPrefix(csv.Version, "v") && !strings.Contains(csv.Version, ".") {
		errs = append(errs, "CSV 'version' must follow SemVer format")
	}
	if !csv.InstallModes[InstallModeAllNamespaces] && !csv.InstallModes[InstallModeOwnNamespace] {
		errs = append(errs, "At least one InstallMode (AllNamespaces or OwnNamespace) must be supported")
	}
	if len(csv.CRDNames) == 0 {
		errs = append(errs, "CSV must define owned CustomResourceDefinitions")
	}

	return len(errs) == 0, errs
}

func main() {
	csv := ClusterServiceVersion{
		Name:        "db-operator.v1.0.0",
		Version:     "1.0.0",
		DisplayName: "Enterprise PostgreSQL Operator",
		Description: "Production-grade PostgreSQL clustering, failover, and automated backups",
		InstallModes: map[InstallModeType]bool{
			InstallModeOwnNamespace:  true,
			InstallModeAllNamespaces: true,
		},
		CRDNames: []string{"databaseclusters.storage.mycompany.com"},
	}

	valid, issues := ValidateOLMBundle(csv)

	fmt.Println("=== OPERATOR LIFECYCLE MANAGER (OLM) BUNDLE VALIDATION ===")
	fmt.Printf("Bundle: %s (v%s)\n", csv.DisplayName, csv.Version)
	fmt.Printf("Validation PASSED: %v\n", valid)
	if len(issues) > 0 {
		for _, issue := range issues {
			fmt.Println(" -", issue)
		}
	} else {
		fmt.Println("Ready for packaging into OCI registry for OperatorHub.io publication!")
	}
}
"""
        }
    ],
    "under_the_hood": "Утилита `operator-sdk bundle validate ./bundle` производит глубокую проверку манифестов: проверяет совпадение прав ServiceAccount с развертываемым бинарником, валидирует схемы `alm-examples` против сгенерированных CRD и контролирует цепочки обновлений `replaces` / `skips` для плавного апгрейда оператора.",
    "pitfalls": [
        "Несовпадение имени поля `replaces: db-operator.v0.9.0`: если указать несуществующую предыдущую версию, OLM не сможет построить граф зависимостей обновлений и откажется обновлять оператор.",
        "Отсутствие примеров манифестов в аннотации `alm-examples`: в веб-интерфейсе OpenShift / Kubernetes Dashboard пользователи увидят пустые формы создания ресурса."
    ],
    "bigtech_interview": "Как Operator Lifecycle Manager (OLM) управляет автоматическим бесшовным обновлением версий операторов? OLM поддерживает два канала обновления: Automatic и Manual в рамках `Subscription`. При появлении нового бандла в `CatalogSource` OLM проверяет граф апгрейдов по полю `replaces` в CSV. Если канал автоматический, OLM разворачивает новый Deployment оператора параллельно со старым, проводит проверку readinessProbe, переключает Lease блокировку лидера и удаляет старый Pod, гарантируя zero-downtime апгрейд."
})

# Ex 36
exercises.append({
    "num": 36,
    "title": "Автоматическое управление сертификатами для Webhooks через cert-manager",
    "task": "Сконфигурируйте автоматический выпуск TLS-сертификатов для валидационных и конверсионных вебхуков оператора с помощью cert-manager: настройка Issuer, Certificate и аннотации `cert-manager.io/inject-ca-from` в манифестах `ValidatingWebhookConfiguration`. Устраните необходимость ручной генерации и монтирования секретов с ключами.",
    "theory": r"""Ручная генерация TLS-сертификатов для Admission Webhooks чревата простоями при истечении срока действия ключей (Cert Expiration Outage).

Архитектура автоматизации TLS с **`cert-manager`**:
1. **Issuer (Эмитент):** Создается ресурс `cert-manager.io/v1 Issuer` с самоподписанным CA:
   ```yaml
   apiVersion: cert-manager.io/v1
   kind: Issuer
   metadata:
     name: webhook-selfsigned-issuer
   spec:
     selfSigned: {}
   ```
2. **Certificate (Сертификат):** cert-manager генерирует TLS-сертификат и монтирует его в секрет `webhook-server-cert`:
   - DNS-имена: `[service-name].[namespace].svc`, `[service-name].[namespace].svc.cluster.local`.
3. **CA-Injector:** Специальный агент cert-manager отслеживает аннотацию `cert-manager.io/inject-ca-from: [namespace]/[certificate-name]` на манифесте `MutatingWebhookConfiguration` и автоматически прописывает Base64-закодированный CA-сертификат в поле `clientConfig.caBundle`.""",
    "step_by_step": [
        "Определите модель конфигурации TLS инъекции `CAInjectionConfig`.",
        "Реализуйте валидацию соответствия DNS-имен сервиса вебхука и параметров аннотации.",
        "Смоделируйте автоматическую подстановку публичного CA бандла в конфигурацию вебхука.",
        "Продемонстрируйте проверку валидности HTTPS соединения API-сервера с вебхуком."
    ],
    "code_blocks": [
        {
            "filename": "cert_manager_webhook_automation.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"strings"
)

type WebhookManifestConfig struct {
	Name        string
	Namespace   string
	ServiceName string
	Annotation  string
	CABundle    string
}

func InjectCABundle(cfg *WebhookManifestConfig, generatedCA string) error {
	expectedAnnotation := fmt.Sprintf("%s/%s-cert", cfg.Namespace, cfg.ServiceName)
	if !strings.Contains(cfg.Annotation, expectedAnnotation) {
		return fmt.Errorf("invalid inject-ca-from annotation: expected '%s', got '%s'",
			expectedAnnotation, cfg.Annotation)
	}

	cfg.CABundle = generatedCA
	return nil
}

func main() {
	webhookConfig := &WebhookManifestConfig{
		Name:        "databasecluster-validating-webhook",
		Namespace:   "operators",
		ServiceName: "db-operator-webhook-service",
		Annotation:  "operators/db-operator-webhook-service-cert",
	}

	fakeCACert := "MIIB...SIMULATED_CERT_MANAGER_PUBLIC_CA_BUNDLE...AQAB"

	fmt.Println("=== CERT-MANAGER WEBHOOK CA INJECTION TEST ===")
	err := InjectCABundle(webhookConfig, fakeCACert)
	if err != nil {
		panic(err)
	}

	fmt.Printf("CA Bundle successfully injected into Webhook Configuration!\n")
	fmt.Printf("Webhook:   %s\nCABundle:  %s\n", webhookConfig.Name, webhookConfig.CABundle[:20]+"...")
}
"""
        }
    ],
    "under_the_hood": "Контроллер `cainjector` использует Watch-подписку на секреты и конфигурации вебхуков. При любой ротации ключей cert-manager генерирует новый приватный ключ и сертификат, сохраняет в секрет, а cainjector на лету патчит `ValidatingWebhookConfiguration` без необходимости перезапуска самого контроллера.",
    "pitfalls": [
        "Неустановленный компонент `cert-manager-cainjector`: секрет создастся, но поле `caBundle` в манифесте вебхука останется пустым, приводя к ошибке `x509: certificate signed by unknown authority`.",
        "Несовпадение Namespace сервиса и секрета сертификата."
    ],
    "bigtech_interview": "Как cert-manager предотвращает простои при плановой ротации TLS-сертификатов вебхуков оператора? cert-manager обновляет сертификат за 30 дней до истечения срока (`renewBefore: 720h`). Сначала генерируется новый секрет с сертификатом, монтируемый в поды через Secret Volume (Go автоматически подхватывает новые сертификаты без рестарта через `tls.Config.GetCertificate`). Затем `cainjector` обновляет `caBundle` в API-сервере. Процедура проходит со 100% Zero-Downtime."
})

# Ex 37
exercises.append({
    "num": 37,
    "title": "Наблюдение за внешними ресурсами (Watch External / Third-Party APIs)",
    "task": "Спроектируйте оператор, согласующий состояние не только объектов Kubernetes, но и облачной инфраструктуры (например, создание топика в Managed Kafka или бакета в S3). Организуйте фоновый опрос или подписку на вебхуки внешнего API и передавайте синтетические события в очередь Reconcile контроллера с помощью `builder.Watches(&source.Channel{...}, &handler.EnqueueRequestForObject{})`.",
    "theory": r"""Современные операторы часто выступают в роли контроллеров гибридной инфраструктуры (Crossplane, AWS ACK, Google Config Connector).
Они управляют ресурсами **за пределами кластера Kubernetes**:
- Создание базы данных в Amazon RDS или Cloud SQL.
- Создание топика в Managed Apache Kafka.
- Выделение DNS-записей в Cloudflare.

Проблема согласования внешних систем:
Внешние облачные API не имеют встроенного Kubernetes Watch.
Решение: **Паттерн Synthetic Events через `source.Channel`**
1. Фоновый воркер (Poller) периодически опрашивает внешнее REST API провайдера (например AWS SDK `DescribeDBInstances`).
2. При обнаружении изменений (статус инстанса изменился с `creating` на `available`) воркер генерирует **синтетическое событие** `event.GenericEvent`.
3. Событие отправляется в канал Go, подключенный к `controller-runtime`.
4. Контроллер запускает `Reconcile`, обновляя `.status` кастомного ресурса.""",
    "step_by_step": [
        "Определите модель внешнего ресурса `ExternalCloudResource`.",
        "Реализуйте фоновый опросчик внешнего облачного API (Cloud Poller).",
        "Смоделируйте генерацию синтетических событий при обнаружении внешнего дрифта.",
        "Продемонстрируйте передачу событий в очередь Reconcile контроллера."
    ],
    "code_blocks": [
        {
            "filename": "watch_external_cloud_api.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"time"
)

type CloudDatabaseState struct {
	InstanceID string
	Status     string // "CREATING", "AVAILABLE", "FAILED"
}

type SyntheticEvent struct {
	K8sResourceName string
	Status          string
}

func CloudResourcePoller(externalAPI func() CloudDatabaseState, eventChan chan<- SyntheticEvent) {
	lastKnownStatus := ""
	for i := 0; i < 3; i++ {
		time.Sleep(30 * time.Millisecond)
		current := externalAPI()
		if current.Status != lastKnownStatus {
			fmt.Printf("[Cloud Poller] Detected status change in AWS RDS: %s -> %s\n",
				lastKnownStatus, current.Status)
			lastKnownStatus = current.Status
			eventChan <- SyntheticEvent{
				K8sResourceName: "cloud-pg-cluster",
				Status:          current.Status,
			}
		}
	}
}

func main() {
	eventChan := make(chan SyntheticEvent, 5)

	// Имитация внешнего облачного API (переход CREATING -> AVAILABLE)
	step := 0
	mockAWSAPI := func() CloudDatabaseState {
		step++
		if step == 1 {
			return CloudDatabaseState{InstanceID: "rds-123", Status: "CREATING"}
		}
		return CloudDatabaseState{InstanceID: "rds-123", Status: "AVAILABLE"}
	}

	fmt.Println("=== KUBERNETES WATCH EXTERNAL CLOUD APIS ===")
	go CloudResourcePoller(mockAWSAPI, eventChan)

	for evt := range eventChan {
		fmt.Printf("[Reconcile Triggered] Updating K8s CRD '%s' status to '%s'\n",
			evt.K8sResourceName, evt.Status)
		if evt.Status == "AVAILABLE" {
			break
		}
	}
}
"""
        }
    ],
    "under_the_hood": "Пакет `controller-runtime/pkg/source` предоставляет готовый адаптер `source.Channel(chan event.GenericEvent, &handler.EnqueueRequestForObject{})`. Он связывает поток кастомных Go-структур с внутренней очередью `workqueue`, обеспечивая точно такие же гарантии идемпотентности и дедупликации, как и для нативных ресурсов Kubernetes.",
    "pitfalls": [
        "Слишком частый опрос внешних API (например раз в секунду): приводит к исчерпанию лимитов облачных провайдеров (AWS API Throttling / Rate Exceeded).",
        "Блокировка отправки в канал при отсутствии слушателя: используйте неблокирующий select или буферизованные каналы."
    ],
    "bigtech_interview": "Как в Crossplane или AWS ACK минимизируют затраты на опрос тысяч внешних облачных ресурсов? Применяется гибридная модель: 1) Большой интервал базового опроса (Poll Interval 5–15 минут); 2) Подписка на шину событий провайдера (AWS EventBridge, GCP Cloud Pub/Sub, Azure Event Grid) через Webhook-эндпоинт оператора, что обеспечивает мгновенную реакцию за миллисекунды без лишних polling-запросов."
})

# Ex 38
exercises.append({
    "num": 38,
    "title": "Ограничение области видимости оператора (Namespace-Scoped Multi-Tenancy)",
    "task": "По умолчанию операторы отслеживают весь кластер, что требует прав ClusterRole и потребляет много памяти на кэширование информеров. Сконфигурируйте оператор для работы строго в рамках заданного набора пространств имен с помощью `cache.Options{DefaultNamespaces: map[string]cache.Config{...}}`. Покажите изоляцию доступа в мультиарендных корпоративных кластерах.",
    "theory": r"""В корпоративных мультиарендных (Multi-Tenant) кластерах предоставление оператору кластерных прав (`ClusterRole`) часто запрещено политиками безопасности.
Кроме того, кластерный информер кэширует все объекты со всех неймспейсов, потребляя гигабайты оперативной памяти.

Режимы видимости оператора:
1. **Cluster-Scoped (Кластерный):** Отслеживает все неймспейсы кластера. Требует `ClusterRoleBinding`.
2. **Single-Namespace (Одно пространство):** Ограничен строго своим неймспейсом. Требует только локальный `RoleBinding`.
3. **Multi-Namespace (Набор пространств):** Отслеживает фиксированный список доверенных арендаторов (Tenants).

Конфигурация в `controller-runtime` (v0.15+):
```go
mgr, err := ctrl.NewManager(cfg, ctrl.Options{
    Cache: cache.Options{
        DefaultNamespaces: map[string]cache.Config{
            "tenant-alpha": {},
            "tenant-beta":  {},
        },
    },
})
```
Информеры инициализируются ТОЛЬКО для указанных пространств имен, радикально снижая нагрузку на память и API-сервер.""",
    "step_by_step": [
        "Определите модель конфигурации кэша арендаторов `MultiTenantCacheConfig`.",
        "Реализуйте фильтр допуска пространств имен `IsNamespaceAllowed`.",
        "Смоделируйте попытку создания ресурса в неразрешенном namespace.",
        "Продемонстрируйте изоляцию кэша информера доверенными тенантами."
    ],
    "code_blocks": [
        {
            "filename": "namespace_scoped_multitenancy.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
)

type MultiTenantFilter struct {
	AllowedNamespaces map[string]bool
}

func (f *MultiTenantFilter) IsNamespaceAllowed(ns string) bool {
	return f.AllowedNamespaces[ns]
}

func ProcessClusterRequest(ns, name string, filter *MultiTenantFilter) error {
	if !filter.IsNamespaceAllowed(ns) {
		return fmt.Errorf("DENIED: Operator is scoped to tenants %v, ignoring namespace '%s'",
			getAllowedList(filter.AllowedNamespaces), ns)
	}

	fmt.Printf("ALLOWED: Processing resource '%s/%s' within tenant boundaries.\n", ns, name)
	return nil
}

func getAllowedList(m map[string]bool) []string {
	var res []string
	for k := range m {
		res = append(res, k)
	}
	return res
}

func main() {
	filter := &MultiTenantFilter{
		AllowedNamespaces: map[string]bool{
			"tenant-alpha": true,
			"tenant-beta":  true,
		},
	}

	fmt.Println("=== NAMESPACE-SCOPED MULTI-TENANCY FILTER ===")

	// 1. Запрос из разрешенного пространства арендатора
	err1 := ProcessClusterRequest("tenant-alpha", "my-db", filter)
	fmt.Printf("Tenant Alpha Result: %v\n\n", err1)

	// 2. Запрос из чужого пространства имен
	err2 := ProcessClusterRequest("kube-system", "rogue-db", filter)
	fmt.Printf("Kube-system Result:  %v\n", err2)
}
"""
        }
    ],
    "under_the_hood": "При настройке `cache.Options.DefaultNamespaces` библиотека `client-go` под капотом создает раздельные информеры с фильтрацией `ListOptions{Namespace: ns}`. В etcd запрос уходит с точным путем `/api/v1/namespaces/tenant-alpha/pods`, минуя глобальный скан всего кластера.",
    "pitfalls": [
        "Попытка доступа к объектам уровня кластера (ClusterRole, StorageClass, Node) из Namespace-Scoped оператора: завершится ошибкой отсутствия прав.",
        "Использование старого параметра `ctrl.Options{Namespace: \"ns\"}`: этот параметр устарел в пользу гибкой структуры `cache.Options.DefaultNamespaces`."
    ],
    "bigtech_interview": "Как динамически обновлять список отслеживаемых неймспейсов в Multi-Namespace операторе без перезапуска процесса? Используется оператор с `cache.Builder` на базе контроллера пространств имен. Контроллер отслеживает метки на неймспейсах (например `company.com/managed-by: db-operator`). При появлении нового неймспейса с такой меткой оператор динамически инициализирует новый информер через `mgr.GetCache()`, бесшовно подключая нового арендатора."
})

# Ex 39
exercises.append({
    "num": 39,
    "title": "Custom Predicates и оптимизация фильтрации событий",
    "task": "Оптимизируйте производительность цикла примирения: напишите кастомные предикаты `predicate.Funcs`, отфильтровывающие события изменения `metadata.resourceVersion`, обновления только в Status-секции ресурсов или сервисных аннотаций. Замерьте сокращение паразитных вызовов метода `Reconcile` на 70–80% при активной жизни кластера.",
    "theory": r"""В высоконагруженных кластерах объекты непрерывно мутируются сторонними агентами:
- Prometheus Operator инжектирует аннотации скрейпинга.
- Istio Service Mesh обновляет статус прокси.
- Kubernetes Controller Manager обновляет метки нод.

Если оператор слушает дочерние поды через `.Owns(&corev1.Pod{})`, каждое такое микро-изменение вызывает метод `Reconcile` родительского кластера!

Решение: **Кастомные предикаты `predicate.Funcs`**
```go
podPredicate := predicate.Funcs{
    UpdateFunc: func(e event.UpdateEvent) bool {
        oldPod := e.ObjectOld.(*corev1.Pod)
        newPod := e.ObjectNew.(*corev1.Pod)

        // Игнорируем обновления, если фаза пода и статус контейнеров не изменились!
        if oldPod.Status.Phase == newPod.Status.Phase &&
           len(oldPod.Status.ContainerStatuses) == len(newPod.Status.ContainerStatuses) {
            return false // ОТСЕЧЬ паразитное событие!
        }
        return true
    },
}
```
Это снижает нагрузку на CPU оператора и etcd на **70–80%**.""",
    "step_by_step": [
        "Определите модель пода с полями фазы, IP-адреса и аннотаций.",
        "Реализуйте кастомный предикат `PodStatusChangedPredicate`.",
        "Смоделируйте мутацию сервисной аннотации (например метка времени скрейпинга).",
        "Докажите, что предикат блокирует паразитные вызовы и пропускает только реальные сбои подов."
    ],
    "code_blocks": [
        {
            "filename": "custom_predicates_optimization.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
)

type PodSnapshot struct {
	Name        string
	Phase       string
	PodIP       string
	Annotations map[string]string
}

type PodStatusChangedPredicate struct{}

func (p PodStatusChangedPredicate) ShouldReconcile(oldPod, newPod PodSnapshot) bool {
	// Реконсилим ТОЛЬКО если изменилась фаза (Pending -> Running -> Failed) или IP
	if oldPod.Phase != newPod.Phase {
		return true
	}
	if oldPod.PodIP != newPod.PodIP {
		return true
	}

	// Игнорируем изменения аннотаций сервисов метрик/логов
	return false
}

func main() {
	predicate := PodStatusChangedPredicate{}

	basePod := PodSnapshot{
		Name:        "pg-0",
		Phase:       "Running",
		PodIP:       "10.244.1.15",
		Annotations: map[string]string{"prometheus.io/scrape": "true"},
	}

	fmt.Println("=== CUSTOM PREDICATES OPTIMIZATION TEST ===")

	// Сценарий 1: Агент мониторинга обновил аннотацию временной метки
	mutatedAnnotationPod := basePod
	mutatedAnnotationPod.Annotations = map[string]string{
		"prometheus.io/scrape":    "true",
		"metrics.last_scrape_time": "1700000000",
	}

	reconcile1 := predicate.ShouldReconcile(basePod, mutatedAnnotationPod)
	fmt.Printf("Scenario 1 (Annotation updated): Reconcile? %v (Parasitic event eliminated!)\n", reconcile1)

	// Сценарий 2: Pod упал (Phase Running -> Failed)
	crashedPod := basePod
	crashedPod.Phase = "Failed"

	reconcile2 := predicate.ShouldReconcile(basePod, crashedPod)
	fmt.Printf("Scenario 2 (Pod crashed!):       Reconcile? %v (Legitimate failure caught!)\n", reconcile2)
}
"""
        }
    ],
    "under_the_hood": "Предикат вызывается внутри `EnqueueRequestForOwner`. Если `UpdateFunc` возвращает `false`, ключ родительского объекта не добавляется в очередь. В масштабных инсталляциях с 10 000 подов это предотвращает миллионы напрасных запусков горутин.",
    "pitfalls": [
        "Слишком жесткая фильтрация: если предикат случайно отсечет переход контейнера в состояние `CrashLoopBackOff`, оператор не узнает об аварии базы данных.",
        "Паника при кастинге типов в `UpdateEvent`: всегда используйте `oldObj, ok := e.ObjectOld.(*MyType)` с проверкой флага `ok`."
    ],
    "bigtech_interview": "Почему предикаты событий должны быть предельно легковесными функциями без сетевых вызовов? Предикаты выполняются синхронно в главном потоке доставки событий информера (Informer Event Handler). Если предикат сделает сетевой вызов (к базе данных или HTTP API), он заблокирует обработку всех входящих событий Watch для всего кластера, вызвав лавинообразное отставание информера от etcd."
})

# Ex 40
exercises.append({
    "num": 40,
    "title": "Управление деградацией и статусными условиями (Meta Conditions Pattern)",
    "task": "Стандартизируйте статусный блок CRD в соответствии со спецификацией Kubernetes API: используйте структуру `[]metav1.Condition` с фиксированными типами `Ready`, `Progressing`, `Degraded`. Реализуйте обновление статусов через стандартный хелпер `meta.SetStatusCondition` с правильным заполнением причин (`Reason`) и человекочитаемых сообщений (`Message`).",
    "theory": r"""Паттерн **Conditions (Условия)** описывает многомерное состояние ресурса.
Согласно руководству Kubernetes API Conventions, ресурс не должен выражать свое состояние одним единственным словом (например `Phase: Degraded`), так как система может быть одновременно деградировавшей по диску, но полностью доступной для чтения!

Канонический набор условий корпоративного оператора:
1. **`Ready`:** Общая готовность обслуживать трафик (`True`/`False`).
2. **`Progressing`:** Выполняется ли в данный момент операция (масштабирование, rolling update, бэкап).
3. **`Degraded`:** Находится ли кластер в субоптимальном состоянии (потеря одной из трех реплик, высокий лаг WAL, приближение к лимиту памяти).

Правила заполнения полей:
- **`Reason`:** Короткое машинно-читаемое слово в `UpperCamelCase` (например `ReplicaMissing`, `SyncReplicationLagHigh`). Никогда не должно содержать динамических переменных!
- **`Message`:** Детальное описание для администратора с точными цифрами и контекстом.""",
    "step_by_step": [
        "Определите структуру условия с типизированными причинами и статусами.",
        "Создайте агрегатор условий `ClusterConditionManager`.",
        "Реализуйте переключение условий при потере синхронной реплики (Ready=True, Degraded=True).",
        "Продемонстрируйте форматирование статусного блока для вывода в kubectl."
    ],
    "code_blocks": [
        {
            "filename": "meta_conditions_degraded_pattern.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"time"
)

type Condition struct {
	Type               string
	Status             string // "True", "False"
	Reason             string
	Message            string
	LastTransitionTime time.Time
}

type ClusterStatus struct {
	Conditions []Condition
}

func (s *ClusterStatus) SetCondition(c Condition) {
	for i, existing := range s.Conditions {
		if existing.Type == c.Type {
			if existing.Status != c.Status {
				existing.Status = c.Status
				existing.LastTransitionTime = c.LastTransitionTime
			}
			existing.Reason = c.Reason
			existing.Message = c.Message
			s.Conditions[i] = existing
			return
		}
	}
	s.Conditions = append(s.Conditions, c)
}

func main() {
	status := &ClusterStatus{}
	now := time.Now().UTC()

	// Ситуация: Кластер работает, но одна реплика отстает (Degraded состояние)
	status.SetCondition(Condition{
		Type:               "Ready",
		Status:             "True",
		Reason:             "ClusterServingTraffic",
		Message:            "Primary node is accepting connections",
		LastTransitionTime: now,
	})

	status.SetCondition(Condition{
		Type:               "Degraded",
		Status:             "True",
		Reason:             "ReplicaLagExceeded",
		Message:            "Replica pg-2 has replication lag of 450MB (> threshold 100MB)",
		LastTransitionTime: now,
	})

	fmt.Println("=== KUBERNETES META CONDITIONS PATTERN ===")
	for _, c := range status.Conditions {
		fmt.Printf("Condition: Type=%-10s Status=%-5s Reason=%-22s Msg=%s\n",
			c.Type, c.Status, c.Reason, c.Message)
	}
}
"""
        }
    ],
    "under_the_hood": "Пакет `k8s.io/apimachinery/pkg/api/meta` гарантирует детерминированный порядок среза `Conditions` при сериализации в JSON. При сортировке или фильтрации условий внешние контроллеры (например kstatus) используют стандартные функции `meta.IsStatusConditionTrue` и `meta.FindStatusCondition`.",
    "pitfalls": [
        "Использование динамических значений (например `Reason: \"Pod_pg-1_Dead\"`): ломает мониторинг Prometheus и автоматические алерты, отслеживающие точные строковые метки причин.",
        "Забытая установка `ObservedGeneration`: внешние системы не могут определить, относится ли статус к текущей примененной спецификации."
    ],
    "bigtech_interview": "Почему в современных Kubernetes контроллерах паттерн Conditions полностью вытеснил старое поле Phase: string? Поле `Phase` одномерно: кластер не может быть одновременно 'Running' и 'Upgrading'. Паттерн Conditions ортогонален: он позволяет одновременно отображать `Ready=True` (база обслуживает клиентов), `Progressing=True` (идет фоновое добавление новой реплики) и `Degraded=False`, давая полный срез здоровья распределенной системы."
})

# Ex 41
exercises.append({
    "num": 41,
    "title": "Dynamic Client и работа с произвольными Custom Resources",
    "task": "Изучите работу с ресурсами Kubernetes, схемы которых неизвестны на этапе компиляции: используйте `k8s.io/client-go/dynamic` и структуры `unstructured.Unstructured`. Реализуйте чтение, мутацию вложенных полей с помощью функций `unstructured.NestedMap` и создание произвольных объектов через динамический клиент.",
    "theory": r"""Обычный типизированный клиент (`client.Client`) требует наличия скомпилированных Go-структур в коде проекта.
Однако в универсальных операторах или плагинах типы целевых ресурсов часто **неизвестны во время компиляции**:
- Оператор бэкапов должен создавать `VolumeSnapshot`, даже если CRD снапшотов еще не установлен в кластере.
- Оператор мониторинга должен взаимодействовать с `PrometheusRule` или `ServiceMonitor`.

Решение: **Динамический клиент (`dynamic.Interface`) и `unstructured.Unstructured`**
Объект `unstructured.Unstructured` представляет собой обертку над сырой структурой `map[string]any`:
```go
obj := &unstructured.Unstructured{
    Object: map[string]any{
        "apiVersion": "monitoring.coreos.com/v1",
        "kind":       "ServiceMonitor",
        "metadata": map[string]any{"name": "my-db-monitor"},
    },
}
```
Пакет `k8s.io/apimachinery/pkg/apis/meta/v1/unstructured` предоставляет безопасные вспомогательные функции работы с вложенными полями: `NestedString`, `NestedSlice`, `SetNestedField`.""",
    "step_by_step": [
        "Определите структуру `UnstructuredResource` на базе `map[string]any`.",
        "Реализуйте типобезопасные функции извлечения и записи вложенных путей `SetNestedField`.",
        "Смоделируйте чтение и мутацию произвольного ресурса `ServiceMonitor` без статических типов.",
        "Продемонстрируйте сериализацию неструктурированного ресурса в валидный JSON/YAML."
    ],
    "code_blocks": [
        {
            "filename": "dynamic_client_unstructured.go",
            "lang": "go",
            "code": r"""package main

import (
	"encoding/json"
	"fmt"
)

type Unstructured struct {
	Object map[string]any
}

func (u *Unstructured) SetNestedField(val any, fields ...string) error {
	curr := u.Object
	for i, f := range fields[:len(fields)-1] {
		next, exists := curr[f]
		if !exists {
			newMap := make(map[string]any)
			curr[f] = newMap
			curr = newMap
		} else {
			nextMap, ok := next.(map[string]any)
			if !ok {
				return fmt.Errorf("field '%s' (index %d) is not a map", f, i)
			}
			curr = nextMap
		}
	}
	curr[fields[len(fields)-1]] = val
	return nil
}

func main() {
	// Создание динамического ресурса без статических Go структур
	u := &Unstructured{Object: make(map[string]any)}
	u.Object["apiVersion"] = "monitoring.coreos.com/v1"
	u.Object["kind"] = "ServiceMonitor"

	_ = u.SetNestedField("postgres-metrics", "metadata", "name")
	_ = u.SetNestedField("monitoring", "metadata", "namespace")
	_ = u.SetNestedField("15s", "spec", "endpoints", "interval")

	raw, err := json.MarshalIndent(u.Object, "", "  ")
	if err != nil {
		panic(err)
	}

	fmt.Println("=== KUBERNETES DYNAMIC CLIENT (UNSTRUCTURED) ===")
	fmt.Println(string(raw))
}
"""
        }
    ],
    "under_the_hood": "Динамический клиент `dynamic.NewForConfig(cfg)` оперирует `schema.GroupVersionResource` (GVR). Он взаимодействует с API-сервером через RESTMapper, преобразуя Kind в множественное число ресурса (Resource URL path) и сериализует JSON напрямую в/из `map[string]any` без вызова сгенерированных кодеков.",
    "pitfalls": [
        "Паника при прямом кастинге интерфейсов `u.Object[\"spec\"].(map[string]any)[\"replicas\"].(int)`: если поле отсутствует или тип является float64 (стандарт десериализации JSON), программа упадет. Всегда используйте хелперы `unstructured.Nested*`.",
        "Отсутствие валидации типов на этапе компиляции: любые опечатки в именах полей (`metadata.nam` вместо `metadata.name`) выявятся только во время работы в кластере."
    ],
    "bigtech_interview": "Когда в архитектуре оператора следует предпочесть dynamic.Interface вместо типизированного client.Client? Динамический клиент незаменим в двух случаях: 1) При работе с опциональными сторонними CRD (например cert-manager Certificate или Prometheus ServiceMonitor), когда вы не хотите вносить их Go-пакеты в `go.mod` вашего проекта; 2) При создании инфраструктурных мета-операторов (GitOps движки, backup-системы, generic-контроллеры), обрабатывающих любые произвольные ресурсы кластера."
})

# Ex 42
exercises.append({
    "num": 42,
    "title": "Chaos Testing оператора: Устойчивость к падениям контроллера и etcd",
    "task": "Напишите интеграционный тест с преднамеренным моделированием сбоев: принудительное завершение процесса оператора в середине транзакции создания кластера, имитация временной недоступности etcd и задержек API-сервера. Докажите, что механизм согласования (Reconciliation Loop) самостоятельно устраняет дрифт конфигурации и завершает процесс без утечки ресурсов.",
    "theory": r"""В распределенной среде контроллер оператора может быть аварийно завершен сигналом `SIGKILL` (OOM-Kill, падение ноды, потеря питания) в **любой строке кода**:
- Сразу после создания StatefulSet, но до создания Service.
- Посреди обновления статуса.
- Во время выполнения процедуры Failover.

**Принцип самоисцеления при хаос-тестировании (Chaos Resilience):**
1. Оператор не должен зависеть от порядка выполнения шагов в предыдущем упавшем процессе.
2. При рестарте новый процесс считывает фактический снимок кластера и безошибочно продолжает прерванную работу.
3. Процедура примирения должна быть готова к тому, что половина дочерних объектов уже создана, часть находится в процессе создания, а часть отсутствует.""",
    "step_by_step": [
        "Смоделируйте аварийное падение процесса оператора на шаге 2 из 3.",
        "Реализуйте симулятор рестарта нового процесса оператора.",
        "Запустите цикл примирения новым процессом и зафиксируйте обнаружение незавершенного состояния.",
        "Докажите, что контроллер успешно довел кластер до желаемого состояния без дублирования ресурсов."
    ],
    "code_blocks": [
        {
            "filename": "chaos_operator_resilience.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
)

type ClusterInfrastructure struct {
	ConfigMapCreated bool
	ServiceCreated   bool
	StatefulSetReady bool
}

type ResilientOperator struct {
	crashedAtStep int
}

func (op *ResilientOperator) Reconcile(infra *ClusterInfrastructure, currentStep *int) error {
	fmt.Println("\n--- STARTING RESILIENT RECONCILE ---")

	// Шаг 1: ConfigMap
	if !infra.ConfigMapCreated {
		if *currentStep == op.crashedAtStep {
			return fmt.Errorf("CRITICAL_CRASH: Process killed by SIGKILL at Step 1")
		}
		infra.ConfigMapCreated = true
		*currentStep++
		fmt.Println("[Step 1] ConfigMap provisioned successfully.")
	} else {
		fmt.Println("[Step 1] ConfigMap already exists (Idempotent skip).")
	}

	// Шаг 2: Service
	if !infra.ServiceCreated {
		if *currentStep == op.crashedAtStep {
			return fmt.Errorf("CRITICAL_CRASH: Process killed by SIGKILL at Step 2")
		}
		infra.ServiceCreated = true
		*currentStep++
		fmt.Println("[Step 2] Headless Service provisioned successfully.")
	} else {
		fmt.Println("[Step 2] Service already exists (Idempotent skip).")
	}

	// Шаг 3: StatefulSet
	if !infra.StatefulSetReady {
		infra.StatefulSetReady = true
		fmt.Println("[Step 3] StatefulSet provisioned and running.")
	}

	return nil
}

func main() {
	infra := &ClusterInfrastructure{}
	stepCounter := 1

	// Процесс #1: Падает на шаге 2
	process1 := &ResilientOperator{crashedAtStep: 2}
	err := process1.Reconcile(infra, &stepCounter)
	fmt.Printf("[Process 1 Died] Error: %v\n", err)
	fmt.Printf("Infra State after Crash: ConfigMap=%v, Service=%v, STS=%v\n",
		infra.ConfigMapCreated, infra.ServiceCreated, infra.StatefulSetReady)

	// Процесс #2: Новый процесс оператора поднялся после рестарта
	fmt.Println("\n>>> RESTARTING OPERATOR REPLICA <<<")
	process2 := &ResilientOperator{crashedAtStep: -1} // Работает без сбоев
	err = process2.Reconcile(infra, &stepCounter)

	fmt.Println("=== CHAOS RESILIENCE TEST RESULT ===")
	fmt.Printf("Final Reconcile Error: %v\n", err)
	fmt.Printf("Infra State: ConfigMap=%v, Service=%v, STS=%v (100%% Recovered!)\n",
		infra.ConfigMapCreated, infra.ServiceCreated, infra.StatefulSetReady)
}
"""
        }
    ],
    "under_the_hood": "В Kubernetes хаос-тестирование операторов автоматизируется инструментами вроде Chaos Mesh или LitmusChaos. Тесты непрерывно перезапускают поды оператора (`pod-kill`), внедряют задержки сокетов API-сервера (`network-delay`) и проверяют, что итоговое состояние кастомных ресурсов сходится к желаемому в пределах заданного SLO (Eventual Consistency).",
    "pitfalls": [
        "Хранение состояния выполнения шагов примирения в глобальных переменных процесса: при падении процесса переменные стираются, и новый процесс может нарушить порядок развертывания.",
        "Неатомарные операции с внешними системами без возможности отката или продолжения с прерванной точки."
    ],
    "bigtech_interview": "Почему архитектура Kubernetes называется Eventual Consistency (Согласованность в конечном счете)? В распределенной среде невозможно гарантировать мгновенную строгую синхронизацию всех компонентов при падениях нод и сети. Kubernetes гарантирует, что система непрерывно стремится к желаемому состоянию, и как только сбои прекратятся, контрольный цикл Reconcile Loop гарантированно приведет состояние кластера в 100% соответствие со спецификацией."
})

# Ex 43
exercises.append({
    "num": 43,
    "title": "Graceful Shutdown контроллера и завершение фоновых горутин",
    "task": "Обеспечьте корректное завершение работы оператора при получении сигналов SIGINT/SIGTERM: передача контекста отмены `mgr.Start(ctrl.SetupSignalHandler())`, ожидание завершения активных вызовов `Reconcile` и корректное закрытие фоновых соединений с базами данных без обрыва клиентских сессий.",
    "theory": r"""При обновлении Deployment оператора старый Pod получает сигнал `SIGTERM`.
Если процесс завершится мгновенно через `os.Exit(0)`:
- Активные вызовы `Reconcile` оборвутся на середине транзакции.
- Незавершенные соединения с внешними базами данных останутся висеть в виде полуоткрытых сокетов.
- Замок Leader Election (`Lease`) не будет добровольно освобожден, и резервным репликам придется ждать 15 секунд таймаута аренды для перехвата управления.

**Процедура Graceful Shutdown в `controller-runtime`:**
1. Инициализация контекста сигналов ОС: `ctx := ctrl.SetupSignalHandler()`.
2. Передача `ctx` в вызов `mgr.Start(ctx)`.
3. При получении `SIGTERM` менеджер:
   - Немедленно прекращает извлечение новых задач из очередей `workqueue`.
   - Дожидается завершения всех активных в данный момент горутин Reconcile (Drain period).
   - Вызывает методы остановки всех зарегистрированных сервисов (`LeaderElection.StepDown()`, остановка вебхук HTTPS-сервера).
   - Корректно завершает работу процесса.""",
    "step_by_step": [
        "Определите менеджер оператора с координацией завершения через контекст.",
        "Реализуйте симулятор обработки сигналов операционной системы.",
        "Запрограммируйте ожидание завершения активных воркеров при получении сигнала отмены.",
        "Продемонстрируйте добровольное освобождение лидерского замка при плановом завершении."
    ],
    "code_blocks": [
        {
            "filename": "operator_graceful_shutdown.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

type ControllerManager struct {
	wg         sync.WaitGroup
	activeJobs int32
}

func (m *ControllerManager) StartWorker(ctx context.Context, id int) {
	m.wg.Add(1)
	go func() {
		defer m.wg.Done()
		fmt.Printf("[Worker %d] Started.\n", id)

		for {
			select {
			case <-ctx.Done():
				fmt.Printf("[Worker %d] Cancellation signal received. Draining in-flight work...\n", id)
				time.Sleep(30 * time.Millisecond) // Завершение текущего шага
				fmt.Printf("[Worker %d] In-flight work completed. Stopped safely.\n", id)
				return
			case <-time.After(20 * time.Millisecond):
				// Имитация примирения
			}
		}
	}()
}

func (m *ControllerManager) Stop() {
	m.wg.Wait()
	fmt.Println("[Manager] All workers drained. Voluntary Leader Election StepDown completed.")
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	manager := &ControllerManager{}

	fmt.Println("=== KUBERNETES OPERATOR GRACEFUL SHUTDOWN ===")
	// Запуск 2 воркеров
	manager.StartWorker(ctx, 1)
	manager.StartWorker(ctx, 2)

	time.Sleep(50 * time.Millisecond)

	// Имитация получения SIGTERM от Kubernetes
	fmt.Println("\n>>> SIGTERM RECEIVED FROM KUBELET <<<")
	cancel()

	// Ожидание аккуратного завершения
	manager.Stop()
	fmt.Println("Operator process exited with code 0. Zero in-flight work dropped!")
}
"""
        }
    ],
    "under_the_hood": "Функция `ctrl.SetupSignalHandler()` перехватывает сигналы `syscall.SIGINT` и `syscall.SIGTERM`. При получении ПЕРВОГО сигнала закрывается канал `stopCh`, инициируя плавную остановку. Если процесс получит ВТОРОЙ сигнал до завершения таймаута, обработчик немедленно форсирует аварийный выход через `os.Exit(1)`.",
    "pitfalls": [
        "Использование `context.Background()` внутри вызовов SDK вместо контекста `r.Reconcile(ctx, req)`: фоновые запросы не получат сигнал отмены при завершении пода.",
        "Слишком долгая процедура shutdown (>30 секунд): если оператор не завершится в течение `terminationGracePeriodSeconds`, Kubernetes убьет его жестким `SIGKILL`."
    ],
    "bigtech_interview": "Зачем лидер оператора при плановом Graceful Shutdown добровольно обнуляет Lease (Leader Election StepDown)? Если процесс оператора убит жестко, Lease остается заблокированным на `leaseDuration` (15 секунд), и резервные реплики ждут истечения таймера. При плановом завершении лидер очищает поле `holderIdentity` в объекте Lease перед выходом. Резервная реплика мгновенно перехватывает лидерство с задержкой менее 50 миллисекунд."
})

# Ex 44
exercises.append({
    "num": 44,
    "title": "Профилирование памяти контроллера под управлением 10 000 CRD",
    "task": "Разверните тестовый стенд с 10 000 пользовательских ресурсов CRD. Проведите профилирование потребления оперативной памяти с помощью `go tool pprof`: выявите объем памяти, занятый кэшами Informer/Cache, и оптимизируйте потребление путем настройки селекторов полей (`SelectorsByObject`) и сужения кэшируемых атрибутов.",
    "theory": r"""При масштабировании оператора до десятков тысяч кастомных ресурсов в одном кластере потребление RAM может вырасти до нескольких гигабайт, вызвав Out-Of-Memory (OOM-Kill).

Где расходуется память оператора?
1. **Informer Cache:** По умолчанию кэширует JSON-десериализованные объекты целиком, включая тяжелые аннотации, историю статусов и управляемые поля `managedFields`.
2. **Очереди `workqueue`:** Десятки тысяч ключей в куче Go.

Методы экстремальной оптимизации памяти в `controller-runtime`:
1. **Сужение кэша по селекторам (`cache.Options.ByObject`):**
   Кэшировать объекты только с определенными метками:
   ```go
   cache.Options{
       ByObject: map[client.Object]cache.ByObject{
           &corev1.Secret{}: {
               Label: labels.SelectorFromSet(labels.Set{"app.kubernetes.io/managed-by": "db-operator"}),
           },
       },
   }
   ```
2. **Исключение тяжелых полей (TransformFunc):**
   Удаление `managedFields` и аннотаций перед сохранением в кэш с помощью функции-трансформера информера (`cache.Transform`), что снижает расход памяти на **40–60%**!""",
    "step_by_step": [
        "Определите модель хранения тяжелого объекта Kubernetes с метаданными.",
        "Реализуйте функцию очистки полей `StripManagedFieldsAndAnnotations` для экономии памяти.",
        "Смоделируйте кэширование 10 000 объектов и замерьте объем сырой и оптимизированной памяти.",
        "Продемонстрируйте двукратное сокращение потребления оперативной памяти кэшем."
    ],
    "code_blocks": [
        {
            "filename": "operator_memory_profiling.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"runtime"
)

type HeavyK8sObject struct {
	Name          string
	Namespace     string
	ManagedFields string // Занимает много памяти!
	Annotations   map[string]string
	Replicas      int
}

type OptimizedK8sObject struct {
	Name      string
	Namespace string
	Replicas  int
}

func TransformToSlim(in HeavyK8sObject) OptimizedK8sObject {
	return OptimizedK8sObject{
		Name:      in.Name,
		Namespace: in.Namespace,
		Replicas:  in.Replicas,
	}
}

func main() {
	count := 10000

	var memStart runtime.MemStats
	runtime.ReadMemStats(&memStart)

	// Симуляция 1: Кэширование тяжелых объектов
	heavyStore := make([]HeavyK8sObject, count)
	for i := 0; i < count; i++ {
		heavyStore[i] = HeavyK8sObject{
			Name:          fmt.Sprintf("db-cluster-%05d", i),
			Namespace:     "production",
			ManagedFields: "{\"manager\":\"kubectl\",\"operation\":\"Update\",\"time\":\"2026-09-08T12:00:00Z\"}",
			Annotations: map[string]string{
				"kubectl.kubernetes.io/last-applied-configuration": "{\"apiVersion\":\"storage/v1\",\"spec\":{...}}",
			},
			Replicas: 3,
		}
	}

	var memHeavy runtime.MemStats
	runtime.ReadMemStats(&memHeavy)
	heavyAlloc := memHeavy.Alloc - memStart.Alloc

	// Симуляция 2: Кэширование оптимизированных объектов
	slimStore := make([]OptimizedK8sObject, count)
	for i := 0; i < count; i++ {
		slimStore[i] = TransformToSlim(heavyStore[i])
	}

	var memSlim runtime.MemStats
	runtime.ReadMemStats(&memSlim)
	slimAlloc := memSlim.Alloc - memHeavy.Alloc

	fmt.Println("=== KUBERNETES OPERATOR MEMORY PROFILING ===")
	fmt.Printf("Cached Resources Count:  %d objects\n", count)
	fmt.Printf("Raw Heavy Cache Memory:  %.2f MB\n", float64(heavyAlloc)/(1024*1024))
	fmt.Printf("Optimized Cache Memory:  %.2f MB\n", float64(slimAlloc)/(1024*1024))
	fmt.Printf("Memory Footprint Saved:  %.1f%%\n", (1.0-float64(slimAlloc)/float64(heavyAlloc))*100.0)
}
"""
        }
    ],
    "under_the_hood": "Параметр `cache.Transform` в `controller-runtime` выполняется ДО сохранения объекта в Indexer кэша. Если функция обнуляет `obj.SetManagedFields(nil)`, сырые JSON-блоки удаляются сборщиком мусора Go сразу после обработки, и миллионы байт строковых структур не оседают в куче (Heap).",
    "pitfalls": [
        "Кэширование всех Secret'ов кластера без селектора меток: оператор попытается закэшировать секреты всех приложений кластера, мгновенно исчерпав память на больших инсталляциях.",
        "Удаление полей в `TransformFunc`, которые затем требуются методу `Reconcile`: приведет к ошибкам логики."
    ],
    "bigtech_interview": "Как профилировать утечки памяти в работающем под нагрузкой Kubernetes операторе без остановки пода? Библиотека `controller-runtime` автоматически регистрирует эндпоинты `net/http/pprof` на порту метрик. Инженер выполняет проброс порта `kubectl port-forward pod/operator 8080:8080` и анализирует профиль кучи командой: `go tool pprof -http=:8081 http://localhost:8080/debug/pprof/heap`. Это позволяет мгновенно визуализировать allocations по типам структур в интерактивном веб-графе."
})

# Ex 45
exercises.append({
    "num": 45,
    "title": "Production-Ready Kubernetes Operator для высоконагруженной платформы кэширования (Capstone)",
    "task": "Объедините все изученные шаблоны в полноценный оператор распределенного кэша Redis/KeyDB на Go: CRD с описанием топологии шардирования и репликации, валидационные и мутационные вебхуки, Server-Side Apply согласование дочерних StatefulSet и Service, автоматический failover мастер-нод, экспорт метрик в Prometheus и защищенный OLM-бандл.",
    "theory": r"""Финальный архитектурный синтез разработки Enterprise Kubernetes Operators:

1. **Декларативный CRD Контракт (`CacheCluster`):**
   - OpenAPI v3 валидация и маркеры Kubebuilder.
   - Четкое разделение `.spec` (шарды, реплики, память, eviction-policy) и `.status` (условия Conditions, endpoints).
2. **Безопасность периметра и Webhooks:**
   - Mutating Webhook для подстановки безопасных дефолтов памяти и образов.
   - Validating Webhook для проверки четности и минимального кворума.
   - Автоматический выпуск TLS-сертификатов через `cert-manager`.
3. **Высоконадежный цикл согласования (Reconcile Loop):**
   - Server-Side Apply для исключения конфликтов версий.
   - OwnerReferences для каскадной сборки мусора дочерних StatefulSet.
   - Quorum-aware rolling updates с мягким переводом мастера.
   - Finalizers для архивации дампов RDB в объектное хранилище S3 перед удалением.
4. **Production Observability & HA:**
   - Active-Passive Leader Election на Lease-замках.
   - Сбор бизнес-метрик состояния шардов в Prometheus.
   - Graceful Shutdown при получении SIGTERM.""",
    "step_by_step": [
        "Определите модель распределенного кэша `CacheClusterSpec` и `CacheClusterStatus`.",
        "Реализуйте контроллер `CacheClusterReconciler`, объединяющий жизненный цикл дочерних ресурсов, финализаторы и статус.",
        "Запрограммируйте Server-Side Apply согласование и проверку условий `Ready` и `Progressing`.",
        "Продемонстрируйте комплексное развертывание кластера кэширования и проверку устойчивости."
    ],
    "code_blocks": [
        {
            "filename": "capstone_production_operator.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
	"time"
)

type CacheClusterSpec struct {
	Shards   int
	Replicas int
	MemoryMB int
}

type CacheClusterStatus struct {
	Phase         string
	ReadyShards   int
	LeaderNode    string
	LastFailover  time.Time
	ConditionType string
}

type CacheCluster struct {
	Name       string
	Namespace  string
	Finalizers []string
	Spec       CacheClusterSpec
	Status     CacheClusterStatus
}

type EnterpriseCacheOperator struct {
	isLeader bool
}

func (op *EnterpriseCacheOperator) Reconcile(ctx context.Context, cluster *CacheCluster) error {
	if !op.isLeader {
		return fmt.Errorf("instance is standby. Only active leader executes Reconcile")
	}

	fmt.Printf("\n=== [CAPSTONE OPERATOR] Reconciling '%s/%s' ===\n",
		cluster.Namespace, cluster.Name)

	// 1. Проверка финализатора
	hasFinalizer := false
	for _, f := range cluster.Finalizers {
		if f == "cache.company.com/s3-dump" {
			hasFinalizer = true
			break
		}
	}
	if !hasFinalizer {
		cluster.Finalizers = append(cluster.Finalizers, "cache.company.com/s3-dump")
		fmt.Println("[Finalizer] Registered 'cache.company.com/s3-dump'")
	}

	// 2. Server-Side Apply для StatefulSet шардов
	totalNodes := cluster.Spec.Shards * cluster.Spec.Replicas
	fmt.Printf("[SSA] Harmonizing %d Shards x %d Replicas (%d total pods, %d MB RAM each)...\n",
		cluster.Spec.Shards, cluster.Spec.Replicas, totalNodes, cluster.Spec.MemoryMB)

	// 3. Обновление статуса
	cluster.Status.Phase = "Running"
	cluster.Status.ReadyShards = cluster.Spec.Shards
	cluster.Status.LeaderNode = fmt.Sprintf("%s-shard-0-master", cluster.Name)
	cluster.Status.ConditionType = "Ready"

	fmt.Printf("[Status Updated] Phase=%s, ReadyShards=%d/%d, Primary=%s\n",
		cluster.Status.Phase, cluster.Status.ReadyShards, cluster.Spec.Shards, cluster.Status.LeaderNode)

	return nil
}

func main() {
	cluster := &CacheCluster{
		Name:      "redis-enterprise-mesh",
		Namespace: "caching",
		Spec: CacheClusterSpec{
			Shards:   3,
			Replicas: 2,
			MemoryMB: 4096,
		},
		Status: CacheClusterStatus{Phase: "Pending"},
	}

	operator := &EnterpriseCacheOperator{isLeader: true}

	fmt.Println("=== CAPSTONE: ENTERPRISE KUBERNETES OPERATOR INITIALIZED ===")
	err := operator.Reconcile(context.Background(), cluster)
	if err != nil {
		panic(err)
	}

	fmt.Println("\nCapstone Kubernetes Operator successfully synchronized distributed cache topology!")
}
"""
        }
    ],
    "under_the_hood": "В архитектуре передовых корпоративных операторов (VictoriaMetrics Operator, Redis Enterprise, Strimzi Kafka) ядро оператора строится как распределенный конечный автомат (Distributed FSM). Каждая итерация цикла примирения делает ровно один шаг перехода состояния, опираясь на неизменяемые математические инварианты консенсуса, гарантируя абсолютную надежность при любых сбоях физической инфраструктуры.",
    "pitfalls": [
        "Монолитная логика Reconcile на тысячи строк кода без декомпозиции на суб-реконсилеры (Sub-Reconcilers): приводит к невозможности модульного тестирования и регрессионным ошибкам.",
        "Игнорирование сетевых разделений (Network Partitions) между оператором и кластером СУБД: оператор обязан проверять таймстемпы и кворум перед принятием решений об аварийном переключении лидера."
    ],
    "bigtech_interview": "Как защитить базу данных от случайного уничтожения при удалении CRD манифеста или namespace администратором (Accidental Deletion Protection)? Применяются три эшелона защиты: 1) Validating Webhook с блокировкой удаления, если на объекте не выставлена явная аннотация `operator.company.com/allow-deletion: \"true\"`; 2) Финализатор (`finalizers`), который не позволит стереть CRD до тех пор, пока внешний бэкап не будет успешно загружен в S3; 3) Защита постоянных томов `PersistentVolumeClaim` через `reclaimPolicy: Retain`, сохраняющая физические данные на диске даже после удаления всех подов и ресурсов Kubernetes."
})

# Verify all code blocks with gofmt
print(f"Total exercises in part 2: {len(exercises)}")
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

out_path = "/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch91_p2.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Wrote {out_path} successfully with {len(exercises)} exercises!")
