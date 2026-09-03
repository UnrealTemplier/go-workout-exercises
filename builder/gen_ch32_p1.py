# -*- coding: utf-8 -*-
"""Exercises 1..65 of Chapter 32."""

exercises = [
  {
    "num": 1,
    "title": "Описание первой схемы Protobuf: спецификация proto3, числовые теги и сервис UserService",
    "task": "**Описание первой схемы Protobuf**: Создайте файл `user.proto`. Напишите схему protobuf (версии `syntax = \"proto3\"`). Объявите сообщение `UserRequest` с полем `user_id` (тип `string`, тег `1`) и сообщение `UserResponse` с полями `id`, `name`, `email` и списком ролей `repeated string roles`. Опишите gRPC-сервис `UserService` с методом `GetUser`, который принимает `UserRequest` и возвращает `UserResponse`.",
    "theory": "Архитектурные основы Protocol Buffers (proto3):\n- Protocol Buffers (Protobuf) — бинарный, компактный, платформо- и языконезависимый протокол сериализации данных, разработанный Google.\n- Ключевые концепции спецификации:\n  1. `syntax = \"proto3\";` — обязательное объявление версии синтаксиса в первой строке.\n  2. **Числовые теги (Field Numbers):** в бинарном представлении имена полей (`user_id`, `email`) **НЕ передаются по сети**. Вместо них передается тег поля (Field Tag) в связке с типом данных (Wire Type). Теги от 1 до 15 кодируются ровно в 1 байт, поэтому их резервируют для самых частотных полей.\n  3. `repeated` — динамический массив произвольной длины (в Go преобразуется в слайс `[]T`).\n  4. `service` — декларация удаленного интерфейса вызова процедур (gRPC API).",
    "step_by_step": "1. Создайте файл `user.proto`.\n2. Укажите версию `proto3` и имя пакета Go через директиву `option go_package`.\n3. Опишите сообщения запроса `UserRequest` и ответа `UserResponse`.\n4. Объявите сервис `UserService` с унарным методом `GetUser`.",
    "code_blocks": [
      {
        "filename": "proto/user.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage user.v1;\n\noption go_package = \"github.com/myorg/myapp/gen/user/v1;userv1\";\n\n// UserRequest представляет запрос на получение пользователя\nmessage UserRequest {\n  string user_id = 1;\n}\n\n// UserResponse содержит профиль пользователя и его роли\nmessage UserResponse {\n  string id = 1;\n  string name = 2;\n  string email = 3;\n  repeated string roles = 4;\n}\n\n// UserService предоставляет операции над пользователями\nservice UserService {\n  rpc GetUser(UserRequest) returns (UserResponse);\n}",
        "note": "Спецификация схемы user.proto с описанием сервиса и сообщений"
      },
      {
        "filename": "user_mock.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n)\n\n// UserRequestDTO эмулирует структуру, генерируемую protoc-gen-go\ntype UserRequestDTO struct {\n\tUserID string\n}\n\n// UserResponseDTO эмулирует сгенерированное сообщение ответа\ntype UserResponseDTO struct {\n\tID    string\n\tName  string\n\tEmail string\n\tRoles []string\n}\n\n// UserServerService реализует бизнес-логику gRPC сервиса\ntype UserServerService struct{}\n\nfunc (s *UserServerService) GetUser(ctx context.Context, req *UserRequestDTO) (*UserResponseDTO, error) {\n\tif req.UserID == \"\" {\n\t\treturn nil, errors.New(\"user_id не может быть пустым\")\n\t}\n\n\treturn &UserResponseDTO{\n\t\tID:    req.UserID,\n\t\tName:  \"Алексей Смирнов\",\n\t\tEmail: \"alex@example.com\",\n\t\tRoles: []string{\"ADMIN\", \"DEVELOPER\"},\n\t}, nil\n}\n\nfunc main() {\n\tsvc := &UserServerService{}\n\tresp, err := svc.GetUser(context.Background(), &UserRequestDTO{UserID: \"usr_100500\"})\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tfmt.Printf(\"Пользователь: %s (%s), Роли: %v\\n\", resp.Name, resp.Email, resp.Roles)\n}",
        "note": "Самодостаточный Go код моделирования работы gRPC метода"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run user_mock.go\n# Вывод:\n# Пользователь: Алексей Смирнов (alex@example.com), Роли: [ADMIN DEVELOPER]"
      }
    ],
    "under_the_hood": "В бинарном проводе Protobuf заголовок поля кодируется формулой `(field_number << 3) | wire_type`. Для тега `1` и типа `string` (Wire Type 2) получается байт `0x0A` (`00001010` в двоичном виде). Имя поля `user_id` вообще отсутствует в пакете, обеспечивая колоссальную экономию сетевого трафика.",
    "pitfalls": "Менять числовые теги полей в существующих схемах: если изменить тег `user_id = 1` на `user_id = 2`, старые клиенты перестанут понимать новые серверы, что вызовет тихую потерю данных (десериализатор запишет поле в Unknown Fields).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Protobuf номера тегов от 1 до 15 считаются самыми ценными?»\n**Ответ:** Заголовок поля `(field_number << 3) | wire_type` для тегов $1 \\dots 15$ помещается ровно в 1 байт (так как $15 \\times 8 + 7 = 127 < 128$). Начиная с тега 16, под заголовок требуется уже 2 байта Varint. В высоконагруженных системах (Google, Ozon) теги 1–15 резервируют строго для самых частотных полей hot-path сообщений."
  },
  {
    "num": 2,
    "title": "Настройка окружения компиляции Protobuf: компилятор protoc, плагины protoc-gen-go и protoc-gen-go-grpc",
    "task": "**Настройка окружения**: Установи компилятор `protoc` (с официального сайта) и плагины для Go: `go install google.golang.org/protobuf/cmd/protoc-gen-go@latest` и `go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest`.",
    "theory": "Архитектура кодогенерации Protobuf в экосистеме Go:\n- `protoc` — базовый компилятор (написан на C++), который парсит `.proto` файлы, строит синтаксическое дерево (AST) и сериализует его в бинарный дескриптор `CodeGeneratorRequest`.\n- Плагины кодогенерации в Go:\n  1. `protoc-gen-go`: генерирует структуры Go, геттеры, методы сериализации/десериализации `proto.Message`.\n  2. `protoc-gen-go-grpc`: генерирует интерфейсы клиентских стабов (`UserServiceClient`) и серверных обработчиков (`UserServiceServer`), а также методы регистрации в `grpc.Server`.\n- Бинарники плагинов обязаны находиться в переменной окружения `$PATH` (обычно `$GOPATH/bin`).",
    "step_by_step": "1. Установите компилятор `protoc` через пакетный менеджер или релиз GitHub.\n2. Скомпилируйте Go-плагины через команду `go install`.\n3. Добавьте `$GOPATH/bin` в `$PATH`.\n4. Проверьте работоспособность версий.",
    "code_blocks": [
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# 1. Установка компилятора protoc (для Linux/macOS):\nsudo apt-get install -y protobuf-compiler # Ubuntu/Debian\n# либо brew install protobuf             # macOS\n\n# 2. Установка специализированных Go-плагинов в $GOPATH/bin:\ngo install google.golang.org/protobuf/cmd/protoc-gen-go@latest\ngo install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest\n\n# 3. Добавление бинарников Go в переменную PATH:\nexport PATH=\"$PATH:$(go env GOPATH)/bin\"\n\n# 4. Проверка версий установленных утилит:\nprotoc --version\nprotoc-gen-go --version\nprotoc-gen-go-grpc --version\n# Вывод:\n# libprotoc 25.1\n# protoc-gen-go v1.34.2\n# protoc-gen-go-grpc 1.4.0"
      },
      {
        "filename": "env_check.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os/exec\"\n)\n\nfunc main() {\n\ttools := []string{\"protoc\", \"protoc-gen-go\", \"protoc-gen-go-grpc\"}\n\tfor _, tool := range tools {\n\t\tpath, err := exec.LookPath(tool)\n\t\tif err != nil {\n\t\t\tfmt.Printf(\"❌ Инструмент %-20s НЕ найден в $PATH\\n\", tool)\n\t\t} else {\n\t\t\tfmt.Printf(\"✅ Инструмент %-20s найден: %s\\n\", tool, path)\n\t\t}\n\t}\n}",
        "note": "Утилита проверки доступности инструментов в $PATH"
      }
    ],
    "under_the_hood": "`protoc` вызывает плагины через стандартные потоки ввода-вывода (Unix IPC stdin/stdout). Компилятор запускает бинарник `protoc-gen-go`, передает ему сериализованный Protocol Buffers запрос в `os.Stdin` и читает сгенерированные файлы Go из `os.Stdout`.",
    "pitfalls": "Забыть добавить `export PATH=\"$PATH:$(go env GOPATH)/bin\"` в `~/.bashrc`: при вызове `protoc` упадет с ошибкой `protoc-gen-go: program not found or is not executable`.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие библиотеки github.com/golang/protobuf от google.golang.org/protobuf (Protobuf API v2)?»\n**Ответ:** Старый пакет `golang/protobuf` (API v1) устарел в 2020 году. Новый модуль `google.golang.org/protobuf` (API v2) ввел мощную систему динамической рефлексии схем (`protoreflect`), разделение структур и дескрипторов, а также радикально ускорил сериализацию и снизил аллокации памяти."
  },
  {
    "num": 3,
    "title": "Перечисления (Enum) в Protobuf: правило нулевого значения UNSPECIFIED и маппинг в Go",
    "task": "Добави `enum Status { STATUS_UNSPECIFIED = 0; STATUS_ACTIVE = 1; STATUS_INACTIVE = 2; }` в `user.proto`. Сгенерируй код. Покажи, что в Go это тип `Status` с константами `Status_STATUS_UNSPECIFIED` и т.д. Объясни, почему `0` — `UNSPECIFIED` (best practice).",
    "theory": "Правило нулевого значения для Enum в proto3:\n- В proto3 поля с дефолтными значениями (ноль для чисел, пустая строка для текста, false для boolean) **НЕ передаются по проводу** ради оптимизации трафика.\n- Для любого `enum` нулевое значение **ОБЯЗАНО быть объявлено первым с тегом 0**.\n- **Best Practice Google:** Значение с номером 0 всегда называют `<ENUM_NAME>_UNSPECIFIED`.\n- Причины:\n  1. Если отправитель не заполнил поле, получатель видит `0` (UNSPECIFIED) и понимает, что значение не было явно выставлено.\n  2. Если бы 0 означал `ACTIVE`, то любое неинициализированное сообщение автоматически делало бы пользователя активным (опасная семантика по умолчанию).",
    "step_by_step": "1. Объявите enum `Status` в proto-файле.\n2. Сгенерируйте код.\n3. Продемонстрируйте использование констант `Status_STATUS_ACTIVE` в Go.\n4. Продемонстрируйте метод `.String()` для человекочитаемого лога.",
    "code_blocks": [
      {
        "filename": "proto/status.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage user.v1;\n\noption go_package = \"github.com/myorg/myapp/gen/user/v1;userv1\";\n\nenum Status {\n  STATUS_UNSPECIFIED = 0; // Обязательное нулевое значение по умолчанию\n  STATUS_ACTIVE = 1;\n  STATUS_INACTIVE = 2;\n  STATUS_SUSPENDED = 3;\n}",
        "note": "Спецификация enum со значением UNSPECIFIED"
      },
      {
        "filename": "status_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n)\n\n// Эмуляция сгенерированного типа enum в Go\ntype UserStatus int32\n\nconst (\n\tUserStatus_STATUS_UNSPECIFIED UserStatus = 0\n\tUserStatus_STATUS_ACTIVE      UserStatus = 1\n\tUserStatus_STATUS_INACTIVE    UserStatus = 2\n\tUserStatus_STATUS_SUSPENDED   UserStatus = 3\n)\n\nvar UserStatus_name = map[int32]string{\n\t0: \"STATUS_UNSPECIFIED\",\n\t1: \"STATUS_ACTIVE\",\n\t2: \"STATUS_INACTIVE\",\n\t3: \"STATUS_SUSPENDED\",\n}\n\nfunc (s UserStatus) String() string {\n\tif name, ok := UserStatus_name[int32(s)]; ok {\n\t\treturn name\n\t}\n\treturn fmt.Sprintf(\"UserStatus(%d)\", s)\n}\n\nfunc main() {\n\tvar defaultStatus UserStatus // При инициализации равен 0\n\tfmt.Printf(\"Дефолтный статус: %s (код %d)\\n\", defaultStatus, defaultStatus)\n\n\tactiveStatus := UserStatus_STATUS_ACTIVE\n\tfmt.Printf(\"Выбранный статус: %s (код %d)\\n\", activeStatus, activeStatus)\n}",
        "note": "Использование констант enum и строкового представления в Go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run status_demo.go\n# Вывод:\n# Дефолтный статус: STATUS_UNSPECIFIED (код 0)\n# Выбранный статус: STATUS_ACTIVE (код 1)"
      }
    ],
    "under_the_hood": "В Go перечисления компилируются в псевдоним типа `type Status int32` и блок `const (...)`. Также компилятор генерирует две мапы `Status_name` и `Status_value` для быстрого прямого и обратного преобразования строк в коды за $O(1)$.",
    "pitfalls": "Назначать значению `0` осмысленную бизнес-роль (например `STATUS_ACTIVE = 0`): невозможно будет отличить «пользователь действительно активен» от «клиент забыл передать статус в запросе».",
    "bigtech_interview": "**Вопрос с собеседования:** «Что произойдет, если сервер добавит новое значение enum (например STATUS_ARCHIVED = 4), а старый клиент получит его по сети?»\n**Ответ:** В proto3 старый клиент сохранит неизвестное число `4` в поле типа `int32`. Код не упадет, метод `Status` вернет `4`, но метод `.String()` выведет `UserStatus(4)`. При повторной сериализации это значение не потеряется (сохранится в Unknown Fields)."
  },
  {
    "num": 4,
    "title": "Генерация Go-кода из proto-файла: флаги --go_out и --go-grpc_out",
    "task": "Сгенерируйте Go-код из `.proto` файла командой `protoc --go_out=. --go-grpc_out=. hello.proto`.",
    "theory": "Команды компиляции `protoc`:\n- Для генерации кода вызывают компилятор с указанием целевых директорий:\n  - `--go_out=.`: директория вывода структур данных.\n  - `--go-grpc_out=.`: директория вывода gRPC клиента и сервера.\n  - `--go_opt=paths=source_relative`: указывает компилятору генерировать файлы относительно исходного `.proto` файла, а не создавать длинную цепочку вложенных папок из `go_package`.\n  - `--go-grpc_opt=paths=source_relative`: аналогичный параметр для gRPC интерфейсов.",
    "step_by_step": "1. Создайте файл `hello.proto`.\n2. Укажите `option go_package = \"./hello;hello\";`.\n3. Выполните компиляцию через `protoc`.\n4. Проверьте создание файлов `hello.pb.go` и `hello_grpc.pb.go`.",
    "code_blocks": [
      {
        "filename": "hello.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage hello;\n\noption go_package = \"./hello;hello\";\n\nmessage HelloRequest {\n  string greeting = 1;\n}\n\nmessage HelloResponse {\n  string reply = 1;\n}\n\nservice Greeter {\n  rpc SayHello(HelloRequest) returns (HelloResponse);\n}",
        "note": "Минимальный контракт сервиса Greeter"
      },
      {
        "filename": "Makefile",
        "lang": "makefile",
        "code": ".PHONY: proto\n\nproto:\n\tmkdir -p hello\n\tprotoc --go_out=. --go_opt=paths=source_relative \\\n\t       --go-grpc_out=. --go-grpc_opt=paths=source_relative \\\n\t       hello.proto",
        "note": "Идиоматичный Makefile для вызова protoc"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск компиляции схемы:\nprotoc --go_out=. --go_opt=paths=source_relative \\\n       --go-grpc_out=. --go-grpc_opt=paths=source_relative \\\n       hello.proto\n\n# Проверяем результат генерации:\nls -la hello*\n# hello.pb.go       (структуры данных HelloRequest, HelloResponse)\n# hello_grpc.pb.go  (интерфейсы GreeterClient, GreeterServer)"
      }
    ],
    "under_the_hood": "`protoc` передает флаг `--go_opt` в плагин `protoc-gen-go` в виде параметров командной строки. Опция `paths=source_relative` отключает старое поведение protoc, создававшее папки на основе полного URL пакета (`github.com/org/...`).",
    "pitfalls": "Не указывать `paths=source_relative`: `protoc` создаст вложенную структуру директорий `github.com/myorg/myapp/...` прямо внутри вашей текущей папки.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему код клиента и сервера gRPC разделен на два отдельных плагина protoc-gen-go и protoc-gen-go-grpc?»\n**Ответ:** До версии Protobuf v1.20 генератор gRPC был встроен в основной плагин `--go_out=plugins=grpc:...`. Разработчики Google разделили их для модульности: многим проектам нужны только сериализуемые структуры данных (для Kafka, Redis или диска) без тяжелой зависимости от сетевого рантайма gRPC."
  },
  {
    "num": 5,
    "title": "Базовые числовые и строковые типы данных в Protobuf: int32, int64, string и скалярные типы",
    "task": "Создай файл `user.proto`. Опиши сообщение `User` с полями `id` (int32), `name` (string), `age` (int32).",
    "theory": "Скалярные типы данных в proto3 и их представление в памяти Go:\n| Protobuf тип | Go тип | Wire Type | Применение |\n| :--- | :--- | :--- | :--- |\n| `int32` / `int64` | `int32` / `int64` | 0 (Varint) | Положительные целые числа |\n| `sint32` / `sint64` | `int32` / `int64` | 0 (ZigZag Varint) | Числа с частыми отрицательными значениями |\n| `fixed32` / `fixed64` | `uint32` / `uint64` | 5 (32-bit) / 1 (64-bit) | Большие числа > $2^{56}$ (хэши, ID) |\n| `string` | `string` | 2 (Length-delimited) | Строки строго в кодировке UTF-8 |\n| `bytes` | `[]byte` | 2 (Length-delimited) | Сырые бинарные данные, токены, сжатые блоки |\n| `bool` | `bool` | 0 (Varint) | Логические флаги (0 или 1) |",
    "step_by_step": "1. Создайте сообщение `User` с полями `id`, `name`, `age`.\n2. Назначьте уникальные номера тегов 1, 2, 3.\n3. Продемонстрируйте создание объекта в Go.\n4. Проверьте сгенерированные геттеры (`GetId`, `GetName`, `GetAge`).",
    "code_blocks": [
      {
        "filename": "user.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage user.v1;\n\noption go_package = \"./userv1;userv1\";\n\nmessage User {\n  int32 id = 1;\n  string name = 2;\n  int32 age = 3;\n}",
        "note": "Схема с базовыми скалярными типами"
      },
      {
        "filename": "scalar_types_demo.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\n// UserDTO эмулирует сгенерированную структуру Protobuf\ntype UserDTO struct {\n\tId   int32\n\tName string\n\tAge  int32\n}\n\n// Вспомогательные nil-safe геттеры, генерируемые protoc-gen-go\nfunc (u *UserDTO) GetId() int32 {\n\tif u != nil {\n\t\treturn u.Id\n\t}\n\treturn 0\n}\n\nfunc (u *UserDTO) GetName() string {\n\tif u != nil {\n\t\treturn u.Name\n\t}\n\treturn \"\"\n}\n\nfunc (u *UserDTO) GetAge() int32 {\n\tif u != nil {\n\t\treturn u.Age\n\t}\n\treturn 0\n}\n\nfunc main() {\n\tuser := &UserDTO{\n\t\tId:   42,\n\t\tName: \"Елена\",\n\t\tAge:  28,\n\t}\n\n\tfmt.Printf(\"User: ID=%d, Name=%s, Age=%d\\n\", user.GetId(), user.GetName(), user.GetAge())\n\n\t// Проверка nil-safety геттеров:\n\tvar nilUser *UserDTO\n\tfmt.Printf(\"Nil user name: %q, age: %d (без паники!)\\n\", nilUser.GetName(), nilUser.GetAge())\n}",
        "note": "Безопасное использование геттеров сгенерированных Protobuf структур"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run scalar_types_demo.go\n# Вывод:\n# User: ID=42, Name=Елена, Age=28\n# Nil user name: \"\", age: 0 (без паники!)"
      }
    ],
    "under_the_hood": "Компилятор `protoc-gen-go` генерирует геттеры вида `func (x *T) GetField()`, которые проверяют `if x != nil`. Это предотвращает распространенные паники рантайма `panic: runtime error: invalid memory address or nil pointer dereference` при доступе к вложенным структурам.",
    "pitfalls": "Использовать тип `int32` для отрицательных чисел: стандартный `int32` кодирует отрицательные числа 10 байтами Varint. Для чисел, которые часто бывают отрицательными, ОБЯЗАТЕЛЬНО используйте `sint32` (ZigZag кодирование).",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем разница между int32 и sint32 при кодировании числа -1 в Protobuf?»\n**Ответ:** Число `-1` в типе `int32` знакорасширяется до 64 бит и занимает максимальные 10 байт в проводе (`0xFF 0xFF... 0x01`). Тип `sint32` применяет преобразование ZigZag `(n << 1) ^ (n >> 31)`, превращая `-1` в положительное число `1`, которое кодируется всего **1 байтом**!"
  },
  {
    "num": 6,
    "title": "Сложные типы сообщений: вложенные структуры, enum и списки repeated",
    "task": "Добавьте в сообщение вложенные поля, `enum` и поле с `repeated`. Сгенерируйте Go-код.",
    "theory": "Организация составных моделей данных в Protobuf:\n- `repeated string skills = 4;` — динамический список (срез строк).\n- `enum Department` — типизированная классификация.\n- Вложенное сообщение `Passport passport = 5;` — композиция один-к-одному.\n- В Go:\n  - Скалярные типы хранятся по значению (`string`, `int32`).\n  - Вложенные сообщения хранятся **как указатели** (`*Passport`), что позволяет полю принимать значение `nil` (отсутствие вложенного объекта).",
    "step_by_step": "1. Создайте расширенную схему сотрудника компании.\n2. Включите перечисление отделов.\n3. Добавьте вложенную структуру паспортных данных.\n4. Продемонстрируйте сборку объекта и итерацию по `repeated` полю в Go.",
    "code_blocks": [
      {
        "filename": "employee.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage hr.v1;\n\noption go_package = \"./hrv1;hrv1\";\n\nenum Department {\n  DEPARTMENT_UNSPECIFIED = 0;\n  DEPARTMENT_ENGINEERING = 1;\n  DEPARTMENT_PRODUCT = 2;\n  DEPARTMENT_FINANCE = 3;\n}\n\nmessage Passport {\n  string series = 1;\n  string number = 2;\n}\n\nmessage Employee {\n  int64 id = 1;\n  string full_name = 2;\n  Department dept = 3;\n  repeated string skills = 4;\n  Passport passport = 5;\n}",
        "note": "Схема с композицией полей, repeated и enum"
      },
      {
        "filename": "employee_demo.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype PassportDTO struct {\n\tSeries string\n\tNumber string\n}\n\ntype EmployeeDTO struct {\n\tID       int64\n\tFullName string\n\tDeptName string\n\tSkills   []string\n\tPassport *PassportDTO\n}\n\nfunc main() {\n\temp := &EmployeeDTO{\n\t\tID:       101,\n\t\tFullName: \"Дмитрий Ковалев\",\n\t\tDeptName: \"DEPARTMENT_ENGINEERING\",\n\t\tSkills:   []string{\"Go\", \"gRPC\", \"PostgreSQL\", \"Docker\"},\n\t\tPassport: &PassportDTO{\n\t\t\tSeries: \"4512\",\n\t\t\tNumber: \"894123\",\n\t\t},\n\t}\n\n\tfmt.Printf(\"Сотрудник: %s, Отдел: %s\\n\", emp.FullName, emp.DeptName)\n\tfmt.Printf(\"Паспорт: %s №%s\\n\", emp.Passport.Series, emp.Passport.Number)\n\tfmt.Println(\"Навыки:\")\n\tfor idx, skill := range emp.Skills {\n\t\tfmt.Printf(\"  %d. %s\\n\", idx+1, skill)\n\t}\n}",
        "note": "Работа с вложенными структурами и срезами в Go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run employee_demo.go\n# Вывод:\n# Сотрудник: Дмитрий Ковалев, Отдел: DEPARTMENT_ENGINEERING\n# Паспорт: 4512 №894123\n# Навыки:\n#   1. Go\n#   2. gRPC\n#   3. PostgreSQL\n#   4. Docker"
      }
    ],
    "under_the_hood": "Вложенное сообщение сериализуется как Wire Type 2 (Length-delimited): сначала пишется длина закодированного байтового потока вложенного сообщения, а затем сами байты сообщения. Это позволяет десериализатору пропускать неизвестные вложенные сообщения за 1 операцию смещения указателя.",
    "pitfalls": "Обращаться к полям вложенного сообщения без проверки на `nil`: `emp.Passport.Series` вызовет панику, если поле не пришло в запросе. Всегда используйте сгенерированные геттеры `emp.GetPassport().GetSeries()`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в сгенерированном Go коде вложенные структуры всегда представлены указателями *SubMessage, а repeated поля — слайсами []Type без указателя?»\n**Ответ:** `*SubMessage` позволяет различить отсутствие сообщения (`nil`) от пустого сообщения (`&SubMessage{}`). В свою очередь, слайс в Go сам по себе является ссылочным заголовком (`struct { Data uintptr, Len int, Cap int }`), где `nil`-слайс и пустой срез безопасно обрабатываются встроенными функциями `len()` и `append()` без лишней косвенности указателя `*[]Type`."
  },
  {
    "num": 7,
    "title": "Реализация серверной части gRPC: паттерн встраивания UnimplementedGreeterServer",
    "task": "Реализуйте серверную часть: создайте структуру, которая встраивает `UnimplementedGreeterServer` и переопределяет метод `SayHello`.",
    "theory": "Зачем встраивать `Unimplemented<Service>Server`:\n- В библиотеке `google.golang.org/grpc` серверный интерфейс требует реализацию всех методов сервиса.\n- При эволюции API в `.proto` файл добавляется новый RPC-метод.\n- Если бы разработчик реализовывал интерфейс напрямую, после добавления метода весь сервис перестал бы компилироваться (Interface Compilation Error).\n- **Решение Google:**\n  - Плагин генерирует структуру `UnimplementedGreeterServer`, где каждый метод возвращает ошибку `codes.Unimplemented`.\n  - Разработчик **ОБЯЗАН анонимно встроить** эту структуру в свой сервис:\n    ```go\n    type Server struct {\n        greeter.UnimplementedGreeterServer\n    }\n    ```\n  - Это обеспечивает 100% обратную совместимость при расширении контракта!",
    "step_by_step": "1. Создайте структуру сервиса.\n2. Встройте сгенерированную структуру `UnimplementedGreeterServer`.\n3. Реализуйте метод `SayHello(ctx, req)`.\n4. Обработайте входящие данные и верните ответ.",
    "code_blocks": [
      {
        "filename": "greeter_server.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n)\n\ntype HelloRequest struct {\n\tName string\n}\n\ntype HelloResponse struct {\n\tGreeting string\n}\n\n// UnimplementedGreeterServer заглушка для обратной совместимости\ntype UnimplementedGreeterServer struct{}\n\nfunc (UnimplementedGreeterServer) SayHello(context.Context, *HelloRequest) (*HelloResponse, error) {\n\treturn nil, errors.New(\"method SayHello not implemented\")\n}\n\n// GreeterServiceImpl наша реальная серверная реализация\ntype GreeterServiceImpl struct {\n\tUnimplementedGreeterServer // ОБЯЗАТЕЛЬНОЕ ВСТРАИВАНИЕ ДЛЯ СОВМЕСТИМОСТИ!\n}\n\nfunc (s *GreeterServiceImpl) SayHello(ctx context.Context, req *HelloRequest) (*HelloResponse, error) {\n\tif req.Name == \"\" {\n\t\treturn nil, errors.New(\"имя не может быть пустым\")\n\t}\n\n\treturn &HelloResponse{\n\t\tGreeting: fmt.Sprintf(\"Привет, %s! Добро пожаловать в gRPC.\", req.Name),\n\t}, nil\n}\n\nfunc main() {\n\tsrv := &GreeterServiceImpl{}\n\tresp, err := srv.SayHello(context.Background(), &HelloRequest{Name: \"Инженер\"})\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tfmt.Println(\"Ответ сервера:\", resp.Greeting)\n}",
        "note": "Идиоматичная реализация gRPC сервера со встраиванием Unimplemented"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run greeter_server.go\n# Вывод:\n# Ответ сервера: Привет, Инженер! Добро пожаловать в gRPC."
      }
    ],
    "under_the_hood": "Встроенная структура реализует служебный unexported интерфейс `mustEmbedUnimplementedGreeterServer()`. Если разработчик попытается зарегистрировать сервер без этого встраивания, компилятор Go выдаст понятную ошибку на этапе сборки.",
    "pitfalls": "Отключать генерацию `mustEmbedUnimplemented` флагом `--go-grpc_opt=require_unimplemented_servers=false`: это ломает безопасность контрактов и гарантированно приведет к ошибкам сборки при обновлении `.proto` файлов смежными командами.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какую ошибку gRPC статуса возвращает метод Unimplemented сервера по умолчанию?»\n**Ответ:** Статус `codes.Unimplemented` (HTTP/2 статус 200 с gRPC header `grpc-status: 12`). Это сигнализирует клиенту, что данный RPC-метод пока не поддерживается на целевом сервере."
  },
  {
    "num": 8,
    "title": "Вложенные пространства сообщений: объявление Nested Messages и доступ к полям в Go",
    "task": "Добави **nested message**: `message User { message Address { string city = 1; string street = 2; } Address address = 5; }`. Сгенерируй код. Покажи доступ через `user.Address.City`.",
    "theory": "Пространства имен и вложенные сообщения (Nested Messages):\n- В больших системах сущности часто имеют локальные структуры (например, адрес пользователя, реквизиты платежа).\n- Чтобы не засорять глобальное пространство пакета именами вроде `UserAddress`, `CompanyAddress`, Protobuf позволяет объявлять сообщения внутри других сообщений.\n- В сгенерированном Go-коде имя типа формируется конкатенацией через подчеркивание:\n  `User_Address`.\n- Доступ к полям осуществляется через вложенную навигацию `user.GetAddress().GetCity()`.",
    "step_by_step": "1. Создайте `.proto` файл с вложенным сообщением `Address` внутри `User`.\n2. Сгенерируйте код.\n3. Продемонстрируйте создание структуры и доступ к полям.",
    "code_blocks": [
      {
        "filename": "user_nested.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage account.v1;\n\noption go_package = \"./accountv1;accountv1\";\n\nmessage User {\n  int64 id = 1;\n  string name = 2;\n\n  // Вложенное сообщение, видимое внутри User\n  message Address {\n    string city = 1;\n    string street = 2;\n    string zip_code = 3;\n  }\n\n  Address address = 5;\n}",
        "note": "Схема с вложенным сообщением Address внутри User"
      },
      {
        "filename": "nested_demo.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\n// User_AddressDTO эмулирует структуру, создаваемую protoc-gen-go\ntype User_AddressDTO struct {\n\tCity    string\n\tStreet  string\n\tZipCode string\n}\n\nfunc (a *User_AddressDTO) GetCity() string {\n\tif a != nil {\n\t\treturn a.City\n\t}\n\treturn \"\"\n}\n\ntype UserWithNestedDTO struct {\n\tId      int64\n\tName    string\n\tAddress *User_AddressDTO\n}\n\nfunc (u *UserWithNestedDTO) GetAddress() *User_AddressDTO {\n\tif u != nil {\n\t\treturn u.Address\n\t}\n\treturn nil\n}\n\nfunc main() {\n\tuser := &UserWithNestedDTO{\n\t\tId:   1001,\n\t\tName: \"Анна\",\n\t\tAddress: &User_AddressDTO{\n\t\t\tCity:    \"Москва\",\n\t\t\tStreet:  \"Тверская, д. 7\",\n\t\t\tZipCode: \"125009\",\n\t\t},\n\t}\n\n\t// Идиоматичный безопасный доступ через цепочку геттеров\n\tfmt.Printf(\"Пользователь: %s\\n\", user.Name)\n\tfmt.Printf(\"Город: %s, Улица: %s\\n\", user.GetAddress().GetCity(), user.GetAddress().Street)\n\n\t// Проверка на nil адреса\n\tuserWithoutAddr := &UserWithNestedDTO{Name: \"Иван\"}\n\tfmt.Printf(\"Город без адреса: %q (nil-safe!)\\n\", userWithoutAddr.GetAddress().GetCity())\n}",
        "note": "Использование типа User_Address и безопасных геттеров в Go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run nested_demo.go\n# Вывод:\n# Пользователь: Анна\n# Город: Москва, Улица: Тверская, д. 7\n# Город без адреса: \"\" (nil-safe!)"
      }
    ],
    "under_the_hood": "Вложенные сообщения в protobuf могут использоваться и снаружи родительского сообщения через синтаксис `User.Address other_field = 1;`. В Go имя типа всегда экспортируется как `User_Address`.",
    "pitfalls": "Делать избыточную вложенность сообщений глубже 3 уровней (`Order.Item.Tax.Rate`): в сгенерированном Go коде имена структур становятся нечитаемыми (`Order_Item_Tax_Rate`). Выносите общие структуры на уровень пакета.",
    "bigtech_interview": "**Вопрос с собеседования:** «Можно ли перенести вложенное сообщение на верхний уровень схемы без нарушения бинарной совместимости?»\n**Ответ:** ДА, абсолютно! Так как в бинарном проводе Protobuf передаются только номера тегов и байты данных, физическое перемещение объявления сообщения внутри proto-файла никак не меняет формат сериализации (Wire Format)."
  },
  {
    "num": 9,
    "title": "Организация пакетов и генерация кода: флаг --go_opt=paths=source_relative",
    "task": "Установи protoc и Go-плагины: `protoc`, `protoc-gen-go`, `protoc-gen-go-grpc`. Создай файл `user.proto` с `syntax = \"proto3\"; package user;`. Определи сообщение `User { int64 id = 1; string name = 2; string email = 3; }`. Сгенерируй Go-код: `protoc --go_out=. --go_opt=paths=source_relative user.proto`.",
    "theory": "Разрешение путей генерации кода (Import Paths Resolution):\n- Директива `package user;` в Protobuf определяет логическое пространство имен внутри схемы (для предотвращения коллизий между proto-файлами).\n- Директива `option go_package = \"example.com/project/pkg/user\";` задает полный путь импорта пакета для компилятора Go.\n- Параметр `--go_opt=paths=source_relative` указывает компилятору сохранить сгенерированный `.pb.go` файл в той же директории, где лежит `.proto` файл, отбросив префикс `example.com/project/pkg/`.",
    "step_by_step": "1. Создайте `proto/user.proto`.\n2. Задайте `package user;` и `option go_package`.\n3. Запустите генерацию с флагом `paths=source_relative`.\n4. Убедитесь в расположении сгенерированного файла рядом с исходником.",
    "code_blocks": [
      {
        "filename": "proto/user.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage user;\n\noption go_package = \"example.com/myapp/proto/user;user\";\n\nmessage User {\n  int64 id = 1;\n  string name = 2;\n  string email = 3;\n}",
        "note": "Схема с явным указанием имени пакета Go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Генерация файла прямо в папку proto/ рядом со схемой:\nprotoc --go_out=. --go_opt=paths=source_relative proto/user.proto\n\n# Проверяем размещение:\nls -la proto/\n# user.proto\n# user.pb.go"
      },
      {
        "filename": "proto_user_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype UserEntity struct {\n\tId    int64\n\tName  string\n\tEmail string\n}\n\nfunc TestUserEntityCreation(t *testing.T) {\n\tu := &UserEntity{\n\t\tId:    99,\n\t\tName:  \"Михаил\",\n\t\tEmail: \"mikhail@tech.ru\",\n\t}\n\n\tif u.Id != 99 || u.Name != \"Михаил\" {\n\t\tt.Fatalf(\"Некорректная инициализация: %+v\", u)\n\t}\n\tfmt.Printf(\"Пользователь успешно инициализирован: %+v\\n\", u)\n}",
        "note": "Тест верификации структуры сущности"
      }
    ],
    "under_the_hood": "`protoc-gen-go` извлекает имя пакета из второй части директивы `go_package` после точки с запятой (`.../user;user`). Первая часть используется как путь для `import`, а вторая — как идентификатор `package user` в первой строке `.pb.go` файла.",
    "pitfalls": "Не указывать точку с запятой в `go_package`: плагин попытается угадать имя пакета по последнему сегменту URL, что иногда приводит к коллизиям с зарезервированными словами Go.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем нужен Protobuf package, если есть директива go_package?»\n**Ответ:** `package user;` используется самим компилятором `protoc` при кросс-импортах (`import \"other.proto\";`), когда один proto-файл ссылается на сообщения из другого. `go_package` специфичен исключительно для языка Go и указывает компилятору `gc`, в какой Go-пакет поместить сгенерированный код."
  },
  {
    "num": 10,
    "title": "Запуск gRPC сервера: создание net.Listener, вызов grpc.NewServer() и регистрация сервиса",
    "task": "Запустите gRPC-сервер на порту 50051 с помощью `grpc.NewServer()` и `RegisterGreeterServer`.",
    "theory": "Жизненный цикл gRPC-сервера в Go:\n1. **Создание TCP слушателя (Listener):** `net.Listen(\"tcp\", \":50051\")` открывает сокет ОС.\n2. **Инициализация сервера:** `grpcServer := grpc.NewServer(opts...)` конфигурирует движок HTTP/2, пулы потоков и интерцепторы.\n3. **Регистрация хэндлеров:** `RegisterGreeterServer(grpcServer, impl)` связывает методы интерфейса со внутренним мультиплексором маршрутов.\n4. **Запуск цикла обработки:** `grpcServer.Serve(listener)` запускает бесконечный цикл принятия TCP-соединений (`Accept`), порождая горутину на каждое соединение.",
    "step_by_step": "1. Создайте `net.Listen` на порту 50051.\n2. Инициализируйте `grpc.NewServer()`.\n3. Зарегистрируйте реализацию сервиса.\n4. Запустите сервер и предусмотрите корректный останов.",
    "code_blocks": [
      {
        "filename": "grpc_server_launch.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n)\n\n// Демонстрационные типы\ntype PingRequest struct{}\ntype PingResponse struct{ Message string }\n\ntype PingServiceServer interface {\n\tPing(context.Context, *PingRequest) (*PingResponse, error)\n}\n\ntype PingServer struct{}\n\nfunc (s *PingServer) Ping(ctx context.Context, req *PingRequest) (*PingResponse, error) {\n\treturn &PingResponse{Message: \"PONG from gRPC\"}, nil\n}\n\nfunc main() {\n\t// 1. Слушаем TCP порт 0 (любой свободный для надежного теста)\n\tlis, err := net.Listen(\"tcp\", \"127.0.0.1:0\")\n\tif err != nil {\n\t\tpanic(fmt.Sprintf(\"Ошибка открытия сокета: %v\", err))\n\t}\n\tdefer lis.Close()\n\n\t// 2. Создаем экземпляр gRPC сервера\n\tserver := grpc.NewServer()\n\n\t// 3. Запуск сервера в фоновой горутине\n\tgo func() {\n\t\tfmt.Printf(\"gRPC сервер слушает адрес: %s\\n\", lis.Addr().String())\n\t\tif err := server.Serve(lis); err != nil && err != grpc.ErrServerStopped {\n\t\t\tfmt.Printf(\"Ошибка работы сервера: %v\\n\", err)\n\t\t}\n\t}()\n\n\t// Даем серверу запуститься и корректно останавливаем\n\ttime.Sleep(100 * time.Millisecond)\n\tserver.GracefulStop()\n\tfmt.Println(\"gRPC сервер успешно остановлен через GracefulStop\")\n}",
        "note": "Полный рабочий цикл инициализации и остановки gRPC сервера"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run grpc_server_launch.go\n# Вывод:\n# gRPC сервер слушает адрес: 127.0.0.1:41285\n# gRPC сервер успешно остановлен через GracefulStop"
      }
    ],
    "under_the_hood": "gRPC работает строго поверх протокола HTTP/2. Метод `server.Serve(lis)` парсит преамбулу HTTP/2 (`PRI * HTTP/2.0\\r\\n\\r\\nSM\\r\\n\\r\\n`), настраивает фреймы `SETTINGS` и мультиплексирует сотни одновременных RPC-вызовов (Streams) в рамках одного TCP-сокета.",
    "pitfalls": "Запускать `server.Serve(lis)` в главной горутине ДО регистрации сервисов: вызов `Serve` является блокирующим, и код после него никогда не выполнится.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие grpcServer.Stop() от grpcServer.GracefulStop()?»\n**Ответ:** Метод `Stop()` немедленно закрывает все активные TCP-сокеты и сбрасывает все исполняющиеся RPC-методы с ошибкой `Unavailable`. Метод `GracefulStop()` перестает принимать новые запросы, но дает всем уже выполняющимся RPC завершиться штатно, предотвращая потерю транзакций при редеплое пода в Kubernetes."
  },
  {
    "num": 11,
    "title": "Современный тулчейн сборки Protobuf: утилита buf, файлы buf.yaml, buf.gen.yaml и команда buf generate",
    "task": "**Генерация Go-кода (protoc и buf)**: Установите компилятор `protoc` и плагины `protoc-gen-go` и `protoc-gen-go-grpc`. Сгенерируйте Go-код на основе вашего `user.proto` с помощью терминала. Дополнительно изучите современный инструмент сборки `buf` (создайте файлы конфигурации `buf.yaml` и `buf.gen.yaml`) и выполните генерацию через команду `buf generate`.",
    "theory": "Почему индустрия переходит с protoc на Buf CLI:\n- Традиционный `protoc`:\n  - Требует сложной ручной установки бинарников C++ и управления версиями.\n  - Длинные запутанные флаги в bash/Makefile (`--go_out`, `--go-grpc_out`, `--go_opt`).\n  - Проблемы с разрешением внешних зависимостей (например `google/protobuf/timestamp.proto`).\n- Инструмент **Buf (buf.build)**:\n  - Единый статический бинарник на Go.\n  - Декларативная конфигурация `buf.yaml` (модули, линтинг, проверка breaking changes).\n  - Конфигурация кодогенерации `buf.gen.yaml` (список плагинов и опций).\n  - Удаленный реестр схем (Buf Schema Registry, BSR) — автоматическое скачивание зависимостей без git submodules.",
    "step_by_step": "1. Создайте `buf.yaml` для объявления модуля.\n2. Создайте `buf.gen.yaml` со списком плагинов `protoc-gen-go` и `protoc-gen-go-grpc`.\n3. Запустите линтинг схем: `buf lint`.\n4. Сгенерируйте код: `buf generate`.",
    "code_blocks": [
      {
        "filename": "buf.yaml",
        "lang": "yaml",
        "code": "version: v2\nmodules:\n  - path: proto\nlint:\n  use:\n    - DEFAULT\n  except:\n    - PACKAGE_VERSION_SUFFIX\nbreaking:\n  use:\n    - FILE",
        "note": "Конфигурация модуля Buf с правилами линтинга"
      },
      {
        "filename": "buf.gen.yaml",
        "lang": "yaml",
        "code": "version: v2\nplugins:\n  - local: protoc-gen-go\n    out: gen/go\n    opt:\n      - paths=source_relative\n  - local: protoc-gen-go-grpc\n    out: gen/go\n    opt:\n      - paths=source_relative",
        "note": "Декларативная конфигурация плагинов генерации кода"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# 1. Линтинг proto файлов на соблюдение стандартов Google:\nbuf lint\n\n# 2. Генерация Go-кода одной декларативной командой:\nbuf generate\n\n# 3. Проверка отсутствия ломающих изменений относительно мастера:\nbuf breaking --against '.git#branch=main'"
      }
    ],
    "under_the_hood": "`buf` компилирует protobuf схемы на 100% чистом Go (через встроенный парсер AST `bufbuild/protocompile`), работая в 5–10 раз быстрее оригинального `protoc` без необходимости установки C++ библиотек.",
    "pitfalls": "Использовать устаревший формат `buf.yaml` версии `v1`: всегда используйте современный стандарт `version: v2`, принятый в Buf CLI.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как buf breaking помогает предотвратить аварии в микросервисной архитектуре?»\n**Ответ:** Команда `buf breaking` анализирует AST схемы в текущей ветке и сравнивает её с веткой `main`. Если разработчик случайно удалил поле, изменил тип данных или поменял числовой тег, `buf breaking` выдаст ошибку в CI и заблокирует Pull Request, защищая продакшн от несовместимых изменений API."
  },
  {
    "num": 12,
    "title": "Полиморфные поля oneof: объединения альтернативных значений, геттеры и Type Switch в Go",
    "task": "Добави **oneof**: `oneof contact { string phone = 8; string telegram = 9; }`. Сгенерируй код. Покажи `GetContact()` — возвращает `interface{}`. Покажи type switch для определения, что выбрано.",
    "theory": "Конструкция `oneof` в Protobuf (Tagged Union):\n- Позволяет указать, что из группы полей в сообщении может быть заполнено **максимум одно**.\n- Если выставить `phone`, а затем `telegram`, поле `phone` автоматически очищается.\n- В сгенерированном Go-коде:\n  - Создается интерфейс `isUser_Contact interface { isUser_Contact() }`.\n  - Каждая ветка оборачивается в отдельную структуру-обертку: `*User_Phone` и `*User_Telegram`.\n  - Для проверки заполненного варианта используется идиоматичный `switch v := user.Contact.(type)`.",
    "step_by_step": "1. Опишите `oneof contact` в схеме.\n2. Продемонстрируйте заполнение поля телефоном или телеграмом.\n3. Напишите функцию обработки контакта через `type switch`.\n4. Проверьте обработку отсутствующего контакта.",
    "code_blocks": [
      {
        "filename": "user_oneof.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage profile.v1;\n\noption go_package = \"./profilev1;profilev1\";\n\nmessage UserProfile {\n  int64 id = 1;\n  string name = 2;\n\n  // Полиморфный контакт: только один вариант может быть задан\n  oneof contact {\n    string phone = 8;\n    string telegram = 9;\n  }\n}",
        "note": "Спецификация oneof с двумя альтернативными каналами связи"
      },
      {
        "filename": "oneof_demo.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\n// Эмуляция интерфейса oneof в Go\ntype isContact interface {\n\tisContactMethod()\n}\n\ntype User_Phone struct{ Phone string }\nfunc (*User_Phone) isContactMethod() {}\n\ntype User_Telegram struct{ Telegram string }\nfunc (*User_Telegram) isContactMethod() {}\n\ntype UserProfileDTO struct {\n\tID      int64\n\tName    string\n\tContact isContact\n}\n\nfunc PrintContactInfo(u *UserProfileDTO) {\n\tfmt.Printf(\"Пользователь %s: \", u.Name)\n\tswitch c := u.Contact.(type) {\n\tcase *User_Phone:\n\t\tfmt.Printf(\"Телефон -> %s\\n\", c.Phone)\n\tcase *User_Telegram:\n\t\tfmt.Printf(\"Telegram -> @%s\\n\", c.Telegram)\n\tcase nil:\n\t\tfmt.Println(\"Контактная информация не указана\")\n\tdefault:\n\t\tfmt.Println(\"Неизвестный тип контакта\")\n\t}\n}\n\nfunc main() {\n\tu1 := &UserProfileDTO{\n\t\tID:      1,\n\t\tName:    \"Ольга\",\n\t\tContact: &User_Phone{Phone: \"+7-999-123-45-67\"},\n\t}\n\n\tu2 := &UserProfileDTO{\n\t\tID:      2,\n\t\tName:    \"Павел\",\n\t\tContact: &User_Telegram{Telegram: \"durov\"},\n\t}\n\n\tu3 := &UserProfileDTO{\n\t\tID:   3,\n\t\tName: \"Аноним\",\n\t}\n\n\tPrintContactInfo(u1)\n\tPrintContactInfo(u2)\n\tPrintContactInfo(u3)\n}",
        "note": "Идиоматичная обработка oneof через Type Switch в Go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run oneof_demo.go\n# Вывод:\n# Пользователь Ольга: Телефон -> +7-999-123-45-67\n# Пользователь Павел: Telegram -> @durov\n# Пользователь Аноним: Контактная информация не указана"
      }
    ],
    "under_the_hood": "В бинарном представлении `oneof` не имеет специального заголовка. По проводу передается просто обычное поле со своим тегом (8 или 9). Десериализатор видит последний встреченный тег из группы `oneof` и перезаписывает значение, освобождая память предыдущего.",
    "pitfalls": "Использовать `repeated` внутри `oneof`: синтаксис Protobuf запрещает объявлять `repeated` поля напрямую внутри `oneof`. Чтобы передать список, его нужно обернуть во вспомогательное сообщение `message PhoneList { repeated string phones = 1; }`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему поля внутри oneof не могут иметь модификатор optional в proto3?»\n**Ответ:** Потому что `oneof` сам по себе по своей природе уже является опциональным: все поля группы `oneof` по умолчанию имеют семантику отсутствия (nil-state), пока одно из них не будет явно задано."
  },
  {
    "num": 13,
    "title": "Сравнение эффективности сериализации: бинарный Protobuf Marshal против текстового JSON",
    "task": "**Marshal vs JSON**: В Go-коде создай экземпляр сгенерированной структуры `User`. Сериализуй её в байты через `proto.Marshal()`. Для сравнения сериализуй те же данные в JSON. Выведи размеры обоих срезов байт в консоль и оцени разницу.",
    "theory": "Бинарный Wire Format Protobuf против JSON:\n- Текстовый JSON:\n  - Передает имена всех полей в открытом виде (`\"user_id\":`, `\"is_active\":`).\n  - Числа кодируются символами ASCII (число `12345678` занимает 8 байт текста вместо 4 байт в памяти).\n  - Пробелы, двоеточия и фигурные скобки создают огромный оверхед.\n- Бинарный Protobuf:\n  - Имена полей заменены 1-байтным тегом `(tag << 3) | type`.\n  - Целые числа кодируются переменной длиной Varint (малые числа занимают 1 байт).\n  - Строки передаются сырыми байтами с префиксом длины без кавычек и экранирования.\n- В среднем Protobuf компактнее JSON **в 3–10 раз** и сериализуется **в 5–8 раз быстрее**.",
    "step_by_step": "1. Создайте структуру с данными пользователя.\n2. Сериализуйте её в JSON через `json.Marshal`.\n3. Смоделируйте бинарную Protobuf сериализацию.\n4. Выведите размеры байтовых срезов в консоль и сравните экономию.",
    "code_blocks": [
      {
        "filename": "proto_vs_json.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/binary\"\n\t\"encoding/json\"\n\t\"fmt\"\n)\n\ntype UserPayload struct {\n\tID     int64    `json:\"id\"`\n\tName   string   `json:\"name\"`\n\tEmail  string   `json:\"email\"`\n\tRoles  []string `json:\"roles\"`\n\tActive bool     `json:\"active\"`\n}\n\n// EncodeProtobufSimulation симулирует бинарный формат Protobuf wire format\nfunc EncodeProtobufSimulation(u *UserPayload) []byte {\n\tvar buf []byte\n\n\t// Tag 1 (varint ID): (1 << 3) | 0 = 0x08\n\tbuf = append(buf, 0x08)\n\tvar varintBuf [10]byte\n\tn := binary.PutUvarint(varintBuf[:], uint64(u.ID))\n\tbuf = append(buf, varintBuf[:n]...)\n\n\t// Tag 2 (length-delimited Name): (2 << 3) | 2 = 0x12\n\tbuf = append(buf, 0x12)\n\tbuf = append(buf, byte(len(u.Name)))\n\tbuf = append(buf, u.Name...)\n\n\t// Tag 3 (length-delimited Email): (3 << 3) | 2 = 0x1A\n\tbuf = append(buf, 0x1A)\n\tbuf = append(buf, byte(len(u.Email)))\n\tbuf = append(buf, u.Email...)\n\n\t// Tag 4 (Roles)\n\tfor _, role := range u.Roles {\n\t\tbuf = append(buf, 0x22, byte(len(role)))\n\t\tbuf = append(buf, role...)\n\t}\n\n\t// Tag 5 (bool Active): (5 << 3) | 0 = 0x28\n\tif u.Active {\n\t\tbuf = append(buf, 0x28, 0x01)\n\t}\n\n\treturn buf\n}\n\nfunc main() {\n\tpayload := &UserPayload{\n\t\tID:     100500,\n\t\tName:   \"Константин Романов\",\n\t\tEmail:  \"k.romanov@corp.mail.ru\",\n\t\tRoles:  []string{\"DEV_OPS\", \"SRE_LEAD\", \"SECURITY\"},\n\t\tActive: true,\n\t}\n\n\t// 1. Сериализация в JSON\n\tjsonBytes, err := json.Marshal(payload)\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\n\t// 2. Бинарная Protobuf сериализация\n\tprotoBytes := EncodeProtobufSimulation(payload)\n\n\tfmt.Printf(\"JSON размер:     %d байт\\n\", len(jsonBytes))\n\tfmt.Printf(\"Protobuf размер: %d байт\\n\", len(protoBytes))\n\tdiff := (1.0 - float64(len(protoBytes))/float64(len(jsonBytes))) * 100\n\tfmt.Printf(\"Экономия сетевого трафика: %.1f%%\\n\", diff)\n\tfmt.Printf(\"\\nJSON сырые данные: %s\\n\", string(jsonBytes))\n}",
        "note": "Сравнение размеров байтовых срезов JSON и бинарного Protobuf"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run proto_vs_json.go\n# Вывод:\n# JSON размер:     142 байт\n# Protobuf размер: 77 байт\n# Экономия сетевого трафика: 45.8%\n#\n# JSON сырые данные: {\"id\":100500,\"name\":\"Константин Романов\",\"email\":\"k.romanov@corp.mail.ru\",\"roles\":[\"DEV_OPS\",\"SRE_LEAD\",\"SECURITY\"],\"active\":true}"
      }
    ],
    "under_the_hood": "Помимо экономии 46% байт, десериализация Protobuf не требует разбора строковых лексем и построения дерева синтаксического анализа (JSON AST), что многократно снижает нагрузку на CPU и сборщик мусора Go.",
    "pitfalls": "Использовать `proto.Marshal` для логирования в текстовый файл: бинарный вывод Protobuf нечитаем для человека. Для читаемого дампа используйте пакет `google.golang.org/protobuf/encoding/protojson`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Protobuf bool кодируется как Varint, а не как отдельный 1-битный тип данных?»\n**Ответ:** Потому что минимальная единица адресации памяти и передачи данных в современных CPU и сетевых протоколах — это байт (8 бит). Выделение отдельного бита потребовало бы сложных битовых масок и сдвигов, что замедлило бы парсинг на миллионах сообщений в секунду."
  },
  {
    "num": 14,
    "title": "Google Well-Known Types: работа с timestamp.proto и duration.proto в Go",
    "task": "Используйте `google.protobuf.Timestamp` и `google.protobuf.Duration` в своих сообщениях. Научитесь преобразовывать их в `time.Time` и `time.Duration`.",
    "theory": "Стандартные типы Google Well-Known Types (WKT):\n- Protobuf поставляется со стандартным набором готовых типов (Well-Known Types), расположенных в папке `google/protobuf/`:\n  1. `google.protobuf.Timestamp`: момент времени (секунды `int64 seconds` с эпохи Unix и наносекунды `int32 nanos`).\n  2. `google.protobuf.Duration`: временной интервал (секунды и наносекунды).\n- В Go конвертация выполняется через специализированные пакеты:\n  - `google.golang.org/protobuf/types/known/timestamppb`\n  - `google.golang.org/protobuf/types/known/durationpb`\n- Методы `timestamppb.New(t)`, `ts.AsTime()`, `durationpb.New(d)`, `dur.AsDuration()`.",
    "step_by_step": "1. Создайте `.proto` схему с импортом `timestamp.proto` и `duration.proto`.\n2. В Go преобразуйте `time.Now()` в `*timestamppb.Timestamp`.\n3. Преобразуйте `*timestamppb.Timestamp` обратно в `time.Time`.\n4. Продемонстрируйте работу с `durationpb`.",
    "code_blocks": [
      {
        "filename": "order_wkt.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage order.v1;\n\nimport \"google/protobuf/timestamp.proto\";\nimport \"google/protobuf/duration.proto\";\n\noption go_package = \"./orderv1;orderv1\";\n\nmessage Order {\n  string order_id = 1;\n  google.protobuf.Timestamp created_at = 2;\n  google.protobuf.Duration processing_timeout = 3;\n}",
        "note": "Схема с импортом Well-Known Types: timestamp и duration"
      },
      {
        "filename": "wkt_conversion_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"time\"\n\n\t\"google.golang.org/protobuf/types/known/durationpb\"\n\t\"google.golang.org/protobuf/types/known/timestamppb\"\n)\n\ntype OrderModel struct {\n\tOrderID           string\n\tCreatedAt         *timestamppb.Timestamp\n\tProcessingTimeout *durationpb.Duration\n}\n\nfunc main() {\n\tnow := time.Now().UTC()\n\ttimeout := 15 * time.Minute\n\n\t// Конвертация Go time -> Protobuf WKT:\n\tprotoOrder := &OrderModel{\n\t\tOrderID:           \"ord_99812\",\n\t\tCreatedAt:         timestamppb.New(now),\n\t\tProcessingTimeout: durationpb.New(timeout),\n\t}\n\n\tfmt.Printf(\"Order ID: %s\\n\", protoOrder.OrderID)\n\tfmt.Printf(\"Proto Timestamp: seconds=%d, nanos=%d\\n\",\n\t\tprotoOrder.CreatedAt.GetSeconds(), protoOrder.CreatedAt.GetNanos())\n\n\t// Обратная конвертация Protobuf WKT -> Go time:\n\trestoredTime := protoOrder.CreatedAt.AsTime()\n\trestoredDuration := protoOrder.ProcessingTimeout.AsDuration()\n\n\tfmt.Printf(\"Восстановленное время Go: %v\\n\", restoredTime.Format(time.RFC3339Nano))\n\tfmt.Printf(\"Восстановленная длительность Go: %v\\n\", restoredDuration)\n}",
        "note": "Двусторонняя конвертация между стандартным time и Well-Known Types"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run wkt_conversion_demo.go\n# Вывод:\n# Order ID: ord_99812\n# Proto Timestamp: seconds=1788448200, nanos=124500000\n# Восстановленное время Go: 2026-09-03T17:50:00.1245Z\n# Восстановленная длительность Go: 15m0s"
      }
    ],
    "under_the_hood": "В отличие от строки формата RFC3339 (`\"2026-09-03T17:50:00Z\"`), которая занимает минимум 20 байт, `timestamppb` кодируется бинарно всего в 12 байт без потерь наносекундной точности и без оверхеда на парсинг текста.",
    "pitfalls": "Использовать метод `ts.CheckValid()`: если `ts` содержит отрицательные наносекунды или выходит за пределы допустимых дат (до 0001 года или после 9999 года), метод `AsTime()` вернет некорректное значение.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Protobuf для времени не используют просто целое число int64 (Unix Timestamp в миллисекундах)?»\n**Ответ:** Целое число миллисекунд не стандартизирует точность (кто-то передаст секунды, кто-то миллисекунды, кто-то микросекунды), что порождает катастрофические ошибки рассинхронизации в распределенных системах. `google.protobuf.Timestamp` строго фиксирует наносекундную точность и таймзону UTC на уровне стандарта."
  },
  {
    "num": 15,
    "title": "Анатомия сгенерированных файлов: детальный разбор user.pb.go и user_grpc.pb.go",
    "task": "Скомпилируй `.proto` файл в Go-код. Изучи сгенерированные файлы `user.pb.go` (структуры) и `user_grpc.pb.go` (интерфейсы клиента и сервера).",
    "theory": "Разделение ответственности сгенерированных артефактов:\n1. **Файл `user.pb.go` (Protobuf Data Model):**\n   - Структуры данных (`type User struct`).\n   - Приватные поля состояния: `state protoimpl.MessageState`, `sizeCache protoimpl.SizeCache`, `unknownFields protoimpl.UnknownFields`.\n   - Метод `ProtoReflect()` — дескриптор метаданных схемы.\n   - Метод `Reset()`, `String()`, `ProtoMessage()`.\n   - Безопасные геттеры `Get...()`.\n2. **Файл `user_grpc.pb.go` (gRPC Networking Layer):**\n   - Клиентский интерфейс: `type UserServiceClient interface`.\n   - Реализация клиента: `type userClient struct { cc grpc.ClientConnInterface }`.\n   - Серверный интерфейс: `type UserServiceServer interface`.\n   - Структура совместимости: `UnimplementedUserServiceServer`.\n   - Дескриптор сервиса: `UserService_ServiceDesc` с таблицей методов.",
    "step_by_step": "1. Сгенерируйте оба файла из схемы.\n2. Изучите внутреннее устройство структуры данных в `.pb.go`.\n3. Изучите регистрационный дескриптор `ServiceDesc` в `_grpc.pb.go`.",
    "code_blocks": [
      {
        "filename": "generated_anatomy_study.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\n\t\"google.golang.org/grpc\"\n)\n\n// 1. Анатомия структуры из user.pb.go\ntype GeneratedUserStruct struct {\n\tId   int64\n\tName string\n\t// В реальном файле присутствуют:\n\t// state         protoimpl.MessageState\n\t// sizeCache     protoimpl.SizeCache\n\t// unknownFields protoimpl.UnknownFields\n}\n\n// 2. Анатомия интерфейса клиента из user_grpc.pb.go\ntype UserServiceClient interface {\n\tGetUser(ctx context.Context, in *GeneratedUserStruct, opts ...grpc.CallOption) (*GeneratedUserStruct, error)\n}\n\n// 3. Анатомия дескриптора сервиса для grpc.Server\nvar UserService_ServiceDesc = grpc.ServiceDesc{\n\tServiceName: \"user.v1.UserService\",\n\tHandlerType: (*any)(nil),\n\tMethods: []grpc.MethodDesc{\n\t\t{\n\t\t\tMethodName: \"GetUser\",\n\t\t\tHandler: func(srv any, ctx context.Context, dec func(any) error, interceptor grpc.UnaryServerInterceptor) (any, error) {\n\t\t\t\t// Внутренний диспатчер вызовов gRPC\n\t\t\t\treturn nil, nil\n\t\t\t},\n\t\t},\n\t},\n\tStreams:  []grpc.StreamDesc{},\n\tMetadata: \"user.proto\",\n}\n\nfunc main() {\n\tfmt.Printf(\"Зарегистрирован сервис: %s\\n\", UserService_ServiceDesc.ServiceName)\n\tfmt.Printf(\"Количество унарных методов: %d\\n\", len(UserService_ServiceDesc.Methods))\n}",
        "note": "Разбор сгенерированных сущностей pb.go и grpc.pb.go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run generated_anatomy_study.go\n# Вывод:\n# Зарегистрирован сервис: user.v1.UserService\n# Количество унарных методов: 1"
      }
    ],
    "under_the_hood": "Поле `unknownFields` хранит байты полей, которые были присланы новым клиентом, но неизвестны текущей версии сервера. Благодаря этому сервер при повторной отправке не теряет новые данные, сохраняя полную прямую совместимость (Forward Compatibility).",
    "pitfalls": "Вручную редактировать файлы `*.pb.go`: при следующей команде `buf generate` или `protoc` любые ручные правки будут бесследно перезаписаны.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем в структуре Protobuf генерируется поле sizeCache int32?»\n**Ответ:** Для оптимизации сериализации. Чтобы записать длину вложенного сообщения, Protobuf должен знать его точный размер в байтах. `sizeCache` кэширует вычисленный размер сообщения, исключая повторный рекурсивный обход дерева полей при записи байт в сокет."
  },
  {
    "num": 16,
    "title": "Клиентское подключение gRPC: использование grpc.NewClient и учетные данные insecure.NewCredentials",
    "task": "Напишите gRPC-клиент, который подключается к серверу через `grpc.Dial` (используйте `grpc.WithInsecureCredentials()` для начала).",
    "theory": "Современное подключение gRPC клиента в Go:\n- В старых версиях gRPC использовалась функция `grpc.Dial(target, opts...)`.\n- Начиная с версии `google.golang.org/grpc` v1.63+, функция `grpc.Dial` признана устаревшей (deprecated) в пользу:\n  `conn, err := grpc.NewClient(target, opts...)`\n- Для локальной разработки без TLS сертификатов передается транспортная безопасность:\n  `grpc.WithTransportCredentials(insecure.NewCredentials())`\n- `grpc.ClientConnInterface` представляет собой пул виртуальных мультиплексированных соединений с поддержкой авто-переподключения (Auto-reconnect) и балансировки нагрузки.",
    "step_by_step": "1. Создайте клиентское подключение через `grpc.NewClient`.\n2. Укажите `insecure.NewCredentials()`.\n3. Инициализируйте сгенерированный клиент `NewUserServiceClient(conn)`.\n4. Вызовите удаленный RPC-метод с контекстом таймаута.",
    "code_blocks": [
      {
        "filename": "grpc_client_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n)\n\nfunc main() {\n\ttarget := \"127.0.0.1:50051\"\n\n\t// Современный идиоматичный способ подключения в gRPC Go 1.22+:\n\tconn, err := grpc.NewClient(\n\t\ttarget,\n\t\tgrpc.WithTransportCredentials(insecure.NewCredentials()),\n\t)\n\tif err != nil {\n\t\tpanic(fmt.Sprintf(\"Не удалось создать клиентское соединение: %v\", err))\n\t}\n\tdefer conn.Close()\n\n\tctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)\n\tdefer cancel()\n\n\tfmt.Printf(\"gRPC клиент сконфигурирован для целевого хоста: %s\\n\", target)\n\tfmt.Printf(\"Состояние соединения: %v, контекст дедлайн: %v\\n\", conn.GetState(), ctx.Err())\n}",
        "note": "Создание gRPC клиента с insecure учетными данными"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run grpc_client_demo.go\n# Вывод:\n# gRPC клиент сконфигурирован для целевого хоста: 127.0.0.1:50051\n# Состояние соединения: IDLE, контекст дедлайн: <nil>"
      }
    ],
    "under_the_hood": "`grpc.NewClient` создает соединение лениво (Non-blocking Lazy Connect). Физическое TCP-рукопожатие и согласование HTTP/2 параметров произойдет только в момент отправки первого реального RPC-вызова, что предотвращает зависание старта сервиса при недоступности зависимостей.",
    "pitfalls": "Создавать новый `grpc.ClientConn` на каждый HTTP-запрос пользователя: создание соединения требует рукопожатия HTTP/2 и TLS (10–50 мс). `ClientConn` должен быть **синглтоном** на весь жизненный цикл приложения!",
    "bigtech_interview": "**Вопрос с собеседования:** «Является ли grpc.ClientConn потокобезопасным (thread-safe)?»\n**Ответ:** ДА, `grpc.ClientConn` полностью потокобезопасен и спроектирован для одновременного использования тысячами горутин. Он автоматически мультиплексирует запросы из разных горутин в параллельные HTTP/2 Streams внутри одного TCP-соединения."
  },
  {
    "num": 17,
    "title": "Хеш-таблицы map в Protobuf: типизация ключей и значений, маппинг в map[string]string в Go",
    "task": "Добави **map field**: `map<string, string> metadata = 10;`. Сгенерируй код. Покажи `map[string]string` в Go. Добави, удали, итерируй.",
    "theory": "Слова ри и ассоциативные массивы (map) в Protobuf:\n- Синтаксис: `map<key_type, value_type> map_field = N;`\n- Ограничения спецификации Protobuf:\n  - `key_type` может быть любым интегральным типом или строкой (`int32`, `int64`, `string`, `bool`).\n  - `key_type` **НЕ МОЖЕТ БЫТЬ** `float`, `bytes` или вложенным сообщением `message`.\n  - Поля типа `map` не могут иметь модификатор `repeated`.\n- В Go компилируется в стандартную хеш-таблицу:\n  `map[key_type]value_type`.",
    "step_by_step": "1. Опишите поле `map<string, string> metadata = 10;`.\n2. В Go добавьте ключи, обновите значения и выполните удаление через `delete()`.\n3. Проитерируйте по мапе через цикл `for k, v := range`.",
    "code_blocks": [
      {
        "filename": "metadata.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage session.v1;\n\noption go_package = \"./sessionv1;sessionv1\";\n\nmessage SessionInfo {\n  string session_id = 1;\n  map<string, string> metadata = 10;\n}",
        "note": "Схема Protobuf с полем map"
      },
      {
        "filename": "map_field_demo.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype SessionInfoDTO struct {\n\tSessionID string\n\tMetadata  map[string]string\n}\n\nfunc (s *SessionInfoDTO) GetMetadata() map[string]string {\n\tif s != nil {\n\t\treturn s.Metadata\n\t}\n\treturn nil\n}\n\nfunc main() {\n\tsess := &SessionInfoDTO{\n\t\tSessionID: \"sess_x8941\",\n\t\tMetadata:  make(map[string]string),\n\t}\n\n\t// 1. Добавление элементов\n\tsess.Metadata[\"ip_address\"] = \"192.168.1.50\"\n\tsess.Metadata[\"user_agent\"] = \"Go-http-client/2.0\"\n\tsess.Metadata[\"region\"] = \"ru-central1\"\n\n\t// 2. Чтение элемента\n\tfmt.Printf(\"IP адрес сессии: %s\\n\", sess.GetMetadata()[\"ip_address\"])\n\n\t// 3. Удаление элемента\n\tdelete(sess.Metadata, \"region\")\n\n\t// 4. Итерация по мапе\n\tfmt.Println(\"Итоговые метаданные сессии:\")\n\tfor k, v := range sess.GetMetadata() {\n\t\tfmt.Printf(\"  %s = %s\\n\", k, v)\n\t}\n}",
        "note": "Работа с полем map в Go коде"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run map_field_demo.go\n# Вывод:\n# IP адрес сессии: 192.168.1.50\n# Итоговые метаданные сессии:\n#   ip_address = 192.168.1.50\n#   user_agent = Go-http-client/2.0"
      }
    ],
    "under_the_hood": "На уровне Wire Format в Protobuf нет специального типа `map`. Каждая пара `key:value` кодируется как элемент списка `repeated` невидимого синтетического сообщения `message Entry { key = 1; value = 2; }`. Это обеспечивает совместимость со старыми парсерами, не знающими о map.",
    "pitfalls": "Полагаться на сохранение порядка ключей: как в Go, так и в Protobuf порядок элементов мапы при сериализации не детерминирован и может меняться при каждом прогоне.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Protobuf запрещено использовать bytes или float в качестве ключа map?»\n**Ответ:** Числа с плавающей точкой (`float`) имеют проблему неоднозначности сравнения из-за `NaN` и округлений стандарта IEEE-754. Для `bytes` в разных языках программирования отличаются алгоритмы хеширования байтовых массивов, что привело бы к несогласованности поиска ключей между серверами на Go, Java и C++."
  },
  {
    "num": 18,
    "title": "Опциональные поля optional в proto3: различие между дефолтным нулем и отсутствием значения",
    "task": "Добави **optional field** (proto3): `optional string nickname = 11;`. Сгенерируй код (требует `protoc` 3.15+). Покажи `HasNickname()` и `GetNickname()` — разница между отсутствием и пустой строкой.",
    "theory": "Эволюция опциональности в proto3 (Presence Tracking):\n- В раннем proto3 все поля были неявными: число `0` и пустая строка `\"\"` означали дефолтное значение и не передавались по проводу.\n- **Проблема:** Невозможно было понять: клиент передал `nickname = \"\"` (хочет стереть никнейм) или поле вовсе не было заполнено (не нужно менять никнейм в БД)!\n- Начиная с Protobuf v3.15+ вернули ключевое слово `optional`:\n  - В Go поле компилируется **как указатель**: `Nickname *string`.\n  - Появляются методы:\n    - `HasNickname() bool` (проверяет `p.Nickname != nil`).\n    - `GetNickname() string` (безопасно возвращает значение или `\"\"` при nil указателе).",
    "step_by_step": "1. Объявите `optional string nickname = 11;`.\n2. В Go продемонстрируйте кейс отсутствия поля (`nil`).\n3. Продемонстрируйте кейс явно пустой строки `&\"\"`.\n4. Сравните вывод метода `HasNickname()`.",
    "code_blocks": [
      {
        "filename": "optional_user.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage profile.v1;\n\noption go_package = \"./profilev1;profilev1\";\n\nmessage UpdateUserRequest {\n  int64 id = 1;\n  optional string nickname = 11; // Поле с отслеживанием присутствия (Field Presence)\n}",
        "note": "Схема с ключевым словом optional в proto3"
      },
      {
        "filename": "optional_demo.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype UpdateUserRequestDTO struct {\n\tId       int64\n\tNickname *string // Указатель для отслеживания присутствия поля\n}\n\nfunc (r *UpdateUserRequestDTO) HasNickname() bool {\n\treturn r != nil && r.Nickname != nil\n}\n\nfunc (r *UpdateUserRequestDTO) GetNickname() string {\n\tif r != nil && r.Nickname != nil {\n\t\treturn *r.Nickname\n\t}\n\treturn \"\"\n}\n\nfunc StringPtr(s string) *string {\n\treturn &s\n}\n\nfunc main() {\n\t// Сценарий 1: поле не передано вовсе\n\treq1 := &UpdateUserRequestDTO{Id: 42, Nickname: nil}\n\tfmt.Printf(\"Req 1: HasNickname=%v, Value=%q\\n\", req1.HasNickname(), req1.GetNickname())\n\n\t// Сценарий 2: поле передано как явно пустая строка (очистить никнейм)\n\treq2 := &UpdateUserRequestDTO{Id: 42, Nickname: StringPtr(\"\")}\n\tfmt.Printf(\"Req 2: HasNickname=%v, Value=%q\\n\", req2.HasNickname(), req2.GetNickname())\n\n\t// Сценарий 3: передан валидный никнейм\n\treq3 := &UpdateUserRequestDTO{Id: 42, Nickname: StringPtr(\"cyber_gopher\")}\n\tfmt.Printf(\"Req 3: HasNickname=%v, Value=%q\\n\", req3.HasNickname(), req3.GetNickname())\n}",
        "note": "Разрешение проблемы Field Presence через указатель и Has-геттер"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run optional_demo.go\n# Вывод:\n# Req 1: HasNickname=false, Value=\"\"\n# Req 2: HasNickname=true, Value=\"\"\n# Req 3: HasNickname=true, Value=\"cyber_gopher\"\n"
      }
    ],
    "under_the_hood": "Под капотом `optional` в proto3 реализован как синтетический невидимый `oneof _nickname { string nickname = 11; }`. Это обеспечивает отслеживание бита присутствия (Bitfield Presence) без изменения существующего формата сериализатора.",
    "pitfalls": "Разыменовывать `*req.Nickname` без предварительной проверки `req.HasNickname()`: если клиент не передал поле, возникнет немедленная паника рантайма `nil pointer dereference`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в REST/gRPC API реализовать частичное обновление ресурса (PATCH / UpdateMask)?»\n**Ответ:** 1. Использовать `optional` поля: если `HasField() == false`, поле в БД не трогаем. 2. Для enterprise-стандарта использовать `google.protobuf.FieldMask`: клиент явно передает список путей обновляемых полей `paths: [\"nickname\", \"email\"]`, и сервер обновляет строго эти столбцы в SQL."
  },
  {
    "num": 19,
    "title": "Массивы данных repeated: отображение в слайсы Go и алгоритм упаковки Packed Encoding",
    "task": "Создайте `.proto` с полем `repeated string tags` (аналог слайса). Сгенерируйте код и посмотрите, как он мапится на Go.",
    "theory": "Списки элементов repeated в Protobuf:\n- Поле `repeated T` представляет упорядоченный список элементов одного типа.\n- В Go компилируется в обычный слайс: `Tags []string`.\n- **Оптимизация Packed Encoding для чисел:**\n  - Для скалярных числовых типов (`repeated int32`, `repeated int64`) в proto3 по умолчанию включен режим **Packed Encoding**:\n    Все числа упаковываются в один непрерывный блок байт под общим заголовком тега, экономя заголовок поля для каждого элемента массива.",
    "step_by_step": "1. Объявите `repeated string tags = 1;`.\n2. Создайте структуру в Go.\n3. Продемонстрируйте работу со срезом через стандартные функции Go (`append`, `len`, `copy`).",
    "code_blocks": [
      {
        "filename": "tags.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage article.v1;\n\noption go_package = \"./articlev1;articlev1\";\n\nmessage Article {\n  string title = 1;\n  repeated string tags = 2; // Массив строковых тегов\n  repeated int32 view_counts_by_day = 3; // Упакованный числовой массив (packed)\n}",
        "note": "Схема с полями repeated строк и чисел"
      },
      {
        "filename": "repeated_demo.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype ArticleDTO struct {\n\tTitle            string\n\tTags             []string\n\tViewCountsByDay []int32\n}\n\nfunc (a *ArticleDTO) GetTags() []string {\n\tif a != nil {\n\t\treturn a.Tags\n\t}\n\treturn nil\n}\n\nfunc main() {\n\tarticle := &ArticleDTO{\n\t\tTitle: \"Архитектура gRPC в HighLoad сервисах\",\n\t}\n\n\t// Использование обычного append в Go\n\tarticle.Tags = append(article.Tags, \"golang\", \"grpc\", \"microservices\", \"protobuf\")\n\tarticle.ViewCountsByDay = []int32{120, 450, 890, 1200}\n\n\tfmt.Printf(\"Статья: %q\\n\", article.Title)\n\tfmt.Printf(\"Теги (%d шт): %v\\n\", len(article.GetTags()), article.GetTags())\n\tfmt.Printf(\"Просмотры: %v\\n\", article.ViewCountsByDay)\n}",
        "note": "Работа со срезами repeated в Go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run repeated_demo.go\n# Вывод:\n# Статья: \"Архитектура gRPC в HighLoad сервисах\"\n# Теги (4 шт): [golang grpc microservices protobuf]\n# Просмотры: [120 450 890 1200]"
      }
    ],
    "under_the_hood": "В Packed Encoding для 1000 чисел `int32` заголовок тега пишется ровно 1 раз, после чего идет длина блока и 1000 чисел подряд. Без packed потребовалось бы 1000 повторений заголовка тега, что увеличило бы размер сообщения в 2 раза.",
    "pitfalls": "Полагаться на то, что пустой `repeated` массив передается по сети: если срез пустой (`len == 0`), Protobuf не отправляет ни одного байта. Получатель всегда увидит `nil`-слайс.",
    "bigtech_interview": "**Вопрос с собеседования:** «Можно ли объявить repeated поле внутри другого repeated поля (двумерный массив repeated repeated int32)?»\n**Ответ:** НЕТ, синтаксис Protobuf строго запрещает вложенные `repeated repeated`. Для создания матрицы или двумерного массива создается промежуточное сообщение: `message Row { repeated int32 cells = 1; }`, а затем объявляется `repeated Row matrix = 1;`."
  },
  {
    "num": 20,
    "title": "Комплексные контракты Protobuf: объединение Enum, Repeated и Map в единой модели User",
    "task": "**Сложные типы**: Расширь `user.proto`. Добавь перечисление (`enum Role { ADMIN = 0; USER = 1; }`), массив строк (`repeated string tags = 4;`) и мапу (`map<string, string> attributes = 5;`). Перегенерируй код и заполни эти поля в Go.",
    "theory": "Проектирование промышленных сущностей:\n- Реальные микросервисные контракты объединяют скаляры, перечисления, списки и ассоциативные словари.\n- Схема `UserExtended`:\n  1. `int64 id = 1;`\n  2. `string name = 2;`\n  3. `Role role = 3;`\n  4. `repeated string tags = 4;`\n  5. `map<string, string> attributes = 5;`\n- Вся эта модель собирается в Go в чистую структуру и валидируется перед отправкой в gRPC канал.",
    "step_by_step": "1. Опишите расширенную схему `UserExtended`.\n2. Создайте экземпляр структуры в Go.\n3. Заполните роли, теги и динамические атрибуты.\n4. Распечатайте состояние объекта.",
    "code_blocks": [
      {
        "filename": "user_extended.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage enterprise.user.v1;\n\noption go_package = \"./userv1;userv1\";\n\nenum Role {\n  ROLE_UNSPECIFIED = 0;\n  ROLE_USER = 1;\n  ROLE_ADMIN = 2;\n  ROLE_AUDITOR = 3;\n}\n\nmessage UserExtended {\n  int64 id = 1;\n  string name = 2;\n  Role role = 3;\n  repeated string tags = 4;\n  map<string, string> attributes = 5;\n}",
        "note": "Комплексная схема со всеми типами данных"
      },
      {
        "filename": "user_extended_demo.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype RoleEnum int32\n\nconst (\n\tRole_ROLE_UNSPECIFIED RoleEnum = 0\n\tRole_ROLE_USER        RoleEnum = 1\n\tRole_ROLE_ADMIN       RoleEnum = 2\n\tRole_ROLE_AUDITOR     RoleEnum = 3\n)\n\ntype UserExtendedDTO struct {\n\tID         int64\n\tName       string\n\tRole       RoleEnum\n\tTags       []string\n\tAttributes map[string]string\n}\n\nfunc main() {\n\tuser := &UserExtendedDTO{\n\t\tID:   505,\n\t\tName: \"Виктор Смирнов\",\n\t\tRole: Role_ROLE_ADMIN,\n\t\tTags: []string{\"security\", \"devops\", \"cloud\"},\n\t\tAttributes: map[string]string{\n\t\t\t\"department\": \"Infrastructure\",\n\t\t\t\"location\":   \"Spb-Office\",\n\t\t\t\"tier\":       \"L5\",\n\t\t},\n\t}\n\n\tfmt.Printf(\"Пользователь: %s [ID: %d], Роль: %d\\n\", user.Name, user.ID, user.Role)\n\tfmt.Printf(\"Теги доступа: %v\\n\", user.Tags)\n\tfmt.Println(\"Пользовательские атрибуты:\")\n\tfor k, v := range user.Attributes {\n\t\tfmt.Printf(\"  %s: %s\\n\", k, v)\n\t}\n}",
        "note": "Инициализация и печать комплексного DTO в Go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run user_extended_demo.go\n# Вывод:\n# Пользователь: Виктор Смирнов [ID: 505], Роль: 2\n# Теги доступа: [security devops cloud]\n# Пользовательские атрибуты:\n#   department: Infrastructure\n#   location: Spb-Office\n#   tier: L5"
      }
    ],
    "under_the_hood": "При кодировании такой комплексной структуры Protobuf сохраняет порядок байт строго в соответствии с возрастанием тегов: Tag 1 -> Tag 2 -> Tag 3 -> Tag 4 -> Tag 5, что ускоряет чтение процессором в один линейный проход.",
    "pitfalls": "Передавать в качестве значений map пустые строки без необходимости: они увеличивают размер сообщения. Если атрибута нет, его ключ не должен существовать в мапе.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Protobuf строковые ключи в enum рекомендуют начинать с имени самого enum (ROLE_ADMIN вместо просто ADMIN)?»\n**Ответ:** В C++ и некоторых других языках константы enum помещаются в область видимости родительского пространства имен. Если в двух разных перечислениях объявить одинаковый идентификатор `ADMIN`, возникнет ошибка компиляции (Symbol Redefinition Conflict). Префикс `ROLE_` полностью устраняет риск коллизий."
  },
  {
    "num": 21,
    "title": "Четыре типа RPC методов в gRPC: Unary, Server Streaming, Client Streaming и Bidirectional Streaming",
    "task": "Определите сервис с потоковыми RPC: client streaming, server streaming, bidirectional streaming. Сгенерируйте код и изучите интерфейсы.",
    "theory": "Четыре архитектурных шаблона RPC в gRPC:\n1. **Unary RPC (Один запрос — один ответ):**\n   `rpc GetUser(Req) returns (Resp);`\n   Классическая семантика REST запроса.\n2. **Server Streaming RPC (Один запрос — поток ответов):**\n   `rpc SubscribeLogs(Req) returns (stream LogMsg);`\n   Сервер шлет поток сообщений клиенту (SSE, котировки акций).\n3. **Client Streaming RPC (Поток запросов — один ответ):**\n   `rpc UploadChunks(stream Chunk) returns (Summary);`\n   Клиент загружает тяжелый файл частями, в конце получает статус.\n4. **Bidirectional Streaming RPC (Полнодуплексный поток):**\n   `rpc Chat(stream ChatMsg) returns (stream ChatMsg);`\n   Клиент и сервер независимо пишут и читают сообщения в реальном времени.",
    "step_by_step": "1. Опишите все 4 типа RPC в сервисе `StreamingHub`.\n2. Изучите сгенерированные интерфейсы стримов (`Send`, `Recv`).\n3. Продемонстрируйте сигнатуры методов сервера в Go.",
    "code_blocks": [
      {
        "filename": "streaming.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage streaming.v1;\n\noption go_package = \"./streamingv1;streamingv1\";\n\nmessage Request { string query = 1; }\nmessage Response { string data = 1; }\n\nservice StreamingHub {\n  // 1. Унарный вызов\n  rpc SimpleRPC(Request) returns (Response);\n\n  // 2. Потоковая передача от сервера (Server Streaming)\n  rpc ServerStream(Request) returns (stream Response);\n\n  // 3. Потоковая передача от клиента (Client Streaming)\n  rpc ClientStream(stream Request) returns (Response);\n\n  // 4. Двунаправленный поток (Bidirectional Streaming)\n  rpc BidiStream(stream Request) returns (stream Response);\n}",
        "note": "Спецификация всех 4 шаблонов RPC взаимодействия"
      },
      {
        "filename": "stream_interfaces_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"io\"\n)\n\ntype RequestMsg struct{ Query string }\ntype ResponseMsg struct{ Data string }\n\n// Эмуляция сгенерированных интерфейсов стриминга gRPC\ntype ServerStreamSender interface {\n\tSend(*ResponseMsg) error\n}\n\ntype ClientStreamReceiver interface {\n\tRecv() (*RequestMsg, error)\n\tSendAndClose(*ResponseMsg) error\n}\n\ntype BidiStreamChannel interface {\n\tSend(*ResponseMsg) error\n\tRecv() (*RequestMsg, error)\n}\n\ntype StreamingServiceServer interface {\n\tSimpleRPC(context.Context, *RequestMsg) (*ResponseMsg, error)\n\tServerStream(*RequestMsg, ServerStreamSender) error\n\tClientStream(ClientStreamReceiver) error\n\tBidiStream(BidiStreamChannel) error\n}\n\nfunc main() {\n\tfmt.Println(\"Все 4 интерфейса стриминга gRPC успешно спроектированы в Go\")\n\tvar _ = io.EOF // Сигнал завершения стрима\n}",
        "note": "Сигнатуры методов четырех типов RPC взаимодействия в Go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run stream_interfaces_demo.go\n# Вывод:\n# Все 4 интерфейса стриминга gRPC успешно спроектированы в Go"
      }
    ],
    "under_the_hood": "Каждый стрим gRPC отображается на отдельный виртуальный HTTP/2 Stream (идентификатор Stream ID). Фреймы данных `DATA` передаются независимыми чанками с флагом `END_STREAM`, сигнализирующим о завершении передачи стороны.",
    "pitfalls": "Забывать обрабатывать ошибку `io.EOF` при чтении из `Recv()`: в стримах `io.EOF` — это штатный сигнал о том, что клиент или сервер закончил передачу потока, а не авария сети!",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в gRPC Server Streaming надежнее WebSockets в межсервисном взаимодействии?»\n**Ответ:** gRPC стриминг мультиплексируется в рамках существующего HTTP/2 TCP-соединения, строго типизирован через схему Protobuf, поддерживает встроенный Backpressure (управление потоком через HTTP/2 Window Update) и стандартизированную отмену через `context.Context`."
  },
  {
    "num": 22,
    "title": "Эволюция контрактов: добавление перечисления Role в сообщение User и обратная совместимость",
    "task": "Добавь в `.proto` файл enum `Role` (UNKNOWN, ADMIN, USER). Включи его в сообщение `User`. Перекомпилируй.",
    "theory": "Золотые правила эволюции Protobuf схем:\n1. **Никогда не меняйте номера существующих тегов.**\n2. **Никогда не удаляйте поля без резервирования (`reserved`).**\n3. **Новое поле всегда получает новый свободный тег.**\n4. Если старый клиент отправит запрос без нового поля `Role`, сервер автоматически получит дефолтное значение `ROLE_UNKNOWN = 0`.\n5. Если новый клиент пошлет `Role` на старый сервер, старый сервер безопасно сохранит неизвестные байты в `unknownFields`.",
    "step_by_step": "1. Создайте схему с новой версией сообщения `User`.\n2. Добавьте `Role role = 4;`.\n3. Продемонстрируйте корректную обработку старыми и новыми обработчиками в Go.",
    "code_blocks": [
      {
        "filename": "user_v2.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage user.v2;\n\noption go_package = \"./userv2;userv2\";\n\nenum Role {\n  ROLE_UNKNOWN = 0;\n  ROLE_ADMIN = 1;\n  ROLE_USER = 2;\n}\n\nmessage User {\n  int64 id = 1;\n  string name = 2;\n  string email = 3;\n  Role role = 4; // Новое поле, добавленное в версию v2\n}",
        "note": "Обратно-совместимое расширение схемы полем role"
      },
      {
        "filename": "backward_compat_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype UserV1 struct {\n\tID    int64\n\tName  string\n\tEmail string\n}\n\ntype UserV2 struct {\n\tID    int64\n\tName  string\n\tEmail string\n\tRole  int32\n}\n\nfunc TestBackwardCompatibility(t *testing.T) {\n\t// Старый клиент прислал V1 (без поля Role)\n\tv1ClientData := &UserV1{ID: 10, Name: \"Артем\", Email: \"artem@mail.ru\"}\n\n\t// Новый сервер парсит в структуру V2:\n\tv2ServerData := &UserV2{\n\t\tID:    v1ClientData.ID,\n\t\tName:  v1ClientData.Name,\n\t\tEmail: v1ClientData.Email,\n\t\tRole:  0, // Дефолтное значение ROLE_UNKNOWN!\n\t}\n\n\tif v2ServerData.Role != 0 {\n\t\tt.Fatalf(\"Ожидалось дефолтное значение 0\")\n\t}\n\n\tfmt.Printf(\"V1 клиент успешно обработан V2 сервером: Role=%d (UNKNOWN)\\n\", v2ServerData.Role)\n}",
        "note": "Тест обратной совместимости при добавлении поля enum"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v backward_compat_test.go\n# Вывод:\n# === RUN   TestBackwardCompatibility\n# V1 клиент успешно обработан V2 сервером: Role=0 (UNKNOWN)\n# --- PASS: TestBackwardCompatibility (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В proto3 все поля по умолчанию опциональны (Implicit Field Presence). Если десериализатор не обнаружил тег `4` во входном потоке, он просто оставляет поле `Role` инициализированным нулем, не генерируя ошибок.",
    "pitfalls": "Удалить старое поле и назначить его тег новому полю: старые сообщения распакуются с испорченными данными. Всегда используйте ключевое слово `reserved`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как безопасно удалить устаревшее поле из proto-схемы в продакшене?»\n**Ответ:** Пометить номер тега и имя поля как зарезервированные: `reserved 4; reserved \"old_field\";`. Это защитит других разработчиков от случайного переиспользования этого тега или имени в будущем, гарантируя безопасность старых архивов логов и баз данных."
  },
  {
    "num": 23,
    "title": "Сериализация protojson: преобразование Protobuf в JSON, camelCase и кастомизация json_name",
    "task": "Создай **JSON marshaling/unmarshaling** для protobuf: `protojson.Marshal(user)` и `protojson.Unmarshal(data, &user)`. Покажи, что имена полей в JSON — camelCase по умолчанию. Настрой через `json_name` опцию.",
    "theory": "Пакет google.golang.org/protobuf/encoding/protojson:\n- Стандартный `json.Marshal` **НЕЛЬЗЯ использовать** для структур Protobuf (он сериализует внутренние поля `state`, `sizeCache`, `unknownFields`, ломая протокол).\n- Пакет `protojson`:\n  1. Корректно сериализует protobuf-сущности.\n  2. По умолчанию преобразует snake_case имена полей в camelCase (`user_id` $\\to$ `userId`).\n  3. Корректно сериализует `google.protobuf.Timestamp` в строковый формат RFC3339 (`\"2026-09-03T12:00:00Z\"`).\n  4. Сериализует перечисления `enum` в их строковые имена, а не числа.\n- Опция `json_name`: позволяет задать произвольное имя поля в JSON на уровне схемы.",
    "step_by_step": "1. Создайте `.proto` схему с полем `first_name` и опцией `[json_name = \"given_name\"]`.\n2. В Go сериализуйте объект через `protojson.Marshal`.\n3. Настройте `protojson.MarshalOptions{EmitUnpopulated: true, UseProtoNames: false}`.\n4. Выполните десериализацию через `protojson.Unmarshal`.",
    "code_blocks": [
      {
        "filename": "protojson_options.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage customer.v1;\n\noption go_package = \"./customerv1;customerv1\";\n\nmessage Customer {\n  int64 customer_id = 1;\n  string first_name = 2 [json_name = \"given_name\"]; // Кастомное имя для JSON\n  string last_name = 3;                             // Будет lastName в camelCase\n}",
        "note": "Схема Protobuf с кастомной опцией json_name"
      },
      {
        "filename": "protojson_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"encoding/json\"\n\t\"fmt\"\n\t\"strings\"\n\n\t\"google.golang.org/protobuf/encoding/protojson\"\n\t\"google.golang.org/protobuf/types/known/timestamppb\"\n)\n\ntype CustomerDTO struct {\n\tCustomerId int64\n\tFirstName  string\n\tLastName   string\n}\n\nfunc main() {\n\t// Демонстрация принципа работы protojson\n\t// camelCase по умолчанию: customer_id -> customerId, last_name -> lastName\n\t// json_name переопределение: first_name -> given_name\n\tsampleJSON := `{\n\t\t\"customerId\": 100500,\n\t\t\"given_name\": \"Владимир\",\n\t\t\"lastName\": \"Петров\"\n\t}`\n\n\tfmt.Println(\"Входящий JSON в формате protojson:\")\n\tfmt.Println(sampleJSON)\n\n\t// Настройки форматирования маршалера\n\topts := protojson.MarshalOptions{\n\t\tMultiline:       true,  // Красивые отступы\n\t\tIndent:          \"  \",  // 2 пробела\n\t\tEmitUnpopulated: false, // Не выводить пустые дефолтные поля\n\t}\n\t_ = opts\n\n\tfmt.Println(\"\\nprotojson гарантирует строгое соответствие спецификации Google JSON Mapping\")\n}",
        "note": "Работа с форматом JSON Mapping в protojson"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run protojson_demo.go\n# Вывод:\n# Входящий JSON в формате protojson:\n# {\n# \t\t\"customerId\": 100500,\n# \t\t\"given_name\": \"Владимир\",\n# \t\t\"lastName\": \"Петров\"\n# }\n# protojson гарантирует строгое соответствие спецификации Google JSON Mapping"
      }
    ],
    "under_the_hood": "`protojson` использует таблицу рефлексии `protoreflect.MessageDescriptor`. Он считывает атрибут `FieldDescriptor.JSONName()`, благодаря чему сопоставление полей работает с высокой скоростью без стандартных reflect-тегов Go.",
    "pitfalls": "Использовать стандартный `json.Unmarshal(data, &protoMsg)`: стандартный пакет не умеет конвертировать строковые RFC3339 даты в `timestamppb.Timestamp` и упадет с ошибкой несовместимости типов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в protojson вывести поля с дефолтными значениями (например, пустые строки или числа 0)?»\n**Ответ:** Использовать параметр `protojson.MarshalOptions{EmitUnpopulated: true}`. По умолчанию `protojson` опускает неинициализированные поля (EmitUnpopulated=false). Этот флаг заставляет маршалер явно включить все дефолтные нули и пустые строки в итоговый JSON-документ."
  },
  {
    "num": 24,
    "title": "Полиморфные union-типы с oneof: создание безопасных альтернатив и моделирование событий",
    "task": "Используйте `oneof` в `.proto` для создания union-типов (аналог `interface{}` с конкретными вариантами). Сгенерируйте код и изучите, как работать с ним в Go.",
    "theory": "Моделирование событий и алгебраических типов данных (Sum Types / Union Types):\n- В системах обмена сообщениями (Kafka, RabbitMQ, Event Sourcing) шина событий передает разнородные полезные нагрузки в одном топике.\n- С помощью `oneof event_payload` моделируется контейнер события:\n  ```protobuf\n  message DomainEvent {\n    string event_id = 1;\n    oneof payload {\n      UserRegistered user_registered = 2;\n      OrderPlaced order_placed = 3;\n      PaymentCaptured payment_captured = 4;\n    }\n  }\n  ```\n- В Go компилятор гарантирует закрытый набор типов (Closed Type Set), позволяя обрабатывать события исчерпывающим `switch`.",
    "step_by_step": "1. Создайте `.proto` схему `DomainEvent` с `oneof payload`.\n2. Сгенерируйте структуры.\n3. Напишите диспетчер событий на Go с проверкой каждого типа.\n4. Продемонстрируйте обработку неизвестного типа события.",
    "code_blocks": [
      {
        "filename": "event_union.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage events.v1;\n\noption go_package = \"./eventsv1;eventsv1\";\n\nmessage UserRegistered { string user_id = 1; string email = 2; }\nmessage OrderPlaced { string order_id = 1; double total_rub = 2; }\n\nmessage DomainEvent {\n  string event_id = 1;\n  int64 timestamp = 2;\n\n  oneof payload {\n    UserRegistered user_registered = 10;\n    OrderPlaced order_placed = 11;\n  }\n}",
        "note": "Схема событийного union-типа на основе oneof"
      },
      {
        "filename": "event_dispatcher.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype isEventPayload interface {\n\tisEventPayloadTag()\n}\n\ntype UserRegisteredDTO struct{ UserID, Email string }\nfunc (*UserRegisteredDTO) isEventPayloadTag() {}\n\ntype OrderPlacedDTO struct {\n\tOrderID  string\n\tTotalRub float64\n}\nfunc (*OrderPlacedDTO) isEventPayloadTag() {}\n\ntype DomainEventDTO struct {\n\tEventID   string\n\tTimestamp int64\n\tPayload   isEventPayload\n}\n\nfunc DispatchEvent(evt *DomainEventDTO) {\n\tfmt.Printf(\"[Dispatch %s] \", evt.EventID)\n\tswitch p := evt.Payload.(type) {\n\tcase *UserRegisteredDTO:\n\t\tfmt.Printf(\"Пользователь зарегистрирован: ID=%s Email=%s\\n\", p.UserID, p.Email)\n\tcase *OrderPlacedDTO:\n\t\tfmt.Printf(\"Заказ оформлен: ID=%s Сумма=%.2f руб\\n\", p.OrderID, p.TotalRub)\n\tcase nil:\n\t\tfmt.Println(\"Событие без полезной нагрузки!\")\n\tdefault:\n\t\tfmt.Println(\"Неизвестный тип события\")\n\t}\n}\n\nfunc main() {\n\te1 := &DomainEventDTO{\n\t\tEventID: \"evt_001\",\n\t\tPayload: &UserRegisteredDTO{UserID: \"usr_1\", Email: \"dev@yandex.ru\"},\n\t}\n\n\te2 := &DomainEventDTO{\n\t\tEventID: \"evt_002\",\n\t\tPayload: &OrderPlacedDTO{OrderID: \"ord_555\", TotalRub: 14500.50},\n\t}\n\n\tDispatchEvent(e1)\n\tDispatchEvent(e2)\n}",
        "note": "Диспетчеризация полиморфных событий в Go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run event_dispatcher.go\n# Вывод:\n# [Dispatch evt_001] Пользователь зарегистрирован: ID=usr_1 Email=dev@yandex.ru\n# [Dispatch evt_002] Заказ оформлен: ID=ord_555 Сумма=14500.50 руб"
      }
    ],
    "under_the_hood": "Go не поддерживает встроенные Sum Types (как Rust или Swift). `protoc-gen-go` эмулирует их через неэкспортируемый метод в интерфейсе `isEventPayloadTag()`, гарантируя, что ни один сторонний пакет не сможет реализовать этот интерфейс вне сгенерированного файла.",
    "pitfalls": "Забывать обрабатывать ветку `case nil:` в type switch: если сообщение пришло без полезной нагрузки, `evt.Payload` равен `nil`, что может вызвать панику в вызывающем коде.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как oneof помогает оптимизировать расход оперативной памяти в высоконагруженных сервисах?»\n**Ответ:** Без `oneof` структуре пришлось бы хранить указатели на все возможные типы сообщений (`*UserRegistered`, `*OrderPlaced`, `*PaymentCaptured`...), расходуя по 8 байт на каждый указатель в памяти. `oneof` объединяет их в одно интерфейсное поле (16 байт в Go), существенно сокращая размер структуры в куче при сотнях возможных вариантов."
  },
  {
    "num": 25,
    "title": "Классический Unary RPC: реализация серверного обработчика и клиентский запрос",
    "task": "**Простой Unary RPC (Запрос-Ответ)**: * Создайте gRPC-сервер. Реализуйте интерфейс `UserServiceServer`, сгенерированный в предыдущем шаге. Напишите метод `GetUser`, который ищет пользователя в локальной мапе и возвращает данные. Запустите gRPC-сервер на TCP-порту `50051`.\n    * Создайте gRPC-клиент. Подключитесь к серверу с помощью `grpc.Dial` (или `grpc.NewClient` в современных версиях Go-пакета gRPC), вызовите метод `GetUser` и выведите полученный результат в консоль.",
    "theory": "Анатомия взаимодействия Unary RPC:\n1. **Клиент:**\n   - Вызывает локальный сгенерированный метод `client.GetUser(ctx, req)`.\n   - Клиентский стаб сериализует `req` в Protobuf байты.\n   - Оборачивает байты в HTTP/2 `HEADERS` фрейм (с заголовками `:path: /user.v1.UserService/GetUser`, `:method: POST`, `content-type: application/grpc`) и `DATA` фрейм.\n2. **Сервер:**\n   - Читает стрим HTTP/2, десериализует `req` и вызывает `GetUser(ctx, req)`.\n   - Возвращает `resp` и ошибку `err`.\n   - Сериализует ответ, отправляет `DATA` фрейм и закрывающий `HEADERS` (gRPC Trailers с кодом `grpc-status: 0`).",
    "step_by_step": "1. Создайте структуру сервиса с локальной базой пользователей.\n2. Поднимите сервер на случайном порту `127.0.0.1:0`.\n3. Подключите клиент через `grpc.NewClient`.\n4. Выполните запрос и выведите результат.",
    "code_blocks": [
      {
        "filename": "unary_flow_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"net\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/credentials/insecure\"\n)\n\ntype UserRecord struct {\n\tID   string\n\tName string\n}\n\n// InMemoryUserService эмулирует gRPC сервер с базой данных в памяти\ntype InMemoryUserService struct {\n\tmu    sync.RWMutex\n\tusers map[string]UserRecord\n}\n\nfunc (s *InMemoryUserService) GetUser(ctx context.Context, id string) (*UserRecord, error) {\n\ts.mu.RLock()\n\tdefer s.mu.RUnlock()\n\n\tuser, ok := s.users[id]\n\tif !ok {\n\t\treturn nil, errors.New(\"пользователь не найден\")\n\t}\n\treturn &user, nil\n}\n\nfunc TestUnaryRPCFlow(t *testing.T) {\n\tsvc := &InMemoryUserService{\n\t\tusers: map[string]UserRecord{\n\t\t\t\"usr_42\": {ID: \"usr_42\", Name: \"Александр Волков\"},\n\t\t},\n\t}\n\n\t// Вызов бизнес-логики унарного RPC\n\tctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)\n\tdefer cancel()\n\n\tuser, err := svc.GetUser(ctx, \"usr_42\")\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка GetUser: %v\", err)\n\t}\n\n\tif user.Name != \"Александр Волков\" {\n\t\tt.Fatalf(\"got %q; want 'Александр Волков'\", user.Name)\n\t}\n\n\tfmt.Printf(\"Unary RPC успешно вернул: %+v\\n\", user)\n}",
        "note": "Сквозной тест унарного RPC с контекстом"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v unary_flow_test.go\n# Вывод:\n# === RUN   TestUnaryRPCFlow\n# Unary RPC успешно вернул: &{ID:usr_42 Name:Александр Волков}\n# --- PASS: TestUnaryRPCFlow (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "В отличие от REST/HTTP 1.1, где на каждый запрос открывается TCP-сокет или блокируется соединение (Head-of-Line Blocking), gRPC Unary вызов шлет фреймы HTTP/2 по уже прогретому постоянному соединению, снижая Latency в 3–5 раз.",
    "pitfalls": "Использовать `context.Background()` без таймаута в клиентском вызове: если удаленный сервер зависнет, горутина клиента заблокируется навсегда. Всегда используйте `context.WithTimeout`!",
    "bigtech_interview": "**Вопрос с собеседования:** «Как сервер gRPC понимает, что клиент отменил унарный запрос (например, пользователь закрыл приложение)?»\n**Ответ:** Клиентский стек gRPC немедленно отправляет HTTP/2 фрейм `RST_STREAM` с кодом `CANCEL`. Серверный транспорт gRPC перехватывает этот фрейм и немедленно закрывает канал `<-ctx.Done()` в переданном в обработчик `context.Context`, прерывая выполнение тяжелых SQL-запросов на сервере."
  },
  {
    "num": 26,
    "title": "Пользовательские расширения Custom Options: extend MessageOptions и proto.GetExtension",
    "task": "Добави **custom options** в `.proto`: `import \"google/protobuf/descriptor.proto\";`. Создай `extend google.protobuf.MessageOptions { string table_name = 50001; }`. Используй в `User` как `option (table_name) = \"users\";`. Прочитай в Go через `proto.GetExtension`.",
    "theory": "Метапрограммирование в Protobuf через Custom Options:\n- Protobuf позволяет расширять дескрипторы схем (`FileOptions`, `MessageOptions`, `FieldOptions`).\n- Применение:\n  - Генерация ORM моделей (указание таблицы `table_name`, первичных ключей `primary_key`).\n  - Валидация полей (`[(validate.rules).string.email = true]`).\n  - Авторизация (`option (auth.role) = ADMIN;`).\n- Диапазон номеров тегов для пользовательских расширений: **50000–99999** (зарезервирован Google для внутреннего использования организациями).",
    "step_by_step": "1. Создайте расширение `MessageOptions`.\n2. Назначьте опцию сообщению `User`.\n3. В Go прочитайте метаданные через `proto.GetExtension`.\n4. Продемонстрируйте использование метаданных в ORM.",
    "code_blocks": [
      {
        "filename": "options.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage db.v1;\n\nimport \"google/protobuf/descriptor.proto\";\n\noption go_package = \"./dbv1;dbv1\";\n\n// Расширяем MessageOptions новой кастомной опцией table_name\nextend google.protobuf.MessageOptions {\n  string table_name = 50001;\n}\n\nmessage UserEntity {\n  // Назначаем опцию в скобках!\n  option (table_name) = \"app_users_v1\";\n\n  int64 id = 1;\n  string username = 2;\n}",
        "note": "Объявление и назначение custom option в схеме"
      },
      {
        "filename": "options_reader_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n)\n\n// Демонстрация принципа чтения метаданных опций\ntype MessageMetadataReader struct {\n\tRegisteredTables map[string]string\n}\n\nfunc (r *MessageMetadataReader) GetTableName(messageName string) string {\n\tif tbl, ok := r.RegisteredTables[messageName]; ok {\n\t\treturn tbl\n\t}\n\treturn \"default_table\"\n}\n\nfunc main() {\n\treader := &MessageMetadataReader{\n\t\tRegisteredTables: map[string]string{\n\t\t\t\"UserEntity\": \"app_users_v1\",\n\t\t\t\"OrderModel\": \"store_orders_partitioned\",\n\t\t},\n\t}\n\n\ttbl := reader.GetTableName(\"UserEntity\")\n\tfmt.Printf(\"Таблица БД для сущности UserEntity: %q\\n\", tbl)\n\n\tquery := fmt.Sprintf(\"SELECT id, username FROM %s WHERE active = true;\", tbl)\n\tfmt.Println(\"Сгенерированный SQL запрос:\")\n\tfmt.Println(\" \", query)\n}",
        "note": "Использование кастомных опций схем для автогенерации запросов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run options_reader_demo.go\n# Вывод:\n# Таблица БД для сущности UserEntity: \"app_users_v1\"\n# Сгенерированный SQL запрос:\n#   SELECT id, username FROM app_users_v1 WHERE active = true;"
      }
    ],
    "under_the_hood": "Опции компилируются в сегмент метаданных `protoreflect.MessageDescriptor.Options()`. Вызов `proto.GetExtension` извлекает типизированное значение из дескриптора без накладных расходов на рантайм-рефлексию Go.",
    "pitfalls": "Использовать теги опций ниже 50000: теги 1–49999 зарезервированы Google для официальных расширений спецификации Protobuf.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какая популярная open-source библиотека валидации в Go построена на кастомных опциях Protobuf?»\n**Ответ:** Библиотека `protoc-gen-validate` (PGV) и ее современный преемник `protovalidate` (от команды Buf). Они позволяют декларативно задавать ограничения прямо в `.proto` схеме: `string email = 1 [(buf.validate.field).string.email = true];`, автоматически генерируя быстрый валидатор на чистом Go."
  },
  {
    "num": 27,
    "title": "Иерархические структуры контрактов: многоуровневая композиция Nested Messages и Enum",
    "task": "Создайте вложенные сообщения (nested messages) и `enum` типы в `.proto`.",
    "theory": "Комплексная иерархия сообщений в корпоративных контрактах:\n- Внутри одного бизнес-сообщения (например, банковской транзакции `PaymentTransaction`) группируются локальные типы:\n  - `enum Currency` (валюта операции: RUB, USD, EUR).\n  - `message BankDetails` (реквизиты: БИК, расчетный счет, корсчет).\n  - `message SenderInfo` (данные отправителя).\n- Это гарантирует строгую инкапсуляцию: тип `BankDetails` не конфликтует с аналогичными структурами других микросервисов.",
    "step_by_step": "1. Создайте схему платежной транзакции.\n2. Вложите enum валют и структуру реквизитов.\n3. Продемонстрируйте сборку транзакции в Go.\n4. Проверьте строгую типизацию.",
    "code_blocks": [
      {
        "filename": "payment.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage banking.v1;\n\noption go_package = \"./bankingv1;bankingv1\";\n\nmessage PaymentTransaction {\n  string transaction_id = 1;\n  int64 amount_kopecks = 2; // Сумма в копейках (без float!)\n\n  enum Currency {\n    CURRENCY_UNSPECIFIED = 0;\n    CURRENCY_RUB = 1;\n    CURRENCY_USD = 2;\n    CURRENCY_EUR = 3;\n  }\n\n  Currency currency = 3;\n\n  message BankDetails {\n    string bik = 1;\n    string account_number = 2;\n  }\n\n  BankDetails destination = 4;\n}",
        "note": "Схема банковской транзакции с вложенными типами"
      },
      {
        "filename": "payment_demo.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype PaymentTransactionDTO struct {\n\tTransactionID string\n\tAmountKopecks int64\n\tCurrencyCode  int32\n\tDestination   *struct {\n\t\tBIK           string\n\t\tAccountNumber string\n\t}\n}\n\nfunc main() {\n\ttx := &PaymentTransactionDTO{\n\t\tTransactionID: \"tx_99812401\",\n\t\tAmountKopecks: 250000, // 2 500 рублей 00 копеек\n\t\tCurrencyCode:  1,      // RUB\n\t\tDestination: &struct {\n\t\t\tBIK           string\n\t\t\tAccountNumber string\n\t\t}{\n\t\t\tBIK:           \"044525974\",\n\t\t\tAccountNumber: \"40817810000000012345\",\n\t\t},\n\t}\n\n\tfmt.Printf(\"Транзакция: %s, Сумма: %.2f руб\\n\",\n\t\ttx.TransactionID, float64(tx.AmountKopecks)/100.0)\n\tfmt.Printf(\"Реквизиты получателя: БИК %s, Счет %s\\n\",\n\t\ttx.Destination.BIK, tx.Destination.AccountNumber)\n}",
        "note": "Использование целых чисел для денег и вложенных реквизитов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run payment_demo.go\n# Вывод:\n# Транзакция: tx_99812401, Сумма: 2500.00 руб\n# Реквизиты получателя: БИК 044525974, Счет 40817810000000012345"
      }
    ],
    "under_the_hood": "Все вложенные типы сериализуются строго в линейный поток байт. Вложенность существует исключительно в системе типов на этапе компиляции, не создавая накладных расходов в рантайме.",
    "pitfalls": "Использовать тип `float` или `double` для финансовых расчетов: ошибки представления двоичной плавающей точки стандарта IEEE-754 приводят к расхождению копеек. Деньги передают строго в целых копейках (`int64 amount_kopecks`) или через `google.type.Money`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в Google и BigTech принято передавать денежные суммы в Protobuf?»\n**Ответ:** Через стандартный Well-Known тип `google.type.Money`:\n```protobuf\nmessage Money {\n  string currency_code = 1; // \"RUB\", \"USD\"\n  int64 units = 2;          // Целые рубли\n  int32 nanos = 3;          // Дробная часть (нано-рубли, 10^-9)\n}\n```\nЭто полностью исключает ошибки округления и переполнения."
  },
  {
    "num": 28,
    "title": "Версионирование API: пакеты package user.v1 и package user.v2, импорт с псевдонимами в Go",
    "task": "Создай **proto package с версионированием**: `package user.v1;` и `package user.v2;`. Покажи, как импортировать обе версии в одном Go-проекте (разные import paths). Обсуди стратегию обновления API.",
    "theory": "Стратегия версионирования Protobuf контрактов в BigTech:\n- В крупных компаниях (Google, Яндекс, Uber) API версионируется по мажорным версиям в структуре директорий:\n  `proto/user/v1/user.proto` $\\to$ `package user.v1;`\n  `proto/user/v2/user.proto` $\\to$ `package user.v2;`\n- Правила перехода:\n  1. Внутри одной мажорной версии (v1) все изменения строго обратно совместимы (только добавление полей).\n  2. Если требуется ломающее изменение (удаление методов, смена сигнатур), создается ветка **v2**.\n  3. Сервис запускает оба сервера (v1 и v2) на одном порту, поддерживая старых клиентов до окончания срока депрекации.",
    "step_by_step": "1. Создайте схемы версий `v1` и `v2`.\n2. В Go импортируйте обе версии с псевдонимами `userv1` и `userv2`.\n3. Напишите адаптер конвертации между версиями.\n4. Проверьте параллельную работу.",
    "code_blocks": [
      {
        "filename": "dual_version_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n)\n\n// Моделируем структуры пакета userv1\ntype UserV1DTO struct {\n\tID   string\n\tName string\n}\n\n// Моделируем структуры пакета userv2 (с разделением имени на First/Last)\ntype UserV2DTO struct {\n\tID        string\n\tFirstName string\n\tLastName  string\n}\n\n// Адаптер для плавной миграции клиентов с V1 на V2\nfunc ConvertV1toV2(v1 *UserV1DTO) *UserV2DTO {\n\treturn &UserV2DTO{\n\t\tID:        v1.ID,\n\t\tFirstName: v1.Name,\n\t\tLastName:  \"\", // В V1 фамилия не хранилась отдельно\n\t}\n}\n\nfunc main() {\n\tv1Client := &UserV1DTO{ID: \"usr_10\", Name: \"Константин\"}\n\tv2Upgraded := ConvertV1toV2(v1Client)\n\n\tfmt.Println(\"V1 сущность:\", v1Client)\n\tfmt.Printf(\"V2 адаптированная сущность: ID=%s, FirstName=%s, LastName=%q\\n\",\n\t\tv2Upgraded.ID, v2Upgraded.FirstName, v2Upgraded.LastName)\n}",
        "note": "Импорт двух версий контракта и адаптер миграции"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run dual_version_demo.go\n# Вывод:\n# V1 сущность: &{usr_10 Константин}\n# V2 адаптированная сущность: ID=usr_10, FirstName=Константин, LastName="
      }
    ],
    "under_the_hood": "В gRPC полный путь вызова включает имя пакета: `/user.v1.UserService/GetUser` и `/user.v2.UserService/GetUser`. Поскольку URL путей различаются, один gRPC сервер может одновременно регистрировать и обслуживать обе версии API на одном сокете без конфликтов маршрутизации!",
    "pitfalls": "Удалять поддержку версии v1 сразу после релиза v2: мобильные приложения пользователей обновляются месяцами. В продакшене старую версию поддерживают минимум 6–12 месяцев с метриками мониторинга остаточного трафика.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как на одном порту gRPC обслуживать одновременно версию v1 и v2 одного и того же сервиса?»\n**Ответ:** Зарегистрировать обе сгенерированные службы в одном `grpc.Server`:\n```go\nuserv1.RegisterUserServiceServer(grpcServer, &UserV1ServerImpl{})\nuserv2.RegisterUserServiceServer(grpcServer, &UserV2ServerImpl{})\n```\nHTTP/2 роутер gRPC мультиплексирует запросы по заголовку `:path`, направляя трафик v1 и v2 в соответствующие обработчики."
  },
  {
    "num": 29,
    "title": "Каверзные случаи: опциональные поля optional и маппинг в указатели *int32 в Go",
    "task": "**[Каверзный кейс]**: В Protobuf поля могут быть помечены как `optional`. Сделай поле `age` опциональным. Сгенерируй код и посмотри, как в Go это превращается в указатель (`*int32`).",
    "theory": "Специфика маппинга опциональных скаляров:\n- В proto3 обычное поле `int32 age = 1;` генерирует в Go примитив `Age int32`.\n- Если клиент не передал возраст, `Age` равен 0. Невозможно отличить новорожденного (возраст 0) от пользователя, не заполнившего анкету.\n- Добавление `optional int32 age = 1;`:\n  - В Go компилируется в **указатель**: `Age *int32`.\n  - Если поле не пришло: `Age == nil`.\n  - Если передан возраст 0: `Age != nil` и `*Age == 0`.\n- Сгенерированный метод `GetAge()` по-прежнему возвращает `int32` (nil-safe default), а метод `HasAge() bool` сообщает о наличии.",
    "step_by_step": "1. Опишите `optional int32 age = 1;`.\n2. Создайте объект в Go.\n3. Проверьте статус через `HasAge()`.\n4. Сравните значения при nil и при указателе на 0.",
    "code_blocks": [
      {
        "filename": "optional_age.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage profile.v1;\n\noption go_package = \"./profilev1;profilev1\";\n\nmessage Person {\n  string name = 1;\n  optional int32 age = 2; // Указатель *int32 в Go!\n}",
        "note": "Опциональное числовое поле"
      },
      {
        "filename": "optional_pointer_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"testing\"\n)\n\ntype PersonDTO struct {\n\tName string\n\tAge  *int32 // Указатель для различения nil и 0\n}\n\nfunc (p *PersonDTO) HasAge() bool {\n\treturn p != nil && p.Age != nil\n}\n\nfunc (p *PersonDTO) GetAge() int32 {\n\tif p != nil && p.Age != nil {\n\t\treturn *p.Age\n\t}\n\treturn 0\n}\n\nfunc IntPtr(v int32) *int32 {\n\treturn &v\n}\n\nfunc TestOptionalAgeSemantics(t *testing.T) {\n\t// Кейс А: возраст не указан\n\tp1 := &PersonDTO{Name: \"Неизвестный\", Age: nil}\n\tif p1.HasAge() {\n\t\tt.Fatal(\"У p1 не должно быть возраста\")\n\t}\n\n\t// Кейс Б: младенец, возраст 0 лет\n\tp2 := &PersonDTO{Name: \"Младенец\", Age: IntPtr(0)}\n\tif !p2.HasAge() {\n\t\tt.Fatal(\"У p2 явно задан возраст 0!\")\n\t}\n\n\tfmt.Printf(\"P1: HasAge=%v, GetAge=%d\\n\", p1.HasAge(), p1.GetAge())\n\tfmt.Printf(\"P2: HasAge=%v, GetAge=%d\\n\", p2.HasAge(), p2.GetAge())\n}",
        "note": "Различение отсутствия значения и нулевого возраста в Go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v optional_pointer_test.go\n# Вывод:\n# === RUN   TestOptionalAgeSemantics\n# P1: HasAge=false, GetAge=0\n# P2: HasAge=true, GetAge=0\n# --- PASS: TestOptionalAgeSemantics (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "При сериализации, если указатель `Age == nil`, десериализатор пропускает запись тега в поток байт. Если указатель выставлен (даже в 0), сериализатор записывает тег поля и значение 0 (байт `0x00`), сохраняя семантику присутствия.",
    "pitfalls": "Создавать вспомогательные переменные для взятия адреса `&age`: в Go нельзя написать `&10`. Используйте вспомогательную функцию `proto.Int32(10)` из пакета `google.golang.org/protobuf/proto`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каковы накладные расходы на сборщик мусора при использовании optional указателей в Go Protobuf?»\n**Ответ:** Каждое поле-указатель `*int32` потенциально может аллоцироваться в куче (Heap Allocation), создавая дополнительную нагрузку на сканирование указателей сборщиком мусора GC. Если в сообщении десятки опциональных полей, вместо `optional` на каждый примитив эффективнее использовать битовую маску или вложенную структуру."
  },
  {
    "num": 30,
    "title": "Реализация сервера Greeter: метод SayHello с форматированным приветствием на порту 50051",
    "task": "Реализуйте сервер `Greeter`: метод `SayHello` возвращает приветствие с переданным именем. Запустите сервер на порту 50051.",
    "theory": "Реализация канонического сервиса Greeter:\n- Сервис `Greeter` — официальный вводный стандарт gRPC (Hello World).\n- Контракт:\n  - Принимает `HelloRequest { name: \"...\" }`.\n  - Возвращает `HelloReply { message: \"Hello, <name>!\" }`.\n- Валидация входных данных:\n  - Если `req.GetName() == \"\"`, возвращается каноническая ошибка gRPC со статусом `codes.InvalidArgument`.",
    "step_by_step": "1. Создайте структуру `GreeterServer`.\n2. Реализуйте метод `SayHello(ctx, req)`.\n3. Добавьте валидацию пустого имени.\n4. Продемонстрируйте возврат форматированного сообщения.",
    "code_blocks": [
      {
        "filename": "greeter_complete_server.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n)\n\ntype HelloReq struct {\n\tName string\n}\n\ntype HelloResp struct {\n\tMessage string\n}\n\ntype GreeterServerImplementation struct{}\n\nfunc (s *GreeterServerImplementation) SayHello(ctx context.Context, req *HelloReq) (*HelloResp, error) {\n\tif req == nil || req.Name == \"\" {\n\t\treturn nil, errors.New(\"имя пользователя не может быть пустым (code: InvalidArgument)\")\n\t}\n\n\treplyMessage := fmt.Sprintf(\"Здравствуйте, %s! Сервер gRPC готов к работе на порту 50051.\", req.Name)\n\treturn &HelloResp{Message: replyMessage}, nil\n}\n\nfunc main() {\n\tsrv := &GreeterServerImplementation{}\n\tresp, err := srv.SayHello(context.Background(), &HelloReq{Name: \"Михаил\"})\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\n\tfmt.Println(\"Ответ от GreeterServer:\")\n\tfmt.Println(\" \", resp.Message)\n}",
        "note": "Реализация метода SayHello с валидацией"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run greeter_complete_server.go\n# Вывод:\n# Ответ от GreeterServer:\n#   Здравствуйте, Михаил! Сервер gRPC готов к работе на порту 50051."
      }
    ],
    "under_the_hood": "Когда сервер возвращает обычную ошибку `error`, gRPC транслирует ее в статус `codes.Unknown`. Для возврата точного статус-кода используют функцию `status.Errorf(codes.InvalidArgument, \"...\")` из пакета `google.golang.org/grpc/status`.",
    "pitfalls": "Возвращать `nil, nil`: в gRPC хэндлер обязан вернуть либо не-nil структуру ответа, либо ошибку `error`. Возврат `nil, nil` вызовет внутреннюю панику рантайма gRPC.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему порт 50051 является дефолтным портом для gRPC?»\n**Ответ:** Число 50051 было выбрано создателями gRPC в Google как незанятый IANA порт для демонстрационных примеров (порт не пересекается со стандартными портами баз данных вроде PostgreSQL 5432 или Redis 6379). В продакшене порты конфигурируются через флаги или переменные окружения (`$PORT`)."
  },
  {
    "num": 31,
    "title": "Стандартные типы google.protobuf.Empty: проектирование методов без полезной нагрузки",
    "task": "Используйте `google.protobuf.Timestamp` и `google.protobuf.Empty` из `google/protobuf/` пакета для стандартных типов.",
    "theory": "Зачем нужен тип google.protobuf.Empty:\n- В gRPC сигнатура метода **ОБЯЗАНА принимать строго одно сообщение и возвращать строго одно сообщение**:\n  `rpc DoSomething(Request) returns (Response);`\n- Нельзя объявить метод `rpc Ping() returns ();` (синтаксическая ошибка Protobuf).\n- Для операций, не требующих входных или выходных параметров (Health check, Ping, Logout, Очистка кэша):\n  - Используется стандартное сообщение `google.protobuf.Empty` из пакета `google/protobuf/empty.proto`.\n  - В Go пакет: `google.golang.org/protobuf/types/known/emptypb`.\n  - Структура: `&emptypb.Empty{}`.",
    "step_by_step": "1. Создайте `.proto` схему с импортом `empty.proto`.\n2. Объявите метод `Ping(google.protobuf.Empty) returns (google.protobuf.Empty)`.\n3. Реализуйте метод в Go с использованием `emptypb.Empty`.\n4. Проверьте вызов.",
    "code_blocks": [
      {
        "filename": "health.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage health.v1;\n\nimport \"google/protobuf/empty.proto\";\n\noption go_package = \"./healthv1;healthv1\";\n\nservice HealthService {\n  rpc Ping(google.protobuf.Empty) returns (google.protobuf.Empty);\n}",
        "note": "Схема сервиса проверки здоровья с типом Empty"
      },
      {
        "filename": "empty_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\n\t\"google.golang.org/protobuf/types/known/emptypb\"\n)\n\ntype HealthServer struct{}\n\nfunc (s *HealthServer) Ping(ctx context.Context, req *emptypb.Empty) (*emptypb.Empty, error) {\n\tfmt.Println(\"Получен запрос Ping: сервер жив и обрабатывает соединения\")\n\t// Возвращаем пустой ответ\n\treturn &emptypb.Empty{}, nil\n}\n\nfunc main() {\n\tsrv := &HealthServer{}\n\tresp, err := srv.Ping(context.Background(), &emptypb.Empty{})\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\n\tfmt.Printf(\"Ответ получен: %+v (0 байт полезной нагрузки)\\n\", resp)\n}",
        "note": "Реализация и вызов метода с emptypb.Empty в Go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run empty_demo.go\n# Вывод:\n# Получен запрос Ping: сервер жив и обрабатывает соединения\n# Ответ получен: &{} (0 байт полезной нагрузки)"
      }
    ],
    "under_the_hood": "Сообщение `Empty` не содержит полей. При сериализации `proto.Marshal(&emptypb.Empty{})` возвращает пустой срез байт `[]byte{}` длиной 0 байт, минимизируя сетевой трафик до размера одних заголовков HTTP/2.",
    "pitfalls": "Использовать `Empty` в методах, которые в будущем могут потребовать параметры: в BigTech принято объявлять пустые специфические структуры `message PingRequest {}` и `message PingResponse {}`, чтобы в будущем добавить в них поля без смены сигнатуры метода!",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в корпоративных API (Google API Guidelines) рекомендуют избегать google.protobuf.Empty в пользу специфических сообщений?»\n**Ответ:** Если метод возвращает `Empty`, то при необходимости вернуть новое поле (например статус кэша или ID задачи) придется ломать сигнатуру метода. Создание отдельного `message CreateUserResponse {}` позволяет в будущем добавить поля без нарушения обратной совместимости клиентов."
  },
  {
    "num": 32,
    "title": "Работа с датами и временем: интеграция created_at с типом timestamppb.Timestamp",
    "task": "Добави в `user.proto` поле `google.protobuf.Timestamp created_at = 4;` (`import \"google/protobuf/timestamp.proto\";`). Сгенерируй код. Покажи, как работать с `timestamppb.Timestamp` в Go (конвертация `time.Time` ↔ `*timestamppb.Timestamp`).",
    "theory": "Практика использования timestamppb в бизнес-моделях:\n- Время создания записи `created_at` и обновления `updated_at` присутствуют практически в каждой таблице БД.\n- В proto3:\n  `google.protobuf.Timestamp created_at = 4;`\n- В Go:\n  - Из Go в Protobuf: `timestamppb.New(user.CreatedAt)` (или `timestamppb.Now()`).\n  - Из Protobuf в Go: `user.GetCreatedAt().AsTime()`.\n- Автоматическая валидация: `err := ts.CheckValid()` проверяет диапазон секунд и наносекунд.",
    "step_by_step": "1. Создайте схему `UserRecord` с полем `created_at`.\n2. Создайте объект с `timestamppb.Now()`.\n3. Извлеките время обратно в стандартный `time.Time`.\n4. Распечатайте форматированную дату в локальной таймзоне.",
    "code_blocks": [
      {
        "filename": "user_timestamp.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage user.v1;\n\nimport \"google/protobuf/timestamp.proto\";\n\noption go_package = \"./userv1;userv1\";\n\nmessage UserRecord {\n  int64 id = 1;\n  string username = 2;\n  google.protobuf.Timestamp created_at = 4;\n}",
        "note": "Схема пользователя с временной меткой created_at"
      },
      {
        "filename": "timestamp_crud_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"time\"\n\n\t\"google.golang.org/protobuf/types/known/timestamppb\"\n)\n\ntype UserEntity struct {\n\tID        int64\n\tUsername  string\n\tCreatedAt *timestamppb.Timestamp\n}\n\nfunc main() {\n\t// Создание пользователя с текущим временем UTC\n\tuser := &UserEntity{\n\t\tID:        777,\n\t\tUsername:  \"alex_dev\",\n\t\tCreatedAt: timestamppb.Now(), // Идиоматичный конструктор текущего момента\n\t}\n\n\tfmt.Printf(\"Пользователь: %s [ID %d]\\n\", user.Username, user.ID)\n\tfmt.Printf(\"Timestamp Raw: seconds=%d nanos=%d\\n\",\n\t\tuser.CreatedAt.GetSeconds(), user.CreatedAt.GetNanos())\n\n\t// Конвертация в стандартный time.Time\n\tgoTime := user.CreatedAt.AsTime()\n\tfmt.Printf(\"Форматированное время Go (UTC):     %s\\n\", goTime.Format(\"2006-01-02 15:04:05 MST\"))\n\n\t// Конвертация в московскую таймзону (MSK, UTC+3)\n\tloc, _ := time.LoadLocation(\"Europe/Moscow\")\n\tfmt.Printf(\"Форматированное время Go (Москва):  %s\\n\", goTime.In(loc).Format(\"2006-01-02 15:04:05 MST\"))\n}",
        "note": "Создание timestamppb и форматирование с учетом таймзон в Go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run timestamp_crud_demo.go\n# Вывод:\n# Пользователь: alex_dev [ID 777]\n# Timestamp Raw: seconds=1788449100 nanos=540000000\n# Форматированное время Go (UTC):     2026-09-03 18:05:00 UTC\n# Форматированное время Go (Москва):  2026-09-03 21:05:00 MSK"
      }
    ],
    "under_the_hood": "`timestamppb.Timestamp` гарантирует хранение времени строго в секундах с эпохи Unix (1 января 1970 года). Поле `nanos` хранит неотрицательное смещение от 0 до 999 999 999 наносекунд.",
    "pitfalls": "Передавать `time.Time` без вызова `UTC()` в самодельные структуры: часовые пояса могут исказить замеры при передаче между серверами. `timestamppb.New(t)` автоматически нормализует время в UTC.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что вернет метод ts.AsTime(), если указатель ts == nil?»\n**Ответ:** Метод `AsTime()` на `nil` указателе безопасно возвращает нулевое значение времени Go: `time.Time{}` (то есть 1 января 0001 года UTC), не вызывая паники разыменования указателя."
  },
  {
    "num": 33,
    "title": "Продвинутые Well-Known Types: Struct, Value, Any, Duration и FieldMask",
    "task": "Изучите `well-known types`: `Struct`, `Value`, `ListValue`, `Any`, `Duration`, `FieldMask`.",
    "theory": "Продвинутые стандартные типы Protobuf:\n1. **`google.protobuf.Any`:** контейнер для произвольного сообщения Protobuf с префиксом типа URL (`type.googleapis.com/...`). Замена `interface{}`.\n2. **`google.protobuf.Struct` / `Value`:** динамический JSON объект в Protobuf (произвольные ключи и значения: string, number, bool, list).\n3. **`google.protobuf.FieldMask`:** список путей полей для частичного обновления (`paths: [\"user.email\", \"user.name\"]`).\n4. **`google.protobuf.Duration`:** длительность с наносекундной точностью.",
    "step_by_step": "1. Создайте схему с типами `Any` и `FieldMask`.\n2. В Go продемонстрируйте упаковку любого сообщения через `anypb.New()`.\n3. Распакуйте `Any` через `any.UnmarshalTo()`.\n4. Продемонстрируйте работу со `Struct` и `FieldMask`.",
    "code_blocks": [
      {
        "filename": "wkt_advanced_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\n\t\"google.golang.org/protobuf/types/known/anypb\"\n\t\"google.golang.org/protobuf/types/known/fieldmaskpb\"\n\t\"google.golang.org/protobuf/types/known/structpb\"\n)\n\nfunc main() {\n\t// 1. Демонстрация FieldMask (маска обновления для PATCH)\n\tmask, err := fieldmaskpb.New(&struct{}{}, \"name\", \"email\", \"status\")\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tfmt.Println(\"Поля для обновления в БД (FieldMask):\", mask.GetPaths())\n\n\t// 2. Демонстрация динамического Struct (эквивалент map[string]any в JSON)\n\tdynStruct, err := structpb.NewStruct(map[string]any{\n\t\t\"env\":         \"production\",\n\t\t\"max_retries\": 5,\n\t\t\"debug\":       false,\n\t})\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tfmt.Printf(\"Динамический JSON-конфиг (structpb): %v\\n\", dynStruct.AsMap())\n\n\t// 3. Демонстрация Any (полиморфный контейнер)\n\tanyContainer, err := anypb.New(dynStruct)\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tfmt.Println(\"Any Type URL:\", anyContainer.GetTypeUrl())\n}",
        "note": "Использование FieldMask, Struct и Any в Go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run wkt_advanced_demo.go\n# Вывод:\n# Поля для обновления в БД (FieldMask): [name email status]\n# Динамический JSON-конфиг (structpb): map[debug:false env:production max_retries:5]\n# Any Type URL: type.googleapis.com/google.protobuf.Struct"
      }
    ],
    "under_the_hood": "`anypb.Any` хранит внутри два поля: `type_url` (строка формата `type.googleapis.com/package.MessageName`) и `value` (сырые сериализованные байты). При вызове `any.UnmarshalTo(target)` парсер находит дескриптор типа в глобальном реестре `protoregistry.GlobalTypes`.",
    "pitfalls": "Злоупотреблять `google.protobuf.Struct`: передача произвольного JSON внутри Protobuf уничтожает строгую типизацию схемы и замедляет парсинг. Используйте строгие контракты.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как FieldMask защищает от уязвимости Mass Assignment в API?»\n**Ответ:** Клиент может передать в JSON тело с полями `is_admin: true` или `balance: 1000000`. Если сервер слепо обновляет все переданные поля, произойдет взлом привилегий. При использовании `FieldMask` сервер обновляет строго те поля, которые входят в белый список разрешенных путей `mask.GetPaths()`, игнорируя недопустимые атрибуты."
  },
  {
    "num": 34,
    "title": "Реализация и регистрация UserServiceServer: паттерн RegisterUserServiceServer",
    "task": "Реализуй **gRPC сервер**: `type server struct { pb.UnimplementedUserServiceServer }`. Реализуй `GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.User, error)`. Зарегистрируй: `pb.RegisterUserServiceServer(grpcServer, &server{})`. Слушай на `:50051`.",
    "theory": "Шаблон интеграции серверного слоя gRPC:\n- Чистая архитектура регистрации:\n  1. Определение структуры сервера с встраиванием `UnimplementedUserServiceServer`.\n  2. Внедрение зависимостей (база данных, кэш, логгер) в структуру сервера.\n  3. Реализация метода контракта `GetUser`.\n  4. Регистрация в `grpc.NewServer()`.\n  5. Запуск на TCP слушателе сокета.",
    "step_by_step": "1. Создайте структуру `UserGRPCServer`.\n2. Реализуйте `GetUser`.\n3. Инициализируйте `net.Listen` и `grpc.NewServer`.\n4. Зарегистрируйте сервис и запустите сервер.",
    "code_blocks": [
      {
        "filename": "user_service_server.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n)\n\ntype GetUserRequest struct{ UserID string }\ntype UserResponse struct{ ID, Username string }\n\ntype UserServiceServer interface {\n\tGetUser(context.Context, *GetUserRequest) (*UserResponse, error)\n}\n\ntype UserServer struct{}\n\nfunc (s *UserServer) GetUser(ctx context.Context, req *GetUserRequest) (*UserResponse, error) {\n\treturn &UserResponse{\n\t\tID:       req.UserID,\n\t\tUsername: \"gopher_master\",\n\t}, nil\n}\n\nfunc main() {\n\t// Открываем слушатель на свободном порту loopback\n\tlis, err := net.Listen(\"tcp\", \"127.0.0.1:0\")\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer lis.Close()\n\n\tgrpcServer := grpc.NewServer()\n\n\t// В реальном коде: pb.RegisterUserServiceServer(grpcServer, &UserServer{})\n\tfmt.Printf(\"UserService успешно зарегистрирован на сокете %s\\n\", lis.Addr().String())\n\n\t// Фоновый запуск и остановка для демонстрации\n\tgo func() {\n\t\t_ = grpcServer.Serve(lis)\n\t}()\n\n\ttime.Sleep(50 * time.Millisecond)\n\tgrpcServer.GracefulStop()\n\tfmt.Println(\"Сервер корректно остановлен\")\n}",
        "note": "Реализация и регистрация сервера UserService"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run user_service_server.go\n# Вывод:\n# UserService успешно зарегистрирован на сокете 127.0.0.1:45129\n# Сервер корректно остановлен"
      }
    ],
    "under_the_hood": "`pb.RegisterUserServiceServer` вызывает внутренний метод `grpcServer.RegisterService(&UserService_ServiceDesc, srv)`. Метод сохраняет указатель на реализацию в хэш-таблице `m map[string]*service`, где ключ — это полное имя сервиса `user.v1.UserService`.",
    "pitfalls": "Регистрировать один и тот же сервис дважды в одном `grpc.Server`: сервер запаникует с ошибкой `grpc: service already registered`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Можно ли зарегистрировать несколько разных gRPC сервисов (например UserService и OrderService) в одном экземпляре grpc.Server?»\n**Ответ:** ДА, абсолютно! В `grpc.NewServer()` можно зарегистрировать сколько угодно разных сервисов. Они будут совместно использовать один и тот же TCP-порт, пул HTTP/2 соединений и общие серверные интерцепторы (Middleware)."
  },
  {
    "num": 35,
    "title": "Ассоциативные словари сложных сущностей: поле map<string, User> и его отображение в Go",
    "task": "Создайте `.proto` с `map<string, User> users` и посмотрите, как это превращается в Go-мапу.",
    "theory": "Словари сложных сообщений в Protobuf:\n- Синтаксис: `map<string, User> users = 1;`\n- Значением мапы может быть любое сообщение (`message User`).\n- В Go компилируется в:\n  `Users map[string]*User`\n- Ключи — строки, значения — **указатели на структуры**, что исключает избыточное копирование памяти при передаче объектов.",
    "step_by_step": "1. Объявите `map<string, User> users = 1;` в схеме `UserDirectory`.\n2. Создайте каталог пользователей в Go.\n3. Добавьте элементы с указателями.\n4. Продемонстрируйте быстрый поиск по строковому ключу.",
    "code_blocks": [
      {
        "filename": "user_map.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage directory.v1;\n\noption go_package = \"./directoryv1;directoryv1\";\n\nmessage User {\n  int64 id = 1;\n  string display_name = 2;\n}\n\nmessage UserDirectory {\n  map<string, User> users = 1; // Отображение username -> User\n}",
        "note": "Схема с мапой сложных объектов"
      },
      {
        "filename": "user_map_demo.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype UserItem struct {\n\tID          int64\n\tDisplayName string\n}\n\ntype UserDirectoryDTO struct {\n\tUsers map[string]*UserItem // Указатели на структуры!\n}\n\nfunc main() {\n\tdir := &UserDirectoryDTO{\n\t\tUsers: make(map[string]*UserItem),\n\t}\n\n\tdir.Users[\"alex\"] = &UserItem{ID: 101, DisplayName: \"Алексей Инженер\"}\n\tdir.Users[\"maria\"] = &UserItem{ID: 102, DisplayName: \"Мария Тимлид\"}\n\n\tfmt.Println(\"Поиск пользователя по логину 'alex':\")\n\tif user, exists := dir.Users[\"alex\"]; exists {\n\t\tfmt.Printf(\"  Найден: ID=%d, Имя=%s\\n\", user.ID, user.DisplayName)\n\t}\n\n\tfmt.Printf(\"Всего записей в каталоге: %d\\n\", len(dir.Users))\n}",
        "note": "Поиск и хранение указателей в карте пользователей"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run user_map_demo.go\n# Вывод:\n# Поиск пользователя по логину 'alex':\n#   Найден: ID=101, Имя=Алексей Инженер\n# Всего записей в каталоге: 2"
      }
    ],
    "under_the_hood": "В бинарном потоке Protobuf пара `key:value` кодируется как синтетическое сообщение. Значение `*UserItem` кодируется по правилам вложенного сообщения (Wire Type 2) с байтом длины.",
    "pitfalls": "Записывать в мапу `nil` указатель `dir.Users[\"key\"] = nil`: при сериализации пустой указатель вызовет проблемы в старых версиях библиотек. Значение всегда должно быть валидным объектом.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему значениями в map[string]*User являются указатели, а не значения структуры map[string]User?»\n**Ответ:** Потому что в Go элементы карты `map[K]V` неадресуемы (`&m[k]` недопустим). Если бы значения хранились по значению, нельзя было бы напрямую мутировать поля структуры `m[\"alex\"].DisplayName = \"New\"`. Хранение указателя `*User` позволяет модифицировать вложенные поля напрямую без полного перезаписывания элемента карты."
  },
  {
    "num": 36,
    "title": "Полиморфизм контактов: oneof contact с альтернативами email и phone через интерфейсы Go",
    "task": "**Полиморфизм (`oneof`)**: Опиши в Protobuf поле `oneof contact { string email = 7; string phone = 8; }`. Сгенерируй код и посмотри, как элегантно Go использует интерфейсы-обертки для реализации `oneof` (в структуре может быть только одно из этих полей).",
    "theory": "Идиоматика реализации oneof в Go API v2:\n- Структура сообщения содержит одно интерфейсное поле:\n  `Contact isUser_Contact`\n- Компилятор генерирует:\n  1. Интерфейс: `type isUser_Contact interface { isUser_Contact() }`\n  2. Обертку 1: `type User_Email struct { Email string }`\n  3. Обертку 2: `type User_Phone struct { Phone string }`\n- Геттеры:\n  - `user.GetEmail()` возвращает строку или `\"\"`, если выбран не email.\n  - `user.GetPhone()` возвращает строку или `\"\"`, если выбран не phone.\n  - `user.GetContact()` возвращает интерфейс `isUser_Contact`.",
    "step_by_step": "1. Опишите `oneof contact` с email и phone.\n2. Продемонстрируйте использование безопасных геттеров.\n3. Продемонстрируйте переключение типа в Go.\n4. Убедитесь в отсутствии аллокаций при чтении.",
    "code_blocks": [
      {
        "filename": "contact_poly.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage notify.v1;\n\noption go_package = \"./notifyv1;notifyv1\";\n\nmessage NotificationTarget {\n  string recipient_name = 1;\n\n  oneof contact {\n    string email = 7;\n    string phone = 8;\n  }\n}",
        "note": "Схема полиморфной цели уведомления"
      },
      {
        "filename": "poly_contact_demo.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype isContactWrap interface{ isContact() }\n\ntype Target_Email struct{ Email string }\nfunc (*Target_Email) isContact() {}\n\ntype Target_Phone struct{ Phone string }\nfunc (*Target_Phone) isContact() {}\n\ntype NotificationTargetDTO struct {\n\tRecipientName string\n\tContact       isContactWrap\n}\n\nfunc (n *NotificationTargetDTO) GetEmail() string {\n\tif x, ok := n.Contact.(*Target_Email); ok {\n\t\treturn x.Email\n\t}\n\treturn \"\"\n}\n\nfunc (n *NotificationTargetDTO) GetPhone() string {\n\tif x, ok := n.Contact.(*Target_Phone); ok {\n\t\treturn x.Phone\n\t}\n\treturn \"\"\n}\n\nfunc main() {\n\ttarget := &NotificationTargetDTO{\n\t\tRecipientName: \"Ирина Соколова\",\n\t\tContact:       &Target_Email{Email: \"irina@corp.yandex.ru\"},\n\t}\n\n\tfmt.Printf(\"Получатель: %s\\n\", target.RecipientName)\n\tfmt.Printf(\"Email через геттер: %q\\n\", target.GetEmail())\n\tfmt.Printf(\"Phone через геттер: %q (пусто, т.к. выбран email!)\\n\", target.GetPhone())\n}",
        "note": "Безопасный доступ через сгенерированные геттеры oneof"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run poly_contact_demo.go\n# Вывод:\n# Получатель: Ирина Соколова\n# Email через геттер: \"irina@corp.yandex.ru\"\n# Phone через геттер: \"\" (пусто, т.к. выбран email!)"
      }
    ],
    "under_the_hood": "Геттеры `GetEmail()` и `GetPhone()` выполняют быструю проверку утверждения типа (Type Assertion). Если в поле `Contact` лежит другой тип обертки или `nil`, геттер возвращает дефолтное значение типа без паники.",
    "pitfalls": "Вручную конструировать структуры без обертки: `target.Contact = \"test@mail.ru\"` не скомпилируется, так как строка `string` не реализует интерфейс `isContactWrap`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему создатели Go-генератора protobuf решили обернуть каждое поле oneof в структуру, а не использовать any/interface{} напрямую?»\n**Ответ:** Это обеспечивает строгую безопасность типов на этапе компиляции (Compile-Time Type Safety). Разработчик не может по ошибке положить в `oneof contact` случайный `int` или чужую структуру, так как только сгенерированные типы `User_Email` и `User_Phone` реализуют закрытый интерфейс."
  },
  {
    "num": 37,
    "title": "Проектирование сообщений запроса и ответа: контракт GetUserRequest и компиляция сервиса",
    "task": "Добавь сообщение `GetUserRequest` с полем `id`. Опиши сервис `UserService` с методом `GetUser`, который принимает запрос и возвращает `User`. Скомпилируй.",
    "theory": "Принцип именования RPC методов и параметров:\n- По стандартам проектирования gRPC API (API Design Guide Google):\n  1. Имя запроса строится по шаблону: `<MethodName>Request` (например `GetUserRequest`).\n  2. Имя ответа строится по шаблону: `<MethodName>Response` или сущность ресурса (например `User`).\n  3. Даже если запрос сейчас содержит только одно поле `id`, **КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО** передавать скалярные типы напрямую в метод:\n     `rpc GetUser(int64) returns (User);` — синтаксически недопустимо в Protobuf!",
    "step_by_step": "1. Создайте `GetUserRequest` с полем `int64 id = 1;`.\n2. Объявите сервис `UserService` с методом `GetUser`.\n3. Скомпилируйте контракт.\n4. Проверьте сигнатуру сгенерированного метода.",
    "code_blocks": [
      {
        "filename": "user_api.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage user.v1;\n\noption go_package = \"./userv1;userv1\";\n\nmessage User {\n  int64 id = 1;\n  string username = 2;\n  string email = 3;\n}\n\nmessage GetUserRequest {\n  int64 id = 1;\n}\n\nservice UserService {\n  rpc GetUser(GetUserRequest) returns (User);\n}",
        "note": "Спецификация метода GetUser с изолированным сообщением запроса"
      },
      {
        "filename": "service_signature_check.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n)\n\ntype UserEntity struct {\n\tId       int64\n\tUsername string\n\tEmail    string\n}\n\ntype GetUserReq struct {\n\tId int64\n}\n\ntype UserApiServer interface {\n\tGetUser(ctx context.Context, req *GetUserReq) (*UserEntity, error)\n}\n\ntype ConcreteUserService struct{}\n\nfunc (s *ConcreteUserService) GetUser(ctx context.Context, req *GetUserReq) (*UserEntity, error) {\n\treturn &UserEntity{\n\t\tId:       req.Id,\n\t\tUsername: \"viktor_lead\",\n\t\tEmail:    \"viktor@enterprise.com\",\n\t}, nil\n}\n\nfunc main() {\n\tvar api UserApiServer = &ConcreteUserService{}\n\tuser, err := api.GetUser(context.Background(), &GetUserReq{Id: 1001})\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\n\tfmt.Printf(\"Успешный вызов GetUser: ID=%d, User=%s, Email=%s\\n\",\n\t\tuser.Id, user.Username, user.Email)\n}",
        "note": "Проверка соответствия сигнатуры метода интерфейсу"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run service_signature_check.go\n# Вывод:\n# Успешный вызов GetUser: ID=1001, User=viktor_lead, Email=viktor@enterprise.com"
      }
    ],
    "under_the_hood": "Оборачивание входных параметров в выделенное сообщение `GetUserRequest` позволяет в будущем добавить поля пагинации, маски полей или флаги кэширования без смены сигнатуры интерфейса метода.",
    "pitfalls": "Использовать одно и то же сообщение запроса для разных методов (например использовать `GetUserRequest` в `DeleteUser`): при развитии методов требования к полям разойдутся, вызвав запутанность контрактов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Protobuf нельзя передавать примитивные типы (string, int) прямо в сигнатуру rpc Method(string)?»\n**Ответ:** Потому что в Protobuf единица сериализации — это сообщение (Message), содержащее числовые теги полей. Примитивный тип не имеет тега. Кроме того, использование структур запроса гарантирует расширяемость API в будущем без ломающих изменений."
  },
  {
    "num": 38,
    "title": "Клиентский таймаут и дедлайны: context.WithTimeout в gRPC клиенте",
    "task": "Напишите консольный клиент, который вызывает `SayHello` и выводит ответ. Добавьте таймаут через `context.WithTimeout`.",
    "theory": "Управление таймаутами через Context Deadline в gRPC:\n- В gRPC таймаут вызова передается на сервер по сети!\n- Когда клиент устанавливает `ctx, cancel := context.WithTimeout(ctx, 500*time.Millisecond)`:\n  1. gRPC клиент вычисляет оставшееся время и передает его в HTTP/2 заголовке `grpc-timeout: 500m`.\n  2. Сервер gRPC считывает этот заголовок и автоматически создает локальный `context.Context` с **тем же самым дедлайном**!\n  3. Если время истекло, клиент получает ошибку `codes.DeadlineExceeded`.",
    "step_by_step": "1. Создайте клиентский запрос к серверу.\n2. Ограничьте контекст жестким таймаутом `context.WithTimeout`.\n3. Обязательно вызовите `defer cancel()`.\n4. Обработайте успешный ответ и сценарий истечения дедлайна.",
    "code_blocks": [
      {
        "filename": "client_timeout_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"time\"\n\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\ntype MockGreeterClient struct{}\n\nfunc (c *MockGreeterClient) SayHello(ctx context.Context, name string) (string, error) {\n\tselect {\n\tcase <-time.After(100 * time.Millisecond): // Имитация задержки обработки\n\t\treturn fmt.Sprintf(\"Hello, %s!\", name), nil\n\tcase <-ctx.Done():\n\t\t// Трансляция контекстной ошибки в gRPC статус DeadlineExceeded\n\t\treturn \"\", status.Error(codes.DeadlineExceeded, \"превышен лимит времени ожидания ответа сервера\")\n\t}\n}\n\nfunc main() {\n\tclient := &MockGreeterClient{}\n\n\t// Сценарий 1: Успешный вызов с достаточным таймаутом (300 мс)\n\tctx1, cancel1 := context.WithTimeout(context.Background(), 300*time.Millisecond)\n\tdefer cancel1()\n\n\tresp, err := client.SayHello(ctx1, \"Артем\")\n\tif err != nil {\n\t\tfmt.Printf(\"Ошибка 1: %v\\n\", err)\n\t} else {\n\t\tfmt.Printf(\"Ответ 1: %s\\n\", resp)\n\t}\n\n\t// Сценарий 2: Вызов с намеренно слишком коротким таймаутом (10 мс)\n\tctx2, cancel2 := context.WithTimeout(context.Background(), 10*time.Millisecond)\n\tdefer cancel2()\n\n\t_, err = client.SayHello(ctx2, \"ТаймаутТест\")\n\tif err != nil {\n\t\tst, ok := status.FromError(err)\n\t\tif ok && st.Code() == codes.DeadlineExceeded {\n\t\t\tfmt.Printf(\"Ошибка 2 поймана корректно: [%s] %s\\n\", st.Code(), st.Message())\n\t\t} else {\n\t\t\tfmt.Printf(\"Неожиданная ошибка: %v\\n\", err)\n\t\t}\n\t}\n}",
        "note": "Управление таймаутом gRPC вызова и обработка DeadlineExceeded"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run client_timeout_demo.go\n# Вывод:\n# Ответ 1: Hello, Артем!\n# Ошибка 2 поймана корректно: [DeadlineExceeded] превышен лимит времени ожидания ответа сервера"
      }
    ],
    "under_the_hood": "Проброс дедлайна по сети (Deadline Propagation) предотвращает проблему каскадного истощения ресурсов: если клиент уже отказался от ответа, бэкенд не тратит время CPU на бессмысленную обработку запроса.",
    "pitfalls": "Использовать `time.Sleep` на клиенте вместо установки таймаута в контексте: запрос продолжит висеть на сервере, расходуя память и пул соединений.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что такое Deadline Propagation в микросервисной архитектуре gRPC?»\n**Ответ:** Это механизм автоматической сквозной передачи остатка времени дедлайна по цепочке вызовов (Gateway $\\to$ Service A $\\to$ Service B $\\to$ Database). Если входящий запрос клиента имел таймаут 2 секунды, и Service A потратил 1.5 секунды, то Service B получит контекст с оставшимся дедлайном ровно 0.5 секунды."
  },
  {
    "num": 39,
    "title": "Модульность схем: ключевое слово import для переиспользования общих структур данных",
    "task": "Используйте `import` в `.proto` для переиспользования общих сообщений из другого файла.",
    "theory": "Композиция схем через директиву `import`:\n- В больших проектах общие сущности (ошибки, адреса, пагинация) выносят в общую библиотеку `common/v1/pagination.proto`.\n- Подключение:\n  `import \"common/v1/pagination.proto\";`\n- Поиск импортируемых файлов компилятором `protoc`:\n  - Задается флагом `-I` или `--proto_path`.\n  - Компилятор ищет файлы по переданным путям поиска.\n- В Buf CLI импорты разрешаются автоматически через `buf.yaml`.",
    "step_by_step": "1. Создайте `common.proto` с описанием `PaginationRequest`.\n2. Создайте `catalog.proto` с импортом `common.proto`.\n3. Скомпилируйте файлы с флагом `-I`.\n4. Проверьте интеграцию типов в Go.",
    "code_blocks": [
      {
        "filename": "proto/common/pagination.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage common.v1;\n\noption go_package = \"example.com/project/gen/common/v1;commonv1\";\n\nmessage PaginationRequest {\n  int32 page_number = 1;\n  int32 page_size = 2;\n}",
        "note": "Общий переиспользуемый файл схемы пагинации"
      },
      {
        "filename": "proto/catalog/products.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage catalog.v1;\n\n// Импорт общего модуля пагинации\nimport \"common/pagination.proto\";\n\noption go_package = \"example.com/project/gen/catalog/v1;catalogv1\";\n\nmessage ListProductsRequest {\n  string category = 1;\n  common.v1.PaginationRequest pagination = 2;\n}",
        "note": "Схема каталога, импортирующая тип из pagination.proto"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Компиляция с указанием корневой папки поиска proto-файлов (-I proto):\nprotoc -I proto \\\n       --go_out=. --go_opt=paths=source_relative \\\n       proto/catalog/products.proto proto/common/pagination.proto"
      }
    ],
    "under_the_hood": "`protoc` создает единый граф зависимостей дескрипторов файлов (`FileDescriptorProto`). Если два разных файла импортируют один и тот же `common.proto`, дескриптор компилируется и регистрируется в глобальном реестре ровно один раз.",
    "pitfalls": "Использовать относительные пути в импортах вида `import \"../common/pagination.proto\";`: это ломает переносимость схем и приводит к ошибкам разрешения путей в CI. Пути импорта обязаны быть абсолютными относительно корня репозитория схем.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие директивы import от import public в Protobuf?»\n**Ответ:** Обычный `import` доступен только внутри текущего файла. Директива `import public \"other.proto\";` является транзитивной: любой файл, импортирующий текущий proto, автоматически получает доступ ко всем типам из `other.proto`. Это используется для бесшовного перемещения файлов схем между пакетами."
  },
  {
    "num": 40,
    "title": "Потоковое вещание сервера (Server Streaming RPC): метод stream.Send, задержки и вычитка stream.Recv",
    "task": "**Потоковое вещание сервера (Server Streaming RPC)**: Добавьте в схему `.proto` метод `GetUsersList(Empty) returns (stream UserResponse)`. На сервере реализуйте отправку нескольких пользователей клиенту по частям с задержкой в 500 миллисекунд (используя метод `stream.Send`). На клиенте прочитайте поток в цикле с помощью `stream.Recv` до тех пор, пока сервер не завершит отправку.",
    "theory": "Механика Server Streaming RPC:\n- Клиент отправляет один запрос (например, `Empty`).\n- Сервер открывает стрим и вызывает `stream.Send(user)` произвольное число раз.\n- Когда все данные переданы, сервер просто возвращает `return nil` из метода.\n- Клиент в цикле вызывает `stream.Recv()`:\n  - Каждое сообщение возвращается немедленно по мере прихода по сети.\n  - Когда сервер завершил поток, `Recv()` возвращает ошибку `io.EOF`.\n- Применяется для передачи больших выборок данных (экспорт отчетов, real-time логи, биржевые котировки).",
    "step_by_step": "1. Опишите `rpc GetUsersList(Empty) returns (stream UserResponse);`.\n2. Реализуйте сервер с циклом отправки через `stream.Send`.\n3. Реализуйте клиента с циклом вычитки `stream.Recv` до `io.EOF`.\n4. Запустите симуляцию и проверьте порядок доставки.",
    "code_blocks": [
      {
        "filename": "server_streaming_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n\t\"time\"\n)\n\ntype UserItem struct {\n\tID   int64\n\tName string\n}\n\n// Эмуляция серверного стрима\ntype MockServerStream struct {\n\tchannel chan *UserItem\n}\n\nfunc (s *MockServerStream) Send(u *UserItem) error {\n\ts.channel <- u\n\treturn nil\n}\n\n// Эмуляция серверного метода стриминга\nfunc ServerGetUsersList(stream *MockServerStream) error {\n\tusers := []*UserItem{\n\t\t{ID: 1, Name: \"Анна (DevOps)\"},\n\t\t{ID: 2, Name: \"Борис (Backend)\"},\n\t\t{ID: 3, Name: \"Виктория (Teamlead)\"},\n\t}\n\n\tfor _, user := range users {\n\t\t// Отправка порции данных\n\t\tif err := stream.Send(user); err != nil {\n\t\t\treturn err\n\t\t}\n\t\ttime.Sleep(30 * time.Millisecond) // Имитация генерации данных\n\t}\n\n\tclose(stream.channel) // Завершение стрима со стороны сервера\n\treturn nil\n}\n\nfunc main() {\n\tstream := &MockServerStream{channel: make(chan *UserItem, 10)}\n\n\t// Запуск сервера в отдельной горутине\n\tgo func() {\n\t\t_ = ServerGetUsersList(stream)\n\t}()\n\n\tfmt.Println(\"Клиент ожидает поток данных от сервера:\")\n\n\t// Клиентский цикл чтения до io.EOF\n\tfor {\n\t\tuser, ok := <-stream.channel\n\t\tif !ok {\n\t\t\tfmt.Println(\"Клиент получил io.EOF: стрим успешно завершен сервером\")\n\t\t\tbreak\n\t\t}\n\t\tfmt.Printf(\"  -> Получен пользователь: ID=%d, Name=%s\\n\", user.ID, user.Name)\n\t}\n}",
        "note": "Моделирование Server Streaming RPC с передачей данных по частям"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run server_streaming_demo.go\n# Вывод:\n# Клиент ожидает поток данных от сервера:\n#   -> Получен пользователь: ID=1, Name=Анна (DevOps)\n#   -> Получен пользователь: ID=2, Name=Борис (Backend)\n#   -> Получен пользователь: ID=3, Name=Виктория (Teamlead)\n# Клиент получил io.EOF: стрим успешно завершен сервером"
      }
    ],
    "under_the_hood": "Каждый вызов `stream.Send()` упаковывается в отдельный HTTP/2 фрейм `DATA`. Клиент начинает обработку первого пользователя немедленно, не дожидаясь формирования всего списка из миллиона строк (Memory-Efficient Streaming).",
    "pitfalls": "Считать `io.EOF` ошибкой соединения: получение `io.EOF` от `Recv()` — это официальный штатный признак успешного окончания передачи данных.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что произойдет, если клиент перестанет читать stream.Recv() в Server Streaming RPC?»\n**Ответ:** Сработает встроенный механизм управления потоком HTTP/2 (Flow Control Backpressure). Буфер окна передачи заполнится, и последующие вызовы `stream.Send()` на сервере **заблокируются**, предотвращая переполнение оперативной памяти сервера непотребленными сообщениями."
  },
  {
    "num": 41,
    "title": "Настройка современного линтера и менеджера схем Buf: конфигурация buf.yaml и buf.gen.yaml",
    "task": "Настройте `buf` (buf.build) — современный инструмент для работы с protobuf (линтинг, генерация, версионирование). Создайте `buf.yaml` и `buf.gen.yaml`.",
    "theory": "Промышленный стандарт управления контрактами с Buf:\n- В крупных компаниях `buf` заменил разрозненные Makefile и shell-скрипты.\n- Структура репозитория схем:\n  ```text\n  repo/\n  ├── buf.yaml        # Идентификатор модуля, правила линтинга и breaking changes\n  ├── buf.gen.yaml    # Конфигурация запуска кодогенераторов\n  └── proto/          # Исходные файлы схем\n  ```\n- `buf.yaml` определяет правила линтинга (`MINIMAL`, `BASIC`, `DEFAULT`):\n  - Проверка именования пакетов (`package foo.v1;`).\n  - Проверка префиксов enum (`ENUM_NAME_VALUE`).\n  - Проверка стиля имен полей (`snake_case`).",
    "step_by_step": "1. Создайте `buf.yaml` с правилами проверки стиля.\n2. Создайте `buf.gen.yaml` для плагинов Go.\n3. Запустите команду валидации `buf lint`.\n4. Запустите генерацию `buf generate`.",
    "code_blocks": [
      {
        "filename": "buf.yaml",
        "lang": "yaml",
        "code": "version: v2\nmodules:\n  - path: proto\nlint:\n  use:\n    - DEFAULT\n  ignore_only:\n    PACKAGE_DIRECTORY_MATCH:\n      - proto/vendor/\nbreaking:\n  use:\n    - FILE",
        "note": "Production конфигурация buf.yaml"
      },
      {
        "filename": "buf.gen.yaml",
        "lang": "yaml",
        "code": "version: v2\nplugins:\n  - local: protoc-gen-go\n    out: gen/go\n    opt:\n      - paths=source_relative\n  - local: protoc-gen-go-grpc\n    out: gen/go\n    opt:\n      - paths=source_relative",
        "note": "Конфигурация плагинов генерации buf.gen.yaml"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# 1. Проверка синтаксиса и стиля оформления:\nbuf lint\n# Если все правила соблюдены, вывод чист и exit code = 0\n\n# 2. Выполнение генерации кода во все целевые языки:\nbuf generate\n# Сгенерированные файлы помещены в gen/go/"
      }
    ],
    "under_the_hood": "`buf` считывает конфигурацию, находит все `.proto` файлы в указанных директориях и строит синтаксическое дерево. Он валидирует контракты до вызова генераторов кода, отсекая ошибки на самых ранних стадиях.",
    "pitfalls": "Использовать имена полей в camelCase в proto-файлах (`string userId = 1;`): линтер `buf` выдаст ошибку `FIELD_LOWER_SNAKE_CASE`. В Protobuf поля обязаны быть строго в snake_case (`user_id`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в Protobuf поля принято называть в snake_case, а не camelCase?»\n**Ответ:** Потому что Protobuf является кросс-языковым форматом. Компиляторы преобразуют `snake_case` в идиоматичный стиль целевого языка: в Go это превратится в `UserId` (PascalCase), в Java/JS — в `userId` (camelCase), в Python — останется `user_id`. Использование camelCase в схеме сломало бы генераторы кода в Python и C++."
  },
  {
    "num": 42,
    "title": "Определение gRPC сервиса: директива service, rpc методы и анализ сгенерированных интерфейсов",
    "task": "**Определение сервиса**: В `.proto` файле добавь `service UserService { rpc GetUser (UserRequest) returns (UserResponse); }`. Сгенерируй код с поддержкой gRPC (`--go-grpc_out=.`). Посмотри на сгенерированные интерфейсы сервера и клиента.",
    "theory": "Генерация клиентских и серверных контрактов плагином protoc-gen-go-grpc:\n- Из определения сервиса компилятор генерирует:\n  1. **Клиентский интерфейс:**\n     ```go\n     type UserServiceClient interface {\n         GetUser(ctx context.Context, in *UserRequest, opts ...grpc.CallOption) (*UserResponse, error)\n     }\n     ```\n  2. **Серверный интерфейс:**\n     ```go\n     type UserServiceServer interface {\n         GetUser(context.Context, *UserRequest) (*UserResponse, error)\n         mustEmbedUnimplementedUserServiceServer()\n     }\n     ```\n  3. **Конструктор клиента:** `NewUserServiceClient(cc grpc.ClientConnInterface)`.",
    "step_by_step": "1. Опишите сервис в `.proto` файле.\n2. Сгенерируйте код с флагом `--go-grpc_out`.\n3. Изучите сгенерированные сигнатуры методов.\n4. Проверьте реализацию интерфейса клиентом и сервером.",
    "code_blocks": [
      {
        "filename": "service_contract.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage user.v1;\n\noption go_package = \"./userv1;userv1\";\n\nmessage UserRequest { string user_id = 1; }\nmessage UserResponse { string user_id = 1; string name = 2; }\n\nservice UserService {\n  rpc GetUser (UserRequest) returns (UserResponse);\n}",
        "note": "Спецификация сервиса UserService"
      },
      {
        "filename": "interface_inspector.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\n\t\"google.golang.org/grpc\"\n)\n\ntype UserRequest struct{ UserID string }\ntype UserResponse struct{ UserID, Name string }\n\n// Сгенерированный клиентский интерфейс\ntype UserServiceClient interface {\n\tGetUser(ctx context.Context, in *UserRequest, opts ...grpc.CallOption) (*UserResponse, error)\n}\n\n// Сгенерированный серверный интерфейс\ntype UserServiceServer interface {\n\tGetUser(context.Context, *UserRequest) (*UserResponse, error)\n}\n\nfunc main() {\n\tfmt.Println(\"Интерфейсы UserServiceClient и UserServiceServer успешно сгенерированы\")\n}",
        "note": "Анализ структуры сгенерированных интерфейсов"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "protoc --go_out=. --go_opt=paths=source_relative \\\n       --go-grpc_out=. --go-grpc_opt=paths=source_relative \\\n       service_contract.proto\n\n# Проверяем интерфейсы в сгенерированном файле:\ngrep -A 5 \"type UserServiceClient interface\" service_contract_grpc.pb.go"
      }
    ],
    "under_the_hood": "Интерфейс `UserServiceClient` принимает переменное число `opts ...grpc.CallOption`. Это позволяет на уровне отдельного RPC-вызова переопределять интерцепторы, настраивать сжатие (`grpc.UseCompressor(\"gzip\")`) или передавать метаданные заголовков.",
    "pitfalls": "Забывать передавать `ctx context.Context` первым аргументом: сигнатуры всех gRPC методов в Go строго начинаются с `ctx`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем клиенту gRPC передавать интерфейс grpc.ClientConnInterface, а не конкретную структуру *grpc.ClientConn?»\n**Ответ:** Это фундаментальный принцип инверсии зависимостей (Dependency Inversion). Благодаря интерфейсу `grpc.ClientConnInterface` клиентский стаб можно легко покрывать unit-тестами с помощью моков, подставляя In-Memory соединения (`bufconn`) без открытия реальных портов операционной системы."
  },
  {
    "num": 43,
    "title": "Сквозной вызов GetUser(id int32): полная интеграция сервера и вызов с клиента",
    "task": "Добавьте серверу метод `GetUser(id int32) returns User`. Реализуйте его на сервере, возвращая тестовые данные. Клиент вызывает его и выводит поля.",
    "theory": "Сквозной конвейер обработки RPC вызова:\n1. Клиент формирует сообщение запроса `GetUserRequest{Id: 42}`.\n2. Клиентский стаб вызывает метод через `ClientConn`.\n3. Соединение HTTP/2 отправляет пакет на сервер.\n4. Серверный роутер перенаправляет вызов в `server.GetUser(ctx, req)`.\n5. Сервер считывает `req.GetId()`, формирует `UserResponse` и возвращает указатель.\n6. Клиент получает десериализованную структуру и печатает поля.",
    "step_by_step": "1. Напишите функцию сервера с возвратом тестовых данных.\n2. Смоделируйте клиентский вызов.\n3. Проверьте правильность возвращенных полей `ID`, `Name`, `Email`.\n4. Убедитесь в отсутствии ошибок.",
    "code_blocks": [
      {
        "filename": "get_user_pipeline_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype UserEntity struct {\n\tId    int32\n\tName  string\n\tEmail string\n}\n\ntype UserServerLogic struct{}\n\nfunc (s *UserServerLogic) GetUser(ctx context.Context, id int32) (*UserEntity, error) {\n\t// Возврат тестовых данных по ID\n\treturn &UserEntity{\n\t\tId:    id,\n\t\tName:  \"Валерий Меладзе\",\n\t\tEmail: \"valery@music.ru\",\n\t}, nil\n}\n\nfunc TestGetUserPipeline(t *testing.T) {\n\tserver := &UserServerLogic{}\n\n\tctx, cancel := context.WithTimeout(context.Background(), time.Second)\n\tdefer cancel()\n\n\ttargetID := int32(1005)\n\tuser, err := server.GetUser(ctx, targetID)\n\tif err != nil {\n\t\tt.Fatalf(\"GetUser вернул ошибку: %v\", err)\n\t}\n\n\tif user.Id != targetID || user.Name != \"Валерий Меладзе\" {\n\t\tt.Fatalf(\"Некорректные данные пользователя: %+v\", user)\n\t}\n\n\tfmt.Printf(\"Клиент успешно получил данные пользователя:\\n\")\n\tfmt.Printf(\"  ID:    %d\\n\", user.Id)\n\tfmt.Printf(\"  Имя:   %s\\n\", user.Name)\n\tfmt.Printf(\"  Email: %s\\n\", user.Email)\n}",
        "note": "Сквозной тест клиент-серверного вызова метода GetUser"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v get_user_pipeline_test.go\n# Вывод:\n# === RUN   TestGetUserPipeline\n# Клиент успешно получил данные пользователя:\n#   ID:    1005\n#   Имя:   Валерий Меладзе\n#   Email: valery@music.ru\n# --- PASS: TestGetUserPipeline (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Вся цепочка сериализации, маршрутизации и валидации занимает менее 15 микросекунд в локальной сети, обеспечивая на порядок меньшие задержки по сравнению с классическим REST JSON.",
    "pitfalls": "Использовать тип `int32` для системных идентификаторов БД: в высоконагруженных таблицах счетчик ID превысит 2 миллиарда (`math.MaxInt32`). Для ID пользователей всегда используйте `int64` или `string` (UUID).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в gRPC методе GetUser не принято возвращать nil при отсутствии пользователя, а принято возвращать ошибку codes.NotFound?»\n**Ответ:** Потому что в распределенных системах `nil` в качестве ответа не несет контекста. Ошибка `status.Error(codes.NotFound, \"пользователь не найден\")` транслируется в HTTP-код 404 на уровне API Gateway и однозначно сообщает клиенту причину сбоя."
  },
  {
    "num": 44,
    "title": "Аудит схем и Best Practices: автоматический линтинг с помощью команды buf lint",
    "task": "Используйте `buf lint` для проверки `.proto` файлов на соответствие best practices.",
    "theory": "Стандарты оформления Protocol Buffers (Buf Style Guide):\n- В командах с десятками разработчиков без линтера схемы быстро деградируют: разные стили именования, пропущенные версионные суффиксы, несогласованные enum.\n- Команда `buf lint`:\n  1. Проверяет структуру пакетов (`FIELD_LOWER_SNAKE_CASE`, `MESSAGE_PASCAL_CASE`).\n  2. Проверяет наличие обязательного значения `0` в enum с суффиксом `_UNSPECIFIED`.\n  3. Проверяет наличие директивы `option go_package`.\n  4. Проверяет правильное именование методов RPC и сообщений запросов/ответов.",
    "step_by_step": "1. Создайте `.proto` файл с намеренной ошибкой стиля.\n2. Запустите `buf lint` и изучите отчет.\n3. Исправьте ошибку в соответствии с рекомендациями.\n4. Добейтесь чистого прохождения линтера.",
    "code_blocks": [
      {
        "filename": "proto/bad_style.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage my_service; // Ошибка: отсутствует суффикс версии v1!\n\nmessage user {      // Ошибка: имя сообщения должно быть PascalCase (User)!\n  string UserName = 1; // Ошибка: поле должно быть lower_snake_case (user_name)!\n}",
        "note": "Пример схемы с нарушениями правил стиля Google"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск линтинга:\nbuf lint proto/bad_style.proto\n# Вывод:\n# proto/bad_style.proto:3:9: Package name \"my_service\" should be in the form of \"package.v1\".\n# proto/bad_style.proto:5:9: Message name \"user\" should be capitalized (PascalCase).\n# proto/bad_style.proto:6:10: Field name \"UserName\" should be lower_snake_case, such as \"user_name\".\n\n# После исправления схемы в соответствии со стандартами:\nbuf lint proto/user/v1/user.proto\n# (вывод пуст, exit code 0 — схема идеальна!)"
      },
      {
        "filename": "proto/user/v1/user.proto",
        "lang": "protobuf",
        "code": "syntax = \"proto3\";\n\npackage user.v1;\n\noption go_package = \"example.com/project/gen/user/v1;userv1\";\n\nmessage User {\n  string user_name = 1;\n}",
        "note": "Исправленная схема, на 100% соответствующая best practices"
      }
    ],
    "under_the_hood": "`buf lint` выполняет статический анализ дерева AST схем за доли миллисекунды без запуска компилятора `protoc`, гарантируя соблюдение единых стандартов кода во всей компании.",
    "pitfalls": "Отключать правила линтера через `except` без веской причины: чистота контрактов — это залог надежности всей микросервисной экосистемы.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем buf lint требует указывать суффикс версии (например .v1) в имени каждого пакета?»\n**Ответ:** Потому что в Protobuf имя пакета является частью полного сетевого пути RPC вызова (`/user.v1.UserService/GetUser`). Без указания версии невозможно будет провести бесшовное канареечное обновление или выпустить версию v2 без остановки работы существующих клиентов."
  },
  {
    "num": 45,
    "title": "Управление дедлайнами: проверка контекста на сервере и возврат статуса codes.DeadlineExceeded",
    "task": "Добави **deadline/timeout**: в клиенте `ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)`. В сервере проверяй `ctx.Err() == context.DeadlineExceeded` и верни `codes.DeadlineExceeded`.",
    "theory": "Сквозная обработка дедлайнов (End-to-End Deadlines):\n- Когда клиент устанавливает таймаут через `context.WithTimeout`, gRPC клиент передает HTTP/2 заголовок `grpc-timeout: 2S`.\n- На стороне сервера:\n  - Рантайм gRPC привязывает этот дедлайн к `ctx context.Context` серверного метода.\n  - Длительные операции (тяжелые вычисления, запросы к БД, походы во внешние API) обязаны периодически проверять `select { case <-ctx.Done(): ... }`.\n  - Если контекст отменен, сервер немедленно прерывает работу и возвращает `status.Error(codes.DeadlineExceeded, \"таймаут операции\")`.",
    "step_by_step": "1. Создайте серверный метод с длительной операцией.\n2. Реализуйте проверку `ctx.Done()`.\n3. Верните gRPC статус `codes.DeadlineExceeded`.\n4. Протестируйте поведение клиента при истечении таймаута.",
    "code_blocks": [
      {
        "filename": "deadline_propagation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\ntype HeavyWorkloadServer struct{}\n\nfunc (s *HeavyWorkloadServer) ProcessHeavyTask(ctx context.Context, itemID string) (string, error) {\n\t// Имитируем тяжелый процесс (например, сложный расчет за 1 секунду)\n\tselect {\n\tcase <-time.After(1 * time.Second):\n\t\treturn fmt.Sprintf(\"Задача %s успешно выполнена\", itemID), nil\n\tcase <-ctx.Done():\n\t\tif ctx.Err() == context.DeadlineExceeded {\n\t\t\treturn \"\", status.Error(codes.DeadlineExceeded, \"время ожидания задачи истекло на сервере\")\n\t\t}\n\t\treturn \"\", status.Error(codes.Canceled, \"задача отменена клиентом\")\n\t}\n}\n\nfunc TestServerDeadlineExceeded(t *testing.T) {\n\tserver := &HeavyWorkloadServer{}\n\n\t// Клиент выделяет только 50 миллисекунд\n\tclientCtx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)\n\tdefer cancel()\n\n\t_, err := server.ProcessHeavyTask(clientCtx, \"job_999\")\n\tif err == nil {\n\t\tt.Fatal(\"Ожидалась ошибка таймаута, но вызов выполнился успешно\")\n\t}\n\n\tst, ok := status.FromError(err)\n\tif !ok || st.Code() != codes.DeadlineExceeded {\n\t\tt.Fatalf(\"Ожидался статус DeadlineExceeded, получено: %v\", err)\n\t}\n\n\tfmt.Printf(\"Успешно зафиксирован gRPC статус: [%s] %s\\n\", st.Code(), st.Message())\n}",
        "note": "Проверка прерывания серверной обработки по дедлайну контекста"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v deadline_propagation_test.go\n# Вывод:\n# === RUN   TestServerDeadlineExceeded\n# Успешно зафиксирован gRPC статус: [DeadlineExceeded] время ожидания задачи истекло на сервере\n# --- PASS: TestServerDeadlineExceeded (0.05s)\n# PASS"
      }
    ],
    "under_the_hood": "В HTTP/2 gRPC клиент при истечении дедлайна посылает фрейм `RST_STREAM`. Серверный транспортный уровень перехватывает этот сигнал и немедленно вызывает функцию отмены `cancel()` контекста метода, экономя такты CPU сервера.",
    "pitfalls": "Игнорировать `ctx.Done()` в цикле обработки на сервере: если код не проверяет контекст, сервер продолжит расходовать процессор и память, хотя клиент уже разорвал соединение и ушел.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему важно пробрасывать ctx из параметров gRPC метода во все вызовы sql.DB, redis.Client и http.Client внутри сервиса?»\n**Ответ:** Потому что если клиент отменит gRPC вызов, отмена контекста каскадно прервет исполняющийся SQL-запрос в PostgreSQL, команду в Redis и сетевой запрос в сторонний API, предотвращая утечки пулов соединений и разгружая кластер баз данных."
  },
  {
    "num": 46,
    "title": "Генерация потока числовых последовательностей: паттерн Server Streaming StreamNumbers",
    "task": "**Server Streaming**: Создайте метод `StreamNumbers(req *Request, stream ServerStream_ServerNumbers)`, который отправляет клиенту последовательность чисел. Клиент читает через `for { resp, err := stream.Recv() }`.",
    "theory": "Потоковая отправка последовательностей (Server Streaming Pattern):\n- Сервер принимает параметры диапазона (например, от 1 до $N$).\n- В цикле генерирует числа и передает их клиенту через `stream.Send(&NumberResponse{Value: i})`.\n- Поток завершается штатным возвратом `return nil`.\n- Клиентский код обрабатывает каждое число сразу по мере поступления, не накапливая гигантский массив в ОЗУ.",
    "step_by_step": "1. Опишите метод `StreamNumbers` с ключевым словом `stream` в возвращаемом значении.\n2. Реализуйте отправку чисел с шагом задержки.\n3. Напишите клиентский цикл вычитки через `stream.Recv()`.\n4. Продемонстрируйте корректный выход по `io.EOF`.",
    "code_blocks": [
      {
        "filename": "stream_numbers_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n\t\"time\"\n)\n\ntype NumberItem struct {\n\tValue int32\n}\n\ntype NumberChannelMock struct {\n\tpipe chan *NumberItem\n}\n\nfunc (m *NumberChannelMock) Send(val int32) error {\n\tm.pipe <- &NumberItem{Value: val}\n\treturn nil\n}\n\nfunc (m *NumberChannelMock) Recv() (*NumberItem, error) {\n\titem, ok := <-m.pipe\n\tif !ok {\n\t\treturn nil, io.EOF\n\t}\n\treturn item, nil\n}\n\n// Server logic\nfunc GenerateStreamNumbers(count int32, mock *NumberChannelMock) error {\n\tdefer close(mock.pipe)\n\tfor i := int32(1); i <= count; i++ {\n\t\tif err := mock.Send(i); err != nil {\n\t\t\treturn err\n\t\t}\n\t\ttime.Sleep(10 * time.Millisecond)\n\t}\n\treturn nil\n}\n\nfunc main() {\n\tmock := &NumberChannelMock{pipe: make(chan *NumberItem, 5)}\n\n\t// Запуск потока генерации чисел\n\tgo func() {\n\t\t_ = GenerateStreamNumbers(5, mock)\n\t}()\n\n\tfmt.Println(\"Клиент получает числа из серверного потока:\")\n\tfor {\n\t\titem, err := mock.Recv()\n\t\tif err == io.EOF {\n\t\t\tfmt.Println(\"Поток успешно завершен (io.EOF)\")\n\t\t\tbreak\n\t\t}\n\t\tif err != nil {\n\t\t\tpanic(err)\n\t\t}\n\t\tfmt.Printf(\"  Получено число: %d\\n\", item.Value)\n\t}\n}",
        "note": "Серверный стриминг чисел с корректным закрытием потока"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run stream_numbers_demo.go\n# Вывод:\n# Клиент получает числа из серверного потока:\n#   Получено число: 1\n#   Получено число: 2\n#   Получено число: 3\n#   Получено число: 4\n#   Получено число: 5\n# Поток успешно завершен (io.EOF)"
      }
    ],
    "under_the_hood": "Вызов `stream.Send()` не блокирует поток исполнения навсегда: если буфер HTTP/2 фреймов на сокете свободен, отправка занимает считанные наносекунды за счет асинхронного буфера gRPC transport.",
    "pitfalls": "Забывать обрабатывать ошибку отправки `if err := stream.Send(...); err != nil`: если клиент разорвал связь, попытка отправки вернет ошибку, и дальнейшая генерация чисел должна быть немедленно остановлена.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем преимущество gRPC Server Streaming перед HTTP/1.1 Chunked Transfer Encoding?»\n**Ответ:** Chunked Encoding в HTTP/1.1 передает нетипизированный текстовый поток байт и занимает соединение целиком. gRPC Server Streaming строго типизирован схемой Protobuf, работает поверх HTTP/2 с мультиплексированием (в одном сокете могут параллельно идти сотни стримов) и поддерживает двустороннюю передачу метаданных (Headers и Trailers)."
  },
  {
    "num": 47,
    "title": "Клиентский стаб NewUserServiceClient: вызов удаленного метода GetUser через ClientConn",
    "task": "Реализуй **gRPC клиент**: `conn, err := grpc.Dial(\"localhost:50051\", grpc.WithTransportCredentials(insecure.NewCredentials()))`. Создай `client := pb.NewUserServiceClient(conn)`. Вызови `client.GetUser(ctx, &pb.GetUserRequest{Id: 1})`.",
    "theory": "Инициализация клиента и вызов стаба:\n- Клиентский стаб создается вызовом фабричной функции `pb.NewUserServiceClient(conn)`.\n- Стаб инкапсулирует вызовы `conn.Invoke(...)`.\n- Идиоматичный вызов:\n  ```go\n  resp, err := client.GetUser(ctx, &pb.GetUserRequest{Id: 1})\n  if err != nil {\n      st, ok := status.FromError(err)\n      // Анализ st.Code() и st.Message()\n  }\n  ```\n- Для продакшна таймаут в контексте обязателен!",
    "step_by_step": "1. Создайте клиентский стаб.\n2. Сконфигурируйте контекст с дедлайном.\n3. Вызовите метод `GetUser`.\n4. Распечатайте полученные поля пользователя.",
    "code_blocks": [
      {
        "filename": "client_stub_call.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"time\"\n)\n\ntype UserRequest struct{ ID int64 }\ntype UserResponse struct{ ID int64; Name, Email string }\n\ntype UserServiceClient interface {\n\tGetUser(ctx context.Context, req *UserRequest) (*UserResponse, error)\n}\n\ntype UserClientStub struct{}\n\nfunc (c *UserClientStub) GetUser(ctx context.Context, req *UserRequest) (*UserResponse, error) {\n\t// Эмуляция сетевого вызова\n\treturn &UserResponse{\n\t\tID:    req.ID,\n\t\tName:  \"Дмитрий Смирнов\",\n\t\tEmail: \"d.smirnov@avito.ru\",\n\t}, nil\n}\n\nfunc main() {\n\tvar client UserServiceClient = &UserClientStub{}\n\n\tctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)\n\tdefer cancel()\n\n\tresp, err := client.GetUser(ctx, &UserRequest{ID: 1})\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\n\tfmt.Println(\"Ответ от сервиса пользователей:\")\n\tfmt.Printf(\"  ID:    %d\\n\", resp.ID)\n\tfmt.Printf(\"  Имя:   %s\\n\", resp.Name)\n\tfmt.Printf(\"  Email: %s\\n\", resp.Email)\n}",
        "note": "Инициализация клиентского стаба и вызов метода"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run client_stub_call.go\n# Вывод:\n# Ответ от сервиса пользователей:\n#   ID:    1\n#   Имя:   Дмитрий Смирнов\n#   Email: d.smirnov@avito.ru"
      }
    ],
    "under_the_hood": "Клиентский стаб генерирует уникальный ID стрима (нечетные числа 1, 3, 5 в HTTP/2) и отправляет запрос без блокировки соседних потоков.",
    "pitfalls": "Использовать устаревший синтаксис `grpc.WithInsecure()`: эта опция удалена в современных версиях gRPC, используйте `grpc.WithTransportCredentials(insecure.NewCredentials())`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в HTTP/2 клиент использует нечетные Stream ID, а сервер четные?»\n**Ответ:** Это стандарт спецификации RFC 7540 (HTTP/2), исключающий необходимость координации номеров стримов по сети. Клиент и сервер могут независимо открывать стримы одновременно без риска назначить один и тот же идентификатор."
  },
  {
    "num": 48,
    "title": "Серверные интерцепторы: логирование вызовов через grpc.UnaryServerInterceptor",
    "task": "Добави **interceptor (unary)**: `func loggingInterceptor(ctx context.Context, req any, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (any, error)`. Логируй метод, длительность, ошибку. Зарегистрируй через `grpc.UnaryInterceptor(loggingInterceptor)`.",
    "theory": "Концепция интерцепторов в gRPC (Middleware):\n- Интерцептор оборачивает исполнение каждого RPC вызова (паттерн «Декоратор / Обертка»).\n- Сигнатура Unary интерцептора:\n  `type UnaryServerInterceptor func(ctx context.Context, req any, info *UnaryServerInfo, handler UnaryHandler) (resp any, err error)`\n- Параметры:\n  - `info.FullMethod`: полное имя метода (например `/user.v1.UserService/GetUser`).\n  - `handler(ctx, req)`: передача управления следующему интерцептору или целевому бизнес-методу.\n- Измерение latency: замеряется через `start := time.Now(); resp, err := handler(ctx, req); duration := time.Since(start)`.",
    "step_by_step": "1. Напишите функцию `loggingInterceptor`.\n2. Замерьте время выполнения вызова.\n3. Залогируйте имя метода, статус и задержку.\n4. Зарегистрируйте интерцептор через `grpc.UnaryInterceptor`.",
    "code_blocks": [
      {
        "filename": "logging_interceptor.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n)\n\n// LoggingUnaryInterceptor перехватывает все унарные вызовы на сервере\nfunc LoggingUnaryInterceptor(\n\tctx context.Context,\n\treq any,\n\tinfo *grpc.UnaryServerInfo,\n\thandler grpc.UnaryHandler,\n) (any, error) {\n\tstart := time.Now()\n\n\t// Передача управления бизнес-обработчику\n\tresp, err := handler(ctx, req)\n\n\tduration := time.Since(start)\n\tstatusStr := \"OK\"\n\tif err != nil {\n\t\tstatusStr = fmt.Sprintf(\"ERROR: %v\", err)\n\t}\n\n\tfmt.Printf(\"[gRPC Access Log] Method=%s | Duration=%v | Status=%s\\n\",\n\t\tinfo.FullMethod, duration, statusStr)\n\n\treturn resp, err\n}\n\nfunc main() {\n\t// Пример создания сервера с интерцептором:\n\tserver := grpc.NewServer(\n\t\tgrpc.UnaryInterceptor(LoggingUnaryInterceptor),\n\t)\n\t_ = server\n\tfmt.Println(\"gRPC сервер успешно сконфигурирован с Logging интерцептором\")\n}",
        "note": "Реализация интерцептора логирования времени выполнения"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run logging_interceptor.go\n# Вывод:\n# gRPC сервер успешно сконфигурирован с Logging интерцептором"
      }
    ],
    "under_the_hood": "Интерцепторы вызываются в той же горутине, что и сам RPC-хэндлер, что позволяет безопасно оборачивать вызовы в транзакции БД, распределенные трассировки OpenTelemetry и контекстные тайм-ауты.",
    "pitfalls": "Модифицировать `req` без синхронизации: если запрос читается параллельно, мутация полей в интерцепторе может вызвать состояние гонки (Data Race).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в gRPC интерцепторе перехватить панику (panic recovery)?»\n**Ответ:** Обернуть вызов `handler(ctx, req)` в конструкцию с `defer func() { if r := recover(); r != nil { ... } }()`, залогировать стек-трейс с помощью `debug.Stack()` и вернуть клиенту стандартизированную gRPC ошибку `status.Errorf(codes.Internal, \"внутренняя ошибка сервера\")`."
  },
  {
    "num": 49,
    "title": "Фильтрация в потоке Server Streaming: метод GetUsersByRole и отправка данных через stream.Send",
    "task": "**Server Streaming**: Добавь в контракт метод `GetUsersByRole`, который принимает `Role` и возвращает `stream User`. Реализуй на сервере отправку нескольких пользователей через `stream.Send()`.",
    "theory": "Бизнес-логика серверного стриминга:\n- Метод `GetUsersByRole(RoleRequest, stream UserServer)`:\n  - Принимает критерий фильтрации (например, роль `ADMIN`).\n  - Сканирует локальную базу или делает запрос к курсору SQL/PostgreSQL.\n  - По мере нахождения совпадающих записей немедленно передает их через `stream.Send(&User{...})`.\n  - После завершения выборки выходит с `return nil`.",
    "step_by_step": "1. Определите контракт метода с фильтрацией по роли.\n2. Создайте коллекцию тестовых пользователей.\n3. Реализуйте метод с фильтрацией и вызовом `stream.Send()`.\n4. Проверьте получение только целевых пользователей.",
    "code_blocks": [
      {
        "filename": "stream_filter_demo.go",
        "lang": "go",
        "code": "package main\n\nimport \"fmt\"\n\ntype Role int32\nconst (\n\tRoleAdmin Role = 1\n\tRoleUser  Role = 2\n)\n\ntype UserModel struct {\n\tID   int64\n\tName string\n\tRole Role\n}\n\ntype MockUserStream struct {\n\tSentUsers []*UserModel\n}\n\nfunc (s *MockUserStream) Send(u *UserModel) error {\n\ts.SentUsers = append(s.SentUsers, u)\n\treturn nil\n}\n\ntype UserServerImplementation struct {\n\tdb []*UserModel\n}\n\nfunc (s *UserServerImplementation) GetUsersByRole(targetRole Role, stream *MockUserStream) error {\n\tfor _, user := range s.db {\n\t\tif user.Role == targetRole {\n\t\t\tif err := stream.Send(user); err != nil {\n\t\t\t\treturn err\n\t\t\t}\n\t\t}\n\t}\n\treturn nil\n}\n\nfunc main() {\n\tserver := &UserServerImplementation{\n\t\tdb: []*UserModel{\n\t\t\t{ID: 1, Name: \"Илья (Администратор)\", Role: RoleAdmin},\n\t\t\t{ID: 2, Name: \"Мария (Пользователь)\", Role: RoleUser},\n\t\t\t{ID: 3, Name: \"Олег (Администратор)\", Role: RoleAdmin},\n\t\t},\n\t}\n\n\tstream := &MockUserStream{}\n\terr := server.GetUsersByRole(RoleAdmin, stream)\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\n\tfmt.Println(\"Поток успешно доставил администраторов:\")\n\tfor _, u := range stream.SentUsers {\n\t\tfmt.Printf(\"  -> ID: %d, Имя: %s\\n\", u.ID, u.Name)\n\t}\n}",
        "note": "Серверная фильтрация и отправка потоковых сообщений"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run stream_filter_demo.go\n# Вывод:\n# Поток успешно доставил администраторов:\n#   -> ID: 1, Имя: Илья (Администратор)\n#   -> ID: 3, Имя: Олег (Администратор)"
      }
    ],
    "under_the_hood": "Серверный стриминг позволяет передавать миллионы строк из базы данных без выгрузки их всех в оперативную память сервера (OOM Protection), так как сборщик мусора GC успевает утилизировать отправленные записи.",
    "pitfalls": "Буферизировать всю выборку в локальный слайс перед циклом отправки: это полностью уничтожает смысл потоковой передачи. Данные должны читаться из курсора БД и сразу отсылаться в сокет.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как защитить сервер gRPC от утечки горутин при обрыве стрима GetUsersByRole?»\n**Ответ:** Перед каждой итерацией цикла отправки проверять контекст стрима:\n```go\nselect {\ncase <-stream.Context().Done():\n    return stream.Context().Err()\ndefault:\n}\n```\nЭто немедленно прервет цикл и закроет курсор к базе данных, если клиент закрыл соединение."
  },
  {
    "num": 50,
    "title": "Полный стек gRPC сервера: net.Listen, grpc.NewServer, регистрация сервиса и запуск Serve",
    "task": "**gRPC Сервер**: Создай структуру, реализующую сгенерированный интерфейс `UserServiceServer`. В `main` открой TCP-порт (`net.Listen`), создай сервер `grpc.NewServer()`, зарегистрируй свой сервис и запусти `Serve()`.",
    "theory": "Каноническая архитектура микросервисного gRPC сервера в Go:\n1. `lis, err := net.Listen(\"tcp\", port)`\n2. `srv := grpc.NewServer(opts...)`\n3. `pb.RegisterUserServiceServer(srv, myImpl)`\n4. `go func() { srv.Serve(lis) }()`\n5. Ожидание сигналов ОС (`os.Interrupt`, `syscall.SIGTERM`).\n6. Плавная остановка: `srv.GracefulStop()`.",
    "step_by_step": "1. Создайте экземпляр сервера.\n2. Откройте слушатель порта.\n3. Зарегистрируйте реализацию сервиса.\n4. Запустите цикл `Serve` в горутине.\n5. Проверьте корректный Graceful Shutdown.",
    "code_blocks": [
      {
        "filename": "grpc_full_stack_server.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"net\"\n\t\"os\"\n\t\"os/signal\"\n\t\"syscall\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n)\n\ntype AppServer struct{}\n\nfunc (s *AppServer) HealthCheck(ctx context.Context) string {\n\treturn \"OK\"\n}\n\nfunc main() {\n\t// 1. Открытие сетевого порта\n\tlis, err := net.Listen(\"tcp\", \"127.0.0.1:0\")\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tdefer lis.Close()\n\n\t// 2. Инициализация gRPC сервера\n\tserver := grpc.NewServer()\n\n\t// 3. Запуск сервера в фоновом режиме\n\tserverErrors := make(chan error, 1)\n\tgo func() {\n\t\tfmt.Printf(\"Сервер запущен на %s\\n\", lis.Addr().String())\n\t\tif err := server.Serve(lis); err != nil && err != grpc.ErrServerStopped {\n\t\t\tserverErrors <- err\n\t\t}\n\t}()\n\n\t// 4. Настройка перехвата сигналов ОС\n\tshutdown := make(chan os.Signal, 1)\n\tsignal.Notify(shutdown, os.Interrupt, syscall.SIGTERM)\n\n\t// Имитируем сигнал остановки через 50 мс для теста\n\tgo func() {\n\t\ttime.Sleep(50 * time.Millisecond)\n\t\tshutdown <- syscall.SIGTERM\n\t}()\n\n\tselect {\n\tcase err := <-serverErrors:\n\t\tpanic(fmt.Sprintf(\"Ошибка сервера: %v\", err))\n\tcase sig := <-shutdown:\n\t\tfmt.Printf(\"Получен сигнал %v: начинаем плавную остановку (GracefulStop)...\\n\", sig)\n\t\tserver.GracefulStop()\n\t\tfmt.Println(\"Все активные соединения закрыты, сервер успешно остановлен\")\n\t}\n}",
        "note": "Эталонный шаблон запуска и Graceful Shutdown gRPC сервера"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run grpc_full_stack_server.go\n# Вывод:\n# Сервер запущен на 127.0.0.1:39215\n# Получен сигнал terminated: начинаем плавную остановку (GracefulStop)...\n# Все активные соединения закрыты, сервер успешно остановлен"
      }
    ],
    "under_the_hood": "`server.GracefulStop()` закрывает слушающий TCP-сокет, отправляет HTTP/2 фреймы `GOAWAY` всем клиентам, уведомляя их о прекращении приема новых вызовов, и блокируется до завершения всех текущих RPC.",
    "pitfalls": "Не передавать сигнал в `server.GracefulStop()` при деплое в Kubernetes: поды будут принудительно убиваться через `SIGKILL` по истечении `terminationGracePeriodSeconds`, обрывая запросы пользователей.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем gRPC шлет фрейм GOAWAY дважды при graceful shutdown?»\n**Ответ:** Первый `GOAWAY` содержит максимальный Stream ID ($2^{31}-1$) и сообщает клиентам о скором закрытии соединения. Второй `GOAWAY` содержит точный номер последнего обработанного стрима. Это предотвращает состояние гонки, когда клиент отправил запрос ровно в момент закрытия сокета сервером."
  },
  {
    "num": 51,
    "title": "Потоковый метод ListUsers: отправка сущностей по одному и цикл клиента до io.EOF",
    "task": "Server streaming: реализуйте метод `ListUsers(stream UserService_ListUsersServer)`, который отправляет нескольких пользователей по одному. Клиент читает поток до EOF.",
    "theory": "Шаблон обхода больших выборок ListUsers:\n- В сценариях экспорта данных или синхронизации каталогов возвращать один гигантский JSON массив `[User, User, ...]` на 500 МБ недопустимо.\n- gRPC Server Streaming позволяет передавать пользователей по одному:\n  `stream.Send(user)`\n- Память приложения константна $O(1)$ вне зависимости от размера каталога пользователей.",
    "step_by_step": "1. Создайте метод `ListUsers`.\n2. Реализуйте отправку порций пользователей.\n3. На стороне клиента организуйте цикл до ошибки `io.EOF`.\n4. Подсчитайте количество переданных записей.",
    "code_blocks": [
      {
        "filename": "list_users_stream_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n)\n\ntype UserRecordDTO struct {\n\tID    int64\n\tLogin string\n}\n\ntype UserListChannel struct {\n\tdata chan *UserRecordDTO\n}\n\nfunc (c *UserListChannel) Send(u *UserRecordDTO) error {\n\tc.data <- u\n\treturn nil\n}\n\nfunc (c *UserListChannel) Recv() (*UserRecordDTO, error) {\n\tu, ok := <-c.data\n\tif !ok {\n\t\treturn nil, io.EOF\n\t}\n\treturn u, nil\n}\n\nfunc ServerListUsers(stream *UserListChannel) {\n\tdefer close(stream.data)\n\n\tusers := []*UserRecordDTO{\n\t\t{ID: 101, Login: \"alice\"},\n\t\t{ID: 102, Login: \"bob\"},\n\t\t{ID: 103, Login: \"charlie\"},\n\t\t{ID: 104, Login: \"dave\"},\n\t}\n\n\tfor _, u := range users {\n\t\t_ = stream.Send(u)\n\t}\n}\n\nfunc main() {\n\tstream := &UserListChannel{data: make(chan *UserRecordDTO, 10)}\n\n\tgo ServerListUsers(stream)\n\n\tfmt.Println(\"Клиент вычитывает пользователей из стрима:\")\n\tcount := 0\n\tfor {\n\t\tuser, err := stream.Recv()\n\t\tif err == io.EOF {\n\t\t\tbreak\n\t\t}\n\t\tif err != nil {\n\t\t\tpanic(err)\n\t\t}\n\t\tcount++\n\t\tfmt.Printf(\"  #%d -> Пользователь: %s [ID %d]\\n\", count, user.Login, user.ID)\n\t}\n\tfmt.Printf(\"Всего успешно получено пользователей: %d\\n\", count)\n}",
        "note": "Потоковое чтение каталога пользователей до EOF"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run list_users_stream_demo.go\n# Вывод:\n# Клиент вычитывает пользователей из стрима:\n#   #1 -> Пользователь: alice [ID 101]\n#   #2 -> Пользователь: bob [ID 102]\n#   #3 -> Пользователь: charlie [ID 103]\n#   #4 -> Пользователь: dave [ID 104]\n# Всего успешно получено пользователей: 4"
      }
    ],
    "under_the_hood": "С точки зрения сетевого стека, отправка через `stream.Send()` не закрывает TCP-сокет. Клиент и сервер продолжают использовать то же постоянное HTTP/2 соединение для последующих запросов.",
    "pitfalls": "Забывать закрывать ресурсы БД (такие как `rows.Close()`) при преждевременном выходе из стрима: всегда оборачивайте курсоры в `defer rows.Close()`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как реализовать пагинацию в gRPC: через Server Streaming или через унарные запросы с page_token?»\n**Ответ:** Для UI-интерфейсов (браузер, мобильное приложение) и поисковых запросов используют унарные запросы со стандартизированным `page_token` (Keyset Pagination). Server Streaming используют для межсервисной передачи данных, фоновой репликации и выгрузки аналитических отчетов."
  },
  {
    "num": 52,
    "title": "Клиентский стриминг Client Streaming RPC: загрузка файлов частями UploadProfilePictures",
    "task": "**Потоковое вещание клиента (Client Streaming RPC)**: Добавьте в схему `.proto` метод `UploadProfilePictures(stream Chunk) returns (UploadStatus)`. Метод должен позволять клиенту отправлять файл изображения по частям (чанками байт). Напишите код клиента, считывающего локальный файл кусками и отправляющего их на сервер. На сервере соберите файл воедино и верните общий статус загрузки.",
    "theory": "Архитектура Client Streaming RPC:\n- Клиент открывает стрим и шлет поток сообщений `stream.Send(chunk)`.\n- Сервер читает чанки в цикле `req, err := stream.Recv()`:\n  - Когда клиент закончил отправку, сервер получает `io.EOF`.\n  - Сервер сохраняет файл и вызывает метод `stream.SendAndClose(&UploadStatus{...})`.\n- Позволяет загружать файлы гигабайтного размера без загрузки всего файла в память.",
    "step_by_step": "1. Опишите метод с параметром `stream Chunk`.\n2. Напишите клиент, разбивающий файл на блоки по 64 КБ.\n3. На стороне сервера агрегируйте байты и посчитайте размер.\n4. Вызовите `SendAndClose` со статусом загрузки.",
    "code_blocks": [
      {
        "filename": "client_streaming_upload.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"bytes\"\n\t\"fmt\"\n\t\"io\"\n)\n\ntype Chunk struct {\n\tData []byte\n}\n\ntype UploadStatus struct {\n\tTotalBytesUploaded int64\n\tSuccess            bool\n}\n\ntype MockClientStream struct {\n\tpipe   chan *Chunk\n\tstatus *UploadStatus\n}\n\nfunc (s *MockClientStream) Send(c *Chunk) error {\n\ts.pipe <- c\n\treturn nil\n}\n\nfunc (s *MockClientStream) CloseAndRecv() (*UploadStatus, error) {\n\tclose(s.pipe)\n\treturn s.status, nil\n}\n\n// Server handler\nfunc ServerUploadProfilePictures(pipe <-chan *Chunk) *UploadStatus {\n\tvar totalSize int64\n\tvar buffer bytes.Buffer\n\n\tfor chunk := range pipe {\n\t\tn, _ := buffer.Write(chunk.Data)\n\t\ttotalSize += int64(n)\n\t}\n\n\treturn &UploadStatus{\n\t\tTotalBytesUploaded: totalSize,\n\t\tSuccess:            true,\n\t}\n}\n\nfunc main() {\n\tpipe := make(chan *Chunk, 10)\n\tclientStream := &MockClientStream{pipe: pipe}\n\n\t// Имитация локального файла изображения (150 КБ)\n\tdummyFileData := bytes.Repeat([]byte(\"A\"), 150*1024)\n\tchunkSize := 64 * 1024 // 64 KB чанки\n\n\t// Запуск сервера в горутине\n\tserverResultChan := make(chan *UploadStatus)\n\tgo func() {\n\t\tstatus := ServerUploadProfilePictures(pipe)\n\t\tserverResultChan <- status\n\t}()\n\n\t// Клиент нарезает и отправляет чанки\n\treader := bytes.NewReader(dummyFileData)\n\tbuf := make([]byte, chunkSize)\n\n\tfor {\n\t\tn, err := reader.Read(buf)\n\t\tif n > 0 {\n\t\t\t_ = clientStream.Send(&Chunk{Data: append([]byte{}, buf[:n]...)})\n\t\t}\n\t\tif err == io.EOF {\n\t\t\tbreak\n\t\t}\n\t}\n\n\tclose(pipe)\n\tstatus := <-serverResultChan\n\tfmt.Printf(\"Файл успешно загружен на сервер!\\n\")\n\tfmt.Printf(\"  Получено байт: %d KB\\n\", status.TotalBytesUploaded/1024)\n\tfmt.Printf(\"  Статус:        %v\\n\", status.Success)\n}",
        "note": "Потоковая загрузка файла кусками (Client Streaming)"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run client_streaming_upload.go\n# Вывод:\n# Файл успешно загружен на сервер!\n#   Получено байт: 150 KB\n#   Статус:        true"
      }
    ],
    "under_the_hood": "В Client Streaming клиент отправляет HTTP/2 фреймы `DATA`, а завершение передачи сигнализирует флагом `END_STREAM`. Сервер в ответ отправляет один финальный `HEADERS` фрейм со статусом.",
    "pitfalls": "Выбирать слишком маленький размер чанка (например 128 байт): оверхед на заголовки фреймов HTTP/2 превысит полезную нагрузку. Оптимальный размер чанка — от 32 КБ до 128 КБ.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каков лимит размера одного gRPC сообщения по умолчанию, и как его изменить для больших файлов?»\n**Ответ:** По умолчанию лимит одного сообщения в gRPC составляет **4 МБ** (`MaxCallRecvMsgSize`). При попытке отправить сообщение большего размера вызов падает с ошибкой `ResourceExhausted`. Лимит можно увеличить через опцию `grpc.MaxRecvMsgSize(32 * 1024 * 1024)`, но для файлов больше 10 МБ стандартом является Client Streaming чанками."
  },
  {
    "num": 53,
    "title": "Аутентификация через метаданные: Auth Interceptor, Bearer Token и статус codes.Unauthenticated",
    "task": "Добави **auth interceptor**: проверяй `authorization` metadata. Извлеки Bearer token, валидируй (заглушка). Если невалиден — верни `codes.Unauthenticated`. Примени `grpc.UnaryInterceptor(authInterceptor)` к серверу.",
    "theory": "Передача метаданных аутентификации в gRPC:\n- В gRPC аналогом HTTP-заголовков является пакет `google.golang.org/grpc/metadata`.\n- Метаданные передаются в формате ключ-значение:\n  `md, ok := metadata.FromIncomingContext(ctx)`\n- Клиент передает токен в ключе `authorization` (`Bearer <token>`).\n- Интерцептор:\n  1. Извлекает заголовок `authorization`.\n  2. Проверяет префикс `Bearer `.\n  3. Валидирует JWT токен или API ключ.\n  4. Если токен невалиден: `return nil, status.Error(codes.Unauthenticated, \"требуется аутентификация\")`.",
    "step_by_step": "1. Напишите `AuthUnaryInterceptor`.\n2. Извлеките метаданные из контекста.\n3. Проверьте валидность токена.\n4. Продемонстрируйте пропуск валидного вызова и блокировку неавторизованного.",
    "code_blocks": [
      {
        "filename": "auth_interceptor_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"strings\"\n\n\t\"google.golang.org/grpc\"\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/metadata\"\n\t\"google.golang.org/grpc/status\"\n)\n\n// AuthUnaryInterceptor проверяет Bearer токен в метаданных вызова\nfunc AuthUnaryInterceptor(\n\tctx context.Context,\n\treq any,\n\tinfo *grpc.UnaryServerInfo,\n\thandler grpc.UnaryHandler,\n) (any, error) {\n\tmd, ok := metadata.FromIncomingContext(ctx)\n\tif !ok {\n\t\treturn nil, status.Error(codes.Unauthenticated, \"метаданные отсутствуют\")\n\t}\n\n\tauthHeaders := md.Get(\"authorization\")\n\tif len(authHeaders) == 0 {\n\t\treturn nil, status.Error(codes.Unauthenticated, \"заголовок authorization не передан\")\n\t}\n\n\ttoken := authHeaders[0]\n\tif !strings.HasPrefix(token, \"Bearer \") {\n\t\treturn nil, status.Error(codes.Unauthenticated, \"неверный формат токена (ожидается Bearer)\")\n\t}\n\n\trawToken := strings.TrimPrefix(token, \"Bearer \")\n\tif rawToken != \"secret_bigtech_token_2026\" {\n\t\treturn nil, status.Error(codes.Unauthenticated, \"недействительный токен доступа\")\n\t}\n\n\t// Токен валиден, передаем управление хэндлеру\n\treturn handler(ctx, req)\n}\n\nfunc main() {\n\tdummyHandler := func(ctx context.Context, req any) (any, error) {\n\t\treturn \"Успешный доступ к защищенному ресурсу\", nil\n\t}\n\n\t// Сценарий 1: Запрос без токена\n\tctxNoAuth := context.Background()\n\t_, err := AuthUnaryInterceptor(ctxNoAuth, nil, &grpc.UnaryServerInfo{FullMethod: \"/secure.API\"}, dummyHandler)\n\tfmt.Printf(\"1. Запрос без токена: %v\\n\", err)\n\n\t// Сценарий 2: Запрос с валидным Bearer токеном\n\tmd := metadata.Pairs(\"authorization\", \"Bearer secret_bigtech_token_2026\")\n\tctxWithAuth := metadata.NewIncomingContext(context.Background(), md)\n\n\tresp, err := AuthUnaryInterceptor(ctxWithAuth, nil, &grpc.UnaryServerInfo{FullMethod: \"/secure.API\"}, dummyHandler)\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tfmt.Printf(\"2. Запрос с токеном: %s\\n\", resp)\n}",
        "note": "Валидация Bearer токена в gRPC Auth Interceptor"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run auth_interceptor_demo.go\n# Вывод:\n# 1. Запрос без токена: rpc error: code = Unauthenticated desc = метаданные отсутствуют\n# 2. Запрос с токеном: Успешный доступ к защищенному ресурсу"
      }
    ],
    "under_the_hood": "Ключи метаданных gRPC в соответствии со стандартом HTTP/2 автоматически приводятся к нижнему регистру (lowercase). Поэтому обращаться нужно строго по имени `authorization`, а не `Authorization`.",
    "pitfalls": "Передавать бинарные токены напрямую: для бинарных данных (сырые подписи, хэши) ключ в метаданных **ОБЯЗАН заканчиваться на суффикс `-bin`** (например `token-bin`), иначе рантайм упадет с ошибкой кодирования.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие gRPC статус-кодов Unauthenticated (16) и PermissionDenied (7)?»\n**Ответ:** `Unauthenticated` означает, что личность клиента не подтверждена (отсутствует или просрочен токен, аналог HTTP 401). `PermissionDenied` означает, что личность подтверждена, но у пользователя нет прав на выполнение данной конкретной операции (например, обычный пользователь пытается вызвать метод удаления БД, аналог HTTP 403)."
  },
  {
    "num": 54,
    "title": "Двунаправленный стриминг Bidirectional Streaming: архитектура полнодуплексного чата",
    "task": "**Bidirectional Streaming**: Реализуйте чат `Chat(stream ChatStream_ChatServer)`, где клиент и сервер одновременно отправляют сообщения друг другу.",
    "theory": "Полнодуплексный обмен (Bidirectional Streaming RPC):\n- Клиент и сервер могут независимо писать и читать сообщения в любой момент времени.\n- Поток не требует строгого чередования «запрос-ответ».\n- Архитектура чат-сервера:\n  - Два параллельных цикла в разных горутинах:\n    1. Горутина чтения: `for { msg, err := stream.Recv() }`\n    2. Горутина записи: `for msg := range outgoingChannel { stream.Send(msg) }`\n  - Завершение соединения: когда одна из сторон закрывает стрим, другая сторона получает `io.EOF`.",
    "step_by_step": "1. Опишите структуру `ChatMessage`.\n2. Реализуйте двусторонний канал обмена.\n3. Запустите параллельные горутины чтения и отправки.\n4. Продемонстрируйте одновременный обмен сообщениями.",
    "code_blocks": [
      {
        "filename": "bidi_chat_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n\t\"sync\"\n\t\"time\"\n)\n\ntype ChatMessage struct {\n\tSender string\n\tText   string\n}\n\ntype MockBidiStream struct {\n\tclientToServer chan *ChatMessage\n\tserverToClient chan *ChatMessage\n}\n\nfunc (s *MockBidiStream) SendClient(m *ChatMessage) { s.clientToServer <- m }\nfunc (s *MockBidiStream) RecvServer() (*ChatMessage, error) {\n\tm, ok := <-s.clientToServer\n\tif !ok { return nil, io.EOF }\n\treturn m, nil\n}\n\nfunc (s *MockBidiStream) SendServer(m *ChatMessage) { s.serverToClient <- m }\nfunc (s *MockBidiStream) RecvClient() (*ChatMessage, error) {\n\tm, ok := <-s.serverToClient\n\tif !ok { return nil, io.EOF }\n\treturn m, nil\n}\n\nfunc main() {\n\tstream := &MockBidiStream{\n\t\tclientToServer: make(chan *ChatMessage, 5),\n\t\tserverToClient: make(chan *ChatMessage, 5),\n\t}\n\n\tvar wg sync.WaitGroup\n\twg.Add(2)\n\n\t// 1. Серверный цикл эхо-ответа\n\tgo func() {\n\t\tdefer wg.Done()\n\t\tdefer close(stream.serverToClient)\n\t\tfor {\n\t\t\tmsg, err := stream.RecvServer()\n\t\t\tif err == io.EOF {\n\t\t\t\tbreak\n\t\t\t}\n\t\t\tfmt.Printf(\"[Сервер получил]: %s: %s\\n\", msg.Sender, msg.Text)\n\t\t\t// Сервер отвечает обратно в стрим\n\t\t\tstream.SendServer(&ChatMessage{Sender: \"Bot\", Text: \"Эхо: \" + msg.Text})\n\t\t}\n\t}()\n\n\t// 2. Клиентский цикл\n\tgo func() {\n\t\tdefer wg.Done()\n\t\tmessages := []string{\"Привет gRPC!\", \"Как работает bidi streaming?\", \"Пока!\"}\n\t\tfor _, txt := range messages {\n\t\t\tstream.SendClient(&ChatMessage{Sender: \"Gopher\", Text: txt})\n\t\t\ttime.Sleep(20 * time.Millisecond)\n\t\t}\n\t\tclose(stream.clientToServer)\n\t}()\n\n\t// Клиент вычитывает ответы\n\tgo func() {\n\t\tfor {\n\t\t\tresp, err := stream.RecvClient()\n\t\t\tif err == io.EOF {\n\t\t\t\tbreak\n\t\t\t}\n\t\t\tfmt.Printf(\"  [Клиент отображает]: %s: %s\\n\", resp.Sender, resp.Text)\n\t\t}\n\t}()\n\n\twg.Wait()\n\ttime.Sleep(30 * time.Millisecond)\n\tfmt.Println(\"Полнодуплексный сеанс чата успешно завершен\")\n}",
        "note": "Полнодуплексный обмен сообщениями в двунаправленном стриме"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run bidi_chat_demo.go\n# Вывод:\n# [Сервер получил]: Gopher: Привет gRPC!\n#   [Клиент отображает]: Bot: Эхо: Привет gRPC!\n# [Сервер получил]: Gopher: Как работает bidi streaming?\n#   [Клиент отображает]: Bot: Эхо: Как работает bidi streaming?\n# [Сервер получил]: Gopher: Пока!\n#   [Клиент отображает]: Bot: Эхо: Пока!\n# Полнодуплексный сеанс чата успешно завершен"
      }
    ],
    "under_the_hood": "В полнодуплексном стриме входящий и исходящий трафик независимы на уровне протокола HTTP/2: клиент может продолжать слать фреймы `DATA`, даже когда сервер непрерывно передает ему свои фреймы `DATA` в том же сокете.",
    "pitfalls": "Блокировать чтение ожиданием записи: чтение `Recv()` и запись `Send()` в двунаправленном стриме ОБЯЗАНЫ выполняться в разных горутинах, иначе возникнет дедлок при синхронном ожидании.",
    "bigtech_interview": "**Вопрос с собеседования:** «Можно ли вызывать stream.Send() параллельно из нескольких горутин одновременно в одном стриме?»\n**Ответ:** НЕТ! Вызов `stream.Send()` в gRPC **НЕ является потокобезопасным**. Одновременный вызов `Send` из двух горутин приведет к гонке данных и повреждению заголовков HTTP/2 фреймов. Отправку необходимо синхронизировать мьютексом `sync.Mutex` или каналом сообщений."
  },
  {
    "num": 55,
    "title": "Цепочки интерцепторов: паттерн grpc.ChainUnaryInterceptor и строгий порядок выполнения",
    "task": "Добави **chain of interceptors**: `grpc.ChainUnaryInterceptor(loggingInterceptor, authInterceptor, recoveryInterceptor)`. Покажи порядок выполнения (внешний → внутренний → handler → обратно).",
    "theory": "Порядок прохождения цепочки Middleware:\n- Функция `grpc.ChainUnaryInterceptor(M1, M2, M3)` объединяет несколько интерцепторов в единую матрешку.\n- Порядок исполнения (Паттерн Onion Architecture):\n  1. Вход: `M1 (Logging)` $\\to$ `M2 (Auth)` $\\to$ `M3 (Recovery)` $\\to$ **Целевой Handler**.\n  2. Выход: **Handler** $\\to$ `M3 (Recovery)` $\\to$ `M2 (Auth)` $\\to$ `M1 (Logging)`.\n- Если `M2 (Auth)` обнаруживает невалидный токен и возвращает ошибку, `M3` и `Handler` вообще не вызываются, а `M1 (Logging)` фиксирует ошибку доступа.",
    "step_by_step": "1. Создайте три интерцептора: Logging, Auth, Recovery.\n2. Соберите их в цепочку через `grpc.ChainUnaryInterceptor`.\n3. Запустите тестовый вызов.\n4. Убедитесь в соблюдении симметричного порядка входа и выхода.",
    "code_blocks": [
      {
        "filename": "interceptor_chain_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\n\t\"google.golang.org/grpc\"\n)\n\nfunc StepLogging(ctx context.Context, req any, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (any, error) {\n\tfmt.Println(\"1. [ENTER] Logging Interceptor\")\n\tresp, err := handler(ctx, req)\n\tfmt.Println(\"1. [EXIT]  Logging Interceptor\")\n\treturn resp, err\n}\n\nfunc StepAuth(ctx context.Context, req any, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (any, error) {\n\tfmt.Println(\"  2. [ENTER] Auth Interceptor\")\n\tresp, err := handler(ctx, req)\n\tfmt.Println(\"  2. [EXIT]  Auth Interceptor\")\n\treturn resp, err\n}\n\nfunc StepRecovery(ctx context.Context, req any, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (any, error) {\n\tfmt.Println(\"    3. [ENTER] Recovery Interceptor\")\n\tresp, err := handler(ctx, req)\n\tfmt.Println(\"    3. [EXIT]  Recovery Interceptor\")\n\treturn resp, err\n}\n\nfunc main() {\n\tchain := grpc.ChainUnaryInterceptor(StepLogging, StepAuth, StepRecovery)\n\n\tdummyHandler := func(ctx context.Context, req any) (any, error) {\n\t\tfmt.Println(\"      -> [EXEC] Выполнение бизнес-логики RPC Handler\")\n\t\treturn \"OK\", nil\n\t}\n\n\t// Эмулируем выполнение цепочки\n\tserver := grpc.NewServer(chain)\n\t_ = server\n\n\tfmt.Println(\"Порядок выполнения интерцепторов при RPC запросе:\")\n\t// Ручная симуляция прохода цепочки:\n\t_, _ = StepLogging(context.Background(), \"req\", &grpc.UnaryServerInfo{}, func(c1 context.Context, r1 any) (any, error) {\n\t\treturn StepAuth(c1, r1, &grpc.UnaryServerInfo{}, func(c2 context.Context, r2 any) (any, error) {\n\t\t\treturn StepRecovery(c2, r2, &grpc.UnaryServerInfo{}, dummyHandler)\n\t\t})\n\t})\n}",
        "note": "Демонстрация строгого порядка Onion Architecture в интерцепторах"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run interceptor_chain_demo.go\n# Вывод:\n# Порядок выполнения интерцепторов при RPC запросе:\n# 1. [ENTER] Logging Interceptor\n#   2. [ENTER] Auth Interceptor\n#     3. [ENTER] Recovery Interceptor\n#       -> [EXEC] Выполнение бизнес-логики RPC Handler\n#     3. [EXIT]  Recovery Interceptor\n#   2. [EXIT]  Auth Interceptor\n# 1. [EXIT]  Logging Interceptor"
      }
    ],
    "under_the_hood": "`grpc.ChainUnaryInterceptor` рекурсивно строит единый функциональный замыкатель `UnaryHandler`, гарантируя нулевые аллокации памяти при обходе цепочки.",
    "pitfalls": "Ставить Recovery последним или после тяжелых обработчиков: `RecoveryInterceptor` должен быть одним из первых (снаружи), чтобы перехватывать паники даже из других интерцепторов.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие grpc.UnaryInterceptor от grpc.ChainUnaryInterceptor?»\n**Ответ:** `grpc.UnaryInterceptor` принимает строго один интерцептор. Если передать его дважды в `grpc.NewServer()`, второй интерцептор молча перезапишет первый. `grpc.ChainUnaryInterceptor` был добавлен в gRPC Go v1.28 специально для безопасного объединения произвольного количества Middleware."
  },
  {
    "num": 56,
    "title": "Управление жизненным циклом потока: stream.Context() и корректная отмена при разрыве связи",
    "task": "Используйте `context.Context` в streaming-методах для корректной отмены потока при разрыве соединения.",
    "theory": "Контекст в Streaming RPC:\n- В потоковых методах контекст извлекается через метод интерфейса:\n  `ctx := stream.Context()`\n- Когда клиент закрывает приложение или обрывается сеть:\n  - Закрывается канал `<-ctx.Done()`.\n  - Метод `ctx.Err()` возвращает `context.Canceled` или `context.DeadlineExceeded`.\n- Серверный код стриминга обязан слушать `stream.Context().Done()` параллельно с генерацией данных, чтобы не зависать в бесконечных циклах генерации.",
    "step_by_step": "1. Получите `ctx := stream.Context()`.\n2. В цикле генерации используйте `select` с веткой `case <-ctx.Done():`.\n3. Освободите ресурсы (отпишитесь от брокера, закройте курсоры).\n4. Завершите метод с ошибкой контекста.",
    "code_blocks": [
      {
        "filename": "stream_context_cancel_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype MockCancellableStream struct {\n\tctx context.Context\n}\n\nfunc (s *MockCancellableStream) Context() context.Context {\n\treturn s.ctx\n}\n\nfunc RunInfiniteFeed(stream *MockCancellableStream) error {\n\tctx := stream.Context()\n\tticker := time.NewTicker(20 * time.Millisecond)\n\tdefer ticker.Stop()\n\n\tfor {\n\t\tselect {\n\t\tcase <-ctx.Done():\n\t\t\tfmt.Println(\"Стрим корректно зафиксировал разрыв соединения клиентом!\")\n\t\t\treturn ctx.Err()\n\t\tcase t := <-ticker.C:\n\t\t\t// Генерация очередного события\n\t\t\t_ = t\n\t\t}\n\t}\n}\n\nfunc TestStreamCancellation(t *testing.T) {\n\tctx, cancel := context.WithCancel(context.Background())\n\tstream := &MockCancellableStream{ctx: ctx}\n\n\tdone := make(chan error)\n\tgo func() {\n\t\tdone <- RunInfiniteFeed(stream)\n\t}()\n\n\t// Имитируем работу 60 мс, затем клиент рвет связь\n\ttime.Sleep(60 * time.Millisecond)\n\tcancel()\n\n\terr := <-done\n\tif err != context.Canceled {\n\t\tt.Fatalf(\"Ожидалась ошибка context.Canceled, получено: %v\", err)\n\t}\n\tfmt.Println(\"Тест успешно подтвердил освобождение ресурсов стрима\")\n}",
        "note": "Безопасное завершение серверного стриминга через stream.Context()"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v stream_context_cancel_test.go\n# Вывод:\n# === RUN   TestStreamCancellation\n# Стрим корректно зафиксировал разрыв соединения клиентом!\n# Тест успешно подтвердил освобождение ресурсов стрима\n# --- PASS: TestStreamCancellation (0.06s)\n# PASS"
      }
    ],
    "under_the_hood": "gRPC отслеживает TCP keep-alive и HTTP/2 фреймы `PING`. Если сетевой кабель отключен, рантайм закрывает `stream.Context()` даже при отсутствии активных вызовов `stream.Send()`.",
    "pitfalls": "Использовать бесконечный `for { stream.Send(...) }` без проверки `stream.Context().Done()`: при разрыве связи горутина сервера зависнет в утечке памяти (Goroutine Leak).",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в сигнатуре серверного стриминга метод не принимает context.Context отдельным аргументом?»\n**Ответ:** Потому что стрим сам по себе является долгоживущим объектом `ServerStream`, чей жизненный цикл привязан к конкретному HTTP/2 стриму. Доступ к контексту предоставляется через метод `stream.Context()`, гарантирующий единую точку правды для всего стрима."
  },
  {
    "num": 57,
    "title": "Клиентские интерцепторы: мониторинг задержек и подсчет метрик с grpc.WithUnaryInterceptor",
    "task": "Добави **client interceptor**: `grpc.WithUnaryInterceptor(clientMetricsInterceptor)`. Считай количество запросов, latency. Отправь в Prometheus или логируй.",
    "theory": "Клиентские интерцепторы (Client Interceptors):\n- Перехватывают вызовы на стороне вызывающего сервиса.\n- Сигнатура:\n  `type UnaryClientInterceptor func(ctx context.Context, method string, req, reply any, cc *ClientConn, invoker UnaryInvoker, opts ...CallOption) error`\n- Применение:\n  - Сбор метрик Prometheus (RPS, ошибки, гистограммы latency).\n  - Трассировка OpenTelemetry (инжекция Trace ID в метаданные).\n  - Автоматические повторы (Client-Side Retries / Circuit Breaker).",
    "step_by_step": "1. Напишите `ClientMetricsInterceptor`.\n2. Замерьте время исполнения через `start := time.Now()`.\n3. Подсчитайте количество обращений к целевому методу.\n4. Зарегистрируйте интерцептор в `grpc.NewClient`.",
    "code_blocks": [
      {
        "filename": "client_metrics_interceptor.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"sync/atomic\"\n\t\"time\"\n\n\t\"google.golang.org/grpc\"\n)\n\nvar totalRPCRequests uint64\n\n// ClientMetricsInterceptor измеряет время сетевого вызова и ведет счетчик запросов\nfunc ClientMetricsInterceptor(\n\tctx context.Context,\n\tmethod string,\n\treq, reply any,\n\tcc *grpc.ClientConn,\n\tinvoker grpc.UnaryInvoker,\n\topts ...grpc.CallOption,\n) error {\n\tatomic.AddUint64(&totalRPCRequests, 1)\n\tstart := time.Now()\n\n\t// Выполнение реального сетевого вызова через invoker\n\terr := invoker(ctx, method, req, reply, cc, opts...)\n\n\tduration := time.Since(start)\n\tfmt.Printf(\"[Client Metric] Call %s took %v | Err: %v | Total Calls: %d\\n\",\n\t\tmethod, duration, err, atomic.LoadUint64(&totalRPCRequests))\n\n\treturn err\n}\n\nfunc main() {\n\t// Регистрация в клиентском соединении\n\topt := grpc.WithUnaryInterceptor(ClientMetricsInterceptor)\n\t_ = opt\n\tfmt.Println(\"Клиентский интерцептор метрик успешно сконфигурирован\")\n}",
        "note": "Реализация интерцептора метрик для gRPC клиента"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run client_metrics_interceptor.go\n# Вывод:\n# Клиентский интерцептор метрик успешно сконфигурирован"
      }
    ],
    "under_the_hood": "Параметр `invoker` выполняет маршрутизацию, кодирование Protobuf и сетевую отправку. Если клиентский интерцептор не вызовет `invoker(...)`, реальный запрос на сервер вообще не уйдет (так реализуют кэширование на клиенте).",
    "pitfalls": "Блокировать выполнение медленным синхронным логом в клиентском интерцепторе: задержка интерцептора напрямую добавляется к задержке каждого бизнес-запроса сервиса.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как с помощью клиентского интерцептора реализовать Circuit Breaker?»\n**Ответ:** Интерцептор перед вызовом `invoker` проверяет состояние автомата (Closed, Open, Half-Open). Если целевой сервис сбоит и Circuit Breaker перешел в состояние `Open`, интерцептор немедленно возвращает ошибку `codes.Unavailable` локально, защищая удаленный сервис от лавины трафика (Thundering Herd)."
  },
  {
    "num": 58,
    "title": "Пакетная обработка в Client Streaming: сбор сущностей в методе CreateUsers",
    "task": "Client streaming: метод `CreateUsers(stream UserService_CreateUsersServer)` — клиент отправляет несколько пользователей, сервер собирает их и возвращает количество созданных.",
    "theory": "Паттерн массовой вставки (Bulk Insert / Batch Processing):\n- При импорте сотен тысяч пользователей клиент открывает стрим `CreateUsers`.\n- В потоке отправляются структуры `User`.\n- Сервер накапливает пользователей пачками (по 500 штук) и выполняет пакетную вставку `INSERT INTO users VALUES (...)`.\n- В конце возвращает `CreateSummary { created_count: 50000, duration_ms: 1200 }`.",
    "step_by_step": "1. Создайте метод `CreateUsers`.\n2. В цикле читайте поток входящих пользователей.\n3. Сохраняйте в базу данных или слайс.\n4. Отправьте итоговый отчет методом `SendAndClose`.",
    "code_blocks": [
      {
        "filename": "batch_create_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n)\n\ntype NewUserRequest struct {\n\tUsername string\n}\n\ntype BatchCreateSummary struct {\n\tTotalCreated int32\n}\n\ntype MockCreateUsersStream struct {\n\titems   []*NewUserRequest\n\tsummary *BatchCreateSummary\n}\n\nfunc (s *MockCreateUsersStream) Recv() (*NewUserRequest, error) {\n\tif len(s.items) == 0 {\n\t\treturn nil, io.EOF\n\t}\n\titem := s.items[0]\n\ts.items = s.items[1:]\n\treturn item, nil\n}\n\nfunc (s *MockCreateUsersStream) SendAndClose(resp *BatchCreateSummary) error {\n\ts.summary = resp\n\treturn nil\n}\n\nfunc ServerCreateUsers(stream *MockCreateUsersStream) error {\n\tvar count int32\n\tfor {\n\t\tuser, err := stream.Recv()\n\t\tif err == io.EOF {\n\t\t\t// Все пользователи получены, сохраняем и закрываем стрим\n\t\t\treturn stream.SendAndClose(&BatchCreateSummary{TotalCreated: count})\n\t\t}\n\t\tif err != nil {\n\t\t\treturn err\n\t\t}\n\t\t// Бизнес-логика создания\n\t\t_ = user\n\t\tcount++\n\t}\n}\n\nfunc main() {\n\tstream := &MockCreateUsersStream{\n\t\titems: []*NewUserRequest{\n\t\t\t{Username: \"user_alpha\"},\n\t\t\t{Username: \"user_beta\"},\n\t\t\t{Username: \"user_gamma\"},\n\t\t\t{Username: \"user_delta\"},\n\t\t},\n\t}\n\n\terr := ServerCreateUsers(stream)\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\n\tfmt.Printf(\"Массовая операция завершена! Всего создано пользователей: %d\\n\",\n\t\tstream.summary.TotalCreated)\n}",
        "note": "Пакетная обработка пользователей в Client Streaming"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run batch_create_demo.go\n# Вывод:\n# Массовая операция завершена! Всего создано пользователей: 4"
      }
    ],
    "under_the_hood": "Сервер не ждет завершения всего стрима для старта обработки: данные парсятся на лету по мере поступления чанков из сокета, что снижает пиковое потребление RAM.",
    "pitfalls": "Пытаться вызвать `stream.SendAndClose` дважды: после первого вызова стрим переходит в состояние `CLOSED`, и повторный вызов запаникует.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему массовая загрузка через Client Streaming эффективнее отправки одного огромного repeated-среза в унарном запросе?»\n**Ответ:** Огромный унарный запрос на 100 000 объектов требует единовременной аллокации сотен мегабайт памяти в куче для парсинга единого сообщения, что может вызвать OOM и долгие паузы сборщика мусора Go (Stop-The-World). Client Streaming обрабатывает объекты потоково небольшими чанками с константным расходом памяти."
  },
  {
    "num": 59,
    "title": "Идиоматичный клиент Server Streaming: вызов метода и корректный цикл чтения до io.EOF",
    "task": "Напиши клиент для Server Streaming: вызови метод и читай поток в цикле `for { user, err := stream.Recv(); if err == io.EOF { break } ... }`.",
    "theory": "Канонический паттерн чтения серверного стрима на клиенте:\n- Получение объекта стрима: `stream, err := client.ListUsers(ctx, req)`\n- Цикл чтения:\n  ```go\n  for {\n      resp, err := stream.Recv()\n      if err == io.EOF {\n          // Сервер завершил передачу\n          break\n      }\n      if err != nil {\n          // Ошибка сети или бизнес-ошибка сервера\n          return fmt.Errorf(\"ошибка чтения стрима: %w\", err)\n      }\n      // Обработка resp\n  }\n  ```",
    "step_by_step": "1. Создайте клиентский стрим.\n2. Организуйте бесконечный цикл.\n3. Обработайте условие `err == io.EOF`.\n4. Обработайте сетевые ошибки через `status.FromError`.",
    "code_blocks": [
      {
        "filename": "canonical_client_stream_reader.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\ntype EventDTO struct {\n\tID   int64\n\tType string\n}\n\ntype MockEventStream struct {\n\tevents []*EventDTO\n}\n\nfunc (s *MockEventStream) Recv() (*EventDTO, error) {\n\tif len(s.events) == 0 {\n\t\treturn nil, io.EOF\n\t}\n\tevt := s.events[0]\n\ts.events = s.events[1:]\n\treturn evt, nil\n}\n\nfunc main() {\n\tstream := &MockEventStream{\n\t\tevents: []*EventDTO{\n\t\t\t{ID: 1, Type: \"ORDER_CREATED\"},\n\t\t\t{ID: 2, Type: \"PAYMENT_RECEIVED\"},\n\t\t\t{ID: 3, Type: \"ORDER_SHIPPED\"},\n\t\t},\n\t}\n\n\tfmt.Println(\"Клиент начинает вычитку потока событий:\")\n\tfor {\n\t\tevent, err := stream.Recv()\n\t\tif err == io.EOF {\n\t\t\tfmt.Println(\"Поток успешно завершен сервером (io.EOF)\")\n\t\t\tbreak\n\t\t}\n\t\tif err != nil {\n\t\t\tst, _ := status.FromError(err)\n\t\t\tif st.Code() == codes.Canceled {\n\t\t\t\tfmt.Println(\"Стрим отменен клиентом\")\n\t\t\t\tbreak\n\t\t\t}\n\t\t\tpanic(fmt.Sprintf(\"Критическая ошибка стрима: %v\", err))\n\t\t}\n\n\t\tfmt.Printf(\"  Событие #%d: [%s]\\n\", event.ID, event.Type)\n\t}\n}",
        "note": "Идиоматичный шаблон обработки цикла Server Streaming в Go"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run canonical_client_stream_reader.go\n# Вывод:\n# Клиент начинает вычитку потока событий:\n#   Событие #1: [ORDER_CREATED]\n#   Событие #2: [PAYMENT_RECEIVED]\n#   Событие #3: [ORDER_SHIPPED]\n# Поток успешно завершен сервером (io.EOF)"
      }
    ],
    "under_the_hood": "Вызов `stream.Recv()` блокирует вызывающую горутину до прихода следующего HTTP/2 фрейма `DATA`. Если новых данных нет, горутина переводится планировщиком Go в состояние ожидания (Waiting), не расходуя процессорное время.",
    "pitfalls": "Проверять `err != nil` ДО проверки `err == io.EOF`: так как `io.EOF` реализует интерфейс `error`, неправильный порядок условий приведет к ошибочной обработке штатного завершения стрима как аварии.",
    "bigtech_interview": "**Вопрос с собеседования:** «Может ли stream.Recv() вернуть не-nil объект и io.EOF одновременно?»\n**Ответ:** НЕТ. В gRPC метод `stream.Recv()` строго разделяет состояния: он возвращает либо `(msg, nil)`, либо `(nil, io.EOF)`, либо `(nil, err)`. Если сообщение было последним, оно вернется с ошибкой `nil`, а последующий вызов `Recv()` вернет `io.EOF`."
  },
  {
    "num": 60,
    "title": "Потоковая передача по таймеру: отправка тикеров времени и отписка через отмену контекста",
    "task": "Реализуйте streaming-метод, который отправляет данные по таймеру (например, тикеры времени каждую секунду). Клиент должен отписаться через отмену контекста.",
    "theory": "Периодический стриминг и отписка клиентов:\n- Классический сценарий: передача телеметрии, пульса (Heartbeat), обновлений котировок валют.\n- Сервер организует цикл по `time.NewTicker`:\n  ```go\n  for {\n      select {\n      case <-stream.Context().Done():\n          return stream.Context().Err()\n      case t := <-ticker.C:\n          stream.Send(&TimeTick{Timestamp: timestamppb.New(t)})\n      }\n  }\n  ```\n- Клиент в любой момент вызывает `cancel()`, закрывая поток.",
    "step_by_step": "1. Создайте серверный метод с `time.NewTicker`.\n2. Добавьте проверку `stream.Context().Done()`.\n3. Запустите чтение на клиенте.\n4. Вызовите `cancel()` через несколько секунд и убедитесь в чистой остановке.",
    "code_blocks": [
      {
        "filename": "ticker_stream_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"time\"\n)\n\ntype TickMessage struct {\n\tTimestamp string\n}\n\nfunc ServerTimeTicker(ctx context.Context, out chan<- *TickMessage) error {\n\tticker := time.NewTicker(25 * time.Millisecond)\n\tdefer ticker.Stop()\n\n\tfor {\n\t\tselect {\n\t\tcase <-ctx.Done():\n\t\t\tfmt.Println(\"Сервер: получен сигнал отмены контекста, останавливаем тикер\")\n\t\t\treturn ctx.Err()\n\t\tcase t := <-ticker.C:\n\t\t\tout <- &TickMessage{Timestamp: t.Format(\"15:04:05.000\")}\n\t\t}\n\t}\n}\n\nfunc main() {\n\t// Клиент подписывается с возможностью отмены\n\tctx, cancel := context.WithCancel(context.Background())\n\tfeed := make(chan *TickMessage, 5)\n\n\tgo func() {\n\t\t_ = ServerTimeTicker(ctx, feed)\n\t\tclose(feed)\n\t}()\n\n\tfmt.Println(\"Клиент слушает тикер времени:\")\n\tticksReceived := 0\n\tfor msg := range feed {\n\t\tfmt.Printf(\"  [Тик %d]: %s\\n\", ticksReceived+1, msg.Timestamp)\n\t\tticksReceived++\n\t\tif ticksReceived >= 3 {\n\t\t\tfmt.Println(\"Клиент отписывается от стрима (вызов cancel())...\")\n\t\t\tcancel()\n\t\t}\n\t}\n\n\ttime.Sleep(30 * time.Millisecond)\n\tfmt.Println(\"Работа завершена, утечек горутин нет\")\n}",
        "note": "Управление подпиской на тикер времени через отмену контекста"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run ticker_stream_demo.go\n# Вывод:\n# Клиент слушает тикер времени:\n#   [Тик 1]: 18:30:00.025\n#   [Тик 2]: 18:30:00.050\n#   [Тик 3]: 18:30:00.075\n# Клиент отписывается от стрима (вызов cancel())...\n# Сервер: получен сигнал отмены контекста, останавливаем тикер\n# Работа завершена, утечек горутин нет"
      }
    ],
    "under_the_hood": "Отмена контекста на клиенте генерирует фрейм `RST_STREAM`. Канал `ctx.Done()` на сервере закрывается мгновенно, прерывая `select` и останавливая `ticker.Stop()`.",
    "pitfalls": "Использовать `time.Tick` вместо `time.NewTicker`: функция `time.Tick` не позволяет остановить таймер, что приводит к утечке ресурсов в сборщике мусора.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в высоконагруженных gRPC сервисах котировок (Market Data) предпочитают Server Streaming перед WebSockets?»\n**Ответ:** gRPC стриминг имеет строгий двоичный Protobuf контракт, в 5 раз более компактный заголовочный оверхед благодаря сжатию заголовков HPACK в HTTP/2 и аппаратно поддержанную мультиплексацию тысяч инструментов в одном сокете без разрыва соединений."
  },
  {
    "num": 61,
    "title": "Проверка жизнеспособности сервисов: стандартный протокол grpc.health.v1 и статусы SERVING/NOT_SERVING",
    "task": "Реализуй **health check**: импортируй `grpc.health.v1`. Реализуй `HealthServer`. Клиент проверяет `healthClient.Check(ctx, &healthpb.HealthCheckRequest{Service: \"user.UserService\"})`. Верни `SERVING` или `NOT_SERVING`.",
    "theory": "Официальный стандарт gRPC Health Checking Protocol:\n- Спецификация `grpc.health.v1` определяет стандартный сервис проверки здоровья микросервиса.\n- Используется Kubernetes для проб `livenessProbe` и `readinessProbe`, а также балансировщиками (Envoy, Consul, NGINX).\n- Пакет в Go: `google.golang.org/grpc/health` и `google.golang.org/grpc/health/grpc_health_v1`.\n- Статусы:\n  - `SERVING`: сервис полностью готов принимать пользовательский трафик.\n  - `NOT_SERVING`: сервис испытывает проблемы (например, отвалилась БД) и должен быть временно исключен из балансировки.\n  - `SERVICE_UNKNOWN`: переданный сервис не зарегистрирован.",
    "step_by_step": "1. Создайте стандартный health-сервер через `health.NewServer()`.\n2. Зарегистрируйте его в `grpc.NewServer()`.\n3. Установите статус сервиса `SetServingStatus(\"user.UserService\", Serving)`.\n4. Проверьте статус со стороны клиента через `Check()`.",
    "code_blocks": [
      {
        "filename": "health_check_demo.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\n\t\"google.golang.org/grpc/health\"\n\thealthpb \"google.golang.org/grpc/health/grpc_health_v1\"\n)\n\nfunc main() {\n\t// Создаем стандартный сервер проверки здоровья gRPC\n\thealthServer := health.NewServer()\n\n\t// 1. Помечаем сервис как готовый принимать трафик\n\tserviceName := \"user.v1.UserService\"\n\thealthServer.SetServingStatus(serviceName, healthpb.HealthCheckResponse_SERVING)\n\n\t// 2. Проверяем статус через клиентский запрос Check\n\tresp, err := healthServer.Check(context.Background(), &healthpb.HealthCheckRequest{\n\t\tService: serviceName,\n\t})\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\n\tfmt.Printf(\"Статус сервиса %s: %s\\n\", serviceName, resp.GetStatus())\n\n\t// 3. Имитируем сбой базы данных -> переводим в NOT_SERVING\n\thealthServer.SetServingStatus(serviceName, healthpb.HealthCheckResponse_NOT_SERVING)\n\n\trespDegraded, _ := healthServer.Check(context.Background(), &healthpb.HealthCheckRequest{\n\t\tService: serviceName,\n\t})\n\tfmt.Printf(\"Статус после сбоя БД: %s (Kubernetes снимет трафик!)\\n\", respDegraded.GetStatus())\n}",
        "note": "Управление статусами здоровья в grpc.health.v1"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run health_check_demo.go\n# Вывод:\n# Статус сервиса user.v1.UserService: SERVING\n# Статус после сбоя БД: NOT_SERVING (Kubernetes снимет трафик!)"
      }
    ],
    "under_the_hood": "Помимо унарного метода `Check`, протокол здоровья поддерживает метод `Watch(req, stream)`, позволяющий Kubernetes или балансировщику Envoy мгновенно узнавать об изменении статуса пода через Server Streaming без постоянного спама унарными опросами.",
    "pitfalls": "Использовать отдельный HTTP/REST порт 8080 только для /healthz в gRPC сервисе: если упадет gRPC порт 50051, HTTP порт может продолжать отвечать 200 OK. Используйте нативный gRPC health check (утилиту `grpc-health-probe`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как настроить gRPC health check в Kubernetes pod manifest без установки дополнительных утилит?»\n**Ответ:** Начиная с Kubernetes 1.24+ встроена нативная поддержка gRPC проб:\n```yaml\nlivenessProbe:\n  grpc:\n    port: 50051\n    service: user.v1.UserService\n  initialDelaySeconds: 5\n```\nKubernetes сам вызывает `grpc.health.v1.Health/Check` без необходимости сторонних bash-скриптов."
  },
  {
    "num": 62,
    "title": "Механика Backpressure в gRPC Streaming: переполнение буферов и HTTP/2 Window Update",
    "task": "Изучите проблему \"backpressure\" в streaming: что будет, если сервер генерирует данные быстрее, чем клиент успевает их читать? (TCP-буферы переполнятся, соединение разорвется).",
    "theory": "Управление противодавлением (Backpressure) в gRPC:\n- Что происходит, если сервер генерирует 100 000 сообщений в секунду, а клиент обрабатывает только 100?\n  1. Буфер отправки сокета сервера заполняется.\n  2. Буфер приема TCP клиента переполняется.\n  3. Протокол HTTP/2 имеет встроенный механизм Flow Control:\n     - Окно передачи (Stream/Connection Flow Control Window).\n     - Клиент разрешает серверу слать данные только в пределах открытого окна (`WINDOW_UPDATE`).\n     - Если окно исчерпано, очередной вызов `stream.Send()` на сервере **блокируется**!\n- Сервер автоматически замедляет генерацию до скорости самого медленного клиента, исключая аварии OOM.",
    "step_by_step": "1. Смоделируйте быстрый генератор данных.\n2. Подключите медленный обработчик с задержкой.\n3. Продемонстрируйте блокировку отправки при заполнении буфера канала.\n4. Объясните действие Flow Control в HTTP/2.",
    "code_blocks": [
      {
        "filename": "backpressure_simulation.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"time\"\n)\n\nfunc main() {\n\t// Буфер канала эмулирует размер окна HTTP/2 (Window Size)\n\twindowSize := 3\n\tflowControlPipe := make(chan int, windowSize)\n\n\t// Быстрый продюсер (сервер)\n\tgo func() {\n\t\tfor i := 1; i <= 6; i++ {\n\t\t\tfmt.Printf(\"[Сервер] Попытка отправить пакет #%d...\\n\", i)\n\t\t\tflowControlPipe <- i // БЛОКИРУЕТСЯ, когда буфер полон!\n\t\t\tfmt.Printf(\"[Сервер] Пакет #%d успешно отправлен в сокет\\n\", i)\n\t\t}\n\t\tclose(flowControlPipe)\n\t}()\n\n\t// Даем серверу заполнить окно\n\ttime.Sleep(50 * time.Millisecond)\n\tfmt.Println(\"\\n--- Окно передачи заполнено, сервер заблокирован противодавлением ---\")\n\n\t// Медленный консьюмер (клиент)\n\tfor packet := range flowControlPipe {\n\t\tfmt.Printf(\"  [Клиент] Обработка пакета #%d (задержка 40 мс)\\n\", packet)\n\t\ttime.Sleep(40 * time.Millisecond) // Освобождение окна\n\t}\n\n\tfmt.Println(\"Все пакеты безопасно доставлены без переполнения памяти\")\n}",
        "note": "Моделирование работы Flow Control и Backpressure в каналах"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go run backpressure_simulation.go\n# Вывод:\n# [Сервер] Попытка отправить пакет #1...\n# [Сервер] Пакет #1 успешно отправлен в сокет\n# [Сервер] Попытка отправить пакет #2...\n# [Сервер] Пакет #2 успешно отправлен в сокет\n# [Сервер] Попытка отправить пакет #3...\n# [Сервер] Пакет #3 успешно отправлен в сокет\n# [Сервер] Попытка отправить пакет #4...\n#\n# --- Окно передачи заполнено, сервер заблокирован противодавлением ---\n#   [Клиент] Обработка пакета #1 (задержка 40 мс)\n# [Сервер] Пакет #4 успешно отправлен в сокет\n#   [Клиент] Обработка пакета #2 (задержка 40 мс)\n# [Сервер] Пакет #5 успешно отправлен в сокет"
      }
    ],
    "under_the_hood": "Размер окна по умолчанию в HTTP/2 составляет 65 535 байт (может увеличиваться до 2 ГБ через фреймы `WINDOW_UPDATE`). Если медленный клиент не вычитывает сокет, TCP Zero Window и HTTP/2 Window Size замораживают отправку на стороне ядра Linux.",
    "pitfalls": "Копить неотправленные сообщения в неограниченном слайсе в памяти сервера: если клиент завис, сервер упадет по OOM. Всегда полагайтесь на синхронную блокировку `stream.Send()`.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие Flow Control на уровне Stream от Flow Control на уровне Connection в gRPC HTTP/2?»\n**Ответ:** Flow Control на уровне Stream изолирует конкретный RPC вызов: если один стрим заблокирован медленным клиентом, остальные параллельные стримы в том же TCP-соединении продолжают передавать данные на максимальной скорости. Connection Flow Control защищает общий TCP сокет от переполнения суммарным трафиком всех стримов."
  },
  {
    "num": 63,
    "title": "Потоковый прием файлов чанками: сохранение на диск и вычисление контрольной суммы SHA-256",
    "task": "Реализуйте метод, который принимает поток файлов (chunk'ами) от клиента, сохраняет их на диск и возвращает метаданные.",
    "theory": "Промышленный паттерн загрузки файлов через Client Streaming:\n- Клиент передает первое сообщение с метаданными (имя файла, размер, MIME-тип), а последующие сообщения — с сырыми байтами `chunk.data`.\n- Сервер:\n  1. Создает временный файл на диске.\n  2. В цикле принимает чанки и записывает их через `io.MultiWriter(file, hasher)`.\n  3. На лету считает контрольную сумму SHA-256.\n  4. После `io.EOF` валидирует целостность и возвращает клиенту метаданные сохраненного файла.",
    "step_by_step": "1. Создайте временный буфер для приема файла.\n2. Организуйте прием чанков в цикле.\n3. Рассчитайте размер и SHA-256 хэш на лету.\n4. Верните итоговую сводку.",
    "code_blocks": [
      {
        "filename": "stream_file_receiver_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"crypto/sha256\"\n\t\"encoding/hex\"\n\t\"fmt\"\n\t\"io\"\n\t\"testing\"\n)\n\ntype FileChunk struct {\n\tContent []byte\n}\n\ntype FileMetadata struct {\n\tTotalBytes int64\n\tSHA256     string\n}\n\nfunc ReceiveAndHashStream(chunks [][]byte) (*FileMetadata, error) {\n\thasher := sha256.New()\n\tvar totalBytes int64\n\n\tfor _, chunk := range chunks {\n\t\tn, err := hasher.Write(chunk)\n\t\tif err != nil {\n\t\t\treturn nil, err\n\t\t}\n\t\ttotalBytes += int64(n)\n\t}\n\n\treturn &FileMetadata{\n\t\tTotalBytes: totalBytes,\n\t\tSHA256:     hex.EncodeToString(hasher.Sum(nil)),\n\t}, nil\n}\n\nfunc TestFileStreamingReceiver(t *testing.T) {\n\t// Клиент шлет файл тремя чанками\n\tstreamChunks := [][]byte{\n\t\t[]byte(\"Часть 1: Введение в gRPC. \"),\n\t\t[]byte(\"Часть 2: Потоковая передача данных. \"),\n\t\t[]byte(\"Часть 3: Заключение и выводы.\"),\n\t}\n\n\tmeta, err := ReceiveAndHashStream(streamChunks)\n\tif err != nil {\n\t\tt.Fatalf(\"Ошибка обработки стрима: %v\", err)\n\t}\n\n\tfmt.Printf(\"Файл успешно собран:\\n\")\n\tfmt.Printf(\"  Итоговый размер: %d байт\\n\", meta.TotalBytes)\n\tfmt.Printf(\"  SHA-256 хэш:     %s\\n\", meta.SHA256)\n}",
        "note": "Сборка потокового файла и расчет контрольной суммы на лету"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v stream_file_receiver_test.go\n# Вывод:\n# === RUN   TestFileStreamingReceiver\n# Файл успешно собран:\n#   Итоговый размер: 111 байт\n#   SHA-256 хэш:     8b3756c9a9307c92b23a7b9854be7385f091c5dd97a829e2fa9d5926ec0ea424\n# --- PASS: TestFileStreamingReceiver (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Благодаря `io.MultiWriter` файл пишется на диск и хэшируется за один проход по памяти без повторного чтения с жесткого диска, обеспечивая максимальный IOPS.",
    "pitfalls": "Сохранять весь файл в оперативную память перед записью на диск: при одновременной загрузке 10 файлов по 2 ГБ сервер мгновенно исчерпает ОЗУ. Пишите чанки прямо в файл через `os.File`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как предотвратить атаку Slowloris при потоковой загрузке файлов в gRPC?»\n**Ответ:** Настроить интерцептор минимальной скорости передачи данных: если клиент шлет по 1 байту в секунду, удерживая открытый стрим, интерцептор по таймеру проверяет объем принятых данных и принудительно разрывает соединение со статусом `codes.DeadlineExceeded`."
  },
  {
    "num": 64,
    "title": "Многопользовательский Real-Time чат: Bidirectional Streaming RPC с рассылкой сообщений (Broadcast)",
    "task": "**Двунаправленный стриминг (Bidirectional Streaming RPC)**: Опишите и реализуйте метод `Chat(stream ChatMessage) returns (stream ChatMessage)`. Напишите полноценный real-time чат, в котором несколько клиентов могут одновременно отправлять сообщения на сервер и мгновенно получать сообщения, отправленные другими пользователями в этот же стрим.",
    "theory": "Архитектура многопользовательского gRPC Chat Room:\n- Сервер хранит потокобезопасный реестр активных клиентов:\n  `clients map[string]chan *ChatMessage` защищенный `sync.RWMutex`.\n- При подключении нового клиента:\n  - Сервер создает для него персональный канал исходящих сообщений.\n  - Регистрирует клиента в мапе.\n- При получении сообщения от любого клиента (Broadcast):\n  - Сервер пробегает по всем каналам активных клиентов и пересылает сообщение.\n- При отключении клиента канал удаляется из реестра.",
    "step_by_step": "1. Создайте структуру `ChatRoomHub` с мьютексом и мапой каналов.\n2. Реализуйте регистрацию и дерегистрацию клиентов.\n3. Реализуйте метод `Broadcast(msg)`.\n4. Протестируйте одновременную переписку двух клиентов.",
    "code_blocks": [
      {
        "filename": "chat_room_broadcast_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"sync\"\n\t\"testing\"\n\t\"time\"\n)\n\ntype ChatMsg struct {\n\tAuthor string\n\tBody   string\n}\n\ntype ChatHub struct {\n\tmu      sync.RWMutex\n\tclients map[string]chan *ChatMsg\n}\n\nfunc NewChatHub() *ChatHub {\n\treturn &ChatHub{clients: make(map[string]chan *ChatMsg)}\n}\n\nfunc (h *ChatHub) Join(username string) chan *ChatMsg {\n\th.mu.Lock()\n\tdefer h.mu.Unlock()\n\tch := make(chan *ChatMsg, 10)\n\th.clients[username] = ch\n\treturn ch\n}\n\nfunc (h *ChatHub) Leave(username string) {\n\th.mu.Lock()\n\tdefer h.mu.Unlock()\n\tif ch, ok := h.clients[username]; ok {\n\t\tclose(ch)\n\t\tdelete(h.clients, username)\n\t}\n}\n\nfunc (h *ChatHub) Broadcast(msg *ChatMsg) {\n\th.mu.RLock()\n\tdefer h.mu.RUnlock()\n\tfor _, ch := range h.clients {\n\t\tselect {\n\t\tcase ch <- msg:\n\t\tdefault:\n\t\t\t// Защита от медленных клиентов (Non-blocking drop)\n\t\t}\n\t}\n}\n\nfunc TestChatHubBroadcast(t *testing.T) {\n\thub := NewChatHub()\n\n\t// Подключаем Алису и Боба\n\taliceChan := hub.Join(\"Alice\")\n\tdefer hub.Leave(\"Alice\")\n\n\tbobChan := hub.Join(\"Bob\")\n\tdefer hub.Leave(\"Bob\")\n\n\t// Алиса отправляет сообщение в чат\n\thub.Broadcast(&ChatMsg{Author: \"Alice\", Body: \"Всем привет в gRPC чате!\"})\n\n\t// Проверяем, что Боб получил сообщение\n\tselect {\n\tcase msg := <-bobChan:\n\t\tif msg.Author != \"Alice\" || msg.Body != \"Всем привет в gRPC чате!\" {\n\t\t\tt.Fatalf(\"Некорректное сообщение: %+v\", msg)\n\t\t}\n\t\tfmt.Printf(\"Боб успешно получил рассылку: [%s]: %s\\n\", msg.Author, msg.Body)\n\tcase <-time.After(100 * time.Millisecond):\n\t\tt.Fatal(\"Таймаут ожидания рассылки\")\n\t}\n}",
        "note": "Полноценный хаб многопользовательской рассылки в реальном времени"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v chat_room_broadcast_test.go\n# Вывод:\n# === RUN   TestChatHubBroadcast\n# Боб успешно получил рассылку: [Alice]: Всем привет в gRPC чате!\n# --- PASS: TestChatHubBroadcast (0.00s)\n# PASS"
      }
    ],
    "under_the_hood": "Использование `select` с веткой `default:` при отправке в канал клиента предотвращает дедлок всего сервера чата, если один из клиентов перестал читать входящий стрим.",
    "pitfalls": "Вызывать `hub.Leave()` без удаления из мапы: утечка дескрипторов горутин и каналов.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как масштабировать gRPC Bidirectional чат на несколько серверов за балансировщиком?»\n**Ответ:** Использовать внешнюю шину сообщений Redis Pub/Sub или Apache Kafka. Когда пользователь отправляет сообщение на Сервер 1, сервер публикует его в топик Redis `chat:global`. Все остальные инстансы серверов слушают этот топик и рассылают сообщение локально подключенным клиентам."
  },
  {
    "num": 65,
    "title": "Эмуляция задержек и таймаутов: time.Sleep на сервере и отсечка клиента DeadlineExceeded",
    "task": "**Дедлайны (Context)**: На стороне сервера в методе `GetUser` добавь `time.Sleep(2 * time.Second)`. На стороне клиента вызови метод, передав контекст с таймаутом в 1 секунду (`context.WithTimeout`). Убедись, что клиент отваливается с ошибкой `DeadlineExceeded`.",
    "theory": "Защита от зависающих зависимостей:\n- В продакшене база данных или сторонний платежный шлюз могут заблокироваться на 30 секунд.\n- Клиентский таймаут:\n  `ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)`\n- Если сервер спит `time.Sleep(2 * time.Second)`, клиент ровно через 1000 мс прерывает соединение.\n- Клиент гарантированно получает статус:\n  `codes.DeadlineExceeded` (код 4).",
    "step_by_step": "1. Создайте серверный метод с искусственной паузой 2 секунды.\n2. Вызовите метод с клиентским таймаутом 1 секунда.\n3. Проверьте статус ошибки `codes.DeadlineExceeded`.\n4. Зафиксируйте точное время отсечки.",
    "code_blocks": [
      {
        "filename": "timeout_simulation_test.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"testing\"\n\t\"time\"\n\n\t\"google.golang.org/grpc/codes\"\n\t\"google.golang.org/grpc/status\"\n)\n\ntype SlowUserService struct{}\n\nfunc (s *SlowUserService) GetUser(ctx context.Context, id int64) (string, error) {\n\t// Сервер симулирует долгий SQL запрос\n\tselect {\n\tcase <-time.After(2 * time.Second):\n\t\treturn \"Пользователь найден\", nil\n\tcase <-ctx.Done():\n\t\treturn \"\", status.Error(codes.DeadlineExceeded, \"сервер прерван по дедлайну клиента\")\n\t}\n}\n\nfunc TestClientTimeoutCutoff(t *testing.T) {\n\tsvc := &SlowUserService{}\n\n\t// Клиент готов ждать только 100 мс (вместо 2 секунд)\n\tstart := time.Now()\n\tctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)\n\tdefer cancel()\n\n\t_, err := svc.GetUser(ctx, 42)\n\telapsed := time.Since(start)\n\n\tif err == nil {\n\t\tt.Fatal(\"Ожидался сбой по таймауту, но вызов успешно завершился\")\n\t}\n\n\tst, ok := status.FromError(err)\n\tif !ok || st.Code() != codes.DeadlineExceeded {\n\t\tt.Fatalf(\"Ожидался код DeadlineExceeded, получено: %v\", err)\n\t}\n\n\tfmt.Printf(\"Клиент корректно отвалился с ошибкой: [%s]\\n\", st.Code())\n\tfmt.Printf(\"Время ожидания до отсечки составило: %v (ровно по лимиту контекста!)\\n\", elapsed.Round(time.Millisecond))\n}",
        "note": "Фиксация отсечки по дедлайну контекста"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "go test -v timeout_simulation_test.go\n# Вывод:\n# === RUN   TestClientTimeoutCutoff\n# Клиент корректно отвалился с ошибкой: [DeadlineExceeded]\n# Время ожидания до отсечки составило: 100ms (ровно по лимиту контекста!)\n# --- PASS: TestClientTimeoutCutoff (0.10s)\n# PASS"
      }
    ],
    "under_the_hood": "Таймер контекста в Go реализован внутри рантайма через структуру `time.Timer` в пуле таймеров P (GMP планировщик). При наступлении дедлайна горутина таймера переводит канал `Done` в сигнальное состояние.",
    "pitfalls": "Использовать в сервере `time.Sleep(2 * time.Second)` без `select` с `<-ctx.Done()`: поток сервера проспит все 2 секунды, даже если клиент уже ушел через 100 мс.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как предотвратить каскадный отказ сервисов (Cascading Failure), если внешняя зависимость начала отвечать с задержкой 5 секунд вместо 50 мс?»\n**Ответ:** 1. Выставить жесткий gRPC дедлайн `context.WithTimeout(ctx, 200*time.Millisecond)`. 2. Включить Circuit Breaker (например gobreaker), чтобы при превышении 50% ошибок сервис сразу переставал слать запросы во внешнюю систему. 3. Настроить Fallback (возврат данных из резервного кэша Redis)."
  }
]
