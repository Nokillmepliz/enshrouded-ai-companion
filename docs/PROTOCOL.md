# Body Adapter 0.1: контракт и реализация

Текущий wire protocol=1 / **safety_revision=2** относится к историческому runtime-профилю `legacy_vukah`. После первого игрового `FAIL` он не является целевым human body и не должен повторно испытываться. Human Body на этапе 6 существует только как офлайн-каталог/capability/identity policy; его spawn заблокирован до отдельной protocol revision 3. Исследование и границы — [HUMAN_COMPANION_RESEARCH.md](HUMAN_COMPANION_RESEARCH.md), архитектура — [HUMAN_COMPANION_ARCHITECTURE.md](HUMAN_COMPANION_ARCHITECTURE.md).

Базовое исследование старого прототипа — [RESEARCH.md](RESEARCH.md). Python отказывает в изменениях через адаптер без safety revision 2. Исторические инструкции этапов 2–3 о rollback без fingerprint и снятии блокировки при смене сессии заменены правилами ниже.

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
| Проверка отсутствия | `world:entities()` — копия списка ID; отсутствие позиции само по себе ничего не доказывает | [bindings.cpp L248–259](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/lua_host/bindings.cpp#L248-L259), [WorldView::entity_ids](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/common/world_view.cpp#L139-L152) |
| Дополнительная проверка идентичности | `SpawnTime.spawnTime`, **только если компонент присутствует** | [структура SpawnTime](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/sdk/include/emf/generated/components.hpp#L19744-L19755), [обычный spawn добавляет только transform](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/core/spawn.cpp#L52-L66) |
| Консольный транспорт | `emf.command`, `emf.reply`; аргументы не включают имя команды | [host.cpp L293–322](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/lua_host/host.cpp#L293-L322) |

Новых движковых API, патчей шаблонов, управления анимациями и записи по адресам в коде проекта нет. Чтение ModelResource на выбранном теле/маркере требует проверки в игре. Если fingerprint недоступен, адаптер сохраняет неподтверждённый handle и переходит в `recovery_required`. **Удаление такого объекта по одному ID запрещено**, даже сразу после spawn. Позднее появление ModelResource не повышает этот handle до доверенного.

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
    "safety_revision": 2,
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
    "recovery_required": false,
    "behavior_verified": false
  },
  "request": {
    "id": "spawn-001",
    "action": "spawn",
    "companion_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "succeeded",
    "code": "guard_and_proximity_observed",
    "phase": "state_confirmed",
    "event_submission": "queued",
    "state_confirmed": true,
    "behavior_verified": false
  }
}
```

Неизвестные Lua `nil` поля опускаются. `error` означает отказ запроса; иначе смотреть `request.status`: `accepted`, `succeeded`, `failed`, `cancelled`. `state.mode` — отдельное состояние тела: `absent`, `follow`, `stay`, `dismissing`, `lost`, `recovery_required`. Не путать состояние приказа со статусом физического тела.

Клиент проверяет версию, формат, единственность JSON-ответа, request ID, действие, companion ID и epoch. Один запрос на изменение отправляется один раз; далее идут status-запросы. При потере ответа outcome неизвестен: нельзя автоматически создавать новое тело новым request ID. Узнать результат можно через status старого request ID.

Дополнительные поля состояния: `body_profile` (`legacy_vukah` для protocol 1), `body_trusted` / `marker_trusted`, `body_identity_invalidated` / `marker_identity_invalidated`, `body_destroy_requested` / `marker_destroy_requested`, `body_destroy_result` / `marker_destroy_result`, `uncertain_spawn`, `orphaned`, `observation_error`, `recovery_action`. `destroy_requested=true` означает, что вызов уже был предпринят и повторять его нельзя; результат отдельно обозначается `accepted`, `refused_or_unknown` или `outcome_unknown`. Ошибка отражения в status сохраняет диагностический ответ с `observation_error=inspect_failed`.

## Уровни подтверждения

| Уровень | Представление | Что действительно известно |
|---|---|---|
| Запрос принят контроллером | `status=accepted`, начальная `phase=accepted` | Запрос зарегистрирован; изменения могут быть ещё не сделаны |
| Событие передано в очередь Lua-host | `event_submission=queued`, для StartGuarding также `phase=event_queued` | `pcall(emf.emit, ...)` вернулся без ошибки; нет квитанции о доставке движку |
| Очередь отказала | `event_submission=enqueue_failed` | Guard не подтверждён; при dismiss это не запрещает безопасную очистку подтверждённых объектов |
| Состояние проверено | `status=succeeded`, `phase=state_confirmed`, `state_confirmed=true` | Наблюдались критерии конкретной команды; Python требует эти поля для признания успеха |
| Длительное поведение NPC | `behavior_verified=false` во всех автоматических ответах | Проверяется только человеком в игре и фиксируется отдельно в протоколе испытания |

`event_submission=not_requested` означает, что события не требовалось либо до его постановки код не дошёл. При завершении запроса phase становится `failed`/`cancelled`/`state_confirmed`, но поле event_submission сохраняет результат попытки очереди. `succeeded` старого request ID — исторический результат команды, не гарантия текущего состояния тела; для него смотреть свежий state.

## Семантика действий

| Действие | Что изменяет | Критерий успеха |
|---|---|---|
| `spawn` | Создаёт `Enemy_Vukah_Melee` в +2 м по X от хоста, ставит `Faction=11`, отправляет guard на владельца | Живое тело, ready-флаг, faction 11, правильный guard и расстояние <=8 м наблюдаются три последовательных server callback |
| `follow` | Отправляет guard на владельца; после подтверждения возвращения удаляет старый stay-маркер | Те же проверки; старый маркер отсутствует |
| `stay` | Создаёт одну бочку `0ce28db1-522f-4455-b358-3888fb5e089b` в текущем месте тела, назначает её guard target | Живое готовое тело охраняет маркер и находится не дальше 8 м три callback |
| `dismiss` | Отменяет ожидающий приказ; для подтверждённого ещё не удаляемого тела пробует StopGuarding; через два callback удаляет только подтверждённые объекты, ещё не получавшие destroy | Каждый ID отсутствует в трёх последовательных callback; lock текущего контроллера проверен, удалён и повторно проверен |

`stay` означает охрану области, а не полную неподвижность. Бочка — реальный дополнительный объект. Дистанция 8 м — наш критерий проверки, **не изменение** `Enemy01BehaviorState.guardSetup`. Шаблонные дистанции не перезаписываются.

Три наблюдения подтверждают текущее состояние; они не доказывают длительное следование, обход препятствий или отсутствие боевого поведения. Это проверяется вручную по [TEST_PLAN.md](TEST_PLAN.md). Боевой AI тела остаётся штатным и может сражаться сам, хотя команды attack в прототипе нет.

Таймаут контроллера — 1800 server callbacks (примерно 30 с при 60 Гц; реальный FPS симуляции может отличаться). Для dismiss результат таймаута — `failed/cleanup_timeout` и recovery_required с сохранёнными handle/lock. Для остальных команд — `failed/verification_timeout`. Таймаут Python по умолчанию 40 секунд, плюс время завершения уже начатого ограниченного ожидания bridge. Таймаут **не отменяет guard или уже отправленное удаление**.

Повтор прежнего request ID возвращает прежний результат и не запускает попытку заново. Для явного продолжения очистки используют **новый dismiss ID**: контроллер наблюдает уже предпринятые удаления, обрабатывает ещё не затронутые подтверждённые handle и может повторить удаление своего lock после ошибки файла. Принятый/неопределённый destroy никогда не отправляется повторно, даже с новым request ID. После `destroy=false` также нет повторного destroy: [guarded_destroy](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/core/spawn.cpp#L16-L30) возвращает false после SEH-исключения, которое могло произойти уже после изменения игры. Если объект не исчезает, дальнейшее ожидание не гарантирует успеха: требуется ручной разбор/восстановление тестового мира.

`world:position(id)==nil` не считается исчезновением. Нужны три наблюдения отсутствия ID в `world:entities()` на последовательных callback; многократный status в одном тике счётчик не увеличивает. Снимок без локального игрока отклоняется как недостоверный. Список кэшируется только внутри одного callback. При сбое reflection/перечисления подтверждение не выдаётся.

## Жизненный цикл и ограничения идентичности

- Профиль `runtime/personality.json`: schema, постоянный UUID, имя и personality. Никаких entity ID или автоспавна после загрузки. После перезапуска клиент читает тот же UUID.
- Runtime контроллера: ID тела/маркера, владелец, session, model GUID, тип AI и необязательный SpawnTime. Любое наблюдаемое расхождение **запоминается**: возвращение прежней модели/SpawnTime не восстанавливает доверие. Возвращение ID после хотя бы одного наблюдения отсутствия также не восстанавливает доверие. После смерти тело не возрождается; corpse можно удалить dismiss, если fingerprint совпадает и destroy ещё не предпринимался.
- Подтверждённого более надёжного идентификатора экземпляра для этих шаблонов не найдено. [EntityId](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/sdk/include/emf/generated/components.hpp#L168-L178) содержит только uint32. `generation` в [Lua bindings](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/lua_host/bindings.cpp#L20-L47) проверяет срок жизни callback/proxy, не игровой экземпляр. Поле [StoredSceneId.uniqueId](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/sdk/include/emf/generated/components.hpp#L20208-L20218) — HashKey32 сцены; наличие и уникальность для каждого spawned Vukah/маркера не подтверждены. Оно не используется как выдуманный UUID. Обзор API и reflection не доказывает невозможность будущего решения, но сейчас подтверждённого механизма нет.
- Это **не гарантия native generation ID**: мгновенную замену на полностью идентичный экземпляр между callbacks нельзя надёжно различить (необязательный SpawnTime не заявлен уникальным). Первая проверка — один компаньон, один процесс игры, без других companion-модов, в отдельном мире.
- При вызове spawn флаг неопределённого результата выставляется **до** игрового API. ID сохраняется как неподтверждённый **до** чтения компонентов. Исключение/0 без ID сохраняет `uncertain_spawn=true`: [guarded_spawn](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/core/spawn.cpp#L16-L22) возвращает 0 также при нативном исключении. Автоматический retry и снятие lock запрещены.
- При отказе Faction handle остаётся подтверждённым, если fingerprint удалось снять; recovery запрещает spawn/follow/stay, но разрешает явный dismiss с прежней личностью. Если fingerprint не снят, dismiss может лишь наблюдать исчезновение ID, без удаления или позднего «усыновления» сущности.
- Успешный dismiss снимает lock только после подтверждённой очистки. При ошибке очистки handle, признаки уже предпринятого destroy и lock остаются. В recovery тики только наблюдают позднее исчезновение; без нового dismiss не выполняют очистку или снятие lock. Завершённый failed-запрос сам не становится succeeded.
- Lua-hot-reload/закрытие игры не являются автоматической очисткой. Маркер может попасть в сохранение; сценарий испытаний требует dismiss перед выходом. После аварии или потери handle использовать резервную копию тестового мира, а не удалять неизвестные объекты по старым ID.
- Кэш хранит 128 обычных запросов на сессию и один резервный ответ dismiss для очистки. При переполнении новые обычные запросы запрещены до смены мира. Повтор ID возвращает исходный результат, смена параметров того же ID отклоняется. Резервный dismiss-ответ заменяется следующим dismiss. Повтор dismiss не повторяет destroy для уже затронутого handle; это гарантия контроллера, не свойство движкового API.

## Runtime lock и безопасное восстановление

Файл рядом с Lua-модом содержит `aic-body-lock-v2`, перевод строки, **epoch контроллера**, перевод строки. Он не содержит игровых ID и не позволяет восстановить владение после reload. Стандартные `io.open`, file read/write/flush/close и `os.remove` доступны: [host.cpp с luaL_openlibs и sandbox](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/lua_host/host.cpp#L103-L145), [Lua-документация о файловом вводе-выводе](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/lua.md#L274-L285). Они не объявляются запрещёнными.

- Только errno=2 при открытии означает отсутствие. Ошибки доступа/чтения/закрытия не считаются отсутствием. Пустой, повреждённый, legacy или чужой файл при загрузке блокирует изменения.
- Перед spawn проверяется отсутствие lock, затем успешные write/flush/close и точное обратное чтение. Ошибка любого шага запрещает spawn; частичный файл не стирается автоматически.
- Перед снятием lock требуется точное совпадение **всего содержимого** с epoch текущего владельца. Затем проверяются os.remove и фактическое отсутствие. Чужой, недоступный или неожиданно отсутствующий файл при живом владельце не считается успешно снятым.
- Смена мира/процесса и hot reload теряют handle и не снимают старый lock. Даже после смены session token spawn блокируется: маркер мог попасть в save. Старые ID не читаются и не используются для удаления в новой сессии.
- Нет автоматического «сброса recovery». `recovery_action=dismiss` предлагает попробовать безопасную очистку/наблюдение в текущей сессии; это не обещание удаления неподтверждённого объекта. `manual_world_restore` означает потерянные handle, неизвестный ID после spawn либо чужой/повреждённый lock.

Порядок восстановления:

1. Сохранить diagnose/status, логи, epoch/request ID; не делать новый spawn и не редактировать lock.
2. При сохранённых handle, прежней сессии и личности — новый явный dismiss с обычным preflight и `--allow-game-mutations`. Python разрешает его в recovery, но не обходит проверок Lua. Отслеживать именно новый request ID.
3. Если handle неподтверждён, fingerprint изменился или destroy уже предпринимался — никаких новых удалений по ID. Возможна только проверка отсутствия; если объект остаётся, остановить сценарий.
4. При невозможности очистки: после **отдельного согласования восстановления** закрыть игру/Steam, сохранить неудачное состояние, вернуть проверенный комплект LOCAL тестовых сохранений до спавна. Учесть все затронутые тестовые миры, если между ними переключались с неочищенным телом. Само закрытие игры не очищает save.
5. Только когда доказано восстановление исходного тестового состояния, при закрытой игре отдельно согласованно архивировать старый runtime.lock и запустить новую сессию. Не удалять lock для обхода проверки в существующем мире. Проект не предоставляет автоматическую команду unlock/reset/restore. Сейчас ни один из этих игровых шагов не выполнялся.

Ограничения файла: стандартный Lua flush не является fsync/транзакцией с сохранением игры. Проверка содержимого и os.remove не атомарны относительно другого процесса/ручного редактирования. Один процесс игры и отсутствие внешних изменений файла обязательны; защита от произвольного удаления lock во время reload или потери дисковых записей при аварии питания не обещается.

## Риски до реального игрового испытания

1. Доступность ModelResource/SpawnTime и фактический тип тела/бочки, корректность reflection и фракции на установленном build не проверены в игре. Отказ может оставить враждебного Vukah, которого нельзя безопасно удалить без fingerprint.
2. Доставка guard-событий, навигация, бой, длительное follow/stay и исчезновение тела/маркера из клиента и save не доказаны unit-тестами.
3. Нет подтверждённого generation ID: полностью совпадающую замену между наблюдениями нельзя исключить. Три проверки отсутствия и наличие игрока в снимке повышают достоверность, но зависят от правильности EMF и живого мира.
4. API spawn/destroy может завершиться нативным исключением после частичного эффекта. При неизвестном ID или зависшем удалении потребуется восстановление тестового save, а не retry вслепую.
5. Полное перечисление entities имеет стоимость и может упереться в лимит времени Lua-host в большом мире. Реальный лимит callback, частота симуляции и задержки удаления ещё не измерены. Таймаут/пауза Lua-host не является очисткой.
6. Файловый lock не атомарен между процессами и не гарантирует сохранность при сбое питания; конкурирующие процессы игры и ручное изменение lock не поддерживаются. Не проверены реальные ACL/антивирус/задержки диска в каталоге игры.
7. После аварии/reload безопасное автоматическое восстановление владения невозможно. Нужна проверенная резервная копия и отдельное разрешение на восстановление. Игровые проверки остаются **NOT RUN**.

## Границы защиты

CLI требует `--allow-game-mutations`, явный game folder/PID, конкретный локальный world slot и имя/slot локального персонажа. Перед изменением проверяет EMF 0.3.2, API 20, protocol 1, build 1273043 и хостовый мир. Epoch берётся **до** world check: смена мира во время preflight не даёт выбрать новую сессию автоматически.

Это защита от ошибочного запуска, а не система безопасности вместо EMF. Человек с доступом к консоли может вручную вызвать команды адаптера; raw console не выполняет клиентскую проверку имени мира/персонажа. Использовать его только в согласованной тестовой среде. Адаптер не запускает игру, не включает bridge и не делает backup/restore самостоятельно.
