# Stage 10.10 — offline checks и будущий load-only

## Выполнено в Phase A

116 новых Python/Lua scenarios в [test_stage10_10.py](../tests/test_stage10_10.py):
build detection и независимые IDs; unsupported/missing/tampered profiles без
fallback; KFC/resources/DAT attribution; real helper guards против cross-build
rollback/restore, stale baseline/manifest/targets, unowned и duplicate paths;
EMF/EML/API/schema contracts; template count/fingerprint/animation/dependencies;
typed UInt32 и source/clone equality; Bridge capture correlation/readonly;
evidence v7 и запрет повышения runtime/install/spawn status; Lua preparation
guard с missing/collision/schema/resource failures. Все работают с fixtures.

Команды из project root:

```powershell
.tools/python/python.exe -m unittest tests.test_stage10_10 -q
.tools/python/python.exe -m unittest discover -s tests -q
.tools/python/python.exe -m compileall -q companion scripts tests tools
git diff --check
```

Полный Python suite: discovered / runner testsRun **525**, реально выполнено
**524**, passed **524**, failed **0**, skipped **1**. Новые **116/116**, regression
**409 discovered / 408 PASS / 1 skip**. Skip — Windows directory-symlink privilege
test; он существовал до этапа и не заменён фиктивным PASS.

Rust Inspector: `cargo test --locked --offline --manifest-path
tools/kfc_readonly_inspect/Cargo.toml`, **2/2 PASS**. Использован существующий
локальный Rust1.88.0, CARGO_HOME/RUSTUP_HOME/PATH только текущего процесса;
системные настройки не менялись. Lock/revision не обновлялись.

Upstream C++ (fa6efda), локальный mingw64 g++17-mode: test_main,
test_ground_service, test_ground_search, test_path_service + ground_service,
ground_search, fog_check, path_service. **30/30 cases, 730/730 assertions PASS**.
Первая link-команда не включала ground_search/fog_check implementation и завершилась
ошибкой; после добавления зависимостей сборка и запуск тестов прошли. Это тестовый
EXE с fake game dependencies, не game process, не скачанный release EXE/DLL.
Не заявляется сборка всего EMF/MSVC или подтверждение hooks на реальном EXE.

Lua sources компилируются через установленный Lupa; реальные userdata EML не
создаются. HashKey mocks подтверждают логику, не runtime reflection.
Перед публикацией — syntax, whitespace, forbidden artifacts/token scan и полный
before/after SHA inventory. Результат в [runtime report](STAGE10_10_RUNTIME_RESULTS.md).

## Phase C — план, НЕ ВЫПОЛНЕНО

Только после закрытых Phase B blockers, успешного reviewed installation и нового
явного разрешения. Нужен verified backup LOCAL **до** первого открытия новой
версией: возможна save migration. Body Test slot1 / AI Body Test slot1 выбирает
пользователь вручную. Совместимость существующих saves сейчас неизвестна; если
потребуется новый изолированный мир, его создаёт пользователь после согласования.

1. Game/server stopped: receipt/build/profile/hash, clean/current baseline,
   backup integrity, отсутствие неизвестных DLL/mods, rollback dry-run.
2. Зафиксировать новые token/session/log offsets, сообщить READY_FOR_MANUAL_START.
3. Пользователь запускает игру и сообщает загрузку LOCAL тестового контекста.
4. Только read-only hello/state и observer status/inspect/compare; проверить
   protocol1/coreAPI46, build1287369, process client/server-world и identity мира.
5. A: patch apply + writer **finalized**, а не print внутри Lua.
   H: typed девять HashKey32, provenance и source/clone equality.
   R: GUID/type/part lookup, отсутствие collisions, actual resource metadata.
   V: CharacterSetup, graph, dependencies, skeleton; render остаётся UNKNOWN.
   B: связанный Bridge/observer token/session и полностью полученные replies.
   C: source integrity, LOCAL context, отсутствие fatal/resource errors.
6. При critical error остановить сбор, сохранить диагностику; не выполнять
   автоматический rollback, reload/retry patch, spawn/despawn/entity mutation.
7. После ручного закрытия игры сравнить KFC/resources/DAT, shadow outputs (если
   выбран shadow owner), installed files и LOCAL saves с новым baseline. Изменённые
   saves описать как наблюдение, не восстанавливать автоматически.
8. Только после фактов сформировать verdict; при LOAD_ONLY_SUCCESS всё равно
   `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.
