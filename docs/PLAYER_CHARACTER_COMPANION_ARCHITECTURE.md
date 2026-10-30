# Архитектура Player Character Companion

## Решение этапа 7

Целевой кандидат — **вариант C: отдельный штатный игровой клиент с отдельным тестовым персонажем и account authority**. Это проект архитектуры, а не разрешение на запуск. Вариант A не поддержан доступным EMF API, вариант B не даёт полноценную player-семантику.

## Компоненты

```text
Python Brain (позже)
        |
        v
Command Planner / Safety Gate
        |
        +--------------------------+
        |                          |
        v                          v
Host Observer Bridge       Companion Client Adapter
(EMF server world)         (пока UNVERIFIED)
        |                          |
        v                          v
roster/account/entity      local input/action pipeline
position/events            второго игрового клиента
        \                          /
         \                        /
          v                      v
       Identity + Authority Binder
       external personality UUID
```

### Host Observer Bridge

Работает в процессе хоста или dedicated server и только читает:

- session token;
- список подключённых игроков;
- player slot, account key, entity id и platform name;
- position и разрешённые ECS-компоненты;
- доступные игровые события для подтверждения результата.

Host Observer не создаёт игрока, не меняет основной character и не считает server teleport доказательством `moveTo`.

### Companion Client Adapter

Должен жить рядом со вторым игровым клиентом и управлять только его локальным персонажем. Его backend пока не выбран: подтверждённого EMF API для генерации `ClientPlayerInput` нет. До отдельного исследования адаптер имеет состояние `UNAVAILABLE`, а все команды отклоняются.

Запрещено использовать глобальный ввод, если нельзя доказать привязку к окну/процессу второго клиента: это может затронуть основного персонажа.

### Identity + Authority Binder

Постоянная личность остаётся во внешнем `personality_id`. Привязка тела:

```text
personality_id
  -> expected companion account key
  -> current session token
  -> current player slot
  -> current entity id
```

Для доверия нужны минимум три последовательных наблюдения одного tuple и обязательные player-компоненты. Account key должен отличаться от account основного игрока, entity — от entity основного персонажа. Смена session, account, slot/entity binding, потеря peer или компонентов необратимо закрывает текущую команду.

`entityId` никогда не сохраняется как постоянная личность. Имя игрока не является идентификатором: оно недоверенное и может повторяться.

## Контракт выполнения

Каждая будущая команда проходит стадии:

1. `accepted` — JSON и параметры проверены;
2. `identity_confirmed` — account/session/slot/entity стабилизированы;
3. `authority_confirmed` — доказано, что backend принадлежит второму клиенту;
4. `input_submitted` — действие отправлено локальному pipeline;
5. `state_confirmed` — наблюдаемое игровое состояние изменилось;
6. `behavior_verified` — длительное поведение проверено отдельным игровым сценарием.

Неопределённый результат блокирует повтор mutating-команды до read-only reconciliation. Краткая близость к игроку не доказывает follow. Teleport не доказывает movement. Изменение визуальной модели не доказывает equip.

## Состояние и восстановление

Внешний runtime state должен хранить:

- `personality_id`;
- ожидаемый account key компаньона;
- текущий session token и наблюдённый binding;
- request journal и последнюю подтверждённую фазу;
- хеш/версию capability contract;
- признак `recovery_required`.

После reload/смены мира старый entity id отбрасывается. Восстановление начинается с нового roster observation и account matching. Нельзя удалять player entity; `dismiss` означает команду штатно выйти вторым клиентом и подтверждение исчезновения player slot. Если выход неизвестен, state остаётся `recovery_required`, а повторный запуск второго клиента блокируется до reconciliation.

Сохранения персонажа остаются собственностью игры и второго клиента. Проект не редактирует `character*.ksd`, не переносит его байты в entity и не хранит копию save в Git.

## Inventory и equipment

Источник истины — штатный character inventory второго клиента. Внешняя память хранит только намерения и подтверждения, а не дублирует содержимое.

Будущий inventory adapter должен:

- читать slots с item id и PIDE/instance state;
- проверять server permissions;
- выполнять одну транзакцию за request id;
- подтверждать source и destination;
- при неопределённом результате только перечитывать состояние;
- никогда не повторять consume/equip/transfer автоматически.

`equip` и `useItem` остаются заблокированы, пока не подтверждён client action pipeline. Host-side put/take не заменяет эти действия.

## Условия безопасного прототипа этапа 8

Потребуется отдельное подтверждение пользователя. До запуска должны быть готовы:

1. Отдельный Steam account с законным доступом к отдельной копии Enshrouded; один аккаунт одновременно не используется.
2. Отдельный тестовый персонаж компаньона и тестовый мир; основные saves исключены.
3. Проверенные резервные копии character/world обоих тестовых клиентов.
4. Предпочтительно второй физический ПК. Если выбран один ПК, сначала отдельная read-only проверка возможности двух процессов и ресурсов без обхода Steam.
5. Read-only survey-мод хоста, который публикует только roster/account/slot/entity/components/position.
6. Отдельные runtime-каталоги и логи для host и companion bridge.
7. Kill switch, который останавливает только внешний adapter и не завершает игру принудительно.

### Порядок будущей проверки

1. Пользователь вручную запускает хост и второй клиент штатным способом.
2. Второй тестовый персонаж вручную входит в тестовый мир.
3. Host Observer подтверждает два разных account key, player slot и entity.
4. Companion-side диагностика только читает `local_player`, client world и компоненты.
5. Сессия штатно закрывается; сверяется сохранение и backup.
6. Только после успешного read-only этапа исследуется один безопасный input, например поворот камеры или короткое движение на открытом месте.
7. Боевые, interaction и inventory-команды рассматриваются отдельными этапами.

Нельзя автоматически запускать второй клиент, создавать character, подключаться к миру, посылать input, spawn или менять inventory без отдельного разрешения.

## Критерий перехода к реализации

Runtime Player Body Adapter можно начинать только после доказательства всех пунктов:

- второй player виден как отдельный account/slot/entity;
- companion-side bridge однозначно привязан ко второму процессу;
- команда не затрагивает основное окно/персонажа;
- движение подтверждено без teleport;
- выход второго клиента сохраняет тестового персонажа штатно;
- recovery не запускает повторный клиент и не удаляет entity.

До этого [`companion/player_character.py`](../companion/player_character.py) остаётся офлайн evidence/policy-модулем с `runtime_control_enabled=False`.
