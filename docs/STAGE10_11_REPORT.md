# Stage 10.11 — First Humanoid Spawn: офлайн-подготовка

**Обновление после отдельного разрешения:** aic_first_spawn 0.1.0 установлен,
verified backup23 и installed7+existing16 проверены; preflight READY_FOR_MANUAL_START.
См. [отчёт об установке](STAGE10_11_INSTALLATION.md). Spawn по-прежнему не разрешён.
Ниже сохранены исходный офлайн-план и его результаты.

2026-11-18. Исходный commit `3337a650f59cd1921e9ca95a3b8ebd5100480ce2`.
**READY_FOR_EXPERIMENTAL_SPAWN_APPROVAL** — готов пакет и план ограниченного
эксперимента. Это не разрешение на установку или spawn и не production readiness.

```text
experimental_spawn_executed=false
production_spawn_ready=false
spawn_ready=false
RUNTIME_RENDER_CONFIRMED=UNKNOWN
```

Игра/сервер не запускались, модуль не установлен, игровые файлы и сохранения не
изменялись. Backup пока только спланирован. Observer, EMF, patch 0.5.1 и shadow/cache
не менялись. Native расширение для этого ограниченного эксперимента не требуется.

## Подтверждённая исходная точка

Прочитаны AGENTS.md, PROGRESS.md, Stage10.10.3, Stage10.8 spawn API/safety contract,
Stage10.9 identity/position/persistence/faction/destroy/variants/safety gates и
пересмотр API из Stage10.10. Старые production gates не ослаблены и не переписаны.

Свежий read-only preflight подготовки сравнил **все 235 game и 23 LOCAL records**
с post-close baseline Stage10.10.3 по SHA-256/размеру/identity/mtime/links: совпали.
Game/server закрыты, Steam build/depot прежние, installed16/16 проверены.
SHA inventory: `2fe87275d6c666bdf8aae2ba810cc606e2a52e1daeb4d95ccbf19d86f60a4987`.
Итог предыдущего теста — LOAD_ONLY_SUCCESS, A/H/R/B/C PASS, V REFERENCES_ONLY.

Используется тот же template GUID `a1c90001-5e4d-4a91-8a1c-000000000001`,
npcId `2939921867`, PlayerAlly/11, 82 components, 102 joints, 63 dependencies,
18 visual references, 9 HashKey32. Независимый KFC readback не повторялся.

## Минимальный API и источники

Проверена локальная закреплённая копия EMF 0.6.18:
`fa6efdac2d93dd1d8ac6fe0e2a658140aec35241`, API46, Lua1.39.0.
Ссылки ниже относятся именно к этому commit, не к меняющемуся master.

| Задача | Подтверждённый механизм и ограничение |
| --- | --- |
| Создать NPC | `emf.spawn(world, GUID, x, y, z)` в server callback; возвращает числовой EntityId, 0 неоднозначен |
| Позиция игрока | `emf.local_player()`, `world:position(id)` в метрах |
| Поверхность | `emf.ground_at(world,x,z,fn)` асинхронно; отдельно проверить ok, координаты, fog и water_y |
| Доступность места | `emf.path_find(world,from,to,opts,fn)` — read-only поиск по игровому path grid; found недостаточно, проверяются reaches и endpoint |
| Строительная преграда | `emf.find_wall(world,from,to)`; попадание запрещает spawn, nil само по себе НЕ доказывает свободное место |
| Наблюдение | `world:entities`, `world:get`, `world:template`, `world:position`; faction читается, не записывается |
| Сессия | `emf.session_token()` связывает процесс и world session; не является generation экземпляра |
| spawn_ex | Lua `emf.spawn(..., components)` использует native spawn_ex; до 15 дополнительных компонентов, CurrentTransform задаётся отдельно. Для первого теста extras не нужны |
| Удаление | destroy принимает ID без атомарного сравнения generation/ownership; в новом модуле отсутствует |

Источники:

- [Lua spawn и spawn_ex binding](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/lua_host/bindings.cpp#L865).
- [Spawn wrapper, transform и guarded fault](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/spawn.cpp#L16).
- [ground_at callback](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/lua_host/map_bindings.cpp#L232).
- [path_find status, reaches и options](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/lua_host/path_bindings.cpp#L58).
- [Описание path grid, радиуса width и высоты](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/docs/modding/lua.md#L642).
- [find_wall и read-only world access](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/docs/modding/lua.md#L854).
- [Session token](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/lua_host/host.cpp#L711).
- [Companion summon](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/mods/companion/companion.cpp#L198): существующий spawn с post-spawn faction; такую смену faction здесь не переносим.
- [Beastmaster spawn](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/mods/beastmaster/pack.lua#L208): использование template GUID и extras, но его respawn/recovery не копируются.
- [Villager Jobs и переиспользование сохранённых ID](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/mods/villager_jobs/jobs_logic.h#L151).
- [EntityId](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/sdk/include/emf/generated/components.hpp#L170),
  [ActiveNpcStateSaved](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/sdk/include/emf/generated/components.hpp#L2290),
  [ForceSave](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/sdk/include/emf/generated/components.hpp#L11351).

Новые API устраняют прежний запрет из-за полного отсутствия ground/path query.
Они не дают точного collision capsule/instance generation и не гарантируют отсутствие
опасности. Это допустимо только в описанном disposable visual experiment после
отдельного принятия рисков, не для постоянного компаньона.

## Реализованный контроллер

- [Lua policy](../mods/aic_first_spawn/controller.lua) и [host binding](../mods/aic_first_spawn/main.lua).
- [Python client](../companion/experimental_spawn.py), [read-only installation gate](../companion/experimental_install_check.py),
  [CLI](../scripts/experimental_spawn.py), [offline builder](../scripts/prepare_stage10_11.py).
- Отдельное пространство команд `aic_first_spawn.*`; неизменный observer не получает мутационных команд.
- Состояния NEW → GROUND → PATH → READY → ATTEMPTED → RETURNED_UNVERIFIED.
  Ошибка/неоднозначность/смена контекста → STOPPED. Повтор/respawn отсутствуют.
- Только hardcoded GUID; перед probe и spawn отвергается уже существующий npcId.
  Один API attempt не доказывает отсутствие автоматического поведения villagers.
- Python проверяет версии, process/PID, LOCAL names/storage/slot1, живого игрока,
  точный список трёх модов. Lua — server world, session token, local player,
  имя персонажа и ровно одного PlayerState. Lua сам не читает world slot/storage:
  эти проверки принадлежат Python; ручной обход клиента не входит в контракт.
- prepare не создаёт entity. Кандидат: +4m по мировой X. Ground: не более 0.75m
  разницы высоты, fog none/removed, water_y отсутствует. Path: radius0.6m/height2.2m,
  без jumps/doors/swim/closest, только walk, длина ≤8m, последний point ≤0.5m от цели.
  Spawn на ground+0.1m, дистанция 3–5m. Нужен ручной осмотр сухого открытого места.
- Probe/confirmation сроком 20s, игрок не должен сместиться больше 0.25m.
  Просрочка блокирует попытку; автоматического повторного probe/spawn нет.
- Перед вызовом Python пишет эксклюзивный fsync journal intent; Lua проверяет,
  пишет, flush/close и перечитывает `attempt.lock`: UNUSED → SPENT!, тот же key.
  Lock не удаляется, не сбрасывается после error/0/timeout/reload/session change.
  Неполная запись или отсутствие файла блокирует spawn. Lua flush не гарантирует
  устойчивость при потере питания; независимый Python journal сохраняется.
- Spawn требует точной фразы `I_APPROVE_ONE_DISPOSABLE_SPAWN`, подтверждения
  осмотра места и принятия риска persistence. Параметры не предоставлены заранее
  как автоматическая авторизация. Request/response журналируются без повторов.
- observe читает npcId/faction, position и наличие visual/persistence components.
  Несовпадение останавливает наблюдение. Совпадение не доказывает ownership,
  render или мирное поведение. Destroy/dismiss/teleport/faction writes отсутствуют.

## Пакет, установка и backup — пока только план

Пакет: `C:\Enshrouded-ai-companion\dist\stage10_11_first_spawn_0_1_0`.
Игра: `D:\SteamLibrary\steamapps\common\Enshrouded`.
[Exact manifest](../compatibility/experiments/stage10_11/exact-install-manifest.json), SHA-256:
`6ecc792b6c320dc19f0fa201259c573efd142c4c37a579eab07376dc40b9e1e3`.

Только семь новых destinations, все сейчас отсутствуют:

| Файлы относительно каталога игры | Назначение |
| --- | --- |
| `emf/mods/aic_first_spawn/mod.json` | Мод 0.1.0, default disabled |
| `emf/mods/aic_first_spawn/main.lua` | Привязка к API и persistent latch |
| `emf/mods/aic_first_spawn/controller.lua` | Экспериментальный автомат |
| `emf/mods/aic_first_spawn/README.md` | Контракт и ограничения |
| `emf/mods/aic_first_spawn/binding.lua` | Private одноразовый deployment key |
| `emf/mods/aic_first_spawn/attempt.lock` | Изначально UNUSED, затем никогда автоматически не сбрасывается |
| `emf/config/aic_first_spawn.ini` | Включает только новый мод после разрешённой установки |

`client-binding.json` и exact manifest остаются в проекте. Их не копировать в игру.
Никаких DLL/EXE/установщиков, EML patch, второго клиента/аккаунта/server нет.
Старые 16 installed files остаются прежними, effective set после установки — 23.
Private key, journal, бинарники, saves и сырые ресурсы в GitHub не публикуются.

[Backup plan](../compatibility/experiments/stage10_11/backup-plan.json):
**23 LOCAL-файла / 637447 bytes (≈0.61 MiB)**, включая персонажа/мир и их текущие
backup-0…9. Полная копия игры не нужна; старые verified backups/quarantine сохраняются.
План проверен существующим `validate_backup_plan` без копирования файлов.
Будущий destination: `runtime/backups/stage10_11-local-before-first-spawn`.
При изменении baseline перед установкой остановиться и подготовить новый план.

После отдельного разрешения на установку:

1. Проверить закрытую игру/server, Steam/build, baseline, pins, отсутствие каждого
   destination и конфликтов. Подтвердить, что Body Test / AI Body Test можно считать
   disposable: потеря прогресса после backup приемлема.
2. Вызвать существующий verified_backup для 23 записей, затем verify_backup;
   сохранить manifest/hash. Нельзя использовать старый backup с другой версией saves.
3. Эксклюзивно скопировать только 7 manifest entries с журналом до каждого действия,
   без overwrite; проверить SHA/size. При ошибке остановиться, не делать автооткат.
4. Создать новый receipt `aic_experiment_receipt_v1`: status INSTALLED, manifest_sha256,
   точные entries, backup_path, backup_manifest_sha256. Старый receipt не редактировать.
   Штатную транзакцию для этого additive manifest выполнить/проверить в разрешённой
   фазе установки; текущий builder намеренно не содержит установочных операций.
5. Проверить existing16+new7, originals67/shadow77/LOCAL23, сохранить новый inventory
   перед запуском. File-only removal dry-run только для этих 7 файлов, без выполнения.

CLI до подключения проверяет pinned receipt, 7 установленных файлов (для latch
допускает только UNUSED/SPENT с тем же key), backup23 и прежний receipt/installed16.
Отсутствие реального receipt/backup блокирует живое выполнение.

## План игрового эксперимента после отдельного согласования

1. Пользователь вручную запускает LOCAL Body Test / AI Body Test, slot1. Другие
   миры, персонажи и сетевые подключения запрещены. Не создавать NPC автоматически.
2. Проверить новый PID, Bridge hello/state, версии, LOCAL context. Observer status
   остаётся read-only. Старый integrated_observe ожидает лишь два активных мода;
   не менять его allowlist: для экспериментального контекста использовать новый клиент.
3. Пользователь выбирает открытое ровное сухое место без врагов/огня/обрыва и смотрит
   область примерно 4m по +X. Read-only prepare → явные status до READY, не более20s.
   Не выполнять probe бесконечным polling; при refused/STOPPED/timeout остановиться.
4. Сообщить пользователю точные координаты, данные ground/path и оставшиеся риски.
   Получить непосредственное разрешение на один spawn и подтверждение осмотра места.
   Если разрешение не получено в срок — spawn запрещён; новый эксперимент требует
   отдельного review, а не ручного удаления journal/latch.
5. Один вызов spawn через CLI с тремя явными подтверждениями. Возвращённый ID означает
   только RETURNED_UNVERIFIED. При 0/error/потере ответа не повторять вызов.
6. Выполнить observe и визуальный чек-лист ниже. Если штатно — несколько отдельных
   read-only наблюдений в течение30–60s, с фиксацией времени; без combat/follow/AI.
7. При агрессии, T-pose/неверной модели, провале в поверхность, исчезновении,
   неоднозначной identity или ошибке — остановить команды, пользователь закрывает игру.
   Не пытаться лечить ситуацию teleport/faction/destroy. При зависании пользователь
   завершает процесс самостоятельно; уже выполненные autosaves остаются возможными.
8. Пользователь закрывает игру и сообщает об этом. Собрать логи, snapshots и результаты.
   Новый post-close audit использует **post-install baseline**, не старый фиксированный
   скрипт для PID202212. Проверить originals, shadow, unchanged16 и 6 immutable новых
   файлов; 7-й — latch — отдельно проверить точное UNUSED→SPENT изменение, identity,
   size и отсутствие reset. Затем v2 атрибуция логов; неизвестное изменение блокирует итог.
9. Сравнить весь LOCAL inventory с новым backup. Не объявлять saves неизменными и не
   выводить persistence из одного изменения SHA. Не перезапускать тестовый мир до review.
10. Только по отдельному разрешению — восстановление **полного** verified LOCAL набора
    теста с новым проверенным restore plan; сохранить evidence и копию состояния после
    эксперимента. Не выполнять частичное KSD редактирование/restore или старый rollback.

Будущие команды (НЕ выполнялись; receipt/его SHA будут получены после установки):

```powershell
$common = @('--package', 'C:\Enshrouded-ai-companion\dist\stage10_11_first_spawn_0_1_0',
  '--manifest-sha256', '6ecc792b6c320dc19f0fa201259c573efd142c4c37a579eab07376dc40b9e1e3',
  '--receipt', '<NEW_RECEIPT_PATH>', '--receipt-sha256', '<NEW_RECEIPT_SHA256>',
  '--pid', '<CURRENT_GAME_PID>', '--live-approved')
.\.tools\python\python.exe scripts/experimental_spawn.py prepare @common
.\.tools\python\python.exe scripts/experimental_spawn.py status @common
# Только после непосредственного отдельного разрешения и подтверждения места:
.\.tools\python\python.exe scripts/experimental_spawn.py spawn @common `
  --authorization I_APPROVE_ONE_DISPOSABLE_SPAWN `
  --confirm-clear-area --accept-disposable-risk
.\.tools\python\python.exe scripts/experimental_spawn.py observe @common
```

При прежнем Access denied — только адресное согласованное выполнение вне sandbox
либо PowerShell пользователя. Не менять ACL/антивирус, не обходить отказ согласования.

## Визуальный чек-лист пользователя

Для каждого пункта записать PASS / FAIL / UNKNOWN, время и имя скриншота:

- NPC появился ровно один; человеческая модель, а не только EntityId.
- Голова и лицо; волосы; руки и ноги отображаются.
- Текстуры, пропорции, одежда и экипировка корректны.
- Нет T-pose, присутствует idle animation.
- Ноги контактируют с поверхностью, тело не парит и не погружено в геометрию.
- Реакция на присутствие игрока; нет агрессии, удара или преследования.
- Повторная оценка через30–60s без вмешательства в поведение.

Пользователь сохраняет screenshots локально, например
`runtime/stage10_11/screenshots/`; это отдельное доказательство рендера.
Faction11, visual components и entity existence не подменяют этот чек-лист.

## Риски и границы завершения

EntityId может переиспользоваться, generation/ownership нет; проверка npcId/faction
не делает delete безопасным. Поэтому нет удаления через API вообще. Lua/Python
контекст и position проверки не являются атомарной гарантией состояния мира.
Path grid приблизителен; ground water_y сообщает воду ≥1m, не любую лужу;
find_wall не покрывает все коллайдеры. Ручной осмотр обязателен.

ForceSave и ActiveNpcStateSaved сохранены; villagers registry/duplicate/persistence
могут действовать на наш clone. PlayerAlly до spawn не доказывает мирный AI.
Crash/зависание/невидимая entity и поздний spawn остаются возможны. Ручное закрытие
останавливает эксперимент, **но не доказывает удаление NPC из сохранения**.
До отдельного restore/review тестовый мир считается потенциально загрязнённым.
Принимается прежнее ограничение CLEAN_BASELINE_PARTIAL; scope не расширен.

## Проверки

Целевые тесты исполняют настоящий Lua controller/main через Lua5.4 mocks и Python
клиент: authorization/context/GUID/ground/path/timeouts, повтор/потеря ответа,
session change/reload, latch write/flush/close failures, no-delete, receipt/backup
gates и разделение readiness. Mocks не доказывают игровой API или рендер.
Фактически: **66 новых целевых тестов PASS; полный suite 824 testsRun / 823 PASS /
1 skip / 0 failures, 14.964s**. Прежний skip directory symlink связан с WinError1314;
права не менялись. Compileall и diff check PASS, package7/7 hash/size/source match PASS.
Результаты записаны в TEST_RESULTS.md и tests.json рядом с manifest.
Первый игровой spawn НЕ выполнялся.

Следующий шаг — отдельное разрешение на verified LOCAL backup и установку семи
файлов. Разрешение на сам spawn запрашивается отдельно непосредственно перед попыткой.
