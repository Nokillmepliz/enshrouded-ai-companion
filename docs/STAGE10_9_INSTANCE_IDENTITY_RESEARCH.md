# Stage 10.9 — instance identity

Дата: 2026-11-01. Исходная база: EMF commit `08d600155fcadc8e45cc9c6f3932a67c717345be`, Enshrouded build 1273043. Runtime не выполнялся.

## Что подтверждено

`keen::ecs::EntityId` содержит единственное поле `uint32_t id`; generation в структуре нет: [components.hpp L168–175](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/sdk/include/emf/generated/components.hpp#L168-L175). Native spawn wrapper возвращает этот `uint32_t`, а `0` означает совокупный отказ: [spawn.h L27–38](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/core/spawn.h#L27-L38), [spawn.cpp L53–64](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/core/spawn.cpp#L53-L64). EMF перечисляет только ID из entity map и читает компоненты по ID: [api.cpp L113–132](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/core/api.cpp#L113-L132).

EMF прямо предупреждает, что entity ID старой сессии не имеют смысла в новой; session number меняется при каждом hosted world: [guide.md L110–118](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/guide.md#L110-L118). Lua `generation` в `bindings.cpp` ограничивает жизнь userdata одним callback и не является поколением entity. Поле `generation` range-query в `ENGINE_MAP.md` относится к query record. Оба запрещено использовать как entity generation.

Native API v5 предоставляет `spawn_ex`: до 15 существующих ECS-компонентов передаются в одном spawn slice вместе с `CurrentTransform`: [emf_api.h L403–406](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/sdk/include/emf/emf_api.h#L403-L406), [spawn.cpp L66–102](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/core/spawn.cpp#L66-L102). API не регистрирует новый component type и не возвращает template GUID, generation или ownership metadata. Подмена неизвестного поля вроде `SpawnTime` токеном нарушила бы семантику игрового компонента и не принимается.

| Механизм | Статус | Ограничение |
|---|---|---|
| EntityId | CONFIRMED | uint32, переиспользуемый handle |
| EMF server session | CONFIRMED | различает hosted sessions, но не экземпляры внутри сессии |
| Runtime template component fingerprint | PARTIAL | повышает уверенность, одинаков у двух экземпляров template |
| Template GUID entity | UNKNOWN | public API его не раскрывает |
| Native entity generation | UNKNOWN/UNAVAILABLE | в исследованных структурах и API не найден |
| Ownership metadata | UNKNOWN/UNAVAILABLE | не найдено |
| Atomic existing-component init через `spawn_ex` | CONFIRMED | нет безопасного уникального ownership-компонента |
| Custom atomic instance marker | UNKNOWN | требует расширения регистрации/хранения identity |

Не исследован игровой allocator глубже wrapper/entity map, поэтому конкретный алгоритм выдачи и момент повторного использования ID не заявляются.

## OwnedEntityIdentity

Офлайн-контракт реализован в `companion/safe_spawn.py`:

`instance_token + entity_generation + template_guid + session_identity + atomic ownership marker`.

Состояния: `CONFIRMED`, `AMBIGUOUS`, `STALE`, `REUSED`, `LOST`. Только `CONFIRMED` разрешает рассматривать адресный destroy, причём отдельным условием остаётся атомарная проверка и удаление. Отсутствующий native generation остаётся `None` и переводит результат в `AMBIGUOUS`; случайное число его не заменяет.

Два NPC одного template нельзя различить по npcId, template GUID, faction или component fingerprint. После reload поиск по этим полям может только сформировать список кандидатов; один кандидат всё равно не доказывает, что это прежний экземпляр.

## Минимально достаточный механизм

Существующего public Lua API недостаточно. Public native `spawn_ex` полезен, но не закрывает marker. Нужен extension, который в одной world-thread операции:

1. создаёт entity и присваивает движково распознаваемый неподлежающий подделке marker;
2. возвращает session, EntityId, реальный generation/эквивалент и template identity;
3. позже внутри одной операции повторно сверяет все поля и вызывает destroy;
4. отказывается при отсутствии любого поля или более чем одном кандидате.

До подтверждения такого marker/generation статус: **NATIVE_EXTENSION_REQUIRED**, gate `INSTANCE_IDENTITY=UNKNOWN`, `OWNERSHIP=UNKNOWN`.
