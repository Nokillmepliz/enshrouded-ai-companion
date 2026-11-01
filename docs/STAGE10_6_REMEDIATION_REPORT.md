# Stage 10.6 — Phase B README remediation audit

Дата: 2026-11-01. Вердикт: **BLOCKED_NO_SAFE_RECEIPT_UPDATE_MECHANISM**.

## Разрешённая операция

Пользователь разрешил заменить только установленный `mods/aic_eml_humanoid/README.md` исправленной repository-версией при условии, что штатный механизм умеет безопасно обновить install plan/receipt, сохранить историю и hashes до/после. При отсутствии такого механизма требовалось остановиться без ручного редактирования receipt.

## Проверки до изменения

- `Enshrouded` и `enshrouded_server`: **NOT_RUNNING**.
- Verified backup `stage10-6-pre-eml-20261101T083034Z`: **PASS**, 24 файла.
- Install receipt: `state=complete`, 9 записей.
- Все 9/9 установленных файлов совпадают с SHA-256 текущего receipt.
- Установленный README SHA-256: `3a2a12ac7adb67e4e8981d615596842dada06f050f3d6542d7cae39aa9db7b1b`.
- Исправленный repository README SHA-256: `bf5fdc8b24718e4522a29187bc7312472f49001153deb8f0a42c9d76162da28b`.
- Rollback dry-run: **PASS**, все девять путей распознаны и removable.

## Проверка штатного механизма

Текущий `companion.stage10.install()` создаёт только первичный receipt. Он требует отсутствия каждого destination, прекращает dry-run на первом существующем файле, запрещает существующий receipt при apply и не имеет revision/history/update операции для одного файла.

```text
preflight: conflicting_or_repeated_dbghelp_install
install dry-run: installation_collision:dbghelp.dll
```

`rollback_added_files()` умеет удалить весь набор из receipt, но не обновляет один файл и не создаёт цепочку ревизий.

## Выполненные изменения

Игровые файлы: **0**. Installed README, Lua, DLL, JSON, KFC, DAT, saves и receipt не изменялись. Ручное редактирование receipt не выполнялось. Игра не запускалась, NPC не создавался.

## Следующий безопасный шаг

Phase C **не готова**. Нужен отдельный этап: реализовать и протестировать атомарный receipt-revision механизм либо отдельно разрешить полный rollback девяти файлов и повторную установку из исправленного plan. До этого статус остаётся `BLOCKED_NO_SAFE_RECEIPT_UPDATE_MECHANISM`.
