# Архитектура Human AI Companion

Статус: архитектурный контракт этапа 6. Runtime Human Body Adapter ещё не существует; игровой spawn заблокирован исследованием.

## Схема

```text
AI Brain
  ↓ намерение
Companion Controller
  ├─ Personality / Memory (внешнее состояние)
  ├─ Skills (проверяют capabilities)
  └─ HumanBodyAdapter
       ├─ CompanionState
       ├─ IdentityGate
       ├─ MovementController
       ├─ CombatController
       ├─ InteractionController
       ├─ CompanionInventory
       └─ EquipmentController
             ↓ подтверждённые операции
          EMF → Enshrouded
```

Brain оперирует намерениями и постоянным `companion_id`; он не знает entity ID, template GUID и протокол EMF. Controller выбирает только capability, которая одновременно подтверждена для тела и реализована адаптером.

## BodyDescriptor и capabilities

`BodyDescriptor` хранит `body_key`, template GUID, ожидаемые fingerprint-поля, требования lifecycle и evidence. На этапе 6 каталог содержит 18 workshop survivor-кандидатов, но `runtime_enabled=false` для каждого.

Capability имеет:

- имя: `spawn`, `follow`, `stay`, `moveTo`, `attack`, `interact`, `dismiss`, `inventory`, `equipment`;
- evidence: `CONFIRMED | LIKELY | UNKNOWN | UNSUPPORTED`;
- `implemented: bool`;
- узкий scope доказательства.

`CONFIRMED` не равен `implemented`. Например, `moveTo` подтверждён для существующего active survivor, но HumanBodyAdapter его пока не реализует. Controller отказывает, если любой из двух критериев ложен.

## Контракты

```text
BodyAdapter.observe() -> CompanionState
BodyAdapter.capabilities() -> CapabilityMap
BodyAdapter.spawn(request) -> BLOCKED до protocol v3
BodyAdapter.follow/stay/moveTo(...) -> только при capability implemented
BodyAdapter.attack/interact(...) -> только при capability implemented
BodyAdapter.dismiss() -> только для trusted handle
```

`MovementController`, `CombatController` и `InteractionController` не отправляют произвольные события. Каждый будущий backend описывает конкретное подтверждённое игровое событие, preconditions, наблюдаемое подтверждение и recovery.

`CompanionInventory` отделяет логический план от транзакции игры. До появления атомарного escrow/transfer backend он работает только как интерфейс без мутаций. `EquipmentController` не считает наличие компонента `Equipment` разрешением на equip.

## Lifecycle

```text
DISABLED
  → READ_ONLY_SURVEYED
  → PREFLIGHT_READY
  → SPAWN_REQUESTED_UNCERTAIN
  → FINGERPRINT_ACQUIRING
  → TRUSTED_INACTIVE
  → ACTIVE
  → DISMISSING
  → ABSENT
```

Сейчас допустимы только `DISABLED` и `READ_ONLY_SURVEYED`. Переход к spawn требует protocol revision 3 и доказанного способа получить изначально безопасное тело. Если native call мог создать entity, состояние сразу `SPAWN_REQUESTED_UNCERTAIN`; повтор запрещён.

`IdentityGate` для survivor-кандидата использует session, EntityId, `ModelResource.model`, `ActiveNpcState.npcId` и kind. Нужны три последовательных полных совпадения. Missing/partial data ждёт только ограниченное окно; reflection error сбрасывает серию; timeout и любое расхождение блокируют владение. Текущий офлайн gate не подключён к игре.

Даже полный fingerprint не исключает мгновенную замену идентичным экземпляром. Пока движок не даёт generation ID, это документированный остаточный риск. EntityId сам по себе никогда не даёт права на запись или удаление.

## Безопасный spawn

До runtime-реализации нужно доказать все условия:

1. Template существует на текущем build и имеет ожидаемые components/model/faction.
2. Spawn не конфликтует с survivor uniqueness и не сохраняет нежелательный duplicate.
3. Entity изначально невраждебен либо создаётся неактивным. Подтверждённого inactive-spawn API сейчас нет.
4. Fingerprint доступен после ограниченной инициализации.
5. Faction/activation применяются только к trusted handle и подтверждаются чтением.
6. Dismiss удаляет именно owned instance, а отсутствие подтверждается несколькими callback.
7. Partial failure сохраняет runtime.lock; неизвестная сущность не удаляется и не «усыновляется» позднее.

Если хотя бы один пункт не выполнен, capability `spawn=false`.

## Состояние и сохранение

Постоянное внешнее состояние:

- `companion_id`, personality, memory;
- выбранный `body_key` и версия descriptor;
- будущий inventory ledger только после доказанной транзакционной модели.

Сессионное состояние:

- epoch/session, entity handle и fingerprint;
- pending request, observation counters, invalidation latch;
- runtime.lock и журнал команд.

EntityId, pointers и component proxy не сохраняются между сессиями. Hot reload с живым/неопределённым телом сохраняет barrier и требует recovery.

## Инвентарь и оборудование

Целевой transaction record должен иметь `operation_id`, source/destination, точный stack identity (`itemId`, count, pide и свойства), этап prepare/commit/verify и recovery. Sidecar не может объявлять предмет принадлежащим companion, пока игра не подтвердила перенос. Повтор операции с неопределённым исходом запрещён.

До подтверждения атомарного backend:

- `add/remove/transfer/equip` отсутствуют;
- sidecar не создаёт игровые предметы;
- нет автоматической компенсации через выдачу копии;
- equipment не меняется прямой записью `Inventory`/`SlotSelection`.

## Реализовано и запланировано

| Подсистема | Этап 6 | Будущее условие |
|---|---|---|
| Каталог human candidates | Реализован offline | Обновлять только из закреплённых game data |
| Capabilities | Реализован offline, всё runtime выключено | Включать по одному после игрового доказательства |
| IdentityGate | Реализован и протестирован offline | Подключить после model/component survey |
| Vukah dependency | Вынесена в `legacy_vukah` profile | Не использовать как human body |
| Human spawn/dismiss | BLOCKED | Безопасный lifecycle + protocol v3 |
| Movement | Только evidence для `GoToPosition` | Контроллер + длительное визуальное испытание |
| Combat/interaction | UNKNOWN | Подтверждённые события и state verification |
| Inventory/equipment | BLOCKED | Атомарная transaction/escrow модель |
| Brain/voice/memory | Не реализуются | После стабильного тела |

## План расширения

1. Read-only survey assistant templates.
2. Выбор одного descriptor и фиксация ожидаемых components/model/faction.
3. Threat model и protocol revision 3; миграция `safety_revision` только с тестами.
4. Изолированное испытание lifecycle `spawn → observe → dismiss`, без follow.
5. `moveTo`, затем follow/stay с длительным визуальным наблюдением.
6. Отдельное исследование combat.
7. Отдельный transaction prototype inventory/equipment без Brain.
