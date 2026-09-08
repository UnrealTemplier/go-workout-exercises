import json
import subprocess
import os

def validate_go(code):
    p = subprocess.run(['gofmt', '-e'], input=code.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise ValueError(f"Go syntax error: {p.stderr.decode('utf-8')}\nCode:\n{code}")

exercises = []

# Ex 1
ex1_code = """package main

import (
	"fmt"
	"net/http"
)

// GatewayRole классифицирует архитектурные обязанности сетевого узла.
type GatewayRole struct {
	Type        string
	Direction   string
	Visibility  string
	CoreDuties  []string
}

func GetArchitectureRoles() []GatewayRole {
	return []GatewayRole{
		{
			Type:       "Forward Proxy",
			Direction:  "Клиент -> Внешний интернет",
			Visibility: "Скрывает клиентов от внешних серверов (корпоративный выход, VPN)",
			CoreDuties: []string{"Кэширование внешних ресурсов", "Фильтрация запрещенных доменов", "Контроль трафика сотрудников"},
		},
		{
			Type:       "Reverse Proxy",
			Direction:  "Интернет -> Внутренний кластер",
			Visibility: "Скрывает топологию внутренней сети от внешних клиентов",
			CoreDuties: []string{"Терминация TLS/HTTPS", "Балансировка нагрузки (L7)", "Сжатие трафика и статический кэш"},
		},
		{
			Type:       "Full API Gateway",
			Direction:  "Интернет / Мобильные приложения -> Микросервисы",
			Visibility: "Единая точка входа (Single Entry Point) корпоративного API",
			CoreDuties: []string{
				"Централизованная аутентификация (JWT, OAuth2, mTLS)",
				"Динамический Rate Limiting и Quotas per Client",
				"Маршрутизация (Path/Header-based, Canary, A/B)",
				"Агрегация API (BFF - Backend For Frontend)",
				"Сквозная наблюдаемость (Distributed Tracing W3C, Prometheus, Slog)",
			},
		},
	}
}

func main() {
	fmt.Println("Архитектурное сравнение Forward Proxy, Reverse Proxy и API Gateway:")
	for _, r := range GetArchitectureRoles() {
		fmt.Printf("==> [%s]\\n    Направление: %s\\n    Видимость:   %s\\n    Обязанности: %v\\n",
			r.Type, r.Direction, r.Visibility, r.CoreDuties)
	}
}
"""
validate_go(ex1_code)

exercises.append({
    "num": 1,
    "title": "Концепция обратного прокси (Reverse Proxy) и API Gateway",
    "task": "Изучите архитектурные различия между прямым прокси (Forward Proxy), обратным прокси (Reverse Proxy) и полнофункциональным API-шлюзом (API Gateway). Спроектируйте сравнительную модель обязанностей сетевых узлов и сформулируйте требования к единой точке входа (Single Entry Point) для микросервисной архитектуры.",
    "theory": "В современных распределенных системах разделяют 3 типа проксирующих сущностей:\\n1. Forward Proxy (прямой прокси): находится на стороне клиента. Все исходящие запросы корпоративной сети идут через него. Он маскирует реальные IP-адреса клиентов, кэширует исходящий трафик и фильтрует доступ к внешним сайтам.\\n2. Reverse Proxy (обратный прокси): находится перед группой бэкендов. Для внешнего мира он выглядит как конечный веб-сервер. Основные задачи: терминация TLS, балансировка нагрузки на L4/L7 уровнях, защита внутренней сети от прямого доступа и сжатие трафика.\\n3. API Gateway (API-шлюз): надстройка над Reverse Proxy уровня приложения (L7), ориентированная на специфику бизнес-API. Шлюз берет на себя кросс-функциональные требования микросервисов (Cross-cutting Concerns): централизованную валидацию JWT-токенов, Rate Limiting, динамический роутинг (Canary, Blue/Green), трансформацию протоколов (gRPC-Web, REST -> gRPC) и инъекцию контекста трассировки OpenTelemetry.",
    "step_by_step": "1. Спроектируйте структуру GatewayRole с классификацией сетевых узлов.\\n2. Задокументируйте ключевые отличия по направлению трафика и обязанностям.\\n3. Реализуйте функцию GetArchitectureRoles для вывода сравнительной матрицы.\\n4. Сформулируйте архитектурные требования к отказоустойчивости шлюза.",
    "code_blocks": [{"filename": "proxy_concepts.go", "lang": "go", "code": ex1_code}],
    "under_the_hood": "API Gateway исключает дублирование логики авторизации и мониторинга в десятках микросервисов, снижая размер кодовой базы и исключая человеческие ошибки при обновлении криптографических ключей и политик безопасности.",
    "pitfalls": "Опасность превращения API Gateway в 'распределенный монолит' (Smart Gateway, Dumb Microservices): не размещайте внутри шлюза тяжелую бизнес-логику или прямые обращения к базам данных бэкендов.",
    "bigtech_interview": "Почему в BigTech (Яндекс, Netflix, Ozon) архитектуру часто разделяют на L4/L7 Edge Proxy (Envoy, Nginx для TLS и DDoS) и внутренний API Gateway (Go-сервисы с бизнес-маршрутизацией и BFF)?"
})

# Ex 2
ex2_code = """package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"net/http/httputil"
	"net/url"
)

func main() {
	// 1. Создаем тестовый бэкенд-сервер
	backendServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("X-Backend-Server", "origin-node-01")
		w.WriteHeader(http.StatusOK)
		_, _ = fmt.Fprintf(w, "Ответ от бэкенда: path=%s, user-agent=%s\\n", r.URL.Path, r.UserAgent())
	}))
	defer backendServer.Close()

	backendURL, err := url.Parse(backendServer.URL)
	if err != nil {
		panic(err)
	}

	// 2. Создаем стандартный обратный прокси
	proxy := httputil.NewSingleHostReverseProxy(backendURL)

	// 3. Создаем тестовый клиентский запрос к прокси
	req := httptest.NewRequest(http.MethodGet, "http://my-gateway.local/api/v1/orders", nil)
	req.Header.Set("User-Agent", "Go-Client/1.0")
	rec := httptest.NewRecorder()

	// 4. Проксируем запрос
	proxy.ServeHTTP(rec, req)

	res := rec.Result()
	defer res.Body.Close()

	fmt.Printf("HTTP Status: %d\\n", res.StatusCode)
	fmt.Printf("Header X-Backend-Server: %s\\n", res.Header.Get("X-Backend-Server"))
	fmt.Printf("Тело ответа: %s", rec.Body.String())
}
"""
validate_go(ex2_code)

exercises.append({
    "num": 2,
    "title": "Устройство net/http/httputil.ReverseProxy",
    "task": "Изучите внутреннее устройство структуры httputil.ReverseProxy из стандартной библиотеки Go. Создайте тестовый апстрим-сервер с помощью httptest.NewServer и минимальный обратный прокси через httputil.NewSingleHostReverseProxy, перенаправляющий входящие клиентские запросы.",
    "theory": "Пакет net/http/httputil содержит структуру ReverseProxy — фундамент для создания производительных L7-прокси на Go. Структура реализует стандартный интерфейс http.Handler (метод ServeHTTP). Основные поля ReverseProxy:\\n- Director func(*http.Request): функция модификации входящего запроса перед отправкой бэкенду (установка целевого URL, заголовков).\\n- Transport http.RoundTripper: сетевой транспорт (пул TCP-соединений, настройки TLS, таймауты).\\n- FlushInterval time.Duration: интервал принудительного сброса буферизованных данных клиенту (критично для SSE и потоков).\\n- ModifyResponse func(*http.Response) error: функция постобработки ответа бэкенда перед отправкой клиенту.\\n- ErrorHandler func(http.ResponseWriter, *http.Request, error): перехватчик сетевых ошибок апстрима.",
    "step_by_step": "1. Запустите mock-бэкенд с помощью httptest.NewServer.\\n2. Распарсите URL бэкенда через url.Parse.\\n3. Инициализируйте прокси через httputil.NewSingleHostReverseProxy.\\n4. Сформируйте клиентский запрос с httptest.NewRequest и проверьте проксирование через httptest.ResponseRecorder.",
    "code_blocks": [{"filename": "simple_proxy.go", "lang": "go", "code": ex2_code}],
    "under_the_hood": "httputil.NewSingleHostReverseProxy создает дефолтный Director, который перезаписывает r.URL.Scheme и r.URL.Host значениями таргета, объединяет пути через SingleJoinPath и удаляет заголовок User-Agent, если он был пустым.",
    "pitfalls": "Функция NewSingleHostReverseProxy по умолчанию использует http.DefaultTransport. В HighLoad системах это приводит к исчерпанию файловых дескрипторов, так как DefaultTransport настроен всего на 2 Idle соединения на хост (MaxIdleConnsPerHost = 2).",
    "bigtech_interview": "Какие ключевые поля httputil.ReverseProxy необходимо обязательно кастомизировать при создании корпоративного шлюза для защиты от утечек дескрипторов и перегрузки бэкендов?"
})

# Ex 3
ex3_code = """package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"net/http/httputil"
	"net/url"
	"strings"
)

// CreateCustomDirector настраивает модификацию запросов с изменением хоста и нормализацией путей.
func CreateCustomDirector(target *url.URL) func(req *http.Request) {
	targetQuery := target.RawQuery
	return func(req *http.Request) {
		// 1. Подменяем схему и целевой хост
		req.URL.Scheme = target.Scheme
		req.URL.Host = target.Host
		
		// 2. Нормализация пути: удаляем префикс шлюза /gateway/v1
		cleanPath := strings.TrimPrefix(req.URL.Path, "/gateway/v1")
		if !strings.HasPrefix(cleanPath, "/") {
			cleanPath = "/" + cleanPath
		}
		req.URL.Path = cleanPath

		// 3. Слияние query параметров
		if targetQuery == "" || req.URL.RawQuery == "" {
			req.URL.RawQuery = targetQuery + req.URL.RawQuery
		} else {
			req.URL.RawQuery = targetQuery + "&" + req.URL.RawQuery
		}

		// 4. Явно сохраняем оригинальный Host для виртуального хостинга
		req.Host = target.Host
	}
}

func main() {
	targetURL, _ := url.Parse("https://backend.internal.net")
	director := CreateCustomDirector(targetURL)

	req := httptest.NewRequest(http.MethodGet, "http://gateway.company.com/gateway/v1/users?role=admin", nil)
	director(req)

	fmt.Printf("Трансформированный запрос:\\nScheme: %s\\nHost: %s\\nPath: %s\\nRawQuery: %s\\n",
		req.URL.Scheme, req.URL.Host, req.URL.Path, req.URL.RawQuery)
}
"""
validate_go(ex3_code)

exercises.append({
    "num": 3,
    "title": "Функция Director: модификация входящих запросов",
    "task": "Реализуйте кастомную функцию Director(req *http.Request) для httputil.ReverseProxy. Настройте динамическую смену целевого хоста и схемы, удаление внутреннего префикса шлюза (/gateway/v1), корректное слияние параметров URL (RawQuery) и перезапись заголовка Host.",
    "theory": "Функция Director вызывается прокси-сервером непосредственно перед отправкой запроса сетевому транспорту. Она отвечает за трансформацию объекта *http.Request. Критически важные нюансы:\\n1. req.URL.Host vs req.Host: присваивание req.URL.Host меняет адрес, куда транспорт отправит TCP-пакеты. Однако значение HTTP-заголовка Host (используемого виртуальными хостами и веб-серверами типа Nginx) берется из поля req.Host. Если не обновить req.Host = target.Host, бэкенд может вернуть ошибку 404 или 400 Invalid Host.\\n2. Слияние Query параметров: если целевой URL уже содержит статические параметры (?env=prod), их необходимо безопасно объединить с параметрами входящего запроса клиента.\\n3. Нормализация путей: удаление технических префиксов шлюза (Path Stripping) перед передачей во внутренний сервис.",
    "step_by_step": "1. Спроектируйте замыкание CreateCustomDirector, захватывающее target URL.\\n2. Реализуйте присваивание схемы и целевого адреса хоста.\\n3. Удалите префикс пути /gateway/v1 с помощью strings.TrimPrefix.\\n4. Реализуйте слияние query-параметров и обновление поля req.Host.\\n5. Протестируйте преобразование входящего запроса.",
    "code_blocks": [{"filename": "custom_director.go", "lang": "go", "code": ex3_code}],
    "under_the_hood": "В Go 1.20+ в ReverseProxy появился альтернативный механизм Rewrite(r *httputil.ProxyRequest), где операции модификации инкапсулированы в методы Out.SetURL() и Out.Header, но понимание классического Director остается фундаментальным для всех версий Go.",
    "pitfalls": "Если забыть обновить req.Host при проксировании на TLS-бэкенд с включенной проверкой SNI (Server Name Indication), TLS-хэндшейк завершится фатальной ошибкой несоответствия сертификата (certificate valid for backend, not gateway).",
    "bigtech_interview": "В чем разница между полями req.URL.Host и req.Host в Go HTTP-сервере? Какое из них определяет сокет подключения, а какое — HTTP-заголовок Host в текстовом протоколе?"
})

# Ex 4
ex4_code = """package main

import (
	"fmt"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
)

// AppendForwardedHeaders формирует стандартизированные заголовки X-Forwarded-*
func AppendForwardedHeaders(req *http.Request, clientIP string, isTLS bool) {
	// 1. X-Forwarded-For: добавляем clientIP в цепочку прокси
	prior := req.Header.Get("X-Forwarded-For")
	if prior != "" {
		req.Header.Set("X-Forwarded-For", prior+", "+clientIP)
	} else {
		req.Header.Set("X-Forwarded-For", clientIP)
	}

	// 2. X-Forwarded-Host: сохраняем оригинальный хост
	if req.Header.Get("X-Forwarded-Host") == "" {
		req.Header.Set("X-Forwarded-Host", req.Host)
	}

	// 3. X-Forwarded-Proto: определяем реальный протокол клиента
	if req.Header.Get("X-Forwarded-Proto") == "" {
		if isTLS {
			req.Header.Set("X-Forwarded-Proto", "https")
		} else {
			req.Header.Set("X-Forwarded-Proto", "http")
		}
	}
}

// ExtractClientIP извлекает реальный IP адрес из RemoteAddr, отсекая порт.
func ExtractClientIP(remoteAddr string) string {
	ip, _, err := net.SplitHostPort(remoteAddr)
	if err != nil {
		return remoteAddr
	}
	return ip
}

func main() {
	req := httptest.NewRequest(http.MethodGet, "http://api.marketplace.ru/v1/products", nil)
	req.RemoteAddr = "192.168.1.50:54321"
	req.Header.Set("X-Forwarded-For", "203.0.113.195") // Внешний клиент через CDN

	clientIP := ExtractClientIP(req.RemoteAddr)
	AppendForwardedHeaders(req, clientIP, true)

	fmt.Printf("Сформированные служебные заголовки:\\n")
	fmt.Printf("X-Forwarded-For:   %s\\n", req.Header.Get("X-Forwarded-For"))
	fmt.Printf("X-Forwarded-Host:  %s\\n", req.Header.Get("X-Forwarded-Host"))
	fmt.Printf("X-Forwarded-Proto: %s\\n", req.Header.Get("X-Forwarded-Proto"))
}
"""
validate_go(ex4_code)

exercises.append({
    "num": 4,
    "title": "Управление служебными заголовками X-Forwarded-*",
    "task": "Реализуйте функцию AppendForwardedHeaders для корректного формирования служебных заголовков проксирования: добавление клиентского IP в X-Forwarded-For (с сохранением цепочки), фиксация оригинального хоста в X-Forwarded-Host и схемы в X-Forwarded-Proto с защитой от IP Spoofing.",
    "theory": "Когда запрос проходит через обратный прокси, реальный IP-клиента для бэкенда заменяется на IP-адрес самого прокси. Для сохранения контекста оригинального клиента используются заголовки X-Forwarded-* (де-факто стандарт) или RFC 7239 Forwarded:\\n- X-Forwarded-For: список IP-адресов через запятую. Каждый промежуточный прокси добавляет IP-адрес узла, от которого он непосредственно получил соединение.\\n- X-Forwarded-Host: оригинальное значение заголовка Host, запрошенное клиентом.\\n- X-Forwarded-Proto: исходный протокол (http или https), что позволяет бэкенду знать, был ли входящий трафик зашифрован до терминации TLS на шлюзе.\\nУязвимость IP Spoofing: если шлюз слепо доверяет входящему заголовку X-Forwarded-For от внешнего недоверенного клиента, злоумышленник может передать фиктивный IP (например, 127.0.0.1) для обхода ACL или Rate Limiting.",
    "step_by_step": "1. Реализуйте ExtractClientIP для разделения IP и порта через net.SplitHostPort.\\n2. В AppendForwardedHeaders проверьте наличие предыдущего значения X-Forwarded-For.\\n3. Добавьте текущий клиентский IP в конец цепочки через запятую.\\n4. Установите X-Forwarded-Host и X-Forwarded-Proto.\\n5. Протестируйте работу с существующей цепочкой прокси.",
    "code_blocks": [{"filename": "forwarded_headers.go", "lang": "go", "code": ex4_code}],
    "under_the_hood": "Для предотвращения IP Spoofing корпоративные шлюзы должны очищать входящий заголовок X-Forwarded-For на внешней границе периметра (Edge), если запрос пришел не от доверенных IP-адресов (например, пула Cloudflare или собственного внешнего L4 балансировщика).",
    "pitfalls": "Использование r.RemoteAddr напрямую в качестве IP клиента без net.SplitHostPort приводит к ошибкам: строка содержит порт (например, 1.2.3.4:56789), что ломает парсинг net.ParseIP.",
    "bigtech_interview": "Как в системах антифрода (Antifraud) определяют реальный IP клиента при наличии цепочки из 3 прокси (Client -> Public Proxy -> Cloudflare -> Corporate Gateway)? Какому IP из списка X-Forwarded-For можно доверять?"
})

# Ex 5
ex5_code = """package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
)

// HopByHopHeaders — перечень транзитных заголовков по спецификации RFC 2616 и RFC 7230.
var HopByHopHeaders = []string{
	"Connection",
	"Keep-Alive",
	"Proxy-Authenticate",
	"Proxy-Authorization",
	"Te",
	"Trailers",
	"Transfer-Encoding",
	"Upgrade",
}

// RemoveHopByHopHeaders удаляет транзитные заголовки, не предназначенные для дальнейшей пересылки.
func RemoveHopByHopHeaders(header http.Header) {
	// 1. Спецификация RFC гласит: заголовок Connection может содержать имена дополнительных hop-by-hop заголовков
	if c := header.Get("Connection"); c != "" {
		for _, extraHeader := range strings.Split(c, ",") {
			header.Del(strings.TrimSpace(extraHeader))
		}
	}

	// 2. Удаляем стандартные транзитные заголовки
	for _, h := range HopByHopHeaders {
		header.Del(h)
	}
}

func main() {
	req := httptest.NewRequest(http.MethodGet, "/test", nil)
	req.Header.Set("Connection", "Keep-Alive, X-Custom-Transit")
	req.Header.Set("Keep-Alive", "timeout=5, max=1000")
	req.Header.Set("Proxy-Authorization", "Basic dXNlcjpwYXNz")
	req.Header.Set("X-Custom-Transit", "should-be-removed")
	req.Header.Set("X-Application-Data", "must-remain")

	fmt.Println("Заголовки до очистки:")
	for k, v := range req.Header {
		fmt.Printf("  %s: %v\\n", k, v)
	}

	RemoveHopByHopHeaders(req.Header)

	fmt.Println("\\nЗаголовки после очистки Hop-by-Hop:")
	for k, v := range req.Header {
		fmt.Printf("  %s: %v\\n", k, v)
	}
}
"""
validate_go(ex5_code)

exercises.append({
    "num": 5,
    "title": "Очистка транзитных заголовков (Hop-by-Hop Headers)",
    "task": "Изучите стандарты RFC 2616 и RFC 7230, запрещающие передачу транзитных заголовков (Hop-by-Hop Headers) через прокси. Реализуйте функцию RemoveHopByHopHeaders, удаляющую стандартные транзитные заголовки (Connection, Keep-Alive, Proxy-Authorization, Transfer-Encoding) и динамические заголовки, перечисленные в Connection.",
    "theory": "В протоколе HTTP заголовки делятся на две категории:\\n1. End-to-End: предназначены для конечного получателя запроса или ответа (например, Content-Type, Authorization, User-Agent). Они должны передаваться через всю цепочку прокси без изменений.\\n2. Hop-by-Hop: имеют значение исключительно для текущего TCP-соединения между двумя соседними узлами (например, Keep-Alive, Connection, Transfer-Encoding, Proxy-Authenticate). Пересылка этих заголовков дальше нарушает спецификацию HTTP и может привести к уязвимостям класса HTTP Request Smuggling (расхождение в парсинге границ запросов между прокси и бэкендом). Кроме того, заголовок Connection может содержать список нестандартных заголовков, которые клиент потребовал удалить перед следующей пересылкой.",
    "step_by_step": "1. Сформируйте срез эталонных Hop-by-Hop заголовков по RFC.\\n2. Считайте значение заголовка Connection и разбейте его по запятым.\\n3. Удалите все динамически указанные заголовки из http.Header.\\n4. Удалите стандартные транзитные заголовки.\\n5. Протестируйте очистку запроса.",
    "code_blocks": [{"filename": "hop_by_hop.go", "lang": "go", "code": ex5_code}],
    "under_the_hood": "В httputil.ReverseProxy стандартная библиотека Go автоматически удаляет hop-by-hop заголовки, если только не используется кастомный транспорт или ручная прокси-обработка сокетов.",
    "pitfalls": "Единственное исключение из правила удаления заголовка Upgrade — процедура WebSocket рукопожатия (HTTP 101 Switching Protocols). Если безоговорочно удалить Upgrade, проксирование WebSockets сломается.",
    "bigtech_interview": "Что такое уязвимость HTTP Desync / Request Smuggling? Как несогласованность обработки заголовков Transfer-Encoding и Content-Length между Reverse Proxy и Backend позволяет злоумышленнику перехватывать чужие сессии?"
})

# Ex 6
ex6_code = """package main

import (
	"bytes"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
)

// CreateSecurityModifyResponse настраивает постобработку ответов бэкенда.
func CreateSecurityModifyResponse() func(resp *http.Response) error {
	return func(resp *http.Response) error {
		// 1. Добавляем корпоративные заголовки безопасности
		resp.Header.Set("X-Content-Type-Options", "nosniff")
		resp.Header.Set("X-Frame-Options", "DENY")
		resp.Header.Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

		// 2. Скрываем внутренние версии серверов
		resp.Header.Del("Server")
		resp.Header.Del("X-Powered-By")

		// 3. Маскирование критических ошибок бэкенда в JSON ответах
		if resp.StatusCode >= 500 {
			origBody, err := io.ReadAll(resp.Body)
			_ = resp.Body.Close()
			if err != nil {
				return err
			}

			// Если бэкенд выплюнул стек трейс или внутреннюю ошибку, маскируем ее
			if strings.Contains(string(origBody), "postgres") || strings.Contains(string(origBody), "panic") {
				sanitized := []byte(`{"error":"internal_server_error","tracking_id":"sec_9918"}`)
				resp.Body = io.NopCloser(bytes.NewReader(sanitized))
				resp.ContentLength = int64(len(sanitized))
				resp.Header.Set("Content-Length", fmt.Sprintf("%d", len(sanitized)))
				resp.Header.Set("Content-Type", "application/json; charset=utf-8")
			} else {
				resp.Body = io.NopCloser(bytes.NewReader(origBody))
			}
		}

		return nil
	}
}

func main() {
	modifyFn := CreateSecurityModifyResponse()

	// Имитация ответа от бэкенда с паникой базы данных
	backendResp := &http.Response{
		StatusCode: http.StatusInternalServerError,
		Header:     http.Header{"Server": []string{"Apache/2.4 internal"}, "X-Powered-By": []string{"PHP/7.4"}},
		Body:       io.NopCloser(strings.NewReader("Fatal error: postgres connection pool exhausted")),
	}

	if err := modifyFn(backendResp); err != nil {
		panic(err)
	}

	maskedBody, _ := io.ReadAll(backendResp.Body)
	fmt.Printf("Статус: %d\\n", backendResp.StatusCode)
	fmt.Printf("Header X-Frame-Options: %s\\n", backendResp.Header.Get("X-Frame-Options"))
	fmt.Printf("Header Server: %q\\n", backendResp.Header.Get("Server"))
	fmt.Printf("Маскированное тело ответа: %s\\n", string(maskedBody))
}
"""
validate_go(ex6_code)

exercises.append({
    "num": 6,
    "title": "Модификация ответов через ModifyResponse",
    "task": "Реализуйте функцию ModifyResponse(resp *http.Response) error для httputil.ReverseProxy. Внедрите автоматическое добавление корпоративных заголовков безопасности (HSTS, nosniff, DENY), удаление серверных маркеров (Server, X-Powered-By) и безопасное маскирование чувствительных сведений об ошибках БД в ответах 5xx.",
    "theory": "Поле ModifyResponse в структуре ReverseProxy позволяет шлюзу инспектировать и модифицировать ответ бэкенда до отправки его клиенту. Сценарии использования:\\n1. Харденинг безопасности (Security Headers): инъекция HSTS, Content-Security-Policy (CSP) и X-Frame-Options на периметре сети.\\n2. Скрытие топологии (Information Disclosure): удаление заголовков Server: nginx/1.18 или X-Powered-By, чтобы злоумышленники не могли сканировать версии уязвимого ПО внутри кластера.\\n3. Data Masking и Sanitize: если бэкенд вернул HTTP 500 с незамаскированным дампом SQL-запроса или паникой Go, шлюз перехватывает тело, заменяет его на обезличенный JSON с tracking_id и корректирует заголовок Content-Length. Если ModifyResponse возвращает ошибку, шлюз отменяет ответ и вызывает ErrorHandler.",
    "step_by_step": "1. Создайте функцию CreateSecurityModifyResponse, возвращающую замыкание.\\n2. Установите заголовки X-Content-Type-Options, X-Frame-Options и Strict-Transport-Security.\\n3. Удалите заголовки Server и X-Powered-By.\\n4. При коде 5xx прочитайте тело, проверьте на наличие ключевых слов БД и замените на sanitized JSON с обновлением Content-Length.\\n5. Протестируйте поведение на ошибочном ответе бэкенда.",
    "code_blocks": [{"filename": "modify_response.go", "lang": "go", "code": ex6_code}],
    "under_the_hood": "При замене тела ответа resp.Body обязательно оборачивайте новый срез в io.NopCloser(bytes.NewReader(...)) и синхронизируйте число байт в ContentLength, иначе клиент получит ошибку обрыва потока или зависнет в ожидании непрочитанных байт.",
    "pitfalls": "Чтение resp.Body через io.ReadAll буферизует весь ответ в памяти. Не делайте io.ReadAll для успешных ответов (HTTP 200) с большими телами (файлы, видео), иначе шлюз моментально исчерпает оперативную память.",
    "bigtech_interview": "Почему заголовки HSTS (Strict-Transport-Security) и nosniff рекомендуется настраивать централизованно на API Gateway, а не размазывать по десяткам микросервисов?"
})

# Ex 7
ex7_code = """package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"net/http"
	"net/http/httptest"
	"syscall"
)

// GatewayErrorResponse описывает структурированную ошибку шлюза для фронтенда.
type GatewayErrorResponse struct {
	Error     string `json:"error"`
	Code      string `json:"code"`
	Details   string `json:"details"`
	Timestamp int64  `json:"timestamp"`
}

// CustomGatewayErrorHandler классифицирует ошибки сети и возвращает понятные JSON-ответы.
func CustomGatewayErrorHandler(w http.ResponseWriter, r *http.Request, err error) {
	statusCode := http.StatusBadGateway
	errCode := "BAD_GATEWAY"
	details := "Upstream server returned an error"

	var netErr net.Error
	if errors.Is(err, context.DeadlineExceeded) || (errors.As(err, &netErr) && netErr.Timeout()) {
		statusCode = http.StatusGatewayTimeout
		errCode = "GATEWAY_TIMEOUT"
		details = "Апстрим-сервис не ответил в отведенный интервал времени"
	} else if errors.Is(err, syscall.ECONNREFUSED) {
		statusCode = http.StatusBadGateway
		errCode = "CONNECTION_REFUSED"
		details = "Целевой сервис недоступен (порт закрыт или сервис остановлен)"
	}

	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("X-Gateway-Error", errCode)
	w.WriteHeader(statusCode)

	resp := GatewayErrorResponse{
		Error:     http.StatusText(statusCode),
		Code:      errCode,
		Details:   details,
		Timestamp: 1718000000,
	}
	_ = json.NewEncoder(w).Encode(resp)
}

func main() {
	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/orders/123", nil)

	// Моделируем таймаут сетевого подключения к бэкенду
	CustomGatewayErrorHandler(rec, req, context.DeadlineExceeded)

	res := rec.Result()
	defer res.Body.Close()

	fmt.Printf("HTTP Status: %d\\n", res.StatusCode)
	fmt.Printf("Header X-Gateway-Error: %s\\n", res.Header.Get("X-Gateway-Error"))
	fmt.Printf("JSON Body:\\n%s", rec.Body.String())
}
"""
validate_go(ex7_code)

exercises.append({
    "num": 7,
    "title": "Кастомная обработка сбоев бэкенда через ErrorHandler",
    "task": "Реализуйте функцию ErrorHandler(w http.ResponseWriter, r *http.Request, err error) для httputil.ReverseProxy. Классифицируйте возникающие сетевые сбои (таймаут context.DeadlineExceeded, сброс соединения ECONNREFUSED) и возвращайте структурированные JSON-ответы со статусами 504 Gateway Timeout или 502 Bad Gateway.",
    "theory": "По умолчанию httputil.ReverseProxy при ошибке соединения с бэкендом логирует сообщение через ErrorLog и возвращает клиенту пустой HTTP-ответ со статусом 502 Bad Gateway. Для фронтенда и мобильных клиентов это неудобно: клиент не может различить, упал ли бэкенд (502) или не уложился в SLA таймаута (504). Поле ErrorHandler позволяет перехватить ошибку раунтриппера. С помощью errors.Is и errors.As инженер может дифференцировать причины: context.DeadlineExceeded (504), syscall.ECONNREFUSED (502), сбой DNS-резолвинга (502) и вернуть структурированный JSON с кодом инцидента.",
    "step_by_step": "1. Спроектируйте структуру GatewayErrorResponse с кодом ошибки и описанием.\\n2. В функции CustomGatewayErrorHandler выполните инспекцию ошибки через errors.Is и errors.As.\\n3. Разделите сценарии Gateway Timeout (504) и Connection Refused (502).\\n4. Установите заголовки Content-Type и X-Gateway-Error.\\n5. Сериализуйте JSON в тело ответа.",
    "code_blocks": [{"filename": "error_handler.go", "lang": "go", "code": ex7_code}],
    "under_the_hood": "Если клиент разорвал соединение до завершения ответа бэкенда, err будет содержать context.Canceled. В этом случае писать в http.ResponseWriter бессмысленно (клиент отключился), и ErrorHandler должен просто завершить выполнение без лишнего спама в лог ошибок.",
    "pitfalls": "Попытка вызова w.WriteHeader() после того, как в w уже записаны данные, приведет к предупреждению рантайма 'http: superfluous response.WriteHeader call'. Убедитесь, что статус пишется строго до вызова json.NewEncoder.",
    "bigtech_interview": "Как в шлюзах BigTech настраивают различие между Client Disconnect (код 499 в Nginx) и Upstream Timeout (код 504)? Почему важно не считать ошибки 499 за деградацию бэкенда в алертах?"
})

# Ex 8
ex8_code = """package main

import (
	"fmt"
	"net/http"
	"net/http/httputil"
	"time"
)

// ConfigureStreamingReverseProxy настраивает потоковую передачу данных без буферизации.
func ConfigureStreamingReverseProxy(targetDirector func(*http.Request)) *httputil.ReverseProxy {
	proxy := &httputil.ReverseProxy{
		Director: targetDirector,
		// FlushInterval = -1 отключает буферизацию и сбрасывает данные клиенту
		// немедленно после каждого успешного чтения из бэкенда (критично для SSE / LLM Streaming)
		FlushInterval: -1,
	}
	return proxy
}

func main() {
	proxy := ConfigureStreamingReverseProxy(func(req *http.Request) {})
	fmt.Printf("ReverseProxy настроен для потоковой передачи:\\nFlushInterval: %v (мгновенный сброс чанков)\\n", proxy.FlushInterval)
	fmt.Println("Идеально для: Server-Sent Events (SSE), генерации токенов LLM и загрузки многогигабайтных файлов.")
}
"""
validate_go(ex8_code)

exercises.append({
    "num": 8,
    "title": "Потоковая передача данных (Zero-Allocation Streaming) и FlushInterval",
    "task": "Изучите механизм потоковой передачи данных в httputil.ReverseProxy. Настройте параметр FlushInterval для сценариев передачи Server-Sent Events (SSE) и потоковых ответов LLM нейросетей, исключив паразитные задержки буферизации данных в оперативной памяти шлюза.",
    "theory": "По умолчанию httputil.ReverseProxy буферизует ответы апстримов в памяти чанками для оптимизации системных вызовов writev. Однако при передаче стриминговых протоколов (Server-Sent Events, прогресс сборки CI/CD, генерация токенов ChatGPT/Ollama) буферизация становится фатальной: клиент не получает данные в реальном времени, а видит зависание до тех пор, пока буфер шлюза (обычно 32 КБ) не заполнится. Параметр FlushInterval управляет поведением:\\n- FlushInterval = 0: стандартная буферизация рантайма.\\n- FlushInterval > 0 (например, 100ms): периодический сброс накопленных байтов клиенту через http.Flusher.\\n- FlushInterval = -1: немедленный сброс (Immediate Flush) каждого прочитанного байта/чанка без задержек. Это снижает latency до единиц микросекунд, обеспечивая плавный пользовательский опыт.",
    "step_by_step": "1. Спроектируйте функцию ConfigureStreamingReverseProxy.\\n2. Установите FlushInterval = -1 для активации мгновенного сброса потока.\\n3. Проанализируйте применимость конфигурации для AI/LLM шлюзов и SSE.\\n4. Задокументируйте влияние на CPU и системные вызовы.",
    "code_blocks": [{"filename": "streaming_proxy.go", "lang": "go", "code": ex8_code}],
    "under_the_hood": "При FlushInterval = -1 горутина копирования данных io.CopyBuffer вызывает flusher.Flush() после каждого непустого считывания из сетевого сокета бэкенда, отправляя TCP-пакет с флагом PUSH.",
    "pitfalls": "Мгновенный Flush увеличивает количество контекстных переключений процессора и пакетов в сети при передаче миллионов мелких строк. Для обычных статических JSON API держите FlushInterval положительным (например, 10–50ms) или дефолтным.",
    "bigtech_interview": "Как в шлюзах типа Nginx директива proxy_buffering off соотносится с параметром FlushInterval в Go? Почему отключение буферизации требует защиты медленных клиентов (Slowloris attacks)?"
})

# Ex 9
ex9_code = """package main

import (
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
)

// MaxBodySizeMiddleware защищает шлюз от DoS атак через исчерпание памяти гигантскими телами запросов.
func MaxBodySizeMiddleware(maxBytes int64, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Ограничиваем поток чтения тела запроса
		r.Body = http.MaxBytesReader(w, r.Body, maxBytes)

		// Оборачиваем вызов для перехвата ошибки превышения лимита
		next.ServeHTTP(w, r)
	})
}

func main() {
	const MaxAllowed = 1024 // 1 КБ

	handler := MaxBodySizeMiddleware(MaxAllowed, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		body, err := io.ReadAll(r.Body)
		if err != nil {
			var maxBytesErr *http.MaxBytesError
			if errors.As(err, &maxBytesErr) {
				w.Header().Set("Content-Type", "application/json")
				w.WriteHeader(http.StatusRequestEntityTooLarge)
				_, _ = fmt.Fprintf(w, `{"error":"payload_too_large","limit_bytes":%d}`, maxBytesErr.Limit)
				return
			}
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		w.WriteHeader(http.StatusOK)
		_, _ = fmt.Fprintf(w, "Успешно прочитано %d байт", len(body))
	}))

	// Тест 1: Запрос в пределах лимита (100 байт)
	rec1 := httptest.NewRecorder()
	req1 := httptest.NewRequest(http.MethodPost, "/upload", strings.NewReader(strings.Repeat("A", 100)))
	handler.ServeHTTP(rec1, req1)
	fmt.Printf("Тест 1 (норма): HTTP %d, ответ: %s\\n", rec1.Code, rec1.Body.String())

	// Тест 2: Превышение лимита (2048 байт)
	rec2 := httptest.NewRecorder()
	req2 := httptest.NewRequest(http.MethodPost, "/upload", strings.NewReader(strings.Repeat("B", 2048)))
	handler.ServeHTTP(rec2, req2)
	fmt.Printf("Тест 2 (DoS защита): HTTP %d, ответ: %s\\n", rec2.Code, rec2.Body.String())
}
"""
validate_go(ex9_code)

exercises.append({
    "num": 9,
    "title": "Защита от переполнения памяти: ограничение размера тела запроса",
    "task": "Защитите API-шлюз от DoS-атак через исчерпание оперативной памяти бесконечными телами запросов (HTTP POST/PUT). Реализуйте middleware MaxBodySizeMiddleware с использованием http.MaxBytesReader, перехватывающее ошибку *http.MaxBytesError и возвращающее статус 413 Request Entity Too Large.",
    "theory": "Злоумышленник может отправить HTTP POST запрос с заголовком Content-Length: 10000000000 или Chunked Transfer Encoding без указания длины и бесконечно слать поток байт. Если прокси попытается буферизовать тело или бэкенд начнет вычитывать его без лимита, наступит исчерпание RAM (OOM Crash). Стандартная библиотека Go предоставляет идиоматичную защиту: http.MaxBytesReader(w, r.Body, limit). Это обертка над io.ReadCloser, которая подсчитывает прочитанные байты. При попытке прочитать limit + 1 байт MaxBytesReader устанавливает флаг закрытия соединения и возвращает ошибку типа *http.MaxBytesError, позволяя вернуть корректный код HTTP 413.",
    "step_by_step": "1. Спроектируйте middleware MaxBodySizeMiddleware с параметром maxBytes.\\n2. Оберните r.Body с помощью http.MaxBytesReader.\\n3. В обработчике проверьте ошибку через errors.As(err, &maxBytesErr).\\n4. При обнаружении ошибки верните HTTP 413 с информативным JSON сообщением.\\n5. Протестируйте запросы нормального и избыточного размера.",
    "code_blocks": [{"filename": "max_body.go", "lang": "go", "code": ex9_code}],
    "under_the_hood": "MaxBytesReader также уведомляет http.Server о том, что соединение нельзя повторно использовать (Keep-Alive отключен), так как в сокете остались непрочитанные байты от клиента.",
    "pitfalls": "Не полагайтесь исключительно на заголовок Content-Length: злоумышленник может умышленно указать Content-Length: 10, а в поток сокета передать 100 мегабайт данных. MaxBytesReader защищает на физическом уровне чтения сокета.",
    "bigtech_interview": "Почему в HighLoad API Gateway критично настраивать разные лимиты MaxBytesReader для разных маршрутов (например, 1 МБ для JSON API и 100 МБ для /upload/avatar)?"
})

# Ex 10
ex10_code = """package main

import (
	"crypto/tls"
	"fmt"
	"net"
	"net/http"
	"time"
)

// NewHighPerformanceTransport создает оптимизированный http.Transport для Reverse Proxy.
func NewHighPerformanceTransport() *http.Transport {
	return &http.Transport{
		Proxy: http.ProxyFromEnvironment,
		DialContext: (&net.Dialer{
			Timeout:   5 * time.Second,  // Таймаут установки TCP соединения
			KeepAlive: 30 * time.Second, // Интервал TCP Keep-Alive зондов ядра
		}).DialContext,
		// Тюнинг пула постоянных соединений (Connection Pooling)
		MaxIdleConns:        10000,             // Общий пул свободных соединений шлюза
		MaxIdleConnsPerHost: 2000,              // Пул свободных соединений на каждый конкретный бэкенд
		MaxConnsPerHost:     5000,              // Жесткий лимит параллельных соединений на бэкенд
		IdleConnTimeout:     90 * time.Second,  // Время жизни неактивного соединения в пуле
		TLSHandshakeTimeout: 5 * time.Second,   // Таймаут TLS хэндшейка
		ExpectContinueTimeout: 1 * time.Second, // Ожидание 100-continue
		ResponseHeaderTimeout: 10 * time.Second,// Таймаут ожидания первых байтов ответа бэкенда
		DisableCompression:    false,           // Разрешаем gzip между шлюзом и бэкендами
		ForceAttemptHTTP2:     true,            // Автоматический переход на HTTP/2 при поддержке
		TLSClientConfig: &tls.Config{
			MinVersion: tls.VersionTLS12,
		},
	}
}

func main() {
	transport := NewHighPerformanceTransport()
	fmt.Println("High-Performance Transport успешно инициализирован:")
	fmt.Printf("MaxIdleConns: %d\\nMaxIdleConnsPerHost: %d\\nMaxConnsPerHost: %d\\nIdleConnTimeout: %v\\nForceAttemptHTTP2: %v\\n",
		transport.MaxIdleConns, transport.MaxIdleConnsPerHost, transport.MaxConnsPerHost,
		transport.IdleConnTimeout, transport.ForceAttemptHTTP2)
}
"""
validate_go(ex10_code)

exercises.append({
    "num": 10,
    "title": "Глубокий тюнинг сетевого транспорта (http.Transport)",
    "task": "Спроектируйте высокопроизводительный сетевой транспорт http.Transport для API-шлюза, рассчитанного на 50 000+ RPS. Настройте пул соединений (MaxIdleConns, MaxIdleConnsPerHost), таймауты TCP/TLS рукопожатий и автоматическую поддержку HTTP/2.",
    "theory": "Производительность reverse proxy на 90% определяется конфигурацией http.Transport. Дефолтный http.DefaultTransport категорически непригоден для шлюзов:\\n- DefaultMaxIdleConnsPerHost = 2: после каждого запроса шлюз закрывает лишние TCP-соединения, вызывая постоянный TIME_WAIT шторм на сокетах и постоянные 3-way handshake на каждый запрос.\\nКритический тюнинг:\\n1. MaxIdleConns: 10 000 (суммарно для всех микросервисов).\\n2. MaxIdleConnsPerHost: 2 000 (позволяет переиспользовать открытые сокеты к популярным бэкендам без пересоздания TCP).\\n3. MaxConnsPerHost: 5 000 (защищает медленный бэкенд от лавинообразного создания сокетов шлюзом).\\n4. DialContext Timeout: 3-5 секунд (быстрый отказ, если машина бэкенда недоступна).\\n5. ForceAttemptHTTP2: true (мультиплексирование сотен запросов в один TCP-сокет к внутренним gRPC/HTTP2 бэкендам).",
    "step_by_step": "1. Спроектируйте функцию NewHighPerformanceTransport.\\n2. Настройте net.Dialer с TCP Keep-Alive зондами.\\n3. Установите увеличенные пулы MaxIdleConns и MaxIdleConnsPerHost.\\n4. Настройте лимиты времени ResponseHeaderTimeout и TLSHandshakeTimeout.\\n5. Задайте минимальную версию TLS 1.2.",
    "code_blocks": [{"filename": "tuned_transport.go", "lang": "go", "code": ex10_code}],
    "under_the_hood": "Повторное использование Keep-Alive соединений снижает сетевую задержку с ~15 мс (DNS + TCP + TLS handshake) до субмиллисекундного времени отправки байт в уже прогретый сокет.",
    "pitfalls": "Если установить MaxIdleConnsPerHost большим, но забыть про IdleConnTimeout, прокси будет держать тысячи сокетов открытыми, а файрволы облака (AWS NAT Gateway, Linux conntrack) начнут тихо сбрасывать неактивные соединения, вызывая 'connection reset by peer' на первом запросе.",
    "bigtech_interview": "Почему в микросервисной сети без должного тюнинга MaxIdleConnsPerHost прокси-сервер упирается в исчерпание локальных ephemeral портов (порт 32768–60999) и переходит в состояние TIME_WAIT?"
})

# Ex 11
ex11_code = """package main

import (
	"errors"
	"fmt"
	"sync/atomic"
)

var ErrNoAvailableBackends = errors.New("no backends available in upstream pool")

// UpstreamNode представляет отдельный сервер бэкенда.
type UpstreamNode struct {
	URL       string
	IsAlive   bool
}

// RoundRobinLoadBalancer реализует потокобезопасную циклическую балансировку.
type RoundRobinLoadBalancer struct {
	counter atomic.Uint64
	nodes   []*UpstreamNode
}

func NewRoundRobinLoadBalancer(urls ...string) *RoundRobinLoadBalancer {
	nodes := make([]*UpstreamNode, len(urls))
	for i, u := range urls {
		nodes[i] = &UpstreamNode{URL: u, IsAlive: true}
	}
	return &RoundRobinLoadBalancer{nodes: nodes}
}

func (lb *RoundRobinLoadBalancer) Next() (*UpstreamNode, error) {
	n := len(lb.nodes)
	if n == 0 {
		return nil, ErrNoAvailableBackends
	}

	// Атомарный инкремент счетчика
	idx := lb.counter.Add(1) - 1

	// Проверяем ноды в порядке кругового обхода
	for i := 0; i < n; i++ {
		targetIdx := (int(idx) + i) % n
		node := lb.nodes[targetIdx]
		if node.IsAlive {
			return node, nil
		}
	}

	return nil, ErrNoAvailableBackends
}

func main() {
	lb := NewRoundRobinLoadBalancer(
		"http://10.0.1.10:8080",
		"http://10.0.1.11:8080",
		"http://10.0.1.12:8080",
	)

	// Симулируем 6 запросов
	fmt.Println("Распределение 6 входящих запросов по алгоритму Round-Robin:")
	for i := 1; i <= 6; i++ {
		node, err := lb.Next()
		if err != nil {
			panic(err)
		}
		fmt.Printf("Запрос #%d -> %s\\n", i, node.URL)
	}
}
"""
validate_go(ex11_code)

exercises.append({
    "num": 11,
    "title": "Балансировка нагрузки: алгоритм Round-Robin",
    "task": "Спроектируйте потокобезопасный балансировщик нагрузки RoundRobinLoadBalancer с использованием атомарного счетчика atomic.Uint64. Обеспечьте равномерное циклическое распределение запросов между живыми узлами пула апстримов с пропуском отключенных серверов.",
    "theory": "Round-Robin — базовый алгоритм балансировки нагрузки L7-прокси. Запросы распределяются между серверами пула по кругу. В многопоточном окружении Go критично избежать блокировок sync.Mutex при выборе сервера под нагрузкой в сотни тысяч RPS. Идиоматичное решение: атомарный счетчик atomic.Uint64. Формула выбора индекса: index = counter.Add(1) % len(nodes). При переполнении uint64 (через 1.8 * 10^19 операций) целочисленное переполнение в Go происходит безопасно и непрерывно продолжает цикл. Если текущий узел нездоров, алгоритм проверяет соседние узлы со смещением (idx + i) % n.",
    "step_by_step": "1. Спроектируйте структуру UpstreamNode с адресом и флагом IsAlive.\\n2. Создайте RoundRobinLoadBalancer с полем atomic.Uint64.\\n3. Реализуйте метод Next с атомарным инкрементом и оператором деления по модулю.\\n4. Добавьте проверку активности ноды с циклом поиска живой реплики.\\n5. Протестируйте равномерность распределения 6 запросов по 3 серверам.",
    "code_blocks": [{"filename": "round_robin.go", "lang": "go", "code": ex11_code}],
    "under_the_hood": "atomic.Uint64.Add транслируется в инструкцию LOCK XADD на процессорах x86-64, выполняя операцию за 5–10 тактов процессора без блокировок горутин на системных мьютексах.",
    "pitfalls": "Round-Robin эффективен только в гомогенных средах, где все запросы требуют одинакового времени CPU, а все серверы обладают равной мощностью. Если один запрос тяжелый (генерация PDF), а соседний легкий (healthcheck), Round-Robin неизбежно приведет к перегрузке одного из серверов.",
    "bigtech_interview": "Почему простой Round-Robin приводит к каскадным сбоям кластера при появлении 'медленных запросов' (Slow Requests) и почему в production предпочитают Least Connections или Peak-EWMA?"
})

# Ex 12
ex12_code = """package main

import (
	"errors"
	"fmt"
	"math"
	"sync"
	"sync/atomic"
)

// ActiveNode отслеживает текущее число обрабатываемых запросов.
type ActiveNode struct {
	URL         string
	ActiveConns atomic.Int64
}

// LeastConnectionsBalancer направляет трафик на сервер с наименьшей текущей нагрузкой.
type LeastConnectionsBalancer struct {
	mu    sync.RWMutex
	nodes []*ActiveNode
}

func NewLeastConnectionsBalancer(urls ...string) *LeastConnectionsBalancer {
	nodes := make([]*ActiveNode, len(urls))
	for i, u := range urls {
		nodes[i] = &ActiveNode{URL: u}
	}
	return &LeastConnectionsBalancer{nodes: nodes}
}

func (lb *LeastConnectionsBalancer) Acquire() (*ActiveNode, func(), error) {
	lb.mu.RLock()
	defer lb.mu.RUnlock()

	if len(lb.nodes) == 0 {
		return nil, nil, errors.New("no nodes available")
	}

	var bestNode *ActiveNode
	minConns := int64(math.MaxInt64)

	// Поиск узла с минимальным active connections
	for _, node := range lb.nodes {
		conns := node.ActiveConns.Load()
		if conns < minConns {
			minConns = conns
			bestNode = node
		}
	}

	// Инкрементируем счетчик активных соединений выбранной ноды
	bestNode.ActiveConns.Add(1)

	// Возвращаем функцию освобождения (release callback)
	release := func() {
		bestNode.ActiveConns.Add(-1)
	}

	return bestNode, release, nil
}

func main() {
	lb := NewLeastConnectionsBalancer(
		"http://node-fast-1:8080",
		"http://node-slow-2:8080",
	)

	// Занимаем ноду 1 двумя активными запросами
	lb.nodes[0].ActiveConns.Store(2)
	// Нода 2 свободна (0 соединений)
	lb.nodes[1].ActiveConns.Store(0)

	node, release, err := lb.Acquire()
	if err != nil {
		panic(err)
	}
	defer release()

	fmt.Printf("Least Connections выбрал наименее загруженную ноду: %s (было соединений: 0)\\n", node.URL)
	fmt.Printf("Текущее число соединений на выбранной ноде: %d\\n", node.ActiveConns.Load())
}
"""
validate_go(ex12_code)

exercises.append({
    "num": 12,
    "title": "Балансировка по наименьшему числу соединений (Least Connections)",
    "task": "Реализуйте алгоритм балансировки нагрузки Least Connections. Спроектируйте структуру ActiveNode с атомарным счетчиком activeConns и метод Acquire, возвращающий наименее загруженный сервер и замыкание освобождения счетчика (Release Callback) для defer.",
    "theory": "Алгоритм Least Connections направляет входящий запрос на сервер, который в данный момент обрабатывает наименьшее количество активных запросов (In-Flight Requests). Это кардинально превосходит Round-Robin в гетерогенных нагрузках: если один сервер получил серию тяжелых долгих вычислений, его счетчик соединений вырастет, и шлюз начнет направлять все новые запросы на свободные серверы. Для корректной реализации каждый узел оснащается счетчиком atomic.Int64. При выборе ноды вызывается Add(1), а при завершении ответа бэкенда (в defer-блоке) вызывается Add(-1).",
    "step_by_step": "1. Спроектируйте ActiveNode со счетчиком atomic.Int64.\\n2. Создайте LeastConnectionsBalancer с пулом нод.\\n3. Реализуйте метод Acquire с поиском минимума среди активных счетчиков.\\n4. Реализуйте инкремент и возврат анонимной функции release для декремента.\\n5. Протестируйте автоматический выбор ноды с минимальной нагрузкой.",
    "code_blocks": [{"filename": "least_conns.go", "lang": "go", "code": ex12_code}],
    "under_the_hood": "Паттерн RAII / Release Callback гарантирует, что даже при панике внутри проксирующего обработчика счетчик соединений будет корректно уменьшен через defer, предотвращая утечки метрик нагрузки.",
    "pitfalls": "При одновременном старте кластера или резком всплеске трафика (Thundering Herd) сотни горутин могут одновременно увидеть, что нода #1 имеет 0 соединений, и направить весь начальный шквал запросов именно на нее. Для сглаживания применяют алгоритм 'Power of Two Choices' (выбор двух случайных нод и сравнение нагрузки только между ними).",
    "bigtech_interview": "Что такое алгоритм 'Power of Two Random Choices' (P2C) и почему в высоконагруженных прокси (Envoy, Finagle) он работает быстрее и устойчивее полного перебора всех нод в Least Connections?"
})

# Ex 13
ex13_code = """package main

import (
	"crypto/sha256"
	"encoding/binary"
	"fmt"
	"sort"
	"strconv"
	"sync"
)

// ConsistentHashRing реализует кольцо консистентного хэширования с виртуальными нодами.
type ConsistentHashRing struct {
	mu           sync.RWMutex
	replicas     int               // Число виртуальных нод на один физический сервер
	ring         []uint32          // Отсортированное кольцо хэшей
	virtualNodes map[uint32]string // Маппинг хэша виртуальной ноды в реальный сервер
}

func NewConsistentHashRing(replicas int) *ConsistentHashRing {
	return &ConsistentHashRing{
		replicas:     replicas,
		virtualNodes: make(map[uint32]string),
	}
}

func (c *ConsistentHashRing) hash(key string) uint32 {
	h := sha256.Sum256([]byte(key))
	return binary.BigEndian.Uint32(h[:4])
}

func (c *ConsistentHashRing) Add(nodes ...string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	for _, node := range nodes {
		for i := 0; i < c.replicas; i++ {
			vnodeKey := node + "#" + strconv.Itoa(i)
			h := c.hash(vnodeKey)
			c.ring = append(c.ring, h)
			c.virtualNodes[h] = node
		}
	}
	sort.Slice(c.ring, func(i, j int) bool { return c.ring[i] < c.ring[j] })
}

func (c *ConsistentHashRing) Get(key string) string {
	c.mu.RLock()
	defer c.mu.RUnlock()

	if len(c.ring) == 0 {
		return ""
	}

	h := c.hash(key)
	// Бинарный поиск первой виртуальной ноды с хэшем >= h
	idx := sort.Search(len(c.ring), func(i int) bool {
		return c.ring[i] >= h
	})

	// Если дошли до конца кольца, делаем оборот на первую ноду
	if idx == len(c.ring) {
		idx = 0
	}

	return c.virtualNodes[c.ring[idx]]
}

func main() {
	ring := NewConsistentHashRing(50) // 50 виртуальных нод на сервер
	ring.Add("cache-node-01", "cache-node-02", "cache-node-03")

	users := []string{"user_101", "user_204", "user_991", "user_404", "user_777"}
	fmt.Println("Маршрутизация пользователей на кэширующие бэкенды (Sticky Sessions):")
	for _, u := range users {
		fmt.Printf("Пользователь %s -> %s\\n", u, ring.Get(u))
	}
}
"""
validate_go(ex13_code)

exercises.append({
    "num": 13,
    "title": "Консистентное хэширование (Consistent Hashing) и Sticky Sessions",
    "task": "Реализуйте кольцо консистентного хэширования ConsistentHashRing с поддержкой виртуальных нод (Virtual Nodes / Vnodes) и бинарным поиском по кольцу через sort.Search. Обеспечьте маршрутизацию запросов пользователей на стабильные кэширующие бэкенды (Sticky Sessions).",
    "theory": "В кэширующих прокси и stateful-системах (сессии пользователей, WebSockets, in-memory кэш) критически важно направлять запросы одного и того же клиента на одну и ту же ноду бэкенда. Простое хэширование hash(key) % N катастрофично: при добавлении или падении одной ноды (N меняется на N-1) почти 100% ключей меняют свои серверы, вызывая полный сброс кэша (Cache Stampede). Алгоритм Consistent Hashing размещает серверы и ключи на общем 32-битном кольце хэшей. При выходе ноды из строя перераспределяются только 1/N ключей. Использование виртуальных нод (например, 50-100 vnodes на физическую ноду) гарантирует статистически идеальную равномерность распределения ключей.",
    "step_by_step": "1. Спроектируйте ConsistentHashRing с коэффициентом репликации виртуальных нод.\\n2. Реализуйте хэш-функцию на базе sha256 и binary.BigEndian.Uint32.\\n3. Напишите метод Add для размещения виртуальных меток на кольце и сортировки слайса.\\n4. Реализуйте метод Get с бинарным поиском sort.Search и циклическим замыканием кольца.\\n5. Протестируйте стабильность маршрутизации сессий пользователей.",
    "code_blocks": [{"filename": "consistent_hash.go", "lang": "go", "code": ex13_code}],
    "under_the_hood": "sort.Search выполняет поиск за O(log(V * N)), где V — число виртуальных нод, а N — число физических серверов. Для 10 серверов по 100 vnodes кольцо содержит 1000 элементов, и поиск занимает всего 10 сравнений (менее 50 нс).",
    "pitfalls": "Без виртуальных нод (vnodes = 1) серверы неравномерно распределяются по кольцу из-за кластеризации хэшей, в результате чего один сервер может забрать до 80% всего входящего трафика.",
    "bigtech_interview": "Как консистентное хэширование защищает кэширующие кластеры (Redis, Memcached, Varnish) от каскадного коллапса при падении одной из нод?"
})

# Ex 14
ex14_code = """package main

import (
	"context"
	"fmt"
	"net/http"
	"sync"
	"sync/atomic"
	"time"
)

// MonitoredBackend хранит состояние здоровья узла.
type MonitoredBackend struct {
	URL          string
	IsHealthy    atomic.Bool
	FailureCount atomic.Int32
}

// ActiveHealthChecker выполняет периодический опрос бэкендов в фоновом режиме.
type ActiveHealthChecker struct {
	mu       sync.RWMutex
	backends []*MonitoredBackend
	client   *http.Client
	interval time.Duration
}

func NewActiveHealthChecker(interval time.Duration, urls ...string) *ActiveHealthChecker {
	backends := make([]*MonitoredBackend, len(urls))
	for i, u := range urls {
		b := &MonitoredBackend{URL: u}
		b.IsHealthy.Store(true)
		backends[i] = b
	}

	return &ActiveHealthChecker{
		backends: backends,
		interval: interval,
		client: &http.Client{
			Timeout: 1 * time.Second, // Жесткий таймаут опроса здоровья
		},
	}
}

func (c *ActiveHealthChecker) CheckSingle(ctx context.Context, b *MonitoredBackend) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, b.URL+"/healthz", nil)
	if err != nil {
		c.markFailed(b, err)
		return
	}

	resp, err := c.client.Do(req)
	if err != nil {
		c.markFailed(b, err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		b.FailureCount.Store(0)
		if !b.IsHealthy.Load() {
			b.IsHealthy.Store(true)
			fmt.Printf("--> [HEALTH RESTORED]: Бэкенд %s вернулся в строй!\\n", b.URL)
		}
	} else {
		c.markFailed(b, fmt.Errorf("status code %d", resp.StatusCode))
	}
}

func (c *ActiveHealthChecker) markFailed(b *MonitoredBackend, err error) {
	fails := b.FailureCount.Add(1)
	if fails >= 3 && b.IsHealthy.Load() {
		b.IsHealthy.Store(false)
		fmt.Printf("--> [HEALTH ALERT]: Бэкенд %s исключен из балансировки! (ошибка: %v, сбоев подряд: %d)\\n",
			b.URL, err, fails)
	}
}

func main() {
	checker := NewActiveHealthChecker(5*time.Second, "http://10.0.1.5:8080", "http://10.0.1.6:8080")
	fmt.Printf("Инициализирован Active Health Checker для %d бэкендов\\n", len(checker.backends))
	fmt.Println("Политика: 3 сбоя подряд с таймаутом 1s исключают узел из трафика.")
}
"""
validate_go(ex14_code)

exercises.append({
    "num": 14,
    "title": "Активный опрос здоровья (Active Health Checking)",
    "task": "Реализуйте систему активного мониторинга бэкендов ActiveHealthChecker. Напишите фоновую процедуру опроса эндпоинта /healthz с контролем таймаута 1s через context.WithTimeout, счетчиком сбоев atomic.Int32 и автоматическим исключением нездоровых нод при трех сбоях подряд.",
    "theory": "Активный мониторинг здоровья (Active Health Checking / Probing) — базовый инструмент обеспечения высокой доступности. Прокси-сервер не ждет, пока реальный клиент наткнется на упавший сервер, а периодически (раз в 1-5 секунд) отправляет синтетические HTTP-запросы GET /healthz на каждый узел пула. Параметры надежности:\\n1. Unhealthy Threshold: количество неудачных проверок подряд (обычно 2–3), после которых нода исключается из роутинга. Это исключает реакцию на единичные сетевые флуктуации.\\n2. Healthy Threshold: количество успешных проверок подряд (обычно 2), подтверждающих, что после рестарта бэкенд прогрел внутренние кэши и готов принимать клиентский трафик.\\n3. Timeout: жесткий таймаут пробы (обычно <= 1с), чтобы зависшая нода не блокировала горутину чекера.",
    "step_by_step": "1. Спроектируйте MonitoredBackend со счетчиками на atomic.Bool и atomic.Int32.\\n2. Создайте структуру ActiveHealthChecker с настроенным http.Client.\\n3. Реализуйте метод CheckSingle с отправкой запроса к /healthz.\\n4. Напишите метод markFailed, исключающий ноду при достижении порога в 3 сбоя.\\n5. Протестируйте логику восстановления статуса IsHealthy при возвращении кода 200.",
    "code_blocks": [{"filename": "active_health.go", "lang": "go", "code": ex14_code}],
    "under_the_hood": "Проверки всех серверов в цикле запускаются в параллельных горутинах с sync.WaitGroup, чтобы опрос медленного сервера не задерживал проверку остальных узлов пула.",
    "pitfalls": "Эндпоинт /healthz не должен проверять доступность внешних баз данных или сторонних сервисов в глубоком режиме (Deep Health Check): если упадет общая база данных Postgres, все бэкенды одновременно объявят себя Unhealthy, и шлюз снимет с балансировки 100% кластера, полностью потушив систему.",
    "bigtech_interview": "В чем разница между Liveness Probe (жив ли процесс) и Readiness Probe (готов ли обрабатывать трафик) в архитектуре Kubernetes и API Gateway? Какой из них должен использовать обратный прокси?"
})

# Ex 15
ex15_code = """package main

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// PassiveNodeMonitor отслеживает реальные клиентские ошибки при проксировании (Outlier Detection).
type PassiveNodeMonitor struct {
	URL             string
	Consecutive5xx  atomic.Int32
	QuarantineUntil atomic.Int64 // Unix nano метка окончания карантина
}

func (n *PassiveNodeMonitor) IsAvailable() bool {
	until := n.QuarantineUntil.Load()
	if until == 0 {
		return true
	}
	// Если время карантина истекло, узел снова допускается к трафику
	if time.Now().UnixNano() > until {
		n.QuarantineUntil.Store(0)
		n.Consecutive5xx.Store(0)
		fmt.Printf("--> [EJECTION OVER]: Сервер %s вышел из карантина и вернулся в балансировку\\n", n.URL)
		return true
	}
	return false
}

func (n *PassiveNodeMonitor) RecordResult(statusCode int) {
	if statusCode >= 500 {
		fails := n.Consecutive5xx.Add(1)
		// Если зафиксировано 5 ошибок 5xx подряд — выбиваем ноду в карантин на 30 секунд
		if fails >= 5 && n.QuarantineUntil.Load() == 0 {
			quarantineDuration := 30 * time.Second
			until := time.Now().Add(quarantineDuration).UnixNano()
			n.QuarantineUntil.Store(until)
			fmt.Printf("--> [OUTLIER DETECTED]: Сервер %s отправлен в карантин на %v (5 ошибок 5xx подряд)!\\n",
				n.URL, quarantineDuration)
		}
	} else {
		// Успешный ответ сбрасывает счетчик последовательных ошибок
		n.Consecutive5xx.Store(0)
	}
}

func main() {
	node := &PassiveNodeMonitor{URL: "http://backend-flakey-01:8080"}

	fmt.Println("Имитация последовательных сбоев сервера при реальных запросах клиентов:")
	for i := 1; i <= 5; i++ {
		node.RecordResult(503)
	}

	fmt.Printf("Доступность сервера после 5 сбоев: %v\\n", node.IsAvailable())
}
"""
validate_go(ex15_code)

exercises.append({
    "num": 15,
    "title": "Пассивный опрос здоровья (Passive / Outlier Detection)",
    "task": "Изучите концепцию пассивного обнаружения аномалий (Outlier Detection / Circuit Breaking per Host). Реализуйте структуру PassiveNodeMonitor, отслеживающую реальные ответы бэкенда на пользовательские запросы и автоматически отправляющую сбоящий узел в карантин на 30 секунд при 5 последовательных ошибках 5xx.",
    "theory": "Активный опрос (Active Health Checking) не спасает, если эндпоинт /healthz возвращает 200 OK, но на 80% пользовательских POST-запросов бэкенд отвечает 500 Internal Server Error (например, поврежден диск или переполнен пул соединений). Пассивный мониторинг (Outlier Detection / Circuit Breaking) наблюдает за реальным рабочим трафиком. Если сервер начинает генерировать аномальное число ошибок (например, 5 сетевых сбоев или кодов 5xx подряд), шлюз признает узел аномальным (Outlier) и временно исключает (ejects) его из балансировки на фиксированное время (Quarantine Window, например, 30 секунд). По истечении времени узел аккуратно возвращается в ротацию.",
    "step_by_step": "1. Спроектируйте PassiveNodeMonitor со счетчиком Consecutive5xx и меткой QuarantineUntil.\\n2. Реализуйте метод RecordResult с анализом HTTP статуса ответа.\\n3. При 5 ошибках 5xx подряд рассчитайте время окончания карантина и сохраните в atomic.Int64.\\n4. Реализуйте метод IsAvailable с lock-free валидацией истечения времени штрафа.\\n5. Протестируйте срабатывание карантина при серии сбоев.",
    "code_blocks": [{"filename": "outlier_detection.go", "lang": "go", "code": ex15_code}],
    "under_the_hood": "В Envoy и Nginx Plus этот механизм называется 'consecutive_5xx ejection'. Он позволяет локализовать сбои отдельных 'серых' нод (grey failures) за миллисекунды, не дожидаясь срабатывания периодического таймера /healthz.",
    "pitfalls": "Защита от полного выбивания кластера (Max Ejection Percent): настройте лимит, запрещающий отправлять в карантин более 50% всех серверов пула. Иначе при глобальном сбое базы данных прокси выбьет все 100% бэкендов, и клиенты получат жесткий 502 на все запросы.",
    "bigtech_interview": "Почему комбинация Active Health Checking и Outlier Detection считается золотым стандартом отказоустойчивости в Envoy и Traefik?"
})

output_path = "/home/ut/.gemini/antigravity-cli/brain/3c5274b6-5dd1-4f9a-8772-d2025a9898f9/scratch/ch93_p1.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print(f"Chapter 93 Part 1 generated successfully: {len(exercises)} exercises.")
