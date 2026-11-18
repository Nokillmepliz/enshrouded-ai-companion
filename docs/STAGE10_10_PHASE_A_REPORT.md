# Stage 10.10 — Phase A report

Дата: **2026-11-18**. Начальный HEAD `1b9ecbff01509e89ba7a7497efdb0f0a2dbb2681`,
master; working tree перед началом был чистым. Результаты Stage 10.7–10.9 сохранены.
Stage 11.0 не начат. Выполнены только source research, read-only file inspection,
offline adaptation/tests и документация.

**Verdict: BLOCKED_BY_GAME_INTEGRITY.** Дополнительные blockers:
`BLOCKED_BY_EML` для непринятой content/evidence интеграции и
`BLOCKED_BY_RESOURCE_SCHEMA` для отсутствующего verified clean resource baseline.
EMF0.6.18 — кандидат с подтверждённой upstream поддержкой build1287369;
это не локальный runtime acceptance. **Phase B сейчас не готова.**

## Ответы на вопросы ТЗ

1. **Установлено:** Enshrouded 1.0.1.2, internal build1287369, EXE SHA
   `5d9ef2f140b8ed49e30dbee655841b89d08baec20f799a1817e171a18a850c77`.
2. **Последняя найденная публичная игра:** 1.0.1.2/1287369 на 18 ноября;
   Steam build26430625, depot manifest7226436020230696061 — отдельные IDs.
3. **Обновления:** 1283531/1.0.1.0 → 1285601/1.0.1.1 → 1287369/1.0.1.2,
   2–4 ноября; [официальные источники и EXE evidence](STAGE10_10_GAME_VERSION_AUDIT.md).
4. **Игровые файлы:** 249 прочитаны; KFC/resources/.bak и 25 исходных DAT изменены
   относительно старого baseline, чистота новой базы не доказана. В ней уже есть clone.
5. **Старые моды остались:** EMF0.3.2, EML0.2.0, patch0.4.0, observer; receipt9/9
   совпал. Сохранённый лог 6 ноября: EMF idle, 38/50 signatures. Это не новый тест.
6. **Старые backup:** содержимое 317/317 verified; 24/24 Stage10.7 intact.
   Исторические game resources нельзя восстанавливать на1287369. LOCAL default22
   совпали со Stage10.7 post-state, но игровая совместимость saves не проверена.
7. **Актуальный EMF stable:** 0.6.18 / fa6efdac2d93dd1d8ac6fe0e2a658140aec35241,
   API46, Lua host1.39.0. Официальный manual archive скачан в project runtime.
8. **EMF support:** upstream знает точный EXE1287369; archive digest и четыре DLL
   проверены статически. DLL NotSigned; воспроизводимая binary/source identity и
   local hooks/runtime не подтверждены. Установки не было.
9. **Актуальный EML stable:** 0.2.0 / 16708594d686b030d909f2d835b199d879ea9ad8.
   «EML0.3.2» из ТЗ — неточное обозначение EMF version.
10. **EML support:** parser/typed decode на новой базе работают offline; standalone
    writer и game load требуют controlled validation. EMF integrated content несёт
    patched EML, использует shadow и выключает export. Канал evidence не выбран.
11. **ECS изменились:** generated subset: 1283 identical, 4 layout-changed, 2 added;
    полный старый alignment/resource ABI comparison местами UNKNOWN.
12. **Source humanoid изменился:** 81→82 components, GrassEffector, movement/AI
    values. Новый observed fingerprint5253f478, не автоматически trusted baseline.
13. **GUID:** source, graph, hierarchy прежние; custom GUID уже присутствует.
    Отсутствие collision в чистой новой базе не доказано.
14. **HashKey32:** девять UInt32, gender и proportions source/clone сохранились;
    `.value` подтверждён исходниками EML и offline schema. Нового runtime Lua proof нет.
15. **Visual chain:** current serialized dependencies доступны; 35 RenderModel и
    hierarchy совпали, preset18 references и102 joints сохранены. Renderer UNKNOWN.
16. **Новый patch нужен:** подготовлен read-only compatibility guard для0.5.0.
    Полноценный installable0.5.0 заблокирован clean baseline/collision/evidence owner;
    историческая0.4.0 не изменена и в игру ничего не копировалось.
17. **Python Bridge:** wire protocol1 сохранился; нужны новые profile gates и
    согласованный collector/observer. Добавлен offline capture validator, команды
    status/inspect/compare проверены на fixtures. Старый BodyClient mutations на
    новой игре блокирует. Pipe connection не выполнялся.
18. **Новые safe-spawn возможности:** ground_at, path_find, building-only find_wall,
    villager_move; они уменьшают scope собственного extension, но не разрешают spawn.
19. **Stage10.9:** identity/ownership/atomic destroy и unique persistence blockers
    остаются; тезис об отсутствии ground/path API устарел. Полная matrix отдельно.
20. **Native extension:** не нужен для дублирования ground/path/move; для недостающей
    надёжной instance identity/atomic ownership check решение ещё требуется.
    Полноценный extension в Stage10.10 не разрабатывался.
21. **Изменения проекта:** profiles, evidencev7, build/baseline-aware rollback guards,
    retired unsafe directory cleanup, source/resource/inventory audit scripts,
    Lua preparation guard, 116 новых tests, 15 документов и публичные metadata reports.
22. **Тесты:** Python525 discovered,524 executed/PASS,0 failures,1 historical skip;
    new116 PASS, regression408 PASS/1skip. Rust2 PASS. C++30 cases/730 assertions PASS.
    Это offline, не успешное игровое испытание.
23. **Оставшиеся blockers:** mixed game data, no clean baseline, custom GUID already
    present, нет accepted patch/observer/export strategy, unsigned DLL/runtime
    untested, unknown full old schema, unknown save migration/render/lifecycle.
24. **Phase B:** **нет**, сначала review clean-baseline/cleanup/content-owner plan и
    конкретных новых files/hashes. Никакое старое разрешение на другой этап не
    переиспользуется как разрешение текущей установки.
25. **Stage11.0:** принять новый профиль после load-only PhaseC/D, убрать повторную
    реализацию upstream ground/path/villager movement, отдельно исследовать
    ownership/generation/atomic destroy, clearance и persistence. Spawn только по
    отдельному согласованию, не вследствие LOAD_ONLY_SUCCESS.

## Доказательства и воспроизводимость

Исходники: [EMF compatibility](STAGE10_10_EMF_COMPATIBILITY.md),
[EML compatibility](STAGE10_10_EML_COMPATIBILITY.md),
[Stage10.9 revalidation](STAGE10_10_STAGE10_9_REVALIDATION.md).
Офлайн-факты: [file inventory](STAGE10_10_GAME_FILE_INVENTORY.md),
[ECS diff](STAGE10_10_ECS_DIFF.md), [template](STAGE10_10_TEMPLATE_COMPATIBILITY.md),
[backup guards](STAGE10_10_BACKUP_AND_ROLLBACK_SAFETY.md),
[Bridge](STAGE10_10_BRIDGE_COMPATIBILITY.md),
[profiles/evidencev7](STAGE10_10_COMPATIBILITY_PROFILES.md),
[тесты](STAGE10_10_TEST_PLAN.md).
Дальнейшие действия: [upgrade](STAGE10_10_UPGRADE_PLAN.md),
[install plan](STAGE10_10_INSTALL_PLAN.md),
[runtime NOT_EXECUTED](STAGE10_10_RUNTIME_RESULTS.md).

Начальный/конечный полный hash inventory хранится локально; публичный
[integrity aggregate](../compatibility/audits/1287369/integrity.json) не содержит
save paths или персональных данных. Raw resource dumps, EXE/DLL, archive, save data,
private tokens и upstream checkouts не публикуются.

`installation_ready=false`, `runtime_status=NOT_EXECUTED`,
`RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.
Остановка после публикации Phase A. Ни installation, ни cleanup/rollback, ни
Steam Verify, ни game/server launch, ни NPC/entity mutations в этом этапе не выполнены.
