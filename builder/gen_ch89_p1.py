# -*- coding: utf-8 -*-
import json
import subprocess
import tempfile
import os

exercises = []

# Exercise 1
exercises.append({
    "num": 1,
    "title": "Принципы хаос-инженерии (Principles of Chaos Engineering)",
    "task": "Изучите принципы хаос-инженерии: формулирование гипотезы о стабильном состоянии (Steady State), определение радиуса поражения (Blast Radius), симуляция реальных аварий в тестовой и производственной среде. Объясните, почему пассивного мониторинга недостаточно для проверки отказоустойчивости распределенных систем.",
    "theory": r"""Хаос-инженерия (Chaos Engineering) — это дисциплина экспериментирования над распределенными системами для формирования уверенности в их способности выдерживать непредвиденные турбулентные условия в рабочей среде (производстве). Впервые концепция была формализована компанией Netflix (Chaos Monkey, Simian Army) в связи с миграцией в публичное облако AWS, где физические серверы и виртуальные машины могут деградировать и отключаться без предупреждения.

Фундаментальные принципы хаос-инженерии:
1. **Определение «Стабильного состояния» (Steady State):**
   Система должна характеризоваться измеримым поведением, отражающим нормальное функционирование бизнеса (бизнес-метрики: количество успешных заказов в минуту, задержка ответа p99, частота ошибок HTTP 5xx < 0.05%).
2. **Формулирование гипотезы:**
   Эксперимент строится вокруг гипотезы: «*Даже если зависимость X откажет или её задержка возрастет на 2000 мс, стабильное состояние системы сохранится (заказы будут приниматься через фоновый буфер, а SLO p99 не упадет ниже 99.9%)*».
3. **Варьирование реальных событий (Real-world Events):**
   Сбои должны имитировать настоящие инциденты: аварийное падение узлов СУБД, исчерпание памяти (OOM), фрагментация пакетов, отказ DNS-резолверов, каскадные сбои очередей сообщений.
4. **Минимизация радиуса поражения (Blast Radius):**
   Эксперименты начинаются с изолированных канареечных (Canary) инстансов или синтетического трафика тестовых аккаунтов (`X-Chaos-Test: true`), постепенно расширяясь до полномасштабных проверок в продакшене.
5. **Автоматизация и непрерывность:**
   Хаос-тестирование должно быть автоматизировано в CI/CD пайплайнах и непрерывно запускаться в продакшене для обнаружения скрытых регрессий надежности до того, как они приведут к ночным авариям.""",
    "step_by_step": [
        "Определите метрики Steady State (SLO успешности и SLA по задержке) с помощью структуры интерфейса проверки метрик.",
        "Реализуйте движок оркестрации хаос-экспериментов `ExperimentRunner`, управляющий жизненным циклом: валидация Steady State -> инъекция сбоя -> мониторинг радиуса поражения -> откат (Rollback) -> финальная оценка гипотезы.",
        "Реализуйте защитный предохранитель (Safety Switch / Circuit Breaker эксперимента), который экстренно прекращает сбой, если метрики падают ниже критического порога Blast Radius.",
        "Протестируйте выполнение эксперимента с симуляцией сбоя внешнего API и проверьте сохранение Steady State за счет локального кэша."
    ],
    "code_blocks": [
        {
            "filename": "chaos_framework.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// MetricSnapshot отражает текущие бизнес-показатели системы
type MetricSnapshot struct {
	SuccessRate float64       // Доля успешных запросов (0.0 - 1.0)
	LatencyP99  time.Duration // Перцентиль p99
	ActiveNodes int           // Количество живых реплик
}

// SteadyStateHypothesis задает критерии стабильного состояния
type SteadyStateHypothesis struct {
	MinSuccessRate float64
	MaxLatencyP99  time.Duration
}

func (h SteadyStateHypothesis) Validate(m MetricSnapshot) error {
	if m.SuccessRate < h.MinSuccessRate {
		return fmt.Errorf("нарушен порог успешности: %.2f%% < %.2f%%", m.SuccessRate*100, h.MinSuccessRate*100)
	}
	if m.LatencyP99 > h.MaxLatencyP99 {
		return fmt.Errorf("превышен порог p99: %v > %v", m.LatencyP99, h.MaxLatencyP99)
	}
	return nil
}

// FaultInjector интерфейс инъекции и отката хаос-сбоя
type FaultInjector interface {
	Name() string
	Inject(ctx context.Context) error
	Rollback(ctx context.Context) error
}

// ExperimentRunner выполняет хаос-эксперимент с контролем Blast Radius
type ExperimentRunner struct {
	hypothesis SteadyStateHypothesis
	getMetrics func(ctx context.Context) MetricSnapshot
	stopLimit  float64 // Критический порог отката (Safety Switch)
}

func NewExperimentRunner(h SteadyStateHypothesis, metricsFn func(context.Context) MetricSnapshot, safetyFloor float64) *ExperimentRunner {
	return &ExperimentRunner{
		hypothesis: h,
		getMetrics: metricsFn,
		stopLimit:  safetyFloor,
	}
}

func (r *ExperimentRunner) Run(ctx context.Context, fault FaultInjector, duration time.Duration) error {
	fmt.Printf("[CHAOS] Запуск эксперимента: '%s'\n", fault.Name())

	initial := r.getMetrics(ctx)
	if err := r.hypothesis.Validate(initial); err != nil {
		return fmt.Errorf("система не в стабильном состоянии перед экспериментом: %w", err)
	}
	fmt.Printf("[CHAOS] Начальный Steady State подтвержден: SR=%.1f%%, p99=%v\n", initial.SuccessRate*100, initial.LatencyP99)

	if err := fault.Inject(ctx); err != nil {
		return fmt.Errorf("ошибка инъекции сбоя: %w", err)
	}
	defer func() {
		fmt.Printf("[CHAOS] Откат сбоя '%s'...\n", fault.Name())
		_ = fault.Rollback(context.Background())
	}()

	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()
	timeout := time.After(duration)

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-timeout:
			fmt.Println("[CHAOS] Время действия сбоя истекло успешно")
			final := r.getMetrics(ctx)
			if err := r.hypothesis.Validate(final); err != nil {
				return fmt.Errorf("гипотеза опровергнута: %w", err)
			}
			fmt.Println("[CHAOS] Гипотеза подтверждена! Система отказоустойчива.")
			return nil
		case <-ticker.C:
			current := r.getMetrics(ctx)
			if current.SuccessRate < r.stopLimit {
				return fmt.Errorf("АВАРИЙНАЯ ОСТАНОВКА: превышен Blast Radius (SR=%.2f%%)", current.SuccessRate*100)
			}
		}
	}
}

type LatencyFault struct {
	name string
}

func (f *LatencyFault) Name() string { return f.name }
func (f *LatencyFault) Inject(ctx context.Context) error {
	fmt.Println("[FAULT] Инжектирована задержка 1500мс на исходящие HTTP-запросы")
	return nil
}
func (f *LatencyFault) Rollback(ctx context.Context) error {
	fmt.Println("[FAULT] Сетевая задержка сброшена в 0")
	return nil
}

func main() {
	var mu sync.Mutex
	currentMetrics := MetricSnapshot{
		SuccessRate: 0.999,
		LatencyP99:  15 * time.Millisecond,
		ActiveNodes: 3,
	}

	hypothesis := SteadyStateHypothesis{
		MinSuccessRate: 0.95,
		MaxLatencyP99:  200 * time.Millisecond,
	}

	runner := NewExperimentRunner(hypothesis, func(ctx context.Context) MetricSnapshot {
		mu.Lock()
		defer mu.Unlock()
		return currentMetrics
	}, 0.80)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	fault := &LatencyFault{name: "Degraded_Payment_Gateway"}
	if err := runner.Run(ctx, fault, 500*time.Millisecond); err != nil {
		fmt.Printf("Результат: %v\n", err)
	}
}
"""
        }
    ],
    "under_the_hood": "Пассивный мониторинг регистрирует сбои только post-factum, когда реальные пользователи уже столкнулись с ошибками. Хаос-инженерия действует проактивно: она создает контролируемые возмущения в непиковые часы или на канареечных хостах, выявляя скрытые дефекты конфигурации (слишком короткие или длинные таймауты, отсутствие Circuit Breaker, перегрузка пулов соединений) до того, как они вызовут каскадную аварию всего датацентра.",
    "pitfalls": [
        "Запуск хаос-тестов без автоматического предохранителя (Safety Switch): сбой может уйти в бесконечный цикл и парализовать работу продакшена.",
        "Фокусировка исключительно на инфраструктурных сбоях (kill pod): логические сбои (медленные ответы 200 OK, деградировавший DNS, поврежденные тела JSON) вызывают куда более разрушительные каскадные аварии.",
        "Игнорирование Steady State: тестирование ради тестирования без четкой математической гипотезы не дает объективного ответа о надежности архитектуры."
    ],
    "bigtech_interview": "В чем разница между классическим нагрузочным тестированием и хаос-инженерией? Нагрузочное тестирование проверяет поведение системы в условиях количественного роста штатного трафика (Capacity Planning), а хаос-инженерия проверяет устойчивость системы к качественным аномалиям (отказ оборудования, разрыв сети, непредсказуемая деградация зависимостей) при любом уровне нагрузки."
})

# Exercise 2
exercises.append({
    "num": 2,
    "title": "Введение в Toxiproxy: архитектура и сценарии сбоев",
    "task": "Изучите архитектуру `Shopify/toxiproxy`: TCP-прокси, перехватывающий сетевой трафик между тестируемым приложением и его зависимостями (PostgreSQL, Redis, Kafka, внешние HTTP-сервисы), и инжектирующий сетевые сбои («токсики»). Разверните контейнер Toxiproxy в Docker.",
    "theory": r"""Toxiproxy — это инструмент хаос-тестирования TCP-соединений, разработанный компанией Shopify для эмуляции нестабильных сетевых условий. В отличие от утилит вроде `iptables` или `tc` (Linux Traffic Control), требующих привилегий `root` (CAP_NET_ADMIN) и воздействующих на весь сетевой интерфейс хоста, Toxiproxy работает в пространстве пользователя (User Space) на уровне прикладных TCP-сокетов.

Архитектура Toxiproxy:
1. **Control API (порт 8474):** REST HTTP API для динамического создания прокси, включения/выключения соединений и манипуляции токсиками в рантайме.
2. **Прокси (Proxy Listeners):** Экземпляр прокси слушает локальный TCP-порт (например, `:54320`) и пересылает входящие байты на целевой сервис (upstream, например `postgres:5432`).
3. **Цепочка токсиков (Toxic Chain):** Трафик проходит через стек токсиков в двух направлениях:
   - `upstream`: от клиента к серверу (например, медленная загрузка запроса).
   - `downstream`: от сервера к клиенту (например, медленный ответ, разрыв связи).
4. **Типы токсиков (Toxics):**
   - `latency`: добавление задержки с возможностью джиттера.
   - `bandwidth`: ограничение скорости передачи (КБ/с).
   - `slow_close`: задержка отправки TCP FIN пакета.
   - `timeout`: полное прекращение передачи данных (эмуляция blackhole).
   - `reset_peer`: немедленная отправка TCP RST пакета.
   - `slicer`: фрагментация пакетов на мелкие куски со случайной задержкой.
   - `limit_data`: закрытие соединения после передачи заданного количества байт.""",
    "step_by_step": [
        "Изучите принципы проксирования TCP-трафика в User Space.",
        "Реализуйте собственный минималистичный симулятор TCP-прокси на чистом Go, демонстрирующий концепцию перехвата трафика и внедрения задержки (`LatencyToxic`) в дуплексный поток `net.Conn`.",
        "Реализуйте структуру `ProxyPair`, связывающую входящее соединение клиента и исходящее соединение с upstream-сервером через регулируемый пайплайн с задержкой.",
        "Продемонстрируйте передачу данных между клиентом и эхо-сервером через прокси."
    ],
    "code_blocks": [
        {
            "filename": "mini_toxiproxy.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
	"io"
	"net"
	"sync"
	"sync/atomic"
	"time"
)

type MiniToxic struct {
	Latency time.Duration
}

type MiniProxy struct {
	listenAddr string
	targetAddr string
	toxic      atomic.Pointer[MiniToxic]
	listener   net.Listener
	wg         sync.WaitGroup
	ctx        context.Context
	cancel     context.CancelFunc
}

func NewMiniProxy(listenAddr, targetAddr string) *MiniProxy {
	ctx, cancel := context.WithCancel(context.Background())
	p := &MiniProxy{
		listenAddr: listenAddr,
		targetAddr: targetAddr,
		ctx:        ctx,
		cancel:     cancel,
	}
	p.toxic.Store(&MiniToxic{Latency: 0})
	return p
}

func (p *MiniProxy) SetLatency(d time.Duration) {
	p.toxic.Store(&MiniToxic{Latency: d})
}

func (p *MiniProxy) Start() error {
	l, err := net.Listen("tcp", p.listenAddr)
	if err != nil {
		return err
	}
	p.listener = l

	p.wg.Add(1)
	go func() {
		defer p.wg.Done()
		for {
			clientConn, err := p.listener.Accept()
			if err != nil {
				select {
				case <-p.ctx.Done():
					return
				default:
					continue
				}
			}
			p.wg.Add(1)
			go func(c net.Conn) {
				defer p.wg.Done()
				p.handleConnection(c)
			}(clientConn)
		}
	}()
	return nil
}

func (p *MiniProxy) handleConnection(clientConn net.Conn) {
	defer clientConn.Close()

	serverConn, err := net.Dial("tcp", p.targetAddr)
	if err != nil {
		return
	}
	defer serverConn.Close()

	var copyWg sync.WaitGroup
	copyWg.Add(2)

	go func() {
		defer copyWg.Done()
		_, _ = io.Copy(serverConn, clientConn)
	}()

	go func() {
		defer copyWg.Done()
		buf := make([]byte, 4096)
		for {
			n, err := serverConn.Read(buf)
			if n > 0 {
				toxic := p.toxic.Load()
				if toxic != nil && toxic.Latency > 0 {
					time.Sleep(toxic.Latency)
				}
				if _, writeErr := clientConn.Write(buf[:n]); writeErr != nil {
					return
				}
			}
			if err != nil {
				return
			}
		}
	}()

	copyWg.Wait()
}

func (p *MiniProxy) Close() error {
	p.cancel()
	if p.listener != nil {
		_ = p.listener.Close()
	}
	p.wg.Wait()
	return nil
}

func main() {
	echoListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		panic(err)
	}
	defer echoListener.Close()
	echoAddr := echoListener.Addr().String()

	go func() {
		for {
			conn, err := echoListener.Accept()
			if err != nil {
				return
			}
			go func(c net.Conn) {
				defer c.Close()
				_, _ = io.Copy(c, c)
			}(conn)
		}
	}()

	proxy := NewMiniProxy("127.0.0.1:0", echoAddr)
	if err := proxy.Start(); err != nil {
		panic(err)
	}
	defer proxy.Close()
	proxyAddr := proxy.listener.Addr().String()

	start := time.Now()
	conn, err := net.Dial("tcp", proxyAddr)
	if err != nil {
		panic(err)
	}
	_, _ = conn.Write([]byte("PING"))
	reply := make([]byte, 4)
	_, _ = conn.Read(reply)
	conn.Close()
	fmt.Printf("Без сбоев: ответ '%s' за %v\n", string(reply), time.Since(start))

	proxy.SetLatency(200 * time.Millisecond)
	start = time.Now()
	conn, err = net.Dial("tcp", proxyAddr)
	if err != nil {
		panic(err)
	}
	_, _ = conn.Write([]byte("PING"))
	_, _ = conn.Read(reply)
	conn.Close()
	fmt.Printf("С токсиком задержки: ответ '%s' за %v\n", string(reply), time.Since(start))
}
"""
        }
    ],
    "under_the_hood": "Toxiproxy внутри оперирует буферизованными каналами и горутинами, транслирующими байты между клиентским и серверным сокетами. Когда активируется токсик (например, latency), горутина downstream приостанавливает вызов `conn.Write()` с помощью таймера рантайма (`time.After` / `time.Sleep`). При токсике `reset_peer` прокси устанавливает для сокета опцию `SO_LINGER` со значением тайм-аута 0 и вызывает `Close()`, что заставляет сетевой стек ядра Linux немедленно послать TCP флаг RST вместо стандартной 4-этапной процедуры закрытия FIN-ACK.",
    "pitfalls": [
        "Размещение Toxiproxy в продакшене: Toxiproxy предназначен исключительно для тестовых окружений и стейджинга, так как накладные расходы проксирования в User Space снижают максимальный сетевой throughput.",
        "Утечка горутин при обрыве полудуплексных соединений: если закрыта только одна сторона TCP-сессии (FIN), вторая горутина может остаться навсегда заблокированной в вызове `Read()`, если не настроены сокетные дедлайны (`SetReadDeadline`).",
        "Жесткая привязка к IP-адресам контейнеров вместо DNS-имен в динамических сетях Docker."
    ],
    "bigtech_interview": "Почему для хаос-тестирования сетевого стека часто выбирают Toxiproxy вместо Linux netem/tc? `tc` (Traffic Control) работает на уровне сетевого интерфейса ядра Linux и искажает трафик глобально для всего хоста или сетевого пространства имен (network namespace). Toxiproxy работает на уровне конкретных TCP портов, позволяет инжектировать сбои точечно в определенные сервисы (например, только к мастеру PostgreSQL, не трогая реплики и Redis) и управляется программно через простой REST API прямо из кода тестов."
})

# Exercise 3
exercises.append({
    "num": 3,
    "title": "Программное управление Toxiproxy из Go-тестов",
    "task": "Подключите официальный Go-клиент `github.com/Shopify/toxiproxy/v2/client`. Напишите вспомогательную функцию для Go-тестов, которая создает прокси перед тестовой базой данных PostgreSQL: `client.CreateProxy(\"postgres\", \"localhost:54320\", \"postgres:5432\")`. Проверьте успешное проксирование трафика.",
    "theory": r"""Использование официального Go-клиента Toxiproxy (`github.com/Shopify/toxiproxy/v2/client`) позволяет организовывать детерминированные хаос-тесты прямо внутри стандартных тестов `go test`.

Ключевые сущности клиента:
1. `client.NewClient(apiAddr)`: инициализирует HTTP-клиент для связи с демоном Toxiproxy.
2. `client.CreateProxy(name, listenAddr, upstreamAddr)`: регистрирует новый виртуальный прокси. Если прокси с таким именем уже существовал, клиент возвращает ошибку или позволяет получить существующий (`client.Proxy(name)`).
3. `proxy.AddToxic(name, type, stream, toxicity, attributes)`: добавляет токсик в цепочку. `toxicity` задает вероятность применения от 0.0 до 1.0.
4. `proxy.RemoveToxic(name)`: мгновенно удаляет токсик и восстанавливает штатный режим.
5. `proxy.Disable()` / `proxy.Enable()`: полное отключение прокси (симуляция полного падения сервера / сетевого блэкаута).

Идиоматичный паттерн в тестах Go:
Использование `t.Cleanup(func() { ... })` для сброса токсиков и закрытия прокси гарантирует, что даже в случае аварийного завершения теста (`t.FailNow()`) окружение вернется в исходное состояние, и следующие тесты не будут затронуты остаточными сбоями.""",
    "step_by_step": [
        "Определите структуры конфигурации хаос-клиента и тестового прокси-контроллера.",
        "Реализуйте обертку `ChaosManager`, эмулирующую протокол управления Toxiproxy: регистрация прокси, инъекция токсика, удаление токсика и сброс состояния.",
        "Реализуйте функцию хелпера `SetupPostgresProxy(t *testing.T)`, автоматически регистрирующую очистку через `t.Cleanup`.",
        "Напишите тест, проверяющий добавление и последующее удаление токсика задержки с замером Round-Trip Time (RTT)."
    ],
    "code_blocks": [
        {
            "filename": "toxiproxy_manager_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"io"
	"net"
	"sync"
	"testing"
	"time"
)

type ToxicDescriptor struct {
	Name       string
	Type       string
	Stream     string
	Toxicity   float64
	Attributes map[string]any
}

type MockToxiproxyClient struct {
	mu      sync.Mutex
	proxies map[string]*SimulatedProxy
}

type SimulatedProxy struct {
	Name     string
	Listen   string
	Upstream string
	Toxics   map[string]ToxicDescriptor
	Enabled  bool
	listener net.Listener
}

func NewMockToxiproxyClient() *MockToxiproxyClient {
	return &MockToxiproxyClient{
		proxies: make(map[string]*SimulatedProxy),
	}
}

func (c *MockToxiproxyClient) CreateProxy(name, listen, upstream string) (*SimulatedProxy, error) {
	c.mu.Lock()
	defer c.mu.Unlock()

	l, err := net.Listen("tcp", listen)
	if err != nil {
		return nil, err
	}

	p := &SimulatedProxy{
		Name:     name,
		Listen:   l.Addr().String(),
		Upstream: upstream,
		Toxics:   make(map[string]ToxicDescriptor),
		Enabled:  true,
		listener: l,
	}
	c.proxies[name] = p

	go func() {
		for {
			clientConn, err := l.Accept()
			if err != nil {
				return
			}
			go p.pipe(clientConn)
		}
	}()

	return p, nil
}

func (p *SimulatedProxy) pipe(clientConn net.Conn) {
	defer clientConn.Close()
	if !p.Enabled {
		return
	}

	serverConn, err := net.Dial("tcp", p.Upstream)
	if err != nil {
		return
	}
	defer serverConn.Close()

	var latency time.Duration
	if tox, ok := p.Toxics["latency"]; ok {
		if ms, valid := tox.Attributes["latency"].(int); valid {
			latency = time.Duration(ms) * time.Millisecond
		}
	}

	var wg sync.WaitGroup
	wg.Add(2)

	go func() {
		defer wg.Done()
		_, _ = io.Copy(serverConn, clientConn)
	}()

	go func() {
		defer wg.Done()
		if latency > 0 {
			time.Sleep(latency)
		}
		_, _ = io.Copy(clientConn, serverConn)
	}()

	wg.Wait()
}

func (p *SimulatedProxy) AddToxic(name, toxType, stream string, toxicity float64, attrs map[string]any) {
	p.Toxics[name] = ToxicDescriptor{
		Name:       name,
		Type:       toxType,
		Stream:     stream,
		Toxicity:   toxicity,
		Attributes: attrs,
	}
}

func (p *SimulatedProxy) RemoveToxic(name string) {
	delete(p.Toxics, name)
}

func (p *SimulatedProxy) Close() {
	p.Enabled = false
	if p.listener != nil {
		_ = p.listener.Close()
	}
}

func TestPostgresProxyLatency(t *testing.T) {
	dbListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("не удалось запустить мок БД: %v", err)
	}
	defer dbListener.Close()

	go func() {
		for {
			conn, err := dbListener.Accept()
			if err != nil {
				return
			}
			go func(c net.Conn) {
				defer c.Close()
				buf := make([]byte, 1024)
				n, _ := c.Read(buf)
				_, _ = c.Write(buf[:n])
			}(conn)
		}
	}()

	toxiClient := NewMockToxiproxyClient()
	proxy, err := toxiClient.CreateProxy("postgres_test", "127.0.0.1:0", dbListener.Addr().String())
	if err != nil {
		t.Fatalf("ошибка создания прокси: %v", err)
	}
	t.Cleanup(func() {
		proxy.Close()
	})

	start := time.Now()
	conn, err := net.Dial("tcp", proxy.Listen)
	if err != nil {
		t.Fatalf("ошибка подключения: %v", err)
	}
	_, _ = conn.Write([]byte("SELECT 1;"))
	res := make([]byte, 9)
	_, _ = conn.Read(res)
	conn.Close()
	normalDuration := time.Since(start)

	if normalDuration > 50*time.Millisecond {
		t.Errorf("Слишком долгий ответ без сбоев: %v", normalDuration)
	}

	proxy.AddToxic("db_latency", "latency", "downstream", 1.0, map[string]any{"latency": 150})

	start = time.Now()
	conn, err = net.Dial("tcp", proxy.Listen)
	if err != nil {
		t.Fatalf("ошибка подключения к прокси: %v", err)
	}
	_, _ = conn.Write([]byte("SELECT 1;"))
	_, _ = conn.Read(res)
	conn.Close()
	toxicDuration := time.Since(start)

	if toxicDuration < 140*time.Millisecond {
		t.Errorf("Токсик не применился: задержка %v < 150ms", toxicDuration)
	}

	proxy.RemoveToxic("db_latency")
}

func main() {
	fmt.Println("Программное управление Toxiproxy проверено успешно")
}
"""
        }
    ],
    "under_the_hood": "Go-клиент `toxiproxy/v2/client` общается с Toxiproxy Server по протоколу HTTP/1.1 REST JSON. Метод `AddToxic` отправляет POST запрос на `/proxies/{proxy}/toxics` с телом конфигурации. Сервер Toxiproxy в ответ находит соответствующий экземпляр соединения в своей таблице, оборачивает низкоуровневый `net.Conn` в цепочку декораторов интерфейса `io.ReadWriter` и применяет изменения на лету, не сбрасывая уже открытые TCP-сокеты.",
    "pitfalls": [
        "Забытый сброс токсиков между тестами: если один тест завершился паникой или ошибкой и не вызвал `RemoveToxic`, все последующие тесты в тестовом пакете начнут падать по таймауту.",
        "Конкурентное изменение токсиков одного прокси в параллельных тестах (`t.Parallel()`): тесты влияют друг на друга, порождая плавающие ошибки (flaky tests). Прокси должны быть изолированы для каждого теста.",
        "Использование стандартных портов (5432) вместо динамически выделяемых (порт 0): риск конфликтов с локальными сервисами разработчика."
    ],
    "bigtech_interview": "Как организовать параллельное тестирование множества интеграционных тестов с использованием Toxiproxy без взаимного влияния? Каждому изолированному тесту необходимо программно создавать свой уникальный экземпляр прокси со случайным свободным портом (bind к `:0`) и уникальным именем (`uuid.New()`), направляя трафик тестируемого клиента именно на этот адрес, а по завершении теста удалять прокси в блоке `t.Cleanup()`."
})

# Exercise 4
exercises.append({
    "num": 4,
    "title": "Инъекция сетевой задержки (Latency Toxic)",
    "task": "Добавьте в прокси токсик сетевой задержки: `proxy.AddToxic(\"latency\", \"latency\", \"downstream\", 1.0, client.Attributes{\"latency\": 1000})` (задержка 1000 мс). Проверьте поведение HTTP-сервера: срабатывают ли таймауты контекста базы данных (`context.WithTimeout`), возвращается ли ошибка `504 Gateway Timeout` клиенту.",
    "theory": r"""Сетевая задержка (Latency) — самый распространенный и коварный вид сбоев в микросервисной архитектуре. В отличие от полного отказа сервиса (когда TCP сокет моментально закрывается с ошибкой `Connection refused`), задержка держит соединение открытым, заставляя клиентские горутины бесконечно ждать ответа.

Если в приложении не настроены таймауты:
1. Каждое входящее HTTP-соединение порождает горутину обработчика.
2. Обработчик отправляет запрос в БД или внешний API и блокируется в синхронном чтении сокета.
3. Новые запросы продолжают поступать, создавая новые горутины.
4. Исчерпывается пул соединений к базе данных, затем заканчивается оперативная память (OOM), и сервис падает целиком (каскадный сбой).

Корректная обработка сетевой задержки требует иерархических контекстов с дедлайнами:
- `context.WithTimeout(r.Context(), 250*time.Millisecond)` для запросов к БД.
- Если БД не отвечает вовремя, драйвер отменяет запрос (`context.DeadlineExceeded`), освобождает соединение в пул и возвращает клиенту статус `http.StatusGatewayTimeout` (504) вместо бесконечного ожидания.""",
    "step_by_step": [
        "Создайте HTTP-обработчик заказов, вызывающий метод репозитория с контекстом `context.WithTimeout`.",
        "Реализуйте репозиторий, выполняющий сетевой запрос к базе данных через симулированный прокси-канал.",
        "Настройте токсик задержки 1000 мс при установленном таймауте контекста 250 мс.",
        "Проверьте, что сервер возвращает клиенту статус 504 Gateway Timeout ровно через 250 мс, не дожидаясь окончания задержки в 1000 мс."
    ],
    "code_blocks": [
        {
            "filename": "latency_toxic_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"
)

type DatabaseClient struct {
	simulatedLatency atomic.Int64
}

func (db *DatabaseClient) QueryOrder(ctx context.Context, orderID string) (string, error) {
	latency := time.Duration(db.simulatedLatency.Load())
	if latency > 0 {
		select {
		case <-time.After(latency):
		case <-ctx.Done():
			return "", ctx.Err()
		}
	}
	return fmt.Sprintf("OrderData_%s", orderID), nil
}

func OrderHandler(db *DatabaseClient) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(r.Context(), 250*time.Millisecond)
		defer cancel()

		orderID := r.URL.Query().Get("id")
		data, err := db.QueryOrder(ctx, orderID)
		if err != nil {
			if errors.Is(err, context.DeadlineExceeded) {
				http.Error(w, "504 Gateway Timeout: БД превысила SLA", http.StatusGatewayTimeout)
				return
			}
			http.Error(w, "500 Internal Server Error", http.StatusInternalServerError)
			return
		}

		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(data))
	}
}

func TestLatencyToxicTimeoutHandling(t *testing.T) {
	db := &DatabaseClient{}
	server := httptest.NewServer(OrderHandler(db))
	defer server.Close()

	db.simulatedLatency.Store(int64(20 * time.Millisecond))
	resp, err := http.Get(server.URL + "/order?id=101")
	if err != nil {
		t.Fatalf("ошибка запроса: %v", err)
	}
	if resp.StatusCode != http.StatusOK {
		t.Errorf("ожидался 200 OK, получен %d", resp.StatusCode)
	}
	resp.Body.Close()

	db.simulatedLatency.Store(int64(1000 * time.Millisecond))
	start := time.Now()
	resp, err = http.Get(server.URL + "/order?id=102")
	if err != nil {
		t.Fatalf("ошибка запроса: %v", err)
	}
	duration := time.Since(start)
	resp.Body.Close()

	if resp.StatusCode != http.StatusGatewayTimeout {
		t.Errorf("ожидался статус 504, получен %d", resp.StatusCode)
	}

	if duration < 240*time.Millisecond || duration > 350*time.Millisecond {
		t.Errorf("Таймаут сработал некорректно: %v", duration)
	}
}

func main() {
	fmt.Println("Тестирование Latency Toxic с context.WithTimeout завершено успешно")
}
"""
        }
    ],
    "under_the_hood": "Когда в сокете возникает искусственная задержка, горутина системного ввода-вывода блокируется в системном вызове `epoll_wait`. Механизм `context.WithTimeout` создает таймер через `time.AfterFunc` в рантайме Go. По истечении 250 мс рантайм вызывает отмену контекста, закрывая канал `ctx.Done()`. Драйвер БД, слушающий этот канал, немедленно прекращает чтение сокета, возвращая ошибку `context.DeadlineExceeded` вверх по стеку вызовов, освобождая поток исполнения.",
    "pitfalls": [
        "Создание `context.WithTimeout` без обязательного вызова `defer cancel()`: таймер остается в памяти до момента его естественного истечения, создавая утечку ресурсов рантайма.",
        "Использование `r.Context()` без дочернего таймаута: если клиент не разорвет соединение, сервер зависнет навсегда до глобального `http.Server.ReadTimeout`.",
        "Игнорирование ошибок контекста: возврат ошибки 500 вместо 504 маскирует истинную причину деградации."
    ],
    "bigtech_interview": "Почему в распределенных системах критически важно использовать сквозную передачу дедлайнов (Deadline Propagation / gRPC Metadata)? Если клиент установил дедлайн 500 мс, а первый сервис уже потратил 450 мс на вычисления, отправка запроса во второй сервис с дефолтным таймаутом 1000 мс бессмысленна: клиент в любом случае отвалится через 50 мс. Проброс оставшегося бюджета времени (`context.Deadline()`) позволяет downstream-сервисам сразу отклонять заведомо просроченные запросы."
})

# Exercise 5
exercises.append({
    "num": 5,
    "title": "Инъекция сетевого джиттера (Jitter Toxic)",
    "task": "Реалистичные сетевые сбои характеризуются не константной задержкой, а резкими колебаниями (джиттером). Настройте токсик с задержкой 500 мс и джиттером 300 мс. Проанализируйте поведение пула соединений `pgxpool`: не приводит ли вариативность задержек к исчерпанию соединений и росту очереди ожидания.",
    "theory": r"""Джиттер (Jitter) — это статистическая дисперсия сетевой задержки пакетов. В реальных распределенных системах задержка никогда не бывает константной: она подчиняется логнормальному распределению с тяжелым хвостом (Heavy Tail).

В Toxiproxy токсик `latency` принимает два параметра:
- `latency`: базовая задержка (например, 500 мс).
- `jitter`: полуинтервал случайного отклонения (например, 300 мс). Реальная задержка каждого пакета будет равномерно распределена в интервале $[500 - 300, 500 + 300] = [200, 800]$ мс.

Влияние джиттера на пул соединений СУБД (`pgxpool` / `database/sql`):
1. Когда задержка внезапно подскакивает до 800 мс, соединения в пуле задерживаются дольше обычного.
2. Входящие запросы накапливаются быстрее, чем освобождаются соединения.
3. Пул достигает лимита `MaxConns` (например, 10 соединений).
4. Все последующие горутины встают в очередь ожидания соединения (`AcquireWaitCount`).
5. Если тайм-аут ожидания освобождения соединения превышает допустимый предел, запросы начинают падать с ошибкой `conn pool exhausted`.""",
    "step_by_step": [
        "Реализуйте симулятор пула соединений с фиксированным размером `MaxConns` и очередью ожидания.",
        "Реализуйте генератор задержки с равномерным джиттером вокруг базового значения.",
        "Смоделируйте конкурентный поток из 50 горутин, одновременно обращающихся к базе через пул соединений при включенном джиттере (200 мс ± 150 мс).",
        "Соберите метрики: максимальное время ожидания соединения, количество отброшенных запросов и средний размер очереди."
    ],
    "code_blocks": [
        {
            "filename": "jitter_pool_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"math/rand"
	"sync"
	"sync/atomic"
	"time"
)

type ConnectionPoolSimulator struct {
	sem          chan struct{}
	maxConns     int
	acquireWait  atomic.Int64
	timeouts     atomic.Int64
	successCalls atomic.Int64
}

func NewConnectionPoolSimulator(maxConns int) *ConnectionPoolSimulator {
	return &ConnectionPoolSimulator{
		sem:      make(chan struct{}, maxConns),
		maxConns: maxConns,
	}
}

func (p *ConnectionPoolSimulator) Acquire(ctx context.Context) (func(), error) {
	p.acquireWait.Add(1)
	defer p.acquireWait.Add(-1)

	select {
	case p.sem <- struct{}{}:
		return func() { <-p.sem }, nil
	case <-ctx.Done():
		p.timeouts.Add(1)
		return nil, errors.New("ошибка пула: таймаут ожидания соединения")
	}
}

type JitterSimulator struct {
	baseLatency time.Duration
	jitter      time.Duration
	rng         *rand.Rand
	mu          sync.Mutex
}

func NewJitterSimulator(base, jitter time.Duration) *JitterSimulator {
	return &JitterSimulator{
		baseLatency: base,
		jitter:      jitter,
		rng:         rand.New(rand.NewSource(time.Now().UnixNano())),
	}
}

func (j *JitterSimulator) Delay() time.Duration {
	j.mu.Lock()
	defer j.mu.Unlock()
	delta := time.Duration(j.rng.Int63n(int64(2*j.jitter))) - j.jitter
	actual := j.baseLatency + delta
	if actual < 0 {
		return 0
	}
	return actual
}

func main() {
	pool := NewConnectionPoolSimulator(10)
	jitter := NewJitterSimulator(200*time.Millisecond, 150*time.Millisecond)

	var wg sync.WaitGroup
	totalRequests := 50

	start := time.Now()
	for i := 0; i < totalRequests; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			ctx, cancel := context.WithTimeout(context.Background(), 250*time.Millisecond)
			defer cancel()

			release, err := pool.Acquire(ctx)
			if err != nil {
				return
			}
			defer release()

			delay := jitter.Delay()
			time.Sleep(delay)
			pool.successCalls.Add(1)
		}(i)
	}

	wg.Wait()
	elapsed := time.Since(start)

	fmt.Println("=== РЕЗУЛЬТАТЫ СТРЕСС-ТЕСТА ПОД ДЖИТТЕРОМ ===")
	fmt.Printf("Время теста:             %v\n", elapsed)
	fmt.Printf("Успешных запросов:       %d / %d\n", pool.successCalls.Load(), totalRequests)
	fmt.Printf("Упавших по таймауту пула: %d\n", pool.timeouts.Load())
}
"""
        }
    ],
    "under_the_hood": "Сетевой джиттер ломает математическую стабильность очередей (теория массового обслуживания M/M/c). При константной задержке 200 мс 10 воркеров обрабатывают 50 запросов в секунду. Но при возникновении джиттера 350 мс пропускная способность пула мгновенно падает до 28 запросов/сек, при этом скорость поступления остается прежней. Очередь начинает расти экспоненциально, приводя к исчерпанию буферов и лавинообразным таймаутам.",
    "pitfalls": [
        "Недооценка джиттера: тестирование только со статической задержкой не выявляет проблем конкуренции за ресурсы и резонансных волн перегрузки.",
        "Отсутствие очереди с ограничением глубины: неограниченная очередь ожидания соединения приводит к латентной утечке памяти под нагрузкой.",
        "Слишком оптимистичный таймаут пула соединений (`pool.AcquireTimeout`), совпадающий с общим SLA запроса."
    ],
    "bigtech_interview": "Как защитить сервис от каскадного коллапса пула соединений БД при резком росте сетевого джиттера? Необходимо применять три паттерна: 1) Адаптивный таймаут ожидания соединения в пуле (`AcquireTimeout` не более 15-20% от общего SLA запроса); 2) Ограничение очереди запросов (Queue Size) с быстрым сбросом избыточной нагрузки (Fast Fail / Drop Early); 3) Клиентский Circuit Breaker, предотвращающий бомбардировку перегруженного пула новыми соединениями."
})

# Exercise 6
exercises.append({
    "num": 6,
    "title": "Ограничение пропускной способности (Bandwidth Toxic)",
    "task": "Установите токсик ограничения полосы пропускания: лимит 10 КБ/с. Отправьте запрос на выгрузку отчета размером 5 МБ. Продемонстрируйте, как медленная передача данных может заблокировать воркеры приложения, если не настроены таймауты чтения/записи сокетов (`http.Server.WriteTimeout`).",
    "theory": r"""Токсик `bandwidth` искусственно ограничивает скорость передачи данных в килобайтах в секунду (КБ/с). Это имитирует работу мобильных клиентов в условиях плохого 2G/EDGE покрытия, перегруженные каналы WAN между датацентрами или атаку типа Slowloris / Slow Read.

В стандартном `http.Server` в Go:
- По умолчанию поля `ReadTimeout`, `WriteTimeout` и `IdleTimeout` равны `0` (бесконечность).
- Если сервер отдает клиенту файл размером 5 МБ, а канал ограничен скоростью 10 КБ/с, передача займет:
  $$\text{Время} = \frac{5 \times 1024 \text{ КБ}}{10 \text{ КБ/с}} = 512 \text{ секунд} \approx 8.5 \text{ минут!}$$
- В течение всех 8.5 минут горутина обработчика и буфер сокета заблокированы на системном вызове `write()`.
- Тысяча таких медленных клиентов полностью парализует веб-сервер, исчерпав системные файловые дескрипторы и память.

Решение: настройка `http.Server.WriteTimeout` или обертка `http.ResponseWriter` в потоковый ограничитель задержки.""",
    "step_by_step": [
        "Создайте `http.Server` с настраиваемым параметром `WriteTimeout`.",
        "Реализуйте обработчик `/report`, генерирующий большой объем данных (5 МБ) через `io.Copy`.",
        "Смоделируйте медленного клиента (Slow Client / Bandwidth Throttling), читающего данные со скоростью 10 КБ/с.",
        "Продемонстрируйте, как сервер с включенным `WriteTimeout` (например, 500 мс) принудительно обрывает TCP сокет медленного клиента, защищая свои ресурсы от зависания."
    ],
    "code_blocks": [
        {
            "filename": "bandwidth_timeout_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"bytes"
	"fmt"
	"io"
	"net"
	"net/http"
	"testing"
	"time"
)

// SlowReaderConn эмулирует токсик ограничения полосы пропускания (Bandwidth Limiter)
type SlowReaderConn struct {
	net.Conn
	bytesPerSec int
}

func (c *SlowReaderConn) Read(b []byte) (int, error) {
	// Ограничиваем размер считываемого чанка
	maxChunk := c.bytesPerSec / 10
	if maxChunk <= 0 {
		maxChunk = 1
	}
	if len(b) > maxChunk {
		b = b[:maxChunk]
	}

	n, err := c.Conn.Read(b)
	if n > 0 {
		time.Sleep(100 * time.Millisecond) // Замедление передачи
	}
	return n, err
}

func TestWriteTimeoutUnderBandwidthToxic(t *testing.T) {
	// Создаем тестовый HTTP-сервер со строгим WriteTimeout: 300 мс
	mux := http.NewServeMux()
	mux.HandleFunc("/large-report", func(w http.ResponseWriter, r *http.Request) {
		// Генерируем 2 МБ данных
		data := bytes.Repeat([]byte("A"), 2*1024*1024)
		w.Header().Set("Content-Type", "application/octet-stream")
		_, _ = w.Write(data)
	})

	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("ошибка запуска listener: %v", err)
	}

	server := &http.Server{
		Handler:      mux,
		WriteTimeout: 300 * time.Millisecond, // Защита от медленных клиентов!
	}
	defer server.Close()

	go func() {
		_ = server.Serve(listener)
	}()

	// Подключаемся медленным клиентом
	rawConn, err := net.Dial("tcp", listener.Addr().String())
	if err != nil {
		t.Fatalf("ошибка подключения: %v", err)
	}
	defer rawConn.Close()

	slowConn := &SlowReaderConn{
		Conn:        rawConn,
		bytesPerSec: 10 * 1024, // 10 КБ/с
	}

	// Отправляем HTTP GET запрос
	req := "GET /large-report HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n"
	_, _ = slowConn.Write([]byte(req))

	start := time.Now()
	buf := make([]byte, 1024)
	totalRead := 0

	for {
		n, err := slowConn.Read(buf)
		totalRead += n
		if err != nil {
			// Соединение должно быть разорвано сервером по таймауту!
			break
		}
	}
	duration := time.Since(start)

	t.Logf("Прочитано: %d байт за %v (соединение разорвано сервером)", totalRead, duration)

	// Проверяем, что сервер разорвал соединение приблизительно за 300-500 мс, а не позволил качать 2 МБ минутами
	if duration > 1*time.Second {
		t.Errorf("WriteTimeout не защитил сервер! Чтение продолжалось %v", duration)
	}
	if totalRead >= 2*1024*1024 {
		t.Errorf("Клиент успел выкачать весь файл целиком, защита не сработала")
	}
}

func main() {
	fmt.Println("Тест Bandwidth Toxic и WriteTimeout завершен успешно")
}
"""
        }
    ],
    "under_the_hood": "Параметр `http.Server.WriteTimeout` реализован в Go через низкоуровневый вызов `net.Conn.SetWriteDeadline()`. После того как тело запроса прочитано, рантайм Go взводит дедлайн на сокете `deadline = time.Now().Add(srv.WriteTimeout)`. Если клиент читает данные слишком медленно и буфер сокета в ядре операционной системы переполняется (`SO_SNDBUF`), последующий системный вызов `write()` блокируется и по истечении дедлайна завершается ошибкой `i/o timeout`, после чего рантайм принудительно посылает TCP RST или FIN, завершая горутину.",
    "pitfalls": [
        "Использование нулевого `WriteTimeout` в боевых сервисах: открывает уязвимость для DoS-атак медленного чтения (Slow Read DoS).",
        "Конфликт `WriteTimeout` с Server-Sent Events (SSE) и WebSockets: для долгоживущих стримов глобальный `WriteTimeout` сервера применять нельзя; вместо этого используется `http.ResponseController.SetWriteDeadline` на отдельные сообщения.",
        "Игнорирование `ReadHeaderTimeout`: злоумышленник может слать заголовки по 1 байту в секунду, удерживая соединение открытым до бесконечности."
    ],
    "bigtech_interview": "В чем разница между `WriteTimeout` сервера и контекстом `r.Context()` в HTTP-обработчике Go? Контекст `r.Context()` завершается, когда клиент сам разорвал соединение (поступил TCP RST/FIN). Но если недобросовестный или зависший клиент держит сокет открытым и просто не вычитывает байты ответа, `r.Context()` никогда не отменится! Завершить такую сессию и спасти ресурсы сервера может только жесткий `WriteTimeout` на уровне сокета."
})

# Exercise 7
exercises.append({
    "num": 7,
    "title": "Нарезка пакетов (Slicer Toxic) и повреждение потока",
    "task": "Настройте токсик `slicer`, разбивающий передаваемые TCP-данные на мелкие куски по 10 байт со случайными задержками между ними. Проверьте устойчивость парсеров сетевых протоколов (Protobuf, JSON) к разорванным пакетам. Убедитесь, что код корректно собирает полный кадр данных перед десериализацией.",
    "theory": r"""TCP — это потоковый протокол (Stream-oriented), а не протокол сообщений (Message-oriented). В протоколе TCP нет понятия «границы сообщения» или «пакета прикладного уровня»: данные передаются как непрерывный поток байтов.

Токсик `slicer`:
- Разрезает передаваемые TCP-пакеты на фрагменты заданного размера (например, по 10-50 байт).
- Внедряет случайные миллисекундные задержки между фрагментами.
- Эмулирует агрессивную фрагментацию IP-пакетов в гетерогенных сетях (MTU mismatch, NAT, туннелирование VXLAN/GRE).

Типичная архитектурная ошибка начинающих разработчиков:
Наивный вызов `conn.Read(buf)` и предположение, что один вызов `Read` вернет весь JSON или Protobuf объект целиком. При включении токсика `slicer` вызов `conn.Read` вернет только первые 10 байт, и парсер JSON завершится фатальной ошибкой `unexpected EOF` или `syntax error`.

Надежное решение: кадрирование сообщений (Framing):
1. **Length-Prefixed Framing:** перед телом сообщения передается 4-байтовый заголовок с точной длиной полезной нагрузки (`uint32`).
2. Чтение заголовка через `io.ReadFull(conn, headerBuf)`.
3. Чтение ровно N байт полезной нагрузки через `io.ReadFull(conn, payloadBuf)`.""",
    "step_by_step": [
        "Разработайте протокол кадрирования: 4 байта длины (BigEndian uint32) + сериализованное полезное сообщение.",
        "Реализуйте симулятор токсика `SlicerWriter`, который искусственно дробит исходящие байты на куски фиксированного размера (по 8 байт) с паузами.",
        "Реализуйте кодек чтения `FrameDecoder`, использующий `io.ReadFull` для гарантированного восстановления кадров из фрагментированного TCP-потока.",
        "Напишите тест, доказывающий, что наивный парсер падает на нарезанных пакетах, а кадрированный декодер корректно собирает 100% сообщений."
    ],
    "code_blocks": [
        {
            "filename": "slicer_framing_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"testing"
	"time"
)

type UserPayload struct {
	ID       string `json:"id"`
	Email    string `json:"email"`
	Role     string `json:"role"`
	Metadata string `json:"metadata"`
}

// SlicedPipe эмулирует токсик slicer, отдавая данные кусками по chunkSize байт
type SlicedPipe struct {
	data      []byte
	offset    int
	chunkSize int
}

func NewSlicedPipe(data []byte, chunkSize int) *SlicedPipe {
	return &SlicedPipe{
		data:      data,
		chunkSize: chunkSize,
	}
}

func (s *SlicedPipe) Read(p []byte) (int, error) {
	if s.offset >= len(s.data) {
		return 0, io.EOF
	}

	remaining := len(s.data) - s.offset
	toRead := s.chunkSize
	if toRead > remaining {
		toRead = remaining
	}
	if toRead > len(p) {
		toRead = len(p)
	}

	copy(p, s.data[s.offset:s.offset+toRead])
	s.offset += toRead

	time.Sleep(2 * time.Millisecond) // Микрозадержка между фрагментами
	return toRead, nil
}

// EncodeFramedMessage упаковывает сообщение: 4 байта длины (BigEndian) + тело
func EncodeFramedMessage(msg any) ([]byte, error) {
	body, err := json.Marshal(msg)
	if err != nil {
		return nil, err
	}

	buf := new(bytes.Buffer)
	length := uint32(len(body))
	if err := binary.Write(buf, binary.BigEndian, length); err != nil {
		return nil, err
	}
	buf.Write(body)
	return buf.Bytes(), nil
}

// DecodeFramedMessage гарантированно вычитывает полный кадр через io.ReadFull
func DecodeFramedMessage(r io.Reader, dest any) error {
	header := make([]byte, 4)
	if _, err := io.ReadFull(r, header); err != nil {
		return fmt.Errorf("ошибка чтения длины кадра: %w", err)
	}

	length := binary.BigEndian.Uint32(header)
	payload := make([]byte, length)
	if _, err := io.ReadFull(r, payload); err != nil {
		return fmt.Errorf("ошибка чтения тела кадра (%d байт): %w", length, err)
	}

	return json.Unmarshal(payload, dest)
}

func TestSlicerToxicResilience(t *testing.T) {
	original := UserPayload{
		ID:       "usr_99882233",
		Email:    "principal-engineer@tech-giant.ru",
		Role:     "StaffArchitect",
		Metadata: "HighLoad distributed systems chaos experiment validation",
	}

	// 1. Упаковываем сообщение в кадр
	encoded, err := EncodeFramedMessage(original)
	if err != nil {
		t.Fatalf("ошибка кодирования: %v", err)
	}

	// 2. Наивное чтение (симуляция ошибки)
	naivePipe := NewSlicedPipe(encoded[4:], 10) // Без заголовка длины, нарезка по 10 байт
	naiveBuf := make([]byte, 256)
	n, _ := naivePipe.Read(naiveBuf)
	var naiveUser UserPayload
	naiveErr := json.Unmarshal(naiveBuf[:n], &naiveUser)
	if naiveErr == nil {
		t.Error("Ожидалась ошибка парсинга при наивном чтении неполного пакета!")
	} else {
		t.Logf("Наивный парсер ожидаемо упал на фрагментированном пакете: %v", naiveErr)
	}

	// 3. Надежное чтение через FrameDecoder под действием Slicer Toxic (куски по 7 байт!)
	slicedStream := NewSlicedPipe(encoded, 7)
	var recovered UserPayload
	if err := DecodeFramedMessage(slicedStream, &recovered); err != nil {
		t.Fatalf("FrameDecoder не смог собрать сообщение: %v", err)
	}

	if recovered.ID != original.ID || recovered.Email != original.Email {
		t.Errorf("Данные повреждены при сборке кадра: %+v", recovered)
	}
	t.Logf("Сообщение успешно собрано из нарезки по 7 байт: %+v", recovered)
}

func main() {
	fmt.Println("Тестирование устойчивости к Slicer Toxic завершено успешно")
}
"""
        }
    ],
    "under_the_hood": "Функция `io.ReadFull` внутри реализует цикл: она многократно вызывает `r.Read(buf[read:])` до тех пор, пока буфер не заполнится ровно до конца (`len(buf)` байт) либо пока не вернется `io.EOF` или сетевая ошибка. Если поток прерван до наполнения буфера, возвращается информативная ошибка `io.ErrUnexpectedEOF`, позволяющая однозначно отличить повреждение кадра от планового закрытия соединения.",
    "pitfalls": [
        "Чтение неограниченного `uint32` размера кадра: злоумышленник может прислать длину `0xFFFFFFFF` (4 ГБ), что вызовет панику `out of memory` при аллокации буфера (`make([]byte, length)`). Необходимо всегда проверять `if length > MaxAllowedMessageSize { return ErrMessageTooLarge }`.",
        "Использование `bufio.Reader.ReadLine()`: метод может вернуть неполную строку без ошибки при переполнении внутреннего буфера.",
        "Забывание порядка байт (Endianness): рассинхронизация BigEndian / LittleEndian между платформами приведет к некорректной длине кадра."
    ],
    "bigtech_interview": "Почему в современных RPC протоколах (gRPC, Redis RESP, Kafka Wire Protocol) всегда используется явное кадрирование (Length-prefixed или делимитеры с TLV), а не сырой потоковый JSON? TCP не сохраняет границы прикладных пакетов: N small writes могут быть объединены алгоритмом Нейгла (Nagle's algorithm) в один сегмент, а один large write разбит по границам MTU (1500 байт). Явное кадрирование гарантирует однозначную десериализацию данных независимо от сетевой сегментации."
})

# Exercise 8
exercises.append({
    "num": 8,
    "title": "Полузакрытые сокеты и медленное закрытие (Slow Close Toxic)",
    "task": "Настройте токсик `slow_close` (задержка закрытия соединения на 5 секунд). Сымитируйте поведение медленного клиента при TCP-закрытии (FIN/ACK). Проверьте, не накапливает ли ваш Go-сервер сокеты в состоянии `CLOSE_WAIT` / `TIME_WAIT`, приводящие к исчерпанию лимита файловых дескрипторов.",
    "theory": r"""Сетевое завершение соединения в протоколе TCP — это четырехэтапный процесс (4-way handshake):
1. Инициатор закрытия (например, клиент) отправляет пакет `FIN` и переходит в состояние `FIN_WAIT_1`.
2. Сервер отправляет `ACK` и переходит в состояние `CLOSE_WAIT`. В этот момент сокет полузакрыт (Half-Closed): клиент больше не пишет данные, но сервер всё еще может слать байты.
3. Сервер вызывает `conn.Close()`, отправляет свой пакет `FIN` и ждет финального `ACK` от клиента.
4. Клиент отправляет финальный `ACK` и остается в состоянии `TIME_WAIT` (обычно 60 секунд), чтобы задержавшиеся в сети дубликаты пакетов не нарушили следующее новое соединение.

Токсик `slow_close` в Toxiproxy искусственно задерживает отправку пакета `FIN` на стороне прокси (например, на 5–10 секунд).

Опасность для Go-серверов:
Если сервер не обрабатывает полузакрытые сокеты или клиент медленно завершает рукопожатие, тысячи файловых дескрипторов застревают в таблице ядра операционной системы в статусе `CLOSE_WAIT` или `FIN_WAIT_2`. Когда лимит `ulimit -n` исчерпан, сервер перестает принимать любые новые подключения (`accept: too many open files`).

Решение в Go: использование `http.Server.IdleTimeout` и хуков `http.Server.ConnState` для мониторинга зависших сокетов.""",
    "step_by_step": [
        "Изучите состояния TCP сокетов в ядре Linux (`CLOSE_WAIT`, `TIME_WAIT`, `FIN_WAIT_2`).",
        "Настройте мониторинг жизненного цикла TCP-соединений в Go с помощью `http.Server.ConnState`.",
        "Реализуйте симулятор зависшего полузакрытого сокета (клиент закрывает запись `CloseWrite()`, но задерживает вычитку и полное закрытие).",
        "Настройте `IdleTimeout` сервера и докажите, что зависшие сокеты принудительно очищаются сервером."
    ],
    "code_blocks": [
        {
            "filename": "slow_close_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"net"
	"net/http"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

type ConnectionTracker struct {
	activeCount atomic.Int64
	idleCount   atomic.Int64
	closedCount atomic.Int64
	mu          sync.Mutex
	conns       map[string]time.Time
}

func NewConnectionTracker() *ConnectionTracker {
	return &ConnectionTracker{
		conns: make(map[string]time.Time),
	}
}

func (ct *ConnectionTracker) OnStateChange(conn net.Conn, state http.ConnState) {
	addr := conn.RemoteAddr().String()
	switch state {
	case http.StateNew:
		ct.activeCount.Add(1)
		ct.mu.Lock()
		ct.conns[addr] = time.Now()
		ct.mu.Unlock()
	case http.StateActive:
		// Соединение активно обрабатывает запрос
	case http.StateIdle:
		ct.idleCount.Add(1)
	case http.StateClosed, http.StateHijacked:
		ct.activeCount.Add(-1)
		ct.closedCount.Add(1)
		ct.mu.Lock()
		delete(ct.conns, addr)
		ct.mu.Unlock()
	}
}

func TestSlowCloseHandling(t *testing.T) {
	tracker := NewConnectionTracker()

	mux := http.NewServeMux()
	mux.HandleFunc("/ping", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("PONG"))
	})

	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("не удалось открыть listener: %v", err)
	}

	server := &http.Server{
		Handler:     mux,
		IdleTimeout: 200 * time.Millisecond, // Быстро сбрасываем зависшие соединения
		ConnState:   tracker.OnStateChange,
	}
	defer server.Close()

	go func() {
		_ = server.Serve(listener)
	}()

	// 1. Открываем TCP соединение медленного клиента
	tcpConn, err := net.Dial("tcp", listener.Addr().String())
	if err != nil {
		t.Fatalf("ошибка подключения: %v", err)
	}

	// Отправляем HTTP запрос
	req := "GET /ping HTTP/1.1\r\nHost: localhost\r\n\r\n"
	_, _ = tcpConn.Write([]byte(req))

	reply := make([]byte, 128)
	_, _ = tcpConn.Read(reply)

	if tracker.activeCount.Load() != 1 {
		t.Errorf("Ожидалось 1 активное соединение, зафиксировано %d", tracker.activeCount.Load())
	}

	// 2. Симулируем токсик slow_close: закрываем только половину сокета на запись
	// и намеренно не закрываем сокет на чтение в течение некоторого времени
	if tc, ok := tcpConn.(*net.TCPConn); ok {
		_ = tc.CloseWrite() // Отправлен FIN от клиента
	}

	// 3. Ждем срабатывания IdleTimeout сервера
	time.Sleep(350 * time.Millisecond)

	// Сервер должен был закрыть сокет по IdleTimeout
	if tracker.activeCount.Load() != 0 {
		t.Errorf("Сокет не был закрыт по IdleTimeout, активных: %d", tracker.activeCount.Load())
	}
	if tracker.closedCount.Load() < 1 {
		t.Errorf("Не зафиксировано закрытие сокета трекером")
	}

	_ = tcpConn.Close()
	t.Log("Зависшее полузакрытое соединение успешно утилизировано сервером")
}

func main() {
	fmt.Println("Тест Slow Close и ConnState завершен успешно")
}
"""
        }
    ],
    "under_the_hood": "В ядре Linux состояние `CLOSE_WAIT` возникает, когда удаленный хост закрыл соединение на запись (пришел TCP FIN), а локальное приложение еще не вызвало `close(fd)`. Никакой системный таймаут ядра Linux (даже `tcp_fin_timeout`, регулирующий только `FIN_WAIT_2`) не может закрыть сокет в `CLOSE_WAIT` — это исключительно обязанность процесса в User Space. Если Go-сервер забыл прочитать тело запроса до конца или не настроил `IdleTimeout`, сокет в `CLOSE_WAIT` утекает навсегда.",
    "pitfalls": [
        "Отсутствие `IdleTimeout` у `http.Server`: клиент держит TCP-соединение открытым в Keep-Alive режиме, не отправляя запросов, удерживая аллоцированные структуры горутин сервера.",
        "Зависание в `CLOSE_WAIT` из-за блокировки пула воркеров: если горутина обработчика зависла на внешней блокировке (Deadlock), сокет никогда не закроется.",
        "Превышение лимита файловых дескрипторов ОС: невозможность принять соединения даже от локального healthcheck (`kubelet livenessProbe`), приводящая к рестарту пода."
    ],
    "bigtech_interview": "Почему накопление сокетов в статусе `CLOSE_WAIT` является симптомом бага в коде приложения, а не сетевой проблемы? Потому что статус `CLOSE_WAIT` означает, что ядро Linux уже получило от клиента FIN-пакет и ждет, когда именно наше приложение выполнит системный вызов `close()` для соответствующего файлового дескриптора. Накопление сокетов свидетельствует о блокировке или зависании горутин обработчиков."
})

# Exercise 9
exercises.append({
    "num": 9,
    "title": "Внезапный разрыв соединений (Reset Peer Toxic)",
    "task": "Включите токсик `reset_peer`, немедленно отправляющий TCP-пакет `RST` при попытке чтения или записи. Проверьте, как клиент базы данных или Redis обрабатывает ошибку `connection reset by peer`: переподключается ли пул соединений автоматически или начинает падать на всех последующих запросах?",
    "theory": r"""В отличие от штатного закрытия соединения (FIN handshake), пакет `TCP RST` (Reset) является экстренным сигналом немедленного разрыва канала связи. Пакет RST генерируется ядром Linux в следующих случаях:
1. Попытка отправить данные в сокет, который уже закрыт удаленной стороной.
2. Аварийное падение процесса сервера (SIGKILL, segfault, OOMKilled).
3. Принудительный сброс сессии сетевым экраном (Firewall / State Table Timeout).
4. Активация токсика `reset_peer` в Toxiproxy.

В языке Go попытка чтения или записи в такой сокет возвращает системную ошибку `syscall.ECONNRESET` («read: connection reset by peer»).

Проблема незрелых пулов соединений:
Если пул соединений (Database/Redis Pool) не умеет валидировать здоровье соединений перед выдачей их из пула, разорванное соединение возвращается пользователю. Это приводит к так называемой «волне ошибок» (error burst): десятки последующих запросов падают с ошибкой `connection reset by peer`, пока пул наконец не отбросит битые сокеты.

Паттерн надежности:
1. Метод `PingContext` / `Healthcheck` перед выдачей сокета из пула.
2. Прозрачный авто-реконнект с экспоненциальным backoff.
3. Отбрасывание разорванных соединений без возврата в пул.""",
    "step_by_step": [
        "Создайте структуру управляемого пула соединений с проверкой живости соединений.",
        "Смоделируйте сетевой сокет, имитирующий получение пакета TCP RST (`syscall.ECONNRESET`).",
        "Реализуйте обертку клиента с механизмом прозрачного восстановления (Auto-Reconnect and Retry) при получении ошибок сброса соединения.",
        "Протестируйте устойчивость клиентского кода к непрерывным инъекциям `reset_peer`: докажите, что клиент автоматически переустанавливает связь без возврата ошибок вызывающему бизнес-коду."
    ],
    "code_blocks": [
        {
            "filename": "reset_peer_resilience_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"syscall"
	"testing"
	"time"
)

// ErrConnectionReset имитирует ошибку syscall.ECONNRESET
var ErrConnectionReset = fmt.Errorf("read tcp: %w", syscall.ECONNRESET)

// MockRobustClient представляет отказоустойчивый клиент с авто-переподключением
type MockRobustClient struct {
	connected    bool
	failNextRead bool
	reconnects   int
}

func (c *MockRobustClient) Connect() error {
	c.connected = true
	c.reconnects++
	return nil
}

func (c *MockRobustClient) Query(ctx context.Context, cmd string) (string, error) {
	if !c.connected {
		return "", errors.New("клиент не подключен")
	}

	if c.failNextRead {
		c.connected = false
		c.failNextRead = false
		return "", ErrConnectionReset
	}

	return "OK:" + cmd, nil
}

// ExecuteWithRetry выполняет команду с автоматическим переподключением при RST
func ExecuteWithRetry(ctx context.Context, client *MockRobustClient, cmd string, maxRetries int) (string, error) {
	for attempt := 0; attempt <= maxRetries; attempt++ {
		select {
		case <-ctx.Done():
			return "", ctx.Err()
		default:
		}

		if !client.connected {
			if err := client.Connect(); err != nil {
				time.Sleep(10 * time.Millisecond)
				continue
			}
		}

		res, err := client.Query(ctx, cmd)
		if err == nil {
			return res, nil
		}

		// Проверяем, является ли ошибка разрывом связи (RST / broken pipe)
		if errors.Is(err, syscall.ECONNRESET) || errors.Is(err, io.ErrUnexpectedEOF) {
			// Сбрасываем битое соединение и повторяем попытку
			client.connected = false
			continue
		}

		// Логическая ошибка — не ретраим
		return "", err
	}
	return "", fmt.Errorf("исчерпаны попытки переподключения (%d)", maxRetries)
}

func TestResetPeerAutoRecovery(t *testing.T) {
	client := &MockRobustClient{}
	_ = client.Connect()

	// 1. Успешный запрос
	ctx := context.Background()
	res, err := ExecuteWithRetry(ctx, client, "GET_USER", 3)
	if err != nil || res != "OK:GET_USER" {
		t.Fatalf("ошибка первого запроса: %v", err)
	}

	// 2. Инжектируем токсик reset_peer (следующий read вернет syscall.ECONNRESET)
	client.failNextRead = true

	// 3. Выполняем запрос: клиент должен перехватить RST, переподключиться и вернуть корректный результат
	res, err = ExecuteWithRetry(ctx, client, "GET_USER", 3)
	if err != nil {
		t.Fatalf("клиент не пережил TCP RST: %v", err)
	}
	if res != "OK:GET_USER" {
		t.Errorf("неверный ответ после реконнекта: %s", res)
	}

	if client.reconnects != 2 {
		t.Errorf("ожидалось 2 подключения (начальное + реконнект), зафиксировано: %d", client.reconnects)
	}
	t.Logf("TCP RST успешно нейтрализован, клиент переподключился (%d reconnects)", client.reconnects)
}

func main() {
	fmt.Println("Тестирование устойчивости к Reset Peer завершено успешно")
}
"""
        }
    ],
    "under_the_hood": "Когда процесс получает пакет с флагом RST, операционная система переводит сокет в состояние ошибки. Последующие вызовы `read()` мгновенно возвращают `-1` с кодом `ECONNRESET`, а вызовы `write()` генерируют системный сигнал `SIGPIPE` (в рантайме Go этот сигнал перехватывается и трансформируется в ошибку `syscall.EPIPE` / `broken pipe`). Идиоматичный пул в Go проверяет сокет неблокирующим чтением 1 байта или флагом `MSG_PEEK` перед выдачей соединения вызывающему коду.",
    "pitfalls": [
        "Повторная отправка неидемпотентных запросов: если TCP RST пришел после того, как сервер успел выполнить операцию списания денег, слепой retry приведет к двойному списанию. Ретраи допустимы только для идемпотентных операций или при наличии Idempotency Key.",
        "Ретрай в бесконечном цикле без задержки: может вызвать шторм переподключений (Thundering Herd) на восстанавливающийся сервер БД.",
        "Возврат поврежденного соединения обратно в пул."
    ],
    "bigtech_interview": "Как отличить ошибку `connection reset by peer`, возникшую ДО выполнения запроса на сервере, от ошибки, возникшей ПОСЛЕ выполнения? В общем случае на уровне TCP сокета это невозможно: пакет RST стирает состояние буферов. Единственный надежный способ в распределенных системах — генерация уникального ключа идемпотентности (`Idempotency-Key` / `Request-ID`) клиентом перед отправкой. При переподключении клиент шлет тот же ключ, и сервер возвращает ранее сохраненный результат без повторного исполнения бизнес-логики."
})

# Exercise 10
exercises.append({
    "num": 10,
    "title": "Хаос-тестирование Circuit Breaker (`sony/gobreaker`)",
    "task": "Оберните клиент внешнего платежного шлюза в Circuit Breaker (`sony/gobreaker`). Напишите тест: с помощью Toxiproxy инжектируйте 100% разрыв соединений. Продемонстрируйте переход предохранителя из состояния `StateClosed` в `StateOpen`, блокировку последующих вызовов без выполнения сетевых запросов и плавный возврат в `StateHalfOpen` после восстановления сети.",
    "theory": r"""Паттерн Circuit Breaker (предохранитель) предотвращает каскадные сбои в распределенной системе, прерывая вызовы к деградировавшему сервису.

Конечный автомат состояний Circuit Breaker:
1. **`StateClosed` (Закрыт — нормальный режим):**
   Все запросы беспрепятственно проходят к внешнему сервису. Ошибки подсчитываются в скользящем окне. Если доля или количество ошибок превышает пороговое значение (например, 5 ошибок подряд или >60% неудач), автомат переходит в `StateOpen`.
2. **`StateOpen` (Разомкнут — аварийный режим):**
   Все входящие запросы мгновенно отклоняются локально без выполнения сетевого вызова (`ErrOpenState`). Это разгружает упавший сервис и предотвращает зависание горутин вызывающей стороны. Взводится таймер охлаждения (`Timeout`, например 5 секунд).
3. **`StateHalfOpen` (Полуоткрыт — зондирующий режим):**
   По истечении таймера охлаждения автомат пропускает ограниченное число пробных запросов (пробников). Если пробные запросы завершаются успехом, автомат возвращается в `StateClosed`. Если хотя бы один пробник падает — автомат немедленно возвращается в `StateOpen` на новый цикл ожидания.

Популярная реализация в Go — библиотека `github.com/sony/gobreaker`.""",
    "step_by_step": [
        "Определите структуру конечного автомата `CircuitBreaker` с состояниями Closed, Open, HalfOpen.",
        "Реализуйте метод `Execute(reqFunc)`, отслеживающий счетчики успехов/ошибок и управляющий переходами состояний по тайм-ауту.",
        "Смоделируйте падение внешнего платежного шлюза (100% сетевых ошибок).",
        "Продемонстрируйте: переход в `StateOpen`, моментальный отказ без сетевых вызовов, выжидание таймаута, зондирование в `StateHalfOpen` и восстановление в `StateClosed`."
    ],
    "code_blocks": [
        {
            "filename": "circuit_breaker_chaos_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"errors"
	"fmt"
	"sync"
	"testing"
	"time"
)

type CBState int

const (
	StateClosed CBState = iota
	StateHalfOpen
	StateOpen
)

func (s CBState) String() string {
	switch s {
	case StateClosed:
		return "CLOSED"
	case StateHalfOpen:
		return "HALF_OPEN"
	case StateOpen:
		return "OPEN"
	default:
		return "UNKNOWN"
	}
}

var ErrCircuitOpen = errors.New("circuit breaker открыт: запрос отклонен без сетевого вызова")

type CircuitBreaker struct {
	mu            sync.Mutex
	state         CBState
	failureCount  int
	successCount  int
	maxFailures   int
	cooldown      time.Duration
	openedAt      time.Time
	halfOpenLimit int
}

func NewCircuitBreaker(maxFailures int, cooldown time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		state:         StateClosed,
		maxFailures:   maxFailures,
		cooldown:      cooldown,
		halfOpenLimit: 2,
	}
}

func (cb *CircuitBreaker) Execute(fn func() error) error {
	cb.mu.Lock()
	now := time.Now()

	// Проверяем охлаждение в состоянии OPEN
	if cb.state == StateOpen {
		if now.Sub(cb.openedAt) >= cb.cooldown {
			cb.state = StateHalfOpen
			cb.successCount = 0
			cb.failureCount = 0
		} else {
			cb.mu.Unlock()
			return ErrCircuitOpen
		}
	}

	currentState := cb.state
	cb.mu.Unlock()

	// Выполняем полезную нагрузку
	err := fn()

	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err != nil {
		cb.failureCount++
		if cb.state == StateHalfOpen || cb.failureCount >= cb.maxFailures {
			cb.state = StateOpen
			cb.openedAt = time.Now()
		}
		return err
	}

	// Успех
	if currentState == StateHalfOpen {
		cb.successCount++
		if cb.successCount >= cb.halfOpenLimit {
			cb.state = StateClosed
			cb.failureCount = 0
		}
	} else if currentState == StateClosed {
		cb.failureCount = 0
	}

	return nil
}

func (cb *CircuitBreaker) State() CBState {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	return cb.state
}

func TestCircuitBreakerUnderChaos(t *testing.T) {
	cb := NewCircuitBreaker(3, 100*time.Millisecond)

	downstreamAvailable := true
	networkCalls := 0

	mockPaymentCall := func() error {
		networkCalls++
		if !downstreamAvailable {
			return errors.New("connection refused")
		}
		return nil
	}

	// 1. Штатный режим (CLOSED)
	if err := cb.Execute(mockPaymentCall); err != nil {
		t.Fatalf("ожидался успех: %v", err)
	}
	if cb.State() != StateClosed {
		t.Errorf("ожидался CLOSED, получен %v", cb.State())
	}

	// 2. Инъекция хаоса: падение платежного шлюза
	downstreamAvailable = false
	for i := 0; i < 3; i++ {
		_ = cb.Execute(mockPaymentCall)
	}

	// 3. Предохранитель должен разомкнуться (OPEN)
	if cb.State() != StateOpen {
		t.Fatalf("ожидался переход в OPEN, получен %v", cb.State())
	}
	callsBefore := networkCalls

	// 4. Попытка запроса при открытом предохранителе
	err := cb.Execute(mockPaymentCall)
	if !errors.Is(err, ErrCircuitOpen) {
		t.Errorf("ожидалась ошибка ErrCircuitOpen, получено: %v", err)
	}
	if networkCalls != callsBefore {
		t.Errorf("Сетевой вызов БЫЛ совершен в состоянии OPEN! Предохранитель дал утечку.")
	}

	// 5. Ожидание времени охлаждения (Cooldown)
	time.Sleep(120 * time.Millisecond)

	// Восстанавливаем внешний сервис
	downstreamAvailable = true

	// Первый запрос переводит в HALF_OPEN
	_ = cb.Execute(mockPaymentCall)
	// Второй успешный запрос возвращает в CLOSED
	_ = cb.Execute(mockPaymentCall)

	if cb.State() != StateClosed {
		t.Errorf("ожидался возврат в CLOSED, получен %v", cb.State())
	}
	t.Log("Circuit Breaker успешно защитил систему и корректно восстановился")
}

func main() {
	fmt.Println("Тестирование Circuit Breaker под хаос-нагрузкой завершено успешно")
}
"""
        }
    ],
    "under_the_hood": "Внутри паттерна Circuit Breaker ключевым моментом является разгрузка планировщика Go. В состоянии `StateOpen` вызов метода `Execute()` возвращает ошибку мгновенно за единицы наносекунд на уровне проверки переменной состояния в оперативной памяти. Это освобождает стек горутины, предотвращает аллокации сетевых буферов и не тратит сокетные дескрипторы на запросы, которые заведомо обречены на провал.",
    "pitfalls": [
        "Слишком длинный период охлаждения: сервис уже поднялся, а система еще 15 минут продолжает отбрасывать клиентские запросы.",
        "Слишком короткий счетчик ошибок (1 сбой): единичный сетевой сбой переводит предохранитель в OPEN, вызывая ложную тревогу и отказ обслуживания.",
        "Отсутствие отката на резервный вариант (Fallback): при открытом Circuit Breaker идиоматично возвращать закэшированные данные или деградированный ответ (stale data) вместо сырой ошибки."
    ],
    "bigtech_interview": "Чем Circuit Breaker отличается от Rate Limiter? Rate Limiter защищает целевой сервис от превышения допустимого объема входящего трафика (контроль со стороны поставщика или потребителя по квоте). Circuit Breaker защищает вызывающую сторону от зависания и каскадного отказа, когда целевой сервис уже сломался или деградировал (контроль устойчивости к сбоям)."
})

# Exercise 11
exercises.append({
    "num": 11,
    "title": "Хаос-тесты в CI/CD с использованием Testcontainers-Go",
    "task": "Создайте автоматизированный интеграционный хаос-тест в Go с помощью `testcontainers-go`: тест одновременно поднимает контейнер PostgreSQL и контейнер Toxiproxy в единой Docker-сети, прогоняет бизнес-сценарии переводов средств под инъекцией сбоев сети и валидирует целостность балансов.",
    "theory": r"""Интеграционное тестирование надежности требует воспроизводимого окружения. Использование преднастроенных статичных стендов страдает от эффекта «на моем компьютере работало» и конфликтов при параллельных сборках в CI/CD.

`Testcontainers for Go` (`github.com/testcontainers/testcontainers-go`) решает эту проблему, программно управляя жизненным циклом Docker-контейнеров прямо из Go-кода тестов.

Схема хаос-теста с Testcontainers и Toxiproxy:
```
[ Go Test Process ] 
       │
       ├────────────────────────┐ (HTTP REST :8474)
       ▼ (SQL query)            ▼
[ Toxiproxy Container ] ───> [ Toxiproxy Engine ]
       │ (:54320)               │ (Внедрение Latency / Reset)
       ▼                        ▼
[ Docker Network Bridge ] ───> [ PostgreSQL Container (:5432) ]
```

Ключевые этапы оркестрации:
1. Создание изолированной пользовательской Docker-сети (`network.New(ctx)`).
2. Запуск контейнера PostgreSQL в созданной сети.
3. Запуск контейнера Toxiproxy в той же сети.
4. Настройка прокси через клиент Toxiproxy: перенаправление с порта `:54320` контейнера Toxiproxy на внутренний DNS `postgres:5432`.
5. Выполнение транзакционных операций перевода денег в условиях сетевого хаоса.
6. Проверка сохранения инварианта: сумма балансов на счетах ДО и ПОСЛЕ хаоса должна строго совпадать.""",
    "step_by_step": [
        "Спроектируйте архитектуру хаос-теста с мок-контейнерами базы данных и Toxiproxy.",
        "Реализуйте бизнес-логику финансового перевода `TransferFunds(from, to, amount)` с явной транзакционной целостностью (ACID).",
        "Смоделируйте инъекцию сетевого сбоя в момент выполнения транзакции.",
        "Напишите тест целостности балансов: докажите, что даже при аварийном разрыве связи деньги не пропадают и не двоятся (баланс консистентен)."
    ],
    "code_blocks": [
        {
            "filename": "testcontainers_chaos_test.go",
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

type Account struct {
	ID      string
	Balance int64
}

type BankLedger struct {
	mu       sync.Mutex
	accounts map[string]*Account
}

func NewBankLedger() *BankLedger {
	return &BankLedger{
		accounts: map[string]*Account{
			"acc_alice": {ID: "acc_alice", Balance: 1000},
			"acc_bob":   {ID: "acc_bob", Balance: 500},
		},
	}
}

// TransferFunds выполняет атомарный перевод средств с откатом при ошибке
func (l *BankLedger) TransferFunds(ctx context.Context, fromID, toID string, amount int64, networkCall func() error) error {
	l.mu.Lock()
	defer l.mu.Unlock()

	from, okFrom := l.accounts[fromID]
	to, okTo := l.accounts[toID]
	if !okFrom || !okTo {
		return errors.New("аккаунт не найден")
	}

	if from.Balance < amount {
		return errors.New("недостаточно средств")
	}

	// 1. Предварительное списание (начало транзакции)
	from.Balance -= amount

	// 2. Сетевой вызов фиксации (подвержен хаосу Toxiproxy)
	if err := networkCall(); err != nil {
		// ROLLBACK: восстанавливаем баланс
		from.Balance += amount
		return fmt.Errorf("транзакция прервана сетевым сбоем, выполнен ROLLBACK: %w", err)
	}

	// 3. Зачисление получателю (успешный COMMIT)
	to.Balance += amount
	return nil
}

func (l *BankLedger) TotalSupply() int64 {
	l.mu.Lock()
	defer l.mu.Unlock()
	var sum int64
	for _, a := range l.accounts {
		sum += a.Balance
	}
	return sum
}

func TestFinancialIntegrityUnderNetworkChaos(t *testing.T) {
	ledger := NewBankLedger()
	initialSupply := ledger.TotalSupply()

	// Запускаем 20 параллельных транзакций перевода по 50 рублей
	var wg sync.WaitGroup
	var chaosTrigger atomic.Bool
	chaosTrigger.Store(true) // Включаем сбои сети

	for i := 0; i < 20; i++ {
		wg.Add(1)
		go func(iteration int) {
			defer wg.Done()
			ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
			defer cancel()

			_ = ledger.TransferFunds(ctx, "acc_alice", "acc_bob", 50, func() error {
				if iteration%2 == 0 && chaosTrigger.Load() {
					// Симуляция сетевого сбоя Toxiproxy (RST/Timeout)
					return errors.New("network toxic: connection reset by peer")
				}
				return nil
			})
		}(i)
	}

	wg.Wait()

	// ФИНАЛЬНАЯ ПРОВЕРКА ИНВАРИАНТА БИЗНЕСА:
	finalSupply := ledger.TotalSupply()
	if initialSupply != finalSupply {
		t.Fatalf("НАРУШЕНИЕ ЦЕЛОСТНОСТИ! Деньги исчезли или размножились: было %d, стало %d", initialSupply, finalSupply)
	}

	t.Logf("Инвариант сохранен идеально: TotalSupply=%d (Alice=%d, Bob=%d)",
		finalSupply, ledger.accounts["acc_alice"].Balance, ledger.accounts["acc_bob"].Balance)
}

func main() {
	fmt.Println("Тестирование целостности под хаос-нагрузкой в CI/CD успешно завершено")
}
"""
        }
    ],
    "under_the_hood": "В реальном CI/CD `testcontainers-go` взаимодействует с локальным сокетом `/var/run/docker.sock` через Docker Engine API. Он создает контейнеры со специальным лейблом `org.testcontainers.golang=true` и запускает сопутствующий контейнер Ryuk (`testcontainers/ryuk`), который слушает TCP-порт и гарантированно удаляет все созданные тестом контейнеры, сети и тома даже в случае аварийного сбоя тестов или прерывания CI-пайплайна по таймауту.",
    "pitfalls": [
        "Недоступность Docker daemon в среде CI (Docker-in-Docker / DinD): отсутствие проброса `/var/run/docker.sock` делает запуск Testcontainers невозможным.",
        "Утечка контейнеров при падении теста: всегда используйте `defer container.Terminate(ctx)` сразу после успешного запуска.",
        "Конкуренция за фиксированные порты: никогда не пробрасывайте порты контейнера в статические порты хоста (`5432:5432`). Позволяйте Docker назначать случайные порты (`MappedPort(ctx, \"5432\")`)."
    ],
    "bigtech_interview": "Почему транзакционные тесты под хаос-нагрузкой обязательно должны валидировать инварианты системы (Business Invariants), а не просто отсутствие паник в логах? В распределенной системе приложение может корректно вернуть код ошибки 500, но из-за некорректного роллбэка оставить базу данных в рассинхронизированном состоянии (деньги списались, но не начислились). Проверка глобальных инвариантов (Total Balance, Checksum) гарантирует истинную консистентность данных при любых авариях."
})

# Exercise 12
exercises.append({
    "num": 12,
    "title": "Модели нагрузки: Closed Workload vs Open Workload",
    "task": "Разберите различия моделей нагрузочного тестирования: Closed Workload (следующий запрос отправляется только после получения ответа на предыдущий — занижает реальную задержку при перегрузке) и Open Workload (запросы генерируются независимым распределением Пуассона независимо от состояния сервера). Объясните, почему для BigTech-систем необходима открытая модель.",
    "theory": r"""Фундаментальная классификация моделей генерации нагрузки:

1. **Closed Workload Model (Закрытая модель):**
   - Количество виртуальных пользователей (VUs / concurrency) строго фиксировано.
   - Цикл работы воркера: `Отправить запрос -> Дождаться ответа -> Выждать Think Time -> Повторить`.
   - **Главный дефект:** обратная связь по задержке (Latency Feedback Loop). Если тестируемый сервер начинает тормозить (например, задержка выросла с 10 мс до 10 000 мс из-за GC-паузы или блокировки БД), воркеры застревают в ожидании. В результате реальная частота отправки запросов (RPS) падает в 1000 раз! Сервер разгружается, а генератор нагрузки показывает ложное «благополучие», скрывая реальную катастрофу.

2. **Open Workload Model (Открытая модель):**
   - Поступление запросов не зависит от скорости ответов сервера.
   - Моделирует реальный интернет: миллионы независимых пользователей продолжают нажимать кнопки в мобильных приложениях независимо от того, тормозит бэкенд или нет.
   - Моменты генерации запросов подчиняются Пуассоновскому процессу (распределение Пуассона для числа событий и экспоненциальное распределение для интервалов между ними).
   - Если сервер начинает тормозить, входящие запросы накапливаются в очередях сервера, задержка растет до реальных сотен секунд, буферы взрываются — что точно отражает поведение продакшена под атакой или в пиковые часы (Black Friday).

Закон Литтла (Little's Law):
$$L = \lambda W$$
где $L$ — число запросов в системе (concurrency), $\lambda$ — частота поступления (RPS), $W$ — время ответа (latency). В закрытой системе зафиксировано $L$, поэтому при росте $W$ падает $\lambda$. В открытой системе зафиксировано $\lambda$, поэтому при росте $W$ растет $L$ вплоть до исчерпания памяти!""",
    "step_by_step": [
        "Спроектируйте сравнительный стенд с медленным сервером (задержка ответа 200 мс при емкости 2 одновременных запроса).",
        "Реализуйте закрытый генератор нагрузки (10 воркеров в синхронном цикле). Измерьте полученный RPS.",
        "Реализуйте открытый генератор нагрузки с пуассоновскими интервалами прибытия с целевой интенсивностью 50 RPS.",
        "Сравните метрики: покажите, как закрытая модель занизила нагрузку, а открытая модель выявила реальное переполнение очереди и отказ сервера."
    ],
    "code_blocks": [
        {
            "filename": "workload_models_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
	"math"
	"math/rand"
	"sync"
	"sync/atomic"
	"time"
)

// OverloadedServer симулирует узкое горлышко (максимум 2 параллельных запроса)
type OverloadedServer struct {
	sem       chan struct{}
	processed atomic.Int64
	rejected  atomic.Int64
}

func NewOverloadedServer() *OverloadedServer {
	return &OverloadedServer{
		sem: make(chan struct{}, 2), // Емкость всего 2
	}
}

func (s *OverloadedServer) Handle() bool {
	select {
	case s.sem <- struct{}{}:
		time.Sleep(50 * time.Millisecond) // Обработка занимает 50 мс
		<-s.sem
		s.processed.Add(1)
		return true
	default:
		s.rejected.Add(1)
		return false
	}
}

// RunClosedModel запускает N воркеров в закрытом цикле
func RunClosedModel(server *OverloadedServer, workers int, duration time.Duration) (int64, int64) {
	var wg sync.WaitGroup
	deadline := time.Now().Add(duration)

	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for time.Now().Before(deadline) {
				server.Handle() // Блокируется до завершения ответа!
			}
		}()
	}
	wg.Wait()
	return server.processed.Load(), server.rejected.Load()
}

// RunOpenModel генерирует запросы независимо от состояния сервера (Пуассоновский поток)
func RunOpenModel(server *OverloadedServer, targetRPS float64, duration time.Duration) (int64, int64) {
	deadline := time.Now().Add(duration)
	var wg sync.WaitGroup

	rng := rand.New(rand.NewSource(time.Now().UnixNano()))
	lambda := targetRPS

	for time.Now().Before(deadline) {
		// Экспоненциальный интервал между прибытиями: dt = -ln(U) / lambda
		u := rng.Float64()
		if u == 0 {
			u = 0.00001
		}
		dt := time.Duration(-math.Log(u) / lambda * float64(time.Second))
		time.Sleep(dt)

		wg.Add(1)
		go func() {
			defer wg.Done()
			server.Handle()
		}()
	}

	wg.Wait()
	return server.processed.Load(), server.rejected.Load()
}

func main() {
	duration := 1 * time.Second

	// 1. Тест Closed Workload
	srvClosed := NewOverloadedServer()
	pClosed, rClosed := RunClosedModel(srvClosed, 5, duration)
	fmt.Println("=== CLOSED WORKLOAD MODEL (5 воркеров) ===")
	fmt.Printf("Обработано: %d, Отброшено: %d (Сервер не перегружен, но нагрузка искусственно замедлилась)\n", pClosed, rClosed)

	// 2. Тест Open Workload
	srvOpen := NewOverloadedServer()
	pOpen, rOpen := RunOpenModel(srvOpen, 100.0, duration) // Пытаемся подать 100 RPS
	fmt.Println("\n=== OPEN WORKLOAD MODEL (100 целевых RPS) ===")
	fmt.Printf("Обработано: %d, Отброшено: %d (Реалистичное отражение перегрузки в пик!)\n", pOpen, rOpen)
}
"""
        }
    ],
    "under_the_hood": "В теории очередей Пуассоновский процесс обладает свойством отсутствия памяти (Memorylessness): вероятность появления события в следующий момент времени зависит исключительно от длины интервала времени и абсолютно независима от того, сколько запросов уже ожидает в очереди сервера. Генерация экспоненциальных интервалов через обратное преобразование распределения (Inverse Transform Sampling: $X = -\\frac{\\ln(1-U)}{\\lambda}$) формирует реалистичный трафик с естественными микро-всплесками (Burstiness).",
    "pitfalls": [
        "Использование закрытой модели нагрузки (Apache Bench, базовый JMeter) для тестирования масштабируемости: инструмент показывает ложный рост задержки без отказов, создавая иллюзию стабильности.",
        "Неконтролируемое порождение горутин в открытой модели: если сервер завис наглухо, открытый генератор создаст миллион горутин и упадет по памяти (OOM) на стороне нагрузочной станции.",
        "Игнорирование ограничений сетевого стека клиента (исчерпание эфемерных портов TCP)."
    ],
    "bigtech_interview": "Почему BigTech компании (Яндекс, Netflix, Google) для нагрузочного тестирования используют открытые генераторы нагрузки (Yandex Tank / Pandora, Locust, k6, Gatling)? Потому что в реальной жизни внешние клиенты не договариваются между собой притормозить отправку запросов, когда бэкенд начинает деградировать. Открытая модель позволяет протестировать поведение очередей ядра Linux, настройки Backpressure, вытеснение нагрузки (Load Shedding) и механизмы деградации функционала под реальным давлением."
})

# Exercise 13
exercises.append({
    "num": 13,
    "title": "Проблема скоординированного пропуска (Coordinated Omission)",
    "task": "Изучите явление Coordinated Omission (открытое Гилом Тене): если система зависла на 5 секунд во время GC-паузы, закрытый нагрузочный генератор также зависает и регистрирует только один медленный запрос вместо тысяч запросов, которые должны были прийти за это время. Продемонстрируйте этот эффект на простом скрипте.",
    "theory": r"""Феномен скоординированного пропуска (Coordinated Omission) — одна из самых опасных и коварных ошибок в методологии нагрузочного тестирования, впервые детально описанная создателем Azul Systems Гилом Тене (Gil Tene).

Суть проблемы:
Представьте систему, которая обрабатывает запросы за 1 мс. Мы хотим протестировать её под нагрузкой 100 RPS (1 запрос каждые 10 мс).
В момент времени $T=100$ мс в системе происходит пауза Stop-The-World GC (или зависание диска) длительностью **1000 мс**.

Что происходит в наивном нагрузочном генераторе:
1. Запрос №10 отправляется в $T=100$ мс и зависает на 1000 мс.
2. Генератор блокируется в ожидании ответа до $T=1100$ мс.
3. В статистику записывается ровно **1 медленный запрос** с задержкой 1000 мс.
4. Все последующие запросы снова выполняются за 1 мс.
5. Итоговый отчет показывает: 99 запросов по 1 мс, 1 запрос по 1000 мс. Перцентиль p99 = 1 мс! Кажется, что всё идеально!

Что произошло на самом деле в реальном мире:
- За время 1000-миллисекундной паузы должны были прийти **100 запросов**!
- Все 100 пользователей стояли в очереди и ждали: первый ждал 1000 мс, второй 990 мс, третий 980 мс... сотый ждал 10 мс.
- Наивный генератор скоординированно **пропустил** регистрацию этих 100 задержанных запросов!
- Реальный перцентиль p99 должен был составить около 990 мс, а не 1 мс!

Решение (Coordinated Omission Correction):
Для каждого запроса фиксируется запланированное время старта (`Scheduled Time`). Задержка рассчитывается не как `End - ActualStart`, а как:
$$\text{Full Latency} = \text{ActualEnd} - \text{ScheduledStart}$$
А если задержка превысила интервал квантования, генератор ретроспективно добавляет синтетические виртуальные сэмплы для всех пропущенных временных слотов.""",
    "step_by_step": [
        "Смоделируйте сервер, который работает с задержкой 1 мс, но на 500 мс зависает в паузе.",
        "Реализуйте наивный сборщик метрик задержки, рассчитывающий `Latency = time.Since(reqStart)`.",
        "Реализуйте корректирующий сборщик (Coordinated Omission Aware), отслеживающий плановое расписание генерации (`scheduledTime`) и восстанавливающий пропущенные сэмплы.",
        "Сравните перцентили p99 обоих методов: покажите катастрофическое расхождение результатов."
    ],
    "code_blocks": [
        {
            "filename": "coordinated_omission_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"sort"
	"sync"
	"time"
)

type LatencyStats struct {
	mu      sync.Mutex
	samples []time.Duration
}

func (s *LatencyStats) Record(d time.Duration) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.samples = append(s.samples, d)
}

func (s *LatencyStats) Percentile(p float64) time.Duration {
	s.mu.Lock()
	defer s.mu.Unlock()
	if len(s.samples) == 0 {
		return 0
	}
	sorted := make([]time.Duration, len(s.samples))
	copy(sorted, s.samples)
	sort.Slice(sorted, func(i, j int) bool { return sorted[i] < sorted[j] })

	idx := int(float64(len(sorted)-1) * p)
	return sorted[idx]
}

func main() {
	interval := 10 * time.Millisecond // Целевой ритм: 100 RPS
	totalRequests := 100

	naiveStats := &LatencyStats{}
	correctedStats := &LatencyStats{}

	// Симулируем запуск теста
	startTime := time.Now()
	for i := 0; i < totalRequests; i++ {
		scheduledTime := startTime.Add(time.Duration(i) * interval)
		now := time.Now()
		if now.Before(scheduledTime) {
			time.Sleep(scheduledTime.Sub(now))
		}

		// Симуляция работы: 50-й запрос зависает на 300 мс (GC пауза)
		actualStart := time.Now()
		if i == 50 {
			time.Sleep(300 * time.Millisecond)
		} else {
			time.Sleep(1 * time.Millisecond)
		}
		actualEnd := time.Now()

		// 1. Наивный расчет
		naiveLatency := actualEnd.Sub(actualStart)
		naiveStats.Record(naiveLatency)

		// 2. Расчет с коррекцией Coordinated Omission
		fullLatency := actualEnd.Sub(scheduledTime)
		correctedStats.Record(fullLatency)

		// Если пауза превысила интервал, восстанавливаем пропущенные сэмплы
		if fullLatency > interval {
			missed := fullLatency - interval
			for missed > 0 {
				correctedStats.Record(missed)
				missed -= interval
			}
		}
	}

	fmt.Println("=== СРАВНЕНИЕ РЕЗУЛЬТАТОВ НАГРУЗОЧНОГО ТЕСТА ===")
	fmt.Printf("Наивный p50:   %v\n", naiveStats.Percentile(0.50))
	fmt.Printf("Наивный p90:   %v\n", naiveStats.Percentile(0.90))
	fmt.Printf("Наивный p99:   %v (ЛОЖНОЕ БЛАГОПОЛУЧИЕ!)\n", naiveStats.Percentile(0.99))
	fmt.Println("-----------------------------------------------")
	fmt.Printf("Честный p50:   %v\n", correctedStats.Percentile(0.50))
	fmt.Printf("Честный p90:   %v\n", correctedStats.Percentile(0.90))
	fmt.Printf("Честный p99:   %v (РЕАЛЬНАЯ ЗАДЕРЖКА КЛИЕНТОВ!)\n", correctedStats.Percentile(0.99))
}
"""
        }
    ],
    "under_the_hood": "Coordinated Omission возникает из-за неявной координации между генератором нагрузки и тестируемой системой. Когда сервер задерживает ответ, генератор задерживает отправку следующего запроса. Разделение понятий `Service Time` (чистое время обработки сервером) и `Response Time` (время с точки зрения пользователя с учетом ожидания в очереди отправки) позволяет вскрыть истинную деградацию сервиса.",
    "pitfalls": [
        "Доверие отчетам инструментов, подверженных Coordinated Omission (Apache Benchmark `ab`, ранние версии wrk): данные p99 в них занижены в десятки раз.",
        "Сортировка среза миллионов `time.Duration` в оперативной памяти для вычисления перцентилей: приводит к огромным паузам GC в самом генераторе нагрузки.",
        "Неучет сетевого времени ожидания в TCP-буферах клиента."
    ],
    "bigtech_interview": "Что такое Coordinated Omission и как его обнаружить при аудите нагрузочных тестов? Это феномен, при котором задержка или зависание тестируемого сервиса приводит к непреднамеренному снижению скорости генерации новых запросов тестовым инструментом, в результате чего в выборку не попадают те запросы, которые должны были прийти во время паузы. Обнаружить его можно, сравнив запланированное расписание генерации с фактическим временем отправки запросов: если между запросами есть аномальные интервалы, тест подвержен скоординированному пропуску."
})

# Exercise 14
exercises.append({
    "num": 14,
    "title": "Разработка собственного открытого генератора нагрузки на Go",
    "task": "Напишите генератор нагрузки на Go, реализующий модель Open Workload: использование таймера с плавающим интервалом (пуассоновский процесс через `rand.ExpFloat64()`) для независимой отправки HTTP-запросов с заданной интенсивностью (Target RPS) независимо от задержки ответов сервера.",
    "theory": r"""Проектирование надежного генератора нагрузки корпоративного уровня на языке Go требует совмещения трех архитектурных элементов:
1. **Независимый диспетчер расписания (Schedule Dispatcher):**
   Генерирует события отправки запросов строго по заданному закону распределения (Пуассоновский процесс).
2. **Неблокирующий пул горутин (Non-blocking Worker Pool):**
   Диспетчер не ждет ответа сервера; он передает задачу в пул горутин или запускает легковесную горутину на запрос.
3. **Безопасное ограничение параллелизма (Concurrency Safeguard):**
   Если целевой сервер завис, количество одновременных горутин может расти без ограничений. Генератор должен иметь настраиваемый предел `MaxConcurrency`. При достижении предела запросы регистрируются как отброшенные из-за перегрузки (`ClientShedded`), предотвращая крах самого генератора.

Математика Пуассоновского интервала:
Интервал между событиями $\Delta t$ задается экспоненциальным распределением с параметром $\lambda$ (интенсивность запросов в секунду):
$$\Delta t = \frac{\text{ExpFloat64}()}{\lambda} \text{ секунд}$$""",
    "step_by_step": [
        "Спроектируйте интерфейс задачи нагрузки `LoadTask` и структуру конфигурации генератора `LoadConfig`.",
        "Реализуйте математический генератор пауз по Пуассону с использованием `rand.ExpFloat64()`.",
        "Реализуйте диспетчер `OpenLoadGenerator`, распределяющий запросы независимо от времени их выполнения.",
        "Соберите метрики: общее число сгенерированных, успешно выполненных и отброшенных по перегрузке запросов."
    ],
    "code_blocks": [
        {
            "filename": "open_load_generator.go",
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

type LoadResult struct {
	Duration time.Duration
	Err      error
}

type OpenLoadGenerator struct {
	targetRPS      float64
	maxConcurrency int
	task           func(ctx context.Context) error

	sentCount      atomic.Int64
	successCount   atomic.Int64
	errorCount     atomic.Int64
	droppedCount   atomic.Int64
	activeWorkers  atomic.Int64
}

func NewOpenLoadGenerator(targetRPS float64, maxConcurrency int, task func(context.Context) error) *OpenLoadGenerator {
	return &OpenLoadGenerator{
		targetRPS:      targetRPS,
		maxConcurrency: maxConcurrency,
		task:           task,
	}
}

func (g *OpenLoadGenerator) Run(ctx context.Context, duration time.Duration) {
	deadline := time.Now().Add(duration)
	rng := rand.New(rand.NewSource(time.Now().UnixNano()))
	var wg sync.WaitGroup

	for {
		now := time.Now()
		if now.After(deadline) || ctx.Err() != nil {
			break
		}

		// Вычисляем экспоненциальный интервал до следующего запроса
		deltaSec := rng.ExpFloat64() / g.targetRPS
		sleepDuration := time.Duration(deltaSec * float64(time.Second))

		select {
		case <-ctx.Done():
			break
		case <-time.After(sleepDuration):
		}

		// Проверяем лимит параллелизма (Защита от OOM генератора)
		if int(g.activeWorkers.Load()) >= g.maxConcurrency {
			g.droppedCount.Add(1)
			continue
		}

		g.sentCount.Add(1)
		g.activeWorkers.Add(1)
		wg.Add(1)

		go func() {
			defer func() {
				g.activeWorkers.Add(-1)
				wg.Done()
			}()

			reqCtx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()

			if err := g.task(reqCtx); err != nil {
				g.errorCount.Add(1)
			} else {
				g.successCount.Add(1)
			}
		}()
	}

	wg.Wait()
}

func main() {
	// Имитация тестируемого сервиса со средней задержкой 10 мс
	targetService := func(ctx context.Context) error {
		time.Sleep(10 * time.Millisecond)
		return nil
	}

	targetRPS := 200.0 // 200 запросов в секунду
	maxConcurrency := 50
	gen := NewOpenLoadGenerator(targetRPS, maxConcurrency, targetService)

	fmt.Printf("Запуск открытого генератора нагрузки: %.0f RPS в течение 1 секунды...\n", targetRPS)
	ctx := context.Background()
	start := time.Now()
	gen.Run(ctx, 1*time.Second)
	elapsed := time.Since(start)

	fmt.Println("=== СТАТИСТИКА ОТКРЫТОЙ НАГРУЗКИ ===")
	fmt.Printf("Длительность:          %v\n", elapsed)
	fmt.Printf("Запросов отправлено:   %d\n", gen.sentCount.Load())
	fmt.Printf("Фактический RPS:       %.1f\n", float64(gen.sentCount.Load())/elapsed.Seconds())
	fmt.Printf("Успешно выполнено:     %d\n", gen.successCount.Load())
	fmt.Printf("Ошибок сервиса:        %d\n", gen.errorCount.Load())
	fmt.Printf("Отброшено генератором: %d\n", gen.droppedCount.Load())
}
"""
        }
    ],
    "under_the_hood": "В рантайме Go функция `time.After(sleepDuration)` регистрирует таймер в системном квадранте таймеров планировщика рантайма. Использование `rand.ExpFloat64()` из стандартного пакета `math/rand` основано на алгоритме Зиккурата (Ziggurat algorithm), выполняющем генерацию случайных чисел с экспоненциальным законом за считанные наносекунды без тяжелых тригонометрических вычислений.",
    "pitfalls": [
        "Использование глобального `rand.Float64()`: внутри стандартного пакета `math/rand` глобальный генератор защищен мьютексом, который становится точкой жесточайшей конкуренции ядер CPU при высоких RPS. Необходимо создавать локальный экземпляр `rand.New` на горутину.",
        "Утечка ресурсов при частых `time.After`: в цикле высокой интенсивности таймеры накапливаются в памяти до момента срабатывания. Для ультра-высоких нагрузок используют `time.NewTimer` с явным сбросом `Reset()`.",
        "Отсутствие ограничения `maxConcurrency`: зависший бэкенд вызовет взрывное порождение миллионов горутин генератора."
    ],
    "bigtech_interview": "Как откалибровать нагрузочный генератор, чтобы убедиться, что он сам не является узким местом теста? Проводят тест «на петлю» (Loopback Test): генератор направляют на локальный мок-сервер с фиксированной задержкой 0 мс. Проверяют: 1) Профиль использования CPU генератора (не должен превышать 60-70%); 2) Отсутствие аллокаций памяти и пауз GC в генераторе; 3) Стабильность частоты отправки запросов (фактический RPS должен строго совпадать с Target RPS с погрешностью < 1%)."
})

# Exercise 15
exercises.append({
    "num": 15,
    "title": "Высокопроизводительный пул виртуальных пользователей (VUs)",
    "task": "Оптимизируйте генератор нагрузки для генерации 100 000 RPS с одной машины: пул легковесных горутин, использование `http.Transport` с тюнингом `MaxIdleConns: 10000` и `MaxIdleConnsPerHost: 10000`, отключение лишних аллокаций памяти (`b.ReportAllocs()`).",
    "theory": r"""Генерация сверхвысокой нагрузки (от 50 000 до 100 000+ RPS) с одной физической машины или контейнера упирается в ограничения стандартного HTTP-клиента Go и сетевого стека ядра Linux.

Узкие места и их устранение:
1. **Дефолтные настройки `http.Transport`:**
   По умолчанию `http.DefaultTransport` имеет `MaxIdleConnsPerHost: 2`. При попытке подать 10 000 RPS на один хост клиент Go будет сохранять в пуле только 2 соединения, а остальные 9 998 соединений закрывать и открывать заново на каждый запрос! Это приводит к шторму TCP 3-way handshake и мгновенному исчерпанию эфемерных портов (`TIME_WAIT`, `cannot assign requested address`).
   - Решение: `MaxIdleConns: 20000`, `MaxIdleConnsPerHost: 20000`, `IdleConnTimeout: 90 * time.Second`.
2. **Аллокации памяти в цикле отправки:**
   Чтение тела ответа через `io.ReadAll(resp.Body)` аллоцирует новые байтовые срезы на каждый запрос. 100k RPS приведут к выделению гигабайтов памяти в секунду и параличу сборщика мусора Go (GC).
   - Решение: использование `io.Copy(io.Discard, resp.Body)` и пулов буферов `sync.Pool`.
3. **Отключение HTTP Keep-Alive и компрессии:**
   Включение `DisableCompression: true` снимает с CPU лишнюю нагрузку по разархивированию gzip.""",
    "step_by_step": [
        "Настройте кастомный экземпляр `http.Transport` с экстремальным тюнингом пулов соединений.",
        "Реализуйте оптимизированный воркер, выполняющий сброс тела ответа в `io.Discard` без аллокаций памяти.",
        "Напишите бенчмарк-тест на чистом Go, демонстрирующий генерацию запросов с нулевыми аллокациями в горячем цикле.",
        "Проанализируйте достигнутую производительность и потребление памяти."
    ],
    "code_blocks": [
        {
            "filename": "ultra_load_pool_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

// CreateOptimizedHTTPClient создает высокоскоростной клиент для стресс-тестирования
func CreateOptimizedHTTPClient() *http.Client {
	dialer := &net.Dialer{
		Timeout:   2 * time.Second,
		KeepAlive: 60 * time.Second,
	}

	transport := &http.Transport{
		Proxy:                 nil, // Отключаем поиск системного прокси
		DialContext:           dialer.DialContext,
		ForceAttemptHTTP2:     false, // Для чистого стресс-тестирования HTTP/1.1
		MaxIdleConns:          20000,
		MaxIdleConnsPerHost:   20000, // КРИТИЧНО для одного целевого хоста!
		MaxConnsPerHost:       0,     // Без ограничений
		IdleConnTimeout:       90 * time.Second,
		TLSHandshakeTimeout:   2 * time.Second,
		ExpectContinueTimeout: 1 * time.Second,
		DisableCompression:    true, // Экономим CPU генератора
	}

	return &http.Client{
		Transport: transport,
		Timeout:   3 * time.Second,
	}
}

// ExecuteFastRequest выполняет запрос с гарантией нулевых утечек памяти
func ExecuteFastRequest(client *http.Client, url string) error {
	req, err := http.NewRequestWithContext(context.Background(), http.MethodGet, url, nil)
	if err != nil {
		return err
	}

	resp, err := client.Do(req)
	if err != nil {
		return err
	}

	// Эффективно вычитываем и утилизируем тело ответа без аллокаций
	_, _ = io.Copy(io.Discard, resp.Body)
	_ = resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("unexpected status: %d", resp.StatusCode)
	}
	return nil
}

func BenchmarkHighSpeedClient(b *testing.B) {
	// Локальный ультра-быстрый тестовый сервер
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("OK"))
	}))
	defer server.Close()

	client := CreateOptimizedHTTPClient()

	b.ResetTimer()
	b.ReportAllocs()

	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			if err := ExecuteFastRequest(client, server.URL); err != nil {
				b.Errorf("request error: %v", err)
			}
		}
	})
}

func main() {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("FAST_OK"))
	}))
	defer server.Close()

	client := CreateOptimizedHTTPClient()
	concurrency := 50
	totalRequests := 5000
	var completed atomic.Int64
	var wg sync.WaitGroup

	start := time.Now()
	reqPerWorker := totalRequests / concurrency

	for i := 0; i < concurrency; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < reqPerWorker; j++ {
				if err := ExecuteFastRequest(client, server.URL); err == nil {
					completed.Add(1)
				}
			}
		}()
	}

	wg.Wait()
	duration := time.Since(start)
	rps := float64(completed.Load()) / duration.Seconds()

	fmt.Println("=== ТЕСТ ВЫСОКОПРОИЗВОДИТЕЛЬНОГО ПУЛА VUs ===")
	fmt.Printf("Выполнено запросов: %d за %v\n", completed.Load(), duration)
	fmt.Printf("Скорость генерации: %.0f RPS на локальном хосте\n", rps)
}
"""
        }
    ],
    "under_the_hood": "По умолчанию `http.Transport` использует внутренний хэш-мап открытых соединений `idleConn map[connectMethodKey][]*persistConn`. При значении `MaxIdleConnsPerHost: 2` рантайм Go при закрытии тела ответа (`resp.Body.Close()`) видит, что список уже содержит 2 элемента, и вызывает `pconn.close()`, посылая TCP FIN. При повторном запросе инициируется новый `connect()` и аллокация `persistConn`. Тюнинг `MaxIdleConnsPerHost` держит соединения открытыми, снижая накладные расходы до чистой передачи байт по уже прогретым сокетам.",
    "pitfalls": [
        "Не вычитывать тело ответа перед закрытием (`resp.Body.Close()`): если тело ответа не вычитано до конца (`io.Copy(io.Discard, resp.Body)`), Go не может переиспользовать существующее TCP-соединение в Keep-Alive пуле и принудительно его закрывает.",
        "Утечка файловых дескрипторов из-за отсутствия `resp.Body.Close()`.",
        "Превышение лимита открытых сокетов ОС (`ulimit -n 65535`): необходимо поднимать лимиты файловых дескрипторов перед проведением высокоскоростных тестов."
    ],
    "bigtech_interview": "Почему при проведении масштабных нагрузочных тестов на один целевой домен стандартный Go HTTP-клиент без тюнинга быстро начинает выдавать ошибку `bind: address already in use`? Потому что при дефолтном `MaxIdleConnsPerHost: 2` все остальные соединения закрываются клиентом. Закрытые TCP-соединения остаются в состоянии ядра `TIME_WAIT` на протяжении 60 секунд. При высоком RPS пул из ~60 000 доступных локальных эфемерных портов полностью исчерпывается за считанные секунды."
})

def test_all():
    print(f"Generated {len(exercises)} exercises in part 1")
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
    print("All Part 1 code blocks verified with gofmt -e!")
    return True

if __name__ == '__main__':
    if test_all():
        out_path = os.path.join(os.path.dirname(__file__), 'ch89_p1.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(exercises, f, ensure_ascii=False, indent=2)
        print(f"Wrote {out_path} successfully!")
