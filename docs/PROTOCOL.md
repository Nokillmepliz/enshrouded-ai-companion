# Body Adapter 0.1: контракт и реализация

Это прототип, проверенный без игры. Базовое исследование — [RESEARCH.md](RESEARCH.md). Здесь зафиксированы дополнительные детали реализации этапа 2.

## Почему Lua

EMF уже предоставляет Lua-обёртки подтверждённых spawn/destroy, компонентов и событий. Пример upstream [pet_follow/main.lua](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/examples/lua/pet_follow/main.lua) делает спавн, назначает фракцию и отправляет `StartGuardingEvent`.

`emf.emit` **не возвращает bool успеха**: Lua-host складывает событие в очередь и позднее отправляет его из собственного ECS program. Поэтому адаптер использует `pcall` только для обнаружения ошибки постановки в очередь, а результат проверяет чтением мира. Источник: [bindings.cpp, l_emit / program_cb_body](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/lua_host/bindings.cpp#L1368-L1459).

Все вызовы мира происходят внутри server callback. Объекты мира и компоненты не сохраняются между callbacks. `side: server` в manifest — описание назначения, а не enforcement; код дополнительно проверяет `world:is_server()`. Команды из чата отклоняются. Dedicated server и подключение к чужому хосту не входят в этот прототип.

## Подтверждённые вызовы и поля

| Код адаптера | Реальный интерфейс EMF | Источник |
|---|---|---|
| Спавн/удаление | `emf.spawn(world, guid, x, y, z)`, `emf.destroy(world, id)` | [bindings.cpp L816–832](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/lua_host/bindings.cpp#L816-L832) |
| Следование/остановка охраны | `emf.emits`, `emf.emit('server', name, fields)`; `guardingEntityId`, `guardedEntityId` | [Companion guard_program](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/mods/companion/companion.cpp#L147-L165), [Lua events](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/lua.md#L199-L225) |
| Положение/статус | `world:position`, `world:get`, `emf.health`, `Faction.faction`, `DynamicEnemy01BehaviorState.guardEntityId`, `Actor.currentState` | [Lua API](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/lua.md#L88-L198), [проверка Actor flag 50](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/mods/companion/companion.cpp#L229-L261) |
| Сессия | `emf.session_token()` — идентификатор процесса и hosted session | [host.cpp L486–504](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/lua_host/host.cpp#L486-L504) |
| Проверка модели | `world:template('ModelResource', entity).model`, read-only; Lua >=1.8 | [world:template](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/lua.md#L166-L198) |
| Дополнительная проверка идентичности | `SpawnTime.spawnTime`, **только если компонент присутствует** | [структура SpawnTime](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/sdk/include/emf/generated/components.hpp#L19744-L19755), [обычный spawn добавляет только transform](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/core/spawn.cpp#L52-L66) |
| Консольный транспорт | `emf.command`, `emf.reply`; аргументы не включают имя команды | [host.cpp L293–322](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/lua_host/host.cpp#L293-L322) |

Новых движковых API, патчей шаблонов, управления анимациями и записи по адресам в коде проекта нет. Чтение ModelResource на выбранном теле/маркере требует проверки в игре. Если оно недоступно, адаптер запрашивает удаление только что созданного объекта и переходит в `recovery_required`, не выдавая успех.

## Канал команд

Внешний транспорт — существующий EMF Windows named pipe с JSON Lines, реализованный [vendor/emf_bridge.py](../vendor/emf_bridge.py). Внутри `Bridge.console()` передаётся строго ограниченная текстовая команда. Это наш контракт поверх настоящей консоли, а не выдуманный endpoint EMF:

```text
aic_body.status
aic_body.status <request-id>
aic_body.request <request-id> <epoch> <companion-id> <spawn|follow|stay|dismiss>
```

Каждый аргумент-ID — 1–96 ASCII букв, цифр, `_` или `-`; координаты, Lua-код и entity ID от клиента не принимаются. В профильном CLI `companion-id` — UUID из файла личности. `epoch` берётся из status: включает процесс/сессию EMF и экземпляр Lua-контроллера, поэтому меняется также после hot reload.

Ответ консоли — одна строка с префиксом `AIC_BODY ` и JSON. Пример структуры, с условными значениями:

```json
{
  "protocol": 1,
  "state": {
    "protocol": 1,
    "adapter": "0.1.0",
    "epoch": "run-1-table0x123",
    "session": "run-1",
    "companion_id": "550e8400-e29b-41d4-a716-446655440000",
    "entity_id": 100,
    "mode": "follow",
    "faction": 11,
    "guard_target": 1,
    "ready": true,
    "health": 119,
    "distance_to_target": 2,
    "recovery_required": false
  },
  "request": {
    "id": "spawn-001",
    "action": "spawn",
    "companion_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "succeeded",
    "code": "guard_and_proximity_observed"
  }
}
```

Неизвестные Lua `nil` поля опускаются. `error` означает отказ запроса; иначе смотреть `request.status`: `accepted`, `succeeded`, `failed`, `cancelled`. `state.mode` — отдельное состояние тела: `absent`, `follow`, `stay`, `dismissing`, `lost`, `recovery_required`. Не путать состояние приказа со статусом физического тела.

Клиент проверяет версию, формат, единственность JSON-ответа, request ID, действие, companion ID и epoch. Один запрос на изменение отправляется один раз; далее идут status-запросы. При потере ответа outcome неизвестен: нельзя автоматически создавать новое тело новым request ID. Узнать результат можно через status старого request ID.

## Семантика действий

| Действие | Что изменяет | Критерий успеха |
|---|---|---|
| `spawn` | Создаёт `Enemy_Vukah_Melee` в +2 м по X от хоста, ставит `Faction=11`, отправляет guard на владельца | Живое тело, ready-флаг, faction 11, правильный guard и расстояние <=8 м наблюдаются три последовательных server callback |
| `follow` | Отправляет guard на владельца; после подтверждения возвращения удаляет старый stay-маркер | Те же проверки; старый маркер отсутствует |
| `stay` | Создаёт одну бочку `0ce28db1-522f-4455-b358-3888fb5e089b` в текущем месте тела, назначает её guard target | Живое готовое тело охраняет маркер и находится не дальше 8 м три callback |
| `dismiss` | Отменяет ожидающий приказ, ставит StopGuarding, через два server callback запрашивает удаление тела и маркера | Отсутствие обоих объектов наблюдено после запроса; runtime lock удалён |

`stay` означает охрану области, а не полную неподвижность. Бочка — реальный дополнительный объект. Дистанция 8 м — наш критерий проверки, **не изменение** `Enemy01BehaviorState.guardSetup`. Шаблонные дистанции не перезаписываются.

Три наблюдения подтверждают текущее состояние; они не доказывают длительное следование, обход препятствий или отсутствие боевого поведения. Это проверяется вручную по [TEST_PLAN.md](TEST_PLAN.md). Боевой AI тела остаётся штатным и может сражаться сам, хотя команды attack в прототипе нет.

Таймаут контроллера — 1800 server callbacks (примерно 30 с при 60 Гц; реальный FPS симуляции может отличаться). Таймаут Python по умолчанию 40 секунд, плюс время завершения уже начатого ограниченного ожидания bridge. Таймаут **не отменяет уже полученный движком guard**. При необходимости пользователь отдельно вызывает dismiss.

## Жизненный цикл и ограничения идентичности

- Профиль `runtime/personality.json`: schema, постоянный UUID, имя и personality. Никаких entity ID или автоспавна после загрузки. После перезапуска клиент читает тот же UUID.
- Runtime контроллера: ID тела/маркера, владелец, session, model GUID, тип AI и необязательный SpawnTime. Любое наблюдаемое расхождение запрещает дальнейшее изменение чужого объекта. После смерти тело не возрождается; corpse можно удалить dismiss, если его идентичность ещё совпадает.
- Это **не гарантия native generation ID**: Lua API такого идентификатора здесь не предоставляет. Мгновенную замену сущности на полностью идентичный экземпляр между callbacks при отсутствии SpawnTime нельзя надёжно различить. Поэтому первая проверка — один компаньон, без других companion-модов, в отдельном мире; массовое управление сущностями этим прототипом не поддерживается.
- Перед spawn пишется `runtime.lock` рядом с Lua-модом. В нём только session token. Hot reload при живом теле или маркере блокирует изменения (`recovery_required`), не пытаясь восстановить неизвестные ID. Не удалять lock вручную в живой сессии. После смены сессии старый lock не означает владения старой сущностью.
- Успешный dismiss снимает lock. При ошибке очистки ID и lock остаются для диагностики. На смерть/исчезновение нет автоматического повторного spawn.
- Lua-hot-reload/закрытие игры не являются автоматической очисткой. Маркер может попасть в сохранение; сценарий испытаний требует dismiss перед выходом. После аварии или потери handle использовать резервную копию тестового мира, а не удалять неизвестные объекты по старым ID.
- Кэш хранит 128 обычных запросов на сессию и один резервный ответ dismiss для очистки. При переполнении новые обычные запросы запрещены до смены мира. Повтор ID возвращает исходный результат, смена параметров того же ID отклоняется. Резервный dismiss-ответ заменяется следующим dismiss; сами удаления идемпотентны по эффекту.

## Границы защиты

CLI требует `--allow-game-mutations`, явный game folder/PID, конкретный локальный world slot и имя/slot локального персонажа. Перед изменением проверяет EMF 0.3.2, API 20, protocol 1, build 1273043 и хостовый мир. Epoch берётся **до** world check: смена мира во время preflight не даёт выбрать новую сессию автоматически.

Это защита от ошибочного запуска, а не система безопасности вместо EMF. Человек с доступом к консоли может вручную вызвать команды адаптера; raw console не выполняет клиентскую проверку имени мира/персонажа. Использовать его только в согласованной тестовой среде. Адаптер не запускает игру, не включает bridge и не делает backup/restore самостоятельно.
