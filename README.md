# enshrouded-ai-companion

**Stage 10.7 Phase B завершена: `READY_FOR_PHASE_C_REVIEW`.** Текущая установка 0.3.0 штатно откатилась, KFC/resources восстановлены, создан новый verified backup текущего LOCAL-состояния и установлен patch 0.4.0/evidence v4 с read-only observer. Receipt и installed hashes 9/9, backup 24/24, rollback dry-run 9/9; игра не запускалась, LOCAL saves не восстанавливались, `spawn_ready=false`. См. [Phase B report](docs/STAGE10_7_PHASE_B_REPORT.md).

**Текущий этап 10.7 Phase A — `PARTIAL_SUCCESS`.** Причина `HashKey32=UNSUPPORTED` найдена и исправлена в исходниках patch 0.4.0: EML отдаёт reflected struct как userdata, а его `.value` — точный UInt32/Lua integer. Подготовлены evidence/evaluator v4 и read-only lookup clone по GUID/type/part; неподтверждённая запись в `GuidRegistryResource` удалена. Реальный runtime нового кода не выполнялся, поэтому H/R остаются непроверенными, `spawn_ready=false`. См. [HashKey32 research](docs/STAGE10_7_HASHKEY32_RESEARCH.md), [registration research](docs/STAGE10_7_REGISTRATION_RESEARCH.md) и [test plan](docs/STAGE10_7_TEST_PLAN.md).

**Текущий результат — этап 10.6 Phase C: `FAILED — V:CHARACTER_SETUP`.** Контролируемый load-only запуск дал A/B/C=PASS, V=FAIL: структура, animation, retarget и 18 visual references совпали, но девять `HashKey32` полей `CharacterSetup` остались `UNSUPPORTED`. Post-run integrity подтверждена, неизвестных изменений нет, rollback не выполнялся. `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`. [Phase C report](docs/STAGE10_6_PHASE_C_REPORT.md), [evidence contract](docs/STAGE10_6_VISUAL_EVIDENCE_CONTRACT.md), [план](docs/STAGE10_6_VISUAL_LOAD_PLAN.md).

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
