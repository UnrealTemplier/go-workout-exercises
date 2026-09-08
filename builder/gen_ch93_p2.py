import json
import subprocess
import os

def validate_go(code):
    p = subprocess.run(['gofmt', '-e'], input=code.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise ValueError(f"Go syntax error: {p.stderr.decode('utf-8')}\nCode:\n{code}")

exercises = []

# Ex 16
ex16_code = """package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
)

// RouteRule описывает правило префиксной маршрутизации.
type RouteRule struct {
	Prefix      string
	UpstreamURL string
	StripPrefix bool
}

// PrefixRouter сопоставляет входящий путь с целевым апстримом.
type PrefixRouter struct {
	mu     sync.RWMutex
	routes []RouteRule
}

func NewPrefixRouter() *PrefixRouter {
	return &PrefixRouter{}
}

func (r *PrefixRouter) AddRoute(prefix, upstream string, strip bool) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.routes = append(r.routes, RouteRule{
		Prefix:      prefix,
		UpstreamURL: upstream,
		StripPrefix: strip,
	})
}

func (r *PrefixRouter) Match(reqPath string) (targetUpstream, targetPath string, ok bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	for _, rule := range r.routes {
		if strings.HasPrefix(reqPath, rule.Prefix) {
			path := reqPath
			if rule.StripPrefix {
				path = strings.TrimPrefix(reqPath, rule.Prefix)
				if !strings.HasPrefix(path, "/") {
					path = "/" + path
				}
			}
			return rule.UpstreamURL, path, true
		}
	}
	return "", "", false
}

func main() {
	router := NewPrefixRouter()
	router.AddRoute("/api/v1/users", "http://users-service.internal:8080", true)
	router.AddRoute("/api/v1/orders", "http://orders-service.internal:8080", true)
	router.AddRoute("/static", "http://s3-cdn.internal:9000", false)

	paths := []string{
		"/api/v1/users/42/profile",
		"/api/v1/orders/create",
		"/static/img/logo.png",
		"/unknown/endpoint",
	}

	fmt.Println("Результаты работы префиксного роутера API-шлюза:")
	for _, p := range paths {
		upstream, rewritten, found := router.Match(p)
		if found {
			fmt.Printf("Вход: %-25s -> Апстрим: %-35s Путь: %s\\n", p, upstream, rewritten)
		} else {
			fmt.Printf("Вход: %-25s -> [404 Not Found]\\n", p)
		}
	}
}
"""
validate_go(ex16_code)

exercises.append({
    "num": 16,
    "title": "Динамическая маршрутизация по префиксам путей (Path Routing)",
    "task": "Спроектируйте префиксный роутер PrefixRouter для API-шлюза. Реализуйте правила сопоставления путей (RouteRule) с возможностью автоматического удаления внешнего префикса шлюза (StripPrefix) перед отправкой запроса во внутренний микросервис.",
    "theory": "API-шлюз служит единым фасадом для десятков внутренних сервисов. Маршрутизация по префиксам путей (Path-based Routing) направляет запросы вида /api/v1/users/* в сервис пользователей, а /api/v1/orders/* — в сервис заказов. Важнейшая операция шлюза — стриппинг префиксов (Strip Prefix): внешний клиент обращается по публичному контракту /api/v1/users/42, однако сам внутренний микросервис пользователей ничего не знает о префиксе /api/v1/users и ожидает запрос на локальный эндпоинт /42. Шлюз отсекает префикс и передает очищенный путь в req.URL.Path.",
    "step_by_step": "1. Спроектируйте структуру RouteRule с полями Prefix, UpstreamURL и флагом StripPrefix.\\n2. Создайте PrefixRouter с потокобезопасным срезом правил.\\n3. Реализуйте метод Match с проверкой strings.HasPrefix и нормализацией слэшей.\\n4. Протестируйте маршрутизацию путей пользователей, заказов и статических файлов.",
    "code_blocks": [{"filename": "path_routing.go", "lang": "go", "code": ex16_code}],
    "under_the_hood": "Для тысяч маршрутов в production вместо линейного перебора среза O(N) используют Radix Tree (префиксное дерево) или хэш-таблицы сегментов путей, что дает сложность поиска O(L), где L — глубина пути в URL.",
    "pitfalls": "Если правило со стриппингом префикса /api оставляет пустую строку вместо '/', веб-сервер бэкенда может вернуть 400 Bad Request. Всегда гарантируйте ведущий слэш: if !strings.HasPrefix(path, '/') { path = '/' + path }.",
    "bigtech_interview": "В чем преимущества единого API Gateway с префиксным роутингом по сравнению с выделением отдельного поддомена для каждого микросервиса (users.company.com vs company.com/users) с точки зрения CORS и мобильных клиентов?"
})

# Ex 17
ex17_code = """package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
)

// CanaryDecisionResult содержит результат маршрутизации трафика.
type CanaryDecisionResult struct {
	UpstreamCluster string
	Reason          string
}

// EvaluateCanaryRouting анализирует заголовки и куки для направления запроса на Canary-кластер.
func EvaluateCanaryRouting(req *http.Request) CanaryDecisionResult {
	// 1. Приоритет: явный заголовок внутреннего тестировщика
	if req.Header.Get("X-Beta-Tester") == "true" {
		return CanaryDecisionResult{
			UpstreamCluster: "http://canary-cluster.internal:8080",
			Reason:          "Header X-Beta-Tester: true",
		}
	}

	// 2. Проверка сессионной куки участия в бета-программе
	if cookie, err := req.Cookie("experiment_group"); err == nil && cookie.Value == "canary" {
		return CanaryDecisionResult{
			UpstreamCluster: "http://canary-cluster.internal:8080",
			Reason:          "Cookie experiment_group=canary",
		}
	}

	// 3. Стандартный продакшн-кластер
	return CanaryDecisionResult{
		UpstreamCluster: "http://prod-stable-cluster.internal:8080",
		Reason:          "Default Production Traffic",
	}
}

func main() {
	// Тест 1: Обычный пользователь
	req1 := httptest.NewRequest(http.MethodGet, "/checkout", nil)
	fmt.Printf("Запрос 1: %s (Причина: %s)\\n", EvaluateCanaryRouting(req1).UpstreamCluster, EvaluateCanaryRouting(req1).Reason)

	// Тест 2: Запрос от QA инженера с заголовком
	req2 := httptest.NewRequest(http.MethodGet, "/checkout", nil)
	req2.Header.Set("X-Beta-Tester", "true")
	fmt.Printf("Запрос 2: %s (Причина: %s)\\n", EvaluateCanaryRouting(req2).UpstreamCluster, EvaluateCanaryRouting(req2).Reason)

	// Тест 3: Клиент с экспериментальной кукой
	req3 := httptest.NewRequest(http.MethodGet, "/checkout", nil)
	req3.AddCookie(&http.Cookie{Name: "experiment_group", Value: "canary"})
	fmt.Printf("Запрос 3: %s (Причина: %s)\\n", EvaluateCanaryRouting(req3).UpstreamCluster, EvaluateCanaryRouting(req3).Reason)
}
"""
validate_go(ex17_code)

exercises.append({
    "num": 17,
    "title": "Маршрутизация по заголовкам и кукам (Header-based Routing)",
    "task": "Реализуйте механизм маршрутизации по метаданным запроса (Header-based & Cookie-based Routing) для Canary-релизов и бета-тестирования. Напишите функцию EvaluateCanaryRouting, направляющую трафик с заголовком X-Beta-Tester: true или кукой experiment_group=canary на экспериментальный кластер.",
    "theory": "Канареечные релизы (Canary Deployments) позволяют протестировать новую версию сервиса на реальных пользователях без риска поломать весь продакшн. API-шлюз — идеальное место для канареечного разделения. Выделяют два подхода к роутингу:\\n1. Весовой (Percentage-based): 5% всех случайных запросов идут на Canary, 95% — на Stable.\\n2. Детерминированный (Header/Cookie/User-ID based): сотрудники компании, QA-инженеры или пользователи из бета-группы помечаются HTTP-заголовком (X-Beta-Tester) или кукой сессии. Шлюз анализирует входящие заголовки и направляет запрос в изолированный upstream-кластер. Это исключает мигание версий (когда один запрос пользователя идет на v1, а следующий на v2).",
    "step_by_step": "1. Спроектируйте структуру CanaryDecisionResult.\\n2. Реализуйте приоритетную проверку кастомного заголовка X-Beta-Tester.\\n3. Добавьте чтение и валидацию HTTP-куки experiment_group через req.Cookie.\\n4. Верните fallback на стабильный кластер при отсутствии признаков бета-трафика.\\n5. Протестируйте все три сценария вызова.",
    "code_blocks": [{"filename": "header_routing.go", "lang": "go", "code": ex17_code}],
    "under_the_hood": "Header-based роутинг позволяет проводить A/B тестирование фронтенда и мобильных приложений без дублирования инсталляций шлюза и без модификации DNS записей.",
    "pitfalls": "Остерегайтесь утечки внутренних тестовых заголовков наружу: очищайте заголовок X-Beta-Tester в ответе или не разрешайте внешним пользователям произвольно переключать кластер без криптографической подписи куки.",
    "bigtech_interview": "Как в современных Service Mesh (Istio VirtualService, Envoy) настраивают Header-based маршрутизацию и Dark Launching (теневой запуск трафика с дублированием запросов через Shadowing)?"
})

# Ex 18
ex18_code = """package main

import (
	"fmt"
	"io"
	"net"
	"net/http"
	"strings"
	"sync"
)

// IsWebSocketRequest проверяет, является ли входящий запрос рукопожатием WebSocket.
func IsWebSocketRequest(req *http.Request) bool {
	containsUpgrade := false
	for _, v := range strings.Split(req.Header.Get("Connection"), ",") {
		if strings.EqualFold(strings.TrimSpace(v), "Upgrade") {
			containsUpgrade = true
			break
		}
	}
	return containsUpgrade && strings.EqualFold(req.Header.Get("Upgrade"), "websocket")
}

// ProxyWebSocketConnection переключает HTTP соединение в двунаправленный сырой TCP поток.
func ProxyWebSocketConnection(w http.ResponseWriter, r *http.Request, targetAddr string) error {
	// 1. Подключаемся к целевому бэкенду по TCP
	backendConn, err := net.Dial("tcp", targetAddr)
	if err != nil {
		http.Error(w, "Backend unavailable", http.StatusBadGateway)
		return err
	}
	defer backendConn.Close()

	// 2. Перехватываем клиентский сокет через http.Hijacker
	hijacker, ok := w.(http.Hijacker)
	if !ok {
		http.Error(w, "Hijacking not supported", http.StatusInternalServerError)
		return fmt.Errorf("webserver doesn't support hijacking")
	}

	clientConn, clientBuf, err := hijacker.Hijack()
	if err != nil {
		return err
	}
	defer clientConn.Close()

	// 3. Пересылаем оригинальный HTTP-запрос рукопожатия бэкенду
	if err := r.Write(backendConn); err != nil {
		return err
	}

	// 4. Двунаправленное копирование байт между клиентским и бэкенд сокетами
	var wg sync.WaitGroup
	wg.Add(2)

	// Клиент -> Бэкенд (учитываем уже буферизованные байты clientBuf)
	go func() {
		defer wg.Done()
		if clientBuf.Reader.Buffered() > 0 {
			_, _ = io.CopyN(backendConn, clientBuf, int64(clientBuf.Reader.Buffered()))
		}
		_, _ = io.Copy(backendConn, clientConn)
	}()

	// Бэкенд -> Клиент
	go func() {
		defer wg.Done()
		_, _ = io.Copy(clientConn, backendConn)
	}()

	wg.Wait()
	return nil
}

func main() {
	req, _ := http.NewRequest(http.MethodGet, "/ws/chat", nil)
	req.Header.Set("Connection", "Upgrade")
	req.Header.Set("Upgrade", "websocket")

	fmt.Printf("Запрос классифицирован как WebSocket Upgrade: %v\\n", IsWebSocketRequest(req))
	fmt.Println("Паттерн Hijacking активирует полнодуплексный TCP туннель между клиентом и бэкендом.")
}
"""
validate_go(ex18_code)

exercises.append({
    "num": 18,
    "title": "Поддержка проксирования WebSockets",
    "task": "Реализуйте прозрачное проксирование WebSockets в Go. Напишите валидатор рукопожатия IsWebSocketRequest, процедуру перехвата сокета через http.Hijacker и организацию полнодуплексного туннеля io.Copy между клиентом и бэкендом с учетом буфера clientBuf.",
    "theory": "Протокол WebSocket начинается как стандартный HTTP GET запрос с заголовками Upgrade: websocket и Connection: Upgrade. После успешного ответа HTTP 101 Switching Protocols соединение переходит из режима запрос-ответ в полнодуплексный бинарный TCP-поток фреймов. Стандартный http.Handler в Go завершает соединение после выхода из функции. Чтобы удержать сокет открытым, прокси использует интерфейс http.Hijacker. Вызов w.(http.Hijacker).Hijack() забирает сырой сетевой сокет net.Conn и буфер чтения bufio.ReadWriter у HTTP-сервера. После этого прокси открывает TCP-сокет к бэкенду и запускает две параллельные горутины io.Copy.",
    "step_by_step": "1. Реализуйте функцию IsWebSocketRequest с регистронезависимой проверкой Connection и Upgrade.\\n2. В ProxyWebSocketConnection откройте TCP-сокет к бэкенду net.Dial.\\n3. Выполните приведение http.ResponseWriter к http.Hijacker и вызовите Hijack().\\n4. Перешлите оригинальный HTTP запрос рукопожатия бэкенду через r.Write(backendConn).\\n5. Запустите двунаправленную перекачку данных через io.Copy с sync.WaitGroup.",
    "code_blocks": [{"filename": "websocket_proxy.go", "lang": "go", "code": ex18_code}],
    "under_the_hood": "Критическая деталь Hijack(): метод возвращает *bufio.ReadWriter. Если клиент уже успел прислать первые WebSocket-фреймы сразу после рукопожатия (Pipelining), они осели во внутреннем буфере clientBuf. Если забыть сбросить clientBuf.Reader.Buffered() в сокет бэкенда, первые пакеты клиента будут безвозвратно потеряны.",
    "pitfalls": "После вызова Hijack() стандартный http.ResponseWriter больше не работает: нельзя вызывать w.WriteHeader() или w.Write(), так как контроль над сокетом полностью передан вызывающему коду.",
    "bigtech_interview": "Почему проксирование миллионов одновременных WebSockets-соединений требует оптимизации размера стека горутин и перехода на epoll/event-loop (gnet) вместо двух горутин io.Copy на каждое соединение?"
})

# Ex 19
ex19_code = """package main

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httputil"
	"net/url"
	"strings"
)

// ConfigureGRPCReverseProxy настраивает сквозное проксирование gRPC трафика.
func ConfigureGRPCReverseProxy(backendURL *url.URL) *httputil.ReverseProxy {
	proxy := httputil.NewSingleHostReverseProxy(backendURL)

	originalDirector := proxy.Director
	proxy.Director = func(req *http.Request) {
		originalDirector(req)
		// gRPC требует точного совпадения authority / host
		req.Host = backendURL.Host
	}

	// Постобработка: сохраняем gRPC трейлеры (grpc-status, grpc-message)
	proxy.ModifyResponse = func(resp *http.Response) error {
		// gRPC передает статус завершения RPC в трейлерах HTTP/2
		return nil
	}

	return proxy
}

// IsGRPCRequest определяет, является ли входящий запрос gRPC вызовом.
func IsGRPCRequest(r *http.Request) bool {
	return r.ProtoMajor == 2 && strings.HasPrefix(r.Header.Get("Content-Type"), "application/grpc")
}

func main() {
	req, _ := http.NewRequest(http.MethodPost, "/com.example.OrderService/CreateOrder", nil)
	req.ProtoMajor = 2
	req.Header.Set("Content-Type", "application/grpc")

	fmt.Printf("Запрос распознан как gRPC: %v (Proto: HTTP/%d, Type: %s)\\n",
		IsGRPCRequest(req), req.ProtoMajor, req.Header.Get("Content-Type"))
	fmt.Println("Для проксирования gRPC без TLS (h2c) сервер Go должен использовать golang.org/x/net/http2/h2c.")
}
"""
validate_go(ex19_code)

exercises.append({
    "num": 19,
    "title": "Сквозное проксирование gRPC (HTTP/2 Cleartext h2c)",
    "task": "Изучите требования к сквозному проксированию gRPC-трафика через API-шлюз на чистом Go. Реализуйте распознавание gRPC-запросов IsGRPCRequest (HTTP/2, Content-Type: application/grpc) и настройку ReverseProxy с сохранением gRPC-трейлеров (grpc-status, grpc-message).",
    "theory": "gRPC базируется строго на протоколе HTTP/2. Он использует специфические возможности HTTP/2:\\n1. Мультиплексирование потоков (Streams) в рамках одного TCP-соединения.\\n2. Бинарный фрейминг (Frame headers) вместо текстовых заголовков.\\n3. HTTP/2 Trailers: статус выполнения RPC (заголовки grpc-status и grpc-message) передается не в начале ответа, а в самом конце после передачи всех данных тела (Trailers / End Stream Flag).\\nПри проксировании gRPC внутри приватного контура без шифрования (Cleartext) используется протокол h2c (HTTP/2 Cleartext). Стандартный http.Server в Go по умолчанию не поддерживает h2c без TLS: для его активации HTTP-обработчик шлюза оборачивают в h2c.NewHandler(mux, &http2.Server{}).",
    "step_by_step": "1. Реализуйте IsGRPCRequest с проверкой ProtoMajor == 2 и Content-Type application/grpc.\\n2. Спроектируйте ConfigureGRPCReverseProxy с фиксацией req.Host.\\n3. Задокументируйте сохранение трейлеров ответа.\\n4. Протестируйте детекцию входящих RPC запросов.",
    "code_blocks": [{"filename": "grpc_proxy.go", "lang": "go", "code": ex19_code}],
    "under_the_hood": "Если прокси-сервер не поддерживает трейлеры и 'съедает' заголовок grpc-status, клиент gRPC не сможет понять результат операции и выбросит ошибку rpc error: code = Internal desc = transport: missing content-type field.",
    "pitfalls": "Использование стандартного http.DefaultClient или транспорта HTTP/1.1 для проксирования gRPC сломает соединение: gRPC клиент получит статус HTTP 415 Unsupported Media Type или ошибку согласования ALPN.",
    "bigtech_interview": "В чем разница между gRPC-Web и чистым gRPC h2c при прохождении через корпоративный API Gateway? Почему для gRPC-Web необходим специальный транслятор трейлеров?"
})

# Ex 20
ex20_code = """package main

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"time"
)

type contextKey string
const UserContextKey contextKey = "auth_user_claims"

// UserClaims описывает данные авторизованного пользователя.
type UserClaims struct {
	UserID string
	Role   string
	Exp    int64
}

// SimpleJWTValidator эмулирует проверку JWT токена на шлюзе.
func SimpleJWTValidator(tokenString string) (*UserClaims, error) {
	// В продакшене здесь вызов jwt.ParseWithClaims(tokenString, ...) с проверкой RSA-256 / Ed25519
	if tokenString != "valid-bearer-token-secret" {
		return nil, errors.New("invalid or expired token signature")
	}
	return &UserClaims{
		UserID: "usr_99182",
		Role:   "senior_engineer",
		Exp:    time.Now().Add(1 * time.Hour).Unix(),
	}, nil
}

// JWTMiddleware проверяет токен и внедряет доверенные заголовки X-User-ID для бэкендов.
func JWTMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" || !strings.HasPrefix(authHeader, "Bearer ") {
			http.Error(w, `{"error":"unauthorized","message":"missing bearer token"}`, http.StatusUnauthorized)
			return
		}

		token := strings.TrimPrefix(authHeader, "Bearer ")
		claims, err := SimpleJWTValidator(token)
		if err != nil {
			http.Error(w, fmt.Sprintf(`{"error":"unauthorized","details":%q}`, err.Error()), http.StatusUnauthorized)
			return
		}

		// Защита: удаляем любые входящие заголовки X-User-*, присланные внешним клиентом (Spoofing)
		r.Header.Del("X-User-ID")
		r.Header.Del("X-User-Role")

		// Инъекция доверенных заголовков для внутренних микросервисов
		r.Header.Set("X-User-ID", claims.UserID)
		r.Header.Set("X-User-Role", claims.Role)

		next.ServeHTTP(w, r)
	})
}

func main() {
	handler := JWTMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = fmt.Fprintf(w, "Успешная авторизация! Внутренние заголовки: User=%s, Role=%s",
			r.Header.Get("X-User-ID"), r.Header.Get("X-User-Role"))
	}))

	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/api/v1/profile", nil)
	req.Header.Set("Authorization", "Bearer valid-bearer-token-secret")
	req.Header.Set("X-User-ID", "hacker_spoofed_id") // Попытка подделки

	handler.ServeHTTP(rec, req)
	fmt.Println("Ответ обработчика после прохождения JWT Middleware:")
	fmt.Println(rec.Body.String())
}
"""
validate_go(ex20_code)

exercises.append({
    "num": 20,
    "title": "Централизованная аутентификация: JWT Middleware на шлюзе",
    "task": "Спроектируйте централизованную аутентификацию на уровне API Gateway. Реализуйте middleware JWTMiddleware, проверяющее заголовок Authorization: Bearer, валидирующее подпись токена, очищающее любые клиентские заголовки X-User-* и инжектирующее проверенные атрибуты пользователя перед отправкой бэкендам.",
    "theory": "В микросервисной архитектуре валидация токенов в каждом отдельном микросервисе создает избыточную нагрузку на CPU (проверка асимметричной криптографии RSA/ECDSA), требует распространения публичных ключей по десяткам репозиториев и повышает риск уязвимостей. Паттерн Token Exchange / Gateway Authentication переносит проверку на границу периметра (Edge):\\n1. Шлюз проверяет подпись JWT, срок действия (exp) и отзыв токена (Blacklist в Redis).\\n2. Шлюз ОБЯЗАТЕЛЬНО удаляет заголовки X-User-ID и X-User-Role, пришедшие из внешнего интернета, для предотвращения атаки Header Injection / Identity Spoofing.\\n3. Шлюз извлекает claims из валидного токена и устанавливает чистые внутренние заголовки: X-User-ID: 101, X-User-Role: admin.\\n4. Внутренние сервисы в изолированной сети доверяют этим заголовкам без повторного дорогостоящего парсинга JWT.",
    "step_by_step": "1. Спроектируйте структуру UserClaims.\\n2. Напишите JWTMiddleware с проверкой наличия заголовка Bearer.\\n3. Реализуйте удаление потенциально скомпрометированных заголовков r.Header.Del.\\n4. Установите проверенные значения X-User-ID и X-User-Role.\\n5. Протестируйте защиту от спуфинга заголовков.",
    "code_blocks": [{"filename": "jwt_gateway.go", "lang": "go", "code": ex20_code}],
    "under_the_hood": "Передача идентификаторов через заголовки X-User-* ускоряет внутренний вызов на микросекунды, так как бэкендам не нужно выполнять операции модульного возведения в степень (RSA) при каждом RPC.",
    "pitfalls": "Если забыть вызвать r.Header.Del(\"X-User-ID\"), злоумышленник может отправить публичный запрос с произвольным X-User-ID: 1 (admin) без токена, и если эндпоинт открыт, получить права администратора.",
    "bigtech_interview": "Как в инфраструктуре Zero Trust организуют доверие между API Gateway и внутренними микросервисами? Почему для межсервисной аутентификации используют mTLS (Spiffe/Spire) вместе с инъекцией заголовков пользователя?"
})

# Ex 21
ex21_code = """package main

import (
	"fmt"
	"sync"
	"time"
)

// SlidingWindowRateLimiter эмулирует алгоритм скользящего окна (Sliding Window Log).
type SlidingWindowRateLimiter struct {
	mu           sync.Mutex
	limitPerMin  int
	requestTimes map[string][]time.Time
}

func NewSlidingWindowRateLimiter(limitPerMinute int) *SlidingWindowRateLimiter {
	return &SlidingWindowRateLimiter{
		limitPerMin:  limitPerMinute,
		requestTimes: make(map[string][]time.Time),
	}
}

// Allow проверяет, укладывается ли клиент в квоту запросов в скользящем окне 1 минута.
func (l *SlidingWindowRateLimiter) Allow(clientID string) (bool, int) {
	l.mu.Lock()
	defer l.mu.Unlock()

	now := time.Now()
	windowStart := now.Add(-1 * time.Minute)

	// 1. Очищаем устаревшие метки времени, вышедшие за пределы 60-секундного окна
	var active []time.Time
	for _, t := range l.requestTimes[clientID] {
		if t.After(windowStart) {
			active = append(active, t)
		}
	}

	// 2. Проверяем превышение лимита
	if len(active) >= l.limitPerMin {
		l.requestTimes[clientID] = active
		return false, 0
	}

	// 3. Регистрируем текущий запрос
	active = append(active, now)
	l.requestTimes[clientID] = active
	remaining := l.limitPerMin - len(active)
	return true, remaining
}

func main() {
	// Лимит: 3 запроса в минуту для клиента
	limiter := NewSlidingWindowRateLimiter(3)
	client := "client_ip_192.168.1.10"

	fmt.Println("Тестирование Sliding Window Rate Limiting:")
	for i := 1; i <= 5; i++ {
		allowed, remaining := limiter.Allow(client)
		fmt.Printf("Запрос #%d: разрешен=%v (осталось в окне: %d)\\n", i, allowed, remaining)
	}
}
"""
validate_go(ex21_code)

exercises.append({
    "num": 21,
    "title": "Распределенный Rate Limiter per Route на базе Redis",
    "task": "Изучите алгоритм скользящего окна (Sliding Window Log) для ограничения частоты запросов. Реализуйте структуру SlidingWindowRateLimiter, очищающую устаревшие временные метки за пределами минутного окна и отклоняющую запросы при исчерпании квоты клиента.",
    "theory": "Ограничение скорости (Rate Limiting) на API-шлюзе предотвращает перегрузку бэкендов и защищает от брутфорса. Недостаток простого Fixed Window: на границе двух минут (в 00:59 и 01:00) клиент может совершить двойной объем запросов (Burst Traffic), перегрузив систему. Алгоритм Sliding Window Log лишен этого недостатка: он учитывает точное скользящее окно (например, последние 60 секунд от текущего мгновения). В распределенной среде на Redis это реализуется структурой Sorted Set (ZSET) с выполнением атомарного Lua-скрипта:\\n1. ZREMRANGEBYSCORE key 0 (now - window)\\n2. ZCARD key -> проверка на limit\\n3. ZADD key now now -> добавление текущего запроса\\n4. EXPIRE key window",
    "step_by_step": "1. Спроектируйте структуру SlidingWindowRateLimiter с картой слайсов time.Time.\\n2. В методе Allow вычислите границу скользящего окна now.Add(-1 * time.Minute).\\n3. Отфильтруйте устаревшие метки времени.\\n4. Проверьте число активных запросов на соответствие лимиту.\\n5. Добавьте текущее время и верните оставшуюся квоту.",
    "code_blocks": [{"filename": "sliding_window_limiter.go", "lang": "go", "code": ex21_code}],
    "under_the_hood": "Выполнение логики через Redis Lua-скрипт гарантирует атомарность: ни один параллельный запрос от других инстансов шлюза не сможет вклиниться между проверкой счетчика и его инкрементом.",
    "pitfalls": "Хранение временных меток в Sorted Set потребляет много памяти при миллионах запросов. Для сверхвысоких нагрузок используют приближенный алгоритм Sliding Window Counter (комбинацию предыдущего и текущего счетчика с весовым коэффициентом).",
    "bigtech_interview": "В чем разница между алгоритмами Token Bucket, Leaky Bucket и Sliding Window Counter? Какой из них лучше подходит для сглаживания всплесков трафика (traffic shaping)?"
})

# Ex 22
ex22_code = """package main

import (
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

type CircuitState int
const (
	StateClosed CircuitState = iota
	StateHalfOpen
	StateOpen
)

var ErrCircuitBreakerOpen = errors.New("circuit breaker is open: upstream unhealthy")

// CircuitBreaker защищает шлюз от каскадного падения при деградации микросервиса.
type CircuitBreaker struct {
	mu           sync.Mutex
	state        CircuitState
	failureCount int
	threshold    int
	timeout      time.Duration
	openedAt     time.Time
}

func NewCircuitBreaker(threshold int, timeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		state:     StateClosed,
		threshold: threshold,
		timeout:   timeout,
	}
}

func (cb *CircuitBreaker) Execute(fn func() error) error {
	cb.mu.Lock()
	now := time.Now()

	// 1. Проверяем состояние цепи
	if cb.state == StateOpen {
		if now.Sub(cb.openedAt) > cb.timeout {
			cb.state = StateHalfOpen
			fmt.Println("--> Circuit Breaker: переход в состояние Half-Open (пробный запрос)...")
		} else {
			cb.mu.Unlock()
			return ErrCircuitBreakerOpen
		}
	}
	cb.mu.Unlock()

	// 2. Выполняем реальный вызов к бэкенду
	err := fn()

	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err != nil {
		cb.failureCount++
		if cb.failureCount >= cb.threshold || cb.state == StateHalfOpen {
			cb.state = StateOpen
			cb.openedAt = time.Now()
			fmt.Printf("--> Circuit Breaker: РАЗМЫКАНИЕ ЦЕПИ (Open)! Сбоев: %d, тайм-аут: %v\\n", cb.failureCount, cb.timeout)
		}
		return err
	}

	// 3. При успехе в Half-Open закрываем цепь обратно
	if cb.state == StateHalfOpen || cb.state == StateClosed {
		cb.state = StateClosed
		cb.failureCount = 0
	}
	return nil
}

func main() {
	// Размыкание после 2 сбоев подряд, таймаут 200 мс
	cb := NewCircuitBreaker(2, 200*time.Millisecond)

	failFn := func() error { return errors.New("500 internal server error") }
	successFn := func() error { return nil }

	_ = cb.Execute(failFn)
	_ = cb.Execute(failFn) // Цепь разомкнулась

	// Следующий вызов отсекается мгновенно без обращения к бэкенду
	err := cb.Execute(successFn)
	fmt.Printf("Быстрый отказ (Fast-Fail): %v\\n", err)
}
"""
validate_go(ex22_code)

exercises.append({
    "num": 22,
    "title": "Паттерн Circuit Breaker на уровне API Gateway",
    "task": "Реализуйте паттерн размыкателя цепи (Circuit Breaker) на уровне маршрутов API-шлюза. Спроектируйте автомат состояний (Closed, Open, Half-Open), отсекающий обращения к упавшему микросервису с ошибкой ErrCircuitBreakerOpen без расхода сетевых соединений и ожидания таймаутов.",
    "theory": "Когда микросервис начинает деградировать (перегрузка БД, deadlock пула), входящие запросы шлюза начинают висеть до исчерпания таймаута (например, 10 секунд). Тысячи подвисших запросов исчерпывают стек горутин и сокетов самого шлюза, вызывая каскадный коллапс всей системы (Cascading Failure). Паттерн Circuit Breaker изолирует сбой:\\n- Closed (замкнута): запросы проходят штатно, счетчик сбоев сбрасывается при успехах.\\n- Open (разомкнута): при превышении порога сбоев цепь размыкается. Шлюз мгновенно возвращает клиентам ошибку 503 Service Unavailable (Fast Fail) без отправки запроса бэкенду, давая сервису время восстановиться.\\n- Half-Open (полуоткрыта): по истечении таймаута восстановления шлюз пропускает один пробный запрос (Canary Probe). Если он успешен — цепь замыкается (Closed); если завершился ошибкой — цепь снова размыкается (Open).",
    "step_by_step": "1. Объявите состояния StateClosed, StateHalfOpen, StateOpen и ошибку ErrCircuitBreakerOpen.\\n2. Спроектируйте структуру CircuitBreaker с полями счетчика сбоев, порога и времени открытия.\\n3. Реализуйте метод Execute с проверкой истечения периода таймаута цепи.\\n4. Напишите логику перевода в Open при сбое и в Closed при успехе в режиме Half-Open.\\n5. Протестируйте механизм быстрого отказа (Fast Fail).",
    "code_blocks": [{"filename": "circuit_breaker.go", "lang": "go", "code": ex22_code}],
    "under_the_hood": "Мгновенный возврат 503 защищает шлюз от накопления очередей горутин (Goroutine Leaks), сохраняя способность обслуживать здоровые сервисы кластера.",
    "pitfalls": "Не размыкайте цепь при ошибках валидации клиента (HTTP 400 Bad Request, 404 Not Found): учитывайте только сетевые таймауты, обрывы соединений и ошибки 5xx бэкенда.",
    "bigtech_interview": "Почему Circuit Breaker обязательно должен комбинироваться с Exponential Backoff и Jitter при повторных попытках (Retry)? Как избежать шторма повторных запросов (Retry Storm)?"
})

# Ex 23
ex23_code = """package main

import (
	"compress/gzip"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
)

// GzipWriterPool оптимизирует выделение памяти под компрессоры gzip.
var gzipPool = sync.Pool{
	New: func() interface{} {
		w, _ := gzip.NewWriterLevel(io.Discard, gzip.BestSpeed)
		return w
	},
}

type gzipResponseWriter struct {
	http.ResponseWriter
	writer *gzip.Writer
}

func (w *gzipResponseWriter) Write(b []byte) (int, error) {
	return w.writer.Write(b)
}

// CompressionMiddleware динамически сжимает JSON и текстовые ответы.
func CompressionMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Проверяем поддержку gzip клиентом
		if !strings.Contains(r.Header.Get("Accept-Encoding"), "gzip") {
			next.ServeHTTP(w, r)
			return
		}

		gzWriter := gzipPool.Get().(*gzip.Writer)
		defer gzipPool.Put(gzWriter)

		gzWriter.Reset(w)
		defer gzWriter.Close()

		w.Header().Set("Content-Encoding", "gzip")
		w.Header().Del("Content-Length") // Длина сжатого тела неизвестна заранее
		w.Header().Set("Vary", "Accept-Encoding")

		gzw := &gzipResponseWriter{ResponseWriter: w, writer: gzWriter}
		next.ServeHTTP(gzw, r)
	})
}

func main() {
	payload := `{"status":"ok","items":[` + strings.Repeat(`{"id":1,"name":"Go book"},`, 50) + `{}]}`

	handler := CompressionMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(payload))
	}))

	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/catalog", nil)
	req.Header.Set("Accept-Encoding", "gzip, deflate")

	handler.ServeHTTP(rec, req)

	fmt.Printf("Исходный размер: %d байт\\n", len(payload))
	fmt.Printf("Размер после сжатия gzip: %d байт (сжатие на %.1f%%)\\n",
		rec.Body.Len(), (1.0-float64(rec.Body.Len())/float64(len(payload)))*100)
	fmt.Printf("Header Content-Encoding: %s\\n", rec.Header().Get("Content-Encoding"))
	fmt.Printf("Header Vary: %s\\n", rec.Header().Get("Vary"))
}
"""
validate_go(ex23_code)

exercises.append({
    "num": 23,
    "title": "Динамическое сжатие HTTP-ответов (Gzip / Brotli / zstd)",
    "task": "Реализуйте middleware динамического сжатия ответов CompressionMiddleware с использованием пула компрессоров sync.Pool (gzip.BestSpeed). Обеспечьте проверку заголовка Accept-Encoding, установку заголовков Content-Encoding, Vary и очистку устаревшего Content-Length.",
    "theory": "Сжатие ответов (HTTP Compression) на уровне API Gateway снижает сетевой трафик между шлюзом и мобильными/веб-клиентами на 60–85%, ускоряя загрузку страниц. Однако компрессия требует процессорного времени. Тюнинг сжатия:\\n1. Уровень сжатия: используйте gzip.BestSpeed (уровень 1) вместо gzip.BestCompression (уровень 9). Первый уровень дает 90% эффекта сжатия, потребляя в 4–5 раз меньше CPU.\\n2. sync.Pool для gzip.Writer: создание нового gzip.Writer аллоцирует десятки килобайт внутренней памяти. Пул с вызовом Reset(w) снижает аллокации до нуля.\\n3. Заголовок Vary: Accept-Encoding: обязателен для предотвращения ситуации, когда промежуточные CDN кэшируют сжатый ответ и отдают его клиенту, не поддерживающему gzip.\\n4. Content-Length: старое значение длины несжатого тела бэкенда должно быть удалено, так как сжатое тело имеет другой размер.",
    "step_by_step": "1. Создайте глобальный gzipPool на базе sync.Pool с уровнем BestSpeed.\\n2. Спроектируйте gzipResponseWriter, перехватывающий вызовы Write.\\n3. В middleware проверьте заголовок Accept-Encoding на наличие 'gzip'.\\n4. Установите Content-Encoding: gzip и Vary: Accept-Encoding, удалите Content-Length.\\n5. Замерьте степень сжатия JSON документа.",
    "code_blocks": [{"filename": "compression.go", "lang": "go", "code": ex23_code}],
    "under_the_hood": "Вызов gzWriter.Close() сбрасывает контрольную сумму CRC32 и завершающий блок Deflate в сокет. Важно делать defer gzWriter.Close() до возврата управления из middleware.",
    "pitfalls": "Никогда не сжимайте ответы размером меньше 1 КБ: накладные расходы на заголовок gzip и таблицу Хаффмана сделают сжатый ответ больше оригинала.",
    "bigtech_interview": "Почему алгоритм Brotli (br) превосходит Gzip для статических веб-ассетов, а zstd становится новым стандартом для внутренних межсервисных RPC?"
})

# Ex 24
ex24_code = """package main

import (
	"crypto/sha256"
	"fmt"
	"net/http"
	"net/http/httptest"
	"sync"
)

// CachedResponse инкапсулирует сохраненный ответ шлюза.
type CachedResponse struct {
	ETag        string
	ContentType string
	Body        []byte
}

// GatewayCacheProxy реализует кэширование на базе ETag и условных запросов If-None-Match.
type GatewayCacheProxy struct {
	mu    sync.RWMutex
	cache map[string]CachedResponse
}

func NewGatewayCacheProxy() *GatewayCacheProxy {
	return &GatewayCacheProxy{cache: make(map[string]CachedResponse)}
}

func (c *GatewayCacheProxy) CalculateETag(body []byte) string {
	h := sha256.Sum256(body)
	return fmt.Sprintf(`W/"%x"`, h[:8])
}

func (c *GatewayCacheProxy) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	cacheKey := r.URL.RequestURI()

	// 1. Проверяем наличие закэшированного ответа
	c.mu.RLock()
	cached, ok := c.cache[cacheKey]
	c.mu.RUnlock()

	if ok {
		// Проверяем заголовок клиента If-None-Match (условный запрос)
		if r.Header.Get("If-None-Match") == cached.ETag {
			// Ресурс не изменился: возвращаем 304 Not Modified без тела
			w.WriteHeader(http.StatusNotModified)
			return
		}

		// Отдаем ответ из кэша шлюза без обращения к бэкенду
		w.Header().Set("ETag", cached.ETag)
		w.Header().Set("Content-Type", cached.ContentType)
		w.Header().Set("X-Cache", "HIT")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write(cached.Body)
		return
	}

	// 2. Имитация ответа от реального бэкенда (Cache MISS)
	backendData := []byte(fmt.Sprintf(`{"config_version":"v42","timestamp":%d}`, 1718000000))
	etag := c.CalculateETag(backendData)

	c.mu.Lock()
	c.cache[cacheKey] = CachedResponse{
		ETag:        etag,
		ContentType: "application/json",
		Body:        backendData,
	}
	c.mu.Unlock()

	w.Header().Set("ETag", etag)
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Cache", "MISS")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(backendData)
}

func main() {
	proxy := NewGatewayCacheProxy()

	// 1. Первый запрос: Cache MISS
	rec1 := httptest.NewRecorder()
	req1 := httptest.NewRequest(http.MethodGet, "/api/v1/config", nil)
	proxy.ServeHTTP(rec1, req1)
	etag := rec1.Header().Get("ETag")
	fmt.Printf("Запрос 1: Status=%d, X-Cache=%s, ETag=%s\\n", rec1.Code, rec1.Header().Get("X-Cache"), etag)

	// 2. Второй условный запрос с If-None-Match: HTTP 304
	rec2 := httptest.NewRecorder()
	req2 := httptest.NewRequest(http.MethodGet, "/api/v1/config", nil)
	req2.Header.Set("If-None-Match", etag)
	proxy.ServeHTTP(rec2, req2)
	fmt.Printf("Запрос 2 (условный): Status=%d (Not Modified, трафик тела=0 байт)\\n", rec2.Code)
}
"""
validate_go(ex24_code)

exercises.append({
    "num": 24,
    "title": "HTTP Caching на шлюзе: поддержка ETag и Cache-Control",
    "task": "Реализуйте кэширующий прокси GatewayCacheProxy с поддержкой спецификации HTTP Caching: генерация слабого ETag (W/\"hash\"), валидация условного запроса клиента If-None-Match и возврат легковесного ответа 304 Not Modified без передачи тела.",
    "theory": "Кэширование на API Gateway снижает нагрузку на базы данных бэкенда до 90% для редко изменяемых данных (каталог товаров, конфигурации приложений, курсы валют). Механизм условных запросов (Conditional Requests):\\n1. При первом ответе шлюз или бэкенд возвращает заголовок ETag (Entity Tag) — криптографический хэш версии документа, и кэширует ответ.\\n2. Браузер или мобильный клиент сохраняет документ в локальном кэше вместе с ETag.\\n3. При повторном запросе клиент передает заголовок If-None-Match: \"etag_value\".\\n4. Шлюз проверяет ETag: если хэш совпадает, шлюз возвращает статус HTTP 304 Not Modified с пустым телом ответа. Это экономит трафик мобильного интернета и устраняет необходимость повторной сериализации данных.",
    "step_by_step": "1. Спроектируйте CachedResponse с полями ETag, ContentType и Body.\\n2. Создайте GatewayCacheProxy с кэшем в памяти и sync.RWMutex.\\n3. Реализуйте генерацию хэша CalculateETag на базе sha256.\\n4. В ServeHTTP проверьте заголовок If-None-Match и верните 304 при совпадении.\\n5. Протестируйте Cache MISS при первом обращении и 304 Not Modified при повторном.",
    "code_blocks": [{"filename": "http_cache.go", "lang": "go", "code": ex24_code}],
    "under_the_hood": "Префикс W/ в ETag (W/\"...\") означает 'слабый ETag' (Weak Validator): он гарантирует семантическую эквивалентность данных, даже если байтовое представление незначительно отличается (например, другой порядок ключей JSON или сжатие).",
    "pitfalls": "Никогда не кэшируйте ответы, содержащие заголовок Set-Cookie или персонализированные данные пользователей: установите Cache-Control: private, no-cache.",
    "bigtech_interview": "В чем разница между заголовками Cache-Control: max-age=300 и ETag / If-None-Match? Какой из них полностью устраняет сетевой запрос к шлюзу, а какой лишь экономит трафик ответа?"
})

# Ex 25
ex25_code = """package main

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
)

// GenerateRandomHex генерирует случайную шестнадцатеричную строку заданной длины байт.
func GenerateRandomHex(bytesCount int) string {
	b := make([]byte, bytesCount)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}

// W3CTraceContextMiddleware инжектирует или пробрасывает стандартизированный заголовок traceparent.
func W3CTraceContextMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		traceparent := r.Header.Get("traceparent")

		var traceID, parentSpanID string
		if traceparent != "" {
			// Формат W3C: version-trace_id-parent_id-trace_flags (например: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01)
			parts := strings.Split(traceparent, "-")
			if len(parts) == 4 && parts[0] == "00" && len(parts[1]) == 32 && len(parts[2]) == 16 {
				traceID = parts[1]
				parentSpanID = parts[2]
			}
		}

		// Если заголовок отсутствует или некорректен — генерируем новый корневой TraceID
		if traceID == "" {
			traceID = GenerateRandomHex(16)      // 16 байт = 32 hex символа
			parentSpanID = GenerateRandomHex(8) // 8 байт = 16 hex символов
			traceparent = fmt.Sprintf("00-%s-%s-01", traceID, parentSpanID)
		}

		// Создаем новый SpanID для вызова следующего микросервиса
		gatewaySpanID := GenerateRandomHex(8)
		outgoingTraceparent := fmt.Sprintf("00-%s-%s-01", traceID, gatewaySpanID)

		// Инжектируем в исходящие заголовки к бэкенду
		r.Header.Set("traceparent", outgoingTraceparent)
		// Возвращаем Trace-ID клиенту для сквозного траблшутинга
		w.Header().Set("X-Trace-ID", traceID)

		next.ServeHTTP(w, r)
	})
}

func main() {
	handler := W3CTraceContextMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = fmt.Fprintf(w, "Проброшенный traceparent к бэкенду: %s", r.Header.Get("traceparent"))
	}))

	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/orders/place", nil)

	handler.ServeHTTP(rec, req)

	fmt.Printf("Клиент получил X-Trace-ID: %s\\n", rec.Header().Get("X-Trace-ID"))
	fmt.Println("Тело ответа:", rec.Body.String())
}
"""
validate_go(ex25_code)

exercises.append({
    "num": 25,
    "title": "Сквозная трассировка: инъекция W3C Trace Context",
    "task": "Реализуйте стандарт сквозной распределенной трассировки W3C Trace Context (traceparent) на шлюзе. Напишите middleware, проверяющее входящий заголовок, генерирующее новый 128-битный TraceID при его отсутствии, формирующее новый SpanID шлюза и возвращающее клиенту заголовок X-Trace-ID.",
    "theory": "Сквозная трассировка (Distributed Tracing) критически необходима в микросервисной архитектуре, где один клиентский клик инициирует десятки межсервисных вызовов. Стандарт W3C Trace Context определяет формат заголовка:\\ntraceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01\\nПоля:\\n- 00: текущая версия стандарта W3C.\\n- 4bf...36: 128-битный TraceID (32 hex-символа), сквозной уникальный идентификатор транзакции через все микросервисы.\\n- 00f...b7: 64-битный ParentSpanID (16 hex-символов), идентификатор вызывающего спана.\\n- 01: флаги трассировки (TraceFlags, 01 = сэмплирование включено, спан пишется в Jaeger/Tempo).\\nШлюз генерирует корневой спан, инжектирует заголовок во внутренние микросервисы и отдает TraceID клиенту в заголовке ответа X-Trace-ID для удобного расследования жалоб пользователей в службе поддержки.",
    "step_by_step": "1. Напишите генератор случайных hex-строк GenerateRandomHex.\\n2. Спроектируйте W3CTraceContextMiddleware.\\n3. Распарсите входящий traceparent по разделителю '-' и проверьте валидность версии 00.\\n4. При отсутствии заголовка сгенерируйте 16-байтный TraceID.\\n5. Сформируйте исходящий traceparent с новым SpanID шлюза и отдайте X-Trace-ID клиенту.",
    "code_blocks": [{"filename": "w3c_trace_context.go", "lang": "go", "code": ex25_code}],
    "under_the_hood": "В продакшене OpenTelemetry Go SDK (go.opentelemetry.io/otel/propagation) автоматически выполняет проброс и извлечение контекста (Extract/Inject), но понимание бинарного формата W3C необходимо для низкоуровневой отладки сетевых дампов tcpdump.",
    "pitfalls": "Если сгенерировать TraceID из одних нулей (00000000000000000000000000000000), стандарт W3C признает заголовок невалидным, и downstream-сервисы сбросят трассировку.",
    "bigtech_interview": "Как в системах высокой нагрузки (Яндекс, Uber) настраивают вероятностное сэмплирование трассировки (Trace Sampling), чтобы записывать в хранилище Jaeger/Tempo не 100% запросов, а 0.1% успешных и 100% ошибочных?"
})

# Ex 26
ex26_code = """package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"strconv"
	"sync/atomic"
	"time"
)

// GatewayPrometheusMetrics аккумулирует ключевые метрики шлюза.
type GatewayPrometheusMetrics struct {
	TotalRequests      atomic.Uint64
	Status2xxRequests  atomic.Uint64
	Status5xxRequests  atomic.Uint64
	ActiveConnections  atomic.Int64
	TotalDurationMicro atomic.Uint64
}

func (m *GatewayPrometheusMetrics) RecordRequest(status int, duration time.Duration) {
	m.TotalRequests.Add(1)
	m.TotalDurationMicro.Add(uint64(duration.Microseconds()))

	if status >= 200 && status < 300 {
		m.Status2xxRequests.Add(1)
	} else if status >= 500 {
		m.Status5xxRequests.Add(1)
	}
}

// MetricsMiddleware собирает метрики времени выполнения и кодов статусов.
func (m *GatewayPrometheusMetrics) MetricsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		m.ActiveConnections.Add(1)
		defer m.ActiveConnections.Add(-1)

		start := time.Now()
		rec := &statusRecorder{ResponseWriter: w, statusCode: http.StatusOK}
		next.ServeHTTP(rec, r)

		m.RecordRequest(rec.statusCode, time.Since(start))
	})
}

type statusRecorder struct {
	http.ResponseWriter
	statusCode int
}

func (r *statusRecorder) WriteHeader(code int) {
	r.statusCode = code
	r.ResponseWriter.WriteHeader(code)
}

func (m *GatewayPrometheusMetrics) FormatPrometheusText() string {
	return fmt.Sprintf(
		"# HELP gateway_requests_total Total HTTP requests handled by gateway.\\n"+
			"# TYPE gateway_requests_total counter\\n"+
			"gateway_requests_total{status=\\"2xx\\"} %d\\n"+
			"gateway_requests_total{status=\\"5xx\\"} %d\\n"+
			"# HELP gateway_active_connections Current in-flight requests.\\n"+
			"# TYPE gateway_active_connections gauge\\n"+
			"gateway_active_connections %d\\n",
		m.Status2xxRequests.Load(),
		m.Status5xxRequests.Load(),
		m.ActiveConnections.Load(),
	)
}

func main() {
	metrics := &GatewayPrometheusMetrics{}
	handler := metrics.MetricsMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	}))

	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	handler.ServeHTTP(rec, req)

	fmt.Println("Сгенерированный Prometheus Text Format:")
	fmt.Print(metrics.FormatPrometheusText())
}
"""
validate_go(ex26_code)

exercises.append({
    "num": 26,
    "title": "Мониторинг шлюза: экспорт Prometheus метрик",
    "task": "Оснастите API-шлюз Prometheus-метриками. Спроектируйте структуру GatewayPrometheusMetrics с атомарными счетчиками для подсчета общего числа запросов, распределения по статусам (2xx, 5xx), отслеживания активных In-Flight соединений и экспорта в текстовом формате Prometheus.",
    "theory": "API-шлюз — первый рубеж мониторинга доступности всей платформы. Золотые сигналы SRE (Google SRE Golden Signals) на шлюзе:\\n1. Трафик (Traffic): счетчик gateway_requests_total{route, method, status}.\\n2. Ошибки (Errors): процент ответов 5xx (SLO Error Budget).\\n3. Задержка (Latency): гистограмма gateway_request_duration_seconds с бакетами p50, p90, p99.\\n4. Насыщение (Saturation): gauge gateway_active_connections (число зависших соединений).\\nМетрики должны собираться потокобезопасно без блокировки запросов, используя атомарные примитивы sync/atomic или промотеевские структуры client_golang.",
    "step_by_step": "1. Спроектируйте структуру GatewayPrometheusMetrics со счетчиками atomic.Uint64 и atomic.Int64.\\n2. Реализуйте статус-рекордер statusRecorder для перехвата кода возврата w.WriteHeader.\\n3. Создайте MetricsMiddleware для замера времени выполнения time.Since(start).\\n4. Напишите метод FormatPrometheusText с экспортом стандартного текстового формата.\\n5. Протестируйте сбор метрик при прохождении запроса.",
    "code_blocks": [{"filename": "prometheus_metrics.go", "lang": "go", "code": ex26_code}],
    "under_the_hood": "Метрика активных соединений (Active Connections) инкрементируется при входе в обработчик и декрементируется через defer. Это позволяет детектировать утечки горутин и DoS-атаки 'Slowloris'.",
    "pitfalls": "Опасность взрыва кардинальности (High Cardinality): никогда не добавляйте User-ID или сырой путь /orders/123456 в метки Prometheus! Используйте только шаблоны маршрутов: route=\"/orders/{id}\".",
    "bigtech_interview": "Как рассчитать процент доступности сервиса (SLO Availability) в Prometheus PromQL по метрикам API Gateway за 30-дневное скользящее окно?"
})

# Ex 27
ex27_code = """package main

import (
	"context"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"os"
	"time"
)

// AccessLogMiddleware генерирует структурированный JSON-лог доступа на базе log/slog.
func AccessLogMiddleware(logger *slog.Logger, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		rec := &logStatusRecorder{ResponseWriter: w, status: http.StatusOK}

		next.ServeHTTP(rec, r)

		duration := time.Since(start)

		// Логируем структурированную запись в формате JSON
		logger.LogAttrs(
			r.Context(),
			slog.LevelInfo,
			"HTTP_REQUEST",
			slog.String("remote_ip", r.RemoteAddr),
			slog.String("method", r.Method),
			slog.String("path", r.URL.Path),
			slog.Int("status", rec.status),
			slog.Int64("bytes_sent", rec.bytesWritten),
			slog.Float64("duration_ms", float64(duration.Microseconds())/1000.0),
			slog.String("user_agent", r.UserAgent()),
			slog.String("trace_id", r.Header.Get("X-Trace-ID")),
		)
	})
}

type logStatusRecorder struct {
	http.ResponseWriter
	status       int
	bytesWritten int64
}

func (r *logStatusRecorder) WriteHeader(code int) {
	r.status = code
	r.ResponseWriter.WriteHeader(code)
}

func (r *logStatusRecorder) Write(b []byte) (int, error) {
	n, err := r.ResponseWriter.Write(b)
	r.bytesWritten += int64(n)
	return n, err
}

func main() {
	jsonLogger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))

	handler := AccessLogMiddleware(jsonLogger, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"result":"processed"}`))
	}))

	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/api/v1/users/99", nil)
	req.RemoteAddr = "10.0.0.1:43210"
	req.Header.Set("User-Agent", "GatewayBench/2.0")
	req.Header.Set("X-Trace-ID", "4bf92f3577b34da6a3ce929d0e0e4736")

	handler.ServeHTTP(rec, req)
}
"""
validate_go(ex27_code)

exercises.append({
    "num": 27,
    "title": "Структурированный Access Log на базе log/slog",
    "task": "Реализуйте высокопроизводительный структурированный Access Log на базе стандартного пакета Go log/slog. Спроектируйте middleware AccessLogMiddleware, логирующее поля remote_ip, method, path, status, bytes_sent, duration_ms, trace_id в формате JSON без паразитных аллокаций памяти.",
    "theory": "Журнал доступа (Access Log) шлюза — главный источник данных для систем анализа безопасности (SIEM), антифрода и аудита SLA. Традиционное форматирование логов через fmt.Sprintf('%s %s ...') порождает сотни тысяч строковых аллокаций в секунду, перегружая сборщик мусора Go. Стандартный пакет log/slog (начиная с Go 1.21) предоставляет метод logger.LogAttrs с типизированными атрибутами slog.Attr (slog.Int, slog.String, slog.Float64). Атрибуты хранятся на стеке без динамического выделения памяти в куче (Zero-allocation logging).",
    "step_by_step": "1. Инициализируйте slog.NewJSONHandler с выводом в os.Stdout.\\n2. Спроектируйте logStatusRecorder для перехвата статуса и числа записанных байт.\\n3. В AccessLogMiddleware вычислите задержку duration_ms.\\n4. Вызовите logger.LogAttrs с типизированными атрибутами запроса.\\n5. Протестируйте генерацию валидной JSON-строки лога.",
    "code_blocks": [{"filename": "access_log.go", "lang": "go", "code": ex27_code}],
    "under_the_hood": "slog.LogAttrs принимает параметры по значению (value-receiver) в структуре slog.Attr, избегая упаковки аргументов в пустой интерфейс any (eface), что устраняет аллокации памяти в рантайме.",
    "pitfalls": "Логирование паролей или токенов авторизации: исключите заголовок Authorization и тело запроса из Access Log во избежание утечки персональных данных и нарушения стандартов PCI-DSS.",
    "bigtech_interview": "Почему в HighLoad системах логирование доступа настраивают асинхронно через буферизованные кольцевые очереди (Ring Buffer / Channel) с возможностью сброса логов (drop on overflow) при всплесках нагрузки?"
})

# Ex 28
ex28_code = """package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
)

// RouteConfig инкапсулирует активную конфигурацию маршрутизации.
type RouteConfig struct {
	Version string
	Routes  map[string]string
}

// HotReloadGateway управляет таблицей маршрутизации с атомарным обновлением.
type HotReloadGateway struct {
	routes atomic.Pointer[RouteConfig]
}

func NewHotReloadGateway(initialVersion string, initialRoutes map[string]string) *HotReloadGateway {
	gw := &HotReloadGateway{}
	gw.routes.Store(&RouteConfig{
		Version: initialVersion,
		Routes:  initialRoutes,
	})
	return gw
}

// ReloadRouteTable атомарно подменяет конфигурацию без блокировки входящих запросов.
func (gw *HotReloadGateway) ReloadRouteTable(newVersion string, newRoutes map[string]string) {
	newCfg := &RouteConfig{
		Version: newVersion,
		Routes:  newRoutes,
	}
	old := gw.routes.Swap(newCfg)
	fmt.Printf("--> [HOT RELOAD]: Маршруты обновлены с %s до %s (маршрутов: %d)\\n",
		old.Version, newCfg.Version, len(newCfg.Routes))
}

func (gw *HotReloadGateway) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// Lock-free чтение текущей активной конфигурации
	cfg := gw.routes.Load()

	upstream, ok := cfg.Routes[r.URL.Path]
	if !ok {
		http.Error(w, "Route not found", http.StatusNotFound)
		return
	}

	w.Header().Set("X-Gateway-Version", cfg.Version)
	w.WriteHeader(http.StatusOK)
	_, _ = fmt.Fprintf(w, "Проксирование на: %s", upstream)
}

func main() {
	gw := NewHotReloadGateway("v1.0", map[string]string{
		"/users": "http://users-v1.internal:8080",
	})

	// 1. Запрос к версии 1
	rec1 := httptest.NewRecorder()
	req1 := httptest.NewRequest(http.MethodGet, "/users", nil)
	gw.ServeHTTP(rec1, req1)
	fmt.Printf("Вызов 1: %s (версия %s)\\n", rec1.Body.String(), rec1.Header().Get("X-Gateway-Version"))

	// 2. Горячее обновление маршрутов без остановки сервиса
	gw.ReloadRouteTable("v2.0-canary", map[string]string{
		"/users":  "http://users-v2-canary.internal:8080",
		"/orders": "http://orders.internal:8080",
	})

	// 3. Запрос к обновленным маршрутам
	rec2 := httptest.NewRecorder()
	req2 := httptest.NewRequest(http.MethodGet, "/users", nil)
	gw.ServeHTTP(rec2, req2)
	fmt.Printf("Вызов 2: %s (версия %s)\\n", rec2.Body.String(), rec2.Header().Get("X-Gateway-Version"))
}
"""
validate_go(ex28_code)

exercises.append({
    "num": 28,
    "title": "Горячая перезагрузка конфигурации маршрутов (Hot Reload)",
    "task": "Реализуйте механизм горячего обновления таблицы маршрутизации API-шлюза (Zero-Downtime Hot Reload). Спроектируйте структуру HotReloadGateway на базе atomic.Pointer[RouteConfig], обеспечивающую мгновенную замену карты маршрутов без разрыва активных соединений и без блокировок мьютексов.",
    "theory": "В облачных окружениях топология микросервисов меняется непрерывно: развертываются новые сервисы, запускаются Canary-реплики, обновляются квоты. Перезапуск процесса шлюза для обновления конфигурации недопустим, так как он сбрасывает Keep-Alive сокеты клиентов и прерывает фоновые потоки. Идиоматичное решение в Go — атомарный указатель atomic.Pointer[T]. При получении новой конфигурации (через gRPC xDS, etcd watcher или REST API) шлюз компилирует новую иммутабельную (immutable) структуру RouteConfig и выполняет atomic.Store или Swap. Горутины читают указатель через Load() без единой блокировки мьютекса (Lock-free Read).",
    "step_by_step": "1. Спроектируйте иммутабельную структуру RouteConfig.\\n2. Создайте HotReloadGateway с полем atomic.Pointer[RouteConfig].\\n3. Реализуйте метод ReloadRouteTable с заменой указателя через Swap().\\n4. В ServeHTTP выполняйте быстрое чтение через Load().\\n5. Протестируйте бесшовный переход между версиями конфигурации.",
    "code_blocks": [{"filename": "hot_reload_routes.go", "lang": "go", "code": ex28_code}],
    "under_the_hood": "Благодаря GC в Go старая версия конфигурации будет автоматически освобождена из кучи ровно тогда, когда последний активный HTTP-запрос, успевший прочитать старый указатель, завершит свою работу.",
    "pitfalls": "Никогда не модифицируйте поля существующей структуры cfg.Routes напрямую! Это приведет к фатальной гонке данных (data race) между читающими горутинами и горутиной обновления. Всегда создавайте новый объект RouteConfig целиком.",
    "bigtech_interview": "Как протокол Envoy Dynamic Discovery Service (xDS - LDS/RDS/CDS) обеспечивает консистентное обновление конфигурации тысяч прокси-узлов в масштабе BigTech?"
})

# Ex 29
ex29_code = """package main

import (
	"context"
	"fmt"
	"net"
	"syscall"
)

// CustomHighLoadListenConfig настраивает системные флаги сокетов Linux (SO_REUSEPORT).
func CustomHighLoadListenConfig() net.ListenConfig {
	return net.ListenConfig{
		Control: func(network, address string, c syscall.RawConn) error {
			var controlErr error
			err := c.Control(func(fd uintptr) {
				// 1. SO_REUSEPORT (константа 0x0f / 15 в ядре Linux)
				// Позволяет нескольким независимым процессам слушать один и тот же порт,
				// ядро Linux балансирует входящие TCP SYN пакеты между сокетами
				const SO_REUSEPORT = 0x0F
				if err := syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET, SO_REUSEPORT, 1); err != nil {
					controlErr = fmt.Errorf("setsockopt SO_REUSEPORT failed: %w", err)
					return
				}

				// 2. SO_REUSEADDR (быстрый перезапуск без ожидания TIME_WAIT)
				if err := syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET, syscall.SO_REUSEADDR, 1); err != nil {
					controlErr = fmt.Errorf("setsockopt SO_REUSEADDR failed: %w", err)
					return
				}
			})
			if err != nil {
				return err
			}
			return controlErr
		},
	}
}

func main() {
	_ = context.Background()
	_ = CustomHighLoadListenConfig()

	fmt.Println("Конфигурация HighLoad сокетов Linux:")
	fmt.Println("1. SO_REUSEPORT: балансировка TCP-соединений ядром между процессами")
	fmt.Println("2. SO_REUSEADDR: мгновенный перезапуск сокета без TIME_WAIT блокировки")
	fmt.Println("3. sysctl net.core.somaxconn=65535: очередь SYN-пакетов ядра")
	fmt.Println("4. sysctl net.ipv4.tcp_tw_reuse=1: безопасное повторное использование TIME_WAIT сокетов")
}
"""
validate_go(ex29_code)

exercises.append({
    "num": 29,
    "title": "Системный тюнинг сокетов для HighLoad Gateway",
    "task": "Изучите тюнинг сетевого стека Linux для шлюзов, обслуживающих 100 000+ одновременных TCP-соединений. Напишите конфигурацию net.ListenConfig с хуком Control, устанавливающим флаги сокетов SO_REUSEPORT и SO_REUSEADDR через syscall.SetsockoptInt, и задокументируйте ключевые параметры sysctl ядра.",
    "theory": "Для достижения предельной пропускной способности одного сервера Go-шлюз должен эффективно взаимодействовать с сетевым стеком ядра Linux:\\n1. SO_REUSEPORT: позволяет нескольким независимым процессам или горутинам-слушателям привязываться к одному TCP-порту (например, :443). Ядро Linux на уровне eBPF/хэширования сокетов равномерно распределяет входящие SYN-пакеты между очередями прослушивания (Listen Queues), исключая contention за один глобальный сокет.\\n2. SO_REUSEADDR: позволяет повторно привязать сокет к порту, находящемуся в состоянии TIME_WAIT, обеспечивая мгновенный рестарт без ожидания 60 секунд.\\n3. Параметры ядра Linux (sysctl):\\n- net.core.somaxconn = 65535 (размер очереди бэклога сокета listen).\\n- net.ipv4.tcp_max_syn_backlog = 65535 (очередь полуоткрытых соединений SYN_RECV).\\n- net.ipv4.tcp_tw_reuse = 1 (безопасное переиспользование исходящих сокетов TIME_WAIT для новых соединений).\\n- fs.file-max и nofile ulimit >= 1000000 (лимиты дескрипторов файлов).",
    "step_by_step": "1. Спроектируйте функцию CustomHighLoadListenConfig.\\n2. В хуке Control вызовите c.Control для доступа к файловому дескриптору сокета (fd).\\n3. Установите флаг SO_REUSEPORT через syscall.SetsockoptInt.\\n4. Установите флаг SO_REUSEADDR.\\n5. Задокументируйте системные настройки ядра Linux для продакшн-серверов.",
    "code_blocks": [{"filename": "socket_tuning.go", "lang": "go", "code": ex29_code}],
    "under_the_hood": "Хук Control вызывается до вызова bind(2) и listen(2), что позволяет настроить опции сокета в ядре до того, как операционная система начнет принимать входящие пакеты.",
    "pitfalls": "Увеличение очереди somaxconn в Go не сработает, если в самом ядре Linux значение sysctl net.core.somaxconn осталось дефолтным (128 или 4096): Go не может выставить backlog больше системного предела.",
    "bigtech_interview": "Что такое проблема 'Thundering Herd' при вызове accept() на одном сокете несколькими процессами и как флаг SO_REUSEPORT в Linux решает ее с помощью ядерного шардирования очередей?"
})

# Ex 30
ex30_code = """package main

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"net/http/httputil"
	"net/url"
	"os"
	"os/signal"
	"strings"
	"sync/atomic"
	"syscall"
	"time"
)

// EnterpriseAPIGateway представляет законченный промышленный API-шлюз.
type EnterpriseAPIGateway struct {
	server       *http.Server
	proxy        *httputil.ReverseProxy
	activeConns  atomic.Int64
	totalHandled atomic.Uint64
}

func NewEnterpriseAPIGateway(listenAddr string, upstreamURL *url.URL) *EnterpriseAPIGateway {
	gw := &EnterpriseAPIGateway{}

	// 1. Настройка прокси
	proxy := httputil.NewSingleHostReverseProxy(upstreamURL)
	originalDirector := proxy.Director
	proxy.Director = func(req *http.Request) {
		originalDirector(req)
		req.Host = upstreamURL.Host
		req.Header.Set("X-Gateway-Node", "gw-prod-01")
	}

	proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadGateway)
		_, _ = fmt.Fprintf(w, `{"error":"bad_gateway","message":%q}`, err.Error())
	}

	gw.proxy = proxy

	// 2. Сборка цепочки Middleware
	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = fmt.Fprintf(w, `{"status":"healthy","in_flight":%d}`, gw.activeConns.Load())
	})

	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		gw.activeConns.Add(1)
		defer gw.activeConns.Add(-1)
		gw.totalHandled.Add(1)

		// Базовая валидация токена
		auth := r.Header.Get("Authorization")
		if !strings.HasPrefix(auth, "Bearer ") && r.URL.Path != "/public" {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusUnauthorized)
			_, _ = fmt.Fprint(w, `{"error":"unauthorized"}`)
			return
		}

		proxy.ServeHTTP(w, r)
	})

	gw.server = &http.Server{
		Addr:         listenAddr,
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	return gw
}

func (gw *EnterpriseAPIGateway) StartGraceful(stopSig <-chan os.Signal) {
	go func() {
		fmt.Printf("[API Gateway] Слушатель запущен на %s...\\n", gw.server.Addr)
		if err := gw.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Printf("Ошибка сервера: %v\\n", err)
		}
	}()

	<-stopSig
	fmt.Println("\\n--> Получен сигнал остановки. Инициализация Graceful Shutdown...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := gw.server.Shutdown(ctx); err != nil {
		fmt.Printf("Ошибка принудительного закрытия: %v\\n", err)
	} else {
		fmt.Println("[API Gateway] Все активные соединения корректно завершены. Шлюз остановлен.")
	}
}

func main() {
	targetURL, _ := url.Parse("http://127.0.0.1:8080")
	gw := NewEnterpriseAPIGateway(":8000", targetURL)

	// Тестовая проверка работоспособности роутинга
	req := httptest.NewRequest(http.MethodGet, "/healthz", nil)
	rec := httptest.NewRecorder()
	gw.server.Handler.ServeHTTP(rec, req)

	fmt.Printf("Health Check Gateway: Status %d, Body: %s\\n", rec.Code, rec.Body.String())
	fmt.Println("Архитектура Enterprise API Gateway полностью спроектирована и готова к HighLoad!")
}
"""
validate_go(ex30_code)

exercises.append({
    "num": 30,
    "title": "Комплексный Production-Ready API Gateway на чистом Go",
    "task": "Спроектируйте законченную архитектуру промышленного API-шлюза EnterpriseAPIGateway на чистом Go: обратный прокси httputil.ReverseProxy, Director с перезаписью заголовков, ErrorHandler, эндпоинт проверки здоровья /healthz, централизованная аутентификация токенов, учет активных соединений и процедура плавного завершения (Graceful Shutdown).",
    "theory": "Полнофункциональный промышленный API-шлюз на чистом Go объединяет все рассмотренные архитектурные компоненты в отказоустойчивый конвейер (Pipeline):\\n1. Core Router: сопоставление маршрутов, нормализация путей и стриппинг префиксов.\\n2. Security Layer: MaxBytesReader, проверка JWT, очистка недоверенных заголовков.\\n3. Reliability: Rate Limiter (Redis Token Bucket), Circuit Breaker per Route, Outlier Detection.\\n4. Observability: сквозной TraceContext W3C, Prometheus метрики и JSON Access Log через log/slog.\\n5. Traffic Management: Round-Robin / Least Connections балансировка, переключение на Canary.\\n6. Network Engine: оптимизированный http.Transport с пулом соединений, FlushInterval для стриминга, SO_REUSEPORT и чистый Graceful Shutdown через server.Shutdown(ctx) с ожиданием завершения In-Flight запросов.",
    "step_by_step": "1. Спроектируйте EnterpriseAPIGateway с полями http.Server, ReverseProxy и атомарными метриками.\\n2. Настройте кастомный Director и ErrorHandler.\\n3. Организуйте цепочку проверки авторизации и эндпоинт /healthz.\\n4. Реализуйте метод StartGraceful с перехватом сигналов OS и shutdown по таймауту.\\n5. Протестируйте сквозную работу всех компонентов шлюза.",
    "code_blocks": [{"filename": "enterprise_gateway.go", "lang": "go", "code": ex30_code}],
    "under_the_hood": "server.Shutdown() сначала закрывает все слушающие TCP-сокеты, чтобы новые запросы не поступали, а затем дожидается завершения обработки активных запросов или истечения таймаута контекста, гарантируя нулевую потерю пользовательских транзакций при деплоях.",
    "pitfalls": "Забытый таймаут ReadTimeout в http.Server позволяет злоумышленнику удерживать сокет открытым бесконечно долго, отправляя по 1 байту в секунду (Slowloris attack). Всегда настраивайте жесткие таймауты сервера.",
    "bigtech_interview": "Какие архитектурные метрики (SLI) и алерты являются критическими для API-шлюза в production (p99 latency, rate of 5xx errors, saturation of connection pool, memory footprint)? Как гарантировать 99.99% SLA доступности?"
})

output_path = "/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch93_p2.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Chapter 93 Part 2 generated successfully: {len(exercises)} exercises.")
