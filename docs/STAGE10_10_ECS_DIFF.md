# Stage 10.10 — ECS и resource schemas

Сравнение выполнили 2026-11-18. Старый source — EMF `08d6001`, новый — `fa6efda`.
Дополнительно из **фактически установленного EXE 1287369** извлечены 12 658 типов
и заново сгенерированы headers в ignored runtime. EXE не запускался.

[Машиночитаемый ECS diff](../compatibility/audits/1287369/ecs-diff.json) содержит
сравнение 1289 generated definitions: 1283 совпали по доступным hash/size/fields,
4 изменили layout, 2 добавлены. Removed/type-hash-changed в этом подмножестве не найдены.
Это не утверждение об идентичности всех 12 658 типов: generated coverage уже.
`IDENTICAL` относится к перечисленным полям сравнения. Исходный alignment старого
EXE не восстановлен из packed C++ headers; его сравнение явно `UNKNOWN` в каждой записи.
Номера индексов type table не считаются стабильными type IDs.

| Структура | Старый размер | Новый | Статус |
|---|---:|---:|---|
| keen::ecs::Enemy01BehaviorState | 2504 | 2520 | LAYOUT_CHANGED |
| keen::ecs::UiAutomaticTransferEvent | 32 | 64 | LAYOUT_CHANGED |
| keen::enemy01::CombatSetup | 384 | 392 | LAYOUT_CHANGED |
| keen::enemy01::TargetSelectionSetup | 224 | 232 | LAYOUT_CHANGED |
| keen::ecs::ItemPerkChanged | — | 4 | ADDED |
| keen::enemy01::TargetSelectionBonusSettings | — | 8 | ADDED |

Старые и новые имена/типы/offsets критичных и изменённых полей доступны в JSON;
для остальных одинаковых схем сохранены размер, hash, field count и SHA списка полей.
В изменениях есть добавление
preferredDistanceThreshold у CombatSetup. Изменение layout не обходится старым offset.

[Critical schemas](../compatibility/audits/1287369/critical-schemas.json) содержит
45 текущих определений, включая пары runtime `keen::` и serialized `keen::ds::`.
Содержимое: qualified name, qualified/internal hash, kind, размер, alignment,
field names/types/offsets и доступные enum metadata; без defaults/игровых данных.

| Runtime/resource type | Size / alignment | Qualified hash |
|---|---|---|
| keen::ecs::EntityId | 4 / 4 | b194077d |
| keen::ecs::CharacterSetup | 44 / 4 | fcee256b |
| keen::ecs::RenderEquipment | 788 / 4 | 41c53af5 |
| keen::ecs::TemplateResource | 24 / 4 | 39768775 |
| keen::CharacterPresetCollection | 24 / 4 | 9a6c99e2 |
| keen::ItemInfo | 2088 / 8 | b5ce8765 |
| keen::RenderModel | 352 / 16 | 177394c7 |
| keen::ModelHierarchyResource | 72 / 4 | 358470de |

CurrentTransform, Faction, PlayerState, ActiveNpcState/Saved, ForceSave, DoNotSave,
RenderEquipment, animation, Movement/PathWalker, combat/AI и Inventory включены
в generated diff. CharacterSetup и его девять typed wrapper fields по доступному
layout не изменились. Значения **ресурсов** могли измениться при прежнем layout —
это отдельное [resource comparison](STAGE10_10_TEMPLATE_COMPATIBILITY.md).

У resource-only schemas нет полного старого EXE dump с alignment/enum/dependency
метаданными, поэтому полное old→new ABI равенство TemplateResource,
CharacterPresetCollection, ItemInfo, RenderModel и ModelHierarchyResource остаётся
`UNKNOWN`; текущий decode подтверждён. Не заменяем отсутствующие данные догадкой.

World storage/program stride также менялись: `0xE15DC0 → 0xE179C0`,
`0x1F20 → 0x1F28`. Это documented upstream offsets, не разрешение использовать их
в нашем коде. [ENGINE_MAP](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/docs/ENGINE_MAP.md#L100-L138),
[новые generated headers](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/sdk/include/emf/generated/components.hpp),
[старые headers](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/sdk/include/emf/generated/components.hpp).
