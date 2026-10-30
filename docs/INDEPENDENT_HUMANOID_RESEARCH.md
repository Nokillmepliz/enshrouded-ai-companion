# Независимое человекоподобное тело: исследование этапа 8

Дата: 30.10.2026. Исследованы закреплённые исходники EMF `08d600155fcadc8e45cc9c6f3932a67c717345be` и Enshwick `135561192969af9ec9ffd0957b97ca6a7aa31820`, целевая сборка Enshrouded 1273043. Игра не запускалась, файлы игры и сохранения не изменялись.

## Вердикт

Безопасный первый `spawn` независимого человека **BLOCKED**. В доступных данных не найден неуникальный обычный человеческий template с доказанными исходной дружественной faction, идентичностью экземпляра, ownership и безопасным удалением. Публичный Lua API EMF создаёт сущность только по существующему template GUID и не регистрирует новый entity template. Подмена `ModelResource` или animation graph отдельной сущности также не подтверждена.

Рабочее направление остаётся `Human NPC Body Adapter`, но runtime выключен. Следующий допустимый игровой шаг — отдельный read-only survey уже существующих NPC в тестовом LOCAL-мире. Он не создаёт и не изменяет сущности.

Статусы в таблицах: **CONFIRMED** — прямо подтверждено исходником или зафиксированным runtime-исследованием upstream; **LIKELY** — обосновано, но не проверено для выбранного тела; **UNKNOWN** — данных недостаточно; **UNSUPPORTED** — публичного подтверждённого механизма нет.

## Направление A: существующий неуникальный гуманоид

Закреплённый Enshwick содержит 18 реальных workshop survivor templates. Их GUID и `npcId` перечислены в [`WORKSHOP_SURVIVORS`](https://github.com/enshwick/enshwick/blob/135561192969af9ec9ffd0957b97ca6a7aa31820/crates/enshwick/src/survivors/workshop.rs#L150-L190). Локальный каталог побайтно проверялся на этапе 6.

| Кандидаты | Количество | Template GUID / npcId | Uniqueness | Решение |
|---|---:|---|---|---|
| workshop survivors и assistants | 18 | подтверждены таблицей Enshwick | один entity на template GUID | только read-only survey |
| `test_Townsfolk_*` | 6 по экспорту EMF | имена подтверждены, GUID в закреплённых публичных файлах отсутствуют | тот же unique villager lifecycle | не добавлять в каталог без GUID |
| `Base_NPC*`, `*_8k_Version2..5` | входят в 58 templates с `ActiveNpcState` | конкретные GUID/ресурсы здесь не опубликованы | villager uniqueness | не кандидаты без полного descriptor |
| trader/event townsfolk | реальные NPC workshops | конкретная торговая роль подтверждена | сюжетный/event NPC | не использовать как тело |

Все 18 полных descriptor находятся в `companion.independent_humanoid.DESCRIPTORS`; каждый помечен `UNIQUE_STORY_NPC`, `runtime_enabled=False`, с неизвестными model/animation/faction. Полная таблица GUID сохранена в [HUMAN_COMPANION_RESEARCH.md](HUMAN_COMPANION_RESEARCH.md), чтобы не дублировать 18 строк.

EMF установил механизм ограничения точно: `unique_npc_init` хеширует 16-байтовый template GUID FNV-1a, а `unique_npc_spawns` удаляет новичка, если этот GUID уже зарегистрирован. `ActiveNpcState.npcId` workshop survivor также равен FNV-1a его template GUID. Это ограничение относится к villager templates с `ActiveNpcState`, а не ко всем существам с человеческим скелетом. Доказательств существования подходящего человеческого template без этого lifecycle нет. Источники: [анализ uniqueness](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/ai.md#L355-L361), [Enshwick survivors](https://github.com/enshwick/enshwick/blob/135561192969af9ec9ffd0957b97ca6a7aa31820/book/src/survivors.md#L1-L28), [сводка villager templates](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/re_villages.md#L125-L138).

Enshwick может перехватывать ответы survivor lookup и выбирать, какой дубликат оставить. Это механизм изменения vanilla uniqueness, а не доказательство независимого безопасного NPC. Он оставляет связанные записи игры на vanilla entity и затрагивает сон, кровать, roaming и summoning. Использовать его для обхода ограничения сюжетного NPC запрещено и не предлагается.

## Направление B: собственный template

Публичный EMF API подтверждает `spawn(templateGuid, position)`, чтение dynamic/template компонентов и регистрацию ECS programs. Он не предоставляет операции «создать template», «клонировать archetype» или «назначить новый template GUID». `world:template` читает общие template-данные существующей сущности и возвращает read-only объект; это не конструктор template. Источники: [Lua API](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/lua.md#L160-L183), [устройство template storage](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/re_templates.md#L1-L39).

Документация EMF указывает, что новые villager GUID требуют **EML data patch**. В исследованном репозитории нет готового, подтверждённого для нашего мода API/формата такого patch, который создаёт независимый человекоподобный template с корректными archetype, ресурсами, faction и save semantics. Поэтому направление B — перспективное внешнее исследование, но не готовый прототип. [Источник требования нового GUID](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/re_villages.md#L135-L144).

Наличие `ActiveNpcState`, `Equipment` или других C++ структур не означает, что мод может собрать жизнеспособный archetype из компонентов. Изначально безопасная faction до появления тела также не задаётся отдельным аргументом `emf.spawn`.

## Направление C: безопасная сущность с человеческой моделью

`ModelResource.model` и `AnimationGraphResourceComponent2.animationGraph` доступны как template-half данные. Они общие для template; EMF предупреждает, что запись template data влияет на **все** сущности этого template и действует до перезапуска. Это не даёт безопасной подмены внешности одного экземпляра. [Описание shared template data](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/guide.md#L18-L26), [последствия записи](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/re_templates.md#L31-L39).

Даже совпадение model и animation graph не доказывает совместимость skeleton, collision, root motion, pathfinding, combat FSM, replication и сохранения. Подтверждённого механизма клонировать полный человеческий archetype или менять эти ресурсы атомарно до появления сущности нет. Направление C остаётся **UNSUPPORTED** текущим публичным API.

## Безопасность, identity и ownership

Для существующей сущности Lua может получить `EntityId`, session, `ModelResource.model`, `ActiveNpcState.npcId`, faction и наличие компонентов. Публичный Lua API не возвращает template GUID сущности и generation идентификатор `EntityId`. Enshwick внутри loader имеет build-specific `ecs.template_guid`, но эта внутренняя функция не является Lua API EMF и не используется нашим модом.

Будущий ownership требует одновременно:

- session и EntityId;
- ожидаемые template GUID, model GUID, animation graph и `npcId`;
- исходную безопасную faction;
- уникальный creation marker, принадлежащий нашему процессу создания;
- три последовательных полных наблюдения;
- неизменность fingerprint перед каждой мутацией и удалением.

Совпадение template/model/NPC описывает тип сущности и не доказывает, что конкретный экземпляр создал наш мод. При неизвестном исходе spawn, reflection error, смене session/identity или переиспользовании EntityId состояние переходит в `RECOVERY_REQUIRED`; повторный spawn и destroy неподтверждённой сущности запрещены.

Сейчас ни один descriptor не имеет creation marker или ownership proof. Поэтому faction write, activation и dismiss заблокированы. Результат этапа 5 с враждебным Vukah подтверждает, что faction нельзя исправлять после непроверенного spawn.

## Движение

| Команда | Подтверждение | Ограничение |
|---|---|---|
| `moveTo(position)` | `NpcCommandEvent.GoToPosition` **CONFIRMED** | только уже существующий active survivor; матч по `npcId` |
| `follow(player)` | **UNKNOWN** | постоянного follow event нет; повторный `GoToPosition` ещё не доказан как безопасное поведение |
| `stay()` | **UNKNOWN** | краткая близость не доказывает длительный stay |
| `lookAt(target)` | **UNKNOWN** | публичная подтверждённая команда не найдена |
| `stop()` | **UNKNOWN** | `Reset` меняет home и телепортирует, поэтому не считается stop |

`GoToPosition` переводит active NPC в Roam, задаёт `currentTargetPosition`, а через несколько секунд NPC может снова перейти к обычному roaming. Это не follow. Источники: [обработчик команды](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/ai.md#L240-L248), [runtime-наблюдение](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/re_villager_jobs.md#L13-L18).

## Бой

Enemy FSM умеет выбирать цель и сражаться, а villager FSM отвечает за idle/roam/sleep/socializing. Подтверждения, что workshop survivor имеет совместимый боевой AI, атаки и человеческие боевые анимации, нет. `AddThreatTargetEvent` доказан для enemy/companion механизмов, но не переносится на survivor автоматически. Не подтверждены weapon use, defend player, friendly-fire policy, смерть и безопасное восстановление независимого humanoid. Полноценный combat на этапе 8 не реализован. [AI systems](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/ai.md#L310-L349).

## Инвентарь и экипировка

Сгенерированные компоненты `Inventory`, `InventorySetup`, `Equipment`, `RenderEquipment` и `VisualEquipment` существуют. EMF подтвердил initialized `InventorySetup` у villager и предоставляет атомарную операцию `take` для одного владельца и `put`; gear имеет отдельную PIDE entity, а перенос через `take -> put` может пересоздать свойства. Источник: [EMF inventory model](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/guide.md#L72-L84).

Не подтверждены для выбранного тела:

- полный набор компонентов equipment/render на server/client;
- использование NPC inventory как постоянного личного backpack;
- equip/unequip через штатную транзакцию;
- визуальное отображение брони и оружия;
- атомарный перенос между двумя владельцами при crash/reload;
- сохранение уникальных свойств PIDE;
- связь экипировки с attack и animation sets.

До доказательства этих пунктов inventory/equipment commands отключены. Sidecar-хранилище может хранить личность и абстрактное состояние, но не считается игровым инвентарём и не должно создавать предметы.

## Capability matrix

| Возможность | Evidence | Runtime |
|---|---|---|
| безопасный spawn человека | UNKNOWN | disabled |
| non-unique human template | UNKNOWN | disabled |
| custom template через public EMF Lua | UNSUPPORTED | disabled |
| instance-local model/animation replacement | UNSUPPORTED | disabled |
| identity/ownership конкретного экземпляра | UNKNOWN | disabled |
| `moveTo` существующего active survivor | CONFIRMED | diagnostic only |
| follow/stay/lookAt/stop | UNKNOWN | disabled |
| combat | UNKNOWN | disabled |
| inventory structures/transactions | CONFIRMED | body integration disabled |
| equipment/visual equipment | UNKNOWN | disabled |
| safe dismiss | UNKNOWN | disabled |
| safe independent persistence | UNKNOWN | disabled |

## Read-only survey

Подготовлен выключенный мод `mods/aic_humanoid_survey`. Он имеет только команды:

```text
aic_humanoid_survey.scan 40
aic_humanoid_survey.inspect <entityId>
```

Мод перечисляет уже существующих nearby entities с `ActiveNpcState` и читает model, animation graph, faction, NPC identity, navigation, inventory/equipment, save/network markers. Он не вызывает tick callback, spawn, destroy, event emission, inventory operations или сохранение данных. Публичный Lua API не отдаёт template GUID, поэтому результат честно содержит `template_guid_available=false`; GUID сопоставляется только с заранее известным NPC descriptor и внешними доказательствами.

Точный сценарий будущего испытания:

1. Сделать и проверить отдельную резервную копию LOCAL-сохранений.
2. Включить только `aic_humanoid_survey`; `aic_body` оставить выключенным.
3. Запустить LOCAL-мир вручную и разместить штатного `hunter_assistant` обычным игровым способом, только если он уже доступен персонажу.
4. Выполнить `scan 40`, затем `inspect <entityId>`.
5. Сохранить только строки `AIC_HUMANOID_SURVEY`, закрыть игру и сравнить компоненты server/client и логи reflection.
6. Ничего не spawn, не менять faction, не удалять NPC, не переносить предметы.

Этот сценарий требует отдельного разрешения пользователя и пока не выполнялся.

## Оставшиеся блокеры

1. Нет подтверждённого non-unique human template GUID.
2. Нет публичного API регистрации собственного template.
3. Нет безопасного inactive/friendly-before-appearance spawn.
4. Нет instance generation и creation marker в доступном API.
5. Template GUID не читается через Lua survey.
6. Safe dismiss и persistence отдельного экземпляра не доказаны.
7. Движение доказано только для vanilla active survivor; follow и stop отсутствуют.
8. Combat/inventory/equipment для независимого humanoid не доказаны.
9. Данные model/animation/faction конкретных candidates ещё не собраны на build 1273043.

Рекомендация: выполнить read-only survey, затем отдельно исследовать поддерживаемый EML data patch для нового GUID. До появления полного descriptor и creation/ownership механизма визуальный прототип в игре не создавать.
