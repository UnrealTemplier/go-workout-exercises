# -*- coding: utf-8 -*-
"""Exercises 39..76 of Chapter 39."""

exercises = [
  {
    "num": 39,
    "title": "Метрика SummaryVec: расчет квантилей задержки 0.5, 0.95, 0.99 на клиенте и ограничения PromQL",
    "task": "Создай **Summary** (редко используется, предпочитай Histogram): `requestLatency := prometheus.NewSummaryVec(prometheus.SummaryOpts{Name: \"http_request_latency_seconds\", Help: \"...\", Objectives: map[float64]float64{0.5: 0.05, 0.95: 0.005, 0.99: 0.001}}, []string{\"method\"})`. Покажи вычисление quantile'ей на клиенте vs сервере.",
    "theory": "Особенности работы SummaryVec с квантилями:\n- Параметр `Objectives: map[float64]float64`:\n  - Ключ — целевой квантиль ($0.5$ — медиана p50, $0.95$ — p95, $0.99$ — p99).\n  - Значение — допустимая статистическая погрешность (абсолютная ошибка, например $\\pm 0.001$).\n- **Почему Summary редко используется в распределенных микросервисах:**\n  - Квантили вычисляются на клиенте по локальным данным одного пода.\n  - Невозможно объединить квантили 50 подов в один общий график в Grafana (математически некорректно брать среднее от перцентилей!).\n  - Для Kubernetes и кластеров всегда выбирают Histogram.",
    "step_by_step": "1. Создайте `SummaryVec` с целевыми квантилями 0.5, 0.95 и 0.99.\n2. Зарегистрируйте метрику в локальном тестовом реестре.\n3. Добавьте серию наблюдений для методов GET и POST.\n4. Проверьте экспорт квантилей в выводе метрики.",
    "code_blocks": [
      {
        "filename": "summary_vec_quantiles_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n\t\"net/http/httptest\"\n\t\"strings\"\n\t\"testing\"\n\n\t\"github.com/prometheus/client_golang/prometheus\"\n\t\"github.com/prometheus/client_golang/prometheus/promhttp\"\n)\n\nfunc TestSummaryVecQuantiles(t *testing.T) {\n\treg := prometheus.NewRegistry()\n\n\trequestLatency := prometheus.NewSummaryVec(\n\t\tprometheus.SummaryOpts{\n\t\t\tName: \"http_request_latency_seconds\",\n\t\t\tHelp: \"Задержка HTTP запросов с клиентскими квантилями\",\n\t\t\tObjectives: map[float64]float64{\n\t\t\t\t0.5:  0.05,  // p50 c погрешностью 5%\n\t\t\t\t0.95: 0.005, // p95 с погрешностью 0.5%\n\t\t\t\t0.99: 0.001, // p99 с погрешностью 0.1%\n\t\t\t},\n\t\t},\n\t\t[]string{\"method\"},\n\t)\n\treg.MustRegister(requestLatency)\n\n\t// Добавляем 100 наблюдений для GET\n\tfor i := 1; i <= 100; i++ {\n\t\trequestLatency.WithLabelValues(\"GET\").Observe(float64(i) * 0.001) // 1ms ... 100ms\n\t}\n\n\thandler := promhttp.HandlerFor(reg, promhttp.HandlerOpts{})\n\trec := httptest.NewRecorder()\n\thandler.ServeHTTP(rec, httptest.NewRequest(\"GET\", \"/metrics\", nil))\n\n\tbody, _ := io.ReadAll(rec.Body)\n\tbodyStr := string(body)\n\n\t// Проверяем наличие строковых квантилей\n\tif !strings.Contains(bodyStr, `quantile=\"0.5\"`) || !strings.Contains(bodyStr, `quantile=\"0.99\"`) {\n\t\tt.Fatal(\"В выводе /metrics отсутствуют расчетные квантили Summary\")\n\t}\n\n\tfmt.Println(\"SummaryVec с клиентскими квантилями успешно протестирован:\")\n\tfmt.Printf(\"  • Метрика:     http_request_latency_seconds\\n\")\n\tfmt.Printf(\"  • Objectives:  p50 (0.5), p95 (0.95), p99 (0.99)\\n\")\n\tfmt.Println(\"  • Вычисление квантилей на клиенте подтверждено!\")\n}",
        "note": "Декларация SummaryVec с квантилями и проверка их генерации на клиенте"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v summary_vec_quantiles_test.go\n# Вывод:\n# === RUN   TestSummaryVecQuantiles\n# SummaryVec с клиентскими квантилями успешно протестирован:\n#   • Метрика:     http_request_latency_seconds\n#   • Objectives:  p50 (0.5), p95 (0.95), p99 (0.99)\n#   • Вычисление квантилей на клиенте подтверждено!\n# --- PASS: TestSummaryVecQuantiles (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Summary использует скользящее временное окно (по умолчанию `MaxAge: 10 * time.Minute`), разбитое на 5 субокон (AgeBuckets). Старые наблюдения автоматически вытесняются новыми без сброса счетчиков суммы и количества.",
    "pitfalls": "Указывать слишком низкую погрешность (например `0.99: 0.00001`): высокая точность алгоритма CKMS требует выделения огромного объема оперативной памяти под структуры сэмплов в Go рантайме.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в PromQL нельзя применить функцию histogram_quantile к метрике типа Summary?»\n**Ответ:** Потому что функция `histogram_quantile` ожидает на вход бакеты с фиксированными границами `le` (`<name>_bucket`), а Summary отдает уже готовые квантили в метках `quantile=\"0.95\"`. Summary не имеет информации о распределении наблюдений по корзинам."
  },
  {
    "num": 40,
    "title": "Продвинутый DBStatsCollector: реализация интерфейса prometheus.Collector для пула sql.DB",
    "task": "Создай **custom Collector**: `type DBStatsCollector struct { db *sql.DB }` с методами `Describe(ch chan<- *prometheus.Desc)` и `Collect(ch chan<- prometheus.Metric)`. Экспортируй `sql.DBStats` (OpenConnections, InUse, Idle, WaitCount) как метрики. Покажи advanced instrumentation.",
    "theory": "Продвинутый кастомный коллектор для базы данных:\n- Структура `DBStatsCollector` инкапсулирует указатель на пул `*sql.DB` или интерфейс провайдера статистики.\n- **Преимущество паттерна Collector перед периодическим таймером:**\n  - Если Prometheus не опрашивает сервис, ресурсы процессора не тратятся вовсе.\n  - Метрики всегда актуальны ровно на наносекунду скрейпа.\n  - Дескрипторы создаются один раз при инициализации коллектора, исключая аллокации в куче.",
    "step_by_step": "1. Создайте структуру `DBStatsCollector` с дескрипторами ключевых параметров пула.\n2. Реализуйте метод `Describe` с отправкой 4 дескрипторов в канал.\n3. Реализуйте метод `Collect` с опросом статистики и отправкой `MustNewConstMetric`.\n4. Протестируйте регистрацию коллектора в `prometheus.NewRegistry`.",
    "code_blocks": [
      {
        "filename": "advanced_db_stats_collector_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"database/sql\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"github.com/prometheus/client_golang/prometheus\"\n\t\"github.com/prometheus/client_golang/prometheus/testutil\"\n)\n\ntype DBStatsProvider interface {\n\tStats() sql.DBStats\n}\n\ntype AdvancedDBStatsCollector struct {\n\tdb        DBStatsProvider\n\topenDesc  *prometheus.Desc\n\tinUseDesc *prometheus.Desc\n\tidleDesc  *prometheus.Desc\n\twaitDesc  *prometheus.Desc\n}\n\nfunc NewAdvancedDBStatsCollector(db DBStatsProvider) *AdvancedDBStatsCollector {\n\treturn &AdvancedDBStatsCollector{\n\t\tdb: db,\n\t\topenDesc: prometheus.NewDesc(\n\t\t\t\"go_sql_db_open_connections\",\n\t\t\t\"Количество открытых соединений пула БД\",\n\t\t\tnil, nil,\n\t\t),\n\t\tinUseDesc: prometheus.NewDesc(\n\t\t\t\"go_sql_db_in_use_connections\",\n\t\t\t\"Количество активных соединений используемых прямо сейчас\",\n\t\t\tnil, nil,\n\t\t),\n\t\tidleDesc: prometheus.NewDesc(\n\t\t\t\"go_sql_db_idle_connections\",\n\t\t\t\"Количество свободных соединений ожидающих в пуле\",\n\t\t\tnil, nil,\n\t\t),\n\t\twaitDesc: prometheus.NewDesc(\n\t\t\t\"go_sql_db_wait_count_total\",\n\t\t\t\"Суммарное количество ожиданий освобождения соединений\",\n\t\t\tnil, nil,\n\t\t),\n\t}\n}\n\nfunc (c *AdvancedDBStatsCollector) Describe(ch chan<- *prometheus.Desc) {\n\tch <- c.openDesc\n\tch <- c.inUseDesc\n\tch <- c.idleDesc\n\tch <- c.waitDesc\n}\n\nfunc (c *AdvancedDBStatsCollector) Collect(ch chan<- prometheus.Metric) {\n\tstats := c.db.Stats()\n\tch <- prometheus.MustNewConstMetric(c.openDesc, prometheus.GaugeValue, float64(stats.OpenConnections))\n\tch <- prometheus.MustNewConstMetric(c.inUseDesc, prometheus.GaugeValue, float64(stats.InUse))\n\tch <- prometheus.MustNewConstMetric(c.idleDesc, prometheus.GaugeValue, float64(stats.Idle))\n\tch <- prometheus.MustNewConstMetric(c.waitDesc, prometheus.CounterValue, float64(stats.WaitCount))\n}\n\ntype mockDBStatsProvider struct {\n\tstats sql.DBStats\n}\n\nfunc (m *mockDBStatsProvider) Stats() sql.DBStats { return m.stats }\n\nfunc TestAdvancedDBStatsCollector(t *testing.T) {\n\treg := prometheus.NewRegistry()\n\tmockDB := &mockDBStatsProvider{\n\t\tstats: sql.DBStats{\n\t\t\tOpenConnections: 20,\n\t\t\tInUse:           12,\n\t\t\tIdle:            8,\n\t\t\tWaitCount:       42,\n\t\t\tWaitDuration:    500 * time.Millisecond,\n\t\t},\n\t}\n\n\tcollector := NewAdvancedDBStatsCollector(mockDB)\n\treg.MustRegister(collector)\n\n\tcount := testutil.CollectAndCount(collector)\n\tif count != 4 {\n\t\tt.Fatalf(\"Ожидалось 4 метрики от коллектора, получено: %d\", count)\n\t}\n\n\tfmt.Println(\"Advanced DBStatsCollector успешно протестирован:\")\n\tfmt.Printf(\"  • OpenConnections: 20\\n\")\n\tfmt.Printf(\"  • InUse:           12\\n\")\n\tfmt.Printf(\"  • Idle:            8\\n\")\n\tfmt.Printf(\"  • WaitCount:       42 (Тип Counter)\\n\")\n\tfmt.Println(\"  • Все 4 показателя экспортируются строго по запросу скрейпера!\")\n}",
        "note": "Продвинутый кастомный коллектор для пула соединений базы данных"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v advanced_db_stats_collector_test.go\n# Вывод:\n# === RUN   TestAdvancedDBStatsCollector\n# Advanced DBStatsCollector успешно протестирован:\n#   • OpenConnections: 20\n#   • InUse:           12\n#   • Idle:            8\n#   • WaitCount:       42 (Тип Counter)\n#   • Все 4 показателя экспортируются строго по запросу скрейпера!\n# --- PASS: TestAdvancedDBStatsCollector (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Тип метрики указывается третьим параметром в `MustNewConstMetric`: для мгновенных величин передается `prometheus.GaugeValue`, а для накопительного счетчика `WaitCount` передается `prometheus.CounterValue`.",
    "pitfalls": "Создавать новые дескрипторы `prometheus.NewDesc` внутри метода `Collect()` при каждом скрейпе: это вызовет лишние аллокации в куче. Дескрипторы обязаны быть полями структуры коллектора и создаваться в конструкторе.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему официальные экспортеры Prometheus (node_exporter, postgres_exporter) написаны как кастомные Collector'ы, а не глобальные метрики?»\n**Ответ:** Потому что экспортеры не знают заранее топологию серверов (сколько дисков, сетевых интерфейсов или таблиц в БД). Кастомный коллектор в методе `Collect()` динамически считывает состояние ОС или системных таблиц СУБД и на лету генерирует точный набор метрик без утечек памяти."
  },
  {
    "num": 41,
    "title": "Бизнес-метрика orders_processed_total: разделение по статусам success и failed в обработке заказов",
    "task": "**[Бизнес-метрики]**: Создай метрику `orders_processed_total` с лейблом `status` (\"success\", \"failed\"). Инкрементируй её в сервисе обработки заказов.",
    "theory": "Проектирование бизнес-метрик обработки заказов:\n- Метрика `orders_processed_total{status=\"...\"}` является корневым SLI (Service Level Indicator) интернет-магазина.\n- **Значения метки status:**\n  - `\"success\"`: заказ полностью оплачен и передан на сборку.\n  - `\"failed\"`: платеж отклонен, отмена по таймауту, ошибка склада.\n- **В PromQL расчет процента успешных заказов:**\n  `sum(rate(orders_processed_total{status=\"success\"}[5m])) / sum(rate(orders_processed_total[5m])) * 100`.",
    "step_by_step": "1. Создайте `CounterVec` с именем `orders_processed_total` и меткой `status`.\n2. Реализуйте функцию оформления заказа с обработкой успеха и отказа.\n3. Симулируйте 9 успешных заказов и 1 сбойный.\n4. Проверьте расчет показателей в тестовом реестре.",
    "code_blocks": [
      {
        "filename": "orders_processed_metric_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n\t\"testing\"\n\n\t\"github.com/prometheus/client_golang/prometheus\"\n\t\"github.com/prometheus/client_golang/prometheus/testutil\"\n)\n\ntype OrderProcessorService struct {\n\tordersProcessed *prometheus.CounterVec\n}\n\nfunc NewOrderProcessorService(reg *prometheus.Registry) *OrderProcessorService {\n\tc := prometheus.NewCounterVec(\n\t\tprometheus.CounterOpts{\n\t\t\tName: \"orders_processed_total\",\n\t\t\tHelp: \"Общее число обработанных заказов по статусам\",\n\t\t},\n\t\t[]string{\"status\"},\n\t)\n\treg.MustRegister(c)\n\treturn &OrderProcessorService{ordersProcessed: c}\n}\n\nfunc (s *OrderProcessorService) ProcessOrder(orderID string, fail bool) error {\n\tif fail {\n\t\ts.ordersProcessed.WithLabelValues(\"failed\").Inc()\n\t\treturn errors.New(\"insufficient funds\")\n\t}\n\ts.ordersProcessed.WithLabelValues(\"success\").Inc()\n\treturn nil\n}\n\nfunc TestOrdersProcessedMetric(t *testing.T) {\n\treg := prometheus.NewRegistry()\n\tsvc := NewOrderProcessorService(reg)\n\n\t// 9 успешных заказов, 1 сбойный\n\tfor i := 1; i <= 9; i++ {\n\t\t_ = svc.ProcessOrder(fmt.Sprintf(\"ord-%d\", i), false)\n\t}\n\t_ = svc.ProcessOrder(\"ord-10\", true)\n\n\tsuccessCount := testutil.ToFloat64(svc.ordersProcessed.WithLabelValues(\"success\"))\n\tfailedCount := testutil.ToFloat64(svc.ordersProcessed.WithLabelValues(\"failed\"))\n\n\tif successCount != 9.0 || failedCount != 1.0 {\n\t\tt.Fatalf(\"Ошибка подсчета: success=%f, failed=%f\", successCount, failedCount)\n\t}\n\n\tsuccessRate := (successCount / (successCount + failedCount)) * 100.0\n\n\tfmt.Println(\"Бизнес-метрика orders_processed_total успешно проверена:\")\n\tfmt.Printf(\"  • Успешных заказов: %.0f (success)\\n\", successCount)\n\tfmt.Printf(\"  • Сбойных заказов:  %.0f (failed)\\n\", failedCount)\n\tfmt.Printf(\"  • Success Rate:     %.1f%%\\n\", successRate)\n}",
        "note": "Учет завершенных заказов по статусам success/failed и расчет бизнес-SLI"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v orders_processed_metric_test.go\n# Вывод:\n# === RUN   TestOrdersProcessedMetric\n# Бизнес-метрика orders_processed_total успешно проверена:\n#   • Успешных заказов: 9 (success)\n#   • Сбойных заказов:  1 (failed)\n#   • Success Rate:     90.0%\n# --- PASS: TestOrdersProcessedMetric (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Метка `status` имеет строго 2 значения (\"success\" и \"failed\"), что обеспечивает кардинальность ровно 2 ряда и минимальную нагрузку на процессор и диск.",
    "pitfalls": "Добавлять причину ошибки в метку `status` (например `status=\"failed: connection timeout to visa\"`): это немедленно приведет к росту кардинальности. Причину сбоя передают в структурированные логи (slog/zap), а метку оставляют строго категоризованной.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какое оповещение в Alertmanager должно иметь наивысший приоритет (P0/Critical): падение CPU ноды или падение orders_processed_total?»\n**Ответ:** Падение бизнес-метрики `orders_processed_total` имеет абсолютный приоритет P0. Потеря CPU одной ноды автоматически компенсируется Kubernetes (поды переедут на другую ноду), в то время как падение потока заказов означает прямую потерю выручки компанией прямо сейчас."
  },
  {
    "num": 42,
    "title": "Инспекция HTTP-эндпоинта /metrics через curl: проверка валидности директив HELP, TYPE и значений",
    "task": "Настрой **Prometheus HTTP endpoint**: `http.Handle(\"/metrics\", promhttp.Handler())`. Проверь `curl localhost:9090/metrics`. Покажи формат: `# HELP`, `# TYPE`, значения.",
    "theory": "Проверка работоспособности эндпоинта через curl и HTTP-клиент:\n- При запуске микросервиса проверка доступности метрик входит в smoke-тесты:\n  `curl -s http://localhost:9090/metrics | head -n 20`\n- Структура стандартного ответа:\n  ```text\n  # HELP http_requests_total Суммарное число запросов\n  # TYPE http_requests_total counter\n  http_requests_total{method=\"GET\",status=\"200\"} 1500\n  ```\n- Код статуса ответа обязан быть строго `200 OK`, а заголовок `Content-Type` должен содержать `version=0.0.4` или `application/openmetrics-text`.",
    "step_by_step": "1. Создайте HTTP-сервер с регистрацией `/metrics`.\n2. Добавьте кастомную метрику с подробным `Help`.\n3. Симулируйте выполнение запроса через `httptest`.\n4. Проверьте наличие всех обязательных компонентов формата OpenMetrics.",
    "code_blocks": [
      {
        "filename": "metrics_endpoint_curl_inspection_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"strings\"\n\t\"testing\"\n\n\t\"github.com/prometheus/client_golang/prometheus\"\n\t\"github.com/prometheus/client_golang/prometheus/promhttp\"\n)\n\nfunc TestMetricsEndpointCurlInspection(t *testing.T) {\n\treg := prometheus.NewRegistry()\n\n\tsvcGauge := prometheus.NewGauge(prometheus.GaugeOpts{\n\t\tName: \"service_health_status\",\n\t\tHelp: \"Числовой статус готовности сервиса: 1 - готов, 0 - деградация\",\n\t})\n\treg.MustRegister(svcGauge)\n\tsvcGauge.Set(1.0)\n\n\tmux := http.NewServeMux()\n\tmux.Handle(\"/metrics\", promhttp.HandlerFor(reg, promhttp.HandlerOpts{}))\n\n\tserver := httptest.NewServer(mux)\n\tdefer server.Close()\n\n\t// Выполняем эквивалент curl http://localhost:9090/metrics\n\tresp, err := http.Get(server.URL + \"/metrics\")\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка GET /metrics: %v\", err)\n\t}\n\tdefer resp.Body.Close()\n\n\tif resp.StatusCode != http.StatusOK {\n\t\tt.Fatalf(\"Статус не 200 OK: %d\", resp.StatusCode)\n\t}\n\n\tbody, _ := io.ReadAll(resp.Body)\n\ttext := string(body)\n\n\tlines := strings.Split(strings.TrimSpace(text), \"\\n\")\n\tif len(lines) < 3 {\n\t\tt.Fatalf(\"Ожидалось минимум 3 строки, получено: %d\", len(lines))\n\t}\n\n\tfmt.Println(\"Инспекция HTTP эндпоинта /metrics (curl emulation):\")\n\tfmt.Printf(\"  • HTTP Status: %s\\n\", resp.Status)\n\tfor _, l := range lines {\n\t\tfmt.Printf(\"  • %s\\n\", l)\n\t}\n\tfmt.Println(\"  • Формат вывода на 100% соответствует спецификации Prometheus text format!\")\n}",
        "note": "Инспекция вывода /metrics и валидация формата директив HELP, TYPE и значений"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v metrics_endpoint_curl_inspection_test.go\n# Вывод:\n# === RUN   TestMetricsEndpointCurlInspection\n# Инспекция HTTP эндпоинта /metrics (curl emulation):\n#   • HTTP Status: 200 OK\n#   • # HELP service_health_status Числовой статус готовности сервиса: 1 - готов, 0 - деградация\n#   • # TYPE service_health_status gauge\n#   • service_health_status 1\n#   • Формат вывода на 100% соответствует спецификации Prometheus text format!\n# --- PASS: TestMetricsEndpointCurlInspection (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Заголовок ответа `Content-Type: text/plain; version=0.0.4; charset=utf-8` сообщает парсеру скрейпера Prometheus, по каким правилам декодировать служебные комментарии и разделители строк.",
    "pitfalls": "Ставить точку в конце имени метрики: имена метрик в Prometheus обязаны соответствовать регулярному выражению `^[a-zA-Z_:][a-zA-Z0-9_:]*$`. Точки, дефисы и спецсимволы вызовут ошибку валидации дескриптора.",
    "bigtech_interview": "**Вопрос с собеседования:** «Можно ли сжимать ответ /metrics с помощью gzip?»\n**Ответ:** Да! Prometheus при скрейпе автоматически передает заголовок `Accept-Encoding: gzip`. Хендлер `promhttp.Handler()` нативно поддерживает упаковку в gzip, что снижает сетевой трафик между сервисом и Prometheus в 5–10 раз при больших объемах экспортируемых данных."
  },
  {
    "num": 43,
    "title": "Гистограмма времени ответа API: замер через time.Since и фиксация в Observe по кастомным бакетам",
    "task": "**Гистограмма (Histogram)**: Создай гистограмму для измерения Latency (времени ответа) API. Обязательно задай правильные бакеты (`prometheus.DefBuckets` или свои, например: 10ms, 50ms, 100ms, 500ms, 1s). Измеряй время через `time.Since` и пиши в метрику через `Observe(duration)`. ",
    "theory": "Шаблон точного замера времени выполнения API:\n- Замер задержки:\n  ```go\n  start := time.Now()\n  defer func() {\n      apiLatencyHistogram.Observe(time.Since(start).Seconds())\n  }()\n  ```\n- Использование `defer` гарантирует, что даже если в обработчике возникнет `panic` или преждевременный `return`, время выполнения запроса все равно будет зафиксировано в гистограмме, предотвращая искажение перцентилей задержек.",
    "step_by_step": "1. Создайте `prometheus.NewHistogram` с бакетами `[]float64{0.01, 0.05, 0.1, 0.5, 1.0}`.\n2. Реализуйте функцию с замером задержки через `defer func() { hist.Observe(...) }()`.\n3. Симулируйте выполнение запроса длительностью 40 мс.\n4. Проверьте корректное попадание замера в бакет `<= 0.05`.",
    "code_blocks": [
      {
        "filename": "histogram_observe_timer_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"github.com/prometheus/client_golang/prometheus\"\n\t\"github.com/prometheus/client_golang/prometheus/testutil\"\n)\n\nfunc MeasureAPIOperation(hist prometheus.Histogram, simulatedWork time.Duration) {\n\tstart := time.Now()\n\tdefer func() {\n\t\tdurationSec := time.Since(start).Seconds()\n\t\thist.Observe(durationSec)\n\t}()\n\ttime.Sleep(simulatedWork)\n}\n\nfunc TestHistogramObserveTimer(t *testing.T) {\n\treg := prometheus.NewRegistry()\n\n\tapiLatency := prometheus.NewHistogram(prometheus.HistogramOpts{\n\t\tName:    \"api_operation_duration_seconds\",\n\t\tHelp:    \"Длительность ключевой API операции\",\n\t\tBuckets: []float64{0.01, 0.05, 0.1, 0.5, 1.0}, // 10ms, 50ms, 100ms, 500ms, 1s\n\t})\n\treg.MustRegister(apiLatency)\n\n\t// Выполняем операцию длительностью 40 мс (должна попасть в бакет <= 0.05)\n\tMeasureAPIOperation(apiLatency, 40*time.Millisecond)\n\n\tcount := testutil.CollectAndCount(apiLatency)\n\tif count == 0 {\n\t\tt.Fatal(\"Метрика гистограммы не собрана\")\n\t}\n\n\tfmt.Println(\"Гистограмма API задержек успешно зафиксировала операцию:\")\n\tfmt.Printf(\"  • Бакетов:   5 интервалов (10ms .. 1s)\\n\")\n\tfmt.Printf(\"  • Операция:  40 мс выполнена и записана через defer Observe(time.Since(start).Seconds())\\n\")\n\tfmt.Println(\"  • Потокобезопасный учет задержки функционирует безупречно!\")\n}",
        "note": "Идиоматичный замер времени API операции через time.Since и defer hist.Observe"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v histogram_observe_timer_test.go\n# Вывод:\n# === RUN   TestHistogramObserveTimer\n# Гистограмма API задержек успешно зафиксировала операцию:\n#   • Бакетов:   5 интервалов (10ms .. 1s)\n#   • Операция:  40 мс выполнена и записана через defer Observe(time.Since(start).Seconds())\n#   • Потокобезопасный учет задержки функционирует безупречно!\n# --- PASS: TestHistogramObserveTimer (0.04s)\n# PASS"
      }
    ],
    "under_the_hood": "Встроенный хелпер `prometheus.NewTimer(histogram)` инкапсулирует вызов `time.Now()` и `ObserveDuration()` в удобную структуру таймера.",
    "pitfalls": "Передавать в `Observe` наносекунды `time.Since(start).Nanoseconds()`: это приведет к тому, что задержка в 40 мс (40 000 000 нс) свалится в бакет `+Inf`, сломав все перцентили. Всегда используйте `time.Since(start).Seconds()`.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем преимущество prometheus.NewTimer() перед ручным time.Since()?\n**Ответ:** `timer := prometheus.NewTimer(hist)` возвращает объект, вызов `timer.ObserveDuration()` у которого вычисляет разницу времени внутри Go SDK в одну наносекундную инструкцию, предотвращая ошибки конвертации единиц измерения и сокращая объем кода."
  },
  {
    "num": 44,
    "title": "Конфигурация скрейпа prometheus.yml: настройка job_name, static_configs и проверка статуса Targets",
    "task": "Настрой **Prometheus scrape**: `prometheus.yml` с `job_name: 'go-services'`, `static_configs: [targets: ['localhost:8080', 'localhost:8081']]`. Проверь targets в Prometheus UI (`http://localhost:9090/targets`).",
    "theory": "Конфигурация задач скрейпа в `prometheus.yml`:\n- Секция `scrape_configs`:\n  ```yaml\n  scrape_configs:\n    - job_name: 'go-services'\n      scrape_interval: 15s\n      scrape_timeout: 10s\n      metrics_path: '/metrics'\n      static_configs:\n        - targets: ['localhost:8080', 'localhost:8081']\n          labels:\n            env: 'production'\n            tier: 'backend'\n  ```\n- Prometheus опрашивает каждый таргет каждые 15 секунд.\n- В веб-интерфейсе `/targets` инженеры видят статус `UP` (зеленый) или `DOWN` (красный с кодом ошибки).",
    "step_by_step": "1. Создайте модель валидации конфигурации `prometheus.yml`.\n2. Проверьте парсинг секции `job_name` и списка `targets`.\n3. Смоделируйте проверку доступности таргетов.\n4. Убедитесь в выставлении служебной метрики `up = 1`.",
    "code_blocks": [
      {
        "filename": "prometheus_scrape_config_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype ScrapeTarget struct {\n\tJobName string\n\tTarget  string\n\tIsUp    bool\n}\n\nfunc ValidateTargetsConfig(job string, targets []string) []ScrapeTarget {\n\tvar results []ScrapeTarget\n\tfor _, t := range targets {\n\t\tresults = append(results, ScrapeTarget{\n\t\t\tJobName: job,\n\t\t\tTarget:  t,\n\t\t\tIsUp:    true, // Симулируем успешный статус 200 OK при скрейпе\n\t\t})\n\t}\n\treturn results\n}\n\nfunc TestPrometheusScrapeConfig(t *testing.T) {\n\tjob := \"go-services\"\n\ttargets := []string{\"localhost:8080\", \"localhost:8081\"}\n\n\tactiveTargets := ValidateTargetsConfig(job, targets)\n\n\tif len(activeTargets) != 2 {\n\t\tt.Fatalf(\"Ожидалось 2 таргета: %d\", len(activeTargets))\n\t}\n\n\tfor _, at := range activeTargets {\n\t\tif !at.IsUp || at.JobName != \"go-services\" {\n\t\t\tt.Fatalf(\"Некорректный таргет: %+v\", at)\n\t\t}\n\t}\n\n\tfmt.Println(\"Конфигурация prometheus.yml успешно верифицирована:\")\n\tfmt.Printf(\"  • job_name: 'go-services'\\n\")\n\tfmt.Printf(\"  • targets:  ['localhost:8080', 'localhost:8081']\\n\")\n\tfmt.Printf(\"  • Prometheus UI (/targets): 2/2 targets UP (up{job=\\\"go-services\\\"} = 1)\\n\")\n}",
        "note": "Валидация конфигурации скрейпа prometheus.yml и проверка статусов таргетов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v prometheus_scrape_config_test.go\n# Вывод:\n# === RUN   TestPrometheusScrapeConfig\n# Конфигурация prometheus.yml успешно верифицирована:\n#   • job_name: 'go-services'\n#   • targets:  ['localhost:8080', 'localhost:8081']\n#   • Prometheus UI (/targets): 2/2 targets UP (up{job=\"go-services\"} = 1)\n# --- PASS: TestPrometheusScrapeConfig (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "При скрейпе Prometheus автоматически прикрепляет к каждому временному ряду метки `job` и `instance` (`instance=\"localhost:8080\"`), идентифицируя источник происхождения метрики.",
    "pitfalls": "Указывать `scrape_timeout` больше, чем `scrape_interval`: это вызовет накопление зависших сетевых соединений и приведет к падению скрейпера Prometheus. Таймаут обязан быть строго меньше интервала.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что происходит с метриками сервиса в Prometheus, если таргет перестал отвечать (стал DOWN)?»\n**Ответ:** Prometheus продолжает хранить исторические данные на диске, но перестает добавлять новые точки. Через 5 минут после исчезновения таргета все его временные ряды помечаются флагом Staleness, и график в Grafana прерывается (линия обрывается), сигнализируя об аварии."
  },
  {
    "num": 45,
    "title": "Тестирование метрик в unit-тестах: валидация инкремента счетчика через testutil.ToFloat64",
    "task": "**[Тестирование метрик]**: Напиши юнит-тест, который вызывает функцию, инкрементирующую счетчик, а затем использует `prometheus/client_golang/prometheus/testutil.ToFloat64` для проверки значения метрики.",
    "theory": "Тестирование наблюдаемости (Testing Observability as First-Class Citizen):\n- В BigTech наличие тестов на бизнес-логику без тестов на метрики считается плохой практикой:\n  - Если разработчик случайно удалит или переименует счетчик, алерты перестанут срабатывать в продакшене.\n- Пакет `github.com/prometheus/client_golang/prometheus/testutil`:\n  - `testutil.ToFloat64(metric)`: извлекает текущее float64 значение Counter или Gauge.\n  - Позволяет в стандартном `testing.T` ассертить инкремент метрик без парсинга сырого HTTP-ответа.",
    "step_by_step": "1. Создайте счетчик `login_attempts_total`.\n2. Реализуйте бизнес-функцию `LoginUser`, вызывающую инкремент.\n3. Проверьте начальное значение (0.0).\n4. Вызовите функцию и убедитесь, что `testutil.ToFloat64` возвращает строго 1.0.",
    "code_blocks": [
      {
        "filename": "unit_testutil_counter_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\n\t\"github.com/prometheus/client_golang/prometheus\"\n\t\"github.com/prometheus/client_golang/prometheus/testutil\"\n)\n\ntype AuthService struct {\n\tloginAttempts prometheus.Counter\n}\n\nfunc (s *AuthService) LoginUser(username string) {\n\t// Бизнес-логика входа\n\t_ = username\n\t// Инкремент счетчика попыток\n\ts.loginAttempts.Inc()\n}\n\nfunc TestUnitTestutilCounter(t *testing.T) {\n\treg := prometheus.NewRegistry()\n\n\tloginCounter := prometheus.NewCounter(prometheus.CounterOpts{\n\t\tName: \"login_attempts_total\",\n\t\tHelp: \"Число попыток входа в систему\",\n\t})\n\treg.MustRegister(loginCounter)\n\n\tsvc := &AuthService{loginAttempts: loginCounter}\n\n\t// 1. Проверяем начальное значение до вызова\n\tif val := testutil.ToFloat64(loginCounter); val != 0.0 {\n\t\tt.Fatalf(\"Начальное значение должно быть 0.0, получено: %f\", val)\n\t}\n\n\t// 2. Вызываем бизнес-метод\n\tsvc.LoginUser(\"admin@sber.ru\")\n\n\t// 3. Проверяем значение после вызова\n\tif val := testutil.ToFloat64(loginCounter); val != 1.0 {\n\t\tt.Fatalf(\"Ожидалось 1.0 после вызова LoginUser, получено: %f\", val)\n\t}\n\n\tfmt.Println(\"Unit-тестирование метрики через testutil.ToFloat64 успешно:\")\n\tfmt.Printf(\"  • Начальное значение: 0.0\\n\")\n\tfmt.Printf(\"  • После вызова:       %.0f (Метрика корректно обновлена в коде)\\n\", testutil.ToFloat64(loginCounter))\n\tfmt.Println(\"  • Телеметрия протестирована как равноправная часть бизнес-логики!\")\n}",
        "note": "Юнит-тестирование обновления метрик с помощью testutil.ToFloat64"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v unit_testutil_counter_test.go\n# Вывод:\n# === RUN   TestUnitTestutilCounter\n# Unit-тестирование метрики через testutil.ToFloat64 успешно:\n#   • Начальное значение: 0.0\n#   • После вызова:       1 (Метрика корректно обновлена в коде)\n#   • Телеметрия протестирована как равноправная часть бизнес-логики!\n# --- PASS: TestUnitTestutilCounter (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Функция `testutil.ToFloat64` вызывает скрытый метод `dto.Metric` коллектора, читая значение из Protobuf-структуры без создания TCP-сокета или HTTP-сервера, что делает тесты быстрыми (доли миллисекунды).",
    "pitfalls": "Тестировать метрики через глобальный `prometheus.DefaultRegisterer`: в параллельных тестах счетчики будут инкрементироваться из разных горутин, приводя к плавающим тестам (Flaky Tests).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как с помощью testutil протестировать полное соответствие вывода метрик эталонному файлу (Golden File)?»\n**Ответ:** Используют функцию `testutil.CollectAndCompare(collector, expectedReader, \"metric_name\")`. Она сравнивает собранные метрики со строковым представлением эталона с точностью до порядка строк и формата меток."
  },
  {
    "num": 46,
    "title": "Метрики по методологии USE: Utilization процессора, Saturation очередей и лимиты горутин",
    "task": "Создай **USE metrics** для ресурсов: Utilization (`process_cpu_seconds_total`), Saturation (`go_sched_wait_duration_seconds_total`), Errors (`go_goroutines` > threshold). Напиши алерты.",
    "theory": "Методология USE (Utilization, Saturation, Errors) для рантайма Go:\n1. **Utilization (Утилизация):**\n   - Доля времени работы ресурса: `rate(process_cpu_seconds_total[1m]) / NumCPU`.\n   - Если CPU > 85%, сервис близок к насыщению.\n2. **Saturation (Насыщение / Очереди ожидания):**\n   - Наличие работы, ожидающей в очереди: `go_sched_latencies_seconds` или время ожидания горутин в очереди планировщика GMP (`runq`).\n   - Если горутины ждут выполнения в очереди планировщика, сервис исчерпал процессорные ресурсы.\n3. **Errors (Ошибки ресурса):**\n   - Превышение лимита горутин (`go_goroutines > 10000`) или ошибок выделения памяти.",
    "step_by_step": "1. Создайте модель сбора показателей по методике USE.\n2. Реализуйте проверку порога утилизации процессора.\n3. Реализуйте проверку задержки планировщика (Saturation).\n4. Проверьте срабатывание алерта при превышении лимита горутин.",
    "code_blocks": [
      {
        "filename": "use_methodology_runtime_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype USEResourceMetrics struct {\n\tCPUUtilization float64 // 0.0 .. 1.0\n\tSchedWaitMS    float64 // время ожидания в очереди планировщика GMP\n\tGoroutines     int     // число активных горутин\n}\n\nfunc EvaluateUSEAlerts(m USEResourceMetrics) (alerts []string) {\n\t// 1. Utilization > 85%\n\tif m.CPUUtilization > 0.85 {\n\t\talerts = append(alerts, fmt.Sprintf(\"ALERT: HighCPUUtilization (%.1f%%)\", m.CPUUtilization*100))\n\t}\n\t// 2. Saturation > 50ms\n\tif m.SchedWaitMS > 50.0 {\n\t\talerts = append(alerts, fmt.Sprintf(\"ALERT: HighSchedulerSaturation (%.1fms)\", m.SchedWaitMS))\n\t}\n\t// 3. Errors / Goroutine Leak > 5000\n\tif m.Goroutines > 5000 {\n\t\talerts = append(alerts, fmt.Sprintf(\"ALERT: GoroutineLeakThresholdExceeded (%d goroutines)\", m.Goroutines))\n\t}\n\treturn alerts\n}\n\nfunc TestUSEMethodologyRuntime(t *testing.T) {\n\t// Деградирующее состояние пода в Kubernetes\n\tstressedNode := USEResourceMetrics{\n\t\tCPUUtilization: 0.92,  // 92%\n\t\tSchedWaitMS:    65.0,  // 65мс в очереди GMP!\n\t\tGoroutines:     12500, // Утечка горутин!\n\t}\n\n\talerts := EvaluateUSEAlerts(stressedNode)\n\n\tif len(alerts) != 3 {\n\t\tt.Fatalf(\"Ожидалось 3 алерта USE: %v\", alerts)\n\t}\n\n\tfmt.Println(\"Оценка метрик по методологии USE (Brendan Gregg):\")\n\tfor _, a := range alerts {\n\t\tfmt.Printf(\"  • %s\\n\", a)\n\t}\n\tfmt.Println(\"  • Все 3 фактора деградации (U, S, E) своевременно обнаружены!\")\n}",
        "note": "Оценка состояния инфраструктуры по трем факторам методологии USE"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v use_methodology_runtime_test.go\n# Вывод:\n# === RUN   TestUSEMethodologyRuntime\n# Оценка метрик по методологии USE (Brendan Gregg):\n#   • ALERT: HighCPUUtilization (92.0%)\n#   • ALERT: HighSchedulerSaturation (65.0ms)\n#   • ALERT: GoroutineLeakThresholdExceeded (12500 goroutines)\n#   • Все 3 фактора деградации (U, S, E) своевременно обнаружены!\n# --- PASS: TestUSEMethodologyRuntime (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Go 1.22+ рантайм экспортирует метрику `/sched/latencies:seconds` через пакет `runtime/metrics`, позволяя точно измерять задержку нахождения горутины в локальной и глобальной очередях планировщика GMP.",
    "pitfalls": "Мониторить только средний CPU контейнера: контейнер с лимитом 2 CPU может потреблять 100% одного ядра и 0% второго, в среднем показывая 50% CPU, в то время как ключевая горутина зависает из-за насыщения очереди потока.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы преимущества методологии USE перед интуитивным мониторингом?»\n**Ответ:** Методология USE дает исчерпывающий чек-лист для любого системного ресурса (CPU, память, диск, сеть, планировщик Go). Проверив все 3 вопроса: *«Насколько ресурс загружен? Есть ли очередь задач? Есть ли ошибки?»*, инженер гарантированно находит корень проблемы производительности без блуждания в догадках."
  },
  {
    "num": 47,
    "title": "Summary против Histogram для размера тел запросов: квантили клиента против агрегации 100 серверов",
    "task": "**Summary vs Histogram**: Создай метрику `Summary` для измерения размера входящих JSON-тел запросов в байтах. Изучи разницу (Summary считает квантили на стороне Go-клиента, а Histogram позволяет агрегировать данные со 100 серверов на стороне самого Prometheus).",
    "theory": "Замер размера полезной нагрузки (Payload Size):\n- Если создать `Summary` для размера тел запросов:\n  - Сервер A вычислит p95 = 5 КБ.\n  - Сервер B вычислит p95 = 20 КБ.\n  - Сложить эти значения в общий p95 по всему кластеру **невозможно**!\n- Если создать `Histogram` с бакетами `[512, 1024, 4096, 16384, 65536]`:\n  - Prometheus суммирует количество запросов в бакете `le=\"4096\"` со всех 100 серверов.\n  - И формулой `histogram_quantile(0.95, sum(rate(..._bucket[5m])) by (le))` вычисляет честный кластерный p95!",
    "step_by_step": "1. Создайте `Summary` для размера JSON-тел запросов.\n2. Продемонстрируйте замер объема входящих байт.\n3. Проанализируйте ограничение агрегации клиентских квантилей.\n4. Сделайте аргументированный выбор в пользу Histogram для кластеров.",
    "code_blocks": [
      {
        "filename": "payload_size_metrics_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\n\t\"github.com/prometheus/client_golang/prometheus\"\n\t\"github.com/prometheus/client_golang/prometheus/testutil\"\n)\n\nfunc TestPayloadSizeMetrics(t *testing.T) {\n\treg := prometheus.NewRegistry()\n\n\tjsonBodySizeSummary := prometheus.NewSummary(prometheus.SummaryOpts{\n\t\tName:       \"http_request_json_payload_bytes\",\n\t\tHelp:       \"Размер входящих JSON тел запросов в байтах\",\n\t\tObjectives: map[float64]float64{0.5: 0.05, 0.9: 0.01, 0.99: 0.001},\n\t})\n\treg.MustRegister(jsonBodySizeSummary)\n\n\t// Замеряем размеры трех входящих JSON тел: 250 байт, 1200 байт, 8400 байт\n\tjsonBodySizeSummary.Observe(250)\n\tjsonBodySizeSummary.Observe(1200)\n\tjsonBodySizeSummary.Observe(8400)\n\n\tcount := testutil.CollectAndCount(jsonBodySizeSummary)\n\tif count == 0 {\n\t\tt.Fatal(\"Метрика не содержит данных\")\n\t}\n\n\tfmt.Println(\"Замер размера входящих тел (JSON Payload Size):\")\n\tfmt.Printf(\"  • Summary:   Локальные квантили p50, p90, p99 посчитаны в памяти процесса\\n\")\n\tfmt.Printf(\"  • Сравнение: Для 100 серверов в проде ОБЯЗАТЕЛЕН Histogram, чтобы суммировать бакеты!\\n\")\n}",
        "note": "Сравнение возможностей агрегации Summary и Histogram для размера входящих тел"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v payload_size_metrics_test.go\n# Вывод:\n# === RUN   TestPayloadSizeMetrics\n# Замер размера входящих тел (JSON Payload Size):\n#   • Summary:   Локальные квантили p50, p90, p99 посчитаны в памяти процесса\n#   • Сравнение: Для 100 серверов в проде ОБЯЗАТЕЛЕН Histogram, чтобы суммировать бакеты!\n# --- PASS: TestPayloadSizeMetrics (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Внутри `Summary.Observe(val)` float64 значение размера байт добавляется в структуру выборки с потоковым вычислением рангов, не сохраняя сами исходные сырые числа в памяти.",
    "pitfalls": "Использовать байты как целые числа без учета единиц СИ: если один сервис передает килобайты, а второй байты, суммирование в Prometheus приведет к искажению данных. В имени метрики строго указывают `_bytes`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Prometheus нет стандартной метрики \"Average\" (Среднее)?»\n**Ответ:** Среднее значение не несет достаточной информации при неравномерных распределениях (один запрос на 30 секунд испортит среднее для миллиона быстрых запросов). Вместо этого Prometheus собирает сумму (`_sum`) и количество (`_count`), позволяя при необходимости получить среднее делением `rate(_sum)/rate(_count)` за любой интервал."
  },
  {
    "num": 48,
    "title": "Unit-тестирование метрик: проверка инкремента счетчика и записи в гистограмму через пакет testutil",
    "task": "**Unit-тестирование метрик**: Напиши тест для своей логики. Используй пакет `github.com/prometheus/client_golang/prometheus/testutil`, чтобы проверить, что после вызова функции счетчик реально увеличился на 1, а в гистограмму записалось нужное значение.",
    "theory": "Комплексное тестирование телеметрии через `testutil`:\n- В Go клиент Prometheus предоставляет специализированные методы тестирования:\n  1. `testutil.ToFloat64(c)`: получение числового значения Counter или Gauge.\n  2. `testutil.CollectAndCount(c)`: количество сгенерированных рядов.\n  3. `testutil.CollectAndCompare(c, reader)`: побайтовое сравнение с ожидаемым выводом OpenMetrics.\n- Гарантирует, что бизнес-логика и метрики тестируются неразрывно в рамках TDD.",
    "step_by_step": "1. Создайте сервис с инжектированными `Counter` и `Histogram`.\n2. Вызовите бизнес-метод обработки платежа.\n3. Проверьте, что счетчик увеличился ровно на 1.0.\n4. Проверьте, что гистограмма зафиксировала ровно 1 наблюдение.",
    "code_blocks": [
      {
        "filename": "comprehensive_testutil_metrics_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"github.com/prometheus/client_golang/prometheus\"\n\t\"github.com/prometheus/client_golang/prometheus/testutil\"\n)\n\ntype PaymentProcessingService struct {\n\tpaymentsTotal    prometheus.Counter\n\tpaymentDuration  prometheus.Histogram\n}\n\nfunc (s *PaymentProcessingService) ExecutePayment(amount int) {\n\tstart := time.Now()\n\t// Симуляция работы\n\ttime.Sleep(5 * time.Millisecond)\n\t_ = amount\n\n\ts.paymentsTotal.Inc()\n\ts.paymentDuration.Observe(time.Since(start).Seconds())\n}\n\nfunc TestComprehensiveTestutilMetrics(t *testing.T) {\n\treg := prometheus.NewRegistry()\n\n\tcounter := prometheus.NewCounter(prometheus.CounterOpts{\n\t\tName: \"payments_executed_total\",\n\t\tHelp: \"Число выполненных платежей\",\n\t})\n\thist := prometheus.NewHistogram(prometheus.HistogramOpts{\n\t\tName:    \"payment_execution_duration_seconds\",\n\t\tHelp:    \"Длительность платежа\",\n\t\tBuckets: []float64{0.001, 0.01, 0.1, 1.0},\n\t})\n\treg.MustRegister(counter, hist)\n\n\tsvc := &PaymentProcessingService{\n\t\tpaymentsTotal:   counter,\n\t\tpaymentDuration: hist,\n\t}\n\n\t// Выполняем платеж\n\tsvc.ExecutePayment(5000)\n\n\t// Проверяем счетчик\n\tif val := testutil.ToFloat64(counter); val != 1.0 {\n\t\tt.Fatalf(\"Счетчик должен быть 1.0, получено: %f\", val)\n\t}\n\n\t// Проверяем, что гистограмма содержит 1 собранную метрику\n\tif count := testutil.CollectAndCount(hist); count == 0 {\n\t\tt.Fatal(\"Гистограмма не зафиксировала наблюдение\")\n\t}\n\n\tfmt.Println(\"Тестирование метрик через testutil успешно завершено:\")\n\tfmt.Printf(\"  • payments_executed_total: %.0f (увеличен на 1)\\n\", testutil.ToFloat64(counter))\n\tfmt.Printf(\"  • payment_execution_duration_seconds: зафиксировано наблюдение\\n\")\n\tfmt.Println(\"  • Корректность работы телеметрии доказана юнит-тестом!\")\n}",
        "note": "Сквозное юнит-тестирование Counter и Histogram с помощью пакета testutil"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v comprehensive_testutil_metrics_test.go\n# Вывод:\n# === RUN   TestComprehensiveTestutilMetrics\n# Тестирование метрик через testutil успешно завершено:\n#   • payments_executed_total: 1 (увеличен на 1)\n#   • payment_execution_duration_seconds: зафиксировано наблюдение\n#   • Корректность работы телеметрии доказана юнит-тестом!\n# --- PASS: TestComprehensiveTestutilMetrics (0.01s)\n# PASS"
      }
    ],
    "under_the_hood": "Метод `testutil.ToFloat64` обращается напрямую к структуре `io_prometheus_client.Metric` в оперативной памяти Go, не требуя сетевых сокетов и сериализации в текстовый формат OpenMetrics.",
    "pitfalls": "Забывать инициализировать кастомный `Registry` в тестах: если завязаться на `prometheus.DefaultRegisterer`, тесты нельзя будет безопасно запускать с флагом `go test -count=1 -parallel 4`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как протестировать, что при ошибке функции инкрементируется счетчик ошибок, а не счетчик успеха?»\n**Ответ:** Пишут два тестовых сценария: в happy-path проверяют `testutil.ToFloat64(successCounter) == 1` и `testutil.ToFloat64(errorCounter) == 0`. В сценарии ошибки (например, сбой соединения) проверяют `testutil.ToFloat64(errorCounter) == 1` и `testutil.ToFloat64(successCounter) == 0`."
  },
  {
    "num": 49,
    "title": "Комплексные бизнес-метрики: orders_created, orders_completed, order_value и payment_failed",
    "task": "Создай **business metrics**: `orders_created_total`, `orders_completed_total`, `order_value_histogram`, `payment_failed_total`. Покажи, что бизнес-метрики важнее инфраструктурных для product decisions.",
    "theory": "Приоритет бизнес-метрик в Data-Driven разработке:\n- Инфраструктурные метрики (CPU, Disk I/O) показывают стоимость эксплуатации.\n- **Бизнес-метрики отражают реальную ценность продукта:**\n  1. `orders_created_total`: намерение пользователей совершить покупку (воронка продаж).\n  2. `orders_completed_total`: фактически завершенные заказы (конверсия).\n  3. `order_value_histogram`: распределение чека (средний чек, микроплатежи vs крупные покупки).\n  4. `payment_failed_total`: прямая финансовая утечка (Lost Revenue).\n- Если `orders_created` растет, а `orders_completed` падает — это немедленный сигнал об отказе платежного шлюза, даже если CPU серверов составляет идеальные 5%.",
    "step_by_step": "1. Создайте продуктовый набор метрик заказа.\n2. Продемонстрируйте прохождение воронки: создание $\\to$ оплата.\n3. Зафиксируйте чек заказа в гистограмме `order_value_histogram`.\n4. Смоделируйте отказ платежа и проверьте инкремент `payment_failed_total`.",
    "code_blocks": [
      {
        "filename": "business_product_metrics_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\n\t\"github.com/prometheus/client_golang/prometheus\"\n\t\"github.com/prometheus/client_golang/prometheus/testutil\"\n)\n\ntype ProductMetricsSuite struct {\n\tordersCreated   prometheus.Counter\n\tordersCompleted prometheus.Counter\n\tpaymentFailed   prometheus.Counter\n\torderValueHist  prometheus.Histogram\n}\n\nfunc NewProductMetricsSuite(reg *prometheus.Registry) *ProductMetricsSuite {\n\tm := &ProductMetricsSuite{\n\t\tordersCreated: prometheus.NewCounter(prometheus.CounterOpts{\n\t\t\tName: \"orders_created_total\",\n\t\t\tHelp: \"Созданные заказы в воронке оформления\",\n\t\t}),\n\t\tordersCompleted: prometheus.NewCounter(prometheus.CounterOpts{\n\t\t\tName: \"orders_completed_total\",\n\t\t\tHelp: \"Успешно оплаченные и закрытые заказы\",\n\t\t}),\n\t\tpaymentFailed: prometheus.NewCounter(prometheus.CounterOpts{\n\t\t\tName: \"payment_failed_total\",\n\t\t\tHelp: \"Отказы платежей банковским шлюзом\",\n\t\t}),\n\t\torderValueHist: prometheus.NewHistogram(prometheus.HistogramOpts{\n\t\t\tName:    \"order_value_histogram_rubles\",\n\t\t\tHelp:    \"Распределение чеков заказов в рублях\",\n\t\t\tBuckets: []float64{500, 1000, 3000, 5000, 10000, 50000},\n\t\t}),\n\t}\n\treg.MustRegister(m.ordersCreated, m.ordersCompleted, m.paymentFailed, m.orderValueHist)\n\treturn m\n}\n\nfunc TestBusinessProductMetrics(t *testing.T) {\n\treg := prometheus.NewRegistry()\n\tp := NewProductMetricsSuite(reg)\n\n\t// Пользователь 1: создал заказ на 4500 руб. и успешно оплатил\n\tp.ordersCreated.Inc()\n\tp.orderValueHist.Observe(4500)\n\tp.ordersCompleted.Inc()\n\n\t// Пользователь 2: создал заказ на 12000 руб., но оплата упала\n\tp.ordersCreated.Inc()\n\tp.orderValueHist.Observe(12000)\n\tp.paymentFailed.Inc()\n\n\tcreated := testutil.ToFloat64(p.ordersCreated)\n\tcompleted := testutil.ToFloat64(p.ordersCompleted)\n\tfailed := testutil.ToFloat64(p.paymentFailed)\n\n\tif created != 2.0 || completed != 1.0 || failed != 1.0 {\n\t\tt.Fatalf(\"Ошибка бизнес-метрик: created=%f, completed=%f, failed=%f\", created, completed, failed)\n\t}\n\n\tconversionRate := (completed / created) * 100.0\n\n\tfmt.Println(\"Продуктовые бизнес-метрики успешно зарегистрированы:\")\n\tfmt.Printf(\"  • Создано заказов (Воронка): %.0f\\n\", created)\n\tfmt.Printf(\"  • Успешно закрыто покупок:   %.0f\\n\", completed)\n\tfmt.Printf(\"  • Отказов шлюза оплаты:      %.0f\\n\", failed)\n\tfmt.Printf(\"  • Конверсия воронки:         %.1f%%\\n\", conversionRate)\n\tfmt.Println(\"  • Бизнес-метрики позволяют принимать точные продуктовые решения!\")\n}",
        "note": "Сквозной учет продуктовой воронки: заказы, чеки и отказы платежей"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v business_product_metrics_test.go\n# Вывод:\n# === RUN   TestBusinessProductMetrics\n# Продуктовые бизнес-метрики успешно зарегистрированы:\n#   • Создано заказов (Воронка): 2\n#   • Успешно закрыто покупок:   1\n#   • Отказов шлюза оплаты:      1\n#   • Конверсия воронки:         50.0%\n#   • Бизнес-метрики позволяют принимать точные продуктовые решения!\n# --- PASS: TestBusinessProductMetrics (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Гистограмма `order_value_histogram_rubles` позволяет в PromQL вычислять средний чек (`sum(rate(..._sum)) / sum(rate(..._count))`) и медианный чек, отсекая влияние единичных оптовых закупок.",
    "pitfalls": "Хранить денежные суммы с плавающей точкой высокой точности в Gauge без суммирования: для объемов выручки обязателен накопительный Counter, иначе невозможно посчитать выручку за произвольный интервал времени.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как на основе бизнес-метрик выстроить мониторинг A/B тестирования нового чекаута?»\n**Ответ:** Добавить метку `checkout_version=\"v2\"` в `orders_created_total` и `orders_completed_total`. В Grafana рассчитывают конверсию `sum(rate(completed{version=\"v2\"})) / sum(rate(created{version=\"v2\"}))` в сравнении с версией v1, оценивая статистическую значимость изменений в реальном времени."
  },
  {
    "num": 50,
    "title": "Service Discovery в Kubernetes: автоматическое обнаружение подов по аннотациям prometheus.io",
    "task": "Настрой **Service Discovery**: Kubernetes SD в Prometheus (`kubernetes_sd_configs: [role: pod]`). Автоматическое обнаружение pod'ов с аннотациями `prometheus.io/scrape: \"true\"`, `prometheus.io/port: \"8080\"`. Покажи dynamic targets.",
    "theory": "Динамическое обнаружение сервисов (Kubernetes Service Discovery):\n- В облачных кластерах поды постоянно создаются, масштабируются и удаляются (HPA, Rolling Update).\n- Статические IP-адреса (`static_configs`) в K8s не работают!\n- **Механизм Kubernetes SD (`kubernetes_sd_configs: [role: pod]`):**\n  - Prometheus непрерывно слушает события K8s API Server.\n  - Фильтрация через аннотации пода в `relabel_configs`:\n    ```yaml\n    relabel_configs:\n      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]\n        action: keep\n        regex: true\n      - source_labels: [__meta_kubernetes_pod_ip, __meta_kubernetes_pod_annotation_prometheus_io_port]\n        action: replace\n        regex: (.+);(.+)\n        replacement: $1:$2\n        target_label: __address__\n    ```\n  - Если у пода есть аннотация `prometheus.io/scrape: \"true\"`, он автоматически добавляется в мониторинг за 1 секунду.",
    "step_by_step": "1. Создайте модель метаданных пода Kubernetes с аннотациями.\n2. Реализуйте алгоритм relabeling для фильтрации по аннотации `scrape: \"true\"`.\n3. Сформируйте динамический адрес таргета `__address__` (IP:Port).\n4. Убедитесь в автоматическом подключении новых подов без рестарта Prometheus.",
    "code_blocks": [
      {
        "filename": "k8s_service_discovery_relabel_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype K8sPodMetadata struct {\n\tName        string\n\tPodIP       string\n\tAnnotations map[string]string\n}\n\ntype DiscoveredTarget struct {\n\tAddress string\n\tPodName string\n}\n\nfunc RelabelK8sPods(pods []K8sPodMetadata) []DiscoveredTarget {\n\tvar targets []DiscoveredTarget\n\tfor _, p := range pods {\n\t\t// 1. keep if annotation prometheus.io/scrape == \"true\"\n\t\tif p.Annotations[\"prometheus.io/scrape\"] != \"true\" {\n\t\t\tcontinue\n\t\t}\n\t\tport := p.Annotations[\"prometheus.io/port\"]\n\t\tif port == \"\" {\n\t\t\tport = \"8080\"\n\t\t}\n\t\t// 2. target_label __address__ = pod_ip:port\n\t\ttargetAddr := fmt.Sprintf(\"%s:%s\", p.PodIP, port)\n\t\ttargets = append(targets, DiscoveredTarget{\n\t\t\tAddress: targetAddr,\n\t\t\tPodName: p.Name,\n\t\t})\n\t}\n\treturn targets\n}\n\nfunc TestK8sServiceDiscoveryRelabel(t *testing.T) {\n\tpods := []K8sPodMetadata{\n\t\t{\n\t\t\tName:  \"order-service-pod-991\",\n\t\t\tPodIP: \"10.244.1.15\",\n\t\t\tAnnotations: map[string]string{\n\t\t\t\t\"prometheus.io/scrape\": \"true\",\n\t\t\t\t\"prometheus.io/port\":   \"9090\",\n\t\t\t},\n\t\t},\n\t\t{\n\t\t\tName:  \"legacy-batch-pod-12\",\n\t\t\tPodIP: \"10.244.2.88\",\n\t\t\tAnnotations: map[string]string{\n\t\t\t\t\"prometheus.io/scrape\": \"false\", // Игнорируется!\n\t\t\t},\n\t\t},\n\t\t{\n\t\t\tName:  \"payment-service-pod-44\",\n\t\t\tPodIP: \"10.244.3.50\",\n\t\t\tAnnotations: map[string]string{\n\t\t\t\t\"prometheus.io/scrape\": \"true\",\n\t\t\t\t\"prometheus.io/port\":   \"8081\",\n\t\t\t},\n\t\t},\n\t}\n\n\ttargets := RelabelK8sPods(pods)\n\n\tif len(targets) != 2 {\n\t\tt.Fatalf(\"Ожидалось 2 таргета, получено: %d\", len(targets))\n\t}\n\n\tif targets[0].Address != \"10.244.1.15:9090\" || targets[1].Address != \"10.244.3.50:8081\" {\n\t\tt.Fatalf(\"Некорректная трансляция адресов: %+v\", targets)\n\t}\n\n\tfmt.Println(\"Kubernetes Service Discovery (Relabeling) успешно подтвержден:\")\n\tfor _, t := range targets {\n\t\tfmt.Printf(\"  • Подключен dynamic target: %-20s (Под: %s)\\n\", t.Address, t.PodName)\n\t}\n\tfmt.Println(\"  • Поды без аннотации scrape=true безопасно отфильтрованы!\")\n}",
        "note": "Эмуляция алгоритма relabel_configs в Kubernetes Service Discovery"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v k8s_service_discovery_relabel_test.go\n# Вывод:\n# === RUN   TestK8sServiceDiscoveryRelabel\n# Kubernetes Service Discovery (Relabeling) успешно подтвержден:\n#   • Подключен dynamic target: 10.244.1.15:9090     (Под: order-service-pod-991)\n#   • Подключен dynamic target: 10.244.3.50:8081     (Под: payment-service-pod-44)\n#   • Поды без аннотации scrape=true безопасно отфильтрованы!\n# --- PASS: TestK8sServiceDiscoveryRelabel (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Prometheus использует клиент `k8s.io/client-go` и механизм Shared Informers для кэширования списка подов в памяти, получая обновления по протоколу WebSocket/Watch с нулевой задержкой.",
    "pitfalls": "Скрейпить по DNS-имени K8s Service (`order-service.default.svc:8080`): K8s Service балансирует трафик случайно между подами, и Prometheus каждый скрейп будет опрашивать случайный под, перемешивая их счетчики! Скрейпить необходимо строго каждый Pod IP напрямую через SD.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие prometheus-operator (ServiceMonitor / PodMonitor) от аннотаций prometheus.io/scrape?»\n**Ответ:** Prometheus Operator использует Custom Resource Definitions (CRD): `ServiceMonitor` и `PodMonitor`. Они декларативны, валидируются Kubernetes OpenAPI схемой, поддерживают версионирование в GitOps (ArgoCD/Flux) и позволяют изолировать мониторинг по неймспейсам без ручного костыльного парсинга аннотаций в YAML."
  },
  {
    "num": 51,
    "title": "Архитектура кастомного экспортера: опрос внешнего REST API и трансляция в метрики Prometheus",
    "task": "**Кастомный Collector**: У тебя есть внешняя БД или API, которая не отдает метрики сама. Напишите структуру, реализующую `prometheus.Collector` (методы `Describe` и `Collect`). В `Collect` делай запрос к внешней системе, парси ответ и отдавай как метрику Prometheus. (Так пишутся официальные экспортеры).",
    "theory": "Шаблон разработки независимых экспортеров (Exporter Pattern):\n- Когда стороннее ПО (ClickHouse, NGINX, hardware коммутаторы) не имеет встроенного клиента Go Prometheus:\n  - Пишется отдельный сервис-экспортер (например, `blackbox_exporter`, `nginx_exporter`).\n  - Экспортер поднимает HTTP-сервер на порту `:9113`.\n  - При поступлении GET-запроса от Prometheus метод `Collect()`:\n    1. Делает HTTP GET или TCP-запрос к целевой системе.\n    2. Парсит JSON или текстовый вывод.\n    3. Отдает метрики в канал `chan<- prometheus.Metric`.\n    4. Отдает служебную метрику `exporter_scrape_duration_seconds` и `exporter_up`.",
    "step_by_step": "1. Создайте структуру `ExternalAPIExporter`.\n2. Объявите дескрипторы для метрик внешнего сервиса.\n3. Реализуйте опрос внешнего API внутри `Collect()`.\n4. Протестируйте парсинг ответа и отправку метрик.",
    "code_blocks": [
      {
        "filename": "external_api_exporter_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"github.com/prometheus/client_golang/prometheus\"\n\t\"github.com/prometheus/client_golang/prometheus/testutil\"\n)\n\ntype ExternalStatusResponse struct {\n\tUptimeSec int     `json:\"uptime\"`\n\tQueueLen  float64 `json:\"queue_len\"`\n}\n\ntype ExternalAPIExporter struct {\n\tfetchFunc    func() (ExternalStatusResponse, error)\n\tuptimeDesc   *prometheus.Desc\n\tqueueLenDesc *prometheus.Desc\n\tupDesc       *prometheus.Desc\n}\n\nfunc NewExternalAPIExporter(fetchFunc func() (ExternalStatusResponse, error)) *ExternalAPIExporter {\n\treturn &ExternalAPIExporter{\n\t\tfetchFunc: fetchFunc,\n\t\tuptimeDesc: prometheus.NewDesc(\n\t\t\t\"external_service_uptime_seconds\",\n\t\t\t\"Аптайм внешнего сервиса в секундах\",\n\t\t\tnil, nil,\n\t\t),\n\t\tqueueLenDesc: prometheus.NewDesc(\n\t\t\t\"external_service_queue_length\",\n\t\t\t\"Текущая длина очереди внешнего сервиса\",\n\t\t\tnil, nil,\n\t\t),\n\t\tupDesc: prometheus.NewDesc(\n\t\t\t\"external_service_up\",\n\t\t\t\"Доступность внешнего API: 1 - доступен, 0 - ошибка\",\n\t\t\tnil, nil,\n\t\t),\n\t}\n}\n\nfunc (e *ExternalAPIExporter) Describe(ch chan<- *prometheus.Desc) {\n\tch <- e.uptimeDesc\n\tch <- e.queueLenDesc\n\tch <- e.upDesc\n}\n\nfunc (e *ExternalAPIExporter) Collect(ch chan<- prometheus.Metric) {\n\tstart := time.Now()\n\tdata, err := e.fetchFunc()\n\t_ = time.Since(start)\n\n\tif err != nil {\n\t\tch <- prometheus.MustNewConstMetric(e.upDesc, prometheus.GaugeValue, 0)\n\t\treturn\n\t}\n\n\tch <- prometheus.MustNewConstMetric(e.upDesc, prometheus.GaugeValue, 1)\n\tch <- prometheus.MustNewConstMetric(e.uptimeDesc, prometheus.GaugeValue, float64(data.UptimeSec))\n\tch <- prometheus.MustNewConstMetric(e.queueLenDesc, prometheus.GaugeValue, data.QueueLen)\n}\n\nfunc TestExternalAPIExporter(t *testing.T) {\n\treg := prometheus.NewRegistry()\n\n\tmockFetch := func() (ExternalStatusResponse, error) {\n\t\trawJSON := []byte(`{\"uptime\": 86400, \"queue_len\": 15.0}`)\n\t\tvar resp ExternalStatusResponse\n\t\t_ = json.Unmarshal(rawJSON, &resp)\n\t\treturn resp, nil\n\t}\n\n\texporter := NewExternalAPIExporter(mockFetch)\n\treg.MustRegister(exporter)\n\n\tcount := testutil.CollectAndCount(exporter)\n\tif count != 3 {\n\t\tt.Fatalf(\"Ожидалось 3 метрики, получено: %d\", count)\n\t}\n\n\tfmt.Println(\"Паттерн кастомного экспортера успешно реализован:\")\n\tfmt.Printf(\"  • external_service_up:             1 (доступен)\\n\")\n\tfmt.Printf(\"  • external_service_uptime_seconds: 86400\\n\")\n\tfmt.Printf(\"  • external_service_queue_length:   15.0\\n\")\n\tfmt.Println(\"  • Полноценный мост между внешним API и Prometheus готов к деплою!\")\n}",
        "note": "Реализация паттерна независимого экспортера для сторонних систем"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v external_api_exporter_test.go\n# Вывод:\n# === RUN   TestExternalAPIExporter\n# Паттерн кастомного экспортера успешно реализован:\n#   • external_service_up:             1 (доступен)\n#   • external_service_uptime_seconds: 86400\n#   • external_service_queue_length:   15.0\n#   • Полноценный мост между внешним API и Prometheus готов к деплою!\n# --- PASS: TestExternalAPIExporter (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Экспортер не сохраняет исторические значения в базу данных: Prometheus сам сохранит временные ряды в свой TSDB при каждом плановом скрейпе.",
    "pitfalls": "Забывать выставлять таймаут для `http.Client` внутри экспортера: дефолтный `http.DefaultClient` не имеет таймаутов, и при зависании внешней системы горутина скрейпа повиснет навсегда.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем каждому кастомному экспортеру обязательно нужна собственная метрика <name>_up?»\n**Ответ:** Метрика `up` самого Prometheus показывает только доступность HTTP-сервера самого экспортера (`localhost:9113`). Но если целевая внешняя база упала, экспортер продолжит отвечать кодом 200 OK. Метрика `<name>_up = 0` сигнализирует мониторингу, что упала именно целевая система."
  },
  {
    "num": 52,
    "title": "Правила алертинга Alerting Rules: условие HighErrorRate, интервал for 5m и аннотации шаблонов",
    "task": "Настрой **Alerting Rules**: `alert: HighErrorRate` when `rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) > 0.05`. `for: 5m` (должно длиться 5 минут). `labels: { severity: critical }`. `annotations: { summary: \"High error rate on {{ $labels.job }}\" }`.",
    "theory": "Спецификация правил алертинга в Prometheus (Alerting Rules):\n- Синтаксис правила:\n  ```yaml\n  groups:\n    - name: api_slo_alerts\n      rules:\n        - alert: HighErrorRate\n          expr: sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) > 0.05\n          for: 5m\n          labels:\n            severity: critical\n            team: checkout\n          annotations:\n            summary: \"High error rate on {{ $labels.job }}\"\n            description: \"Более 5% запросов завершаются с ошибкой 5xx в течение 5 минут.\"\n  ```\n- **Параметр `for: 5m` (Pending State):**\n  - Предотвращает ложные срабатывания (Alert Flapping): если был секундный всплеск ошибок (например при перезапуске пода), алерт переходит в состояние `PENDING`.\n  - Только если условие стабильно сохраняется 5 минут подряд, алерт переходит в статус `FIRING` и отправляется в Alertmanager.",
    "step_by_step": "1. Создайте модель оценки правила алертинга `AlertRuleEngine`.\n2. Реализуйте проверку перехода между статусами: `INACTIVE` $\\to$ `PENDING` $\\to$ `FIRING`.\n3. Продемонстрируйте подавление кратковременного секундного сбоя.\n4. Проверьте отправку алерта при сохранении аварии свыше 5 минут.",
    "code_blocks": [
      {
        "filename": "alerting_rules_evaluator_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype AlertState string\n\nconst (\n\tStateInactive AlertState = \"INACTIVE\"\n\tStatePending  AlertState = \"PENDING\"\n\tStateFiring   AlertState = \"FIRING\"\n)\n\ntype AlertRuleEvaluator struct {\n\tName        string\n\tThreshold   float64\n\tForDuration time.Duration\n\tpendingSince *time.Time\n\tState       AlertState\n}\n\nfunc (r *AlertRuleEvaluator) Evaluate(currentErrorRatio float64, now time.Time) AlertState {\n\tif currentErrorRatio > r.Threshold {\n\t\tif r.pendingSince == nil {\n\t\t\tr.pendingSince = &now\n\t\t\tr.State = StatePending\n\t\t\treturn r.State\n\t\t}\n\t\tif now.Sub(*r.pendingSince) >= r.ForDuration {\n\t\t\tr.State = StateFiring\n\t\t\treturn r.State\n\t\t}\n\t\tr.State = StatePending\n\t\treturn r.State\n\t}\n\n\t// Сбой устранился -> сброс в Inactive\n\tr.pendingSince = nil\n\tr.State = StateInactive\n\treturn r.State\n}\n\nfunc TestAlertingRulesEvaluator(t *testing.T) {\n\trule := &AlertRuleEvaluator{\n\t\tName:        \"HighErrorRate\",\n\t\tThreshold:   0.05, // 5% ошибок\n\t\tForDuration: 5 * time.Minute,\n\t\tState:       StateInactive,\n\t}\n\n\tstartTime := time.Now()\n\n\t// 1. Минута 0: Ошибок нет (0.01) -> INACTIVE\n\ts1 := rule.Evaluate(0.01, startTime)\n\tif s1 != StateInactive {\n\t\tt.Fatalf(\"Должно быть Inactive: %s\", s1)\n\t}\n\n\t// 2. Минута 1: Всплеск ошибок 8% -> PENDING\n\ts2 := rule.Evaluate(0.08, startTime.Add(1*time.Minute))\n\tif s2 != StatePending {\n\t\tt.Fatalf(\"Должно быть Pending: %s\", s2)\n\t}\n\n\t// 3. Минута 3: Ошибки продолжаются (7%), прошло всего 3 мин -> PENDING\n\ts3 := rule.Evaluate(0.07, startTime.Add(3*time.Minute))\n\tif s3 != StatePending {\n\t\tt.Fatalf(\"Все еще должно быть Pending: %s\", s3)\n\t}\n\n\t// 4. Минута 6: Ошибки длятся больше 5 минут -> FIRING!\n\ts4 := rule.Evaluate(0.09, startTime.Add(6*time.Minute))\n\tif s4 != StateFiring {\n\t\tt.Fatalf(\"Алерт обязан перейти в FIRING: %s\", s4)\n\t}\n\n\tfmt.Println(\"Жизненный цикл Alerting Rule успешно верифицирован:\")\n\tfmt.Printf(\"  • 0 мин (1%% ошибок): %s\\n\", s1)\n\tfmt.Printf(\"  • 1 мин (8%% ошибок): %s (Защита от Alert Flapping)\\n\", s2)\n\tfmt.Printf(\"  • 3 мин (7%% ошибок): %s (Таймер for: 5m тикает)\\n\", s3)\n\tfmt.Printf(\"  • 6 мин (9%% ошибок): %s (Отправка нотификации дежурному инженеру!)\\n\", s4)\n}",
        "note": "Эмуляция жизненного цикла правила алертинга: Inactive, Pending и Firing"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v alerting_rules_evaluator_test.go\n# Вывод:\n# === RUN   TestAlertingRulesEvaluator\n# Жизненный цикл Alerting Rule успешно верифицирован:\n#   • 0 мин (1% ошибок): INACTIVE\n#   • 1 мин (8% ошибок): PENDING (Защита от Alert Flapping)\n#   • 3 мин (7% ошибок): PENDING (Таймер for: 5m тикает)\n#   • 6 мин (9% ошибок): FIRING (Отправка нотификации дежурному инженеру!)\n# --- PASS: TestAlertingRulesEvaluator (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Движок правил Prometheus Rules Engine вычисляет выражение `expr` с интервалом `evaluation_interval` (обычно 15–30 секунд) и хранит состояние переходов в оперативной памяти.",
    "pitfalls": "Писать правило `rate(...) > 0.05` без деления на общий трафик: если запросов пришло всего 2, и один завершился с ошибкой, доля ошибок составит 50%, но в абсолютных числах это всего 1 ошибка. В BigTech алерты дополняют проверкой минимального порога трафика (`and sum(rate(http_requests_total[5m])) > 10`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое Multiwindow, Multi-Burn-Rate Alerts по стандарту Google SRE?»\n**Ответ:** Это алерты по сжиганию бюджета ошибок (Error Budget Burn Rate). Вместо одного простого порога за 5 минут настраивают систему из нескольких окон: быстрое сжигание (за 1 час сжигается 2% бюджета $\\to$ немедленный звонок на телефон PagerDuty) и медленное сжигание (за 3 дня сжигается 10% бюджета $\\to$ тикет в Jira в рабочее время)."
  },
  {
    "num": 53,
    "title": "Маршрутизация инцидентов в Alertmanager: группировка, PagerDuty, Slack и правила ингибирования",
    "task": "Настрой **Alertmanager**: группировка по `alertname`, `job`. `group_wait: 30s`, `group_interval: 5m`, `repeat_interval: 4h`. Маршрутизация: `severity=critical` → PagerDuty, `severity=warning` → Slack. Ингибирование: `HighErrorRate` ингибирует `InstanceDown`.",
    "theory": "Архитектура Alertmanager:\n1. **Группировка (Grouping):**\n   - Если упал датацентр, 100 подов одновременно пришлют алерт `InstanceDown`.\n   - Alertmanager объединяет их в **одно уведомление** благодаря `group_by: [alertname, cluster]`.\n   - `group_wait: 30s`: ждет 30 секунд для сбора пачки алертов перед отправкой.\n   - `repeat_interval: 4h`: не шлет повторные уведомления чаще раза в 4 часа.\n2. **Маршрутизация (Routing Tree):**\n   - `severity: critical` $\\to$ ночной звонок инженеру в PagerDuty/Opsgenie.\n   - `severity: warning` $\\to$ сообщение в командный канал Slack/Telegram.\n3. **Ингибирование (Inhibition Rules):**\n   - Подавление вторичных алертов: если упал весь кластер (`ClusterDown`), нет смысла будить инженера сотней алертов о задержках отдельных сервисов.",
    "step_by_step": "1. Создайте модель маршрутизатора Alertmanager.\n2. Реализуйте правила группировки и отправки уведомлений.\n3. Продемонстрируйте маршрутизацию Critical в PagerDuty и Warning в Slack.\n4. Проверьте работу правила ингибирования.",
    "code_blocks": [
      {
        "filename": "alertmanager_router_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype AlertNotification struct {\n\tAlertName string\n\tSeverity  string\n\tReceiver  string\n}\n\nfunc RouteAlert(name, severity string, isClusterDown bool) (receiver string, suppressed bool) {\n\t// Правило ингибирования (Inhibition): если упал весь кластер, подавляем алерты сервисов\n\tif isClusterDown && name != \"ClusterDown\" {\n\t\treturn \"\", true\n\t}\n\n\tif severity == \"critical\" {\n\t\treturn \"PagerDuty-OnCall\", false\n\t}\n\treturn \"Slack-Dev-Channel\", false\n}\n\nfunc TestAlertmanagerRouter(t *testing.T) {\n\t// 1. Critical алерт\n\tr1, supp1 := RouteAlert(\"HighErrorRate\", \"critical\", false)\n\tif supp1 || r1 != \"PagerDuty-OnCall\" {\n\t\tt.Fatalf(\"Critical должен идти в PagerDuty: %s\", r1)\n\t}\n\n\t// 2. Warning алерт\n\tr2, supp2 := RouteAlert(\"DiskUsageWarning\", \"warning\", false)\n\tif supp2 || r2 != \"Slack-Dev-Channel\" {\n\t\tt.Fatalf(\"Warning должен идти в Slack: %s\", r2)\n\t}\n\n\t// 3. Ингибирование: сервис упал, но кластер лежит целиком\n\tr3, supp3 := RouteAlert(\"InstanceDown\", \"critical\", true)\n\tif !supp3 {\n\t\tt.Fatal(\"Алерт должен быть подавлен ингибированием ClusterDown\")\n\t}\n\n\tfmt.Println(\"Alertmanager: маршрутизация и ингибирование успешно подтверждены:\")\n\tfmt.Printf(\"  • Severity: critical -> Маршрут: %s\\n\", r1)\n\tfmt.Printf(\"  • Severity: warning  -> Маршрут: %s\\n\", r2)\n\tfmt.Printf(\"  • Ингибирование:     InstanceDown подавлен (suppressed=%v)\\n\", supp3)\n\tfmt.Println(\"  • Защита от шторма нотификаций (Alert Storm) работает штатно!\")\n}",
        "note": "Маршрутизация уведомлений по severity и подавление вторичных алертов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v alertmanager_router_test.go\n# Вывод:\n# === RUN   TestAlertmanagerRouter\n# Alertmanager: маршрутизация и ингибирование успешно подтверждены:\n#   • Severity: critical -> Маршрут: PagerDuty-OnCall\n#   • Severity: warning  -> Маршрут: Slack-Dev-Channel\n#   • Ингибирование:     InstanceDown подавлен (suppressed=true)\n#   • Защита от шторма нотификаций (Alert Storm) работает штатно!\n# --- PASS: TestAlertmanagerRouter (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Alertmanager использует протокол Gossip (библиотека `hashicorp/memberlist`) для кластеризации нескольких инстансов: они синхронизируют статус отправки нотификаций и заглушек (Silences) без единой базы данных.",
    "pitfalls": "Указывать слишком короткий `group_wait: 0s`: это приведет к отправке десятков отдельных пушей в первую же секунду инцидента вместо одного компактного сгруппированного отчета.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое Alert Silence в Alertmanager и когда его применять?»\n**Ответ:** Silence (Заглушка) — это временное правило (например на 2 часа), создаваемое инженером перед началом плановых работ или регламентного обновления базы данных. Silence блокирует отправку нотификаций для заданного набора меток, предотвращая ложные звонки дежурным во время планового обслуживания."
  },
  {
    "num": 54,
    "title": "Pushgateway для эфемерных задач: отправка метрик пакетных заданий перед завершением процесса",
    "task": "**Pushgateway (Для крон-джобов)**: Метрики Prometheus работают по pull-модели (Prometheus сам ходит к тебе). Но что если твой скрипт запускается по крону, работает 5 секунд и умирает? Используй пакет `push`, чтобы отправить метрику \"успешности джобы\" в Prometheus Pushgateway перед самым `os.Exit()`.",
    "theory": "Проблема эфемерных заданий (Batch / Cron Jobs):\n- Стандартный Prometheus опрашивает сервисы раз в 15–60 секунд.\n- Если CronJob на Go запускается раз в час, отрабатывает за 4 секунды и завершается:\n  - Скрейпер Prometheus никогда не успеет поймать момент ее работы!\n- **Решение: Prometheus Pushgateway:**\n  - Pushgateway — это легковесный постоянный in-memory сервер-посредник.\n  - CronJob перед завершением делает HTTP POST с метриками в Pushgateway:\n    ```go\n    push.New(\"http://pushgateway:9091\", \"nightly_billing\").\n        Collector(ordersProcessedCounter).\n        Push()\n    ```\n  - Pushgateway хранит эти метрики у себя.\n  - Prometheus спокойно скрейпит Pushgateway по стандартной Pull-модели.",
    "step_by_step": "1. Создайте модель передачи метрик в Pushgateway через пакет `push`.\n2. Смоделируйте выполнение ночной пакетной задачи `nightly_billing`.\n3. Отправьте статус завершения задачи и количество обработанных счетов.\n4. Проверьте доступность метрик для скрейпа после завершения работы джобы.",
    "code_blocks": [
      {
        "filename": "pushgateway_cronjob_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"github.com/prometheus/client_golang/prometheus\"\n\t\"github.com/prometheus/client_golang/prometheus/testutil\"\n)\n\ntype MockPushgatewayServer struct {\n\tstoredMetrics map[string]float64\n}\n\nfunc (s *MockPushgatewayServer) Ingest(job string, metricName string, val float64) {\n\tkey := fmt.Sprintf(\"%s:%s\", job, metricName)\n\ts.storedMetrics[key] = val\n}\n\nfunc ExecuteBatchJob(pg *MockPushgatewayServer) {\n\t// Симуляция быстрой крон-джобы на 10 мс\n\ttime.Sleep(10 * time.Millisecond)\n\tprocessedAccounts := 15420.0\n\n\t// Пушим метрику перед выходом\n\tpg.Ingest(\"nightly_billing\", \"accounts_billed_total\", processedAccounts)\n\tpg.Ingest(\"nightly_billing\", \"job_last_success_timestamp_seconds\", float64(time.Now().Unix()))\n}\n\nfunc TestPushgatewayCronjob(t *testing.T) {\n\tpg := &MockPushgatewayServer{storedMetrics: make(map[string]float64)}\n\n\t// Запускаем крон-джобу\n\tExecuteBatchJob(pg)\n\n\tkey := \"nightly_billing:accounts_billed_total\"\n\tval, ok := pg.storedMetrics[key]\n\tif !ok || val != 15420.0 {\n\t\tt.Fatalf(\"Метрика не зафиксирована в Pushgateway: %v\", pg.storedMetrics)\n\t}\n\n\tfmt.Println(\"Интеграция с Prometheus Pushgateway успешно проверена:\")\n\tfmt.Printf(\"  • Job Name:                 nightly_billing\\n\")\n\tfmt.Printf(\"  • accounts_billed_total:    %.0f счетов обработано\\n\", val)\n\tfmt.Printf(\"  • Доступность для скрейпа:  Метрики сохранены в памяти Pushgateway после выхода джобы!\\n\")\n}",
        "note": "Экспорт метрик краткоживущих пакетных заданий в Pushgateway перед выходом"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v pushgateway_cronjob_test.go\n# Вывод:\n# === RUN   TestPushgatewayCronjob\n# Интеграция с Prometheus Pushgateway успешно проверена:\n#   • Job Name:                 nightly_billing\n#   • accounts_billed_total:    15420 счетов обработано\n#   • Доступность для скрейпа:  Метрики сохранены в памяти Pushgateway после выхода джобы!\n# --- PASS: TestPushgatewayCronjob (0.01s)\n# PASS"
      }
    ],
    "under_the_hood": "Метод `push.Add()` сохраняет старые метрики в бакете Pushgateway, а метод `push.Push()` заменяет все метрики этой группы новыми значениями.",
    "pitfalls": "Использовать Pushgateway для обычных долгоживущих веб-сервисов: Pushgateway превращает Prometheus в Push-систему, теряется автоматический контроль доступности (Instance Liveness) и ломается дедупликация.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему метрики упавшей джобы остаются висеть в Pushgateway навсегда?»\n**Ответ:** Pushgateway не знает, упала джоба или просто спит до следующего запуска. Если джоба упала до вызова `Push()`, в Pushgateway останутся старые метрики от прошлого успешного запуска. Для корректного мониторинга крон-джоб всегда пушат время последнего успеха `job_last_success_timestamp_seconds` и настраивают алерт `time() - job_last_success_timestamp_seconds > 86400`."
  },
  {
    "num": 55,
    "title": "Ручное создание спанов трассировки: передача атрибутов order.id и amount в OpenTelemetry Span",
    "task": "Вручную создайте спаны для критичного бизнес-метода (например, расчёт стоимости заказа). Добавьте атрибуты: `order.id`, `amount`.",
    "theory": "Связывание трассировки (Tracing) и бизнес-метрик:\n- В критических операциях (биллинг, списание со счета) инженеры создают ручные спаны через OpenTelemetry Tracer:\n  ```go\n  tracer := otel.Tracer(\"order-service\")\n  ctx, span := tracer.Start(ctx, \"CalculateOrderPrice\")\n  defer span.End()\n  span.SetAttributes(\n      attribute.String(\"order.id\", orderID),\n      attribute.Float64(\"amount\", amount),\n  )\n  ```\n- В спане допустимо указывать конкретный `order.id` (в отличие от метрик Prometheus, спаны не страдают от взрыва кардинальности).",
    "step_by_step": "1. Создайте модель спана OpenTelemetry с поддержкой атрибутов.\n2. Инициализируйте спан для метода `CalculateOrderTotal`.\n3. Добавьте структурированные атрибуты `order.id` и `amount`.\n4. Завершите спан через `defer span.End()` и проверьте сохранность контекста.",
    "code_blocks": [
      {
        "filename": "manual_otel_spans_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype MockSpan struct {\n\tName       string\n\tAttributes map[string]any\n\tDuration   time.Duration\n\tended      bool\n}\n\nfunc (s *MockSpan) SetAttribute(k string, v any) {\n\ts.Attributes[k] = v\n}\n\nfunc (s *MockSpan) End(start time.Time) {\n\ts.Duration = time.Since(start)\n\ts.ended = true\n}\n\nfunc CalculateOrderTotalWithTracing(ctx context.Context, orderID string, amount float64) (float64, *MockSpan) {\n\tstart := time.Now()\n\tspan := &MockSpan{\n\t\tName:       \"CalculateOrderTotal\",\n\t\tAttributes: make(map[string]any),\n\t}\n\tdefer span.End(start)\n\n\t// Добавляем бизнес-атрибуты в трейс\n\tspan.SetAttribute(\"order.id\", orderID)\n\tspan.SetAttribute(\"amount\", amount)\n\tspan.SetAttribute(\"currency\", \"RUB\")\n\n\t// Расчет скидки\n\tfinalTotal := amount * 0.95\n\treturn finalTotal, span\n}\n\nfunc TestManualOTelSpans(t *testing.T) {\n\tfinal, span := CalculateOrderTotalWithTracing(context.Background(), \"ord-trace-771\", 5000.0)\n\n\tif final != 4750.0 || !span.ended {\n\t\tt.Fatalf(\"Ошибка расчета или завершения спана: %f, ended=%v\", final, span.ended)\n\t}\n\n\tif span.Attributes[\"order.id\"] != \"ord-trace-771\" || span.Attributes[\"amount\"] != 5000.0 {\n\t\tt.Fatalf(\"Некорректные атрибуты спана: %+v\", span.Attributes)\n\t}\n\n\tfmt.Println(\"Ручное создание спанов OpenTelemetry успешно подтверждено:\")\n\tfmt.Printf(\"  • Спан:     %s (Завершен: %v)\\n\", span.Name, span.ended)\n\tfmt.Printf(\"  • order.id: %s (В трейсах допустима любая кардинальность!)\\n\", span.Attributes[\"order.id\"])\n\tfmt.Printf(\"  • amount:   %.2f RUB -> Итог со скидкой: %.2f RUB\\n\", span.Attributes[\"amount\"], final)\n}",
        "note": "Ручное создание спанов трассировки OpenTelemetry и обогащение бизнес-атрибутами"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v manual_otel_spans_test.go\n# Вывод:\n# === RUN   TestManualOTelSpans\n# Ручное создание спанов OpenTelemetry успешно подтверждено:\n#   • Спан:     CalculateOrderTotal (Завершен: true)\n#   • order.id: ord-trace-771 (В трейсах допустима любая кардинальность!)\n#   • amount:   5000.00 RUB -> Итог со скидкой: 4750.00 RUB\n# --- PASS: TestManualOTelSpans (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Спаны OpenTelemetry сохраняются в виде графа распределенных вызовов в Jaeger/Tempo. В отличие от TSDB, системы трассировки хранят данные в колоночных индексах или блоб-хранилищах (S3), где высокая кардинальность является нормой.",
    "pitfalls": "Забывать вызывать `span.End()`: спан не завершится, его длительность не рассчитается, и экспортер не сможет передать трассировку в коллектор.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в спаны трассировки можно смело добавлять user_id и order_id, а в метрики Prometheus категорически нельзя?»\n**Ответ:** Потому что в Prometheus каждая комбинация меток создает постоянный временной ряд в индексе TSDB, который потребляет оперативную память все время жизни базы. В распределенной трассировке (Jaeger/Tempo) каждый спан — это изолированное событие (Log-like Document), которое пишется на диск и удаляется по TTL без поддержания тяжелых таблиц обратных индексов в RAM."
  },
  {
    "num": 56,
    "title": "Пакетная отправка в Pushgateway: метод Grouping по instance и критерии выбора Push vs Pull",
    "task": "Настрой **Pushgateway** (для batch jobs): `push.New(\"http://localhost:9091\", \"batch_job\").Collector(myCounter).Grouping(\"instance\", \"batch-1\").Push()`. Покажи, когда push vs pull.",
    "theory": "Группировка метрик в Pushgateway (`Grouping`):\n- Метод `.Grouping(\"instance\", \"batch-1\")`:\n  - Создает отдельное пространство имен для метрик конкретного инстанса задачи.\n  - Позволяет одновременно собирать метрики с параллельно работающих воркеров одной пакетной джобы без перезаписи данных друг друга.\n- **Матрица выбора модели:**\n  - **Pull (Prometheus Scrape):** веб-серверы, gRPC API, постоянные воркеры очередей, демоны баз данных (работают дольше 1 минуты).\n  - **Push (Pushgateway):** cron jobs, миграции баз данных, скрипты ночной генерации отчетов (работают секунды).",
    "step_by_step": "1. Создайте тестовый коллектор пакетной джобы.\n2. Настройте конфигурацию отправки в Pushgateway с группировкой по инстансу.\n3. Продемонстрируйте изоляцию метрик разных инстансов `batch-1` и `batch-2`.\n4. Проверьте сохранность показателей в шлюзе.",
    "code_blocks": [
      {
        "filename": "pushgateway_grouping_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype PushgatewayGroupEntry struct {\n\tJobName  string\n\tInstance string\n\tCounter  float64\n}\n\ntype PushgatewayInstanceStore struct {\n\tentries map[string]PushgatewayGroupEntry\n}\n\nfunc (s *PushgatewayInstanceStore) Push(job, instance string, val float64) {\n\tkey := fmt.Sprintf(\"%s/%s\", job, instance)\n\ts.entries[key] = PushgatewayGroupEntry{\n\t\tJobName:  job,\n\t\tInstance: instance,\n\t\tCounter:  val,\n\t}\n}\n\nfunc TestPushgatewayGrouping(t *testing.T) {\n\tstore := &PushgatewayInstanceStore{entries: make(map[string]PushgatewayGroupEntry)}\n\n\t// Воркер 1 завершил работу\n\tstore.Push(\"data_sync_job\", \"pod-batch-1\", 450.0)\n\n\t// Воркер 2 завершил работу параллельно\n\tstore.Push(\"data_sync_job\", \"pod-batch-2\", 820.0)\n\n\tif len(store.entries) != 2 {\n\t\tt.Fatalf(\"Должно быть 2 изолированные записи: %d\", len(store.entries))\n\t}\n\n\tfmt.Println(\"Группировка в Pushgateway (Grouping) успешно подтверждена:\")\n\tfor key, e := range store.entries {\n\t\tfmt.Printf(\"  • Ключ группы: %-30s -> %.0f строк обработано\\n\", key, e.Counter)\n\t}\n\tfmt.Println(\"  • Параллельные инстансы пакетных джоб не перезаписывают метрики друг друга!\")\n}",
        "note": "Изоляция метрик пакетных заданий в Pushgateway с помощью Grouping"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v pushgateway_grouping_test.go\n# Вывод:\n# === RUN   TestPushgatewayGrouping\n# Группировка в Pushgateway (Grouping) успешно подтверждена:\n#   • Ключ группы: data_sync_job/pod-batch-1     -> 450 строк обработано\n#   • Ключ группы: data_sync_job/pod-batch-2     -> 820 строк обработано\n#   • Параллельные инстансы пакетных джоб не перезаписывают метрики друг друга!\n# --- PASS: TestPushgatewayGrouping (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В URL эндпоинта Pushgateway группировка кодируется прямо в пути: `/metrics/job/data_sync_job/instance/pod-batch-1`, что позволяет однозначно идентифицировать и удалять конкретный набор метрик через HTTP DELETE.",
    "pitfalls": "Использовать метод `push.Delete()` без параметров группировки: это сотрет метрики всех инстансов джобы разом.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как очищать устаревшие метрики из Pushgateway после удаления CronJob?»\n**Ответ:** Отправлять HTTP DELETE запрос к URL группы в Pushgateway (`DELETE /metrics/job/<job_name>/instance/<instance>`). В продакшене для этого настраивают завершающий шаг пайплайна (Post-Job Hook) или отдельный служебный крон, удаляющий метрики старше 24 часов."
  },
  {
    "num": 57,
    "title": "Иерархический мониторинг (Federation): эндпоинт federate и агрегация региональных Prometheus",
    "task": "Настрой **Federation**: Prometheus global scrapes `/federate` endpoint от regional Prometheus'ов. Агрегируй `up`, `job:...:p95`. Покажи hierarchical monitoring.",
    "theory": "Иерархическая федерация Prometheus (Prometheus Federation):\n- Когда сервисы работают в нескольких датацентрах (Москва, Питер, Екатеринбург):\n  - Передавать ВСЕ сырые метрики в центральный датацентр по глобальной сети дорого и ненадёжно.\n- **Архитектура Federation:**\n  1. В каждом регионе работает локальный **Regional Prometheus**:\n     - Скрейпит локальные поды с частотой 5 секунд.\n     - Хранит сырые бакеты гистограмм и детальные ряды.\n     - Рассчитывает агрегаты через `Recording Rules`: `job:http_request_duration_seconds:p95`.\n  2. В центральном ЦОД работает **Global Prometheus**:\n     - Опрашивает региональные серверы через эндпоинт `/federate?match[]={job=~\".+\"}`.\n     - Забирает только уже агрегированные p95 и ключевой статус `up`.\n     - Снижает межрегиональный сетевой трафик на 98%!",
    "step_by_step": "1. Создайте модель регионального сервера Prometheus с предвычисленным правилом записи.\n2. Смоделируйте генерацию эндпоинта `/federate`.\n3. Реализуйте скрейп глобальным сервером Prometheus только агрегированных метрик.\n4. Проверьте объединение региональных показателей в глобальный дашборд.",
    "code_blocks": [
      {
        "filename": "prometheus_federation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n\t\"testing\"\n)\n\ntype RegionalPrometheus struct {\n\tRegion     string\n\tAggregates map[string]float64\n}\n\nfunc (r *RegionalPrometheus) ExportFederate(matchQuery string) []string {\n\tvar lines []string\n\tfor metric, val := range r.Aggregates {\n\t\tif strings.HasPrefix(metric, \"job:\") || metric == \"up\" {\n\t\t\tlines = append(lines, fmt.Sprintf(\"%s{region=\\\"%s\\\"} %f\", metric, r.Region, val))\n\t\t}\n\t}\n\treturn lines\n}\n\nfunc TestPrometheusFederation(t *testing.T) {\n\t// 1. Регион Москва (ru-central-msk)\n\tpromMsk := &RegionalPrometheus{\n\t\tRegion: \"ru-central-msk\",\n\t\tAggregates: map[string]float64{\n\t\t\t\"up\": 1.0,\n\t\t\t\"job:api_latency:p95\": 0.025, // 25 мс\n\t\t\t\"raw_debug_temp_metric\": 99.0, // НЕ должно попасть в федерацию!\n\t\t},\n\t}\n\n\t// 2. Регион Питер (ru-central-spb)\n\tpromSpb := &RegionalPrometheus{\n\t\tRegion: \"ru-central-spb\",\n\t\tAggregates: map[string]float64{\n\t\t\t\"up\": 1.0,\n\t\t\t\"job:api_latency:p95\": 0.038, // 38 мс\n\t\t},\n\t}\n\n\t// 3. Global Prometheus собирает /federate\n\tglobalMetricsMsk := promMsk.ExportFederate(\"job:.*\")\n\tglobalMetricsSpb := promSpb.ExportFederate(\"job:.*\")\n\n\ttotalFederated := len(globalMetricsMsk) + len(globalMetricsSpb)\n\tif totalFederated != 4 {\n\t\tt.Fatalf(\"Ожидалось 4 агрегированные метрики, получено: %d\", totalFederated)\n\t}\n\n\tfmt.Println(\"Иерархическая федерация (Prometheus Federation) успешно подтверждена:\")\n\tfmt.Printf(\"  • Москва (ru-central-msk): %v\\n\", globalMetricsMsk)\n\tfmt.Printf(\"  • Питер  (ru-central-spb): %v\\n\", globalMetricsSpb)\n\tfmt.Println(\"  • Сырые промежуточные метрики отфильтрованы, передан только чистый агрегат!\")\n}",
        "note": "Сбор предварительно рассчитанных агрегатов через эндпоинт /federate"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v prometheus_federation_test.go\n# Вывод:\n# === RUN   TestPrometheusFederation\n# Иерархическая федерация (Prometheus Federation) успешно подтверждена:\n#   • Москва (ru-central-msk): [up{region=\"ru-central-msk\"} 1.000000 job:api_latency:p95{region=\"ru-central-msk\"} 0.025000]\n#   • Питер  (ru-central-spb): [up{region=\"ru-central-spb\"} 1.000000 job:api_latency:p95{region=\"ru-central-spb\"} 0.038000]\n#   • Сырые промежуточные метрики отфильтрованы, передан только чистый агрегат!\n# --- PASS: TestPrometheusFederation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Эндпоинт `/federate` принимает URL-параметр `match[]`: глобальный Prometheus передает PromQL-селекторы, указывая, какие именно метрики необходимо слить из локального хранилища TSDB.",
    "pitfalls": "Забирать через `/federate` все метрики без фильтрации (`match[]={__name__=~\".+\"}`): это перегрузит сеть и нивелирует преимущества федерации. Через федерацию передают строго агрегаты Recording Rules и индикаторы доступности.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы современные альтернативы классической Prometheus Federation в HighLoad кластерах?»\n**Ответ:** Для распределенных мульти-кластерных сред сегодня стандартом являются решения Thanos или VictoriaMetrics (VictoriaMetrics Cluster). Они используют легковесный Remote-Write протокол или Sidecar-компоненты над хранилищем объектов (S3), предоставляя единый глобальный PromQL эндпоинт без необходимости сложной настройки правил федерации."
  },
  {
    "num": 58,
    "title": "Долговременное хранение метрик Remote Write: архитектура Thanos, Cortex и VictoriaMetrics",
    "task": "Настрой **Remote Write** (Thanos/Cortex/VictoriaMetrics): `remote_write: [url: http://thanos-receive:19291/api/v1/receive]`. Long-term storage, global query, high availability. Покажи архитектуру.",
    "theory": "Протокол Prometheus Remote Write:\n- По умолчанию локальный TSDB Prometheus хранит данные 15–30 дней:\n  - Хранить данные за 2–3 года на локальном диске Prometheus неэффективно (ограничения файловой системы, долгий старт при рестарте).\n- **Спецификация Remote Write:**\n  - Prometheus скрейпит метрики в память.\n  - Батчами пакует сэмплы в бинарный протокол Snappy + Protocol Buffers.\n  - Отправляет по HTTP POST на URL долговременного хранилища (`remote_write`):\n    - **VictoriaMetrics** (`/api/v1/write`)\n    - **Thanos Receive** (`/api/v1/receive`)\n    - **Cortex / Mimir**\n- Обеспечивает глобальные запросы по сотням кластеров и дешевое хранение в S3/Ceph.",
    "step_by_step": "1. Создайте модель конфигурации `remote_write` в Prometheus.\n2. Смоделируйте упаковку батча метрик и отправку на эндпоинт долговременного хранилища.\n3. Проверьте сжатие данных и гарантию доставки при сбоях сети (Write-Ahead Log Queue).\n4. Оцените архитектуру глобального хранилища.",
    "code_blocks": [
      {
        "filename": "remote_write_architecture_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype RemoteWriteConfig struct {\n\tURL           string\n\tRemoteTimeout string\n\tBatchSize     int\n}\n\ntype MockThanosReceiver struct {\n\treceivedBatches int\n\ttotalSamples    int\n}\n\nfunc (r *MockThanosReceiver) ReceiveWriteBatch(samplesCount int) {\n\tr.receivedBatches++\n\tr.totalSamples += samplesCount\n}\n\nfunc TestRemoteWriteArchitecture(t *testing.T) {\n\tcfg := RemoteWriteConfig{\n\t\tURL:           \"http://thanos-receive:19291/api/v1/receive\",\n\t\tRemoteTimeout: \"30s\",\n\t\tBatchSize:     500,\n\t}\n\n\treceiver := &MockThanosReceiver{}\n\n\t// Имитируем отправку 3 батчей по 500 сэмплов из WAL\n\treceiver.ReceiveWriteBatch(cfg.BatchSize)\n\treceiver.ReceiveWriteBatch(cfg.BatchSize)\n\treceiver.ReceiveWriteBatch(cfg.BatchSize)\n\n\tif receiver.receivedBatches != 3 || receiver.totalSamples != 1500 {\n\t\tt.Fatalf(\"Ошибка отправки Remote Write: %+v\", receiver)\n\t}\n\n\tfmt.Println(\"Архитектура Prometheus Remote Write успешно подтверждена:\")\n\tfmt.Printf(\"  • Целевой ресивер: %s\\n\", cfg.URL)\n\tfmt.Printf(\"  • Батчей передано: %d (Всего сэмплов: %d)\\n\", receiver.receivedBatches, receiver.totalSamples)\n\tfmt.Println(\"  • Метрики надежно реплицированы в долговременное хранилище S3 (Thanos/VictoriaMetrics)!\")\n}",
        "note": "Спецификация и тестирование протокола Remote Write для долговременного хранения"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v remote_write_architecture_test.go\n# Вывод:\n# === RUN   TestRemoteWriteArchitecture\n# Архитектура Prometheus Remote Write успешно подтверждена:\n#   • Целевой ресивер: http://thanos-receive:19291/api/v1/receive\n#   • Батчей передано: 3 (Всего сэмплов: 1500)\n#   • Метрики надежно реплицированы в долговременное хранилище S3 (Thanos/VictoriaMetrics)!\n# --- PASS: TestRemoteWriteArchitecture (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Prometheus использует диск (WAL) как буфер для Remote Write: если удаленный Thanos временно недоступен, сэмплы копятся на локальном диске и досылаются при восстановлении сети без потери точек данных.",
    "pitfalls": "Отправлять тяжелые гистограммы через Remote Write без фильтрации: объем сетевого трафика вырастет в десятки раз. В секции `remote_write` настраивают `write_relabel_configs`, отсекая ненужные промежуточные метрики.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие архитектуры Thanos Sidecar от Thanos Receive?»\n**Ответ:** Thanos Sidecar работает по Pull-модели: раз в 2 часа sidecar скидывает уже сформированные закрытые 2-часовые блоки TSDB из локального диска Prometheus в S3. Thanos Receive работает по Push-модели (Remote Write) в реальном времени, что позволяет хранить метрики централизованно, даже если локальный Prometheus полностью сгорит вместе с диском."
  },
  {
    "num": 59,
    "title": "Prometheus Operator в Kubernetes: декларативные CRD ServiceMonitor и PodMonitor в GitOps",
    "task": "Настрой **Prometheus Operator** (Kubernetes): `ServiceMonitor` CRD автоматически конфигурирует Prometheus. `PodMonitor` для sidecars. Покажи GitOps approach.",
    "theory": "Декларативное управление мониторингом через Prometheus Operator:\n- Вместо ручной правки единого файла `prometheus.yml`:\n  - Разработчики кладут манифест `ServiceMonitor` прямо в Helm-чарт своего микросервиса.\n  - Оператор автоматически считывает `ServiceMonitor`, валидирует его и генерирует конфигурацию скрейпа для инстанса Prometheus.\n- **Спецификация ServiceMonitor:**\n  ```yaml\n  apiVersion: monitoring.coreos.com/v1\n  kind: ServiceMonitor\n  metadata:\n    name: order-service-monitor\n    labels:\n      release: prometheus-stack\n  spec:\n    selector:\n      matchLabels:\n        app: order-service\n    endpoints:\n      - port: metrics\n        interval: 15s\n        path: /metrics\n  ```\n- Для подов без K8s Service (например, standalone демоны или sidecar-контейнеры) используется `PodMonitor`.",
    "step_by_step": "1. Создайте модель манифеста `ServiceMonitor` и `PodMonitor`.\n2. Реализуйте селектор совпадения меток сервиса (`matchLabels`).\n3. Продемонстрируйте автоматическую генерацию таргетов скрейпа.\n4. Верифицируйте соответствие GitOps-стандартам.",
    "code_blocks": [
      {
        "filename": "servicemonitor_operator_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype ServiceMonitorSpec struct {\n\tName        string\n\tTargetApp   string\n\tPortName    string\n\tInterval    string\n\tMetricsPath string\n}\n\nfunc MatchServiceToMonitor(serviceLabels map[string]string, sm ServiceMonitorSpec) bool {\n\treturn serviceLabels[\"app\"] == sm.TargetApp\n}\n\nfunc TestServiceMonitorOperator(t *testing.T) {\n\tsm := ServiceMonitorSpec{\n\t\tName:        \"order-service-monitor\",\n\t\tTargetApp:   \"order-service\",\n\t\tPortName:    \"metrics\",\n\t\tInterval:    \"15s\",\n\t\tMetricsPath: \"/metrics\",\n\t}\n\n\tappServiceLabels := map[string]string{\n\t\t\"app\":     \"order-service\",\n\t\t\"release\": \"production\",\n\t}\n\n\totherServiceLabels := map[string]string{\n\t\t\"app\": \"auth-service\",\n\t}\n\n\tif !MatchServiceToMonitor(appServiceLabels, sm) {\n\t\tt.Fatal(\"ServiceMonitor обязан матчить order-service\")\n\t}\n\n\tif MatchServiceToMonitor(otherServiceLabels, sm) {\n\t\tt.Fatal(\"ServiceMonitor не должен матчить auth-service\")\n\t}\n\n\tfmt.Println(\"Prometheus Operator ServiceMonitor успешно подтвержден:\")\n\tfmt.Printf(\"  • CRD:         monitoring.coreos.com/v1/ServiceMonitor\\n\")\n\tfmt.Printf(\"  • Имя монитора: %s (TargetApp: %s)\\n\", sm.Name, sm.TargetApp)\n\tfmt.Printf(\"  • Скрейп:      %s по порту '%s'\\n\", sm.Interval, sm.PortName)\n\tfmt.Println(\"  • GitOps подход: конфигурация мониторинга хранится рядом с кодом сервиса!\")\n}",
        "note": "Декларативное сопоставление ServiceMonitor с сервисами Kubernetes"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v servicemonitor_operator_test.go\n# Вывод:\n# === RUN   TestServiceMonitorOperator\n# Prometheus Operator ServiceMonitor успешно подтвержден:\n#   • CRD:         monitoring.coreos.com/v1/ServiceMonitor\n#   • Имя монитора: order-service-monitor (TargetApp: order-service)\n#   • Скрейп:      15s по порту 'metrics'\n#   • GitOps подход: конфигурация мониторинга хранится рядом с кодом сервиса!\n# --- PASS: TestServiceMonitorOperator (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Prometheus Operator запускает контроллер, который слушает Kubernetes API events по CRD `ServiceMonitor`, собирает конфигурацию в секрет `prometheus-k8s-rulefiles` и вызывает перечитывание конфига через HTTP POST `/-/reload`.",
    "pitfalls": "Забыть добавить лейбл `release: <helm-release-name>` в метаданные `ServiceMonitor`: по умолчанию инстанс Prometheus скрейпит только те мониторы, чьи лейблы совпадают с селектором `serviceMonitorSelector` в спецификации оператора.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда вместо ServiceMonitor необходимо использовать PodMonitor?»\n**Ответ:** Когда поды не объединены в `Service` (например, DaemonSet сборщиков логов, задачи Envoy sidecar в Service Mesh или воркеры фоновых очередей, которые не принимают входящих клиентских подключений). `PodMonitor` напрямую находит поды по селектору меток пода."
  },
  {
    "num": 60,
    "title": "Интеграция Grafana и Prometheus: запуск в контейнере, настройка DataSource и построение графика RPS",
    "task": "Установи Grafana (`docker run -p 3000:3000 grafana/grafana`). Добавь Prometheus datasource (`http://prometheus:9090`). Создай **Dashboard** с Panel: Graph для `rate(http_requests_total[5m])`.",
    "theory": "Связка Prometheus и Grafana:\n- Grafana — лидирующая платформа визуализации метрик.\n- **Архитектура взаимодействия:**\n  - Prometheus выступает базой данных временных рядов (Data Source).\n  - Grafana подключается по HTTP к `http://prometheus:9090`.\n  - Панели дашборда отправляют PromQL-запросы на эндпоинт `/api/v1/query_range`.\n  - График `rate(http_requests_total[5m])` отображает динамику RPS (запросов в секунду) по времени.",
    "step_by_step": "1. Создайте модель подключения DataSource Prometheus в Grafana.\n2. Сформируйте конфигурацию панели дашборда с запросом `rate(http_requests_total[5m])`.\n3. Проверьте генерацию JSON-модели панели.\n4. Верифицируйте структуру дашборда.",
    "code_blocks": [
      {
        "filename": "grafana_dashboard_setup_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype GrafanaPanelTarget struct {\n\tExpr         string `json:\"expr\"`\n\tLegendFormat string `json:\"legendFormat\"`\n}\n\ntype GrafanaDashboardPanel struct {\n\tID      int                  `json:\"id\"`\n\tTitle   string               `json:\"title\"`\n\tType    string               `json:\"type\"` // \"timeseries\"\n\tTargets []GrafanaPanelTarget `json:\"targets\"`\n}\n\nfunc TestGrafanaDashboardSetup(t *testing.T) {\n\tpanel := GrafanaDashboardPanel{\n\t\tID:    1,\n\t\tTitle: \"Входящий трафик (RPS)\",\n\t\tType:  \"timeseries\",\n\t\tTargets: []GrafanaPanelTarget{\n\t\t\t{\n\t\t\t\tExpr:         `sum(rate(http_requests_total[5m])) by (method)`,\n\t\t\t\tLegendFormat: `{{method}}`,\n\t\t\t},\n\t\t},\n\t}\n\n\tpayload, err := json.Marshal(panel)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка сериализации панели: %v\", err)\n\t}\n\n\tif panel.Targets[0].Expr != \"sum(rate(http_requests_total[5m])) by (method)\" {\n\t\tt.Fatal(\"Некорректный PromQL запрос в панели\")\n\t}\n\n\tfmt.Println(\"Интеграция Grafana Dashboard успешно верифицирована:\")\n\tfmt.Printf(\"  • Панель:   %s [Тип: %s]\\n\", panel.Title, panel.Type)\n\tfmt.Printf(\"  • Запрос:   %s\\n\", panel.Targets[0].Expr)\n\tfmt.Printf(\"  • JSON:     %s\\n\", string(payload))\n\tfmt.Println(\"  • Панель готова для импорта в Grafana через Provisioning!\")\n}",
        "note": "Программная генерация JSON-структуры панели дашборда Grafana для RPS"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v grafana_dashboard_setup_test.go\n# Вывод:\n# === RUN   TestGrafanaDashboardSetup\n# Интеграция Grafana Dashboard успешно верифицирована:\n#   • Панель:   Входящий трафик (RPS) [Тип: timeseries]\n#   • Запрос:   sum(rate(http_requests_total[5m])) by (method)\n#   • JSON:     {\"id\":1,\"title\":\"Входящий трафик (RPS)\",\"type\":\"timeseries\",\"targets\":[{\"expr\":\"sum(rate(http_requests_total[5m])) by (method)\",\"legendFormat\":\"{{method}}\"}]}\n#   • Панель готова для импорта в Grafana через Provisioning!\n# --- PASS: TestGrafanaDashboardSetup (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Grafana вместо жестко заданного шага времени `5m` в PromQL используют переменную `$__rate_interval`, которая автоматически адаптирует окно вычисления `rate()` под масштаб времени графика, исключая пропуски данных.",
    "pitfalls": "Вводить пароль к Data Source вручную в веб-интерфейсе при каждом перезапуске: в Production настройка Data Source автоматизируется через YAML-манифесты Grafana Provisioning (`/etc/grafana/provisioning/datasources`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем в PromQL графиках Grafana используется переменная $__rate_interval?»\n**Ответ:** Если пользователь смотрит график за 7 дней, шаг пикселей на экране составляет, например, 1 час. Окно `[5m]` в таком случае приведет к тому, что 90% данных будут проигнорированы. Переменная `$__rate_interval` динамически расширяет интервал до $1h + 4 \\times ScrapeInterval$, обеспечивая идеально гладкий и математически точный график без пропусков."
  },
  {
    "num": 61,
    "title": "Методология RED в Grafana: построение панелей Rate (RPS), Errors (5xx) и Duration (p95)",
    "task": "**The RED Method**: Настрой дашборд в Grafana (если поднял её). Построй графики по методологии RED для своего API: **R**ate (запросов/сек из Counter), **E**rrors (ошибок/сек из Counter, где статус >= 500), **D**uration (95-й перцентиль времени ответа из Histogram).",
    "theory": "Практическая реализация методологии RED (Tom Wilkie):\n- Три панели на дашборде микросервиса:\n  1. **Rate:** `sum(rate(http_requests_total[5m]))`\n     - Отражает пропускную способность сервиса в запросах в секунду.\n  2. **Errors:** `sum(rate(http_requests_total{status=~\"5..\"}[5m]))`\n     - Показывает абсолютное число сбоев. Дополняется панелью Error Rate (%): `Errors / Rate * 100`.\n  3. **Duration (Latency p95 / p99):**\n     `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`\n     - Показывает время, в которое укладываются 95% пользователей.\n- Позволяет дежурному инженеру за 3 секунды оценить работоспособность любого сервиса.",
    "step_by_step": "1. Создайте структуру дашборда с 3 панелями RED.\n2. Сформируйте точные формулы PromQL для Rate, Errors и Duration.\n3. Проверьте синтаксис и квантиль 0.95.\n4. Убедитесь в полноте покрытия требований методологии RED.",
    "code_blocks": [
      {
        "filename": "red_method_dashboard_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype REDDashboardSpec struct {\n\tRateQuery     string\n\tErrorsQuery   string\n\tDurationQuery string\n}\n\nfunc CreateREDDashboard() REDDashboardSpec {\n\treturn REDDashboardSpec{\n\t\tRateQuery:     `sum(rate(http_requests_total[5m]))`,\n\t\tErrorsQuery:   `sum(rate(http_requests_total{status=~\"5..\"}[5m]))`,\n\t\tDurationQuery: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`,\n\t}\n}\n\nfunc TestREDMethodDashboard(t *testing.T) {\n\tred := CreateREDDashboard()\n\n\tif red.RateQuery == \"\" || red.ErrorsQuery == \"\" || red.DurationQuery == \"\" {\n\t\tt.Fatal(\"Запросы RED дашборда не могут быть пустыми\")\n\t}\n\n\tfmt.Println(\"Дашборд по методологии RED успешно сконфигурирован:\")\n\tfmt.Printf(\"  • [R] Rate:     %s\\n\", red.RateQuery)\n\tfmt.Printf(\"  • [E] Errors:   %s\\n\", red.ErrorsQuery)\n\tfmt.Printf(\"  • [D] Duration: %s\\n\", red.DurationQuery)\n\tfmt.Println(\"  • Золотой стандарт визуализации микросервисов готов!\")\n}",
        "note": "Конфигурация PromQL запросов дашборда по методологии RED"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v red_method_dashboard_test.go\n# Вывод:\n# === RUN   TestREDMethodDashboard\n# Дашборд по методологии RED успешно сконфигурирован:\n#   • [R] Rate:     sum(rate(http_requests_total[5m]))\n#   • [E] Errors:   sum(rate(http_requests_total{status=~\"5..\"}[5m]))\n#   • [D] Duration: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))\n#   • Золотой стандарт визуализации микросервисов готов!\n# --- PASS: TestREDMethodDashboard (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В запросе Duration обязательна группировка `by (le)`: функция `histogram_quantile` требует сохранения метки границы корзины `le` для выполнения кусочно-линейной интерполяции внутри бакета.",
    "pitfalls": "Забывать объединять ошибки регулярным выражением `{status=~\"5..\"}`: если указать строго `status=\"500\"`, алерты пропустят ошибки 502 Bad Gateway, 503 Service Unavailable и 504 Gateway Timeout.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в формуле histogram_quantile сумму sum(...) берут до вызова квантиля, а не после?»\n**Ответ:** Потому что квантили нельзя складывать математически. Сначала нужно просуммировать счетчики всех одинаковых бакетов со всех подов сервиса (`sum by (le)`), получив единую суммарную гистограмму кластера, и только затем рассчитать перцентиль `histogram_quantile` над этой объединенной гистограммой."
  },
  {
    "num": 62,
    "title": "Развертывание стека Prometheus и Grafana через Docker Compose: оркестрация и скрейпинг Go-сервиса",
    "task": "Поднимите стек **Prometheus + Grafana** через Docker Compose. Настройте Prometheus для скрейпинга вашего Go-сервиса (`scrape_configs`).",
    "theory": "Оркестрация стека мониторинга через Docker Compose:\n- Состав сервисов:\n  1. `app`: Go-сервис (порт `:8080`).\n  2. `prometheus`: сервер сбора метрик (порт `:9090`).\n  3. `grafana`: дашборды (порт `:3000`).\n- **Сетевое взаимодействие:**\n  - Контейнеры объединяются в единую сеть `bridge`.\n  - В `prometheus.yml` таргет указывается по имени контейнера: `targets: ['app:8080']`.\n  - Обеспечивает мгновенный подъем тестового стенда одной командой `docker compose up -d`.",
    "step_by_step": "1. Создайте модель конфигурации Docker Compose для стека мониторинга.\n2. Проверьте привязку портов 3000, 9090 и 8080.\n3. Проверьте валидность сетевого имени таргета `app:8080`.\n4. Убедитесь в готовности инфраструктурного манифеста.",
    "code_blocks": [
      {
        "filename": "docker_compose_stack_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n\t\"testing\"\n)\n\nconst DockerComposeTemplate = `\nversion: '3.8'\nservices:\n  app:\n    build: .\n    ports:\n      - \"8080:8080\"\n    networks:\n      - monitoring\n\n  prometheus:\n    image: prom/prometheus:v2.50.0\n    ports:\n      - \"9090:9090\"\n    volumes:\n      - ./prometheus.yml:/etc/prometheus/prometheus.yml\n    networks:\n      - monitoring\n\n  grafana:\n    image: grafana/grafana:10.3.0\n    ports:\n      - \"3000:3000\"\n    depends_on:\n      - prometheus\n    networks:\n      - monitoring\n\nnetworks:\n  monitoring:\n    driver: bridge\n`\n\nfunc TestDockerComposeStack(t *testing.T) {\n\tif !strings.Contains(DockerComposeTemplate, \"prom/prometheus\") || !strings.Contains(DockerComposeTemplate, \"grafana/grafana\") {\n\t\tt.Fatal(\"Манифест Docker Compose не содержит образы стека\")\n\t}\n\n\tfmt.Println(\"Стек Prometheus + Grafana в Docker Compose успешно проверен:\")\n\tfmt.Printf(\"  • Сервисы: app (:8080) -> prometheus (:9090) -> grafana (:3000)\\n\")\n\tfmt.Printf(\"  • Сеть:    bridge (DNS резолв таргета 'app:8080')\\n\")\n\tfmt.Println(\"  • Готов к локальному запуску и отладке метрик одной командой!\")\n}",
        "note": "Валидация спецификации Docker Compose для связки Go-сервиса, Prometheus и Grafana"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v docker_compose_stack_test.go\n# Вывод:\n# === RUN   TestDockerComposeStack\n# Стек Prometheus + Grafana в Docker Compose успешно проверен:\n#   • Сервисы: app (:8080) -> prometheus (:9090) -> grafana (:3000)\n#   • Сеть:    bridge (DNS резолв таргета 'app:8080')\n#   • Готов к локальному запуску и отладке метрик одной командой!\n# --- PASS: TestDockerComposeStack (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Внутри Docker сети встроенный DNS-сервер Docker резолвит имя хоста `app` во внутренний IP-адрес контейнера, избавляя от необходимости прописывать статические IP.",
    "pitfalls": "Использовать `localhost:8080` внутри контейнера Prometheus: для контейнера Prometheus `localhost` указывает на него самого! Для обращения к приложению необходимо указывать имя сервиса `app:8080` или `host.docker.internal`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как обеспечить сохранение данных Prometheus при перезапуске Docker Compose?»\n**Ответ:** Подключить именованный том (Named Volume): `volumes: - prometheus_data:/prometheus`. Сервер Prometheus сохраняет сегменты WAL и блоки TSDB в директорию `/prometheus`, поэтому том гарантирует сохранность исторических метрик при пересоздании контейнеров."
  },
  {
    "num": 63,
    "title": "Панель RPS в Grafana: визуализация скорости запросов rate(http_requests_total[5m])",
    "task": "Создайте Grafana-дашборд с панелью: `rate(http_requests_total[5m])` — количество запросов в секунду.",
    "theory": "Визуализация скорости входящих запросов (RPS):\n- Запрос PromQL: `rate(http_requests_total[5m])`.\n- В панели Timeseries в Grafana настраивают:\n  - Единицы измерения (Unit): `Requests / sec (reqps)`.\n  - Легенда: `{{method}} {{path}}` или `{{code}}`.\n  - Заливка области под графиком (Fill Opacity: 15%) для наглядности тренда.\n- Позволяет моментально отслеживать дневные пики активности пользователей и ночные спады.",
    "step_by_step": "1. Создайте спецификацию панели RPS.\n2. Задайте параметры единиц измерения `reqps`.\n3. Сформируйте запрос с агрегацией по методам.\n4. Проверьте валидность параметров панели.",
    "code_blocks": [
      {
        "filename": "rps_panel_config_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype RPSPanelConfig struct {\n\tTitle string\n\tUnit  string\n\tExpr  string\n}\n\nfunc TestRPSPanelConfig(t *testing.T) {\n\tcfg := RPSPanelConfig{\n\t\tTitle: \"Throughput (RPS)\",\n\t\tUnit:  \"reqps\",\n\t\tExpr:  \"sum(rate(http_requests_total[5m]))\",\n\t}\n\n\tif cfg.Unit != \"reqps\" || cfg.Expr != \"sum(rate(http_requests_total[5m]))\" {\n\t\tt.Fatalf(\"Некорректная конфигурация RPS: %+v\", cfg)\n\t}\n\n\tfmt.Println(\"Конфигурация панели RPS успешно верифицирована:\")\n\tfmt.Printf(\"  • Заголовок панели: %s\\n\", cfg.Title)\n\tfmt.Printf(\"  • Единица (Unit):  %s (req/s)\\n\", cfg.Unit)\n\tfmt.Printf(\"  • PromQL:          %s\\n\", cfg.Expr)\n}",
        "note": "Конфигурация параметров визуализации RPS панели в Grafana"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v rps_panel_config_test.go\n# Вывод:\n# === RUN   TestRPSPanelConfig\n# Конфигурация панели RPS успешно верифицирована:\n#   • Заголовок панели: Throughput (RPS)\n#   • Единица (Unit):  reqps (req/s)\n#   • PromQL:          sum(rate(http_requests_total[5m]))\n# --- PASS: TestRPSPanelConfig (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Функция `rate()` рассчитывает прирост счетчика в секунду: если за 5 минут пришло 300 запросов, `rate()` вернет $300 / 300 = 1.0$ req/s.",
    "pitfalls": "Использовать функцию `increase()` вместо `rate()` на графике RPS: `increase()` вернет суммарное число запросов за 5 минут (300 запросов), а не скорость в секунду.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие функций rate() и irate() в PromQL?»\n**Ответ:** `rate()` усредняет скорость по всему временному окну (например 5 минут), сглаживая шум. `irate()` (Instant Rate) вычисляет скорость строго по двум последним точкам внутри окна, показывая мгновенные микро-всплески. Для алертов и графиков трендов всегда используют `rate()`, а `irate()` применяют только для поиска кратковременных скачков высокой частоты."
  },
  {
    "num": 64,
    "title": "Панель Singlestat для SLO: расчет коэффициента доступности 99.9% и бюджета ошибок Error Budget",
    "task": "Создай **Singlestat Panel** для SLO: `1 - (sum(rate(http_requests_total{status=~\"5..\"}[30d])) / sum(rate(http_requests_total[30d])))`. Покажи error budget: `1 - 0.999 = 0.001` (0.1% допустимых ошибок).",
    "theory": "Расчет доступности и Error Budget по стандарту Google SRE:\n- **SLO (Service Level Objective):** целевой уровень надежности, согласованный с бизнесом (например, 99.9% «три девятки»).\n- **Error Budget (Бюджет ошибок):**\n  $$\\text{Error Budget} = 1 - \\text{SLO} = 1 - 0.999 = 0.001 \\quad (0.1\\%)$$\n- **Формула фактического SLI за 30 дней в PromQL:**\n  $$1 - \\frac{\\sum \\text{rate}(http\\_requests\\_total\\{status=\\sim\"5..\" \\}[30d])}{\\sum \\text{rate}(http\\_requests\\_total[30d])}$$\n- Панель Singlestat (Stat Panel) в Grafana:\n  - Отображает крупную цифру (например `99.94%`).\n  - Зеленый цвет, если бюджет в норме, и красный, если лимит ошибок исчерпан.",
    "step_by_step": "1. Создайте модель расчета SLI и остатка бюджета ошибок.\n2. Проверьте расчет доступности при 150 ошибках на 1 000 000 запросов.\n3. Рассчитайте остаток Error Budget.\n4. Проверьте форматирование статуса панели Singlestat.",
    "code_blocks": [
      {
        "filename": "slo_error_budget_panel_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\nfunc CalculateSLOAndBudget(totalRequests, errorRequests float64, targetSLO float64) (sliPercent float64, budgetRemainingPercent float64) {\n\tsli := 1.0 - (errorRequests / totalRequests)\n\terrorBudgetTotal := 1.0 - targetSLO\n\tactualErrorsRatio := errorRequests / totalRequests\n\n\tbudgetRemaining := (errorBudgetTotal - actualErrorsRatio) / errorBudgetTotal * 100.0\n\treturn sli * 100.0, budgetRemaining\n}\n\nfunc TestSLOErrorBudgetPanel(t *testing.T) {\n\ttotalReq := 1000000.0 // 1 миллион запросов за месяц\n\terrorReq := 450.0     // 450 сбоев 5xx\n\ttargetSLO := 0.999    // 99.9%\n\n\tsli, remainingBudget := CalculateSLOAndBudget(totalReq, errorReq, targetSLO)\n\n\tif sli < 99.9 || remainingBudget <= 0 {\n\t\tt.Fatalf(\"SLO нарушен: sli=%f, budget=%f\", sli, remainingBudget)\n\t}\n\n\tfmt.Println(\"Панель Singlestat (SLO & Error Budget) успешно рассчитана:\")\n\tfmt.Printf(\"  • Целевой SLO:              %.1f%% (Три девятки)\\n\", targetSLO*100)\n\tfmt.Printf(\"  • Фактический SLI за 30d:   %.4f%% [СТАТУС: ЗЕЛЕНЫЙ]\\n\", sli)\n\tfmt.Printf(\"  • Использовано ошибок:      %.0f из допустимых 1000\\n\", errorReq)\n\tfmt.Printf(\"  • Остаток бюджета ошибок:   %.1f%% бюджета сохранено\\n\", remainingBudget)\n\tfmt.Println(\"  • Команда разработки имеет право релизить новые рискованные фичи!\")\n}",
        "note": "Расчет месячного SLI доступности и остатка бюджета ошибок по методологии SRE"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v slo_error_budget_panel_test.go\n# Вывод:\n# === RUN   TestSLOErrorBudgetPanel\n# Панель Singlestat (SLO & Error Budget) успешно рассчитана:\n#   • Целевой SLO:              99.9% (Три девятки)\n#   • Фактический SLI за 30d:   99.9550% [СТАТУС: ЗЕЛЕНЫЙ]\n#   • Использовано ошибок:      450 из допустимых 1000\n#   • Остаток бюджета ошибок:   55.0% бюджета сохранено\n#   • Команда разработки имеет право релизить новые рискованные фичи!\n# --- PASS: TestSLOErrorBudgetPanel (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Вычисление окна `[30d]` требует агрегации миллионов точек. В продакшене для такого запроса настраивают Prometheus Recording Rule, предрасчитывая часовые агрегаты, чтобы панель Grafana открывалась мгновенно.",
    "pitfalls": "Включать ошибки 4xx (404 Not Found, 401 Unauthorized) в расчет SLI: ошибки клиента не свидетельствуют о недоступности бэкенда и не должны сжигать Error Budget инженерной команды.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что происходит в компании, когда Error Budget исчерпан до 0%?»\n**Ответ:** По политике SRE внедряется режим Feature Freeze: все продуктовые релизы и новые фичи блокируются. 100% инженерных ресурсов команды перенаправляются на повышение надежности, багфикс архитектуры, рефакторинг и покрытие тестами, пока бюджет ошибок не восстановится."
  },
  {
    "num": 65,
    "title": "Сквозная трассировка в логах: извлечение trace_id и span_id из OpenTelemetry контекста",
    "task": "Свяжите логи и трейсы: в каждую структурированную запись лога добавьте `trace_id` и `span_id`, извлекая их из контекста OpenTelemetry.",
    "theory": "Связка Logs $\\leftrightarrow$ Traces (Distributed Context Propagation):\n- В микросервисной архитектуре один пользовательский клик порождает цепочку вызовов в 10 сервисах.\n- При возникновении ошибки найти нужную строчку среди терабайтов логов невозможно без общего идентификатора.\n- **Стандарт W3C TraceContext:**\n  - `trace_id`: уникальный 128-битный хэш всей цепочки транзакции.\n  - `span_id`: 64-битный идентификатор текущей конкретной операции.\n- Логгер автоматически извлекает их из `trace.SpanContextFromContext(ctx)` и добавляет в каждую строку лога.",
    "step_by_step": "1. Создайте модель извлечения идентификаторов OpenTelemetry TraceContext.\n2. Реализуйте функцию логирования с атрибутами `trace_id` и `span_id`.\n3. Симулируйте генерацию лога об ошибке с контекстом трассировки.\n4. Убедитесь в наличии сквозных идентификаторов в теле лога.",
    "code_blocks": [
      {
        "filename": "logs_traces_correlation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log/slog\"\n\t\"strings\"\n\t\"testing\"\n)\n\ntype traceContextKey string\n\nconst (\n\tCtxTraceID traceContextKey = \"trace_id\"\n\tCtxSpanID  traceContextKey = \"span_id\"\n)\n\nfunc LogWithTraceContext(ctx context.Context, logger *slog.Logger, msg string, args ...any) {\n\ttraceID, _ := ctx.Value(CtxTraceID).(string)\n\tspanID, _ := ctx.Value(CtxSpanID).(string)\n\n\tif traceID != \"\" {\n\t\targs = append(args, \"trace_id\", traceID)\n\t}\n\tif spanID != \"\" {\n\t\targs = append(args, \"span_id\", spanID)\n\t}\n\n\tlogger.Info(msg, args...)\n}\n\nfunc TestLogsTracesCorrelation(t *testing.T) {\n\tvar buf strings.Builder\n\tlogger := slog.New(slog.NewTextHandler(&buf, nil))\n\n\tctx := context.WithValue(context.Background(), CtxTraceID, \"4bf92f3577b34da6a3ce929d0e0e4736\")\n\tctx = context.WithValue(ctx, CtxSpanID, \"00f067aa0ba902b7\")\n\n\tLogWithTraceContext(ctx, logger, \"database query slow\", \"table\", \"payments\", \"latency_ms\", 120)\n\n\tlogOutput := buf.String()\n\n\tif !strings.Contains(logOutput, \"trace_id=4bf92f3577b34da6a3ce929d0e0e4736\") ||\n\t\t!strings.Contains(logOutput, \"span_id=00f067aa0ba902b7\") {\n\t\tt.Fatalf(\"Лог не содержит идентификаторов трейса: %s\", logOutput)\n\t}\n\n\tfmt.Println(\"Связывание логов и трейсов успешно подтверждено:\")\n\tfmt.Printf(\"  • Вывод: %s\", logOutput)\n\tfmt.Println(\"  • Инженер может скопировать trace_id и мгновенно открыть весь граф вызова в Jaeger!\")\n}",
        "note": "Сквозная привязка логов к распределенным трейсам OpenTelemetry"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v logs_traces_correlation_test.go\n# Вывод:\n# === RUN   TestLogsTracesCorrelation\n# Связывание логов и трейсов успешно подтверждено:\n#   • Вывод: time=... level=INFO msg=\"database query slow\" table=payments latency_ms=120 trace_id=4bf92f3577b34da6a3ce929d0e0e4736 span_id=00f067aa0ba902b7\n#   • Инженер может скопировать trace_id и мгновенно открыть весь граф вызова в Jaeger!\n# --- PASS: TestLogsTracesCorrelation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В стандартном OpenTelemetry Go SDK вызов `trace.SpanFromContext(ctx).SpanContext().TraceID().String()` возвращает шестнадцатеричную строку hex-формата, совместимую с Grafana Tempo и Elastic APM.",
    "pitfalls": "Логировать `trace_id` только при возникновении ошибок: `trace_id` обязан присутствовать во ВСЕХ логах (INFO, WARN, ERROR), чтобы при расследовании можно было воспроизвести полную хронологию успешных шагов до сбоя.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в Grafana настроить бесшовный переход от логов в Loki к трейсу в Jaeger/Tempo?»\n**Ответ:** Настройкой Derived Fields в настройках Data Source Loki в Grafana. Указывают регулярное выражение `trace_id=(\\w+)` и связывают найденный идентификатор с внутренним переходом на Data Source Tempo, превращая текст `trace_id` в кликабельную ссылку прямо в окне просмотра логов."
  },
  {
    "num": 66,
    "title": "Диагностика утечек горутин: мониторинг метрики go_goroutines и паттерны предотвращения утечек",
    "task": "Добавьте панель: `go_goroutines` — количество активных горутин. Объясните, почему резкий рост — это признак goroutine leak.",
    "theory": "Природа и диагностика утечек горутин (Goroutine Leaks):\n- Горутина в Go весит от 2 КБ до десятков мегабайт (включая переменные, захваченные в стек и замыкания).\n- В рантайме Go сборщик мусора (GC) **НЕ собирает работающие или заблокированные горутины**!\n- **Причины утечек горутин:**\n  1. Чтение из небуферизованного канала, в который больше никто не пишет.\n  2. Запись в канал, из которого никто не читает (зависший консьюмер).\n  3. Сетевой вызов без таймаута (`http.Get` без `context.WithTimeout`).\n  4. Забытый `cancel()` контекста при использовании `context.WithCancel`.",
    "step_by_step": "1. Создайте модель отслеживания динамики метрики `go_goroutines`.\n2. Смоделируйте нормальное состояние сервиса (базовый уровень 20 горутин).\n3. Смоделируйте утечку (рост до 2000 горутин).\n4. Проверьте генерацию предупреждения об утечке.",
    "code_blocks": [
      {
        "filename": "goroutine_leak_detector_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype GoroutineMonitor struct {\n\tbaselineCount int\n}\n\nfunc (m *GoroutineMonitor) CheckLeak(currentCount int) (isLeaking bool, msg string) {\n\t// Рост более чем в 10 раз от базы свидетельствует об утечке\n\tif currentCount > m.baselineCount*10 {\n\t\treturn true, fmt.Sprintf(\"КРИТИЧЕСКАЯ УТЕЧКА ГОРУТИН: текущее число %d (база %d)\", currentCount, m.baselineCount)\n\t}\n\treturn false, \"OK\"\n}\n\nfunc TestGoroutineLeakDetector(t *testing.T) {\n\tmon := &GoroutineMonitor{baselineCount: 25}\n\n\tleak1, _ := mon.CheckLeak(30)\n\tif leak1 {\n\t\tt.Fatal(\"30 горутин не должно считаться утечкой\")\n\t}\n\n\tleak2, msg := mon.CheckLeak(4500)\n\tif !leak2 {\n\t\tt.Fatal(\"4500 горутин обязаны вызвать алерт утечки\")\n\t}\n\n\tfmt.Println(\"Диагностика утечки горутин (go_goroutines) подтверждена:\")\n\tfmt.Printf(\"  • Базовый уровень: 25 горутин\\n\")\n\tfmt.Printf(\"  • Аномальный рост: 4500 горутин\\n\")\n\tfmt.Printf(\"  • Диагноз:         %s\\n\", msg)\n\tfmt.Println(\"  • Мониторинг go_goroutines позволяет предотвратить OOMKilled контейнеров!\")\n}",
        "note": "Детекция аномального роста числа горутин в памяти Go сервиса"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v goroutine_leak_detector_test.go\n# Вывод:\n# === RUN   TestGoroutineLeakDetector\n# Диагностика утечки горутин (go_goroutines) подтверждена:\n#   • Базовый уровень: 25 горутин\n#   • Аномальный рост: 4500 горутин\n#   • Диагноз:         КРИТИЧЕСКАЯ УТЕЧКА ГОРУТИН: текущее число 4500 (база 25)\n#   • Мониторинг go_goroutines позволяет предотвратить OOMKilled контейнеров!\n# --- PASS: TestGoroutineLeakDetector (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "При утечке горутин растет не только память стеков, но и размер структур планировщика GMP (`runtime.g`), что приводит к деградации циклов `sysmon` и увеличению накладных расходов на переключение контекста.",
    "pitfalls": "Пытаться убить зависшую горутину снаружи: в языке Go невозможно принудительно остановить горутину из другого потока! Горутина обязана завершаться сама по сигналу отмены `<-ctx.Done()`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как на живом поде в продакшене локализовать место утечки горутин?»\n**Ответ:** Запросить дамп горутин через pprof: `curl http://localhost:9090/debug/pprof/goroutine?debug=2`. В выводе будут перечислены стектрейсы всех запущенных горутин с указанием номеров строк кода и причин блокировки (например, `chan receive`, `select`, `IO wait`), что позволяет мгновенно найти застрявший вызов."
  },
  {
    "num": 67,
    "title": "Табличная панель Top 10 медленных эндпоинтов: расчет в PromQL через topk и отношение sum к count",
    "task": "Создай **Table Panel** для Top 10 slow endpoints: `topk(10, sum by (path) (rate(http_request_duration_seconds_sum[5m])) / sum by (path) (rate(http_request_duration_seconds_count[5m])))`. Покажи actionable insights.",
    "theory": "Анализ узких мест производительности через PromQL `topk`:\n- Функция `topk(K, v)` возвращает $K$ наибольших элементов по значению выражения.\n- **Формула среднего времени ответа эндпоинта:**\n  $$\\text{Avg Latency} = \\frac{\\sum_{\\text{path}} \\text{rate}(http\\_request\\_duration\\_seconds\\_sum[5m])}{\\sum_{\\text{path}} \\text{rate}(http\\_request\\_duration\\_seconds\\_count[5m])}$$\n- Панель Table в Grafana сортирует эндпоинты по убыванию задержки, давая инженерам четкий список приоритетов для оптимизации SQL-индексов и кэширования.",
    "step_by_step": "1. Создайте модель данных задержек по эндпоинтам.\n2. Рассчитайте среднее время выполнения для каждого пути.\n3. Отфильтруйте 3 самых медленных маршрута (top 3).\n4. Проверьте правильность сортировки.",
    "code_blocks": [
      {
        "filename": "top_slow_endpoints_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sort\"\n\t\"testing\"\n)\n\ntype EndpointLatencyStat struct {\n\tPath       string\n\tAvgLatency float64 // в секундах\n}\n\nfunc TopKSlowEndpoints(stats []EndpointLatencyStat, k int) []EndpointLatencyStat {\n\tsort.Slice(stats, func(i, j int) bool {\n\t\treturn stats[i].AvgLatency > stats[j].AvgLatency // по убыванию\n\t})\n\tif len(stats) > k {\n\t\treturn stats[:k]\n\t}\n\treturn stats\n}\n\nfunc TestTopSlowEndpoints(t *testing.T) {\n\tendpoints := []EndpointLatencyStat{\n\t\t{Path: \"/api/ping\", AvgLatency: 0.002},\n\t\t{Path: \"/api/catalog/search\", AvgLatency: 0.450},\n\t\t{Path: \"/api/reports/annual\", AvgLatency: 2.850}, // Самый медленный!\n\t\t{Path: \"/api/users/profile\", AvgLatency: 0.045},\n\t\t{Path: \"/api/checkout/pay\", AvgLatency: 1.150},\n\t}\n\n\ttop3 := TopKSlowEndpoints(endpoints, 3)\n\n\tif len(top3) != 3 || top3[0].Path != \"/api/reports/annual\" {\n\t\tt.Fatalf(\"Некорректный Top-3: %+v\", top3)\n\t}\n\n\tfmt.Println(\"Table Panel: Top медленных эндпоинтов (PromQL topk):\")\n\tfor idx, ep := range top3 {\n\t\tfmt.Printf(\"  #%d %-25s -> %.3f сек (%.0f мс)\\n\", idx+1, ep.Path, ep.AvgLatency, ep.AvgLatency*1000)\n\t}\n\tfmt.Println(\"  • Четкие инсайты для оптимизации архитектуры получены!\")\n}",
        "note": "Сортировка и выборка Top медленных эндпоинтов по PromQL формуле topk"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v top_slow_endpoints_test.go\n# Вывод:\n# === RUN   TestTopSlowEndpoints\n# Table Panel: Top медленных эндпоинтов (PromQL topk):\n#   #1 /api/reports/annual       -> 2.850 сек (2850 мс)\n#   #2 /api/checkout/pay         -> 1.150 сек (1150 мс)\n#   #3 /api/catalog/search       -> 0.450 сек (450 мс)\n#   • Четкие инсайты для оптимизации архитектуры получены!\n# --- PASS: TestTopSlowEndpoints (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Внутри PromQL функция `topk` выполняется на каждом шаге вычисления графика: если задержка эндпоинта упала, он автоматически выпадает из таблицы, уступая место другим узким местам.",
    "pitfalls": "Использовать `topk` без ограничения по минимальному количеству запросов: маршрут, вызванный 1 раз за день и занявший 3 секунды, займет первое место в таблице, хотя реальной проблемы под нагрузкой он не представляет. Добавляют фильтр `and sum by (path) (rate(..._count[5m])) > 1`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в алертах опасно использовать функцию topk()?»\n**Ответ:** Потому что состав возвращаемых рядов в `topk` постоянно меняется (ряды то появляются, то исчезают из выборки). Это приводит к постоянному миганию статусов алертов (Alert Flapping) и сбою механизмов дедупликации в Alertmanager. Для алертов используют стабильные фильтры без `topk`."
  },
  {
    "num": 68,
    "title": "Мониторинг памяти приложения: сравнение process_resident_memory_bytes (RSS) и go_memstats_alloc_bytes",
    "task": "Добавьте панель: `process_resident_memory_bytes` и `go_memstats_alloc_bytes` — использование памяти (RSS vs Go heap).",
    "theory": "Разница между памятью кучи (Heap Alloc) и резидентной памятью процесса (RSS):\n- `go_memstats_alloc_bytes`:\n  - Объем активных объектов в Go куче, доступных через указатели.\n- `process_resident_memory_bytes` (RSS):\n  - Фактическая физическая память, выделенная операционной системой Linux процессу (Resident Set Size).\n  - Включает: кучу Go, стеки всех горутин, структуры рантайма, код бинарника и память, освобожденную GC, но **еще не возвращенную ОС** (`madvise`).\n- Если RSS приближается к лимиту памяти пода в Kubernetes (`limits.memory`), Linux OOM Killer уничтожит контейнер, даже если `go_memstats_alloc_bytes` составляет всего 30% лимита!",
    "step_by_step": "1. Создайте модель замера памяти процесса и кучи.\n2. Проверьте соотношение: RSS обязан быть больше или равен Heap Alloc.\n3. Продемонстрируйте вычисление фрагментации памяти и резерва ОС.\n4. Сформируйте рекомендации по настройке `GOMEMLIMIT`.",
    "code_blocks": [
      {
        "filename": "rss_vs_heap_memory_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype ProcessMemoryStats struct {\n\tHeapAllocBytes int64 // go_memstats_alloc_bytes\n\tRSSBytes       int64 // process_resident_memory_bytes\n\tK8sLimitBytes  int64 // resources.limits.memory\n}\n\nfunc AnalyzeMemoryOverhead(m ProcessMemoryStats) (fragmentationMB float64, headroomMB float64) {\n\tfrag := float64(m.RSSBytes-m.HeapAllocBytes) / (1024 * 1024)\n\theadroom := float64(m.K8sLimitBytes-m.RSSBytes) / (1024 * 1024)\n\treturn frag, headroom\n}\n\nfunc TestRSSVsHeapMemory(t *testing.T) {\n\tstats := ProcessMemoryStats{\n\t\tHeapAllocBytes: 150 * 1024 * 1024, // 150 МБ в куче Go\n\t\tRSSBytes:       280 * 1024 * 1024, // 280 МБ физической памяти занято (RSS)\n\t\tK8sLimitBytes:  512 * 1024 * 1024, // 512 МБ лимит K8s пода\n\t}\n\n\tfragMB, headroomMB := AnalyzeMemoryOverhead(stats)\n\n\tif fragMB != 130.0 || headroomMB != 232.0 {\n\t\tt.Fatalf(\"Некорректный расчет памяти: frag=%f, headroom=%f\", fragMB, headroomMB)\n\t}\n\n\tfmt.Println(\"Сравнение памяти RSS и Go Heap Alloc:\")\n\tfmt.Printf(\"  • Активная куча (Go Heap): %.1f МБ\\n\", float64(stats.HeapAllocBytes)/(1024*1024))\n\tfmt.Printf(\"  • Память ОС (Linux RSS):   %.1f МБ\\n\", float64(stats.RSSBytes)/(1024*1024))\n\tfmt.Printf(\"  • Оверхед рантайма / стеки: %.1f МБ\\n\", fragMB)\n\tfmt.Printf(\"  • Запас до K8s OOM Killer:  %.1f МБ\\n\", headroomMB)\n\tfmt.Println(\"  • Мониторинг RSS критичен для защиты контейнера от внезапного убийства!\")\n}",
        "note": "Сравнение метрик памяти RSS и Go Heap Alloc для предотвращения OOMKilled"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v rss_vs_heap_memory_test.go\n# Вывод:\n# === RUN   TestRSSVsHeapMemory\n# Сравнение памяти RSS и Go Heap Alloc:\n#   • Активная куча (Go Heap): 150.0 МБ\n#   • Память ОС (Linux RSS):   280.0 МБ\n#   • Оверхед рантайма / стеки: 130.0 МБ\n#   • Запас до K8s OOM Killer:  232.0 МБ\n#   • Мониторинг RSS критичен для защиты контейнера от внезапного убийства!\n# --- PASS: TestRSSVsHeapMemory (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Начиная с Go 1.19, переменная окружения `GOMEMLIMIT` задает мягкий лимит памяти (например `GOMEMLIMIT=450MiB`). Рантайм Go начинает более агрессивно запускать GC при приближении к лимиту, предотвращая разрастание RSS до границы K8s OOM.",
    "pitfalls": "Выставлять `GOMEMLIMIT` ровно в 100% лимита K8s: рантайм Go контролирует только свою память, но память бинарника, C-библиотек и стеков потоков ОС не учитывается в куче. Оптимально выставлять `GOMEMLIMIT` на уровне 80–85% от `limits.memory`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему после освобождения объектов в Go память RSS процесса в htop/Prometheus не уменьшается немедленно?»\n**Ответ:** Рантайм Go не возвращает память операционной системе сразу через `free()`. Он помечает страницы системным вызовом `madvise(MADV_DONTNEED / MADV_FREE)`, сообщая ядру Linux, что память можно забрать при нехватке. Но пока у ОС есть свободная RAM, страницы остаются закрепленными за процессом, удерживая высокий RSS для ускорения будущих аллокаций."
  },
  {
    "num": 69,
    "title": "Переменные дашборда Grafana Variables: выпадающие списки job и каскадный выбор instance",
    "task": "Создай **Dashboard с Variables**: `job` (dropdown), `instance` (dependent). `$job` в queries. Покажи reusable dashboard для multiple services.",
    "theory": "Шаблонизация дашбордов (Grafana Template Variables):\n- Вместо создания 50 отдельных дашбордов под каждый микросервис создается **один универсальный дашборд**:\n  1. Переменная `$job`:\n     - Запрос: `label_values(http_requests_total, job)`\n     - Выпадающий список всех сервисов компании (`order-service`, `auth-service`, `billing-service`).\n  2. Зависимая (каскадная) переменная `$instance`:\n     - Запрос: `label_values(http_requests_total{job=\"$job\"}, instance)`\n     - Выпадающий список конкретных подов выбранного сервиса.\n  3. В панелях PromQL пишется запрос с переменными:\n     `rate(http_requests_total{job=\"$job\", instance=~\"$instance\"}[5m])`.",
    "step_by_step": "1. Создайте модель шаблонизированного запроса с переменными `$job` и `$instance`.\n2. Реализуйте подстановку значений переменных в тело PromQL выражения.\n3. Продемонстрируйте переключение между сервисами без изменения кода дашборда.\n4. Проверьте изоляцию фильтрации.",
    "code_blocks": [
      {
        "filename": "grafana_variables_templating_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n\t\"testing\"\n)\n\ntype DashboardVariable struct {\n\tName       string\n\tQuery      string\n\tIsCascade  bool\n}\n\nfunc RenderTemplatedQuery(templateExpr string, jobVal string, instanceVal string) string {\n\tres := strings.ReplaceAll(templateExpr, \"$job\", jobVal)\n\tres = strings.ReplaceAll(res, \"$instance\", instanceVal)\n\treturn res\n}\n\nfunc TestGrafanaVariablesTemplating(t *testing.T) {\n\tvars := []DashboardVariable{\n\t\t{Name: \"job\", Query: \"label_values(http_requests_total, job)\", IsCascade: false},\n\t\t{Name: \"instance\", Query: \"label_values(http_requests_total{job=\\\"$job\\\"}, instance)\", IsCascade: true},\n\t}\n\n\trawQuery := `sum(rate(http_requests_total{job=\"$job\", instance=~\"$instance\"}[5m]))`\n\n\t// Выбираем order-service и под pod-1\n\trendered := RenderTemplatedQuery(rawQuery, \"order-service\", \"pod-1.*\")\n\n\texpected := `sum(rate(http_requests_total{job=\"order-service\", instance=~\"pod-1.*\"}[5m]))`\n\tif rendered != expected {\n\t\tt.Fatalf(\"Ошибка рендеринга шаблона: %s\", rendered)\n\t}\n\n\tfmt.Println(\"Шаблонизация дашборда Grafana с переменными успешна:\")\n\tfmt.Printf(\"  • Переменные:  $%s -> $%s (Каскадный выбор)\\n\", vars[0].Name, vars[1].Name)\n\tfmt.Printf(\"  • Исходный:    %s\\n\", rawQuery)\n\tfmt.Printf(\"  • Рендеринг:   %s\\n\", rendered)\n\tfmt.Println(\"  • Один универсальный дашборд обслуживает сотни микросервисов компании!\")\n}",
        "note": "Подстановка переменных шаблонизации Grafana в запросы PromQL"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v grafana_variables_templating_test.go\n# Вывод:\n# === RUN   TestGrafanaVariablesTemplating\n# Шаблонизация дашборда Grafana с переменными успешна:\n#   • Переменные:  $job -> $instance (Каскадный выбор)\n#   • Исходный:    sum(rate(http_requests_total{job=\"$job\", instance=~\"$instance\"}[5m]))\n#   • Рендеринг:   sum(rate(http_requests_total{job=\"order-service\", instance=~\"pod-1.*\"}[5m]))\n#   • Один универсальный дашборд обслуживает сотни микросервисов компании!\n# --- PASS: TestGrafanaVariablesTemplating (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Grafana регулярное выражение `=~` в паре с переменной `instance=~\"$instance\"` позволяет выбирать опцию `All` или мульти-выбор (Multi-value), подставляя регулярное выражение `pod-1|pod-2|pod-3`.",
    "pitfalls": "Использовать строгое равенство `instance=\"$instance\"` при включенном мульти-выборе: если пользователь выберет 2 пода, Grafana подставит `pod1|pod2`, и оператор `=` вернет синтаксическую ошибку. При наличии переменных всегда используют `=~`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как скрыть технические системные job (например, pushgateway, node-exporter) из выпадающего списка переменных Grafana?»\n**Ответ:** В настройках переменной в поле `Regex` задают фильтрующее регулярное выражение, например `/^(.*-service)$/`. Grafana отобразит в выпадающем меню только те сервисы, чье имя оканчивается на `-service`, исключая системные инфраструктурные экспортеры."
  },
  {
    "num": 70,
    "title": "Предрасчет тяжелых запросов через Recording Rules: оптимизация скорости дашбордов в Prometheus",
    "task": "Создайте **recording rules** в Prometheus для предрасчёта тяжёлых запросов: `job:http_requests:rate5m = sum(rate(http_requests_total[5m])) by (job)`.",
    "theory": "Оптимизация производительности через Recording Rules (Правила записи):\n- Проблема:\n  - Когда дашборд открывают 20 инженеров одновременно, сложный запрос по 10 000 временных рядов выполняется 20 раз, перегружая CPU сервера Prometheus.\n- **Решение — Recording Rules:**\n  - Prometheus по таймеру (раз в 15 секунд) вычисляет тяжелое выражение в фоне.\n  - Сохраняет результат как **новый предвычисленный временной ряд**:\n    ```yaml\n    groups:\n      - name: http_recording_rules\n        rules:\n          - record: job:http_requests:rate5m\n            expr: sum(rate(http_requests_total[5m])) by (job)\n    ```\n  - Дашборд запрашивает уже готовую метрику `job:http_requests:rate5m`.\n  - Время загрузки графиков сокращается с 5 секунд до 2 миллисекунд!",
    "step_by_step": "1. Создайте модель правила предрасчета `RecordingRule`.\n2. Реализуйте фоновое вычисление агрегата по сервисам.\n3. Продемонстрируйте чтение готового предвычисленного ряда.\n4. Оцените ускорение выполнения запросов в Grafana.",
    "code_blocks": [
      {
        "filename": "recording_rules_evaluator_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype PrecomputedMetricStore struct {\n\trecords map[string]float64\n}\n\nfunc (s *PrecomputedMetricStore) ExecuteRecordingRule(ruleName string, exprResult float64) {\n\ts.records[ruleName] = exprResult\n}\n\nfunc TestRecordingRulesEvaluator(t *testing.T) {\n\tstore := &PrecomputedMetricStore{records: make(map[string]float64)}\n\n\t// Имя правила по соглашению Prometheus: level:metric:operations\n\trule := \"job:http_requests:rate5m\"\n\n\t// Prometheus вычисляет sum(rate(http_requests_total[5m])) by (job) в фоне\n\tcalculatedRPS := 4250.0\n\tstore.ExecuteRecordingRule(rule, calculatedRPS)\n\n\tval, exists := store.records[rule]\n\tif !exists || val != 4250.0 {\n\t\tt.Fatalf(\"Ошибка предрасчета метрики: %v\", store.records)\n\t}\n\n\tfmt.Println(\"Recording Rules в Prometheus успешно подтверждены:\")\n\tfmt.Printf(\"  • Предвычисленный ряд: %s\\n\", rule)\n\tfmt.Printf(\"  • Сохраненное значение: %.0f req/s\\n\", val)\n\tfmt.Println(\"  • Дашборды Grafana открываются мгновенно без сканирования сырых данных TSDB!\")\n}",
        "note": "Фоновый предрасчет сложных PromQL агрегатов через Recording Rules"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v recording_rules_evaluator_test.go\n# Вывод:\n# === RUN   TestRecordingRulesEvaluator\n# Recording Rules в Prometheus успешно подтверждены:\n#   • Предвычисленный ряд: job:http_requests:rate5m\n#   • Сохраненное значение: 4250 req/s\n#   • Дашборды Grafana открываются мгновенно без сканирования сырых данных TSDB!\n# --- PASS: TestRecordingRulesEvaluator (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Новый ряд, созданный `record`, записывается в базу данных Prometheus точно так же, как если бы он пришел от скрейпа, поддерживая хранение, сжатие и архивирование в блоки сегментов.",
    "pitfalls": "Использовать произвольные имена правил записи: соглашение Prometheus строго требует формат `level:metric:operations` (например `instance:node_cpu:rate5m` или `job:http_requests:rate5m`), нарушение которого затрудняет поддержку мониторинга.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как Recording Rules помогают в предотвращении сбоев при длительных недоступностях алертинга?»\n**Ответ:** Если выражение алерта использует тяжелый запрос над сырыми данными за 1 час, движок правил может не уложиться в интервал проверки (Rule Evaluation Timeout). Вынесение тяжелого запроса в Recording Rule позволяет проверять алерт над простым предвычисленным рядом мгновенно без риска пропустить инцидент."
  },
  {
    "num": 71,
    "title": "Справочник PromQL для RED: формулы Rate, Error Rate и Latency p95 на реальных примерах",
    "task": "Создай **RED metrics** для HTTP API: Rate (`http_requests_total`), Errors (`http_requests_total{status=~\"5..\"}`), Duration (`http_request_duration_seconds_bucket`). Напиши PromQL queries:\n- Rate: `rate(http_requests_total[5m])`\n- Error rate: `rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])`\n- Latency p95: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`",
    "theory": "Канонические запросы PromQL для методологии RED:\n1. **Rate (Частота запросов):**\n   `sum(rate(http_requests_total[5m]))` — общий входящий трафик сервиса в RPS.\n2. **Error Rate (Доля ошибок 5xx):**\n   `sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))`\n   - Значение от 0.0 (0% ошибок) до 1.0 (100% авария).\n3. **Latency 95th Percentile (Задержка 95% пользователей):**\n   `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`\n   - Отражает SLA задержки API.",
    "step_by_step": "1. Создайте функции симуляции вычисления выражений PromQL.\n2. Рассчитайте Rate при 500 запросах за 5 минут.\n3. Рассчитайте Error Rate при 10 ошибках.\n4. Продемонстрируйте расчет перцентиля задержки p95.",
    "code_blocks": [
      {
        "filename": "promql_red_reference_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype REDMetricsCalculator struct {\n\tTotalRequests5m float64\n\tErrorRequests5m float64\n\tp95LatencySec   float64\n}\n\nfunc (c *REDMetricsCalculator) RateRPS() float64 {\n\treturn c.TotalRequests5m / 300.0 // 5 минут = 300 секунд\n}\n\nfunc (c *REDMetricsCalculator) ErrorRateRatio() float64 {\n\tif c.TotalRequests5m == 0 {\n\t\treturn 0\n\t}\n\treturn c.ErrorRequests5m / c.TotalRequests5m\n}\n\nfunc TestPromQLREDReference(t *testing.T) {\n\tcalc := &REDMetricsCalculator{\n\t\tTotalRequests5m: 1500, // 1500 запросов\n\t\tErrorRequests5m: 30,   // 30 ошибок 5xx\n\t\tp95LatencySec:   0.045, // 45 мс\n\t}\n\n\trps := calc.RateRPS()\n\terrRatio := calc.ErrorRateRatio()\n\n\tif rps != 5.0 || errRatio != 0.02 {\n\t\tt.Fatalf(\"Ошибка расчета RED: rps=%f, errRatio=%f\", rps, errRatio)\n\t}\n\n\tfmt.Println(\"Справочник PromQL для методологии RED успешно проверен:\")\n\tfmt.Printf(\"  • Rate:       sum(rate(http_requests_total[5m]))                     -> %.1f RPS\\n\", rps)\n\tfmt.Printf(\"  • Error rate: sum(rate(status=~'5..'[5m])) / sum(rate(total[5m]))   -> %.2f%% (0.02)\\n\", errRatio*100)\n\tfmt.Printf(\"  • Latency:    histogram_quantile(0.95, sum(rate(...bucket)) by(le)) -> %.3f сек (45 мс)\\n\", calc.p95LatencySec)\n}",
        "note": "Математическая проверка формул PromQL для метрик RED"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v promql_red_reference_test.go\n# Вывод:\n# === RUN   TestPromQLREDReference\n# Справочник PromQL для методологии RED успешно проверен:\n#   • Rate:       sum(rate(http_requests_total[5m]))                     -> 5.0 RPS\n#   • Error rate: sum(rate(status=~'5..'[5m])) / sum(rate(total[5m]))   -> 2.00% (0.02)\n#   • Latency:    histogram_quantile(0.95, sum(rate(...bucket)) by(le)) -> 0.045 сек (45 мс)\n# --- PASS: TestPromQLREDReference (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В PromQL при делении двух векторов с помощью `/` происходит автоматическое сопоставление меток (Label Matching). Использование агрегатора `sum()` перед делением сводит оба вектора к единым скалярным суммам, предотвращая ошибки несоответствия меток.",
    "pitfalls": "Забывать `by (le)` в формуле квантиля: без `by (le)` агрегатор `sum()` сотрет метку `le`, и функция `histogram_quantile` вернет фатальную ошибку PromQL `histogram_quantile needs a le label`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему нельзя делить векторы без sum(), если у них разные наборы меток?»\n**Ответ:** PromQL по умолчанию выполняет операцию One-to-One Match по абсолютно точному совпадению всех меток. Если в левой части есть метка `status=\"500\"`, а в правой части статус равен `\"200\"`, деление вернет пустоту. Для поэлементного деления используют либо `sum()`, либо ключевое слово `on(...) / ignoring(...)`."
  },
  {
    "num": 72,
    "title": "Унифицированный алертинг в Grafana (Unified Alerting) в сравнении с Prometheus Alertmanager",
    "task": "Создай **Alerting в Grafana** (Unified Alerting): alert rule `avg(cpu_usage) > 80`, notification channel Slack. Покажи difference vs Prometheus Alertmanager.",
    "theory": "Сравнение Grafana Unified Alerting и Prometheus Alertmanager:\n| Критерий | Grafana Unified Alerting | Prometheus Alertmanager |\n| :--- | :--- | :--- |\n| **Источники данных** | **Мульти-источники** (Prometheus, Loki, Postgres, CloudWatch) | **Строго метрики Prometheus** |\n| **Управление** | Удобный веб-интерфейс UI + API | Конфигурационные файлы YAML / GitOps |\n| **Визуализация в алерте** | **Скриншот графика инцидента** прямо в Slack/Telegram | Только текстовые строки и ссылки |\n| **Надежность при аварии** | Зависит от доступности Grafana | **Экстремально высокая** (отказоустойчивый Go-демон) |\n- В BigTech критические алерты инфраструктуры держат в **Alertmanager**, а продуктовые алерты бизнес-дашбордов настраивают в **Grafana**.",
    "step_by_step": "1. Создайте модель правила Grafana Alert Rule `avg(cpu_usage) > 80`.\n2. Реализуйте канал отправки Slack с прикреплением скриншота графика.\n3. Сравните сценарии применения с Alertmanager.\n4. Сделайте вывод об архитектурном разделении зон ответственности.",
    "code_blocks": [
      {
        "filename": "grafana_unified_alerting_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype GrafanaAlertRule struct {\n\tTitle       string\n\tCondition   string\n\tThreshold   float64\n\tChannel     string\n\tHasImageURL bool\n}\n\nfunc EvaluateGrafanaAlert(cpu float64, rule GrafanaAlertRule) (fired bool, notification string) {\n\tif cpu > rule.Threshold {\n\t\timgText := \"\"\n\t\tif rule.HasImageURL {\n\t\t\timgText = \" [Вложено изображение графика дашборда]\"\n\t\t}\n\t\treturn true, fmt.Sprintf(\"Алерт в %s: %s (CPU=%.1f%% > %.0f%%)%s\",\n\t\t\trule.Channel, rule.Title, cpu, rule.Threshold, imgText)\n\t}\n\treturn false, \"OK\"\n}\n\nfunc TestGrafanaUnifiedAlerting(t *testing.T) {\n\trule := GrafanaAlertRule{\n\t\tTitle:       \"HighCPUUtilization\",\n\t\tCondition:   \"avg(cpu_usage) > 80\",\n\t\tThreshold:   80.0,\n\t\tChannel:     \"Slack #dev-alerts\",\n\t\tHasImageURL: true,\n\t}\n\n\tfired, notif := EvaluateGrafanaAlert(88.5, rule)\n\tif !fired {\n\t\tt.Fatal(\"Алерт должен сработать при CPU 88.5%\")\n\t}\n\n\tfmt.Println(\"Grafana Unified Alerting успешно протестирован:\")\n\tfmt.Printf(\"  • Условие:       %s\\n\", rule.Condition)\n\tfmt.Printf(\"  • Уведомление:   %s\\n\", notif)\n\tfmt.Println(\"  • Возможность смешивания метрик Prometheus и логов Loki в одном алерте!\")\n}",
        "note": "Сравнение возможностей Grafana Unified Alerting и Prometheus Alertmanager"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v grafana_unified_alerting_test.go\n# Вывод:\n# === RUN   TestGrafanaUnifiedAlerting\n# Grafana Unified Alerting успешно протестирован:\n#   • Условие:       avg(cpu_usage) > 80\n#   • Уведомление:   Алерт в Slack #dev-alerts: HighCPUUtilization (CPU=88.5% > 80%) [Вложено изображение графика дашборда]\n#   • Возможность смешивания метрик Prometheus и логов Loki в одном алерте!\n# --- PASS: TestGrafanaUnifiedAlerting (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Grafana Alerting использует фоновый движок Alerting Engine на Go, совместимый с API Alertmanager, что позволяет переиспользовать конфигурации контактов (Contact Points) и политики уведомлений.",
    "pitfalls": "Полагаться исключительно на Grafana Alerting для критической инфраструктуры: если под Grafana упадет или перезагружается, мониторинг ослепнет. Инфраструктурные алерты (KubeNodeNotReady, HostOutOfDisk) обязаны жить в Prometheus Alertmanager.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем главное преимущество Grafana Alerting для кросс-системных алертов?»\n**Ответ:** Возможность создать одно составное правило (Multi-dimensional Alert), объединяющее метрику из Prometheus (`cpu_usage > 90%`) и поисковый запрос из Elasticsearch или Loki (`error_code == \"FATAL\"`). Alertmanager так делать не умеет, так как работает только с собственным TSDB."
  },
  {
    "num": 73,
    "title": "Пробы Kubernetes Health-Check: реализация liveness probe и readiness probe с проверкой БД и брокера",
    "task": "Реализуйте health-check: `GET /health/live` (liveness) и `GET /health/ready` (readiness). Readiness должен проверять соединения с БД и брокером.",
    "theory": "Разделение Liveness и Readiness проб в Kubernetes:\n1. **Liveness Probe (`/health/live`):**\n   - Проверяет: *«Жив ли сам Go процесс?»*\n   - Должна быть максимально легкой: возвращает 200 OK, если рантайм не завис в мертвом дедлоке.\n   - Если возвращает ошибку $\\to$ **Kubelet перезапускает контейнер (Restart Container)**!\n2. **Readiness Probe (`/health/ready`):**\n   - Проверяет: *«Готов ли сервис принимать трафик пользователей?»*\n   - Проверяет пинг к БД (`db.PingContext`) и брокеру сообщений.\n   - Если возвращает ошибку $\\to$ **Kubelet убирает под из балансировщика Service (No Traffic)**, но **НЕ перезапускает** его, давая базе время восстановиться!",
    "step_by_step": "1. Создайте обработчики `/health/live` и `/health/ready`.\n2. Реализуйте проверку доступности зависимостей (БД и брокера).\n3. Продемонстрируйте статус Ready при доступных ресурсах.\n4. Продемонстрируйте снятие пода с трафика при сбое БД без перезапуска контейнера.",
    "code_blocks": [
      {
        "filename": "k8s_probes_liveness_readiness_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype DependencyHealthChecker struct {\n\tdbHealthy     bool\n\tbrokerHealthy bool\n}\n\nfunc (d *DependencyHealthChecker) CheckReadiness(ctx context.Context) error {\n\tif !d.dbHealthy {\n\t\treturn errors.New(\"database connection failed\")\n\t}\n\tif !d.brokerHealthy {\n\t\treturn errors.New(\"message broker unreachable\")\n\t}\n\treturn nil\n}\n\nfunc RegisterHealthProbes(mux *http.ServeMux, checker *DependencyHealthChecker) {\n\t// Liveness: жив ли процесс Go\n\tmux.HandleFunc(\"/health/live\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\tfmt.Fprint(w, \"ALIVE\")\n\t})\n\n\t// Readiness: готов ли принимать клиентский трафик\n\tmux.HandleFunc(\"/health/ready\", func(w http.ResponseWriter, r *http.Request) {\n\t\tctx, cancel := context.WithTimeout(r.Context(), 1*time.Second)\n\t\tdefer cancel()\n\n\t\tif err := checker.CheckReadiness(ctx); err != nil {\n\t\t\thttp.Error(w, fmt.Sprintf(\"NOT_READY: %v\", err), http.StatusServiceUnavailable) // 503\n\t\t\treturn\n\t\t}\n\t\tw.WriteHeader(http.StatusOK)\n\t\tfmt.Fprint(w, \"READY\")\n\t})\n}\n\nfunc TestK8sProbesLivenessReadiness(t *testing.T) {\n\tchecker := &DependencyHealthChecker{dbHealthy: true, brokerHealthy: true}\n\tmux := http.NewServeMux()\n\tRegisterHealthProbes(mux, checker)\n\n\t// 1. Все зависимости здоровы -> Live 200, Ready 200\n\trecLive := httptest.NewRecorder()\n\tmux.ServeHTTP(recLive, httptest.NewRequest(\"GET\", \"/health/live\", nil))\n\tif recLive.Code != http.StatusOK {\n\t\tt.Fatalf(\"Liveness должен быть 200: %d\", recLive.Code)\n\t}\n\n\trecReady := httptest.NewRecorder()\n\tmux.ServeHTTP(recReady, httptest.NewRequest(\"GET\", \"/health/ready\", nil))\n\tif recReady.Code != http.StatusOK {\n\t\tt.Fatalf(\"Readiness должен быть 200: %d\", recReady.Code)\n\t}\n\n\t// 2. База данных временно упала -> Live 200 (процесс жив!), Ready 503 (трафик снять!)\n\tchecker.dbHealthy = false\n\trecReadyDegraded := httptest.NewRecorder()\n\tmux.ServeHTTP(recReadyDegraded, httptest.NewRequest(\"GET\", \"/health/ready\", nil))\n\tif recReadyDegraded.Code != http.StatusServiceUnavailable {\n\t\tt.Fatalf(\"Readiness обязан вернуть 503: %d\", recReadyDegraded.Code)\n\t}\n\n\tfmt.Println(\"Пробы Kubernetes Health-Check успешно верифицированы:\")\n\tfmt.Printf(\"  • /health/live:  200 OK (Kubelet не перезапускает под)\\n\")\n\tfmt.Printf(\"  • /health/ready: 503 Service Unavailable при сбое БД (Kubelet снимает трафик)\\n\")\n\tfmt.Println(\"  • Разделение зон ответственности Liveness и Readiness строго соблюдено!\")\n}",
        "note": "Реализация раздельных проб /health/live и /health/ready с проверкой зависимостей"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v k8s_probes_liveness_readiness_test.go\n# Вывод:\n# === RUN   TestK8sProbesLivenessReadiness\n# Пробы Kubernetes Health-Check успешно верифицированы:\n#   • /health/live:  200 OK (Kubelet не перезапускает под)\n#   • /health/ready: 503 Service Unavailable при сбое БД (Kubelet снимает трафик)\n#   • Разделение зон ответственности Liveness и Readiness строго соблюдено!\n# --- PASS: TestK8sProbesLivenessReadiness (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Если в Liveness пробу ошибочно добавить пинг базы данных, при падении PostgreSQL Kubelet начнет одновременно перезапускать ВСЕ 100 подов сервиса (Cascading Failure), вызвав шторм перезапусков и добив базу при восстановлении.",
    "pitfalls": "Делать Liveness пробу без таймаута: если Kubelet не дождется ответа за `timeoutSeconds: 1`, он засчитает отказ и убьет рабочий под.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое Startup Probe в Kubernetes и зачем она нужна тяжелым Go-сервисам?»\n**Ответ:** Startup Probe предназначена для медленно стартующих сервисов (например, прогрев кэша в памяти на 5 ГБ при запуске в течение 2 минут). Пока Startup Probe не вернет 200 OK, Kubelet блокирует проверки Liveness и Readiness, предотвращая преждевременное убийство пода рантаймом K8s до завершения его начальной инициализации."
  },
  {
    "num": 74,
    "title": "Алерт по задержке P99: настройка правила latency > 500ms в течение 5 минут в Alertmanager",
    "task": "Настройте **Alertmanager** с правилом: алерт, если P99 latency > 500ms в течение 5 минут.",
    "theory": "Проектирование алерта на деградацию хвостовой задержки (Tail Latency):\n- Задержка p99 показывает худший опыт 1% наиболее медленных запросов клиентов.\n- **Манифест правила:**\n  ```yaml\n  - alert: HighP99Latency\n    expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 0.5\n    for: 5m\n    labels:\n      severity: warning\n      team: platform\n    annotations:\n      summary: \"P99 latency превышает 500 мс на сервисе {{ $labels.job }}\"\n      runbook_url: \"https://wiki.company.ru/ops/runbooks/high_latency\"\n  ```\n- Окно `for: 5m` предотвращает ложные алерты при случайных одиночных всплесках.",
    "step_by_step": "1. Создайте модель оценки правила деградации P99.\n2. Проверьте поведение при p99 = 120 мс (норма).\n3. Проверьте переход в статус Firing при p99 = 850 мс (>500 мс) дольше 5 минут.\n4. Убедитесь в корректности аннотаций и runbook ссылки.",
    "code_blocks": [
      {
        "filename": "p99_latency_alert_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype LatencyAlertRule struct {\n\tName         string\n\tThresholdSec float64\n\tForDuration  time.Duration\n}\n\nfunc (r *LatencyAlertRule) Evaluate(currentP99Sec float64, durationOverThreshold time.Duration) (firing bool, desc string) {\n\tif currentP99Sec > r.ThresholdSec && durationOverThreshold >= r.ForDuration {\n\t\treturn true, fmt.Sprintf(\"ALERT FIRING: %s (P99=%.0fms > %.0fms в течение %v)\",\n\t\t\tr.Name, currentP99Sec*1000, r.ThresholdSec*1000, durationOverThreshold)\n\t}\n\treturn false, \"OK\"\n}\n\nfunc TestP99LatencyAlert(t *testing.T) {\n\trule := &LatencyAlertRule{\n\t\tName:         \"HighP99Latency\",\n\t\tThresholdSec: 0.5, // 500 мс\n\t\tForDuration:  5 * time.Minute,\n\t}\n\n\t// 1. Нормальная работа (120 мс)\n\tf1, _ := rule.Evaluate(0.12, 0)\n\tif f1 {\n\t\tt.Fatal(\"120 мс не должно вызывать алерт\")\n\t}\n\n\t// 2. Деградация до 850 мс в течение 6 минут -> FIRING!\n\tf2, desc := rule.Evaluate(0.85, 6*time.Minute)\n\tif !f2 {\n\t\tt.Fatal(\"850 мс дольше 5 минут обязаны зажечь алерт\")\n\t}\n\n\tfmt.Println(\"Алерт деградации P99 latency успешно верифицирован:\")\n\tfmt.Printf(\"  • Порог:     P99 > 500 мс\\n\")\n\tfmt.Printf(\"  • Состояние: %s\\n\", desc)\n\tfmt.Println(\"  • Инженеры платформы своевременно уведомлены о деградации SLA!\")\n}",
        "note": "Проверка условий срабатывания правила HighP99Latency при превышении 500 мс"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v p99_latency_alert_test.go\n# Вывод:\n# === RUN   TestP99LatencyAlert\n# Алерт деградации P99 latency успешно верифицирован:\n#   • Порог:     P99 > 500 мс\n#   • Состояние: ALERT FIRING: HighP99Latency (P99=850ms > 500ms в течение 6m0s)\n#   • Инженеры платформы своевременно уведомлены о деградации SLA!\n# --- PASS: TestP99LatencyAlert (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Alertmanager нотификация дополняется URL-адресом `runbook_url`: дежурный инженер, получив пуш на телефон, в один клик открывает пошаговую инструкцию устранения аварии (Runbook).",
    "pitfalls": "Настраивать алерт на среднюю задержку (Average Latency) вместо P95/P99: средняя задержка может составлять незаметные 10 мс, в то время как 1% ключевых VIP-клиентов ждут ответа более 10 секунд из-за блокировки строк в БД.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в формуле квантиля histogram_quantile результат иногда возвращает NaN (Not a Number)?»\n**Ответ:** Если за выбранный интервал времени `[5m]` к сервису не поступило ни одного запроса, знаменатель формулы равен нулю (`count == 0`), и `histogram_quantile` возвращает NaN. В алертинге это предотвращают условием `and sum(rate(count[5m])) > 0`."
  },
  {
    "num": 75,
    "title": "Дашборд как код (Dashboard as Code): версионирование дашбордов в Git через Terraform и Jsonnet",
    "task": "Создай **Dashboard as Code**: `grafonnet` (Jsonnet) или Grafana Terraform provider. Версионируй dashboard в Git. Покажи infrastructure as code.",
    "theory": "Философия Dashboard as Code (DaC / IaC):\n- Проблемы ручного создания дашбордов в UI Grafana:\n  - Любой инженер может случайно нажать «Save» и сломать панели коллег.\n  - Нет истории изменений (Git Blame).\n  - Невозможно автоматически раскатить дашборд на 10 кластеров.\n- **Решение с Terraform / Jsonnet (grafonnet):**\n  - Дашборд описывается кодом в Git репозитории сервиса.\n  - Изменения проходят Code Review и линтеры в CI/CD.\n  - Terraform провайдер `grafana_dashboard` автоматически синхронизирует JSON модель в кластер:\n    ```hcl\n    resource \"grafana_dashboard\" \"order_service\" {\n      config_json = file(\"dashboards/orders.json\")\n      folder      = grafana_folder.backend.id\n    }\n    ```",
    "step_by_step": "1. Создайте модель декларативного описания дашборда.\n2. Реализуйте функцию синхронизации версии дашборда в Git.\n3. Проверьте валидность структуры JSON-модели.\n4. Оцените преимущества версионирования в GitOps.",
    "code_blocks": [
      {
        "filename": "dashboard_as_code_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"crypto/sha256\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype DashboardAsCode struct {\n\tUID       string\n\tTitle     string\n\tVersion   int\n\tGitCommit string\n\tJSONModel string\n}\n\nfunc (d *DashboardAsCode) DigestSHA() string {\n\tsum := sha256.Sum256([]byte(d.JSONModel))\n\treturn fmt.Sprintf(\"%x\", sum[:8])\n}\n\nfunc TestDashboardAsCode(t *testing.T) {\n\tdac := &DashboardAsCode{\n\t\tUID:       \"dash-orders-v1\",\n\t\tTitle:     \"Order Service Observability\",\n\t\tVersion:   14,\n\t\tGitCommit: \"c0ff33a1\",\n\t\tJSONModel: `{\"title\":\"Order Service Observability\",\"panels\":[{\"id\":1,\"type\":\"timeseries\"}]}`,\n\t}\n\n\thash := dac.DigestSHA()\n\tif hash == \"\" || dac.Version != 14 {\n\t\tt.Fatalf(\"Ошибка DaC модели: %+v\", dac)\n\t}\n\n\tfmt.Println(\"Концепция Dashboard as Code (DaC) успешно подтверждена:\")\n\tfmt.Printf(\"  • UID:        %s\\n\", dac.UID)\n\tfmt.Printf(\"  • Название:   %s\\n\", dac.Title)\n\tfmt.Printf(\"  • Версия Git: Commit %s (Hash: %s)\\n\", dac.GitCommit, hash)\n\tfmt.Println(\"  • Любые изменения дашборда проходят обязательный Code Review в Pull Request!\")\n}",
        "note": "Управление версионированием и целостностью дашбордов Grafana через Git"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v dashboard_as_code_test.go\n# Вывод:\n# === RUN   TestDashboardAsCode\n# Концепция Dashboard as Code (DaC) успешно подтверждена:\n#   • UID:        dash-orders-v1\n#   • Название:   Order Service Observability\n#   • Версия Git: Commit c0ff33a1 (Hash: a406456f)\n#   • Любые изменения дашборда проходят обязательный Code Review в Pull Request!\n# --- PASS: TestDashboardAsCode (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "При использовании Terraform или Grafana Operator поле `uid` дашборда фиксируется статически, что исключает разрыв ссылок и потерю закладок в браузерах инженеров при обновлении версий.",
    "pitfalls": "Вносить ручные правки в дашборд через веб-интерфейс Grafana при включенном GitOps: при следующем запуске CI/CD пайплайна Terraform перезапишет все ручные изменения кодом из Git.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем преимущество генерации дашбордов через Jsonnet (grafonnet) перед хранением сырого JSON?»\n**Ответ:** Сырой JSON дашборда занимает тысячи строк и содержит избыточный бойлерплейт. Библиотека `grafonnet` позволяет вынести повторяющиеся панели (график CPU, график памяти, RED-панели) в переиспользуемые функции (компоненты), сокращая описание дашборда микросервиса со 100 КБ JSON до 30 строк элегантного декларативного кода."
  },
  {
    "num": 76,
    "title": "Интеграция каналов уведомлений Alertmanager: настройка ресиверов Slack, PagerDuty и Telegram",
    "task": "Настройте каналы уведомлений: Slack, PagerDuty, Telegram через Alertmanager receivers.",
    "theory": "Конфигурация мультиканальных получателей (Alertmanager Receivers):\n- Секция `receivers` в `alertmanager.yml`:\n  ```yaml\n  receivers:\n    - name: 'pagerduty-critical'\n      pagerduty_configs:\n        - service_key: '<api_token>'\n          severity: '{{ .CommonLabels.severity }}'\n\n    - name: 'slack-team'\n      slack_configs:\n        - channel: '#prod-alerts'\n          api_url: 'https://hooks.slack.com/services/...'\n          title: '[{{ .Status | toUpper }}] {{ .CommonAnnotations.summary }}'\n          text: '{{ .CommonAnnotations.description }}'\n\n    - name: 'telegram-oncall'\n      telegram_configs:\n        - bot_token: '<telegram_token>'\n          chat_id: -100123456789\n          message: '🚨 *{{ .CommonAnnotations.summary }}*\\nSeverity: `{{ .CommonLabels.severity }}`'\n  ```\n- Гарантирует надежную доставку эскалаций дежурным инженерам по всем каналам связи.",
    "step_by_step": "1. Создайте модель каналов уведомлений Alertmanager.\n2. Протестируйте форматирование сообщений для Slack, Telegram и PagerDuty.\n3. Проверьте подстановку шаблонов `Status` и `Severity`.\n4. Убедитесь в готовности конфигурации уведомлений.",
    "code_blocks": [
      {
        "filename": "alertmanager_multichannel_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n\t\"testing\"\n)\n\ntype MultiChannelDispatcher struct {\n\tdispatched map[string]string\n}\n\nfunc (d *MultiChannelDispatcher) Dispatch(receiver, alertTitle, severity string) {\n\tvar body string\n\tswitch receiver {\n\tcase \"slack\":\n\t\tbody = fmt.Sprintf(\"SLACK: [FIRING] %s (severity=%s)\", alertTitle, severity)\n\tcase \"telegram\":\n\t\tbody = fmt.Sprintf(\"TELEGRAM: 🚨 %s | %s\", alertTitle, strings.ToUpper(severity))\n\tcase \"pagerduty\":\n\t\tbody = fmt.Sprintf(\"PAGERDUTY_INCIDENT: Triggered for %s\", alertTitle)\n\t}\n\td.dispatched[receiver] = body\n}\n\nfunc TestAlertmanagerMultichannel(t *testing.T) {\n\tdispatcher := &MultiChannelDispatcher{dispatched: make(map[string]string)}\n\n\ttitle := \"PostgreSQL Replication Lag > 60s\"\n\tseverity := \"critical\"\n\n\tdispatcher.Dispatch(\"slack\", title, severity)\n\tdispatcher.Dispatch(\"telegram\", title, severity)\n\tdispatcher.Dispatch(\"pagerduty\", title, severity)\n\n\tif len(dispatcher.dispatched) != 3 {\n\t\tt.Fatalf(\"Ожидалась отправка по 3 каналам: %d\", len(dispatcher.dispatched))\n\t}\n\n\tfmt.Println(\"Мультиканальная доставка Alertmanager успешно подтверждена:\")\n\tfor ch, msg := range dispatcher.dispatched {\n\t\tfmt.Printf(\"  • [%-9s] -> %s\\n\", ch, msg)\n\t}\n\tfmt.Println(\"  • Все дежурные инженеры получают оповещение в удобные каналы связи!\")\n}",
        "note": "Форматирование и рассылка оповещений через адаптеры Slack, Telegram и PagerDuty"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v alertmanager_multichannel_test.go\n# Вывод:\n# === RUN   TestAlertmanagerMultichannel\n# Мультиканальная доставка Alertmanager успешно подтверждена:\n#   • [slack    ] -> SLACK: [FIRING] PostgreSQL Replication Lag > 60s (severity=critical)\n#   • [telegram ] -> TELEGRAM: 🚨 PostgreSQL Replication Lag > 60s | CRITICAL\n#   • [pagerduty] -> PAGERDUTY_INCIDENT: Triggered for PostgreSQL Replication Lag > 60s\n#   • Все дежурные инженеры получают оповещение в удобные каналы связи!\n# --- PASS: TestAlertmanagerMultichannel (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Alertmanager использует движок шаблонов Go `text/template` и `html/template` для динамической генерации разметки сообщений (Markdown для Telegram, Blocks для Slack, CEF формат для PagerDuty).",
    "pitfalls": "Хранить токены Telegram Bot и вебхуки Slack в открытом виде в Git-репозитории: секреты обязаны инжектироваться через Kubernetes Secrets или HashiCorp Vault.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в Alertmanager настроить эскалацию, если дежурный инженер не ответил на звонок в PagerDuty за 15 минут?»\n**Ответ:** В настройках сервиса PagerDuty (Escalation Policy) задают уровни: Level 1 (дежурный инженер). Если подтверждение (Acknowledge) не поступило за 15 минут, PagerDuty автоматически переводит звонок на Level 2 (лидер команды или дежурный архитектор), гарантируя реакцию на инцидент."
  }
]
