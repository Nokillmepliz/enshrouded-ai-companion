# Stage 10.6 — runtime results

Дата: 2026-11-01.

Статус runtime: **EXECUTED**. Verdict: **FAILED — V:CHARACTER_SETUP**.

| Уровень | Результат |
|---|---|
| A — EML patch/resource/writer | PASS |
| V — clone visual evidence | FAIL |
| B — menu/LOCAL world/integrity | PASS |
| C — EMF/observer/bridge | PASS |

`load_only_success=false`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.

Patch 0.3.0 применён, source/clone structure, animation graph, retarget и canonical set из 18 visual references совпали. Девять `HashKey32` полей `CharacterSetup` имеют статус `UNSUPPORTED` и пустые values, поэтому typed visual acceptance не пройден.

Bridge подтвердил LOCAL `Body Test` slot 1 / `AI Body Test` slot 1. Observer `status/inspect/compare` отработал read-only с совпадающим token/fingerprint. NPC не создавался, игровые команды мутации не выполнялись.

Post-run integrity: backup 24/24, install hashes 9/9, исходные DAT 55/55; добавлены только нулевые DAT `055–063`, штатно изменены шесть файлов изолированного LOCAL-профиля. Unknown changes: 0. Rollback ready, но rollback не выполнялся.

Подробный разбор визуальных зависимостей, регистрации и ограничений: [STAGE10_6_PHASE_C_REPORT.md](STAGE10_6_PHASE_C_REPORT.md).
