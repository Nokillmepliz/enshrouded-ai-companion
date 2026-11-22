# Stage 10.12 — Persistence & Companion Movement

Дата: 2026-11-22. Результат: **OFFLINE_PROTOTYPE_READY; RUNTIME_NOT_TESTED**.
Игру/сервер не запускали, Bridge к игре не подключали, моды не устанавливали.
Spawn/destroy/движение, запись компонентов и сохранений не выполнялись.
SPENT, spawn-intent и предыдущие истории не открываются новым кодом для записи.

## Обнаружение и границы идентичности

Новый отдельный мод `mods/aic_companion_movement` 0.1.0 выключен в mod.json.
`controller.lua` перечисляет сущности текущего server world через `w:entities()`,
читает `w:template('ActiveNpcState', id)`, Faction и компоненты штатного NPC.
Ожидаемый профиль: template GUID `a1c90001-5e4d-4a91-8a1c-000000000001`,
npcId `2939921867`, faction 11, DynamicActiveNpcState, ActiveNpcStateSaved,
NpcCommon, DynamicPathWalker, доступная позиция, отсутствие PlayerState.
GUID — ожидаемая связь с нашим content patch, **не измеренный GUID сущности**.

- `NOT_FOUND`: в доступном server world нет данного npcId. Это не доказательство
  отсутствия NPC в сохранении: возможна незагруженная область или другой контекст.
- `FOUND_ONE`: ровно один npcId и полный ожидаемый профиль. Возвращаются текущие
  entity ID, position, home, AI state/decision, component flags, session и player.
- `AMBIGUOUS`: несколько одинаковых npcId либо единственный кандидат не проходит
  профиль. Никакого движения; не выбираем «ближайшего» и не создаём замену.

Считаются **все** одинаковые npcId, включая неверную faction/неполные компоненты:
двигательная команда адресуется по npcId и потенциально затронет дубликаты.
Профиль clone получил отдельный npcId в существующем
[`patch.lua`](../experimental/integrated_humanoid_0_5_1/patch.lua): проверка
коллизии среди ресурсов и присвоение при клонировании. Это не гарантия единственного
экземпляра после загрузки мира.

В проверенных Lua world bindings отсутствует getter GUID шаблона живой сущности
или generation ID экземпляра. `emf.item_info().guid` относится к предметам,
его нельзя использовать как GUID этого NPC. Поэтому ответ всегда содержит
`guid_verified=false`, `identity=PROFILE_ONLY`. Entity 6959 не зашит в код.
Даже совпавший профиль после reload не доказывает непрерывность того же экземпляра;
смена session требует нового клиента и нового поиска. Повторное использование ID
внутри сессии сущностью с тем же профилем неотличимо. SpawnTime не объявляется
постоянным UUID и не решает идентичность между перезапусками.

## Подтверждённая механика и источники

Использован уже имеющийся checkout EMF `fa6efdac2d93dd1d8ac6fe0e2a658140aec35241`.
Повторное исследование content/shadow/template и скачивание EMF не выполнялись.
Это проверка исходников API, а не новое доказательство идентичности DLL.

| Вопрос | Что подтверждено исходниками |
|---|---|
| Свободное перемещение | ActiveNpcState: decisionSetup с весами idle/inspect/sit/roam, roamingSetup.maxRadiusFromSpawn, movementSetup, searchTargetSetup. DynamicActiveNpcState хранит state/previousState/decision. |
| Домашняя точка | ActiveNpcStateSaved.spawnPosition; overrideRoamingRange/roamingRange переопределяют радиус. Нулевой override означает stay. Наш код только читает home; штатный путь назначения/переноса дома здесь не установлен и setter не реализован. |
| Сон и отдых | ActiveNpcState содержит sleepSequence/sitSequence, SleepSetup — диапазоны sleepTime/wakeUpTime. NpcCommon содержит sleepTime/wakeUpTime, bedId, interactionStates, currentSequenceId и текущую цель. Присутствие полей не раскрывает все условия AI игры. |
| Навигация | `emf.villager_move(world, entity, {x,y,z}, {arrive,seconds,stuck}, callback)`; результат id либо nil, reason. Callback `(world, id, status)` с arrived/stuck/timeout/gone/cancelled. `emf.villager_moving` позволяет не заменить существующий приказ. |
| Реализация EMF | Очередь NpcCommandEvent GoToPosition по npcId, выполнение на server world. Не собственный pathfinding, не телепорт и не прямая запись компонентов. EMF повторяет потерянную штатную команду с ограничением частоты; это часть одного заказа, не повторный вызов клиента. |
| Ограничения | Проверяются home, walk area и leash. EMF учитывает сон, общение, воду, удалённость игрока; stuck clock может приостанавливаться, общий seconds ограничен. Первый send ставится в очередь уже в add; нельзя обещать, что вызов вообще не повлияет на спящего NPC. Первый тест — днём. |
| Завершение | EMF может признать arrived до указанной точки при TargetReached; timeout/stuck/cancel иногда отправляют «иди в текущую точку». Это игровые события, даже если наш Python только наблюдает. Reload Lua прекращает принадлежащие ему заказы — не перезагружать мод во время теста. |

Точные источники:

- [Lua world entities/position/template и item GUID](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/lua_host/bindings.cpp#L227-L367).
- [Lua villager_move и его параметры](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/lua_host/move_bindings.cpp#L210-L334).
- [Core server gate и отказы](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/api.cpp#L1117-L1160).
- [VillagerMoves: условия, отправка, прогресс и завершение](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/villager_moves.cpp).
- [Описанный контракт и ограничения EMF](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/villager_moves.h).
- [AI setup и сохранённый home](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/sdk/include/emf/generated/components.hpp#L2008-L2320),
  [NpcCommon](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/sdk/include/emf/generated/components.hpp#L16150),
  [DynamicActiveNpcState](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/sdk/include/emf/generated/components.hpp#L22281).

Наблюдения пользователя — лежал ночью, встал при приближении, перемещался днём —
согласуются с возможным штатным поведением, но не доказывают конкретную ветку AI.
Runtime значения новых полей пока не получены. Предыдущие скриншоты подтверждают
внешний вид; сохранение NPC после перезапуска всё ещё неизвестно.

## Прототип движения

`companion/movement.py` использует существующий pinned Bridge и
`validate_context`: точные EMF/build, LOCAL slot1/1, живой игрок, версии модов.
Добавлен отдельный строго фиксированный movement profile; старые spawn проверки
по умолчанию по-прежнему отвергают новый мод. Observer 0.3.0 не изменён.

Lua main намеренно содержит `allow_move=false`, а готовый CLI предоставляет только
discover/status. Снятие блокировки потребует отдельного согласованного обновления
после read-only идентификации NPC. Это **прототип**, не установленное управление.

Метод `move_to(x,y,z, approval=..., intent_path=...)` повторяет поиск, требует
явного `APPROVE_PROFILE_ONLY_MOVE`, fsync эксклюзивного нового movement intent,
затем отправляет один запрос. Он не трогает spawn-intent. Lua повторно проверяет
контекст, уникальность, entity/session, отсутствие текущего заказа, конечные
координаты и дистанцию 2–5 м; попытка расходуется до API. Вызов с исключением или
потерянным ответом не повторяется. Timeout 30 s, stuck 10 s, arrive 0.5 m, hold нет.
Дальность относительно home дополнительно проверяет EMF. Клиент опрашивает каждые
500 мс, по умолчанию не более 35 s; не вызывает cancel/destroy/rollback.

Результаты разделены:

1. `ACCEPTED` — API вернул ID заказа. Отправку события в движок ответ не доказывает:
   `event_sent=UNVERIFIED`.
2. `displacement_observed` — смещение от начальной позиции минимум 0.25 m;
   `progress_observed` — расстояние до цели уменьшилось минимум на 0.5 m.
   Самостоятельное блуждание может дать те же измерения: причинность не доказана.
3. `ARRIVAL_OBSERVED` — callback arrived плюс измеренное расстояние до цели <=0.75 m.
   Иначе `ENGINE_ARRIVED_NOT_AT_TARGET`. Это достижение близости, не полноценный follow.
4. REFUSED/STUCK/TIMEOUT/GONE/CANCELLED/IDENTITY_LOST_NO_RETRY — остановить эксперимент.
   `OBSERVATION_TIMEOUT_NO_RETRY` не означает подтверждённое завершение заказа движком.

Локальная защита от повтора движения ограничена lifetime Lua и эксклюзивным
movement intent. Это не новая глобальная система persistence/ownership: другой
путь intent или reload не должны использоваться для обхода остановки. Команды
движения пока физически заблокированы. Непосредственная запись saves отсутствует,
но будущие штатные autosave могут сохранить последствия игрового движения.

## Следующий ручной тест — план, НЕ выполнено

1. Отдельно согласовать установку только нового выключенного по движению мода;
   подготовить exact manifest/receipt и свежую проверенную копию LOCAL. Не менять
   установленный Spawn Controller, SPENT, intent, observer или content patch.
   Последний известный post-close baseline: SHA-256
   `120850afac7ff4242f5e07b32f8fa071607c2af411a06681cadf61e7bc56fe80`.
   Это исторический baseline; перед установкой нужен свежий preflight.
2. Пользователь запускает LOCAL Body Test / AI Body Test slot1. Проверить
   Bridge hello/state и прежний observer compare/evidence v8 штатными валидаторами.
3. После согласованной установки и проверки контекста выполнить только:

   ```powershell
   & 'C:\Enshrouded-ai-companion\.tools\python\python.exe' 'C:\Enshrouded-ai-companion\scripts\companion_movement.py' --pid <АКТУАЛЬНЫЙ_PID> discover
   ```

   Сейчас команда не готова к runtime: новый мод не установлен; PID не фиксирован.
   FOUND_ONE сопоставить визуально с существующим NPC. NOT_FOUND — не создавать
   замену; AMBIGUOUS — сохранить диагностику и остановиться.
4. Сохранить результаты поиска и нынешний home/position/AI state. Даже FOUND_ONE
   не называть доказательством instance persistence. Закрытие игры — вручную;
   проверить saves и файлы относительно свежего baseline, без восстановления.
5. Только после отдельного разрешения на игровую мутацию и принятия ограничения
   PROFILE_ONLY подготовить reviewed включение движения и свежий movement intent.
   Днём выбрать видимую свободную точку в 2–5 m, внутри домашнего радиуса. До запроса
   проверить позицию, единственность npcId и отсутствие чужого заказа. Один вызов
   move_to, затем только status и визуальное наблюдение 30–60 s. Не общаться с NPC
   во время измерения, не менять home/faction/inventory, не делать follow.
6. При отказе, исчезновении, дубле, смене сессии или неоднозначном ответе прекратить
   тест без retry/cancel/destroy/rollback. Поведение самого EMF при timeout входит
   в разрешаемую будущую мутацию. После ручного закрытия — обычный post-close audit
   и отдельный отчёт. Ничего из этих runtime шагов Stage 10.12 не выполнял.

Открытые риски: persistence после reload; instance identity и reuse ID; полнота
видимого world; реальная доступность компонентов нового NPC; API capability в
работающей DLL; маршрут/сон/диалог и самопроизвольное движение; интерпретация
прибытия; естественные autosave. `spawn_ready=false` сохраняется.

## Выполненные проверки

- Новые тесты: 22/22 PASS (Lua 5.4 через Lupa, fake world/API/Bridge, включая
  реальный main.lua, размер ответа и запрет движения в поставляемой версии).
- Итоговый полный suite: `python -m unittest discover -s tests`, 974 tests,
  973 PASS, 1 SKIP, 0 failures/errors, 19.716 s, exit 0.
- Причина SKIP отдельно проверена verbose запуском `test_kfc_inspector_audit.py`:
  directory symlink unavailable, WinError 1314; права Windows не менялись.
- Покрыты FOUND_ONE/NOT_FOUND/AMBIGUOUS, неверная faction/компоненты,
  LOCAL context/session/entity changes, существующий заказ, нечисловые/далёкие
  цели, displacement/progress/arrival, API refusal/exception, timeout/stuck/gone/
  cancelled, durable intent и запрет повторной отправки, bounded read-only polling.
- Это не игровое испытание и не подтверждение persistence/навигации NPC.
