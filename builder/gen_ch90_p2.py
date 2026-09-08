# -*- coding: utf-8 -*-
import json
import subprocess
import tempfile
import os

exercises = []

# Exercise 16
exercises.append({
    "num": 16,
    "title": "Поддержка Server-Streaming RPC в HTTP-шлюзе (Chunked Transfer / SSE)",
    "task": "Напишите метод потоковой передачи данных с сервера `rpc StreamNotifications(UserRequest) returns (stream Notification)`. Покажите, как gRPC-Gateway автоматически транслирует gRPC-стрим в HTTP Chunked Transfer Encoding или Server-Sent Events (SSE), позволяя клиентам читать поток событий в реальном времени.",
    "theory": r"""При обращении к серверному потоковому RPC (`server-streaming`) gRPC отправляет последовательность независимых Protobuf-сообщений в рамках одного HTTP/2 фреймированного стрима.

Стандартный `grpc-gateway` транслирует такой gRPC-стрим в непрерывный HTTP/1.1 или HTTP/2 ответ со следующими характеристиками:
1. **Chunked Transfer Encoding:** Заголовок `Transfer-Encoding: chunked` активируется автоматически.
2. **Разделители сообщений:** По умолчанию gRPC-Gateway сериализует каждое Protobuf-сообщение в отдельную JSON-строку, завершающуюся переводом строки `\n` (NDJSON — *Newline Delimited JSON*).
3. **Буферизация прокси:** Промежуточные обратные прокси (Nginx, Envoy, Cloudflare) по умолчанию буферизуют HTTP-ответы (`proxy_buffering on`). Чтобы стриминг доходил до браузера в реальном времени, шлюз должен отправлять заголовок `X-Accel-Buffering: no`.
4. **Сброс буфера (Flushing):** Обработчик шлюза выполняет проверку интерфейса `w.(http.Flusher)` и вызывает `flusher.Flush()` после каждого доставленного сообщения. Если контекст клиента прерывается (`r.Context().Done()`), gRPC-Gateway немедленно закрывает клиентский контекст gRPC-стрима.""",
    "step_by_step": [
        "Опишите структуру потокового события `Notification` с полями EventID, UserID, Payload и Timestamp.",
        "Реализуйте симулятор gRPC-сервера `NotificationServer` с методом потоковой генерации событий с проверкой `ctx.Done()`.",
        "Создайте HTTP-обработчик шлюза с проверкой `http.Flusher` и установкой заголовков потоковой передачи.",
        "Реализуйте стриминг сообщений в формате Newline-Delimited JSON (NDJSON) с принудительным сбросом буфера сокета."
    ],
    "code_blocks": [
        {
            "filename": "server_streaming_gateway.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"sync"
	"time"
)

type Notification struct {
	EventID   string    `json:"event_id"`
	UserID    string    `json:"user_id"`
	Payload   string    `json:"payload"`
	Timestamp time.Time `json:"timestamp"`
}

type NotificationServer struct{}

func (s *NotificationServer) StreamNotifications(ctx context.Context, userID string, out chan<- Notification) error {
	defer close(out)
	for i := 1; i <= 3; i++ {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(30 * time.Millisecond):
			out <- Notification{
				EventID:   fmt.Sprintf("evt-%03d", i),
				UserID:    userID,
				Payload:   fmt.Sprintf("Realtime alert #%d for user %s", i, userID),
				Timestamp: time.Now().UTC(),
			}
		}
	}
	return nil
}

func StreamNotificationsGatewayHandler(srv *NotificationServer) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		flusher, ok := w.(http.Flusher)
		if !ok {
			http.Error(w, "Streaming unsupported by response writer", http.StatusInternalServerError)
			return
		}

		userID := r.URL.Query().Get("user_id")
		if userID == "" {
			http.Error(w, "query param user_id is required", http.StatusBadRequest)
			return
		}

		w.Header().Set("Content-Type", "application/x-ndjson; charset=utf-8")
		w.Header().Set("Transfer-Encoding", "chunked")
		w.Header().Set("X-Accel-Buffering", "no")
		w.Header().Set("Cache-Control", "no-cache")
		w.WriteHeader(http.StatusOK)
		flusher.Flush()

		ch := make(chan Notification, 4)
		var wg sync.WaitGroup
		wg.Add(1)

		go func() {
			defer wg.Done()
			_ = srv.StreamNotifications(r.Context(), userID, ch)
		}()

		enc := json.NewEncoder(w)
		for notif := range ch {
			if err := enc.Encode(notif); err != nil {
				return
			}
			flusher.Flush()
		}
		wg.Wait()
	}
}

func main() {
	srv := &NotificationServer{}
	handler := StreamNotificationsGatewayHandler(srv)

	req := httptest.NewRequest(http.MethodGet, "/v1/notifications/stream?user_id=usr_42", nil)
	rec := httptest.NewRecorder()

	handler(rec, req)

	fmt.Println("=== HTTP CHUNKED STREAMING OUTPUT ===")
	fmt.Printf("HTTP Status:   %d\n", rec.Code)
	fmt.Printf("Content-Type:  %s\n", rec.Header().Get("Content-Type"))
	fmt.Printf("Raw Body:\n%s", rec.Body.String())
}
"""
        }
    ],
    "under_the_hood": "gRPC-Gateway использует `http.Flusher` для проталкивания каждого Protobuf-сообщения в сокет сразу после его получения из gRPC-стрима. Если клиент разрывает TCP-соединение, `r.Context()` входящего HTTP-запроса отменяется, что через внутренний `ClientStream` инициирует отправку HTTP/2 RST_STREAM фрейма на gRPC-бэкенд, предотвращая напрасную генерацию данных горутинами сервера.",
    "pitfalls": [
        "Отсутствие заголовка `X-Accel-Buffering: no` при размещении шлюза за обратным прокси Nginx: Nginx буферизует ответ размером до 4–8 КБ, из-за чего браузер не получает события в реальном времени.",
        "Забытый вызов `flusher.Flush()` после записи JSON чанка, что приводит к задержке данных во внутреннем буфере сокета Go runtime.",
        "Игнорирование контекста `r.Context().Done()` внутри серверной горутины, порождающее утечки горутин (Goroutine Leaks) при частых отключениях клиентов."
    ],
    "bigtech_interview": "В чем ключевые различия между NDJSON (Newline-Delimited JSON) и SSE (Server-Sent Events) при трансляции gRPC-стримов в веб-клиенты? NDJSON — это простой поток JSON-структур с разделителем `\\n`, требующий ручного разбора чанков на стороне JS (через `ReadableStreamDefaultReader`). SSE (`text/event-stream`) — стандартизированный W3C протокол с полями `event`, `data`, `id` и нативной поддержкой браузерного объекта `EventSource`, автоматически восстанавливающего TCP-сессию с заголовком `Last-Event-ID` при сетевых сбоях."
})

# Exercise 17
exercises.append({
    "num": 17,
    "title": "Протокол gRPC-Web: мост между браузером и gRPC",
    "task": "Браузерный JavaScript не имеет доступа к низкоуровневым HTTP/2 фреймам трейлеров (HTTP/2 trailers), которые необходимы для передачи gRPC статус-кодов. Изучите спецификацию протокола gRPC-Web, кодирующего трейлеры прямо в конец тела ответа. Объясните, почему gRPC-Web позволяет фронтенд-приложениям работать с gRPC напрямую.",
    "theory": r"""Почему gRPC не работает напрямую в браузере через стандартный `fetch()`?
1. **Проблема HTTP/2 Trailers:** В нативном gRPC статус завершения RPC (`grpc-status`, `grpc-message`, бинарные детали ошибок) передается в блоке **HTTP/2 Trailers** (HEADERS фрейм с флагом `END_STREAM`, следующий строго после всех DATA фреймов). Браузерные API исторически не предоставляли доступ к трейлерам в JS.
2. **Проблема бинарного управления соединениями:** Браузерная песочница не разрешает JS-коду управлять фреймами HTTP/2 на транспортном уровне сокета.

Решение: **Спецификация gRPC-Web**
В протоколе gRPC-Web статус-коды инкапсулируются прямо в **тело HTTP-ответа**:
- Каждый блок данных предваряется 5-байтным заголовком:
  - Байт 0: **Флаг типа** (`0x00` — сообщение protobuf, `0x80` — блок трейлеров).
  - Байты 1–4: Длина полезной нагрузки в формате Big-Endian uint32.
- Блок трейлеров (`0x80`) передается в самом конце тела ответа и содержит HTTP-заголовки в текстовом виде: `grpc-status: 0\r\ngrpc-message: OK\r\n`.
- Это позволяет фронтенду работать поверх обычного HTTP/1.1 Chunked Encoding или HTTP/2 без необходимости нативной поддержки trailers в браузере.""",
    "step_by_step": [
        "Определите константы протокола gRPC-Web: флаг данных (0x00) и флаг трейлеров (0x80).",
        "Создайте структуру фрейма `GrpcWebFrame` с флагом, длиной и полезной нагрузкой.",
        "Реализуйте функцию `EncodeGrpcWebFrame` для формирования 5-байтного заголовка фрейма.",
        "Реализуйте декодер `DecodeGrpcWebFrame` и покажите симуляцию ответа gRPC-Web с передачей трейлеров в теле ответа."
    ],
    "code_blocks": [
        {
            "filename": "grpc_web_framing.go",
            "lang": "go",
            "code": r"""package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
)

const (
	PayloadFrameFlag  byte = 0x00
	TrailersFrameFlag byte = 0x80
)

type GrpcWebFrame struct {
	Flag    byte
	Length  uint32
	Payload []byte
}

func EncodeGrpcWebFrame(flag byte, payload []byte) []byte {
	buf := make([]byte, 5+len(payload))
	buf[0] = flag
	binary.BigEndian.PutUint32(buf[1:5], uint32(len(payload)))
	copy(buf[5:], payload)
	return buf
}

func DecodeGrpcWebFrame(data []byte) (*GrpcWebFrame, error) {
	if len(data) < 5 {
		return nil, fmt.Errorf("buffer too short for gRPC-Web header: %d bytes", len(data))
	}
	flag := data[0]
	length := binary.BigEndian.Uint32(data[1:5])
	if uint32(len(data)-5) < length {
		return nil, fmt.Errorf("truncated frame: expected %d bytes, got %d", length, len(data)-5)
	}

	return &GrpcWebFrame{
		Flag:    flag,
		Length:  length,
		Payload: data[5 : 5+length],
	}, nil
}

func main() {
	protoPayload := []byte{0x08, 0x01, 0x12, 0x06, 'P', 'r', 'o', 'd', 'u', 'c', 't'}
	trailersPayload := []byte("grpc-status: 0\r\ngrpc-message: OK\r\n")

	var responseStream bytes.Buffer
	responseStream.Write(EncodeGrpcWebFrame(PayloadFrameFlag, protoPayload))
	responseStream.Write(EncodeGrpcWebFrame(TrailersFrameFlag, trailersPayload))

	fmt.Println("=== GRPC-WEB RESPONSE BODY SIMULATION ===")
	fmt.Printf("Total Encoded Bytes: %d\n", responseStream.Len())

	raw := responseStream.Bytes()
	frame1, err := DecodeGrpcWebFrame(raw)
	if err != nil {
		panic(err)
	}
	fmt.Printf("Frame 1: Flag=0x%02X (Data), Length=%d bytes, Payload=%v\n", frame1.Flag, frame1.Length, frame1.Payload)

	offset := 5 + frame1.Length
	frame2, err := DecodeGrpcWebFrame(raw[offset:])
	if err != nil {
		panic(err)
	}
	fmt.Printf("Frame 2: Flag=0x%02X (Trailers), Length=%d bytes\nTrailers Body:\n%s", frame2.Flag, frame2.Length, string(frame2.Payload))
}
"""
        }
    ],
    "under_the_hood": "gRPC-Web протокол поддерживает два Content-Type: `application/grpc-web+proto` (чистый бинарный фрейминг) и `application/grpc-web-text+proto` (где весь поток, включая 5-байтные заголовки, дополнительно оборачивается в Base64). Текстовый вариант использовался для старых браузеров (IE11/Safari), которые не поддерживали потоковое чтение бинарных ArrayBuffer через XMLHttpRequest.",
    "pitfalls": [
        "Попытка использовать Client-Streaming или Bidirectional Streaming через gRPC-Web в браузере: браузерный Fetch API не поддерживает потоковую отправку тела запроса в большинстве реализаций. gRPC-Web поддерживает только Unary и Server-Streaming вызовы.",
        "Парсинг gRPC-Web ответа обычным JSON-клиентом: тело является бинарным протоколом и при попытке десериализации как JSON завершится ошибкой синтаксиса."
    ],
    "bigtech_interview": "Почему в современных веб-приложениях gRPC-Web часто предпочитают классическому REST/JSON API? 1) Единая кодовая база контрактов: фронтенд компилирует TypeScript типы и методы напрямую из тех же `.proto` файлов, что и бэкенд, что исключает ошибки согласования типов; 2) Скорость бинарной сериализации и компактность передачи protobuf сообщений; 3) Встроенная поддержка потоковых обновлений (Server-Streaming) без необходимости поднимать отдельный WebSocket сервер."
})

# Exercise 18
exercises.append({
    "num": 18,
    "title": "Интеграция gRPC-Web прокси в Go-сервер (improbable-eng/grpc-web)",
    "task": "Подключите библиотеку `improbable-eng/grpc-web/go/grpcweb`. Оберните существующий `grpc.Server` в `grpcweb.WrapServer(grpcServer)`. Настройте единый HTTP-сервер, обрабатывающий как стандартные gRPC запросы, так и gRPC-Web запросы от веб-клиентов (`grpcweb.IsGrpcWebRequest(r)`).",
    "theory": r"""Для предоставления прямого доступа браузерным приложениям к gRPC-сервисам обычно используется один из двух архитектурных подходов:
1. **Внешний Ingress-прокси (Envoy):** В кластере поднимается Envoy с фильтром `envoy.filters.http.grpc_web`.
2. **Встроенный In-Process Go-прокси:** Использование библиотеки `github.com/improbable-eng/grpc-web/go/grpcweb`.

Преимущество in-process решения:
- Отсутствие дополнительного сетевого хопа между шлюзом и сервисом (Zero Network Hop).
- Упрощенное локальное окружение и монолитный деплой в Docker-контейнер без необходимости настройки конфигураций Envoy.

Библиотека `grpcweb.WrapServer(grpcServer)` оборачивает стандартный `*grpc.Server` в `http.Handler`, который:
- Перехватывает запросы с заголовком `Content-Type: application/grpc-web*`.
- Читает тело с 5-байтным фреймингом.
- Передает распакованное сообщение в метод gRPC-сервера.
- Перехватывает возвращаемые трейлеры и сериализует их в финальный `0x80` фрейм HTTP-ответа.""",
    "step_by_step": [
        "Создайте структуру gRPC-сервиса `OrderManagementService` с реализацией бизнес-метода.",
        "Реализуйте функцию-предикат `IsGrpcWebRequest(r *http.Request) bool` для проверки Content-Type.",
        "Реализуйте мультиплексирующий middleware `GrpcWebMuxHandler`, разделяющий трафик на нативный gRPC (HTTP/2), браузерный gRPC-Web и стандартный REST HTTP.",
        "Протестируйте обработку запроса каждого типа через `httptest`."
    ],
    "code_blocks": [
        {
            "filename": "grpcweb_proxy_server.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

type OrderManagementServer struct{}

func (s *OrderManagementServer) GetOrderStatus(ctx context.Context, orderID string) (string, error) {
	if orderID == "" {
		return "", status.Error(codes.InvalidArgument, "orderID cannot be empty")
	}
	return "STATUS_DELIVERED", nil
}

func IsGrpcWebRequest(r *http.Request) bool {
	ct := r.Header.Get("Content-Type")
	return strings.HasPrefix(ct, "application/grpc-web") || strings.HasPrefix(ct, "application/grpc-web-text")
}

func GrpcWebMuxHandler(grpcServer *grpc.Server, standardHTTP http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if IsGrpcWebRequest(r) {
			w.Header().Set("Content-Type", "application/grpc-web+proto")
			w.Header().Set("Access-Control-Allow-Origin", "*")
			w.WriteHeader(http.StatusOK)
			// Симуляция ответа grpcweb.WrapServer: данные фрейма + трейлеры со статусом OK
			_, _ = w.Write([]byte{0x00, 0x00, 0x00, 0x00, 0x04, 'D', 'O', 'N', 'E'})
			_, _ = w.Write([]byte{0x80, 0x00, 0x00, 0x00, 0x1E})
			_, _ = w.Write([]byte("grpc-status: 0\r\ngrpc-message: OK\r\n"))
			return
		}

		if r.ProtoMajor == 2 && strings.HasPrefix(r.Header.Get("Content-Type"), "application/grpc") {
			grpcServer.ServeHTTP(w, r)
			return
		}

		standardHTTP.ServeHTTP(w, r)
	})
}

func main() {
	grpcServer := grpc.NewServer()
	restMux := http.NewServeMux()
	restMux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("HEALTHY"))
	})

	handler := GrpcWebMuxHandler(grpcServer, restMux)

	// Тест gRPC-Web запроса
	reqWeb := httptest.NewRequest(http.MethodPost, "/OrderService/GetOrderStatus", nil)
	reqWeb.Header.Set("Content-Type", "application/grpc-web+proto")
	recWeb := httptest.NewRecorder()
	handler.ServeHTTP(recWeb, reqWeb)

	fmt.Println("=== GRPC-WEB DISPATCH TEST ===")
	fmt.Printf("Status:       %d\n", recWeb.Code)
	fmt.Printf("Content-Type: %s\n", recWeb.Header().Get("Content-Type"))
	fmt.Printf("Body Length:  %d bytes\n", recWeb.Body.Len())

	// Тест обычного REST запроса
	reqREST := httptest.NewRequest(http.MethodGet, "/healthz", nil)
	recREST := httptest.NewRecorder()
	handler.ServeHTTP(recREST, reqREST)

	fmt.Println("\n=== REST DISPATCH TEST ===")
	fmt.Printf("Status:       %d\n", recREST.Code)
	fmt.Printf("Body:         %s\n", recREST.Body.String())
}
"""
        }
    ],
    "under_the_hood": "При использовании `grpcweb.WrapServer` библиотека перехватывает вызовы низкоуровневого `http.ResponseWriter`. Когда gRPC-обработчик записывает трейлеры через `grpc.SetTrailer()`, обертка сериализует их в текстовые HTTP заголовки и выводит в виде завершающего фрейма с флагом `0x80`, после чего закрывает HTTP-соединение.",
    "pitfalls": [
        "Конфликты с middleware, читающими тело запроса `r.Body`: потоковые gRPC-Web данные нельзя считывать повторно (`io.ReadAll` опустошает `r.Body`), если тело не было скопировано или буферизовано.",
        "Забытая поддержка CORS preflight запросов (OPTIONS): браузер не отправит gRPC-Web POST запрос, если на сервере не настроена обработка preflight заголовков."
    ],
    "bigtech_interview": "В каких архитектурных сценариях предпочтительнее внешний Envoy proxy с фильтром grpc_web, а в каких — in-process grpcweb Go-обертка? Envoy предпочтителен в крупных микросервисных средах (Kubernetes Service Mesh), так как он централизует CORS, mTLS, TLS termination, Rate Limiting и Observability, снимая нагрузку с Go-рантайма. In-process обертка на Go идеальна для автономных сервисов, десктопных утилит, локальной разработки и сред с жесткими ограничениями на сетевые задержки (Zero Hop Architecture)."
})

# Exercise 19
exercises.append({
    "num": 19,
    "title": "Настройка CORS для gRPC-Web и REST-эндпоинтов",
    "task": "Браузерные запросы с других доменов блокируются политикой Same-Origin Policy. Реализуйте CORS middleware для поддержки предварительных запросов `OPTIONS`: настройте заголовки `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers` (включая `x-grpc-web`, `content-type`, `x-user-agent`) и `Access-Control-Expose-Headers` (включая `grpc-status`, `grpc-message`).",
    "theory": r"""При выполнении кросс-доменных запросов из браузера к gRPC-Web или REST API шлюза вступают в силу правила Same-Origin Policy (SOP).

Критически важные нюансы конфигурации CORS для gRPC-Web:
1. **Кастомные заголовки запроса (`Access-Control-Allow-Headers`):** Браузерный gRPC-Web клиент всегда отправляет специфические заголовки: `x-grpc-web`, `x-user-agent`, `content-type` (`application/grpc-web+proto`). Если они не перечислены в `Allow-Headers`, браузер блокирует preflight запрос.
2. **Экспортируемые заголовки ответа (`Access-Control-Expose-Headers`):** По умолчанию браузерный JavaScript видит только базовые заголовки ответа (`Content-Type`, `Cache-Control` и др.). Все статусы gRPC передаются в `grpc-status`, `grpc-message` и `grpc-status-details-bin`. Если их не добавить в `Access-Control-Expose-Headers`, фронтенд посчитает любой запрос завершившимся с неизвестной сетевой ошибкой (UNKNOWN), даже если HTTP статус был 200 OK!""",
    "step_by_step": [
        "Создайте структуру конфигурации `CORSOptions` с перечнем разрешенных и экспортируемых заголовков.",
        "Сформируйте конфигурацию по умолчанию `DefaultGrpcWebCORSOptions`.",
        "Реализуйте middleware `CORSMiddleware`, перехватывающий запросы с методом `OPTIONS` и возвращающий HTTP 204 No Content.",
        "Проверьте выставление заголовков `Access-Control-Expose-Headers` для передачи gRPC статусов браузеру."
    ],
    "code_blocks": [
        {
            "filename": "cors_grpcweb_middleware.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
)

type CORSOptions struct {
	AllowedOrigins []string
	AllowedMethods []string
	AllowedHeaders []string
	ExposedHeaders []string
	MaxAgeSeconds  int
}

func DefaultGrpcWebCORSOptions() CORSOptions {
	return CORSOptions{
		AllowedOrigins: []string{"*"},
		AllowedMethods: []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowedHeaders: []string{
			"Keep-Alive",
			"User-Agent",
			"X-Grpc-Web",
			"Content-Type",
			"Authorization",
			"X-User-Agent",
			"X-Request-ID",
		},
		ExposedHeaders: []string{
			"grpc-status",
			"grpc-message",
			"grpc-status-details-bin",
			"X-Request-ID",
		},
		MaxAgeSeconds: 86400,
	}
}

func CORSMiddleware(opts CORSOptions, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")
		if origin == "" {
			next.ServeHTTP(w, r)
			return
		}

		w.Header().Set("Access-Control-Allow-Origin", strings.Join(opts.AllowedOrigins, ", "))
		w.Header().Set("Access-Control-Allow-Methods", strings.Join(opts.AllowedMethods, ", "))
		w.Header().Set("Access-Control-Allow-Headers", strings.Join(opts.AllowedHeaders, ", "))
		w.Header().Set("Access-Control-Expose-Headers", strings.Join(opts.ExposedHeaders, ", "))
		w.Header().Set("Access-Control-Max-Age", fmt.Sprintf("%d", opts.MaxAgeSeconds))

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}

		next.ServeHTTP(w, r)
	})
}

func main() {
	opts := DefaultGrpcWebCORSOptions()
	dummyHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("grpc-status", "0")
		w.Header().Set("grpc-message", "OK")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("SUCCESS"))
	})

	corsHandler := CORSMiddleware(opts, dummyHandler)

	// Тест Preflight OPTIONS запроса
	optReq := httptest.NewRequest(http.MethodOptions, "/v1/orders", nil)
	optReq.Header.Set("Origin", "https://frontend.company.com")
	optRec := httptest.NewRecorder()
	corsHandler.ServeHTTP(optRec, optReq)

	fmt.Println("=== PREFLIGHT OPTIONS TEST ===")
	fmt.Printf("Status:             %d\n", optRec.Code)
	fmt.Printf("Expose-Headers:     %s\n", optRec.Header().Get("Access-Control-Expose-Headers"))
	fmt.Printf("Allow-Headers:      %s\n", optRec.Header().Get("Access-Control-Allow-Headers"))

	// Тест обычного POST запроса
	postReq := httptest.NewRequest(http.MethodPost, "/v1/orders", nil)
	postReq.Header.Set("Origin", "https://frontend.company.com")
	postRec := httptest.NewRecorder()
	corsHandler.ServeHTTP(postRec, postReq)

	fmt.Println("\n=== ACTUAL REQUEST TEST ===")
	fmt.Printf("Status:             %d\n", postRec.Code)
	fmt.Printf("grpc-status Header: %s\n", postRec.Header().Get("grpc-status"))
}
"""
        }
    ],
    "under_the_hood": "Браузер производит строгую фильтрацию заголовков ответа в соответствии со спецификацией CORS-W3C. Если заголовок `grpc-status` не перечислен в `Access-Control-Expose-Headers`, JavaScript движок браузера скрывает его из возвращаемого объекта `Headers`. В результате клиентская библиотека gRPC-Web не может определить результат выполнения операции.",
    "pitfalls": [
        "Использование `Access-Control-Allow-Origin: *` в сочетании с `Access-Control-Allow-Credentials: true`: спецификация W3C CORS явно запрещает использовать wildcard '*' при отправке авторизационных cookies или сертификатов.",
        "Забытый заголовок `grpc-status-details-bin` в `Expose-Headers`: приводит к тому, что богатые Protobuf-ошибки (`google.rpc.Status` с details) не доходят до фронтенда."
    ],
    "bigtech_interview": "Как безопасно настроить динамический CORS в корпоративной среде с десятками поддоменов компании? Вместо небезопасного wildcard '*' шлюз должен считывать заголовок `Origin` из входящего запроса, валидировать его по строгому регулярному выражению доверенных доменов компании (например `^https://[a-z0-9-]+\\.company\\.internal$`), при совпадении зеркалировать этот Origin в заголовок `Access-Control-Allow-Origin` и обязательно добавлять заголовок `Vary: Origin`, чтобы промежуточные кэши и CDN не отдавали закэшированный чужой Origin другим пользователям."
})

# Exercise 20
exercises.append({
    "num": 20,
    "title": "Декларативная валидация запросов с protovalidate",
    "task": "Подключите библиотеку валидации `bufbuild/protovalidate-go`. Добавьте правила валидации прямо в `.proto` файл: `string email = 1 [(buf.validate.field).string.email = true]; int32 age = 2 [(buf.validate.field).int32.gte = 18];`. Напишите gRPC-интерцептор, автоматически валидирующий входящие сообщения и возвращающий `codes.InvalidArgument` при нарушении правил.",
    "theory": r"""Традиционная ручная валидация аргументов в каждом методе сервиса приводит к дублированию кода и расхождению бизнес-правил между бэкендом и клиентами.

Современный индустриальный стандарт в Protobuf — **`bufbuild/protovalidate`** (преемник `protoc-gen-validate`):
1. **Декларативные правила в контракте `.proto`:**
   ```protobuf
   import "buf/validate/validate.proto";

   message CreateUserRequest {
     string email = 1 [(buf.validate.field).string.email = true];
     int32 age = 2 [(buf.validate.field).int32 = {gte: 18, lte: 120}];
   }
   ```
2. **CEL (Common Expression Language):** Правила валидируются с помощью быстрого интерпретатора выражений CEL от Google прямо в рантайме Go.
3. **Единый gRPC-интерцептор:** Перехватывает все входящие `req` до передачи управления бизнес-логике. Если контракт нарушен, интерцептор прерывает цепочку и возвращает статус `codes.InvalidArgument` со структурированным описанием нарушенных полей (`BadRequest_FieldViolation`).""",
    "step_by_step": [
        "Определите интерфейс `Validatable` для сущностей, поддерживающих декларативную проверку.",
        "Создайте структуру `UserRegistrationRequest` с проверкой корректности email, возраста и роли пользователя.",
        "Реализуйте серверный gRPC Unary интерцептор `ProtovalidateServerInterceptor`, автоматически вызывающий проверку контракта.",
        "Продемонстрируйте возврат структурированной gRPC ошибки `codes.InvalidArgument` при невалидных входных данных."
    ],
    "code_blocks": [
        {
            "filename": "protovalidate_interceptor.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"errors"
	"fmt"
	"net/mail"
	"strings"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

type Validatable interface {
	Validate() error
}

type UserRegistrationRequest struct {
	Email string `json:"email"`
	Age   int32  `json:"age"`
	Role  string `json:"role"`
}

func (r *UserRegistrationRequest) Validate() error {
	var errs []string
	if _, err := mail.ParseAddress(r.Email); err != nil {
		errs = append(errs, "field 'email' must be a valid email address")
	}
	if r.Age < 18 || r.Age > 120 {
		errs = append(errs, "field 'age' must be between 18 and 120")
	}
	if r.Role != "admin" && r.Role != "member" {
		errs = append(errs, "field 'role' must be either 'admin' or 'member'")
	}
	if len(errs) > 0 {
		return errors.New(strings.Join(errs, "; "))
	}
	return nil
}

func ProtovalidateServerInterceptor() grpc.UnaryServerInterceptor {
	return func(
		ctx context.Context,
		req any,
		info *grpc.UnaryServerInfo,
		handler grpc.UnaryHandler,
	) (any, error) {
		if v, ok := req.(Validatable); ok {
			if err := v.Validate(); err != nil {
				return nil, status.Errorf(codes.InvalidArgument, "contract validation failed: %s", err.Error())
			}
		}
		return handler(ctx, req)
	}
}

func main() {
	interceptor := ProtovalidateServerInterceptor()
	dummyHandler := func(ctx context.Context, req any) (any, error) {
		return "USER_REGISTERED_SUCCESS", nil
	}

	fmt.Println("=== TEST 1: VALID REQUEST ===")
	validReq := &UserRegistrationRequest{Email: "techlead@company.com", Age: 30, Role: "admin"}
	res, err := interceptor(context.Background(), validReq, &grpc.UnaryServerInfo{}, dummyHandler)
	fmt.Printf("Result: %v, Error: %v\n", res, err)

	fmt.Println("\n=== TEST 2: INVALID REQUEST ===")
	invalidReq := &UserRegistrationRequest{Email: "invalid-email-string", Age: 14, Role: "root"}
	_, err = interceptor(context.Background(), invalidReq, &grpc.UnaryServerInfo{}, dummyHandler)
	st, _ := status.FromError(err)
	fmt.Printf("gRPC Status Code: %s\n", st.Code())
	fmt.Printf("gRPC Message:     %s\n", st.Message())
}
"""
        }
    ],
    "under_the_hood": "Библиотека `bufbuild/protovalidate-go` во время компиляции или первого запуска парсит Protobuf дескрипторы и компилирует аннотации правил в байткод Common Expression Language (CEL). При выполнении интерцептора CEL программа вычисляется за микросекунды на стек-машине без использования тяжелой рефлексии Go.",
    "pitfalls": [
        "Отсутствие детализации ошибок (`FieldViolations`): возвращение клиенту только общего текста 'validation error' без указания конкретного имени поля и причины нарушения заставляет клиентов заниматься ручным дебагом.",
        "Выполнение ресурсоемких сетевых проверок (проверка существования записи в БД) внутри правил Protobuf: Protobuf валидация должна быть строго статической и бессерверной."
    ],
    "bigtech_interview": "Как вернуть ошибки валидации по стандарту Google Cloud APIs, чтобы gRPC-Gateway автоматически упаковал их в богатый HTTP JSON? Для этого используется protobuf-тип `google.rpc.BadRequest`. Сервер создает объект `BadRequest`, наполняет его элементами `BadRequest_FieldViolation{Field: 'email', Description: '...'}` и прикрепляет к статусу вызовом `st.WithDetails(badRequest)`. Шлюз gRPC-Gateway автоматически транслирует эти details в поле `details: [...]` JSON-ответа с HTTP статусом 400 Bad Request."
})

# Exercise 21
exercises.append({
    "num": 21,
    "title": "Линтинг и проверка обратной совместимости с Buf CLI",
    "task": "Настройте утилиту `buf`: создайте конфигурационный файл `buf.yaml`. Выполните команду `buf lint` для проверки соответствия кодстайлу API. Выполните проверку обратной совместимости `buf breaking --against \".git#branch=main\"` и продемонстрируйте, как инструмент блокирует опасные изменения схемы (удаление полей, смена номеров тегов).",
    "theory": r"""Современный тулинг **Buf CLI** (`buf`) вытеснил устаревший `protoc` в промышленной Go-разработке благодаря стандартизации и строгой валидации:
1. **`buf lint`:** Проверяет оформление схем: именование пакетов (наличие версии v1, v2), snake_case для имен полей, CamelCase для сообщений, наличие описаний RPC методов.
2. **`buf breaking`:** Автоматически выявляет нарушения бинарной и JSON обратной совместимости относительно git-ветки (`main`) или последнего стабильного релиза.

Критически опасные изменения контрактов:
- **Удаление поля или сдвиг номеров тегов:** Нарушает бинарную десериализацию старых клиентов.
- **Изменение типа поля:** Например `int32` -> `string` делает декодирование невозможным на аппаратном уровне.
- **Переименование поля:** В бинарном Protobuf имена не хранятся, но в REST JSON (`grpc-gateway`) смена имени поля мгновенно ломает всех фронтенд и REST клиентов!
- **Правило `reserved`:** При удалении поля его номер и имя обязаны помечаться как `reserved 3, "status";`, гарантируя, что другой инженер не использует этот тег в будущем.""",
    "step_by_step": [
        "Создайте модель описания поля контракта `ProtoField` с тегом, именем и типом данных.",
        "Реализуйте детектор критических изменений схемы `BreakingChangeDetector`.",
        "Запрограммируйте правила выявления удаленных тегов без reserved, изменения типов и смещения номеров тегов.",
        "Продемонстрируйте запуск детектора на двух версиях схемы и вывод списка нарушений."
    ],
    "code_blocks": [
        {
            "filename": "buf_breaking_detector.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
)

type ProtoField struct {
	Tag  int
	Name string
	Type string
}

type BreakingChangeDetector struct{}

func (d *BreakingChangeDetector) CheckBreakingChanges(baseSchema, targetSchema []ProtoField) []string {
	var violations []string

	baseByTag := make(map[int]ProtoField)
	for _, f := range baseSchema {
		baseByTag[f.Tag] = f
	}

	targetByTag := make(map[int]ProtoField)
	for _, f := range targetSchema {
		targetByTag[f.Tag] = f
	}

	// 1. Проверка удаленных тегов
	for tag, oldF := range baseByTag {
		if newF, exists := targetByTag[tag]; !exists {
			violations = append(violations, fmt.Sprintf("RULE_FIELD_NO_DELETE: Tag %d (%s) was removed without 'reserved'", tag, oldF.Name))
		} else if oldF.Type != newF.Type {
			violations = append(violations, fmt.Sprintf("RULE_WIRE_TYPE_CHANGE: Tag %d changed type from %s to %s", tag, oldF.Type, newF.Type))
		}
	}

	// 2. Проверка смещения тегов существующих полей
	baseByName := make(map[string]ProtoField)
	for _, f := range baseSchema {
		baseByName[f.Name] = f
	}
	for _, newF := range targetSchema {
		if oldF, exists := baseByName[newF.Name]; exists && oldF.Tag != newF.Tag {
			violations = append(violations, fmt.Sprintf("RULE_FIELD_TAG_CHANGED: Field '%s' changed tag from %d to %d", newF.Name, oldF.Tag, newF.Tag))
		}
	}

	return violations
}

func main() {
	v1Main := []ProtoField{
		{Tag: 1, Name: "order_id", Type: "string"},
		{Tag: 2, Name: "price_cents", Type: "int64"},
		{Tag: 3, Name: "status", Type: "string"},
	}

	v2DevBranch := []ProtoField{
		{Tag: 1, Name: "order_id", Type: "string"},
		{Tag: 2, Name: "price_cents", Type: "double"}, // Нарушение: смена типа int64 -> double
		{Tag: 4, Name: "status", Type: "string"},       // Нарушение: удаление тега 3 и сдвиг тега поля status на 4
	}

	detector := &BreakingChangeDetector{}
	issues := detector.CheckBreakingChanges(v1Main, v2DevBranch)

	fmt.Println("=== BUF BREAKING CHANGE ANALYSIS ===")
	fmt.Printf("Total Breaking Changes Detected: %d\n", len(issues))
	for i, issue := range issues {
		fmt.Printf(" [%d] %s\n", i+1, issue)
	}
}
"""
        }
    ],
    "under_the_hood": "Buf CLI компилирует `.proto` файлы в универсальный бинарный Image (представление `FileDescriptorSet`). При сравнении двух версий схемы Buf строит граф типов и сверяет свойства узлов по правилам категорий обратной совместимости (WIRE, WIRE_JSON, PACKAGE, FILE), предотвращая повреждение сериализованных данных.",
    "pitfalls": [
        "Игнорирование категории `WIRE_JSON` при использовании gRPC-Gateway: переименование поля со `status` на `order_status` бинарно совместимо, но ломает всех внешних REST клиентов.",
        "Отсутствие проверки `buf breaking` в CI/CD пайплайне перед мерджем Pull Request, позволяющее разработчикам незаметно сломать обратную совместимость схемы."
    ],
    "bigtech_interview": "Каковы 4 основные категории проверки обратной совместимости в Buf CLI (FILE, PACKAGE, WIRE, WIRE_JSON)? WIRE проверяет сохранение бинарной совместимости Protobuf (номера тегов, типы данных). WIRE_JSON дополнительно гарантирует неизменность строковых имен полей и названий enum, критичных для JSON-клиентов gRPC-Gateway. PACKAGE запрещает удаление или перемещение типов между файлами одного пакета. FILE — самый строгий уровень, требующий неизменности путей к файлам и номеров строк."
})

# Exercise 22
exercises.append({
    "num": 22,
    "title": "Паттерн FieldMask для частичного обновления сущностей (PATCH)",
    "task": "Реализуйте идиоматичный HTTP `PATCH` метод для обновления профиля пользователя: используйте стандартный тип `google.protobuf.FieldMask`. Покажите, как клиент передает список обновляемых полей (`paths: [\"email\", \"bio\"]`), а сервер обновляет в базе данных только указанные колонки, игнорируя остальные.",
    "theory": r"""При реализации HTTP `PATCH` в Protobuf возникает фундаментальная проблема:
В спецификации Proto3 отсутствует значение `null`. Пустая строка `""` или число `0` могут означать как «клиент хочет очистить поле», так и «клиент просто не передал это поле в запросе».

Решение: **Стандартный паттерн `google.protobuf.FieldMask`**
1. В `.proto` запросе объявляется маска:
   ```protobuf
   message UpdateUserRequest {
     User user = 1;
     google.protobuf.FieldMask update_mask = 2;
   }
   ```
2. В REST маппинге аннотируется метод:
   ```protobuf
   option (google.api.http) = {
     patch: "/v1/users/{user.id}"
     body: "user"
   };
   ```
3. Клиент отправляет: `PATCH /v1/users/123?updateMask=email,bio` с телом `{"email": "new@mail.com", "bio": "Staff Go Engineer"}`.
4. Сервер парсит `updateMask` и генерирует частичный SQL запрос: `UPDATE users SET email = $1, bio = $2 WHERE id = $3`, не затрагивая остальные колонки.""",
    "step_by_step": [
        "Создайте сущность `UserProfile` с набором изменяемых и неизменяемых полей.",
        "Реализуйте структуру `FieldMask` со списком путей обновления `Paths`.",
        "Напишите функцию `ApplyFieldMask`, обновляющую только указанные атрибуты с валидацией неизменяемых полей.",
        "Продемонстрируйте обновление указанных полей и сохранение неизменности остальных атрибутов."
    ],
    "code_blocks": [
        {
            "filename": "field_mask_patch.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"strings"
)

type UserProfile struct {
	ID        string
	Username  string
	Email     string
	Bio       string
	AvatarURL string
}

type FieldMask struct {
	Paths []string
}

type UpdateUserProfileRequest struct {
	Profile    UserProfile
	UpdateMask *FieldMask
}

func ApplyFieldMask(target *UserProfile, src UserProfile, mask *FieldMask) error {
	if mask == nil || len(mask.Paths) == 0 {
		*target = src
		return nil
	}

	for _, rawPath := range mask.Paths {
		path := strings.TrimSpace(strings.ToLower(rawPath))
		switch path {
		case "email":
			target.Email = src.Email
		case "bio":
			target.Bio = src.Bio
		case "avatar_url", "avatarurl":
			target.AvatarURL = src.AvatarURL
		case "username":
			return fmt.Errorf("field 'username' is immutable and cannot be updated")
		default:
			return fmt.Errorf("unknown or unsupported field path in mask: %s", rawPath)
		}
	}
	return nil
}

func main() {
	currentRecord := UserProfile{
		ID:        "usr-100",
		Username:  "antigravity_lead",
		Email:     "old@company.com",
		Bio:       "Senior Go Engineer",
		AvatarURL: "https://cdn.company.com/old_avatar.png",
	}

	patchReq := UpdateUserProfileRequest{
		Profile: UserProfile{
			Email:     "principal@company.com",
			Bio:       "Principal Distributed Systems Architect",
			AvatarURL: "https://cdn.company.com/hacker.png", // Не должно обновиться!
		},
		UpdateMask: &FieldMask{
			Paths: []string{"email", "bio"},
		},
	}

	err := ApplyFieldMask(&currentRecord, patchReq.Profile, patchReq.UpdateMask)
	if err != nil {
		panic(err)
	}

	fmt.Println("=== PARTIAL UPDATE RESULT (PATCH) ===")
	fmt.Printf("User ID:    %s\n", currentRecord.ID)
	fmt.Printf("Username:   %s (Immutable)\n", currentRecord.Username)
	fmt.Printf("Email:      %s (Updated!)\n", currentRecord.Email)
	fmt.Printf("Bio:        %s (Updated!)\n", currentRecord.Bio)
	fmt.Printf("Avatar URL: %s (Unchanged!)\n", currentRecord.AvatarURL)
}
"""
        }
    ],
    "under_the_hood": "gRPC-Gateway транслирует query-параметр URL вида `?updateMask=email,bio` непосредственно в экземпляр `fieldmaskpb.FieldMask`. Внутри сгенерированного кода Go поля `Paths` нормализуются в нижний регистр snake_case для однозначного сопоставления с именами колонок СУБД.",
    "pitfalls": [
        "Обновление сущности целиком при пустом `FieldMask`: если клиент забыл передать маску, неконтролируемое обновление может затереть все неуказанные поля значениями по умолчанию (`\"\"`, `0`).",
        "Отсутствие проверки вложенных путей: для глубоких структур (например `user.address.city`) маска должна рекурсивно проверять корректность дочерних узлов."
    ],
    "bigtech_interview": "Как транслировать `google.protobuf.FieldMask` в безопасный SQL-запрос `UPDATE` без риска SQL-инъекций? Необходимо создать статический whitelist разрешенных путей маски, отображаемых на проверенные имена колонок: `map[string]string{'email': 'email', 'avatar_url': 'avatar_url'}`. При получении маски сервер фильтрует входные пути по мапе и использует параметризованный SQL-билдер (`squirrel` или `pgx`), подставляя позиционные параметры `$1, $2`, полностью исключая конкатенацию сырых строк."
})

# Exercise 23
exercises.append({
    "num": 23,
    "title": "Работа с полиморфными данными через google.protobuf.Any",
    "task": "Спроектируйте расширяемый эндпоинт аудита событий: поле `details` имеет тип `google.protobuf.Any`. Напишите код сериализации произвольных структур в `Any` и их распаковки на стороне шлюза с проверкой зарегистрированных URL типов.",
    "theory": r"""В распределенных микросервисах часто требуется передавать гетерогенные и полиморфные структуры данных в рамках единого контракта (системы аудита, webhook payloads, шины событий).

Для этого используется стандартный тип **`google.protobuf.Any`**:
1. Структура `Any` содержит два поля:
   - `string type_url = 1;` — глобально уникальный URI типа в формате `type.googleapis.com/full.package.MessageName`.
   - `bytes value = 2;` — бинарный сериализованный Protobuf payload.
2. В JSON-представлении (`grpc-gateway`) поле `Any` транслируется в нативный JSON-объект со специальным ключом `"@type": "type.googleapis.com/..."`, инкапсулируя поля вложенного объекта.
3. В Go для безопасной работы используются функции:
   - `anypb.New(msg)` — упаковка структуры в `*anypb.Any`.
   - `any.UnmarshalTo(target)` — безопасная распаковка с валидацией совпадения `TypeURL`.""",
    "step_by_step": [
        "Создайте структуру `AnyRecord` с полями `TypeURL` и `Value`.",
        "Опишите событие аудита `AuditLogEntry` и типы полезных нагрузок `UserCreatedPayload` и `OrderPlacedPayload`.",
        "Реализуйте упаковщик `PackAny` и динамический диспетчер событий `DispatchAuditLog`.",
        "Продемонстрируйте безопасную распаковку полиморфного события по TypeURL."
    ],
    "code_blocks": [
        {
            "filename": "protobuf_any_polymorphism.go",
            "lang": "go",
            "code": r"""package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

type AnyRecord struct {
	TypeURL string `json:"@type"`
	Value   []byte `json:"value"`
}

type AuditLogEntry struct {
	EventID   string    `json:"event_id"`
	Action    string    `json:"action"`
	Timestamp int64     `json:"timestamp"`
	Payload   AnyRecord `json:"payload"`
}

type UserCreatedPayload struct {
	UserID string `json:"user_id"`
	Email  string `json:"email"`
}

type OrderPlacedPayload struct {
	OrderID     string  `json:"order_id"`
	TotalAmount float64 `json:"total_amount"`
}

func PackAny(typeURL string, data any) (AnyRecord, error) {
	bytes, err := json.Marshal(data)
	if err != nil {
		return AnyRecord{}, err
	}
	return AnyRecord{
		TypeURL: typeURL,
		Value:   bytes,
	}, nil
}

func DispatchAuditLog(entry AuditLogEntry) error {
	switch {
	case strings.HasSuffix(entry.Payload.TypeURL, "UserCreatedPayload"):
		var p UserCreatedPayload
		if err := json.Unmarshal(entry.Payload.Value, &p); err != nil {
			return err
		}
		fmt.Printf("[AUDIT DISPATCH] User Created -> UserID: %s, Email: %s\n", p.UserID, p.Email)

	case strings.HasSuffix(entry.Payload.TypeURL, "OrderPlacedPayload"):
		var p OrderPlacedPayload
		if err := json.Unmarshal(entry.Payload.Value, &p); err != nil {
			return err
		}
		fmt.Printf("[AUDIT DISPATCH] Order Placed -> OrderID: %s, Amount: $%.2f\n", p.OrderID, p.TotalAmount)

	default:
		return fmt.Errorf("unsupported or unregistered type URL: %s", entry.Payload.TypeURL)
	}
	return nil
}

func main() {
	userEvent, _ := PackAny("type.googleapis.com/company.events.UserCreatedPayload", UserCreatedPayload{
		UserID: "usr_lead_99",
		Email:  "architect@bigtech.ru",
	})

	entry := AuditLogEntry{
		EventID:   "evt-audit-1001",
		Action:    "USER_SIGNUP",
		Timestamp: 1700000000,
		Payload:   userEvent,
	}

	fmt.Println("=== DISPATCHING POLYMORPHIC PROTOBUF ANY EVENT ===")
	if err := DispatchAuditLog(entry); err != nil {
		panic(err)
	}
}
"""
        }
    ],
    "under_the_hood": "При сериализации в JSON gRPC-Gateway запрашивает глобальный реестр типов `protoregistry.GlobalTypes`. Если переданный `TypeURL` зарегистрирован в реестре приложения, маршалер разворачивает сообщение в полноценный JSON-объект. Если тип отсутствует, возвращается ошибка десериализации неизвестного типа.",
    "pitfalls": [
        "Неконтролируемая распаковка произвольных типов: попытка распаковать `Any` без валидации префикса домена в `TypeURL` может привести к выполнению нежелательного кода или исчерпанию ресурсов.",
        "Утечки памяти при передаче тяжелых вложенных `Any` структур через очереди сообщений без лимитов на размер сообщений."
    ],
    "bigtech_interview": "В чем отличие `google.protobuf.Any` от объединения `oneof` в Protobuf, и когда что следует использовать? `oneof` — это закрытый полиморфизм (Sum Type): все возможные варианты строго перечислены в схеме во время компиляции. Он эффективнее по памяти и дает типобезопасность на этапе сборки. `google.protobuf.Any` — это открытый полиморфизм: типы могут добавляться новыми модулями и плагинами динамически без обновления базового `.proto` файла, что незаменимо для платформ аудита и шин событий общего назначения."
})

# Exercise 24
exercises.append({
    "num": 24,
    "title": "Загрузка и выгрузка бинарных файлов через шлюз (google.api.HttpBody)",
    "task": "Спроектируйте метод загрузки аватара пользователя. Настройте gRPC-Gateway для приема бинарного потока или `multipart/form-data`: используйте тип `google.api.HttpBody` для прозрачной передачи потока байтов напрямую в gRPC-сервер без Base64-кодирования в JSON.",
    "theory": r"""Передача бинарных файлов через классический JSON REST API требует кодирования в Base64. Это приводит к:
1. Увеличению объема сетевого трафика на **~33%**.
2. Высокой нагрузке на сборщик мусора (аллокация миллионов байтовых массивов и строк).

Решение: **Стандартный тип `google.api.HttpBody`**
В Google API экосистеме тип `google.api.HttpBody` обрабатывается шлюзом gRPC-Gateway особым образом:
- **Запрос:** Если метод принимает `google.api.HttpBody` с аннотацией `body: "*"`, gRPC-Gateway не пытается парсить тело как JSON. Он считывает входящий сырой поток байтов напрямую в поле `Data []byte`, а значение HTTP заголовка `Content-Type` помещает в `ContentType string`.
- **Ответ:** Если метод возвращает `google.api.HttpBody`, шлюз устанавливает HTTP заголовок `Content-Type` из структуры и пишет `Data []byte` прямо в сокет ответа.
- Это обеспечивает прозрачную потоковую передачу бинарных файлов без оверхеда JSON.""",
    "step_by_step": [
        "Создайте модель `HttpBody` с полями `ContentType` и `Data []byte`.",
        "Реализуйте сервис `FileStorageService` с проверкой допустимых MIME-типов.",
        "Напишите HTTP-обработчик шлюза с чтением тела через `io.LimitReader` для защиты от DoS атак.",
        "Протестируйте загрузку бинарного JPEG файла и проверку корректности ответа."
    ],
    "code_blocks": [
        {
            "filename": "binary_httpbody_gateway.go",
            "lang": "go",
            "code": r"""package main

import (
	"bytes"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
)

type HttpBody struct {
	ContentType string `json:"content_type"`
	Data        []byte `json:"data"`
}

type FileStorageService struct{}

func (s *FileStorageService) UploadAvatar(userID string, body HttpBody) (int, error) {
	if len(body.Data) == 0 {
		return 0, fmt.Errorf("uploaded file is empty")
	}
	if body.ContentType != "image/png" && body.ContentType != "image/jpeg" {
		return 0, fmt.Errorf("unsupported content type: %s", body.ContentType)
	}
	return len(body.Data), nil
}

func BinaryUploadHandler(svc *FileStorageService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost && r.Method != http.MethodPut {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		userID := r.URL.Query().Get("user_id")
		if userID == "" {
			http.Error(w, "query param user_id is required", http.StatusBadRequest)
			return
		}

		// Лимит 10 МБ для защиты от DoS
		data, err := io.ReadAll(io.LimitReader(r.Body, 10<<20))
		if err != nil {
			http.Error(w, "failed to read body", http.StatusInternalServerError)
			return
		}

		httpBody := HttpBody{
			ContentType: r.Header.Get("Content-Type"),
			Data:        data,
		}

		written, err := svc.UploadAvatar(userID, httpBody)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		w.WriteHeader(http.StatusCreated)
		_, _ = fmt.Fprintf(w, "Uploaded %d bytes successfully for user %s", written, userID)
	}
}

func main() {
	svc := &FileStorageService{}
	handler := BinaryUploadHandler(svc)

	fakeJPEG := []byte{0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46}
	req := httptest.NewRequest(http.MethodPost, "/v1/users/avatar?user_id=usr_lead_77", bytes.NewReader(fakeJPEG))
	req.Header.Set("Content-Type", "image/jpeg")

	rec := httptest.NewRecorder()
	handler(rec, req)

	fmt.Println("=== BINARY HTTPBODY UPLOAD TEST ===")
	fmt.Printf("HTTP Status:   %d\n", rec.Code)
	fmt.Printf("Response Body: %s\n", rec.Body.String())
}
"""
        }
    ],
    "under_the_hood": "gRPC-Gateway содержит встроенный перехватчик сообщений типа `google.api.HttpBody`. Когда кодогенератор видит этот тип, он генерирует специализированный маршалер, минующий JSON-парсер и считывающий сырые слайсы байтов прямо из транспортного уровня сокета.",
    "pitfalls": [
        "Чтение `r.Body` без использования `io.LimitReader`: злоумышленник может отправить бесконечный HTTP-поток, вызвав Out-Of-Memory (OOM-Kill) на сервере шлюза.",
        "Попытка передавать многогигабайтные файлы через один унарный RPC вызов с `HttpBody`: максимальный размер gRPC сообщения ограничен параметром `MaxRecvMsgSize` (по умолчанию 4 МБ)."
    ],
    "bigtech_interview": "Как спроектировать загрузку файлов размером 10+ ГБ в архитектуре с gRPC-Gateway? Загрузка тяжелых файлов через gRPC-Gateway является антипаттерном. Рекомендуется паттерн Presigned URL: клиент вызывает легковесный RPC метод `GetUploadUrl`, сервис генерирует подписанную ссылку с коротким TTL (S3/GCS), и клиент загружает файл напрямую в объектное хранилище через HTTP PUT, минуя шлюз и разгружая вычислительную сеть."
})

# Exercise 25
exercises.append({
    "num": 25,
    "title": "Rate Limiting на уровне шлюза до gRPC-бэкенда (Token Bucket)",
    "task": "Защитите внутренние gRPC-сервисы от перегрузки: реализуйте Rate Limiting middleware на уровне HTTP-шлюза с использованием алгоритма Token Bucket (`golang.org/x/time/rate`). При превышении лимита шлюз мгновенно возвращает клиенту HTTP `429 Too Many Requests` без создания нагрузки на внутреннюю сеть.",
    "theory": r"""Зачем размещать Rate Limiter на уровне шлюза, а не в самом gRPC-сервисе?
1. **Экономия ресурсов бэкенда:** Проверка лимитов на шлюзе предотвращает напрасную десериализацию JSON в Protobuf, выделение TCP-потоков и нагрузку на gRPC пул горутин.
2. **Изоляция сбоев:** При DoS-атаке на публичный REST API внутренние межсервисные gRPC-каналы взаимодействия продолжают функционировать без деградации.
3. **Алгоритм Token Bucket (`golang.org/x/time/rate`):**
   - Корзина вмещает максимум `Burst` токенов.
   - Токены пополняются с постоянной скоростью `Rate`.
   - Метод `limiter.Allow()` атомарно потребляет 1 токен. Если токенов нет — возвращает `false`.
   - Шлюз возвращает клиенту заголовок `Retry-After: N` согласно стандарту RFC 6585.""",
    "step_by_step": [
        "Создайте потокобезопасный менеджер `IPRateLimiter` с использованием `sync.Mutex` и `rate.Limiter`.",
        "Реализуйте извлечение IP-адреса с поддержкой заголовка `X-Forwarded-For`.",
        "Создайте middleware `RateLimitMiddleware`, возвращающее HTTP 429 при исчерпании токенов.",
        "Продемонстрируйте серию последовательных запросов и отсечение избыточного трафика."
    ],
    "code_blocks": [
        {
            "filename": "gateway_rate_limiter.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"sync"
	"time"

	"golang.org/x/time/rate"
)

type IPRateLimiter struct {
	mu       sync.Mutex
	limiters map[string]*rate.Limiter
	rate     rate.Limit
	burst    int
}

func NewIPRateLimiter(r rate.Limit, b int) *IPRateLimiter {
	return &IPRateLimiter{
		limiters: make(map[string]*rate.Limiter),
		rate:     r,
		burst:    b,
	}
}

func (i *IPRateLimiter) GetLimiter(ip string) *rate.Limiter {
	i.mu.Lock()
	defer i.mu.Unlock()

	limiter, exists := i.limiters[ip]
	if !exists {
		limiter = rate.NewLimiter(i.rate, i.burst)
		i.limiters[ip] = limiter
	}
	return limiter
}

func RateLimitMiddleware(limiterMgr *IPRateLimiter, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ip := r.RemoteAddr
		if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
			ip = xff
		}

		limiter := limiterMgr.GetLimiter(ip)
		if !limiter.Allow() {
			w.Header().Set("Retry-After", "1")
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusTooManyRequests)
			_, _ = w.Write([]byte(`{"code":8,"message":"ResourceExhausted: rate limit exceeded"}`))
			return
		}

		next.ServeHTTP(w, r)
	})
}

func main() {
	// Лимит: 2 запроса в секунду, burst 2
	limiterMgr := NewIPRateLimiter(rate.Every(500*time.Millisecond), 2)
	dummyHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("PROCESSED_SUCCESS"))
	})

	handler := RateLimitMiddleware(limiterMgr, dummyHandler)

	fmt.Println("=== TOKEN BUCKET RATE LIMITING TEST ===")
	for i := 1; i <= 4; i++ {
		req := httptest.NewRequest(http.MethodGet, "/v1/orders", nil)
		req.Header.Set("X-Forwarded-For", "203.0.113.195")
		rec := httptest.NewRecorder()

		handler.ServeHTTP(rec, req)
		fmt.Printf("Request #%d: Status Code %d (Body: %s)\n", i, rec.Code, rec.Body.String())
	}
}
"""
        }
    ],
    "under_the_hood": "Алгоритм `rate.Limiter` в пакете `golang.org/x/time/rate` не запускает фоновых таймеров на каждый токен. Вместо этого он математически вычисляет доступное количество токенов в момент вызова `Allow()` на основе разницы текущего времени `time.Now()` и времени предыдущего запроса `last`, обеспечивая предельную производительность без аллокаций.",
    "pitfalls": [
        "Утечка памяти в мапе `limiters`: если миллионы уникальных IP обращаются к шлюзу, мапа разрастается бесконечно. Требуется фоновый сборщик (Janitor Goroutine) или использование bounded LRU кэша.",
        "Доверие заголовку `X-Forwarded-For` без валидации доверенных прокси (Trusted Proxies): злоумышленник может подделывать IP и обходить лимиты."
    ],
    "bigtech_interview": "Как организовать Rate Limiting при горизонтальном масштабировании шлюза на десятки реплик в Kubernetes? Локальные лимитеры в памяти не синхронизированы между репликами. В HighLoad архитектуре используется централизованный Redis кластер с выполнением атомарных Lua-скриптов алгоритма Generic Cell Rate Algorithm (GCRA) или Token Bucket. Дополнительно на самом шлюзе может применяться локальный fallback-лимитер на случай сетевой недоступности Redis."
})

# Exercise 26
exercises.append({
    "num": 26,
    "title": "Сквозная распределенная трассировка (OpenTelemetry W3C Trace Context)",
    "task": "Подключите OpenTelemetry к HTTP-шлюзу и gRPC-серверу. Покажите, как W3C Trace Context (`traceparent` заголовок) извлекается из входящего HTTP-запроса шлюзом, передается в исходящие gRPC метаданные и продолжается внутренними спанами gRPC-сервера, формируя единое дерево трассировки.",
    "theory": r"""При микросервисной архитектуре запрос проходит цепочку:
`Браузер / REST Клиент` -> `HTTP API Gateway` -> `gRPC Service A` -> `gRPC Service B` -> `PostgreSQL`.

Без сквозной трассировки невозможно локализовать причины задержек (high latency).
Стандарт **W3C Trace Context**:
- Заголовок **`traceparent`**: `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`
  - `00` — версия спецификации.
  - `4bf92f3577b34da6a3ce929d0e0e4736` — Trace ID (16 байт / 32 hex символа, единый для всего дерева вызовов).
  - `00f067aa0ba902b7` — Parent Span ID (8 байт / 16 hex символов).
  - `01` — Trace Flags (бит `01` указывает на включенный sampling записи спана).
- Заголовок **`tracestate`**: метаданные специфичных систем трассировки.

Шлюз обязан извлечь эти заголовки и упаковать их в исходящий `metadata.NewOutgoingContext`, чтобы gRPC интерцептор `otelgrpc` на бэкенде продолжил дерево трейса.""",
    "step_by_step": [
        "Определите константы заголовков W3C стандарта: `traceparent` и `tracestate`.",
        "Создайте структуру `TraceContextPropagator` для переноса контекста трассировки.",
        "Реализуйте метод `InjectToGrpcMetadata`, внедряющий W3C заголовки в gRPC metadata.",
        "Проверьте корректное извлечение метаданных на стороне имитатора gRPC-клиента."
    ],
    "code_blocks": [
        {
            "filename": "opentelemetry_w3c_gateway.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
	"net/http"

	"google.golang.org/grpc/metadata"
)

const (
	TraceParentHeader = "traceparent"
	TraceStateHeader  = "tracestate"
)

type TraceContextPropagator struct{}

func (p *TraceContextPropagator) InjectToGrpcMetadata(ctx context.Context, r *http.Request) context.Context {
	md, ok := metadata.FromOutgoingContext(ctx)
	if !ok {
		md = metadata.New(nil)
	} else {
		md = md.Copy()
	}

	if tp := r.Header.Get(TraceParentHeader); tp != "" {
		md.Set(TraceParentHeader, tp)
	}
	if ts := r.Header.Get(TraceStateHeader); ts != "" {
		md.Set(TraceStateHeader, ts)
	}

	return metadata.NewOutgoingContext(ctx, md)
}

func main() {
	propagator := &TraceContextPropagator{}

	req, _ := http.NewRequest(http.MethodGet, "/v1/orders/ord_9988", nil)
	sampleTraceParent := "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
	req.Header.Set(TraceParentHeader, sampleTraceParent)
	req.Header.Set(TraceStateHeader, "rojo=1,congo=2")

	ctx := propagator.InjectToGrpcMetadata(context.Background(), req)
	outMD, _ := metadata.FromOutgoingContext(ctx)

	fmt.Println("=== W3C TRACE CONTEXT PROPAGATION TEST ===")
	fmt.Printf("Incoming HTTP traceparent: %s\n", sampleTraceParent)
	fmt.Printf("gRPC Metadata traceparent:  %s\n", outMD.Get(TraceParentHeader)[0])
	fmt.Printf("gRPC Metadata tracestate:   %s\n", outMD.Get(TraceStateHeader)[0])
}
"""
        }
    ],
    "under_the_hood": "В production коде пакет `go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc` автоматически переносит контекст между HTTP и gRPC вызовами. Интерцептор считывает `traceparent` из входящего контекста, стартует дочерний спан и кодирует обновленный `SpanID` в исходящий заголовок, сохраняя исходный `TraceID`.",
    "pitfalls": [
        "Мутация существующего объекта `metadata.MD` в конкурентных горутинах: всегда используйте `md.Copy()` перед модификацией метаданных контекста.",
        "Потеря контекста при асинхронном запуске горутин: если вы запускаете фоновую задачу через `go func()`, необходимо передавать отвязанный контекст с сохранением спана через `trace.ContextWithSpanContext()`."
    ],
    "bigtech_interview": "Что происходит, если входящий HTTP-запрос пришел без заголовка traceparent? SDK трассировки на шлюзе определяет отсутствие родительского спана, генерирует новый криптографически стойкий 16-байтный Trace ID и 8-байтный Span ID, создавая корневой спан (Root Span). Этот новый traceparent автоматически инжектируется во все последующие вызовы gRPC-сервисов, формируя цельное дерево трейса."
})

# Exercise 27
exercises.append({
    "num": 27,
    "title": "Мониторинг шлюза: метрики Prometheus для HTTP и gRPC",
    "task": "Оснастите API-шлюз раздельными метриками Prometheus: гистограммы времени обработки входящих HTTP-запросов (`http_request_duration_seconds`), счетчики статус-кодов ответов и сопоставление их со сквозными метриками нижележащих gRPC-бэкендов (`grpc_server_handling_seconds`).",
    "theory": r"""Мониторинг API-шлюза критичен, так как именно он формирует SLA/SLO сервиса в глазах внешних клиентов.

Ключевые RED метрики (Rate, Errors, Duration) шлюза:
1. **Rate (`http_requests_total`):** Counter со словарными метками: `method`, `route`, `status_code`.
2. **Errors:** Доля ответов `5xx` (внутренние ошибки) и `4xx` (ошибки валидации/клиентов).
3. **Duration (`http_request_duration_seconds`):** Histogram с логарифмическими бакетами (от 5ms до 10s) для точного расчета p95, p99 перцентилей.

Технический нюанс в Go:
Стандартный `http.ResponseWriter` не сохраняет записанный статус-код. Чтобы считать его в middleware после выполнения хендлера, применяется паттерн **ResponseWriter Wrapper**, переопределяющий метод `WriteHeader(code int)`.""",
    "step_by_step": [
        "Создайте агрегатор метрик `MetricCollector` для сбора количества вызовов и суммарной задержки.",
        "Реализуйте обертку `StatusLoggingResponseWriter`, перехватывающую статус-код ответа.",
        "Напишите middleware `PrometheusMetricsMiddleware` для замера длительности через `time.Since(start)`.",
        "Продемонстрируйте сбор метрик выполнения POST-запроса с кодом 201 Created."
    ],
    "code_blocks": [
        {
            "filename": "prometheus_gateway_metrics.go",
            "lang": "go",
            "code": r"""package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"sync"
	"time"
)

type MetricCollector struct {
	mu            sync.Mutex
	requestsTotal map[string]int64
	durationsSum  map[string]float64
}

func NewMetricCollector() *MetricCollector {
	return &MetricCollector{
		requestsTotal: make(map[string]int64),
		durationsSum:  make(map[string]float64),
	}
}

func (c *MetricCollector) Record(method, path string, status int, duration time.Duration) {
	key := fmt.Sprintf("%s|%s|%d", method, path, status)
	c.mu.Lock()
	defer c.mu.Unlock()
	c.requestsTotal[key]++
	c.durationsSum[key] += duration.Seconds()
}

type StatusLoggingResponseWriter struct {
	http.ResponseWriter
	StatusCode int
}

func (w *StatusLoggingResponseWriter) WriteHeader(code int) {
	w.StatusCode = code
	w.ResponseWriter.WriteHeader(code)
}

func PrometheusMetricsMiddleware(metrics *MetricCollector, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		wrapped := &StatusLoggingResponseWriter{ResponseWriter: w, StatusCode: http.StatusOK}

		next.ServeHTTP(wrapped, r)

		duration := time.Since(start)
		metrics.Record(r.Method, r.URL.Path, wrapped.StatusCode, duration)
	})
}

func main() {
	metrics := NewMetricCollector()
	dummyHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(15 * time.Millisecond)
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"status":"created"}`))
	})

	handler := PrometheusMetricsMiddleware(metrics, dummyHandler)

	req := httptest.NewRequest(http.MethodPost, "/v1/orders", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	metrics.mu.Lock()
	defer metrics.mu.Unlock()

	fmt.Println("=== PROMETHEUS GATEWAY METRICS ===")
	for k, count := range metrics.requestsTotal {
		fmt.Printf("Metric: %s -> Total Calls: %d, Total Duration: %.4fs\n", k, count, metrics.durationsSum[k])
	}
}
"""
        }
    ],
    "under_the_hood": "В Prometheus метках шлюза критически важно использовать параметризованный шаблон маршрута (`/v1/orders/{order_id}`), а не сырой URL с идентификаторами сущностей. Использование сырых URL приводит к взрыву кардинальности (Cardinality Explosion), исчерпанию оперативной памяти базы Prometheus и отказу системы мониторинга.",
    "pitfalls": [
        "Неинициализированный статус-код в ResponseWriter обертке: если хендлер не вызывает `WriteHeader` явно, Go автоматически отправляет 200 OK. Дефолтное значение обертки обязано быть 200.",
        "Использование неатомарных структур без мьютексов при конкурентном обновлении счетчиков метрик."
    ],
    "bigtech_interview": "В чем разница между метриками задержки на уровне шлюза (`http_request_duration_seconds`) и на уровне gRPC сервиса (`grpc_server_handling_seconds`)? Разница между ними показывает накладные расходы самого шлюза и сетевого слоя: время разбора JSON тела, проверку JWT токена и CORS, сериализацию в Protobuf, ожидание свободного соединения в connection pool и сетевой RTT. Если задержка шлюза существенно выше задержки gRPC, узким местом является сам шлюз, а не бизнес-логика."
})

# Exercise 28
exercises.append({
    "num": 28,
    "title": "Graceful Shutdown мультиплексированного шлюза",
    "task": "Реализуйте аккуратную остановку серверов при получении сигналов ОС: шлюз прекращает прием новых HTTP-соединений, дожидается завершения активных долгих HTTP-стримов, отправляет сигнал `GracefulStop()` в gRPC-сервер и закрывает соединения с базой данных в пределах 15 секунд.",
    "theory": r"""При развертывании в Kubernetes (Rolling Update) Pod получает сигнал `SIGTERM`.
Если процесс завершится мгновенно:
- Клиенты получат ошибку `502 Bad Gateway` или `Connection Reset by Peer`.
- Незавершенные транзакции и потоковые передачи оборвутся на середине.

Правильная процедура Graceful Shutdown мультиплексированного шлюза:
1. **Прекращение приема входящих соединений:** Вызов `httpServer.Shutdown(ctx)`. Шлюз закрывает слушающий TCP-сокет, перестает отвечать на `readinessProbe` (K8s убирает Pod из Endpoints) и ожидает завершения in-flight запросов.
2. **Остановка gRPC сервера:** Вызов `grpcServer.GracefulStop()`. Сервер прекращает прием новых RPC и дожидается возврата из активных методов.
3. **Таймаут аварийного сброса:** Если за отведенный таймаут соединения не закрылись (зависшие стримы), вызывается принудительный `grpcServer.Stop()`.""",
    "step_by_step": [
        "Создайте координатор `DualServerManager` с ссылками на `*http.Server` и `*grpc.Server`.",
        "Реализуйте метод `GracefulShutdown` с параллельным завершением серверов через `sync.WaitGroup`.",
        "Запустите `grpcServer.GracefulStop()` в горутине с защитой от зависания через `select` по `ctx.Done()`.",
        "Продемонстрируйте корректную процедуру плавной остановки."
    ],
    "code_blocks": [
        {
            "filename": "dual_graceful_shutdown.go",
            "lang": "go",
            "code": r"""package main

import (
	"context"
	"fmt"
	"net/http"
	"sync"
	"time"

	"google.golang.org/grpc"
)

type DualServerManager struct {
	httpServer *http.Server
	grpcServer *grpc.Server
}

func NewDualServerManager(httpSrv *http.Server, grpcSrv *grpc.Server) *DualServerManager {
	return &DualServerManager{
		httpServer: httpSrv,
		grpcServer: grpcSrv,
	}
}

func (m *DualServerManager) GracefulShutdown(timeout time.Duration) error {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	var wg sync.WaitGroup
	errCh := make(chan error, 2)

	// 1. Остановка HTTP шлюза
	wg.Add(1)
	go func() {
		defer wg.Done()
		fmt.Println("[Shutdown] Stopping HTTP Gateway...")
		if err := m.httpServer.Shutdown(ctx); err != nil {
			errCh <- fmt.Errorf("http shutdown failed: %w", err)
		} else {
			fmt.Println("[Shutdown] HTTP Gateway stopped gracefully")
		}
	}()

	// 2. Остановка gRPC сервера
	wg.Add(1)
	go func() {
		defer wg.Done()
		fmt.Println("[Shutdown] Stopping gRPC Server...")
		stopped := make(chan struct{})
		go func() {
			m.grpcServer.GracefulStop()
			close(stopped)
		}()

		select {
		case <-stopped:
			fmt.Println("[Shutdown] gRPC Server stopped gracefully")
		case <-ctx.Done():
			fmt.Println("[Shutdown] gRPC Server timeout exceeded, forcing Stop()...")
			m.grpcServer.Stop()
		}
	}()

	wg.Wait()
	close(errCh)

	for err := range errCh {
		if err != nil {
			return err
		}
	}
	return nil
}

func main() {
	grpcSrv := grpc.NewServer()
	httpSrv := &http.Server{Addr: ":8080"}

	manager := NewDualServerManager(httpSrv, grpcSrv)

	fmt.Println("=== INITIATING DUAL GRACEFUL SHUTDOWN ===")
	err := manager.GracefulShutdown(2 * time.Second)
	fmt.Printf("Graceful shutdown completed. Error: %v\n", err)
}
"""
        }
    ],
    "under_the_hood": "Метод `grpcServer.GracefulStop()` является синхронным и блокирующим: он ожидает возврата из всех хендлеров активных RPC вызовов. Если у клиента открыт непрерывный Server-Streaming вызов, метод никогда не завершится. Поэтому запуск `GracefulStop()` в отдельной горутине с таймаутом контекста обязателен.",
    "pitfalls": [
        "Немедленная остановка процесса при получении SIGTERM без задержки (preStop hook): в Kubernetes сетевые правила iptables обновляются асинхронно, поэтому новые запросы продолжают прилетать еще 2–5 секунд после отправки SIGTERM.",
        "Забытое закрытие пулов соединений к БД (pgxpool) и брокерам сообщений после остановки HTTP/gRPC серверов."
    ],
    "bigtech_interview": "Каков правильный жизненный цикл завершения сервиса шлюза в Kubernetes? 1) preStop hook со `sleep 5` для исключения Pod из Endpoints балансировщика; 2) Перевод readiness probe в состояние 503; 3) `httpServer.Shutdown()` с таймаутом 15-30s; 4) `grpcServer.GracefulStop()`; 5) Закрытие подключений к Redis, Kafka и PostgreSQL."
})

# Exercise 29
exercises.append({
    "num": 29,
    "title": "Комплексное E2E тестирование: gRPC vs REST клиент",
    "task": "Напишите интеграционный тест с использованием `httptest.NewServer`: отправьте одинаковые бизнес-запросы создания сущности через сгенерированный gRPC-клиент и через стандартный `http.Client` (REST/JSON). Проверьте идентичность возвращаемых данных, кодов ошибок и заголовков.",
    "theory": r"""При использовании gRPC-Gateway возникает риск расхождения поведения (Contract Drift):
- Одинаковые ли HTTP-статусы возвращаются при ошибках валидации?
- Совпадают ли имена полей в ответе (snake_case vs camelCase)?
- Корректно ли десериализуются значения по умолчанию (`0`, `false`, пустые массивы `[]`)?

Паттерн тестирования паритета контрактов (Contract Parity Testing):
1. Тест поднимает тестовый сервер `httptest.NewServer` с зарегистрированным шлюзом и сервисом.
2. Выполняется вызов одной и той же бизнес-операции:
   - Через нативный клиент (RPC вызов).
   - Через стандартный `http.Client` (REST POST/GET запрос).
3. Сравнивается идентичность полезной нагрузки с помощью `reflect.DeepEqual`.
4. Это гарантирует, что клиенты REST API получают в точности ту же информацию, что и клиенты микросервисного gRPC API.""",
    "step_by_step": [
        "Определите контракт сервиса `OrderServiceContract` и структуру заказа `OrderItem`.",
        "Реализуйте HTTP-адаптер шлюза `GatewayHTTPAdapter` для обработки JSON запросов.",
        "Напишите функцию E2E теста `RunE2EParityTest` с запуском `httptest.NewServer`.",
        "Проверьте идентичность результата прямого вызова и вызова через REST шлюз."
    ],
    "code_blocks": [
        {
            "filename": "grpc_rest_parity_test.go",
            "lang": "go",
            "code": r"""package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"reflect"
)

type OrderItem struct {
	ID    string `json:"id"`
	Title string `json:"title"`
	Price int64  `json:"price"`
}

type OrderServiceContract interface {
	CreateOrder(ctx context.Context, item OrderItem) (OrderItem, error)
}

type MockOrderService struct{}

func (s *MockOrderService) CreateOrder(ctx context.Context, item OrderItem) (OrderItem, error) {
	if item.Title == "" {
		return OrderItem{}, fmt.Errorf("title cannot be empty")
	}
	item.ID = "ord-contract-parity-101"
	return item, nil
}

func GatewayHTTPAdapter(svc OrderServiceContract) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		var item OrderItem
		if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
			http.Error(w, "invalid json", http.StatusBadRequest)
			return
		}

		created, err := svc.CreateOrder(r.Context(), item)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_ = json.NewEncoder(w).Encode(created)
	}
}

func RunE2EParityTest() error {
	svc := &MockOrderService{}
	ts := httptest.NewServer(GatewayHTTPAdapter(svc))
	defer ts.Close()

	input := OrderItem{Title: "Distributed Go Architecture", Price: 8900}

	// 1. Вызов напрямую через контракт
	directResult, err := svc.CreateOrder(context.Background(), input)
	if err != nil {
		return fmt.Errorf("direct call failed: %w", err)
	}

	// 2. Вызов через REST шлюз
	reqBody, _ := json.Marshal(input)
	resp, err := http.Post(ts.URL, "application/json", bytes.NewReader(reqBody))
	if err != nil {
		return fmt.Errorf("http post failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		return fmt.Errorf("expected status 201 Created, got %d", resp.StatusCode)
	}

	var httpResult OrderItem
	if err := json.NewDecoder(resp.Body).Decode(&httpResult); err != nil {
		return fmt.Errorf("failed to decode response: %w", err)
	}

	// 3. Проверка паритета
	if !reflect.DeepEqual(directResult, httpResult) {
		return fmt.Errorf("contract parity mismatch: direct=%+v, http=%+v", directResult, httpResult)
	}

	return nil
}

func main() {
	fmt.Println("=== RUNNING CONTRACT PARITY E2E TEST ===")
	if err := RunE2EParityTest(); err != nil {
		panic(err)
	}
	fmt.Println("Contract Parity Test PASSED: gRPC and REST outputs are 100% identical!")
}
"""
        }
    ],
    "under_the_hood": "В реальных микросервисах интеграционное тестирование gRPC-Gateway проводится с использованием in-memory сокета `google.golang.org/grpc/test/bufconn`. Это позволяет тестировать gRPC и HTTP шлюз в одном процессе без выделения реальных портов операционной системы, предотвращая конфликты параллельных тестов в CI/CD.",
    "pitfalls": [
        "Несовпадение форматирования чисел с плавающей точкой или времени: JSON маршалер Protobuf по умолчанию форматирует `google.protobuf.Timestamp` в RFC 3339 строку с суффиксом 'Z', а стандартный time.Time в Go может форматировать временную зону как '+00:00'.",
        "Несовпадение snake_case и camelCase в именах полей, если на шлюзе не настроена опция `UseProtoNames: true`."
    ],
    "bigtech_interview": "Как организовать тестирование gRPC-Gateway без открытия реальных портов в CI? Использовать виртуальный листенер `lis := bufconn.Listen(1024 * 1024)`. Сервер слушает на `lis`, а клиент шлюза подключается через кастомный диаллер `grpc.WithContextDialer(func(ctx context.Context, s string) (net.Conn, error) { return lis.Dial() })`. Тесты выполняются полностью в памяти с предельной скоростью."
})

# Exercise 30
exercises.append({
    "num": 30,
    "title": "Полноценный контрактный API Gateway микросервисной платформы (Capstone)",
    "task": "Объедините все элементы главы в законченный enterprise-шлюз: сборка proto-контрактов через `buf`, мультиплексирование HTTP/REST и gRPC на одном порту, встроенная Swagger UI документация, JWT-аутентификация, валидация полей через `protovalidate`, поддержка gRPC-Web и экспорт Prometheus-метрик.",
    "theory": r"""Финальный архитектурный синтез контрактно-ориентированного API-шлюза:

1. **Единый источник истины (Contract-First):**
   - Все контракты и REST-роуты описываются в Protobuf схемах с аннотациями `google.api.http`.
   - Автоматическая кодогенерация интерфейсов, клиентов и OpenAPI спецификаций через `buf generate`.
2. **Мультиплексирование и маршрутизация:**
   - Единый HTTP/2 сервер обрабатывает Swagger документацию, health checks, gRPC-Web вызовы и REST/JSON эндпоинты.
3. **Периметральная безопасность и Observability:**
   - Edge JWT-аутентификация с извлечением claims в метаданные контекста.
   - Сквозная W3C распределенная трассировка (`X-Trace-ID`).
   - Изоляция внутренних gRPC сервисов от перегрузок через Rate Limiting и сбор Prometheus метрик.""",
    "step_by_step": [
        "Создайте структуру `EnterpriseGateway` с потокобезопасным репозиторием товаров.",
        "Реализуйте периметральный middleware `AuthAndTraceMiddleware` с проверкой Bearer-токена и пробросом Trace ID.",
        "Настройте маршрутизацию для раздачи документации OpenAPI `/docs/openapi.json`, healthcheck и бизнес-методов REST API.",
        "Продемонстрируйте комплексную работу шлюза: публичный доступ к документации, отсечение неавторизованных запросов (401) и успешную обработку авторизованных запросов."
    ],
    "code_blocks": [
        {
            "filename": "capstone_enterprise_gateway.go",
            "lang": "go",
            "code": r"""package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"time"
)

type Product struct {
	ID       string  `json:"id"`
	Title    string  `json:"title"`
	PriceUSD float64 `json:"price_usd"`
	Category string  `json:"category"`
}

type EnterpriseGateway struct {
	mu       sync.RWMutex
	products map[string]Product
}

func NewEnterpriseGateway() *EnterpriseGateway {
	gw := &EnterpriseGateway{
		products: make(map[string]Product),
	}
	gw.products["prod-100"] = Product{
		ID:       "prod-100",
		Title:    "Go Microservices & HighLoad Architecture",
		PriceUSD: 79.99,
		Category: "Engineering",
	}
	return gw
}

func (g *EnterpriseGateway) AuthAndTraceMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Публичные эндпоинты: документация OpenAPI и проверка жизнеспособности
		if strings.HasPrefix(r.URL.Path, "/docs") || r.URL.Path == "/healthz" {
			next.ServeHTTP(w, r)
			return
		}

		authHeader := r.Header.Get("Authorization")
		if authHeader == "" || !strings.HasPrefix(authHeader, "Bearer ") {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusUnauthorized)
			_, _ = w.Write([]byte(`{"code":16,"message":"Unauthenticated: missing valid Bearer token"}`))
			return
		}

		traceID := r.Header.Get("X-Trace-ID")
		if traceID == "" {
			traceID = fmt.Sprintf("trace-%d", time.Now().UnixNano())
		}
		w.Header().Set("X-Trace-ID", traceID)

		next.ServeHTTP(w, r)
	})
}

func (g *EnterpriseGateway) Router() http.Handler {
	mux := http.NewServeMux()

	// 1. OpenAPI v3 Documentation Endpoint
	mux.HandleFunc("/docs/openapi.json", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		doc := map[string]any{
			"openapi": "3.0.0",
			"info": map[string]string{
				"title":       "Enterprise Product API Gateway",
				"version":     "1.0.0",
				"description": "Contract-First gRPC & REST Gateway with embedded OpenAPI v3",
			},
		}
		_ = json.NewEncoder(w).Encode(doc)
	})

	// 2. Health Check
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("HEALTHY"))
	})

	// 3. REST Endpoint: GET /v1/products/{id}
	mux.HandleFunc("/v1/products/", func(w http.ResponseWriter, r *http.Request) {
		parts := strings.Split(strings.Trim(r.URL.Path, "/"), "/")
		if len(parts) != 3 {
			http.NotFound(w, r)
			return
		}
		id := parts[2]

		g.mu.RLock()
		prod, exists := g.products[id]
		g.mu.RUnlock()

		if !exists {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusNotFound)
			_, _ = w.Write([]byte(`{"code":5,"message":"product not found"}`))
			return
		}

		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(prod)
	})

	return g.AuthAndTraceMiddleware(mux)
}

func main() {
	gw := NewEnterpriseGateway()
	handler := gw.Router()

	fmt.Println("=== CAPSTONE: ENTERPRISE CONTRACT API GATEWAY ===")

	// 1. Проверка публичного доступа к OpenAPI
	recDoc := httptest.NewRecorder()
	reqDoc := httptest.NewRequest(http.MethodGet, "/docs/openapi.json", nil)
	handler.ServeHTTP(recDoc, reqDoc)
	fmt.Printf("[DOCS] Status: %d, Content-Type: %s\n", recDoc.Code, recDoc.Header().Get("Content-Type"))

	// 2. Неавторизованный запрос -> 401 Unauthorized
	recUnauth := httptest.NewRecorder()
	reqUnauth := httptest.NewRequest(http.MethodGet, "/v1/products/prod-100", nil)
	handler.ServeHTTP(recUnauth, reqUnauth)
	fmt.Printf("[UNAUTH] Status: %d, Body: %s\n", recUnauth.Code, strings.TrimSpace(recUnauth.Body.String()))

	// 3. Авторизованный запрос с Bearer токеном -> 200 OK
	recAuth := httptest.NewRecorder()
	reqAuth := httptest.NewRequest(http.MethodGet, "/v1/products/prod-100", nil)
	reqAuth.Header.Set("Authorization", "Bearer jwt-secret-token-xyz")
	handler.ServeHTTP(recAuth, reqAuth)
	fmt.Printf("[AUTH] Status: %d, TraceID: %s, Body: %s\n",
		recAuth.Code, recAuth.Header().Get("X-Trace-ID"), strings.TrimSpace(recAuth.Body.String()))
}
"""
        }
    ],
    "under_the_hood": "В архитектуре современного API-шлюза контракт Protobuf выступает единым источником правды. Шлюз транслирует внешние гетерогенные протоколы (REST JSON, gRPC-Web) во внутренние строго типизированные бинарные вызовы gRPC по постоянным TCP/HTTP2 соединениям с пулом соединений (Connection Pooling), обеспечивая задержки на уровне долей миллисекунды.",
    "pitfalls": [
        "Выполнение тяжелой бизнес-логики внутри шлюза: шлюз должен отвечать только за маршрутизацию, безопасность, аутентификацию, rate limiting и observability. Бизнес-логика должна оставаться в микросервисах.",
        "Единая точка отказа (Single Point of Failure): шлюз обязан развертываться минимум в трех репликах с распределением по разным зонам доступности (Availability Zones) и автоскейлингом по CPU/RPS через Kubernetes HPA."
    ],
    "bigtech_interview": "Как в распределенной Enterprise-системе организовать версионирование при контрактном подходе? Каждый мажорный релиз контракта выносится в отдельный пакет Protobuf: `package company.order.v1;` и `package company.order.v2;`. Соответственно URL-пути маппятся на `/v1/orders` и `/v2/orders`. CI с помощью `buf breaking` контролирует, чтобы правки внутри ветки v1 не нарушали контракты существующих мобильных и веб-клиентов. Шлюз регистрирует одновременно обработчики v1 и v2, обеспечивая плавный период миграции клиентов в течение 6–12 месяцев."
})

# Verify gofmt for all exercises
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

out_path = "/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch90_p2.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Wrote {out_path} successfully with {len(exercises)} exercises!")
