# Stage 10.11.3 — установка aic_first_spawn 0.1.1

2026-11-18. **INSTALLED_VERIFIED**. Выполнена отдельно разрешённая установка; игра/сервер не запускались, Bridge/probe/spawn не выполнялись.

Свежий closed preflight подтвердил Steam build26430625/game1287369, отсутствие запущенной игры/сервера, baseline245 game/23LOCAL, установленные23 файла, payload4, историю75 и UNUSED latch. Использован согласованный exact manifest SHA-256 `52a54fb2fa446df5d83527407ed3faf795739f0dae5f3dd2f66698c67a3310c9`.

## Выполнено

- Создан новый backup **27/27 файлов, 650492 байта**: LOCAL23 и четыре прежних файла мода. SHA-256, состав и сохранённые metadata проверены штатным verified_backup; исходные saves не изменялись.
- Backup: `C:\Enshrouded-ai-companion\runtime\backups\stage10_11_3-before-update`. SHA-256 `manifest.json`: `7d445cf14a2c7cb8158304de47de5be4d6fdb25e39583ea662d81389e155cb6c`.
- Обновлены только `README.md`, `controller.lua`, `main.lua`, `mod.json` в `D:\SteamLibrary\steamapps\common\Enshrouded\emf\mods\aic_first_spawn`. Версия **0.1.1**. Хеши соответствуют ранее согласованному manifest; игровой payload не перерабатывался.
- Проверены **23/23 effective hashes**. Остальные **241 файл игры** полностью совпали с baseline, включая исходные ресурсы, EMF, patch, Observer, Shadow Resources, binding, INI и latch. LOCAL23 и история75 неизменны. Состав каталога игры остался245 файлов, временных файлов установки не осталось.
- Создан новый [receipt](../compatibility/experiments/stage10_11_3/installation/receipt.json), SHA-256 `d973898fbd447f274fbf2365a9146d1b193a01413677d253fbcfbfc0da338485`. Старые receipts/backup/quarantine сохранены.
- Новый baseline для следующего эксперимента: `runtime/stage10_11_3/installation/inventory-after.json`, SHA-256 `0cc0a9b1564e35d8c6b8cd586baa737b49cdbf352f86a97cf3d16df09539375e`.
- [Rollback dry-run](../compatibility/experiments/stage10_11_3/installation/rollback-dry-run.json): **PASS, 4 файла**. Реальный rollback не выполнялся; saves/latch не восстанавливались.

Установщик проверяет все четыре источника до первой замены, пишет эксклюзивный журнал каждого действия, проверяет staged copy и заменяет файл атомарно. Ошибка сохраняет фактическое частичное состояние без автоматического rollback. Журнал находится в `runtime/stage10_11_3/installation` и не публикуется вместе с приватными saves/binding.

## Проверки

Пять новых тестов установщика PASS: точные четыре замены, dry-run, обязательная авторизация, проверка всего payload до записи, отказ второй замены без отката первой, сохранение неизвестного временного файла. Финальный полный suite: **952 testsRun / 951 PASS / 1 skip / 0 failures/errors**,22.084s, exit0. Skip прежний — привилегия directory symlink Windows. [Результат](../compatibility/experiments/stage10_11_3/install-tests.json). Py_compile/diff check PASS.

Runtime нового контроллера ещё **NOT RUN**. Производительность поиска, реальный humanoid render и поведение NPC остаются непроверенными. `spawn_ready=false`, `production_spawn_ready=false`; установка не является выполненным игровым испытанием.

После установки отдельно выполнен новый closed preflight: **PASS**, installed23/backup27/baseline245/23/history75/UNUSED. [Запись проверки](../compatibility/experiments/stage10_11_3/installation/closed-preflight.json).

## Следующий игровой эксперимент

Перед новым запуском выполнить closed preflight:

```powershell
& 'C:\Enshrouded-ai-companion\.tools\python\python.exe' 'C:\Enshrouded-ai-companion\scripts\preflight_stage10_11_3.py'
```

После отдельного согласования эксперимента пользователь самостоятельно запускает игру и загружает **LOCAL Body Test / AI Body Test, slot1/1**. Ниже готовая команда для обычного интерактивного PowerShell; PID берётся у уже запущенной игры. Команда не запускает Enshrouded. При отсутствии процесса или нескольких процессах не продолжать.

```powershell
& 'C:\Enshrouded-ai-companion\.tools\python\python.exe' 'C:\Enshrouded-ai-companion\scripts\smart_spawn_position.py' --plan 'C:\Enshrouded-ai-companion\runtime\stage10_11_3\smart-position-plan.json' --sha256 d137680beff2ccc68fedefd87617202075a1d367407ddd34096ae43537d6647c --receipt 'C:\Enshrouded-ai-companion\compatibility\experiments\stage10_11_3\installation\receipt.json' --receipt-sha256 d973898fbd447f274fbf2365a9146d1b193a01413677d253fbcfbfc0da338485 --pid (Get-Process -Name enshrouded -ErrorAction Stop | Select-Object -ExpandProperty Id) --interactive
```

CLI до probe проверяет установленный набор/backup, Bridge hello/state, версию0.1.1, PID и LOCAL context. Стойте неподвижно на открытом сухом месте. **Не нажимайте Y заранее.** После READY посмотрите координаты: свежая **Y без Enter** разрешает одно создание и принимает риск для тестового мира; **N/ESC** отменяют. Просрочка отменяет попытку. Если нужно только проверить поиск, заменить `--interactive` на `--search-only`.

После ошибки не запускать команду вслепую. Новая ручная попытка поиска допустима только после подтверждённого закрытия предыдущей истории, при UNUSED latch и отсутствии durable intent; незавершённая очередь требует предусмотренного `--settle-only`, а неоднозначный spawn запрещает повтор. Подробный контракт — [Stage 10.11.3](STAGE10_11_3.md).

После появления NPC — визуальная проверка и read-only наблюдение30–60с. Пользователь закрывает игру самостоятельно; post-close audit использует новый baseline `0cc0a9…`, сохраняет все AIC_POSITION записи/журналы и проверяет ресурсы, файлы установки, latch и LOCAL. Автоматические destroy/rollback и изменения saves не разрешены.
