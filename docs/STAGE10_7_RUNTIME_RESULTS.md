# Stage 10.7 — runtime results

**LOAD_ONLY_SUCCESS**

Контролируемый Phase C выполнен 2026-11-01 в LOCAL-персонаже `Body Test` (slot 1) и LOCAL-мире `AI Body Test` (slot 1). Enshrouded запускал и закрывал пользователь. Codex выполнял только read-only запросы Bridge/observer и чтение evidence/logs. Spawn, создание NPC, faction, inventory, entity mutations и rollback не выполнялись.

| Gate | Результат | Подтверждение |
|---|---|---|
| A — patch | PASS | evidence v4, GUID, `npcId`, faction, source, run token и завершение writer согласованы. |
| H — HashKey32 | PASS | Все 9 полей source/clone имеют `CONFIRMED`, точные UInt32 совпадают, provenance получен через EML reflection. |
| R — registration/lookup | PASS | Resource создан и сериализован; read-only `EML_ASSET_MANAGER_GET_RESOURCE` вернул ожидаемые GUID, тип, 81 компонент и fingerprint. |
| V — visual clone | PASS | Структура, `CharacterSetup`, animation graph, visual references и dependencies совпадают. |
| B — game/integrity | PASS | Нужный LOCAL-мир загружен; post-run source integrity подтверждена. |
| C — EMF runtime | PASS | Bridge и все три observer-команды доступны, ответы полны и имеют safety flags. |

`RUNTIME_RENDER_CONFIRMED=UNKNOWN`: entity не создавалась, поэтому фактическое отображение модели, материалов, skeleton и анимации на экране не проверялось. Результат не является разрешением на spawn; `spawn_ready=false`.

Подробности, хеши и оставшиеся ограничения: [Stage 10.7 Phase C report](STAGE10_7_PHASE_C_REPORT.md).
