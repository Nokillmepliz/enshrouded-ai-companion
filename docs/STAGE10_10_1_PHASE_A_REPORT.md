# Stage 10.10.1 Phase A — итоговый отчёт

Дата2026-11-18. Выполнена подготовка; Phase B–F не выполнялись. Начальный commit`7d45464b3ded5e03e8a6a636e03a96171ceb81ce`. Recovery verdict **BLOCKED_BY_UNKNOWN_ARTIFACTS** / **BLOCKED_BY_GAME_BASELINE**. Architecture verdict **PARTIAL_UPSTREAM_REUSE**; условный **NATIVE_EXTENSION_STILL_REQUIRED** для прежних строгих instance/atomic-destroy требований.

Прочитаны правила, PROGRESS, полное ТЗ, прежние отчёты и pinned source. Повторно проверены официальные GitHub releases через API: EMFv0.6.18 и EMLv0.2.0. Web fetch не предоставил страницы; прямой read-only API запрос успешно подтвердил metadata. Никакие downloaded DLL/EXE не запускались.

## Ответы по результатам

1. **Что убрать:** подготовлен карантин81 файла с exact-hash attribution; физического удаления/перемещения не было. [Manifest](STAGE10_10_1_CLEANUP_MANIFEST.md).
2. **Что не трогать:** LOCAL23, EXE/game resources/DAT; неизвестные файлы и директории целиком. Steam repair отдельно, не нашим unlink.
3. **Что неизвестно:** 51 MANUAL_REVIEW, в том числе DAT055–063, KFC.bak, changed body.lua/config/cache/log/export и vendor DLL без официального per-file доказательства. UNKNOWN не означает malware или право удалить.
4. **Backup:** ограниченный419971833 bytes + карантин29504495; полный mixed state51924042489 bytes без запаса. Полный backup не выбран; без тел DAT полного возврата после Steam Verify нет. [Стратегия](STAGE10_10_1_BACKUP_STRATEGY.md).
5. **Готовность cleanup:** инструменты/ограниченный план/fixture tests готовы; полная очистка заблокирована unknown attribution. Backup пока не создан. Нет разрешения Phase B.
6. **Steam:** после разрешённого backup/карантина и residue review пользователь вручную запускает Verify. [Шаги](STAGE10_10_1_STEAM_VERIFY_PLAN.md).
7. **Clean proof:** inventory+source/clone/GUID/npcId+loader/residue+LOCAL+официальные hashes. Одно сообщение Steam недостаточно; сейчас clean=false. [Evaluator](STAGE10_10_1_CLEAN_BASELINE_CONTRACT.md).
8. **Content owner:** integrated EMF предпочтителен как кандидат, потому что меняет private shadow resources. Одновременно standalone не использовать.
9. **Почему не готов:** runtime/hardlink/writer/redirect acceptance и чистая база не подтверждены; известный mixed KFC не используется как clean.
10. **Integrated возможен:** исходники подтверждают patch/reflection/resource APIs, export отключён. Возможность — source-level, не проведённый игровой тест. [Сравнение](STAGE10_10_1_CONTENT_OWNER_COMPARISON.md).
11. **Evidence:** print→content.log frames, отдельные writer-state/unload/shadow readback и fresh session/world; стандартный export не нужен для проекта канала. Capture integration пока не завершена.
12. **Patch:** PATCH_PREPARATION_ONLY; historical0.4 не изменён. Доверенные82-component fingerprints не утверждены до clean DB;0.5 не installable.
13. **Bridge/observer:** protocol1, новая offline validation library status/inspect/compare и error diagnostics; нет live transport use, bootstrap/mod.json, установки. Старый mutation client не разблокирован. [Evidence/observer](STAGE10_10_1_EVIDENCE_CHANNEL.md).
14. **Companion — что это:** C++ bundled1.7.0, configurable GUID, default Vukah, enemy guard/orders/combat/sidecar gear. [Исследование](STAGE10_10_1_COMPANION_RESEARCH.md).
15. **Humanoid:** готовое человеческое тело Companion не подтверждает; требуется собственный compatible template/AI/visual.
16. **Lifecycle:** sidecar/session/presence полезны, но destroy response и replace не доказывают отсутствие/идентичность instance.
17. **Follow:** Enemy guard/catch-up не универсальный villager open-world follow; proximity не критерий успеха.
18. **Beastmaster:** reuse roster/logical owner, mode/queue/reload/recovery patterns. `ours` health/faction недостаточен для безопасного destroy. [Исследование](STAGE10_10_1_BEASTMASTER_RESEARCH.md).
19. **Villager Jobs:** existing villager selection, npcId/place rebind, job cancellation/local movement. Свой humanoid не спавнит, home leash не снимает. [Исследование](STAGE10_10_1_VILLAGER_JOBS_RESEARCH.md).
20. **Что переносимо по лицензиям:** MIT implementations с сохранением notices, pinned versions/dependency audit; GPL EML boundary отдельно. Игровые assets/бинарники не публикуются. Код upstream сейчас не копировался.
21. **Identity/ownership:** публичный stable generation/atomic ownership marker не найден; logical account/npcId/pointer не решение instance reuse. [Матрица](STAGE10_10_1_UPSTREAM_REUSE_MATRIX.md).
22. **Native extension:** не дублировать ground/path/villager APIs. Остаются conditional instance destroy/ownership и неполная geometry/persistence; native implementation не начинался. [Review](STAGE10_10_1_NATIVE_EXTENSION_REVIEW.md).
23. **Roadmap:** сокращён за счёт готовых navigation/ground/job/roster patterns, архитектура Lua+Python сохранена. [Этапы и done criteria](STAGE10_10_1_UPDATED_ROADMAP.md).
24. **Тесты:** полный Python586 testsRun /585 PASS /1 skipped /0 failures. Новые61 PASS, включая Lua fixtures и Windows junction. Syntax15/15 Lua; compileall PASS. Rust/C++ компоненты не менялись; их исторические результаты не выдаются за новые.
25. **Блокеры:** unknown attribution, нет clean/depot evidence, не готов финальный patch/capture/profile, runtime render/AI/lifecycle/identity/geometry остаются неподтверждёнными. Нельзя обещать работу после установки.
26. **Следующий шаг:** отдельно согласовать Phase B limited backup+только81 reviewed quarantine, сохраняя остальные файлы, либо сначала дополнить атрибуцию. Steam Verify/установка/игровой запуск не разрешаются автоматически.

## Проверки и пределы

- Fresh inventory до/после: **249/249 game и23/23 LOCAL без изменений** по paths/size/SHA/mtime; также без изменений относительно Stage10.10. [Публичный integrity metadata](../compatibility/recovery/1287369/integrity.json).
- Game/server process enumeration до/после: отсутствуют. Ошибка перечисления процессов в CLI приводит к отказу, не к предположению, что игра закрыта.
- Recovery fixtures: authorization/default dry-run, cross-build/receipt/hash/missing/new-file, protected DAT/game files/saves, backup space/corruption/missing/wrong-path, destination overlap/existing, copy/unlink failures, process appearing before unlink, traversal/ADS/reserved names/hardlink/junction.
- Реальный read-only recovery CLI dry-run по новому manifest: **DRY_RUN_VALID**, unresolved51, cleanup_executed=false. Повторно проверены EXE/Steam identity, process state, receipt, все inventory paths/size/SHA. Это не dry-run утверждения clean baseline и не выполнение cleanup.
- Evidence fixtures: truncated/stale/duplicate frames, exact nine HashKey32 names/ranges/types, duplicate JSON keys, no partial print on malformed value, missing writer/baseline, invalid context и запрет mutations.
- Один skip — существующий privilege-dependent directory-symlink test; новый unprivileged junction test PASS. Runtime EML userdata, реальный rendered NPC и поведение не проверялись.
- Protected profiles/historical receipts не исправлялись вручную; backup/restore/cleanup/install/game/server/Steam Verify/spawn/Bridge runtime не выполнялись.
- Commit включает source/tests/docs и sanitized metadata. Не включает private receipt/run token, Steam account metadata, LOCAL contents, game dumps, upstream binary/archive.

```text
cleanup_executed=false
clean_baseline_confirmed=false
installation_ready=false
runtime_status=NOT_EXECUTED
RUNTIME_RENDER_CONFIRMED=UNKNOWN
spawn_ready=false
```
