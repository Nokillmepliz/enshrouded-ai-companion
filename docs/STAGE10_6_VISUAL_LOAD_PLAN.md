# Stage 10.6 — план visual load-only проверки

Дата: 2026-11-01. Текущий checkpoint: **PHASE_B_STOPPED; PHASE_C_BLOCKED**.

## Подтверждено офлайн

- Игра не запущена. Хеши build 1273043 повторно совпали: EXE `d64966e…`, KFC `54a8cb7…`, resources `53786c4…`, EMF loader `53b3f6e…`.
- После отката отсутствуют `dbghelp.dll`, каталог `eml`, observer и старый export. Конфликтующей установки EML нет.
- Реальный dry-run preflight: `PREPARATION_READY`; свободно 434 611 761 152 байта при расчётной потребности 1 297 670 144 байта. Единственный штатный blocker — `verified_backup_missing`.
- Patch 0.3.0 экспортирует evidence v3 и не содержит spawn/entity command.
- Observer 0.2.0 выключен по умолчанию, read-only, имеет предел 1023 байта.
- Полный source baseline содержит 18 preset paths, 35 подтверждённых RenderModel с gender overrides и общий hierarchy `87b29df6…` / 102 joints.

## Часть B — выполнена

Verified backup создан и проверен; девять файлов установлены по plan; новый run token и complete receipt созданы; post-install hashes и rollback dry-run подтверждены. Дополнительная проверка обнаружила stale README 0.2.0 при фактическом patch 0.3.0, поэтому дальнейшая установка остановлена. Игра не запускалась. См. [отчёт Phase B](STAGE10_6_PHASE_B_REPORT.md).

## Часть C — только после ещё одного разрешения

Пользователь запускает игру вручную, открывает главное меню и LOCAL test world. Spawn, console mutation и NPC-команды запрещены. Codex читает только EML/EMF logs, evidence v3, observer `status/inspect/compare`, bridge diagnostics и hashes. После закрытия игры выполняется post-run integrity review.

Порядок evaluator: A → V → B → C. Кратковременная загрузка ресурса не считается render proof. Даже `LOAD_ONLY_SUCCESS` оставляет `RUNTIME_RENDER_CONFIRMED=UNKNOWN` и `spawn_ready=false`.

## Rollback

Rollback использует новый verified manifest и install receipt. Удаляются только файлы, чьи post-install hashes совпадают с receipt; заменённые файлы восстанавливаются только из verified backup. Неизвестное изменение, работающая игра, mismatch или новый неатрибутированный DAT останавливают откат. Затем повторно сверяются KFC/resources, исходные DAT, LOCAL saves и отсутствие temp/export/cache.

## Блокеры до части C

- установленный README не соответствует patch 0.3.0; исправленный файл подготовлен только в репозитории;
- требуется отдельное разрешение на исправление установленного plan/receipt;
- отдельного разрешения на ручной load-only запуск нет;
- runtime writer/registry acceptance, collision и clone evidence не проверены до Phase C.
