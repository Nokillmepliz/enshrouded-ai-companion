# EML Humanoid Template — исследование этапа 9

Дата: 2026-10-30. Вердикт: **создание нового `TemplateResource` технически подтверждено; игровой humanoid body остаётся `BLOCKED` до двух раздельных испытаний — загрузки patch и затем контролируемого spawn**.

## Источники и воспроизводимость

Исследованы без установки и запуска игры:

- официальный репозиторий EML/KFC parser, tag `v0.2.0`, commit [`16708594`](https://github.com/Brabb3l/kfc-parser/tree/16708594d686b030d909f2d835b199d879ea9ad8), GPL-3.0;
- [официальная документация EML](https://brabb3l.github.io/kfc-parser/eml/), включая [структуру мода](https://brabb3l.github.io/kfc-parser/eml/develop/setup.html) и [Resource API](https://brabb3l.github.io/kfc-parser/eml/api/assets/resource.html);
- pinned EMF `08d600155fcadc8e45cc9c6f3932a67c717345be`, особенно [проверенный генератор новых creature templates](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/tools/models/make_mod.py) и [исследование content patch на build 1273043](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/re_content.md);
- pinned Enshwick `135561192969af9ec9ffd0957b97ca6a7aa31820`, включая [каталог workshop survivors](https://github.com/enshwick/enshwick/blob/135561192969af9ec9ffd0957b97ca6a7aa31820/crates/enshwick/src/survivors/workshop.rs#L161-L190).

Локальные upstream checkout находятся в `.research/` и не публикуются. Проверка прототипа выполняется командой `python -m unittest tests.test_eml_humanoid -v`; она не читает каталог игры.

## Что такое EML

EML — отдельный от EMF Lua loader/framework для изменения asset database Enshrouded до загрузки данных игрой. Официальная документация прямо ограничивает текущую реализацию asset modifications; runtime capability остаётся WIP. EML читает отражённые типы KFC, исполняет `src/mod.lua`, накапливает dirty/new resources и записывает новый индекс/контент. Это видно в [`mod-loader-lua`](https://github.com/Brabb3l/kfc-parser/tree/16708594d686b030d909f2d835b199d879ea9ad8/crates/mod-loader-lua) и его [`AppState`](https://github.com/Brabb3l/kfc-parser/blob/16708594d686b030d909f2d835b199d879ea9ad8/crates/mod-loader-lua/src/env/app_state.rs).

Подтверждённый layout:

```text
<mod-id>/
  mod.json
  README.md
  src/mod.lua
```

`.luarc.json` нужен только редактору. Manifest требует `id`, `name`, semver `version`, `capabilities`; после подготовки этапа 10 prototype использует `patch` и `export`: первый создаёт ресурс, второй пишет диагностический fingerprint. EML mod не является EMF Lua mod и не загружается EMF самостоятельно.

## Новый resource и новый GUID

`game.assets.create_resource(value, type)` создаёт resource с random UUID. Перегрузка с `(value, type, guid, part)` принимает фиксированный GUID; EML отказывает при совпадении тройки GUID/type/part. Реализация находится в [`assets.rs`](https://github.com/Brabb3l/kfc-parser/blob/16708594d686b030d909f2d835b199d879ea9ad8/crates/mod-loader-lua/src/env/game/assets.rs) и `AppState::add_resource`.

Это подтверждает именно **создание**, а не редактирование vanilla resource. Pinned EMF применяет тот же механизм: копирует source `keen::ecs::TemplateResource`, задаёт новый fixed GUID, меняет его компоненты и условно добавляет GUID в `keen::GuidRegistryResource`. Его генератор уже использовался для новых creature templates. Поэтому минимальный способ для проекта:

1. получить source template по vanilla GUID;
2. deep-copy `source.data` в новый `TemplateResource` с нашим fixed GUID;
3. изменить только данные нового resource;
4. добавить новый GUID в registry лишь если source там зарегистрирован;
5. остановить patch через `assert`, если обязательный source/component исчез.

Наш GUID `a1c90001-5e4d-4a91-8a1c-000000000001` не совпадает с 18 известными story templates. Полную глобальную уникальность можно окончательно проверить только на реальной resource database: сам EML fail-closed отклонит collision. Смена GUID после использования недопустима, потому что ссылки/сохранённые identity зависят от него.

## База humanoid и зависимости

Прототип клонирует подтверждённый `hunter_assistant` (`e3736dff-0ad2-47fc-903c-66c1775836e8`). Это обеспечивает глубокое копирование существующих ссылок на человеческую модель, skeleton, animation graph и всех template components. Исходный story resource не меняется.

Такой выбор доказывает повторное использование human asset graph, но пока не доказывает пригодность NPC как компаньона. Без read-only export build 1273043 неизвестны конкретные model/animation GUID и полный набор зависимостей. Унаследованные `ActiveNpcState`, `ForceSave`, workshop/bed/job/socializing компоненты могут сделать новый template уникальным villager и связать его со штатным lifecycle. Прототип рассчитан на **одного** собственного NPC; несколько экземпляров не заявлены.

`ActiveNpcState.npcId` — FNV-1a 32 от 16 байтов template GUID в memory/Windows GUID order. Это подтверждают [Enshwick `Guid::fnv1a`](https://github.com/enshwick/enshwick/blob/135561192969af9ec9ffd0957b97ca6a7aa31820/crates/enshwick/src/content/ids.rs) и совпадения всех проверенных survivor pairs. Для нового GUID значение равно `2939921867`; patch вычисляет его через `game.guid.hash` и записывает в cloned `ActiveNpcState`, не копируя identity Hunter Assistant.

Не доказаны:

- нужна ли ещё отдельная регистрация NPC identity помимо template GUID/`npcId`;
- примет ли `NpcRegistry` новый unique NPC;
- как `ForceSave` сериализует mod template и что произойдёт после удаления patch;
- можно ли безопасно иметь более одного экземпляра;
- переживёт ли entity выключение patch без потери/ошибки world save.

## Безопасная faction

Clone до записи получает `Faction = PlayerAlly`, а patch делает `assert`, если `Faction` отсутствует. Значение `PlayerAlly` равно 11 и входит в player side; это подтверждено [исследованием combat rules EMF](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/combat.md). Поскольку template data патчится до любого будущего spawn, безопасная faction не зависит от первого EMF callback. Это устраняет конкретную гонку, из-за которой Vukah этапа 5 появился враждебным.

Офлайн-код подтверждает запись значения в новый resource. Только игровой read-only осмотр может подтвердить, что загрузчик сохранил значение и никакая villager system не заменила faction при создании. До такого подтверждения spawn запрещён.

## Модель, анимации, движение и бой

Deep copy сохраняет все resource references source template. Поэтому повторное использование human model/skeleton/animation graph технически поддерживается без копирования бинарных assets. Точные ожидаемые GUID оставлены `None`, а не выдуманы.

Pinned EMF показывает, что `ActiveNpcState` поддерживает villager locomotion/roaming и что `NpcCommandEvent.GoToPosition` адресует NPC по `npcId`; см. [AI research](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/ai.md). Это даёт статус `LIKELY` для `moveTo`, но не подтверждает новый template. Follow, длительный stay, enemy selection и combat остаются `UNKNOWN`; patch их не реализует.

## Inventory и equipment

Клонирование переносит только компоненты, уже присутствующие в source. Наличие `InventorySetup` или `Equipment` само по себе не создаёт работающий NPC inventory: нужны registry initialization, server authority, transaction paths, save/network replication и visual equipment systems. Upstream ECS map показывает эти системы, но ни одна офлайн-проверка не доказала их совместимость с новым villager. Поэтому `inventory` и `equipment` имеют статус `UNKNOWN`, а mutations отсутствуют.

## EML вместе с EMF

Это независимые loaders. EML patch должен завершиться до чтения KFC игрой; затем EMF runtime видит уже загруженные resources и теоретически может вызвать `emf.spawn` с новым template GUID. Последняя связь является обоснованным выводом из двух подтверждённых механизмов, а не игровым результатом.

EMF обычно занимает `dinput8.dll`, EML документирует `dbghelp.dll`; EMF также умеет chain-load DLL. Совместное присутствие по разным proxy names возможно архитектурно, но конкретная комбинация build 1273043 + EMF 0.3.2 + EML 0.2.0 ещё не запускалась. EML source умеет сверять/extract type registry, а pinned EMF получил `types.json` version `1273043|^/game38/branches/release_1.0|2026-10-20`; это подтверждает совместимый формат данных, но не равнозначно бинарному compatibility test.

Data patch меняет KFC/data files, поэтому нужен отдельный backup/restore. EML re-applies patches после обновления игры. Для multiplayer одинаковый data patch нужен каждому процессу; первый эксперимент ограничен LOCAL world.

## Identity и ownership

Новый template GUID надёжно отличает **тип** от vanilla story NPC и подтверждает происхождение template из нашего patch. Он не различает два экземпляра одного template и не защищает от reuse `entityId`. EML не позволяет добавить новый произвольный ECS component type как marker: отражённые типы определены игрой.

Поэтому descriptor намеренно содержит:

- новый template GUID и ожидаемый `npcId`;
- `initial faction = 11`;
- неизвестные model/animation GUID до export;
- `creation_marker = None` и `ownership_proof = None`;
- `safe_dismiss_proven = false`;
- `runtime_enabled = false`.

Рабочий spawn allow-list и существующий `IdentityGate` не изменены. Нельзя удалять сущность только по template GUID/entityId.

## Офлайн-прототип и вердикт

[`experimental/eml_humanoid`](../experimental/eml_humanoid/) соответствует реальному EML layout и API. Он:

- создаёт новый resource с fixed GUID;
- копирует source humanoid, не редактируя его;
- задаёт новый `npcId` и `PlayerAlly` до spawn;
- не вызывает EMF, spawn, faction runtime write, destroy или inventory;
- не читает сохранения и не устанавливается автоматически;
- не входит в основной runtime/package.

Структура и safety invariants проверяются офлайн. Это **технически корректный patch prototype**, но не готовое игровое тело. Блокеры: фактическая загрузка EML/EMF вместе; точные model/animation/component fingerprints; workshop/unique/save behavior; instance ownership marker; безопасный dismiss; совместимость `GoToPosition`; inventory/equipment и combat.
