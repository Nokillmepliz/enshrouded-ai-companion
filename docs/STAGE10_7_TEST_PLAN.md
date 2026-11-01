# Stage 10.7 — план проверки

## Phase A — выполнено

Проверить uint32 boundary/nil/type/provenance, девять source/clone полей, mismatch и fail-closed статусы; create/registry/lookup identity; duplicate GUID/key, source mutation, stale token, writer; v3 compatibility, v4 validation, независимые A/H/R/V/B/C, observer limit/read-only и отсутствие mutation/launcher кода. Синтетический PASS не является runtime evidence.

## Phase B — выполнено 2026-11-01

1. Убедиться, что игра/server закрыты; проверить текущий receipt, 9 installed hashes и attribution KFC/DAT/saves.
2. Проверить verified backup и штатный rollback dry-run.
3. Штатно откатить только атрибутированные файлы; восстановить KFC/resources; проверить clean baseline и LOCAL differences.
4. Сформировать новый plan для patch 0.4.0/observer, новый token и receipt; установить только план; проверить hashes и rollback dry-run.
5. Остановиться до ручного запуска.

Все пять шагов выполнены; результаты и hashes приведены в [Phase B report](STAGE10_7_PHASE_B_REPORT.md). LOCAL saves не восстанавливались.

## Будущая Phase C — отдельное разрешение

Пользователь вручную запускает только LOCAL `Body Test` / `AI Body Test`. Codex собирает read-only evidence v4 и проверяет A/H/R/V/B/C. Никаких spawn/entity/faction/inventory действий. После закрытия повторяется integrity. Минимальный эксперимент подтверждает девять runtime values и EML lookup после writer/reload; `spawn_ready=false`.
