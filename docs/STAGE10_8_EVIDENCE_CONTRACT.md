# Stage 10.8 — evidence v5 contract

Формат: `aic_humanoid_spawn_evidence_v5`. Валидатор находится в [safe_spawn.py](../companion/safe_spawn.py). Phase A создаёт только схему и synthetic fixtures; runtime evidence отсутствует.

Общие поля: 32-hex run token, build, template GUID и template fingerprint. Один новый token связывает все пять разделов:

1. `PRE_SPAWN`: character/world identity, точный spawn method, safety verdict, faction verification, position validation, persistence status.
2. `SPAWN_RESULT`: handle, полный entity identity, failure reason. `0`/nil/exception — `UNKNOWN`, не «не создано».
3. `RENDER_OBSERVATION`: `ENTITY_CREATED`, `ENTITY_IDENTITY_CONFIRMED`, `MODEL_LOADED`, `SKELETON_CONFIRMED`, `ANIMATION_CONFIRMED`, `RUNTIME_RENDER_CONFIRMED`.
4. `DESPAWN_RESULT`: method, acceptance отдельно от verified absence, recovery status.
5. `POST_RUN_INTEGRITY`: KFC/resources, DAT, LOCAL saves, receipt, backup и source integrity.

Каждый verdict имеет `CONFIRMED`, `FAILED`, `UNKNOWN` или `NOT_EXECUTED` и provenance. `RUNTIME_RENDER_CONFIRMED` требует визуального наблюдения пользователем вместе с согласованной identity/diagnostics. Логи сами по себе недостаточны. Существование entity не подтверждает model/skeleton/animation.

Evidence хранится в ignored runtime-каталоге. В Git разрешены только обезличенные итоги: `public_evidence` удаляет run token, character/world identity и entity handle. Отсутствие ошибок не повышает статус despawn. `spawn_ready` не является полем, выводимым из частичного evidence; до отдельного разрешения он всегда false.
