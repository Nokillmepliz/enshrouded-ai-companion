# Stage 10.10.1 — recovery plan (2026-11-18)

Ниже исторический план Phase A. Актуальное состояние: limited Phase B завершена;
идёт read-only Phase C/D, [новый отчёт](STAGE10_10_1_PHASE_C_REPORT.md).
Старый manifest нельзя повторно выполнять после перемещения81 файлов.

Выполняется только Phase A. Исходный HEAD: `7d45464b3ded5e03e8a6a636e03a96171ceb81ce`.
Игра: `D:\SteamLibrary\steamapps\common\Enshrouded`.
LOCAL: `C:\Users\user\Saved Games\keen games\Enshrouded`.

Свежий read-only inventory содержит 249 игровых и 23 LOCAL-файла. EXE SHA соответствует profile1287369; Steam build26430625, depot1203621 manifest7226436020230696061 повторно прочитаны из manifest. Никаких вызовов Bridge/game runtime не было.

| Фаза | Действия | Разрешение / результат |
|---|---|---|
| A | Manifest, инструменты, fixtures, upstream research | Текущая задача |
| B | Новый проверенный backup; карантин только подтверждённых файлов | Нужно отдельное разрешение; unknown остаются на месте |
| C | Steam Verify вручную; затем read-only audit | Пользователь запускает Verify отдельно |
| D | Clean resource fingerprints, patch0.5, observer, evidence | Только после достаточного clean-baseline evidence |
| E | Установка единственного content owner | Новое разрешение и install plan |
| F | Load-only; пользователь запускает игру | Новое разрешение; spawn запрещён |

Вердикт: **BLOCKED_BY_UNKNOWN_ARTIFACTS** для полной очистки, **BLOCKED_BY_GAME_BASELINE** для миграции. Точный ограниченный план карантина 81 файла подготовлен, но не выполнен. `MANUAL_REVIEW` не означает «удалить вручную». Исторический rollback1273043 не применяется.

Инструменты: [inventory](../scripts/stage10_10_1_inventory.py), [recovery CLI](../scripts/stage10_10_1_recovery.py), [контракты](../companion/recovery.py). CLI по умолчанию dry-run. Ошибка оставляет исходные/уже скопированные файлы и журнал; автоматического продолжения либо обратного восстановления нет. Перед будущими операциями требуется остановить Steam downloads/Verify, редакторы модов и другие writers. Проверки пути и хешей не являются защитой от привилегированного процесса, меняющего файл в промежутке между проверкой и unlink.

Зависимые документы: [manifest](STAGE10_10_1_CLEANUP_MANIFEST.md), [backup](STAGE10_10_1_BACKUP_STRATEGY.md), [Steam](STAGE10_10_1_STEAM_VERIFY_PLAN.md), [baseline](STAGE10_10_1_CLEAN_BASELINE_CONTRACT.md).

`cleanup_executed=false`, `clean_baseline_confirmed=false`, `installation_ready=false`, `runtime_status=NOT_EXECUTED`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.
