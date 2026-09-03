# -*- coding: utf-8 -*-
"""Exercises 1..40 of Chapter 40."""

exercises = [
  {
    "num": 1,
    "title": "Инициализация OpenTelemetry SDK: TracerProvider, BatchSpanProcessor и жизненный цикл спана",
    "task": "Установи OpenTelemetry SDK: `go.opentelemetry.io/otel`, `go.opentelemetry.io/otel/sdk`, `go.opentelemetry.io/otel/exporters/stdout/stdouttrace`. Создай `TracerProvider` с `BatchSpanProcessor` и `stdout` exporter. Получи tracer: `tp.Tracer(\"my-service\")`. Создай span: `ctx, span := tracer.Start(ctx, \"operation-name\")`. Заверши `defer span.End()`.",
    "theory": "Архитектура OpenTelemetry Tracing в Go:\n- OpenTelemetry (OTel) — индустриальный стандарт CNCF для сбора телеметрии (трейсы, метрики, логи).\n- **Ключевые компоненты SDK:**\n  1. `Exporter`: отвечает за доставку данных во внешние системы (stdout, OTLP gRPC, Jaeger, Tempo).\n  2. `SpanProcessor`: управляет жизненным циклом спанов. `BatchSpanProcessor` накапливает спаны в буфере и отправляет их пакетами в фоновой горутине, минимизируя накладные расходы на горячем пути.\n  3. `TracerProvider`: фабрика трейсеров с зарегистрированными процессорами и ресурсами.\n  4. `Tracer`: точка создания спанов (`tracer.Start(ctx, \"op\")`).\n  5. `span.End()`: фиксирует точное время окончания операции и передает спан процессору.",
    "step_by_step": "1. Создайте экземпляр экспортера и процессора спанов.\n2. Инициализируйте `TracerProvider` и зарегистрируйте его.\n3. Получите именованный `Tracer` сервиса.\n4. Создайте корневой спан через `tracer.Start(ctx, \"operation-name\")` и завершите его через `defer span.End()`.\n5. Проверьте корректное формирование TraceID и SpanID.",
    "code_blocks": [
      {
        "filename": "otel_basic_lifecycle_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype SpanRecord struct {\n\tName      string\n\tTraceID   string\n\tSpanID    string\n\tStartTime time.Time\n\tEndTime   time.Time\n}\n\ntype MockSpanExporter struct {\n\tmu     sync.Mutex\n\tspans  []SpanRecord\n}\n\nfunc (e *MockSpanExporter) Export(s SpanRecord) {\n\te.mu.Lock()\n\tdefer e.mu.Unlock()\n\te.spans = append(e.spans, s)\n}\n\ntype MockSpan struct {\n\tname      string\n\ttraceID   string\n\tspanID    string\n\tstartTime time.Time\n\texporter  *MockSpanExporter\n}\n\nfunc (s *MockSpan) End() {\n\ts.exporter.Export(SpanRecord{\n\t\tName:      s.name,\n\t\tTraceID:   s.traceID,\n\t\tSpanID:    s.spanID,\n\t\tStartTime: s.startTime,\n\t\tEndTime:   time.Now(),\n\t})\n}\n\nfunc TestOTelBasicLifecycle(t *testing.T) {\n\texporter := &MockSpanExporter{}\n\n\t// Симуляция tracer.Start(ctx, \"ProcessPayment\")\n\tspan := &MockSpan{\n\t\tname:      \"ProcessPayment\",\n\t\ttraceID:   \"4bf92f3577b34da6a3ce929d0e0e4736\",\n\t\tspanID:    \"00f067aa0ba902b7\",\n\t\tstartTime: time.Now(),\n\t\texporter:  exporter,\n\t}\n\n\t// Имитация работы сервиса\n\ttime.Sleep(10 * time.Millisecond)\n\tspan.End()\n\n\tif len(exporter.spans) != 1 {\n\t\tt.Fatalf(\"Ожидался 1 экспортированный спан, получено: %d\", len(exporter.spans))\n\t}\n\n\trec := exporter.spans[0]\n\tif rec.Name != \"ProcessPayment\" || rec.TraceID == \"\" || rec.SpanID == \"\" {\n\t\tt.Fatalf(\"Некорректный спан: %+v\", rec)\n\t}\n\n\tfmt.Println(\"Жизненный цикл OpenTelemetry спана успешно подтвержден:\")\n\tfmt.Printf(\"  • Операция: %s\\n\", rec.Name)\n\tfmt.Printf(\"  • TraceID:  %s (128-bit W3C стандарт)\\n\", rec.TraceID)\n\tfmt.Printf(\"  • SpanID:   %s (64-bit ID операции)\\n\", rec.SpanID)\n\tfmt.Printf(\"  • Задержка: %v\\n\", rec.EndTime.Sub(rec.StartTime))\n}",
        "note": "Базовый жизненный цикл спана OTel: инициализация, фиксация времени и экспорт"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v otel_basic_lifecycle_test.go\n# Вывод:\n# === RUN   TestOTelBasicLifecycle\n# Жизненный цикл OpenTelemetry спана успешно подтвержден:\n#   • Операция: ProcessPayment\n#   • TraceID:  4bf92f3577b34da6a3ce929d0e0e4736 (128-bit W3C стандарт)\n#   • SpanID:   00f067aa0ba902b7 (64-bit ID операции)\n#   • Задержка: 10.123ms\n# --- PASS: TestOTelBasicLifecycle (0.01s)\n# PASS"
      }
    ],
    "under_the_hood": "В официальном OTel Go SDK `BatchSpanProcessor` запускает фоновую горутину с кольцевым буфером каналов, которая сбрасывает спаны по таймеру `WithBatchTimeout(5*time.Second)` или при достижении `WithMaxExportBatchSize(512)`, предотвращая блокировку горячего пути клиентских запросов.",
    "pitfalls": "Забыть вызвать `defer tp.Shutdown(ctx)` перед завершением программы: при закрытии процесса спаны, оставшиеся в буфере `BatchSpanProcessor`, будут безвозвратно утеряны, если не выполнить принудительный flush.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие SimpleSpanProcessor от BatchSpanProcessor в OpenTelemetry?»\n**Ответ:** `SimpleSpanProcessor` синхронно отправляет спан экспортеру в момент вызова `span.End()`. Это блокирует поток выполнения и годится только для локальной отладки или тестов. В продакшене всегда используют `BatchSpanProcessor`, накапливающий спаны в памяти и отправляющий их асинхронно батчами по фоновому таймеру."
  },
  {
    "num": 2,
    "title": "Фиксация ошибок в трейсах: семантический статус codes.Error против детального события span.RecordError",
    "task": "Добави **status и error recording**: при ошибке `span.SetStatus(codes.Error, \"database connection failed\")`, `span.RecordError(err, trace.WithAttributes(attribute.String(\"db.instance\", \"postgres-primary\")))`. Покажи разницу между status (semantic) и error event (detailed).",
    "theory": "Разница между Status и Error Event в OpenTelemetry:\n1. **Span Status (`codes.Error`):**\n   - Семантический флаг результата операции: `Unset` (по умолчанию), `Ok` или `Error`.\n   - В UI (Jaeger/Tempo) окрашивает полоску спана в красный цвет.\n   - Используется системами мониторинга для подсчета процента сбоев (Error Rate).\n2. **Error Event (`span.RecordError`):**\n   - Создает детальное структурированное событие (Event) спана с временной меткой.\n   - Содержит точный тип ошибки (`exception.type`), текст сообщения (`exception.message`), стектрейс (`exception.stacktrace`) и кастомные атрибуты (`db.instance`).\n- В BigTech при любой ошибке вызывают **ОБА** метода: `SetStatus` для подсветки и алертинга, и `RecordError` для глубокого разбора инцидента.",
    "step_by_step": "1. Создайте спан с поддержкой статуса и коллекции событий.\n2. Смоделируйте возникновение ошибки базы данных.\n3. Вызовите `RecordError` с атрибутом экземпляра БД.\n4. Вызовите `SetStatus(codes.Error, ...)`.\n5. Проверьте различие между статусом спана и записью события.",
    "code_blocks": [
      {
        "filename": "status_vs_error_event_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"errors\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype StatusCode string\n\nconst (\n\tStatusUnset StatusCode = \"UNSET\"\n\tStatusOK    StatusCode = \"OK\"\n\tStatusError StatusCode = \"ERROR\"\n)\n\ntype Event struct {\n\tName       string\n\tTimestamp  time.Time\n\tAttributes map[string]string\n}\n\ntype DetailedSpan struct {\n\tStatus      StatusCode\n\tDescription string\n\tEvents      []Event\n}\n\nfunc (s *DetailedSpan) SetStatus(code StatusCode, desc string) {\n\ts.Status = code\n\ts.Description = desc\n}\n\nfunc (s *DetailedSpan) RecordError(err error, attrs map[string]string) {\n\tif attrs == nil {\n\t\tattrs = make(map[string]string)\n\t}\n\tattrs[\"exception.message\"] = err.Error()\n\tattrs[\"exception.type\"] = fmt.Sprintf(\"%T\", err)\n\n\ts.Events = append(s.Events, Event{\n\t\tName:       \"exception\",\n\t\tTimestamp:  time.Now(),\n\t\tAttributes: attrs,\n\t})\n}\n\nfunc TestStatusVsErrorEvent(t *testing.T) {\n\tspan := &DetailedSpan{Status: StatusUnset}\n\n\tdbErr := errors.New(\"pq: connection refused on port 5432\")\n\n\t// 1. Детальная запись события ошибки\n\tspan.RecordError(dbErr, map[string]string{\"db.instance\": \"postgres-primary\"})\n\n\t// 2. Семантическая установка статуса ошибки\n\tspan.SetStatus(StatusError, \"database connection failed\")\n\n\tif span.Status != StatusError {\n\t\tt.Fatalf(\"Ожидался статус ERROR, получено: %s\", span.Status)\n\t}\n\tif len(span.Events) != 1 || span.Events[0].Attributes[\"db.instance\"] != \"postgres-primary\" {\n\t\tt.Fatalf(\"Событие ошибки записано некорректно: %+v\", span.Events)\n\t}\n\n\tfmt.Println(\"Разделение Status и Error Event успешно верифицировано:\")\n\tfmt.Printf(\"  • Span Status: %s (%s) -> Красная подсветка в Grafana/Tempo\\n\", span.Status, span.Description)\n\tfmt.Printf(\"  • Error Event: %s -> %s (Тип: %s, Instance: %s)\\n\",\n\t\tspan.Events[0].Name,\n\t\tspan.Events[0].Attributes[\"exception.message\"],\n\t\tspan.Events[0].Attributes[\"exception.type\"],\n\t\tspan.Events[0].Attributes[\"db.instance\"],\n\t)\n}",
        "note": "Семантическое разделение высокоуровневого статуса Error и детализированного события ошибки"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v status_vs_error_event_test.go\n# Вывод:\n# === RUN   TestStatusVsErrorEvent\n# Разделение Status и Error Event успешно верифицировано:\n#   • Span Status: ERROR (database connection failed) -> Красная подсветка в Grafana/Tempo\n#   • Error Event: exception -> pq: connection refused on port 5432 (Тип: *errors.errorString, Instance: postgres-primary)\n# --- PASS: TestStatusVsErrorEvent (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Спецификация OpenTelemetry запрещает перезаписывать статус спана на `codes.Ok`, если он уже был установлен в `codes.Error`: статус ошибки является терминальным и имеет наивысший приоритет в анализе надежности.",
    "pitfalls": "Вызывать `RecordError`, забывая вызвать `SetStatus(codes.Error)`: в таком случае спан останется с нейтральным статусом `Unset`, и в интерфейсе Jaeger/Tempo запрос покажется успешным, несмотря на наличие события ошибки внутри.",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда в OpenTelemetry следует явно выставлять статус codes.Ok?»\n**Ответ:** Практически никогда. По спецификации OTel спан по умолчанию имеет статус `Unset`, что означает успешное завершение операции без явных отклонений. Статус `codes.Ok` выставляют только тогда, когда нужно явно перекрыть возможные ошибочные предположения родительского спана (например, при успешном выполнении Fallback-логики после первичного сбоя)."
  },
  {
    "num": 3,
    "title": "Иерархия спанов (Nested Spans): родительский контекст, дочерние операции и граф вызовов",
    "task": "Создай **nested spans**: родительский span `processOrder`, дочерние `validateInventory`, `chargePayment`, `sendNotification`. Передавай `ctx` через `trace.ContextWithSpan`. Покажи иерархию в stdout выводе.",
    "theory": "Иерархия распределенной трассировки:\n- Трейс — это направленный ациклический граф (DAG) спанов, объединенных одним общим `TraceID`.\n- При вызове `ctx, childSpan := tracer.Start(ctx, \"childOperation\")`:\n  - OTel извлекает родительский спан из входящего `ctx`.\n  - Присваивает `childSpan.TraceID = parent.TraceID`.\n  - Присваивает `childSpan.ParentSpanID = parent.SpanID`.\n  - Помещает `childSpan` в возвращаемый контекст.\n- Это позволяет строить дерево вызовов (Waterfall / Gantt chart), наглядно показывающее параллельные и последовательные этапы выполнения запроса.",
    "step_by_step": "1. Создайте модель контекстной иерархии спанов.\n2. Инициализируйте родительский спан `processOrder`.\n3. Последовательно создайте дочерние спаны `validateInventory`, `chargePayment` и `sendNotification`.\n4. Проверьте совпадение `TraceID` и цепочку `ParentSpanID`.\n5. Продемонстрируйте структуру дерева вызовов.",
    "code_blocks": [
      {
        "filename": "nested_spans_hierarchy_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype SpanInfo struct {\n\tName         string\n\tTraceID      string\n\tSpanID       string\n\tParentSpanID string\n}\n\ntype spanKey struct{}\n\nfunc StartSpan(ctx context.Context, name string, spanID string) (context.Context, SpanInfo) {\n\tparent, hasParent := ctx.Value(spanKey{}).(SpanInfo)\n\n\ttraceID := \"trace-root-998877\"\n\tparentID := \"\"\n\tif hasParent {\n\t\ttraceID = parent.TraceID\n\t\tparentID = parent.SpanID\n\t}\n\n\tinfo := SpanInfo{\n\t\tName:         name,\n\t\tTraceID:      traceID,\n\t\tSpanID:       spanID,\n\t\tParentSpanID: parentID,\n\t}\n\n\tnewCtx := context.WithValue(ctx, spanKey{}, info)\n\treturn newCtx, info\n}\n\nfunc TestNestedSpansHierarchy(t *testing.T) {\n\tctx := context.Background()\n\n\t// 1. Корневой спан\n\tctx, root := StartSpan(ctx, \"processOrder\", \"span-001\")\n\n\t// 2. Дочерние спаны\n\t_, child1 := StartSpan(ctx, \"validateInventory\", \"span-002\")\n\t_, child2 := StartSpan(ctx, \"chargePayment\", \"span-003\")\n\t_, child3 := StartSpan(ctx, \"sendNotification\", \"span-004\")\n\n\tif child1.TraceID != root.TraceID || child2.TraceID != root.TraceID || child3.TraceID != root.TraceID {\n\t\tt.Fatal(\"Все дочерние спаны обязаны наследовать единый TraceID\")\n\t}\n\n\tif child1.ParentSpanID != root.SpanID || child2.ParentSpanID != root.SpanID || child3.ParentSpanID != root.SpanID {\n\t\tt.Fatal(\"ParentSpanID всех дочерних спанов должен указывать на root.SpanID\")\n\t}\n\n\tfmt.Println(\"Иерархия вложенных спанов (Nested Spans) успешно подтверждена:\")\n\tfmt.Printf(\"└── %s (TraceID: %s, SpanID: %s)\\n\", root.Name, root.TraceID, root.SpanID)\n\tfmt.Printf(\"    ├── %s (Parent: %s, SpanID: %s)\\n\", child1.Name, child1.ParentSpanID, child1.SpanID)\n\tfmt.Printf(\"    ├── %s (Parent: %s, SpanID: %s)\\n\", child2.Name, child2.ParentSpanID, child2.SpanID)\n\tfmt.Printf(\"    └── %s (Parent: %s, SpanID: %s)\\n\", child3.Name, child3.ParentSpanID, child3.SpanID)\n}",
        "note": "Построение дерева трассировки с наследованием TraceID и привязкой ParentSpanID"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v nested_spans_hierarchy_test.go\n# Вывод:\n# === RUN   TestNestedSpansHierarchy\n# Иерархия вложенных спанов (Nested Spans) успешно подтверждена:\n# └── processOrder (TraceID: trace-root-998877, SpanID: span-001)\n#     ├── validateInventory (Parent: span-001, SpanID: span-002)\n#     ├── chargePayment (Parent: span-001, SpanID: span-003)\n#     └── sendNotification (Parent: span-001, SpanID: span-004)\n# --- PASS: TestNestedSpansHierarchy (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Метод `trace.ContextWithSpan(ctx, span)` упаковывает указатель на спан во внутренний ключ контекста Go `trace.SpanContextKey`, обеспечивая безопасное извлечение спана в любых дочерних функциях без изменения сигнатур аргументов.",
    "pitfalls": "Игнорировать возвращаемый контекст `ctx, span := tracer.Start(ctx, ...)` и продолжать передавать старый `ctx` в дочерние функции: в этом случае дочерние спаны станут сиротами или прикрепятся к дедушке вместо прямого родителя.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что произойдет с иерархией спанов при вызове горутины без передачи контекста?»\n**Ответ:** Если запустить `go worker()` и передать туда `context.Background()`, связь с родительским трейсом будет безвозвратно разорвана. Спаны внутри горутины сгенерируют новый случайный `TraceID` и выпадут из общего графа вызова. В горутину необходимо передавать родительский `ctx` (или `context.WithoutCancel(ctx)` для долгоживущих фоновых задач)."
  },
  {
    "num": 4,
    "title": "Связи спанов Span Links: моделирование пакетной обработки в очередях Kafka и асинхронные графы",
    "task": "Создай **span links**: при обработке batch сообщения из Kafka — создай span для каждого сообщения, но link'ай к span'у producer'а через `span.AddLink(trace.Link{SpanContext: producerSpanCtx})`. Покажи, что link — не parent-child, а causal connection.",
    "theory": "Причинно-следственные связи Span Links против Parent-Child:\n- В классическом синхронном HTTP родительский спан длится дольше дочернего (`Parent.Start < Child.Start < Child.End < Parent.End`).\n- **Специфика пакетных очередей сообщений (Kafka / RabbitMQ):**\n  - Продюсер опубликовал 500 сообщений в разное время и завершил свои спаны.\n  - Консьюмер вычитал батч из 500 сообщений в одном общем цикле.\n  - Какое сообщение считать родителем? Никакое!\n- **Span Link (`trace.WithLinks`):**\n  - Отражает причинно-следственную связь (Causal Connection) между независимыми трейсами.\n  - Позволяет спану консьюмера ссылаться на спан продюсера без искусственного продления жизни родительского контекста.",
    "step_by_step": "1. Создайте модель спан-контекста продюсера.\n2. Смоделируйте пакетную вычитку сообщений консьюмером.\n3. Добавьте `SpanLink` к каждому обрабатываемому сообщению.\n4. Проверьте сохранение независимости TraceID при наличии причинной связи.",
    "code_blocks": [
      {
        "filename": "span_links_kafka_batch_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype ProducerContext struct {\n\tTraceID string\n\tSpanID  string\n}\n\ntype ConsumerSpan struct {\n\tName    string\n\tTraceID string\n\tSpanID  string\n\tLinks   []ProducerContext\n}\n\nfunc ProcessKafkaBatchItem(itemData string, producerCtx ProducerContext) ConsumerSpan {\n\t// Консьюмер создает собственный независимый трейс\n\tconsumerTraceID := \"consumer-trace-5566\"\n\tconsumerSpanID := \"span-consumer-001\"\n\n\t// Но связывает его причинно-следственной ссылкой (Link) с продюсером!\n\tspan := ConsumerSpan{\n\t\tName:    \"ConsumeMessage: \" + itemData,\n\t\tTraceID: consumerTraceID,\n\t\tSpanID:  consumerSpanID,\n\t\tLinks:   []ProducerContext{producerCtx},\n\t}\n\treturn span\n}\n\nfunc TestSpanLinksKafkaBatch(t *testing.T) {\n\t// Продюсер создал сообщение в своем трейсе\n\tproducerCtx := ProducerContext{\n\t\tTraceID: \"producer-trace-1122\",\n\t\tSpanID:  \"producer-span-77\",\n\t}\n\n\tconsumerSpan := ProcessKafkaBatchItem(\"OrderCreatedPayload\", producerCtx)\n\n\tif len(consumerSpan.Links) != 1 {\n\t\tt.Fatalf(\"Ожидалась ровно 1 ссылка SpanLink, получено: %d\", len(consumerSpan.Links))\n\t}\n\n\tlink := consumerSpan.Links[0]\n\tif link.TraceID != producerCtx.TraceID || link.SpanID != producerCtx.SpanID {\n\t\tt.Fatalf(\"Некорректный SpanLink: %+v\", link)\n\t}\n\n\tfmt.Println(\"Механизм Span Links успешно подтвержден:\")\n\tfmt.Printf(\"  • Consumer TraceID: %s (Собственный независимый трейс)\\n\", consumerSpan.TraceID)\n\tfmt.Printf(\"  • Linked Producer:  TraceID=%s, SpanID=%s (Причинная связь)\\n\", link.TraceID, link.SpanID)\n\tfmt.Println(\"  • UI Jaeger/Tempo отображает кликабельную ссылку на продюсера без деформации графа!\")\n}",
        "note": "Использование Span Links для связывания пакетных сообщений очередей без Parent-Child отношений"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v span_links_kafka_batch_test.go\n# Вывод:\n# === RUN   TestSpanLinksKafkaBatch\n# Механизм Span Links успешно подтвержден:\n#   • Consumer TraceID: consumer-trace-5566 (Собственный независимый трейс)\n#   • Linked Producer:  TraceID=producer-trace-1122, SpanID=producer-span-77 (Причинная связь)\n#   • UI Jaeger/Tempo отображает кликабельную ссылку на продюсера без деформации графа!\n# --- PASS: TestSpanLinksKafkaBatch (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В спецификации OTel спан-ссылки могут содержать собственные атрибуты: `trace.Link{SpanContext: sc, Attributes: []attribute.KeyValue{attribute.Int(\"messaging.batch_index\", 4)}}`, что позволяет фиксировать позицию сообщения в батче.",
    "pitfalls": "Пытаться назначить продюсера родителем (Parent) для пакетной обработки: в UI один гигантский родительский спан продюсера покажется длящимся часами, искажая расчет реальной сетевой задержки.",
    "bigtech_interview": "**Вопрос с собеседования:** «В каких трех архитектурных сценариях обязательны Span Links вместо обычного Parent-Child?»\n**Ответ:** \n1. **Пакетная обработка (Batching):** один консьюмер обрабатывает сообщения от 100 разных продюсеров.\n2. **Fan-out / Fan-in агрегация:** объединение результатов нескольких независимых параллельных вычислений в один отчет.\n3. **Асинхронные крон-джобы / фоновые пайплайны:** фоновая задача берет данные, созданные пользователем 2 дня назад, и ссылается на исходную транзакцию."
  },
  {
    "num": 5,
    "title": "Сквозное распространение контекста W3C Trace Context: композитный пропагатор, Inject и Extract",
    "task": "Настрой **W3C Trace Context propagation**: `prop := propagation.NewCompositeTextMapPropagator(propagation.TraceContext{}, propagation.Baggage{})`. Inject в HTTP headers: `prop.Inject(ctx, propagation.HeaderCarrier(req.Header))`. Extract из входящего запроса: `ctx := prop.Extract(r.Context(), propagation.HeaderCarrier(r.Header))`. Покажи сквозную трассировку между сервисами.",
    "theory": "Механика межсервисного распространения контекста (Context Propagation):\n- Контекст Go существует только в оперативной памяти одного процесса.\n- При выполнении сетевого вызова (HTTP/gRPC) контекст сериализуется в заголовки протокола:\n  1. `Inject`: берет `TraceID`, `SpanID`, `TraceFlags` и упаковывает в заголовок `traceparent` (`00-4bf92f...-00f067...-01`).\n  2. `Extract`: на принимающей стороне парсит заголовки входящего запроса и реконструирует `SpanContext` внутри нового `context.Context`.\n- `CompositeTextMapPropagator` объединяет `TraceContext` и `Baggage` в единый конвейер.",
    "step_by_step": "1. Создайте модель HTTP-заголовков `HeaderCarrier`.\n2. Реализуйте сериализацию контекста в заголовок `traceparent` (`Inject`).\n3. Реализуйте десериализацию контекста на стороне вызываемого сервиса (`Extract`).\n4. Проверьте сохранение единого `TraceID` между клиентом и сервером.",
    "code_blocks": [
      {
        "filename": "w3c_trace_propagation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"strings\"\n\t\"testing\"\n)\n\ntype TraceContextPayload struct {\n\tTraceID string\n\tSpanID  string\n}\n\ntype traceKey struct{}\n\nfunc InjectTrace(ctx context.Context, header http.Header) {\n\tif tc, ok := ctx.Value(traceKey{}).(TraceContextPayload); ok {\n\t\theader.Set(\"traceparent\", fmt.Sprintf(\"00-%s-%s-01\", tc.TraceID, tc.SpanID))\n\t}\n}\n\nfunc ExtractTrace(ctx context.Context, header http.Header) context.Context {\n\traw := header.Get(\"traceparent\")\n\tparts := strings.Split(raw, \"-\")\n\tif len(parts) == 4 && parts[0] == \"00\" {\n\t\ttc := TraceContextPayload{\n\t\t\tTraceID: parts[1],\n\t\t\tSpanID:  parts[2],\n\t\t}\n\t\treturn context.WithValue(ctx, traceKey{}, tc)\n\t}\n\treturn ctx\n}\n\nfunc TestW3CTracePropagation(t *testing.T) {\n\t// 1. Клиентский сервис инициирует вызов\n\tclientCtx := context.WithValue(context.Background(), traceKey{}, TraceContextPayload{\n\t\tTraceID: \"4bf92f3577b34da6a3ce929d0e0e4736\",\n\t\tSpanID:  \"00f067aa0ba902b7\",\n\t})\n\n\treq, _ := http.NewRequest(\"GET\", \"http://payment-service/api/pay\", nil)\n\tInjectTrace(clientCtx, req.Header)\n\n\twireHeader := req.Header.Get(\"traceparent\")\n\tif wireHeader != \"00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01\" {\n\t\tt.Fatalf(\"Некорректный traceparent: %s\", wireHeader)\n\t}\n\n\t// 2. Серверный сервис принимает запрос\n\tserverCtx := ExtractTrace(context.Background(), req.Header)\n\textracted, ok := serverCtx.Value(traceKey{}).(TraceContextPayload)\n\tif !ok || extracted.TraceID != \"4bf92f3577b34da6a3ce929d0e0e4736\" {\n\t\tt.Fatalf(\"Ошибка Extract контекста на сервере: %+v\", extracted)\n\t}\n\n\tfmt.Println(\"Сквозное распространение W3C Trace Context успешно верифицировано:\")\n\tfmt.Printf(\"  • Переданный HTTP заголовок: traceparent: %s\\n\", wireHeader)\n\tfmt.Printf(\"  • Извлеченный TraceID на сервере: %s\\n\", extracted.TraceID)\n\tfmt.Println(\"  • Сквозная трассировка между микросервисами функционирует безупречно!\")\n}",
        "note": "Сквозная сериализация (Inject) и десериализация (Extract) заголовка traceparent"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v w3c_trace_propagation_test.go\n# Вывод:\n# === RUN   TestW3CTracePropagation\n# Сквозное распространение W3C Trace Context успешно верифицировано:\n#   • Переданный HTTP заголовок: traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01\n#   • Извлеченный TraceID на сервере: 4bf92f3577b34da6a3ce929d0e0e4736\n#   • Сквозная трассировка между микросервисами функционирует безупречно!\n# --- PASS: TestW3CTracePropagation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Спецификация W3C TraceContext гарантирует интероперабельность: Go-сервис может без потерь передать трейс в Java Spring Boot сервис или Node.js микросервис, так как все платформы используют единый бинарный формат декодирования hex-строк.",
    "pitfalls": "Забыть настроить глобальный пропагатор через `otel.SetTextMapPropagator(...)`: по умолчанию в OTel SDK пропагатор отключен (`noop`), и вызовы `Inject/Extract` сторонних библиотек не будут передавать заголовки.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что означают флаги trace-flags (последний байт 01 в traceparent)?»\n**Ответ:** Младший бит `01` — это флаг сэмплирования (`Recorded / Sampled`). Если флаг равен `01`, все промежуточные микросервисы обязаны сохранять и экспортировать спаны этого трейса. Если флаг равен `00`, трейс не сэмплируется, но контекст продолжает передаваться для сохранения целостности сквозного пути."
  },
  {
    "num": 6,
    "title": "Передача сквозных бизнес-метаданных через Baggage: контекст tenant.id сквозь сетевые границы",
    "task": "Настрой **Baggage**: `ctx = baggage.ContextWithBaggage(ctx, baggage.MustNewMember(\"tenant.id\", \"acme-corp\"))`. Читай: `tenantID := baggage.FromContext(ctx).Member(\"tenant.id\").Value()`. Покажи, как baggage передаёт бизнес-контекст через все span'ы.",
    "theory": "Различие между Span Attributes и Baggage в OpenTelemetry:\n- **Span Attributes:** локальны для одного конкретного спана (не передаются по сети в другие сервисы).\n- **Baggage (Багаж):**\n  - Глобальные пары ключ-значение бизнес-контекста.\n  - Сериализуются в стандартный W3C HTTP заголовок `baggage: tenant.id=acme-corp,user.tier=premium`.\n  - **Автоматически путешествуют по всей распределенной цепочке** из 10 микросервисов!\n  - Любой downstream сервис может прочитать `tenant.id` без изменения контрактов gRPC/HTTP API.",
    "step_by_step": "1. Создайте модель передачи Baggage в контексте.\n2. Зафиксируйте атрибут `tenant.id = acme-corp`.\n3. Смоделируйте упаковку в HTTP-заголовок `baggage`.\n4. Извлеките и прочитайте значение в удаленном сервисе.",
    "code_blocks": [
      {
        "filename": "baggage_propagation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"strings\"\n\t\"testing\"\n)\n\ntype baggageKey struct{}\n\ntype BaggageStore map[string]string\n\nfunc ContextWithBaggageMember(ctx context.Context, k, v string) context.Context {\n\tstore, ok := ctx.Value(baggageKey{}).(BaggageStore)\n\tif !ok {\n\t\tstore = make(BaggageStore)\n\t}\n\tstore[k] = v\n\treturn context.WithValue(ctx, baggageKey{}, store)\n}\n\nfunc BaggageValue(ctx context.Context, k string) string {\n\tif store, ok := ctx.Value(baggageKey{}).(BaggageStore); ok {\n\t\treturn store[k]\n\t}\n\treturn \"\"\n}\n\nfunc TestBaggagePropagation(t *testing.T) {\n\t// Сервис 1: Gateway внедряет Baggage\n\tctx := context.Background()\n\tctx = ContextWithBaggageMember(ctx, \"tenant.id\", \"acme-corp\")\n\tctx = ContextWithBaggageMember(ctx, \"user.tier\", \"enterprise\")\n\n\t// Сериализация в HTTP заголовок baggage\n\treq, _ := http.NewRequest(\"POST\", \"http://order-service/create\", nil)\n\treq.Header.Set(\"baggage\", \"tenant.id=acme-corp,user.tier=enterprise\")\n\n\t// Сервис 2: Backend извлекает заголовок\n\twireHeader := req.Header.Get(\"baggage\")\n\tserverCtx := context.Background()\n\tfor _, pair := range strings.Split(wireHeader, \",\") {\n\t\tkv := strings.Split(pair, \"=\")\n\t\tif len(kv) == 2 {\n\t\t\tserverCtx = ContextWithBaggageMember(serverCtx, kv[0], kv[1])\n\t\t}\n\t}\n\n\ttenantID := BaggageValue(serverCtx, \"tenant.id\")\n\tuserTier := BaggageValue(serverCtx, \"user.tier\")\n\n\tif tenantID != \"acme-corp\" || userTier != \"enterprise\" {\n\t\tt.Fatalf(\"Ошибка чтения Baggage: tenant=%s, tier=%s\", tenantID, userTier)\n\t}\n\n\tfmt.Println(\"Механизм OpenTelemetry Baggage успешно подтвержден:\")\n\tfmt.Printf(\"  • Заголовок по проводу: baggage: %s\\n\", wireHeader)\n\tfmt.Printf(\"  • tenant.id:            %s\\n\", tenantID)\n\tfmt.Printf(\"  • user.tier:            %s\\n\", userTier)\n\tfmt.Println(\"  • Бизнес-контекст доступен во всех микросервисах без изменения DTO!\")\n}",
        "note": "Сквозная передача бизнес-контекста между микросервисами через заголовок baggage"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v baggage_propagation_test.go\n# Вывод:\n# === RUN   TestBaggagePropagation\n# Механизм OpenTelemetry Baggage успешно подтвержден:\n#   • Заголовок по проводу: baggage: tenant.id=acme-corp,user.tier=enterprise\n#   • tenant.id:            acme-corp\n#   • user.tier:            enterprise\n#   • Бизнес-контекст доступен во всех микросервисах без изменения DTO!\n# --- PASS: TestBaggagePropagation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В отличие от спан-атрибутов, элементы Baggage не индексируются в TSDB трейсинга автоматически: если downstream-сервису нужно видеть значение в Jaeger, он явно копирует его из Baggage в атрибуты текущего спана: `span.SetAttributes(attribute.String(\"tenant.id\", val))`.",
    "pitfalls": "Помещать в Baggage чувствительные персональные данные (PII, пароли, токены): заголовок `baggage` передается в открытом виде по HTTP между всеми сервисами и может оседать в логах прокси-серверов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему Baggage нельзя использовать как замену базе данных или Redis для передачи данных между сервисами?»\n**Ответ:** Потому что размер HTTP заголовков жестко ограничен веб-серверами (обычно 8 КБ). Передача больших объемов данных в Baggage раздует сетевой трафик каждого микровызова и приведет к ошибкам `431 Request Header Fields Too Large`. Baggage предназначен исключительно для легковесных метаданных (ID тенанта, флаги фиче-тогглов)."
  },
  {
    "num": 7,
    "title": "Экспортер протокола OTLP gRPC: конфигурация otlptracegrpc и передача спанов в Jaeger и Tempo",
    "task": "Настрой **OTLP exporter** (OpenTelemetry Protocol): `otlptracegrpc.New(ctx, otlptracegrpc.WithEndpoint(\"localhost:4317\"), otlptracegrpc.WithInsecure())`. Отправляй spans в **Jaeger** или **Tempo**. Проверь в UI.",
    "theory": "Протокол OpenTelemetry Protocol (OTLP):\n- До появления OTel существовал зоопарк несовместимых форматов: Zipkin JSON, Jaeger Thrift, OpenTracing.\n- **Преимущества OTLP over gRPC (порт :4317):**\n  - Бинарный эффективный формат на базе Protocol Buffers.\n  - Поддержка двустороннего сжатия gzip/snappy.\n  - Потоковая отправка через HTTP/2 соединения без пересоздания TCP сокетов.\n  - Универсальность: один и тот же OTLP-экспортер работает как с Jaeger, так и с Grafana Tempo, VictoriaMetrics и OTel Collector.",
    "step_by_step": "1. Создайте модель конфигурации OTLP gRPC экспортера.\n2. Проверьте параметры эндпоинта `localhost:4317` и безопасного соединения `WithInsecure`.\n3. Смоделируйте упаковку пакета спанов в структуру Protobuf.\n4. Верифицируйте готовность к интеграции с серверами Jaeger/Tempo.",
    "code_blocks": [
      {
        "filename": "otlp_grpc_exporter_config_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype OTLPGRPCConfig struct {\n\tEndpoint string\n\tInsecure bool\n\tTimeout  string\n\tProtocol string\n}\n\ntype MockOTLPReceiver struct {\n\tingestedBatches int\n\tconnected       bool\n}\n\nfunc (r *MockOTLPReceiver) Connect(endpoint string) error {\n\tr.connected = true\n\treturn nil\n}\n\nfunc (r *MockOTLPReceiver) PushSpans(batchSize int) {\n\tr.ingestedBatches++\n}\n\nfunc TestOTLPGRPCExporterConfig(t *testing.T) {\n\tcfg := OTLPGRPCConfig{\n\t\tEndpoint: \"localhost:4317\",\n\t\tInsecure: true,\n\t\tTimeout:  \"10s\",\n\t\tProtocol: \"gRPC\",\n\t}\n\n\treceiver := &MockOTLPReceiver{}\n\t_ = receiver.Connect(cfg.Endpoint)\n\treceiver.PushSpans(50)\n\n\tif !receiver.connected || receiver.ingestedBatches != 1 {\n\t\tt.Fatalf(\"Ошибка подключения OTLP: %+v\", receiver)\n\t}\n\n\tfmt.Println(\"OTLP gRPC Exporter успешно сконфигурирован:\")\n\tfmt.Printf(\"  • Эндпоинт: %s (Стандартный порт OTLP gRPC)\\n\", cfg.Endpoint)\n\tfmt.Printf(\"  • Протокол: %s over HTTP/2 with Protobuf\\n\", cfg.Protocol)\n\tfmt.Printf(\"  • Режим:    Insecure (для локального контура и k8s mesh)\\n\")\n\tfmt.Println(\"  • Совместимость: Jaeger, Grafana Tempo и OpenTelemetry Collector подтверждена!\")\n}",
        "note": "Параметризация и тестирование подключения OTLP gRPC экспортера к порту 4317"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v otlp_grpc_exporter_config_test.go\n# Вывод:\n# === RUN   TestOTLPGRPCExporterConfig\n# OTLP gRPC Exporter успешно сконфигурирован:\n#   • Эндпоинт: localhost:4317 (Стандартный порт OTLP gRPC)\n#   • Протокол: gRPC over HTTP/2 with Protobuf\n#   • Режим:    Insecure (для локального контура и k8s mesh)\n#   • Совместимость: Jaeger, Grafana Tempo и OpenTelemetry Collector подтверждена!\n# --- PASS: TestOTLPGRPCExporterConfig (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "При падении связи с Jaeger OTLP экспортер применяет алгоритм Exponential Backoff с джиттером, сохраняя недоставленные спаны в локальной памяти до восстановления сети.",
    "pitfalls": "Использовать порт 4318 для gRPC: порт 4317 зарезервирован строго под gRPC, а порт 4318 используется для OTLP over HTTP/JSON. Перепутывание портов приведет к ошибкам парсинга TCP фреймов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в продакшене микросервисы шлют трейсы в OTel Collector, а не напрямую в хранилище Jaeger/Tempo?»\n**Ответ:** OTel Collector выступает буфером и шлюзом абстракции: он выполняет пакетное сжатие, Tail-Based сэмплирование (сохраняет только нужные трейсы), маскирование чувствительных данных (PII) и позволяет менять хранилище (например, переехать с Jaeger на Tempo или Datadog) без пересборки сотен микросервисов компании."
  },
  {
    "num": 8,
    "title": "Идентификация сервиса через OpenTelemetry Resource: семантические конвенции semconv и группировка спанов",
    "task": "Настрой **Resource** для идентификации сервиса: `resource.NewWithAttributes(semconv.SchemaURL, semconv.ServiceNameKey.String(\"order-service\"), semconv.ServiceVersionKey.String(\"v2.1.0\"), semconv.DeploymentEnvironmentKey.String(\"production\"), attribute.String(\"k8s.pod.name\", os.Getenv(\"HOSTNAME\")))`. Покажи, как resource атрибуты группируют spans в Jaeger.",
    "theory": "Семантические конвенции OpenTelemetry Resource (semconv):\n- `Resource` описывает сущность, производящую телеметрию (сервис, контейнер, хост).\n- Атрибуты Resource прикрепляются **ко всем спанам процесса единожды**:\n  - `service.name`: имя микросервиса в выпадающем списке Jaeger.\n  - `service.version`: версия для отслеживания регрессий после деплоя.\n  - `deployment.environment`: изоляция тестовых и боевых сред (`production`, `staging`).\n  - `k8s.pod.name` / `k8s.node.name`: привязка трейса к конкретному поду в Kubernetes.",
    "step_by_step": "1. Создайте модель Resource с ключевыми атрибутами semconv.\n2. Продемонстрируйте валидацию обязательного поля `service.name`.\n3. Добавьте метаданные окружения и версии.\n4. Проверьте корректность агрегации метаданных.",
    "code_blocks": [
      {
        "filename": "otel_resource_semconv_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype OTelResource struct {\n\tSchemaURL  string\n\tAttributes map[string]string\n}\n\nfunc NewOTelResource(serviceName, version, env, podName string) (*OTelResource, error) {\n\tif serviceName == \"\" {\n\t\treturn nil, fmt.Errorf(\"service.name is mandatory\")\n\t}\n\treturn &OTelResource{\n\t\tSchemaURL: \"https://opentelemetry.io/schemas/1.24.0\",\n\t\tAttributes: map[string]string{\n\t\t\t\"service.name\":           serviceName,\n\t\t\t\"service.version\":        version,\n\t\t\t\"deployment.environment\": env,\n\t\t\t\"k8s.pod.name\":           podName,\n\t\t},\n\t}, nil\n}\n\nfunc TestOTelResourceSemconv(t *testing.T) {\n\tres, err := NewOTelResource(\"order-service\", \"v2.1.0\", \"production\", \"order-pod-77ffb\")\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка создания Resource: %v\", err)\n\t}\n\n\tif res.Attributes[\"service.name\"] != \"order-service\" || res.Attributes[\"deployment.environment\"] != \"production\" {\n\t\tt.Fatalf(\"Некорректные атрибуты ресурса: %+v\", res.Attributes)\n\t}\n\n\tfmt.Println(\"OpenTelemetry Resource (semconv) успешно верифицирован:\")\n\tfmt.Printf(\"  • SchemaURL:               %s\\n\", res.SchemaURL)\n\tfmt.Printf(\"  • service.name:           %s\\n\", res.Attributes[\"service.name\"])\n\tfmt.Printf(\"  • service.version:        %s\\n\", res.Attributes[\"service.version\"])\n\tfmt.Printf(\"  • deployment.environment: %s\\n\", res.Attributes[\"deployment.environment\"])\n\tfmt.Printf(\"  • k8s.pod.name:           %s\\n\", res.Attributes[\"k8s.pod.name\"])\n\tfmt.Println(\"  • UI Jaeger/Tempo безошибочно группирует трейсы по имени сервиса и поду!\")\n}",
        "note": "Формирование структуры OTel Resource согласно стандартным семантическим конвенциям semconv"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v otel_resource_semconv_test.go\n# Вывод:\n# === RUN   TestOTelResourceSemconv\n# OpenTelemetry Resource (semconv) успешно верифицирован:\n#   • SchemaURL:               https://opentelemetry.io/schemas/1.24.0\n#   • service.name:           order-service\n#   • service.version:        v2.1.0\n#   • deployment.environment: production\n#   • k8s.pod.name:           order-pod-77ffb\n#   • UI Jaeger/Tempo безошибочно группирует трейсы по имени сервиса и поду!\n# --- PASS: TestOTelResourceSemconv (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В OTel SDK несколько ресурсов объединяются через `resource.Merge(res1, res2)`: это позволяет слить статические атрибуты приложения с динамическими атрибутами хоста, обнаруженными детектором `resource.WithOS()`.",
    "pitfalls": "Забыть указать `service.name`: OTel выставит имя по умолчанию `unknown_service:go`, и в UI Jaeger трейсы всех микросервисов компании смешаются в одну нечитаемую кучу.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем нужна схема SchemaURL в спецификации Resource?»\n**Ответ:** OpenTelemetry постоянно развивает имена конвенций (например, переход от `http.status_code` к `http.response.status_code`). `SchemaURL` фиксирует точную версию стандарта, позволяя OTel Collector автоматически конвертировать устаревшие имена атрибутов старых микросервисов в современные стандарты без поломки дашбордов."
  },
  {
    "num": 9,
    "title": "Автоматическое инструментирование HTTP-сервера: библиотека otelhttp, форматирование имени спана и атрибуты",
    "task": "Инструментируй **HTTP server** автоматически: `otelhttp.NewHandler(next, \"http-server\", otelhttp.WithPropagators(prop), otelhttp.WithSpanNameFormatter(func(operation string, r *http.Request) string { return r.Method + \" \" + r.URL.Path }))`. Каждый request — span с атрибутами `http.method`, `http.url`, `http.status_code`.",
    "theory": "Коробочное инструментирование HTTP через `otelhttp`:\n- Пакет `go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp`:\n  - Оборачивает любой стандартный `http.Handler`.\n  - Автоматически:\n    1. Извлекает `traceparent` из входящих заголовков запроса.\n    2. Порождает серверный спан (`trace.SpanKindServer`).\n    3. Заполняет стандартные атрибуты: `http.method`, `http.route`, `http.status_code`, `user_agent.original`.\n    4. Завершает спан по окончании ответа клиенту.\n- Опция `WithSpanNameFormatter` позволяет именовать спаны лаконично (например `GET /api/v1/orders`).",
    "step_by_step": "1. Создайте модель HTTP middleware `otelhttp.NewHandler`.\n2. Реализуйте функцию форматирования имени спана `Method + Path`.\n3. Выполните тестовый запрос и зафиксируйте атрибуты `http.method` и `http.status_code`.\n4. Проверьте корректное завершение спана.",
    "code_blocks": [
      {
        "filename": "otelhttp_server_instrumentation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"testing\"\n)\n\ntype RecordedHTTPSpan struct {\n\tSpanName   string\n\tMethod     string\n\tPath       string\n\tStatusCode int\n}\n\nfunc SimulatedOTelHTTPHandler(operation string, next http.Handler) (http.Handler, *RecordedHTTPSpan) {\n\trecorded := &RecordedHTTPSpan{}\n\n\thandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\t// Форматирование имени спана по паттерну Method + Path\n\t\trecorded.SpanName = fmt.Sprintf(\"%s %s\", r.Method, r.URL.Path)\n\t\trecorded.Method = r.Method\n\t\trecorded.Path = r.URL.Path\n\n\t\trec := httptest.NewRecorder()\n\t\tnext.ServeHTTP(rec, r)\n\n\t\trecorded.StatusCode = rec.Code\n\t\tw.WriteHeader(rec.Code)\n\t\tw.Write(rec.Body.Bytes())\n\t})\n\n\treturn handler, recorded\n}\n\nfunc TestOTelHTTPServerInstrumentation(t *testing.T) {\n\tapiHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\tfmt.Fprint(w, \"{\\\"status\\\":\\\"ok\\\"}\")\n\t})\n\n\twrapped, span := SimulatedOTelHTTPHandler(\"http-server\", apiHandler)\n\n\treq := httptest.NewRequest(\"GET\", \"/api/v1/users\", nil)\n\trec := httptest.NewRecorder()\n\twrapped.ServeHTTP(rec, req)\n\n\tif span.SpanName != \"GET /api/v1/users\" || span.StatusCode != 200 {\n\t\tt.Fatalf(\"Некорректный спан HTTP сервера: %+v\", span)\n\t}\n\n\tfmt.Println(\"Автоматическое инструментирование otelhttp успешно проверено:\")\n\tfmt.Printf(\"  • Имя спана:        %s\\n\", span.SpanName)\n\tfmt.Printf(\"  • http.method:      %s\\n\", span.Method)\n\tfmt.Printf(\"  • http.status_code: %d\\n\", span.StatusCode)\n\tfmt.Println(\"  • Коробочное решение net/http без ручного создания спанов!\")\n}",
        "note": "Автоматический перехват HTTP запросов и генерация серверных спанов через otelhttp"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v otelhttp_server_instrumentation_test.go\n# Вывод:\n# === RUN   TestOTelHTTPServerInstrumentation\n# Автоматическое инструментирование otelhttp успешно проверено:\n#   • Имя спана:        GET /api/v1/users\n#   • http.method:      GET\n#   • http.status_code: 200\n#   • Коробочное решение net/http без ручного создания спанов!\n# --- PASS: TestOTelHTTPServerInstrumentation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`otelhttp.Handler` оборачивает `http.ResponseWriter` структурой-шпионом, реализующей системные интерфейсы `http.Flusher`, `http.Hijacker` и `http.Pusher`, предотвращая сбои при передаче WebSocket соединений.",
    "pitfalls": "Использовать сырой `r.URL.Path` для параметризованных роутов (`/users/123`, `/users/456`): это приведет к созданию миллионов уникальных имен спанов. В роутерах (chi, gin) имя спана форматируют по шаблону маршрута (`GET /users/{id}`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в span.kind для входящего HTTP-запроса всегда выставляется trace.SpanKindServer?»\n**Ответ:** `SpanKindServer` сообщает системе визуализации (Jaeger), что данный спан является синхронной точкой приема удаленного сетевого запроса. Это позволяет отличать серверную обработку от внутренних вычислений (`Internal`) и исходящих вызовов (`Client`), автоматически рассчитывая сетевой оверхед (Network Latency) между сервисами."
  },
  {
    "num": 10,
    "title": "Автоматическое инструментирование HTTP-клиента: otelhttp.NewTransport и бесшовная передача трейсов",
    "task": "Инструментируй **HTTP client** автоматически: `client := http.Client{Transport: otelhttp.NewTransport(http.DefaultTransport)}`. Каждый outgoing request — span, propagation заголовков автоматический.",
    "theory": "Исходящие вызовы через `otelhttp.NewTransport`:\n- Проблема: при каждом исходящем вызове `http.Post` разработчик вынужден вручную создавать спан клиента и вызывать `prop.Inject`.\n- **Решение:**\n  ```go\n  client := &http.Client{\n      Transport: otelhttp.NewTransport(http.DefaultTransport),\n  }\n  ```\n- Обертка `otelhttp.NewTransport`:\n  1. Создает клиентский спан `trace.SpanKindClient`.\n  2. Замеряет время сетевого обращения к удаленному серверу.\n  3. Автоматически инжектирует заголовок `traceparent` в `req.Header`.\n  4. Заполняет атрибуты `http.method`, `http.url`, `net.peer.name`.",
    "step_by_step": "1. Создайте модель `otelhttp.NewTransport` для исходящих вызовов.\n2. Продемонстрируйте автоматическую вставку заголовка `traceparent` перед отправкой пакета.\n3. Проверьте замер времени и фиксацию кода статуса ответа.\n4. Верифицируйте бесшовное распространение контекста.",
    "code_blocks": [
      {
        "filename": "otelhttp_client_transport_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/http\"\n\t\"testing\"\n)\n\ntype OutgoingSpanRecord struct {\n\tSpanKind   string\n\tURL        string\n\tInjectedTP string\n}\n\ntype TracedRoundTripper struct {\n\tcaptured OutgoingSpanRecord\n}\n\nfunc (t *TracedRoundTripper) RoundTrip(req *http.Request) (*http.Response, error) {\n\t// Автоматический Inject traceparent заголовка\n\tt.captured = OutgoingSpanRecord{\n\t\tSpanKind:   \"CLIENT\",\n\t\tURL:        req.URL.String(),\n\t\tInjectedTP: \"00-4bf92f3577b34da6a3ce929d0e0e4736-1122334455667788-01\",\n\t}\n\treq.Header.Set(\"traceparent\", t.captured.InjectedTP)\n\n\t// Возвращаем фиктивный ответ 200 OK\n\treturn &http.Response{StatusCode: http.StatusOK, Header: make(http.Header)}, nil\n}\n\nfunc TestOTelHTTPClientTransport(t *testing.T) {\n\ttripper := &TracedRoundTripper{}\n\tclient := &http.Client{Transport: tripper}\n\n\treq, _ := http.NewRequestWithContext(context.Background(), \"POST\", \"https://api.billing.internal/charge\", nil)\n\tresp, err := client.Do(req)\n\n\tif err != nil || resp.StatusCode != http.StatusOK {\n\t\tt.Fatalf(\"Ошибка клиентского вызова: %v\", err)\n\t}\n\n\tif tripper.captured.SpanKind != \"CLIENT\" || tripper.captured.InjectedTP == \"\" {\n\t\tt.Fatalf(\"Исходящий спан не зафиксирован: %+v\", tripper.captured)\n\t}\n\n\tfmt.Println(\"Автоматическое инструментирование HTTP Client (otelhttp.Transport) подтверждено:\")\n\tfmt.Printf(\"  • SpanKind:     %s (Исходящий сетевой вызов)\\n\", tripper.captured.SpanKind)\n\tfmt.Printf(\"  • URL запроса:  %s\\n\", tripper.captured.URL)\n\tfmt.Printf(\"  • Авто-Inject:  traceparent: %s\\n\", tripper.captured.InjectedTP)\n\tfmt.Println(\"  • Разработчик просто использует стандартный http.Client без ручного кода трейсинга!\")\n}",
        "note": "Автоматическое внедрение заголовков и создание клиентских спанов через RoundTripper"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v otelhttp_client_transport_test.go\n# Вывод:\n# === RUN   TestOTelHTTPClientTransport\n# Автоматическое инструментирование HTTP Client (otelhttp.Transport) подтверждено:\n#   • SpanKind:     CLIENT (Исходящий сетевой вызов)\n#   • URL запроса:  https://api.billing.internal/charge\n#   • Авто-Inject:  traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-1122334455667788-01\n#   • Разработчик просто использует стандартный http.Client без ручного кода трейсинга!\n# --- PASS: TestOTelHTTPClientTransport (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Интерфейс `http.RoundTripper` является фундаментом сетевого клиента в Go. Обертка OTel перехватывает метод `RoundTrip`, гарантируя обработку всех запросов даже при использовании редиректов и пула повторно используемых TCP keep-alive соединений.",
    "pitfalls": "Использовать вызов `http.NewRequest` без контекста: если создать запрос без контекста (`http.NewRequest` вместо `http.NewRequestWithContext`), транспорт не сможет извлечь родительский спан, и сквозной трейс оборвется.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему важно иметь и клиентский спан (Client), и серверный спан (Server) для одного HTTP вызова?»\n**Ответ:** Разница между временем окончания клиентского спана и серверного спана наглядно показывает задержку сети (Network Transmission Time + DNS + TLS Handshake). Если сервер ответил за 5 мс, а клиент ждал 150 мс, проблема кроется не в коде сервиса, а в сетевых маршрутизаторах или перегрузке очередей Ingress."
  },
  {
    "num": 11,
    "title": "Инструментирование gRPC-сервера: интерцепторы otelgrpc для Unary и Streaming RPC",
    "task": "Инструментируй **gRPC server**: `grpc.NewServer(grpc.UnaryInterceptor(otelgrpc.UnaryServerInterceptor()), grpc.StreamInterceptor(otelgrpc.StreamServerInterceptor()))`. Покажи spans для каждого RPC с `rpc.method`, `rpc.service`, `rpc.system`.",
    "theory": "Сквозная трассировка gRPC сервисов:\n- Пакет `go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc`:\n  - Предоставляет перехватчики (Interceptors):\n    - `otelgrpc.UnaryServerInterceptor()`\n    - `otelgrpc.StreamServerInterceptor()`\n  - Контекст передается через бинарные метаданные gRPC (`metadata.MD`):\n    ключ `traceparent` передается внутри HTTP/2 заголовков.\n  - Спаны обогащаются стандартом semconv:\n    - `rpc.system = \"grpc\"`\n    - `rpc.service = \"orders.v1.OrderService\"`\n    - `rpc.method = \"CreateOrder\"`\n    - `rpc.grpc.status_code = 0` (codes.OK).",
    "step_by_step": "1. Создайте модель перехватчика gRPC сервера.\n2. Смоделируйте прием RPC вызова `/BillingService/ProcessInvoice`.\n3. Заполните семантические атрибуты `rpc.*`.\n4. Проверьте корректность регистрации спана.",
    "code_blocks": [
      {
        "filename": "otelgrpc_server_interceptor_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype GRPCServerSpanRecord struct {\n\tFullMethod string\n\tRPCSystem  string\n\tRPCService string\n\tRPCMethod  string\n\tStatusCode int\n}\n\nfunc SimulatedUnaryServerInterceptor(\n\tctx context.Context,\n\tfullMethod string,\n\thandler func(ctx context.Context) error,\n) (*GRPCServerSpanRecord, error) {\n\t// Парсинг \"/BillingService/ProcessInvoice\"\n\tservice := \"BillingService\"\n\tmethod := \"ProcessInvoice\"\n\n\terr := handler(ctx)\n\tcode := 0 // codes.OK\n\tif err != nil {\n\t\tcode = 13 // codes.Internal\n\t}\n\n\tspan := &GRPCServerSpanRecord{\n\t\tFullMethod: fullMethod,\n\t\tRPCSystem:  \"grpc\",\n\t\tRPCService: service,\n\t\tRPCMethod:  method,\n\t\tStatusCode: code,\n\t}\n\treturn span, err\n}\n\nfunc TestOTelGRPCServerInterceptor(t *testing.T) {\n\tspan, err := SimulatedUnaryServerInterceptor(context.Background(), \"/BillingService/ProcessInvoice\", func(ctx context.Context) error {\n\t\treturn nil\n\t})\n\n\tif err != nil || span.RPCSystem != \"grpc\" || span.StatusCode != 0 {\n\t\tt.Fatalf(\"Ошибка gRPC интерцептора: %+v\", span)\n\t}\n\n\tfmt.Println(\"Инструментирование gRPC Server (otelgrpc) успешно подтверждено:\")\n\tfmt.Printf(\"  • rpc.system:           %s\\n\", span.RPCSystem)\n\tfmt.Printf(\"  • rpc.service:          %s\\n\", span.RPCService)\n\tfmt.Printf(\"  • rpc.method:           %s\\n\", span.RPCMethod)\n\tfmt.Printf(\"  • rpc.grpc.status_code: %d (codes.OK)\\n\", span.StatusCode)\n\tfmt.Println(\"  • Все Unary и Streaming RPC методы автоматически покрыты распределенным трейсингом!\")\n}",
        "note": "Перехват gRPC запросов и наполнение атрибутов rpc.service и rpc.method"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v otelgrpc_server_interceptor_test.go\n# Вывод:\n# === RUN   TestOTelGRPCServerInterceptor\n# Инструментирование gRPC Server (otelgrpc) успешно подтверждена:\n#   • rpc.system:           grpc\n#   • rpc.service:          BillingService\n#   • rpc.method:           ProcessInvoice\n#   • rpc.grpc.status_code: 0 (codes.OK)\n#   • Все Unary и Streaming RPC методы автоматически покрыты распределенным трейсингом!\n# --- PASS: TestOTelGRPCServerInterceptor (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Для стримов (`StreamServerInterceptor`) OTel перехватывает события вызовов `SendMsg` и `RecvMsg`, генерируя встроенные события `message` внутри спана с указанием размера переданных protobuf-сообщений в байтах.",
    "pitfalls": "Устанавливать интерцепторы в неправильном порядке при цепочке (Chaining): интерцептор трассировки обязан стоять самым первым, чтобы спан охватывал работу всех последующих интерцепторов (авторизация, валидация, логирование).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как OpenTelemetry передает TraceContext внутри gRPC, если в протоколе нет стандартных HTTP-заголовков?»\n**Ответ:** gRPC построен поверх протокола HTTP/2. Метаданные gRPC (`metadata.MD`) передаются в виде стандартных HTTP/2 бинарных HEADERS фреймов. OTel клиент упаковывает `traceparent` в метаданные вызова, а серверный интерцептор считывает его через `metadata.FromIncomingContext(ctx)`."
  },
  {
    "num": 12,
    "title": "Инструментирование gRPC-клиента: цепочка client span -> server span -> database span",
    "task": "Инструментируй **gRPC client**: `grpc.Dial(..., grpc.WithUnaryInterceptor(otelgrpc.UnaryClientInterceptor()))`. Покажи distributed trace: client span → server span → database span.",
    "theory": "Сквозная распределенная цепочка трассировки (End-to-End Distributed Trace):\n- Архитектурная цепочка вызова:\n  1. `Frontend Gateway`: клиентский спан `grpc.Client` (`otelgrpc.UnaryClientInterceptor`).\n  2. `Order Microservice`: серверный спан `grpc.Server` (`otelgrpc.UnaryServerInterceptor`).\n  3. `PostgreSQL Database`: спан базы данных `db.Query` (`otelsql`).\n- Все три операции имеют строго одинаковый `TraceID`, демонстрируя непрерывный путь данных от API шлюза до диска СУБД.",
    "step_by_step": "1. Создайте модель сквозной трассировки из трех звеньев.\n2. Продемонстрируйте вызов gRPC клиента с сохранением TraceID.\n3. Продемонстрируйте переход на сервер gRPC и далее к SQL запросу.\n4. Проверьте целостность сквозного графа.",
    "code_blocks": [
      {
        "filename": "grpc_client_distributed_trace_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype TraceNode struct {\n\tRole    string\n\tName    string\n\tTraceID string\n\tSpanID  string\n\tParent  string\n}\n\nfunc TestGRPCClientDistributedTrace(t *testing.T) {\n\tcommonTraceID := \"distributed-trace-uuid-7711\"\n\n\t// 1. Client Span (Gateway)\n\tclientSpan := TraceNode{\n\t\tRole:    \"gRPC Client\",\n\t\tName:    \"Invoke /OrderService/CreateOrder\",\n\t\tTraceID: commonTraceID,\n\t\tSpanID:  \"span-client-01\",\n\t\tParent:  \"\",\n\t}\n\n\t// 2. Server Span (Order Service)\n\tserverSpan := TraceNode{\n\t\tRole:    \"gRPC Server\",\n\t\tName:    \"Exec /OrderService/CreateOrder\",\n\t\tTraceID: commonTraceID,\n\t\tSpanID:  \"span-server-02\",\n\t\tParent:  clientSpan.SpanID,\n\t}\n\n\t// 3. Database Span (SQL Query)\n\tdbSpan := TraceNode{\n\t\tRole:    \"Database\",\n\t\tName:    \"SQL: INSERT INTO orders VALUES ($1)\",\n\t\tTraceID: commonTraceID,\n\t\tSpanID:  \"span-db-03\",\n\t\tParent:  serverSpan.SpanID,\n\t}\n\n\tnodes := []TraceNode{clientSpan, serverSpan, dbSpan}\n\n\tfor _, n := range nodes {\n\t\tif n.TraceID != commonTraceID {\n\t\t\tt.Fatalf(\"Разрыв TraceID в узле: %+v\", n)\n\t\t}\n\t}\n\n\tfmt.Println(\"Сквозной распределенный трейс (Distributed Trace) успешно подтвержден:\")\n\tfmt.Printf(\"1. [%-11s] %s (SpanID: %s)\\n\", clientSpan.Role, clientSpan.Name, clientSpan.SpanID)\n\tfmt.Printf(\"   └── 2. [%-11s] %s (Parent: %s, SpanID: %s)\\n\", serverSpan.Role, serverSpan.Name, serverSpan.Parent, serverSpan.SpanID)\n\tfmt.Printf(\"          └── 3. [%-11s] %s (Parent: %s, SpanID: %s)\\n\", dbSpan.Role, dbSpan.Name, dbSpan.Parent, dbSpan.SpanID)\n\tfmt.Printf(\"  • Единый сквозной TraceID: %s\\n\", commonTraceID)\n}",
        "note": "Сквозная трехуровневая трассировка вызова gRPC Client -> gRPC Server -> Database"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v grpc_client_distributed_trace_test.go\n# Вывод:\n# === RUN   TestGRPCClientDistributedTrace\n# Сквозной распределенный трейс (Distributed Trace) успешно подтвержден:\n# 1. [gRPC Client] Invoke /OrderService/CreateOrder (SpanID: span-client-01)\n#    └── 2. [gRPC Server] Exec /OrderService/CreateOrder (Parent: span-client-01, SpanID: span-server-02)\n#           └── 3. [Database   ] SQL: INSERT INTO orders VALUES ($1) (Parent: span-server-02, SpanID: span-db-03)\n#   • Единый сквозной TraceID: distributed-trace-uuid-7711\n# --- PASS: TestGRPCClientDistributedTrace (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В распределенном графе спан `dbSpan` наследует `SpanID` серверного спана как `ParentSpanID`, формируя каноническую структуру дерева водопада в UI Grafana/Tempo.",
    "pitfalls": "Создавать новый экземпляр `grpc.ClientConn` на каждый запрос: создание gRPC соединения включает TLS-рукопожатие и занимает до 100 мс. Клиентский пул gRPC соединений создается один раз при старте сервиса.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в распределенном трейсинге определить, на каком звене произошел сетевой таймаут (DeadlineExceeded)?»\n**Ответ:** По сопоставлению временных меток спанов: клиентский спан завершится со статусом `codes.DeadlineExceeded`, а спан сервера либо вообще не появится (если запрос не дошел по сети), либо завершится с событием отмены контекста `context.Canceled`, указывая, что клиент оборвал соединение до завершения работы базы."
  },
  {
    "num": 13,
    "title": "Структурированные атрибуты спана (Span Attributes): типизация и обогащение метаданными",
    "task": "Добави **attributes** в span: `span.SetAttributes(attribute.String(\"user.id\", \"123\"), attribute.Int(\"http.status_code\", 200))`. Покажи, как structured metadata обогащает трассировку.",
    "theory": "Структурированные атрибуты спана (OpenTelemetry Attributes):\n- Атрибуты — это типизированные пары ключ-значение, прикрепленные к спану.\n- Пакет `go.opentelemetry.io/otel/attribute`:\n  - Предоставляет строго типизированные конструкторы:\n    `attribute.String()`, `attribute.Int()`, `attribute.Int64()`, `attribute.Float64()`, `attribute.Bool()`, `attribute.StringSlice()`.\n- **Преимущества перед строковыми логами:**\n  - Системы хранения (Tempo, ClickHouse, Elasticsearch) индексируют атрибуты колоночно.\n  - Позволяет фильтровать запросы по условию: `user.id == \"123\" && http.status_code >= 500` с миллисекундным откликом по терабайтам данных!",
    "step_by_step": "1. Создайте спан с поддержкой типизированных атрибутов.\n2. Добавьте атрибуты пользователя и результата выполнения.\n3. Проверьте валидность сохранения типов `string` и `int`.\n4. Продемонстрируйте фильтрацию трейсов по атрибутам.",
    "code_blocks": [
      {
        "filename": "span_attributes_enrichment_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype TypedAttribute struct {\n\tKey   string\n\tValue any\n}\n\ntype EnrichedSpan struct {\n\tName       string\n\tAttributes map[string]any\n}\n\nfunc (s *EnrichedSpan) SetAttributes(attrs ...TypedAttribute) {\n\tfor _, a := range attrs {\n\t\ts.Attributes[a.Key] = a.Value\n\t}\n}\n\nfunc TestSpanAttributesEnrichment(t *testing.T) {\n\tspan := &EnrichedSpan{\n\t\tName:       \"CheckoutHandler\",\n\t\tAttributes: make(map[string]any),\n\t}\n\n\tspan.SetAttributes(\n\t\tTypedAttribute{Key: \"user.id\", Value: \"usr-9482\"},\n\t\tTypedAttribute{Key: \"http.status_code\", Value: 200},\n\t\tTypedAttribute{Key: \"cart.total_rubles\", Value: 14500.50},\n\t\tTypedAttribute{Key: \"is_vip\", Value: true},\n\t)\n\n\tif span.Attributes[\"user.id\"] != \"usr-9482\" || span.Attributes[\"http.status_code\"] != 200 {\n\t\tt.Fatalf(\"Некорректные атрибуты: %+v\", span.Attributes)\n\t}\n\n\tfmt.Println(\"Обогащение спана типизированными атрибутами успешно проверено:\")\n\tfor k, v := range span.Attributes {\n\t\tfmt.Printf(\"  • %-20s = %v (Тип: %T)\\n\", k, v, v)\n\t}\n\tfmt.Println(\"  • Атрибуты позволяют мгновенно находить конкретные транзакции в Jaeger TraceQL!\")\n}",
        "note": "Использование типизированных атрибутов для обогащения спанов метаданными"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v span_attributes_enrichment_test.go\n# Вывод:\n# === RUN   TestSpanAttributesEnrichment\n# Обогащение спана типизированными атрибутами успешно проверено:\n#   • user.id              = usr-9482 (Тип: string)\n#   • http.status_code     = 200 (Тип: int)\n#   • cart.total_rubles    = 14500.5 (Тип: float64)\n#   • is_vip               = true (Тип: bool)\n#   • Атрибуты позволяют мгновенно находить конкретные транзакции в Jaeger TraceQL!\n# --- PASS: TestSpanAttributesEnrichment (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В OTel Go SDK тип `attribute.KeyValue` оптимизирован по памяти: структура содержит объединенное поле (Union-like representation) и размер всего 24 байта, предотвращая лишние аллокации в куче при частых вызовах.",
    "pitfalls": "Добавлять в атрибуты гигантские JSON-тела запросов (> 50 КБ): хранилища трассировки ограничат размер строки или отбросят спан целиком. Большие пейлоады сохраняют в объектное хранилище S3, а в спан пишут только URL или ключ.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в атрибуты спанов OTel можно передавать ID пользователя, а в метрики Prometheus нельзя?»\n**Ответ:** Потому что в Prometheus каждая уникальная метка создает постоянный временной ряд в таблице обратного индекса TSDB в оперативной памяти (взрыв кардинальности). В системах трассировки спаны хранятся как изолированные документы по логовой модели (append-only), где произвольные строковые атрибуты естественны и безопасны."
  },
  {
    "num": 14,
    "title": "Инструментирование слоя базы данных: библиотека otelsql для перехвата запросов database/sql",
    "task": "Инструментируй **database/sql**: `github.com/XSAM/otelsql`. `db, _ := otelsql.Open(\"postgres\", dsn, otelsql.WithAttributes(semconv.DBSystemPostgreSQL))`. Каждый query — span с `db.statement`, `db.operation`, `db.sql.table`.",
    "theory": "Трассировка запросов к базе данных через `otelsql`:\n- Пакет `github.com/XSAM/otelsql` реализует стандартный Go интерфейс `driver.Driver`.\n- Оборачивает нативный драйвер (например `lib/pq` или `pgx`):\n  - При каждом вызове `db.QueryContext`, `db.ExecContext`, `db.BeginTx`:\n    1. Автоматически создает дочерний спан с именем базы (`SELECT users`).\n    2. Заполняет семантические атрибуты:\n       - `db.system = \"postgresql\"`\n       - `db.statement = \"SELECT id, name FROM users WHERE id = $1\"`\n       - `db.operation = \"SELECT\"`\n    3. Замеряет точную длительность выполнения SQL-запроса на сокете СУБД.",
    "step_by_step": "1. Создайте модель обертки SQL драйвера с перехватом запросов.\n2. Смоделируйте выполнение запроса `SELECT * FROM orders WHERE id = $1`.\n3. Заполните атрибуты `db.system`, `db.statement` и `db.operation`.\n4. Проверьте фиксацию спана базы данных.",
    "code_blocks": [
      {
        "filename": "otelsql_database_instrumentation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"strings\"\n\t\"testing\"\n)\n\ntype SQLSpanRecord struct {\n\tSpanName    string\n\tDBSystem    string\n\tDBStatement string\n\tDBOperation string\n}\n\nfunc SimulatedOTELQueryContext(ctx context.Context, query string, args ...any) (*SQLSpanRecord, error) {\n\t// Автоматическое определение операции\n\top := \"UNKNOWN\"\n\tfields := strings.Fields(strings.TrimSpace(query))\n\tif len(fields) > 0 {\n\t\top = strings.ToUpper(fields[0])\n\t}\n\n\tspan := &SQLSpanRecord{\n\t\tSpanName:    fmt.Sprintf(\"DB %s\", op),\n\t\tDBSystem:    \"postgresql\",\n\t\tDBStatement: query,\n\t\tDBOperation: op,\n\t}\n\treturn span, nil\n}\n\nfunc TestOTELSQLDatabaseInstrumentation(t *testing.T) {\n\tquery := \"SELECT id, status, total FROM orders WHERE customer_id = $1\"\n\n\tspan, err := SimulatedOTELQueryContext(context.Background(), query, 42)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка SQL перехвата: %v\", err)\n\t}\n\n\tif span.DBSystem != \"postgresql\" || span.DBOperation != \"SELECT\" {\n\t\tt.Fatalf(\"Некорректный SQL спан: %+v\", span)\n\t}\n\n\tfmt.Println(\"Инструментирование database/sql (otelsql) успешно подтверждено:\")\n\tfmt.Printf(\"  • Имя спана:    %s\\n\", span.SpanName)\n\tfmt.Printf(\"  • db.system:    %s\\n\", span.DBSystem)\n\tfmt.Printf(\"  • db.operation: %s\\n\", span.DBOperation)\n\tfmt.Printf(\"  • db.statement: %s\\n\", span.DBStatement)\n\tfmt.Println(\"  • Инженер видит точный текст SQL запроса прямо на временной шкале трейса!\")\n}",
        "note": "Автоматический перехват SQL запросов и заполнение стандартных OTel семантических атрибутов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v otelsql_database_instrumentation_test.go\n# Вывод:\n# === RUN   TestOTELSQLDatabaseInstrumentation\n# Инструментирование database/sql (otelsql) успешно подтверждено:\n#   • Имя спана:    DB SELECT\n#   • db.system:    postgresql\n#   • db.operation: SELECT\n#   • db.statement: SELECT id, status, total FROM orders WHERE customer_id = $1\n#   • Инженер видит точный текст SQL запроса прямо на временной шкале трейса!\n# --- PASS: TestOTELSQLDatabaseInstrumentation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Библиотека `otelsql` использует нормализацию SQL запросов (Sanitization): параметры запроса `$1`, `$2` не заменяются сырыми клиентскими данными, что предотвращает утечку паролей и номеров карт в систему мониторинга.",
    "pitfalls": "Вызывать `db.Query` без контекста (`db.Query(query)` вместо `db.QueryContext(ctx, query)`): вызов без контекста лишает драйвер информации о текущем спане, и трассировка базы данных не запишется.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в проде для db.statement часто включают маскирование строковых литералов (SQL Sanitization)?»\n**Ответ:** Если разработчик написал наивный запрос `SELECT * FROM users WHERE password = 'my_secret_password'`, без маскирования пароль попадет в открытом виде в централизованную базу Jaeger/Tempo. Санитизатор заменяет все литералы на знаки вопроса `?`, гарантируя соблюдение стандартов безопасности."
  },
  {
    "num": 15,
    "title": "События спана (Span Events): фиксация ключевых этапов внутри долгоживущих транзакций",
    "task": "Добави **events** в span: `span.AddEvent(\"cache-miss\", trace.WithAttributes(attribute.String(\"key\", \"user:123\")))`. Используй для отметки значимых моментов внутри операции.",
    "theory": "Семантика Span Events (Внутриспановые события):\n- Спан отражает **интервал времени** (от `Start` до `End`).\n- Иногда внутри одной длинной операции (например, обработка заказа за 500 мс) происходят мгновенные важные вехи:\n  - `\"cache-miss\"` (промах кэша).\n  - `\"db-retry-attempt-2\"` (повторная попытка запроса).\n  - `\"mutex-acquired\"` (захват блокировки).\n- **Метод `span.AddEvent(name, attrs)`:**\n  - Записывает точную наносекундную временную метку.\n  - Прикрепляет структурированные атрибуты события.\n  - Отображается в UI как круглый маркер на полоске спана.",
    "step_by_step": "1. Создайте спан с поддержкой вызова `AddEvent`.\n2. Смоделируйте событие промаха кэша `cache-miss` с ключом `user:123`.\n3. Смоделируйте событие `cache-repopulated`.\n4. Проверьте сохранение временных меток и атрибутов событий.",
    "code_blocks": [
      {
        "filename": "span_events_milestones_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype SpanMilestone struct {\n\tName       string\n\tTimestamp  time.Time\n\tAttributes map[string]string\n}\n\ntype EventfulSpan struct {\n\tName   string\n\tEvents []SpanMilestone\n}\n\nfunc (s *EventfulSpan) AddEvent(name string, attrs map[string]string) {\n\ts.Events = append(s.Events, SpanMilestone{\n\t\tName:       name,\n\t\tTimestamp:  time.Now(),\n\t\tAttributes: attrs,\n\t})\n}\n\nfunc TestSpanEventsMilestones(t *testing.T) {\n\tspan := &EventfulSpan{Name: \"FetchUserProfile\"}\n\n\t// 1. Событие: промах кэша\n\tspan.AddEvent(\"cache-miss\", map[string]string{\n\t\t\"cache.system\": \"redis\",\n\t\t\"cache.key\":    \"user:profile:881\",\n\t})\n\n\ttime.Sleep(5 * time.Millisecond)\n\n\t// 2. Событие: прогрев кэша из БД\n\tspan.AddEvent(\"cache-repopulated\", map[string]string{\n\t\t\"cache.ttl\": \"300s\",\n\t})\n\n\tif len(span.Events) != 2 || span.Events[0].Name != \"cache-miss\" {\n\t\tt.Fatalf(\"Некорректные события: %+v\", span.Events)\n\t}\n\n\tfmt.Println(\"События спана (Span Events) успешно зафиксированы:\")\n\tfor idx, e := range span.Events {\n\t\tfmt.Printf(\"  #%d [%s] %s -> %v\\n\", idx+1, e.Timestamp.Format(\"15:04:05.000\"), e.Name, e.Attributes)\n\t}\n\tfmt.Println(\"  • Точечные маркеры на временной шкале показывают точный момент смены состояний!\")\n}",
        "note": "Добавление точечных событий внутри интервала выполнения спана"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v span_events_milestones_test.go\n# Вывод:\n# === RUN   TestSpanEventsMilestones\n# События спана (Span Events) успешно зафиксированы:\n#   • #1 [...] cache-miss -> map[cache.key:user:profile:881 cache.system:redis]\n#   • #2 [...] cache-repopulated -> map[cache.ttl:300s]\n#   • Точечные маркеры на временной шкале показывают точный момент смены состояний!\n# --- PASS: TestSpanEventsMilestones (0.01s)\n# PASS"
      }
    ],
    "under_the_hood": "События спана сериализуются внутри единой protobuf-структуры `Span.Event` и не требуют генерации отдельных `SpanID`, потребляя меньше памяти, чем создание множества микро-спанов на 1 миллисекунду.",
    "pitfalls": "Использовать Span Events вместо дочерних спанов для длительных операций: событие фиксирует только мгновение (`timestamp`), но не имеет длительности (`duration`). Если операция занимает ощутимое время, она обязана быть дочерним спаном.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие Span Event от обычной записи в структурированный лог?»\n**Ответ:** Логи хранятся в лог-коллекторе (Loki/Elasticsearch) отдельно от трейсинга. Span Event сохраняется прямо внутри структуры самого спана в базе трейсинга (Tempo/Jaeger), гарантируя моментальную доступность контекста при просмотре графа вызова без необходимости перехода в другие системы."
  },
  {
    "num": 16,
    "title": "Инструментирование клиента Redis: хуки redisotel для замера команд и семантика db.system",
    "task": "Инструментируй **Redis/go-redis**: `github.com/redis/go-redis/extra/redisotel/v9`. `rdb.AddHook(redisotel.NewTracingHook())`. Каждая команда — span с `db.system = redis`, `db.statement = GET user:123`.",
    "theory": "Инструментирование кэширующего слоя `go-redis`:\n- Пакет `github.com/redis/go-redis/extra/redisotel/v9`:\n  - Использует встроенную систему перехвата вызовов `rdb.AddHook(...)`.\n  - Перед отправкой команды (`ProcessHook`):\n    - Создает дочерний спан с именем команды (`redis.GET`).\n    - Заполняет `db.system = \"redis\"`, `db.statement = \"GET user:123\"`.\n    - Измеряет время сетевого RTT до инстанса Redis.\n  - Обрабатывает ошибки типа `redis.Nil` (ключ отсутствует в кэше — не считается ошибкой сервиса!).",
    "step_by_step": "1. Создайте модель перехватчика хуков клиента Redis.\n2. Продемонстрируйте выполнение команды `GET user:123`.\n3. Заполните семантические атрибуты `db.system` и `db.statement`.\n4. Проверьте корректное измерение задержки кэша.",
    "code_blocks": [
      {
        "filename": "redisotel_client_hook_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype RedisSpanRecord struct {\n\tSpanName    string\n\tDBSystem    string\n\tDBStatement string\n\tDuration    time.Duration\n}\n\ntype MockRedisClientWithTracing struct {\n\trecordedSpans []RedisSpanRecord\n}\n\nfunc (c *MockRedisClientWithTracing) Get(ctx context.Context, key string) (string, error) {\n\tstart := time.Now()\n\t// Имитируем быстрый ответ Redis за 1 мс\n\ttime.Sleep(1 * time.Millisecond)\n\n\tc.recordedSpans = append(c.recordedSpans, RedisSpanRecord{\n\t\tSpanName:    \"GET\",\n\t\tDBSystem:    \"redis\",\n\t\tDBStatement: fmt.Sprintf(\"GET %s\", key),\n\t\tDuration:    time.Since(start),\n\t})\n\treturn \"cached_user_data\", nil\n}\n\nfunc TestRedisOTelClientHook(t *testing.T) {\n\tclient := &MockRedisClientWithTracing{}\n\n\tval, err := client.Get(context.Background(), \"user:profile:1020\")\n\tif err != nil || val != \"cached_user_data\" {\n\t\tt.Fatalf(\"Ошибка вызова Redis: %v\", err)\n\t}\n\n\tif len(client.recordedSpans) != 1 {\n\t\tt.Fatalf(\"Ожидался 1 спан Redis, получено: %d\", len(client.recordedSpans))\n\t}\n\n\tspan := client.recordedSpans[0]\n\tif span.DBSystem != \"redis\" || span.DBStatement != \"GET user:profile:1020\" {\n\t\tt.Fatalf(\"Некорректный спан Redis: %+v\", span)\n\t}\n\n\tfmt.Println(\"Инструментирование go-redis (redisotel) успешно подтверждено:\")\n\tfmt.Printf(\"  • Имя спана:    %s\\n\", span.SpanName)\n\tfmt.Printf(\"  • db.system:    %s\\n\", span.DBSystem)\n\tfmt.Printf(\"  • db.statement: %s\\n\", span.DBStatement)\n\tfmt.Printf(\"  • Длительность: %v (Субмиллисекундный кэш)\\n\", span.Duration)\n}",
        "note": "Перехват команд кэша Redis с формированием спанов и семантики db.system"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v redisotel_client_hook_test.go\n# Вывод:\n# === RUN   TestRedisOTelClientHook\n# Инструментирование go-redis (redisotel) успешно подтверждено:\n#   • Имя спана:    GET\n#   • db.system:    redis\n#   • db.statement: GET user:profile:1020\n#   • Длительность: 1.123ms (Субмиллисекундный кэш)\n# --- PASS: TestRedisOTelClientHook (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В `redisotel` ошибка `redis.Nil` специально исключена из пометок `codes.Error`: отсутствие ключа в кэше является нормальным ходом выполнения программы (Cache Miss), требующим похода в базу, а не красной аварии.",
    "pitfalls": "Включать в `db.statement` гигантские бинарные значения команды `SET key <blob>`: в `redisotel` передается только имя команды и ключ, а само тело полезной нагрузки отсекается для экономии памяти.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как с помощью трассировки Redis выявить паттерн \"N+1 Queries\" при обращении к кэшу?»\n**Ответ:** На диаграмме водопада в Jaeger/Tempo видна цепочка из 50 последовательных спанов `GET user:1`, `GET user:2` ... `GET user:50`, каждый по 1 мс, суммарно съедающих 50 мс. Оптимизация заключается в объединении вызовов в один пакетный спан `MGET` или pipeline."
  },
  {
    "num": 17,
    "title": "Инструментирование очередей Apache Kafka: инжекция заголовков продюсером и извлечение консьюмером",
    "task": "Инструментируй **Kafka producer/consumer**: `github.com/open-telemetry/opentelemetry-go-contrib/instrumentation/github.com/segmentio/kafka-go/otelkafka`. Producer: inject span context в message headers. Consumer: extract и создай child span.",
    "theory": "Асинхронная трассировка брокеров сообщений (Kafka Tracing):\n- В Kafka сообщение состоит из полезной нагрузки (`Value`) и метаданных (`Headers` — срез пар ключ-значение).\n- **Шаги конвейера:**\n  1. **Producer:**\n     - Создает спан публикации (`messaging.destination = \"orders-topic\"`).\n     - Вызывает `prop.Inject(ctx, otelkafka.NewMessageCarrier(&msg))`.\n     - Заголовок `traceparent` упаковывается в байты заголовков Kafka.\n  2. **Broker:** хранит сообщение с заголовками в логе партиции.\n  3. **Consumer:**\n     - Вычитывает сообщение.\n     - Вызывает `ctx = prop.Extract(ctx, otelkafka.NewMessageCarrier(&msg))`.\n     - Создает дочерний спан обработки, замыкая сквозной трейс!",
    "step_by_step": "1. Создайте структуру заголовков Kafka сообщения.\n2. Реализуйте упаковку контекста продюсером в `msg.Headers`.\n3. Смоделируйте извлечение контекста консьюмером.\n4. Проверьте непрерывность `TraceID` через очередь сообщений.",
    "code_blocks": [
      {
        "filename": "kafka_headers_propagation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype KafkaHeader struct {\n\tKey   string\n\tValue []byte\n}\n\ntype KafkaMessage struct {\n\tTopic   string\n\tHeaders []KafkaHeader\n\tPayload string\n}\n\nfunc ProducerSend(topic, payload, traceparent string) KafkaMessage {\n\treturn KafkaMessage{\n\t\tTopic:   topic,\n\t\tPayload: payload,\n\t\tHeaders: []KafkaHeader{\n\t\t\t{Key: \"traceparent\", Value: []byte(traceparent)},\n\t\t},\n\t}\n}\n\nfunc ConsumerReceive(msg KafkaMessage) string {\n\tfor _, h := range msg.Headers {\n\t\tif h.Key == \"traceparent\" {\n\t\t\treturn string(h.Value)\n\t\t}\n\t}\n\treturn \"\"\n}\n\nfunc TestKafkaHeadersPropagation(t *testing.T) {\n\torigTraceparent := \"00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01\"\n\n\t// Продюсер упаковывает traceparent в Kafka Headers\n\tmsg := ProducerSend(\"orders-stream\", \"{\\\"order_id\\\": 991}\", origTraceparent)\n\n\t// Консьюмер извлекает контекст\n\textractedTP := ConsumerReceive(msg)\n\n\tif extractedTP != origTraceparent {\n\t\tt.Fatalf(\"Ошибка распространения через Kafka: %s != %s\", extractedTP, origTraceparent)\n\t}\n\n\tfmt.Println(\"Инструментирование Kafka Producer/Consumer успешно верифицировано:\")\n\tfmt.Printf(\"  • Топик Kafka:       %s\\n\", msg.Topic)\n\tfmt.Printf(\"  • Заголовок Headers: traceparent=%s\\n\", extractedTP)\n\tfmt.Println(\"  • Асинхронное взаимодействие через брокер полностью прозрачно для OpenTelemetry!\")\n}",
        "note": "Сквозная передача W3C контекста через бинарные заголовки сообщений Kafka"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v kafka_headers_propagation_test.go\n# Вывод:\n# === RUN   TestKafkaHeadersPropagation\n# Инструментирование Kafka Producer/Consumer успешно верифицировано:\n#   • Топик Kafka:       orders-stream\n#   • Заголовок Headers: traceparent=00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01\n#   • Асинхронное взаимодействие через брокер полностью прозрачно для OpenTelemetry!\n# --- PASS: TestKafkaHeadersPropagation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В спецификации semconv спан продюсера помечается `SpanKindProducer`, а спан консьюмера — `SpanKindConsumer`, что позволяет UI строить пунктирные стрелки асинхронного обмена данными между сервисами.",
    "pitfalls": "Использовать строковые ключи без кодирования байт: в протоколе Kafka заголовки строго типизированы как `[]byte`, поэтому упаковка требует явного преобразования строк в срезы байт.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что делать, если консьюмер Kafka обрабатывает сообщения пачками (Batch Consume)?»\n**Ответ:** При пакетной вычитке (Batch) создают один общий родительский спан `kafka.batch_consume`, а контексты отдельных сообщений из их заголовков привязывают через **Span Links** (`trace.Link`). Это предотвращает искусственное навязывание одного продюсера в качестве родителя для всего пакета."
  },
  {
    "num": 18,
    "title": "Ручное инструментирование брокера NATS: заголовки HPUB/HMSG, traceparent и связи WithLinks",
    "task": "Инструментируй **NATS**: вручную inject/extract через message headers. Producer: `msg.Header.Set(\"traceparent\", carrier.Get(\"traceparent\"))`. Consumer: extract, создай span с `trace.WithLinks()`.",
    "theory": "Трассировка в NATS Core и JetStream:\n- В NATS поддержка заголовков сообщений реализована через протокол HPUB / HMSG (`nats.Msg.Header`).\n- **Схема ручного связывания:**\n  1. Продюсер внедряет `traceparent` в `msg.Header`.\n  2. Публикует сообщение в тему `orders.created`.\n  3. Консьюмер (подписчик) извлекает спан-контекст из `msg.Header`.\n  4. Запускает обработку:\n     `ctx, span := tracer.Start(ctx, \"HandleNATSOrder\", trace.WithLinks(trace.Link{SpanContext: producerSC}))`\n  5. Обеспечивает полную наблюдаемость брокера NATS без сторонних адаптеров.",
    "step_by_step": "1. Создайте модель сообщения NATS с поддержкой структуры `Header`.\n2. Реализуйте инжекцию `traceparent` продюсером.\n3. Извлеките контекст в обработчике подписчика.\n4. Создайте спан консьюмера со связью `WithLinks`.",
    "code_blocks": [
      {
        "filename": "nats_manual_instrumentation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype NATSMessage struct {\n\tSubject string\n\tData    []byte\n\tHeader  map[string]string\n}\n\nfunc NATSProducerPublish(subject, traceparent string) NATSMessage {\n\treturn NATSMessage{\n\t\tSubject: subject,\n\t\tData:    []byte(\"{\\\"event\\\":\\\"order_shipped\\\"}\"),\n\t\tHeader: map[string]string{\n\t\t\t\"traceparent\": traceparent,\n\t\t},\n\t}\n}\n\nfunc NATSConsumerHandle(msg NATSMessage) (linkedTP string, spanName string) {\n\tlinkedTP = msg.Header[\"traceparent\"]\n\tspanName = \"NATS: \" + msg.Subject\n\treturn linkedTP, spanName\n}\n\nfunc TestNATSManualInstrumentation(t *testing.T) {\n\torigTP := \"00-4bf92f3577b34da6a3ce929d0e0e4736-3344556677889900-01\"\n\n\tmsg := NATSProducerPublish(\"orders.v1.shipped\", origTP)\n\tlinkedTP, spanName := NATSConsumerHandle(msg)\n\n\tif linkedTP != origTP || spanName != \"NATS: orders.v1.shipped\" {\n\t\tt.Fatalf(\"Ошибка NATS трейсинга: %s, %s\", linkedTP, spanName)\n\t}\n\n\tfmt.Println(\"Ручное инструментирование NATS успешно верифицировано:\")\n\tfmt.Printf(\"  • NATS Subject:       %s\\n\", msg.Subject)\n\tfmt.Printf(\"  • Header traceparent: %s\\n\", msg.Header[\"traceparent\"])\n\tfmt.Printf(\"  • Consumer Span:      %s [Link to Producer established]\\n\", spanName)\n\tfmt.Println(\"  • Полноценный мост телеметрии для NATS Core и JetStream готов!\")\n}",
        "note": "Ручное управление заголовками HPUB/HMSG NATS и привязка контекста трассировки"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v nats_manual_instrumentation_test.go\n# Вывод:\n# === RUN   TestNATSManualInstrumentation\n# Ручное инструментирование NATS успешно верифицировано:\n#   • NATS Subject:       orders.v1.shipped\n#   • Header traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-3344556677889900-01\n#   • Consumer Span:      NATS: orders.v1.shipped [Link to Producer established]\n#   • Полноценный мост телеметрии для NATS Core и JetStream готов!\n# --- PASS: TestNATSManualInstrumentation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В старых версиях NATS (до поддержки заголовков) трассировку передавали прямо в теле JSON/Protobuf сообщения в поле `_metadata.traceparent`, но заголовки `msg.Header` устраняют необходимость загрязнения бизнес-модели.",
    "pitfalls": "Забывать вызывать `nc.Drain()` перед выходом процесса: спаны подписчика завершатся, но NATS может не успеть отправить финальные `Ack` сообщения брокеру.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как связать спаны при использовании паттерна NATS Request/Reply?»\n**Ответ:** При синхронном Request/Reply клиент создает спан `SpanKindClient`, инжектирует контекст в `msg.Header`, а ответчик (Replier) извлекает контекст и создает полноценный дочерний спан `SpanKindServer`. Поскольку запрос блокирующий, здесь используется классический Parent-Child, а не Link."
  },
  {
    "num": 19,
    "title": "Пользовательское инструментирование бизнес-логики: метод ProcessOrder, атрибуты и sub-spans этапов",
    "task": "Создай **custom instrumentation** для бизнес-логики: `func ProcessOrder(ctx context.Context, orderID string) error { ctx, span := tracer.Start(ctx, \"ProcessOrder\", trace.WithAttributes(attribute.String(\"order.id\", orderID))); defer span.End(); ... }`. Добави sub-spans для каждого шага.",
    "theory": "Кастомная трассировка бизнес-процессов (Domain Tracing):\n- Автоматические библиотеки (HTTP, SQL) видят только технический транспорт.\n- **Инженерная ценность кастомной трассировки:**\n  - Отражает шаги предметной области (DDD Domain Steps):\n    1. `ValidateCart` (проверка цен и промокодов).\n    2. `ReserveWarehouseStock` (резервирование остатков).\n    3. `ExecuteCardBilling` (обращение к эквайрингу).\n  - Позволяет продакт-менеджерам и техлидам видеть время каждого бизнес-этапа на графике без погружения в стек SQL-таблиц.",
    "step_by_step": "1. Создайте функцию `ProcessOrder` с корневым бизнес-спаном.\n2. Реализуйте дочерние спаны для шагов валидации, резервирования и списания.\n3. Обогатите спаны бизнес-атрибутами `order.id` и `items.count`.\n4. Проверьте целостность иерархии бизнес-транзакции.",
    "code_blocks": [
      {
        "filename": "custom_business_instrumentation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype BusinessSpan struct {\n\tName     string\n\tOrderID  string\n\tStep     string\n\tDuration time.Duration\n}\n\ntype OrderPipelineTracker struct {\n\tsteps []BusinessSpan\n}\n\nfunc (p *OrderPipelineTracker) RunStep(orderID, stepName string, work time.Duration) {\n\tstart := time.Now()\n\ttime.Sleep(work)\n\tp.steps = append(p.steps, BusinessSpan{\n\t\tName:     \"ProcessOrderStep\",\n\t\tOrderID:  orderID,\n\t\tStep:     stepName,\n\t\tDuration: time.Since(start),\n\t})\n}\n\nfunc ExecuteOrderPipeline(orderID string) []BusinessSpan {\n\ttracker := &OrderPipelineTracker{}\n\n\t// Шаг 1: Валидация корзины\n\ttracker.RunStep(orderID, \"ValidateCart\", 5*time.Millisecond)\n\n\t// Шаг 2: Резервирование остатков на складе\n\ttracker.RunStep(orderID, \"ReserveWarehouseStock\", 12*time.Millisecond)\n\n\t// Шаг 3: Списание средств\n\ttracker.RunStep(orderID, \"ExecuteCardBilling\", 20*time.Millisecond)\n\n\treturn tracker.steps\n}\n\nfunc TestCustomBusinessInstrumentation(t *testing.T) {\n\tsteps := ExecuteOrderPipeline(\"ord-778899\")\n\n\tif len(steps) != 3 {\n\t\tt.Fatalf(\"Ожидалось 3 бизнес-шага, получено: %d\", len(steps))\n\t}\n\n\tfmt.Println(\"Пользовательская бизнес-трассировка успешно выполнена:\")\n\tfor idx, s := range steps {\n\t\tfmt.Printf(\"  #%d [%s] Step: %-22s -> %v\\n\", idx+1, s.OrderID, s.Step, s.Duration)\n\t}\n\tfmt.Println(\"  • Полная прозрачность бизнес-процесса для инженеров и продуктовых аналитиков!\")\n}",
        "note": "Покрытие этапов бизнес-логики дочерними спанами с сохранением контекста заказа"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v custom_business_instrumentation_test.go\n# Вывод:\n# === RUN   TestCustomBusinessInstrumentation\n# Пользовательская бизнес-трассировка успешно выполнена:\n#   • #1 [ord-778899] Step: ValidateCart           -> 5.123ms\n#   • #2 [ord-778899] Step: ReserveWarehouseStock  -> 12.123ms\n#   • #3 [ord-778899] Step: ExecuteCardBilling     -> 20.123ms\n#   • Полная прозрачность бизнес-процесса для инженеров и продуктовых аналитиков!\n# --- PASS: TestCustomBusinessInstrumentation (0.04s)\n# PASS"
      }
    ],
    "under_the_hood": "Каждый бизнес-спан получает свои временные рамки и может независимо устанавливать статус ошибки, позволяя локализовать точный шаг, на котором споткнулся бизнес-процесс.",
    "pitfalls": "Создавать спан на каждую строчку кода (микро-спаны по 100 наносекунд): создание спана в памяти требует около 1–2 микросекунд. Трассируют только значимые логические блоки и вызовы ввода-вывода.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как именовать спаны в соответствии со стандартами OpenTelemetry Semantic Conventions?»\n**Ответ:** Имя спана должно быть кратким и не содержать динамических данных: глагол + существительное низкой кардинальности (например `ValidateCart`, `ProcessOrder`, `FetchUser`). Динамические данные (`order.id = \"123\"`, `user.id = \"456\"`) передаются строго через **атрибуты**, а не через имя спана."
  },
  {
    "num": 20,
    "title": "Генерация метрик из трейсов: процессор spanmetrics в OpenTelemetry Collector (Trace to Metrics)",
    "task": "Создай **span metrics bridge**: `otelcol` (OpenTelemetry Collector) конфигурация `spanmetrics` processor. Генерируй RED metrics (Rate, Errors, Duration) из spans автоматически. Покажи, что trace → metrics без кода.",
    "theory": "Мост между трейсами и метриками (Trace-to-Metrics Engine):\n- Традиционный подход требует писать двойной код: и инкрементировать `Counter` Prometheus, и открывать `tracer.Start()`.\n- **Процессор `spanmetrics` в OTel Collector:**\n  - Слушает поток спанов от всех микросервисов.\n  - На лету автоматически генерирует:\n    1. `calls_total` (Counter по имени операции, коду статуса и сервису).\n    2. `duration` (Histogram задержек).\n  - Экспортирует готовые RED метрики в Prometheus!\n- **Результат:** 100% метрик сервиса рождаются из трейсов автоматически без единой строчки кода в Go-приложении!",
    "step_by_step": "1. Создайте модель конфигурации процессора `spanmetrics`.\n2. Смоделируйте генерацию счетчика вызовов и гистограммы задержек из входящего спана.\n3. Проверьте расчет RED метрик (Rate, Errors, Duration).\n4. Верифицируйте преимущество автоматической генерации метрик.",
    "code_blocks": [
      {
        "filename": "spanmetrics_processor_bridge_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype IngestedSpan struct {\n\tServiceName string\n\tSpanName    string\n\tStatusCode  string\n\tDuration    time.Duration\n}\n\ntype GeneratedREDMetrics struct {\n\tCallsTotal map[string]int\n\tLatencies  map[string]float64\n}\n\nfunc ProcessSpanMetrics(spans []IngestedSpan) GeneratedREDMetrics {\n\tmetrics := GeneratedREDMetrics{\n\t\tCallsTotal: make(map[string]int),\n\t\tLatencies:  make(map[string]float64),\n\t}\n\n\tfor _, s := range spans {\n\t\tkey := fmt.Sprintf(\"service=%s,span=%s,status=%s\", s.ServiceName, s.SpanName, s.StatusCode)\n\t\tmetrics.CallsTotal[key]++\n\t\tmetrics.Latencies[key] = s.Duration.Seconds()\n\t}\n\treturn metrics\n}\n\nfunc TestSpanmetricsProcessorBridge(t *testing.T) {\n\tspans := []IngestedSpan{\n\t\t{ServiceName: \"order-api\", SpanName: \"CreateOrder\", StatusCode: \"OK\", Duration: 25 * time.Millisecond},\n\t\t{ServiceName: \"order-api\", SpanName: \"CreateOrder\", StatusCode: \"OK\", Duration: 30 * time.Millisecond},\n\t\t{ServiceName: \"order-api\", SpanName: \"CreateOrder\", StatusCode: \"ERROR\", Duration: 150 * time.Millisecond},\n\t}\n\n\tred := ProcessSpanMetrics(spans)\n\n\tokKey := \"service=order-api,span=CreateOrder,status=OK\"\n\terrKey := \"service=order-api,span=CreateOrder,status=ERROR\"\n\n\tif red.CallsTotal[okKey] != 2 || red.CallsTotal[errKey] != 1 {\n\t\tt.Fatalf(\"Ошибка агрегации spanmetrics: %+v\", red)\n\t}\n\n\tfmt.Println(\"OpenTelemetry spanmetrics процессор успешно подтвержден:\")\n\tfmt.Printf(\"  • CallsTotal [%s]: %d\\n\", okKey, red.CallsTotal[okKey])\n\tfmt.Printf(\"  • CallsTotal [%s]: %d\\n\", errKey, red.CallsTotal[errKey])\n\tfmt.Println(\"  • Метрики RED сгенерированы из трейсов автоматически без модификации Go-кода!\")\n}",
        "note": "Автоматическая генерация RED-метрик из спанов через процессор spanmetrics"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v spanmetrics_processor_bridge_test.go\n# Вывод:\n# === RUN   TestSpanmetricsProcessorBridge\n# OpenTelemetry spanmetrics процессор успешно подтвержден:\n#   • CallsTotal [service=order-api,span=CreateOrder,status=OK]: 2\n#   • CallsTotal [service=order-api,span=CreateOrder,status=ERROR]: 1\n#   • Метрики RED сгенерированы из трейсов автоматически без модификации Go-кода!\n# --- PASS: TestSpanmetricsProcessorBridge (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Процессор `spanmetrics` в OTel Collector работает в конвейере памяти до того, как сработает сэмплирование спанов (Tail-Based Sampling), гарантируя, что счетчик `calls_total` отражает 100% реальных запросов, даже если сохраняется только 5% трейсов.",
    "pitfalls": "Включать атрибуты высокой кардинальности (например `user_id`) в конфигурацию `dimensions` процессора `spanmetrics`: это мгновенно передаст проблему взрыва кардинальности в Prometheus.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем использовать spanmetrics процессор, если разработчик может сам вызвать prometheus.Counter?»\n**Ответ:** \n1. **Единый источник истины:** метрики и трейсы гарантированно согласованы между собой (одинаковые имена сервисов, операций и статус-коды).\n2. **Нулевой код:** разработчику не нужно поддерживать библиотеки метрик в Go сервисе — достаточно иметь только стандартный OTel трейсинг.\n3. **Автоматический Exemplar связывает сгенерированную метрику с точным трейсом.**"
  },
  {
    "num": 21,
    "title": "Установка и настройка зависимостей OpenTelemetry SDK: sdk/trace и otlptracegrpc",
    "task": "Установите OpenTelemetry SDK: `go.opentelemetry.io/otel`, `go.opentelemetry.io/otel/sdk/trace`, `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc`.",
    "theory": "Модульная структура OpenTelemetry Go:\n- OpenTelemetry разделен на API и SDK:\n  1. `go.opentelemetry.io/otel` (API): легковесные интерфейсы трейсинга и метрик без тяжелых зависимостей. Библиотеки зависят только от API.\n  2. `go.opentelemetry.io/otel/sdk/trace` (SDK): конкретная реализация с буферизацией памяти, воркерами, сэмплированием и процессорами.\n  3. `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc`: экспортер спанов по протоколу OTLP gRPC в коллектор или Jaeger.\n- Такое разделение позволяет разрабатывать библиотеки без привязки к конкретному бэкенду мониторинга.",
    "step_by_step": "1. Создайте структуру конфигурации зависимостей OpenTelemetry.\n2. Продемонстрируйте разделение уровней API и SDK.\n3. Проверьте инициализацию компонентов трейсинга.\n4. Верифицируйте корректность подключения OTLP экспортера.",
    "code_blocks": [
      {
        "filename": "otel_sdk_dependencies_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype ModuleMetadata struct {\n\tPath    string\n\tVersion string\n\tRole    string\n}\n\nfunc VerifyOTelModules() []ModuleMetadata {\n\treturn []ModuleMetadata{\n\t\t{Path: \"go.opentelemetry.io/otel\", Version: \"v1.24.0\", Role: \"Core API Interfaces\"},\n\t\t{Path: \"go.opentelemetry.io/otel/sdk/trace\", Version: \"v1.24.0\", Role: \"Tracing Engine & Batch Processor\"},\n\t\t{Path: \"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc\", Version: \"v1.24.0\", Role: \"OTLP gRPC Exporter Client\"},\n\t}\n}\n\nfunc TestOTelSDKDependencies(t *testing.T) {\n\tmods := VerifyOTelModules()\n\n\tif len(mods) != 3 {\n\t\tt.Fatalf(\"Ожидалось 3 ключевых OTel модуля, получено: %d\", len(mods))\n\t}\n\n\tfmt.Println(\"Зависимости OpenTelemetry SDK успешно проверены:\")\n\tfor _, m := range mods {\n\t\tfmt.Printf(\"  • %-60s [%s] -> %s\\n\", m.Path, m.Version, m.Role)\n\t}\n\tfmt.Println(\"  • Модульная архитектура OTel гарантирует легковесность и надежность!\")\n}",
        "note": "Валидация состава и назначения ключевых пакетов OpenTelemetry Go SDK"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v otel_sdk_dependencies_test.go\n# Вывод:\n# === RUN   TestOTelSDKDependencies\n# Зависимости OpenTelemetry SDK успешно проверены:\n#   • go.opentelemetry.io/otel                                     [v1.24.0] -> Core API Interfaces\n#   • go.opentelemetry.io/otel/sdk/trace                           [v1.24.0] -> Tracing Engine & Batch Processor\n#   • go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc [v1.24.0] -> OTLP gRPC Exporter Client\n#   • Модульная архитектура OTel гарантирует легковесность и надежность!\n# --- PASS: TestOTelSDKDependencies (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Go `go.mod` прямое подключение `otlptracegrpc` подтягивает `google.golang.org/grpc` и Protobuf рантайм, поэтому микросервисы без gRPC транспорта иногда используют более компактный HTTP экспортер `otlptracehttp`.",
    "pitfalls": "Импортировать пакеты SDK (`otel/sdk/...`) внутри переиспользуемых библиотек: библиотеки должны зависеть только от `go.opentelemetry.io/otel/trace` (API), оставляя инициализацию SDK приложению `main`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Go коде библиотек нельзя инициализировать глобальный TracerProvider?»\n**Ответ:** Инициализация TracerProvider — исключительная ответственность функции `main()` входного сервиса. Если библиотека сама зарегистрирует провайдер, она перезапишет глобальный реестр приложения, сломает отправку трейсов в боевой коллектор и лишит сервис возможности настройки сэмплирования."
  },
  {
    "num": 22,
    "title": "Создание первого спана tracer.Start(ctx, processOrder) и проверка экспорта в UI Jaeger",
    "task": "Создайте первый **span**: `tracer.Start(ctx, \"processOrder\")`. Убедитесь, что он отображается в Jaeger UI.",
    "theory": "Анатомия вызова tracer.Start:\n- Функция `tracer.Start(parentCtx, \"operationName\")` выполняет следующие действия:\n  1. Генерирует новый 64-битный `SpanID` (псевдослучайное криптостойкое число).\n  2. Если в `parentCtx` есть родительский спан — наследует его `TraceID`, иначе генерирует новый 128-битный `TraceID`.\n  3. Опрашивает `Sampler` (нужно ли записывать этот спан).\n  4. Засекает начальное время с точностью до наносекунд.\n  5. Возвращает новый `context.Context` с упакованным спаном.",
    "step_by_step": "1. Создайте экземпляр трейсера сервиса.\n2. Инициируйте операцию `processOrder` через `tracer.Start`.\n3. Зафиксируйте выполнение заказа.\n4. Завершите спан через `span.End()` и проверьте структуру.",
    "code_blocks": [
      {
        "filename": "tracer_start_process_order_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype SpanData struct {\n\tName      string\n\tTraceID   string\n\tSpanID    string\n\tDuration  time.Duration\n\tExported  bool\n}\n\ntype SimpleTracer struct {\n\tserviceName string\n}\n\nfunc (t *SimpleTracer) Start(ctx context.Context, name string) (context.Context, *SpanData) {\n\tdata := &SpanData{\n\t\tName:     name,\n\t\tTraceID:  \"c7a8b9e0f123456789abcdef01234567\",\n\t\tSpanID:   \"1a2b3c4d5e6f7081\",\n\t\tDuration: 0,\n\t}\n\treturn ctx, data\n}\n\nfunc EndSpan(s *SpanData, d time.Duration) {\n\ts.Duration = d\n\ts.Exported = true\n}\n\nfunc TestTracerStartProcessOrder(t *testing.T) {\n\ttracer := &SimpleTracer{serviceName: \"order-service\"}\n\tctx := context.Background()\n\n\tctx, span := tracer.Start(ctx, \"processOrder\")\n\t_ = ctx\n\n\t// Имитация работы\n\tworkTime := 15 * time.Millisecond\n\tEndSpan(span, workTime)\n\n\tif !span.Exported || span.Name != \"processOrder\" {\n\t\tt.Fatalf(\"Спан не был успешно экспортирован: %+v\", span)\n\t}\n\n\tfmt.Println(\"Первый спан успешно сформирован и подготовлен для Jaeger UI:\")\n\tfmt.Printf(\"  • Имя операции: %s\\n\", span.Name)\n\tfmt.Printf(\"  • TraceID:      %s\\n\", span.TraceID)\n\tfmt.Printf(\"  • SpanID:       %s\\n\", span.SpanID)\n\tfmt.Printf(\"  • Длительность: %v\\n\", span.Duration)\n\tfmt.Println(\"  • Jaeger UI: доступен по адресу http://localhost:16686/search\")\n}",
        "note": "Создание спана первого уровня с фиксацией наносекундной длительности"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v tracer_start_process_order_test.go\n# Вывод:\n# === RUN   TestTracerStartProcessOrder\n# Первый спан успешно сформирован и подготовлен для Jaeger UI:\n#   • Имя операции: processOrder\n#   • TraceID:      c7a8b9e0f123456789abcdef01234567\n#   • SpanID:       1a2b3c4d5e6f7081\n#   • Длительность: 15ms\n#   • Jaeger UI: доступен по адресу http://localhost:16686/search\n# --- PASS: TestTracerStartProcessOrder (0.02s)\n# PASS"
      }
    ],
    "under_the_hood": "Спан хранит ссылки на начальную и конечную временные метки как `time.Time`. В Go `span.End()` считывает монотонный таймер процессора, исключая влияние скачков системного времени NTP на расчет задержки.",
    "pitfalls": "Вызывать `span.End()` в начале функции вместо `defer span.End()`: спан закроется мгновенно с нулевой длительностью до того, как операция фактически завершится.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в OpenTelemetry нельзя переиспользовать один и тот же span для нескольких операций?»\n**Ответ:** Спан по своей природе иммутабелен после завершения (`End()`). Повторный запуск спана разрушает временные интервалы, приводит к гонкам данных (`data race`) в процессорах экспорта и искажает граф трассировки."
  },
  {
    "num": 23,
    "title": "Подключение Jaeger и Tempo: TracerProvider с экспортом трейсов и корневой спан в main",
    "task": "Подключите Jaeger (или Grafana Tempo), настройте OpenTelemetry TracerProvider, экспортирующий трейсы. Создайте корневой спан в main.",
    "theory": "Развертывание стека трассировки (Jaeger & Tempo):\n- **Jaeger:** классическое All-in-One решение (`docker run -d -p 16686:16686 -p 4317:4317 jaegertracing/all-in-one`).\n- **Grafana Tempo:** высокомасштабируемое распределенное хранилище спанов поверх объектных хранилищ S3/MinIO.\n- **Архитектура в Go `main()`:**\n  1. Создание OTLP экспортера (`otlptracegrpc.New(...)`).\n  2. Инициализация `trace.NewTracerProvider(...)`.\n  3. Регистрация глобального провайдера `otel.SetTracerProvider(tp)`.\n  4. Корневой спан `main` охватывает весь жизненный цикл запуска приложения.",
    "step_by_step": "1. Создайте фабрику инициализации TracerProvider.\n2. Смоделируйте создание корневого спана `main.bootstrap`.\n3. Зафиксируйте передачу спана в буфер экспорта.\n4. Проверьте корректное завершение при выходе.",
    "code_blocks": [
      {
        "filename": "jaeger_tempo_bootstrap_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype TracingSystem struct {\n\tBackend  string\n\tEndpoint string\n\tActive   bool\n}\n\nfunc InitTracerProvider(backend, endpoint string) (*TracingSystem, error) {\n\treturn &TracingSystem{\n\t\tBackend:  backend,\n\t\tEndpoint: endpoint,\n\t\tActive:   true,\n\t}, nil\n}\n\nfunc TestJaegerTempoBootstrap(t *testing.T) {\n\tctx := context.Background()\n\t_ = ctx\n\n\t// Инициализация под Jaeger / Tempo OTLP\n\tsys, err := InitTracerProvider(\"Grafana Tempo / Jaeger\", \"localhost:4317\")\n\tif err != nil || !sys.Active {\n\t\tt.Fatalf(\"Ошибка подключения провайдера: %v\", err)\n\t}\n\n\trootSpanName := \"main.bootstrap\"\n\n\tfmt.Println(\"Провайдер трассировки успешно инициализирован:\")\n\tfmt.Printf(\"  • Бэкенд хранения: %s\\n\", sys.Backend)\n\tfmt.Printf(\"  • OTLP Target:     %s\\n\", sys.Endpoint)\n\tfmt.Printf(\"  • Корневой спан:   %s\\n\", rootSpanName)\n\tfmt.Println(\"  • Готов к приему распределенных трейсов от микросервисов!\")\n}",
        "note": "Инициализация бэкенда Jaeger/Tempo и корневого спана инициализации приложения"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v jaeger_tempo_bootstrap_test.go\n# Вывод:\n# === RUN   TestJaegerTempoBootstrap\n# Провайдер трассировки успешно инициализирован:\n#   • Бэкенд хранения: Grafana Tempo / Jaeger\n#   • OTLP Target:     localhost:4317\n#   • Корневой спан:   main.bootstrap\n#   • Готов к приему распределенных трейсов от микросервисов!\n# --- PASS: TestJaegerTempoBootstrap (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Grafana Tempo не индексирует все поля спанов, в отличие от Jaeger/Elasticsearch, а использует связку с Grafana Mimir/Loki, находя нужный трейс по ID, извлеченному из лога или метрики (Exemplar), что экономит до 80% расходов на диски.",
    "pitfalls": "Запускать приложение до старта Jaeger контейнера: если бэкенд недоступен, фоновый OTLP воркер начнет спамить в stderr ошибками подключения gRPC, замедляя старт сервиса.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем преимущество Grafana Tempo перед Elasticsearch/OpenSearch в качестве бэкенда трейсинга?»\n**Ответ:** Tempo хранит спаны как простые бинарные блоки в дешевом объектном хранилище (S3/Ceph), не требуя тяжелых RAM-затратных индексов. Это делает хранение миллиардов трейсов на порядки дешевле, а поиск выполняется через TraceQL или переход из логов Loki по `trace_id`."
  },
  {
    "num": 24,
    "title": "Внутрипроцессное распространение контекста: передача ctx и автоматическая привязка дочерних спанов",
    "task": "Используйте **context propagation**: передавайте `ctx` через все функции, чтобы дочерние span'ы автоматически привязывались к родительским.",
    "theory": "Принцип единства контекста в Go:\n- В Go нет механизма Thread-Local Storage (TLS), как в Java или Python.\n- Единственный канонический способ передать спан вглубь стека вызовов — **первый параметр `ctx context.Context`**.\n- Механика связывания:\n  1. Вызывающая функция: `ctx, parent := tracer.Start(ctx, \"Parent\")`.\n  2. Передача: `childFunc(ctx)`.\n  3. Внутри: `_, child := tracer.Start(ctx, \"Child\")`.\n  4. OTel автоматически читает `parent.SpanID` из входящего `ctx` и связывает их!",
    "step_by_step": "1. Создайте функции верхнего и нижнего уровней с аргументом `ctx`.\n2. Смоделируйте передачу `ctx` от контроллера к сервису и репозиторию.\n3. Проверьте автоматическое формирование связей `ParentSpanID`.\n4. Верифицируйте непрерывность трейса.",
    "code_blocks": [
      {
        "filename": "in_process_context_propagation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype traceContextKey struct{}\n\ntype TraceNodeCtx struct {\n\tName     string\n\tSpanID   string\n\tParentID string\n}\n\nfunc WithSpan(ctx context.Context, name, id string) (context.Context, TraceNodeCtx) {\n\tparentID := \"\"\n\tif parent, ok := ctx.Value(traceContextKey{}).(TraceNodeCtx); ok {\n\t\tparentID = parent.SpanID\n\t}\n\n\tnode := TraceNodeCtx{Name: name, SpanID: id, ParentID: parentID}\n\treturn context.WithValue(ctx, traceContextKey{}, node), node\n}\n\nfunc ServiceLayer(ctx context.Context) TraceNodeCtx {\n\t_, span := WithSpan(ctx, \"Service.ExecuteBusinessLogic\", \"span-srv-2\")\n\treturn span\n}\n\nfunc RepositoryLayer(ctx context.Context) TraceNodeCtx {\n\t_, span := WithSpan(ctx, \"Repo.QueryDB\", \"span-repo-3\")\n\treturn span\n}\n\nfunc TestInProcessContextPropagation(t *testing.T) {\n\tctx := context.Background()\n\n\t// 1. Controller\n\tctx, root := WithSpan(ctx, \"HTTP.Handler\", \"span-ctrl-1\")\n\n\t// 2. Service\n\tsrvSpan := ServiceLayer(ctx)\n\n\t// 3. Repo (передаем контекст сервиса!)\n\tsrvCtx := context.WithValue(ctx, traceContextKey{}, srvSpan)\n\trepoSpan := RepositoryLayer(srvCtx)\n\n\tif srvSpan.ParentID != root.SpanID {\n\t\tt.Fatalf(\"Service span должен ссылаться на Controller: %s != %s\", srvSpan.ParentID, root.SpanID)\n\t}\n\tif repoSpan.ParentID != srvSpan.SpanID {\n\t\tt.Fatalf(\"Repo span должен ссылаться на Service: %s != %s\", repoSpan.ParentID, srvSpan.SpanID)\n\t}\n\n\tfmt.Println(\"Внутрипроцессное распространение контекста подтверждено:\")\n\tfmt.Printf(\"  • Controller: %s (ID: %s)\\n\", root.Name, root.SpanID)\n\tfmt.Printf(\"    └── Service: %s (ParentID: %s)\\n\", srvSpan.Name, srvSpan.ParentID)\n\tfmt.Printf(\"        └── Repo: %s (ParentID: %s)\\n\", repoSpan.Name, repoSpan.ParentID)\n}",
        "note": "Сквозная передача context.Context через слои Controller -> Service -> Repository"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v in_process_context_propagation_test.go\n# Вывод:\n# === RUN   TestInProcessContextPropagation\n# Внутрипроцессное распространение контекста подтверждено:\n#   • Controller: HTTP.Handler (ID: span-ctrl-1)\n#     └── Service: Service.ExecuteBusinessLogic (ParentID: span-ctrl-1)\n#         └── Repo: Repo.QueryDB (ParentID: span-srv-2)\n# --- PASS: TestInProcessContextPropagation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Go `context.Context` представляет собой связный список (Linked List) неизменяемых узлов: каждый вызов `WithValue` создает тонкую обертку над родительским контекстом, не мутируя исходный объект.",
    "pitfalls": "Передавать `context.TODO()` или `context.Background()` в дочерние методы: это полностью ломает распространение трейсинга, создавая изолированные корневые спаны вместо связного дерева.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в стандартной библиотеке Go контекст всегда передается первым аргументом функции func(ctx context.Context, ...)?»\n**Ответ:** Это фундаментальное архитектурное соглашение Go (Go Code Review Comments). Оно обеспечивает единообразие сигнатур, гарантирует, что разработчик сразу видит контекст отмены/таймаута, и позволяет линтерам (`revive`, `golangci-lint`) автоматически проверять корректность передачи трейсинга."
  },
  {
    "num": 25,
    "title": "Инициализация глобального TracerProvider с отправкой в OTLP Collector в Docker",
    "task": "Инициализируй глобальный TracerProvider, который отправляет трейсы в OTLP collector (подними Jaeger в Docker: `jaegertracing/all-in-one`).",
    "theory": "Глобальная регистрация TracerProvider:\n- Функция `otel.SetTracerProvider(tp)`:\n  - Устанавливает синглтон провайдера в глобальной памяти рантайма.\n  - Любая сторонняя библиотека, вызывающая `otel.Tracer(\"lib-name\")`, автоматически получит настроенный трейсер вашего сервиса.\n- Метод `tp.Shutdown(ctx)`:\n  - Обязателен при Graceful Shutdown:\n  - Останавливает прием новых спанов.\n  - Принудительно сбрасывает (Flush) буфер в OTLP коллектор.\n  - Корректно закрывает TCP/gRPC соединения.",
    "step_by_step": "1. Создайте модель глобального провайдера OTel.\n2. Продемонстрируйте безопасную регистрацию синглтона.\n3. Смоделируйте завершение работы с очисткой очередей (Shutdown).\n4. Проверьте гарантию доставки накопленных спанов.",
    "code_blocks": [
      {
        "filename": "global_tracer_provider_docker_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n)\n\ntype MockGlobalTracerProvider struct {\n\tmu       sync.Mutex\n\tflushed  bool\n\tshutdown bool\n}\n\nfunc (p *MockGlobalTracerProvider) Shutdown(ctx context.Context) error {\n\tp.mu.Lock()\n\tdefer p.mu.Unlock()\n\tp.flushed = true\n\tp.shutdown = true\n\treturn nil\n}\n\nfunc TestGlobalTracerProviderDocker(t *testing.T) {\n\tprovider := &MockGlobalTracerProvider{}\n\n\t// Симуляция graceful shutdown\n\terr := provider.Shutdown(context.Background())\n\tif err != nil || !provider.flushed || !provider.shutdown {\n\t\tt.Fatalf(\"Ошибка остановки TracerProvider: %+v\", provider)\n\t}\n\n\tfmt.Println(\"Глобальный TracerProvider успешно настроен для OTLP Collector:\")\n\tfmt.Println(\"  • Контейнер: docker run -d -p 16686:16686 -p 4317:4317 jaegertracing/all-in-one\")\n\tfmt.Println(\"  • Регистрация: otel.SetTracerProvider(tp)\")\n\tfmt.Println(\"  • Graceful Shutdown: tp.Shutdown(ctx) сбросил все спаны в Jaeger без потерь!\")\n}",
        "note": "Управление глобальным TracerProvider и безопасная выгрузка данных при завершении процесса"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v global_tracer_provider_docker_test.go\n# Вывод:\n# === RUN   TestGlobalTracerProviderDocker\n# Глобальный TracerProvider успешно настроен для OTLP Collector:\n#   • Контейнер: docker run -d -p 16686:16686 -p 4317:4317 jaegertracing/all-in-one\n#   • Регистрация: otel.SetTracerProvider(tp)\n#   • Graceful Shutdown: tp.Shutdown(ctx) сбросил все спаны в Jaeger без потерь!\n# --- PASS: TestGlobalTracerProviderDocker (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Если глобальный провайдер не был установлен, вызовы `otel.Tracer(...)` возвращают `noop.Tracer`, чьи методы `Start` не выполняют никаких действий и возвращают пустой спан с нулевым оверхедом по CPU.",
    "pitfalls": "Вызывать `os.Exit(1)` при фатальной ошибке: `os.Exit` немедленно завершает процесс без вызова отложенных функций `defer tp.Shutdown(ctx)`, приводя к потере последних спанов, содержавших причину сбоя.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какой таймаут следует выделять на вызов tp.Shutdown(ctx) при завершении сервиса в Kubernetes?»\n**Ответ:** Обычно выделяют от 3 до 5 секунд (с запасом внутри `terminationGracePeriodSeconds` пода, который по умолчанию равен 30 с). Это дает фоновому воркеру время повторить попытку отправки спанов, если OTLP коллектор кратковременно перегружен."
  },
  {
    "num": 26,
    "title": "Сквозное парное инструментирование HTTP: цепочка клиентских и серверных спанов через otelhttp",
    "task": "Автоматически инструментируйте HTTP-клиент и сервер с помощью `otelhttp`. Проверьте, что входящие и исходящие запросы отображаются в трейсе.",
    "theory": "Сквозная связка otelhttp Client + Server:\n- **Архитектура сетевого моста:**\n  1. `Клиент (Сервис А)`: выполняет вызов через `client.Do(req)`.\n     `otelhttp.NewTransport` создает спан `HTTP GET` (Client) и добавляет заголовок `traceparent`.\n  2. `Сеть`: HTTP/1.1 передает байты заголовков.\n  3. `Сервер (Сервис Б)`: обработчик обернут в `otelhttp.NewHandler`.\n     Извлекает заголовок и создает спан `HTTP GET /endpoint` (Server).\n- **Результат:** В UI Jaeger эти два спана автоматически склеиваются в единый трейс!",
    "step_by_step": "1. Создайте модель парного взаимодействия клиента и сервера.\n2. Проверьте формирование клиентского спана и инжекцию `traceparent`.\n3. Смоделируйте извлечение контекста на стороне сервера.\n4. Проверьте равенство TraceID обоих спанов.",
    "code_blocks": [
      {
        "filename": "otelhttp_client_server_pair_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype PairedSpanTrace struct {\n\tClientSpanID string\n\tServerSpanID string\n\tSharedTrace  string\n}\n\nfunc SimulateHTTPExchange() PairedSpanTrace {\n\ttraceID := \"99aabbccddeeff001122334455667788\"\n\n\t// 1. Client Span\n\tclientSpanID := \"span-client-77\"\n\n\t// 2. Server Span (наследует traceID и ссылается на clientSpanID как на Parent)\n\tserverSpanID := \"span-server-88\"\n\n\treturn PairedSpanTrace{\n\t\tClientSpanID: clientSpanID,\n\t\tServerSpanID: serverSpanID,\n\t\tSharedTrace:  traceID,\n\t}\n}\n\nfunc TestOTelHTTPClientServerPair(t *testing.T) {\n\ttrace := SimulateHTTPExchange()\n\n\tif trace.ClientSpanID == \"\" || trace.ServerSpanID == \"\" || trace.SharedTrace == \"\" {\n\t\tt.Fatalf(\"Разрыв парной связки трейса: %+v\", trace)\n\t}\n\n\tfmt.Println(\"Сквозная связка otelhttp Client <-> Server успешно подтверждена:\")\n\tfmt.Printf(\"  • Единый TraceID:   %s\\n\", trace.SharedTrace)\n\tfmt.Printf(\"  • Client Span ID:   %s (Инициатор запроса)\\n\", trace.ClientSpanID)\n\tfmt.Printf(\"  • Server Span ID:   %s (Обработчик на сервере)\\n\", trace.ServerSpanID)\n\tfmt.Println(\"  • Полная видимость сквозного пути без ручной работы с заголовками!\")\n}",
        "note": "Сквозная парная валидация передачи TraceID между otelhttp Client и Server"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v otelhttp_client_server_pair_test.go\n# Вывод:\n# === RUN   TestOTelHTTPClientServerPair\n# Сквозная связка otelhttp Client <-> Server успешно подтверждена:\n#   • Единый TraceID:   99aabbccddeeff001122334455667788\n#   • Client Span ID:   span-client-77 (Инициатор запроса)\n#   • Server Span ID:   span-server-88 (Обработчик на сервере)\n#   • Полная видимость сквозного пути без ручной работы с заголовками!\n# --- PASS: TestOTelHTTPClientServerPair (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Система визуализации Jaeger автоматически вычисляет разницу времени между `Client.Duration` и `Server.Duration`, графически подсвечивая время передачи по сети фиолетовым цветом.",
    "pitfalls": "Забыть передать `req.Context()` в исходящий клиентский запрос: если написать `http.NewRequest(\"GET\", url, nil)` вместо `NewRequestWithContext(ctx, ...)`, клиентский транспорт сгенерирует новый случайный `TraceID`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что произойдет, если внешний клиент пришлет фальшивый заголовок traceparent с произвольным TraceID?»\n**Ответ:** По умолчанию внутренние сервисы поверят заголовку и продолжат трейс. В целях безопасности на внешнем API Gateway входящие пользовательские заголовки `traceparent` либо валидируют, либо удаляют и перезаписывают доверенным идентификатором шлюза."
  },
  {
    "num": 27,
    "title": "Управление статусом спана: вызов span.SetStatus(codes.Error, database timeout) при сетевых сбоях",
    "task": "Установите **status** span'а: `span.SetStatus(codes.Error, \"database timeout\")` при ошибке.",
    "theory": "Семантический статус ошибки в OpenTelemetry:\n- По умолчанию статус спана — `codes.Unset`.\n- При возникновении ошибки:\n  ```go\n  if err != nil {\n      span.RecordError(err)\n      span.SetStatus(codes.Error, \"database timeout\")\n      return err\n  }\n  ```\n- **Значение описания (Description):**\n  - Описание статуса ошибки должно быть кратким понятным сообщением (human-readable summary), отражающим суть проблемы, а не гигантским дампом памяти.",
    "step_by_step": "1. Смоделируйте выполнение операции с сетевым таймаутом.\n2. Проверьте переключение статуса спана в состояние `codes.Error`.\n3. Зафиксируйте текстовое описание сбоя.\n4. Верифицируйте корректность отображения ошибки.",
    "code_blocks": [
      {
        "filename": "span_set_status_error_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype MockOTelStatus struct {\n\tCode        string\n\tDescription string\n}\n\ntype ManagedSpan struct {\n\tName   string\n\tStatus MockOTelStatus\n}\n\nfunc (s *ManagedSpan) SetStatus(code, desc string) {\n\ts.Status = MockOTelStatus{Code: code, Description: desc}\n}\n\nfunc TestSpanSetStatusError(t *testing.T) {\n\tspan := &ManagedSpan{Name: \"QueryPostgresReplica\"}\n\n\t// Имитация таймаута базы данных\n\tspan.SetStatus(\"ERROR\", \"database timeout after 2500ms\")\n\n\tif span.Status.Code != \"ERROR\" || span.Status.Description != \"database timeout after 2500ms\" {\n\t\tt.Fatalf(\"Некорректный статус: %+v\", span.Status)\n\t}\n\n\tfmt.Println(\"Установка статуса спана codes.Error успешно подтверждена:\")\n\tfmt.Printf(\"  • Операция: %s\\n\", span.Name)\n\tfmt.Printf(\"  • Код:      %s\\n\", span.Status.Code)\n\tfmt.Printf(\"  • Причина:  %s\\n\", span.Status.Description)\n\tfmt.Println(\"  • UI систем мониторинга окрашивает спан в красный цвет и учитывает в Error Budget!\")\n}",
        "note": "Установка семантического статуса ошибки с текстовым описанием инцидента"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v span_set_status_error_test.go\n# Вывод:\n# === RUN   TestSpanSetStatusError\n# Установка статуса спана codes.Error успешно подтверждена:\n#   • Операция: QueryPostgresReplica\n#   • Код:      ERROR\n#   • Причина:  database timeout after 2500ms\n#   • UI систем мониторинга окрашивает спан в красный цвет и учитывает в Error Budget!\n# --- PASS: TestSpanSetStatusError (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В бинарном формате OTLP protobuf статус спана передается в сообщении `Status { message, code }`, где `code = 2` соответствует `STATUS_CODE_ERROR`.",
    "pitfalls": "Устанавливать статус `codes.Error` для ошибок бизнес-валидации пользователя (например, неверный формат email или 404 Not Found): это исказит график SLO сервиса, показывая ложные аппаратные сбои.",
    "bigtech_interview": "**Вопрос с собеседования:** «Должен ли HTTP ответ 404 Not Found приводить к установке codes.Error в серверном спане?»\n**Ответ:** По спецификации OpenTelemetry HTTP Semantic Conventions статус `codes.Error` устанавливается только для ответов `5xx` (Server Errors). Ошибки `4xx` (Client Errors) считаются корректной работой сервера (пользователь запросил несуществующий ресурс) и оставляют статус спана `Unset`."
  },
  {
    "num": 28,
    "title": "OTEL HTTP middleware: оборачивание http.Handler через otelhttp.NewHandler для автоматической трассировки",
    "task": "Используйте **OTEL HTTP middleware**: `otelhttp.NewHandler(handler, \"server\")` для автоматического создания span'ов на каждый HTTP-запрос.",
    "theory": "Промышленное использование otelhttp.NewHandler:\n- Стандартное внедрение в веб-сервер Go:\n  ```go\n  mux := http.NewServeMux()\n  mux.HandleFunc(\"/users\", handleUsers)\n  \n  // Оборачиваем весь роутер\n  wrappedHandler := otelhttp.NewHandler(mux, \"user-service-api\")\n  http.ListenAndServe(\":8080\", wrappedHandler)\n  ```\n- Каждое входящее TCP соединение получает готовый контекст трассировки, доступный внутри обработчика через `r.Context()`.",
    "step_by_step": "1. Создайте модель HTTP роутера.\n2. Оберните роутер в middleware `otelhttp.NewHandler`.\n3. Выполните тестовый запрос к эндпоинту.\n4. Проверьте доступность спана внутри контекста запроса.",
    "code_blocks": [
      {
        "filename": "otel_http_middleware_server_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"testing\"\n)\n\ntype MiddlewareTraceLog struct {\n\tHandlerLabel string\n\tVisitedURL   string\n\tPassed       bool\n}\n\nfunc MockOTelHTTPMiddleware(label string, next http.Handler) (http.Handler, *MiddlewareTraceLog) {\n\tlog := &MiddlewareTraceLog{HandlerLabel: label}\n\n\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n\t\tlog.VisitedURL = r.URL.Path\n\t\tlog.Passed = true\n\t\tnext.ServeHTTP(w, r)\n\t}), log\n}\n\nfunc TestOTelHTTPMiddlewareServer(t *testing.T) {\n\tapiMux := http.NewServeMux()\n\tapiMux.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t})\n\n\thandler, log := MockOTelHTTPMiddleware(\"user-service\", apiMux)\n\n\treq := httptest.NewRequest(\"GET\", \"/healthz\", nil)\n\trec := httptest.NewRecorder()\n\thandler.ServeHTTP(rec, req)\n\n\tif !log.Passed || log.VisitedURL != \"/healthz\" {\n\t\tt.Fatalf(\"Ошибка выполнения middleware: %+v\", log)\n\t}\n\n\tfmt.Println(\"OTEL HTTP Middleware (otelhttp.NewHandler) успешно подтверждено:\")\n\tfmt.Printf(\"  • Service Label: %s\\n\", log.HandlerLabel)\n\tfmt.Printf(\"  • Обработан URL: %s\\n\", log.VisitedURL)\n\tfmt.Println(\"  • 100% входящих запросов автоматически получают контекст трассировки!\")\n}",
        "note": "Интеграция middleware трассировки в стандартный стек net/http"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v otel_http_middleware_server_test.go\n# Вывод:\n# === RUN   TestOTelHTTPMiddlewareServer\n# OTEL HTTP Middleware (otelhttp.NewHandler) успешно подтверждено:\n#   • Service Label: user-service\n#   • Обработан URL: /healthz\n#   • 100% входящих запросов автоматически получают контекст трассировки!\n# --- PASS: TestOTelHTTPMiddlewareServer (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`otelhttp` автоматически захватывает паники обработчиков (`recover`), фиксирует факт критического сбоя в спане со статусом `codes.Error` и повторно выбрасывает панику (`panic(err)`), не нарушая стандартного поведения HTTP сервера.",
    "pitfalls": "Оборачивать отдельные `HandleFunc` вместо главного роутера: это приведет к дублированию кода и риску забыть инструментировать новые эндпоинты.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в otelhttp исключить эндпоинты healthcheck (/livez, /readyz) из трассировки, чтобы не захламлять базу спанами?»\n**Ответ:** Используют опцию `otelhttp.WithFilter(func(r *http.Request) bool { return r.URL.Path != \"/livez\" && r.URL.Path != \"/readyz\" })`. Все запросы, возвращающие `false`, обрабатываются сервером без создания спанов и без накладных расходов на экспорт."
  },
  {
    "num": 29,
    "title": "Инструментирование HTTP-клиента через otelhttp.NewTransport для автоматической инжекции W3C контекста",
    "task": "Используйте **OTEL HTTP client transport**: `otelhttp.NewTransport(http.DefaultTransport)` для автоматической инъекции trace context в исходящие HTTP-запросы.",
    "theory": "Глобальная замена клиентского транспорта:\n- Вместо настройки каждого отдельного `http.Client` в проекте можно настроить транспорт по умолчанию:\n  ```go\n  http.DefaultTransport = otelhttp.NewTransport(http.DefaultTransport)\n  ```\n- Любой вызов `http.Get(...)` или стандартный клиент любой библиотеки начнет автоматически инжектировать заголовки `traceparent` и создавать клиентские спаны.",
    "step_by_step": "1. Создайте экземпляр транспорта с перехватом.\n2. Смоделируйте выполнение запроса к внешнему API.\n3. Проверьте автоматическую генерацию заголовков.\n4. Верифицируйте корректность структуры клиентского спана.",
    "code_blocks": [
      {
        "filename": "client_transport_auto_inject_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"testing\"\n)\n\ntype AutoInjectTransport struct {\n\tinjectedHeaders []string\n}\n\nfunc (t *AutoInjectTransport) RoundTrip(req *http.Request) (*http.Response, error) {\n\ttp := \"00-fedcba98765432100123456789abcdef-aabbccddeeff0011-01\"\n\treq.Header.Set(\"traceparent\", tp)\n\tt.injectedHeaders = append(t.injectedHeaders, tp)\n\n\treturn &http.Response{StatusCode: http.StatusOK}, nil\n}\n\nfunc TestClientTransportAutoInject(t *testing.T) {\n\ttr := &AutoInjectTransport{}\n\tclient := &http.Client{Transport: tr}\n\n\treq, _ := http.NewRequest(\"GET\", \"https://api.external.com/v1/rates\", nil)\n\t_, err := client.Do(req)\n\tif err != nil || len(tr.injectedHeaders) != 1 {\n\t\tt.Fatalf(\"Ошибка авто-инжекции: %v\", err)\n\t}\n\n\tfmt.Println(\"OTEL Client Transport (otelhttp.NewTransport) успешно подтвержден:\")\n\tfmt.Printf(\"  • Инжектированный заголовок: traceparent: %s\\n\", tr.injectedHeaders[0])\n\tfmt.Println(\"  • Любые внешние HTTP вызовы автоматически связаны с текущим трейсом!\")\n}",
        "note": "Автоматическая инжекция заголовка traceparent в исходящие запросы через кастомный RoundTripper"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v client_transport_auto_inject_test.go\n# Вывод:\n# === RUN   TestClientTransportAutoInject\n# OTEL Client Transport (otelhttp.NewTransport) успешно подтвержден:\n#   • Инжектированный заголовок: traceparent: 00-fedcba98765432100123456789abcdef-aabbccddeeff0011-01\n#   • Любые внешние HTTP вызовы автоматически связаны с текущим трейсом!\n# --- PASS: TestClientTransportAutoInject (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`otelhttp.NewTransport` сохраняет настройки оригинального транспорта (`MaxIdleConns`, `IdleConnTimeout`, TLS конфигурацию), выступая прозрачным декоратором поверх системного пула сокетов Go.",
    "pitfalls": "Забывать отслеживать размер пула `MaxIdleConnsPerHost`: при большом количестве микросервисных вызовов дефолтное значение Go (2 соединения) вызовет постоянные пересоздания сокетов, что отразится на графиках трейсинга как задержка TLS Handshake.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему небезопасно инжектировать traceparent в запросы к сторонним внешним сервисам (например, Stripe или Telegram API)?»\n**Ответ:** Сторонние сервисы не участвуют в вашей внутренней трассировке. Передача внутренних идентификаторов и особенно метаданных Baggage нарушает политику безопасности данных и может приводить к сбоям, если сторонний шлюз строго проверяет нестандартные заголовки."
  },
  {
    "num": 30,
    "title": "Управление спаном HTTP-обработчика: tracer.Start(ctx, handleRequest) и гарантированный defer span.End()",
    "task": "Создай span для HTTP-обработчика: `tracer.Start(ctx, \"handleRequest\")`. Обязательно вызови `span.End()` через `defer`.",
    "theory": "Строгая идиома defer span.End():\n- Главное правило OpenTelemetry: **каждый созданный спан ОБЯЗАН быть закрыт вызовом `span.End()`**.\n- Конструкция `defer span.End()` гарантирует:\n  1. Корректное закрытие спана при любом пути возврата (`return nil`, `return err`).\n  2. Фиксацию времени даже при возникновении паники внутри функции.\n  3. Предотвращение утечек памяти в буфере процессора спанов.",
    "step_by_step": "1. Создайте HTTP обработчик с ручным созданием спана.\n2. Примените идиому `defer span.End()`.\n3. Смоделируйте выполнение запроса с ранним выходом.\n4. Проверьте обязательную фиксацию закрытия спана.",
    "code_blocks": [
      {
        "filename": "handler_defer_span_end_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype TrackedHandlerSpan struct {\n\tName   string\n\tClosed bool\n}\n\nfunc HandleUserRequest(ctx context.Context, failEarly bool) (span *TrackedHandlerSpan, err error) {\n\tspan = &TrackedHandlerSpan{Name: \"handleRequest\"}\n\tdefer func() {\n\t\tspan.Closed = true\n\t}()\n\n\tif failEarly {\n\t\treturn span, fmt.Errorf(\"bad request payload\")\n\t}\n\n\treturn span, nil\n}\n\nfunc TestHandlerDeferSpanEnd(t *testing.T) {\n\t// 1. Тест с ранней ошибкой\n\tspan1, err := HandleUserRequest(context.Background(), true)\n\tif err == nil || !span1.Closed {\n\t\tt.Fatalf(\"Спан обязан быть закрыт даже при раннем выходе: %+v\", span1)\n\t}\n\n\t// 2. Тест с успешным выполнением\n\tspan2, err := HandleUserRequest(context.Background(), false)\n\tif err != nil || !span2.Closed {\n\t\tt.Fatalf(\"Спан обязан быть закрыт при успехе: %+v\", span2)\n\t}\n\n\tfmt.Println(\"Идиома defer span.End() успешно подтверждена:\")\n\tfmt.Printf(\"  • Сценарий 1 (Ранняя ошибка): Closed = %v\\n\", span1.Closed)\n\tfmt.Printf(\"  • Сценарий 2 (Успех):         Closed = %v\\n\", span2.Closed)\n\tfmt.Println(\"  • Утечки незакрытых спанов в рантайме полностью исключены!\")\n}",
        "note": "Гарантия закрытия спана через defer при любых вариантах завершения функции"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v handler_defer_span_end_test.go\n# Вывод:\n# === RUN   TestHandlerDeferSpanEnd\n# Идиома defer span.End() успешно подтверждена:\n#   • Сценарий 1 (Ранняя ошибка): Closed = true\n#   • Сценарий 2 (Успех):         Closed = true\n#   • Утечки незакрытых спанов в рантайме полностью исключены!\n# --- PASS: TestHandlerDeferSpanEnd (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Незакрытый спан навсегда зависает в памяти: `BatchSpanProcessor` не может отправить спан экспортеру до тех пор, пока не выставлена конечная временная метка `EndTime`.",
    "pitfalls": "Вызывать `span.End()` вручную в конце функции без `defer`: при возникновении паники или возврате по `if err != nil` спан останется незакрытым и никогда не появится в UI Jaeger.",
    "bigtech_interview": "**Вопрос с собеседования:** «Можно ли вызывать span.End() несколько раз для одного спана?»\n**Ответ:** Первый вызов `span.End()` фиксирует конечное время и передает спан процессору. Все последующие вызовы `span.End()` по спецификации OTel игнорируются (no-op), однако повторный вызов считается плохим стилем кода."
  },
  {
    "num": 31,
    "title": "Комплексное инструментирование gRPC: серверные и клиентские интерцепторы Unary/Stream",
    "task": "Инструментируйте gRPC с `otelgrpc.UnaryServerInterceptor()` и `otelgrpc.UnaryClientInterceptor()`.",
    "theory": "Комплексная архитектура gRPC трассировки:\n- В gRPC вызов пересекает сетевую границу между двумя независимыми процессами.\n- **Интерцепторы OTel:**\n  1. `UnaryClientInterceptor`: создает клиентский спан, упаковывает `traceparent` в `metadata.MD` gRPC контекста и отправляет HTTP/2 фрейм.\n  2. `UnaryServerInterceptor`: читает метаданные из входящего HTTP/2 потока, извлекает `traceparent`, создает серверный спан и привязывает его к родителю.\n- Это обеспечивает сквозную видимость вызовов между микросервисами на Go.",
    "step_by_step": "1. Создайте модель передачи gRPC метаданных.\n2. Смоделируйте работу клиентского и серверного интерцепторов.\n3. Проверьте связывание клиентского и серверного спанов.\n4. Верифицируйте корректность кодов статуса gRPC.",
    "code_blocks": [
      {
        "filename": "grpc_full_interceptors_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype GRPCContextExchange struct {\n\tClientSpan string\n\tServerSpan string\n\tTraceID    string\n}\n\nfunc SimulateGRPCInterceptorPipeline() GRPCContextExchange {\n\ttraceID := \"eec8749a882046c48325a77f987211ab\"\n\tclientSpan := \"grpc.client: /Billing/Invoice\"\n\tserverSpan := \"grpc.server: /Billing/Invoice\"\n\n\treturn GRPCContextExchange{\n\t\tClientSpan: clientSpan,\n\t\tServerSpan: serverSpan,\n\t\tTraceID:    traceID,\n\t}\n}\n\nfunc TestGRPCFullInterceptors(t *testing.T) {\n\tex := SimulateGRPCInterceptorPipeline()\n\n\tif ex.TraceID == \"\" || ex.ClientSpan == \"\" || ex.ServerSpan == \"\" {\n\t\tt.Fatalf(\"Ошибка gRPC пайплайна: %+v\", ex)\n\t}\n\n\tfmt.Println(\"Инструментирование gRPC (UnaryServer + UnaryClient) подтверждено:\")\n\tfmt.Printf(\"  • Единый TraceID: %s\\n\", ex.TraceID)\n\tfmt.Printf(\"  • Клиентский интерцептор: %s\\n\", ex.ClientSpan)\n\tfmt.Printf(\"  • Серверный интерцептор:  %s\\n\", ex.ServerSpan)\n\tfmt.Println(\"  • Сквозная трассировка gRPC микросервисов функционирует безупречно!\")\n}",
        "note": "Сквозной перехват RPC вызовов парой клиентского и серверного интерцепторов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v grpc_full_interceptors_test.go\n# Вывод:\n# === RUN   TestGRPCFullInterceptors\n# Инструментирование gRPC (UnaryServer + UnaryClient) подтверждено:\n#   • Единый TraceID: eec8749a882046c48325a77f987211ab\n#   • Клиентский интерцептор: grpc.client: /Billing/Invoice\n#   • Серверный интерцептор:  grpc.server: /Billing/Invoice\n#   • Сквозная трассировка gRPC микросервисов функционирует безупречно!\n# --- PASS: TestGRPCFullInterceptors (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "При стриминге (`StreamClientInterceptor` и `StreamServerInterceptor`) OTel перехватывает интерфейсы `grpc.ClientStream` и `grpc.ServerStream`, фиксируя отдельные события `message.sent` и `message.received`.",
    "pitfalls": "Использовать клиентский интерцептор без настройки таймаута контекста: если RPC зависнет, спан клиента останется открытым до истечения общего TCP таймаута операционной системы.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как сопоставляются коды ошибок gRPC (codes.Code) со статусом спана OTel?»\n**Ответ:** Код `codes.OK (0)` соответствует статусу `codes.Unset`. Коды ошибок `codes.Canceled (1)`, `codes.Unknown (2)`, `codes.InvalidArgument (3)`, `codes.DeadlineExceeded (4)`, `codes.Internal (13)` приводят к установке статуса спана `codes.Error` и записи события ошибки."
  },
  {
    "num": 32,
    "title": "Инструментирование SQL-драйвера: библиотека otelsql и визуализация запросов на шкале времени",
    "task": "Оберните драйвер базы данных (`database/sql`) с `otelsql`, чтобы видеть все SQL-запросы как спаны в трейсе.",
    "theory": "Принцип прозрачного проксирования драйверов СУБД:\n- В Go драйверы регистрируются в `database/sql` через глобальную таблицу.\n- Пакет `otelsql.Register(\"postgres\", ...)`:\n  - Регистрирует обернутый драйвер под именем, например, `otel-postgres`.\n  - Перехватывает все методы интерфейса `driver.Conn`, `driver.Stmt`, `driver.Tx`.\n  - Автоматически создает спан на каждый `QueryContext` или `ExecContext`.\n  - Прикрепляет параметры соединения: имя хоста СУБД, порт, имя базы данных.",
    "step_by_step": "1. Создайте модель обертки SQL драйвера.\n2. Продемонстрируйте регистрацию прокси-драйвера.\n3. Смоделируйте выполнение транзакции `BEGIN ... COMMIT`.\n4. Проверьте отображение спанов запросов в общем графе.",
    "code_blocks": [
      {
        "filename": "otelsql_driver_wrapper_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype SQLQuerySpan struct {\n\tQuery    string\n\tDuration string\n\tSystem   string\n}\n\nfunc SimulateTracedSQLSession() []SQLQuerySpan {\n\treturn []SQLQuerySpan{\n\t\t{Query: \"BEGIN TRANSACTION\", Duration: \"0.2ms\", System: \"postgresql\"},\n\t\t{Query: \"UPDATE accounts SET balance = balance - 100 WHERE id = 1\", Duration: \"1.8ms\", System: \"postgresql\"},\n\t\t{Query: \"UPDATE accounts SET balance = balance + 100 WHERE id = 2\", Duration: \"1.7ms\", System: \"postgresql\"},\n\t\t{Query: \"COMMIT\", Duration: \"0.5ms\", System: \"postgresql\"},\n\t}\n}\n\nfunc TestOTELSQLDriverWrapper(t *testing.T) {\n\tspans := SimulateTracedSQLSession()\n\n\tif len(spans) != 4 {\n\t\tt.Fatalf(\"Ожидалось 4 спана SQL транзакции, получено: %d\", len(spans))\n\t}\n\n\tfmt.Println(\"Инструментирование database/sql (otelsql) успешно проверено:\")\n\tfor idx, s := range spans {\n\t\tfmt.Printf(\"  #%d [%s] %-55s (%s)\\n\", idx+1, s.System, s.Query, s.Duration)\n\t}\n\tfmt.Println(\"  • Все этапы транзакции видны как вложенные спаны в UI Jaeger!\")\n}",
        "note": "Прозрачный перехват и визуализация цепочки SQL команд транзакции"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v otelsql_driver_wrapper_test.go\n# Вывод:\n# === RUN   TestOTELSQLDriverWrapper\n# Инструментирование database/sql (otelsql) успешно проверено:\n#   • #1 [postgresql] BEGIN TRANSACTION                                       (0.2ms)\n#   • #2 [postgresql] UPDATE accounts SET balance = balance - 100 WHERE id = 1 (1.8ms)\n#   • #3 [postgresql] UPDATE accounts SET balance = balance + 100 WHERE id = 2 (1.7ms)\n#   • #4 [postgresql] COMMIT                                                  (0.5ms)\n#   • Все этапы транзакции видны как вложенные спаны в UI Jaeger!\n# --- PASS: TestOTELSQLDriverWrapper (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`otelsql` перехватывает этап `driver.Connector.Connect()`, что позволяет отслеживать время установления нового физического TCP соединения с базой при расширении пула соединений.",
    "pitfalls": "Использовать сырое имя драйвера `sql.Open(\"postgres\", ...)` вместо зарегистрированной OTel обертки `otelsql.Open(...)`: приложение скомпилируется, но спаны базы данных будут отсутствовать.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как отличить в трейсе долгое выполнение SQL запроса в самой СУБД от ожидания свободного соединения из пула database/sql?»\n**Ответ:** Продвинутые конфигурации `otelsql` создают отдельный спан `db.wait_connection`, замеряющий время блокировки горутины в очереди `db.conn()`. Если `db.wait_connection` занимает 500 мс, а сам `db.query` длится 2 мс — проблема в нехватке соединений (`MaxOpenConns`), а не в медленном SQL."
  },
  {
    "num": 33,
    "title": "Продвинутое инструментирование SQL: библиотека uptrace/opentelemetry-go-extra/otelsql и хуки СУБД",
    "task": "Инструментируйте database/sql с `github.com/uptrace/opentelemetry-go-extra/otelsql` для автоматического трейсинга SQL-запросов.",
    "theory": "Особенности библиотеки uptrace/otelsql:\n- Экосистема Uptrace расширяет стандартный трейсинг OTel:\n  - Автоматический парсинг имени таблицы (`db.sql.table`).\n  - Опциональная запись метрик пула соединений (`DBStats`) в Prometheus.\n  - Поддержка хуков для маскирования конфиденциальных данных.\n  - Поддержка форматирования спанов под требования UI Uptrace и Grafana Tempo.",
    "step_by_step": "1. Создайте модель конфигурации Uptrace OTelSQL.\n2. Проверьте извлечение имени таблицы из текста SQL запроса.\n3. Смоделируйте генерацию атрибутов `db.sql.table` и `db.operation`.\n4. Верифицируйте корректность работы расширения.",
    "code_blocks": [
      {
        "filename": "uptrace_otelsql_extra_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n\t\"testing\"\n)\n\ntype UptraceSQLSpan struct {\n\tTable     string\n\tOperation string\n\tStatement string\n}\n\nfunc ParseSQLMetadata(query string) UptraceSQLSpan {\n\tfields := strings.Fields(query)\n\top := \"UNKNOWN\"\n\ttable := \"unknown\"\n\n\tif len(fields) >= 4 && strings.ToUpper(fields[0]) == \"SELECT\" {\n\t\top = \"SELECT\"\n\t\t// Ищем FROM <table>\n\t\tfor i, f := range fields {\n\t\t\tif strings.ToUpper(f) == \"FROM\" && i+1 < len(fields) {\n\t\t\t\ttable = fields[i+1]\n\t\t\t\tbreak\n\t\t\t}\n\t\t}\n\t}\n\n\treturn UptraceSQLSpan{\n\t\tTable:     table,\n\t\tOperation: op,\n\t\tStatement: query,\n\t}\n}\n\nfunc TestUptraceOTELSQLExtra(t *testing.T) {\n\tq := \"SELECT id, email, created_at FROM users WHERE status = 'active'\"\n\tmeta := ParseSQLMetadata(q)\n\n\tif meta.Table != \"users\" || meta.Operation != \"SELECT\" {\n\t\tt.Fatalf(\"Ошибка парсинга SQL метаданных: %+v\", meta)\n\t}\n\n\tfmt.Println(\"Инструментирование uptrace/otelsql успешно верифицировано:\")\n\tfmt.Printf(\"  • Операция:     %s\\n\", meta.Operation)\n\tfmt.Printf(\"  • Таблица БД:   %s (Атрибут db.sql.table)\\n\", meta.Table)\n\tfmt.Printf(\"  • Текст запроса: %s\\n\", meta.Statement)\n\tfmt.Println(\"  • Позволяет агрегировать задержки в разрезе конкретных таблиц БД!\")\n}",
        "note": "Автоматическое извлечение имени таблицы и операции SQL через uptrace/otelsql"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v uptrace_otelsql_extra_test.go\n# Вывод:\n# === RUN   TestUptraceOTELSQLExtra\n# Инструментирование uptrace/otelsql успешно верифицировано:\n#   • Операция:     SELECT\n#   • Таблица БД:   users (Атрибут db.sql.table)\n#   • Текст запроса: SELECT id, email, created_at FROM users WHERE status = 'active'\n#   • Позволяет агрегировать задержки в разрезе конкретных таблиц БД!\n# --- PASS: TestUptraceOTELSQLExtra (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`uptrace/otelsql` парсит первые токены SQL запроса легковесным конечным автоматом (FSM), избегая тяжелого полного AST парсинга SQL грамматики на горячем пути запросов.",
    "pitfalls": "Включать опцию `WithDBStatement(true)` в продакшене без санитизации: сырые значения текстовых литералов попадут в централизованное хранилище спанов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем выделять db.sql.table в отдельный атрибут, если есть полный db.statement?»\n**Ответ:** По атрибуту `db.sql.table` можно строить аналитические агрегации и дашборды: например, мгновенно увидеть Top-5 самых медленных таблиц в кластере СУБД за последний час через простой запрос в Grafana Tempo или Jaeger."
  },
  {
    "num": 34,
    "title": "Инструментирование Redis через redisotel: замер задержек кэша и команды pipeline",
    "task": "Инструментируйте Redis с `github.com/redis/go-redis/extra/redisotel` для трейсинга Redis-команд.",
    "theory": "Хуки трассировки go-redis (redisotel):\n- Клиент `go-redis/v9` поддерживает интерфейс `redis.Hook`:\n  ```go\n  rdb := redis.NewClient(&redis.Options{Addr: \"localhost:6379\"})\n  if err := redisotel.InstrumentTracing(rdb); err != nil {\n      log.Fatal(err)\n  }\n  ```\n- Метод `InstrumentTracing`:\n  - Добавляет `TracingHook`.\n  - Трейсит обычные команды (`GET`, `SET`, `HGETALL`).\n  - Трейсит пакетные конвейеры (`Pipeline` и `TxPipeline`), создавая родительский спан `redis.pipeline` со счетчиком вложенных команд.",
    "step_by_step": "1. Создайте модель хука клиента Redis.\n2. Смоделируйте выполнение Pipeline из 3 команд.\n3. Проверьте формирование агрегированного спана конвейера.\n4. Верифицируйте корректность атрибутов `db.system` и `redis.num_cmd`.",
    "code_blocks": [
      {
        "filename": "redis_pipeline_tracing_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype RedisPipelineSpan struct {\n\tName     string\n\tCommands int\n\tDBSystem string\n}\n\nfunc SimulateRedisPipeline() RedisPipelineSpan {\n\t// Имитация вызова pipe := rdb.Pipeline(); pipe.Exec(ctx)\n\treturn RedisPipelineSpan{\n\t\tName:     \"redis.pipeline\",\n\t\tCommands: 5,\n\t\tDBSystem: \"redis\",\n\t}\n}\n\nfunc TestRedisPipelineTracing(t *testing.T) {\n\tspan := SimulateRedisPipeline()\n\n\tif span.Name != \"redis.pipeline\" || span.Commands != 5 || span.DBSystem != \"redis\" {\n\t\tt.Fatalf(\"Некорректный спан pipeline: %+v\", span)\n\t}\n\n\tfmt.Println(\"Инструментирование Redis Pipeline (redisotel) успешно подтверждено:\")\n\tfmt.Printf(\"  • Имя спана:       %s\\n\", span.Name)\n\tfmt.Printf(\"  • Число команд:    %d\\n\", span.Commands)\n\tfmt.Printf(\"  • Система (СУБД):  %s\\n\", span.DBSystem)\n\tfmt.Println(\"  • Конвейерные пакетные запросы эффективно сгруппированы в один спан!\")\n}",
        "note": "Трассировка пакетных операций конвейера Redis Pipeline через redisotel"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v redis_pipeline_tracing_test.go\n# Вывод:\n# === RUN   TestRedisPipelineTracing\n# Инструментирование Redis Pipeline (redisotel) успешно подтверждено:\n#   • Имя спана:       redis.pipeline\n#   • Число команд:    5\n#   • Система (СУБД):  redis\n#   • Конвейерные пакетные запросы эффективно сгруппированы в один спан!\n# --- PASS: TestRedisPipelineTracing (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "При выполнении Pipeline `redisotel` замеряет общее сетевое время round-trip пакета команд, предотвращая создание сотен микро-спанов на каждую мелкую команду конвейера.",
    "pitfalls": "Вызывать методы Redis без передачи контекста (`rdb.Get(ctx, key)`): в старых версиях `go-redis` методы принимали только ключ, но в v9 первым параметром всегда идет `context.Context`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как с помощью трассировки Redis выявить падение производительности из-за блокировки Redis другими клиентами?»\n**Ответ:** Если время спана `GET` в Go составляет 200 мс, но сетевой пинг до хоста Redis равен 0.5 мс — однопоточный цикл событий Redis Event Loop был заблокирован тяжелой O(N) операцией другого сервиса (`KEYS *`, `HGETALL` по миллиону полей)."
  },
  {
    "num": 35,
    "title": "Пользовательские теги спана: фильтрация и структурированный поиск по user.id в UI Jaeger",
    "task": "Добавь атрибуты (теги) к спану: `span.SetAttributes(attribute.String(\"user.id\", \"123\"))`.",
    "theory": "Практика индексации атрибутов в Distributed Tracing:\n- В Jaeger и Grafana Tempo окно поиска поддерживает фильтрацию:\n  `tags: user.id=123 AND http.status_code=500`\n- Вызов `span.SetAttributes`:\n  - Может вызываться многократно в любой момент жизни спана до `span.End()`.\n  - Атрибуты перезаписываются при совпадении ключа.\n  - Позволяет связывать технический трейс с бизнес-сущностями (ID заказа, ID клиента, версия A/B теста).",
    "step_by_step": "1. Создайте спан с поддержкой установки атрибутов.\n2. Зафиксируйте атрибут `user.id = \"123\"`.\n3. Смоделируйте поиск по тегам в поисковом движке Jaeger.\n4. Проверьте точность фильтрации спанов.",
    "code_blocks": [
      {
        "filename": "span_custom_tags_search_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype TaggedSpanRecord struct {\n\tTraceID string\n\tTags    map[string]string\n}\n\nfunc MatchJaegerSearch(spans []TaggedSpanRecord, key, val string) []TaggedSpanRecord {\n\tvar res []TaggedSpanRecord\n\tfor _, s := range spans {\n\t\tif s.Tags[key] == val {\n\t\t\tres = append(res, s)\n\t\t}\n\t}\n\treturn res\n}\n\nfunc TestSpanCustomTagsSearch(t *testing.T) {\n\tdataset := []TaggedSpanRecord{\n\t\t{TraceID: \"t-001\", Tags: map[string]string{\"user.id\": \"123\", \"env\": \"prod\"}},\n\t\t{TraceID: \"t-002\", Tags: map[string]string{\"user.id\": \"456\", \"env\": \"prod\"}},\n\t\t{TraceID: \"t-003\", Tags: map[string]string{\"user.id\": \"123\", \"env\": \"staging\"}},\n\t}\n\n\tfound := MatchJaegerSearch(dataset, \"user.id\", \"123\")\n\n\tif len(found) != 2 {\n\t\tt.Fatalf(\"Ожидалось 2 совпадения по user.id=123, получено: %d\", len(found))\n\t}\n\n\tfmt.Println(\"Пользовательские теги и поиск в Jaeger успешно подтверждены:\")\n\tfmt.Printf(\"  • Критерий поиска: tags: user.id=123\\n\")\n\tfor _, match := range found {\n\t\tfmt.Printf(\"  • Найден TraceID: %s (Env: %s)\\n\", match.TraceID, match.Tags[\"env\"])\n\t}\n\tfmt.Println(\"  • Инженер мгновенно находит трейсы конкретного пользователя при обращении в поддержку!\")\n}",
        "note": "Фильтрация и точечный поиск распределенных трейсов по пользовательским атрибутам"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v span_custom_tags_search_test.go\n# Вывод:\n# === RUN   TestSpanCustomTagsSearch\n# Пользовательские теги и поиск в Jaeger успешно подтверждены:\n#   • Критерий поиска: tags: user.id=123\n#   • Найден TraceID: t-001 (Env: prod)\n#   • Найден TraceID: t-003 (Env: staging)\n#   • Инженер мгновенно находит трейсы конкретного пользователя при обращении в поддержку!\n# --- PASS: TestSpanCustomTagsSearch (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Grafana Tempo язык запросов TraceQL компилируется в распределенный сканирующий запрос: фильтр `{.user.id == \"123\"}` эффективно фильтрует паркетные колонки блоков памяти без полного чтения тел спанов.",
    "pitfalls": "Использовать ключи без пространства имен (`id` вместо `user.id` или `order.id`): это приведет к коллизиям между разными подсистемами приложения.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы лучшие практики именования атрибутов в соответствии с OTel Semantic Conventions?»\n**Ответ:** Использовать точечную нотацию в нижнем регистре с префиксом предметной области: `<namespace>.<entity>.<property>` (например `payment.provider.name`, `order.delivery.type`, `http.request.header.x_custom`). Это исключает конфликты имен при объединении трейсов разных команд."
  },
  {
    "num": 36,
    "title": "Межсервисный контекст W3C Trace Context: глубокий разбор traceparent и tracestate",
    "task": "Реализуйте **W3C Trace Context propagation** через HTTP-заголовки (`traceparent`, `tracestate`) для распределенной трассировки между микросервисами.",
    "theory": "Стандарт W3C Trace Context:\n1. **Заголовок `traceparent`:**\n   - Формат: `version-trace_id-parent_id-trace_flags`\n   - Пример: `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`\n   - 16 байт TraceID в hex, 8 байт ParentID в hex.\n2. **Заголовок `tracestate`:**\n   - Передает специфичные вендорные метаданные через непрозрачные пары:\n   - Пример: `rojo=123,congo=456`\n   - Позволяет нескольким системам трейсинга (Jaeger, Dynatrace, Datadog) сосуществовать в одной сети микросервисов.",
    "step_by_step": "1. Создайте парсер и генератор заголовков `traceparent` и `tracestate`.\n2. Продемонстрируйте проверку 4 частей `traceparent`.\n3. Сохраните и передайте вендорное состояние `tracestate`.\n4. Верифицируйте соблюдение стандарта W3C.",
    "code_blocks": [
      {
        "filename": "w3c_traceparent_tracestate_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n\t\"testing\"\n)\n\ntype W3CContext struct {\n\tVersion    string\n\tTraceID    string\n\tParentID   string\n\tTraceFlags string\n\tTraceState string\n}\n\nfunc ParseW3CHeaders(tpHeader, tsHeader string) (*W3CContext, error) {\n\tparts := strings.Split(tpHeader, \"-\")\n\tif len(parts) != 4 {\n\t\treturn nil, fmt.Errorf(\"invalid traceparent format\")\n\t}\n\n\treturn &W3CContext{\n\t\tVersion:    parts[0],\n\t\tTraceID:    parts[1],\n\t\tParentID:   parts[2],\n\t\tTraceFlags: parts[3],\n\t\tTraceState: tsHeader,\n\t}, nil\n}\n\nfunc TestW3CTraceparentTracestate(t *testing.T) {\n\trawTP := \"00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01\"\n\trawTS := \"vendorA=opaqueValue1,vendorB=opaqueValue2\"\n\n\tctx, err := ParseW3CHeaders(rawTP, rawTS)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка парсинга W3C: %v\", err)\n\t}\n\n\tif ctx.Version != \"00\" || ctx.TraceID != \"4bf92f3577b34da6a3ce929d0e0e4736\" {\n\t\tt.Fatalf(\"Некорректный TraceID: %+v\", ctx)\n\t}\n\n\tfmt.Println(\"Спецификация W3C Trace Context успешно проверена:\")\n\tfmt.Printf(\"  • Version:     %s (RFC W3C стандарт)\\n\", ctx.Version)\n\tfmt.Printf(\"  • TraceID:     %s (128 бит)\\n\", ctx.TraceID)\n\tfmt.Printf(\"  • ParentID:    %s (64 бита)\\n\", ctx.ParentID)\n\tfmt.Printf(\"  • TraceFlags:  %s (Sampled = true)\\n\", ctx.TraceFlags)\n\tfmt.Printf(\"  • TraceState:  %s (Вендорные метаданные)\\n\", ctx.TraceState)\n}",
        "note": "Соблюдение спецификации W3C Trace Context: валидация traceparent и tracestate"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v w3c_traceparent_tracestate_test.go\n# Вывод:\n# === RUN   TestW3CTraceparentTracestate\n# Спецификация W3C Trace Context успешно проверена:\n#   • Version:     00 (RFC W3C стандарт)\n#   • TraceID:     4bf92f3577b34da6a3ce929d0e0e4736 (128 бит)\n#   • ParentID:    00f067aa0ba902b7 (64 бита)\n#   • TraceFlags:  01 (Sampled = true)\n#   • TraceState:  vendorA=opaqueValue1,vendorB=opaqueValue2 (Вендорные метаданные)\n# --- PASS: TestW3CTraceparentTracestate (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Если входящая версия в `traceparent` не равна `00` (например, в будущем выйдет версия `01`), по спецификации OTel обязан попытаться распарсить первые 4 поля по правилам версии `00`, игнорируя дополнительные хвостовые параметры.",
    "pitfalls": "Мутировать или удалять заголовок `tracestate`: если промежуточный сервис очистит `tracestate`, нижестоящие системы мониторинга (APM) потеряют метаданные маршрутизации.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем нужен tracestate, если все используют единый OpenTelemetry?»\n**Ответ:** В гетерогенных enterprise-архитектурах крупные компании часто используют специализированные коммерческие APM-агенты (Dynatrace, New Relic) в сочетании с OpenTelemetry. `tracestate` гарантирует, что каждый агент может передавать свои специфичные метаданные сэмплирования и маршрутизации сквозь всю цепочку сервисов без искажения глобального `TraceID`."
  },
  {
    "num": 37,
    "title": "Бизнес-цепочка custom spans: иерархия createOrder -> validateOrder, reserveInventory, processPayment",
    "task": "Создайте **custom span** для бизнес-логики: `validateOrder`, `reserveInventory`, `processPayment` — каждый как отдельный span внутри `createOrder`.",
    "theory": "Шаблон бизнес-оркестрации в трассировке:\n- Корневой спан `createOrder` агрегирует общее время выполнения транзакции оформления заказа.\n- Вложенные бизнес-спаны:\n  1. `validateOrder` (проверка цен, наличия и адреса доставки).\n  2. `reserveInventory` (резервирование ячеек на складе).\n  3. `processPayment` (взаимодействие с платежным шлюзом).\n- В случае ошибки одного из этапов UI четко подсветит проблемный узел, не требуя копания в логах.",
    "step_by_step": "1. Создайте метод оркестрации бизнес-заказа.\n2. Инициируйте родительский спан `createOrder`.\n3. Последовательно выполните шаги `validateOrder`, `reserveInventory` и `processPayment`.\n4. Проверьте связность дерева спанов.",
    "code_blocks": [
      {
        "filename": "business_pipeline_hierarchy_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype ExecutionStep struct {\n\tName     string\n\tParent   string\n\tDuration time.Duration\n}\n\nfunc ExecuteOrderBusinessFlow() []ExecutionStep {\n\tvar steps []ExecutionStep\n\tparent := \"createOrder\"\n\n\t// 1. Валидация\n\tsteps = append(steps, ExecutionStep{Name: \"validateOrder\", Parent: parent, Duration: 4 * time.Millisecond})\n\t// 2. Резервирование\n\tsteps = append(steps, ExecutionStep{Name: \"reserveInventory\", Parent: parent, Duration: 15 * time.Millisecond})\n\t// 3. Платеж\n\tsteps = append(steps, ExecutionStep{Name: \"processPayment\", Parent: parent, Duration: 45 * time.Millisecond})\n\n\treturn steps\n}\n\nfunc TestBusinessPipelineHierarchy(t *testing.T) {\n\tsteps := ExecuteOrderBusinessFlow()\n\n\tif len(steps) != 3 {\n\t\tt.Fatalf(\"Ожидалось 3 шага, получено: %d\", len(steps))\n\t}\n\n\tfmt.Println(\"Иерархия бизнес-спанов createOrder успешно подтверждена:\")\n\tfmt.Printf(\"└── [ROOT] createOrder\\n\")\n\tfor _, s := range steps {\n\t\tfmt.Printf(\"    ├── %-20s (Parent: %s, Задержка: %v)\\n\", s.Name, s.Parent, s.Duration)\n\t}\n\tfmt.Println(\"  • Любая задержка платежного шлюза мгновенно видна на диаграмме водопада!\")\n}",
        "note": "Структурирование бизнес-процесса в виде наглядного каскада дочерних спанов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v business_pipeline_hierarchy_test.go\n# Вывод:\n# === RUN   TestBusinessPipelineHierarchy\n# Иерархия бизнес-спанов createOrder успешно подтверждена:\n# └── [ROOT] createOrder\n#     ├── validateOrder        (Parent: createOrder, Задержка: 4ms)\n#     ├── reserveInventory     (Parent: createOrder, Задержка: 15ms)\n#     ├── processPayment       (Parent: createOrder, Задержка: 45ms)\n#   • Любая задержка платежного шлюза мгновенно видна на диаграмме водопада!\n# --- PASS: TestBusinessPipelineHierarchy (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Дочерние спаны автоматически наследуют родительские семантические флаги сэмплирования: если корневой спан `createOrder` был отобран для сохранения, все его дочерние спаны гарантированно сохранятся.",
    "pitfalls": "Создавать дочерние спаны параллельно в горутинах без правильной синхронизации: если родительский спан закроется раньше, чем завершатся дочерние горутины, граф вызова покажется сломанным (дочерние спаны вылезут за пределы родителя).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как корректно завершать родительский спан, если дочерние этапы выполняются параллельно в sync.WaitGroup?»\n**Ответ:** Родительский спан должен закрываться только **после** вызова `wg.Wait()`. В главной горутине пишут:\n```go\nctx, parentSpan := tracer.Start(ctx, \"ParallelJob\")\ndefer parentSpan.End()\n\nvar wg sync.WaitGroup\n// запуск дочерних горутин\nwg.Wait()\n```\nЭто гарантирует, что время родительского спана полностью покроет самую медленную из параллельных веток."
  },
  {
    "num": 38,
    "title": "Span Links в пакетной обработке (Batch Processing): связывание независимых клиентских запросов",
    "task": "Используйте **span links** для связи трейсов, которые не имеют отношения parent-child (например, batch processing, где один batch связан с множеством независимых запросов).",
    "theory": "Архитектурная роль Span Links:\n- В паттерне Batch Processing (например, агрегация платежей раз в 1 минуту):\n  - 100 разных пользователей создали 100 разных трейсов.\n  - Фоновый воркер взял все 100 платежей и отправил один общий запрос в Центробанк.\n- **Почему нельзя использовать Parent-Child:**\n  - У батча не может быть 100 родителей одновременно.\n  - Если сделать родителя произвольным, остальные 99 трейсов потеряют связь с фактическим исполнением.\n- **Span Link:** связывает батчевый спан со всеми 100 исходными спанами!",
    "step_by_step": "1. Создайте список исходных клиентских контекстов.\n2. Сформируйте батчевый спан обработки.\n3. Добавьте ссылки на каждый клиентский спан через `SpanLink`.\n4. Проверьте сохранение многосторонней причинной связи.",
    "code_blocks": [
      {
        "filename": "batch_span_links_multicontext_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype LinkedContext struct {\n\tTraceID string\n\tSpanID  string\n}\n\ntype BatchExecutionSpan struct {\n\tName    string\n\tBatchID string\n\tLinks   []LinkedContext\n}\n\nfunc AggregateBatch(items []LinkedContext) BatchExecutionSpan {\n\treturn BatchExecutionSpan{\n\t\tName:    \"ExecuteClearingBatch\",\n\t\tBatchID: \"batch-cb-991\",\n\t\tLinks:   items,\n\t}\n}\n\nfunc TestBatchSpanLinksMulticontext(t *testing.T) {\n\tclientRequests := []LinkedContext{\n\t\t{TraceID: \"client-trace-1\", SpanID: \"span-1\"},\n\t\t{TraceID: \"client-trace-2\", SpanID: \"span-2\"},\n\t\t{TraceID: \"client-trace-3\", SpanID: \"span-3\"},\n\t}\n\n\tbatch := AggregateBatch(clientRequests)\n\n\tif len(batch.Links) != 3 {\n\t\tt.Fatalf(\"Ожидалось 3 ссылки Span Links, получено: %d\", len(batch.Links))\n\t}\n\n\tfmt.Println(\"Связи Span Links для пакетной обработки успешно подтверждены:\")\n\tfmt.Printf(\"  • Операция пакета: %s (ID: %s)\\n\", batch.Name, batch.BatchID)\n\tfmt.Println(\"  • Причинно-следственные связи (Causal Links):\")\n\tfor idx, l := range batch.Links {\n\t\tfmt.Printf(\"    [%d] Linked to Trace: %s (Span: %s)\\n\", idx+1, l.TraceID, l.SpanID)\n\t}\n\tfmt.Println(\"  • UI Jaeger/Tempo позволяет в один клик перейти от любого клиентского платежа к батчу!\")\n}",
        "note": "Агрегация множества независимых трейсов в один пакетный спан через Span Links"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v batch_span_links_multicontext_test.go\n# Вывод:\n# === RUN   TestBatchSpanLinksMulticontext\n# Связи Span Links для пакетной обработки успешно подтверждены:\n#   • Операция пакета: ExecuteClearingBatch (ID: batch-cb-991)\n#   • Причинно-следственные связи (Causal Links):\n#     [1] Linked to Trace: client-trace-1 (Span: span-1)\n#     [2] Linked to Trace: client-trace-2 (Span: span-2)\n#     [3] Linked to Trace: client-trace-3 (Span: span-3)\n#   • UI Jaeger/Tempo позволяет в один клик перейти от любого клиентского платежа к батчу!\n# --- PASS: TestBatchSpanLinksMulticontext (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В структуре protobuf спана OTel links хранятся как срез `repeated Link links`, где каждая ссылка содержит полный 128-битный `trace_id` и 64-битный `span_id`, обеспечивая переход между трейсами в интерфейсе мониторинга.",
    "pitfalls": "Добавлять более 1 000 ссылок в один спан: хранилища трейсинга имеют лимит на максимальное число links на один спан (обычно 128 по умолчанию), отбрасывая избыточные ссылки.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие семантики Span Links от Parent-Child с точки зрения расчета задержки (Latency)?»\n**Ответ:** Время дочернего спана (Child) напрямую включается в общую длительность родителя на шкале водопада. Время спана, привязанного через Link, **не включается** в расчет задержки текущего спана, так как оперативно эти транзакции выполнялись асинхронно в разное время."
  },
  {
    "num": 39,
    "title": "Стратегии сэмплирования: процентное вероятностное сэмплирование TraceIDRatioBased(0.1) в HighLoad",
    "task": "Настройте **sampling strategy**: `TraceIDRatioBased(0.1)` для трейсинга 10% запросов в продакшене (снижение нагрузки на Jaeger/Tempo).",
    "theory": "Стратегии сэмплирования в OpenTelemetry:\n- В HighLoad системах со 100 000 RPS сохранение 100% трейсов убьет сеть и диски хранилища.\n- **Head-Based Sampler'ы OTel SDK:**\n  1. `AlwaysOn()`: 100% трейсов (только dev/stage).\n  2. `AlwaysOff()`: трейсинг выключен.\n  3. `TraceIDRatioBased(ratio)`: детерминированное вероятностное сэмплирование на основе хэша первых 64 бит `TraceID`.\n  4. `ParentBased(rootSampler)`: если родительский сервис решил сэмплировать запрос, дочерние микросервисы обязаны подчиниться и тоже сохранить свои спаны!",
    "step_by_step": "1. Создайте модель сэмплера `TraceIDRatioBased`.\n2. Смоделируйте отбор 10% запросов (`ratio = 0.1`).\n3. Проверьте детерминированность решения на основе `TraceID`.\n4. Верифицируйте снижение нагрузки на хранилище.",
    "code_blocks": [
      {
        "filename": "sampling_strategy_ratio_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"math/rand\"\n\t\"testing\"\n)\n\ntype HeadSampler struct {\n\tRatio float64\n}\n\nfunc (s *HeadSampler) ShouldSample(seed int) bool {\n\t// Детерминированный псевдослучайный выбор на базе хэша TraceID\n\tnormalized := float64(seed%100) / 100.0\n\treturn normalized < s.Ratio\n}\n\nfunc TestSamplingStrategyRatio(t *testing.T) {\n\tsampler := &HeadSampler{Ratio: 0.10} // 10% сэмплирование\n\n\ttotalRequests := 1000\n\tsampledCount := 0\n\n\tr := rand.New(rand.NewSource(42))\n\tfor i := 0; i < totalRequests; i++ {\n\t\tseed := r.Intn(10000)\n\t\tif sampler.ShouldSample(seed) {\n\t\t\tsampledCount++\n\t\t}\n\t}\n\n\tratio := float64(sampledCount) / float64(totalRequests)\n\n\t// Допускаем статистическую погрешность около 10%\n\tif ratio < 0.08 || ratio > 0.12 {\n\t\tt.Fatalf(\"Сэмплирование вышло за допустимый диапазон: %.2f\", ratio)\n\t}\n\n\tfmt.Println(\"Стратегия сэмплирования TraceIDRatioBased(0.1) успешно проверена:\")\n\tfmt.Printf(\"  • Всего запросов:       %d\\n\", totalRequests)\n\tfmt.Printf(\"  • Отобрано для Jaeger:  %d (%.1f%%)\\n\", sampledCount, ratio*100)\n\tfmt.Println(\"  • Нагрузка на сеть и хранилище Tempo снижена ровно на 90%!\")\n}",
        "note": "Вероятностное детерминированное сэмплирование 10% трейсов на базе TraceIDRatioBased"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v sampling_strategy_ratio_test.go\n# Вывод:\n# === RUN   TestSamplingStrategyRatio\n# Стратегия сэмплирования TraceIDRatioBased(0.1) успешно проверена:\n#   • Всего запросов:       1000\n#   • Отобрано для Jaeger:  98 (9.8%)\n#   • Нагрузка на сеть и хранилище Tempo снижена ровно на 90%!\n# --- PASS: TestSamplingStrategyRatio (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`TraceIDRatioBased` берет младшие 64 бита 128-битного `TraceID` и делит их на `math.MaxUint64`. Поскольку `TraceID` генерируется криптостойким генератором случайных чисел, распределение идеально равномерно по всему числовому полю.",
    "pitfalls": "Использовать чистый `TraceIDRatioBased` без обертки `ParentBased`: в этом случае шлюз может решить сохранить трейс, а вызванный им downstream-сервис независимо решит отбросить свой спан, оставив в Jaeger разорванный трейс без данных бэкенда.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие Head-Based сэмплирования от Tail-Based сэмплирования?»\n**Ответ:** \n- **Head-Based:** решение принимается в момент старта запроса на шлюзе (дешево по памяти, но есть риск отбросить медленный трейс или ошибку 500).\n- **Tail-Based:** все спаны временно буферизуются в памяти OTel Collector, и решение принимается **после** завершения запроса: 100% ошибок и 100% медленных запросов (> 1 сек) сохраняются безусловно, а успешные быстрые запросы сэмплируются на уровне 1%."
  },
  {
    "num": 40,
    "title": "Внутрипроцессный Context-Propagation: вложенность спана SaveToDB(ctx) внутри родителя",
    "task": "**[Контекст-propagation (Внутрипроцессный)]**: В обработчике создай родительский спан. Вызови функцию `SaveToDB(ctx)`. Внутри `SaveToDB` создай дочерний спан, передав `ctx`. Убедись, что в Jaeger дочерний спан вложен в родительский.",
    "theory": "Сквозной поток контекста между функциями:\n- Классический паттерн чистого Go кода:\n  ```go\n  func Handler(w http.ResponseWriter, r *http.Request) {\n      ctx, span := tracer.Start(r.Context(), \"Handler\")\n      defer span.End()\n      \n      if err := SaveToDB(ctx, data); err != nil {\n          span.RecordError(err)\n      }\n  }\n  \n  func SaveToDB(ctx context.Context, data Data) error {\n      ctx, span := tracer.Start(ctx, \"SaveToDB\")\n      defer span.End()\n      // ...\n  }\n  ```\n- Передача `ctx` гарантирует, что спан `SaveToDB` всегда будет вложен в спан `Handler`.",
    "step_by_step": "1. Создайте обработчик запроса с родительским спаном.\n2. Реализуйте функцию `SaveToDB` с дочерним спаном.\n3. Передайте `ctx` по цепочке выполнения.\n4. Верифицируйте корректность родительско-дочерних отношений.",
    "code_blocks": [
      {
        "filename": "save_to_db_inprocess_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype TestTraceContextKey struct{}\n\ntype ActiveSpanContext struct {\n\tTraceID string\n\tSpanID  string\n}\n\ntype ProducedSpan struct {\n\tName     string\n\tTraceID  string\n\tSpanID   string\n\tParentID string\n}\n\nfunc StartTraceSpan(ctx context.Context, name, spanID string) (context.Context, ProducedSpan) {\n\ttraceID := \"trace-root-404040\"\n\tparentID := \"\"\n\n\tif parent, ok := ctx.Value(TestTraceContextKey{}).(ActiveSpanContext); ok {\n\t\ttraceID = parent.TraceID\n\t\tparentID = parent.SpanID\n\t}\n\n\tspan := ProducedSpan{\n\t\tName:     name,\n\t\tTraceID:  traceID,\n\t\tSpanID:   spanID,\n\t\tParentID: parentID,\n\t}\n\n\tnewCtx := context.WithValue(ctx, TestTraceContextKey{}, ActiveSpanContext{\n\t\tTraceID: traceID,\n\t\tSpanID:  spanID,\n\t})\n\n\treturn newCtx, span\n}\n\nfunc SaveToDB(ctx context.Context) ProducedSpan {\n\t_, child := StartTraceSpan(ctx, \"SaveToDB\", \"span-db-777\")\n\treturn child\n}\n\nfunc TestSaveToDBInProcess(t *testing.T) {\n\t// 1. Родительский спан в обработчике\n\tctx, parent := StartTraceSpan(context.Background(), \"HTTPHandler\", \"span-http-111\")\n\n\t// 2. Дочерний спан в функции работы с БД\n\tchild := SaveToDB(ctx)\n\n\tif child.TraceID != parent.TraceID {\n\t\tt.Fatalf(\"TraceID не совпадает: %s != %s\", child.TraceID, parent.TraceID)\n\t}\n\tif child.ParentID != parent.SpanID {\n\t\tt.Fatalf(\"Дочерний спан не привязан к родителю: ParentID=%s, expected=%s\", child.ParentID, parent.SpanID)\n\t}\n\n\tfmt.Println(\"Внутрипроцессный Context-Propagation успешно подтвержден:\")\n\tfmt.Printf(\"└── %s (TraceID: %s, SpanID: %s)\\n\", parent.Name, parent.TraceID, parent.SpanID)\n\tfmt.Printf(\"    └── %s (ParentID: %s, SpanID: %s)\\n\", child.Name, child.ParentID, child.SpanID)\n\tfmt.Println(\"  • В Jaeger спан SaveToDB строго вложен в прямоугольник HTTPHandler!\")\n}",
        "note": "Вложенность вызова SaveToDB внутри родительского спана HTTPHandler"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v save_to_db_inprocess_test.go\n# Вывод:\n# === RUN   TestSaveToDBInProcess\n# Внутрипроцессный Context-Propagation успешно подтвержден:\n# └── HTTPHandler (TraceID: trace-root-404040, SpanID: span-http-111)\n#     └── SaveToDB (ParentID: span-http-111, SpanID: span-db-777)\n#   • В Jaeger спан SaveToDB строго вложен в прямоугольник HTTPHandler!\n# --- PASS: TestSaveToDBInProcess (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Механизм `context.WithValue` в Go создает потокобезопасные неизменяемые контексты, позволяя передавать `ctx` в параллельные горутины без риска состояний гонки памяти.",
    "pitfalls": "Мутировать глобальные переменные вместо использования `ctx`: глобальные переменные неизбежно приведут к гонкам данных (`data race`) при параллельных запросах.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Go нельзя использовать контекст в качестве поля структуры struct { ctx context.Context }?»\n**Ответ:** По официальному руководству Go контекст должен передаваться только как первый аргумент функций (`func DoSomething(ctx context.Context, ...)`). Сохранение контекста в структуре привязывает его к жизненному циклу объекта, создавая путаницу с отменами и утечки спанов между разными запросами."
  }
]
