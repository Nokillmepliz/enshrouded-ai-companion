# Stage10.10.2 — patch0.5.1 установлен

2026-11-18. **READY_FOR_REPEAT_LOAD_ONLY_APPROVAL**.

- Генератор использует `.as_posix()`. Исходный план сохранён; новый
  [backup-plan-revision-2.json](../compatibility/updates/1287369/0.5.1/backup-plan-revision-2.json)
  закреплён SHA-256 `6b55956af459d8d3d82daa6c383740a4517a12e689d013ad3716271a2b05208a`.
  Игровой payload и exact update manifest не изменялись.
- До создания каталога и копирования проверяются все38 путей, группы, дубликаты без
  учёта регистра, ограничения containment/links, общий размер и SHA/размер источников.
  Прежние проверки каждой копии сохранены; валидаторы не ослаблены.
- Partial37 повторно прошёл проверку точного состава, SHA и размеров. Первоначальный
  диагностический glob ошибочно включил каталог `.cache` как38-й объект; остановка
  произошла до установки. Read-only проверка только файлов подтвердила37/37.
  Manifest отсутствует, а контракт запрещает resume существующего каталога:
  partial сохранён, создан новый backup38.
- Полный preflight: игра/server закрыты, build1287369/Steam26430625 прежний;
  pinned inputs/current16/clean backup27 PASS. Полный baseline222 game/23 LOCAL
  совпал, включая67 originals/66 shadow; старый fingerprint подтверждён.
- Новый verified backup38, **247154745 bytes**, проверен до и после обновления:
  `runtime/backups/stage10_10_2-patch-0.5.1-20261118T133801929065Z`.
  Manifest SHA-256: `eb7d81b857650c34f9f46d5040e21a033722fb5394b20e0fa4565c0eacc51208`.
- Заменены только `emf/mods/aic_integrated_observer/binding.lua`,
  `mods/aic_eml_humanoid/README.md`, `mods/aic_eml_humanoid/mod.json`,
  `mods/aic_eml_humanoid/src/mod.lua`. Все16 effective hashes PASS.
- Фактический fingerprint совпал с планом:
  `sha256:17d1f36bb57e8dd9fc064eee5402ed4f10365d9970bda8fa975e7156638f1138`.
- Post-update:218 остальных game records неизменны по SHA/размеру/mtime/identity/links;
  в том числе67 originals и66 shadow. Все23 LOCAL records также неизменны.
  Старый receipt, backup/quarantine и partial37 сохранены.
- Новый [receipt](../compatibility/updates/1287369/0.5.1/installation/receipt.json)
  SHA-256 `8fa2fa02ef0ad12b5c3c00864c0e81f21803fc2851872a708dea4e4d8efd2053`
  содержит revision2/pinned hash и ссылку на immutable journal.
- [Rollback dry-run](../compatibility/updates/1287369/0.5.1/installation/rollback-dry-run.json)
  PASS для4 файлов. Откат не выполнялся; `full_live_rollback_ready=false`:
  это не разрешение на очистку shadow или восстановление сохранений.

[Машиночитаемый результат](../compatibility/updates/1287369/0.5.1/installation/result.json).

Полный suite: **729 testsRun /728 PASS /1 skip /0 failures**,15.748s,exit0.
Добавлены8 regression tests: некорректный38-й path/hash без создания каталога/копий,
успешные38, duplicate casefold, неизвестная группа, неверный total, запрет resume,
реальный revision2 manifest и POSIX генерация. Py_compile и diff check PASS.
Лог: `runtime/stage10_10_2/revision2-tests.log`.

Игра/server не запускались; spawn и игровые мутации не выполнялись.
Shadow/cache вручную не очищались. Сохранён failed0.5.0 state; штатная пересборка EMF
с новым fingerprint, исправление graph, writer, evidence8 и rendering ещё не проверены.
`runtime_validation=NOT_EXECUTED`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, **spawn_ready=false**.
Следующий шаг — отдельное разрешение на повторный load-only тест, затем новый read-only
preflight перед ручным запуском пользователем.

---

# История: предыдущая установка0.5.1 остановлена на backup

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
