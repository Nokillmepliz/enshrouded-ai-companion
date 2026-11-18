# Stage10.10.2 — разрешённая установка0.5.1: остановка на backup

**BLOCKED_BACKUP_PLAN_PATH**, 2026-11-18. Установлен patch **0.5.0**.
Обновление0.5.1 не начиналось. Повторный load-only тест пока не готов.

Пользователь разрешил verified backup38 и замену4 файлов exact manifest, без игры,
spawn, ручной очистки shadow/cache и automatic rollback. При ошибке предписано остановиться.

## Фактическая последовательность

1. Проверены закрытые game/server, прежний build, pinned package/profile/binding,
   parent receipt и16 current installed hashes.
2. Полный baseline222 game/23 LOCAL точно совпал с post-close snapshot, включая67
   original resources и66 shadow. Старый fingerprint совпал; clean backup27 проверен.
3. Создан новый отдельный каталог backup. Скопированы37 из38 файлов, после чего
   валидатор отказал на последнем path **до начала replacement transaction**.
4. Операция остановлена с `INVALID_PATH`; retry/rollback/cleanup не выполнялись.
   Повторно проверены16 старых installed hashes и SHA/размер37 скопированных файлов.
   Нет journal replacements, нового update receipt и backup manifest.

Ошибка находится в ранее согласованном [backup-plan.json](../compatibility/updates/1287369/0.5.1/backup-plan.json):

```text
group: project
path: compatibility\migration\1287369\phase_e\install-receipt.json
```

`recovery.target` принимает только безопасные относительные пути с `/`.
Источник ошибки — генератор плана использовал Windows `str(relative_path)` для этого
единственного project entry, тогда как game/LOCAL entries уже использовали `/`.
План не исправлялся задним числом, валидатор не ослаблялся. Это ошибка подготовки
backup plan, а не антивирус, отказ прав или несовпадение содержимого backup.

## Состояние после остановки

Run:
`C:\Enshrouded-ai-companion\runtime\stage10_10_2\install\20261118T132845581508Z`.

Частичный backup сохранён:
`C:\Enshrouded-ai-companion\runtime\backups\stage10_10_2-patch-0.5.1-20261118T132845581508Z`.

- **37 файлов /247144644 bytes**, SHA-256 и размеры37/37 совпадают с планом.
  Не скопирован только старый receipt10101 bytes. Это **не завершённый verified backup38**.
- Файлы игры не заменялись: **0/4**. Старые16 hashes подтверждены.
- Повторный полный аудит после остановки (13:30:51 UTC): **222 game/23 LOCAL**
  records совпали с before, включая67 original resources и66 shadow. Проверены
  SHA/размер/mtime/file identity/link counts, а не только отсутствие вызовов записи.
- Игра/server не запускались; NPC/Bridge mutations/rollback не выполнялись.
- Shadow/cache не очищались; старый failed0.5.0 state сохранён.
- Старые backups/quarantines и immutable receipt сохранены.
- Новый fingerprint не применяется, поскольку пакет0.5.1 не установлен.
- Update rollback dry-run не применим к выполненной установке: выполненной установки нет.
  Исторический успешный fixture dry-run не выдаётся за live dry-run.

[Машиночитаемый итог и post-stop audit](../compatibility/updates/1287369/0.5.1/installation-attempt/result.json).
Результат повторной полной проверки неизменности game/LOCAL фиксируется в этом файле;
копии before/after остаются в private run directory, без публикации save payload.

## Проверки кода

Исполнитель [`install_patch_0_5_1.py`](../scripts/install_patch_0_5_1.py) использует
новый [`patch_update_transaction.py`](../companion/patch_update_transaction.py):
exclusive backup, fsync, pinned inputs, temporary private files, immutable per-file
intent/verified journal, SHA/mtime/identity проверки, остановка без rollback.
Receipt допускается только после post-integrity. Реальная ошибка возникла раньше замен.

7 новых transaction fixtures PASS, полный suite **721 testsRun /720 PASS /1 existing skip**,
0 failures,12.549s,exit0. Py_compile PASS. Эти тесты не покрыли Windows separator в
конкретном38-entry backup manifest; реальные проверки обоснованно остановили исполнение.
Никакого успешного игрового испытания или обновления из результатов unit tests не следует.

## Что нужно дальше

Исправить генерацию project-relative path на `.as_posix()`, подготовить отдельную
reviewed revision backup plan и её pinned hash; добавить регрессию для всех38 paths
до создания копий. Сохранить текущий partial backup. После согласования повторить
полный preflight и создать новый verified backup, затем update4/receipt/dry-run.
В этом запуске эти исправления и повторная попытка **не выполнялись** согласно условию
остановки при ошибке. Игровые payloads и их exact update manifest менять не требуется.

`runtime_validation=NOT_EXECUTED`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.
