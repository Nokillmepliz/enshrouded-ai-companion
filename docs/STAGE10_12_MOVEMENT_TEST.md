# Stage 10.12 — первый ручной Companion Movement

2026-11-22: **PREPARED_NOT_INSTALLED_NOT_EXECUTED**.

Обновление статуса 2026-11-22: по отдельному разрешению пользователя установка
выполнена, **INSTALLED_READY_FOR_MANUAL_START**. Ниже сохранён план подготовки;
фактические результаты установки приведены в конце. Движение ещё не выполнялось.

Подготовлено минимальное обновление существующего aic_companion_movement
0.1.0 → **0.1.1**, без изменения Spawn Controller, observer/content и конфигурации.
Четыре заменяемых файла: `main.lua`, `controller.lua`, `mod.json`, `README.md`.
Текущая установка0.1.0 повторно проверена:5/5 исходных записей совпадают с receipt,
SPENT и112 файлов истории (включая spawn-intent) неизменны.

[Exact update manifest](../compatibility/experiments/stage10_12/movement-preparation/exact-update-manifest.json)
содержит before/after SHA-256 и размеры. SHA-256 самого manifest:
`a4c574d4e0678caec35d1a4567ca2cdeed2a5955983a00eae1a3e099b100681d`.
Локальный пакет: `dist/stage10_12_movement_0_1_1`. В игру ничего не копировалось.
Для будущей установки: fresh closed preflight, verified backup текущих LOCAL и
четырёх заменяемых файлов, установка ровно этих четырёх, receipt и проверка
неизменности остальных файлов. Backup/установка на этапе подготовки не выполнялись.
Последний post-close baseline: `90164f817c4ac2bbf1f1a48876a1aee8bb381e4ffe91844ede392c0281585d32`.

## Что делает команда

1. Проверяет Bridge/build, LOCAL Body Test / AI Body Test slot1/1, версии модов.
   Для движения требуется ровно Movement0.1.1; установленная0.1.0 отвергается.
2. Выполняет свежий discover: только FOUND_ONE, без активного villager order.
   Берёт цель из текущей позиции **игрока**, а не из старых координат/entity1025.
3. Проверяет расстояние NPC→цель2–5m, разницу высот<=1m и конечные координаты.
   Показывает entity/координаты, просит подтвердить дневное время, твёрдую свободную
   землю без воды/обрыва/препятствий и ограничение PROFILE_ONLY.
4. Пользователь вводит **MOVE** и Enter в течение30s. Любой иной ввод — отмена;
   просрочка не отправляет движение. Это отдельный локальный ввод, не разрешение
   через чат. Ожидание input само по таймеру не прерывается, но поздний ответ отвергается.
5. Повторяет discover/context после подтверждения и требует того же session/entity/
   player. Записывает exclusive/fsync `runtime/stage10_12/first-movement/movement-intent.json`.
6. Lua заново проверяет уникальность профиля, session/context, отсутствие заказа,
   расстояние/высоту и awake state; `find_wall` проверяет сегмент на высоте+1m.
   Sleep/FindBed/Start/InsideWater и WantsToSleep отвергаются. Проверка дня остаётся
   визуальным подтверждением пользователя: API времени не выдумывается.
7. Один `villager_move`: arrive0.5m, seconds30, stuck10, без hold. EMF проверяет
   домашний радиус/leash и использует штатную навигацию. Никаких записей home,
   faction/inventory/persistence, телепорта или собственного pathfinding.
8. Только read-only status каждые500ms до35s, затем результат/история наблюдения.
   `ACCEPTED` не равен начавшемуся движению. `displacement_observed` и
   `progress_observed` — измерения, а не доказательство причинности.
   `ARRIVAL_OBSERVED` требует arrived callback и расстояния<=0.75m;
   `ENGINE_ARRIVED_NOT_AT_TARGET` не объявляется успешным точным прибытием.

Клиент не повторяет отправку после неопределённого ответа и не вызывает cancel.
Lua расходует единственную попытку до native API. CLI использует один фиксированный
movement intent и отказывается при его наличии. Не удалять intent и не reload мод
для обхода отказа. Защита Lua живёт до reload; это не новое persistent ownership.
Потеря ответа/ошибка Bridge после intent означает STOP и разбор, не новый запуск.
При отказе до intent ручной повтор здесь также не предписан: сначала сообщить ошибку.

Свободная земля/отсутствие воды проверяются оператором; wall-ray не гарантирует
полную проходимость и не заменяет Ground API. Путь проверяет навигация EMF при
заказе: возможны refusal/stuck/timeout. Это не предварительно доказанный маршрут.
Штатный timeout/stuck может сам отправить stop-position event; автосохранения
могут сохранить последствия движения. Обе особенности входят в будущий игровой
тест, который пока не разрешён и не выполнен.

## Одна PowerShell-команда для будущего испытания

**Сейчас не запускать.** Сначала отдельно согласовать установку0.1.1 и сам тест.
Затем пользователь вручную запускает LOCAL Body Test / AI Body Test, дожидается дня
и встаёт на свободной ровной земле в2–5m от NPC. Это будет цель. Не двигаться до
подтверждения/ответа команды. Не открывать диалог NPC; близость игрока может влиять
на его поведение, поэтому точное прибытие не гарантируется.

```powershell
$gameProcess = @(Get-Process -Name enshrouded -ErrorAction Stop)
if ($gameProcess.Count -ne 1) { throw 'Expected exactly one Enshrouded client' }
& 'C:\Enshrouded-ai-companion\.tools\python\python.exe' 'C:\Enshrouded-ai-companion\scripts\companion_movement.py' --pid $gameProcess[0].Id move_to
```

CLI сам проверит контекст и покажет цель. Ввести MOVE только после проверки места.
Цель фиксируется один раз: это **не follow**, за последующим перемещением игрока
NPC не перенаправляется. Наблюдать внешний вид/движение, сохранить вывод; при любой
ошибке остановиться без повторов. Затем вручную закрыть игру, выполнить обычный
короткий post-close audit. Новый NPC не создаётся и существующий не удаляется.

Read-only discover/status остаются доступны; после обновления явно указывать
`--mod-version 0.1.1` для этих команд. Без него сохранена совместимость с0.1.0.
Полноценный follow, бой, inventory и Brain не добавлялись.

## Проверки подготовки

- 30/30 movement tests PASS,0.035s: прежние safety cases и новые manual confirm,
  отмена, просрочка, свежий повторный поиск, смена entity, active order, wall/height,
  sleep, old-version refusal, один native вызов и запрет повторной команды.
- 66/66 Stage10.11 regression tests PASS,0.250s: изменение общего context validator
  не ослабило прежний spawn profile.
- CLI `--help` проверен без Bridge подключения. Полный suite не повторялся.
- Runtime движение не тестировалось; установленный мод остаётся0.1.0 с allow_move=false.

## Разрешённая установка0.1.1 — выполнено

Fresh closed preflight: игра/сервер закрыты, build/depot прежние, snapshot252 game/
23 LOCAL полностью совпал с post-close90164f…. Pinned payload4 и текущая установка
проверены; movement intent отсутствовал. Новый backup27 (LOCAL23+четыре старых файла),
644218bytes, verified SHA-256; путь `runtime/backups/stage10_12-movement-0_1_1`,
manifest SHA `cc0c0101c410e35de7971330530ec7cd9433eb09f2b29529f06bfffe09ac0441`.

Заменены ровно четыре файла согласно manifesta4c574…;4/4 installed hashes PASS.
Остальные248 game-файлов,23 LOCAL записи и112 файлов истории неизменны; config,
Spawn Controller,SPENT,spawn-intent,observer/content,оригиналы/shadow не менялись.
Backup повторно verified. Игра/Bridge/движение не запускались; rollback не выполнялся.
Исходники payload не менялись после30+66 прошедших тестов; suite не повторяли.

[Installation receipt](../compatibility/experiments/stage10_12/movement-installation/receipt.json).
Новый baseline: `runtime/stage10_12/movement-installation/inventory-after.json`,
SHA256 `a806a328acfea8c361a4e1df5750fb08bc4599dd62d09f2a5c49eed7e3e2018d`.

Пользователь вручную загружает LOCAL Body Test/AI Body Test slot1/1 и сообщает
«загрузился». После read-only context check разрешена одна локально подтверждённая
команда move_to из плана выше. До проверки контекста команду не выполнять.
После ручного закрытия — короткий аудит и публикация runtime результата.
