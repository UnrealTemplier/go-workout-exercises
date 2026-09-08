# -*- coding: utf-8 -*-
"""
Chapter 85 Part 1: Exercises 1 to 15
Multi-Level Caching (L1/L2) and Distributed Coherence in Go
"""

exercises = [
    {
        "num": 1,
        "title": "Архитектура L1/L2 кэша: локальная память + Redis",
        "task": "Спроектируйте архитектуру двухуровневого кэширования на Go. Определите интерфейсы локального L1-кэша (In-Memory) и распределенного L2-кэша (Redis), а также координирующую структуру MultiLevelCache. Реализуйте иерархический алгоритм чтения: при запросе ключа сначала проверяется L1; при промахе опрашивается L2; если значение найдено в L2, оно асинхронно или синхронно прогревает L1 (backfill). При полном промахе вызывается функция-загрузчик из первоисточника (БД), после чего результат сохраняется в L2 и L1.",
        "theory": "Многоуровневое кэширование (Multi-Level Caching) является золотым стандартом построения систем с субмиллисекундным временем отклика при миллионных RPS (HighLoad). Одиночный распределенный кэш (например, Redis или Memcached) упирается в задержки сети (Network RTT ~0.5–2 мс) и накладные расходы на системные вызовы ядра при чтении сокетов. Локальный L1-кэш в оперативной памяти Go-процесса обеспечивает чтение за 20–100 наносекунд.\n\nОднако память отдельного инстанса ограничена, а данные рассинхронизируются при масштабировании. Двухуровневая архитектура L1/L2 объединяет достоинства обоих подходов:\n1. L1 (In-Memory): Экстремально быстрый доступ, хранит самое горячее подмножество ключей, короткий TTL.\n2. L2 (Redis Cluster): Общий распределенный источник правды кэша с длительным TTL, защищающий базу данных от пиковых нагрузок при перезапуске отдельных подов в Kubernetes.",
        "step_by_step": "1. Определите интерфейсы L1Cache и L2Cache с методами Get, Set, Delete.\n2. Создайте структуру MultiLevelCache со ссылками на оба уровня кэша.\n3. Реализуйте метод GetOrLoad с поддержкой контекста, функции-загрузчика (fetcher) и индивидуальных TTL для L1 и L2.\n4. Обеспечьте логику Backfill: найденное в L2 значение немедленно помещается в L1 перед возвратом клиенту.\n5. Напишите сценарий в main.go, демонстрирующий время отклика при холодном старте, попадании в L2 и мгновенном попадании в L1.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

var ErrCacheMiss = errors.New("cache: key not found")

// L1Cache представляет интерфейс сверхбыстрого локального кэша в памяти процесса.
type L1Cache interface {
	Get(key string) ([]byte, bool)
	Set(key string, val []byte, ttl time.Duration)
	Delete(key string)
}

// L2Cache представляет интерфейс распределенного сетевого кэша (Redis).
type L2Cache interface {
	Get(ctx context.Context, key string) ([]byte, error)
	Set(ctx context.Context, key string, val []byte, ttl time.Duration) error
	Delete(ctx context.Context, key string) error
}

// InMemoryL1 реализация L1 на sync.Map с фиксацией времени экспирации.
type InMemoryL1 struct {
	data sync.Map
}

type l1Entry struct {
	value     []byte
	expiresAt time.Time
}

func NewInMemoryL1() *InMemoryL1 {
	return &InMemoryL1{}
}

func (c *InMemoryL1) Get(key string) ([]byte, bool) {
	raw, ok := c.data.Load(key)
	if !ok {
		return nil, false
	}
	entry := raw.(l1Entry)
	if time.Now().After(entry.expiresAt) {
		c.data.Delete(key)
		return nil, false
	}
	return entry.value, true
}

func (c *InMemoryL1) Set(key string, val []byte, ttl time.Duration) {
	c.data.Store(key, l1Entry{
		value:     val,
		expiresAt: time.Now().Add(ttl),
	})
}

func (c *InMemoryL1) Delete(key string) {
	c.data.Delete(key)
}

// MockRedisL2 симулирует удаленный Redis с сетевой задержкой.
type MockRedisL2 struct {
	mu      sync.RWMutex
	storage map[string]l1Entry
	latency time.Duration
}

func NewMockRedisL2(latency time.Duration) *MockRedisL2 {
	return &MockRedisL2{
		storage: make(map[string]l1Entry),
		latency: latency,
	}
}

func (r *MockRedisL2) Get(ctx context.Context, key string) ([]byte, error) {
	time.Sleep(r.latency) // Имитация сетевого RTT
	r.mu.RLock()
	defer r.mu.RUnlock()

	entry, ok := r.storage[key]
	if !ok || time.Now().After(entry.expiresAt) {
		return nil, ErrCacheMiss
	}
	return entry.value, nil
}

func (r *MockRedisL2) Set(ctx context.Context, key string, val []byte, ttl time.Duration) error {
	time.Sleep(r.latency)
	r.mu.Lock()
	defer r.mu.Unlock()

	r.storage[key] = l1Entry{
		value:     val,
		expiresAt: time.Now().Add(ttl),
	}
	return nil
}

func (r *MockRedisL2) Delete(ctx context.Context, key string) error {
	time.Sleep(r.latency)
	r.mu.Lock()
	defer r.mu.Unlock()
	delete(r.storage, key)
	return nil
}

// MultiLevelCache оркестрирует согласованную работу L1 и L2.
type MultiLevelCache struct {
	l1 L1Cache
	l2 L2Cache
}

func NewMultiLevelCache(l1 L1Cache, l2 L2Cache) *MultiLevelCache {
	return &MultiLevelCache{l1: l1, l2: l2}
}

// GetOrLoad реализует каскадное чтение с обратным заполнением L1 (backfill).
func (m *MultiLevelCache) GetOrLoad(
	ctx context.Context,
	key string,
	fetcher func(ctx context.Context) ([]byte, error),
	ttlL1, ttlL2 time.Duration,
) ([]byte, string, error) {
	// 1. Поиск в L1
	if val, ok := m.l1.Get(key); ok {
		return val, "L1_HIT", nil
	}

	// 2. Поиск в L2
	val, err := m.l2.Get(ctx, key)
	if err == nil {
		m.l1.Set(key, val, ttlL1) // Backfill L1
		return val, "L2_HIT", nil
	}

	// 3. Полный промах -> вызов загрузчика БД
	freshVal, err := fetcher(ctx)
	if err != nil {
		return nil, "MISS", err
	}

	// 4. Прогрев L2 и L1
	_ = m.l2.Set(ctx, key, freshVal, ttlL2)
	m.l1.Set(key, freshVal, ttlL1)

	return freshVal, "DB_HIT", nil
}

func main() {
	ctx := context.Background()
	l1 := NewInMemoryL1()
	l2 := NewMockRedisL2(10 * time.Millisecond)
	mlc := NewMultiLevelCache(l1, l2)

	key := "product:991"
	dbCalls := 0

	fetcher := func(ctx context.Context) ([]byte, error) {
		dbCalls++
		time.Sleep(40 * time.Millisecond) // Имитация задержки Postgres
		return []byte(`{"id": 991, "title": "Go Concurrency Book", "stock": 14}`), nil
	}

	// 1. Первый холодный запрос -> идет в БД
	t0 := time.Now()
	v, src, _ := mlc.GetOrLoad(ctx, key, fetcher, 2*time.Second, 10*time.Second)
	fmt.Printf("[1] Источник: %s, Время: %v, Данные: %s\n", src, time.Since(t0), string(v))

	// 2. Повторный запрос -> мгновенный L1
	t1 := time.Now()
	v, src, _ = mlc.GetOrLoad(ctx, key, fetcher, 2*time.Second, 10*time.Second)
	fmt.Printf("[2] Источник: %s, Время: %v\n", src, time.Since(t1))

	// 3. Инвалидируем только L1 (моделируем новый экземпляр микросервиса)
	l1.Delete(key)
	t2 := time.Now()
	v, src, _ = mlc.GetOrLoad(ctx, key, fetcher, 2*time.Second, 10*time.Second)
	fmt.Printf("[3] Источник: %s, Время: %v\n", src, time.Since(t2))

	// 4. Повторный запрос после backfill -> снова L1
	t3 := time.Now()
	v, src, _ = mlc.GetOrLoad(ctx, key, fetcher, 2*time.Second, 10*time.Second)
	fmt.Printf("[4] Источник: %s, Время: %v\n", src, time.Since(t3))

	fmt.Printf("Всего обращений к БД: %d (ожидается ровно 1)\n", dbCalls)
}
"""
            }
        ],
        "under_the_hood": "При обращении к L1 чтение происходит непосредственно из кучи или стека процесса за десятки наносекунд без системных вызовов ядра ОС. При сетевом обращении к Redis рантайм Go переводит сетевой сокет в netpoller (epoll/kqueue), паркуя текущую горутину через gopark и возвращая процессор P другим задачам. Синхронный backfill в L1 гарантирует, что следующий локальный запрос не будет тратить сетевой RTT на опрос L2.",
        "pitfalls": "Основная опасность многоуровневого кэша - рассинхронизация между репликами приложения (L1 Incoherence). Если инстанс А обновил БД и L2, инстанс Б продолжит возвращать устаревшие данные из L1 до окончания его TTL. Решение: сверхкороткий TTL для L1 (3–15 сек) либо распределенная шина инвалидации (Redis Pub/Sub).",
        "bigtech_interview": "'Как вы выберете соотношение TTL между L1 и L2 в HighLoad системе?' Ответ: L1 настраивается на короткий TTL (секунды), достаточный для сглаживания микро-всплесков (traffic bursts) и защиты от Thundering Herd. L2 в Redis хранит данные минутами/часами с добавлением случайного джиттера (10–20%), предотвращающего лавинное устаревание."
    },
    {
        "num": 2,
        "title": "Потокобезопасный In-Memory L1 кэш на sync.RWMutex",
        "task": "Реализуйте эффективный и безопасный локальный L1-кэш на чистом Go. Чтобы избежать глобальной блокировки при миллионах конкурентных обращений, спроектируйте шардированную структуру кэша (Sharded Cache) из 32 или 64 шардов. Каждый шард должен управляться собственным sync.RWMutex и иметь хеширование ключей по алгоритму FNV-1a. Реализуйте методы Get, Set, Delete и фоновую горутину плановой очистки истекших ключей (TTL cleanup).",
        "theory": "Использование единого `sync.RWMutex` для всего словаря кэша `map[string]Item` под нагрузкой в 100 000+ RPS приводит к тяжелой конкуренции за мьютекс (Mutex Contention) и деградации кеш-линий процессора (Cache-line bouncing). Стандартная `sync.Map` оптимизирована только под сценарии append-only и частые стабильные чтения, но уступает обычной мапе при постоянных частых модификациях и обновлениях TTL.\n\nШардирование (Sharding / Striping) делит адресное пространство ключей на N независимых шардов (обычно степень двойки, например 32). По хешу ключа (например, FNV-1a) запрос направляется строго в один шард: `shard = hash(key) & (N - 1)`. Это снижает вероятность пересечения горутин на одном мьютексе в 32 раза.",
        "step_by_step": "1. Создайте структуру `cacheShard` с `sync.RWMutex` и картой `map[string]cacheItem`.\n2. Реализуйте функцию FNV-1a хеширования строки в uint64.\n3. Спроектируйте `ShardedL1Cache` с фиксированным слайсом шардов (константа `shardCount = 32`).\n4. Добавьте метод `getShard(key string) *cacheShard` с быстрым побитовым маскированием.\n5. Запустите фоновую горутину, которая с интервалом раз в 5 секунд очищает просроченные записи по каждому шарду.",
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

const (
	shardCount = 32
	shardMask  = shardCount - 1
)

type cacheItem struct {
	value     []byte
	expiresAt time.Time
}

type cacheShard struct {
	mu      sync.RWMutex
	entries map[string]cacheItem
}

// ShardedL1Cache представляет масштабируемый L1-кэш с шардированием.
type ShardedL1Cache struct {
	shards [shardCount]*cacheShard
}

func NewShardedL1Cache(ctx context.Context) *ShardedL1Cache {
	c := &ShardedL1Cache{}
	for i := 0; i < shardCount; i++ {
		c.shards[i] = &cacheShard{
			entries: make(map[string]cacheItem),
		}
	}

	// Фоновая горутина плановой очистки истекших записей
	go c.startCleanupWorker(ctx, 2*time.Second)

	return c
}

// fnv1a быстрый некриптографический 64-битный хеш
func fnv1a(key string) uint64 {
	var h uint64 = 14695981039346656037
	for i := 0; i < len(key); i++ {
		h ^= uint64(key[i])
		h *= 1099511628211
	}
	return h
}

func (c *ShardedL1Cache) getShard(key string) *cacheShard {
	idx := fnv1a(key) & uint64(shardMask)
	return c.shards[idx]
}

func (c *ShardedL1Cache) Get(key string) ([]byte, bool) {
	shard := c.getShard(key)
	shard.mu.RLock()
	item, ok := shard.entries[key]
	shard.mu.RUnlock()

	if !ok {
		return nil, false
	}
	if time.Now().After(item.expiresAt) {
		// Ленивое удаление просроченного ключа
		shard.mu.Lock()
		delete(shard.entries, key)
		shard.mu.Unlock()
		return nil, false
	}
	return item.value, true
}

func (c *ShardedL1Cache) Set(key string, val []byte, ttl time.Duration) {
	shard := c.getShard(key)
	shard.mu.Lock()
	shard.entries[key] = cacheItem{
		value:     val,
		expiresAt: time.Now().Add(ttl),
	}
	shard.mu.Unlock()
}

func (c *ShardedL1Cache) Delete(key string) {
	shard := c.getShard(key)
	shard.mu.Lock()
	delete(shard.entries, key)
	shard.mu.Unlock()
}

func (c *ShardedL1Cache) startCleanupWorker(ctx context.Context, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case now := <-ticker.C:
			for i := 0; i < shardCount; i++ {
				shard := c.shards[i]
				shard.mu.Lock()
				for k, it := range shard.entries {
					if now.After(it.expiresAt) {
						delete(shard.entries, k)
					}
				}
				shard.mu.Unlock()
			}
		}
	}
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	cache := NewShardedL1Cache(ctx)

	// Заполняем кэш ключами
	for i := 1; i <= 10; i++ {
		k := fmt.Sprintf("session:user:%d", i)
		v := fmt.Sprintf("token_data_%d", i*100)
		ttl := 300 * time.Millisecond
		if i%2 == 0 {
			ttl = 5 * time.Second
		}
		cache.Set(k, []byte(v), ttl)
	}

	fmt.Println("Проверяем наличие ключей сразу после вставки:")
	for i := 1; i <= 4; i++ {
		k := fmt.Sprintf("session:user:%d", i)
		val, ok := cache.Get(k)
		fmt.Printf("Key: %s, Found: %v, Val: %s\n", k, ok, string(val))
	}

	fmt.Println("\nЖдем 500мс для истечения ключей с коротким TTL...")
	time.Sleep(500 * time.Millisecond)

	for i := 1; i <= 4; i++ {
		k := fmt.Sprintf("session:user:%d", i)
		val, ok := cache.Get(k)
		fmt.Printf("Key: %s, Found: %v (ожидалось: %v)\n", k, ok, i%2 == 0)
		_ = val
	}
}
"""
            }
        ],
        "under_the_hood": "Побитовое маскирование `idx = hash & (N - 1)` требует, чтобы число шардов N было степенью двойки (32, 64, 128). На уровне CPU ассемблерная инструкция AND выполняется за 1 такт, в то время как операция деления по модулю (DIV / IDIV) занимает 10–30 тактов. Разделение данных на независимые шарды предотвращает false sharing процессорных строк кэша L1/L2 ядер CPU.",
        "pitfalls": "Фоновый воркер очистки не должен держать блокировку шарда слишком долго. Если в одном шарде накопились сотни тысяч записей, блокирующий проход по мапе заблокирует все параллельные Get/Set запросы к этому шарду. В продакшене очистку выполняют порциями (batch cleaning) с вызовом runtime.Gosched().",
        "bigtech_interview": "'Почему стандартная sync.Map не подходит для роли высоконагруженного L1 кэша?' Ответ: sync.Map идеальна при чтении стабильного множества ключей. Но при постоянном создании новых ключей и инвалидации старых sync.Map переходит в режим 'misses >= len(read)', вынуждена брать внутренний мьютекс и копировать dirty-карту, что вызывает резкую деградацию производительности и всплеск аллокаций."
    },
    {
        "num": 3,
        "title": "Проблема GC Overhead при миллионах ключей в L1",
        "task": "Исследуйте влияние огромного количества указателей в локальной памяти на время фазы Mark сборщика мусора Go (GC Mark Phase). Напишите тестовую программу, которая аллоцирует 2 миллиона записей в обычной мапе указателей map[string]*Item. Замерьте время пауз GC с помощью runtime.ReadMemStats и метрики gcPauseTotal. Затем перепишите структуру на хранение значений без указателей (value types или сериализованные байты) и продемонстрируйте многократное сокращение накладных расходов GC.",
        "theory": "Сборщик мусора Go использует триколорный concurrent mark-sweep алгоритм. Во время фазы трассировки (Marking) рантайм обязан обойти абсолютно все объекты в памяти, содержащие указатели, чтобы определить их достижимость.\n\nЕсли в памяти процесса хранится мапа `map[string]*User` с 5 000 000 элементов, сборщик мусора вынужден просканировать не менее 10 000 000 указателей в каждом цикле сборки (даже если ни один из этих элементов не изменился!). Это приводит к утилизации 25% CPU на GC Assist и росту задержек p99 до десятков миллисекунд.\n\nОптимизация компилятора Go: Если тип ключа и тип значения в карте не содержат указателей (например, `map[uint64][32]byte`), рантайм Go маркирует бакеты этой мапы как noscan! Сборщик мусора полностью игнорирует такую мапу при трассировке кучи.",
        "step_by_step": "1. Создайте структуру `PointerItem` с полями-указателями и заполните `map[string]*PointerItem` 1 000 000 элементов.\n2. Вызовите `runtime.GC()` и замерьте затраченное время через `time.Since`.\n3. Создайте оптимизированную структуру `NoPointerItem` со скалярными полями и сравните длительность `runtime.GC()`.\n4. Проанализируйте `MemStats.PauseTotalNs` и `NumGC`.\n5. Сделайте вывод об архитектуре Zero-GC кэшей.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"runtime"
	"strconv"
	"time"
)

type PointerItem struct {
	ID        *string
	Title     *string
	Payload   *[]byte
	CreatedAt *time.Time
}

type NoPointerItem struct {
	ID        uint64
	Timestamp int64
	Data      [64]byte
}

const itemCount = 500_000

func benchPointerMap() time.Duration {
	runtime.GC()
	var m1, m2 runtime.MemStats
	runtime.ReadMemStats(&m1)

	// Аллоцируем мапу с огромным числом указателей
	data := make(map[string]*PointerItem, itemCount)
	now := time.Now()
	for i := 0; i < itemCount; i++ {
		idStr := strconv.Itoa(i)
		titleStr := "title_" + idStr
		b := []byte("some payload data")
		data[idStr] = &PointerItem{
			ID:        &idStr,
			Title:     &titleStr,
			Payload:   &b,
			CreatedAt: &now,
		}
	}

	start := time.Now()
	runtime.GC() // Принудительный прогон сборщика мусора
	gcDuration := time.Since(start)

	runtime.ReadMemStats(&m2)
	runtime.KeepAlive(data)

	return gcDuration
}

func benchNoPointerMap() time.Duration {
	runtime.GC()

	// Ключи и значения БЕЗ указателей -> компилятор включает флаг noscan!
	data := make(map[uint64]NoPointerItem, itemCount)
	for i := 0; i < itemCount; i++ {
		var item NoPointerItem
		item.ID = uint64(i)
		item.Timestamp = time.Now().UnixNano()
		data[uint64(i)] = item
	}

	start := time.Now()
	runtime.GC() // GC полностью пропускает тело этой мапы!
	gcDuration := time.Since(start)

	runtime.KeepAlive(data)
	return gcDuration
}

func main() {
	fmt.Printf("Тестирование накладных расходов GC на %d элементов...\n\n", itemCount)

	fmt.Println("1. Запуск теста с map[string]*PointerItem (миллионы указателей)...")
	pDuration := benchPointerMap()
	fmt.Printf("   Длительность runtime.GC(): %v\n\n", pDuration)

	// Очищаем кучу
	runtime.GC()
	time.Sleep(100 * time.Millisecond)

	fmt.Println("2. Запуск теста с map[uint64]NoPointerItem (noscan мапа без указателей)...")
	npDuration := benchNoPointerMap()
	fmt.Printf("   Длительность runtime.GC(): %v\n\n", npDuration)

	speedup := float64(pDuration) / float64(npDuration)
	fmt.Printf("Итог: отсутствие указателей ускорило фазу GC в %.1f раз!\n", speedup)
}
"""
            }
        ],
        "under_the_hood": "В исходниках рантайма Go (src/runtime/map.go) тип бакета bmap проверяется компилятором. Если тип ключа и тип элемента удовлетворяют свойству !type.HasPointers(), флаг бакета помечается как bucketHasNoPointers. При вызове heap scan сборщик мусора не углубляется в память бакетов мапы, экономя такты CPU и ресурсы шины памяти.",
        "pitfalls": "Строка string в Go - это структура `struct { Data unsafe.Pointer; Len int }`. То есть тип string содержит указатель! Поэтому мапа `map[string]int` все равно требует сканирования заголовков строк. Полный Zero-GC достигается либо числовыми ключами (uint64), либо хранением сериализованных байт в едином монолитном буфере (BigCache).",
        "bigtech_interview": "'Как хранить 50 миллионов объектов в оперативной памяти одного Go-процесса без пауз GC?' Ответ: Использовать монолитные байтовые кольцевые буферы (Zero-GC кэши типа BigCache или FreeCache), хранить данные в мапах `map[uint64]uint32` (где значение - смещение в слайсе `[]byte`), либо размещать память вне кучи через `mmap` / off-heap аллокации."
    },
    {
        "num": 4,
        "title": "Интеграция Zero-GC локального кэша (BigCache / FreeCache)",
        "task": "Реализуйте упрощенный Zero-GC кэш, использующий архитектуру BigCache. Структура должна хранить хеш-таблицу смещений map[uint64]uint32 (где ключ - FNV хеш строки, а значение - смещение в байтовом буфере) и единый байтовый слайс-буфер []byte. При записи нового элемента сериализуйте длину ключа, ключ, длину значения, значение и метку времени в хвост буфера. Продемонстрируйте работу методов Put и Get без единой аллокации промежуточных объектов в куче.",
        "theory": "Библиотека `allegro/bigcache` стала стандартом де-факто для высокопроизводительных in-memory L1 кэшей на Go благодаря трем ключевым архитектурным решениям:\n1. **Шардирование памяти**: Наличие N независимых шардов для минимизации конкуренции за локи.\n2. **Zero-GC мапа**: Внутри каждого шарда используется мапа `map[uint64]uint32`, где ключ — 64-битный хеш, а значение — смещение (offset) в байтовом массиве. Так как эта мапа не содержит указателей, GC ее не сканирует.\n3. **Циклический байтовый буфер**: Данные сохраняются последовательно в один гигантский срез `[]byte`. Вытеснение по FIFO происходит простым сдвигом указателя головы очереди без дефрагментации памяти.",
        "step_by_step": "1. Спроектируйте структуру бинарного заголовка записи (8 байт timestamp + 4 байта keyLen + 4 байта valLen).\n2. Создайте структуру `ZeroGCShard` с `sync.RWMutex`, `map[uint64]uint32` и слайсом `buffer []byte`.\n3. Реализуйте метод `Set`: запишите заголовок, ключ и значение в конец буфера, сохранив смещение в мапу.\n4. Реализуйте метод `Get`: найдите смещение по хешу, прочитайте бинарный заголовок, валидируйте ключ и верните срез байт.\n5. Напишите тест в main.go, демонстрирующий корректное извлечение и валидацию данных.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"encoding/binary"
	"errors"
	"fmt"
	"sync"
	"time"
)

var (
	ErrKeyNotFound = errors.New("zero-gc: key not found")
	ErrExpired     = errors.New("zero-gc: entry expired")
)

// ZeroGCCache реализует структуру кэша без указателей в теле записей.
type ZeroGCCache struct {
	mu     sync.RWMutex
	index  map[uint64]uint32 // hash -> offset в buffer (noscan мапа!)
	buffer []byte            // единый срез памяти без указателей
}

func NewZeroGCCache(initialCap int) *ZeroGCCache {
	return &ZeroGCCache{
		index:  make(map[uint64]uint32),
		buffer: make([]byte, 0, initialCap),
	}
}

func hashString(s string) uint64 {
	var h uint64 = 14695981039346656037
	for i := 0; i < len(s); i++ {
		h ^= uint64(s[i])
		h *= 1099511628211
	}
	return h
}

// Формат записи в buffer:
// [0..8]   ExpiresAt (int64 unix nano)
// [8..12]  KeyLen (uint32)
// [12..16] ValLen (uint32)
// [16..16+KeyLen] Key bytes
// [16+KeyLen..]   Val bytes

func (c *ZeroGCCache) Set(key string, val []byte, ttl time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()

	h := hashString(key)
	offset := uint32(len(c.buffer))

	expNano := time.Now().Add(ttl).UnixNano()
	kLen := uint32(len(key))
	vLen := uint32(len(val))

	var header [16]byte
	binary.LittleEndian.PutUint64(header[0:8], uint64(expNano))
	binary.LittleEndian.PutUint32(header[8:12], kLen)
	binary.LittleEndian.PutUint32(header[12:16], vLen)

	// Дописываем заголовок, ключ и значение в монолитный буфер
	c.buffer = append(c.buffer, header[:]...)
	c.buffer = append(c.buffer, key...)
	c.buffer = append(c.buffer, val...)

	c.index[h] = offset
}

func (c *ZeroGCCache) Get(key string) ([]byte, error) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	h := hashString(key)
	offset, ok := c.index[h]
	if !ok {
		return nil, ErrKeyNotFound
	}

	// Читаем заголовок
	if int(offset)+16 > len(c.buffer) {
		return nil, ErrKeyNotFound
	}
	header := c.buffer[offset : offset+16]
	expNano := int64(binary.LittleEndian.Uint64(header[0:8]))
	kLen := int(binary.LittleEndian.Uint32(header[8:12]))
	vLen := int(binary.LittleEndian.Uint32(header[12:16]))

	if time.Now().UnixNano() > expNano {
		return nil, ErrExpired
	}

	keyStart := int(offset) + 16
	keyEnd := keyStart + kLen
	valEnd := keyEnd + vLen

	// Сверяем ключ во избежание коллизий хешей
	storedKey := string(c.buffer[keyStart:keyEnd])
	if storedKey != key {
		return nil, ErrKeyNotFound // Хеш-коллизия
	}

	// Возвращаем копию значения, чтобы изолировать буфер
	res := make([]byte, vLen)
	copy(res, c.buffer[keyEnd:valEnd])
	return res, nil
}

func main() {
	cache := NewZeroGCCache(1024 * 1024)

	cache.Set("auth:token:user_42", []byte("bearer_jwt_secret_999"), 2*time.Second)
	cache.Set("config:feature_flag", []byte("true"), 500*time.Millisecond)

	val, err := cache.Get("auth:token:user_42")
	fmt.Printf("auth:token:user_42 -> %s (err: %v)\n", string(val), err)

	val, err = cache.Get("config:feature_flag")
	fmt.Printf("config:feature_flag -> %s (err: %v)\n", string(val), err)

	fmt.Println("\nЖдем 600мс для экспирации флага...")
	time.Sleep(600 * time.Millisecond)

	_, err = cache.Get("config:feature_flag")
	fmt.Printf("config:feature_flag после ожидания -> (err: %v, ожидалось expired)\n", err)

	val, err = cache.Get("auth:token:user_42")
	fmt.Printf("auth:token:user_42 по-прежнему активен -> %s (err: %v)\n", string(val), err)
}
"""
            }
        ],
        "under_the_hood": "BigCache и FreeCache используют трюк со срезом памяти. Вместо миллиона отдельных аллокаций в куче создается один или несколько огромных массивов `[]byte`. Для GC один слайс на 1 ГБ байтов — это ровно один объект в куче, содержащий ноль указателей внутри себя. Обход такого среза занимает у GC менее одной микросекунды независимо от того, сколько записей внутри него находится.",
        "pitfalls": "Поскольку байтовый буфер BigCache работает по принципу циклической очереди (FIFO ring-buffer), обновление существующего ключа не перезаписывает старую запись на месте, а аппендит новую версию в хвост. При интенсивных обновлениях одних и тех же ключей буфер может быстро забиться устаревшими данными до момента их перезаписи циклом.",
        "bigtech_interview": "'Какая разница между BigCache и FreeCache?' Ответ: BigCache использует FIFO вытеснение по времени (TTL) и последовательный кольцевой буфер, идеален при равномерном времени жизни ключей. FreeCache разбивает память на страницы по 512 КБ и реализует алгоритм кольцевого буфера с сегментами и подобием LRU, что эффективнее при неравномерных размерах объектов, но дает чуть больший оверхед."
    },
    {
        "num": 5,
        "title": "Паттерн Cache-Aside (Lazy Loading)",
        "task": "Реализуйте канонический паттерн Cache-Aside (ленивая загрузка кэша) в виде обобщенной Go-структуры CacheAsideService[T any]. Сервис должен инкапсулировать вызов репозитория БД и многоуровневого кэша. Реализуйте метод Get(ctx context.Context, id int64) (T, error) и метод Invalidate(ctx context.Context, id int64) error. Особое внимание уделите graceful degradation: если кэш возвращает сетевую ошибку (таймаут или отказ соединения), сервис не должен падать, а обязан прозрачно прочитать данные из БД и залогировать ошибку кэша.",
        "theory": "Паттерн Cache-Aside (он же Lazy Loading) — наиболее распространенный паттерн кэширования в бэкенд-архитектуре. Логика работы:\n1. Приложение запрашивает данные у кэша.\n2. Если данные есть (Cache Hit), они немедленно возвращаются клиенту.\n3. Если данных нет (Cache Miss), приложение делает запрос к базе данных.\n4. Полученные из БД данные асинхронно или синхронно сохраняются в кэш с заданным TTL.\n5. При обновлении или удалении сущности приложение сначала фиксирует изменения в БД, а затем инвалидирует (удаляет) ключ из кэша (Write-then-Invalidate).\n\nКритическое правило надежности: Кэш — это всего лишь оптимизация. При полном отказе кэш-сервера бизнес-логика сервиса обязана продолжить функционировать через БД.",
        "step_by_step": "1. Объявите интерфейсы `Store` (кэш) и `Repository[T]` (БД).\n2. Реализуйте структуру `CacheAsideService[T]`.\n3. В методе `Get` перехватывайте ошибки кэша: при ошибке логируйте инцидент и делайте фолбек на БД.\n4. При успешном чтении из БД запишите данные в кэш, игнорируя возможный сбой записи (Best-Effort caching).\n5. В методе `Update` сначала вызывайте БД, а при успехе отправляйте команду удаления в кэш.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"os"
	"sync"
	"time"
)

var ErrNotFound = errors.New("repository: entity not found")

type UserProfile struct {
	ID       int64  `json:"id"`
	Username string `json:"username"`
	Email    string `json:"email"`
}

type CacheStorage interface {
	Get(ctx context.Context, key string) ([]byte, error)
	Set(ctx context.Context, key string, val []byte, ttl time.Duration) error
	Delete(ctx context.Context, key string) error
}

type UserRepository interface {
	FindByID(ctx context.Context, id int64) (*UserProfile, error)
	Update(ctx context.Context, u *UserProfile) error
}

// CacheAsideService инкапсулирует логику ленивой загрузки и отказоустойчивости.
type CacheAsideService struct {
	repo   UserRepository
	cache  CacheStorage
	ttl    time.Duration
	logger *slog.Logger
}

func NewCacheAsideService(repo UserRepository, cache CacheStorage, ttl time.Duration, logger *slog.Logger) *CacheAsideService {
	return &CacheAsideService{
		repo:   repo,
		cache:  cache,
		ttl:    ttl,
		logger: logger,
	}
}

func (s *CacheAsideService) makeKey(id int64) string {
	return fmt.Sprintf("user:profile:%d", id)
}

func (s *CacheAsideService) Get(ctx context.Context, id int64) (*UserProfile, error) {
	key := s.makeKey(id)

	// 1. Попытка чтения из кэша
	raw, err := s.cache.Get(ctx, key)
	if err == nil {
		var user UserProfile
		if err := json.Unmarshal(raw, &user); err == nil {
			return &user, nil
		}
	} else {
		// Логируем сбой кэша, но НЕ прерываем выполнение (Graceful Degradation)
		s.logger.Warn("кэш недоступен, фолбек на БД", "key", key, "error", err)
	}

	// 2. Cache Miss или сбой кэша -> Запрос в БД
	user, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}

	// 3. Асинхронная запись в кэш
	if serialized, err := json.Marshal(user); err == nil {
		go func() {
			setCtx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()
			if err := s.cache.Set(setCtx, key, serialized, s.ttl); err != nil {
				s.logger.Error("ошибка заполнения кэша", "key", key, "error", err)
			}
		}()
	}

	return user, nil
}

func (s *CacheAsideService) Update(ctx context.Context, u *UserProfile) error {
	// Сначала фиксируем в основном хранилище
	if err := s.repo.Update(ctx, u); err != nil {
		return err
	}

	// Затем инвалидируем кэш
	key := s.makeKey(u.ID)
	if err := s.cache.Delete(ctx, key); err != nil {
		s.logger.Error("ошибка инвалидации кэша при обновлении", "key", key, "error", err)
	}
	return nil
}

// Мок репозитория и кэша
type mockDB struct {
	mu    sync.Mutex
	users map[int64]*UserProfile
}

func (d *mockDB) FindByID(ctx context.Context, id int64) (*UserProfile, error) {
	d.mu.Lock()
	defer d.mu.Unlock()
	u, ok := d.users[id]
	if !ok {
		return nil, ErrNotFound
	}
	return u, nil
}

func (d *mockDB) Update(ctx context.Context, u *UserProfile) error {
	d.mu.Lock()
	defer d.mu.Unlock()
	d.users[u.ID] = u
	return nil
}

type memoryCache struct {
	mu      sync.Mutex
	data    map[string][]byte
	downErr error
}

func (m *memoryCache) Get(ctx context.Context, key string) ([]byte, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	if m.downErr != nil {
		return nil, m.downErr
	}
	val, ok := m.data[key]
	if !ok {
		return nil, errors.New("miss")
	}
	return val, nil
}

func (m *memoryCache) Set(ctx context.Context, key string, val []byte, ttl time.Duration) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	if m.downErr != nil {
		return m.downErr
	}
	m.data[key] = val
	return nil
}

func (m *memoryCache) Delete(ctx context.Context, key string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	delete(m.data, key)
	return nil
}

func main() {
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))
	db := &mockDB{
		users: map[int64]*UserProfile{
			1: {ID: 1, Username: "alex_staff", Email: "alex@lead.com"},
		},
	}
	cache := &memoryCache{data: make(map[string][]byte)}

	svc := NewCacheAsideService(db, cache, 10*time.Minute, logger)
	ctx := context.Background()

	// 1. Первый запрос (холодный кэш)
	u1, _ := svc.Get(ctx, 1)
	fmt.Printf("Получен юзер (DB Miss -> Set): %+v\n", u1)

	time.Sleep(50 * time.Millisecond) // Ждем завершения фоновой записи

	// 2. Второй запрос (попадание в кэш)
	u2, _ := svc.Get(ctx, 1)
	fmt.Printf("Получен юзер (Cache Hit): %+v\n", u2)

	// 3. Имитация падения кэш-сервера
	cache.downErr = errors.New("dial tcp 127.0.0.1:6379: connection refused")
	fmt.Println("\nКэш-сервер упал! Тестируем устойчивость...")

	u3, err := svc.Get(ctx, 1)
	fmt.Printf("Получен юзер при упавшем кэше: %+v, err: %v\n", u3, err)
}
"""
            }
        ],
        "under_the_hood": "При сетевой ошибке Redis драйвер возвращает ошибку ввода-вывода (net.OpError). Сервис проверяет ошибку и вместо передачи 500 Internal Server Error клиенту прозрачно переключается на прямой SQL-запрос. Чтобы медленный или зависший кэш не заблокировал все горутины запросов, вызовы к кэшу оборачиваются жестким коротким таймаутом (например, 20–50 мс через context.WithTimeout).",
        "pitfalls": "Опасность асинхронного сохранения в кэш: если фоновая горутина берет контекст родительского HTTP-запроса, то при закрытии клиентом соединения контекст отменяется (context canceled) и `cache.Set` падает с ошибкой. В фоновую горутину всегда передается отвязанный контекст (`context.Background()` или `context.WithoutCancel(ctx)`).",
        "bigtech_interview": "'Что лучше при изменении данных: инвалидировать ключ кэша (Delete) или сразу перезаписывать новым значением (Set)?' Ответ: Инвалидация (Delete) значительно безопаснее! Если два потока одновременно обновляют БД в разном порядке, при перезаписи кэша (Set) возможна инверсия: старое значение запишется после нового и останется там навсегда. Инвалидация же гарантирует, что следующее чтение гарантированно возьмет актуальную версию из базы."
    },
    {
        "num": 6,
        "title": "Демонстрация проблемы Cache Stampede (Thundering Herd)",
        "task": "Смоделируйте проблему 'набегающего стада' (Cache Stampede / Thundering Herd). Напишите тестовый сценарий, где популярный ключ кэша (например, баннер главной страницы или карточка товара на распродаже) внезапно истекает по TTL. Запустите 500 параллельных горутин, одновременно запрашивающих этот ключ. Покажите, как все 500 горутин одновременно получают Cache Miss и штурмуют имитатор базы данных, исчерпывая лимит подключений и вызывая отказ обслуживания.",
        "theory": "Cache Stampede (эффект набегающего стада) возникает, когда высоконагруженный ключ кэша (на который приходит, например, 10 000 RPS) внезапно инвалидируется или истекает по TTL.\n\nВ микросекунду после экспирации все входящие параллельные запросы получают `Cache Miss`. Каждый из них независимо друг от друга решает пойти в базу данных, чтобы пересчитать значение. В результате база данных мгновенно получает цунами из тысяч тяжелых идентичных запросов. Пул соединений БД исчерпывается, задержки взлетают до секунд, база падает от перегрузки по CPU/IO, а микросервисы начинают отказывать по таймаутам (каскадный сбой всей системы).",
        "step_by_step": "1. Создайте структуру `MockDatabase` со счетчиком активных параллельных подключений и максимальным лимитом (например, 10).\n2. Напишите метод базы `HeavyQuery`, выполняющий работу за 100 мс, и возвращающий ошибку `ErrPoolExhausted`, если лимит превышен.\n3. Запустите 1000 горутин, обращающихся к сервису за одним и тем же ключом после истечения кэша.\n4. Зафиксируйте количество успешных и упавших запросов.\n5. Сделайте вывод о необходимости защитных барьеров (singleflight, mutex locks, probabilistic early expiration).",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

var ErrPoolExhausted = errors.New("postgres: connection pool exhausted (max 10 connections)")

type MockDatabase struct {
	maxConns      int32
	activeConns   int32
	totalQueries  int64
	failedQueries int64
}

func NewMockDatabase(maxConns int32) *MockDatabase {
	return &MockDatabase{maxConns: maxConns}
}

func (db *MockDatabase) ExecuteHeavyQuery(ctx context.Context, id string) (string, error) {
	atomic.AddInt64(&db.totalQueries, 1)

	// Пытаемся захватить соединение из пула
	curr := atomic.AddInt32(&db.activeConns, 1)
	defer atomic.AddInt32(&db.activeConns, -1)

	if curr > db.maxConns {
		atomic.AddInt64(&db.failedQueries, 1)
		return "", ErrPoolExhausted
	}

	// Имитация тяжелого SQL-запроса с агрегациями (50 мс)
	time.Sleep(50 * time.Millisecond)
	return fmt.Sprintf("data_for_%s", id), nil
}

func main() {
	db := NewMockDatabase(10) // Пул всего на 10 соединений
	var cache sync.Map        // Простой кэш

	key := "hot_banner:black_friday"
	// Ключ изначально отсутствует или истек!

	concurrency := 200
	var wg sync.WaitGroup
	wg.Add(concurrency)

	var successCount int64
	var errorCount int64

	fmt.Printf("Запуск %d параллельных запросов к истекшему ключу без защиты...\n", concurrency)
	start := time.Now()

	for i := 0; i < concurrency; i++ {
		go func() {
			defer wg.Done()

			// 1. Проверяем кэш
			if val, ok := cache.Load(key); ok {
				atomic.AddInt64(&successCount, 1)
				_ = val
				return
			}

			// 2. Cache Miss -> Все горутины одновременно бегут в БД!
			res, err := db.ExecuteHeavyQuery(context.Background(), key)
			if err != nil {
				atomic.AddInt64(&errorCount, 1)
				return
			}

			cache.Store(key, res)
			atomic.AddInt64(&successCount, 1)
		}()
	}

	wg.Wait()
	duration := time.Since(start)

	fmt.Printf("\n=== РЕЗУЛЬТАТЫ ЭКСПЕРИМЕНТА THUNDERING HERD ===\n")
	fmt.Printf("Общее время выполнения: %v\n", duration)
	fmt.Printf("Всего запросов в БД: %d\n", db.totalQueries)
	fmt.Printf("Успешных запросов: %d\n", successCount)
	fmt.Printf("Упавших с ошибкой переполнения пула: %d\n", errorCount)
	fmt.Printf("Процент отказов базы данных: %.1f%%\n", float64(errorCount)/float64(concurrency)*100)
}
"""
            }
        ],
        "under_the_hood": "В операционной системе и сетевых демонах Thundering Herd возникает при пробуждении сотен спящих процессов/потоков по одному событию (например, epoll на общем сокете). В контексте кэширования все горутины, заблокированные или выполняющие чтение, одновременно видят `nil` и генерируют сетевые пакеты TCP SYN / Query в сторону СУБД. Коннекшн-пул базы данных упирается в `max_connections`, вызывая ошибку `too many clients already`.",
        "pitfalls": "Наивная попытка решить проблему через обычный `sync.Mutex` в месте вызова базы данных заблокирует все потоки на одном сервере, но не защитит распределенную базу, если у вас 50 подов в Kubernetes. Для распределенной защиты требуется либо алгоритм XFetch, либо распределенный Singleflight/Redlock.",
        "bigtech_interview": "'Как математически оценить вероятность Cache Stampede?' Ответ: Вероятность пропорциональна RPS запросов к ключу, умноженному на время выполнения запроса в БД: `P ~ RPS * QueryTime`. Если ключ запрашивают 2000 раз в секунду, а запрос в базу выполняется 150 мс (0.15 с), то за время выполнения первого запроса в базу прилетит 2000 * 0.15 = 300 параллельных запросов!"
    },
    {
        "num": 7,
        "title": "Дедупликация конкурентных запросов через sync/singleflight",
        "task": "Внедрите пакет `golang.org/x/sync/singleflight` для ликвидации эффекта Thundering Herd на уровне инстанса Go. Реализуйте обертку кэш-сервиса, которая при возникновении Cache Miss объединяет идентичные параллельные запросы к одному ключу с помощью singleflight.Group. Покажите, что при 1000 конкурентных запросов к пустому ключу выполняется ровно один SQL-запрос к базе данных, а все 1000 горутин получают одинаковый корректный результат без ошибок.",
        "theory": "Пакет `singleflight` предоставляет механизм подавления дублирующих вызовов функций (Duplicate Function Call Suppression). Метод `Group.Do(key, fn)` гарантирует, что для одного строкового ключа в текущий момент времени выполняется не более одного вызова функции `fn`.\n\nЕсли первая горутина вызвала `Do('product:123', fetchDB)` и запрос ушел в сеть, то все последующие горутины, вызывающие `Do` с этим же ключом, не инициируют новый поход в БД. Они регистрируются во внутреннем списке ожидания на `sync.WaitGroup` и засыпают. Когда первый запрос возвращает результат или ошибку, singleflight пробуждает всех ожидающих и отдает им копию результата.",
        "step_by_step": "1. Подключите структуру `singleflight.Group` внутрь кэш-сервиса.\n2. В методе `Get` при промахе кэша выполните вызов через `group.Do(key, func() (interface{}, error) { ... })`.\n3. Внутри функции singleflight загрузите данные из БД и сохраните их в кэш.\n4. Проверьте возвращенный флаг `shared`, сигнализирующий о том, что результат был разделен между несколькими клиентами.\n5. Запустите 1000 параллельных горутин и убедитесь, что база обработала ровно 1 запрос.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// SingleflightGroup эмулирует golang.org/x/sync/singleflight на стандартной библиотеке
type call struct {
	wg  sync.WaitGroup
	val interface{}
	err error
}

type SingleflightGroup struct {
	mu sync.Mutex
	m  map[string]*call
}

func NewSingleflightGroup() *SingleflightGroup {
	return &SingleflightGroup{m: make(map[string]*call)}
}

func (g *SingleflightGroup) Do(key string, fn func() (interface{}, error)) (interface{}, error, bool) {
	g.mu.Lock()
	if c, ok := g.m[key]; ok {
		g.mu.Unlock()
		c.wg.Wait()
		return c.val, c.err, true // shared = true
	}

	c := new(call)
	c.wg.Add(1)
	g.m[key] = c
	g.mu.Unlock()

	c.val, c.err = fn()
	c.wg.Done()

	g.mu.Lock()
	delete(g.m, key)
	g.mu.Unlock()

	return c.val, c.err, false // shared = false (лидер запроса)
}

type SafeCacheService struct {
	cache       sync.Map
	sfGroup     *SingleflightGroup
	dbExecCount int64
}

func NewSafeCacheService() *SafeCacheService {
	return &SafeCacheService{
		sfGroup: NewSingleflightGroup(),
	}
}

func (s *SafeCacheService) Get(ctx context.Context, key string) (string, error) {
	// 1. Проверяем кэш
	if val, ok := s.cache.Load(key); ok {
		return val.(string), nil
	}

	// 2. Дедуплицируем поход в БД через singleflight
	val, err, shared := s.sfGroup.Do(key, func() (interface{}, error) {
		// Повторная проверка кэша (Double-Check)
		if v, ok := s.cache.Load(key); ok {
			return v, nil
		}

		// Выполняем реальный запрос в БД
		atomic.AddInt64(&s.dbExecCount, 1)
		time.Sleep(50 * time.Millisecond) // Имитация задержки базы
		res := fmt.Sprintf("payload_for_%s", key)

		s.cache.Store(key, res)
		return res, nil
	})

	_ = shared
	if err != nil {
		return "", err
	}
	return val.(string), nil
}

func main() {
	svc := NewSafeCacheService()
	key := "catalog:category:smartphones"

	concurrency := 1000
	var wg sync.WaitGroup
	wg.Add(concurrency)

	start := time.Now()

	// Запускаем 1000 конкурентных запросов к пустому кэшу
	for i := 0; i < concurrency; i++ {
		go func() {
			defer wg.Done()
			val, err := svc.Get(context.Background(), key)
			if err != nil || val == "" {
				fmt.Println("Ошибка запроса:", err)
			}
		}()
	}

	wg.Wait()
	duration := time.Since(start)

	fmt.Printf("Успешно выполнено %d параллельных запросов за %v\n", concurrency, duration)
	fmt.Printf("Фактических обращений к БД: %d (ИДЕАЛЬНО: ровно 1!)\n", svc.dbExecCount)
}
"""
            }
        ],
        "under_the_hood": "Внутри singleflight мапа хранит указатели на внутреннюю структуру `call`. При первом вызове создается запись, инкрементируется `wg.Add(1)` и отпускается мьютекс. Все последующие горутины находят существующий `call` и блокируются на `c.wg.Wait()`. Когда основная горутина завершает `fn()`, она вызывает `c.wg.Done()`, разблокируя всех ждущих. В рантайме Go горутины переводятся из состояния `_Gwaiting` в `_Grunnable` и распределяются по свободным процессорам P.",
        "pitfalls": "Мутация возвращаемого объекта: Если функция `fn()` возвращает указатель на структуру или срез (например, `*User` или `[]byte`), ВСЕ 1000 горутин получают ссылку на ОДИН И ТОТ ЖЕ объект в куче. Если одна из горутин решит изменить поле структуры, возникнет катастрофическая гонка данных (Data Race). Решение: возвращать иммутабельные структуры или клонировать данные перед возвратом.",
        "bigtech_interview": "'Что произойдет, если тяжелая функция внутри singleflight зависнет навсегда?' Ответ: Все входящие горутины с этим ключом зависнут на `wg.Wait()`, вызывая утечку памяти (goroutine leak) и исчерпание пула рабочих потоков. Чтобы этого избежать, используют метод `Group.DoChan`, принимающий `context.WithTimeout`, либо оборачивают тело функции жестким тайм-лимитом."
    },
    {
        "num": 8,
        "title": "Ловушка разделяемого контекста в singleflight.Group",
        "task": "Исследуйте опасную архитектурную ошибку утечки контекста при использовании singleflight: если функция singleflight захватывает контекст первой пришедшей горутины, то при досрочной отмене запроса первым клиентом (context canceled) прерывается запрос в БД для ВСЕХ остальных ожидающих горутин. Напишите код, воспроизводящий эту проблему. Затем реализуйте правильное решение: отвязку контекста (detached context / context.WithoutCancel) с независимым жестким таймаутом выполнения запроса в базу.",
        "theory": "Типичный антипаттерн использования `singleflight.Group`:\n```go\nval, err, _ := g.Do(key, func() (interface{}, error) {\n    return db.Query(ctx, key) // ОШИБКА: ctx принадлежит первой горутине!\n})\n```\nЕсли клиент №1 (первая горутина) закрыл вкладку в браузере или у него истек короткий таймаут (5 мс), HTTP-сервер отменяет `ctx.Done()`. Базовый драйвер прерывает SQL-запрос с ошибкой `context canceled`. В результате все остальные 99 горутин, у которых таймаут был больше или которые терпеливо ждали ответа, тоже получают `context canceled`!\n\nКорректный подход: Фоновый запрос к источнику правды должен выполняться с независимым корневым контекстом (`context.Background()`), либо с использованием функции Go 1.21 `context.WithoutCancel(ctx)`, защищенным выделенным сервисным таймаутом.",
        "step_by_step": "1. Смоделируйте функцию `FetchData(ctx context.Context)` с задержкой 100 мс.\n2. Покажите уязвимый вызов: передайте контекст первого клиента с таймаутом 20 мс, и контекст второго клиента с таймаутом 500 мс.\n3. Убедитесь, что второй клиент упал из-за отмены контекста первого.\n4. Исправьте код, создав отвязанный контекст с защитным таймаутом `context.WithTimeout(context.WithoutCancel(ctx), 2*time.Second)`.\n5. Докажите, что второй клиент успешно получает данные, несмотря на отмену первого.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

type SharedCall struct {
	wg  sync.WaitGroup
	val string
	err error
}

type SFGroup struct {
	mu sync.Mutex
	m  map[string]*SharedCall
}

func (g *SFGroup) Do(key string, fn func() (string, error)) (string, error) {
	g.mu.Lock()
	if c, ok := g.m[key]; ok {
		g.mu.Unlock()
		c.wg.Wait()
		return c.val, c.err
	}
	c := &SharedCall{}
	c.wg.Add(1)
	g.m[key] = c
	g.mu.Unlock()

	c.val, c.err = fn()
	c.wg.Done()

	g.mu.Lock()
	delete(g.m, key)
	g.mu.Unlock()

	return c.val, c.err
}

// DetachContext отвязывает отмену родительского контекста, сохраняя values
type detachedContext struct {
	context.Context
}

func (d detachedContext) Done() <-chan struct{} {
	return nil
}

func (d detachedContext) Err() error {
	return nil
}

func (d detachedContext) Deadline() (deadline time.Time, ok bool) {
	return time.Time{}, false
}

func DetachContext(parent context.Context) context.Context {
	return detachedContext{Context: parent}
}

func slowDBQuery(ctx context.Context) (string, error) {
	select {
	case <-time.After(80 * time.Millisecond):
		return "ultra_secure_data_payload", nil
	case <-ctx.Done():
		return "", ctx.Err()
	}
}

func main() {
	var g SFGroup
	g.m = make(map[string]*SharedCall)

	key := "report:financial:q3"

	fmt.Println("=== СЦЕНАРИЙ 1: Ошибка разделяемого контекста ===")
	// Клиент 1 (инициатор) имеет короткий таймаут 30мс
	ctx1, cancel1 := context.WithTimeout(context.Background(), 30*time.Millisecond)
	defer cancel1()

	// Клиент 2 готов ждать 300мс
	ctx2, cancel2 := context.WithTimeout(context.Background(), 300*time.Millisecond)
	defer cancel2()

	var res1, res2 string
	var err1, err2 error
	var wg sync.WaitGroup
	wg.Add(2)

	go func() {
		defer wg.Done()
		// Неправильно: передаем ctx1 напрямую в runner!
		res1, err1 = g.Do(key, func() (string, error) {
			return slowDBQuery(ctx1)
		})
	}()

	time.Sleep(5 * time.Millisecond) // Гарантируем, что горутина 2 придет второй

	go func() {
		defer wg.Done()
		res2, err2 = g.Do(key, func() (string, error) {
			return slowDBQuery(ctx2)
		})
	}()

	wg.Wait()
	fmt.Printf("Клиент 1 (30ms): res='%s', err=%v\n", res1, err1)
	fmt.Printf("Клиент 2 (300ms): res='%s', err=%v (НЕВИННАЯ ЖЕРТВА!)\n\n", res2, err2)

	fmt.Println("=== СЦЕНАРИЙ 2: Правильная изоляция контекста через Detach ===")
	ctx1Fix, cancel1Fix := context.WithTimeout(context.Background(), 30*time.Millisecond)
	defer cancel1Fix()

	ctx2Fix, cancel2Fix := context.WithTimeout(context.Background(), 300*time.Millisecond)
	defer cancel2Fix()

	wg.Add(2)

	go func() {
		defer wg.Done()
		// ПРАВИЛЬНО: Отвязываем контекст и задаем независимый таймаут на операцию
		detachedCtx, cancelOp := context.WithTimeout(DetachContext(ctx1Fix), 2*time.Second)
		defer cancelOp()

		res1, err1 = g.Do(key, func() (string, error) {
			return slowDBQuery(detachedCtx)
		})
	}()

	time.Sleep(5 * time.Millisecond)

	go func() {
		defer wg.Done()
		detachedCtx, cancelOp := context.WithTimeout(DetachContext(ctx2Fix), 2*time.Second)
		defer cancelOp()

		res2, err2 = g.Do(key, func() (string, error) {
			return slowDBQuery(detachedCtx)
		})
	}()

	wg.Wait()
	fmt.Printf("Клиент 1 (30ms): res='%s', err=%v\n", res1, err1)
	fmt.Printf("Клиент 2 (300ms): res='%s', err=%v (УСПЕШНО СПАСЕН!)\n", res2, err2)
}
"""
            }
        ],
        "under_the_hood": "Контекст в Go образует иерархическое дерево. Метод `propagateCancel` связывает дочерний контекст с каналом `done` родителя. Если отменяется родитель, закрывается его канал `done`, что каскадно закрывает каналы всех потомков. Создание `detachedContext` разрывает цепочку отмены (метод `Done()` возвращает `nil`), но сохраняет доступ к `Value(key)`, позволяя передавать Trace ID и метаданные трассировки OpenTelemetry.",
        "pitfalls": "Отвязывая контекст от запроса клиента, вы рискуете создать неуправляемый зомби-запрос, если забудете повесить жесткий собственный таймаут (`context.WithTimeout`). Если база зависнет, отвязанный запрос без таймаута останется висеть вечно, удерживая соединение пула.",
        "bigtech_interview": "'Как в Go 1.21 штатно отвязать контекст от отмены?' Ответ: Использовать стандартную функцию `context.WithoutCancel(parentContext)`. Она возвращает обертку, которая игнорирует отмену родителя, но сохраняет значения context.Value."
    },
    {
        "num": 9,
        "title": "Вероятностное раннее устаревание: алгоритм XFetch",
        "task": "Реализуйте алгоритм вероятностного раннего устаревания XFetch (Optimal Probabilistic Cache Invalidation). Спроектируйте структуру CacheItem, хранящую значение, время вычисления дельты (delta computation time) и метку экспирации (expiry). Напишите функцию ShouldRefresh(item CacheItem, beta float64) bool, использующую формулу: `now - delta * beta * ln(rand()) > expiry`. Продемонстрируйте, как при приближении к истечению срока ключа под нагрузкой одна из горутин асинхронно обновляет кэш до его фактического устаревания.",
        "theory": "Алгоритм XFetch был сформулирован в исследовании Стэнфордского университета и ACM 'Optimal Probabilistic Cache Invalidation to Prevent Thundering Herds'. В отличие от Singleflight, требующего синхронизации между процессами, XFetch работает полностью децентрализованно.\n\nСуть алгоритма: Чем ближе время к истечению TTL и чем дольше вычисляется значение (параметр delta), тем выше математическая вероятность того, что случайный входящий запрос решит: 'Я обновлю этот кэш прямо сейчас!'.\nФормула триггера обновления:\n`- delta * beta * ln(rand()) > (expiry - now)`,\nгде:\n- `delta` — время, затраченное на генерацию значения из БД в прошлый раз;\n- `beta` — коэффициент агрессивности (обычно 1.0, при beta > 1 обновление происходит раньше);\n- `rand()` — случайное число с плавающей точкой в диапазоне (0, 1];\n- `expiry - now` — оставшееся время жизни кэша.\n\nЕсли условие выполняется, клиент возвращает еще валидное старое значение пользователю, а в фоне запускает обновление кэша!",
        "step_by_step": "1. Создайте структуру `XFetchItem` с полями `Value []byte`, `Delta time.Duration`, `Expiry time.Time`.\n2. Реализуйте функцию `ShouldRefresh(item *XFetchItem, beta float64) bool` с вычислением логарифма `math.Log(rand.Float64())`.\n3. Напишите метод `Get(key string, fetcher func() ([]byte, error))`.\n4. Если `ShouldRefresh` истинно, запустите фоновую горутину обновления значения и замера новой `delta`.\n5. Смоделируйте поток запросов и покажите, что кэш ни разу не возвращает `Cache Miss`.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"math"
	"math/rand"
	"sync"
	"time"
)

type XFetchItem struct {
	Value  string
	Delta  time.Duration // Время, затраченное на вычисление значения
	Expiry time.Time     // Момент жесткого истечения срока жизни
}

type XFetchCache struct {
	mu      sync.RWMutex
	storage map[string]*XFetchItem
	beta    float64 // Параметр агрессивности (обычно 1.0)
}

func NewXFetchCache(beta float64) *XFetchCache {
	return &XFetchCache{
		storage: make(map[string]*XFetchItem),
		beta:    beta,
	}
}

// ShouldRefresh вычисляет вероятностную формулу XFetch:
// now - delta * beta * ln(rnd) > expiry
func (c *XFetchCache) ShouldRefresh(item *XFetchItem) bool {
	now := time.Now()
	if now.After(item.Expiry) {
		return true // Уже жестко просрочен
	}

	// rand.Float64() возвращает [0.0, 1.0). Для ln исключаем 0.0:
	rnd := rand.Float64()
	if rnd <= 0.0 {
		rnd = 0.00001
	}

	// - delta * beta * ln(rnd)
	earlyExpirationOffset := -float64(item.Delta) * c.beta * math.Log(rnd)
	timeOffset := time.Duration(earlyExpirationOffset)

	// Если now + offset > Expiry -> пора обновлять!
	return now.Add(timeOffset).After(item.Expiry)
}

func (c *XFetchCache) GetOrFetch(key string, ttl time.Duration, fetcher func() (string, error)) (string, bool) {
	c.mu.RLock()
	item, ok := c.storage[key]
	c.mu.RUnlock()

	// Полный промах (холодный старт)
	if !ok {
		return c.refresh(key, ttl, fetcher), true
	}

	// Проверяем вероятностный триггер раннего обновления
	if c.ShouldRefresh(item) {
		// Запускаем упреждающее обновление в фоне
		go func() {
			c.refresh(key, ttl, fetcher)
		}()
	}

	return item.Value, false
}

func (c *XFetchCache) refresh(key string, ttl time.Duration, fetcher func() (string, error)) string {
	start := time.Now()
	val, err := fetcher()
	if err != nil {
		return ""
	}
	delta := time.Since(start)

	c.mu.Lock()
	c.storage[key] = &XFetchItem{
		Value:  val,
		Delta:  delta,
		Expiry: time.Now().Add(ttl),
	}
	c.mu.Unlock()

	return val
}

func main() {
	cache := NewXFetchCache(1.5) // beta = 1.5
	key := "weather:moscow"

	dbCalls := 0
	dbFetcher := func() (string, error) {
		dbCalls++
		time.Sleep(30 * time.Millisecond) // Тяжелый расчет
		return fmt.Sprintf("Temperature: +21C (v%d)", dbCalls), nil
	}

	// 1. Первый запрос (холодный старт)
	val, isCold := cache.GetOrFetch(key, 500*time.Millisecond, dbFetcher)
	fmt.Printf("1. Инициализация: val='%s', cold=%v\n", val, isCold)

	// 2. Имитируем поток запросов на протяжении 1 секунды
	start := time.Now()
	requests := 0
	for time.Since(start) < 1*time.Second {
		val, _ = cache.GetOrFetch(key, 500*time.Millisecond, dbFetcher)
		requests++
		time.Sleep(15 * time.Millisecond)
	}

	fmt.Printf("За 1 секунду обработано %d запросов.\n", requests)
	fmt.Printf("Всего фоновых вызовов БД (XFetch): %d (кэш ни разу не протух полностью!)\n", dbCalls)
	fmt.Printf("Текущее значение в кэше: %s\n", val)
}
"""
            }
        ],
        "under_the_hood": "Поскольку логарифм `ln(x)` при x -> 0 стремится к -минус бесконечности, значение `-delta * beta * ln(rand)` всегда положительно и распределено экспоненциально. Чем ближе текущее время к `expiry`, тем больше случайных чисел вызовут срабатывание условия. При миллионах запросов математически доказано, что ровно один запрос запустит фоновое обновление за секунды до экспирации, полностью исключая Cache Stampede.",
        "pitfalls": "Если параметр `beta` выставлен слишком большим (> 5.0) или время `delta` аномально подскочило из-за сетевого лага, алгоритм начнет обновлять кэш практически сразу после его создания, создавая непрерывную паразитную нагрузку на БД. Значение beta рекомендуется держать в диапазоне 1.0–1.5.",
        "bigtech_interview": "'В чем преимущество XFetch перед Singleflight в геораспределенной архитектуре?' Ответ: Singleflight работает только внутри памяти одного Go-процесса. Если у нас 200 подов в Kubernetes, при экспирации ключа в базу придет 200 параллельных запросов (по одному с каждого пода). Алгоритм XFetch выполняется вероятностно на уровне каждого пода независимо: вероятность того, что два пода решат обновиться одновременно в одну и ту же миллисекунду, стремится к нулю!"
    },
    {
        "num": 10,
        "title": "Проблема Cache Penetration и кэширование Null-Object",
        "task": "Смоделируйте атаку или проблему Cache Penetration (пробивание кэша): клиент массово запрашивает заведомо несуществующие ID сущностей (например, user:9999999). Поскольку таких записей нет ни в кэше, ни в БД, каждый запрос транзитом проходит сквозь кэш и бьет по базе данных. Реализуйте защиту методом кэширования 'Null-Object' (пустого значения / sentinel value) с коротким TTL (30–60 секунд). Покажите, как повторные запросы несуществующих ID мгновенно отбиваются кэшем.",
        "theory": "Cache Penetration возникает, когда запрашиваются данные, которых физически не существует в системе. В классической реализации Cache-Aside при отсутствии записи в БД в кэш ничего не пишется.\n\nЗлоумышленник может запустить сканер, перебирающий случайные несуществующие UUID или отрицательные ID со скоростью 50 000 RPS. Ни один из этих запросов не осядет в кэше, и все 50 000 RPS обрушатся прямо на дисковую подсистему базы данных.\n\nРешение 1: Кэширование пустых значений (Null-Object Caching). Если база вернула `ErrNotFound`, мы сохраняем в кэш специальный маркер (например, `{\"__null__\": true}` или пустую строку `\"\"`) с коротким TTL (от 30 сек до 2 минут).\nРешение 2: Предварительная фильтрация через Фильтр Блума (Bloom Filter).",
        "step_by_step": "1. Создайте структуру `NullCacheService`.\n2. Реализуйте метод `Get(id int64)`.\n3. Если репозиторий вернул `ErrNotFound`, запишите в кэш sentinel-байт `[]byte(\"__NULL__\")` с TTL = 1 минута.\n4. При чтении из кэша проверяйте совпадение со значением `__NULL__`: если совпало, немедленно возвращайте ошибку `ErrNotFound` без обращения к БД.\n5. Продемонстрируйте эффективность защиты на симуляции 100 запросов к случайным ID.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

var (
	ErrNotFound       = errors.New("entity not found")
	SentinelNullValue = []byte("__NULL_OBJECT_SENTINEL__")
)

type Database struct {
	queriesCount int64
	records      map[int64]string
}

func (db *Database) Query(id int64) (string, error) {
	atomic.AddInt64(&db.queriesCount, 1)
	time.Sleep(10 * time.Millisecond) // Имитация поиска по индексу

	val, ok := db.records[id]
	if !ok {
		return "", ErrNotFound
	}
	return val, nil
}

type SafeNullCache struct {
	db       *Database
	cache    sync.Map
	nullTTL  time.Duration
	validTTL time.Duration
}

type cacheEntry struct {
	val       []byte
	expiresAt time.Time
}

func NewSafeNullCache(db *Database) *SafeNullCache {
	return &SafeNullCache{
		db:       db,
		nullTTL:  2 * time.Second, // Короткий TTL для отсутствующих записей
		validTTL: 10 * time.Minute,
	}
}

func (c *SafeNullCache) Get(ctx context.Context, id int64) (string, error) {
	key := fmt.Sprintf("user:%d", id)

	// 1. Проверяем кэш
	if raw, ok := c.cache.Load(key); ok {
		entry := raw.(cacheEntry)
		if time.Now().Before(entry.expiresAt) {
			// Проверяем sentinel
			if string(entry.val) == string(SentinelNullValue) {
				return "", ErrNotFound // Мгновенный отказ из кэша!
			}
			return string(entry.val), nil
		}
		c.cache.Delete(key)
	}

	// 2. Поход в базу данных
	val, err := c.db.Query(id)
	if err != nil {
		if errors.Is(err, ErrNotFound) {
			// КЭШИРУЕМ ПУСТОЙ РЕЗУЛЬТАТ!
			c.cache.Store(key, cacheEntry{
				val:       SentinelNullValue,
				expiresAt: time.Now().Add(c.nullTTL),
			})
			return "", ErrNotFound
		}
		return "", err
	}

	// 3. Кэшируем валидный результат
	c.cache.Store(key, cacheEntry{
		val:       []byte(val),
		expiresAt: time.Now().Add(c.validTTL),
	})

	return val, nil
}

func main() {
	db := &Database{
		records: map[int64]string{
			100: "User: Elon Musk",
			200: "User: Satya Nadella",
		},
	}
	cache := NewSafeNullCache(db)
	ctx := context.Background()

	fmt.Println("1. Запрос существующего ID 100...")
	v, err := cache.Get(ctx, 100)
	fmt.Printf("Результат: '%s', err: %v\n", v, err)

	fmt.Println("\n2. Атака: 10 запросов подряд к несуществующему ID 999999...")
	for i := 1; i <= 10; i++ {
		_, err := cache.Get(ctx, 999999)
		if !errors.Is(err, ErrNotFound) {
			fmt.Println("Неожиданная ошибка:", err)
		}
	}

	fmt.Printf("\nИтого запросов к базе данных: %d\n", db.queriesCount)
	fmt.Printf("Из них к ID 100: 1 запрос, к несуществующему ID 999999: ровно 1 запрос (остальные 9 отбил кэш!)\n")
}
"""
            }
        ],
        "under_the_hood": "Sentinel-объект помещается в обычный бакет кэша. Если злоумышленник генерирует миллионы уникальных случайных ID, кэширование Null-Object может переполнить память самого кэша (OOM по ключам). Поэтому для Null-записей обязательно задают агрессивный алгоритм вытеснения по LRU/LFU и максимальный лимит памяти.",
        "pitfalls": "Слишком длинный TTL для Null-значений: если пользователь только что зарегистрировался в системе с ID 555, а за 2 секунды до этого кто-то проверил этот ID и закэшировал Null-Object на 1 час, новому пользователю в течение часа будет отдаваться ошибка 'User Not Found'! Поэтому TTL для Null-записей никогда не делают больше нескольких десятков секунд.",
        "bigtech_interview": "'Как защититься от миллиона запросов с уникальными несуществующими ID, чтобы не переполнить память кэша Null-объектами?' Ответ: Использовать Фильтр Блума (Bloom Filter) или Cuckoo Filter на входе перед кэшем! Фильтр Блума компактно (в битовом массиве) хранит информацию о существовании ключей: если фильтр говорит, что ключа нет в БД, запрос отбрасывается без обращения к кэшу и без аллокации Null-записей."
    },
    {
        "num": 11,
        "title": "Фильтр Блума (Bloom Filter) на входе в кэш",
        "task": "Реализуйте потокобезопасный Фильтр Блума на Go для защиты от Cache Penetration. Спроектируйте структуру BloomFilter на базе битового массива []uint64 и K независимых функций хеширования (на базе Murmur3/FNV). Реализуйте методы Add(key string) и Contains(key string) bool. Интегрируйте фильтр в цепочку обработки: перед любым обращением к L1/L2 или базе данных проверяется Contains. Если фильтр возвращает false, немедленно возвращайте ErrNotFound.",
        "theory": "Фильтр Блума (Bloom Filter) — это вероятностная структура данных для сверхбыстрой проверки принадлежности элемента множеству с фиксированным потреблением памяти.\n\nКлючевые математические гарантии:\n- **Ложноотрицательные срабатывания невозможны (False Negatives = 0%)**: Если фильтр вернул `false`, элемента ГАРАНТИРОВАННО нет в базе данных!\n- **Ложноположительные срабатывания возможны (False Positives = P)**: Если фильтр вернул `true`, элемент с высокой вероятностью есть, но возможна ложная тревога.\n\nФильтр размером всего 10 МБ в оперативной памяти может хранить информацию о 10 000 000 записей с вероятностью ошибки всего 1%. Это делает его идеальным щитом на входе в сервис.",
        "step_by_step": "1. Создайте структуру `BloomFilter` с размером битовой маски `m` и числом хеш-функций `k`.\n2. Реализуйте установку битов через побитовые сдвиги `bits[idx/64] |= 1 << (idx%64)`.\n3. Реализуйте проверку наличия битов в методе `Contains`.\n4. Интегрируйте фильтр в сервис перед проверкой L1/L2.\n5. Продемонстрируйте мгновенную отсечку 10 000 несуществующих ключей без единого сетевого запроса.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"sync"
)

type BloomFilter struct {
	mu    sync.RWMutex
	bits  []uint64
	size  uint64
	kHash uint64
}

func NewBloomFilter(sizeBits uint64, kHash uint64) *BloomFilter {
	words := (sizeBits + 63) / 64
	return &BloomFilter{
		bits:  make([]uint64, words),
		size:  sizeBits,
		kHash: kHash,
	}
}

// hash64 вычисляет базовый хеш для ключа
func (bf *BloomFilter) getHashes(key string) (uint64, uint64) {
	var h1 uint64 = 14695981039346656037
	var h2 uint64 = 5381
	for i := 0; i < len(key); i++ {
		h1 ^= uint64(key[i])
		h1 *= 1099511628211

		h2 = ((h2 << 5) + h2) + uint64(key[i])
	}
	return h1, h2
}

func (bf *BloomFilter) Add(key string) {
	bf.mu.Lock()
	defer bf.mu.Unlock()

	h1, h2 := bf.getHashes(key)
	for i := uint64(0); i < bf.kHash; i++ {
		// Кирш-Митценмахер метод генерации K хешей: h(i) = h1 + i*h2
		bitIdx := (h1 + i*h2) % bf.size
		wordIdx := bitIdx / 64
		bitPos := bitIdx % 64
		bf.bits[wordIdx] |= (1 << bitPos)
	}
}

func (bf *BloomFilter) Contains(key string) bool {
	bf.mu.RLock()
	defer bf.mu.RUnlock()

	h1, h2 := bf.getHashes(key)
	for i := uint64(0); i < bf.kHash; i++ {
		bitIdx := (h1 + i*h2) % bf.size
		wordIdx := bitIdx / 64
		bitPos := bitIdx % 64
		if (bf.bits[wordIdx] & (1 << bitPos)) == 0 {
			return false // Точно отсутствует!
		}
	}
	return true // Возможно, присутствует
}

type UserStoreWithBloom struct {
	bloom *BloomFilter
	db    map[string]string
}

func (s *UserStoreWithBloom) Get(id string) (string, string) {
	// Шаг 1: Проверка фильтром Блума
	if !s.bloom.Contains(id) {
		return "", "REJECTED_BY_BLOOM"
	}

	// Шаг 2: Только если фильтр сказал YES -> идем в БД
	val, ok := s.db[id]
	if !ok {
		return "", "FALSE_POSITIVE"
	}
	return val, "FOUND_IN_DB"
}

func main() {
	// Фильтр на 10 000 бит с 4 хеш-функциями
	bloom := NewBloomFilter(10_000, 4)
	db := make(map[string]string)

	// Заполняем существующие ID (от 1 до 500)
	for i := 1; i <= 500; i++ {
		id := fmt.Sprintf("user:%d", i)
		db[id] = fmt.Sprintf("UserData_%d", i)
		bloom.Add(id)
	}

	store := &UserStoreWithBloom{bloom: bloom, db: db}

	// 1. Проверяем валидный ключ
	val, status := store.Get("user:42")
	fmt.Printf("user:42 -> %s [%s]\n", val, status)

	// 2. Проверяем 10 000 несуществующих ключей
	rejected := 0
	falsePositives := 0

	for i := 501; i <= 10500; i++ {
		id := fmt.Sprintf("user:%d", i)
		_, st := store.Get(id)
		if st == "REJECTED_BY_BLOOM" {
			rejected++
		} else if st == "FALSE_POSITIVE" {
			falsePositives++
		}
	}

	fmt.Printf("\n=== РЕЗУЛЬТАТЫ ФИЛЬТРА БЛУМА ===\n")
	fmt.Printf("Проверено несуществующих ключей: 10000\n")
	fmt.Printf("Отсечено без обращения к базе данных: %d (%.2f%%)\n", rejected, float64(rejected)/100.0)
	fmt.Printf("Ложноположительных пропусков в БД: %d (%.2f%%)\n", falsePositives, float64(falsePositives)/100.0)
}
"""
            }
        ],
        "under_the_hood": "Техника Kirsch-Mitzenmacher позволяет генерировать произвольное количество $k$ независимых хеш-значений по формуле $g_i(x) = h_1(x) + i \cdot h_2(x) \pmod m$, используя всего две 64-битные хеш-функции вместо вычисления $k$ отдельных хешей. Это экономит циклы CPU и делает проверку битовой карты практически мгновенной.",
        "pitfalls": "Классический фильтр Блума не поддерживает операцию удаления элементов! Если запись удалена из БД, удалить ее биты из фильтра нельзя (так как эти биты могут разделяться другими ключами). Для систем с частыми удалениями используют Counting Bloom Filter или Cuckoo Filter.",
        "bigtech_interview": "'Как рассчитать оптимальный размер битового массива фильтра Блума?' Ответ: Формула $m = - \frac{n \cdot \ln(p)}{(\ln 2)^2}$, где $n$ — число элементов, $p$ — допустимая вероятность ложноположительного ответа. Оптимальное число хеш-функций: $k = \frac{m}{n} \cdot \ln 2$."
    },
    {
        "num": 12,
        "title": "Cache Avalanche и добавление джиттера к TTL (TTL Jitter)",
        "task": "Смоделируйте проблему 'лавины кэша' (Cache Avalanche): при одновременной записи большого каталога сущностей с одинаковым TTL (например, ровно 1 час) все ключи одновременно истекают в один момент времени, вызывая мгновенный лавинообразный отказ базы данных. Реализуйте алгоритм вычисления TTL со случайным джиттером (Full Jitter / Equal Jitter): `ApplyJitter(baseTTL time.Duration, jitterPercent float64) time.Duration`. Покажите на графике/статистике размазывание моментов экспирации во времени.",
        "theory": "Cache Avalanche (лавина кэша) возникает, когда огромное количество ключей имеют одинаковое время жизни. Классический сценарий: в 03:00 ночи запускается ETL-скрипт или кэш-вормер, который обновляет кэш 500 000 товаров с жестким `TTL = 2 * time.Hour`.\n\nРовно в 05:00:00 все 500 000 ключей одновременно испаряются из Redis. В 05:00:01 вся нагрузка интернет-магазина обрушивается на реляционную БД, приводя к ее падению.\n\nРешение: Внедрение случайного джиттера (TTL Jitter). Вместо фиксированного TTL к каждому ключу при записи добавляется псевдослучайное смещение:\n`actualTTL = baseTTL + randRange(-jitter, +jitter)`.\nВ результате момент экспирации плавно 'размазывается' по временному окну в 10–30 минут, сглаживая нагрузку на БД до безопасного фонового уровня.",
        "step_by_step": "1. Напишите функцию `WithJitter(base time.Duration, factor float64) time.Duration`.\n2. Сгенерируйте 100 000 ключей с фиксированным TTL и постройте гистограмму истечения ключей по 1-секундным интервалам.\n3. Сгенерируйте те же 100 000 ключей с джиттером 20%.\n4. Сравните пиковый RPS нагрузки на БД в обеих моделях.\n5. Зафиксируйте отсутствие пиков при использовании джиттера.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"fmt"
	"math/rand"
	"time"
)

// ApplyJitter добавляет симметричный процентный джиттер к базовому TTL.
// Например, base = 100s, jitterFactor = 0.2 -> TTL от 80s до 120s.
func ApplyJitter(baseTTL time.Duration, jitterFactor float64) time.Duration {
	if jitterFactor <= 0 {
		return baseTTL
	}
	// Случайный коэффициент в диапазоне [-jitterFactor, +jitterFactor]
	delta := (rand.Float64()*2 - 1) * jitterFactor
	multiplier := 1.0 + delta

	return time.Duration(float64(baseTTL) * multiplier)
}

func main() {
	itemCount := 100_000
	baseTTL := 60 * time.Second
	jitterFactor := 0.20 // 20% джиттер (+-12 секунд)

	// Моделируем моменты экспирации без джиттера
	noJitterBuckets := make(map[int]int)
	for i := 0; i < itemCount; i++ {
		sec := int(baseTTL.Seconds())
		noJitterBuckets[sec]++
	}

	// Моделируем моменты экспирации с джиттером
	jitterBuckets := make(map[int]int)
	for i := 0; i < itemCount; i++ {
		actual := ApplyJitter(baseTTL, jitterFactor)
		sec := int(actual.Seconds())
		jitterBuckets[sec]++
	}

	fmt.Println("=== СРАВНЕНИЕ ЭКСПИРАЦИИ 100 000 КЛЮЧЕЙ ===")
	fmt.Printf("1. Без джиттера (Cache Avalanche):\n")
	fmt.Printf("   Секунда 59: %d ключей истекло\n", noJitterBuckets[59])
	fmt.Printf("   Секунда 60: %d ключей истекло (КАТАСТРОФИЧЕСКИЙ ПИК!)\n", noJitterBuckets[60])
	fmt.Printf("   Секунда 61: %d ключей истекло\n\n", noJitterBuckets[61])

	fmt.Printf("2. С джиттером 20%% (Равномерное распределение):\n")
	minSec, maxSec := 48, 72
	maxInJitter := 0
	for s := minSec; s <= maxSec; s++ {
		c := jitterBuckets[s]
		if c > maxInJitter {
			maxInJitter = c
		}
	}

	fmt.Printf("   Диапазон истечения: от %dс до %dс (окно %d секунд)\n", minSec, maxSec, maxSec-minSec)
	fmt.Printf("   Пиковая нагрузка в секунду: %d ключей (в %.1f раз меньше!)\n",
		maxInJitter, float64(noJitterBuckets[60])/float64(maxInJitter))

	fmt.Println("\nПример распределения по секундам с джиттером:")
	for s := minSec; s <= minSec+6; s++ {
		fmt.Printf("   t = %dc: %d ключей\n", s, jitterBuckets[s])
	}
}
"""
            }
        ],
        "under_the_hood": "Без джиттера производная функции истечения кэша представляет собой дельта-функцию Дирака с бесконечным пиком в точке $t = TTL$. С джиттером моменты распределяются по непрерывному равномерному закону, а нагрузка на базу данных масштабируется как $RPS_{peak} = \frac{N}{2 \cdot \Delta t}$, снижая пиковое давление на порядок.",
        "pitfalls": "Использование неинициализированного генератора случайных чисел `rand.New(rand.NewSource(1))` приведет к тому, что при каждом перезапуске пода все ноды сгенерируют идентичные псевдослучайные последовательности джиттера. В современном Go (Go 1.20+) используйте потокобезопасный и автоматически инициализируемый глобальный генератор пакета `math/rand`.",
        "bigtech_interview": "'В чем разница между Full Jitter и Equal Jitter?' Ответ: В Equal Jitter базовое время делится пополам: фиксированная половина плюс случайная добавка от 0 до половины: $TTL = \frac{T}{2} + rand(0, \frac{T}{2})$. В Full Jitter весь интервал случаен: $TTL = rand(0, T)$. Для кэширования чаще используют процентный центрированный джиттер $T \pm \delta$, чтобы гарантировать минимальное время кэширования."
    },
    {
        "num": 13,
        "title": "Паттерн Write-Through Caching",
        "task": "Реализуйте паттерн сквозной записи (Write-Through Caching) на Go. В отличие от Cache-Aside, приложение взаимодействует исключительно со структурой WriteThroughService, которая синхронно обновляет и кэш, и реляционную базу данных в рамках одной логической операции. Продемонстрируйте механизм отката: если транзакция в базе данных завершилась ошибкой, значение в кэше не должно обновляться (или должно быть инвалидировано).",
        "theory": "Паттерн Write-Through Caching инвертирует ответственность за запись: приложение никогда не пишет в БД напрямую, а обращается только к уровню кэша.\n\nАлгоритм Write-Through:\n1. Приложение вызывает `cache.Write(key, value)`.\n2. Кэш-сервис открывает транзакцию в БД и фиксирует новую запись.\n3. При успехе SQL-транзакции кэш обновляет собственную память (L1/L2).\n4. Кэш возвращает клиенту статус успеха.\n\nПлюсы: Данные в кэше всегда свежие (Read-Your-Own-Writes с нулевым Cache Miss). Нет проблемы Cache Stampede при первом чтении.\nМинусы: Высокая задержка записи (Write Latency), так как каждая запись блокируется сетевым RTT к базе данных.",
        "step_by_step": "1. Создайте интерфейсы `SQLDatabase` с поддержкой транзакций и `CacheStore`.\n2. Реализуйте структуру `WriteThroughManager`.\n3. В методе `Save(ctx, id, data)` запустите транзакцию в БД.\n4. Если коммит успешен, обновите кэш.\n5. Если коммит упал, убедитесь, что кэш остался нетронут, и верните ошибку клиенту.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

type CustomerAccount struct {
	ID      string
	Balance int64
}

type WriteThroughService struct {
	mu       sync.RWMutex
	l1Cache  map[string]CustomerAccount
	dbStore  map[string]CustomerAccount
	simDBErr bool
}

func NewWriteThroughService() *WriteThroughService {
	return &WriteThroughService{
		l1Cache: make(map[string]CustomerAccount),
		dbStore: make(map[string]CustomerAccount),
	}
}

func (s *WriteThroughService) Get(ctx context.Context, id string) (CustomerAccount, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	// При Write-Through кэш всегда прогрет!
	acc, ok := s.l1Cache[id]
	return acc, ok
}

func (s *WriteThroughService) Save(ctx context.Context, acc CustomerAccount) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Шаг 1: Запись в базу данных (первоисточник правды)
	if s.simDBErr {
		return errors.New("db error: disk I/O failure on commit")
	}
	s.dbStore[acc.ID] = acc

	// Шаг 2: Синхронная сквозная запись в кэш
	s.l1Cache[acc.ID] = acc

	return nil
}

func main() {
	svc := NewWriteThroughService()
	ctx := context.Background()

	acc := CustomerAccount{ID: "acc_777", Balance: 50000}

	fmt.Println("1. Успешная сквозная запись аккаунта...")
	err := svc.Save(ctx, acc)
	fmt.Printf("Save err: %v\n", err)

	val, found := svc.Get(ctx, "acc_777")
	fmt.Printf("Мгновенное чтение из L1: %+v (найдено: %v)\n\n", val, found)

	fmt.Println("2. Попытка обновления с ошибкой в базе данных...")
	svc.simDBErr = true
	badUpdate := CustomerAccount{ID: "acc_777", Balance: 999999}
	err = svc.Save(ctx, badUpdate)
	fmt.Printf("Save err: %v\n", err)

	valAfterErr, _ := svc.Get(ctx, "acc_777")
	fmt.Printf("Баланс в кэше после сбоя БД: %d (НЕ изменился, консистентность соблюдена!)\n", valAfterErr.Balance)
}
"""
            }
        ],
        "under_the_hood": "Write-Through устраняет разрыв между записью и чтением. Однако в многопоточной среде при конкурентной записи двух клиентов критически важно сериализовать запись, иначе запрос А запишет в БД, запрос Б запишет в БД, а в кэш запишется сначала Б, затем А. Для предотвращения этого используют CAS (Compare-And-Swap) или версионирование записей.",
        "pitfalls": "Загрязнение кэша холодными данными: если в систему пишется много сущностей, которые затем никогда или редко читаются (например, архивные логи или разовые чеки), Write-Through забивает оперативную память кэша бесполезным мусором, вытесняя действительно горячие ключи.",
        "bigtech_interview": "'Чем Write-Through отличается от Write-Back (Write-Behind)?' Ответ: При Write-Through запись в БД выполняется синхронно ДО ответа клиенту (гарантия надежности ценой повышенной задержки записи). При Write-Behind запись фиксируется только в оперативной памяти кэша и немедленно подтверждается клиенту, а в БД сбрасывается асинхронно фоновым батчем (экстремальная скорость записи, но есть риск потери данных при аварии ноды)."
    },
    {
        "num": 14,
        "title": "Паттерн Write-Behind (Write-Back) Caching",
        "task": "Спроектируйте высокопроизводительный сервис на паттерне Write-Behind (Write-Back Caching). Сервис должен мгновенно подтверждать запись клиенту, сохраняя данные в локальный кэш и помещая задание во внутренний буферизованный канал. Фоновый воркер (Flush Worker) должен периодически (по таймауту 100 мс или по накоплению батча в 50 элементов) сбрасывать накопленные изменения пакетной вставкой (Batch Insert) в базу данных. Реализуйте Graceful Shutdown с гарантией сброса оставшегося буфера при остановке процесса.",
        "theory": "Паттерн Write-Behind (Write-Back) обеспечивает максимально возможную скорость записи:\n1. Приложение пишет данные только в кэш в оперативной памяти.\n2. Кэш немедленно подтверждает успешность операции клиенту (задержка < 1 мс).\n3. В фоне асинхронный воркер объединяет тысячи мелких записей в один пакетный запрос к БД (`INSERT ... ON CONFLICT DO UPDATE ...`) и сбрасывает их на диск.\n\nПреимущества: Фантастическая пропускная способность (дедупликация повторных записей одного ключа прямо в памяти, снижение нагрузки на БД в 10–100 раз).\nРиск: Если процесс Go аварийно завершится (OOM killer, Kernel Panic, отключение питания) до того, как фоновый воркер сбросит данные в БД, последние изменения будут безвозвратно утеряны.",
        "step_by_step": "1. Создайте структуру `WriteBehindCache` с очередью `chan WriteOperation`.\n2. В методе `Set` запишите данные в локальную мапу и отправьте операцию в канал.\n3. Запустите фоновый воркер `flushLoop` с тикером и накопительным буфером.\n4. При заполнении буфера или срабатывании тикера вызывайте `db.BatchSave`.\n5. В методе `Close()` закройте канал, дождитесь сброса всех данных через `sync.WaitGroup`.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

type Record struct {
	Key   string
	Value string
}

type WriteBehindCache struct {
	mu         sync.RWMutex
	memory     map[string]string
	queue      chan Record
	wg         sync.WaitGroup
	batchSize  int
	dbInserts  int64
	dbRowsSaved int64
}

func NewWriteBehindCache(queueCap, batchSize int, flushInterval time.Duration) *WriteBehindCache {
	c := &WriteBehindCache{
		memory:    make(map[string]string),
		queue:     make(chan Record, queueCap),
		batchSize: batchSize,
	}

	c.wg.Add(1)
	go c.flushWorker(flushInterval)

	return c
}

func (c *WriteBehindCache) Get(key string) (string, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	val, ok := c.memory[key]
	return val, ok
}

func (c *WriteBehindCache) Set(key, value string) {
	c.mu.Lock()
	c.memory[key] = value
	c.mu.Unlock()

	// Асинхронная отправка в очередь записи
	c.queue <- Record{Key: key, Value: value}
}

func (c *WriteBehindCache) flushWorker(interval time.Duration) {
	defer c.wg.Done()
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	buffer := make([]Record, 0, c.batchSize)

	flush := func() {
		if len(buffer) == 0 {
			return
		}
		// Имитация пакетной вставки в БД
		atomic.AddInt64(&c.dbInserts, 1)
		atomic.AddInt64(&c.dbRowsSaved, int64(len(buffer)))
		time.Sleep(20 * time.Millisecond) // Задержка записи батча
		buffer = buffer[:0]
	}

	for {
		select {
		case rec, ok := <-c.queue:
			if !ok {
				flush() // Сбрасываем остаток при закрытии
				return
			}
			buffer = append(buffer, rec)
			if len(buffer) >= c.batchSize {
				flush()
			}
		case <-ticker.C:
			flush()
		}
	}
}

func (c *WriteBehindCache) Close() {
	close(c.queue)
	c.wg.Wait()
}

func main() {
	cache := NewWriteBehindCache(10000, 50, 100*time.Millisecond)

	fmt.Println("Запись 200 событий в режиме Write-Behind...")
	start := time.Now()

	for i := 1; i <= 200; i++ {
		cache.Set(fmt.Sprintf("metric:cpu:core_%d", i%4), fmt.Sprintf("val_%d", i))
	}
	writeDuration := time.Since(start)
	fmt.Printf("Клиент завершил 200 записей мгновенно за %v!\n", writeDuration)

	// Проверяем, что в оперативной памяти данные уже доступны сразу
	val, _ := cache.Get("metric:cpu:core_1")
	fmt.Printf("Мгновенный Get из памяти: %s\n", val)

	// Закрываем кэш с гарантированным сбросом (Graceful Flush)
	cache.Close()

	fmt.Printf("\n=== РЕЗУЛЬТАТЫ БАТЧИНГА В БАЗУ ДАННЫХ ===\n")
	fmt.Printf("Фактических SQL-транзакций (батчей): %d\n", cache.dbInserts)
	fmt.Printf("Всего строк сброшено в БД: %d\n", cache.dbRowsSaved)
}
"""
            }
        ],
        "under_the_hood": "Write-Behind аккумулирует данные в буферизованном канале Go. На уровне ядра СУБД один пакетный запрос на 100 строк выполняет один вызов `fsync` к журналу WAL (Write-Ahead Log), в то время как 100 отдельных запросов потребовали бы 100 независимых синхронизаций с диском, что привело бы к исчерпанию дискового IOPS.",
        "pitfalls": "Переполнение очереди (Queue Overflow): если база данных начинает деградировать по скорости, канал `queue` заполнится до предела `cap(c.queue)`. При попытке записи метод `Set` либо заблокирует вызывающую горутину, либо уронит запись. Необходимо настроить метрику заполненности очереди и алерт при достижении 80% емкости.",
        "bigtech_interview": "'Как обезопасить Write-Behind кэш от потери данных при аварийном падении сервера?' Ответ: Использовать упреждающий журнал транзакций (WAL) на локальном NVMe диске (append-only файл с `O_DIRECT` или mmap), либо использовать распределенный durable-буфер на базе Apache Kafka или Redis Streams."
    },
    {
        "num": 15,
        "title": "Распределенная инвалидация L1 через Redis Pub/Sub",
        "task": "Реализуйте механизм согласованности кэшей (Cache Coherence) в распределенном кластере с помощью Redis Pub/Sub. Когда инстанс сервиса изменяет данные в БД, он публикует сообщение об инвалидации в канал кэша: InvalidationMessage{Key: 'user:123', NodeID: 'node-A'}. Все остальные реплики сервиса, подписанные на этот канал, получают событие и немедленно вычищают устаревший ключ из своего локального L1-кэша. Реализуйте защиту от повторного удаления ключа на ноде-инициаторе.",
        "theory": "В горизонтально масштабируемой микросервисной архитектуре (Kubernetes) работают десятки реплик одного сервиса. У каждой реплики свой независимый L1 In-Memory кэш.\n\nЕсли запрос на изменение профиля пользователя пришел на Ноду 1, она обновляет БД и инвалидирует свой L1. Но Ноды 2, 3 и 4 ничего об этом не знают и продолжают отдавать устаревший профиль пользователю!\n\nРешение: Распределенная шина инвалидации на базе Redis Pub/Sub:\n1. При изменении сущности Нода 1 отправляет команду `PUBLISH cache:invalidate {\"key\":\"user:123\",\"sender\":\"node-1\"}`.\n2. Все инстансы слушают этот канал в фоновой горутине через `SUBSCRIBE`.\n3. Получив сообщение, каждый инстанс проверяет `sender != self.nodeID` и выполняет `L1.Delete(key)`.\n4. Время распространения инвалидации составляет менее 2–5 миллисекунд.",
        "step_by_step": "1. Спроектируйте структуру сообщения `InvalidationEvent`.\n2. Создайте симулятор брокера Pub/Sub с широковещательной рассылкой сообщений.\n3. Создайте 3 независимых экземпляра сервиса с уникальными `NodeID`.\n4. Вызовите обновление на Ноде 1 и покажите, как Ноды 2 и 3 очищают свои L1 кэши.\n5. Убедитесь, что нода-отправитель не тратит ресурсы на повторную обработку собственного сообщения.",
        "code_blocks": [
            {
                "filename": "main.go",
                "lang": "go",
                "code": r"""package main

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"
)

type InvalidationEvent struct {
	Key      string `json:"key"`
	SenderID string `json:"sender_id"`
}

// MockRedisPubSub симулирует централизованный брокер Pub/Sub Redis
type MockRedisPubSub struct {
	mu          sync.Mutex
	subscribers map[string]chan []byte
}

func NewMockRedisPubSub() *MockRedisPubSub {
	return &MockRedisPubSub{
		subscribers: make(map[string]chan []byte),
	}
}

func (b *MockRedisPubSub) Subscribe(nodeID string) <-chan []byte {
	b.mu.Lock()
	defer b.mu.Unlock()
	ch := make(chan []byte, 100)
	b.subscribers[nodeID] = ch
	return ch
}

func (b *MockRedisPubSub) Publish(msg []byte) {
	b.mu.Lock()
	defer b.mu.Unlock()
	for _, ch := range b.subscribers {
		select {
		case ch <- msg:
		default:
			// Защита от зависания при медленном подписчике
		}
	}
}

// ClusterNode представляет инстанс сервиса в Kubernetes
type ClusterNode struct {
	NodeID string
	l1     sync.Map
	broker *MockRedisPubSub
}

func NewClusterNode(nodeID string, broker *MockRedisPubSub) *ClusterNode {
	n := &ClusterNode{
		NodeID: nodeID,
		broker: broker,
	}

	// Запускаем слушатель инвалидаций
	ch := broker.Subscribe(nodeID)
	go n.listenInvalidations(ch)

	return n
}

func (n *ClusterNode) listenInvalidations(ch <-chan []byte) {
	for raw := range ch {
		var evt InvalidationEvent
		if err := json.Unmarshal(raw, &evt); err != nil {
			continue
		}
		// Игнорируем собственные события
		if evt.SenderID == n.NodeID {
			continue
		}
		// Инвалидируем ключ в локальной памяти
		n.l1.Delete(evt.Key)
		fmt.Printf("[%s] Инвалидирован ключ '%s' по сообщению от %s\n", n.NodeID, evt.Key, evt.SenderID)
	}
}

func (n *ClusterNode) UpdateData(key, newVal string) {
	// 1. Обновляем локально
	n.l1.Store(key, newVal)

	// 2. Рассылаем широковещательное уведомление другим нодам
	evt := InvalidationEvent{
		Key:      key,
		SenderID: n.NodeID,
	}
	bytes, _ := json.Marshal(evt)
	n.broker.Publish(bytes)
}

func main() {
	broker := NewMockRedisPubSub()

	// Поднимаем 3 реплики сервиса
	nodeA := NewClusterNode("pod-srv-node-A", broker)
	nodeB := NewClusterNode("pod-srv-node-B", broker)
	nodeC := NewClusterNode("pod-srv-node-C", broker)

	key := "pricing:plan:pro"

	// Все ноды закэшировали старый план
	nodeA.l1.Store(key, "Price: 99$")
	nodeB.l1.Store(key, "Price: 99$")
	nodeC.l1.Store(key, "Price: 99$")

	fmt.Println("Все ноды имеют в L1 кэше: Price: 99$")

	// Клиент отправляет запрос на изменение цены на Ноду А
	fmt.Println("\nНода А обновляет цену на 129$ и рассылает инвалидацию...")
	nodeA.UpdateData(key, "Price: 129$")

	time.Sleep(50 * time.Millisecond) // Даем брокеру доставить сообщения

	// Проверяем состояние кэшей
	valA, _ := nodeA.l1.Load(key)
	_, foundB := nodeB.l1.Load(key)
	_, foundC := nodeC.l1.Load(key)

	fmt.Printf("\nРезультаты состояния L1 кэшей на нодах:\n")
	fmt.Printf("Нода A (автор): '%s'\n", valA)
	fmt.Printf("Нода B: в кэше найдено = %v (устаревшие данные очищены!)\n", foundB)
	fmt.Printf("Нода C: в кэше найдено = %v (устаревшие данные очищены!)\n", foundC)
}
"""
            }
        ],
        "under_the_hood": "Redis Pub/Sub работает по принципу At-Most-Once (Fire-and-Forget). Сервер Redis не буферизует сообщения для отключенных подписчиков. Если в момент отправки инвалидации Нода Б кратковременно потеряла соединение с Redis (сетевой флап), она пропустит сообщение и останется с рассинхронизированным кэшем до истечения TTL.",
        "pitfalls": "Проблема разрыва соединения Pub/Sub: в продакшене при обнаружении дисконнекта от Redis подписка обязана полностью очистить весь локальный L1 кэш целиком (`L1.Clear()`), так как за время оффлайна могли произойти любые изменения.",
        "bigtech_interview": "'Как бороться с лавиной сообщений инвалидации в Redis Pub/Sub при 100 000 обновлений в секунду?' Ответ: Использовать пакетирование сообщений (Batch Invalidation), инвалидировать префиксами/версиями пространств имен (`version:users++`), либо использовать механизм Redis RESP3 Client-Side Tracking, перекладывающий отслеживание ключей на сторону сервера Redis."
    }
]
