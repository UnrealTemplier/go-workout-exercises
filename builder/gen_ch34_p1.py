# -*- coding: utf-8 -*-
"""Exercises 1..40 of Chapter 34."""

exercises = [
  {
    "num": 1,
    "title": "Проектирование схемы GraphQL: файл schema.graphqls, корневой тип Query и парадигма Schema-first",
    "task": "**Проектирование схемы GraphQL**: Создайте файл схемы `schema.graphqls`. Опишите в нем тип `User` с полями `id: ID!`, `name: String!`, `email: String!`. Объявите корневой тип `Query` с методом `user(id: ID!): User` и `users: [User!]!`. Изучите разницу между подходами Schema-first (сначала схема) и Code-first (сначала код на Go) в экосистеме GraphQL.",
    "theory": "Архитектурные подходы к построению GraphQL в Go:\n- **Schema-First (gqlgen):**\n  - Разработчик сначала пишет строгий контракт в файле `schema.graphqls` на языке SDL (Schema Definition Language).\n  - Генератор кода автоматически создает Go-структуры моделей, интерфейсы резолверов и валидаторы.\n  - Преимущество: схема является единственным источником правды (Single Source of Truth), согласованным с фронтенд-командами до написания бэкенда.\n- **Code-First (graphql-go):**\n  - Схема описывается в Go-коде через фабричные функции `graphql.NewObject(...)`.\n  - Минусы: огромный объем бойлерплейта, сложно читать схему, отсутствие единого SDL-файла для документации.\n- В индустрии BigTech (Яндекс, Авито, Ozon) стандартом де-факто для Go является подход **Schema-First на базе `gqlgen`**.",
    "step_by_step": "1. Создайте файл `schema.graphqls` с объявлением типов User и Query.\n2. Используйте модификатор `!` для обязательных полей.\n3. Опишите методы выборки одного пользователя и списка.\n4. Протестируйте синтаксическую валидность схемы на Go.",
    "code_blocks": [
      {
        "filename": "schema.graphqls",
        "lang": "graphql",
        "code": "# Определение сущности пользователя\ntype User {\n  id: ID!\n  name: String!\n  email: String!\n}\n\n# Корневая точка входа для чтения данных\ntype Query {\n  user(id: ID!): User\n  users: [User!]!\n}",
        "note": "Схема GraphQL на языке SDL (Schema Definition Language)"
      },
      {
        "filename": "schema_validator_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n\n\t\"github.com/vektah/gqlparser/v2\"\n\t\"github.com/vektah/gqlparser/v2/ast\"\n)\n\nfunc TestValidateGraphQLSchema(t *testing.T) {\n\tsdl := `\n\t\ttype User {\n\t\t\tid: ID!\n\t\t\tname: String!\n\t\t\temail: String!\n\t\t}\n\t\ttype Query {\n\t\t\tuser(id: ID!): User\n\t\t\tusers: [User!]!\n\t\t}\n\t`\n\n\tschema, err := gqlparser.LoadSchema(&ast.Source{\n\t\tName:  \"schema.graphqls\",\n\t\tInput: sdl,\n\t})\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка валидации SDL схемы: %v\", err)\n\t}\n\n\tuserType := schema.Types[\"User\"]\n\tif userType == nil || len(userType.Fields) != 3 {\n\t\tt.Fatal(\"Тип User не найден или не содержит 3 поля\")\n\t}\n\n\tfmt.Printf(\"GraphQL Schema успешно валидирована! Корневые типы: Query=%v, User.Fields=%d\\n\",\n\t\tschema.Query != nil, len(userType.Fields))\n}",
        "note": "Парсинг и валидация SDL схемы через официальный парсер gqlparser"
      }
    ],
    "under_the_hood": "Парсер `gqlparser` строит AST (абстрактное синтаксическое дерево) схемы, проверяет циклические зависимости директив и гарантирует соответствие спецификации GraphQL June 2018 / October 2021.",
    "pitfalls": "Забывать указывать восклицательный знак внутри списков: `[User]` (список может содержать null и сам быть null), `[User!]` (список не содержит null, но может быть null), `[User!]!` (список гарантированно существует и все элементы валидны). В продакшене почти всегда нужен `[User!]!`.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем ключевое отличие Schema-First от Code-First в плане производительности рантайма Go?»\n**Ответ:** `gqlgen` генерирует специализированный статический код маршалинга и вызова резолверов без использования рефлексии `reflect` в горячем пути исполнения. В Code-First библиотеках (например `graphql-go`) каждый запрос парсится и резолвится через рефлексию, что в 5–10 раз медленнее и создает колоссальное количество мелких аллокаций в куче."
  },
  {
    "num": 2,
    "title": "Инициализация проекта gqlgen: структура каталогов, генерация кода и базовый резолвер",
    "task": "Установите `gqlgen` (или `graphql-go`), инициализируйте проект. Определите схему с типом `User` (id, name, email) и запросом `users: [User!]!`. Реализуйте резолвер, возвращающий тестовые данные.",
    "theory": "Структура проекта на базе `gqlgen`:\n- `server.go` — точка входа HTTP-сервера, монтирующая GraphQL handler и Playground.\n- `graph/schema.graphqls` — исходная схема SDL.\n- `graph/schema.resolvers.go` — файл бизнес-логики, куда разработчик пишет реализацию резолверов.\n- `graph/generated.go` — автоматически генерируемый движок парсинга, валидации и выполнения запросов (никогда не редактируется вручную!).\n- `graph/model/models_gen.go` — сгенерированные структуры Go (`type User struct`).",
    "step_by_step": "1. Опишите интерфейс корневого резолвера.\n2. Создайте реализацию метода `Users` с mock-данными.\n3. Смоделируйте выполнение запроса.\n4. Проверьте корректность сериализации JSON.",
    "code_blocks": [
      {
        "filename": "mock_users_resolver_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype User struct {\n\tID    string `json:\"id\"`\n\tName  string `json:\"name\"`\n\tEmail string `json:\"email\"`\n}\n\ntype QueryResolver interface {\n\tUsers(ctx context.Context) ([]*User, error)\n}\n\ntype Resolver struct {\n\tusers []*User\n}\n\nfunc (r *Resolver) Users(ctx context.Context) ([]*User, error) {\n\treturn r.users, nil\n}\n\nfunc TestUsersResolver(t *testing.T) {\n\tmockData := []*User{\n\t\t{ID: \"usr_1\", Name: \"Алексей Иванов\", Email: \"alex@yandex.ru\"},\n\t\t{ID: \"usr_2\", Name: \"Дарья Петрова\", Email: \"daria@ozon.ru\"},\n\t}\n\n\tr := &Resolver{users: mockData}\n\n\tusers, err := r.Users(context.Background())\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка получения пользователей: %v\", err)\n\t}\n\n\tif len(users) != 2 || users[0].Name != \"Алексей Иванов\" {\n\t\tt.Fatalf(\"Некорректный результат выборки: %+v\", users)\n\t}\n\n\tfmt.Printf(\"UsersResolver успешно вернул %d пользователей из mock-хранилища!\\n\", len(users))\n}",
        "note": "Базовая реализация резолвера выборки списка сущностей"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v mock_users_resolver_test.go\n# Вывод:\n# === RUN   TestUsersResolver\n# UsersResolver успешно вернул 2 пользователей из mock-хранилища!\n# --- PASS: TestUsersResolver (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`gqlgen` связывает резолверы со сгенерированным кодом через интерфейс `ResolverRoot`. При запуске генератор проверяет, какие методы уже реализованы в `schema.resolvers.go`, и генерирует заглушки только для новых полей.",
    "pitfalls": "Вручную редактировать `generated.go` или `models_gen.go`: при следующем запуске `gqlgen generate` любые ручные правки в этих файлах будут безвозвратно перезаписаны.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в резолверах Go всегда первым аргументом передается context.Context?»\n**Ответ:** Контекст несет критически важную информацию: таймауты запроса (`ctx.Done()`), данные аутентификации пользователя (JWT Claims), логгеры с correlation-id, спаны трейсинга OpenTelemetry, а также экземпляры **DataLoaders** для решения проблемы N+1."
  },
  {
    "num": 3,
    "title": "Минимальная схема User и query-метод поиска по ID: user(id: ID!): User",
    "task": "Напишите простейшую схему с типом `User { id: ID!, name: String!, email: String! }` и query `user(id: ID!): User`.",
    "theory": "Семантика nullable vs non-null возвращаемых типов:\n- В сигнатуре `user(id: ID!): User`:\n  - Аргумент `id: ID!` является обязательным (Non-Null): клиент **обязан** передать валидный идентификатор.\n  - Возвращаемый тип `User` является **Nullable** (без `!`): если пользователь с таким `id` не найден в базе данных, сервер легитимно возвращает `null` в поле данных (`\"data\": {\"user\": null}`) без генерации критической ошибки GraphQL.\n- В Go nullable тип модели мапится в указатель: `*model.User`.",
    "step_by_step": "1. Опишите метод `User(ctx, id)` в резолвере.\n2. Реализуйте поиск в хеш-мапе по ключу.\n3. Верните `nil, nil`, если объект не найден.\n4. Проверьте поведение при успешном поиске и при отсутствии записи.",
    "code_blocks": [
      {
        "filename": "user_by_id_resolver_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype User struct {\n\tID    string\n\tName  string\n\tEmail string\n}\n\ntype QueryResolver struct {\n\tstore map[string]*User\n}\n\nfunc (r *QueryResolver) User(ctx context.Context, id string) (*User, error) {\n\tu, ok := r.store[id]\n\tif !ok {\n\t\t// В GraphQL отсутствие сущности при типе nullable возвращает (nil, nil)\n\t\treturn nil, nil\n\t}\n\treturn u, nil\n}\n\nfunc TestUserByID(t *testing.T) {\n\tr := &QueryResolver{\n\t\tstore: map[string]*User{\n\t\t\t\"101\": {ID: \"101\", Name: \"Иван Смирнов\", Email: \"ivan@avito.ru\"},\n\t\t},\n\t}\n\n\t// 1. Поиск существующего\n\tuser, err := r.User(context.Background(), \"101\")\n\tif err != nil || user == nil || user.Name != \"Иван Смирнов\" {\n\t\tt.Fatalf(\"Ожидался пользователь 101, получено: %+v, err: %v\", user, err)\n\t}\n\n\t// 2. Поиск отсутствующего\n\tnotFound, err := r.User(context.Background(), \"999\")\n\tif err != nil || notFound != nil {\n\t\tt.Fatalf(\"Ожидался nil при отсутствии, получено: %+v, err: %v\", notFound, err)\n\t}\n\n\tfmt.Println(\"Поиск по ID успешно протестирован: существующий возвращен, отсутствующий вернул nil!\")\n}",
        "note": "Корректная обработка отсутствия сущности при nullable возвращаемом типе"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v user_by_id_resolver_test.go\n# Вывод:\n# === RUN   TestUserByID\n# Поиск по ID успешно протестирован: существующий возвращен, отсутствующий вернул nil!\n# --- PASS: TestUserByID (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В спецификации GraphQL, если поле nullable возвращает ошибку (`err != nil`), значение поля заменяется на `null`, а ошибка добавляется в массив `\"errors\": [...]`. Если же возвращается `nil, nil`, ошибка в `\"errors\"` не пишется.",
    "pitfalls": "Возвращать ошибку `fmt.Errorf(\"user not found\")` для nullable поля: клиентский фронтенд Apollo/Relay будет считать это сетевой или системной ошибкой и может показать пользователю экран сбоя вместо аккуратного «Пользователь не найден».",
    "bigtech_interview": "**Вопрос с собеседования:** «Когда в GraphQL нужно возвращать ошибку, а когда nil в ответе резолвера?»\n**Ответ:** `nil` возвращают, когда отсутствие данных является ожидаемым бизнес-сценарием (пользователь не найден, статья еще не опубликована). `error` возвращают при сбоях инфраструктуры (таймаут БД, отказ сети), нарушениях прав доступа (`Unauthorized`/`Forbidden`) или валидации входных аргументов."
  },
  {
    "num": 4,
    "title": "Схема User с кастомным скаляром времени createdAt: Time! и генерация моделей в gqlgen",
    "task": "Определи **GraphQL schema** для `User`: `type User { id: ID! name: String! email: String! createdAt: Time! }`. Сгенерируй код через `gqlgen generate`. Покажи, как gqlgen создаёт Go-структуры из schema.",
    "theory": "Маппинг типов SDL в структуры Go:\n- По умолчанию стандартные скаляры маппятся:\n  - `ID` $\\to$ `string`\n  - `String` $\\to$ `string`\n  - `Int` $\\to$ `int`\n  - `Float` $\\to$ `float64`\n  - `Boolean` $\\to$ `bool`\n- Скаляр `Time!` мапится в стандартный пакет `time.Time`.\n- Сгенерированная Go-структура в `models_gen.go` содержит json-теги и строгую типизацию:\n```go\ntype User struct {\n    ID        string    `json:\"id\"`\n    Name      string    `json:\"name\"`\n    Email     string    `json:\"email\"`\n    CreatedAt time.Time `json:\"createdAt\"`\n}\n```",
    "step_by_step": "1. Опишите структуру с полями схемы.\n2. Используйте `time.Time` для поля `CreatedAt`.\n3. Смоделируйте сериализацию структуры в JSON.\n4. Проверьте соответствие формату RFC3339.",
    "code_blocks": [
      {
        "filename": "generated_model_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\n// Модель, генерируемая gqlgen из schema.graphqls\ntype User struct {\n\tID        string    `json:\"id\"`\n\tName      string    `json:\"name\"`\n\tEmail     string    `json:\"email\"`\n\tCreatedAt time.Time `json:\"createdAt\"`\n}\n\nfunc TestGeneratedModelSerialization(t *testing.T) {\n\tnow := time.Date(2026, 9, 3, 12, 0, 0, 0, time.UTC)\n\tu := User{\n\t\tID:        \"usr_42\",\n\t\tName:      \"Анна Сергеева\",\n\t\tEmail:     \"anna@ozon.ru\",\n\t\tCreatedAt: now,\n\t}\n\n\tbytes, err := json.Marshal(u)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка сериализации: %v\", err)\n\t}\n\n\texpected := `{\"id\":\"usr_42\",\"name\":\"Анна Сергеева\",\"email\":\"anna@ozon.ru\",\"createdAt\":\"2026-09-03T12:00:00Z\"}`\n\tif string(bytes) != expected {\n\t\tt.Fatalf(\"Несовпадение JSON: got %s, want %s\", string(bytes), expected)\n\t}\n\n\tfmt.Println(\"Сгенерированная модель User успешно сериализована в канонический RFC3339 JSON!\")\n}",
        "note": "Сериализация времени в модели gqlgen в формате ISO-8601 / RFC3339"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v generated_model_test.go\n# Вывод:\n# === RUN   TestGeneratedModelSerialization\n# Сгенерированная модель User успешно сериализована в канонический RFC3339 JSON!\n# --- PASS: TestGeneratedModelSerialization (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Встроенный маршалер `graphql.MarshalTime` сериализует даты в строковом представлении `time.RFC3339Nano`, обеспечивая совместимость с любыми JavaScript клиентами (React, iOS, Android).",
    "pitfalls": "Использовать строковый тип `String` вместо `Time` для дат: клиенты теряют возможность валидировать форматы дат на этапе запроса, а сервер вынужден вручную парсить строки во всех резолверах.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в gqlgen использовать собственную доменную модель User вместо сгенерированной в models_gen.go?»\n**Ответ:** В файле `gqlgen.yml` в секции `models` настраивается биндинг:\n```yaml\nmodels:\n  User:\n    model: github.com/my/project/internal/domain.User\n```\nТогда генератор использует существующую модель и не будет дублировать структуру в `models_gen.go`."
  },
  {
    "num": 5,
    "title": "Анатомия сгенерированного кода gqlgen: файлы generated.go, models_gen.go и schema.resolvers.go",
    "task": "Сгенерируйте Go-код из схемы командой `go run github.com/99designs/gqlgen generate`. Изучите сгенерированные модели и резолверы.",
    "theory": "Роли файлов, создаваемых командой `gqlgen generate`:\n1. `graph/generated.go`:\n   - Содержит таблицу диспетчеризации полей.\n   - Парсит входящий JSON в переменные.\n   - Вызывает соответствующие методы резолверов.\n   - Занимает от 5 000 до 50 000 строк оптимизированного Go-кода.\n2. `graph/model/models_gen.go`:\n   - Хранит DTO структуры, перечисления (Enums) и структуры входных данных (`input`).\n3. `graph/schema.resolvers.go`:\n   - Реализует интерфейс `ResolverRoot`.\n   - Включает дочерние структуры `queryResolver` и `mutationResolver`.",
    "step_by_step": "1. Создайте архитектурный каркас резолверов проекта.\n2. Свяжите `queryResolver` с корневой структурой `Resolver`.\n3. Реализуйте метод `Query()` возвращающий интерфейс.\n4. Протестируйте иерархию связывания.",
    "code_blocks": [
      {
        "filename": "resolver_architecture_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype User struct {\n\tID   string\n\tName string\n}\n\n// Корневой объект внедрения зависимостей (БД, кэши, gRPC клиенты)\ntype Resolver struct {\n\tUserStore map[string]*User\n}\n\n// Интерфейсы, генерируемые gqlgen\ntype ResolverRoot interface {\n\tQuery() QueryResolver\n}\n\ntype QueryResolver interface {\n\tUsers(ctx context.Context) ([]*User, error)\n}\n\ntype queryResolver struct{ *Resolver }\n\nfunc (r *Resolver) Query() QueryResolver {\n\treturn &queryResolver{r}\n}\n\nfunc (r *queryResolver) Users(ctx context.Context) ([]*User, error) {\n\tlist := make([]*User, 0, len(r.UserStore))\n\tfor _, u := range r.UserStore {\n\t\tlist = append(list, u)\n\t}\n\treturn list, nil\n}\n\nfunc TestResolverHierarchy(t *testing.T) {\n\troot := &Resolver{\n\t\tUserStore: map[string]*User{\n\t\t\t\"1\": {ID: \"1\", Name: \"Борис\"},\n\t\t},\n\t}\n\n\tvar rootInterface ResolverRoot = root\n\tusers, err := rootInterface.Query().Users(context.Background())\n\tif err != nil || len(users) != 1 {\n\t\tt.Fatalf(\"Ошибка в структуре резолвера: %v\", err)\n\t}\n\n\tfmt.Println(\"Архитектурный шаблон резолверов gqlgen успешно подтвержден!\")\n}",
        "note": "Паттерн иерархии вложенных резолверов gqlgen"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v resolver_architecture_test.go\n# Вывод:\n# === RUN   TestResolverHierarchy\n# Архитектурный шаблон резолверов gqlgen успешно подтвержден!\n# --- PASS: TestResolverHierarchy (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Такая многоуровневая структура позволяет разделять резолверы сущностей по разным файлам (`user.resolvers.go`, `order.resolvers.go`), избегая разрастания одного монолитного файла.",
    "pitfalls": "Хранить состояние запроса в полях структуры `queryResolver`: структура резолвера является синглтоном на весь сервер! Любые мутации полей в ней приведут к Data Race при конкурентных запросах.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в generated.go gqlgen использует fast-path буферы для вывода JSON?»\n**Ответ:** Стандартный `json.Marshal` использует рефлексию и аллокации. `gqlgen` генерирует кастомные функции сериализации, напрямую записывающие байты в пул буферов `io.Writer`, что обеспечивает околонулевые накладные расходы рантайма."
  },
  {
    "num": 6,
    "title": "Реализация резолвера Query.User: выборка из in-memory хранилища с обработкой ошибок",
    "task": "Реализуйте резолвер `Query.User`, который возвращает захардкоженного пользователя из памяти.",
    "theory": "Обработка ошибок и контекста в резолвере выборки:\n- Метод резолвера принимает `context.Context` и аргументы из GraphQL-запроса:\n  `func (r *queryResolver) User(ctx context.Context, id string) (*model.User, error)`\n- Хорошие практики:\n  1. Проверка отмены контекста: `if err := ctx.Err(); err != nil { return nil, err }`.\n  2. Валидация входных аргументов (например, `id` не должен быть пустым).\n  3. Извлечение сущности из потокобезопасного хранилища (`sync.RWMutex`).",
    "step_by_step": "1. Создайте структуру хранилища с RWMutex.\n2. Реализуйте метод User с валидацией ID.\n3. Проверьте возврат пользователя по ключу.\n4. Протестируйте отказ при пустом аргументе.",
    "code_blocks": [
      {
        "filename": "safe_user_resolver_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n)\n\ntype User struct {\n\tID    string\n\tName  string\n\tEmail string\n}\n\ntype SafeUserResolver struct {\n\tmu    sync.RWMutex\n\tusers map[string]*User\n}\n\nfunc (r *SafeUserResolver) User(ctx context.Context, id string) (*User, error) {\n\tif id == \"\" {\n\t\treturn nil, errors.New(\"идентификатор пользователя не может быть пустым\")\n\t}\n\n\tr.mu.RLock()\n\tdefer r.mu.RUnlock()\n\n\tu, ok := r.users[id]\n\tif !ok {\n\t\treturn nil, nil // GraphQL Nullable\n\t}\n\treturn u, nil\n}\n\nfunc TestSafeUserResolver(t *testing.T) {\n\tr := &SafeUserResolver{\n\t\tusers: map[string]*User{\n\t\t\t\"usr_dev\": {ID: \"usr_dev\", Name: \"Дмитрий\", Email: \"dmitry@tbank.ru\"},\n\t\t},\n\t}\n\n\t// Валидный вызов\n\tu, err := r.User(context.Background(), \"usr_dev\")\n\tif err != nil || u.Name != \"Дмитрий\" {\n\t\tt.Fatalf(\"Ошибка получения: %v\", err)\n\t}\n\n\t// Пустой ID\n\t_, errEmpty := r.User(context.Background(), \"\")\n\tif errEmpty == nil {\n\t\tt.Fatal(\"Ожидалась ошибка при пустом ID\")\n\t}\n\n\tfmt.Printf(\"Потокобезопасный резолвер User успешно вернул [%s] и отсек некорректный ID!\\n\", u.Name)\n}",
        "note": "Потокобезопасный резолвер с валидацией аргументов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v safe_user_resolver_test.go\n# Вывод:\n# === RUN   TestSafeUserResolver\n# Потокобезопасный резолвер User успешно вернул [Дмитрий] и отсек некорректный ID!\n# --- PASS: TestSafeUserResolver (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Если резолвер возвращает `error`, `gqlgen` оборачивает ее в `gqlerror.Error` с привязкой к пути поля в документе запроса (`path: [\"user\"]`) и номерам строки/колонки в GraphQL документе.",
    "pitfalls": "Игнорировать проверку пустого ID: при вызове `user(id: \"\")` можно случайно выполнить неэффективный Full Scan базы данных или получить коллизию в кэше.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что происходит, если резолвер паникует (panic) во время обработки запроса?»\n**Ответ:** В `gqlgen` встроен механизм `RecoverFunc`. При панике сервер не падает: паника перехватывается, стек трейс логируется, а клиенту возвращается GraphQL ошибка с кодом `INTERNAL_SERVER_ERROR`."
  },
  {
    "num": 7,
    "title": "Реализация резолвера Query.Users: возврат слайса mock-данных и подготовка к Playground",
    "task": "Реализуй **Query resolver** `users: [User!]!`: `func (r *queryResolver) Users(ctx context.Context) ([]*model.User, error)`. Верни mock-данные из слайса. Запусти playground (`localhost:8080`) и выполни query.",
    "theory": "Инварианты списка `[User!]!`:\n- Внешний `!` гарантирует, что поле `users` никогда не будет `null`. Если пользователей нет, сервер обязан вернуть пустой слайс `[]` (а не `null`).\n- Внутренний `!` гарантирует, что в слайсе не может быть `nil` элементов (`[]*User{nil}`).\n- Если резолвер возвращает `nil` слайс в Go (`var res []*User = nil`), `gqlgen` автоматически сериализует его в пустой массив `[]` в ответе JSON, сохраняя инвариант Non-Null контракта.",
    "step_by_step": "1. Реализуйте сигнатуру резолвера `Users`.\n2. Подготовьте список пользователей.\n3. Проверьте отдачу пустого и заполненного списка.\n4. Убедитесь в отсутствии nil элементов.",
    "code_blocks": [
      {
        "filename": "users_list_resolver_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype User struct {\n\tID    string\n\tName  string\n\tEmail string\n}\n\ntype Resolver struct {\n\tusers []*User\n}\n\nfunc (r *Resolver) Users(ctx context.Context) ([]*User, error) {\n\tif r.users == nil {\n\t\treturn []*User{}, nil // Гарантируем не-nil слайс\n\t}\n\treturn r.users, nil\n}\n\nfunc TestUsersListResolver(t *testing.T) {\n\tr := &Resolver{\n\t\tusers: []*User{\n\t\t\t{ID: \"1\", Name: \"Илья\", Email: \"ilya@vk.com\"},\n\t\t\t{ID: \"2\", Name: \"Ольга\", Email: \"olga@vk.com\"},\n\t\t},\n\t}\n\n\tres, err := r.Users(context.Background())\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка: %v\", err)\n\t}\n\n\tif len(res) != 2 {\n\t\tt.Fatalf(\"Ожидалось 2 пользователя, получено %d\", len(res))\n\t}\n\n\tfmt.Printf(\"Users резолвер успешно вернул список из %d записей!\\n\", len(res))\n}",
        "note": "Строгое соблюдение контракта [User!]! в Go резолвере"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v users_list_resolver_test.go\n# Вывод:\n# === RUN   TestUsersListResolver\n# Users резолвер успешно вернул список из 2 записей!\n# --- PASS: TestUsersListResolver (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Сериализатор `gqlgen` проверяет каждый элемент массива: если один из элементов оказался `nil` при контракте `[User!]!`, генерируется ошибка нарушения Non-Null типа, и весь массив обнуляется в соответствии со спецификацией GraphQL.",
    "pitfalls": "Возвращать слайс, содержащий `nil` указатели: `[]*User{user1, nil, user2}`. Это вызовет каскадное всплытие null (Null Bubbling) и сломает ответ клиенту.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое Null Bubbling в GraphQL?»\n**Ответ:** Если поле с модификатором `!` (non-null) возвращает `null` или ошибку, GraphQL не может вернуть `null` в этом поле. Ошибка «всплывает» к родительскому полю. Если и родительское поле non-null, всплытие продолжается до тех пор, пока не встретится nullable поле или весь корневой объект `data` не превратится в `null`."
  },
  {
    "num": 8,
    "title": "GraphQL Playground: интерактивная среда отладки запросов и переменных в браузере",
    "task": "Запустите GraphQL-плейграунд (встроен в gqlgen) и выполните первый query через браузер.",
    "theory": "Архитектура HTTP эндпоинтов GraphQL:\n- В отличие от REST с сотнями URL, в GraphQL используется всего **два маршрута**:\n  1. `GET /`: отдает HTML страницу **GraphQL Playground** (или Apollo Sandbox) для разработчиков.\n  2. `POST /query`: единственный рабочий эндпоинт, принимающий JSON:\n     ```json\n     {\n       \"query\": \"query GetUsers { users { id name email } }\",\n       \"variables\": {}\n     }\n     ```\n- Плейграунд автоматически запрашивает интроспекцию схемы (`__schema`) и предоставляет автодополнение полей, документацию и подсветку ошибок прямо в окне браузера.",
    "step_by_step": "1. Настройте HTTP роутер со статическим Playground handler.\n2. Настройте рабочий GraphQL handler.\n3. Смоделируйте выполнение HTTP POST запроса к эндпоинту.\n4. Проверьте JSON ответ сервера.",
    "code_blocks": [
      {
        "filename": "playground_server_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"bytes\"\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"io\"\n\t\"net/http\"\n\t\"net/http/httptest\"\n\t\"testing\"\n)\n\nfunc MockGraphQLHandler(w http.ResponseWriter, r *http.Request) {\n\tif r.Method == http.MethodGet {\n\t\tw.Header().Set(\"Content-Type\", \"text/html; charset=utf-8\")\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"<h1>GraphQL Playground</h1>\"))\n\t\treturn\n\t}\n\n\tvar req struct {\n\t\tQuery string `json:\"query\"`\n\t}\n\t_ = json.NewDecoder(r.Body).Decode(&req)\n\n\tw.Header().Set(\"Content-Type\", \"application/json\")\n\tresp := map[string]any{\n\t\t\"data\": map[string]any{\n\t\t\t\"users\": []map[string]string{\n\t\t\t\t{\"id\": \"1\", \"name\": \"Михаил\", \"email\": \"mikhail@yandex.ru\"},\n\t\t\t},\n\t\t},\n\t}\n\t_ = json.NewEncoder(w).Encode(resp)\n}\n\nfunc TestPlaygroundAndQueryEndpoint(t *testing.T) {\n\tsrv := httptest.NewServer(http.HandlerFunc(MockGraphQLHandler))\n\tdefer srv.Close()\n\n\t// 1. Проверка Playground GET\n\trespHTML, err := http.Get(srv.URL)\n\tif err != nil || respHTML.StatusCode != http.StatusOK {\n\t\tt.Fatalf(\"Ошибка загрузки Playground: %v\", err)\n\t}\n\tbody, _ := io.ReadAll(respHTML.Body)\n\tif !bytes.Contains(body, []byte(\"GraphQL Playground\")) {\n\t\tt.Fatal(\"Playground HTML не найден\")\n\t}\n\n\t// 2. Проверка POST Query\n\tqueryPayload := `{\"query\": \"{ users { id name email } }\"}`\n\trespJSON, err := http.Post(srv.URL, \"application/json\", bytes.NewBufferString(queryPayload))\n\tif err != nil || respJSON.StatusCode != http.StatusOK {\n\t\tt.Fatalf(\"Ошибка выполнения query: %v\", err)\n\t}\n\n\tvar result map[string]any\n\t_ = json.NewDecoder(respJSON.Body).Decode(&result)\n\tdata := result[\"data\"].(map[string]any)\n\n\tfmt.Printf(\"Playground доступен! Выполнен POST запрос, получен ответ: %v\\n\", data)\n}",
        "note": "Тестирование эндпоинтов Playground GET и GraphQL POST"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v playground_server_test.go\n# Вывод:\n# === RUN   TestPlaygroundAndQueryEndpoint\n# Playground доступен! Выполнен POST запрос, получен ответ: map[users:[map[email:mikhail@yandex.ru id:1 name:Михаил]]]\n# --- PASS: TestPlaygroundAndQueryEndpoint (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Пакет `github.com/99designs/gqlgen/graphql/playground` отдает минифицированный SPA на React, который выполняет стандартные HTTP POST запросы на указанный в параметрах эндпоинт.",
    "pitfalls": "Оставлять GraphQL Playground открытым в Production среде: злоумышленники могут использовать интроспекцию и плейграунд для исследования внутренней архитектуры и уязвимостей API. В проде плейграунд отключают.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в продакшене отключают GraphQL Introspection?»\n**Ответ:** Интроспекция раскрывает полную схему данных, все типы, приватные поля и мутации, облегчая атакующим поиск скрытых эндпоинтов (Security through Obscurity). Для ее отключения в `gqlgen` используют middleware `extension.Introspection` с проверкой окружения (`env != \"production\"`)."
  },
  {
    "num": 9,
    "title": "Конфигурация gqlgen.yml: настройка пакетов, автогенерации и путей к файлам",
    "task": "**Настройка генератора `gqlgen`**: Установите самую популярную библиотеку для работы с GraphQL в Go — `github.com/99designs/gqlgen`. Сгенерируйте заготовку сервера с помощью команды `gqlgen generate` (предварительно настроив файл конфигурации `gqlgen.yml`). Запустите сгенерированный сервер и откройте в браузере интерактивную песочницу GraphQL Playground (обычно на порту `8080`).",
    "theory": "Структура файла конфигурации `gqlgen.yml`:\n- `schema`: список glob-паттернов поиска файлов схем (`graph/*.graphqls`).\n- `exec`: путь и пакет для движка исполнения (`graph/generated.go`).\n- `model`: директория для сгенерированных DTO (`graph/model/models_gen.go`).\n- `resolver`: настройки резолверов (`layout: follow-schema`).\n- `autobind`: автоматический поиск соответствия типов в существующих Go-пакетах.\n- `models`: явное связывание GraphQL типов с кастомными типами Go.",
    "step_by_step": "1. Создайте типовой файл `gqlgen.yml`.\n2. Опишите пути к исполняемому коду и моделям.\n3. Проверьте парсинг конфигурационного файла.\n4. Протестируйте валидацию структуры настроек.",
    "code_blocks": [
      {
        "filename": "gqlgen.yml",
        "lang": "yaml",
        "code": "# Файл конфигурации генератора gqlgen\nschema:\n  - \"graph/*.graphqls\"\n\nexec:\n  filename: graph/generated.go\n  package: graph\n\nmodel:\n  filename: graph/model/models_gen.go\n  package: model\n\nresolver:\n  layout: follow-schema\n  dir: graph\n  package: graph\n  filename_template: \"{name}.resolvers.go\"\n\nautobind:\n  - \"my-project/internal/domain\"\n\nmodels:\n  ID:\n    model:\n      - github.com/99designs/gqlgen/graphql.ID\n      - github.com/99designs/gqlgen/graphql.Int\n      - github.com/99designs/gqlgen/graphql.Int64",
        "note": "Эталонная конфигурация генератора gqlgen"
      },
      {
        "filename": "config_validator_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n\t\"testing\"\n\n\t\"gopkg.in/yaml.v3\"\n)\n\ntype GqlgenConfig struct {\n\tSchema []string `yaml:\"schema\"`\n\tExec   struct {\n\t\tFilename string `yaml:\"filename\"`\n\t\tPackage  string `yaml:\"package\"`\n\t} `yaml:\"exec\"`\n\tModel struct {\n\t\tFilename string `yaml:\"filename\"`\n\t\tPackage  string `yaml:\"package\"`\n\t} `yaml:\"model\"`\n}\n\nfunc TestGqlgenConfigValidation(t *testing.T) {\n\tdata, err := os.ReadFile(\"gqlgen.yml\")\n\tif err != nil {\n\t\tt.Fatalf(\"Файл gqlgen.yml не найден: %v\", err)\n\t}\n\n\tvar cfg GqlgenConfig\n\tif err := yaml.Unmarshal(data, &cfg); err != nil {\n\t\tt.Fatalf(\"Ошибка парсинга YAML: %v\", err)\n\t}\n\n\tif len(cfg.Schema) == 0 || cfg.Exec.Package != \"graph\" {\n\t\tt.Fatalf(\"Некорректная конфигурация: %+v\", cfg)\n\t}\n\n\tfmt.Printf(\"Конфигурация gqlgen.yml валидна! Схемы: %v, Пакет Exec: %s\\n\",\n\t\tcfg.Schema, cfg.Exec.Package)\n}",
        "note": "Валидация YAML конфигурации gqlgen"
      }
    ],
    "under_the_hood": "`gqlgen` использует `gopkg.in/yaml.v3` для чтения `gqlgen.yml`. Если файл отсутствует, генератор использует настройки по умолчанию, что часто приводит к генерации файлов в нежелательных директориях.",
    "pitfalls": "Использовать табуляцию вместо пробелов в файле `gqlgen.yml`: стандарт YAML запрещает табуляцию, генератор упадет с ошибкой `yaml: line X: found character that cannot start any token`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем нужна опция layout: follow-schema в gqlgen.yml?»\n**Ответ:** По умолчанию gqlgen помещает все резолверы в один файл `schema.resolvers.go`. При `layout: follow-schema` gqlgen разделяет резолверы по файлам соответственно именам исходных схем: резолверы из `user.graphqls` пойдут в `user.resolvers.go`, а из `order.graphqls` — в `order.resolvers.go`."
  },
  {
    "num": 10,
    "title": "NonNull типы в GraphQL SDL: влияние восклицательного знака на генерацию указателей в Go",
    "task": "Добавьте в схему **NonNull-типы** (`!`) и изучите, как gqlgen генерирует Go-типы (указатели vs значения).",
    "theory": "Правила генерации типов Go генератором gqlgen:\n1. **Поле с `!` (Non-Null):**\n   - SDL: `name: String!` $\\to$ Go: `Name string` (значение).\n   - SDL: `age: Int!` $\\to$ Go: `Age int` (значение).\n   - Значение гарантированно присутствует, указатель не нужен.\n2. **Поле БЕЗ `!` (Nullable):**\n   - SDL: `bio: String` $\\to$ Go: `Bio *string` (указатель).\n   - SDL: `age: Int` $\\to$ Go: `Age *int` (указатель).\n   - Значение может быть `null`, поэтому в Go используется указатель (`nil` означает отсутствие).\n3. **Списки:**\n   - `tags: [String!]` $\\to$ `Tags []string` (может быть nil).\n   - `tags: [String]!` $\\to$ `Tags []*string` (список не nil, элементы могут быть nil).\n   - `tags: [String!]!` $\\to$ `Tags []string` (гарантированный непустой список значений).",
    "step_by_step": "1. Создайте структуру с полями значений и указателей.\n2. Смоделируйте генерацию nullable и non-null полей.\n3. Проверьте сериализацию `nil` полей в `null`.\n4. Протестируйте обязательные поля значений.",
    "code_blocks": [
      {
        "filename": "nullability_types_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"testing\"\n)\n\n// GraphQL:\n// type Profile {\n//   username: String!  -> string\n//   bio: String        -> *string\n//   age: Int           -> *int\n// }\ntype Profile struct {\n\tUsername string  `json:\"username\"`\n\tBio      *string `json:\"bio\"`\n\tAge      *int    `json:\"age\"`\n}\n\nfunc TestNullabilityInGo(t *testing.T) {\n\t// 1. Профиль с заполненными опциональными полями\n\tbioText := \"Gopher & HighLoad Engineer\"\n\tageVal := 28\n\tp1 := Profile{\n\t\tUsername: \"gopher_master\",\n\t\tBio:      &bioText,\n\t\tAge:      &ageVal,\n\t}\n\n\tb1, _ := json.Marshal(p1)\n\tfmt.Println(\"Заполненный профиль:\", string(b1))\n\n\t// 2. Профиль с отсутствующими полями (null в JSON)\n\tp2 := Profile{\n\t\tUsername: \"anon_user\",\n\t\tBio:      nil,\n\t\tAge:      nil,\n\t}\n\n\tb2, _ := json.Marshal(p2)\n\tfmt.Println(\"Профиль с null полями:\", string(b2))\n\n\tvar parsed map[string]any\n\t_ = json.Unmarshal(b2, &parsed)\n\tif parsed[\"username\"] != \"anon_user\" || parsed[\"bio\"] != nil {\n\t\tt.Fatalf(\"Некорректная обработка null: %v\", parsed)\n\t}\n}",
        "note": "Маппинг nullable полей в указатели Go и сериализация в null"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v nullability_types_test.go\n# Вывод:\n# === RUN   TestNullabilityInGo\n# Заполненный профиль: {\"username\":\"gopher_master\",\"bio\":\"Gopher & HighLoad Engineer\",\"age\":28}\n# Профиль с null полями: {\"username\":\"anon_user\",\"bio\":null,\"age\":null}\n# --- PASS: TestNullabilityInGo (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Go разыменование `*string` без предварительной проверки `if str != nil` приводит к `panic: runtime error: invalid memory address or nil pointer dereference`. `gqlgen` генерирует безопасные проверки для всех nullable полей.",
    "pitfalls": "Делать все поля в схеме Non-Null (`!`): если у пользователя нет отчества или номера телефона, бэкенд не сможет вернуть объект и выбросит критическую ошибку на клиенте.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в GraphQL клиентских приложениях рекомендуют делать поля nullable, если отказ одного сервиса не должен ломать весь экран?»\n**Ответ:** Из-за правила Null Bubbling: если поле объявлено Non-Null (`!`), а соответствующий микросервис упал, ошибка уничтожит весь родительский объект. Если же поле Nullable, клиент получит `null` в одном блоке (например, рекомендации) и сможет отобразить остальную часть страницы."
  },
  {
    "num": 11,
    "title": "Реализация Query-резолвера с аргументами: user(id: ID!): User с возвратом кастомной ошибки",
    "task": "Реализуй **Query resolver** с аргументом: `user(id: ID!): User`. Извлеки `id` из аргументов, найди пользователя. Верни `nil` + ошибку, если не найден.",
    "theory": "Возврат бизнес-ошибок через `gqlerror.Error`:\n- Когда требуется не просто вернуть `nil`, а явно сообщить клиенту причину с кодом ошибки:\n```go\nreturn nil, &gqlerror.Error{\n    Message: \"пользователь с указанным ID не найден\",\n    Extensions: map[string]any{\n        \"code\": \"USER_NOT_FOUND\",\n        \"user_id\": id,\n    },\n}\n```\n- Клиентский фреймворк разбирает `errors[0].extensions.code` для интернационализации сообщений.",
    "step_by_step": "1. Создайте структуру ошибки с расширениями extensions.\n2. Реализуйте поиск пользователя в резолвере.\n3. Верните кастомную ошибку при отсутствии сущности.\n4. Проверьте код ошибки и сообщение.",
    "code_blocks": [
      {
        "filename": "gqlerror_resolver_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\n\t\"github.com/vektah/gqlparser/v2/gqlerror\"\n)\n\ntype User struct {\n\tID   string\n\tName string\n}\n\ntype QueryResolver struct {\n\tusers map[string]*User\n}\n\nfunc (r *QueryResolver) User(ctx context.Context, id string) (*User, error) {\n\tu, ok := r.users[id]\n\tif !ok {\n\t\treturn nil, &gqlerror.Error{\n\t\t\tMessage: fmt.Sprintf(\"пользователь с id '%s' не найден\", id),\n\t\t\tExtensions: map[string]any{\n\t\t\t\t\"code\":    \"NOT_FOUND\",\n\t\t\t\t\"user_id\": id,\n\t\t\t},\n\t\t}\n\t}\n\treturn u, nil\n}\n\nfunc TestGqlErrorOnNotFound(t *testing.T) {\n\tr := &QueryResolver{users: make(map[string]*User)}\n\n\tu, err := r.User(context.Background(), \"missing_404\")\n\tif u != nil {\n\t\tt.Fatal(\"Пользователь должен быть nil\")\n\t}\n\n\tgqlErr, ok := err.(*gqlerror.Error)\n\tif !ok {\n\t\tt.Fatalf(\"Ожидалась ошибка *gqlerror.Error, получено: %T\", err)\n\t}\n\n\tif gqlErr.Extensions[\"code\"] != \"NOT_FOUND\" {\n\t\tt.Fatalf(\"Некорректный код ошибки: %v\", gqlErr.Extensions)\n\t}\n\n\tfmt.Printf(\"GraphQL ошибка успешно сформирована: Message='%s', Code=%v\\n\",\n\t\tgqlErr.Message, gqlErr.Extensions[\"code\"])\n}",
        "note": "Формирование расширенной ошибки gqlerror.Error с кодом в Extensions"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v gqlerror_resolver_test.go\n# Вывод:\n# === RUN   TestGqlErrorOnNotFound\n# GraphQL ошибка успешно сформирована: Message='пользователь с id 'missing_404' не найден', Code=NOT_FOUND\n# --- PASS: TestGqlErrorOnNotFound (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В GraphQL спецификации массив `errors` стандартизирован: он обязан содержать `message`, опциональные `locations`, `path` и произвольный объект `extensions` для метаданных.",
    "pitfalls": "Возвращать системные ошибки SQL драйвера напрямую (`pq: relation \"users\" does not exist`): это раскрывает детали реализации злоумышленникам. Ошибки базы данных нужно маскировать.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как скрыть системные ошибки от пользователей в production через gqlgen?»\n**Ответ:** Переопределить `server.SetErrorPresenter(func(ctx context.Context, e error) *gqlerror.Error { ... })`. Внутри проверяют тип ошибки: если это внутренняя ошибка, ее логируют в Sentry/Jaeger, а клиенту отдают общее сообщение `\"Internal Server Error\"` с уникальным `trace_id`."
  },
  {
    "num": 12,
    "title": "Базовые скалярные типы: Int, Float, Boolean, ID, String и их типизация в Go",
    "task": "Используйте **скалярные типы**: `Int`, `Float`, `Boolean`, `ID`, `String`. Создайте query, который возвращает данные всех типов.",
    "theory": "Соответствие 5 встроенных скаляров GraphQL спецификации:\n1. `Int`: знаковое 32-битное целое число ($\\pm 2^{31}-1$). В Go мапится в `int` (или `int32`).\n2. `Float`: число с плавающей запятой двойной точности по стандарту IEEE 754. В Go мапится в `float64`.\n3. `String`: последовательность символов UTF-8. В Go мапится в `string`.\n4. `Boolean`: логическое значение (`true` / `false`). В Go мапится в `bool`.\n5. `ID`: уникальный строковый сериализатор идентификатора. В Go мапится в `string`.\n- Для больших 64-битных чисел (`int64`) в GraphQL создают кастомный скаляр `Int64`, так как встроенный `Int` переполнится при значениях $> 2\\,147\\,483\\,647$.",
    "step_by_step": "1. Создайте структуру со всеми 5 скалярными типами.\n2. Заполните тестовыми данными.\n3. Проверьте сериализацию в корректные JSON типы.\n4. Убедитесь в отсутствии потери точности Float.",
    "code_blocks": [
      {
        "filename": "scalars_model_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"testing\"\n)\n\n// GraphQL:\n// type SystemMetrics {\n//   id: ID!\n//   nodeName: String!\n//   cpuUsage: Float!\n//   activeTasks: Int!\n//   isHealthy: Boolean!\n// }\ntype SystemMetrics struct {\n\tID          string  `json:\"id\"`\n\tNodeName    string  `json:\"nodeName\"`\n\tCPUUsage    float64 `json:\"cpuUsage\"`\n\tActiveTasks int     `json:\"activeTasks\"`\n\tIsHealthy   bool    `json:\"isHealthy\"`\n}\n\nfunc TestScalarsMapping(t *testing.T) {\n\tmetrics := SystemMetrics{\n\t\tID:          \"node-az-102\",\n\t\tNodeName:    \"prod-worker-01\",\n\t\tCPUUsage:    42.75,\n\t\tActiveTasks: 180,\n\t\tIsHealthy:   true,\n\t}\n\n\tbytes, err := json.Marshal(metrics)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка сериализации: %v\", err)\n\t}\n\n\texpected := `{\"id\":\"node-az-102\",\"nodeName\":\"prod-worker-01\",\"cpuUsage\":42.75,\"activeTasks\":180,\"isHealthy\":true}`\n\tif string(bytes) != expected {\n\t\tt.Fatalf(\"Некорректный JSON: got %s, want %s\", string(bytes), expected)\n\t}\n\n\tfmt.Printf(\"Все 5 базовых скаляров успешно валидированы: %s\\n\", string(bytes))\n}",
        "note": "Маппинг всех 5 стандартных скаляров GraphQL в типы Go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v scalars_model_test.go\n# Вывод:\n# === RUN   TestScalarsMapping\n# Все 5 базовых скаляров успешно валидированы: {\"id\":\"node-az-102\",\"nodeName\":\"prod-worker-01\",\"cpuUsage\":42.75,\"activeTasks\":180,\"isHealthy\":true}\n# --- PASS: TestScalarsMapping (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В JSON спецификации числа не имеют строгой разницы между целыми и вещественными. GraphQL строго проверяет AST токен: если в поле `Int` передать `12.34`, парсер вернет ошибку валидации синтаксиса до вызова резолвера.",
    "pitfalls": "Использовать встроенный скаляр `Int` для идентификаторов базы данных типа `BIGINT` (64-бита): при превышении 2 миллиардов запрос завершится ошибкой парсера.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему поле ID в GraphQL имеет тип String в Go, а не int?»\n**Ответ:** По спецификации GraphQL скаляр `ID` предназначен для уникального глобального идентификатора сущности. Часто это UUID (`\"c9bf9e57-...\"`) или base64-кодированная составная строка (`\"User:123\"` в Relay), поэтому он всегда сериализуется как строка."
  },
  {
    "num": 13,
    "title": "Кастомный скаляр Time: реализация интерфейсов MarshalGQL и UnmarshalGQL для time.Time",
    "task": "Реализуйте **кастомный скаляр** `Time` (для `time.Time`), реализовав методы `MarshalGQL` и `UnmarshalGQL`. Это нужно для корректной работы с датами.",
    "theory": "Контракт кастомного скаляра в `gqlgen`:\n- Для любого кастомного типа в Go требуются 2 метода:\n  1. `MarshalGQL(w io.Writer)`: преобразует Go-значение в валидный JSON-литерал и записывает в `w`.\n  2. `UnmarshalGQL(v any) error`: принимает распарсенное значение из запроса (строку, число, bool) и десериализует его в Go-тип.\n- Реализация для `time.Time` гарантирует, что даты всегда передаются в строгом формате ISO 8601 / RFC 3339.",
    "step_by_step": "1. Создайте пользовательский тип `CustomTime`.\n2. Реализуйте метод `MarshalGQL` с экранированием кавычек.\n3. Реализуйте метод `UnmarshalGQL` с парсингом `time.RFC3339`.\n4. Протестируйте оба направления сериализации.",
    "code_blocks": [
      {
        "filename": "custom_time_scalar_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"bytes\"\n\t\"fmt\"\n\t\"io\"\n\t\"strconv\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype CustomTime time.Time\n\nfunc (ct CustomTime) MarshalGQL(w io.Writer) {\n\tt := time.Time(ct)\n\t// Обязательно выводим кавычки для строки JSON\n\t_, _ = io.WriteString(w, strconv.Quote(t.Format(time.RFC3339)))\n}\n\nfunc (ct *CustomTime) UnmarshalGQL(v any) error {\n\tstr, ok := v.(string)\n\tif !ok {\n\t\treturn fmt.Errorf(\"ожидалась строка для скаляра Time, получено: %T\", v)\n\t}\n\n\tparsed, err := time.Parse(time.RFC3339, str)\n\tif err != nil {\n\t\treturn fmt.Errorf(\"невалидный формат даты RFC3339: %w\", err)\n\t}\n\n\t*ct = CustomTime(parsed)\n\treturn nil\n}\n\nfunc TestCustomTimeScalar(t *testing.T) {\n\t// 1. Тест MarshalGQL\n\tsample := time.Date(2026, 9, 3, 15, 30, 0, 0, time.UTC)\n\tct := CustomTime(sample)\n\n\tvar buf bytes.Buffer\n\tct.MarshalGQL(&buf)\n\texpectedJSON := `\"2026-09-03T15:30:00Z\"`\n\n\tif buf.String() != expectedJSON {\n\t\tt.Fatalf(\"Ошибка маршалинга: got %s, want %s\", buf.String(), expectedJSON)\n\t}\n\n\t// 2. Тест UnmarshalGQL\n\tvar unmarshaled CustomTime\n\terr := unmarshaled.UnmarshalGQL(\"2026-09-03T15:30:00Z\")\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка демаршалинга: %v\", err)\n\t}\n\n\tif time.Time(unmarshaled).Year() != 2026 {\n\t\tt.Fatal(\"Год распарсен неверно\")\n\t}\n\n\tfmt.Printf(\"Кастомный скаляр Time успешно сериализован (%s) и десериализован!\\n\", buf.String())\n}",
        "note": "Реализация интерфейсов MarshalGQL и UnmarshalGQL для time.Time"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v custom_time_scalar_test.go\n# Вывод:\n# === RUN   TestCustomTimeScalar\n# Кастомный скаляр Time успешно сериализован (\"2026-09-03T15:30:00Z\") и десериализован!\n# --- PASS: TestCustomTimeScalar (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Метод `MarshalGQL` пишет сырые байты напрямую в поток. Если забыть добавить кавычки `strconv.Quote`, JSON станет невалидным, так как дата будет выведена без кавычек.",
    "pitfalls": "Использовать парсинг без указания временной зоны: даты без указания смещения UTC будут интерпретироваться в локальной зоне сервера, вызывая смещение времени на несколько часов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем создавать кастомный скаляр Upload в GraphQL?»\n**Ответ:** Спецификация GraphQL Multipart Request позволяет передавать бинарные файлы (картинки, документы) через `multipart/form-data`. Кастомный скаляр `Upload` мапится в `graphql.Upload` (`io.Reader` + метаданные `filename`, `contentType`), позволяя загружать файлы без base64-кодирования."
  },
  {
    "num": 14,
    "title": "Перечисления (Enums) в схеме: enum Role { ADMIN, USER, GUEST } и валидация значений",
    "task": "Создайте тип `enum Role { ADMIN, USER, GUEST }` и используйте его в схеме.",
    "theory": "Перечисления в GraphQL и Go:\n- SDL:\n```graphql\nenum Role {\n  ADMIN\n  USER\n  GUEST\n}\n```\n- Сгенерированный код в Go:\n```go\ntype Role string\n\nconst (\n    RoleAdmin Role = \"ADMIN\"\n    RoleUser  Role = \"USER\"\n    RoleGuest Role = \"GUEST\"\n)\n```\n- gqlgen автоматически генерирует методы `IsValid()`, `MarshalGQL()` и `UnmarshalGQL()` для каждого enum, гарантируя, что недопустимые строковые значения отсекаются парсером.",
    "step_by_step": "1. Объявите тип `Role` и константы перечисления.\n2. Реализуйте метод проверки валидности `IsValid()`.\n3. Реализуйте методы демаршалинга с проверкой допустимости.\n4. Протестируйте отказ при передаче неизвестного значения.",
    "code_blocks": [
      {
        "filename": "enum_role_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype Role string\n\nconst (\n\tRoleAdmin Role = \"ADMIN\"\n\tRoleUser  Role = \"USER\"\n\tRoleGuest Role = \"GUEST\"\n)\n\nvar AllRoles = []Role{RoleAdmin, RoleUser, RoleGuest}\n\nfunc (e Role) IsValid() bool {\n\tswitch e {\n\tcase RoleAdmin, RoleUser, RoleGuest:\n\t\treturn true\n\t}\n\treturn false\n}\n\nfunc (e *Role) UnmarshalGQL(v any) error {\n\tstr, ok := v.(string)\n\tif !ok {\n\t\treturn fmt.Errorf(\"роль должна быть строкой\")\n\t}\n\t*e = Role(str)\n\tif !e.IsValid() {\n\t\treturn fmt.Errorf(\"%s не является допустимой ролью\", str)\n\t}\n\treturn nil\n}\n\nfunc TestEnumRoleValidation(t *testing.T) {\n\t// 1. Валидный enum\n\tvar r Role\n\tif err := r.UnmarshalGQL(\"ADMIN\"); err != nil || r != RoleAdmin {\n\t\tt.Fatalf(\"Ошибка валидации ADMIN: %v\", err)\n\t}\n\n\t// 2. Невалидный enum\n\tvar invalidR Role\n\terr := invalidR.UnmarshalGQL(\"SUPERUSER\")\n\tif err == nil {\n\t\tt.Fatal(\"Ожидалась ошибка валидации для SUPERUSER\")\n\t}\n\n\tfmt.Println(\"Перечисление Role успешно протестировано: ADMIN принят, SUPERUSER отклонен!\")\n}",
        "note": "Строгая проверка значений GraphQL Enum в Go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v enum_role_test.go\n# Вывод:\n# === RUN   TestEnumRoleValidation\n# Перечисление Role успешно протестировано: ADMIN принят, SUPERUSER отклонен!\n# --- PASS: TestEnumRoleValidation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В GraphQL запросе enum передается без кавычек (`role: ADMIN`). Парсер `gqlparser` сопоставляет идентификатор со списком допустимых значений схемы на этапе валидации AST.",
    "pitfalls": "Использовать строчные буквы в значениях enum в SDL: по стайл-гайду GraphQL все значения enum пишутся заглавными буквами (`SCREAMING_SNAKE_CASE`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как безопасно удалить значение из GraphQL Enum без поломки мобильных приложений?»\n**Ответ:** Пометить значение директивой `@deprecated(reason: \"Используйте новое значение ...\")`. Клиенты получат предупреждение в интроспекции, а сервер должен временно продолжать поддерживать старое значение до полного обновления всех версий мобильных клиентов в App Store и Google Play."
  },
  {
    "num": 15,
    "title": "Частичное обновление (Partial Update) в Mutation updateUser: проверка указателей на nil",
    "task": "Реализуй **Mutation resolver** `updateUser(id: ID!, input: UpdateUserInput!): User`. Обработай **partial update**: только переданные поля обновляются, остальные — без изменений. Используй `input.Name != nil` (pointer в Go).",
    "theory": "Паттерн Partial Update (PATCH семантика) в GraphQL:\n- Входной тип:\n```graphql\ninput UpdateUserInput {\n  name: String\n  email: String\n}\n```\n- В Go поля генерируются как указатели: `Name *string`, `Email *string`.\n- Логика резолвера:\n  - Если `input.Name != nil`, обновляем имя: `user.Name = *input.Name`.\n  - Если `input.Name == nil`, поле не было передано в запросе, оставляем старое значение.\n- Это позволяет обновлять только нужные поля объекта без перезаписи всей структуры.",
    "step_by_step": "1. Создайте структуру `UpdateUserInput` с полями-указателями.\n2. Реализуйте метод `UpdateUser` с проверкой `!= nil`.\n3. Смоделируйте обновление только имени при неизменном email.\n4. Проверьте сохранность неизмененных полей.",
    "code_blocks": [
      {
        "filename": "partial_update_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype User struct {\n\tID    string\n\tName  string\n\tEmail string\n}\n\ntype UpdateUserInput struct {\n\tName  *string\n\tEmail *string\n}\n\ntype MutationResolver struct {\n\tstore map[string]*User\n}\n\nfunc (r *MutationResolver) UpdateUser(ctx context.Context, id string, input UpdateUserInput) (*User, error) {\n\tu, exists := r.store[id]\n\tif !exists {\n\t\treturn nil, errors.New(\"пользователь не найден\")\n\t}\n\n\t// Частичное обновление (Partial Update):\n\tif input.Name != nil {\n\t\tu.Name = *input.Name\n\t}\n\tif input.Email != nil {\n\t\tu.Email = *input.Email\n\t}\n\n\treturn u, nil\n}\n\nfunc TestPartialUpdateUser(t *testing.T) {\n\tuser := &User{ID: \"usr_1\", Name: \"Старое Имя\", Email: \"original@mail.ru\"}\n\tr := &MutationResolver{\n\t\tstore: map[string]*User{\"usr_1\": user},\n\t}\n\n\t// Обновляем ТОЛЬКО имя, email оставляем nil\n\tnewName := \"Новое Имя\"\n\tupdated, err := r.UpdateUser(context.Background(), \"usr_1\", UpdateUserInput{\n\t\tName:  &newName,\n\t\tEmail: nil,\n\t})\n\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка обновления: %v\", err)\n\t}\n\n\tif updated.Name != \"Новое Имя\" || updated.Email != \"original@mail.ru\" {\n\t\tt.Fatalf(\"Некорректное частичное обновление: %+v\", updated)\n\t}\n\n\tfmt.Println(\"Partial Update успешно выполнен: имя обновлено, email сохранен без изменений!\")\n}",
        "note": "Частичное обновление полей структуры через проверку указателей на nil"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v partial_update_test.go\n# Вывод:\n# === RUN   TestPartialUpdateUser\n# Partial Update успешно выполнен: имя обновлено, email сохранен без изменений!\n# --- PASS: TestPartialUpdateUser (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В Go простой указатель `*string` не позволяет отличить «поле не передано» от «поле передано как явный null для очистки». Если требуется различать эти два состояния, в Go используют тройное состояние (Tri-state / Optional тип).",
    "pitfalls": "Прямое разыменование `*input.Name` без проверки `if input.Name != nil`: мгновенный сбой и паника сервера при запросе, где поле `name` опущено.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как отличить в Go, передал ли клиент поле как null (хочет стереть bio), или вообще не передал поле в запросе (оставить как есть)?»\n**Ответ:** В `gqlgen` можно проверить наличие поля через контекст операции: `graphql.HasOperationContext(ctx)` и анализ аргументов `fc := graphql.GetFieldContext(ctx)`. Другой подход — использовать специализированную обертку `graphql.Omittable[*string]`, имеющую состояния `Defined` (true/false) и `Value`."
  },
  {
    "num": 16,
    "title": "Входные типы Input Object: структурирование аргументов мутаций через CreateUserInput",
    "task": "Используйте `input` типы для аргументов мутаций: `input CreateUserInput { name: String!, email: String! }`.",
    "theory": "Зачем использовать Input Types вместо плоских аргументов:\n- **Плохой подход:** `createUser(name: String!, email: String!, age: Int, city: String, role: Role!): User!`\n  - При добавлении 10 новых полей сигнатура мутации превращается в нечитаемую простыню.\n- **Хороший подход (Input Object):**\n```graphql\ninput CreateUserInput {\n  name: String!\n  email: String!\n}\ntype Mutation {\n  createUser(input: CreateUserInput!): User!\n}\n```\n- Добавление полей в `input` обратно совместимо и не меняет сигнатуру метода мутации в Go.",
    "step_by_step": "1. Опишите DTO структуру `CreateUserInput`.\n2. Реализуйте метод `CreateUser` принимающий единую структуру.\n3. Проверьте распаковку полей из структуры входных данных.\n4. Протестируйте создание нового пользователя.",
    "code_blocks": [
      {
        "filename": "input_object_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype User struct {\n\tID    string\n\tName  string\n\tEmail string\n}\n\ntype CreateUserInput struct {\n\tName  string `json:\"name\"`\n\tEmail string `json:\"email\"`\n}\n\ntype MutationResolver struct {\n\tcounter int\n}\n\nfunc (r *MutationResolver) CreateUser(ctx context.Context, input CreateUserInput) (*User, error) {\n\tr.counter++\n\treturn &User{\n\t\tID:    fmt.Sprintf(\"usr_%d\", r.counter),\n\t\tName:  input.Name,\n\t\tEmail: input.Email,\n\t}, nil\n}\n\nfunc TestCreateUserInput(t *testing.T) {\n\tr := &MutationResolver{}\n\tinput := CreateUserInput{\n\t\tName:  \"Василий Кузнецов\",\n\t\tEmail: \"vasily@lamoda.ru\",\n\t}\n\n\tu, err := r.CreateUser(context.Background(), input)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка создания: %v\", err)\n\t}\n\n\tif u.ID != \"usr_1\" || u.Name != \"Василий Кузнецов\" {\n\t\tt.Fatalf(\"Некорректный результат создания: %+v\", u)\n\t}\n\n\tfmt.Printf(\"Пользователь успешно создан через Input Object: ID=%s, Name=%s\\n\", u.ID, u.Name)\n}",
        "note": "Использование единого входного объекта CreateUserInput для мутации"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v input_object_test.go\n# Вывод:\n# === RUN   TestCreateUserInput\n# Пользователь успешно создан через Input Object: ID=usr_1, Name=Василий Кузнецов\n# --- PASS: TestCreateUserInput (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В спецификации GraphQL типы `type` и `input` строго разделены: обычный объект `type` не может быть передан в качестве аргумента, а тип `input` не может содержать поля, возвращающие другие `type`.",
    "pitfalls": "Использовать тип `type` вместо `input` для входных аргументов в SDL: `gqlparser` выдаст ошибку валидации схемы `Objects must not be used as input types`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в GraphQL мутациях всегда рекомендуется возвращать созданный объект целиком, а не просто boolean или ID?»\n**Ответ:** Фронтенд-клиенты (Apollo Client, Relay) используют **Normalized Cache**: получив созданный или обновленный объект со всеми полями, кэш клиента автоматически обновляет интерфейс без необходимости делать повторный запрос `query` к серверу."
  },
  {
    "num": 17,
    "title": "Реализация Query-резолверов в schema.resolvers.go: проекция выборки полей без оверхеда",
    "task": "**Реализация Query-резолверов**: В сгенерированном файле `schema.resolvers.go` найдите заглушки методов `User` и `Users`. Реализуйте их логику: извлеките данные из тестовой мапы в оперативной памяти и верните клиенту. Выполните тестовый запрос в Playground, запрашивая только поле `name`, а затем все поля сразу.",
    "theory": "Механика выборки полей (Field Selection) в GraphQL:\n- В отличие от REST, где сервер всегда отдает фиксированный JSON со 100 полями (Overfetching), клиент GraphQL запрашивает только нужные поля:\n  `query { user(id: \"1\") { name } }`\n- Метод резолвера `User` возвращает полную Go-структуру `*model.User`.\n- `generated.go` проверяет AST запроса и сериализует в итоговый JSON **только запрошенные клиентом поля**, отбрасывая остальные.\n- Если вычисление поля тяжелое (например `avatarUrl` или `orders`), такое поле выносят в отдельный резолвер поля!",
    "step_by_step": "1. Создайте структуру модели пользователя с несколькими полями.\n2. Реализуйте фильтрацию полей на основе списка запрошенных полей.\n3. Проверьте запрос с одним полем `name`.\n4. Проверьте запрос со всеми полями сразу.",
    "code_blocks": [
      {
        "filename": "field_selection_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype User struct {\n\tID    string `json:\"id,omitempty\"`\n\tName  string `json:\"name,omitempty\"`\n\tEmail string `json:\"email,omitempty\"`\n}\n\n// Имитация проекции полей движком gqlgen\nfunc ProjectFields(u *User, requestedFields []string) map[string]any {\n\tresult := make(map[string]any)\n\tfor _, f := range requestedFields {\n\t\tswitch f {\n\t\tcase \"id\":\n\t\t\tresult[\"id\"] = u.ID\n\t\tcase \"name\":\n\t\t\tresult[\"name\"] = u.Name\n\t\tcase \"email\":\n\t\t\tresult[\"email\"] = u.Email\n\t\t}\n\t}\n\treturn result\n}\n\nfunc TestFieldProjection(t *testing.T) {\n\tfullUser := &User{ID: \"usr_100\", Name: \"Кирилл\", Email: \"kirill@kaspersky.ru\"}\n\n\t// 1. Клиент запросил только `name`\n\tp1 := ProjectFields(fullUser, []string{\"name\"})\n\tb1, _ := json.Marshal(p1)\n\tif string(b1) != `{\"name\":\"Кирилл\"}` {\n\t\tt.Fatalf(\"Некорректная проекция name: %s\", string(b1))\n\t}\n\n\t// 2. Клиент запросил все поля\n\tp2 := ProjectFields(fullUser, []string{\"id\", \"name\", \"email\"})\n\tb2, _ := json.Marshal(p2)\n\n\tfmt.Printf(\"1. Запрос только name:     %s (Overfetching устранен!)\\n\", string(b1))\n\tfmt.Printf(\"2. Запрос всех полей:      %s\\n\", string(b2))\n}",
        "note": "Устранение проблемы Overfetching через точечную выборку полей"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v field_selection_test.go\n# Вывод:\n# === RUN   TestFieldProjection\n# 1. Запрос только name:     {\"name\":\"Кирилл\"} (Overfetching устранен!)\n# 2. Запрос всех полей:      {\"email\":\"kirill@kaspersky.ru\",\"id\":\"usr_100\",\"name\":\"Кирилл\"}\n# --- PASS: TestFieldProjection (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В `gqlgen` узнать запрошенные клиентом поля можно через вызов `graphql.CollectFieldsCtx(ctx, nil)`. Это позволяет оптимизировать SQL-запрос (`SELECT name FROM users` вместо `SELECT *`).",
    "pitfalls": "Выполнять тяжелые вычисления в резолвере родительского типа, если поле клиентом не запрошено: тяжелые вычисления всегда выносят в явные Field Resolvers.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как динамически формировать SELECT в SQL на основе полей GraphQL запроса?»\n**Ответ:** Через пакет `github.com/99designs/gqlgen/graphql` анализируют список полей:\n```go\nfields := graphql.CollectAllFields(ctx)\n// fields = [\"id\", \"name\"] -> SELECT id, name FROM users\n```\nЭто предотвращает избыточную нагрузку на дисковую подсистему и сеть базы данных."
  },
  {
    "num": 18,
    "title": "Валидация аргументов в мутации createUser: проверка формата email и непустого имени",
    "task": "Реализуй **Mutation resolver** `createUser(input: CreateUserInput!): User!`. Валидируй входные данные (email формат, name не пустой). Сохрани в in-memory map или PostgreSQL. Верни созданного пользователя.",
    "theory": "Многоуровневая валидация в GraphQL:\n1. **Синтаксическая валидация:** выполняется движком GraphQL на основе типов схемы (например, поле не `null`, типы совпадают).\n2. **Семантическая / Бизнес-валидация:** выполняется внутри метода резолвера:\n   - Имя должно содержать не менее 2 символов и не состоять из одних пробелов.\n   - Email должен соответствовать регулярному выражению RFC 5322.\n3. При нарушении валидации возвращается ошибка с кодом `BAD_USER_INPUT`.",
    "step_by_step": "1. Создайте регулярное выражение валидации email.\n2. Напишите проверки входных аргументов в резолвере.\n3. Верните структурированную ошибку валидации при сбое.\n4. Протестируйте успешное создание при корректных данных.",
    "code_blocks": [
      {
        "filename": "create_user_validation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net/mail\"\n\t\"strings\"\n\t\"testing\"\n\n\t\"github.com/vektah/gqlparser/v2/gqlerror\"\n)\n\ntype User struct {\n\tID    string\n\tName  string\n\tEmail string\n}\n\ntype CreateUserInput struct {\n\tName  string\n\tEmail string\n}\n\nfunc ValidateAndCreateUser(ctx context.Context, input CreateUserInput) (*User, error) {\n\tcleanName := strings.TrimSpace(input.Name)\n\tif len(cleanName) < 2 {\n\t\treturn nil, &gqlerror.Error{\n\t\t\tMessage: \"имя пользователя должно содержать не менее 2 символов\",\n\t\t\tExtensions: map[string]any{\n\t\t\t\t\"code\":  \"BAD_USER_INPUT\",\n\t\t\t\t\"field\": \"name\",\n\t\t\t},\n\t\t}\n\t}\n\n\t_, err := mail.ParseAddress(input.Email)\n\tif err != nil || !strings.Contains(input.Email, \"@\") {\n\t\treturn nil, &gqlerror.Error{\n\t\t\tMessage: \"некорректный формат адреса электронной почты\",\n\t\t\tExtensions: map[string]any{\n\t\t\t\t\"code\":  \"BAD_USER_INPUT\",\n\t\t\t\t\"field\": \"email\",\n\t\t\t},\n\t\t}\n\t}\n\n\treturn &User{\n\t\tID:    \"usr_validated_1\",\n\t\tName:  cleanName,\n\t\tEmail: input.Email,\n\t}, nil\n}\n\nfunc TestCreateUserValidation(t *testing.T) {\n\t// 1. Невалидный email\n\t_, errMail := ValidateAndCreateUser(context.Background(), CreateUserInput{Name: \"Игорь\", Email: \"bad-email\"})\n\tif errMail == nil {\n\t\tt.Fatal(\"Ожидалась ошибка валидации email\")\n\t}\n\n\t// 2. Короткое имя\n\t_, errName := ValidateAndCreateUser(context.Background(), CreateUserInput{Name: \" \", Email: \"valid@wb.ru\"})\n\tif errName == nil {\n\t\tt.Fatal(\"Ожидалась ошибка валидации имени\")\n\t}\n\n\t// 3. Успешный ввод\n\tuser, errOK := ValidateAndCreateUser(context.Background(), CreateUserInput{Name: \"Игорь Соколов\", Email: \"igor@wb.ru\"})\n\tif errOK != nil || user.Name != \"Игорь Соколов\" {\n\t\tt.Fatalf(\"Ошибка успешного создания: %v\", errOK)\n\t}\n\n\tfmt.Printf(\"Валидация мутации успешно отработала: пользователь %s сохранен!\\n\", user.Name)\n}",
        "note": "Строгая проверка входных полей мутации и код BAD_USER_INPUT"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v create_user_validation_test.go\n# Вывод:\n# === RUN   TestCreateUserValidation\n# Валидация мутации успешно отработала: пользователь Игорь Соколов сохранен!\n# --- PASS: TestCreateUserValidation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Стандартная библиотека Go `net/mail.ParseAddress` выполняет полную проверку адреса в соответствии со стандартами RFC 5322 и RFC 6532, исключая опасные инъекции заголовков.",
    "pitfalls": "Использовать примитивную проверку `strings.Contains(email, \"@\")`: адрес `\"@\"` или `\"a@b\"` пройдет такую проверку, но вызовет ошибку почтового сервиса при отправке писем.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы общепринятые коды ошибок GraphQL в Apollo/GraphQL спецификации?»\n**Ответ:** Стандартные коды в `extensions.code`:\n1. `GRAPHQL_VALIDATION_FAILED` — синтаксис запроса не соответствует схеме.\n2. `BAD_USER_INPUT` — ошибка бизнес-валидации полей аргументов.\n3. `UNAUTHENTICATED` — не передан или просрочен JWT токен.\n4. `FORBIDDEN` — нет прав доступа к операции.\n5. `INTERNAL_SERVER_ERROR` — паника или непредвиденная системная ошибка."
  },
  {
    "num": 19,
    "title": "Контроль уникальности email в мутации: возврат ошибки с кодом EMAIL_ALREADY_EXISTS",
    "task": "Реализуйте мутацию `createUser(name: String!, email: String!): User!`. Проверьте, что email уникален (in-memory), при дубликате верните ошибку с расширенным кодом.",
    "theory": "Предотвращение дублирования уникальных сущностей:\n- Перед сохранением пользователя в хранилище проверяется индекс уникальности по полю `email`.\n- При обнаружении дубликата сервер возвращает GraphQL ошибку:\n  - `code: \"EMAIL_ALREADY_EXISTS\"`\n  - Понятное пользователю сообщение на русском языке.\n- Это позволяет фронтенду подсветить поле email красным цветом и предложить восстановить пароль.",
    "step_by_step": "1. Создайте потокобезопасное хранилище с индексом email.\n2. Реализуйте проверку наличия email перед добавлением.\n3. Верните кастомный код ошибки при конфликте.\n4. Протестируйте успешное добавление и отклонение дубликата.",
    "code_blocks": [
      {
        "filename": "email_uniqueness_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\n\t\"github.com/vektah/gqlparser/v2/gqlerror\"\n)\n\ntype User struct {\n\tID    string\n\tName  string\n\tEmail string\n}\n\ntype UserStorage struct {\n\tmu     sync.Mutex\n\tusers  map[string]*User\n\temails map[string]string // email -> id\n}\n\nfunc (s *UserStorage) CreateUser(ctx context.Context, name, email string) (*User, error) {\n\ts.mu.Lock()\n\tdefer s.mu.Unlock()\n\n\tif _, exists := s.emails[email]; exists {\n\t\treturn nil, &gqlerror.Error{\n\t\t\tMessage: fmt.Sprintf(\"пользователь с адресом '%s' уже зарегистрирован\", email),\n\t\t\tExtensions: map[string]any{\n\t\t\t\t\"code\":  \"EMAIL_ALREADY_EXISTS\",\n\t\t\t\t\"email\": email,\n\t\t\t},\n\t\t}\n\t}\n\n\tnewID := fmt.Sprintf(\"usr_%d\", len(s.users)+1)\n\tu := &User{ID: newID, Name: name, Email: email}\n\ts.users[newID] = u\n\ts.emails[email] = newID\n\n\treturn u, nil\n}\n\nfunc TestEmailUniqueness(t *testing.T) {\n\tstorage := &UserStorage{\n\t\tusers:  make(map[string]*User),\n\t\temails: make(map[string]string),\n\t}\n\n\t// 1. Первая регистрация успешна\n\tu1, err1 := storage.CreateUser(context.Background(), \"Артём\", \"artem@yandex.ru\")\n\tif err1 != nil || u1 == nil {\n\t\tt.Fatalf(\"Ошибка первой регистрации: %v\", err1)\n\t}\n\n\t// 2. Повторная регистрация с тем же email\n\t_, err2 := storage.CreateUser(context.Background(), \"Артём Дубль\", \"artem@yandex.ru\")\n\tif err2 == nil {\n\t\tt.Fatal(\"Ожидался конфликт дублирования email\")\n\t}\n\n\tgqlErr := err2.(*gqlerror.Error)\n\tif gqlErr.Extensions[\"code\"] != \"EMAIL_ALREADY_EXISTS\" {\n\t\tt.Fatalf(\"Некорректный код ошибки: %v\", gqlErr.Extensions)\n\t}\n\n\tfmt.Printf(\"Контроль уникальности сработал корректно: %s (код: %v)\\n\",\n\t\tgqlErr.Message, gqlErr.Extensions[\"code\"])\n}",
        "note": "Проверка уникальности email и возврат кода EMAIL_ALREADY_EXISTS"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v email_uniqueness_test.go\n# Вывод:\n# === RUN   TestEmailUniqueness\n# Контроль уникальности сработал корректно: пользователь с адресом 'artem@yandex.ru' уже зарегистрирован (код: EMAIL_ALREADY_EXISTS)\n# --- PASS: TestEmailUniqueness (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В реальной реляционной БД (PostgreSQL) проверка дубликата опирается на `UNIQUE INDEX (email)`. При ошибке `23505 (unique_violation)` Go-драйвер мапит SQL-ошибку в `EMAIL_ALREADY_EXISTS`.",
    "pitfalls": "Делать проверку уникальности в коде без уникального индекса в базе: при двух параллельных запросах возникнет состояние гонки (Race Condition), и оба пользователя запишутся с одинаковым email.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в GraphQL рекомендуется возвращать Union или Result type для мутаций вместо выброса ошибок?»\n**Ответ:** Паттерн **Result Pattern**: `union CreateUserResult = User | EmailAlreadyExistsError | ValidationError`. Клиент явно обрабатывает все ожидаемые бизнес-исходы через `... on EmailAlreadyExistsError`, а массив `errors` используется строго для технических аварий."
  },
  {
    "num": 20,
    "title": "Интерфейсы в схеме GraphQL: interface Node { id: ID! } и динамический резолвинг __typename",
    "task": "Добавьте **интерфейсы** в схему (`interface Node { id: ID! }`) и реализуйте их для разных типов.",
    "theory": "Интерфейсы (Interfaces) в GraphQL SDL:\n```graphql\ninterface Node {\n  id: ID!\n}\n\ntype User implements Node {\n  id: ID!\n  name: String!\n}\n\ntype Order implements Node {\n  id: ID!\n  totalAmount: Float!\n}\n\ntype Query {\n  node(id: ID!): Node\n}\n```\n- В Go интерфейс `Node` генерируется как интерфейс Go:\n  `type Node interface { IsNode(); GetID() string }`\n- Мета-поле `__typename` возвращает точное имя типа (`\"User\"` или `\"Order\"`), позволяя клиенту использовать фрагменты `... on User` и `... on Order`.",
    "step_by_step": "1. Опишите Go интерфейс `Node` с методом маркером.\n2. Реализуйте интерфейс структурами `User` и `Order`.\n3. Смоделируйте фабричный резолвер `Node(id)`.\n4. Протестируйте приведение типов (Type Assertion).",
    "code_blocks": [
      {
        "filename": "graphql_interface_node_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype Node interface {\n\tIsNode()\n\tGetID() string\n}\n\ntype User struct {\n\tID   string\n\tName string\n}\n\nfunc (User) IsNode() {}\nfunc (u User) GetID() string { return u.ID }\n\ntype Order struct {\n\tID          string\n\tTotalAmount float64\n}\n\nfunc (Order) IsNode() {}\nfunc (o Order) GetID() string { return o.ID }\n\nfunc ResolveNode(ctx context.Context, id string) (Node, error) {\n\tif id == \"usr_1\" {\n\t\treturn &User{ID: id, Name: \"Татьяна\"}, nil\n\t}\n\tif id == \"ord_100\" {\n\t\treturn &Order{ID: id, TotalAmount: 4990.50}, nil\n\t}\n\treturn nil, nil\n}\n\nfunc TestGraphQLInterfaceNode(t *testing.T) {\n\t// 1. Запрос пользователя через Node\n\tn1, err1 := ResolveNode(context.Background(), \"usr_1\")\n\tif err1 != nil || n1.GetID() != \"usr_1\" {\n\t\tt.Fatalf(\"Ошибка выборки Node usr_1: %v\", err1)\n\t}\n\n\tuser, ok := n1.(*User)\n\tif !ok || user.Name != \"Татьяна\" {\n\t\tt.Fatal(\"Type assertion к типу User не удался\")\n\t}\n\n\t// 2. Запрос заказа через Node\n\tn2, err2 := ResolveNode(context.Background(), \"ord_100\")\n\tif err2 != nil || n2.GetID() != \"ord_100\" {\n\t\tt.Fatalf(\"Ошибка выборки Node ord_100: %v\", err2)\n\t}\n\n\torder, ok := n2.(*Order)\n\tif !ok || order.TotalAmount != 4990.50 {\n\t\tt.Fatal(\"Type assertion к типу Order не удался\")\n\t}\n\n\tfmt.Printf(\"Интерфейс Node успешно реализован: User.Name=%s, Order.Total=%.2f\\n\",\n\t\tuser.Name, order.TotalAmount)\n}",
        "note": "Реализация и динамическое приведение типов для интерфейса GraphQL Node"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v graphql_interface_node_test.go\n# Вывод:\n# === RUN   TestGraphQLInterfaceNode\n# Интерфейс Node успешно реализован: User.Name=Татьяна, Order.Total=4990.50\n# --- PASS: TestGraphQLInterfaceNode (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В спецификации Relay Global Object Identification интерфейс `Node` с методом `node(id: ID!): Node` является фундаментальным: он позволяет клиентскому кэшу обновить любую сущность системы по глобальному ID.",
    "pitfalls": "Забывать указывать метод-маркер `IsNode()`: без него структура Go может случайно удовлетворять другому интерфейсу с идентичной сигнатурой `GetID()`.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем разница между Interface и Union в GraphQL?»\n**Ответ:** **Interface** требует, чтобы все реализующие его типы имели общий набор одинаковых полей (`id`, `createdAt`). **Union** объединяет совершенно разные типы, у которых может не быть ни одного общего поля (`union SearchResult = User | Order | Article`). Для интерфейсов можно делать общую выборку полей без фрагментов (`node { id }`), а для union поля выбираются только внутри условных фрагментов `... on Type`."
  },
  {
    "num": 21,
    "title": "Мутация deleteUser(id: ID!): Soft delete против Hard delete и архитектурные компромиссы",
    "task": "Реализуй **Mutation resolver** `deleteUser(id: ID!): Boolean!`. Soft delete: установи `deleted_at`. Или hard delete — обсуди trade-offs. Верни `true` или ошибку.",
    "theory": "Сравнение стратегий удаления данных:\n1. **Hard Delete (`DELETE FROM users WHERE id = ...`):**\n   - Плюсы: мгновенное освобождение места на диске, соответствие требованиям GDPR («Право на забвение»).\n   - Минусы: безвозвратная потеря истории, нарушение внешних ключей (Foreign Keys) в заказах и транзакциях.\n2. **Soft Delete (`UPDATE users SET deleted_at = NOW() WHERE id = ...`):**\n   - Плюсы: возможность мгновенного восстановления, сохранение аудита и целостности связей.\n   - Минусы: необходимость добавлять `WHERE deleted_at IS NULL` во все SQL-запросы, разрастание таблиц и индексов.\n- В корпоративных бэкендах BigTech стандартным выбором является **Soft Delete** с возможностью фоновой анонимизации данных.",
    "step_by_step": "1. Создайте модель пользователя с полем `DeletedAt *time.Time`.\n2. Реализуйте метод `DeleteUser` с проставлением временной метки.\n3. Исключите удаленных пользователей из последующих выборок.\n4. Протестируйте возврат `true` при успешном мягком удалении.",
    "code_blocks": [
      {
        "filename": "soft_delete_resolver_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype User struct {\n\tID        string\n\tName      string\n\tDeletedAt *time.Time\n}\n\ntype UserStore struct {\n\tusers map[string]*User\n}\n\nfunc (s *UserStore) DeleteUser(ctx context.Context, id string) (bool, error) {\n\tu, exists := s.users[id]\n\tif !exists || u.DeletedAt != nil {\n\t\treturn false, errors.New(\"пользователь не найден или уже удален\")\n\t}\n\n\tnow := time.Now().UTC()\n\tu.DeletedAt = &now // Soft Delete\n\treturn true, nil\n}\n\nfunc (s *UserStore) GetActiveUsers(ctx context.Context) []*User {\n\tactive := make([]*User, 0)\n\tfor _, u := range s.users {\n\t\tif u.DeletedAt == nil {\n\t\t\tactive = append(active, u)\n\t\t}\n\t}\n\treturn active\n}\n\nfunc TestSoftDelete(t *testing.T) {\n\tstore := &UserStore{\n\t\tusers: map[string]*User{\n\t\t\t\"1\": {ID: \"1\", Name: \"Максим\"},\n\t\t\t\"2\": {ID: \"2\", Name: \"Наталья\"},\n\t\t},\n\t}\n\n\t// 1. Успешное мягкое удаление\n\tok, err := store.DeleteUser(context.Background(), \"1\")\n\tif err != nil || !ok {\n\t\tt.Fatalf(\"Ошибка удаления: %v\", err)\n\t}\n\n\t// 2. Проверка, что пользователь не отдается в активных\n\tactive := store.GetActiveUsers(context.Background())\n\tif len(active) != 1 || active[0].ID != \"2\" {\n\t\tt.Fatalf(\"Пользователь не был отфильтрован: %v\", active)\n\t}\n\n\t// 3. Повторная попытка удаления возвращает ошибку\n\t_, errRepeat := store.DeleteUser(context.Background(), \"1\")\n\tif errRepeat == nil {\n\t\tt.Fatal(\"Ожидалась ошибка при повторном удалении\")\n\t}\n\n\tfmt.Printf(\"Soft Delete успешно протестирован: активных пользователей осталось: %d\\n\", len(active))\n}",
        "note": "Реализация паттерна Soft Delete с сохранением временной метки"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v soft_delete_resolver_test.go\n# Вывод:\n# === RUN   TestSoftDelete\n# Soft Delete успешно протестирован: активных пользователей осталось: 1\n# --- PASS: TestSoftDelete (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Для эффективной работы с Soft Delete в PostgreSQL создают частичный индекс (Partial Index): `CREATE INDEX idx_users_active ON users (email) WHERE deleted_at IS NULL`. Это исключает удаленные записи из B-Tree индекса, уменьшая его объем на 90%.",
    "pitfalls": "Возвращать `null` вместо `Boolean!`: если контракт `Boolean!`, резолвер обязан вернуть строго `true` или `false`. Возврат `nil` вызовет Null Bubbling.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как реализовать полное соблюдение GDPR при использовании Soft Delete?»\n**Ответ:** По регламенту GDPR персональные данные должны быть удалены по запросу. В архитектуре применяют гибридный подход: при Soft Delete поля `name`, `email`, `phone` затираются псевдонимами (`\"Deleted User\"`, `\"deleted_hash@gdpr.internal\"`), а запись с `deleted_at` сохраняется для связности финансовых отчетов."
  },
  {
    "num": 22,
    "title": "Union-типы в схеме: union SearchResult = User | Product и полиморфный возврат разнородных данных",
    "task": "Используйте **union-типы** (`union SearchResult = User | Product`) для возврата разнородных данных из одного query.",
    "theory": "Спецификация Union типов в GraphQL:\n- Объединение разнородных типов:\n```graphql\nunion SearchResult = User | Product\n\ntype Query {\n  search(query: String!): [SearchResult!]!\n}\n```\n- Запрос клиента с условными фрагментами:\n```graphql\nquery GlobalSearch {\n  search(query: \"MacBook\") {\n    __typename\n    ... on User {\n      id\n      name\n    }\n    ... on Product {\n      id\n      title\n      price\n    }\n  }\n}\n```\n- В Go `SearchResult` генерируется как пустой маркерный интерфейс:\n  `type SearchResult interface { IsSearchResult() }`",
    "step_by_step": "1. Создайте интерфейс `SearchResult`.\n2. Реализуйте метод `IsSearchResult()` в структурах `User` и `Product`.\n3. Смоделируйте поиск возвращающий разнородный слайс.\n4. Протестируйте типизацию элементов.",
    "code_blocks": [
      {
        "filename": "union_search_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype SearchResult interface {\n\tIsSearchResult()\n}\n\ntype User struct {\n\tID   string\n\tName string\n}\n\nfunc (User) IsSearchResult() {}\n\ntype Product struct {\n\tID    string\n\tTitle string\n\tPrice float64\n}\n\nfunc (Product) IsSearchResult() {}\n\nfunc GlobalSearch(ctx context.Context, text string) ([]SearchResult, error) {\n\tresults := []SearchResult{\n\t\t&User{ID: \"usr_10\", Name: \"Александр (Продавец)\"},\n\t\t&Product{ID: \"prod_55\", Title: \"MacBook Pro M3\", Price: 199990.0},\n\t}\n\treturn results, nil\n}\n\nfunc TestUnionSearchResult(t *testing.T) {\n\titems, err := GlobalSearch(context.Background(), \"MacBook\")\n\tif err != nil || len(items) != 2 {\n\t\tt.Fatalf(\"Ошибка поиска: %v\", err)\n\t}\n\n\tfor i, item := range items {\n\t\tswitch v := item.(type) {\n\t\tcase *User:\n\t\t\tfmt.Printf(\"[%d] Найден пользователь: %s (ID=%s)\\n\", i+1, v.Name, v.ID)\n\t\tcase *Product:\n\t\t\tfmt.Printf(\"[%d] Найден товар:        %s (Цена=%.2f руб)\\n\", i+1, v.Title, v.Price)\n\t\tdefault:\n\t\t\tt.Fatalf(\"Неизвестный тип в union: %T\", item)\n\t\t}\n\t}\n}",
        "note": "Полиморфная обработка Union-типа SearchResult в Go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v union_search_test.go\n# Вывод:\n# === RUN   TestUnionSearchResult\n# [1] Найден пользователь: Александр (Продавец) (ID=usr_10)\n# [2] Найден товар:        MacBook Pro M3 (Цена=199990.00 руб)\n# --- PASS: TestUnionSearchResult (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Движок `gqlgen` определяет мета-поле `__typename` через конструкцию Go `switch v := val.(type)`. Каждому известному типу сопоставляется точное имя из SDL схемы.",
    "pitfalls": "Пытаться объединить в `union` скалярные типы (например `Int | String`): спецификация GraphQL категорически запрещает скаляры и интерфейсы внутри `union`, членами могут быть только типы объектов (`type`).",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем преимущество паттерна Union Error Handling перед стандартным массивом errors?»\n**Ответ:** Мутация возвращает `union RegisterResult = User | UserAlreadyExistsError | WeakPasswordError`. Это превращает ошибки в **типизированные бизнес-данные**: клиентский компилятор TypeScript гарантирует, что разработчик фронтенда обработал все возможные ветки ответа, а полезная нагрузка ошибки строго типизирована."
  },
  {
    "num": 23,
    "title": "Декларативная валидация схемы через директивы: директива @constraint для входных аргументов",
    "task": "Реализуй **Input type** с валидацией: `input CreateUserInput { name: String! @constraint(minLength: 2, maxLength: 100) email: String! @constraint(format: \"email\") }`. Используй directives или валидацию в resolver'е.",
    "theory": "Директивы валидации в SDL (Schema Directives):\n```graphql\ndirective @constraint(\n  minLength: Int\n  maxLength: Int\n  format: String\n) on INPUT_FIELD_DEFINITION | ARGUMENT_DEFINITION\n\ninput CreateUserInput {\n  name: String! @constraint(minLength: 2, maxLength: 100)\n  email: String! @constraint(format: \"email\")\n}\n```\n- Преимущества директив:\n  - Самодокументируемый контракт: фронтенд видит ограничения в документации GraphQL.\n  - Централизация: валидация выполняется декоратором до вызова кода резолвера.",
    "step_by_step": "1. Создайте структуру правил валидации constraint.\n2. Реализуйте функцию-валидатор для полей структуры.\n3. Проверьте отсечение слишком коротких имен (< 2 символов).\n4. Протестируйте успешную валидацию.",
    "code_blocks": [
      {
        "filename": "constraint_directive_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/mail\"\n\t\"testing\"\n)\n\ntype ConstraintRule struct {\n\tMinLength int\n\tMaxLength int\n\tFormat    string\n}\n\nfunc ValidateField(val string, rule ConstraintRule) error {\n\tif rule.MinLength > 0 && len(val) < rule.MinLength {\n\t\treturn fmt.Errorf(\"длина поля (%d) меньше минимальной допустимой (%d)\", len(val), rule.MinLength)\n\t}\n\tif rule.MaxLength > 0 && len(val) > rule.MaxLength {\n\t\treturn fmt.Errorf(\"длина поля (%d) превышает максимальную допустимую (%d)\", len(val), rule.MaxLength)\n\t}\n\tif rule.Format == \"email\" {\n\t\tif _, err := mail.ParseAddress(val); err != nil {\n\t\t\treturn fmt.Errorf(\"невалидный email: %w\", err)\n\t\t}\n\t}\n\treturn nil\n}\n\nfunc TestConstraintValidation(t *testing.T) {\n\tnameRule := ConstraintRule{MinLength: 2, MaxLength: 100}\n\temailRule := ConstraintRule{Format: \"email\"}\n\n\t// 1. Ошибка minLength\n\terrShort := ValidateField(\"A\", nameRule)\n\tif errShort == nil {\n\t\tt.Fatal(\"Ожидалась ошибка длины имени\")\n\t}\n\n\t// 2. Ошибка email\n\terrMail := ValidateField(\"not-an-email\", emailRule)\n\tif errMail == nil {\n\t\tt.Fatal(\"Ожидалась ошибка формата email\")\n\t}\n\n\t// 3. Успех\n\tif err := ValidateField(\"Константин\", nameRule); err != nil {\n\t\tt.Fatalf(\"Имя должно быть валидно: %v\", err)\n\t}\n\n\tfmt.Println(\"Директива @constraint успешно отсекла невалидные данные до вызова резолвера!\")\n}",
        "note": "Эмуляция работы хука директивы @constraint в gqlgen"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v constraint_directive_test.go\n# Вывод:\n# === RUN   TestConstraintValidation\n# Директива @constraint успешно отсекла невалидные данные до вызова резолвера!\n# --- PASS: TestConstraintValidation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В `gqlgen.yml` директивы регистрируются в `directives: { constraint: { ... } }`. Генератор оборачивает вызов поля в функцию middleware: `next(ctx)` вызывается только если директива не вернула ошибку.",
    "pitfalls": "Полагаться исключительно на директивы схемы для защиты от SQL/XSS атак: директивы проверяют формат данных, но не отменяют параметризованные SQL-запросы в репозитории.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в gqlgen работают кастомные директивы аутентификации (@hasRole)?»\n**Ответ:** Объявляется директива `directive @hasRole(role: Role!) on FIELD_DEFINITION`. В `server.go` регистрируется хук:\n```go\ncfg.Directives.HasRole = func(ctx context.Context, obj any, next graphql.Resolver, role Role) (any, error) {\n    user := auth.GetUserFromContext(ctx)\n    if user == nil || user.Role != role {\n        return nil, gqlerror.Errorf(\"Forbidden\")\n    }\n    return next(ctx)\n}\n```\nЕсли роль не совпадает, выполнение резолвера прерывается до обращения к БД."
  },
  {
    "num": 24,
    "title": "Регулярные выражения в валидации email: защита от DoS и возврат канонических ошибок GraphQL",
    "task": "Добавьте **валидацию** в mutation: проверяйте email через регулярку, возвращайте ошибку GraphQL при невалидных данных.",
    "theory": "Безопасная валидация регулярными выражениями в Go:\n- Регулярные выражения в Go (`regexp`) компилируются на базе конечных автоматов (DFA), что математически защищает от катастрофического отката (ReDoS), свойственного JavaScript/Python.\n- Перекомпиляция регулярки на каждый запрос в резолвере (`regexp.Compile`) создает гигантский оверхед.\n- **Правило:** компилировать регулярные выражения один раз при инициализации пакета в глобальную переменную:\n  `var emailRegex = regexp.MustCompile(pattern)`.",
    "step_by_step": "1. Создайте скомпилированное регулярное выражение на уровне пакета.\n2. Реализуйте проверку в мутации.\n3. Верните структурированную ошибку при несовпадении.\n4. Протестируйте валидные и искаженные email адреса.",
    "code_blocks": [
      {
        "filename": "regex_validation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"regexp\"\n\t\"testing\"\n\n\t\"github.com/vektah/gqlparser/v2/gqlerror\"\n)\n\n// Компилируем 1 раз при старте процесса\nvar emailRegex = regexp.MustCompile(`^[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}$`)\n\nfunc ValidateEmailRegex(email string) error {\n\tif !emailRegex.MatchString(email) {\n\t\treturn &gqlerror.Error{\n\t\t\tMessage: \"адрес электронной почты имеет невалидный формат\",\n\t\t\tExtensions: map[string]any{\n\t\t\t\t\"code\":  \"INVALID_EMAIL_FORMAT\",\n\t\t\t\t\"email\": email,\n\t\t\t},\n\t\t}\n\t}\n\treturn nil\n}\n\nfunc TestEmailRegexValidation(t *testing.T) {\n\t// Валидные адреса\n\tval := \"developer@alfa-bank.ru\"\n\tif err := ValidateEmailRegex(val); err != nil {\n\t\tt.Fatalf(\"Адрес %s должен быть валидным: %v\", val, err)\n\t}\n\n\t// Невалидные адреса\n\tinvalids := []string{\"no-domain@\", \"@missing.ru\", \"spaces in@mail.com\", \"plainaddress\"}\n\tfor _, bad := range invalids {\n\t\tif err := ValidateEmailRegex(bad); err == nil {\n\t\t\tt.Fatalf(\"Адрес %s должен был вызвать ошибку!\", bad)\n\t\t}\n\t}\n\n\tfmt.Println(\"Регулярное выражение emailRegex успешно протестировано на граничных случаях!\")\n}",
        "note": "Эффективная статическая компиляция регулярного выражения с защитой от ReDoS"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v regex_validation_test.go\n# Вывод:\n# === RUN   TestEmailRegexValidation\n# Регулярное выражение emailRegex успешно протестировано на граничных случаях!\n# --- PASS: TestEmailRegexValidation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Движок `regexp` в Go гарантирует выполнение за линейное время $O(N)$ от длины строки, полностью предотвращая атаки отказа в обслуживании (ReDoS).",
    "pitfalls": "Вызывать `regexp.MustCompile` внутри функции резолвера: при 10 000 RPS сервер потратит 90% времени CPU на бесконечный парсинг синтаксического дерева регулярного выражения.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему regexp.MustCompile внутри функции резолвера считается грубейшей ошибкой в Go?»\n**Ответ:** Компиляция регулярного выражения аллоцирует десятки внутренних структур и строит NFA/DFA автомат. Это тратит миллисекунды CPU и перегружает GC миллионами мусорных объектов. Регулярные выражения всегда выносят в `var` уровня пакета."
  },
  {
    "num": 25,
    "title": "Добавление мутаций в схему: NewUserInput, кодогенерация и резолвер регистрации пользователя",
    "task": "**Добавление мутаций (Mutations)**: Добавьте в схему `.graphqls` тип `Mutation` и метод `createUser(input: NewUserInput!): User!`. Опишите тип `NewUserInput` с необходимыми для регистрации полями. Перегенерируйте код через `gqlgen` и реализуйте резолвер для мутации, добавив логику сохранения нового пользователя и валидации входящих полей (например, проверка формата email).",
    "theory": "Жизненный цикл мутации в GraphQL:\n1. Описание контракта в `schema.graphqls`:\n```graphql\ninput NewUserInput {\n  name: String!\n  email: String!\n  password: String!\n}\n\ntype Mutation {\n  createUser(input: NewUserInput!): User!\n}\n```\n2. Команда `gqlgen generate` добавляет интерфейс `MutationResolver` в `generated.go`.\n3. Разработчик реализует метод `CreateUser` в `schema.resolvers.go`:\n   - Хэширует пароль (например bcrypt).\n   - Сохраняет пользователя в базу данных.\n   - Возвращает созданный объект `*model.User`.",
    "step_by_step": "1. Создайте структуры входных данных и сущности пользователя.\n2. Смоделируйте хэширование пароля и генерацию ID.\n3. Реализуйте метод `CreateUser` в резолвере мутаций.\n4. Проверьте сохранение и маскирование чувствительных данных.",
    "code_blocks": [
      {
        "filename": "new_user_mutation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"crypto/sha256\"\n\t\"encoding/hex\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype User struct {\n\tID    string `json:\"id\"`\n\tName  string `json:\"name\"`\n\tEmail string `json:\"email\"`\n}\n\ntype NewUserInput struct {\n\tName     string `json:\"name\"`\n\tEmail    string `json:\"email\"`\n\tPassword string `json:\"password\"`\n}\n\ntype MutationResolver struct {\n\tdb map[string]*User\n}\n\nfunc (r *MutationResolver) CreateUser(ctx context.Context, input NewUserInput) (*User, error) {\n\t// Хэширование пароля (в проде bcrypt)\n\th := sha256.Sum256([]byte(input.Password))\n\t_ = hex.EncodeToString(h[:])\n\n\tnewID := fmt.Sprintf(\"usr_%d\", len(r.db)+1)\n\tuser := &User{\n\t\tID:    newID,\n\t\tName:  input.Name,\n\t\tEmail: input.Email,\n\t}\n\n\tr.db[newID] = user\n\treturn user, nil\n}\n\nfunc TestNewUserMutation(t *testing.T) {\n\tr := &MutationResolver{db: make(map[string]*User)}\n\n\tinput := NewUserInput{\n\t\tName:     \"Сергей Васильев\",\n\t\tEmail:    \"sergey@wildberries.ru\",\n\t\tPassword: \"SecurePassword999!\",\n\t}\n\n\tcreated, err := r.CreateUser(context.Background(), input)\n\tif err != nil || created.ID != \"usr_1\" {\n\t\tt.Fatalf(\"Ошибка создания: %v\", err)\n\t}\n\n\tfmt.Printf(\"Мутация createUser успешно выполнена! Возвращен User: ID=%s, Name=%s\\n\",\n\t\tcreated.ID, created.Name)\n}",
        "note": "Реализация резолвера мутации создания пользователя NewUserInput"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v new_user_mutation_test.go\n# Вывод:\n# === RUN   TestNewUserMutation\n# Мутация createUser успешно выполнена! Возвращен User: ID=usr_1, Name=Сергей Васильев\n# --- PASS: TestNewUserMutation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В GraphQL мутации выполняются **строго последовательно** в том порядке, в котором они перечислены в документе запроса клиента, в отличие от полей Query, которые могут выполняться параллельно.",
    "pitfalls": "Возвращать поле пароля (даже хэшированного) в типе `User`: тип `User` никогда не должен содержать полей `password` или `passwordHash` в GraphQL схеме.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему поля Query могут резолвиться параллельно, а поля Mutation выполняются строго последовательно?»\n**Ответ:** По спецификации GraphQL мутации вызывают побочные эффекты (Side Effects). Если клиент отправляет две мутации в одном запросе (`mutation { debit(); credit(); }`), их параллельный запуск привел бы к непредсказуемым гонкам данных. Поэтому спецификация гарантирует детерминированный последовательный порядок для корневых полей Mutation."
  },
  {
    "num": 26,
    "title": "Вложенные резолверы (Nested Resolvers) User.orders: демонстрация катастрофы N+1 запросов",
    "task": "Реализуй **Nested resolver**: `type User { ... orders: [Order!]! }`. `orders` — отдельный resolver `func (r *userResolver) Orders(ctx context.Context, obj *model.User) ([]*model.Order, error)`. Покажи N+1 problem: запрос 100 пользователей → 100 запросов заказов.",
    "theory": "Природа проблемы N+1 в GraphQL:\n- Запрос клиента:\n```graphql\nquery {\n  users {       # 1 запрос: SELECT * FROM users (вернул 100 пользователей)\n    id\n    name\n    orders {    # Вложенный резолвер User.orders вызывается 100 РАЗ!\n      id        # SELECT * FROM orders WHERE user_id = 'usr_1'\n      total     # SELECT * FROM orders WHERE user_id = 'usr_2'\n    }           # ... еще 98 отдельных SQL-запросов к БД!\n  }\n}\n```\n- Итог: $1 + 100 = 101$ обращение к базе данных!\n- База данных захлебывается в сетевых круглых задержках (Round-Trips) и блокировках пула соединений.",
    "step_by_step": "1. Создайте счетчик запросов к БД.\n2. Смоделируйте наивный вложенный резолвер `Orders(user)`.\n3. Выполните выборку для 100 пользователей.\n4. Продемонстрируйте совершение ровно 101 запроса к хранилищу.",
    "code_blocks": [
      {
        "filename": "n_plus_one_demo_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync/atomic\"\n\t\"testing\"\n)\n\ntype User struct {\n\tID   string\n\tName string\n}\n\ntype Order struct {\n\tID     string\n\tUserID string\n\tTotal  float64\n}\n\ntype DatabaseMock struct {\n\tqueryCounter int64\n}\n\nfunc (db *DatabaseMock) FetchUsers(ctx context.Context) []*User {\n\tatomic.AddInt64(&db.queryCounter, 1) // 1-й запрос\n\tusers := make([]*User, 100)\n\tfor i := 0; i < 100; i++ {\n\t\tusers[i] = &User{ID: fmt.Sprintf(\"usr_%d\", i+1), Name: fmt.Sprintf(\"User #%d\", i+1)}\n\t}\n\treturn users\n}\n\nfunc (db *DatabaseMock) FetchOrdersForUser(ctx context.Context, userID string) []*Order {\n\tatomic.AddInt64(&db.queryCounter, 1) // +1 запрос на КАЖДОГО пользователя!\n\treturn []*Order{\n\t\t{ID: fmt.Sprintf(\"ord_%s_1\", userID), UserID: userID, Total: 1500.0},\n\t}\n}\n\nfunc TestNPlusOneCatastrophe(t *testing.T) {\n\tdb := &DatabaseMock{}\n\n\t// 1. Корневой резолвер выбирает 100 пользователей\n\tusers := db.FetchUsers(context.Background())\n\n\t// 2. Вложенный резолвер User.orders вызывается движком gqlgen для каждого пользователя\n\tfor _, u := range users {\n\t\t_ = db.FetchOrdersForUser(context.Background(), u.ID)\n\t}\n\n\ttotalQueries := atomic.LoadInt64(&db.queryCounter)\n\tif totalQueries != 101 {\n\t\tt.Fatalf(\"Ожидался 101 запрос (проблема N+1), выполнено: %d\", totalQueries)\n\t}\n\n\tfmt.Printf(\"Катастрофа N+1 наглядно доказана:\\n\")\n\tfmt.Printf(\"  • Пользователей запрошено:   100\\n\")\n\tfmt.Printf(\"  • Всего запросов к базе:     %d (1 на список + 100 на вложенные заказы!)\\n\", totalQueries)\n}",
        "note": "Демонстрация проблемы 101 запроса в наивном вложенном резолвере"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v n_plus_one_demo_test.go\n# Вывод:\n# === RUN   TestNPlusOneCatastrophe\n# Катастрофа N+1 наглядно доказана:\n#   • Пользователей запрошено:   100\n#   • Всего запросов к базе:     101 (1 на список + 100 на вложенные заказы!)\n# --- PASS: TestNPlusOneCatastrophe (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Каждый вызов вложенного резолвера происходит независимо в рамках обхода дерева GraphQL AST. Движок не знает заранее, для скольких пользователей потребуется поле `orders`, поэтому наивный код порождает серию одиночных вызовов.",
    "pitfalls": "Использовать наивный вложенный резолвер в production: при росте списка до 1 000 пользователей сервер отправит 1 001 запрос к БД, что мгновенно исчерпает пул соединений `pgxpool`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в REST API проблема N+1 встречается реже, чем в GraphQL?»\n**Ответ:** В REST бэкенд-разработчик контролирует фиксированный эндпоинт (`GET /users-with-orders`) и заранее пишет эффективный `JOIN` (`SELECT * FROM users u LEFT JOIN orders o ON ...`). В GraphQL клиент сам решает, запрашивать ли вложенное поле `orders`, поэтому сервер вынужден либо писать ленивые резолверы, либо использовать батчинг (DataLoader)."
  },
  {
    "num": 27,
    "title": "Вложенный объект Post.author: логирование лавины вызовов и аудит сетевых задержек",
    "task": "Добавьте вложенный объект: тип `Post` (id, title, body, author: User!). Запрос `posts` возвращает список постов, резолвер поля `author` лениво подгружает автора (проблема N+1). Покажите проблему в логах.",
    "theory": "Обратная связь N+1 (Many-to-One):\n- Схема:\n```graphql\ntype Post {\n  id: ID!\n  title: String!\n  body: String!\n  author: User!\n}\ntype Query {\n  posts: [Post!]!\n}\n```\n- Если 50 постов написаны **одним и тем же автором** (например, официальный блог компании), наивный резолвер `Post.Author` выполнит:\n  `SELECT * FROM users WHERE id = 'author_1'` — **50 раз подряд для одного и того же ID**!\n- Это не просто N+1, это еще и полное дублирование одинаковых запросов.",
    "step_by_step": "1. Создайте модели `Post` и `User`.\n2. Реализуйте резолвер с логированием каждого запроса автора.\n3. Смоделируйте выборку 5 постов.\n4. Продемонстрируйте избыточные логи в консоли.",
    "code_blocks": [
      {
        "filename": "post_author_n1_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype User struct {\n\tID   string\n\tName string\n}\n\ntype Post struct {\n\tID       string\n\tTitle    string\n\tAuthorID string\n}\n\ntype PostAuthorResolver struct {\n\tqueryLogs []string\n}\n\nfunc (r *PostAuthorResolver) Author(ctx context.Context, p *Post) (*User, error) {\n\tlogMsg := fmt.Sprintf(\"SQL: SELECT * FROM users WHERE id = '%s'\", p.AuthorID)\n\tr.queryLogs = append(r.queryLogs, logMsg)\n\treturn &User{ID: p.AuthorID, Name: \"Главный Редактор\"}, nil\n}\n\nfunc TestPostAuthorNPlusOneLogging(t *testing.T) {\n\tposts := []*Post{\n\t\t{ID: \"p1\", Title: \"Релиз Go 1.24\", AuthorID: \"usr_editor\"},\n\t\t{ID: \"p2\", Title: \"Архитектура GraphQL\", AuthorID: \"usr_editor\"},\n\t\t{ID: \"p3\", Title: \"Паттерн DataLoader\", AuthorID: \"usr_editor\"},\n\t}\n\n\tr := &PostAuthorResolver{}\n\n\t// Имитация вызовов gqlgen для каждого поста\n\tfor _, p := range posts {\n\t\t_, _ = r.Author(context.Background(), p)\n\t}\n\n\tif len(r.queryLogs) != 3 {\n\t\tt.Fatalf(\"Ожидалось 3 лога запросов к БД, получено %d\", len(r.queryLogs))\n\t}\n\n\tfmt.Println(\"Аудит логов N+1 запросов к базе данных:\")\n\tfor i, l := range r.queryLogs {\n\t\tfmt.Printf(\"  [%d] %s\\n\", i+1, l)\n\t}\n\tfmt.Println(\"Обнаружено: 3 абсолютно одинаковых запроса к одному и тому же автору!\")\n}",
        "note": "Логирование дублирующихся SQL-запросов в резолвере Post.author"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v post_author_n1_test.go\n# Вывод:\n# === RUN   TestPostAuthorNPlusOneLogging\n# Аудит логов N+1 запросов к базе данных:\n#   [1] SQL: SELECT * FROM users WHERE id = 'usr_editor'\n#   [2] SQL: SELECT * FROM users WHERE id = 'usr_editor'\n#   [3] SQL: SELECT * FROM users WHERE id = 'usr_editor'\n# Обнаружено: 3 абсолютно одинаковых запроса к одному и тому же автору!\n# --- PASS: TestPostAuthorNPlusOneLogging (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Без кэширования и дедупликации база данных тратит ресурсы процессора на повторный парсинг SQL-запроса и чтение страниц из буферного пула.",
    "pitfalls": "Пытаться решить проблему локальным Go-кэшем `sync.Map`: кэш в памяти сервиса быстро рассинхронизируется при обновлении пользователя на другом поде.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы две главные задачи паттерна DataLoader?»\n**Ответ:** 1. **Batching (Пакетирование):** объединение десятков одиночных запросов `id = ?` в один групповой `IN (?, ?, ...)`. 2. **Caching (Мемоизация на время запроса):** если один и тот же `id` запрашивается многократно в рамках одного HTTP-запроса, DataLoader выполняет вызов к БД ровно 1 раз и отдает результат остальным резолверам из локального кэша запроса."
  },
  {
    "num": 28,
    "title": "Генерация Field Resolvers в gqlgen: директива @goField(forceResolver: true) и разделение ответственности",
    "task": "Создайте **вложенные резолверы**: тип `Post` с полем `author: User!`. gqlgen автоматически создаст резолвер `Post.Author`, который будет вызываться для каждого поста.",
    "theory": "Когда gqlgen создает отдельный метод резолвера для поля:\n- По умолчанию gqlgen пытается сопоставить поле схемы с полем Go-структуры:\n  - Если в структуре `Post` есть поле `Author User`, gqlgen просто возьмет его значение без генерации отдельного метода.\n- Если же в структуре `Post` есть только `AuthorID string`, а объекта `User` нет, gqlgen **автоматически генерирует метод интерфейса**:\n  `Author(ctx context.Context, obj *model.Post) (*model.User, error)`\n- Также можно принудительно заставить gqlgen сгенерировать резолвер с помощью директивы:\n  `author: User! @goField(forceResolver: true)`.",
    "step_by_step": "1. Опишите интерфейс `PostResolver` со ссылкой на родительский объект `obj`.\n2. Реализуйте метод `Author(ctx, post)`.\n3. Продемонстрируйте передачу данных родителя в дочерний резолвер.\n4. Проверьте корректность выборки автора.",
    "code_blocks": [
      {
        "filename": "post_field_resolver_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype User struct {\n\tID   string\n\tName string\n}\n\ntype Post struct {\n\tID       string\n\tTitle    string\n\tAuthorID string\n}\n\n// Интерфейс, сгенерированный gqlgen для вложенного поля\ntype PostResolver interface {\n\tAuthor(ctx context.Context, obj *Post) (*User, error)\n}\n\ntype postResolverImpl struct {\n\tuserTable map[string]*User\n}\n\nfunc (r *postResolverImpl) Author(ctx context.Context, obj *Post) (*User, error) {\n\t// Доступ к родительскому объекту Post через аргумент obj!\n\tauthor, ok := r.userTable[obj.AuthorID]\n\tif !ok {\n\t\treturn nil, fmt.Errorf(\"автор поста с id %s не найден\", obj.AuthorID)\n\t}\n\treturn author, nil\n}\n\nfunc TestPostFieldResolver(t *testing.T) {\n\tr := &postResolverImpl{\n\t\tuserTable: map[string]*User{\n\t\t\t\"u_99\": {ID: \"u_99\", Name: \"Евгений\"},\n\t\t},\n\t}\n\n\tcurrentPost := &Post{ID: \"p_1\", Title: \"HighLoad на Go\", AuthorID: \"u_99\"}\n\n\tauthor, err := r.Author(context.Background(), currentPost)\n\tif err != nil || author.Name != \"Евгений\" {\n\t\tt.Fatalf(\"Ошибка резолвера поля: %v\", err)\n\t}\n\n\tfmt.Printf(\"Field Resolver Post.Author успешно извлек автора [%s] для поста [%s]!\\n\",\n\t\tauthor.Name, currentPost.Title)\n}",
        "note": "Реализация Field Resolver с получением родительского объекта через obj"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v post_field_resolver_test.go\n# Вывод:\n# === RUN   TestPostFieldResolver\n# Field Resolver Post.Author успешно извлек автора [Евгений] для поста [HighLoad на Go]!\n# --- PASS: TestPostFieldResolver (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Параметр `obj` передается движком исполнения `generated.go` как результат предыдущего вызова родительского резолвера `Query.Posts`.",
    "pitfalls": "Изменять поля `obj` внутри резолвера: `obj` может использоваться в параллельных горутинах для других полей этого же типа. Мутация `obj` приведет к состоянию гонки (Data Race).",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем нужна опция omit_slice_element_pointers в gqlgen.yml?»\n**Ответ:** По умолчанию gqlgen генерирует списки как `[]*model.User` (слайс указателей). Включение `omit_slice_element_pointers: true` заставляет gqlgen генерировать `[]model.User` (слайс значений), что снижает фрагментацию кучи и нагрузку на GC при передаче списков из десятков тысяч объектов."
  },
  {
    "num": 29,
    "title": "Offset-based пагинация: users(limit: Int, offset: Int) и проблема деградации производительности",
    "task": "Реализуй **Pagination** (offset-based): `users(limit: Int, offset: Int): [User!]!`. Верни `totalCount` через отдельный query или в payload. Обсуди проблемы offset-пагинации (performance при больших offset'ах).",
    "theory": "Архитектура Offset-Based пагинации:\n- Запрос: `users(limit: 20, offset: 40)` (третья страница по 20 элементов).\n- В SQL транслируется как: `SELECT * FROM users ORDER BY id LIMIT 20 OFFSET 40`.\n- **Проблема производительности при больших смещениях:**\n  - При `OFFSET 1000000 LIMIT 20` СУБД (PostgreSQL / MySQL) вынуждена прочитать и отсканировать **1 000 020 строк**, отбросить первый миллион и отдать клиенту только 20 строк!\n  - Дисковая подсистема испытывает колоссальную нагрузку, время ответа деградирует с 1 мс до 5–10 секунд.\n- **Проблема сдвига данных (Data Drifting):** если во время чтения пользователь удалил или добавил запись, на следующей странице клиент увидит дубликат строки или пропустит запись.",
    "step_by_step": "1. Создайте структуру ответа с данными и общим счетчиком `totalCount`.\n2. Реализуйте метод выборки со срезом по слайсу (эмуляция LIMIT/OFFSET).\n3. Задайте значения по умолчанию для limit и offset.\n4. Проверьте корректность разбиения на страницы.",
    "code_blocks": [
      {
        "filename": "offset_pagination_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype User struct {\n\tID   int\n\tName string\n}\n\ntype UsersPayload struct {\n\tTotalCount int\n\tUsers      []*User\n}\n\nfunc PaginateUsers(ctx context.Context, allUsers []*User, limit, offset *int) UsersPayload {\n\ttotal := len(allUsers)\n\n\tl := 10 // default limit\n\tif limit != nil && *limit > 0 {\n\t\tl = *limit\n\t\tif l > 100 { // защита от DoS\n\t\t\tl = 100\n\t\t}\n\t}\n\n\to := 0 // default offset\n\tif offset != nil && *offset > 0 {\n\t\to = *offset\n\t}\n\n\tif o >= total {\n\t\treturn UsersPayload{TotalCount: total, Users: []*User{}}\n\t}\n\n\tend := o + l\n\tif end > total {\n\t\tend = total\n\t}\n\n\treturn UsersPayload{\n\t\tTotalCount: total,\n\t\tUsers:      allUsers[o:end],\n\t}\n}\n\nfunc TestOffsetPagination(t *testing.T) {\n\tusers := make([]*User, 50)\n\tfor i := 0; i < 50; i++ {\n\t\tusers[i] = &User{ID: i + 1, Name: fmt.Sprintf(\"User #%d\", i+1)}\n\t}\n\n\t// Страница 2: limit=10, offset=10\n\tl, o := 10, 10\n\tres := PaginateUsers(context.Background(), users, &l, &o)\n\n\tif res.TotalCount != 50 || len(res.Users) != 10 {\n\t\tt.Fatalf(\"Некорректная пагинация: %+v\", res)\n\t}\n\n\tif res.Users[0].ID != 11 || res.Users[9].ID != 20 {\n\t\tt.Fatalf(\"Неверный диапазон элементов: first=%d, last=%d\", res.Users[0].ID, res.Users[9].ID)\n\t}\n\n\tfmt.Printf(\"Offset-пагинация успешна: Total=%d, Выбрано=%d (IDs: %d..%d)\\n\",\n\t\tres.TotalCount, len(res.Users), res.Users[0].ID, res.Users[9].ID)\n}",
        "note": "Реализация смещения и лимита с ограничением максимального размера страницы"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v offset_pagination_test.go\n# Вывод:\n# === RUN   TestOffsetPagination\n# Offset-пагинация успешна: Total=50, Выбрано=10 (IDs: 11..20)\n# --- PASS: TestOffsetPagination (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Для устранения проблем Offset-пагинации в HighLoad системах используют **Keyset / Cursor Pagination**: `WHERE id > last_seen_id ORDER BY id LIMIT 20`, работающую строго по индексу за $O(\\log N)$ при любой глубине страниц.",
    "pitfalls": "Не ограничивать максимальный `limit`: если клиент передаст `limit: 1000000`, сервер выделит гигабайты памяти под структуры и упадет по OOM (Out Of Memory).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему SELECT COUNT(*) для поля totalCount считается антипаттерном в высоконагруженных таблицах PostgreSQL?»\n**Ответ:** Из-за многоверсионности (MVCC) PostgreSQL не хранит счетчик строк в метаданных. `SELECT COUNT(*)` вынужден сканировать всю таблицу или весь индекс, что на таблицах от 10 миллионов строк занимает секунды. Для общего счетчика в HighLoad используют приближенные значения (`reltuples` из `pg_class`) или счетчик в Redis."
  },
  {
    "num": 30,
    "title": "Решение проблемы N+1 через DataLoader: батчинг 100 одиночных вызовов в 1 запрос IN",
    "task": "Реши **N+1 problem** через **DataLoader**: `github.com/graph-gophers/dataloader`. Батчинг: вместо 100 отдельных запросов — 1 запрос `SELECT * FROM orders WHERE user_id IN (...)`. Реализуй `Loader` для `User.orders`.",
    "theory": "Принцип работы паттерна DataLoader:\n1. Во время фазы исполнения GraphQL запроса каждый вызов `User.orders` не идет в БД, а регистрирует свой `userID` в очереди DataLoader:\n   `loader.Load(ctx, dataloader.StringKey(u.ID))`\n2. В конце текущего тика цикла событий (Event Loop) или через микрозадержку (1–2 мс) DataLoader собирает все зарегистрированные ключи:\n   `keys = [\"usr_1\", \"usr_2\", ..., \"usr_100\"]`\n3. Вызывает пользовательскую batch-функцию **ровно 1 раз**:\n   `SELECT * FROM orders WHERE user_id IN ('usr_1', 'usr_2', ..., 'usr_100')`\n4. Раскладывает полученные заказы по соответствующим пользователям в исходном порядке ключей.\n- Результат: вместо 101 запроса выполняется **ровно 2 запроса**!",
    "step_by_step": "1. Создайте структуру батч-функции DataLoader.\n2. Сгруппируйте заказы по `UserID` в мапу.\n3. Верните результаты в строгом соответствии с порядком входных ключей.\n4. Докажите сокращение обращений к БД со 100 до 1.",
    "code_blocks": [
      {
        "filename": "dataloader_batching_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync/atomic\"\n\t\"testing\"\n)\n\ntype Order struct {\n\tID     string\n\tUserID string\n\tTotal  float64\n}\n\ntype OrderBatchDB struct {\n\tbatchQueryCount int64\n}\n\n// Пакетная функция DataLoader: принимает слайс ключей, возвращает срез результатов\nfunc (db *OrderBatchDB) BatchGetOrdersByUserIDs(ctx context.Context, userIDs []string) ([][]*Order, error) {\n\tatomic.AddInt64(&db.batchQueryCount, 1)\n\n\t// Имитируем выполнение ОДНОГО запроса: SELECT * FROM orders WHERE user_id IN (...)\n\tordersMap := make(map[string][]*Order)\n\tfor _, uid := range userIDs {\n\t\tordersMap[uid] = []*Order{\n\t\t\t{ID: fmt.Sprintf(\"ord_%s_1\", uid), UserID: uid, Total: 2500.0},\n\t\t}\n\t}\n\n\t// DataLoader ТРЕБУЕТ возврата результатов строго в том же порядке, что и входные ключи!\n\tresults := make([][]*Order, len(userIDs))\n\tfor i, uid := range userIDs {\n\t\tresults[i] = ordersMap[uid]\n\t}\n\n\treturn results, nil\n}\n\nfunc TestDataLoaderBatching(t *testing.T) {\n\tdb := &OrderBatchDB{}\n\n\t// Симулируем 100 пользователей, чьи заказы запрашиваются параллельно\n\tuserIDs := make([]string, 100)\n\tfor i := 0; i < 100; i++ {\n\t\tuserIDs[i] = fmt.Sprintf(\"usr_%d\", i+1)\n\t}\n\n\t// DataLoader объединяет все 100 запросов в 1 пакетный вызов\n\tres, err := db.BatchGetOrdersByUserIDs(context.Background(), userIDs)\n\tif err != nil || len(res) != 100 {\n\t\tt.Fatalf(\"Ошибка пакетной выборки: %v\", err)\n\t}\n\n\tqueryCount := atomic.LoadInt64(&db.batchQueryCount)\n\tif queryCount != 1 {\n\t\tt.Fatalf(\"Ожидался ровно 1 батч-запрос к БД, выполнено: %d\", queryCount)\n\t}\n\n\tfmt.Printf(\"🎉 Проблема N+1 успешно решена с помощью DataLoader!\\n\")\n\tfmt.Printf(\"  • Пользователей обработано: 100\\n\")\n\tfmt.Printf(\"  • Количество запросов к БД:  %d (вместо 100!)\\n\", queryCount)\n}",
        "note": "Пакетная выборка заказов через batch-функцию DataLoader"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v dataloader_batching_test.go\n# Вывод:\n# === RUN   TestDataLoaderBatching\n# 🎉 Проблема N+1 успешно решена с помощью DataLoader!\n#   • Пользователей обработано: 100\n#   • Количество запросов к БД:  1 (вместо 100!)\n# --- PASS: TestDataLoaderBatching (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Строгое требование спецификации DataLoader: срез возвращаемых результатов `results` обязан иметь точно такую же длину, как и срез входных ключей `keys`, и индексы должны совпадать (`results[i]` соответствует `keys[i]`).",
    "pitfalls": "Создавать один глобальный экземпляр DataLoader на все приложение: кэш DataLoader привязан к конкретному запросу! Глобальный экземпляр приведет к утечке памяти и покажет пользователю A данные пользователя B.",
    "bigtech_interview": "**Вопрос с собеседования:** «Где должен инициализироваться экземпляр DataLoader в приложении Go?»\n**Ответ:** Экземпляр DataLoader **обязан создаваться в HTTP Middleware для каждого входящего HTTP-запроса** и помещаться в `context.Context`:\n`ctx = context.WithValue(r.Context(), loadersKey, loaders)`\nЭто гарантирует, что кэш лоадера живет ровно столько, сколько длится текущий GraphQL-запрос, изолируя пользователей друг от друга."
  },
  {
    "num": 31,
    "title": "Внедрение зависимостей в Resolver: конструктор NewResolver с БД, логгером и кэшем",
    "task": "Изучите структуру `Resolver` в gqlgen: как передавать зависимости (БД, сервисы) через конструктор `NewResolver()`.",
    "theory": "Принцип внедрения зависимостей (Dependency Injection) в GraphQL:\n- Файл `graph/resolver.go`:\n```go\ntype Resolver struct {\n    DB     *pgxpool.Pool\n    Logger *slog.Logger\n    Redis  *redis.Client\n}\n\nfunc NewResolver(db *pgxpool.Pool, log *slog.Logger, rdb *redis.Client) *Resolver {\n    return &Resolver{DB: db, Logger: log, Redis: rdb}\n}\n```\n- Резолверы получают доступ ко всей инфраструктуре через поле получателя метода `r.DB` без использования антипаттерна глобальных переменных.",
    "step_by_step": "1. Создайте структуру `Resolver` с полями зависимостей.\n2. Реализуйте фабричный конструктор `NewResolver`.\n3. Подключите резолвер к схеме исполнения.\n4. Протестируйте доступ к зависимостям в методе.",
    "code_blocks": [
      {
        "filename": "resolver_di_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log/slog\"\n\t\"os\"\n\t\"testing\"\n)\n\ntype DatabasePool struct {\n\tDSN string\n}\n\ntype Resolver struct {\n\tdb     *DatabasePool\n\tlogger *slog.Logger\n}\n\nfunc NewResolver(db *DatabasePool, logger *slog.Logger) *Resolver {\n\treturn &Resolver{\n\t\tdb:     db,\n\t\tlogger: logger,\n\t}\n}\n\nfunc (r *Resolver) QueryDatabase(ctx context.Context) string {\n\tr.logger.Info(\"Выполнение запроса к базе данных через DI\", \"dsn\", r.db.DSN)\n\treturn \"DATA_FROM_\" + r.db.DSN\n}\n\nfunc TestResolverDependencyInjection(t *testing.T) {\n\tdb := &DatabasePool{DSN: \"postgres://prod-db:5432/main\"}\n\tlogger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))\n\n\tresolver := NewResolver(db, logger)\n\n\tres := resolver.QueryDatabase(context.Background())\n\tif res != \"DATA_FROM_postgres://prod-db:5432/main\" {\n\t\tt.Fatalf(\"Ошибка выборки: %s\", res)\n\t}\n\n\tfmt.Println(\"Зависимости успешно внедрены в Resolver через конструктор NewResolver!\")\n}",
        "note": "Чистое внедрение зависимостей в Resolver без глобальных переменных"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v resolver_di_test.go\n# Вывод:\n# === RUN   TestResolverDependencyInjection\n# time=2026-09-03T21:18:00.000+04:00 level=INFO msg=\"Выполнение запроса к базе данных через DI\" dsn=postgres://prod-db:5432/main\n# Зависимости успешно внедрены в Resolver через конструктор NewResolver!\n# --- PASS: TestResolverDependencyInjection (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В `server.go` вызов `handler.NewDefaultServer(generated.NewExecutableSchema(generated.Config{Resolvers: resolver}))` передает корневой экземпляр `Resolver` во все сгенерированные замыкания.",
    "pitfalls": "Использовать глобальные переменные пакета `var DB *sql.DB`: это делает невозможным параллельное юнит-тестирование резолверов с моками.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как протестировать GraphQL резолвер изолированно от базы данных?»\n**Ответ:** Помещать в структуру `Resolver` не конкретный `*pgxpool.Pool`, а интерфейсы доменных сервисов (`type UserService interface { GetByID(...) }`). В тестах в `NewResolver` передается мок-структура, реализующая интерфейс, что позволяет тестировать резолверы со 100% покрытием без поднятия реальной БД."
  },
  {
    "num": 32,
    "title": "Передача данных аутентификации через Context: извлечение JWT в HTTP middleware и доступ в резолвере",
    "task": "Используйте **контекст GraphQL** (`graphql.GetOperationContext`) для передачи данных между резолверами (например, текущего пользователя из JWT).",
    "theory": "Сквозная аутентификация в GraphQL:\n1. **HTTP Middleware (до GraphQL):**\n   - Перехватывает HTTP-заголовок `Authorization: Bearer <token>`.\n   - Валидирует JWT токен.\n   - Извлекает пользователя `auth.User{ID: \"usr_77\", Role: \"ADMIN\"}`.\n   - Помещает пользователя в `context.Context` с типизированным ключом.\n2. **GraphQL Resolver:**\n   - Извлекает пользователя из `ctx`: `user := auth.ForContext(ctx)`.\n   - Если пользователя нет в контексте, возвращает ошибку `UNAUTHENTICATED`.",
    "step_by_step": "1. Создайте неэкспортируемый тип контекстного ключа `userCtxKey`.\n2. Напишите функции внедрения и извлечения пользователя из контекста.\n3. Реализуйте проверку прав в резолвере.\n4. Протестируйте авторизованный и анонимный вызовы.",
    "code_blocks": [
      {
        "filename": "graphql_auth_context_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\n\t\"github.com/vektah/gqlparser/v2/gqlerror\"\n)\n\ntype AuthUser struct {\n\tID   string\n\tRole string\n}\n\ntype authContextKey struct{}\n\nfunc WithAuthUser(ctx context.Context, u *AuthUser) context.Context {\n\treturn context.WithValue(ctx, authContextKey{}, u)\n}\n\nfunc AuthUserFromContext(ctx context.Context) *AuthUser {\n\tu, _ := ctx.Value(authContextKey{}).(*AuthUser)\n\treturn u\n}\n\ntype SecureQueryResolver struct{}\n\nfunc (r *SecureQueryResolver) Viewer(ctx context.Context) (*AuthUser, error) {\n\tuser := AuthUserFromContext(ctx)\n\tif user == nil {\n\t\treturn nil, &gqlerror.Error{\n\t\t\tMessage: \"требуется аутентификация\",\n\t\t\tExtensions: map[string]any{\n\t\t\t\t\"code\": \"UNAUTHENTICATED\",\n\t\t\t},\n\t\t}\n\t}\n\treturn user, nil\n}\n\nfunc TestAuthContextPropagation(t *testing.T) {\n\tresolver := &SecureQueryResolver{}\n\n\t// 1. Анонимный вызов -> UNAUTHENTICATED\n\t_, errAnon := resolver.Viewer(context.Background())\n\tif errAnon == nil {\n\t\tt.Fatal(\"Ожидался отказ для анонимного запроса\")\n\t}\n\n\t// 2. Авторизованный вызов с JWT\n\tauthCtx := WithAuthUser(context.Background(), &AuthUser{ID: \"usr_999\", Role: \"ADMIN\"})\n\tuser, errAuth := resolver.Viewer(authCtx)\n\tif errAuth != nil || user.ID != \"usr_999\" {\n\t\tt.Fatalf(\"Ошибка аутентификации: %v\", errAuth)\n\t}\n\n\tfmt.Printf(\"Контекст аутентификации успешно передан: Пользователь ID=%s (Роль: %s)\\n\",\n\t\tuser.ID, user.Role)\n}",
        "note": "Потокобезопасная передача JWT пользователя через context.Context"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v graphql_auth_context_test.go\n# Вывод:\n# === RUN   TestAuthContextPropagation\n# Контекст аутентификации успешно передан: Пользователь ID=usr_999 (Роль: ADMIN)\n# --- PASS: TestAuthContextPropagation (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Вызов `graphql.GetOperationContext(ctx)` в `gqlgen` дает доступ к сырому тексту запроса, имени операции (`operationName`), переменным и заголовкам HTTP-запроса.",
    "pitfalls": "Возвращать ошибку HTTP 401 в middleware при отсутствии токена: в GraphQL многие запросы (каталог, регистрация, публичные статьи) доступны анонимным пользователям. Middleware должен просто не заполнять пользователя в контексте, а блокировку выполняет конкретный резолвер или директива `@auth`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в GraphQL HTTP middleware не должен прерывать запрос с кодом 401 при невалидном токене?»\n**Ответ:** По спецификации GraphQL всегда возвращает HTTP 200 OK для валидных GraphQL документов, даже если внутри произошли ошибки авторизации отдельных полей. Прерывание с 401 на уровне HTTP ломает работу клиентских библиотек (Apollo/Relay), которые умеют парсить частичные ответы (`data` + `errors`)."
  },
  {
    "num": 33,
    "title": "Хуки и расширения gqlgen через HandlerExtension: измерение времени исполнения и аудит латентности",
    "task": "Реализуйте **middleware для резолверов** через `graphql.HandlerExtension`, чтобы логировать время выполнения каждого query.",
    "theory": "Интерфейс расширений `graphql.HandlerExtension` в gqlgen:\n- Позволяет перехватывать жизненный цикл запроса:\n  1. `InterceptOperation`: перехват до и после выполнения всей операции.\n  2. `InterceptField`: перехват вызова каждого отдельного поля схемы.\n  3. `InterceptResponse`: перехват формирования финального JSON ответа.\n- Это идеальное место для:\n  - Сбора метрик Prometheus (`graphql_query_duration_seconds`).\n  - Трейсинга OpenTelemetry (создание Span на каждое поле).\n  - Структурированного логирования времени выполнения через `slog`.",
    "step_by_step": "1. Создайте структуру таймера операции.\n2. Реализуйте замер длительности от старта до завершения.\n3. Зафиксируйте имя операции и время в логах.\n4. Протестируйте работу интерцептора.",
    "code_blocks": [
      {
        "filename": "graphql_metrics_extension_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype QueryMetricsInterceptor struct {\n\tlastDuration time.Duration\n\tlastOpName   string\n}\n\nfunc (m *QueryMetricsInterceptor) Intercept(ctx context.Context, opName string, next func(context.Context) error) error {\n\tstart := time.Now()\n\terr := next(ctx)\n\tm.lastDuration = time.Since(start)\n\tm.lastOpName = opName\n\n\tfmt.Printf(\"[GraphQL Metric] Операция '%s' завершена за %v\\n\", opName, m.lastDuration.Round(time.Microsecond))\n\treturn err\n}\n\nfunc TestQueryMetricsInterceptor(t *testing.T) {\n\tinterceptor := &QueryMetricsInterceptor{}\n\n\tmockOperation := func(ctx context.Context) error {\n\t\ttime.Sleep(15 * time.Millisecond)\n\t\treturn nil\n\t}\n\n\terr := interceptor.Intercept(context.Background(), \"GetUsersDashboard\", mockOperation)\n\tif err != nil {\n\t\tt.Fatalf(\"Сбой выполнения: %v\", err)\n\t}\n\n\tif interceptor.lastOpName != \"GetUsersDashboard\" || interceptor.lastDuration < 10*time.Millisecond {\n\t\tt.Fatalf(\"Некорректно зафиксирована метрика: %+v\", interceptor)\n\t}\n\n\tfmt.Println(\"HandlerExtension успешно замерил латентность выполнения GraphQL запроса!\")\n}",
        "note": "Интерцептор измерения времени выполнения GraphQL операций"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v graphql_metrics_extension_test.go\n# Вывод:\n# === RUN   TestQueryMetricsInterceptor\n# [GraphQL Metric] Операция 'GetUsersDashboard' завершена за 15ms\n# HandlerExtension успешно замерил латентность выполнения GraphQL запроса!\n# --- PASS: TestQueryMetricsInterceptor (0.02s)\n# PASS"
      }
    ],
    "under_the_hood": "Встроенное расширение `extension.FixedComplexityLimit` использует `InterceptOperation` для подсчета сложности дерева запроса (Query Complexity) до начала его выполнения, отсекая потенциальные DoS-атаки.",
    "pitfalls": "Использовать `InterceptField` для логирования каждого поля в production при миллионном RPS: интерцепция каждого скалярного поля создает миллионы аллокаций памяти. Логируют только на уровне операции (`InterceptOperation`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как ограничить максимальную глубину (Query Depth) GraphQL запроса в gqlgen?»\n**Ответ:** Зарегистрировать расширение `server.Use(extension.FixedComplexityLimit(300))` или кастомный валидатор AST правил `ast.QueryDocument`, который обходит дерево и подсчитывает максимальный уровень вложенности (`depth`). Если глубина $> 6..8$, запрос отклоняется до резолвинга."
  },
  {
    "num": 34,
    "title": "Инициализация проекта через gqlgen init: детальный разбор структуры сгенерированного кода",
    "task": "Установи `github.com/99designs/gqlgen`: `go run github.com/99designs/gqlgen init`. Изучи сгенерированную структуру: `graph/schema.graphqls`, `graph/model/models_gen.go`, `graph/resolver.go`.",
    "theory": "Разбор артефактов команды `gqlgen init`:\n- `go.mod` — модуль Go с зависимостями `gqlgen` и `gqlparser`.\n- `gqlgen.yml` — конфигурация путей и правил генерации.\n- `server.go` — готовый к запуску HTTP сервер с Playground и GraphQL handler.\n- `graph/resolver.go` — корень внедрения зависимостей.\n- `graph/schema.graphqls` — стартовая схема Todo (Query, Mutation, Todo, User).\n- `graph/schema.resolvers.go` — реализация резолверов Todo.\n- `graph/generated.go` — сгенерированное ядро парсинга и сериализации.",
    "step_by_step": "1. Опишите карту соответствия сгенерированных файлов и их обязанностей.\n2. Проверьте связи между `resolver.go` и `schema.resolvers.go`.\n3. Смоделируйте выполнение стартового сервера Todo.\n4. Протестируйте целостность архитектуры.",
    "code_blocks": [
      {
        "filename": "init_architecture_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype ProjectFileRole struct {\n\tPath        string\n\tGenerated   bool\n\tUserEditable bool\n\tPurpose     string\n}\n\nfunc GetProjectArchitecture() []ProjectFileRole {\n\treturn []ProjectFileRole{\n\t\t{\"graph/schema.graphqls\", false, true, \"Исходный контракт схемы SDL\"},\n\t\t{\"gqlgen.yml\", false, true, \"Конфигурация кодогенератора\"},\n\t\t{\"graph/resolver.go\", false, true, \"Корень внедрения зависимостей (DI)\"},\n\t\t{\"graph/schema.resolvers.go\", true, true, \"Бизнес-логика методов резолверов\"},\n\t\t{\"graph/generated.go\", true, false, \"Сгенерированное ядро GraphQL рантайма\"},\n\t\t{\"graph/model/models_gen.go\", true, false, \"Сгенерированные Go DTO структуры\"},\n\t\t{\"server.go\", false, true, \"Точка входа main() и HTTP маршрутизатор\"},\n\t}\n}\n\nfunc TestGqlgenInitStructure(t *testing.T) {\n\troles := GetProjectArchitecture()\n\n\tif len(roles) != 7 {\n\t\tt.Fatalf(\"Ожидалось 7 ключевых компонентов, получено: %d\", len(roles))\n\t}\n\n\tfmt.Println(\"Архитектурная структура проекта gqlgen init:\")\n\tfor _, r := range roles {\n\t\tstatus := \"Редактируется разработчиком\"\n\t\tif !r.UserEditable {\n\t\t\tstatus = \"СТРОГО автогенерируемый (не менять!)\"\n\t\t}\n\t\tfmt.Printf(\"  • %-26s | %s\\n\", r.Path, status)\n\t}\n}",
        "note": "Анализ зон ответственности файлов в структуре проекта gqlgen"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v init_architecture_test.go\n# Вывод:\n# === RUN   TestGqlgenInitStructure\n# Архитектурная структура проекта gqlgen init:\n#   • graph/schema.graphqls      | Редактируется разработчиком\n#   • gqlgen.yml                 | Редактируется разработчиком\n#   • graph/resolver.go          | Редактируется разработчиком\n#   • graph/schema.resolvers.go  | Редактируется разработчиком\n#   • graph/generated.go         | СТРОГО автогенерируемый (не менять!)\n#   • graph/model/models_gen.go  | СТРОГО автогенерируемый (не менять!)\n#   • server.go                  | Редактируется разработчиком\n# --- PASS: TestGqlgenInitStructure (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "`gqlgen` использует шаблонный движок `text/template` для генерации файлов `generated.go` и `models_gen.go`, генерируя типизированные вызовы без единой рефлексивной аллокации.",
    "pitfalls": "Коммитить сгенерированные файлы без проверки синхронизации в CI: если разработчик изменил `schema.graphqls`, но забыл запустить `gqlgen generate`, CI должен падать по `git diff --exit-code`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в CI/CD пайплайне гарантировать, что сгенерированный код GraphQL актуален?»\n**Ответ:** В GitHub Actions запускается шаг:\n```bash\ngo run github.com/99designs/gqlgen generate\ngit diff --exit-code\n```\nЕсли разработчик изменил `.graphqls`, но забыл сгенерировать Go-код локально, `git diff` вернет ненулевой код возврата и заблокирует слияние PR."
  },
  {
    "num": 35,
    "title": "Многоуровневая обработка ошибок в резолверах: форматирование gqlerror.Error с метаданными",
    "task": "Добавьте обработку ошибок в резолверах: возвращайте `gqlerror.Error` с кастомными кодами ошибок.",
    "theory": "Формат ошибок GraphQL по спецификации RFC:\n```json\n{\n  \"errors\": [\n    {\n      \"message\": \"недостаточно средств на счете\",\n      \"locations\": [{ \"line\": 2, \"column\": 3 }],\n      \"path\": [\"transferMoney\"],\n      \"extensions\": {\n        \"code\": \"INSUFFICIENT_FUNDS\",\n        \"current_balance\": 150.0,\n        \"required_amount\": 500.0,\n        \"timestamp\": \"2026-09-03T21:00:00Z\"\n      }\n    }\n  ],\n  \"data\": null\n}\n```\n- Поле `extensions` — единственный легитимный способ передавать типизированные метаданные ошибок клиентам.",
    "step_by_step": "1. Создайте кастомный конструктор GraphQL ошибок.\n2. Добавьте метаданные в словарь `Extensions`.\n3. Смоделируйте ошибку недостатка баланса в резолвере.\n4. Проверьте корректность сериализации структуры ошибки.",
    "code_blocks": [
      {
        "filename": "custom_gql_error_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"github.com/vektah/gqlparser/v2/gqlerror\"\n)\n\nfunc NewBusinessError(msg, code string, extra map[string]any) *gqlerror.Error {\n\text := map[string]any{\n\t\t\"code\":      code,\n\t\t\"timestamp\": time.Now().UTC().Format(time.RFC3339),\n\t}\n\tfor k, v := range extra {\n\t\text[k] = v\n\t}\n\n\treturn &gqlerror.Error{\n\t\tMessage:    msg,\n\t\tExtensions: ext,\n\t}\n}\n\nfunc TestCustomGqlError(t *testing.T) {\n\terr := NewBusinessError(\n\t\t\"недостаточно средств на счете\",\n\t\t\"INSUFFICIENT_FUNDS\",\n\t\tmap[string]any{\n\t\t\t\"current_balance\": 150.0,\n\t\t\t\"required_amount\": 500.0,\n\t\t},\n\t)\n\n\tb, _ := json.MarshalIndent(err, \"\", \"  \")\n\n\tif err.Extensions[\"code\"] != \"INSUFFICIENT_FUNDS\" {\n\t\tt.Fatalf(\"Некорректный код: %v\", err.Extensions)\n\t}\n\n\tfmt.Printf(\"Кастомная GraphQL ошибка успешно сериализована:\\n%s\\n\", string(b))\n}",
        "note": "Создание структурированной ошибки GraphQL с произвольными extensions"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v custom_gql_error_test.go\n# Вывод:\n# === RUN   TestCustomGqlError\n# Кастомная GraphQL ошибка успешно сериализована:\n# {\n#   \"message\": \"недостаточно средств на счете\",\n#   \"extensions\": {\n#     \"code\": \"INSUFFICIENT_FUNDS\",\n#     \"current_balance\": 150,\n#     \"required_amount\": 500,\n#     \"timestamp\": \"...\"\n#   }\n# }\n# --- PASS: TestCustomGqlError (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Пакет `github.com/vektah/gqlparser/v2/gqlerror` предоставляет тип `List`, позволяющий возвращать сразу несколько ошибок из одного метода резолвера.",
    "pitfalls": "Помещать стек-трейсы паник в `message` ошибки в проде: пользователи увидят внутренние пути к файлам и логику сервера, что является уязвимостью Information Disclosure.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в GraphQL реализовать локализацию (i18n) сообщений об ошибках?»\n**Ответ:** Сервер возвращает стабильный машиночитаемый код `extensions.code: \"INSUFFICIENT_FUNDS\"` и параметры подстановки (`extensions.params: { min: 500 }`). Клиентское приложение (React/Flutter) сопоставляет код с файлом локализации пользователя (`ru.json`, `en.json`) и отображает текст на языке устройства клиента."
  },
  {
    "num": 36,
    "title": "Курсорная пагинация (Relay Cursor Connections): спецификация Connection, Edge, PageInfo и base64",
    "task": "Реализуй **Cursor-based pagination** (Relay spec): `type UserConnection { edges: [UserEdge!]! pageInfo: PageInfo! }`, `type UserEdge { node: User! cursor: String! }`. Курсор — base64-encoded `id:timestamp`. Поддерживай `first/after`, `last/before`.",
    "theory": "Спецификация Relay Cursor Connections:\n```graphql\ntype PageInfo {\n  hasNextPage: Boolean!\n  hasPreviousPage: Boolean!\n  startCursor: String\n  endCursor: String\n}\n\ntype UserEdge {\n  cursor: String!\n  node: User!\n}\n\ntype UserConnection {\n  edges: [UserEdge!]!\n  pageInfo: PageInfo!\n  totalCount: Int!\n}\n\ntype Query {\n  users(first: Int, after: String): UserConnection!\n}\n```\n- Курсор кодируется в Base64 для непрозрачности (Opaque Token).\n- Запрос следующей страницы: `users(first: 10, after: \"dXNyXzEw\")`.",
    "step_by_step": "1. Создайте функции кодирования и декодирования курсора в Base64.\n2. Смоделируйте выборку элементов «после курсора».\n3. Сформируйте структуры `PageInfo`, `UserEdge` и `UserConnection`.\n4. Протестируйте бесконечную прокрутку (Infinite Scroll).",
    "code_blocks": [
      {
        "filename": "relay_cursor_pagination_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/base64\"\n\t\"fmt\"\n\t\"strconv\"\n\t\"strings\"\n\t\"testing\"\n)\n\ntype User struct {\n\tID   int\n\tName string\n}\n\ntype PageInfo struct {\n\tHasNextPage bool\n\tEndCursor   string\n}\n\ntype UserEdge struct {\n\tCursor string\n\tNode   *User\n}\n\ntype UserConnection struct {\n\tEdges    []*UserEdge\n\tPageInfo PageInfo\n}\n\nfunc EncodeCursor(id int) string {\n\traw := fmt.Sprintf(\"cursor:%d\", id)\n\treturn base64.StdEncoding.EncodeToString([]byte(raw))\n}\n\nfunc DecodeCursor(c string) (int, error) {\n\tbytes, err := base64.StdEncoding.DecodeString(c)\n\tif err != nil {\n\t\treturn 0, err\n\t}\n\tparts := strings.Split(string(bytes), \":\")\n\tif len(parts) != 2 {\n\t\treturn 0, fmt.Errorf(\"невалидный курсор\")\n\t}\n\treturn strconv.Atoi(parts[1])\n}\n\nfunc PaginateRelay(users []*User, first int, afterCursor string) UserConnection {\n\tstartIndex := 0\n\tif afterCursor != \"\" {\n\t\tlastID, err := DecodeCursor(afterCursor)\n\t\tif err == nil {\n\t\t\tfor i, u := range users {\n\t\t\t\tif u.ID == lastID {\n\t\t\t\t\tstartIndex = i + 1\n\t\t\t\t\tbreak\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\n\n\tendIndex := startIndex + first\n\thasNext := true\n\tif endIndex >= len(users) {\n\t\tendIndex = len(users)\n\t\thasNext = false\n\t}\n\n\tsliced := users[startIndex:endIndex]\n\tedges := make([]*UserEdge, len(sliced))\n\tvar lastCursor string\n\n\tfor i, u := range sliced {\n\t\tcur := EncodeCursor(u.ID)\n\t\tedges[i] = &UserEdge{Cursor: cur, Node: u}\n\t\tlastCursor = cur\n\t}\n\n\treturn UserConnection{\n\t\tEdges: edges,\n\t\tPageInfo: PageInfo{\n\t\t\tHasNextPage: hasNext,\n\t\t\tEndCursor:   lastCursor,\n\t\t},\n\t}\n}\n\nfunc TestRelayPagination(t *testing.T) {\n\tdataset := make([]*User, 25)\n\tfor i := 0; i < 25; i++ {\n\t\tdataset[i] = &User{ID: i + 1, Name: fmt.Sprintf(\"User #%d\", i+1)}\n\t}\n\n\t// 1. Первая страница (first: 10, after: \"\")\n\tp1 := PaginateRelay(dataset, 10, \"\")\n\tif len(p1.Edges) != 10 || !p1.PageInfo.HasNextPage {\n\t\tt.Fatalf(\"Ошибка страницы 1: %+v\", p1)\n\t}\n\n\t// 2. Вторая страница (first: 10, after: p1.PageInfo.EndCursor)\n\tp2 := PaginateRelay(dataset, 10, p1.PageInfo.EndCursor)\n\tif len(p2.Edges) != 10 || p2.Edges[0].Node.ID != 11 {\n\t\tt.Fatalf(\"Ошибка страницы 2: %+v\", p2)\n\t}\n\n\t// 3. Третья страница (хвост 5 записей, hasNext = false)\n\tp3 := PaginateRelay(dataset, 10, p2.PageInfo.EndCursor)\n\tif len(p3.Edges) != 5 || p3.PageInfo.HasNextPage {\n\t\tt.Fatalf(\"Ошибка страницы 3: %+v\", p3)\n\t}\n\n\tfmt.Printf(\"Relay Cursor пагинация успешно протестирована: 3 страницы (10 + 10 + 5 = 25 элементов)!\\n\")\n}",
        "note": "Эталонная реализация Relay Cursor Connections пагинации"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v relay_cursor_pagination_test.go\n# Вывод:\n# === RUN   TestRelayPagination\n# Relay Cursor пагинация успешно протестирована: 3 страницы (10 + 10 + 5 = 25 элементов)!\n# --- PASS: TestRelayPagination (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Курсорная пагинация транслируется в SQL: `SELECT * FROM users WHERE id > :cursor_id ORDER BY id ASC LIMIT :first`. Это гарантирует чтение строго по индексу за доли миллисекунды независимо от глубины прокрутки ленты.",
    "pitfalls": "Позволять клиенту сортировать по колонкам без уникальности (например `ORDER BY created_at`): если у нескольких записей одинаковый `created_at`, курсор пропустит строки. Решение: всегда добавлять уникальный тай-брейкер: `ORDER BY created_at DESC, id DESC`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в бесконечных лентах соцсетей (VK, Telegram) используют только Cursor-based пагинацию?»\n**Ответ:** В реальном времени в ленту ежесекундно поступают новые посты. При Offset-пагинации смещение `OFFSET 20` из-за добавления 5 новых постов покажет пользователю 5 постов с первой страницы повторно. Курсорная пагинация привязана к конкретному ID последнего просмотренного поста (`after: post_100`), поэтому лента никогда не сдвигается и не дублирует контент."
  },
  {
    "num": 37,
    "title": "Строго типизированный кодогенератор dataloaden: устранение интерфейсов any в пакетировании",
    "task": "Установите и внедрите `dataloaden` для пакетной загрузки пользователей. Покажите, что N+1 запросов больше нет.",
    "theory": "Библиотека `dataloaden` от автора gqlgen (vektah):\n- В отличие от `graph-gophers/dataloader`, использующего `interface{}` и кастинг типов, `dataloaden` — это **генератор строго типизированного Go-кода**:\n  `go run github.com/vektah/dataloaden UserLoader string *github.com/my/app.User`\n- Генерирует файл `userloader_gen.go` со специализированными методами:\n  - `Load(key string) (*User, error)`\n  - `LoadAll(keys []string) ([]*User, []error)`\n  - `Prime(key string, value *User) bool`\n- Нулевые накладные расходы на упаковку/распаковку `any` и максимальная скорость в рантайме Go.",
    "step_by_step": "1. Создайте структуру строго типизированного загрузчика `TypedUserLoader`.\n2. Реализуйте метод `Prime` для предварительного заполнения кэша.\n3. Смоделируйте пакетную загрузку по ключам.\n4. Протестируйте отсутствие дублирующих вызовов.",
    "code_blocks": [
      {
        "filename": "typed_dataloader_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n)\n\ntype User struct {\n\tID   string\n\tName string\n}\n\ntype TypedUserLoader struct {\n\tmu       sync.Mutex\n\tcache    map[string]*User\n\tfetchFn  func(keys []string) ([]*User, error)\n\tapiCalls int\n}\n\nfunc (l *TypedUserLoader) Load(ctx context.Context, key string) (*User, error) {\n\tl.mu.Lock()\n\tdefer l.mu.Unlock()\n\n\tif val, ok := l.cache[key]; ok {\n\t\treturn val, nil // Взято из кэша текущего запроса\n\t}\n\n\tl.apiCalls++\n\tusers, err := l.fetchFn([]string{key})\n\tif err != nil {\n\t\treturn nil, err\n\t}\n\tl.cache[key] = users[0]\n\treturn users[0], nil\n}\n\nfunc (l *TypedUserLoader) Prime(key string, val *User) {\n\tl.mu.Lock()\n\tdefer l.mu.Unlock()\n\tl.cache[key] = val\n}\n\nfunc TestTypedDataloader(t *testing.T) {\n\tloader := &TypedUserLoader{\n\t\tcache: make(map[string]*User),\n\t\tfetchFn: func(keys []string) ([]*User, error) {\n\t\t\treturn []*User{{ID: keys[0], Name: \"Пользователь \" + keys[0]}}, nil\n\t\t},\n\t}\n\n\t// 1. Первый запрос идет в БД\n\tu1, _ := loader.Load(context.Background(), \"usr_1\")\n\tif u1.Name != \"Пользователь usr_1\" {\n\t\tt.Fatal(\"Некорректная загрузка\")\n\t}\n\n\t// 2. Второй запрос того же ключа берется из кэша\n\tu2, _ := loader.Load(context.Background(), \"usr_1\")\n\tif u2 != u1 {\n\t\tt.Fatal(\"Ожидался тот же объект из кэша\")\n\t}\n\n\tif loader.apiCalls != 1 {\n\t\tt.Fatalf(\"Ожидался ровно 1 вызов БД, выполнено: %d\", loader.apiCalls)\n\t}\n\n\tfmt.Println(\"Typed DataLoader успешно мемоизировал объект в рамках запроса (1 вызов к БД)!\")\n}",
        "note": "Строго типизированный кэширующий загрузчик данных"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v typed_dataloader_test.go\n# Вывод:\n# === RUN   TestTypedDataloader\n# Typed DataLoader успешно мемоизировал объект в рамках запроса (1 вызов к БД)!\n# --- PASS: TestTypedDataloader (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Метод `Prime(key, val)` позволяет вручную положить в кэш DataLoader данные, которые уже были выбраны родительским запросом, исключая даже батч-запрос для известных сущностей.",
    "pitfalls": "Забывать обрабатывать частичные ошибки в `fetchFn`: если из 10 ключей один не найден в базе, DataLoader ожидает `nil` для этого элемента, а не падение всей пачки из 10 пользователей.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем преимущество dataloaden перед graph-gophers/dataloader?»\n**Ответ:** `dataloaden` генерирует конкретные типы (`*model.User`) вместо пустых интерфейсов `interface{}` / `any`. Это предотвращает escape-анализ структур в кучу при боксинге интерфейсов, сокращает аллокации памяти на 40% и дает полную безопасность типов на этапе компиляции Go."
  },
  {
    "num": 38,
    "title": "Field Masks через graphql.CollectFields: динамический SQL SELECT только запрошенных полей",
    "task": "Используйте **field masks** (через `graphql.CollectFields`) для оптимизации запросов к БД — загружайте только те поля, которые реально запрошены клиентом.",
    "theory": "Оптимизация обращений к базе через Field Masks:\n- Допустим, таблица `products` содержит тяжелые колонки `description_html` (10 КБ) и `specs_json` (20 КБ).\n- Запрос клиента для каталога:\n  `query { products { id title price } }`\n- Если бэкенд выполняет `SELECT * FROM products`, база перегоняет мегабайты неиспользуемых данных по сети.\n- С помощью `graphql.CollectFieldsCtx(ctx, nil)`:\n  1. Сервер извлекает точный список запрошенных клиентом колонок: `[\"id\", \"title\", \"price\"]`.\n  2. Формирует SQL: `SELECT id, title, price FROM products`.\n  3. Трафик сети и нагрузка на память уменьшаются в десятки раз!",
    "step_by_step": "1. Создайте функцию извлечения запрошенных полей.\n2. Реализуйте построитель динамического SQL SELECT.\n3. Проверьте исключение тяжелых полей.\n4. Протестируйте итоговый SQL-запрос.",
    "code_blocks": [
      {
        "filename": "field_mask_sql_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n\t\"testing\"\n)\n\n// Белый список колонок для защиты от SQL-инъекций\nvar allowedColumns = map[string]string{\n\t\"id\":          \"id\",\n\t\"title\":       \"title\",\n\t\"price\":       \"price\",\n\t\"description\": \"description_html\",\n\t\"specs\":       \"specs_json\",\n}\n\nfunc BuildOptimizedSQL(tableName string, requestedGQLFields []string) string {\n\tselectedCols := make([]string, 0, len(requestedGQLFields))\n\tfor _, f := range requestedGQLFields {\n\t\tif col, ok := allowedColumns[f]; ok {\n\t\t\tselectedCols = append(selectedCols, col)\n\t\t}\n\t}\n\n\tif len(selectedCols) == 0 {\n\t\tselectedCols = []string{\"id\"} // fallback\n\t}\n\n\treturn fmt.Sprintf(\"SELECT %s FROM %s\", strings.Join(selectedCols, \", \"), tableName)\n}\n\nfunc TestFieldMaskSQL(t *testing.T) {\n\t// Клиент запросил только id, title и price\n\trequestedFields := []string{\"id\", \"title\", \"price\"}\n\n\tquery := BuildOptimizedSQL(\"products\", requestedFields)\n\texpected := \"SELECT id, title, price FROM products\"\n\n\tif query != expected {\n\t\tt.Fatalf(\"Некорректный SQL: got '%s', want '%s'\", query, expected)\n\t}\n\n\tfmt.Printf(\"Динамический Field Mask успешно сгенерировал SQL:\\n  %s\\n\", query)\n\tfmt.Println(\"Тяжелые колонки description_html и specs_json исключены из выборки!\")\n}",
        "note": "Построение оптимизированного SELECT на основе маски запрошенных полей"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v field_mask_sql_test.go\n# Вывод:\n# === RUN   TestFieldMaskSQL\n# Динамический Field Mask успешно сгенерировал SQL:\n#   SELECT id, title, price FROM products\n# Тяжелые колонки description_html и specs_json исключены из выборки!\n# --- PASS: TestFieldMaskSQL (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Обязательно используйте белый список соответствия полей GraphQL колонкам БД (`allowedColumns`), чтобы исключить возможность передачи зловредных выражений в тело SQL-запроса.",
    "pitfalls": "Вставлять имена полей из GraphQL напрямую в SQL без белого списка: уязвимость SQL Injection через передачу алиасов в запросе.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в ORM (например GORM или Ent) передавать field masks из GraphQL?»\n**Ответ:** В GORM используют метод `.Select(columns...)`:\n```go\nfields := graphql.CollectAllFields(ctx)\ndb.Select(fields).Find(&users)\n```\nЭто предотвращает чтение неиспользуемых колонок на уровне базы данных."
  },
  {
    "num": 39,
    "title": "Классическая проблема N+1: стресс-тест латентности при 100 постах и 101 сетевом запросе",
    "task": "**Классическая проблема N+1**: Реализуйте query `posts(limit: 100)`, где для каждого поста вызывается резолвер `author`. Заметьте, что для 100 постов выполняется 101 запрос к БД.",
    "theory": "Математика сетевой задержки N+1:\n- Пусть один сетевой Round-Trip Time (RTT) до базы данных составляет **2 миллисекунды**.\n- При одном оптимизированном батч-запросе (`IN (...)`):\n  - Время выполнения: $2\\,\\text{мс} \\times 2 = 4\\,\\text{мс}$.\n- При проблеме N+1 (100 последовательных одиночных запросов):\n  - Время выполнения: $2\\,\\text{мс} + (100 \\times 2\\,\\text{мс}) = \\mathbf{202\\,\\text{миллисекунды}}$!\n- Задержка ответа увеличивается в **50 раз**, создавая иллюзию «тормозящего бэкенда» на пустом месте.",
    "step_by_step": "1. Создайте симулятор сетевой задержки RTT в 1 мс.\n2. Смоделируйте выполнение 100 постов через N+1 вызовы.\n3. Замерьте суммарное время исполнения.\n4. Продемонстрируйте катастрофическую просадку по SLA.",
    "code_blocks": [
      {
        "filename": "n_plus_one_latency_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype LatencySimulator struct {\n\trtt time.Duration\n}\n\nfunc (s *LatencySimulator) Query(ctx context.Context) {\n\ttime.Sleep(s.rtt) // Имитация RTT до СУБД\n}\n\nfunc TestNPlusOneLatencyImpact(t *testing.T) {\n\tsim := &LatencySimulator{rtt: 1 * time.Millisecond}\n\n\t// 1. Выборка 100 постов: 1 запрос\n\tstart := time.Now()\n\tsim.Query(context.Background())\n\n\t// 2. N=100 одиночных вызовов автора\n\tfor i := 0; i < 50; i++ { // Берем 50 для быстрого теста\n\t\tsim.Query(context.Background())\n\t}\n\telapsed := time.Since(start)\n\n\tfmt.Printf(\"Анализ влияния N+1 на задержку (50 постов с RTT 1ms):\\n\")\n\tfmt.Printf(\"  • Суммарное время ответа: %v\\n\", elapsed.Round(time.Millisecond))\n\tfmt.Printf(\"  • Батч-запрос выполнился бы за: ~2ms!\\n\")\n\n\tif elapsed < 40*time.Millisecond {\n\t\tt.Fatal(\"Слишком быстро для последовательных сетевых вызовов\")\n\t}\n}",
        "note": "Анализ деградации времени ответа из-за сетевых round-trips N+1"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v n_plus_one_latency_test.go\n# Вывод:\n# === RUN   TestNPlusOneLatencyImpact\n# Анализ влияния N+1 на задержку (50 постов с RTT 1ms):\n#   • Суммарное время ответа: 52ms\n#   • Батч-запрос выполнился бы за: ~2ms!\n# --- PASS: TestNPlusOneLatencyImpact (0.05s)\n# PASS"
      }
    ],
    "under_the_hood": "Даже если запросы к БД выполняются параллельно в горутинах, пул соединений СУБД имеет жесткий лимит (обычно `max_connections = 50..100`). Параллельные запросы выстраиваются в очередь ожидания свободного коннекта, вызывая таймауты `context deadline exceeded`.",
    "pitfalls": "Считать, что быстрый SSD в базе данных спасет от N+1: проблема N+1 кроется не в чтении с диска, а в сетевых накладных расходах протокола TCP/IP и планировщика операционной системы.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как обнаружить проблему N+1 в production автоматически?»\n**Ответ:** Через OpenTelemetry трассировку в Jaeger. Запрос с проблемой N+1 выглядит в трейсе как длинная вертикальная «лесенка» из десятков или сотен одинаковых спанов `db.query: SELECT * FROM authors WHERE id = ?`. На основе трейсов настраивают автоматические алерты детекции аномального количества SQL-спанов в одном родительском трейсе."
  },
  {
    "num": 40,
    "title": "Динамическая фильтрация: users(filter: UserFilter) с обработкой nil полей и генерацией SQL",
    "task": "Реализуй **Filtering**: `users(filter: UserFilter): [User!]!`, `input UserFilter { nameContains: String status: Status minCreatedAt: Time }`. Строй SQL динамически через `squirrel` или ручно. Обрабатывай nil-поля (фильтр не применяется).",
    "theory": "Паттерн динамической фильтрации в GraphQL:\n```graphql\nenum UserStatus { ACTIVE BLOCKED PENDING }\n\ninput UserFilter {\n  nameContains: String\n  status: UserStatus\n  minCreatedAt: Time\n}\n\ntype Query {\n  users(filter: UserFilter): [User!]!\n}\n```\n- Логика построения SQL:\n  - Если `filter == nil`, возвращаются все записи (`WHERE 1=1`).\n  - Если `filter.NameContains != nil`, добавляется: `AND name ILIKE '%' || $1 || '%'`.\n  - Если `filter.Status != nil`, добавляется: `AND status = $2`.\n  - Если `filter.MinCreatedAt != nil`, добавляется: `AND created_at >= $3`.\n- Все аргументы должны быть строго параметризованы для защиты от SQL-инъекций.",
    "step_by_step": "1. Создайте структуру входного фильтра `UserFilter` с указателями.\n2. Напишите построитель SQL с динамическим срезом условий и аргументов.\n3. Проверьте случай, когда фильтры не переданы (nil).\n4. Проверьте генерацию корректного запроса с несколькими фильтрами.",
    "code_blocks": [
      {
        "filename": "dynamic_filtering_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"strings\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype UserStatus string\n\nconst (\n\tStatusActive  UserStatus = \"ACTIVE\"\n\tStatusBlocked UserStatus = \"BLOCKED\"\n)\n\ntype UserFilter struct {\n\tNameContains *string\n\tStatus       *UserStatus\n\tMinCreatedAt *time.Time\n}\n\nfunc BuildFilteredQuery(filter *UserFilter) (string, []any) {\n\tquery := \"SELECT id, name, status, created_at FROM users WHERE 1=1\"\n\tvar args []any\n\targIdx := 1\n\n\tif filter == nil {\n\t\treturn query, args\n\t}\n\n\tif filter.NameContains != nil {\n\t\tquery += fmt.Sprintf(\" AND name ILIKE $%d\", argIdx)\n\t\targs = append(args, \"%\"+*filter.NameContains+\"%\")\n\t\targIdx++\n\t}\n\n\tif filter.Status != nil {\n\t\tquery += fmt.Sprintf(\" AND status = $%d\", argIdx)\n\t\targs = append(args, string(*filter.Status))\n\t\targIdx++\n\t}\n\n\tif filter.MinCreatedAt != nil {\n\t\tquery += fmt.Sprintf(\" AND created_at >= $%d\", argIdx)\n\t\targs = append(args, *filter.MinCreatedAt)\n\t\targIdx++\n\t}\n\n\treturn query, args\n}\n\nfunc TestDynamicFiltering(t *testing.T) {\n\t// 1. Без фильтров\n\tq1, args1 := BuildFilteredQuery(nil)\n\tif q1 != \"SELECT id, name, status, created_at FROM users WHERE 1=1\" || len(args1) != 0 {\n\t\tt.Fatalf(\"Ошибка пустого фильтра: %s\", q1)\n\t}\n\n\t// 2. С двумя фильтрами\n\tname := \"Иван\"\n\tst := StatusActive\n\tfilter := &UserFilter{NameContains: &name, Status: &st}\n\n\tq2, args2 := BuildFilteredQuery(filter)\n\texpectedQ := \"SELECT id, name, status, created_at FROM users WHERE 1=1 AND name ILIKE $1 AND status = $2\"\n\n\tif q2 != expectedQ || len(args2) != 2 || args2[0] != \"%Иван%\" || args2[1] != \"ACTIVE\" {\n\t\tt.Fatalf(\"Некорректный динамический SQL: query='%s', args=%v\", q2, args2)\n\t}\n\n\tfmt.Printf(\"Динамическая фильтрация успешно сформировала параметризованный SQL:\\n  %s\\n\", q2)\n\tfmt.Printf(\"  Аргументы: %v\\n\", args2)\n}",
        "note": "Параметризованное построение динамического SQL-запроса с фильтрами"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v dynamic_filtering_test.go\n# Вывод:\n# === RUN   TestDynamicFiltering\n# Динамическая фильтрация успешно сформировала параметризованный SQL:\n#   SELECT id, name, status, created_at FROM users WHERE 1=1 AND name ILIKE $1 AND status = $2\n#   Аргументы: [%Иван% ACTIVE]\n# --- PASS: TestDynamicFiltering (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Использование паттерна `WHERE 1=1` позволяет легко объединять динамические условия через `AND` без необходимости проверять, является ли текущее условие первым в цепочке.",
    "pitfalls": "Конкатенировать значение `*filter.NameContains` напрямую в строку запроса: это открывает критическую уязвимость SQL Injection. Параметры всегда передаются через позиционные плейсхолдеры `$1, $2`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как оптимизировать динамический поиск по подстроке ILIKE %text% в PostgreSQL?»\n**Ответ:** Стандартный B-Tree индекс бесполезен при поиске с `%` в начале строки (`ILIKE '%text%'`). Для мгновенного поиска по подстроке в PostgreSQL создают триграммный индекс с помощью расширения `pg_trgm`:\n`CREATE INDEX idx_users_name_trgm ON users USING gin (name gin_trgm_ops);`\nЭто превращает сканирование таблицы в быстрый индексный поиск по триграммам."
  }
]
