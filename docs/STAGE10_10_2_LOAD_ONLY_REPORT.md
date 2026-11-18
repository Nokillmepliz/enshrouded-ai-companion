# Stage10.10.2 — повторный load-only patch0.5.1

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
