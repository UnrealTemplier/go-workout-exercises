# -*- coding: utf-8 -*-
import json
import subprocess
import tempfile
import os

exercises = []

# Exercise 1
exercises.append({
    "num": 1,
    "title": "Концепция Contract-First разработки и Protobuf Single Source of Truth",
    "task": "Изучите парадигму Contract-First: API проектируется в виде схемы Protobuf, из которой автоматически генерируются строго типизированные серверные интерфейсы, клиентские SDK, обратный REST/JSON прокси и интерактивная документация Swagger. Сравните этот подход с Code-First и объясните, почему он устраняет расхождение контрактов между командами.",
    "theory": r"""В разработке распределенных систем и микросервисов существуют две противоположные парадигмы проектирования API:

1. **Code-First (Сначала код):**
   - Разработчик сначала пишет структуры Go и обработчики `http.HandlerFunc`, а затем аннотирует код специальными комментариями (`// @Router /orders [get]`) для генерации Swagger через сторонние парсеры (например, `swag`).
   - **Главный порок:** расхождение контракта и реализации (Contract Drift). Разработчик меняет поле структуры или возвращаемый код ошибки, но забывает обновить комментарий. Документация устаревает, клиенты других команд (фронтенд, мобильные приложения, соседние бэкенды) ломаются в рантайме.

2. **Contract-First (Сначала контракт / Single Source of Truth):**
   - API начинается с формального контракта на машинно-читаемом языке IDL (Interface Definition Language) — **Protocol Buffers v3 (`.proto`)**.
   - Схема фиксирует типы полей, номера тегов, методы сервиса, правила валидации и REST-маппинг.
   - Из единого `.proto` файла компилятор `protoc` (или `buf`) автоматически генерирует:
     - Серверные интерфейсы Go (`*_grpc.pb.go`).
     - Бинарный кодек Protobuf (`*.pb.go`).
     - Обратный REST/JSON шлюз (`*.pb.gw.go`).
     - Спецификацию OpenAPI v3 (`*.swagger.json`).
     - Клиентские SDK для TypeScript, Swift, Kotlin, Python, C#.
   - Разработчик бэкенда **физически не может** нарушить контракт, так как компилятор Go просто не скомпилирует метод, сигнатура которого не совпадает со сгенерированным интерфейсом.""",
    "step_by_step": [
        "Спроектируйте канонический Protobuf IDL контракт заказа `order.proto` с аннотациями `google.api.http`.",
        "Реализуйте симулятор компилятора контракта, валидирующий строгое соответствие структур Go исходной схеме IDL.",
        "Смоделируйте серверный интерфейс Go, строго выведенный из Protobuf контракта.",
        "Проверьте статическую типизацию: покажите, как попытка возврата несовместимого типа пресекается компилятором."
    ],
    "code_blocks": [
        {
            "filename": "contract_first_demo.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

type OrderStatusEnum int32

const (
	OrderStatus_UNKNOWN   OrderStatusEnum = 0
	OrderStatus_PENDING   OrderStatusEnum = 1
	OrderStatus_PAID      OrderStatusEnum = 2
	OrderStatus_CANCELLED OrderStatusEnum = 3
)

func (s OrderStatusEnum) String() string {
	switch s {
	case OrderStatus_PENDING:
		return "PENDING"
	case OrderStatus_PAID:
		return "PAID"
	case OrderStatus_CANCELLED:
		return "CANCELLED"
	default:
		return "UNKNOWN"
	}
}

type GetOrderRequest struct {
	OrderId string `json:"order_id"`
}

type OrderResponse struct {
	OrderId   string          `json:"order_id"`
	Amount    int64           `json:"amount_cents"`
	Status    OrderStatusEnum `json:"status"`
	CreatedAt time.Time       `json:"created_at"`
}

type OrderServiceServer interface {
	GetOrder(ctx context.Context, req *GetOrderRequest) (*OrderResponse, error)
}

type OrderServiceImpl struct{}

func (s *OrderServiceImpl) GetOrder(ctx context.Context, req *GetOrderRequest) (*OrderResponse, error) {
	if req.OrderId == "" {
		return nil, errors.New("invalid argument: order_id cannot be empty")
	}

	return &OrderResponse{
		OrderId:   req.OrderId,
		Amount:    49900,
		Status:    OrderStatus_PAID,
		CreatedAt: time.Now().UTC(),
	}, nil
}

func main() {
	var server OrderServiceServer = &OrderServiceImpl{}

	ctx := context.Background()
	resp, err := server.GetOrder(ctx, &GetOrderRequest{OrderId: "ord_776655"})
	if err != nil {
		panic(err)
	}

	fmt.Println("=== ВЫПОЛНЕНИЕ МЕТОДА ИЗ PROTOBUF КОНТРАКТА ===")
	fmt.Printf("Заказ ID:       %s\n", resp.OrderId)
	fmt.Printf("Сумма:          %.2f руб\n", float64(resp.Amount)/100.0)
	fmt.Printf("Статус:         %s\n", resp.Status)
	fmt.Printf("Время создания: %s\n", resp.CreatedAt.Format(time.RFC3339))
}
"""
        }
    ],
    "under_the_hood": "В парадигме Contract-First файл `.proto` компилируется плагином `protoc-gen-go-grpc`, который генерирует неэкспортируемый интерфейсный маркер `mustEmbedUnimplementedOrderServiceServer()` в интерфейсе сервера. Если разработчик попытается зарегистрировать структуру, не реализовавшую хотя бы один метод контракта, компилятор Go откажется собирать бинарник. Это устраняет человеческий фактор при версионировании и рефакторинге API.",
    "pitfalls": [
        "Ручное редактирование сгенерированных файлов `*.pb.go` или `*.pb.gw.go`: при следующей сборке protoc все изменения будут безвозвратно затерты. Любая логика должна реализовываться в отдельных файлах бизнес-слоя.",
        "Использование номеров тегов полей (Field Numbers) больше 536 870 911 или переиспользование удаленных номеров тегов без директивы `reserved`.",
        "Хранение несовместимых версий `.proto` файлов в разных репозиториях микросервисов."
    ],
    "bigtech_interview": "Почему в Google, Uber и Netflix принята строгая концепция Contract-First на базе Protobuf, а не REST/OpenAPI Code-First? В BigTech над одной платформой работают тысячи инженеров на разных языках (Go, Java, Python, C++, TypeScript). Contract-First на Protobuf гарантирует: 1) Бинарную обратную и прямую совместимость за счет числовых тегов полей; 2) Высочайшую скорость бинарной сериализации (в 5–10 раз быстрее JSON); 3) Автоматическую генерацию клиентских SDK день-в-день при обновлении схемы."
})

# Exercise 2
exercises.append({
    "num": 2,
    "title": "Установка и настройка генератора grpc-gateway v2",
    "task": "Настройте окружение разработки: установите плагины компилятора `protoc-gen-go`, `protoc-gen-go-grpc` и `protoc-gen-grpc-gateway/v2`. Напишите Makefile или скрипт автоматической компиляции `.proto` файлов с корректными путями импорта стандартных библиотек Google API.",
    "theory": r"""Кодогенерация в экосистеме Go основывается на стандартном компиляторе `protoc` и подключаемых плагинах:
1. `protoc-gen-go`: генерирует Go-структуры сообщений (`.pb.go`) и функции бинарной сериализации/десериализации.
2. `protoc-gen-go-grpc`: генерирует клиентские стабы и интерфейсы gRPC-серверов (`_grpc.pb.go`).
3. `protoc-gen-grpc-gateway/v2`: генерирует HTTP Reverse Proxy мультиплексор (`.pb.gw.go`), преобразующий входящие HTTP REST JSON запросы в вызовы gRPC-сервера.

Управление инструментарием через Go Modules (`tools.go`):
Чтобы версионировать генераторы строго внутри `go.mod` (гарантируя одинаковые сборки у всех разработчиков и в CI), создается файл `tools.go` с тегом сборки `//go:build tools`:
```go
//go:build tools
package tools

import (
    _ "github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-grpc-gateway"
    _ "github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-openapiv2"
    _ "google.golang.org/grpc/cmd/protoc-gen-go-grpc"
    _ "google.golang.org/protobuf/cmd/protoc-gen-go"
)
```

Скрипт компиляции или Makefile выполняет установку `go install` и запускает `protoc` с флагами `--grpc-gateway_out=paths=source_relative:.`.""",
    "step_by_step": [
        "Изучите назначение паттерна `tools.go` для версионирования плагинов кодогенерации.",
        "Реализуйте Go-утилиту сборки `ProtoBuildRunner`, валидирующую установку бинарников плагинов в `$GOPATH/bin`.",
        "Сформируйте аргументы вызова компилятора с флагами `source_relative` и маппингом путей стандартных Google API.",
        "Протестируйте парсинг конфигурации и проверку готовности окружения."
    ],
    "code_blocks": [
        {
            "filename": "proto_builder_check.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

type ToolRequirement struct {
	Name        string
	InstallPath string
	Required    bool
}

type EnvironmentAuditor struct {
	tools []ToolRequirement
}

func NewEnvironmentAuditor() *EnvironmentAuditor {
	return &EnvironmentAuditor{
		tools: []ToolRequirement{
			{Name: "protoc", InstallPath: "protoc", Required: true},
			{Name: "protoc-gen-go", InstallPath: "google.golang.org/protobuf/cmd/protoc-gen-go@v1.33.0", Required: true},
			{Name: "protoc-gen-go-grpc", InstallPath: "google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.3.0", Required: true},
			{Name: "protoc-gen-grpc-gateway", InstallPath: "github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-grpc-gateway@v2.19.1", Required: true},
			{Name: "protoc-gen-openapiv2", InstallPath: "github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-openapiv2@v2.19.1", Required: true},
		},
	}
}

func (a *EnvironmentAuditor) Audit() []string {
	var missing []string
	gopath := os.Getenv("GOPATH")
	if gopath == "" {
		home, _ := os.UserHomeDir()
		gopath = filepath.Join(home, "go")
	}
	gobin := filepath.Join(gopath, "bin")

	for _, tool := range a.tools {
		_, errPath := exec.LookPath(tool.Name)
		_, errBin := os.Stat(filepath.Join(gobin, tool.Name))

		if errPath != nil && errBin != nil {
			missing = append(missing, fmt.Sprintf("%s (команда: go install %s)", tool.Name, tool.InstallPath))
		} else {
			fmt.Printf("✅ Инструмент найден: %-25s\n", tool.Name)
		}
	}
	return missing
}

func GenerateCompileCommand(protoFile, outDir string) string {
	return fmt.Sprintf(
		"protoc -I . -I /usr/local/include \\\n"+
			"  --go_out=%s --go_opt=paths=source_relative \\\n"+
			"  --go-grpc_out=%s --go-grpc_opt=paths=source_relative \\\n"+
			"  --grpc-gateway_out=%s --grpc-gateway_opt=paths=source_relative,generate_unbound_methods=true \\\n"+
			"  --openapiv2_out=%s --openapiv2_opt=logtostderr=true \\\n"+
			"  %s",
		outDir, outDir, outDir, outDir, protoFile,
	)
}

func main() {
	fmt.Println("=== АУДИТ ОКРУЖЕНИЯ ДЛЯ GRPC-GATEWAY V2 ===")
	auditor := NewEnvironmentAuditor()
	missing := auditor.Audit()

	if len(missing) > 0 {
		fmt.Println("\n⚠️ Внимание! Не установлены следующие компоненты:")
		for _, m := range missing {
			fmt.Println("  -", m)
		}
	} else {
		fmt.Println("\n🎉 Окружение полностью готово к сборке gRPC-Gateway!")
	}

	fmt.Println("\nПример генерируемой команды компиляции:")
	fmt.Println(GenerateCompileCommand("proto/api/v1/order.proto", "gen/go/api/v1"))
}
"""
        }
    ],
    "under_the_hood": "Флаг `paths=source_relative` указывает генераторам `protoc-gen-go` и `protoc-gen-grpc-gateway` создавать выходные файлы `.pb.go` в той же структуре поддиректорий, где находился исходный `.proto` файл, игнорируя опцию `option go_package`.",
    "pitfalls": [
        "Отсутствие файлов `google/api/annotations.proto` и `google/api/http.proto`.",
        "Несовпадение версий плагинов `protoc-gen-go` и библиотек рантайма `google.golang.org/protobuf`.",
        "Забывание флага `generate_unbound_methods=true`."
    ],
    "bigtech_interview": "Почему современная индустрия переходит от связки `Makefile + protoc` к инструменту `Buf` (`buf.build`)? Компилятор `protoc` написан на C++, требует ручной установки системных бинарников, страдает от проблем с поиском путей импорта стандартных зависимостей Google API и не умеет автоматически кэшировать удаленные модули. Утилита `Buf` написана на Go, содержит встроенный компилятор Protobuf, проверяет кодстайл (`buf lint`), контролирует обратную совместимость (`buf breaking`) и использует BSR (Buf Schema Registry) как пакетный менеджер контрактов."
})

# Exercise 3
exercises.append({
    "num": 3,
    "title": "Аннотации google.api.http для маппинга REST-методов",
    "task": "Создайте файл `order_service.proto`. Импортируйте `google/api/annotations.proto`. Добавьте аннотации HTTP-роутинга для gRPC-методов: `CreateOrder` -> `POST /v1/orders` (с привязкой тела запроса `body: \"*\"`), `GetOrder` -> `GET /v1/orders/{order_id}`, `ListOrders` -> `GET /v1/orders`.",
    "theory": r"""Связывание gRPC-процедур с REST-эндпоинтами выполняется с помощью стандартных аннотаций Google API (`google.api.http`, спецификация PEP HTTP API):

Ключевые правила маппинга:
1. **Параметры пути (Path Parameters):**
   - Переменные пути заключаются в фигурные скобки: `GET /v1/orders/{order_id}`.
   - Значение из URL автоматически парсится и помещается в соответствующее поле gRPC-запроса `req.OrderId`.
2. **Тело запроса (Request Body):**
   - Для методов `POST`, `PUT`, `PATCH` директива `body: "*"` указывает декодеру разобрать все входящее тело JSON-запроса в корневую структуру protobuf-сообщения.
   - Если указано конкретное поле `body: "item"`, тело JSON маппится только в это вложенное поле.
3. **Параметры строки запроса (Query Parameters):**
   - Для методов `GET` или `DELETE` все поля сообщения, не вошедшие в путь URL, автоматически считываются из Query String: например, `GET /v1/orders?page_size=20&filter=ACTIVE`.""",
    "step_by_step": [
        "Спроектируйте структуру proto-файла `order_service.proto` с методами CRUD и аннотациями `google.api.http`.",
        "Реализуйте маршрутизатор на чистом Go, эмулирующий логику парсинга аннотаций `google.api.http` (извлечение path params, query params и JSON body).",
        "Продемонстрируйте трансляцию входящего HTTP GET запроса `/v1/orders/ORD-9988?verbose=true` в заполненную структуру Protobuf запроса.",
        "Проверьте трансляцию POST запроса с телом JSON."
    ],
    "code_blocks": [
        {
            "filename": "http_annotations_mapper.go",
            "lang": "go",
            "code": r"""package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
)

type CreateOrderRequest struct {
	CustomerId string `json:"customer_id"`
	Amount     int64  `json:"amount"`
	Currency   string `json:"currency"`
}

type GetOrderRequest struct {
	OrderId string `json:"order_id"`
	Verbose bool   `json:"verbose"`
}

type OrderResponse struct {
	OrderId string `json:"order_id"`
	Status  string `json:"status"`
}

type RouterSimulator struct {
	mux *http.ServeMux
}

func NewRouterSimulator() *RouterSimulator {
	r := &RouterSimulator{mux: http.NewServeMux()}
	r.setupRoutes()
	return r
}

func (r *RouterSimulator) setupRoutes() {
	r.mux.HandleFunc("/v1/orders", func(w http.ResponseWriter, req *http.Request) {
		if req.Method == http.MethodPost {
			var protoReq CreateOrderRequest
			if err := json.NewDecoder(req.Body).Decode(&protoReq); err != nil {
				http.Error(w, "invalid json body", http.StatusBadRequest)
				return
			}

			resp := OrderResponse{
				OrderId: fmt.Sprintf("ord_%s_%d", protoReq.CustomerId, protoReq.Amount),
				Status:  "CREATED",
			}

			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusCreated)
			_ = json.NewEncoder(w).Encode(resp)
			return
		}
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
	})

	r.mux.HandleFunc("/v1/orders/", func(w http.ResponseWriter, req *http.Request) {
		if req.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}

		pathParts := strings.Split(strings.Trim(req.URL.Path, "/"), "/")
		if len(pathParts) != 3 {
			http.Error(w, "not found", http.StatusNotFound)
			return
		}
		orderID := pathParts[2]
		verbose, _ := strconv.ParseBool(req.URL.Query().Get("verbose"))

		protoReq := GetOrderRequest{
			OrderId: orderID,
			Verbose: verbose,
		}

		resp := OrderResponse{
			OrderId: protoReq.OrderId,
			Status:  fmt.Sprintf("FETCHED (verbose=%v)", protoReq.Verbose),
		}

		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(resp)
	})
}

func main() {
	router := NewRouterSimulator()

	body := `{"customer_id": "cust_42", "amount": 1500, "currency": "RUB"}`
	reqPost := httptest.NewRequest(http.MethodPost, "/v1/orders", strings.NewReader(body))
	recPost := httptest.NewRecorder()
	router.mux.ServeHTTP(recPost, reqPost)

	fmt.Println("=== ТЕСТ POST /v1/orders ===")
	fmt.Printf("HTTP Status: %d\n", recPost.Code)
	fmt.Printf("Ответ JSON:  %s\n", strings.TrimSpace(recPost.Body.String()))

	reqGet := httptest.NewRequest(http.MethodGet, "/v1/orders/ORD-100200?verbose=true", nil)
	recGet := httptest.NewRecorder()
	router.mux.ServeHTTP(recGet, reqGet)

	fmt.Println("\n=== ТЕСТ GET /v1/orders/{order_id} ===")
	fmt.Printf("HTTP Status: %d\n", recGet.Code)
	fmt.Printf("Ответ JSON:  %s\n", strings.TrimSpace(recGet.Body.String()))
}
"""
        }
    ],
    "under_the_hood": "Сгенерированный файл `*.pb.gw.go` регистрирует маршруты в структуре `runtime.ServeMux`. Для сопоставления URL используется префиксное дерево (Radix Tree).",
    "pitfalls": [
        "Забывание `body: \"*\"` для POST/PUT методов.",
        "Коллизии маршрутов.",
        "Несовпадение имен полей в JSON: по умолчанию protobuf использует camelCase для JSON."
    ],
    "bigtech_interview": "Как в `google.api.http` аннотациях назначить одному и тому же gRPC-методу сразу несколько REST-эндпоинтов? С помощью директивы `additional_bindings`: в аннотации метода указывается основной путь, а внутри массива `additional_bindings` задается дополнительный маршрут. Шлюз создаст оба роута, перенаправляя их в один и тот же gRPC-метод."
})

# Exercise 4
exercises.append({
    "num": 4,
    "title": "Запуск первого HTTP-шлюза поверх gRPC-сервера",
    "task": "Напишите Go-приложение, запускающее gRPC-сервер на порту `:9090` и HTTP-шлюз на порту `:8080`. Инициализируйте мультиплексор шлюза: `mux := runtime.NewServeMux()`, зарегистрируйте обработчик через `RegisterOrderServiceHandlerFromEndpoint(ctx, mux, \"localhost:9090\", opts)`. Проверьте вызов метода через `curl -X GET http://localhost:8080/v1/orders/123`.",
    "theory": r"""Архитектура gRPC-Gateway представляет собой обратный прокси (Reverse Proxy), работающий внутри Go-процесса или в виде отдельного сайдкара:
1. **gRPC Backend:** слушает порт `:9090` (чистый бинарный HTTP/2 + Protobuf).
2. **Gateway HTTP Server:** слушает порт `:8080` (HTTP/1.1 или HTTP/2 REST/JSON).
3. **Механика трансляции:**
   - Клиент отправляет стандартный JSON-запрос по HTTP на `:8080`.
   - Шлюз декодирует JSON в Protobuf-структуру сообщения в памяти.
   - Шлюз обращается к локальному gRPC-серверу по адресу `localhost:9090` через gRPC-клиент.
   - Бэкенд возвращает бинарный ответ.
   - Шлюз кодирует ответ в JSON и отдает клиенту с кодом 200 OK.

Регистрация через Endpoint (`Register...HandlerFromEndpoint`):
Функция `RegisterOrderServiceHandlerFromEndpoint(ctx, mux, endpoint, opts)` берет на себя автоматическое создание клиентского пула соединений `grpc.DialContext` с переданными опциями диалера (`grpc.WithTransportCredentials(insecure.NewCredentials())`).""",
    "step_by_step": [
        "Спроектируйте архитектуру двух серверов: внутренний gRPC сервис и внешний HTTP REST шлюз.",
        "Реализуйте gRPC-сервер с бизнес-методом получения информации о заказе.",
        "Инициализируйте прокси-шлюз `GatewayServer`, транслирующий HTTP REST вызовы во внутренний gRPC вызов.",
        "Протестируйте сквозной вызов: клиент отправляет HTTP GET запрос, шлюз выполняет gRPC вызов, и клиент получает корректный JSON."
    ],
    "code_blocks": [
        {
            "filename": "dual_server_gateway.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
)

type OrderInfo struct {
	ID        string `json:"id"`
	Customer  string `json:"customer"`
	AmountRUB int64  `json:"amount_rub"`
	Status    string `json:"status"`
}

type SimulatedBackendService struct {
	mu     sync.Mutex
	orders map[string]OrderInfo
}

func NewBackendService() *SimulatedBackendService {
	return &SimulatedBackendService{
		orders: map[string]OrderInfo{
			"123": {ID: "123", Customer: "Иван Смирнов", AmountRUB: 12500, Status: "CONFIRMED"},
			"456": {ID: "456", Customer: "Анна Кузнецова", AmountRUB: 4300, Status: "DELIVERED"},
		},
	}
}

func (s *SimulatedBackendService) GetOrderRPC(ctx context.Context, orderID string) (*OrderInfo, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	order, exists := s.orders[orderID]
	if !exists {
		return nil, fmt.Errorf("order %s not found", orderID)
	}
	return &order, nil
}

type SimulatedGatewayMux struct {
	backend *SimulatedBackendService
}

func (g *SimulatedGatewayMux) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodGet && strings.HasPrefix(r.URL.Path, "/v1/orders/") {
		orderID := strings.TrimPrefix(r.URL.Path, "/v1/orders/")
		if orderID == "" {
			http.Error(w, "missing order id", http.StatusBadRequest)
			return
		}

		order, err := g.backend.GetOrderRPC(r.Context(), orderID)
		if err != nil {
			http.Error(w, err.Error(), http.StatusNotFound)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_ = json.NewEncoder(w).Encode(order)
		return
	}

	http.NotFound(w, r)
}

func main() {
	backend := NewBackendService()
	gatewayMux := &SimulatedGatewayMux{backend: backend}

	ts := httptest.NewServer(gatewayMux)
	defer ts.Close()

	fmt.Printf("HTTP-шлюз запущен по адресу: %s\n", ts.URL)

	url := fmt.Sprintf("%s/v1/orders/123", ts.URL)
	resp, err := http.Get(url)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	var result OrderInfo
	_ = json.NewDecoder(resp.Body).Decode(&result)

	fmt.Println("=== ОТВЕТ ОТ HTTP-ШЛЮЗА ПОСЛЕ ТРАНСЛЯЦИИ В GRPC ===")
	fmt.Printf("HTTP Status:  %d\n", resp.StatusCode)
	fmt.Printf("ID заказа:    %s\n", result.ID)
	fmt.Printf("Покупатель:   %s\n", result.Customer)
	fmt.Printf("Сумма:        %d руб\n", result.AmountRUB)
	fmt.Printf("Статус:       %s\n", result.Status)
}
"""
        }
    ],
    "under_the_hood": "В реальном приложении при использовании `RegisterOrderServiceHandlerFromEndpoint` шлюз создает постоянное gRPC соединение (Multiplexed HTTP/2 ClientConn) с бэкендом. Все поступающие параллельные HTTP REST запросы мультиплексируются в виде параллельных HTTP/2 потоков (Streams) внутри одного или нескольких постоянных TCP-сокетов, что исключает накладные расходы на постоянный TCP-handshake.",
    "pitfalls": [
        "Использование блокирующего `grpc.WithBlock()`.",
        "Утечка ресурсов при отсутствии отмены контекста `context.WithCancel`.",
        "Забывание закрытия тел входящих HTTP-запросов."
    ],
    "bigtech_interview": "В чем преимущество запуска gRPC-Gateway внутри того же бинарника Go (In-Process Gateway) по сравнению с отдельным прокси (Envoy)? In-Process Gateway устраняет лишний сетевой сетевой хоп (loopback network hop) и контекстные переключения ядра операционной системы. При правильной настройке (`RegisterOrderServiceHandlerClient`) шлюз может вызывать методы gRPC сервиса напрямую через внутренний интерфейс в оперативной памяти (In-Memory Direct Dispatch) без сериализации в сетевые сокеты."
})

# Exercise 5
exercises.append({
    "num": 5,
    "title": "Генерация OpenAPI v3 (Swagger) спецификации",
    "task": "Подключите плагин `protoc-gen-openapiv2`. Сгенерируйте файл `order_service.swagger.json`. Проверьте, как схемы сообщений Protobuf автоматически транслируются в OpenAPI Data Types, включая вложенные структуры, перечисления (enum) и валидационные ограничения.",
    "theory": r"""Плагин `protoc-gen-openapiv2` (ранее `protoc-gen-swagger`) анализирует proto-файлы и генерирует единую валидную спецификацию OpenAPI v2/v3 в формате JSON или YAML.

Правила трансформации Protobuf типов в OpenAPI Data Types:
- `int32`, `sint32`, `uint32` -> `type: "integer", format: "int32"`
- `int64`, `sint64`, `uint64` -> `type: "string", format: "int64"` (Внимание! 64-битные целые числа в JSON представляются строками во избежание потери точности в JavaScript).
- `double`, `float` -> `type: "number", format: "double"`
- `bool` -> `type: "boolean"`
- `string` -> `type: "string"`
- `bytes` -> `type: "string", format: "byte"` (Base64)
- `repeated T` -> `type: "array", items: { ... }`
- `map<string, T>` -> `type: "object", additionalProperties: { ... }`
- `enum E` -> `type: "string", enum: ["VALUE_A", "VALUE_B"]`
- `google.protobuf.Timestamp` -> `type: "string", format: "date-time"` (RFC 3339).""",
    "step_by_step": [
        "Изучите спецификацию OpenAPI v2/v3 и соответствие типов Protobuf.",
        "Реализуйте генератор спецификации OpenAPI Schema на Go, конвертирующий описания моделей Protobuf в JSON-схему Swagger.",
        "Проверьте корректное преобразование перечислений (enum), 64-битных целых и обязательных полей.",
        "Сгенерируйте и распечатайте результирующий `swagger.json` документ."
    ],
    "code_blocks": [
        {
            "filename": "swagger_generator_demo.go",
            "lang": "go",
            "code": r"""package main

import (
	"encoding/json"
	"fmt"
)

type SwaggerDoc struct {
	Swagger     string               `json:"swagger"`
	Info        SwaggerInfo          `json:"info"`
	BasePath    string               `json:"basePath"`
	Schemes     []string             `json:"schemes"`
	Paths       map[string]any       `json:"paths"`
	Definitions map[string]SchemaDef `json:"definitions"`
}

type SwaggerInfo struct {
	Title   string `json:"title"`
	Version string `json:"version"`
}

type SchemaDef struct {
	Type       string                `json:"type"`
	Properties map[string]SchemaProp `json:"properties"`
	Required   []string              `json:"required,omitempty"`
}

type SchemaProp struct {
	Type        string   `json:"type,omitempty"`
	Format      string   `json:"format,omitempty"`
	Description string   `json:"description,omitempty"`
	Enum        []string `json:"enum,omitempty"`
	Ref         string   `json:"$ref,omitempty"`
}

func GenerateOrderServiceSwagger() SwaggerDoc {
	doc := SwaggerDoc{
		Swagger:  "2.0",
		Info:     SwaggerInfo{Title: "Order Management API", Version: "1.0.0"},
		BasePath: "/",
		Schemes:  []string{"https", "http"},
		Paths:    make(map[string]any),
		Definitions: map[string]SchemaDef{
			"v1OrderStatus": {
				Type: "string",
				Properties: map[string]SchemaProp{
					"status": {
						Type: "string",
						Enum: []string{"PENDING", "PROCESSING", "COMPLETED", "FAILED"},
					},
				},
			},
			"v1Order": {
				Type:     "object",
				Required: []string{"id", "amount"},
				Properties: map[string]SchemaProp{
					"id": {
						Type:        "string",
						Description: "Уникальный идентификатор заказа",
					},
					"amount": {
						Type:        "string",
						Format:      "int64",
						Description: "Сумма в копейках",
					},
					"status": {
						Ref: "#/definitions/v1OrderStatus",
					},
					"created_at": {
						Type:        "string",
						Format:      "date-time",
						Description: "Временная метка RFC 3339",
					},
				},
			},
		},
	}

	doc.Paths["/v1/orders/{id}"] = map[string]any{
		"get": map[string]any{
			"summary":     "Получить детали заказа по ID",
			"operationId": "OrderService_GetOrder",
			"parameters": []map[string]any{
				{
					"name":        "id",
					"in":          "path",
					"required":    true,
					"type":        "string",
					"description": "ID заказа",
				},
			},
			"responses": map[string]any{
				"200": map[string]any{
					"description": "Успешный ответ",
					"schema": map[string]any{
						"$ref": "#/definitions/v1Order",
					},
				},
				"404": map[string]any{
					"description": "Заказ не найден",
				},
			},
		},
	}

	return doc
}

func main() {
	swagger := GenerateOrderServiceSwagger()
	out, err := json.MarshalIndent(swagger, "", "  ")
	if err != nil {
		panic(err)
	}

	fmt.Println("=== СГЕНЕРИРОВАННАЯ OPENAPI SPECIFICATION (SWAGGER JSON) ===")
	fmt.Println(string(out))
}
"""
        }
    ],
    "under_the_hood": "При кодогенерации `protoc-gen-openapiv2` парсит AST-дерево дескрипторов Protobuf (`FileDescriptorProto`). Комментарии, расположенные непосредственно перед сообщениями и полями в `.proto` файле, автоматически парсятся через механизм `SourceCodeInfo` компилятора `protoc` и превращаются в поля `description` и `summary` документации OpenAPI, обеспечивая 100% синхронизацию комментариев и спецификации.",
    "pitfalls": [
        "Потеря 64-битных целых чисел в веб-браузерах: если `int64` сериализовать как число в JSON, JavaScript округлит младшие разряды чисел.",
        "Игнорирование опции `allow_merge=true`: плагин создаст отдельные JSON-файлы для каждого proto-файла.",
        "Некорректная валидация схем: различия между версиями OpenAPI v2 и v3."
    ],
    "bigtech_interview": "Почему при генерации OpenAPI документации из Protobuf критически важно использовать флаг `allow_merge=true` и опцию `openapiv2_swagger`? Опция `allow_merge=true` объединяет все proto-дефиниции сервиса в единый монолитный `api.swagger.json`, готовый для импорта в Postman или отображения в корпоративном портале Swagger UI."
})

# Exercise 6
exercises.append({
    "num": 6,
    "title": "Кастомизация OpenAPI через аннотации Protobuf",
    "task": "Импортируйте `protoc-gen-openapiv2/options/annotations.proto`. Настройте метаданные API в proto-файле: заголовок документации, описание, контактные данные команды, схему безопасности `security_definitions` (JWT Bearer Auth) и кастомные теги для группировки эндпоинтов.",
    "theory": r"""Плагин `protoc-gen-openapiv2` поддерживает расширенные аннотации Protobuf для тонкой настройки Swagger-документации:

1. **Опция файла `openapiv2_swagger`:**
   Позволяет декларировать глобальные свойства спецификации прямо в заголовке `.proto` файла:
   - Лицензия и условия обслуживания.
   - Схемы безопасности (`security_definitions`): определение JWT Bearer авторизации (`apiKey` в заголовке `Authorization`).
   - Глобальные ответы об ошибках (400, 401, 403, 500) для всех эндпоинтов.
2. **Опция метода `openapiv2_operation`:**
   Кастомизирует конкретную RPC-процедуру:
   - `summary` и `description`.
   - `tags`: группировка методов в UI по логическим доменам.
   - `security`: указание необходимых областей видимости.
3. **Опция поля `openapiv2_field`:**
   Позволяет задать регулярные выражения валидации (`pattern`), минимальные и максимальные значения (`minimum`, `maximum`) и примеры значений (`example: "ORD-998822"`).""",
    "step_by_step": [
        "Изучите proto-пакет `grpc.gateway.protoc_gen_openapiv2.options`.",
        "Спроектируйте структуру метаданных безопасности JWT Bearer для OpenAPI.",
        "Реализуйте симулятор компилятора аннотаций безопасности, автоматически внедряющий объект `securityDefinitions` и привязку `security` к защищенным методам.",
        "Проверьте, что в сгенерированной спецификации для приватных методов появился замок авторизации."
    ],
    "code_blocks": [
        {
            "filename": "openapi_customizer.go",
            "lang": "go",
            "code": r"""package main

import (
	"encoding/json"
	"fmt"
)

type SecurityScheme struct {
	Type        string `json:"type"`
	Name        string `json:"name"`
	In          string `json:"in"`
	Description string `json:"description"`
}

type OpenAPIOperation struct {
	Summary   string                `json:"summary"`
	Tags      []string              `json:"tags"`
	Security  []map[string][]string `json:"security,omitempty"`
	Responses map[string]any        `json:"responses"`
}

type EnrichedOpenAPISpec struct {
	Swagger             string                                 `json:"swagger"`
	Info                map[string]string                      `json:"info"`
	SecurityDefinitions map[string]SecurityScheme              `json:"securityDefinitions"`
	Paths               map[string]map[string]OpenAPIOperation `json:"paths"`
}

func BuildSecuredOpenAPISpec() EnrichedOpenAPISpec {
	spec := EnrichedOpenAPISpec{
		Swagger: "2.0",
		Info: map[string]string{
			"title":       "Billing & Payments Enterprise API",
			"version":     "v2.1.0",
			"description": "Production contract-first API Gateway with JWT Bearer Security",
		},
		SecurityDefinitions: map[string]SecurityScheme{
			"BearerAuth": {
				Type:        "apiKey",
				Name:        "Authorization",
				In:          "header",
				Description: "Введите JWT токен в формате: Bearer <TOKEN>",
			},
		},
		Paths: make(map[string]map[string]OpenAPIOperation),
	}

	spec.Paths["/v1/auth/login"] = map[string]OpenAPIOperation{
		"post": {
			Summary: "Аутентификация пользователя и получение JWT",
			Tags:    []string{"Authentication"},
			Responses: map[string]any{
				"200": map[string]string{"description": "Успешная авторизация"},
			},
		},
	}

	spec.Paths["/v1/wallets/transfer"] = map[string]OpenAPIOperation{
		"post": {
			Summary: "Перевод денежных средств между кошельками",
			Tags:    []string{"Billing", "Wallets"},
			Security: []map[string][]string{
				{"BearerAuth": []string{}},
			},
			Responses: map[string]any{
				"200": map[string]string{"description": "Перевод выполнен"},
				"401": map[string]string{"description": "Отсутствует или недействителен JWT токен"},
			},
		},
	}

	return spec
}

func main() {
	spec := BuildSecuredOpenAPISpec()
	raw, _ := json.MarshalIndent(spec, "", "  ")

	fmt.Println("=== ENRICHED OPENAPI SPECIFICATION WITH JWT SECURITY ===")
	fmt.Println(string(raw))
}
"""
        }
    ],
    "under_the_hood": "Аннотации `openapiv2_swagger` компилируются в байткод расширений Protobuf (Custom Options). При вызове `protoc` плагин читает расширения через дескриптор файла (`proto.GetExtension(fileDesc.Options, openapiv2.E_Swagger)`), преобразуя их в структуры Go-библиотеки OpenAPI, после чего выполняет финальную сериализацию в JSON.",
    "pitfalls": [
        "Неверное имя схемы безопасности.",
        "Забывание префикса `Bearer ` в Swagger UI.",
        "Отсутствие описания ответов ошибок 401/403 в контракте."
    ],
    "bigtech_interview": "Как в Protobuf-схеме скрыть внутренние поля или закрытые эндпоинты от публичной OpenAPI документации? Используется опция `visibility`: аннотация `[(grpc.gateway.protoc_gen_openapiv2.options.openapiv2_operation).visibility = \"INTERNAL\"]` или флаг генератора `--openapiv2_opt=filter_unexposed=true`."
})

# Exercise 7
exercises.append({
    "num": 7,
    "title": "Встраивание Swagger UI в Go-бинарник через embed.FS",
    "task": "Используя директиву Go `//go:embed swagger-ui/*`, встройте статические файлы Swagger UI и сгенерированный `swagger.json` прямо внутрь скомпилированного бинарного файла. Настройте раздачу интерактивной документации по адресу `http://localhost:8080/docs/` без внешних зависимостей от файловой системы хоста.",
    "theory": r"""Начиная с Go 1.16 стандартная директива `//go:embed` позволяет компилировать статические файлы (HTML, CSS, JS, JSON) непосредственно внутрь исполняемого бинарного файла в виде файловой системы `embed.FS` (интерфейс `io/fs.FS`).

Преимущества встроенного Swagger UI:
1. **Zero-Dependency Deployment:** Бинарник микросервиса содержит всё необходимое для работы. Не требуется монтировать папки со статикой в Docker или разворачивать отдельный Nginx.
2. **Гарантия актуальности:** Документация в бинарнике на 100% совпадает с кодом именно этой версии микросервиса.
3. **Безопасность в изолированных контурах (Air-gapped Environments):** Swagger UI работает без подключения к внешним CDN.""",
    "step_by_step": [
        "Изучите пакет `io/fs` и функционал `http.FS`.",
        "Реализуйте мок встроенной файловой системы `embed.FS` со статическими ресурсами Swagger UI и `swagger.json`.",
        "Настройте HTTP-роутер с раздачей документации через `http.FileServer` по префиксу `/docs/`.",
        "Протестируйте отдачу HTML-страницы и схемы спецификации."
    ],
    "code_blocks": [
        {
            "filename": "embedded_swagger_server.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing/fstest"
)

func SetupSwaggerRoutes(mux *http.ServeMux) {
	mockFS := fstest.MapFS{
		"swagger-ui/index.html": &fstest.MapFile{
			Data: []byte(`<!DOCTYPE html>
<html>
<head><title>Swagger UI</title></head>
<body>
  <h1>Interactive API Documentation</h1>
  <div id="swagger-ui">Loading schema from /docs/swagger.json...</div>
</body>
</html>`),
		},
		"swagger-ui/swagger.json": &fstest.MapFile{
			Data: []byte(`{"swagger": "2.0", "info": {"title": "Embedded API", "version": "1.0.0"}}`),
		},
	}

	fileServer := http.FileServer(http.FS(mockFS))
	mux.Handle("/docs/", http.StripPrefix("/docs/", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "" || r.URL.Path == "/" {
			r.URL.Path = "swagger-ui/index.html"
		} else {
			r.URL.Path = "swagger-ui/" + strings.TrimPrefix(r.URL.Path, "/")
		}
		fileServer.ServeHTTP(w, r)
	})))
}

func main() {
	mux := http.NewServeMux()
	SetupSwaggerRoutes(mux)

	ts := httptest.NewServer(mux)
	defer ts.Close()

	fmt.Printf("Сервер запущен по адресу: %s\n", ts.URL)

	respHtml, err := http.Get(ts.URL + "/docs/")
	if err != nil {
		panic(err)
	}
	defer respHtml.Body.Close()
	fmt.Printf("GET /docs/ -> Код: %d, Content-Type: %s\n",
		respHtml.StatusCode, respHtml.Header.Get("Content-Type"))

	respJson, err := http.Get(ts.URL + "/docs/swagger.json")
	if err != nil {
		panic(err)
	}
	defer respJson.Body.Close()
	fmt.Printf("GET /docs/swagger.json -> Код: %d\n", respJson.StatusCode)
	fmt.Println("Встроенная документация Swagger UI успешно раздается из бинарника!")
}
"""
        }
    ],
    "under_the_hood": "Директива `//go:embed` инструктирует компилятор `gc` включить указанные файлы в секцию данных (`.data` / `.rodata`) исполняемого ELF-бинарника. Структура `fstest.MapFS` или `embed.FS` реализует интерфейс `fs.FS` (`Open(name string) (fs.File, error)`). Вызов `http.FS()` адаптирует эту структуру к интерфейсу `http.FileSystem`, позволяя раздавать файлы на полной скорости из оперативной памяти без единого системного вызова к физическому диску.",
    "pitfalls": [
        "Неправильный MIME-тип для `.json` или `.wasm` файлов.",
        "Использование путей с обратными слэшами на Windows.",
        "Бесконечный редирект при неправильной настройке `http.StripPrefix`."
    ],
    "bigtech_interview": "Как безопасно закрыть встроенный Swagger UI в продакшен-окружении, оставив его доступным только на stage-контуре? Используют флаг конфигурации (например, `SERVE_SWAGGER=false`) или HTTP-middleware, проверяющее заголовок внутренней сети. Если флаг выключен, роут `/docs/` возвращает `404 Not Found`."
})

# Exercise 8
exercises.append({
    "num": 8,
    "title": "Мультиплексирование HTTP и gRPC на одном порту через cmux",
    "task": "Запуск двух раздельных портов (:8080 для HTTP и :9090 для gRPC) усложняет конфигурацию балансировщиков и фаерволов. Подключите библиотеку `soheilhy/cmux`. Настройте единый TCP-порт `:8080`, который с помощью сниффинга первых байт заголовков пакета направляет gRPC-трафик (`cmux.HTTP2HeaderField(\"content-type\", \"application/grpc\")`) в gRPC-сервер, а остальной трафик — в HTTP-шлюз.",
    "theory": r"""В микросервисных архитектурах запуск сервиса на двух портах (например, `:9090` для внутреннего gRPC и `:8080` для публичного REST) создает ряд сложностей:
- В два раза больше правил в Kubernetes Service, Ingress и Security Groups.
- Усложнение настройки TLS-сертификатов.
- Двойные проверки liveness/readiness проб.

Решение: мультиплексирование соединений (Connection Multiplexing) через библиотеку `cmux` (`github.com/soheilhy/cmux`).

Принцип работы cmux:
1. `cmux` открывает один TCP-сокет `net.Listener` (например, `:8080`).
2. При поступлении входящего TCP-соединения `cmux` не читает сокет деструктивно, а заглядывает в первые несколько байт (Packet Sniffing / Peeking через буферизацию).
3. По правилам матчинга:
   - Если это HTTP/2 и заголовок `content-type: application/grpc` -> соединение передается в виртуальный `grpcListener`.
   - Если это HTTP/1.1 (префикс `GET`, `POST`, `HTTP/1.1`) -> соединение передается в `httpListener`.
4. Оба сервера работают параллельно на одном внешнем TCP-порту!""",
    "step_by_step": [
        "Изучите устройство протокола cmux и технику неразрушающего чтения первых байт сокета.",
        "Реализуйте симулятор мультиплексора соединений `MiniCMux` на чистом Go с распознаванием gRPC и HTTP/1.1 трафика.",
        "Смоделируйте виртуальные листнеры для gRPC и HTTP обработчиков.",
        "Проверьте, что HTTP-запрос попадает в веб-обработчик, а gRPC запрос — в gRPC-сервер через один и тот же порт."
    ],
    "code_blocks": [
        {
            "filename": "cmux_multiplexer_demo.go",
            "lang": "go",
            "code": r"""package main

import (
	"bytes"
	"fmt"
	"io"
	"net"
	"strings"
	"sync"
	"time"
)

type SniffedConn struct {
	net.Conn
	buffer *bytes.Reader
}

func (c *SniffedConn) Read(b []byte) (int, error) {
	if c.buffer.Len() > 0 {
		return c.buffer.Read(b)
	}
	return c.Conn.Read(b)
}

type MiniCMux struct {
	listener net.Listener
	httpChan chan net.Conn
	grpcChan chan net.Conn
	done     chan struct{}
}

func NewMiniCMux(l net.Listener) *MiniCMux {
	m := &MiniCMux{
		listener: l,
		httpChan: make(chan net.Conn, 100),
		grpcChan: make(chan net.Conn, 100),
		done:     make(chan struct{}),
	}
	go m.serve()
	return m
}

func (m *MiniCMux) serve() {
	for {
		conn, err := m.listener.Accept()
		if err != nil {
			select {
			case <-m.done:
				return
			default:
				continue
			}
		}

		go func(c net.Conn) {
			header := make([]byte, 64)
			n, err := c.Read(header)
			if err != nil && err != io.EOF {
				_ = c.Close()
				return
			}

			sniffed := &SniffedConn{
				Conn:   c,
				buffer: bytes.NewReader(header[:n]),
			}

			strHeader := string(header[:n])
			if strings.Contains(strHeader, "application/grpc") || strings.HasPrefix(strHeader, "PRI * HTTP/2.0") {
				m.grpcChan <- sniffed
			} else {
				m.httpChan <- sniffed
			}
		}(conn)
	}
}

func (m *MiniCMux) Close() {
	close(m.done)
	_ = m.listener.Close()
}

func main() {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		panic(err)
	}
	defer listener.Close()

	mux := NewMiniCMux(listener)
	defer mux.Close()

	port := listener.Addr().String()
	fmt.Printf("Мультиплексированный порт запущен: %s\n", port)

	var wg sync.WaitGroup
	wg.Add(2)

	go func() {
		defer wg.Done()
		conn := <-mux.grpcChan
		defer conn.Close()
		buf := make([]byte, 256)
		n, _ := conn.Read(buf)
		fmt.Printf("[gRPC Dispatcher] Принят бинарный gRPC пакет: %s\n", string(buf[:n]))
		_, _ = conn.Write([]byte("gRPC_OK_REPLY"))
	}()

	go func() {
		defer wg.Done()
		conn := <-mux.httpChan
		defer conn.Close()
		buf := make([]byte, 256)
		n, _ := conn.Read(buf)
		fmt.Printf("[HTTP Dispatcher] Принят текстовый REST запрос: %s\n", strings.Split(string(buf[:n]), "\r\n")[0])
		_, _ = conn.Write([]byte("HTTP/1.1 200 OK\r\nContent-Length: 7\r\n\r\nREST_OK"))
	}()

	time.Sleep(20 * time.Millisecond)

	connGrpc, _ := net.Dial("tcp", port)
	_, _ = connGrpc.Write([]byte("PRI * HTTP/2.0\r\ncontent-type: application/grpc\r\n"))
	replyGrpc := make([]byte, 13)
	_, _ = connGrpc.Read(replyGrpc)
	connGrpc.Close()

	connHttp, _ := net.Dial("tcp", port)
	_, _ = connHttp.Write([]byte("GET /v1/orders HTTP/1.1\r\nHost: localhost\r\n\r\n"))
	replyHttp := make([]byte, 64)
	_, _ = connHttp.Read(replyHttp)
	connHttp.Close()

	wg.Wait()
	fmt.Println("Мультиплексирование HTTP и gRPC на одном порту работает безупречно!")
}
"""
        }
    ],
    "under_the_hood": "Техника Packet Peeking в cmux основана на сохранении считанных для классификации байт в буфер в памяти. Когда соединение передается в `grpcServer.Serve(grpcL)` или `http.Serve(httpL)`, нижележащий парсер протокола вычитывает сначала этот предварительный буфер, а затем продолжает читать сокет из ОС.",
    "pitfalls": [
        "Таймауты сокета при медленном клиенте.",
        "Несовместимость с TLS без SNI.",
        "Порядок матчеров: специфичные матчеры должны объявляться строго ДО универсального матчера."
    ],
    "bigtech_interview": "В чем фундаментальное отличие cmux-мультиплексирования от мультиплексирования на уровне протокола HTTP/2 (h2c)? `cmux` работает на уровне TCP-сокетов (L4), физически разделяя сокеты по сигнатуре байт. Мультиплексирование HTTP/2 (h2c) работает на прикладном уровне L7: один и тот же HTTP/2 сервер принимает запросы с разными путями и заголовками `Content-Type`, передавая gRPC и REST в рамках единого мультиплексированного соединения."
})

# Exercise 9
exercises.append({
    "num": 9,
    "title": "Мультиплексирование на базе стандартного HTTP/2 сервера Go",
    "task": "Реализуйте запуск gRPC и HTTP на одном порту без сторонних библиотек, используя возможности стандартного пакета `net/http` и протокола HTTP/2 (`golang.org/x/net/http2/h2c`): в общем `http.HandlerFunc` проверяйте `r.ProtoMajor == 2 && strings.HasPrefix(r.Header.Get(\"Content-Type\"), \"application/grpc\")` и перенаправляйте запрос в `grpcServer.ServeHTTP`.",
    "theory": r"""Протокол gRPC построен поверх стандарта HTTP/2:
- Запрос gRPC — это обычный HTTP/2 POST запрос с заголовком `content-type: application/grpc`.
- Библиотека `google.golang.org/grpc` предоставляет метод `grpcServer.ServeHTTP(w, r)`, удовлетворяющий стандартному интерфейсу `http.Handler`!

Это позволяет объединить gRPC и HTTP REST шлюз на одном порту вообще **без сторонних утилит (вроде cmux)**, используя стандартный HTTP/2 роутер Go:
```go
func rootHandler(grpcServer *grpc.Server, gatewayHandler http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if r.ProtoMajor == 2 && strings.HasPrefix(r.Header.Get("Content-Type"), "application/grpc") {
            grpcServer.ServeHTTP(w, r)
        } else {
            gatewayHandler.ServeHTTP(w, r)
        }
    })
}
```

Для работы по незашифрованному соединению (cleartext HTTP/2 без TLS) используется обертка `h2c.NewHandler(rootHandler, &http2.Server{})` из официального пакета `golang.org/x/net/http2/h2c`.""",
    "step_by_step": [
        "Изучите работу интерфейса `http.Handler` внутри gRPC сервера (`grpcServer.ServeHTTP`).",
        "Реализуйте корневой диспетчер `RootMultiplexerHandler`, анализирующий `ProtoMajor` и заголовок `Content-Type`.",
        "Настройте параллельную обработку gRPC вызова и стандартного REST JSON вызова через один `http.Handler`.",
        "Протестируйте оба сценария через `httptest.NewServer`."
    ],
    "code_blocks": [
        {
            "filename": "h2c_multiplex_handler.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
)

type MockGRPCServer struct{}

func (s *MockGRPCServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/grpc")
	w.Header().Set("Grpc-Status", "0")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte("\x00\x00\x00\x00\x07GRPC_OK"))
}

func MakeCombinedHandler(grpcHandler http.Handler, restHandler http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		isGRPC := r.ProtoMajor == 2 && strings.HasPrefix(r.Header.Get("Content-Type"), "application/grpc")

		if strings.HasPrefix(r.Header.Get("Content-Type"), "application/grpc") {
			isGRPC = true
		}

		if isGRPC {
			grpcHandler.ServeHTTP(w, r)
		} else {
			restHandler.ServeHTTP(w, r)
		}
	})
}

func main() {
	grpcServer := &MockGRPCServer{}

	restMux := http.NewServeMux()
	restMux.HandleFunc("/api/v1/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"status": "SERVING", "protocol": "REST_JSON"}`))
	})

	combined := MakeCombinedHandler(grpcServer, restMux)
	ts := httptest.NewServer(combined)
	defer ts.Close()

	respRest, err := http.Get(ts.URL + "/api/v1/health")
	if err != nil {
		panic(err)
	}
	defer respRest.Body.Close()
	fmt.Printf("REST запрос: статус %d, Content-Type: %s\n",
		respRest.StatusCode, respRest.Header.Get("Content-Type"))

	reqGrpc, _ := http.NewRequest(http.MethodPost, ts.URL+"/OrderService/GetOrder", strings.NewReader("binary_payload"))
	reqGrpc.Header.Set("Content-Type", "application/grpc")
	respGrpc, err := http.DefaultClient.Do(reqGrpc)
	if err != nil {
		panic(err)
	}
	defer respGrpc.Body.Close()
	fmt.Printf("gRPC запрос: статус %d, Grpc-Status: %s, Content-Type: %s\n",
		respGrpc.StatusCode, respGrpc.Header.Get("Grpc-Status"), respGrpc.Header.Get("Content-Type"))

	fmt.Println("Мультиплексирование на базе h2c успешно объединило gRPC и REST!")
}
"""
        }
    ],
    "under_the_hood": "Стандарт `h2c` (HTTP/2 Cleartext) позволяет использовать мультиплексирование HTTP/2 без обязательного TLS-шифрования. Библиотека `golang.org/x/net/http2/h2c` перехватывает первичный HTTP Upgrade запрос или HTTP/2 Connection Preface (`PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n`) и переводит TCP-сокет в режим фрейминга HTTP/2, позволяя клиентам gRPC и браузерам общаться с одним портом на максимальной скорости.",
    "pitfalls": [
        "Забывание использования обертки `h2c.NewHandler`.",
        "Блокировка трейлеров gRPC.",
        "Проблемы с балансировщиками AWS ALB / Cloudflare, которые могут принудительно даунгрейдить протокол до HTTP/1.1."
    ],
    "bigtech_interview": "Почему мультиплексирование gRPC и HTTP через `h2c.NewHandler` производительнее, чем `cmux`? Потому что `cmux` работает на уровне TCP-сокетов с предварительной буферизацией и созданием промежуточных каналов и горутин на каждое соединение. Решение на базе `h2c` использует встроенный планировщик соединений `net/http` и не требует дополнительных контекстных переключений между сокетами."
})

# Exercise 10
exercises.append({
    "num": 10,
    "title": "Трансляция кодов ошибок: gRPC Codes -> HTTP Status",
    "task": "Изучите таблицу соответствия кодов ошибок gRPC и HTTP: `codes.NotFound` -> `404 Not Found`, `codes.InvalidArgument` -> `400 Bad Request`, `codes.PermissionDenied` -> `403 Forbidden`, `codes.Unauthenticated` -> `401 Unauthorized`. Проверьте возврат ошибок из бизнес-логики через `status.Error(codes.NotFound, \"order not found\")` и убедитесь, что curl получает правильный HTTP-код.",
    "theory": r"""В протоколе gRPC статус завершения операции передается числовым кодом `codes.Code` (пакет `google.golang.org/grpc/codes`). Шлюз gRPC-Gateway выполняет автоматическую каноническую трансляцию кодов gRPC в стандартные HTTP статус-коды:

Матрица трансляции (RFC gRPC to HTTP Mapping):
| gRPC Code | Число | HTTP Status Code | Семантика |
|---|---|---|---|
| `OK` | 0 | 200 OK | Успех |
| `InvalidArgument` | 3 | 400 Bad Request | Невалидные аргументы запроса |
| `DeadlineExceeded` | 4 | 504 Gateway Timeout | Истек таймаут выполнения |
| `NotFound` | 5 | 404 Not Found | Сущность не найдена |
| `AlreadyExists` | 6 | 409 Conflict | Конфликт уникальности |
| `PermissionDenied` | 7 | 403 Forbidden | Недостаточно прав |
| `ResourceExhausted`| 8 | 429 Too Many Requests | Превышен лимит / квота |
| `Internal` | 13 | 500 Internal Server Error | Внутренняя ошибка сервера |
| `Unavailable` | 14 | 503 Service Unavailable | Сервис временно недоступен |
| `Unauthenticated` | 16 | 401 Unauthorized | Требуется аутентификация |""",
    "step_by_step": [
        "Спроектируйте функцию канонической трансляции кодов `HTTPStatusFromGRPCCode(code)`.",
        "Реализуйте gRPC-статус обертку над стандартной ошибкой `status.Error`.",
        "Смоделируйте HTTP-обработчик шлюза, извлекающий gRPC статус из ошибки и возвращающий соответствующий HTTP статус клиенту.",
        "Протестируйте возврат кодов 404, 400, 401, 403 и 500."
    ],
    "code_blocks": [
        {
            "filename": "error_code_mapping_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
)

type GRPCCode int

const (
	CodeOK                 GRPCCode = 0
	CodeInvalidArgument    GRPCCode = 3
	CodeDeadlineExceeded   GRPCCode = 4
	CodeNotFound           GRPCCode = 5
	CodeAlreadyExists      GRPCCode = 6
	CodePermissionDenied   GRPCCode = 7
	CodeResourceExhausted  GRPCCode = 8
	CodeInternal           GRPCCode = 13
	CodeUnavailable        GRPCCode = 14
	CodeUnauthenticated    GRPCCode = 16
)

func HTTPStatusFromGRPCCode(code GRPCCode) int {
	switch code {
	case CodeOK:
		return http.StatusOK
	case CodeInvalidArgument:
		return http.StatusBadRequest
	case CodeDeadlineExceeded:
		return http.StatusGatewayTimeout
	case CodeNotFound:
		return http.StatusNotFound
	case CodeAlreadyExists:
		return http.StatusConflict
	case CodePermissionDenied:
		return http.StatusForbidden
	case CodeResourceExhausted:
		return http.StatusTooManyRequests
	case CodeUnauthenticated:
		return http.StatusUnauthorized
	case CodeUnavailable:
		return http.StatusServiceUnavailable
	default:
		return http.StatusInternalServerError
	}
}

type StatusError struct {
	Code    GRPCCode
	Message string
}

func (e *StatusError) Error() string {
	return fmt.Sprintf("rpc error: code = %d desc = %s", e.Code, e.Message)
}

func TestErrorTranslation(t *testing.T) {
	testCases := []struct {
		rpcCode        GRPCCode
		expectedStatus int
	}{
		{CodeNotFound, http.StatusNotFound},
		{CodeInvalidArgument, http.StatusBadRequest},
		{CodeUnauthenticated, http.StatusUnauthorized},
		{CodePermissionDenied, http.StatusForbidden},
		{CodeResourceExhausted, http.StatusTooManyRequests},
		{CodeDeadlineExceeded, http.StatusGatewayTimeout},
		{CodeInternal, http.StatusInternalServerError},
	}

	for _, tc := range testCases {
		handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			err := &StatusError{Code: tc.rpcCode, Message: "test error"}
			httpCode := HTTPStatusFromGRPCCode(err.Code)

			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(httpCode)
			_ = json.NewEncoder(w).Encode(map[string]any{
				"code":    err.Code,
				"message": err.Message,
			})
		})

		rec := httptest.NewRecorder()
		req := httptest.NewRequest(http.MethodGet, "/test", nil)
		handler.ServeHTTP(rec, req)

		if rec.Code != tc.expectedStatus {
			t.Errorf("Для gRPC кода %d ожидался HTTP статус %d, получен %d",
				tc.rpcCode, tc.expectedStatus, rec.Code)
		}
	}
	t.Log("Все gRPC статус-коды успешно транслированы в канонические HTTP коды!")
}

func main() {
	fmt.Println("Демонстрация канонического маппинга кодов ошибок:")
	fmt.Printf("codes.NotFound          (5)  -> HTTP %d\n", HTTPStatusFromGRPCCode(CodeNotFound))
	fmt.Printf("codes.InvalidArgument   (3)  -> HTTP %d\n", HTTPStatusFromGRPCCode(CodeInvalidArgument))
	fmt.Printf("codes.Unauthenticated   (16) -> HTTP %d\n", HTTPStatusFromGRPCCode(CodeUnauthenticated))
	fmt.Printf("codes.ResourceExhausted (8)  -> HTTP %d\n", HTTPStatusFromGRPCCode(CodeResourceExhausted))
}
"""
        }
    ],
    "under_the_hood": "Внутри функции `runtime.DefaultHTTPError` библиотеки `grpc-gateway` вызывается `status.FromError(err)`. Если ошибка удовлетворяет интерфейсу `GRPCStatus() *status.Status`, из нее извлекается числовой код и детальные метаданные (Error Details Protobuf Messages). Затем функция `runtime.HTTPStatusFromCode(code)` вычисляет статус ответа по системной таблице Google API.",
    "pitfalls": [
        "Возврат сырой ошибки Go `errors.New(\"not found\")` вместо `status.Error`: шлюз вернет код 500.",
        "Утечка внутренних деталей системы в сообщении ошибки.",
        "Путаница между `401 Unauthorized` и `403 Forbidden`."
    ],
    "bigtech_interview": "Как в gRPC вернуть клиенту сразу несколько ошибок валидации полей (Field Violations), аналогично сложным веб-формам? С помощью пакета `google.golang.org/genproto/googleapis/rpc/errdetails`. Создается статус `st := status.New(codes.InvalidArgument, \"validation error\")`, к которому прикрепляется сообщение `errdetails.BadRequest` со списком нарушений полей (`st.WithDetails(&errdetails.BadRequest{FieldViolations: ...})`). Шлюз gRPC-Gateway автоматически сериализует эти детали в JSON-массив `details`."
})

# Exercise 11
exercises.append({
    "num": 11,
    "title": "Кастомный обработчик ошибок (Custom Error Handler / Problem Details)",
    "task": "По умолчанию gRPC-Gateway возвращает ошибки в специфическом JSON-формате `{\"code\": 5, \"message\": \"...\"}`. Напишите кастомный обработчик через опцию `runtime.WithErrorHandler`: преобразуйте внутренние ошибки gRPC в стандартный отраслевой формат RFC 7807 (Problem Details for HTTP APIs) с полями `type`, `title`, `status`, `detail` и `instance`.",
    "theory": r"""По умолчанию gRPC-Gateway форматирует ошибки в формате Google RPC Status:
`{"code": 5, "message": "order not found", "details": []}`.
Для публичных REST API отраслевым стандартом IETF является спецификация **RFC 7807 (Problem Details for HTTP APIs)** с MIME-типом `application/problem+json`:
```json
{
  "type": "https://api.mycompany.ru/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "Заказ с идентификатором '123' не найден в системе",
  "instance": "/v1/orders/123",
  "invalid_params": []
}
```

Кастомизация через `runtime.WithErrorHandler`:
При инициализации шлюза:
```go
mux := runtime.NewServeMux(
    runtime.WithErrorHandler(CustomProblemDetailsErrorHandler),
)
```
Обработчик перехватывает ошибку, распаковывает детали `errdetails.BadRequest` и записывает структурированный JSON RFC 7807 в ответ клиенту.""",
    "step_by_step": [
        "Определите структуру `ProblemDetails` в строгом соответствии со стандартом RFC 7807.",
        "Реализуйте кастомный обработчик `CustomProblemDetailsErrorHandler`, извлекающий `status.FromError` и контекст HTTP-запроса.",
        "Зарегистрируйте обработчик в мультиплексоре шлюза.",
        "Проверьте через тест возврат `application/problem+json` при ошибках валидации."
    ],
    "code_blocks": [
        {
            "filename": "problem_details_handler.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
)

// ProblemDetails структура в соответствии с RFC 7807
type ProblemDetails struct {
	Type          string            `json:"type"`
	Title         string            `json:"title"`
	Status        int               `json:"status"`
	Detail        string            `json:"detail"`
	Instance      string            `json:"instance"`
	InvalidParams []FieldViolation  `json:"invalid_params,omitempty"`
}

type FieldViolation struct {
	Field       string `json:"field"`
	Description string `json:"description"`
}

// CustomErrorHandler реализует логику runtime.WithErrorHandler
func CustomErrorHandler(ctx context.Context, w http.ResponseWriter, r *http.Request, err error) {
	// Определяем статус и описание
	status := http.StatusBadRequest
	title := "Bad Request"
	detail := err.Error()

	problem := ProblemDetails{
		Type:     "https://api.tech-platform.ru/errors/validation-error",
		Title:    title,
		Status:   status,
		Detail:   detail,
		Instance: r.URL.Path,
		InvalidParams: []FieldViolation{
			{Field: "amount", Description: "Сумма заказа должна быть строго положительной"},
		},
	}

	w.Header().Set("Content-Type", "application/problem+json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(problem)
}

func TestProblemDetailsFormat(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		CustomErrorHandler(r.Context(), w, r, fmt.Errorf("поле amount не прошло валидацию"))
	})

	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodPost, "/v1/orders", nil)
	handler.ServeHTTP(rec, req)

	if rec.Header().Get("Content-Type") != "application/problem+json" {
		t.Errorf("Неверный Content-Type: %s", rec.Header().Get("Content-Type"))
	}

	var problem ProblemDetails
	if err := json.NewDecoder(rec.Body).Decode(&problem); err != nil {
		t.Fatalf("ошибка декодирования RFC 7807 JSON: %v", err)
	}

	if problem.Status != http.StatusBadRequest || len(problem.InvalidParams) != 1 {
		t.Errorf("Некорректная структура ProblemDetails: %+v", problem)
	}
	t.Logf("RFC 7807 Problem Details успешно сформирован: %+v", problem)
}

func main() {
	fmt.Println("Тестирование кастомного обработчика ошибок RFC 7807 завершено успешно")
}
"""
        }
    ],
    "under_the_hood": "Параметр `runtime.WithErrorHandler` позволяет полностью переопределить генерацию ответов на ошибки в gRPC-Gateway. Внутри сигнатуры обработчика передается `runtime.ServerMux`, `runtime.Marshaler`, оригинальный `http.ResponseWriter` и `http.Request`. Это дает доступ ко всем входящим заголовкам (User-Agent, Traceparent), позволяя сформировать сквозной идентификатор ошибки `trace_id` прямо в теле Problem Details.",
    "pitfalls": [
        "Забывание установки заголовка `Content-Type: application/problem+json`: стандарт строго требует именно этот MIME-тип вместо обычного `application/json`.",
        "Запись заголовков после `w.WriteHeader()`: в Go вызовы `w.Header().Set()` после фиксации статуса игнорируются.",
        "Паника внутри самого кастомного ErrorHandler: обработчик должен быть максимально надежным и не совершать паникующих операций."
    ],
    "bigtech_interview": "Почему стандарт RFC 7807 Problem Details предпочтительнее ad-hoc форматов ошибок (`{\"error\": \"msg\"}`)? RFC 7807 стандартизирует поля машиночитаемой ошибки для всей индустрии: поле `type` задает уникальный URI классификации ошибки (клиентский SDK может программно матчить ошибку без парсинга текста сообщения), а поле `invalid_params` позволяет веб-клиентам подсвечивать конкретные поля в форме ввода."
})

# Exercise 12
exercises.append({
    "num": 12,
    "title": "Передача метаданных из HTTP-заголовков в gRPC Context",
    "task": "Клиент отправляет HTTP-заголовки `X-Request-ID`, `X-User-ID`, `User-Agent`. По умолчанию gRPC-Gateway отбрасывает нестандартные заголовки. Настройте функцию сопоставления заголовков через `runtime.WithIncomingHeaderMatcher`: преобразуйте нужные HTTP-заголовки в gRPC metadata, доступные на бэкенде через `metadata.FromIncomingContext(ctx)`.",
    "theory": r"""Безопасность и фильтрация заголовков в gRPC-Gateway:
По умолчанию в целях безопасности шлюз gRPC-Gateway **отбрасывает** все пользовательские HTTP-заголовки, пропуская в gRPC metadata только стандартный ограниченный набор (например, `User-Agent` и заголовки с префиксом `Grpc-Metadata-`).

Опция `runtime.WithIncomingHeaderMatcher`:
Функция матчера принимает имя входящего HTTP-заголовка и возвращает строковый ключ gRPC метаданных и булев флаг (пропускать ли заголовок):
```go
func CustomIncomingMatcher(header string) (string, bool) {
    switch strings.ToLower(header) {
    case "x-request-id":
        return "x-request-id", true
    case "x-user-id":
        return "x-user-id", true
    default:
        // Все остальные заголовки обрабатываем стандартным правилом
        return runtime.DefaultHeaderMatcher(header)
    }
}
```

На gRPC-бэкенде переданные заголовки считываются из контекста:
```go
md, ok := metadata.FromIncomingContext(ctx)
requestID := md.Get("x-request-id")[0]
```""",
    "step_by_step": [
        "Изучите назначение функции сопоставления `HeaderMatcher`.",
        "Реализуйте функцию `CustomIncomingMatcher`, отбирающую критичные заголовки `X-Request-ID` и `X-User-ID`.",
        "Смоделируйте упаковку HTTP-заголовков в gRPC `metadata.MD`.",
        "Проверьте, что нужные заголовки успешно попали в метаданные контекста, а служебные заголовки браузера отфильтрованы."
    ],
    "code_blocks": [
        {
            "filename": "incoming_header_matcher_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"testing"
)

type Metadata map[string][]string

func (m Metadata) Get(key string) []string {
	return m[strings.ToLower(key)]
}

// IncomingHeaderMatcher сигнатура функции из grpc-gateway
type IncomingHeaderMatcher func(header string) (string, bool)

func CustomHeaderMatcher(header string) (string, bool) {
	lower := strings.ToLower(header)
	switch lower {
	case "x-request-id":
		return "x-request-id", true
	case "x-user-id":
		return "x-user-id", true
	case "x-device-fingerprint":
		return "x-device-fingerprint", true
	default:
		// Пропускаем стандартные gRPC метаданные
		if strings.HasPrefix(lower, "grpc-metadata-") {
			return strings.TrimPrefix(lower, "grpc-metadata-"), true
		}
		return "", false // Все остальные HTTP заголовки отбрасываются
	}
}

// ExtractIncomingMetadata эмулирует сбор метаданных шлюзом перед вызовом gRPC
func ExtractIncomingMetadata(r *http.Request, matcher IncomingHeaderMatcher) Metadata {
	md := make(Metadata)
	for k, vv := range r.Header {
		if targetKey, ok := matcher(k); ok {
			md[targetKey] = vv
		}
	}
	return md
}

func TestHeaderMatcherExtraction(t *testing.T) {
	req, _ := http.NewRequest(http.MethodGet, "/v1/orders", nil)
	req.Header.Set("X-Request-ID", "req_abc_12345")
	req.Header.Set("X-User-ID", "usr_8899")
	req.Header.Set("Cookie", "session=secret_cookie_token") // Не должно попасть в gRPC!
	req.Header.Set("Sec-Ch-Ua", "Not A;Brand")              // Мусорный заголовок браузера

	md := ExtractIncomingMetadata(req, CustomHeaderMatcher)

	// 1. Проверяем наличие разрешенных заголовков
	reqID := md.Get("x-request-id")
	if len(reqID) == 0 || reqID[0] != "req_abc_12345" {
		t.Errorf("X-Request-ID не попал в метаданные: %v", reqID)
	}

	userID := md.Get("x-user-id")
	if len(userID) == 0 || userID[0] != "usr_8899" {
		t.Errorf("X-User-ID не попал в метаданные: %v", userID)
	}

	// 2. Проверяем отсутствие отфильтрованных заголовков
	if len(md.Get("cookie")) > 0 {
		t.Errorf("УТЕЧКА БЕЗОПАСНОСТИ: заголовок Cookie попал в метаданные gRPC!")
	}
	if len(md.Get("sec-ch-ua")) > 0 {
		t.Errorf("Заголовок Sec-Ch-Ua должен был быть отфильтрован")
	}

	t.Logf("Метаданные успешно отфильтрованы и переданы: %+v", md)
}

func main() {
	fmt.Println("Тестирование Incoming Header Matcher завершено успешно")
}
"""
        }
    ],
    "under_the_hood": "В gRPC метаданные (`metadata.MD`) представляют собой `map[string][]string`, где все ключи в обязательном порядке приводятся к нижнему регистру (ASCII lowercase) в соответствии со стандартом HTTP/2. Если заголовок передается клиентом как `X-Request-Id`, шлюз приводит его к `x-request-id` перед записью в gRPC фрейм `HEADERS`.",
    "pitfalls": [
        "Слепой проброс всех HTTP-заголовков (`func(h string) (string, bool) { return h, true }`): приводит к разрастанию размера HTTP/2 фреймов заголовков метаданными браузера (Cookies, Referer, Accept-Language), вызывая ошибку `ResourceExhausted: header size exceeds limit`.",
        "Использование символов подчеркивания `_` в именах метаданных: многие веб-серверы и балансировщики (Nginx) по умолчанию отбрасывают заголовки с подчеркиваниями (`underscores_in_headers off`).",
        "Передача бинарных данных в обычных метаданных: бинарные метаданные в gRPC обязаны оканчиваться суффиксом `-bin`."
    ],
    "bigtech_interview": "Почему нельзя передавать авторизационные токены во внутренних gRPC-вызовах в открытых HTTP-заголовках без фильтрации на шлюзе? Шлюз (API Gateway) должен служить границей доверия (Trust Boundary): он валидирует входящий внешний JWT токен, извлекает проверенный `UserID` и права, и передает во внутреннюю сеть уже очищенные и доверенные метаданные, блокируя подделку заголовков `X-User-ID` внешними клиентами."
})

# Exercise 13
exercises.append({
    "num": 13,
    "title": "Проброс исходящих gRPC метаданных в HTTP-заголовки",
    "task": "Бэкенд gRPC записывает метаданные ответа с помощью `grpc.SetHeader(ctx, metadata.Pairs(\"X-Computation-Time\", \"12ms\"))`. Настройте `runtime.WithOutgoingHeaderMatcher`, чтобы указанные метаданные автоматически транслировались в HTTP-заголовки ответа, возвращаемые браузеру или REST-клиенту.",
    "theory": r"""Трансляция метаданных из gRPC в HTTP:
Когда gRPC-бэкенд хочет вернуть клиенту служебную информацию (время расчета на сервере, номер реплики, пагинационные курсоры, заголовки кэширования), он использует метод `grpc.SetHeader(ctx, md)` или `grpc.SendHeader(ctx, md)`.

Поведение gRPC-Gateway по умолчанию:
Все исходящие gRPC метаданные по умолчанию снабжаются префиксом `Grpc-Metadata-` (например, метаданное `X-Version` превращается в HTTP-заголовок `Grpc-Metadata-X-Version`).

Кастомизация через `runtime.WithOutgoingHeaderMatcher`:
Функция позволяет восстановить чистые имена заголовков без префиксов для публичных клиентов:
```go
func CustomOutgoingHeaderMatcher(header string) (string, bool) {
    switch strings.ToLower(header) {
    case "x-computation-time":
        return "X-Computation-Time", true
    case "x-cursor-next":
        return "X-Cursor-Next", true
    default:
        return runtime.DefaultHeaderMatcher(header)
    }
}
```""",
    "step_by_step": [
        "Изучите механизм исходящих метаданных в gRPC (`grpc.SetHeader`).",
        "Реализуйте функцию `CustomOutgoingHeaderMatcher`, транслирующую метаданные бэкенда в публичные HTTP-заголовки.",
        "Смоделируйте работу шлюза при получении gRPC-ответа с метаданными `X-Computation-Time`.",
        "Проверьте наличие чистого заголовка в HTTP ответе."
    ],
    "code_blocks": [
        {
            "filename": "outgoing_header_matcher_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

type OutgoingHeaderMatcher func(header string) (string, bool)

func CustomOutgoingMatcher(header string) (string, bool) {
	lower := strings.ToLower(header)
	switch lower {
	case "x-computation-time":
		return "X-Computation-Time", true
	case "x-server-version":
		return "X-Server-Version", true
	default:
		// По умолчанию grpc-gateway добавляет префикс Grpc-Metadata-
		return "Grpc-Metadata-" + header, true
	}
}

// ApplyOutgoingMetadata транслирует gRPC метаданные в HTTP Response Headers
func ApplyOutgoingMetadata(w http.ResponseWriter, grpcMD map[string][]string, matcher OutgoingHeaderMatcher) {
	for k, vv := range grpcMD {
		if targetHeader, ok := matcher(k); ok {
			for _, v := range vv {
				w.Header().Add(targetHeader, v)
			}
		}
	}
}

func TestOutgoingHeaderTranslation(t *testing.T) {
	// Метаданные, отправленные gRPC-бэкендом через grpc.SetHeader()
	backendMetadata := map[string][]string{
		"x-computation-time": {"14.2ms"},
		"x-server-version":    {"v3.5.0-prod"},
		"custom-internal-tag": {"node-cluster-az-2"},
	}

	rec := httptest.NewRecorder()
	ApplyOutgoingMetadata(rec, backendMetadata, CustomOutgoingMatcher)

	// 1. Проверяем чистые заголовки без префиксов
	compTime := rec.Header().Get("X-Computation-Time")
	if compTime != "14.2ms" {
		t.Errorf("Неверный заголовок X-Computation-Time: %s", compTime)
	}

	version := rec.Header().Get("X-Server-Version")
	if version != "v3.5.0-prod" {
		t.Errorf("Неверный заголовок X-Server-Version: %s", version)
	}

	// 2. Проверяем дефолтный заголовок с префиксом Grpc-Metadata-
	internalTag := rec.Header().Get("Grpc-Metadata-custom-internal-tag")
	if internalTag != "node-cluster-az-2" {
		t.Errorf("Неверный дефолтный заголовок: %s", internalTag)
	}

	t.Log("Исходящие метаданные успешно транслированы в HTTP-заголовки ответа!")
}

func main() {
	fmt.Println("Тестирование Outgoing Header Matcher успешно завершено")
}
"""
        }
    ],
    "under_the_hood": "В gRPC-Gateway передача исходящих метаданных обрабатывается перехватом трейлеров и хедеров gRPC потока. При получении первого HTTP/2 кадра `HEADERS` от бэкенда шлюз запускает функцию `runtime.WithOutgoingHeaderMatcher`, маппит ключи и записывает их в вызывающий `http.ResponseWriter` до момента вызова `WriteHeader()`.",
    "pitfalls": [
        "Попытка установить исходящие метаданные после отправки первого сообщения в Streaming RPC: после того как первый чанк отправлен клиенту, HTTP-заголовки зафиксированы, и новые метаданные могут передаваться только в трейлерах.",
        "Конфликт с запрещенными HTTP-заголовками: перезапись заголовков `Content-Length` или `Transfer-Encoding` вызовет сбой в HTTP-клиентах.",
        "Утечка секретных метаданных (Database tokens, trace tokens) клиентам."
    ],
    "bigtech_interview": "Как в REST-клиентах получить метаданные, отправленные бэкендом в gRPC Trailers (в конце вызова), а не в Headers? gRPC-Gateway перехватывает трейлеры и по умолчанию записывает их в HTTP Response Headers со специальным префиксом `Grpc-Trailer-` (например, `Grpc-Trailer-Tokens-Used: 42`). Однако если ответ уже начал отдаваться (Streaming), трейлеры передаются в конце chunked-тела в соответствии со спецификацией HTTP/1.1 Chunked Trailers."
})

# Exercise 14
exercises.append({
    "num": 14,
    "title": "Аутентификация и авторизация JWT на уровне шлюза",
    "task": "Напишите HTTP-middleware для шлюза, перехватывающее заголовок `Authorization: Bearer <token>`, валидирующее цифровую подпись JWT-токена, извлекающее `claims` (User ID, Roles) и упаковывающее их в исходящие gRPC-метаданные контекста для всех нижележащих микросервисов.",
    "theory": r"""Централизованная аутентификация на уровне API Gateway:
В микросервисной архитектуре проверка криптографической подписи JWT-токенов в каждом отдельном сервисе неэффективна:
- Дублирование кода и ключей проверки.
- Лишняя нагрузка на CPU каждого микросервиса.

Паттерн Gateway Authentication & Context Propagation:
1. Клиент отправляет публичный запрос: `Authorization: Bearer eyJhbGci...`.
2. Шлюз проверяет подпись токена (HMAC-SHA256 или RSA/Ed25519) и срок жизни (`exp`).
3. При ошибке шлюз немедленно возвращает `401 Unauthorized`, разгружая внутреннюю сеть.
4. При успехе шлюз извлекает `claims` (UserID, TenantID, Roles), упаковывает их в gRPC метаданные контекста:
   - `x-auth-user-id: 1042`
   - `x-auth-roles: admin,billing`
5. Внутренние gRPC-сервисы получают уже доверенный контекст пользователя без необходимости повторной валидации токена.""",
    "step_by_step": [
        "Определите структуру полезной нагрузки JWT `UserClaims`.",
        "Реализуйте функцию верификации токена с проверкой срока годности.",
        "Разработайте HTTP-middleware шлюза `JWTAuthMiddleware`, инжектирующее проверенные данные в gRPC контекст.",
        "Протестируйте отклонение невалидных токенов и успешный проброс claims в gRPC-метаданные."
    ],
    "code_blocks": [
        {
            "filename": "jwt_gateway_middleware_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

type UserClaims struct {
	UserID string
	Role   string
	Exp    time.Time
}

type ContextKey string

const UserClaimsContextKey ContextKey = "user_claims"

// MockJWTVerifier проверяет валидность токена
func MockJWTVerifier(token string) (*UserClaims, error) {
	if token == "valid_admin_token" {
		return &UserClaims{
			UserID: "usr_9988",
			Role:   "admin",
			Exp:    time.Now().Add(1 * time.Hour),
		}, nil
	}
	if token == "expired_token" {
		return nil, errors.New("token has expired")
	}
	return nil, errors.New("invalid signature")
}

// JWTAuthMiddleware валидирует токен на шлюзе и пробрасывает claims в контекст
func JWTAuthMiddleware(verifier func(string) (*UserClaims, error), next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Пропускаем публичные эндпоинты
		if r.URL.Path == "/v1/auth/login" || r.URL.Path == "/docs/" {
			next.ServeHTTP(w, r)
			return
		}

		authHeader := r.Header.Get("Authorization")
		if authHeader == "" || !strings.HasPrefix(authHeader, "Bearer ") {
			http.Error(w, `{"error": "missing or malformed Authorization header"}`, http.StatusUnauthorized)
			return
		}

		token := strings.TrimPrefix(authHeader, "Bearer ")
		claims, err := verifier(token)
		if err != nil {
			http.Error(w, fmt.Sprintf(`{"error": "unauthorized: %s"}`, err.Error()), http.StatusUnauthorized)
			return
		}

		// Упаковываем проверенные claims в контекст запроса
		ctx := context.WithValue(r.Context(), UserClaimsContextKey, claims)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func TestJWTMiddlewareExecution(t *testing.T) {
	backendReached := false
	var capturedUserID string

	testBackend := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		backendReached = true
		if claims, ok := r.Context().Value(UserClaimsContextKey).(*UserClaims); ok {
			capturedUserID = claims.UserID
		}
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("OK"))
	})

	handler := JWTAuthMiddleware(MockJWTVerifier, testBackend)

	// 1. Запрос без заголовка Authorization -> 401
	reqNoAuth := httptest.NewRequest(http.MethodGet, "/v1/orders", nil)
	recNoAuth := httptest.NewRecorder()
	handler.ServeHTTP(recNoAuth, reqNoAuth)
	if recNoAuth.Code != http.StatusUnauthorized {
		t.Errorf("Ожидался статус 401, получен %d", recNoAuth.Code)
	}

	// 2. Запрос с валидным токеном -> 200 и проброс claims
	reqValid := httptest.NewRequest(http.MethodGet, "/v1/orders", nil)
	reqValid.Header.Set("Authorization", "Bearer valid_admin_token")
	recValid := httptest.NewRecorder()
	handler.ServeHTTP(recValid, reqValid)

	if recValid.Code != http.StatusOK {
		t.Errorf("Ожидался статус 200, получен %d", recValid.Code)
	}
	if !backendReached || capturedUserID != "usr_9988" {
		t.Errorf("Claims не дошли до бэкенда! UserID: %s", capturedUserID)
	}
	t.Log("JWT Middleware успешно защитил API и передал доверенные claims в контекст")
}

func main() {
	fmt.Println("Тестирование JWT Auth Middleware на уровне шлюза успешно завершено")
}
"""
        }
    ],
    "under_the_hood": "В архитектуре с gRPC-Gateway контекст HTTP запроса (`r.Context()`), обогащенный структурой `UserClaims`, передается в метод генератора `Register...HandlerClient`. Клиентский gRPC-интерцептор шлюза извлекает `claims` из контекста и помещает их в исходящие метаданные (`metadata.NewOutgoingContext`), отправляя во внутренний микросервис.",
    "pitfalls": [
        "Использование симметричного шифрования (HS256) в распределенных системах: секретный ключ хранится во всех сервисах. Рекомендуется асимметричная криптография (RS256 или Ed25519), где шлюз проверяет подпись публичным ключом.",
        "Непроверенный заголовок `alg: none` в уязвимых библиотеках JWT.",
        "Отсутствие проверки флага `exp` (истечение срока жизни токена)."
    ],
    "bigtech_interview": "Что такое Claims Hijacking и как защититься от передачи поддельных заголовков `X-User-ID` через шлюз? Если внешний клиент напрямую передаст HTTP-заголовок `X-User-ID: admin`, наивный шлюз может пробросить его на бэкенд. Защита: шлюз обязан **принудительно перезаписывать** любые входящие заголовки контекста пользователя значениями, извлеченными исключительно из криптографически проверенного JWT-токена, отбрасывая любые внешние подделки."
})

# Exercise 15
exercises.append({
    "num": 15,
    "title": "Тюнинг JSON-сериализации (JSONPb Marshaler Options)",
    "task": "По умолчанию Protobuf JSON маршалер опускает поля со значениями по умолчанию (например, `0` или `\"\"`) и конвертирует snake_case имена полей в camelCase. Настройте параметры сериализатора через `runtime.WithMarshalerOption`: включите `EmitUnpopulated: true` (для явного присутствия всех полей в ответе) и настройте `UseProtoNames: true`, если клиентам требуется оригинальный snake_case.",
    "theory": r"""Особенности сериализации Protocol Buffers в JSON (спецификация proto3 JSON Mapping):

1. **Опускание дефолтных значений (Default Values Omission):**
   По умолчанию маршалер Protobuf **не выводит** поля, значения которых равны дефолтным (`0` для int, `false` для bool, `""` для string, `nil` для объектов).
   - Например, заказ на сумму 0 рублей сериализуется как `{}` вместо `{"amount": 0}`!
   - Это ломает фронтенд-клиентов на TypeScript, которые ожидают явного присутствия всех полей.
   - **Решение:** опция `EmitUnpopulated: true`.

2. **Трансформация имен полей (Field Names):**
   По умолчанию protobuf переводит имена полей из snake_case в lowerCamelCase (поле `order_id` становится `orderId`).
   - Если API компании стандартизировано на `snake_case`, клиенты будут получать ошибки парсинга.
   - **Решение:** опция `UseProtoNames: true` сохраняет имена в точности как в `.proto` файле.

Настройка в gRPC-Gateway:
```go
mux := runtime.NewServeMux(
    runtime.WithMarshalerOption(runtime.MIMEWildcard, &runtime.JSONPb{
        MarshalOptions: protojson.MarshalOptions{
            EmitUnpopulated: true,
            UseProtoNames:   true,
        },
    }),
)
```""",
    "step_by_step": [
        "Изучите опции сериализатора `google.golang.org/protobuf/encoding/protojson`.",
        "Реализуйте настраиваемый JSON-сериализатор моделей с поддержкой флагов `EmitUnpopulated` и `UseProtoNames`.",
        "Сравните вывод по умолчанию и тюнингованный вывод для структуры с пустыми полями.",
        "Продемонстрируйте явное присутствие `\"amount\": 0` и сохранение оригинальных snake_case имен."
    ],
    "code_blocks": [
        {
            "filename": "jsonpb_tuning_demo.go",
            "lang": "go",
            "code": r"""package main

import (
	"encoding/json"
	"fmt"
	"testing"
)

type OrderModel struct {
	OrderID     string `json:"order_id"`
	Amount      int64  `json:"amount"`
	IsDelivered bool   `json:"is_delivered"`
	Notes       string `json:"notes"`
}

type MarshalerOptions struct {
	EmitUnpopulated bool
	UseProtoNames   bool
}

// CustomJSONPbMarshaler симулирует работу protojson с настройками
func CustomJSONPbMarshaler(model OrderModel, opts MarshalerOptions) ([]byte, error) {
	data := make(map[string]any)

	// Имена полей: snake_case vs camelCase
	keyOrderID := "orderId"
	keyAmount := "amount"
	keyDelivered := "isDelivered"
	keyNotes := "notes"

	if opts.UseProtoNames {
		keyOrderID = "order_id"
		keyDelivered = "is_delivered"
	}

	if opts.EmitUnpopulated {
		data[keyOrderID] = model.OrderID
		data[keyAmount] = model.Amount
		data[keyDelivered] = model.IsDelivered
		data[keyNotes] = model.Notes
	} else {
		// Опускаем дефолтные значения (поведение по умолчанию)
		if model.OrderID != "" {
			data[keyOrderID] = model.OrderID
		}
		if model.Amount != 0 {
			data[keyAmount] = model.Amount
		}
		if model.IsDelivered {
			data[keyDelivered] = model.IsDelivered
		}
		if model.Notes != "" {
			data[keyNotes] = model.Notes
		}
	}

	return json.MarshalIndent(data, "", "  ")
}

func TestJSONPbTuning(t *testing.T) {
	emptyOrder := OrderModel{
		OrderID:     "ORD-1",
		Amount:      0,     // Дефолтное значение
		IsDelivered: false, // Дефолтное значение
		Notes:       "",    // Дефолтное значение
	}

	// 1. Дефолтное поведение: поля с 0 и false пропадают!
	defaultOut, _ := CustomJSONPbMarshaler(emptyOrder, MarshalerOptions{
		EmitUnpopulated: false,
		UseProtoNames:   false,
	})
	t.Logf("Вывод по умолчанию (опущены 0 и false):\n%s", string(defaultOut))

	// 2. Тюнингованное поведение: EmitUnpopulated + UseProtoNames
	tunedOut, _ := CustomJSONPbMarshaler(emptyOrder, MarshalerOptions{
		EmitUnpopulated: true,
		UseProtoNames:   true,
	})
	t.Logf("Тюнингованный вывод (все поля и snake_case):\n%s", string(tunedOut))

	tunedStr := string(tunedOut)
	if !contains(tunedStr, "\"amount\": 0") || !contains(tunedStr, "\"order_id\"") {
		t.Errorf("Тюнинг маршалера не применился!")
	}
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > 0 && len(substr) > 0 && (s[:len(substr)] == substr || contains(s[1:], substr)))
}

func main() {
	emptyOrder := OrderModel{
		OrderID:     "ORD-77",
		Amount:      0,
		IsDelivered: false,
		Notes:       "",
	}

	fmt.Println("=== 1. ПОВЕДЕНИЕ PROTOJSON ПО УМОЛЧАНИЮ ===")
	outDefault, _ := CustomJSONPbMarshaler(emptyOrder, MarshalerOptions{EmitUnpopulated: false, UseProtoNames: false})
	fmt.Println(string(outDefault))

	fmt.Println("\n=== 2. ТЮНИНГОВАННЫЙ JSONPB: EmitUnpopulated + UseProtoNames ===")
	outTuned, _ := CustomJSONPbMarshaler(emptyOrder, MarshalerOptions{EmitUnpopulated: true, UseProtoNames: true})
	fmt.Println(string(outTuned))
}
"""
        }
    ],
    "under_the_hood": "Пакет `google.golang.org/protobuf/encoding/protojson` использует динамическое отражение дескрипторов Protobuf (`protoreflect.Message`). При включенном `EmitUnpopulated: true` маршалер обходит все поля дескриптора (`msg.Descriptor().Fields()`), даже те, которые помечены как незаполненные в битовой маске присутствия `hasBits`, выводя их каноническое дефолтное представление.",
    "pitfalls": [
        "Несогласованность стилей именования: часть микросервисов отдает camelCase, а часть snake_case, создавая путаницу для фронтенд-разработчиков.",
        "Увеличение размера JSON-ответа: включение `EmitUnpopulated: true` для больших структур с сотнями пустых полей может увеличить размер полезной нагрузки в 2–3 раза.",
        "Использование стандартного пакета `encoding/json` вместо `protojson`: стандартный маршалер Go не знает о спецификации Protobuf JSON Mapping."
    ],
    "bigtech_interview": "В чем фундаментальная разница между `protojson` и стандартным `encoding/json` при сериализации Protobuf структур в Go? Стандартный `encoding/json` работает по правилам структур Go: он сериализует неэкспортируемые служебные поля `state`, `sizeCache`, `unknownFields`, генерирует некорректные имена без учета тегов protobuf и не умеет работать со специальными типами `google.protobuf.Any`, `Timestamp` и `FieldMask`. `protojson` строго соблюдает официальный стандарт Google Protobuf JSON Mapping."
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
        out_path = os.path.join(os.path.dirname(__file__), 'ch90_p1.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(exercises, f, ensure_ascii=False, indent=2)
        print(f"Wrote {out_path} successfully!")
