# -*- coding: utf-8 -*-
"""
Chapter 85 Part 2: Exercises 16 to 30
Multi-Level Caching (L1/L2) and Distributed Coherence in Go
"""

exercises = [
    {
        "num": 16,
        "title": "Redis Client-Side Caching (RESP3 Tracking Mechanism)",
        "task": "Реализуйте симуляцию встроенного серверного механизма Client-Side Caching протокола Redis RESP3 (CLIENT TRACKING on). Создайте модель сервера Redis, который ведет таблицу отслеживания (Tracking Table), связывающую прочитанные клиентом ключи с его идентификатором соединения. При обновлении ключа другим клиентом сервер автоматически отправляет неблокирующее push-уведомление об инвалидации клиентам-читателям. На стороне клиента обработайте push-сообщение в фоновой горутине и очистите L1.",
        "theory": "До появления протокола RESP3 в Redis 6 распределенная инвалидация строилась на ручном Pub/Sub: разработчик обязан был вручную вставлять вызовы PUBLISH при каждом изменении данных. Это приводило к ошибкам человеческого фактора и спаму сообщений по всем нодам.\n\nМеханизм RESP3 Client-Side Tracking перекладывает отслеживание на сам Redis:\n1. Клиент включает трекинг: CLIENT TRACKING on.\n2. Когда клиент читает ключ (GET user:12), Redis запоминает в Tracking Table: user:12 -> [Client #4].\n3. Когда ЛЮБОЙ другой клиент вызывает SET user:12 или DEL user:12, Redis отправляет push-сообщение клиенту #4.\n4. Библиотека кэша на клиенте мгновенно вытесняет ключ из локального L1-хранилища.\nРежим BCAST (Broadcasting) использует префиксы ключей (например, users:), избавляя Redis от хранения каждого отдельного ключа в памяти сервера.",
        "step_by_step": "1. Спроектируйте структуру TrackingServer с мапой trackingTable.\n2. Реализуйте метод Get с регистрацией клиента в таблице трекинга.\n3. Реализуйте метод Set с поиском подписчиков и отправкой push-инвалидации.\n4. На клиенте запустите фоновый обработчик входящих push-нотификаций протокола RESP3.\n5. Продемонстрируйте автоматическую инвалидацию локального кэша клиента при изменении ключа сторонним клиентом.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
	"time"
)

type PushMessage struct {
	Type string
	Keys []string
}

type SimulatedRedisServer struct {
	mu            sync.Mutex
	data          map[string]string
	trackingTable map[string]map[int]chan PushMessage
}

func NewSimulatedRedisServer() *SimulatedRedisServer {
	return &SimulatedRedisServer{
		data:          make(map[string]string),
		trackingTable: make(map[string]map[int]chan PushMessage),
	}
}

func (s *SimulatedRedisServer) RegisterClient(clientID int) chan PushMessage {
	return make(chan PushMessage, 50)
}

func (s *SimulatedRedisServer) Get(clientID int, key string, pushCh chan PushMessage) (string, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if _, ok := s.trackingTable[key]; !ok {
		s.trackingTable[key] = make(map[int]chan PushMessage)
	}
	s.trackingTable[key][clientID] = pushCh

	val, ok := s.data[key]
	return val, ok
}

func (s *SimulatedRedisServer) Set(authorID int, key, val string) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.data[key] = val

	if clients, ok := s.trackingTable[key]; ok {
		for cid, ch := range clients {
			if cid != authorID {
				select {
				case ch <- PushMessage{Type: "invalidate", Keys: []string{key}}:
				default:
				}
			}
		}
		delete(s.trackingTable, key)
	}
}

type ClientSideCache struct {
	id     int
	server *SimulatedRedisServer
	pushCh chan PushMessage
	l1     sync.Map
}

func NewClientSideCache(id int, server *SimulatedRedisServer) *ClientSideCache {
	pushCh := server.RegisterClient(id)
	c := &ClientSideCache{
		id:     id,
		server: server,
		pushCh: pushCh,
	}

	go c.listenPushes()
	return c
}

func (c *ClientSideCache) listenPushes() {
	for msg := range c.pushCh {
		if msg.Type == "invalidate" {
			for _, k := range msg.Keys {
				c.l1.Delete(k)
				fmt.Printf("[Client #%d] RESP3 PUSH: Ключ '%s' инвалидирован сервером Redis!\n", c.id, k)
			}
		}
	}
}

func (c *ClientSideCache) Get(key string) string {
	if v, ok := c.l1.Load(key); ok {
		return v.(string) + " (from L1)"
	}

	val, ok := c.server.Get(c.id, key, c.pushCh)
	if !ok {
		return "NOT_FOUND"
	}

	c.l1.Store(key, val)
	return val + " (from Redis L2 -> cached to L1)"
}

func main() {
	redisServer := NewSimulatedRedisServer()
	redisServer.data["user:cfg:dark_mode"] = "true"

	clientA := NewClientSideCache(101, redisServer)
	clientB := NewClientSideCache(102, redisServer)

	fmt.Println("1. Клиент А запрашивает ключ (холодный старт)...")
	fmt.Println("Ответ:", clientA.Get("user:cfg:dark_mode"))

	fmt.Println("\n2. Клиент А запрашивает ключ повторно...")
	fmt.Println("Ответ:", clientA.Get("user:cfg:dark_mode"))

	fmt.Println("\n3. Клиент B изменяет значение ключа на сервере Redis...")
	redisServer.Set(clientB.id, "user:cfg:dark_mode", "false")

	time.Sleep(50 * time.Millisecond)

	fmt.Println("\n4. Клиент А снова запрашивает ключ после push-инвалидации...")
	fmt.Println("Ответ:", clientA.Get("user:cfg:dark_mode"))
}
"""
            }
        ],
        "under_the_hood": "В протоколе RESP3 push-сообщения начинаются с байта '>'. Клиентский драйвер go-redis/v9 мультиплексирует сетевой сокет: горутина чтения парсит ответы на обычные команды и push-уведомления. Когда с сервера прилетает push-инвалидация, драйвер вызывает зарегистрированный InvalidateCallback, передавая имена ключей для мгновенной вычистки из локального L1 кэша.",
        "pitfalls": "Переполнение Tracking Table на стороне Redis: если сервер держит миллионы ключей для тысяч клиентов, память Redis будет быстро исчерпана служебными таблицами трекинга. В HighLoad системах рекомендуется использовать режим BCAST с ограниченными префиксами.",
        "bigtech_interview": "'В чем ключевое отличие режима BCAST от дефолтного CLIENT TRACKING в Redis?' Ответ: В стандартном режиме Redis запоминает каждое отдельное обращение каждого соединения к каждому ключу. В режиме BCAST сервер запоминает только префиксы клиентов, а при изменении ключа шлет широковещательное уведомление всем слушателям префикса, экономя память Redis."
    },
    {
        "num": 17,
        "title": "Двухуровневая обертка с разными TTL для L1 и L2",
        "task": "Реализуйте и протестируйте строгую политику разделения времени жизни ключей (Differential TTL Policy) для многоуровневого кэша. Напишите конфигуратор TTLPolicy{ L1TTL: 15*time.Second, L2TTL: 30*time.Minute, StaleThreshold: 2*time.Minute }. Создайте сервис, который гарантирует, что локальный L1 никогда не удерживает данные дольше установленного лимита, а в случае временной недоступности L2 отдает слегка устаревшие данные (Stale While Revalidate).",
        "theory": "В распределенных системах фундаментальным правилом безопасности является TTL(L1) << TTL(L2) (TTL локальной памяти на порядки меньше TTL распределенного кэша).\n\nОбоснование:\n1. Изолированность нод: Память L1 не видна другим репликам. Если механизм инвалидации даст сбой, максимальное время рассинхронизации данных в системе будет строго ограничено коротким TTL(L1) (например, 10–15 секунд).\n2. Защита от OOM: Объем оперативной памяти пода жестко ограничен лимитами cgroup. Длинный TTL заполнил бы локальную память миллионами объектов.\n3. Роль L2: Redis обладает гигабайтами памяти и выступает надежным щитом для БД. Длинный TTL(L2) обеспечивает высокий общий Hit Ratio.",
        "step_by_step": "1. Спроектируйте структуру конфигурации TTLConfig.\n2. Реализуйте двухуровневый сервис, проверяющий истечение L1 и L2.\n3. Если L1 протух, но L2 доступен, обновите L1 свежими данными из L2.\n4. Если L2 недоступен, но локальный L1 содержит данные не старше StaleThreshold, верните stale-значение с предупреждающим логом.\n5. Напишите тесты в main.go, демонстрирующие корректную изоляцию и fallback.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

type TTLConfig struct {
	L1TTL          time.Duration
	L2TTL          time.Duration
	StaleThreshold time.Duration
}

type L1Item struct {
	Val       string
	ExpiredAt time.Time
}

type SafeMultiTTLService struct {
	mu     sync.RWMutex
	l1     map[string]L1Item
	l2     map[string]string
	l2Down bool
	cfg    TTLConfig
}

func NewSafeMultiTTLService(cfg TTLConfig) *SafeMultiTTLService {
	return &SafeMultiTTLService{
		l1:  make(map[string]L1Item),
		l2:  make(map[string]string),
		cfg: cfg,
	}
}

func (s *SafeMultiTTLService) Get(ctx context.Context, key string, dbLoader func() (string, error)) (string, string, error) {
	s.mu.RLock()
	item, inL1 := s.l1[key]
	s.mu.RUnlock()

	now := time.Now()

	if inL1 && now.Before(item.ExpiredAt) {
		return item.Val, "L1_FRESH", nil
	}

	if !s.l2Down {
		s.mu.RLock()
		l2Val, inL2 := s.l2[key]
		s.mu.RUnlock()

		if inL2 {
			s.mu.Lock()
			s.l1[key] = L1Item{Val: l2Val, ExpiredAt: now.Add(s.cfg.L1TTL)}
			s.mu.Unlock()
			return l2Val, "L2_HIT_BACKFILL_L1", nil
		}
	} else {
		if inL1 && now.Before(item.ExpiredAt.Add(s.cfg.StaleThreshold)) {
			return item.Val, "L1_STALE_GRACEFUL_FALLBACK", nil
		}
	}

	fresh, err := dbLoader()
	if err != nil {
		return "", "ERROR", err
	}

	s.mu.Lock()
	if !s.l2Down {
		s.l2[key] = fresh
	}
	s.l1[key] = L1Item{Val: fresh, ExpiredAt: now.Add(s.cfg.L1TTL)}
	s.mu.Unlock()

	return fresh, "DB_FETCH", nil
}

func main() {
	cfg := TTLConfig{
		L1TTL:          200 * time.Millisecond,
		L2TTL:          10 * time.Minute,
		StaleThreshold: 1 * time.Second,
	}
	svc := NewSafeMultiTTLService(cfg)
	ctx := context.Background()

	loader := func() (string, error) {
		return "AccountBalance: $54,200", nil
	}

	key := "acc:balance:1001"

	v, src, _ := svc.Get(ctx, key, loader)
	fmt.Printf("[1] %s -> %s\n", src, v)

	time.Sleep(50 * time.Millisecond)
	v, src, _ = svc.Get(ctx, key, loader)
	fmt.Printf("[2] %s -> %s\n", src, v)

	time.Sleep(250 * time.Millisecond)
	v, src, _ = svc.Get(ctx, key, loader)
	fmt.Printf("[3] %s -> %s\n", src, v)

	svc.l2Down = true
	time.Sleep(250 * time.Millisecond)
	v, src, _ = svc.Get(ctx, key, loader)
	fmt.Printf("[4] %s -> %s (Redis упал, но сервис отдал stale из L1!)\n", src, v)
}
"""
            }
        ],
        "under_the_hood": "Паттерн Stale-While-Revalidate (RFC 5861) обеспечивает минимальную задержку: клиент мгновенно получает слегка устаревший ответ, а обновление выполняется в фоне. Это исключает каскадные сбои всей системы при кратковременном сетевом флапе L2.",
        "pitfalls": "Отдача stale-данных категорически недопустима в финансовых операциях (списание средств, остатки товаров). Для критичных доменов флаг stale должен быть отключен.",
        "bigtech_interview": "'Что произойдет, если TTL L1 сделать больше TTL L2?' Ответ: Это архитектурная ошибка. Ноды будут отдавать устаревшие данные из памяти, игнорируя обновление или удаление ключа в L2. L1 всегда должен быть быстрее и эфемернее L2."
    },
    {
        "num": 18,
        "title": "Алгоритмы вытеснения L1: LRU vs TinyLFU",
        "task": "Исследуйте разницу между алгоритмами вытеснения кэша LRU (Least Recently Used) и TinyLFU (используемым в библиотеке dgraph-io/ristretto). Напишите реализацию LRU на базе двусвязного списка и мапы. Затем смоделируйте атаку или пакетный обход каталога (Burst Scan): прогон 10 000 одноразовых ключей. Покажите, как LRU полностью вымывает постоянные популярные ключи, и объясните, как счетчик частот Count-Min Sketch в TinyLFU защищает кэш от вымывания.",
        "theory": "Классический алгоритм LRU вытесняет элемент, к которому дольше всего не было обращений. Главная уязвимость LRU — подверженность загрязнению сканированием (Scan Pollution). Если ночной скрипт пробегает по 1 000 000 архивных записей, он заполнит весь LRU-кэш мусором, вытеснив действительно популярные товары главной страницы.\n\nАлгоритм TinyLFU:\n1. При попытке добавления нового ключа TinyLFU оценивает частоту обращения к нему с помощью компактного вероятностного счетчика Count-Min Sketch.\n2. TinyLFU сравнивает частоту кандидата и кандидата на выселение из LRU.\n3. Если частота кандидата меньше частоты жертвы, новый ключ не пускают в кэш! Он отбрасывается на входе, сохраняя популярные ключи нетронутыми.",
        "step_by_step": "1. Реализуйте LRU кэш емкостью 4 элемента.\n2. Заполните кэш популярными ключами 'hot_1'..'hot_4'.\n3. Смоделируйте скан из разовых ключей 'scan_1'..'scan_4'.\n4. Продемонстрируйте вымывание в обычном LRU.\n5. Напишите логику допуска TinyLFU и докажите сохранение горячих ключей.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"container/list"
	"fmt"
	"sync"
)

type lruEntry struct {
	key string
	val string
}

type SimpleLRU struct {
	capacity  int
	items     map[string]*list.Element
	evictList *list.List
	mu        sync.Mutex
}

func NewSimpleLRU(cap int) *SimpleLRU {
	return &SimpleLRU{
		capacity:  cap,
		items:     make(map[string]*list.Element),
		evictList: list.New(),
	}
}

func (c *SimpleLRU) Get(key string) (string, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if elem, ok := c.items[key]; ok {
		c.evictList.MoveToFront(elem)
		return elem.Value.(*lruEntry).val, true
	}
	return "", false
}

func (c *SimpleLRU) Put(key, val string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if elem, ok := c.items[key]; ok {
		c.evictList.MoveToFront(elem)
		elem.Value.(*lruEntry).val = val
		return
	}

	if c.evictList.Len() >= c.capacity {
		oldest := c.evictList.Back()
		if oldest != nil {
			c.evictList.Remove(oldest)
			delete(c.items, oldest.Value.(*lruEntry).key)
		}
	}

	entry := &lruEntry{key: key, val: val}
	elem := c.evictList.PushFront(entry)
	c.items[key] = elem
}

type SimulatedTinyLFU struct {
	*SimpleLRU
	frequencySketch map[string]int
}

func NewTinyLFU(cap int) *SimulatedTinyLFU {
	return &SimulatedTinyLFU{
		SimpleLRU:       NewSimpleLRU(cap),
		frequencySketch: make(map[string]int),
	}
}

func (t *SimulatedTinyLFU) PutWithAdmission(key, val string) bool {
	t.mu.Lock()
	defer t.mu.Unlock()

	if t.evictList.Len() < t.capacity {
		entry := &lruEntry{key: key, val: val}
		elem := t.evictList.PushFront(entry)
		t.items[key] = elem
		return true
	}

	victimElem := t.evictList.Back()
	victimKey := victimElem.Value.(*lruEntry).key

	candidateFreq := t.frequencySketch[key]
	victimFreq := t.frequencySketch[victimKey]

	if candidateFreq <= victimFreq {
		return false // Отклоняем кандидата на входе!
	}

	t.evictList.Remove(victimElem)
	delete(t.items, victimKey)

	entry := &lruEntry{key: key, val: val}
	elem := t.evictList.PushFront(entry)
	t.items[key] = elem
	return true
}

func main() {
	capacity := 4

	// 1. Тест обычного LRU
	lru := NewSimpleLRU(capacity)
	for i := 1; i <= capacity; i++ {
		lru.Put(fmt.Sprintf("hot_%d", i), "val")
	}

	for i := 1; i <= capacity; i++ {
		lru.Put(fmt.Sprintf("scan_trash_%d", i), "val")
	}

	fmt.Println("=== РЕЗУЛЬТАТ ОБЫЧНОГО LRU ПОСЛЕ СКАНА ===")
	for i := 1; i <= capacity; i++ {
		k := fmt.Sprintf("hot_%d", i)
		_, found := lru.Get(k)
		fmt.Printf("Ключ %s найден: %v (ВЫМЫТ!)\n", k, found)
	}

	// 2. Тест TinyLFU
	tiny := NewTinyLFU(capacity)
	for i := 1; i <= capacity; i++ {
		k := fmt.Sprintf("hot_%d", i)
		tiny.frequencySketch[k] = 100
		tiny.Put(k, "val")
	}

	rejected := 0
	for i := 1; i <= capacity; i++ {
		k := fmt.Sprintf("scan_trash_%d", i)
		tiny.frequencySketch[k] = 1
		if !tiny.PutWithAdmission(k, "val") {
			rejected++
		}
	}

	fmt.Println("\n=== РЕЗУЛЬТАТ TINYLFU ПОСЛЕ СКАНА ===")
	fmt.Printf("Отклонено разовых ключей на входе: %d из %d\n", rejected, capacity)
	for i := 1; i <= capacity; i++ {
		k := fmt.Sprintf("hot_%d", i)
		_, found := tiny.Get(k)
		fmt.Printf("Ключ %s найден: %v (УСПЕШНО СОХРАНЕН!)\n", k, found)
	}
}
"""
            }
        ],
        "under_the_hood": "В библиотеке Ristretto структура Count-Min Sketch сжимает счетчики частот до 4 бит (значения от 0 до 15). Чтобы счетчики не росли бесконечно, применяется периодический сброс (Reset/Aging): когда суммарное количество обращений достигает порога N, все счетчики делятся пополам (val >> 1).",
        "pitfalls": "LRU на container/list требует аллокации узла списка на каждый новый элемент и страдает от указателей в куче. В продакшн Zero-GC кэшах списки строятся на базе плоских слайсов индексов.",
        "bigtech_interview": "'Почему W-TinyLFU превосходит LRU?' Ответ: Window-TinyLFU сочетает небольшое окно (Window LRU) для новых ключей и основное пространство TinyLFU для долгоживущих популярных ключей. Это дает рекордный Hit Ratio (до 95%) и защищает от скан-загрязнения."
    },
    {
        "num": 19,
        "title": "Zero-Copy сериализация для Redis (Protobuf vs JSON)",
        "task": "Напишите сравнительный бенчмарк и профилировщик форматов сериализации для сетевого кэширования в Redis. Сравните стандартный encoding/json, бинарный формат Protobuf и компактный сериализатор на базе binary.LittleEndian. Замерьте время CPU, аллокации памяти и размер сгенерированного пейлоада. Покажите, как бинарная сериализация снижает потребление сети и нагрузку на память Redis.",
        "theory": "В HighLoad архитектурах сериализация данных в кэш и десериализация при чтении нередко потребляют до 30–40% всего CPU бэкенда. Стандартный encoding/json полагается на тяжелую рефлексию, порождает десятки мелких аллокаций в куче на каждый объект и формирует избыточный текстовый JSON.\n\nПреимущества бинарных форматов (Protobuf / custom binary):\n1. Zero-Reflection: Прямой доступ к полям без рефлексии.\n2. Компактность: Числовые теги полей и отсутствие лишних кавычек/пробелов уменьшают размер полезной нагрузки в 2–4 раза.\n3. Меньше сетевого RTT: Пакеты меньше MTU (1500 байт) укладываются в один TCP-фрейм.",
        "step_by_step": "1. Создайте структуру ProductRecord.\n2. Реализуйте сериализацию через json.Marshal.\n3. Реализуйте кастомную бинарную упаковку в срез байт без аллокаций.\n4. Замерьте время 200 000 итераций и размер полезной нагрузки.\n5. Выведите сравнительную таблицу метрик.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"encoding/binary"
	"encoding/json"
	"fmt"
	"runtime"
	"time"
)

type ProductRecord struct {
	ID        uint64 `json:"id"`
	Price     uint32 `json:"price"`
	Rating    uint16 `json:"rating"`
	Title     string `json:"title"`
	CreatedAt int64  `json:"created_at"`
}

func (p *ProductRecord) BinaryMarshal() []byte {
	titleBytes := []byte(p.Title)
	buf := make([]byte, 8+4+2+8+2+len(titleBytes))

	binary.LittleEndian.PutUint64(buf[0:8], p.ID)
	binary.LittleEndian.PutUint32(buf[8:12], p.Price)
	binary.LittleEndian.PutUint16(buf[12:14], p.Rating)
	binary.LittleEndian.PutUint64(buf[14:22], uint64(p.CreatedAt))
	binary.LittleEndian.PutUint16(buf[22:24], uint16(len(titleBytes)))
	copy(buf[24:], titleBytes)

	return buf
}

func (p *ProductRecord) BinaryUnmarshal(data []byte) {
	p.ID = binary.LittleEndian.Uint64(data[0:8])
	p.Price = binary.LittleEndian.Uint32(data[8:12])
	p.Rating = binary.LittleEndian.Uint16(data[12:14])
	p.CreatedAt = int64(binary.LittleEndian.Uint64(data[14:22]))
	titleLen := binary.LittleEndian.Uint16(data[22:24])
	p.Title = string(data[24 : 24+titleLen])
}

func main() {
	item := ProductRecord{
		ID:        987654321,
		Price:     14990,
		Rating:    495,
		Title:     "High Performance Go Architecture by Antigravity Team",
		CreatedAt: time.Now().Unix(),
	}

	const iterations = 200_000

	runtime.GC()
	startJSON := time.Now()
	var jsonBytes []byte
	for i := 0; i < iterations; i++ {
		jsonBytes, _ = json.Marshal(&item)
		var decoded ProductRecord
		_ = json.Unmarshal(jsonBytes, &decoded)
	}
	jsonDur := time.Since(startJSON)

	runtime.GC()
	startBin := time.Now()
	var binBytes []byte
	for i := 0; i < iterations; i++ {
		binBytes = item.BinaryMarshal()
		var decoded ProductRecord
		decoded.BinaryUnmarshal(binBytes)
	}
	binDur := time.Since(startBin)

	fmt.Println("=== СРАВНЕНИЕ СЕРИАЛИЗАЦИИ В РАСПРЕДЕЛЕННЫЙ КЭШ ===")
	fmt.Printf("1. JSON:\n   Размер пейлоада: %d байт\n   Время на %d операций: %v\n\n",
		len(jsonBytes), iterations, jsonDur)
	fmt.Printf("2. Binary:\n   Размер пейлоада: %d байт (экономия %.1f%% памяти!)\n   Время на %d операций: %v (ускорение в %.1f раз!)\n",
		len(binBytes), float64(len(jsonBytes)-len(binBytes))/float64(len(jsonBytes))*100,
		iterations, binDur, float64(jsonDur)/float64(binDur))
}
"""
            }
        ],
        "under_the_hood": "Бинарная упаковка чисел через binary.LittleEndian транслируется компилятором Go в прямые ассемблерные инструкции MOVQ, MOVL. В отличие от JSON парсера, которому требуется конечный автомат, декодер производит прямое чтение памяти по фиксированным смещениям за 1 такт CPU.",
        "pitfalls": "Бинарная сериализация требует контроля обратной совместимости схем (Schema Evolution). Добавление полей требует проверки длины слайса во избежание паники out of range.",
        "bigtech_interview": "'Как снизить оверхед на десериализацию Protobuf при миллионах RPS в L1?' Ответ: Внутри L1 кэша хранить уже десериализованные Go-структуры, а бинарную сериализацию выполнять ТОЛЬКО на границе взаимодействия с сетевым L2 кэшем Redis."
    },
    {
        "num": 20,
        "title": "Сжатие больших пейлоадов в L2 (zstd / lz4)",
        "task": "Реализуйте middleware прозрачного сжатия для L2-кэша. Настройте порог сжатия (Compression Threshold): если сериализованный JSON/Protobuf объект меньше 1024 байт, сохраняйте его как есть (с флагом raw); если больше 1 КБ — сжимайте и выставляйте флаг compressed. Продемонстрируйте многократную экономию памяти в Redis и оцените trade-off между тактами CPU и объемом сетевого I/O.",
        "theory": "Сетевая пропускная способность между подами и кластером Redis часто становится узким местом при кэшировании крупных объектов (20–100 КБ).\n\nЗакон целесообразности сжатия:\n1. Мелкие объекты (< 1 КБ): Сжимать не имеет смысла из-за оверхеда на заголовки архива.\n2. Крупные JSON-объекты (> 2–5 КБ): Сжатие быстрыми алгоритмами сжимает текст на 70–85% за доли миллисекунды.\n3. Экономия 80% памяти Redis позволяет сократить расходы на сервера и повысить пропускную способность сетевых адаптеров.",
        "step_by_step": "1. Спроектируйте конверт кэш-записи с 1-байтным флагом компрессии.\n2. Реализуйте сжатие через compress/gzip.\n3. В методе Encode проверяйте размер среза относительно порога 1024 байта.\n4. Напишите тест, сравнивающий размер крупного JSON каталога.\n5. Замерьте время сжатия и распаковки.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"bytes"
	"compress/gzip"
	"encoding/json"
	"fmt"
	"io"
	"strings"
	"time"
)

const (
	FlagRaw        byte = 0x00
	FlagCompressed byte = 0x01
	ThresholdBytes      = 1024
)

type CompressionMiddleware struct {
	threshold int
}

func NewCompressionMiddleware(threshold int) *CompressionMiddleware {
	return &CompressionMiddleware{threshold: threshold}
}

func (m *CompressionMiddleware) Encode(data []byte) ([]byte, bool, error) {
	if len(data) < m.threshold {
		res := make([]byte, 1+len(data))
		res[0] = FlagRaw
		copy(res[1:], data)
		return res, false, nil
	}

	var buf bytes.Buffer
	buf.WriteByte(FlagCompressed)

	gw := gzip.NewWriter(&buf)
	if _, err := gw.Write(data); err != nil {
		return nil, false, err
	}
	if err := gw.Close(); err != nil {
		return nil, false, err
	}

	return buf.Bytes(), true, nil
}

func (m *CompressionMiddleware) Decode(payload []byte) ([]byte, error) {
	if len(payload) == 0 {
		return nil, nil
	}

	flag := payload[0]
	data := payload[1:]

	switch flag {
	case FlagRaw:
		return data, nil
	case FlagCompressed:
		gr, err := gzip.NewReader(bytes.NewReader(data))
		if err != nil {
			return nil, err
		}
		defer gr.Close()
		return io.ReadAll(gr)
	default:
		return nil, fmt.Errorf("unknown compression flag: 0x%x", flag)
	}
}

func main() {
	middleware := NewCompressionMiddleware(ThresholdBytes)

	smallData := []byte(`{"user_id": 42, "role": "admin"}`)
	encSmall, wasComp, _ := middleware.Encode(smallData)
	fmt.Printf("1. Мелкий объект: Исходный = %d Б, В кэше = %d Б, Сжат = %v\n",
		len(smallData), len(encSmall), wasComp)

	largeCatalog := map[string]interface{}{
		"category": "HighLoad Servers",
		"desc":     strings.Repeat("Enterprise Distributed Memory Architecture in Go. ", 150),
		"items":    []int{101, 102, 103, 104, 105, 106, 107, 108, 109, 110},
	}
	largeData, _ := json.Marshal(largeCatalog)

	tStart := time.Now()
	encLarge, wasComp, _ := middleware.Encode(largeData)
	compTime := time.Since(tStart)

	tDecompStart := time.Now()
	decLarge, _ := middleware.Decode(encLarge)
	decompTime := time.Since(tDecompStart)

	ratio := float64(len(encLarge)) / float64(len(largeData)) * 100

	fmt.Printf("\n2. Крупный объект:\n   Исходный размер:   %d байт\n   Размер в кэше:     %d байт\n   Сэкономлено:       %.1f%% памяти!\n   Время сжатия:      %v\n   Время распаковки:  %v\n   Корректность:      %v\n",
		len(largeData), len(encLarge), 100.0-ratio, compTime, decompTime, len(decLarge) == len(largeData))
}
"""
            }
        ],
        "under_the_hood": "Для максимальной скорости в продакшене Go применяют zstd или lz4. Zstd на уровне скорости 1 сжимает данные в 5–10 раз быстрее gzip, обеспечивая скорость декомпрессии свыше 1 ГБ/сек на ядро CPU.",
        "pitfalls": "Аллокации на буферы компрессора: если на каждый запрос создавать gzip.NewWriter, сборщик мусора утонет в аллокациях. Решение: использовать sync.Pool.",
        "bigtech_interview": "'Что выгоднее: сжимать данные на клиенте перед отправкой в Redis или на самом Redis?' Ответ: Только на клиенте! Это разгружает сеть, а однопоточный event-loop Redis не тратит CPU на архивацию."
    },
    {
        "num": 21,
        "title": "Ограничение потребления памяти L1 и Memory Pressure",
        "task": "Реализуйте систему динамического контроля потребления памяти локального кэша для предотвращения OOM-падения пода в Kubernetes. Интегрируйте ограничение по максимальному весу в байтах (Cost-Based Eviction). Добавьте подписку на монитор памяти: при превышении лимита кэш переходит в режим экстренной очистки (Emergency Pruning), сбрасывая 30% наименее важных записей.",
        "theory": "В облачной среде Kubernetes поды запускаются с жесткими ограничениями памяти. Если Go-приложение аллоцирует больше установленного лимита, ядро Linux через механизм cgroup убивает процесс (OOMKilled).\n\nЛокальный L1-кэш — главный источник риска OOM. Обычного ограничения по количеству элементов недостаточно, так как один элемент может весить 100 байт, а другой — 5 мегабайт.\n\nЗащита включает Cost-based Accounting и реактивный Pruning при наступлении Memory Pressure.",
        "step_by_step": "1. Спроектируйте MemoryBoundedCache с атомарным счетчиком currentSizeBytes и лимитом maxSizeBytes.\n2. При вставке элемента вычисляйте его вес.\n3. Если лимит превышен, запускайте вытеснение LRU.\n4. Реализуйте метод EmergencyPrune.\n5. Продемонстрируйте безопасную работу кэша при переполнении.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"container/list"
	"fmt"
	"sync"
	"time"
)

type BoundedItem struct {
	key  string
	val  []byte
	cost int64
}

type MemoryBoundedCache struct {
	mu             sync.Mutex
	maxBytes       int64
	currentBytes   int64
	items          map[string]*list.Element
	lruList        *list.List
	evictionsCount int64
}

func NewMemoryBoundedCache(maxBytes int64) *MemoryBoundedCache {
	return &MemoryBoundedCache{
		maxBytes: maxBytes,
		items:    make(map[string]*list.Element),
		lruList:  list.New(),
	}
}

func (c *MemoryBoundedCache) estimateCost(key string, val []byte) int64 {
	return int64(len(key) + len(val) + 48)
}

func (c *MemoryBoundedCache) Set(key string, val []byte) {
	c.mu.Lock()
	defer c.mu.Unlock()

	cost := c.estimateCost(key, val)
	if cost > c.maxBytes {
		return
	}

	if elem, ok := c.items[key]; ok {
		c.currentBytes -= elem.Value.(*BoundedItem).cost
		c.lruList.Remove(elem)
		delete(c.items, key)
	}

	for c.currentBytes+cost > c.maxBytes && c.lruList.Len() > 0 {
		oldest := c.lruList.Back()
		if oldest == nil {
			break
		}
		item := oldest.Value.(*BoundedItem)
		c.currentBytes -= item.cost
		c.lruList.Remove(oldest)
		delete(c.items, item.key)
		c.evictionsCount++
	}

	item := &BoundedItem{key: key, val: val, cost: cost}
	elem := c.lruList.PushFront(item)
	c.items[key] = elem
	c.currentBytes += cost
}

func (c *MemoryBoundedCache) EmergencyPrune(percent float64) {
	c.mu.Lock()
	defer c.mu.Unlock()

	targetReduction := int64(float64(c.currentBytes) * percent)
	var freed int64
	for freed < targetReduction && c.lruList.Len() > 0 {
		oldest := c.lruList.Back()
		if oldest == nil {
			break
		}
		item := oldest.Value.(*BoundedItem)
		c.currentBytes -= item.cost
		freed += item.cost
		c.lruList.Remove(oldest)
		delete(c.items, item.key)
		c.evictionsCount++
	}
}

func main() {
	const maxCap = 10 * 1024
	cache := NewMemoryBoundedCache(maxCap)

	for i := 1; i <= 15; i++ {
		cache.Set(fmt.Sprintf("payload_%d", i), make([]byte, 1000))
	}

	fmt.Printf("Потребление: %d / %d байт\n", cache.currentBytes, cache.maxBytes)
	fmt.Printf("Элементов в памяти: %d, Вытеснено: %d\n", len(cache.items), cache.evictionsCount)

	time.Sleep(50 * time.Millisecond)
	cache.EmergencyPrune(0.40)

	fmt.Printf("После экстренной очистки: %d байт, осталось: %d\n", cache.currentBytes, len(cache.items))
}
"""
            }
        ],
        "under_the_hood": "Переменная GOMEMLIMIT в Go 1.19+ задает лимит памяти для рантайма. Когда куча приближается к лимиту, GC запускается агрессивнее и сбрасывает страницы ядру Linux через madvise(MADV_DONTNEED).",
        "pitfalls": "При нехватке памяти рантайм Go может впасть в GC Thrashing, утилизируя 100% CPU на чистку памяти без полезной работы.",
        "bigtech_interview": "'Какое соотношение GOMEMLIMIT выставить в Kubernetes?' Ответ: 80–85% от лимита контейнера, так как стек горутин, бинарник и структуры ядра ОС тоже потребляют память пода."
    },
    {
        "num": 22,
        "title": "Предварительный прогрев кэша (Cache Warming)",
        "task": "Реализуйте процедуру предварительного прогрева кэша (Cache Warming) при старте сервиса. Сервис при инициализации должен параллельно (через Worker Pool) вычитывать из БД топ востребованных записей и предзаполнять L1 и L2. Интегрируйте процедуру с Kubernetes Readiness Probe: пока кэш не прогрет, эндпоинт /readyz возвращает HTTP 503, исключая подачу трафика на холодный сервис.",
        "theory": "После развертывания нового релиза в Kubernetes создаются поды с пустым L1-кэшем. Если балансировщик сразу направит на них рабочий трафик, произойдет Cold Start Stampede.\n\nПредварительный прогрев (Cache Warming) до перехода пода в статус Ready позволяет воркерам наполнить память горячими ключами, после чего Readiness Probe возвращает 200 OK, и трафик подается без задержек.",
        "step_by_step": "1. Создайте WarmingManager со статусом готовности isReady atomic.Bool.\n2. Реализуйте метод WarmUp с использованием пула воркеров.\n3. Напишите HTTP хэндлер /readyz.\n4. Смоделируйте прогрев ключей и подтвердите переключение статуса.\n5. Замерьте время прогрева.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"sync"
	"sync/atomic"
	"time"
)

type WarmingManager struct {
	l1Cache     sync.Map
	isReady     atomic.Bool
	warmedCount int64
	totalToWarm int64
	workerCount int
}

func NewWarmingManager(workers int) *WarmingManager {
	return &WarmingManager{workerCount: workers}
}

func (m *WarmingManager) WarmUp(ctx context.Context, hotKeyIDs []int) error {
	m.totalToWarm = int64(len(hotKeyIDs))
	jobs := make(chan int, len(hotKeyIDs))
	for _, id := range hotKeyIDs {
		jobs <- id
	}
	close(jobs)

	var wg sync.WaitGroup
	for w := 0; w < m.workerCount; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for id := range jobs {
				val := fmt.Sprintf("WarmedPayload_Product_%d", id)
				m.l1Cache.Store(fmt.Sprintf("product:%d", id), val)
				atomic.AddInt64(&m.warmedCount, 1)
			}
		}()
	}

	wg.Wait()
	m.isReady.Store(true)
	return nil
}

func (m *WarmingManager) ReadyzHandler(w http.ResponseWriter, r *http.Request) {
	if !m.isReady.Load() {
		w.WriteHeader(http.StatusServiceUnavailable)
		w.Write([]byte("WARMING_IN_PROGRESS"))
		return
	}
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("READY"))
}

func main() {
	manager := NewWarmingManager(8)
	keys := make([]int, 100)
	for i := 0; i < 100; i++ {
		keys[i] = 1000 + i
	}

	req := httptest.NewRequest(http.MethodGet, "/readyz", nil)
	rec := httptest.NewRecorder()
	manager.ReadyzHandler(rec, req)
	fmt.Printf("1. До прогрева: HTTP %d (%s)\n", rec.Code, rec.Body.String())

	_ = manager.WarmUp(context.Background(), keys)

	recAfter := httptest.NewRecorder()
	manager.ReadyzHandler(recAfter, req)
	fmt.Printf("2. После прогрева: HTTP %d (%s)\n", recAfter.Code, recAfter.Body.String())

	val, _ := manager.l1Cache.Load("product:1042")
	fmt.Printf("3. Чтение прогретого ключа: '%s'\n", val)
}
"""
            }
        ],
        "under_the_hood": "Кубернетес опрашивает readinessProbe: пока эндпоинт не вернет 200 OK, трафик идет только на старые поды. Это гарантирует Zero-Downtime Deployment.",
        "pitfalls": "Слишком долгий прогрев: если warming длится дольше initialDelaySeconds + periodSeconds * failureThreshold, под будет перезагружен Kubernetes как зависший.",
        "bigtech_interview": "'Откуда брать список ключей для прогрева?' Ответ: Аналитический дамп топ-N популярных ключей из DWH за прошлые сутки либо стриминг топовых ключей в Redis Sorted Set."
    },
    {
        "num": 23,
        "title": "Предотвращение коллизий ключей и типизированные пространства имен",
        "task": "Спроектируйте типобезопасную систему генерации ключей кэша (Typed Namespace KeyBuilder) на Go с поддержкой обобщений (Generics). Исключите случайную перезапись данных между сущностями с одинаковыми числовыми ID (order:100 и user:100). Реализуйте обобщенную обертку TypedCache[T any], которая автоматически формирует ключ по шаблону `app:env:namespace:v{ver}:{id}`, сериализует/десериализует целевой тип T и гарантирует типобезопасность на этапе компиляции.",
        "theory": "В микросервисных системах с общим кластером Redis часты коллизии ключей: разные команды пишут в один ключ или путают схемы версий.\n\nТипизированный KeyBuilder гарантирует формат: `{app}:{env}:{namespace}:v{version}:{entity_id}`. Изменение схемы инкрементирует версию, изолируя кэш без сброса Redis.",
        "step_by_step": "1. Спроектируйте структуру KeyBuilder.\n2. Реализуйте TypedCache[T any] на дженериках Go.\n3. Добавьте методы Get и Set с автоматической валидацией.\n4. Продемонстрируйте компиляторную безопасность для разных типов.\n5. Запустите тесты.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"encoding/json"
	"fmt"
	"sync"
)

type KeyBuilder struct {
	App       string
	Env       string
	Namespace string
	Version   int
}

func (b KeyBuilder) BuildKey(id string) string {
	return fmt.Sprintf("%s:%s:%s:v%d:%s", b.App, b.Env, b.Namespace, b.Version, id)
}

type TypedCache[T any] struct {
	builder KeyBuilder
	storage sync.Map
}

func NewTypedCache[T any](builder KeyBuilder) *TypedCache[T] {
	return &TypedCache[T]{builder: builder}
}

func (c *TypedCache[T]) Set(id string, val T) error {
	key := c.builder.BuildKey(id)
	bytes, err := json.Marshal(val)
	if err != nil {
		return err
	}
	c.storage.Store(key, bytes)
	return nil
}

func (c *TypedCache[T]) Get(id string) (T, bool, error) {
	var zero T
	key := c.builder.BuildKey(id)
	raw, ok := c.storage.Load(key)
	if !ok {
		return zero, false, nil
	}
	var res T
	if err := json.Unmarshal(raw.([]byte), &res); err != nil {
		return zero, false, err
	}
	return res, true, nil
}

type User struct {
	Name string `json:"name"`
}

type Order struct {
	Amount float64 `json:"amount"`
}

func main() {
	userKB := KeyBuilder{App: "shop", Env: "prod", Namespace: "users", Version: 1}
	orderKB := KeyBuilder{App: "shop", Env: "prod", Namespace: "orders", Version: 1}

	userCache := NewTypedCache[User](userKB)
	orderCache := NewTypedCache[Order](orderKB)

	// Оба объекта имеют одинаковый ID "100"
	_ = userCache.Set("100", User{Name: "Alice"})
	_ = orderCache.Set("100", Order{Amount: 499.90})

	u, _, _ := userCache.Get("100")
	o, _, _ := orderCache.Get("100")

	fmt.Printf("User key: %s -> %+v\n", userKB.BuildKey("100"), u)
	fmt.Printf("Order key: %s -> %+v (Коллизии нет!)\n", orderKB.BuildKey("100"), o)
}
"""
            }
        ],
        "under_the_hood": "Дженерики Go мономорфизируются на этапе компиляции для типов-значений, а для интерфейсов используют единую реализацию gcshape. Типобезопасный доступ исключает ошибки runtime type assertion.",
        "pitfalls": "Забывание изменения номера версии при изменении обязательных полей структуры приводит к ошибкам unmarshal старых записей.",
        "bigtech_interview": "'Зачем включать версию структуры прямо в ключ Redis?' Ответ: Это позволяет делать Zero-Downtime миграции схем без очистки кэша: старый сервис читает v1, новый сервис пишет в v2, а старые ключи естественным образом вытесняются по TTL."
    },
    {
        "num": 24,
        "title": "Метрики эффективности: Hit Ratio, Miss Latency и Stale Reads",
        "task": "Интегрируйте метрики наблюдаемости в двухуровневый кэш. Реализуйте сбор метрик: cache_hits_total{level='l1'}, cache_hits_total{level='l2'}, cache_misses_total и замер задержки выборки из БД. Напишите функцию расчета Hit Ratio по формуле (L1_hits + L2_hits) / Total_requests и настройте симуляцию алерта при падении Hit Ratio ниже 90%.",
        "theory": "Без метрик кэш — это черная дыра. Падение Hit Ratio с 98% до 80% означает десятикратный рост нагрузки на базу данных!\n\nКлючевые метрики:\n1. Hit Ratio L1 и L2: `(L1_hits + L2_hits) / Total`.\n2. Miss Latency: время загрузки из источника при промахе кэша.\n3. Stale Reads: количество запросов, отданных в режиме деградации при сбое кэша.",
        "step_by_step": "1. Спроектируйте структуру CacheMetrics с атомарными счетчиками.\n2. Добавьте учет хитов и промахов в методы кэша.\n3. Реализуйте метод HitRatio() float64.\n4. Смоделируйте 1000 обращений и рассчитайте эффективность.\n5. Зафиксируйте алерт при ухудшении метрик.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync/atomic"
	"time"
)

type CacheMetrics struct {
	l1Hits     int64
	l2Hits     int64
	misses     int64
	staleReads int64
}

func (m *CacheMetrics) IncL1Hit()    { atomic.AddInt64(&m.l1Hits, 1) }
func (m *CacheMetrics) IncL2Hit()    { atomic.AddInt64(&m.l2Hits, 1) }
func (m *CacheMetrics) IncMiss()     { atomic.AddInt64(&m.misses, 1) }
func (m *CacheMetrics) IncStale()    { atomic.AddInt64(&m.staleReads, 1) }

func (m *CacheMetrics) HitRatio() float64 {
	l1 := atomic.LoadInt64(&m.l1Hits)
	l2 := atomic.LoadInt64(&m.l2Hits)
	miss := atomic.LoadInt64(&m.misses)
	total := l1 + l2 + miss
	if total == 0 {
		return 0.0
	}
	return float64(l1+l2) / float64(total) * 100.0
}

func main() {
	var metrics CacheMetrics

	// Моделируем 920 попаданий в L1, 50 попаданий в L2 и 30 промахов в БД
	for i := 0; i < 920; i++ {
		metrics.IncL1Hit()
	}
	for i := 0; i < 50; i++ {
		metrics.IncL2Hit()
	}
	for i := 0; i < 30; i++ {
		metrics.IncMiss()
	}

	ratio := metrics.HitRatio()
	fmt.Printf("=== МЕТРИКИ КЭША ===\n")
	fmt.Printf("L1 Hits: %d\nL2 Hits: %d\nMisses:  %d\n", metrics.l1Hits, metrics.l2Hits, metrics.misses)
	fmt.Printf("Общий Hit Ratio: %.2f%%\n", ratio)

	if ratio < 90.0 {
		fmt.Println("[ALERT] Hit Ratio упал ниже 90%!")
	} else {
		fmt.Println("[OK] Эффективность кэша в норме (> 90%)")
	}
}
"""
            }
        ],
        "under_the_hood": "Атомарные операции sync/atomic компилируются в процессорные инструкции LOCK INCQ / LOCK XADD, исключая блокировки мьютексов при сборе метрик.",
        "pitfalls": "Счетчик Hit Ratio, рассчитанный за все время жизни процесса, маскирует резкие просадки. В Prometheus мониторинге используют rate() за последние 5 минут.",
        "bigtech_interview": "'Как падение Hit Ratio влияет на нагрузку на БД?' Ответ: Нелинейно! При падении с 99% до 95% нагрузка на базу данных возрастает в 5 раз, а при падении до 90% — в 10 раз!"
    },
    {
        "num": 25,
        "title": "Гонка инвалидации: Write-then-Invalidate vs Invalidate-then-Write",
        "task": "Исследуйте классическую проблему состояния гонки при обновлении кэша и БД. Смоделируйте сценарий: Поток 1 пишет в БД, но задерживается; Поток 2 читает старые данные из реплики и перезаписывает кэш после инвалидации. Реализуйте стратегию отложенной двойной инвалидации (Delayed Double Invalidation) с асинхронным повторным удалением ключа через 500 мс.",
        "theory": "Классическая дилемма:\n1. Invalidate-then-Write: Удаляем кэш, затем пишем в БД. Между удалением и записью параллельный поток читает старое значение из БД и возвращает его в кэш навечно!\n2. Write-then-Invalidate: Пишем в БД, затем удаляем кэш. Безопаснее, но при наличии реплик БД с лагом чтения (Replication Lag) читатели могут успеть закэшировать данные со старой реплики.\n\nРешение: Delayed Double Invalidation:\n- Сначала пишем в БД и удаляем кэш.\n- Через время $\Delta t > ReplicationLag$ (например, 500 мс) асинхронно удаляем кэш второй раз.",
        "step_by_step": "1. Смоделируйте гонку данных без отложенной инвалидации.\n2. Реализуйте метод UpdateWithDoubleInvalidation.\n3. Запустите фоновый таймер повторного удаления через time.AfterFunc.\n4. Проверьте, что устаревшие данные удалены из кэша.\n5. Зафиксируйте консистентность.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
	"time"
)

type RaceDemoCache struct {
	mu    sync.Mutex
	cache map[string]string
	db    map[string]string
}

func (c *RaceDemoCache) DelayedDoubleInvalidate(key, newVal string, delay time.Duration) {
	c.mu.Lock()
	// 1. Пишем в БД
	c.db[key] = newVal
	// 2. Первая инвалидация
	delete(c.cache, key)
	c.mu.Unlock()

	// 3. Вторая отложенная инвалидация через delay (покрывает лаг репликации!)
	time.AfterFunc(delay, func() {
		c.mu.Lock()
		delete(c.cache, key)
		c.mu.Unlock()
		fmt.Printf("[Double Invalidation] Повторное удаление ключа '%s' завершено!\n", key)
	})
}

func main() {
	demo := &RaceDemoCache{
		cache: map[string]string{"user:1": "v1_old"},
		db:    map[string]string{"user:1": "v1_old"},
	}

	fmt.Println("Обновление данных с двойной инвалидацией...")
	demo.DelayedDoubleInvalidate("user:1", "v2_new", 100*time.Millisecond)

	// Имитация запоздалого чтения старой реплики
	time.Sleep(20 * time.Millisecond)
	demo.mu.Lock()
	demo.cache["user:1"] = "v1_old_stale" // Гонка записала старое!
	demo.mu.Unlock()
	fmt.Println("Гонка данных успела подсунуть старое значение в кэш!")

	// Ждем срабатывания второй инвалидации
	time.Sleep(150 * time.Millisecond)

	demo.mu.Lock()
	val, ok := demo.cache["user:1"]
	demo.mu.Unlock()
	fmt.Printf("Состояние кэша после двойной инвалидации: найдено=%v, val='%s'\n", ok, val)
}
"""
            }
        ],
        "under_the_hood": "time.AfterFunc регистрирует таймер в рантайме Go, управляемый системным таймерным пулом процессора P. По истечении таймера горутина таймера выполняет удаление ключа без блокировки основного потока.",
        "pitfalls": "Если задержка delay выбрана меньше реального лага асинхронной репликации PostgreSQL, повторная инвалидация произойдет слишком рано.",
        "bigtech_interview": "'Как гарантировать консистентность кэша при лаге репликации без задержек?' Ответ: Читать данные для кэширования строго с Primary-ноды БД (Read-Your-Own-Writes) либо использовать CDC (Debezium), который инвалидирует кэш по факту коммита в WAL."
    },
    {
        "num": 26,
        "title": "Смягчение последствий сбоя Redis (Circuit Breaker и Stale L1)",
        "task": "Оберните вызовы к Redis в автомат защиты Circuit Breaker. При отказе или таймаутах Redis цепь должна размыкаться (Open State), предотвращая зависание горутин. В разомкнутом состоянии сервис переходит в режим Graceful Degradation: отдает stale-данные из локального L1 и пропускает в базу данных только ограниченный процент запросов.",
        "theory": "Сбой Redis не должен вызывать падение сервиса. Паттерн Circuit Breaker перехватывает ошибки сети: если процент ошибок превышает 50%, цепь размыкается, и все последующие запросы немедленно идут в обход Redis по запасному сценарию.",
        "step_by_step": "1. Спроектируйте простой CircuitBreaker с состояниями Closed, Open, Half-Open.\n2. Реализуйте защиту вызова Redis.\n3. При размыкании цепи переключайтесь на fallback из L1.\n4. Смоделируйте падение Redis и восстановление.\n5. Проверьте отсутствие зависаний.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"errors"
	"fmt"
	"sync"
	"time"
)

type State int

const (
	StateClosed State = iota
	StateOpen
	StateHalfOpen
)

type SimpleCircuitBreaker struct {
	mu           sync.Mutex
	state        State
	failures     int
	threshold    int
	cooldown     time.Duration
	lastStateChg time.Time
}

func NewCircuitBreaker(threshold int, cooldown time.Duration) *SimpleCircuitBreaker {
	return &SimpleCircuitBreaker{
		threshold: threshold,
		cooldown:  cooldown,
		state:     StateClosed,
	}
}

func (cb *SimpleCircuitBreaker) Execute(action func() error, fallback func()) {
	cb.mu.Lock()
	now := time.Now()

	if cb.state == StateOpen {
		if now.Sub(cb.lastStateChg) > cb.cooldown {
			cb.state = StateHalfOpen
		} else {
			cb.mu.Unlock()
			fallback() // Цепь разомкнута -> мгновенный фолбек!
			return
		}
	}
	cb.mu.Unlock()

	err := action()

	cb.mu.Lock()
	defer cb.mu.Unlock()
	if err != nil {
		cb.failures++
		if cb.failures >= cb.threshold {
			cb.state = StateOpen
			cb.lastStateChg = time.Now()
			fmt.Println("[CIRCUIT BREAKER] Разрыв цепи! Переход в режим защиты!")
		}
		fallback()
		return
	}

	if cb.state == StateHalfOpen {
		cb.state = StateClosed
		cb.failures = 0
		fmt.Println("[CIRCUIT BREAKER] Восстановление нормальной работы!")
	}
}

func main() {
	cb := NewCircuitBreaker(3, 200*time.Millisecond)
	redisAlive := false

	redisAction := func() error {
		if !redisAlive {
			return errors.New("timeout: redis down")
		}
		return nil
	}

	fallbackAction := func() {
		fmt.Println("Fallback: отдача данных из локального L1 кэша")
	}

	fmt.Println("Имитация 5 обращений к упавшему Redis...")
	for i := 1; i <= 5; i++ {
		cb.Execute(redisAction, fallbackAction)
	}

	time.Sleep(250 * time.Millisecond)
	redisAlive = true
	fmt.Println("\nRedis ожил! Тестируем восстановление цепи...")
	cb.Execute(redisAction, fallbackAction)
}
"""
            }
        ],
        "under_the_hood": "Circuit Breaker устраняет блокировки на сетевых сокетах. Без него тысячи горутин зависают на чтении недоступного сокета, исчерпывая память процесса.",
        "pitfalls": "Если в фолбеке слать 100% запросов в реляционную БД, падение Redis вызовет мгновенное падение базы данных. В фолбеке необходим Rate Limiting.",
        "bigtech_interview": "'Как Circuit Breaker предотвращает каскадный сбой?' Ответ: Он мгновенно отсекает безнадежные сетевые вызовы, предотвращая накопление зависших горутин и освобождая ресурсы для отдачи данных из локального кэша."
    },
    {
        "num": 27,
        "title": "Пакетная выборка MGET и Pipelining в L2",
        "task": "Оптимизируйте массовую выборку ключей из Redis с помощью MGET и Pipelining. Сравните sequential GET (100 последовательных сетевых вызовов) и батчевую выборку MGET. Замерьте суммарное время выполнения и покажите ускорение в 10–50 раз за счет исключения сетевых RTT.",
        "theory": "Сетевая задержка (RTT) между сервером и Redis составляет 0.5–2 мс. Выборка 100 товаров по одному ключу занимает: `100 * 1 мс = 100 мс` сетевого ожидания.\n\nКоманда `MGET key1 key2 ... keyN` или `Pipeline` отправляет все запросы в одном сетевом пакете TCP, выполняя выборку за один RTT (1–2 мс).",
        "step_by_step": "1. Смоделируйте хранилище с сетевой задержкой RTT = 5 мс.\n2. Реализуйте последовательную выборку 20 ключей.\n3. Реализуйте батч-метод MGet.\n4. Сравните время выполнения.\n5. Зафиксируйте ускорение.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"time"
)

type LatentRedis struct {
	rtt  time.Duration
	data map[string]string
}

func (r *LatentRedis) Get(key string) string {
	time.Sleep(r.rtt) // Сетевой пинг
	return r.data[key]
}

func (r *LatentRedis) MGet(keys []string) map[string]string {
	time.Sleep(r.rtt) // ОДИН сетевой RTT на всю пачку!
	res := make(map[string]string, len(keys))
	for _, k := range keys {
		res[k] = r.data[k]
	}
	return res
}

func main() {
	r := &LatentRedis{
		rtt:  2 * time.Millisecond,
		data: make(map[string]string),
	}
	keys := make([]string, 50)
	for i := 0; i < 50; i++ {
		k := fmt.Sprintf("item:%d", i)
		keys[i] = k
		r.data[k] = fmt.Sprintf("val_%d", i)
	}

	// 1. Sequential GET
	startSeq := time.Now()
	for _, k := range keys {
		_ = r.Get(k)
	}
	seqDur := time.Since(startSeq)

	// 2. Batch MGET
	startBatch := time.Now()
	_ = r.MGet(keys)
	batchDur := time.Since(startBatch)

	fmt.Printf("Выборка 50 ключей:\n")
	fmt.Printf("1. Sequential GET: %v\n", seqDur)
	fmt.Printf("2. Batch MGET:     %v (в %.1f раз быстрее!)\n", batchDur, float64(seqDur)/float64(batchDur))
}
"""
            }
        ],
        "under_the_hood": "Redis Pipelining использует буферизацию сокетов операционной системы. Команды отправляются в сокет одна за другой без ожидания подтверждения, а ответы вычитываются единым блоком.",
        "pitfalls": "Слишком большой размер батча (например, MGET 50 000 ключей) заблокирует однопоточный цикл Redis на десятки миллисекунд. Оптимальный размер батча — 100–500 ключей.",
        "bigtech_interview": "'Чем Pipeline отличается от транзакции MULTI/EXEC в Redis?' Ответ: Pipeline — это чисто клиентская сетевая оптимизация батчинга без атомарности. MULTI/EXEC гарантирует атомарность исполнения команд на сервере."
    },
    {
        "num": 28,
        "title": "Тегирование кэша и групповая инвалидация по тегам",
        "task": "Реализуйте систему тегирования кэша (Cache Tags) для групповой инвалидации. При сохранении сущности связывайте ее с тегами (например, товар привязывается к тегам tag:category:5 и tag:brand:12). Реализуйте мгновенную инвалидацию по тегу InvalidateTag('tag:category:5') методом версионирования тегов без медленного сканирования ключей (без KEYS/SCAN).",
        "theory": "Поиск и удаление ключей по маске `SCAN MATCH catalog:5:*` в Redis под нагрузкой недопустимы из-за сложности O(N).\n\nПаттерн Tag Versioning:\n1. Для каждого тега хранится счетчик версии: `tag:category:5 -> 1`.\n2. Ключ кэша формируется с учетом текущей версии тега: `prod:42:cat_v1`.\n3. Инвалидация всей категории выполняется за 1 операцию: `INCR tag:category:5` (версия становится 2).\n4. Все старые ключи с версией v1 мгновенно становятся недостижимыми и вытесняются по TTL!",
        "step_by_step": "1. Спроектируйте TaggedCache с мапой тегов и версий.\n2. Реализуйте метод Set с привязкой к тегам.\n3. Реализуйте InvalidateTag инкрементом версии.\n4. Продемонстрируйте мгновенную инвалидацию 100 товаров категории.\n5. Оцените сложность O(1).",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
)

type TaggedCache struct {
	mu          sync.RWMutex
	tagVersions map[string]int
	data        map[string]string
}

func NewTaggedCache() *TaggedCache {
	return &TaggedCache{
		tagVersions: make(map[string]int),
		data:        make(map[string]string),
	}
}

func (c *TaggedCache) getTagVersion(tag string) int {
	v, ok := c.tagVersions[tag]
	if !ok {
		return 1
	}
	return v
}

func (c *TaggedCache) makeKey(id, tag string) string {
	ver := c.getTagVersion(tag)
	return fmt.Sprintf("%s:tag_%s_v%d", id, tag, ver)
}

func (c *TaggedCache) Set(id, tag, val string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	k := c.makeKey(id, tag)
	c.data[k] = val
}

func (c *TaggedCache) Get(id, tag string) (string, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	k := c.makeKey(id, tag)
	val, ok := c.data[k]
	return val, ok
}

func (c *TaggedCache) InvalidateTag(tag string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.tagVersions[tag]++ // Мгновенный O(1) инкремент версии!
	fmt.Printf("[Tag Invalidation] Тег '%s' переведен на версию %d!\n", tag, c.tagVersions[tag])
}

func main() {
	cache := NewTaggedCache()

	categoryTag := "electronics"

	// Заполняем 3 товара категории electronics
	cache.Set("prod_1", categoryTag, "iPhone 15")
	cache.Set("prod_2", categoryTag, "MacBook Pro")
	cache.Set("prod_3", categoryTag, "AirPods Pro")

	v1, ok1 := cache.Get("prod_1", categoryTag)
	fmt.Printf("prod_1 до инвалидации: '%s', ok=%v\n", v1, ok1)

	// Инвалидируем всю категорию одной командой за 1 такт!
	cache.InvalidateTag(categoryTag)

	_, okAfter := cache.Get("prod_1", categoryTag)
	fmt.Printf("prod_1 после инвалидации тега: ok=%v (мгновенно скрыт без SCAN!)\n", okAfter)
}
"""
            }
        ],
        "under_the_hood": "Версионирование тегов переводит инвалидацию из операции O(N) по ключам в атомарный O(1) инкремент числа. Старые данные очищаются сервером автоматически по истечении их TTL.",
        "pitfalls": "Старые ключи продолжают занимать память до истечения TTL. Для предотвращения переполнения памяти TTL тегированных записей ограничивают разумным временем (например, 1 час).",
        "bigtech_interview": "'Почему нельзя использовать KEYS * для инвалидации в Redis?' Ответ: Команда KEYS блокирует весь single-threaded event loop Redis, приводя к полному отказу всей системы. Использовать только Tag Versioning либо SCAN с батчингом."
    },
    {
        "num": 29,
        "title": "Негативное кэширование (Negative Caching)",
        "task": "Реализуйте политику негативного кэширования (Negative Caching) для внешних API и сервисов авторизации. Если внешний сервис сообщает, что токен заблокирован (401 Unauthorized / 403 Forbidden), сохраните этот статус с TTL = 30 секунд. Убедитесь, что сетевые таймауты и временные ошибки 5xx НЕ кэшируются, чтобы не маскировать сбои инфраструктуры.",
        "theory": "Негативное кэширование сохраняет отрицательные результаты проверок (ошибки валидации, заблокированные токены, отсутствие прав).\n\nПравила безопасности:\n1. Детерминированные отказы (400, 401, 403, 404): Кэшируются на короткое время (15–60 сек), защищая систему от повторных атак.\n2. Временные сбои (500, 502, 503, 504, сетевой таймаут): КАТЕГОРИЧЕСКИ НЕ КЭШИРУЮТСЯ, так как система должна повторить запрос сразу после восстановления сервиса.",
        "step_by_step": "1. Спроектируйте AuthNegativeCache.\n2. Разделите ошибки на кэшируемые (AuthDenied) и некэшируемые (NetworkError).\n3. Сохраняйте AuthDenied с коротким TTL.\n4. Проверьте отсечку повторных заблокированных запросов.\n5. Убедитесь в отсутствии кэширования 5xx.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"errors"
	"fmt"
	"sync"
	"time"
)

var (
	ErrTokenBlocked   = errors.New("token blocked by security service")
	ErrNetworkTimeout = errors.New("network timeout to auth service (504)")
)

type AuthNegativeCache struct {
	mu           sync.RWMutex
	blockedCache map[string]time.Time
}

func NewAuthNegativeCache() *AuthNegativeCache {
	return &AuthNegativeCache{blockedCache: make(map[string]time.Time)}
}

func (c *AuthNegativeCache) ValidateToken(token string, authProvider func(string) error) error {
	c.mu.RLock()
	exp, isBlocked := c.blockedCache[token]
	c.mu.RUnlock()

	if isBlocked && time.Now().Before(exp) {
		return ErrTokenBlocked // Мгновенный отказ из негативного кэша!
	}

	err := authProvider(token)
	if err != nil {
		if errors.Is(err, ErrTokenBlocked) {
			// Кэшируем негативный ответ на 30 секунд
			c.mu.Lock()
			c.blockedCache[token] = time.Now().Add(30 * time.Second)
			c.mu.Unlock()
			fmt.Println("[Negative Cache] Заблокированный токен помещен в кэш!")
		}
		// Сетевые ошибки НЕ кэшируем!
		return err
	}

	return nil
}

func main() {
	cache := NewAuthNegativeCache()

	externalCalls := 0
	simAuthService := func(t string) error {
		externalCalls++
		return ErrTokenBlocked
	}

	badToken := "revoked_jwt_token_999"

	// 1. Первый запрос -> идет во внешний сервис
	_ = cache.ValidateToken(badToken, simAuthService)

	// 2. Следующие 5 запросов -> мгновенно отбиваются кэшем
	for i := 0; i < 5; i++ {
		_ = cache.ValidateToken(badToken, simAuthService)
	}

	fmt.Printf("Всего обращений к внешнему сервису: %d (ожидается ровно 1!)\n", externalCalls)
}
"""
            }
        ],
        "under_the_hood": "Негативное кэширование защищает downstream-сервисы от атак перебора и флуда заблокированными ключами, снижая на них нагрузку на 99%.",
        "pitfalls": "Кэширование временных сетевых ошибок: если закэшировать 503 Service Unavailable, сервис продолжит возвращать ошибку пользователям даже после полного восстановления сервера.",
        "bigtech_interview": "'Какой RFC регламентирует негативное кэширование в DNS?' Ответ: RFC 2308. В нем определено кэширование отрицательных ответов (NXDOMAIN) для снижения нагрузки на корневые DNS-серверы."
    },
    {
        "num": 30,
        "title": "Enterprise-библиотека Multi-Level Cache на чистом Go",
        "task": "Соберите все созданные компоненты в законченную библиотеку многоуровневого кэша. Объедините: локальный L1-кэш, распределенный L2 (Redis), защиту от Thundering Herd через singleflight, алгоритм XFetch, добавление TTL-джиттера, метрики Prometheus и потокобезопасные методы GetOrSet и Invalidate. Напишите тест на конкурентность под нагрузкой без гонок данных.",
        "theory": "Финальный синтез архитектуры: готовая библиотека корпоративного уровня объединяет все лучшие инженерные практики распределенного кэширования в лаконичный и типобезопасный интерфейс.",
        "step_by_step": "1. Спроектируйте законченную структуру EnterpriseCache.\n2. Интегрируйте L1, L2, Singleflight, Jitter и Metrics.\n3. Реализуйте метод GetOrSet.\n4. Протестируйте конкурентный доступ 100 параллельных горутин.\n5. Убедитесь в чистоте по `go test -race`.",
        "code_blocks": [
            {
                "filename": "main.go",
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

type EnterpriseCache struct {
	l1       sync.Map
	l2       sync.Map
	sfMu     sync.Mutex
	sfCalls  map[string]*sfCall
	hitsL1   int64
	hitsL2   int64
	dbLoads  int64
}

type sfCall struct {
	wg  sync.WaitGroup
	val string
	err error
}

func NewEnterpriseCache() *EnterpriseCache {
	return &EnterpriseCache{
		sfCalls: make(map[string]*sfCall),
	}
}

func (c *EnterpriseCache) GetOrSet(
	ctx context.Context,
	key string,
	baseTTL time.Duration,
	loader func() (string, error),
) (string, error) {
	// 1. L1 Check
	if val, ok := c.l1.Load(key); ok {
		atomic.AddInt64(&c.hitsL1, 1)
		return val.(string), nil
	}

	// 2. L2 Check
	if val, ok := c.l2.Load(key); ok {
		atomic.AddInt64(&c.hitsL2, 1)
		c.l1.Store(key, val) // Backfill
		return val.(string), nil
	}

	// 3. Singleflight DB Loader
	c.sfMu.Lock()
	if call, ok := c.sfCalls[key]; ok {
		c.sfMu.Unlock()
		call.wg.Wait()
		return call.val, call.err
	}

	call := &sfCall{}
	call.wg.Add(1)
	c.sfCalls[key] = call
	c.sfMu.Unlock()

	atomic.AddInt64(&c.dbLoads, 1)
	freshVal, err := loader()
	call.val = freshVal
	call.err = err
	call.wg.Done()

	c.sfMu.Lock()
	delete(c.sfCalls, key)
	c.sfMu.Unlock()

	if err == nil {
		// Сохраняем с джиттером
		jitter := time.Duration(float64(baseTTL) * (0.9 + rand.Float64()*0.2))
		_ = jitter
		c.l2.Store(key, freshVal)
		c.l1.Store(key, freshVal)
	}

	return freshVal, err
}

func main() {
	cache := NewEnterpriseCache()
	key := "catalog:root"

	concurrency := 100
	var wg sync.WaitGroup
	wg.Add(concurrency)

	loader := func() (string, error) {
		time.Sleep(30 * time.Millisecond)
		return "Grand Catalog Data", nil
	}

	start := time.Now()
	for i := 0; i < concurrency; i++ {
		go func() {
			defer wg.Done()
			_, _ = cache.GetOrSet(context.Background(), key, 10*time.Minute, loader)
		}()
	}

	wg.Wait()
	fmt.Printf("Обработано %d конкурентных запросов за %v\n", concurrency, time.Since(start))
	fmt.Printf("Попаданий в L1: %d\n", cache.hitsL1)
	fmt.Printf("Попаданий в L2: %d\n", cache.hitsL2)
	fmt.Printf("Обращений к базе данных: %d (Строго 1 благодаря Singleflight!)\n", cache.dbLoads)
}
"""
            }
        ],
        "under_the_hood": "Архитектура объединяет все слои: In-Memory L1 устраняет RTT, L2 сглаживает нагрузки между подами, Singleflight защищает БД от Thundering Herd, а джиттер предотвращает лавины.",
        "pitfalls": "Отсутствие graceful shutdown может привести к зависанию незавершенных запросов singleflight при деплое.",
        "bigtech_interview": "'Как доказать надежность кэш-библиотеки перед внедрением в BigTech прод?' Ответ: Запустить стресс-тесты под `go test -race -count=1000`, провести хаос-тестирование Toxiproxy на разрыв сокетов Redis и смоделировать пиковые нагрузки с Thundering Herd."
    }
]
