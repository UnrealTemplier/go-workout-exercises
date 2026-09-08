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

# Ex 1: Архитектура etcd v3 и протокол консенсуса Raft
code1 = r'''package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// RaftRole описывает роль узла в алгоритме консенсуса Raft
type RaftRole string

const (
	RoleFollower  RaftRole = "Follower"
	RoleCandidate RaftRole = "Candidate"
	RoleLeader    RaftRole = "Leader"
)

// RaftNodeState моделирует базовое состояние узла Raft в etcd
type RaftNodeState struct {
	mu          sync.RWMutex
	nodeID      string
	currentTerm uint64
	role        RaftRole
	votedFor    string
	commitIndex uint64
	logEntries  []string
}

func NewRaftNode(id string) *RaftNodeState {
	return &RaftNodeState{
		nodeID:      id,
		currentTerm: 1,
		role:        RoleFollower,
		logEntries:  make([]string, 0),
	}
}

func (n *RaftNodeState) GetStatus() (string, RaftRole, uint64, uint64) {
	n.mu.RLock()
	defer n.mu.RUnlock()
	return n.nodeID, n.role, n.currentTerm, n.commitIndex
}

// ProposeCommand имитирует предложение команды клиентом лидеру etcd
func (n *RaftNodeState) ProposeCommand(ctx context.Context, cmd string) (uint64, error) {
	n.mu.Lock()
	defer n.mu.Unlock()

	if n.role != RoleLeader {
		return 0, fmt.Errorf("node %s не является лидером, перенаправление запроса", n.nodeID)
	}

	n.logEntries = append(n.logEntries, cmd)
	n.commitIndex = uint64(len(n.logEntries))
	return n.commitIndex, nil
}

// BecomeLeader переводит узел в состояние лидера после успешного кворума
func (n *RaftNodeState) BecomeLeader(term uint64) {
	n.mu.Lock()
	defer n.mu.Unlock()
	n.role = RoleLeader
	n.currentTerm = term
	fmt.Printf("[RAFT] Узел %s избран лидером терма %d (Кворум подтвержден)\n", n.nodeID, n.currentTerm)
}

func main() {
	node := NewRaftNode("etcd-node-1")
	node.BecomeLeader(2)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	idx, err := node.ProposeCommand(ctx, "PUT /configs/db/host = pg.prod.local")
	if err != nil {
		panic(err)
	}

	id, role, term, commit := node.GetStatus()
	fmt.Printf("Узел: %s, Роль: %s, Терм: %d, Реплицированный индекс: %d (Команда %d закоммичена)\n",
		id, role, term, commit, idx)
}
'''
validate_go_code(code1, "code1")
exercises.append({
    "num": 1,
    "title": "Архитектура etcd v3 и протокол консенсуса Raft",
    "task": "Изучите архитектуру etcd v3 и алгоритм консенсуса Raft. Смоделируйте потокобезопасную структуру RaftNodeState с ролями Follower/Candidate/Leader, текущим термом (currentTerm) и индексом коммита (commitIndex). Реализуйте метод репликации команд и переход в состояние лидера при получении кворума.",
    "theory": "etcd v3 — это строго консистентное распределенное хранилище метаданных вида 'ключ-значение', лежащее в основе Kubernetes (хранение всего состояния кластера, Pods, Services, CRD) и критических enterprise-систем.\n\nКлючевые архитектурные столпы etcd:\n1. Консенсус Raft: гарантирует линеаризуемость (Linearizable Reads/Writes) и устойчивость к разделению сети (Network Partitions). Кластер из `2F+1` узлов сохраняет работоспособность при падении до `F` узлов (для кластера из 3 узлов допустима потеря 1, для 5 узлов — 2).\n2. Хранилище BoltDB (bbolt): встроенная transactional B+tree СУБД, в которой данные персистентно сохраняются на диск через memory-mapped files (`mmap`).\n3. MVCC (Multi-Version Concurrency Control): данные не перезаписываются на месте. Каждая операция записи создает новую глобальную ревизию, позволяя осуществлять исторические запросы и подписки на изменения.",
    "step_by_step": [
        "Определите тип перечисления RaftRole для состояний Follower, Candidate и Leader.",
        "Создайте структуру RaftNodeState с защитой состояния через sync.RWMutex.",
        "Реализуйте метод BecomeLeader с фиксацией текущего терма выборов.",
        "Напишите метод ProposeCommand с проверкой роли лидера и инкрементом commitIndex.",
        "Продемонстрируйте фиксацию команды в реплицированном журнале."
    ],
    "code_blocks": [{
        "filename": "raft_architecture.go",
        "lang": "go",
        "code": code1
    }],
    "under_the_hood": "В etcd v3 все изменения сначала попадают в Raft-лог в памяти, затем сбрасываются на диск с `fsync` (WAL — Write-Ahead Log). Лидер рассылает `AppendEntries` RPC фолловерам. Как только большинство (кворум `N/2 + 1`) подтвердило запись на диск, команда считается закоммиченной и применяется к состоянию MVCC в bbolt.",
    "pitfalls": [
        "Четное число узлов: развертывание 4 узлов не увеличивает отказоустойчивость по сравнению с 3 (в обоих случаях допустима потеря только 1 узла, но для 4 узлов требуется кворум из 3). Всегда используйте нечетное число нод (3 или 5).",
        "Медленные диски: задержка `fsync` на WAL напрямую определяет пропускную способность etcd. Использование медленных сетевых HDD дисков приводит к потере heartbeat-пакетов и непрерывным перевыборам лидера."
    ],
    "bigtech_interview": "Почему etcd не масштабируется горизонтально по объему хранимых данных? etcd оптимизирован под консистентность метаданных (CP по CAP-теореме), а не под Big Data. Каждый узел хранит полную копию всех ключей. Лимит размера базы etcd по умолчанию — от 2 до 8 ГБ."
})

# Ex 2: Модель данных etcd: глобальные ревизии и версионирование
code2 = r'''package main

import (
	"fmt"
	"sync"
)

// KeyMetadata описывает MVCC-метаданные конкретного ключа в etcd
type KeyMetadata struct {
	Key            string
	Value          []byte
	CreateRevision int64 // Глобальная ревизия создания ключа
	ModRevision    int64 // Глобальная ревизия последнего изменения ключа
	Version        int64 // Счетчик версий (число изменений в текущей жизни)
}

// MVCCStore эмулирует хранилище etcd v3 с глобальным счетчиком ревизий
type MVCCStore struct {
	mu           sync.RWMutex
	mainRevision int64
	keys         map[string]KeyMetadata
}

func NewMVCCStore() *MVCCStore {
	return &MVCCStore{
		mainRevision: 1, // Начальная ревизия etcd
		keys:         make(map[string]KeyMetadata),
	}
}

// Put сохраняет значение с инкрементом глобальной ревизии
func (s *MVCCStore) Put(key string, val []byte) KeyMetadata {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.mainRevision++ // Каждая операция записи инкрементирует глобальный счетчик
	existing, exists := s.keys[key]

	meta := KeyMetadata{
		Key:            key,
		Value:          val,
		ModRevision:    s.mainRevision,
		CreateRevision: s.mainRevision,
		Version:        1,
	}

	if exists {
		meta.CreateRevision = existing.CreateRevision
		meta.Version = existing.Version + 1
	}

	s.keys[key] = meta
	return meta
}

// Delete удаляет ключ с фиксацией ревизии удаления (Tombstone)
func (s *MVCCStore) Delete(key string) (int64, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if _, exists := s.keys[key]; !exists {
		return s.mainRevision, false
	}

	s.mainRevision++
	delete(s.keys, key)
	return s.mainRevision, true
}

func (s *MVCCStore) CurrentRevision() int64 {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.mainRevision
}

func main() {
	store := NewMVCCStore()

	// Шаг 1: Первое создание ключа
	m1 := store.Put("/app/rate_limit", []byte("100"))
	fmt.Printf("1. Создан ключ: Key=%s CreateRev=%d ModRev=%d Version=%d Val=%s\n",
		m1.Key, m1.CreateRevision, m1.ModRevision, m1.Version, string(m1.Value))

	// Шаг 2: Создание другого ключа (глобальная ревизия растет)
	store.Put("/app/db_pool", []byte("50"))

	// Шаг 3: Модификация первого ключа
	m2 := store.Put("/app/rate_limit", []byte("250"))
	fmt.Printf("2. Обновлен ключ: Key=%s CreateRev=%d ModRev=%d Version=%d Val=%s\n",
		m2.Key, m2.CreateRevision, m2.ModRevision, m2.Version, string(m2.Value))

	// Шаг 4: Удаление ключа
	delRev, _ := store.Delete("/app/rate_limit")
	fmt.Printf("3. Ключ удален на глобальной ревизии: %d (Текущая ревизия кластера: %d)\n",
		delRev, store.CurrentRevision())

	// Шаг 5: Повторное создание удаленного ключа
	m3 := store.Put("/app/rate_limit", []byte("500"))
	fmt.Printf("4. Вновь создан: Key=%s CreateRev=%d ModRev=%d Version=%d Val=%s\n",
		m3.Key, m3.CreateRevision, m3.ModRevision, m3.Version, string(m3.Value))
}
'''
validate_go_code(code2, "code2")
exercises.append({
    "num": 2,
    "title": "Модель данных etcd: глобальные ревизии и версионирование",
    "task": "Изучите версионирование в etcd v3: глобальный счетчик ревизий (Main Revision), CreateRevision, ModRevision и Version. Напишите имитатор MVCCStore, демонстрирующий, как изменяются метаданные при создании, повторных модификациях, удалении и пересоздании ключа.",
    "theory": "В etcd v3 ревизия (Revision) — это 64-битный монотонно возрастающий счетчик кластера. В отличие от реляционных баз данных с табличными строками, в etcd любое действие записи (Put, Delete) увеличивает единую ревизию всего кластера.\n\nКаждая запись в etcd сопровождается тремя мета-полями:\n- `CreateRevision`: ревизия, на которой ключ был физически создан. Сохраняется неизменной при последующих обновлениях значения.\n- `ModRevision`: ревизия последней модификации данного ключа.\n- `Version`: локальный счетчик изменений ключа, начинающийся с 1. При удалении ключа счетчик сбрасывается в 0. При пересоздании начинается заново с 1.\n\nБлагодаря глобальным ревизиям etcd обеспечивает линеаризуемые снимки (Point-in-time Reads) и надежные подписки Watcher без race condition.",
    "step_by_step": [
        "Создайте структуру KeyMetadata с полями CreateRevision, ModRevision, Version и Value.",
        "Реализуйте MVCCStore с глобальным счетчиком mainRevision под защитой sync.RWMutex.",
        "В методе Put инкрементируйте mainRevision. Если ключ уже существует, сохраните CreateRevision и инкрементируйте Version.",
        "В методе Delete инкрементируйте mainRevision и удалите ключ из активного словаря.",
        "Проверьте, что при пересоздании ключа CreateRevision обновляется до текущей ревизии, а Version сбрасывается в 1."
    ],
    "code_blocks": [{
        "filename": "etcd_mvcc_model.go",
        "lang": "go",
        "code": code2
    }],
    "under_the_hood": "В реальном etcd v3 в оперативной памяти поддерживается древовидный индекс B-Tree (`treeIndex`). Он хранит для каждого ключа цепочку всех ревизий. Реальные значения и ключи хранятся в bbolt на диске, где ключом является пара `(revision, sub-revision)`, что делает запись строго последовательной (append-only) и оптимизированной под SSD.",
    "pitfalls": [
        "Путаница между Version и Revision: Version относится только к конкретному ключу и обнуляется при удалении. Revision — глобальное свойство всего кластера etcd, монотонно растущее на протяжении всей жизни кластера.",
        "Переполнение счетчика: 64-битный integer (int64) при 10 000 записей в секунду переполнится только через 29 миллионов лет, поэтому переполнение исключено."
    ],
    "bigtech_interview": "Как глобальные ревизии etcd используются в Kubernetes контроллерах? Kubernetes сохраняет `ModRevision` как `metadata.resourceVersion`. Контроллеры используют optimistic concurrency control: при обновлении объекта в etcd отправляется проверка 'обновить только если resourceVersion не изменился'."
})

# Ex 3: Подключение к кластеру etcd на Go (clientv3)
code3 = r'''package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"os"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
)

// EtcdConnectionManager управляет жизненным циклом клиента etcd
type EtcdConnectionManager struct {
	client *clientv3.Client
}

// NewEtcdClient создает подключение с настройкой mTLS и таймаутов
func NewEtcdClient(endpoints []string, dialTimeout time.Duration, certFile, keyFile, caFile string) (*clientv3.Client, error) {
	var tlsConfig *tls.Config

	if certFile != "" && keyFile != "" && caFile != "" {
		cert, err := tls.LoadX509KeyPair(certFile, keyFile)
		if err != nil {
			return nil, fmt.Errorf("ошибка загрузки сертификата клиента: %w", err)
		}

		caData, err := os.ReadFile(caFile)
		if err != nil {
			return nil, fmt.Errorf("ошибка чтения CA файла: %w", err)
		}

		caPool := x509.NewCertPool()
		if !caPool.AppendCertsFromPEM(caData) {
			return nil, fmt.Errorf("не удалось распарсить CA сертификат")
		}

		tlsConfig = &tls.Config{
			Certificates: []tls.Certificate{cert},
			RootCAs:      caPool,
			MinVersion:   tls.VersionTLS13,
		}
	}

	cli, err := clientv3.New(clientv3.Config{
		Endpoints:            endpoints,
		DialTimeout:          dialTimeout,
		DialKeepAliveTime:    10 * time.Second,
		DialKeepAliveTimeout: 3 * time.Second,
		TLS:                  tlsConfig,
		AutoSyncInterval:     30 * time.Second, // Периодическое автообновление списка активных узлов
	})
	if err != nil {
		return nil, fmt.Errorf("сбой инициализации clientv3: %w", err)
	}

	return cli, nil
}

func main() {
	// Демонстрация конфигурации подключения
	endpoints := []string{"http://127.0.0.1:2379", "http://127.0.0.1:22379", "http://127.0.0.1:32379"}
	timeout := 3 * time.Second

	fmt.Println("Инициализация пула подключения к кластеру etcd v3...")
	fmt.Printf("Эндпоинты кластера: %v\n", endpoints)
	fmt.Printf("DialTimeout: %v, TLS: опциональный mTLS\n", timeout)

	// Пример создания клиента с базовой конфигурацией
	cfg := clientv3.Config{
		Endpoints:   endpoints,
		DialTimeout: timeout,
	}

	client, err := clientv3.New(cfg)
	if err != nil {
		fmt.Printf("Ошибка подключения: %v\n", err)
		return
	}
	defer client.Close()

	fmt.Println("Клиент clientv3 успешно инициализирован (HTTP/2 gRPC транспорт настроен).")
}
'''
validate_go_code(code3, "code3")
exercises.append({
    "num": 3,
    "title": "Подключение к кластеру etcd на Go (clientv3)",
    "task": "Подключите официальную библиотеку go.etcd.io/etcd/client/v3. Напишите функцию инициализации клиента NewEtcdClient с поддержкой множественных эндпоинтов, таймаутов, авто-синхронизации топологии кластера (AutoSyncInterval) и настройки взаимной аутентификации по сертификатам (mTLS с TLS 1.3).",
    "theory": "`go.etcd.io/etcd/client/v3` — официальный клиентский SDK для etcd v3. В отличие от etcd v2 (который работал по протоколу HTTP/1.1 REST/JSON), v3 общается исключительно по бинарному протоколу gRPC поверх мультиплексированных соединений HTTP/2.\n\nКлючевые опции конфигурации клиента:\n1. `Endpoints`: срез адресов нод кластера (`host:port`). Клиент балансирует запросы между ними и автоматически переключается при сбое одной из нод.\n2. `AutoSyncInterval`: периодический опрос топологии кластера через `MemberList RPC`. Если в кластер добавилась новая нода, клиент автоматически начинает посылать запросы и на нее.\n3. `DialKeepAliveTime` и `DialKeepAliveTimeout`: периодические gRPC PING-пакеты для своевременного обнаружения мертвых TCP-соединений.\n4. `TLS`: взаимная аутентификация клиента и сервера (mTLS) — обязательный стандарт безопасности для доступа к etcd в корпоративных кластерах.",
    "step_by_step": [
        "Изучите структуру clientv3.Config и опции подключения.",
        "Реализуйте функцию загрузки x509 клиентских сертификатов и CA пула для TLS.",
        "Настройте параметры gRPC KeepAlive для упреждающего контроля соединений.",
        "Инициализируйте клиент clientv3.New() и настройте корректный defer client.Close().",
        "Проверьте обработку ошибок инициализации."
    ],
    "code_blocks": [{
        "filename": "etcd_client_init.go",
        "lang": "go",
        "code": code3
    }],
    "under_the_hood": "При вызове `clientv3.New()` создается пул соединений `grpc.ClientConn`. По умолчанию etcd Go клиент использует Round-Robin балансировку gRPC между переданными эндпоинтами для операций чтения. Запросы на запись перенаправляются лидером кластера.",
    "pitfalls": [
        "Отсутствие client.Close(): клиент etcd держит фоновые горутины KeepAlive и HTTP/2 потоки. Утечка экземпляров клиента ведет к утечке файловых дескрипторов и памяти.",
        "Короткий DialTimeout: при сетевой нестабильности слишком короткий таймаут (< 1s) приведет к невозможности поднять gRPC соединение при холодном старте сервиса."
    ],
    "bigtech_interview": "Что произойдет, если нода etcd, к которой подключен клиент, внезапно упадет? gRPC транспорт под капотом clientv3 автоматически зафиксирует обрыв потока и прозрачно перенаправит последующие вызовы на следующую здоровую ноду из списка Endpoints."
})

# Ex 4: Базовые операции с ключами: Put, Get, Delete
code4 = r'''package main

import (
	"context"
	"fmt"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
)

// KeyValueService абстрагирует CRUD операции над etcd v3
type KeyValueService struct {
	kv clientv3.KV
}

func NewKeyValueService(client *clientv3.Client) *KeyValueService {
	return &KeyValueService{kv: clientv3.NewKV(client)}
}

// PutKey записывает ключ и возвращает ревизию изменения
func (s *KeyValueService) PutKey(ctx context.Context, key, val string) (int64, error) {
	resp, err := s.kv.Put(ctx, key, val)
	if err != nil {
		return 0, err
	}
	return resp.Header.Revision, nil
}

// GetKey читает значение и метаданные ключа
func (s *KeyValueService) GetKey(ctx context.Context, key string) (string, int64, int64, error) {
	resp, err := s.kv.Get(ctx, key)
	if err != nil {
		return "", 0, 0, err
	}
	if len(resp.Kvs) == 0 {
		return "", 0, 0, fmt.Errorf("ключ %s не найден", key)
	}

	kv := resp.Kvs[0]
	return string(kv.Value), kv.CreateRevision, kv.ModRevision, nil
}

// DeleteKey удаляет ключ и возвращает число удаленных элементов
func (s *KeyValueService) DeleteKey(ctx context.Context, key string) (int64, error) {
	resp, err := s.kv.Delete(ctx, key)
	if err != nil {
		return 0, err
	}
	return resp.Deleted, nil
}

func main() {
	// Демонстрация сигнатур и работы интерфейса clientv3.KV
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	fmt.Println("Операции Put / Get / Delete через интерфейс clientv3.KV:")
	fmt.Println(" 1. Put(ctx, key, val) -> *PutResponse (resp.Header.Revision)")
	fmt.Println(" 2. Get(ctx, key) -> *GetResponse (resp.Kvs[0].CreateRevision, ModRevision, Version)")
	fmt.Println(" 3. Delete(ctx, key) -> *DeleteResponse (resp.Deleted)")
	_ = ctx
}
'''
validate_go_code(code4, "code4")
exercises.append({
    "num": 4,
    "title": "Базовые операции с ключами: Put, Get, Delete",
    "task": "Используя интерфейс clientv3.KV, реализуйте сервис KeyValueService с базовыми операциями PutKey, GetKey и DeleteKey. Извлеките из ответов etcd метаданные ревизий (Header.Revision, CreateRevision, ModRevision) и количество удаленных ключей.",
    "theory": "Интерфейс `clientv3.KV` предоставляет низкоуровневый доступ к хранилищу etcd:\n- `Put(ctx, key, val, opts...)`: сохраняет пару ключ-значение. Возвращает `*PutResponse`. Поле `Header.Revision` отражает текущую ревизию кластера после применения данной записи.\n- `Get(ctx, key, opts...)`: считывает ключ. Возвращает `*GetResponse`. Срез `resp.Kvs` содержит найденные записи типа `*mvccpb.KeyValue`. Если ключ отсутствует, срез `resp.Kvs` будет пустым (len == 0), что не является ошибкой Go.\n- `Delete(ctx, key, opts...)`: удаляет ключ. Поле `resp.Deleted` сообщает, сколько именно ключей было удалено (0 или 1 при точном поиске, либо > 1 при удалении по префиксу).",
    "step_by_step": [
        "Инициализируйте интерфейс clientv3.KV через clientv3.NewKV(client).",
        "Реализуйте метод PutKey с возвратом глобальной ревизии операции.",
        "Реализуйте метод GetKey с безопасной проверкой наличия записей в resp.Kvs.",
        "Извлеките значения Value, CreateRevision и ModRevision.",
        "Реализуйте метод DeleteKey с проверкой количества удаленных сущностей."
    ],
    "code_blocks": [{
        "filename": "etcd_kv_crud.go",
        "lang": "go",
        "code": code4
    }],
    "under_the_hood": "По умолчанию `Get` в etcd v3 линеаризуем (Linearizable Read): перед возвратом данных клиент делает раунд обмена `ReadIndex` через протокол Raft, чтобы гарантировать, что опрашиваемый узел не находится в изолированном меньшинстве и возвращает самые свежие данные. Для сверхбыстрого, но потенциально устаревшего чтения можно передать `clientv3.WithSerializable()`.",
    "pitfalls": [
        "Panic при пустом Kvs: если ключ не найден в etcd, `resp.Kvs` пуст. Попытка немедленного обращения `resp.Kvs[0]` вызовет `runtime error: index out of range`.",
        "Размер значения: etcd жестко ограничивает максимальный размер одного значения (по умолчанию 1.5 МБ). Попытка положить большой бинарный блоб вернет ошибку `etcdserver: request is too large`."
    ],
    "bigtech_interview": "В чем отличие линеаризуемого чтения от сериализуемого в etcd? Линеаризуемое (дефолт) опрашивает кворум узлов через Raft ReadIndex (задержка RTT), гарантируя строго свежие данные. Сериализуемое (`WithSerializable()`) читает локально из памяти узла без сетевых запросов (микросекунды), но может вернуть немного устаревшие данные."
})

# Ex 5: Поиск по диапазону ключей (Range) и префиксный поиск
code5 = r'''package main

import (
	"context"
	"fmt"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
)

// PrefixSearchService осуществляет сканирование пространств ключей etcd
type PrefixSearchService struct {
	kv clientv3.KV
}

func NewPrefixSearchService(kv clientv3.KV) *PrefixSearchService {
	return &PrefixSearchService{kv: kv}
}

// GetByPrefix вычитывает все ключи с заданным иерархическим префиксом
func (s *PrefixSearchService) GetByPrefix(ctx context.Context, prefix string) (map[string]string, error) {
	resp, err := s.kv.Get(ctx, prefix, clientv3.WithPrefix())
	if err != nil {
		return nil, fmt.Errorf("ошибка префиксного поиска: %w", err)
	}

	result := make(map[string]string, len(resp.Kvs))
	for _, item := range resp.Kvs {
		result[string(item.Key)] = string(item.Value)
	}
	return result, nil
}

// GetByAlphabeticalRange вычитывает диапазон ключей [startKey, endKey)
func (s *PrefixSearchService) GetByAlphabeticalRange(ctx context.Context, startKey, endKey string) ([]string, error) {
	resp, err := s.kv.Get(ctx, startKey, clientv3.WithRange(endKey))
	if err != nil {
		return nil, fmt.Errorf("ошибка диапазонного запроса: %w", err)
	}

	keys := make([]string, 0, len(resp.Kvs))
	for _, item := range resp.Kvs {
		keys = append(keys, fmt.Sprintf("%s = %s", string(item.Key), string(item.Value)))
	}
	return keys, nil
}

// DeleteByPrefix атомарно удаляет все ключи в иерархической подпапке
func (s *PrefixSearchService) DeleteByPrefix(ctx context.Context, prefix string) (int64, error) {
	resp, err := s.kv.Delete(ctx, prefix, clientv3.WithPrefix())
	if err != nil {
		return 0, err
	}
	return resp.Deleted, nil
}

func main() {
	fmt.Println("Префиксный и диапазонный поиск в etcd v3:")
	fmt.Println(" 1. clientv3.WithPrefix() транслирует префикс '/services/' в диапазон ['/services/', '/services0')")
	fmt.Println(" 2. clientv3.WithRange(endKey) выполняет лексикографический скан от startKey до endKey")
	fmt.Println(" 3. Delete с WithPrefix() удаляет целые директории ключей одной операцией")
}
'''
validate_go_code(code5, "code5")
exercises.append({
    "num": 5,
    "title": "Поиск по диапазону ключей (Range) и префиксный поиск",
    "task": "Реализуйте методы префиксного и диапазонного чтения пространства ключей etcd. Напишите функции GetByPrefix (с опцией clientv3.WithPrefix()) и GetByAlphabeticalRange (с опцией clientv3.WithRange()), а также массовое удаление по префиксу DeleteByPrefix.",
    "theory": "В etcd v3 нет концепции реальных папок и файлов, но ключи упорядочены лексикографически в B-Tree. Иерархические пути (`/configs/billing/tax_rate`) эмулируются префиксами.\n\nКак работает префиксный поиск:\nОпция `clientv3.WithPrefix()` — это синтаксический сахар над диапазонным запросом `WithRange(endKey)`. etcd берет последний байт префикса и инкрементирует его на 1. Например, для префикса `/configs/a` конечным ключом диапазона становится `/configs/b`. Все ключи, попадающие в полуинтервал `[\"/configs/a\", \"/configs/b\")`, возвращаются клиенту.",
    "step_by_step": [
        "Создайте сервис PrefixSearchService с полем clientv3.KV.",
        "Реализуйте метод GetByPrefix, передавая clientv3.WithPrefix().",
        "Преобразуйте срез resp.Kvs в результирующую карту map[string]string.",
        "Реализуйте метод GetByAlphabeticalRange с опцией clientv3.WithRange().",
        "Реализуйте массовое удаление DeleteByPrefix с возвратом счетчика удаленных ключей."
    ],
    "code_blocks": [{
        "filename": "etcd_prefix_range.go",
        "lang": "go",
        "code": code5
    }],
    "under_the_hood": "Поскольку в bbolt и в in-memory B-Tree etcd ключи отсортированы побайтово, поиск по диапазону выполняется за `O(log N + M)`, где N — общее число ключей в базе, а M — количество элементов в возвращаемом диапазоне. Это на порядки быстрее сканирования полнотекстовых баз данных.",
    "pitfalls": [
        "Непреднамеренное удаление всей базы: вызов `client.Delete(ctx, \"\", clientv3.WithPrefix())` удалит АБСОЛЮТНО ВСЕ КЛЮЧИ в кластере etcd! Всегда строго валидируйте входящий префикс на непустоту.",
        "Слишком широкий префикс: чтение префикса `/` в большом кластере приведет к выгрузке сотен тысяч ключей и OOM-падению приложения."
    ],
    "bigtech_interview": "Как Kubernetes организует хранилище объектов в etcd? Kubernetes использует жесткую префиксную схему: `/registry/<resource_type>/<namespace>/<name>`. Например, `/registry/pods/default/nginx-pod`. Это позволяет API-серверу мгновенно получать все поды неймспейса одним префиксным вызовом."
})

# Ex 6: Постраничная выгрузка и сортировка ключей в etcd
code6 = r'''package main

import (
	"context"
	"fmt"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
)

// EtcdPaginator обеспечивает постраничную вычитку большого объема ключей
type EtcdPaginator struct {
	kv       clientv3.KV
	pageSize int64
}

func NewEtcdPaginator(kv clientv3.KV, pageSize int64) *EtcdPaginator {
	return &EtcdPaginator{kv: kv, pageSize: pageSize}
}

// FetchAllPaged читает все ключи по префиксу пачками без риска исчерпания памяти
func (p *EtcdPaginator) FetchAllPaged(ctx context.Context, prefix string, processBatch func(batch []*clientv3.GetResponse) error) (int, error) {
	// Базовые опции: лимит страницы и сортировка ключей
	opts := []clientv3.OpOption{
		clientv3.WithPrefix(),
		clientv3.WithSort(clientv3.SortByKey, clientv3.SortAscend),
		clientv3.WithLimit(p.pageSize),
	}

	currentKey := prefix
	totalCount := 0

	for {
		// При переходе на следующую страницу начинаем с последнего прочитанного ключа
		pageOpts := append(opts, clientv3.WithFromKey())
		resp, err := p.kv.Get(ctx, currentKey, pageOpts...)
		if err != nil {
			return totalCount, fmt.Errorf("ошибка постраничного чтения: %w", err)
		}

		if len(resp.Kvs) == 0 {
			break
		}

		totalCount += len(resp.Kvs)

		// Если на первой итерации прочитано меньше pageSize элементов, страниц больше нет
		if int64(len(resp.Kvs)) < p.pageSize {
			break
		}

		// Следующий ключ для WithFromKey — добавляем нулевой байт к последнему ключу пачки
		lastKey := resp.Kvs[len(resp.Kvs)-1].Key
		currentKey = string(append(lastKey, 0x00))
	}

	return totalCount, nil
}

func main() {
	fmt.Println("Постраничная выгрузка (Pagination) в etcd v3:")
	fmt.Println(" 1. WithLimit(N) ограничивает размер пачки")
	fmt.Println(" 2. WithSort(clientv3.SortByKey, clientv3.SortAscend) гарантирует стабильный порядок")
	fmt.Println(" 3. WithFromKey() в сочетании с lastKey + 0x00 исключает дублирование пограничных элементов")
}
'''
validate_go_code(code6, "code6")
exercises.append({
    "num": 6,
    "title": "Постраничная выгрузка и сортировка ключей в etcd",
    "task": "Спроектируйте компонент EtcdPaginator для безопасной постраничной выгрузки сотен тысяч ключей. Используйте комбинацию опций clientv3.WithLimit, clientv3.WithSort и clientv3.WithFromKey с правильным инкрементом пограничного ключа через добавление нулевого байта.",
    "theory": "В продуктовом кластере etcd могут храниться миллионы записей (например, реестр маршрутов или пользовательских сессий). Попытка вычитать весь каталог за один запрос `Get(ctx, prefix, WithPrefix())` чревата серьезными проблемами:\n1. Гигантский gRPC ответ превысит лимит `MaxCallRecvMsgSize` (по умолчанию 4 МБ) и вызовет падение клиента.\n2. Пауза GC в Go вырастет из-за выделения сотен мегабайт в куче под единый срез.\n3. etcd потратит значительные процессорные ресурсы на формирование одного гигантского ответа.\n\nПравильное решение — Cursor-based пагинация:\n- Запрашиваем пачку из N элементов (`WithLimit(N)`).\n- Сортируем по возрастанию ключа (`WithSort(SortByKey, SortAscend)`).\n- Для следующей страницы начинаем поиск от `lastKey + 0x00` с помощью `WithFromKey()`, предотвращая повторную обработку последнего ключа предыдущей страницы.",
    "step_by_step": [
        "Создайте структуру EtcdPaginator с параметром размера страницы pageSize.",
        "Сформируйте опции сортировки clientv3.WithSort(SortByKey, SortAscend) и лимита clientv3.WithLimit.",
        "Реализуйте цикл выгрузки с использованием WithFromKey().",
        "Для избежания зацикливания добавьте нулевой байт (0x00) к последнему элементу пачки перед следующим запросом.",
        "Завершите цикл, если размер пачки меньше pageSize."
    ],
    "code_blocks": [{
        "filename": "etcd_pagination.go",
        "lang": "go",
        "code": code6
    }],
    "under_the_hood": "Добавление байта `0x00` — стандартная идиома в лексикографических системах (etcd, RocksDB, LevelDB). Ключ `\"/users/1\" + 0x00` строго больше `\"/users/1\"`, но меньше любого другого допустимого ключа (например, `\"/users/2\"`), что обеспечивает точный сдвиг курсора без пропусков.",
    "pitfalls": [
        "Зацикливание при повторном чтении lastKey: если просто передать `lastKey` в `WithFromKey()`, он вернется первым элементом в следующей странице, вызвав дублирование записей и бесконечный цикл.",
        "Изменение данных во время пагинации: если во время постраничной выгрузки в etcd добавляются новые ключи, они могут попасть в срез. Чтобы зафиксировать неизменяемый снимок, следует передать `clientv3.WithRev(snapshotRevision)`."
    ],
    "bigtech_interview": "Как в Kubernetes `kubectl get pods --all-namespaces` избегает падения etcd при миллионах подов? Используется chunking (пагинация) через параметры `limit` и `continue` (который хранит etcd cursor revision), вычитывая данные страницами по 500 штук."
})

# Ex 7: Механизм аренды (Leases) и TTL ключей
code7 = r'''package main

import (
	"context"
	"fmt"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
)

// EphemeralStore управляет временными ключами с TTL через Leases
type EphemeralStore struct {
	client *clientv3.Client
	lease  clientv3.Lease
	kv     clientv3.KV
}

func NewEphemeralStore(cli *clientv3.Client) *EphemeralStore {
	return &EphemeralStore{
		client: cli,
		lease:  clientv3.NewLease(cli),
		kv:     clientv3.NewKV(cli),
	}
}

// PutWithTTL создает аренду на ttlSeconds и привязывает к ней ключ
func (s *EphemeralStore) PutWithTTL(ctx context.Context, key, val string, ttlSeconds int64) (clientv3.LeaseID, error) {
	// 1. Создаем объект аренды в кластере
	grantResp, err := s.lease.Grant(ctx, ttlSeconds)
	if err != nil {
		return 0, fmt.Errorf("ошибка создания аренды: %w", err)
	}

	leaseID := grantResp.ID

	// 2. Привязываем ключ к аренде
	_, err = s.kv.Put(ctx, key, val, clientv3.WithLease(leaseID))
	if err != nil {
		// Откатываем аренду при сбое
		_, _ = s.lease.Revoke(ctx, leaseID)
		return 0, fmt.Errorf("ошибка привязки ключа к аренде: %w", err)
	}

	return leaseID, nil
}

// AttachKeyToExistingLease привязывает дополнительный ключ к существующей аренде
func (s *EphemeralStore) AttachKeyToExistingLease(ctx context.Context, key, val string, leaseID clientv3.LeaseID) error {
	_, err := s.kv.Put(ctx, key, val, clientv3.WithLease(leaseID))
	return err
}

// RevokeLease досрочно отзывает аренду (удаляя все привязанные ключи)
func (s *EphemeralStore) RevokeLease(ctx context.Context, leaseID clientv3.LeaseID) error {
	_, err := s.lease.Revoke(ctx, leaseID)
	return err
}

func main() {
	fmt.Println("Механизм аренды (Leases) в etcd v3:")
	fmt.Println(" 1. client.Grant(ctx, ttl) создает один LeaseID на несколько секунд")
	fmt.Println(" 2. Десятки ключей могут привязываться к ОДНОМУ LeaseID через WithLease(id)")
	fmt.Println(" 3. При истечении TTL или вызове Revoke(id) etcd удаляет ВСЕ привязанные ключи")
}
'''
validate_go_code(code7, "code7")
exercises.append({
    "num": 7,
    "title": "Механизм аренды (Leases) и TTL ключей",
    "task": "Изучите механизм аренды (Lease) в etcd v3. Реализуйте сервис EphemeralStore с методами PutWithTTL, AttachKeyToExistingLease и RevokeLease. Покажите, как один объект аренды с единым LeaseID может управлять временем жизни множества связанных ключей.",
    "theory": "В Redis каждый ключ имеет собственный таймер TTL. В etcd архитекторы применили принципиально иную, высокомасштабируемую модель: концепцию аренды (Lease).\n\nОбъект Lease создается в кластере вызовом `client.Grant(ctx, ttl)` и получает уникальный 64-битный идентификатор `LeaseID`.\nПреимущества архитектуры Leases:\n1. Группировка ресурсов: к одному `LeaseID` можно привязать сотни ключей (`/services/payments/host1`, `/metrics/host1`, `/status/host1`).\n2. Минимальные накладные расходы: etcd отслеживает таймер только для объекта аренды, а не для каждого ключа в отдельности.\n3. Атомарное каскадное удаление: как только срок аренды истекает (или вызывается `Revoke`), etcd атомарно удаляет абсолютно все ключи, привязанные к этой аренде.",
    "step_by_step": [
        "Инициализируйте интерфейсы clientv3.Lease и clientv3.KV.",
        "Реализуйте метод PutWithTTL: вызовите lease.Grant(ctx, ttlSeconds) для получения LeaseID.",
        "Сохраните ключ с опцией clientv3.WithLease(leaseID).",
        "Напишите метод AttachKeyToExistingLease для переиспользования существующего LeaseID.",
        "Реализуйте досрочный отзыв аренды через lease.Revoke."
    ],
    "code_blocks": [{
        "filename": "etcd_leases_ttl.go",
        "lang": "go",
        "code": code7
    }],
    "under_the_hood": "Внутри etcd хранит список аренд в куче минимальных элементов (Min-Heap) по времени истечения. Каждые 500 мс фоновый таймер проверяет вершину кучи. Если аренда истекла, etcd генерирует Raft-команду на удаление всех ассоциированных с ней ключей.",
    "pitfalls": [
        "Создание отдельного Lease на каждый ключ: если на 100 000 ключей создать 100 000 отдельных Leases, таймер etcd перегрузится. Все ключи одного сервиса/узла должны шарить единый `LeaseID`.",
        "Отказ от явного Revoke: если сервис штатно завершает работу, вызов `Revoke` освобождает ресурсы немедленно, не дожидаясь истечения таймаута."
    ],
    "bigtech_interview": "Почему в etcd TTL задается в секундах, а не миллисекундах? etcd предназначен для распределенной координации сервисов, блокировок и обнаружения узлов, где гранулярность в секундах оптимальна. Высокочастотные миллисекундные таймеры перегрузили бы протокол консенсуса Raft постоянными обновлениями."
})

# Ex 8: Автоматическое продление аренды (Lease KeepAlive)
code8 = r'''package main

import (
	"context"
	"fmt"
	"sync"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
)

// HeartbeatService поддерживает жизнь аренды в фоновом режиме
type HeartbeatService struct {
	client  *clientv3.Client
	lease   clientv3.Lease
	leaseID clientv3.LeaseID
	stopCh  chan struct{}
	wg      sync.WaitGroup
}

func NewHeartbeatService(cli *clientv3.Client) *HeartbeatService {
	return &HeartbeatService{
		client: cli,
		lease:  clientv3.NewLease(cli),
		stopCh: make(chan struct{}),
	}
}

// StartKeepAlive создает аренду и запускает непрерывное продление
func (h *HeartbeatService) StartKeepAlive(ctx context.Context, ttl int64) (clientv3.LeaseID, error) {
	grantResp, err := h.lease.Grant(ctx, ttl)
	if err != nil {
		return 0, fmt.Errorf("ошибка grant lease: %w", err)
	}

	h.leaseID = grantResp.ID

	// KeepAlive запускает gRPC двунаправленный стрим продления
	keepAliveChan, err := h.lease.KeepAlive(ctx, h.leaseID)
	if err != nil {
		_, _ = h.lease.Revoke(ctx, h.leaseID)
		return 0, fmt.Errorf("ошибка запуска keepalive: %w", err)
	}

	h.wg.Add(1)
	go func() {
		defer h.wg.Done()
		for {
			select {
			case <-h.stopCh:
				fmt.Println("[KEEPALIVE] Остановка продления по сигналу сервиса")
				return
			case kaResp, ok := <-keepAliveChan:
				if !ok {
					fmt.Printf("⚠️ [KEEPALIVE CRITICAL] Канал продления закрыт! Аренда %x утеряна\n", h.leaseID)
					return
				}
				// kaResp.TTL содержит актуальный подтвержденный TTL от сервера etcd
				_ = kaResp
			}
		}
	}()

	return h.leaseID, nil
}

func (h *HeartbeatService) Stop(ctx context.Context) error {
	close(h.stopCh)
	h.wg.Wait()
	if h.leaseID != 0 {
		_, err := h.lease.Revoke(ctx, h.leaseID)
		return err
	}
	return nil
}

func main() {
	fmt.Println("Автоматическое продление аренды (Lease KeepAlive):")
	fmt.Println(" 1. client.KeepAlive(ctx, id) возвращает канал подтверждений <-chan *LeaseKeepAliveResponse")
	fmt.Println(" 2. Закрытие канала ok == false сигнализирует о разрыве связи или удалении аренды на сервере")
	fmt.Println(" 3. При штатной остановке вызывается Revoke() для немедленного удаления эфемерных записей")
}
'''
validate_go_code(code8, "code8")
exercises.append({
    "num": 8,
    "title": "Автоматическое продление аренды (Lease KeepAlive)",
    "task": "Реализуйте подсистему непрерывного продления аренды HeartbeatService с помощью метода client.KeepAlive. Организуйте фоновый воркер, слушающий канал <-chan *clientv3.LeaseKeepAliveResponse, и предусмотрите корректную обработку обрыва связи и штатный отзыв аренды при завершении сервиса.",
    "theory": "Чтобы узел считался живым в кластере, его регистрационные ключи не должны исчезать. Однако ручная отправка команд `KeepAliveOnce` в цикле `for range time.Tick` неэффективна и создает избыточные TCP-запросы.\n\nВ Go SDK метод `client.KeepAlive(ctx, leaseID)` открывает постоянный двунаправленный gRPC-стрим к etcd:\n- Клиент автоматически рассчитывает оптимальную частоту отправки пингов (обычно `TTL / 3`).\n- Ответы сервера передаются в канал `<-chan *clientv3.LeaseKeepAliveResponse`.\n- Если канал закрывается (`!ok`), это свидетельствует о серьезной аварии: аренда истекла на сервере (например, из-за сетевого раздела split-brain или паузы GC) либо связь с кластером разорвана. Сервис должен немедленно перейти в режим перерегистрации.",
    "step_by_step": [
        "Создайте структуру HeartbeatService с каналом завершения stopCh и sync.WaitGroup.",
        "Вызовите lease.Grant для выделения аренды с базовым TTL.",
        "Запустите двунаправленный стрим через lease.KeepAlive().",
        "В отдельной горутине читайте входящие ответы из keepAliveChan с проверкой закрытия канала.",
        "Реализуйте метод Stop с гарантированным отзывом аренды через Revoke."
    ],
    "code_blocks": [{
        "filename": "etcd_keepalive_service.go",
        "lang": "go",
        "code": code8
    }],
    "under_the_hood": "gRPC стрим KeepAlive мультиплексируется в то же самое единое HTTP/2 TCP-соединение, что и обычные вызовы KV. При кратковременном сетевом сбое clientv3 автоматически пытается переподключить стрим без вмешательства разработчика до тех пор, пока контекст не отменен.",
    "pitfalls": [
        "Игнорирование закрытия канала: если горутина не проверяет `ok := <-keepAliveChan`, она завершится или начнет крутиться вхолостую, а сервис не узнает, что его ключи уже удалены из реестра кластера.",
        "Утечка горутин продления: если не отменять context или не закрывать канал stopCh, фоновая горутина продолжит работать вечно."
    ],
    "bigtech_interview": "Что произойдет с ключами сервиса при долгой Stop-The-World паузе GC в Go приложении? Если пауза GC превысит время TTL аренды (например, 15 секунд), etcd сочтет узел упавшим и удалит все его регистрационные ключи. Поэтому в HighLoad-системах TTL аренды выбирают с запасом (обычно 10–15 секунд)."
})

# Ex 9: Реализация Service Discovery на базе etcd и Leases
code9 = r'''package main

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
)

// ServiceInstance описывает метаданные регистрируемого экземпляра микросервиса
type ServiceInstance struct {
	ServiceName string            `json:"service_name"`
	InstanceID  string            `json:"instance_id"`
	Address     string            `json:"address"`
	Metadata    map[string]string `json:"metadata"`
}

// ServiceRegistrar регистрирует сервис в etcd с автоматическим продлением аренды
type ServiceRegistrar struct {
	client  *clientv3.Client
	lease   clientv3.Lease
	kv      clientv3.KV
	leaseID clientv3.LeaseID
	cancel  context.CancelFunc
	wg      sync.WaitGroup
}

func NewServiceRegistrar(cli *clientv3.Client) *ServiceRegistrar {
	return &ServiceRegistrar{
		client: cli,
		lease:  clientv3.NewLease(cli),
		kv:     clientv3.NewKV(cli),
	}
}

// Register публикует инстанс сервиса в etcd с TTL и запускает KeepAlive
func (r *ServiceRegistrar) Register(ctx context.Context, inst ServiceInstance, ttlSeconds int64) error {
	grantResp, err := r.lease.Grant(ctx, ttlSeconds)
	if err != nil {
		return fmt.Errorf("сбой grant lease: %w", err)
	}
	r.leaseID = grantResp.ID

	key := fmt.Sprintf("/services/%s/%s", inst.ServiceName, inst.InstanceID)
	val, err := json.Marshal(inst)
	if err != nil {
		return err
	}

	_, err = r.kv.Put(ctx, key, string(val), clientv3.WithLease(r.leaseID))
	if err != nil {
		_, _ = r.lease.Revoke(ctx, r.leaseID)
		return fmt.Errorf("сбой регистрации ключа сервиса: %w", err)
	}

	kaCtx, cancel := context.WithCancel(context.Background())
	r.cancel = cancel

	keepAliveCh, err := r.lease.KeepAlive(kaCtx, r.leaseID)
	if err != nil {
		cancel()
		return fmt.Errorf("сбой KeepAlive: %w", err)
	}

	r.wg.Add(1)
	go func() {
		defer r.wg.Done()
		for range keepAliveCh {
			// Аренда успешно продлевается
		}
		fmt.Printf("[DISCOVERY] Регистрация экземпляра %s прекращена\n", inst.InstanceID)
	}()

	fmt.Printf("[DISCOVERY] Сервис %s зарегистрирован по ключу %s (LeaseID=%x, TTL=%ds)\n",
		inst.ServiceName, key, r.leaseID, ttlSeconds)
	return nil
}

// Unregister производит корректную дерегистрацию сервиса
func (r *ServiceRegistrar) Unregister(ctx context.Context) error {
	if r.cancel != nil {
		r.cancel()
	}
	r.wg.Wait()
	if r.leaseID != 0 {
		_, err := r.lease.Revoke(ctx, r.leaseID)
		return err
	}
	return nil
}

func main() {
	inst := ServiceInstance{
		ServiceName: "payment-service",
		InstanceID:  "node-eu-1",
		Address:     "10.240.0.15:9090",
		Metadata:    map[string]string{"version": "v2.4.0", "dc": "eu-central"},
	}

	data, _ := json.MarshalIndent(inst, "", "  ")
	fmt.Printf("Регистрация инстанса Service Discovery в etcd:\n%s\n", string(data))
	fmt.Println("Паттерн: ключ /services/<name>/<id> с привязкой к Lease KeepAlive")
}
'''
validate_go_code(code9, "code9")
exercises.append({
    "num": 9,
    "title": "Реализация Service Discovery на базе etcd и Leases",
    "task": "Спроектируйте компонент ServiceRegistrar для обнаружения сервисов (Service Discovery). При старте микросервис сериализует структуру ServiceInstance в JSON, регистрирует её по ключу /services/<name>/<id> с привязкой к LeaseID и поддерживает присутствие через фоновый KeepAlive. Реализуйте метод корректной дерегистрации Unregister.",
    "theory": "В динамических облачных средах (Kubernetes, Bare-metal кластеры) IP-адреса и порты микросервисов постоянно меняются в результате масштабирования, перебалансировки и перезапусков подов.\n\nПаттерн Service Discovery (Обнаружение сервисов) на базе etcd v3:\n1. Иерархический ключ: сервис регистрирует себя по пути `/services/<service_name>/<instance_id>`.\n2. Эфемерность через Leases: запись привязывается к аренде с TTL (10–15 сек).\n3. Устойчивость к авариям: если процесс сервиса падает (OOMKilled, SIGKILL) или нода физически обесточивается, стрим KeepAlive мгновенно прекращается. Спустя 15 секунд etcd самостоятельно удаляет ключ из каталога.\n4. Чистый Unregister: при штатном `SIGTERM` сервис отзывает аренду через `Revoke()`, и адрес исчезает из балансировщика за 5 миллисекунд.",
    "step_by_step": [
        "Определите структуру ServiceInstance с метаданными адреса, версии и идентификатора экземпляра.",
        "Создайте ServiceRegistrar с полями clientv3.Lease и clientv3.KV.",
        "В методе Register выделите аренду, сохраните JSON-описание инстанса и запустите KeepAlive в горутине.",
        "Обеспечьте сохранение функции отмены контекста cancel для остановки продления.",
        "Реализуйте метод Unregister с остановкой стрима и вызовом lease.Revoke."
    ],
    "code_blocks": [{
        "filename": "etcd_service_discovery.go",
        "lang": "go",
        "code": code9
    }],
    "under_the_hood": "Такой подход аналогичен механизму эфемерных нод (Ephemeral Nodes) в Apache ZooKeeper, но превосходит его по производительности: etcd не требует сохранения сессий в отдельных файлах состояния и масштабируется до десятков тысяч регистраций в секунду.",
    "pitfalls": [
        "Коллизия InstanceID: если два запущенных пода случайно используют одинаковый `InstanceID`, они начнут перезаписывать ключ друг друга в etcd, нарушая маршрутизацию.",
        "Большой объем метаданных: не следует сохранять в Service Discovery крупные объекты данных. Только IP, порт, протокол и версия."
    ],
    "bigtech_interview": "Почему etcd предпочтительнее Consul для Service Discovery в высоконадежных системах? etcd проще в эксплуатации, не имеет избыточного UI, строго следует спецификации Raft и имеет минимальное потребление ресурсов при поддержке официального Go SDK."
})

# Ex 10: Клиентский Service Resolver (Балансировка вызовов)
code10 = r'''package main

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"sync/atomic"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
)

// DiscoveredEndpoint содержит адрес и метаданные сервиса
type DiscoveredEndpoint struct {
	InstanceID string `json:"instance_id"`
	Address    string `json:"address"`
}

// ClientServiceResolver осуществляет клиентскую балансировку по данным etcd
type ClientServiceResolver struct {
	cli         *clientv3.Client
	serviceName string
	mu          sync.RWMutex
	endpoints   []DiscoveredEndpoint
	rrIndex     atomic.Uint64
}

func NewClientServiceResolver(cli *clientv3.Client, serviceName string) *ClientServiceResolver {
	return &ClientServiceResolver{
		cli:         cli,
		serviceName: serviceName,
	}
}

// RefreshEndpoints запрашивает актуальный список инстансов из etcd
func (r *ClientServiceResolver) RefreshEndpoints(ctx context.Context) error {
	prefix := fmt.Sprintf("/services/%s/", r.serviceName)
	resp, err := r.cli.Get(ctx, prefix, clientv3.WithPrefix())
	if err != nil {
		return fmt.Errorf("ошибка разрешения эндпоинтов: %w", err)
	}

	var newEndpoints []DiscoveredEndpoint
	for _, kv := range resp.Kvs {
		var ep DiscoveredEndpoint
		if err := json.Unmarshal(kv.Value, &ep); err == nil && ep.Address != "" {
			newEndpoints = append(newEndpoints, ep)
		}
	}

	r.mu.Lock()
	r.endpoints = newEndpoints
	r.mu.Unlock()

	return nil
}

// NextEndpoint возвращает следующий адрес по алгоритму Round-Robin
func (r *ClientServiceResolver) NextEndpoint() (string, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if len(r.endpoints) == 0 {
		return "", fmt.Errorf("нет доступных инстансов для сервиса %s", r.serviceName)
	}

	idx := r.rrIndex.Add(1) - 1
	selected := r.endpoints[idx%uint64(len(r.endpoints))]
	return selected.Address, nil
}

func main() {
	resolver := &ClientServiceResolver{
		serviceName: "auth-service",
		endpoints: []DiscoveredEndpoint{
			{InstanceID: "auth-1", Address: "10.0.1.10:8080"},
			{InstanceID: "auth-2", Address: "10.0.1.11:8080"},
			{InstanceID: "auth-3", Address: "10.0.1.12:8080"},
		},
	}

	fmt.Println("Клиентская балансировка Round-Robin по эндпоинтам из etcd:")
	for i := 1; i <= 6; i++ {
		addr, _ := resolver.NextEndpoint()
		fmt.Printf(" Запрос #%d -> направлен на бэкенд: %s\n", i, addr)
	}
}
'''
validate_go_code(code10, "code10")
exercises.append({
    "num": 10,
    "title": "Клиентский Service Resolver (Балансировка вызовов)",
    "task": "Реализуйте компонент ClientServiceResolver для клиентской балансировки нагрузки (Client-Side Load Balancing). Резолвер считывает список активных инстансов по префиксу /services/<name>/, кэширует адреса и распределяет вызовы по алгоритму Round-Robin с использованием atomic.Uint64.",
    "theory": "В классической инфраструктуре клиент отправляет запрос на единый L4/L7 балансировщик (Nginx, HAProxy), который перенаправляет трафик на целевой узел. Это создает дополнительный сетевой хоп (Network Hop) и единую точку отказа.\n\nКлиентская балансировка (Client-Side Load Balancing), популяризованная gRPC и Finagle:\n1. Клиент сам периодически опрашивает etcd (или слушает Watcher) и хранит актуальный пул IP-адресов целевого сервиса.\n2. Запросы отправляются напрямую от клиента к нужному пода без промежуточных прокси.\n3. Алгоритм Round-Robin на `atomic.Uint64` обеспечивает равномерное распределение запросов с нулевыми накладными расходами на блокировки.",
    "step_by_step": [
        "Определите структуру DiscoveredEndpoint для хранения IP и порта инстанса.",
        "Спроектируйте ClientServiceResolver со списком эндпоинтов под защитой sync.RWMutex и счетчиком rrIndex.",
        "В методе RefreshEndpoints выполните префиксный запрос client.Get(ctx, prefix, WithPrefix()) и распарсите JSON.",
        "Реализуйте метод NextEndpoint: атомарный инкремент счетчика и вычисление индекса по модулю len(endpoints).",
        "Продемонстрируйте корректное циклическое распределение запросов."
    ],
    "code_blocks": [{
        "filename": "client_service_resolver.go",
        "lang": "go",
        "code": code10
    }],
    "under_the_hood": "В официальной библиотеке `google.golang.org/grpc/resolver` есть готовый интерфейс для подключения кастомных резолверов к пулу соединений gRPC. Клиент etcd v3 может выступать в качестве бэкенда для `grpc.Dial(\"etcd:///services/auth\", ...)`.",
    "pitfalls": [
        "Опрос etcd на каждый запрос: вызов `RefreshEndpoints` нельзя делать перед каждым HTTP-вызовом, иначе etcd упадет от нагрузки. Рефреш выполняется либо по таймеру раз в 10–30 секунд, либо реактивно по событиям Watcher.",
        "Деление на ноль: если список `endpoints` пуст, операция деления по модулю `% len(r.endpoints)` вызовет панику `integer divide by zero`. Обязательна проверка `len == 0`."
    ],
    "bigtech_interview": "В чем преимущество связки etcd Watcher + Client-Side Balancer перед классическим DNS Round-Robin? DNS кэшируется промежуточными серверами (TTL), из-за чего клиенты могут слать запросы на умерший узел еще несколько минут. Watcher в etcd доставляет события удаления узла за 1–2 миллисекунды."
})

# Ex 11: Подписка на изменения (Watchers) в реальном времени
code11 = r'''package main

import (
	"context"
	"fmt"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/api/v3/mvccpb"
)

// ConfigWatcher демонстрирует обработку потоковых событий изменения ключа
type ConfigWatcher struct {
	cli *clientv3.Client
}

func NewConfigWatcher(cli *clientv3.Client) *ConfigWatcher {
	return &ConfigWatcher{cli: cli}
}

// WatchKey слушает события по конкретному ключу
func (w *ConfigWatcher) WatchKey(ctx context.Context, key string) {
	watcher := clientv3.NewWatcher(w.cli)
	defer watcher.Close()

	// Watch возвращает канал событий clientv3.WatchChan
	watchChan := watcher.Watch(ctx, key)
	fmt.Printf("[WATCHER] Запущена подписка на ключ: %s\n", key)

	for watchResp := range watchChan {
		if watchResp.Canceled {
			fmt.Printf("[WATCHER] Подписка отменена: %v\n", watchResp.Err())
			return
		}

		for _, event := range watchResp.Events {
			switch event.Type {
			case mvccpb.PUT:
				fmt.Printf(" 📝 [EVENT PUT] Key=%s Val=%s (ModRev=%d, Version=%d)\n",
					string(event.Kv.Key), string(event.Kv.Value), event.Kv.ModRevision, event.Kv.Version)
				if event.PrevKv != nil {
					fmt.Printf("    Старое значение было: %s\n", string(event.PrevKv.Value))
				}
			case mvccpb.DELETE:
				fmt.Printf(" ❌ [EVENT DELETE] Key=%s (Удален на ModRev=%d)\n",
					string(event.Kv.Key), event.Kv.ModRevision)
			}
		}
	}
}

func main() {
	fmt.Println("Подписка на изменения (Watchers) в реальном времени:")
	fmt.Println(" 1. watcher.Watch(ctx, key) открывает постоянный gRPC поток")
	fmt.Println(" 2. mvccpb.PUT фиксирует создание или модификацию ключа")
	fmt.Println(" 3. mvccpb.DELETE сигнализирует об удалении (или истечении срока аренды)")
	fmt.Println(" 4. Опция clientv3.WithPrevKV() позволяет получить предыдущее значение до изменения")
}
'''
validate_go_code(code11, "code11")
exercises.append({
    "num": 11,
    "title": "Подписка на изменения (Watchers) в реальном времени",
    "task": "Изучите механизм Watchers в etcd v3. Создайте компонент ConfigWatcher, подписывающийся на поток событий по заданному ключу через clientv3.NewWatcher. Напишите цикл обработки событий, классифицирующий операции mvccpb.PUT и mvccpb.DELETE с извлечением метаданных ревизии и предыдущего значения (WithPrevKV).",
    "theory": "Механизм Watcher — одна из самых мощных возможностей etcd v3. Вместо неэффективного периодического поллинга (Polling) клиент открывает долгоживущий gRPC-поток, в который сервер etcd асинхронно пушит события в момент их коммита в Raft-лог.\n\nОсобенности архитектуры Watcher:\n1. Мультиплексирование потоков: сотни подписок на разные ключи внутри одного приложения передаются через единственный TCP/HTTP2 стрим.\n2. Типы событий: `mvccpb.PUT` (создание или перезапись) и `mvccpb.DELETE` (явное удаление или истечение Lease TTL).\n3. Опция `WithPrevKV()`: указывает etcd передать вместе с новым значением и предыдущее состояние ключа (`event.PrevKv`), что незаменимо для логирования аудита и отката транзакций.",
    "step_by_step": [
        "Инициализируйте наблюдатель clientv3.NewWatcher(client) с обязательным defer watcher.Close().",
        "Вызовите watcher.Watch(ctx, key) для получения канала WatchChan.",
        "Организуйте цикл for watchResp := range watchChan.",
        "Проверьте флаг watchResp.Canceled и ошибки отмены стрима.",
        "Используйте switch-case по event.Type (mvccpb.PUT vs mvccpb.DELETE)."
    ],
    "code_blocks": [{
        "filename": "etcd_watcher_stream.go",
        "lang": "go",
        "code": code11
    }],
    "under_the_hood": "На стороне сервера etcd все Watchers хранятся в двухуровневой структуре в памяти. При коммите новой ревизии etcd сопоставляет измененные ключи с активными вотчерами и собирает их в единый батч для отправки по HTTP/2, снижая накладные расходы до микросекунд.",
    "pitfalls": [
        "Незакрытый Watcher: если не вызывать `watcher.Close()` или не отменять контекст, сервер etcd будет продолжать удерживать вотчер в памяти, что приведет к утечке ресурсов на стороне кластера.",
        "Медленный обработчик событий: если в цикле обработки `range watchChan` выполнять тяжелые синхронные операции (запросы в БД), внутренний буфер канала переполнится, замедляя чтение."
    ],
    "bigtech_interview": "Как Kubernetes Informer использует etcd Watchers? Паттерн Reflector в client-go сначала делает `Get(prefix)` для начальной синхронизации локального кэша, сохраняет максимальную ревизию и сразу открывает `Watch(prefix, WithRev(lastRev))`, поддерживая 100% консистентность без нагрузки на etcd."
})

# Ex 12: Префиксное наблюдение за каталогом конфигурации
code12 = r'''package main

import (
	"context"
	"fmt"
	"strings"
	"sync"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/api/v3/mvccpb"
)

// DynamicConfigRegistry хранит конфигурацию микросервиса, обновляемую на лету
type DynamicConfigRegistry struct {
	cli    *clientv3.Client
	prefix string
	mu     sync.RWMutex
	params map[string]string
}

func NewDynamicConfigRegistry(cli *clientv3.Client, prefix string) *DynamicConfigRegistry {
	return &DynamicConfigRegistry{
		cli:    cli,
		prefix: prefix,
		params: make(map[string]string),
	}
}

// WatchCatalog запускает префиксный вотчер для целого каталога параметров
func (r *DynamicConfigRegistry) WatchCatalog(ctx context.Context) error {
	// 1. Начальная выгрузка всех параметров каталога
	initResp, err := r.cli.Get(ctx, r.prefix, clientv3.WithPrefix())
	if err != nil {
		return fmt.Errorf("ошибка начальной загрузки каталога: %w", err)
	}

	r.mu.Lock()
	for _, kv := range initResp.Kvs {
		cleanKey := strings.TrimPrefix(string(kv.Key), r.prefix)
		r.params[cleanKey] = string(kv.Value)
	}
	r.mu.Unlock()
	fmt.Printf("[CONFIG INIT] Загружено %d параметров из каталога %s (Rev=%d)\n",
		len(initResp.Kvs), r.prefix, initResp.Header.Revision)

	// 2. Запуск наблюдения с ревизии сразу после снимка
	watcher := clientv3.NewWatcher(r.cli)
	watchChan := watcher.Watch(ctx, r.prefix,
		clientv3.WithPrefix(),
		clientv3.WithRev(initResp.Header.Revision+1),
		clientv3.WithPrevKV(),
	)

	go func() {
		defer watcher.Close()
		for resp := range watchChan {
			for _, ev := range resp.Events {
				cleanKey := strings.TrimPrefix(string(ev.Kv.Key), r.prefix)
				r.mu.Lock()
				if ev.Type == mvccpb.PUT {
					r.params[cleanKey] = string(ev.Kv.Value)
					fmt.Printf("[CONFIG UPDATE] Параметр '%s' изменен на '%s'\n", cleanKey, string(ev.Kv.Value))
				} else if ev.Type == mvccpb.DELETE {
					delete(r.params, cleanKey)
					fmt.Printf("[CONFIG DELETE] Параметр '%s' удален\n", cleanKey)
				}
				r.mu.Unlock()
			}
		}
	}()

	return nil
}

func (r *DynamicConfigRegistry) Get(key string) string {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.params[key]
}

func main() {
	fmt.Println("Префиксное наблюдение за каталогом конфигурации в etcd v3:")
	fmt.Println(" 1. Initial Load: Get(prefix, WithPrefix()) фиксирует снапшот и startRevision")
	fmt.Println(" 2. Watch(prefix, WithPrefix(), WithRev(startRev+1)) ловит ВСЕ последующие изменения")
	fmt.Println(" 3. Локальный in-memory кэш гарантирует чтение за доли наносекунды")
}
'''
validate_go_code(code12, "code12")
exercises.append({
    "num": 12,
    "title": "Префиксное наблюдение за каталогом конфигурации",
    "task": "Спроектируйте реестр динамической конфигурации DynamicConfigRegistry. Реализуйте двухфазную схему: 1) Начальная вычитка каталога по префиксу через Get с сохранением ревизии, 2) Запуск префиксного Watcher с опциями WithPrefix() и WithRev(initRev+1) для обновления in-memory карты без потери событий.",
    "theory": "Частая ошибка начинающих инженеров — запустить `Watch(prefix)` и отдельно сделать `Get(prefix)`. Между выполнением `Get` и запуском `Watch` неизбежно возникает временное окно (race window), в течение которого сторонний сервис может изменить ключ. В результате это изменение не попадет ни в `Get`, ни в `Watch`, вызвав рассинхронизацию.\n\nКанонический паттерн надежной инициализации:\n1. Делаем `Get(prefix, WithPrefix())` и получаем `initResp.Header.Revision`.\n2. Наполняем локальную мапу в памяти данными из `initResp.Kvs`.\n3. Запускаем `Watch(prefix, WithPrefix(), WithRev(initResp.Header.Revision + 1))`.\nПоскольку etcd хранит историю изменений в MVCC, передача `WithRev(N+1)` гарантирует получение всех событий, произошедших строго после точки начального чтения.",
    "step_by_step": [
        "Создайте структуру DynamicConfigRegistry с локальной картой параметров под sync.RWMutex.",
        "Выполните начальный запрос client.Get(ctx, prefix, WithPrefix()) для заполнения карты.",
        "Извлеките ревизию initResp.Header.Revision.",
        "Запустите watcher.Watch с опциями WithPrefix() и WithRev(initRev+1).",
        "В горутине обновляйте локальную карту при событиях PUT и DELETE."
    ],
    "code_blocks": [{
        "filename": "etcd_prefix_watcher.go",
        "lang": "go",
        "code": code12
    }],
    "under_the_hood": "Опция `WithRev(rev)` обращается к MVCC-журналу etcd. Если запрошенная ревизия еще не была удалена процедурой компактификации (Compaction), etcd проиграет все исторические события из bbolt и передаст их в стрим, после чего прозрачно перейдет в режим реального времени.",
    "pitfalls": [
        "Обрезка префикса: если не удалять префикс `/configs/app/` при сохранении в локальную карту, приложению придется везде передавать полные пути.",
        "Отсутствие синхронизации доступа: локальная карта параметров должна защищаться `sync.RWMutex`, так как чтение из нее будет происходить параллельно с записью из горутины вотчера."
    ],
    "bigtech_interview": "Почему в production микросервисах предпочитают etcd Watchers вместо Consul Watches? Consul Watches под капотом используют механизм Long Polling HTTP/1.1 (постоянный перезапуск HTTP-запросов), что создает на порядки больший трафик и задержки по сравнению с мультиплексированным gRPC-стримом etcd."
})

# Ex 13: Надежная обработка разрыва соединения в Watcher
code13 = r'''package main

import (
	"context"
	"fmt"
	"sync/atomic"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
)

// ResilientWatcher обеспечивает надежное возобновление наблюдения при сбоях сети
type ResilientWatcher struct {
	cli          *clientv3.Client
	key          string
	lastRevision atomic.Int64
}

func NewResilientWatcher(cli *clientv3.Client, key string, startRev int64) *ResilientWatcher {
	w := &ResilientWatcher{cli: cli, key: key}
	w.lastRevision.Store(startRev)
	return w
}

// StartWatchLoop запускает устойчивый цикл наблюдения с авто-восстановлением
func (w *ResilientWatcher) StartWatchLoop(ctx context.Context, onEvent func(ev *clientv3.Event)) {
	backoff := 100 * time.Millisecond

	for {
		select {
		case <-ctx.Done():
			fmt.Println("[WATCHER LOOP] Завершение работы по контексту")
			return
		default:
		}

		currentRev := w.lastRevision.Load()
		fmt.Printf("[WATCHER RECONNECT] Подключение Watcher к ключу %s с ревизии %d...\n", w.key, currentRev+1)

		watcher := clientv3.NewWatcher(w.cli)
		watchChan := watcher.Watch(ctx, w.key, clientv3.WithRev(currentRev+1))

		watchErr := false
		for resp := range watchChan {
			if resp.Canceled {
				fmt.Printf("⚠️ [WATCHER CANCEL] Стрим разорван: %v\n", resp.Err())
				watchErr = true
				break
			}

			// Фиксируем последнюю обработанную ревизию
			if resp.Header.Revision > w.lastRevision.Load() {
				w.lastRevision.Store(resp.Header.Revision)
			}

			for _, ev := range resp.Events {
				if ev.Kv.ModRevision > w.lastRevision.Load() {
					w.lastRevision.Store(ev.Kv.ModRevision)
				}
				onEvent(ev)
			}
			backoff = 100 * time.Millisecond // Сбрасываем бэкофф при успешных событиях
		}

		watcher.Close()

		if watchErr {
			fmt.Printf("[WATCHER RETRY] Пауза перед переподключением: %v\n", backoff)
			time.Sleep(backoff)
			if backoff < 5*time.Second {
				backoff *= 2 // Экспоненциальный бэкофф
			}
		}
	}
}

func main() {
	fmt.Println("Надежная обработка разрыва соединения в Watcher:")
	fmt.Println(" 1. lastRevision непрерывно сохраняется в atomic.Int64 при каждом полученном событии")
	fmt.Println(" 2. При обрыве gRPC стрима цикл переподключается с WithRev(lastRevision + 1)")
	fmt.Println(" 3. Экспоненциальный бэкофф предотвращает Thundering Herd при недоступности кластера etcd")
}
'''
validate_go_code(code13, "code13")
exercises.append({
    "num": 13,
    "title": "Надежная обработка разрыва соединения в Watcher",
    "task": "Реализуйте отказоустойчивый наблюдатель ResilientWatcher с сохранением последней подтвержденной ревизии в atomic.Int64. Напишите цикл автоматического переподключения при обрывах gRPC-потока с возобновлением наблюдения через WithRev(lastRevision + 1) и экспоненциальным бэкоффом.",
    "theory": "Сетевые сбои, рестарты нод etcd и плановые миграции подов — обычное дело в production. При обрыве TCP-соединения канал `watchChan` закрывается.\n\nЕсли просто перезапустить `watcher.Watch(ctx, key)` без указания ревизии, клиент начнет слушать только будущие события. Все изменения, произошедшие в кластере за секунды отсутствия связи, будут безвозвратно потеряны для приложения.\n\nАрхитектура непрерывного потока:\n1. При обработке каждого события сохраняем `lastRevision = max(lastRevision, event.Kv.ModRevision)`.\n2. При падении стрима делаем повторное подключение с опцией `clientv3.WithRev(lastRevision + 1)`.\n3. Сервер etcd выдаст клиенту накопившуюся очередь пропущенных событий из истории MVCC, и сервис восстановит консистентность без потерь.",
    "step_by_step": [
        "Создайте структуру ResilientWatcher с потокобезопасным полем lastRevision atomic.Int64.",
        "Реализуйте бесконечный цикл for с проверкой ctx.Done().",
        "Инициализируйте watcher.Watch с передачей WithRev(currentRev + 1).",
        "Обновляйте lastRevision на основе resp.Header.Revision и ev.Kv.ModRevision.",
        "Добавьте экспоненциальный бэкофф при возникновении ошибок стрима."
    ],
    "code_blocks": [{
        "filename": "resilient_etcd_watcher.go",
        "lang": "go",
        "code": code13
    }],
    "under_the_hood": "etcd гарантирует строгий порядок доставки событий (FIFO ordering). Даже если за время сетевого сбоя ключ изменился 5 раз, etcd при передаче `WithRev` передаст все 5 промежуточных событий в точной хронологической последовательности их фиксации в Raft.",
    "pitfalls": [
        "Переподключение с той же ревизией: если передать `WithRev(lastRevision)`, а не `lastRevision + 1`, клиент повторно получит последнее уже обработанное событие (дубликат).",
        "Отсутствие бэкоффа: при полном падении etcd миллионы клиентов начнут спамить запросами на подключение каждую миллисекунду, не давая кластеру подняться."
    ],
    "bigtech_interview": "Что произойдет, если клиент etcd был оффлайн 2 дня? За это время etcd выполнит процедуру Compaction и сотрет старые ревизии. Попытка вызвать `WithRev` вернет ошибку `ErrCompacted`. Как с ней бороться, разберем в следующем упражнении."
})

# Ex 14: Обработка фатальной ошибки ErrCompacted в Watcher
code14 = r'''package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/api/v3/v3rpc/rpctypes"
)

// SelfHealingWatcher умеет самовосстанавливаться при фатальной ошибке ErrCompacted
type SelfHealingWatcher struct {
	cli      *clientv3.Client
	prefix   string
	mu       sync.RWMutex
	lastRev  int64
	cache    map[string]string
}

func NewSelfHealingWatcher(cli *clientv3.Client, prefix string) *SelfHealingWatcher {
	return &SelfHealingWatcher{
		cli:    cli,
		prefix: prefix,
		cache:  make(map[string]string),
	}
}

// fullResync производит полную пересинхронизацию снимка данных из etcd
func (w *SelfHealingWatcher) fullResync(ctx context.Context) (int64, error) {
	resp, err := w.cli.Get(ctx, w.prefix, clientv3.WithPrefix())
	if err != nil {
		return 0, fmt.Errorf("ошибка full resync: %w", err)
	}

	w.mu.Lock()
	newCache := make(map[string]string, len(resp.Kvs))
	for _, kv := range resp.Kvs {
		newCache[string(kv.Key)] = string(kv.Value)
	}
	w.cache = newCache
	w.lastRev = resp.Header.Revision
	w.mu.Unlock()

	fmt.Printf("🔄 [FULL RESYNC] Полная ресинхронизация завершена: %d ключей (Новая ревизия: %d)\n",
		len(resp.Kvs), resp.Header.Revision)
	return resp.Header.Revision, nil
}

// RunWatchLoop обрабатывает ErrCompacted с полным сбросом и ресинхронизацией
func (w *SelfHealingWatcher) RunWatchLoop(ctx context.Context) error {
	rev, err := w.fullResync(ctx)
	if err != nil {
		return err
	}

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}

		watcher := clientv3.NewWatcher(w.cli)
		watchChan := watcher.Watch(ctx, w.prefix, clientv3.WithPrefix(), clientv3.WithRev(rev+1))

		needResync := false
		for resp := range watchChan {
			if resp.Canceled {
				// Проверяем, является ли ошибка фатальным ErrCompacted
				if errors.Is(resp.Err(), rpctypes.ErrCompacted) {
					fmt.Printf("🚨 [COMPACTED ERROR] Запрошенная ревизия %d была сжата кластером etcd!\n", rev+1)
					needResync = true
					break
				}
				fmt.Printf("[WATCH CANCEL] Обычный разрыв стрима: %v\n", resp.Err())
				break
			}

			w.mu.Lock()
			rev = resp.Header.Revision
			w.lastRev = rev
			// Обработка событий PUT/DELETE...
			w.mu.Unlock()
		}

		watcher.Close()

		if needResync {
			// При компактификации история утеряна: делаем полный сброс и начинаем с текущей ревизии
			newRev, err := w.fullResync(ctx)
			if err != nil {
				time.Sleep(1 * time.Second)
				continue
			}
			rev = newRev
		}
	}
}

func main() {
	fmt.Println("Обработка ошибки rpctypes.ErrCompacted в etcd Watcher:")
	fmt.Println(" 1. При длительном оффлайне история старых ревизий удаляется etcd compaction")
	fmt.Println(" 2. errors.Is(resp.Err(), rpctypes.ErrCompacted) перехватывает ошибку сжатия")
	fmt.Println(" 3. Выполняется полный сброс in-memory кэша (Full Resync) с текущего снапшота кластера")
}
'''
validate_go_code(code14, "code14")
exercises.append({
    "num": 14,
    "title": "Обработка фатальной ошибки ErrCompacted в Watcher",
    "task": "Реализуйте самоисцеляющийся наблюдатель SelfHealingWatcher, корректно обрабатывающий ошибку rpctypes.ErrCompacted. При получении ошибки сжатия истории сервис должен перехватить её, выполнить полный ресинхронизационный срез (Full Resync) через Get и возобновить наблюдение со свежей ревизии кластера.",
    "theory": "Файл базы данных etcd не может расти бесконечно: чтобы диск не переполнился, администраторы настраивают периодическую компактификацию (например, удалять ревизии старше 1 часа).\n\nЕсли сервис:\n1. Был остановлен на несколько часов для технического обслуживания,\n2. Или испытывал длительную сетевую изоляцию,\nто при попытке возобновить стрим `Watch(WithRev(lastRev + 1))` etcd вернет фатальную ошибку `rpctypes.ErrCompacted`: запрашиваемая историческая ревизия уже физически стерта с диска!\n\nОбычный ретрай здесь бесполезен — он приведет к бесконечному циклу ошибок. Единственное правильное решение — выполнить двухфазное восстановление:\n1. Сбросить локальное состояние и выполнить полный `Get(prefix, WithPrefix())` с текущей ревизии кластера.\n2. Перезапустить Watcher с полученной свежей ревизии.",
    "step_by_step": [
        "Импортируйте пакет go.etcd.io/etcd/api/v3/v3rpc/rpctypes.",
        "Создайте SelfHealingWatcher с методом fullResync для полной перезагрузки данных.",
        "В цикле обработки watchChan проверьте условие errors.Is(resp.Err(), rpctypes.ErrCompacted).",
        "При обнаружении ошибки компактификации установите флаг needResync и прервите стрим.",
        "Вызовите fullResync() и возобновите наблюдение со свежего снапшота."
    ],
    "code_blocks": [{
        "filename": "etcd_err_compacted_handler.go",
        "lang": "go",
        "code": code14
    }],
    "under_the_hood": "В Kubernetes эта же ситуация возникает, когда `kube-apiserver` компактифицирует etcd. Контроллер в `k8s.io/client-go` ловит `410 Gone (Too old resource version)` и инициирует процедуру List-Watch Re-list.",
    "pitfalls": [
        "Бесконечный цикл ретраев без проверки ошибки: если не проверять `ErrCompacted`, сервис будет долбить etcd миллионы раз в секунду с одной и той же умершей ревизией.",
        "Игнорирование локальных удалений: при `fullResync` необходимо полностью перезаписать локальную карту, иначе ключи, удаленные во время оффлайна, останутся в кэше навсегда (Ghost Keys)."
    ],
    "bigtech_interview": "Почему etcd не хранит историю бесконечно? Хранение всех ревизий при интенсивной записи (10 000 операций/сек) привело бы к исчерпанию диска за считанные часы. Компактификация очищает старые версии ключей из bbolt, поддерживая компактный размер файла базы."
})

# Ex 15: Атомарные транзакции Compare-And-Swap (etcd Txn / STM)
code15 = r'''package main

import (
	"context"
	"fmt"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
)

// AtomicLockService реализует примитив атомарной вставки (Insert-if-not-exists)
type AtomicLockService struct {
	kv clientv3.KV
}

func NewAtomicLockService(cli *clientv3.Client) *AtomicLockService {
	return &AtomicLockService{kv: clientv3.NewKV(cli)}
}

// TryAcquireLock выполняет атомарный CAS через etcd Txn
func (s *AtomicLockService) TryAcquireLock(ctx context.Context, lockKey, holderID string) (bool, error) {
	// Декларативная транзакция etcd v3: If -> Then -> Else
	// Условие: Ключ НЕ существует (его CreateRevision равен 0)
	cmp := clientv3.Compare(clientv3.CreateRevision(lockKey), "=", 0)

	// Ветка Then: Если условие истинно, создаем ключ со значением владельца
	thenOp := clientv3.OpPut(lockKey, holderID)

	// Ветка Else: Если ключ уже существует, считываем текущего владельца
	elseOp := clientv3.OpGet(lockKey)

	// Выполняем транзакцию атомарно на сервере etcd
	txnResp, err := s.kv.Txn(ctx).
		If(cmp).
		Then(thenOp).
		Else(elseOp).
		Commit()

	if err != nil {
		return false, fmt.Errorf("ошибка выполнения транзакции: %w", err)
	}

	if txnResp.Succeeded {
		fmt.Printf("✅ [TXN SUCCESS] Блокировка %s успешно захвачена узлом %s\n", lockKey, holderID)
		return true, nil
	}

	// Извлекаем текущего владельца из ветки Else
	if len(txnResp.Responses) > 0 {
		getResp := txnResp.Responses[0].GetResponseRange()
		if len(getResp.Kvs) > 0 {
			currentHolder := string(getResp.Kvs[0].Value)
			fmt.Printf("❌ [TXN REJECTED] Блокировка %s занята узлом: %s\n", lockKey, currentHolder)
		}
	}

	return false, nil
}

func main() {
	fmt.Println("Атомарные транзакции Compare-And-Swap (etcd Txn):")
	fmt.Println(" 1. If(Compare(CreateRevision(key), '=', 0)) проверяет отсутствие ключа")
	fmt.Println(" 2. Then(OpPut(key, val)) выполняется атомарно при успехе проверки")
	fmt.Println(" 3. Else(OpGet(key)) возвращает текущее состояние при отказе")
	fmt.Println(" 4. txnResp.Succeeded указывает, какая именно ветка была выполнена в Raft")
}
'''
validate_go_code(code15, "code15")
exercises.append({
    "num": 15,
    "title": "Атомарные транзакции Compare-And-Swap (etcd Txn / STM)",
    "task": "Изучите декларативную модель транзакций etcd v3: If(Condition) -> Then(Op) -> Else(Op). Реализуйте метод TryAcquireLock, осуществляющий атомарную проверку отсутствия ключа (CreateRevision == 0) и создание блокировки за один шаг без гонок данных.",
    "theory": "В распределенных системах проверка условия и последующая запись, разделенные по времени (Check-Then-Act), приводят к race condition: между проверкой `Get` и записью `Put` другой узел может успеть перехватить ресурс.\n\netcd v3 предоставляет мощный декларативный механизм мини-транзакций `Txn`:\n```go\nclient.Txn(ctx).\n    If(Conditions...).\n    Then(SuccessOps...).\n    Else(FailureOps...).\n    Commit()\n```\nВсе проверки условий (`If`) и операции (`Then` / `Else`) пакуются в единое сообщение Raft и атомарно применяются к bbolt в рамках одной ревизии кластера. Либо все операции `Then` успешно фиксируются, либо выполняется ветка `Else`. Никакие промежуточные состояния другим клиентам не видны.",
    "step_by_step": [
        "Сформируйте предикат проверки: clientv3.Compare(clientv3.CreateRevision(key), \"=\", 0).",
        "Подготовьте операцию ветки успеха clientv3.OpPut(key, holderID).",
        "Подготовьте операцию ветки отката clientv3.OpGet(key).",
        "Вызовите kv.Txn(ctx).If(cmp).Then(thenOp).Else(elseOp).Commit().",
        "Проверьте флаг txnResp.Succeeded и извлеките данные текущего владельца из ответа ветки Else."
    ],
    "code_blocks": [{
        "filename": "etcd_atomic_txn.go",
        "lang": "go",
        "code": code15
    }],
    "under_the_hood": "Транзакции etcd не требуют блокировок строк на стороне сервера. etcd валидирует предикаты условий в момент применения Raft-лога. Если условие истинно, операции применяются немедленно в памяти и сбрасываются в bbolt в рамках единой ACID-транзакции bbolt.",
    "pitfalls": [
        "Сложные условия: в etcd транзакции не поддерживают циклические запросы. Все операции `OpPut`, `OpGet`, `OpDelete` должны быть детерминированными и определены заранее.",
        "Превышение лимита операций: etcd по умолчанию ограничивает число операций в одной транзакции (обычно до 128 операций)."
    ],
    "bigtech_interview": "Как в etcd v3 реализован CAS (Compare-And-Swap) по значению или ревизии? Мы передаем `Compare(ModRevision(key), \"=\", expectedRev)` или `Compare(Value(key), \"=\", expectedVal)`. Если кто-то успел изменить ключ, транзакция возвращает `Succeeded: false`."
})

# Save Part 1
out_path = '/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch95_p1.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Chapter 95 Part 1 generated successfully: {len(exercises)} exercises.")
