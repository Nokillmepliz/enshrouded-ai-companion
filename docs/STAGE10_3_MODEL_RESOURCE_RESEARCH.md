# Этап 10.3 — исследование model resource

Статус: **BLOCKED**. Настоящий model fingerprint `hunter_assistant` офлайн не получен. Игра не запускалась, EML не устанавливался, игровые файлы и сохранения не изменялись.

## Причина `model_guid=nil`

Evidence реального запуска 10.2 перечисляет компоненты и клона, и source. В обоих списках отсутствует `keen::ecs::ModelResource`; при этом присутствуют `CharacterSetup`, `NewCharacterSetup`, `EquipmentCheck`, `InventorySetup` и `RenderEquipment`. Поэтому прежний вызов `component(..., "keen::ecs::ModelResource")` вернул `nil`, а выражение `new_model and new_model.model` не дошло до чтения поля. Это не доказывает отсутствия человеческой модели у отображаемой сущности; оно доказывает отсутствие непосредственного `ModelResource` в сериализованном `TemplateResource` `hunter_assistant`.

## Подтверждённые контракты

| Структура | Класс доказательства | Вывод |
|---|---|---|
| `keen::ecs::ModelResource` имеет одно поле `model`, тип `Guid` | `CONFIRMED_FROM_SOURCE` | EMF generated reflection: тип начинается в записи `ModelResource`, поле `model` — GUID размером 16 байт. |
| `AnimationGraphResourceComponent2.animationGraph` и `.retargetData` — GUID | `CONFIRMED_FROM_SOURCE` | Оба поля присутствуют в generated reflection; реальный export 10.2 получил одинаковый `animationGraph` source/clone. |
| Отсутствующее поле mapped struct возвращает Lua `nil` | `CONFIRMED_FROM_SOURCE` | `MappedStructValue::get_field` возвращает `LuaValue::Nil`, если `data.get(key)` не дал значение. Это не ошибка `tostring`. |
| Mapped GUID передаётся в Lua как строка | `CONFIRMED_FROM_SOURCE` | `MappedValue::Guid` вызывает `guid.to_string()` и создаёт Lua string. GUID-object/table не является ожидаемым контрактом чтения. |
| Source и clone этапа 10.2 не содержали `ModelResource` | `CONFIRMED_FROM_OFFLINE_ASSET` | Сохранённый EML export был сформирован из загруженного игрового ресурса и после испытания анализируется без игры; оба component fingerprints совпадают и не содержат компонент. Это runtime-derived asset evidence, а не прямой dump KFC. |
| Человеческий renderable собирается через `RenderEquipment`/setup/equipment | `LIKELY` | Компоненты присутствуют, а reflection подтверждает их типы. Конкретная цепочка до mesh/skeleton и её resource GUID не установлены. |
| Точная model dependency `hunter_assistant` | `UNKNOWN` | Ни прямой GUID, ни подтверждённый field path внешней зависимости не извлечены. |
| Использовать `ModelResource.model` как обязательный fingerprint этого survivor template | `UNSUPPORTED` | Реальный source template не содержит компонента. |

Исходники: [EMF reflection, pinned commit](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/sdk/include/emf/generated/reflection.hpp), [EML mapped value](https://github.com/Brabb3l/kfc-parser/blob/16708594d686b030d909f2d835b199d879ea9ad8/crates/mod-loader-lua/src/env/game/assets/value/mapped.rs#L162-L204), [EML GUID conversion](https://github.com/Brabb3l/kfc-parser/blob/16708594d686b030d909f2d835b199d879ea9ad8/crates/mod-loader-lua/src/env/game/assets/value/converter.rs#L557-L569), [assets API](https://github.com/Brabb3l/kfc-parser/blob/16708594d686b030d909f2d835b199d879ea9ad8/crates/mod-loader-lua/src/env/game/assets.rs#L32-L52).

## Офлайн KFC

Прочитаны без изменения оригинальные файлы build 1273043:

- `enshrouded.kfc`: `54a8cb76b3229c486ef55a7ababcd48828fa0ffc5bb144d206f687fd0ab00a92`;
- `enshrouded.kfc_resources`: `53786c45797d275661f3ccc1fd8c84527a74f376e01f05fc76351f91fb17cb3d`.

Простой binary string search не нашёл GUID/имена `hunter_assistant` и `blacksmith_assistant`, что ожидаемо для индексированного бинарного формата и ничего не говорит об их отсутствии. Закреплённый `kfc-parser` действительно содержит read/write библиотеку и deprecated unpack CLI, но в среде нет Rust toolchain и проверенного read-only parser-бинарника. Официальный `emm.exe` не запускался: его рабочий путь загружает моды и может писать patch, поэтому он не подходит для гарантированно read-only извлечения. Прямой структурный dump KFC не получен.

Сравнение с `blacksmith_assistant` ограничено подтверждённым GUID `04d42ed2-beb4-4013-8f10-5d63efae2015`: component dump для него отсутствует. Делать вывод об одинаковой визуальной цепочке нельзя.

## Клонирование и риски

`create_resource(source.data, TemplateResource, ...)` получает весь mapped `source.data`; реальный evidence подтвердил одинаковые списки компонентов, animation graph и неизменность source. Это подтверждает структурный clone сериализованных данных, но не доказывает, что внешние render/equipment зависимости разрешатся после создания entity. Skeleton, mesh, материалы, appearance, lifecycle, uniqueness, ownership и dismiss остаются `UNKNOWN` до отдельной read-only проверки и более позднего контролируемого spawn.

Минимальная следующая проверка: отдельно согласованный load-only запуск версии 0.2.0 должен экспортировать typed `MISSING/component_missing` для обоих ресурсов и компактно подтвердить его observer. Чтобы получить настоящий model fingerprint, нужен проверенный read-only KFC exporter либо новый EML export только подтверждённых полей `RenderEquipment`/setup после изучения их точного asset schema. Поля наугад добавлять нельзя.
