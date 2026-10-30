# Второй игровой персонаж как тело AI Companion

Статус исследования: **вариант A — `UNSUPPORTED`, вариант B — `UNKNOWN` и не является настоящим игроком, вариант C — `LIKELY` как архитектура, но управление ИИ ещё не подтверждено**.

Игра, второй клиент и spawn на этапе 7 не запускались. Анализ сохранений был только read-only: перечисление имён, размеров и времени изменения файлов. Никакие игровые файлы и сохранения не менялись.

## Источники и границы доказательств

- EMF закреплён на commit [`08d600155fcadc8e45cc9c6f3932a67c717345be`](https://github.com/matenm/emf-enshrouded/tree/08d600155fcadc8e45cc9c6f3932a67c717345be).
- Enshwick закреплён на commit [`135561192969af9ec9ffd0957b97ca6a7aa31820`](https://github.com/enshwick/enshwick/tree/135561192969af9ec9ffd0957b97ca6a7aa31820).
- Исследованная сборка игры: `1273043`; её соответствие установленному EMF 0.3.2 ранее зафиксировано в [EMF_DISTRIBUTION_AUDIT.md](EMF_DISTRIBUTION_AUDIT.md).
- Официальная документация Enshrouded подтверждает кооператив до 16 игроков и перенос персонажем экипировки, инвентаря, уровней и навыков между серверами: [FAQ Enshrouded](https://enshrouded.zendesk.com/hc/en-us/articles/9223654187805-Frequently-Asked-Questions).
- Официальная документация сервера подтверждает, что character progression хранится на клиенте, а world progression — на сервере: [Dedicated Server FAQ](https://enshrouded.zendesk.com/hc/en-us/articles/16056312924957-Dedicated-Server-FAQ).
- Steam не разрешает одновременную игру двух клиентов под одним аккаунтом; для нескольких клиентов нужны отдельные аккаунты и лицензии: [Steam Account Use](https://help.steampowered.com/en/faqs/view/71EA-CDCE-FB5C-82B3), [multiple clients](https://help.steampowered.com/en/faqs/view/48C1-A297-4839-8BB8). Steam Families допускает одновременный запуск одной игры только при наличии нескольких копий в семье: [Steam Families FAQ](https://help.steampowered.com/en/faqs/view/054C-3167-DD7F-49D4).

Статусы в таблицах:

- `CONFIRMED` — подтверждено API, исходником или зафиксированным runtime-исследованием;
- `LIKELY` — механизм существует, но требуемая комбинация не проверена;
- `UNKNOWN` — доказательств недостаточно;
- `UNSUPPORTED` — доступный API прямо не предоставляет требуемую операцию или запрещает её.

## Краткие ответы

1. **Загрузить второй выбранный в меню character save в уже работающий мир без второго клиента нельзя через подтверждённый EMF API.** EMF возвращает локального или уже подключённых игроков, но не создаёт server player slot, network peer или account authority.
2. **Создать через EMF независимую копию персонажа с полной player-семантикой не подтверждено.** `spawn(template)` создаёт entity из template; наличие компонентов `PlayerInput`, `Inventory` или `Equipment` не создаёт подключённого игрока.
3. **Второй клиент — наиболее реалистичный путь к настоящему персонажу.** Он штатно создаёт player slot/entity и сохраняет character progression. Не подтверждены управление этим клиентом через ИИ, одновременный запуск двух графических клиентов на текущем ПК и приемлемая производительность.
4. **Настоящие инвентарь, экипировка, характеристики и прогресс гарантирует только вариант C.** В A это было бы возможно по замыслу, но создание такого игрока не поддержано; B требует отдельной имитации и остаётся NPC/копией.

## Player entity и authority

| Механизм | Статус | Доказательство | Следствие |
|---|---|---|---|
| Получить локального игрока | `CONFIRMED` | [`emf.local_player()` возвращает entity id из client world](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/reference.md#L111-L125) | Можно идентифицировать основного персонажа; это не фабрика игроков. |
| Перечислить подключённых игроков | `CONFIRMED` | Enshwick [`HostApi::players`](https://github.com/enshwick/enshwick/blob/135561192969af9ec9ffd0957b97ca6a7aa31820/crates/enshwick/src/abi/host_api.rs#L110-L125) | Сервер видит только уже существующие подключения. |
| Связать entity с игроком | `CONFIRMED` | [`PlayerInfo`: slot, entity, стабильный account key](https://github.com/enshwick/enshwick/blob/135561192969af9ec9ffd0957b97ca6a7aa31820/crates/enshwick/src/abi/events.rs#L415-L440) | Для ownership нужны session + account key + slot + entity, а не один EntityId. |
| Player slot требует живое подключение | `CONFIRMED` | Enshwick читает slot только при ненулевом handle, состоянии `IN_GAME` и entity: [`world.rs`](https://github.com/enshwick/enshwick/blob/135561192969af9ec9ffd0957b97ca6a7aa31820/crates/internal/loader/src/world.rs#L561-L618) | Простого spawn entity недостаточно. |
| Создать player slot / network peer | `UNSUPPORTED` | В публичных EMF spawn/entity API такой операции нет; `spawn` принимает template и position | Вариант A заблокирован. |
| Удалить player entity | `UNSUPPORTED` | Enshwick [`destroy` отказывает для entity подключённого игрока](https://github.com/enshwick/enshwick/blob/135561192969af9ec9ffd0957b97ca6a7aa31820/crates/internal/loader/src/entities.rs#L159-L174) | `dismiss` для C означает штатный выход второго клиента, а не destroy. |
| Получить постоянный идентификатор игрока | `CONFIRMED` | EMF Lua предоставляет [`world:account(id)`](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/lua.md#L158-L172) | Личность компаньона связывается с внешним UUID и ожидаемым account key; entity id остаётся сессионным. |

EMF различает server/client world. На клиенте чужого мира server world отсутствует, но local player берётся из client world. Gameplay changes предназначены для server world хоста. Это означает, что host-side EMF подходит для наблюдения и серверных разрешённых операций, но не доказывает возможность генерировать локальный ввод второго клиента.

## ECS-компоненты игрока

Сгенерированный SDK EMF 0.3.2 содержит `ClientPlayerInput`, `PlayerInput`, `ServerConsumedPlayerInput`, `PlayerLocomotion`, `PlayerState`, `NetworkActor`, `NetworkPlayerAttributes`, `Inventory`, `InventorySetup`, `Equipment`, `RenderEquipment` и `VisualEquipment`. Каталог компонентов помечает стороны исполнения:

- `ClientPlayerInput` — client-only, dynamic, do-not-save;
- `PlayerInput`, `PlayerLocomotion`, `Equipment` — server-only/dynamic, часть из них do-not-save;
- `Inventory` и `InventorySetup` — savegame-relevant;
- `RenderEquipment` и `VisualEquipment` — client-side представление.

Это подтверждает распределённый pipeline игрока, а не возможность собрать игрока добавлением нескольких компонентов. В runtime-исследовании EMF batch игровых персонажей определён сочетанием `PlayerInput`, `ServerConsumedPlayerInput`, `InventorySetup`, `CharacterSetup` и `SlotSelection`: [`re_inventory_api.md`](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/re_inventory_api.md#L201-L208). Эти компоненты используются в `PlayerCompanionGate` только как проверка уже подключённого игрока.

`ClientPlayerInputData` содержит movement stick, camera input, item, equipment и другие action structures. Статус их прямой записи как поддерживаемого API управления отдельным клиентом — `UNKNOWN`. Это внутренний layout компонента, а не контракт безопасной инъекции. Атаки, использование предметов и экипировка зависят от client/server pipeline и authority; подтверждённого высокоуровневого EMF API для них нет.

Серверный `emf.teleport` умеет перемещать actors и characters, но teleport не заменяет `moveTo` или длительное следование. Его успех не будет считаться доказательством управления локомоцией.

## Сохранения персонажей

Закреплённое исследование EMF подтверждает два storage backend и до 16 character slots: [`re_saves.md`](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/re_saves.md#L1-L23). LOCAL и Steam slot 0 — разные файлы.

Read-only наблюдение 2026-10-30:

- LOCAL: `%USERPROFILE%\Saved Games\keen games\Enshrouded\default\character0.ksd`, `world0.ksd` и ротация `backup`;
- Steam remote: обнаружены `character0.ksd`–`character2.ksd`, `world0.ksd`–`world3.ksd`, `global.ksd` и отдельные index-файлы;
- Steam ID в документацию не записан, содержимое файлов не читалось и не публиковалось.

Во время игры персонаж клиента существует на сервере; сервер передаёт клиенту character save; клиент коммитит свой `character<slot>.ksd`; хост сохраняет world, но каждый клиент сохраняет своего персонажа. Источник: [`re_saves.md`, replication/commit](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/re_saves.md#L130-L147) и официальный Dedicated Server FAQ.

Menu record достоверно содержит имя, уровень, experience и время сохранения, а упакованная часть — ECS-данные персонажа. Точные поля внешности, инвентаря, экипировки, навыков и quest state в бинарном character save полностью не картированы. Наличие данных в save не даёт безопасного API импортировать их в entity. Прямое редактирование бинарников исключено.

## Инвентарь и экипировка

| Возможность | A | B | C |
|---|---|---|---|
| Настоящий character inventory | задуман, но player не создаётся | отдельная имитация, `UNKNOWN` | `CONFIRMED` штатной игрой |
| Уникальные PIDE, durability, perks | player отсутствует | нужна собственная полная реализация | `CONFIRMED` штатной игрой |
| Экипировка и внешний вид от gear | player отсутствует | может быть только визуальной копией | `CONFIRMED` штатной игрой |
| Сохранение между сессиями | нет безопасного lifecycle | внешнее custom state | character save клиента |
| Серверные put/take/move | API подтверждён для entity с InventorySetup | после доказательства тела | возможно при authority/permissions; не тестировалось |

EMF подтвердил транзакции inventory, сохранение PIDE и level/rarity, но это не подтверждает `useItem` или `equip` без client action pipeline. Для уникального предмета проверка результата должна сопоставлять item id, slot id и PIDE/состояние экземпляра, а не только количество.

## Сравнение вариантов

| Критерий | A: player без клиента | B: управляемая копия | C: второй клиент |
|---|---|---|---|
| Итоговый статус | `UNSUPPORTED` | `UNKNOWN` | `LIKELY`, control `UNKNOWN` |
| Настоящая человеческая внешность | потенциально | потенциально/визуально | да |
| Настоящий player entity | API нет | нет | да |
| Настоящий inventory/gear/skills | недоступны | нет, пока не реализованы отдельно | да |
| Движение и бой | API отсутствует | отдельные NPC-контроллеры | штатные механики, AI input не подтверждён |
| Прогресс между сессиями | не подтверждён | custom persistence | штатный character save |
| Независимость от второго клиента | да | да | нет |
| Network/account authority | отсутствует | NPC authority | штатное подключение отдельного аккаунта |
| Риски сохранений | высокие при подделке | средние при custom state | обычное сохранение отдельного test character |
| Производительность | лучшая теоретически | лучше C | второй процесс/ПК, стоимость выше |
| Поддерживаемость после update | крайне хрупкая | зависит от NPC API | network join устойчивее, adapter версионный |

### Вариант A

Это наиболее желательный UX: один процесс и настоящий второй персонаж. Он **не реализуем подтверждёнными механизмами**. EMF `spawn` не принимает character slot/save/account, не создаёт peer и не регистрирует player slot. `FakePlayerSpawner` в типах содержит лишь template GUID; его название не является доказательством сетевого игрока. Синтез player entity из компонентов обходит внутренний lifecycle и создаёт риск для основного персонажа.

### Вариант B

Можно проектировать отдельное humanoid/NPC-тело и копировать вид, но безопасный clone appearance/equipment API не подтверждён. Даже успешный визуальный клон останется NPC или репликой без штатных player inventory, skills и character save. Наработки этапа 6 сохраняются как резервный путь.

### Вариант C

Штатный второй клиент создаёт настоящего игрока и даёт нужную семантику. Для одновременной работы нужны отдельный Steam account и доступная отдельная копия/лицензия; один аккаунт использовать нельзя. Запуск двух клиентов на одном ПК не подтверждён Enshrouded и не тестировался. Для первого опыта безопаснее отдельный ПК, чтобы не смешивать процессы, ввод, GPU-контекст и каталоги клиента.

EMF может работать на стороне сервера/хоста и видеть второго player. EMF во втором клиенте может получить его `local_player()` и client world, но на клиенте чужого мира нет server world. Существующий Python Bridge ещё не доказан как канал управления client input. Поэтому C пока означает архитектуру наблюдения и identity binding, а не готового AI Companion.

## Целевой интерфейс команд

| Метод | Статус | Возможный механизм | Подтверждение результата |
|---|---|---|---|
| `observe()` | `CONFIRMED` частично | host EMF: roster, account, entity, position, компоненты | session/account/slot/entity стабильны |
| `moveTo(position)` | `UNKNOWN` | input второго клиента или новый supported API | движение к цели без teleport |
| `follow(player)` | `UNKNOWN` | цикл observe + moveTo | длительная дистанция на ручном маршруте |
| `stay()` | `UNKNOWN` | нейтральный input | позиция стабильна заданный интервал |
| `lookAt(target)` | `UNKNOWN` | camera/aim input | ориентация направлена на цель |
| `attack(target)` | `UNKNOWN` | action input | hit/target/attacker подтверждены |
| `defend(player)` | `UNKNOWN` | Brain над observe/move/attack | отдельный сценарий с угрозой |
| `interact(target)` | `UNKNOWN` | interaction input | конкретное state/event |
| `useItem(item)` | `UNKNOWN` | item action | точный stack/PIDE изменён ожидаемо |
| `equip(item)` | `UNKNOWN` | equipment action | slot и replicated equipment совпали |
| `transferItem(item,destination)` | `LIKELY` | inventory transaction с permissions | source/destination/PIDE согласованы |

Ни одна mutating-команда не включена в коде этапа 7. [`companion/player_character.py`](../companion/player_character.py) хранит evidence-каталог и закрывает runtime даже после успешной проверки identity.

## Рекомендация

**Рекомендуемый путь — C, второй штатный клиент, только если пользователь принимает стоимость второго аккаунта/копии и второго игрового процесса.** Это наиболее технически подтверждённый способ получить настоящее тело игрока, инвентарь, экипировку, навыки и сохранение. Наиболее желательный по UX вариант A остаётся заблокирован отсутствием player/session API. B остаётся резервом, если второй клиент окажется неприемлемым.

Следующий этап должен сначала доказать только подключение и наблюдение второго тестового игрока. До этого нельзя реализовывать input injection, AI Brain или предметные операции.

## Непроверенные риски

- Стабильность двух клиентов на одном ПК.
- EMF/Python Bridge в нужном режиме внутри второго remote client.
- Безопасная адресация input только второму клиенту.
- Достоверное подтверждение attack/interact/use/equip.
- Нагрузка двух клиентов на CPU, GPU, RAM и сеть.
- Сохранение при аварийном завершении второго клиента.
- Изменения ECS layout и network pipeline после обновления игры.
