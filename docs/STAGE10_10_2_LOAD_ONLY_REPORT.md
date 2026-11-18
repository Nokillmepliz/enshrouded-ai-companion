# Stage10.10.2 — повторный load-only patch0.5.1

## Итог после закрытия — LOAD_ONLY_UNCONFIRMED

2026-11-18,13:50:45 UTC: пользователь закрыл игру. Read-only audit подтвердил
отсутствие game/server, прежний build, package/profile/binding/receipt, installed16/16
и verified backup38/38. Проверки выполнены заново, не перенесены из preflight.

- **67/67 оригинальных ресурсов неизменны** по SHA/size/mtime/identity/links:
  EXE, KFC, resources и64 root DAT. Все16 установленных файлов совпали с receipt.
  Fingerprint0.5.1 совпал. Gate C PASS.
- Game inventory234 (до запуска222):12 добавлений, удалений нет. Shadow77 (ранее66):
  добавлены9 generated DAT055–063, `.cache/files.json`, `shadow.txt`.
  Изменены private KFC/resources, state и3 копии мода; их SHA совпадают с установленным
  payload.56 base hardlinks совпали с оригиналами; неожиданных links/reparse не выявлено.
  Это проверка файловой структуры, не семантический readback новых ресурсов.
- Post-close audit завершился **POST_CLOSE_BLOCKED / UNATTRIBUTED_NON_SHADOW_CHANGES**:
  новый `backup/enshrouded_2026-11-18T16-46-15.log` и изменение только метаданных
  `emf/chain_status.txt` не входят в список разрешённых изменений этого исполнителя.
  SHA chain_status не изменился. Эти результаты не доказывают повреждение или
  конфликт модов, но автоматический общий PASS запрещён. Список не расширялся
  задним числом, повторного запуска аудита для снятия блокера не было.
- LOCAL23:7 файлов изменили содержимое (character0/world0 и5 backup-файлов),
  остальные16 сохранили SHA/размер. `local_settings.json` изменил только metadata.
  Добавлений/удалений нет. Before/after hashes опубликованы без содержимого сохранений;
  семантическая целостность KSD не доказана. Агент сохранения не изменял и не восстанавливал.

[Полный post-close результат](../compatibility/updates/1287369/0.5.1/load-only/post-close.json).
Private inventory/logs: `runtime/stage10_10_2/load_only/20261118T134435140530Z/post-close-20261118T135045278853Z`.

Итог: A/H/C PASS, V REFERENCES_ONLY, R/B UNKNOWN; LOAD_ONLY_UNCONFIRMED.
Исправление animationGraph/retargetData и завершение writer подтверждены этим запуском.
Bridge error5 остаётся неразобранным: подключение не повторялось, observer/LOCAL runtime
context не подтверждены. Shadow readback, независимая resource redirection и rendering
остаются непроверенными. После ошибки выполнялся только разрешённый post-close audit.
Spawn, игровые мутации, ручная очистка cache/shadow и rollback не выполнялись.
**spawn_ready=false**. Работа остановлена; следующий шаг — отдельно разобрать Bridge
access и два неатрибутированных изменения перед дальнейшим испытанием.

`scripts/audit_patch_0_5_1_closed.py` использует существующие snapshot/differences,
check_plan/verify_updated/verify_backup/input_fingerprint/live validators.
Py_compile PASS. Полный набор unit tests выполнен отдельно; результаты приведены
в PROGRESS.md. Успех unit tests не отменяет фактический POST_CLOSE_BLOCKED.

## История runtime: BLOCKED_BRIDGE_ACCESS — ожидание закрытия игры

Пользователь загрузил мир. PID187928, старт16:46:13 MSK, fresh build13:46:15 UTC.
Копии logs/state/shadow.txt сохранены в private checkpoint/runtime-capture.

- Штатная пересборка выполнена: loader сообщает новый build и shadow copy;
  state code0, unloaded=true, truncated=false, errors/warnings пусты.
  Existing `validate_state` подтвердил fingerprint,0.5.1 и freshness.
- AnimationGraph PASS: `402df515-5965-4b01-a17b-17d482a91af4`.
  RetargetData PASS: Lua string ZERO_GUID нормализован в null.
- Existing evidence v8 parser PASS: clone зарегистрирован в EML app state,
 82 компонента, fingerprint5253f478,9 HashKey32 source/clone,63 dependencies,
 102 joints,18 visual references; source_unchanged=true. Это build evidence,
  не доказательство визуального отображения NPC или runtime lookup.
- Writer завершён по отдельному fresh state. REQUESTED_NOT_FINALIZED внутри
  evidence относится к моменту Lua emission до завершения writer.
- Existing `integrated_observe.py compare` остановился на открытии pipe
  `emf-bridge-187928`: **Windows error5 / access denied**. hello/state и команды
  observer не выполнялись. Причина отказа не установлена; текст библиотеки
  «8 clients connected already?» не доказывает исчерпание лимита.
- Согласно условию остановки повторного подключения, изменения прав и обхода
  ограничений не было. Shadow readback, фактическая resource redirection,
  observer/session и текущий LOCAL context остаются UNKNOWN.

[Промежуточный результат](../compatibility/updates/1287369/0.5.1/load-only/runtime-result.json).
Verdict LOAD_ONLY_UNCONFIRMED: A/H PASS, V REFERENCES_ONLY, B/R/C UNKNOWN.
После ручного закрытия игры ещё предстоит post-close integrity относительно preflight.
Игра не закрывается агентом. Spawn/мутации/cleanup/rollback не выполнялись,
`spawn_ready=false`, runtime render UNKNOWN. Тесты кода повторно не запускались.

## История preflight

2026-11-18,13:44:35 UTC: **READY_FOR_MANUAL_START**.
Это результат preflight, не результат игрового теста.

Использованы существующие read_pinned/check_plan/verify_updated/verify_backup,
clean backup verify, snapshot, input_fingerprint, rollback_plan и live guards.
Новый read-only исполнитель: `scripts/preflight_patch_0_5_1.py`.

- Game/server закрыты, Steam build26430625/game1287369 прежний.
- Pinned package/profile/binding/parent receipt/update receipt PASS;16/16 installed hashes PASS.
- Verified backup38/38 и clean backup27/27 PASS. Rollback dry-run4 PASS, не выполнен.
- Полная сверка222 game records и23 LOCAL records с post-install snapshot PASS,
  включая67 original resources и66 shadow. Проверены SHA/size/mtime/identity/links.
- Фактический content fingerprint совпал с receipt/plan:
  `sha256:17d1f36bb57e8dd9fc064eee5402ed4f10365d9970bda8fa975e7156638f1138`.
- LOCAL `default/character0.ksd` / `default/world0.ksd`: SHA совпали с baseline;
  в каждом найдено одно вхождение соответствующего имени Body Test / AI Body Test.
  Историческая привязка slot1 сохранена; выбранный runtime context ещё требует Bridge.
- Py_compile нового исполнителя PASS; реальное выполнение preflight exit0.
  Полный unit suite повторно не запускался: валидаторы и игровой payload не менялись.

Private checkpoint: `runtime/stage10_10_2/load_only/20261118T134435140530Z`.
Inventory SHA-256: `fa172fc1c270ac4cd5751fdc185211149d8053adac8227fa03b1aa46d3204d18`.
[Публичный preflight](../compatibility/updates/1287369/0.5.1/load-only/preflight.json).

## После ручного запуска

Пользователь запускает игру через Steam и загружает только LOCAL Body Test (slot1)
и LOCAL AI Body Test (slot1), затем сообщает «загрузился».
Read-only диагностика сначала проверяет свежие logs/state и критические ошибки.
Затем проверяются animationGraph/retargetData diagnostics, регистрация clone,
evidence v8 существующим parser с binding0.5.1, writer completion/freshness,
shadow integrity/readback и resource redirection. IntegratedClient разрешает только
observer status/inspect/compare и проверяет LOCAL context через hello/state.
При ошибке диагностика прекращается и сохраняется фактическое evidence.

После ручного закрытия выполняется новый inventory и сравнение с этим checkpoint:
original resources/installed16, изменения shadow/logs и LOCAL перечисляются отдельно.
Изменения сохранений от игры нельзя заранее объявлять отсутствующими или восстанавливать.
Автоматический rollback, spawn, игровые мутации и ручная очистка cache запрещены.

Старый failed0.5.0 shadow state сохранён; штатная пересборка ещё не выполнялась.
Writer/registration/evidence/redirection/observer/Bridge/runtime render пока **не проверены**.
`runtime_validation=WAITING_FOR_MANUAL_START`, `spawn_ready=false`.
