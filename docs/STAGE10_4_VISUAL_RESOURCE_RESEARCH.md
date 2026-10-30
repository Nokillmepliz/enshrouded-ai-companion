# Этап 10.4 — визуальные ресурсы humanoid NPC

Статус: **BLOCKED — подтверждена схема систем, но конкретные model/mesh/skeleton dependencies не разрешены**. Исследование выполнено офлайн на pinned EMF `08d600155fcadc8e45cc9c6f3932a67c717345be`, pinned `kfc-parser` `16708594d686b030d909f2d835b199d879ea9ad8` и сохранённом evidence этапа 10.2. Игра не запускалась, EML не устанавливался, игровые файлы и сохранения не менялись.

## Reflection компонентов

`template component` ниже означает только классификацию generated reflection. Флаги side/runtime взяты из `docs/components.txt`; они объясняют, почему поле может заполняться системой после создания entity.

| Компонент | Подтверждённые поля | Роль и ограничения |
|---|---|---|
| `keen::ecs::RenderEquipment` | `modelHandles: U32[24]`; `lastModels: Guid[24]`; `colors: ItemRenderColors[24]`; `hideMask: U32`; `uiHideMask: U32`; `foleyMaterialId: HashKey32`; `blendShapeMask: U32`; `renderPoseHandle: RenderPoseHandleValue` | 788 байт, dynamic/client-only. Это данные, а не маркер. `lastModels` — единственные прямые model-like GUID в исследованном наборе, но компонент записывает runtime render-система; значений template/source у нас нет. |
| `keen::ecs::CharacterSetup` | `gender: U8`; `voicePackId`, `presetId`, `hair`, `beard`, `hairColorId`, `beardColorId`, `skinColor`, `eyeBrowColor`, `eyeColor`: `HashKey32`; `useNewProportions: Bool` | 44 байта, dynamic/savegame-relevant. Описывает выбор внешности хешами реестра, прямых GUID/mesh/skeleton полей нет. |
| `keen::ecs::NewCharacterSetup` | полей нет | Однобайтовый dynamic/server-only маркер. Сам не содержит appearance. |
| `keen::ecs::EquipmentCheck` | полей нет | Однобайтовый dynamic/server-only маркер, используемый `apply_charactersetup`. |
| `keen::ecs::InventorySetup` | `linksEntities: EntityId[16]`; `linksCategories: U8[16]`; `inventoryFlags`, `genericSlotCount`, `availableSlotCount: U8`; `isInitialized: Bool` | 84 байта, dynamic/savegame-relevant. Связывает inventory entities; прямых visual resource references нет. |
| `keen::ecs::AnimationGraphResourceComponent2` | `animationGraph: Guid`; `retargetData: Guid`; `maxSnapshotPoses: I32`; `hasServerLogic`, `hasFootstepSyncLogic: Bool` | Прямые ссылки на animation graph/retarget data. Реальный evidence подтвердил `animationGraph=402df515-5965-4b01-a17b-17d482a91af4` у hunter и клона; `retargetData` не экспортировался. |

Связанные структуры:

- `Equipment` содержит `equipmentVisuals: ItemVisual[24]`, где `ItemVisual` состоит из `ItemInstanceInfo` и `EntityId`; также есть `bodyMaterialId: HashKey32`. Прямого model GUID в `ItemVisual` нет.
- `VisualEquipment` — client-only маркер без полей.
- `ItemRenderColors` содержит три `U32` цвета; `RenderPoseHandleValue` — один `U32`; `HashKey32` — один `U32 value`.

Источник: [generated reflection](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/sdk/include/emf/generated/reflection.hpp), [component flags](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/components.txt). Репозиторий содержит read-only parser [reflection_schema.py](../tools/reflection_schema.py), используемый тестами вместо ручного копирования смещений.

## Подтверждённая цепочка систем

1. `TemplateResource` hunter содержит шесть исследуемых компонентов — это подтверждено EML evidence 10.2. Source и clone имеют одинаковый полный component set (`STRUCTURAL_MATCH`).
2. Server system `apply_charactersetup` читает `InventorySetup`, опциональный `NewCharacterSetup`, `CharacterPresetRegistry` и `ItemRegistry`, использует `EquipmentCheck` и пишет `CharacterSetup` и inventory state. Это подтверждает получение appearance из preset/item registries, но не раскрывает значения реестров.
3. `equipment_visuals` читает `CharacterSetup`, slot/inventory/item state и те же registries, затем пишет `Equipment` и `EquipmentAnimationSets`.
4. Client system `render_equipment_models_ag2` читает `CharacterSetup`, animation graph runtime state, slot/inventory/item state и registries, пишет `RenderEquipment` и `RenderScene`.
5. Клиентская и серверная animation systems читают template `AnimationGraphResourceComponent2`; `CharacterSetup` для них только optional runtime input.

Источники: [`apply_charactersetup`](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/ecs_programs.md#L92), [`equipment_visuals`](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/ecs_programs.md#L271), [`render_equipment_models_ag2`](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/ecs_programs.md#L600), [animation systems](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/ecs_programs.md#L175).

```text
Template markers/setup
  -> CharacterPresetRegistry + ItemRegistry + inventory links       CONFIRMED_FROM_SOURCE
  -> CharacterSetup (preset/hair/colors as HashKey32)               CONFIRMED_FROM_SOURCE
  -> Equipment / EquipmentAnimationSets                             CONFIRMED_FROM_SOURCE
  -> RenderEquipment.lastModels + RenderScene                       CONFIRMED_FROM_SOURCE
  -> concrete model/mesh/skeleton resources                         UNKNOWN
```

Следствия по вопросам внешности:

- тип/лицо/волосы/цвета задаются `CharacterSetup` через `gender`, `presetId` и HashKey32 choices; конкретные значения hunter неизвестны;
- одежда и предметы проходят через inventory/slot/item registry в `Equipment`, затем в `RenderEquipment`;
- animation graph задан template GUID; `retargetData` потенциально связан с адаптацией скелета, но реальная ссылка неизвестна;
- отдельного подтверждённого skeleton или mesh field в этих компонентах нет;
- `RenderEquipment.lastModels` наиболее близок к resolved visual model list, но это client runtime output. Наличие компонента в template не доказывает заполнение массива или успешное разрешение ресурсов.

## EML и KFC

EML `game.assets.get_resource` выполняет lookup GUID+type+part и возвращает lazy mapped resource. Вложенные struct/array доступны через mapped values; GUID преобразуется в Lua string; отсутствующее mapped поле возвращает nil. `get_resource`, `get_resource_parts`, `get_resources_by_type` и `get_resource_types` читают AppState. `create_resource` меняет AppState, а `io.export` пишет файл; они не являются чистым read-only lookup.

Готов source-only инструмент [kfc_readonly_inspect](../tools/kfc_readonly_inspect/README.md). Он использует pinned `KFCReader`, `TypeRegistry::load_from_executable` и `Value::from_bytes_with_options`, читает один GUID/type и запрещает output внутри каталога игры и перезапись. Read-only preflight оригинального KFC подтвердил `KFC4`, входы и отсутствие записей, но обнаружил `cargo=null`, `rustc=null`. Бинарник не собран и не запускался; структурные данные hunter/blacksmith из KFC не получены. Системная или локальная установка Rust без разрешения не выполнялась.

## Сравнение шаблонов

| Проверка | hunter source | clone `aic_eml_humanoid` | blacksmith |
|---|---|---|---|
| Component set | подтверждён evidence 10.2 | совпадает с hunter | dump отсутствует |
| Шесть visual components | присутствуют | присутствуют | UNKNOWN |
| Animation graph | `402df515-5965-4b01-a17b-17d482a91af4` | совпадает | UNKNOWN |
| `CharacterSetup` values | UNKNOWN | deep-copy предполагает те же serialized values, но они не экспортированы | UNKNOWN |
| `RenderEquipment.lastModels` | UNKNOWN/runtime-generated | UNKNOWN/runtime-generated | UNKNOWN |
| Mesh/skeleton dependencies | UNKNOWN | UNKNOWN | UNKNOWN |

Новый template отсутствует в исходном KFC; сведения о нём происходят только из сохранённого EML evidence. Blacksmith GUID известен, но component/resource dump отсутствует.

## Вердикт и минимальный следующий шаг

Получен проверяемый **structural visual fingerprint**: одинаковый набор visual components плюс одинаковый animation graph. Это уровень `STRUCTURAL_MATCH`, а не доказательство модели. `RESOURCE_REFERENCES_MATCH`, `VISUAL_DEPENDENCIES_RESOLVED` и `RUNTIME_RENDER_CONFIRMED` остаются `UNKNOWN`.

Минимальный следующий шаг — отдельно разрешить установку Rust 1.88 в локальный каталог проекта, собрать и проверить inspector из source, затем read-only извлечь `hunter_assistant`, `blacksmith_assistant`, `CharacterPresetRegistry` и связанные ItemRegistry entries в JSON вне каталога игры. Если registry data не сериализуется как KFC resource, понадобится отдельный load-only EML export подтверждённых `CharacterSetup`, `AnimationGraphResourceComponent2.retargetData` и `RenderEquipment.lastModels` с ожиданием, что runtime-only поля могут остаться пустыми. Spawn для этого не нужен и не разрешён.
