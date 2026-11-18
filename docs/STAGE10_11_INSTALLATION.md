# Stage 10.11 — установка aic_first_spawn 0.1.0

2026-11-18. Пользователь отдельно разрешил backup 23 LOCAL-файлов, установку
семи новых файлов, receipt, проверки и removal dry-run. Body Test / AI Body Test
подтверждены как тестовые, потеря прогресса после backup допустима.
**Spawn не разрешён.** Игру и сервер агент не запускал.

## Фактическая установка

Выполнена в 14:51:46 UTC (17:51:46 MSK), без ошибок и без отката.
Транзакция: [install_stage10_11.py](../scripts/install_stage10_11.py),
[exclusive-copy module](../companion/experimental_install.py).
Перед копированием выполнены отдельный read-only preflight и повторный preflight
в разрешённой транзакции: закрытые процессы, Steam build/depot/idle, package7,
installed16, отсутствие destinations, полный актуальный baseline235 game/23 LOCAL.

Сохранён исходный immutable exact manifest SHA-256:
`6ecc792b6c320dc19f0fa201259c573efd142c4c37a579eab07376dc40b9e1e3`.
Поле installation_authorized=false в историческом плане не переписывалось:
отдельное разрешение записано в transaction authorization.json и новом receipt.

В `D:\SteamLibrary\steamapps\common\Enshrouded` добавлены только:

1. `emf/mods/aic_first_spawn/mod.json`
2. `emf/mods/aic_first_spawn/main.lua`
3. `emf/mods/aic_first_spawn/controller.lua`
4. `emf/mods/aic_first_spawn/README.md`
5. `emf/mods/aic_first_spawn/binding.lua`
6. `emf/mods/aic_first_spawn/attempt.lock`
7. `emf/config/aic_first_spawn.ini`

Мод включён отдельным ini, но не содержит auto-spawn. Latch остаётся UNUSED.
Существующие моды, EMF, patch0.5.1, observer, ACL, shadow/cache и saves не изменялись.
Каждому файлу предшествует journal intent; запись эксклюзивная, с flush/fsync и
проверкой hash/size/source identity. При ошибке сохраняются журнал и частичный файл,
никакого автоматического удаления или восстановления нет.

## Verified backup

Путь: `C:\Enshrouded-ai-companion\runtime\backups\stage10_11-local-before-first-spawn`.
Источник: `C:\Users\user\Saved Games\keen games\Enshrouded`.
**23/23 файлов, 637447 bytes (≈0.61 MiB)**. Состав, SHA-256, размеры и сохранённые
source mtime проверены существующим verify_backup; источник до/после не изменился.
Проверены персонаж/мир, их backup-0…9 и local_settings.json. Полная копия игры не создавалась.

SHA-256 `manifest.json` backup:
`c88339083683e9f6ce36aa2ab2fceb4bebcf9bdfe90926630e52422463011041`.
Существующие backup/quarantine сохранены. Этот backup не означает разрешения на restore.

## Receipt и целостность

[Installation receipt](../compatibility/experiments/stage10_11/installation/receipt.json), SHA-256:
`3b9d80c0ade318c378584e38809eda54d6c4bc689ef16f1a5af28e5a993fd950`.

[Результат установки](../compatibility/experiments/stage10_11/installation/result.json), SHA-256:
`dd82da3dd998d9f0ee95d229ebcb18967dffdaa0cad8beaa811db95ec2e9d9f1`.

- Новые7 и прежние16 installed files прошли проверку: effective set23.
- Все235 существующих game records совпали по SHA/size/identity/mtime/links.
- Original resources67, shadow77 и LOCAL23 не изменились.
- Game inventory теперь242: ровно235+7, неизвестных additions/removals нет.
- Новый post-install baseline SHA:
  `5f200502df076c1d2c81d126b4f6db5d10e9010f8f32cd682eb09b8117c1175a`.
- Private evidence: `runtime/stage10_11/install/20261118T145106436795Z`.

[Removal dry-run](../compatibility/experiments/stage10_11/installation/removal-dry-run.json):
**PASS7**, ничего не удалено. Проверены точные records семи файлов из receipt.
План не включает каталоги рекурсивно, неизвестные файлы, старые16, resources,
shadow/cache или LOCAL. После изменения latch/spawn этот dry-run устаревает:
нужен новый review, а не сброс latch или прежний rollback.

## Preflight и следующий ручной запуск

Отдельный [preflight_stage10_11.py](../scripts/preflight_stage10_11.py) только читает:
receipt/pins, backup23, installed23, UNUSED latch, отсутствие журнала предыдущей
попытки, closed/build/Steam, полный post-install baseline и имена LOCAL-пары.
Он не подключается к Bridge, не вызывает probe/spawn и не создаёт authorization.

Свежий preflight **READY_FOR_MANUAL_START**, 14:52:38 UTC (17:52:38 MSK):
installed23/backup23/removal dry-run PASS, полный inventory242 game/23 LOCAL точно
совпал с post-install baseline, latch UNUSED, имена Body Test / AI Body Test подтверждены.
[Preflight evidence](../compatibility/experiments/stage10_11/installation/preflight/20261118T145238316160Z.json).
Runtime slot/storage/session ещё предстоит проверить через Bridge после загрузки.

Для повторной проверки перед новым запуском:

```powershell
.\.tools\python\python.exe scripts/preflight_stage10_11.py `
  --installation-result-sha256 dd82da3dd998d9f0ee95d229ebcb18967dffdaa0cad8beaa811db95ec2e9d9f1
```

После READY_FOR_MANUAL_START пользователь может вручную загрузить **LOCAL Body Test /
AI Body Test, slot1**, выбрать открытое сухое ровное место и сообщить «загрузился».
Пока не вводить spawn-команды. Далее — только проверка Bridge/LOCAL/mod/session
контекста; ground/path probe не создаёт NPC. Непосредственно перед созданием всё равно
нужно отдельное разрешение пользователя и подтверждение места в пределах20s окна.

Для будущего клиента параметры receipt уже определены:

```text
--package C:\Enshrouded-ai-companion\dist\stage10_11_first_spawn_0_1_0
--manifest-sha256 6ecc792b6c320dc19f0fa201259c573efd142c4c37a579eab07376dc40b9e1e3
--receipt C:\Enshrouded-ai-companion\compatibility\experiments\stage10_11\installation\receipt.json
--receipt-sha256 3b9d80c0ade318c378584e38809eda54d6c4bc689ef16f1a5af28e5a993fd950
```

PID будет определён только после ручного запуска. Binding key не публикуется.
См. [план эксперимента](STAGE10_11_REPORT.md) для чек-листа, 30–60s наблюдения,
остановки и отдельно согласуемого восстановления saves. Закрытие игры само по себе
не доказывает исчезновение persistent NPC.

## Тесты и ограничения

Перед установкой выполнено **833 testsRun / 832 PASS / 1 skip / 0 failures**,15.986s.
Девять новых тестов транзакции проверяют authorization, collisions, изменённый source,
неизвестный path, live guard, partial write без rollback и changed-file removal refusal.
Прежний skip directory symlink — WinError1314; права не менялись.
Py_compile новых модулей/скриптов и git diff check PASS.
[Machine test report](../compatibility/experiments/stage10_11/install-tests.json).

Runtime загрузка нового мода, фактический spawn, внешность/поведение и cleanup
ещё не проверены. Сохраняются риски ForceSave/villagers, reuse EntityId и ограничения
ground/path; production readiness не следует из успешной установки.

```text
spawn_authorized=false
experimental_spawn_executed=false
production_spawn_ready=false
spawn_ready=false
RUNTIME_RENDER_CONFIRMED=UNKNOWN
```
