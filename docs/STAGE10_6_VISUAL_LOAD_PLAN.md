# Stage 10.6 — план visual load-only проверки

Дата: 2026-11-01. Текущий checkpoint: **PHASE_B_COMPLETE; READY_FOR_PHASE_C_REVIEW**.

## Подтверждено офлайн

- Игра не запущена. Хеши build 1273043 повторно совпали: EXE `d64966e…`, KFC `54a8cb7…`, resources `53786c4…`, EMF loader `53b3f6e…`.
- EML, patch 0.3.0 и observer 0.2.0 установлены по исправленному plan; новый receipt `complete`, hashes совпали 9/9.
- Preflight перед повторной установкой вернул `PREPARATION_READY`; verified backup и rollback readiness подтверждены.
- Patch 0.3.0 экспортирует evidence v3 и не содержит spawn/entity command.
- Observer 0.2.0 выключен по умолчанию, read-only, имеет предел 1023 байта.
- Полный source baseline содержит 18 preset paths, 35 подтверждённых RenderModel с gender overrides и общий hierarchy `87b29df6…` / 102 joints.

## Часть B — выполнена

Verified backup создан и проверен. После обнаружения stale README выполнены отдельно разрешённые полный rollback и повторная установка исправленного plan. Новый run token и отдельный complete receipt созданы; post-install hashes и rollback dry-run подтверждены 9/9. DAT 55/55 и LOCAL saves 22/22 совпали с baseline. Игра не запускалась. См. [remediation report](STAGE10_6_REMEDIATION_REPORT.md).

## Часть C — только после ещё одного разрешения

Пользователь запускает игру вручную, открывает главное меню и LOCAL test world. Spawn, console mutation и NPC-команды запрещены. Codex читает только EML/EMF logs, evidence v3, observer `status/inspect/compare`, bridge diagnostics и hashes. После закрытия игры выполняется post-run integrity review.

Порядок evaluator: A → V → B → C. Кратковременная загрузка ресурса не считается render proof. Даже `LOAD_ONLY_SUCCESS` оставляет `RUNTIME_RENDER_CONFIRMED=UNKNOWN` и `spawn_ready=false`.

## Rollback

Rollback использует новый verified manifest и install receipt. Удаляются только файлы, чьи post-install hashes совпадают с receipt; заменённые файлы восстанавливаются только из verified backup. Неизвестное изменение, работающая игра, mismatch или новый неатрибутированный DAT останавливают откат. Затем повторно сверяются KFC/resources, исходные DAT, LOCAL saves и отсутствие temp/export/cache.

## Условия до части C

- отдельного разрешения на ручной load-only запуск нет;
- runtime writer/registry acceptance, collision и clone evidence невозможно подтвердить до Phase C;
- spawn, entity mutation и NPC-команды остаются запрещены.
