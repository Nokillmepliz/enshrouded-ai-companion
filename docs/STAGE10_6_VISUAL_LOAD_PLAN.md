# Stage 10.6 — план visual load-only проверки

Дата: 2026-11-01. Текущий checkpoint: **PHASE_A_COMPLETE; PHASE_B_NOT_AUTHORIZED**.

## Подтверждено офлайн

- Игра не запущена. Хеши build 1273043 повторно совпали: EXE `d64966e…`, KFC `54a8cb7…`, resources `53786c4…`, EMF loader `53b3f6e…`.
- После отката отсутствуют `dbghelp.dll`, каталог `eml`, observer и старый export. Конфликтующей установки EML нет.
- Реальный dry-run preflight: `PREPARATION_READY`; свободно 434 611 761 152 байта при расчётной потребности 1 297 670 144 байта. Единственный штатный blocker — `verified_backup_missing`.
- Patch 0.3.0 экспортирует evidence v3 и не содержит spawn/entity command.
- Observer 0.2.0 выключен по умолчанию, read-only, имеет предел 1023 байта.
- Полный source baseline содержит 18 preset paths, 35 подтверждённых RenderModel с gender overrides и общий hierarchy `87b29df6…` / 102 joints.

## Часть B — только после отдельного разрешения

1. Убедиться, что Enshrouded закрыт.
2. Создать новый backup KFC, KFC resources, LOCAL saves и всех заменяемых/добавляемых путей; проверить SHA-256 копий и исходников.
3. Повторить exact hashes, stale evidence/collision/conflict checks и проверить достаточное место.
4. Установить только проверенный EML `dbghelp.dll`, EML runtime, patch 0.3.0 и observer 0.2.0 с новым случайным run token.
5. Не запускать игру. Проверить receipt, hashes, отсутствие placeholder, права чтения и готовность rollback.
6. Остановиться и представить post-install отчёт.

## Часть C — только после ещё одного разрешения

Пользователь запускает игру вручную, открывает главное меню и LOCAL test world. Spawn, console mutation и NPC-команды запрещены. Codex читает только EML/EMF logs, evidence v3, observer `status/inspect/compare`, bridge diagnostics и hashes. После закрытия игры выполняется post-run integrity review.

Порядок evaluator: A → V → B → C. Кратковременная загрузка ресурса не считается render proof. Даже `LOAD_ONLY_SUCCESS` оставляет `RUNTIME_RENDER_CONFIRMED=UNKNOWN` и `spawn_ready=false`.

## Rollback

Rollback использует новый verified manifest и install receipt. Удаляются только файлы, чьи post-install hashes совпадают с receipt; заменённые файлы восстанавливаются только из verified backup. Неизвестное изменение, работающая игра, mismatch или новый неатрибутированный DAT останавливают откат. Затем повторно сверяются KFC/resources, исходные DAT, LOCAL saves и отсутствие temp/export/cache.

## Блокеры до части B

- отдельного разрешения на backup/install нет;
- новый verified backup ещё не создан;
- runtime writer/registry acceptance, collision и clone evidence не проверены;
- новый verified backup ещё не создан; поэтому `installation_ready=false`, `rollback_ready=false` и `phase_b_allowed=false`.
