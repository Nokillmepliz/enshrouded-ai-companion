# Stage 10.8 — исследование spawn/despawn API

Дата: 2026-11-01. Исследован закреплённый EMF commit `08d600155fcadc8e45cc9c6f3932a67c717345be`. Итог: **BLOCKED_FOR_SPAWN**.

## Подтверждённый API

Lua binding принимает ровно `world`, GUID-строку и три числа, парсит GUID и передаёт их в `api->spawn`; результат возвращается как Lua integer: [`bindings.cpp` L816–824](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/lua_host/bindings.cpp#L816-L824). Конкретный вызов:

```lua
local entity_id = emf.spawn(world, "a1c90001-5e4d-4a91-8a1c-000000000001", x, y, z)
```

Core разрешает вызов только в server world, создаёт единственный spawn component `CurrentTransform`, переводит метры в fixed 32.32, задаёт quaternion `w=1` и scale 1, затем возвращает `EntityId`: [`spawn.cpp` L53–66](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/core/spawn.cpp#L53-L66). Параметра yaw/orientation в public spawn API нет. Нулевой результат объединяет неизвестный template, плохие данные и native fault; SEH wrapper возвращает `0`: [`spawn.cpp` L16–22](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/core/spawn.cpp#L16-L22).

Binding удаления принимает только `world` и числовой ID: [`bindings.cpp` L827–831](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/lua_host/bindings.cpp#L827-L831). Core вызывает native destroy и возвращает `true`, если вызов не вызвал SEH; это не наблюдение исчезновения: [`spawn.cpp` L24–30](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/core/spawn.cpp#L24-L30). EMF отдельно отказывает для entity с `PlayerState`: [`api.cpp` L765–770](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/core/api.cpp#L765-L770).

Публичная документация подтверждает host-only `spawn/destroy`, `world:entities`, `world:position`, dynamic `world:get` и read-only template component по уже существующей entity: [`lua.md` L98–121](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/lua.md#L98-L121), [`lua.md` L158–175](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/lua.md#L158-L175).

## Наш TemplateResource

Binding не содержит allowlist GUID: корректные 16 байт передаются игровому spawn wrapper. Поэтому API **может попытаться** использовать собственный GUID. Stage 10.7 доказал EML serialization и asset-manager lookup, но не доказал, что игровой spawn wrapper разрешит этот resource. Единственный допустимый runtime ответ на этот вопрос — отдельно разрешённый spawn; Phase A не выполняет его.

До создания template уже содержит `Faction=PlayerAlly (11)`. Это устраняет гонку post-spawn faction write, но не доказывает фактическую dynamic faction или отсутствие агрессии. Будущая проверка обязана наблюдать `Faction=11` и отсутствие hostile behavior; fallback на hostile template запрещён.

## Identity и ownership

Spawn возвращает только `EntityId`. EMF предупреждает, что ID переиспользуются и после reload, и внутри сессии: [`pet_follow/README.md` L15–18](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/examples/lua/pet_follow/README.md#L15-L18). `emf.session_token()` связывает ID с процессом/сессией, но не является generation ID экземпляра: [`lua.md` L121](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/lua.md#L121).

После spawn можно сверить ID, session token, `ActiveNpcState.npcId=2939921867`, faction, компонентные признаки, animation/model fields и position несколько callbacks подряд. Public Lua не возвращает template GUID сущности и не даёт поставить атомарный instance marker вместе со стандартным `emf.spawn`. Поэтому точное владение экземпляром и безопасное удаление после потери handle/reload не доказаны.

## Позиция и ориентация

Spawn принимает необработанные `x/y/z`. В Lua surface нет raycast/navmesh/voxel/ground-query до создания. Ground search доступен только как часть `emf.teleport` уже существующей entity; даже при отсутствии walkable spot он оставляет entity в исходной точке: [`lua.md` L142–154](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/lua.md#L142-L154). Spawn с последующим teleport сначала уже создаёт NPC в непроверенной геометрии и не удовлетворяет контракту. Телепортация игрока как обход не рассматривается.

Итог: безопасная surface/geometry validation до spawn отсутствует в подтверждённом public API. Это самостоятельный blocker.

## Persistence

Пример `pet_follow` утверждает, что его spawned creatures не сохраняются: [`README.md` L7–9](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/examples/lua/pet_follow/README.md#L7-L9). Но это нельзя переносить на clone villager. Документация EMF отдельно говорит, что обычные spawn не сохраняются **кроме villagers**: [`guide.md` L113–118](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/guide.md#L113-L118). Исследование villages связывает `ForceSave` у всех villager templates с сохранением и описывает уничтожение дубликатов по template GUID: [`re_villages.md` L124–131](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/re_villages.md#L124-L131).

Наш clone содержит `ForceSave`, `ActiveNpcState` и `ActiveNpcStateSaved`. Удалять их без исследования нельзя. Возможны сохранение в KSD и unique-NPC lifecycle. Persistence и поведение после reload остаются `UNKNOWN` и блокируют spawn.

## Ответы по API

1. Создание: `emf.spawn(world, guid, x, y, z)` в server callback.
2. Собственный GUID синтаксически поддержан; spawnability resource не проверена.
3. Позиция — raw metres; orientation всегда identity quaternion.
4. Faction приходит из template, затем доступна dynamic `world:get`; runtime не проверен.
5. Handle — возвращённый uint32 `EntityId`, либо `0` при неоднозначном отказе.
6. Identity можно усилить fingerprint-наблюдением, но native instance identity отсутствует.
7. Удаление: `emf.destroy(world, id)`; перед вызовом проект требует точную identity, которой сейчас нет.
8. Humanoid villager с `ForceSave` может сохраниться; точный результат неизвестен.

Неподтверждённые identity, безопасная позиция и persistence означают: `spawn_ready=false`.
