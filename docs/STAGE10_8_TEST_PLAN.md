# Stage 10.8 — test plan

## Phase A

Обязательные 50 сценариев из ТЗ реализованы в [test_stage10_8.py](../tests/test_stage10_8.py): game/template/context failures; faction/ownership/position/despawn/persistence blockers; confirmation, duplicate/reconnect/reload lockout; handle/GUID mismatch; timeout/crash/recovery; Bridge/observer; receipt/backup/DAT/LOCAL integrity; evidence v5; render levels; source/fallback/regression и mutation prohibition.

Дополнительно проверяются Lua syntax, disabled manifest, публикационная redaction и полнота пяти evidence sections. После targeted suite запускается полный Python suite, `compileall`, Lua compile и `git diff --check`.

Synthetic PASS не является runtime evidence. Phase A должна завершиться `NOT_EXECUTED`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.

## Будущая Phase B

Phase B пока заблокирована. После устранения blockers и отдельного разрешения: повторно проверить процессы/receipt 9/9; создать новый backup текущих KFC/resources и всех LOCAL-файлов; проверить DAT 000–063 attribution; новый run token; install plan только для отдельно проверенного controller; post-install hashes и rollback dry-run. Игру не запускать.

## Будущая Phase C

Требуются два отдельных разрешения: сначала ручной load/preflight без spawn, затем непосредственное подтверждение одной команды `spawn_once`. До второго подтверждения controller обязан оставаться `READY_FOR_CONFIRMATION`.

После одного spawn: identity/faction/position/render/behavior наблюдаются раздельно; затем адресный despawn и подтверждение отсутствия. Пользователь вручную закрывает игру, после чего выполняется post-run integrity. Любой unknown прекращает тест без retry. Этот сценарий нельзя выполнять, пока Phase A blockers не закрыты.
