# Stage 10.13 — Autonomous Companion Test Runner + Follow Prototype

**Текущее состояние, 2026-11-22:** Movement0.2.1 установлен, exact3/effective31
hashes и backup26 PASS. Старый журнал и follow lock сохранены; ожидается
ручной запуск игры. [Исправление и продолжение](STAGE10_13_REGISTRATION_FIX.md).
После «загрузился» разрешена одна автоматическая сессия без MOVE.

**Предыдущая попытка0.2.0:** `BLOCKED_COMMAND_NAME_LIMIT`.
Попытка PID471028 завершена; игра закрыта пользователем. Контекст и Bridge
прошли проверку, но EMF не зарегистрировал follow_start/step/stop/status:
полные имена имеют35/34/34/36 символов при лимите32, включая префикс мода.
follow_start вернул unknown command. Follow не начался, команд движения0.
Это дефект подготовленного интерфейса; mock регистрации в офлайн-тестах
не проверял лимит. Исторический PASS тестов не подтверждает загрузку команд.

Post-close audit: оригиналы67, shadow77 и installed31 неизменны; backup26/26
PASS, история112 и старые intent/SPENT сохранены. Follow latch остался UNUSED,
но Python session journal сохранён и запрещает повтор. LOCAL23 без добавлений
или удалений:6 content/7 metadata изменений,5 сохранений мира в журнале.
Семантическая целостность сохранений не установлена; восстановления не было.
Post_close_v2 ATTRIBUTION_PASS. Отчёт:
[post-close-471028.json](../compatibility/experiments/stage10_13/post-close-471028.json).
Новый baseline: `runtime/stage10_13/session471028/post-close/inventory.json`,
SHA-256 `ac979a13426a5d311bd37f48e502239db238e322980249b1c8f16a2eb8629534`.

Следующая итерация: короткие имена команд (например f_start/f_step/f_stop/f_status),
проверка результата регистрации и regression-тест с реальным лимитом32.
Без сброса существующего journal; любое продолжение требует отдельного
проверяемого плана. Исправление/установка/повторный запуск сейчас не выполнялись.
Исходный planned тест следования и recovery остаётся NOT_TESTED.

**История установки, 2026-11-22:** Movement0.2.0 установлен по отдельному
разрешению пользователя. Exact6/6 и effective31/31 hashes PASS; backup26/26
(641142 байта) проверен. LOCAL23, остальные251 game-файлов и112 записей истории
неизменны. Старый SPENT сохранён, новый follow latch UNUSED; офлайн-проверка
Runner тогда прошла, runtime ещё не выполнялся. Receipt:
[installation/receipt.json](../compatibility/experiments/stage10_13/installation/receipt.json).
Rollback dry-run PASS, откат не выполнялся. Режим native сохранён.
Ниже сохранён исходный отчёт подготовки; актуальный итог указан выше.

2026-11-22. Подготовка офлайн; **не установлен и не испытан в игре**.
Архитектура сохранена: Lua Body Adapter + Python Bridge. Обновление Movement
0.2.0 использует прежний discovery и профиль NPC. Новые spawn/destroy, запись
компонентов, home/faction/inventory/persistence и прямой доступ к сохранениям
для записи отсутствуют. SPENT и предыдущие intent сохранены.

## Поведение и границы

`companion/follow.py` и `scripts/companion_follow.py` запускают одну тестовую
сессию после отдельного разрешения и сообщения «загрузился». Ввод MOVE не нужен.
До старта — строгая проверка EMF0.6.18/API46, Lua1.39, patch/observer по прежнему
контракту Bridge, Movement0.2.0 и LOCAL Body Test / AI Body Test slot1/1.
Нет игрока при сохранённом LOCAL-контексте: до30с ожидания без мутаций.
Потеря игрока/контекста после старта — STOPPED. Уникальность и профиль NPC
проверяются заново; entity1025 не используется как постоянный идентификатор.
Ограничение PROFILE_ONLY остаётся.

| Состояние | Поведение |
|---|---|
| WAITING_FOR_PLAYER | Начальный режим; после выхода за20м отменяется только собственный заказ, новых заказов нет |
| FOLLOWING | Вход при дистанции ≤19м; последовательный Ground/Wall/Path probe |
| MOVING | Один принятый villager_move; следующий заказ не накладывается |
| IDLE_NEAR_PLAYER | Дистанция ≤2м; движение отменяется, новый подход только при ≥2,8м |
| STUCK / RECOVERING | STUCK/TIMEOUT записываются отдельно; максимум две новые проверенные цели, cooldown4с |
| STOPPED | Лимит, неопределённость, потеря контекста/идентичности, отказ API или явное завершение |

Гистерезис19/20м предотвращает дребезг на границе. На дистанции19–20м сохраняется
предыдущий режим. За20м отмена проверяется через `villager_moving`; ошибка отмены
останавливает сессию без повторного cancel. Отмена заказа не доказывает физическую
неподвижность NPC и не блокирует его штатное поведение.

Цель — точка в1,8м от игрока в сторону NPC. При recovery направление смещается
на45/90°. Игрок не является целью коллизии. Ground проверяет координаты/высоту,
fog и water; Wall — препятствия; Path — достижение, только walk, без дверей,
прыжков и плавания, длина≤30м. Перед отправкой ещё раз проверяются позиции,
расстояние от игрока и Wall. Запросы идут последовательно, максимум один
незавершённый, включая устаревшие callback; всего≤30 probes. Неуспешный поиск
останавливает сессию, не создаёт бесконечного перебора.

Это доступные проверки среды, не доказательство отсутствия всех динамических
коллизий. Native villager_move проверяет home/leash; его отказ сохраняется.
При движении игрока >2м цель пересматривается после cooldown, прежний заказ
сначала отменяется. Нового pathfinding и телепортации нет.

Лимиты: Lua180с, Python завершает цикл через175с после start; ≤24 заказа,
≤2 восстановления, cooldown4с. Опрос примерно раз в секунду плюс длительность
Bridge RPC, без ускоренного восполнения пропущенных отсчётов. Каждый заказ:
seconds12, stuck6, arrive0.5; опциональный hold5. Watchdog проверяется на server
tick раз в секунду: отсутствие heartbeat более4с прекращает сессию. При утрате
идентичности cancel не отправляется; остаются конечные таймауты движка.

## Roaming: что подтверждено

Ограниченное исследование уже имеющегося upstream snapshot
`fa6efdac2d93dd1d8ac6fe0e2a658140aec35241`:

- [villager_moves.h](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/villager_moves.h#L2): повторные штатные GoToPosition, паузы при сне/диалоге/воде, конечный hold.
- [villager_moves.cpp](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/villager_moves.cpp#L145): `ActiveNpcStateSaved.overrideRoamingRange/roamingRange`, home=`spawnPosition`, иначе template `roamingSetup.maxRadiusFromSpawn`; leash из `searchTargetSetup.targetRadius/bedRadius`. Нулевая область запрещает move.
- [Lua API](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/docs/modding/lua.md#L786): hold возвращает NPC к точке после прибытия, прекращается по cancel/reload, ничего не пишет в компоненты. Sleep/decision/взаимодействие могут приостанавливать заказ.
- [cancel binding](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/api.cpp#L1162): на dispatch server world отмена непосредственная; вне него — на следующем шаге. Контроллер дополнительно проверяет исчезновение заказа.

**Безопасное полное отключение самостоятельного roaming с сохранением move
не подтверждено.** Поэтому пакет оставляет `roaming='native'`. Никаких записей
AI state/decision, обнуления радиуса или удаления DynamicPathWalker нет.
Переключатель `roaming='hold'` подготовлен как обратимый конечный режим удержания
после arrival, но не называется отключением roaming. Он ещё не проверен в игре;
он не создаёт новый заказ при далёком игроке, не гарантирует постоянную стойку и
не поддерживает блокировку сна. Его включение потребует отдельной ревизии пакета
при закрытой игре. Главная цель «всегда стоит в ожидании» остаётся ограничением.

## Одно разрешение на сессию вместо отдельных MOVE

Фиксированный `runtime/stage10_13/test-session.jsonl` создаётся эксклюзивно,
fsync выполняется перед start и каждой выдачей разрешения на шаг. Нельзя выбирать
новый каталог/имя или перезапустить после неизвестного результата. Lua дополнительно
потребляет `follow-session.lock` UNUSED→SPENT до первого заказа. Reload не даёт
новое разрешение; старые spawn/movement intent не изменяются. Номера step строго
последовательны. В рамках сессии разрешены только заранее ограниченные recovery
после известного STUCK/TIMEOUT. При неопределённом ответе Bridge новых RPC нет.

Локальные SAMPLE записывают позиции NPC/игрока, расстояние, состояние, target,
order, AI state/decision, home, числа orders/probes/recoveries и roaming mode.
EMF `AIC_FOLLOW` пишет результаты Ground/Path, принятие заказа, его длительность,
фактическое смещение, итог/дистанцию и cancel. Python автоматически формирует
REPORT с покрытием состояний, дистанциями и лимитами. Эти логи нужно сопоставить
после игры; принятие заказа, наблюдаемый подход и ARRIVED — разные результаты.
STUCK остаётся STUCK, короткое native arrival — ENGINE_ARRIVED_SHORT. Неохваченные
сценарии считаются NOT_TESTED; сам набор состояний не доказывает полноценный follow.

## Пакет и следующая игровая сессия

Пакет: `dist/stage10_13_movement_0_2_0`, воспроизводится
`scripts/prepare_companion_follow.py`. Точный manifest:
[exact-update-manifest.json](../compatibility/experiments/stage10_13/exact-update-manifest.json).
Заменяются только `main.lua`, `mod.json`, `README.md`; добавляются только
`follow.lua`, `follow_config.lua`, `follow-session.lock` в существующий мод.
`controller.lua`, EMF, observer, content patch и spawn controller не меняются.
Manifest содержит исходные/целевые SHA и31 effective hashes, включая новый lock.
Lock запрещено перезаписывать, если файл уже существует.

После отдельного разрешения установки: closed preflight по post-close baseline
PID456828, свежий verified backup LOCAL23 + заменяемые3 =26 файлов; проверка
исходных хешей, добавление только отсутствующих файлов, receipt и сверка31 hashes.
Ошибки останавливают установку, автоматического rollback нет. Сейчас backup и
установка НЕ выполнялись. Исходный baseline SHA:
`9698e1e8e0437b22bc4bbfca40e065379bc7001343343b438aff2ca8d858e553`.

После разрешения игрового теста и сообщения «загрузился» Codex определяет PID,
проверяет LOCAL/Bridge, hashes/истории и запускает один Runner. Команда для Codex
(пользователь её вручную не вводит; PID и hash берутся из preflight):

```powershell
& 'C:\Enshrouded-ai-companion\.tools\python\python.exe' 'C:\Enshrouded-ai-companion\scripts\companion_follow.py' --pid <PID> --manifest-sha256 <SHA256> --authorized-session
```

Пользователь только перемещается: начать дальше20м, подойти до19м, постоять,
пройти несколько метров/повернуть, выйти за20м и вернуться. Нужна дневная открытая
площадка внутри штатной home/leash области. Намеренное застревание не обязательно:
если его не было, recovery остаётся непроверенным. Проверка «после отключения
roaming не гуляет» для текущего native-пакета — NOT_APPLICABLE, не PASS.

После ручного закрытия — короткий аудит по новому install baseline с отдельно
ожидаемым изменением follow-session.lock и новыми логами. Проверить originals,
shadow, установленные файлы, старые intent/SPENT и LOCAL; сохранить отчёт/коммит.
Игру не запускать из Codex, не создавать NPC и не сбрасывать latch.

## Выполненные проверки

- Целевые Lua/Python/host тесты:69/69 PASS. Покрыты радиус/гистерезис,
  offset, Ground/Wall/Path, устаревшие и повторные callback, очередь/лимит probes,
  конфликт заказов, отказ cancel без повтора, STUCK/recovery/budgets, таймаут,
  смена сессии/дубликаты, reload с SPENT, размер ответа и durable журнал.
- Финальный suite:1021 тест,1020 PASS,1 SKIP,20,823с; Python exit0.
  Локальный лог: `runtime/stage10_13-offline-tests-final.txt`.
- Closed/build check PASS;28 установленных файлов неизменны, LOCAL23 совпадают
  с post-close baseline,112 записей истории и прежние movement intent сохранены.
- Package6/6 hashes PASS. Manifest SHA-256:
  `5e18844a7999679f1cd0af12fbf49ce00813c023b0bbc3674c90b40dab09b4c8`.
- В этой задаче Bridge к игре не подключали, игру не запускали, моды не
  устанавливали, NPC не двигали. Офлайн-тесты не подтверждают живой follow,
  отсутствие конфликтов с AI или успешную отмену в конкретной игровой ситуации.

Вердикт: `OFFLINE_FOLLOW_PROTOTYPE_READY_WITH_ROAMING_LIMITATION`.
Следующий шаг — отдельное разрешение установки, затем отдельная игровая сессия.
