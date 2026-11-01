# Stage 10.9 — offline test plan

Phase A использует только Python mocks/fixtures и статические проверки. Успех mocks не доказывает свойства движка.

## Покрытие

- Identity: generation same/changed/missing, reused ID, changed session, missing/forged marker, unknown ownership, ambiguity и non-atomic destroy.
- Position: valid, no ground, wall/normal, cliff/height, unwalkable, danger, wrong world, unavailable collision, unknown geometry/hostile distance и provenance.
- Persistence: ForceSave present/absent, ActiveNpcStateSaved, unique collision, reload duplicate, restore after destroy, unknown evidence и backup gate.
- Faction: template PlayerAlly не повышается до runtime CONFIRMED; hostile/dynamic mismatch, combat/AI unknown; `NOT_APPLICABLE` требует доказательства.
- Destroy: exact identity, reused/foreign/stale entity, accepted-but-present, timeout, reappearance, crash, три и менее трёх absent ticks.
- Regression: Stage 10.7 evaluator, Stage 10.8 blocked verdict, восемь gates, no Python runtime process/mutation path.
- Full suite, `compileall`, Lua syntax, `git diff --check`, tracked-file audit.

## Acceptance

Все 54 Stage 10.9 tests и весь прежний suite должны пройти. Единственный допустимый skip — ранее документированный Windows directory-symlink privilege test. Lua проверяется доступным parser/compiler из проекта. В repository не должны попасть DLL/EXE, KFC/DAT/KSD, runtime dump, private token или secret.

Expected verdict: `NATIVE_EXTENSION_REQUIRED` и `BLOCKED_FOR_SPAWN`; `NOT_EXECUTED`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.
