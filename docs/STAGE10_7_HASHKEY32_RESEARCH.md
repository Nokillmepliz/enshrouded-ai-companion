# Stage 10.7 — исследование HashKey32

Статус Phase A: **OFFLINE CONFIRMED, RUNTIME NOT EXECUTED**. Исследована закреплённая ревизия KFC/EML `16708594d686b030d909f2d835b199d879ea9ad8` и EMF reflection исследованной сборки.

## Причина `UNSUPPORTED`

`HashKey32` — четырёхбайтовая структура с единственным `uint32_t value`: `sdk/include/emf/generated/components.hpp:111-120`. Все девять полей `CharacterSetup` имеют этот тип и занимают смещения 4–36. EML представляет reflected struct как `MappedStructValue` userdata. Его `__index` вызывает `get_field`; вложенный `value` типа `UInt32` конвертируется в `LuaValue::Integer(*v as i64)` (`mapped.rs:209-236`, `converter.rs:507-545`). Диапазон `uint32` полностью точен в Lua integer/i64.

Старый `scalar()` разворачивал `.value` только при `type(v)=="table"`. Реальный тип — `userdata`, поэтому код возвращал `UNSUPPORTED` до чтения доступного поля. Patch 0.4.0 читает `v.value` через `pcall`, принимает только целое `0..4294967295`, сохраняет ноль и отклоняет nil, строки, float, отрицательные и переполненные значения. `tostring(userdata)` не используется. HashKey32 не трактуется как GUID.

## Проверенный KFC baseline hunter_assistant

Источник — read-only decode `runtime/research/stage10_5/hunter_assistant.json`, компонент `keen::ecs::CharacterSetup`; это локальный ignored артефакт ранее проверенного KFC и не runtime-подстановка.

| Поле | UInt32 |
|---|---:|
| voicePackId | 3178345104 |
| presetId | 1602195472 |
| hair | 100818570 |
| beard | 0 |
| hairColorId | 2593349132 |
| beardColorId | 2593349132 |
| skinColor | 510686028 |
| eyeBrowColor | 1294605571 |
| eyeColor | 1843389514 |

Эти девять значений подтверждены в KFC source. Совпадение source/clone через исправленный Lua accessor требует нового load-only запуска; Phase A его не выполняла. Экспортёр не содержит эти числа как константы.

Источники: [EML mapped userdata](https://github.com/Brabb3l/kfc-parser/blob/16708594d686b030d909f2d835b199d879ea9ad8/crates/mod-loader-lua/src/env/game/assets/value/mapped.rs), [UInt32 conversion](https://github.com/Brabb3l/kfc-parser/blob/16708594d686b030d909f2d835b199d879ea9ad8/crates/mod-loader-lua/src/env/game/assets/value/converter.rs), [EMF generated reflection](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/sdk/include/emf/generated/components.hpp).
