# Stage 10.16 — Movement 0.3.2: отмена и восстановление расписания

2026-11-22. **PREPARED_NOT_INSTALLED / RUNTIME_UNVERIFIED**.

Исправлены два дефекта ночного теста PID507224. Игра и сервер не запускались,
Bridge не использовался, обновление не устанавливалось. Установлена прежняя
Movement0.3.1; её история и восстановленные часы сохранены.

## Отмена движения

Команда Follow теперь только ставит отмену принадлежащего ей приказа в очередь.
В свежем server tick контроллер проверяет identity и текущий приказ, фиксирует
однократный CANCEL_REQUEST и вызывает `villager_move_cancel`. После этого
вызова он не читает world, позицию, компоненты или статус. Ответ команды Bridge
также не оказывается после вложенного cancel callback: сам cancel выполняется
позже, в tick.

Следующий tick со свежим world проверяет исчезновение отменяемого приказа.
До подтверждения новые приказы запрещены. Подтверждение очищает старый приказ;
следующий шаг Follow использует актуальную позицию игрока. Исключение/отказ
отмены останавливает Follow, повторного cancel нет. Если отменяемый приказ
остаётся активным5с, фиксируется CANCEL_TIMEOUT; Follow останавливается без
нового движения. У прежнего native-приказа остаётся его30-секундный deadline.
Чужой приказ не отменяется и не блокирует восстановление нашего schedule lease.

Алгоритм маршрутов, лимиты и20/50 X/Z не изменены. Прибытие по-прежнему3D,
дистанция около2м; высота сама по себе не запрещает маршрут.

## STOPPED и cleanup

`stop()` меняет только состояние Lua, поэтому допустим и после ошибки,
сделавшей переданный world недействительным. STOPPED прекращает Follow,
но не прекращает работу cleanup в server ticks.

Статус отдельно содержит `cleanup`: NONE, PENDING или DONE. При STOPPED
контроллер в свежем callback проверяет уникальность и прежние session/entity,
подтверждает отмену и вызывает существующий `schedule.release`. При ошибке
компонента, журнала или временной недоступности identity lease остаётся PENDING;
проверки восстановления повторяются не чаще раза в секунду. Новые приказы
движения при этом не отправляются, исходная причина остановки сохраняется.

Существующие правила владения полями, запись исходных часов до override,
readback, append-журнал и native sleep exit не изменены. В частности, чужие
значения не перезаписываются. Гарантия восстановления относится к доступному
прежнему NPC, работающему tick и успешной записи/чтению компонентов и журнала.
При смене сессии, неоднозначности, недоступном диске или принудительном
завершении процесса нельзя обещать восстановление; состояние остаётся
неподтверждённым. Принудительная запись в другой NPC не применяется.

Runner0.3.2 после остановки или ошибки ограниченно опрашивает только `f_status`
(до8с/16 запросов, без повторения move/stop). Результат явно содержит
`schedule_cleanup=CONFIRMED` или `UNCONFIRMED`; ошибка Runner сохраняется в отчёте.
Read-only запросы используют прежние проверки версии, контекста и session.

## Проверки

**194/194 целевых теста PASS,0.798с.** Полный suite не повторялся.

```powershell
& .tools/python/python.exe -m unittest tests.test_follow_lifecycle tests.test_follow_stage16_package tests.test_companion_schedule tests.test_npc_schedule tests.test_companion_follow tests.test_companion_movement tests.test_stage10_11 tests.test_follow_stage14_installation -q
```

Новые проверки моделируют синхронный cancel callback с увеличением generation:
любое обращение к старому world завершает тест ошибкой. Проверены следующий
tick/новая цель, отсутствие перекрытия приказов, REQUEST_ERROR, исключение
native move/cancel, зависшая отмена без повторов, чужой приказ, временная потеря
identity, отказ записи RELEASED и последующее восстановление. Host-тест
выполняет реальный main.lua: ошибка команды → следующий tick → исходные часы
и ACQUIRED→RELEASED без reload; старые SPENT/journal/intent сохраняются.
Проверены read-only наблюдение cleanup и честный UNCONFIRMED при timeout.

Существующие тесты покрывают20/50, обновление цели,3D/перепады высоты, Ground/Path,
ночное пробуждение, переход суток и ограничение одной сессии. Два старых host
fixture обновлены для нового имени журнала; исторический пакет0.3.1 проверяется
по своему неизменному архиву, текущие исходники — по новому manifest.
Первый расширенный запуск обнаружил старое имя журнала в fixture discovery;
оно исправлено. Игровое Follow0.3.2 ещё не проверено.
При итоговом ревью исправлена ссылка Runner на receipt прежнего этапа;
добавлен тест разрешённого запуска с receipt/token/journal именно Stage16.

## Пакет и будущая установка

- Пакет: `dist/stage10_16_movement_0_3_2`.
- [Exact manifest](../compatibility/experiments/stage10_16/exact-update-manifest.json),
  SHA-256 `c4fd95db4d72a2ca90834f0f5769cef2d79b7a26afe1c1a2c1bdc73a2f938804`.
- Ровно7 операций: заменить main.lua, follow.lua, follow_config.lua, mod.json,
  README.md; добавить follow-stage10-16.lock и пустой schedule-stage10-16.jsonl.
  schedule.lua и контроллер discovery не меняются.
- Baseline: post-close PID507224, SHA
  `aaf088bd87def15f73fe10a349831af4477fbbdfc1e1d1ad4de9d2260b8593ab`.
- Будущий fresh backup28: LOCAL23 + пять заменяемых файлов. После установки
  effective37, receipt и rollback dry-run. Сейчас backup/receipt0.3.2 не созданы.
- Отдельные Stage16 token/lock/Python journal;128 прежних runtime/intent файлов
  и112 записей spawn-history защищены. Stage13–15 SPENT и история не сбрасываются.

Свежая узкая read-only проверка: closed/build PASS, exact payload7 PASS,
установленные35 содержимых и LOCAL23 совпадают с post-close baseline, protected
history PASS. Большие ресурсы повторно полностью не хешировались; полный
baseline проверит штатный установщик перед записью.
[Результат подготовки](../compatibility/experiments/stage10_16/preparation-check.json).

Только после отдельного разрешения установки:

```powershell
& 'C:\Enshrouded-ai-companion\.tools\python\python.exe' 'C:\Enshrouded-ai-companion\scripts\install_follow_stage16.py' --install-approved
```

После отдельного разрешения одной сессии и ручной загрузки LOCAL Body Test /
AI Body Test slot1/1 Runner запускается с актуальным PID:

```powershell
& .tools/python/python.exe scripts/follow_stage16.py --pid <PID> --manifest-sha256 c4fd95db4d72a2ca90834f0f5769cef2d79b7a26afe1c1a2c1bdc73a2f938804 --authorized-session
```

Следующий тест: ночью проверить wake, движение по ровной поверхности, затем
смену цели движущимся игроком с CANCEL_REQUEST→CANCEL_CONFIRMED и новым приказом.
При нормальной остановке/ошибке дождаться STOPPED + cleanup DONE +
SCHEDULE_RESTORED/RELEASED без reload. Считать успехом Follow только реальное
сближение NPC, а не ACCEPTED. При ошибке не запускать вторую сессию.
После ручного закрытия — короткий аудит. `spawn_ready=false`.
