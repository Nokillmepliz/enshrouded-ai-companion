# Stage 10.9 — ForceSave, villager persistence и lifecycle

Дата: 2026-11-01. Runtime нашего template не выполнялся.

## Подтверждённые факты

`ForceSave` — однобайтовый marker, `ActiveNpcState` содержит `npcId`, а `ActiveNpcStateSaved` — сохранённое состояние со `spawnPosition` и другими полями: [components.hpp ForceSave L11331–11338](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/sdk/include/emf/generated/components.hpp#L11331-L11338), [ActiveNpcState L2246–2253](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/sdk/include/emf/generated/components.hpp#L2246-L2253), [ActiveNpcStateSaved L2288–2295](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/sdk/include/emf/generated/components.hpp#L2288-L2295). `DoNotSave` также является однобайтовым marker: [components.hpp L8022–8029](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/sdk/include/emf/generated/components.hpp#L8022-L8029).

EMF runtime research показал, что произвольно spawned roots, chest, feeder и animal исчезли после reload; даже добавленный через `spawn_ex` `ForceSave` не сделал root сохраняемым: [re_villages.md L199–201](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/re_villages.md#L199-L201). Guide отдельно указывает исключение для villagers: [guide.md L110–119](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/guide.md#L110-L119).

Villager lifecycle включает `unique_npc_init` и `unique_npc_spawns`; первая программа пишет `ActiveNpcStateSaved`, вторая читает его и работает с NpcRegistry/PlayerBasesSystemServer: [ecs_programs.md L757–759](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/ecs_programs.md#L757-L759). EMF research сообщает одну entity на villager template и уничтожение дубликатов по template GUID, но точный путь KSD/restore для нового EML GUID не исследован полностью: [re_villages.md L126–132](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/re_villages.md#L126-L132).

Следствия:

- `ForceSave` не равен гарантии сохранения.
- Отсутствие `ForceSave` не доказывает, что villager не попадёт в особый lifecycle.
- `ActiveNpcStateSaved` участвует в инициализации/unique spawn, но наличие структуры не доказывает фактическую запись KSD нового template.
- Render/animation используют другие компоненты; прямой dependency на эти три marker/state в render programs не найден. Это только статический признак, не runtime-гарантия отсутствия побочных эффектов при удалении.

## Проект двух вариантов

Окончательные GUID/npcId не назначены, Stage 10.7 template не меняется.

### `aic_humanoid_visual_test`

Предлагаемый diff для отдельного template: сохранить подтверждённые `CharacterSetup`, `RenderEquipment`, animation graph и visual references; удалить `ForceSave`, `ActiveNpcState`, `ActiveNpcStateSaved`; добавить `DoNotSave` только после проверки EML serialization и game semantics. Без `ActiveNpcState` возможна потеря villager AI/initialization, поэтому вариант пока `DESIGN_ONLY`. Его временность должна быть доказана quit/reload и KSD comparison.

### `aic_humanoid_companion`

Отдельный будущий GUID/npcId; сохранить villager state только после исследования регистрации в NpcRegistry, duplicate policy, save/load и controlled removal. Permanent lifecycle требует собственного per-world identity record и разрешённой процедуры восстановления. Сейчас `DESIGN_ONLY`.

`classify_persistence()` принимает runtime provenance и результаты reload/restore. Статический component diff всегда остаётся `UNKNOWN`. Gate `PERSISTENCE=UNKNOWN`.
