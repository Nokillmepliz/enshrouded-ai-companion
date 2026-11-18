# enshrouded-ai-companion

**Stage10.10.2: `READY_FOR_PATCH_UPDATE_APPROVAL`.** Кандидат0.5.1 исправляет
проверку пустой resource reference и разделяет диагностику animationGraph/retargetData.
Подготовлен update4 файлов и backup-план247.2 MB; установленный0.5.0 не изменён.
713 тестов PASS,1 skip; новый runtime не выполнен, `spawn_ready=false`.
[Отчёт и порядок согласования обновления](docs/STAGE10_10_2_REPORT.md).

**Stage10.10.1 Phase F: `BLOCKED_CONTENT_BUILD / LOAD_ONLY_UNCONFIRMED`.**
Ручной тест завершён: patch0.5.0 остановился на `AIC_PATCH:graph_changed`.
После закрытия originals67/67, installed16/16 и backup27/27 PASS; за игровой сеанс
изменились6 LOCAL-файлов, их хеши зафиксированы, восстановления не было.
[Итоговый отчёт Phase F](docs/STAGE10_10_1_PHASE_F_REPORT.md). `spawn_ready=false`.

**История: Stage10.10.1 Phase E завершена: `READY_FOR_PHASE_F_APPROVAL`.**
Установлены только16 согласованных файлов;16/16 hashes, новый receipt и rollback
dry-run PASS.137 оригинальных файлов и23 LOCAL неизменны, backup/quarantine сохранены.
Python690 PASS/1skip. Игра/server не запускались; Phase F ещё не разрешена,
runtime NOT_EXECUTED, spawn_ready=false.
[Отчёт Phase E и receipt](docs/STAGE10_10_1_PHASE_E_REPORT.md).

**История: Stage10.10.1 offline Phase D: `READY_FOR_PHASE_E_APPROVAL`.**
Пользователь принял `CLEAN_BASELINE_PARTIAL`. Новый verified backup27/27 создан:
260600882 bytes с metadata. Patch0.5.0, evidencev8, observer0.3.0, read-only Bridge,
профиль1287369 и точный пакет16 файлов готовы. Финальный preflight137 game/23 LOCAL
PASS; rollback dry-run на project fixture PASS. Python684 PASS/1skip; Lua19/19.
Установка пока не разрешена и не выполнена; runtime NOT_EXECUTED, spawn_ready=false.
[Отчёт и план Phase E](docs/STAGE10_10_1_PHASE_D_REPORT.md),
[exact manifest](compatibility/migration/1287369/exact-install-manifest.json),
[будущая Phase F](docs/STAGE10_10_1_LOAD_ONLY_PLAN.md).

**История: Stage10.10.1 post-Steam Phase C: `CLEAN_BASELINE_PARTIAL`.**
Steam Verify завершён: KFC восстановлен, из resources удалён лишний хвост4096 bytes.
61/61 штатный файл совпал с локальным depot manifest; его подпись не подтверждена.
KFC55 containers; старый clone GUID/npcId отсутствует,12269 templates проверены.
64 DAT/23 LOCAL/20 KEEP неизменны; backup209/209 и карантины81/81+31/31 сохранены.
[Отчёт и предложение ограниченного acceptance](docs/STAGE10_10_1_POST_STEAM_AUDIT.md).
Новый backup27 файлов260563026 bytes пока только рассчитан. Migration package остаётся
PARTIAL: patch0.5/observer/Bridge/exact install plan ещё не завершены.
Python644 PASS/1skip; Rust3 PASS. Установка не разрешена; runtime NOT_EXECUTED, spawn_ready=false.
[Исторический pre-cleanup audit](docs/STAGE10_10_1_PHASE_C_REPORT.md),
[подготовка Phase D](docs/STAGE10_10_1_PHASE_D_REPORT.md).

**Stage10.10.1 limited Phase B: `LIMITED_PHASE_B_COMPLETED`.** Создан и проверен
backup420406619 bytes; в карантин перенесён только81 разрешённый файл.
Оставшиеся168 игровых файлов, все51 MANUAL_REVIEW,64 DAT и23 LOCAL-файла неизменны.
Старые известные loaders убраны; чистый baseline пока не подтверждён.
Integrated EMF content принят как будущая архитектура с integrity gates.
Phase C/Steam Verify/установка/runtime не выполнялись; `spawn_ready=false`.
Тесты:596 PASS/1skip. [Отчёт Phase B](docs/STAGE10_10_1_PHASE_B_REPORT.md),
[разбор оставшихся51 файлов](docs/STAGE10_10_1_RESIDUAL_FILES_REVIEW.md).

**Stage10.10.1 Phase A: `BLOCKED_BY_UNKNOWN_ARTIFACTS`, `PARTIAL_UPSTREAM_REUSE`.**
Подготовлены точный recovery manifest272 файлов, безопасные backup/quarantine
инструменты и offline observer/evidence libraries. Карантин81 подтверждённого файла
только запланирован;51 файл требует review. Рекомендован integrated EMF content
после clean baseline. Patch0.5/установка/runtime пока не готовы; `spawn_ready=false`.
Новые61 тест PASS; весь suite585 PASS/1skip. Игра249/249 и LOCAL23/23 неизменны.
[Итог и ответы по ТЗ](docs/STAGE10_10_1_PHASE_A_REPORT.md),
[план recovery](docs/STAGE10_10_1_RECOVERY_PLAN.md),
[обновлённый roadmap](docs/STAGE10_10_1_UPDATED_ROADMAP.md).

**Stage 10.10 Phase A: `BLOCKED_BY_GAME_INTEGRITY`.** Установлена игра 1.0.1.2 /
build1287369; старый EMF0.3.2 несовместим. Проверен официальный EMF0.6.18/API46,
но установки не было. Текущая база содержит старый custom clone; source теперь
имеет82 компонента. Добавлены compatibility profiles, evidencev7 и защита от
cross-build rollback. Python:524 PASS/1skip (116 новых), Rust:2 PASS, C++:30 PASS.
Game249/249 и LOCAL23/23 файлов неизменны. `installation_ready=false`,
`runtime_status=NOT_EXECUTED`, `spawn_ready=false`.
[Полный отчёт и блокеры](docs/STAGE10_10_PHASE_A_REPORT.md),
[план перехода](docs/STAGE10_10_UPGRADE_PLAN.md).
Следующие результаты Stage10.7–10.9 относятся к **историческому build1273043**;
новый EMF уже предоставляет ground/path/villager APIs, что меняет прежний extension scope.

**Stage 10.9 Phase A: `NATIVE_EXTENSION_REQUIRED / BLOCKED_FOR_SPAWN`.** Исходники EMF подтверждают native `spawn_ex`, но `EntityId` остаётся простым `uint32` без доступного generation/ownership marker; teleport ground search изменяет уже существующую entity и не заменяет read-only position validator; `ForceSave` сам по себе не сохраняет runtime spawn, а custom villager lifecycle остаётся неизвестным. Добавлены `OwnedEntityIdentity`, tri-state position/persistence/destroy contracts, восемь независимых gates, recovery matrix, проект минимального native extension и 54 offline-теста. Runtime не выполнялся; `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`. См. [identity research](docs/STAGE10_9_INSTANCE_IDENTITY_RESEARCH.md), [position research](docs/STAGE10_9_POSITION_VALIDATION_RESEARCH.md), [persistence research](docs/STAGE10_9_PERSISTENCE_RESEARCH.md) и [extension design](docs/STAGE10_9_NATIVE_EXTENSION_DESIGN.md).

**Stage 10.8 Phase A: `BLOCKED_FOR_SPAWN`.** Подтверждены реальные `emf.spawn(world,guid,x,y,z)` и `emf.destroy(world,id)`, но public API не даёт pre-spawn ground/geometry validation, native instance identity/ownership, а persistence villager clone с `ForceSave` неизвестен. Добавлены fail-closed offline controller, выключенный Lua scaffold, evidence v5 и тесты. Игра не запускалась, мод не устанавливался, spawn/despawn/rollback не выполнялись; `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`. См. [API research](docs/STAGE10_8_SPAWN_API_RESEARCH.md) и [safety contract](docs/STAGE10_8_SAFETY_CONTRACT.md).

**Stage 10.7 Phase C завершена: `LOAD_ONLY_SUCCESS`.** Контролируемый ручной запуск подтвердил A/H/R/V/B/C: все девять HashKey32 у source/clone совпали, новый template сериализован и найден read-only lookup, `CharacterSetup`, animation graph и visual dependencies согласованы. Post-run integrity прошла без неизвестных изменений; rollback готов и не выполнялся. Entity не создавалась, поэтому runtime render остаётся `UNKNOWN`, а `spawn_ready=false`. См. [Phase C report](docs/STAGE10_7_PHASE_C_REPORT.md) и [runtime results](docs/STAGE10_7_RUNTIME_RESULTS.md).

**Исторический результат — этап 10.6 Phase C: `FAILED — V:CHARACTER_SETUP`.** Контролируемый load-only запуск дал A/B/C=PASS, V=FAIL: структура, animation, retarget и 18 visual references совпали, но девять `HashKey32` полей `CharacterSetup` остались `UNSUPPORTED`. Post-run integrity подтверждена, неизвестных изменений нет, rollback не выполнялся. `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`. [Phase C report](docs/STAGE10_6_PHASE_C_REPORT.md), [evidence contract](docs/STAGE10_6_VISUAL_EVIDENCE_CONTRACT.md), [план](docs/STAGE10_6_VISUAL_LOAD_PLAN.md).

**Предыдущий результат — этап 10.5: `PARTIAL_SUCCESS`.** Read-only исследование разрешило source-цепочку `TemplateResource → CharacterPresetCollection → ItemRegistryResource/ItemInfo → RenderModel → ModelHierarchyResource`; 35/35 target models найдены, общий hierarchy содержит 102 joints. Подробности: [результаты inspector](docs/STAGE10_5_KFC_INSPECTOR_RESULTS.md) и [visual dependencies](docs/STAGE10_5_VISUAL_DEPENDENCIES.md).

**Исторический результат этапа 10.4 — `BLOCKED`.** Reflection и ECS program map подтвердили цепочку `CharacterSetup → Equipment → RenderEquipment → RenderScene`, но конкретные model/mesh/skeleton dependencies не извлечены. Подробности: [исследование visual resources](docs/STAGE10_4_VISUAL_RESOURCE_RESEARCH.md) и [дизайн fingerprint](docs/STAGE10_4_VISUAL_FINGERPRINT_DESIGN.md).

**Исторический результат этапа 10.3 — `BLOCKED`.** Офлайн-диагностика установила, что реальный `hunter_assistant` не содержит `ModelResource` в сериализованном `TemplateResource`; прежний `model_guid=nil` возник до чтения поля GUID. Typed evidence v2 и evaluator исправлены fail-closed, но фактическая внешняя model dependency не извлечена. Подробности: [исследование модели](docs/STAGE10_3_MODEL_RESOURCE_RESEARCH.md) и [исправление fingerprint](docs/STAGE10_3_MODEL_FINGERPRINT_FIX.md).

**Исторический результат этапа 10.2 — `FAILED`.** Первый ручной load-only запуск подтвердил загрузку игры и LOCAL-мира (`B=true`), EML применил один patch, а EMF/Bridge работали на build 1273043. Уровень A отклонён: export вернул `model_guid=nil`. Уровень C неполон: ответ observer `inspect` был обрезан лимитом строки EMF. `load_only_success=false`, `spawn_ready=false`; spawn не выполнялся. Backup и post-run integrity проверены; отдельно разрешённый откат выполнен и подтверждён итоговой сверкой `ok=true`. Подробности: [runtime-отчёт 10.2](docs/STAGE10_2_RUNTIME_RESULTS.md).

После испытания evaluator исправлен: nil-подобные fingerprints больше не проходят, реальный формат EML log поддержан, а observer `inspect` сокращён для лимита EMF. Исправления находятся только в репозитории; после отката EML/patch/observer в игре отсутствуют, игра повторно не запускалась. Полный offline suite: **188 PASS**.

**Текущий приоритет — независимый Human NPC Body Adapter в одном экземпляре игры.** Вариант со вторым клиентом отклонён. Этап 8 не нашёл безопасного неуникального человеческого template: все подтверждённые workshop survivors уникальны, а public EMF Lua не регистрирует новый entity template и не даёт instance-local замену model/animation graph. Runtime spawn человека выключен; подготовлены fail-closed lifecycle и отдельный disabled read-only survey. Исследование: [INDEPENDENT_HUMANOID_RESEARCH.md](docs/INDEPENDENT_HUMANOID_RESEARCH.md), архитектура: [INDEPENDENT_HUMANOID_ARCHITECTURE.md](docs/INDEPENDENT_HUMANOID_ARCHITECTURE.md).

Исторический этап 7 сохранён: [PLAYER_CHARACTER_COMPANION_RESEARCH.md](docs/PLAYER_CHARACTER_COMPANION_RESEARCH.md), [PLAYER_CHARACTER_COMPANION_ARCHITECTURE.md](docs/PLAYER_CHARACTER_COMPANION_ARCHITECTURE.md). Его вариант со вторым account/client больше не является направлением проекта.

**Текущее направление:** человекоподобный AI Companion. Исследованы 18 реальных workshop survivor templates, варианты player clone и отдельного humanoid body. Безопасный runtime spawn гуманоида пока заблокирован: uniqueness, начальная faction, ownership и dismiss независимого экземпляра не подтверждены. Выводы — [HUMAN_COMPANION_RESEARCH.md](docs/HUMAN_COMPANION_RESEARCH.md), контракты — [HUMAN_COMPANION_ARCHITECTURE.md](docs/HUMAN_COMPANION_ARCHITECTURE.md).

**Первое игровое испытание:** `emf.spawn` создал Vukah, но fingerprint отсутствовал; faction не была изменена, NPC оказался враждебным. Сценарий остановлен, тестовые LOCAL-сохранения восстановлены и проверены. Vukah отложен как `legacy_vukah`; результат не переписывается — [FIRST_INGAME_TEST.md](docs/FIRST_INGAME_TEST.md).

**Техническое состояние этапа 8:** 126 офлайн-тестов PASS, `safety_revision=2` старого адаптера не ослаблена. Добавлены `HumanBodyDescriptor`, capability registry, независимый lifecycle/ownership gate и read-only Lua survey; ни одна игровая команда нового гуманоида не включена. Актуальные проверки — [TEST_RESULTS.md](docs/TEST_RESULTS.md).

**История подготовки первого игрового испытания:** [проверка установленной игры, резервная копия и пошаговый запуск](docs/STAGE3_PREFLIGHT.md). EXE соответствовал сборке EMF 1273043. Body Adapter — Lua-мод, собственной DLL у него нет; фактический результат позднейшего теста Vukah приведён выше.

Проект автономного ИИ-компаньона для Enshrouded. Долгосрочная цель: игровое тело, внешний ИИ, зрение, голос, личность, навыки и память.

**На этапе 2 был подготовлен минимальный прототип тела без установки и запуска игры.**

В прототип входят:

- [Lua Body Adapter](mods/aic_body/main.lua) для EMF: `spawn`, `follow`, `stay`, `dismiss`, опрос состояния и проверка результата. Тело — `Enemy_Vukah_Melee`.
- [Python-клиент](companion/client.py) поверх существующего EMF bridge; JSON-ответы, диагностика, таймауты и защита от повторов.
- [Профиль личности](companion/profile.py) с постоянным UUID во внешнем JSON-файле, независимо от `entityId`.
- [Тесты](tests/) настоящего Lua-кода в поддельной среде EMF, интеграции Python → Lua и упаковки; никаких подключений к игре.

Документация: [первый запуск и резервное копирование](docs/FIRST_RUN.md), [контракт и ограничения](docs/PROTOCOL.md), [план игровых испытаний](docs/TEST_PLAN.md), [первоначальное исследование](docs/RESEARCH.md).

Проверки этапа 2: **48 тестов прошли**; подробности и SHA-256 архива — [TEST_RESULTS.md](docs/TEST_RESULTS.md).

Голос, добыча ресурсов и полноценный Brain не реализованы. Мод выключен по умолчанию, автоматически ничего не спавнит. Первые испытания ограничены локальным миром хоста, EMF 0.3.2 / API 20 и исследованной сборкой игры 1273043. Другую сборку сначала нужно исследовать.

## Проверка без игры

Нужен Python 3.12 для зафиксированной тестовой среды; сам клиент использует только стандартную библиотеку. Из корня проекта:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-test.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/package.py
```

Тестовый dependency `lupa==2.6` выполняет Lua 5.4; в игре его не нужно устанавливать. Упаковка создаёт `dist/aic_body-0.1.0.zip`, не устанавливая мод. В текущем рабочем каталоге также подготовлен изолированный `.tools/python/python.exe` для запуска тех же проверок без системной установки.

Пример создания личности без игры:

```powershell
.\.venv\Scripts\python.exe -m companion profile-init --name "Спутник"
```

Профиль появится в `runtime/personality.json`; повторная команда не перезаписывает существующую личность.

Исходники upstream находятся в `.research/` и исключены из Git. Копия Python bridge с лицензией включена в [vendor/](vendor/README.md), остальной upstream не нужен для запуска клиента. Официальный установщик EMF был выполнен 30.10.2026 после аудита дистрибутива; в игре выполнены только read-only `diagnose/status`.

Следующий шаг — отдельно согласованное load-only испытание по плану этапа 10.1: новый verified backup, установка проверенного EML/patch/observer, ручной запуск только LOCAL test world, сбор A/B/C evidence и откат. Spawn остаётся запрещённым до отдельного следующего этапа с ownership marker и безопасным dismiss.
