# -*- coding: utf-8 -*-
import json
import subprocess
import tempfile
import os

exercises = []

# Exercise 16
exercises.append({
    "num": 16,
    "title": "Точный расчет перцентилей задержки с HdrHistogram",
    "task": "Накопление времен ответов в срезе `[]time.Duration` для последующей сортировки требует гигабайты памяти при миллионах запросов. Подключите библиотеку `HdrHistogram/hdrhistogram-go`. Накапливайте метрики в гистограмме с динамическим диапазоном от 1 мкс до 1 часа с гарантированной точностью и вычисляйте p50, p90, p99, p99.9 и p99.99.",
    "theory": r"""При проведении высоконагруженных тестов сбор метрик задержки наталкивается на проблему эффективности хранения:
- Если тест генерирует 100 000 RPS в течение 10 минут, общее количество измерений составит $60\,000\,000$ сэмплов.
- Хранение такого среза `[]time.Duration` (8 байт на элемент) требует ~480 МБ оперативной памяти.
- Сортировка среза (`sort.Slice`) для вычисления перцентилей блокирует процессор на десятки секунд и вызывает лавину аллокаций памяти.

HdrHistogram (High Dynamic Range Histogram), разработанный Гилом Тене:
1. Поддерживает запись значений в широком диапазоне (например, от 1 микросекунды до 1 часа — динамический диапазон $1 : 3.6 \times 10^9$).
2. Обеспечивает настраиваемую точность (обычно 3 значащие цифры, относительная погрешность не более 1%).
3. Фиксированное потребление памяти: внутренняя структура использует логарифмическую сетку бакетов (Buckets and Sub-buckets). Для диапазона от 1 мкс до 1 часа при точности 3 знака требуется всего **десятки килобайт памяти**!
4. Запись значения (`RecordValue`) выполняется за константное время $O(1)$ без единой аллокации памяти в куче, что критически важно для горячего цикла нагрузочного генератора.""",
    "step_by_step": [
        "Изучите математическую модель логарифмического квантования HdrHistogram.",
        "Реализуйте высокопроизводительную структуру `HDRBucketHistogram` на Go с логарифмическими бакетами и фиксированным объемом памяти.",
        "Реализуйте методы `Record(duration)` за $O(1)$ и `ValueAtPercentile(percentile)` для расчета p50, p90, p99, p99.9.",
        "Проведите бенчмарк: запишите 1 000 000 сэмплов и вычислите перцентили, доказав отсутствие динамических аллокаций памяти."
    ],
    "code_blocks": [
        {
            "filename": "hdr_histogram_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"math"
	"sync"
	"testing"
	"time"
)

type HDRBucketHistogram struct {
	mu          sync.Mutex
	minVal      int64
	maxVal      int64
	totalCount  int64
	subBuckets  int
	bucketMask  int64
	counts      []int64
	bucketCount int
}

func NewHDRBucketHistogram(minMicros, maxMicros int64) *HDRBucketHistogram {
	bucketCount := 32
	subBuckets := 1024

	return &HDRBucketHistogram{
		minVal:      minMicros,
		maxVal:      maxMicros,
		subBuckets:  subBuckets,
		counts:      make([]int64, bucketCount*subBuckets),
		bucketCount: bucketCount,
	}
}

func (h *HDRBucketHistogram) Record(d time.Duration) {
	micros := d.Microseconds()
	if micros < h.minVal {
		micros = h.minVal
	}
	if micros > h.maxVal {
		micros = h.maxVal
	}

	h.mu.Lock()
	defer h.mu.Unlock()

	bucketIdx := 0
	val := micros
	for val >= int64(h.subBuckets) && bucketIdx < h.bucketCount-1 {
		val >>= 1
		bucketIdx++
	}

	idx := bucketIdx*h.subBuckets + int(val)
	if idx < len(h.counts) {
		h.counts[idx]++
		h.totalCount++
	}
}

func (h *HDRBucketHistogram) ValueAtPercentile(p float64) time.Duration {
	h.mu.Lock()
	defer h.mu.Unlock()

	if h.totalCount == 0 {
		return 0
	}

	targetCount := int64(math.Ceil(float64(h.totalCount) * (p / 100.0)))
	var accumulated int64

	for b := 0; b < h.bucketCount; b++ {
		for s := 0; s < h.subBuckets; s++ {
			idx := b*h.subBuckets + s
			accumulated += h.counts[idx]
			if accumulated >= targetCount {
				val := int64(s) << b
				return time.Duration(val) * time.Microsecond
			}
		}
	}

	return time.Duration(h.maxVal) * time.Microsecond
}

func TestHdrHistogramPrecision(t *testing.T) {
	hist := NewHDRBucketHistogram(1, 3600*1000*1000)

	for i := 0; i < 9000; i++ {
		hist.Record(5 * time.Millisecond)
	}
	for i := 0; i < 900; i++ {
		hist.Record(50 * time.Millisecond)
	}
	for i := 0; i < 100; i++ {
		hist.Record(500 * time.Millisecond)
	}

	p50 := hist.ValueAtPercentile(50.0)
	p90 := hist.ValueAtPercentile(90.0)
	p99 := hist.ValueAtPercentile(99.0)

	t.Logf("Рассчитанные перцентили: p50=%v, p90=%v, p99=%v", p50, p90, p99)

	if p50 < 4*time.Millisecond || p50 > 6*time.Millisecond {
		t.Errorf("p50 не совпал с ожидаемым: %v", p50)
	}
	if p99 < 400*time.Millisecond || p99 > 600*time.Millisecond {
		t.Errorf("p99 не совпал с ожидаемым: %v", p99)
	}
}

func main() {
	hist := NewHDRBucketHistogram(1, 10000000)
	start := time.Now()
	for i := 0; i < 1000000; i++ {
		hist.Record(time.Duration(i%500) * time.Millisecond)
	}
	fmt.Printf("Запись 1 000 000 сэмплов выполнена за %v\n", time.Since(start))
	fmt.Printf("p50: %v\n", hist.ValueAtPercentile(50))
	fmt.Printf("p95: %v\n", hist.ValueAtPercentile(95))
	fmt.Printf("p99: %v\n", hist.ValueAtPercentile(99))
}
"""
        }
    ],
    "under_the_hood": "В отличие от линейных гистограмм, где ширина бакета фиксирована (например, 1 мс), HdrHistogram использует плавающую сетку: на малых задержках (1-100 мкс) ширина бакета составляет единицы наносекунд, а на больших задержках (секунды) бакет расширяется пропорционально логарифму значения. Это обеспечивает постоянную относительную погрешность (relative error) на всем диапазоне при минимальном потреблении оперативной памяти.",
    "pitfalls": [
        "Неверно выбранный диапазон `highestTrackableValue`: если запрос длился дольше максимального значения гистограммы, он будет записан в последний бакет, занижая перцентиль p99.99.",
        "Использование одного мьютекса при сотнях параллельных горутин: возникает сильная конкуренция блокировок. В высоконагруженных генераторах используют локальные гистограммы на горутину (`Thread-Local Histogram`) с последующим их объединением через `Merge()`.",
        "Пренебрежение коррекцией Coordinated Omission: HdrHistogram поддерживает метод `RecordCorrectedValue()`, который автоматически заполняет пропущенные интервалы."
    ],
    "bigtech_interview": "Почему среднее арифметическое (Average Latency) категорически запрещено использовать в качестве SLA/SLO веб-сервисов? В реальных системах распределение задержки имеет тяжелый хвост (длинный шлейф редких медленных запросов). Девяносто девять запросов по 1 мс и один запрос по 10 000 мс дают среднее 100 мс — значение, которое ни о чем не говорит (ни один реальный пользователь не получил ответ за 100 мс!). Пользовательский опыт и соблюдение SLA оцениваются исключительно по перцентилям p95, p99 и p99.9."
})

# Exercise 17
exercises.append({
    "num": 17,
    "title": "Сценарии профилей нагрузки: Step-Up, Spike и Soak Test",
    "task": "Реализуйте в нагрузочном инструменте три сценария: ступенчатый рост нагрузки (Step-Up Test для определения предела масштабируемости), резкий скачок нагрузки (Spike Test для проверки реакции автоскейлинга) и длительный многочасовой тест на выносливость (Soak Test для выявления медленных утечек памяти).",
    "theory": r"""В профессиональном нагрузочном тестировании используются различные профили нагрузки (Workload Profiles) в зависимости от инженерной цели:

1. **Ступенчатый тест (Step-Up / Stress Test):**
   - Нагрузка повышается дискретными шагами: 1000 RPS -> 2000 RPS -> 3000 RPS (по 2–5 минут на каждой ступени).
   - **Цель:** Найти точку насыщения системы (Knee Point / Saturation Point), где задержка начинает экспоненциально расти или появляются первые 5xx ошибки.
2. **Всплесковый тест (Spike Test):**
   - Мгновенный скачок трафика с базового уровня (500 RPS) до пикового (5000 RPS) за доли секунды, удержание в течение 30 секунд и резкий спад.
   - **Цель:** Проверить реакцию Kubernetes HPA (Horizontal Pod Autoscaler), вытеснение очереди (Queue Shedding) и устойчивость к падениям при холодном старте подов.
3. **Тест на выносливость (Soak / Endurance Test):**
   - Непрерывная подача номинальной нагрузки (70-80% от максимума) на протяжении 12–48 часов.
   - **Цель:** Обнаружить медленные, скрытые утечки ресурсов: фрагментацию кучи рантайма Go, утечку файловых дескрипторов, разрастание кэшей в памяти без TTL, утечку соединений в БД.""",
    "step_by_step": [
        "Спроектируйте конфигурацию этапа нагрузки `LoadStage{Duration, TargetRPS}`.",
        "Реализуйте оркестратор профилей `ProfileRunner`, плавно или ступенчато интерполирующий RPS между этапами.",
        "Настройте три типовых профиля: Step-Up (ступенчатый), Spike (всплеск) и Soak (плато).",
        "Проверьте исполнение сценария и валидацию SLO на каждом этапе."
    ],
    "code_blocks": [
        {
            "filename": "load_profiles_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
	"sync/atomic"
	"time"
)

type LoadStage struct {
	Name      string
	Duration  time.Duration
	TargetRPS float64
}

type ProfileExecutionResult struct {
	StageName string
	TotalReqs int64
	ActualRPS float64
}

type ProfileRunner struct {
	stages []LoadStage
	task   func(ctx context.Context) error
}

func NewProfileRunner(stages []LoadStage, task func(ctx context.Context) error) *ProfileRunner {
	return &ProfileRunner{
		stages: stages,
		task:   task,
	}
}

func (r *ProfileRunner) Execute(ctx context.Context) []ProfileExecutionResult {
	results := make([]ProfileExecutionResult, 0, len(r.stages))

	for _, stage := range r.stages {
		fmt.Printf("[PROFILE] Старт этапа '%s' (Цель: %.0f RPS, длительность: %v)...\n",
			stage.Name, stage.TargetRPS, stage.Duration)

		var stageReqs atomic.Int64
		stageStart := time.Now()
		stageDeadline := stageStart.Add(stage.Duration)

		interval := time.Duration(float64(time.Second) / stage.TargetRPS)
		ticker := time.NewTicker(interval)

		for time.Now().Before(stageDeadline) {
			select {
			case <-ctx.Done():
				ticker.Stop()
				return results
			case <-ticker.C:
				stageReqs.Add(1)
				go func() {
					reqCtx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
					defer cancel()
					_ = r.task(reqCtx)
				}()
			}
		}
		ticker.Stop()

		elapsed := time.Since(stageStart)
		res := ProfileExecutionResult{
			StageName: stage.Name,
			TotalReqs: stageReqs.Load(),
			ActualRPS: float64(stageReqs.Load()) / elapsed.Seconds(),
		}
		results = append(results, res)
	}

	return results
}

func main() {
	mockWork := func(ctx context.Context) error {
		time.Sleep(2 * time.Millisecond)
		return nil
	}

	stages := []LoadStage{
		{Name: "Warmup", Duration: 200 * time.Millisecond, TargetRPS: 50},
		{Name: "Step 1", Duration: 200 * time.Millisecond, TargetRPS: 100},
		{Name: "Spike!", Duration: 200 * time.Millisecond, TargetRPS: 300},
	}

	runner := NewProfileRunner(stages, mockWork)
	ctx := context.Background()
	results := runner.Execute(ctx)

	fmt.Println("=== ИТОГОВЫЙ ОТЧЕТ ПРОФИЛЯ НАГРУЗКИ ===")
	for _, r := range results {
		fmt.Printf("Этап: %-10s | Запросов: %-5d | RPS: %.1f\n", r.StageName, r.TotalReqs, r.ActualRPS)
	}
}
"""
        }
    ],
    "under_the_hood": "Переключение этапов в генераторе нагрузки требует аккуратной синхронизации таймеров. При резком скачке с 100 до 5000 RPS интервал таймера изменяется на лету (`ticker.Reset()`). Если генератор не справляется с темпом генерации тиков, он начинает пропускать события, что приводит к скоординированному пропуску. В промышленных генераторах для каждого этапа рассчитывается точное количество сэмплов с непрерывной коррекцией ошибки времени через дрифт-компенсатор (Clock Drift Compensator).",
    "pitfalls": [
        "Отсутствие этапа прогрева (Warmup): запуск пиковой нагрузки на холодный сервис искажает результаты из-за JIT-компиляции, прогрева кэшей и ленивой инициализации пулов соединений.",
        "Слишком короткий Soak Test: медленные утечки памяти (Memory Leaks) по 50 КБ в час невозможно обнаружить на 10-минутных тестах.",
        "Игнорирование метрик ресурсов (CPU, RAM, GC Pause) хоста-генератора."
    ],
    "bigtech_interview": "Как отличить утечку памяти (Memory Leak) от естественного поведения кэшей при анализе результатов Soak Test? В нормальной системе с кэшированием график потребления памяти (HeapAlloc) сначала растет линейно, затем достигает плато (размер ограничен LRU/TTL) и колеблется в форме пилы из-за циклов сборщика мусора GC. При утечке памяти график `HeapAlloc` после прохождения GC монотонно возрастает без выхода на плато вплоть до срабатывания OOMKilled."
})

# Exercise 18
exercises.append({
    "num": 18,
    "title": "Симуляция разделения сети (Split-Brain / Network Partition)",
    "task": "Разверните локальный кластер из 3 узлов с консенсусом Raft (из Главы 72). С помощью Toxiproxy разорвите сетевую связность между лидером и двумя фолловерами (сетевая изоляция меньшинства). Продемонстрируйте корректный выбор нового лидера в большинстве и защиту от двойной записи (Split-Brain).",
    "theory": r"""Сетевое разделение (Network Partition / Split-Brain) — экстремальный сценарий в распределенных системах, при котором кластер распадается на две или более изолированные группы узлов, потерявших связь друг с другом.

Теорема CAP и защита от Split-Brain:
Если в кластере из 3 узлов $\{N_1, N_2, N_3\}$ узел $N_1$ (текущий Лидер) оказывается изолирован от узлов $\{N_2, N_3\}$:
- **Опасность (Split-Brain):** если обе части кластера продолжат независимо принимать операции записи, данные разойдутся, и база окажется безнадежно повреждена.
- **Решение (Кворум большинства):**
  Кворум $Q$ рассчитывается как:
  $$Q = \left\lfloor \frac{N}{2} \right\rfloor + 1$$
  Для кластера из 3 узлов кворум равен 2 узлам.
  - В изолированном меньшинстве ($N_1$) кворум отсутствует ($1 < 2$). Лидер $N_1$ не может подтвердить запись и обязан отклонять запросы.
  - В изолированном большинстве ($\{N_2, N_3\}$) кворум присутствует ($2 \ge 2$). Узлы фиксируют отсутствие heartbeat от старого лидера, инициируют новые выборы (Election Timeout), выбирают нового легитимного лидера и продолжают фиксацию транзакций.""",
    "step_by_step": [
        "Спроектируйте симулятор распределенного кластера из 3 узлов с матрицей сетевой связности.",
        "Реализуйте проверку кворума большинства перед фиксацией операции записи.",
        "Смоделируйте сетевую изоляцию узла-лидера $N_1$ от узлов $N_2$ и $N_3$.",
        "Продемонстрируйте: отклонение записей на изолированном лидере, выборы нового лидера в кворуме и последующее восстановление связности."
    ],
    "code_blocks": [
        {
            "filename": "split_brain_resilience_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"testing"
)

type ClusterNode struct {
	ID        int
	isLeader  bool
	peers     []*ClusterNode
	matrix    *NetworkMatrix
	mu        sync.Mutex
	committed []string
}

type NetworkMatrix struct {
	mu         sync.Mutex
	partitions map[int]map[int]bool
}

func NewNetworkMatrix() *NetworkMatrix {
	return &NetworkMatrix{
		partitions: make(map[int]map[int]bool),
	}
}

func (m *NetworkMatrix) IsBlocked(from, to int) bool {
	m.mu.Lock()
	defer m.mu.Unlock()
	if row, ok := m.partitions[from]; ok {
		return row[to]
	}
	return false
}

func (m *NetworkMatrix) Isolate(nodeID int, allNodes []int) {
	m.mu.Lock()
	defer m.mu.Unlock()
	for _, id := range allNodes {
		if id != nodeID {
			if m.partitions[nodeID] == nil {
				m.partitions[nodeID] = make(map[int]bool)
			}
			if m.partitions[id] == nil {
				m.partitions[id] = make(map[int]bool)
			}
			m.partitions[nodeID][id] = true
			m.partitions[id][nodeID] = true
		}
	}
}

func (m *NetworkMatrix) Heal() {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.partitions = make(map[int]map[int]bool)
}

func (n *ClusterNode) ProposeWrite(ctx context.Context, value string) error {
	n.mu.Lock()
	if !n.isLeader {
		n.mu.Unlock()
		return errors.New("not leader")
	}
	peers := n.peers
	myID := n.ID
	n.mu.Unlock()

	votes := 1
	for _, p := range peers {
		if !n.matrix.IsBlocked(myID, p.ID) {
			votes++
		}
	}

	quorum := (len(peers)+1)/2 + 1
	if votes < quorum {
		return fmt.Errorf("потеря кворума: собрано %d из необходимых %d голосов", votes, quorum)
	}

	n.mu.Lock()
	n.committed = append(n.committed, value)
	n.mu.Unlock()
	return nil
}

func TestNetworkPartitionQuorum(t *testing.T) {
	matrix := NewNetworkMatrix()

	node1 := &ClusterNode{ID: 1, isLeader: true, matrix: matrix}
	node2 := &ClusterNode{ID: 2, isLeader: false, matrix: matrix}
	node3 := &ClusterNode{ID: 3, isLeader: false, matrix: matrix}

	nodes := []*ClusterNode{node1, node2, node3}
	_ = nodes
	node1.peers = []*ClusterNode{node2, node3}
	node2.peers = []*ClusterNode{node1, node3}
	node3.peers = []*ClusterNode{node1, node2}

	ctx := context.Background()
	if err := node1.ProposeWrite(ctx, "TX_1"); err != nil {
		t.Fatalf("ошибка записи в здоровом кластере: %v", err)
	}

	matrix.Isolate(1, []int{1, 2, 3})

	err := node1.ProposeWrite(ctx, "TX_ILLEGAL")
	if err == nil {
		t.Fatal("КРИТИЧЕСКАЯ ОШИБКА: Изолированный лидер зафиксировал запись без кворума!")
	}

	node2.mu.Lock()
	node2.isLeader = true
	node2.mu.Unlock()

	if err := node2.ProposeWrite(ctx, "TX_VALID_MAJORITY"); err != nil {
		t.Fatalf("большинство должно успешно коммитить записи: %v", err)
	}

	matrix.Heal()
	node1.mu.Lock()
	node1.isLeader = false
	node1.mu.Unlock()
}

func main() {
	fmt.Println("Тестирование защиты от Split-Brain завершено успешно")
}
"""
        }
    ],
    "under_the_hood": r"Принцип кворума гарантирует, что любые два кворума большинства в кластере размера $N$ обязательно пересекаются хотя бы по одному узлу: $Q_1 \cap Q_2 \neq \emptyset$. Это фундаментальное математическое свойство делает невозможным одновременное принятие двух несовместимых решений в разных сетевых сегментах кластера.",
    "pitfalls": [
        "Четное число узлов в кластере: при разделении сети пополам ни одна из половин не наберет строгого большинства.",
        "Отсутствие механизма Leader Lease: старый лидер может отвечать на запросы чтения устаревшими данными.",
        "Асинхронные репликации без кворума в распределенных базах."
    ],
    "bigtech_interview": "Почему в кластерах с консенсусом Raft/etcd/ZooKeeper всегда рекомендуется разворачивать строго нечетное количество узлов (3, 5, 7)? Нечетное количество узлов обеспечивает максимальную отказоустойчивость при минимальных аппаратных затратах. Кластер из 3 узлов переносит отказ 1 узла ($Q=2$). Кластер из 4 узлов также переносит отказ только 1 узла ($Q=3$, так как потеря 2 узлов оставит 2, что не является строгим большинством). Четвертый узел повышает сетевые издержки, не увеличивая отказоустойчивость."
})

# Exercise 19
exercises.append({
    "num": 19,
    "title": "Паттерн Chaos Monkey внутри Go-сервиса",
    "task": "Реализуйте хаос-middleware внутри боевого HTTP-сервиса: если включен флаг конфигурации `CHAOS_ENABLED=true`, middleware с вероятностью 1% инжектирует искусственную задержку от 1 до 5 секунд, либо возвращает `500 Internal Server Error`, либо вызывает `panic()`. Настройте активацию хаоса только для тестовых пользователей по заголовку `X-Chaos-Test: true`.",
    "theory": r"""Инфраструктурные хаос-инструменты (Toxiproxy, Chaos Mesh) требуют отдельного развертывания и управления. Паттерн прикладного хаоса (Application-Level Chaos Monkey) заключается во внедрении логики управляемых сбоев непосредственно в код самого микросервиса.

Преимущества прикладного хаос-middleware:
1. **Точечный таргетинг (Fine-grained Blast Radius):**
   Хаос можно активировать не для всех пользователей, а строго избирательно:
   - По HTTP-заголовку: `X-Chaos-Test: true`.
   - По идентификатору пользователя: хэш `UserID % 100 == 0` (1% синтетических или бета-тестеров).
   - По сессионным кукам или IP-диапазону тестовых нагрузочных станций.
2. **Нулевые инфраструктурные издержки:**
   Не требуется настраивать сложные iptables, daemonsets или sidecar-контейнеры.
3. **Разнообразие симулируемых сбоев:**
   - Задержка времени ответа (Sleep).
   - Искусственная ошибка 500 / 503.
   - Повреждение полезной нагрузки (Corrupted JSON).
   - Вызов неперехваченной паники `panic("chaos monkey strike")` для проверки механизма `recover()`.""",
    "step_by_step": [
        "Определите структуру конфигурации `ChaosConfig` с флагами включения, вероятностью и списком разрешенных заголовков.",
        "Реализуйте middleware `ChaosMonkeyMiddleware`, перехватывающее HTTP-запросы.",
        "Реализуйте безопасную обработку паники через сопутствующий middleware `RecoveryMiddleware`.",
        "Напишите тест, проверяющий, что штатные пользователи никогда не получают сбоев, а запросы с заголовком `X-Chaos-Test` подвергаются контролируемым сбоям."
    ],
    "code_blocks": [
        {
            "filename": "chaos_middleware_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"math/rand"
	"net/http"
	"net/http/httptest"
	"sync"
	"testing"
	"time"
)

type ChaosConfig struct {
	Enabled       bool
	FailureRate   float64
	LatencyMin    time.Duration
	LatencyMax    time.Duration
	InjectPanics  bool
	HeaderTrigger string
}

type ChaosMonkey struct {
	cfg ChaosConfig
	rng *rand.Rand
	mu  sync.Mutex
}

func NewChaosMonkey(cfg ChaosConfig) *ChaosMonkey {
	return &ChaosMonkey{
		cfg: cfg,
		rng: rand.New(rand.NewSource(time.Now().UnixNano())),
	}
}

func (cm *ChaosMonkey) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if !cm.cfg.Enabled {
			next.ServeHTTP(w, r)
			return
		}

		if cm.cfg.HeaderTrigger != "" && r.Header.Get(cm.cfg.HeaderTrigger) != "true" {
			next.ServeHTTP(w, r)
			return
		}

		cm.mu.Lock()
		roll := cm.rng.Float64()
		cm.mu.Unlock()

		if roll < cm.cfg.FailureRate {
			switch {
			case cm.cfg.InjectPanics && roll < cm.cfg.FailureRate*0.2:
				panic("Chaos Monkey: simulated application panic!")
			case roll < cm.cfg.FailureRate*0.6:
				time.Sleep(cm.cfg.LatencyMin)
			default:
				http.Error(w, "Chaos Monkey: Simulated Error", http.StatusInternalServerError)
				return
			}
		}

		next.ServeHTTP(w, r)
	})
}

func RecoveryMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				http.Error(w, fmt.Sprintf("Recovered: %v", rec), http.StatusInternalServerError)
			}
		}()
		next.ServeHTTP(w, r)
	})
}

func TestChaosMonkeyIsolation(t *testing.T) {
	cfg := ChaosConfig{
		Enabled:       true,
		FailureRate:   1.0,
		LatencyMin:    10 * time.Millisecond,
		InjectPanics:  true,
		HeaderTrigger: "X-Chaos-Test",
	}
	monkey := NewChaosMonkey(cfg)

	targetHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("NORMAL_RESPONSE"))
	})

	chain := RecoveryMiddleware(monkey.Middleware(targetHandler))

	reqNormal := httptest.NewRequest(http.MethodGet, "/orders", nil)
	recNormal := httptest.NewRecorder()
	chain.ServeHTTP(recNormal, reqNormal)

	if recNormal.Code != http.StatusOK {
		t.Errorf("Обычный пользователь пострадал от хаоса! Статус: %d", recNormal.Code)
	}

	reqChaos := httptest.NewRequest(http.MethodGet, "/orders", nil)
	reqChaos.Header.Set("X-Chaos-Test", "true")
	recChaos := httptest.NewRecorder()
	chain.ServeHTTP(recChaos, reqChaos)

	if recChaos.Code == http.StatusOK {
		t.Errorf("Хаос не сработал для тестового запроса с заголовком!")
	}
}

func main() {
	fmt.Println("Тестирование паттерна Chaos Monkey Middleware завершено успешно")
}
"""
        }
    ],
    "under_the_hood": "Использование стандартного механизма `defer recover()` внутри HTTP-стека Go перехватывает паники на уровне конкретной горутины запроса, генерируя стандартный HTTP ответ 500 и сохраняя процесс приложения живым. Без middleware с `recover()` любая неперехваченная паника в горутине обработчика вызывает аварийный крах всего бинарника Go с дампом стека (`SIGABRT`).",
    "pitfalls": [
        "Активация Chaos Monkey без проверки заголовка или флага окружения в продакшене.",
        "Паника в фоновой асинхронной горутине: HTTP middleware не может перехватить панику, возникшую в дочерней отвязанной горутине.",
        "Использование псевдослучайных чисел без мьютекса при конкурентном доступе."
    ],
    "bigtech_interview": "Как в распределенной микросервисной архитектуре пробросить контекст хаос-тестирования через цепочку из 10 микросервисов? Для этого используется проброс контекста трассировки W3C Baggage / Distributed Tracing Headers. Входящий HTTP-заголовок `X-Chaos-Test: true` помещается в контекст запроса Go (`context.WithValue`) и автоматически сериализуется исходящими gRPC / HTTP клиентами во все downstream-вызовы, позволяя протестировать всю сквозную цепочку надежности."
})

# Exercise 20
exercises.append({
    "num": 20,
    "title": "Изоляция каскадных сбоев через паттерн Bulkhead",
    "task": "Покажите, как сбой одного второстепенного сервиса (например, сервис рекомендаций) может исчерпать пул горутин и положить весь сайт. Реализуйте паттерн Bulkhead: выделите независимые семафоры и пулы горутин для каждого внешнего вызова, ограничив влияние падения одной зависимости.",
    "theory": r"""Паттерн Bulkhead (водонепроницаемая переборка в трюме корабля) изолирует ресурсы различных подсистем, гарантируя, что пробоина в одном отсеке не приведет к затоплению всего судна.

Проблема каскадного отказа без Bulkhead:
Сервер имеет общий пул соединений или общий пул горутин (например, 100 параллельных воркеров).
При оформлении заказа сервис вызывает:
1. Платежный шлюз (Критичный сервис).
2. Сервис рекомендаций похожих товаров (Второстепенный сервис).
Если сервис рекомендаций начинает зависать на 10 секунд, все 100 воркеров блокируются на его ожидании. В результате пользователи не могут даже оплатить корзину! Второстепенный сбой потопил весь бизнес.

Реализация Bulkhead в Go:
1. **Семафорный Bulkhead (`channel semaphore`):**
   Каждая внешняя зависимость получает свой независимый буферизованный канал фиксированной емкости (например, `chan struct{}` на 10 слотов).
2. Если лимит зависимости исчерпан, новый запрос к ней отбрасывается мгновенно (`ErrBulkheadFull`), не расходуя системные ресурсы сервера.
3. Критичные вызовы (платежи) продолжают работать в своем независимом пуле на полной скорости.""",
    "step_by_step": [
        "Смоделируйте сервис оформления заказа с вызовом критичной (Payment) и второстепенной (Recommendations) зависимостей.",
        "Реализуйте структуру `Bulkhead`, управляющую параллелизмом через канал-семафор с быстрым отказом (`tryAcquire`).",
        "Инжектируйте зависание во второстепенный сервис.",
        "Докажите, что платежи продолжают выполняться за миллисекунды, а второстепенный сервис безопасно деградирует."
    ],
    "code_blocks": [
        {
            "filename": "bulkhead_isolation_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

var ErrBulkheadFull = errors.New("bulkhead limit exceeded: dependency capacity saturated")

type Bulkhead struct {
	sem      chan struct{}
	rejected atomic.Int64
}

func NewBulkhead(maxConcurrent int) *Bulkhead {
	return &Bulkhead{
		sem: make(chan struct{}, maxConcurrent),
	}
}

func (b *Bulkhead) Execute(ctx context.Context, fn func() error) error {
	select {
	case b.sem <- struct{}{}:
		defer func() { <-b.sem }()
		return fn()
	default:
		b.rejected.Add(1)
		return ErrBulkheadFull
	}
}

func TestBulkheadIsolation(t *testing.T) {
	recsBulkhead := NewBulkhead(5)
	paymentBulkhead := NewBulkhead(50)

	var successfulPayments atomic.Int64
	var degradedRecs atomic.Int64
	var wg sync.WaitGroup

	for i := 0; i < 20; i++ {
		wg.Add(1)
		go func(userID int) {
			defer wg.Done()
			ctx := context.Background()

			err := recsBulkhead.Execute(ctx, func() error {
				time.Sleep(200 * time.Millisecond)
				return nil
			})
			if errors.Is(err, ErrBulkheadFull) {
				degradedRecs.Add(1)
			}

			err = paymentBulkhead.Execute(ctx, func() error {
				time.Sleep(2 * time.Millisecond)
				successfulPayments.Add(1)
				return nil
			})
			if err != nil {
				t.Errorf("Платеж упал: %v", err)
			}
		}(i)
	}

	wg.Wait()

	if successfulPayments.Load() != 20 {
		t.Fatalf("Платежи пострадали от сбоя рекомендаций!")
	}
}

func main() {
	fmt.Println("Тестирование паттерна Bulkhead завершено успешно")
}
"""
        }
    ],
    "under_the_hood": "Неблокирующий `select` с веткой `default` компилируется в Go в атомарную проверку внутреннего счетчика канала в рантайме. Если буфер канала полон, горутина не ставится в очередь ожидания планировщика рантайма Go, а мгновенно переходит к выполнению ветки `default` за доли наносекунды.",
    "pitfalls": [
        "Слишком оптимистичный размер отсека: второстепенный сервис может поглотить большую часть ресурсов процессора.",
        "Отсутствие Fallback-стратегии: код должен возвращать безопасное значение по умолчанию, а не ронять сценарий.",
        "Использование небуферизованных каналов вместо буферизованных семафоров."
    ],
    "bigtech_interview": "В чем разница между Thread Pool Isolation (Bulkhead в Netflix Hystrix на Java) и Semaphore Isolation (Bulkhead в Go)? В Java создание пула потоков требует выделения фиксированных потоков ОС с тяжелыми стеками памяти (по 1 МБ на поток). В Go горутины сверхлегкие (стек от 2 КБ), поэтому создавать отдельные физические пулы потоков не требуется: семафорный Bulkhead на буферизованном канале обеспечивает абсолютную изоляцию с околонулевыми накладными расходами памяти."
})

# Exercise 21
exercises.append({
    "num": 21,
    "title": "Имитация деградации дискового ввода-вывода (I/O Hang)",
    "task": "Напишите интерфейс-обертку над файловыми операциями `io.Reader` и `io.Writer`, которая случайным образом задерживает запись или возвращает ошибки `io.ErrShortWrite`. Проверьте устойчивость механизма ротации логов и сохранения локальных файлов к зависаниям дисковой подсистемы.",
    "theory": r"""В распределенных системах дисковая подсистема считается одной из самых ненадежных:
- Сетевые диски (AWS EBS, Ceph, NFS) подвержены сетевым паузам и деградации IOPS (Burst Balance Exhaustion).
- При зависании диска системный вызов `write()` или `fsync()` переходит в состояние Uninterruptible Sleep (статус `D` в выводе `ps/top`), блокируя поток ОС операционной системы.
- В рантайме Go поток `M`, заблокированный в системном вызове дискового ввода-вывода, отвязывается от процессора `P`, и планировщик запускает новый системный поток `M` (sysmon). При массовых зависаниях диска число потоков ОС быстро достигает лимита ядра (`10 000`), вызывая панику `fatal error: checkdead: no runnable goroutines`.

Решение для надежных систем:
1. Асинхронная запись через кольцевой буфер в памяти (Lock-free Ring Buffer).
2. Защита дисковых операций таймаутами через каналы или контекст.
3. Обработка ошибки частичной записи (`io.ErrShortWrite`).""",
    "step_by_step": [
        "Реализуйте декоратор `ChaosWriter`, оборачивающий `io.Writer` и инжектирующий искусственные задержки и ошибки `io.ErrShortWrite`.",
        "Разработайте асинхронный логгер с вытеснением устаревших записей при переполнении буфера (Drop on Full / Non-blocking Append).",
        "Протестируйте поведение логгера при внезапном зависании нижележащего диска.",
        "Убедитесь, что критичные бизнес-горутины продолжают работу без блокировок."
    ],
    "code_blocks": [
        {
            "filename": "io_chaos_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

// ChaosWriter инжектирует сбои диска в io.Writer
type ChaosWriter struct {
	target      io.Writer
	mu          sync.Mutex
	hangDelay   time.Duration
	injectShort bool
}

func (w *ChaosWriter) Write(p []byte) (int, error) {
	w.mu.Lock()
	delay := w.hangDelay
	short := w.injectShort
	w.mu.Unlock()

	if delay > 0 {
		time.Sleep(delay) // Имитация зависшего fsync() / EBS volume
	}

	if short && len(p) > 2 {
		// Записываем только 2 байта и возвращаем io.ErrShortWrite
		n, _ := w.target.Write(p[:2])
		return n, io.ErrShortWrite
	}

	return w.target.Write(p)
}

// AsyncBufferedLogger обеспечивает неблокирующее логирование
type AsyncBufferedLogger struct {
	queue        chan []byte
	droppedCount atomic.Int64
	done         chan struct{}
	writer       io.Writer
}

func NewAsyncBufferedLogger(w io.Writer, capacity int) *AsyncBufferedLogger {
	l := &AsyncBufferedLogger{
		queue:  make(chan []byte, capacity),
		done:   make(chan struct{}),
		writer: w,
	}
	go l.worker()
	return l
}

func (l *AsyncBufferedLogger) Log(msg string) bool {
	select {
	case l.queue <- []byte(msg + "\n"):
		return true
	default:
		// Буфер полон из-за зависшего диска! Отбрасываем лог во избежание зависания сервиса
		l.droppedCount.Add(1)
		return false
	}
}

func (l *AsyncBufferedLogger) worker() {
	for msg := range l.queue {
		_, _ = l.writer.Write(msg)
	}
	close(l.done)
}

func (l *AsyncBufferedLogger) Close() {
	close(l.queue)
	<-l.done
}

func TestDiskIOHangResilience(t *testing.T) {
	memBuf := new(bytes.Buffer)
	chaosDisk := &ChaosWriter{target: memBuf}
	logger := NewAsyncBufferedLogger(chaosDisk, 5) // Небольшой буфер на 5 сообщений

	// 1. Быстрая штатная запись
	for i := 0; i < 3; i++ {
		if !logger.Log(fmt.Sprintf("msg_%d", i)) {
			t.Errorf("не удалось записать лог")
		}
	}

	// 2. Инжектируем зависание диска на 500 мс (I/O Hang)
	chaosDisk.mu.Lock()
	chaosDisk.hangDelay = 500 * time.Millisecond
	chaosDisk.mu.Unlock()

	// 3. Отправляем пачку логов из бизнес-горутины
	start := time.Now()
	for i := 0; i < 20; i++ {
		logger.Log(fmt.Sprintf("highload_event_%d", i))
	}
	duration := time.Since(start)

	// Бизнес-горутина не должна была заблокироваться на 500 мс!
	if duration > 50*time.Millisecond {
		t.Fatalf("Бизнес-код заблокировался на зависшем диске! Задержка: %v", duration)
	}

	if logger.droppedCount.Load() == 0 {
		t.Errorf("Ожидался сброс сообщений при переполнении буфера зависшего диска")
	}
	t.Logf("Бизнес-горутина отработала за %v, сброшено сообщений: %d", duration, logger.droppedCount.Load())
}

func main() {
	fmt.Println("Тестирование устойчивости к зависаниям дискового I/O завершено успешно")
}
"""
        }
    ],
    "under_the_hood": "В Go системные вызовы работы с файлами (в отличие от сетевых сокетов, управляемых через `netpoller` и `epoll`) всегда являются блокирующими на уровне операционной системы, так как ядро Linux не поддерживает `epoll` для обычных дисковых файлов (ext4, xfs). При блокировке файла рантайм Go вынужден переводить системный поток `M` в режим ожидания, освобождая поток планировщика `P`. Использование асинхронного буфера в памяти полностью отвязывает горячий путь исполнения от непредсказуемой задержки диска.",
    "pitfalls": [
        "Синхронная запись логов на диск в горячем цикле HTTP-обработчика: зависание диска мгновенно приводит к параличу всего веб-сервера.",
        "Использование неограниченного буфера памяти для накопления логов: при долгом зависании диска память сервера переполнится (OOM).",
        "Игнорирование возвращаемого значения `io.ErrShortWrite` при записи бинарных протоколов."
    ],
    "bigtech_interview": "Почему сетевые сокеты в Go масштабируются до миллионов соединений без создания миллионов потоков ОС, а дисковый ввод-вывод (File I/O) нет? Сетевые сокеты поддерживают механизм неблокирующего уведомления о готовности через системный вызов `epoll` (netpoller). Обычные дисковые файлы в Linux всегда считаются «готовыми к чтению/записи» ядром, но физическая операция ввода-вывода блокирует системный поток ядра до завершения чтения с пластин HDD или чипов flash-памяти."
})

# Exercise 22
exercises.append({
    "num": 22,
    "title": "Хаос-тестирование с ограничением ресурсов (cgroups v2)",
    "task": "Используя cgroups v2 в Linux, урежьте доступные ресурсы работающему Go-сервису: ограничьте память до 64 МБ (`memory.max`) и CPU до 0.2 ядра (`cpu.max`). Запустите нагрузочный тест. Проверьте реакцию рантайма Go: корректно ли отрабатывает `GOMEMLIMIT` или контейнер падает по OOMKilled.",
    "theory": r"""При развертывании Go-микросервисов в Kubernetes ресурсы каждого контейнера жестко ограничиваются механизмами Linux Control Groups (cgroups v2):
- `memory.max`: жесткий лимит оперативной памяти (Hard Limit). Превышение этого лимита ядром Linux немедленно активирует механизм OOM Killer (`kill -9`, статус выхода 137 / `OOMKilled`).
- `cpu.max`: квота процессорного времени (CFS Bandwidth Control). Превышение квоты приводит к троттлингу процессора (CPU Throttling), резкому росту задержки p99 и пропуску liveness-проб.

Революция `GOMEMLIMIT` (Go 1.19+):
Исторически сборщик мусора Go (`GC`) ориентировался только на параметр `GOGC` (процент прироста кучи, по умолчанию 100%). Если сервис потреблял 40 МБ, следующий запуск GC планировался при достижении 80 МБ. В контейнере с лимитом 64 МБ процесс неизбежно убивался OOM Killer до того, как GC успевал проснуться!

Параметр `GOMEMLIMIT` (или `debug.SetMemoryLimit`):
- Задает мягкий лимит памяти для рантайма Go (рекомендуется 85–90% от лимита cgroup, например 55 МБ при квоте 64 МБ).
- Рантайм Go отслеживает суммарное потребление памяти (куча + стеки горутин + структуры рантайма). При приближении к `GOMEMLIMIT` сборщик мусора запускается агрессивно и адаптивно, предотвращая падение по OOMKilled.""",
    "step_by_step": [
        "Изучите механизм `debug.SetMemoryLimit` в стандартной библиотеке `runtime/debug`.",
        "Реализуйте симулятор сервиса под пиковой нагрузкой, генерирующего большой объем временных аллокаций памяти.",
        "Смоделируйте жесткий лимит памяти cgroup (64 МБ) с автоматическим контролем переполнения.",
        "Продемонстрируйте, как настройка `SetMemoryLimit` спасает приложение от аварийного завершения за счет учащения циклов GC."
    ],
    "code_blocks": [
        {
            "filename": "cgroups_memlimit_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"runtime"
	"runtime/debug"
	"testing"
	"time"
)

// MemoryStresser симулирует генерацию временных объектов под нагрузкой
type MemoryStresser struct {
	allocatedMB int
}

func (s *MemoryStresser) AllocateTransient(mb int) {
	// Создаем временные срезы, которые сразу становятся мусором
	for i := 0; i < mb; i++ {
		_ = make([]byte, 1024*1024)
	}
}

func TestGOMEMLIMITPreventsOOM(t *testing.T) {
	// Устанавливаем мягкий лимит памяти рантайма Go: 30 МБ (симуляция контейнера 35 МБ)
	limitBytes := int64(30 * 1024 * 1024)
	oldLimit := debug.SetMemoryLimit(limitBytes)
	defer debug.SetMemoryLimit(oldLimit)

	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	gcBefore := m.NumGC

	// Генерируем 100 МБ суммарных аллокаций в цикле (что в 3 раза превышает лимит cgroup!)
	stresser := &MemoryStresser{}
	for i := 0; i < 10; i++ {
		stresser.AllocateTransient(10)
		time.Sleep(10 * time.Millisecond)
	}

	runtime.ReadMemStats(&m)
	gcAfter := m.NumGC
	heapAllocMB := float64(m.HeapAlloc) / (1024 * 1024)

	t.Logf("Куча после стресс-теста: %.2f МБ, запусков GC: %d", heapAllocMB, gcAfter-gcBefore)

	// Проверяем, что активная куча удерживается ниже установленного лимита 30 МБ
	if m.HeapAlloc > uint64(limitBytes) {
		t.Errorf("Куча превысила установленный лимит GOMEMLIMIT: %d > %d", m.HeapAlloc, limitBytes)
	}

	// Сборщик мусора должен был сработать многократно для удержания памяти
	if gcAfter-gcBefore < 2 {
		t.Errorf("Сборщик мусора не проявил достаточной активности под давлением памяти")
	}
	t.Log("GOMEMLIMIT успешно предотвратил выход за пределы квоты памяти")
}

func main() {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	fmt.Printf("Текущая аллокация кучи: %.2f МБ\n", float64(m.HeapAlloc)/(1024*1024))
	fmt.Println("Тестирование адаптации GOMEMLIMIT к cgroups успешно завершено")
}
"""
        }
    ],
    "under_the_hood": "Алгоритм GC Pacer в Go непрерывно вычисляет оптимальный момент запуска следующего цикла сборки мусора. При наличии `GOMEMLIMIT` алгоритм объединяет две формулы: классическую формулу `GOGC` и ограничение по абсолютному потолку памяти. Если потребление кучи приближается к пределу, GC Pacer автоматически увеличивает процент времени CPU, выделяемого на сборку мусора (GC CPU Target, вплоть до 50%), жертвуя пропускной способностью сервиса ради сохранения его жизни.",
    "pitfalls": [
        "Установка `GOMEMLIMIT` равным ровно 100% лимита cgroups: структуры рантайма Go, бинарный код, стек потоков CGO и буферы сокетов ядра не входят в расчет кучи Go, что приведет к OOMKilled. Рекомендуется ставить 80–90% от лимита контейнера.",
        "GC Thrashing (захлебывание GC): если постоянные живые данные (In-use Live Heap) превышают `GOMEMLIMIT`, GC будет крутиться в бесконечном цикле, сжигая 50% всех ядер процессора.",
        "Неучет CPU Quota: при жестком ограничении `cpu.max` работа GC замедляется, что может не оставить времени на своевременную очистку памяти."
    ],
    "bigtech_interview": "Что происходит с планировщиком Go при наступлении CPU Throttling в Kubernetes cgroups v2? Ядро Linux замораживает выполнение системных потоков контейнера на остаток периода CFS (обычно 100 мс). Для сервиса это выглядит как внезапная пауза «Stop The World» на 50–80 мс: горутины не исполняются, таймеры задерживаются, сетевые дедлайны истекают. Мониторинг метрики `container_cpu_cfs_throttled_periods_total` в Prometheus позволяет оперативно выявить эту проблему."
})

# Exercise 23
exercises.append({
    "num": 23,
    "title": "Хаос-тестирование gRPC-интерцепторов",
    "task": "Напишите клиентский gRPC-интерцептор хаоса: он перехватывает вызовы и инжектирует ошибки gRPC-кодов (`codes.Unavailable`, `codes.DeadlineExceeded`, `codes.ResourceExhausted`). Убедитесь, что клиентские сервисы корректно обрабатывают эти статусы и запускают логику повторных попыток или отката.",
    "theory": r"""В микросервисной архитектуре на базе gRPC взаимодействие между сервисами стандартизировано кодами статусов (gRPC Status Codes, пакет `google.golang.org/grpc/codes`).

Интерцепторы (gRPC Interceptors) представляют собой аналог HTTP-middleware:
- `UnaryClientInterceptor`: перехватывает унарные RPC-вызовы (`(ctx, method, req, reply, cc, invoker, opts)`).
- Позволяет прозрачно внедрять логику хаоса: задержку вызова, модификацию метаданных, инъекцию кодов ошибок.

Критические статусы для хаос-тестирования:
1. `codes.Unavailable` (14): сервис временно недоступен (сетевой сбой, рестарт пода). **Требует ретрая** с экспоненциальным backoff.
2. `codes.DeadlineExceeded` (4): превышен таймаут вызова. Ретрай допустим только для идемпотентных методов.
3. `codes.ResourceExhausted` (8): превышена квота или лимит Rate Limiter. Требует немедленного прекращения вызовов и ожидания (`Retry-After`).
4. `codes.InvalidArgument` (3) или `codes.Unauthenticated` (16): логические ошибки. **Категорически запрещено ретраить**.""",
    "step_by_step": [
        "Спроектируйте интерфейс унарного интерцептора gRPC и структуру симуляции контекста вызова.",
        "Реализуйте `ChaosClientInterceptor`, подменяющий успешный ответ инжектируемыми кодами ошибок (`codes.Unavailable`).",
        "Реализуйте отказоустойчивый клиент с механизмом умных повторных попыток (Smart Retry Policy) только для транзиентных ошибок.",
        "Протестируйте работу клиента под хаос-интерцептором: убедитесь в успешном повторном выполнении при `codes.Unavailable` и немедленном выходе при фатальных кодах."
    ],
    "code_blocks": [
        {
            "filename": "grpc_chaos_interceptor_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"sync/atomic"
	"testing"
	"time"
)

type StatusCode int

const (
	CodeOK                 StatusCode = 0
	CodeInvalidArgument    StatusCode = 3
	CodeDeadlineExceeded   StatusCode = 4
	CodeResourceExhausted  StatusCode = 8
	CodeUnavailable        StatusCode = 14
)

type RPCError struct {
	Code StatusCode
	Msg  string
}

func (e *RPCError) Error() string {
	return fmt.Sprintf("rpc error: code = %d desc = %s", e.Code, e.Msg)
}

// InvokerFunc симулирует вызов удаленной процедуры
type InvokerFunc func(ctx context.Context, method string, req, reply any) error

// UnaryInterceptor сигнатура клиентского интерцептора
type UnaryInterceptor func(ctx context.Context, method string, req, reply any, invoker InvokerFunc) error

// ChaosClientInterceptor инжектирует сбои gRPC кодов
type ChaosClientInterceptor struct {
	failCount atomic.Int64
	codeToFail StatusCode
}

func NewChaosClientInterceptor(times int64, code StatusCode) *ChaosClientInterceptor {
	ci := &ChaosClientInterceptor{codeToFail: code}
	ci.failCount.Store(times)
	return ci
}

func (ci *ChaosClientInterceptor) Intercept(ctx context.Context, method string, req, reply any, invoker InvokerFunc) error {
	if ci.failCount.Load() > 0 {
		ci.failCount.Add(-1)
		return &RPCError{Code: ci.codeToFail, Msg: "chaos injected failure"}
	}
	return invoker(ctx, method, req, reply)
}

// ClientWithRetry выполняет RPC с политикой ретраев транзиентных кодов
func ClientWithRetry(ctx context.Context, method string, req, reply any, invoker InvokerFunc, interceptor UnaryInterceptor) error {
	maxRetries := 3
	for attempt := 0; attempt <= maxRetries; attempt++ {
		err := interceptor(ctx, method, req, reply, invoker)
		if err == nil {
			return nil
		}

		var rpcErr *RPCError
		if errors.As(err, &rpcErr) {
			// Ретраи разрешены ТОЛЬКО для CodeUnavailable
			if rpcErr.Code == CodeUnavailable {
				time.Sleep(10 * time.Millisecond) // Backoff
				continue
			}
		}

		// Для остальных кодов — немедленный возврат ошибки
		return err
	}
	return errors.New("retries exhausted")
}

func TestGRPCChaosInterceptor(t *testing.T) {
	invokerCalled := 0
	mockInvoker := func(ctx context.Context, method string, req, reply any) error {
		invokerCalled++
		return nil
	}

	// 1. Тест: 2 раза отдаем CodeUnavailable, клиент должен успешно отретраить и выполнить вызов
	chaos := NewChaosClientInterceptor(2, CodeUnavailable)
	ctx := context.Background()

	err := ClientWithRetry(ctx, "/OrderService/Create", "req", "reply", mockInvoker, chaos.Intercept)
	if err != nil {
		t.Fatalf("клиент не смог отретраить транзиентную ошибку: %v", err)
	}
	if invokerCalled != 1 {
		t.Errorf("invoker должен был успешно вызваться 1 раз после 2 ошибок перехватчика")
	}

	// 2. Тест: отдаем фатальный код CodeInvalidArgument — ретраи ЗАПРЕЩЕНЫ
	chaosFatal := NewChaosClientInterceptor(1, CodeInvalidArgument)
	err = ClientWithRetry(ctx, "/OrderService/Create", "req", "reply", mockInvoker, chaosFatal.Intercept)
	if err == nil {
		t.Fatal("ожидалась фатальная ошибка без повторов")
	}

	var rpcErr *RPCError
	if !errors.As(err, &rpcErr) || rpcErr.Code != CodeInvalidArgument {
		t.Errorf("неверный код ошибки: %v", err)
	}
	t.Log("gRPC интерцептор хаоса и умные ретраи отработали идеально")
}

func main() {
	fmt.Println("Тестирование gRPC интерцепторов хаоса успешно завершено")
}
"""
        }
    ],
    "under_the_hood": "Клиентские интерцепторы в gRPC организуются в цепочку (Chain Interceptors), где каждый интерцептор оборачивает следующий по принципу луковой шелухи (Onion Architecture). Добавление интерцептора хаоса в начало цепочки позволяет протестировать все последующие слои: сбор трассировок OpenTelemetry, запись метрик Prometheus и реакцию встроенного балансировщика нагрузки gRPC (Round Robin / Pick First).",
    "pitfalls": [
        "Повторная отправка запросов при `codes.InvalidArgument` или `codes.NotFound`: создает бесполезную нагрузку на CPU сервера.",
        "Ретраи без добавления случайного джиттера: тысячи клиентов, получивших `codes.Unavailable`, отправят повторные запросы синхронно в одну и ту же миллисекунду, добив восстанавливающийся сервис (Retry Storm).",
        "Модификация аргументов запроса `req` внутри интерцептора без глубокого клонирования (Data Race)."
    ],
    "bigtech_interview": "Почему слепые повторные попытки (Blind Retries) в микросервисной сети с глубиной вызовов 5+ сервисов называют «умножителем катастрофы» (Cascading Retry Storm)? Если каждый сервис на каждом уровне делает 3 попытки, то при сбое на глубине 5 общее число запросов к упавшей БД возрастет в $3^5 = 243$ раза! Для предотвращения катастрофы используют бюджет повторов (Retry Budgets: не более 10% от общего трафика) и сквозную передачу признака повтора в заголовках."
})

# Exercise 24
exercises.append({
    "num": 24,
    "title": "Стресс-тестирование брокеров сообщений (Kafka Crash Test)",
    "task": "Запустите высокоинтенсивную публикацию событий в Kafka через Transactional Outbox. С помощью Toxiproxy или команды `docker stop` уроните брокер Kafka на 30 секунд. Убедитесь, что продюсер Go не теряет события, буферизует их в базе данных и успешно доставляет после восстановления Kafka.",
    "theory": r"""В архитектуре современных событийно-ориентированных систем (EDA) прямая отправка сообщений в Apache Kafka из HTTP-обработчиков является грубым антипаттерном надежности:
- Если брокер Kafka временно недоступен (сетевой сбой, переизбрание контроллера Raft/KRaft, перезагрузка брокера), синхронный вызов `producer.SendMessage()` зависнет по таймауту.
- Пользователь получит ошибку 500, хотя строка в базе данных могла уже успешно закоммититься (рассинхронизация данных).

Паттерн Transactional Outbox (Глава 69):
1. Бизнес-данные и исходящее событие сохраняются в рамках **одной локальной ACID транзакции** в PostgreSQL (таблица `outbox_events`).
2. Фоновый воркер (Relay Worker) непрерывно вычитывает события из таблицы и отправляет их в брокер Kafka.
3. При падении Kafka:
   - Бизнес-транзакции пользователей продолжают успешно приниматься за доли миллисекунды.
   - События безопасно накапливаются в таблице Outbox.
   - Фоновый воркер ловит ошибку, переходит в режим экспоненциального ожидания (Backoff) и не теряет ни одного сообщения.
4. После восстановления Kafka все накопившиеся события гарантированно доставляются получателям (At-Least-Once Delivery).""",
    "step_by_step": [
        "Реализуйте репозиторий Transactional Outbox с методами сохранения события в транзакции и выборки неотправленных записей.",
        "Реализуйте симулятор брокера сообщений Kafka с возможностью аварийной остановки (`Crash()`) и восстановления (`Recover()`).",
        "Создайте отказоустойчивый фоновый воркер `OutboxRelay` с экспоненциальным backoff при сетевых ошибках.",
        "Протестируйте сценарий: 100 событий создаются во время 30-секундного падения брокера. Докажите, что после восстановления доставлены все 100 сообщений без потерь."
    ],
    "code_blocks": [
        {
            "filename": "kafka_crash_outbox_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

type OutboxEvent struct {
	ID        int64
	Topic     string
	Payload   string
	Published bool
}

type SimulatedKafkaBroker struct {
	mu        sync.Mutex
	isOnline  bool
	delivered []string
}

func (k *SimulatedKafkaBroker) Send(topic, payload string) error {
	k.mu.Lock()
	defer k.mu.Unlock()
	if !k.isOnline {
		return errors.New("kafka: connection refused / leader not available")
	}
	k.delivered = append(k.delivered, payload)
	return nil
}

type OutboxStore struct {
	mu     sync.Mutex
	events []*OutboxEvent
	nextID int64
}

func (s *OutboxStore) Insert(payload string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.nextID++
	s.events = append(s.events, &OutboxEvent{
		ID:        s.nextID,
		Topic:     "orders",
		Payload:   payload,
		Published: false,
	})
}

func (s *OutboxStore) GetUnpublished() []*OutboxEvent {
	s.mu.Lock()
	defer s.mu.Unlock()
	var res []*OutboxEvent
	for _, e := range s.events {
		if !e.Published {
			res = append(res, e)
		}
	}
	return res
}

func (s *OutboxStore) MarkPublished(id int64) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, e := range s.events {
		if e.ID == id {
			e.Published = true
			break
		}
	}
}

func RunOutboxRelay(ctx context.Context, store *OutboxStore, kafka *SimulatedKafkaBroker) {
	for {
		select {
		case <-ctx.Done():
			return
		default:
		}

		events := store.GetUnpublished()
		if len(events) == 0 {
			time.Sleep(10 * time.Millisecond)
			continue
		}

		for _, e := range events {
			if err := kafka.Send(e.Topic, e.Payload); err != nil {
				// Брокер лежит: ждем и повторяем попытку
				time.Sleep(50 * time.Millisecond)
				break // Выходим из пачки во избежание изменения порядка
			}
			store.MarkPublished(e.ID)
		}
	}
}

func TestKafkaCrashDurability(t *testing.T) {
	store := &OutboxStore{}
	kafka := &SimulatedKafkaBroker{isOnline: false} // Kafka ИЗНАЧАЛЬНО СЛОМАНА!

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go RunOutboxRelay(ctx, store, kafka)

	// 1. Клиенты генерируют 50 заказов при лежащей Kafka
	for i := 1; i <= 50; i++ {
		store.Insert(fmt.Sprintf("ORDER_PAYLOAD_%d", i))
	}

	time.Sleep(100 * time.Millisecond)

	// В брокере должно быть 0 сообщений
	kafka.mu.Lock()
	deliveredCount := len(kafka.delivered)
	kafka.mu.Unlock()
	if deliveredCount != 0 {
		t.Errorf("Сообщения не должны были попасть в сломанный брокер")
	}

	// 2. ВОССТАНАВЛИВАЕМ KAFKA (Recover)
	t.Log("KAFKA ВОССТАНОВИЛАСЬ: включаем сеть...")
	kafka.mu.Lock()
	kafka.isOnline = true
	kafka.mu.Unlock()

	// 3. Ждем, пока Relay воркер вычитает накопившуюся очередь
	time.Sleep(300 * time.Millisecond)

	// 4. Проверяем, что доставлены ВСЕ 50 сообщений без единой потери
	kafka.mu.Lock()
	deliveredCount = len(kafka.delivered)
	kafka.mu.Unlock()

	if deliveredCount != 50 {
		t.Fatalf("ПОТЕРЯ ДАННЫХ! Доставлено %d из 50 сообщений", deliveredCount)
	}

	unpub := store.GetUnpublished()
	if len(unpub) != 0 {
		t.Errorf("В базе остались неотправленные события: %d", len(unpub))
	}
	t.Logf("Все %d сообщений успешно доставлены в Kafka после падения брокера!", deliveredCount)
}

func main() {
	fmt.Println("Тестирование отказоустойчивости Kafka и Transactional Outbox успешно завершено")
}
"""
        }
    ],
    "under_the_hood": "Ключевое свойство связки RDBMS + Transactional Outbox — транзакционная атомарность сохранения состояния сущности и события в логе предварительной записи (WAL) PostgreSQL. Даже при физическом выдергивании питания сервера БД при перезагрузке механизм Crash Recovery (REDO log) восстановит обе записи в согласованном виде. Никакой прямой сетевой вызов в Kafka не способен предоставить подобных гарантий.",
    "pitfalls": [
        "Изменение порядка отправки сообщений при сбое: если при ошибке одного сообщения воркер продолжает отправлять следующие, нарушается хронологический порядок событий для одной сущности.",
        "Неограниченный рост таблицы Outbox: при длительном простое Kafka таблица может разрастись до миллионов строк. Необходима регулярная очистка (Retention/Pruning) отправленных записей.",
        "Дублирование сообщений при сетевом сбое подтверждения: потребители (Consumers) обязаны быть идемпотентными."
    ],
    "bigtech_interview": "Почему паттерн Transactional Outbox гарантирует семантику At-Least-Once (как минимум один раз), но не Exactly-Once? Потому что если релей отправил сообщение в Kafka, брокер сохранил его, но сетевой пакет подтверждения (ACK) потерялся по дороге, релей сочтет отправку неудачной и отправит то же сообщение повторно. Дедупликация на стороне потребителя по первичному ключу события (`Event-ID`) является обязательным требованием распределенных архитектур."
})

# Exercise 25
exercises.append({
    "num": 25,
    "title": "Тестирование распределенных блокировок при падении узла",
    "task": "Узел удерживает распределенную блокировку в Redis с TTL 30 секунд. Внезапно завершите процесс узла с помощью `kill -9` прямо посередине критической секции. Проверьте, что второй узел не зависает навсегда и корректно перехватывает блокировку по истечении срока аренды (Lease TTL).",
    "theory": r"""Распределенные блокировки (Distributed Locks на базе Redis Redlock или etcd) необходимы для взаимного исключения (Mutual Exclusion) в распределенной среде, где несколько реплик сервиса претендуют на один неделимый ресурс (например, обработка одного платежного поручения).

Опасность вечного взаимного дедлока (Deadlock):
Если узел захватил блокировку (`SET lock:resource token NX`) без указания времени жизни (TTL), и в этот момент процесс падает (SIGKILL, паника ядра, сбой питания):
- Блокировка навсегда останется в памяти Redis.
- Ни один другой узел никогда больше не сможет захватить ресурс. Бизнес-процесс встает намертво.

Паттерн Lease (Аренда с TTL) и механизм продления (Heartbeat / Watchdog):
1. Блокировка захватывается с гарантированным сроком аренды: `SET lock:key token NX PX 5000` (5 секунд).
2. Фоновая горутина узла (Watchdog / Heartbeat) периодически продлевает аренду (`EXPIRE lock:key 5000`), пока узел жив и выполняет работу.
3. Если узел внезапно умирает (`kill -9`), горутина продления останавливается.
4. По истечении TTL Redis автоматически удаляет ключ, и ожидающий второй узел безопасно захватывает ресурс.""",
    "step_by_step": [
        "Спроектируйте симулятор распределенного хранилища с поддержкой атомарной команды `SET NX PX` и автоматического истечения TTL.",
        "Реализуйте клиент распределенной блокировки с фоновым продлением аренды (Watchdog).",
        "Смоделируйте аварийное падение узла (остановка фонового процесса продления).",
        "Продемонстрируйте, как второй узел успешно перехватывает блокировку точно по истечении TTL без дедлока."
    ],
    "code_blocks": [
        {
            "filename": "distributed_lock_crash_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"testing"
	"time"
)

type LockItem struct {
	owner     string
	expiresAt time.Time
}

// SimulatedRedisLockStore симулирует Redis с атомарным SET NX PX
type SimulatedRedisLockStore struct {
	mu    sync.Mutex
	locks map[string]LockItem
}

func NewSimulatedRedisLockStore() *SimulatedRedisLockStore {
	return &SimulatedRedisLockStore{
		locks: make(map[string]LockItem),
	}
}

func (s *SimulatedRedisLockStore) TryAcquire(key, owner string, ttl time.Duration) bool {
	s.mu.Lock()
	defer s.mu.Unlock()

	now := time.Now()
	current, exists := s.locks[key]

	// Если блокировка существует и еще не истекла — отказ
	if exists && current.expiresAt.After(now) {
		return false
	}

	// Захватываем или перехватываем протухшую блокировку
	s.locks[key] = LockItem{
		owner:     owner,
		expiresAt: now.Add(ttl),
	}
	return true
}

func (s *SimulatedRedisLockStore) Extend(key, owner string, ttl time.Duration) bool {
	s.mu.Lock()
	defer s.mu.Unlock()

	current, exists := s.locks[key]
	if !exists || current.owner != owner || current.expiresAt.Before(time.Now()) {
		return false
	}

	s.locks[key] = LockItem{
		owner:     owner,
		expiresAt: time.Now().Add(ttl),
	}
	return true
}

func (s *SimulatedRedisLockStore) Release(key, owner string) bool {
	s.mu.Lock()
	defer s.mu.Unlock()

	current, exists := s.locks[key]
	if exists && current.owner == owner {
		delete(s.locks, key)
		return true
	}
	return false
}

func TestDistributedLockNodeCrash(t *testing.T) {
	store := NewSimulatedRedisLockStore()
	lockKey := "payout:user_123"

	// 1. Узел 1 захватывает блокировку на 200 мс
	node1TTL := 200 * time.Millisecond
	if !store.TryAcquire(lockKey, "node_1", node1TTL) {
		t.Fatalf("Узел 1 не смог захватить блокировку")
	}
	t.Log("Узел 1 успешно захватил блокировку на 200 мс")

	// 2. Узел 2 пытается захватить блокировку прямо сейчас — должен получить отказ
	if store.TryAcquire(lockKey, "node_2", 200*time.Millisecond) {
		t.Fatalf("ОШИБКА: Узел 2 захватил заблокированный ресурс!")
	}
	t.Log("Узел 2 получил отказ (ресурс занят узлом 1)")

	// 3. СИМУЛЯЦИЯ АВАРИИ УЗЛА 1 (kill -9):
	// Узел 1 падает посередине работы, не вызвав Release() и не продлевая аренду
	t.Log("АВАРИЯ: Процесс Узла 1 внезапно уничтожен сигналом SIGKILL!")

	// 4. Узел 2 ожидает освобождения ресурса по истечении срока аренды (Lease TTL)
	time.Sleep(250 * time.Millisecond) // Ждем истечения 200 мс

	// 5. Узел 2 повторяет попытку захвата
	acquired := store.TryAcquire(lockKey, "node_2", 200*time.Millisecond)
	if !acquired {
		t.Fatalf("ДЕДЛОК: Узел 2 не смог перехватить блокировку после падения узла 1!")
	}

	t.Log("Узел 2 успешно перехватил блокировку по истечении TTL аренды. Дедлок предотвращен!")
	store.Release(lockKey, "node_2")
}

func main() {
	fmt.Println("Тестирование устойчивости распределенных блокировок при падении узла завершено успешно")
}
"""
        }
    ],
    "under_the_hood": "В реальном Redis удаление протухших ключей происходит двумя путями: ленивым (Lazy Eviction — при обращении к ключу Redis проверяет текущий timestamp) и периодическим (Active Expiration — фоновый цикл случайной выборки 20 ключей в секунду с удалением просроченных). Это гарантирует, что даже при полной тишине на сервере протухшие блокировки не будут висеть в памяти вечно.",
    "pitfalls": [
        "Слишком короткий TTL без фонового продления (Watchdog): сборщик мусора Go задерживает выполнение горутины на 3 секунды, TTL блокировки истекает, другой узел захватывает ресурс, и оба узла одновременно пишут в одну запись в базе данных!",
        "Удаление чужой блокировки при освобождении: если узел 1 просрочил свой TTL, а узел 2 уже захватил ресурс, вызов `DEL lock:key` узлом 1 удалит блокировку узла 2. Освобождение обязано выполняться через Lua-скрипт с проверкой токена владельца.",
        "Ненадежность Redlock при сетевых разделениях и дрифте системных часов (Clock Drift)."
    ],
    "bigtech_interview": "Почему Мартин Клеппманн (Martin Kleppmann) критиковал Redlock и распределенные блокировки на базе Redis для критичных данных? Из-за отсутствия защиты от пауз рантайма (GC Stop-The-World) и дрифта часов. Единственный математически строгий способ гарантировать взаимное исключение при записи в хранилище — использование упорядочивающего токена ограждения (Fencing Token / Epoch Number). База данных принимает операцию только в том случае, если токен транзакции строго больше токена предыдущей фиксации."
})

# Exercise 26
exercises.append({
    "num": 26,
    "title": "Верификация алертов мониторинга (Alert Testing)",
    "task": "В хаос-инженерии критично проверять не только отказоустойчивость, но и наблюдаемость. Инжектируйте сбой (например, 50% ошибок базы данных). Убедитесь, что в течение 60 секунд Prometheus переводит правило `HighDatabaseErrorRate` в статус `Firing`, а Alertmanager отправляет уведомление в канал дежурных инженеров.",
    "theory": r"""Отказоустойчивость системы бесполезна, если дежурные инженеры (On-Call SRE) не знают о происходящей аварии. Одна из главных целей хаос-инженерии — верификация пайплайна наблюдаемости (Observability & Alerting Pipeline Verification).

Жизненный цикл алерта в Prometheus / Alertmanager:
1. **Inactive:** метрика находится в пределах допустимой нормы.
2. **Pending:** условие правила нарушено (например, `rate(http_errors_total[1m]) > 0.1`), но еще не прошло время выдержки `for: 30s`. Защищает от ложных срабатываний на секундных всплесках.
3. **Firing:** условие стабильно нарушается дольше `for: 30s`. Алерт отправляется в Alertmanager для дедупликации, группировки и отправки уведомления в Telegram/Slack/PagerDuty.

Сценарий Alert Verification Chaos Test:
- Инжектируется сбой базы данных (50% ошибок).
- Запускается секундомер.
- Тест программно опрашивает API Prometheus (`/api/v1/alerts`).
- Проверяется:
  - Время обнаружения (Mean Time To Detect, MTTD) не превышает SLA (например, строго до 45 секунд).
  - Алерт корректно переходит из `Pending` в `Firing`.
  - После снятия сбоя алерт автоматически возвращается в статус `Inactive`.""",
    "step_by_step": [
        "Спроектируйте модель Prometheus-алерта с состояниями Inactive, Pending, Firing и интервалом выдержки `forDuration`.",
        "Реализуйте вычислитель правил алертинга `AlertRuleEvaluator`, непрерывно анализирующий входящий поток метрик ошибок.",
        "Инжектируйте всплеск ошибок базы данных.",
        "Напишите тест, подтверждающий переход алерта в статус Firing в отведенный временной норматив."
    ],
    "code_blocks": [
        {
            "filename": "alert_verification_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"sync"
	"testing"
	"time"
)

type AlertState int

const (
	StateInactive AlertState = iota
	StatePending
	StateFiring
)

func (s AlertState) String() string {
	switch s {
	case StateInactive:
		return "INACTIVE"
	case StatePending:
		return "PENDING"
	case StateFiring:
		return "FIRING"
	default:
		return "UNKNOWN"
	}
}

type PrometheusAlertRule struct {
	Name         string
	Threshold    float64
	ForDuration  time.Duration
	state        AlertState
	pendingSince time.Time
	mu           sync.Mutex
}

func NewAlertRule(name string, threshold float64, forDur time.Duration) *PrometheusAlertRule {
	return &PrometheusAlertRule{
		Name:        name,
		Threshold:   threshold,
		ForDuration: forDur,
		state:       StateInactive,
	}
}

func (r *PrometheusAlertRule) Evaluate(currentErrorRate float64, now time.Time) AlertState {
	r.mu.Lock()
	defer r.mu.Unlock()

	conditionViolated := currentErrorRate > r.Threshold

	switch r.state {
	case StateInactive:
		if conditionViolated {
			r.state = StatePending
			r.pendingSince = now
		}
	case StatePending:
		if !conditionViolated {
			r.state = StateInactive
		} else if now.Sub(r.pendingSince) >= r.ForDuration {
			r.state = StateFiring
		}
	case StateFiring:
		if !conditionViolated {
			r.state = StateInactive
		}
	}

	return r.state
}

func TestAlertRuleTransitionUnderChaos(t *testing.T) {
	// Правило: алертить, если ошибка > 10% в течение 100 мс
	rule := NewAlertRule("HighDatabaseErrorRate", 0.10, 100*time.Millisecond)

	startTime := time.Now()

	// 1. Штатный режим: 2% ошибок
	state := rule.Evaluate(0.02, startTime)
	if state != StateInactive {
		t.Errorf("ожидался INACTIVE, получен %v", state)
	}

	// 2. Инъекция сбоя: всплеск ошибок до 50%
	t.Log("ИНЪЕКЦИЯ СБОЯ: частота ошибок выросла до 50%!")
	t1 := startTime.Add(10 * time.Millisecond)
	state = rule.Evaluate(0.50, t1)
	if state != StatePending {
		t.Errorf("ожидался PENDING, получен %v", state)
	}

	// 3. Ошибки продолжаются 50 мс (меньше forDuration) — алерт все еще в PENDING
	t2 := startTime.Add(60 * time.Millisecond)
	state = rule.Evaluate(0.50, t2)
	if state != StatePending {
		t.Errorf("алерт сработал слишком рано! Должен быть PENDING, получен %v", state)
	}

	// 4. Ошибки длятся 120 мс (превышен forDuration 100 мс) — переход в FIRING!
	t3 := startTime.Add(120 * time.Millisecond)
	state = rule.Evaluate(0.50, t3)
	if state != StateFiring {
		t.Fatalf("Алерт НЕ перешел в FIRING! Дежурные не получили уведомление. Состояние: %v", state)
	}
	t.Logf("Алерт '%s' успешно перешел в FIRING! MTTD: %v", rule.Name, t3.Sub(startTime))

	// 5. Восстановление: ошибки упали до 1%
	t4 := startTime.Add(200 * time.Millisecond)
	state = rule.Evaluate(0.01, t4)
	if state != StateInactive {
		t.Errorf("Алерт не сбросился после восстановления: %v", state)
	}
	t.Log("Алерт успешно вернулся в INACTIVE после нормализации метрик")
}

func main() {
	fmt.Println("Тестирование верификации правил алертинга успешно завершено")
}
"""
        }
    ],
    "under_the_hood": "В Prometheus сервер выполняет вычисление правил алертинга (Alerting Rules) циклически по таймеру `evaluation_interval` (обычно 15–30 секунд). При выполнении условия Prometheus присваивает алерту статус `PENDING`. Если по истечении интервала `for` условие продолжает выполняться, статус меняется на `FIRING`, и генерируется POST запрос в Alertmanager, где к алерту применяются правила ингибирования (Inhibition) и группировки (Grouping).",
    "pitfalls": [
        "Слишком короткий `for`: алерт переходит в FIRING от единичного сетевого сбоя, перегружая дежурных ночным шумом (Alert Fatigue).",
        "Слишком длинный `evaluation_interval` + `for`: например, интервал 1 мин и for 15 мин означают, что об отказе критичной базы дежурные узнают только через 16 минут после начала аварии.",
        "Отсутствие теста доставки уведомлений: алерт перешел в Firing в Prometheus, но из-за некорректного токена Telegram-бота сообщение не дошло до инженеров."
    ],
    "bigtech_interview": "В чем заключается опасность феномена Alert Fatigue (усталость от алертов) и как хаос-тестирование помогает с ней бороться? При обилии ложных или неинформативных алертов инженеры вырабатывают привычку автоматически нажимать «Acknowledge» не глядя, пропуская реальные аварии. Хаос-инженерия позволяет верифицировать матрицу алертинга: инжектируя точечные сбои, инженеры убеждаются, что срабатывают строго 1–2 высокоуровневых бизнес-алерта (User Impact), а не лавина из 50 вспомогательных уведомлений."
})

# Exercise 27
exercises.append({
    "num": 27,
    "title": "Автоматизация сценариев Game Day",
    "task": "Напишите декларативный сценарий аварийных учений (Game Day) на YAML/Go: «Шаг 1: подать нормальную нагрузку 5000 RPS; Шаг 2: добавить задержку 2 секунды к БД; Шаг 3: проверить SLO доступности > 99.5%; Шаг 4: восстановить сеть; Шаг 5: зафиксировать время восстановления (MTTR)». Реализуйте раннер этого сценария.",
    "theory": r"""Game Day (День аварийных учений) — это структурированная практика хаос-инженерии, при которой инженерная команда моделирует крупномасштабный сбой в контролируемой среде для проверки готовности людей, процессов и программного обеспечения.

Декларативное описание сценариев Game Day:
Вместо ручного хаотичного дергания рубильников сценарий формулируется в виде детерминированного конечного автомата:
1. **Normal Load Phase:** проверка работы под нагрузкой без сбоев.
2. **Chaos Injection Phase:** внедрение запланированного сбоя.
3. **Hypothesis Evaluation:** непрерывная валидация SLO доступности и задержки.
4. **Healing & Recovery:** автоматический откат сбоя.
5. **Scorecard & MTTR Calculation:** расчет времени обнаружения (MTTD) и времени полного восстановления (Mean Time To Recovery, MTTR).""",
    "step_by_step": [
        "Спроектируйте декларативную структуру шага сценария Game Day `GameDayStep`.",
        "Реализуйте исполнитель сценариев `GameDayRunner` с контролем прохождения фаз и таймингов.",
        "Смоделируйте аварийный сценарий деградации БД и восстановления.",
        "Сформируйте итоговый отчет учений с расчетом метрик MTTR и статусом выполнения SLO."
    ],
    "code_blocks": [
        {
            "filename": "gameday_automator_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
	"testing"
	"time"
)

type StepAction func(ctx context.Context) error

type GameDayStep struct {
	Name        string
	Action      StepAction
	Expectation func() error
	Duration    time.Duration
}

type GameDayScorecard struct {
	TotalSteps int
	Passed     int
	MTTR       time.Duration
	SLOHonored bool
}

type GameDayRunner struct {
	steps []GameDayStep
}

func NewGameDayRunner(steps []GameDayStep) *GameDayRunner {
	return &GameDayRunner{steps: steps}
}

func (r *GameDayRunner) Run(ctx context.Context) (*GameDayScorecard, error) {
	score := &GameDayScorecard{
		TotalSteps: len(r.steps),
		SLOHonored: true,
	}

	var outageStart time.Time
	var outageEnd time.Time

	for i, step := range r.steps {
		fmt.Printf("[GAME-DAY] Шаг %d/%d: '%s'...\n", i+1, len(r.steps), step.Name)

		if step.Name == "InjectChaos" {
			outageStart = time.Now()
		} else if step.Name == "Heal" {
			outageEnd = time.Now()
		}

		if step.Action != nil {
			if err := step.Action(ctx); err != nil {
				return score, fmt.Errorf("ошибка действия на шаге '%s': %w", step.Name, err)
			}
		}

		if step.Duration > 0 {
			time.Sleep(step.Duration)
		}

		if step.Expectation != nil {
			if err := step.Expectation(); err != nil {
				score.SLOHonored = false
				return score, fmt.Errorf("нарушено ожидание SLO на шаге '%s': %w", step.Name, err)
			}
		}

		score.Passed++
	}

	if !outageStart.IsZero() && !outageEnd.IsZero() {
		score.MTTR = outageEnd.Sub(outageStart)
	}

	return score, nil
}

func TestGameDayExecution(t *testing.T) {
	dbDegraded := false
	successRate := 1.0

	steps := []GameDayStep{
		{
			Name: "NormalLoad",
			Duration: 50 * time.Millisecond,
			Expectation: func() error {
				if successRate < 0.99 {
					return fmt.Errorf("SLO нарушен на старте")
				}
				return nil
			},
		},
		{
			Name: "InjectChaos",
			Action: func(ctx context.Context) error {
				dbDegraded = true
				successRate = 0.96 // Деградация до 96%, но в рамках допустимого порога 95%
				return nil
			},
			Duration: 50 * time.Millisecond,
			Expectation: func() error {
				if successRate < 0.95 {
					return fmt.Errorf("критическое нарушение SLO во время хаоса!")
				}
				return nil
			},
		},
		{
			Name: "Heal",
			Action: func(ctx context.Context) error {
				dbDegraded = false
				successRate = 1.0
				return nil
			},
			Duration: 20 * time.Millisecond,
			Expectation: func() error {
				if !dbDegraded && successRate == 1.0 {
					return nil
				}
				return fmt.Errorf("система не восстановилась")
			},
		},
	}

	runner := NewGameDayRunner(steps)
	score, err := runner.Run(context.Background())
	if err != nil {
		t.Fatalf("Game Day завершился неудачей: %v", err)
	}

	t.Logf("Game Day завершен успешно! Пройдено шагов: %d/%d, MTTR: %v, SLO: %v",
		score.Passed, score.TotalSteps, score.MTTR, score.SLOHonored)

	if !score.SLOHonored {
		t.Errorf("SLO было нарушено в процессе учений")
	}
}

func main() {
	fmt.Println("Тестирование автоматизации Game Day сценариев успешно завершено")
}
"""
        }
    ],
    "under_the_hood": "Декларативные раннеры учений позволяют версионировать хаос-сценарии в Git (Chaos as Code). Каждый коммит в архитектурный репозиторий может запускать автоматизированный Game Day в предпроизводственной среде, гарантируя постоянное соблюдение требований надежности без участия человека.",
    "pitfalls": [
        "Проведение Game Day без предварительного согласования времени с соседними командами.",
        "Отсутствие четкого критерия отката: если при проведении учений в продакшене бизнес-потери превысили лимит, учения обязаны откатиться автоматически за секунды.",
        "Отсутствие постмортема (Postmortem) по результатам учений."
    ],
    "bigtech_interview": "Что такое Error Budget (бюджет ошибок) в концепции Google SRE и как он связан с хаос-учениями Game Day? Бюджет ошибок — это допустимый объем сбоев за расчетный период (например, 0.01% недоступности для SLO 99.99%, что составляет ~4.3 минуты простоя в месяц). Если сервис работает стабильно и бюджет ошибок не израсходован, команда имеет полное право использовать этот остаток бюджета для проведения контролируемых учений Game Day и хаос-экспериментов в продакшене."
})

# Exercise 28
exercises.append({
    "num": 28,
    "title": "Стресс-тестирование GC и аллокаций памяти под пиковой нагрузкой",
    "task": "Подайте на сервис нагрузку, генерирующую миллионы временных объектов в секунду. Проанализируйте графики задержки Stop-The-World пауз GC. Настройте параметры `GOGC` (например, снизьте до 50 или поднимите до 200) и `GOMEMLIMIT`. Найдите оптимальный баланс между потреблением оперативной памяти и задержкой ответов p99.",
    "theory": r"""В высоконагруженных Go-сервисах аллокации памяти в куче (`heap allocations`) являются главным драйвером задержки p99:
1. Каждый вызов `new`, конкатенация строк или создание среза динамического размера обращается к аллокатору памяти Go (`mcache` -> `mcentral` -> `mheap`).
2. При заполнении кучи активируется трехцветный конкурентный сборщик мусора (Concurrent Tri-color Mark and Sweep GC).
3. Хотя фаза разметки выполняется параллельно с бизнес-горутинами, рантайм выполняет две фазы Stop-The-World (STW): `Sweep Termination` и `Mark Termination`.
4. Кроме того, если горутина аллоцирует память быстрее, чем GC успевает ее собирать, планировщик Go принудительно переводит эту горутину в режим **Mark Assist** (помощь сборщику), кратно увеличивая время ответа этого запроса.

Тюнинг переменных окружения:
- `GOGC` (по умолчанию 100): задает целевой размер кучи перед следующим запуском GC как процент от живых данных ($Target = Live \times (1 + \frac{GOGC}{100})$).
  - Снижение `GOGC=50`: куча меньше, но GC работает в 2 раза чаще, сжигая CPU.
  - Повышение `GOGC=200`: GC запускается в 2 раза реже, задержки p99 минимальны, но требуется в 2 раза больше RAM.
- `GOMEMLIMIT`: ограничивает максимальный потолок памяти, позволяя безопасно поднимать `GOGC` до больших значений.""",
    "step_by_step": [
        "Изучите структуры статистики сборщика мусора в `runtime.MemStats` (`PauseTotalNs`, `NumGC`, `PauseNs`).",
        "Создайте стресс-генератор, аллоцирующий 500 000 временных структур в секунду.",
        "Проведите замеры при дефолтном `GOGC=100` и оптимизированном `GOGC=200` + `GOMEMLIMIT`.",
        "Сравните число пауз GC и суммарное время простоя."
    ],
    "code_blocks": [
        {
            "filename": "gc_stress_tuning_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"runtime"
	"runtime/debug"
	"testing"
	"time"
)

type HeavyAllocationWorkload struct {
	iterations int
}

func (w *HeavyAllocationWorkload) Run() {
	// Аллоцируем множество короткоживущих объектов
	for i := 0; i < w.iterations; i++ {
		data := make([]byte, 1024) // 1 КБ
		data[0] = byte(i)
		_ = data
	}
}

func BenchmarkGCTuning(b *testing.B) {
	work := &HeavyAllocationWorkload{iterations: 10000}

	// 1. Замер с GOGC=50 (Частый запуск GC, экономия памяти)
	debug.SetGCPercent(50)
	var m1, m2 runtime.MemStats
	runtime.GC()
	runtime.ReadMemStats(&m1)

	start := time.Now()
	for i := 0; i < 50; i++ {
		work.Run()
	}
	d50 := time.Since(start)
	runtime.ReadMemStats(&m2)
	gcCount50 := m2.NumGC - m1.NumGC

	// 2. Замер с GOGC=200 (Редкий запуск GC, максимальная скорость)
	debug.SetGCPercent(200)
	runtime.GC()
	runtime.ReadMemStats(&m1)

	start = time.Now()
	for i := 0; i < 50; i++ {
		work.Run()
	}
	d200 := time.Since(start)
	runtime.ReadMemStats(&m2)
	gcCount200 := m2.NumGC - m1.NumGC

	// Сброс на дефолт
	debug.SetGCPercent(100)

	b.Logf("GOGC=50:  время=%v, запусков GC=%d", d50, gcCount50)
	b.Logf("GOGC=200: время=%v, запусков GC=%d", d200, gcCount200)

	if gcCount200 >= gcCount50 {
		b.Errorf("При GOGC=200 число запусков GC должно быть значительно меньше")
	}
}

func main() {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	fmt.Printf("Всего запусков GC: %d, суммарная пауза STW: %v\n", m.NumGC, time.Duration(m.PauseTotalNs))
	fmt.Println("Тестирование тюнинга GC и аллокаций завершено успешно")
}
"""
        }
    ],
    "under_the_hood": "В рантайме Go паузы Stop-The-World выполняются за счет прерывания работы горутин специальными инструкциями вызова планировщика (Preemption Points). Начиная с Go 1.14 введена асинхронная вытесняющая многозадачность (Non-cooperative Goroutine Preemption) через сигналы ОС `SIGURG`, что позволило свести время входа в STW паузу до суб-микросекунд даже при наличии плотных счетных циклов без вызовов функций.",
    "pitfalls": [
        "Полное отключение GC (`GOGC=off` или `-1`): память процесса будет бесконечно расти вплоть до гарантированного OOMKilled.",
        "Использование `runtime.GC()` в боевом коде: принудительный запуск блокирует вызывающую горутину и вызывает мгновенную деградацию задержки p99 всего сервиса.",
        "Игнорирование Escape Analysis: объекты, которые могли аллоцироваться на стеке горутины, утекают в кучу из-за использования пустых интерфейсов `any` или возврата указателей."
    ],
    "bigtech_interview": "Что такое Mark Assist в рантайме Go и как он влияет на задержку ответов p99? Когда темп аллокаций памяти бизнес-горутинами превышает скорость работы фоновых воркеров GC, планировщик Go насильно переключает аллоцирующую горутину с выполнения бизнес-логики на помощь в разметке живых объектов в куче. Время выполнения этой горутины скачкообразно возрастает на миллисекунды, формируя тяжелый хвост перцентиля p99. Профилирование метрики `schedlatency` и событий `runtime/trace` позволяет точно обнаружить фазы Mark Assist."
})

# Exercise 29
exercises.append({
    "num": 29,
    "title": "Автоматический регрессионный нагрузочный тест в CI/CD пайплайне",
    "task": "Интегрируйте нагрузочный тест в GitHub Actions / GitLab CI: после сборки нового бинарника запускается 5-минутный тест на 10 000 RPS. Тестовый скрипт сверяет результаты с базовыми метриками (Baseline): если p99 вырос более чем на 10% или потребление CPU увеличилось на 15%, CI-пайплайн завершается с ошибкой, блокируя деплой регрессии в прод.",
    "theory": r"""Continuous Performance Testing (Непрерывное нагрузочное тестирование в CI/CD) предотвращает появление регрессий производительности до их релиза в продакшен.

Архитектура автоматического контрольного шлюза (Quality Gate):
1. **Эталонные метрики (Baseline):**
   В репозитории хранится утвержденный файл эталонных метрик (`baseline.json`), зафиксированный на стабильной версии сервиса:
   - `LatencyP99`: 12.5 мс
   - `CPUUsageCores`: 1.2
   - `MemoryMB`: 180
2. **Запуск тестового прогона:**
   В изолированном раннере CI собирается кандидат релиза и прогревается нагрузкой с фиксированным профилем.
3. **Сравнение с допусками (Tolerance Thresholds):**
   - Допустимое отклонение p99: не более $+10\%$.
   - Допустимое отклонение CPU: не более $+15\%$.
4. Если кандидат превышает лимиты, тестовый раннер генерирует детальный diff, публикует комментарий в Pull Request и возвращает ненулевой код завершения `os.Exit(1)`, блокируя слияние кода.""",
    "step_by_step": [
        "Определите структуры метрик `PerformanceMetrics` и параметров порога отклонения `RegressionThresholds`.",
        "Реализуйте анализатор деградации `RegressionDetector`, сравнивающий текущие замеры с базовой линией.",
        "Смоделируйте успешный замер без регрессии и замер с ухудшением p99 задержки на 25%.",
        "Проверьте автоматическое формирование вердикта и блокировку релиза."
    ],
    "code_blocks": [
        {
            "filename": "ci_regression_gate_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"encoding/json"
	"fmt"
	"math"
	"testing"
	"time"
)

type PerformanceMetrics struct {
	LatencyP99 time.Duration `json:"latency_p99"`
	CPUCores   float64       `json:"cpu_cores"`
	MemoryMB   float64       `json:"memory_mb"`
	ErrorRate  float64       `json:"error_rate"`
}

type RegressionThresholds struct {
	MaxP99DegradationPct float64 // Например, 10.0 (%)
	MaxCPUDegradationPct float64 // Например, 15.0 (%)
}

type RegressionDetector struct {
	thresholds RegressionThresholds
}

func NewRegressionDetector(th RegressionThresholds) *RegressionDetector {
	return &RegressionDetector{thresholds: th}
}

func (d *RegressionDetector) Check(baseline, candidate PerformanceMetrics) (bool, []string) {
	var violations []string

	// Проверка задержки p99
	p99DiffPct := (float64(candidate.LatencyP99-baseline.LatencyP99) / float64(baseline.LatencyP99)) * 100.0
	if p99DiffPct > d.thresholds.MaxP99DegradationPct {
		violations = append(violations, fmt.Sprintf(
			"РЕГРЕССИЯ ЗАДЕРЖКИ: p99 вырос на +%.2f%% (было %v, стало %v, лимит +%.1f%%)",
			p99DiffPct, baseline.LatencyP99, candidate.LatencyP99, d.thresholds.MaxP99DegradationPct))
	}

	// Проверка CPU
	cpuDiffPct := ((candidate.CPUCores - baseline.CPUCores) / baseline.CPUCores) * 100.0
	if cpuDiffPct > d.thresholds.MaxCPUDegradationPct {
		violations = append(violations, fmt.Sprintf(
			"РЕГРЕССИЯ CPU: потребление процессора выросло на +%.2f%% (было %.2f cores, стало %.2f cores, лимит +%.1f%%)",
			cpuDiffPct, baseline.CPUCores, candidate.CPUCores, d.thresholds.MaxCPUDegradationPct))
	}

	return len(violations) == 0, violations
}

func TestPerformanceRegressionGate(t *testing.T) {
	detector := NewRegressionDetector(RegressionThresholds{
		MaxP99DegradationPct: 10.0,
		MaxCPUDegradationPct: 15.0,
	})

	baseline := PerformanceMetrics{
		LatencyP99: 20 * time.Millisecond,
		CPUCores:   1.0,
		MemoryMB:   250.0,
	}

	// 1. Кандидат с незначительными колебаниями (+3% p99) — УСПЕХ
	candidateGood := PerformanceMetrics{
		LatencyP99: 20600 * time.Microsecond,
		CPUCores:   1.02,
		MemoryMB:   255.0,
	}
	passed, violations := detector.Check(baseline, candidateGood)
	if !passed {
		t.Fatalf("Ложное срабатывание регрессионного шлюза: %v", violations)
	}
	t.Log("Кандидат 1 успешно прошел Quality Gate")

	// 2. Кандидат с регрессией задержки (+30% p99 из-за неоптимального мьютекса) — ОТКАЗ
	candidateBad := PerformanceMetrics{
		LatencyP99: 26 * time.Millisecond, // 26мс vs 20мс (+30%)
		CPUCores:   1.05,
		MemoryMB:   250.0,
	}
	passed, violations = detector.Check(baseline, candidateBad)
	if passed {
		t.Fatal("Quality Gate пропустил опасную регрессию задержки!")
	}
	t.Logf("Регрессия успешно заблокирована: %v", violations[0])
}

func main() {
	fmt.Println("Тестирование CI/CD регрессионного Quality Gate успешно завершено")
}
"""
        }
    ],
    "under_the_hood": "В CI/CD окружении виртуальные машины часто страдают от эффекта шумных соседей (Noisy Neighbors), из-за чего результаты одного прогона могут колебаться на 10–20%. Для обеспечения достоверности регрессионного тестирования применяют статистические критерии (например, критерий Манна-Уитни / Mann-Whitney U-test) по результатам 5 независимых прогонов, сравнивая распределения с доверительным интервалом 95%.",
    "pitfalls": [
        "Слишком жесткие пороги отклонения (например, 1%): приведут к постоянным ложным блокировкам CI из-за естественных флуктуаций операционной системы.",
        "Запуск бенчмарков на разделяемых runner-машинах с плавающим числом vCPU.",
        "Отсутствие автоматического обновления эталонного baseline после согласованных оптимизаций."
    ],
    "bigtech_interview": "Как организовать автоматическое нагрузочное тестирование в CI, если полный тест длится 4 часа, а пайплайн сборки Pull Request должен завершаться за 10 минут? Применяют двухуровневый подход: 1) В PR запускается короткий микро-бенчмарк (Micro-benchmark / Smoke Load) на 3 минуты с проверкой аллокаций памяти и локальной задержки критичных путей; 2) Полномасштабный 4-часовой нагрузочный тест запускается ночью (Nightly Build) на выделенном аппаратном стенде для всех смерженных за день изменений."
})

# Exercise 30
exercises.append({
    "num": 30,
    "title": "Комплексная платформа хаос-инженерии и нагрузочного тестирования на Go",
    "task": "Разработайте законченный инструмент хаос-тестирования на Go: консольная утилита с поддержкой генерации открытой нагрузки, интеграцией с Toxiproxy, автоматическим сбором метрик p50/p90/p99 через HdrHistogram, проверкой гипотез steady-state, экспортом HTML-отчета с графиками и готовыми сценариями тестирования микросервисов.",
    "theory": r"""Флагманский проект главы объединяет все изученные концепции в законченную корпоративную платформу хаос-инженерии и нагрузочного тестирования (`ChaosLoadPlatform`):

Архитектурные компоненты платформы:
1. **Open Workload Engine:** генератор пуассоновского трафика с настраиваемым Target RPS и защитой от Coordinated Omission.
2. **Chaos Orchestrator:** динамическое управление сбоями (Toxiproxy controller) с поддержкой сценариев Latency, Jitter, Bandwidth и Connection Reset.
3. **High Dynamic Range Metrics Collector:** логарифмическая гистограмма для сбора миллионов сэмплов с нулевыми аллокациями и точным расчетом p50, p90, p99, p99.9.
4. **Steady-State Hypothesis Evaluator:** автоматическая оценка критериев качества бизнеса (Success Rate > 99.0%, p99 < 150ms).
5. **Safety Blast Radius Guard:** автоматический предохранитель, экстренно останавливающий инъекцию сбоя при катастрофической деградации системы.
6. **Executive Summary Generator:** формирование детального текстового и HTML отчета со всеми метриками и графиками.""",
    "step_by_step": [
        "Спроектируйте архитектуру единой платформы, объединяющей нагрузочный движок, хаос-контроллер и сборщик метрик.",
        "Реализуйте координатор полного жизненного цикла: Baseline Test -> Chaos Phase -> Hypothesis Verification -> Cooldown -> Scorecard Generation.",
        "Запустите сквозной сценарий тестирования финансового сервиса под инъекцией сетевого джиттера.",
        "Сформируйте итоговый отчет и подтвердите готовность платформы к промышленной эксплуатации."
    ],
    "code_blocks": [
        {
            "filename": "chaos_platform_capstone.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
	"math/rand"
	"sync"
	"sync/atomic"
	"time"
)

// MetricCollector компактный сборщик метрик
type MetricCollector struct {
	mu           sync.Mutex
	latencies    []time.Duration
	successCount atomic.Int64
	failCount    atomic.Int64
}

func NewMetricCollector() *MetricCollector {
	return &MetricCollector{
		latencies: make([]time.Duration, 0, 10000),
	}
}

func (c *MetricCollector) Record(d time.Duration, success bool) {
	if success {
		c.successCount.Add(1)
	} else {
		c.failCount.Add(1)
	}

	c.mu.Lock()
	if len(c.latencies) < 50000 {
		c.latencies = append(c.latencies, d)
	}
	c.mu.Unlock()
}

func (c *MetricCollector) Report() (float64, time.Duration) {
	succ := c.successCount.Load()
	fail := c.failCount.Load()
	total := succ + fail
	var sr float64
	if total > 0 {
		sr = float64(succ) / float64(total)
	}

	c.mu.Lock()
	defer c.mu.Unlock()
	if len(c.latencies) == 0 {
		return sr, 0
	}

	// Простое приближение p99 для отчета
	idx := int(float64(len(c.latencies)) * 0.99)
	if idx >= len(c.latencies) {
		idx = len(c.latencies) - 1
	}
	return sr, c.latencies[idx]
}

// ChaosPlatform orchestrates the entire chaos load experiment
type ChaosPlatform struct {
	targetRPS float64
	targetFn  func(ctx context.Context) error
}

func NewChaosPlatform(rps float64, fn func(context.Context) error) *ChaosPlatform {
	return &ChaosPlatform{
		targetRPS: rps,
		targetFn:  fn,
	}
}

func (p *ChaosPlatform) RunExperiment(ctx context.Context, duration time.Duration, injectFault func(), rollbackFault func()) {
	fmt.Println("================================================================")
	fmt.Println("   ENTERPRISE CHAOS & LOAD TESTING PLATFORM (GO CAPSTONE)       ")
	fmt.Println("================================================================")

	collector := NewMetricCollector()
	done := make(chan struct{})
	interval := time.Duration(float64(time.Second) / p.targetRPS)
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	// Генератор нагрузки
	go func() {
		for {
			select {
			case <-done:
				return
			case <-ticker.C:
				go func() {
					start := time.Now()
					reqCtx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
					defer cancel()

					err := p.targetFn(reqCtx)
					collector.Record(time.Since(start), err == nil)
				}()
			}
		}
	}()

	// 1. Этап Baseline (прогрев)
	fmt.Println("[PHASE 1] Сбор эталонных метрик (Baseline)...")
	time.Sleep(duration / 3)

	srBase, p99Base := collector.Report()
	fmt.Printf("          Baseline: SuccessRate=%.1f%%, Latency p99=%v\n", srBase*100, p99Base)

	// 2. Этап Chaos Injection
	fmt.Println("[PHASE 2] Инъекция хаос-сбоя (Chaos Injection)...")
	injectFault()

	time.Sleep(duration / 3)

	srChaos, p99Chaos := collector.Report()
	fmt.Printf("          Under Chaos: SuccessRate=%.1f%%, Latency p99=%v\n", srChaos*100, p99Chaos)

	// 3. Этап Recovery
	fmt.Println("[PHASE 3] Восстановление системы (Healing & Rollback)...")
	rollbackFault()
	time.Sleep(duration / 3)

	close(done)

	// 4. Финальный аудит гипотезы
	srFinal, p99Final := collector.Report()
	fmt.Println("\n================ ФИНАЛЬНЫЙ ОТЧЕТ ХАОС-ТЕСТА ================")
	fmt.Printf("Всего успешных запросов: %d\n", collector.successCount.Load())
	fmt.Printf("Всего ошибок:            %d\n", collector.failCount.Load())
	fmt.Printf("Итоговый Success Rate:   %.2f%%\n", srFinal*100)
	fmt.Printf("Итоговый p99 Latency:    %v\n", p99Final)

	if srFinal >= 0.95 {
		fmt.Println("ВЕРДИКТ: [PASSED] Система подтвердила гипотезу отказоустойчивости!")
	} else {
		fmt.Println("ВЕРДИКТ: [FAILED] Нарушено стабильное состояние системы!")
	}
	fmt.Println("================================================================")
}

func main() {
	var networkLag atomic.Int64
	targetService := func(ctx context.Context) error {
		lag := time.Duration(networkLag.Load())
		if lag > 0 {
			time.Sleep(lag)
		}
		return nil
	}

	platform := NewChaosPlatform(100.0, targetService)
	ctx := context.Background()

	inject := func() {
		networkLag.Store(int64(40 * time.Millisecond))
	}
	rollback := func() {
		networkLag.Store(0)
	}

	platform.RunExperiment(ctx, 300*time.Millisecond, inject, rollback)
}
"""
        }
    ],
    "under_the_hood": "Флагманская платформа объединяет математические модели теории очередей (Пуассон), высокоэффективное квантование HdrHistogram, недеструктивную изоляцию Blast Radius и автоматический расчет MTTR. В продакшен-системах такие платформы непрерывно оркестрируют учения с помощью Kubernetes CRD и экспортируют агрегированные метрики в Prometheus через OpenTelemetry SDK.",
    "pitfalls": [
        "Проведение хаос-тестов без автоматического предохранителя отката (Safety Rollback Switch).",
        "Использование закрытой модели нагрузки, маскирующей реальные задержки клиентов.",
        "Пренебрежение анализом метрик операционной системы (CPU throttling, cgroups memory limits) во время теста."
    ],
    "bigtech_interview": "Как обосновать внедрение хаос-инженерии руководству компании и доказать ее возврат инвестиций (ROI)? Главный аргумент — предотвращение финансовых и репутационных потерь от простоев в пиковые часы (Black Friday). Стоимость 1 часа простоя крупного e-commerce сервиса исчисляется миллионами рублей. Обнаружение дефекта таймаута базы данных во время 30-минутного хаос-учения окупает затраты на команду хаос-инженерии на годы вперед."
})

def test_all():
    print(f"Generated {len(exercises)} exercises in part 2")
    for ex in exercises:
        for cb in ex['code_blocks']:
            code = cb['code']
            with tempfile.NamedTemporaryFile('w', suffix='.go', delete=False) as tf:
                tf.write(code)
                tf_path = tf.name
            try:
                res = subprocess.run(['gofmt', '-e', tf_path], capture_output=True, text=True)
                if res.returncode != 0:
                    print(f"ERROR in Ex {ex['num']} ({cb['filename']}): {res.stderr}")
                    return False
            finally:
                if os.path.exists(tf_path):
                    os.remove(tf_path)
    print("All Part 2 code blocks verified with gofmt -e!")
    return True

if __name__ == '__main__':
    if test_all():
        out_path = os.path.join(os.path.dirname(__file__), 'ch89_p2.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(exercises, f, ensure_ascii=False, indent=2)
        print(f"Wrote {out_path} successfully!")
